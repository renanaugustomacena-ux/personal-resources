---
corso: "Sviluppo Web"
fase: "6 — DevOps"
modulo: "16"
titolo: "Build Tools e Deployment"
versione: "Vite 6.x / Turbopack / Docker / Vercel / Cloudflare"
livello: "Intermedio"
prerequisiti:
  - "06 — TypeScript"
  - "10 — Node.js"
obiettivi:
  - "Configurare Vite per sviluppo e produzione"
  - "Comprendere bundling, tree-shaking e code splitting"
  - "Implementare CI/CD con GitHub Actions per deploy automatico"
  - "Deployare su Vercel, Cloudflare Pages e container Docker"
  - "Gestire variabili d'ambiente e configurazione per ambiente"
  - "Ottimizzare bundle size e tempi di build"
tag: [Vite, build-tools, deployment, Docker, Vercel, Cloudflare, CI-CD, bundling]
---

# Build Tools e Deployment

> **Modulo 16** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [TypeScript](06-typescript.md), [Node.js](10-nodejs.md)
>
> Al termine di questo modulo saprai:
> 1. Configurare Vite per sviluppo e produzione
> 2. Comprendere bundling, tree-shaking e code splitting
> 3. Implementare CI/CD con GitHub Actions per deploy automatico
> 4. Deployare su Vercel, Cloudflare Pages e container Docker
> 5. Gestire variabili d'ambiente e configurazione per ambiente
> 6. Ottimizzare bundle size e tempi di build
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio

## Idee guida
1. **Vite > Webpack per nuovi progetti.** Speed + DX.
2. **Bundle analyzer mandatory.** Visualize bloat.
3. **CDN edge deploy: Vercel, Netlify, Cloudflare.**
4. **Preview deploy per PR.** Test before merge.


## Panoramica

Lo sviluppo web moderno non si limita alla scrittura del codice: richiede una pipeline di build sofisticata che trasforma il codice sorgente in artefatti ottimizzati pronti per la produzione. Questa pipeline comprende la compilazione TypeScript, il bundling dei moduli, la minificazione, l'ottimizzazione degli asset, il linting, il testing e infine il deployment automatizzato verso l'infrastruttura di hosting.

Il concetto di **build pipeline** descrive la sequenza ordinata di trasformazioni che il codice attraversa dal repository locale fino al server di produzione. Una pipeline tipica segue questo flusso:

```
Codice Sorgente
    → Linting e Formatting (ESLint, Prettier)
    → Type Checking (TypeScript)
    → Testing (Vitest, Playwright)
    → Bundling e Ottimizzazione (Vite, Webpack)
    → Asset Processing (immagini, font, CSS)
    → Containerizzazione (Docker)
    → CI/CD (GitHub Actions)
    → Deployment (Vercel, AWS, self-hosted)
    → CDN e Invalidazione Cache
```

Ogni fase della pipeline serve uno scopo preciso. Il linting cattura errori stilistici e potenziali bug prima della compilazione. Il type checking verifica la correttezza dei tipi. Il testing garantisce che il comportamento atteso sia preservato. Il bundling combina centinaia di moduli in un numero ridotto di file ottimizzati per il browser. La containerizzazione garantisce la riproducibilità dell'ambiente. Il CI/CD automatizza l'intero processo, eliminando errori manuali.

La scelta degli strumenti non è neutrale: influenza la developer experience, i tempi di build, le dimensioni del bundle finale e la complessità della manutenzione. Questa guida analizza gli strumenti più rilevanti dell'ecosistema attuale, con un focus primario su Vite come bundler di riferimento.

---

## Vite

Vite ha ridefinito le aspettative della developer experience nel frontend. Creato da Evan You (autore di Vue.js), Vite sfrutta i moduli ES nativi del browser durante lo sviluppo, eliminando la necessità di un bundling completo ad ogni modifica. In produzione utilizza Rollup (dalla versione 6, Rolldown basato su Rust) per generare bundle altamente ottimizzati.

### Configurazione Base — vite.config.ts

La configurazione di Vite è un file TypeScript che esporta un oggetto di configurazione tramite la funzione `defineConfig`:

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    },
  },

  server: {
    port: 3000,
    open: true,
    cors: true,
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2022',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },

  css: {
    modules: {
      localsConvention: 'camelCase',
    },
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables" as *;`,
      },
    },
  },
});
```

### Configurazione Condizionale per Ambiente

Vite supporta una funzione di configurazione che riceve il contesto dell'ambiente corrente:

```typescript
// vite.config.ts — configurazione condizionale
import { defineConfig, type UserConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command, mode }) => {
  const isProduction = mode === 'production';
  const isDevelopment = mode === 'development';

  const config: UserConfig = {
    plugins: [react()],

    // Abilita sourcemap solo in sviluppo
    build: {
      sourcemap: isDevelopment ? 'inline' : false,
      minify: isProduction ? 'esbuild' : false,
    },

    // In sviluppo, configura il proxy verso il backend
    server: isDevelopment
      ? {
          proxy: {
            '/api': {
              target: 'http://localhost:8080',
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/api/, ''),
            },
            '/ws': {
              target: 'ws://localhost:8080',
              ws: true,
            },
          },
        }
      : undefined,
  };

  return config;
});
```

### Plugin Ecosystem

Il sistema di plugin di Vite è compatibile con quello di Rollup, con estensioni specifiche per le funzionalità del dev server. I plugin più utilizzati includono:

```typescript
// vite.config.ts — plugin avanzati
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { compression } from 'vite-plugin-compression2';
import { visualizer } from 'rollup-plugin-visualizer';
import { VitePWA } from 'vite-plugin-pwa';
import svgr from 'vite-plugin-svgr';

export default defineConfig({
  plugins: [
    // Plugin React con supporto SWC (più veloce di Babel)
    react(),

    // Importa SVG come componenti React
    svgr({
      svgrOptions: {
        icon: true,
        dimensions: false,
      },
    }),

    // Compressione Gzip e Brotli degli asset
    compression({
      algorithm: 'gzip',
      exclude: [/\.(br)$/, /\.(gz)$/],
    }),
    compression({
      algorithm: 'brotliCompress',
      exclude: [/\.(br)$/, /\.(gz)$/],
    }),

    // Progressive Web App
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
      },
    }),

    // Analisi visuale del bundle (solo in build)
    visualizer({
      filename: 'stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
});
```

### Dev Server e HMR

Il dev server di Vite serve i moduli ES nativi al browser, trasformando ogni file on-demand. L'Hot Module Replacement (HMR) aggiorna solo i moduli modificati senza ricaricare la pagina, preservando lo stato dell'applicazione:

```typescript
// Il modulo React Fast Refresh è integrato nel plugin @vitejs/plugin-react
// L'HMR funziona automaticamente per i componenti React

// Per moduli personalizzati, si può gestire l'HMR manualmente:
if (import.meta.hot) {
  import.meta.hot.accept('./module.ts', (newModule) => {
    // Aggiorna il modulo senza ricaricare la pagina
    console.log('Modulo aggiornato:', newModule);
  });

  // Esegui cleanup quando il modulo viene sostituito
  import.meta.hot.dispose(() => {
    clearInterval(timer);
  });
}
```

### Variabili d'Ambiente

Vite espone le variabili d'ambiente tramite `import.meta.env`. Solo le variabili con prefisso `VITE_` sono esposte al codice client:

```bash
# .env — caricato in tutti gli ambienti
VITE_APP_TITLE=La Mia App
VITE_API_BASE_URL=https://api.example.com

# .env.development — solo in sviluppo
VITE_API_BASE_URL=http://localhost:8080/api
VITE_DEBUG=true

# .env.production — solo in produzione
VITE_API_BASE_URL=https://api.production.com
VITE_SENTRY_DSN=https://xxx@sentry.io/123

# Variabili SENZA prefisso VITE_ non sono esposte al client
DATABASE_URL=postgresql://localhost:5432/mydb
SECRET_KEY=supersecret
```

```typescript
// src/env.d.ts — tipizzazione delle variabili d'ambiente
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string;
  readonly VITE_API_BASE_URL: string;
  readonly VITE_DEBUG?: string;
  readonly VITE_SENTRY_DSN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Utilizzo nel codice
const apiUrl = import.meta.env.VITE_API_BASE_URL;
const isDebug = import.meta.env.VITE_DEBUG === 'true';
const mode = import.meta.env.MODE; // 'development' | 'production'
const isProd = import.meta.env.PROD; // boolean
```

### Build Optimization

Vite offre diverse strategie per ottimizzare il bundle di produzione:

```typescript
// vite.config.ts — ottimizzazione avanzata del build
export default defineConfig({
  build: {
    // Target browser moderni per bundle più leggeri
    target: 'es2022',

    // Chunk size warning limit (kB)
    chunkSizeWarningLimit: 500,

    // Rimuovi console.log in produzione
    minify: 'esbuild',
    esbuild: {
      drop: ['console', 'debugger'],
    },

    rollupOptions: {
      output: {
        // Strategia di chunking manuale
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Separa le librerie grandi in chunk dedicati
            if (id.includes('chart.js') || id.includes('d3')) {
              return 'charts';
            }
            if (id.includes('@tanstack/react-query')) {
              return 'query';
            }
            // Tutte le altre dipendenze in un chunk vendor
            return 'vendor';
          }
        },

        // Naming pattern per cache busting
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },

    // Abilita CSS code splitting
    cssCodeSplit: true,

    // Genera report di analisi
    reportCompressedSize: true,
  },
});
```

### Vite Deep-Dive: Authoring Plugin Personalizzati

Il sistema di plugin di Vite estende l'interfaccia di Rollup con hook specifici per il dev server. Comprendere l'architettura dei plugin permette di personalizzare profondamente il comportamento del bundler senza dipendere da soluzioni di terze parti.

Un plugin Vite e' un oggetto che implementa uno o piu' hook. Gli hook si dividono in tre categorie: hook universali (condivisi con Rollup, eseguiti sia in dev che in build), hook specifici di Vite (eseguiti solo durante lo sviluppo o solo durante il build), e hook di trasformazione che modificano il codice sorgente al volo.

```typescript
// plugins/vite-plugin-build-info.ts — Plugin custom che inietta metadati di build
import { execSync } from 'node:child_process';
import type { Plugin } from 'vite';

interface BuildInfoOptions {
  /** Prefisso per le variabili iniettate */
  prefix?: string;
  /** Includi il timestamp di build */
  includeTimestamp?: boolean;
}

export function buildInfoPlugin(options: BuildInfoOptions = {}): Plugin {
  const { prefix = 'VITE_BUILD', includeTimestamp = true } = options;

  let commitHash: string;
  let buildTimestamp: string;

  return {
    name: 'vite-plugin-build-info',

    // enforce: 'pre' esegue il plugin prima dei plugin core di Vite
    // enforce: 'post' lo esegue dopo
    enforce: 'pre',

    // configResolved riceve la configurazione finale risolta
    configResolved(config) {
      try {
        commitHash = execSync('git rev-parse --short HEAD')
          .toString()
          .trim();
      } catch {
        commitHash = 'unknown';
      }
      buildTimestamp = new Date().toISOString();
    },

    // config hook modifica la configurazione prima che venga risolta
    config(config, { command }) {
      return {
        define: {
          [`import.meta.env.${prefix}_COMMIT`]: JSON.stringify(
            commitHash ?? 'dev',
          ),
          ...(includeTimestamp && {
            [`import.meta.env.${prefix}_TIMESTAMP`]: JSON.stringify(
              buildTimestamp ?? new Date().toISOString(),
            ),
          }),
        },
      };
    },

    // transform hook modifica il codice sorgente dei moduli
    transform(code, id) {
      // Esempio: sostituisci un placeholder custom nel codice
      if (id.endsWith('.ts') || id.endsWith('.tsx')) {
        return code.replace(
          /__BUILD_VERSION__/g,
          JSON.stringify(commitHash ?? 'dev'),
        );
      }
    },

    // configureServer aggiunge middleware al dev server
    configureServer(server) {
      server.middlewares.use('/api/build-info', (_req, res) => {
        res.setHeader('Content-Type', 'application/json');
        res.end(
          JSON.stringify({
            commit: commitHash,
            timestamp: buildTimestamp,
            mode: 'development',
          }),
        );
      });
    },

    // buildEnd viene chiamato al termine del build
    buildEnd() {
      console.log(`Build completato — commit: ${commitHash}`);
    },
  };
}
```

```typescript
// vite.config.ts — utilizzo del plugin custom
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { buildInfoPlugin } from './plugins/vite-plugin-build-info';

export default defineConfig({
  plugins: [
    react(),
    buildInfoPlugin({ prefix: 'VITE_APP', includeTimestamp: true }),
  ],
});
```

L'ordine di esecuzione dei plugin segue una gerarchia precisa: prima i plugin con `enforce: 'pre'`, poi i plugin senza `enforce` (normali), poi i plugin core di Vite per la risoluzione e la trasformazione, e infine i plugin con `enforce: 'post'`. Questa gerarchia permette di intercettare il codice prima o dopo le trasformazioni standard.

#### Hook Principali dei Plugin Vite

| Hook | Fase | Descrizione |
|---|---|---|
| `config` | Pre-risoluzione | Modifica la configurazione prima della risoluzione |
| `configResolved` | Post-risoluzione | Accede alla configurazione finale |
| `configureServer` | Dev only | Aggiunge middleware al dev server |
| `configurePreviewServer` | Preview only | Aggiunge middleware al server di anteprima |
| `transformIndexHtml` | Build/Dev | Trasforma il file `index.html` |
| `handleHotUpdate` | Dev only | Gestisce aggiornamenti HMR personalizzati |
| `resolveId` | Build/Dev | Risolve percorsi di importazione personalizzati |
| `load` | Build/Dev | Carica il contenuto di un modulo personalizzato |
| `transform` | Build/Dev | Trasforma il codice sorgente di un modulo |

### Vite Deep-Dive: Server-Side Rendering (SSR)

Vite fornisce supporto nativo per il Server-Side Rendering, consentendo di renderizzare i componenti React, Vue o Svelte sul server e inviare HTML pre-renderizzato al client. L'architettura SSR di Vite si basa sul concetto di doppio entry point: un entry per il client (che gestisce l'idratazione nel browser) e un entry per il server (che genera l'HTML).

```typescript
// src/entry-server.tsx — Entry point per il server
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom';
import { App } from './App';

export function render(url: string) {
  const html = renderToString(
    <StaticRouter location={url}>
      <App />
    </StaticRouter>,
  );
  return { html };
}
```

```typescript
// src/entry-client.tsx — Entry point per il client (idratazione)
import { hydrateRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './App';

hydrateRoot(
  document.getElementById('root')!,
  <BrowserRouter>
    <App />
  </BrowserRouter>,
);
```

```typescript
// server.ts — Server Express con Vite SSR
import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer as createViteServer, type ViteDevServer } from 'vite';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const isProduction = process.env.NODE_ENV === 'production';

async function createServer() {
  const app = express();
  let vite: ViteDevServer | undefined;

  if (!isProduction) {
    // In sviluppo, usa il dev server di Vite come middleware
    vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'custom',
    });
    app.use(vite.middlewares);
  } else {
    // In produzione, servi gli asset statici
    app.use(
      '/assets',
      express.static(path.resolve(__dirname, 'dist/client/assets'), {
        maxAge: '1y',
        immutable: true,
      }),
    );
  }

  app.use('*', async (req, res) => {
    const url = req.originalUrl;

    try {
      let template: string;
      let render: (url: string) => { html: string };

      if (!isProduction && vite) {
        // In sviluppo, Vite trasforma il template e i moduli al volo
        template = fs.readFileSync(
          path.resolve(__dirname, 'index.html'),
          'utf-8',
        );
        template = await vite.transformIndexHtml(url, template);
        const mod = await vite.ssrLoadModule('/src/entry-server.tsx');
        render = mod.render;
      } else {
        // In produzione, usa i file pre-compilati
        template = fs.readFileSync(
          path.resolve(__dirname, 'dist/client/index.html'),
          'utf-8',
        );
        const mod = await import('./dist/server/entry-server.js');
        render = mod.render;
      }

      const { html: appHtml } = render(url);
      const finalHtml = template.replace('<!--ssr-outlet-->', appHtml);
      res.status(200).set({ 'Content-Type': 'text/html' }).end(finalHtml);
    } catch (e) {
      if (!isProduction && vite) {
        vite.ssrFixStacktrace(e as Error);
      }
      console.error(e);
      res.status(500).end('Internal Server Error');
    }
  });

  app.listen(3000, () => {
    console.log('Server SSR avviato su http://localhost:3000');
  });
}

createServer();
```

La configurazione di build per SSR richiede due build separati: uno per il client e uno per il server.

```json
// package.json — script per SSR
{
  "scripts": {
    "dev": "node server.ts",
    "build": "pnpm build:client && pnpm build:server",
    "build:client": "vite build --outDir dist/client",
    "build:server": "vite build --outDir dist/server --ssr src/entry-server.tsx",
    "preview": "NODE_ENV=production node dist/server.js"
  }
}
```

A partire da Vite 6, il modulo `server.ssrLoadModule` e' stato sostituito dal ModuleRunner API, che offre un'architettura piu' pulita per l'esecuzione dei moduli server-side con supporto migliorato per l'HMR e l'isolamento del contesto di esecuzione.

### Vite Deep-Dive: Library Mode

Vite supporta la modalita' libreria per la compilazione di pacchetti npm riutilizzabili. In questa modalita', Vite genera bundle ottimizzati nei formati ES Module e CommonJS, con file di dichiarazione TypeScript e gestione corretta delle dipendenze esterne.

```typescript
// vite.config.ts — configurazione per library mode
import { defineConfig } from 'vite';
import { resolve } from 'node:path';
import dts from 'vite-plugin-dts';

export default defineConfig({
  plugins: [
    // Genera file .d.ts per i tipi TypeScript
    dts({
      insertTypesEntry: true,
      rollupTypes: true,
    }),
  ],

  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'MyLib',
      // Genera file nei formati ES e CommonJS
      formats: ['es', 'cjs'],
      fileName: (format) => `my-lib.${format}.js`,
      // Da Vite 6, il nome del file CSS segue il nome nel package.json
      cssFileName: 'my-lib',
    },

    rollupOptions: {
      // Escludi le dipendenze esterne dal bundle
      external: ['react', 'react-dom', 'react/jsx-runtime'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
        // Preserva la struttura dei moduli per tree shaking ottimale
        preserveModules: true,
        preserveModulesRoot: 'src',
      },
    },

    // Disabilita la minificazione per le librerie
    // (sara' il consumatore a minificare nel proprio build)
    minify: false,

    // Genera source map per il debugging
    sourcemap: true,
  },
});
```

```json
// package.json — configurazione exports per una libreria
{
  "name": "my-lib",
  "version": "1.0.0",
  "type": "module",
  "main": "./dist/my-lib.cjs.js",
  "module": "./dist/my-lib.es.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/my-lib.es.js",
      "require": "./dist/my-lib.cjs.js",
      "types": "./dist/index.d.ts"
    },
    "./styles": "./dist/my-lib.css"
  },
  "files": ["dist"],
  "sideEffects": ["**/*.css"],
  "peerDependencies": {
    "react": "^18.0.0 || ^19.0.0",
    "react-dom": "^18.0.0 || ^19.0.0"
  }
}
```

L'opzione `preserveModules` e' particolarmente importante per le librerie: invece di generare un singolo bundle monolitico, mantiene la struttura dei file sorgente nell'output. Questo consente ai consumatori della libreria di beneficiare del tree shaking a livello di singolo modulo, importando solo le funzionalita' effettivamente utilizzate.

### Vite Deep-Dive: Gestione Avanzata delle Variabili d'Ambiente

Oltre al meccanismo base con prefisso `VITE_`, esistono pattern avanzati per la gestione delle variabili d'ambiente in progetti complessi.

```typescript
// src/config.ts — validazione runtime delle variabili d'ambiente
import { z } from 'zod';

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url('API_BASE_URL deve essere un URL valido'),
  VITE_APP_TITLE: z.string().min(1, 'APP_TITLE e\' obbligatorio'),
  VITE_SENTRY_DSN: z.string().url().optional(),
  VITE_FEATURE_AUTH_SSO: z
    .enum(['true', 'false'])
    .transform((v) => v === 'true')
    .default('false'),
  VITE_MAX_UPLOAD_SIZE_MB: z.coerce.number().min(1).max(100).default(10),
});

// Validazione al caricamento del modulo — fallisce immediatamente
// se una variabile obbligatoria e' mancante o non valida
const parsed = envSchema.safeParse(import.meta.env);

if (!parsed.success) {
  console.error(
    'Configurazione ambiente non valida:',
    parsed.error.flatten().fieldErrors,
  );
  throw new Error('Variabili d\'ambiente mancanti o non valide');
}

export const config = Object.freeze(parsed.data);

// Utilizzo nel codice
// import { config } from '@/config';
// fetch(`${config.VITE_API_BASE_URL}/users`);
```

```typescript
// vite.config.ts — caricamento variabili d'ambiente nella configurazione
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  // loadEnv carica le variabili da .env, .env.[mode], .env.[mode].local
  // Il terzo parametro '' carica TUTTE le variabili (non solo VITE_)
  const env = loadEnv(mode, process.cwd(), '');

  return {
    // Usa variabili non-VITE_ nella configurazione (lato server)
    server: {
      proxy: {
        '/api': {
          target: env.BACKEND_URL || 'http://localhost:8080',
          changeOrigin: true,
        },
      },
    },

    // envPrefix personalizzato per progetti con prefisso diverso
    envPrefix: ['VITE_', 'PUBLIC_'],
  };
});
```

La gerarchia di caricamento dei file `.env` segue un ordine preciso di priorita': `.env` (caricato sempre), `.env.local` (caricato sempre, ignorato da git), `.env.[mode]` (caricato solo nel modo specificato), `.env.[mode].local` (caricato solo nel modo specificato, ignorato da git). I file piu' specifici sovrascrivono quelli generici, e i file `.local` sovrascrivono i file non-local.

---

## Webpack

Webpack rimane il bundler più diffuso in progetti legacy e in framework come Next.js (che sta migrando verso Turbopack). Sebbene Vite sia la scelta raccomandata per nuovi progetti, comprendere i concetti fondamentali di Webpack è essenziale per la manutenzione del codice esistente.

### Concetti Fondamentali

Webpack si basa su quattro concetti chiave:

- **Entry**: il punto di ingresso da cui Webpack inizia a costruire il grafo delle dipendenze
- **Output**: dove e come Webpack emette i bundle generati
- **Loaders**: trasformazioni applicate ai file prima di includerli nel bundle (TypeScript, CSS, immagini)
- **Plugins**: estensioni che intervengono nel processo di build per operazioni più complesse

```javascript
// webpack.config.js — configurazione tipica
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';

  return {
    entry: './src/index.tsx',

    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: isProduction
        ? '[name].[contenthash].js'
        : '[name].bundle.js',
      clean: true,
      publicPath: '/',
    },

    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader',
            'postcss-loader',
          ],
        },
        {
          test: /\.(png|jpg|gif|svg|woff2?)$/,
          type: 'asset/resource',
        },
      ],
    },

    plugins: [
      new HtmlWebpackPlugin({
        template: './public/index.html',
      }),
      isProduction && new MiniCssExtractPlugin({
        filename: '[name].[contenthash].css',
      }),
      env.analyze && new BundleAnalyzerPlugin(),
    ].filter(Boolean),

    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },

    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
        },
      },
    },

    devServer: {
      port: 3000,
      hot: true,
      historyApiFallback: true,
    },
  };
};
```

### Code Splitting e Tree Shaking

Webpack supporta il code splitting tramite import dinamici e la configurazione `splitChunks`. Il tree shaking elimina il codice non utilizzato dai bundle di produzione, ma richiede che i moduli utilizzino la sintassi ESM (`import`/`export`):

```javascript
// Import dinamico — crea un chunk separato caricato on-demand
const AdminPanel = React.lazy(() => import('./pages/AdminPanel'));

// Il tree shaking elimina le funzioni non importate
// utils.js esporta 10 funzioni, ma solo 2 sono importate:
import { formatDate, parseJSON } from './utils';
// Le altre 8 funzioni vengono rimosse dal bundle finale
```

La configurazione `sideEffects: false` nel `package.json` indica a Webpack che tutti i moduli del pacchetto sono privi di effetti collaterali, abilitando un tree shaking più aggressivo.

### Webpack 5 Avanzato: Module Federation

Module Federation e' la funzionalita' piu' innovativa introdotta da Webpack 5. Consente a piu' applicazioni Webpack indipendenti di condividere codice a runtime, abilitando architetture micro-frontend dove ciascun team sviluppa, testa e deploya il proprio modulo in modo autonomo.

Il concetto si basa su due ruoli: l'**host** (l'applicazione che consuma moduli remoti) e il **remote** (l'applicazione che espone moduli). Un'applicazione puo' ricoprire entrambi i ruoli contemporaneamente.

```javascript
// webpack.config.js — Remote: espone componenti
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  // ...
  plugins: [
    new ModuleFederationPlugin({
      name: 'dashboard',
      filename: 'remoteEntry.js',

      // Moduli esposti al consumo da parte di altre applicazioni
      exposes: {
        './AnalyticsWidget': './src/components/AnalyticsWidget',
        './UserProfile': './src/components/UserProfile',
        './chartUtils': './src/utils/charts',
      },

      // Dipendenze condivise: evita duplicazione in runtime
      shared: {
        react: {
          singleton: true,        // Una sola istanza globale
          requiredVersion: '^19.0.0',
          eager: false,           // Caricamento lazy
        },
        'react-dom': {
          singleton: true,
          requiredVersion: '^19.0.0',
        },
        'react-router-dom': {
          singleton: true,
          requiredVersion: '^7.0.0',
        },
      },
    }),
  ],
};
```

```javascript
// webpack.config.js — Host: consuma moduli remoti
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  // ...
  plugins: [
    new ModuleFederationPlugin({
      name: 'shell',
      remotes: {
        // URL del remoteEntry.js generato dall'applicazione remota
        dashboard: 'dashboard@https://dashboard.example.com/remoteEntry.js',
        auth: 'auth@https://auth.example.com/remoteEntry.js',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^19.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^19.0.0' },
      },
    }),
  ],
};
```

```tsx
// src/App.tsx — Consumo di un componente federato nell'host
import React, { Suspense } from 'react';

// Import dinamico dal modulo remoto
const AnalyticsWidget = React.lazy(
  () => import('dashboard/AnalyticsWidget'),
);
const UserProfile = React.lazy(
  () => import('dashboard/UserProfile'),
);

function App() {
  return (
    <div>
      <h1>Shell Application</h1>
      <Suspense fallback={<div>Caricamento widget...</div>}>
        <AnalyticsWidget />
        <UserProfile userId="123" />
      </Suspense>
    </div>
  );
}
```

Module Federation richiede attenzione particolare alla gestione delle versioni delle dipendenze condivise. Se due applicazioni federate dichiarano versioni incompatibili di una dipendenza singleton, Webpack genera un warning e carica la versione piu' recente che soddisfa entrambi i vincoli. Per evitare conflitti, e' fondamentale allineare le versioni major delle dipendenze condivise tra tutti i micro-frontend.

### Webpack 5 Avanzato: Persistent Caching

Webpack 5 introduce un sistema di caching persistente su filesystem che riduce drasticamente i tempi di build successivi al primo. La cache serializza il grafo dei moduli, le trasformazioni e i risultati intermedi su disco, riutilizzandoli nelle build successive se gli input non sono cambiati.

```javascript
// webpack.config.js — persistent caching
module.exports = {
  // ...
  cache: {
    type: 'filesystem',

    // Directory della cache (default: node_modules/.cache/webpack)
    cacheDirectory: path.resolve(__dirname, '.webpack-cache'),

    // Versione della cache: un cambio invalida tutta la cache
    version: `${process.env.NODE_ENV}-${packageJson.version}`,

    // File che, se modificati, invalidano la cache
    buildDependencies: {
      config: [__filename],          // Questo file di configurazione
      tsconfig: [
        path.resolve(__dirname, 'tsconfig.json'),
      ],
    },

    // Strategia di compressione per ridurre lo spazio disco
    compression: 'gzip',

    // Durata massima di conservazione della cache (default: 1 mese)
    maxAge: 1000 * 60 * 60 * 24 * 30, // 30 giorni

    // Controlla la serializzazione degli snapshot per i moduli
    managedPaths: [path.resolve(__dirname, 'node_modules')],
  },

  // Snapshot configuration per determinare quando invalidare
  snapshot: {
    // Controlla come Webpack verifica se un file e' cambiato
    module: {
      timestamp: true,  // Usa il timestamp del filesystem
      hash: true,       // Usa anche l'hash del contenuto (piu' affidabile)
    },
    resolve: {
      timestamp: true,
      hash: true,
    },
  },
};
```

Il persistent caching puo' ridurre i tempi di build dal 60% al 90% nelle build successive. In ambiente CI/CD, la cache del filesystem deve essere salvata e ripristinata tra le esecuzioni tramite le funzionalita' di caching del sistema CI (ad esempio `actions/cache` in GitHub Actions).

### Webpack 5 Avanzato: Tree Shaking Approfondito

Il tree shaking di Webpack 5 elimina il codice non raggiungibile analizzando staticamente le dipendenze ESM. Tuttavia, la sua efficacia dipende da come il codice e' scritto e configurato.

```javascript
// package.json — configurazione sideEffects per tree shaking ottimale
{
  "name": "my-library",
  "sideEffects": [
    "**/*.css",
    "**/*.scss",
    "./src/polyfills.ts",
    "./src/analytics/init.ts"
  ]
}
```

Il campo `sideEffects` indica a Webpack quali file contengono effetti collaterali (codice che ha impatto al di la' delle esportazioni, come CSS imports o inizializzazioni globali). Tutti i file non elencati vengono considerati "puri" e possono essere eliminati se le loro esportazioni non sono utilizzate.

Per massimizzare il tree shaking:

1. **Usa named exports** invece di default exports. I default export sono un singolo binding che Webpack non puo' suddividere ulteriormente.
2. **Evita re-export barrel** massicci. Un file `index.ts` che re-esporta 50 moduli impedisce al tree shaking di operare a livello granulare in molti casi.
3. **Marca le funzioni come pure** con il commento `/*#__PURE__*/` prima delle chiamate che Webpack potrebbe non riconoscere come prive di effetti collaterali.
4. **Configura `optimization.usedExports: true`** (attivo di default in produzione) perche' Webpack marchi le esportazioni non utilizzate.
5. **Configura `optimization.minimize: true`** per rimuovere effettivamente il codice marcato come non utilizzato dal bundle finale.

```javascript
// optimization avanzata per tree shaking
module.exports = {
  optimization: {
    usedExports: true,
    minimize: true,
    sideEffects: true,
    concatenateModules: true,  // Module concatenation (scope hoisting)
    innerGraph: true,          // Analisi del grafo interno dei moduli
    providedExports: true,     // Traccia le esportazioni fornite
  },
};
```

`concatenateModules` (scope hoisting) unisce moduli piccoli in un unico scope di funzione, riducendo l'overhead del sistema di moduli Webpack e migliorando sia le dimensioni del bundle che le performance di esecuzione.

---

## Alternative ai Bundler Tradizionali

### esbuild

esbuild, scritto in Go, è estremamente veloce (10-100x più rapido di Webpack). Vite lo utilizza internamente per la trasformazione dei file durante lo sviluppo e per la minificazione in produzione:

```bash
# Build diretto con esbuild
npx esbuild src/index.tsx --bundle --outfile=dist/bundle.js \
  --minify --sourcemap --target=es2022 --loader:.svg=dataurl
```

esbuild eccelle come transpiler e minifier, ma offre un supporto limitato per funzionalità avanzate come il code splitting basato su CSS o l'HMR completo.

### Turbopack

Turbopack, sviluppato da Vercel e scritto in Rust, è il successore designato di Webpack. Integrato in Next.js a partire dalla versione 13, promette performance di build significativamente superiori grazie all'architettura incrementale. Attualmente è utilizzabile tramite il flag `--turbopack` in Next.js ma non è ancora disponibile come bundler standalone generico.

### Bun Bundler

Bun include un bundler nativo scritto in Zig, progettato per essere un'alternativa drop-in a esbuild con performance ancora superiori:

```bash
# Build con il bundler di Bun
bun build ./src/index.tsx --outdir ./dist --minify --sourcemap=external
```

Bun bundler è ancora in fase di maturazione e non supporta tutte le funzionalità necessarie per applicazioni complesse in produzione, ma rappresenta una direzione interessante per il futuro.

### esbuild come Bundler Standalone

Sebbene Vite utilizzi esbuild internamente per la trasformazione dei file e la minificazione, esbuild puo' essere impiegato come bundler standalone per progetti dove la velocita' di build e' la priorita' assoluta e le funzionalita' avanzate (come l'HMR completo o il CSS code splitting sofisticato) non sono necessarie.

```typescript
// build.mjs — configurazione esbuild programmatica
import * as esbuild from 'esbuild';

const isProduction = process.env.NODE_ENV === 'production';

/** @type {esbuild.BuildOptions} */
const buildOptions = {
  entryPoints: ['src/index.tsx'],
  bundle: true,
  outdir: 'dist',

  // Formati di output
  format: 'esm',
  splitting: true,           // Abilita code splitting (solo con format: 'esm')

  // Ottimizzazione
  minify: isProduction,
  treeShaking: true,
  sourcemap: isProduction ? 'external' : 'inline',
  target: ['es2022', 'chrome100', 'firefox100', 'safari16'],

  // Loader per tipi di file
  loader: {
    '.png': 'file',
    '.jpg': 'file',
    '.svg': 'dataurl',
    '.woff2': 'file',
    '.css': 'css',
  },

  // Definizioni di compile-time
  define: {
    'process.env.NODE_ENV': JSON.stringify(
      process.env.NODE_ENV || 'development',
    ),
    __DEV__: JSON.stringify(!isProduction),
  },

  // Alias di percorso
  alias: {
    '@': './src',
    '@components': './src/components',
  },

  // Dipendenze esterne (non incluse nel bundle)
  external: isProduction ? [] : ['fsevents'],

  // Metafile per analisi del bundle
  metafile: true,

  // Banner e footer personalizzati
  banner: {
    js: '/* Build: ' + new Date().toISOString() + ' */',
  },
};

async function build() {
  const result = await esbuild.build(buildOptions);

  if (result.metafile) {
    // Genera un report testuale dell'analisi del bundle
    const analysis = await esbuild.analyzeMetafile(result.metafile, {
      verbose: true,
    });
    console.log(analysis);
  }
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

```typescript
// esbuild-plugin-example.mjs — plugin custom per esbuild
import * as esbuild from 'esbuild';
import fs from 'node:fs';

/** Plugin che risolve import con estensione .graphql */
const graphqlPlugin: esbuild.Plugin = {
  name: 'graphql-loader',
  setup(build) {
    // Intercetta la risoluzione dei file .graphql
    build.onResolve({ filter: /\.graphql$/ }, (args) => ({
      path: new URL(args.path, `file://${args.resolveDir}/`).pathname,
      namespace: 'graphql',
    }));

    // Carica e trasforma il contenuto dei file .graphql
    build.onLoad({ filter: /.*/, namespace: 'graphql' }, async (args) => {
      const source = await fs.promises.readFile(args.path, 'utf-8');
      return {
        contents: `export default ${JSON.stringify(source)}`,
        loader: 'js',
      };
    });
  },
};
```

Le limitazioni principali di esbuild come bundler standalone includono: assenza di type checking TypeScript nativo (richiede `tsc` separato), ecosistema di plugin piu' ristretto rispetto a Webpack e Rollup, supporto limitato per CSS Modules avanzati, e mancanza di HMR integrato nel dev server. Queste limitazioni lo rendono ideale per build di librerie, script di backend, e strumenti CLI, ma meno adatto come bundler primario per applicazioni frontend complesse.

### Turbopack: Architettura e Funzionamento Interno

Turbopack rappresenta un cambio di paradigma nell'architettura dei bundler JavaScript. Sviluppato da Vercel in Rust, si basa su un motore di computazione incrementale chiamato **Turbo Engine** che memorizza il risultato di ogni funzione nel programma. Quando il codice viene modificato, solo le funzioni i cui input sono cambiati vengono rieseguite.

L'architettura di Turbopack si articola in tre livelli:

1. **Turbo Engine** — il livello di memoizzazione e invalidazione. Tratta ogni operazione (parsing, trasformazione, risoluzione delle dipendenze, generazione del codice) come una funzione pura i cui risultati possono essere memorizzati nella cache. L'invalidazione opera a livello di singola funzione, non di modulo intero, garantendo che il lavoro minimo necessario venga eseguito dopo ogni modifica.

2. **Grafo delle Dipendenze Reattivo** — Turbopack costruisce un grafo di dipendenze dove ogni nodo rappresenta il risultato di una computazione. Quando un file viene modificato, il sistema invalida solo i nodi direttamente dipendenti da quel file, propagando l'invalidazione lungo il grafo con complessita' O(m) dove m e' il numero di nodi impattati (tipicamente molto piccolo rispetto al totale).

3. **Parallelizzazione Nativa** — Grazie a Rust e al modello di concorrenza basato su task, Turbopack parallelizza il lavoro su tutti i core CPU disponibili. Ogni funzione memoizzata puo' essere eseguita in parallelo con le altre, sfruttando appieno le architetture multi-core moderne.

Le performance di scaling di Turbopack sono lineari rispetto alla dimensione della modifica, non dell'applicazione:

| Moduli totali | Tempo di rebuild (singolo file) |
|---|---|
| 1.000 | ~50 ms |
| 5.000 | ~100 ms |
| 10.000 | ~150 ms |
| 30.000 | ~250 ms |

Questa caratteristica lo rende particolarmente adatto per applicazioni di grandi dimensioni dove Webpack e persino Vite iniziano a mostrare rallentamenti significativi.

```javascript
// next.config.js — abilitazione Turbopack in Next.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Da Next.js 15, Turbopack e' stabile per lo sviluppo
  // Da Next.js 16, e' il bundler predefinito
  turbopack: {
    // Alias di risoluzione
    resolveAlias: {
      '@': './src',
      '@components': './src/components',
      '@lib': './src/lib',
    },

    // Estensioni di risoluzione
    resolveExtensions: ['.tsx', '.ts', '.jsx', '.js', '.json'],

    // Regole di modulo (equivalente dei Webpack loaders)
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },
};

module.exports = nextConfig;
```

Turbopack non e' ancora disponibile come bundler standalone al di fuori di Next.js. La roadmap prevede il supporto per build di produzione (in fase di stabilizzazione) e l'apertura dell'API per l'integrazione con altri framework, ma al momento il suo utilizzo e' vincolato all'ecosistema Next.js/Vercel.

### Rollup per Librerie JavaScript

Rollup rimane il bundler di riferimento per la pubblicazione di librerie npm. La sua architettura, progettata nativamente attorno agli ES Modules, produce output puliti e altamente ottimizzabili grazie al tree shaking statico di primo livello.

```javascript
// rollup.config.mjs — configurazione completa per una libreria
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import terser from '@rollup/plugin-terser';
import peerDepsExternal from 'rollup-plugin-peer-deps-external';
import postcss from 'rollup-plugin-postcss';
import { readFileSync } from 'node:fs';

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'));

/** @type {import('rollup').RollupOptions} */
export default {
  input: 'src/index.ts',

  output: [
    {
      file: pkg.main,
      format: 'cjs',
      sourcemap: true,
      exports: 'named',
      // Preserva interop per moduli CommonJS
      interop: 'auto',
    },
    {
      file: pkg.module,
      format: 'esm',
      sourcemap: true,
      // Preserva la struttura dei moduli per tree shaking
      preserveModules: false,
    },
    {
      file: pkg.unpkg,
      format: 'umd',
      name: 'MyLib',
      sourcemap: true,
      globals: {
        react: 'React',
        'react-dom': 'ReactDOM',
      },
      plugins: [terser()],
    },
  ],

  plugins: [
    // Esclude automaticamente le peerDependencies dal bundle
    peerDepsExternal(),

    // Risolve i moduli da node_modules
    resolve({
      extensions: ['.ts', '.tsx', '.js', '.jsx'],
      browser: true,
    }),

    // Converte moduli CommonJS in ESM per l'inclusione nel bundle
    commonjs(),

    // Compila TypeScript
    typescript({
      tsconfig: './tsconfig.build.json',
      declaration: true,
      declarationDir: './dist/types',
      exclude: ['**/*.test.*', '**/*.spec.*', '**/*.stories.*'],
    }),

    // Processa CSS/SCSS
    postcss({
      modules: true,
      extract: 'styles.css',
      minimize: true,
    }),
  ],

  // Marcha moduli esterni che non devono entrare nel bundle
  external: [
    ...Object.keys(pkg.peerDependencies || {}),
    /^react\//,           // react/jsx-runtime, etc.
    /^@types\//,
  ],

  // Avvisi da ignorare
  onwarn(warning, warn) {
    // Ignora warning sui moduli circolari in dipendenze note
    if (warning.code === 'CIRCULAR_DEPENDENCY') return;
    warn(warning);
  },
};
```

La differenza chiave tra Rollup e Vite library mode e' che Rollup offre un controllo piu' granulare sull'output (formati multipli nella stessa configurazione, configurazione UMD avanzata, output separati per sotto-moduli), mentre Vite library mode e' piu' semplice da configurare per i casi comuni. Per librerie che devono supportare contemporaneamente ESM, CJS e UMD con configurazioni diverse per ciascun formato, Rollup diretto rimane la scelta superiore.

---

## Package Manager

La scelta del package manager influenza la velocità di installazione, l'utilizzo dello spazio disco, la gestione delle dipendenze e la riproducibilità dei build.

### Confronto npm vs pnpm vs yarn vs bun

| Caratteristica | npm | pnpm | yarn (v4 Berry) | bun |
|---|---|---|---|---|
| **Velocità installazione** | Lenta | Molto veloce | Veloce | Estremamente veloce |
| **Spazio disco** | Duplicati per progetto | Content-addressable store condiviso | PnP (zero-installs) o node_modules | node_modules |
| **Lockfile** | `package-lock.json` | `pnpm-lock.yaml` | `yarn.lock` | `bun.lock` |
| **Monorepo nativo** | Workspaces (base) | Workspaces (eccellente) | Workspaces (maturo) | Workspaces (base) |
| **Strict dependency** | No (hoisting) | Si (struttura isolata) | Si (PnP) | No (hoisting) |
| **Compatibilita** | Universale | Ottima | Richiede configurazione | In crescita |
| **Script runner** | `npm run` | `pnpm run` | `yarn run` | `bun run` (nativo, veloce) |

```bash
# pnpm — installazione e comandi principali
npm install -g pnpm

pnpm install                    # Installa tutte le dipendenze
pnpm add react react-dom       # Aggiunge dipendenze
pnpm add -D vitest              # Aggiunge dev dependency
pnpm remove lodash              # Rimuove una dipendenza
pnpm update --latest            # Aggiorna tutto all'ultima versione
pnpm run build                  # Esegue uno script
pnpm dlx create-vite@latest     # Esegue un pacchetto senza installarlo (npx equivalente)

# Workspace (monorepo) con pnpm
pnpm --filter @myorg/web build  # Esegue build solo nel pacchetto specificato
pnpm -r run test                # Esegue test in tutti i pacchetti
```

pnpm è la scelta raccomandata per la maggior parte dei progetti grazie alla combinazione di velocità, risparmio di spazio disco e gestione rigorosa delle dipendenze che previene il phantom dependency problem.

---

## Linting e Formatting

Una codebase consistente richiede strumenti automatici che impongano convenzioni di stile e catturino errori comuni prima che raggiungano la code review.

### ESLint — Flat Config

A partire dalla versione 9, ESLint utilizza il sistema flat config (`eslint.config.js`) come formato predefinito, sostituendo il precedente `.eslintrc.*`:

```javascript
// eslint.config.js — configurazione flat per un progetto React + TypeScript
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import importPlugin from 'eslint-plugin-import';
import prettierConfig from 'eslint-config-prettier';

export default tseslint.config(
  // Configurazione base JavaScript
  js.configs.recommended,

  // Configurazione TypeScript
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // React
  {
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off', // Non necessario con React 17+
      'react/prop-types': 'off', // Usiamo TypeScript
    },
    settings: {
      react: { version: 'detect' },
    },
  },

  // Import ordering
  {
    plugins: { import: importPlugin },
    rules: {
      'import/order': [
        'error',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            'parent',
            'sibling',
            'index',
          ],
          'newlines-between': 'always',
          alphabetize: { order: 'asc' },
        },
      ],
      'import/no-duplicates': 'error',
    },
  },

  // Regole personalizzate
  {
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },

  // Disabilita regole che confliggono con Prettier
  prettierConfig,

  // Ignora file e directory
  {
    ignores: ['dist/', 'node_modules/', '*.config.js', 'coverage/'],
  },
);
```

### Prettier

Prettier formatta il codice automaticamente, eliminando dibattiti sullo stile. La configurazione è minimale:

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 80,
  "tabWidth": 2,
  "arrowParens": "always",
  "endOfLine": "lf",
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### eslint-config-prettier

Il pacchetto `eslint-config-prettier` disabilita tutte le regole ESLint che confliggono con Prettier, garantendo che i due strumenti non producano indicazioni contraddittorie. Va sempre aggiunto come ultimo elemento nell'array di configurazione.

### lint-staged

`lint-staged` esegue linting e formatting solo sui file staged in git, rendendo il processo pre-commit veloce anche in codebase grandi:

```json
// package.json
{
  "scripts": {
    "lint": "eslint .",
    "format": "prettier --write .",
    "prepare": "husky"
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,css,scss}": [
      "prettier --write"
    ]
  }
}
```

```bash
# Installazione e configurazione con Husky
pnpm add -D husky lint-staged
pnpm exec husky init

# .husky/pre-commit
pnpm exec lint-staged
```

---

## Docker per Applicazioni Web

Docker garantisce che l'applicazione funzioni in modo identico in ogni ambiente, dallo sviluppo locale alla produzione. Per le applicazioni web, Docker è particolarmente utile per creare immagini di produzione leggere e riproducibili.

### Multi-Stage Dockerfile per Node.js

Un Dockerfile multi-stage separa le fasi di build dall'immagine finale, riducendo drasticamente la dimensione dell'immagine:

```dockerfile
# Dockerfile — Multi-stage build per applicazione Node.js

# ─── Stage 1: dipendenze ─────────────────────────────
FROM node:22-alpine AS deps
WORKDIR /app

# Copia solo i file necessari per l'installazione delle dipendenze
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@latest --activate
RUN pnpm install --frozen-lockfile --prod=false

# ─── Stage 2: build ──────────────────────────────────
FROM node:22-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build dell'applicazione
ENV NODE_ENV=production
RUN corepack enable && corepack prepare pnpm@latest --activate
RUN pnpm run build

# ─── Stage 3: produzione (solo per app con server Node) ──
FROM node:22-alpine AS runner
WORKDIR /app

# Utente non-root per sicurezza
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

# Copia solo gli artefatti necessari
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER appuser
EXPOSE 3000

ENV NODE_ENV=production
CMD ["node", "dist/server.js"]
```

### Nginx per SPA

Le Single Page Application non necessitano di un server Node.js in produzione. Nginx serve i file statici con performance eccellenti:

```dockerfile
# Dockerfile — SPA con Nginx
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@latest --activate
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

# ─── Immagine finale con Nginx ───────────────────────
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf — configurazione per SPA
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Compressione Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml;
    gzip_min_length 1000;

    # Cache aggressiva per asset con hash (immutabili)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Nessuna cache per index.html (entry point)
    location = /index.html {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Fallback per client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Header di sicurezza
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

### Docker Compose per Sviluppo e Produzione

```yaml
# docker-compose.yml — ambiente di sviluppo
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      # Monta il codice sorgente per hot-reload
      - .:/app
      - /app/node_modules  # Esclude node_modules dal mount
    environment:
      - NODE_ENV=development
      - VITE_API_BASE_URL=http://api:8080
    depends_on:
      - api
      - db

  api:
    build:
      context: ./backend
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

```yaml
# docker-compose.prod.yml — override per produzione
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "80:80"
    restart: unless-stopped
    environment:
      - NODE_ENV=production

  api:
    build:
      context: ./backend
      target: production
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}

  db:
    restart: unless-stopped
    volumes:
      - /data/postgres:/var/lib/postgresql/data
```

```bash
# Comandi Docker Compose
docker compose up -d                              # Sviluppo
docker compose -f docker-compose.yml \
  -f docker-compose.prod.yml up -d --build        # Produzione
```

---

## CI/CD Pipeline

L'automazione del processo di build, test e deployment tramite CI/CD elimina gli errori manuali e garantisce che ogni modifica venga validata prima di raggiungere la produzione.

### GitHub Actions — Pipeline Completa

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '22'
  PNPM_VERSION: '9'

jobs:
  # ─── Lint e Type Check ─────────────────────────────
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm run lint
      - run: pnpm run typecheck

  # ─── Test ──────────────────────────────────────────
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm run test -- --coverage

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  # ─── Build ─────────────────────────────────────────
  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  # ─── Deploy a Produzione (solo su push in main) ───
  deploy:
    name: Deploy Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://myapp.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      # Esempio: deploy su Vercel
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### Preview Deployments su Pull Request

Le preview deployments creano un ambiente unico per ogni pull request, permettendo ai reviewer di testare le modifiche prima del merge:

```yaml
# .github/workflows/preview.yml
name: Preview Deployment

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  preview:
    name: Deploy Preview
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: '9'

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm run build

      - name: Deploy Preview to Vercel
        id: deploy
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Comment PR with preview URL
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Preview Deployment

              La preview e' disponibile su: ${{ steps.deploy.outputs.preview-url }}

              Commit: \`${context.sha.substring(0, 7)}\``
            });
```

---

## Hosting e Deployment

La scelta della piattaforma di hosting dipende dal tipo di applicazione (statica, SSR, API), dal budget, dai requisiti di performance e dalla complessità operativa accettabile.

### Vercel

Vercel eccelle nel deployment di applicazioni frontend e framework full-stack come Next.js. Offre serverless functions, edge functions e un sistema di preview deployments integrato:

```json
// vercel.json — configurazione
{
  "buildCommand": "pnpm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ],
  "functions": {
    "api/**/*.ts": {
      "memory": 256,
      "maxDuration": 10
    }
  },
  "crons": [
    {
      "path": "/api/cron/cleanup",
      "schedule": "0 3 * * *"
    }
  ]
}
```

```typescript
// api/hello.ts — Serverless Function su Vercel
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  const { name } = req.query;
  res.status(200).json({ message: `Ciao, ${name || 'mondo'}!` });
}
```

```typescript
// Edge Function — esecuzione globale a bassa latenza
export const config = { runtime: 'edge' };

export default async function handler(request: Request) {
  const { searchParams } = new URL(request.url);
  const country = request.headers.get('x-vercel-ip-country') || 'XX';

  return new Response(
    JSON.stringify({ country, greeting: `Benvenuto da ${country}` }),
    { headers: { 'Content-Type': 'application/json' } },
  );
}
```

### Netlify

Netlify offre funzionalità simili a Vercel con un focus su siti statici e JAMstack. La configurazione avviene tramite `netlify.toml`:

```toml
# netlify.toml
[build]
  command = "pnpm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

### AWS S3 + CloudFront

Per il massimo controllo, la combinazione S3 + CloudFront offre hosting statico scalabile con CDN globale:

```bash
# Deploy di una SPA su S3 con invalidazione CloudFront
aws s3 sync dist/ s3://my-app-bucket \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html" \
  --exclude "*.json"

# index.html senza cache
aws s3 cp dist/index.html s3://my-app-bucket/index.html \
  --cache-control "no-cache, no-store, must-revalidate"

# Invalida la cache CloudFront
aws cloudfront create-invalidation \
  --distribution-id E1234567890 \
  --paths "/index.html" "/manifest.json"
```

### Railway, Render e Fly.io

Queste piattaforme PaaS offrono un'esperienza di deployment semplificata per applicazioni full-stack che necessitano di un server:

- **Railway**: deployment da Git con supporto nativo per PostgreSQL, Redis e cron jobs. Pricing basato sull'utilizzo.
- **Render**: simile a Railway, con un tier gratuito più generoso. Supporta web services, static sites, cron jobs e database.
- **Fly.io**: deploy di container Docker in data center globali. Eccellente per applicazioni che richiedono bassa latenza in regioni specifiche. Utilizza un formato di configurazione `fly.toml`.

### Self-Hosted: Nginx + PM2

Per il deployment su VPS o server dedicati, la combinazione Nginx come reverse proxy e PM2 come process manager per Node.js è la soluzione standard:

```nginx
# /etc/nginx/sites-available/myapp.conf
server {
    listen 80;
    server_name myapp.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name myapp.example.com;

    ssl_certificate /etc/letsencrypt/live/myapp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myapp.example.com/privkey.pem;

    # Proxy verso l'app Node.js gestita da PM2
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Servire asset statici direttamente da Nginx
    location /assets/ {
        alias /var/www/myapp/dist/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```javascript
// ecosystem.config.cjs — configurazione PM2
module.exports = {
  apps: [
    {
      name: 'myapp',
      script: './dist/server.js',
      instances: 'max',            // Utilizza tutti i core CPU
      exec_mode: 'cluster',        // Modalita cluster per load balancing
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      max_memory_restart: '512M',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/var/log/pm2/myapp-error.log',
      out_file: '/var/log/pm2/myapp-out.log',
    },
  ],
};
```

```bash
# Comandi PM2
pm2 start ecosystem.config.cjs --env production
pm2 reload myapp          # Zero-downtime reload
pm2 monit                 # Monitor in tempo reale
pm2 logs myapp            # Visualizza i log
pm2 save                  # Salva la lista dei processi
pm2 startup               # Configura l'avvio automatico al boot
```

### Coolify

Coolify è una piattaforma open-source self-hosted che replica l'esperienza di Vercel/Netlify sul proprio server. Si installa su qualsiasi VPS e gestisce deployment automatici da Git, certificati SSL tramite Let's Encrypt, database, e monitoraggio:

```bash
# Installazione di Coolify su un VPS
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Coolify supporta deployment di applicazioni Docker, Nixpacks (build automatico simile a Heroku buildpacks), Dockerfile personalizzati, e siti statici. Offre un'interfaccia web per la gestione dei progetti, variabili d'ambiente, domini, e webhook per il deployment automatico su push.

### Cloudflare Pages: Edge-First Deployment

Cloudflare Pages si distingue per l'integrazione nativa con l'ecosistema Cloudflare. Oltre all'hosting statico, offre Cloudflare Workers per logica server-side eseguita sull'edge, D1 per database SQL distribuiti, R2 per object storage, e KV per coppie chiave-valore. Questa combinazione permette di costruire applicazioni full-stack interamente sulla rete edge di Cloudflare.

```toml
# wrangler.toml — configurazione Cloudflare Pages con Functions
name = "my-app"
compatibility_date = "2025-01-01"
pages_build_output_dir = "./dist"

# Binding per servizi Cloudflare
[[d1_databases]]
binding = "DB"
database_name = "my-app-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

[[r2_buckets]]
binding = "ASSETS"
bucket_name = "my-app-assets"

[[kv_namespaces]]
binding = "CACHE"
id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

[vars]
API_VERSION = "v2"
```

```typescript
// functions/api/users.ts — Cloudflare Pages Function
interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
}

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { env, request } = context;
  const url = new URL(request.url);
  const page = parseInt(url.searchParams.get('page') || '1');

  // Verifica cache KV
  const cacheKey = `users:page:${page}`;
  const cached = await env.CACHE.get(cacheKey);
  if (cached) {
    return new Response(cached, {
      headers: { 'Content-Type': 'application/json', 'X-Cache': 'HIT' },
    });
  }

  // Query D1
  const { results } = await env.DB.prepare(
    'SELECT id, name, email FROM users LIMIT 20 OFFSET ?',
  )
    .bind((page - 1) * 20)
    .all();

  const body = JSON.stringify({ data: results, page });

  // Salva in cache per 5 minuti
  await env.CACHE.put(cacheKey, body, { expirationTtl: 300 });

  return new Response(body, {
    headers: { 'Content-Type': 'application/json', 'X-Cache': 'MISS' },
  });
};
```

Cloudflare Pages offre un tier gratuito estremamente generoso: 500 build al mese, larghezza di banda illimitata, e preview deployment automatici per ogni branch e pull request. Il pricing e' prevedibile e spesso risulta a costo zero per progetti personali e piccoli team.

### AWS Amplify: Integrazione con l'Ecosistema AWS

AWS Amplify semplifica il deployment di applicazioni frontend con integrazione nativa verso i servizi AWS. Supporta build automatiche da Git, preview deployment per branch, e SSR tramite Lambda@Edge. La configurazione avviene tramite un file `amplify.yml`:

```yaml
# amplify.yml — configurazione di build AWS Amplify
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - corepack enable
        - corepack prepare pnpm@latest --activate
        - pnpm install --frozen-lockfile
    build:
      commands:
        - pnpm run build
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
      - .pnpm-store/**/*

  # Configurazione custom headers
  customHeaders:
    - pattern: '/assets/**'
      headers:
        - key: 'Cache-Control'
          value: 'public, max-age=31536000, immutable'
    - pattern: '/**'
      headers:
        - key: 'X-Frame-Options'
          value: 'DENY'
        - key: 'X-Content-Type-Options'
          value: 'nosniff'
```

Il punto di forza di Amplify e' l'integrazione con Cognito (autenticazione), AppSync (GraphQL), DynamoDB e S3, che permette di costruire backend serverless completi senza lasciare l'ecosistema AWS. Il punto debole e' la complessita' tipica di AWS e un pricing che puo' diventare difficile da prevedere quando l'applicazione scala e utilizza molti servizi interconnessi.

### Confronto Piattaforme di Deployment

| Caratteristica | Vercel | Netlify | Cloudflare Pages | AWS Amplify | Railway |
|---|---|---|---|---|---|
| **Specializzazione** | Next.js, React | JAMstack, statico | Edge-first, Workers | Ecosistema AWS | Full-stack, Docker |
| **Serverless Functions** | Si (Node, Edge) | Si (AWS Lambda) | Si (Workers) | Si (Lambda) | Container persistenti |
| **Database integrato** | Postgres (Neon) | No (addon) | D1 (SQLite dist.) | DynamoDB, Aurora | Postgres, Redis |
| **Preview deploy** | Automatico | Automatico | Automatico | Automatico | Manuale |
| **Edge network** | Globale | Globale | 300+ citta | CloudFront | Regioni limitate |
| **Free tier** | 100GB BW/mese | 100GB BW/mese | BW illimitata | 5GB/mese | $5 credito/mese |
| **SSR nativo** | Next.js, SvelteKit | Astro, SvelteKit | Qualsiasi framework | Next.js, Nuxt | Qualsiasi framework |
| **Monorepo** | Nativo | Plugin | Manuale | Nativo | Manuale |
| **Self-hostable** | No | No | No | No | No |
| **CLI deploy** | `vercel` | `netlify deploy` | `wrangler pages` | `amplify push` | `railway up` |

La scelta della piattaforma dipende dal contesto: Vercel domina per progetti Next.js grazie all'integrazione nativa del framework con la piattaforma. Cloudflare Pages offre il miglior rapporto costo/performance per siti statici e applicazioni edge. AWS Amplify e' la scelta naturale per team gia' investiti nell'ecosistema AWS. Railway eccelle per applicazioni che richiedono processi persistenti, database gestiti e deployment basati su container.

### Strategie di Deployment Avanzate

Oltre al deployment diretto, esistono strategie avanzate per minimizzare il rischio e il downtime durante il rilascio.

**Blue-Green Deployment** mantiene due ambienti identici (blue e green). Il traffico e' instradato verso uno dei due. Il deploy avviene sull'ambiente inattivo, e dopo la verifica il traffico viene commutato. In caso di problemi, il rollback e' istantaneo: basta tornare all'ambiente precedente.

**Canary Deployment** rilascia la nuova versione a una percentuale ridotta di utenti (tipicamente 1-5%), monitorando metriche chiave (error rate, latenza, conversioni). Se le metriche sono positive, la percentuale viene gradualmente aumentata fino al 100%. Vercel supporta questa strategia tramite le Edge Config e i Skew Protection.

**Rolling Deployment** aggiorna le istanze una alla volta in un cluster. Ogni istanza viene tolta dal load balancer, aggiornata, e reinserita. Questo approccio e' tipico dei deployment Kubernetes e Docker Swarm.

```yaml
# Esempio: canary deployment con Vercel usando skew protection
# vercel.json
{
  "skewProtection": "60",
}
# Le Edge Config consentono di indirizzare percentuali di traffico
# verso versioni specifiche del deployment
```

---

## CI/CD Avanzato

### GitHub Actions: Strategie di Caching Avanzate

Il caching corretto e' il singolo fattore con maggiore impatto sui tempi di esecuzione delle pipeline CI/CD. Una strategia di caching ben progettata puo' ridurre i tempi di build del 40-80%.

```yaml
# .github/workflows/ci.yml — caching avanzato
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: '9'

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'  # Cache automatica della store pnpm

      # Cache della directory di build di Vite
      - name: Cache Vite build
        uses: actions/cache@v4
        with:
          path: |
            node_modules/.vite
            node_modules/.cache
          key: vite-${{ runner.os }}-${{ hashFiles('pnpm-lock.yaml') }}-${{ hashFiles('src/**') }}
          restore-keys: |
            vite-${{ runner.os }}-${{ hashFiles('pnpm-lock.yaml') }}-
            vite-${{ runner.os }}-

      # Cache dei risultati ESLint
      - name: Cache ESLint
        uses: actions/cache@v4
        with:
          path: .eslintcache
          key: eslint-${{ runner.os }}-${{ hashFiles('eslint.config.js') }}-${{ github.sha }}
          restore-keys: |
            eslint-${{ runner.os }}-${{ hashFiles('eslint.config.js') }}-

      # Cache della store Turborepo (per monorepo)
      - name: Cache Turborepo
        uses: actions/cache@v4
        with:
          path: .turbo
          key: turbo-${{ runner.os }}-${{ hashFiles('pnpm-lock.yaml') }}-${{ github.sha }}
          restore-keys: |
            turbo-${{ runner.os }}-${{ hashFiles('pnpm-lock.yaml') }}-
            turbo-${{ runner.os }}-

      - run: pnpm install --frozen-lockfile
      - run: pnpm run lint --cache --cache-location .eslintcache
      - run: pnpm run build
```

La strategia di caching si basa su chiavi composite: la chiave primaria include l'hash del lockfile e del codice sorgente per una corrispondenza esatta, mentre le `restore-keys` forniscono fallback progressivamente meno specifici per cache hit parziali. Questo garantisce che la cache sia utilizzata anche quando il codice cambia (con le dipendenze invariate), fornendo comunque un'installazione piu' rapida.

### GitHub Actions: Workflow Riutilizzabili

Per organizzazioni con piu' repository, i workflow riutilizzabili evitano la duplicazione della configurazione CI/CD:

```yaml
# .github/workflows/reusable-frontend-ci.yml
name: Frontend CI (Reusable)

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '22'
      build-command:
        type: string
        default: 'pnpm run build'
      test-command:
        type: string
        default: 'pnpm run test'
    secrets:
      VERCEL_TOKEN:
        required: false
      SENTRY_AUTH_TOKEN:
        required: false

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: '9'

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm run lint

      - name: Type Check
        run: pnpm run typecheck

      - name: Test
        run: ${{ inputs.test-command }}

      - name: Build
        run: ${{ inputs.build-command }}

      # Upload source maps a Sentry se il token e' disponibile
      - name: Upload Source Maps
        if: ${{ secrets.SENTRY_AUTH_TOKEN != '' }}
        run: pnpm exec sentry-cli sourcemaps upload ./dist
        env:
          SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
```

```yaml
# .github/workflows/ci.yml — consumo del workflow riutilizzabile
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  frontend:
    uses: ./.github/workflows/reusable-frontend-ci.yml
    with:
      node-version: '22'
      build-command: 'pnpm run build:production'
    secrets:
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
      SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
```

### Deployment Strategies nel CI/CD

Una pipeline CI/CD matura implementa strategie di deployment differenziate in base al contesto:

```yaml
# .github/workflows/deploy.yml — deployment con approval e smoke test
name: Production Deploy

on:
  push:
    branches: [main]

jobs:
  # Smoke test post-deploy
  smoke-test:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Wait for deployment
        run: sleep 30

      - name: Health check
        run: |
          STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
            https://myapp.example.com/api/health)
          if [ "$STATUS" != "200" ]; then
            echo "Health check failed with status $STATUS"
            exit 1
          fi

      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v12
        with:
          urls: |
            https://myapp.example.com
            https://myapp.example.com/dashboard
          uploadArtifacts: true
          temporaryPublicStorage: true
          budgetPath: ./lighthouse-budget.json

  # Rollback automatico se lo smoke test fallisce
  rollback:
    needs: smoke-test
    if: failure()
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Rollback to previous deployment
        run: |
          vercel rollback --token=${{ secrets.VERCEL_TOKEN }}
          echo "Rollback eseguito con successo"
```

---

## CDN e Ottimizzazione degli Asset

### Concetto di CDN

Un Content Delivery Network (CDN) distribuisce copie degli asset statici in server edge distribuiti globalmente. Quando un utente richiede una risorsa, il CDN la serve dal nodo piu' vicino geograficamente, riducendo la latenza. Servizi come CloudFront, Cloudflare, Fastly e Bunny.net operano come CDN, ma anche Vercel e Netlify includono un CDN integrato.

### Asset Hashing e Cache Busting

Vite genera automaticamente nomi file con hash basati sul contenuto (`main-a1b2c3d4.js`). Questo permette di impostare cache headers aggressivi (`max-age=31536000, immutable`) perche' ogni modifica al contenuto produce un hash diverso, quindi un URL diverso che non interferisce con la cache.

```
dist/
  index.html                      ← nessuna cache (entry point)
  assets/
    js/main-a1b2c3d4.js          ← cache immutabile (1 anno)
    js/vendor-e5f6g7h8.js        ← cache immutabile
    css/style-i9j0k1l2.css       ← cache immutabile
    img/logo-m3n4o5p6.svg        ← cache immutabile
```

### Ottimizzazione delle Immagini

Le immagini rappresentano spesso la maggior parte del peso di una pagina web. L'ottimizzazione include la conversione in formati moderni e il dimensionamento responsive:

```typescript
// vite.config.ts — con vite-plugin-image-optimizer
import { ViteImageOptimizer } from 'vite-plugin-image-optimizer';

export default defineConfig({
  plugins: [
    ViteImageOptimizer({
      png: { quality: 80 },
      jpeg: { quality: 75 },
      webp: { quality: 80 },
      avif: { quality: 65 },
    }),
  ],
});
```

```html
<!-- Utilizzo di formati moderni con fallback -->
<picture>
  <source srcset="/img/hero.avif" type="image/avif" />
  <source srcset="/img/hero.webp" type="image/webp" />
  <img src="/img/hero.jpg" alt="Hero image"
       loading="lazy" decoding="async"
       width="1200" height="630" />
</picture>
```

Per i framework come Next.js e Nuxt, i componenti `<Image>` integrati gestiscono automaticamente ottimizzazione, lazy loading e formati responsivi.

### Ottimizzazione dei Font

I font web possono causare layout shift (CLS) e rallentare il rendering. Le best practice includono:

```css
/* Precaricamento del font critico */
/* In index.html: */
/* <link rel="preload" href="/fonts/Inter-Variable.woff2"
         as="font" type="font/woff2" crossorigin /> */

/* Font-face con font-display: swap per evitare FOIT */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-Variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC;
}

/* Fallback metrica-compatibile per ridurre layout shift */
@font-face {
  font-family: 'Inter-fallback';
  src: local('Arial');
  ascent-override: 90.49%;
  descent-override: 22.56%;
  line-gap-override: 0%;
  size-adjust: 107.06%;
}

body {
  font-family: 'Inter', 'Inter-fallback', system-ui, sans-serif;
}
```

### Analisi del Bundle

L'analisi periodica del bundle identifica dipendenze eccessive, codice duplicato e opportunita' di ottimizzazione:

```bash
# Analisi con rollup-plugin-visualizer (integrato nella config Vite)
pnpm run build    # Genera stats.html se il plugin visualizer e' configurato

# Analisi della dimensione dei pacchetti importati
npx vite-bundle-visualizer

# Verifica della dimensione di un pacchetto prima di installarlo
npx bundlephobia <package-name>

# source-map-explorer per analisi dettagliata
npx source-map-explorer dist/assets/js/*.js
```

### Source Map in Produzione

Le source map mappano il codice minificato e bundled al codice sorgente originale, rendendo possibile il debugging di errori in produzione. Tuttavia, pubblicare le source map sul web server espone la struttura interna dell'applicazione, gli endpoint API interni, e potenzialmente segreti hardcoded. La strategia raccomandata e' generare source map nascoste e caricarle esclusivamente sul servizio di error tracking.

```typescript
// vite.config.ts — source map nascoste per produzione
export default defineConfig({
  build: {
    // 'hidden' genera i file .map senza il commento
    // //# sourceMappingURL= nel bundle finale
    sourcemap: 'hidden',
  },
});
```

```javascript
// webpack.config.js — source map nascoste
module.exports = {
  devtool: process.env.NODE_ENV === 'production'
    ? 'hidden-source-map'    // Genera .map senza riferimento nel bundle
    : 'eval-source-map',     // Veloce per sviluppo
};
```

Le tre strategie per le source map in produzione:

1. **Hidden Source Maps + Error Tracking (raccomandata)**: genera i file `.map` durante il build, caricali sul servizio di error tracking (Sentry, Datadog, Bugsnag), e non deployarli sul web server. Il servizio di error tracking usa le source map per decodificare gli stack trace degli errori, ma gli utenti finali non possono accedere ai file `.map`.

2. **Accesso Ristretto**: deploya i file `.map` sul server ma blocca l'accesso pubblico tramite regole Nginx o CDN. Gli sviluppatori interni possono caricare le source map manualmente nel browser DevTools per il debugging.

3. **Nessuna Generazione**: non generare source map in produzione. Questa strategia e' la piu' semplice ma elimina la possibilita' di debugging degli errori in produzione. Non raccomandata per applicazioni con necessita' di monitoraggio degli errori.

```yaml
# .github/workflows/ci.yml — upload source map a Sentry
- name: Build con source map nascoste
  run: pnpm run build
  env:
    VITE_SENTRY_DSN: ${{ secrets.SENTRY_DSN }}

- name: Upload source maps a Sentry
  run: |
    pnpm exec sentry-cli sourcemaps inject ./dist
    pnpm exec sentry-cli sourcemaps upload \
      --org my-org \
      --project my-project \
      --release ${{ github.sha }} \
      ./dist
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}

- name: Rimuovi source maps prima del deploy
  run: find dist -name '*.map' -delete
```

```nginx
# nginx.conf — blocco accesso pubblico ai file .map (strategia 2)
location ~* \.map$ {
    # Permetti solo dalla rete interna
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;

    # Oppure richiedi autenticazione
    # auth_basic "Source Maps";
    # auth_basic_user_file /etc/nginx/.htpasswd;
}
```

Le source map devono sempre includere `sourcesContent` (il codice sorgente originale embedded nel file `.map`). Senza `sourcesContent`, i servizi di error tracking possono mostrare nomi di file e numeri di riga, ma non il codice effettivo. In TypeScript, assicurati che `inlineSources: true` sia impostato nel `tsconfig.json`.

### Ottimizzazione Avanzata degli Asset

L'ottimizzazione degli asset va oltre le immagini e i font. Una strategia completa include la compressione, il lazy loading, il prefetching e la gestione intelligente della cache.

#### Compressione Brotli e Gzip

La compressione degli asset e' uno dei miglioramenti piu' impattanti sulle performance di caricamento. Brotli offre una compressione superiore del 15-25% rispetto a Gzip per asset testuali (JavaScript, CSS, HTML, SVG), con un costo computazionale marginalmente superiore.

```typescript
// vite.config.ts — pre-compressione degli asset
import { compression } from 'vite-plugin-compression2';

export default defineConfig({
  plugins: [
    // Pre-comprimi in Gzip per compatibilita' con browser meno recenti
    compression({
      algorithm: 'gzip',
      threshold: 1024,       // Comprimi solo file > 1KB
      deleteOriginalAssets: false,
    }),

    // Pre-comprimi in Brotli per browser moderni
    compression({
      algorithm: 'brotliCompress',
      threshold: 1024,
      compressionOptions: {
        params: {
          // Livello 11 per compressione massima (statica, fatta una volta)
          [Symbol.for('BrotliCompress.BROTLI_PARAM_QUALITY')]: 11,
        },
      },
    }),
  ],
});
```

```nginx
# nginx.conf — servire asset pre-compressi
# Brotli (richiede modulo ngx_http_brotli_module)
brotli_static on;

# Gzip fallback
gzip_static on;
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript
           text/xml application/xml application/xml+rss text/javascript
           image/svg+xml application/wasm;
gzip_min_length 1000;
gzip_comp_level 6;
```

#### Lazy Loading e Prefetching degli Asset

Il lazy loading ritarda il caricamento delle risorse non critiche fino a quando non sono necessarie, riducendo il payload iniziale. Il prefetching anticipa il caricamento di risorse che l'utente probabilmente richiedera', migliorando la percezione di velocita'.

```html
<!-- Prefetch per risorse di navigazione probabile -->
<link rel="prefetch" href="/dashboard/chunk-abc123.js" />
<link rel="prefetch" href="/dashboard/chunk-abc123.css" />

<!-- Preload per risorse critiche del percorso corrente -->
<link rel="preload" href="/fonts/Inter-Variable.woff2"
      as="font" type="font/woff2" crossorigin />
<link rel="preload" href="/hero-image.avif"
      as="image" type="image/avif" />

<!-- Preconnect per domini di terze parti -->
<link rel="preconnect" href="https://api.example.com" />
<link rel="dns-prefetch" href="https://analytics.example.com" />
```

```typescript
// Lazy loading di componenti React con route-based splitting
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Ogni import() crea un chunk separato caricato on-demand
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const Analytics = lazy(() =>
  import('./pages/Analytics').then((mod) => ({
    default: mod.AnalyticsPage,
  })),
);

function App() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  );
}
```

#### Ottimizzazione CSS

La separazione del CSS critico (above-the-fold) dal resto degli stili riduce il tempo di rendering iniziale. Il CSS critico viene inlined nel documento HTML, mentre il resto viene caricato in modo asincrono.

```typescript
// vite.config.ts — separazione CSS critico
import criticalCss from 'vite-plugin-critical';

export default defineConfig({
  plugins: [
    criticalCss({
      criticalUrl: 'http://localhost:3000',
      criticalBase: './dist',
      criticalPages: [
        { uri: '/', template: 'index' },
      ],
      criticalConfig: {
        inline: true,
        dimensions: [
          { width: 375, height: 667 },   // Mobile
          { width: 1440, height: 900 },  // Desktop
        ],
      },
    }),
  ],
});
```

```css
/* Utilizzo di CSS layers per controllare la specificita'
   e facilitare il tree shaking del CSS */
@layer reset, tokens, base, components, utilities;

@layer tokens {
  :root {
    --color-primary: oklch(65% 0.25 250);
    --space-unit: 0.25rem;
  }
}

@layer base {
  body {
    font-family: 'Inter', system-ui, sans-serif;
    line-height: 1.5;
  }
}
```

### CDN: Configurazione Avanzata

Un CDN ben configurato e' il singolo miglioramento piu' impattante sulla latenza percepita dagli utenti. La configurazione deve bilanciare tre obiettivi: massimizzare il cache hit ratio, minimizzare il TTFB (Time To First Byte), e garantire che gli utenti ricevano sempre la versione corrente dell'applicazione.

```nginx
# Configurazione cache headers completa per un'applicazione SPA
server {
    # Asset immutabili (JavaScript, CSS, immagini con hash)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
        add_header Vary "Accept-Encoding";

        # Security headers
        add_header X-Content-Type-Options "nosniff" always;
    }

    # Font con cache lunga
    location /fonts/ {
        expires 6M;
        add_header Cache-Control "public, max-age=15768000";
        add_header Access-Control-Allow-Origin "*";
    }

    # Immagini caricate dagli utenti (senza hash nel nome)
    location /uploads/ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800, must-revalidate";
    }

    # index.html — NESSUNA cache
    location = /index.html {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate";
        add_header Pragma "no-cache";
    }

    # Service Worker — nessuna cache per aggiornamenti immediati
    location = /sw.js {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # API reverse proxy — nessuna cache dal CDN
    location /api/ {
        proxy_pass http://backend:8080;
        add_header Cache-Control "no-store";
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

La strategia di invalidazione della cache e' critica. Per gli asset con content hash nel nome file (`main-a1b2c3d4.js`), l'invalidazione e' automatica: ogni modifica produce un nuovo hash, quindi un nuovo URL. Per `index.html` (l'unico entry point senza hash), il browser verifica sempre la versione aggiornata con il server. Questo schema garantisce che gli utenti ricevano sempre la versione corrente dell'applicazione senza sacrificare la cache degli asset statici.

---

## Monorepo

Un monorepo contiene piu' progetti (pacchetti) in un singolo repository, facilitando la condivisione di codice, la consistenza delle dipendenze e i processi di build coordinati.

### Struttura Tipica

```
my-monorepo/
  packages/
    web/              # App frontend (React/Vue/Svelte)
    api/              # Backend Node.js
    ui/               # Libreria componenti condivisa
    shared/           # Tipi TypeScript e utilities condivise
    config/           # Configurazioni condivise (ESLint, TypeScript)
  package.json        # Root package.json
  pnpm-workspace.yaml # Definizione workspace (pnpm)
  turbo.json          # Configurazione Turborepo
```

### pnpm Workspaces

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'
```

```json
// packages/web/package.json
{
  "name": "@myorg/web",
  "dependencies": {
    "@myorg/ui": "workspace:*",
    "@myorg/shared": "workspace:*",
    "react": "^19.0.0"
  }
}
```

```bash
# Comandi pnpm workspace
pnpm --filter @myorg/web add react-router-dom    # Aggiunge dipendenza a un pacchetto
pnpm --filter @myorg/web dev                     # Avvia il dev server di un pacchetto
pnpm -r run build                                 # Build di tutti i pacchetti
pnpm --filter @myorg/ui... run build              # Build del pacchetto e tutte le sue dipendenze
```

### Turborepo

Turborepo, sviluppato da Vercel, e' un build system per monorepo che gestisce il task scheduling, il caching e il parallelismo:

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"],
      "env": ["NODE_ENV", "VITE_API_BASE_URL"]
    },
    "dev": {
      "dependsOn": ["^build"],
      "persistent": true,
      "cache": false
    },
    "lint": {
      "dependsOn": ["^build"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "typecheck": {
      "dependsOn": ["^build"]
    }
  }
}
```

```bash
# Comandi Turborepo
turbo run build                    # Build di tutti i pacchetti (con cache)
turbo run build --filter=@myorg/web  # Build di un pacchetto specifico
turbo run lint test --parallel      # Esegue lint e test in parallelo
turbo run build --dry               # Mostra cosa verrebbe eseguito
turbo run build --force             # Ignora la cache
```

Turborepo genera un hash per ogni task basato su input, dipendenze e variabili d'ambiente. Se l'hash corrisponde a un risultato precedente nella cache, il task viene saltato e l'output viene ripristinato dalla cache, riducendo i tempi di build da minuti a millisecondi.

### Nx

Nx, sviluppato da Nrwl, e' un'alternativa matura a Turborepo con funzionalita' aggiuntive:

```bash
# Inizializzazione di un workspace Nx
npx create-nx-workspace@latest my-workspace --preset=ts

# Comandi principali
nx run @myorg/web:build             # Build di un progetto
nx affected --target=build          # Build solo dei progetti modificati
nx graph                            # Visualizza il grafo delle dipendenze
nx migrate latest                   # Aggiorna Nx e le sue dipendenze
```

Nx offre un sistema di plugin per framework specifici (React, Angular, Node.js), generatori di codice, e il concetto di "affected" che calcola automaticamente quali progetti sono impattati da una modifica, eseguendo solo i task necessari. Include anche una dashboard remota (Nx Cloud) per la condivisione della cache tra sviluppatori e CI.

La scelta tra Turborepo e Nx dipende dalle necessita': Turborepo e' piu' semplice e si integra bene con l'ecosistema Vercel, mentre Nx offre piu' funzionalita' out-of-the-box ma con una curva di apprendimento superiore.

### Turborepo vs Nx: Confronto Approfondito

La scelta tra Turborepo e Nx e' una delle decisioni architetturali piu' importanti quando si adotta una strategia monorepo. Le due soluzioni hanno filosofie profondamente diverse.

**Turborepo** e' un task runner intelligente. Si posiziona sopra le workspace native del package manager (pnpm, npm, yarn) e aggiunge caching, parallelizzazione e ordinamento delle dipendenze tra task. La sua configurazione e' minimale: un singolo file `turbo.json` che dichiara i task e le loro relazioni. L'integrazione con un monorepo esistente richiede meno di 10 minuti.

**Nx** e' un framework per monorepo completo. Oltre al task running e al caching, offre generatori di codice (scaffold di progetti, componenti, moduli), un sistema di plugin per framework specifici (React, Angular, NestJS, Express), analisi delle dipendenze con grafo visuale, e il concetto di "affected" che determina automaticamente quali progetti sono impattati da una modifica.

| Aspetto | Turborepo | Nx |
|---|---|---|
| **Filosofia** | Task runner leggero | Framework monorepo completo |
| **Setup iniziale** | < 10 minuti | 30-60 minuti |
| **Configurazione** | `turbo.json` (< 30 righe) | `nx.json` + `project.json` per progetto |
| **Caching locale** | Hash-based, automatico | Hash-based, automatico |
| **Remote caching** | Vercel (free/paid) | Nx Cloud (free/paid) |
| **Distributed execution** | No | Si (Nx Agents) |
| **Generatori di codice** | No | Si (molto potenti) |
| **Plugin ecosystem** | Minimale | Ampio (React, Angular, Node, etc.) |
| **Affected detection** | No | Si (granulare, basata su grafo) |
| **Grafo dipendenze** | Implicito (dal package.json) | Esplicito (visualizzabile) |
| **Supporto non-JS** | No | Si (Go, Rust, Python via plugin) |
| **Migrazione** | Facile (additive) | Complessa (richiede struttura Nx) |
| **Manutenzione** | Vercel | Nrwl (team dedicato) |

Per team di 1-10 sviluppatori con un monorepo JavaScript/TypeScript puro, Turborepo offre il miglior rapporto semplicita'/valore. Per organizzazioni con 10+ sviluppatori, monorepo poliglotti, o necessita' di code generation e CI distribuito, Nx giustifica la complessita' aggiuntiva.

### Remote Caching nei Monorepo

Il remote caching e' la funzionalita' che trasforma un monorepo da un'inconvenienza operativa a un vantaggio competitivo. Senza remote caching, ogni sviluppatore e ogni pipeline CI esegue tutti i task da zero. Con il remote caching, il risultato di un task eseguito da un membro del team o dalla CI viene condiviso con tutti, eliminando lavoro duplicato.

```bash
# Turborepo: abilitazione remote caching con Vercel
npx turbo login              # Autentica con Vercel
npx turbo link               # Collega il repo al progetto Vercel

# Ogni build successivo condivide la cache
turbo run build              # Cache MISS al primo run
turbo run build              # Cache HIT: < 100ms
```

```bash
# Nx: abilitazione remote caching con Nx Cloud
npx nx connect               # Collega a Nx Cloud

# Visualizza la dashboard della cache
npx nx show --web

# Esegui solo i task impattati dalla modifica corrente
npx nx affected --target=build
npx nx affected --target=test
```

Il remote caching funziona calcolando un hash deterministico di tutti gli input di un task: codice sorgente, dipendenze, variabili d'ambiente, e configurazione. Se l'hash corrisponde a un risultato nella cache remota, l'output viene scaricato e ripristinato localmente, saltando l'intera esecuzione del task. Per un build che richiede 2 minuti, il ripristino dalla cache richiede tipicamente 1-3 secondi.

### Monorepo: Gestione delle Dipendenze Interne

Un aspetto critico dei monorepo e' la gestione corretta delle dipendenze tra pacchetti interni. L'approccio varia in base al package manager e al build tool utilizzato.

```json
// packages/ui/package.json — libreria interna
{
  "name": "@myorg/ui",
  "version": "0.0.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": {
      "import": "./src/index.ts",
      "types": "./src/index.ts"
    },
    "./button": {
      "import": "./src/components/Button.tsx",
      "types": "./src/components/Button.tsx"
    }
  }
}
```

```json
// apps/web/package.json — applicazione che consuma la libreria
{
  "name": "@myorg/web",
  "dependencies": {
    "@myorg/ui": "workspace:*"
  }
}
```

L'approccio mostrato sopra, con `main` che punta direttamente al file sorgente TypeScript (`./src/index.ts`), e' chiamato **internal packages pattern**. Il bundler dell'applicazione (Vite, Next.js) compila direttamente il codice sorgente della libreria interna, eliminando la necessita' di un build step separato per i pacchetti condivisi. Questo semplifica enormemente lo sviluppo: le modifiche alla libreria sono immediatamente visibili nell'applicazione grazie all'HMR, senza necessita' di ricompilare la libreria.

---

## Docker Avanzato per Applicazioni Frontend

### Ottimizzazione della Dimensione delle Immagini

Le immagini Docker per applicazioni frontend possono essere ridotte drasticamente con tecniche mirate. L'obiettivo e' un'immagine finale sotto i 50MB per le SPA servite da Nginx.

```dockerfile
# Dockerfile — immagine ottimizzata per SPA (< 30MB)
FROM node:22-alpine AS builder
WORKDIR /app

# Installa solo le dipendenze necessarie
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@latest --activate \
    && pnpm install --frozen-lockfile

# Copia il codice sorgente e compila
COPY . .
RUN pnpm run build

# ─── Immagine finale: solo Nginx + asset statici ──────
FROM nginx:1.27-alpine-slim AS production

# Rimuovi configurazione di default e file non necessari
RUN rm -rf /usr/share/nginx/html/* \
    && rm /etc/nginx/conf.d/default.conf

# Copia configurazione custom e asset
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Utente non-root
RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chmod -R 755 /usr/share/nginx/html

# Healthcheck integrato
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80
USER nginx
CMD ["nginx", "-g", "daemon off;"]
```

```bash
# Verifica della dimensione dell'immagine
docker build -t myapp:prod .
docker images myapp:prod
# REPOSITORY    TAG     SIZE
# myapp         prod    25.3MB
```

### Docker: Layer Caching nel CI

Il caching dei layer Docker e' fondamentale per velocizzare le build nel CI. La strategia consiste nel separare le fasi che cambiano raramente (installazione dipendenze) da quelle che cambiano frequentemente (codice sorgente).

```yaml
# .github/workflows/docker-build.yml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.sha }}
            ghcr.io/${{ github.repository }}:latest
          # Cache dei layer tra build successive
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

La direttiva `cache-from: type=gha` utilizza il GitHub Actions cache come backend per i layer Docker. Il flag `mode=max` salva tutti i layer intermedi, non solo quelli dell'immagine finale, massimizzando il riutilizzo della cache nelle build successive.

---

## Gestione Avanzata degli Ambienti

La gestione degli ambienti in un progetto frontend moderno coinvolge variabili d'ambiente, feature flag, e configurazioni specifiche per ambiente che devono essere coordinate tra il codice, il CI/CD e la piattaforma di hosting.

### Pattern di Configurazione Multi-Ambiente

```typescript
// src/config/index.ts — configurazione centralizzata con validazione
import { z } from 'zod';

// Schema di validazione per le variabili d'ambiente
const baseSchema = z.object({
  API_BASE_URL: z.string().url(),
  APP_VERSION: z.string().default('0.0.0-dev'),
  ENVIRONMENT: z.enum(['development', 'staging', 'production']),
});

// Estensione dello schema per ambienti specifici
const devSchema = baseSchema.extend({
  DEBUG: z.coerce.boolean().default(true),
  MOCK_API: z.coerce.boolean().default(false),
});

const prodSchema = baseSchema.extend({
  SENTRY_DSN: z.string().url(),
  ANALYTICS_ID: z.string().min(1),
});

function loadConfig() {
  const env = {
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    APP_VERSION: import.meta.env.VITE_APP_VERSION,
    ENVIRONMENT: import.meta.env.MODE,
    SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
    ANALYTICS_ID: import.meta.env.VITE_ANALYTICS_ID,
    DEBUG: import.meta.env.VITE_DEBUG,
    MOCK_API: import.meta.env.VITE_MOCK_API,
  };

  const schema = import.meta.env.PROD ? prodSchema : devSchema;
  const result = schema.safeParse(env);

  if (!result.success) {
    const errors = result.error.flatten().fieldErrors;
    console.error('Configurazione non valida:', errors);
    throw new Error(
      `Variabili d'ambiente mancanti: ${Object.keys(errors).join(', ')}`,
    );
  }

  return Object.freeze(result.data);
}

export const config = loadConfig();
```

### Feature Flags Basati sull'Ambiente

I feature flag permettono di abilitare o disabilitare funzionalita' senza necessita' di un nuovo deployment. In combinazione con le variabili d'ambiente, creano un sistema flessibile per il rilascio graduale delle feature.

```typescript
// src/config/features.ts — feature flag system
interface FeatureFlags {
  readonly newDashboard: boolean;
  readonly darkMode: boolean;
  readonly experimentalSearch: boolean;
  readonly maintenanceMode: boolean;
}

// I flag possono provenire da variabili d'ambiente, API remota,
// o una combinazione di entrambi
function loadFeatureFlags(): FeatureFlags {
  return Object.freeze({
    newDashboard:
      import.meta.env.VITE_FF_NEW_DASHBOARD === 'true',
    darkMode:
      import.meta.env.VITE_FF_DARK_MODE !== 'false', // Default: true
    experimentalSearch:
      import.meta.env.VITE_FF_EXPERIMENTAL_SEARCH === 'true',
    maintenanceMode:
      import.meta.env.VITE_FF_MAINTENANCE === 'true',
  });
}

export const features = loadFeatureFlags();

// Utilizzo nei componenti
// if (features.newDashboard) { ... }
```

```bash
# .env.staging — feature flag attivi in staging
VITE_FF_NEW_DASHBOARD=true
VITE_FF_DARK_MODE=true
VITE_FF_EXPERIMENTAL_SEARCH=true
VITE_FF_MAINTENANCE=false

# .env.production — feature flag conservativi in produzione
VITE_FF_NEW_DASHBOARD=false
VITE_FF_DARK_MODE=true
VITE_FF_EXPERIMENTAL_SEARCH=false
VITE_FF_MAINTENANCE=false
```

Questo approccio e' adeguato per team piccoli con un numero limitato di flag. Per sistemi di feature flag piu' sofisticati con targeting per utente, percentuali di rollout, e A/B testing, soluzioni dedicate come LaunchDarkly, Unleash, o Flagsmith offrono funzionalita' avanzate con SDK client-side ottimizzati.

### Gestione dei Segreti nella Pipeline

I segreti (chiavi API, token di autenticazione, credenziali di database) non devono mai essere inclusi nel codice sorgente, nei commit, o negli artifact di build. Ogni piattaforma offre un meccanismo dedicato per la gestione sicura dei segreti.

```yaml
# GitHub Actions — gestione segreti
# I segreti sono configurati nelle Settings del repository
# e accessibili tramite ${{ secrets.NOME_SEGRETO }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production     # Usa i segreti dell'ambiente "production"
    steps:
      - name: Build con segreti
        run: pnpm run build
        env:
          # Le variabili VITE_ sono incluse nel bundle client
          # NON inserire segreti server-side qui
          VITE_API_BASE_URL: ${{ vars.API_BASE_URL }}  # vars = non segreti

      - name: Deploy
        run: |
          # I segreti server-side sono usati solo nella pipeline
          vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
```

La distinzione critica e' tra variabili client-side (prefisso `VITE_`, incluse nel bundle JavaScript visibile al browser) e variabili server-side (usate solo durante il build o nel server). Le chiavi API, i token di autenticazione e i DSN di servizi come Sentry possono essere esposti nel bundle client solo se sono progettati per l'uso pubblico. Le credenziali di database, i token con privilegi elevati, e le chiavi private non devono mai avere il prefisso `VITE_`.

---

## Best Practice

### Analisi Comparativa dei Build Tool

La scelta del build tool e' una decisione architetturale che impatta la developer experience, i tempi di build, la qualita' del bundle finale, e la complessita' di manutenzione. Questa tabella riassume le caratteristiche principali degli strumenti trattati in questo modulo.

| Caratteristica | Vite | Webpack 5 | esbuild | Turbopack | Rollup | Bun Bundler |
|---|---|---|---|---|---|---|
| **Linguaggio** | JS (Rollup/esbuild) | JavaScript | Go | Rust | JavaScript | Zig |
| **Dev server** | ESM nativo, istantaneo | Bundle completo, lento | Basilare | Incrementale, veloce | No (dev) | Basilare |
| **HMR** | ~20-50ms | ~200-500ms | Limitato | ~15-30ms | No | Limitato |
| **Tree shaking** | Eccellente (Rollup) | Buono | Buono | Buono | Eccellente | Buono |
| **Code splitting** | Automatico + manuale | Configurabile | Solo ESM | Automatico | Manuale | Limitato |
| **CSS handling** | Moduli, preprocessori | Via loader | Basilare | Moduli | Via plugin | Basilare |
| **Plugin ecosystem** | Ampio (Rollup compat.) | Enorme, maturo | Limitato | In crescita | Ampio, maturo | Minimale |
| **SSR** | Nativo | Via configurazione | No | Nativo (Next.js) | Via plugin | No |
| **Library mode** | Si | Si | Si | No | Si (eccellente) | Si |
| **Config complexity** | Bassa | Alta | Molto bassa | Bassa (Next.js) | Media | Molto bassa |
| **Standalone** | Si | Si | Si | No (solo Next.js) | Si | Si |
| **Maturita** | Stabile (v6) | Maturo (v5) | Stabile | Stabile per dev | Maturo (v4) | Beta |

#### Quando Usare Quale Strumento

- **Vite**: scelta predefinita per nuovi progetti SPA, SSR custom, e applicazioni full-stack con React, Vue, Svelte, o Solid. Il miglior equilibrio tra velocita', funzionalita', e semplicita'.

- **Webpack 5**: progetti legacy che non possono migrare, applicazioni con requisiti di Module Federation (micro-frontend), o configurazioni estremamente personalizzate non supportate da altri bundler.

- **esbuild**: build di librerie, transpilazione veloce di codice TypeScript, strumenti CLI, e script di backend dove l'HMR e il CSS avanzato non sono necessari.

- **Turbopack**: progetti Next.js dove la velocita' del dev server e' critica. Non disponibile al di fuori di Next.js.

- **Rollup**: pubblicazione di librerie npm dove il controllo granulare sull'output (formati multipli, external dependencies, tree shaking ottimale) e' prioritario.

- **Bun Bundler**: sperimentazione e progetti piccoli dove la velocita' di build e' l'unico requisito. Non ancora maturo per produzione complessa.

### Code Splitting: Strategie Approfondite

Il code splitting e' la tecnica che suddivide il bundle JavaScript in chunk separati, caricati dal browser solo quando necessari. Una strategia di code splitting ben progettata riduce il payload iniziale, migliora il Time to Interactive (TTI), e ottimizza l'utilizzo della cache.

Esistono tre approcci complementari:

1. **Route-based splitting**: ogni pagina o route dell'applicazione diventa un chunk separato. E' la strategia piu' comune e piu' impattante. L'utente scarica il codice solo per la pagina che sta visitando.

2. **Component-based splitting**: componenti pesanti (editor di testo ricco, grafici, mappe) vengono separati in chunk dedicati e caricati on-demand. Utile per componenti che appaiono solo in contesti specifici (modale, tab secondario).

3. **Vendor splitting**: le dipendenze di terze parti vengono raggruppate in chunk separati dal codice applicativo. Poiche' le dipendenze cambiano meno frequentemente del codice dell'applicazione, i chunk vendor rimangono nella cache del browser piu' a lungo.

```typescript
// vite.config.ts — strategia di vendor splitting avanzata
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;

          // Framework core: cambia raramente, cache lunga
          if (id.includes('react') || id.includes('react-dom')) {
            return 'framework';
          }

          // Router: cambia raramente
          if (id.includes('react-router')) {
            return 'router';
          }

          // State management
          if (id.includes('zustand') || id.includes('@tanstack/react-query')) {
            return 'state';
          }

          // Librerie UI pesanti
          if (id.includes('chart.js') || id.includes('d3')) {
            return 'charts';
          }

          // Editor di testo ricco
          if (id.includes('prosemirror') || id.includes('tiptap')) {
            return 'editor';
          }

          // Tutte le altre dipendenze
          return 'vendor';
        },
      },
    },
  },
});
```

La granularita' della strategia di splitting deve essere calibrata. Troppi chunk piccoli aumentano il numero di richieste HTTP e l'overhead di parsing. Troppo pochi chunk grandi annullano i benefici del code splitting. La regola empirica e' mirare a chunk tra 50KB e 200KB gzipped, con il bundle principale (entry point) sotto i 150KB gzipped.

### Budget di Performance per il Bundle

Definire budget di dimensione espliciti e' essenziale per prevenire la crescita incontrollata del bundle. I budget devono essere integrati nella pipeline CI/CD come gate di qualita' che bloccano il merge se superati.

```json
// bundlesize.config.json — definizione budget
{
  "files": [
    {
      "path": "dist/assets/js/framework-*.js",
      "maxSize": "50KB",
      "compression": "gzip"
    },
    {
      "path": "dist/assets/js/vendor-*.js",
      "maxSize": "100KB",
      "compression": "gzip"
    },
    {
      "path": "dist/assets/js/index-*.js",
      "maxSize": "80KB",
      "compression": "gzip"
    },
    {
      "path": "dist/assets/css/style-*.css",
      "maxSize": "30KB",
      "compression": "gzip"
    }
  ]
}
```

```yaml
# .github/workflows/ci.yml — check budget nel CI
- name: Check bundle size
  run: npx bundlesize --config bundlesize.config.json
```

### 1. Automatizza Ogni Fase della Pipeline

Nessun passaggio del processo di build e deployment dovrebbe richiedere intervento manuale. Configura CI/CD per eseguire lint, type check, test, build e deploy automaticamente su ogni push. L'automazione elimina errori umani, garantisce consistenza e accelera il ciclo di rilascio.

```yaml
# Esempio minimale: ogni push attiva l'intera pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

### 2. Tratta l'Infrastruttura come Codice

Ogni configurazione — Dockerfile, docker-compose, nginx.conf, CI/CD workflows, vercel.json — deve essere versionata nel repository. Questo garantisce la riproducibilita' dell'ambiente e permette la review delle modifiche infrastrutturali con lo stesso rigore del codice applicativo.

### 3. Isola gli Ambienti con le Variabili d'Ambiente

Non hardcodare URL, chiavi API, o qualsiasi configurazione specifica dell'ambiente nel codice. Utilizza variabili d'ambiente con file `.env` per lo sviluppo locale, secrets del CI/CD per la pipeline, e variabili d'ambiente della piattaforma di hosting per la produzione. Mantieni un file `.env.example` versionato con le chiavi necessarie (senza valori sensibili) come documentazione.

### 4. Implementa il Cache Busting Corretto

Configura il bundler per generare nomi file con content hash per tutti gli asset statici. Imposta `Cache-Control: public, max-age=31536000, immutable` per questi asset e `Cache-Control: no-cache` per `index.html`. Questo schema massimizza l'efficacia della cache senza rischiare di servire contenuti obsoleti.

### 5. Analizza Regolarmente il Bundle

Integra strumenti di analisi del bundle nella pipeline di sviluppo. Imposta budget di dimensione (`chunkSizeWarningLimit` in Vite) e monitora le tendenze nel tempo. Un bundle che cresce senza controllo degrada progressivamente la user experience, specialmente su connessioni lente e dispositivi mobile.

### 6. Adotta una Strategia di Preview Deployment

Ogni pull request dovrebbe generare un ambiente di preview isolato con un URL unico. Questo permette ai reviewer di verificare visivamente le modifiche, ai QA di testare le funzionalita' e agli stakeholder di approvare i cambiamenti prima del merge. Vercel e Netlify offrono questa funzionalita' nativamente.

### 7. Configura Rollback Rapidi

Il deployment non e' completo senza una strategia di rollback. Mantieni le versioni precedenti degli artefatti di build e configura un meccanismo per tornare rapidamente all'ultima versione stabile. Piattaforme come Vercel conservano automaticamente i deployment precedenti, permettendo il rollback con un click.

### 8. Minimizza la Superficie del Container

Le immagini Docker di produzione devono contenere solo il minimo indispensabile. Utilizza immagini base Alpine, multi-stage build per escludere le dipendenze di sviluppo, e utenti non-root per la sicurezza. Un'immagine piu' piccola si avvia piu' rapidamente, consuma meno risorse e presenta una superficie di attacco ridotta.

### 9. Centralizza le Configurazioni nel Monorepo

In un monorepo, condividi le configurazioni di ESLint, TypeScript, Prettier e testing in un pacchetto dedicato (`@myorg/config`). Ogni pacchetto estende la configurazione condivisa, garantendo consistenza e riducendo la duplicazione. Le modifiche alle regole si propagano automaticamente a tutti i pacchetti.

```json
// packages/config/tsconfig.base.json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "declaration": true,
    "declarationMap": true
  }
}

// packages/web/tsconfig.json
{
  "extends": "@myorg/config/tsconfig.base.json",
  "compilerOptions": {
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

### 10. Monitora le Performance Post-Deployment

Il deployment non termina con la pubblicazione del codice. Integra strumenti di monitoraggio delle performance reali (Real User Monitoring) come Sentry, Datadog, o Vercel Analytics per tracciare Core Web Vitals, errori JavaScript, e tempi di risposta delle API in produzione. Configura alert per regressioni delle performance e stabilisci baseline per ogni metrica chiave. Il feedback dai dati reali guida le priorita' di ottimizzazione meglio di qualsiasi benchmark sintetico.

---

## Riepilogo

La pipeline di build e deployment moderna e' un sistema complesso di strumenti interconnessi, ciascuno con un ruolo specifico nel trasformare il codice sorgente in un'applicazione accessibile agli utenti. Vite ha semplificato enormemente la configurazione del bundling, le piattaforme PaaS come Vercel hanno reso il deployment accessibile con zero configurazione infrastrutturale, e gli strumenti di CI/CD come GitHub Actions hanno automatizzato il ciclo di rilascio.

La chiave per una pipeline efficace non risiede nella scelta di strumenti specifici, ma nella comprensione dei principi sottostanti: automazione completa, riproducibilita' degli ambienti, ottimizzazione degli asset, monitoraggio continuo e capacita' di rollback rapido. Questi principi rimangono validi indipendentemente dall'evoluzione degli strumenti.

---

## Esercizi

### Esercizio 1 — Configurazione Vite Multi-Ambiente

**Obiettivo:** configurare un progetto Vite con gestione completa delle variabili d'ambiente per sviluppo, staging e produzione.

Crea un progetto React + TypeScript con Vite e configura:

- Tre file di ambiente: `.env.development`, `.env.staging`, `.env.production` con variabili `VITE_API_URL`, `VITE_SENTRY_DSN`, `VITE_FEATURE_FLAGS`
- Un file `src/config.ts` che esporta la configurazione tipizzata con validazione a runtime (fallisce all'avvio se manca una variabile obbligatoria)
- Script npm: `dev`, `build:staging`, `build:production` con il flag `--mode` appropriato
- Un plugin Vite custom che inietta la versione dal `package.json` e il commit hash di git come `VITE_APP_VERSION` e `VITE_COMMIT_SHA`
- Verifica che le variabili senza prefisso `VITE_` non vengano esposte al client

### Esercizio 2 — Ottimizzazione Bundle con Code Splitting

**Obiettivo:** ridurre il bundle JavaScript iniziale di un'applicazione React sotto i 150KB gzipped usando code splitting e tree shaking.

Parti da un progetto React con le dipendenze `lodash`, `date-fns`, `chart.js` e `react-markdown`:

- Configura `vite.config.ts` con `manualChunks` per separare le dipendenze di vendor in chunk distinti (react, charting, utility)
- Implementa lazy loading con `React.lazy()` e `Suspense` per le route non critiche
- Sostituisci l'import completo di lodash (`import _ from 'lodash'`) con import cherry-pick (`import debounce from 'lodash/debounce'`)
- Configura `rollup-plugin-visualizer` e genera il report del bundle
- Documenta la dimensione di ogni chunk prima e dopo l'ottimizzazione
- Il bundle principale (entry point) deve risultare sotto i 150KB gzipped

### Esercizio 3 — Pipeline CI/CD con GitHub Actions

**Obiettivo:** creare una pipeline CI/CD completa con build, test, preview deploy e produzione.

Scrivi un workflow `.github/workflows/ci.yml` che implementi:

- Job `lint`: esegue ESLint e Prettier check in parallelo
- Job `test`: esegue Vitest con coverage report e fallisce se la copertura scende sotto l'80%
- Job `build`: esegue `vite build` e salva la cartella `dist/` come artifact
- Job `preview`: su pull request, deploya una preview su Vercel usando `vercel --prebuilt` e commenta la PR con l'URL della preview
- Job `deploy`: su push al branch `main`, deploya in produzione su Vercel con `--prod`
- Configura caching per `node_modules` con hash del lockfile
- Aggiungi concurrency group per cancellare pipeline obsolete sulla stessa PR

### Esercizio 4 — Containerizzazione con Docker Multi-Stage

**Obiettivo:** creare un Dockerfile multi-stage ottimizzato per un'applicazione full-stack (React + Node.js/Express).

Implementa un setup Docker completo:

- Stage 1 (`deps`): installa le dipendenze con `npm ci --only=production` su immagine `node:20-alpine`
- Stage 2 (`build`): compila il frontend React con Vite e il backend TypeScript con `tsc`
- Stage 3 (`runtime`): immagine finale basata su `node:20-alpine` con solo gli artefatti necessari, utente non-root, healthcheck configurato
- `docker-compose.yml` con servizi `app`, `postgres`, `redis` con volumi, network dedicato e variabili d'ambiente da file `.env`
- `.dockerignore` che escluda `node_modules`, `.git`, file di test, documentazione
- L'immagine finale deve pesare meno di 200MB
- Verifica che il container si avvii correttamente con `docker compose up` e risponda su `http://localhost:3000`

### Esercizio 5 — Monorepo con Turborepo e Shared Config

**Obiettivo:** configurare un monorepo con Turborepo che condivida configurazioni di build, lint e TypeScript tra piu pacchetti.

Struttura il monorepo con:

- `apps/web`: applicazione Next.js
- `apps/api`: server Express con TypeScript
- `packages/ui`: libreria di componenti React condivisi
- `packages/config`: configurazioni condivise (ESLint, TypeScript, Prettier)
- `packages/types`: tipi TypeScript condivisi tra frontend e backend
- Configura `turbo.json` con pipeline per `build`, `lint`, `test` e `typecheck` con dipendenze corrette tra i task
- Configura il caching remoto di Turborepo per condividere la cache tra CI e sviluppo locale
- Verifica che `turbo run build` compili tutti i pacchetti nell'ordine corretto rispettando le dipendenze

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Vite** — build tool di nuova generazione con HMR istantaneo e bundling basato su Rollup. https://vite.dev/ (consultato: 2026-05-24)
- **Rollup** — bundler modulare per JavaScript con supporto nativo a tree shaking. https://rollupjs.org/ (consultato: 2026-05-24)
- **Turborepo** — sistema di build incrementale per monorepo JavaScript/TypeScript. https://turbo.build/repo (consultato: 2026-05-24)
- **Docker** — piattaforma per containerizzazione di applicazioni con build multi-stage. https://docs.docker.com/ (consultato: 2026-05-24)
- **GitHub Actions** — piattaforma CI/CD integrata con i repository GitHub. https://docs.github.com/en/actions (consultato: 2026-05-24)
- **Vercel** — piattaforma di deployment per applicazioni frontend e full-stack con preview deploy. https://vercel.com/docs (consultato: 2026-05-24)
- **Cloudflare Pages** — hosting edge per siti statici e applicazioni full-stack con Cloudflare Workers. https://developers.cloudflare.com/pages/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Nader Dabit, *Full Stack Serverless*, O'Reilly, 2020.
- Elton Stoneman, *Learn Docker in a Month of Lunches*, Manning, 2020.
- Bret Fisher, *Docker and Kubernetes: The Complete Guide*, Udemy / self-published, 2023.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [06 — TypeScript](06-typescript.md) | La compilazione TypeScript e' il primo step della pipeline di build trattata qui |
| [10 — Node.js](10-nodejs.md) | Runtime per script di build, server di sviluppo e backend containerizzati |
| [15 — Testing Web](15-testing-web.md) | I test automatizzati si integrano come step della pipeline CI/CD |
| [17 — Performance Web](17-performance-web.md) | L'ottimizzazione del bundle e la compressione degli asset sono obiettivi condivisi |
| [14 — Sicurezza Web](14-sicurezza-web.md) | Gestione sicura di secret e variabili d'ambiente nel deploy |
| [25 — Next.js](25-nextjs-guida-completa.md) | Framework full-stack che integra build, SSR e deployment in un unico strumento |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Bundling** | Processo di combinazione di molteplici file sorgente in uno o piu file ottimizzati per la distribuzione. |
| **Tree shaking** | Tecnica di eliminazione del codice morto che rimuove le esportazioni non utilizzate dal bundle finale. |
| **Code splitting** | Suddivisione del bundle in chunk separati caricati on-demand per ridurre il payload iniziale. |
| **HMR** | Hot Module Replacement: aggiornamento dei moduli nel browser durante lo sviluppo senza ricaricare la pagina. |
| **CI/CD** | Continuous Integration / Continuous Deployment: automazione del ciclo di build, test e rilascio del software. |
| **Artifact** | File o cartella prodotti da uno step della pipeline (bundle compilato, report di copertura, immagine Docker). |
| **Preview deploy** | Deployment temporaneo generato automaticamente per ogni pull request, utile per revisione e test. |
| **Multi-stage build** | Tecnica Docker che utilizza piu stage nel Dockerfile per produrre immagini finali piu leggere separando build e runtime. |
| **Monorepo** | Strategia di organizzazione del codice in cui piu progetti correlati risiedono nello stesso repository. |
| **Lockfile** | File generato dal package manager (`package-lock.json`, `pnpm-lock.yaml`) che fissa le versioni esatte delle dipendenze. |
| **Edge deployment** | Distribuzione dell'applicazione su nodi CDN geograficamente distribuiti per minimizzare la latenza. |
| **Rollback** | Ripristino di una versione precedente dell'applicazione in produzione in caso di errore nel deploy corrente. |
| **Source map** | File che mappa il codice minificato/transpiled al codice sorgente originale per facilitare il debugging. |
| **Environment variable** | Valore di configurazione iniettato a runtime tramite il sistema operativo, non incluso nel codice sorgente. |
| **Module Federation** | Funzionalita' di Webpack 5 che consente a piu' applicazioni indipendenti di condividere codice a runtime, abilitando architetture micro-frontend. |
| **Scope hoisting** | Ottimizzazione che unisce moduli piccoli in un unico scope di funzione, riducendo l'overhead del sistema di moduli e migliorando le performance. |
| **Persistent caching** | Sistema di caching su filesystem che serializza i risultati del build su disco, riducendo drasticamente i tempi delle build successive. |
| **Remote caching** | Condivisione della cache di build tra sviluppatori e pipeline CI tramite un server remoto, eliminando lavoro duplicato nei monorepo. |
| **Incremental computation** | Modello di computazione dove solo le funzioni i cui input sono cambiati vengono rieseguite, utilizzato da Turbopack per rebuild istantanei. |
| **Memoizzazione** | Tecnica di ottimizzazione che memorizza il risultato di funzioni costose per evitarne la riesecuzione con gli stessi input. |
| **Feature flag** | Meccanismo che permette di abilitare o disabilitare funzionalita' dell'applicazione senza necessita' di un nuovo deployment. |
| **Canary deployment** | Strategia di rilascio che espone la nuova versione a una percentuale ridotta di utenti prima del rollout completo. |
| **Blue-green deployment** | Strategia che mantiene due ambienti identici, commutando il traffico tra di essi per deployment a zero downtime. |
| **Entry point** | Il file principale da cui il bundler inizia a costruire il grafo delle dipendenze dell'applicazione. |
| **Content hash** | Hash crittografico derivato dal contenuto di un file, usato nei nomi dei file per garantire il cache busting automatico. |
| **Vendor chunk** | Chunk separato contenente le dipendenze di terze parti, che cambia meno frequentemente del codice applicativo e beneficia di cache lunga. |
| **Brotli** | Algoritmo di compressione sviluppato da Google che offre compressione superiore del 15-25% rispetto a Gzip per asset testuali web. |
| **Affected detection** | Capacita' di determinare automaticamente quali progetti in un monorepo sono impattati da una modifica, eseguendo solo i task necessari. |
| **Internal packages pattern** | Pattern monorepo dove il campo `main` del pacchetto punta al codice sorgente TypeScript, compilato direttamente dal bundler dell'applicazione consumatrice. |
