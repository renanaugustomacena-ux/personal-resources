---
corso: "Sviluppo Web"
fase: "2 — Linguaggi"
modulo: "06"
titolo: "TypeScript"
versione: "TypeScript 5.x"
livello: "Intermedio"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "05 — JavaScript Avanzato"
obiettivi:
  - "Padroneggiare il sistema di tipi: union, intersection, generics"
  - "Utilizzare utility types, conditional types e mapped types"
  - "Configurare tsconfig.json con strict mode"
  - "Integrare TypeScript con React, Node.js e build tools"
  - "Applicare pattern type-safe: discriminated union, branded types, zod"
  - "Migrare progressivamente un progetto JavaScript a TypeScript"
tag: [TypeScript, tipi, generics, utility-types, tsconfig, strict-mode, zod]
---

# TypeScript — Guida Completa

> **Modulo 06** · **Aggiornamento:** 2026-05-24 · **Versione:** TypeScript 5.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [JavaScript Avanzato](05-javascript-avanzato.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare il sistema di tipi: union, intersection, generics
> 2. Utilizzare utility types, conditional types e mapped types
> 3. Configurare `tsconfig.json` con strict mode
> 4. Integrare TypeScript con React, Node.js e build tools
> 5. Applicare pattern type-safe: discriminated union, branded types, zod
> 6. Migrare progressivamente un progetto JavaScript a TypeScript
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **`strict: true` mandatory, no opt-out.**
2. **`unknown` > `any`. Sempre.**
3. **Type narrowing > type assertion.** `as` antipattern.
4. **Discriminated union per state machine.**
5. **`satisfies` operator > type annotation per literal narrowing.**


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti](#fondamenti)
3. [Funzioni](#funzioni)
4. [Interfacce e Type Alias](#interfacce-e-type-alias)
5. [Generics](#generics)
6. [Classi](#classi)
7. [Moduli e Namespaces](#moduli-e-namespaces)
8. [Configurazione (tsconfig.json)](#configurazione-tsconfigjson)
9. [Pattern Avanzati](#pattern-avanzati)
10. [TypeScript con React](#typescript-con-react)
11. [TypeScript con Node.js](#typescript-con-nodejs)
12. [Best Practices](#best-practices)
13. [Novita TypeScript 5.4 / 5.5 / 5.6](#novita-typescript-54--55--56)
14. [Sistema di Tipi Avanzato — Approfondimento](#sistema-di-tipi-avanzato--approfondimento)
15. [Type Narrowing — Approfondimento](#type-narrowing--approfondimento)
16. [Generics Avanzati](#generics-avanzati)
17. [Utility Types — Approfondimento](#utility-types--approfondimento)
18. [File di Dichiarazione e Augmentation](#file-di-dichiarazione-e-augmentation)
19. [Compilatore: Project References e Build Incrementali](#compilatore-project-references-e-build-incrementali)
20. [Flag Strict Mode — Spiegazione Dettagliata](#flag-strict-mode--spiegazione-dettagliata)
21. [Pattern TypeScript con React — Approfondimento](#pattern-typescript-con-react--approfondimento)
22. [Validazione a Runtime: Zod, Valibot, ArkType](#validazione-a-runtime-zod-valibot-arktype)
23. [Performance del Compilatore](#performance-del-compilatore)
24. [Migrazione da JavaScript](#migrazione-da-javascript)

---

## Panoramica

### Cos'e TypeScript e Perche Esiste

TypeScript e un linguaggio di programmazione open-source sviluppato e mantenuto da Microsoft, il cui primo rilascio pubblico risale a ottobre 2012, frutto del lavoro di Anders Hejlsberg, lo stesso progettista di C# e Turbo Pascal. Si tratta di un **superset sintattico di JavaScript**: ogni programma JavaScript valido e anche un programma TypeScript valido, ma TypeScript aggiunge un potente sistema di tipi statici che viene verificato a tempo di compilazione.

La motivazione fondamentale dietro TypeScript nasce dalle limitazioni intrinseche di JavaScript quando viene utilizzato per sviluppare applicazioni di grandi dimensioni. JavaScript, essendo un linguaggio a tipizzazione dinamica, non offre alcun controllo sui tipi durante la fase di scrittura del codice. Questo significa che interi classi di errori — riferimenti a proprieta inesistenti, passaggio di argomenti del tipo sbagliato, operazioni su valori `null` o `undefined` — vengono scoperti solo a runtime, spesso in produzione. TypeScript risolve questo problema introducendo annotazioni di tipo opzionali e un compilatore che verifica la correttezza del codice prima che venga eseguito.

### TypeScript vs JavaScript

La differenza principale e il **sistema di tipi statici**. In JavaScript si puo scrivere:

```javascript
function somma(a, b) {
  return a + b;
}
somma("5", 3); // "53" — concatenazione, non somma
```

In TypeScript lo stesso errore viene intercettato dal compilatore:

```typescript
function somma(a: number, b: number): number {
  return a + b;
}
somma("5", 3); // Errore di compilazione: Argument of type 'string' is not assignable to parameter of type 'number'
```

Altre differenze significative includono il supporto nativo per interfacce, enum, generics, tuple e tipi avanzati come union, intersection e tipi condizionali. TypeScript offre inoltre un'esperienza di sviluppo superiore grazie all'autocompletamento intelligente, la navigazione nel codice e il refactoring assistito negli IDE moderni come Visual Studio Code.

E fondamentale comprendere che TypeScript non aggiunge funzionalita a runtime: tutto il sistema di tipi viene **completamente rimosso** durante la compilazione. Il codice che viene eseguito e puro JavaScript.

### Processo di Compilazione (tsc)

Il compilatore TypeScript, invocato tramite il comando `tsc`, trasforma il codice `.ts` in codice `.js`. Il processo si articola in diverse fasi:

1. **Parsing**: il codice sorgente viene analizzato e trasformato in un Abstract Syntax Tree (AST).
2. **Type checking**: l'AST viene analizzato per verificare la correttezza dei tipi.
3. **Emit**: il codice JavaScript viene generato rimuovendo tutte le annotazioni di tipo.

```bash
# Installazione globale
npm install -g typescript

# Compilazione di un singolo file
tsc app.ts

# Compilazione con file di configurazione
tsc --project tsconfig.json

# Modalita watch — ricompila automaticamente ai cambiamenti
tsc --watch
```

Il compilatore puo generare codice compatibile con diverse versioni di JavaScript (ES5, ES6, ES2020, ESNext) attraverso l'opzione `target` nel file di configurazione. Questo permette di utilizzare le funzionalita piu recenti del linguaggio mantenendo la compatibilita con ambienti di esecuzione meno recenti.

---

## Fondamenti

### Tipi Base

TypeScript mette a disposizione un insieme ricco di tipi primitivi che riflettono e ampliano quelli di JavaScript.

**string, number, boolean** — i tre tipi primitivi fondamentali:

```typescript
let nome: string = "Marco";
let eta: number = 28;
let attivo: boolean = true;

// number include interi, decimali, hex, octal, binary
let esadecimale: number = 0xff;
let binario: number = 0b1010;
let decimale: number = 3.14;
```

**null e undefined** — rappresentano rispettivamente l'assenza intenzionale di valore e un valore non ancora assegnato:

```typescript
let valoreMancante: null = null;
let nonDefinito: undefined = undefined;

// Con strictNullChecks attivo (raccomandato), null e undefined
// non sono assegnabili ad altri tipi senza union esplicita
let forse: string | null = null;
```

**void** — indica l'assenza di un valore di ritorno, tipicamente usato per funzioni che non restituiscono nulla:

```typescript
function saluta(nome: string): void {
  console.log(`Ciao, ${nome}!`);
}
```

**never** — rappresenta un tipo che non puo mai verificarsi. Viene utilizzato per funzioni che non terminano mai o per rami di codice irraggiungibili:

```typescript
function errore(messaggio: string): never {
  throw new Error(messaggio);
}

function cicloInfinito(): never {
  while (true) {
    // non termina mai
  }
}
```

**any** — disabilita completamente il controllo dei tipi. Qualsiasi operazione e permessa su un valore `any`. E fortemente sconsigliato il suo utilizzo perche annulla i benefici di TypeScript:

```typescript
let qualsiasi: any = "stringa";
qualsiasi = 42;
qualsiasi = true;
qualsiasi.metodoInesistente(); // nessun errore a compile-time
```

**unknown** — l'alternativa sicura ad `any`. Rappresenta un valore di tipo sconosciuto, ma richiede un controllo esplicito prima di poterlo utilizzare:

```typescript
let valore: unknown = "ciao";

// Errore: Object is of type 'unknown'
// valore.toUpperCase();

// Corretto: type guard prima dell'uso
if (typeof valore === "string") {
  console.log(valore.toUpperCase()); // OK
}
```

#### Type Annotations e Type Inference

Le **type annotations** permettono di dichiarare esplicitamente il tipo di una variabile, parametro o valore di ritorno:

```typescript
let messaggio: string = "Buongiorno";
let contatore: number = 0;
```

La **type inference** e la capacita del compilatore di dedurre automaticamente il tipo basandosi sul valore assegnato:

```typescript
let messaggio = "Buongiorno"; // TypeScript deduce: string
let contatore = 0;            // TypeScript deduce: number
let flag = true;              // TypeScript deduce: boolean
```

In generale, se l'inizializzazione fornisce informazioni sufficienti, le annotazioni esplicite non sono necessarie. Tuttavia, e consigliabile annotare esplicitamente i parametri delle funzioni e, in alcuni casi, i valori di ritorno.

#### Literal Types

I literal types restringono un tipo a un valore specifico:

```typescript
let direzione: "nord" | "sud" | "est" | "ovest";
direzione = "nord"; // OK
direzione = "alto"; // Errore

let codice: 200 | 404 | 500;
codice = 200; // OK
codice = 301; // Errore

// const inferisce automaticamente literal types
const protocollo = "https"; // tipo: "https", non string
```

#### Type Assertions (as)

Le type assertions permettono di comunicare al compilatore che si conosce il tipo effettivo di un valore meglio di quanto possa dedurre il compilatore stesso:

```typescript
const inputElement = document.getElementById("email") as HTMLInputElement;
inputElement.value = "test@esempio.it";

// Sintassi alternativa (non utilizzabile in JSX)
const elemento = <HTMLInputElement>document.getElementById("email");

// Double assertion per casi estremi (da evitare)
const valore = ("ciao" as unknown) as number;
```

Le type assertions non eseguono alcuna conversione a runtime: sono puramente un'indicazione al compilatore.

### Array e Tuple

#### Array

TypeScript offre due sintassi equivalenti per dichiarare array tipizzati:

```typescript
// Sintassi con generics
let numeri: Array<number> = [1, 2, 3, 4, 5];

// Sintassi abbreviata (piu comune)
let nomi: string[] = ["Anna", "Marco", "Lucia"];

// Array di tipi complessi
let coppie: [string, number][] = [["a", 1], ["b", 2]];

// Array readonly — impedisce modifiche
let costanti: readonly number[] = [1, 2, 3];
// costanti.push(4); // Errore: Property 'push' does not exist on type 'readonly number[]'
```

#### Tuple

Le tuple sono array a lunghezza fissa dove ogni elemento ha un tipo specifico:

```typescript
let coordinata: [number, number] = [45.464, 9.190];
let persona: [string, number, boolean] = ["Marco", 28, true];

// Tuple con etichette (migliora la leggibilita)
type Punto = [x: number, y: number, z: number];
let punto: Punto = [10, 20, 30];

// Tuple readonly
let immutabile: readonly [string, number] = ["fisso", 42];

// Tuple con rest elements
type StringENumeri = [string, ...number[]];
let dati: StringENumeri = ["valori", 1, 2, 3, 4, 5];

// Tuple opzionali
type RispostaHTTP = [number, string, string?];
let risposta: RispostaHTTP = [200, "OK"];
let rispostaConCorpo: RispostaHTTP = [200, "OK", '{"dati": true}'];
```

### Object Types

#### Annotazioni di Tipo per Oggetti

```typescript
let utente: { nome: string; eta: number; email: string } = {
  nome: "Giulia",
  eta: 32,
  email: "giulia@esempio.it"
};

// Proprietà opzionali con ?
let configurazione: {
  host: string;
  porta: number;
  ssl?: boolean;  // opzionale
} = {
  host: "localhost",
  porta: 3000
};
```

#### Proprieta Readonly

```typescript
let punto: {
  readonly x: number;
  readonly y: number;
} = { x: 10, y: 20 };

// punto.x = 30; // Errore: Cannot assign to 'x' because it is a read-only property
```

#### Index Signatures

Le index signatures permettono di definire oggetti con chiavi dinamiche:

```typescript
interface Dizionario {
  [chiave: string]: number;
}

let voti: Dizionario = {
  matematica: 8,
  storia: 7,
  scienze: 9
};

// Index signature con vincolo aggiuntivo
interface ConfigFlessibile {
  nome: string; // proprieta obbligatoria
  [chiave: string]: string; // tutte le altre chiavi devono avere valore string
}
```

#### Record<K, V>

Il tipo utility `Record` crea un tipo oggetto con chiavi di tipo `K` e valori di tipo `V`:

```typescript
type Ruolo = "admin" | "editor" | "viewer";

const permessi: Record<Ruolo, string[]> = {
  admin: ["leggere", "scrivere", "eliminare"],
  editor: ["leggere", "scrivere"],
  viewer: ["leggere"]
};

// Record con chiavi stringa generiche
type CacheRisposte = Record<string, { dati: unknown; timestamp: number }>;
```

### Union e Intersection

#### Union Types (|)

Un union type rappresenta un valore che puo essere uno tra diversi tipi:

```typescript
type Risultato = string | number;
type ID = string | number;

function stampaID(id: ID): void {
  if (typeof id === "string") {
    console.log(id.toUpperCase());
  } else {
    console.log(id.toFixed(2));
  }
}

// Union con null (pattern molto comune)
type MaybeString = string | null;

function lunghezza(testo: MaybeString): number {
  if (testo === null) return 0;
  return testo.length;
}
```

#### Intersection Types (&)

Un intersection type combina piu tipi in uno solo, richiedendo che il valore soddisfi tutti i tipi contemporaneamente:

```typescript
type ConNome = { nome: string };
type ConEta = { eta: number };
type Persona = ConNome & ConEta;

let persona: Persona = { nome: "Luca", eta: 25 };

// Composizione di interfacce tramite intersection
interface Timestamped {
  createdAt: Date;
  updatedAt: Date;
}

interface SoftDeletable {
  deletedAt: Date | null;
}

type Entita = Timestamped & SoftDeletable & { id: string };
```

#### Discriminated Unions

Le discriminated unions (o tagged unions) utilizzano una proprieta comune come discriminante per distinguere tra diversi tipi in una union:

```typescript
interface Cerchio {
  tipo: "cerchio";
  raggio: number;
}

interface Rettangolo {
  tipo: "rettangolo";
  larghezza: number;
  altezza: number;
}

interface Triangolo {
  tipo: "triangolo";
  base: number;
  altezza: number;
}

type Forma = Cerchio | Rettangolo | Triangolo;

function area(forma: Forma): number {
  switch (forma.tipo) {
    case "cerchio":
      return Math.PI * forma.raggio ** 2;
    case "rettangolo":
      return forma.larghezza * forma.altezza;
    case "triangolo":
      return (forma.base * forma.altezza) / 2;
  }
}
```

#### Type Narrowing

Il type narrowing e il processo attraverso il quale TypeScript restringe il tipo di una variabile all'interno di un blocco di codice condizionale:

```typescript
// typeof guard
function processa(valore: string | number): string {
  if (typeof valore === "string") {
    return valore.toUpperCase(); // qui valore e string
  }
  return valore.toFixed(2); // qui valore e number
}

// instanceof guard
function formatta(data: Date | string): string {
  if (data instanceof Date) {
    return data.toISOString();
  }
  return new Date(data).toISOString();
}

// in operator guard
interface Pesce {
  nuota: () => void;
}

interface Uccello {
  vola: () => void;
}

function muovi(animale: Pesce | Uccello): void {
  if ("nuota" in animale) {
    animale.nuota();
  } else {
    animale.vola();
  }
}

// Custom type guard (user-defined)
function isStringa(valore: unknown): valore is string {
  return typeof valore === "string";
}

function elabora(input: unknown): void {
  if (isStringa(input)) {
    console.log(input.toUpperCase()); // TypeScript sa che input e string
  }
}
```

---

## Funzioni

### Tipi dei Parametri e Valore di Ritorno

```typescript
// Annotazione esplicita dei parametri e del ritorno
function moltiplica(a: number, b: number): number {
  return a * b;
}

// Arrow function con tipi
const dividi = (a: number, b: number): number => a / b;

// Il tipo di ritorno puo essere inferito
const somma = (a: number, b: number) => a + b; // ritorno inferito: number
```

### Parametri Opzionali e Default

```typescript
// Parametro opzionale (deve essere dopo quelli obbligatori)
function saluta(nome: string, titolo?: string): string {
  if (titolo) {
    return `Buongiorno ${titolo} ${nome}`;
  }
  return `Ciao ${nome}`;
}

saluta("Rossi", "Dott.");  // "Buongiorno Dott. Rossi"
saluta("Marco");           // "Ciao Marco"

// Parametro con valore predefinito
function creaUtente(nome: string, ruolo: string = "viewer"): object {
  return { nome, ruolo };
}

creaUtente("Anna");           // { nome: "Anna", ruolo: "viewer" }
creaUtente("Anna", "admin");  // { nome: "Anna", ruolo: "admin" }
```

### Rest Parameters

```typescript
function sommaRest(...numeri: number[]): number {
  return numeri.reduce((acc, n) => acc + n, 0);
}

sommaRest(1, 2, 3, 4, 5); // 15

// Rest parameters con altri parametri
function log(livello: string, ...messaggi: string[]): void {
  messaggi.forEach(msg => console.log(`[${livello}] ${msg}`));
}
```

### Function Overloads

I function overloads permettono di definire piu firme per una stessa funzione, consentendo al compilatore di selezionare il tipo di ritorno corretto in base ai parametri forniti:

```typescript
function cerca(id: number): Utente;
function cerca(email: string): Utente;
function cerca(query: number | string): Utente {
  if (typeof query === "number") {
    return trovaPerID(query);
  }
  return trovaPerEmail(query);
}

// L'overload garantisce tipi di ritorno precisi
const utente1 = cerca(42);        // tipo: Utente
const utente2 = cerca("a@b.it");  // tipo: Utente
```

### Generics nelle Funzioni

```typescript
function primoElemento<T>(array: T[]): T | undefined {
  return array[0];
}

const num = primoElemento([1, 2, 3]);       // tipo: number | undefined
const str = primoElemento(["a", "b", "c"]); // tipo: string | undefined

// Generics con vincolo
function proprietà<T, K extends keyof T>(obj: T, chiave: K): T[K] {
  return obj[chiave];
}

const persona = { nome: "Luca", eta: 30 };
const nome = proprietà(persona, "nome"); // tipo: string
const eta = proprietà(persona, "eta");   // tipo: number
```

### Typing delle Callback

```typescript
// Tipo funzione come parametro
function eseguiOperazione(
  a: number,
  b: number,
  operazione: (x: number, y: number) => number
): number {
  return operazione(a, b);
}

eseguiOperazione(10, 5, (x, y) => x + y); // 15
eseguiOperazione(10, 5, (x, y) => x * y); // 50

// Tipo funzione con type alias
type Comparatore<T> = (a: T, b: T) => number;

function ordina<T>(array: T[], compara: Comparatore<T>): T[] {
  return [...array].sort(compara);
}

const numeri = ordina([3, 1, 2], (a, b) => a - b); // [1, 2, 3]
```

---

## Interfacce e Type Alias

### interface

#### Dichiarazione e Estensione

```typescript
interface Animale {
  nome: string;
  eta: number;
  verso(): string;
}

// Estensione di interfaccia
interface Cane extends Animale {
  razza: string;
  scodinzola: boolean;
}

// Estensione multipla
interface CaneGuida extends Cane {
  proprietario: string;
  certificato: boolean;
}

// Estensione di piu interfacce contemporaneamente
interface Anfibbio extends Animale {
  puoNuotare: boolean;
  puoCamminare: boolean;
}
```

#### Implementazione di Interfacce

```typescript
interface Serializzabile {
  toJSON(): string;
  fromJSON(json: string): void;
}

class Prodotto implements Serializzabile {
  constructor(
    public nome: string,
    public prezzo: number
  ) {}

  toJSON(): string {
    return JSON.stringify({ nome: this.nome, prezzo: this.prezzo });
  }

  fromJSON(json: string): void {
    const dati = JSON.parse(json);
    this.nome = dati.nome;
    this.prezzo = dati.prezzo;
  }
}
```

#### Declaration Merging

Una caratteristica unica delle interfacce e la possibilita di unire piu dichiarazioni con lo stesso nome:

```typescript
interface Finestra {
  titolo: string;
}

interface Finestra {
  larghezza: number;
  altezza: number;
}

// Le due dichiarazioni vengono fuse automaticamente
const finestra: Finestra = {
  titolo: "La mia app",
  larghezza: 800,
  altezza: 600
};
```

Questa capacita e particolarmente utile per estendere tipi di librerie esterne senza modificarne il codice sorgente.

#### Tipi Ibridi

Le interfacce possono descrivere oggetti che sono contemporaneamente funzioni e contengono proprieta:

```typescript
interface Contatore {
  (inizio: number): string;
  intervallo: number;
  reset(): void;
}

function creaContatore(): Contatore {
  let conteggio = 0;
  const contatore = function (inizio: number) {
    conteggio = inizio;
    return `Conteggio: ${conteggio}`;
  } as Contatore;
  contatore.intervallo = 1000;
  contatore.reset = () => { conteggio = 0; };
  return contatore;
}
```

### type

#### Type Alias

I type alias creano un nome per qualsiasi tipo:

```typescript
type ID = string | number;
type Coordinate = [number, number];
type CallbackErrore = (errore: Error | null, risultato?: unknown) => void;

type Utente = {
  id: ID;
  nome: string;
  email: string;
  ruoli: string[];
};
```

#### Mapped Types

I mapped types trasformano le proprieta di un tipo esistente:

```typescript
// Rendere tutte le proprieta opzionali
type Opzionale<T> = {
  [P in keyof T]?: T[P];
};

// Rendere tutte le proprieta di sola lettura
type SolaLettura<T> = {
  readonly [P in keyof T]: T[P];
};

// Rendere tutte le proprieta nullable
type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

type UtenteOpzionale = Opzionale<Utente>;
// equivale a: { id?: ID; nome?: string; email?: string; ruoli?: string[]; }
```

#### Conditional Types

I tipi condizionali selezionano un tipo in base a una condizione:

```typescript
type IsStringa<T> = T extends string ? true : false;

type A = IsStringa<string>;  // true
type B = IsStringa<number>;  // false

// Esempio pratico: estrai il tipo degli elementi di un array
type ElementoArray<T> = T extends (infer U)[] ? U : T;

type X = ElementoArray<string[]>; // string
type Y = ElementoArray<number>;   // number
```

#### Template Literal Types

I template literal types permettono di manipolare tipi stringa:

```typescript
type Colore = "rosso" | "verde" | "blu";
type Dimensione = "piccolo" | "medio" | "grande";

type ClasseCSS = `${Dimensione}-${Colore}`;
// "piccolo-rosso" | "piccolo-verde" | "piccolo-blu" | "medio-rosso" | ...

// Trasformazioni di stringhe
type Maiuscolo<S extends string> = Uppercase<S>;
type Minuscolo<S extends string> = Lowercase<S>;
type Capitalizzato<S extends string> = Capitalize<S>;

type EventoNome = `on${Capitalize<"click" | "hover" | "focus">}`;
// "onClick" | "onHover" | "onFocus"
```

### interface vs type — Quando Usare Quale

Le differenze chiave sono:

| Caratteristica | `interface` | `type` |
|---|---|---|
| Declaration merging | Si | No |
| Estensione con `extends` | Si | Si (con `&`) |
| Union types | No | Si |
| Mapped types | No | Si |
| Tipi primitivi | No | Si |
| Tuple | No | Si |

**Linea guida pratica**: usare `interface` per definire la forma di oggetti e contratti API. Usare `type` per union types, tipi complessi, tuple, mapped types e quando si ha bisogno di funzionalita che le interfacce non supportano. In molti team, la convenzione e preferire `interface` per i casi semplici e passare a `type` quando necessario.

---

## Generics

I generics permettono di scrivere componenti riutilizzabili che funzionano con diversi tipi mantenendo la type safety.

### Funzioni Generiche

```typescript
function identita<T>(valore: T): T {
  return valore;
}

const stringa = identita("ciao");  // tipo: string
const numero = identita(42);       // tipo: number

// Generics multipli
function coppia<A, B>(primo: A, secondo: B): [A, B] {
  return [primo, secondo];
}

const risultato = coppia("chiave", 100); // tipo: [string, number]
```

### Classi Generiche

```typescript
class Pila<T> {
  private elementi: T[] = [];

  push(elemento: T): void {
    this.elementi.push(elemento);
  }

  pop(): T | undefined {
    return this.elementi.pop();
  }

  peek(): T | undefined {
    return this.elementi[this.elementi.length - 1];
  }

  get dimensione(): number {
    return this.elementi.length;
  }
}

const pilaNumeri = new Pila<number>();
pilaNumeri.push(1);
pilaNumeri.push(2);
pilaNumeri.pop(); // tipo: number | undefined

const pilaStringhe = new Pila<string>();
pilaStringhe.push("primo");
```

### Vincoli Generici (extends)

```typescript
// Il tipo T deve avere una proprietà 'length'
function lunghezzaMinima<T extends { length: number }>(a: T, b: T): T {
  return a.length <= b.length ? a : b;
}

lunghezzaMinima("abc", "ab");   // OK, le stringhe hanno 'length'
lunghezzaMinima([1, 2], [1]);   // OK, gli array hanno 'length'
// lunghezzaMinima(10, 20);     // Errore: number non ha 'length'

// Vincolo con keyof
function ottieni<T, K extends keyof T>(obj: T, chiave: K): T[K] {
  return obj[chiave];
}
```

### Parametri di Tipo Predefiniti

```typescript
interface RispostaAPI<T = unknown> {
  dati: T;
  stato: number;
  messaggio: string;
}

// Senza specificare T, viene usato unknown
const risposta: RispostaAPI = { dati: null, stato: 200, messaggio: "OK" };

// Con T specificato
const utenteRisposta: RispostaAPI<Utente> = {
  dati: { id: "1", nome: "Marco", email: "m@e.it", ruoli: ["admin"] },
  stato: 200,
  messaggio: "OK"
};
```

### Conditional Types con Generics (infer)

La parola chiave `infer` permette di estrarre tipi all'interno di tipi condizionali:

```typescript
// Estrarre il tipo di ritorno di una funzione
type TipoRitorno<T> = T extends (...args: any[]) => infer R ? R : never;

type A = TipoRitorno<() => string>;         // string
type B = TipoRitorno<(x: number) => void>;  // void

// Estrarre il tipo delle Promise
type Unwrap<T> = T extends Promise<infer U> ? U : T;

type C = Unwrap<Promise<string>>;  // string
type D = Unwrap<number>;           // number

// Estrarre i parametri di una funzione
type Parametri<T> = T extends (...args: infer P) => any ? P : never;

type E = Parametri<(a: string, b: number) => void>; // [a: string, b: number]
```

### Utility Types Principali

TypeScript include numerosi utility types built-in basati su generics e mapped types:

```typescript
interface Utente {
  id: string;
  nome: string;
  email: string;
  eta: number;
  ruolo: "admin" | "editor" | "viewer";
}

// Partial<T> — tutte le proprieta diventano opzionali
type UtenteAggiornamento = Partial<Utente>;

// Required<T> — tutte le proprieta diventano obbligatorie
type UtenteCompleto = Required<Partial<Utente>>;

// Pick<T, K> — seleziona solo alcune proprieta
type UtenteBase = Pick<Utente, "id" | "nome">;

// Omit<T, K> — esclude alcune proprieta
type UtenteSenzaID = Omit<Utente, "id">;

// Record<K, V> — crea un tipo oggetto con chiavi K e valori V
type PermessiPerRuolo = Record<Utente["ruolo"], string[]>;

// Readonly<T> — tutte le proprieta diventano readonly
type UtenteImmutabile = Readonly<Utente>;

// Exclude<T, U> — esclude da T i tipi assegnabili a U
type Primitivi = string | number | boolean;
type SoloPrimitivi = Exclude<Primitivi, boolean>; // string | number

// Extract<T, U> — estrae da T i tipi assegnabili a U
type SoloStringhe = Extract<Primitivi, string>; // string

// NonNullable<T> — rimuove null e undefined
type Sicuro = NonNullable<string | null | undefined>; // string

// ReturnType<T> — estrae il tipo di ritorno di una funzione
type RitornoFetch = ReturnType<typeof fetch>; // Promise<Response>

// Parameters<T> — estrae i tipi dei parametri come tuple
type ParamFetch = Parameters<typeof fetch>; // [input: RequestInfo | URL, init?: RequestInit]

// InstanceType<T> — estrae il tipo dell'istanza di un costruttore
type IstanzaData = InstanceType<typeof Date>; // Date
```

---

## Classi

### Tipizzazione delle Classi

```typescript
class Veicolo {
  marca: string;
  modello: string;
  anno: number;

  constructor(marca: string, modello: string, anno: number) {
    this.marca = marca;
    this.modello = modello;
    this.anno = anno;
  }

  descrizione(): string {
    return `${this.marca} ${this.modello} (${this.anno})`;
  }
}

// Sintassi abbreviata con parameter properties
class VeicoloCompatto {
  constructor(
    public marca: string,
    public modello: string,
    public anno: number
  ) {}
}
```

### Modificatori di Accesso

```typescript
class ContoBancario {
  public titolare: string;       // accessibile ovunque (default)
  private saldo: number;         // accessibile solo nella classe
  protected valuta: string;      // accessibile nella classe e nelle sottoclassi
  readonly iban: string;         // assegnabile solo nel costruttore

  constructor(titolare: string, saldoIniziale: number, iban: string) {
    this.titolare = titolare;
    this.saldo = saldoIniziale;
    this.valuta = "EUR";
    this.iban = iban;
  }

  public deposita(importo: number): void {
    if (importo > 0) {
      this.saldo += importo;
    }
  }

  public getSaldo(): number {
    return this.saldo;
  }

  private registraOperazione(tipo: string, importo: number): void {
    console.log(`[${tipo}] ${importo} ${this.valuta}`);
  }
}

class ContoRisparmio extends ContoBancario {
  private tassoInteresse: number;

  constructor(titolare: string, saldo: number, iban: string, tasso: number) {
    super(titolare, saldo, iban);
    this.tassoInteresse = tasso;
  }

  calcolaInteresse(): string {
    // this.valuta e accessibile (protected)
    // this.saldo NON e accessibile (private)
    return `Tasso: ${this.tassoInteresse}% in ${this.valuta}`;
  }
}
```

### Classi Astratte

```typescript
abstract class Forma {
  abstract area(): number;
  abstract perimetro(): number;

  // Metodo concreto condiviso
  descrizione(): string {
    return `Forma con area ${this.area().toFixed(2)} e perimetro ${this.perimetro().toFixed(2)}`;
  }
}

class Cerchio extends Forma {
  constructor(private raggio: number) {
    super();
  }

  area(): number {
    return Math.PI * this.raggio ** 2;
  }

  perimetro(): number {
    return 2 * Math.PI * this.raggio;
  }
}

class Quadrato extends Forma {
  constructor(private lato: number) {
    super();
  }

  area(): number {
    return this.lato ** 2;
  }

  perimetro(): number {
    return 4 * this.lato;
  }
}

// const forma = new Forma(); // Errore: non si puo istanziare una classe astratta
const cerchio = new Cerchio(5);
console.log(cerchio.descrizione());
```

### Membri Statici

```typescript
class Configurazione {
  private static istanza: Configurazione;
  private impostazioni: Map<string, string> = new Map();

  private constructor() {} // costruttore privato per Singleton

  static getIstanza(): Configurazione {
    if (!Configurazione.istanza) {
      Configurazione.istanza = new Configurazione();
    }
    return Configurazione.istanza;
  }

  imposta(chiave: string, valore: string): void {
    this.impostazioni.set(chiave, valore);
  }

  ottieni(chiave: string): string | undefined {
    return this.impostazioni.get(chiave);
  }
}

const config = Configurazione.getIstanza();
config.imposta("tema", "scuro");
```

### Decorators

I decorators sono una funzionalita che permette di aggiungere metadati e modificare il comportamento di classi, metodi, proprieta e parametri. Sono supportati come funzionalita sperimentale e sono entrati nello stage 3 delle proposte ECMAScript:

```typescript
// Abilitare in tsconfig.json: "experimentalDecorators": true

// Decorator di classe
function Loggabile(target: Function) {
  console.log(`Classe registrata: ${target.name}`);
}

@Loggabile
class ServizioUtente {
  ottieni(id: string): string {
    return `Utente ${id}`;
  }
}

// Decorator di metodo
function MisuraTempo(
  target: any,
  nomeMetodo: string,
  descriptor: PropertyDescriptor
) {
  const metodoOriginale = descriptor.value;

  descriptor.value = function (...args: any[]) {
    const inizio = performance.now();
    const risultato = metodoOriginale.apply(this, args);
    const fine = performance.now();
    console.log(`${nomeMetodo}: ${(fine - inizio).toFixed(2)}ms`);
    return risultato;
  };
}

class Servizio {
  @MisuraTempo
  calcolaPesante(): number {
    let somma = 0;
    for (let i = 0; i < 1000000; i++) somma += i;
    return somma;
  }
}
```

---

## Moduli e Namespaces

### ES Modules con TypeScript

TypeScript supporta pienamente la sintassi ES Modules:

```typescript
// matematica.ts — esportazione
export function somma(a: number, b: number): number {
  return a + b;
}

export function moltiplica(a: number, b: number): number {
  return a * b;
}

export default class Calcolatrice {
  static valuta(espressione: string): number {
    return eval(espressione);
  }
}

// app.ts — importazione
import Calcolatrice, { somma, moltiplica } from "./matematica";

console.log(somma(2, 3));
console.log(Calcolatrice.valuta("2 + 3"));
```

### Import di Soli Tipi (import type)

La sintassi `import type` garantisce che l'importazione venga completamente rimossa dal codice compilato, evitando effetti collaterali:

```typescript
// tipi.ts
export interface Utente {
  id: string;
  nome: string;
}

export type Ruolo = "admin" | "editor" | "viewer";

// servizio.ts
import type { Utente, Ruolo } from "./tipi";

function creaUtente(nome: string, ruolo: Ruolo): Utente {
  return { id: crypto.randomUUID(), nome };
}

// Si puo anche usare inline
import { creaUtente, type Utente } from "./servizio";
```

### File di Dichiarazione (.d.ts)

I file `.d.ts` contengono solo dichiarazioni di tipo, senza implementazione. Servono per descrivere la forma di librerie JavaScript esistenti:

```typescript
// globale.d.ts
declare global {
  interface Window {
    analytics: {
      traccia(evento: string, dati?: Record<string, unknown>): void;
    };
  }
}

// modulo-esterno.d.ts
declare module "libreria-senza-tipi" {
  export function elabora(dati: unknown): string;
  export const versione: string;
}
```

### Pacchetti @types

Per le librerie JavaScript che non includono definizioni di tipo, la community DefinitelyTyped fornisce pacchetti `@types`:

```bash
# Installazione tipi per librerie comuni
npm install --save-dev @types/node
npm install --save-dev @types/express
npm install --save-dev @types/lodash

# I tipi vengono automaticamente riconosciuti dal compilatore
```

### Risoluzione dei Moduli e Path Mapping

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "moduleResolution": "bundler", // o "node", "node16"
    "baseUrl": "./src",
    "paths": {
      "@componenti/*": ["componenti/*"],
      "@servizi/*": ["servizi/*"],
      "@utils/*": ["utils/*"],
      "@tipi": ["tipi/index"]
    }
  }
}
```

Questo permette importazioni pulite:

```typescript
// Invece di
import { Utente } from "../../../tipi/utente";

// Si puo scrivere
import { Utente } from "@tipi";
import { formattaData } from "@utils/data";
```

---

## Configurazione (tsconfig.json)

Il file `tsconfig.json` e il cuore della configurazione di un progetto TypeScript. Ecco le opzioni piu importanti con spiegazioni dettagliate:

```jsonc
{
  "compilerOptions": {
    // === Output ===
    "target": "ES2022",          // Versione JS di output (ES5, ES6, ES2020, ES2022, ESNext)
    "module": "ESNext",          // Sistema di moduli (CommonJS, ESNext, Node16, NodeNext)
    "outDir": "./dist",          // Directory di output per i file compilati
    "rootDir": "./src",          // Directory radice dei file sorgente
    "declaration": true,         // Genera file .d.ts
    "sourceMap": true,           // Genera file .map per debugging

    // === Risoluzione Moduli ===
    "moduleResolution": "bundler", // Strategia di risoluzione (node, node16, bundler)
    "baseUrl": "./src",           // Base per risolvere percorsi non relativi
    "paths": {                    // Mapping dei percorsi
      "@/*": ["./*"]
    },
    "esModuleInterop": true,      // Compatibilita con import di moduli CommonJS
    "skipLibCheck": true,         // Salta il controllo tipi dei file .d.ts

    // === Librerie e Ambiente ===
    "lib": ["ES2022", "DOM", "DOM.Iterable"],  // Librerie di tipo incluse
    "jsx": "react-jsx",          // Supporto JSX (react, react-jsx, react-jsxdev, preserve)

    // === Rigore (Strict Mode) ===
    "strict": true,              // Abilita tutte le flag strict
    // Le flag individuali incluse in strict:
    // "strictNullChecks": true,       — null/undefined non assegnabili ad altri tipi
    // "strictFunctionTypes": true,    — controllo piu rigoroso sui tipi funzione
    // "strictBindCallApply": true,    — controllo corretto di bind, call, apply
    // "strictPropertyInitialization": true, — proprieta classe devono essere inizializzate
    // "noImplicitAny": true,          — errore su tipi 'any' impliciti
    // "noImplicitThis": true,         — errore su 'this' con tipo implicito
    // "alwaysStrict": true,           — emetti "use strict" in ogni file
    // "useUnknownInCatchVariables": true, — catch variable di tipo unknown

    // === Controlli Aggiuntivi ===
    "noUnusedLocals": true,        // Errore su variabili locali non utilizzate
    "noUnusedParameters": true,    // Errore su parametri non utilizzati
    "noImplicitReturns": true,     // Errore se non tutti i percorsi restituiscono un valore
    "noFallthroughCasesInSwitch": true, // Errore su case senza break
    "forceConsistentCasingInFileNames": true // Case-sensitive nei nomi file
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### Configurazione Raccomandata

Per un nuovo progetto, si raccomanda di partire con `strict: true` e aggiungere controlli aggiuntivi progressivamente. Ecco una configurazione di partenza solida:

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "resolveJsonModule": true,
    "isolatedModules": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

---

## Pattern Avanzati

### Branded Types

I branded types creano tipi nominali in un sistema strutturale, impedendo l'uso accidentale di valori semanticamente diversi ma strutturalmente identici:

```typescript
type EUR = number & { readonly __brand: "EUR" };
type USD = number & { readonly __brand: "USD" };

function eur(valore: number): EUR {
  return valore as EUR;
}

function usd(valore: number): USD {
  return valore as USD;
}

function sommaEUR(a: EUR, b: EUR): EUR {
  return (a + b) as EUR;
}

const prezzo = eur(100);
const sconto = eur(20);
const totale = sommaEUR(prezzo, sconto); // OK

const dollari = usd(50);
// sommaEUR(prezzo, dollari); // Errore! Non si possono mischiare EUR e USD
```

### Builder Pattern con Tipi

```typescript
class QueryBuilder<T extends Record<string, unknown>> {
  private condizioni: Partial<T> = {};
  private limite?: number;
  private offset?: number;

  where<K extends keyof T>(campo: K, valore: T[K]): this {
    this.condizioni[campo] = valore;
    return this;
  }

  limit(n: number): this {
    this.limite = n;
    return this;
  }

  skip(n: number): this {
    this.offset = n;
    return this;
  }

  build(): { condizioni: Partial<T>; limite?: number; offset?: number } {
    return {
      condizioni: this.condizioni,
      limite: this.limite,
      offset: this.offset
    };
  }
}

interface Prodotto {
  nome: string;
  prezzo: number;
  categoria: string;
}

const query = new QueryBuilder<Prodotto>()
  .where("categoria", "elettronica")
  .where("prezzo", 99.99)
  .limit(10)
  .build();
```

### Macchine a Stati con Discriminated Unions

```typescript
type StatoOrdine =
  | { stato: "bozza"; dati: { articoli: string[] } }
  | { stato: "confermato"; dati: { articoli: string[]; dataConferma: Date } }
  | { stato: "spedito"; dati: { articoli: string[]; dataConferma: Date; codiceTracking: string } }
  | { stato: "consegnato"; dati: { articoli: string[]; dataConferma: Date; codiceTracking: string; dataConsegna: Date } }
  | { stato: "annullato"; dati: { motivazione: string } };

function prossimaAzione(ordine: StatoOrdine): string {
  switch (ordine.stato) {
    case "bozza":
      return "Conferma l'ordine";
    case "confermato":
      return "Attendi la spedizione";
    case "spedito":
      return `Traccia: ${ordine.dati.codiceTracking}`;
    case "consegnato":
      return "Lascia una recensione";
    case "annullato":
      return `Ordine annullato: ${ordine.dati.motivazione}`;
  }
}
```

### Exhaustive Checking con never

```typescript
type Colore = "rosso" | "verde" | "blu";

function esadecimale(colore: Colore): string {
  switch (colore) {
    case "rosso":
      return "#FF0000";
    case "verde":
      return "#00FF00";
    case "blu":
      return "#0000FF";
    default:
      // Se si aggiunge un nuovo colore senza gestirlo, TypeScript segnala un errore qui
      const _esaustivo: never = colore;
      throw new Error(`Colore non gestito: ${_esaustivo}`);
  }
}
```

### Type-Safe Event Emitter

```typescript
type MappaEventi = {
  "utente:login": { utenteId: string; timestamp: Date };
  "utente:logout": { utenteId: string };
  "ordine:creato": { ordineId: string; totale: number };
  "errore": { messaggio: string; codice: number };
};

class EventEmitter<T extends Record<string, unknown>> {
  private ascoltatori = new Map<keyof T, Set<(dati: any) => void>>();

  on<K extends keyof T>(evento: K, callback: (dati: T[K]) => void): void {
    if (!this.ascoltatori.has(evento)) {
      this.ascoltatori.set(evento, new Set());
    }
    this.ascoltatori.get(evento)!.add(callback);
  }

  emit<K extends keyof T>(evento: K, dati: T[K]): void {
    this.ascoltatori.get(evento)?.forEach(cb => cb(dati));
  }

  off<K extends keyof T>(evento: K, callback: (dati: T[K]) => void): void {
    this.ascoltatori.get(evento)?.delete(callback);
  }
}

const bus = new EventEmitter<MappaEventi>();

bus.on("utente:login", (dati) => {
  console.log(`Login: ${dati.utenteId} alle ${dati.timestamp}`);
});

bus.emit("utente:login", { utenteId: "123", timestamp: new Date() });
// bus.emit("utente:login", { utenteId: "123" }); // Errore: manca timestamp
```

### Zod per Validazione a Runtime

TypeScript controlla i tipi solo a compile-time. Per la validazione a runtime, librerie come Zod colmano questa lacuna:

```typescript
import { z } from "zod";

// Definizione dello schema
const SchemaUtente = z.object({
  nome: z.string().min(2).max(50),
  email: z.string().email(),
  eta: z.number().int().min(18).max(120),
  ruolo: z.enum(["admin", "editor", "viewer"]),
  preferenze: z.object({
    tema: z.enum(["chiaro", "scuro"]).default("chiaro"),
    notifiche: z.boolean().default(true)
  }).optional()
});

// Estrazione del tipo TypeScript dallo schema
type Utente = z.infer<typeof SchemaUtente>;

// Validazione a runtime
function registraUtente(datiGrezzi: unknown): Utente {
  const risultato = SchemaUtente.safeParse(datiGrezzi);

  if (!risultato.success) {
    throw new Error(`Validazione fallita: ${risultato.error.message}`);
  }

  return risultato.data; // tipo: Utente, validato a runtime
}
```

### Template Literal Types per Manipolazione Stringhe

```typescript
// Generazione automatica di getter
type Getter<T extends string> = `get${Capitalize<T>}`;

type CampiUtente = "nome" | "email" | "eta";
type GettersUtente = Getter<CampiUtente>;
// "getNome" | "getEmail" | "getEta"

// Parsing di percorsi
type EstraiParametri<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | EstraiParametri<Rest>
    : T extends `${string}:${infer Param}`
      ? Param
      : never;

type Params = EstraiParametri<"/utenti/:utenteId/ordini/:ordineId">;
// "utenteId" | "ordineId"
```

---

## TypeScript con React

### Componenti Funzionali

L'approccio moderno preferisce la tipizzazione esplicita delle props rispetto all'uso di `React.FC`:

```typescript
// Approccio raccomandato: tipizzazione esplicita delle props
interface CardProps {
  titolo: string;
  descrizione: string;
  immagine?: string;
  onClick?: () => void;
}

function Card({ titolo, descrizione, immagine, onClick }: CardProps) {
  return (
    <div onClick={onClick}>
      {immagine && <img src={immagine} alt={titolo} />}
      <h2>{titolo}</h2>
      <p>{descrizione}</p>
    </div>
  );
}

// Con children espliciti
interface LayoutProps {
  titolo: string;
  children: React.ReactNode;
}

function Layout({ titolo, children }: LayoutProps) {
  return (
    <div>
      <header><h1>{titolo}</h1></header>
      <main>{children}</main>
    </div>
  );
}

// Nota: React.FC aggiunge implicitamente children e altre proprietà.
// L'approccio esplicito offre maggiore chiarezza e controllo.
```

### Tipizzazione degli Hooks

```typescript
import { useState, useRef, useContext, createContext } from "react";

// useState con tipo esplicito
interface Utente {
  id: string;
  nome: string;
}

function ProfiloUtente() {
  const [utente, setUtente] = useState<Utente | null>(null);
  const [caricamento, setCaricamento] = useState(false); // inferito: boolean
  const [contatore, setContatore] = useState(0); // inferito: number

  // useRef per elementi DOM
  const inputRef = useRef<HTMLInputElement>(null);

  // useRef per valori mutabili
  const timerRef = useRef<number>(0);

  const focusInput = () => {
    inputRef.current?.focus();
  };

  return (
    <div>
      <input ref={inputRef} />
      <button onClick={focusInput}>Focus</button>
      {utente && <p>{utente.nome}</p>}
    </div>
  );
}

// Context con tipi
interface TemaContexto {
  tema: "chiaro" | "scuro";
  cambiaTema: () => void;
}

const TemaContext = createContext<TemaContexto | null>(null);

function useTema(): TemaContexto {
  const contesto = useContext(TemaContext);
  if (!contesto) {
    throw new Error("useTema deve essere utilizzato dentro TemaProvider");
  }
  return contesto;
}
```

### Tipizzazione degli Event Handler

```typescript
function Formulario() {
  const gestisciSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // logica di submit
  };

  const gestisciInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log(e.target.value);
  };

  const gestisciClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    console.log(e.clientX, e.clientY);
  };

  const gestisciTastiera = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      // azione
    }
  };

  return (
    <form onSubmit={gestisciSubmit}>
      <input onChange={gestisciInput} onKeyDown={gestisciTastiera} />
      <button onClick={gestisciClick}>Invia</button>
    </form>
  );
}
```

### Componenti Generici

```typescript
interface ListaProps<T> {
  elementi: T[];
  renderElemento: (elemento: T, indice: number) => React.ReactNode;
  chiave: (elemento: T) => string;
}

function Lista<T>({ elementi, renderElemento, chiave }: ListaProps<T>) {
  return (
    <ul>
      {elementi.map((elemento, i) => (
        <li key={chiave(elemento)}>{renderElemento(elemento, i)}</li>
      ))}
    </ul>
  );
}

// Utilizzo
interface Prodotto {
  id: string;
  nome: string;
  prezzo: number;
}

function PaginaProdotti() {
  const prodotti: Prodotto[] = [
    { id: "1", nome: "Laptop", prezzo: 999 },
    { id: "2", nome: "Mouse", prezzo: 29 }
  ];

  return (
    <Lista
      elementi={prodotti}
      chiave={(p) => p.id}
      renderElemento={(p) => (
        <span>{p.nome} - {p.prezzo} EUR</span>
      )}
    />
  );
}
```

---

## TypeScript con Node.js

### Setup e Configurazione

```bash
# Inizializzazione progetto
mkdir mio-server && cd mio-server
npm init -y

# Installazione TypeScript e tipi Node
npm install --save-dev typescript @types/node

# Generazione tsconfig.json
npx tsc --init
```

Configurazione `tsconfig.json` ottimizzata per Node.js:

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "sourceMap": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### Tipizzazione Express e Fastify

```typescript
// === Express ===
import express, { Request, Response, NextFunction } from "express";

interface CreaUtenteBody {
  nome: string;
  email: string;
}

interface UtenteParams {
  id: string;
}

interface RispostaUtente {
  id: string;
  nome: string;
  email: string;
}

const app = express();
app.use(express.json());

app.post(
  "/api/utenti",
  (req: Request<{}, RispostaUtente, CreaUtenteBody>, res: Response<RispostaUtente>) => {
    const { nome, email } = req.body;
    const nuovoUtente: RispostaUtente = {
      id: crypto.randomUUID(),
      nome,
      email
    };
    res.status(201).json(nuovoUtente);
  }
);

app.get(
  "/api/utenti/:id",
  (req: Request<UtenteParams>, res: Response<RispostaUtente>) => {
    const { id } = req.params;
    // logica di recupero utente
    res.json({ id, nome: "Marco", email: "marco@esempio.it" });
  }
);

// Middleware per gestione errori tipizzato
interface ErroreAPI extends Error {
  statusCode: number;
  dettagli?: string;
}

app.use((err: ErroreAPI, req: Request, res: Response, next: NextFunction) => {
  const stato = err.statusCode || 500;
  res.status(stato).json({
    errore: err.message,
    dettagli: err.dettagli
  });
});

app.listen(3000, () => console.log("Server avviato sulla porta 3000"));
```

```typescript
// === Fastify ===
import Fastify, { FastifyRequest, FastifyReply } from "fastify";

const server = Fastify({ logger: true });

interface CreaOrdineBody {
  prodottoId: string;
  quantita: number;
}

interface OrdineParams {
  id: string;
}

server.post<{ Body: CreaOrdineBody }>(
  "/api/ordini",
  async (request, reply) => {
    const { prodottoId, quantita } = request.body; // completamente tipizzato
    reply.code(201).send({ id: "ord-1", prodottoId, quantita });
  }
);

server.get<{ Params: OrdineParams }>(
  "/api/ordini/:id",
  async (request, reply) => {
    const { id } = request.params; // tipo: string
    reply.send({ id, stato: "confermato" });
  }
);

server.listen({ port: 3000 });
```

### Strumenti di Sviluppo: ts-node e tsx

Per eseguire TypeScript direttamente senza compilazione manuale:

```bash
# ts-node — il classico
npm install --save-dev ts-node
npx ts-node src/app.ts

# tsx — alternativa moderna e piu veloce (basata su esbuild)
npm install --save-dev tsx
npx tsx src/app.ts

# tsx in modalita watch
npx tsx watch src/app.ts
```

### Compilazione per Produzione

```jsonc
// package.json
{
  "scripts": {
    "dev": "tsx watch src/app.ts",
    "build": "tsc",
    "start": "node dist/app.js",
    "typecheck": "tsc --noEmit",
    "clean": "rm -rf dist"
  }
}
```

La strategia raccomandata per la produzione e compilare con `tsc` e servire il JavaScript risultante con `node`. L'uso di `ts-node` o `tsx` in produzione e sconsigliato per ragioni di performance e di overhead all'avvio.

---

## Best Practices

### 1. Attivare Sempre la Strict Mode

Configurare `"strict": true` nel `tsconfig.json` e la singola azione piu importante per ottenere il massimo beneficio da TypeScript. La strict mode attiva una serie di controlli che catturano la maggior parte degli errori comuni. Non disattivare mai le singole flag strict a meno che non ci sia una ragione tecnica documentata e temporanea.

### 2. Evitare `any`, Preferire `unknown`

Il tipo `any` disabilita completamente il type checking, rendendo inutile l'uso di TypeScript. Quando il tipo di un valore e veramente sconosciuto, usare `unknown` e poi restringere il tipo con type guards. Se si eredita codice pieno di `any`, migrare progressivamente verso tipi specifici o almeno verso `unknown`. Configurare la regola ESLint `@typescript-eslint/no-explicit-any` come errore per impedire l'introduzione accidentale di nuovi `any`.

### 3. Sfruttare la Type Inference

Non annotare cio che TypeScript puo dedurre autonomamente. Le annotazioni ridondanti aggiungono rumore visivo senza migliorare la sicurezza dei tipi. Annotare esplicitamente i parametri delle funzioni (obbligatorio), i valori di ritorno delle funzioni esportate (raccomandato per chiarezza dell'API pubblica) e le variabili il cui tipo non e ovvio dall'inizializzazione. Lasciare che il compilatore inferisca il resto.

### 4. Usare Discriminated Unions per Modellare lo Stato

Invece di combinazioni di flag booleani (`isLoading`, `isError`, `hasData`), modellare gli stati dell'applicazione come discriminated unions. Questo approccio rende impossibile rappresentare stati invalidi e permette al compilatore di verificare che tutti i casi siano gestiti. E particolarmente utile per le macchine a stati, le risposte API e i flussi di lavoro multi-step.

### 5. Preferire l'Immutabilita

Usare `readonly` per le proprieta che non dovrebbero cambiare, `ReadonlyArray<T>` o `readonly T[]` per array che non dovrebbero essere modificati, e `as const` per creare tipi literal profondamente immutabili. L'immutabilita previene un'intera categoria di bug legati a mutazioni inattese e rende il codice piu prevedibile e facile da ragionare.

### 6. Validare i Dati ai Confini dell'Applicazione

TypeScript garantisce la correttezza dei tipi solo a compile-time. I dati che provengono dall'esterno (API, input utente, file, variabili d'ambiente) non hanno alcuna garanzia di tipo. Utilizzare librerie come Zod, Valibot, o ArkType per validare questi dati a runtime e derivare automaticamente i tipi TypeScript dagli schemi di validazione. Questo crea un "ponte" sicuro tra il mondo esterno non tipizzato e il codice interno completamente tipizzato.

### 7. Usare i Tipi per Documentare le Intenzioni

Creare type alias significativi anche per tipi semplici quando aggiungono chiarezza semantica. Un tipo `type EmailAddress = string` non aggiunge sicurezza a livello di tipi, ma documenta l'intenzione. Per una sicurezza effettiva, combinare type alias con branded types. Nomi di tipi ben scelti rendono il codice auto-documentante e riducono la necessita di commenti esplicativi.

### 8. Scrivere Type Guard Riutilizzabili

Centralizzare la logica di narrowing in funzioni type guard (`function isX(val): val is X`) riutilizzabili piuttosto che ripetere controlli `typeof` e `instanceof` in tutto il codice. Le type guard personalizzate rendono il codice piu leggibile, mantengono la logica di validazione in un unico punto e si integrano perfettamente con il sistema di tipi di TypeScript.

### 9. Mantenere i Tipi Vicini al Codice che li Usa

Evitare file monolitici `types.ts` che contengono tutti i tipi del progetto. Collocare le definizioni di tipo vicino al codice che le utilizza: i tipi di un componente nello stesso file o nella stessa directory del componente. Esportare solo i tipi che fanno parte dell'interfaccia pubblica di un modulo. Questo migliora la manutenibilita, riduce le dipendenze circolari e rende piu facile trovare e aggiornare i tipi quando il codice cambia.

### 10. Aggiornare TypeScript Regolarmente

Ogni nuova versione di TypeScript introduce miglioramenti al sistema di tipi, nuovi utility types, migliore inferenza e ottimizzazioni del compilatore. Aggiornare regolarmente (almeno ogni minor release) e adattare il codice per sfruttare le nuove funzionalita. Prima di ogni aggiornamento, compilare il progetto con la nuova versione usando `tsc --noEmit` per identificare eventuali breaking changes. Consultare le release notes ufficiali per comprendere cosa cambia e quali nuove possibilita si aprono.

---

## Novita TypeScript 5.4 / 5.5 / 5.6

Le versioni 5.4, 5.5 e 5.6 di TypeScript, rilasciate tra marzo e settembre 2024, hanno introdotto miglioramenti significativi al sistema di tipi, alla control flow analysis e al supporto per le nuove API ECMAScript. Questa sezione approfondisce le funzionalita piu rilevanti che ogni sviluppatore TypeScript dovrebbe conoscere.

### TypeScript 5.4 — NoInfer e Closure Narrowing

#### NoInfer<T>

Il tipo utility `NoInfer<T>`, introdotto in TypeScript 5.4 (marzo 2024), risolve un problema annoso nell'inferenza dei generics. Quando un parametro di tipo generico appare in piu posizioni nella firma di una funzione, TypeScript raccoglie candidati di inferenza da tutte le posizioni. In alcuni casi questo comportamento e indesiderato, perche un parametro "secondario" contamina l'inferenza con tipi non voluti.

`NoInfer<T>` avvolge un tipo e segnala al compilatore di non utilizzare quella posizione come sito di inferenza:

```typescript
// PRIMA di NoInfer — problema
function creaLista<T>(elementi: T[], predefinito: T): T[] {
  return [...elementi, predefinito];
}

// TypeScript inferisce T come "rosso" | "verde" | "blu" | "giallo"
// perche "giallo" e un candidato valido dalla posizione `predefinito`
creaLista(["rosso", "verde", "blu"], "giallo"); // nessun errore

// DOPO — con NoInfer
function creaListaSicura<T>(elementi: T[], predefinito: NoInfer<T>): T[] {
  return [...elementi, predefinito];
}

// Errore: "giallo" non e assegnabile a "rosso" | "verde" | "blu"
creaListaSicura(["rosso", "verde", "blu"], "giallo");
```

Il caso d'uso principale si presenta con funzioni che accettano un insieme di valori e un valore predefinito che deve appartenere a quell'insieme:

```typescript
function creaComponente<C extends string>(
  colori: C[],
  colorePredefinito: NoInfer<C>
): { colori: C[]; predefinito: C } {
  return { colori, predefinito: colorePredefinito };
}

// OK — "primario" e tra i colori forniti
creaComponente(["primario", "secondario", "accento"], "primario");

// Errore — "sconosciuto" non e tra i colori forniti
creaComponente(["primario", "secondario", "accento"], "sconosciuto");
```

#### Narrowing nelle Closure

TypeScript 5.4 ha migliorato significativamente il narrowing nelle closure. Nelle versioni precedenti, il tipo ristretto di una variabile all'interno di una closure veniva spesso perso se la variabile era stata riassegnata in qualsiasi punto del codice circostante, anche se la riassegnazione avveniva in un ramo logicamente irraggiungibile dopo la closure.

```typescript
function elabora(url: string | undefined) {
  if (url !== undefined) {
    // Prima di TS 5.4: il narrowing poteva essere perso nelle callback successive
    // Da TS 5.4: il compilatore traccia correttamente che `url` e `string` qui
    const callback = () => {
      console.log(url.toUpperCase()); // OK — url e narrowed a string
    };
    setTimeout(callback, 100);
  }
}
```

### TypeScript 5.5 — Predicati di Tipo Inferiti

#### Inferred Type Predicates

La funzionalita piu significativa di TypeScript 5.5 (giugno 2024) e l'inferenza automatica dei predicati di tipo. Nelle versioni precedenti, per sfruttare il type narrowing con funzioni di filtro, era necessario annotare esplicitamente il tipo di ritorno come predicato (`value is Type`):

```typescript
// PRIMA di TS 5.5 — annotazione manuale obbligatoria
function isDefinito<T>(valore: T | null | undefined): valore is T {
  return valore !== null && valore !== undefined;
}

const misti: (string | null)[] = ["ciao", null, "mondo", null];
const definiti = misti.filter(isDefinito); // tipo: string[]
```

Da TypeScript 5.5, il compilatore inferisce automaticamente il predicato quando una funzione soddisfa tre condizioni: (1) non ha un'annotazione esplicita del tipo di ritorno, (2) ha una singola istruzione `return` senza return impliciti, e (3) non muta il parametro:

```typescript
// DA TS 5.5 — il predicato viene inferito automaticamente
const definiti = misti.filter((v) => v !== null && v !== undefined);
// TypeScript inferisce automaticamente: (v) => v is string
// tipo risultante: string[]
```

Questo elimina centinaia di righe di boilerplate in progetti reali. Le funzioni di filtro su array ora funzionano correttamente senza type guard espliciti:

```typescript
interface Ordine {
  id: string;
  stato: "attivo" | "annullato";
  totale: number;
}

const ordini: (Ordine | undefined)[] = fetchOrdini();

// TS 5.5 inferisce il predicato — il tipo risultante e Ordine[]
const ordiniValidi = ordini.filter((o) => o !== undefined);

// Anche con condizioni piu complesse
const ordiniAttivi = ordiniValidi.filter((o) => o.stato === "attivo");
```

#### Costanti negli Accessi Indicizzati

TypeScript 5.5 ha migliorato la control flow analysis per gli accessi indicizzati con chiavi costanti. Il narrowing ora funziona correttamente quando si accede a proprieta di oggetti tramite costanti:

```typescript
const chiave = "stato" as const;

interface Risposta {
  stato: "successo" | "errore";
  dati?: unknown;
}

function processa(risposta: Risposta) {
  if (risposta[chiave] === "successo") {
    // TypeScript sa che risposta.stato === "successo" qui
    console.log("Operazione completata");
  }
}
```

#### Espressioni Regolari Controllate

TypeScript 5.5 ha introdotto il controllo sintattico di base delle espressioni regolari. Il compilatore ora segnala errori per espressioni regolari sintatticamente invalide che in precedenza venivano scoperte solo a runtime:

```typescript
// TS 5.5 segnala errore — parentesi non bilanciate
const regex = /([a-z]+/; // Errore: espressione regolare non valida

// TS 5.5 segnala errore — quantificatore invalido
const regex2 = /a{,}/; // Errore
```

### TypeScript 5.6 — Controlli Nullish/Truthy e Iterator Helpers

#### Controlli Nullish e Truthy Non Validi

TypeScript 5.6 (settembre 2024) ha introdotto un controllo che segnala come errore le espressioni in cui il compilatore puo determinare sintatticamente che un controllo truthy o nullish produrra sempre lo stesso risultato. Questo cattura intere classi di bug logici:

```typescript
// TS 5.6 segnala errore — la condizione e sempre truthy
if (/[a-z]/) {
  // Un oggetto regex e sempre truthy — probabilmente si intendeva .test()
}

// Corretto
if (/[a-z]/.test(input)) {
  // ...
}

// TS 5.6 segnala errore — la funzione e sempre truthy
function esegui(callback: () => void) {
  if (callback) {   // Errore: la funzione e sempre truthy
    callback();     // Probabilmente si intendeva callback()
  }
}

// Eccezioni: true, false, 0, 1 sono ancora permessi
// perche pattern come while (true) sono idiomatici
```

#### Iterator Helpers

TypeScript 5.6 ha aggiunto il supporto per i nuovi metodi sugli iteratori introdotti dalla proposta ECMAScript Iterator Helpers. Questi metodi — `map`, `filter`, `take`, `drop`, `flatMap`, `reduce`, `forEach`, `some`, `every`, `find`, `toArray` — sono disponibili su tutti gli iteratori built-in senza necessita di convertirli prima in array:

```typescript
// Prima: conversione in array necessaria
function* genera(): Generator<number> {
  yield 1; yield 2; yield 3; yield 4; yield 5;
}

// Vecchio approccio
const risultato = [...genera()]
  .filter((n) => n % 2 === 0)
  .map((n) => n * 10);

// Con Iterator Helpers (TS 5.6+)
const risultato2 = genera()
  .filter((n) => n % 2 === 0)
  .map((n) => n * 10)
  .toArray(); // [20, 40]

// Funziona anche con Map e Set
const mappa = new Map([["a", 1], ["b", 2], ["c", 3]]);
const chiavi = mappa.keys().filter((k) => k !== "b").toArray(); // ["a", "c"]

// take e drop per paginazione sugli iteratori
const primiTre = genera().take(3).toArray(); // [1, 2, 3]
const dopoDue = genera().drop(2).toArray();  // [3, 4, 5]
```

TypeScript ha rinominato il tipo `BuiltinIterator` in `IteratorObject` e ha introdotto sottotipi specializzati come `ArrayIterator`, `MapIterator`, `SetIterator` e `StringIterator`, ognuno con i propri parametri di tipo per una tipizzazione piu precisa.

#### Il Tipo `--noUncheckedSideEffectImports`

TypeScript 5.6 ha aggiunto la flag `--noUncheckedSideEffectImports` che verifica che gli import side-effect (`import "./modulo"`) facciano riferimento a file effettivamente esistenti. Nelle versioni precedenti, se il file importato non esisteva, TypeScript non segnalava alcun errore.

---

## Sistema di Tipi Avanzato — Approfondimento

Come introdotto nelle sezioni [Interfacce e Type Alias](#interfacce-e-type-alias) e [Generics](#generics), il sistema di tipi di TypeScript e un linguaggio di programmazione a se stante, Turing-complete, valutato interamente a compile-time. Questa sezione esplora le sue capacita piu avanzate.

### Variadic Tuple Types

I variadic tuple types, introdotti in TypeScript 4.0 e perfezionati nelle versioni successive, permettono di manipolare tuple con un numero variabile di elementi tramite l'operatore spread (`...`) a livello di tipo:

```typescript
// Concatenazione di tuple a livello di tipo
type Concatena<A extends unknown[], B extends unknown[]> = [...A, ...B];

type Risultato = Concatena<[string, number], [boolean]>;
// tipo: [string, number, boolean]

// Funzione che concatena due tuple preservando i tipi
function concatena<A extends unknown[], B extends unknown[]>(
  a: [...A],
  b: [...B]
): [...A, ...B] {
  return [...a, ...b];
}

const r = concatena([1, "due"] as [number, string], [true] as [boolean]);
// tipo: [number, string, boolean]

// Pattern: inserire un elemento in una posizione specifica
type InserisciInizio<T, Tuple extends unknown[]> = [T, ...Tuple];
type InserisciFine<T, Tuple extends unknown[]> = [...Tuple, T];

type ConPrefisso = InserisciInizio<"prefisso", [number, boolean]>;
// tipo: ["prefisso", number, boolean]
```

I variadic tuple types sono particolarmente utili per tipizzare funzioni con argomenti variabili come `bind`, `call` e funzioni di composizione:

```typescript
// Tipizzazione di una funzione curry parziale
type Testa<T extends unknown[]> = T extends [infer H, ...unknown[]] ? H : never;
type Coda<T extends unknown[]> = T extends [unknown, ...infer R] ? R : never;

type PrimoTipo = Testa<[string, number, boolean]>; // string
type Resto = Coda<[string, number, boolean]>;       // [number, boolean]

// Funzione pipe tipizzata con variadic tuples
function pipe<T, Fns extends ((arg: any) => any)[]>(
  valore: T,
  ...funzioni: Fns
): ReturnType<Fns[number]> {
  return funzioni.reduce((acc, fn) => fn(acc), valore as any);
}
```

### Conditional Types Avanzati

Oltre alla sintassi base `T extends U ? X : Y` introdotta nella sezione [Conditional Types con Generics](#conditional-types-con-generics-infer), i tipi condizionali supportano pattern di inferenza multipla e ricorsione:

```typescript
// Inferenza multipla nella stessa condizione
type TipoFunzione<T> = T extends (...args: infer A) => infer R
  ? { parametri: A; ritorno: R }
  : never;

type Info = TipoFunzione<(nome: string, eta: number) => boolean>;
// { parametri: [nome: string, eta: number]; ritorno: boolean }

// Conditional type distributivo su union
type SoloStringhe<T> = T extends string ? T : never;

type Filtrato = SoloStringhe<"a" | 42 | "b" | true>;
// "a" | "b" — i non-string vengono eliminati

// Disabilitare la distribuzione avvolgendo in tuple
type NonDistributivo<T> = [T] extends [string] ? "stringa" : "altro";
type TestA = NonDistributivo<string | number>; // "altro" (non distribuito)
type TestB = SoloStringhe<string | number>;     // string (distribuito)

// Ricorsione nei conditional types
type AppiattisciArray<T> = T extends Array<infer U>
  ? AppiattisciArray<U>
  : T;

type Profondo = AppiattisciArray<number[][][]>; // number
type Semplice = AppiattisciArray<string>;        // string
```

### Mapped Types con Remapping delle Chiavi

Da TypeScript 4.1, i mapped types supportano il remapping delle chiavi tramite la clausola `as`, che permette di rinominare, filtrare o trasformare le chiavi durante l'iterazione:

```typescript
// Rinominare le chiavi aggiungendo un prefisso
type ConPrefisso<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K];
};

interface Utente {
  nome: string;
  email: string;
}

type UtenteConGet = ConPrefisso<Utente, "get">;
// { getNome: string; getEmail: string }

// Filtrare chiavi per tipo di valore
type SoloMetodi<T> = {
  [K in keyof T as T[K] extends Function ? K : never]: T[K];
};

interface Servizio {
  nome: string;
  versione: number;
  avvia(): void;
  ferma(): void;
}

type MetodiServizio = SoloMetodi<Servizio>;
// { avvia: () => void; ferma: () => void }

// Rimuovere proprieta readonly
type Mutabile<T> = {
  -readonly [K in keyof T]: T[K];
};

// Rimuovere l'opzionalita
type Obbligatorio<T> = {
  [K in keyof T]-?: T[K];
};
```

### Template Literal Types Avanzati

Oltre alla generazione combinatoria mostrata nella sezione precedente, i template literal types supportano pattern matching ricorsivo su stringhe a livello di tipo:

```typescript
// Parsing di percorsi URL con estrazione dei parametri
type EstraiParametriURL<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? { [K in Param | keyof EstraiParametriURL<Rest>]:
        K extends keyof EstraiParametriURL<Rest>
          ? EstraiParametriURL<Rest>[K]
          : string }
    : T extends `${string}:${infer Param}`
      ? { [K in Param]: string }
      : {};

type Params = EstraiParametriURL<"/api/utenti/:utenteId/ordini/:ordineId">;
// { utenteId: string; ordineId: string }

// Conversione CamelCase a snake_case a livello di tipo
type CamelASnake<S extends string> =
  S extends `${infer Primo}${infer Resto}`
    ? Primo extends Uppercase<Primo>
      ? `_${Lowercase<Primo>}${CamelASnake<Resto>}`
      : `${Primo}${CamelASnake<Resto>}`
    : S;

type Convertito = CamelASnake<"nomeUtente">; // "nome_utente"

// Tipi built-in per manipolazione stringhe
type Maiuscolo = Uppercase<"ciao">;       // "CIAO"
type Minuscolo = Lowercase<"MONDO">;      // "mondo"
type Capitalizzato = Capitalize<"test">;   // "Test"
type Decapitalizzato = Uncapitalize<"Test">; // "test"

// Generazione automatica di nomi di eventi dal tipo di un modello
type NomiEventi<T> = {
  [K in keyof T as `on${Capitalize<string & K>}Change`]: (
    vecchioValore: T[K],
    nuovoValore: T[K]
  ) => void;
};

interface Impostazioni {
  tema: string;
  lingua: string;
  notifiche: boolean;
}

type EventiImpostazioni = NomiEventi<Impostazioni>;
// {
//   onTemaChange: (vecchio: string, nuovo: string) => void;
//   onLinguaChange: (vecchio: string, nuovo: string) => void;
//   onNotificheChange: (vecchio: boolean, nuovo: boolean) => void;
// }
```

---

## Type Narrowing — Approfondimento

Come introdotto nella sezione [Type Narrowing](#type-narrowing), TypeScript restringe progressivamente il tipo delle variabili attraverso l'analisi del flusso di controllo. Questa sezione esplora le tecniche avanzate di narrowing.

### Assertion Functions

Le assertion functions sono funzioni che, se terminano senza lanciare un'eccezione, garantiscono al compilatore che una condizione e vera. A differenza dei type predicate (`value is Type`), le assertion functions usano la sintassi `asserts`:

```typescript
// Assertion function — se non lancia, param e string
function assertIsString(valore: unknown): asserts valore is string {
  if (typeof valore !== "string") {
    throw new TypeError(`Atteso string, ricevuto ${typeof valore}`);
  }
}

function elabora(input: unknown): string {
  assertIsString(input);
  // Da qui in poi, TypeScript sa che input e string
  return input.toUpperCase();
}

// Assertion function con condizione generica
function assertDefined<T>(
  valore: T | null | undefined,
  messaggio?: string
): asserts valore is T {
  if (valore === null || valore === undefined) {
    throw new Error(messaggio ?? "Valore non definito");
  }
}

const config = getConfig(); // tipo: Config | undefined
assertDefined(config, "Configurazione mancante");
// Da qui: config e Config (senza undefined)
console.log(config.porta);
```

Le assertion functions sono particolarmente utili per le fasi di inizializzazione e validazione dove un fallimento deve interrompere l'esecuzione:

```typescript
function assertNonVuoto<T>(
  array: T[],
  messaggio?: string
): asserts array is [T, ...T[]] {
  if (array.length === 0) {
    throw new Error(messaggio ?? "Array vuoto");
  }
}

const risultati = cercaUtenti(query); // tipo: Utente[]
assertNonVuoto(risultati, "Nessun utente trovato");
// Da qui: risultati e [Utente, ...Utente[]] — ha almeno un elemento
const primo = risultati[0]; // tipo: Utente (non Utente | undefined)
```

### Exhaustive Checking Approfondito

Come mostrato brevemente nella sezione [Pattern Avanzati](#exhaustive-checking-con-never), l'exhaustive checking con `never` garantisce che tutti i rami di una discriminated union siano gestiti. Questa tecnica diventa indispensabile quando l'unione si evolve nel tempo:

```typescript
// Funzione helper per exhaustive checks con messaggio di errore utile
function assertNever(valore: never, messaggio?: string): never {
  throw new Error(
    messaggio ?? `Caso non gestito: ${JSON.stringify(valore)}`
  );
}

type AzioneUI =
  | { tipo: "apri_modale"; contenuto: string }
  | { tipo: "chiudi_modale" }
  | { tipo: "mostra_notifica"; messaggio: string; livello: "info" | "errore" }
  | { tipo: "naviga"; percorso: string };

function riduci(stato: StatoUI, azione: AzioneUI): StatoUI {
  switch (azione.tipo) {
    case "apri_modale":
      return { ...stato, modale: { aperta: true, contenuto: azione.contenuto } };
    case "chiudi_modale":
      return { ...stato, modale: { aperta: false, contenuto: "" } };
    case "mostra_notifica":
      return { ...stato, notifica: { messaggio: azione.messaggio, livello: azione.livello } };
    case "naviga":
      return { ...stato, percorsoCorrente: azione.percorso };
    default:
      // Se si aggiunge un nuovo tipo di azione senza gestirlo qui,
      // TypeScript segnala un errore a compile-time
      return assertNever(azione);
  }
}
```

### Narrowing con `satisfies`

L'operatore `satisfies`, introdotto in TypeScript 4.9, verifica che un valore sia conforme a un tipo senza allargare il tipo inferito. Questo e utile per mantenere i literal types preservando al contempo la validazione:

```typescript
type Colore = { r: number; g: number; b: number } | string;
type Palette = Record<string, Colore>;

// Con annotazione di tipo — i literal types vengono persi
const palette1: Palette = {
  primario: { r: 0, g: 100, b: 200 },
  secondario: "#FF5733"
};
// palette1.primario e di tipo Colore (string | {r,g,b})

// Con satisfies — i literal types vengono preservati
const palette2 = {
  primario: { r: 0, g: 100, b: 200 },
  secondario: "#FF5733"
} satisfies Palette;

// palette2.primario e di tipo { r: number; g: number; b: number }
// palette2.secondario e di tipo string
// TypeScript conosce la forma esatta di ogni proprieta
palette2.primario.r; // OK — TypeScript sa che e un oggetto, non una stringa
```

### Discriminated Unions con Piu Discriminanti

Le discriminated unions non sono limitate a un singolo campo discriminante. Si possono usare combinazioni di campi per creare discriminanti composti:

```typescript
type RispostaHTTP =
  | { stato: "successo"; codice: 200 | 201; dati: unknown }
  | { stato: "redirect"; codice: 301 | 302; destinazione: string }
  | { stato: "errore_client"; codice: 400 | 401 | 403 | 404; messaggio: string }
  | { stato: "errore_server"; codice: 500 | 502 | 503; dettagli: string; retry: boolean };

function gestisciRisposta(risposta: RispostaHTTP): void {
  switch (risposta.stato) {
    case "successo":
      console.log("Dati:", risposta.dati);
      break;
    case "redirect":
      console.log("Redirect a:", risposta.destinazione);
      break;
    case "errore_client":
      if (risposta.codice === 401) {
        console.log("Non autenticato");
      } else if (risposta.codice === 403) {
        console.log("Non autorizzato");
      } else {
        console.log("Errore:", risposta.messaggio);
      }
      break;
    case "errore_server":
      console.log("Errore server:", risposta.dettagli);
      if (risposta.retry) {
        console.log("Riprovo...");
      }
      break;
  }
}
```

---

## Generics Avanzati

Come introdotto nella sezione [Generics](#generics), i parametri di tipo rendono il codice riutilizzabile e type-safe. Questa sezione esplora tecniche avanzate di inferenza, vincoli e pattern architetturali.

### Siti di Inferenza e Ordine di Priorita

Quando un parametro di tipo appare in piu posizioni, TypeScript raccoglie candidati di inferenza da tutti i "siti" e cerca di trovare un tipo comune. Comprendere l'ordine di priorita e fondamentale per controllare l'inferenza:

```typescript
// T viene inferito dal primo argomento, non dal secondo
function fondiArray<T>(sorgente: T[], destinazione: T[]): T[] {
  return [...sorgente, ...destinazione];
}

// TypeScript inferisce T come string | number (unione di entrambi i candidati)
fondiArray(["a", "b"], [1, 2]); // tipo: (string | number)[]

// Per forzare T dal solo primo argomento, usare NoInfer sul secondo
function fondiConPriorita<T>(sorgente: T[], destinazione: NoInfer<T>[]): T[] {
  return [...sorgente, ...destinazione];
}

// Errore: number non e assegnabile a string
fondiConPriorita(["a", "b"], [1, 2]);
```

### Constrained Identity Pattern

Questo pattern combina un vincolo generico con il tipo esatto inferito per ottenere sia la validazione che il narrowing:

```typescript
// Pattern: constrained identity
function definisciConfig<T extends {
  host: string;
  porta: number;
  ssl?: boolean;
  timeout?: number;
}>(config: T): T {
  return config;
}

// Il tipo ritornato preserva i literal types esatti
const config = definisciConfig({
  host: "localhost",
  porta: 3000,
  ssl: true
});
// tipo: { host: "localhost"; porta: 3000; ssl: true }
// NON: { host: string; porta: number; ssl?: boolean }
```

Questo pattern e usato ampiamente nei framework (Next.js `defineConfig`, Vite `defineConfig`, ecc.) per fornire autocompletamento e validazione senza perdere i tipi esatti.

### Generics Ricorsivi

I tipi generici possono essere definiti ricorsivamente per modellare strutture dati ad albero:

```typescript
// Tipo JSON ricorsivo
type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [chiave: string]: JsonValue };

// Albero generico
interface NodoAlbero<T> {
  valore: T;
  figli: NodoAlbero<T>[];
}

// Traversal type-safe
function cercaNodoDepthFirst<T>(
  nodo: NodoAlbero<T>,
  predicato: (valore: T) => boolean
): NodoAlbero<T> | undefined {
  if (predicato(nodo.valore)) return nodo;
  for (const figlio of nodo.figli) {
    const trovato = cercaNodoDepthFirst(figlio, predicato);
    if (trovato) return trovato;
  }
  return undefined;
}

// DeepReadonly ricorsivo
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object
    ? T[K] extends Function
      ? T[K]
      : DeepReadonly<T[K]>
    : T[K];
};
```

### Higher-Kinded Types — Workaround

TypeScript non supporta nativamente i Higher-Kinded Types (HKT), ovvero la capacita di parametrizzare un tipo con un costruttore di tipo (come `Functor<F>` dove `F` puo essere `Array`, `Promise`, `Option`, ecc.). Tuttavia, si puo simulare questo pattern tramite l'augmentation delle interfacce e un registro di tipi:

```typescript
// Passo 1: Definire un'interfaccia "registro" vuota che verra estesa
interface RegistroTipi<A = unknown> {}

// Passo 2: Definire un alias per estrarre il tipo dal registro
type Kind<F extends keyof RegistroTipi, A> = RegistroTipi<A>[F];

// Passo 3: Registrare costruttori di tipo concreti tramite augmentation
interface RegistroTipi<A> {
  Array: A[];
  Promise: Promise<A>;
  Nullable: A | null;
}

// Passo 4: Usare Kind per scrivere funzioni "polimorfiche"
// su costruttori di tipo
type Mappabile<F extends keyof RegistroTipi> = {
  map: <A, B>(fa: Kind<F, A>, f: (a: A) => B) => Kind<F, B>;
};

// Implementazione per Array
const mappabileArray: Mappabile<"Array"> = {
  map: (fa, f) => fa.map(f)
};

// Implementazione per Nullable
const mappabileNullable: Mappabile<"Nullable"> = {
  map: (fa, f) => (fa === null ? null : f(fa))
};
```

Questa tecnica e utilizzata in librerie come Effect-TS per costruire astrazioni funzionali avanzate. Va usata con cautela: aggiunge complessita significativa e non e necessaria per la maggior parte dei progetti.

---

## Utility Types — Approfondimento

Come introdotto nella sezione [Utility Types Principali](#utility-types-principali), TypeScript include numerosi tipi utility built-in. Questa sezione approfondisce quelli meno noti e mostra come crearne di personalizzati.

### Awaited<T>

Introdotto in TypeScript 4.5, `Awaited<T>` estrae ricorsivamente il tipo "risolto" da un `Promise`, indipendentemente dal livello di annidamento:

```typescript
type A = Awaited<Promise<string>>;                // string
type B = Awaited<Promise<Promise<number>>>;        // number
type C = Awaited<boolean | Promise<string>>;       // boolean | string

// Caso d'uso: tipizzare il risultato di Promise.all
async function caricaDati() {
  const [utente, ordini, preferenze] = await Promise.all([
    fetchUtente(),      // Promise<Utente>
    fetchOrdini(),      // Promise<Ordine[]>
    fetchPreferenze()   // Promise<Preferenze>
  ]);
  // TypeScript usa Awaited internamente per dedurre:
  // utente: Utente, ordini: Ordine[], preferenze: Preferenze
}
```

### Extract e Exclude — Pattern Avanzati

`Extract<T, U>` e `Exclude<T, U>` operano su union types tramite distribuzione condizionale e sono strumenti potenti per filtrare tipi:

```typescript
type Evento =
  | { tipo: "click"; x: number; y: number }
  | { tipo: "input"; valore: string }
  | { tipo: "scroll"; posizione: number }
  | { tipo: "resize"; larghezza: number; altezza: number };

// Estrarre solo gli eventi con coordinate
type EventiConPosizione = Extract<Evento, { x: number }>;
// { tipo: "click"; x: number; y: number }

// Escludere eventi di tipo specifico
type EventiSenzaScroll = Exclude<Evento, { tipo: "scroll" }>;
// Click | Input | Resize

// Estrarre i nomi dei tipi di evento
type NomeEvento = Evento["tipo"];
// "click" | "input" | "scroll" | "resize"

// Estrarre solo i nomi degli eventi che hanno una proprietà 'valore'
type EventiConValore = Extract<Evento, { valore: unknown }>["tipo"];
// "input"
```

### ReturnType e Parameters — Applicazioni Reali

```typescript
// ReturnType per derivare tipi da funzioni esistenti
function creaSessione(utenteId: string, ruolo: string) {
  return {
    id: crypto.randomUUID(),
    utenteId,
    ruolo,
    scadenza: new Date(Date.now() + 3600_000),
    attiva: true
  };
}

// Derivare il tipo senza duplicarlo
type Sessione = ReturnType<typeof creaSessione>;
// { id: string; utenteId: string; ruolo: string; scadenza: Date; attiva: boolean }

// Parameters per estrarre i tipi degli argomenti
type ParamSessione = Parameters<typeof creaSessione>;
// [utenteId: string, ruolo: string]

// ConstructorParameters per le classi
class Connessione {
  constructor(
    public host: string,
    public porta: number,
    public opzioni?: { ssl: boolean; timeout: number }
  ) {}
}

type ParamConnessione = ConstructorParameters<typeof Connessione>;
// [host: string, porta: number, opzioni?: { ssl: boolean; timeout: number }]
```

### Utility Types Personalizzati

I tipi utility personalizzati piu comuni nei progetti reali:

```typescript
// DeepPartial — rende tutte le proprieta opzionali ricorsivamente
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object
    ? T[K] extends Function
      ? T[K]
      : DeepPartial<T[K]>
    : T[K];
};

// Prettify — "appiattisce" l'intersezione di tipi per leggibilita
type Prettify<T> = {
  [K in keyof T]: T[K];
} & {};

type Complesso = { a: string } & { b: number } & { c: boolean };
type Leggibile = Prettify<Complesso>;
// Mostra: { a: string; b: number; c: boolean } (non l'intersezione)

// KeysOfType — estrae le chiavi il cui valore e di un tipo specifico
type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];

interface Modello {
  id: string;
  nome: string;
  attivo: boolean;
  contatore: number;
  visibile: boolean;
}

type ChiaviBooleane = KeysOfType<Modello, boolean>;
// "attivo" | "visibile"

type ChiaviStringa = KeysOfType<Modello, string>;
// "id" | "nome"

// StrictOmit — versione piu sicura di Omit che verifica le chiavi
type StrictOmit<T, K extends keyof T> = Omit<T, K>;
// A differenza di Omit standard, segnala errore se K non e una chiave di T

// RequireAtLeastOne — almeno una delle chiavi specificate deve essere presente
type RequireAtLeastOne<T, Keys extends keyof T = keyof T> =
  Pick<T, Exclude<keyof T, Keys>> &
  { [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>> }[Keys];

// XOR — esattamente uno dei due tipi
type XOR<T, U> =
  | (T & { [K in Exclude<keyof U, keyof T>]?: never })
  | (U & { [K in Exclude<keyof T, keyof U>]?: never });
```

---

## File di Dichiarazione e Augmentation

Come introdotto nella sezione [File di Dichiarazione (.d.ts)](#file-di-dichiarazione-dts), i file `.d.ts` descrivono la forma di librerie JavaScript senza implementazione. Questa sezione approfondisce le tecniche avanzate di dichiarazione e augmentation.

### Struttura di un File .d.ts

I file di dichiarazione contengono solo firme di tipo: interfacce, tipi, firme di funzione, dichiarazioni di variabili e moduli, ma nessuna implementazione:

```typescript
// libreria-esterna.d.ts

// Dichiarazione di funzione
declare function formattaValuta(importo: number, valuta: string): string;

// Dichiarazione di variabile
declare const VERSIONE: string;

// Dichiarazione di classe
declare class Logger {
  constructor(prefisso: string);
  info(messaggio: string): void;
  errore(messaggio: string, errore?: Error): void;
  warn(messaggio: string): void;
}

// Dichiarazione di enum
declare enum Ambiente {
  Sviluppo = "development",
  Produzione = "production",
  Test = "test"
}

// Dichiarazione di namespace (per librerie con struttura a oggetto)
declare namespace MiaLibreria {
  function inizializza(opzioni: OpzioniConfig): void;
  interface OpzioniConfig {
    debug: boolean;
    logLevel: "info" | "warn" | "error";
  }
}
```

### Module Augmentation

Il module augmentation permette di estendere i tipi di moduli esistenti senza modificarne il codice sorgente. Questo e essenziale per aggiungere proprieta personalizzate a librerie di terze parti:

```typescript
// express-augmentation.d.ts
// Aggiungere proprieta personalizzate a Express Request
import "express";

declare module "express" {
  interface Request {
    utente?: {
      id: string;
      ruolo: "admin" | "editor" | "viewer";
      token: string;
    };
    sessioneId?: string;
    lingua: "it" | "en" | "de" | "fr";
  }
}

// Ora nei route handler:
app.get("/profilo", (req: Request, res: Response) => {
  // req.utente e tipizzato correttamente
  if (req.utente?.ruolo === "admin") {
    // ...
  }
});
```

```typescript
// Estendere i tipi di una libreria di stato
declare module "zustand" {
  interface StoreApi<T> {
    persist: () => void;
    versione: number;
  }
}
```

### Global Augmentation

Il global augmentation estende lo scope globale per aggiungere variabili, interfacce o tipi disponibili ovunque senza importazione:

```typescript
// globali.d.ts
declare global {
  // Estendere l'interfaccia Window
  interface Window {
    __APP_CONFIG__: {
      apiUrl: string;
      versione: string;
      ambiente: "sviluppo" | "produzione";
    };
    dataLayer: Record<string, unknown>[];
  }

  // Aggiungere metodi a tipi built-in
  interface Array<T> {
    ultimo(): T | undefined;
  }

  // Variabili globali
  var __DEV__: boolean;
  var __BUILD_TIMESTAMP__: string;
}

// Necessario per rendere questo file un modulo
export {};
```

### Ambient Modules e Wildcard

Per importare risorse non-JavaScript (CSS, immagini, JSON), si dichiarano moduli ambient con pattern wildcard:

```typescript
// assets.d.ts
declare module "*.css" {
  const classi: { [chiave: string]: string };
  export default classi;
}

declare module "*.svg" {
  const contenuto: string;
  export default contenuto;
}

declare module "*.png" {
  const percorso: string;
  export default percorso;
}

declare module "*.module.css" {
  const classi: { readonly [chiave: string]: string };
  export default classi;
}

// Per file JSON (alternativa a resolveJsonModule)
declare module "*.json" {
  const valore: unknown;
  export default valore;
}
```

### Triple-Slash Directives

Le direttive triple-slash sono commenti speciali che il compilatore interpreta come istruzioni di preprocessing. Sono necessarie in contesti dove `import` non e disponibile (ad esempio nei file `.d.ts` globali):

```typescript
/// <reference types="node" />        — include i tipi di @types/node
/// <reference path="./altro.d.ts" /> — include un altro file di dichiarazione
/// <reference lib="dom" />           — include la libreria DOM

// Esempio: file di dichiarazione che dipende dai tipi di Node.js
/// <reference types="node" />

declare module "mia-libreria-server" {
  import { IncomingMessage, ServerResponse } from "http";

  export function creaServer(
    handler: (req: IncomingMessage, res: ServerResponse) => void
  ): void;
}
```

---

## Compilatore: Project References e Build Incrementali

Per i progetti di grandi dimensioni, la velocita di compilazione diventa critica. TypeScript offre due meccanismi complementari: le compilazioni incrementali e i project references.

### Compilazione Incrementale

La flag `incremental` abilita la compilazione incrementale, dove TypeScript salva uno snapshot del programma in un file di cache (`.tsbuildinfo`) e ricompila solo i file modificati nelle esecuzioni successive:

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "incremental": true,
    "tsBuildInfoFile": "./.tsbuildinfo" // percorso del file di cache
  }
}
```

Alla prima compilazione, TypeScript analizza tutti i file e genera il file `.tsbuildinfo` contenente dipendenze, hash dei file e informazioni di tipo. Nelle compilazioni successive, il compilatore confronta gli hash e ricompila solo cio che e cambiato, riducendo i tempi di build del 40-70% nei progetti di medie dimensioni.

### Project References

I project references permettono di suddividere un monorepo o un progetto di grandi dimensioni in sotto-progetti con dipendenze esplicite. Ogni sotto-progetto compila indipendentemente e viene ricostruito solo quando le sue dipendenze cambiano:

```jsonc
// tsconfig.json — progetto radice
{
  "references": [
    { "path": "./packages/common" },
    { "path": "./packages/server" },
    { "path": "./packages/client" }
  ],
  "files": [] // il progetto radice non compila file direttamente
}

// packages/common/tsconfig.json
{
  "compilerOptions": {
    "composite": true,        // OBBLIGATORIO per i project references
    "declaration": true,      // implicito con composite, ma esplicito per chiarezza
    "declarationMap": true,   // per navigazione Go-to-Definition tra progetti
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src"]
}

// packages/server/tsconfig.json
{
  "compilerOptions": {
    "composite": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "references": [
    { "path": "../common" }   // dipende dal progetto common
  ],
  "include": ["src"]
}
```

La flag `composite: true` abilita diverse restrizioni e ottimizzazioni:
- Forza la generazione dei file `.d.ts` (implicita `declaration: true`)
- Imposta `rootDir` alla directory del `tsconfig.json` (se non specificato diversamente)
- Tutti i file di implementazione devono corrispondere ai pattern `include` o essere elencati in `files`

### Modalita Build (--build)

Il flag `--build` (o `-b`) trasforma `tsc` in un orchestratore di build che compila i progetti nell'ordine corretto basandosi sul grafo delle dipendenze:

```bash
# Compila tutti i progetti nell'ordine corretto
tsc --build

# Build incrementale (default con --build)
tsc -b

# Forza ricompilazione completa
tsc -b --force

# Pulisce gli output di build
tsc -b --clean

# Modalita watch con build incrementale
tsc -b --watch

# Build con output dettagliato
tsc -b --verbose
```

In benchmark su progetti reali, i project references hanno ridotto i tempi di build incrementale del 68-74% per monorepo con 40+ pacchetti, passando da minuti a decine di secondi per una modifica singola.

### `disableSourceOfProjectReferenceRedirect`

Per i progetti composite molto grandi, la flag `disableSourceOfProjectReferenceRedirect` migliora le performance dell'editor (IDE) facendo si che l'editor utilizzi i file `.d.ts` generati invece di analizzare il codice sorgente dei sotto-progetti:

```jsonc
{
  "compilerOptions": {
    "disableSourceOfProjectReferenceRedirect": true
  }
}
```

---

## Flag Strict Mode — Spiegazione Dettagliata

Come indicato nella sezione [Configurazione](#configurazione-tsconfigjson), la flag `strict: true` abilita un insieme di controlli. Questa sezione spiega ogni singola flag con esempi concreti di cosa cattura.

### `strictNullChecks`

Impedisce di assegnare `null` e `undefined` a tipi non nullable. Senza questa flag, `null` e assegnabile a qualsiasi tipo, rendendo possibili errori `null reference` a runtime:

```typescript
// CON strictNullChecks: true (raccomandato)
let nome: string = null;  // Errore
let nome2: string | null = null; // OK — union esplicita

function trova(id: string): Utente | undefined {
  // Il chiamante DEVE gestire undefined
  return database.get(id);
}
```

### `noImplicitAny`

Segnala un errore quando TypeScript non riesce a inferire il tipo e userebbe implicitamente `any`:

```typescript
// CON noImplicitAny: true
function elabora(dati) { // Errore: Parameter 'dati' implicitly has an 'any' type
  return dati.valore;
}

// Corretto
function elabora(dati: { valore: string }): string {
  return dati.valore;
}
```

### `strictFunctionTypes`

Abilita la controvarianza nei parametri delle funzioni. Senza questa flag, i parametri delle funzioni sono trattati in modo bivariante (sia covariante che controvariante), il che e meno sicuro:

```typescript
// CON strictFunctionTypes: true
type Handler = (evento: MouseEvent) => void;
type HandlerGenerico = (evento: Event) => void;

let gestoreGenerico: HandlerGenerico = (e: Event) => console.log(e.type);
let gestoreMouse: Handler = gestoreGenerico; // OK — Event e piu generico

let gestoreGenerico2: HandlerGenerico = (e: MouseEvent) => console.log(e.clientX);
// Errore con strictFunctionTypes — MouseEvent e piu specifico di Event
```

### `strictBindCallApply`

Verifica la correttezza dei tipi per `bind`, `call` e `apply`:

```typescript
function saluta(nome: string, eta: number): string {
  return `Ciao ${nome}, hai ${eta} anni`;
}

// CON strictBindCallApply: true
saluta.call(undefined, "Marco", 30);     // OK
saluta.call(undefined, "Marco", "30");   // Errore: string non e number
saluta.apply(undefined, ["Marco", 30]);  // OK
saluta.apply(undefined, ["Marco"]);      // Errore: manca il secondo argomento
```

### `strictPropertyInitialization`

Richiede che tutte le proprieta di classe siano inizializzate nel costruttore o con un inizializzatore:

```typescript
class Servizio {
  nome: string;       // Errore: non inizializzato
  porta: number = 80; // OK — inizializzatore

  constructor(nome: string) {
    this.nome = nome;  // OK — inizializzato nel costruttore
  }
}

// Per proprieta inizializzate in modo asincrono, usare !
class Database {
  connessione!: Connessione; // definite assignment assertion

  async inizializza(): Promise<void> {
    this.connessione = await creaConnessione();
  }
}
```

### `useUnknownInCatchVariables`

Le variabili nei blocchi `catch` sono tipizzate come `unknown` invece di `any`:

```typescript
// CON useUnknownInCatchVariables: true
try {
  operazionePericolosa();
} catch (errore) {
  // errore e di tipo unknown, non any
  // errore.message; // Errore: Object is of type 'unknown'

  if (errore instanceof Error) {
    console.log(errore.message); // OK — narrowed a Error
  }
}
```

### `noUncheckedIndexedAccess`

Flag aggiuntiva (non inclusa in `strict`) che aggiunge `| undefined` al tipo di ritorno degli accessi indicizzati. Altamente raccomandata:

```typescript
// CON noUncheckedIndexedAccess: true
const mappa: Record<string, number> = { a: 1, b: 2 };
const valore = mappa["c"]; // tipo: number | undefined (non number)

const array = [1, 2, 3];
const elemento = array[5]; // tipo: number | undefined (non number)

// Forza la gestione del caso undefined
if (valore !== undefined) {
  console.log(valore.toFixed(2)); // OK
}
```

---

## Pattern TypeScript con React — Approfondimento

Come introdotto nella sezione [TypeScript con React](#typescript-con-react), TypeScript offre vantaggi significativi nei progetti React. Questa sezione esplora pattern avanzati.

### Componente Polimorfico con `as` Prop

Il pattern polimorfico permette a un componente di renderizzare diversi elementi HTML preservando la tipizzazione delle props native:

```typescript
import { ElementType, ComponentPropsWithoutRef } from "react";

type BottoneProps<E extends ElementType = "button"> = {
  as?: E;
  variante?: "primario" | "secondario" | "ghost";
  dimensione?: "sm" | "md" | "lg";
} & Omit<ComponentPropsWithoutRef<E>, "as" | "variante" | "dimensione">;

function Bottone<E extends ElementType = "button">({
  as,
  variante = "primario",
  dimensione = "md",
  ...props
}: BottoneProps<E>) {
  const Componente = as || "button";
  return <Componente {...props} />;
}

// Utilizzo type-safe
<Bottone onClick={() => {}}>Click</Bottone>           // button
<Bottone as="a" href="/pagina">Link</Bottone>         // anchor
<Bottone as="a" href={42} />                           // Errore: href deve essere string
```

### forwardRef con Generics

Per creare componenti generici che supportano `ref`, serve un wrapper specifico:

```typescript
import { forwardRef, Ref } from "react";

interface InputProps<T> {
  valore: T;
  onChange: (nuovoValore: T) => void;
  etichetta: string;
}

// Funzione helper per forwardRef con generics
function fixedForwardRef<T, P>(
  render: (props: P, ref: Ref<T>) => React.ReactNode
) {
  return forwardRef(render) as (
    props: P & { ref?: Ref<T> }
  ) => React.ReactNode;
}

const InputGenerico = fixedForwardRef(
  <T extends string | number>(
    props: InputProps<T>,
    ref: Ref<HTMLInputElement>
  ) => {
    return (
      <label>
        {props.etichetta}
        <input
          ref={ref}
          value={String(props.valore)}
          onChange={(e) => props.onChange(e.target.value as T)}
        />
      </label>
    );
  }
);
```

### useReducer Tipizzato con Discriminated Unions

Il pattern piu robusto per `useReducer` usa discriminated unions sia per lo stato che per le azioni:

```typescript
// Stato come discriminated union
type StatoCaricamento<T> =
  | { fase: "inattivo" }
  | { fase: "caricamento" }
  | { fase: "successo"; dati: T }
  | { fase: "errore"; messaggio: string };

// Azioni come discriminated union
type AzioneCaricamento<T> =
  | { tipo: "INIZIA" }
  | { tipo: "SUCCESSO"; dati: T }
  | { tipo: "ERRORE"; messaggio: string }
  | { tipo: "RESET" };

function riduttoreCaricamento<T>(
  stato: StatoCaricamento<T>,
  azione: AzioneCaricamento<T>
): StatoCaricamento<T> {
  switch (azione.tipo) {
    case "INIZIA":
      return { fase: "caricamento" };
    case "SUCCESSO":
      return { fase: "successo", dati: azione.dati };
    case "ERRORE":
      return { fase: "errore", messaggio: azione.messaggio };
    case "RESET":
      return { fase: "inattivo" };
  }
}

// Utilizzo nel componente
function ListaUtenti() {
  const [stato, dispatch] = useReducer(
    riduttoreCaricamento<Utente[]>,
    { fase: "inattivo" }
  );

  // Il narrowing funziona perfettamente
  if (stato.fase === "successo") {
    return <ul>{stato.dati.map(u => <li key={u.id}>{u.nome}</li>)}</ul>;
  }
  if (stato.fase === "errore") {
    return <p>Errore: {stato.messaggio}</p>;
  }
  if (stato.fase === "caricamento") {
    return <p>Caricamento...</p>;
  }
  return <button onClick={() => dispatch({ tipo: "INIZIA" })}>Carica</button>;
}
```

### Discriminated Union per Props di Componenti

Usare discriminated unions nelle props impedisce combinazioni invalide:

```typescript
// Discriminated union per varianti di un componente
type AlertProps =
  | { variante: "successo"; messaggio: string; azione?: () => void }
  | { variante: "errore"; messaggio: string; codiceErrore: number; retry: () => void }
  | { variante: "info"; messaggio: string }
  | { variante: "warning"; messaggio: string; scadenza?: Date };

function Alert(props: AlertProps) {
  switch (props.variante) {
    case "errore":
      return (
        <div className="alert-errore">
          <p>{props.messaggio} (Codice: {props.codiceErrore})</p>
          <button onClick={props.retry}>Riprova</button>
        </div>
      );
    case "successo":
      return (
        <div className="alert-successo">
          <p>{props.messaggio}</p>
          {props.azione && <button onClick={props.azione}>Continua</button>}
        </div>
      );
    // ... altri casi
  }
}

// Type-safe: non si puo passare codiceErrore a variante "successo"
<Alert variante="errore" messaggio="Fallito" codiceErrore={500} retry={() => {}} />
<Alert variante="successo" messaggio="OK" codiceErrore={200} /> // Errore!
```

---

## Validazione a Runtime: Zod, Valibot, ArkType

Come introdotto nella sezione [Zod per Validazione a Runtime](#zod-per-validazione-a-runtime), la validazione a runtime colma il divario tra il type system compile-time di TypeScript e i dati esterni non tipizzati. Questa sezione confronta le tre principali librerie del 2024-2025.

### Panoramica e Confronto

| Caratteristica | Zod | Valibot | ArkType |
|---|---|---|---|
| Bundle size (min+gzip) | ~14 KB | ~1-6 KB (tree-shakeable) | ~6 KB core |
| Performance (100K validazioni) | ~180 ms | ~85 ms | ~12 ms |
| API style | Method chaining | Funzionale/pipe | Syntax simile a TypeScript |
| Tree-shaking | Limitato | Eccellente | Medio |
| Ecosistema | Maturo, ampio | In crescita | Emergente |
| Casi d'uso ideali | Progetti generali | Frontend, edge runtime | Alte performance, backend |

### Valibot — API Modulare

Valibot adotta un approccio modulare dove ogni validatore e una funzione importabile separatamente, abilitando un tree-shaking eccellente. Questo lo rende ideale per applicazioni frontend dove la dimensione del bundle e critica:

```typescript
import * as v from "valibot";

// Definizione dello schema
const SchemaUtente = v.object({
  nome: v.pipe(v.string(), v.minLength(2), v.maxLength(50)),
  email: v.pipe(v.string(), v.email()),
  eta: v.pipe(v.number(), v.integer(), v.minValue(18)),
  ruolo: v.picklist(["admin", "editor", "viewer"]),
  preferenze: v.optional(
    v.object({
      tema: v.optional(v.picklist(["chiaro", "scuro"]), "chiaro"),
      notifiche: v.optional(v.boolean(), true)
    })
  )
});

// Estrazione del tipo TypeScript
type Utente = v.InferOutput<typeof SchemaUtente>;

// Validazione
function validaUtente(dati: unknown): Utente {
  const risultato = v.safeParse(SchemaUtente, dati);
  if (!risultato.success) {
    const errori = risultato.issues.map((i) => i.message);
    throw new Error(`Validazione fallita: ${errori.join(", ")}`);
  }
  return risultato.output;
}

// Composizione di schemi
const SchemaRisposta = v.object({
  stato: v.literal("successo"),
  dati: v.array(SchemaUtente),
  meta: v.object({
    pagina: v.number(),
    totale: v.number()
  })
});
```

### ArkType — Sintassi Nativa

ArkType adotta una sintassi che ricorda quella dei tipi TypeScript, con performance di parsing significativamente superiori grazie a un compilatore JIT interno:

```typescript
import { type } from "arktype";

// La sintassi e simile a TypeScript stesso
const Utente = type({
  nome: "string > 1",
  email: "string.email",
  eta: "number.integer >= 18",
  ruolo: "'admin' | 'editor' | 'viewer'",
  "preferenze?": {
    tema: "'chiaro' | 'scuro'",
    notifiche: "boolean"
  }
});

// Il tipo TypeScript viene inferito automaticamente
type Utente = typeof Utente.infer;

// Validazione
const risultato = Utente({ nome: "Marco", email: "m@e.it", eta: 30, ruolo: "admin" });

if (risultato instanceof type.errors) {
  console.log(risultato.summary);
} else {
  console.log(risultato.nome); // tipo: string
}

// Composizione
const Risposta = type({
  stato: "'successo'",
  "dati": Utente.array(),
  meta: { pagina: "number", totale: "number" }
});
```

### Criteri di Scelta

- **Zod**: la scelta predefinita per la maggior parte dei progetti. Ecosistema maturo, ampia documentazione, integrazioni con tRPC, React Hook Form, OpenAPI. Scegliere Zod quando l'ecosistema e la stabilita contano piu delle performance pure.

- **Valibot**: preferire quando il bundle size e critico (edge functions, applicazioni frontend leggere) o quando si necessita di tree-shaking aggressivo. L'API funzionale/pipe e familiare agli sviluppatori funzionali.

- **ArkType**: preferire quando le performance di parsing sono critiche (validazione ad alto throughput, backend che processa milioni di payload). La sintassi puo risultare meno intuitiva per validazioni complesse con messaggi personalizzati.

---

## Performance del Compilatore

La velocita del compilatore TypeScript diventa un fattore critico nei progetti di grandi dimensioni. Questa sezione illustra le tecniche di ottimizzazione del `tsconfig.json` e le flag che influenzano le performance.

### `isolatedModules`

La flag `isolatedModules` assicura che ogni file possa essere compilato indipendentemente dagli altri, senza accesso all'intero programma. Questo e un requisito per i transpiler single-file come esbuild, SWC e Babel, che processano un file alla volta:

```jsonc
{
  "compilerOptions": {
    "isolatedModules": true
  }
}
```

Con `isolatedModules` attivo, il compilatore segnala errori per costrutti che richiedono informazioni cross-file, come i `const enum` esportati e le re-esportazioni di tipi ambigue. L'impatto sulle performance e indiretto: questa flag abilita l'uso di transpiler veloci per il codice di sviluppo, mantenendo `tsc` solo per il type checking.

### `isolatedDeclarations`

Introdotto in TypeScript 5.5, `isolatedDeclarations` richiede annotazioni esplicite per tutte le esportazioni, permettendo la generazione di file `.d.ts` senza analizzare l'intero programma. Questo sblocca la generazione parallela delle dichiarazioni nei monorepo:

```jsonc
{
  "compilerOptions": {
    "isolatedDeclarations": true,
    "declaration": true
  }
}
```

```typescript
// CON isolatedDeclarations: true

// Errore — il tipo di ritorno deve essere esplicito nelle esportazioni
export function calcola(a: number, b: number) {
  return a + b;
}

// Corretto
export function calcola(a: number, b: number): number {
  return a + b;
}

// Le funzioni non esportate possono ancora usare l'inferenza
function helper(x: number) {
  return x * 2; // OK — non esportata
}
```

### `skipLibCheck`

La flag `skipLibCheck` salta il type checking dei file `.d.ts` (inclusi quelli in `node_modules/@types`). Questo riduce drasticamente i tempi di compilazione, specialmente in progetti con molte dipendenze:

```jsonc
{
  "compilerOptions": {
    "skipLibCheck": true // raccomandato per tutti i progetti
  }
}
```

Il compromesso e minimo: gli errori nei file `.d.ts` di terze parti sono rari, e quando esistono sono tipicamente segnalati dalla community e risolti rapidamente.

### Checklist di Ottimizzazione tsconfig

```jsonc
{
  "compilerOptions": {
    // Performance di compilazione
    "incremental": true,                    // ricompila solo i file modificati
    "skipLibCheck": true,                   // salta il check dei .d.ts
    "isolatedModules": true,                // abilita transpiler single-file
    "tsBuildInfoFile": "./.tsbuildinfo",     // percorso cache incrementale

    // Monorepo / grandi progetti
    "composite": true,                      // per project references
    "disableSourceOfProjectReferenceRedirect": true, // performance IDE
    "disableReferencedProjectLoad": true,   // carica solo i progetti necessari

    // Ridurre il lavoro del compilatore
    "types": ["node"],                      // limita i pacchetti @types caricati
    "moduleResolution": "bundler"           // evita la risoluzione complessa di Node
  },
  "include": ["src"],                       // limita i file analizzati
  "exclude": ["node_modules", "dist", "**/*.test.ts", "coverage"]
}
```

---

## Migrazione da JavaScript

La migrazione da JavaScript a TypeScript e un processo che richiede pianificazione e un approccio incrementale. Questa sezione illustra una strategia collaudata per migrare progetti di qualsiasi dimensione.

### Fase 1 — Configurazione Iniziale

Il primo passo e aggiungere un `tsconfig.json` permissivo che permetta la coesistenza di file `.js` e `.ts`:

```jsonc
// tsconfig.json — configurazione di migrazione
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",

    // Flag di migrazione
    "allowJs": true,          // permette file .js nel progetto
    "checkJs": false,         // disattivato inizialmente
    "strict": false,          // si attiva progressivamente

    "outDir": "./dist",
    "rootDir": "./src",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### Fase 2 — Ordine di Migrazione

L'ordine in cui si convertono i file e cruciale. La strategia "dalle foglie alla radice" evita di propagare tipi `any` attraverso il progetto:

1. **Tipi e interfacce condivise** — creare file `.ts` con i tipi fondamentali del dominio (`tipi/modelli.ts`, `tipi/api.ts`)
2. **Utility e helper puri** — funzioni senza dipendenze esterne, facili da tipizzare
3. **Modelli di dati e validazione** — le strutture dati che attraversano il sistema
4. **Servizi e logica di business** — i moduli con dipendenze gia tipizzate
5. **Route handler e middleware** — i punti di ingresso dell'applicazione
6. **File di configurazione e bootstrap** — l'ultimo livello

```bash
# Rinominare un file alla volta
mv src/utils/formattazione.js src/utils/formattazione.ts
# Compilare per scoprire errori
npx tsc --noEmit
# Correggere gli errori
# Ripetere
```

### Fase 3 — Abilitare `checkJs`

Una volta convertiti i file critici, abilitare `checkJs` per ricevere errori di tipo anche nei file `.js` rimanenti tramite l'inferenza di tipo e le annotazioni JSDoc:

```jsonc
{
  "compilerOptions": {
    "checkJs": true
  }
}
```

```javascript
// In file .js ancora non migrati, JSDoc fornisce annotazioni di tipo
/**
 * @param {string} nome
 * @param {number} eta
 * @returns {{ nome: string, eta: number }}
 */
function creaUtente(nome, eta) {
  return { nome, eta };
}
```

### Fase 4 — Stringere le Flag Strict Progressivamente

Non attivare `strict: true` tutto in una volta. Abilitare le flag una alla volta, correggendo gli errori man mano:

```jsonc
// Ordine raccomandato di attivazione:
{
  "compilerOptions": {
    // Passo 1 — i piu impattanti
    "noImplicitAny": true,
    "strictNullChecks": true,

    // Passo 2 — errori meno comuni
    "strictFunctionTypes": true,
    "strictBindCallApply": true,

    // Passo 3 — ultimi
    "strictPropertyInitialization": true,
    "useUnknownInCatchVariables": true,
    "noImplicitThis": true,
    "alwaysStrict": true,

    // Passo 4 — sostituire tutto con
    "strict": true,

    // Passo 5 — flag aggiuntive raccomandate
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true
  }
}
```

### Gestione dei Tipi Mancanti

Durante la migrazione, si incontreranno librerie senza tipi. Strategie per gestirle:

```typescript
// Opzione 1: Installare i tipi dalla community
// npm install --save-dev @types/nome-libreria

// Opzione 2: Creare una dichiarazione locale minimale
// src/tipi/nome-libreria.d.ts
declare module "nome-libreria" {
  export function funzionePrincipale(input: string): unknown;
  export default function init(config: Record<string, unknown>): void;
}

// Opzione 3: Dichiarazione "escape hatch" per procedere velocemente
// (da sostituire con tipi reali il prima possibile)
declare module "libreria-senza-tipi";

// Opzione 4: @ts-expect-error per errori temporanei specifici
// @ts-expect-error — MIGRATION: tipizzare dopo il merge di #1234
const risultato = libreriaVecchia.metodo(dati);
```

### Metriche di Progresso

Tenere traccia del progresso della migrazione:

```bash
# Contare i file per estensione
find src -name "*.js" | wc -l   # file ancora da migrare
find src -name "*.ts" | wc -l   # file migrati
find src -name "*.tsx" | wc -l  # componenti React migrati

# Contare le occorrenze di any
grep -r ":\s*any" src/ --include="*.ts" --include="*.tsx" | wc -l

# Contare i @ts-ignore/@ts-expect-error
grep -r "@ts-ignore\|@ts-expect-error" src/ --include="*.ts" --include="*.tsx" | wc -l
```

L'obiettivo finale e raggiungere zero file `.js`, zero `any` espliciti e `strict: true` attivo. In progetti di grandi dimensioni (100K+ righe), questo processo puo richiedere settimane o mesi, ma il valore e incrementale: ogni file migrato migliora la type safety dell'intero sistema.

---

> **Nota finale**: TypeScript e un investimento che ripaga enormemente man mano che la complessita del progetto cresce. Il sistema di tipi non e un vincolo, ma uno strumento di design che guida verso codice piu corretto, piu manutenibile e piu facile da comprendere. L'obiettivo non e annotare ogni singola riga, ma stabilire contratti chiari ai confini tra moduli, validare i dati esterni e sfruttare l'inferenza del compilatore per tutto il resto.

---

## Esercizi

### Esercizio 1 — Tipi Base e Unioni

**Obiettivo:** padroneggiare i tipi fondamentali, le union e il type narrowing.

Creare un modulo `shapes.ts` che modelli figure geometriche tramite discriminated union:

- Definire un tipo `Shape` come unione di `Circle`, `Rectangle` e `Triangle`, ciascuno con un campo discriminante `kind`
- Implementare una funzione `area(shape: Shape): number` che utilizzi uno `switch` esaustivo (con `never` nel caso `default`) per calcolare l'area
- Implementare una funzione `describe(shape: Shape): string` che restituisca una descrizione testuale della figura
- Scrivere almeno 5 test unitari che verifichino i calcoli e il narrowing corretto
- Compilare con `strict: true` e zero errori

### Esercizio 2 — Generics e Utility Types

**Obiettivo:** creare strutture dati generiche type-safe e sfruttare gli utility types.

Implementare una struttura dati `TypedMap<K extends string, V>`:

- Supportare operazioni `get`, `set`, `delete`, `has`, `keys`, `values` e `entries`
- Il tipo di ritorno di `get` deve essere `V | undefined`
- Creare un tipo `ReadonlyTypedMap<K, V>` che esponga solo operazioni di lettura, derivato con `Readonly` e `Pick`
- Implementare una funzione `merge<K, V>(a: TypedMap<K, V>, b: TypedMap<K, V>): TypedMap<K, V>` che restituisca una nuova mappa senza mutare gli argomenti
- Creare utility types personalizzati: `KeysOfType<T, V>` (chiavi di T il cui valore e assegnabile a V) e `DeepPartial<T>`
- Test completi per ogni operazione e utility type

### Esercizio 3 — Validazione Runtime con Zod

**Obiettivo:** costruire un layer di validazione che colleghi i dati esterni non tipizzati al codice interno type-safe.

Creare un modulo di validazione per un'API di e-commerce:

- Definire schemi Zod per `Product`, `CartItem`, `Order` e `Customer`
- Derivare i tipi TypeScript dagli schemi con `z.infer<typeof schema>`
- Implementare una funzione `validateApiResponse<T>(schema: z.ZodSchema<T>, data: unknown): Result<T, ValidationError>` con gestione esplicita degli errori
- Creare un type `Result<T, E>` come discriminated union con varianti `Ok` e `Err`
- Scrivere test che verifichino la validazione corretta, il rifiuto di dati malformati e i messaggi di errore strutturati
- Dimostrare la composizione degli schemi (array, nested, optional, transform)

### Esercizio 4 — Conditional Types e Template Literal Types

**Obiettivo:** padroneggiare i type-level computation avanzati di TypeScript.

Costruire un sistema di tipi per un event emitter type-safe:

- Definire un tipo `EventMap` come record di nomi evento -> payload
- Creare un tipo `EventHandler<T extends EventMap, K extends keyof T>` che inferisca automaticamente il tipo del payload
- Implementare `TypedEmitter<T extends EventMap>` con metodi `on`, `off` e `emit` completamente tipizzati
- Usare template literal types per creare un tipo `DotPath<T>` che generi tutti i percorsi possibili di un oggetto annidato (es. `"user.address.city"`)
- Implementare una funzione `getByPath<T, P extends DotPath<T>>(obj: T, path: P)` il cui tipo di ritorno sia inferito automaticamente dal percorso
- Test che verifichino la correttezza dei tipi a compile-time (usando `expectTypeOf` di vitest)

### Esercizio 5 — Migrazione JavaScript a TypeScript

**Obiettivo:** applicare una strategia di migrazione incrementale su un progetto reale.

Partendo da un progetto Node.js/Express in JavaScript puro (almeno 10 file sorgente):

- Configurare `tsconfig.json` con `strict: true`, `noUncheckedIndexedAccess: true` e `allowJs: true` per la migrazione graduale
- Migrare i file nell'ordine corretto: utility puri prima, poi modelli, poi route, infine middleware
- Per ogni file migrato, aggiungere tipi espliciti alle interfacce pubbliche e lasciare che l'inferenza gestisca il resto
- Creare un file `types/express.d.ts` per estendere i tipi di Express (es. aggiungere `user` a `Request`)
- Introdurre Zod per validare i body delle richieste nei route handler
- Documentare ogni decisione non ovvia con un commento `// MIGRATION:`
- Il progetto deve compilare senza errori e tutti i test preesistenti devono continuare a passare

---

## Letture e Riferimenti

### Documentazione ufficiale

- **TypeScript Handbook** — guida ufficiale completa al linguaggio e al sistema di tipi. https://www.typescriptlang.org/docs/handbook/ (consultato: 2026-05-24)
- **TypeScript Playground** — ambiente interattivo per sperimentare con i tipi e condividere snippet. https://www.typescriptlang.org/play (consultato: 2026-05-24)
- **TSConfig Reference** — documentazione esaustiva di ogni opzione del compilatore. https://www.typescriptlang.org/tsconfig (consultato: 2026-05-24)
- **TypeScript Release Notes** — changelog dettagliato per ogni versione. https://devblogs.microsoft.com/typescript/ (consultato: 2026-05-24)
- **Zod Documentation** — libreria di validazione schema-first per TypeScript. https://zod.dev/ (consultato: 2026-05-24)
- **Type Challenges** — raccolta di esercizi per padroneggiare il sistema di tipi avanzato. https://github.com/type-challenges/type-challenges (consultato: 2026-05-24)
- **DefinitelyTyped** — repository centrale delle definizioni di tipo per pacchetti npm. https://github.com/DefinitelyTyped/DefinitelyTyped (consultato: 2026-05-24)

### Libri e approfondimenti

- Cherny B., *Programming TypeScript*, O'Reilly Media, 2019.
- Vanderkam D., *Effective TypeScript: 62 Specific Ways to Improve Your TypeScript*, O'Reilly Media, 2024.
- Rauschmayer A., *Tackling TypeScript*, pubblicazione indipendente, 2023. https://exploringjs.com/tackling-ts/

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Prerequisito diretto: TypeScript estende la sintassi e la semantica di JavaScript ES2015+ |
| [05 — JavaScript Avanzato](05-javascript-avanzato.md) | Pattern avanzati (closure, prototype, iteratori) che TypeScript tipizza e rende piu sicuri |
| [07 — React](07-react.md) | TypeScript e lo standard de facto per i progetti React: props tipizzate, hooks generici, Context tipizzato |
| [10 — Node.js](10-nodejs.md) | TypeScript lato server: tipizzazione di Express/Fastify, moduli Node e configurazione `ts-node` |
| [15 — Testing Web](15-testing-web.md) | I tipi migliorano l'affidabilita dei test: mock tipizzati, `expectTypeOf`, fixture type-safe |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Configurazione di `tsc`, integrazione con Vite/esbuild/SWC, emissione di declaration files |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Type Narrowing** | Tecnica con cui TypeScript restringe un tipo ampio a uno piu specifico all'interno di un blocco condizionale, tramite `typeof`, `instanceof`, `in` o type guard personalizzati. |
| **Discriminated Union** | Union type in cui ogni membro possiede un campo letterale comune (discriminante) che permette al compilatore di distinguere i casi in modo esaustivo. |
| **Generics** | Parametri di tipo che rendono funzioni, classi e interfacce riutilizzabili per diversi tipi concreti mantenendo la type safety. |
| **Utility Types** | Tipi built-in di TypeScript (`Partial`, `Required`, `Pick`, `Omit`, `Record`, ecc.) che trasformano altri tipi in modo dichiarativo. |
| **Conditional Types** | Costrutto `T extends U ? X : Y` che permette di selezionare un tipo in base a una condizione valutata a compile-time. |
| **Mapped Types** | Tipi che iterano sulle chiavi di un altro tipo per creare nuovi tipi derivati, usando la sintassi `{ [K in keyof T]: ... }`. |
| **Template Literal Types** | Tipi stringa costruiti tramite interpolazione di altri tipi letterali, ad esempio `` `on${Capitalize<string>}` ``. |
| **Type Guard** | Funzione con tipo di ritorno `param is Type` che esegue un controllo a runtime e informa il compilatore del narrowing risultante. |
| **Branded Type** | Pattern che usa l'intersezione con un tag unico (`type UserId = string & { __brand: 'UserId' }`) per distinguere tipi strutturalmente identici. |
| **`satisfies` Operator** | Operatore introdotto in TS 4.9 che verifica la conformita di un valore a un tipo senza allargare il tipo inferito, preservando i tipi letterali. |
| **`infer` Keyword** | Parola chiave utilizzabile nei conditional types per estrarre e assegnare un nome a un sotto-tipo durante la valutazione del tipo. |
| **Declaration File (.d.ts)** | File che contiene solo dichiarazioni di tipo senza implementazione, usato per descrivere la forma di librerie JavaScript. |
| **Strict Mode** | Insieme di flag del compilatore (`strict: true`) che abilita i controlli piu rigorosi: `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, ecc. |
| **Type Assertion** | Sintassi `value as Type` che forza il compilatore a trattare un valore come un tipo specifico; da evitare quando il narrowing e possibile. |
| **Covariance / Contravariance** | Proprieta che descrivono come la relazione di sottotipo si propaga attraverso i costruttori di tipo: covariante per i valori di ritorno, contravariante per i parametri delle funzioni. |
| **NoInfer<T>** | Utility type introdotto in TypeScript 5.4 che segnala al compilatore di escludere una posizione dalla raccolta di candidati per l'inferenza dei generics. |
| **Awaited<T>** | Utility type che estrae ricorsivamente il tipo risolto da un `Promise<T>`, indipendentemente dal livello di annidamento. |
| **Variadic Tuple Types** | Estensione del sistema di tuple che permette di manipolare tuple con un numero variabile di elementi tramite l'operatore spread a livello di tipo. |
| **Assertion Function** | Funzione il cui tipo di ritorno e `asserts param is Type`, che garantisce al compilatore una condizione sui tipi se la funzione termina senza lanciare eccezioni. |
| **Project References** | Meccanismo del compilatore TypeScript che permette di suddividere un progetto in sotto-progetti con dipendenze esplicite, abilitando build incrementali e parallele. |
| **Valibot** | Libreria di validazione runtime per TypeScript con architettura modulare e tree-shaking eccellente, alternativa leggera a Zod per applicazioni frontend. |
| **ArkType** | Libreria di validazione runtime ad alte performance che usa una sintassi simile ai tipi TypeScript nativi, con un compilatore JIT interno. |
| **`isolatedModules`** | Flag del compilatore che assicura che ogni file possa essere trasformato indipendentemente, requisito per transpiler single-file come esbuild e SWC. |
| **`isolatedDeclarations`** | Flag introdotta in TS 5.5 che richiede annotazioni esplicite per le esportazioni, abilitando la generazione parallela dei file `.d.ts`. |
