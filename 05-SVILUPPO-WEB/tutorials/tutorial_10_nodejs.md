# Tutorial 10 — Node.js: Dal Principiante all'Esperto

> **Companion a:** `10-nodejs.md`
> **Scope:** Il runtime e l'event loop di Node, i moduli core (`fs`, `path`, `http`, `crypto`, `stream`), ESM e TypeScript sul server, Express e Fastify, middleware e gestione centralizzata degli errori, stream e backpressure, worker threads, cluster e scalabilità, variabili d'ambiente e configurazione, logging strutturato, diagnostica e profiling, il permission model, sicurezza della supply chain, testing con `node:test` e Vitest
> **Prerequisiti:** `tutorial_04_javascript_fondamenti.md` e `tutorial_05_javascript_avanzato.md` — event loop, Promise, moduli; `tutorial_06_typescript.md`
> **Durata stimata:** 28-35 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Node.js LTS (linea 24.x) · TypeScript 5.6+ · Express 5 · Fastify 5 · Pino · Vitest

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Cos'è Node.js e cosa non è](#a1-cosè-nodejs-e-cosa-non-è)
  - [A2. Moduli ESM e TypeScript sul server](#a2-moduli-esm-e-typescript-sul-server)
  - [A3. I moduli core che userai davvero](#a3-i-moduli-core-che-userai-davvero)
  - [A4. Il primo server HTTP](#a4-il-primo-server-http)
  - [A5. Express: routing e middleware](#a5-express-routing-e-middleware)
  - [A6. Configurazione e variabili d'ambiente](#a6-configurazione-e-variabili-dambiente)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. L'event loop di Node in dettaglio](#b1-levent-loop-di-node-in-dettaglio)
  - [B2. Gestione centralizzata degli errori](#b2-gestione-centralizzata-degli-errori)
  - [B3. Stream e backpressure](#b3-stream-e-backpressure)
  - [B4. Fastify: quando e perché](#b4-fastify-quando-e-perché)
  - [B5. Logging strutturato e tracciabilità](#b5-logging-strutturato-e-tracciabilità)
  - [B6. Worker threads](#b6-worker-threads)
  - [B7. Cluster, scalabilità e spegnimento pulito](#b7-cluster-scalabilità-e-spegnimento-pulito)
  - [B8. Sicurezza: il minimo indispensabile](#b8-sicurezza-il-minimo-indispensabile)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: server Express modulare](#c2-mini-progetto-server-express-modulare)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Diagnostica e profiling in produzione](#d1-diagnostica-e-profiling-in-produzione)
  - [D2. Il permission model](#d2-il-permission-model)
  - [D3. Supply chain e integrità delle dipendenze](#d3-supply-chain-e-integrità-delle-dipendenze)
  - [D4. Testare un server](#d4-testare-un-server)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                             NODE.JS
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
    ┌─────────▼──────────┐              ┌─────────▼──────────┐
    │   IL RUNTIME       │              │    I MODULI CORE   │
    │                    │              │                    │
    │  V8 (JavaScript)   │              │  node:fs/promises  │
    │  libuv (I/O)       │              │  node:path         │
    │   └ thread pool    │              │  node:http         │
    │     (4 di default) │              │  node:crypto       │
    │  event loop        │              │  node:stream       │
    │   └ 6 fasi         │              │  node:worker_threads│
    │   └ UN thread      │              │  node:test         │
    │     per JavaScript │              │  node:util         │
    │                    │              │                    │
    │  I/O = asincrono   │              │  fetch, WebSocket, │
    │  CPU = blocca      │              │  AbortController   │
    │                    │              │  sono GLOBALI      │
    └─────────┬──────────┘              └─────────┬──────────┘
              └─────────────────┬─────────────────┘
                                │
    ┌───────────────────────────┼───────────────────────────┐
    │                           │                           │
┌───▼─────────────┐  ┌──────────▼─────────┐  ┌──────────────▼────┐
│   IL SERVER     │  │      STREAM        │  │   PRODUZIONE      │
│                 │  │                    │  │                   │
│ http.createServer│ │ Readable           │  │ configurazione    │
│ Express 5       │  │ Writable           │  │  └ validata       │
│  ├ middleware   │  │ Transform          │  │    all'avvio      │
│  ├ router       │  │ pipeline()         │  │ logging strutturato│
│  └ error handler│  │  └ gestisce errori │  │  └ pino + trace id│
│ Fastify 5       │  │    e pulizia       │  │ spegnimento pulito│
│  ├ schema JSON  │  │ BACKPRESSURE       │  │ health check      │
│  ├ 2-3x più     │  │  └ il consumatore  │  │ cluster / PM2     │
│  │   veloce     │  │    detta il ritmo  │  │ permission model  │
│  └ plugin       │  │                    │  │ npm audit, SBOM   │
└─────────────────┘  └────────────────────┘  └───────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cos'è Node.js e cosa non è

> **Analogia:** un ristorante con un cameriere solo ma una brigata di cuochi. Il cameriere (il thread JavaScript) prende gli ordini, li passa in cucina (libuv e il sistema operativo) e serve altri tavoli mentre i piatti si preparano. Finché il lavoro è "aspettare che qualcun altro finisca" — la rete, il disco, il database — un cameriere basta per centinaia di tavoli. Ma se il cameriere si mette a sbucciare le patate, tutti aspettano.

```
Node.js = V8 + libuv + le API di Node

  V8      esegue JavaScript (lo stesso motore di Chrome)
  libuv   gestisce l'I/O asincrono e il thread pool
  API     fs, http, crypto, stream, e il resto
```

```javascript
// Ciò che Node fa bene: I/O concorrente
// Mille richieste HTTP contemporanee non sono un problema:
// il thread JavaScript è libero mentre la rete lavora
const risposte = await Promise.all(url.map((u) => fetch(u)))

// Ciò che Node fa male: calcolo intensivo
// Questo blocca TUTTE le richieste per la sua durata
function fibonacci(n) {
  return n < 2 ? n : fibonacci(n - 1) + fibonacci(n - 2)
}
fibonacci(45) // ~10 secondi di server completamente fermo
```

```
Il criterio, in una frase:

  Node è adatto quando il server passa il tempo ad ASPETTARE
  (database, altre API, file, rete) e non a CALCOLARE.

  Un'API che legge da un database e restituisce JSON è il
  caso ideale. Un servizio che ridimensiona immagini o
  elabora video no — o richiede i worker threads (B6).
```

### Il thread pool

```javascript
// Non tutto l'I/O è veramente asincrono a livello di sistema.
// libuv usa un pool di thread (4 di default) per:
//   · il filesystem (fs)
//   · la risoluzione DNS con dns.lookup()
//   · crypto: pbkdf2, scrypt, randomBytes
//   · zlib: compressione e decompressione

// Cinque operazioni crypto insieme: la quinta aspetta
// che una delle prime quattro finisca
import { scrypt } from 'node:crypto'

// Il pool si dimensiona con una variabile d'ambiente,
// PRIMA dell'avvio del processo
// UV_THREADPOOL_SIZE=16 node server.js
```

```javascript
// La rete NON usa il thread pool: usa epoll/kqueue/IOCP,
// che sono asincroni a livello di kernel. È il motivo
// per cui Node regge decine di migliaia di connessioni.
```

### Verificare la versione

```powershell
node --version
```

```javascript
// Nel codice, quando serve
console.log(process.version) // 'v24.4.1'
console.log(process.versions.v8)
console.log(process.platform) // 'win32' | 'linux' | 'darwin'
console.log(process.arch) // 'x64' | 'arm64'
```

---

## A2. Moduli ESM e TypeScript sul server

```json
// package.json — dichiarare ESM è il primo passo di ogni progetto nuovo
{
  "name": "api-fatture",
  "type": "module",
  "engines": {
    "node": ">=22.0.0"
  },
  "scripts": {
    "dev": "node --watch --env-file=.env src/server.ts",
    "start": "node --env-file=.env dist/server.js",
    "build": "tsc",
    "typecheck": "tsc --noEmit"
  }
}
```

### TypeScript senza passo di build

Da Node 22.6 esiste il type stripping: Node esegue i file `.ts` rimuovendo le annotazioni, senza compilarli. Dalla 23.6 è attivo di default.

```powershell
# Node 22: serve il flag
node --experimental-strip-types src/server.ts

# Node 23.6+: funziona direttamente
node src/server.ts
```

```
Cosa il type stripping fa e non fa:

  ✅ rimuove le annotazioni di tipo, le interfacce, i type alias
  ✅ nessun passo di build in sviluppo: avvio immediato

  ❌ NON verifica i tipi: serve comunque 'tsc --noEmit'
  ❌ NON trasforma enum, namespace, parameter properties
     (le sintassi TypeScript che GENERANO codice)
     → con --experimental-transform-types funzionano anche quelle

Per la produzione, compilare con tsc resta la scelta
più prevedibile: il codice emesso è quello che gira.
```

```json
// tsconfig.json per il server
{
  "compilerOptions": {
    "target": "ES2023",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2023"],

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "verbatimModuleSyntax": true,

    "outDir": "dist",
    "rootDir": "src",
    "sourceMap": true,

    "skipLibCheck": true,
    "types": ["node"]
  },
  "include": ["src"]
}
```

```typescript
// ⚠ Con "module": "NodeNext" gli import DEVONO avere
//    l'estensione .js, anche importando file .ts.
//    È il percorso del file EMESSO, non del sorgente.
import { creaServer } from './server.js' // il file è server.ts
import type { Configurazione } from './configurazione.js'
```

### Gli equivalenti di `__dirname`

```typescript
// In ESM non esistono. Da Node 20.11 ci sono i sostituti diretti:
console.log(import.meta.dirname)
console.log(import.meta.filename)

// Risolvere un percorso relativo al modulo
const percorsoDati = new URL('./dati.json', import.meta.url)

// La forma compatibile con versioni precedenti
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'

const file = fileURLToPath(import.meta.url)
const cartella = dirname(file)
```

### Importare CommonJS

```typescript
// Un modulo CJS ha un solo export: arriva come default
import moduloCjs from 'libreria-vecchia'
const { funzione } = moduloCjs

// createRequire, quando serve require dentro ESM
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)

const pacchetto = require('./package.json')

// Oppure, con gli import attributes
import pacchetto2 from './package.json' with { type: 'json' }
```

---

## A3. I moduli core che userai davvero

### `node:path` — mai concatenare percorsi a mano

```typescript
import path from 'node:path'

// ❌ Si rompe su Windows, e con i percorsi che finiscono con /
const sbagliato = cartella + '/' + nome + '.json'

// ✅ path.join normalizza i separatori
const corretto = path.join(cartella, `${nome}.json`)

path.resolve('src', 'file.ts') // percorso assoluto dalla cwd
path.dirname('/a/b/c.txt') // '/a/b'
path.basename('/a/b/c.txt') // 'c.txt'
path.basename('/a/b/c.txt', '.txt') // 'c'
path.extname('/a/b/c.txt') // '.txt'
path.relative('/a/b', '/a/c/d') // '../c/d'
path.parse('/a/b/c.txt') // { root, dir, base, ext, name }

// posix e win32 per forzare uno stile
path.posix.join('a', 'b') // 'a/b' anche su Windows
```

```typescript
// ⚠ IL PATTERN DI SICUREZZA: la traversal.
//    Un nome di file che arriva dall'utente può contenere ../
function percorsoSicuro(base: string, nomeUtente: string): string {
  // 1. Normalizza e risolve
  const risolto = path.resolve(base, nomeUtente)

  // 2. Verifica che sia DENTRO la base
  const baseRisolta = path.resolve(base)
  if (!risolto.startsWith(baseRisolta + path.sep) && risolto !== baseRisolta) {
    throw new Error('Percorso fuori dalla cartella consentita')
  }

  return risolto
}

// percorsoSicuro('/var/dati', '../../etc/passwd')  → errore
```

### `node:fs/promises` — sempre la versione a Promise

```typescript
import fs from 'node:fs/promises'
import { createReadStream, createWriteStream } from 'node:fs'

// Lettura e scrittura
const testo = await fs.readFile('dati.json', 'utf8')
const binario = await fs.readFile('immagine.png') // Buffer
await fs.writeFile('esito.json', JSON.stringify(dati, null, 2), 'utf8')
await fs.appendFile('registro.log', `${riga}\n`)

// Cartelle
await fs.mkdir('cartella/annidata', { recursive: true })
const voci = await fs.readdir('.', { withFileTypes: true })

for (const voce of voci) {
  if (voce.isDirectory()) console.log('cartella:', voce.name)
  if (voce.isFile()) console.log('file:', voce.name)
}

// Ricorsivo (Node 20+)
const tutte = await fs.readdir('src', { recursive: true })

// Informazioni
const stato = await fs.stat('file.txt')
console.log(stato.size, stato.mtime, stato.isFile())

// Copia, spostamento, rimozione
await fs.copyFile('a.txt', 'b.txt')
await fs.rename('vecchio.txt', 'nuovo.txt')
await fs.rm('cartella', { recursive: true, force: true })
```

```typescript
// ❌ existsSync seguito da un'operazione: c'è una finestra
//    fra la verifica e l'uso in cui il file può cambiare.
//    È la vulnerabilità TOCTOU (time-of-check to time-of-use).
import { existsSync } from 'node:fs'

if (existsSync(percorso)) {
  const contenuto = await fs.readFile(percorso, 'utf8') // può fallire comunque
}

// ✅ Provare e gestire l'errore
async function leggiSePresente(percorso: string): Promise<string | null> {
  try {
    return await fs.readFile(percorso, 'utf8')
  } catch (errore) {
    if (isErrnoException(errore) && errore.code === 'ENOENT') {
      // il file non esiste: caso previsto
      return null
    }
    throw errore
  }
}

/** Type guard per gli errori di sistema di Node. */
function isErrnoException(errore: unknown): errore is NodeJS.ErrnoException {
  return errore instanceof Error && 'code' in errore
}
```

```typescript
// La scrittura ATOMICA: scrivere su un file temporaneo
// e poi rinominare. Il rename è atomico sullo stesso
// filesystem: nessuno legge mai un file a metà.
async function scriviAtomico(percorso: string, contenuto: string): Promise<void> {
  const temporaneo = `${percorso}.${process.pid}.tmp`

  try {
    await fs.writeFile(temporaneo, contenuto, 'utf8')
    await fs.rename(temporaneo, percorso)
  } catch (errore) {
    await fs.rm(temporaneo, { force: true })
    throw errore
  }
}
```

### `node:crypto`

```typescript
import crypto from 'node:crypto'

// Identificativi casuali
crypto.randomUUID() // '3f2b...'
crypto.randomBytes(32).toString('base64url')

// Un intero casuale sicuro, senza modulo bias
crypto.randomInt(0, 100)

// Hash — per il contenuto, NON per le password
const hash = crypto.createHash('sha256').update(contenuto).digest('hex')

// HMAC — per firmare
const firma = crypto.createHmac('sha256', segreto).update(payload).digest('base64url')

// ⚠ Il confronto delle firme DEVE essere a tempo costante:
//    === esce al primo byte diverso e permette un attacco
//    a tempo che ricostruisce la firma byte per byte
function firmaValida(attesa: string, ricevuta: string): boolean {
  const a = Buffer.from(attesa)
  const b = Buffer.from(ricevuta)

  // timingSafeEqual richiede la stessa lunghezza
  if (a.length !== b.length) return false

  return crypto.timingSafeEqual(a, b)
}
```

```typescript
// Le password: MAI con un hash veloce.
// scrypt e argon2 sono lenti per progetto.
import { scrypt, randomBytes, timingSafeEqual } from 'node:crypto'
import { promisify } from 'node:util'

const scryptAsync = promisify(scrypt) as (
  password: string,
  sale: Buffer,
  lunghezza: number,
) => Promise<Buffer>

export async function hashPassword(password: string): Promise<string> {
  const sale = randomBytes(16)
  const derivata = await scryptAsync(password, sale, 64)
  return `${sale.toString('hex')}:${derivata.toString('hex')}`
}

export async function verificaPassword(password: string, memorizzata: string): Promise<boolean> {
  const [saleHex, hashHex] = memorizzata.split(':')
  if (!saleHex || !hashHex) return false

  const sale = Buffer.from(saleHex, 'hex')
  const atteso = Buffer.from(hashHex, 'hex')
  const derivata = await scryptAsync(password, sale, atteso.length)

  return timingSafeEqual(derivata, atteso)
}
```

In produzione, `argon2` è la scelta raccomandata: `scrypt` va bene ed è nel core, senza dipendenze.

---

## A4. Il primo server HTTP

```typescript
// src/server-minimo.ts — senza framework, per capire cosa c'è sotto
import http from 'node:http'

const server = http.createServer((richiesta, risposta) => {
  const url = new URL(richiesta.url ?? '/', `http://${richiesta.headers.host}`)

  if (richiesta.method === 'GET' && url.pathname === '/salute') {
    risposta.writeHead(200, { 'Content-Type': 'application/json' })
    risposta.end(JSON.stringify({ stato: 'ok', quando: new Date().toISOString() }))
    return
  }

  risposta.writeHead(404, { 'Content-Type': 'application/json' })
  risposta.end(JSON.stringify({ errore: 'Non trovato' }))
})

server.listen(3000, () => {
  console.log('In ascolto su http://localhost:3000')
})
```

```typescript
// Leggere il corpo di una richiesta: arriva a PEZZI
async function leggiCorpo(richiesta: http.IncomingMessage): Promise<string> {
  const pezzi: Buffer[] = []
  let dimensione = 0
  const MASSIMO = 1024 * 1024 // 1 MB

  for await (const pezzo of richiesta) {
    dimensione += pezzo.length

    // Il limite NON è opzionale: senza, una richiesta
    // enorme esaurisce la memoria del processo
    if (dimensione > MASSIMO) {
      richiesta.destroy()
      throw new Error('Corpo della richiesta troppo grande')
    }

    pezzi.push(pezzo)
  }

  return Buffer.concat(pezzi).toString('utf8')
}
```

Scrivere un server a mano insegna cosa i framework fanno: il parsing dell'URL, la lettura del corpo, i limiti di dimensione, le intestazioni. In produzione si usa un framework, ma sapere cosa c'è sotto serve quando qualcosa non funziona.

---

## A5. Express: routing e middleware

```powershell
pnpm add express
pnpm add -D @types/express
```

```typescript
// src/app.ts
import express, { type Request, type Response, type NextFunction } from 'express'

export function creaApp() {
  const app = express()

  // ── Middleware globali, nell'ordine in cui vengono eseguiti ──

  // Fidarsi del proxy: necessario dietro un load balancer,
  // altrimenti req.ip è l'indirizzo del proxy
  app.set('trust proxy', 1)

  // Rimuove l'intestazione X-Powered-By: non dice nulla di utile
  // e rivela lo stack
  app.disable('x-powered-by')

  // Il parsing del corpo, CON un limite
  app.use(express.json({ limit: '1mb' }))
  app.use(express.urlencoded({ extended: true, limit: '1mb' }))

  // Un identificativo per ogni richiesta, per correlare i log
  app.use((richiesta, risposta, prossimo) => {
    const id = richiesta.get('X-Request-Id') ?? crypto.randomUUID()
    richiesta.idRichiesta = id
    risposta.setHeader('X-Request-Id', id)
    prossimo()
  })

  // ── Rotte ────────────────────────────────────────────────
  app.get('/salute', (_richiesta, risposta) => {
    risposta.json({ stato: 'ok', tempoAttivo: process.uptime() })
  })

  app.use('/api/fatture', rotteFatture)

  // ── 404: dopo tutte le rotte ─────────────────────────────
  app.use((richiesta, risposta) => {
    risposta.status(404).json({ errore: 'Risorsa non trovata', percorso: richiesta.path })
  })

  // ── Gestore degli errori: QUATTRO parametri, per ULTIMO ───
  app.use(gestoreErrori)

  return app
}
```

```typescript
// src/tipi/express.d.ts — estendere il tipo Request
declare global {
  namespace Express {
    interface Request {
      idRichiesta: string
      utente?: {
        readonly id: string
        readonly ruoli: readonly string[]
      }
    }
  }
}

export {}
```

### L'ordine dei middleware è tutto

```typescript
// I middleware si eseguono NELL'ORDINE in cui sono registrati.
// Un middleware che non chiama next() interrompe la catena.

app.use(registraRichiesta) // 1. registra tutto
app.use(express.json()) // 2. analizza il corpo
app.use(autenticazione) // 3. identifica l'utente
app.use('/api', limitatoreRichieste) // 4. limita, solo su /api
app.use('/api/admin', richiedeRuolo('admin')) // 5. autorizza

// ❌ Un gestore d'errore registrato PRIMA delle rotte
//    non cattura nulla: Express lo salta perché ha 4 parametri
// app.use(gestoreErrori)
// app.get('/x', ...)

// ✅ Per ultimo
```

### Un middleware asincrono, e la trappola di Express 4

```typescript
// In Express 4 un errore in un handler async NON viene catturato:
// la Promise rifiutata non arriva al gestore d'errore, e il
// client resta appeso finché non scade il timeout.
app.get('/rotta', async (richiesta, risposta) => {
  const dati = await puoFallire() // ← in Express 4 va perso
  risposta.json(dati)
})

// La soluzione per Express 4: un wrapper
function asincrono<T extends Request>(
  gestore: (r: T, s: Response, n: NextFunction) => Promise<unknown>,
) {
  return (richiesta: T, risposta: Response, prossimo: NextFunction) => {
    void Promise.resolve(gestore(richiesta, risposta, prossimo)).catch(prossimo)
  }
}

app.get(
  '/rotta',
  asincrono(async (richiesta, risposta) => {
    const dati = await puoFallire()
    risposta.json(dati)
  }),
)
```

**Express 5 lo gestisce nativamente**: le Promise rifiutate arrivano al gestore d'errore senza wrapper. È la ragione principale per aggiornare.

### Un router modulare

```typescript
// src/rotte/fatture.ts
import { Router } from 'express'
import { z } from 'zod'
import { ErroreNonTrovato, ErroreValidazione } from '../errori.js'

export const rotteFatture = Router()

const SchemaFiltri = z.object({
  pagina: z.coerce.number().int().positive().default(1),
  perPagina: z.coerce.number().int().min(1).max(100).default(50),
  cliente: z.string().trim().min(1).optional(),
})

rotteFatture.get('/', async (richiesta, risposta) => {
  const esito = SchemaFiltri.safeParse(richiesta.query)

  if (!esito.success) {
    throw new ErroreValidazione(esito.error.flatten().fieldErrors)
  }

  const { pagina, perPagina, cliente } = esito.data
  const risultato = await servizioFatture.elenca({ pagina, perPagina, cliente })

  risposta.json({
    elementi: risultato.elementi,
    totale: risultato.totale,
    pagina,
    perPagina,
  })
})

rotteFatture.get('/:id', async (richiesta, risposta) => {
  const fattura = await servizioFatture.trova(richiesta.params.id)

  if (!fattura) {
    throw new ErroreNonTrovato('Fattura', richiesta.params.id)
  }

  risposta.json(fattura)
})
```

---

## A6. Configurazione e variabili d'ambiente

```typescript
// src/configurazione.ts
// Validare la configurazione all'AVVIO: fallire subito con un
// messaggio preciso è incomparabilmente meglio che scoprire
// alla prima query che DATABASE_URL era vuota.
import { z } from 'zod'

const SchemaConfigurazione = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),

  DATABASE_URL: z.string().url(),
  DATABASE_POOL_MAX: z.coerce.number().int().positive().default(10),

  JWT_SECRET: z.string().min(32, 'il segreto deve avere almeno 32 caratteri'),

  LOG_LEVEL: z.enum(['trace', 'debug', 'info', 'warn', 'error', 'fatal']).default('info'),

  CORS_ORIGINI: z
    .string()
    .default('')
    .transform((v) => v.split(',').map((o) => o.trim()).filter(Boolean)),

  REDIS_URL: z.string().url().optional(),
})

const esito = SchemaConfigurazione.safeParse(process.env)

if (!esito.success) {
  console.error('Configurazione non valida:\n')
  for (const [campo, errori] of Object.entries(esito.error.flatten().fieldErrors)) {
    console.error(`  ${campo}: ${errori?.join(', ')}`)
  }
  process.exit(1)
}

export const configurazione = Object.freeze(esito.data)

export const inProduzione = configurazione.NODE_ENV === 'production'
export const inSviluppo = configurazione.NODE_ENV === 'development'
```

```
# Output atteso con una configurazione errata:
Configurazione non valida:

  DATABASE_URL: Invalid url
  JWT_SECRET: il segreto deve avere almeno 32 caratteri
```

```powershell
# Node legge il file .env nativamente, senza dotenv
node --env-file=.env src/server.ts

# Più file, in ordine di precedenza
node --env-file=.env --env-file=.env.local src/server.ts
```

```
# .env — MAI in Git
DATABASE_URL=postgresql://sviluppo:locale@localhost:5432/app_dev
JWT_SECRET=una-stringa-lunga-almeno-32-caratteri-per-lo-sviluppo
LOG_LEVEL=debug
```

```
# .env.example — QUESTO va in Git
DATABASE_URL=postgresql://utente:password@localhost:5432/nome_db
JWT_SECRET=
LOG_LEVEL=info
CORS_ORIGINI=http://localhost:5173
```

```
La regola: i segreti non stanno MAI nel repository, e
la configurazione va validata prima che il server accetti
la prima richiesta. Un server che si avvia con una
configurazione incompleta fallirà comunque — ma alla
prima richiesta di un utente, con un errore incomprensibile.
```

---

# Parte B — Comprensione Profonda

---

## B1. L'event loop di Node in dettaglio

L'event loop del browser visto in `tutorial_04_javascript_fondamenti.md` ha una struttura; quello di Node ne ha una più articolata, con sei fasi.

```
   ┌───────────────────────────┐
┌─►│           timers          │  setTimeout, setInterval scaduti
│  └─────────────┬─────────────┘
│  ┌─────────────▼─────────────┐
│  │     pending callbacks     │  callback di I/O rinviati
│  └─────────────┬─────────────┘
│  ┌─────────────▼─────────────┐
│  │       idle, prepare       │  uso interno
│  └─────────────┬─────────────┘
│  ┌─────────────▼─────────────┐
│  │           poll            │  ◄─── QUI il loop passa
│  │  recupera nuovi eventi    │       la maggior parte del tempo
│  │  di I/O ed esegue i loro  │
│  │  callback                 │
│  └─────────────┬─────────────┘
│  ┌─────────────▼─────────────┐
│  │           check           │  setImmediate
│  └─────────────┬─────────────┘
│  ┌─────────────▼─────────────┐
│  │      close callbacks      │  socket.on('close')
└──┴───────────────────────────┘

  FRA OGNI FASE, e fra ogni callback dentro una fase:
    1. process.nextTick()   ← priorità più alta
    2. le microtask (Promise, await, queueMicrotask)
```

```javascript
console.log('1 — sincrono')

setTimeout(() => console.log('2 — timer'), 0)
setImmediate(() => console.log('3 — check'))

process.nextTick(() => console.log('4 — nextTick'))
Promise.resolve().then(() => console.log('5 — microtask'))

console.log('6 — sincrono')
```

```
# Output atteso:
1 — sincrono
6 — sincrono
4 — nextTick        ← nextTick precede SEMPRE le microtask
5 — microtask
2 — timer           ← l'ordine fra timer e immediate al livello
3 — check              superiore NON è deterministico: dipende
                       da quanto ci ha messo il processo ad avviarsi
```

```javascript
// Dentro un callback di I/O, invece, l'ordine È deterministico:
// setImmediate viene SEMPRE prima, perché la fase check
// segue immediatamente la fase poll
import fs from 'node:fs'

fs.readFile('file.txt', () => {
  setTimeout(() => console.log('timer'), 0)
  setImmediate(() => console.log('immediate'))
})

// Output: immediate, poi timer — sempre
```

### `process.nextTick` e la starvation

```javascript
// ⚠ nextTick ha priorità sulle microtask e su tutto il resto.
//    Una ricorsione con nextTick blocca il loop PER SEMPRE:
//    la coda non si svuota mai, e l'I/O non viene mai servito.
function ricorsivo() {
  process.nextTick(ricorsivo)
}
// ricorsivo()   ← il processo smette di rispondere

// ✅ setImmediate cede il controllo al loop
function periodico() {
  setImmediate(periodico)
}
```

**Quando usare `nextTick`:** quasi mai. Serve nelle librerie, per garantire che un evento venga emesso dopo che chi chiama ha avuto modo di registrare i listener. Nel codice applicativo, `queueMicrotask` o `setImmediate` sono più prevedibili.

### Misurare il ritardo del loop

```typescript
// Il ritardo dell'event loop è LA metrica di salute di un
// processo Node: se cresce, qualcosa sta bloccando il thread.
import { monitorEventLoopDelay, performance } from 'node:perf_hooks'

const istogramma = monitorEventLoopDelay({ resolution: 20 })
istogramma.enable()

setInterval(() => {
  const medio = istogramma.mean / 1e6 // da nanosecondi a millisecondi
  const p99 = istogramma.percentile(99) / 1e6

  if (p99 > 100) {
    registro.warn({ ritardoMedio: medio, ritardoP99: p99 }, 'event loop sotto pressione')
  }

  istogramma.reset()
}, 30_000).unref() // unref: non impedisce al processo di uscire
```

```typescript
// Rilevare i blocchi lunghi
import { PerformanceObserver } from 'node:perf_hooks'

const osservatore = new PerformanceObserver((elenco) => {
  for (const voce of elenco.getEntries()) {
    if (voce.duration > 100) {
      registro.warn({ operazione: voce.name, durata: voce.duration }, 'operazione lenta')
    }
  }
})

osservatore.observe({ entryTypes: ['function', 'measure'] })
```

### Non bloccare il loop

```typescript
// ❌ Un ciclo su un milione di elementi blocca tutte
//    le richieste in arrivo per la sua durata
function elaboraTutto(elementi: readonly Riga[]): Risultato[] {
  return elementi.map(calcoloPesante)
}

// ✅ Spezzare, cedendo il controllo al loop
import { setImmediate as cedi } from 'node:timers/promises'

async function elaboraAPezzi(
  elementi: readonly Riga[],
  dimensioneBlocco = 500,
): Promise<Risultato[]> {
  const esiti: Risultato[] = []

  for (let i = 0; i < elementi.length; i += dimensioneBlocco) {
    for (const elemento of elementi.slice(i, i + dimensioneBlocco)) {
      esiti.push(calcoloPesante(elemento))
    }

    // Cede il controllo: le richieste in coda vengono servite
    await cedi()
  }

  return esiti
}

// ✅ Per il calcolo puro e prolungato: un worker thread (B6)
```

---

## B2. Gestione centralizzata degli errori

```typescript
// src/errori.ts
export class ErroreApplicativo extends Error {
  constructor(
    messaggio: string,
    readonly statoHttp: number,
    readonly codice: string,
    readonly opzioni: { causa?: unknown; contesto?: Record<string, unknown> } = {},
  ) {
    super(messaggio, { cause: opzioni.causa })
    this.name = this.constructor.name
    Error.captureStackTrace?.(this, this.constructor)
  }

  /** Ciò che l'utente può vedere: non espone dettagli interni. */
  get messaggioPubblico(): string {
    return 'Si è verificato un errore.'
  }

  get contesto(): Record<string, unknown> {
    return this.opzioni.contesto ?? {}
  }
}

export class ErroreValidazione extends ErroreApplicativo {
  constructor(readonly campi: Record<string, readonly string[] | undefined>) {
    super(`Validazione fallita: ${Object.keys(campi).join(', ')}`, 422, 'VALIDAZIONE')
  }

  override get messaggioPubblico(): string {
    return 'Alcuni campi non sono corretti.'
  }
}

export class ErroreNonTrovato extends ErroreApplicativo {
  constructor(tipo: string, identificativo: string) {
    super(`${tipo} ${identificativo} non trovato`, 404, 'NON_TROVATO', {
      contesto: { tipo, identificativo },
    })
  }

  override get messaggioPubblico(): string {
    return 'Risorsa non trovata.'
  }
}

export class ErroreAutorizzazione extends ErroreApplicativo {
  constructor(azione: string, risorsa: string) {
    super(`Non autorizzato: ${azione} su ${risorsa}`, 403, 'AUTORIZZAZIONE')
  }

  override get messaggioPubblico(): string {
    return 'Non hai i permessi per questa operazione.'
  }
}

export class ErroreServizioEsterno extends ErroreApplicativo {
  constructor(servizio: string, causa: unknown) {
    super(`Il servizio ${servizio} non ha risposto`, 502, 'SERVIZIO_ESTERNO', {
      causa,
      contesto: { servizio },
    })
  }

  override get messaggioPubblico(): string {
    return 'Un servizio esterno non è disponibile. Riprova fra qualche minuto.'
  }
}
```

```typescript
// src/middleware/gestore-errori.ts
import type { ErrorRequestHandler } from 'express'
import { ZodError } from 'zod'
import { ErroreApplicativo } from '../errori.js'
import { inProduzione } from '../configurazione.js'

export const gestoreErrori: ErrorRequestHandler = (errore, richiesta, risposta, prossimo) => {
  // Se le intestazioni sono già state inviate, Express deve
  // chiudere la connessione: non si può inviare un'altra risposta
  if (risposta.headersSent) {
    return prossimo(errore)
  }

  const registro = richiesta.registro ?? console

  // 1. Gli errori di validazione di Zod, tradotti
  if (errore instanceof ZodError) {
    risposta.status(422).json({
      codice: 'VALIDAZIONE',
      messaggio: 'Alcuni campi non sono corretti.',
      campi: errore.flatten().fieldErrors,
    })
    return
  }

  // 2. I nostri errori: sappiamo cosa dire e con quale stato
  if (errore instanceof ErroreApplicativo) {
    // I 4xx sono normali: log a livello info o warn.
    // I 5xx sono anomalie: log a livello error.
    const livello = errore.statoHttp >= 500 ? 'error' : 'warn'

    registro[livello](
      { errore, codice: errore.codice, contesto: errore.contesto },
      errore.message,
    )

    const corpo: Record<string, unknown> = {
      codice: errore.codice,
      messaggio: errore.messaggioPubblico,
    }

    if ('campi' in errore) corpo['campi'] = errore.campi

    risposta.status(errore.statoHttp).json(corpo)
    return
  }

  // 3. Tutto il resto: è un bug. Log completo, risposta generica.
  registro.error({ errore, url: richiesta.originalUrl }, 'errore non gestito')

  risposta.status(500).json({
    codice: 'INTERNO',
    messaggio: 'Errore interno del server.',
    // Lo stack SOLO fuori dalla produzione
    ...(inProduzione ? {} : { dettaglio: String(errore), stack: (errore as Error)?.stack }),
  })
}
```

### Gli errori che sfuggono al gestore

```typescript
// src/server.ts
import { creaApp } from './app.js'
import { registro } from './registro.js'
import { configurazione } from './configurazione.js'

const app = creaApp()
const server = app.listen(configurazione.PORT, () => {
  registro.info({ porta: configurazione.PORT }, 'server avviato')
})

// Una Promise rifiutata senza catch: in Node 15+ termina
// il processo. Registrarla prima è indispensabile.
process.on('unhandledRejection', (motivo, promessa) => {
  registro.fatal({ motivo, promessa }, 'promise rifiutata senza gestione')
  spegnimentoPulito('unhandledRejection', 1)
})

// Un'eccezione non catturata: lo stato del processo è
// ora inaffidabile. Si registra e si TERMINA.
process.on('uncaughtException', (errore, origine) => {
  registro.fatal({ errore, origine }, 'eccezione non catturata')
  spegnimentoPulito('uncaughtException', 1)
})
```

```
Perché terminare invece di proseguire:

  Dopo un'eccezione non catturata, lo stato del processo
  è indefinito: una transazione può essere a metà, una
  connessione in uno stato incoerente, una variabile
  globale corrotta.

  Proseguire significa servire richieste con uno stato
  inaffidabile. Terminare e lasciare che l'orchestratore
  (systemd, Docker, Kubernetes) riavvii è più sicuro.

  La condizione è che il riavvio sia rapido e che le
  richieste in corso vengano completate: è lo spegnimento
  pulito di B7.
```

---

## B3. Stream e backpressure

> **Analogia:** travasare l'acqua da una vasca a un'altra con un tubo. Senza controllo, se la vasca di destinazione si riempie più lentamente di quanto arrivi l'acqua, straripa. La *backpressure* è il segnale che risale il tubo: "rallenta, non ce la faccio". Negli stream di Node è automatica se si usano gli strumenti giusti, e assente se si copiano i dati a mano.

```typescript
// ❌ Legge l'INTERO file in memoria: un file da 2 GB
//    fa terminare il processo per esaurimento di memoria
const contenuto = await fs.readFile('enorme.csv', 'utf8')
const righe = contenuto.split('\n')

// ✅ Uno stream: la memoria resta costante indipendentemente
//    dalla dimensione del file
import { createReadStream } from 'node:fs'
import { createInterface } from 'node:readline'

const lettore = createInterface({
  input: createReadStream('enorme.csv', { encoding: 'utf8' }),
  crlfDelay: Infinity, // gestisce i fine riga di Windows
})

for await (const riga of lettore) {
  elabora(riga)
}
```

### `pipeline`: l'unico modo corretto di concatenare

```typescript
import { pipeline } from 'node:stream/promises'
import { createReadStream, createWriteStream } from 'node:fs'
import { createGzip } from 'node:zlib'

// ❌ .pipe() NON propaga gli errori e NON distrugge gli stream
//    in caso di fallimento: restano aperti, e il descrittore
//    del file resta occupato
createReadStream('grande.csv').pipe(createGzip()).pipe(createWriteStream('grande.csv.gz'))

// ✅ pipeline gestisce errori, pulizia e backpressure
await pipeline(
  createReadStream('grande.csv'),
  createGzip({ level: 6 }),
  createWriteStream('grande.csv.gz'),
)
```

```typescript
// Con annullamento
async function comprimiConTimeout(): Promise<void> {
  const controller = new AbortController()

  setTimeout(() => controller.abort(), 30_000)

  try {
    await pipeline(sorgente, trasformazione, destinazione, { signal: controller.signal })
  } catch (errore) {
    if (errore instanceof Error && errore.name === 'AbortError') {
      registro.warn('elaborazione annullata per timeout')
    } else {
      throw errore
    }
  }
}
```

### Uno stream di trasformazione

```typescript
import { Transform } from 'node:stream'

/** Analizza righe CSV e produce oggetti. */
function analizzaCsv(): Transform {
  let intestazioni: string[] | null = null
  let residuo = ''

  return new Transform({
    // objectMode: lo stream emette oggetti invece di Buffer
    readableObjectMode: true,

    transform(pezzo: Buffer, _codifica, prossimo) {
      // Un pezzo può contenere righe incomplete: il residuo
      // viene conservato per il pezzo successivo
      const testo = residuo + pezzo.toString('utf8')
      const righe = testo.split('\n')
      residuo = righe.pop() ?? ''

      for (const riga of righe) {
        const campi = riga.trim().split(',')
        if (campi.length === 1 && campi[0] === '') continue

        if (intestazioni === null) {
          intestazioni = campi
          continue
        }

        this.push(Object.fromEntries(intestazioni.map((h, i) => [h, campi[i] ?? ''])))
      }

      prossimo()
    },

    // flush: chiamato alla fine, per l'ultima riga senza \n
    flush(prossimo) {
      if (residuo.trim() !== '' && intestazioni !== null) {
        const campi = residuo.trim().split(',')
        this.push(Object.fromEntries(intestazioni.map((h, i) => [h, campi[i] ?? ''])))
      }
      prossimo()
    },
  })
}
```

```typescript
// L'uso: importare un CSV enorme in un database, a memoria costante
import { Writable } from 'node:stream'

function scriviSuDatabase(dimensioneLotto = 500): Writable {
  let lotto: Record<string, string>[] = []

  return new Writable({
    objectMode: true,

    async write(riga: Record<string, string>, _codifica, prossimo) {
      lotto.push(riga)

      if (lotto.length >= dimensioneLotto) {
        try {
          await db.fattura.createMany({ data: lotto })
          lotto = []
        } catch (errore) {
          // Passare l'errore a next(): pipeline lo propaga
          // e distrugge tutta la catena
          return prossimo(errore as Error)
        }
      }

      prossimo()
    },

    async final(prossimo) {
      // L'ultimo lotto parziale
      if (lotto.length > 0) {
        try {
          await db.fattura.createMany({ data: lotto })
        } catch (errore) {
          return prossimo(errore as Error)
        }
      }
      prossimo()
    },
  })
}

await pipeline(createReadStream('fatture.csv'), analizzaCsv(), scriviSuDatabase())
```

### Gli stream web e la loro interoperabilità

```typescript
// Node supporta anche gli stream standard del web,
// gli stessi di fetch e del browser
import { Readable, Writable } from 'node:stream'

// Da Node stream a Web stream
const webReadable = Readable.toWeb(createReadStream('file.txt'))

// Da Web stream a Node stream
const risposta = await fetch('https://esempio.it/grande.csv')
if (!risposta.body) throw new Error('Corpo assente')

const nodeReadable = Readable.fromWeb(risposta.body)

await pipeline(nodeReadable, analizzaCsv(), scriviSuDatabase())
```

```typescript
// Restituire uno stream come risposta HTTP: la memoria
// resta costante anche esportando un milione di righe
app.get('/api/fatture/esporta', async (richiesta, risposta) => {
  risposta.setHeader('Content-Type', 'text/csv; charset=utf-8')
  risposta.setHeader('Content-Disposition', 'attachment; filename="fatture.csv"')

  try {
    await pipeline(
      // Un generatore asincrono È uno stream leggibile
      generaRigheCsv(),
      risposta,
    )
  } catch (errore) {
    // Se il client chiude la connessione a metà, l'errore
    // è previsto: non va segnalato come anomalia
    if ((errore as NodeJS.ErrnoException).code !== 'ERR_STREAM_PREMATURE_CLOSE') {
      throw errore
    }
  }
})

async function* generaRigheCsv(): AsyncGenerator<string> {
  yield 'numero,cliente,importo\n'

  let cursore: string | null = null

  // Paginazione a cursore: non carica mai tutto in memoria
  while (true) {
    const lotto = await db.fattura.findMany({
      take: 1000,
      ...(cursore ? { cursor: { id: cursore }, skip: 1 } : {}),
      orderBy: { id: 'asc' },
    })

    if (lotto.length === 0) break

    for (const f of lotto) {
      yield `${f.numero},${f.cliente},${f.importo}\n`
    }

    cursore = lotto.at(-1)?.id ?? null
  }
}
```

---

## B4. Fastify: quando e perché

```powershell
pnpm add fastify @fastify/helmet @fastify/cors @fastify/rate-limit
```

```typescript
// src/app-fastify.ts
import Fastify from 'fastify'
import { configurazione } from './configurazione.js'

export function creaApp() {
  const app = Fastify({
    logger: {
      level: configurazione.LOG_LEVEL,
      // In sviluppo, log leggibili; in produzione, JSON
      transport: configurazione.NODE_ENV === 'development'
        ? { target: 'pino-pretty' }
        : undefined,
    },
    // Un identificativo per ogni richiesta, generato da Fastify
    genReqId: (richiesta) => richiesta.headers['x-request-id']?.toString() ?? crypto.randomUUID(),
    trustProxy: true,
    bodyLimit: 1024 * 1024,
  })

  return app
}
```

### Gli schemi JSON: validazione e serializzazione

```typescript
// La differenza principale con Express: gli schemi vengono
// COMPILATI in funzioni ottimizzate. Validano l'ingresso E
// serializzano l'uscita, ed è quest'ultima a dare il guadagno
// di prestazioni.
app.get(
  '/api/fatture/:id',
  {
    schema: {
      params: {
        type: 'object',
        required: ['id'],
        properties: {
          id: { type: 'string', format: 'uuid' },
        },
      },
      response: {
        200: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            numero: { type: 'string' },
            importo: { type: 'number' },
          },
          // I campi non dichiarati vengono RIMOSSI dalla risposta:
          // è una difesa contro l'esposizione accidentale di dati
          additionalProperties: false,
        },
        404: {
          type: 'object',
          properties: {
            codice: { type: 'string' },
            messaggio: { type: 'string' },
          },
        },
      },
    },
  },
  async (richiesta, risposta) => {
    const fattura = await servizio.trova(richiesta.params.id)

    if (!fattura) {
      return risposta.code(404).send({ codice: 'NON_TROVATO', messaggio: 'Fattura non trovata' })
    }

    // passwordHash, note interne e qualunque altro campo
    // non dichiarato nello schema NON escono
    return fattura
  },
)
```

```typescript
// Con Zod, tramite un type provider
import { serializerCompiler, validatorCompiler, type ZodTypeProvider } from 'fastify-type-provider-zod'
import { z } from 'zod'

app.setValidatorCompiler(validatorCompiler)
app.setSerializerCompiler(serializerCompiler)

app.withTypeProvider<ZodTypeProvider>().get(
  '/api/fatture',
  {
    schema: {
      querystring: z.object({
        pagina: z.coerce.number().int().positive().default(1),
        cliente: z.string().optional(),
      }),
      response: {
        200: z.object({
          elementi: z.array(SchemaFattura),
          totale: z.number(),
        }),
      },
    },
  },
  async (richiesta) => {
    // richiesta.query è TIPIZZATA dallo schema
    const { pagina, cliente } = richiesta.query
    return servizio.elenca({ pagina, cliente })
  },
)
```

### I plugin e l'incapsulamento

```typescript
// In Fastify, un plugin crea un CONTESTO isolato:
// ciò che registra dentro non esce, a meno che
// non sia dichiarato con fastify-plugin
import fp from 'fastify-plugin'

// SENZA fp: l'incapsulamento resta
async function rotteFatture(app: FastifyInstance) {
  app.addHook('preHandler', autenticazione) // solo per queste rotte

  app.get('/', async () => servizio.elenca())
  app.get('/:id', async (r) => servizio.trova(r.params.id))
}

// CON fp: il decoratore è disponibile ovunque
const pluginDatabase = fp(async (app: FastifyInstance) => {
  const db = await connetti(configurazione.DATABASE_URL)

  app.decorate('db', db)

  app.addHook('onClose', async () => {
    await db.close()
  })
})

app.register(pluginDatabase)
app.register(rotteFatture, { prefix: '/api/fatture' })
```

### Il confronto onesto

```
                          Express 5        Fastify 5

Richieste/secondo         ~15.000          ~40.000
  (JSON semplice, dati indicativi: dipende
   fortemente dal carico reale)

Validazione               a mano, o Zod    schemi JSON compilati
Serializzazione           JSON.stringify   compilata (il guadagno
                                           principale)
Logging                   da aggiungere    incluso (pino)
Documentazione OpenAPI    da aggiungere    generata dagli schemi
Ecosistema                enorme           ampio, ma minore
Curva di apprendimento    bassissima       media (plugin,
                                           incapsulamento)

QUANDO EXPRESS:
  · il team lo conosce già
  · servono middleware specifici che esistono solo lì
  · il carico è modesto e la produttività conta più
    del throughput

QUANDO FASTIFY:
  · API ad alto volume
  · si vuole OpenAPI generato dagli schemi
  · la serializzazione controllata è un requisito
    (non esporre campi per errore)

La differenza di prestazioni è reale ma raramente decisiva:
in un'API che interroga un database, il collo di bottiglia
è il database, non il framework.
```

---

## B5. Logging strutturato e tracciabilità

```powershell
pnpm add pino
pnpm add -D pino-pretty
```

```typescript
// src/registro.ts
import pino from 'pino'
import { configurazione, inProduzione } from './configurazione.js'

export const registro = pino({
  level: configurazione.LOG_LEVEL,

  // In sviluppo: leggibile. In produzione: JSON su una riga,
  // che gli aggregatori di log sanno analizzare.
  transport: inProduzione ? undefined : { target: 'pino-pretty', options: { colorize: true } },

  // ⚠ La redazione dei campi sensibili non è opzionale:
  //    un log con una password dentro è un incidente
  redact: {
    paths: [
      'password',
      'passwordHash',
      '*.password',
      'req.headers.authorization',
      'req.headers.cookie',
      'req.body.password',
      'req.body.carta',
      '*.token',
      '*.segreto',
    ],
    censor: '[RIMOSSO]',
  },

  formatters: {
    level: (etichetta) => ({ level: etichetta }),
  },

  base: {
    servizio: 'api-fatture',
    versione: process.env['npm_package_version'],
    ambiente: configurazione.NODE_ENV,
  },
})
```

```typescript
// src/middleware/registro-richiesta.ts
import type { RequestHandler } from 'express'
import { registro } from '../registro.js'

export const registraRichiesta: RequestHandler = (richiesta, risposta, prossimo) => {
  const inizio = performance.now()

  // Un registro FIGLIO con il contesto della richiesta:
  // ogni log emesso durante questa richiesta porta l'id
  richiesta.registro = registro.child({
    idRichiesta: richiesta.idRichiesta,
    metodo: richiesta.method,
    percorso: richiesta.path,
  })

  risposta.on('finish', () => {
    const durata = performance.now() - inizio

    const livello =
      risposta.statusCode >= 500 ? 'error' : risposta.statusCode >= 400 ? 'warn' : 'info'

    richiesta.registro[livello](
      {
        stato: risposta.statusCode,
        durataMs: Math.round(durata),
        lunghezza: risposta.get('content-length'),
        ip: richiesta.ip,
        utente: richiesta.utente?.id,
      },
      'richiesta completata',
    )
  })

  prossimo()
}
```

```typescript
// L'uso: log strutturati, con i dati come OGGETTO
// ❌ Un messaggio interpolato non è interrogabile
registro.info(`Fattura ${id} creata da ${utente} per ${importo} euro`)

// ✅ I campi separati: si possono filtrare, aggregare, contare
registro.info({ idFattura: id, idUtente: utente, importo }, 'fattura creata')
```

### `AsyncLocalStorage`: il contesto senza inoltrarlo

```typescript
// src/contesto.ts
// Il problema: l'identificativo della richiesta serve nei log
// del livello dati, che è cinque chiamate più in basso.
// Inoltrarlo come parametro sporca ogni firma.
import { AsyncLocalStorage } from 'node:async_hooks'

type ContestoRichiesta = {
  readonly idRichiesta: string
  readonly idUtente?: string
}

export const contestoRichiesta = new AsyncLocalStorage<ContestoRichiesta>()

export function conContesto<T>(contesto: ContestoRichiesta, funzione: () => T): T {
  return contestoRichiesta.run(contesto, funzione)
}

export function leggiContesto(): ContestoRichiesta | undefined {
  return contestoRichiesta.getStore()
}
```

```typescript
// Il middleware che lo popola
app.use((richiesta, risposta, prossimo) => {
  conContesto({ idRichiesta: richiesta.idRichiesta, idUtente: richiesta.utente?.id }, () =>
    prossimo(),
  )
})
```

```typescript
// E il registro che lo legge, ovunque nello stack
export function registraConContesto(livello: pino.Level, dati: object, messaggio: string): void {
  const contesto = leggiContesto()
  registro[livello]({ ...contesto, ...dati }, messaggio)
}

// Cinque livelli sotto, senza aver inoltrato nulla:
async function salvaFattura(dati: DatiFattura) {
  registraConContesto('info', { numero: dati.numero }, 'salvataggio fattura')
}
```

`AsyncLocalStorage` mantiene il contesto attraverso `await`, callback e Promise. È il meccanismo su cui si basano i sistemi di tracciamento distribuito.

---

## B6. Worker threads

```typescript
// src/lavoratori/pool.ts
// Un pool di worker: crearne uno per richiesta costa
// ~30-50 ms di avvio, che vanifica il beneficio
import { Worker } from 'node:worker_threads'
import { availableParallelism } from 'node:os'

type Compito = {
  readonly id: number
  readonly metodo: string
  readonly argomenti: readonly unknown[]
  readonly risolvi: (valore: unknown) => void
  readonly rifiuta: (errore: Error) => void
}

export function creaPool(percorso: URL, { dimensione = availableParallelism() - 1 } = {}) {
  const lavoratori = Array.from({ length: Math.max(1, dimensione) }, () => ({
    istanza: new Worker(percorso),
    occupato: false,
  }))

  const coda: Compito[] = []
  const inVolo = new Map<number, Compito>()
  let prossimoId = 0

  for (const lavoratore of lavoratori) {
    lavoratore.istanza.on('message', (messaggio: { id: number; risultato?: unknown; errore?: { message: string; stack?: string } }) => {
      const compito = inVolo.get(messaggio.id)
      lavoratore.occupato = false

      if (compito) {
        inVolo.delete(messaggio.id)

        if (messaggio.errore) {
          const errore = new Error(messaggio.errore.message)
          errore.stack = messaggio.errore.stack
          compito.rifiuta(errore)
        } else {
          compito.risolvi(messaggio.risultato)
        }
      }

      serviCoda()
    })

    lavoratore.istanza.on('error', (errore) => {
      lavoratore.occupato = false
      // Un errore del worker non è associabile a un compito:
      // si rifiuta tutto ciò che è in volo su di lui
      for (const [id, compito] of inVolo) {
        compito.rifiuta(errore)
        inVolo.delete(id)
      }
      serviCoda()
    })
  }

  function serviCoda(): void {
    while (coda.length > 0) {
      const libero = lavoratori.find((l) => !l.occupato)
      if (!libero) return

      const compito = coda.shift()!
      libero.occupato = true
      inVolo.set(compito.id, compito)
      libero.istanza.postMessage({
        id: compito.id,
        metodo: compito.metodo,
        argomenti: compito.argomenti,
      })
    }
  }

  return {
    esegui<T>(metodo: string, ...argomenti: readonly unknown[]): Promise<T> {
      const { promise, resolve, reject } = Promise.withResolvers<T>()

      coda.push({
        id: prossimoId++,
        metodo,
        argomenti,
        risolvi: resolve as (v: unknown) => void,
        rifiuta: reject,
      })

      serviCoda()
      return promise
    },

    async termina(): Promise<void> {
      await Promise.all(lavoratori.map((l) => l.istanza.terminate()))
      for (const compito of inVolo.values()) {
        compito.rifiuta(new Error('Pool terminato'))
      }
      inVolo.clear()
    },
  }
}
```

```typescript
// src/lavoratori/calcolo.worker.ts
import { parentPort } from 'node:worker_threads'

if (!parentPort) throw new Error('Questo file va eseguito come worker')

const OPERAZIONI: Record<string, (...a: never[]) => unknown> = {
  aggrega(righe: readonly Riga[], campo: string) {
    const totali = new Map<string, number>()
    for (const riga of righe) {
      totali.set(riga[campo], (totali.get(riga[campo]) ?? 0) + riga.importo)
    }
    return Object.fromEntries(totali)
  },

  generaPdf(dati: DatiDocumento) {
    return costruisciPdf(dati)
  },
}

parentPort.on('message', async ({ id, metodo, argomenti }) => {
  try {
    const operazione = OPERAZIONI[metodo]
    if (!operazione) throw new Error(`Metodo sconosciuto: ${metodo}`)

    const risultato = await (operazione as (...a: unknown[]) => unknown)(...argomenti)
    parentPort!.postMessage({ id, risultato })
  } catch (errore) {
    // Un Error non è clonabile: va scomposto
    parentPort!.postMessage({
      id,
      errore: {
        message: errore instanceof Error ? errore.message : String(errore),
        stack: errore instanceof Error ? errore.stack : undefined,
      },
    })
  }
})
```

```typescript
// L'uso in una rotta
const pool = creaPool(new URL('./lavoratori/calcolo.worker.ts', import.meta.url))

app.post('/api/report', async (richiesta, risposta) => {
  // Il thread principale resta libero: le altre richieste
  // vengono servite normalmente
  const aggregato = await pool.esegui('aggrega', righe, 'categoria')
  risposta.json(aggregato)
})
```

```
Quando un worker conviene:

  ✅ operazioni CPU oltre i 50-100 ms
     generazione di PDF, elaborazione di immagini,
     crittografia pesante, parsing di file enormi

  ❌ operazioni brevi: il costo del passaggio dei dati
     (clonazione strutturata) supera il beneficio

  ❌ I/O: è già asincrono, un worker non aggiunge nulla

Il passaggio COPIA i dati. Per strutture grandi:
  · trasferire un ArrayBuffer (costo zero, ma lo svuota)
  · far leggere i dati AL WORKER (fetch e fs funzionano lì)
  · SharedArrayBuffer per i dati numerici
```

---

## B7. Cluster, scalabilità e spegnimento pulito

### Lo spegnimento pulito

```typescript
// src/server.ts
import { createServer } from 'node:http'
import { creaApp } from './app.js'
import { registro } from './registro.js'
import { configurazione } from './configurazione.js'
import { db } from './database.js'

const app = creaApp()
const server = createServer(app)

server.listen(configurazione.PORT, () => {
  registro.info({ porta: configurazione.PORT, pid: process.pid }, 'server avviato')
})

let inChiusura = false

async function spegnimentoPulito(segnale: string, codice = 0): Promise<void> {
  if (inChiusura) return
  inChiusura = true

  registro.info({ segnale }, 'spegnimento avviato')

  // 1. Smettere di accettare NUOVE connessioni.
  //    Le richieste in corso vengono completate.
  server.close(() => registro.info('server chiuso alle nuove connessioni'))

  // 2. Chiudere le connessioni inattive (Node 18.2+):
  //    senza, le connessioni keep-alive tengono aperto
  //    il server fino al timeout
  server.closeIdleConnections()

  // 3. Un limite: se qualcosa non si chiude, si termina comunque
  const scadenza = setTimeout(() => {
    registro.error('spegnimento non completato entro 15 s: chiusura forzata')
    process.exit(1)
  }, 15_000)
  scadenza.unref()

  try {
    // 4. Attendere che le richieste in corso finiscano
    await new Promise<void>((risolvi) => server.close(() => risolvi()))

    // 5. Chiudere le risorse, nell'ordine inverso all'apertura
    await pool.termina()
    await db.close()
    await registro.flush?.()

    clearTimeout(scadenza)
    registro.info('spegnimento completato')
    process.exit(codice)
  } catch (errore) {
    registro.error({ errore }, 'errore durante lo spegnimento')
    process.exit(1)
  }
}

// SIGTERM: l'orchestratore chiede di terminare (Docker, Kubernetes)
process.on('SIGTERM', () => void spegnimentoPulito('SIGTERM'))
// SIGINT: Ctrl+C
process.on('SIGINT', () => void spegnimentoPulito('SIGINT'))
```

```
Perché lo spegnimento pulito conta:

  Senza, un deploy termina il processo mentre sta servendo
  richieste: quegli utenti vedono un errore di connessione.
  Con un deploy ogni ora e cento richieste al secondo,
  sono centinaia di errori evitabili al giorno.

  Kubernetes invia SIGTERM e attende terminationGracePeriodSeconds
  (30 s di default) prima di SIGKILL. Il timeout dello
  spegnimento va tenuto SOTTO quella soglia.
```

### Health check: liveness e readiness

```typescript
// Sono due cose diverse, e confonderle causa riavvii inutili
app.get('/salute/vivo', (_richiesta, risposta) => {
  // LIVENESS: "il processo è vivo?"
  // Non verifica le dipendenze: se il database è giù,
  // riavviare il processo non aiuta.
  risposta.json({ stato: 'vivo', tempoAttivo: process.uptime() })
})

app.get('/salute/pronto', async (_richiesta, risposta) => {
  // READINESS: "posso servire traffico?"
  // Verifica le dipendenze: se il database è irraggiungibile,
  // il load balancer deve smettere di mandarci richieste.
  if (inChiusura) {
    return risposta.status(503).json({ stato: 'in-chiusura' })
  }

  const controlli = await Promise.allSettled([
    db.query('SELECT 1'),
    redis?.ping(),
  ])

  const problemi = controlli
    .map((c, i) => ({ c, nome: ['database', 'redis'][i] }))
    .filter(({ c }) => c.status === 'rejected')
    .map(({ nome }) => nome)

  if (problemi.length > 0) {
    return risposta.status(503).json({ stato: 'non-pronto', problemi })
  }

  risposta.json({ stato: 'pronto' })
})
```

### Cluster

```typescript
// src/cluster.ts
// Node usa un core solo: cluster ne sfrutta N,
// condividendo la stessa porta
import cluster from 'node:cluster'
import { availableParallelism } from 'node:os'
import { registro } from './registro.js'

if (cluster.isPrimary) {
  const processi = availableParallelism()
  registro.info({ processi }, 'avvio del cluster')

  for (let i = 0; i < processi; i++) cluster.fork()

  cluster.on('exit', (lavoratore, codice, segnale) => {
    registro.warn({ pid: lavoratore.process.pid, codice, segnale }, 'processo terminato')

    // Riavvia, a meno che non sia uno spegnimento voluto
    if (!lavoratore.exitedAfterDisconnect) {
      cluster.fork()
    }
  })

  process.on('SIGTERM', () => {
    for (const lavoratore of Object.values(cluster.workers ?? {})) {
      lavoratore?.disconnect()
    }
  })
} else {
  await import('./server.js')
}
```

```
Cluster o l'orchestratore:

  In un container (Docker, Kubernetes), la pratica corrente
  è UN processo Node per container, e scalare aumentando
  i container. L'orchestratore gestisce già il riavvio,
  la distribuzione del carico e il rilascio graduale.

  Cluster serve quando si esegue direttamente su una
  macchina, senza orchestratore.

  ⚠ Con cluster, lo stato in memoria NON è condiviso fra
    i processi: le sessioni, le cache e i limiti di frequenza
    vanno in Redis, o si comportano in modo incoerente.
```

---

## B8. Sicurezza: il minimo indispensabile

```powershell
pnpm add helmet cors express-rate-limit
```

```typescript
// src/app.ts — il livello di sicurezza
import helmet from 'helmet'
import cors from 'cors'
import rateLimit from 'express-rate-limit'
import { configurazione, inProduzione } from './configurazione.js'

export function applicaSicurezza(app: Express) {
  // 1. Le intestazioni di sicurezza
  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'"],
          styleSrc: ["'self'"],
          imgSrc: ["'self'", 'data:', 'https:'],
          objectSrc: ["'none'"],
          baseUri: ["'self'"],
          frameAncestors: ["'none'"],
        },
      },
      hsts: inProduzione ? { maxAge: 31_536_000, includeSubDomains: true } : false,
      crossOriginResourcePolicy: { policy: 'same-site' },
    }),
  )

  // 2. CORS: una lista di origini AMMESSE, mai un riflesso
  app.use(
    cors({
      origin(origine, callback) {
        // Le richieste senza origine (curl, app native) passano
        if (!origine) return callback(null, true)

        if (configurazione.CORS_ORIGINI.includes(origine)) {
          return callback(null, true)
        }

        callback(new Error('Origine non consentita'))
      },
      credentials: true,
      maxAge: 86_400,
    }),
  )

  // 3. Limite di frequenza
  app.use(
    '/api',
    rateLimit({
      windowMs: 15 * 60 * 1000,
      limit: 300,
      standardHeaders: 'draft-7',
      legacyHeaders: false,
      // ⚠ Con più processi serve un archivio condiviso:
      //    in memoria, ogni processo conta per conto suo
      // store: new RedisStore({ ... }),
      message: { codice: 'TROPPE_RICHIESTE', messaggio: 'Troppe richieste. Riprova più tardi.' },
    }),
  )

  // Un limite più stretto sulle rotte di autenticazione
  app.use(
    '/api/accesso',
    rateLimit({
      windowMs: 15 * 60 * 1000,
      limit: 5,
      skipSuccessfulRequests: true,
    }),
  )
}
```

```typescript
// ❌ IL RIFLESSO DELL'ORIGINE: la vulnerabilità CORS più comune.
//    Accetta QUALUNQUE origine, e con credentials: true
//    permette a un sito ostile di leggere le risposte
//    autenticate dell'utente.
app.use(
  cors({
    origin: (origine, callback) => callback(null, true), // ✗
    credentials: true,
  }),
)
```

```typescript
// La validazione dell'ingresso: al confine, sempre
import { z } from 'zod'

const SchemaCorpo = z.object({
  cliente: z.string().trim().min(1).max(200),
  importo: z.number().int().nonnegative(),
  note: z.string().max(2000).optional(),
})

app.post('/api/fatture', async (richiesta, risposta) => {
  // parse solleva un ZodError, che il gestore traduce in 422
  const dati = SchemaCorpo.parse(richiesta.body)
  const creata = await servizio.crea(dati)
  risposta.status(201).json(creata)
})
```

```
Le difese in ordine di importanza:

  1. Validare OGNI ingresso al confine (Zod)
  2. Query parametrizzate — mai concatenare SQL
  3. Segreti fuori dal repository, in variabili d'ambiente
  4. Password con scrypt o argon2, mai con SHA
  5. Intestazioni di sicurezza (helmet)
  6. CORS con lista di origini, non riflesso
  7. Limite di frequenza, più stretto sull'autenticazione
  8. Limite sulla dimensione del corpo
  9. Dipendenze verificate (pnpm audit)
 10. Log senza dati sensibili (redact)

Il trattamento sistematico è in tutorial_14_sicurezza_web.md.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Prevedere l'ordine dell'event loop di Node

**Obiettivo:** dire l'ordine esatto, poi eseguire.

```javascript
// PROBLEMA
import fs from 'node:fs'

console.log('1')

setTimeout(() => console.log('2'), 0)
setImmediate(() => console.log('3'))

process.nextTick(() => console.log('4'))
Promise.resolve().then(() => console.log('5'))

fs.readFile(import.meta.filename, () => {
  console.log('6')
  setTimeout(() => console.log('7'), 0)
  setImmediate(() => console.log('8'))
  process.nextTick(() => console.log('9'))
})

console.log('10')
```

```
# SOLUZIONE: 1 10 4 5 [2 e 3 in ordine variabile] 6 9 8 7
#
# ── FASE SINCRONA ────────────────────────────────────────────
#   '1'
#   setTimeout → coda dei timer
#   setImmediate → coda check
#   nextTick → coda nextTick (priorità massima)
#   .then → coda microtask
#   fs.readFile → parte, il callback arriverà nella fase poll
#   '10'
#
# ── FRA LE FASI ──────────────────────────────────────────────
#   '4'   nextTick viene svuotata PRIMA delle microtask
#   '5'   poi le microtask
#
# ── PRIMO GIRO DEL LOOP ──────────────────────────────────────
#   '2' e '3' in ordine NON DETERMINISTICO.
#
#   Perché: il loop entra nella fase timers e verifica se
#   setTimeout(…, 0) — che in realtà è 1 ms — è già scaduto.
#   Dipende da quanto è durato l'avvio del processo:
#     · se è passato più di 1 ms → timer prima
#     · altrimenti → il loop prosegue fino a check,
#       e immediate viene prima
#
#   Eseguendo lo script più volte si vedono entrambi gli ordini.
#
# ── QUANDO IL FILE È PRONTO (fase poll) ──────────────────────
#   '6'   il callback di readFile
#   '9'   nextTick, svuotata subito dopo il callback
#   '8'   setImmediate: la fase check segue IMMEDIATAMENTE poll
#   '7'   il timer, al giro successivo
#
#   Qui l'ordine È deterministico: dentro un callback di I/O,
#   setImmediate viene sempre prima di setTimeout, perché
#   la fase check è la prossima nel ciclo.
#
#
# LE TRE REGOLE CHE BASTANO:
#
#   1. nextTick ha priorità su TUTTO, microtask comprese
#   2. Al livello superiore, timer contro immediate è casuale
#   3. Dentro un callback di I/O, immediate viene sempre prima
```

```javascript
// La dimostrazione della non determinatezza
for (let i = 0; i < 5; i++) {
  setTimeout(() => process.stdout.write('T'), 0)
  setImmediate(() => process.stdout.write('I'))
}
// Output variabile fra esecuzioni: TTTTTIIIII, ITITITITIT, ...
```

---

### Esercizio 2 — Importare un CSV enorme a memoria costante

**Obiettivo:** importare un file da 2 GB in un database senza superare i 100 MB di memoria, con gestione degli errori e avanzamento.

```typescript
// SOLUZIONE — src/importazione/importa-csv.ts
import { createReadStream } from 'node:fs'
import { stat } from 'node:fs/promises'
import { Transform, Writable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import { registro } from '../registro.js'

export type RigaFattura = {
  numero: string
  cliente: string
  importoCentesimi: number
  emessaIl: Date
}

export class ErroreRiga extends Error {
  constructor(
    readonly numeroRiga: number,
    readonly contenuto: string,
    messaggio: string,
  ) {
    super(`Riga ${numeroRiga}: ${messaggio}`)
    this.name = 'ErroreRiga'
  }
}

/**
 * Analizza il CSV riga per riga.
 * Il residuo conserva l'ultima riga incompleta di ogni pezzo:
 * senza, le righe a cavallo di due pezzi verrebbero spezzate.
 */
function analizzaCsv({ separatore = ',', maxErrori = 100 } = {}): Transform {
  let intestazioni: string[] | null = null
  let residuo = ''
  let numeroRiga = 0
  const errori: ErroreRiga[] = []

  function analizzaRiga(riga: string): RigaFattura | null {
    numeroRiga++

    const campi = riga.split(separatore).map((c) => c.trim())

    if (intestazioni === null) {
      intestazioni = campi
      return null
    }

    if (campi.length !== intestazioni.length) {
      throw new ErroreRiga(numeroRiga, riga, `attesi ${intestazioni.length} campi, trovati ${campi.length}`)
    }

    const oggetto = Object.fromEntries(intestazioni.map((h, i) => [h, campi[i] ?? '']))

    const importo = Number(oggetto['importo'])
    if (!Number.isFinite(importo)) {
      throw new ErroreRiga(numeroRiga, riga, `importo non numerico: ${oggetto['importo']}`)
    }

    const data = new Date(oggetto['data'] ?? '')
    if (Number.isNaN(data.getTime())) {
      throw new ErroreRiga(numeroRiga, riga, `data non valida: ${oggetto['data']}`)
    }

    return {
      numero: oggetto['numero'] ?? '',
      cliente: oggetto['cliente'] ?? '',
      importoCentesimi: Math.round(importo * 100),
      emessaIl: data,
    }
  }

  const stream = new Transform({
    readableObjectMode: true,

    transform(pezzo: Buffer, _codifica, prossimo) {
      const testo = residuo + pezzo.toString('utf8')
      const righe = testo.split('\n')
      // L'ULTIMA riga può essere incompleta: si conserva
      residuo = righe.pop() ?? ''

      for (const riga of righe) {
        const pulita = riga.replace(/\r$/, '')
        if (pulita.trim() === '') continue

        try {
          const analizzata = analizzaRiga(pulita)
          if (analizzata) this.push(analizzata)
        } catch (errore) {
          if (!(errore instanceof ErroreRiga)) return prossimo(errore as Error)

          errori.push(errore)

          // Un file interamente malformato non deve produrre
          // centomila errori: si interrompe dopo la soglia
          if (errori.length > maxErrori) {
            return prossimo(
              new Error(`Superati ${maxErrori} errori di formato: il file sembra corrotto`),
            )
          }
        }
      }

      prossimo()
    },

    flush(prossimo) {
      // L'ultima riga, se il file non finisce con \n
      if (residuo.trim() !== '') {
        try {
          const analizzata = analizzaRiga(residuo.replace(/\r$/, ''))
          if (analizzata) this.push(analizzata)
        } catch (errore) {
          if (errore instanceof ErroreRiga) errori.push(errore)
        }
      }
      prossimo()
    },
  })

  // Espone gli errori raccolti a chi chiama
  Object.defineProperty(stream, 'errori', { get: () => errori })

  return stream
}

/**
 * Scrive a LOTTI: una INSERT per riga su due milioni di righe
 * significa due milioni di round-trip al database.
 */
function scriviALotti(dimensioneLotto = 1000, alProgresso?: (scritte: number) => void): Writable {
  let lotto: RigaFattura[] = []
  let scritte = 0

  async function svuota(): Promise<void> {
    if (lotto.length === 0) return

    await db.fattura.createMany({ data: lotto, skipDuplicates: true })
    scritte += lotto.length
    lotto = []
    alProgresso?.(scritte)
  }

  return new Writable({
    objectMode: true,
    // highWaterMark controlla la BACKPRESSURE: quante righe
    // il buffer accetta prima di dire "rallenta" al lettore
    highWaterMark: dimensioneLotto * 2,

    async write(riga: RigaFattura, _codifica, prossimo) {
      lotto.push(riga)

      if (lotto.length >= dimensioneLotto) {
        try {
          await svuota()
        } catch (errore) {
          return prossimo(errore as Error)
        }
      }

      prossimo()
    },

    async final(prossimo) {
      try {
        await svuota()
        prossimo()
      } catch (errore) {
        prossimo(errore as Error)
      }
    },
  })
}

export async function importaCsv(
  percorso: string,
  { signal }: { signal?: AbortSignal } = {},
): Promise<{ scritte: number; errori: readonly ErroreRiga[]; durataMs: number }> {
  const inizio = performance.now()
  const informazioni = await stat(percorso)

  registro.info({ percorso, dimensioneMb: (informazioni.size / 1024 / 1024).toFixed(1) }, 'importazione avviata')

  let ultimoAvviso = 0
  const analizzatore = analizzaCsv()

  await pipeline(
    createReadStream(percorso, { highWaterMark: 64 * 1024 }),
    analizzatore,
    scriviALotti(1000, (scritte) => {
      // Registra l'avanzamento ogni 10.000 righe, non a ogni lotto
      if (scritte - ultimoAvviso >= 10_000) {
        ultimoAvviso = scritte
        const memoria = process.memoryUsage().heapUsed / 1024 / 1024
        registro.info({ scritte, memoriaMb: memoria.toFixed(0) }, 'avanzamento')
      }
    }),
    { signal },
  )

  const errori = (analizzatore as unknown as { errori: ErroreRiga[] }).errori

  return {
    scritte: 0, // popolato dal writable in un'implementazione completa
    errori,
    durataMs: Math.round(performance.now() - inizio),
  }
}
```

```typescript
// L'uso, con annullamento
async function principale(): Promise<void> {
  const controller = new AbortController()
  process.on('SIGINT', () => controller.abort())

  const esito = await importaCsv('fatture-2026.csv', { signal: controller.signal })

  registro.info(
    { scritte: esito.scritte, errori: esito.errori.length, durataMs: esito.durataMs },
    'importazione completata',
  )

  for (const errore of esito.errori.slice(0, 10)) {
    registro.warn({ riga: errore.numeroRiga, contenuto: errore.contenuto }, errore.message)
  }
}
```

```
# Output atteso su un file da 2 GB:
{"level":"info","percorso":"fatture-2026.csv","dimensioneMb":"2048.0","msg":"importazione avviata"}
{"level":"info","scritte":10000,"memoriaMb":"64","msg":"avanzamento"}
{"level":"info","scritte":20000,"memoriaMb":"66","msg":"avanzamento"}
...
{"level":"info","scritte":8400000,"memoriaMb":"71","msg":"avanzamento"}
{"level":"info","scritte":8400000,"errori":23,"durataMs":412000,"msg":"importazione completata"}
```

```
# I punti che rendono l'importazione corretta:
#
# 1. MEMORIA COSTANTE: ~70 MB su un file da 2 GB.
#    Con readFile, il processo sarebbe terminato per
#    esaurimento di memoria intorno ai 2 GB.
#
# 2. IL RESIDUO fra i pezzi.
#    Un pezzo da 64 kB taglia quasi sempre a metà una riga.
#    Senza conservarla, una riga su ottocento verrebbe
#    spezzata e persa.
#
# 3. LA SCRITTURA A LOTTI.
#    Una INSERT per riga: 8,4 milioni di round-trip.
#    A lotti da 1000: 8.400. La differenza sono ore.
#
# 4. LA BACKPRESSURE.
#    highWaterMark sul writable dice al lettore quando
#    rallentare. Con pipeline è automatica: se il database
#    è lento, la lettura del file rallenta di conseguenza.
#    Con .pipe() o con un ciclo manuale, il buffer cresce
#    senza limite.
#
# 5. GLI ERRORI DI RIGA NON FERMANO TUTTO.
#    Una riga malformata su otto milioni non deve annullare
#    l'importazione. Ma oltre una soglia, il file è corrotto
#    e proseguire è inutile.
#
# 6. pipeline INVECE DI .pipe().
#    Se il database va giù a metà, pipeline distrugge tutta
#    la catena e chiude il descrittore del file. Con .pipe()
#    lo stream di lettura resterebbe aperto.
```

---

### Esercizio 3 — Middleware di autenticazione con contesto

**Obiettivo:** un middleware che verifica il token, popola il contesto e propaga l'identificativo della richiesta in tutto lo stack.

```typescript
// SOLUZIONE — src/middleware/autenticazione.ts
import type { RequestHandler } from 'express'
import { createHmac, timingSafeEqual } from 'node:crypto'
import { ErroreAutorizzazione } from '../errori.js'
import { configurazione } from '../configurazione.js'
import { conContesto } from '../contesto.js'

export type Utente = {
  readonly id: string
  readonly ruoli: readonly string[]
}

class ErroreToken extends ErroreApplicativo {
  constructor(motivo: string) {
    super(`Token non valido: ${motivo}`, 401, 'TOKEN_NON_VALIDO')
  }

  override get messaggioPubblico(): string {
    return 'Sessione non valida o scaduta.'
  }
}

/** Verifica un token firmato, con confronto a tempo costante. */
function verificaToken(token: string): Utente {
  const parti = token.split('.')
  if (parti.length !== 3) throw new ErroreToken('formato')

  const [intestazione, payload, firma] = parti as [string, string, string]

  const attesa = createHmac('sha256', configurazione.JWT_SECRET)
    .update(`${intestazione}.${payload}`)
    .digest('base64url')

  // ⚠ Il confronto DEVE essere a tempo costante: === esce
  //    al primo byte diverso, e permette di ricostruire la
  //    firma misurando i tempi di risposta
  const a = Buffer.from(attesa)
  const b = Buffer.from(firma)

  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    throw new ErroreToken('firma')
  }

  const dati = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8')) as {
    sub?: string
    ruoli?: string[]
    exp?: number
  }

  if (typeof dati.exp !== 'number' || dati.exp * 1000 < Date.now()) {
    throw new ErroreToken('scaduto')
  }

  if (typeof dati.sub !== 'string') throw new ErroreToken('soggetto mancante')

  return { id: dati.sub, ruoli: dati.ruoli ?? [] }
}

/** Popola richiesta.utente se il token c'è ed è valido. Non blocca. */
export const autenticazioneOpzionale: RequestHandler = (richiesta, _risposta, prossimo) => {
  const intestazione = richiesta.get('Authorization')

  if (intestazione?.startsWith('Bearer ')) {
    try {
      richiesta.utente = verificaToken(intestazione.slice(7))
    } catch {
      // Token non valido: si prosegue come anonimo.
      // Sarà 'richiedeAutenticazione' a bloccare se serve.
    }
  }

  // Il contesto attraversa await, callback e Promise:
  // ogni log emesso durante questa richiesta lo porta con sé
  conContesto(
    { idRichiesta: richiesta.idRichiesta, idUtente: richiesta.utente?.id },
    () => prossimo(),
  )
}

/** Blocca se non autenticato. */
export const richiedeAutenticazione: RequestHandler = (richiesta, _risposta, prossimo) => {
  if (!richiesta.utente) {
    return prossimo(new ErroreToken('assente'))
  }
  prossimo()
}

/** Blocca se manca il ruolo. */
export function richiedeRuolo(...ruoliAmmessi: readonly string[]): RequestHandler {
  return (richiesta, _risposta, prossimo) => {
    if (!richiesta.utente) {
      return prossimo(new ErroreToken('assente'))
    }

    const autorizzato = ruoliAmmessi.some((r) => richiesta.utente!.ruoli.includes(r))

    if (!autorizzato) {
      return prossimo(
        new ErroreAutorizzazione(`${richiesta.method} ${richiesta.path}`, ruoliAmmessi.join('|')),
      )
    }

    prossimo()
  }
}
```

```typescript
// L'uso, con la composizione dei middleware
import { Router } from 'express'

export const rotteAmministrazione = Router()

// L'ordine conta: autenticazione, poi autorizzazione
rotteAmministrazione.use(richiedeAutenticazione)
rotteAmministrazione.use(richiedeRuolo('admin'))

rotteAmministrazione.get('/utenti', async (_richiesta, risposta) => {
  // A questo punto richiesta.utente esiste ed è admin
  risposta.json(await servizioUtenti.elenca())
})

// Oppure per singola rotta
app.delete(
  '/api/fatture/:id',
  richiedeAutenticazione,
  richiedeRuolo('admin', 'contabile'),
  async (richiesta, risposta) => {
    await servizio.elimina(richiesta.params.id)
    risposta.status(204).end()
  },
)
```

```typescript
// Il test del confronto a tempo costante
import { describe, it, expect } from 'vitest'

describe('verificaToken', () => {
  it('rifiuta una firma manomessa', () => {
    const valido = firmaToken({ sub: 'u-1', exp: Date.now() / 1000 + 3600 })
    const manomesso = valido.slice(0, -4) + 'AAAA'

    expect(() => verificaToken(manomesso)).toThrow('firma')
  })

  it('rifiuta un token scaduto', () => {
    const scaduto = firmaToken({ sub: 'u-1', exp: Date.now() / 1000 - 1 })
    expect(() => verificaToken(scaduto)).toThrow('scaduto')
  })

  it('il tempo di verifica non dipende da quanti byte combaciano', () => {
    // Un test indicativo: la varianza deve essere piccola
    const valido = firmaToken({ sub: 'u-1', exp: Date.now() / 1000 + 3600 })
    const [i, p] = valido.split('.')

    const tempi = ['A'.repeat(43), valido.split('.')[2]!.slice(0, 40) + 'AAA'].map((firma) => {
      const inizio = performance.now()
      try {
        verificaToken(`${i}.${p}.${firma}`)
      } catch {
        /* atteso */
      }
      return performance.now() - inizio
    })

    // Con === la differenza sarebbe sistematica
    expect(Math.abs(tempi[0]! - tempi[1]!)).toBeLessThan(1)
  })
})
```

```
# Le decisioni di progetto:
#
# 1. OPZIONALE E OBBLIGATORIO SEPARATI.
#    Molte rotte cambiano comportamento se c'è un utente,
#    senza richiederlo. Un middleware unico che blocca
#    costringerebbe a duplicare le rotte.
#
# 2. IL CONFRONTO A TEMPO COSTANTE.
#    === esce al primo byte diverso. Misurando i tempi di
#    risposta su migliaia di tentativi, un attaccante
#    ricostruisce la firma un byte alla volta. timingSafeEqual
#    confronta sempre tutti i byte.
#
# 3. IL CONTESTO CON AsyncLocalStorage.
#    L'identificativo della richiesta serve nei log del
#    livello dati, cinque chiamate più in basso. Inoltrarlo
#    come parametro sporcherebbe ogni firma della codebase.
#
# 4. GLI ERRORI PASSANO DA next(), NON DA throw.
#    In Express 4 un throw dentro un middleware sincrono
#    funziona, ma in uno asincrono no. next(errore) funziona
#    sempre, ed è la forma da preferire.
#
# 5. IL MESSAGGIO PUBBLICO NON DICE PERCHÉ.
#    "Sessione non valida o scaduta" invece di "firma non
#    valida": distinguere i motivi aiuta chi attacca.
#    Il motivo preciso resta nei log.
```

---

## C2. Mini-progetto: server Express modulare

L'esercizio chiave del modulo: un server Express con middleware personalizzati e gestione centralizzata degli errori, pronto per la produzione.

### Struttura

```
api-fatture/
├── package.json
├── tsconfig.json
├── .env.example
├── Dockerfile
└── src/
    ├── server.ts              avvio, segnali, spegnimento pulito
    ├── app.ts                 composizione dei middleware
    ├── configurazione.ts      validata con Zod all'avvio
    ├── registro.ts            pino, con redazione
    ├── contesto.ts            AsyncLocalStorage
    ├── errori.ts              la gerarchia
    ├── database.ts            pool di connessioni
    ├── middleware/
    │   ├── registro-richiesta.ts
    │   ├── autenticazione.ts
    │   ├── sicurezza.ts
    │   └── gestore-errori.ts
    ├── rotte/
    │   ├── salute.ts
    │   └── fatture.ts
    └── servizi/
        └── fatture.ts
```

### `src/app.ts`

```typescript
import express, { type Express } from 'express'
import { randomUUID } from 'node:crypto'
import { registraRichiesta } from './middleware/registro-richiesta.js'
import { autenticazioneOpzionale } from './middleware/autenticazione.js'
import { applicaSicurezza } from './middleware/sicurezza.js'
import { gestoreErrori } from './middleware/gestore-errori.js'
import { rotteSalute } from './rotte/salute.js'
import { rotteFatture } from './rotte/fatture.js'

export function creaApp(): Express {
  const app = express()

  // ── 1. Impostazioni di base ──────────────────────────────
  app.set('trust proxy', 1)
  app.disable('x-powered-by')
  // etag sui JSON: permette le risposte 304
  app.set('etag', 'strong')

  // ── 2. Identificativo della richiesta ────────────────────
  // Prima di tutto: serve anche ai log degli errori
  app.use((richiesta, risposta, prossimo) => {
    const id = richiesta.get('X-Request-Id') ?? randomUUID()
    richiesta.idRichiesta = id
    risposta.setHeader('X-Request-Id', id)
    prossimo()
  })

  // ── 3. Logging ───────────────────────────────────────────
  app.use(registraRichiesta)

  // ── 4. Sicurezza: helmet, CORS, limite di frequenza ──────
  applicaSicurezza(app)

  // ── 5. Parsing del corpo, CON limite ─────────────────────
  app.use(express.json({ limit: '1mb' }))
  app.use(express.urlencoded({ extended: true, limit: '1mb' }))

  // ── 6. Autenticazione opzionale ──────────────────────────
  app.use(autenticazioneOpzionale)

  // ── 7. Rotte ─────────────────────────────────────────────
  // La salute PRIMA del limite di frequenza: l'orchestratore
  // la interroga di continuo e non deve essere limitato
  app.use('/salute', rotteSalute)
  app.use('/api/fatture', rotteFatture)

  // ── 8. 404, dopo tutte le rotte ──────────────────────────
  app.use((richiesta, risposta) => {
    risposta.status(404).json({
      codice: 'NON_TROVATO',
      messaggio: 'Risorsa non trovata.',
      percorso: richiesta.path,
    })
  })

  // ── 9. Gestore degli errori: PER ULTIMO, 4 parametri ─────
  app.use(gestoreErrori)

  return app
}
```

### `src/rotte/fatture.ts`

```typescript
import { Router } from 'express'
import { z } from 'zod'
import { richiedeAutenticazione, richiedeRuolo } from '../middleware/autenticazione.js'
import { ErroreNonTrovato } from '../errori.js'
import { servizioFatture } from '../servizi/fatture.js'

export const rotteFatture = Router()

const SchemaFiltri = z.object({
  pagina: z.coerce.number().int().positive().default(1),
  perPagina: z.coerce.number().int().min(1).max(100).default(50),
  cliente: z.string().trim().min(1).max(200).optional(),
  stato: z.enum(['bozza', 'emessa', 'pagata', 'annullata']).optional(),
})

const SchemaCreazione = z.object({
  cliente: z.string().trim().min(1).max(200),
  importoCentesimi: z.number().int().nonnegative(),
  scadeIl: z.coerce.date(),
  righe: z
    .array(
      z.object({
        descrizione: z.string().min(1).max(500),
        quantita: z.number().positive(),
        prezzoUnitarioCentesimi: z.number().int().nonnegative(),
      }),
    )
    .min(1, 'serve almeno una riga'),
})

rotteFatture.use(richiedeAutenticazione)

// GET /api/fatture
rotteFatture.get('/', async (richiesta, risposta) => {
  // parse solleva ZodError, che il gestore traduce in 422
  const filtri = SchemaFiltri.parse(richiesta.query)

  const esito = await servizioFatture.elenca({
    ...filtri,
    idUtente: richiesta.utente!.id,
  })

  // Le intestazioni di paginazione: standard e utili ai client
  risposta.setHeader('X-Total-Count', String(esito.totale))
  risposta.json({
    elementi: esito.elementi,
    totale: esito.totale,
    pagina: filtri.pagina,
    perPagina: filtri.perPagina,
  })
})

// GET /api/fatture/:id
rotteFatture.get('/:id', async (richiesta, risposta) => {
  const fattura = await servizioFatture.trova(richiesta.params.id, richiesta.utente!.id)

  if (!fattura) {
    // L'errore arriva al gestore centralizzato tramite il
    // supporto nativo di Express 5 alle Promise rifiutate
    throw new ErroreNonTrovato('Fattura', richiesta.params.id)
  }

  risposta.json(fattura)
})

// POST /api/fatture
rotteFatture.post('/', richiedeRuolo('admin', 'contabile'), async (richiesta, risposta) => {
  const dati = SchemaCreazione.parse(richiesta.body)

  const creata = await servizioFatture.crea({ ...dati, idUtente: richiesta.utente!.id })

  richiesta.registro.info({ idFattura: creata.id, numero: creata.numero }, 'fattura creata')

  // 201 con Location: la convenzione REST
  risposta.status(201).location(`/api/fatture/${creata.id}`).json(creata)
})

// DELETE /api/fatture/:id
rotteFatture.delete('/:id', richiedeRuolo('admin'), async (richiesta, risposta) => {
  const eliminata = await servizioFatture.elimina(richiesta.params.id, richiesta.utente!.id)

  if (!eliminata) {
    throw new ErroreNonTrovato('Fattura', richiesta.params.id)
  }

  richiesta.registro.warn({ idFattura: richiesta.params.id }, 'fattura eliminata')

  // 204: nessun contenuto
  risposta.status(204).end()
})
```

### `Dockerfile`

```dockerfile
# Multi-stage: l'immagine finale non contiene il compilatore
# né le dipendenze di sviluppo

# ── Stadio 1: le dipendenze ──────────────────────────────────
FROM node:24-alpine AS dipendenze
WORKDIR /app

RUN corepack enable
COPY package.json pnpm-lock.yaml ./
# --frozen-lockfile: fallisce se il lockfile non combacia
RUN pnpm install --frozen-lockfile

# ── Stadio 2: la build ───────────────────────────────────────
FROM node:24-alpine AS build
WORKDIR /app

RUN corepack enable
COPY --from=dipendenze /app/node_modules ./node_modules
COPY . .
RUN pnpm exec tsc

# Rimuove le dipendenze di sviluppo
RUN pnpm prune --prod

# ── Stadio 3: l'immagine finale ──────────────────────────────
FROM node:24-alpine AS produzione
WORKDIR /app

ENV NODE_ENV=production

# Utente non privilegiato: l'immagine node ne fornisce uno
USER node

COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
COPY --from=build --chown=node:node /app/package.json ./

EXPOSE 3000

# dumb-init o --init gestiscono la propagazione dei segnali:
# senza, SIGTERM non arriva a Node e lo spegnimento pulito
# non parte mai
# (docker run --init, oppure ENTRYPOINT ["dumb-init", "--"])

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://localhost:3000/salute/pronto').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "dist/server.js"]
```

### Verifica

```powershell
# 1. I tipi
pnpm exec tsc --noEmit

# 2. La configurazione fallisce con un messaggio chiaro
$env:DATABASE_URL = ""
node dist/server.js
# Deve stampare "Configurazione non valida: DATABASE_URL: Invalid url"
# ed uscire con codice 1

# 3. Il server risponde
pnpm start
curl http://localhost:3000/salute/vivo
curl http://localhost:3000/salute/pronto
```

```
# I controlli, in ordine:
#
# 1. GLI ERRORI ARRIVANO AL GESTORE
#    curl -X POST http://localhost:3000/api/fatture -d '{}'
#    → 422 con i campi mancanti elencati, non 500
#
#    Una rotta che solleva un errore asincrono → 500 con
#    codice 'INTERNO', E lo stack nei log (non nella risposta)
#
# 2. L'IDENTIFICATIVO DELLA RICHIESTA
#    curl -i http://localhost:3000/salute/vivo
#    → l'intestazione X-Request-Id nella risposta
#    → lo stesso id in TUTTI i log di quella richiesta
#
# 3. I LOG NON CONTENGONO SEGRETI
#    curl -X POST .../accesso -d '{"password":"segretissima"}'
#    Cerca 'segretissima' nei log: non deve comparire.
#    La redazione di pino deve averla sostituita con [RIMOSSO]
#
# 4. IL LIMITE SUL CORPO
#    Invia 2 MB di JSON → 413, non un processo che consuma memoria
#
# 5. LO SPEGNIMENTO PULITO
#    · Avvia una richiesta lenta
#    · Invia SIGTERM (Ctrl+C, o docker stop)
#    · La richiesta in corso DEVE completarsi
#    · Le nuove connessioni vengono rifiutate
#    · Il processo esce entro 15 secondi
#
# 6. IL SEGNALE ARRIVA NEL CONTAINER
#    docker run --init …
#    docker stop <container>
#    Nei log deve comparire "spegnimento avviato".
#    Se non compare, il segnale non arriva a Node: manca --init
#    o l'ENTRYPOINT è sbagliato.
#
# 7. L'IMMAGINE NON CONTIENE IL SORGENTE
#    docker run --rm --entrypoint sh <immagine> -c "ls /app"
#    → solo dist, node_modules e package.json
#
# 8. IL PROCESSO NON GIRA COME ROOT
#    docker run --rm --entrypoint id <immagine>
#    → uid=1000(node)
```

```
# I meccanismi del tutorial usati, e dove:
#
#   configurazione validata   fallisce all'avvio, non alla prima richiesta
#   AsyncLocalStorage         l'id della richiesta nei log profondi
#   gerarchia di errori       statoHttp e messaggioPubblico sulla classe
#   gestore centralizzato     un posto solo per tradurre gli errori
#   redazione dei log         le password non finiscono su disco
#   spegnimento pulito        i deploy non interrompono le richieste
#   liveness ≠ readiness      il database giù non causa riavvii inutili
#   multi-stage Docker        l'immagine finale non ha il compilatore
#   utente non privilegiato   un'escalation nel container non dà root
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Diagnostica e profiling in produzione

### Il profilo della CPU

```powershell
# Avviare con il profiler
node --cpu-prof --cpu-prof-dir=./profili dist/server.js

# Il file .cpuprofile si apre in Chrome DevTools:
# chrome://inspect → Open dedicated DevTools for Node → Profiler → Load
```

```typescript
// Profilare a comando, in produzione, senza riavviare
import { Session } from 'node:inspector/promises'
import { writeFile } from 'node:fs/promises'

let sessione: Session | null = null

export async function avviaProfilazione(): Promise<void> {
  sessione = new Session()
  sessione.connect()
  await sessione.post('Profiler.enable')
  await sessione.post('Profiler.start')
}

export async function fermaProfilazione(percorso: string): Promise<void> {
  if (!sessione) throw new Error('Nessuna profilazione in corso')

  const { profile } = await sessione.post('Profiler.stop')
  await writeFile(percorso, JSON.stringify(profile))

  sessione.disconnect()
  sessione = null
}
```

```typescript
// Una rotta protetta per attivarlo quando serve
app.post('/interno/profilo/avvia', richiedeRuolo('operazioni'), async (_r, risposta) => {
  await avviaProfilazione()
  risposta.json({ stato: 'profilazione avviata' })
})

app.post('/interno/profilo/ferma', richiedeRuolo('operazioni'), async (_r, risposta) => {
  const percorso = `/tmp/profilo-${Date.now()}.cpuprofile`
  await fermaProfilazione(percorso)
  risposta.json({ percorso })
})
```

### Gli heap snapshot e i memory leak

```powershell
# Uno snapshot a comando
node --heapsnapshot-signal=SIGUSR2 dist/server.js
# Poi, da un altro terminale:
kill -USR2 <pid>
```

```typescript
// Da codice
import { writeHeapSnapshot } from 'node:v8'

app.post('/interno/heap', richiedeRuolo('operazioni'), (_richiesta, risposta) => {
  const percorso = writeHeapSnapshot(`/tmp/heap-${Date.now()}.heapsnapshot`)
  risposta.json({ percorso })
})
```

```
La procedura per trovare un leak:

  1. Snapshot subito dopo l'avvio, a regime
  2. Genera carico per qualche minuto
  3. Forza la garbage collection (--expose-gc, global.gc())
  4. Secondo snapshot
  5. In Chrome DevTools → Memory → carica entrambi
     → "Comparison": mostra il delta

  Cosa cercare:
    · oggetti il cui conteggio cresce e non scende
    · closure che trattengono richieste concluse
    · listener accumulati su un EventEmitter
    · una Map o un array globale che non viene mai svuotato
```

```typescript
// Il monitoraggio continuo della memoria
import { registro } from './registro.js'

setInterval(() => {
  const memoria = process.memoryUsage()
  const mb = (b: number) => Math.round(b / 1024 / 1024)

  registro.info(
    {
      heapUsato: mb(memoria.heapUsed),
      heapTotale: mb(memoria.heapTotal),
      rss: mb(memoria.rss),
      esterno: mb(memoria.external),
      arrayBuffer: mb(memoria.arrayBuffers),
    },
    'memoria',
  )

  // Un allarme quando l'heap supera una soglia
  if (memoria.heapUsed > 1024 * 1024 * 1024) {
    registro.warn({ heapUsato: mb(memoria.heapUsed) }, 'heap oltre 1 GB')
  }
}, 60_000).unref()
```

### `MaxListenersExceededWarning`

```typescript
// Un avviso che indica quasi sempre un leak:
// listener aggiunti in un ciclo e mai rimossi
process.on('warning', (avviso) => {
  registro.warn({ nome: avviso.name, messaggio: avviso.message, stack: avviso.stack }, 'avviso')
})

// Per trovarne l'origine:
// node --trace-warnings dist/server.js
```

### Il tracciamento distribuito

```powershell
pnpm add @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node @opentelemetry/exporter-trace-otlp-http
```

```typescript
// src/telemetria.ts — va importato PRIMA di tutto il resto
import { NodeSDK } from '@opentelemetry/sdk-node'
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { resourceFromAttributes } from '@opentelemetry/resources'

const sdk = new NodeSDK({
  resource: resourceFromAttributes({
    'service.name': 'api-fatture',
    'service.version': process.env['npm_package_version'] ?? '0.0.0',
    'deployment.environment': process.env['NODE_ENV'] ?? 'development',
  }),

  traceExporter: new OTLPTraceExporter({
    url: process.env['OTEL_EXPORTER_OTLP_ENDPOINT'],
  }),

  instrumentations: [
    getNodeAutoInstrumentations({
      // Il filesystem produce un rumore enorme
      '@opentelemetry/instrumentation-fs': { enabled: false },
    }),
  ],
})

sdk.start()

process.on('SIGTERM', () => {
  void sdk.shutdown().finally(() => process.exit(0))
})
```

```powershell
# Va caricato prima del codice applicativo
node --import ./dist/telemetria.js dist/server.js
```

L'auto-instrumentation traccia HTTP, il database, Redis e le chiamate in uscita senza modificare il codice. Il tema è approfondito in `31-osservabilita-otel-prometheus.md` del dominio Python, e in `tutorial_19_troubleshooting.md`.

---

## D2. Il permission model

Da Node 20 esiste un modello di permessi: il processo può essere limitato a leggere e scrivere solo certi percorsi, e a non avviare processi figli.

```powershell
# Node 20-22: sperimentale
node --experimental-permission --allow-fs-read=./dist --allow-fs-write=./log dist/server.js

# Node 23+: stabile, senza il prefisso experimental
node --permission --allow-fs-read=./dist --allow-fs-write=./log dist/server.js
```

```
I permessi disponibili:

  --allow-fs-read=<percorso>    lettura, ripetibile
  --allow-fs-write=<percorso>   scrittura, ripetibile
  --allow-child-process         avviare processi figli
  --allow-worker                creare worker threads
  --allow-addons                caricare addon nativi

Senza un flag, l'operazione corrispondente solleva
ERR_ACCESS_DENIED.
```

```typescript
// Verificare i permessi da codice
if (process.permission) {
  console.log(process.permission.has('fs.read', '/etc/passwd')) // false
  console.log(process.permission.has('fs.write', './log')) // true
  console.log(process.permission.has('child'))
}
```

```typescript
// Gestire il rifiuto
async function leggiConPermessi(percorso: string): Promise<string> {
  try {
    return await fs.readFile(percorso, 'utf8')
  } catch (errore) {
    if ((errore as NodeJS.ErrnoException).code === 'ERR_ACCESS_DENIED') {
      registro.error({ errore, percorso }, 'accesso negato dal permission model')
    }
    throw errore
  }
}
```

```
Cosa il permission model protegge:

  ✅ una dipendenza compromessa che legge ~/.ssh o .env
  ✅ una traversal che sfugge alla validazione
  ✅ l'esecuzione di comandi di sistema da codice iniettato

Cosa NON protegge:
  ❌ la rete: non ci sono permessi di rete
  ❌ ciò che il processo può già leggere
  ❌ le vulnerabilità logiche dell'applicazione

È un livello aggiuntivo di difesa in profondità, non un
sostituto della validazione. In un container che gira
già come utente non privilegiato con un filesystem
in sola lettura, il guadagno marginale è modesto.
```

---

## D3. Supply chain e integrità delle dipendenze

```powershell
# Le vulnerabilità note
pnpm audit
pnpm audit --audit-level high

# Cosa è obsoleto
pnpm outdated

# Chi ha portato dentro un pacchetto
pnpm why lodash
```

```
# .npmrc — le difese di base
# Nessuno script di dipendenza si esegue automaticamente
enable-pre-post-scripts=false

# Solo pacchetti pubblicati da almeno 3 giorni:
# la finestra in cui i pacchetti compromessi vengono rimossi
minimum-release-age=4320
```

```yaml
# pnpm-workspace.yaml — solo questi pacchetti possono
# eseguire script di build (servono binari nativi)
onlyBuiltDependencies:
  - esbuild
  - sharp
  - '@prisma/engines'
```

```
Perché gli script postinstall sono il vettore principale:

  Un pacchetto compromesso esegue codice arbitrario CON
  I TUOI PERMESSI al momento dell'installazione — sulla
  tua macchina, e nella pipeline di CI dove ci sono
  i token di deploy.

  L'attacco tipico: un pacchetto popolare viene compromesso,
  il postinstall cerca .env, ~/.aws/credentials, ~/.npmrc
  e li invia a un server remoto.

  Disattivare gli script e autorizzare solo quelli che
  servono davvero elimina la superficie.
```

### Bloccare le versioni

```json
// package.json — pinning esatto per le dipendenze critiche
{
  "dependencies": {
    "express": "5.1.0",
    "zod": "3.24.1"
  },
  "pnpm": {
    "overrides": {
      // Forzare una versione corretta in tutto l'albero,
      // anche nelle dipendenze transitive.
      // Rimuovere quando la correzione arriva a monte.
      "pacchetto-vulnerabile": ">=4.17.21"
    }
  }
}
```

```powershell
# In CI: fallisce se il lockfile non combacia con package.json
pnpm install --frozen-lockfile
```

### Generare un SBOM

```powershell
# Un inventario delle dipendenze, per l'audit e la conformità
pnpm dlx @cyclonedx/cyclonedx-npm --output-file sbom.json
```

```yaml
# .github/workflows/sicurezza.yml
name: Sicurezza

on:
  push:
    branches: [main]
  schedule:
    # Una verifica settimanale: le vulnerabilità vengono
    # pubblicate anche quando il codice non cambia
    - cron: '0 6 * * 1'

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: '.nvmrc'
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile --ignore-scripts

      - name: Vulnerabilità note
        run: pnpm audit --audit-level high

      - name: SBOM
        run: pnpm dlx @cyclonedx/cyclonedx-npm --output-file sbom.json

      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.json
```

---

## D4. Testare un server

```typescript
// Node ha un test runner nel core: nessuna dipendenza
// node --test
import { test, describe, before, after } from 'node:test'
import assert from 'node:assert/strict'

describe('servizioFatture', () => {
  before(async () => {
    await preparaDatabaseDiProva()
  })

  after(async () => {
    await pulisciDatabaseDiProva()
  })

  test('calcola il totale dalle righe', () => {
    const totale = calcolaTotale([
      { quantita: 2, prezzoUnitarioCentesimi: 1000 },
      { quantita: 3, prezzoUnitarioCentesimi: 500 },
    ])

    assert.equal(totale, 3500)
  })
})
```

```powershell
node --test
node --test --watch
node --test --experimental-test-coverage
```

### Testare le rotte con Supertest

```powershell
pnpm add -D supertest @types/supertest vitest
```

```typescript
import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest'
import request from 'supertest'
import { creaApp } from '../src/app.js'

describe('API fatture', () => {
  const app = creaApp()
  let token: string

  beforeAll(async () => {
    token = firmaTokenDiProva({ sub: 'u-1', ruoli: ['contabile'] })
  })

  it('rifiuta una richiesta senza token', async () => {
    const risposta = await request(app).get('/api/fatture')

    expect(risposta.status).toBe(401)
    expect(risposta.body.codice).toBe('TOKEN_NON_VALIDO')
  })

  it('restituisce 422 con i campi non validi', async () => {
    const risposta = await request(app)
      .post('/api/fatture')
      .set('Authorization', `Bearer ${token}`)
      .send({ cliente: '', importoCentesimi: -5 })

    expect(risposta.status).toBe(422)
    expect(risposta.body.campi).toHaveProperty('cliente')
    expect(risposta.body.campi).toHaveProperty('importoCentesimi')
  })

  it('crea una fattura e restituisce Location', async () => {
    const risposta = await request(app)
      .post('/api/fatture')
      .set('Authorization', `Bearer ${token}`)
      .send({
        cliente: 'Rossi',
        importoCentesimi: 120_000,
        scadeIl: '2026-12-31',
        righe: [{ descrizione: 'Consulenza', quantita: 1, prezzoUnitarioCentesimi: 120_000 }],
      })

    expect(risposta.status).toBe(201)
    expect(risposta.headers['location']).toMatch(/^\/api\/fatture\//)
    expect(risposta.body.numero).toBeDefined()
  })

  it('non espone mai il messaggio interno di un errore 500', async () => {
    vi.spyOn(servizioFatture, 'elenca').mockRejectedValue(
      new Error('connessione al database persa su db-prod-01:5432'),
    )

    const risposta = await request(app).get('/api/fatture').set('Authorization', `Bearer ${token}`)

    expect(risposta.status).toBe(500)
    // Il dettaglio interno NON deve uscire
    expect(JSON.stringify(risposta.body)).not.toContain('db-prod-01')
    expect(risposta.body.messaggio).toBe('Errore interno del server.')
  })

  it('include X-Request-Id nella risposta', async () => {
    const risposta = await request(app).get('/salute/vivo')
    expect(risposta.headers['x-request-id']).toBeDefined()
  })
})
```

### Testcontainers: un database vero, isolato

```powershell
pnpm add -D testcontainers
```

```typescript
import { PostgreSqlContainer, type StartedPostgreSqlContainer } from '@testcontainers/postgresql'
import { beforeAll, afterAll } from 'vitest'

let container: StartedPostgreSqlContainer

beforeAll(async () => {
  // Un PostgreSQL vero in un container: i test verificano
  // anche i vincoli, le transazioni e le query reali,
  // che un mock non può riprodurre
  container = await new PostgreSqlContainer('postgres:17-alpine').start()

  process.env['DATABASE_URL'] = container.getConnectionUri()
  await eseguiMigrazioni()
}, 60_000)

afterAll(async () => {
  await container.stop()
})
```

```
Cosa testare, e a quale livello:

  UNITÀ        la logica pura: calcoli, validazioni,
               trasformazioni. Nessun I/O, millisecondi.

  INTEGRAZIONE le rotte con Supertest, il database con
               Testcontainers. Verifica che i pezzi
               si parlino.

  E2E          il sistema completo, dal client al database.
               Pochi, sui percorsi critici.

Cosa NON testare:
  · che un mock restituisca ciò che gli hai detto
  · i dettagli implementativi
  · il framework

Da testare per primo, sempre:
  1. la logica su denaro, date e permessi
  2. i casi limite: vuoto, zero, negativo, molto grande
  3. gli errori: cosa succede quando il database cade a metà
  4. le regressioni: ogni bug corretto diventa un test
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
NODE.JS — Mappa dei concetti

IL RUNTIME
├── V8 + libuv + le API di Node
├── UN thread per JavaScript, un thread pool (4) per fs,
│     dns.lookup, crypto e zlib
├── La rete NON usa il pool: epoll/kqueue, asincrona nel kernel
└── Adatto quando il server ASPETTA, non quando CALCOLA

EVENT LOOP — sei fasi
├── timers → pending → idle/prepare → POLL → check → close
├── Fra ogni fase: nextTick (priorità massima), poi le microtask
├── Al livello superiore, timer contro immediate è CASUALE
├── Dentro un callback di I/O, immediate viene SEMPRE prima
└── monitorEventLoopDelay è LA metrica di salute del processo

MODULI
├── "type": "module" — ESM è il default per i progetti nuovi
├── Con "module": "NodeNext" gli import vogliono l'estensione .js
├── import.meta.dirname / .filename (Node 20.11+)
├── Type stripping: Node esegue i .ts senza compilarli
│     ma NON verifica i tipi: serve tsc --noEmit
└── createRequire e import attributes per CJS e JSON

MODULI CORE
├── node:path        mai concatenare percorsi; attenzione alla traversal
├── node:fs/promises sempre la versione a Promise
│     └── existsSync + uso = TOCTOU: provare e gestire l'errore
│     └── scrittura atomica: file temporaneo + rename
├── node:crypto      randomUUID, HMAC, timingSafeEqual
│     └── le password con scrypt o argon2, MAI con SHA
└── fetch, WebSocket, AbortController sono GLOBALI

IL SERVER
├── Express 5: le Promise rifiutate arrivano al gestore d'errore
│     (in Express 4 servivano i wrapper)
├── L'ORDINE dei middleware è tutto
├── Il gestore d'errore ha QUATTRO parametri e va per ULTIMO
├── Fastify: schemi JSON compilati, serializzazione controllata
│     └── i campi non dichiarati NON escono dalla risposta
└── Limite sul corpo, sempre

STREAM
├── pipeline(), MAI .pipe(): propaga errori e pulisce
├── Backpressure: il consumatore detta il ritmo
├── Transform con residuo per le righe a cavallo dei pezzi
├── Scrittura a LOTTI, non riga per riga
└── Readable.toWeb / fromWeb per l'interoperabilità

PRODUZIONE
├── Configurazione VALIDATA all'avvio: fallire subito
├── Logging strutturato (pino) con REDAZIONE dei segreti
├── AsyncLocalStorage per il contesto senza inoltrarlo
├── Gerarchia di errori con statoHttp e messaggioPubblico
├── unhandledRejection e uncaughtException → registra e TERMINA
├── Spegnimento pulito: close, closeIdleConnections, timeout
├── liveness ≠ readiness: il database giù non causa riavvii
├── Cluster, o un processo per container
└── Docker multi-stage, utente non privilegiato, --init

WORKER THREADS
├── Per la CPU oltre i 50-100 ms
├── Un POOL, non un worker per richiesta (~30-50 ms di avvio)
└── Il passaggio COPIA: trasferire ArrayBuffer, o leggere nel worker

SICUREZZA
├── Validare ogni ingresso al confine (Zod)
├── helmet, CORS con lista (mai il riflesso), limite di frequenza
├── permission model: --allow-fs-read / write
└── Supply chain: enable-pre-post-scripts=false, audit, SBOM

DIAGNOSTICA
├── --cpu-prof, writeHeapSnapshot, inspector a comando
├── monitorEventLoopDelay, process.memoryUsage
└── OpenTelemetry con auto-instrumentation
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai spiegare per quali carichi Node è adatto e per quali no
- [ ] Sai cosa usa il thread pool e cosa no
- [ ] Configuri un progetto ESM con TypeScript e sai perché gli import vogliono `.js`
- [ ] Sai cosa il type stripping fa e cosa non fa
- [ ] Usi `import.meta.dirname` e sai come risolvere un percorso relativo al modulo
- [ ] Sai perché `existsSync` seguito da un'operazione è una vulnerabilità
- [ ] Scrivi un file in modo atomico
- [ ] Sai perché le password non vanno hashate con SHA
- [ ] Sai perché il confronto delle firme deve essere a tempo costante
- [ ] Conosci l'ordine dei middleware Express e dove va il gestore d'errore
- [ ] Validi la configurazione all'avvio con un messaggio utile

**Parte B — Comprensione**

- [ ] Sai elencare le sei fasi dell'event loop di Node
- [ ] Sai perché al livello superiore timer e immediate hanno ordine casuale
- [ ] Sai perché `process.nextTick` ricorsivo blocca il processo
- [ ] Sai spezzare un calcolo lungo cedendo il controllo al loop
- [ ] Costruisci una gerarchia di errori con stato HTTP e messaggio pubblico
- [ ] Sai perché dopo `uncaughtException` si termina invece di proseguire
- [ ] Sai perché `pipeline` è preferibile a `.pipe()`
- [ ] Sai cos'è la backpressure e cosa succede senza
- [ ] Gestisci il residuo fra i pezzi in un Transform
- [ ] Sai quando Fastify conviene e quando no
- [ ] Sai perché la serializzazione con schema è una difesa
- [ ] Configuri la redazione dei campi sensibili nei log
- [ ] Usi `AsyncLocalStorage` per il contesto della richiesta
- [ ] Sai perché serve un pool di worker invece di crearne uno per richiesta
- [ ] Implementi lo spegnimento pulito con timeout
- [ ] Distingui liveness e readiness e sai perché confonderle causa riavvii
- [ ] Sai perché il riflesso dell'origine in CORS è una vulnerabilità

**Parte C — Pratica**

- [ ] Hai previsto correttamente l'ordine dell'event loop dell'esercizio 1
- [ ] Hai importato un file enorme a memoria costante
- [ ] Hai scritto il middleware di autenticazione con confronto a tempo costante
- [ ] Hai verificato che i log non contengano segreti
- [ ] Hai verificato che lo spegnimento pulito completi le richieste in corso

**Parte D — Esperto**

- [ ] Sai profilare la CPU in produzione senza riavviare
- [ ] Sai trovare un memory leak con due heap snapshot
- [ ] Sai a cosa serve `--trace-warnings`
- [ ] Conosci il permission model e cosa protegge davvero
- [ ] Sai perché gli script `postinstall` sono il vettore principale
- [ ] Generi un SBOM e sai a cosa serve
- [ ] Testi le rotte con Supertest e verifichi che i 500 non espongano dettagli
- [ ] Usi Testcontainers per un database vero nei test

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Calcolo pesante sul thread principale | Blocca tutte le richieste per la sua durata | Spezzare, o un worker thread |
| `process.nextTick` ricorsivo | La coda non si svuota: il processo smette di rispondere | `setImmediate` |
| `readFile` su file grandi | Esaurisce la memoria | Stream con `pipeline` |
| `.pipe()` invece di `pipeline()` | Non propaga gli errori, lascia gli stream aperti | `pipeline` da `node:stream/promises` |
| Una INSERT per riga in un import | Milioni di round-trip al database | Scrittura a lotti |
| `existsSync` seguito dall'uso | Finestra TOCTOU fra verifica e uso | Provare e gestire `ENOENT` |
| Concatenare percorsi con `+` | Si rompe su Windows e con i separatori doppi | `path.join`, e verificare la traversal |
| Password con SHA o MD5 | Troppo veloci: si forzano in ore | `scrypt` o `argon2` |
| `===` per confrontare firme | Attacco a tempo: la firma si ricostruisce | `crypto.timingSafeEqual` |
| Gestore d'errore prima delle rotte | Express lo salta: non cattura nulla | Per ultimo, con quattro parametri |
| Nessun limite sul corpo | Una richiesta enorme esaurisce la memoria | `express.json({ limit: '1mb' })` |
| Configurazione non validata | Il server parte e fallisce alla prima richiesta | Validare con Zod e `process.exit(1)` |
| Segreti nei log | Un incidente di sicurezza a ogni richiesta | `redact` in pino |
| Messaggio interno in una risposta 500 | Espone lo stack, i nomi degli host, le query | Messaggio generico; il dettaglio nei log |
| Proseguire dopo `uncaughtException` | Lo stato del processo è inaffidabile | Registrare e terminare |
| Nessuno spegnimento pulito | Ogni deploy interrompe le richieste in corso | `SIGTERM` → `server.close()` → timeout |
| Liveness che verifica il database | Il database giù causa riavvii inutili del processo | Liveness solo sul processo, readiness sulle dipendenze |
| CORS con riflesso dell'origine | Qualunque sito può leggere le risposte autenticate | Lista di origini ammesse |
| Limite di frequenza in memoria con più processi | Ogni processo conta per conto suo | Archivio condiviso (Redis) |
| Un worker per richiesta | ~30-50 ms di avvio annullano il beneficio | Un pool |
| `postinstall` abilitato | Vettore principale degli attacchi alla supply chain | `enable-pre-post-scripts=false` |
| Container che gira come root | Un'escalation dà root sull'host | `USER node` |
| Container senza `--init` | `SIGTERM` non arriva a Node: nessuno spegnimento pulito | `docker run --init`, o `dumb-init` |

---

## Troubleshooting rapido

**`ERR_MODULE_NOT_FOUND` su un import relativo**
- Causa: manca l'estensione `.js` con `"module": "NodeNext"`
- Fix: `import { x } from './modulo.js'`, anche se il file è `.ts`

**`ERR_REQUIRE_ESM`**
- Causa: `require()` di un modulo che dichiara `"type": "module"`
- Fix: `await import()`, oppure convertire il chiamante a ESM

**`__dirname is not defined`**
- Causa: non esiste in ESM
- Fix: `import.meta.dirname`

**Il server non risponde più, senza errori**
- Causa: qualcosa blocca l'event loop — un ciclo lungo, una regex catastrofica, `nextTick` ricorsivo
- Fix: `monitorEventLoopDelay` per confermarlo; `--cpu-prof` per trovare la funzione

**`EADDRINUSE`**
- Causa: la porta è occupata da un processo precedente
- Fix: `Get-NetTCPConnection -LocalPort 3000 | Select-Object OwningProcess`, poi `Stop-Process`

**`MaxListenersExceededWarning`**
- Causa: listener aggiunti in un ciclo e mai rimossi
- Fix: `--trace-warnings` per l'origine; rimuovere i listener, o `AbortController`

**La memoria cresce e non scende**
- Causa: memory leak — closure che trattengono richieste, cache senza limite, listener accumulati
- Fix: due heap snapshot a confronto in Chrome DevTools

**`JavaScript heap out of memory`**
- Causa: un file letto interamente in memoria, o un leak
- Fix: stream invece di `readFile`; `--max-old-space-size` solo come tampone

**Gli errori asincroni non arrivano al gestore (Express 4)**
- Causa: le Promise rifiutate non vengono catturate
- Fix: aggiornare a Express 5, o avvolgere gli handler

**Il container non si ferma con `docker stop`**
- Causa: `SIGTERM` non arriva a Node — manca l'init, o l'entrypoint è una shell
- Fix: `docker run --init`, oppure `ENTRYPOINT ["dumb-init", "--"]`

**`ERR_ACCESS_DENIED`**
- Causa: il permission model blocca l'operazione
- Fix: aggiungere `--allow-fs-read` o `--allow-fs-write` per quel percorso

**Il limite di frequenza non funziona dietro un proxy**
- Causa: `req.ip` è l'indirizzo del proxy, uguale per tutti
- Fix: `app.set('trust proxy', 1)`, e verificare che il proxy imposti `X-Forwarded-For`

**I log non compaiono in produzione**
- Causa: `pino-pretty` configurato anche in produzione, o il livello è troppo alto
- Fix: transport solo in sviluppo; verificare `LOG_LEVEL`

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_11_api_design.md` | REST, paginazione, versionamento, idempotenza sulle rotte scritte qui |
| `tutorial_12_database_web.md` | Prisma e Drizzle, pool di connessioni, migrazioni, problema N+1 |
| `tutorial_13_autenticazione_autorizzazione.md` | JWT, refresh token, sessioni e cookie in profondità |
| `tutorial_14_sicurezza_web.md` | OWASP, CSP, injection e supply chain in modo sistematico |
| `tutorial_16_build_tools_deploy.md` | Docker, CI/CD e le piattaforme di hosting |
| `tutorial_19_troubleshooting.md` | Debug, profiling e osservabilità in produzione |
| `tutorial_22_rate_limiting_edge.md` | Algoritmi di limitazione e difesa dal traffico anomalo |

---

## Risorse di riferimento

**Documentazione:**
- [Node.js API](https://nodejs.org/api/) — il riferimento; la versione va scelta in alto a sinistra
- [Node.js — Previous Releases](https://nodejs.org/en/about/previous-releases) — calendario LTS e fine supporto
- [Express 5](https://expressjs.com/en/5x/api.html) — le novità rispetto alla 4
- [Fastify](https://fastify.dev/docs/latest/) — plugin, schemi, hook
- [pino](https://getpino.io/) — logging strutturato

**Approfondimenti:**
- [Node.js — Event Loop, Timers, and process.nextTick](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick) — la spiegazione ufficiale delle sei fasi
- [Node.js — Backpressuring in Streams](https://nodejs.org/en/learn/modules/backpressuring-in-streams)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices) — raccolta molto ampia, con le motivazioni
- [OWASP — NodeJS Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html)

**Strumenti:**
- [Clinic.js](https://clinicjs.org/) — diagnostica: doctor, flame, bubbleprof
- [autocannon](https://github.com/mcollina/autocannon) — test di carico da riga di comando
- [Testcontainers](https://node.testcontainers.org/) — dipendenze reali nei test
- [OpenTelemetry per Node](https://opentelemetry.io/docs/languages/js/) — tracciamento distribuito

---

> **Fine del Tutorial 10 — Node.js**
>
> Prossimo tutorial: `tutorial_11_api_design.md`

