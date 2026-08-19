# Tutorial 16 — Build Tools e Deploy: Dal Principiante all'Esperto

> **Companion a:** `16-build-tools-e-deploy.md`
> **Scope:** perché esiste un bundler, Vite in sviluppo e in build, code splitting e tree shaking, budget di dimensione, gestori di pacchetti e lockfile, lint e formattazione, Docker multi-stage, pipeline CI/CD, variabili d'ambiente e segreti, strategie di rilascio, CDN e cache, monorepo, rollback
> **Prerequisiti:** `tutorial_00_ambiente_setup_web.md` — Node, pnpm, lockfile; `tutorial_15_testing_web.md` — la suite che la pipeline esegue; `tutorial_10_nodejs.md` — il processo che va in produzione
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Vite 6 · pnpm 10 · Docker · GitHub Actions · Node.js LTS

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Perché esiste un bundler](#a1-perché-esiste-un-bundler)
  - [A2. Vite: sviluppo e build sono due cose diverse](#a2-vite-sviluppo-e-build-sono-due-cose-diverse)
  - [A3. Il gestore di pacchetti e il lockfile](#a3-il-gestore-di-pacchetti-e-il-lockfile)
  - [A4. Lint e formattazione: due strumenti, due compiti](#a4-lint-e-formattazione-due-strumenti-due-compiti)
  - [A5. La prima pipeline](#a5-la-prima-pipeline)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Code splitting: cosa dividere e cosa no](#b1-code-splitting-cosa-dividere-e-cosa-no)
  - [B2. Tree shaking e i side effect](#b2-tree-shaking-e-i-side-effect)
  - [B3. Il budget di dimensione, e come si fa rispettare](#b3-il-budget-di-dimensione-e-come-si-fa-rispettare)
  - [B4. Variabili d'ambiente: build time e runtime](#b4-variabili-dambiente-build-time-e-runtime)
  - [B5. Docker multi-stage e l'immagine minima](#b5-docker-multi-stage-e-limmagine-minima)
  - [B6. Cache: nel bundler, in Docker, in CI](#b6-cache-nel-bundler-in-docker-in-ci)
  - [B7. Strategie di rilascio e rollback](#b7-strategie-di-rilascio-e-rollback)
  - [B8. CDN, impronte e intestazioni di cache](#b8-cdn-impronte-e-intestazioni-di-cache)
  - [B9. Monorepo: quando conviene e cosa costa](#b9-monorepo-quando-conviene-e-cosa-costa)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: pipeline CI/CD completa](#c2-mini-progetto-pipeline-cicd-completa)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Build riproducibili](#d1-build-riproducibili)
  - [D2. Feature flag: separare il rilascio dall'attivazione](#d2-feature-flag-separare-il-rilascio-dallattivazione)
  - [D3. Migrazioni del database nel deploy](#d3-migrazioni-del-database-nel-deploy)
  - [D4. Osservabilità del rilascio](#d4-osservabilità-del-rilascio)
  - [D5. Sicurezza della catena di build](#d5-sicurezza-della-catena-di-build)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   SORGENTE                BUILD                    DISTRIBUZIONE
   ────────                ─────                    ─────────────
   .ts .tsx .css     →  transpile · bundle    →  dist/
   node_modules         tree shaking             app.a3f9c2.js
   .env                 code splitting           index.html
                        minify · impronte        assets/…
                             │
                             ▼
   ┌───────────────────────────────────────────────────────────┐
   │  PIPELINE — dal più veloce al più lento                   │
   │   lint → tipi → test unitari → build → test E2E → deploy  │
   │   ogni gradino ferma il successivo: fallire presto costa   │
   │   secondi, fallire tardi costa minuti                     │
   └───────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         CDN (statici)   container      migrazioni DB
         immutable       rolling/blue    prima o dopo?
         1 anno          -green/canary   (vedi D3)

   LE TRE PROPRIETÀ DI UN DEPLOY DI CUI CI SI PUÒ FIDARE
     1. RIPRODUCIBILE  stesso commit → stesso artefatto
     2. REVERSIBILE    tornare indietro in un minuto, senza build
     3. OSSERVABILE    ci si accorge del problema prima degli utenti
```

---

# Parte A — Basi Assolute

---

## A1. Perché esiste un bundler

> **Analogia:** una libreria con quattrocento fascicoli separati. Puoi consultarli tutti, ma ogni volta devi andarli a prendere uno per uno. Rilegarli in tre volumi tematici non cambia il contenuto: cambia quante volte ti alzi dalla sedia.

```
IL PROBLEMA CHE RISOLVE
  Un'applicazione moderna è centinaia di moduli. Servirli uno per
  uno significa centinaia di richieste HTTP, ciascuna con la sua
  latenza. Su una connessione mobile a 100 ms di round-trip, anche
  con HTTP/2, la differenza è visibile.

COSA FA UN BUNDLER, IN QUATTRO PASSI
  1. RISOLVE  segue gli import e costruisce il grafo delle dipendenze
  2. TRASFORMA  TypeScript, JSX e CSS moderno diventano codice che
     il browser capisce
  3. UNISCE E DIVIDE  raggruppa i moduli in pochi file, separando
     ciò che non serve subito (code splitting)
  4. OTTIMIZZA  elimina il codice non usato (tree shaking), minifica,
     e aggiunge un'IMPRONTA al nome per poter memorizzare in cache
     per sempre

⚠ Il bundler NON è più necessario in sviluppo — i browser capiscono
  i moduli ES nativamente, ed è su questo che si basa la velocità di
  Vite. Resta indispensabile per la PRODUZIONE.
```

---

## A2. Vite: sviluppo e build sono due cose diverse

```
IN SVILUPPO Vite NON impacchetta nulla: serve i moduli ES nativi al
browser, e trasforma solo il file richiesto, quando viene richiesto.
  → l'avvio è istantaneo anche su un progetto grande
  → una modifica aggiorna solo quel modulo (HMR), senza ricaricare

IN BUILD Vite usa Rollup e impacchetta davvero: bundle, divisione,
tree shaking, minificazione, impronte nei nomi.

⚠ SONO DUE PIPELINE DIVERSE, e questo produce la classe di bug più
  fastidiosa: "funziona in sviluppo, non in produzione".
  Le cause tipiche: un import case-sensitive che il filesystem di
  Windows perdona, una dipendenza che in sviluppo viene pre-bundle e
  in build no, un side effect eliminato dal tree shaking.
  ➜ `pnpm build && pnpm preview` va eseguito PRIMA di ogni push, non
    solo prima del rilascio.
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },

  build: {
    // Il target decide quanto codice viene trasformato: più alto è,
    // meno polyfill e meno byte. 'baseline-widely-available' è il
    // predefinito di Vite 6 ed è una scelta sensata.
    target: 'baseline-widely-available',
    sourcemap: true, // ⚠ generati ma NON pubblicati: vedi B5
    rollupOptions: {
      output: {
        // Le impronte nel nome permettono la cache immutabile
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash][extname]',
      },
    },
  },

  server: {
    proxy: {
      // In sviluppo l'API è su un'altra porta: il proxy evita CORS e
      // fa sì che il codice usi lo stesso percorso relativo che
      // userà in produzione
      '/api': { target: 'http://localhost:3001', changeOrigin: true },
    },
  },
})
```

---

## A3. Il gestore di pacchetti e il lockfile

```
IL LOCKFILE È IL FILE PIÙ IMPORTANTE DEL PROGETTO DOPO IL CODICE.
`package.json` dice "voglio React 19.x"; il lockfile dice "19.1.4,
con queste 847 dipendenze transitive a queste versioni esatte".
Senza, la build di oggi non è quella di ieri.

  ✅ SEMPRE committato
  ✅ in CI: `pnpm install --frozen-lockfile` — fallisce se il
     lockfile non combacia con package.json, invece di aggiornarlo
     silenziosamente
  ❌ mai rigenerato "per risolvere un conflitto": si risolve il
     conflitto su package.json e si rilancia l'installazione
```

```
PERCHÉ pnpm  npm e yarn copiano ogni pacchetto in ogni progetto.
pnpm tiene un archivio unico e crea collegamenti: meno spazio, meno
tempo, e — la parte che conta di più — una struttura RIGOROSA di
node_modules.
  Con npm, un pacchetto può importare una dipendenza che non ha
  dichiarato, perché è finita nella cartella per caso (hoisting).
  Il codice funziona finché quella dipendenza non sparisce.
  pnpm lo impedisce: si importa solo ciò che si dichiara.
```

```json
{
  "packageManager": "pnpm@10.6.1",
  "engines": { "node": ">=22.11" },
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "lint": "eslint . --max-warnings 0",
    "format": "prettier --write .",
    "test": "vitest run",
    "verifica": "pnpm lint && pnpm build && pnpm test"
  }
}
```

```
⚠ `packageManager` con la versione esatta (Corepack) evita che uno
  sviluppatore con pnpm 9 e uno con pnpm 10 producano lockfile
  diversi. `engines` fa fallire l'installazione su una versione di
  Node sbagliata, invece di produrre errori incomprensibili più tardi.
```

---

## A4. Lint e formattazione: due strumenti, due compiti

```
SONO COSE DIVERSE, E CONFONDERLE PRODUCE LITIGI INUTILI
  PRETTIER  formatta: virgolette, virgole, a capo, indentazione.
    Non ha opinioni sul codice, solo sull'aspetto. Nessuna
    discussione: si configura una volta e non se ne parla più.
  ESLINT    trova problemi: variabili non usate, `await` dimenticati,
    hook chiamati condizionalmente, promesse non gestite.

⚠ Le regole di ESLint sulla FORMATTAZIONE sono deprecate: si
  disattivano tutte e si lascia il compito a Prettier. Altrimenti i
  due strumenti si contraddicono e il file cambia a ogni salvataggio.
```

```javascript
// eslint.config.js — flat config
import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import prettier from 'eslint-config-prettier'

export default tseslint.config(
  js.configs.recommended,
  // typeChecked usa il compilatore: trova promesse non attese e
  // confronti impossibili, che le regole sintattiche non vedono
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      // Le tre regole che prendono i bug più frequenti
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },
  // ⚠ Per ULTIMO: disattiva le regole che confliggono con Prettier
  prettier,
)
```

```
DOVE VANNO ESEGUITI
  · nell'editor, mentre si scrive — il ciclo più corto possibile
  · in un hook pre-commit sui SOLI file modificati (lint-staged):
    veloce, e impedisce di committare codice non formattato
  · in CI su TUTTO, con `--max-warnings 0`: l'hook si può saltare
    con `--no-verify`, la CI no
```

---

## A5. La prima pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push: { branches: [main] }
  pull_request:

# Una pull request aggiornata annulla l'esecuzione precedente:
# risparmia minuti e non lascia risultati obsoleti
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verifica:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: '.nvmrc'
          cache: 'pnpm'

      # --ignore-scripts: i postinstall non girano in CI, dove ci
      # sono i segreti (vedi tutorial_14 §B6)
      - run: pnpm install --frozen-lockfile --ignore-scripts

      # L'ordine è per COSTO CRESCENTE: un errore di battitura non
      # deve costare cinque minuti di build
      - run: pnpm lint
      - run: pnpm exec tsc --noEmit
      - run: pnpm test
      - run: pnpm build

      - uses: actions/upload-artifact@v4
        with: { name: dist, path: dist/, retention-days: 7 }
```

```
LE QUATTRO PROPRIETÀ DI UNA PIPELINE CHE SI USA DAVVERO
  1. VELOCE  sotto i cinque minuti per una pull request. Oltre, si
     smette di aspettarla e si fa il merge alla cieca.
  2. AFFIDABILE  un rosso significa sempre un problema reale. Un
     test instabile insegna a ignorare i fallimenti.
  3. LEGGIBILE  quando fallisce, il nome del passo e l'output devono
     bastare, senza scaricare i log.
  4. UGUALE IN LOCALE  `pnpm verifica` esegue le stesse cose: si
     scopre il problema prima di aprire la pull request.
```

---

# Parte B — Comprensione Profonda

---

## B1. Code splitting: cosa dividere e cosa no

```
IL PRINCIPIO: l'utente scarica ciò che serve ORA. Il pannello di
amministrazione non deve pesare sulla pagina di accesso.

I TRE PUNTI DI DIVISIONE, IN ORDINE DI RESA
  1. PER ROTTA — quasi sempre il più efficace: ogni pagina è un
     pezzo separato, caricato quando ci si arriva
  2. PER COMPONENTE PESANTE — un editor di testo ricco, un grafico,
     una mappa: si caricano quando l'utente li apre davvero
  3. PER DIPENDENZA GRANDE E RARA — una libreria di esportazione PDF
     usata da un pulsante in fondo a una pagina
```

```tsx
import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router'

// L'import dinamico è il punto di divisione: Rollup crea un pezzo
// separato per ognuno
const Dashboard = lazy(() => import('./pagine/Dashboard.js'))
const Amministrazione = lazy(() => import('./pagine/Amministrazione.js'))

export const router = createBrowserRouter([
  {
    path: '/',
    // ⚠ Il fallback non deve essere uno spinner nudo: uno scheletro
    //    con la forma del contenuto evita lo spostamento del layout
    element: (
      <Suspense fallback={<ScheletroPagina />}>
        <Dashboard />
      </Suspense>
    ),
  },
  { path: '/admin', element: <Suspense fallback={<ScheletroPagina />}><Amministrazione /></Suspense> },
])
```

```
COSA NON DIVIDERE
  ❌ i componenti piccoli: ogni pezzo è una richiesta in più, e sotto
     i 10-15 kB il costo della richiesta supera il risparmio
  ❌ ciò che serve SUBITO: dividere il percorso critico lo rallenta
  ❌ le dipendenze condivise da tutte le rotte: finirebbero
     duplicate, oppure in un pezzo che si carica comunque sempre

⚠ IL WATERFALL DEI PEZZI: se il pezzo A importa B che importa C, il
  browser li scopre uno dopo l'altro e paga tre round-trip in serie.
  Si risolve con `modulepreload` sui pezzi noti in anticipo — Vite
  li genera automaticamente per le rotte dichiarate.
```

---

## B2. Tree shaking e i side effect

```
IL TREE SHAKING elimina il codice esportato ma mai importato. Funziona
solo con i moduli ES statici: `require()` e gli import dinamici con
percorso variabile non sono analizzabili.
```

```typescript
// ❌ L'import di default trascina l'intera libreria
// import _ from 'lodash'
// const unico = _.uniq(elenco)           → ~70 kB

// ✅ L'import nominale da un pacchetto con moduli ES
import { uniq } from 'lodash-es'         //  → ~2 kB

// ✅✅ E spesso non serve la libreria
const unico = [...new Set(elenco)]       //  → 0 kB
```

```json
// package.json — `sideEffects` dice al bundler che eliminare un
// modulo non importato è sicuro. Senza, il bundler è prudente e
// tiene tutto.
{
  "sideEffects": ["*.css", "./src/polyfill.ts"]
}
```

```
⚠ `"sideEffects": false` DICHIARATO PER SBAGLIO è un bug sottile: se
  un modulo registra qualcosa all'import (un web component, un
  polyfill, un plugin), il bundler lo elimina e il codice si rompe
  solo in produzione. Si elencano le eccezioni, non si dichiara falso
  a occhi chiusi.

COSA IMPEDISCE IL TREE SHAKING, IN PRATICA
  · pacchetti pubblicati solo in CommonJS (niente campo `module` o
    `exports` con `import`)
  · le classi con metodi non usati: il bundler non elimina un metodo,
    solo un modulo o una funzione
  · gli effetti al livello superiore di un modulo (una chiamata, un
    `window.x = …`): rendono il modulo non eliminabile
```

---

## B3. Il budget di dimensione, e come si fa rispettare

```
UN BUDGET NON MISURATO NON ESISTE. La dimensione cresce di poche
decine di kilobyte per rilascio, e nessuno se ne accorge finché il
sito non è lento — a quel punto la causa è distribuita su cento
commit e nessuno sa da dove ricominciare.

UN PUNTO DI PARTENZA RAGIONEVOLE (compressi, brotli)
  JavaScript del percorso critico   ≤ 170 kB
  CSS del percorso critico          ≤  50 kB
  ogni pezzo per rotta              ≤ 100 kB
  immagine più grande above the fold ≤ 200 kB
⚠ Sono ordini di grandezza tipici, non una norma: il budget giusto
  dipende dal pubblico e dalla rete su cui gira. Un gestionale
  aziendale su fibra può permettersi di più di un negozio mobile.
```

```yaml
# Il controllo in CI: la pull request fallisce se supera il budget
- name: Budget di dimensione
  run: pnpm exec size-limit
```

```json
// .size-limit.json
[
  {
    "name": "percorso critico",
    "path": "dist/assets/index.*.js",
    "limit": "170 kB",
    "gzip": false,
    "brotli": true
  },
  { "name": "CSS", "path": "dist/assets/*.css", "limit": "50 kB", "brotli": true }
]
```

```
QUANDO IL BUDGET VIENE SUPERATO, IN ORDINE DI RESA
  1. GUARDARE COSA C'È DENTRO
     pnpm exec vite-bundle-visualizer
     Nove volte su dieci la causa è una singola dipendenza pesante
     entrata per una funzione sola.
  2. SOSTITUIRE  moment → date-fns o Temporal · lodash → funzioni
     native · una libreria di icone intera → le sole icone usate
  3. DIVIDERE  spostare la funzionalità in un pezzo caricato su
     richiesta
  4. ALZARE IL BUDGET — con una motivazione scritta nel commit. È
     una scelta legittima; farla senza dirlo non lo è.
```

---

## B4. Variabili d'ambiente: build time e runtime

```
LA DISTINZIONE CHE CAUSA PIÙ CONFUSIONE

  BUILD TIME (frontend)  il valore viene SOSTITUITO nel codice
    durante la build. Cambiarlo richiede una build nuova, e il
    valore è PUBBLICO: sta nel file che il browser scarica.
      VITE_API_URL, NEXT_PUBLIC_*
      ➜ il prefisso è una DICHIARAZIONE che il valore è pubblico,
        non una protezione

  RUNTIME (backend)  il valore è letto dal processo all'avvio.
    Cambiarlo richiede un riavvio, non una build, e resta segreto.
      DATABASE_URL, JWT_SECRET
```

```typescript
// src/configurazione.ts — validata all'avvio, per fallire subito
import { z } from 'zod'

const Schema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_AMBIENTE: z.enum(['sviluppo', 'staging', 'produzione']),
})

const esito = Schema.safeParse(import.meta.env)

if (!esito.success) {
  // Meglio un errore chiaro alla build che un `undefined` che
  // diventa la stringa "undefined" dentro un URL
  throw new Error(`Configurazione non valida: ${esito.error.issues.map((i) => i.path).join(', ')}`)
}

export const configurazione = esito.data
```

```
⚠ IL PROBLEMA DELLA STESSA IMMAGINE IN PIÙ AMBIENTI
  Se l'URL dell'API è inserito a build time, l'artefatto di staging
  e quello di produzione sono DIVERSI: si testa una cosa e se ne
  rilascia un'altra.
  Le due soluzioni:
   · lo stesso dominio in entrambi, con l'API su un percorso
     relativo (/api) — la più semplice, e quasi sempre sufficiente
   · una configurazione servita a runtime: index.html include un
     piccolo `<script>` con i valori, generato dal server all'avvio.
     L'artefatto resta uno solo per tutti gli ambienti.
```

---

## B5. Docker multi-stage e l'immagine minima

```dockerfile
# ── 1. Dipendenze ────────────────────────────────────────────
FROM node:24-alpine AS dipendenze
WORKDIR /app
RUN corepack enable
# Prima SOLO i file che descrivono le dipendenze: se il codice
# cambia ma non le dipendenze, questo strato resta in cache
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts

# ── 2. Build ─────────────────────────────────────────────────
FROM node:24-alpine AS build
WORKDIR /app
RUN corepack enable
COPY --from=dipendenze /app/node_modules ./node_modules
COPY . .
RUN pnpm build
# Le dipendenze di sviluppo escono dall'immagine finale
RUN pnpm prune --prod

# ── 3. Produzione ────────────────────────────────────────────
FROM node:24-alpine AS produzione
WORKDIR /app
ENV NODE_ENV=production

# Utente non privilegiato: un'escalation nel container non dà root
USER node

COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
COPY --from=build --chown=node:node /app/package.json ./

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://localhost:3000/salute/pronto').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "dist/server.js"]
```

```
LE SEI DECISIONI, E IL PERCHÉ
  1. MULTI-STAGE  l'immagine finale non contiene il compilatore, i
     sorgenti né le dipendenze di sviluppo: meno superficie e meno
     peso (spesso da 1,2 GB a 180 MB)
  2. ORDINE DEI COPY  package.json prima del codice: la cache degli
     strati regge fra una build e l'altra
  3. --ignore-scripts  i postinstall non girano
  4. USER node  mai root
  5. HEALTHCHECK  l'orchestratore sa se il processo è pronto
  6. --init  ⚠ `docker run --init`, oppure un ENTRYPOINT che
     propaga i segnali: senza, SIGTERM non arriva a Node e lo
     spegnimento pulito non parte mai (tutorial_10 §B7)

⚠ .dockerignore È OBBLIGATORIO: senza, `COPY . .` porta dentro
  node_modules, .git, .env e i sourcemap. È anche il modo più comune
  di far finire un segreto in un'immagine.
```

```
# .dockerignore
node_modules
.git
.env*
dist
*.map
coverage
test-results
```

```
⚠ I SOURCEMAP: generarli sì, PUBBLICARLI no. Un `.map` accanto al
  bundle espone tutto il codice sorgente. Si caricano sul servizio di
  monitoraggio degli errori (Sentry) e si eliminano dall'artefatto
  pubblico.
```

---

## B6. Cache: nel bundler, in Docker, in CI

```
TRE CACHE DIVERSE, TRE MECCANISMI DIVERSI, E UN SOLO PRINCIPIO:
la chiave della cache deve cambiare esattamente quando cambia il
risultato — mai prima (spreco), mai dopo (risultato sbagliato).

  BUNDLER  Vite mette in cache le dipendenze pre-bundle in
    node_modules/.vite. La chiave è il lockfile.
    ⚠ Quando "funziona solo dopo aver cancellato node_modules", la
      causa è quasi sempre questa cache disallineata.

  DOCKER  ogni istruzione è uno strato; uno strato si riusa se
    l'istruzione e i file che copia non sono cambiati. Da qui
    l'ordine dei COPY.

  CI  `actions/setup-node` con `cache: 'pnpm'` mette in cache
    l'archivio dei pacchetti (chiave: il lockfile). Per la build,
    una cache esplicita con la chiave giusta.
```

```yaml
# La cache della build in CI: chiave su lockfile + sorgenti
- uses: actions/cache@v4
  with:
    path: |
      node_modules/.vite
      .turbo
    key: build-${{ hashFiles('pnpm-lock.yaml') }}-${{ hashFiles('src/**') }}
    # La chiave di ripiego riusa una cache parziale invece di
    # ripartire da zero
    restore-keys: build-${{ hashFiles('pnpm-lock.yaml') }}-
```

```
⚠ L'ERRORE PIÙ COSTOSO: una chiave troppo generica (per esempio solo
  il nome del ramo). La cache viene riusata quando non dovrebbe, e si
  ottiene una build con artefatti vecchi — che è peggio di nessuna
  cache, perché il risultato è sbagliato e sembra giusto.
```

---

## B7. Strategie di rilascio e rollback

```
ROLLING  le istanze vengono sostituite poche alla volta.
  ✅ nessun costo aggiuntivo, è il predefinito di quasi tutti gli
     orchestratori
  ⚠ per qualche minuto convivono due versioni: lo schema del
     database e le API devono essere compatibili con ENTRAMBE

BLUE-GREEN  due ambienti completi; si sposta il traffico da uno
  all'altro in un istante.
  ✅ rollback immediato: si rimette il traffico sul vecchio
  ❌ costo doppio durante il rilascio, e il database resta condiviso
     (quindi le migrazioni vanno comunque compatibili)

CANARY  il 5% del traffico va alla versione nuova; se le metriche
  reggono, si sale.
  ✅ l'unica che limita il danno di un problema che i test non hanno
     visto
  ❌ richiede metriche per versione e un instradamento fine

⚠ QUALUNQUE STRATEGIA, LO SPEGNIMENTO PULITO È OBBLIGATORIO:
  SIGTERM → smettere di accettare, finire le richieste in corso,
  chiudere il pool, uscire. Senza, ogni rilascio interrompe le
  richieste che erano a metà.
```

```yaml
# Il rollback non deve richiedere una build: si ridistribuisce un
# artefatto già esistente
- name: Rollback alla versione precedente
  run: |
    PRECEDENTE=$(gh release list --limit 2 --json tagName -q '.[1].tagName')
    gh workflow run deploy.yml -f versione="$PRECEDENTE"
```

```
LE TRE DOMANDE DA RISPONDERE PRIMA DEL PRIMO RILASCIO
  1. Quanto ci metto a tornare indietro? Se la risposta è "rifaccio
     la build", non è un rollback: è un altro rilascio, con altri
     rischi.
  2. Il rollback del CODICE basta? Se la migrazione del database non
     è reversibile, no — e va saputo prima (vedi D3).
  3. Chi decide e chi esegue, alle tre di notte? Scritto, non
     sottinteso.
```

---

## B8. CDN, impronte e intestazioni di cache

```
LE IMPRONTE NEI NOMI RENDONO POSSIBILE LA CACHE PERFETTA
  app.a3f9c2.js  → il contenuto è cambiato? il nome cambia.
  Quindi quel file, con QUEL nome, non cambierà mai:

    Cache-Control: public, max-age=31536000, immutable

  L'unico file senza impronta è index.html, che referenzia gli altri:

    Cache-Control: no-cache

  `no-cache` NON significa "non memorizzare": significa "memorizza,
  ma chiedi sempre se è cambiato". Con l'ETag, la risposta è un 304
  senza corpo — pochi byte per sapere che è ancora valido.
```

```
   IL RISULTATO, A OGNI VISITA SUCCESSIVA
   index.html      → 304, ~200 byte
   app.a3f9c2.js   → dalla cache, 0 byte, 0 ms
   (dopo un rilascio: index.html cambia, punta a app.b1e4d8.js, e
    SOLO quel file viene riscaricato)
```

```
GLI ALTRI PUNTI CHE CONTANO
  · COMPRESSIONE  brotli per i testi (JS, CSS, HTML, JSON), circa il
    15-20% meglio di gzip. Le immagini e i font già compressi non si
    ricomprimono.
  · IMMAGINI  AVIF con ripiego WebP e JPEG, dimensioni multiple con
    `srcset`, `width` e `height` sempre dichiarati per non spostare
    il layout.
  · FONT  `font-display: swap`, `preload` sul font del percorso
    critico, sottoinsieme dei caratteri effettivamente usati.
  · L'INVALIDAZIONE DELLA CDN dopo il rilascio riguarda solo
    index.html e gli altri file senza impronta: gli asset con
    impronta non vanno mai invalidati, ed è il punto.
```

---

## B9. Monorepo: quando conviene e cosa costa

```
UN MONOREPO È UN REPOSITORY CON PIÙ PACCHETTI CHE SI RIFERISCONO
FRA LORO — non "tutto il codice dell'azienda in un posto".

  CONVIENE QUANDO
   ✅ più applicazioni condividono codice (tipi, componenti, client
      dell'API) e quel codice cambia spesso
   ✅ una modifica deve attraversare più pacchetti nello stesso
      commit: un cambio di API e i suoi consumatori insieme
   ✅ si vuole una versione sola di TypeScript, ESLint e delle
      dipendenze comuni

  NON CONVIENE QUANDO
   ❌ i progetti sono indipendenti e hanno cadenze di rilascio
      diverse
   ❌ team diversi con permessi diversi
   ❌ è solo per "avere tutto insieme": si paga la complessità senza
      il beneficio
```

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

```json
// turbo.json — la parte che rende il monorepo sostenibile: si
// ricostruisce solo ciò che è cambiato, e il resto viene dalla cache
{
  "tasks": {
    "build": {
      // ^build: prima le dipendenze, poi il pacchetto
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "test": { "dependsOn": ["^build"] },
    "lint": {}
  }
}
```

```
⚠ IL COSTO REALE DI UN MONOREPO
  · la CI deve capire COSA è cambiato, altrimenti ogni push ricostruisce
    tutto e i tempi diventano insostenibili
  · i confini fra pacchetti vanno fatti rispettare, altrimenti si
    ottiene un unico blocco con più cartelle
  · gli strumenti (Turborepo, Nx) sono una dipendenza in più da
    aggiornare e capire
  ➜ per due applicazioni che condividono tre tipi, un pacchetto
    pubblicato o una cartella condivisa costano molto meno.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Ridurre un bundle da 1,2 MB

**Obiettivo:** trovare cosa pesa e ridurre il percorso critico sotto i 200 kB compressi.

```
# LA SITUAZIONE
#   pnpm build
#   dist/assets/index.a3f9c2.js   1.243,12 kB │ brotli: 387,44 kB
#
#   Il primo passo NON è indovinare: è guardare.
#   pnpm exec vite-bundle-visualizer
```

```
# COSA MOSTRA LA MAPPA
#   moment + locales      287 kB  ← tutte le lingue del mondo, e ne
#                                   serve una
#   lodash (completo)      71 kB  ← usato per uniq e debounce
#   @mui/icons-material   198 kB  ← importate 12 icone su 5.000
#   chart.js              164 kB  ← una sola pagina lo usa
#   react + react-dom     142 kB  ← necessario
#   il nostro codice      181 kB
```

```typescript
// CORREZIONE 1 — moment (287 kB) → date-fns con import nominali (4 kB)
// import moment from 'moment'
// moment(data).format('DD/MM/YYYY')
import { format } from 'date-fns'
import { it } from 'date-fns/locale'

export const formattaData = (data: Date) => format(data, 'dd/MM/yyyy', { locale: it })

// CORREZIONE 2 — lodash (71 kB) → niente (0 kB)
// import _ from 'lodash'
export const unici = <T,>(elenco: T[]) => [...new Set(elenco)]

export function ritarda<A extends unknown[]>(fn: (...a: A) => void, ms: number) {
  let timer: ReturnType<typeof setTimeout>
  return (...argomenti: A) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...argomenti), ms)
  }
}
```

```typescript
// CORREZIONE 3 — le icone (198 kB → 3 kB): import nominali dal
// percorso specifico, non dal barrel file
// import { Save, Delete } from '@mui/icons-material'   ← trascina tutto
import Save from '@mui/icons-material/Save'
import Delete from '@mui/icons-material/Delete'
```

```tsx
// CORREZIONE 4 — chart.js (164 kB) esce dal percorso critico e
// arriva solo su chi apre la pagina dei rapporti
import { lazy, Suspense } from 'react'

const GraficoFatturato = lazy(() => import('./GraficoFatturato.js'))

export function PaginaRapporti() {
  return (
    <Suspense fallback={<ScheletroGrafico />}>
      <GraficoFatturato />
    </Suspense>
  )
}
```

```
# IL RISULTATO
#   index.b1e4d8.js      312,40 kB │ brotli:  98,12 kB   ← percorso critico
#   grafico.c2f7a1.js    171,08 kB │ brotli:  52,30 kB   ← su richiesta
#   Da 387 kB a 98 kB sul percorso critico: circa quattro volte meno.
#
# E IL PASSO CHE IMPEDISCE IL RITORNO — senza questo, fra sei mesi
# si è di nuovo a 1,2 MB:
#   .size-limit.json con limit "110 kB" e size-limit in CI
#
# ⚠ La verifica va fatta sul valore COMPRESSO (brotli), non sul
#   file non compresso: è quello che l'utente scarica davvero.
```

---

### Esercizio 2 — Da una pipeline sequenziale a una parallela

**Obiettivo:** una CI di 18 minuti che blocca ogni pull request. Portarla sotto i 6.

```yaml
# LA PIPELINE DA CORREGGERE — un solo job, tutto in fila
jobs:
  tutto:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4     # nessuna cache
      - run: npm install                # 3 min, e senza lockfile bloccato
      - run: npm run build              # 4 min
      - run: npm run lint               # 1 min
      - run: npm run test               # 3 min
      - run: npx playwright install     # 2 min ogni volta
      - run: npm run test:e2e           # 5 min
```

```
# LA DIAGNOSI — cinque problemi
# 1. NESSUNA CACHE: dipendenze e browser riscaricati a ogni push
# 2. `npm install` invece di `ci --frozen-lockfile`: lento, e può
#    installare versioni diverse da quelle bloccate
# 3. ORDINE SBAGLIATO: la build (4 min) precede il lint (1 min). Un
#    errore di battitura costa quattro minuti prima di essere visto.
# 4. TUTTO SEQUENZIALE: lint, tipi e test unitari sono indipendenti
# 5. GLI E2E SU UNA SOLA MACCHINA: sono partizionabili
```

```yaml
# LA SOLUZIONE
name: CI
on: [push, pull_request]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # 1. Le dipendenze una volta sola, riusate da tutti i job
  prepara:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: '.nvmrc', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile --ignore-scripts

  # 2. I tre controlli veloci IN PARALLELO: il tempo è quello del
  #    più lento, non la somma
  controlli:
    needs: prepara
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        comando: [lint, 'exec tsc --noEmit', test]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: '.nvmrc', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile --ignore-scripts
      - run: pnpm ${{ matrix.comando }}

  # 3. La build solo se i controlli passano, e l'artefatto si riusa
  build:
    needs: controlli
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: '.nvmrc', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile --ignore-scripts
      - run: pnpm build
      - run: pnpm exec size-limit
      - uses: actions/upload-artifact@v4
        with: { name: dist, path: dist/ }

  # 4. Gli E2E su quattro macchine, con i browser in cache
  e2e:
    needs: build
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: { parte: [1, 2, 3, 4] }
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: '.nvmrc', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - uses: actions/download-artifact@v4
        with: { name: dist, path: dist/ }
      - uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-${{ hashFiles('pnpm-lock.yaml') }}
      - run: pnpm exec playwright install --with-deps chromium
      - run: pnpm exec playwright test --shard=${{ matrix.parte }}/4
      - uses: actions/upload-artifact@v4
        if: failure()
        with: { name: traccia-${{ matrix.parte }}, path: test-results/ }
```

```
# IL RISULTATO
#   prima:  18 min in fila
#   dopo:   ~1 min (prepara) + ~2 min (controlli in parallelo)
#           + ~2 min (build) + ~2 min (E2E su 4 macchine) ≈ 5-6 min
#
# ⚠ `fail-fast: false` sulle matrici: se una parte fallisce, le
#   altre continuano. Vedere tutti i fallimenti insieme evita tre
#   giri di correzione.
```

---

### Esercizio 3 — Un'immagine Docker da 1,4 GB a meno di 200 MB

**Obiettivo:** ridurre l'immagine, e correggere i problemi di sicurezza che si scoprono strada facendo.

```dockerfile
# IL DOCKERFILE DA CORREGGERE
FROM node:24
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
ENV DATABASE_URL=postgres://utente:password@db:5432/app
EXPOSE 3000
CMD npm start
```

```
# LA DIAGNOSI — sette problemi
# 1. `node:24` completo (~1,1 GB) invece di alpine (~130 MB)
# 2. `COPY . .` PRIMA di install: ogni modifica al codice invalida
#    la cache delle dipendenze
# 3. Nessun .dockerignore: dentro finiscono node_modules, .git, .env
# 4. Nessun multi-stage: compilatore, sorgenti e dipendenze di
#    sviluppo restano nell'immagine finale
# 5. SEGRETO NELL'IMMAGINE: `ENV DATABASE_URL=…` con la password si
#    legge con `docker history`. È il problema più grave.
# 6. Gira come ROOT
# 7. `CMD npm start` avvia npm che avvia node: npm diventa il
#    processo 1 e NON propaga SIGTERM. Nessuno spegnimento pulito.
```

```dockerfile
# LA SOLUZIONE
FROM node:24-alpine AS dipendenze
WORKDIR /app
RUN corepack enable
# Solo i file delle dipendenze: lo strato resta in cache finché il
# lockfile non cambia
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --ignore-scripts

FROM node:24-alpine AS build
WORKDIR /app
RUN corepack enable
COPY --from=dipendenze /app/node_modules ./node_modules
COPY . .
RUN pnpm build && pnpm prune --prod

FROM node:24-alpine AS produzione
WORKDIR /app
ENV NODE_ENV=production
USER node

COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
COPY --from=build --chown=node:node /app/package.json ./

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://localhost:3000/salute/pronto').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# node direttamente, in forma exec: è il processo 1 e riceve SIGTERM
CMD ["node", "dist/server.js"]
```

```
# .dockerignore
node_modules
.git
.env*
dist
*.map
coverage
```

```
# LA VERIFICA
#   docker build -t app:prova .
#   docker images app:prova                    → ~180 MB
#   docker history app:prova | grep -i pass    → nessun risultato
#   docker run --rm --entrypoint id app:prova  → uid=1000(node)
#   docker run --rm --entrypoint sh app:prova -c "ls /app"
#     → solo dist, node_modules, package.json
#
#   # Lo spegnimento pulito:
#   docker run --init -d --name p app:prova
#   docker stop p     → nei log deve comparire "spegnimento avviato"
#
#   # E la seconda build, dopo una modifica al solo codice:
#   deve riusare lo strato delle dipendenze (CACHED)
#
# ⚠ Il segreto: DATABASE_URL si passa a RUNTIME (`docker run -e`, o
#   il gestore di segreti della piattaforma), mai nel Dockerfile. E
#   la password che era nell'immagine va considerata compromessa:
#   si RUOTA, non si cancella soltanto.
```

---

## C2. Mini-progetto: pipeline CI/CD completa

L'esercizio chiave del modulo: lint, controllo dei tipi, test, build e deploy automatico a ogni push.

```
LA FORMA DELLA PIPELINE
  su PULL REQUEST   controlli veloci in parallelo → build → budget →
    E2E partizionati → anteprima su un ambiente effimero
  su MAIN           tutto quanto sopra → deploy su staging → test di
    fumo → approvazione umana → deploy in produzione → verifica
  su TAG            rilascio versionato, con artefatto firmato e note
    generate dai commit

I QUATTRO PRINCIPI
  1. UN SOLO ARTEFATTO attraversa tutti gli ambienti. Ricostruire
     per la produzione significa rilasciare qualcosa che non è stato
     testato.
  2. NESSUN SEGRETO NELLA BUILD: la configurazione entra a runtime.
  3. IL DEPLOY IN PRODUZIONE HA UN'APPROVAZIONE, e l'ambiente ha
     revisori obbligatori.
  4. IL ROLLBACK NON RICOSTRUISCE: ridistribuisce l'artefatto
     precedente, e deve richiedere meno di un minuto.
```

```yaml
# .github/workflows/deploy.yml (estratto — la parte che porta le decisioni)
name: Deploy
on:
  push: { branches: [main] }
  workflow_dispatch:
    inputs:
      versione: { description: 'Tag da ridistribuire (rollback)', required: false }

# Il minimo indispensabile, esplicito: il predefinito di GitHub è
# più largo di quanto serva
permissions:
  contents: read
  id-token: write   # OIDC verso il cloud: nessuna chiave statica

jobs:
  staging:
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: dist }
      - run: ./scripts/deploy.sh staging
      # Il test di fumo: se il servizio non risponde, il deploy in
      # produzione non parte nemmeno
      - run: ./scripts/fumo.sh https://staging.esempio.it

  produzione:
    needs: staging
    # L'ambiente con revisori obbligatori: la pipeline si FERMA qui
    # e aspetta un'approvazione
    environment:
      name: produzione
      url: https://esempio.it
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: dist }
      - run: ./scripts/deploy.sh produzione
      - run: ./scripts/fumo.sh https://esempio.it
      # Se il fumo fallisce, si torna indietro da soli
      - if: failure()
        run: ./scripts/rollback.sh produzione
```

```
# LA VERIFICA, IN ORDINE
# 1. RIPRODUCIBILITÀ  due build dallo stesso commit producono
#    artefatti con lo stesso hash (vedi D1)
# 2. LA PIPELINE FALLISCE QUANDO DEVE  introduci un errore di tipo,
#    un test rotto e un bundle oltre il budget: tre rossi distinti
# 3. NESSUN SEGRETO NELL'ARTEFATTO  cerca le chiavi nei file di dist
#    e in `docker history`: zero risultati
# 4. LO STESSO ARTEFATTO IN STAGING E PRODUZIONE  confronta gli hash
# 5. IL ROLLBACK  eseguilo davvero, e CRONOMETRALO: deve stare sotto
#    il minuto e non richiedere una build
# 6. LO SPEGNIMENTO PULITO  durante il rilascio, una richiesta lenta
#    in corso deve completarsi
# 7. TEMPI  pull request sotto i sei minuti
# 8. LE MIGRAZIONI  applicate prima del codice nuovo, e compatibili
#    con quello vecchio (D3)
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Build riproducibili

```
UNA BUILD È RIPRODUCIBILE SE LO STESSO COMMIT PRODUCE LO STESSO
ARTEFATTO, BIT PER BIT. Non è pedanteria: è ciò che permette di
rispondere alla domanda "l'artefatto in produzione corrisponde a
questo commit?" — e senza quella risposta, la firma degli artefatti
e l'SBOM non valgono nulla.

COSA ROMPE LA RIPRODUCIBILITÀ
  · versioni non bloccate (lockfile assente o non rispettato)
  · timestamp incorporati negli artefatti
  · l'ordine di iterazione di una directory, che dipende dal
    filesystem
  · valori casuali o date usate nella build
  · la versione di Node, di pnpm o del sistema operativo

LE CONTROMISURE
  · lockfile + `--frozen-lockfile` + `packageManager` fissato
  · `SOURCE_DATE_EPOCH` per i timestamp deterministici
  · build dentro un container con un'immagine fissata al digest
  · confrontare gli hash: `sha256sum dist/**` da due build
```

---

## D2. Feature flag: separare il rilascio dall'attivazione

```
IL RILASCIO (il codice va in produzione) e l'ATTIVAZIONE (gli utenti
lo vedono) diventano due decisioni distinte. Cambia tre cose:
  · si integra spesso su main, senza rami di funzionalità lunghi
  · si attiva per pochi utenti prima, e si spegne in un secondo se
    qualcosa non va — senza un rilascio
  · un problema si risolve spegnendo un interruttore, non tornando
    indietro con il deploy
```

```typescript
// L'interfaccia minima: la valutazione dipende dal CONTESTO, e il
// valore predefinito è sempre lo stato SICURO
export type Contesto = { idUtente: string; ruoli: readonly string[] }

export function attiva(nome: string, contesto: Contesto): boolean {
  const regola = regole.get(nome)
  if (!regola) return false // sconosciuto = spento

  if (regola.utenti?.includes(contesto.idUtente)) return true
  if (regola.ruoli?.some((r) => contesto.ruoli.includes(r))) return true

  // La percentuale deve essere STABILE per utente: con Math.random
  // un utente vedrebbe la funzionalità apparire e sparire a ogni
  // ricaricamento
  if (regola.percentuale) {
    return improntaStabile(`${nome}:${contesto.idUtente}`) % 100 < regola.percentuale
  }
  return false
}
```

```
⚠ I FLAG SONO DEBITO TECNICO A TERMINE. Ogni flag raddoppia i
  percorsi da testare, e dieci flag sono mille combinazioni. Ogni
  flag nasce con una DATA DI RIMOZIONE, e un flag attivo al 100% da
  due mesi va tolto insieme al codice del ramo morto.
```

---

## D3. Migrazioni del database nel deploy

```
IL PROBLEMA: durante un rilascio rolling convivono per qualche minuto
il codice VECCHIO e quello NUOVO, sullo STESSO database.

  migrazione PRIMA del codice → il codice vecchio deve funzionare
    con lo schema nuovo
  migrazione DOPO il codice   → il codice nuovo deve funzionare con
    lo schema vecchio

  ➜ In entrambi i casi serve la COMPATIBILITÀ IN AVANTI, ed è per
    questo che si usa expand-contract (tutorial_12 §B8): il campo
    nuovo si aggiunge accanto al vecchio, si migra, e solo dopo due
    rilasci si rimuove il vecchio.
```

```
LA SEQUENZA CHE FUNZIONA
  1. migrazione ADDITIVA (colonne nullable, tabelle nuove, indici
     con CONCURRENTLY)
  2. deploy del codice che scrive su entrambi e legge dal nuovo
  3. riempimento a lotti dei dati esistenti
  4. deploy del codice che usa solo il nuovo
  5. migrazione DISTRUTTIVA (rimozione del vecchio)

⚠ IL ROLLBACK DEL CODICE NON ANNULLA LA MIGRAZIONE. Se il passo 5 è
  già stato eseguito, tornare al codice del passo 2 lo fa fallire.
  La regola: la migrazione distruttiva si esegue solo quando il
  rollback a quella versione non è più previsto — cioè dopo che la
  nuova è stata in produzione abbastanza da fidarsi.

DOVE ESEGUIRLE  in un job dedicato PRIMA del deploy, non all'avvio
dell'applicazione: se le istanze sono dieci, dieci processi
proverebbero a migrare insieme. Se il framework lo fa all'avvio,
serve un lock (Prisma lo prende da solo).
```

---

## D4. Osservabilità del rilascio

```
UN DEPLOY SENZA OSSERVAZIONE È UNA SCOMMESSA. Le quattro cose da
guardare nei dieci minuti successivi, confrontate con il PRIMA:

  1. TASSO DI ERRORE  5xx per endpoint. Un salto è il segnale più
     immediato.
  2. LATENZA  p95 e p99, non la media: una media stabile può
     nascondere che il 5% degli utenti ha raddoppiato i tempi.
  3. THROUGHPUT  un CALO è sospetto quanto un picco: significa che
     qualcuno non riesce più ad arrivare.
  4. SATURAZIONE  CPU, memoria, connessioni al database. Una
     perdita di memoria introdotta ora si vede in mezz'ora, non
     subito.
```

```typescript
// Marcare la versione su ogni traccia e ogni log: senza, non si può
// confrontare il prima e il dopo
export const risorsa = {
  'service.name': 'api-esempio',
  'service.version': process.env['VERSIONE_APP'] ?? 'sconosciuta',
  'deployment.environment': process.env['AMBIENTE'] ?? 'sviluppo',
}
```

```
E IL PASSO CHE CHIUDE IL CERCHIO: annotare il deploy sui grafici.
Quando qualcuno guarda un picco di errori delle 14:32, la riga
verticale "rilascio v2.4.1 alle 14:30" è la diagnosi già fatta.
Ogni strumento di monitoraggio ha un'API per le annotazioni, e
aggiungerla alla pipeline costa tre righe.
```

---

## D5. Sicurezza della catena di build

```
LA CI HA I SEGRETI DI PRODUZIONE E SCRIVE NEGLI ARTEFATTI CHE
VERRANNO ESEGUITI: è l'obiettivo più redditizio che esista, e quasi
nessuno la sorveglia come sorveglia il server.

  · AZIONI FISSATE AL COMMIT, non al tag: un tag si può spostare
      uses: actions/checkout@8ade135…   ✅
      uses: actions/checkout@v4          ❌
  · PERMESSI MINIMI ed espliciti: `contents: read` come predefinito
    del workflow, e i permessi in più solo sul job che li richiede
  · ⚠ `pull_request_target` esegue codice del fork CON i segreti:
    una pull request esterna può esfiltrarli. Si usa `pull_request`.
  · OIDC verso il cloud invece delle chiavi statiche: nessun segreto
    di lunga durata da rubare
  · `--ignore-scripts` in installazione, e `enable-pre-post-scripts=false`
  · ARTEFATTI FIRMATI (Sigstore) e verificati prima del deploy
  · SBOM a ogni rilascio: quando esce una vulnerabilità, "ce
    l'abbiamo?" ha una risposta in un minuto
  · scansione dei segreti (gitleaks) su ogni push
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
BUILD TOOLS E DEPLOY — Mappa dei concetti

IL BUNDLER
├── risolve · trasforma · unisce e divide · ottimizza
├── Vite: moduli ES nativi in sviluppo, Rollup in build
├── sono DUE pipeline: "funziona in dev, non in prod" nasce qui
└── `pnpm build && pnpm preview` prima di ogni push

DIMENSIONE
├── code splitting: per rotta, per componente pesante, per
│     dipendenza grande e rara — non sotto i 10-15 kB
├── tree shaking: import nominali, moduli ES, `sideEffects` corretto
├── budget in CI (size-limit) sul valore COMPRESSO
└── quando si supera: guardare la mappa, sostituire, dividere, o
      alzare il budget con una motivazione scritta

DIPENDENZE
├── il lockfile è il file più importante dopo il codice
├── `--frozen-lockfile` in CI · `packageManager` fissato · `engines`
├── pnpm: archivio unico, e nessun import non dichiarato
└── Prettier formatta, ESLint trova problemi: due compiti distinti

AMBIENTE
├── build time (frontend, PUBBLICO) contro runtime (backend, segreto)
├── il prefisso VITE_/NEXT_PUBLIC_ è una dichiarazione, non una difesa
└── un solo artefatto per tutti gli ambienti: configurazione a runtime

DOCKER
├── multi-stage · COPY del lockfile prima del codice · prune --prod
├── USER node · HEALTHCHECK · --init per i segnali
├── .dockerignore obbligatorio · sourcemap generati, non pubblicati
└── mai un segreto in un ENV del Dockerfile: si legge con history

PIPELINE
├── ordine per costo crescente: lint → tipi → test → build → E2E
├── parallelo dove le cose sono indipendenti; partizionare gli E2E
├── cache con la chiave giusta: mai troppo generica
├── un solo artefatto attraversa gli ambienti
└── sotto i sei minuti, altrimenti si smette di aspettarla

RILASCIO
├── rolling · blue-green · canary — tutti richiedono compatibilità
│     in avanti dello schema
├── spegnimento pulito obbligatorio
├── rollback = ridistribuire, non ricostruire, in meno di un minuto
├── migrazioni additive prima, distruttive molto dopo
└── osservare errori, p95/p99, throughput e saturazione per dieci
      minuti, con il deploy annotato sui grafici

CDN E CACHE
├── impronte nei nomi → immutable, un anno
├── index.html → no-cache (verifica sempre, 304 se invariato)
├── brotli sui testi · AVIF/WebP con srcset · font-display: swap
└── invalidare solo ciò che non ha impronta

SICUREZZA DELLA BUILD
├── azioni fissate al commit · permessi minimi espliciti
├── mai `pull_request_target` con codice di fork
├── OIDC invece di chiavi statiche · --ignore-scripts
└── artefatti firmati, SBOM, scansione dei segreti
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai spiegare i quattro compiti di un bundler
- [ ] Sai perché sviluppo e build in Vite sono pipeline diverse
- [ ] Esegui `build && preview` prima di ogni push, e sai perché
- [ ] Sai perché il lockfile va committato e cosa fa `--frozen-lockfile`
- [ ] Sai perché pnpm impedisce gli import non dichiarati
- [ ] Distingui il compito di Prettier da quello di ESLint
- [ ] Sai perché `eslint-config-prettier` va per ultimo
- [ ] Ordini i passi della pipeline per costo crescente

**Parte B — Comprensione**

- [ ] Sai dove conviene dividere il codice e dove no
- [ ] Sai cos'è il waterfall dei pezzi e come si evita
- [ ] Sai cosa impedisce il tree shaking e a cosa serve `sideEffects`
- [ ] Sai perché `"sideEffects": false` sbagliato rompe solo in produzione
- [ ] Imposti un budget e lo fai rispettare in CI, sul valore compresso
- [ ] Distingui variabili di build time e di runtime, e le implicazioni
- [ ] Sai perché un artefatto per ambiente è un problema
- [ ] Sai spiegare ognuna delle sei decisioni di un Dockerfile multi-stage
- [ ] Sai perché `.dockerignore` è obbligatorio e perché i `.map` non si pubblicano
- [ ] Sai perché una chiave di cache troppo generica è peggio di nessuna cache
- [ ] Conosci rolling, blue-green e canary e i loro costi
- [ ] Sai perché il rollback non deve ricostruire
- [ ] Sai quali file ricevono `immutable` e quali `no-cache`
- [ ] Sai quando un monorepo conviene e cosa costa davvero

**Parte C — Pratica**

- [ ] Hai usato la mappa del bundle prima di ottimizzare
- [ ] Hai ridotto il percorso critico e impedito il ritorno con un budget
- [ ] Hai parallelizzato la pipeline e partizionato gli E2E
- [ ] Hai portato l'immagine sotto i 200 MB con il multi-stage
- [ ] Hai trovato e rimosso il segreto dall'immagine, e lo hai ruotato
- [ ] Hai verificato che `docker stop` produca uno spegnimento pulito

**Parte D — Esperto**

- [ ] Sai cosa rompe la riproducibilità e come si verifica
- [ ] Sai perché una percentuale di feature flag deve essere stabile per utente
- [ ] Sai perché ogni flag nasce con una data di rimozione
- [ ] Sai perché la migrazione distruttiva impedisce il rollback
- [ ] Sai perché le migrazioni non vanno eseguite all'avvio dell'applicazione
- [ ] Osservi le quattro metriche dopo un deploy, con l'annotazione sui grafici
- [ ] Fissi le azioni al commit e usi OIDC invece di chiavi statiche

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Lockfile non committato, o `npm install` in CI | La build di oggi non è quella di ieri | Committarlo; `--frozen-lockfile` |
| Regole di formattazione in ESLint | I due strumenti si contraddicono a ogni salvataggio | Prettier formatta, `eslint-config-prettier` per ultimo |
| Build prima di lint e tipi | Un errore di battitura costa minuti | Ordine per costo crescente |
| Passi indipendenti in sequenza | Il tempo è la somma invece del massimo | Job paralleli; E2E partizionati |
| Chiave di cache troppo generica | Riusa artefatti vecchi: sbagliato e sembra giusto | Chiave su lockfile e sorgenti |
| `import _ from 'lodash'` | Trascina l'intera libreria | Import nominali, o funzioni native |
| Import dal barrel file di una libreria di icone | Centinaia di kB per dodici icone | Import dal percorso specifico |
| `"sideEffects": false` non verificato | Il bundler elimina moduli che registrano qualcosa | Elencare le eccezioni |
| Dividere componenti piccoli | Ogni pezzo è una richiesta: sotto i 10 kB si perde | Dividere per rotta e per dipendenza grande |
| Nessun budget di dimensione | Cresce di poche decine di kB per rilascio, senza accorgersene | `size-limit` in CI, sul compresso |
| Segreto in un `ENV` del Dockerfile | Si legge con `docker history` | A runtime; e ruotare quello esposto |
| `COPY . .` prima di `install` | La cache delle dipendenze si invalida a ogni modifica | Prima lockfile e package.json |
| Nessun `.dockerignore` | `node_modules`, `.git` e `.env` finiscono nell'immagine | Crearlo, sempre |
| Immagine senza multi-stage | Compilatore e sorgenti in produzione | Tre stadi, `prune --prod` |
| Container che gira come root | Un'escalation dà root sull'host | `USER node` |
| `CMD npm start` | npm è il processo 1 e non propaga SIGTERM | `CMD ["node", "dist/server.js"]` |
| Sourcemap pubblicati | Espongono il codice sorgente | Caricarli sul monitoraggio, eliminarli dall'artefatto |
| Ricostruire per il rollback | Non è un rollback: è un altro rilascio | Ridistribuire l'artefatto precedente |
| Un artefatto per ambiente | Si testa una cosa e se ne rilascia un'altra | Uno solo, configurato a runtime |
| Migrazione distruttiva insieme al deploy | Il rollback del codice non la annulla | Expand-contract, distruttiva molto dopo |
| Migrazioni all'avvio dell'applicazione | Dieci istanze migrano insieme | Job dedicato prima del deploy |
| Azioni CI fissate al tag | Un tag si può spostare su codice diverso | Fissare al commit |
| Feature flag senza scadenza | Ogni flag raddoppia i percorsi da testare | Data di rimozione alla nascita |

---

## Troubleshooting rapido

**Funziona in sviluppo, si rompe dopo la build**
- Causa: sviluppo e build sono pipeline diverse — maiuscole nei percorsi, side effect eliminato, dipendenza CommonJS
- Fix: riprodurre con `build && preview`; verificare l'errore nel bundle, non nel sorgente

**Il bundle è cresciuto senza motivo apparente**
- Causa: una dipendenza nuova, o un import che ha trascinato un barrel file
- Fix: `vite-bundle-visualizer` e confronto con la build precedente

**`Cannot find module` solo in CI**
- Causa: differenza di maiuscole nel percorso (Windows e macOS perdonano, Linux no), o dipendenza non dichiarata che l'hoisting nascondeva
- Fix: allineare i percorsi; con pnpm il problema emerge già in locale

**La cache di Vite serve codice vecchio**
- Causa: `node_modules/.vite` disallineato dopo un cambio di dipendenze
- Fix: `vite --force`, oppure eliminare la cartella

**La build Docker non usa la cache**
- Causa: `COPY . .` prima dell'installazione, o un file che cambia sempre (timestamp) copiato presto
- Fix: copiare prima solo lockfile e package.json; `.dockerignore` completo

**Il container non si ferma con `docker stop`**
- Causa: SIGTERM non arriva a Node — `CMD npm start`, o manca l'init
- Fix: `CMD ["node", …]` in forma exec; `docker run --init`

**Il deploy è passato ma il sito mostra la versione vecchia**
- Causa: `index.html` in cache sulla CDN
- Fix: `no-cache` su index.html; invalidare solo i file senza impronta

**Gli utenti vedono errori di caricamento dei pezzi dopo un rilascio**
- Causa: la pagina aperta prima del deploy chiede un pezzo che non esiste più
- Fix: conservare gli artefatti precedenti per qualche giorno; intercettare l'errore di import dinamico e proporre il ricaricamento

**La pipeline è verde ma la produzione è rotta**
- Causa: l'artefatto della produzione non è quello testato, o una variabile d'ambiente differisce
- Fix: un solo artefatto per tutti gli ambienti; confrontare le configurazioni

**Il rollback non ripristina il funzionamento**
- Causa: una migrazione distruttiva già applicata
- Fix: expand-contract; la distruttiva solo quando il rollback non è più previsto

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_17_performance_web.md` | Cosa fare con i byte che la build produce, e i budget misurati sul campo |
| `tutorial_19_troubleshooting.md` | Diagnosi in produzione dopo un rilascio andato male |
| `tutorial_14_sicurezza_web.md` | Segreti, supply chain e sicurezza della pipeline in profondità |
| `tutorial_15_testing_web.md` | La suite che questa pipeline esegue |
| `tutorial_12_database_web.md` | Migrazioni senza downtime, che il deploy deve rispettare |
| `tutorial_25_nextjs.md` | Build e deploy di un'applicazione con rendering sul server |

---

## Risorse di riferimento

**Documentazione:** [Vite](https://vite.dev/guide/) — in particolare *Build Options* e *Dep Optimization* · [Rollup](https://rollupjs.org/) · [pnpm](https://pnpm.io/) · [Docker — Best practices](https://docs.docker.com/build/building/best-practices/) · [GitHub Actions](https://docs.github.com/actions)

**Approfondimenti:** [web.dev — Fast load times](https://web.dev/explore/fast) · [Node.js Docker best practices](https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md) · [The Twelve-Factor App](https://12factor.net/), in particolare *Config* e *Build, release, run* · [SLSA](https://slsa.dev/) per l'integrità della catena di build

**Strumenti:** [size-limit](https://github.com/ai/size-limit) · [vite-bundle-visualizer](https://github.com/KusStar/vite-bundle-visualizer) · [Turborepo](https://turbo.build/repo) · [dive](https://github.com/wagoodman/dive) per ispezionare gli strati di un'immagine · [Sigstore](https://www.sigstore.dev/)

---

> **Fine del Tutorial 16 — Build Tools e Deploy**
>
> Prossimo tutorial: `tutorial_17_performance_web.md`
