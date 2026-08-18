# Tutorial 04 — Fondamenti di JavaScript: Dal Principiante all'Esperto

> **Companion a:** `04-javascript-fondamenti.md`
> **Scope:** Tipi primitivi e coercizione, `var`/`let`/`const`, hoisting e temporal dead zone, scope lessicale e closure, funzioni e arrow function, le cinque regole di `this`, oggetti e catena prototipale, classi ES6+, array e metodi funzionali, destructuring e spread, manipolazione del DOM, eventi e delegazione, moduli ES, event loop, gestione degli errori, Symbol, generatori, espressioni regolari, garbage collection
> **Prerequisiti:** `tutorial_01_html5.md` — il DOM come albero, gli elementi che manipolerai; `tutorial_00_ambiente_setup_web.md` — un progetto Vite avviabile
> **Durata stimata:** 30-40 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** ECMAScript 2024+ · browser evergreen · Node.js LTS

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Cos'è JavaScript e dove gira](#a1-cosè-javascript-e-dove-gira)
  - [A2. Valori e tipi](#a2-valori-e-tipi)
  - [A3. Variabili: `var`, `let`, `const`](#a3-variabili-var-let-const)
  - [A4. Operatori e coercizione di tipo](#a4-operatori-e-coercizione-di-tipo)
  - [A5. Controllo di flusso](#a5-controllo-di-flusso)
  - [A6. Funzioni](#a6-funzioni)
  - [A7. Array e metodi funzionali](#a7-array-e-metodi-funzionali)
  - [A8. Oggetti](#a8-oggetti)
  - [A9. Destructuring, spread e rest](#a9-destructuring-spread-e-rest)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Scope lessicale e closure](#b1-scope-lessicale-e-closure)
  - [B2. `this`: le cinque regole](#b2-this-le-cinque-regole)
  - [B3. Prototipi e catena prototipale](#b3-prototipi-e-catena-prototipale)
  - [B4. Classi: cosa sono davvero](#b4-classi-cosa-sono-davvero)
  - [B5. Il DOM: selezionare, creare, modificare](#b5-il-dom-selezionare-creare-modificare)
  - [B6. Eventi: propagazione e delegazione](#b6-eventi-propagazione-e-delegazione)
  - [B7. Moduli ES](#b7-moduli-es)
  - [B8. L'event loop](#b8-levent-loop)
  - [B9. Gestione degli errori](#b9-gestione-degli-errori)
  - [B10. Uguaglianza, copia e riferimenti](#b10-uguaglianza-copia-e-riferimenti)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: todo-list in JavaScript vanilla](#c2-mini-progetto-todo-list-in-javascript-vanilla)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Symbol e i well-known symbol](#d1-symbol-e-i-well-known-symbol)
  - [D2. Iteratori e generatori](#d2-iteratori-e-generatori)
  - [D3. Espressioni regolari moderne](#d3-espressioni-regolari-moderne)
  - [D4. Memoria, garbage collection e memory leak](#d4-memoria-garbage-collection-e-memory-leak)
  - [D5. Come V8 esegue il tuo codice](#d5-come-v8-esegue-il-tuo-codice)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                            JAVASCRIPT
                                 │
      ┌──────────────────────────┼──────────────────────────┐
      │                          │                          │
┌─────▼──────┐          ┌────────▼────────┐        ┌────────▼────────┐
│  IL VALORE │          │   LA FUNZIONE   │        │   L'OGGETTO     │
│            │          │                 │        │                 │
│ 7 primitivi│          │ dichiarazione   │        │ proprietà       │
│  string    │          │ espressione     │        │ [[Prototype]]   │
│  number    │          │ arrow           │        │  └ catena       │
│  bigint    │          │ closure         │        │ class = zucchero│
│  boolean   │          │  └ ricorda lo   │        │  sintattico     │
│  undefined │          │    scope in cui │        │ this dipende    │
│  symbol    │          │    è NATA       │        │  da COME chiami │
│  null      │          │ this: 5 regole  │        │                 │
│ + object   │          │ arrow NON ha    │        │                 │
│            │          │  this proprio   │        │                 │
│ primitivi  │          │                 │        │ oggetti         │
│  per VALORE│          │                 │        │  per RIFERIMENTO│
└─────┬──────┘          └────────┬────────┘        └────────┬────────┘
      │                          │                          │
      └──────────────────────────┼──────────────────────────┘
                                 │
      ┌──────────────────────────┼──────────────────────────┐
      │                          │                          │
┌─────▼──────┐          ┌────────▼────────┐        ┌────────▼────────┐
│   SCOPE    │          │      IL DOM     │        │   EVENT LOOP    │
│            │          │                 │        │                 │
│ globale    │          │ querySelector   │        │ call stack      │
│ di funzione│          │ createElement   │        │  └ un thread    │
│ di blocco  │          │ textContent     │        │ microtask       │
│  └ let,const│         │  ≠ innerHTML    │        │  └ Promise      │
│ lessicale  │          │ classList       │        │  └ svuotata     │
│  └ deciso  │          │ dataset         │        │    TUTTA        │
│    da DOVE │          │                 │        │ macrotask       │
│    è scritto│         │ eventi          │        │  └ setTimeout   │
│ hoisting   │          │  capture giù    │        │  └ UNA per giro │
│ TDZ        │          │  target         │        │ rendering       │
│            │          │  bubble su      │        │  └ ~16,7ms      │
│            │          │  delegazione    │        │                 │
└────────────┘          └─────────────────┘        └─────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │        MODULI           │
                    │                         │
                    │  import / export        │
                    │  sempre strict mode     │
                    │  differiti per natura   │
                    │  binding VIVI, non copie│
                    └─────────────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cos'è JavaScript e dove gira

> **Analogia:** HTML è lo scheletro, CSS è la pelle, JavaScript è il sistema nervoso. Senza scheletro non c'è nulla da vestire; senza pelle la struttura è nuda ma esiste; senza sistema nervoso il corpo c'è ed è visibile, ma non reagisce. JavaScript è ciò che rende la pagina capace di rispondere.

JavaScript è nato nel 1995 in dieci giorni, per far muovere qualcosa nelle pagine di Netscape. Quella fretta ha lasciato tracce che studieremo — la coercizione di tipo, `typeof null`, `var` — e che oggi convivono con un linguaggio serio.

**ECMAScript è lo standard, JavaScript è l'implementazione.** Dal 2015 esce una versione all'anno: ES2015 (chiamata anche ES6) è quella che ha cambiato tutto, e da lì in poi gli aggiornamenti sono incrementali.

### I due ambienti

```javascript
// Nel BROWSER: l'oggetto globale è window,
// e hai accesso al documento e alle API del browser
console.log(typeof window)     // 'object'
console.log(typeof document)   // 'object'
console.log(typeof process)    // 'undefined'

// In NODE.JS: l'oggetto globale è globalThis,
// e hai accesso al filesystem e alla rete a basso livello
console.log(typeof process)    // 'object'
console.log(typeof document)   // 'undefined'

// globalThis funziona in entrambi: è il modo portabile
console.log(typeof globalThis) // 'object'
```

Il linguaggio è lo stesso; cambia cosa gli sta intorno. `Array`, `Promise`, `Math` e la sintassi appartengono a ECMAScript e ci sono ovunque. `document`, `fetch`, `localStorage` sono API del browser. `fs`, `path`, `process` sono di Node.

### Il primo script

```html
<!-- index.html -->
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <title>Primi passi</title>
  </head>
  <body>
    <h1 id="titolo">Ciao</h1>
    <button type="button" id="saluta">Saluta</button>

    <!-- type="module" abilita gli import ED È DIFFERITO per natura:
         il DOM è già pronto quando lo script parte. -->
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

```javascript
// src/main.js
const titolo = document.querySelector('#titolo')
const comando = document.querySelector('#saluta')

comando.addEventListener('click', () => {
  titolo.textContent = 'Ciao, mondo!'
})
```

```javascript
// ❌ SBAGLIATO — script classico nel <head>: il DOM non esiste ancora,
//    querySelector restituisce null e la riga dopo va in errore.
//    <head><script src="/src/main.js"></script></head>

// ✅ CORRETTO — tre modi, in ordine di preferenza:
//    1. <script type="module">   → differito per natura
//    2. <script defer src="..."> → differito esplicito
//    3. <script> in fondo al <body>
```

---

## A2. Valori e tipi

JavaScript ha **sette tipi primitivi** e un tipo oggetto. Tutto il resto — array, funzioni, date, espressioni regolari — è un oggetto.

```javascript
// I sette primitivi
const testo = 'Anna'              // string
const numero = 42                 // number
const grande = 9007199254740993n  // bigint
const vero = true                 // boolean
let nonAssegnato                  // undefined
const vuoto = null                // null
const unico = Symbol('chiave')    // symbol

// Tutto il resto è object
const oggetto = { nome: 'Anna' }
const lista = [1, 2, 3]
const funzione = () => {}
const data = new Date()
```

### `typeof` e la sua bugia storica

```javascript
console.log(typeof 'Anna')         // 'string'
console.log(typeof 42)             // 'number'
console.log(typeof 42n)            // 'bigint'
console.log(typeof true)           // 'boolean'
console.log(typeof undefined)      // 'undefined'
console.log(typeof Symbol())       // 'symbol'
console.log(typeof {})             // 'object'
console.log(typeof [])             // 'object'    ← non 'array'
console.log(typeof function () {}) // 'function'  ← caso speciale

console.log(typeof null)           // 'object'    ← IL BUG STORICO
```

`typeof null === 'object'` è un difetto della prima implementazione del 1995. Correggerlo romperebbe una quantità di codice esistente troppo grande, quindi resta. Per riconoscere `null` serve il confronto diretto:

```javascript
// Riconoscere null
const valore = null
console.log(valore === null)   // true

// Riconoscere un array
console.log(Array.isArray([]))       // true
console.log(Array.isArray({}))       // false

// Il modo generale, quando serve distinguere davvero
function tipoDi(valore) {
  return Object.prototype.toString.call(valore).slice(8, -1).toLowerCase()
}

console.log(tipoDi(null))       // 'null'
console.log(tipoDi([]))         // 'array'
console.log(tipoDi(new Date())) // 'date'
console.log(tipoDi(/ab+/))      // 'regexp'
console.log(tipoDi(new Map()))  // 'map'
```

### `null` contro `undefined`

```javascript
// undefined = "non è stato assegnato nulla".
// Lo mette il linguaggio, da solo.
let x
console.log(x)                       // undefined

function f(parametro) {
  return parametro
}
console.log(f())                     // undefined

const oggetto = {}
console.log(oggetto.inesistente)     // undefined

// null = "assenza VOLUTA di un valore".
// Lo metti tu, e comunica un'intenzione.
let utenteCollegato = null   // "so che non c'è nessuno collegato"
```

La distinzione non è formale: `undefined` significa "non lo so", `null` significa "so che non c'è". In un'API, restituire `null` per un record non trovato è diverso da restituire `undefined` per un campo che nessuno ha mai impostato.

### I numeri, e la loro precisione

```javascript
// JavaScript ha UN SOLO tipo numerico: il float a 64 bit (IEEE 754).
// Non esiste un intero separato.
console.log(1 === 1.0)   // true

// Da cui il classico:
console.log(0.1 + 0.2)           // 0.30000000000000004
console.log(0.1 + 0.2 === 0.3)   // false
```

```javascript
// ❌ SBAGLIATO — confronto diretto fra numeri in virgola mobile
// if (totale === 0.3) { ... }

// ✅ CORRETTO — confronto con tolleranza
function quasiUguali(a, b, tolleranza = Number.EPSILON) {
  return Math.abs(a - b) < tolleranza
}
console.log(quasiUguali(0.1 + 0.2, 0.3))   // true

// ✅ PER IL DENARO — mai virgola mobile. Lavora in centesimi, con interi.
const prezzoInCentesimi = 1999          // 19,99 euro
const quantita = 3
const totaleInCentesimi = prezzoInCentesimi * quantita   // 5997

// E formatta solo alla fine, per la visualizzazione
const formattatore = new Intl.NumberFormat('it-IT', {
  style: 'currency',
  currency: 'EUR',
})
console.log(formattatore.format(totaleInCentesimi / 100))   // '59,97 €'
```

```javascript
// Il limite degli interi rappresentabili esattamente
console.log(Number.MAX_SAFE_INTEGER)                  // 9007199254740991
console.log(9007199254740992 === 9007199254740993)    // true ← perdita di precisione

// BigInt per gli interi oltre quel limite
const enorme = 9007199254740993n
console.log(enorme + 1n)   // 9007199254740994n

// BigInt e Number non si mescolano: 1n + 1 solleva TypeError

// I valori speciali
console.log(1 / 0)                   // Infinity
console.log(-1 / 0)                  // -Infinity
console.log(0 / 0)                   // NaN
console.log(Number('non un numero')) // NaN

// NaN non è uguale a niente, nemmeno a sé stesso
console.log(NaN === NaN)             // false
console.log(Number.isNaN(NaN))       // true   ← il modo corretto
console.log(isNaN('testo'))          // true   ← la globale converte: evitala
console.log(Number.isNaN('testo'))   // false  ← non è NaN, è una stringa
```

### Le stringhe

```javascript
// Tre modi di scrivere una stringa
const singoli = 'con apici singoli'
const doppi = 'con apici doppi'
const modello = `template literal`

// I template literal fanno due cose in più:
const nome = 'Anna'
const eta = 34

// 1. Interpolazione
console.log(`${nome} ha ${eta} anni, l'anno prossimo ne avrà ${eta + 1}.`)

// 2. Righe multiple senza \n
const messaggio = `Gentile ${nome},
la sua fattura è disponibile.

Cordiali saluti.`

// Le stringhe sono IMMUTABILI: ogni metodo restituisce una nuova stringa
const originale = 'ciao'
console.log(originale.toUpperCase())   // 'CIAO'
console.log(originale)                 // 'ciao'  ← invariato
```

```javascript
// I metodi che userai davvero
const testo = '  Fattura 2026-0042  '

testo.trim() // 'Fattura 2026-0042'
testo.trimStart() // 'Fattura 2026-0042  '
testo.length // 21

'Fattura'.toUpperCase() // 'FATTURA'
'Fattura'.toLowerCase() // 'fattura'

'2026-0042'.split('-') // ['2026', '0042']
'2026-0042'.replace('-', '/') // '2026/0042'
'a-b-c'.replaceAll('-', '/') // 'a/b/c'

'Fattura'.includes('att') // true
'Fattura'.startsWith('Fat') // true
'Fattura'.endsWith('ura') // true
'Fattura'.indexOf('t') // 2   (-1 se assente)

'Fattura'.slice(0, 3) // 'Fat'
'Fattura'.slice(-3) // 'ura'  ← indici negativi dalla fine
'Fattura'.at(-1) // 'a'

'42'.padStart(5, '0') // '00042'
'ab'.repeat(3) // 'ababab'
```

```javascript
// Le stringhe sono sequenze di UTF-16, non di caratteri.
// Gli emoji e molti caratteri occupano due posizioni.
const emoji = '👍'
console.log(emoji.length) // 2  ← non 1
console.log([...emoji].length) // 1  ← lo spread itera per punti di codice

// Per contare i caratteri percepiti serve Intl.Segmenter
const segmentatore = new Intl.Segmenter('it', { granularity: 'grapheme' })
console.log([...segmentatore.segment('👨‍👩‍👧')].length) // 1
```

---

## A3. Variabili: `var`, `let`, `const`

```javascript
var vecchio = 'da non usare più'
let variabile = 'può essere riassegnata'
const costante = 'non può essere riassegnata'
```

### Le tre differenze che contano

```javascript
// ── 1. SCOPE ────────────────────────────────────────────────
function esempio() {
  if (true) {
    var conVar = 'visibile in tutta la funzione'
    let conLet = 'visibile solo in questo blocco'
    const conConst = 'visibile solo in questo blocco'
  }

  console.log(conVar) // 'visibile in tutta la funzione'
  // console.log(conLet)  // ReferenceError: conLet is not defined
}

// ── 2. HOISTING ─────────────────────────────────────────────
console.log(a) // undefined  ← dichiarata, non ancora assegnata
var a = 1

// console.log(b)   // ReferenceError: Cannot access 'b' before initialization
let b = 2

// ── 3. RIDICHIARAZIONE ──────────────────────────────────────
var c = 1
var c = 2 // consentito, e silenzioso

let d = 1
// let d = 2     // SyntaxError: Identifier 'd' has already been declared
```

### Hoisting e temporal dead zone

> **Analogia:** immagina che prima di eseguire una funzione qualcuno legga tutto il codice e appenda alla parete un cartello per ogni nome dichiarato. Con `var` il cartello dice "esiste, valore ancora ignoto". Con `let` e `const` il cartello dice "esiste, ma guardarlo prima della riga di dichiarazione è vietato". La zona fra l'inizio del blocco e la dichiarazione è la **temporal dead zone**: il nome esiste ma toccarlo è un errore.

```javascript
{
  // ← inizio della temporal dead zone per 'valore'
  // console.log(valore)   // ReferenceError
  let valore = 42
  // ← fine della TDZ: da qui in poi si può usare
  console.log(valore) // 42
}
```

La TDZ non è una complicazione gratuita: trasforma in errore immediato quello che con `var` era un `undefined` silenzioso che si manifestava dieci righe più in basso.

### `const` non significa immutabile

```javascript
// const impedisce la RIASSEGNAZIONE del nome,
// non la modifica del valore.
const elenco = [1, 2, 3]
elenco.push(4) // consentito: modifica l'oggetto
console.log(elenco) // [1, 2, 3, 4]

// elenco = [5, 6]      // TypeError: Assignment to constant variable

const configurazione = { porta: 3000 }
configurazione.porta = 8080 // consentito
// configurazione = {}         // TypeError
```

```javascript
// Per impedire davvero la modifica
const congelato = Object.freeze({ porta: 3000 })
congelato.porta = 8080
console.log(congelato.porta) // 3000  ← silenziosamente ignorato
//   (in strict mode è un TypeError)

// freeze è SUPERFICIALE: gli oggetti annidati restano modificabili
const config = Object.freeze({ db: { host: 'localhost' } })
config.db.host = 'altro'
console.log(config.db.host) // 'altro'  ← modificato

// Il congelamento profondo va scritto
function congelaProfondamente(oggetto) {
  for (const valore of Object.values(oggetto)) {
    if (valore && typeof valore === 'object') {
      congelaProfondamente(valore)
    }
  }
  return Object.freeze(oggetto)
}
```

**La regola operativa:** `const` sempre, `let` quando il valore deve cambiare, `var` mai. Dichiarare con `const` non è pedanteria: comunica a chi legge che quel nome non cambierà, e trasforma in errore ogni riassegnazione accidentale.

---

## A4. Operatori e coercizione di tipo

### `==` contro `===`

```javascript
// === confronta valore E tipo, senza conversioni
console.log(1 === 1) // true
console.log(1 === '1') // false

// == converte prima di confrontare, secondo regole complicate
console.log(1 == '1') // true
console.log(0 == '') // true
console.log(0 == '0') // true
console.log('' == '0') // false   ← non è nemmeno transitivo
console.log(null == undefined) // true
console.log(null === undefined) // false
console.log([] == false) // true
console.log([1] == 1) // true
console.log('0' == false) // true
```

```javascript
// Usa SEMPRE === e !==.
// L'unica eccezione difendibile: verificare null e undefined insieme.
const valore = recuperaValore()

if (valore == null) {
  // vero per null E per undefined, falso per 0, '' e false
}

// Equivalente esplicito
if (valore === null || valore === undefined) {
  // ...
}
```

### I valori falsy

Otto valori si convertono a `false`. Tutto il resto è `true`.

```javascript
// I FALSY, per intero:
//   false   0   -0   0n   ''   null   undefined   NaN

// Tutto il resto è truthy, comprese le sorprese:
console.log(Boolean([])) // true   ← array vuoto
console.log(Boolean({})) // true   ← oggetto vuoto
console.log(Boolean('0')) // true   ← stringa non vuota
console.log(Boolean('false')) // true
console.log(Boolean(-1)) // true
```

```javascript
// ❌ SBAGLIATO — 0 e '' sono valori legittimi, ma vengono scartati
function mostraQuantitaSbagliato(quantita) {
  if (!quantita) return 'Nessuna quantità indicata'
  return `Quantità: ${quantita}`
}
console.log(mostraQuantitaSbagliato(0)) // 'Nessuna quantità indicata'  ← errato

// ✅ CORRETTO — verifica ciò che intendi verificare
function mostraQuantita(quantita) {
  if (quantita == null) return 'Nessuna quantità indicata'
  return `Quantità: ${quantita}`
}
console.log(mostraQuantita(0)) // 'Quantità: 0'
```

### `||`, `??` e la differenza che conta

```javascript
// || restituisce il primo valore TRUTHY
console.log(0 || 'ripiego') // 'ripiego'   ← 0 è falsy
console.log('' || 'ripiego') // 'ripiego'
console.log(null || 'ripiego') // 'ripiego'

// ?? restituisce il primo valore che NON è null né undefined
console.log(0 ?? 'ripiego') // 0           ← 0 è un valore valido
console.log('' ?? 'ripiego') // ''
console.log(null ?? 'ripiego') // 'ripiego'
console.log(undefined ?? 'ripiego') // 'ripiego'
```

```javascript
// ❌ SBAGLIATO — l'utente che imposta 0 secondi ottiene 30
// const timeout = opzioni.timeout || 30

// ✅ CORRETTO — solo l'assenza attiva il valore predefinito
// const timeout = opzioni.timeout ?? 30
```

```javascript
// Optional chaining: interrompe se il valore è null o undefined
const utente = { indirizzo: { citta: 'Milano' } }

const citta = utente?.indirizzo?.citta // 'Milano', o undefined invece di TypeError
const primo = [1, 2]?.[0] // 1
const callback = null
const esito = callback?.() // undefined: chiama solo se esiste

// Combinato con ??
const cittaSicura = utente?.indirizzo?.citta ?? 'non indicata'
```

```javascript
// Assegnazione logica (ES2021)
const opzioni = {}
opzioni.timeout ??= 30 // assegna solo se null o undefined

const contatori = { visite: 0 }
contatori.visite ||= 10 // assegna se falsy: qui 0 diventa 10

const stato = { attivo: true }
stato.attivo &&= false // assegna solo se già truthy
```

### Gli altri operatori

```javascript
// Aritmetici
console.log(7 / 2) // 3.5   ← divisione sempre in virgola mobile
console.log(7 % 2) // 1     ← resto
console.log(2 ** 10) // 1024  ← elevamento a potenza

// Il resto di un numero negativo conserva il segno del dividendo
console.log(-7 % 3) // -1
// Per l'aritmetica modulare vera:
console.log(((-7 % 3) + 3) % 3) // 2

// Incremento: la posizione cambia il valore restituito
let n = 5
console.log(n++) // 5  ← restituisce e POI incrementa
console.log(n) // 6
console.log(++n) // 7  ← incrementa e POI restituisce

// Confronto fra stringhe: ordine lessicografico UTF-16, non alfabetico
console.log('Zebra' < 'apple') // true  ← le maiuscole vengono prima
// Per ordinare testo in italiano serve il collatore
console.log('à'.localeCompare('b', 'it')) // -1
```

---

## A5. Controllo di flusso

```javascript
const saldo = 500
let categoria

if (saldo > 1000) {
  categoria = 'premium'
} else if (saldo > 100) {
  categoria = 'standard'
} else {
  categoria = 'base'
}

// switch: il confronto è ===, e i case senza break CADONO nel successivo
const stato = 'bozza'
let permessi

switch (stato) {
  case 'bozza':
  case 'in-revisione':
    // entrambi arrivano qui: la caduta è voluta
    permessi = ['modifica', 'elimina']
    break

  case 'pubblicato':
    permessi = ['visualizza']
    break

  default:
    permessi = []
}
```

```javascript
// Le variabili dichiarate in un case appartengono a TUTTO lo switch:
// serve un blocco per isolarle.
const tipo = 'a'

switch (tipo) {
  case 'a': {
    const messaggio = 'primo'
    console.log(messaggio)
    break
  }
  case 'b': {
    const messaggio = 'secondo' // senza le graffe: SyntaxError
    console.log(messaggio)
    break
  }
}
```

### I cicli

```javascript
const fatture = [
  { numero: 1, importo: 120, pagata: true },
  { numero: 2, importo: 340, pagata: false },
  { numero: 3, importo: 90, pagata: false },
]

// for classico: quando serve l'indice o un passo diverso da 1
for (let i = 0; i < fatture.length; i++) {
  console.log(i, fatture[i].numero)
}

// for...of: itera sui VALORI. Il ciclo da preferire per gli array.
for (const fattura of fatture) {
  console.log(fattura.numero)
}

// Con l'indice, quando serve
for (const [indice, fattura] of fatture.entries()) {
  console.log(indice, fattura.numero)
}

// for...in: itera sulle CHIAVI, e risale la catena prototipale.
// Per gli oggetti, e con cautela.
const configurazione = { host: 'localhost', porta: 5432 }
for (const chiave in configurazione) {
  console.log(chiave, configurazione[chiave])
}

// Meglio ancora, senza sorprese dalla catena prototipale:
for (const [chiave, valore] of Object.entries(configurazione)) {
  console.log(chiave, valore)
}
```

```javascript
// ❌ SBAGLIATO — for...in su un array: le chiavi sono STRINGHE
const numeri = [10, 20, 30]
for (const i in numeri) {
  console.log(i + 1) // '01', '11', '21'  ← concatenazione, non somma
}

// ✅ CORRETTO
for (const n of numeri) {
  console.log(n + 1) // 11, 21, 31
}
```

```javascript
// break, continue e le etichette
const righe = [
  [1, 2],
  [3, null],
]

for (const fattura of fatture) {
  if (fattura.pagata) continue // salta al prossimo giro
  if (fattura.importo > 1000) break // esce dal ciclo
}

// Le etichette servono per uscire da cicli annidati
esterno: for (const riga of righe) {
  for (const cella of riga) {
    if (cella === null) break esterno
  }
}
```

---

## A6. Funzioni

### Le tre forme

```javascript
// 1. DICHIARAZIONE — sollevata per intero: usabile prima di dove è scritta
console.log(somma(2, 3)) // 5  ← funziona

function somma(a, b) {
  return a + b
}

// 2. ESPRESSIONE — soggetta alla TDZ come ogni const
// console.log(sottrai(5, 2))   // ReferenceError

const sottrai = function (a, b) {
  return a - b
}

// 3. ARROW FUNCTION — più concisa, e senza this proprio
const moltiplica = (a, b) => a * b

// Le varianti della sintassi arrow
const doppio = (n) => n * 2 // ritorno implicito
const identita = (n) => n // un parametro: le parentesi
//   sono opzionali, ma metterle
//   è più coerente
const nulla = () => {} // nessun parametro
const creaOggetto = (n) => ({ valore: n }) // le graffe di un oggetto vanno
//   avvolte, o sono un blocco
const lungo = (a, b) => {
  const parziale = a + b
  return parziale * 2 // con le graffe, return esplicito
}
```

### Parametri

```javascript
// Valori predefiniti — valutati a ogni chiamata
function crea(nome, opzioni = {}, creatoIl = new Date()) {
  return { nome, ...opzioni, creatoIl }
}

// Il default scatta SOLO per undefined, non per null
function saluta(nome = 'ospite') {
  return `Ciao ${nome}`
}
console.log(saluta()) // 'Ciao ospite'
console.log(saluta(undefined)) // 'Ciao ospite'
console.log(saluta(null)) // 'Ciao null'   ← null è un valore

// Rest: raccoglie i parametri restanti in un array vero
function sommaTutti(primo, ...altri) {
  return altri.reduce((totale, n) => totale + n, primo)
}
console.log(sommaTutti(1, 2, 3, 4)) // 10

// Destructuring dei parametri, con default:
// il pattern più usato per le funzioni con molte opzioni
function creaUtente({ nome, email, ruolo = 'utente', attivo = true } = {}) {
  return { nome, email, ruolo, attivo }
}

console.log(creaUtente({ nome: 'Anna', email: 'anna@example.it' }))
// { nome: 'Anna', email: 'anna@example.it', ruolo: 'utente', attivo: true }
```

```javascript
// ❌ SBAGLIATO — tre booleani posizionali: chi legge la chiamata
//    non ha idea di cosa significhino
function inviaSbagliato(messaggio, urgente, copia, tracciato) {
  // ...
}
inviaSbagliato('Ciao', true, false, true)

// ✅ CORRETTO — un oggetto di opzioni: la chiamata si autodocumenta
function invia(messaggio, { urgente = false, copia = false, tracciato = false } = {}) {
  // ...
}
invia('Ciao', { urgente: true, tracciato: true })
```

### Arrow function: la differenza sostanziale

```javascript
// Le arrow NON hanno:
//   · this proprio  → lo prendono dallo scope in cui sono scritte
//   · arguments     → usa il rest
//   · prototype     → non si possono usare con new
//   · super proprio

const oggetto = {
  nome: 'Acme',

  // Metodo normale: this è l'oggetto
  saluta() {
    return `Ciao da ${this.nome}`
  },

  // Arrow: this NON è l'oggetto, è quello dello scope esterno
  salutaSbagliato: () => {
    return `Ciao da ${this?.nome}`
  },
}

console.log(oggetto.saluta()) // 'Ciao da Acme'
console.log(oggetto.salutaSbagliato()) // 'Ciao da undefined'
```

Questo non è un difetto: è esattamente ciò che rende le arrow utili nei callback, dove vuoi che `this` resti quello esterno. Approfondiamo in [B2](#b2-this-le-cinque-regole).

---

## A7. Array e metodi funzionali

```javascript
const fatture = [
  { numero: 1, cliente: 'Rossi', importo: 1200, pagata: true },
  { numero: 2, cliente: 'Bianchi', importo: 340, pagata: false },
  { numero: 3, cliente: 'Rossi', importo: 890, pagata: false },
  { numero: 4, cliente: 'Verdi', importo: 2100, pagata: true },
]
```

### I metodi che trasformano

```javascript
// map: da N elementi a N elementi, trasformati
const numeri = fatture.map((f) => f.numero)
// [1, 2, 3, 4]

const riepiloghi = fatture.map((f) => `#${f.numero} ${f.cliente}: ${f.importo} euro`)

// filter: da N elementi a M <= N, secondo una condizione
const insolute = fatture.filter((f) => !f.pagata)
// [{numero: 2, ...}, {numero: 3, ...}]

// reduce: da N elementi a UN valore di qualunque forma
const totale = fatture.reduce((somma, f) => somma + f.importo, 0)
// 4530

// reduce che produce un oggetto: raggruppare
const perCliente = fatture.reduce((gruppi, f) => {
  gruppi[f.cliente] ??= []
  gruppi[f.cliente].push(f)
  return gruppi
}, {})
// { Rossi: [...], Bianchi: [...], Verdi: [...] }

// Dal 2024 esiste il metodo nativo per raggruppare
const perCliente2 = Object.groupBy(fatture, (f) => f.cliente)
const perStato = Object.groupBy(fatture, (f) => (f.pagata ? 'pagate' : 'insolute'))
```

### I metodi che cercano

```javascript
fatture.find((f) => f.numero === 3) // l'ELEMENTO, o undefined
fatture.findIndex((f) => f.numero === 3) // l'INDICE, o -1
fatture.findLast((f) => !f.pagata) // dall'ultimo
fatture.some((f) => !f.pagata) // true se ALMENO UNO soddisfa
fatture.every((f) => f.importo > 0) // true se TUTTI soddisfano
fatture.includes(fatture[0]) // confronto per identità

// Su array di primitivi
console.log([1, 2, 3].includes(2)) // true
console.log([1, 2, 3].indexOf(2)) // 1
```

```javascript
// some ed every su array vuoti
console.log([].some(() => true)) // false
console.log([].every(() => false)) // true   ← "vacuamente vero"
```

### I metodi che modificano l'originale

```javascript
const lista = [3, 1, 2]

// QUESTI MODIFICANO l'array su cui li chiami:
lista.push(4) // aggiunge in fondo, restituisce la nuova lunghezza
lista.pop() // toglie l'ultimo, lo restituisce
lista.unshift(0) // aggiunge in testa
lista.shift() // toglie il primo
lista.splice(1, 2) // rimuove 2 elementi dall'indice 1
lista.sort() // ordina IN PLACE
lista.reverse() // inverte IN PLACE

// QUESTI restituiscono un nuovo array, lasciando l'originale intatto:
lista.slice(1, 3) // porzione
lista.concat([5, 6]) // concatenazione
lista.toSorted() // ordinamento (ES2023)
lista.toReversed() // inversione (ES2023)
lista.toSpliced(1, 2) // splice (ES2023)
lista.with(0, 99) // sostituisce un elemento (ES2023)
lista.flat(2) // appiattisce
lista.flatMap((n) => [n, n * 2])
```

```javascript
// ❌ SBAGLIATO — sort modifica l'originale, e chi lo aveva
//    ricevuto si trova l'ordine cambiato sotto i piedi
function ordinaPerImportoSbagliato(elenco) {
  return elenco.sort((a, b) => a.importo - b.importo)
}

// ✅ CORRETTO — toSorted non tocca l'originale
function ordinaPerImporto(elenco) {
  return elenco.toSorted((a, b) => a.importo - b.importo)
}

// ✅ ALTERNATIVA compatibile con basi installate più datate
function ordinaPerImportoCompatibile(elenco) {
  return [...elenco].sort((a, b) => a.importo - b.importo)
}
```

### `sort` e la sua trappola

```javascript
// Senza funzione di confronto, sort converte tutto in STRINGA
console.log([10, 9, 100, 1].sort())
// [1, 10, 100, 9]   ← ordine lessicografico

// Numeri
console.log([10, 9, 100, 1].toSorted((a, b) => a - b)) // [1, 9, 10, 100]

// Stringhe in italiano — localeCompare gestisce gli accenti
console.log(['àbaco', 'zebra', 'Ancona'].toSorted((a, b) => a.localeCompare(b, 'it')))

// Oggetti, per più criteri
const ordinate = fatture.toSorted(
  (a, b) => Number(a.pagata) - Number(b.pagata) || b.importo - a.importo,
)
// prima le insolute, e dentro ogni gruppo per importo decrescente
```

### Concatenare le operazioni

```javascript
// Leggibile: ogni passo fa una cosa sola
const totaleInsolutoRossi = fatture
  .filter((f) => f.cliente === 'Rossi')
  .filter((f) => !f.pagata)
  .reduce((somma, f) => somma + f.importo, 0)
// 890
```

```javascript
// Ogni passo crea un array intermedio. Su array di milioni di elementi
// conviene un ciclo solo, o reduce. Su array di centinaia, la
// leggibilità vale più della differenza.
const totale = fatture.reduce(
  (somma, f) => (f.cliente === 'Rossi' && !f.pagata ? somma + f.importo : somma),
  0,
)
```

---

## A8. Oggetti

```javascript
// Letterale
const utente = {
  nome: 'Anna',
  email: 'anna@example.it',
  eta: 34,

  // Metodo (forma breve)
  saluta() {
    return `Ciao, sono ${this.nome}`
  },

  // Proprietà calcolata
  ['chiave' + 'Dinamica']: 'valore',
}

// Forma breve quando nome della variabile e della proprietà coincidono
const nome = 'Anna'
const eta = 34
const persona = { nome, eta } // { nome: 'Anna', eta: 34 }
```

### Accedere, aggiungere, rimuovere

```javascript
// Due notazioni
utente.nome // punto: quando il nome è noto e valido
utente['nome'] // parentesi: quando il nome è in una variabile
//   o contiene caratteri non validi

const campo = 'email'
utente[campo] // 'anna@example.it'

// Aggiungere e modificare
utente.telefono = '02 1234567'
utente['codice fiscale'] = 'RSSNNA90A41F205X'

// Rimuovere
delete utente.telefono

// Verificare l'esistenza
console.log('nome' in utente) // true, anche ereditate
console.log(Object.hasOwn(utente, 'nome')) // true, solo proprie (ES2022)
```

### Iterare

```javascript
const configurazione = { host: 'localhost', porta: 5432, ssl: false }

Object.keys(configurazione) // ['host', 'porta', 'ssl']
Object.values(configurazione) // ['localhost', 5432, false]
Object.entries(configurazione) // [['host', 'localhost'], ['porta', 5432], ...]

for (const [chiave, valore] of Object.entries(configurazione)) {
  console.log(`${chiave} = ${valore}`)
}

// Da coppie a oggetto
const coppie = [
  ['a', 1],
  ['b', 2],
]
console.log(Object.fromEntries(coppie)) // { a: 1, b: 2 }

// Il pattern che serve spesso: trasformare i valori di un oggetto
const raddoppiati = Object.fromEntries(
  Object.entries({ a: 1, b: 2 }).map(([k, v]) => [k, v * 2]),
)
// { a: 2, b: 4 }
```

### Copiare

```javascript
const originale = { nome: 'Anna', indirizzo: { citta: 'Milano' } }

// Copia SUPERFICIALE: il primo livello è copiato,
// gli oggetti annidati sono CONDIVISI
const copia1 = { ...originale }
const copia2 = Object.assign({}, originale)

copia1.nome = 'Marco'
console.log(originale.nome) // 'Anna'   ← indipendente

copia1.indirizzo.citta = 'Torino'
console.log(originale.indirizzo.citta) // 'Torino' ← CONDIVISO

// Copia PROFONDA
const profonda = structuredClone(originale)
profonda.indirizzo.citta = 'Roma'
console.log(originale.indirizzo.citta) // 'Torino' ← indipendente
```

```javascript
// structuredClone NON copia:
//   funzioni, Symbol, prototipi, getter/setter, nodi del DOM
// structuredClone({ f: () => {} })   // DataCloneError

// Il vecchio trucco JSON perde molto di più:
const perso = JSON.parse(
  JSON.stringify({
    data: new Date(), // → stringa
    indefinito: undefined, // → sparisce
    nan: NaN, // → null
  }),
)
```

### Unire

```javascript
const predefinite = { porta: 3000, host: 'localhost', debug: false }
const scelte = { porta: 8080 }

// Lo spread: le proprietà successive VINCONO
const finali = { ...predefinite, ...scelte }
// { porta: 8080, host: 'localhost', debug: false }

// L'unione è SUPERFICIALE: un oggetto annidato viene sostituito, non fuso
const a = { db: { host: 'localhost', porta: 5432 } }
const b = { db: { porta: 5433 } }
console.log({ ...a, ...b })
// { db: { porta: 5433 } }   ← host è sparito
```

---

## A9. Destructuring, spread e rest

### Destructuring di oggetti

```javascript
const utente = { nome: 'Anna', email: 'anna@example.it', eta: 34, ruolo: 'admin' }

// Estrazione base
const { nome, email } = utente

// Rinominare
const { nome: nomeUtente } = utente

// Valore predefinito, se la proprietà è undefined
const { telefono = 'non indicato' } = utente

// Rinominare E dare un default
const { citta: cittaResidenza = 'non indicata' } = utente

// Rest: tutto il resto in un oggetto nuovo
const { nome: n, ...altriCampi } = utente
// altriCampi = { email, eta, ruolo }

// Annidato
const risposta = { dati: { utente: { nome: 'Anna' } } }
const {
  dati: {
    utente: { nome: nomeAnnidato },
  },
} = risposta

// Annidato con protezione dall'assenza
const { dati: { utente: { nome: sicuro } = {} } = {} } = risposta ?? {}
```

### Destructuring di array

```javascript
const coordinate = [45.4642, 9.19]

const [latitudine, longitudine] = coordinate

// Saltare posizioni
const [primo, , terzo] = [1, 2, 3]

// Rest
const [testa, ...coda] = [1, 2, 3, 4]
// testa = 1, coda = [2, 3, 4]

// Default
const [a = 0, b = 0] = [5]
// a = 5, b = 0

// Scambio senza variabile temporanea
let x = 1
let y = 2
;[x, y] = [y, x]
```

```javascript
// Il punto e virgola prima di [ o ( è necessario quando la riga
// precedente non lo ha: senza, JavaScript legge una continuazione.
// const valore = calcola()
// ;[x, y] = [y, x]   // senza il ; iniziale: calcola()[x, y] = ...
```

### Spread

```javascript
// Array
const a1 = [1, 2]
const b1 = [3, 4]
const uniti = [...a1, ...b1] // [1, 2, 3, 4]
const conAggiunta = [0, ...a1, 99] // [0, 1, 2, 99]

// Copia superficiale
const copia = [...a1]

// Da iterabile ad array
const caratteri = [...'ciao'] // ['c', 'i', 'a', 'o']
const daSet = [...new Set([1, 1, 2])] // [1, 2]
const daNodeList = [...document.querySelectorAll('p')]

// Argomenti di funzione
const numeri = [5, 2, 9]
console.log(Math.max(...numeri)) // 9

// Oggetti
const base = { a: 1 }
const esteso = { ...base, b: 2 }
```

### Il pattern del destructuring nei parametri

```javascript
// Il modo standard di scrivere una funzione con opzioni
async function recuperaDati(
  url,
  { metodo = 'GET', intestazioni = {}, timeout = 5000, segnale } = {},
) {
  const controller = new AbortController()
  const scadenza = setTimeout(() => controller.abort(), timeout)

  try {
    return await fetch(url, {
      method: metodo,
      headers: intestazioni,
      signal: segnale ?? controller.signal,
    })
  } finally {
    clearTimeout(scadenza)
  }
}

// La chiamata si legge senza consultare la firma
// await recuperaDati('/api/fatture', { timeout: 10_000 })
```

L'`= {}` finale non è opzionale: senza, chiamare `recuperaDati(url)` senza secondo argomento tenterebbe di destrutturare `undefined` e solleverebbe un `TypeError`.

---

# Parte B — Comprensione Profonda

---

## B1. Scope lessicale e closure

Lo scope in JavaScript è **lessicale**: deciso da *dove il codice è scritto*, non da dove viene chiamato. Questa singola frase spiega le closure, e le closure spiegano metà del JavaScript che incontrerai.

```javascript
const globale = 'sono globale'

function esterna() {
  const dellEsterna = 'sono dell esterna'

  function interna() {
    const dellInterna = 'sono dell interna'

    // interna vede: dellInterna, dellEsterna, globale
    console.log(dellInterna, dellEsterna, globale)
  }

  interna()
  // esterna NON vede dellInterna
}
```

```
La catena di scope si risale verso l'ESTERNO, mai verso l'interno:

    ┌──────────────────────────────────────────┐
    │  scope globale                           │
    │    globale                               │
    │  ┌────────────────────────────────────┐  │
    │  │  scope di esterna()                │  │
    │  │    dellEsterna                     │  │
    │  │  ┌──────────────────────────────┐  │  │
    │  │  │  scope di interna()          │  │  │
    │  │  │    dellInterna               │  │  │
    │  │  │                              │  │  │
    │  │  │  cerca qui, poi sopra,       │  │  │
    │  │  │  poi ancora sopra            │  │  │
    │  │  └──────────────────────────────┘  │  │
    │  └────────────────────────────────────┘  │
    └──────────────────────────────────────────┘
```

### Cos'è una closure

> **Analogia:** una funzione che parte per un viaggio si porta dietro uno zaino con tutte le variabili dello scope in cui è nata. Anche quando quello scope non esiste più — la funzione che lo conteneva è finita da un pezzo — lo zaino resta pieno, e la funzione continua a leggerci dentro. Quello zaino è la closure.

```javascript
function creaContatore(partenza = 0) {
  // 'valore' vive nello scope di creaContatore
  let valore = partenza

  // Le funzioni restituite portano con sé quello scope
  return {
    incrementa() {
      valore++
      return valore
    },
    leggi() {
      return valore
    },
    azzera() {
      valore = partenza
    },
  }
}

const contatore = creaContatore(10)
console.log(contatore.incrementa()) // 11
console.log(contatore.incrementa()) // 12
console.log(contatore.leggi()) // 12

// 'valore' NON è raggiungibile dall'esterno: è privato per costruzione
console.log(contatore.valore) // undefined
```

`creaContatore` è finita da tempo, eppure `valore` esiste ancora. Non è magia: finché una funzione che lo referenzia è viva, il garbage collector non può liberare quello scope.

### Ogni chiamata crea una closure nuova

```javascript
const primo = creaContatore(0)
const secondo = creaContatore(100)

primo.incrementa() // 1
secondo.incrementa() // 101

console.log(primo.leggi()) // 1   ← indipendenti
console.log(secondo.leggi()) // 101
```

### La trappola classica del ciclo

```javascript
// ❌ SBAGLIATO — con var esiste UNA SOLA variabile i,
//    condivisa da tutte e tre le funzioni.
//    Alla fine del ciclo vale 3.
const sbagliate = []
for (var i = 0; i < 3; i++) {
  sbagliate.push(() => console.log(i))
}
sbagliate[0]() // 3
sbagliate[1]() // 3
sbagliate[2]() // 3
```

```javascript
// ✅ CORRETTO — let crea una variabile NUOVA a ogni giro del ciclo.
//    È un comportamento specifico di let nei cicli for.
const corrette = []
for (let i = 0; i < 3; i++) {
  corrette.push(() => console.log(i))
}
corrette[0]() // 0
corrette[1]() // 1
corrette[2]() // 2
```

```javascript
// La soluzione storica, prima di let: una IIFE per creare uno scope
const conIife = []
for (var j = 0; j < 3; j++) {
  conIife.push(
    (function (catturato) {
      return () => console.log(catturato)
    })(j),
  )
}
```

### I pattern che le closure rendono possibili

```javascript
// 1. Stato privato — il modulo, prima che i moduli esistessero
const gestoreSessione = (function () {
  let token = null
  let scadenza = null

  return {
    imposta(nuovoToken, secondi) {
      token = nuovoToken
      scadenza = Date.now() + secondi * 1000
    },
    valido() {
      return token !== null && Date.now() < scadenza
    },
    pulisci() {
      token = null
      scadenza = null
    },
  }
})()

// 2. Memoizzazione — la cache vive nella closure
function memoizza(funzione) {
  const cache = new Map()

  return function (...argomenti) {
    const chiave = JSON.stringify(argomenti)
    if (cache.has(chiave)) return cache.get(chiave)

    const risultato = funzione.apply(this, argomenti)
    cache.set(chiave, risultato)
    return risultato
  }
}

const fibonacci = memoizza(function fib(n) {
  return n < 2 ? n : fibonacci(n - 1) + fibonacci(n - 2)
})

console.log(fibonacci(40)) // istantaneo invece di ~1 secondo

// 3. Debounce — il timer vive nella closure
function debounce(funzione, attesa = 300) {
  let temporizzatore = null

  return function (...argomenti) {
    clearTimeout(temporizzatore)
    temporizzatore = setTimeout(() => funzione.apply(this, argomenti), attesa)
  }
}

const cercaConRitardo = debounce((termine) => {
  console.log('cerco', termine)
}, 500)

// 4. Throttle — l'ultimo istante di esecuzione vive nella closure
function throttle(funzione, intervallo = 200) {
  let ultimaEsecuzione = 0

  return function (...argomenti) {
    const adesso = Date.now()
    if (adesso - ultimaEsecuzione < intervallo) return

    ultimaEsecuzione = adesso
    return funzione.apply(this, argomenti)
  }
}
```

**Debounce o throttle?** Debounce aspetta che l'utente si fermi — per il campo di ricerca, dove vuoi una richiesta sola alla fine. Throttle esegue al massimo una volta ogni N millisecondi — per lo scorrimento e il ridimensionamento, dove vuoi aggiornamenti regolari ma non sessanta al secondo.

---

## B2. `this`: le cinque regole

`this` non dipende da dove la funzione è scritta: dipende da **come viene chiamata**. Cinque regole, in ordine di precedenza.

```javascript
// ── REGOLA 1: new binding ───────────────────────────────────
// Con new, this è l'oggetto appena creato
function Utente(nome) {
  this.nome = nome
}
const u = new Utente('Anna')
console.log(u.nome) // 'Anna'

// ── REGOLA 2: binding esplicito ─────────────────────────────
// call, apply e bind impongono this
function saluta(saluto) {
  return `${saluto}, ${this.nome}`
}

const persona = { nome: 'Anna' }

console.log(saluta.call(persona, 'Ciao')) // argomenti separati
console.log(saluta.apply(persona, ['Ciao'])) // argomenti in un array
const legata = saluta.bind(persona) // restituisce una funzione NUOVA
console.log(legata('Ciao'))

// ── REGOLA 3: binding implicito ─────────────────────────────
// Chiamata come metodo: this è l'oggetto PRIMA DEL PUNTO
const oggetto = {
  nome: 'Acme',
  saluta() {
    return `Ciao da ${this.nome}`
  },
}
console.log(oggetto.saluta()) // 'Ciao da Acme'

// ── REGOLA 4: binding predefinito ───────────────────────────
// Chiamata semplice: undefined in strict mode (e nei moduli),
// l'oggetto globale altrimenti
function libera() {
  return this
}
console.log(libera()) // undefined nei moduli ES

// ── REGOLA 5: arrow function ────────────────────────────────
// Le arrow NON hanno this: lo ereditano dallo scope in cui sono SCRITTE.
// Questa regola VINCE su tutte le altre: nemmeno bind la cambia.
const conArrow = {
  nome: 'Acme',
  saluta: () => `Ciao da ${this?.nome}`, // this è quello esterno
}
console.log(conArrow.saluta()) // 'Ciao da undefined'
```

### Il `this` perduto

È l'errore più frequente con `this`, e vale la pena vederlo per intero.

```javascript
const contatore = {
  valore: 0,
  incrementa() {
    this.valore++
    console.log(this.valore)
  },
}

contatore.incrementa() // 1  ← funziona: c'è il punto

// ❌ Passando il METODO come callback, si perde l'oggetto prima del punto
const comando = document.querySelector('#incrementa')
comando.addEventListener('click', contatore.incrementa)
// TypeError: Cannot read properties of undefined (reading 'valore')
// this ora è l'elemento del DOM, non 'contatore'
```

```javascript
// ✅ Tre soluzioni, in ordine di preferenza

// 1. Arrow che chiama il metodo — la più leggibile
comando.addEventListener('click', () => contatore.incrementa())

// 2. bind — restituisce una funzione con this fissato
comando.addEventListener('click', contatore.incrementa.bind(contatore))

// 3. Campo di classe come arrow — this è legato alla creazione
class Contatore {
  valore = 0

  // Metodo normale: this dipende dalla chiamata
  incrementa() {
    this.valore++
  }

  // Campo arrow: this è SEMPRE l'istanza
  incrementaLegato = () => {
    this.valore++
  }
}

const c = new Contatore()
comando.addEventListener('click', c.incrementaLegato) // funziona
```

### `this` nei gestori di eventi

```javascript
const comando = document.querySelector('#salva')

// Funzione normale: this è l'elemento su cui è registrato il listener
comando.addEventListener('click', function (evento) {
  console.log(this === comando) // true
  console.log(this === evento.currentTarget) // true
})

// Arrow: this è quello dello scope esterno
comando.addEventListener('click', (evento) => {
  console.log(this === comando) // false
  // Usa evento.currentTarget invece di this
  console.log(evento.currentTarget === comando) // true
})
```

**La regola operativa:** usa `evento.currentTarget` invece di `this`. Funziona con entrambe le forme, ed elimina la domanda.

### `call`, `apply`, `bind` a confronto

```javascript
function descrivi(prefisso, suffisso) {
  return `${prefisso} ${this.nome} ${suffisso}`
}

const azienda = { nome: 'Acme' }

// call: chiama SUBITO, argomenti separati da virgole
descrivi.call(azienda, 'La', 'S.p.A.') // 'La Acme S.p.A.'

// apply: chiama SUBITO, argomenti in un array
descrivi.apply(azienda, ['La', 'S.p.A.']) // 'La Acme S.p.A.'

// bind: NON chiama, restituisce una funzione nuova
const descriviAcme = descrivi.bind(azienda, 'La')
descriviAcme('S.p.A.') // 'La Acme S.p.A.'  ← applicazione parziale
```

```javascript
// bind non si può "slegare": il primo bind vince
function f() {
  return this.x
}
const legataUnaVolta = f.bind({ x: 1 })
const legataDueVolte = legataUnaVolta.bind({ x: 2 })
console.log(legataDueVolte()) // 1  ← non 2
```

---

## B3. Prototipi e catena prototipale

JavaScript non ha classi nel senso di Java o C++. Ha **oggetti che delegano ad altri oggetti**. La sintassi `class` che vedrai in [B4](#b4-classi-cosa-sono-davvero) è zucchero sintattico sopra questo meccanismo.

> **Analogia:** una biblioteca a scaffali sovrapposti. Cerchi un libro sul tuo scaffale; se non c'è, sali a quello sopra; se non c'è nemmeno lì, sali ancora, fino a raggiungere lo scaffale radice. Se non lo trovi da nessuna parte, la risposta è `undefined`. Ogni oggetto ha un collegamento verso lo scaffale superiore: quello è il suo prototipo.

```javascript
const animale = {
  respira() {
    return `${this.nome} respira`
  },
}

const cane = Object.create(animale) // il prototipo di cane è animale
cane.nome = 'Fido'
cane.abbaia = function () {
  return `${this.nome} abbaia`
}

console.log(cane.abbaia()) // 'Fido abbaia'   ← proprietà propria
console.log(cane.respira()) // 'Fido respira'  ← trovata sul prototipo
```

```
La catena prototipale:

    cane                    { nome: 'Fido', abbaia: f }
      │  [[Prototype]]
      ▼
    animale                 { respira: f }
      │  [[Prototype]]
      ▼
    Object.prototype        { toString, hasOwnProperty, valueOf, ... }
      │  [[Prototype]]
      ▼
    null                    ← la fine della catena

Cercando cane.respira:
  1. su cane?             no
  2. su animale?          SÌ → usa questo
Cercando cane.toString:
  1. su cane?             no
  2. su animale?          no
  3. su Object.prototype? SÌ → usa questo
Cercando cane.vola:
  ... fino a null → undefined
```

### Ispezionare e modificare la catena

```javascript
// Leggere il prototipo
Object.getPrototypeOf(cane) === animale // true
cane.__proto__ === animale // true, ma __proto__ è deprecato

// Impostarlo alla creazione — il modo da preferire
const gatto = Object.create(animale)

// Impostarlo dopo — legale, ma deottimizza l'oggetto in V8: evitalo
// Object.setPrototypeOf(gatto, altroPrototipo)

// Verificare l'appartenenza alla catena
console.log(animale.isPrototypeOf(cane)) // true
console.log(cane instanceof Object) // true

// Distinguere proprie ed ereditate
console.log(Object.hasOwn(cane, 'nome')) // true
console.log(Object.hasOwn(cane, 'respira')) // false
console.log('respira' in cane) // true  ← anche ereditate

// Solo le proprie
console.log(Object.keys(cane)) // ['nome', 'abbaia']
```

### Un oggetto senza prototipo

```javascript
// Utile per le mappe di dati arbitrari: nessuna proprietà ereditata
// può confliggere con le chiavi.
const dizionario = Object.create(null)
dizionario.toString = 'un valore qualunque' // nessun conflitto

// Da ES2022 esiste una forma diretta
const dizionario2 = { __proto__: null }

// Attenzione: senza prototipo non ci sono i metodi di Object.prototype
// dizionario.hasOwnProperty('x')   // TypeError
console.log(Object.hasOwn(dizionario, 'toString')) // true — la forma statica funziona
```

### Le funzioni costruttrici, prima delle classi

```javascript
// Il modo pre-ES6 di creare "classi". Lo incontri nel codice esistente.
function Utente(nome, email) {
  // this è l'oggetto nuovo creato da new
  this.nome = nome
  this.email = email
}

// I metodi vanno sul PROTOTIPO, non nel costruttore:
// così esiste una copia sola condivisa da tutte le istanze
Utente.prototype.descrivi = function () {
  return `${this.nome} <${this.email}>`
}

const anna = new Utente('Anna', 'anna@example.it')
console.log(anna.descrivi()) // 'Anna <anna@example.it>'
```

```javascript
// ❌ SBAGLIATO — un metodo dentro il costruttore crea una funzione
//    NUOVA per ogni istanza: mille utenti, mille copie identiche
function UtenteSbagliato(nome) {
  this.nome = nome
  this.descrivi = function () {
    return this.nome
  }
}

// ✅ CORRETTO — sul prototipo: una copia sola
function UtenteCorretto(nome) {
  this.nome = nome
}
UtenteCorretto.prototype.descrivi = function () {
  return this.nome
}
```

```
Cosa fa `new`, in quattro passi:

  1. crea un oggetto vuoto
  2. ne imposta il [[Prototype]] a Costruttore.prototype
  3. chiama il costruttore con this = quell'oggetto
  4. restituisce l'oggetto, a meno che il costruttore
     non restituisca esplicitamente un altro oggetto
```

---

## B4. Classi: cosa sono davvero

```javascript
class Utente {
  // Campi privati: il # è parte del nome, e l'accesso dall'esterno
  // è un errore di sintassi, non una convenzione
  #passwordHash

  // Campi pubblici
  attivo = true

  // Campo statico: appartiene alla classe, non alle istanze
  static contatore = 0

  constructor(nome, email) {
    this.nome = nome
    this.email = email
    Utente.contatore++
  }

  // Metodo: finisce su Utente.prototype
  descrivi() {
    return `${this.nome} <${this.email}>`
  }

  // Getter e setter: si usano come proprietà
  get dominio() {
    return this.email.split('@')[1]
  }

  set nomeCompleto(valore) {
    const parti = valore.trim().split(/\s+/)
    this.nome = parti[0]
    this.cognome = parti.slice(1).join(' ')
  }

  // Metodo privato
  #verificaPassword(candidata) {
    return this.#passwordHash === candidata
  }

  accedi(password) {
    return this.#verificaPassword(password)
  }

  // Metodo statico: costruttore alternativo, il caso d'uso più comune
  static daJson(json) {
    const dati = JSON.parse(json)
    return new Utente(dati.nome, dati.email)
  }

  // Blocco di inizializzazione statica (ES2022)
  static {
    Utente.creataIl = new Date()
  }
}

const anna = new Utente('Anna', 'anna@example.it')
console.log(anna.descrivi()) // 'Anna <anna@example.it>'
console.log(anna.dominio) // 'example.it'  ← senza parentesi
anna.nomeCompleto = 'Anna Maria Rossi'
console.log(anna.cognome) // 'Maria Rossi'
console.log(Utente.contatore) // 1
```

### `class` è zucchero sintattico

```javascript
// Queste due scritture producono la stessa struttura
class A {
  metodo() {}
}

function B() {}
B.prototype.metodo = function () {}

console.log(typeof A) // 'function'  ← una classe È una funzione
console.log(Object.getOwnPropertyNames(A.prototype)) // ['constructor', 'metodo']
```

**Le differenze che non sono solo sintassi:**

```javascript
// 1. Le classi NON sono sollevate come le dichiarazioni di funzione
// new C()   // ReferenceError: Cannot access 'C' before initialization
class C {}

// 2. Il corpo di una classe è sempre in strict mode

// 3. I metodi non sono enumerabili: non compaiono in for...in

// 4. Chiamare una classe senza new è un errore
// C()   // TypeError: Class constructor C cannot be invoked without 'new'
```

### Ereditarietà

```javascript
class Persona {
  constructor(nome) {
    this.nome = nome
  }

  saluta() {
    return `Ciao, sono ${this.nome}`
  }

  descrivi() {
    return this.saluta()
  }
}

class Dipendente extends Persona {
  constructor(nome, ruolo) {
    // super() DEVE essere chiamato prima di toccare this
    super(nome)
    this.ruolo = ruolo
  }

  // Override, con richiamo al metodo del genitore
  saluta() {
    return `${super.saluta()}, ${this.ruolo}`
  }
}

const marco = new Dipendente('Marco', 'sviluppatore')
console.log(marco.saluta()) // 'Ciao, sono Marco, sviluppatore'

// descrivi() è definito su Persona ma chiama this.saluta():
// la ricerca parte dall'istanza, quindi trova la versione di Dipendente
console.log(marco.descrivi()) // 'Ciao, sono Marco, sviluppatore'
```

```javascript
// ❌ SBAGLIATO — this prima di super()
class Sbagliata extends Persona {
  constructor(nome) {
    this.qualcosa = 1 // ReferenceError
    super(nome)
  }
}
```

### Composizione invece di ereditarietà

```javascript
// Le gerarchie profonde diventano fragili: un cambiamento in cima
// si propaga a tutti i discendenti in modi difficili da prevedere.

// ❌ Ereditarietà per riuso del codice
class Base {}
class Intermedia extends Base {}
class Specifica extends Intermedia {}
class MoltoSpecifica extends Specifica {} // quattro livelli: già troppi

// ✅ Composizione — l'oggetto ha le capacità, non le eredita
function conRegistrazione(oggetto) {
  return {
    ...oggetto,
    registra(messaggio) {
      console.log(`[${new Date().toISOString()}] ${messaggio}`)
    },
  }
}

function conValidazione(oggetto, regole) {
  return {
    ...oggetto,
    valida() {
      return Object.entries(regole).every(([campo, regola]) => regola(oggetto[campo]))
    },
  }
}

const servizio = conValidazione(conRegistrazione({ nome: 'importazione' }), {
  nome: (v) => typeof v === 'string' && v.length > 0,
})
```

La regola pratica: **l'ereditarietà esprime "è un"**, la composizione esprime "ha un" o "sa fare". Un `Dipendente` *è una* `Persona`: l'ereditarietà è corretta. Un servizio *sa* registrare: la composizione è corretta.

---

## B5. Il DOM: selezionare, creare, modificare

### Selezionare

```javascript
// I due metodi che coprono tutto
const uno = document.querySelector('.scheda') // il PRIMO che corrisponde, o null
const tutti = document.querySelectorAll('.scheda') // una NodeList statica

// Qualunque selettore CSS funziona
document.querySelector('#modulo input[type="email"]:required')
document.querySelector('article:has(img)')

// I metodi storici, ancora utili in un caso specifico
document.getElementById('titolo') // più veloce, ma solo per id
const vive = document.getElementsByClassName('scheda') // HTMLCollection VIVA

// Cercare DENTRO un elemento, non in tutto il documento
const scheda = document.querySelector('.scheda')
const titoloDentro = scheda.querySelector('h3')

// Risalire e spostarsi
elemento.closest('.scheda') // il primo antenato che corrisponde
elemento.parentElement
elemento.children // solo elementi
elemento.nextElementSibling
elemento.previousElementSibling
```

```javascript
// NodeList statica contro HTMLCollection viva — la differenza morde
const statica = document.querySelectorAll('.voce') // fotografia
const viva = document.getElementsByClassName('voce') // sempre aggiornata

console.log(statica.length) // 3
console.log(viva.length) // 3

document.body.append(document.createElement('div'))
// (con class="voce")

console.log(statica.length) // 3  ← non cambia
console.log(viva.length) // 4  ← cambiata
```

```javascript
// ❌ SBAGLIATO — ciclo su una collezione VIVA che stai modificando:
//    ogni rimozione accorcia la collezione e l'indice salta un elemento
const vive2 = document.getElementsByClassName('da-rimuovere')
for (let i = 0; i < vive2.length; i++) {
  vive2[i].remove()
}

// ✅ CORRETTO — querySelectorAll restituisce una fotografia
for (const elemento of document.querySelectorAll('.da-rimuovere')) {
  elemento.remove()
}
```

### Modificare il contenuto

```javascript
const elemento = document.querySelector('#messaggio')

// textContent — testo puro, NON interpreta markup.
// È la scelta predefinita, ed è sicura per definizione.
elemento.textContent = '<b>non diventa grassetto</b>'

// innerHTML — interpreta il markup. Pericoloso con dati non fidati.
elemento.innerHTML = '<b>diventa grassetto</b>'

// innerText — come textContent ma tiene conto dello stile:
// salta gli elementi nascosti e forza un ricalcolo del layout.
// Più lento: usalo solo quando ti serve davvero il testo "come si vede".
console.log(elemento.innerText)
```

```javascript
// ❌ SBAGLIATO — cross-site scripting: il commento arriva dall'utente
elemento.innerHTML = commentoUtente

// ✅ CORRETTO — testo puro
elemento.textContent = commentoUtente

// ✅ CORRETTO quando serve davvero del markup limitato
// import DOMPurify from 'dompurify'
// elemento.innerHTML = DOMPurify.sanitize(commentoUtente, {
//   ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
//   ALLOWED_ATTR: ['href'],
// })
```

### Creare

```javascript
// Il modo esplicito
const scheda = document.createElement('article')
scheda.className = 'scheda'
scheda.dataset.id = '42' // → data-id="42"

const titolo = document.createElement('h3')
titolo.textContent = 'Fattura 2026-0042'
scheda.append(titolo)

document.querySelector('#elenco').append(scheda)
```

```javascript
// I metodi di inserimento
genitore.append(figlio) // in fondo, accetta più nodi e stringhe
genitore.prepend(figlio) // in testa
elemento.before(nuovo) // come fratello precedente
elemento.after(nuovo) // come fratello successivo
elemento.replaceWith(nuovo) // sostituisce
elemento.remove() // si rimuove da solo

// I metodi storici, più verbosi
genitore.appendChild(figlio) // accetta UN nodo solo
genitore.insertBefore(nuovo, riferimento)
genitore.removeChild(figlio)
```

### Inserire molti elementi senza far ricalcolare il layout

```javascript
// ❌ SBAGLIATO — mille inserimenti nel documento vivo:
//    il browser può ricalcolare il layout a ogni giro
const elenco = document.querySelector('#elenco')
for (const fattura of milleFatture) {
  const riga = document.createElement('li')
  riga.textContent = fattura.numero
  elenco.append(riga) // ← nel DOM vivo, mille volte
}

// ✅ CORRETTO — un frammento fuori dal documento, un solo inserimento
const frammento = document.createDocumentFragment()
for (const fattura of milleFatture) {
  const riga = document.createElement('li')
  riga.textContent = fattura.numero
  frammento.append(riga)
}
elenco.append(frammento) // ← una volta sola

// ✅ ALTERNATIVA — una sola assegnazione, quando i dati sono fidati
elenco.innerHTML = milleFatture.map((f) => `<li>${f.numero}</li>`).join('')
```

### Attributi, classi, stili, dati

```javascript
const elemento = document.querySelector('.scheda')

// Attributi
elemento.getAttribute('data-stato')
elemento.setAttribute('aria-expanded', 'true')
elemento.hasAttribute('disabled')
elemento.removeAttribute('hidden')
elemento.toggleAttribute('hidden') // aggiunge o toglie

// Classi — classList è l'API da usare
elemento.classList.add('attiva', 'evidenziata')
elemento.classList.remove('nascosta')
elemento.classList.toggle('aperta')
elemento.classList.toggle('aperta', condizione) // forza lo stato
elemento.classList.contains('attiva')
elemento.classList.replace('vecchia', 'nuova')

// Stili — meglio le classi, ma per i valori calcolati serve
elemento.style.setProperty('--percentuale', '62%')
elemento.style.transform = 'translateX(10px)'

// Leggere lo stile EFFETTIVO (non solo quello inline)
const calcolato = getComputedStyle(elemento)
console.log(calcolato.getPropertyValue('--percentuale').trim())

// Dati personalizzati: data-* diventa dataset in camelCase
// <div data-id="42" data-stato-corrente="attivo">
console.log(elemento.dataset.id) // '42'  ← sempre stringa
console.log(elemento.dataset.statoCorrente) // 'attivo'
elemento.dataset.nuovo = 'valore' // → data-nuovo="valore"
```

---

## B6. Eventi: propagazione e delegazione

### Le tre fasi

```
Un clic su <button> dentro <div> dentro <body>:

  1. CATTURA (dall'alto verso il basso)
     window → document → body → div → button

  2. BERSAGLIO
     button

  3. RISALITA / BUBBLING (dal basso verso l'alto)
     button → div → body → document → window

I listener registrati normalmente ascoltano in fase 3.
Con { capture: true } ascoltano in fase 1.
```

```javascript
const contenitore = document.querySelector('.contenitore')
const comando = contenitore.querySelector('button')

contenitore.addEventListener('click', () => console.log('contenitore: risalita'))
contenitore.addEventListener('click', () => console.log('contenitore: cattura'), {
  capture: true,
})
comando.addEventListener('click', () => console.log('comando'))
```

```
# Output atteso, cliccando sul pulsante:
contenitore: cattura
comando
contenitore: risalita
```

### `target` contro `currentTarget`

```javascript
contenitore.addEventListener('click', (evento) => {
  // target: l'elemento su cui il clic è AVVENUTO davvero
  console.log(evento.target)

  // currentTarget: l'elemento su cui il LISTENER è registrato.
  // Vale solo durante la gestione dell'evento.
  console.log(evento.currentTarget) // sempre 'contenitore'
})
```

Questa distinzione è il fondamento della delegazione.

### Delegazione: un listener invece di mille

> **Analogia:** invece di mettere un citofono su ogni appartamento, ne metti uno al portone e chiedi a chi suona per chi sta chiamando. Un solo dispositivo, e funziona anche per gli inquilini che arriveranno domani.

```javascript
// ❌ SBAGLIATO — un listener per riga.
//    Con mille righe sono mille listener, e le righe aggiunte dopo
//    non ne hanno nessuno.
for (const comando of document.querySelectorAll('.elimina')) {
  comando.addEventListener('click', gestisciEliminazione)
}

// ✅ CORRETTO — un listener sul contenitore, per sempre
const tabella = document.querySelector('#tabella-fatture')

tabella.addEventListener('click', (evento) => {
  // closest risale dal punto del clic cercando il pulsante
  const comando = evento.target.closest('.elimina')
  if (!comando) return // il clic era altrove: ignora

  const riga = comando.closest('tr')
  eliminaFattura(riga.dataset.id)
})
```

I vantaggi sono tre: memoria (un listener invece di N), funziona per gli elementi aggiunti dopo la registrazione, e non serve rimuovere i listener quando gli elementi vengono eliminati.

### Le opzioni di `addEventListener`

```javascript
elemento.addEventListener('click', gestore, {
  // Ascolta in fase di cattura invece che di risalita
  capture: false,

  // Si rimuove da solo dopo la prima esecuzione
  once: true,

  // Promette di non chiamare preventDefault().
  // Per scroll, wheel e touchmove permette al browser di
  // scorrere senza attendere il gestore: differenza visibile.
  passive: true,

  // Rimozione tramite AbortController
  signal: controller.signal,
})
```

```javascript
// Rimuovere un listener: serve LA STESSA funzione
function gestore() {}

elemento.addEventListener('click', gestore)
elemento.removeEventListener('click', gestore) // funziona

// ❌ Questo NON rimuove nulla: sono due funzioni diverse
elemento.addEventListener('click', () => console.log('a'))
elemento.removeEventListener('click', () => console.log('a'))
```

```javascript
// ✅ AbortController: rimuove molti listener in un colpo solo.
//    È il pattern migliore per la pulizia di un componente.
const controller = new AbortController()

elemento.addEventListener('click', gestisciClic, { signal: controller.signal })
window.addEventListener('resize', gestisciRidimensionamento, { signal: controller.signal })
document.addEventListener('keydown', gestisciTasto, { signal: controller.signal })

// Alla distruzione del componente: tutti e tre rimossi
controller.abort()
```

### `preventDefault` e `stopPropagation`

```javascript
modulo.addEventListener('submit', (evento) => {
  // Impedisce il comportamento predefinito (qui: ricaricare la pagina)
  evento.preventDefault()
})

comando.addEventListener('click', (evento) => {
  // Impedisce che l'evento salga ai genitori.
  // Da usare con parsimonia: rompe la delegazione di chi sta sopra.
  evento.stopPropagation()

  // Impedisce anche gli ALTRI listener sullo STESSO elemento
  evento.stopImmediatePropagation()
})
```

**`stopPropagation` è quasi sempre la soluzione sbagliata.** Se un clic sul pulsante non deve attivare il gestore del contenitore, la correzione giusta è che il gestore del contenitore verifichi il bersaglio — non che il pulsante interrompa la propagazione, rompendo anche i listener che nessuno conosce.

### Eventi personalizzati

```javascript
// Creare e lanciare
const evento = new CustomEvent('fattura:pagata', {
  detail: { id: 42, importo: 1200 },
  bubbles: true, // risale ai genitori
  cancelable: true, // può essere annullato con preventDefault
})

elemento.dispatchEvent(evento)

// Ascoltare
document.addEventListener('fattura:pagata', (evento) => {
  console.log(evento.detail.id, evento.detail.importo)
})
```

La convenzione `dominio:azione` per i nomi evita collisioni con gli eventi nativi e rende leggibile da dove viene l'evento.

### Gli eventi da conoscere

```javascript
// Puntatore — pointer* copre mouse, tocco e penna con un'API sola
elemento.addEventListener('pointerdown', gestore)
elemento.addEventListener('pointerup', gestore)
elemento.addEventListener('click', gestore) // anche da tastiera con Invio

// Tastiera — usa 'key', non i codici numerici deprecati
document.addEventListener('keydown', (evento) => {
  if (evento.key === 'Escape') chiudi()
  if (evento.key === 'Enter' && evento.ctrlKey) invia()
})

// Form
modulo.addEventListener('submit', gestore)
campo.addEventListener('input', gestore) // a ogni carattere
campo.addEventListener('change', gestore) // alla perdita del focus
campo.addEventListener('invalid', gestore, true) // non fa bubbling

// Focus — focusin e focusout FANNO bubbling, focus e blur no
elemento.addEventListener('focusin', gestore)

// Documento e finestra
document.addEventListener('DOMContentLoaded', gestore) // HTML analizzato
window.addEventListener('load', gestore) // anche immagini e stili
window.addEventListener('scroll', gestore, { passive: true })
window.addEventListener('resize', gestore)

// Uscita dalla pagina — l'unico affidabile su mobile
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') salvaBozza()
})
```

---

## B7. Moduli ES

```javascript
// src/fatture.js

// Export con nome
export const ALIQUOTA_IVA = 0.22

export function calcolaTotale(imponibile) {
  return imponibile * (1 + ALIQUOTA_IVA)
}

export class Fattura {
  constructor(numero) {
    this.numero = numero
  }
}

// Export di default: uno solo per modulo
export default function creaFattura(numero) {
  return new Fattura(numero)
}

// Export in blocco, in fondo al file
const interno = 42
export { interno as valoreEsposto }
```

```javascript
// src/main.js

// Import con nome — le graffe non sono opzionali
import { calcolaTotale, ALIQUOTA_IVA } from './fatture.js'

// Import di default — nessuna graffa, e il nome lo scegli tu
import creaFattura from './fatture.js'

// Insieme
import creaFattura2, { calcolaTotale as calcola } from './fatture.js'

// Tutto in uno spazio dei nomi
import * as Fatture from './fatture.js'
console.log(Fatture.ALIQUOTA_IVA)

// Solo per gli effetti collaterali (registrare un componente, importare CSS)
import './stile.css'
```

### Le proprietà dei moduli che vale la pena conoscere

```javascript
// 1. Sempre in strict mode, senza doverlo dichiarare

// 2. Lo scope è il MODULO, non globale:
//    una const dichiarata qui non finisce su window

// 3. Gli import sono SOLLEVATI e valutati prima del resto del file

// 4. Gli import sono BINDING VIVI, non copie del valore
```

```javascript
// contatore.js
export let valore = 0
export function incrementa() {
  valore++
}
```

```javascript
// main.js
import { valore, incrementa } from './contatore.js'

console.log(valore) // 0
incrementa()
console.log(valore) // 1  ← il binding riflette il cambiamento

// Ma non si può riassegnare dall'esterno:
// valore = 5   // TypeError: Assignment to constant variable
```

### Import dinamico

```javascript
// Restituisce una Promise: il modulo viene scaricato al bisogno
const comando = document.querySelector('#apri-grafici')

comando.addEventListener('click', async () => {
  // Il codice dei grafici — pesante — arriva solo se qualcuno lo apre
  const { disegnaGrafico } = await import('./grafici.js')
  disegnaGrafico(datiCorrenti)
})

// Import condizionale
if (navigator.language.startsWith('it')) {
  const { traduzioni } = await import('./i18n/it.js')
}

// Con gestione dell'errore
try {
  const modulo = await import('./opzionale.js')
} catch (errore) {
  console.warn('Modulo opzionale non disponibile', errore)
}
```

L'import dinamico è ciò che rende possibile il **code splitting**: il bundler crea un file separato per ogni import dinamico, e il browser lo scarica solo quando serve. Il tema è di `tutorial_16_build_tools_deploy.md`.

### Le differenze con CommonJS

```javascript
// modulo-vecchio.cjs — CommonJS, ancora diffuso in Node.js
const fs = require('node:fs')

function leggiConfigurazione(percorso) {
  return JSON.parse(fs.readFileSync(percorso, 'utf8'))
}

module.exports = { leggiConfigurazione }
```

```javascript
// modulo-nuovo.js — ESM, lo standard
import fs from 'node:fs'

export function leggiConfigurazione(percorso) {
  return JSON.parse(fs.readFileSync(percorso, 'utf8'))
}
```

| | CommonJS | ESM |
|---|---|---|
| Risoluzione | a runtime | **statica, a tempo di analisi** |
| Tree shaking | no | **sì** |
| Caricamento | sincrono | asincrono |
| Nel browser | no (serve un bundler) | **sì, nativo** |
| `__dirname` | disponibile | usa `import.meta.dirname` |
| Top-level `await` | no | **sì** |

```json
// package.json — dichiarare che il progetto usa ESM
{
  "type": "module"
}
```

### Dipendenze circolari

```javascript
// a.js — importa da b.js
import { b } from './b.js'

export const a = 'A'
console.log('a.js vede b =', b)
```

```javascript
// b.js — importa da a.js: il ciclo è chiuso
import { a } from './a.js'

export const b = 'B'
console.log('b.js vede a =', a) // undefined durante l'inizializzazione
```

I moduli ES gestiscono i cicli senza andare in errore, ma uno dei due vedrà un valore non ancora inizializzato. La correzione non è tecnica: è estrarre la parte condivisa in un terzo modulo da cui entrambi dipendono.

---

## B8. L'event loop

JavaScript ha **un solo thread**. Una funzione che gira per due secondi blocca tutto: clic, animazioni, rendering. Capire l'event loop significa capire perché.

```
    ┌────────────────────────────────────────────────────────┐
    │                     CALL STACK                         │
    │  la funzione in esecuzione adesso, e chi l'ha chiamata │
    └────────────────────────┬───────────────────────────────┘
                             │ quando si svuota
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │                  MICROTASK QUEUE                       │
    │  Promise.then · await · queueMicrotask                 │
    │  MutationObserver                                      │
    │                                                        │
    │  ⚠ Svuotata COMPLETAMENTE prima di proseguire.         │
    │     Un microtask che ne accoda un altro all'infinito   │
    │     blocca la pagina per sempre.                       │
    └────────────────────────┬───────────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │                     RENDERING                          │
    │  requestAnimationFrame → stile → layout → paint        │
    │  al massimo ~60 volte al secondo (ogni ~16,7 ms)       │
    └────────────────────────┬───────────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │                  MACROTASK QUEUE                       │
    │  setTimeout · setInterval · eventi · I/O               │
    │                                                        │
    │  UNA sola per giro, poi si ricomincia dai microtask.   │
    └────────────────────────────────────────────────────────┘
```

### L'ordine, dimostrato

```javascript
console.log('1 — sincrono')

setTimeout(() => console.log('2 — macrotask'), 0)

Promise.resolve().then(() => console.log('3 — microtask'))

queueMicrotask(() => console.log('4 — microtask'))

console.log('5 — sincrono')
```

```
# Output atteso:
1 — sincrono
5 — sincrono
3 — microtask
4 — microtask
2 — macrotask

# Perché:
#   · tutto il codice sincrono gira per primo (1, 5)
#   · poi la coda dei microtask viene svuotata TUTTA (3, 4)
#   · solo alla fine UNA macrotask (2)
#
# setTimeout(…, 0) non significa "subito": significa
# "dopo il codice sincrono e dopo tutti i microtask".
```

### Il caso che confonde davvero

```javascript
async function esempio() {
  console.log('A')
  await null // await mette in coda il RESTO della funzione come microtask
  console.log('B')
}

console.log('inizio')
esempio()
console.log('fine')
Promise.resolve().then(() => console.log('C'))
```

```
# Output atteso:
inizio
A
fine
B
C

# 'A' è sincrono: await non è ancora stato raggiunto.
# Tutto ciò che segue await diventa un microtask,
# accodato PRIMA del .then() scritto dopo.
```

### La starvation dei microtask

```javascript
// ❌ Questo blocca la pagina PER SEMPRE.
//    La coda dei microtask va svuotata completamente prima
//    di qualunque rendering, e questa non si svuota mai.
function ricorsivo() {
  queueMicrotask(ricorsivo)
}
// ricorsivo()

// ✅ Con setTimeout la pagina resta reattiva:
//    una macrotask per giro, e fra un giro e l'altro
//    il browser può disegnare e gestire gli eventi.
function periodico() {
  setTimeout(periodico, 0)
}
```

### Non bloccare il thread

```javascript
// ❌ Un ciclo lungo blocca clic, animazioni e rendering
function elaboraTutto(elementi) {
  for (const elemento of elementi) {
    calcoloPesante(elemento) // 100.000 elementi = pagina congelata
  }
}

// ✅ Spezzare il lavoro, restituendo il controllo al browser
async function elaboraAPezzi(elementi, dimensioneBlocco = 500) {
  for (let i = 0; i < elementi.length; i += dimensioneBlocco) {
    const blocco = elementi.slice(i, i + dimensioneBlocco)
    for (const elemento of blocco) {
      calcoloPesante(elemento)
    }

    // Cede il controllo: il browser può disegnare e rispondere
    await new Promise((risolvi) => setTimeout(risolvi, 0))
  }
}

// ✅ ANCORA MEGLIO — scheduler.yield(), dove disponibile:
//    cede senza retrocedere in fondo alla coda
async function elaboraConScheduler(elementi) {
  for (const elemento of elementi) {
    calcoloPesante(elemento)
    if (globalThis.scheduler?.yield) {
      await scheduler.yield()
    }
  }
}

// ✅ PER IL CALCOLO PURO — un Web Worker, su un thread separato
// const lavoratore = new Worker('/src/calcolo.js', { type: 'module' })
// lavoratore.postMessage({ elementi })
// lavoratore.onmessage = (evento) => console.log(evento.data)
```

### `setTimeout` e i suoi limiti

```javascript
// Il ritardo è un MINIMO, non una garanzia:
// se il thread è occupato, il callback aspetta.
const inizio = Date.now()
setTimeout(() => {
  console.log('ritardo reale:', Date.now() - inizio, 'ms')
}, 100)

// Un ciclo bloccante di 500ms fa arrivare il callback a ~500ms, non 100

// Dopo cinque annidamenti, i browser impongono un minimo di 4ms
// Con la scheda in background, il minimo sale a ~1000ms
```

```javascript
// Per le animazioni, requestAnimationFrame invece di setTimeout:
// è sincronizzato con il rendering e si ferma in background
function anima() {
  elemento.style.transform = `translateX(${posizione}px)`
  posizione += 2
  if (posizione < 300) requestAnimationFrame(anima)
}
requestAnimationFrame(anima)
```

---

## B9. Gestione degli errori

```javascript
try {
  const dati = JSON.parse(testoNonValido)
} catch (errore) {
  // Dal 2019 il parametro è opzionale: catch { } è valido
  console.error(errore.name, errore.message)
} finally {
  // Eseguito SEMPRE: dopo il try riuscito, dopo il catch,
  // e anche se try o catch contengono un return
  chiudiConnessione()
}
```

### I tipi di errore nativi

```javascript
// Error            — l'errore generico
// TypeError        — operazione su un tipo sbagliato
// ReferenceError   — variabile non definita
// SyntaxError      — codice non analizzabile
// RangeError       — valore fuori dall'intervallo consentito
// URIError         — encodeURI / decodeURI con input non valido
// AggregateError   — più errori insieme (Promise.any)
```

### Errori personalizzati

```javascript
class ErroreValidazione extends Error {
  constructor(campo, messaggio, opzioni) {
    super(messaggio, opzioni)
    this.name = 'ErroreValidazione'
    this.campo = campo
  }
}

class ErroreRete extends Error {
  constructor(risposta, opzioni) {
    super(`Richiesta fallita: ${risposta.status} ${risposta.statusText}`, opzioni)
    this.name = 'ErroreRete'
    this.stato = risposta.status
    this.url = risposta.url
  }
}

try {
  throw new ErroreValidazione('email', 'Indirizzo non valido')
} catch (errore) {
  if (errore instanceof ErroreValidazione) {
    console.log(`Campo ${errore.campo}: ${errore.message}`)
  } else {
    throw errore // ciò che non sai gestire, rilancialo
  }
}
```

### `cause`: non perdere l'errore originale

```javascript
// ❌ SBAGLIATO — l'errore originale sparisce, e con esso la causa vera
async function caricaUtente(id) {
  try {
    return await recuperaDaDatabase(id)
  } catch (errore) {
    throw new Error('Impossibile caricare l utente')
  }
}

// ✅ CORRETTO — cause conserva la catena completa (ES2022)
async function caricaUtenteCorretto(id) {
  try {
    return await recuperaDaDatabase(id)
  } catch (errore) {
    throw new Error(`Impossibile caricare l utente ${id}`, { cause: errore })
  }
}

// La catena si legge risalendo
try {
  await caricaUtenteCorretto(42)
} catch (errore) {
  console.error(errore.message) // 'Impossibile caricare l utente 42'
  console.error(errore.cause) // l'errore originale del database
  console.error(errore.cause?.cause) // e così via
}
```

### Il pattern del risultato

Quando un errore è un esito previsto e non un'anomalia, le eccezioni sono lo strumento sbagliato: obbligano chi chiama a ricordarsi del `try`.

```javascript
/**
 * Restituisce { ok: true, valore } oppure { ok: false, errore }.
 * Chi chiama DEVE guardare l'esito: non può dimenticarsene.
 */
function analizzaJson(testo) {
  try {
    return { ok: true, valore: JSON.parse(testo) }
  } catch (errore) {
    return { ok: false, errore }
  }
}

const esito = analizzaJson(testoUtente)
if (esito.ok) {
  console.log(esito.valore)
} else {
  console.error('JSON non valido:', esito.errore.message)
}
```

```
La regola per scegliere:

  throw   →  la condizione è ANOMALA e chi chiama non può farci nulla
             (database irraggiungibile, configurazione mancante)

  Result  →  la condizione è PREVISTA e fa parte del dominio
             (input dell'utente non valido, record non trovato)
```

### Gli errori che sfuggono

```javascript
// Nel browser: gli errori non catturati
window.addEventListener('error', (evento) => {
  registraErrore({
    messaggio: evento.message,
    file: evento.filename,
    riga: evento.lineno,
    errore: evento.error,
  })
})

// Le Promise rifiutate senza .catch()
window.addEventListener('unhandledrejection', (evento) => {
  registraErrore({ tipo: 'promise', motivo: evento.reason })
  evento.preventDefault() // evita il messaggio nella console
})
```

```javascript
// ❌ SBAGLIATO — un errore dentro un callback asincrono
//    NON viene catturato dal try che lo circonda
try {
  setTimeout(() => {
    throw new Error('non catturato')
  }, 0)
} catch (errore) {
  // non arriva mai qui
}

// ✅ CORRETTO — il try va DENTRO il callback
setTimeout(() => {
  try {
    operazioneRischiosa()
  } catch (errore) {
    gestisci(errore)
  }
}, 0)
```

---

## B10. Uguaglianza, copia e riferimenti

### Primitivi per valore, oggetti per riferimento

```javascript
// I primitivi si copiano
let a = 5
let b = a
b = 10
console.log(a) // 5   ← invariato

// Gli oggetti si condividono: la variabile contiene un RIFERIMENTO
const oggetto1 = { valore: 5 }
const oggetto2 = oggetto1
oggetto2.valore = 10
console.log(oggetto1.valore) // 10  ← modificato
```

```javascript
// Da cui: due oggetti con lo stesso contenuto non sono uguali
console.log({ a: 1 } === { a: 1 }) // false
console.log([1, 2] === [1, 2]) // false

// Sono riferimenti diversi a due oggetti diversi.
const x = { a: 1 }
const y = x
console.log(x === y) // true   ← stesso riferimento
```

```javascript
// Il passaggio alle funzioni segue la stessa regola
function modifica(oggetto, primitivo) {
  oggetto.valore = 99 // il chiamante VEDE questa modifica
  primitivo = 99 // il chiamante NON la vede
}

const o = { valore: 1 }
let p = 1
modifica(o, p)
console.log(o.valore) // 99
console.log(p) // 1
```

### Le tre uguaglianze

```javascript
// == con coercizione: da evitare
console.log(0 == '') // true

// === stretta
console.log(NaN === NaN) // false
console.log(0 === -0) // true

// Object.is: come === con due eccezioni
console.log(Object.is(NaN, NaN)) // true
console.log(Object.is(0, -0)) // false
```

### Confronto profondo

```javascript
/**
 * Confronto strutturale ricorsivo.
 * Non gestisce riferimenti circolari, Map, Set né Date:
 * per quelli serve una libreria.
 */
function ugualiInProfondita(a, b) {
  if (Object.is(a, b)) return true

  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) {
    return false
  }

  const chiaviA = Object.keys(a)
  const chiaviB = Object.keys(b)
  if (chiaviA.length !== chiaviB.length) return false

  return chiaviA.every(
    (chiave) => Object.hasOwn(b, chiave) && ugualiInProfondita(a[chiave], b[chiave]),
  )
}

console.log(ugualiInProfondita({ a: { b: 1 } }, { a: { b: 1 } })) // true
```

### `Map` e `Set` invece di oggetti e array

```javascript
// Map: chiavi di QUALUNQUE tipo, ordine garantito, dimensione diretta
const cache = new Map()

const chiaveOggetto = { id: 1 }
cache.set(chiaveOggetto, 'valore') // un oggetto come chiave
cache.set('stringa', 'valore')
cache.set(42, 'valore')

console.log(cache.get(chiaveOggetto)) // 'valore'
console.log(cache.has('stringa')) // true
console.log(cache.size) // 3
cache.delete(42)

for (const [chiave, valore] of cache) {
  console.log(chiave, valore)
}

// Set: valori unici, verifica di appartenenza in tempo costante
const visti = new Set()
visti.add('a')
visti.add('a') // ignorato
console.log(visti.size) // 1
console.log(visti.has('a')) // true

// Deduplicare un array
const unici = [...new Set([1, 1, 2, 3, 3])] // [1, 2, 3]
```

```javascript
// ❌ includes su un array è O(n): dentro un ciclo diventa O(n²)
const elencoGrande = [
  /* 10.000 elementi */
]
for (const elemento of altriElementi) {
  if (elencoGrande.includes(elemento)) {
    // ...
  }
}

// ✅ Set: la verifica è O(1)
const insieme = new Set(elencoGrande)
for (const elemento of altriElementi) {
  if (insieme.has(elemento)) {
    // ...
  }
}
```

```javascript
// WeakMap e WeakSet: le chiavi NON impediscono la raccolta della memoria.
// Servono per associare dati a oggetti senza tenerli in vita.
const datiPrivati = new WeakMap()

class Componente {
  constructor(elemento) {
    datiPrivati.set(elemento, { stato: 'iniziale' })
  }
}

// Quando l'elemento del DOM viene rimosso e nessuno lo referenzia più,
// la voce nella WeakMap sparisce da sola: nessun memory leak.
```

| | `Object` | `Map` |
|---|---|---|
| Chiavi | stringhe e Symbol | **qualunque valore** |
| Ordine | parzialmente garantito | **di inserimento** |
| Dimensione | `Object.keys(o).length` | **`.size`** |
| Iterazione | serve `Object.entries` | **iterabile di suo** |
| Prototipo | ereditato | nessuno |
| Serializzabile in JSON | **sì** | no |

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Prevedere l'output

**Obiettivo:** dire cosa stampa ogni blocco, e perché, prima di eseguirlo.

```javascript
// PROBLEMA
console.log(typeof null)
console.log(0.1 + 0.2 === 0.3)
console.log([] + {})
console.log([1, 2] + [3])
console.log(NaN === NaN)
console.log([10, 9, 1].sort())
console.log(0 || 'a', 0 ?? 'a')
console.log((function () { return this })())
```

```javascript
// SOLUZIONE, con la spiegazione di ciascuno

console.log(typeof null)
// 'object'
// Il bug della prima implementazione del 1995. Correggerlo romperebbe
// troppo codice esistente. Per riconoscere null: valore === null.

console.log(0.1 + 0.2 === 0.3)
// false
// I numeri sono float IEEE 754 a 64 bit: 0.1 e 0.2 non hanno
// rappresentazione binaria esatta. Il risultato è 0.30000000000000004.

console.log([] + {})
// '[object Object]'
// L'operatore + su due oggetti li converte in stringa:
// [] diventa '' e {} diventa '[object Object]'.

console.log([1, 2] + [3])
// '1,23'
// Entrambi gli array diventano stringhe con join(','):
// '1,2' e '3', poi concatenate.

console.log(NaN === NaN)
// false
// NaN non è uguale a nulla, per specifica IEEE 754.
// Per verificarlo: Number.isNaN(valore).

console.log([10, 9, 1].sort())
// [1, 10, 9]
// Senza funzione di confronto, sort converte in stringa e ordina
// lessicograficamente: '1' < '10' < '9'.
// Corretto: [10, 9, 1].toSorted((a, b) => a - b)

console.log(0 || 'a', 0 ?? 'a')
// 'a' 0
// || scatta su qualunque falsy, e 0 è falsy.
// ?? scatta solo su null e undefined, quindi 0 passa.

console.log((function () { return this })())
// undefined in un modulo ES, globalThis in uno script classico
// non-strict. Chiamata semplice: binding predefinito.
// I moduli sono sempre in strict mode.
```

---

### Esercizio 2 — Closure: contatore, memoizzazione, debounce

**Obiettivo:** implementare tre utility che si basano tutte sullo stesso meccanismo — una funzione che ricorda lo scope in cui è nata.

```javascript
// SOLUZIONE

/**
 * 1. Contatore con stato privato.
 * 'valore' non è raggiungibile dall'esterno: non è una convenzione,
 * è impossibile per costruzione.
 */
function creaContatore(partenza = 0, passo = 1) {
  let valore = partenza

  return {
    incrementa() {
      valore += passo
      return valore
    },
    decrementa() {
      valore -= passo
      return valore
    },
    get valoreCorrente() {
      return valore
    },
    azzera() {
      valore = partenza
      return valore
    },
  }
}

const contatore = creaContatore(10, 5)
console.log(contatore.incrementa()) // 15
console.log(contatore.incrementa()) // 20
console.log(contatore.valoreCorrente) // 20
console.log(contatore.azzera()) // 10
console.log(contatore.valore) // undefined  ← inaccessibile

/**
 * 2. Memoizzazione con limite di dimensione (LRU semplificata).
 * La Map mantiene l'ordine di inserimento: la prima chiave
 * è la meno recente.
 */
function memoizza(funzione, { dimensioneMassima = 100 } = {}) {
  const cache = new Map()

  return function (...argomenti) {
    const chiave = JSON.stringify(argomenti)

    if (cache.has(chiave)) {
      // Rimuovi e reinserisci: la sposta in fondo, cioè "usata di recente"
      const valore = cache.get(chiave)
      cache.delete(chiave)
      cache.set(chiave, valore)
      return valore
    }

    const risultato = funzione.apply(this, argomenti)
    cache.set(chiave, risultato)

    if (cache.size > dimensioneMassima) {
      // La prima chiave dell'iteratore è la meno usata di recente
      cache.delete(cache.keys().next().value)
    }

    return risultato
  }
}

let chiamate = 0
const quadratoLento = memoizza((n) => {
  chiamate++
  return n * n
})

console.log(quadratoLento(4), quadratoLento(4), chiamate) // 16 16 1

/**
 * 3. Debounce con annullamento e esecuzione immediata.
 * Il timer vive nella closure, quindi ogni funzione debounce
 * ha il proprio, indipendente.
 */
function debounce(funzione, attesa = 300, { immediato = false } = {}) {
  let temporizzatore = null

  function debounced(...argomenti) {
    const contesto = this
    const chiamaSubito = immediato && temporizzatore === null

    clearTimeout(temporizzatore)

    temporizzatore = setTimeout(() => {
      temporizzatore = null
      if (!immediato) funzione.apply(contesto, argomenti)
    }, attesa)

    if (chiamaSubito) funzione.apply(contesto, argomenti)
  }

  debounced.annulla = () => {
    clearTimeout(temporizzatore)
    temporizzatore = null
  }

  return debounced
}
```

```javascript
// Test
const registro = []
const registraDebounced = debounce((testo) => registro.push(testo), 50)

registraDebounced('a')
registraDebounced('b')
registraDebounced('c')

setTimeout(() => {
  console.log(registro) // ['c']  ← solo l'ultima chiamata
}, 100)
```

```
# Output atteso:
15
20
20
10
undefined
16 16 1
[ 'c' ]
```

```
# Il filo comune ai tre:
#
# In tutti e tre i casi una funzione interna continua a leggere
# una variabile dello scope esterno DOPO che quella funzione
# esterna è terminata. Il garbage collector non può liberare
# quello scope finché la funzione interna è viva.
#
# È lo stesso identico meccanismo, applicato a tre problemi diversi:
#   valore          → stato privato
#   cache           → memoria fra le chiamate
#   temporizzatore  → coordinamento nel tempo
```

---

### Esercizio 3 — `this`: diagnosticare e correggere

**Obiettivo:** dato un componente rotto, spiegare perché `this` è sbagliato in ognuno dei quattro punti e correggerlo.

```javascript
// PARTENZA — quattro errori distinti su this
const cronometro = {
  secondi: 0,
  intervallo: null,

  avvia() {
    // Errore 1
    this.intervallo = setInterval(function () {
      this.secondi++
      this.aggiorna()
    }, 1000)
  },

  aggiorna() {
    document.querySelector('#tempo').textContent = this.secondi
  },

  // Errore 2
  collega: () => {
    document.querySelector('#avvia').addEventListener('click', this.avvia)
  },

  // Errore 3
  formatta() {
    return [this.secondi].map(function (s) {
      return `${s} secondi su ${this.massimo}`
    })
  },

  massimo: 3600,
}

// Errore 4
const avviaSciolto = cronometro.avvia
```

```javascript
// SOLUZIONE — le quattro cause, e le correzioni

const cronometroCorretto = {
  secondi: 0,
  intervallo: null,
  massimo: 3600,

  // ── CORREZIONE 1 ──────────────────────────────────────────
  // CAUSA: una function normale dentro setInterval riceve
  //   il binding predefinito: this è undefined nei moduli.
  // FIX: arrow function — eredita this dallo scope in cui è scritta,
  //   che qui è il metodo avvia(), dove this è l'oggetto.
  avvia() {
    this.intervallo = setInterval(() => {
      this.secondi++
      this.aggiorna()
    }, 1000)
  },

  ferma() {
    clearInterval(this.intervallo)
    this.intervallo = null
  },

  aggiorna() {
    document.querySelector('#tempo').textContent = this.secondi
  },

  // ── CORREZIONE 2 ──────────────────────────────────────────
  // CAUSA: una arrow come METODO non ha this proprio: prende
  //   quello del modulo, non l'oggetto. E passando this.avvia
  //   come callback si perde comunque il legame.
  // FIX: metodo normale, e arrow nel listener.
  collega() {
    document.querySelector('#avvia').addEventListener('click', () => this.avvia())
    document.querySelector('#ferma').addEventListener('click', () => this.ferma())
  },

  // ── CORREZIONE 3 ──────────────────────────────────────────
  // CAUSA: il callback di map è una function normale: this è undefined.
  // FIX: arrow. (In alternativa, map accetta un secondo argomento
  //   che diventa this: [..].map(function(s){...}, this) )
  formatta() {
    return [this.secondi].map((s) => `${s} secondi su ${this.massimo}`)
  },
}

// ── CORREZIONE 4 ────────────────────────────────────────────
// CAUSA: estraendo il metodo, si perde l'oggetto prima del punto.
// FIX: bind, che restituisce una funzione con this fissato.
const avviaLegato = cronometroCorretto.avvia.bind(cronometroCorretto)
```

```javascript
// La versione con class, dove i campi arrow risolvono tutto alla radice
class Cronometro {
  secondi = 0
  intervallo = null
  massimo = 3600

  // Campo arrow: this è SEMPRE l'istanza, comunque venga chiamato.
  // Si può passare come callback senza bind.
  avvia = () => {
    this.intervallo = setInterval(() => {
      this.secondi++
      this.aggiorna()
    }, 1000)
  }

  ferma = () => {
    clearInterval(this.intervallo)
    this.intervallo = null
  }

  aggiorna() {
    document.querySelector('#tempo').textContent = this.secondi
  }

  collega() {
    document.querySelector('#avvia').addEventListener('click', this.avvia)
    document.querySelector('#ferma').addEventListener('click', this.ferma)
  }
}
```

```
# Le quattro regole che spiegano tutti e quattro gli errori:
#
#   1. function normale chiamata semplice  → this = undefined (strict)
#   2. arrow come metodo                   → this = scope esterno
#   3. callback di un metodo di array      → this = undefined
#   4. metodo estratto dall'oggetto        → perde il binding implicito
#
# In tutti e quattro i casi la domanda da porsi è la stessa:
#   "COME viene chiamata questa funzione?"
# Non "dove è scritta" — tranne che per le arrow, dove è l'opposto.
```

---

### Esercizio 4 — Trasformare dati con i metodi funzionali

**Obiettivo:** partendo da un elenco grezzo, produrre un riepilogo aggregato con una catena leggibile.

```javascript
// PARTENZA
const movimenti = [
  { id: 1, cliente: 'Rossi', tipo: 'fattura', importo: 1200, data: '2026-01-15', pagato: true },
  { id: 2, cliente: 'Bianchi', tipo: 'fattura', importo: 340, data: '2026-01-22', pagato: false },
  { id: 3, cliente: 'Rossi', tipo: 'nota-credito', importo: -200, data: '2026-02-03', pagato: true },
  { id: 4, cliente: 'Verdi', tipo: 'fattura', importo: 2100, data: '2026-02-11', pagato: false },
  { id: 5, cliente: 'Rossi', tipo: 'fattura', importo: 890, data: '2026-03-07', pagato: false },
  { id: 6, cliente: 'Bianchi', tipo: 'fattura', importo: 1500, data: '2026-03-19', pagato: true },
]

// Obiettivo: per ogni cliente, il totale fatturato, l'insoluto,
// il numero di documenti e il mese con più attività.
```

```javascript
// SOLUZIONE

const formattaEuro = new Intl.NumberFormat('it-IT', {
  style: 'currency',
  currency: 'EUR',
})

/** Estrae 'AAAA-MM' dalla data in formato ISO. */
function mesediData(dataIso) {
  return dataIso.slice(0, 7)
}

function riepilogaPerCliente(elenco) {
  const perCliente = Object.groupBy(elenco, (m) => m.cliente)

  return Object.entries(perCliente)
    .map(([cliente, documenti]) => {
      const totale = documenti.reduce((somma, m) => somma + m.importo, 0)

      const insoluto = documenti
        .filter((m) => !m.pagato)
        .reduce((somma, m) => somma + m.importo, 0)

      // Conteggio per mese, poi il massimo
      const perMese = documenti.reduce((conteggi, m) => {
        const mese = mesediData(m.data)
        conteggi[mese] = (conteggi[mese] ?? 0) + 1
        return conteggi
      }, {})

      const [mesePiuAttivo, quantiInQuelMese] = Object.entries(perMese).reduce(
        (massimo, corrente) => (corrente[1] > massimo[1] ? corrente : massimo),
        ['—', 0],
      )

      return {
        cliente,
        documenti: documenti.length,
        totale,
        insoluto,
        percentualeInsoluta: totale === 0 ? 0 : Math.round((insoluto / totale) * 100),
        mesePiuAttivo,
        quantiInQuelMese,
      }
    })
    .toSorted((a, b) => b.insoluto - a.insoluto)
}

const riepilogo = riepilogaPerCliente(movimenti)

for (const r of riepilogo) {
  console.log(
    `${r.cliente.padEnd(10)} ` +
      `${String(r.documenti).padStart(2)} doc · ` +
      `tot ${formattaEuro.format(r.totale).padStart(10)} · ` +
      `insoluto ${formattaEuro.format(r.insoluto).padStart(10)} ` +
      `(${r.percentualeInsoluta}%) · ` +
      `mese ${r.mesePiuAttivo}`,
  )
}
```

```
# Output atteso:
Verdi       1 doc · tot  2.100,00 € · insoluto  2.100,00 € (100%) · mese 2026-02
Rossi       3 doc · tot  1.890,00 € · insoluto    890,00 € (47%) · mese 2026-01
Bianchi     2 doc · tot  1.840,00 € · insoluto    340,00 € (18%) · mese 2026-01
```

```
# I punti di attenzione:
#
# Object.groupBy (ES2024) sostituisce il reduce che tutti scrivevano
#   per raggruppare. Restituisce un oggetto con prototipo null,
#   quindi Object.entries funziona ma i metodi di Object.prototype no.
#
# toSorted invece di sort: non modifica l'array ricevuto.
#   Chi ha passato 'elenco' non si trova l'ordine cambiato.
#
# Il reduce che cerca il massimo parte da ['—', 0]: senza valore
#   iniziale, reduce su un array vuoto solleva TypeError.
#
# Intl.NumberFormat va creato UNA VOLTA fuori dal ciclo:
#   costruirlo è costoso, e ricrearlo a ogni riga si nota
#   su elenchi lunghi.
#
# La divisione per il totale è protetta: una nota di credito
#   che azzera il totale produrrebbe NaN o Infinity.
```

---

### Esercizio 5 — Delegazione degli eventi su una tabella dinamica

**Obiettivo:** una tabella dove si possono ordinare le colonne, eliminare righe e modificarle in linea — con **un solo listener**.

```html
<table id="tabella-fatture">
  <caption>Fatture del trimestre</caption>
  <thead>
    <tr>
      <th scope="col"><button type="button" data-ordina="numero">Numero</button></th>
      <th scope="col"><button type="button" data-ordina="cliente">Cliente</button></th>
      <th scope="col"><button type="button" data-ordina="importo">Importo</button></th>
      <th scope="col">Azioni</th>
    </tr>
  </thead>
  <tbody id="corpo-tabella"></tbody>
</table>

<p id="annunci" role="status" aria-live="polite"></p>
```

```javascript
// SOLUZIONE — src/tabella.js

const tabella = document.querySelector('#tabella-fatture')
const corpo = document.querySelector('#corpo-tabella')
const annunci = document.querySelector('#annunci')

let dati = [
  { id: 1, numero: '2026-001', cliente: 'Rossi', importo: 1200 },
  { id: 2, numero: '2026-002', cliente: 'Bianchi', importo: 340 },
  { id: 3, numero: '2026-003', cliente: 'Verdi', importo: 2100 },
]

let ordinamento = { campo: 'numero', crescente: true }

const formattaEuro = new Intl.NumberFormat('it-IT', {
  style: 'currency',
  currency: 'EUR',
})

/** Sostituisce i caratteri che avrebbero significato nell'HTML. */
function proteggi(testo) {
  return String(testo).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  )
}

function disegna() {
  const ordinati = dati.toSorted((a, b) => {
    const { campo, crescente } = ordinamento
    const segno = crescente ? 1 : -1

    return typeof a[campo] === 'number'
      ? (a[campo] - b[campo]) * segno
      : a[campo].localeCompare(b[campo], 'it') * segno
  })

  // Una sola assegnazione invece di N inserimenti nel DOM vivo
  corpo.innerHTML = ordinati
    .map(
      (f) => `
      <tr data-id="${f.id}">
        <th scope="row">${proteggi(f.numero)}</th>
        <td class="modificabile" data-campo="cliente">${proteggi(f.cliente)}</td>
        <td class="numerico">${formattaEuro.format(f.importo)}</td>
        <td>
          <button type="button" class="elimina">
            Elimina<span class="solo-screen-reader"> la fattura ${proteggi(f.numero)}</span>
          </button>
        </td>
      </tr>`,
    )
    .join('')

  // Lo stato di ordinamento, annunciato anche agli screen reader
  for (const comando of tabella.querySelectorAll('[data-ordina]')) {
    const attivo = comando.dataset.ordina === ordinamento.campo
    comando.closest('th').setAttribute(
      'aria-sort',
      attivo ? (ordinamento.crescente ? 'ascending' : 'descending') : 'none',
    )
  }
}

// ── UN SOLO listener per i clic, su tutta la tabella ──────────
tabella.addEventListener('click', (evento) => {
  // Ordinamento
  const comandoOrdina = evento.target.closest('[data-ordina]')
  if (comandoOrdina) {
    const campo = comandoOrdina.dataset.ordina
    ordinamento =
      ordinamento.campo === campo
        ? { campo, crescente: !ordinamento.crescente }
        : { campo, crescente: true }
    disegna()
    annunci.textContent = `Ordinato per ${campo}, ${
      ordinamento.crescente ? 'crescente' : 'decrescente'
    }`
    return
  }

  // Eliminazione
  const comandoElimina = evento.target.closest('.elimina')
  if (comandoElimina) {
    const riga = comandoElimina.closest('tr')
    const id = Number(riga.dataset.id)
    const rimossa = dati.find((f) => f.id === id)

    dati = dati.filter((f) => f.id !== id)
    disegna()
    annunci.textContent = `Fattura ${rimossa.numero} eliminata`
    return
  }
})

// ── Modifica in linea: doppio clic per aprire ─────────────────
tabella.addEventListener('dblclick', (evento) => {
  const cella = evento.target.closest('.modificabile')
  if (!cella || cella.querySelector('input')) return

  const valoreAttuale = cella.textContent.trim()
  cella.innerHTML = `<input type="text" value="${proteggi(valoreAttuale)}"
                            aria-label="Modifica ${cella.dataset.campo}" />`
  const campo = cella.querySelector('input')
  campo.focus()
  campo.select()
})

// ── Conferma e annullamento della modifica ────────────────────
// focusout e keydown si delegano allo stesso modo
tabella.addEventListener('focusout', (evento) => {
  if (evento.target.matches('.modificabile input')) {
    confermaModifica(evento.target)
  }
})

tabella.addEventListener('keydown', (evento) => {
  if (!evento.target.matches('.modificabile input')) return

  if (evento.key === 'Enter') {
    evento.preventDefault()
    confermaModifica(evento.target)
  }

  if (evento.key === 'Escape') {
    disegna() // ridisegna dai dati: annulla la modifica
  }
})

function confermaModifica(campo) {
  const cella = campo.closest('.modificabile')
  const riga = cella.closest('tr')
  const id = Number(riga.dataset.id)
  const nuovoValore = campo.value.trim()

  if (nuovoValore === '') {
    disegna()
    return
  }

  const fattura = dati.find((f) => f.id === id)
  fattura[cella.dataset.campo] = nuovoValore

  disegna()
  annunci.textContent = `${cella.dataset.campo} aggiornato a ${nuovoValore}`
}

disegna()
```

```
# Perché la delegazione è la scelta giusta qui:
#
# Con un listener per riga servirebbero, per 100 fatture:
#   100 listener 'click' sul pulsante elimina
#   100 listener 'dblclick' sulla cella
#   + la registrazione di quelli nuovi a ogni ridisegno
#   + la rimozione dei vecchi, o si accumulano
#
# Con la delegazione: 4 listener, per sempre.
# Il ridisegno con innerHTML distrugge e ricrea le righe,
# e i listener continuano a funzionare perché non sono
# sulle righe: sono sulla tabella.
#
# Il pattern in ogni gestore è lo stesso:
#   1. evento.target.closest('<selettore>')
#   2. se non trova nulla, return: il clic era altrove
#   3. risali con closest('tr') per il contesto
#
# La funzione proteggi() non è opzionale: i dati potrebbero
# contenere < o >, e innerHTML li interpreterebbe come markup.
# È la stessa ragione per cui textContent è la scelta predefinita.
```

---

### Esercizio 6 — Prevedere l'ordine dell'event loop

**Obiettivo:** dire l'ordine esatto di stampa, poi eseguire e confrontare.

```javascript
// PROBLEMA
console.log('1')

setTimeout(() => console.log('2'), 0)

Promise.resolve()
  .then(() => console.log('3'))
  .then(() => console.log('4'))

;(async () => {
  console.log('5')
  await null
  console.log('6')
})()

queueMicrotask(() => console.log('7'))

setTimeout(() => {
  console.log('8')
  Promise.resolve().then(() => console.log('9'))
}, 0)

console.log('10')
```

```
# SOLUZIONE: 1 5 10 3 6 7 4 2 8 9
#
# Il ragionamento, fase per fase:
#
# ── FASE SINCRONA ────────────────────────────────────────────
#   '1'   console.log diretto
#         setTimeout → accoda una MACROTASK (chiamiamola M1)
#         .then → accoda una MICROTASK (m1: stampa '3')
#   '5'   la funzione async parte SINCRONA fino al primo await.
#         await null → accoda il resto come MICROTASK (m2: stampa '6')
#         queueMicrotask → MICROTASK (m3: stampa '7')
#         setTimeout → MACROTASK (M2)
#  '10'   console.log diretto
#
#   Stampato finora: 1, 5, 10
#   Coda microtask:  [m1='3', m2='6', m3='7']
#   Coda macrotask:  [M1='2', M2='8'+then]
#
# ── SVUOTAMENTO DEI MICROTASK ────────────────────────────────
#   La coda va svuotata COMPLETAMENTE, e ciò che viene accodato
#   durante lo svuotamento viene eseguito nello stesso giro.
#
#   m1 → '3'   e il .then concatenato accoda m4 ('4') IN FONDO
#   m2 → '6'
#   m3 → '7'
#   m4 → '4'   ← accodato durante lo svuotamento, eseguito subito dopo
#
#   Stampato: 1, 5, 10, 3, 6, 7, 4
#
# ── PRIMA MACROTASK ──────────────────────────────────────────
#   M1 → '2'
#   Poi si svuotano i microtask: nessuno in coda.
#
# ── SECONDA MACROTASK ────────────────────────────────────────
#   M2 → '8', e accoda una microtask
#   Svuotamento microtask → '9'
#
# ── RISULTATO ────────────────────────────────────────────────
#   1 5 10 3 6 7 4 2 8 9
#
#
# Le tre regole che bastano a prevedere qualunque caso:
#
#   1. Tutto il codice sincrono gira per primo, fino in fondo.
#   2. Poi la coda dei microtask viene svuotata TUTTA, comprese
#      quelle accodate durante lo svuotamento.
#   3. Poi UNA sola macrotask, e si ricomincia dal punto 2.
#
# 'await' non blocca: accoda il resto della funzione
# come microtask e restituisce il controllo.
```

---

### Esercizio 7 — Prototipi contro classi

**Obiettivo:** scrivere la stessa gerarchia nei due modi e verificare che producano la stessa struttura.

```javascript
// SOLUZIONE — versione con funzioni costruttrici (pre-ES6)

function Documento(numero, data) {
  this.numero = numero
  this.data = data
}

// I metodi sul PROTOTIPO: una copia sola, condivisa
Documento.prototype.descrivi = function () {
  return `${this.tipo()} ${this.numero} del ${this.data}`
}

Documento.prototype.tipo = function () {
  return 'Documento'
}

function Fattura(numero, data, importo) {
  // Chiamare il costruttore genitore con il this corrente
  Documento.call(this, numero, data)
  this.importo = importo
}

// Collegare le catene prototipali
Fattura.prototype = Object.create(Documento.prototype)
Fattura.prototype.constructor = Fattura // altrimenti punta a Documento

Fattura.prototype.tipo = function () {
  return 'Fattura'
}

Fattura.prototype.descrivi = function () {
  // Richiamare il metodo del genitore
  return `${Documento.prototype.descrivi.call(this)} — ${this.importo} euro`
}
```

```javascript
// SOLUZIONE — versione con class (ES6+)

class DocumentoClass {
  constructor(numero, data) {
    this.numero = numero
    this.data = data
  }

  tipo() {
    return 'Documento'
  }

  descrivi() {
    return `${this.tipo()} ${this.numero} del ${this.data}`
  }
}

class FatturaClass extends DocumentoClass {
  constructor(numero, data, importo) {
    super(numero, data)
    this.importo = importo
  }

  tipo() {
    return 'Fattura'
  }

  descrivi() {
    return `${super.descrivi()} — ${this.importo} euro`
  }
}
```

```javascript
// LA VERIFICA: le due versioni producono la stessa struttura

const f1 = new Fattura('2026-001', '2026-01-15', 1200)
const f2 = new FatturaClass('2026-001', '2026-01-15', 1200)

console.log(f1.descrivi())
console.log(f2.descrivi())

// Stessa catena prototipale
console.log(Object.getPrototypeOf(f1) === Fattura.prototype) // true
console.log(Object.getPrototypeOf(f2) === FatturaClass.prototype) // true

console.log(f1 instanceof Documento) // true
console.log(f2 instanceof DocumentoClass) // true

// Una classe È una funzione
console.log(typeof FatturaClass) // 'function'

// I metodi stanno sul prototipo in entrambe
console.log(Object.getOwnPropertyNames(FatturaClass.prototype))
// ['constructor', 'tipo', 'descrivi']

// Le proprietà proprie sono solo i dati
console.log(Object.keys(f2)) // ['numero', 'data', 'importo']
```

```
# Output atteso:
Fattura 2026-001 del 2026-01-15 — 1200 euro
Fattura 2026-001 del 2026-01-15 — 1200 euro
true
true
true
true
function
[ 'constructor', 'tipo', 'descrivi' ]
[ 'numero', 'data', 'importo' ]
```

```
# Cosa dimostra il confronto:
#
# class NON introduce un modello a oggetti nuovo: produce
# esattamente la stessa struttura prototipale, con una sintassi
# che non richiede di scrivere a mano
#   Object.create(Genitore.prototype)
#   Figlia.prototype.constructor = Figlia
#   Genitore.prototype.metodo.call(this)
#
# Le differenze che class aggiunge davvero:
#   · non è sollevata come una dichiarazione di funzione
#   · il corpo è sempre in strict mode
#   · i metodi non sono enumerabili (non compaiono in for...in)
#   · chiamarla senza new è un TypeError
#   · campi privati con #, impossibili con i prototipi
#
# Il polimorfismo funziona per la stessa ragione in entrambe:
# descrivi() chiama this.tipo(), e la ricerca parte dall'istanza,
# quindi trova la versione più specifica della catena.
```

---

## C2. Mini-progetto: todo-list in JavaScript vanilla

L'esercizio chiave del modulo: un'applicazione todo-list con filtri, persistenza in `localStorage` e trascinamento per riordinare — **tutto in JavaScript puro**, senza librerie.

### Cosa deve fare

1. Aggiungere, modificare, completare ed eliminare attività.
2. Filtrare per stato: tutte, da fare, completate.
3. Persistere in `localStorage` e sopravvivere al ricaricamento.
4. Riordinare con il trascinamento **e** con la tastiera.
5. Annullare l'ultima eliminazione.
6. Essere accessibile: landmark, live region, focus gestito.
7. Nessuna libreria, nessun framework.

### Struttura

```
todo/
├── index.html
└── src/
    ├── main.js          composizione e avvio
    ├── stato.js         il modello dei dati e la persistenza
    ├── vista.js         il rendering
    └── stile.css
```

### `src/stato.js`

```javascript
// src/stato.js
// Tutto lo stato dell'applicazione in un posto solo.
// La vista non lo modifica mai direttamente: passa dalle azioni.

const CHIAVE_ARCHIVIO = 'todo:attivita:v1'

/**
 * Crea lo store. Le funzioni restituite chiudono su 'stato',
 * che resta privato: nessuno può modificarlo senza passare da qui.
 */
export function creaStore() {
  let stato = {
    attivita: caricaDaArchivio(),
    filtro: 'tutte', // 'tutte' | 'da-fare' | 'completate'
    ultimaEliminata: null, // per l'annullamento
  }

  const iscritti = new Set()

  function notifica() {
    salvaInArchivio(stato.attivita)
    for (const ascoltatore of iscritti) ascoltatore(stato)
  }

  return {
    /** Registra un ascoltatore; restituisce la funzione per disiscriversi. */
    iscriviti(ascoltatore) {
      iscritti.add(ascoltatore)
      ascoltatore(stato)
      return () => iscritti.delete(ascoltatore)
    },

    /** Copia superficiale: la vista non può modificare lo stato per sbaglio. */
    leggi() {
      return { ...stato, attivita: [...stato.attivita] }
    },

    aggiungi(testo) {
      const pulito = testo.trim()
      if (pulito === '') return null

      const nuova = {
        id: crypto.randomUUID(),
        testo: pulito,
        completata: false,
        creataIl: new Date().toISOString(),
      }

      stato.attivita = [...stato.attivita, nuova]
      notifica()
      return nuova
    },

    modifica(id, testo) {
      const pulito = testo.trim()
      if (pulito === '') return

      stato.attivita = stato.attivita.map((a) => (a.id === id ? { ...a, testo: pulito } : a))
      notifica()
    },

    commuta(id) {
      stato.attivita = stato.attivita.map((a) =>
        a.id === id ? { ...a, completata: !a.completata } : a,
      )
      notifica()
    },

    elimina(id) {
      const indice = stato.attivita.findIndex((a) => a.id === id)
      if (indice === -1) return null

      // Ricorda posizione e contenuto, per poter annullare
      stato.ultimaEliminata = { attivita: stato.attivita[indice], indice }
      stato.attivita = stato.attivita.filter((a) => a.id !== id)
      notifica()
      return stato.ultimaEliminata.attivita
    },

    annullaEliminazione() {
      if (!stato.ultimaEliminata) return null

      const { attivita, indice } = stato.ultimaEliminata
      stato.attivita = stato.attivita.toSpliced(indice, 0, attivita)
      stato.ultimaEliminata = null
      notifica()
      return attivita
    },

    /** Sposta un'attività da una posizione all'altra. */
    sposta(idOrigine, indiceDestinazione) {
      const indiceOrigine = stato.attivita.findIndex((a) => a.id === idOrigine)
      if (indiceOrigine === -1 || indiceOrigine === indiceDestinazione) return

      const senza = stato.attivita.toSpliced(indiceOrigine, 1)
      // Se si sposta in avanti, la rimozione ha già accorciato l'array
      const destinazione =
        indiceOrigine < indiceDestinazione ? indiceDestinazione - 1 : indiceDestinazione

      stato.attivita = senza.toSpliced(destinazione, 0, stato.attivita[indiceOrigine])
      notifica()
    },

    impostaFiltro(filtro) {
      stato.filtro = filtro
      notifica()
    },

    svuotaCompletate() {
      const quante = stato.attivita.filter((a) => a.completata).length
      stato.attivita = stato.attivita.filter((a) => !a.completata)
      notifica()
      return quante
    },
  }
}

/** Le attività filtrate secondo il filtro corrente. */
export function attivitaVisibili({ attivita, filtro }) {
  switch (filtro) {
    case 'da-fare':
      return attivita.filter((a) => !a.completata)
    case 'completate':
      return attivita.filter((a) => a.completata)
    default:
      return attivita
  }
}

// ── Persistenza ──────────────────────────────────────────────

function caricaDaArchivio() {
  try {
    const grezzo = localStorage.getItem(CHIAVE_ARCHIVIO)
    if (!grezzo) return []

    const analizzato = JSON.parse(grezzo)
    if (!Array.isArray(analizzato)) return []

    // Validazione: l'archivio può contenere dati di una versione
    // precedente, o essere stato modificato a mano
    return analizzato.filter(
      (a) => a && typeof a.id === 'string' && typeof a.testo === 'string',
    )
  } catch (errore) {
    console.warn('Archivio non leggibile, si riparte da zero.', errore)
    return []
  }
}

function salvaInArchivio(attivita) {
  try {
    localStorage.setItem(CHIAVE_ARCHIVIO, JSON.stringify(attivita))
  } catch (errore) {
    // QuotaExceededError, o modalità privata su alcuni browser.
    // L'applicazione deve continuare a funzionare in memoria.
    console.warn('Salvataggio non riuscito.', errore)
  }
}
```

### `src/vista.js`

```javascript
// src/vista.js
// Trasforma lo stato in DOM. Non conosce le azioni: riceve
// solo lo stato e i gestori da collegare.

import { attivitaVisibili } from './stato.js'

const ETICHETTE_FILTRO = {
  tutte: 'Tutte',
  'da-fare': 'Da fare',
  completate: 'Completate',
}

/** Sostituisce i caratteri che avrebbero significato nell'HTML. */
function proteggi(testo) {
  return String(testo).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  )
}

export function creaVista({ radice, store, annuncia }) {
  radice.innerHTML = `
    <header>
      <h1>Attività</h1>
      <form id="modulo-aggiunta">
        <label for="campo-nuova">Nuova attività</label>
        <input type="text" id="campo-nuova" name="testo"
               placeholder="Che cosa c'è da fare?" required
               maxlength="200" autocomplete="off" />
        <button type="submit">Aggiungi</button>
      </form>
    </header>

    <nav aria-label="Filtro delle attività">
      <ul id="filtri">
        ${Object.entries(ETICHETTE_FILTRO)
          .map(
            ([valore, etichetta]) => `
            <li>
              <button type="button" data-filtro="${valore}" aria-pressed="false">
                ${etichetta}
              </button>
            </li>`,
          )
          .join('')}
      </ul>
    </nav>

    <main>
      <ul id="elenco" role="list"></ul>
      <p id="vuoto" hidden>Nessuna attività da mostrare.</p>
    </main>

    <footer>
      <p id="conteggio"></p>
      <button type="button" id="svuota-completate">Elimina le completate</button>
      <button type="button" id="annulla" hidden>Annulla l'eliminazione</button>
    </footer>
  `

  const elenco = radice.querySelector('#elenco')
  const vuoto = radice.querySelector('#vuoto')
  const conteggio = radice.querySelector('#conteggio')
  const comandoAnnulla = radice.querySelector('#annulla')

  function disegna(stato) {
    const visibili = attivitaVisibili(stato)

    elenco.innerHTML = visibili
      .map(
        (a, indice) => `
        <li class="attivita" data-id="${a.id}" data-indice="${indice}" draggable="true">
          <button type="button" class="maniglia" aria-label="Sposta ${proteggi(a.testo)}"
                  aria-describedby="istruzioni-spostamento">⠿</button>

          <input type="checkbox" id="fatto-${a.id}" class="completa"
                 ${a.completata ? 'checked' : ''} />
          <label for="fatto-${a.id}" class="testo ${a.completata ? 'completata' : ''}">
            ${proteggi(a.testo)}
          </label>

          <button type="button" class="elimina">
            <span aria-hidden="true">×</span>
            <span class="solo-screen-reader">Elimina ${proteggi(a.testo)}</span>
          </button>
        </li>`,
      )
      .join('')

    vuoto.hidden = visibili.length > 0

    const daFare = stato.attivita.filter((a) => !a.completata).length
    conteggio.textContent =
      stato.attivita.length === 0
        ? 'Nessuna attività'
        : `${daFare} da fare su ${stato.attivita.length}`

    for (const comando of radice.querySelectorAll('[data-filtro]')) {
      comando.setAttribute('aria-pressed', String(comando.dataset.filtro === stato.filtro))
    }

    comandoAnnulla.hidden = stato.ultimaEliminata === null
  }

  store.iscriviti(disegna)

  return { elenco, radice, annuncia }
}
```

### `src/main.js`

```javascript
// src/main.js
// Collega gli eventi alle azioni dello store. Tutta la delegazione
// sta qui: pochi listener sul contenitore, mai sulle righe.

import { creaStore } from './stato.js'
import { creaVista } from './vista.js'

const radice = document.querySelector('#applicazione')
const annunci = document.querySelector('#annunci')

const store = creaStore()

/** Scrive nella live region: l'annuncio arriva senza spostare il focus. */
function annuncia(messaggio) {
  annunci.textContent = ''
  // Un cambiamento da testo vuoto a testo garantisce l'annuncio
  // anche quando il messaggio è identico al precedente.
  requestAnimationFrame(() => {
    annunci.textContent = messaggio
  })
}

const vista = creaVista({ radice, store, annuncia })

// ── Aggiunta ─────────────────────────────────────────────────
radice.addEventListener('submit', (evento) => {
  if (evento.target.id !== 'modulo-aggiunta') return

  evento.preventDefault()
  const campo = evento.target.elements.testo
  const creata = store.aggiungi(campo.value)

  if (creata) {
    campo.value = ''
    campo.focus()
    annuncia(`Aggiunta: ${creata.testo}`)
  }
})

// ── Clic: completamento, eliminazione, filtri, annullamento ───
radice.addEventListener('click', (evento) => {
  const filtro = evento.target.closest('[data-filtro]')
  if (filtro) {
    store.impostaFiltro(filtro.dataset.filtro)
    annuncia(`Filtro: ${filtro.textContent.trim()}`)
    return
  }

  const elimina = evento.target.closest('.elimina')
  if (elimina) {
    const riga = elimina.closest('.attivita')
    const rimossa = store.elimina(riga.dataset.id)
    if (rimossa) {
      annuncia(`Eliminata: ${rimossa.testo}. Puoi annullare.`)
      // Il pulsante che aveva il focus non esiste più:
      // portalo su un ancoraggio stabile.
      radice.querySelector('#annulla').focus()
    }
    return
  }

  if (evento.target.id === 'annulla') {
    const ripristinata = store.annullaEliminazione()
    if (ripristinata) annuncia(`Ripristinata: ${ripristinata.testo}`)
    return
  }

  if (evento.target.id === 'svuota-completate') {
    const quante = store.svuotaCompletate()
    annuncia(quante === 0 ? 'Nessuna attività completata' : `${quante} attività eliminate`)
  }
})

// ── Commutazione del completamento ───────────────────────────
radice.addEventListener('change', (evento) => {
  if (!evento.target.matches('.completa')) return

  const riga = evento.target.closest('.attivita')
  store.commuta(riga.dataset.id)
})

// ── Modifica in linea: doppio clic ───────────────────────────
radice.addEventListener('dblclick', (evento) => {
  const etichetta = evento.target.closest('.testo')
  if (!etichetta) return

  const riga = etichetta.closest('.attivita')
  const testoAttuale = etichetta.textContent.trim()

  etichetta.innerHTML = `<input type="text" class="modifica"
                                value="${testoAttuale.replace(/"/g, '&quot;')}"
                                aria-label="Modifica l'attività" />`
  const campo = etichetta.querySelector('.modifica')
  campo.focus()
  campo.select()
})

radice.addEventListener('keydown', (evento) => {
  if (!evento.target.matches('.modifica')) return

  if (evento.key === 'Enter') {
    evento.preventDefault()
    const riga = evento.target.closest('.attivita')
    store.modifica(riga.dataset.id, evento.target.value)
    annuncia('Attività aggiornata')
  }

  if (evento.key === 'Escape') {
    // Ridisegna dallo stato: annulla la modifica in corso
    store.impostaFiltro(store.leggi().filtro)
  }
})

radice.addEventListener(
  'focusout',
  (evento) => {
    if (!evento.target.matches('.modifica')) return
    const riga = evento.target.closest('.attivita')
    store.modifica(riga.dataset.id, evento.target.value)
  },
  true, // focusout non fa bubbling da tutti gli elementi: cattura
)

// ── Trascinamento con il mouse ───────────────────────────────
let idTrascinato = null

radice.addEventListener('dragstart', (evento) => {
  const riga = evento.target.closest('.attivita')
  if (!riga) return

  idTrascinato = riga.dataset.id
  riga.classList.add('in-trascinamento')
  evento.dataTransfer.effectAllowed = 'move'
  // Alcuni browser richiedono che qualcosa sia impostato
  evento.dataTransfer.setData('text/plain', idTrascinato)
})

radice.addEventListener('dragover', (evento) => {
  const riga = evento.target.closest('.attivita')
  if (!riga || !idTrascinato) return

  // preventDefault è NECESSARIO: senza, il drop non avviene
  evento.preventDefault()
  evento.dataTransfer.dropEffect = 'move'

  for (const altra of radice.querySelectorAll('.attivita')) {
    altra.classList.toggle('bersaglio', altra === riga)
  }
})

radice.addEventListener('drop', (evento) => {
  const riga = evento.target.closest('.attivita')
  if (!riga || !idTrascinato) return

  evento.preventDefault()
  store.sposta(idTrascinato, Number(riga.dataset.indice))
  annuncia('Attività spostata')
  idTrascinato = null
})

radice.addEventListener('dragend', () => {
  idTrascinato = null
  for (const riga of radice.querySelectorAll('.attivita')) {
    riga.classList.remove('in-trascinamento', 'bersaglio')
  }
})

// ── Riordino DA TASTIERA ─────────────────────────────────────
// Il trascinamento con il mouse non basta: chi non usa il mouse
// deve poter riordinare comunque. Ctrl+Freccia sposta la riga.
radice.addEventListener('keydown', (evento) => {
  const maniglia = evento.target.closest('.maniglia')
  if (!maniglia) return

  const riga = maniglia.closest('.attivita')
  const indice = Number(riga.dataset.indice)
  const visibili = radice.querySelectorAll('.attivita').length

  let destinazione = null
  if (evento.key === 'ArrowUp' && indice > 0) destinazione = indice - 1
  if (evento.key === 'ArrowDown' && indice < visibili - 1) destinazione = indice + 2

  if (destinazione === null) return

  evento.preventDefault()
  const id = riga.dataset.id
  store.sposta(id, destinazione)
  annuncia(`Spostata in posizione ${evento.key === 'ArrowUp' ? indice : indice + 2}`)

  // Il DOM è stato ricostruito: ritrova la maniglia e ridalle il focus
  requestAnimationFrame(() => {
    radice.querySelector(`.attivita[data-id="${id}"] .maniglia`)?.focus()
  })
})

// ── Sincronizzazione fra schede ──────────────────────────────
// L'evento storage scatta nelle ALTRE schede dello stesso dominio.
window.addEventListener('storage', (evento) => {
  if (evento.key === 'todo:attivita:v1') {
    location.reload()
  }
})
```

### `index.html`

```html
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Attività</title>
    <link rel="stylesheet" href="/src/stile.css" />
  </head>

  <body>
    <div id="applicazione"></div>

    <!-- La live region deve ESISTERE prima che il testo cambi -->
    <p id="annunci" role="status" aria-live="polite" class="solo-screen-reader"></p>

    <p id="istruzioni-spostamento" class="solo-screen-reader">
      Usa le frecce su e giù per spostare l'attività.
    </p>

    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

### `src/stile.css`

```css
/* src/stile.css — il minimo perché l'applicazione sia usabile */

:root {
  --testo: #1a1a1a;
  --superficie: #fff;
  --sfondo: #f5f5f5;
  --bordo: #d4d4d4;
  --tenue: #595959;
  --azione: #1d4ed8;
}

@media (prefers-color-scheme: dark) {
  :root {
    --testo: #ececec;
    --superficie: #1c1c1c;
    --sfondo: #121212;
    --bordo: #3a3a3a;
    --tenue: #a3a3a3;
    --azione: #7aa7ff;
  }
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 2rem 1rem;
  font-family: system-ui, sans-serif;
  line-height: 1.6;
  color: var(--testo);
  background: var(--sfondo);
  color-scheme: light dark;
}

#applicazione {
  max-inline-size: 40rem;
  margin-inline: auto;
  padding: 1.5rem;
  background: var(--superficie);
  border-radius: 0.5rem;
}

:focus-visible {
  outline: 3px solid var(--azione);
  outline-offset: 2px;
}

.solo-screen-reader {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

#modulo-aggiunta {
  display: flex;
  gap: 0.5rem;
  align-items: end;
  flex-wrap: wrap;
}

#modulo-aggiunta label {
  flex-basis: 100%;
  font-size: 0.9rem;
  color: var(--tenue);
}

#campo-nuova {
  flex: 1;
  min-inline-size: 12rem;
}

input[type='text'] {
  padding: 0.6rem;
  font: inherit;
  color: inherit;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: 0.25rem;
}

button {
  min-block-size: 2.75rem;
  padding-inline: 1rem;
  font: inherit;
  color: inherit;
  background: transparent;
  border: 1px solid var(--bordo);
  border-radius: 0.25rem;
  cursor: pointer;
}

button[type='submit'] {
  color: #fff;
  background: var(--azione);
  border-color: var(--azione);
}

[aria-pressed='true'] {
  font-weight: 600;
  border-color: var(--azione);
  color: var(--azione);
}

#filtri {
  display: flex;
  gap: 0.5rem;
  padding: 0;
  margin-block: 1.5rem;
  list-style: none;
}

#elenco {
  padding: 0;
  margin: 0;
  list-style: none;
}

.attivita {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding-block: 0.5rem;
  border-block-end: 1px solid var(--bordo);
}

.attivita .testo {
  flex: 1;
  min-inline-size: 0; /* contro l'overflow del testo lungo */
  overflow-wrap: break-word;
}

.attivita .testo.completata {
  text-decoration: line-through;
  color: var(--tenue);
}

.maniglia {
  min-inline-size: 2.75rem;
  cursor: grab;
}

.attivita.in-trascinamento {
  opacity: 0.5;
}

.attivita.bersaglio {
  border-block-start: 2px solid var(--azione);
}

footer {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin-block-start: 1.5rem;
  padding-block-start: 1rem;
  border-block-start: 1px solid var(--bordo);
}

#conteggio {
  flex: 1;
  margin: 0;
  color: var(--tenue);
  font-size: 0.9rem;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Verifica

```powershell
pnpm dev
```

```
# I controlli, in ordine:
#
# 1. PERSISTENZA
#    Aggiungi tre attività, ricarica la pagina: ci sono ancora.
#    DevTools → Application → Local Storage → verifica la chiave
#    'todo:attivita:v1'.
#    Modifica il valore a mano scrivendo "non-json" e ricarica:
#    l'applicazione deve ripartire vuota SENZA errori in console —
#    è ciò che il try/catch in caricaDaArchivio garantisce.
#
# 2. DELEGAZIONE
#    DevTools → Elements → seleziona <ul id="elenco">
#    → pannello Event Listeners: NON deve esserci nessun listener
#    sulle righe. Sono tutti su #applicazione.
#    Aggiungi una riga nuova: funziona senza registrare nulla.
#
# 3. TASTIERA — il controllo che conta di più
#    Tab dall'inizio: campo, Aggiungi, i tre filtri, poi per ogni
#    riga maniglia, casella, elimina.
#    · Invio nel campo aggiunge
#    · Spazio sulla casella completa
#    · Ctrl non serve: le frecce su/giù sulla maniglia riordinano
#    · Il focus RESTA sulla maniglia dopo lo spostamento
#      (è il requestAnimationFrame che lo ripristina)
#    · Esc durante la modifica annulla
#
# 4. TRASCINAMENTO
#    Trascina una riga su un'altra: si sposta.
#    Il riordino da tastiera deve produrre lo STESSO risultato:
#    se solo il mouse funziona, l'applicazione non è utilizzabile
#    da chi non lo usa.
#
# 5. ANNULLAMENTO
#    Elimina un'attività: il pulsante Annulla appare e riceve
#    il focus (il pulsante che l'aveva è stato rimosso dal DOM).
#    Annulla: torna nella POSIZIONE originale, non in fondo.
#
# 6. SCREEN READER
#    NVDA su Windows. Ogni azione deve essere annunciata dalla
#    live region senza che il focus si sposti:
#    "Aggiunta: comprare il latte", "Eliminata: ... Puoi annullare".
#
# 7. DUE SCHEDE
#    Apri l'applicazione in due schede, aggiungi in una:
#    l'altra si ricarica. È l'evento 'storage', che scatta
#    solo nelle ALTRE schede.
```

```
# I meccanismi del tutorial che questo progetto usa, e dove:
#
#   closure           creaStore(): 'stato' e 'iscritti' sono privati
#                     per costruzione, non per convenzione
#   delegazione       6 listener su #applicazione, zero sulle righe
#   metodi immutabili toSpliced, toSorted, map, filter: lo stato
#                     non viene mai modificato sul posto
#   spread            { ...stato } in leggi(): la vista riceve una
#                     copia e non può corrompere il modello
#   dataset           data-id e data-indice collegano DOM e modello
#   optional chaining ?.focus() dopo il ridisegno: l'elemento
#                     potrebbe non esserci più
#   try/catch         localStorage può fallire per quota o modalità
#                     privata: l'applicazione continua in memoria
#   event loop        requestAnimationFrame per ripristinare il focus
#                     DOPO che il browser ha ridisegnato
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Symbol e i well-known symbol

Un `Symbol` è un valore primitivo **unico per costruzione**: due Symbol con la stessa descrizione non sono uguali.

```javascript
const a = Symbol('descrizione')
const b = Symbol('descrizione')

console.log(a === b) // false
console.log(a.description) // 'descrizione'  ← solo per il debug
```

### Come chiavi di proprietà

```javascript
// Il caso d'uso: aggiungere una proprietà a un oggetto che non
// controlli, senza rischiare di sovrascrivere qualcosa.
const CHIAVE_INTERNA = Symbol('metadati')

const utente = {
  nome: 'Anna',
  [CHIAVE_INTERNA]: { ultimoAccesso: Date.now() },
}

// Le chiavi Symbol sono invisibili all'iterazione normale
console.log(Object.keys(utente)) // ['nome']
console.log(JSON.stringify(utente)) // '{"nome":"Anna"}'
for (const chiave in utente) console.log(chiave) // 'nome'

// Ma sono raggiungibili se sai dove guardare
console.log(utente[CHIAVE_INTERNA]) // { ultimoAccesso: ... }
console.log(Object.getOwnPropertySymbols(utente)) // [Symbol(metadati)]
```

**Non sono un meccanismo di sicurezza:** `getOwnPropertySymbols` le rivela. Sono un meccanismo per evitare **collisioni** di nomi.

### Il registro globale

```javascript
// Symbol.for cerca nel registro globale, e crea se non trova.
// Lo stesso Symbol è condiviso fra moduli, iframe e worker.
const condiviso1 = Symbol.for('app.chiave')
const condiviso2 = Symbol.for('app.chiave')
console.log(condiviso1 === condiviso2) // true

console.log(Symbol.keyFor(condiviso1)) // 'app.chiave'
console.log(Symbol.keyFor(Symbol('x'))) // undefined  ← non nel registro
```

### I well-known symbol

Sono punti di aggancio nel linguaggio: definendoli su un oggetto, ne cambi il comportamento con la sintassi nativa.

```javascript
class Intervallo {
  constructor(da, a, passo = 1) {
    this.da = da
    this.a = a
    this.passo = passo
  }

  // Symbol.iterator → l'oggetto funziona con for...of, spread, destructuring
  *[Symbol.iterator]() {
    for (let n = this.da; n <= this.a; n += this.passo) {
      yield n
    }
  }

  // Symbol.toPrimitive → controlla la conversione a numero e stringa
  [Symbol.toPrimitive](suggerimento) {
    if (suggerimento === 'number') return this.a - this.da
    if (suggerimento === 'string') return `[${this.da}..${this.a}]`
    return `Intervallo(${this.da}, ${this.a})`
  }

  // Symbol.toStringTag → cambia il risultato di Object.prototype.toString
  get [Symbol.toStringTag]() {
    return 'Intervallo'
  }

  // Symbol.hasInstance → controlla il comportamento di instanceof
  static [Symbol.hasInstance](valore) {
    return typeof valore?.da === 'number' && typeof valore?.a === 'number'
  }
}

const intervallo = new Intervallo(1, 5)

console.log([...intervallo]) // [1, 2, 3, 4, 5]
for (const n of intervallo) process.stdout?.write?.(`${n} `)

console.log(+intervallo) // 4    ← suggerimento 'number'
console.log(`${intervallo}`) // '[1..5]'  ← suggerimento 'string'
console.log(Object.prototype.toString.call(intervallo)) // '[object Intervallo]'
console.log({ da: 0, a: 3 } instanceof Intervallo) // true  ← hasInstance
```

```javascript
// Symbol.asyncIterator → for await...of
class FlussoDati {
  async *[Symbol.asyncIterator]() {
    for (let pagina = 1; pagina <= 3; pagina++) {
      const risposta = await fetch(`/api/dati?pagina=${pagina}`)
      const dati = await risposta.json()
      yield* dati.elementi
    }
  }
}

// for await (const elemento of new FlussoDati()) { ... }
```

```
I well-known symbol più usati:

  Symbol.iterator       for...of, spread, destructuring
  Symbol.asyncIterator  for await...of
  Symbol.toPrimitive    conversione a numero/stringa
  Symbol.toStringTag    Object.prototype.toString
  Symbol.hasInstance    instanceof
  Symbol.dispose        using (proposta, gestione delle risorse)
```

---

## D2. Iteratori e generatori

### Il protocollo di iterazione

Un oggetto è **iterabile** se ha un metodo `[Symbol.iterator]` che restituisce un **iteratore**: un oggetto con un metodo `next()` che restituisce `{ value, done }`.

```javascript
// Un iteratore scritto a mano
const contatoreManuale = {
  da: 1,
  a: 3,

  [Symbol.iterator]() {
    let corrente = this.da
    const fine = this.a

    return {
      next() {
        return corrente <= fine ? { value: corrente++, done: false } : { value: undefined, done: true }
      },
      // Chiamato quando il ciclo termina prima del tempo (break, throw)
      return() {
        console.log('pulizia')
        return { done: true }
      },
    }
  },
}

console.log([...contatoreManuale]) // [1, 2, 3]
```

### I generatori: la stessa cosa, in dieci volte meno codice

```javascript
function* contatore(da, a) {
  for (let n = da; n <= a; n++) {
    yield n
  }
}

console.log([...contatore(1, 3)]) // [1, 2, 3]

// Un generatore è sia iterabile sia iteratore
const gen = contatore(1, 3)
console.log(gen.next()) // { value: 1, done: false }
console.log(gen.next()) // { value: 2, done: false }
console.log(gen.next()) // { value: 3, done: false }
console.log(gen.next()) // { value: undefined, done: true }
```

> **Analogia:** una funzione normale è un discorso letto tutto d'un fiato: parte e non si ferma finché non finisce. Un generatore è un dialogo: dice una frase, si ferma, aspetta che tu chieda di continuare, e nel frattempo ricorda esattamente dove era rimasto. `yield` è il punto in cui si ferma.

### Pigrizia: sequenze infinite

```javascript
// Un generatore non calcola nulla finché non gli si chiede il prossimo
// valore. Questo rende possibile una sequenza infinita.
function* naturali() {
  let n = 0
  while (true) yield n++
}

function* prendi(iterabile, quanti) {
  let contati = 0
  for (const valore of iterabile) {
    if (contati++ >= quanti) return
    yield valore
  }
}

function* filtra(iterabile, predicato) {
  for (const valore of iterabile) {
    if (predicato(valore)) yield valore
  }
}

function* trasforma(iterabile, funzione) {
  for (const valore of iterabile) yield funzione(valore)
}

// Una pipeline pigra: nessun array intermedio, nessun calcolo superfluo
const primi5Quadrati = [
  ...prendi(
    trasforma(
      filtra(naturali(), (n) => n % 2 === 0),
      (n) => n * n,
    ),
    5,
  ),
]

console.log(primi5Quadrati) // [0, 4, 16, 36, 64]
```

Con `map` e `filter` su array questo sarebbe impossibile: `naturali()` non finisce mai, e `.filter()` proverebbe a percorrerlo tutto.

### `yield*` — delegare a un altro generatore

```javascript
function* interno() {
  yield 'a'
  yield 'b'
}

function* esterno() {
  yield 1
  yield* interno() // delega: cede tutti i valori di interno
  yield* [10, 20] // funziona con qualunque iterabile
  yield 2
}

console.log([...esterno()]) // [1, 'a', 'b', 10, 20, 2]
```

```javascript
// L'uso pratico: percorrere una struttura ad albero
function* attraversa(nodo) {
  yield nodo
  for (const figlio of nodo.figli ?? []) {
    yield* attraversa(figlio)
  }
}

const albero = {
  nome: 'radice',
  figli: [{ nome: 'a', figli: [{ nome: 'a1' }] }, { nome: 'b' }],
}

console.log([...attraversa(albero)].map((n) => n.nome))
// ['radice', 'a', 'a1', 'b']
```

### Comunicazione bidirezionale

```javascript
// next(valore) invia un valore DENTRO il generatore:
// diventa il risultato dell'espressione yield.
function* dialogo() {
  const nome = yield 'Come ti chiami?'
  const eta = yield `Ciao ${nome}, quanti anni hai?`
  return `${nome}, ${eta} anni`
}

const d = dialogo()
console.log(d.next().value) // 'Come ti chiami?'
console.log(d.next('Anna').value) // 'Ciao Anna, quanti anni hai?'
console.log(d.next(34).value) // 'Anna, 34 anni'
```

```javascript
// throw() e return() per il controllo dall'esterno
function* conPulizia() {
  try {
    yield 1
    yield 2
  } finally {
    console.log('risorse liberate')
  }
}

const g = conPulizia()
console.log(g.next().value) // 1
console.log(g.return('interrotto')) // 'risorse liberate'
//   { value: 'interrotto', done: true }
```

Il blocco `finally` viene eseguito anche quando il ciclo si interrompe con `break` — è il meccanismo che rende affidabile la liberazione delle risorse in un generatore.

### Generatori asincroni

```javascript
// Il pattern per consumare un'API paginata senza caricare tutto
async function* recuperaTutteLePagine(urlBase) {
  let pagina = 1
  let ancora = true

  while (ancora) {
    const risposta = await fetch(`${urlBase}?pagina=${pagina}`)
    if (!risposta.ok) throw new Error(`Pagina ${pagina}: ${risposta.status}`)

    const dati = await risposta.json()
    yield* dati.elementi

    ancora = dati.haAltrePagine
    pagina++
  }
}

// Chi consuma vede un flusso continuo, senza sapere delle pagine
// for await (const fattura of recuperaTutteLePagine('/api/fatture')) {
//   elabora(fattura)
//   if (condizioneDiUscita) break   // le pagine successive non
//                                    // vengono nemmeno richieste
// }
```

L'ultimo dettaglio è il punto: con `break`, le richieste rimanenti non partono. Con un `await fetch` di tutte le pagine seguito da un `filter`, sarebbero partite tutte.

---

## D3. Espressioni regolari moderne

```javascript
// Due modi di crearle
const letterale = /\d{4}-\d{2}-\d{2}/
const costruita = new RegExp('\\d{4}-\\d{2}-\\d{2}') // le barre vanno raddoppiate

// I flag
/pattern/g // globale: tutte le corrispondenze
/pattern/i // insensibile a maiuscole e minuscole
/pattern/m // multiriga: ^ e $ valgono per ogni riga
/pattern/s // dotAll: . corrisponde anche agli a capo
/pattern/u // unicode
/pattern/v // unicode con insiemi (ES2024)
/pattern/y // sticky: parte esattamente da lastIndex
/pattern/d // hasIndices: fornisce le posizioni dei gruppi
```

### Gruppi con nome

```javascript
const patternData = /(?<anno>\d{4})-(?<mese>\d{2})-(?<giorno>\d{2})/

const corrispondenza = '2026-04-28'.match(patternData)
console.log(corrispondenza.groups.anno) // '2026'
console.log(corrispondenza.groups.mese) // '04'

// Destructuring diretto dai gruppi
const {
  groups: { anno, mese, giorno },
} = '2026-04-28'.match(patternData)

// Nella sostituzione
console.log('2026-04-28'.replace(patternData, '$<giorno>/$<mese>/$<anno>'))
// '28/04/2026'
```

I gruppi con nome eliminano gli indici numerici, che diventano sbagliati appena qualcuno aggiunge un gruppo all'inizio del pattern.

### Lookahead e lookbehind

```javascript
// (?=...)  lookahead positivo: seguito da
// (?!...)  lookahead negativo: NON seguito da
// (?<=...) lookbehind positivo: preceduto da
// (?<!...) lookbehind negativo: NON preceduto da

// Il numero prima di 'euro', senza catturare 'euro'
console.log('120 euro'.match(/\d+(?= euro)/)[0]) // '120'

// L'importo dopo il simbolo, senza catturarlo
console.log('Totale: €1200'.match(/(?<=€)\d+/)[0]) // '1200'

// Una password con almeno una minuscola, una maiuscola e una cifra
const forte = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{12,}$/
console.log(forte.test('Password1234')) // true
console.log(forte.test('password1234')) // false
```

### `matchAll` e `replaceAll`

```javascript
const testo = 'Fattura 2026-001 del 15/01, fattura 2026-002 del 22/01'
const pattern = /(?<anno>\d{4})-(?<progressivo>\d{3})/g

// matchAll restituisce un iteratore di corrispondenze complete
for (const c of testo.matchAll(pattern)) {
  console.log(c.groups.anno, c.groups.progressivo, 'a posizione', c.index)
}

// Con una funzione di sostituzione
console.log(
  testo.replaceAll(pattern, (intera, anno, progressivo) => `[${anno}/${progressivo}]`),
)

// La forma con i gruppi con nome
console.log(testo.replaceAll(pattern, (...argomenti) => {
  const gruppi = argomenti.at(-1)
  return `${gruppi.progressivo}-${gruppi.anno}`
}))
```

```javascript
// replaceAll con una stringa NON richiede il flag g;
// replace con un pattern globale sì.
// 'a-b'.replace(/-/g, '/')     → 'a/b'
// 'a-b'.replaceAll('-', '/')   → 'a/b'
// 'a-b'.replaceAll(/-/, '/')   → TypeError: serve il flag g
```

### La trappola del flag `g` con `test`

```javascript
// Una regex con /g mantiene lastIndex fra le chiamate:
// test() restituisce risultati alternati sullo stesso input
const conG = /\d+/g

console.log(conG.test('123')) // true
console.log(conG.test('123')) // false  ← lastIndex è a fine stringa
console.log(conG.test('123')) // true   ← si è azzerato

// ✅ Per test(), niente flag g
const senzaG = /\d+/
console.log(senzaG.test('123')) // true
console.log(senzaG.test('123')) // true

// ✅ Oppure azzerare esplicitamente
conG.lastIndex = 0
```

### ReDoS: la regex che blocca il server

```javascript
// ❌ CATASTROFICA — quantificatori annidati su un pattern ambiguo.
//    Il motore prova un numero esponenziale di combinazioni.
const pericolosa = /^(a+)+$/
// pericolosa.test('aaaaaaaaaaaaaaaaaaaaaaaaaaaaX')
// → il thread resta bloccato per minuti

// ❌ Anche questa, molto comune nella validazione delle email
const emailPericolosa = /^([a-zA-Z0-9_.-])+@(([a-zA-Z0-9-])+.)+([a-zA-Z0-9]{2,4})+$/

// ✅ CORRETTO — nessun quantificatore annidato, classi disgiunte
const sicura = /^[a-z]+$/

// ✅ Per le email: non validarle con una regex.
//    <input type="email"> lo fa nel browser, e sul server
//    l'unica verifica che conta è mandare un messaggio all'indirizzo.
```

```javascript
// Costruire una regex da input dell'utente richiede la protezione
function proteggiPerRegex(testo) {
  return testo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const termine = 'costo (netto)'
const pattern = new RegExp(proteggiPerRegex(termine), 'gi')
// Senza la protezione, le parentesi diventerebbero un gruppo
```

L'incidente di Cloudflare del 2 luglio 2019 — 27 minuti di irraggiungibilità globale — fu causato da una regex con backtracking catastrofico in una regola del WAF. Il caso è documentato in [99-CASE-STUDY/cloudflare-regex-2019.md](../99-CASE-STUDY/cloudflare-regex-2019.md).

---

## D4. Memoria, garbage collection e memory leak

### Il modello di memoria

```
STACK                              HEAP
─────────────────────────          ────────────────────────────────
Valori primitivi e riferimenti     Gli oggetti veri e propri
Dimensione nota, veloce            Dimensione variabile
Liberato all'uscita dallo scope    Liberato dal garbage collector

  let n = 42          → 42 nello stack
  let o = { a: 1 }    → il riferimento nello stack,
                        { a: 1 } nell'heap
```

### Come funziona la raccolta

V8 usa un garbage collector **generazionale**, basato sulla raggiungibilità: un oggetto è vivo se è raggiungibile da una radice (le variabili globali, lo stack corrente).

```
Giovane generazione (Scavenger)
  · piccola, raccolta molto spesso
  · la maggioranza degli oggetti muore qui: è l'ipotesi generazionale
  · copia i sopravvissuti, veloce

Vecchia generazione (Mark-Compact)
  · oggetti sopravvissuti a più raccolte giovani
  · raccolta rara e più costosa
  · marca i raggiungibili, poi compatta
```

Il conteggio dei riferimenti non è usato proprio perché non gestirebbe i cicli: due oggetti che si referenziano a vicenda ma non sono raggiungibili da nessuna radice vengono comunque raccolti.

### Le quattro cause di memory leak

```javascript
// ── 1. LISTENER MAI RIMOSSI ─────────────────────────────────
// ❌ Il listener tiene vivo 'elemento' e tutta la sua closure,
//    anche dopo che l'elemento è stato rimosso dal DOM.
function creaComponenteSbagliato(elemento) {
  const datiPesanti = new Array(1_000_000).fill('x')

  window.addEventListener('resize', () => {
    elemento.textContent = datiPesanti.length
  })
}

// ✅ AbortController: un solo abort() rimuove tutto
function creaComponente(elemento) {
  const controller = new AbortController()
  const datiPesanti = new Array(1_000_000).fill('x')

  window.addEventListener(
    'resize',
    () => {
      elemento.textContent = datiPesanti.length
    },
    { signal: controller.signal },
  )

  return () => controller.abort() // funzione di pulizia
}

// ── 2. TIMER MAI FERMATI ────────────────────────────────────
// ❌ setInterval continua per sempre e tiene vivo tutto ciò
//    che la sua closure referenzia
function avviaAggiornamentoSbagliato(componente) {
  setInterval(() => componente.aggiorna(), 1000)
}

// ✅ Restituire l'identificativo, e fermarlo
function avviaAggiornamento(componente) {
  const id = setInterval(() => componente.aggiorna(), 1000)
  return () => clearInterval(id)
}

// ── 3. RIFERIMENTI IN STRUTTURE GLOBALI ─────────────────────
// ❌ La cache cresce per sempre: nessuno la svuota
const cacheSbagliata = new Map()
function memorizza(elemento, dati) {
  cacheSbagliata.set(elemento, dati) // l'elemento non muore mai
}

// ✅ WeakMap: la chiave non impedisce la raccolta.
//    Quando l'elemento del DOM sparisce, la voce sparisce con lui.
const cache = new WeakMap()
function memorizzaBene(elemento, dati) {
  cache.set(elemento, dati)
}

// ── 4. RIFERIMENTI AL DOM DOPO LA RIMOZIONE ─────────────────
// ❌ L'array tiene vivo l'intero sottoalbero di ogni riga,
//    anche dopo che la tabella è stata svuotata
const righeSbagliate = []
function registra(riga) {
  righeSbagliate.push(riga)
}

// ✅ Conserva l'identificativo, non il nodo
const idRighe = []
function registraBene(riga) {
  idRighe.push(riga.dataset.id)
}
```

### Diagnosticare

```
DevTools → Memory

1. HEAP SNAPSHOT — la fotografia
   · Scatta uno snapshot
   · Compi l'azione sospetta dieci volte
   · Forza la raccolta (l'icona del cestino)
   · Scatta un secondo snapshot
   · Confronto: "Comparison" mostra il delta fra i due
   · Se il conteggio di Detached HTMLElement cresce, hai
     nodi rimossi dal DOM ma ancora referenziati

2. ALLOCATION TIMELINE — dove nasce la memoria
   · Registra durante l'interazione
   · Le barre blu che NON diventano grigie sono memoria
     allocata e mai liberata
   · Cliccando una barra si vede lo stack di allocazione

3. PERFORMANCE MONITOR — il grafico continuo
   · JS heap size: deve oscillare, non crescere costantemente
   · DOM Nodes: se cresce senza scendere, i nodi non vengono
     raccolti
```

```javascript
// Misurare da codice, dove l'API è disponibile
if (performance.memory) {
  const mb = (b) => (b / 1024 / 1024).toFixed(1)
  console.log(`heap usato: ${mb(performance.memory.usedJSHeapSize)} MB`)
}

// L'API standard, più recente e con più dettaglio
if (performance.measureUserAgentSpecificMemory) {
  const misura = await performance.measureUserAgentSpecificMemory()
  console.log(misura.bytes, misura.breakdown)
}
```

### `WeakRef` e `FinalizationRegistry`

```javascript
// WeakRef: un riferimento che non impedisce la raccolta
const riferimentoDebole = new WeakRef(oggettoPesante)

// deref() restituisce l'oggetto, o undefined se è stato raccolto
const forse = riferimentoDebole.deref()
if (forse) {
  usa(forse)
}

// FinalizationRegistry: un callback dopo la raccolta.
// L'esecuzione NON è garantita né prevedibile nel tempo:
// serve per la diagnostica, mai per la logica applicativa.
const registro = new FinalizationRegistry((etichetta) => {
  console.log(`${etichetta} è stato raccolto`)
})

registro.register(oggettoPesante, 'cache-immagini')
```

Entrambi sono strumenti da usare con cautela: la specifica non garantisce *quando* la raccolta avvenga, quindi costruirci sopra della logica produce comportamenti diversi fra browser e fra esecuzioni.

---

## D5. Come V8 esegue il tuo codice

### La pipeline

```
  SORGENTE
     │
     ▼
  PARSER ──────────► AST (albero sintattico astratto)
     │                 · il parsing pigro salta le funzioni
     ▼                   non ancora chiamate
  IGNITION ────────► bytecode
     │                 · interprete: parte subito, esegue lentamente
     │                 · raccoglie profili di tipo mentre esegue
     ▼
  SPARKPLUG ───────► codice macchina non ottimizzato
     │                 · compilazione quasi istantanea
     ▼
  MAGLEV ──────────► codice macchina mediamente ottimizzato
     │
     ▼
  TURBOFAN ────────► codice macchina molto ottimizzato
                       · solo per il codice caldo (eseguito molte volte)
                       · assume che i tipi restino quelli osservati
                       · se l'assunzione salta → DEOTTIMIZZAZIONE,
                         e si torna al bytecode
```

### Hidden class e inline cache

V8 non tratta gli oggetti come dizionari: costruisce una **hidden class** per ogni forma di oggetto incontrata, e la riusa.

```javascript
// ✅ Stessa forma → stessa hidden class → accesso veloce
function creaPunto(x, y) {
  return { x, y }
}

const p1 = creaPunto(1, 2)
const p2 = creaPunto(3, 4) // stessa hidden class di p1

// ❌ Aggiungere proprietà dopo la creazione cambia la hidden class:
//    ogni transizione invalida le ottimizzazioni fatte
const p3 = {}
p3.x = 1 // hidden class C0 → C1
p3.y = 2 // C1 → C2

// ❌ Ordine diverso → hidden class DIVERSE, anche se le proprietà
//    sono le stesse
const a = { x: 1, y: 2 }
const b = { y: 2, x: 1 } // hidden class diversa da a
```

```javascript
// ❌ SBAGLIATO — la forma cambia a seconda del ramo:
//    il sito di accesso diventa polimorfico e l'ottimizzazione salta
function creaUtenteVariabile(dati) {
  const u = { nome: dati.nome }
  if (dati.email) u.email = dati.email
  if (dati.telefono) u.telefono = dati.telefono
  return u
}

// ✅ CORRETTO — forma STABILE: i campi assenti valgono null
function creaUtente(dati) {
  return {
    nome: dati.nome,
    email: dati.email ?? null,
    telefono: dati.telefono ?? null,
  }
}
```

### Consigli che hanno un effetto misurabile

```javascript
// 1. Array monomorfici: non mescolare i tipi
const veloce = [1, 2, 3] // PACKED_SMI_ELEMENTS
const lento = [1, 'due', {}] // PACKED_ELEMENTS: nessuna ottimizzazione

// 2. Niente buchi negli array
const conBuchi = [1, , 3] // HOLEY_ELEMENTS: ogni accesso
//   deve verificare il buco
const senzaBuchi = [1, 0, 3]

// ❌ new Array(n) crea un array pieno di buchi
const male = new Array(1000)

// ✅
const bene = Array.from({ length: 1000 }, () => 0)

// 3. Funzioni monomorfiche: chiamale sempre con gli stessi tipi
function somma(a, b) {
  return a + b
}
somma(1, 2) // monomorfica: veloce
// somma('a', 'b')   // ora è polimorfica: più lenta per entrambi

// 4. delete deottimizza l'oggetto: preferisci l'assegnazione a null
// delete oggetto.campo        ← passa a modalità dizionario
// oggetto.campo = null        ← conserva la hidden class
```

### Misurare, non indovinare

```powershell
# Vedere le decisioni di ottimizzazione di V8
node --trace-opt --trace-deopt script.js

# Il bytecode generato
node --print-bytecode script.js
```

```javascript
// Il benchmark che vale: confrontare due implementazioni
// sulla stessa macchina, con lo stesso carico.
function misura(nome, funzione, iterazioni = 1_000_000) {
  // Riscaldamento: le prime esecuzioni girano nell'interprete
  for (let i = 0; i < 10_000; i++) funzione()

  const inizio = performance.now()
  for (let i = 0; i < iterazioni; i++) funzione()
  const durata = performance.now() - inizio

  console.log(`${nome.padEnd(24)} ${durata.toFixed(1)} ms`)
  return durata
}
```

**L'avvertenza che conta più dei consigli:** questi accorgimenti hanno effetto su cicli caldi eseguiti milioni di volte. Nel codice di un'interfaccia, il collo di bottiglia è quasi sempre il layout del browser, una richiesta di rete, o un algoritmo con complessità sbagliata — non la forma degli oggetti. Ottimizzare per V8 prima di aver profilato è tempo speso male, e produce codice meno leggibile in cambio di nulla.

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
FONDAMENTI DI JAVASCRIPT — Mappa dei concetti

VALORI E TIPI
├── 7 primitivi: string number bigint boolean undefined null symbol
│   └── + object (array, funzioni, date: tutto è object)
├── typeof null === 'object'  ← il bug del 1995, mai corretto
├── Numeri: SOLO float 64 bit
│   ├── 0.1 + 0.2 !== 0.3
│   ├── per il denaro: interi in centesimi
│   └── NaN !== NaN → Number.isNaN()
├── Stringhe: immutabili, UTF-16 ('👍'.length === 2)
├── undefined = "non lo so"   ·   null = "so che non c'è"
└── Primitivi per VALORE, oggetti per RIFERIMENTO
      { a: 1 } === { a: 1 }  →  false

VARIABILI
├── const sempre · let se cambia · var mai
├── Hoisting: var → undefined · let/const → TDZ (ReferenceError)
└── const NON è immutabile: blocca il nome, non il contenuto
      Object.freeze è SUPERFICIALE

COERCIZIONE
├── === sempre. == solo per "== null" (null e undefined insieme)
├── 8 falsy: false 0 -0 0n '' null undefined NaN
│   └── [] e {} sono TRUTHY
├── ||  → primo truthy   (scarta 0 e '')
├── ??  → primo non-nullish (0 e '' passano)
└── ?.  interrompe su null/undefined

SCOPE E CLOSURE
├── Lessicale: deciso da DOVE è scritto, non da dove è chiamato
├── Closure = la funzione porta con sé lo scope in cui è NATA
│   └── stato privato · memoizzazione · debounce · throttle
└── for con let → una variabile NUOVA per giro
      for con var → una sola, condivisa da tutti i callback

THIS — cinque regole, in ordine di precedenza
├── 1. new              → l'oggetto nuovo
├── 2. call/apply/bind  → quello imposto
├── 3. oggetto.metodo() → l'oggetto PRIMA DEL PUNTO
├── 4. funzione()       → undefined (strict/moduli)
└── 5. arrow            → lo scope in cui è SCRITTA — vince su tutte
      Il metodo estratto PERDE il binding: bind, o arrow che lo chiama
      Nei listener: evento.currentTarget invece di this

PROTOTIPI
├── Gli oggetti DELEGANO ad altri oggetti, non copiano
├── La ricerca risale la catena fino a null
├── class è zucchero sintattico: stessa struttura
│   └── ma: non sollevata · strict · metodi non enumerabili
│           · new obbligatorio · campi privati con #
└── super() PRIMA di this nel costruttore

ARRAY
├── Trasformano: map filter reduce flatMap
├── Cercano: find findIndex some every includes
├── MODIFICANO: push pop splice sort reverse
├── NON modificano: slice concat toSorted toReversed with
├── sort() senza confronto ordina come STRINGHE
└── Object.groupBy per raggruppare (ES2024)

DOM
├── querySelector / querySelectorAll (statica)
│   └── getElementsBy* restituisce collezioni VIVE
├── textContent (sicuro) ≠ innerHTML (interpreta markup)
├── DocumentFragment per inserire molti nodi
└── classList · dataset · getComputedStyle

EVENTI
├── cattura (giù) → bersaglio → risalita (su)
├── target = dove è successo · currentTarget = dove ascolti
├── DELEGAZIONE: un listener sul contenitore + closest()
│   └── funziona anche per gli elementi aggiunti dopo
├── { once, passive, signal, capture }
├── AbortController per rimuoverne molti insieme
└── stopPropagation rompe la delegazione altrui: quasi mai giusto

MODULI ES
├── Sempre strict · scope di modulo · differiti per natura
├── Binding VIVI, non copie
├── import() dinamico → code splitting
└── Statici → tree shaking (CommonJS no)

EVENT LOOP
├── 1. TUTTO il codice sincrono
├── 2. TUTTI i microtask (Promise, await, queueMicrotask)
│      comprese quelle accodate durante lo svuotamento
├── 3. rendering (~16,7 ms)
├── 4. UNA macrotask (setTimeout, eventi), poi si torna al 2
├── setTimeout(f, 0) ≠ "subito"
└── Un microtask ricorsivo blocca la pagina per sempre

ERRORI
├── cause per non perdere l'errore originale (ES2022)
├── Result pattern quando l'errore è previsto dal dominio
├── throw quando è anomalo e chi chiama non può farci nulla
└── try NON cattura ciò che avviene dentro un callback asincrono

STRUTTURE
├── Map: chiavi di qualunque tipo, ordine, .size
├── Set: unicità, has() in O(1) invece di includes() in O(n)
└── WeakMap/WeakSet: non impediscono la raccolta della memoria
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai elencare i sette primitivi e perché `typeof null` mente
- [ ] Sai perché `0.1 + 0.2 !== 0.3` e come trattare il denaro
- [ ] Distingui `null` da `undefined` e sai quando usare quale
- [ ] Sai perché `const` non rende immutabile, e cosa fa `Object.freeze`
- [ ] Sai spiegare hoisting e temporal dead zone
- [ ] Conosci gli otto valori falsy e sai che `[]` e `{}` non lo sono
- [ ] Sai quando `||` è sbagliato e serve `??`
- [ ] Scegli il ciclo giusto e sai perché `for...in` non va sugli array
- [ ] Conosci le tre forme di funzione e le differenze di hoisting
- [ ] Usi il destructuring nei parametri con `= {}` finale
- [ ] Distingui i metodi di array che modificano da quelli che non lo fanno
- [ ] Sai perché `sort()` senza confronto ordina `[10, 9, 1]` come `[1, 10, 9]`
- [ ] Sai che la copia con spread è superficiale, e cosa usare per quella profonda

**Parte B — Comprensione**

- [ ] Sai spiegare una closure e scrivere un contatore con stato privato
- [ ] Sai perché `var` in un ciclo produce tre volte lo stesso valore
- [ ] Sai enunciare le cinque regole di `this` in ordine di precedenza
- [ ] Sai diagnosticare un `this` perduto e correggerlo in tre modi
- [ ] Sai disegnare la catena prototipale di un oggetto
- [ ] Sai perché i metodi vanno sul prototipo e non nel costruttore
- [ ] Sai cosa `class` aggiunge davvero rispetto ai prototipi
- [ ] Distingui `textContent` da `innerHTML` e sai quando ciascuno è sicuro
- [ ] Sai perché `getElementsByClassName` in un ciclo di rimozione salta elementi
- [ ] Usi `DocumentFragment` per inserire molti nodi
- [ ] Sai descrivere le tre fasi di propagazione di un evento
- [ ] Implementi la delegazione con `closest()` e sai perché conviene
- [ ] Sai a cosa serve `{ passive: true }` e su quali eventi
- [ ] Usi `AbortController` per rimuovere più listener insieme
- [ ] Sai perché gli import ES sono binding vivi e non copie
- [ ] Sai prevedere l'ordine di sincrono, microtask e macrotask
- [ ] Sai perché un microtask ricorsivo blocca la pagina
- [ ] Sai spezzare un calcolo lungo senza congelare l'interfaccia
- [ ] Usi `cause` per conservare l'errore originale
- [ ] Sai quando usare `throw` e quando un pattern a risultato
- [ ] Sai quando `Map` e `Set` battono oggetti e array

**Parte C — Pratica**

- [ ] Hai previsto correttamente l'output dell'esercizio 1 prima di eseguirlo
- [ ] Hai implementato contatore, memoizzazione e debounce con le closure
- [ ] Hai corretto i quattro errori di `this` dell'esercizio 3
- [ ] Hai previsto correttamente l'ordine dell'event loop dell'esercizio 6
- [ ] Hai costruito la todo-list e verificato il riordino DA TASTIERA

**Parte D — Esperto**

- [ ] Sai a cosa servono i Symbol e perché non sono un meccanismo di sicurezza
- [ ] Sai implementare `Symbol.iterator` con un generatore
- [ ] Sai perché un generatore permette sequenze infinite
- [ ] Usi `yield*` per delegare e per attraversare un albero
- [ ] Usi i gruppi con nome invece degli indici numerici
- [ ] Sai perché `test()` con il flag `g` alterna i risultati
- [ ] Riconosci una regex a rischio ReDoS
- [ ] Sai elencare le quattro cause di memory leak e le rispettive correzioni
- [ ] Sai usare gli heap snapshot per trovare i nodi staccati
- [ ] Sai cos'è una hidden class e perché la forma stabile degli oggetti conta
- [ ] Sai perché ottimizzare per V8 prima di profilare è tempo sprecato

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `var` | Scope di funzione, hoisting a `undefined`, ridichiarazione silenziosa | `const`, e `let` se deve cambiare |
| `==` | Coercizione con regole non transitive: `0 == ''` è `true` | `===`, tranne `== null` per null e undefined insieme |
| `if (!valore)` per verificare l'assenza | Scarta anche `0` e `''`, che spesso sono validi | `if (valore == null)` |
| `opzioni.x || predefinito` | `0` e `''` attivano il ripiego | `opzioni.x ?? predefinito` |
| `sort()` senza funzione di confronto | Ordina come stringhe: `[1, 10, 9]` | `toSorted((a, b) => a - b)` |
| `sort()` su un array ricevuto | Modifica l'originale sotto i piedi del chiamante | `toSorted()` o `[...array].sort()` |
| `innerHTML` con dati dell'utente | Cross-site scripting | `textContent`, o DOMPurify se serve markup |
| `for...in` su un array | Chiavi stringa, ordine non garantito, proprietà ereditate | `for...of`, o `.entries()` con l'indice |
| Metodo nel costruttore invece che sul prototipo | Una copia della funzione per ogni istanza | Sul prototipo, o metodo di classe |
| Un listener per elemento | N listener, e nulla per gli elementi aggiunti dopo | Delegazione con `closest()` |
| `stopPropagation()` per abitudine | Rompe la delegazione di chi sta sopra, senza avvisarlo | Verificare `target` nel gestore del contenitore |
| Passare un metodo come callback | Perde il binding implicito: `this` diventa altro | Arrow che lo chiama, `bind`, o campo arrow |
| Arrow come metodo di un oggetto | Non ha `this` proprio: prende quello esterno | Metodo normale |
| Ciclo lungo sul thread principale | Congela clic, animazioni e rendering | Spezzare con `await`, o un Web Worker |
| `setTimeout(f, 0)` per "eseguire subito" | Va dopo tutto il codice sincrono e tutti i microtask | `queueMicrotask()` se serve prima del rendering |
| Microtask ricorsiva | La coda non si svuota mai: la pagina si blocca | `setTimeout` per cedere il controllo |
| `catch` che rilancia un errore nuovo | Perde la causa originale e la sua traccia | `new Error(msg, { cause: errore })` |
| `try` attorno a un callback asincrono | Non cattura nulla: il callback gira in un altro turno | Il `try` va dentro il callback |
| Listener mai rimossi | Tengono viva la closure e i nodi del DOM | `AbortController` con `signal` |
| `setInterval` senza `clearInterval` | Continua per sempre, e trattiene tutto ciò che referenzia | Restituire una funzione di pulizia |
| Cache globale con chiavi oggetto | Impedisce la raccolta della memoria | `WeakMap` |
| `includes()` in un ciclo | O(n²) su elenchi grandi | `Set` con `has()`, O(1) |
| `delete oggetto.campo` | Fa passare V8 alla modalità dizionario | `oggetto.campo = null` |
| Regex con quantificatori annidati | Backtracking catastrofico: blocca il thread | Riscrivere il pattern senza ambiguità |
| `/g` con `test()` | `lastIndex` persiste: risultati alternati | Niente `g` per `test()` |
| Ottimizzare per V8 senza profilare | Codice meno leggibile, guadagno nullo | Misurare prima, con il pannello Performance |

---

## Troubleshooting rapido

**`TypeError: Cannot read properties of undefined (reading 'x')`**
- Causa: si accede a una proprietà di qualcosa che è `undefined` o `null`
- Fix: `valore?.x` per interrompere in sicurezza; risalire a chi doveva assegnare `valore`

**`TypeError: Cannot read properties of null` su un elemento del DOM**
- Causa: lo script gira prima che l'elemento esista — script classico nel `<head>`, o selettore sbagliato
- Fix: `<script type="module">` o `defer`; verificare il selettore in console

**`ReferenceError: Cannot access 'x' before initialization`**
- Causa: temporal dead zone — si usa una `let`/`const` prima della sua riga di dichiarazione
- Fix: spostare la dichiarazione prima dell'uso

**`this` è `undefined` dentro un metodo**
- Causa: il metodo è stato estratto e passato come callback, oppure è una `function` dentro `setTimeout`/`map`
- Fix: arrow function, `bind`, o campo arrow di classe

**Un listener non scatta sugli elementi aggiunti dopo**
- Causa: registrato sugli elementi esistenti al momento della registrazione
- Fix: delegazione — un listener sul contenitore con `closest()`

**`removeEventListener` non rimuove nulla**
- Causa: è stata passata una funzione diversa, anche se il corpo è identico
- Fix: conservare il riferimento alla funzione, o usare `AbortController`

**Le modifiche a un oggetto si riflettono dove non dovrebbero**
- Causa: gli oggetti si passano per riferimento; lo spread copia solo il primo livello
- Fix: `structuredClone()` per una copia profonda

**Un ciclo che rimuove elementi ne salta la metà**
- Causa: si sta iterando una `HTMLCollection` viva mentre la si modifica
- Fix: `querySelectorAll`, che restituisce una NodeList statica

**`setTimeout` con `0` non esegue subito**
- Causa: è una macrotask — va dopo il codice sincrono e dopo tutti i microtask
- Fix: `queueMicrotask()` se serve prima del rendering; `requestAnimationFrame()` se serve prima del disegno

**Il totale ha molti decimali inattesi**
- Causa: aritmetica in virgola mobile su valori monetari
- Fix: lavorare in centesimi con numeri interi, e formattare solo per la visualizzazione

**`JSON.parse` fallisce su dati che sembrano corretti**
- Causa: la risposta non è JSON — spesso una pagina di errore HTML
- Fix: verificare `risposta.ok` e `Content-Type` prima di analizzare; stampare il testo grezzo

**`[object Object]` a schermo**
- Causa: un oggetto convertito in stringa implicitamente
- Fix: `JSON.stringify(oggetto)` per il debug; la proprietà giusta per la visualizzazione

**Una regex funziona nel tester e non nel codice**
- Causa: con `new RegExp('...')` le barre rovesciate vanno raddoppiate
- Fix: usare la forma letterale `/pattern/`, o raddoppiare gli escape

**La pagina rallenta progressivamente nel tempo**
- Causa: memory leak — listener, timer o riferimenti al DOM mai liberati
- Fix: DevTools → Memory → confronto fra due heap snapshot; cercare i `Detached HTMLElement`

**`Maximum call stack size exceeded`**
- Causa: ricorsione senza condizione d'uscita, o troppo profonda
- Fix: verificare il caso base; convertire in iterazione, o usare un generatore

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_05_javascript_avanzato.md` | Promise e async/await in profondità, pattern funzionali, metaprogrammazione, Web Workers |
| `tutorial_06_typescript.md` | Tipizzare tutto ciò che qui è dinamico: gli errori di `this` e di forma diventano errori di compilazione |
| `tutorial_07_react.md` | Le closure sotto gli hook, il perché delle dipendenze di `useEffect` |
| `tutorial_10_nodejs.md` | Lo stesso linguaggio sul server: moduli, event loop, stream |
| `tutorial_14_sicurezza_web.md` | XSS in profondità: perché `innerHTML` con dati dell'utente è un vettore |
| `tutorial_15_testing_web.md` | Testare le funzioni pure, il DOM e gli eventi di questo tutorial |
| `tutorial_17_performance_web.md` | Long task, profiling e il costo reale delle scelte fatte qui |

---

## Risorse di riferimento

**Specifiche e documentazione:**
- [MDN — JavaScript](https://developer.mozilla.org/it/docs/Web/JavaScript) — il riferimento, in italiano per gran parte
- [ECMAScript Language Specification](https://tc39.es/ecma262/) — la norma, quando la documentazione non basta
- [TC39 Proposals](https://github.com/tc39/proposals) — cosa sta arrivando, e a che stadio
- [MDN — DOM](https://developer.mozilla.org/it/docs/Web/API/Document_Object_Model)

**Materiale didattico:**
- [javascript.info](https://it.javascript.info/) — il tutorial più completo, tradotto in italiano
- [web.dev — Learn JavaScript](https://web.dev/learn/javascript) — corso strutturato di Google
- [Jake Archibald — In The Loop](https://www.youtube.com/watch?v=cCOL7MC4Pl0) — l'event loop spiegato visivamente
- [Loupe](http://latentflip.com/loupe/) — visualizzatore interattivo dell'event loop

**Libri, tutti disponibili gratuitamente online:**
- Marijn Haverbeke, *Eloquent JavaScript* (4ª ed.) — teoria e pratica, con esercizi progressivi
- Kyle Simpson, *You Don't Know JS Yet* — sei volumi su scope, closure, `this`, prototipi e tipi
- Axel Rauschmayer, *JavaScript for impatient programmers* — moderno e conciso

**Strumenti:**
- [Can I use](https://caniuse.com/) — supporto dei browser
- [ESLint](https://eslint.org/) — intercetta gran parte degli anti-pattern di questa tabella
- [regex101.com](https://regex101.com/) — con la spiegazione passo passo del pattern
- [Bundlephobia](https://bundlephobia.com/) — quanto pesa una dipendenza prima di aggiungerla

---

> **Fine del Tutorial 04 — Fondamenti di JavaScript**
>
> Prossimo tutorial: `tutorial_05_javascript_avanzato.md`
