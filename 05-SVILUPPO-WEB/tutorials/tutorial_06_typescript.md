# Tutorial 06 — TypeScript: Dal Principiante all'Esperto

> **Companion a:** `06-typescript.md`
> **Scope:** Inferenza e annotazioni, union e literal type, type narrowing e discriminated union, `interface` contro `type`, generics e constraint, `any`/`unknown`/`never`, tipizzazione strutturale, utility type e come sono costruiti, mapped e conditional type con `infer`, `as const` e `satisfies`, branded type, `tsconfig.json` e i flag strict, file di dichiarazione e module augmentation, validazione a runtime con Zod, project reference, performance del compilatore, migrazione da JavaScript
> **Prerequisiti:** `tutorial_04_javascript_fondamenti.md` e `tutorial_05_javascript_avanzato.md` — closure, `this`, prototipi, Promise, moduli
> **Durata stimata:** 28-35 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** TypeScript 5.6+ · Node.js LTS · Vite · Zod 3.x

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Quale problema risolve TypeScript](#a1-quale-problema-risolve-typescript)
  - [A2. Installazione e primo file](#a2-installazione-e-primo-file)
  - [A3. Tipi primitivi e inferenza](#a3-tipi-primitivi-e-inferenza)
  - [A4. Array, tuple e oggetti](#a4-array-tuple-e-oggetti)
  - [A5. Union, literal type e narrowing di base](#a5-union-literal-type-e-narrowing-di-base)
  - [A6. Funzioni](#a6-funzioni)
  - [A7. `interface` e `type`](#a7-interface-e-type)
  - [A8. `any`, `unknown`, `never`, `void`](#a8-any-unknown-never-void)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Il sistema di tipi è strutturale](#b1-il-sistema-di-tipi-è-strutturale)
  - [B2. Type narrowing in profondità](#b2-type-narrowing-in-profondità)
  - [B3. Generics](#b3-generics)
  - [B4. Utility type, e come sono costruiti](#b4-utility-type-e-come-sono-costruiti)
  - [B5. Mapped type, conditional type e `infer`](#b5-mapped-type-conditional-type-e-infer)
  - [B6. `as const`, `satisfies` e branded type](#b6-as-const-satisfies-e-branded-type)
  - [B7. `tsconfig.json` e i flag strict](#b7-tsconfigjson-e-i-flag-strict)
  - [B8. File di dichiarazione e augmentation](#b8-file-di-dichiarazione-e-augmentation)
  - [B9. Il confine con il runtime: Zod](#b9-il-confine-con-il-runtime-zod)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la todo-list convertita a TypeScript](#c2-mini-progetto-la-todo-list-convertita-a-typescript)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Programmazione a livello di tipi](#d1-programmazione-a-livello-di-tipi)
  - [D2. Project reference e build incrementali](#d2-project-reference-e-build-incrementali)
  - [D3. Performance del compilatore](#d3-performance-del-compilatore)
  - [D4. Migrare un progetto JavaScript](#d4-migrare-un-progetto-javascript)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                             TYPESCRIPT
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
        ┌─────────▼──────────┐          ┌─────────▼──────────┐
        │   TEMPO DI BUILD   │          │      RUNTIME       │
        │                    │          │                    │
        │  i tipi esistono   │          │  i tipi NON        │
        │  il compilatore    │          │  esistono più      │
        │  verifica          │          │                    │
        │                    │          │  serve Zod, o      │
        │  ↓ cancellazione   │          │  un type guard     │
        └─────────┬──────────┘          └─────────┬──────────┘
                  └───────────────┬───────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
┌─────▼──────────┐      ┌─────────▼─────────┐      ┌──────────▼────────┐
│    I TIPI      │      │    NARROWING      │      │    GENERICS       │
│                │      │                   │      │                   │
│ primitivi      │      │ typeof            │      │ <T>               │
│ literal        │      │ instanceof        │      │ extends (vincolo) │
│ union    A | B │      │ in                │      │ keyof             │
│ intersect A & B│      │ truthiness        │      │ typeof            │
│ tuple          │      │ discriminated     │      │ infer             │
│ object         │      │  union  ← il      │      │ default <T = X>   │
│                │      │  pattern centrale │      │                   │
│ any     spegne │      │ type predicate    │      │ mapped type       │
│ unknown sicuro │      │  x is T           │      │ conditional type  │
│ never   vuoto  │      │ assertion         │      │  T extends U ? A:B│
│ void    ritorno│      │  asserts x is T   │      │                   │
└────────────────┘      └───────────────────┘      └───────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
┌─────▼──────────┐      ┌─────────▼─────────┐      ┌──────────▼────────┐
│  STRUTTURALE   │      │    STRUMENTI      │      │   CONFIGURAZIONE  │
│                │      │                   │      │                   │
│ conta la FORMA │      │ Partial  Required │      │ strict            │
│ non il nome    │      │ Pick     Omit     │      │  ├ noImplicitAny  │
│                │      │ Record   Readonly │      │  ├ strictNullCheck│
│ due tipi con   │      │ Exclude  Extract  │      │  ├ strictFunction │
│ gli stessi     │      │ ReturnType        │      │  └ ...            │
│ campi sono     │      │ Awaited           │      │ noUncheckedIndex  │
│ intercambiabili│      │ NoInfer           │      │  Access           │
│                │      │                   │      │ verbatimModule    │
│ branded type   │      │ as const          │      │  Syntax           │
│ per distinguere│      │ satisfies         │      │ project reference │
└────────────────┘      └───────────────────┘      └───────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Quale problema risolve TypeScript

> **Analogia:** costruire un mobile con o senza il disegno tecnico. Senza, tagli i pezzi, li assembli, e scopri all'ultimo che il ripiano è tre centimetri troppo corto — quando hai già tagliato. Con il disegno, l'errore emerge sulla carta, prima che il legno sia rovinato. TypeScript è il disegno tecnico: non cambia il mobile finito, cambia quando scopri gli errori.

```javascript
// JavaScript: l'errore emerge in esecuzione, forse in produzione
function calcolaSconto(prezzo, percentuale) {
  return prezzo - prezzo * (percentuale / 100)
}

calcolaSconto(100, 20) // 80
calcolaSconto('100', 20) // '100' - ... → NaN, silenziosamente
calcolaSconto(100) // NaN
calcolaSconto(100, 20, 5) // l'argomento in più è ignorato
```

```typescript
// TypeScript: gli stessi errori sono segnalati mentre scrivi
function calcolaSconto(prezzo: number, percentuale: number): number {
  return prezzo - prezzo * (percentuale / 100)
}

calcolaSconto(100, 20) // ok
// calcolaSconto('100', 20)  // Argument of type 'string' is not
//                           // assignable to parameter of type 'number'
// calcolaSconto(100)        // Expected 2 arguments, but got 1
// calcolaSconto(100, 20, 5) // Expected 2 arguments, but got 3
```

### Le due cose da capire subito

**1. I tipi spariscono alla compilazione.** TypeScript verifica, poi cancella tutto e produce JavaScript.

```typescript
// Quello che scrivi
interface Utente {
  nome: string
  eta: number
}

function saluta(utente: Utente): string {
  return `Ciao ${utente.nome}`
}
```

```javascript
// Quello che viene eseguito: nessuna traccia dei tipi
function saluta(utente) {
  return `Ciao ${utente.nome}`
}
```

Da qui la conseguenza più importante: **TypeScript non protegge dai dati esterni**. Una risposta di rete, un `JSON.parse`, un valore da `localStorage` possono avere qualunque forma, e il compilatore non lo sa. Il tema è di [B9](#b9-il-confine-con-il-runtime-zod).

**2. Il tipo si deduce quasi sempre.** Annotare tutto è rumore.

```typescript
// ❌ Ridondante: il tipo è ovvio dal valore
const nome: string = 'Anna'
const eta: number = 34
const attivo: boolean = true

// ✅ L'inferenza fa lo stesso lavoro
const nome2 = 'Anna' // string
const eta2 = 34 // number
const attivo2 = true // boolean
```

```
Dove annotare, e dove no:

  ✅ ANNOTA
     · i parametri delle funzioni (l'inferenza non li deduce)
     · le firme pubbliche di un modulo (documentano il contratto
       e impediscono che un refactoring lo cambi in silenzio)
     · le variabili dichiarate vuote:  let esito: Risultato | null = null
     · quando l'inferenza è più larga di quanto vuoi

  ❌ NON ANNOTARE
     · le variabili inizializzate con un valore
     · il tipo di ritorno, quando è ovvio e il corpo è breve
     · i callback passati a metodi già tipizzati
```

---

## A2. Installazione e primo file

```powershell
pnpm add -D typescript
pnpm exec tsc --init
```

```json
// tsconfig.json — la configurazione minima per un progetto nuovo
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],

    "strict": true,
    "noUncheckedIndexedAccess": true,

    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,

    "noEmit": true
  },
  "include": ["src"]
}
```

```
Le righe che contano davvero:

  strict: true            attiva otto controlli in un colpo. Su un
                          progetto nuovo non c'è motivo di ometterlo.

  noUncheckedIndexedAccess  array[i] diventa T | undefined, che è la
                          verità: l'indice potrebbe essere fuori
                          dall'array. Scomodo all'inizio, salva
                          da un'intera classe di errori.

  noEmit: true            con Vite o esbuild, il codice lo produce
                          il bundler. tsc serve solo a verificare,
                          ed è molto più veloce senza emissione.

  moduleResolution: bundler  risolve gli import come fa Vite,
                          senza pretendere l'estensione .js
                          negli import di file .ts.

  verbatimModuleSyntax    obbliga a scrivere 'import type' quando
                          si importa solo un tipo. Rende esplicito
                          cosa sopravvive alla compilazione.
```

```powershell
# Verificare senza produrre file
pnpm exec tsc --noEmit

# In modalità continua, durante lo sviluppo
pnpm exec tsc --noEmit --watch
```

```json
// package.json — lo script che va in CI
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "dev": "vite",
    "build": "tsc --noEmit && vite build"
  }
}
```

Vite **non verifica i tipi**: li rimuove con esbuild, che è veloce proprio perché non controlla nulla. Senza `tsc --noEmit` nella build, un errore di tipo arriva in produzione.

---

## A3. Tipi primitivi e inferenza

```typescript
// I primitivi, con i nomi in minuscolo
const testo: string = 'Anna'
const numero: number = 42
const grande: bigint = 9007199254740993n
const vero: boolean = true
const nulla: null = null
const indefinito: undefined = undefined
const unico: symbol = Symbol('chiave')
```

```typescript
// ❌ SBAGLIATO — String, Number e Boolean con la maiuscola sono
//    i tipi degli OGGETTI wrapper, non dei primitivi
// const sbagliato: String = 'Anna'

// ✅ CORRETTO
const corretto: string = 'Anna'
```

### `let` e `const` inferiscono diversamente

```typescript
// const → tipo LITERAL: il valore non può cambiare, quindi
// il tipo è esattamente quel valore
const stato = 'attivo' // tipo: 'attivo'

// let → tipo ALLARGATO: il valore può cambiare, quindi
// il tipo è l'insieme dei valori possibili
let statoModificabile = 'attivo' // tipo: string
```

Questa differenza è il motivo per cui `const` funziona con le union di literal e `let` no:

```typescript
type Stato = 'bozza' | 'pubblicato' | 'archiviato'

function pubblica(stato: Stato) {
  return stato
}

const daConst = 'bozza'
pubblica(daConst) // ok: il tipo è 'bozza'

let daLet = 'bozza'
// pubblica(daLet)  // ✗ Argument of type 'string' is not assignable
//                  //   to parameter of type 'Stato'

// Le tre soluzioni
let conTipo: Stato = 'bozza'
let conAssertion = 'bozza' as const
pubblica(conTipo)
pubblica(conAssertion)
```

### L'inferenza negli oggetti

```typescript
// Le proprietà di un oggetto sono sempre allargate, anche con const:
// l'oggetto è mutabile, quindi le sue proprietà possono cambiare
const configurazione = {
  ambiente: 'sviluppo', // string, non 'sviluppo'
  porta: 3000, // number
}

configurazione.ambiente = 'produzione' // consentito

// as const congela tutto e mantiene i literal
const configurazioneFissa = {
  ambiente: 'sviluppo',
  porta: 3000,
} as const
// tipo: { readonly ambiente: 'sviluppo'; readonly porta: 3000 }

// configurazioneFissa.ambiente = 'x'  // ✗ Cannot assign to 'ambiente'
//                                     //   because it is a read-only property
```

---

## A4. Array, tuple e oggetti

### Array

```typescript
// Le due sintassi sono equivalenti; la prima è più diffusa
const numeri: number[] = [1, 2, 3]
const testi: Array<string> = ['a', 'b']

// Array di union: ogni elemento può essere dell'uno o dell'altro tipo
const misti: (string | number)[] = ['a', 1]

// Array di oggetti
const utenti: { nome: string; eta: number }[] = [{ nome: 'Anna', eta: 34 }]

// Sola lettura: i metodi che modificano spariscono dal tipo
const costanti: readonly number[] = [1, 2, 3]
// costanti.push(4)  // ✗ Property 'push' does not exist on type
//                   //   'readonly number[]'
```

### `noUncheckedIndexedAccess`, e perché conta

```typescript
const elenco = ['a', 'b', 'c']

// SENZA il flag: TypeScript dice string, e mente
// const primo = elenco[10]   // tipo string, valore undefined

// CON noUncheckedIndexedAccess: string | undefined, che è la verità
const primo = elenco[10]
// console.log(primo.toUpperCase())  // ✗ 'primo' is possibly 'undefined'

// Le tre risposte corrette
if (primo !== undefined) {
  console.log(primo.toUpperCase())
}

console.log(primo?.toUpperCase())

const sicuro = elenco.at(0) ?? 'predefinito'
```

Il flag rende scomodo l'accesso per indice, ed è il punto: l'accesso per indice **è** rischioso, e la scomodità spinge verso `for...of`, `.at()` e i metodi funzionali, che non hanno il problema.

### Tuple

```typescript
// Lunghezza e tipo per posizione fissati
type Coordinate = [number, number]
const milano: Coordinate = [45.4642, 9.19]

// Con etichette: compaiono nei suggerimenti dell'editor
type Intervallo = [inizio: number, fine: number]

// Elementi opzionali e rest
type Configurazione = [nome: string, porta?: number, ...opzioni: string[]]

// Il caso d'uso più frequente: il ritorno di useState in React
function useStato<T>(iniziale: T): [T, (nuovo: T) => void] {
  let valore = iniziale
  return [valore, (nuovo) => (valore = nuovo)]
}

const [conteggio, impostaConteggio] = useStato(0)
```

```typescript
// as const trasforma un array in una tupla di literal
const punto = [1, 2] // number[]
const puntoTupla = [1, 2] as const // readonly [1, 2]
```

### Oggetti

```typescript
// Tipo anonimo, per un uso singolo
function stampa(utente: { nome: string; eta: number }): void {
  console.log(utente.nome, utente.eta)
}

// Proprietà opzionali
type Contatto = {
  nome: string
  email: string
  telefono?: string // string | undefined
}

// Proprietà di sola lettura
type Punto = {
  readonly x: number
  readonly y: number
}

// Index signature: chiavi non note in anticipo
type Dizionario = {
  [chiave: string]: number
}

const conteggi: Dizionario = { rossi: 3, bianchi: 1 }
conteggi.verdi = 2 // qualunque chiave string è ammessa

// Con noUncheckedIndexedAccess, la lettura restituisce number | undefined
const forse = conteggi.inesistente // number | undefined
```

```typescript
// Record è la forma leggibile della index signature
type ConteggiPerCliente = Record<string, number>

// E permette di limitare le chiavi
type Traduzioni = Record<'it' | 'en' | 'de', string>

const etichette: Traduzioni = {
  it: 'Salva',
  en: 'Save',
  de: 'Speichern',
  // manca una chiave → errore; una chiave in più → errore
}
```

### Il controllo delle proprietà in eccesso

```typescript
type Utente = { nome: string; eta: number }

// ❌ L'oggetto LETTERALE assegnato direttamente viene controllato
//    anche per le proprietà in eccesso
// const a: Utente = { nome: 'Anna', eta: 34, ruolo: 'admin' }
//   ✗ Object literal may only specify known properties

// ✅ Passando da una variabile, il controllo non scatta:
//    conta solo che la forma sia compatibile
const grezzo = { nome: 'Anna', eta: 34, ruolo: 'admin' }
const b: Utente = grezzo // ok
```

Non è un'incoerenza: il controllo sui letterali intercetta i refusi (`nmoe` invece di `nome`), che sono l'errore che vale la pena catturare. Su una variabile già costruita, la compatibilità strutturale basta.

---

## A5. Union, literal type e narrowing di base

```typescript
// Union: uno dei tipi elencati
type Identificativo = string | number

function stampaId(id: Identificativo) {
  // Qui id è string | number: si possono usare solo i membri COMUNI
  console.log(id.toString()) // ok: entrambi ce l'hanno
  // console.log(id.toUpperCase())  // ✗ non esiste su number
}
```

### Restringere per poter usare

```typescript
function formattaId(id: string | number): string {
  if (typeof id === 'string') {
    // Qui TypeScript SA che id è string
    return id.toUpperCase()
  }
  // E qui sa che è number, per esclusione
  return id.toFixed(0)
}
```

### Literal type

```typescript
// Un tipo che ammette esattamente un valore
type Sì = 'sì'

// Utile in union: è l'enum di TypeScript, senza enum
type Metodo = 'GET' | 'POST' | 'PUT' | 'DELETE'
type Stato = 'bozza' | 'in-revisione' | 'pubblicato'
type Dimensione = 'piccolo' | 'medio' | 'grande'
type CodiceRisposta = 200 | 201 | 400 | 404 | 500

function richiedi(url: string, metodo: Metodo = 'GET') {
  // ...
}

richiedi('/api', 'POST') // ok
// richiedi('/api', 'PATCH')   // ✗ non è nell'union
```

Le union di literal sono da preferire agli `enum` di TypeScript: producono zero codice a runtime, funzionano con i dati che arrivano da JSON, e l'editor suggerisce comunque i valori.

```typescript
// L'enum genera un oggetto a runtime e non è cancellabile
enum StatoEnum {
  Bozza = 'bozza',
  Pubblicato = 'pubblicato',
}

// La union no: sparisce completamente
type StatoUnion = 'bozza' | 'pubblicato'

// Se serve anche l'oggetto dei valori, si costruisce con as const
const STATI = ['bozza', 'in-revisione', 'pubblicato'] as const
type StatoDaArray = (typeof STATI)[number] // 'bozza' | 'in-revisione' | 'pubblicato'

// E si può iterare, cosa che con il solo tipo non si può fare
for (const stato of STATI) {
  console.log(stato)
}
```

### Intersection

```typescript
// & combina: il risultato ha TUTTE le proprietà
type ConIdentificativo = { id: string }
type ConDate = { creatoIl: Date; modificatoIl: Date }

type Entita = ConIdentificativo & ConDate

const fattura: Entita = {
  id: 'f-1',
  creatoIl: new Date(),
  modificatoIl: new Date(),
}
```

```typescript
// ⚠ L'intersezione di primitivi incompatibili produce never
type Impossibile = string & number // never
```

---

## A6. Funzioni

```typescript
// Dichiarazione
function somma(a: number, b: number): number {
  return a + b
}

// Espressione, con il tipo della funzione
const sottrai: (a: number, b: number) => number = (a, b) => a - b

// Arrow, con i tipi sui parametri: il ritorno è dedotto
const moltiplica = (a: number, b: number) => a * b // number

// Parametri opzionali: DEVONO stare in fondo
function saluta(nome: string, titolo?: string): string {
  return titolo ? `${titolo} ${nome}` : nome
}

// Con un valore predefinito, il parametro è implicitamente opzionale
function connetti(host: string, porta: number = 5432): string {
  return `${host}:${porta}`
}

// Rest
function sommaTutti(primo: number, ...altri: number[]): number {
  return altri.reduce((s, n) => s + n, primo)
}
```

### Il tipo di ritorno: annotarlo o no

```typescript
// Non annotato: dedotto, e cambia se cambi il corpo
function calcola(a: number, b: number) {
  return a + b // dedotto number
}

// Annotato: il compilatore verifica che il corpo lo rispetti.
// Su una funzione esportata è un contratto: se il corpo cambia
// in modo incompatibile, l'errore è QUI e non nei venti punti
// che la usano.
export function calcolaTotale(righe: Riga[]): number {
  return righe.reduce((s, r) => s + r.importo, 0)
}
```

### Oggetto di opzioni

```typescript
// Il pattern per le funzioni con molti parametri
type OpzioniRichiesta = {
  metodo?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  intestazioni?: Record<string, string>
  timeout?: number
  segnale?: AbortSignal
}

async function recupera(url: string, opzioni: OpzioniRichiesta = {}): Promise<Response> {
  const { metodo = 'GET', intestazioni = {}, timeout = 5000, segnale } = opzioni

  return fetch(url, {
    method: metodo,
    headers: intestazioni,
    signal: segnale ?? AbortSignal.timeout(timeout),
  })
}
```

### Overload

```typescript
// Le firme visibili a chi chiama
function converti(valore: string): number
function converti(valore: number): string
// L'implementazione: non è visibile, e deve coprire tutte le firme
function converti(valore: string | number): string | number {
  return typeof valore === 'string' ? Number(valore) : String(valore)
}

const a = converti('42') // number
const b = converti(42) // string
```

```typescript
// Nella maggior parte dei casi i generici sono più semplici degli overload
function primo<T>(elenco: readonly T[]): T | undefined {
  return elenco[0]
}

const n = primo([1, 2, 3]) // number | undefined
const s = primo(['a', 'b']) // string | undefined
```

### `this` nelle funzioni

```typescript
// Il parametro this è fittizio: non esiste a runtime,
// serve solo a tipizzare il contesto
function gestisciClic(this: HTMLButtonElement, evento: MouseEvent): void {
  console.log(this.textContent)
}

const comando = document.querySelector('button')
comando?.addEventListener('click', gestisciClic)
```

---

## A7. `interface` e `type`

Fanno quasi la stessa cosa. Le differenze sono poche e precise.

```typescript
// interface
interface Utente {
  nome: string
  eta: number
}

// type alias
type UtenteAlias = {
  nome: string
  eta: number
}
```

### Cosa può solo `type`

```typescript
// Union
type Risultato = { ok: true; valore: string } | { ok: false; errore: Error }

// Primitivi e literal
type Identificativo = string
type Stato = 'attivo' | 'sospeso'

// Tuple
type Coordinate = [number, number]

// Mapped e conditional type
type Opzionale<T> = { [K in keyof T]?: T[K] }
type SoloArray<T> = T extends unknown[] ? T : never
```

### Cosa può solo `interface`

```typescript
// Il merging delle dichiarazioni: due interface con lo stesso nome
// si fondono. È il meccanismo che permette la module augmentation.
interface Finestra {
  titolo: string
}

interface Finestra {
  larghezza: number
}

// Finestra ha ora entrambe le proprietà
const f: Finestra = { titolo: 'x', larghezza: 100 }
```

```typescript
// Il caso d'uso reale: estendere tipi di libreria
declare global {
  interface Window {
    analitica?: {
      traccia(evento: string, dati?: Record<string, unknown>): void
    }
  }
}

window.analitica?.traccia('pagina-vista')
```

### Estendere

```typescript
// interface estende con extends
interface Persona {
  nome: string
}

interface Dipendente extends Persona {
  ruolo: string
}

// type estende con l'intersezione
type PersonaType = { nome: string }
type DipendenteType = PersonaType & { ruolo: string }

// E si possono mescolare
interface DaType extends PersonaType {
  reparto: string
}
```

```
La regola operativa che evita di doverci pensare:

  interface   per la forma degli OGGETTI, e per tutto ciò
              che potrebbe dover essere esteso da fuori
              (API pubbliche, tipi di libreria)

  type        per tutto il resto: union, tuple, primitivi,
              funzioni, tipi calcolati

  In un progetto applicativo, usare 'type' ovunque è una scelta
  difendibile: il merging serve raramente, e una convenzione sola
  è più semplice da seguire. La cosa che conta è la coerenza.
```

Un dettaglio non ovvio: nei messaggi d'errore, `interface` viene mostrata con il suo nome, mentre un `type` complesso viene spesso espanso per intero. Su tipi grandi, `interface` produce errori più leggibili.

---

## A8. `any`, `unknown`, `never`, `void`

### `any` — la valvola di sfogo che spegne tutto

```typescript
let qualunque: any = 42
qualunque = 'testo'
qualunque.metodoInesistente() // nessun errore
qualunque.a.b.c.d // nessun errore

// E si propaga: il valore restituito è any
const risultato = qualunque.qualcosa // any
```

`any` non è "un tipo qualsiasi": è **la disattivazione del controllo** per quel valore e per tutto ciò che ne deriva. Un `any` in un punto centrale svuota di significato i tipi di mezzo progetto.

```typescript
// ❌ any su un dato esterno: il tipo mente per tutto il flusso
async function recuperaSbagliato(url: string): Promise<any> {
  const risposta = await fetch(url)
  return risposta.json()
}

// ✅ unknown obbliga a verificare prima di usare
async function recupera(url: string): Promise<unknown> {
  const risposta = await fetch(url)
  return risposta.json()
}
```

### `unknown` — "non lo so, e devi verificarlo"

```typescript
let sconosciuto: unknown = recuperaDaChissaDove()

// Nessuna operazione è permessa prima del narrowing
// sconosciuto.toUpperCase()   // ✗ 'sconosciuto' is of type 'unknown'
// const n: number = sconosciuto  // ✗ non assegnabile

// Dopo il narrowing, tutto funziona
if (typeof sconosciuto === 'string') {
  console.log(sconosciuto.toUpperCase()) // ok
}
```

```typescript
// Il posto in cui unknown è obbligatorio: catch
try {
  operazioneRischiosa()
} catch (errore) {
  // errore è unknown (con useUnknownInCatchVariables, incluso in strict)
  // console.log(errore.message)  // ✗

  if (errore instanceof Error) {
    console.log(errore.message)
  } else {
    console.log('errore non standard:', String(errore))
  }
}
```

```typescript
/** La funzione che serve in ogni progetto, perché si può lanciare qualunque cosa. */
function normalizzaErrore(errore: unknown): Error {
  if (errore instanceof Error) return errore

  if (typeof errore === 'string') return new Error(errore)

  if (
    typeof errore === 'object' &&
    errore !== null &&
    'message' in errore &&
    typeof errore.message === 'string'
  ) {
    return new Error(errore.message)
  }

  return new Error(`Errore non riconosciuto: ${JSON.stringify(errore)}`)
}
```

### `never` — il tipo che non ha valori

```typescript
// Il ritorno di una funzione che non ritorna mai
function solleva(messaggio: string): never {
  throw new Error(messaggio)
}

function cicloInfinito(): never {
  while (true) {
    // ...
  }
}

// Il risultato di un'intersezione impossibile
type Vuoto = string & number // never

// Il tipo di un array vuoto senza contesto
const vuoto = [] // never[] con strictNullChecks
```

Il suo uso più prezioso: **verificare l'esaustività**.

```typescript
type Forma =
  | { tipo: 'cerchio'; raggio: number }
  | { tipo: 'quadrato'; lato: number }
  | { tipo: 'rettangolo'; base: number; altezza: number }

function area(forma: Forma): number {
  switch (forma.tipo) {
    case 'cerchio':
      return Math.PI * forma.raggio ** 2
    case 'quadrato':
      return forma.lato ** 2
    case 'rettangolo':
      return forma.base * forma.altezza
    default: {
      // Se tutti i casi sono coperti, qui forma è never.
      // Aggiungendo un tipo di forma senza gestirlo,
      // QUESTA riga diventa un errore di compilazione.
      const esaustivo: never = forma
      throw new Error(`Forma non gestita: ${JSON.stringify(esaustivo)}`)
    }
  }
}
```

Questo pattern è il motivo principale per cui vale la pena usare le discriminated union: aggiungere una variante fa emergere **tutti** i punti che vanno aggiornati, invece di produrre un `undefined` a runtime sei mesi dopo.

### `void` — nessun valore utile

```typescript
// Il ritorno di una funzione che non restituisce nulla
function registra(messaggio: string): void {
  console.log(messaggio)
}

// void come tipo di ritorno atteso ACCETTA qualunque ritorno:
// è voluto, e serve per i callback
const numeri = [1, 2, 3]
const risultati: number[] = []

// forEach si aspetta (v: number) => void, ma push restituisce number
numeri.forEach((n) => risultati.push(n)) // ok
```

```
Il riassunto:

  any      spegne il controllo. Usalo solo per zittire
           temporaneamente un errore, con un commento che dice perché.

  unknown  "verifica prima di usare". È il tipo giusto per
           tutto ciò che arriva da fuori: rete, JSON, catch,
           postMessage, localStorage.

  never    "non può accadere". Per l'esaustività e per le
           funzioni che sollevano sempre.

  void     "il ritorno non serve". Diverso da undefined:
           void accetta qualunque valore restituito.
```

---

# Parte B — Comprensione Profonda

---

## B1. Il sistema di tipi è strutturale

TypeScript confronta i tipi per **forma**, non per nome. Due tipi con gli stessi membri sono intercambiabili, anche se dichiarati separatamente e senza alcuna relazione.

```typescript
interface Punto2D {
  x: number
  y: number
}

interface Coordinate {
  x: number
  y: number
}

const p: Punto2D = { x: 1, y: 2 }
const c: Coordinate = p // ok: stessa forma, nessuna relazione dichiarata
```

```typescript
// Vale anche per le classi: nessun 'implements' necessario
class Cane {
  nome = 'Fido'
  verso() {
    return 'bau'
  }
}

interface Animale {
  nome: string
  verso(): string
}

const a: Animale = new Cane() // ok
```

Il vantaggio è la flessibilità: non serve dichiarare in anticipo tutte le relazioni. Il costo è che due concetti diversi con la stessa forma si confondono.

```typescript
// ❌ Il problema: idUtente e idFattura sono entrambi string.
//    Scambiarli è un errore che il compilatore non vede.
function eliminaFattura(idFattura: string) {
  // ...
}

const idUtente = 'u-42'
eliminaFattura(idUtente) // compila, ed è sbagliato
```

### Branded type: rendere nominale ciò che serve

```typescript
// Si aggiunge una proprietà fantasma che esiste solo nei tipi
declare const marchio: unique symbol

type Marchiato<T, M extends string> = T & { readonly [marchio]: M }

type IdUtente = Marchiato<string, 'IdUtente'>
type IdFattura = Marchiato<string, 'IdFattura'>

// I costruttori sono l'unico modo di produrre un valore marchiato:
// concentrano la validazione in un punto solo
function idUtente(grezzo: string): IdUtente {
  if (!/^u-\d+$/.test(grezzo)) {
    throw new Error(`Identificativo utente non valido: ${grezzo}`)
  }
  return grezzo as IdUtente
}

function idFattura(grezzo: string): IdFattura {
  if (!/^f-\d+$/.test(grezzo)) {
    throw new Error(`Identificativo fattura non valido: ${grezzo}`)
  }
  return grezzo as IdFattura
}

function elimina(id: IdFattura): void {
  // ...
}

const u = idUtente('u-42')
const f = idFattura('f-7')

elimina(f) // ok
// elimina(u)         // ✗ IdUtente non è assegnabile a IdFattura
// elimina('f-7')     // ✗ nemmeno una stringa qualunque
```

A runtime `IdUtente` è una stringa normale: il marchio esiste solo per il compilatore, e il codice prodotto è identico.

```typescript
// Lo stesso pattern per le unità di misura
type Euro = Marchiato<number, 'Euro'>
type Centesimi = Marchiato<number, 'Centesimi'>

function inCentesimi(euro: Euro): Centesimi {
  return Math.round(euro * 100) as Centesimi
}

function addebita(importo: Centesimi): void {
  // ...
}

const prezzo = 19.99 as Euro
addebita(inCentesimi(prezzo)) // ok
// addebita(prezzo)             // ✗ Euro non è Centesimi
```

### La varianza dei parametri di funzione

```typescript
type Gestore = (evento: { tipo: string }) => void

// ✅ Un gestore che accetta MENO (un supertipo) va bene:
//    riceverà comunque qualcosa che sa gestire
const generico: Gestore = (evento: object) => {}

// ❌ Un gestore che pretende DI PIÙ non va bene:
//    potrebbe ricevere un evento senza 'dettaglio'
// const specifico: Gestore = (evento: { tipo: string; dettaglio: number }) => {}
//   ✗ con strictFunctionTypes
```

```typescript
// ⚠ L'eccezione: i METODI sono controllati in modo bivariante,
//    per compatibilità storica con gli array. Le proprietà
//    di tipo funzione no.
interface ConMetodo {
  gestisci(evento: { tipo: string }): void // bivariante: più permissivo
}

interface ConProprieta {
  gestisci: (evento: { tipo: string }) => void // controvariante: più rigoroso
}
```

Scrivere i callback come **proprietà** invece che come metodi attiva il controllo più rigoroso. È una differenza che quasi nessuno conosce e che di tanto in tanto spiega un errore sfuggito.

---

## B2. Type narrowing in profondità

Il narrowing è ciò che rende usabili le union. TypeScript segue il flusso del controllo e restringe il tipo a ogni verifica.

```typescript
// typeof — per i primitivi
function elabora(valore: string | number | boolean) {
  if (typeof valore === 'string') return valore.toUpperCase()
  if (typeof valore === 'number') return valore.toFixed(2)
  return valore ? 'vero' : 'falso'
}

// instanceof — per le classi
function descrivi(valore: Date | RegExp | Error) {
  if (valore instanceof Date) return valore.toISOString()
  if (valore instanceof RegExp) return valore.source
  return valore.message
}

// in — per la presenza di una proprietà
type Cane = { abbaia(): void }
type Gatto = { miagola(): void }

function verso(animale: Cane | Gatto) {
  if ('abbaia' in animale) {
    animale.abbaia()
  } else {
    animale.miagola()
  }
}

// Verifica di verità: elimina null, undefined, '', 0, NaN, false
function lunghezza(testo: string | null | undefined): number {
  if (!testo) return 0
  return testo.length // string
}

// Uguaglianza
function confronta(a: string | number, b: string | boolean) {
  if (a === b) {
    // Entrambi devono essere string: è l'unico tipo in comune
    console.log(a.toUpperCase(), b.toUpperCase())
  }
}
```

### Discriminated union: il pattern centrale

```typescript
// Ogni variante ha una proprietà con un literal type diverso:
// è il "discriminante", e TypeScript lo usa per restringere.
type StatoRichiesta =
  | { stato: 'inattiva' }
  | { stato: 'caricamento'; iniziataIl: number }
  | { stato: 'riuscita'; dati: string[]; durata: number }
  | { stato: 'fallita'; errore: Error; tentativi: number }

function descriviStato(richiesta: StatoRichiesta): string {
  switch (richiesta.stato) {
    case 'inattiva':
      return 'In attesa'

    case 'caricamento':
      // Solo qui esiste iniziataIl
      return `In corso da ${Date.now() - richiesta.iniziataIl} ms`

    case 'riuscita':
      return `${richiesta.dati.length} elementi in ${richiesta.durata} ms`

    case 'fallita':
      return `Fallita dopo ${richiesta.tentativi} tentativi: ${richiesta.errore.message}`

    default: {
      const esaustivo: never = richiesta
      throw new Error(`Stato non gestito: ${JSON.stringify(esaustivo)}`)
    }
  }
}
```

```typescript
// ❌ L'alternativa senza discriminante: tutto opzionale,
//    e ogni accesso richiede un controllo che il compilatore
//    non può verificare
type StatoSbagliato = {
  caricamento?: boolean
  dati?: string[]
  errore?: Error
}

// Sono possibili stati insensati:
const impossibile: StatoSbagliato = { caricamento: true, errore: new Error('x') }
```

La discriminated union rende **impossibili da rappresentare** gli stati che non devono esistere. È il beneficio principale, più della comodità del narrowing.

### Type predicate: insegnare a TypeScript

```typescript
// Una funzione che restituisce boolean non restringe nulla.
// 'valore is Tipo' come tipo di ritorno lo trasforma in un narrowing.
function eStringa(valore: unknown): valore is string {
  return typeof valore === 'string'
}

function eArrayDiStringhe(valore: unknown): valore is string[] {
  return Array.isArray(valore) && valore.every((v) => typeof v === 'string')
}

const sconosciuto: unknown = ['a', 'b']

if (eArrayDiStringhe(sconosciuto)) {
  console.log(sconosciuto.map((s) => s.toUpperCase())) // string[]
}
```

```typescript
// Il caso d'uso che serve di continuo: filtrare i null da un array
const forse: (string | null)[] = ['a', null, 'b', null]

// ❌ filter non restringe: il tipo resta (string | null)[]
const ancoraNullabili = forse.filter((v) => v !== null)

// ✅ Con un type predicate, il tipo diventa string[]
function nonNullo<T>(valore: T | null | undefined): valore is T {
  return valore !== null && valore !== undefined
}

const soloStringhe = forse.filter(nonNullo) // string[]
```

Da TypeScript 5.5 l'inferenza dei type predicate è automatica in molti casi: `forse.filter((v) => v !== null)` viene dedotto correttamente. Scrivere il predicato esplicito resta utile per la logica non banale e per le versioni precedenti.

```typescript
// ⚠ Un type predicate è una PROMESSA: il compilatore si fida.
//    Se mente, il narrowing è sbagliato e l'errore emerge a runtime.
function eNumeroBugiardo(valore: unknown): valore is number {
  return true // mente
}

const testo: unknown = 'non un numero'
if (eNumeroBugiardo(testo)) {
  // testo.toFixed(2)   // compila, e a runtime solleva TypeError
}
```

### Assertion function

```typescript
// 'asserts valore is T': se non solleva, da lì in poi il tipo è ristretto
function assicuraStringa(valore: unknown, nome: string): asserts valore is string {
  if (typeof valore !== 'string') {
    throw new TypeError(`${nome} deve essere una stringa, ricevuto ${typeof valore}`)
  }
}

function elaboraInput(grezzo: unknown) {
  assicuraStringa(grezzo, 'input')
  // Da qui grezzo è string, senza bisogno di un if
  return grezzo.trim().toLowerCase()
}
```

```typescript
// ⚠ Una assertion function richiede un'annotazione esplicita
//    sulla variabile che la contiene: l'inferenza non basta.
// ❌ const assicura = (v: unknown): asserts v is string => { ... }
//    Assertions require every name in the call target to be declared
//    with an explicit type annotation.

// ✅
const assicura: (v: unknown) => asserts v is string = (v) => {
  if (typeof v !== 'string') throw new TypeError('non è una stringa')
}
```

### Dove il narrowing si perde

```typescript
type Contenitore = { valore: string | null }

function usaSbagliato(c: Contenitore) {
  if (c.valore !== null) {
    // Una chiamata di funzione può aver modificato c.valore:
    // TypeScript è conservativo e in alcuni casi perde il narrowing
    effettoCollaterale()
    // console.log(c.valore.toUpperCase())  // può risultare possibly null
  }
}

// ✅ Estrarre in una costante locale: il narrowing non si perde più
function usaCorretto(c: Contenitore) {
  const valore = c.valore
  if (valore !== null) {
    effettoCollaterale()
    console.log(valore.toUpperCase()) // sicuro
  }
}
```

```typescript
// Il narrowing si perde anche nelle closure che catturano un let
function conClosure(valore: string | null) {
  if (valore !== null) {
    // Dentro il callback il narrowing non vale: valore potrebbe
    // essere cambiato fra la verifica e l'esecuzione
    setTimeout(() => {
      // console.log(valore.toUpperCase())  // possibly null
    }, 100)
  }
}

// ✅ Con const, il valore non può cambiare e il narrowing regge
function conConst(valoreIniziale: string | null) {
  const valore = valoreIniziale
  if (valore !== null) {
    setTimeout(() => console.log(valore.toUpperCase()), 100) // ok
  }
}
```

---

## B3. Generics

Un generico è un **parametro di tipo**: permette a una funzione o a un tipo di lavorare con tipi diversi conservando la relazione fra ingresso e uscita.

```typescript
// ❌ Senza generici: any perde l'informazione
function primoQualunque(elenco: any[]): any {
  return elenco[0]
}
const x = primoQualunque([1, 2, 3]) // any: il tipo è perso

// ✅ Con un generico: il legame è conservato
function primo<T>(elenco: readonly T[]): T | undefined {
  return elenco[0]
}
const y = primo([1, 2, 3]) // number | undefined
const z = primo(['a', 'b']) // string | undefined
```

### Vincoli

```typescript
// extends limita ciò che T può essere, e sblocca le proprietà
function lunghezza<T extends { length: number }>(valore: T): number {
  return valore.length
}

lunghezza('testo') // 5
lunghezza([1, 2, 3]) // 3
// lunghezza(42)      // ✗ number non ha length
```

```typescript
// keyof: le chiavi di un tipo, come union di literal
type Utente = { nome: string; eta: number; attivo: boolean }
type ChiaviUtente = keyof Utente // 'nome' | 'eta' | 'attivo'

// Il generico che accede a una proprietà conservando il tipo
function leggi<T, K extends keyof T>(oggetto: T, chiave: K): T[K] {
  return oggetto[chiave]
}

const utente: Utente = { nome: 'Anna', eta: 34, attivo: true }

const nome = leggi(utente, 'nome') // string
const eta = leggi(utente, 'eta') // number
// leggi(utente, 'inesistente')     // ✗ non è una chiave di Utente
```

```typescript
// Il pattern completo: scrivere una proprietà con il tipo corretto
function scrivi<T, K extends keyof T>(oggetto: T, chiave: K, valore: T[K]): T {
  return { ...oggetto, [chiave]: valore }
}

scrivi(utente, 'eta', 35) // ok
// scrivi(utente, 'eta', 'trentacinque')  // ✗ string non è number
```

### Valori predefiniti e più parametri

```typescript
type Risposta<T = unknown> = {
  dati: T
  stato: number
}

const generica: Risposta = { dati: 'qualunque', stato: 200 }
const tipizzata: Risposta<Utente[]> = { dati: [utente], stato: 200 }

// Più parametri, con vincoli fra loro
function raggruppa<T, K extends string | number>(
  elementi: readonly T[],
  chiaveDi: (elemento: T) => K,
): Map<K, T[]> {
  const gruppi = new Map<K, T[]>()

  for (const elemento of elementi) {
    const chiave = chiaveDi(elemento)
    const esistente = gruppi.get(chiave)
    if (esistente) {
      esistente.push(elemento)
    } else {
      gruppi.set(chiave, [elemento])
    }
  }

  return gruppi
}

const fatture = [
  { cliente: 'Rossi', importo: 1200 },
  { cliente: 'Bianchi', importo: 340 },
  { cliente: 'Rossi', importo: 890 },
]

const perCliente = raggruppa(fatture, (f) => f.cliente) // Map<string, {...}[]>
```

### Classi e interfacce generiche

```typescript
class Cache<C, V> {
  #voci = new Map<C, { valore: V; scadenza: number }>()

  constructor(private durata: number = 60_000) {}

  imposta(chiave: C, valore: V): void {
    this.#voci.set(chiave, { valore, scadenza: Date.now() + this.durata })
  }

  leggi(chiave: C): V | undefined {
    const voce = this.#voci.get(chiave)
    if (!voce) return undefined

    if (Date.now() > voce.scadenza) {
      this.#voci.delete(chiave)
      return undefined
    }

    return voce.valore
  }

  get dimensione(): number {
    return this.#voci.size
  }
}

const cacheUtenti = new Cache<string, Utente>(30_000)
cacheUtenti.imposta('u-1', utente)
const forse = cacheUtenti.leggi('u-1') // Utente | undefined
```

```typescript
// Un repository generico: la firma è la stessa per ogni entità
interface Repository<T, Id = string> {
  trova(id: Id): Promise<T | null>
  elenca(filtri?: Partial<T>): Promise<T[]>
  salva(entita: Omit<T, 'id'> & { id?: Id }): Promise<T>
  elimina(id: Id): Promise<void>
}
```

### `NoInfer`

```typescript
// ❌ Il problema: TypeScript deduce T da ENTRAMBI i parametri,
//    e allarga il tipo per farli combaciare
function conPredefinitoSbagliato<T>(valori: T[], predefinito: T): T {
  return valori[0] ?? predefinito
}

const esito = conPredefinitoSbagliato(['a', 'b'], 'z')
// T diventa string, e 'q' sarebbe accettato anche se non è nell'elenco

// ✅ NoInfer (TypeScript 5.4) esclude un parametro dall'inferenza
function conPredefinito<T extends string>(valori: T[], predefinito: NoInfer<T>): T {
  return valori[0] ?? predefinito
}

const colori = ['rosso', 'verde'] as const
conPredefinito([...colori], 'rosso') // ok
// conPredefinito([...colori], 'blu')  // ✗ 'blu' non è fra i valori
```

---

## B4. Utility type, e come sono costruiti

TypeScript ne fornisce una ventina. Conoscere come sono fatti conta più che memorizzarli: sono tutti mapped o conditional type che potresti scrivere tu.

```typescript
interface Fattura {
  id: string
  numero: string
  cliente: string
  importo: number
  pagata: boolean
  note?: string
}
```

### Quelli che trasformano le proprietà

```typescript
// Partial: tutte opzionali. Per gli aggiornamenti parziali.
type FatturaParziale = Partial<Fattura>
// { id?: string; numero?: string; ... }

// Required: tutte obbligatorie. Rimuove anche il ? da 'note'.
type FatturaCompleta = Required<Fattura>

// Readonly: tutte in sola lettura.
type FatturaImmutabile = Readonly<Fattura>

// La loro implementazione, che puoi scrivere in una riga:
type MioPartial<T> = { [K in keyof T]?: T[K] }
type MioRequired<T> = { [K in keyof T]-?: T[K] } // -? rimuove l'opzionalità
type MioReadonly<T> = { readonly [K in keyof T]: T[K] }
type MioMutabile<T> = { -readonly [K in keyof T]: T[K] } // -readonly la rimuove
```

### Quelli che selezionano

```typescript
// Pick: tiene solo le chiavi elencate
type RiepilogoFattura = Pick<Fattura, 'id' | 'numero' | 'importo'>

// Omit: toglie le chiavi elencate
type NuovaFattura = Omit<Fattura, 'id'>

// Record: costruisce un oggetto da chiavi e valore
type ConteggiPerStato = Record<'bozza' | 'emessa' | 'pagata', number>

// Le implementazioni
type MioPick<T, K extends keyof T> = { [P in K]: T[P] }
type MioOmit<T, K extends keyof never> = MioPick<T, Exclude<keyof T, K>>
type MioRecord<K extends keyof never, V> = { [P in K]: V }
```

```typescript
// ⚠ Omit NON verifica che le chiavi esistano: un refuso passa in silenzio
type ConRefuso = Omit<Fattura, 'importoo'> // nessun errore, non toglie nulla

// La variante severa, che vale la pena avere in ogni progetto
type OmitSicuro<T, K extends keyof T> = Omit<T, K>

// type ConRefusoSicuro = OmitSicuro<Fattura, 'importoo'>  // ✗ errore
```

### Quelli che operano sulle union

```typescript
type Stato = 'bozza' | 'emessa' | 'pagata' | 'annullata'

// Exclude: toglie dalla union
type StatoAttivo = Exclude<Stato, 'annullata'> // 'bozza' | 'emessa' | 'pagata'

// Extract: tiene solo ciò che corrisponde
type StatoFinale = Extract<Stato, 'pagata' | 'annullata'> // 'pagata' | 'annullata'

// NonNullable: toglie null e undefined
type Certo = NonNullable<string | null | undefined> // string

// Le implementazioni: conditional type DISTRIBUTIVI
type MioExclude<T, U> = T extends U ? never : T
type MioExtract<T, U> = T extends U ? T : never
type MioNonNullable<T> = T & {}
```

```
La distributività è la chiave: quando il tipo a sinistra di
'extends' è un parametro generico nudo e riceve una union,
il conditional type si applica a OGNI membro separatamente.

  MioExclude<'a' | 'b' | 'c', 'b'>
  → ('a' extends 'b' ? never : 'a')
  | ('b' extends 'b' ? never : 'b')
  | ('c' extends 'b' ? never : 'c')
  → 'a' | never | 'c'
  → 'a' | 'c'        (never sparisce dalle union)

Per DISATTIVARE la distributività si avvolgono i due lati
in una tupla:
  type NonDistributivo<T> = [T] extends [U] ? A : B
```

### Quelli che operano sulle funzioni

```typescript
function creaFattura(cliente: string, importo: number): Fattura {
  return { id: '', numero: '', cliente, importo, pagata: false }
}

type Parametri = Parameters<typeof creaFattura> // [cliente: string, importo: number]
type Ritorno = ReturnType<typeof creaFattura> // Fattura

async function recupera(): Promise<Fattura[]> {
  return []
}

type Atteso = Awaited<ReturnType<typeof recupera>> // Fattura[]

// Le implementazioni usano infer, che vediamo in B5
type MioReturnType<T> = T extends (...argomenti: never[]) => infer R ? R : never
type MioParameters<T> = T extends (...argomenti: infer P) => unknown ? P : never
```

### Quelli sulle stringhe

```typescript
type Metodo = 'get' | 'post'

type MetodoMaiuscolo = Uppercase<Metodo> // 'GET' | 'POST'
type MetodoCapitalizzato = Capitalize<Metodo> // 'Get' | 'Post'
type MetodoMinuscolo = Lowercase<'GET'> // 'get'
type Decapitalizzato = Uncapitalize<'Get'> // 'get'
```

---

## B5. Mapped type, conditional type e `infer`

### Mapped type

```typescript
// La forma base: itera sulle chiavi e trasforma
type Nullabile<T> = { [K in keyof T]: T[K] | null }

type FatturaNullabile = Nullabile<Fattura>
// { id: string | null; numero: string | null; ... }
```

```typescript
// Rinominare le chiavi con 'as'
type ConPrefisso<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K]
}

type FatturaConPrefisso = ConPrefisso<Pick<Fattura, 'numero' | 'importo'>, 'fattura'>
// { fatturaNumero: string; fatturaImporto: number }
```

```typescript
// Il pattern che genera getter e setter da un tipo
type ConAccessori<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
} & {
  [K in keyof T as `set${Capitalize<string & K>}`]: (valore: T[K]) => void
}

type AccessoriFattura = ConAccessori<Pick<Fattura, 'importo' | 'pagata'>>
// {
//   getImporto: () => number
//   getPagata: () => boolean
//   setImporto: (valore: number) => void
//   setPagata: (valore: boolean) => void
// }
```

```typescript
// Filtrare le chiavi: 'never' come nuova chiave la elimina
type SoloDiTipo<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K]
}

type SoloStringhe = SoloDiTipo<Fattura, string> // { id: string; numero: string; cliente: string }
type SoloNumeri = SoloDiTipo<Fattura, number> // { importo: number }
```

### Conditional type e `infer`

```typescript
// La forma: T extends U ? A : B
type SeArray<T> = T extends unknown[] ? 'array' : 'non array'

type A = SeArray<string[]> // 'array'
type B = SeArray<string> // 'non array'
```

```typescript
// infer dichiara una variabile di tipo dentro la condizione
type ElementoDi<T> = T extends readonly (infer E)[] ? E : never

type C = ElementoDi<string[]> // string
type D = ElementoDi<readonly number[]> // number
type E = ElementoDi<string> // never
```

```typescript
// infer in posizioni diverse
type PrimoParametro<T> = T extends (primo: infer P, ...resto: never[]) => unknown ? P : never
type Risolto<T> = T extends Promise<infer V> ? V : T
type ChiaviDi<T> = T extends Record<infer K, unknown> ? K : never

// Ricorsivo: srotola le Promise annidate
type RisoltoProfondo<T> = T extends Promise<infer V> ? RisoltoProfondo<V> : T

type F = RisoltoProfondo<Promise<Promise<Promise<string>>>> // string
```

```typescript
// infer con vincolo (TypeScript 4.7+)
type PrimoSeStringa<T> = T extends readonly [infer P extends string, ...unknown[]] ? P : never

type G = PrimoSeStringa<['a', 1, true]> // 'a'
type H = PrimoSeStringa<[1, 'a']> // never
```

### Template literal type

```typescript
type Metodo = 'GET' | 'POST'
type Risorsa = 'utenti' | 'fatture'

// Il prodotto cartesiano delle due union
type Endpoint = `${Metodo} /api/${Risorsa}`
// 'GET /api/utenti' | 'GET /api/fatture' | 'POST /api/utenti' | 'POST /api/fatture'
```

```typescript
// Estrarre i parametri da un percorso: il tipo si calcola dalla stringa
type ParametriPercorso<T extends string> =
  T extends `${string}:${infer Parametro}/${infer Resto}`
    ? Parametro | ParametriPercorso<`/${Resto}`>
    : T extends `${string}:${infer Parametro}`
      ? Parametro
      : never

type P = ParametriPercorso<'/utenti/:idUtente/fatture/:idFattura'>
// 'idUtente' | 'idFattura'

// E si usa per tipizzare una funzione di navigazione
function vaiA<T extends string>(
  percorso: T,
  parametri: Record<ParametriPercorso<T>, string>,
): void {
  // ...
}

vaiA('/utenti/:idUtente/fatture/:idFattura', {
  idUtente: 'u-1',
  idFattura: 'f-2',
})

// vaiA('/utenti/:idUtente', {})  // ✗ manca idUtente
```

### Il tipo che rende leggibili gli errori

```typescript
// Un tipo composto da intersezioni viene mostrato come
// 'A & B & C' nei messaggi d'errore, che è illeggibile.
// Prettify lo appiattisce in un unico oggetto.
type Prettify<T> = { [K in keyof T]: T[K] } & {}

type Composto = Pick<Fattura, 'id'> & { extra: string }
type Leggibile = Prettify<Composto> // { id: string; extra: string }
```

`Prettify` non cambia il tipo: cambia come viene **mostrato**. Su tipi generici complessi la differenza fra un errore comprensibile e uno indecifrabile è tutta qui.

---

## B6. `as const`, `satisfies` e branded type

### `as const`

```typescript
// Senza: i tipi sono allargati
const rotte = {
  home: '/',
  fatture: '/fatture',
} // { home: string; fatture: string }

// Con: literal e readonly, in profondità
const rotteFisse = {
  home: '/',
  fatture: '/fatture',
} as const // { readonly home: '/'; readonly fatture: '/fatture' }

// E da lì si estraggono i tipi
type Rotta = (typeof rotteFisse)[keyof typeof rotteFisse] // '/' | '/fatture'
type NomeRotta = keyof typeof rotteFisse // 'home' | 'fatture'
```

```typescript
// Il pattern per gli array di costanti
const STATI = ['bozza', 'emessa', 'pagata'] as const

type Stato = (typeof STATI)[number] // 'bozza' | 'emessa' | 'pagata'

// L'array esiste a runtime — si può iterare e validare —
// e il tipo è derivato da lui: non possono divergere.
function eStato(valore: string): valore is Stato {
  return (STATI as readonly string[]).includes(valore)
}
```

### `satisfies`

Risolve un conflitto reale: verificare che un valore rispetti un tipo **senza** perdere l'inferenza precisa.

```typescript
type Configurazione = Record<string, string | number | boolean>

// ❌ Con l'annotazione, il tipo diventa quello annotato
//    e si perde la precisione
const conAnnotazione: Configurazione = {
  porta: 3000,
  host: 'localhost',
  debug: true,
}
const p1 = conAnnotazione.porta // string | number | boolean
// conAnnotazione.qualunque       // nessun errore: la index signature lo ammette

// ❌ Senza annotazione: precisione sì, verifica no
const senzaAnnotazione = {
  porta: 3000,
  host: 'localhost',
  debug: true,
}
const p2 = senzaAnnotazione.porta // number
// Ma nessuno verifica che rispetti Configurazione

// ✅ satisfies: verifica E conserva l'inferenza
const conSatisfies = {
  porta: 3000,
  host: 'localhost',
  debug: true,
} satisfies Configurazione

const p3 = conSatisfies.porta // number  ← preciso
// conSatisfies.qualunque       // ✗ Property 'qualunque' does not exist
```

```typescript
// Il caso d'uso più utile: una mappa di configurazioni
// dove le chiavi vanno verificate e i valori restano precisi
type Stato = 'bozza' | 'emessa' | 'pagata'

const COLORI_STATO = {
  bozza: { sfondo: '#f5f5f5', testo: '#525252' },
  emessa: { sfondo: '#dbeafe', testo: '#1e40af' },
  pagata: { sfondo: '#dcfce7', testo: '#166534' },
} satisfies Record<Stato, { sfondo: string; testo: string }>

// Verifica: se aggiungi uno stato all'union e dimentichi
// il colore, QUESTA riga diventa un errore.

// E l'inferenza resta precisa:
const sfondoBozza = COLORI_STATO.bozza.sfondo // string
type ChiaviColori = keyof typeof COLORI_STATO // 'bozza' | 'emessa' | 'pagata'
```

```typescript
// as const satisfies: entrambi i benefici
const ROTTE = {
  home: '/',
  fatture: '/fatture',
  dettaglioFattura: '/fatture/:id',
} as const satisfies Record<string, `/${string}`>

type Percorso = (typeof ROTTE)[keyof typeof ROTTE]
// '/' | '/fatture' | '/fatture/:id'   ← literal, non string
```

```
Il criterio, in una riga:

  : Tipo        quando vuoi che la variabile ABBIA quel tipo
  satisfies     quando vuoi solo VERIFICARE che lo rispetti,
                conservando il tipo dedotto
  as const      quando vuoi i literal invece dei tipi allargati
```

### `as`: l'assertion, e perché va evitata

```typescript
// as dice al compilatore "fidati". Se sbagli, non se ne accorge.
const risposta: unknown = { nome: 'Anna' }

// ❌ Nessuna verifica: se la forma è diversa, l'errore è a runtime
const utente = risposta as Utente
console.log(utente.eta.toFixed(0)) // TypeError: Cannot read properties of undefined

// ✅ Verificare, e restringere
function eUtente(valore: unknown): valore is Utente {
  return (
    typeof valore === 'object' &&
    valore !== null &&
    'nome' in valore &&
    typeof valore.nome === 'string' &&
    'eta' in valore &&
    typeof valore.eta === 'number'
  )
}

if (eUtente(risposta)) {
  console.log(risposta.eta.toFixed(0)) // sicuro
}
```

```typescript
// ❌ La doppia assertion: il modo di forzare qualunque cosa.
//    È sempre il segnale che qualcosa a monte è modellato male.
// const forzato = 'testo' as unknown as number
```

Gli usi legittimi di `as` sono tre: i branded type (dove la validazione è appena avvenuta), il narrowing di `document.querySelector` a un tipo specifico, e i mock nei test. Fuori da questi, è quasi sempre un problema di modellazione.

---

## B7. `tsconfig.json` e i flag strict

`"strict": true` accende otto flag. Vale la pena sapere cosa fa ciascuno, perché ognuno intercetta una categoria diversa di errori.

```typescript
// ── noImplicitAny ───────────────────────────────────────────
// Un parametro senza tipo dedotto è un errore invece di diventare any
// function f(x) { }   // ✗ Parameter 'x' implicitly has an 'any' type
function f(x: number) {}

// ── strictNullChecks ────────────────────────────────────────
// null e undefined non sono assegnabili a tutto:
// è il flag che vale più di tutti gli altri messi insieme
let testo: string = 'a'
// testo = null   // ✗

let forse: string | null = 'a'
forse = null // ok
// forse.toUpperCase()   // ✗ 'forse' is possibly 'null'

// ── strictFunctionTypes ─────────────────────────────────────
// I parametri delle funzioni sono controllati in modo controvariante
// (vedi B1). Non si applica ai metodi.

// ── strictBindCallApply ─────────────────────────────────────
// bind, call e apply verificano gli argomenti
function somma(a: number, b: number) {
  return a + b
}
// somma.call(null, 1, 'due')   // ✗

// ── strictPropertyInitialization ────────────────────────────
// Le proprietà di classe devono essere inizializzate
class Servizio {
  // nome: string          // ✗ non ha inizializzatore né è assegnata nel costruttore
  nome: string = ''
  altro!: string // ! dichiara "la assegno io altrove"
}

// ── noImplicitThis ──────────────────────────────────────────
// this implicitamente any è un errore

// ── useUnknownInCatchVariables ──────────────────────────────
// La variabile di catch è unknown invece che any

// ── alwaysStrict ────────────────────────────────────────────
// Emette 'use strict' e analizza in strict mode
```

### I flag oltre `strict` che vale la pena accendere

```json
{
  "compilerOptions": {
    "strict": true,

    // array[i] restituisce T | undefined: è la verità
    "noUncheckedIndexedAccess": true,

    // Un accesso a una proprietà opzionale in scrittura
    // non può cancellarla implicitamente
    "exactOptionalPropertyTypes": true,

    // Ogni case di uno switch deve terminare con break o return
    "noFallthroughCasesInSwitch": true,

    // Un ramo di una funzione che non restituisce è un errore
    "noImplicitReturns": true,

    // Le variabili e i parametri non usati sono errori
    // (spesso si delega a ESLint, che è più configurabile)
    "noUnusedLocals": true,
    "noUnusedParameters": true,

    // Chi sovrascrive un metodo deve dichiararlo con 'override'
    "noImplicitOverride": true,

    // Le proprietà dichiarate con index signature vanno lette
    // con la notazione a parentesi
    "noPropertyAccessFromIndexSignature": true
  }
}
```

```typescript
// exactOptionalPropertyTypes, spiegato con un esempio
type Opzioni = { timeout?: number }

// SENZA il flag: assegnare undefined è come non assegnare
const a: Opzioni = { timeout: undefined } // ok

// CON il flag: sono cose diverse
// const b: Opzioni = { timeout: undefined }
//   ✗ Type 'undefined' is not assignable to type 'number'

// Per ammettere entrambi, va dichiarato
type OpzioniEsplicite = { timeout?: number | undefined }
const c: OpzioniEsplicite = { timeout: undefined } // ok
```

La distinzione conta con gli oggetti di aggiornamento: `{ nome: undefined }` e `{}` significano cose diverse — "cancella il nome" e "non toccare il nome" — e senza il flag il tipo non le distingue.

### `verbatimModuleSyntax` e `import type`

```typescript
// Con verbatimModuleSyntax, un import usato SOLO come tipo
// deve essere dichiarato come tale
import type { Fattura } from './tipi.js'
import { creaFattura } from './fabbrica.js'

// Forma mista
import { creaFattura as crea, type Fattura as F } from './modulo.js'
```

```
Perché conta: senza 'import type', il transpiler non sa se
l'import va rimosso o conservato. Con moduli che hanno effetti
collaterali, rimuoverlo per sbaglio rompe il codice; conservarlo
per sbaglio impedisce il tree shaking.

'import type' rende la decisione esplicita, e sposta
l'ambiguità dal transpiler a chi scrive.
```

---

## B8. File di dichiarazione e augmentation

### `.d.ts`

Un file di dichiarazione contiene solo tipi: nessun codice, nessuna emissione.

```typescript
// src/tipi/globali.d.ts

// Dichiarare un modulo che non ha i tipi
declare module 'libreria-senza-tipi' {
  export function elabora(dati: string): number
  export default function principale(): void
}

// Dichiarare l'import di risorse non JavaScript
declare module '*.svg' {
  const contenuto: string
  export default contenuto
}

declare module '*.module.css' {
  const classi: Record<string, string>
  export default classi
}
```

### Estendere i tipi globali

```typescript
// src/tipi/ambiente.d.ts

// declare global funziona solo dentro un MODULO:
// serve un export o un import nel file, altrimenti
// il file è già globale e 'declare global' è un errore
export {}

declare global {
  interface Window {
    analitica?: {
      traccia(evento: string, dati?: Record<string, unknown>): void
    }
    __STATO_INIZIALE__?: unknown
  }

  // Le variabili d'ambiente di Node
  namespace NodeJS {
    interface ProcessEnv {
      readonly DATABASE_URL: string
      readonly JWT_SECRET: string
      readonly NODE_ENV: 'development' | 'production' | 'test'
    }
  }
}
```

```typescript
// Le variabili d'ambiente di Vite
// src/tipi/vite-env.d.ts

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

Il vantaggio è concreto: `import.meta.env.VITE_API_BASE_UR` (con il refuso) diventa un errore di compilazione invece di `undefined` in produzione.

### Module augmentation

```typescript
// Aggiungere proprietà ai tipi di una libreria esistente
import 'express'

declare module 'express' {
  interface Request {
    utente?: {
      id: string
      ruoli: readonly string[]
    }
    idRichiesta: string
  }
}
```

```typescript
// Estendere gli eventi personalizzati del DOM
declare global {
  interface HTMLElementEventMap {
    'fattura:pagata': CustomEvent<{ id: string; importo: number }>
    'carrello:modificato': CustomEvent<{ righe: number; totale: number }>
  }
}

// Da qui, il tipo del dettaglio è noto
elemento.addEventListener('fattura:pagata', (evento) => {
  console.log(evento.detail.importo) // number, non any
})
```

---

## B9. Il confine con il runtime: Zod

I tipi spariscono alla compilazione. Ogni dato che arriva da fuori — rete, `localStorage`, `postMessage`, un file, l'URL — può avere qualunque forma, e il compilatore non può saperlo.

```typescript
// ❌ La bugia più diffusa nel codice TypeScript
async function recuperaSbagliato(id: string): Promise<Utente> {
  const risposta = await fetch(`/api/utenti/${id}`)
  return risposta.json() // il tipo dichiarato è una PROMESSA non verificata
}

// Se l'API cambia, o restituisce un errore in formato diverso,
// il tipo dice Utente e il valore è altro. L'errore emerge
// venti righe più in là, con un messaggio che non c'entra.
```

```powershell
pnpm add zod
```

```typescript
import { z } from 'zod'

// Lo SCHEMA esiste a runtime e valida davvero
const SchemaUtente = z.object({
  id: z.string().uuid(),
  nome: z.string().min(1).max(100),
  email: z.string().email(),
  eta: z.number().int().min(0).max(150),
  ruolo: z.enum(['admin', 'utente', 'ospite']),
  creatoIl: z.coerce.date(), // accetta una stringa ISO e produce una Date
  note: z.string().optional(),
})

// Il TIPO si deriva dallo schema: non possono divergere
type Utente = z.infer<typeof SchemaUtente>
// {
//   id: string; nome: string; email: string; eta: number
//   ruolo: 'admin' | 'utente' | 'ospite'; creatoIl: Date; note?: string
// }
```

```typescript
// ✅ La verifica avviene al confine, una volta sola
async function recuperaUtente(id: string): Promise<Utente> {
  const risposta = await fetch(`/api/utenti/${id}`)

  if (!risposta.ok) {
    throw new Error(`${risposta.status} ${risposta.statusText}`)
  }

  const grezzo: unknown = await risposta.json()

  // parse solleva se la forma non corrisponde
  return SchemaUtente.parse(grezzo)
}

// La variante che non solleva
async function recuperaUtenteSicuro(id: string) {
  const risposta = await fetch(`/api/utenti/${id}`)
  const grezzo: unknown = await risposta.json()

  const esito = SchemaUtente.safeParse(grezzo)

  if (!esito.success) {
    // Gli errori sono strutturati, per campo
    console.error(esito.error.flatten().fieldErrors)
    return null
  }

  return esito.data // tipizzato
}
```

### Trasformazioni e affinamenti

```typescript
const SchemaFattura = z
  .object({
    numero: z.string().regex(/^\d{4}-\d{3}$/, 'formato atteso AAAA-NNN'),
    // Gli importi arrivano in centesimi e si convertono in euro
    importoCentesimi: z.number().int().nonnegative(),
    dataEmissione: z.coerce.date(),
    dataScadenza: z.coerce.date(),
    righe: z
      .array(
        z.object({
          descrizione: z.string().min(1),
          quantita: z.number().positive(),
          prezzoUnitario: z.number().nonnegative(),
        }),
      )
      .min(1, 'la fattura deve avere almeno una riga'),
  })
  // refine verifica una regola che coinvolge più campi
  .refine((f) => f.dataScadenza >= f.dataEmissione, {
    message: 'la scadenza non può precedere l emissione',
    path: ['dataScadenza'],
  })
  // transform cambia la forma dopo la validazione
  .transform((f) => ({
    ...f,
    importoEuro: f.importoCentesimi / 100,
    totaleRighe: f.righe.reduce((s, r) => s + r.quantita * r.prezzoUnitario, 0),
  }))

type Fattura = z.infer<typeof SchemaFattura>
// include importoEuro e totaleRighe, aggiunti dalla trasformazione
```

### Validare le variabili d'ambiente all'avvio

```typescript
// src/ambiente.ts
import { z } from 'zod'

const SchemaAmbiente = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().int().positive().default(3000),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32, 'il segreto deve avere almeno 32 caratteri'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
})

const esito = SchemaAmbiente.safeParse(process.env)

if (!esito.success) {
  console.error('Configurazione non valida:\n')
  for (const [campo, errori] of Object.entries(esito.error.flatten().fieldErrors)) {
    console.error(`  ${campo}: ${errori?.join(', ')}`)
  }
  process.exit(1)
}

export const ambiente = esito.data
```

```
# Output atteso con una configurazione errata:
Configurazione non valida:

  DATABASE_URL: Invalid url
  JWT_SECRET: il segreto deve avere almeno 32 caratteri
```

Fallire all'avvio con un messaggio preciso è incomparabilmente meglio che scoprire alla prima query che `DATABASE_URL` era vuota.

### Le alternative

| | Zod | Valibot | ArkType | TypeBox |
|---|---|---|---|---|
| Peso (gzip) | ~14 kB | **~2 kB** (modulare) | ~12 kB | ~10 kB |
| API | concatenata | funzionale | sintassi simile a TS | schema JSON |
| Adozione | **la più ampia** | in crescita | di nicchia | standard JSON Schema |
| Integrazioni | tRPC, RHF, ecc. | crescenti | poche | OpenAPI |

Zod è la scelta predefinita per l'ecosistema. Valibot pesa molto meno grazie al tree shaking, e conta quando lo schema finisce nel bundle del browser.

```
La regola che riassume tutto B9:

  Valida al CONFINE, fidati all'INTERNO.

  I punti di confine sono: risposte di rete, JSON.parse,
  localStorage, URL e query string, postMessage, form,
  file caricati, variabili d'ambiente, webhook.

  Dentro quel confine, i tipi di TypeScript bastano.
  Validare due volte è rumore; non validare al confine
  è una bugia che il compilatore non può smascherare.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Modellare uno stato con una discriminated union

**Obiettivo:** sostituire un tipo che ammette stati impossibili con uno in cui gli stati impossibili non si possono nemmeno scrivere.

```typescript
// PARTENZA — ogni campo è opzionale, e nulla impedisce
// combinazioni insensate
type StatoRichiestaSbagliato = {
  inCaricamento?: boolean
  dati?: string[]
  errore?: Error
  ultimoAggiornamento?: Date
}

// Tutti questi compilano, e nessuno ha senso:
const a: StatoRichiestaSbagliato = { inCaricamento: true, errore: new Error('x') }
const b: StatoRichiestaSbagliato = { dati: ['x'], errore: new Error('y') }
const c: StatoRichiestaSbagliato = {}
```

```typescript
// SOLUZIONE

type StatoRichiesta<T> =
  | { stato: 'inattiva' }
  | { stato: 'caricamento'; iniziataIl: number }
  | { stato: 'riuscita'; dati: T; aggiornatoIl: Date; durataMs: number }
  | { stato: 'fallita'; errore: Error; tentativi: number; ultimoTentativoIl: Date }

// Gli stati impossibili non sono più scrivibili:
// const impossibile: StatoRichiesta<string[]> = {
//   stato: 'caricamento',
//   errore: new Error('x'),
// }
//   ✗ Object literal may only specify known properties

/**
 * L'esaustività: aggiungendo una variante all'union senza
 * gestirla, il ramo default diventa un errore di compilazione.
 */
function descrivi<T>(richiesta: StatoRichiesta<T>): string {
  switch (richiesta.stato) {
    case 'inattiva':
      return 'In attesa'

    case 'caricamento':
      return `In corso da ${Date.now() - richiesta.iniziataIl} ms`

    case 'riuscita':
      return `Completata in ${richiesta.durataMs} ms`

    case 'fallita':
      return `Fallita dopo ${richiesta.tentativi} tentativi: ${richiesta.errore.message}`

    default: {
      const esaustivo: never = richiesta
      throw new Error(`Stato non gestito: ${JSON.stringify(esaustivo)}`)
    }
  }
}

/** Le transizioni sono funzioni pure: da uno stato al successivo. */
const transizioni = {
  avvia(): Extract<StatoRichiesta<never>, { stato: 'caricamento' }> {
    return { stato: 'caricamento', iniziataIl: Date.now() }
  },

  completa<T>(
    precedente: Extract<StatoRichiesta<T>, { stato: 'caricamento' }>,
    dati: T,
  ): Extract<StatoRichiesta<T>, { stato: 'riuscita' }> {
    return {
      stato: 'riuscita',
      dati,
      aggiornatoIl: new Date(),
      durataMs: Date.now() - precedente.iniziataIl,
    }
  },

  fallisci<T>(
    errore: Error,
    tentativiPrecedenti = 0,
  ): Extract<StatoRichiesta<T>, { stato: 'fallita' }> {
    return {
      stato: 'fallita',
      errore,
      tentativi: tentativiPrecedenti + 1,
      ultimoTentativoIl: new Date(),
    }
  },
}
```

```typescript
// I type guard, per usare lo stato senza switch
function eRiuscita<T>(
  richiesta: StatoRichiesta<T>,
): richiesta is Extract<StatoRichiesta<T>, { stato: 'riuscita' }> {
  return richiesta.stato === 'riuscita'
}

const richiesta: StatoRichiesta<string[]> = {
  stato: 'riuscita',
  dati: ['a', 'b'],
  aggiornatoIl: new Date(),
  durataMs: 120,
}

if (eRiuscita(richiesta)) {
  console.log(richiesta.dati.length) // string[], senza controlli
}
```

```
# Cosa si guadagna:
#
# 1. GLI STATI IMPOSSIBILI NON ESISTONO.
#    Con il tipo di partenza, { inCaricamento: true, errore: ... }
#    compila. Con la discriminated union non è nemmeno scrivibile.
#
# 2. L'ACCESSO È SICURO SENZA CONTROLLI.
#    Nel ramo 'riuscita', dati è T e non T | undefined:
#    niente dati?.length sparso ovunque.
#
# 3. AGGIUNGERE UNA VARIANTE FA EMERGERE TUTTI I PUNTI
#    da aggiornare. Aggiungi { stato: 'annullata' } e il
#    compilatore elenca ogni switch da completare.
#    È il beneficio che ripaga da solo l'adozione di TypeScript.
#
# LA REGOLA GENERALE:
#   rendere impossibili da RAPPRESENTARE gli stati che non
#   devono esistere, invece di verificarli a runtime.
```

---

### Esercizio 2 — Generics con vincoli: un accessore per percorso

**Obiettivo:** una funzione che legga una proprietà annidata conservando il tipo esatto del valore letto.

```typescript
// SOLUZIONE

/** Legge una proprietà, conservando il tipo. */
function leggi<T, K extends keyof T>(oggetto: T, chiave: K): T[K] {
  return oggetto[chiave]
}

/** Due livelli. */
function leggi2<T, K1 extends keyof T, K2 extends keyof T[K1]>(
  oggetto: T,
  c1: K1,
  c2: K2,
): T[K1][K2] {
  return oggetto[c1][c2]
}

/** Tre livelli. */
function leggi3<T, K1 extends keyof T, K2 extends keyof T[K1], K3 extends keyof T[K1][K2]>(
  oggetto: T,
  c1: K1,
  c2: K2,
  c3: K3,
): T[K1][K2][K3] {
  return oggetto[c1][c2][c3]
}

interface Configurazione {
  server: {
    http: { porta: number; host: string }
    tls: { certificato: string; abilitato: boolean }
  }
  database: {
    connessione: { url: string; poolMassimo: number }
  }
}

declare const configurazione: Configurazione

const porta = leggi3(configurazione, 'server', 'http', 'porta') // number
const url = leggi2(leggi(configurazione, 'database'), 'connessione', 'url') // string

// leggi3(configurazione, 'server', 'http', 'inesistente')  // ✗
// leggi3(configurazione, 'server', 'tls', 'porta')          // ✗ non esiste in tls
```

```typescript
// LA VERSIONE GENERALE: un percorso come stringa,
// con il tipo calcolato dalla stringa stessa

/** Tutti i percorsi validi di un oggetto, come union di literal. */
type Percorsi<T> = T extends object
  ? {
      [K in keyof T & string]: T[K] extends object
        ? K | `${K}.${Percorsi<T[K]>}`
        : K
    }[keyof T & string]
  : never

/** Il tipo del valore in fondo a un percorso. */
type ValoreIn<T, P extends string> = P extends `${infer Testa}.${infer Coda}`
  ? Testa extends keyof T
    ? ValoreIn<T[Testa], Coda>
    : never
  : P extends keyof T
    ? T[P]
    : never

type PercorsiConfig = Percorsi<Configurazione>
// 'server' | 'database' | 'server.http' | 'server.tls'
// | 'server.http.porta' | 'server.http.host' | ...

function leggiPercorso<T, P extends Percorsi<T>>(oggetto: T, percorso: P): ValoreIn<T, P> {
  return percorso
    .split('.')
    .reduce<unknown>((corrente, chiave) => (corrente as Record<string, unknown>)[chiave], oggetto) as ValoreIn<T, P>
}

const porta2 = leggiPercorso(configurazione, 'server.http.porta') // number
const abilitato = leggiPercorso(configurazione, 'server.tls.abilitato') // boolean

// leggiPercorso(configurazione, 'server.http.inesistente')  // ✗
// leggiPercorso(configurazione, 'refuso')                    // ✗
```

```
# I meccanismi in gioco:
#
# K extends keyof T      il vincolo che limita la chiave a quelle
#                        esistenti, e permette a T[K] di essere preciso
#
# T[K]                   indexed access type: il tipo del valore
#                        alla chiave K
#
# Percorsi<T>            mapped type RICORSIVO che produce
#                        'a' | 'a.b' | 'a.b.c' ...
#                        Il [keyof T & string] finale trasforma
#                        l'oggetto in una union dei suoi valori.
#
# ValoreIn<T, P>         conditional type ricorsivo con infer:
#                        spezza il percorso al primo punto e
#                        scende di un livello a ogni passo
#
# QUANDO USARE QUALE:
#   La versione a livelli fissi è più leggibile e produce errori
#   più chiari. La versione con i percorsi è più elegante ma
#   i messaggi d'errore diventano illeggibili su oggetti grandi,
#   e su strutture molto profonde rallenta il compilatore.
#
#   Per un'API pubblica: livelli fissi.
#   Per un'utility interna dove i percorsi sono molti: la generale.
```

---

### Esercizio 3 — Costruire da zero gli utility type

**Obiettivo:** implementare `Partial`, `Pick`, `Omit`, `Exclude`, `ReturnType` e `Awaited` per capire come sono fatti.

```typescript
// SOLUZIONE

interface Fattura {
  id: string
  numero: string
  importo: number
  pagata: boolean
  note?: string
}

// ── 1. Partial: aggiunge ? a ogni proprietà ─────────────────
type MioPartial<T> = { [K in keyof T]?: T[K] }

type A1 = MioPartial<Fattura>
// { id?: string; numero?: string; importo?: number; pagata?: boolean; note?: string }

// ── 2. Required: -? RIMUOVE l'opzionalità ───────────────────
type MioRequired<T> = { [K in keyof T]-?: T[K] }

type A2 = MioRequired<Fattura> // note diventa obbligatoria

// ── 3. Readonly, e il suo inverso ───────────────────────────
type MioReadonly<T> = { readonly [K in keyof T]: T[K] }
type MioMutabile<T> = { -readonly [K in keyof T]: T[K] }

// ── 4. Pick: itera solo sulle chiavi indicate ───────────────
type MioPick<T, K extends keyof T> = { [P in K]: T[P] }

type A3 = MioPick<Fattura, 'id' | 'importo'> // { id: string; importo: number }

// ── 5. Exclude: conditional type DISTRIBUTIVO ───────────────
// Con T generico nudo, si applica a ogni membro dell'union
type MioExclude<T, U> = T extends U ? never : T

type A4 = MioExclude<'a' | 'b' | 'c', 'b'> // 'a' | 'c'
//   ('a' extends 'b' ? never : 'a')  →  'a'
// | ('b' extends 'b' ? never : 'b')  →  never  (sparisce)
// | ('c' extends 'b' ? never : 'c')  →  'c'

type MioExtract<T, U> = T extends U ? T : never

// ── 6. Omit: Pick sulle chiavi rimaste ──────────────────────
type MioOmit<T, K extends keyof never> = MioPick<T, MioExclude<keyof T, K>>

type A5 = MioOmit<Fattura, 'id'> // tutto tranne id

// ── 7. ReturnType: infer nella posizione del ritorno ────────
type MioReturnType<T extends (...argomenti: never[]) => unknown> = T extends (
  ...argomenti: never[]
) => infer R
  ? R
  : never

function creaFattura(): Fattura {
  return { id: '', numero: '', importo: 0, pagata: false }
}

type A6 = MioReturnType<typeof creaFattura> // Fattura

// ── 8. Parameters: infer nella posizione dei parametri ──────
type MioParameters<T extends (...argomenti: never[]) => unknown> = T extends (
  ...argomenti: infer P
) => unknown
  ? P
  : never

// ── 9. Awaited: ricorsivo, srotola le Promise annidate ──────
type MioAwaited<T> = T extends Promise<infer V> ? MioAwaited<V> : T

type A7 = MioAwaited<Promise<Promise<string>>> // string
type A8 = MioAwaited<number> // number

// ── 10. NonNullable ─────────────────────────────────────────
type MioNonNullable<T> = T extends null | undefined ? never : T

type A9 = MioNonNullable<string | null | undefined> // string
```

```typescript
// ── I DUE COMPORTAMENTI CHE SORPRENDONO ─────────────────────

// A. La DISTRIBUTIVITÀ, e come disattivarla
type Distributivo<T> = T extends string ? 'sì' : 'no'
type B1 = Distributivo<string | number> // 'sì' | 'no'  ← applicato a ciascuno

// Avvolgendo in una tupla, la distributività sparisce
type NonDistributivo<T> = [T] extends [string] ? 'sì' : 'no'
type B2 = NonDistributivo<string | number> // 'no'  ← valutato in blocco

// L'uso pratico: verificare se un tipo È never
type ENever<T> = [T] extends [never] ? true : false
type B3 = ENever<never> // true
// Senza le tuple sarebbe never, perché la distribuzione
// su never non produce alcun membro.

// B. never SPARISCE dalle union, ma non dalle tuple
type B4 = string | never // string
type B5 = [string, never] // [string, never]  ← resta
```

```typescript
// ── UTILITY PROPRI CHE VALGONO LA PENA ──────────────────────

/** Rende leggibili i tipi composti nei messaggi d'errore. */
type Prettify<T> = { [K in keyof T]: T[K] } & {}

/** Omit che verifica l'esistenza delle chiavi: un refuso diventa errore. */
type OmitSicuro<T, K extends keyof T> = Prettify<Omit<T, K>>

// type Sbagliato = OmitSicuro<Fattura, 'importoo'>  // ✗ errore
type Giusto = OmitSicuro<Fattura, 'id'> // ok

/** Rende opzionali SOLO alcune chiavi. */
type ParzialeSu<T, K extends keyof T> = Prettify<Omit<T, K> & Partial<Pick<T, K>>>

type NuovaFattura = ParzialeSu<Fattura, 'id' | 'pagata'>
// id e pagata opzionali, il resto obbligatorio

/** Rende obbligatorie SOLO alcune chiavi. */
type ObbligatorioSu<T, K extends keyof T> = Prettify<Omit<T, K> & Required<Pick<T, K>>>

/** Partial ricorsivo, per gli aggiornamenti annidati. */
type PartialProfondo<T> = T extends object
  ? { [K in keyof T]?: PartialProfondo<T[K]> }
  : T

/** Readonly ricorsivo. */
type ReadonlyProfondo<T> = T extends object
  ? { readonly [K in keyof T]: ReadonlyProfondo<T[K]> }
  : T

/** Le chiavi di T il cui valore è di tipo V. */
type ChiaviDiTipo<T, V> = { [K in keyof T]-?: T[K] extends V ? K : never }[keyof T]

type ChiaviStringa = ChiaviDiTipo<Fattura, string> // 'id' | 'numero'
type ChiaviNumero = ChiaviDiTipo<Fattura, number> // 'importo'

/** Almeno una delle chiavi indicate deve essere presente. */
type AlmenoUna<T, K extends keyof T = keyof T> = K extends unknown
  ? Prettify<Partial<T> & Required<Pick<T, K>>>
  : never

type FiltroRicerca = AlmenoUna<{ nome: string; email: string; telefono: string }>
// almeno uno dei tre campi deve esserci

const f1: FiltroRicerca = { nome: 'Anna' } // ok
const f2: FiltroRicerca = { email: 'a@b.it', telefono: '02' } // ok
// const f3: FiltroRicerca = {}                                 // ✗
```

```
# La lezione generale:
#
# Gli utility type non sono magia: sono mapped e conditional
# type che potresti scrivere in tre righe. Capirne la
# costruzione permette di scriverne di propri quando i
# venti forniti non bastano — e capita spesso.
#
# I due meccanismi che spiegano quasi tutto:
#   [K in keyof T]     itera sulle chiavi
#   T extends U ? A:B  decide, e distribuisce sulle union
#
# E i tre modificatori:
#   ?  -?  readonly  -readonly
```

---

### Esercizio 4 — Un client API tipizzato end-to-end

**Obiettivo:** un client in cui il tipo della risposta si deduce dall'endpoint richiesto, e i parametri del percorso sono verificati.

```typescript
// SOLUZIONE
import { z } from 'zod'

// ── 1. Gli schemi: esistono a runtime, e da loro nascono i tipi ──
const SchemaUtente = z.object({
  id: z.string().uuid(),
  nome: z.string().min(1),
  email: z.string().email(),
  ruolo: z.enum(['admin', 'utente']),
})

const SchemaFattura = z.object({
  id: z.string().uuid(),
  numero: z.string(),
  clienteId: z.string().uuid(),
  importoCentesimi: z.number().int().nonnegative(),
  pagata: z.boolean(),
  emessaIl: z.coerce.date(),
})

type Utente = z.infer<typeof SchemaUtente>
type Fattura = z.infer<typeof SchemaFattura>

// ── 2. La mappa degli endpoint: percorso → schema ────────────
const ENDPOINT = {
  'GET /utenti': z.array(SchemaUtente),
  'GET /utenti/:id': SchemaUtente,
  'POST /utenti': SchemaUtente,
  'GET /fatture': z.array(SchemaFattura),
  'GET /fatture/:id': SchemaFattura,
  'GET /utenti/:idUtente/fatture': z.array(SchemaFattura),
} as const

type Endpoint = keyof typeof ENDPOINT

// ── 3. I tipi calcolati dagli endpoint ───────────────────────

/** Il tipo della risposta, dedotto dallo schema associato. */
type RispostaDi<E extends Endpoint> = z.infer<(typeof ENDPOINT)[E]>

/** I nomi dei parametri presenti nel percorso. */
type ParametriDi<S extends string> = S extends `${string}:${infer P}/${infer Resto}`
  ? P | ParametriDi<`/${Resto}`>
  : S extends `${string}:${infer P}`
    ? P
    : never

/** Se non ci sono parametri, l'oggetto non va nemmeno passato. */
type OpzioniDi<E extends Endpoint> = [ParametriDi<E>] extends [never]
  ? { corpo?: unknown; segnale?: AbortSignal }
  : { parametri: Record<ParametriDi<E>, string>; corpo?: unknown; segnale?: AbortSignal }

type P1 = ParametriDi<'GET /utenti/:id'> // 'id'
type P2 = ParametriDi<'GET /utenti/:idUtente/fatture'> // 'idUtente'
type P3 = ParametriDi<'GET /utenti'> // never

// ── 4. Il client ─────────────────────────────────────────────

class ErroreApi extends Error {
  constructor(
    readonly stato: number,
    readonly url: string,
    readonly corpo: unknown,
  ) {
    super(`${stato} — ${url}`)
    this.name = 'ErroreApi'
  }
}

class ErroreSchema extends Error {
  constructor(
    readonly endpoint: string,
    readonly dettagli: z.ZodError,
  ) {
    super(`Risposta non conforme allo schema di ${endpoint}`)
    this.name = 'ErroreSchema'
  }
}

class ClienteApi {
  constructor(private readonly base: string) {}

  async chiama<E extends Endpoint>(endpoint: E, opzioni: OpzioniDi<E>): Promise<RispostaDi<E>> {
    const [metodo, modello] = endpoint.split(' ') as [string, string]

    // Sostituisce i :parametri con i valori forniti
    const parametri = (opzioni as { parametri?: Record<string, string> }).parametri ?? {}
    const percorso = modello.replaceAll(/:(\w+)/g, (_, nome: string) => {
      const valore = parametri[nome]
      if (valore === undefined) {
        throw new Error(`Parametro mancante nel percorso: ${nome}`)
      }
      return encodeURIComponent(valore)
    })

    const risposta = await fetch(`${this.base}${percorso}`, {
      method: metodo,
      headers: opzioni.corpo ? { 'Content-Type': 'application/json' } : undefined,
      body: opzioni.corpo ? JSON.stringify(opzioni.corpo) : undefined,
      signal: opzioni.segnale,
    })

    const grezzo: unknown = await risposta.json().catch(() => null)

    if (!risposta.ok) {
      throw new ErroreApi(risposta.status, risposta.url, grezzo)
    }

    // La validazione al confine: da qui il tipo è garantito
    const esito = ENDPOINT[endpoint].safeParse(grezzo)

    if (!esito.success) {
      throw new ErroreSchema(endpoint, esito.error)
    }

    return esito.data as RispostaDi<E>
  }
}
```

```typescript
// ── 5. L'uso: tutto è dedotto ────────────────────────────────
const api = new ClienteApi('https://esempio.it/api')

async function caricaPagina() {
  // Nessun parametro richiesto: l'oggetto parametri non serve
  const utenti = await api.chiama('GET /utenti', {})
  //    ^? Utente[]

  // Parametro richiesto e verificato
  const utente = await api.chiama('GET /utenti/:id', {
    parametri: { id: 'u-1' },
  })
  //    ^? Utente

  const fatture = await api.chiama('GET /utenti/:idUtente/fatture', {
    parametri: { idUtente: 'u-1' },
  })
  //    ^? Fattura[]

  return { utenti, utente, fatture }
}

// Gli errori che il compilatore intercetta:
//
// api.chiama('GET /utenti/:id', {})
//   ✗ Property 'parametri' is missing
//
// api.chiama('GET /utenti/:id', { parametri: { identificativo: 'x' } })
//   ✗ 'identificativo' does not exist in type Record<'id', string>
//
// api.chiama('GET /inesistente', {})
//   ✗ Argument of type '"GET /inesistente"' is not assignable
//
// const n: number = await api.chiama('GET /utenti', {})
//   ✗ Type 'Utente[]' is not assignable to type 'number'
```

```
# Cosa rende questo client diverso da uno normale:
#
# 1. IL TIPO DELLA RISPOSTA NON SI DICHIARA, si deduce.
#    Nessun  api.get<Utente[]>('/utenti')  in cui il generico
#    è una promessa non verificata. Qui il tipo VIENE
#    dallo schema che validerà davvero la risposta.
#
# 2. LO SCHEMA È L'UNICA FONTE.
#    z.infer deriva il tipo dallo schema: non possono
#    divergere, perché sono la stessa dichiarazione.
#
# 3. I PARAMETRI DEL PERCORSO SONO CALCOLATI DALLA STRINGA.
#    ParametriDi<'GET /utenti/:id'> produce 'id' analizzando
#    il literal type. Cambiando il percorso, i parametri
#    richiesti cambiano da soli.
#
# 4. GLI ENDPOINT SENZA PARAMETRI NON CHIEDONO L'OGGETTO.
#    [ParametriDi<E>] extends [never] — con le tuple per
#    disattivare la distributività, altrimenti never
#    non produrrebbe alcun ramo.
#
# 5. LA VALIDAZIONE È AL CONFINE, una volta sola.
#    Dopo safeParse, il tipo non è una promessa: è verificato.
```

---

### Esercizio 5 — Branded type per identificativi e denaro

**Obiettivo:** impedire che due identificativi diversi, entrambi stringhe, si possano scambiare.

```typescript
// PARTENZA — il bug che compila
function trasferisci(daContoId: string, aContoId: string, importo: number) {
  // ...
}

const contoOrigine = 'c-1'
const contoDestinazione = 'c-2'
const importoEuro = 150.5

// Argomenti invertiti: nessun errore, e i soldi vanno dalla parte sbagliata
trasferisci(contoDestinazione, contoOrigine, importoEuro)
```

```typescript
// SOLUZIONE

// ── L'infrastruttura dei brand ───────────────────────────────
declare const marchio: unique symbol

type Marchiato<T, M extends string> = T & { readonly [marchio]: M }

// ── Gli identificativi ───────────────────────────────────────
type IdConto = Marchiato<string, 'IdConto'>
type IdUtente = Marchiato<string, 'IdUtente'>
type IdTransazione = Marchiato<string, 'IdTransazione'>

// ── Le unità monetarie ───────────────────────────────────────
type Centesimi = Marchiato<number, 'Centesimi'>
type Euro = Marchiato<number, 'Euro'>

// ── I costruttori: l'unico modo di produrre un valore marchiato.
//    Concentrano la validazione in un punto solo.
function idConto(grezzo: string): IdConto {
  if (!/^c-\d+$/.test(grezzo)) {
    throw new TypeError(`Identificativo conto non valido: ${grezzo}`)
  }
  return grezzo as IdConto
}

function idUtente(grezzo: string): IdUtente {
  if (!/^u-\d+$/.test(grezzo)) {
    throw new TypeError(`Identificativo utente non valido: ${grezzo}`)
  }
  return grezzo as IdUtente
}

/** Il denaro si tiene SEMPRE in centesimi interi: mai in virgola mobile. */
function centesimi(valore: number): Centesimi {
  if (!Number.isInteger(valore)) {
    throw new TypeError(`I centesimi devono essere interi: ${valore}`)
  }
  if (valore < 0) {
    throw new TypeError(`Importo negativo: ${valore}`)
  }
  return valore as Centesimi
}

function euroInCentesimi(euro: number): Centesimi {
  return centesimi(Math.round(euro * 100))
}

function formattaCentesimi(valore: Centesimi): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(
    valore / 100,
  )
}

// ── Le operazioni: i tipi impediscono gli errori di dominio ──
function somma(a: Centesimi, b: Centesimi): Centesimi {
  return (a + b) as Centesimi
}

function sottrai(a: Centesimi, b: Centesimi): Centesimi {
  return centesimi(a - b) // il costruttore rifiuta i negativi
}

function trasferisciSicuro(
  da: IdConto,
  a: IdConto,
  importo: Centesimi,
): { transazione: IdTransazione; importo: Centesimi } {
  if (da === a) {
    throw new Error('Origine e destinazione coincidono')
  }
  return {
    transazione: crypto.randomUUID() as IdTransazione,
    importo,
  }
}
```

```typescript
// ── L'uso ────────────────────────────────────────────────────
const origine = idConto('c-1')
const destinazione = idConto('c-2')
const utente = idUtente('u-7')
const importo = euroInCentesimi(150.5) // 15050 centesimi

trasferisciSicuro(origine, destinazione, importo) // ok

// Gli errori che il compilatore ora intercetta:
//
// trasferisciSicuro(utente, destinazione, importo)
//   ✗ IdUtente non è assegnabile a IdConto
//
// trasferisciSicuro('c-1', 'c-2', importo)
//   ✗ string non è assegnabile a IdConto
//
// trasferisciSicuro(origine, destinazione, 150.5)
//   ✗ number non è assegnabile a Centesimi
//
// somma(importo, 100)
//   ✗ number non è assegnabile a Centesimi

console.log(formattaCentesimi(somma(importo, centesimi(500)))) // '155,50 €'
```

```
# Output atteso:
155,50 €
```

```
# Cosa costa e cosa rende:
#
# A RUNTIME: nulla. Il marchio è una proprietà fantasma che
# esiste solo per il compilatore. Il JavaScript prodotto è
# identico a quello senza brand.
#
# IL COSTO REALE è la conversione al confine: i dati che
# arrivano da fuori sono stringhe e numeri normali, e vanno
# fatti passare dai costruttori. Ed è esattamente il punto:
# quella conversione È la validazione, e concentrarla nei
# costruttori garantisce che nessun valore non validato
# entri nel sistema.
#
# QUANDO NE VALE LA PENA:
#   · identificativi di entità diverse, tutti string
#   · unità di misura: centesimi contro euro, metri contro piedi,
#     millisecondi contro secondi
#   · stringhe già validate: email verificata, URL normalizzato,
#     HTML sanificato
#   · valori con un invariante: intero positivo, percentuale 0-100
#
# QUANDO NO:
#   · su tutto: la conversione ai confini diventa rumore
#   · su tipi che non si scambiano mai fra loro
#
# IL DENARO merita una nota a parte. Tenerlo in virgola mobile
# è un errore che si paga: 0.1 + 0.2 !== 0.3, e su migliaia
# di righe gli arrotondamenti divergono. Centesimi interi
# più un branded type che impedisce di confonderli con gli
# euro elimina l'intera categoria di problemi.
```

---

### Esercizio 6 — Validare i dati esterni con Zod

**Obiettivo:** trasformare tre punti di ingresso non fidati — API, `localStorage`, query string — in dati tipizzati e verificati.

```typescript
// SOLUZIONE
import { z } from 'zod'

// ── 1. RISPOSTA DI RETE ──────────────────────────────────────

const SchemaRigaFattura = z.object({
  descrizione: z.string().min(1),
  quantita: z.number().positive(),
  prezzoUnitarioCentesimi: z.number().int().nonnegative(),
})

const SchemaFattura = z
  .object({
    id: z.string().uuid(),
    numero: z.string().regex(/^\d{4}-\d{3}$/, 'formato atteso AAAA-NNN'),
    emessaIl: z.coerce.date(),
    scadeIl: z.coerce.date(),
    righe: z.array(SchemaRigaFattura).min(1, 'serve almeno una riga'),
    // I campi sconosciuti vengono scartati invece di passare
    stato: z.enum(['bozza', 'emessa', 'pagata', 'annullata']),
  })
  .strict() // un campo in più è un errore, non viene ignorato
  .refine((f) => f.scadeIl >= f.emessaIl, {
    message: 'la scadenza non può precedere l emissione',
    path: ['scadeIl'],
  })
  .transform((f) => ({
    ...f,
    totaleCentesimi: f.righe.reduce(
      (somma, r) => somma + r.quantita * r.prezzoUnitarioCentesimi,
      0,
    ),
  }))

type Fattura = z.infer<typeof SchemaFattura>

const SchemaRispostaElenco = z.object({
  elementi: z.array(SchemaFattura),
  totale: z.number().int().nonnegative(),
  pagina: z.number().int().positive(),
})

async function recuperaFatture(pagina = 1): Promise<z.infer<typeof SchemaRispostaElenco>> {
  const risposta = await fetch(`/api/fatture?pagina=${pagina}`)

  if (!risposta.ok) {
    throw new Error(`${risposta.status} ${risposta.statusText}`)
  }

  const grezzo: unknown = await risposta.json()
  const esito = SchemaRispostaElenco.safeParse(grezzo)

  if (!esito.success) {
    // L'errore dice ESATTAMENTE quale campo e perché
    console.error('Risposta non conforme:', esito.error.issues)
    throw new Error(
      `Il server ha restituito dati non validi: ${esito.error.issues
        .map((i) => `${i.path.join('.')}: ${i.message}`)
        .join('; ')}`,
    )
  }

  return esito.data
}

// ── 2. LOCALSTORAGE ──────────────────────────────────────────

const SchemaPreferenze = z.object({
  tema: z.enum(['chiaro', 'scuro', 'sistema']).catch('sistema'),
  righePerPagina: z.number().int().min(10).max(200).catch(50),
  colonneVisibili: z.array(z.string()).catch(['numero', 'importo', 'stato']),
  ultimaVisita: z.coerce.date().optional().catch(undefined),
})

type Preferenze = z.infer<typeof SchemaPreferenze>

/**
 * .catch() dà un valore di ripiego per campo invece di far
 * fallire tutto: una preferenza corrotta non deve impedire
 * l'avvio dell'applicazione.
 */
function leggiPreferenze(): Preferenze {
  try {
    const grezzo = localStorage.getItem('preferenze')
    if (!grezzo) return SchemaPreferenze.parse({})

    return SchemaPreferenze.parse(JSON.parse(grezzo))
  } catch {
    // JSON malformato, o localStorage non disponibile
    return SchemaPreferenze.parse({})
  }
}

function salvaPreferenze(preferenze: Preferenze): void {
  try {
    localStorage.setItem('preferenze', JSON.stringify(preferenze))
  } catch (errore) {
    console.warn('Preferenze non salvate', errore)
  }
}

// ── 3. QUERY STRING ──────────────────────────────────────────

const SchemaFiltri = z.object({
  // I parametri dell'URL sono SEMPRE stringhe: coerce li converte
  pagina: z.coerce.number().int().positive().default(1),
  perPagina: z.coerce.number().int().min(10).max(100).default(50),
  stato: z.enum(['bozza', 'emessa', 'pagata', 'annullata']).optional(),
  cliente: z.string().min(1).max(100).optional(),
  daData: z.coerce.date().optional(),
  aData: z.coerce.date().optional(),
  ordine: z.enum(['numero', '-numero', 'importo', '-importo']).default('-numero'),
})

type Filtri = z.infer<typeof SchemaFiltri>

function leggiFiltriDaUrl(url: URL): Filtri {
  const grezzi = Object.fromEntries(url.searchParams)

  const esito = SchemaFiltri.safeParse(grezzi)

  if (!esito.success) {
    // Un URL manipolato non deve rompere la pagina:
    // si torna ai valori predefiniti
    console.warn('Parametri non validi, uso i predefiniti', esito.error.issues)
    return SchemaFiltri.parse({})
  }

  return esito.data
}

function scriviFiltriInUrl(filtri: Filtri): URLSearchParams {
  const parametri = new URLSearchParams()

  for (const [chiave, valore] of Object.entries(filtri)) {
    if (valore === undefined) continue
    parametri.set(chiave, valore instanceof Date ? valore.toISOString() : String(valore))
  }

  return parametri
}
```

```typescript
// Test dei tre punti di ingresso
const url = new URL('https://esempio.it/fatture?pagina=2&stato=pagata&perPagina=25')
const filtri = leggiFiltriDaUrl(url)
console.log(filtri)

const urlManipolato = new URL('https://esempio.it/fatture?pagina=-5&stato=inventato')
const filtriSicuri = leggiFiltriDaUrl(urlManipolato)
console.log(filtriSicuri)
```

```
# Output atteso:
{ pagina: 2, perPagina: 25, stato: 'pagata', ordine: '-numero' }
{ pagina: 1, perPagina: 50, ordine: '-numero' }
```

```
# Le tre strategie, e quando usare quale:
#
# .parse()      solleva. Per i dati che DEVONO essere corretti:
#               la configurazione all'avvio, la risposta di
#               un'API interna. Fallire subito è meglio che
#               proseguire con dati insensati.
#
# .safeParse()  restituisce { success, data | error }. Per i
#               dati che possono legittimamente essere sbagliati:
#               input dell'utente, API di terze parti.
#
# .catch()      valore di ripiego per campo. Per i dati non
#               critici dove un valore predefinito è meglio
#               di un fallimento: preferenze, cache locale.
#
# .strict() sull'oggetto è una scelta di sicurezza: senza,
# i campi non dichiarati vengono SCARTATI in silenzio.
# Con .strict(), un campo inatteso è un errore — utile per
# accorgersi che l'API è cambiata.
#
# z.coerce è indispensabile per query string e form, dove
# tutto arriva come stringa: coerce.number() converte '2' in 2
# e poi applica i controlli.
#
# LA REGOLA:
#   uno schema per ogni punto di ingresso, e il tipo derivato
#   con z.infer. Dichiarare il tipo a mano ACCANTO allo schema
#   crea due fonti che divergeranno.
```

---

### Esercizio 7 — Da JavaScript a TypeScript, un file alla volta

**Obiettivo:** convertire un modulo JavaScript esistente senza riscriverlo, e senza `any`.

```javascript
// PARTENZA — src/carrello.js
export function creaCarrello() {
  const righe = []

  return {
    aggiungi(prodotto, quantita) {
      const esistente = righe.find((r) => r.prodotto.id === prodotto.id)
      if (esistente) {
        esistente.quantita += quantita
      } else {
        righe.push({ prodotto, quantita })
      }
    },

    rimuovi(prodottoId) {
      const indice = righe.findIndex((r) => r.prodotto.id === prodottoId)
      if (indice !== -1) righe.splice(indice, 1)
    },

    totale() {
      return righe.reduce((s, r) => s + r.prodotto.prezzo * r.quantita, 0)
    },

    get righe() {
      return [...righe]
    },
  }
}
```

```typescript
// SOLUZIONE — src/carrello.ts

/** Il denaro in centesimi interi: mai in virgola mobile. */
type Centesimi = number & { readonly __marchio: 'Centesimi' }

export interface Prodotto {
  readonly id: string
  readonly nome: string
  readonly prezzoCentesimi: Centesimi
  readonly disponibile: boolean
}

export interface RigaCarrello {
  readonly prodotto: Prodotto
  readonly quantita: number
}

export interface Carrello {
  aggiungi(prodotto: Prodotto, quantita?: number): void
  rimuovi(prodottoId: string): boolean
  imposta(prodottoId: string, quantita: number): boolean
  svuota(): void
  readonly righe: readonly RigaCarrello[]
  readonly totaleCentesimi: Centesimi
  readonly numeroArticoli: number
}

export class ErroreCarrello extends Error {
  constructor(
    messaggio: string,
    readonly codice: 'QUANTITA_NON_VALIDA' | 'PRODOTTO_NON_DISPONIBILE' | 'RIGA_ASSENTE',
  ) {
    super(messaggio)
    this.name = 'ErroreCarrello'
  }
}

export function creaCarrello(righeIniziali: readonly RigaCarrello[] = []): Carrello {
  // Una Map invece di un array: la ricerca per id è O(1)
  const righe = new Map<string, RigaCarrello>(
    righeIniziali.map((r) => [r.prodotto.id, r]),
  )

  function verificaQuantita(quantita: number): void {
    if (!Number.isInteger(quantita) || quantita < 1) {
      throw new ErroreCarrello(
        `La quantità deve essere un intero positivo, ricevuto ${quantita}`,
        'QUANTITA_NON_VALIDA',
      )
    }
  }

  return {
    aggiungi(prodotto, quantita = 1) {
      verificaQuantita(quantita)

      if (!prodotto.disponibile) {
        throw new ErroreCarrello(
          `Il prodotto ${prodotto.nome} non è disponibile`,
          'PRODOTTO_NON_DISPONIBILE',
        )
      }

      const esistente = righe.get(prodotto.id)

      righe.set(prodotto.id, {
        prodotto,
        quantita: (esistente?.quantita ?? 0) + quantita,
      })
    },

    rimuovi(prodottoId) {
      return righe.delete(prodottoId)
    },

    imposta(prodottoId, quantita) {
      const esistente = righe.get(prodottoId)
      if (!esistente) return false

      if (quantita === 0) {
        righe.delete(prodottoId)
        return true
      }

      verificaQuantita(quantita)
      righe.set(prodottoId, { ...esistente, quantita })
      return true
    },

    svuota() {
      righe.clear()
    },

    get righe() {
      return [...righe.values()]
    },

    get totaleCentesimi() {
      let totale = 0
      for (const riga of righe.values()) {
        totale += riga.prodotto.prezzoCentesimi * riga.quantita
      }
      return totale as Centesimi
    },

    get numeroArticoli() {
      let totale = 0
      for (const riga of righe.values()) {
        totale += riga.quantita
      }
      return totale
    },
  }
}
```

```
# Cosa la conversione ha fatto emergere:
#
# 1. UNA MUTAZIONE NASCOSTA.
#    L'originale faceva  esistente.quantita += quantita
#    modificando l'oggetto nell'array. Con readonly, il
#    compilatore lo rifiuta e costringe a creare una riga nuova.
#
# 2. LA RICERCA LINEARE.
#    find() e findIndex() su ogni operazione sono O(n).
#    Passando a Map, diventano O(1). Non è la conversione
#    ad averlo imposto, ma riscrivere le firme fa
#    guardare il codice con attenzione.
#
# 3. I CASI LIMITE NON GESTITI.
#    Quantità zero, negativa o decimale? Prodotto non
#    disponibile? L'originale li accettava in silenzio.
#
# 4. IL DENARO IN VIRGOLA MOBILE.
#    prodotto.prezzo era un float: su un carrello con molte
#    righe gli arrotondamenti divergono. Centesimi interi
#    più il brand eliminano il problema.
#
# 5. IL VALORE DI RITORNO MANCANTE.
#    rimuovi() non diceva se aveva rimosso qualcosa.
#    Dichiarando il tipo di ritorno, la domanda emerge.
#
# LA PROCEDURA DI CONVERSIONE, in ordine:
#
#   1. Rinomina .js in .ts. Guarda quanti errori compaiono.
#   2. Dichiara le INTERFACCE dei dati per primi:
#      è lì che sta il valore.
#   3. Annota le firme pubbliche del modulo.
#   4. Lascia che l'inferenza faccia il resto all'interno.
#   5. Ogni errore è una domanda legittima: rispondi
#      correggendo il codice, non aggiungendo 'any'.
#   6. Dove serve davvero una via d'uscita, usa 'unknown'
#      con un type guard, o '@ts-expect-error' con un
#      commento che spiega perché — mai '@ts-ignore', che
#      resta anche quando l'errore sparisce.
```

---

## C2. Mini-progetto: la todo-list convertita a TypeScript

L'esercizio chiave del modulo: riprendere la todo-list scritta in JavaScript vanilla in `tutorial_04_javascript_fondamenti.md` e convertirla a TypeScript con interfacce rigorose e generics.

### Cosa deve cambiare, e cosa no

```
Il COMPORTAMENTO deve restare identico. Cambiano:

  · lo stato modellato come discriminated union
  · uno store generico riusabile, non specifico per le attività
  · gli identificativi con branded type
  · la persistenza validata con Zod: localStorage non è fidato
  · gli eventi del DOM tipizzati, senza 'as'
  · zero 'any' nel progetto, verificato dal linter
```

### Struttura

```
todo-ts/
├── index.html
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── main.ts          composizione e collegamento degli eventi
    ├── tipi.ts          i tipi del dominio
    ├── store.ts         lo store generico
    ├── persistenza.ts   Zod e localStorage
    ├── vista.ts         il rendering
    └── dom.ts           gli aiutanti tipizzati per il DOM
```

### `src/tipi.ts`

```typescript
// src/tipi.ts — il dominio, senza dipendenze

declare const marchio: unique symbol
export type Marchiato<T, M extends string> = T & { readonly [marchio]: M }

/** Un identificativo di attività, non confondibile con una stringa qualunque. */
export type IdAttivita = Marchiato<string, 'IdAttivita'>

export function idAttivita(grezzo: string): IdAttivita {
  if (grezzo.length === 0) {
    throw new TypeError('Identificativo vuoto')
  }
  return grezzo as IdAttivita
}

export function nuovoId(): IdAttivita {
  return crypto.randomUUID() as IdAttivita
}

export interface Attivita {
  readonly id: IdAttivita
  readonly testo: string
  readonly completata: boolean
  readonly creataIl: string // ISO 8601
  readonly completataIl: string | null
}

export const FILTRI = ['tutte', 'da-fare', 'completate'] as const
export type Filtro = (typeof FILTRI)[number]

export function eFiltro(valore: unknown): valore is Filtro {
  return typeof valore === 'string' && (FILTRI as readonly string[]).includes(valore)
}

/** Lo stato dell'applicazione. */
export interface StatoApp {
  readonly attivita: readonly Attivita[]
  readonly filtro: Filtro
  readonly ultimaEliminata: { readonly attivita: Attivita; readonly indice: number } | null
}

/**
 * Le azioni come discriminated union: ogni azione porta
 * esattamente i dati che le servono, e nessun altro.
 */
export type Azione =
  | { tipo: 'aggiungi'; testo: string }
  | { tipo: 'modifica'; id: IdAttivita; testo: string }
  | { tipo: 'commuta'; id: IdAttivita }
  | { tipo: 'elimina'; id: IdAttivita }
  | { tipo: 'annulla-eliminazione' }
  | { tipo: 'imposta-filtro'; filtro: Filtro }
  | { tipo: 'sposta'; id: IdAttivita; versoIndice: number }
  | { tipo: 'svuota-completate' }
```

### `src/store.ts`

```typescript
// src/store.ts — uno store generico, non specifico per le attività

/** Una funzione pura: dallo stato corrente e un'azione, il nuovo stato. */
export type Riduttore<S, A> = (stato: S, azione: A) => S

export type Ascoltatore<S> = (stato: S, precedente: S) => void

export interface Store<S, A> {
  readonly stato: S
  invia(azione: A): void
  iscriviti(ascoltatore: Ascoltatore<S>): () => void
  /** Legge una porzione dello stato, con il tipo dedotto. */
  seleziona<R>(selettore: (stato: S) => R): R
}

export interface OpzioniStore<S, A> {
  /** Eseguito dopo ogni azione: per la persistenza, i log, la telemetria. */
  readonly dopoOgniAzione?: (stato: S, azione: A, precedente: S) => void
}

export function creaStore<S, A>(
  riduttore: Riduttore<S, A>,
  statoIniziale: S,
  opzioni: OpzioniStore<S, A> = {},
): Store<S, A> {
  let stato = statoIniziale
  const ascoltatori = new Set<Ascoltatore<S>>()

  return {
    get stato() {
      return stato
    },

    invia(azione) {
      const precedente = stato
      stato = riduttore(stato, azione)

      // Se il riduttore ha restituito lo stesso oggetto,
      // nulla è cambiato: non si notifica
      if (Object.is(stato, precedente)) return

      opzioni.dopoOgniAzione?.(stato, azione, precedente)

      for (const ascoltatore of ascoltatori) {
        ascoltatore(stato, precedente)
      }
    },

    iscriviti(ascoltatore) {
      ascoltatori.add(ascoltatore)
      return () => {
        ascoltatori.delete(ascoltatore)
      }
    },

    seleziona(selettore) {
      return selettore(stato)
    },
  }
}
```

### `src/persistenza.ts`

```typescript
// src/persistenza.ts — il confine con l'esterno

import { z } from 'zod'
import { FILTRI, type Attivita, type IdAttivita, type StatoApp } from './tipi.js'

const CHIAVE = 'todo-ts:stato:v1'

const SchemaAttivita = z.object({
  id: z.string().min(1),
  testo: z.string().min(1).max(500),
  completata: z.boolean(),
  creataIl: z.string().datetime(),
  completataIl: z.string().datetime().nullable(),
})

const SchemaStatoSalvato = z.object({
  attivita: z.array(SchemaAttivita).max(1000),
  filtro: z.enum(FILTRI).catch('tutte'),
})

/**
 * localStorage NON è fidato: l'utente può modificarlo, e una
 * versione precedente dell'applicazione può averci scritto
 * una forma diversa. Va validato come qualunque dato esterno.
 */
export function caricaStato(): Pick<StatoApp, 'attivita' | 'filtro'> {
  try {
    const grezzo = localStorage.getItem(CHIAVE)
    if (grezzo === null) return { attivita: [], filtro: 'tutte' }

    const analizzato: unknown = JSON.parse(grezzo)
    const esito = SchemaStatoSalvato.safeParse(analizzato)

    if (!esito.success) {
      console.warn('Stato salvato non valido, si riparte da zero', esito.error.issues)
      return { attivita: [], filtro: 'tutte' }
    }

    return {
      // Il cast è sicuro: lo schema ha appena verificato la forma
      attivita: esito.data.attivita as readonly Attivita[],
      filtro: esito.data.filtro,
    }
  } catch (errore) {
    // JSON malformato, o localStorage non disponibile
    console.warn('Stato non leggibile', errore)
    return { attivita: [], filtro: 'tutte' }
  }
}

export function salvaStato(stato: Pick<StatoApp, 'attivita' | 'filtro'>): void {
  try {
    localStorage.setItem(
      CHIAVE,
      JSON.stringify({ attivita: stato.attivita, filtro: stato.filtro }),
    )
  } catch (errore) {
    // QuotaExceededError, o modalità privata su alcuni browser:
    // l'applicazione deve continuare a funzionare in memoria
    console.warn('Salvataggio non riuscito', errore)
  }
}
```

### `src/dom.ts`

```typescript
// src/dom.ts — aiutanti tipizzati, per evitare le assertion sparse

/** querySelector che solleva invece di restituire null. */
export function richiedi<E extends Element = HTMLElement>(
  selettore: string,
  contesto: ParentNode = document,
): E {
  const elemento = contesto.querySelector<E>(selettore)
  if (elemento === null) {
    throw new Error(`Elemento non trovato: ${selettore}`)
  }
  return elemento
}

/** Restringe un EventTarget al tipo atteso. */
export function eElemento<K extends keyof HTMLElementTagNameMap>(
  bersaglio: EventTarget | null,
  tag: K,
): bersaglio is HTMLElementTagNameMap[K] {
  return bersaglio instanceof HTMLElement && bersaglio.tagName.toLowerCase() === tag
}

/** closest tipizzato, per la delegazione degli eventi. */
export function antenato<E extends Element = HTMLElement>(
  bersaglio: EventTarget | null,
  selettore: string,
): E | null {
  if (!(bersaglio instanceof Element)) return null
  return bersaglio.closest<E>(selettore)
}

/** Sostituisce i caratteri che avrebbero significato nell'HTML. */
export function proteggi(testo: string): string {
  const sostituzioni: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }
  return testo.replace(/[&<>"']/g, (c) => sostituzioni[c] ?? c)
}

/**
 * addEventListener tipizzato che restituisce la funzione di pulizia.
 * Il tipo dell'evento è dedotto dal nome.
 */
export function ascolta<K extends keyof HTMLElementEventMap>(
  bersaglio: HTMLElement,
  tipo: K,
  gestore: (evento: HTMLElementEventMap[K]) => void,
  opzioni?: AddEventListenerOptions,
): () => void {
  bersaglio.addEventListener(tipo, gestore as EventListener, opzioni)
  return () => bersaglio.removeEventListener(tipo, gestore as EventListener)
}
```

### `src/main.ts`

```typescript
// src/main.ts — il riduttore e il collegamento

import { creaStore, type Riduttore } from './store.js'
import { caricaStato, salvaStato } from './persistenza.js'
import { antenato, ascolta, richiedi } from './dom.js'
import {
  eFiltro,
  idAttivita,
  nuovoId,
  type Attivita,
  type Azione,
  type StatoApp,
} from './tipi.js'

// ── Il riduttore: una funzione pura, esaustiva sulle azioni ──

const riduttore: Riduttore<StatoApp, Azione> = (stato, azione) => {
  switch (azione.tipo) {
    case 'aggiungi': {
      const testo = azione.testo.trim()
      if (testo === '') return stato // nessun cambiamento

      const nuova: Attivita = {
        id: nuovoId(),
        testo,
        completata: false,
        creataIl: new Date().toISOString(),
        completataIl: null,
      }

      return { ...stato, attivita: [...stato.attivita, nuova] }
    }

    case 'modifica': {
      const testo = azione.testo.trim()
      if (testo === '') return stato

      return {
        ...stato,
        attivita: stato.attivita.map((a) => (a.id === azione.id ? { ...a, testo } : a)),
      }
    }

    case 'commuta':
      return {
        ...stato,
        attivita: stato.attivita.map((a) =>
          a.id === azione.id
            ? {
                ...a,
                completata: !a.completata,
                completataIl: a.completata ? null : new Date().toISOString(),
              }
            : a,
        ),
      }

    case 'elimina': {
      const indice = stato.attivita.findIndex((a) => a.id === azione.id)
      const attivita = stato.attivita[indice]
      if (indice === -1 || attivita === undefined) return stato

      return {
        ...stato,
        attivita: stato.attivita.filter((a) => a.id !== azione.id),
        ultimaEliminata: { attivita, indice },
      }
    }

    case 'annulla-eliminazione': {
      const ultima = stato.ultimaEliminata
      if (ultima === null) return stato

      return {
        ...stato,
        attivita: stato.attivita.toSpliced(ultima.indice, 0, ultima.attivita),
        ultimaEliminata: null,
      }
    }

    case 'imposta-filtro':
      return { ...stato, filtro: azione.filtro }

    case 'sposta': {
      const da = stato.attivita.findIndex((a) => a.id === azione.id)
      const elemento = stato.attivita[da]
      if (da === -1 || elemento === undefined || da === azione.versoIndice) return stato

      const senza = stato.attivita.toSpliced(da, 1)
      const a = da < azione.versoIndice ? azione.versoIndice - 1 : azione.versoIndice

      return { ...stato, attivita: senza.toSpliced(a, 0, elemento) }
    }

    case 'svuota-completate':
      return { ...stato, attivita: stato.attivita.filter((a) => !a.completata) }

    default: {
      // Aggiungendo un'azione senza gestirla, QUESTA riga
      // diventa un errore di compilazione.
      const esaustivo: never = azione
      throw new Error(`Azione non gestita: ${JSON.stringify(esaustivo)}`)
    }
  }
}

// ── Lo store, con la persistenza come effetto collaterale ────

const salvato = caricaStato()

const store = creaStore<StatoApp, Azione>(
  riduttore,
  { ...salvato, ultimaEliminata: null },
  {
    dopoOgniAzione: (stato) => salvaStato(stato),
  },
)

// ── Il collegamento degli eventi, tutto delegato ─────────────

const radice = richiedi<HTMLElement>('#applicazione')
const annunci = richiedi<HTMLParagraphElement>('#annunci')

function annuncia(messaggio: string): void {
  annunci.textContent = ''
  requestAnimationFrame(() => {
    annunci.textContent = messaggio
  })
}

ascolta(radice, 'submit', (evento) => {
  const modulo = evento.target
  if (!(modulo instanceof HTMLFormElement) || modulo.id !== 'modulo-aggiunta') return

  evento.preventDefault()

  const campo = modulo.elements.namedItem('testo')
  if (!(campo instanceof HTMLInputElement)) return

  store.invia({ tipo: 'aggiungi', testo: campo.value })
  campo.value = ''
  campo.focus()
  annuncia('Attività aggiunta')
})

ascolta(radice, 'click', (evento) => {
  const comandoFiltro = antenato<HTMLButtonElement>(evento.target, '[data-filtro]')
  if (comandoFiltro) {
    const valore = comandoFiltro.dataset['filtro']
    if (eFiltro(valore)) {
      store.invia({ tipo: 'imposta-filtro', filtro: valore })
    }
    return
  }

  const comandoElimina = antenato<HTMLButtonElement>(evento.target, '.elimina')
  if (comandoElimina) {
    const riga = antenato<HTMLLIElement>(comandoElimina, '.attivita')
    const id = riga?.dataset['id']
    if (id !== undefined) {
      store.invia({ tipo: 'elimina', id: idAttivita(id) })
      annuncia('Attività eliminata. Puoi annullare.')
    }
    return
  }

  if (evento.target instanceof HTMLElement && evento.target.id === 'annulla') {
    store.invia({ tipo: 'annulla-eliminazione' })
    annuncia('Eliminazione annullata')
  }
})

ascolta(radice, 'change', (evento) => {
  const casella = evento.target
  if (!(casella instanceof HTMLInputElement) || !casella.classList.contains('completa')) return

  const riga = antenato<HTMLLIElement>(casella, '.attivita')
  const id = riga?.dataset['id']
  if (id !== undefined) {
    store.invia({ tipo: 'commuta', id: idAttivita(id) })
  }
})
```

### Verifica

```powershell
pnpm exec tsc --noEmit
pnpm dev
```

```json
// eslint.config.js — la regola che impedisce di barare
{
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unsafe-assignment": "error",
    "@typescript-eslint/no-unsafe-member-access": "error",
    "@typescript-eslint/no-unsafe-call": "error",
    "@typescript-eslint/no-unsafe-return": "error"
  }
}
```

```
# I controlli, in ordine:
#
# 1. ZERO ERRORI DI TIPO
#    pnpm exec tsc --noEmit deve passare senza output.
#
# 2. ZERO 'any'
#    grep -rn ": any\| as any" src/
#    Non deve trovare nulla. Le regole no-unsafe-* di
#    typescript-eslint intercettano anche gli 'any'
#    che arrivano dalle librerie.
#
# 3. L'ESAUSTIVITÀ FUNZIONA
#    Aggiungi { tipo: 'duplica'; id: IdAttivita } all'union
#    Azione e ricompila: il riduttore deve dare errore
#    sulla riga 'const esaustivo: never = azione'.
#    Se non lo dà, il pattern non è impostato correttamente.
#
# 4. IL BRANDED TYPE FUNZIONA
#    Prova  store.invia({ tipo: 'elimina', id: 'x' })
#    Deve dare errore: string non è IdAttivita.
#
# 5. LA PERSISTENZA È VALIDATA
#    In DevTools → Application → Local Storage, sostituisci
#    il valore con  {"attivita":"non un array"}  e ricarica.
#    L'applicazione deve ripartire vuota, con un avviso in
#    console e nessun errore non gestito.
#
# 6. IL COMPORTAMENTO È IDENTICO
#    Tutti i controlli di tutorial_04 devono continuare
#    a passare: tastiera, riordino, annullamento, due schede.
```

```
# Cosa la conversione ha aggiunto, oltre ai tipi:
#
#   discriminated union    gli stati e le azioni impossibili
#                          non sono rappresentabili
#   never nel default      aggiungere un'azione senza gestirla
#                          è un errore di COMPILAZIONE
#   store generico         creaStore<S, A> funziona per qualunque
#                          dominio: è riusabile fuori da questo progetto
#   branded type           un id di attività non si confonde
#                          con una stringa qualunque
#   Zod al confine         localStorage validato come qualunque
#                          dato esterno
#   readonly ovunque       le mutazioni accidentali sullo stato
#                          diventano errori
#   aiutanti del DOM       una assertion in dom.ts invece di
#                          venti 'as HTMLInputElement' sparse
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Programmazione a livello di tipi

Il sistema di tipi di TypeScript è Turing-completo: ci si può calcolare. La domanda giusta non è *se* si può, ma *quando* conviene.

### Ricorsione sui tipi

```typescript
/** Una tupla di N elementi: si costruisce ricorsivamente. */
type TuplaDi<N extends number, T = unknown, Acc extends T[] = []> = Acc['length'] extends N
  ? Acc
  : TuplaDi<N, T, [...Acc, T]>

type Tre = TuplaDi<3, string> // [string, string, string]

/** L'aritmetica sui tipi passa dalla lunghezza delle tuple. */
type Somma<A extends number, B extends number> = [
  ...TuplaDi<A>,
  ...TuplaDi<B>,
]['length'] extends infer N
  ? N
  : never

type Cinque = Somma<2, 3> // 5
```

```typescript
/** Invertire una tupla. */
type Inverti<T extends readonly unknown[]> = T extends readonly [
  infer Testa,
  ...infer Coda,
]
  ? [...Inverti<Coda>, Testa]
  : []

type Invertita = Inverti<[1, 2, 3]> // [3, 2, 1]

/** Unire le stringhe di una tupla con un separatore. */
type Unisci<
  T extends readonly string[],
  S extends string = ',',
> = T extends readonly [infer Testa extends string, ...infer Coda extends string[]]
  ? Coda['length'] extends 0
    ? Testa
    : `${Testa}${S}${Unisci<Coda, S>}`
  : ''

type Percorso = Unisci<['api', 'v1', 'utenti'], '/'> // 'api/v1/utenti'
```

### Un caso d'uso che vale la pena: le chiavi di traduzione

```typescript
const traduzioni = {
  comune: {
    salva: 'Salva',
    annulla: 'Annulla',
  },
  fatture: {
    titolo: 'Fatture',
    vuoto: 'Nessuna fattura',
    azioni: {
      emetti: 'Emetti',
      annulla: 'Annulla la fattura',
    },
  },
} as const

/** Tutte le chiavi foglia, come percorsi puntati. */
type ChiaviProfonde<T, Prefisso extends string = ''> = {
  [K in keyof T & string]: T[K] extends string
    ? `${Prefisso}${K}`
    : ChiaviProfonde<T[K], `${Prefisso}${K}.`>
}[keyof T & string]

type ChiaveTraduzione = ChiaviProfonde<typeof traduzioni>
// 'comune.salva' | 'comune.annulla' | 'fatture.titolo'
// | 'fatture.vuoto' | 'fatture.azioni.emetti' | 'fatture.azioni.annulla'

function t(chiave: ChiaveTraduzione): string {
  return chiave
    .split('.')
    .reduce<unknown>(
      (corrente, parte) => (corrente as Record<string, unknown>)[parte],
      traduzioni,
    ) as string
}

t('fatture.azioni.emetti') // ok
// t('fatture.azioni.emettti')  // ✗ il refuso è un errore di compilazione
// t('fatture')                  // ✗ non è una foglia
```

Qui il calcolo sui tipi paga: le chiavi di traduzione sono centinaia, cambiano spesso, e un refuso produce una stringa grezza a schermo che nessuno nota fino alla segnalazione di un utente.

### I limiti, che vanno conosciuti

```typescript
// 1. La profondità di ricorsione è limitata
// type Troppo = TuplaDi<10000>
//   ✗ Type instantiation is excessively deep and possibly infinite

// 2. Le union grandi esplodono combinatoriamente
type A = 'a' | 'b' | 'c' | 'd' | 'e'
type Coppie = `${A}-${A}` // 25 membri
type Terne = `${A}-${A}-${A}` // 125 membri
// Con dieci lettere e quattro posizioni: 10.000 membri,
// e il compilatore rallenta sensibilmente.

// 3. I messaggi d'errore diventano illeggibili
//    Un tipo calcolato su cinque livelli produce errori
//    di venti righe che nessuno riesce a interpretare.
```

```
Il criterio per decidere se vale la pena:

  ✅ SÌ quando
     · il tipo si deriva da dati che esistono già
       (le traduzioni, le rotte, uno schema)
     · l'alternativa è mantenere a mano due elenchi
       che divergeranno
     · l'errore che previene è silenzioso a runtime

  ❌ NO quando
     · serve solo a dimostrare che si può fare
     · rende i messaggi d'errore incomprensibili
     · un tipo scritto a mano sarebbe più chiaro
     · rallenta il compilatore in modo percepibile
```

---

## D2. Project reference e build incrementali

In un monorepo, ricompilare tutto a ogni modifica diventa insostenibile. I project reference permettono a TypeScript di trattare i pacchetti come unità separate, ricostruendo solo ciò che è cambiato.

```
mio-monorepo/
├── tsconfig.json              ← la radice: solo riferimenti
├── tsconfig.base.json         ← le opzioni condivise
├── packages/
│   ├── tipi/
│   │   ├── tsconfig.json
│   │   └── src/
│   └── utility/
│       ├── tsconfig.json      ← dipende da tipi
│       └── src/
└── apps/
    ├── web/
    │   └── tsconfig.json      ← dipende da tipi e utility
    └── api/
        └── tsconfig.json
```

```json
// tsconfig.base.json — le opzioni comuni
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "composite": true,
    "incremental": true
  }
}
```

```json
// packages/tipi/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist",
    "tsBuildInfoFile": "dist/.tsbuildinfo"
  },
  "include": ["src"]
}
```

```json
// packages/utility/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"],
  "references": [{ "path": "../tipi" }]
}
```

```json
// tsconfig.json — la radice non compila nulla, coordina
{
  "files": [],
  "references": [
    { "path": "packages/tipi" },
    { "path": "packages/utility" },
    { "path": "apps/web" },
    { "path": "apps/api" }
  ]
}
```

```powershell
# --build rispetta le dipendenze e ricostruisce solo il necessario
pnpm exec tsc --build

# In modalità continua
pnpm exec tsc --build --watch

# Ricostruire da zero
pnpm exec tsc --build --clean
pnpm exec tsc --build --force

# Vedere cosa verrebbe ricostruito, senza farlo
pnpm exec tsc --build --dry
```

```
Le tre opzioni che rendono possibile tutto questo:

  composite: true       obbliga a dichiarare rootDir, genera i .d.ts
                        e il file .tsbuildinfo. È il prerequisito
                        per essere referenziato da un altro progetto.

  declaration: true     produce i .d.ts, che sono ciò che gli altri
                        progetti consumano: non ricompilano il
                        sorgente, leggono le dichiarazioni.

  declarationMap: true  permette a "vai alla definizione" nell'editor
                        di saltare al SORGENTE invece che al .d.ts.
                        Senza, la navigazione nel monorepo è inutilizzabile.
```

```
Il guadagno, su un monorepo di media dimensione:

  senza project reference   ogni tsc --noEmit ricompila tutto: 45 s
  con, prima build          45 s
  con, dopo una modifica    3-6 s (solo il pacchetto toccato
                            e chi ne dipende)
```

---

## D3. Performance del compilatore

Su progetti grandi il type checking può passare da secondi a minuti. Le cause sono poche e identificabili.

### Misurare

```powershell
# I tempi per fase
pnpm exec tsc --noEmit --diagnostics

# La traccia dettagliata, per il profiling
pnpm exec tsc --noEmit --generateTrace traccia
# Poi si apre traccia/trace.json in chrome://tracing
```

```
# Output atteso di --diagnostics:
Files:                         1247
Lines of Library:             42891
Lines of Definitions:        184203   ← se è enorme, il problema
Lines of TypeScript:          38104     sono le dipendenze
Identifiers:                 412887
Symbols:                     287431
Types:                        94218   ← il numero che conta
Instantiations:             1284772   ← se è nell'ordine dei milioni,
Memory used:                642180K     ci sono generici troppo complessi
Check time:                   18.42s
Total time:                   24.91s
```

### Le cause tipiche, in ordine di frequenza

```typescript
// ── 1. Union enormi ─────────────────────────────────────────
// ❌ Un tipo che elenca centinaia di literal, spesso generato
type IconaSbagliata = 'freccia-su' | 'freccia-giu' /* ... altri 800 ... */

// ✅ Se serve solo la verifica, un branded type con un
//    costruttore validante costa molto meno
type Icona = string & { readonly __icona: true }
const ICONE = new Set(['freccia-su', 'freccia-giu' /* ... */])
function icona(nome: string): Icona {
  if (!ICONE.has(nome)) throw new Error(`Icona sconosciuta: ${nome}`)
  return nome as Icona
}

// ── 2. Conditional type ricorsivi profondi ──────────────────
// Ogni livello moltiplica il lavoro. Limitare la profondità
// con un contatore evita l'esplosione.
type PartialProfondoLimitato<T, P extends number = 5> = P extends 0
  ? T
  : T extends object
    ? { [K in keyof T]?: PartialProfondoLimitato<T[K], Decrementa<P>> }
    : T

type Decrementa<N extends number> = [never, 0, 1, 2, 3, 4, 5][N]

// ── 3. Intersezioni ripetute ────────────────────────────────
// ❌ A & B & C & D & ... valutato ogni volta
type Composto = TipoA & TipoB & TipoC & TipoD

// ✅ Appiattito una volta con un mapped type
type Prettify<T> = { [K in keyof T]: T[K] } & {}
type CompostoPiatto = Prettify<TipoA & TipoB & TipoC & TipoD>

// ── 4. Import di tipo che trascinano l'implementazione ──────
// ❌ Importa il modulo intero, e con lui la sua catena
import { type Utente } from './modulo-enorme.js'

// ✅ import type garantisce che sparisca alla compilazione
import type { Utente as U } from './modulo-enorme.js'
```

### Le opzioni che aiutano

```json
{
  "compilerOptions": {
    // Non verifica i .d.ts delle dipendenze: su un progetto
    // con molte librerie, dimezza il tempo. Il rischio è
    // non accorgersi di conflitti fra i tipi di due librerie.
    "skipLibCheck": true,

    // Riusa il lavoro fra le esecuzioni
    "incremental": true,
    "tsBuildInfoFile": "node_modules/.cache/tsbuildinfo",

    // Limita quali @types vengono inclusi: senza, li carica TUTTI
    // quelli presenti in node_modules
    "types": ["node", "vite/client"],

    // Ogni file è compilabile isolatamente: necessario con esbuild
    "isolatedModules": true
  },
  "exclude": ["node_modules", "dist", "coverage", "**/*.test.ts"]
}
```

```
La regola operativa:

  Il numero da guardare è 'Instantiations'.
  Sotto 500.000: normale.
  Fra 500.000 e 2 milioni: c'è margine di miglioramento.
  Oltre: c'è un generico che esplode, e --generateTrace
  dice quale.

  Prima di ottimizzare i tipi, verificare 'Lines of Definitions':
  se è dieci volte il proprio codice, il problema sono le
  dipendenze, non i tipi scritti in casa.
```

---

## D4. Migrare un progetto JavaScript

Una migrazione completa in un colpo solo fallisce: blocca lo sviluppo e produce una revisione impossibile da fare. La strategia che funziona è incrementale, e TypeScript la supporta esplicitamente.

### Fase 1 — Convivenza, senza convertire nulla

```json
// tsconfig.json — la configurazione permissiva di partenza
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",

    // Accetta i file .js accanto ai .ts
    "allowJs": true,
    // Ma non li verifica ancora
    "checkJs": false,

    // Tutto disattivato all'inizio
    "strict": false,
    "noImplicitAny": false,

    "noEmit": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

```powershell
# Deve passare senza errori: se non passa, c'è un problema
# di configurazione, non di tipi
pnpm exec tsc --noEmit
```

Questo primo passo non cambia niente e non deve trovare errori. Serve solo a mettere TypeScript nella pipeline.

### Fase 2 — Tipi dai commenti, senza rinominare

```javascript
// src/carrello.js — JSDoc dà i tipi senza convertire il file

/**
 * @typedef {object} Prodotto
 * @property {string} id
 * @property {string} nome
 * @property {number} prezzoCentesimi
 */

/**
 * @typedef {object} RigaCarrello
 * @property {Prodotto} prodotto
 * @property {number} quantita
 */

/**
 * @param {readonly RigaCarrello[]} righe
 * @returns {number}
 */
export function calcolaTotale(righe) {
  return righe.reduce((s, r) => s + r.prodotto.prezzoCentesimi * r.quantita, 0)
}

/** @type {Map<string, Prodotto>} */
const catalogo = new Map()
```

```json
// Attivare la verifica dei .js, un file alla volta
{
  "compilerOptions": {
    "checkJs": true
  }
}
```

```javascript
// Oppure per singolo file, con un commento in cima
// @ts-check
```

JSDoc è la via meno invasiva: nessun file rinominato, nessun passo di build nuovo, e i tipi sono già utili nell'editor. Su progetti che non possono permettersi una conversione, è un punto d'arrivo accettabile.

### Fase 3 — Conversione, dai file foglia

```
L'ordine che funziona:

  1. I file SENZA dipendenze interne (utility, costanti, tipi)
  2. I moduli di dominio che dipendono solo da quelli
  3. I servizi
  4. I componenti dell'interfaccia
  5. Il punto d'ingresso

Convertire dall'alto produce cascate di errori in file
non ancora convertiti. Dal basso, ogni file convertito
migliora i tipi di chi lo usa.
```

```powershell
# Trovare i file senza dipendenze interne
pnpm dlx madge --orphans src/
```

```typescript
// Durante la conversione, la via d'uscita ONESTA

// ❌ @ts-ignore: silenzia, e resta anche quando l'errore sparisce
// @ts-ignore
const x = qualcosaDiRotto()

// ✅ @ts-expect-error: silenzia, MA diventa un errore quando
//    l'errore sottostante viene corretto. Si autopulisce.
// @ts-expect-error — la libreria non ha i tipi, in attesa di @types/x
const y = qualcosaDiRotto()
```

### Fase 4 — Stringere i flag, uno alla volta

```
L'ordine in cui accenderli, dal meno al più invasivo:

  1. noImplicitAny            costringe ad annotare i parametri
  2. strictNullChecks         il salto più grande, e il più utile
  3. strictFunctionTypes
  4. strictBindCallApply
  5. strictPropertyInitialization
  6. noImplicitThis
  7. useUnknownInCatchVariables
  8. alwaysStrict
  → poi "strict": true, che li racchiude tutti
  9. noUncheckedIndexedAccess  (il più scomodo, va per ultimo)
```

`strictNullChecks` è quello che produce più errori e che vale di più: intercetta l'intera famiglia dei `Cannot read properties of undefined`. Su un progetto grande può produrre migliaia di errori il primo giorno — è normale, e vanno affrontati per cartelle.

### Misurare l'avanzamento

```javascript
// scripts/avanzamento-migrazione.js
// Uso: node scripts/avanzamento-migrazione.js

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, extname } from 'node:path'

const IGNORA = new Set(['node_modules', 'dist', '.git', 'coverage'])

function scansiona(percorso, esito = { ts: [], js: [], jsConCheck: [], any: 0, ignore: 0 }) {
  for (const voce of readdirSync(percorso)) {
    if (IGNORA.has(voce)) continue

    const completo = join(percorso, voce)

    if (statSync(completo).isDirectory()) {
      scansiona(completo, esito)
      continue
    }

    const estensione = extname(voce)
    if (!['.ts', '.tsx', '.js', '.jsx'].includes(estensione)) continue

    const testo = readFileSync(completo, 'utf8')

    // Gli 'any' espliciti e i silenziamenti sono il debito residuo
    esito.any += (testo.match(/:\s*any\b|<any>|as any\b/g) ?? []).length
    esito.ignore += (testo.match(/@ts-ignore/g) ?? []).length

    if (estensione === '.ts' || estensione === '.tsx') {
      esito.ts.push(completo)
    } else if (testo.includes('@ts-check')) {
      esito.jsConCheck.push(completo)
    } else {
      esito.js.push(completo)
    }
  }
  return esito
}

const esito = scansiona('src')
const totale = esito.ts.length + esito.js.length + esito.jsConCheck.length
const percentuale = (n) => ((n / totale) * 100).toFixed(0)

console.log('Avanzamento della migrazione\n')
console.log(`  TypeScript:      ${String(esito.ts.length).padStart(4)}  ${percentuale(esito.ts.length)}%`)
console.log(`  JS con @ts-check:${String(esito.jsConCheck.length).padStart(4)}  ${percentuale(esito.jsConCheck.length)}%`)
console.log(`  JavaScript:      ${String(esito.js.length).padStart(4)}  ${percentuale(esito.js.length)}%`)

console.log(`\nDebito residuo:`)
console.log(`  'any' espliciti: ${esito.any}`)
console.log(`  @ts-ignore:      ${esito.ignore}`)

if (esito.js.length > 0) {
  console.log('\nProssimi candidati (senza @ts-check):')
  for (const percorso of esito.js.slice(0, 10)) console.log(`  ${percorso}`)
}
```

```
# Output atteso a metà migrazione:
Avanzamento della migrazione

  TypeScript:        87  62%
  JS con @ts-check:  31  22%
  JavaScript:        22  16%

Debito residuo:
  'any' espliciti: 43
  @ts-ignore:      7

Prossimi candidati (senza @ts-check):
  src/legacy/importazione.js
  src/utility/formattazione.js
  ...
```

```
# La metrica che conta NON è la percentuale di file convertiti:
# è il numero di 'any' e di @ts-ignore.
#
# Un progetto al 100% TypeScript con duecento 'any' sparsi
# ha gli stessi bug di uno in JavaScript, più il costo
# della compilazione. La conversione ha valore solo se
# i tipi dicono la verità.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
TYPESCRIPT — Mappa dei concetti

IL PRINCIPIO
└── I tipi esistono SOLO a tempo di build, poi spariscono.
    → non proteggono dai dati esterni: serve Zod al confine.

INFERENZA
├── const → literal ('bozza')   ·   let → allargato (string)
├── Annota: parametri, firme pubbliche, variabili vuote
└── Non annotare: variabili inizializzate, ritorni ovvi

I TIPI
├── union A | B          uno dei due; usabili solo i membri comuni
├── intersection A & B   tutte le proprietà
├── literal              'GET' | 'POST' — meglio degli enum
│     └── as const su un array + (typeof X)[number]
├── tuple                [number, number], con etichette
└── index signature      Record<K, V>

any / unknown / never / void
├── any      spegne il controllo, e si propaga
├── unknown  "verifica prima di usare" ← per tutto ciò che viene da fuori
├── never    "non può accadere" ← esaustività
└── void     "il ritorno non serve"

STRUTTURALE
├── Conta la FORMA, non il nome: due tipi uguali sono intercambiabili
├── Il controllo delle proprietà in eccesso scatta solo sui LETTERALI
└── branded type per rendere nominale ciò che serve
      identificativi · unità di misura · valori già validati

NARROWING
├── typeof · instanceof · in · truthiness · uguaglianza
├── DISCRIMINATED UNION ← il pattern centrale
│     una proprietà literal distingue le varianti
│     rende IMPOSSIBILI da rappresentare gli stati insensati
│     + never nel default = esaustività verificata
├── type predicate    x is T   ← è una PROMESSA: se mente, mente
├── assertion         asserts x is T ← richiede annotazione esplicita
└── Si perde dopo una chiamata di funzione e nelle closure su let
      → estrarre in una const locale

GENERICS
├── <T> conserva il legame fra ingresso e uscita
├── extends vincola e sblocca le proprietà
├── keyof T + T[K] → accessori tipizzati
└── NoInfer<T> esclude un parametro dall'inferenza

UTILITY TYPE
├── Sono mapped e conditional type: si possono riscrivere in tre righe
├── [K in keyof T]  con i modificatori  ?  -?  readonly  -readonly
├── T extends U ? A : B, DISTRIBUTIVO su T generico nudo
│     → [T] extends [U] disattiva la distribuzione
├── infer dichiara una variabile di tipo dentro la condizione
└── Prettify<T> per rendere leggibili gli errori

as const / satisfies / as
├── as const     literal + readonly, in profondità
├── satisfies    VERIFICA senza perdere l'inferenza precisa
├── : Tipo       IMPONE il tipo, e perde la precisione
└── as           "fidati": nessuna verifica. Legittimo solo per
                 brand, querySelector e mock

CONFIGURAZIONE
├── strict: true → otto flag, il più importante strictNullChecks
├── noUncheckedIndexedAccess → array[i] è T | undefined (la verità)
├── exactOptionalPropertyTypes → { x: undefined } ≠ {}
├── verbatimModuleSyntax → import type esplicito
└── Vite NON verifica i tipi: serve tsc --noEmit nella build

DICHIARAZIONI
├── .d.ts per i moduli senza tipi e le risorse (*.svg, *.css)
├── declare global richiede un export nel file
└── module augmentation per estendere i tipi di libreria

IL CONFINE
└── Zod: lo schema esiste a runtime, il tipo si deriva con z.infer
      parse solleva · safeParse restituisce · catch dà un ripiego
      .strict() per accorgersi che l'API è cambiata
      z.coerce per query string e form
      → valida al CONFINE, fidati all'INTERNO
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai che i tipi spariscono alla compilazione, e cosa comporta
- [ ] Sai dove annotare e dove lasciare fare all'inferenza
- [ ] Sai perché `const` inferisce un literal e `let` no
- [ ] Sai perché Vite da solo non basta e serve `tsc --noEmit`
- [ ] Usi le union di literal invece degli `enum`, e sai perché
- [ ] Sai cosa fa `noUncheckedIndexedAccess` e perché la scomodità è voluta
- [ ] Sai perché il controllo delle proprietà in eccesso scatta solo sui letterali
- [ ] Distingui i casi in cui serve `interface` da quelli in cui serve `type`
- [ ] Sai perché `unknown` è quasi sempre preferibile ad `any`
- [ ] Usi `never` per verificare l'esaustività di uno switch

**Parte B — Comprensione**

- [ ] Sai cosa significa che il sistema di tipi è strutturale
- [ ] Costruisci un branded type e sai quando ne vale la pena
- [ ] Sai perché i metodi sono bivarianti e le proprietà funzione no
- [ ] Modelli uno stato con una discriminated union invece di campi opzionali
- [ ] Scrivi un type predicate e sai che il compilatore si fida
- [ ] Sai perché il narrowing si perde nelle closure su `let`
- [ ] Usi `keyof` e `T[K]` per un accessore generico tipizzato
- [ ] Sai riscrivere `Partial`, `Pick`, `Omit` ed `Exclude` da zero
- [ ] Sai cos'è la distributività dei conditional type e come disattivarla
- [ ] Usi `infer`, anche in posizione ricorsiva
- [ ] Sai quando usare `satisfies` invece dell'annotazione
- [ ] Conosci gli otto flag di `strict` e cosa fa ciascuno
- [ ] Sai a cosa serve `exactOptionalPropertyTypes`
- [ ] Estendi i tipi globali con `declare global` e sai perché serve un export
- [ ] Validi i dati esterni con Zod e derivi il tipo con `z.infer`
- [ ] Sai quando usare `parse`, `safeParse` e `catch`

**Parte C — Pratica**

- [ ] Hai sostituito un tipo con campi opzionali con una discriminated union
- [ ] Hai scritto gli utility type da zero e capito i due meccanismi
- [ ] Hai costruito il client API in cui la risposta si deduce dall'endpoint
- [ ] Hai applicato i branded type a identificativi e denaro
- [ ] Hai validato i tre punti di ingresso con Zod
- [ ] Hai convertito la todo-list senza usare `any`

**Parte D — Esperto**

- [ ] Sai calcolare un tipo ricorsivo e conosci i limiti di profondità
- [ ] Sai quando il calcolo sui tipi vale la pena e quando no
- [ ] Sai configurare i project reference e a cosa serve `composite`
- [ ] Sai perché `declarationMap` è necessario in un monorepo
- [ ] Leggi l'output di `--diagnostics` e sai quale numero guardare
- [ ] Conosci le quattro cause tipiche di lentezza del compilatore
- [ ] Sai in che ordine convertire i file di un progetto JavaScript
- [ ] Sai perché `@ts-expect-error` è preferibile a `@ts-ignore`
- [ ] Sai qual è la metrica reale di una migrazione

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `any` per far passare il compilatore | Spegne il controllo e si propaga a tutto ciò che ne deriva | `unknown` con un type guard |
| `Promise<Utente>` su una risposta di rete | È una promessa non verificata: il tipo mente | Validare con Zod al confine |
| `as` per convertire un tipo | Nessuna verifica: l'errore emerge a runtime | Type predicate, o validazione |
| `as unknown as X` | Forza qualunque cosa: segnala un problema di modellazione a monte | Rimodellare il tipo |
| `@ts-ignore` | Resta anche quando l'errore sparisce, nascondendo regressioni | `@ts-expect-error` con un commento |
| Campi opzionali per rappresentare uno stato | Ammette combinazioni impossibili | Discriminated union |
| `switch` senza il caso `never` | Aggiungere una variante non produce alcun errore | `const esaustivo: never = valore` |
| `enum` di TypeScript | Genera codice a runtime, non è cancellabile, mal si integra con JSON | Union di literal, o `as const` |
| Annotare ogni variabile | Rumore, e a volte peggiora l'inferenza | Annotare parametri e firme pubbliche |
| `: Tipo` dove serviva `satisfies` | Perde l'inferenza precisa e ammette chiavi in più | `satisfies` |
| `interface` con lo stesso nome, per sbaglio | Il merging le fonde in silenzio | `type`, che dà errore sui duplicati |
| Tipo dichiarato accanto allo schema Zod | Due fonti che divergeranno | `z.infer<typeof Schema>` |
| Validare gli stessi dati più volte | Rumore, e nasconde dove sta il vero confine | Validare una volta, all'ingresso |
| `Omit` con una chiave inesistente | Non dà errore: il refuso passa in silenzio | Un `OmitSicuro<T, K extends keyof T>` |
| Generici ricorsivi senza limite di profondità | Il compilatore esplode o rallenta | Limitare con un contatore |
| Union di centinaia di literal | Rallenta il compilatore in modo percepibile | Branded type con validazione a runtime |
| `skipLibCheck: false` senza motivo | Verifica i `.d.ts` di ogni dipendenza: raddoppia i tempi | `true`, salvo conflitti da diagnosticare |
| Convertire un progetto dall'alto verso il basso | Cascate di errori in file non ancora convertiti | Partire dai file foglia |
| Migrazione misurata in percentuale di file | Un progetto tutto `.ts` pieno di `any` non è migrato | Contare gli `any` e i `@ts-ignore` |
| `tsc` assente dalla pipeline di build | Vite rimuove i tipi senza verificarli: l'errore va in produzione | `tsc --noEmit && vite build` |

---

## Troubleshooting rapido

**`Object is possibly 'null' or 'undefined'`**
- Causa: `strictNullChecks` fa il suo lavoro — il valore può davvero essere assente
- Fix: `?.`, `??`, un `if` di guardia, o `!` **solo** se sei certo e puoi spiegare perché

**`Property 'x' does not exist on type 'never'`**
- Causa: il narrowing ha escluso tutte le varianti — spesso una `if` di troppo, o uno switch già esaustivo
- Fix: rileggere la catena di condizioni; è quasi sempre logica sbagliata, non un problema di tipi

**`Type 'string' is not assignable to type '"a" | "b"'`**
- Causa: una `let`, o una proprietà di oggetto, inferita come `string`
- Fix: annotare il tipo, oppure `as const`

**`Argument of type 'X' is not assignable to parameter of type 'Y'` su tipi identici**
- Causa: due dichiarazioni distinte dello stesso tipo — spesso due copie di una libreria in `node_modules`
- Fix: `pnpm why <pacchetto>`; deduplicare con un `override`

**`Object literal may only specify known properties`**
- Causa: il controllo delle proprietà in eccesso sui letterali
- Fix: rimuovere la proprietà se è un refuso; passare da una variabile se è voluta

**`Type instantiation is excessively deep and possibly infinite`**
- Causa: un tipo ricorsivo senza caso base raggiungibile, o troppo profondo
- Fix: limitare la profondità con un contatore; semplificare il tipo

**`Cannot find module 'x' or its corresponding type declarations`**
- Causa: mancano i tipi della libreria
- Fix: `pnpm add -D @types/x`; se non esistono, un `declare module 'x'` in un `.d.ts`

**`This expression is not callable. Type has no call signatures`**
- Causa: quasi sempre un import di default da un modulo CommonJS senza `esModuleInterop`
- Fix: `"esModuleInterop": true`, oppure `import * as x`

**Il tipo è corretto nell'editor ma `tsc` dà errore**
- Causa: l'editor usa una versione di TypeScript diversa da quella del progetto
- Fix: in VS Code, `TypeScript: Select TypeScript Version` → *Use Workspace Version*, e `"typescript.tsdk": "node_modules/typescript/lib"` nelle impostazioni del progetto

**`declare global` dà "Augmentations for the global scope..."**
- Causa: il file non è un modulo
- Fix: aggiungere `export {}` in fondo

**Il narrowing sparisce dentro un callback**
- Causa: la variabile è `let`, o è una proprietà che potrebbe cambiare
- Fix: estrarre in una `const` locale prima del controllo

**`tsc` è lentissimo**
- Causa: `skipLibCheck` disattivato, `types` non limitato, o generici che esplodono
- Fix: `--diagnostics` e guardare `Instantiations`; `--generateTrace` per il dettaglio

**Zod non deduce il tipo che ti aspetti dopo `transform`**
- Causa: `z.infer` restituisce il tipo di **uscita**; l'ingresso è `z.input`
- Fix: `z.input<typeof Schema>` per il tipo prima della trasformazione

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_07_react.md` | Props e hook tipizzati, `PropsWithChildren`, generici nei componenti |
| `tutorial_10_nodejs.md` | TypeScript sul server: `tsx`, i tipi di Node, ESM |
| `tutorial_11_api_design.md` | Contratti condivisi fra client e server, tRPC, OpenAPI |
| `tutorial_12_database_web.md` | Prisma e Drizzle: tipi generati dallo schema del database |
| `tutorial_15_testing_web.md` | Testare i tipi con `expectTypeOf`, e i mock tipizzati |
| `tutorial_16_build_tools_deploy.md` | `tsc --noEmit` in CI, project reference nella pipeline |
| `tutorial_24_graphql.md` | Codegen: tipi generati dallo schema GraphQL |

---

## Risorse di riferimento

**Documentazione:**
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html) — il riferimento ufficiale
- [TSConfig Reference](https://www.typescriptlang.org/tsconfig) — ogni opzione, spiegata
- [TypeScript Playground](https://www.typescriptlang.org/play) — per provare un tipo senza un progetto
- [Zod](https://zod.dev/) — documentazione completa

**Approfondimenti:**
- [Type Challenges](https://github.com/type-challenges/type-challenges) — esercizi sui tipi, dal facile all'impossibile
- [Total TypeScript](https://www.totaltypescript.com/) — Matt Pocock, articoli e tips gratuiti
- [type-fest](https://github.com/sindresorhus/type-fest) — una raccolta di utility type pronti, e ottima da leggere
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/) — libro gratuito

**Strumenti:**
- [typescript-eslint](https://typescript-eslint.io/) — le regole che intercettano gli `any` impliciti
- [ts-reset](https://github.com/mattpocock/ts-reset) — corregge alcuni tipi troppo permissivi della libreria standard
- [madge](https://github.com/pahen/madge) — grafo delle dipendenze, per pianificare una migrazione
- [arethetypeswrong](https://arethetypeswrong.github.io/) — verifica che i tipi di un pacchetto siano pubblicati correttamente

---

> **Fine del Tutorial 06 — TypeScript**
>
> Prossimo tutorial: `tutorial_07_react.md`
