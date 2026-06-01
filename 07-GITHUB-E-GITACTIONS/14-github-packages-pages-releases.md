---
corso: "GitHub e Git Actions"
fase: "3 — Piattaforma GitHub"
modulo: "14"
titolo: "GitHub Packages, Pages e Releases"
versione: "GitHub 2024"
livello: "intermedio"
prerequisiti:
  - "conoscenza base di GitHub Actions (workflow, job, step)"
  - "familiarita con almeno un package manager (npm, pip, Maven)"
  - "concetti base di hosting statico e DNS"
obiettivi:
  - "pubblicare e gestire pacchetti su GitHub Packages e Container Registry (ghcr.io)"
  - "configurare GitHub Pages con Jekyll, generatori statici e custom domain"
  - "automatizzare il ciclo di release con semantic versioning e changelog"
  - "implementare workflow di pubblicazione multi-ecosistema (npm, Maven, Docker)"
  - "gestire la retention e la pulizia automatica delle versioni dei pacchetti"
tag: [github, packages, pages, releases, ghcr, npm, docker, semantic-versioning, changelog]
---

# GitHub Packages, Pages e Releases — Guida Approfondita

> **Modulo 14** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Pubblicare e gestire pacchetti su GitHub Packages e Container Registry (ghcr.io)
> 2. Configurare GitHub Pages con Jekyll, generatori statici e custom domain
> 3. Automatizzare il ciclo di release con semantic versioning e changelog
> 4. Implementare workflow di pubblicazione multi-ecosistema (npm, Maven, Docker)
> 5. Gestire la retention e la pulizia automatica delle versioni dei pacchetti
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **GitHub Container Registry (ghcr.io) > Docker Hub per perm OAuth.**
2. **GitHub Pages: free static hosting, custom domain.**
3. **Releases: GitHub Actions auto-create on tag.**
4. **Semantic versioning + changelog automation.**


## Indice
- [Panoramica](#panoramica)
- [GitHub Pages: Hosting di Siti Statici](#github-pages-hosting-di-siti-statici)
- [GitHub Pages: Configurazione Avanzata](#github-pages--configurazione-avanzata)
- [GitHub Pages: Deploy con Generatori Statici Moderni](#github-pages-deploy-con-generatori-statici-moderni)
- [GitHub Pages: Limiti, Quote e Vincoli della Piattaforma](#github-pages-limiti-quote-e-vincoli-della-piattaforma)
- [GitHub Releases: Gestione delle Versioni](#github-releases-gestione-delle-versioni)
- [Releases: Automazione Avanzata e Changelog](#releases-automazione-avanzata-e-changelog)
- [Releases: Strategie Avanzate per Monorepo e Hotfix](#releases-strategie-avanzate-per-monorepo-e-hotfix)
- [Releases: semantic-release — Pipeline Completamente Automatizzata](#releases-semantic-release--pipeline-completamente-automatizzata)
- [Releases: Changesets per Monorepo — Versioning e Publishing Moderno](#releases-changesets-per-monorepo--versioning-e-publishing-moderno)
- [GitHub Packages: Registry di Pacchetti](#github-packages-registry-di-pacchetti)
- [GitHub Packages: Workflow Avanzati per Ecosistema](#github-packages-workflow-avanzati-per-ecosistema)
- [GitHub Packages: RubyGems e Gradle/Kotlin](#github-packages-rubygems-e-gradlekotlin)
- [GitHub Packages: Trusted Publishing e Provenance](#github-packages-trusted-publishing-e-provenance)
- [GitHub Packages: Pricing, Quote e Limiti di Storage](#github-packages-pricing-quote-e-limiti-di-storage)
- [GitHub Packages vs Registry Esterni — Confronto Dettagliato](#github-packages-vs-registry-esterni--confronto-dettagliato)
- [GitHub Container Registry (GHCR)](#github-container-registry-ghcr)
- [GHCR: OCI Artifacts — Helm Charts, WASM e Artefatti Generici](#ghcr-oci-artifacts--helm-charts-wasm-e-artefatti-generici)
- [GHCR: Sicurezza e Scanning delle Immagini](#ghcr-sicurezza-e-scanning-delle-immagini)
- [GHCR: Attestazioni SLSA e Supply Chain Security](#ghcr-attestazioni-slsa-e-supply-chain-security)
- [Visibilità e Permessi dei Pacchetti](#visibilità-e-permessi-dei-pacchetti)
- [Consumo di Pacchetti Privati tra Organizzazioni](#consumo-di-pacchetti-privati-tra-organizzazioni)
- [Lifecycle Management dei Pacchetti](#lifecycle-management-dei-pacchetti)
- [Strategie Avanzate di Retention e Cleanup](#strategie-avanzate-di-retention-e-cleanup)
- [Integrazione Completa: dalla Feature alla Distribuzione](#integrazione-completa-dalla-feature-alla-distribuzione)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Riferimenti](#riferimenti)

---

## Panoramica

GitHub offre tre servizi fondamentali per la pubblicazione e distribuzione del software: **GitHub Pages** per l'hosting di siti web statici, **GitHub Releases** per la gestione delle versioni con asset scaricabili e **GitHub Packages** come registry universale per pacchetti software. Questi servizi, integrati nativamente con il repository e con GitHub Actions, formano una pipeline completa dalla scrittura del codice alla distribuzione agli utenti finali.

Comprendere come configurare e utilizzare questi servizi è essenziale per qualsiasi progetto che necessita di documentazione pubblica, distribuzione di release o pubblicazione di pacchetti riutilizzabili. Questa guida esplora in profondità ciascun servizio con configurazioni pratiche, workflow di automazione e best practices per la gestione in produzione.

---

## GitHub Pages: Hosting di Siti Statici

### Cos'è GitHub Pages

GitHub Pages è un servizio di hosting gratuito per siti web statici direttamente dal repository GitHub. Supporta HTML, CSS, JavaScript e generatori di siti statici come Jekyll, Hugo, Next.js (export statico) e molti altri.

### Configurazione di Base

```bash
# Abilitare Pages via CLI
gh api repos/{owner}/{repo}/pages -X POST \
  --input - << 'EOF'
{
  "source": {
    "branch": "main",
    "path": "/docs"
  }
}
EOF

# Opzioni per source.path:
# "/" — root del repository
# "/docs" — directory docs/

# Verificare lo stato di Pages
gh api repos/{owner}/{repo}/pages
```

### Deploy con GitHub Actions

Il metodo moderno per GitHub Pages usa GitHub Actions per il build e il deploy:

```yaml
# .github/workflows/pages.yml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './dist'

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Jekyll

Jekyll è il generatore di siti statici nativo di GitHub Pages. Non richiede un workflow Actions — GitHub lo costruisce automaticamente.

```yaml
# _config.yml (Jekyll)
title: "Il Mio Progetto"
description: "Documentazione del progetto"
baseurl: "/repo-name"
url: "https://username.github.io"

theme: minima
# Oppure un tema remoto
remote_theme: pages-themes/cayman@v0.2.0

plugins:
  - jekyll-feed
  - jekyll-seo-tag
  - jekyll-sitemap

# Esclusioni dalla build
exclude:
  - node_modules/
  - vendor/
  - README.md
  - Gemfile
  - Gemfile.lock

# Collezioni personalizzate
collections:
  docs:
    output: true
    permalink: /docs/:title/
```

```markdown
---
layout: default
title: Home
nav_order: 1
---

# Benvenuto nella documentazione

Questa è la documentazione ufficiale del progetto.

## Quick Start

```bash
npm install my-package
```
```

### Custom Domain

```bash
# Configurare un dominio personalizzato
# 1. Aggiungere un file CNAME nella root del sito
echo "docs.example.com" > CNAME

# 2. Configurare i DNS
# Per apex domain (example.com):
# A record → 185.199.108.153
# A record → 185.199.109.153
# A record → 185.199.110.153
# A record → 185.199.111.153

# Per subdomain (docs.example.com):
# CNAME record → username.github.io

# 3. Abilitare HTTPS (automatico con Let's Encrypt)
gh api repos/{owner}/{repo}/pages -X PUT \
  --input - << 'EOF'
{
  "cname": "docs.example.com",
  "https_enforced": true
}
EOF

# Verificare lo stato del dominio
gh api repos/{owner}/{repo}/pages
```

### Generatori Statici Popolari

| Generatore | Linguaggio | Uso Tipico |
|-----------|-----------|-----------|
| Jekyll | Ruby | Blog, documentazione |
| Hugo | Go | Blog, siti aziendali |
| Next.js (export) | JavaScript | Applicazioni web statiche |
| Gatsby | JavaScript | Siti content-rich |
| VitePress | JavaScript | Documentazione tecnica |
| Docusaurus | JavaScript | Documentazione open source |
| MkDocs | Python | Documentazione tecnica |
| Astro | JavaScript | Siti performanti |

---

## GitHub Pages — Configurazione Avanzata

### SPA (Single Page Application) Routing

Le SPA con client-side routing (React Router, Vue Router, Angular) richiedono una configurazione specifica perché GitHub Pages non supporta rewrite rules lato server:

```html
<!-- 404.html — Redirect hack per SPA routing -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Redirect</title>
  <script>
    // Converte il path in un parametro query e redirige alla root
    // dove l'SPA router gestirà il routing client-side
    var pathSegmentsToKeep = 1; // 0 per user.github.io, 1 per project pages
    var l = window.location;
    l.replace(
      l.protocol + '//' + l.hostname + (l.port ? ':' + l.port : '') +
      l.pathname.split('/').slice(0, 1 + pathSegmentsToKeep).join('/') + '/?/' +
      l.pathname.slice(1).split('/').slice(pathSegmentsToKeep).join('/').replace(/&/g, '~and~') +
      (l.search ? '&' + l.search.slice(1).replace(/&/g, '~and~') : '') +
      l.hash
    );
  </script>
</head>
<body></body>
</html>
```

```javascript
// In index.html — Script per ripristinare il path reale
(function(l) {
  if (l.search[1] === '/') {
    var decoded = l.search.slice(1).split('&').map(function(s) {
      return s.replace(/~and~/g, '&')
    }).join('?');
    window.history.replaceState(null, null,
      l.pathname.slice(0, -1) + decoded + l.hash
    );
  }
}(window.location))
```

### Performance Optimization per Pages

```yaml
# .github/workflows/pages-optimized.yml
name: Deploy Optimized Pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'src/**'
      - 'package.json'

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      # Ottimizzare le immagini
      - name: Optimize images
        run: |
          npx @squoosh/cli --webp '{"quality":80}' dist/**/*.{png,jpg,jpeg} || true
          npx @squoosh/cli --avif '{"quality":60}' dist/**/*.{png,jpg,jpeg} || true

      # Compressione dei file statici
      - name: Pre-compress assets
        run: |
          find dist -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) \
            -exec gzip -9 -k {} \;

      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: './dist'

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

### Monitoraggio e Analytics per Pages

```yaml
# Aggiungere analytics leggero e privacy-friendly
# In _includes/analytics.html (Jekyll) o nel template HTML:

<!-- Plausible Analytics (privacy-friendly, no cookie) -->
<script defer data-domain="docs.example.com"
  src="https://plausible.io/js/script.js"></script>

<!-- Oppure self-hosted con Umami -->
<script async src="https://analytics.example.com/script.js"
  data-website-id="your-website-id"></script>
```

### Pages con Build Condizionali

```yaml
# Deploy Pages solo se i test della documentazione passano
jobs:
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:docs  # Verifica link rotti, spelling, etc.
      - run: npm run build

      # Verifica che non ci siano link rotti
      - name: Check broken links
        run: npx linkinator dist --recurse --skip "^(?!https?://docs\.example\.com)"

  deploy:
    needs: test-docs
    if: github.ref == 'refs/heads/main'
    # ... deploy steps ...
```

---

## GitHub Pages: Deploy con Generatori Statici Moderni

Oltre a Jekyll, l'ecosistema dei generatori di siti statici si e evoluto significativamente. GitHub Pages supporta qualsiasi generatore tramite GitHub Actions, permettendo build personalizzate con pieno controllo sulla pipeline. Di seguito le configurazioni per i generatori piu diffusi nel 2025-2026.

### Deploy con Hugo

Hugo e uno dei generatori di siti statici piu veloci, scritto in Go, ideale per blog, documentazione e siti aziendali. La velocita di build (tipicamente sotto il secondo per siti con centinaia di pagine) lo rende particolarmente adatto a pipeline CI/CD frequenti.

```yaml
# .github/workflows/hugo-pages.yml
name: Deploy Hugo to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

defaults:
  run:
    shell: bash

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.145.0
    steps:
      - name: Install Hugo CLI
        run: |
          wget -O ${{ runner.temp }}/hugo.deb \
            https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb
          sudo dpkg -i ${{ runner.temp }}/hugo.deb

      - name: Install Dart Sass
        run: sudo snap install dart-sass

      - uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Install Node.js dependencies
        run: "[[ -f package-lock.json || -f npm-shrinkwrap.json ]] && npm ci || true"

      - name: Build with Hugo
        env:
          HUGO_CACHEDIR: ${{ runner.temp }}/hugo_cache
          HUGO_ENVIRONMENT: production
          TZ: Europe/Rome
        run: |
          hugo \
            --gc \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

Punti chiave del workflow Hugo:

- **Hugo Extended**: la versione extended include il supporto per la compilazione SCSS/SASS nativa, necessaria per la maggior parte dei temi moderni.
- **Submodules ricorsivi**: molti temi Hugo sono installati come sottomoduli Git; `submodules: recursive` li scarica automaticamente.
- **fetch-depth 0**: necessario per le funzionalita di Hugo che dipendono dalla cronologia Git (es. `.GitInfo`, `.Lastmod`).
- **Flag `--gc --minify`**: `--gc` rimuove file inutilizzati dalla cache, `--minify` comprime l'output HTML/CSS/JS.

### Deploy con Astro

Astro e un framework moderno che produce siti estremamente performanti grazie al suo approccio "zero JavaScript by default" (Islands Architecture). Supporta componenti React, Vue, Svelte e Lit all'interno dello stesso progetto.

```yaml
# .github/workflows/astro-pages.yml
name: Deploy Astro to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Detect package manager
        id: detect-pm
        run: |
          if [ -f "pnpm-lock.yaml" ]; then
            echo "manager=pnpm" >> "$GITHUB_OUTPUT"
            echo "command=install" >> "$GITHUB_OUTPUT"
            echo "runner=pnpm" >> "$GITHUB_OUTPUT"
          elif [ -f "yarn.lock" ]; then
            echo "manager=yarn" >> "$GITHUB_OUTPUT"
            echo "command=install --frozen-lockfile" >> "$GITHUB_OUTPUT"
            echo "runner=yarn" >> "$GITHUB_OUTPUT"
          else
            echo "manager=npm" >> "$GITHUB_OUTPUT"
            echo "command=ci" >> "$GITHUB_OUTPUT"
            echo "runner=npx --no-install" >> "$GITHUB_OUTPUT"
          fi

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: ${{ steps.detect-pm.outputs.manager }}

      - name: Setup pnpm
        if: steps.detect-pm.outputs.manager == 'pnpm'
        run: npm install -g pnpm

      - name: Install dependencies
        run: ${{ steps.detect-pm.outputs.manager }} ${{ steps.detect-pm.outputs.command }}

      - name: Build Astro
        run: ${{ steps.detect-pm.outputs.runner }} astro build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

La configurazione di Astro per GitHub Pages richiede l'impostazione corretta nel file `astro.config.mjs`:

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://username.github.io',
  base: '/repo-name',  // Omettere se user/org site (username.github.io)
  output: 'static',     // Default: output statico
  build: {
    assets: '_astro',    // Directory per asset con hash per cache-busting
  },
  vite: {
    build: {
      cssMinify: 'lightningcss',  // Minificazione CSS performante
    },
  },
});
```

### Deploy con VitePress

VitePress e il successore di VuePress, progettato specificamente per la documentazione tecnica. Utilizza Vite per build istantanee e offre un tema di documentazione ricco out-of-the-box con ricerca full-text, sidebar navigabile e supporto per i18n.

```yaml
# .github/workflows/vitepress-pages.yml
name: Deploy VitePress to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - '.vitepress/**'
      - 'package.json'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necessario per lastUpdated

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - run: npm ci
      - run: npm run docs:build

      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: docs/.vitepress/dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Deploy con Docusaurus

Docusaurus, creato da Meta, e particolarmente adatto alla documentazione di progetti open source. Offre versionamento dei documenti, supporto MDX, internazionalizzazione nativa e un sistema di plugin estensibile.

```yaml
# .github/workflows/docusaurus-pages.yml
name: Deploy Docusaurus to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: yarn

      - name: Install dependencies
        run: yarn install --frozen-lockfile

      - name: Build Docusaurus
        env:
          # Impostare la URL base per GitHub Pages
          URL: https://org-name.github.io
          BASE_URL: /repo-name/
        run: yarn build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: build

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Deploy con MkDocs e Material for MkDocs

MkDocs con il tema Material e una combinazione molto popolare per la documentazione tecnica, specialmente nell'ecosistema Python. Offre ricerca istantanea, navigazione a tab, admonitions e supporto per diagrammi Mermaid.

```yaml
# .github/workflows/mkdocs-pages.yml
name: Deploy MkDocs to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install MkDocs and plugins
        run: |
          pip install mkdocs-material \
            mkdocs-minify-plugin \
            mkdocs-redirects \
            mkdocs-git-revision-date-localized-plugin

      - name: Build MkDocs
        run: mkdocs build --strict

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Confronto tra Generatori per GitHub Pages

| Caratteristica | Jekyll | Hugo | Astro | VitePress | Docusaurus | MkDocs |
|---|---|---|---|---|---|---|
| Linguaggio | Ruby | Go | JS/TS | JS/TS | JS/TS | Python |
| Velocita di build | Lenta | Molto veloce | Veloce | Veloce | Media | Veloce |
| Build nativa Pages | Si | No (Actions) | No (Actions) | No (Actions) | No (Actions) | No (Actions) |
| Componenti UI | No | Limitato | Si (React/Vue/Svelte) | Si (Vue) | Si (React/MDX) | No |
| Versionamento docs | No | No | No | No | Si | No nativo |
| Ricerca integrata | No | No | No | Si | Si | Si |
| Curva di apprendimento | Bassa | Media | Media | Bassa | Media | Bassa |
| Dimensione output tipica | Media | Piccola | Molto piccola | Piccola | Media | Piccola |

La scelta del generatore dipende dal caso d'uso: Jekyll rimane valido per blog semplici grazie alla build nativa; Hugo per siti con molte pagine dove la velocita di build conta; Astro per siti ad alte prestazioni con componenti interattivi; VitePress e MkDocs per documentazione tecnica; Docusaurus per documentazione open source con versionamento.

---

## GitHub Pages: Limiti, Quote e Vincoli della Piattaforma

GitHub Pages e un servizio gratuito con limiti documentati. Conoscere questi vincoli e fondamentale per decidere se Pages e adatto al proprio caso d'uso e per evitare interruzioni del servizio.

### Limiti Ufficiali

```
Limiti di GitHub Pages (aggiornati al 2026):

Dimensione repository sorgente:
├── Raccomandato: ≤ 1 GB
└── Il sito pubblicato non puo superare 1 GB

Bandwidth:
├── Soft limit: 100 GB / mese
├── Superamento: email da GitHub con suggerimenti per ridurre l'impatto
└── Non e un hard cap — il servizio non viene disattivato immediatamente

Build:
├── Build automatiche (Jekyll nativo): 10 build / ora
├── Build via GitHub Actions: nessun limite specifico Pages
│   (soggetto ai limiti generali di Actions)
└── Timeout build: 10 minuti

Rate limiting:
├── Richieste eccessive: HTTP 429 (Too Many Requests)
└── Nessun SLA ufficiale per la disponibilita del servizio
```

### Vincoli Tecnici della Piattaforma

GitHub Pages ha vincoli architetturali importanti che derivano dalla sua natura di servizio di hosting statico su CDN globale:

**Nessun supporto per header HTTP personalizzati.** GitHub Pages non offre alcun meccanismo per configurare header HTTP come `Content-Security-Policy`, `X-Frame-Options`, `Access-Control-Allow-Origin` o `Strict-Transport-Security`. Non esistono file `.htaccess`, `_headers` (come su Netlify/Cloudflare Pages) o file di configurazione equivalenti. Tutti i file vengono serviti con header predefiniti da GitHub, senza possibilita di personalizzazione. Questo significa che:

- Non si puo implementare una Content Security Policy restrittiva
- Non si possono configurare header CORS per API cross-origin
- Non si possono aggiungere header di sicurezza custom
- Il caching e interamente gestito dalla CDN di GitHub

**Nessun server-side processing.** Pages serve esclusivamente file statici. Non esiste possibilita di eseguire codice server-side, accedere a database, gestire sessioni o processare form. Qualsiasi logica dinamica deve essere implementata client-side (JavaScript) o delegata a servizi esterni (API, serverless functions, BaaS).

**Nessun redirect lato server.** Non esiste supporto per redirect HTTP 301/302 configurabili. Le alternative sono redirect via meta tag HTML o JavaScript, oppure il plugin `jekyll-redirect-from` per siti Jekyll.

**Nessun supporto per `.htaccess` o rewrite rules.** Le SPA con client-side routing richiedono il workaround con `404.html` documentato nella sezione configurazione avanzata.

### Quando NON Usare GitHub Pages

GitHub Pages non e la scelta giusta nei seguenti scenari:

```
Scenari inadatti per GitHub Pages:
├── Siti con necessita di header di sicurezza personalizzati (CSP rigorosa)
├── Applicazioni con logica server-side (SSR, API, database)
├── Siti con traffico elevato e SLA di disponibilita
├── Siti che necessitano di A/B testing server-side
├── Applicazioni con autenticazione/autorizzazione complessa
├── Siti con necessita di edge functions o middleware
└── Siti commerciali con requisiti di compliance (PCI DSS, SOC 2)
```

### Alternative a GitHub Pages

| Piattaforma | Headers custom | Edge functions | SLA | Costo base |
|---|---|---|---|---|
| GitHub Pages | No | No | Nessuno | Gratuito |
| Cloudflare Pages | Si (`_headers`) | Si (Workers) | 99.99% | Gratuito |
| Vercel | Si (`vercel.json`) | Si (Edge/Serverless) | 99.99% | Gratuito |
| Netlify | Si (`_headers`) | Si (Edge Functions) | 99.99% | Gratuito |
| AWS Amplify | Si (custom rules) | Si (Lambda@Edge) | 99.9% | Pay-as-you-go |

Per progetti che necessitano di funzionalita avanzate mantenendo l'integrazione con GitHub, Cloudflare Pages e Vercel offrono l'alternativa piu naturale: entrambi supportano il deploy automatico da repository GitHub con un setup minimale.

### Strategia Ibrida: GitHub Pages con CDN Esterno

Per mitigare le limitazioni di Pages senza migrare completamente, e possibile mettere un CDN (come Cloudflare) davanti al sito GitHub Pages:

```
Architettura ibrida:

Utente → Cloudflare (CDN + security headers + WAF)
    → GitHub Pages (origin)

Vantaggi:
├── Header di sicurezza personalizzati via Cloudflare Workers / Transform Rules
├── WAF e protezione DDoS
├── Caching aggressivo configurabile
├── Analytics server-side
└── Redirect e rewrite rules
```

```bash
# Configurazione DNS con Cloudflare come proxy
# 1. Cambiare i nameserver del dominio a Cloudflare
# 2. Aggiungere record DNS con proxy abilitato (nuvola arancione)
#    CNAME  www     username.github.io  (Proxied)
#    A      @       185.199.108.153     (Proxied)

# 3. Aggiungere header di sicurezza con Cloudflare Transform Rules
# Dashboard → Rules → Transform Rules → Modify Response Header
# Aggiungere:
#   X-Frame-Options: DENY
#   X-Content-Type-Options: nosniff
#   Referrer-Policy: strict-origin-when-cross-origin
#   Content-Security-Policy: default-src 'self'; script-src 'self'
```

---

## GitHub Releases: Gestione delle Versioni

### Semantic Versioning

Le release GitHub seguono tipicamente il Semantic Versioning (SemVer):

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └─ Bug fix retrocompatibili
  │     └───── Funzionalità retrocompatibili
  └────────── Cambiamenti incompatibili (breaking changes)

Esempi:
  1.0.0     → Prima release stabile
  1.1.0     → Nuova funzionalità retrocompatibile
  1.1.1     → Bug fix
  2.0.0     → Breaking change
  2.0.0-beta.1 → Pre-release
  2.0.0-rc.1   → Release candidate
```

### Creare Release

```bash
# Creare un tag
git tag -a v1.0.0 -m "Release 1.0.0: prima release stabile"
git push origin v1.0.0

# Creare una release dal tag
gh release create v1.0.0 \
  --title "v1.0.0 — Prima Release Stabile" \
  --notes "## Novità
- Implementazione autenticazione OAuth2
- Dashboard utente
- API REST completa

## Bug Fix
- Correzione parsing JSON per caratteri speciali
- Fix memory leak nel connection pool

## Breaking Changes
- Rimossa API v0 deprecata"

# Creare una release con asset allegati
gh release create v1.0.0 \
  --title "v1.0.0" \
  dist/app-linux-amd64 \
  dist/app-darwin-amd64 \
  dist/app-windows-amd64.exe \
  --generate-notes

# Creare una pre-release
gh release create v2.0.0-beta.1 --prerelease --title "v2.0.0 Beta 1"

# Creare una draft release
gh release create v1.1.0 --draft --title "v1.1.0 — WIP"
```

### Generazione Automatica delle Release Notes

GitHub può generare automaticamente le release notes basandosi sulle PR mergiate:

```yaml
# .github/release.yml
changelog:
  exclude:
    labels:
      - skip-changelog
      - dependencies
    authors:
      - dependabot
      - renovate-bot

  categories:
    - title: "🚀 Nuove Funzionalità"
      labels:
        - enhancement
        - feature
    - title: "🐛 Bug Fix"
      labels:
        - bug
        - bugfix
    - title: "🔒 Sicurezza"
      labels:
        - security
    - title: "📖 Documentazione"
      labels:
        - documentation
    - title: "🏗️ Infrastruttura"
      labels:
        - infrastructure
        - ci
    - title: "🔄 Altre Modifiche"
      labels:
        - "*"
```

```bash
# Generare le release notes automaticamente
gh release create v1.1.0 --generate-notes

# Visualizzare le release notes generate senza creare la release
gh api repos/{owner}/{repo}/releases/generate-notes \
  -f tag_name="v1.1.0" \
  -f target_commitish="main" \
  -f previous_tag_name="v1.0.0"
```

### Automazione delle Release con Actions

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Build
        run: |
          npm ci
          npm run build

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
          files: |
            dist/*.tar.gz
            dist/*.zip
            dist/checksums.txt
          prerelease: ${{ contains(github.ref, '-beta') || contains(github.ref, '-rc') }}
```

---

## Releases: Automazione Avanzata e Changelog

### Release Please — Automazione Completa

[Release Please](https://github.com/googleapis/release-please) di Google automatizza l'intero ciclo di release basandosi sui Conventional Commits:

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          release-type: node
          # Opzioni:
          # node, python, rust, go, java, ruby, php, dart, elixir,
          # simple (per progetti generici)

  # Job di pubblicazione che si attiva solo quando una release viene creata
  publish:
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Release Please funziona creando una "Release PR" che viene aggiornata automaticamente ad ogni push su main. La PR contiene:
- Aggiornamento della versione in `package.json` (o equivalente)
- `CHANGELOG.md` generato automaticamente
- Quando la PR viene mergiata, viene creata la release con tag

### Changelog Manuale Strutturato

Per progetti che preferiscono un changelog manuale ma strutturato:

```markdown
<!-- CHANGELOG.md — formato keepachangelog.com -->
# Changelog

Tutte le modifiche rilevanti sono documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/lang/it/).

## [Unreleased]

### Added
- Supporto per autenticazione SAML

### Changed
- Migrazione database da PostgreSQL 14 a 16

## [2.1.0] - 2026-05-15

### Added
- API endpoint per esportazione report in PDF
- Supporto multi-lingua (IT, EN, DE, FR)
- Dashboard real-time con WebSocket

### Fixed
- Memory leak nel connection pool (#234)
- Race condition nella cache (#289)

### Security
- Aggiornamento dipendenze con CVE critici

## [2.0.0] - 2026-04-01

### Changed
- **BREAKING**: Migrazione API da v1 a v2
- Nuovo formato risposta JSON con envelope standard

### Removed
- Endpoint deprecati v0 (rimossi dopo 12 mesi di deprecation)

[Unreleased]: https://github.com/org/repo/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/org/repo/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/org/repo/compare/v1.9.0...v2.0.0
```

### Release con Build Cross-Platform

```yaml
# .github/workflows/release-multiplatform.yml
name: Release Multi-Platform

on:
  push:
    tags: ['v*']

permissions:
  contents: write

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: linux-amd64
            ext: ""
          - os: ubuntu-latest
            target: linux-arm64
            ext: ""
            cross: true
          - os: macos-latest
            target: darwin-amd64
            ext: ""
          - os: macos-latest
            target: darwin-arm64
            ext: ""
          - os: windows-latest
            target: windows-amd64
            ext: ".exe"

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          # Esempio per Go
          GOOS=$(echo ${{ matrix.target }} | cut -d- -f1) \
          GOARCH=$(echo ${{ matrix.target }} | cut -d- -f2) \
          go build -ldflags="-s -w -X main.version=${{ github.ref_name }}" \
          -o dist/myapp-${{ matrix.target }}${{ matrix.ext }} ./cmd/myapp

      - name: Generate checksums
        run: sha256sum dist/* > dist/checksums-${{ matrix.target }}.txt
        shell: bash

      - uses: actions/upload-artifact@v4
        with:
          name: binaries-${{ matrix.target }}
          path: dist/

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: dist/
          merge-multiple: true

      - name: Merge checksums
        run: cat dist/checksums-*.txt > dist/checksums.txt && rm dist/checksums-*.txt

      - uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            dist/myapp-*
            dist/checksums.txt
          prerelease: ${{ contains(github.ref, '-beta') || contains(github.ref, '-rc') }}
```

### Signing delle Release

```bash
# Firmare i binari della release con cosign (Sigstore)
cosign sign-blob --yes dist/myapp-linux-amd64 \
  --output-signature dist/myapp-linux-amd64.sig \
  --output-certificate dist/myapp-linux-amd64.pem

# Verificare la firma
cosign verify-blob dist/myapp-linux-amd64 \
  --signature dist/myapp-linux-amd64.sig \
  --certificate dist/myapp-linux-amd64.pem \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

---

## Releases: Strategie Avanzate per Monorepo e Hotfix

### Release in Monorepo con Release Please

Nei monorepo con piu pacchetti indipendenti, Release Please supporta la gestione di release multiple tramite un manifest file. Ogni pacchetto ha il proprio changelog, la propria versione e la propria release PR.

```json
// release-please-config.json
{
  "packages": {
    "packages/core": {
      "release-type": "node",
      "component": "core",
      "changelog-path": "CHANGELOG.md"
    },
    "packages/cli": {
      "release-type": "node",
      "component": "cli",
      "changelog-path": "CHANGELOG.md"
    },
    "packages/server": {
      "release-type": "node",
      "component": "server",
      "changelog-path": "CHANGELOG.md"
    }
  },
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
}
```

```json
// .release-please-manifest.json — versioni attuali
{
  "packages/core": "2.3.1",
  "packages/cli": "1.5.0",
  "packages/server": "3.0.0"
}
```

```yaml
# .github/workflows/release-monorepo.yml
name: Release Monorepo

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      releases_created: ${{ steps.release.outputs.releases_created }}
      core--release_created: ${{ steps.release.outputs['packages/core--release_created'] }}
      cli--release_created: ${{ steps.release.outputs['packages/cli--release_created'] }}
      server--release_created: ${{ steps.release.outputs['packages/server--release_created'] }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json

  publish-core:
    needs: release-please
    if: ${{ needs.release-please.outputs.core--release_created }}
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: 'https://npm.pkg.github.com'
      - run: cd packages/core && npm ci && npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-cli:
    needs: release-please
    if: ${{ needs.release-please.outputs.cli--release_created }}
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: 'https://npm.pkg.github.com'
      - run: cd packages/cli && npm ci && npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Strategia di Hotfix e Release di Emergenza

Per gli hotfix di emergenza in produzione, la strategia prevede un flusso accelerato che bypassa il normale ciclo di release mantenendo la tracciabilita:

```bash
# Flusso hotfix
# 1. Creare un branch hotfix dal tag di produzione
git checkout -b hotfix/v2.3.2 v2.3.1

# 2. Applicare il fix
git commit -m "fix: risolve crash critico nel processamento pagamenti (#456)"

# 3. Creare il tag e la release
git tag -a v2.3.2 -m "Hotfix: crash processamento pagamenti"
git push origin hotfix/v2.3.2 v2.3.2

# 4. Creare la release con urgenza documentata
gh release create v2.3.2 \
  --title "v2.3.2 — Hotfix Critico" \
  --notes "## Hotfix di Emergenza

### Problema
Crash nel modulo di processamento pagamenti quando l'importo contiene
piu di 2 decimali. Issue: #456.

### Impatto
Tutti gli utenti che processano pagamenti con valute a 3+ decimali.

### Correzione
Validazione dell'input con arrotondamento al numero corretto di decimali
prima del processamento.

### Rollback
In caso di regressione, tornare a v2.3.1:
\`\`\`
docker pull ghcr.io/org/app:v2.3.1
kubectl set image deployment/app app=ghcr.io/org/app:v2.3.1
\`\`\`"

# 5. Cherry-pick il fix su main per la prossima release
git checkout main
git cherry-pick hotfix/v2.3.2
git push origin main
```

### Release Channels e Pre-Release

Per progetti con cicli di release strutturati, e comune avere piu canali di distribuzione:

```
Canali di release:
├── stable    (v2.3.1)     → Utenti in produzione
├── rc        (v2.4.0-rc.1) → Testing interno pre-produzione
├── beta      (v2.4.0-beta.3) → Early adopters e beta tester
├── alpha     (v2.4.0-alpha.7) → Sviluppatori interni
├── canary    (v2.4.0-canary.20260524) → Build giornaliere automatiche
└── nightly   (nightly-20260524) → Build notturne per CI/CD
```

```yaml
# .github/workflows/canary-release.yml
name: Canary Release

on:
  push:
    branches: [main]

jobs:
  canary:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: 'https://npm.pkg.github.com'

      - run: npm ci

      - name: Set canary version
        run: |
          CANARY_VERSION=$(node -p "require('./package.json').version")-canary.$(date +%Y%m%d%H%M%S).$(git rev-parse --short HEAD)
          npm version "$CANARY_VERSION" --no-git-tag-version
          echo "CANARY_VERSION=$CANARY_VERSION" >> "$GITHUB_ENV"

      - name: Publish canary
        run: npm publish --tag canary
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Comment on commit
        run: |
          gh api repos/${{ github.repository }}/commits/${{ github.sha }}/comments \
            -f body="Canary release pubblicata: \`${{ env.CANARY_VERSION }}\`
          Installare con: \`npm install @org/package@canary\`"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Releases: semantic-release — Pipeline Completamente Automatizzata

### Panoramica di semantic-release

[semantic-release](https://github.com/semantic-release/semantic-release) automatizza l'intero ciclo di vita della release: determina la versione successiva analizzando i commit, genera il changelog, pubblica il pacchetto e crea la release GitHub. A differenza di Release Please (che crea una PR da mergiare), semantic-release esegue tutto in un'unica esecuzione del workflow.

### Configurazione Completa

```json
// .releaserc.json
{
  "branches": [
    "main",
    { "name": "next", "prerelease": true },
    { "name": "beta", "prerelease": true },
    { "name": "alpha", "prerelease": true }
  ],
  "plugins": [
    ["@semantic-release/commit-analyzer", {
      "preset": "conventionalcommits",
      "releaseRules": [
        { "type": "feat", "release": "minor" },
        { "type": "fix", "release": "patch" },
        { "type": "perf", "release": "patch" },
        { "type": "revert", "release": "patch" },
        { "type": "refactor", "release": "patch" },
        { "breaking": true, "release": "major" }
      ]
    }],
    ["@semantic-release/release-notes-generator", {
      "preset": "conventionalcommits",
      "presetConfig": {
        "types": [
          { "type": "feat", "section": "Nuove Funzionalita" },
          { "type": "fix", "section": "Bug Fix" },
          { "type": "perf", "section": "Miglioramenti Prestazioni" },
          { "type": "revert", "section": "Revert" },
          { "type": "refactor", "section": "Refactoring" },
          { "type": "docs", "section": "Documentazione", "hidden": true },
          { "type": "chore", "section": "Manutenzione", "hidden": true },
          { "type": "test", "section": "Test", "hidden": true },
          { "type": "ci", "section": "CI/CD", "hidden": true }
        ]
      }
    }],
    "@semantic-release/changelog",
    ["@semantic-release/npm", {
      "npmPublish": true
    }],
    ["@semantic-release/github", {
      "assets": [
        { "path": "dist/*.tar.gz", "label": "Distribuzione (tar.gz)" },
        { "path": "dist/*.zip", "label": "Distribuzione (zip)" },
        { "path": "dist/checksums.txt", "label": "Checksums SHA-256" }
      ]
    }],
    ["@semantic-release/git", {
      "assets": ["package.json", "CHANGELOG.md"],
      "message": "chore(release): ${nextRelease.version}\n\n${nextRelease.notes}"
    }]
  ]
}
```

```yaml
# .github/workflows/semantic-release.yml
name: Semantic Release

on:
  push:
    branches: [main, next, beta, alpha]

permissions:
  contents: write
  issues: write
  pull-requests: write
  packages: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - run: npm ci

      - name: Build
        run: npm run build

      - name: Run tests
        run: npm test

      - name: Semantic Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npx semantic-release
```

### Confronto: Release Please vs semantic-release

| Aspetto | Release Please | semantic-release |
|---|---|---|
| Approccio | Release PR da mergiare | Esecuzione automatica diretta |
| Controllo umano | Merge della PR = gate manuale | Nessun gate manuale (push = release) |
| Conventional Commits | Richiesti | Richiesti |
| Changelog | Generato nella PR | Generato al momento della release |
| Multi-branch | Limitato | Eccellente (main, next, beta, alpha) |
| Monorepo | Si (manifest) | Si (con plugin monorepo) |
| Plugin ecosystem | Limitato | Molto esteso |
| Pubblicazione pacchetti | Separata (job successivo) | Integrata (plugin npm/pypi/etc.) |
| Complessita setup | Bassa | Media-alta |

La scelta dipende dal flusso di lavoro del team: Release Please e preferibile quando si desidera un gate umano prima della pubblicazione; semantic-release e ideale per continuous deployment dove ogni merge su main deve produrre una release automatica.

---

## Releases: Changesets per Monorepo — Versioning e Publishing Moderno

### Perche Changesets

Changesets (`@changesets/cli`) e lo strumento di versioning e publishing che ha sostituito Lerna nella maggior parte dei monorepo JavaScript/TypeScript moderni. Progetti come Radix UI, Chakra UI, Turborepo e Pnpm lo utilizzano in produzione. A differenza di Release Please e semantic-release, Changesets adotta un modello **intent-file**: ogni pull request che modifica un pacchetto include un file `.changeset/*.md` che dichiara esplicitamente il tipo di bump (major, minor, patch) e una descrizione del cambiamento leggibile da umani. Questo approccio separa la decisione di versioning dal formato del commit message, eliminando la necessita di imporre Conventional Commits a tutto il team.

### Workflow Operativo

Il flusso di lavoro Changesets si articola in tre fasi distinte:

1. **Creazione del changeset**: lo sviluppatore esegue `npx changeset` nella root del monorepo. Il CLI interattivo chiede quali pacchetti sono stati modificati e quale tipo di bump applicare. Il risultato e un file Markdown in `.changeset/` con frontmatter YAML:

```markdown
---
"@myorg/ui-button": minor
"@myorg/ui-theme": patch
---

Aggiunto supporto per la variante `ghost` nel componente Button.
Aggiornato il tema per includere i token di colore per la nuova variante.
```

2. **Accumulo nel branch principale**: piu changeset possono coesistere. Ogni PR aggiunge il proprio file senza conflitti, perche i nomi sono UUID-based.

3. **Version e publish**: l'action ufficiale `changesets/action` apre una PR automatica intitolata "Version Packages" che aggrega tutti i changeset pendenti, aggiorna i `package.json`, genera i `CHANGELOG.md` per ogni pacchetto e rimuove i file changeset consumati. Al merge della PR, un secondo job esegue `changeset publish` per pubblicare su npm o GitHub Packages.

### Configurazione GitHub Actions

```yaml
name: Release con Changesets
on:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      packages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'
          registry-url: 'https://npm.pkg.github.com'

      - run: pnpm install --frozen-lockfile

      - name: Crea Release PR oppure Pubblica
        id: changesets
        uses: changesets/action@v1
        with:
          version: pnpm changeset version
          publish: pnpm changeset publish
          title: 'chore: version packages'
          commit: 'chore: version packages'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_CONFIG_PROVENANCE: true

      - name: Crea GitHub Release per ogni pacchetto pubblicato
        if: steps.changesets.outputs.published == 'true'
        run: |
          PUBLISHED='${{ steps.changesets.outputs.publishedPackages }}'
          echo "$PUBLISHED" | jq -c '.[]' | while read -r pkg; do
            NAME=$(echo "$pkg" | jq -r '.name')
            VERSION=$(echo "$pkg" | jq -r '.version')
            TAG="${NAME}@${VERSION}"
            gh release create "$TAG" \
              --title "$TAG" \
              --generate-notes \
              --verify-tag || true
          done
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Gestione delle Dipendenze Interne

Changesets gestisce automaticamente le dipendenze interne del monorepo tramite la configurazione `linked` e `fixed` in `.changeset/config.json`:

```json
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": "@changesets/changelog-github",
  "commit": false,
  "fixed": [],
  "linked": [["@myorg/ui-*"]],
  "access": "restricted",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": ["@myorg/docs", "@myorg/e2e-tests"]
}
```

- **`linked`**: pacchetti che devono avere la stessa versione (bump congiunto). Utile per componenti UI che devono restare allineati.
- **`fixed`**: come `linked`, ma forza lo stesso numero di versione esatto.
- **`updateInternalDependencies`**: quando un pacchetto viene bumpato, aggiorna automaticamente i consumatori interni con almeno un patch bump.
- **`ignore`**: esclude pacchetti che non devono essere pubblicati (docs, test suite, app interne).

### Snapshot Releases per Testing

Changesets supporta le **snapshot releases**, versioni temporanee pubblicate con un tag speciale per testare modifiche prima del merge:

```yaml
      - name: Pubblica snapshot per PR
        if: github.event_name == 'pull_request'
        run: |
          pnpm changeset version --snapshot preview
          pnpm changeset publish --tag preview --no-git-tag
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Le snapshot producono versioni come `0.0.0-preview-20260524T143022`, installabili con `npm install @myorg/ui-button@preview` per validare le modifiche in ambienti di staging.

### Pre-release Mode

Per gestire versioni alpha, beta e release candidate, Changesets offre la modalita pre-release:

```bash
# Entrare in modalita pre-release
npx changeset pre enter beta

# I bump successivi producono versioni come 2.0.0-beta.0, 2.0.0-beta.1
npx changeset version

# Uscire dalla modalita pre-release
npx changeset pre exit
npx changeset version  # Produce la versione stabile 2.0.0
```

### Confronto: Changesets vs Release Please vs semantic-release

| Aspetto | Changesets | Release Please | semantic-release |
|---------|------------|----------------|------------------|
| Input versioning | File `.changeset/*.md` | Conventional Commits | Conventional Commits |
| Gate umano | PR "Version Packages" | PR release | Nessuno (full auto) |
| Monorepo nativo | Si (linked/fixed groups) | Si (manifest mode) | Parziale (multi-release) |
| Snapshot releases | Si (`--snapshot`) | No | Si (plugin) |
| Pre-release mode | Si (`pre enter/exit`) | Si (prerelease branches) | Si (branches config) |
| Changelog | Per-pacchetto automatico | Per-pacchetto automatico | Per-pacchetto automatico |
| Ecosistema principale | JavaScript/TypeScript | Qualsiasi linguaggio | JavaScript/TypeScript |
| Curva di apprendimento | Bassa | Bassa | Media-alta |
| Adozione 2025 | Pnpm, Turborepo, Radix | Googleapis, Terraform | Molti progetti OSS |

La scelta tra i tre strumenti dipende dall'ecosistema e dal grado di automazione desiderato. Changesets eccelle nei monorepo JavaScript grazie al modello intent-file che non vincola il formato dei commit message. Release Please e il piu versatile per progetti multi-linguaggio. semantic-release rimane la scelta migliore per continuous deployment completamente automatizzato dove nessun intervento umano e desiderato tra il merge e la pubblicazione.

---

## GitHub Packages: Registry di Pacchetti

### Registry Supportati

GitHub Packages supporta diversi registry per diversi ecosistemi:

| Ecosistema | Registry URL | Client |
|-----------|-------------|--------|
| npm | `npm.pkg.github.com` | npm, yarn, pnpm |
| Maven | `maven.pkg.github.com` | Maven, Gradle |
| NuGet | `nuget.pkg.github.com` | dotnet, nuget |
| Docker | `ghcr.io` | docker, podman |
| RubyGems | `rubygems.pkg.github.com` | gem, bundler |

### Pubblicare Pacchetti npm

```json
// package.json
{
  "name": "@my-org/my-package",
  "version": "1.0.0",
  "publishConfig": {
    "registry": "https://npm.pkg.github.com"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/my-org/my-package.git"
  }
}
```

```bash
# Autenticazione
echo "//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}" >> ~/.npmrc

# Pubblicare
npm publish

# Installare un pacchetto da GitHub Packages
echo "@my-org:registry=https://npm.pkg.github.com" >> .npmrc
npm install @my-org/my-package
```

```yaml
# .github/workflows/publish-npm.yml
name: Publish npm Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: 'https://npm.pkg.github.com'

      - run: npm ci
      - run: npm test
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Pubblicare Pacchetti Maven

```xml
<!-- pom.xml -->
<distributionManagement>
    <repository>
        <id>github</id>
        <name>GitHub Packages</name>
        <url>https://maven.pkg.github.com/my-org/my-package</url>
    </repository>
</distributionManagement>
```

```xml
<!-- ~/.m2/settings.xml -->
<settings>
    <servers>
        <server>
            <id>github</id>
            <username>${env.GITHUB_ACTOR}</username>
            <password>${env.GITHUB_TOKEN}</password>
        </server>
    </servers>
</settings>
```

```yaml
# .github/workflows/publish-maven.yml
name: Publish Maven Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'

      - name: Publish to GitHub Packages
        run: mvn deploy -DskipTests
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## GitHub Packages: Workflow Avanzati per Ecosistema

### Pubblicare Pacchetti Python (PyPI)

```yaml
# .github/workflows/publish-python.yml
name: Publish Python Package

on:
  release:
    types: [published]

permissions:
  id-token: write  # Per trusted publishing

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI (trusted publishing)
        uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun token necessario con trusted publishing!
        # Configurare su pypi.org → Manage → Publishing → Add publisher

      # Pubblicare anche su GitHub Packages (opzionale)
      - name: Publish to GitHub Packages
        run: |
          python -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

### Pubblicare Pacchetti NuGet (.NET)

```yaml
# .github/workflows/publish-nuget.yml
name: Publish NuGet Package

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: 8.x

      - name: Build and pack
        run: |
          dotnet build --configuration Release
          dotnet pack --configuration Release --output nupkgs \
            -p:PackageVersion=${{ github.event.release.tag_name }}

      - name: Publish to NuGet.org
        run: dotnet nuget push nupkgs/*.nupkg --api-key ${{ secrets.NUGET_API_KEY }} --source https://api.nuget.org/v3/index.json

      - name: Publish to GitHub Packages
        run: dotnet nuget push nupkgs/*.nupkg --api-key ${{ secrets.GITHUB_TOKEN }} --source https://nuget.pkg.github.com/{owner}/index.json
```

### Monorepo — Pubblicazione Selettiva

```yaml
# Per monorepo con più pacchetti, pubblicare solo quelli modificati
name: Publish Changed Packages

on:
  push:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.changes.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - id: changes
        run: |
          changed=$(git diff --name-only HEAD~1 HEAD | grep '^packages/' | cut -d/ -f2 | sort -u | jq -R -s -c 'split("\n")[:-1]')
          echo "packages=$changed" >> "$GITHUB_OUTPUT"

  publish:
    needs: detect-changes
    if: needs.detect-changes.outputs.packages != '[]'
    strategy:
      matrix:
        package: ${{ fromJson(needs.detect-changes.outputs.packages) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: 'https://npm.pkg.github.com'
      - run: cd packages/${{ matrix.package }} && npm ci && npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## GitHub Packages: RubyGems e Gradle/Kotlin

### Pubblicare Pacchetti RubyGems

GitHub Packages supporta il registry RubyGems, permettendo di pubblicare gemme Ruby con autenticazione integrata tramite `GITHUB_TOKEN`.

```ruby
# Gemspec — configurazione della gemma
# my-gem.gemspec
Gem::Specification.new do |spec|
  spec.name          = "my-gem"
  spec.version       = "1.0.0"
  spec.authors       = ["Org Name"]
  spec.summary       = "Una gemma pubblicata su GitHub Packages"
  spec.homepage      = "https://github.com/my-org/my-gem"
  spec.license       = "MIT"
  spec.metadata      = {
    "github_repo"       => "ssh://github.com/my-org/my-gem",
    "source_code_uri"   => "https://github.com/my-org/my-gem",
    "changelog_uri"     => "https://github.com/my-org/my-gem/blob/main/CHANGELOG.md"
  }

  spec.files = Dir["lib/**/*", "LICENSE", "README.md"]
  spec.require_paths = ["lib"]
  spec.required_ruby_version = ">= 3.2"
end
```

```bash
# Configurare l'autenticazione per RubyGems su GitHub Packages
# ~/.gem/credentials
---
:github: Bearer TOKEN

# Pubblicare la gemma
gem build my-gem.gemspec
gem push --key github \
  --host https://rubygems.pkg.github.com/my-org \
  my-gem-1.0.0.gem
```

```yaml
# .github/workflows/publish-rubygem.yml
name: Publish RubyGem

on:
  release:
    types: [published]

permissions:
  packages: write
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'

      - name: Build gem
        run: gem build *.gemspec

      - name: Setup credentials
        run: |
          mkdir -p ~/.gem
          echo "---" > ~/.gem/credentials
          echo ":github: Bearer ${{ secrets.GITHUB_TOKEN }}" >> ~/.gem/credentials
          chmod 0600 ~/.gem/credentials

      - name: Publish to GitHub Packages
        run: gem push --key github --host https://rubygems.pkg.github.com/${{ github.repository_owner }} *.gem

      - name: Cleanup credentials
        if: always()
        run: rm -f ~/.gem/credentials
```

Per consumare una gemma da GitHub Packages in un progetto Ruby:

```ruby
# Gemfile
source "https://rubygems.org"

# Aggiungere la sorgente GitHub Packages per lo scope dell'organizzazione
source "https://rubygems.pkg.github.com/my-org" do
  gem "my-gem", "~> 1.0"
end
```

```bash
# Configurare Bundler per l'autenticazione
bundle config set --global https://rubygems.pkg.github.com/my-org USERNAME:TOKEN
```

### Pubblicare con Gradle (Java/Kotlin)

Per i progetti Java e Kotlin, Gradle offre un'integrazione fluida con GitHub Packages tramite il plugin `maven-publish`.

```kotlin
// build.gradle.kts — configurazione Gradle Kotlin DSL
plugins {
    kotlin("jvm") version "2.1.0"
    `maven-publish`
}

group = "com.example"
version = "1.0.0"

publishing {
    repositories {
        maven {
            name = "GitHubPackages"
            url = uri("https://maven.pkg.github.com/my-org/my-library")
            credentials {
                username = System.getenv("GITHUB_ACTOR")
                    ?: project.findProperty("gpr.user") as String?
                password = System.getenv("GITHUB_TOKEN")
                    ?: project.findProperty("gpr.key") as String?
            }
        }
    }
    publications {
        register<MavenPublication>("gpr") {
            from(components["java"])
            pom {
                name.set("My Library")
                description.set("Una libreria pubblicata su GitHub Packages")
                url.set("https://github.com/my-org/my-library")
                licenses {
                    license {
                        name.set("MIT")
                        url.set("https://opensource.org/licenses/MIT")
                    }
                }
            }
        }
    }
}
```

```yaml
# .github/workflows/publish-gradle.yml
name: Publish Gradle Package

on:
  release:
    types: [published]

permissions:
  packages: write
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v4

      - name: Run tests
        run: ./gradlew test

      - name: Publish to GitHub Packages
        run: ./gradlew publish
        env:
          GITHUB_ACTOR: ${{ github.actor }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Per consumare un pacchetto Gradle da GitHub Packages in un altro progetto:

```kotlin
// build.gradle.kts — progetto consumer
repositories {
    mavenCentral()
    maven {
        url = uri("https://maven.pkg.github.com/my-org/my-library")
        credentials {
            username = System.getenv("GITHUB_ACTOR")
                ?: project.findProperty("gpr.user") as String?
            password = System.getenv("GITHUB_TOKEN")
                ?: project.findProperty("gpr.key") as String?
        }
    }
}

dependencies {
    implementation("com.example:my-library:1.0.0")
}
```

### Pubblicazione Duale: GitHub Packages + Registry Pubblico

Un pattern comune e pubblicare contemporaneamente su GitHub Packages (per uso interno e CI) e sul registry pubblico (per la distribuzione esterna):

```yaml
# .github/workflows/dual-publish-gradle.yml
name: Dual Publish — GitHub Packages + Maven Central

on:
  release:
    types: [published]

jobs:
  publish-github:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
      - uses: gradle/actions/setup-gradle@v4
      - run: ./gradlew publishGprPublicationToGitHubPackagesRepository
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-maven-central:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
      - uses: gradle/actions/setup-gradle@v4
      - name: Publish to Maven Central
        run: ./gradlew publishToSonatype closeAndReleaseSonatypeStagingRepository
        env:
          SONATYPE_USERNAME: ${{ secrets.SONATYPE_USERNAME }}
          SONATYPE_PASSWORD: ${{ secrets.SONATYPE_PASSWORD }}
          GPG_PRIVATE_KEY: ${{ secrets.GPG_PRIVATE_KEY }}
          GPG_PASSPHRASE: ${{ secrets.GPG_PASSPHRASE }}
```

---

## GitHub Packages: Trusted Publishing e Provenance

### Cos'e il Trusted Publishing

A partire da luglio 2025, npm supporta il Trusted Publishing con OIDC in disponibilita generale (GA). Questa funzionalita elimina la necessita di gestire token npm (`NPM_TOKEN`) nei secret di GitHub: il workflow si autentica direttamente con il registry npm tramite OpenID Connect, utilizzando credenziali temporanee specifiche per l'esecuzione del workflow.

Il vantaggio fondamentale e l'eliminazione del rischio associato ai token long-lived: non ci sono token da ruotare, non ci sono token che possono essere esfiltrati o riutilizzati. Ogni pubblicazione e autenticata con credenziali usa-e-getta generate al momento dell'esecuzione.

### Configurazione del Trusted Publishing per npm

La configurazione richiede due passaggi: la registrazione del publisher su npmjs.com e la modifica del workflow GitHub Actions.

```
Passaggio 1: Configurare il Trusted Publisher su npmjs.com

1. Accedere a npmjs.com → Account Settings → Packages → [package]
2. Selezionare "Manage" → "Publishing" → "Add a trusted publisher"
3. Compilare:
   - Repository owner: my-org
   - Repository name: my-package
   - Workflow filename: publish.yml
   - Environment (opzionale): npm-publish
4. Salvare
```

```yaml
# .github/workflows/publish-trusted.yml
name: Publish npm (Trusted Publishing)

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    # L'environment e opzionale ma raccomandato
    # per aggiungere un gate di approvazione manuale
    environment: npm-publish
    permissions:
      contents: read
      id-token: write  # CRITICO: necessario per OIDC
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm test

      # Con trusted publishing, npm genera automaticamente
      # le attestazioni di provenance — nessun flag necessario
      - run: npm publish --access public
        # NOTA: NON serve NODE_AUTH_TOKEN con trusted publishing!
        # L'autenticazione avviene tramite OIDC automaticamente
```

### Provenance e Attestazioni npm

La provenance fornisce una prova crittografica verificabile di dove e come un pacchetto e stato costruito. Quando un pacchetto e pubblicato con provenance, npmjs.com mostra un badge "Provenance" nella pagina del pacchetto con link diretto al workflow che ha generato la build.

```bash
# Verificare la provenance di un pacchetto npm
npm audit signatures

# Ispezionare le attestazioni di un pacchetto specifico
npm view @org/package --json | jq '.dist.attestations'

# Il risultato contiene:
# - Il bundle Sigstore con la firma
# - Il predicato SLSA provenance v1.0
# - L'identita del workflow (URL, ref, SHA)
# - L'OIDC issuer (token.actions.githubusercontent.com)
```

Le informazioni contenute nell'attestazione di provenance includono:

```
Attestazione di provenance npm:
├── Build type: GitHub Actions
├── Source repository: github.com/org/package
├── Source ref: refs/tags/v1.2.3
├── Source commit: sha256:abc123...
├── Build workflow: .github/workflows/publish.yml
├── Runner environment: ubuntu-latest (GitHub-hosted)
├── Builder ID: https://github.com/actions/runner
├── Build timestamp: 2026-05-24T10:30:00Z
└── OIDC issuer: https://token.actions.githubusercontent.com
```

### Trusted Publishing per PyPI

PyPI supporta il trusted publishing con OIDC da ancora prima di npm. La configurazione e simile:

```yaml
# .github/workflows/publish-pypi-trusted.yml
name: Publish to PyPI (Trusted Publishing)

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # OIDC per trusted publishing

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install build dependencies
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun token necessario!
        # L'action usa OIDC per autenticarsi automaticamente con PyPI
```

### NuGet Trusted Publishing

Anche NuGet.org supporta il trusted publishing con OIDC, eliminando la necessita di gestire API key:

```yaml
# .github/workflows/publish-nuget-trusted.yml
name: Publish NuGet (Trusted Publishing)

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: 9.x

      - run: dotnet build --configuration Release
      - run: dotnet pack --configuration Release --output nupkgs

      - name: Publish with OIDC
        run: |
          dotnet nuget push nupkgs/*.nupkg \
            --source https://api.nuget.org/v3/index.json \
            --api-key az
        # Il trusted publishing su NuGet.org gestisce l'autenticazione
        # via OIDC senza API key tradizionale
```

---

## GitHub Packages: Pricing, Quote e Limiti di Storage

### Struttura dei Costi

GitHub Packages condivide la quota di storage con GitHub Actions. Lo storage e il transfer dati inclusi dipendono dal piano:

```
Limiti per piano GitHub (aggiornati al 2026):

Free:
├── Storage: 500 MB
├── Data transfer: 1 GB / mese
└── Nota: Actions artifacts e Packages condividono la quota

Pro:
├── Storage: 2 GB
├── Data transfer: 10 GB / mese
└── Stesso pool condiviso con Actions

Team:
├── Storage: 2 GB
├── Data transfer: 10 GB / mese
└── Per organizzazione

Enterprise:
├── Storage: 50 GB
├── Data transfer: 100 GB / mese
└── Per organizzazione
```

### Eccezioni Importanti

Non tutto il consumo di GitHub Packages conta verso la quota:

```
Consumo che NON conta verso la quota:
├── Container images PUBBLICHE su ghcr.io
│   ├── Storage: gratuito illimitato
│   └── Transfer: gratuito illimitato
├── Pacchetti di repository PUBBLICI
│   └── Transfer: gratuito
└── GITHUB_TOKEN in Actions
    └── Transfer all'interno dello stesso workflow: gratuito

Consumo che CONTA verso la quota:
├── Container images PRIVATE su ghcr.io
│   ├── Storage: conta
│   └── Transfer: conta
├── Pacchetti di repository PRIVATI
│   ├── Storage: conta
│   └── Transfer: conta
└── Download da client esterni (non Actions)
    └── Transfer: conta
```

### Monitoraggio dell'Utilizzo

```bash
# Verificare l'utilizzo corrente di storage
gh api /orgs/{org}/settings/billing/shared-storage --jq '
  {
    storage_used_gb: (.estimated_storage_for_month / 1024 | floor * 100 / 100),
    days_left_in_cycle: .days_left_in_billing_cycle,
    included_gb: (.included_minutes_used_for_packages / 1024)
  }'

# Elencare i pacchetti per dimensione (per identificare i piu grandi)
gh api /orgs/{org}/packages?package_type=container --paginate --jq '
  .[] | {name: .name, visibility: .visibility, created: .created_at}'

# Calcolare la dimensione totale delle immagini container
gh api /user/packages/container/{package}/versions --paginate --jq '
  [.[] | .metadata.container.tags] | flatten | length' 
```

### Strategie di Riduzione dei Costi

Per mantenere i costi sotto controllo, applicare le seguenti strategie:

1. **Rendere pubblici i pacchetti open source**: le immagini pubbliche su ghcr.io non consumano quota.
2. **Implementare retention policy aggressive**: eliminare tag non necessari (sha-*, pr-*) dopo periodi definiti.
3. **Usare multi-stage build**: ridurre la dimensione delle immagini container riduce lo storage consumato.
4. **Consolidare i layer Docker**: meno layer = meno storage overhead.
5. **Monitorare regolarmente**: impostare alert quando l'utilizzo supera il 80% della quota.

---

## GitHub Packages vs Registry Esterni — Confronto Dettagliato

La scelta tra GitHub Packages e i registry esterni (npmjs.com, Docker Hub, Maven Central, NuGet.org) dipende da fattori come autenticazione, rate limiting, costi, ecosistema e integrazione CI/CD. Questa sezione analizza le differenze per ciascun ecosistema.

### npm: GitHub Packages vs npmjs.com

| Aspetto | GitHub Packages npm | npmjs.com |
|---------|---------------------|-----------|
| **URL registry** | `npm.pkg.github.com` | `registry.npmjs.org` |
| **Scope obbligatorio** | Si (`@org/package`) | No (ma raccomandato) |
| **Autenticazione download** | Sempre richiesta (anche pacchetti pubblici) | Solo per pacchetti privati |
| **Rate limiting** | Nessun limite documentato per Actions | 2,880 req/ora per IP (utenti anonimi) |
| **Provenance (SLSA)** | Si (con `--provenance`) | Si (dal 2023) |
| **Trusted publishing (OIDC)** | Si | Si (dal 2024) |
| **Costo pacchetti privati** | Incluso nella quota del piano GitHub | $7/utente/mese (npm Teams) |
| **Ricerca pubblica** | Solo via API GitHub, non indicizzato globalmente | Indicizzato su npmjs.com, `npm search` |
| **Proxy/mirror** | No | Si (Verdaccio, Artifactory, Nexus) |
| **Granularita permessi** | Legata a repo/org GitHub | Team, 2FA enforcement, access tokens |
| **Download da CI esterni** | PAT o GitHub App token richiesto | Token npm standard |

**Quando scegliere GitHub Packages npm**: pacchetti interni all'organizzazione dove tutti i consumatori sono gia su GitHub. L'autenticazione unificata con `GITHUB_TOKEN` elimina la gestione di token npm separati. Ideale per design system interni, librerie condivise e SDK privati.

**Quando scegliere npmjs.com**: pacchetti open source destinati alla comunita globale. La ricerca pubblica, la compatibilita universale con tutti i client npm e l'assenza di autenticazione per il download sono vantaggi decisivi per l'adozione.

### Container: GHCR vs Docker Hub

| Aspetto | GHCR (ghcr.io) | Docker Hub |
|---------|----------------|------------|
| **Immagini pubbliche gratuite** | Storage e transfer illimitati | Storage illimitato, pull limitati |
| **Rate limiting pull** | Nessun limite documentato | 100 pull/6h (anonimo), 200 pull/6h (free auth) |
| **Rate limiting push** | Nessun limite documentato | Illimitato per piani a pagamento |
| **Retention immagini** | Nessuna scadenza automatica | 6 mesi inattivita (piano free, dal 2024) |
| **OCI Artifacts** | Si (Helm, WASM, ORAS) | Si (Helm, generico) |
| **Signing nativo** | Si (Sigstore/cosign via attestazioni) | Si (Docker Content Trust / Notary) |
| **Multi-arch manifest** | Si | Si |
| **Scansione vulnerabilita** | Trivy, Grype, Snyk (esterni) | Docker Scout (integrato) |
| **Costo team** | Incluso nel piano GitHub | $7/utente/mese (Pro), $11 (Team) |
| **Mirror/proxy** | No nativo | Si (Docker Hub mirror supportato) |

**Quando scegliere GHCR**: progetti con CI su GitHub Actions dove l'autenticazione tramite `GITHUB_TOKEN` semplifica la pipeline. L'assenza di rate limiting sui pull e un vantaggio critico per pipeline CI intensive. Le immagini pubbliche non consumano quota di storage.

**Quando scegliere Docker Hub**: immagini base ufficiali (Alpine, Ubuntu, Node), massima visibilita pubblica, compatibilita con ogni runtime container. Docker Scout integrato offre scansione vulnerabilita senza strumenti aggiuntivi.

### Maven: GitHub Packages vs Maven Central

| Aspetto | GitHub Packages Maven | Maven Central (Sonatype) |
|---------|----------------------|--------------------------|
| **Pubblicazione** | Deploy via `mvn deploy` con settings.xml | Staging + release via Sonatype OSSRH |
| **Firma GPG** | Non richiesta | Obbligatoria per release |
| **Review processo** | Nessuna (push diretto) | Review Sonatype per primo rilascio |
| **Namespace** | `groupId` libero | `groupId` deve corrispondere a dominio verificato |
| **Consumo senza auth** | Impossibile (auth sempre richiesta) | Aperto a tutti senza autenticazione |
| **Proxy-ability** | Configurabile come repo in Nexus/Artifactory | Default in ogni build tool |
| **Costo** | Incluso nel piano GitHub | Gratuito per open source |
| **Latenza primo rilascio** | Minuti | Ore/giorni (verifica namespace) |

**Quando scegliere GitHub Packages Maven**: librerie Java interne che non devono essere pubbliche. La pipeline e piu semplice (nessuna firma GPG, nessuna review Sonatype) e l'integrazione con GitHub Actions e nativa.

**Quando scegliere Maven Central**: qualsiasi libreria Java/Kotlin destinata alla comunita open source. Maven Central e il default di Maven, Gradle e ogni IDE Java. Non essere su Maven Central significa non esistere per la maggior parte degli sviluppatori Java.

### NuGet: GitHub Packages vs NuGet.org

| Aspetto | GitHub Packages NuGet | NuGet.org |
|---------|----------------------|-----------|
| **Push** | `dotnet nuget push` con source GitHub | `dotnet nuget push` con API key NuGet |
| **Autenticazione download** | Sempre richiesta | Solo per pacchetti privati (NuGet.org non li supporta) |
| **Ricerca pubblica** | Solo via API GitHub | Integrata in Visual Studio, `dotnet` CLI |
| **Symbol packages** | Non supportati | Si (`.snupkg`) |
| **Source Link** | Configurabile | Integrato |
| **Costo** | Incluso nel piano GitHub | Gratuito |

**Quando scegliere GitHub Packages NuGet**: pacchetti .NET interni all'organizzazione. Simile al caso Maven: semplifica l'autenticazione per team gia su GitHub.

**Quando scegliere NuGet.org**: qualsiasi pacchetto .NET pubblico. NuGet.org e il registry predefinito di dotnet CLI e Visual Studio. L'integrazione con symbol server e Source Link e superiore.

### Strategia Ibrida Multi-Registry

Molte organizzazioni adottano un approccio ibrido, pubblicando lo stesso pacchetto su piu registry contemporaneamente:

```yaml
# Publish su GitHub Packages E sul registry pubblico
- name: Pubblica su GitHub Packages
  run: dotnet nuget push **/*.nupkg --source github
  env:
    NUGET_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

- name: Pubblica su NuGet.org
  run: dotnet nuget push **/*.nupkg --source nuget.org
  env:
    NUGET_AUTH_TOKEN: ${{ secrets.NUGET_API_KEY }}
```

Questa strategia combina i vantaggi di entrambi i mondi: GitHub Packages per il consumo interno con autenticazione unificata, e il registry pubblico per la visibilita e l'adozione nella comunita. La chiave e automatizzare entrambi i push nella stessa pipeline CI per evitare drift tra le versioni.

---

## GitHub Container Registry (GHCR)

### Autenticazione

```bash
# Login a GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Oppure con gh CLI
gh auth token | docker login ghcr.io -u $(gh api user -q .login) --password-stdin
```

### Build e Push di Immagini

```bash
# Build
docker build -t ghcr.io/my-org/my-app:latest .
docker build -t ghcr.io/my-org/my-app:1.0.0 .

# Push
docker push ghcr.io/my-org/my-app:latest
docker push ghcr.io/my-org/my-app:1.0.0

# Pull
docker pull ghcr.io/my-org/my-app:latest
```

```yaml
# .github/workflows/docker-publish.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Multi-Platform Build

```yaml
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push multi-platform
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64,linux/arm/v7
          push: true
          tags: ${{ steps.meta.outputs.tags }}
```

---

## GHCR: OCI Artifacts — Helm Charts, WASM e Artefatti Generici

### Oltre le Immagini Container: OCI Artifacts

A partire da Helm 3.8, le OCI-based registries sono supportate nativamente. Questo significa che ghcr.io puo ospitare non solo immagini Docker, ma anche Helm charts, moduli WASM, SBOM, bundle di policy OPA e qualsiasi altro artefatto conforme alla specifica OCI Distribution. Questo unifica la gestione degli artefatti: lo stesso registry, le stesse credenziali, gli stessi permessi.

### Pubblicare Helm Charts su GHCR

```bash
# Login al registry OCI per Helm
echo $GITHUB_TOKEN | helm registry login ghcr.io -u USERNAME --password-stdin

# Creare il package dal chart
helm package charts/my-app/
# Output: my-app-1.2.0.tgz

# Push del chart su GHCR come artefatto OCI
helm push my-app-1.2.0.tgz oci://ghcr.io/my-org/charts

# Il chart sara disponibile come:
# oci://ghcr.io/my-org/charts/my-app:1.2.0

# Installare il chart direttamente da GHCR
helm install my-release oci://ghcr.io/my-org/charts/my-app --version 1.2.0
```

```yaml
# .github/workflows/publish-helm.yml
name: Publish Helm Chart

on:
  push:
    tags: ['chart-v*']

permissions:
  packages: write
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Helm
        uses: azure/setup-helm@v4
        with:
          version: v3.16.0

      - name: Login to GHCR
        run: echo ${{ secrets.GITHUB_TOKEN }} | helm registry login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Lint chart
        run: helm lint charts/my-app/

      - name: Template chart (dry run)
        run: helm template my-app charts/my-app/ --debug

      - name: Package chart
        run: helm package charts/my-app/

      - name: Push to GHCR
        run: |
          CHART_VERSION=$(grep '^version:' charts/my-app/Chart.yaml | awk '{print $2}')
          helm push my-app-${CHART_VERSION}.tgz oci://ghcr.io/${{ github.repository_owner }}/charts

      - name: Verify chart
        run: |
          CHART_VERSION=$(grep '^version:' charts/my-app/Chart.yaml | awk '{print $2}')
          helm show chart oci://ghcr.io/${{ github.repository_owner }}/charts/my-app --version ${CHART_VERSION}
```

### Pubblicare Moduli WASM su GHCR

I moduli WebAssembly possono essere distribuiti come artefatti OCI, facilitando il deployment in ambienti edge, serverless e browser:

```bash
# Push di un modulo WASM come artefatto OCI
# Usando ORAS (OCI Registry As Storage)
oras push ghcr.io/my-org/wasm/my-module:1.0.0 \
  --artifact-type application/vnd.wasm.module.v1+wasm \
  my-module.wasm:application/wasm

# Pull del modulo
oras pull ghcr.io/my-org/wasm/my-module:1.0.0

# Listare i tag disponibili
oras repo tags ghcr.io/my-org/wasm/my-module
```

```yaml
# .github/workflows/publish-wasm.yml
name: Publish WASM Module

on:
  release:
    types: [published]

permissions:
  packages: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown

      - name: Build WASM module
        run: cargo build --target wasm32-unknown-unknown --release

      - name: Install ORAS
        run: |
          ORAS_VERSION="1.2.0"
          curl -sLO "https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz"
          tar xzf oras_${ORAS_VERSION}_linux_amd64.tar.gz
          sudo mv oras /usr/local/bin/

      - name: Login to GHCR
        run: echo ${{ secrets.GITHUB_TOKEN }} | oras login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Push WASM to GHCR
        run: |
          oras push ghcr.io/${{ github.repository_owner }}/wasm/my-module:${{ github.ref_name }} \
            --artifact-type application/vnd.wasm.module.v1+wasm \
            target/wasm32-unknown-unknown/release/my_module.wasm:application/wasm
```

### Artefatti Generici con ORAS

ORAS (OCI Registry As Storage) permette di utilizzare ghcr.io come registry per qualsiasi tipo di file. Questo e utile per distribuire configurazioni, bundle ML, dataset e altri artefatti non tradizionali:

```bash
# Pubblicare un artefatto generico (es. modello ML)
oras push ghcr.io/my-org/models/sentiment-analyzer:v2.0 \
  --artifact-type application/vnd.ml.model.v1+onnx \
  model.onnx:application/octet-stream \
  config.json:application/json \
  tokenizer.json:application/json

# Aggiungere annotazioni
oras push ghcr.io/my-org/models/sentiment-analyzer:v2.0 \
  --annotation "org.opencontainers.image.description=Sentiment analysis ONNX model" \
  --annotation "com.example.accuracy=0.95" \
  --annotation "com.example.framework=pytorch-exported" \
  model.onnx:application/octet-stream

# Scaricare l'artefatto
oras pull ghcr.io/my-org/models/sentiment-analyzer:v2.0

# Copiare tra registry
oras copy ghcr.io/my-org/models/sentiment-analyzer:v2.0 \
  registry.example.com/models/sentiment-analyzer:v2.0
```

### Tabella Riassuntiva: Tipi di Artefatti OCI su GHCR

| Tipo Artefatto | Media Type | Strumento di Push | Caso d'Uso |
|---|---|---|---|
| Immagine Docker | `application/vnd.docker.distribution.manifest.v2` | docker push | Applicazioni containerizzate |
| Helm Chart | `application/vnd.cncf.helm.chart.content.v1.tar+gzip` | helm push | Deployment Kubernetes |
| Modulo WASM | `application/vnd.wasm.module.v1+wasm` | oras push | Edge computing, browser |
| SBOM | `application/spdx+json` | cosign attach sbom | Supply chain transparency |
| Firma Cosign | `application/vnd.dev.cosign.simplesigning.v1+json` | cosign sign | Verifica integrita |
| Modello ML | `application/octet-stream` | oras push | Distribuzione modelli AI |
| Policy OPA | `application/vnd.oci.image.layer.v1.tar+gzip` | oras push | Policy as Code |
| Configurazione | `application/json` | oras push | Configurazione distribuita |

---

## GHCR: Sicurezza e Scanning delle Immagini

### Scanning delle Vulnerabilita

```yaml
# .github/workflows/container-security.yml
name: Container Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Scan settimanale per nuove CVE

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t ghcr.io/${{ github.repository }}:scan .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'ghcr.io/${{ github.repository }}:scan'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fallisce il build se trova vulnerabilità critiche

      - name: Upload scan results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      # Scan alternativo con Grype (Anchore)
      - name: Run Grype scan
        uses: anchore/scan-action@v4
        with:
          image: 'ghcr.io/${{ github.repository }}:scan'
          fail-build: true
          severity-cutoff: high
```

### Image Signing con Cosign

```yaml
# Firmare le immagini container con Sigstore/Cosign (keyless)
      - name: Install Cosign
        uses: sigstore/cosign-installer@v3

      - name: Sign container image
        run: |
          cosign sign --yes \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
        env:
          COSIGN_EXPERIMENTAL: "1"

      # Verificare la firma
      - name: Verify signature
        run: |
          cosign verify \
            --certificate-identity "https://github.com/${{ github.repository }}/.github/workflows/docker-publish.yml@refs/heads/main" \
            --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
            ghcr.io/${{ github.repository }}:latest
```

### SBOM (Software Bill of Materials) per Container

```yaml
      # Generare SBOM per l'immagine container
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          image: ghcr.io/${{ github.repository }}:${{ github.sha }}
          format: spdx-json
          output-file: sbom.spdx.json

      - name: Attach SBOM to container image
        run: |
          cosign attach sbom --sbom sbom.spdx.json \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}

      # Allegare SBOM alla release GitHub
      - name: Upload SBOM as release asset
        if: startsWith(github.ref, 'refs/tags/')
        run: |
          gh release upload ${{ github.ref_name }} sbom.spdx.json
```

---

## GHCR: Attestazioni SLSA e Supply Chain Security

### Attestazioni di Build con GitHub Actions

GitHub fornisce l'action `actions/attest-build-provenance` che genera attestazioni SLSA (Supply-chain Levels for Software Artifacts) v1.0 firmate con certificati Sigstore. Queste attestazioni certificano crittograficamente dove e come un artefatto e stato costruito, raggiungendo il livello SLSA Build L2 senza configurazione aggiuntiva.

```yaml
# .github/workflows/build-attest-container.yml
name: Build, Push and Attest Container

on:
  push:
    tags: ['v*']

permissions:
  contents: read
  packages: write
  id-token: write        # Per firme Sigstore
  attestations: write    # Per generare attestazioni

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-attest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push
        id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

      - name: Generate build provenance attestation
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true

      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        id: sbom
        with:
          image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }}
          format: spdx-json
          output-file: sbom.spdx.json

      - name: Attest SBOM
        uses: actions/attest-sbom@v2
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.build.outputs.digest }}
          sbom-path: sbom.spdx.json
          push-to-registry: true
```

### Verificare le Attestazioni

```bash
# Verificare l'attestazione di build provenance di un'immagine
gh attestation verify oci://ghcr.io/my-org/my-app:v1.2.3 \
  --owner my-org

# Verificare con output dettagliato
gh attestation verify oci://ghcr.io/my-org/my-app@sha256:abc123... \
  --owner my-org \
  --format json | jq '.[] | {
    predicate_type: .verificationResult.statement.predicateType,
    builder: .verificationResult.statement.predicate.buildDefinition.buildType,
    source_repo: .verificationResult.statement.predicate.buildDefinition.externalParameters.workflow.repository
  }'

# Verificare l'SBOM attestato
gh attestation verify oci://ghcr.io/my-org/my-app:v1.2.3 \
  --owner my-org \
  --predicate-type https://spdx.dev/Document
```

### Pipeline Completa: Build, Scan, Sign, Attest

Questo workflow rappresenta una pipeline di sicurezza completa per container su ghcr.io, combinando build, vulnerability scanning, firma, SBOM e attestazione SLSA:

```yaml
# .github/workflows/secure-container-pipeline.yml
name: Secure Container Pipeline

on:
  push:
    tags: ['v*']

permissions:
  contents: read
  packages: write
  id-token: write
  attestations: write
  security-events: write

env:
  REGISTRY: ghcr.io
  IMAGE: ${{ github.repository }}

jobs:
  build-scan-sign-attest:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.build.outputs.digest }}
    steps:
      # 1. Checkout e login
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # 2. Setup build tools
      - uses: docker/setup-buildx-action@v3
      - uses: sigstore/cosign-installer@v3

      # 3. Build e push
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=sha

      - id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: mode=max
          sbom: true

      # 4. Vulnerability scan
      - name: Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.build.outputs.digest }}
          format: sarif
          output: trivy.sarif
          severity: CRITICAL,HIGH
          exit-code: '1'

      - name: Upload scan to Security tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy.sarif

      # 5. Sign con Cosign (keyless / Sigstore)
      - name: Sign container image
        run: |
          cosign sign --yes \
            ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.build.outputs.digest }}

      # 6. Build provenance attestation
      - name: Attest build provenance
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true

      # 7. SBOM generation e attestation
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        id: sbom
        with:
          image: ${{ env.REGISTRY }}/${{ env.IMAGE }}@${{ steps.build.outputs.digest }}
          format: spdx-json
          output-file: sbom.spdx.json

      - name: Attest SBOM
        uses: actions/attest-sbom@v2
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE }}
          subject-digest: ${{ steps.build.outputs.digest }}
          sbom-path: sbom.spdx.json
          push-to-registry: true

      # 8. Allegare SBOM alla release
      - name: Upload SBOM to release
        if: startsWith(github.ref, 'refs/tags/')
        run: gh release upload ${{ github.ref_name }} sbom.spdx.json --clobber
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Questa pipeline raggiunge SLSA Build L2 e fornisce una catena di fiducia verificabile end-to-end: dall'identita del builder (GitHub Actions), al codice sorgente (commit hash), al processo di build (workflow file), fino all'artefatto finale (digest dell'immagine container).

---

## Visibilita e Permessi dei Pacchetti

### Configurazione della Visibilità

```bash
# I pacchetti ereditano la visibilità del repository per default

# Cambiare la visibilità di un pacchetto container
gh api user/packages/container/my-app -X PATCH \
  -f visibility="public"

# Per organizzazioni
gh api orgs/{org}/packages/container/my-app -X PATCH \
  -f visibility="public"

# Listare i pacchetti
gh api user/packages?package_type=container

# Eliminare una versione specifica
gh api user/packages/container/my-app/versions/12345 -X DELETE
```

### Permessi Granulari

```bash
# Aggiungere un collaboratore a un pacchetto
gh api user/packages/container/my-app/collaborators/{username} -X PUT \
  -f permission="write"

# Permessi disponibili: read, write, admin
```

---

## Consumo di Pacchetti Privati tra Organizzazioni

### Il Problema del Cross-Organization Access

GitHub Packages non supporta nativamente la condivisione di pacchetti privati tra organizzazioni diverse. Un pacchetto privato di `org-platform` non e visibile a `org-frontend` nemmeno se le due organizzazioni appartengono alla stessa azienda (a meno che non si utilizzi GitHub Enterprise con la visibilita `internal`). Questo e uno dei limiti piu frequentemente incontrati dai team enterprise che adottano GitHub Packages.

### Soluzioni per Cross-Org Access

#### 1. Personal Access Token (PAT) — Approccio Semplice

Il metodo piu diretto consiste nel creare un PAT (classic o fine-grained) con permesso `read:packages` nell'organizzazione che ospita il pacchetto, e configurarlo come secret nell'organizzazione consumatrice:

```bash
# Nell'organizzazione consumatrice, configurare il token come secret
# EXTERNAL_PKG_TOKEN = PAT con read:packages su org-platform

# .npmrc per consumare pacchetti npm da un'altra org
@platform:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${EXTERNAL_PKG_TOKEN}
```

**Limitazioni**: il PAT e legato a un account utente specifico. Se l'utente lascia l'organizzazione, il token smette di funzionare. Per mitigare, creare un account macchina (machine user) dedicato.

#### 2. GitHub App Installation — Approccio Enterprise

Una GitHub App installata in entrambe le organizzazioni offre autenticazione machine-to-machine senza dipendere da account utente:

```yaml
# Workflow nell'organizzazione consumatrice
- name: Genera token GitHub App per org-platform
  id: app-token
  uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ vars.CROSS_ORG_APP_ID }}
    private-key: ${{ secrets.CROSS_ORG_APP_PRIVATE_KEY }}
    owner: org-platform

- name: Configura autenticazione npm
  run: |
    echo "@platform:registry=https://npm.pkg.github.com" >> .npmrc
    echo "//npm.pkg.github.com/:_authToken=${{ steps.app-token.outputs.token }}" >> .npmrc

- name: Installa dipendenze
  run: npm ci
```

La GitHub App deve avere il permesso `packages:read` e essere installata in entrambe le organizzazioni. Questo approccio e piu robusto del PAT perche il token e generato dinamicamente e ha una scadenza di 1 ora.

#### 3. Visibilita `internal` — Solo GitHub Enterprise

Le organizzazioni che fanno parte della stessa GitHub Enterprise possono impostare la visibilita dei pacchetti su `internal`. I pacchetti `internal` sono visibili a tutti i membri dell'Enterprise, indipendentemente dall'organizzazione di appartenenza:

```bash
# Impostare un pacchetto come internal (richiede Enterprise)
gh api /orgs/{org}/packages/npm/{package}/visibility -X PUT \
  -f visibility="internal"
```

Questa e la soluzione piu pulita ma richiede GitHub Enterprise Cloud o Server. I pacchetti `internal` sono accessibili senza configurazione aggiuntiva da qualsiasi workflow Actions all'interno dell'Enterprise.

### Configurazione Multi-Registry per npm

Quando un progetto consuma pacchetti da piu organizzazioni GitHub e da npmjs.com, il file `.npmrc` deve configurare registry multipli:

```ini
# .npmrc — configurazione multi-registry
# Pacchetti @platform/* dall'org-platform su GitHub Packages
@platform:registry=https://npm.pkg.github.com

# Pacchetti @design/* dall'org-design su GitHub Packages
@design:registry=https://npm.pkg.github.com

# Tutti gli altri pacchetti da npmjs.com (default)
registry=https://registry.npmjs.org

# Autenticazione per GitHub Packages (token diversi per org diverse)
//npm.pkg.github.com/:_authToken=${GH_PACKAGES_TOKEN}
```

> **Nota**: npm supporta un solo token per hostname del registry. Se `org-platform` e `org-design` sono su GitHub Packages, un singolo token con permessi `read:packages` su entrambe le organizzazioni e sufficiente (se si usa un PAT classic) oppure servono due GitHub App separate (se si usa fine-grained auth).

### Configurazione Multi-Registry per Maven/Gradle

Per progetti Java/Kotlin che consumano librerie da organizzazioni GitHub diverse:

```kotlin
// build.gradle.kts — repository multipli
repositories {
    mavenCentral()

    // Pacchetti dall'org-platform
    maven {
        url = uri("https://maven.pkg.github.com/org-platform/*")
        credentials {
            username = System.getenv("GITHUB_ACTOR") ?: "ci"
            password = System.getenv("GH_PACKAGES_TOKEN")
        }
    }

    // Pacchetti dall'org-shared-libs
    maven {
        url = uri("https://maven.pkg.github.com/org-shared-libs/*")
        credentials {
            username = System.getenv("GITHUB_ACTOR") ?: "ci"
            password = System.getenv("GH_PACKAGES_TOKEN")
        }
    }
}
```

### Raccomandazioni

1. **Enterprise**: usare visibilita `internal` quando possibile — e la soluzione con meno attrito.
2. **Multi-org senza Enterprise**: preferire GitHub App a PAT per evitare dipendenze da account individuali.
3. **Monitorare i token**: impostare scadenze sui PAT e notifiche di rotazione tramite workflow schedulati.
4. **Documentare la configurazione**: mantenere un README nel repository che elenca le dipendenze cross-org e le istruzioni di setup per nuovi sviluppatori.

---

## Lifecycle Management dei Pacchetti

### Pulizia Automatica delle Versioni Vecchie

```yaml
# .github/workflows/cleanup-packages.yml
name: Cleanup Old Package Versions

on:
  schedule:
    - cron: '0 3 * * 0'  # Ogni domenica alle 03:00
  workflow_dispatch:

jobs:
  cleanup-ghcr:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - name: Delete old container images
        uses: actions/delete-package-versions@v5
        with:
          package-name: 'my-app'
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: true

  cleanup-npm:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - name: Delete old npm versions
        uses: actions/delete-package-versions@v5
        with:
          package-name: '@my-org/my-package'
          package-type: 'npm'
          min-versions-to-keep: 20
          delete-only-pre-release-versions: true
```

```bash
# Pulizia manuale via CLI — eliminare immagini non taggate più vecchie di 30 giorni
gh api user/packages/container/my-app/versions --paginate --jq '
  .[] | select(.metadata.container.tags | length == 0) |
  select((.created_at | fromdateiso8601) < (now - 2592000)) |
  {id: .id, created: .created_at, tags: .metadata.container.tags}' | \
  jq -r '.id' | while read -r version_id; do
    gh api user/packages/container/my-app/versions/$version_id -X DELETE
    echo "Deleted version: $version_id"
  done
```

### Retention Policy per Container Images

```
Strategia di retention raccomandata:

Tag policy:
├── latest          → Sempre presente, punta all'ultimo build di main
├── v*.*.* (semver) → Conservare TUTTE le release stabili
├── v*.*.*-beta.*   → Conservare le ultime 5 pre-release
├── sha-*           → Conservare per 30 giorni
├── pr-*            → Eliminare dopo il merge della PR
└── untagged        → Eliminare dopo 7 giorni

Dimensione:
├── Monitorare la dimensione totale dei pacchetti (quota GitHub)
├── Alert se la dimensione supera il 80% della quota
└── Comprimere layer con docker-slim per immagini di produzione
```

### Deprecazione e Migrazione di Pacchetti

```bash
# Marcare una versione come deprecata (npm)
# Nel package.json della versione da deprecare:
npm deprecate @my-org/my-package@"< 2.0.0" "Versione 1.x deprecata. Migrare a v2.x entro 2026-12-31."

# Pubblicare un avviso di deprecazione nella release
gh release edit v1.9.0 \
  --notes "## DEPRECATO
Questa versione è deprecata e non riceverà più aggiornamenti di sicurezza.
Migrare a v2.x seguendo la [guida di migrazione](https://docs.example.com/migration-v2)."
```

---

## Strategie Avanzate di Retention e Cleanup

### actions/delete-package-versions@v5 — Pattern Avanzati

L'action ufficiale `actions/delete-package-versions` e lo strumento principale per la pulizia automatica dei pacchetti su GitHub Packages. La versione 5 introduce miglioramenti significativi nella gestione dei filtri e nella compatibilita con il nuovo sistema di permessi granulari.

#### Eliminazione Selettiva con Pattern Regex

```yaml
name: Cleanup Avanzato Pacchetti
on:
  schedule:
    - cron: '0 3 * * 0'  # Ogni domenica alle 03:00 UTC
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Eseguire in modalita dry-run (solo log, nessuna eliminazione)'
        type: boolean
        default: true

jobs:
  cleanup-preview-tags:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    strategy:
      matrix:
        package:
          - name: my-app
            type: container
          - name: my-lib
            type: npm
    steps:
      - name: Elimina versioni preview e sha piu vecchie di 14 giorni
        uses: actions/delete-package-versions@v5
        with:
          package-name: ${{ matrix.package.name }}
          package-type: ${{ matrix.package.type }}
          min-versions-to-keep: 5
          delete-only-pre-release-versions: true
          ignore-versions: '^(latest|stable|v\\d+\\.\\d+\\.\\d+)$'

      - name: Elimina tag sha-* e pr-* piu vecchi di 30 giorni
        uses: actions/delete-package-versions@v5
        with:
          package-name: ${{ matrix.package.name }}
          package-type: ${{ matrix.package.type }}
          min-versions-to-keep: 0
          delete-only-untagged-versions: false
          ignore-versions: '^v\\d+\\.\\d+\\.\\d+'
```

#### Limite di 100 Versioni per Esecuzione

L'API GitHub Packages restituisce un massimo di 100 versioni per chiamata. Per pacchetti con centinaia di versioni accumulate, una singola esecuzione dell'action non e sufficiente. Il workaround consiste nell'eseguire l'action in un loop:

```yaml
      - name: Pulizia iterativa (supera il limite di 100 versioni)
        run: |
          for i in $(seq 1 5); do
            echo "=== Iterazione $i ==="
            gh api \
              /orgs/${{ github.repository_owner }}/packages/container/my-app/versions \
              --paginate --jq '
                [.[] | select(
                  .metadata.container.tags | length == 0
                  or (.metadata.container.tags | any(test("^(sha-|pr-)")))
                )] | length' | while read -r count; do
              echo "Versioni candidate alla eliminazione: $count"
              if [ "$count" -eq 0 ]; then
                echo "Nessuna versione da eliminare. Uscita."
                exit 0
              fi
            done

            # Elimina batch di untagged versions
            gh api \
              /orgs/${{ github.repository_owner }}/packages/container/my-app/versions \
              --paginate --jq '
                .[] | select(.metadata.container.tags | length == 0) | .id' \
            | head -100 | while read -r version_id; do
              gh api \
                /orgs/${{ github.repository_owner }}/packages/container/my-app/versions/$version_id \
                -X DELETE 2>/dev/null || true
            done

            sleep 5  # Rate limiting gentile
          done
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### snok/container-retention-policy — Alternativa Specializzata

Per la pulizia specifica di immagini container su GHCR, `snok/container-retention-policy` offre funzionalita piu granulari rispetto all'action generica:

```yaml
      - name: Pulizia container con retention policy
        uses: snok/container-retention-policy@v3
        with:
          account: ${{ github.repository_owner }}
          token: ${{ secrets.GITHUB_TOKEN }}
          image-names: 'my-app,my-api,my-worker'
          cut-off: '14 days ago UTC'
          keep-n-most-recent: 3
          tag-selection: 'both'
          filter-tags: 'sha-*,pr-*,dev-*'
          skip-tags: 'latest,stable,production,v*.*.*'
```

Vantaggi rispetto a `delete-package-versions`: supporto nativo per GHCR, filtro per eta (`cut-off`), possibilita di specificare tag da preservare con glob pattern, e gestione automatica della paginazione oltre le 100 versioni.

### Preservazione dei Referrer Sigstore

Quando si eliminano versioni di immagini container firmate con Sigstore/cosign, e fondamentale non eliminare i referrer OCI (attestazioni, firme, SBOM) prima dell'immagine stessa. L'ordine corretto di eliminazione e:

1. Identificare le immagini candidate alla eliminazione
2. Verificare che non abbiano referrer attivi ancora necessari
3. Eliminare prima i referrer orfani (attestazioni di immagini gia eliminate)
4. Eliminare le immagini

```bash
# Elencare i referrer OCI di un'immagine
oras discover ghcr.io/myorg/my-app:v1.0.0 --output json | jq '.manifests'

# Verificare le attestazioni prima della eliminazione
cosign verify-attestation \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  ghcr.io/myorg/my-app:v1.0.0 2>/dev/null && echo "ATTENZIONE: attestazioni attive"
```

### Cleanup Schedulato con Dry-Run e Notifica

Una best practice e eseguire la pulizia in due fasi: prima un dry-run che notifica il team su Slack o Teams con il riepilogo delle versioni che verranno eliminate, poi l'eliminazione effettiva dopo un periodo di grazia:

```yaml
  notify-before-cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Genera report dry-run
        id: report
        run: |
          VERSIONS=$(gh api \
            /orgs/${{ github.repository_owner }}/packages/container/my-app/versions \
            --paginate --jq '
              [.[] | select(
                (.metadata.container.tags | length == 0) or
                (.metadata.container.tags | any(test("^(sha-|pr-)")))
              ) | {
                id: .id,
                tags: (.metadata.container.tags // ["<untagged>"] | join(", ")),
                created: .created_at
              }] | length')
          echo "count=$VERSIONS" >> "$GITHUB_OUTPUT"
          echo "### Cleanup Report" >> "$GITHUB_STEP_SUMMARY"
          echo "Versioni candidate alla eliminazione: **$VERSIONS**" >> "$GITHUB_STEP_SUMMARY"
          echo "Esecuzione effettiva schedulata tra 48 ore." >> "$GITHUB_STEP_SUMMARY"

      - name: Notifica Slack
        if: steps.report.outputs.count > 0
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_CLEANUP_WEBHOOK }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": ":broom: *Package Cleanup Schedulato*\n${{ steps.report.outputs.count }} versioni di `my-app` saranno eliminate tra 48 ore.\nReview: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }
```

### Matrice di Retention Raccomandata

| Tipo di tag | Retention | Motivazione |
|-------------|-----------|-------------|
| `v*.*.*` (semver) | Indefinita | Release ufficiali, potenzialmente in produzione |
| `latest`, `stable` | Indefinita | Tag di riferimento |
| `main`, `develop` | 30 giorni | Branch build, utili per debug recenti |
| `pr-*` | 7 giorni | Preview di PR, obsolete dopo il merge |
| `sha-*` | 14 giorni | Build per commit specifico, raramente necessarie a lungo |
| `<untagged>` | 3 giorni | Layer orfani, nessun valore dopo pochi giorni |
| `*-snapshot`, `*-preview` | 14 giorni | Versioni di test temporanee |
| `*-beta.*`, `*-rc.*` | 90 giorni | Pre-release, mantenere per rollback durante stabilizzazione |

---

## Best Practices

### GitHub Pages

1. **HTTPS sempre**: Abilitare "Enforce HTTPS" nelle impostazioni di Pages.
2. **Custom 404**: Creare un file `404.html` nella root per una pagina di errore personalizzata.
3. **Cache busting**: Usare hashing nei nomi dei file statici per invalidare la cache.
4. **Performance**: Ottimizzare immagini, minimizzare CSS/JS, usare lazy loading.
5. **Accessibilità**: Seguire le linee guida WCAG per rendere il sito accessibile.

### Releases

1. **Tag firmati**: Usare tag annotati e firmati con GPG per le release.
2. **Checksums**: Includere file di checksum (SHA-256) per gli asset binari.
3. **Release notes strutturate**: Usare `.github/release.yml` per categorizzare le modifiche.
4. **Pre-release per testing**: Pubblicare beta e release candidate prima della release stabile.
5. **Asset naming**: Usare nomi descrittivi per gli asset: `app-v1.0.0-linux-amd64.tar.gz`.

### Packages

1. **Scoping**: Usare sempre il scope dell'organizzazione (`@org/package`).
2. **Versioning immutabile**: Non ripubblicare la stessa versione con contenuto diverso.
3. **Automazione**: Pubblicare i pacchetti tramite CI/CD, non manualmente.
4. **Pulizia**: Eliminare periodicamente le versioni vecchie per risparmiare storage.
5. **Signing**: Firmare i pacchetti quando possibile per verificare l'integrità.

---

## Troubleshooting

### Pages: Sito Non Aggiornato

```bash
# Verificare lo stato del deploy
gh api repos/{owner}/{repo}/pages/builds

# Forzare un rebuild
gh api repos/{owner}/{repo}/pages/builds -X POST

# Verificare che il branch e il path siano corretti
gh api repos/{owner}/{repo}/pages --jq '.source'
```

### Pages: Custom Domain Non Funziona

```bash
# Verificare i DNS
dig docs.example.com +short
# Deve restituire gli IP di GitHub Pages o il CNAME

# Verificare il file CNAME
cat CNAME

# Verificare lo stato HTTPS
gh api repos/{owner}/{repo}/pages --jq '.https_enforced'
```

### Packages: Autenticazione Fallita

```bash
# npm: Verificare il token in .npmrc
cat ~/.npmrc

# Docker/GHCR: Verificare il login
docker login ghcr.io

# Verificare i permessi del token
# Il token deve avere scope "packages:write" per pubblicare
gh auth status
```

### Release: Asset Non Caricato

```bash
# Verificare i limiti di dimensione
# GitHub ha un limite di 2 GB per asset nelle release

# Upload manuale di un asset
gh release upload v1.0.0 dist/large-file.tar.gz --clobber
```

### GHCR: Pull Rate Limited

**Sintomi**: `docker pull` fallisce con errore 429 (Too Many Requests) o "rate limit exceeded".

**Causa**: GitHub Container Registry ha rate limit per utenti non autenticati (limitato) e autenticati (più generoso). Pull da CI/CD senza autenticazione raggiungono rapidamente il limite.

**Soluzione**:

```bash
# Autenticare sempre le operazioni docker, anche per pull
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# In GitHub Actions, usare il GITHUB_TOKEN automatico
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### Pages: Build Jekyll Fallisce

**Sintomi**: Il build automatico di Jekyll fallisce con errori di dipendenze Ruby o temi non trovati.

**Causa**: Il `Gemfile` contiene gemme non supportate da GitHub Pages, oppure il tema remoto non è accessibile.

**Soluzione**:

```bash
# Verificare le gemme supportate da GitHub Pages
# https://pages.github.com/versions/

# Usare Actions per un build Jekyll personalizzato anziché il builder automatico
# Settings → Pages → Build and deployment → Source: GitHub Actions

# Gemfile minimo compatibile con GitHub Pages:
cat > Gemfile << 'EOF'
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
gem "jekyll-feed"
gem "jekyll-seo-tag"
EOF
```

### Release Notes Generate Vuote o Poco Informative

**Sintomi**: Le release notes automatiche (`--generate-notes`) producono un elenco di commit poco utile o mancano PR importanti.

**Causa**: Le PR non hanno label, oppure il file `.github/release.yml` non è configurato correttamente per categorizzare le modifiche.

**Soluzione**:

```bash
# Verificare che le PR abbiano label appropriate
gh pr list --state merged --json number,title,labels --jq '
  .[] | select(.labels | length == 0) | {number, title}'

# Automatizzare l'assegnazione delle label con un workflow
# .github/workflows/label-pr.yml con actions come:
# - github/issue-labeler
# - actions/labeler
```

### Packages: Versione Già Pubblicata

**Sintomi**: La pubblicazione fallisce con "409 Conflict" o "Cannot publish over existing version".

**Causa**: Il versioning immutabile impedisce la ripubblicazione di una versione esistente. Questo è by design.

**Soluzione**:

```bash
# Opzione 1: Incrementare la versione
npm version patch  # Bumpa la patch version
npm publish

# Opzione 2: Eliminare la versione esistente (se non in produzione)
gh api user/packages/npm/my-package/versions/{version_id} -X DELETE

# Opzione 3: Per pre-release, usare suffissi univoci
npm version 1.0.0-beta.$(date +%s)
npm publish --tag beta
```

### Pages: HTTPS Non Funziona con Custom Domain

**Sintomi**: Dopo aver configurato un custom domain, HTTPS mostra un certificato invalido o non si attiva.

**Causa**: I record DNS non puntano agli IP corretti di GitHub Pages, la propagazione DNS non è completa, o il dominio ha un record CAA che impedisce a Let's Encrypt di emettere certificati.

**Soluzione**:

```bash
# Verificare i record DNS
dig +short docs.example.com
# Per CNAME: deve restituire username.github.io
# Per apex domain: deve restituire gli IP di GitHub Pages

# Verificare CAA record
dig CAA example.com +short
# Se presente, deve includere: 0 issue "letsencrypt.org"

# Verificare lo stato nel repository
gh api repos/{owner}/{repo}/pages --jq '{url: .url, status: .status, https_enforced: .https_enforced, cname: .cname}'

# Forzare il re-provisioning del certificato
# Settings → Pages → Remove custom domain → Save → Re-add domain → Save
```

### Pages: Cache CDN Mostra Contenuto Vecchio

**Sintomi**: Dopo un deploy riuscito (il build è verde), il sito continua a mostrare la versione precedente. Il problema persiste anche dopo un hard refresh nel browser.

**Causa**: La CDN di GitHub Pages ha una cache aggressiva (fino a 10 minuti). I file con lo stesso nome vengono serviti dalla cache. I service worker precedenti possono intercettare le richieste.

**Soluzione**:

```bash
# Verificare che il deploy sia effettivamente completato
gh api repos/{owner}/{repo}/pages/builds --jq '.[0] | {status: .status, created_at: .created_at}'

# Forzare il cache-busting aggiungendo hash ai nomi dei file
# Nel build tool (es. Vite, Webpack): output con content hash
# build: { rollupOptions: { output: { entryFileNames: '[name].[hash].js' } } }

# Verificare i cache headers restituiti
curl -I https://username.github.io/repo/index.html 2>/dev/null | grep -i cache

# Se un service worker vecchio è il problema, aggiungere un unregister script
# nel nuovo deploy per forzare la pulizia
```

### GHCR: Tag Sovrascritta Causa Inconsistenza

**Sintomi**: Un'immagine con tag `:latest` o un tag mutabile (es. `:v1`) è stata sovrascritta da un nuovo push. I deployment che usano quel tag ottengono una versione diversa da quella attesa.

**Causa**: I tag OCI sono mutabili per default. Un push con lo stesso tag sovrascrive il manifest precedente. Il digest dell'immagine cambia ma il tag resta lo stesso.

**Soluzione**:

```bash
# Verificare il digest attuale dell'immagine
docker inspect ghcr.io/org/app:latest --format '{{.RepoDigests}}'

# Confrontare con il digest atteso (dal build CI)
gh api user/packages/container/app/versions --jq '
  .[:5] | .[] | {id: .id, tags: .metadata.container.tags, created: .created_at}'

# Best practice: usare tag immutabili (SHA del commit o SemVer completo)
# Nel workflow CI:
# tags: ghcr.io/org/app:${{ github.sha }},ghcr.io/org/app:v1.2.3

# Pinning nei deployment: usare il digest invece del tag
# image: ghcr.io/org/app@sha256:abc123...
```

### npm Scoped Package Non Trovato dopo Pubblicazione

**Sintomi**: `npm install @org/package` fallisce con "404 Not Found" nonostante la pubblicazione sia riuscita su GitHub Packages.

**Causa**: npm cerca il package nel registry npm pubblico per default. Per i scoped packages su GitHub Packages, il client deve essere configurato per usare il registry GitHub per quello scope.

**Soluzione**:

```bash
# Configurare .npmrc per lo scope dell'organizzazione
echo "@org:registry=https://npm.pkg.github.com" >> .npmrc
echo "//npm.pkg.github.com/:_authToken=\${GITHUB_TOKEN}" >> .npmrc

# Verificare che il package sia pubblicato
gh api orgs/{org}/packages/npm/{package-name} --jq '{name: .name, visibility: .visibility}'

# Se il package è privato, assicurarsi che l'utente abbia accesso
# Settings → Packages → [package] → Manage access

# Per GitHub Actions, usare il setup-node con registry-url
# - uses: actions/setup-node@v4
#   with:
#     registry-url: https://npm.pkg.github.com
#     scope: '@org'
```

### Draft Release Pubblicata per Errore

**Sintomi**: Una release in stato draft è stata pubblicata accidentalmente, attivando workflow di deployment e notifiche agli utenti.

**Causa**: Un membro del team ha premuto "Publish release" oppure un workflow con `gh release edit --draft=false` è stato eseguito prematuramente.

**Soluzione**:

```bash
# Riconvertire a draft immediatamente (non elimina gli asset)
gh release edit v1.0.0 --draft

# Se il tag è già stato pushato e il deploy è partito:
# 1. Annullare i run del workflow attivati
gh run list --event release --limit 5
gh run cancel <run-id>

# 2. Verificare cosa è stato deployato
gh release view v1.0.0 --json assets --jq '.assets[].name'

# Per prevenire in futuro: usare environment protection rules
# Il workflow di release deve richiedere approvazione manuale
# per l'environment "production" prima di eseguire il deploy
```

### Multi-Platform Build ARM Fallisce

**Sintomi**: La build multi-architettura (amd64 + arm64) fallisce sulla piattaforma ARM con errori di compilazione, timeout, o segmentation fault.

**Causa**: GitHub Actions runners sono x86_64. Le build ARM usano QEMU emulation che è significativamente più lenta e può avere incompatibilità con alcuni toolchain. Pacchetti nativi ARM potrebbero non compilare correttamente sotto emulazione.

**Soluzione**:

```yaml
# Opzione 1: Build nativa con matrix strategy e runner ARM
strategy:
  matrix:
    include:
      - platform: linux/amd64
        runner: ubuntu-latest
      - platform: linux/arm64
        runner: ubuntu-24.04-arm  # Runner ARM nativo (GitHub-hosted)

# Opzione 2: Ottimizzare la build QEMU
- uses: docker/setup-qemu-action@v3
  with:
    platforms: arm64
- uses: docker/setup-buildx-action@v3
  with:
    driver-opts: |
      image=moby/buildkit:v0.12.0
      network=host

# Opzione 3: Build separata con merge del manifest
# Buildare amd64 e arm64 separatamente, poi creare un manifest list
# docker manifest create ghcr.io/org/app:v1 --amend ghcr.io/org/app:v1-amd64 --amend ghcr.io/org/app:v1-arm64
```

### Container Image Size Troppo Grande

**Sintomi**: L'immagine pubblicata su GHCR supera dimensioni ragionevoli (>1 GB), rallentando pull e deploy. Lo storage GHCR viene consumato rapidamente.

**Causa**: Il Dockerfile non usa multi-stage build, include tool di build non necessari al runtime, copia file non necessari (es. `.git`, `node_modules` di sviluppo), o usa un'immagine base troppo pesante.

**Soluzione**:

```dockerfile
# Multi-stage build per ridurre la dimensione finale
FROM node:22-bookworm AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS runtime
# Non copiare devDependencies, sorgenti, o tool di build
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER node
CMD ["node", "dist/server.js"]
```

```bash
# Verificare la dimensione dei layer
docker history ghcr.io/org/app:latest --human --no-trunc

# Usare .dockerignore per escludere file non necessari
cat > .dockerignore << 'EOF'
.git
.github
node_modules
*.md
tests/
.env*
EOF

# Confrontare dimensioni prima e dopo l'ottimizzazione
docker images ghcr.io/org/app --format "{{.Tag}}: {{.Size}}"
```

---

## FAQ — Domande Frequenti

### 1. Qual è la differenza tra GitHub Packages e npm/PyPI/Docker Hub?

GitHub Packages è un registry universale integrato nativamente con GitHub: stessi permessi del repository, autenticazione con GITHUB_TOKEN, visibilità collegata al repo. npm/PyPI/Docker Hub sono registry dedicati con ecosistemi più ampi. Best practice: pubblicare su entrambi — GitHub Packages per uso interno/organizzazione, registry pubblici per la distribuzione open source.

### 2. GitHub Pages è adatto per un sito in produzione?

Per siti statici (documentazione, blog, landing page), sì. Limitazioni: nessun server-side processing, nessun database, bandwidth non garantita per traffico alto, nessun SLA ufficiale. Per siti critici con SLA, considerare Cloudflare Pages, Vercel o Netlify che offrono funzionalità equivalenti con SLA e features aggiuntive (edge functions, A/B testing).

### 3. Posso usare GitHub Pages con un repository privato?

Sì, ma richiede un piano GitHub Pro (utenti) o GitHub Team/Enterprise (organizzazioni). Con il piano gratuito, Pages è disponibile solo per repository pubblici. Il sito Pages di un repository privato è comunque pubblicamente accessibile via URL — la privacy del repository non implica la privacy del sito.

### 4. Come gestisco le breaking changes nelle release?

Seguire il Semantic Versioning: incrementare il MAJOR version per breaking changes. Nella release note:
1. Documentare chiaramente cosa cambia
2. Fornire una guida di migrazione
3. Mantenere la versione precedente con supporto di sicurezza per almeno 6 mesi
4. Usare il periodo di deprecation per avvisare prima della rimozione

### 5. GHCR vs Docker Hub — quale usare?

| Aspetto | GHCR | Docker Hub |
|---------|------|------------|
| Integrazione GitHub | Nativa (GITHUB_TOKEN) | Token separato |
| Rate limit (free) | 500/min autenticato | 100 pull/6h non autenticato |
| Immagini private | Gratuito (entro quota) | 1 repo privato gratuito |
| Scanning CVE | Con Dependabot | Con Docker Scout |
| SBOM | Via Cosign | Via Docker Scout |

Per progetti GitHub: GHCR. Per distribuzione pubblica: entrambi (multi-registry).

### 6. Come faccio rollback di una release?

```bash
# Opzione 1: Creare una nuova release con il fix
gh release create v1.0.1 --title "v1.0.1 - Hotfix" --notes "Rollback di v1.0.0 - fix critico"

# Opzione 2: Eliminare la release (non il tag)
gh release delete v1.0.0 --yes
# Ri-creare con il contenuto corretto
gh release create v1.0.0 --target <commit-sha-corretto> --title "v1.0.0"
```

### 7. Come posso pubblicare lo stesso pacchetto su GitHub Packages E npm/PyPI?

Usare un workflow con job paralleli che pubblicano su entrambi i registry:

```yaml
jobs:
  publish-github:
    steps:
      - uses: actions/setup-node@v4
        with:
          registry-url: 'https://npm.pkg.github.com'
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-npm:
    steps:
      - uses: actions/setup-node@v4
        with:
          registry-url: 'https://registry.npmjs.org'
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 8. GitHub Pages supporta i redirect?

Non nativamente (no `.htaccess`, no server-side redirect). Opzioni:
- **HTML meta refresh**: `<meta http-equiv="refresh" content="0;url=https://...">`
- **JavaScript redirect**: `window.location.replace('...')`
- **Jekyll redirect plugin**: `jekyll-redirect-from` (supportato da GitHub Pages)
- **Custom 404**: Gestire i percorsi modificati con un `404.html` intelligente

### 9. Come monitoro il download delle release?

```bash
# Statistiche di download per release
gh api repos/{owner}/{repo}/releases --jq '
  .[] | {tag: .tag_name, downloads: [.assets[].download_count] | add}'

# Download totali per asset specifico
gh api repos/{owner}/{repo}/releases --jq '
  [.[] | .assets[] | {name: .name, downloads: .download_count}] | sort_by(-.downloads)'
```

### 10. Qual è il costo di GitHub Packages?

GitHub Packages include storage e transfer gratuiti nei limiti del piano:
- **Free**: 500 MB storage, 1 GB transfer/mese
- **Pro**: 2 GB storage, 10 GB transfer/mese
- **Team**: 2 GB storage, 10 GB transfer/mese
- **Enterprise**: 50 GB storage, 100 GB transfer/mese

Oltre i limiti, il pricing è pay-as-you-go. Le immagini container pubbliche su GHCR non consumano la quota di transfer.

### 11. Come posso servire più siti Pages da un'unica organizzazione?

Ogni repository può avere il proprio sito Pages. L'organizzazione ha un sito "principale" da un repository `{org}.github.io`, e ogni altro repository serve il proprio sito su `{org}.github.io/{repo}`. Per custom domain, ogni repository può avere il proprio dominio personalizzato.

### 12. Come gestisco i secret nei workflow di pubblicazione?

Non committare MAI i token di pubblicazione nel codice. Usare:
1. **Repository secrets**: Settings → Secrets → Actions
2. **Environment secrets**: Per token con protezione aggiuntiva (required reviewers)
3. **OIDC Trusted Publishing** (PyPI, npm): Nessun token da gestire — il workflow si autentica direttamente
4. **GITHUB_TOKEN**: Per pubblicare su GitHub Packages — automatico, nessuna configurazione

### 13. Posso avere release automatiche per ogni merge su main?

Sì, usando Release Please o un workflow personalizzato. L'approccio raccomandato è: ogni merge su main crea/aggiorna una "Release PR" che, quando mergiata, crea la release. Per continuous delivery, creare una release automatica ad ogni tag con `gh release create`.

### 14. Come impedisco la pubblicazione accidentale di pacchetti da branch non-main?

Usare environment protection rules:

```yaml
jobs:
  publish:
    environment: npm-publish  # Environment con protezione
    if: github.ref == 'refs/heads/main'  # Doppia protezione via condizione
```

### 15. GitHub Pages supporta i form?

No, Pages è un servizio di hosting statico senza backend. Per form, usare:
- **Formspree** / **Getform**: Servizi esterni che ricevono form submissions
- **Netlify Forms**: Se si migra da Pages a Netlify
- **Google Forms embedded**: iframe con Google Forms
- **GitHub Issues via API**: Submit form → GitHub Issue via API client-side (richiede token pubblico)

---

## Esercizi

### Esercizio 1 — GitHub Pages con Custom Domain e HTTPS

**Obiettivo:** Configurare un sito GitHub Pages production-ready con dominio personalizzato.

1. Creare un repository con un sito statico (HTML/CSS o generatore come Hugo/Jekyll)
2. Abilitare GitHub Pages dal branch `main` (directory `/docs` o root)
3. Configurare un custom domain con record DNS: `CNAME` per `www` e `A`/`AAAA` per apex domain
4. Verificare che HTTPS venga abilitato automaticamente (Let's Encrypt)
5. Creare un workflow che esegue il build e il deploy su ogni push al branch `main`

### Esercizio 2 — Release Automation con Semantic Versioning

**Obiettivo:** Automatizzare la creazione di release con changelog generato dai commit.

1. Configurare il repository per usare Conventional Commits (`feat:`, `fix:`, `chore:`)
2. Creare un workflow che si attiva su push di tag `v*` e genera una release con note automatiche
3. Configurare `.github/release.yml` con categorie: Features, Bug Fixes, Breaking Changes, Other
4. Creare almeno 5 commit con tipi diversi, taggare `v1.0.0`, e verificare il changelog generato
5. Testare una release con breaking change (`feat!:`) e verificare che appaia nella sezione corretta

### Esercizio 3 — Pubblicazione npm su GitHub Packages

**Obiettivo:** Pubblicare un pacchetto npm su GitHub Packages con workflow automatizzato.

1. Creare un pacchetto npm con `package.json` configurato per `@org/package-name` e registry `https://npm.pkg.github.com`
2. Creare un workflow che pubblica il pacchetto su push di tag: `npm publish` con `NODE_AUTH_TOKEN`
3. Configurare `.npmrc` per autenticazione al registry GitHub Packages
4. Pubblicare almeno due versioni (1.0.0 e 1.1.0) e verificare che entrambe appaiano nel tab Packages
5. Installare il pacchetto pubblicato in un altro progetto e verificare che funzioni

### Esercizio 4 — Container Registry (ghcr.io) Multi-Arch

**Obiettivo:** Pubblicare un'immagine Docker multi-architettura su GitHub Container Registry.

1. Creare un Dockerfile multi-stage per un'applicazione (Go, Node.js o Python)
2. Creare un workflow con `docker/build-push-action` che costruisce e pubblica su `ghcr.io`
3. Configurare il build multi-architettura con `platforms: linux/amd64,linux/arm64`
4. Taggare l'immagine con: `latest`, versione semver dal tag, e SHA del commit
5. Verificare che l'immagine sia scaricabile con `docker pull ghcr.io/org/image:tag` e che il manifest multi-arch sia corretto

### Esercizio 5 — Cleanup e Retention Policy

**Obiettivo:** Implementare una strategia di pulizia automatica per pacchetti e immagini.

1. Creare un workflow schedulato (cron settimanale) che usa `gh api` per elencare le versioni di un pacchetto
2. Eliminare automaticamente le versioni piu vecchie di 90 giorni, mantenendo almeno le ultime 5
3. Per le immagini Docker: eliminare i tag `sha-*` piu vecchi di 30 giorni, mantenendo `latest` e i tag `v*`
4. Aggiungere un dry-run mode che elenca le versioni da eliminare senza cancellarle
5. Inviare una notifica Slack/email con il riepilogo delle versioni eliminate

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Docs — GitHub Pages** — Hosting gratuito di siti statici da repository GitHub. <https://docs.github.com/en/pages> (consultato: 2026-05-24)
- **GitHub Docs — Releases** — Creazione e gestione delle release con note e asset. <https://docs.github.com/en/repositories/releasing-projects-on-github> (consultato: 2026-05-24)
- **GitHub Docs — GitHub Packages** — Registry di pacchetti integrato con GitHub. <https://docs.github.com/en/packages> (consultato: 2026-05-24)
- **GitHub Docs — Container Registry** — Pubblicazione e gestione di immagini OCI su ghcr.io. <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry> (consultato: 2026-05-24)
- **GitHub Docs — Custom Domain** — Configurazione di domini personalizzati per GitHub Pages. <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site> (consultato: 2026-05-24)
- **Semantic Versioning** — Specifica per il versionamento semantico (MAJOR.MINOR.PATCH). <https://semver.org/> (consultato: 2026-05-24)
- **Jekyll Documentation** — Documentazione del generatore di siti statici integrato con GitHub Pages. <https://jekyllrb.com/docs/> (consultato: 2026-05-24)
- **Docker Buildx** — Plugin Docker per build multi-piattaforma e caching avanzato. <https://docs.docker.com/buildx/working-with-buildx/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Chacon S., Straub B., *Pro Git* (2nd ed.), Apress, 2014. Disponibile gratuitamente su <https://git-scm.com/book>.
- Nickoloff S., Kuenzli S., *Docker in Action* (2nd ed.), Manning, 2019.
- Preston-Werner T., *Semantic Versioning 2.0.0* — Specifica fondamentale per il versionamento. <https://semver.org/>

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [13 — Issues, Projects e Collaborazione](13-github-issues-projects-collaboration.md) | Le release si collegano alle milestone e alle issue chiuse per generare changelog significativi |
| [17 — GitHub Actions Workflow e Sintassi](17-github-actions-workflow-sintassi.md) | I workflow di pubblicazione utilizzano la sintassi e i trigger (push tag, workflow_dispatch) trattati qui |
| [18 — GitHub Actions Avanzate](18-github-actions-avanzate.md) | Le tecniche avanzate (matrix, caching, artifacts) ottimizzano i workflow di build e pubblicazione |
| [19 — GitHub Actions CI/CD Ricette](19-github-actions-ci-cd-ricette.md) | Le ricette CI/CD includono pipeline complete di build, test e pubblicazione |
| [24 — DevOps Completo con GitHub](24-devops-completo-con-github.md) | Il ciclo completo DevOps integra packages, releases e deploy trattati in questo modulo |
| [27 — Supply Chain e Attestation SLSA](27-supply-chain-attestation-slsa.md) | La provenance e le attestazioni SLSA si applicano ai pacchetti e alle release pubblicati |

---

## Glossario

| Termine | Definizione |
|---|---|
| **GitHub Pages** | Servizio di hosting statico gratuito che pubblica siti web direttamente da un repository GitHub, con supporto per Jekyll e custom domain. |
| **GitHub Packages** | Registry di pacchetti integrato con GitHub che supporta npm, Maven, NuGet, RubyGems e container OCI. |
| **ghcr.io** | GitHub Container Registry: registry OCI-compliant per immagini Docker, con autenticazione via GITHUB_TOKEN e permessi granulari. |
| **Release** | Snapshot distribuibile di un progetto, associato a un tag Git, con note di rilascio e asset binari allegati. |
| **Semantic versioning** | Schema di versionamento MAJOR.MINOR.PATCH dove MAJOR indica breaking changes, MINOR nuove funzionalita e PATCH correzioni. |
| **Changelog** | Documento che elenca le modifiche tra versioni, generato automaticamente dai commit (Conventional Commits) o redatto manualmente. |
| **Tag** | Riferimento Git immutabile che punta a un commit specifico, usato per marcare le release (es. `v1.2.3`). |
| **OCI** | Open Container Initiative: standard per formati di immagini container e runtime, supportato da ghcr.io e tutti i registry moderni. |
| **Custom domain** | Dominio personalizzato (es. `docs.example.com`) configurato per un sito GitHub Pages tramite record DNS CNAME o A. |
| **Jekyll** | Generatore di siti statici in Ruby, integrato nativamente con GitHub Pages per la trasformazione di Markdown in HTML. |
| **Multi-arch build** | Build di immagini Docker per piu architetture (amd64, arm64) tramite Docker Buildx e QEMU emulation. |
| **Asset** | File binario allegato a una release GitHub (installer, archivio, documentazione) scaricabile dagli utenti. |
| **Retention policy** | Strategia di pulizia automatica che elimina versioni vecchie di pacchetti o immagini per risparmiare spazio e costi di storage. |
| **CNAME** | Record DNS Canonical Name che mappa un sottodominio a un altro hostname, usato per i custom domain di GitHub Pages. |
| **Conventional Commits** | Specifica per messaggi di commit strutturati (`feat:`, `fix:`, `chore:`) che abilita la generazione automatica di changelog e versioni. |
