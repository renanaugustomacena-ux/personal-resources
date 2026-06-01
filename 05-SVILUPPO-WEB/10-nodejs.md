---
corso: "Sviluppo Web"
fase: "4 — Backend"
modulo: "10"
titolo: "Node.js"
versione: "Node.js 22 LTS"
livello: "Intermedio"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "05 — JavaScript Avanzato"
obiettivi:
  - "Comprendere l'architettura event-driven e il runtime Node.js"
  - "Costruire server HTTP con Express e Fastify"
  - "Gestire file system, stream e child process"
  - "Implementare middleware, routing e error handling"
  - "Utilizzare npm/pnpm per gestione pacchetti e workspaces"
  - "Deployare applicazioni Node.js con Docker e PM2"
tag: [Node.js, Express, Fastify, npm, event-driven, stream, middleware]
---

# Node.js — Guida Completa

> **Modulo 10** · **Aggiornamento:** 2026-05-24 · **Versione:** Node.js 22 LTS

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [JavaScript Avanzato](05-javascript-avanzato.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere l'architettura event-driven e il runtime Node.js
> 2. Costruire server HTTP con Express e Fastify
> 3. Gestire file system, stream e child process
> 4. Implementare middleware, routing e error handling
> 5. Utilizzare npm/pnpm per gestione pacchetti e workspaces
> 6. Deployare applicazioni Node.js con Docker e PM2
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **Node 22 LTS: built-in test runner, fetch, watcher.**
2. **`node --watch` no piu nodemon dep.**
3. **Worker threads per CPU-bound; cluster module per scaling.**
4. **Bun + Deno alternative valide ma ecosystem npm-compatible.**


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti](#fondamenti)
3. [Express.js](#expressjs)
4. [Fastify](#fastify)
5. [API Development](#api-development)
6. [Database Integration](#database-integration)
7. [Testing](#testing)
8. [Security](#security)
9. [Deployment](#deployment)
10. [Best Practices](#best-practices)

---

## Panoramica

### Cos'e Node.js

Node.js e un runtime JavaScript costruito sul motore V8 di Google Chrome. A differenza del JavaScript tradizionale che viene eseguito esclusivamente nel browser, Node.js permette di eseguire codice JavaScript lato server, aprendo le porte allo sviluppo backend, agli strumenti da riga di comando, alle applicazioni desktop e molto altro.

Il cuore di Node.js e il motore V8, lo stesso engine che alimenta Google Chrome. V8 compila il codice JavaScript direttamente in codice macchina nativo, garantendo prestazioni eccellenti. Questo motore gestisce l'allocazione della memoria, la garbage collection e l'ottimizzazione runtime del codice.

L'architettura di Node.js si basa su un modello **event-driven** con **I/O non bloccante**. Questo significa che Node.js utilizza un singolo thread principale (l'event loop) che gestisce tutte le richieste in modo asincrono. Quando un'operazione di I/O viene avviata (lettura file, query al database, richiesta di rete), Node.js non attende il completamento ma registra un callback e continua a processare altre richieste. Quando l'operazione si completa, il callback viene inserito nella coda degli eventi e processato dall'event loop.

```
   ┌───────────────────────────┐
┌─>│         Timers             │  (setTimeout, setInterval)
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     Pending Callbacks      │  (I/O callbacks differiti)
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │       Idle, Prepare        │  (uso interno)
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │          Poll              │  (recupera nuovi eventi I/O)
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │          Check             │  (setImmediate)
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │      Close Callbacks       │  (socket.on('close'))
│  └─────────────┬─────────────┘
│                 │
└─────────────────┘
```

### Node.js vs JavaScript nel Browser

| Caratteristica | Browser | Node.js |
|---|---|---|
| Motore | V8, SpiderMonkey, JavaScriptCore | V8 |
| DOM | Disponibile | Non disponibile |
| File System | Non accessibile | Pieno accesso |
| Moduli nativi | ESM | CommonJS + ESM |
| Oggetti globali | window, document | global, process, Buffer |
| Rete | fetch, XMLHttpRequest | http, https, net, undici |
| Thread | Web Workers | Worker Threads, child_process |

### Casi d'Uso Principali

Node.js eccelle in diversi scenari. Le **API RESTful e GraphQL** rappresentano il caso d'uso piu comune, grazie alla capacita di gestire migliaia di connessioni concorrenti con un overhead minimo. Le **applicazioni real-time** come chat, giochi multiplayer e dashboard live sfruttano WebSocket e Socket.IO nativamente. I **microservizi** beneficiano della leggerezza di Node.js e del rapido avvio. Gli **strumenti CLI** come webpack, eslint e prettier sono costruiti su Node.js. Il **server-side rendering** (SSR) con framework come Next.js e Nuxt.js utilizza Node.js per renderizzare le pagine lato server. Infine, lo **streaming di dati** e ideale grazie all'architettura basata su stream di Node.js.

---

## Fondamenti

### Runtime

#### Node.js REPL

Il REPL (Read-Eval-Print Loop) e un ambiente interattivo integrato che permette di eseguire codice JavaScript riga per riga. Si avvia digitando `node` nel terminale senza argomenti.

```bash
$ node
> const saluto = "Ciao dal REPL"
> console.log(saluto)
Ciao dal REPL
> .help    # mostra i comandi disponibili
> .exit    # esce dal REPL
```

Per eseguire un file JavaScript si utilizza `node nomefile.js`. Con il flag `--watch` (da Node.js 18+) il file viene rieseguito automaticamente ad ogni modifica: `node --watch server.js`.

#### Moduli

Node.js supporta due sistemi di moduli: **CommonJS** e **ESM** (ECMAScript Modules).

**CommonJS** e il sistema storico di Node.js. Usa `require()` per importare e `module.exports` per esportare.

```javascript
// utils.js — esportazione CommonJS
const formattaData = (data) => {
  return data.toISOString().split('T')[0];
};

const calcolaIVA = (prezzo, aliquota = 0.22) => {
  return prezzo * (1 + aliquota);
};

module.exports = { formattaData, calcolaIVA };

// app.js — importazione CommonJS
const { formattaData, calcolaIVA } = require('./utils');
console.log(formattaData(new Date()));
console.log(calcolaIVA(100)); // 122
```

**ESM** e il sistema moderno, abilitato tramite l'estensione `.mjs` oppure impostando `"type": "module"` nel `package.json`.

```javascript
// utils.mjs — esportazione ESM
export const formattaData = (data) => {
  return data.toISOString().split('T')[0];
};

export default class Logger {
  log(messaggio) {
    console.log(`[${new Date().toISOString()}] ${messaggio}`);
  }
}

// app.mjs — importazione ESM
import Logger, { formattaData } from './utils.mjs';
const logger = new Logger();
logger.log(formattaData(new Date()));
```

#### Oggetti Globali

Node.js mette a disposizione diversi oggetti globali accessibili ovunque senza bisogno di importazione.

```javascript
// process — informazioni e controllo del processo corrente
console.log(process.pid);        // ID del processo
console.log(process.platform);   // 'linux', 'darwin', 'win32'
console.log(process.cwd());      // directory di lavoro corrente
console.log(process.memoryUsage()); // utilizzo memoria

// __dirname e __filename (solo CommonJS)
console.log(__dirname);   // percorso assoluto della directory del file
console.log(__filename);  // percorso assoluto del file

// In ESM si usa import.meta
// import.meta.url         → 'file:///percorso/del/file.mjs'
// import.meta.dirname     → percorso della directory (Node 21+)

// Buffer — gestione dati binari
const buf = Buffer.from('Ciao mondo', 'utf-8');
console.log(buf.toString('hex'));
console.log(buf.toString('base64'));
console.log(buf.length); // dimensione in byte

// console — output formattato
console.log('Messaggio informativo');
console.error('Errore critico');
console.warn('Attenzione');
console.table([{ nome: 'Mario', eta: 30 }, { nome: 'Luigi', eta: 28 }]);
console.time('operazione');
// ... codice ...
console.timeEnd('operazione'); // operazione: 12.345ms

// Timer
setTimeout(() => console.log('Dopo 1 secondo'), 1000);
setInterval(() => console.log('Ogni 2 secondi'), 2000);
setImmediate(() => console.log('Alla prossima iterazione dell\'event loop'));
process.nextTick(() => console.log('Prima della prossima fase dell\'event loop'));
```

#### L'Oggetto process

L'oggetto `process` e fondamentale per interagire con il sistema operativo e l'ambiente di esecuzione.

```javascript
// Variabili d'ambiente
console.log(process.env.NODE_ENV);  // 'development', 'production'
console.log(process.env.PORT);      // porta configurata
console.log(process.env.HOME);      // directory home dell'utente

// Argomenti da riga di comando
// node app.js --porta 3000 --debug
console.log(process.argv);
// ['/usr/bin/node', '/percorso/app.js', '--porta', '3000', '--debug']

// Uscita dal processo
process.exit(0);   // uscita con successo
process.exit(1);   // uscita con errore

// Gestione segnali
process.on('SIGTERM', () => {
  console.log('Segnale SIGTERM ricevuto. Chiusura graceful...');
  server.close(() => process.exit(0));
});

process.on('uncaughtException', (errore) => {
  console.error('Eccezione non gestita:', errore);
  process.exit(1);
});

process.on('unhandledRejection', (ragione, promise) => {
  console.error('Promise non gestita:', ragione);
});
```

### npm / pnpm

#### package.json

Il file `package.json` e il cuore di ogni progetto Node.js. Contiene metadati, dipendenze e script di automazione.

```json
{
  "name": "mia-applicazione",
  "version": "1.0.0",
  "description": "Applicazione di esempio Node.js",
  "main": "src/index.js",
  "type": "module",
  "scripts": {
    "start": "node src/index.js",
    "dev": "node --watch src/index.js",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "lint": "eslint src/",
    "build": "tsc",
    "db:migrate": "prisma migrate dev",
    "db:seed": "node prisma/seed.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "prisma": "^5.10.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "vitest": "^1.3.0",
    "eslint": "^8.56.0",
    "typescript": "^5.3.0",
    "@types/express": "^4.17.21"
  },
  "engines": {
    "node": ">=20.0.0",
    "npm": ">=10.0.0"
  }
}
```

#### Comandi npm Essenziali

```bash
# Inizializzazione progetto
npm init              # wizard interattivo
npm init -y           # con valori predefiniti

# Installazione dipendenze
npm install express           # aggiunge a dependencies
npm install -D vitest         # aggiunge a devDependencies
npm install -g nodemon        # installazione globale
npm install                   # installa tutto da package.json

# Aggiornamento e rimozione
npm update express            # aggiorna un pacchetto
npm uninstall express         # rimuove un pacchetto
npm outdated                  # mostra pacchetti obsoleti

# Esecuzione script e pacchetti
npm run dev                   # esegue script definito in package.json
npm test                      # scorciatoia per npm run test
npm start                     # scorciatoia per npm run start
npx create-express-api        # esegue pacchetto senza installare

# Informazioni e audit
npm list --depth=0            # dipendenze di primo livello
npm audit                     # controllo vulnerabilita
npm audit fix                 # corregge vulnerabilita automaticamente
```

#### package-lock.json

Il file `package-lock.json` viene generato automaticamente e blocca le versioni esatte di tutte le dipendenze, incluse quelle transitive. Questo garantisce che ogni installazione produca lo stesso albero di dipendenze. Va sempre committato nel repository. Per installazioni deterministiche in CI/CD si usa `npm ci` invece di `npm install`.

#### pnpm

pnpm e un gestore di pacchetti alternativo che offre vantaggi significativi rispetto a npm.

```bash
# Installazione di pnpm
npm install -g pnpm

# Comandi equivalenti
pnpm install              # installa dipendenze
pnpm add express          # aggiunge dipendenza
pnpm add -D vitest        # aggiunge dipendenza di sviluppo
pnpm remove express       # rimuove dipendenza
pnpm run dev              # esegue script
pnpm dlx create-next-app  # equivalente di npx
```

I vantaggi principali di pnpm sono tre. Il **risparmio di spazio su disco**: pnpm utilizza un content-addressable store globale, condividendo le dipendenze tra progetti. Se dieci progetti usano la stessa versione di express, il pacchetto viene scaricato e memorizzato una sola volta. La **velocita**: grazie allo store condiviso e alla struttura ottimizzata, le installazioni sono notevolmente piu rapide. La **modalita strict**: pnpm crea una struttura `node_modules` non piatta, impedendo l'accesso a dipendenze non dichiarate esplicitamente nel `package.json`. Questo previene il "phantom dependencies" problem.

#### Workspaces per Monorepo

I workspace permettono di gestire piu pacchetti in un singolo repository.

```json
// package.json nella root del monorepo (pnpm)
{
  "name": "mio-monorepo",
  "private": true
}
```

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

```bash
# Struttura tipica monorepo
mio-monorepo/
├── pnpm-workspace.yaml
├── package.json
├── packages/
│   ├── ui/
│   │   └── package.json
│   └── utils/
│       └── package.json
└── apps/
    ├── web/
    │   └── package.json
    └── api/
        └── package.json

# Comandi workspace
pnpm --filter api add express     # installa in un workspace specifico
pnpm --filter ./apps/* run build  # esegue build in tutti gli apps
pnpm -r run test                  # esegue test in tutti i workspace
```

#### Configurazione .npmrc

Il file `.npmrc` configura il comportamento di npm e pnpm a livello di progetto.

```ini
# .npmrc
registry=https://registry.npmjs.org/
save-exact=true
engine-strict=true
auto-install-peers=true

# Per pnpm
shamefully-hoist=false
strict-peer-dependencies=true

# Registry privato per pacchetti aziendali
@mia-azienda:registry=https://npm.mia-azienda.it/
```

### File System (fs)

Il modulo `fs` fornisce API per interagire con il file system. Esistono tre stili: callback, sincrono e promise.

#### Lettura e Scrittura File

```javascript
import { readFile, writeFile, appendFile } from 'fs/promises';
import { createReadStream, createWriteStream } from 'fs';

// Lettura file con async/await (metodo consigliato)
async function leggiFile() {
  try {
    const contenuto = await readFile('./dati.json', 'utf-8');
    const dati = JSON.parse(contenuto);
    console.log(dati);
  } catch (errore) {
    if (errore.code === 'ENOENT') {
      console.error('File non trovato');
    } else {
      throw errore;
    }
  }
}

// Scrittura file
async function scriviFile() {
  const dati = { nome: 'Mario', ruolo: 'sviluppatore' };
  await writeFile('./output.json', JSON.stringify(dati, null, 2), 'utf-8');
  console.log('File scritto con successo');
}

// Aggiunta a file esistente
async function aggiungiALog() {
  const riga = `[${new Date().toISOString()}] Evento registrato\n`;
  await appendFile('./app.log', riga, 'utf-8');
}
```

#### Streaming di File

Lo streaming e essenziale per gestire file di grandi dimensioni senza caricarli interamente in memoria.

```javascript
import { createReadStream, createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';
import { createGzip } from 'zlib';

// Copia file con stream
async function copiaFileGrande(sorgente, destinazione) {
  const lettore = createReadStream(sorgente);
  const scrittore = createWriteStream(destinazione);
  await pipeline(lettore, scrittore);
  console.log('Copia completata');
}

// Compressione file con stream pipeline
async function comprimiFile(percorso) {
  await pipeline(
    createReadStream(percorso),
    createGzip(),
    createWriteStream(`${percorso}.gz`)
  );
  console.log('Compressione completata');
}

// Lettura file riga per riga
import { createInterface } from 'readline';

async function leggiRighe(percorso) {
  const flusso = createReadStream(percorso, 'utf-8');
  const rl = createInterface({ input: flusso });

  for await (const riga of rl) {
    console.log('Riga:', riga);
  }
}
```

#### Operazioni su Directory

```javascript
import { readdir, mkdir, rm, stat } from 'fs/promises';

// Elenco contenuto directory
async function elencaDirectory(percorso) {
  const voci = await readdir(percorso, { withFileTypes: true });
  for (const voce of voci) {
    const tipo = voce.isDirectory() ? 'DIR' : 'FILE';
    console.log(`[${tipo}] ${voce.name}`);
  }
}

// Creazione directory ricorsiva
await mkdir('./percorso/profondo/annidato', { recursive: true });

// Rimozione directory ricorsiva
await rm('./percorso', { recursive: true, force: true });

// Informazioni file
const info = await stat('./file.txt');
console.log('Dimensione:', info.size, 'byte');
console.log('Creato:', info.birthtime);
console.log('Modificato:', info.mtime);
console.log('E una directory:', info.isDirectory());
```

#### Modulo path

Il modulo `path` gestisce i percorsi in modo cross-platform.

```javascript
import path from 'path';

// Composizione percorsi
const percorsoCompleto = path.join('/utenti', 'mario', 'documenti', 'file.txt');
// /utenti/mario/documenti/file.txt

// Percorso assoluto
const assoluto = path.resolve('src', 'utils', 'helper.js');
// /percorso/corrente/src/utils/helper.js

// Estrazione componenti
console.log(path.basename('/percorso/file.txt'));       // 'file.txt'
console.log(path.basename('/percorso/file.txt', '.txt')); // 'file'
console.log(path.dirname('/percorso/file.txt'));        // '/percorso'
console.log(path.extname('/percorso/file.txt'));        // '.txt'
console.log(path.parse('/percorso/file.txt'));
// { root: '/', dir: '/percorso', base: 'file.txt', ext: '.txt', name: 'file' }
```

#### Watch dei File

```javascript
import { watch } from 'fs';

// Monitoraggio nativo (limitato)
watch('./src', { recursive: true }, (tipoEvento, nomeFile) => {
  console.log(`${tipoEvento}: ${nomeFile}`);
});

// Con chokidar (piu affidabile e ricco di funzionalita)
// npm install chokidar
import chokidar from 'chokidar';

const watcher = chokidar.watch('./src', {
  ignored: /node_modules/,
  persistent: true
});

watcher
  .on('add', percorso => console.log(`File aggiunto: ${percorso}`))
  .on('change', percorso => console.log(`File modificato: ${percorso}`))
  .on('unlink', percorso => console.log(`File rimosso: ${percorso}`));
```

### Networking

#### Modulo http/https

```javascript
import http from 'http';

// Creazione server HTTP
const server = http.createServer((req, res) => {
  const { method, url, headers } = req;

  if (method === 'GET' && url === '/api/saluto') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ messaggio: 'Ciao dal server!' }));
  } else if (method === 'POST' && url === '/api/dati') {
    let corpo = '';
    req.on('data', chunk => { corpo += chunk; });
    req.on('end', () => {
      const dati = JSON.parse(corpo);
      res.writeHead(201, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ricevuto: dati }));
    });
  } else {
    res.writeHead(404);
    res.end('Non trovato');
  }
});

server.listen(3000, () => {
  console.log('Server in ascolto sulla porta 3000');
});
```

#### Richieste HTTP con fetch e undici

A partire da Node.js 18, la `fetch` API globale e disponibile nativamente. Per prestazioni superiori si usa la libreria `undici`.

```javascript
// fetch nativa (Node.js 18+)
const risposta = await fetch('https://api.esempio.it/dati', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ chiave: 'valore' })
});
const dati = await risposta.json();

// undici — client HTTP ad alte prestazioni
import { request } from 'undici';

const { statusCode, headers, body } = await request('https://api.esempio.it/dati');
const dati2 = await body.json();
```

#### URL e URLSearchParams

```javascript
const url = new URL('https://esempio.it/ricerca?q=node&pagina=2');
console.log(url.hostname);    // 'esempio.it'
console.log(url.pathname);    // '/ricerca'
console.log(url.searchParams.get('q'));       // 'node'
console.log(url.searchParams.get('pagina')); // '2'

url.searchParams.set('limite', '10');
console.log(url.toString());
// 'https://esempio.it/ricerca?q=node&pagina=2&limite=10'
```

#### Moduli net (TCP) e dgram (UDP)

```javascript
// Server TCP
import net from 'net';

const serverTCP = net.createServer((socket) => {
  socket.write('Benvenuto al server TCP\n');
  socket.on('data', (dati) => {
    console.log('Ricevuto:', dati.toString());
    socket.write(`Echo: ${dati}`);
  });
  socket.on('end', () => console.log('Client disconnesso'));
});

serverTCP.listen(8080, () => console.log('Server TCP sulla porta 8080'));

// Server UDP
import dgram from 'dgram';

const serverUDP = dgram.createSocket('udp4');
serverUDP.on('message', (msg, rinfo) => {
  console.log(`Messaggio da ${rinfo.address}:${rinfo.port} — ${msg}`);
});
serverUDP.bind(41234);
```

---

## Express.js

### Fondamenti

Express.js e il framework web piu diffuso per Node.js. Si basa sul concetto di middleware, funzioni che hanno accesso all'oggetto request, all'oggetto response e alla funzione `next()` nel ciclo richiesta-risposta.

```javascript
import express from 'express';

const app = express();

// Middleware built-in per parsing
app.use(express.json());                         // parsing JSON
app.use(express.urlencoded({ extended: true }));  // parsing form

// Rotta semplice
app.get('/', (req, res) => {
  res.json({ messaggio: 'Benvenuto nell\'API' });
});

app.listen(3000, () => {
  console.log('Server Express sulla porta 3000');
});
```

### Routing

```javascript
import { Router } from 'express';

const router = Router();

// Rotte CRUD per una risorsa "prodotti"
router.get('/prodotti', async (req, res) => {
  // req.query — parametri di query string (?pagina=1&limite=10)
  const { pagina = 1, limite = 10 } = req.query;
  const prodotti = await ProdottoService.trovaTutti({ pagina, limite });
  res.json(prodotti);
});

router.get('/prodotti/:id', async (req, res) => {
  // req.params — parametri di rotta
  const prodotto = await ProdottoService.trovaPerId(req.params.id);
  if (!prodotto) return res.status(404).json({ errore: 'Prodotto non trovato' });
  res.json(prodotto);
});

router.post('/prodotti', async (req, res) => {
  // req.body — corpo della richiesta (richiede middleware di parsing)
  const nuovoProdotto = await ProdottoService.crea(req.body);
  res.status(201).json(nuovoProdotto);
});

router.put('/prodotti/:id', async (req, res) => {
  const aggiornato = await ProdottoService.aggiorna(req.params.id, req.body);
  res.json(aggiornato);
});

router.delete('/prodotti/:id', async (req, res) => {
  await ProdottoService.elimina(req.params.id);
  res.status(204).send();
});

// Request object — proprieta principali
// req.params      — parametri di rotta (/utenti/:id)
// req.query       — parametri query string (?chiave=valore)
// req.body        — corpo della richiesta
// req.headers     — intestazioni HTTP
// req.cookies     — cookie (con cookie-parser)
// req.ip          — indirizzo IP del client
// req.method      — metodo HTTP
// req.path        — percorso dell'URL

// Response object — metodi principali
// res.send()      — invia risposta generica
// res.json()      — invia risposta JSON
// res.status()    — imposta codice di stato
// res.redirect()  — reindirizzamento
// res.render()    — renderizza template
// res.download()  — invia file come allegato
// res.cookie()    — imposta cookie
// res.set()       — imposta intestazioni

export default router;
```

### Middleware

I middleware sono il cuore di Express. Ogni richiesta passa attraverso una catena di middleware prima di raggiungere il gestore della rotta.

```javascript
// Middleware a livello di applicazione
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url} — ${new Date().toISOString()}`);
  next(); // passa al prossimo middleware
});

// Middleware a livello di router
router.use((req, res, next) => {
  // Si applica solo alle rotte di questo router
  next();
});

// Middleware di gestione errori (4 parametri)
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.statusCode || 500).json({
    errore: {
      messaggio: err.message || 'Errore interno del server',
      codice: err.codice
    }
  });
});

// Middleware di terze parti comuni
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import rateLimit from 'express-rate-limit';

app.use(cors({ origin: 'https://miosito.it', credentials: true }));
app.use(helmet());                      // intestazioni di sicurezza
app.use(morgan('combined'));            // logging richieste HTTP
app.use(compression());                // compressione gzip delle risposte

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,           // finestra di 15 minuti
  max: 100,                            // massimo 100 richieste per finestra
  message: 'Troppe richieste, riprova piu tardi'
});
app.use('/api/', limiter);

// Middleware personalizzato — esempio di autenticazione
function autenticazione(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) {
    return res.status(401).json({ errore: 'Token mancante' });
  }
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    req.utente = payload;
    next();
  } catch (errore) {
    res.status(403).json({ errore: 'Token non valido' });
  }
}

app.get('/api/profilo', autenticazione, (req, res) => {
  res.json(req.utente);
});
```

### Template Engine e File Statici

```javascript
// Configurazione EJS come template engine
app.set('view engine', 'ejs');
app.set('views', './views');

app.get('/dashboard', (req, res) => {
  res.render('dashboard', {
    titolo: 'La Mia Dashboard',
    utente: req.utente,
    prodotti: listaProdotti
  });
});

// Servire file statici
app.use(express.static('public'));
app.use('/assets', express.static('risorse'));
```

### Gestione Errori

Una gestione degli errori strutturata e fondamentale per applicazioni robuste.

```javascript
// Classe di errore personalizzata
class AppError extends Error {
  constructor(messaggio, statusCode, codice) {
    super(messaggio);
    this.statusCode = statusCode;
    this.codice = codice;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

class NotFoundError extends AppError {
  constructor(risorsa = 'Risorsa') {
    super(`${risorsa} non trovata`, 404, 'NOT_FOUND');
  }
}

class ValidationError extends AppError {
  constructor(dettagli) {
    super('Errore di validazione', 400, 'VALIDATION_ERROR');
    this.dettagli = dettagli;
  }
}

// Wrapper per gestione async automatica
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Uso con asyncHandler
router.get('/prodotti/:id', asyncHandler(async (req, res) => {
  const prodotto = await ProdottoService.trovaPerId(req.params.id);
  if (!prodotto) throw new NotFoundError('Prodotto');
  res.json(prodotto);
}));

// Gestore centralizzato degli errori
app.use((err, req, res, next) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      stato: 'errore',
      codice: err.codice,
      messaggio: err.message,
      ...(err.dettagli && { dettagli: err.dettagli })
    });
  }
  // Errore non previsto
  console.error('Errore imprevisto:', err);
  res.status(500).json({
    stato: 'errore',
    messaggio: 'Errore interno del server'
  });
});
```

---

## Fastify

Fastify e un framework web focalizzato sulle prestazioni, fino a 2-3 volte piu veloce di Express in alcuni benchmark. Offre validazione degli schema integrata, un potente sistema di plugin e supporto nativo per TypeScript.

```javascript
import Fastify from 'fastify';

const fastify = Fastify({ logger: true });

// Definizione rotta con schema di validazione
fastify.get('/prodotti/:id', {
  schema: {
    params: {
      type: 'object',
      properties: {
        id: { type: 'string', format: 'uuid' }
      },
      required: ['id']
    },
    response: {
      200: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          nome: { type: 'string' },
          prezzo: { type: 'number' }
        }
      }
    }
  },
  handler: async (request, reply) => {
    const prodotto = await trovaProdotto(request.params.id);
    return prodotto; // Fastify serializza automaticamente con lo schema
  }
});

// Plugin — sistema modulare
async function pluginDatabase(fastify, opzioni) {
  const pool = await creaPpool(opzioni.connectionString);
  fastify.decorate('db', pool);       // aggiunge .db all'istanza fastify
}

fastify.register(pluginDatabase, {
  connectionString: process.env.DATABASE_URL
});

// Hooks — ciclo di vita della richiesta
fastify.addHook('onRequest', async (request, reply) => {
  // Eseguito prima di ogni richiesta
  request.tempoInizio = Date.now();
});

fastify.addHook('onResponse', async (request, reply) => {
  const durata = Date.now() - request.tempoInizio;
  fastify.log.info(`${request.method} ${request.url} — ${durata}ms`);
});

// Avvio server
await fastify.listen({ port: 3000, host: '0.0.0.0' });
```

---

## API Development

### Struttura Progetto REST API

Una struttura ben organizzata e essenziale per la manutenibilita del progetto.

```
src/
├── config/
│   ├── database.js           # configurazione database
│   ├── environment.js        # variabili d'ambiente
│   └── logger.js             # configurazione logger
├── middleware/
│   ├── autenticazione.js     # verifica JWT
│   ├── validazione.js        # validazione input
│   ├── gestoreErrori.js      # error handler centralizzato
│   └── rateLimiter.js        # limitazione richieste
├── routes/
│   ├── index.js              # aggregatore rotte
│   ├── utenti.routes.js      # rotte utenti
│   └── prodotti.routes.js    # rotte prodotti
├── controllers/
│   ├── utenti.controller.js  # logica HTTP per utenti
│   └── prodotti.controller.js
├── services/
│   ├── utenti.service.js     # logica di business utenti
│   └── prodotti.service.js
├── models/
│   ├── utente.model.js       # schema/modello utente
│   └── prodotto.model.js
├── utils/
│   ├── AppError.js           # classe errore personalizzata
│   └── helpers.js            # funzioni utilita
├── app.js                    # configurazione Express
└── server.js                 # avvio server
```

### Validazione Input

```javascript
// Con Zod — validazione type-safe
import { z } from 'zod';

const SchemaProdotto = z.object({
  nome: z.string().min(2).max(100),
  descrizione: z.string().max(1000).optional(),
  prezzo: z.number().positive().multipleOf(0.01),
  categoria: z.enum(['elettronica', 'abbigliamento', 'alimentari', 'casa']),
  disponibile: z.boolean().default(true),
  tag: z.array(z.string()).max(10).optional()
});

// Middleware di validazione generico
function validaCorpo(schema) {
  return (req, res, next) => {
    const risultato = schema.safeParse(req.body);
    if (!risultato.success) {
      return res.status(400).json({
        errore: 'Dati non validi',
        dettagli: risultato.error.issues.map(i => ({
          campo: i.path.join('.'),
          messaggio: i.message
        }))
      });
    }
    req.body = risultato.data; // dati validati e tipizzati
    next();
  };
}

router.post('/prodotti', validaCorpo(SchemaProdotto), controller.crea);
```

### Paginazione, Filtri e Ordinamento

```javascript
async function trovaProdotti(req, res) {
  const {
    pagina = 1,
    limite = 20,
    ordina = 'createdAt',
    direzione = 'desc',
    categoria,
    prezzoMin,
    prezzoMax,
    cerca
  } = req.query;

  const filtri = {};
  if (categoria) filtri.categoria = categoria;
  if (prezzoMin || prezzoMax) {
    filtri.prezzo = {};
    if (prezzoMin) filtri.prezzo.$gte = Number(prezzoMin);
    if (prezzoMax) filtri.prezzo.$lte = Number(prezzoMax);
  }
  if (cerca) filtri.$text = { $search: cerca };

  const offset = (Number(pagina) - 1) * Number(limite);
  const [prodotti, totale] = await Promise.all([
    Prodotto.find(filtri)
      .sort({ [ordina]: direzione === 'desc' ? -1 : 1 })
      .skip(offset)
      .limit(Number(limite)),
    Prodotto.countDocuments(filtri)
  ]);

  res.json({
    dati: prodotti,
    meta: {
      totale,
      pagina: Number(pagina),
      limite: Number(limite),
      pagine: Math.ceil(totale / Number(limite))
    }
  });
}
```

### Upload File

```javascript
import multer from 'multer';
import path from 'path';

const storage = multer.diskStorage({
  destination: './uploads/',
  filename: (req, file, cb) => {
    const nomeUnico = `${Date.now()}-${Math.round(Math.random() * 1E9)}`;
    cb(null, `${nomeUnico}${path.extname(file.originalname)}`);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5 MB
  fileFilter: (req, file, cb) => {
    const tipiPermessi = /jpeg|jpg|png|gif|webp/;
    const estensione = tipiPermessi.test(path.extname(file.originalname).toLowerCase());
    const mimetype = tipiPermessi.test(file.mimetype);
    if (estensione && mimetype) {
      cb(null, true);
    } else {
      cb(new Error('Solo immagini JPEG, PNG, GIF e WebP sono permesse'));
    }
  }
});

router.post('/prodotti/:id/immagine', upload.single('immagine'), async (req, res) => {
  const percorsoFile = req.file.path;
  await ProdottoService.aggiornaImmagine(req.params.id, percorsoFile);
  res.json({ messaggio: 'Immagine caricata', percorso: percorsoFile });
});
```

### Autenticazione

#### JWT (JSON Web Token)

```javascript
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;

// Registrazione utente
async function registrazione(req, res) {
  const { email, password, nome } = req.body;

  // Hash della password con bcrypt
  const saltRounds = 12;
  const passwordHash = await bcrypt.hash(password, saltRounds);

  const utente = await UtenteService.crea({
    email,
    password: passwordHash,
    nome
  });

  const { accessToken, refreshToken } = generaTokens(utente);

  res.status(201).json({
    utente: { id: utente.id, email: utente.email, nome: utente.nome },
    accessToken,
    refreshToken
  });
}

// Login
async function login(req, res) {
  const { email, password } = req.body;
  const utente = await UtenteService.trovPerEmail(email);
  if (!utente) {
    return res.status(401).json({ errore: 'Credenziali non valide' });
  }

  const passwordValida = await bcrypt.compare(password, utente.password);
  if (!passwordValida) {
    return res.status(401).json({ errore: 'Credenziali non valide' });
  }

  const { accessToken, refreshToken } = generaTokens(utente);
  res.json({ accessToken, refreshToken });
}

// Generazione coppia di token
function generaTokens(utente) {
  const accessToken = jwt.sign(
    { id: utente.id, email: utente.email, ruolo: utente.ruolo },
    JWT_SECRET,
    { expiresIn: '15m' }
  );
  const refreshToken = jwt.sign(
    { id: utente.id },
    JWT_REFRESH_SECRET,
    { expiresIn: '7d' }
  );
  return { accessToken, refreshToken };
}

// Refresh token pattern
async function rinnovaToken(req, res) {
  const { refreshToken } = req.body;
  try {
    const payload = jwt.verify(refreshToken, JWT_REFRESH_SECRET);
    const utente = await UtenteService.trovaPerId(payload.id);
    if (!utente) throw new Error('Utente non trovato');

    const nuoviTokens = generaTokens(utente);
    res.json(nuoviTokens);
  } catch (errore) {
    res.status(403).json({ errore: 'Refresh token non valido' });
  }
}
```

#### Session-based Authentication

L'autenticazione basata su sessioni utilizza cookie lato server per mantenere lo stato dell'utente. E un approccio tradizionale ancora valido per applicazioni monolitiche e siti web server-rendered.

```javascript
import session from 'express-session';
import RedisStore from 'connect-redis';

app.use(session({
  store: new RedisStore({ client: redis }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production', // solo HTTPS
    httpOnly: true,                                 // non accessibile da JS
    maxAge: 24 * 60 * 60 * 1000,                   // 24 ore
    sameSite: 'strict'                              // protezione CSRF
  }
}));
```

#### Passport.js

Passport.js e un middleware di autenticazione che supporta oltre 500 strategie (local, OAuth, SAML, ecc.).

```javascript
import passport from 'passport';
import { Strategy as LocalStrategy } from 'passport-local';
import { Strategy as JwtStrategy, ExtractJwt } from 'passport-jwt';

// Strategia locale (email + password)
passport.use(new LocalStrategy(
  { usernameField: 'email' },
  async (email, password, done) => {
    const utente = await UtenteService.trovaPerEmail(email);
    if (!utente) return done(null, false, { message: 'Utente non trovato' });
    const valida = await bcrypt.compare(password, utente.password);
    if (!valida) return done(null, false, { message: 'Password errata' });
    return done(null, utente);
  }
));

// Strategia JWT
passport.use(new JwtStrategy(
  {
    jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
    secretOrKey: JWT_SECRET
  },
  async (payload, done) => {
    const utente = await UtenteService.trovaPerId(payload.id);
    return done(null, utente || false);
  }
));
```

### Real-time

#### WebSocket con la libreria ws

```javascript
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (ws, req) => {
  console.log('Nuova connessione WebSocket');

  ws.on('message', (messaggio) => {
    const dati = JSON.parse(messaggio);
    // Broadcast a tutti i client connessi
    wss.clients.forEach((client) => {
      if (client.readyState === 1) { // WebSocket.OPEN
        client.send(JSON.stringify({
          tipo: 'messaggio',
          dati: dati,
          timestamp: Date.now()
        }));
      }
    });
  });

  ws.on('close', () => console.log('Client disconnesso'));
});
```

#### Socket.IO

Socket.IO offre funzionalita avanzate come room, namespace, riconnessione automatica e fallback a long polling.

```javascript
import { Server } from 'socket.io';

const io = new Server(httpServer, {
  cors: { origin: 'https://miosito.it' }
});

// Namespace per la chat
const chat = io.of('/chat');

chat.on('connection', (socket) => {
  console.log('Utente connesso alla chat:', socket.id);

  // Entrare in una stanza
  socket.on('entra-stanza', (stanza) => {
    socket.join(stanza);
    chat.to(stanza).emit('notifica', `Un utente e entrato nella stanza ${stanza}`);
  });

  // Inviare messaggio nella stanza
  socket.on('messaggio', ({ stanza, testo }) => {
    chat.to(stanza).emit('messaggio', {
      autore: socket.id,
      testo,
      timestamp: new Date()
    });
  });

  socket.on('disconnect', () => {
    console.log('Utente disconnesso:', socket.id);
  });
});
```

#### Server-Sent Events (SSE)

SSE e un protocollo unidirezionale (server verso client) ideale per notifiche e aggiornamenti in tempo reale.

```javascript
app.get('/api/eventi', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });

  const inviaEvento = (dati, tipo = 'messaggio') => {
    res.write(`event: ${tipo}\n`);
    res.write(`data: ${JSON.stringify(dati)}\n\n`);
  };

  // Invia heartbeat ogni 30 secondi
  const heartbeat = setInterval(() => {
    res.write(': heartbeat\n\n');
  }, 30000);

  // Esempio: invia aggiornamenti
  const intervallo = setInterval(() => {
    inviaEvento({ valore: Math.random() }, 'aggiornamento');
  }, 5000);

  req.on('close', () => {
    clearInterval(heartbeat);
    clearInterval(intervallo);
  });
});
```

---

## Database Integration

### MongoDB con Mongoose

```javascript
import mongoose from 'mongoose';

// Connessione
await mongoose.connect(process.env.MONGODB_URI, {
  maxPoolSize: 10
});

// Definizione schema e modello
const schemaProdotto = new mongoose.Schema({
  nome: { type: String, required: true, trim: true, index: true },
  descrizione: { type: String, maxlength: 2000 },
  prezzo: { type: Number, required: true, min: 0 },
  categoria: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Categoria',
    required: true
  },
  tag: [String],
  immagini: [{
    url: String,
    alt: String
  }],
  disponibile: { type: Boolean, default: true }
}, {
  timestamps: true,
  toJSON: { virtuals: true }
});

// Indice composto
schemaProdotto.index({ nome: 'text', descrizione: 'text' });

// Metodo di istanza
schemaProdotto.methods.applicaSconto = function(percentuale) {
  this.prezzo = this.prezzo * (1 - percentuale / 100);
  return this.save();
};

// Metodo statico
schemaProdotto.statics.trovaPerCategoria = function(categoriaId) {
  return this.find({ categoria: categoriaId, disponibile: true })
    .populate('categoria', 'nome')
    .sort('-createdAt');
};

const Prodotto = mongoose.model('Prodotto', schemaProdotto);

// Operazioni CRUD
const nuovo = await Prodotto.create({ nome: 'Laptop', prezzo: 999.99, categoria: catId });
const tutti = await Prodotto.find({ disponibile: true }).populate('categoria').limit(20);
const aggiornato = await Prodotto.findByIdAndUpdate(id, { prezzo: 899.99 }, { new: true });
await Prodotto.findByIdAndDelete(id);
```

### PostgreSQL con Prisma

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Utente {
  id        String   @id @default(uuid())
  email     String   @unique
  nome      String
  password  String
  ruolo     Ruolo    @default(UTENTE)
  ordini    Ordine[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Prodotto {
  id           String         @id @default(uuid())
  nome         String
  prezzo       Decimal        @db.Decimal(10, 2)
  descrizione  String?
  righeOrdine  RigaOrdine[]
  createdAt    DateTime       @default(now())
}

model Ordine {
  id        String       @id @default(uuid())
  utente    Utente       @relation(fields: [utenteId], references: [id])
  utenteId  String
  righe     RigaOrdine[]
  totale    Decimal      @db.Decimal(10, 2)
  stato     StatoOrdine  @default(IN_ATTESA)
  createdAt DateTime     @default(now())
}

model RigaOrdine {
  id         String   @id @default(uuid())
  ordine     Ordine   @relation(fields: [ordineId], references: [id])
  ordineId   String
  prodotto   Prodotto @relation(fields: [prodottoId], references: [id])
  prodottoId String
  quantita   Int
  prezzo     Decimal  @db.Decimal(10, 2)
}

enum Ruolo {
  UTENTE
  ADMIN
}

enum StatoOrdine {
  IN_ATTESA
  CONFERMATO
  SPEDITO
  CONSEGNATO
  ANNULLATO
}
```

```javascript
// Utilizzo Prisma Client
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Creazione con relazione
const ordine = await prisma.ordine.create({
  data: {
    utenteId: utente.id,
    totale: 199.99,
    righe: {
      create: [
        { prodottoId: prod1.id, quantita: 2, prezzo: 49.99 },
        { prodottoId: prod2.id, quantita: 1, prezzo: 100.01 }
      ]
    }
  },
  include: {
    righe: { include: { prodotto: true } },
    utente: { select: { nome: true, email: true } }
  }
});

// Transazione
const [utente, ordine] = await prisma.$transaction(async (tx) => {
  const utente = await tx.utente.update({
    where: { id: utenteId },
    data: { credito: { decrement: totale } }
  });
  if (utente.credito < 0) throw new Error('Credito insufficiente');

  const ordine = await tx.ordine.create({
    data: { utenteId, totale, stato: 'CONFERMATO', righe: { create: righe } }
  });
  return [utente, ordine];
});

// Migrazioni
// npx prisma migrate dev --name aggiunta_campo_telefono
// npx prisma migrate deploy   (produzione)
// npx prisma generate          (rigenera client)
```

### Redis con ioredis

```javascript
import Redis from 'ioredis';

const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: 6379,
  password: process.env.REDIS_PASSWORD,
  maxRetriesPerRequest: 3
});

// Caching
async function getProdottoConCache(id) {
  const chiaveCache = `prodotto:${id}`;
  const cached = await redis.get(chiaveCache);
  if (cached) return JSON.parse(cached);

  const prodotto = await ProdottoService.trovaPerId(id);
  if (prodotto) {
    await redis.setex(chiaveCache, 3600, JSON.stringify(prodotto)); // TTL 1 ora
  }
  return prodotto;
}

// Invalidazione cache
async function aggiornaProdotto(id, dati) {
  const prodotto = await ProdottoService.aggiorna(id, dati);
  await redis.del(`prodotto:${id}`);
  return prodotto;
}

// Pub/Sub per comunicazione tra servizi
const subscriber = new Redis();
const publisher = new Redis();

subscriber.subscribe('ordini', (err, count) => {
  console.log(`Iscritto a ${count} canali`);
});

subscriber.on('message', (canale, messaggio) => {
  const evento = JSON.parse(messaggio);
  console.log(`Evento da ${canale}:`, evento);
});

// Pubblica evento
await publisher.publish('ordini', JSON.stringify({
  tipo: 'ORDINE_CREATO',
  dati: { ordineId: '123', totale: 99.99 }
}));

// Gestione sessioni
async function creaSessione(utenteId, datiSessione) {
  const sessioneId = crypto.randomUUID();
  await redis.setex(
    `sessione:${sessioneId}`,
    86400,
    JSON.stringify({ utenteId, ...datiSessione })
  );
  return sessioneId;
}
```

---

## Testing

### Unit Test con Vitest

```javascript
// prodotto.service.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProdottoService } from './prodotto.service.js';

// Mock del repository
vi.mock('./prodotto.repository.js', () => ({
  ProdottoRepository: {
    trova: vi.fn(),
    crea: vi.fn(),
    aggiorna: vi.fn(),
    elimina: vi.fn()
  }
}));

import { ProdottoRepository } from './prodotto.repository.js';

describe('ProdottoService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('calcolaPrezzFinale', () => {
    it('dovrebbe applicare lo sconto percentuale', () => {
      const risultato = ProdottoService.calcolaPrezzoFinale(100, 20);
      expect(risultato).toBe(80);
    });

    it('dovrebbe rifiutare sconti negativi', () => {
      expect(() => {
        ProdottoService.calcolaPrezzoFinale(100, -10);
      }).toThrow('Lo sconto non puo essere negativo');
    });

    it('dovrebbe restituire il prezzo originale senza sconto', () => {
      const risultato = ProdottoService.calcolaPrezzoFinale(100);
      expect(risultato).toBe(100);
    });
  });

  describe('trovaProdotto', () => {
    it('dovrebbe restituire il prodotto se esiste', async () => {
      const mockProdotto = { id: '1', nome: 'Laptop', prezzo: 999 };
      ProdottoRepository.trova.mockResolvedValue(mockProdotto);

      const risultato = await ProdottoService.trova('1');
      expect(risultato).toEqual(mockProdotto);
      expect(ProdottoRepository.trova).toHaveBeenCalledWith('1');
    });

    it('dovrebbe lanciare errore se il prodotto non esiste', async () => {
      ProdottoRepository.trova.mockResolvedValue(null);

      await expect(ProdottoService.trova('999'))
        .rejects.toThrow('Prodotto non trovato');
    });
  });
});
```

### Test API con Supertest

```javascript
// app.test.js
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { app } from './app.js';

describe('API Prodotti', () => {
  let tokenAuth;

  beforeAll(async () => {
    // Setup: login per ottenere token
    const risposta = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@esempio.it', password: 'password123' });
    tokenAuth = risposta.body.accessToken;
  });

  describe('GET /api/prodotti', () => {
    it('dovrebbe restituire la lista dei prodotti con paginazione', async () => {
      const risposta = await request(app)
        .get('/api/prodotti?pagina=1&limite=10')
        .expect(200);

      expect(risposta.body).toHaveProperty('dati');
      expect(risposta.body).toHaveProperty('meta');
      expect(risposta.body.dati).toBeInstanceOf(Array);
      expect(risposta.body.meta.pagina).toBe(1);
    });
  });

  describe('POST /api/prodotti', () => {
    it('dovrebbe creare un nuovo prodotto con dati validi', async () => {
      const nuovoProdotto = {
        nome: 'Tastiera Meccanica',
        prezzo: 89.99,
        categoria: 'elettronica'
      };

      const risposta = await request(app)
        .post('/api/prodotti')
        .set('Authorization', `Bearer ${tokenAuth}`)
        .send(nuovoProdotto)
        .expect(201);

      expect(risposta.body.nome).toBe(nuovoProdotto.nome);
      expect(risposta.body).toHaveProperty('id');
    });

    it('dovrebbe rifiutare dati non validi con 400', async () => {
      const datiNonValidi = { nome: '', prezzo: -10 };

      const risposta = await request(app)
        .post('/api/prodotti')
        .set('Authorization', `Bearer ${tokenAuth}`)
        .send(datiNonValidi)
        .expect(400);

      expect(risposta.body).toHaveProperty('errore');
    });

    it('dovrebbe rifiutare richieste senza autenticazione con 401', async () => {
      await request(app)
        .post('/api/prodotti')
        .send({ nome: 'Test', prezzo: 10 })
        .expect(401);
    });
  });
});
```

### Mocking

Il mocking e essenziale per isolare le unita sotto test dalle loro dipendenze esterne.

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock di un intero modulo
vi.mock('./servizi/email.service.js', () => ({
  EmailService: {
    inviaEmail: vi.fn().mockResolvedValue({ inviato: true }),
    inviaEmailBenvenuto: vi.fn().mockResolvedValue({ inviato: true })
  }
}));

// Mock di fetch per chiamate API esterne
vi.stubGlobal('fetch', vi.fn());

describe('ServizioNotifiche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('dovrebbe inviare notifica via email e webhook', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ successo: true })
    });

    await ServizioNotifiche.notifica('utente123', 'Ordine confermato');

    expect(EmailService.inviaEmail).toHaveBeenCalledWith(
      expect.objectContaining({ destinatario: 'utente123' })
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/webhook'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});
```

### Fixture e Factory

```javascript
// test/factories/prodotto.factory.js
import { faker } from '@faker-js/faker/locale/it';

export function creaProdottoFittizio(override = {}) {
  return {
    nome: faker.commerce.productName(),
    descrizione: faker.commerce.productDescription(),
    prezzo: parseFloat(faker.commerce.price({ min: 5, max: 500 })),
    categoria: faker.helpers.arrayElement(['elettronica', 'abbigliamento', 'casa']),
    disponibile: true,
    tag: faker.helpers.arrayElements(['nuovo', 'offerta', 'popolare', 'esclusivo'], 2),
    ...override
  };
}

export function creaUtenteFittizio(override = {}) {
  return {
    nome: faker.person.fullName(),
    email: faker.internet.email(),
    password: 'Password123!',
    ruolo: 'UTENTE',
    ...override
  };
}
```

---

## Security

### OWASP Top 10 per Node.js

La sicurezza e un aspetto critico di ogni applicazione. Ecco le contromisure principali per le vulnerabilita piu comuni.

```javascript
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import cors from 'cors';
import hpp from 'hpp';
import mongoSanitize from 'express-mongo-sanitize';

// 1. Intestazioni di sicurezza con Helmet
app.use(helmet());
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "'unsafe-inline'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", 'data:', 'https:']
  }
}));

// 2. Rate limiting per prevenire attacchi brute-force
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Troppi tentativi di accesso, riprova tra 15 minuti',
  standardHeaders: true,
  legacyHeaders: false
});
app.use('/api/auth/login', authLimiter);

// 3. CORS configurato restrittivamente
app.use(cors({
  origin: ['https://miosito.it', 'https://admin.miosito.it'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400
}));

// 4. Prevenzione inquinamento parametri HTTP
app.use(hpp());

// 5. Sanitizzazione contro NoSQL injection
app.use(mongoSanitize());

// 6. Sanitizzazione input personalizzata
import DOMPurify from 'isomorphic-dompurify';

function sanitizzaInput(req, res, next) {
  if (req.body) {
    for (const chiave in req.body) {
      if (typeof req.body[chiave] === 'string') {
        req.body[chiave] = DOMPurify.sanitize(req.body[chiave]);
      }
    }
  }
  next();
}

// 7. Prevenzione SQL injection con query parametrizzate (Prisma lo fa nativamente)
// MAI fare: `SELECT * FROM utenti WHERE id = ${utenteId}` — vulnerabile!
// Prisma: prisma.utente.findUnique({ where: { id: utenteId } }) — sicuro

// 8. Audit delle dipendenze
// npm audit               — verifica vulnerabilita
// npm audit fix            — corregge automaticamente
// npx npm-check-updates   — aggiorna dipendenze

// 9. Protezione contro attacchi di tipo ReDoS (Regular Expression DoS)
// Utilizzare librerie come 'safe-regex' per validare le espressioni regolari
// Evitare regex con backtracking catastrofico su input non controllati

// 10. Limitazione della dimensione del corpo della richiesta
app.use(express.json({ limit: '10kb' }));     // limita il payload JSON
app.use(express.urlencoded({ limit: '10kb', extended: true }));
```

---

## Deployment

### PM2

PM2 e un process manager per Node.js in produzione. Offre cluster mode, monitoraggio, gestione log e riavvio automatico.

```javascript
// ecosystem.config.cjs
module.exports = {
  apps: [{
    name: 'mia-api',
    script: './src/server.js',
    instances: 'max',          // utilizza tutti i core CPU
    exec_mode: 'cluster',      // modalita cluster
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'development',
      PORT: 3000
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 8080
    },
    // Logging
    error_file: './logs/error.log',
    out_file: './logs/output.log',
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    // Riavvio automatico
    watch: false,
    max_restarts: 10,
    restart_delay: 4000
  }]
};
```

```bash
# Comandi PM2 essenziali
pm2 start ecosystem.config.cjs --env production
pm2 list                        # elenco processi
pm2 monit                       # monitoraggio in tempo reale
pm2 logs                        # visualizza log
pm2 restart mia-api             # riavvio
pm2 reload mia-api              # ricaricamento zero-downtime
pm2 stop mia-api                # arresto
pm2 delete mia-api              # rimozione
pm2 save                        # salva configurazione
pm2 startup                     # configura avvio automatico al boot
```

### Docker

```dockerfile
# Dockerfile
FROM node:20-alpine AS base
WORKDIR /app
RUN corepack enable

# Fase di installazione dipendenze
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod

# Fase di build (se necessaria)
FROM base AS build
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

# Fase di produzione
FROM base AS production
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./

# Utente non-root per sicurezza
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser
USER appuser

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/server.js"]
```

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://utente:password@db:5432/mioapp
      - REDIS_URL=redis://cache:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: utente
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mioapp
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U utente -d mioapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  cache:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

volumes:
  pg_data:
  redis_data:
```

### Variabili d'Ambiente e Configurazione

```javascript
// config/environment.js
import 'dotenv/config';
import { z } from 'zod';

const schemaEnv = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url().optional(),
  JWT_SECRET: z.string().min(32),
  JWT_REFRESH_SECRET: z.string().min(32),
  CORS_ORIGIN: z.string().default('http://localhost:5173'),
  LOG_LEVEL: z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace']).default('info')
});

export const env = schemaEnv.parse(process.env);
```

### Graceful Shutdown

L'arresto graceful garantisce che tutte le richieste in corso vengano completate prima di chiudere il server.

```javascript
import { createServer } from 'http';

const server = createServer(app);

function avviaChiusuraGraceful(segnale) {
  console.log(`Segnale ${segnale} ricevuto. Avvio chiusura graceful...`);

  // Smetti di accettare nuove connessioni
  server.close(async () => {
    console.log('Server HTTP chiuso');

    try {
      // Chiudi connessioni al database
      await prisma.$disconnect();
      console.log('Connessione database chiusa');

      // Chiudi connessione Redis
      await redis.quit();
      console.log('Connessione Redis chiusa');

      process.exit(0);
    } catch (errore) {
      console.error('Errore durante la chiusura:', errore);
      process.exit(1);
    }
  });

  // Forza chiusura dopo 30 secondi
  setTimeout(() => {
    console.error('Chiusura forzata dopo timeout');
    process.exit(1);
  }, 30000);
}

process.on('SIGTERM', () => avviaChiusuraGraceful('SIGTERM'));
process.on('SIGINT', () => avviaChiusuraGraceful('SIGINT'));
```

### Health Check e Logging

```javascript
// Health check endpoint
app.get('/health', async (req, res) => {
  const stato = {
    stato: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memoria: process.memoryUsage(),
    servizi: {}
  };

  try {
    await prisma.$queryRaw`SELECT 1`;
    stato.servizi.database = 'connesso';
  } catch {
    stato.servizi.database = 'non raggiungibile';
    stato.stato = 'degradato';
  }

  try {
    await redis.ping();
    stato.servizi.redis = 'connesso';
  } catch {
    stato.servizi.redis = 'non raggiungibile';
    stato.stato = 'degradato';
  }

  const codiceStato = stato.stato === 'ok' ? 200 : 503;
  res.status(codiceStato).json(stato);
});

// Logging strutturato con pino
import pino from 'pino';

const logger = pino({
  level: env.LOG_LEVEL,
  transport: env.NODE_ENV === 'development'
    ? { target: 'pino-pretty', options: { colorize: true } }
    : undefined,
  serializers: {
    req: pino.stdSerializers.req,
    res: pino.stdSerializers.res,
    err: pino.stdSerializers.err
  }
});

// Middleware di logging per Express con pino-http
import pinoHttp from 'pino-http';

app.use(pinoHttp({ logger }));

// Utilizzo nel codice
logger.info({ utenteId: '123' }, 'Utente ha effettuato il login');
logger.error({ err: errore, ordineId: '456' }, 'Errore nel processamento ordine');
logger.warn({ tempoRisposta: 2500 }, 'Risposta lenta rilevata');
```

---

## Best Practices

1. **Usare sempre async/await con gestione errori appropriata.** Ogni operazione asincrona deve essere racchiusa in un blocco try/catch o gestita tramite un middleware centralizzato. Le Promise non gestite causano crash imprevedibili e memory leak. Utilizzare `process.on('unhandledRejection')` come rete di sicurezza, ma non come sostituto della corretta gestione degli errori.

2. **Validare tutti gli input in ingresso.** Non fidarsi mai dei dati provenienti dal client. Utilizzare librerie come Zod o Joi per definire schemi di validazione rigorosi. Validare non solo il corpo della richiesta, ma anche parametri di rotta, query string e intestazioni. La validazione deve avvenire il prima possibile nella catena dei middleware, prima che i dati raggiungano la logica di business.

3. **Strutturare il progetto in layer separati.** Separare chiaramente routes (definizione endpoint), controllers (gestione HTTP), services (logica di business) e repositories (accesso ai dati). Questa separazione facilita i test unitari, la manutenibilita e la sostituzione dei componenti. Il controller non deve mai contenere query al database; il service non deve mai accedere a `req` e `res`.

4. **Gestire le variabili d'ambiente con cura.** Non inserire mai segreti direttamente nel codice sorgente o nel repository. Utilizzare file `.env` (esclusi dal version control tramite `.gitignore`), validare le variabili d'ambiente all'avvio dell'applicazione con uno schema e fornire valori predefiniti sensati per l'ambiente di sviluppo. In produzione, utilizzare sistemi di gestione segreti dedicati.

5. **Implementare logging strutturato.** Usare un logger come pino o winston al posto di `console.log`. Il logging strutturato (in formato JSON) facilita l'analisi con strumenti come ELK Stack o Datadog. Includere sempre un correlation ID per tracciare le richieste attraverso i microservizi. Definire livelli di log appropriati: error per errori critici, warn per situazioni anomale, info per eventi significativi, debug per dettagli di sviluppo.

6. **Scrivere test a piu livelli.** I test unitari verificano le singole funzioni e servizi in isolamento. I test di integrazione verificano l'interazione tra componenti (API con database). I test end-to-end verificano i flussi completi. Puntare a una copertura significativa della logica di business, non a metriche di copertura arbitrarie. Usare fixture e factory per dati di test consistenti e manutenibili.

7. **Implementare graceful shutdown.** L'applicazione deve gestire correttamente i segnali di terminazione (SIGTERM, SIGINT). Smettere di accettare nuove connessioni, completare le richieste in corso, chiudere le connessioni a database e cache, quindi terminare il processo. Questo e essenziale per deployment zero-downtime e ambienti containerizzati dove i pod vengono riciclati frequentemente.

8. **Utilizzare rate limiting e protezioni di sicurezza.** Limitare il numero di richieste per IP e per utente. Applicare limiti piu restrittivi agli endpoint sensibili come login e registrazione. Usare helmet per le intestazioni di sicurezza, CORS configurato restrittivamente e sanitizzazione degli input. Eseguire regolarmente `npm audit` per identificare vulnerabilita nelle dipendenze.

9. **Ottimizzare le prestazioni con caching e streaming.** Utilizzare Redis per il caching dei dati letti frequentemente e modificati raramente. Implementare il caching a piu livelli: in-memory per dati caldi, Redis per dati condivisi tra istanze. Per file di grandi dimensioni, usare sempre gli stream invece di caricare tutto in memoria. Monitorare l'utilizzo della memoria e delle connessioni al database con strumenti come Clinic.js.

10. **Containerizzare l'applicazione e automatizzare il deployment.** Usare Docker con build multi-stage per immagini leggere. Utilizzare un utente non-root nel container. Definire health check sia nel Dockerfile che nell'orchestratore. Configurare CI/CD per eseguire automaticamente lint, test e build ad ogni push. Usare `pnpm install --frozen-lockfile` (o `npm ci`) nelle pipeline per installazioni deterministiche e riproducibili.

---

## Node.js 22 LTS — Novita e Funzionalita Avanzate

Node.js 22 e entrato in Long Term Support (LTS) nell'ottobre 2024 con il codename "Jod" e ricevera aggiornamenti di sicurezza fino ad aprile 2027. Questa versione introduce cambiamenti sostanziali che modificano il modo in cui si sviluppano applicazioni Node.js, dalla interoperabilita tra moduli CommonJS e ESM fino al supporto nativo per TypeScript e WebSocket.

### require(esm) — Unificazione dei Sistemi di Moduli

La novita piu significativa di Node.js 22.12+ e la possibilita di utilizzare `require()` per importare moduli ES senza alcun flag sperimentale. Questa funzionalita, dopo anni di sviluppo e iterazione, e stata marcata come stabile a partire dalla versione 22.12.0, eliminando definitivamente la barriera tra i due sistemi di moduli.

```javascript
// Prima di Node.js 22.12: ERR_REQUIRE_ESM
// const { readFile } = require('node:fs/promises'); // funzionava gia
// const esModulo = require('./modulo-esm.mjs');     // ERRORE

// Da Node.js 22.12+: require() puo caricare moduli ESM sincronamente
const moduloESM = require('./utils.mjs');

// Limitazione: se il modulo ESM contiene top-level await,
// viene lanciato ERR_REQUIRE_ASYNC_MODULE
// const moduloAsync = require('./modulo-con-tla.mjs'); // ERRORE

// Verifica se require(esm) e disponibile
if (process.features?.require_module) {
  console.log('require(esm) supportato nativamente');
}
```

Questa unificazione semplifica enormemente l'ecosistema. Le librerie possono ora pubblicare solo il formato ESM sapendo che i consumatori CommonJS potranno comunque importarle tramite `require()`, a condizione che non utilizzino top-level await. Per i maintainer di pacchetti, questo elimina la necessita di produrre build dual (CJS + ESM), riducendo la complessita di configurazione e la dimensione del pacchetto pubblicato.

La raccomandazione per nuovi progetti nel 2025-2026 e di adottare ESM come formato predefinito impostando `"type": "module"` nel `package.json`. ESM allinea il backend al frontend, supporta top-level await stabile e garantisce compatibilita con le future versioni di Node.js.

### WebSocket Client Nativo

Node.js 22 abilita per default il client WebSocket globale, implementato internamente da undici. Non e piu necessario il flag `--experimental-websocket` ne dipendenze esterne come `ws` per connessioni client.

```javascript
// WebSocket client nativo — disponibile globalmente da Node.js 22
const ws = new WebSocket('wss://api.esempio.it/stream');

ws.addEventListener('open', () => {
  console.log('Connessione WebSocket aperta');
  ws.send(JSON.stringify({ tipo: 'subscribe', canale: 'prezzi' }));
});

ws.addEventListener('message', (evento) => {
  const dati = JSON.parse(evento.data);
  console.log('Dati ricevuti:', dati);
});

ws.addEventListener('close', (evento) => {
  console.log(`Connessione chiusa: ${evento.code} — ${evento.reason}`);
});

ws.addEventListener('error', (evento) => {
  console.error('Errore WebSocket:', evento.message);
});
```

Il client WebSocket nativo segue la specifica W3C WebSocket API, la stessa interfaccia utilizzata nei browser. Per i server WebSocket, la libreria `ws` rimane la scelta raccomandata, ma per le connessioni client la dipendenza esterna non e piu necessaria.

### glob e globSync nel Modulo fs

Node.js 22 aggiunge le funzioni `glob` e `globSync` al modulo `node:fs`, consentendo il pattern matching sui percorsi dei file senza dipendenze esterne come `glob` o `fast-glob`.

```javascript
import { glob, globSync } from 'node:fs';
import { glob as globPromise } from 'node:fs/promises';

// Versione sincrona
const fileTS = globSync('src/**/*.ts');
console.log('File TypeScript trovati:', fileTS);

// Versione asincrona con callback
glob('src/**/*.{js,ts}', (errore, file) => {
  if (errore) throw errore;
  console.log('File trovati:', file);
});

// Versione promise-based
const tuttiIFile = await globPromise('**/*.json', {
  cwd: './config',
  exclude: (nome) => nome.startsWith('.')
});
```

### node --run — Esecuzione Diretta di Script

Il flag `--run` permette di eseguire script definiti nel `package.json` direttamente tramite il runtime Node.js, senza passare per `npm run` o `pnpm run`. Questo riduce l'overhead di avvio e semplifica i workflow.

```bash
# Invece di:
npm run test
pnpm run build

# Si puo usare direttamente:
node --run test
node --run build
node --run lint
```

`node --run` cerca il `package.json` piu vicino risalendo la gerarchia delle directory, esegue lo script specificato e imposta automaticamente `node_modules/.bin` nel `PATH`. La differenza rispetto a `npm run` e che non esegue i lifecycle scripts (pre/post) e ha un tempo di avvio significativamente inferiore.

### Altre Novita di Node.js 22

**V8 Maglev Compiler:** Il compilatore JIT mid-tier Maglev e abilitato per default sulle architetture supportate. Maglev si posiziona tra Sparkplug (compilazione rapida ma codice meno ottimizzato) e TurboFan (compilazione lenta ma codice altamente ottimizzato), offrendo un equilibrio ideale per funzioni a vita breve tipiche del server-side rendering. I benchmark mostrano miglioramenti fino al 30% per task CPU-bound.

**AbortSignal ottimizzato:** La creazione di istanze `AbortSignal` e stata resa significativamente piu efficiente, con benefici diretti per `fetch()` e il test runner nativo.

**Structured cloning migliorato:** Il trasferimento dati tra Worker threads tramite clonazione strutturata e ora quasi 2 volte piu veloce rispetto alle versioni precedenti.

**import.meta.dirname e import.meta.filename:** Disponibili in ESM come equivalenti di `__dirname` e `__filename` di CommonJS, senza necessita di costruzioni manuali con `fileURLToPath`.

```javascript
// ESM — equivalenti moderni di __dirname e __filename
console.log(import.meta.dirname);   // '/percorso/alla/directory'
console.log(import.meta.filename);  // '/percorso/alla/directory/file.mjs'
console.log(import.meta.url);       // 'file:///percorso/alla/directory/file.mjs'
```

---

## Event Loop — Approfondimento Architetturale

L'event loop e il cuore del modello di concorrenza di Node.js. Comprenderne le fasi interne, l'ordine di esecuzione delle code e le differenze tra microtask e macrotask e fondamentale per scrivere codice performante e prevedibile.

### Fasi dell'Event Loop

L'event loop di Node.js, implementato dalla libreria C `libuv`, esegue un ciclo continuo attraverso sei fasi distinte. Ogni fase ha una propria coda FIFO di callback da eseguire. Quando l'event loop entra in una fase, esegue le operazioni specifiche di quella fase e poi processa i callback nella coda fino a esaurimento o fino al raggiungimento del limite massimo di callback per iterazione.

```
┌─────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────┐  │
│  │              Timers                            │  │
│  │  setTimeout(), setInterval()                   │  │
│  └───────────────────┬────────────────────────────┘  │
│          ↓  [nextTick queue + microtask queue]       │
│  ┌───────────────────┴────────────────────────────┐  │
│  │         Pending Callbacks                      │  │
│  │  Callback I/O differiti (errori TCP, ecc.)     │  │
│  └───────────────────┬────────────────────────────┘  │
│          ↓  [nextTick queue + microtask queue]       │
│  ┌───────────────────┴────────────────────────────┐  │
│  │           Idle / Prepare                       │  │
│  │  Uso interno di libuv                          │  │
│  └───────────────────┬────────────────────────────┘  │
│          ↓  [nextTick queue + microtask queue]       │
│  ┌───────────────────┴────────────────────────────┐  │
│  │              Poll                              │  │
│  │  Recupera nuovi eventi I/O, esegue callback    │  │
│  │  I/O (file, rete, ecc.)                        │  │
│  └───────────────────┬────────────────────────────┘  │
│          ↓  [nextTick queue + microtask queue]       │
│  ┌───────────────────┴────────────────────────────┐  │
│  │             Check                              │  │
│  │  setImmediate()                                │  │
│  └───────────────────┬────────────────────────────┘  │
│          ↓  [nextTick queue + microtask queue]       │
│  ┌───────────────────┴────────────────────────────┐  │
│  │         Close Callbacks                        │  │
│  │  socket.on('close'), server.on('close')        │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Timers:** Esegue i callback schedulati da `setTimeout()` e `setInterval()` i cui timer sono scaduti. Il timer specifica la soglia minima dopo la quale il callback puo essere eseguito, non il momento esatto. I ritardi del sistema operativo e di altre operazioni possono posticipare l'esecuzione.

**Pending Callbacks:** Esegue callback di operazioni I/O differite alla precedente iterazione, come gli errori di sistema TCP (es. `ECONNREFUSED`).

**Poll:** Fase cruciale in cui Node.js recupera nuovi eventi I/O e ne esegue i callback. Se la coda di poll non e vuota, l'event loop itera attraverso la coda eseguendo i callback in modo sincrono fino a esaurimento o al raggiungimento del limite. Se la coda e vuota e ci sono callback `setImmediate()`, l'event loop passa alla fase Check. Se non ci sono `setImmediate()`, l'event loop attende che nuovi callback vengano aggiunti alla coda e li esegue immediatamente.

**Check:** Esegue i callback di `setImmediate()`. Questa fase permette di eseguire codice immediatamente dopo il completamento della fase Poll.

**Close Callbacks:** Gestisce gli eventi di chiusura come `socket.on('close')`.

### Microtask, process.nextTick e queueMicrotask

Tra ogni fase dell'event loop, Node.js svuota completamente due code speciali prima di procedere alla fase successiva. L'ordine di priorita e:

1. **Coda nextTick** — callback registrati con `process.nextTick()`
2. **Coda microtask** — callback di Promise (`.then()`, `.catch()`, `.finally()`), `async/await` e `queueMicrotask()`

```javascript
// Dimostrazione dell'ordine di esecuzione
console.log('1 — Script sincrono');

setTimeout(() => console.log('6 — setTimeout (macrotask, fase Timers)'), 0);

setImmediate(() => console.log('7 — setImmediate (fase Check)'));

Promise.resolve().then(() => console.log('3 — Promise.then (microtask)'));

queueMicrotask(() => console.log('4 — queueMicrotask (microtask)'));

process.nextTick(() => {
  console.log('2 — process.nextTick (massima priorita)');
  // Un nextTick dentro un nextTick viene eseguito prima delle microtask
  process.nextTick(() => console.log('5 — nextTick annidato'));
});

console.log('1b — Ancora script sincrono');

// Output garantito:
// 1 — Script sincrono
// 1b — Ancora script sincrono
// 2 — process.nextTick (massima priorita)
// 5 — nextTick annidato
// 3 — Promise.then (microtask)
// 4 — queueMicrotask (microtask)
// 6 — setTimeout (macrotask, fase Timers)
// 7 — setImmediate (fase Check)
```

**process.nextTick vs queueMicrotask:** `process.nextTick()` ha priorita superiore rispetto a `queueMicrotask()`: la coda nextTick viene svuotata completamente prima che qualsiasi microtask venga processata. Tuttavia, `queueMicrotask()` e la scelta raccomandata per nuovo codice perche e conforme allo standard web (WHATWG) ed e disponibile anche nei browser, mentre `process.nextTick()` e specifico di Node.js.

**Rischio di starvation:** Se i callback `process.nextTick()` o le microtask schedulano ricorsivamente altri callback nella stessa coda, l'event loop non avanzera mai alle fasi successive, bloccando l'esecuzione dei timer, dell'I/O e di tutti i macrotask. Questo fenomeno e chiamato "starvation" e deve essere evitato.

```javascript
// PERICOLOSO — causa starvation dell'event loop
function starvation() {
  process.nextTick(starvation); // loop infinito nella coda nextTick
}

// CORRETTO — cede il controllo all'event loop
function deferAlProssimoGiro() {
  setImmediate(() => {
    // questa logica viene eseguita nella fase Check,
    // permettendo ad altre fasi di procedere
    elaboraDatiInBatch();
    if (ciSonoPiuDati) setImmediate(deferAlProssimoGiro);
  });
}
```

### Thread Pool di libuv

Sebbene Node.js sia single-threaded per il codice JavaScript, le operazioni I/O bloccanti vengono delegate al thread pool di libuv. Per default, il pool contiene 4 thread, configurabile tramite la variabile d'ambiente `UV_THREADPOOL_SIZE` (massimo 1024).

Le operazioni che utilizzano il thread pool includono: operazioni su file system (`fs.*`), ricerche DNS (`dns.lookup()`), alcune operazioni crittografiche (`crypto.pbkdf2`, `crypto.randomBytes`), compressione (`zlib`). Le operazioni di rete (TCP, UDP, HTTP) utilizzano invece le API asincrone del sistema operativo (epoll su Linux, kqueue su macOS, IOCP su Windows) e non occupano il thread pool.

```bash
# Aumentare il thread pool per applicazioni I/O-intensive
UV_THREADPOOL_SIZE=16 node server.js

# Oppure nel codice, prima di qualsiasi operazione asincrona
process.env.UV_THREADPOOL_SIZE = '16';
```

---

## Stream Avanzati

Gli stream sono il meccanismo fondamentale di Node.js per gestire flussi di dati in modo incrementale. Oltre all'uso base di `createReadStream` e `createWriteStream`, esistono pattern avanzati essenziali per applicazioni production-ready.

### Pipeline e Gestione Errori

La funzione `pipeline()` del modulo `stream/promises` e il metodo raccomandato per collegare stream tra loro. A differenza del metodo `.pipe()`, `pipeline()` gestisce automaticamente la propagazione degli errori e la pulizia delle risorse in caso di fallimento.

```javascript
import { pipeline } from 'stream/promises';
import { createReadStream, createWriteStream } from 'fs';
import { createGzip, createGunzip } from 'zlib';
import { Transform } from 'stream';

// Pipeline con transform stream personalizzato
const filtroRighe = new Transform({
  transform(chunk, encoding, callback) {
    const righe = chunk.toString().split('\n');
    const filtrate = righe
      .filter(riga => riga.includes('ERROR'))
      .join('\n');
    callback(null, filtrate + '\n');
  }
});

// Catena completa: leggi → filtra → comprimi → scrivi
try {
  await pipeline(
    createReadStream('/var/log/applicazione.log'),
    filtroRighe,
    createGzip(),
    createWriteStream('/var/log/errori-compressi.log.gz')
  );
  console.log('Pipeline completata con successo');
} catch (errore) {
  // pipeline() propaga automaticamente gli errori da qualsiasi stream
  // e distrugge tutti gli stream nella catena
  console.error('Pipeline fallita:', errore.message);
}
```

### Transform Stream Personalizzati

I Transform stream sono stream duplex che trasformano i dati in transito. Sono fondamentali per il processing di flussi di dati senza accumularli in memoria.

```javascript
import { Transform } from 'stream';

// Transform stream con gestione dello stato interno
class ParserCSV extends Transform {
  constructor(opzioni = {}) {
    super({ ...opzioni, objectMode: true });
    this._intestazioni = null;
    this._buffer = '';
    this._separatore = opzioni.separatore || ',';
  }

  _transform(chunk, encoding, callback) {
    this._buffer += chunk.toString();
    const righe = this._buffer.split('\n');
    // Mantieni l'ultima riga incompleta nel buffer
    this._buffer = righe.pop();

    for (const riga of righe) {
      if (!riga.trim()) continue;
      const campi = riga.split(this._separatore);

      if (!this._intestazioni) {
        this._intestazioni = campi.map(c => c.trim());
        continue;
      }

      const oggetto = {};
      this._intestazioni.forEach((intestazione, indice) => {
        oggetto[intestazione] = campi[indice]?.trim();
      });
      this.push(oggetto); // emette un oggetto per ogni riga
    }
    callback();
  }

  _flush(callback) {
    // Processa l'ultima riga rimasta nel buffer
    if (this._buffer.trim() && this._intestazioni) {
      const campi = this._buffer.split(this._separatore);
      const oggetto = {};
      this._intestazioni.forEach((intestazione, indice) => {
        oggetto[intestazione] = campi[indice]?.trim();
      });
      this.push(oggetto);
    }
    callback();
  }
}

// Utilizzo
const parser = new ParserCSV({ separatore: ';' });
createReadStream('dati.csv')
  .pipe(parser)
  .on('data', (riga) => console.log(riga))
  .on('end', () => console.log('Parsing completato'));
```

### Backpressure

La backpressure e il meccanismo che impedisce a un produttore di dati di sopraffare un consumatore piu lento. Quando un `Writable` stream non riesce a tenere il passo con il `Readable` stream che lo alimenta, il sistema di backpressure entra in azione automaticamente.

```javascript
import { createReadStream, createWriteStream } from 'fs';

// ERRATO — ignora la backpressure, rischia overflow di memoria
const sorgente = createReadStream('file-enorme.dat');
const destinazione = createWriteStream('output.dat');

sorgente.on('data', (chunk) => {
  // .write() restituisce false quando il buffer interno e pieno
  // Ignorare il valore di ritorno causa accumulo in memoria
  destinazione.write(chunk);
});

// CORRETTO — rispetta la backpressure manualmente
const sorgente2 = createReadStream('file-enorme.dat');
const destinazione2 = createWriteStream('output.dat');

sorgente2.on('data', (chunk) => {
  const bufferDisponibile = destinazione2.write(chunk);
  if (!bufferDisponibile) {
    // Il buffer e pieno: mette in pausa la lettura
    sorgente2.pause();
    // Riprende quando il buffer e stato svuotato
    destinazione2.once('drain', () => sorgente2.resume());
  }
});

// MIGLIORE — pipeline gestisce tutto automaticamente
import { pipeline } from 'stream/promises';
await pipeline(
  createReadStream('file-enorme.dat'),
  createWriteStream('output.dat')
);
```

Il `highWaterMark` e la soglia (in byte, default 16 KB per stream di byte, 16 oggetti per objectMode) che determina quando la backpressure si attiva. Quando il buffer interno supera questa soglia, `.write()` restituisce `false` e il flusso viene rallentato. E possibile personalizzare questa soglia per ottimizzare il throughput in base al caso d'uso.

### Web Streams API

Node.js supporta anche la Web Streams API, conforme allo standard WHATWG. Questa API e interoperabile con i browser e viene utilizzata internamente da `fetch()` e da altre API web native.

```javascript
// ReadableStream WHATWG
const streamLeggibile = new ReadableStream({
  start(controller) {
    controller.enqueue('Prima parte dei dati\n');
    controller.enqueue('Seconda parte dei dati\n');
    controller.close();
  }
});

// TransformStream WHATWG
const trasformaMaiuscolo = new TransformStream({
  transform(chunk, controller) {
    controller.enqueue(chunk.toUpperCase());
  }
});

// Composizione con pipeThrough e pipeTo
const streamScrittura = new WritableStream({
  write(chunk) {
    process.stdout.write(chunk);
  }
});

await streamLeggibile
  .pipeThrough(trasformaMaiuscolo)
  .pipeTo(streamScrittura);

// Conversione tra Node.js streams e Web Streams
import { Readable, Writable } from 'stream';

// Node.js Readable → Web ReadableStream
const nodeStream = createReadStream('file.txt');
const webStream = Readable.toWeb(nodeStream);

// Web ReadableStream → Node.js Readable
const tornaNodo = Readable.fromWeb(webStream);

// Iterazione asincrona sui Web Streams
const risposta = await fetch('https://api.esempio.it/dati-grandi');
const lettore = risposta.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await lettore.read();
  if (done) break;
  console.log(decoder.decode(value, { stream: true }));
}
```

---

## Worker Threads e Clustering

Node.js offre due meccanismi complementari per sfruttare CPU multi-core: i **Worker Threads** per il parallelismo all'interno di un singolo processo e il **Cluster Module** per la distribuzione del carico su processi separati.

### Worker Threads — Parallelismo Reale

I Worker Threads sono thread separati che eseguono codice JavaScript in parallelo al thread principale, ciascuno con il proprio event loop e la propria istanza V8. Sono ideali per operazioni CPU-intensive che bloccherebbero l'event loop del main thread.

```javascript
// worker-pool.js — Pool di worker riutilizzabili
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { cpus } from 'os';

if (isMainThread) {
  // --- MAIN THREAD ---
  class WorkerPool {
    #pool = [];
    #coda = [];
    #dimensioneMax;

    constructor(fileWorker, dimensioneMax = cpus().length) {
      this.#dimensioneMax = dimensioneMax;
      this._fileWorker = fileWorker;

      for (let i = 0; i < dimensioneMax; i++) {
        this.#pool.push(this._creaWorker());
      }
    }

    _creaWorker() {
      const worker = new Worker(this._fileWorker);
      worker.disponibile = true;
      worker.on('message', (risultato) => {
        worker._resolve(risultato);
        worker.disponibile = true;
        this._prossimoTask(worker);
      });
      worker.on('error', (errore) => {
        worker._reject(errore);
        worker.disponibile = true;
        this._prossimoTask(worker);
      });
      return worker;
    }

    _prossimoTask(worker) {
      if (this.#coda.length > 0) {
        const { dati, resolve, reject } = this.#coda.shift();
        worker.disponibile = false;
        worker._resolve = resolve;
        worker._reject = reject;
        worker.postMessage(dati);
      }
    }

    esegui(dati) {
      return new Promise((resolve, reject) => {
        const workerLibero = this.#pool.find(w => w.disponibile);
        if (workerLibero) {
          workerLibero.disponibile = false;
          workerLibero._resolve = resolve;
          workerLibero._reject = reject;
          workerLibero.postMessage(dati);
        } else {
          this.#coda.push({ dati, resolve, reject });
        }
      });
    }

    async terminaTutti() {
      await Promise.all(this.#pool.map(w => w.terminate()));
    }
  }

  // Utilizzo del pool
  const pool = new WorkerPool('./calcolo-pesante.js');

  const risultati = await Promise.all([
    pool.esegui({ operazione: 'hash', dati: 'password1' }),
    pool.esegui({ operazione: 'hash', dati: 'password2' }),
    pool.esegui({ operazione: 'fibonacci', n: 45 }),
    pool.esegui({ operazione: 'fibonacci', n: 42 })
  ]);

  console.log('Risultati:', risultati);
  await pool.terminaTutti();

} else {
  // --- WORKER THREAD ---
  parentPort.on('message', (messaggio) => {
    let risultato;
    switch (messaggio.operazione) {
      case 'hash':
        risultato = calcolaHash(messaggio.dati);
        break;
      case 'fibonacci':
        risultato = fibonacci(messaggio.n);
        break;
    }
    parentPort.postMessage(risultato);
  });
}
```

### SharedArrayBuffer e Atomics

Per condividere memoria tra thread senza copia, si utilizzano `SharedArrayBuffer` e `Atomics` per la sincronizzazione.

```javascript
import { Worker, isMainThread } from 'worker_threads';

if (isMainThread) {
  // Memoria condivisa tra main thread e worker
  const bufferCondiviso = new SharedArrayBuffer(4); // 4 byte = 1 Int32
  const vista = new Int32Array(bufferCondiviso);

  const worker = new Worker(import.meta.filename, {
    workerData: { buffer: bufferCondiviso }
  });

  // Attendi che il worker completi l'incremento
  worker.on('message', () => {
    console.log('Valore finale:', Atomics.load(vista, 0));
  });
} else {
  const vista = new Int32Array(workerData.buffer);

  // Incremento atomico — thread-safe
  for (let i = 0; i < 1_000_000; i++) {
    Atomics.add(vista, 0, 1);
  }

  parentPort.postMessage('completato');
}
```

### Cluster Module — Scaling Multi-Processo

Il cluster module crea processi figli (worker) che condividono la stessa porta di rete. Il processo master distribuisce le connessioni in ingresso tra i worker utilizzando un algoritmo round-robin (default su Linux e macOS).

```javascript
import cluster from 'node:cluster';
import http from 'node:http';
import { cpus } from 'node:os';

const numeroCPU = cpus().length;

if (cluster.isPrimary) {
  console.log(`Master ${process.pid} avviato su ${numeroCPU} core`);

  // Fork di un worker per ogni core CPU
  for (let i = 0; i < numeroCPU; i++) {
    cluster.fork();
  }

  // Riavvio automatico dei worker che terminano
  cluster.on('exit', (worker, codice, segnale) => {
    console.warn(
      `Worker ${worker.process.pid} terminato (codice: ${codice}, segnale: ${segnale})`
    );
    if (codice !== 0 && !worker.exitedAfterDisconnect) {
      console.log('Avvio di un nuovo worker...');
      cluster.fork();
    }
  });

  // Comunicazione master → worker
  cluster.on('message', (worker, messaggio) => {
    if (messaggio.tipo === 'metriche') {
      console.log(`Worker ${worker.id}: ${messaggio.richiesteServite} richieste`);
    }
  });

  // Riavvio rolling zero-downtime
  process.on('SIGUSR2', () => {
    const workers = Object.values(cluster.workers);
    const riavviaProssimo = (indice) => {
      if (indice >= workers.length) return;
      const worker = workers[indice];
      console.log(`Riavvio worker ${worker.id}...`);

      const nuovoWorker = cluster.fork();
      nuovoWorker.on('listening', () => {
        worker.disconnect();
        worker.on('disconnect', () => riavviaProssimo(indice + 1));
      });
    };
    riavviaProssimo(0);
  });

} else {
  let richiesteServite = 0;

  const server = http.createServer((req, res) => {
    richiesteServite++;
    res.writeHead(200);
    res.end(`Risposta dal worker ${process.pid}\n`);
  });

  server.listen(3000);
  console.log(`Worker ${process.pid} in ascolto`);

  // Invia metriche al master ogni 10 secondi
  setInterval(() => {
    process.send({ tipo: 'metriche', richiesteServite });
  }, 10000);
}
```

### Worker Threads vs Cluster — Quando Usare Quale

| Aspetto | Worker Threads | Cluster Module |
|---|---|---|
| Modello | Thread nello stesso processo | Processi separati |
| Memoria | Condivisa (SharedArrayBuffer) | Isolata (ogni processo ha il suo heap) |
| Caso d'uso | Calcolo CPU-intensive | Scaling server HTTP |
| Comunicazione | `postMessage`, memoria condivisa | IPC (Inter-Process Communication) |
| Crash | Un crash nel worker non abbatte il processo | Un crash nel worker non impatta gli altri |
| Overhead | Basso (stesso processo V8) | Alto (processo OS completo) |
| Uso tipico | Hash, crittografia, parsing, compressione | Server web multi-core |

---

## Strumenti Diagnostici e Profiling

Identificare colli di bottiglia, memory leak e blocchi dell'event loop richiede strumenti diagnostici specifici. Node.js offre sia tool integrati che un ecosistema di strumenti di terze parti.

### --inspect e Chrome DevTools

Il flag `--inspect` avvia il debugger V8 integrato, che espone un'interfaccia compatibile con Chrome DevTools.

```bash
# Avvio con debugger
node --inspect server.js                    # debugger sulla porta 9229
node --inspect=0.0.0.0:9229 server.js       # accessibile da remoto
node --inspect-brk server.js                # pausa all'inizio del codice

# Connessione da Chrome: chrome://inspect
# Oppure da VS Code: configurazione launch.json con "attach"
```

Da Chrome DevTools e possibile: impostare breakpoint, ispezionare variabili, eseguire codice nella console, catturare heap snapshot per analisi della memoria, registrare profili CPU per identificare funzioni costose, monitorare l'allocazione della memoria in tempo reale.

### Heap Snapshot per Memory Leak

```javascript
import v8 from 'v8';
import { writeFileSync } from 'fs';

// Cattura un heap snapshot programmaticamente
function catturaDump() {
  const nomeFile = `heap-${Date.now()}.heapsnapshot`;
  const stream = v8.writeHeapSnapshot(nomeFile);
  console.log(`Heap snapshot salvato: ${stream}`);
}

// Monitoraggio utilizzo memoria
function monitoraMemoria() {
  const uso = process.memoryUsage();
  console.log({
    rss: `${(uso.rss / 1024 / 1024).toFixed(1)} MB`,           // memoria totale del processo
    heapTotal: `${(uso.heapTotal / 1024 / 1024).toFixed(1)} MB`, // heap allocato
    heapUsed: `${(uso.heapUsed / 1024 / 1024).toFixed(1)} MB`,  // heap in uso
    external: `${(uso.external / 1024 / 1024).toFixed(1)} MB`,  // oggetti C++ legati a JS
    arrayBuffers: `${(uso.arrayBuffers / 1024 / 1024).toFixed(1)} MB`
  });
}

// Cattura snapshot quando la memoria supera una soglia
setInterval(() => {
  const { heapUsed } = process.memoryUsage();
  if (heapUsed > 500 * 1024 * 1024) { // > 500 MB
    catturaDump();
    console.warn('Heap > 500 MB — snapshot catturato');
  }
}, 30000);
```

### Clinic.js

Clinic.js e una suite di strumenti diagnostici che genera visualizzazioni interattive per identificare problemi di performance.

```bash
# Installazione
npm install -g clinic

# clinic doctor — rileva problemi comuni (event loop delay, I/O, GC)
clinic doctor -- node server.js
# Genera un report HTML con raccomandazioni

# clinic flame — CPU flame graph
clinic flame -- node server.js
# Mostra dove l'applicazione spende la maggior parte del tempo CPU

# clinic bubbleprof — visualizzazione del flusso asincrono
clinic bubbleprof -- node server.js
# Identifica colli di bottiglia nel flusso asincrono
```

**clinic doctor** analizza tre metriche chiave: ritardo dell'event loop (se supera costantemente 20ms indica un problema), frequenza della garbage collection (GC troppo frequente indica allocazioni eccessive), throughput I/O (pattern anomali indicano bottleneck di rete o disco).

**clinic flame** genera flame graph CPU che mostrano visivamente la gerarchia delle chiamate e il tempo speso in ciascuna funzione. Le "fiamme" larghe indicano funzioni costose da ottimizzare.

### 0x — Flame Graph Leggero

`0x` e un tool piu leggero di Clinic.js specifico per la generazione di flame graph CPU.

```bash
# Installazione
npm install -g 0x

# Generazione flame graph
0x -- node server.js
# Genera una directory con un file HTML interattivo

# Con script npm
0x -- node --max-old-space-size=4096 server.js

# Analisi in produzione con tempo limitato
0x --collect-only --output-dir ./profili -- node server.js &
# Dopo il periodo di raccolta, genera il flame graph
0x --visualize-only ./profili/*.0x
```

### perf_hooks — Metriche Interne

Il modulo `perf_hooks` fornisce accesso alle API Performance del browser all'interno di Node.js.

```javascript
import {
  performance,
  PerformanceObserver,
  monitorEventLoopDelay
} from 'perf_hooks';

// Misurazione delle operazioni
performance.mark('inizio-query');
const risultati = await database.query('SELECT * FROM prodotti');
performance.mark('fine-query');
performance.measure('query-database', 'inizio-query', 'fine-query');

// Observer per raccogliere le misurazioni
const obs = new PerformanceObserver((lista) => {
  for (const entry of lista.getEntries()) {
    console.log(`${entry.name}: ${entry.duration.toFixed(2)}ms`);
  }
});
obs.observe({ entryTypes: ['measure'] });

// Monitoraggio del ritardo dell'event loop
const istogramma = monitorEventLoopDelay({ resolution: 20 });
istogramma.enable();

setInterval(() => {
  console.log({
    min: `${(istogramma.min / 1e6).toFixed(2)}ms`,
    max: `${(istogramma.max / 1e6).toFixed(2)}ms`,
    media: `${(istogramma.mean / 1e6).toFixed(2)}ms`,
    p99: `${(istogramma.percentile(99) / 1e6).toFixed(2)}ms`
  });
  istogramma.reset();
}, 5000);
```

---

## Test Runner Nativo (node:test)

A partire da Node.js 22, il test runner nativo `node:test` e una soluzione matura per test unitari e di integrazione senza dipendenze esterne. Supporta test suite annidate, mocking, hook del ciclo di vita, reporter personalizzati e copertura del codice.

### Struttura Base

```javascript
// calcoli.test.js
import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { calcolaSconto, validaEmail, formattaPrezzo } from './calcoli.js';

describe('calcolaSconto', () => {
  it('applica uno sconto percentuale al prezzo', () => {
    const risultato = calcolaSconto(100, 20);
    assert.strictEqual(risultato, 80);
  });

  it('restituisce il prezzo originale se lo sconto e zero', () => {
    assert.strictEqual(calcolaSconto(50, 0), 50);
  });

  it('lancia un errore per sconto negativo', () => {
    assert.throws(
      () => calcolaSconto(100, -5),
      { message: /sconto.*negativo/i }
    );
  });

  it('lancia un errore per sconto superiore a 100', () => {
    assert.throws(
      () => calcolaSconto(100, 150),
      { message: /sconto.*100/i }
    );
  });
});

describe('validaEmail', () => {
  it('accetta email valide', () => {
    assert.ok(validaEmail('utente@esempio.it'));
    assert.ok(validaEmail('nome.cognome@dominio.co.uk'));
  });

  it('rifiuta email senza chiocciola', () => {
    assert.ok(!validaEmail('utente-esempio.it'));
  });

  it('rifiuta stringhe vuote', () => {
    assert.ok(!validaEmail(''));
  });
});

describe('formattaPrezzo', () => {
  it('formatta con due decimali e simbolo euro', () => {
    assert.strictEqual(formattaPrezzo(19.9), '19,90 EUR');
  });
});
```

### Mocking Nativo

```javascript
import { describe, it, mock, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

describe('ServizioOrdini', () => {
  let mockDB;
  let mockEmail;

  beforeEach(() => {
    // Mock di funzioni
    mockDB = {
      trova: mock.fn(async (id) => ({ id, nome: 'Prodotto Test', prezzo: 29.99 })),
      salva: mock.fn(async (ordine) => ({ ...ordine, id: 'ordine-123' }))
    };

    mockEmail = {
      invia: mock.fn(async () => ({ inviato: true }))
    };
  });

  it('crea un ordine e invia email di conferma', async () => {
    const servizio = creaServizioOrdini(mockDB, mockEmail);
    const ordine = await servizio.creaOrdine('utente-1', ['prod-1']);

    // Verifica che il database sia stato chiamato
    assert.strictEqual(mockDB.salva.mock.calls.length, 1);
    assert.strictEqual(mockDB.trova.mock.calls.length, 1);

    // Verifica gli argomenti passati
    const argomentiSalvataggio = mockDB.salva.mock.calls[0].arguments[0];
    assert.strictEqual(argomentiSalvataggio.utenteId, 'utente-1');

    // Verifica invio email
    assert.strictEqual(mockEmail.invia.mock.calls.length, 1);
  });

  it('non invia email se il salvataggio fallisce', async () => {
    mockDB.salva = mock.fn(async () => { throw new Error('DB non disponibile'); });

    const servizio = creaServizioOrdini(mockDB, mockEmail);
    await assert.rejects(
      () => servizio.creaOrdine('utente-1', ['prod-1']),
      { message: 'DB non disponibile' }
    );

    assert.strictEqual(mockEmail.invia.mock.calls.length, 0);
  });
});

// Mock di moduli
import { describe, it, mock } from 'node:test';

// Mock di un intero modulo
mock.module('./database.js', {
  namedExports: {
    connetti: mock.fn(async () => ({ connesso: true })),
    query: mock.fn(async (sql) => [])
  }
});

// Mock di timer
import { describe, it, mock } from 'node:test';

it('esegue il callback dopo il timer', () => {
  mock.timers.enable({ apis: ['setTimeout'] });

  const callback = mock.fn();
  setTimeout(callback, 5000);

  mock.timers.tick(5000);
  assert.strictEqual(callback.mock.calls.length, 1);

  mock.timers.reset();
});
```

### Esecuzione e Copertura

```bash
# Esecuzione test
node --test                                    # tutti i file *.test.js
node --test src/**/*.test.js                   # pattern specifico
node --test --test-reporter spec               # reporter dettagliato
node --test --test-reporter tap                # formato TAP
node --test --test-concurrency 4               # 4 file in parallelo
node --test --test-only                        # solo test con { only: true }

# Copertura del codice (sperimentale)
node --test --experimental-test-coverage       # report in console
node --test --experimental-test-coverage \
  --test-coverage-include=src/**/*.js          # filtra file
node --test --experimental-test-coverage \
  --test-reporter lcov                         # formato lcov per CI

# Watch mode
node --test --watch                            # riesegue su modifiche
```

---

## Native fetch e undici

### fetch Nativa

La funzione `fetch()` e disponibile globalmente da Node.js 18+ ed e stabile in Node.js 22. L'implementazione sottostante e fornita da `undici`, un client HTTP/1.1 ad alte prestazioni scritto interamente in JavaScript.

```javascript
// GET con gestione errori completa
async function recuperaDati(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const risposta = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'MiaApp/1.0'
      },
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!risposta.ok) {
      throw new Error(`HTTP ${risposta.status}: ${risposta.statusText}`);
    }

    const dati = await risposta.json();
    return dati;
  } catch (errore) {
    if (errore.name === 'AbortError') {
      throw new Error(`Timeout: la richiesta a ${url} non ha risposto in 5 secondi`);
    }
    throw errore;
  }
}

// POST con FormData
const form = new FormData();
form.append('nome', 'Mario');
form.append('avatar', new Blob(['contenuto']), 'avatar.png');

const risposta = await fetch('https://api.esempio.it/utenti', {
  method: 'POST',
  body: form
  // Content-Type impostato automaticamente con boundary
});

// Streaming della risposta
const rispostaStream = await fetch('https://api.esempio.it/dati-grandi');
const reader = rispostaStream.body.getReader();
let totaleByte = 0;

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  totaleByte += value.length;
  // Processa il chunk
}
```

### undici — Client HTTP ad Alte Prestazioni

`undici` offre API piu avanzate di `fetch()` con controllo fine sulle connessioni, pool e dispatching.

```javascript
import { request, Agent, Pool, setGlobalDispatcher } from 'undici';

// Richiesta base con undici
const { statusCode, headers, body } = await request('https://api.esempio.it/dati', {
  method: 'GET',
  headers: { 'Authorization': `Bearer ${token}` }
});
const dati = await body.json();

// Connection pooling globale
const agente = new Agent({
  keepAliveTimeout: 30_000,     // 30 secondi di keep-alive
  keepAliveMaxTimeout: 600_000, // 10 minuti massimo
  connections: 100,             // connessioni per origine
  pipelining: 10                // richieste HTTP pipelined
});
setGlobalDispatcher(agente);

// Pool dedicato per un servizio specifico
const poolServizio = new Pool('https://servizio-interno.it', {
  connections: 50,
  pipelining: 6
});

const { body: corpo } = await poolServizio.request({
  path: '/api/v2/risorse',
  method: 'GET'
});
const risultato = await corpo.json();

// Retry con undici
import { RetryAgent } from 'undici';

const agenteConRetry = new RetryAgent(agente, {
  maxRetries: 3,
  minTimeout: 500,   // 500ms prima del primo retry
  maxTimeout: 10_000, // 10 secondi massimo tra retry
  timeoutFactor: 2,   // raddoppia il timeout a ogni retry
  retryAfter: true    // rispetta l'header Retry-After
});
```

---

## Permission Model

Node.js introduce un modello di permessi sperimentale (disponibile da Node.js 20, migliorato in Node.js 22) che limita l'accesso del processo a risorse specifiche del sistema operativo. Questo e particolarmente utile per eseguire codice di terze parti con il minimo privilegio necessario.

### Flag di Permesso

```bash
# Permessi di lettura file system
node --experimental-permission --allow-fs-read=/app/data server.js
node --experimental-permission --allow-fs-read=/app/config,/tmp server.js

# Permessi di scrittura file system
node --experimental-permission --allow-fs-write=/app/logs,/tmp server.js

# Permessi di rete
node --experimental-permission --allow-net=api.esempio.it server.js
node --experimental-permission --allow-net=api.esempio.it:443,db.interna.it:5432 server.js

# Permessi per child process
node --experimental-permission --allow-child-process server.js

# Permessi per worker threads
node --experimental-permission --allow-worker server.js

# Combinazione di piu permessi
node --experimental-permission \
  --allow-fs-read=/app \
  --allow-fs-write=/app/logs,/tmp \
  --allow-net=api.esempio.it:443 \
  server.js
```

### Verifica Programmatica dei Permessi

```javascript
// Verifica se un permesso e stato concesso
if (process.permission.has('fs.read', '/app/data')) {
  const dati = await readFile('/app/data/config.json', 'utf-8');
} else {
  console.warn('Permesso di lettura negato per /app/data');
}

// Verifica permessi di rete
if (process.permission.has('net', 'api.esempio.it')) {
  const risposta = await fetch('https://api.esempio.it/dati');
}

// Gestione degli errori di permesso
try {
  await readFile('/etc/passwd', 'utf-8');
} catch (errore) {
  if (errore.code === 'ERR_ACCESS_DENIED') {
    console.error('Accesso negato dal permission model');
  }
}
```

Il permission model e utile come strato difensivo aggiuntivo per applicazioni che eseguono codice di terze parti, plugin o script utente. Non sostituisce il sandboxing a livello di sistema operativo (container, seccomp, AppArmor) ma aggiunge un controllo a livello di runtime. In Node.js 22.18+, i flag di permesso vengono propagati automaticamente ai processi figli creati con `child_process.spawn()`.

---

## Pattern di Error Handling Avanzati

### AsyncLocalStorage per Context Propagation

`AsyncLocalStorage` (modulo `node:async_hooks`) permette di propagare dati contestuali attraverso catene di chiamate asincrone senza passarli esplicitamente come parametri. E la soluzione ufficiale per sostituire il deprecato modulo `domain` ed e stabile a partire da Node.js 16.

```javascript
import { AsyncLocalStorage } from 'node:async_hooks';

// Store globale per il contesto della richiesta
const contestoRichiesta = new AsyncLocalStorage();

// Middleware Express per impostare il contesto
function middlewareContesto(req, res, next) {
  const contesto = {
    richiestaId: crypto.randomUUID(),
    utenteId: req.utente?.id || 'anonimo',
    timestamp: Date.now(),
    ip: req.ip
  };

  // run() crea un nuovo contesto asincrono
  // Tutti i callback e le Promise all'interno ereditano questo contesto
  contestoRichiesta.run(contesto, () => next());
}

// Il contesto e accessibile ovunque nella catena asincrona
// senza doverlo passare come parametro
class Logger {
  static info(messaggio, dati = {}) {
    const ctx = contestoRichiesta.getStore();
    console.log(JSON.stringify({
      livello: 'info',
      messaggio,
      richiestaId: ctx?.richiestaId,
      utenteId: ctx?.utenteId,
      timestamp: new Date().toISOString(),
      ...dati
    }));
  }

  static error(messaggio, errore, dati = {}) {
    const ctx = contestoRichiesta.getStore();
    console.error(JSON.stringify({
      livello: 'error',
      messaggio,
      richiestaId: ctx?.richiestaId,
      utenteId: ctx?.utenteId,
      errore: {
        nome: errore.name,
        messaggio: errore.message,
        stack: errore.stack
      },
      ...dati
    }));
  }
}

// Utilizzo nel service layer — nessun parametro di contesto necessario
async function processaOrdine(datiOrdine) {
  Logger.info('Inizio processamento ordine', { ordineId: datiOrdine.id });

  try {
    const prodotti = await recuperaProdotti(datiOrdine.articoli);
    const totale = calcolaTotale(prodotti);
    Logger.info('Totale calcolato', { ordineId: datiOrdine.id, totale });

    const ordine = await salvaOrdine({ ...datiOrdine, totale });
    await inviaConferma(ordine);

    Logger.info('Ordine completato', { ordineId: ordine.id });
    return ordine;
  } catch (errore) {
    Logger.error('Errore nel processamento ordine', errore, {
      ordineId: datiOrdine.id
    });
    throw errore;
  }
}
```

### Pattern di Error Handling Strutturato

```javascript
// Gerarchia di errori operativi
class ErroreBase extends Error {
  constructor(messaggio, opzioni = {}) {
    super(messaggio);
    this.nome = this.constructor.name;
    this.statusCode = opzioni.statusCode || 500;
    this.codice = opzioni.codice || 'ERRORE_INTERNO';
    this.operazionale = opzioni.operazionale ?? true;
    this.contesto = opzioni.contesto || {};
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON() {
    return {
      nome: this.nome,
      messaggio: this.message,
      codice: this.codice,
      statusCode: this.statusCode,
      contesto: this.contesto
    };
  }
}

class ErroreValidazione extends ErroreBase {
  constructor(campi) {
    super('Errore di validazione', {
      statusCode: 400,
      codice: 'VALIDAZIONE_FALLITA',
      contesto: { campi }
    });
  }
}

class ErroreNonTrovato extends ErroreBase {
  constructor(risorsa, id) {
    super(`${risorsa} con id ${id} non trovato`, {
      statusCode: 404,
      codice: 'RISORSA_NON_TROVATA',
      contesto: { risorsa, id }
    });
  }
}

class ErroreConflitto extends ErroreBase {
  constructor(messaggio, contesto) {
    super(messaggio, {
      statusCode: 409,
      codice: 'CONFLITTO',
      contesto
    });
  }
}

class ErroreServizioEsterno extends ErroreBase {
  constructor(servizio, erroreOriginale) {
    super(`Servizio ${servizio} non disponibile`, {
      statusCode: 502,
      codice: 'SERVIZIO_NON_DISPONIBILE',
      operazionale: true,
      contesto: {
        servizio,
        erroreOriginale: erroreOriginale.message
      }
    });
  }
}

// Gestore centralizzato che distingue errori operativi da programmatore
function gestoreErroriCentralizzato(errore) {
  if (errore instanceof ErroreBase && errore.operazionale) {
    // Errore operazionale: loggare e rispondere al client
    Logger.error('Errore operazionale', errore, errore.contesto);
    return; // l'applicazione puo continuare
  }

  // Errore del programmatore: bug — crash controllato
  Logger.error('Errore critico del programmatore — arresto', errore);
  process.exit(1);
}

process.on('uncaughtException', (errore) => {
  gestoreErroriCentralizzato(errore);
});

process.on('unhandledRejection', (ragione) => {
  gestoreErroriCentralizzato(
    ragione instanceof Error ? ragione : new Error(String(ragione))
  );
});
```

---

## Sicurezza — Supply Chain e Hardening

La sicurezza della supply chain npm e diventata una priorita critica dopo gli attacchi su larga scala del 2025. Proteggere la catena delle dipendenze richiede difese multilivello.

### Attacchi alla Supply Chain npm

Nel settembre 2025, 18 pacchetti npm popolari (tra cui `debug` e `chalk`, con oltre 2,6 miliardi di download settimanali combinati) sono stati compromessi tramite social engineering. Gli attaccanti hanno inviato email di reset 2FA convincenti ai maintainer, ottenendo l'accesso ai loro account. Questo tipo di attacco dimostra che la sicurezza delle dipendenze non e solo una questione di codice, ma anche di protezione degli account dei maintainer.

### Hardening della Supply Chain

```bash
# 1. Audit delle dipendenze
npm audit                           # verifica CVE note
npm audit --audit-level=moderate    # soglia minima di severita
pnpm audit                          # equivalente per pnpm

# 2. Lockfile rigoroso in CI/CD
npm ci                              # installazione deterministica da lockfile
pnpm install --frozen-lockfile      # equivalente pnpm
# MAI usare `npm install` in CI — puo aggiornare il lockfile silenziosamente

# 3. Pinning delle versioni
npm config set save-exact true      # salva versioni esatte (senza ^)
# Oppure in .npmrc:
# save-exact=true

# 4. Disabilitare lifecycle scripts per default
npm config set ignore-scripts true
# Poi abilitare esplicitamente per pacchetti fidati:
# npm install --ignore-scripts=false pacchetto-fidato

# 5. Generare SBOM (Software Bill of Materials)
npm sbom --sbom-format cyclonedx    # formato CycloneDX
npm sbom --sbom-format spdx         # formato SPDX
```

### Socket.dev — Analisi Comportamentale

Socket.dev analizza staticamente ogni versione pubblicata di ogni pacchetto npm, rilevando comportamenti sospetti che `npm audit` non puo identificare. Quando un pacchetto inizia improvvisamente a leggere `~/.aws/credentials`, aprire connessioni di rete o eseguire `child_process`, Socket genera un alert immediato, anche se non esiste ancora un advisory formale.

```json
{
  "scripts": {
    "postinstall": "echo 'Nessun lifecycle script pericoloso'"
  }
}
```

```bash
# Installazione del CLI Socket
npm install -g @socketsecurity/cli

# Analisi delle dipendenze
socket npm-audit
socket report create .

# Integrazione CI/CD — blocca PR con dipendenze sospette
# In GitHub Actions:
# - uses: SocketDev/socket-security-py-action@v1
```

### Policy di Sicurezza delle Dipendenze

```javascript
// scripts/audit-deps.js — script di audit personalizzato
import { execSync } from 'child_process';
import { readFileSync } from 'fs';

function auditDipendenze() {
  // 1. Verifica che il lockfile sia committato
  try {
    execSync('git ls-files --error-unmatch pnpm-lock.yaml', { stdio: 'pipe' });
  } catch {
    console.error('ERRORE: pnpm-lock.yaml non presente nel repository');
    process.exit(1);
  }

  // 2. Verifica vulnerabilita note
  try {
    execSync('pnpm audit --audit-level moderate', { stdio: 'inherit' });
  } catch {
    console.error('ERRORE: vulnerabilita trovate nelle dipendenze');
    process.exit(1);
  }

  // 3. Verifica licenze
  const pkgLock = JSON.parse(readFileSync('package.json', 'utf-8'));
  const licenzeVietate = ['GPL-3.0', 'AGPL-3.0', 'SSPL'];

  console.log('Audit dipendenze completato con successo');
}

auditDipendenze();
```

### Configurazione Sicura di npm/pnpm

```ini
# .npmrc — configurazione di sicurezza
save-exact=true
engine-strict=true
ignore-scripts=true
audit=true
fund=false

# pnpm specifico
shamefully-hoist=false
strict-peer-dependencies=true
auto-install-peers=true

# Verifica integrita dei pacchetti
package-lock=true
```

---

## Performance Tuning

### Flag V8 per Ottimizzazione

Node.js espone numerosi flag V8 per controllare il comportamento del compilatore JIT, della garbage collection e dell'allocazione della memoria.

```bash
# Memoria — flag fondamentali
node --max-old-space-size=4096 server.js    # heap massimo 4 GB
node --max-semi-space-size=64 server.js     # semi-space 64 MB (default 16 MB)

# Il semi-space controlla la dimensione del "young generation" dove
# vengono allocati gli oggetti a vita breve. Un semi-space piu grande
# riduce la frequenza del GC Scavenge ma aumenta il consumo di memoria.

# Diagnostica delle ottimizzazioni V8
node --trace-opt server.js          # log delle funzioni ottimizzate
node --trace-deopt server.js        # log delle de-ottimizzazioni
# Le de-ottimizzazioni indicano che V8 ha dovuto annullare
# un'ottimizzazione — spesso a causa di tipi inconsistenti

# Ottimizzazione per ambienti con memoria limitata
node --optimize-for-size server.js  # meno memoria per il codice compilato

# Garbage collection manuale (solo per debug)
node --expose-gc server.js
# Poi nel codice: global.gc()

# Container-aware (Node.js 20+)
# Node.js rileva automaticamente i limiti cgroup del container
# e imposta --max-old-space-size di conseguenza
```

### Limiti di Memoria e Container

In ambienti containerizzati, Node.js 20+ e container-aware: rileva automaticamente i limiti di memoria imposti dal cgroup del container e configura il heap V8 di conseguenza. Tuttavia, e buona pratica impostare esplicitamente i limiti.

```dockerfile
# Dockerfile — configurazione memoria
FROM node:22-alpine
ENV NODE_OPTIONS="--max-old-space-size=1536"
# Per un container con 2 GB di RAM, riservare ~75% per il heap V8
# Il restante 25% e per il sistema operativo, buffer, stack C++
```

```javascript
// Monitoraggio runtime della memoria
import v8 from 'v8';

function statisticheHeap() {
  const stats = v8.getHeapStatistics();
  return {
    heapTotale: `${(stats.total_heap_size / 1024 / 1024).toFixed(1)} MB`,
    heapUsato: `${(stats.used_heap_size / 1024 / 1024).toFixed(1)} MB`,
    limiteHeap: `${(stats.heap_size_limit / 1024 / 1024).toFixed(1)} MB`,
    malevodEsterno: `${(stats.external_memory / 1024 / 1024).toFixed(1)} MB`,
    percentualeUso: `${((stats.used_heap_size / stats.heap_size_limit) * 100).toFixed(1)}%`
  };
}
```

### Connection Pooling

Il pooling delle connessioni e critico per le prestazioni di applicazioni che comunicano con database e servizi esterni.

```javascript
// Pool di connessioni PostgreSQL con pg
import pg from 'pg';

const pool = new pg.Pool({
  host: process.env.DB_HOST,
  port: 5432,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20,                        // connessioni massime nel pool
  idleTimeoutMillis: 30000,       // chiudi connessioni inattive dopo 30s
  connectionTimeoutMillis: 5000,  // timeout per ottenere una connessione
  maxUses: 7500,                  // ricicla connessione dopo N query
  allowExitOnIdle: true           // permette al processo di terminare
});

// Monitoraggio del pool
pool.on('connect', () => {
  console.log(`Pool: ${pool.totalCount} totali, ${pool.idleCount} inattive, ${pool.waitingCount} in attesa`);
});

pool.on('error', (errore) => {
  console.error('Errore pool database:', errore.message);
});

// Pool HTTP per servizi upstream
import { Agent } from 'undici';

const agenteHTTP = new Agent({
  connections: 50,           // connessioni per origine
  pipelining: 10,            // richieste pipelined per connessione
  keepAliveTimeout: 30_000,  // keep-alive 30 secondi
  keepAliveMaxTimeout: 600_000
});
```

---

## TypeScript in Node.js

Node.js 22 introduce il supporto nativo per l'esecuzione di file TypeScript tramite il meccanismo di "type stripping", che rimuove le annotazioni di tipo a runtime senza compilazione completa.

### --experimental-strip-types

```bash
# Esecuzione diretta di file .ts (da Node.js 22.6+)
node --experimental-strip-types app.ts

# Con transform dei costrutti TypeScript-only (enum, namespace)
node --experimental-transform-types app.ts
# Implica automaticamente --experimental-strip-types

# Da Node.js 23.6+, --experimental-strip-types e abilitato per default
# In Node.js 25.2+, la funzionalita e stata marcata come stabile
```

Il type stripping rimuove le annotazioni di tipo (`: string`, `interface`, `type`, generics) senza eseguire alcun type-checking. Il codice TypeScript viene trattato come JavaScript con annotazioni da eliminare. Questo approccio e estremamente veloce ma ha delle limitazioni.

**Limitazioni del type stripping nativo:**
- Non supporta `enum` e `namespace` senza `--experimental-transform-types`
- Non risolve i path alias del `tsconfig.json` (es. `@/utils`)
- Non supporta decoratori (proposta TC39 Stage 3)
- Non esegue type-checking — per quello serve `tsc --noEmit`
- Non supporta JSX senza flag aggiuntivi

```javascript
// app.ts — funziona con --experimental-strip-types
interface Utente {
  id: string;
  nome: string;
  email: string;
}

function saluta(utente: Utente): string {
  return `Ciao ${utente.nome}!`;
}

const utente: Utente = { id: '1', nome: 'Mario', email: 'mario@esempio.it' };
console.log(saluta(utente));

// ATTENZIONE: i seguenti costrutti NON funzionano con strip-types base
// enum Ruolo { ADMIN, UTENTE }           // richiede --experimental-transform-types
// namespace MioNamespace { ... }          // richiede --experimental-transform-types
```

### tsx — Alternativa Completa

`tsx` (TypeScript Execute) utilizza `esbuild` internamente per una transpilazione quasi istantanea con supporto completo per tutti i costrutti TypeScript.

```bash
# Installazione
pnpm add -D tsx

# Esecuzione
pnpm tsx src/server.ts

# Watch mode
pnpm tsx watch src/server.ts

# In package.json
{
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "start": "tsx src/server.ts"
  }
}
```

`tsx` supporta: enum, namespace, decoratori, path alias (tramite tsconfig-paths), JSX/TSX, import di file JSON, e funziona sia con CommonJS che ESM. Il compromesso e l'aggiunta di una dipendenza di sviluppo.

### ts-node — Alternativa Tradizionale

`ts-node` utilizza il compilatore TypeScript ufficiale (`tsc`) ed e la soluzione piu matura ma anche la piu lenta.

```bash
pnpm add -D ts-node typescript

# Esecuzione con ESM
node --loader ts-node/esm src/server.ts

# Oppure con il binario ts-node
pnpm ts-node --esm src/server.ts
```

### Confronto Approcci TypeScript in Node.js

| Aspetto | strip-types nativo | tsx | ts-node |
|---|---|---|---|
| Velocita | Istantanea | Molto veloce (esbuild) | Lenta (tsc) |
| Dipendenze | Nessuna | tsx, esbuild | ts-node, typescript |
| enum/namespace | Con flag aggiuntivo | Completo | Completo |
| Path alias | No | Con configurazione | Con configurazione |
| Type-checking | No | No | Opzionale |
| Decoratori | No | Parziale | Completo |
| Caso d'uso | Script rapidi, CI | Sviluppo quotidiano | Progetti che richiedono piena compatibilita |

### Setup TypeScript Raccomandato per Node.js 22

```json
// tsconfig.json — configurazione raccomandata
{
  "compilerOptions": {
    "target": "ES2023",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

```json
// package.json — script di sviluppo e produzione
{
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/",
    "test": "node --test --experimental-strip-types src/**/*.test.ts"
  }
}
```

---

## Deployment Avanzato

### PM2 — Configurazione Avanzata

Oltre alla configurazione base, PM2 offre funzionalita avanzate per il deployment in produzione.

```javascript
// ecosystem.config.cjs — configurazione avanzata
module.exports = {
  apps: [{
    name: 'api-produzione',
    script: './dist/server.js',
    instances: 'max',
    exec_mode: 'cluster',
    max_memory_restart: '500M',
    node_args: '--max-old-space-size=1536',

    // Metriche personalizzate
    instance_var: 'INSTANCE_ID',

    // Variabili d'ambiente per ambiente
    env_production: {
      NODE_ENV: 'production',
      PORT: 8080
    },
    env_staging: {
      NODE_ENV: 'staging',
      PORT: 8081
    },

    // Logging avanzato
    error_file: '/var/log/api/error.log',
    out_file: '/var/log/api/output.log',
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss.SSS Z',
    log_type: 'json',

    // Riavvio intelligente
    exp_backoff_restart_delay: 100,  // backoff esponenziale
    max_restarts: 15,
    min_uptime: '10s',              // minimo uptime prima di riavvio
    listen_timeout: 8000,           // timeout per la porta
    kill_timeout: 5000,             // tempo per graceful shutdown

    // Cron restart — riavvio schedulato
    cron_restart: '0 3 * * *',      // riavvio ogni notte alle 3:00

    // Source map support
    source_map_support: true
  }],

  // Deploy con PM2
  deploy: {
    production: {
      user: 'deploy',
      host: ['server1.esempio.it', 'server2.esempio.it'],
      ref: 'origin/main',
      repo: 'git@github.com:utente/progetto.git',
      path: '/var/www/api',
      'pre-deploy': 'git fetch --all',
      'post-deploy': 'pnpm install --frozen-lockfile && pnpm build && pm2 reload ecosystem.config.cjs --env production',
      'pre-setup': 'echo "Preparazione server..."'
    }
  }
};
```

```bash
# Deploy con PM2
pm2 deploy production setup        # setup iniziale
pm2 deploy production              # deploy
pm2 deploy production revert 1     # rollback di un deploy

# Monitoraggio avanzato
pm2 monit                          # dashboard real-time nel terminale
pm2 plus                           # dashboard web (pm2.io)
```

### Docker — Pattern Avanzati

```dockerfile
# Dockerfile — produzione ottimizzata
FROM node:22-alpine AS base
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

# Fase dipendenze — cached layer
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod

# Fase build
FROM base AS build
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build && pnpm prune --prod

# Fase produzione — immagine minimale
FROM node:22-alpine AS production

# Variabili d'ambiente
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=1536 --enable-source-maps"

WORKDIR /app

# Copiare solo il necessario
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./

# Utente non-root
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser && \
    chown -R appuser:nodejs /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:${PORT:-3000}/health || exit 1

EXPOSE ${PORT:-3000}

# Segnale di terminazione corretto
STOPSIGNAL SIGTERM

CMD ["node", "dist/server.js"]
```

```yaml
# docker-compose.yml — stack completo con monitoring
services:
  api:
    build:
      context: .
      target: production
    ports:
      - "${PORT:-3000}:${PORT:-3000}"
    environment:
      - DATABASE_URL=postgresql://utente:${DB_PASSWORD}@db:5432/app
      - REDIS_URL=redis://:${REDIS_PASSWORD}@cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: utente
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: app
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U utente -d app"]
      interval: 5s
      timeout: 5s
      retries: 5

  cache:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pg_data:
  redis_data:
```

### Graceful Shutdown — Pattern Completo

```javascript
import { createServer } from 'http';

function configuraShutdown(server, risorse = {}) {
  let chiusuraInCorso = false;
  const TIMEOUT_CHIUSURA = 30_000; // 30 secondi

  async function chiudi(segnale) {
    if (chiusuraInCorso) return;
    chiusuraInCorso = true;

    console.log(`[${new Date().toISOString()}] Segnale ${segnale} ricevuto`);
    console.log('Avvio chiusura graceful...');

    // Timer di sicurezza per forzare la chiusura
    const timerForzatura = setTimeout(() => {
      console.error('Chiusura forzata: timeout raggiunto');
      process.exit(1);
    }, TIMEOUT_CHIUSURA);
    timerForzatura.unref(); // non impedisce l'uscita del processo

    try {
      // 1. Smetti di accettare nuove connessioni
      await new Promise((resolve, reject) => {
        server.close((errore) => errore ? reject(errore) : resolve());
      });
      console.log('Server HTTP chiuso — nessuna nuova connessione');

      // 2. Chiudi pool di connessioni database
      if (risorse.database) {
        await risorse.database.$disconnect();
        console.log('Pool database chiuso');
      }

      // 3. Chiudi connessione Redis
      if (risorse.redis) {
        await risorse.redis.quit();
        console.log('Connessione Redis chiusa');
      }

      // 4. Chiudi pool HTTP upstream
      if (risorse.httpAgent) {
        await risorse.httpAgent.close();
        console.log('Agent HTTP chiuso');
      }

      // 5. Flush dei log
      if (risorse.logger) {
        risorse.logger.flush();
        console.log('Log flush completato');
      }

      clearTimeout(timerForzatura);
      console.log('Chiusura graceful completata');
      process.exit(0);
    } catch (errore) {
      console.error('Errore durante la chiusura:', errore);
      process.exit(1);
    }
  }

  process.on('SIGTERM', () => chiudi('SIGTERM'));
  process.on('SIGINT', () => chiudi('SIGINT'));
}

// Utilizzo
const server = createServer(app);
configuraShutdown(server, {
  database: prisma,
  redis: redisClient,
  httpAgent: agenteHTTP,
  logger: pinoLogger
});

server.listen(process.env.PORT || 3000);
```

---

> **Riferimenti**: [Documentazione ufficiale Node.js](https://nodejs.org/docs/latest/api/), [Express.js](https://expressjs.com/), [Fastify](https://fastify.dev/), [Prisma](https://www.prisma.io/docs), [Documentazione pnpm](https://pnpm.io/)

---

## Esercizi

### Esercizio 1 — Server HTTP con routing manuale

**Obiettivo:** Comprendere il modulo `http` nativo di Node.js senza framework.

Costruire un server HTTP utilizzando esclusivamente il modulo `node:http` che gestisca le seguenti rotte:

- `GET /` — restituisce una pagina HTML di benvenuto con status 200
- `GET /api/items` — restituisce un array JSON di almeno 5 oggetti con campi `id`, `name`, `price`
- `POST /api/items` — accetta un body JSON, lo valida (campi obbligatori: `name`, `price`) e lo aggiunge alla lista in memoria
- `GET /api/items/:id` — restituisce un singolo oggetto per ID oppure 404 con messaggio strutturato
- Qualsiasi altra rotta — restituisce 404 con body JSON `{ "error": "Not Found" }`

Requisiti aggiuntivi:
- Parsare manualmente il body della richiesta tramite gli eventi `data` ed `end` dello stream
- Impostare correttamente gli header `Content-Type` e `Access-Control-Allow-Origin`
- Gestire gli errori di parsing JSON con status 400
- Scrivere almeno 3 test con il built-in test runner (`node:test`)

### Esercizio 2 — API REST con Express e middleware custom

**Obiettivo:** Padroneggiare il pattern middleware di Express e la struttura a layer.

Creare un'applicazione Express con la seguente architettura:

- **Routes** → **Controllers** → **Services** → **Repository** (in-memory o file JSON)
- Risorsa principale: `tasks` con campi `id`, `title`, `description`, `status`, `createdAt`, `updatedAt`
- CRUD completo con validazione input tramite Zod
- Middleware custom per: request logging con timestamp e durata, correlationId (`X-Request-Id`), error handling centralizzato, rate limiting basico (max 100 req/min per IP)
- Pagination con query params `?page=1&limit=20` e risposta con metadata `{ data, total, page, limit, totalPages }`
- Variabili d'ambiente gestite con `dotenv` e validate all'avvio
- Test di integrazione con `supertest` per ogni endpoint (almeno 10 test case)

### Esercizio 3 — File processing con Stream e Worker Threads

**Obiettivo:** Gestire file di grandi dimensioni senza saturare la memoria.

Sviluppare un tool CLI che processi file CSV di grandi dimensioni (>100MB):

- Leggere il file CSV con `node:fs/createReadStream` e un transform stream custom per il parsing riga per riga
- Implementare un pipeline (`node:stream/promises.pipeline`) che: legga il CSV, filtri le righe in base a un criterio passato come argomento CLI, trasformi i dati (es. normalizzazione campi), scriva il risultato in un nuovo file CSV
- Aggiungere un worker thread (`node:worker_threads`) che calcoli statistiche aggregate (conteggio, media, min, max di una colonna numerica) in parallelo al processing principale
- Mostrare una progress bar nel terminale con percentuale di completamento
- Gestire il graceful shutdown con `SIGINT` interrompendo correttamente gli stream
- Generare un file CSV di test con `node -e` da almeno 100.000 righe per verificare che il consumo di memoria resti costante

### Esercizio 4 — Microservizio con Fastify, Prisma e Redis

**Obiettivo:** Costruire un microservizio production-ready con stack moderno.

Implementare un microservizio per la gestione di un catalogo prodotti:

- **Fastify** con schema validation JSON Schema per request e response
- **Prisma** con PostgreSQL (o SQLite per sviluppo locale) per la persistenza, con migrazioni versionarie
- **Redis** (o `ioredis`) per caching delle query GET con invalidazione su write
- Endpoint: `GET /products` (paginato, con filtri per categoria e prezzo), `GET /products/:id`, `POST /products`, `PUT /products/:id`, `DELETE /products/:id`
- Serializzazione response con `@fastify/response-validation`
- Health check endpoint (`GET /health`) che verifichi connettività a PostgreSQL e Redis
- Logging strutturato con pino (già integrato in Fastify)
- Dockerfile multi-stage con utente non-root e `.dockerignore` appropriato
- `docker-compose.yml` con servizi app, postgres e redis
- Test unitari per i service e test di integrazione per gli endpoint con database di test

### Esercizio 5 — Sistema real-time con WebSocket e Cluster

**Obiettivo:** Scalare un'applicazione Node.js su più CPU con comunicazione in tempo reale.

Progettare un sistema di notifiche in tempo reale:

- Server WebSocket con `ws` (o `@fastify/websocket`) che gestisca: connessione/disconnessione dei client con heartbeat, canali di sottoscrizione (subscribe/unsubscribe a topic), broadcast di messaggi ai sottoscrittori di un topic, acknowledgment dei messaggi ricevuti
- Scaling orizzontale con `node:cluster` su tutti i core disponibili, utilizzando Redis Pub/Sub per sincronizzare i messaggi tra i worker
- API REST per inviare notifiche (`POST /notifications`) che vengano distribuite ai client WebSocket connessi al topic specificato
- Persistenza delle notifiche non consegnate (utente offline) con consegna al reconnect
- Monitoring: endpoint `/metrics` con conteggio connessioni attive, messaggi inviati/ricevuti, uptime per worker
- Graceful shutdown del cluster: il master invia `SIGTERM` ai worker, ciascuno chiude le connessioni WebSocket in corso, poi termina
- Test end-to-end con client WebSocket multipli che verifichino la consegna dei messaggi cross-worker

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Node.js Documentation** — documentazione ufficiale dell'API Node.js 22 LTS, inclusi moduli core, CLI flags e guide. https://nodejs.org/docs/latest-v22.x/api/ (consultato: 2026-05-24)
- **Express.js Guide** — guida ufficiale del framework Express, routing, middleware e best practice. https://expressjs.com/en/guide/routing.html (consultato: 2026-05-24)
- **Fastify Documentation** — documentazione completa di Fastify con riferimenti a plugin, schema validation e lifecycle hooks. https://fastify.dev/docs/latest/ (consultato: 2026-05-24)
- **Node.js Built-in Test Runner** — documentazione del modulo `node:test` per test unitari senza dipendenze esterne. https://nodejs.org/docs/latest-v22.x/api/test.html (consultato: 2026-05-24)
- **pnpm Documentation** — gestione pacchetti performante con workspace e content-addressable storage. https://pnpm.io/motivation (consultato: 2026-05-24)
- **libuv Design Overview** — architettura dell'event loop e del thread pool sottostante a Node.js. https://docs.libuv.org/en/v1.x/design.html (consultato: 2026-05-24)
- **V8 JavaScript Engine** — documentazione del motore V8 utilizzato da Node.js per la compilazione JIT. https://v8.dev/docs (consultato: 2026-05-24)

### Libri e approfondimenti

- Young, Alex; Meck, Bradley; Cantelon, Mike, *Node.js in Action*, Manning, 2017.
- Casciaro, Mario; Mammino, Luciano, *Node.js Design Patterns*, Packt, 2024.
- Hahn, Evan, *Express in Action*, Manning, 2016.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Prerequisito: sintassi ES6+, closures, prototype chain usati nel runtime Node.js |
| [05 — JavaScript Avanzato](05-javascript-avanzato.md) | Prerequisito: async/await, generators, Proxy e Reflect applicati lato server |
| [11 — API Design](11-api-design.md) | Node.js è il runtime principale per implementare le API REST, GraphQL e gRPC descritte |
| [12 — Database Web](12-database-web.md) | Integrazione database: Prisma, Drizzle e driver nativi eseguiti in ambiente Node.js |
| [15 — Testing Web](15-testing-web.md) | Framework di test (Vitest, Jest, Playwright) eseguiti nel runtime Node.js |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Docker, CI/CD e PM2 per il deployment di applicazioni Node.js in produzione |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Event Loop** | Meccanismo single-threaded di Node.js che gestisce operazioni asincrone tramite una coda di callback e microtask. |
| **Middleware** | Funzione che intercetta una richiesta HTTP prima che raggiunga il route handler, utilizzata per logging, autenticazione, validazione. |
| **Stream** | Interfaccia per leggere o scrivere dati in modo incrementale (chunk per chunk) anziché caricarli interamente in memoria. |
| **Worker Thread** | Thread separato dal main thread di Node.js, utilizzato per operazioni CPU-intensive senza bloccare l'event loop. |
| **Cluster Module** | Modulo nativo che permette di creare processi figli che condividono la stessa porta di rete per sfruttare CPU multi-core. |
| **libuv** | Libreria C multi-piattaforma che fornisce l'event loop, l'I/O asincrono e il thread pool a Node.js. |
| **npm** | Node Package Manager, il registro e il CLI predefinito per la gestione delle dipendenze JavaScript. |
| **pnpm** | Gestore pacchetti alternativo che utilizza un content-addressable store per risparmiare spazio disco e velocizzare le installazioni. |
| **REPL** | Read-Eval-Print Loop: shell interattiva di Node.js per eseguire espressioni JavaScript in tempo reale. |
| **CommonJS (CJS)** | Sistema di moduli originale di Node.js basato su `require()` e `module.exports`. |
| **ESM (ES Modules)** | Standard ECMAScript per i moduli JavaScript, supportato nativamente in Node.js con `import`/`export`. |
| **Graceful Shutdown** | Procedura di arresto controllato che completa le richieste in corso e rilascia le risorse prima di terminare il processo. |
| **Buffer** | Oggetto Node.js per gestire dati binari grezzi, utilizzato internamente da stream, file system e networking. |
| **V8** | Motore JavaScript open-source di Google che compila JS in codice macchina nativo, utilizzato da Node.js e Chrome. |