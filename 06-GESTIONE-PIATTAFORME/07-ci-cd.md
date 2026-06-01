---
corso: "Gestione Piattaforme e DevOps"
fase: "2 — IaC e CI/CD"
modulo: 7
titolo: "CI/CD — Piattaforme e Pipeline"
versione: "GitHub Actions / GitLab CI 17 / ArgoCD 2.x"
livello: "Intermedio"
prerequisiti: ["04-infrastructure-as-code", "06-docker-avanzato"]
obiettivi:
  - "Progettare pipeline CI/CD dichiarative con GitHub Actions, GitLab CI e Jenkins"
  - "Implementare SHA pinning, OIDC authentication e secret management nelle pipeline"
  - "Configurare deployment GitOps con ArgoCD e Flux per ambienti multi-stage"
  - "Applicare strategie di deployment progressivo: canary, blue-green, rolling update"
  - "Monitorare le DORA metrics e ottimizzare la pipeline per feedback rapido"
tag: [ci-cd, github-actions, gitlab-ci, jenkins, argocd, flux, gitops, dora-metrics]
---

# CI/CD — Piattaforme e Pipeline

> **Modulo 07** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Progettare pipeline CI/CD dichiarative con GitHub Actions, GitLab CI e Jenkins
> 2. Implementare SHA pinning, OIDC authentication e secret management nelle pipeline
> 3. Configurare deployment GitOps con ArgoCD e Flux per ambienti multi-stage
> 4. Applicare strategie di deployment progressivo: canary, blue-green, rolling update
> 5. Monitorare le DORA metrics e ottimizzare la pipeline per feedback rapido
>
> **Prerequisiti:** [Infrastructure as Code](04-infrastructure-as-code.md) · [Docker Avanzato](06-docker-avanzato.md)
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida

1. **SHA pinning + Renovate.** Mai `@latest` o `@v1`; pin a SHA con auto-update.
2. **`permissions: {}` minimo, espandi solo dove serve.**
3. **OIDC > long-lived secret per cloud auth.** AWS, Azure, GCP supportano.
4. **GitOps (ArgoCD/Flux) > push-based deploy.** Git e source of truth.


## Indice

1. [Panoramica](#1-panoramica)
2. [GitHub Actions](#2-github-actions)
3. [GitLab CI](#3-gitlab-ci)
4. [Jenkins](#4-jenkins)
5. [ArgoCD e GitOps](#5-argocd-e-gitops)
6. [Pipeline Patterns](#6-pipeline-patterns)
7. [Testing in Pipeline](#7-testing-in-pipeline)
8. [Artifact Management](#8-artifact-management)
9. [Notification e Monitoring](#9-notification-e-monitoring)
10. [Best Practices](#10-best-practices)
11. [CI/CD Security e Supply Chain](#11-cicd-security-e-supply-chain)
12. [CI/CD per Container](#12-cicd-per-container)
13. [Secret Management nelle Pipeline](#13-secret-management-nelle-pipeline)
14. [Infrastructure as Code nelle Pipeline](#14-infrastructure-as-code-nelle-pipeline)
15. [CI/CD Observability Avanzata](#15-cicd-observability-avanzata)
16. [CI/CD Performance Optimization](#16-cicd-performance-optimization)

---

## 1. Panoramica

### 1.1 Concetti Fondamentali di CI/CD

**Continuous Integration (CI)** e **Continuous Delivery/Deployment (CD)** rappresentano le pratiche fondamentali dell'ingegneria del software moderna. L'obiettivo primario e' automatizzare l'intero ciclo di vita del software, dalla scrittura del codice fino alla distribuzione in produzione, riducendo errori manuali e accelerando il time-to-market.

**Continuous Integration** prevede che ogni sviluppatore integri il proprio codice nel branch principale con frequenza elevata (idealmente piu' volte al giorno). Ogni integrazione attiva una pipeline automatizzata che compila il codice, esegue i test e verifica la qualita'. Questo approccio permette di individuare conflitti e regressioni in tempi brevissimi, evitando il cosiddetto "integration hell" tipico dei rilasci monolitici.

**Continuous Delivery** estende la CI garantendo che il codice sia sempre in uno stato rilasciabile. Dopo il superamento di tutti i test e le verifiche di qualita', l'artefatto e' pronto per il deployment in produzione con un singolo click o approvazione manuale.

**Continuous Deployment** rappresenta il livello piu' avanzato: ogni modifica che supera l'intera pipeline viene automaticamente distribuita in produzione senza intervento umano. Questa pratica richiede una copertura di test estremamente solida e meccanismi di rollback affidabili.

### 1.2 Stadi della Pipeline

Una pipeline CI/CD tipica si articola in fasi sequenziali, ciascuna con responsabilita' specifiche:

```
Source → Build → Test → Security Scan → Package → Deploy (Staging) → Approval → Deploy (Production) → Verify
```

- **Source**: trigger del pipeline al push o alla creazione di una pull request.
- **Build**: compilazione del codice sorgente, risoluzione delle dipendenze.
- **Test**: esecuzione di unit test, integration test e, eventualmente, test end-to-end.
- **Security Scan**: analisi statica (SAST) e dinamica (DAST) per vulnerabilita'.
- **Package**: creazione dell'artefatto (container image, pacchetto, bundle).
- **Deploy Staging**: distribuzione nell'ambiente di pre-produzione.
- **Approval Gate**: approvazione manuale o automatica per procedere.
- **Deploy Production**: distribuzione nell'ambiente di produzione.
- **Verify**: health check, smoke test e monitoraggio post-deployment.

### 1.3 Strategie di Deployment

Le strategie di deployment determinano come le nuove versioni vengono introdotte nell'ambiente di produzione, bilanciando velocita', sicurezza e disponibilita'.

**Blue-Green Deployment**: si mantengono due ambienti identici, denominati "Blue" (produzione attuale) e "Green" (nuova versione). Il traffico viene instradato interamente verso l'ambiente Green una volta verificata la stabilita'. In caso di problemi, il rollback e' istantaneo: basta redirigere il traffico verso Blue. Il principale svantaggio e' il costo di mantenere due ambienti completi in parallelo.

**Canary Deployment**: la nuova versione viene distribuita inizialmente a un sottoinsieme ridotto di utenti (ad esempio il 5%), monitorando attentamente metriche e errori. Se tutto procede correttamente, la percentuale viene incrementata progressivamente (10%, 25%, 50%, 100%). Questa strategia minimizza il rischio esponendo solo una frazione degli utenti a eventuali problemi.

**Rolling Deployment**: le istanze vengono aggiornate una alla volta (o in piccoli batch). In ogni momento, una parte del cluster esegue la vecchia versione e una parte la nuova. Questa strategia non richiede infrastruttura duplicata ma introduce un periodo di coesistenza tra versioni che puo' causare problemi di compatibilita'.

**Recreate Deployment**: tutte le istanze della vecchia versione vengono terminate prima di avviare quelle nuove. Semplice da implementare ma comporta un periodo di downtime. Adatto solo ad ambienti non critici o a finestre di manutenzione pianificate.

---

## 2. GitHub Actions

> **Riferimento incrociato**: per una trattazione approfondita sulla struttura dei workflow, sintassi YAML e funzionalita' di base, consultare `07-GITHUB-E-GITACTIONS/04-github-actions.md`.

### 2.1 Riepilogo della Struttura del Workflow

Un workflow GitHub Actions e' definito in un file YAML all'interno di `.github/workflows/`. La struttura gerarchica e': **Workflow → Job → Step**.

```yaml
name: CI Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test
```

I job vengono eseguiti in parallelo per default; le dipendenze tra job si esprimono con la keyword `needs`.

### 2.2 Pattern Avanzati

**Matrix Strategy** permette di eseguire lo stesso job su combinazioni multiple di parametri:

```yaml
jobs:
  test:
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest]
      fail-fast: false
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci && npm test
```

**Reusable Workflows** consentono di definire workflow riutilizzabili invocabili da altri repository tramite `workflow_call`:

```yaml
# .github/workflows/reusable-deploy.yml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      DEPLOY_KEY:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy to ${{ inputs.environment }}
        run: ./deploy.sh
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

**Composite Actions** raggruppano piu' step in un'azione personalizzata riutilizzabile, favorendo il principio DRY.

### 2.3 Self-Hosted Runners

I self-hosted runner permettono di eseguire i workflow su infrastruttura propria invece che sugli ambienti GitHub-hosted. Sono utili quando si necessita di hardware specifico (GPU, ARM), accesso a risorse di rete interne o tempi di esecuzione piu' lunghi dei limiti standard.

```yaml
jobs:
  build:
    runs-on: [self-hosted, linux, x64, gpu]
    steps:
      - uses: actions/checkout@v4
      - run: ./train-model.sh
```

Considerazioni operative: i self-hosted runner richiedono manutenzione dell'ambiente (aggiornamenti OS, pulizia della cache, sicurezza). Per ambienti Kubernetes, il progetto **Actions Runner Controller (ARC)** permette di orchestrare runner come pod effimeri, garantendo isolamento e scalabilita' automatica.

### 2.4 OIDC (OpenID Connect)

GitHub Actions supporta OIDC per autenticarsi presso cloud provider (AWS, Azure, GCP) senza memorizzare credenziali long-lived nei secrets. Il workflow richiede un token JWT a GitHub, che viene scambiato con credenziali temporanee dal cloud provider.

```yaml
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-arn: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: eu-west-1
      - name: Deploy to S3
        run: aws s3 sync ./build s3://my-bucket
```

OIDC elimina il rischio di credenziali compromesse e segue il principio del privilegio minimo grazie a token con scadenza breve e scope limitato.

### 2.5 Composite Actions — Deep Dive

Le **Composite Actions** permettono di raggruppare piu' step in un'unica action riutilizzabile, definita in un file `action.yml`. A differenza dei Reusable Workflows (che operano a livello di job), le Composite Actions operano a livello di step e possono essere richiamate all'interno di qualsiasi job, offrendo granularita' piu' fine.

**Struttura di una Composite Action:**

```yaml
# .github/actions/setup-and-test/action.yml
name: 'Setup and Test'
description: 'Installa dipendenze, esegue lint e test'
inputs:
  node-version:
    description: 'Versione di Node.js'
    required: false
    default: '20'
  working-directory:
    description: 'Directory di lavoro'
    required: false
    default: '.'
outputs:
  coverage-report:
    description: 'Path del report di copertura'
    value: ${{ steps.test.outputs.coverage-path }}

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@b23f66c5e6a7e38c4e79e2a04e3a16e5de5b2dab
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'
        cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json

    - name: Install dependencies
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: npm ci --prefer-offline --no-audit

    - name: Lint
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: npm run lint

    - name: Test with coverage
      id: test
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: |
        npm test -- --coverage --coverageReporters=text --coverageReporters=cobertura
        echo "coverage-path=${{ inputs.working-directory }}/coverage/cobertura-coverage.xml" >> "$GITHUB_OUTPUT"
```

**Utilizzo nel workflow:**

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-and-test
        with:
          node-version: '20'
          working-directory: 'packages/api'
```

**Differenze chiave tra Composite Actions e Reusable Workflows:**

| Aspetto | Composite Action | Reusable Workflow |
|---|---|---|
| Livello di astrazione | Step (dentro un job) | Job completo (con `runs-on` proprio) |
| `runs-on` | Ereditato dal job chiamante | Definito nel workflow riutilizzabile |
| Services | Non supportati direttamente | Supportati |
| Matrix strategy | Non applicabile (singolo step) | Supportata |
| Secrets | Passati come input | Passati via `secrets:` o `secrets: inherit` |
| Visibilita' nell'UI | Step singolo espandibile | Job separato nel grafo |
| Nesting | Puo' chiamare altre composite actions | Puo' chiamare altri reusable workflows (max 4 livelli) |

La scelta tra i due dipende dal livello di isolamento richiesto: le Composite Actions sono ideali per raggruppare step correlati (setup, lint, test) mantenendo un unico job; i Reusable Workflows per definire pipeline complete con ambienti e servizi dedicati.

### 2.6 Environments e Protection Rules

Gli **Environments** in GitHub Actions rappresentano target di deployment (development, staging, production) con regole di protezione configurabili. Ogni environment puo' definire:

- **Required reviewers**: uno o piu' approvatori devono autorizzare il deployment prima che il job proceda. Fino a 6 reviewer per environment.
- **Wait timer**: un ritardo configurabile (fino a 43.200 minuti / 30 giorni) prima dell'esecuzione del job.
- **Deployment branches/tags**: restrizioni su quali branch o tag possono effettuare deployment nell'environment.
- **Environment secrets**: secrets specifici dell'environment, con scope limitato ai job che referenziano quell'environment.
- **Environment variables**: variabili non sensibili specifiche dell'environment.

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
          API_KEY: ${{ secrets.STAGING_API_KEY }}
          DB_HOST: ${{ vars.STAGING_DB_HOST }}

  deploy-production:
    needs: [deploy-staging, e2e-tests]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
        env:
          API_KEY: ${{ secrets.PRODUCTION_API_KEY }}
```

Le **deployment protection rules** possono essere estese con custom deployment protection rules tramite GitHub Apps, consentendo l'integrazione con sistemi di approvazione esterni, verifiche di compliance o controlli di performance pre-deployment. Questa funzionalita' permette, ad esempio, di bloccare un deployment fino a quando un servizio di monitoring non conferma che le metriche del deployment precedente sono stabili.

**Deployment concurrency** e' un pattern essenziale per evitare deployment simultanei sullo stesso environment:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    concurrency:
      group: production-deploy
      cancel-in-progress: false    # Non cancellare deployment in corso
    steps:
      - run: ./deploy.sh
```

### 2.7 GitHub Actions Security Hardening

La sicurezza delle pipeline GitHub Actions richiede un approccio stratificato che copra permessi, dipendenze, runner e secrets.

**Permissions Block — Principio del Minimo Privilegio:**

Il `GITHUB_TOKEN` dispone per default di permessi ampi. La best practice e' dichiarare `permissions: {}` a livello di workflow (nessun permesso) e poi espandere solo dove necessario a livello di job:

```yaml
permissions: {}    # Revoca tutti i permessi a livello workflow

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read       # Solo lettura del codice
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  publish:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write      # Scrittura su GitHub Packages
      id-token: write      # OIDC per attestation
    steps:
      - uses: actions/checkout@v4
      - run: npm publish
```

**SHA Pinning — Meccanica e Automazione:**

Il SHA pinning consiste nel referenziare le action tramite il commit SHA completo (40 caratteri) anziche' il tag. Questo previene attacchi di tipo tag-hijacking, dove un attaccante compromette il repository di un'action e modifica il tag per puntare a codice malevolo.

```yaml
# INSICURO: il tag v4 e' mutabile, puo' essere spostato
- uses: actions/checkout@v4

# SICURO: SHA immutabile, non puo' essere modificato
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
```

Per automatizzare l'aggiornamento degli SHA si utilizza **Renovate** o **Dependabot** con configurazione specifica per GitHub Actions:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchManagers": ["github-actions"],
      "pinDigests": true,
      "automerge": true,
      "automergeType": "pr",
      "matchUpdateTypes": ["pin", "digest"]
    }
  ]
}
```

**Protezione contro Script Injection:**

Gli input utente (titoli di PR, messaggi di commit, nomi di branch) non devono mai essere interpolati direttamente nelle espressioni `run:`, poiche' un attaccante potrebbe iniettare comandi shell tramite un titolo di PR malizioso:

```yaml
# VULNERABILE: il titolo della PR viene interpolato nella shell
- run: echo "Processing PR: ${{ github.event.pull_request.title }}"

# SICURO: uso di variabile d'ambiente intermedia
- run: echo "Processing PR: $PR_TITLE"
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
```

**Fork e Pull Request Security:**

I workflow attivati da `pull_request` su fork non hanno accesso ai secrets del repository target. Il trigger `pull_request_target` concede accesso ai secrets ma esegue il codice nel contesto del branch target. Se si necessita di eseguire codice dal fork con accesso ai secrets, il pattern raccomandato e' un workflow a due fasi: la prima fase (senza secrets) esegue build e test dal fork; la seconda fase (con secrets) viene attivata solo dopo approvazione manuale.

---

## 3. GitLab CI

### 3.1 Struttura del File `.gitlab-ci.yml`

GitLab CI utilizza un singolo file `.gitlab-ci.yml` nella root del repository per definire l'intera pipeline. La struttura si compone di **stage**, **job**, **script** e direttive di configurazione globale.

```yaml
default:
  image: node:20-alpine
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .npm/

stages:
  - build
  - test
  - security
  - deploy

variables:
  NPM_CONFIG_CACHE: "$CI_PROJECT_DIR/.npm"

build:
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

unit-test:
  stage: test
  script:
    - npm run test:unit -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      junit: coverage/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-test:
  stage: test
  services:
    - postgres:16
    - redis:7
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: runner
    POSTGRES_PASSWORD: secret
  script:
    - npm run test:integration

sast:
  stage: security
  include:
    - template: Security/SAST.gitlab-ci.yml

deploy-staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - ./deploy.sh staging
  only:
    - main

deploy-production:
  stage: deploy
  environment:
    name: production
    url: https://example.com
  script:
    - ./deploy.sh production
  when: manual
  only:
    - main
```

### 3.2 Stages, Jobs e Regole

Gli **stage** definiscono l'ordine di esecuzione: tutti i job appartenenti allo stesso stage vengono eseguiti in parallelo; lo stage successivo parte solo dopo il completamento di tutti i job dello stage corrente.

I **job** sono l'unita' fondamentale di lavoro. Ogni job specifica uno stage, uno script e opzionalmente regole di esecuzione, artefatti e dipendenze.

Le **rules** offrono un controllo granulare sull'esecuzione condizionale dei job, sostituendo le vecchie keyword `only`/`except`:

```yaml
deploy-production:
  stage: deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"
      when: manual
      allow_failure: false
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
      when: on_success
```

### 3.3 Artifacts e Cache

Gli **artifacts** sono file generati da un job e resi disponibili ai job successivi o scaricabili dall'interfaccia GitLab. Hanno una scadenza configurabile e possono essere tipizzati (report JUnit, coverage Cobertura, SAST).

La **cache** e' pensata per accelerare le build memorizzando dipendenze scaricate (node_modules, .m2, pip cache). A differenza degli artifacts, la cache e' best-effort e puo' non essere disponibile.

```yaml
cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/
  policy: pull-push    # pull = solo lettura, push = solo scrittura, pull-push = entrambi
```

### 3.4 Environments e Auto DevOps

Gli **environments** rappresentano i target di deployment (staging, production, review apps). GitLab traccia la cronologia dei deployment per ciascun environment e permette rollback con un click.

Le **review apps** creano ambienti effimeri per ogni merge request, consentendo la revisione del codice in un ambiente reale:

```yaml
review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop-review
  script:
    - deploy_review_app
  rules:
    - if: $CI_MERGE_REQUEST_IID

stop-review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  script:
    - teardown_review_app
  when: manual
```

**Auto DevOps** e' una funzionalita' di GitLab che fornisce una pipeline CI/CD preconfigurata senza necessita' di scrivere `.gitlab-ci.yml`. Rileva automaticamente il linguaggio del progetto, esegue build, test, security scanning e deployment su Kubernetes. E' ideale per progetti standard ma limitata per configurazioni complesse.

### 3.5 GitLab Runners

I runner GitLab possono essere **shared** (disponibili per tutti i progetti dell'istanza), **group** (condivisi all'interno di un gruppo) o **project-specific**. Supportano diversi executor: Shell, Docker, Kubernetes, VirtualBox, tra gli altri.

Il runner con executor **Docker** e' il piu' diffuso: ogni job viene eseguito in un container isolato, garantendo riproducibilita' e pulizia dell'ambiente. Il runner **Kubernetes** crea un pod per ogni job, ideale per ambienti cloud-native con autoscaling.

### 3.6 Confronto con GitHub Actions

| Aspetto | GitLab CI | GitHub Actions |
|---|---|---|
| Configurazione | `.gitlab-ci.yml` singolo | Multipli file in `.github/workflows/` |
| Marketplace | Limitato, template integrati | Marketplace vastissimo di actions |
| Container Registry | Integrato nativamente | GHCR disponibile ma separato |
| Review Apps | Supporto nativo | Richiede configurazione custom |
| Security Scanning | SAST/DAST integrati (Ultimate) | Tramite actions di terze parti |
| Self-hosting | GitLab self-managed completo | Solo runner self-hosted |
| Costo | Tier gratuito con limiti CI/CD | 2.000 minuti/mese gratuiti |
| Pipeline Visualization | DAG nativo integrato | Visualizzazione base dei job |

GitLab CI eccelle negli ambienti enterprise che necessitano di una piattaforma DevOps completa (SCM + CI/CD + Registry + Monitoring). GitHub Actions e' preferibile per progetti open source e team gia' radicati nell'ecosistema GitHub.

### 3.7 DAG Pipeline con `needs`

Le pipeline GitLab tradizionali seguono un modello sequenziale per stage: tutti i job di uno stage devono completarsi prima che lo stage successivo inizi. Questo modello puo' causare sprechi di tempo quando job indipendenti attendono inutilmente il completamento di job non correlati.

Le **DAG (Directed Acyclic Graph) Pipeline** superano questa limitazione tramite la keyword `needs`, che permette di definire dipendenze dirette tra job, ignorando i confini degli stage:

```yaml
stages:
  - build
  - test
  - deploy

build-frontend:
  stage: build
  script: npm run build:frontend
  artifacts:
    paths: [dist/frontend/]

build-backend:
  stage: build
  script: npm run build:backend
  artifacts:
    paths: [dist/backend/]

test-frontend:
  stage: test
  needs: [build-frontend]        # Parte subito dopo build-frontend,
  script: npm run test:frontend   # non aspetta build-backend

test-backend:
  stage: test
  needs: [build-backend]
  script: npm run test:backend

test-integration:
  stage: test
  needs: [build-frontend, build-backend]    # Aspetta entrambe le build
  script: npm run test:integration

deploy:
  stage: deploy
  needs: [test-frontend, test-backend, test-integration]
  script: ./deploy.sh
```

In questa configurazione, `test-frontend` inizia immediatamente dopo `build-frontend`, senza attendere `build-backend`. Il risparmio di tempo puo' essere significativo in pipeline con molti job indipendenti. Senza `needs`, se `build-backend` impiega 10 minuti, `test-frontend` resterebbe in attesa inutilmente per quei 10 minuti.

La keyword `needs` supporta anche il passaggio selettivo degli artefatti. Per default, un job che dichiara `needs` riceve solo gli artefatti dei job specificati (non di tutti i job precedenti). Questo riduce il tempo di download degli artefatti e il consumo di spazio:

```yaml
test-frontend:
  stage: test
  needs:
    - job: build-frontend
      artifacts: true
    - job: lint
      artifacts: false     # Nessun artefatto da lint, solo dipendenza temporale
```

**Limiti del DAG:** il numero massimo di job dichiarabili in `needs` per un singolo job e' 50. Per pipeline molto grandi, e' necessario strutturare le dipendenze in modo gerarchico o ricorrere a parent-child pipeline.

### 3.8 Parent-Child Pipeline e Dynamic Child Pipeline

Le **Parent-Child Pipeline** permettono di spezzare una pipeline monolitica in sotto-pipeline indipendenti, ciascuna definita in un file YAML separato. Il parent pipeline attiva i child pipeline tramite la keyword `trigger`:

```yaml
# .gitlab-ci.yml (parent)
stages:
  - triggers
  - deploy

trigger-frontend:
  stage: triggers
  trigger:
    include: ci/frontend.yml
    strategy: depend          # Il parent attende il completamento del child

trigger-backend:
  stage: triggers
  trigger:
    include: ci/backend.yml
    strategy: depend

trigger-infra:
  stage: triggers
  trigger:
    include: ci/infrastructure.yml
    strategy: depend

deploy-all:
  stage: deploy
  needs: [trigger-frontend, trigger-backend, trigger-infra]
  script: ./deploy.sh
```

```yaml
# ci/frontend.yml (child)
stages:
  - build
  - test

build:
  stage: build
  image: node:20-alpine
  script:
    - cd frontend && npm ci && npm run build
  artifacts:
    paths: [frontend/dist/]

test:
  stage: test
  image: node:20-alpine
  script:
    - cd frontend && npm run test:unit
```

**Dynamic Child Pipeline** estendono ulteriormente il concetto, consentendo di generare il file di configurazione del child pipeline a runtime. Questo e' particolarmente utile per **monorepo**, dove la pipeline dovrebbe eseguire solo i job relativi ai componenti modificati:

```yaml
# .gitlab-ci.yml (parent)
detect-changes:
  stage: .pre
  script:
    - |
      python3 scripts/generate_pipeline.py \
        --changed-files "$(git diff --name-only HEAD~1)" \
        --output generated-pipeline.yml
  artifacts:
    paths: [generated-pipeline.yml]

trigger-dynamic:
  stage: triggers
  needs: [detect-changes]
  trigger:
    include:
      - artifact: generated-pipeline.yml
        job: detect-changes
    strategy: depend
```

Lo script `generate_pipeline.py` analizza i file modificati e produce un `.gitlab-ci.yml` contenente solo i job necessari. Se sono stati modificati solo file nella directory `frontend/`, il pipeline generato conterra' solo job relativi al frontend, risparmiando tempo e risorse di compute.

**Passaggio di variabili tra parent e child:**

```yaml
trigger-frontend:
  stage: triggers
  variables:
    DEPLOY_ENV: staging
    IMAGE_TAG: $CI_COMMIT_SHA
  trigger:
    include: ci/frontend.yml
```

Le variabili definite nel job `trigger` vengono propagate al child pipeline. Il child pipeline puo' accedere a queste variabili come qualsiasi altra variabile CI/CD.

### 3.9 `include` e Template Composition

La keyword `include` permette di suddividere la configurazione CI/CD in file modulari riutilizzabili, favorendo il principio DRY e la governance centralizzata. GitLab supporta quattro metodi di inclusione:

```yaml
include:
  # 1. Local: file nello stesso repository
  - local: '/ci/templates/docker-build.yml'

  # 2. File: file da un altro progetto GitLab
  - project: 'devops/ci-templates'
    ref: 'v2.5.0'
    file:
      - '/templates/nodejs.yml'
      - '/templates/security-scan.yml'

  # 3. Remote: URL esterna (HTTPS)
  - remote: 'https://raw.githubusercontent.com/org/templates/main/ci/lint.yml'

  # 4. Template: template predefiniti di GitLab
  - template: 'Security/SAST.gitlab-ci.yml'
  - template: 'Security/Dependency-Scanning.gitlab-ci.yml'
```

**Pattern di Template Centralizzati:**

Un team di piattaforma puo' gestire un repository di template CI/CD condivisi. Ogni progetto dell'organizzazione include questi template, garantendo standard uniformi per sicurezza, qualita' e deployment:

```yaml
# Repository devops/ci-templates: templates/nodejs.yml
.nodejs-base:
  image: node:${NODE_VERSION}-alpine
  variables:
    NODE_VERSION: '20'
  before_script:
    - npm ci --prefer-offline --no-audit
  cache:
    key:
      files: [package-lock.json]
    paths: [node_modules/]

.nodejs-test:
  extends: .nodejs-base
  script:
    - npm run lint
    - npm run test:unit -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      junit: coverage/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

.nodejs-build:
  extends: .nodejs-base
  script:
    - npm run build
  artifacts:
    paths: [dist/]
    expire_in: 1 hour
```

```yaml
# Progetto applicativo: .gitlab-ci.yml
include:
  - project: 'devops/ci-templates'
    ref: 'v2.5.0'
    file: '/templates/nodejs.yml'

stages: [build, test, deploy]

build:
  extends: .nodejs-build
  stage: build

test:
  extends: .nodejs-test
  stage: test

deploy:
  stage: deploy
  script: ./deploy.sh
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

**`extends` e override selettivo:** i job che utilizzano `extends` ereditano tutte le proprieta' del template, ma possono sovrascrivere selettivamente singole chiavi. Le chiavi di tipo hash vengono fuse (deep merge); le chiavi di tipo array vengono sostituite. Questo meccanismo permette di definire template robusti con default sensati, lasciando ai progetti la liberta' di personalizzare aspetti specifici senza duplicare l'intera configurazione.

**Compliance Pipeline (GitLab Ultimate):** la funzionalita' Compliance Pipeline forza l'inclusione di un file di configurazione specifico in tutte le pipeline di un gruppo, garantendo che job di sicurezza, audit o quality gate non possano essere rimossi o modificati dai singoli team di sviluppo.

---

## 4. Jenkins

### 4.1 Architettura Master/Agent

Jenkins adotta un'architettura distribuita composta da un **controller** (precedentemente chiamato "master") e uno o piu' **agent** (precedentemente "slave"). Il controller gestisce la configurazione, la schedulazione dei job e l'interfaccia web. Gli agent eseguono effettivamente le build, distribuendo il carico computazionale.

Gli agent possono essere connessi tramite diversi protocolli: SSH, JNLP (Java Network Launch Protocol) o tramite plugin Kubernetes che creano pod effimeri. Questa architettura permette di scalare orizzontalmente aggiungendo agent secondo necessita' e di supportare piattaforme eterogenee (Linux, Windows, macOS) nello stesso cluster Jenkins.

```
                    ┌──────────────┐
                    │  Controller  │
                    │  (Scheduler, │
                    │   UI, Config)│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌───┴────┐ ┌────┴─────┐
        │ Agent      │ │ Agent  │ │ Agent    │
        │ Linux/x64  │ │ Windows│ │ K8s Pod  │
        └────────────┘ └────────┘ └──────────┘
```

### 4.2 Jenkinsfile — Pipeline Dichiarativa

Il **Jenkinsfile** definisce la pipeline come codice (Pipeline as Code) e viene versionato nel repository. La sintassi dichiarativa e' la piu' comune e strutturata:

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                  - name: node
                    image: node:20
                    command: ['sleep', '3600']
                  - name: docker
                    image: docker:24-dind
                    securityContext:
                      privileged: true
            '''
        }
    }

    environment {
        REGISTRY = 'registry.example.com'
        IMAGE_NAME = 'myapp'
    }

    stages {
        stage('Build') {
            steps {
                container('node') {
                    sh 'npm ci'
                    sh 'npm run build'
                }
            }
        }

        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        container('node') {
                            sh 'npm run test:unit'
                        }
                    }
                }
                stage('Lint') {
                    steps {
                        container('node') {
                            sh 'npm run lint'
                        }
                    }
                }
            }
        }

        stage('Build Image') {
            steps {
                container('docker') {
                    sh "docker build -t ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER} ."
                    sh "docker push ${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}"
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh "./deploy.sh staging ${BUILD_NUMBER}"
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            input {
                message 'Deploy to production?'
                ok 'Deploy'
                submitter 'admin,deploy-team'
            }
            steps {
                sh "./deploy.sh production ${BUILD_NUMBER}"
            }
        }
    }

    post {
        always {
            junit '**/test-results/*.xml'
            archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true
        }
        failure {
            slackSend channel: '#builds', message: "Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        success {
            slackSend channel: '#builds', message: "Build SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
```

### 4.3 Shared Libraries

Le **Shared Libraries** permettono di centralizzare logica comune tra pipeline di progetti diversi. Vengono definite in un repository Git separato con una struttura specifica:

```
shared-library/
├── vars/
│   ├── deployApp.groovy        # Step globali richiamabili come funzioni
│   └── notifySlack.groovy
├── src/
│   └── com/example/
│       └── Pipeline.groovy     # Classi Groovy riutilizzabili
└── resources/
    └── templates/              # Template e file di configurazione
```

Utilizzo nel Jenkinsfile:

```groovy
@Library('my-shared-library@main') _

pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                deployApp(environment: 'staging', version: env.BUILD_NUMBER)
            }
        }
    }
    post {
        failure {
            notifySlack(channel: '#alerts', status: 'FAILURE')
        }
    }
}
```

### 4.4 Blue Ocean UI

**Blue Ocean** e' l'interfaccia moderna di Jenkins che offre una visualizzazione intuitiva delle pipeline con rappresentazione grafica degli stage, log colorati e gestione semplificata delle pull request. Sebbene il progetto Blue Ocean sia ora in modalita' di manutenzione (non riceve piu' nuove funzionalita' significative), resta utile per la visualizzazione delle pipeline complesse. L'interfaccia classica di Jenkins rimane comunque il punto di riferimento per la configurazione avanzata.

### 4.5 Quando Utilizzare Jenkins

Jenkins rimane rilevante in scenari specifici:

- **Ambienti enterprise legacy** con investimenti significativi in pipeline Jenkins esistenti.
- **Requisiti di compliance** che impongono il controllo completo sull'infrastruttura CI/CD (on-premise).
- **Pipeline estremamente complesse** che beneficiano della flessibilita' di Groovy e dell'ecosistema di oltre 1.800 plugin.
- **Ambienti eterogenei** dove e' necessario orchestrare build su piattaforme diverse (mainframe, embedded, mobile).

Per nuovi progetti greenfield, GitHub Actions o GitLab CI sono generalmente preferibili per la minore complessita' operativa e il modello SaaS che elimina l'onere di manutenzione.

### 4.6 Scripted vs Declarative Pipeline

Jenkins supporta due sintassi per il Jenkinsfile, ciascuna con vantaggi distinti:

**Declarative Pipeline** (raccomandata per la maggior parte dei casi) offre una struttura rigida e prevedibile con validazione sintattica preventiva. La struttura `pipeline { agent {} stages { stage { steps {} } } }` impone una forma canonica che semplifica la lettura e la manutenzione.

**Scripted Pipeline** offre la piena potenza di Groovy, consentendo logica arbitraria, loop, condizionali complessi e manipolazione dinamica della pipeline. E' necessaria quando la complessita' del flusso supera le capacita' espressive della sintassi dichiarativa.

```groovy
// Scripted Pipeline - esempio con logica dinamica
node('linux') {
    def services = ['auth', 'api', 'worker', 'gateway']
    def parallelStages = [:]

    stage('Checkout') {
        checkout scm
    }

    // Generazione dinamica di stage paralleli
    services.each { svc ->
        parallelStages["test-${svc}"] = {
            stage("Test ${svc}") {
                dir(svc) {
                    sh 'npm ci && npm test'
                }
            }
        }
    }

    stage('Parallel Tests') {
        parallel parallelStages
    }

    stage('Deploy') {
        if (env.BRANCH_NAME == 'main') {
            sh './deploy.sh production'
        } else {
            echo "Skipping deploy for branch ${env.BRANCH_NAME}"
        }
    }
}
```

**Quando usare Scripted Pipeline:** generazione dinamica di stage basata su file di configurazione, integrazione con API esterne per determinare il flusso di esecuzione, pipeline che orchestrano decine di micro-servizi con logica di deployment differenziata. In tutti gli altri casi, preferire la sintassi dichiarativa per leggibilita' e manutenibilita'.

### 4.7 Jenkins Configuration as Code (JCasC)

**JCasC** (Jenkins Configuration as Code) permette di definire l'intera configurazione di Jenkins (system settings, security, credentials, plugin configuration) in un file YAML versionato, eliminando la configurazione manuale tramite interfaccia web.

```yaml
# jenkins.yaml - JCasC
jenkins:
  systemMessage: "Jenkins configurato tramite JCasC"
  numExecutors: 0     # Il controller non esegue build
  securityRealm:
    ldap:
      configurations:
        - server: ldap://ldap.example.com
          rootDN: "dc=example,dc=com"
          userSearchBase: "ou=people"
  authorizationStrategy:
    roleBased:
      roles:
        global:
          - name: "admin"
            permissions:
              - "Overall/Administer"
            entries:
              - group: "jenkins-admins"
          - name: "developer"
            permissions:
              - "Job/Build"
              - "Job/Read"
              - "Job/Workspace"
            entries:
              - group: "developers"
  clouds:
    - kubernetes:
        name: "k8s-cloud"
        serverUrl: "https://kubernetes.default.svc"
        namespace: "jenkins"
        jenkinsUrl: "http://jenkins.jenkins.svc:8080"
        podTemplates:
          - name: "node20"
            label: "node20"
            containers:
              - name: "node"
                image: "node:20-alpine"
                command: "sleep"
                args: "3600"
                resourceRequestCpu: "500m"
                resourceRequestMemory: "512Mi"

credentials:
  system:
    domainCredentials:
      - credentials:
          - string:
              scope: GLOBAL
              id: "slack-webhook"
              secret: "${SLACK_WEBHOOK_URL}"
              description: "Slack Webhook per notifiche"

unclassified:
  slackNotifier:
    teamDomain: "myteam"
    tokenCredentialId: "slack-webhook"
  gitHubConfiguration:
    apiRateLimitChecker: ThrottleForNormalize
```

I benefici di JCasC sono significativi: la configurazione di Jenkins diventa riproducibile (disaster recovery), auditabile (ogni modifica e' un commit Git), e testabile (validazione del YAML prima dell'applicazione). L'adozione di JCasC elimina il rischio di "configuration drift" dove l'istanza di produzione diverge dalla configurazione documentata.

**Seed Job con Job DSL:** complementare a JCasC, il plugin **Job DSL** permette di definire i job Jenkins stessi come codice Groovy. Un seed job legge le definizioni e crea/aggiorna i job automaticamente. Questo approccio, combinato con JCasC, rende l'intera installazione Jenkins completamente definita come codice.

---

## 5. ArgoCD e GitOps

### 5.1 Principi GitOps

**GitOps** e' un paradigma operativo che utilizza Git come unica fonte di verita' (single source of truth) per l'infrastruttura e le configurazioni applicative. I quattro principi fondamentali sono:

1. **Dichiarativo**: l'intero sistema desiderato e' descritto in modo dichiarativo (manifesti YAML, Helm chart, Kustomize).
2. **Versionato e immutabile**: lo stato desiderato e' memorizzato in Git, con cronologia completa delle modifiche.
3. **Automaticamente applicato**: agent software applicano automaticamente lo stato desiderato al cluster.
4. **Continuamente riconciliato**: agent monitorano lo stato effettivo e lo riconciliano con lo stato desiderato, correggendo eventuali drift.

Il flusso GitOps separa nettamente la CI (che produce artefatti) dalla CD (che li distribuisce). La pipeline CI aggiorna il repository GitOps con la nuova versione dell'immagine; ArgoCD rileva la modifica e sincronizza il cluster.

### 5.2 Architettura di ArgoCD

ArgoCD e' un controller Kubernetes che implementa il paradigma GitOps come continuous delivery tool dichiarativo. I componenti principali sono:

- **API Server**: espone l'API gRPC/REST e l'interfaccia web per la gestione delle applicazioni.
- **Repository Server**: clona e gestisce la cache dei repository Git, genera i manifesti Kubernetes a partire da Helm, Kustomize o directory di YAML.
- **Application Controller**: monitora lo stato delle applicazioni e riconcilia lo stato attuale del cluster con lo stato desiderato definito in Git.
- **Redis**: cache per lo stato delle applicazioni e i manifesti generati.
- **Dex / SSO**: integrazione per l'autenticazione tramite OIDC, LDAP, SAML.

```
┌─────────────────────────────────────────────────┐
│                  ArgoCD Server                   │
│  ┌──────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ API      │  │ Repo       │  │ Application │  │
│  │ Server   │  │ Server     │  │ Controller  │  │
│  └────┬─────┘  └─────┬──────┘  └──────┬──────┘  │
│       │              │                │          │
│       │         ┌────┴────┐     ┌─────┴──────┐  │
│       │         │  Git    │     │ Kubernetes │  │
│       │         │  Repos  │     │  Clusters  │  │
│       │         └─────────┘     └────────────┘  │
└─────────────────────────────────────────────────┘
```

### 5.3 Application CRD

L'oggetto fondamentale di ArgoCD e' la Custom Resource **Application**, che definisce la relazione tra un repository Git (source) e un cluster/namespace Kubernetes (destination):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/k8s-manifests.git
    targetRevision: main
    path: apps/myapp/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 5.4 Sync Policies

Le **sync policy** controllano il comportamento di riconciliazione:

- **Automated Sync**: ArgoCD applica automaticamente le modifiche rilevate nel repository Git senza intervento manuale.
- **Self-Heal**: se qualcuno modifica manualmente una risorsa nel cluster (kubectl edit, dashboard), ArgoCD ripristina automaticamente lo stato desiderato da Git.
- **Prune**: rimuove le risorse che non sono piu' presenti nel repository Git.
- **Sync Windows**: finestre temporali in cui la sincronizzazione e' permessa o negata, utili per evitare deployment durante orari critici.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
spec:
  syncWindows:
    - kind: allow
      schedule: '0 8-18 * * 1-5'     # Lun-Ven 08:00-18:00
      duration: 10h
      applications: ['*']
    - kind: deny
      schedule: '0 0 25 12 *'         # Natale
      duration: 24h
      applications: ['*']
```

### 5.5 Pattern App-of-Apps

Il pattern **App-of-Apps** utilizza un'applicazione ArgoCD "root" che gestisce altre applicazioni ArgoCD. Questo approccio consente di gestire decine o centinaia di applicazioni in modo gerarchico e scalabile:

```yaml
# root-app/Chart.yaml - Helm chart che genera Application per ogni servizio
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/org/argocd-apps.git
    path: root
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
```

Il repository `root` contiene i manifesti di tipo Application per ciascun servizio, permettendo di aggiungere o rimuovere applicazioni semplicemente committando un file YAML.

### 5.6 ApplicationSet

**ApplicationSet** e' un controller complementare che genera automaticamente Application ArgoCD a partire da template e generatori. Supporta diversi generatori:

- **Git Generator**: crea un'applicazione per ogni directory o file nel repository.
- **Cluster Generator**: crea un'applicazione per ogni cluster registrato.
- **Matrix Generator**: combina piu' generatori (ad esempio: ogni applicazione su ogni cluster).
- **Pull Request Generator**: crea ambienti temporanei per le pull request.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservices
  namespace: argocd
spec:
  generators:
    - matrix:
        generators:
          - git:
              repoURL: https://github.com/org/k8s-manifests.git
              directories:
                - path: apps/*
          - clusters:
              selector:
                matchLabels:
                  env: production
  template:
    metadata:
      name: '{{path.basename}}-{{name}}'
    spec:
      source:
        repoURL: https://github.com/org/k8s-manifests.git
        path: '{{path}}/overlays/{{metadata.labels.env}}'
      destination:
        server: '{{server}}'
        namespace: '{{path.basename}}'
```

### 5.7 Gestione Multi-Cluster

ArgoCD supporta nativamente la gestione di cluster multipli. Un singolo ArgoCD centrale puo' sincronizzare applicazioni su decine di cluster distribuiti geograficamente. I cluster vengono registrati tramite CLI:

```bash
argocd cluster add my-remote-cluster --name production-eu-west
```

Questo approccio centralizzato semplifica la governance, il monitoraggio e l'applicazione di policy uniformi su tutti i cluster. Per installazioni di grande scala, e' possibile adottare un'architettura "hub and spoke" con un ArgoCD centrale per la configurazione di piattaforma e istanze ArgoCD locali per le applicazioni di ciascun cluster.

### 5.8 Integrazione con Kustomize e Helm

ArgoCD supporta nativamente sia **Kustomize** che **Helm** come strumenti di templating:

Per **Kustomize**, ArgoCD rileva automaticamente la presenza di un `kustomization.yaml` e lo processa. E' possibile sovrascrivere immagini e namespace direttamente nella specifica Application.

Per **Helm**, ArgoCD supporta chart da repository Helm o da directory Git. I valori possono essere specificati inline o tramite file values:

```yaml
spec:
  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: postgresql
    targetRevision: 15.x
    helm:
      releaseName: mydb
      valueFiles:
        - values-production.yaml
      values: |
        primary:
          resources:
            requests:
              memory: 512Mi
              cpu: 250m
```

### 5.9 Flux CD — Deep Dive

**Flux** e' il secondo strumento GitOps di riferimento per Kubernetes, anch'esso progetto CNCF graduated. A differenza di ArgoCD, che offre un'interfaccia web ricca e un modello "hub-and-spoke" centralizzato, Flux adotta un'architettura modulare basata su controller specializzati che operano indipendentemente:

**Controller principali di Flux:**

- **Source Controller**: gestisce le sorgenti Git, Helm repository, OCI registry e S3 bucket. Monitora le sorgenti per nuovi commit o chart version e ne rende disponibile il contenuto agli altri controller.
- **Kustomize Controller**: riconcilia le risorse Kubernetes a partire da Kustomize overlay o directory di YAML plain, applicando patch, sostituzione di immagini e configurazione per environment.
- **Helm Controller**: gestisce le HelmRelease CRD, installando e aggiornando Helm chart con valori specifici per environment. Supporta rollback automatico se l'upgrade fallisce.
- **Notification Controller**: gestisce le notifiche in entrata (webhook da GitHub, GitLab) e in uscita (Slack, Teams, PagerDuty), consentendo trigger event-driven e alerting.
- **Image Reflector + Image Automation Controller**: scansionano i container registry per nuove immagini e aggiornano automaticamente i manifest Git con le nuove versioni, chiudendo il loop CI → GitOps senza intervento manuale.

**Esempio di GitRepository e Kustomization:**

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: app-manifests
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/k8s-manifests.git
  ref:
    branch: main
  secretRef:
    name: git-credentials
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-production
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: app-manifests
  path: ./apps/production
  prune: true
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: api-server
      namespace: production
  timeout: 3m
```

**HelmRelease — Gestione Dichiarativa di Helm Chart:**

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: redis
  namespace: production
spec:
  interval: 10m
  chart:
    spec:
      chart: redis
      version: '18.x'
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
  values:
    architecture: replication
    replica:
      replicaCount: 3
  upgrade:
    remediation:
      retries: 3
      remediateLastFailure: true
  rollback:
    cleanupOnFail: true
```

La keyword `remediation` in Flux e' particolarmente potente: se un upgrade Helm fallisce (il deployment non diventa healthy entro il timeout), Flux ritenta automaticamente l'upgrade o effettua un rollback all'ultima release funzionante, senza intervento manuale.

**Image Automation — Chiusura del Loop CI/CD:**

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: api-server
  namespace: flux-system
spec:
  image: ghcr.io/org/api-server
  interval: 1m
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: api-server
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: api-server
  policy:
    semver:
      range: '>=1.0.0'
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: auto-update
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: app-manifests
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        name: flux-bot
        email: flux@example.com
      messageTemplate: 'chore: update {{.AutomationObject}} images'
    push:
      branch: main
  update:
    path: ./apps
    strategy: Setters
```

Con l'Image Automation, quando la pipeline CI pubblica una nuova immagine `ghcr.io/org/api-server:1.5.2`, Flux rileva la nuova versione, aggiorna il manifest nel repository Git e il Kustomize Controller applica la modifica al cluster. L'intero ciclo e' completamente automatizzato.

**ArgoCD vs Flux — Quando Scegliere:**

| Aspetto | ArgoCD | Flux |
|---|---|---|
| UI Web | Ricca, con visualizzazione grafica | Assente nativamente (terze parti: Weave GitOps UI) |
| Architettura | Monolitica (server unico) | Modulare (controller indipendenti) |
| Multi-tenancy | AppProject con RBAC | Namespace-scoped con Kustomization |
| Image Automation | Tramite Argo CD Image Updater (separato) | Integrata (Image Automation Controller) |
| Helm | Supporto nativo | HelmRelease CRD con rollback automatico |
| Curva di apprendimento | Piu' accessibile | Piu' concetti da padroneggiare |
| Community (post-2024) | Molto attiva, CNCF graduated | Attiva, CNCF graduated (post-chiusura Weaveworks) |

### 5.10 Progressive Delivery con Argo Rollouts e Flagger

La **progressive delivery** estende il deployment tradizionale con controlli graduali sul traffico, metriche di analisi e promozione/rollback automatici. Due strumenti dominano questo spazio:

**Argo Rollouts** (ecosistema ArgoCD):

Argo Rollouts sostituisce il Deployment standard di Kubernetes con una CRD `Rollout` che supporta strategie canary e blue-green con analisi metrica integrata:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: api-server
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: api-server-canary
      stableService: api-server-stable
      trafficRouting:
        istio:
          virtualServices:
            - name: api-server-vsvc
              routes:
                - primary
      steps:
        - setWeight: 5
        - pause: { duration: 2m }
        - analysis:
            templates:
              - templateName: success-rate
            args:
              - name: service-name
                value: api-server-canary
        - setWeight: 20
        - pause: { duration: 5m }
        - analysis:
            templates:
              - templateName: success-rate
        - setWeight: 50
        - pause: { duration: 5m }
        - setWeight: 100
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
        - name: api-server
          image: ghcr.io/org/api-server:1.5.2
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 30s
      count: 5
      successCondition: result[0] >= 0.99
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",code=~"2.."}[2m]))
            /
            sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
```

In questo esempio, il rollout canary procede attraverso step progressivi (5% → 20% → 50% → 100% del traffico). A ogni fase, un `AnalysisTemplate` interroga Prometheus per verificare che il tasso di successo HTTP del canary sia almeno il 99%. Se l'analisi fallisce, Argo Rollouts esegue automaticamente il rollback al revision stabile.

**Flagger** (ecosistema Flux):

Flagger adotta un approccio diverso: non sostituisce il Deployment ma crea e gestisce deployment canary e primary in automatico. Supporta Istio, Linkerd, NGINX Ingress, Contour, Gloo e Gateway API come backend di traffic routing:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: api-server
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  service:
    port: 8080
    targetPort: 8080
  analysis:
    interval: 30s
    threshold: 5          # Numero massimo di analisi fallite
    maxWeight: 50         # Massimo peso canary
    stepWeight: 10        # Incremento per step
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
        interval: 1m
      - name: request-duration
        thresholdRange:
          max: 500         # p99 latency < 500ms
        interval: 1m
    webhooks:
      - name: load-test
        url: http://flagger-loadtester.test/
        metadata:
          cmd: "hey -z 1m -q 10 -c 2 http://api-server-canary.production:8080/"
```

La combinazione di GitOps (ArgoCD/Flux) con progressive delivery (Rollouts/Flagger) rappresenta lo stato dell'arte per deployment sicuri e automatizzati in ambienti Kubernetes di produzione.

---

## 6. Pipeline Patterns

### 6.1 Trunk-Based Deployment

Il **trunk-based development** prevede che tutti gli sviluppatori lavorino direttamente sul branch principale (trunk/main), utilizzando feature branch di brevissima durata (massimo 1-2 giorni). Ogni commit sul trunk attiva la pipeline completa e, se tutti i test passano, il codice puo' essere immediatamente distribuito.

Questo approccio funziona in sinergia con i **feature flag** (trattati nella sezione 6.5): le funzionalita' incomplete vengono integrate nel trunk ma nascoste dietro flag, permettendo integrazione continua senza esporre codice non pronto agli utenti.

### 6.1.1 Implementazione Pratica delle Strategie di Deployment

Le strategie descritte nella sezione 1.3 richiedono implementazioni specifiche a seconda della piattaforma e dell'orchestratore utilizzato.

**Blue-Green con Kubernetes e Service:**

In Kubernetes, il blue-green deployment si implementa con due Deployment separati (blue e green) e un Service che commuta il selettore:

```yaml
# deployment-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-blue
  labels:
    app: myapp
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      version: blue
  template:
    metadata:
      labels:
        app: myapp
        version: blue
    spec:
      containers:
        - name: myapp
          image: ghcr.io/org/myapp:v1.4.0
---
# service.yaml - commuta tra blue e green modificando il selettore
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
    version: blue    # Cambiare a "green" per lo switch
  ports:
    - port: 80
      targetPort: 8080
```

Lo switch avviene aggiornando il label `version` nel selettore del Service. In un contesto GitOps, questo si traduce in una modifica al manifesto nel repository Git. Il rollback e' altrettanto semplice: revertire il selettore alla versione precedente.

**Canary con NGINX Ingress Controller:**

Per team che non utilizzano service mesh (Istio, Linkerd), NGINX Ingress Controller supporta canary deployment tramite annotazioni:

```yaml
# Ingress canary - riceve il 10% del traffico
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-canary
                port:
                  number: 80
```

L'annotazione `canary-weight` controlla la percentuale di traffico instradato al backend canary. Per la promozione progressiva, si incrementa il peso (10 → 25 → 50 → 100) tramite aggiornamenti al manifesto. NGINX Ingress supporta anche il canary basato su header (`canary-by-header`) e cookie (`canary-by-cookie`), utili per testing interno prima dell'esposizione pubblica.

**Rolling Update — Parametri Kubernetes:**

I rolling update in Kubernetes sono controllati dai parametri `maxUnavailable` e `maxSurge` nella strategia del Deployment:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1         # Massimo 1 pod non disponibile durante l'update
      maxSurge: 1               # Massimo 1 pod extra durante l'update
  minReadySeconds: 30           # Il pod deve essere ready per 30s prima di considerarlo stabile
```

Il parametro `minReadySeconds` e' cruciale: ritarda la rimozione del pod precedente fino a quando il nuovo pod non e' rimasto in stato Ready per il tempo specificato, proteggendo da crash immediati dopo l'avvio. Il `progressDeadlineSeconds` (default 600s) definisce il timeout dopo il quale l'update viene considerato fallito se non completato.

**Feature Flag — Integrazione nella Pipeline:**

La pipeline puo' automatizzare l'attivazione dei feature flag come step post-deployment:

```yaml
# Step post-deployment: attiva il feature flag per il 5% degli utenti
- name: Enable canary feature flag
  run: |
    curl -X PATCH "https://app.launchdarkly.com/api/v2/flags/production/new-checkout" \
      -H "Authorization: ${{ secrets.LD_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '[{
        "op": "replace",
        "path": "/environments/production/rules/0/rollout/variations/0/weight",
        "value": 5000
      }]'
```

Questo pattern consente di separare completamente il deployment del codice (che diventa un evento a basso rischio) dall'attivazione delle funzionalita' (che avviene gradualmente tramite feature flag). Il codice e' gia' in produzione ma la funzionalita' e' visibile solo alla percentuale configurata di utenti.

### 6.2 Environment Promotion: Dev → Staging → Prod

Il pattern di **environment promotion** prevede che gli artefatti vengano promossi attraverso ambienti progressivamente piu' simili alla produzione:

```
Dev (automatico) → Staging (automatico + test E2E) → Production (manuale/automatico)
```

Principio fondamentale: **l'artefatto e' lo stesso in tutti gli ambienti**. Cio' che cambia e' la configurazione (variabili d'ambiente, secrets, scaling). Non si ricompila mai il codice per un ambiente diverso.

```yaml
# GitLab CI - Promotion pattern
deploy-dev:
  stage: deploy
  environment: development
  script:
    - helm upgrade --install myapp ./chart -f values-dev.yaml --set image.tag=$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-staging:
  stage: deploy
  environment: staging
  needs: [deploy-dev, e2e-tests-dev]
  script:
    - helm upgrade --install myapp ./chart -f values-staging.yaml --set image.tag=$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-production:
  stage: deploy
  environment: production
  needs: [deploy-staging, e2e-tests-staging]
  script:
    - helm upgrade --install myapp ./chart -f values-prod.yaml --set image.tag=$CI_COMMIT_SHA
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### 6.3 Approval Gates

Gli **approval gate** introducono punti di controllo manuali nella pipeline, richiedendo l'approvazione esplicita prima di procedere. Sono essenziali per il deployment in produzione in contesti enterprise.

In GitHub Actions, gli approval gate si configurano tramite gli **environments** con reviewer designati nel pannello Settings del repository. In GitLab CI, si usa `when: manual` con `allow_failure: false`. In Jenkins, la direttiva `input` blocca la pipeline in attesa di approvazione.

### 6.4 Strategie di Rollback

Un rollback efficace richiede pianificazione preventiva:

- **Rollback basato su artefatti**: ridistribuire la versione precedente dell'artefatto (image tag precedente, chart version precedente).
- **Rollback GitOps**: revertire il commit nel repository GitOps (`git revert`), lasciando che ArgoCD applichi lo stato precedente.
- **Rollback automatico**: configurare health check post-deployment che attivano automaticamente il rollback se le metriche superano soglie critiche (error rate > 1%, latency p99 > 500ms).

```bash
# Rollback Helm
helm rollback myapp 42    # Rollback alla revision 42

# Rollback Kubernetes
kubectl rollout undo deployment/myapp

# Rollback ArgoCD (GitOps - revert del commit)
git revert HEAD && git push
```

### 6.5 Feature Flags con LaunchDarkly e Unleash

I **feature flag** (detti anche feature toggle) disaccoppiano il rilascio del codice dall'attivazione delle funzionalita'. Due piattaforme principali:

**LaunchDarkly** (SaaS commerciale): offre targeting avanzato per utente, segmento, percentuale. Supporta multivariate flag, A/B testing, ed e' ottimizzato per ambienti enterprise con audit trail completo e governance centralizzata.

**Unleash** (open source): fornisce funzionalita' simili con la possibilita' di self-hosting. Supporta strategie di attivazione graduali, per IP, per utente e personalizzate. La versione open source copre la maggior parte dei casi d'uso.

L'integrazione nella pipeline avviene in due modi: la pipeline attiva/disattiva i flag come step di deployment, oppure i flag vengono gestiti indipendentemente dalla pipeline tramite l'interfaccia della piattaforma.

### 6.6 Database Migrations nella Pipeline

Le migrazioni dello schema del database rappresentano uno degli aspetti piu' delicati del deployment automatizzato. Regole fondamentali:

- **Le migrazioni devono essere backward-compatible**: la nuova migrazione deve funzionare con la versione corrente E precedente dell'applicazione (expand-contract pattern).
- **Separare il deployment della migrazione dal deployment dell'applicazione**: eseguire la migrazione come step separato prima del deployment applicativo.
- **Non eseguire mai migrazioni distruttive in automatico**: rinominare colonne, eliminare tabelle o modificare tipi di dato richiedono approcci multi-fase.

```yaml
# Step di migrazione nella pipeline
migrate-database:
  stage: pre-deploy
  script:
    - flyway -url=$DB_URL -user=$DB_USER -password=$DB_PASS migrate
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      changes:
        - db/migrations/**
```

L'**expand-contract pattern** prevede tre fasi: (1) expand - aggiungere la nuova colonna senza rimuovere la vecchia, (2) migrate - aggiornare l'applicazione per usare la nuova colonna, (3) contract - rimuovere la vecchia colonna in un deployment successivo.

---

## 7. Testing in Pipeline

### 7.1 Livelli di Test

La piramide dei test nella pipeline prevede tre livelli principali, ciascuno con caratteristiche diverse in termini di velocita', copertura e costo:

**Unit Test**: veloci (millisecondi ciascuno), isolati, numerosissimi. Verificano la logica di singole funzioni o classi. Devono essere eseguiti per primi nella pipeline per fornire feedback rapido.

**Integration Test**: verificano l'interazione tra componenti (servizio + database, servizio + API esterna). Richiedono dipendenze esterne (database, cache, message broker) tipicamente fornite tramite container.

**End-to-End (E2E) Test**: simulano il comportamento dell'utente finale attraverso l'intero stack applicativo. Sono i piu' lenti e fragili ma verificano il corretto funzionamento del sistema nel suo complesso. Strumenti comuni: Cypress, Playwright, Selenium.

### 7.2 Test Paralleli

La parallelizzazione dei test riduce drasticamente i tempi della pipeline:

```yaml
# GitLab CI - Test paralleli con partizionamento
test:
  stage: test
  parallel: 4
  script:
    - TOTAL=$CI_NODE_TOTAL INDEX=$CI_NODE_INDEX npm run test:partitioned
```

In GitHub Actions, la matrix strategy permette di distribuire i test su piu' runner. Strumenti come **Jest** (--shard), **pytest** (pytest-split) e **RSpec** (parallel_tests) supportano nativamente il partizionamento.

### 7.3 Testcontainers

**Testcontainers** e' una libreria che permette di avviare container Docker come dipendenze per i test direttamente dal codice di test. Garantisce ambienti di test riproducibili e isolati senza dipendere da servizi condivisi:

```java
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
    .withDatabaseName("testdb")
    .withUsername("test")
    .withPassword("test");

@Container
static GenericContainer<?> redis = new GenericContainer<>("redis:7")
    .withExposedPorts(6379);
```

Nelle pipeline CI/CD, Testcontainers richiede l'accesso al Docker daemon. Questo si ottiene con Docker-in-Docker (DinD) o montando il Docker socket dell'host.

### 7.4 Code Coverage Thresholds

Definire soglie minime di copertura del codice impedisce la regressione della qualita' dei test:

```yaml
# GitHub Actions - Enforce coverage threshold
- name: Run tests with coverage
  run: npm test -- --coverage --coverageThreshold='{"global":{"branches":80,"functions":85,"lines":85,"statements":85}}'
```

Attenzione: una copertura elevata non garantisce test di qualita'. E' preferibile una copertura dell'80% con test significativi rispetto al 95% con test superficiali. Le metriche di coverage vanno usate come guardrail per prevenire la regressione, non come obiettivo fine a se stesso.

### 7.5 Contract Testing nella Pipeline

I **contract test** verificano che le interfacce tra servizi (API HTTP, messaggi asincroni, eventi) rispettino i contratti concordati, prevenendo rotture di compatibilita' quando un servizio viene aggiornato indipendentemente.

**Pact** e' il framework piu' diffuso per il consumer-driven contract testing. Il flusso nella pipeline e':

1. Il servizio consumer genera un "pact" (contratto) durante i suoi test, descrivendo le richieste che effettua e le risposte attese.
2. Il pact viene pubblicato su un **Pact Broker** (centralizzato).
3. Il servizio provider esegue i test di verifica del pact nella propria pipeline, confermando che soddisfa i contratti dei consumer.

```yaml
# Pipeline del consumer - pubblica il contract
contract-test-consumer:
  stage: test
  script:
    - npm run test:contract
    - npx pact-broker publish ./pacts \
        --consumer-app-version=$CI_COMMIT_SHA \
        --broker-base-url=$PACT_BROKER_URL \
        --broker-token=$PACT_BROKER_TOKEN

# Pipeline del provider - verifica il contract
contract-test-provider:
  stage: test
  script:
    - npm run test:contract:provider -- \
        --pact-broker-url=$PACT_BROKER_URL \
        --provider-version=$CI_COMMIT_SHA
```

Il **can-i-deploy** check di Pact consente di verificare nella pipeline se un servizio puo' essere distribuito senza rompere i contratti con gli altri servizi:

```yaml
can-i-deploy:
  stage: pre-deploy
  script:
    - npx pact-broker can-i-deploy \
        --pacticipant=api-service \
        --version=$CI_COMMIT_SHA \
        --to-environment=production
```

Questo step blocca il deployment se il provider non ha verificato con successo i contratti dell'ultima versione dei consumer, prevenendo deployment che causerebbero errori di integrazione in produzione.

### 7.6 SAST e DAST Scanning

**SAST (Static Application Security Testing)** analizza il codice sorgente senza eseguirlo, identificando vulnerabilita' come SQL injection, XSS, path traversal e utilizzo di dipendenze vulnerabili. Strumenti: SonarQube, Semgrep, CodeQL (integrato in GitHub), GitLab SAST.

**DAST (Dynamic Application Security Testing)** testa l'applicazione in esecuzione simulando attacchi dall'esterno. Identifica vulnerabilita' che emergono solo a runtime. Strumenti: OWASP ZAP, Burp Suite, GitLab DAST.

```yaml
# GitHub Actions - CodeQL Analysis
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: javascript, python

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

L'integrazione di SAST nella pipeline CI (su ogni pull request) e' considerata una pratica essenziale. DAST viene tipicamente eseguito sull'ambiente di staging dopo il deployment.

---

## 8. Artifact Management

### 8.1 Container Registry

I container registry ospitano le immagini Docker/OCI prodotte dalla pipeline. Le opzioni principali sono:

- **GHCR (GitHub Container Registry)**: integrato con GitHub, supporta visibilita' pubblica/privata e autenticazione tramite `GITHUB_TOKEN`. Ideale per progetti su GitHub.
- **ECR (Amazon Elastic Container Registry)**: registry AWS con integrazione nativa in ECS/EKS, scanning delle vulnerabilita' integrato, lifecycle policy per la pulizia automatica delle immagini obsolete.
- **ACR (Azure Container Registry)**: equivalente Azure con supporto a Helm chart OCI, geo-replication e integrazione con AKS.
- **Harbor**: registry open source self-hosted con scanning, firma delle immagini (Notary/cosign), replica tra istanze e RBAC avanzato.

Best practice per il tagging delle immagini:

```bash
# Tag immutabile basato su commit SHA (raccomandato)
docker tag myapp:latest registry.example.com/myapp:abc123f

# Tag semantico per i rilasci
docker tag myapp:latest registry.example.com/myapp:v2.3.1

# EVITARE: il tag 'latest' in produzione - e' mutabile e non tracciabile
```

### 8.2 Helm Chart Repository

I chart Helm possono essere ospitati in repository dedicati:

- **ChartMuseum**: server open source per chart Helm con API REST, supporto a storage multipli (S3, GCS, Azure Blob, filesystem locale).
- **OCI Registry**: Helm 3 supporta chart archiviati in registry OCI-compatibili (GHCR, ECR, ACR, Harbor), eliminando la necessita' di un server chart dedicato.
- **GitHub Pages / GitLab Pages**: hosting statico per chart repository Helm con l'utility `helm-push`.

```bash
# Push di un chart su un OCI registry
helm package ./my-chart
helm push my-chart-1.0.0.tgz oci://ghcr.io/org/charts
```

### 8.3 Registry Privati per Pacchetti

**npm (GitHub Packages / Artifactory)**: per pacchetti Node.js privati, si configura il registry nel file `.npmrc`:

```ini
@myorg:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}
```

**PyPI (Artifactory / AWS CodeArtifact)**: per pacchetti Python privati, si configura l'indice nel `pip.conf` o tramite variabile d'ambiente `PIP_INDEX_URL`.

**Artifactory** di JFrog e' la soluzione enterprise piu' completa, supportando contemporaneamente npm, PyPI, Maven, NuGet, Docker, Helm e oltre 30 formati di pacchetto in un'unica piattaforma.

### 8.4 Versionamento degli Artefatti

Adottare una strategia di versionamento coerente e' fondamentale per la tracciabilita':

- **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH` per i rilasci ufficiali.
- **Commit SHA**: per le build intermedie e gli artefatti di staging.
- **Build Number**: progressivo incrementale utile per ordinamento cronologico.
- **Git Tag**: collegare i rilasci ai tag Git per tracciabilita' completa dal codice sorgente all'artefatto.

La combinazione raccomandata e' SemVer per i rilasci e commit SHA per le build di sviluppo, con metadata che collegano l'artefatto al commit, alla pipeline e all'autore della modifica.

---

## 9. Notification e Monitoring

### 9.1 Integrazione Slack e Microsoft Teams

Le notifiche di pipeline sono essenziali per la visibilita' del team sullo stato del deployment:

```yaml
# GitHub Actions - Notifica Slack
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v2
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
    webhook-type: incoming-webhook
    payload: |
      {
        "text": "Deployment ${{ job.status }}: ${{ github.repository }}@${{ github.sha }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*${{ github.workflow }}* #${{ github.run_number }}\nStatus: `${{ job.status }}`\nBranch: `${{ github.ref_name }}`"
            }
          }
        ]
      }
```

Per Microsoft Teams, si utilizzano webhook connector o l'action dedicata `jdcargile/ms-teams-notification`. Le notifiche devono essere calibrate per evitare l'alert fatigue: notificare solo i fallimenti e i deployment in produzione, non ogni build riuscita.

### 9.2 Deployment Tracking

Il tracciamento dei deployment permette di correlare modifiche al codice con cambiamenti nel comportamento del sistema. Strumenti e pratiche chiave:

- **GitHub Deployments API**: registra ogni deployment con stato (pending, success, failure, inactive) e URL dell'ambiente.
- **GitLab Environments**: dashboard integrata con cronologia deployment, link all'ambiente e rollback con un click.
- **Deployment markers** negli strumenti di monitoring (Datadog, Grafana, New Relic): annotazioni temporali che evidenziano quando un deployment e' avvenuto, facilitando la correlazione con variazioni nelle metriche.

### 9.3 DORA Metrics

Le **DORA Metrics** (DevOps Research and Assessment) sono quattro metriche chiave per misurare le prestazioni del processo di software delivery:

1. **Deployment Frequency**: quanto spesso il team rilascia in produzione. Team ad alte prestazioni rilasciano on-demand, piu' volte al giorno.
2. **Lead Time for Changes**: tempo dal commit alla produzione. I team eccellenti raggiungono meno di un'ora.
3. **Change Failure Rate**: percentuale di deployment che causano un'interruzione o richiedono rollback. L'obiettivo e' sotto il 15%.
4. **Time to Restore Service (MTTR)**: tempo per ripristinare il servizio dopo un'interruzione. I team migliori si attestano sotto l'ora.

GitLab offre una dashboard DORA integrata (tier Ultimate). Per GitHub Actions, strumenti come **Sleuth**, **LinearB** o **Faros** calcolano le DORA metrics a partire dai dati delle pipeline. In Jenkins, il plugin **DevOps Portal** fornisce visibilita' su queste metriche.

### 9.4 Pipeline Analytics

L'analisi delle prestazioni della pipeline stessa e' fondamentale per l'ottimizzazione continua:

- **Durata media della pipeline**: identificare bottleneck e stage lenti.
- **Tasso di successo/fallimento**: monitorare la stabilita' della pipeline nel tempo.
- **Tempo di attesa in coda**: per i self-hosted runner, identificare la necessita' di scaling.
- **Costo per build**: per runner cloud, monitorare la spesa e ottimizzare (caching, parallelismo, scelta dell'istanza).

GitLab fornisce analytics integrati nella sezione CI/CD del progetto. Per GitHub Actions, strumenti come **Actionlint** verificano la correttezza dei workflow, mentre **GitHub Actions Metrics** (azioni della community) raccolgono statistiche sulle esecuzioni.

---

## 10. Best Practices

1. **Pipeline as Code**: definire sempre la pipeline nel repository (Jenkinsfile, `.github/workflows/`, `.gitlab-ci.yml`). La pipeline deve essere versionata, sottoposta a review e testata come qualsiasi altro codice. Non configurare mai pipeline tramite interfaccia web se esiste l'alternativa dichiarativa.

2. **Build veloci con feedback rapido**: una pipeline CI dovrebbe completarsi in meno di 10 minuti. Ottimizzare tramite caching aggressivo delle dipendenze, parallelizzazione dei test, esecuzione incrementale (solo i test impattati dalle modifiche) e scelta di immagini base leggere. Ogni minuto risparmiato si moltiplica per il numero di sviluppatori e commit giornalieri.

3. **Artefatti immutabili e promossi**: costruire l'artefatto una sola volta e promuoverlo attraverso gli ambienti senza ricostruirlo. L'immagine container distribuita in produzione deve essere identica (stesso digest SHA256) a quella testata in staging. La configurazione specifica dell'ambiente deve essere iniettata esternamente (variabili d'ambiente, ConfigMap, secrets).

4. **Secrets mai nel codice**: utilizzare secret management nativo della piattaforma CI/CD (GitHub Encrypted Secrets, GitLab CI/CD Variables con masking, Jenkins Credentials) o vault esterni (HashiCorp Vault, AWS Secrets Manager). Preferire OIDC per l'autenticazione verso cloud provider, eliminando credenziali long-lived. Eseguire scansioni automatiche per secrets accidentalmente committati (git-secrets, truffleHog, gitleaks).

5. **Idempotenza e riproducibilita'**: ogni esecuzione della pipeline con lo stesso input deve produrre lo stesso risultato. Fissare le versioni delle dipendenze (lockfile), delle immagini base (digest SHA invece di tag mutabili) e degli strumenti utilizzati nella pipeline. Evitare comandi che dipendono dallo stato di esecuzioni precedenti.

6. **Strategia di branching allineata alla pipeline**: il modello di branching deve supportare la strategia di deployment. Il trunk-based development con feature flag e' la combinazione piu' efficace per il continuous deployment. GitFlow e' appropriato per progetti con rilasci pianificati e manutenzione di versioni multiple.

7. **Rollback testato e automatizzato**: il meccanismo di rollback deve essere testato regolarmente, non solo in emergenza. Includere nella pipeline step di verifica post-deployment (smoke test, synthetic monitoring) che attivano automaticamente il rollback se le metriche degradano oltre soglie predefinite. In un contesto GitOps, il rollback e' un semplice `git revert`.

8. **Security shift-left**: integrare i controlli di sicurezza nelle fasi piu' precoci della pipeline. SAST su ogni pull request, dependency scanning automatico (Dependabot, Renovate), container image scanning prima del push al registry. Bloccare la pipeline se vengono rilevate vulnerabilita' critiche, con possibilita' di override documentato per falsi positivi.

9. **Monitorare la pipeline stessa**: trattare la pipeline CI/CD come un sistema di produzione. Monitorare durata, tasso di successo, costo e tempo di attesa in coda. Definire SLO per la pipeline (ad esempio: il 95% delle build CI deve completarsi in meno di 10 minuti). Analizzare le DORA metrics mensilmente per identificare trend e aree di miglioramento.

10. **Documentazione e onboarding**: mantenere documentazione aggiornata sulla struttura della pipeline, le convenzioni di naming, le procedure di rollback e i contatti per il supporto. Un nuovo membro del team deve poter comprendere e contribuire alla pipeline entro il primo giorno. Includere commenti esplicativi nei file di pipeline per le sezioni non ovvie e mantenere un runbook per la risoluzione dei problemi comuni.

---

## 11. CI/CD Security e Supply Chain

### 11.1 SLSA Framework (Supply-chain Levels for Software Artifacts)

**SLSA** (pronunciato "salsa") e' un framework di sicurezza sviluppato originariamente da Google e ora gestito dalla OpenSSF (Open Source Security Foundation). Definisce livelli incrementali di garanzia sulla provenienza e integrita' degli artefatti software, rispondendo alla domanda: "come posso fidarmi che questo artefatto sia stato costruito dal codice sorgente che dichiara, senza manomissioni?"

**I quattro livelli SLSA:**

| Livello | Requisiti | Garanzia |
|---|---|---|
| SLSA 1 | Processo di build documentato; provenance generata automaticamente | L'artefatto ha una "ricetta" di build tracciabile |
| SLSA 2 | Build ospitata su piattaforma fidata; provenance firmata crittograficamente | La provenance non puo' essere falsificata dall'autore del build |
| SLSA 3 | Build isolata (ephemeral, non modificabile dall'utente); source verificata | Protegge da compromissione dell'infrastruttura di build |
| SLSA 4 | Build ermetica; dipendenze completamente dichiarate e verificate | Massima garanzia di integrita' end-to-end |

La **provenance** e' il documento che descrive come un artefatto e' stato costruito: quale sorgente, quale build system, quali parametri, quali dipendenze. In formato SLSA, la provenance segue lo schema in-toto attestation.

**Implementazione in GitHub Actions:**

GitHub ha introdotto il supporto nativo per l'artifact attestation, raggiungendo SLSA Level 3 grazie alla natura ephemeral e non modificabile dei runner GitHub-hosted:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      attestations: write
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Build container image
        run: |
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .

      - name: Push to GHCR
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: sha256:${{ steps.push.outputs.digest }}
          push-to-registry: true
```

**Verifica della provenance:**

```bash
# Verifica che l'immagine abbia attestation valida
gh attestation verify oci://ghcr.io/org/myapp:abc123f \
  --owner org \
  --format json
```

### 11.2 Sigstore, Cosign e Rekor

**Sigstore** e' un progetto open source (CNCF) che fornisce strumenti per la firma e verifica crittografica degli artefatti software. I tre componenti principali sono:

- **Cosign**: strumento CLI per firmare e verificare container image e artefatti OCI. Supporta la modalita' "keyless" dove non e' necessario gestire chiavi private — l'identita' viene verificata tramite OIDC (GitHub, Google, Microsoft).
- **Fulcio**: Certificate Authority (CA) che emette certificati X.509 di breve durata basati sull'identita' OIDC del firmatario. Il certificato scade in pochi minuti, eliminando il problema della gestione e rotazione delle chiavi.
- **Rekor**: transparency log immutabile e pubblico dove vengono registrate tutte le firme. Consente di verificare retroattivamente che una firma esisteva in un determinato momento, anche dopo la scadenza del certificato.

**Firma keyless con Cosign in GitHub Actions:**

```yaml
jobs:
  sign:
    runs-on: ubuntu-latest
    permissions:
      id-token: write      # Per OIDC
      packages: write
    steps:
      - name: Install cosign
        uses: sigstore/cosign-installer@v3

      - name: Login to GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Sign container image (keyless)
        run: |
          cosign sign --yes \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
        env:
          COSIGN_EXPERIMENTAL: "true"

      - name: Verify signature
        run: |
          cosign verify \
            --certificate-identity-regexp="https://github.com/${{ github.repository }}/" \
            --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

In modalita' keyless, Cosign ottiene un token OIDC da GitHub Actions, lo scambia con Fulcio per un certificato X.509 effimero, firma l'artefatto e registra la firma in Rekor. La verifica successiva controlla la catena di fiducia: certificato emesso da Fulcio, firma presente in Rekor, identita' OIDC corrispondente al repository atteso.

### 11.3 SBOM (Software Bill of Materials)

Un **SBOM** e' un inventario completo dei componenti software inclusi in un artefatto: librerie, framework, versioni e licenze. Due formati standard dominano:

- **SPDX** (Software Package Data Exchange): standard ISO/IEC 5962:2021, ampiamente adottato e supportato dalla Linux Foundation.
- **CycloneDX**: standard OWASP orientato alla sicurezza, con supporto nativo per vulnerabilita' e analisi delle dipendenze.

**Generazione SBOM nella pipeline:**

```yaml
- name: Generate SBOM with Syft
  uses: anchore/sbom-action@v0
  with:
    image: ghcr.io/${{ github.repository }}:${{ github.sha }}
    format: spdx-json
    output-file: sbom.spdx.json

- name: Attach SBOM to image
  run: |
    cosign attach sbom \
      --sbom sbom.spdx.json \
      ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

La generazione e l'allegazione di un SBOM a ogni artefatto pubblicato sta diventando un requisito normativo in molte giurisdizioni. L'Executive Order 14028 del governo USA (2021) richiede SBOM per tutto il software venduto ad agenzie federali. Il Cyber Resilience Act dell'UE (in vigore dal 2024) introduce requisiti simili per il mercato europeo.

### 11.4 Signed Commits e Branch Protection

I **signed commit** utilizzano GPG, SSH o S/MIME per firmare crittograficamente i commit Git, provando che il commit e' stato effettivamente creato dall'autore dichiarato e non e' stato modificato in transito.

**Configurazione per la pipeline:**

```yaml
# Richiedere signed commit come condizione di merge
# GitHub: Settings → Branches → Branch protection rules
# - Require signed commits: enabled
# - Require linear history: enabled
# - Require status checks to pass: enabled

# Verifica nella pipeline CI
- name: Verify commit signature
  run: |
    git log --show-signature -1
    SIGNATURE_STATUS=$(git log --format='%G?' -1)
    if [ "$SIGNATURE_STATUS" != "G" ] && [ "$SIGNATURE_STATUS" != "U" ]; then
      echo "ERROR: Commit non firmato o firma non valida"
      exit 1
    fi
```

La combinazione di signed commits, branch protection rules, CODEOWNERS e required reviews crea una catena di fiducia dal commit iniziale al deployment finale, rendendo ogni passaggio verificabile e auditabile.

---

## 12. CI/CD per Container

### 12.1 Build Sicuro con Kaniko e BuildKit

Il build di container image nella pipeline presenta sfide di sicurezza: l'approccio tradizionale Docker-in-Docker (DinD) richiede il flag `--privileged`, concedendo al container di build accesso root all'host. Alternative piu' sicure:

**Kaniko** esegue il build di immagini container in userspace, senza Docker daemon e senza privilegi elevati. E' la scelta raccomandata per pipeline su Kubernetes:

```yaml
# GitLab CI con Kaniko
build-image:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.23.0-debug
    entrypoint: [""]
  script:
    - |
      /kaniko/executor \
        --context "${CI_PROJECT_DIR}" \
        --dockerfile "${CI_PROJECT_DIR}/Dockerfile" \
        --destination "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHA}" \
        --cache=true \
        --cache-repo="${CI_REGISTRY_IMAGE}/cache" \
        --snapshot-mode=redo \
        --use-new-run
```

**BuildKit** e' il backend di build di nuova generazione incluso in Docker (abilitato con `DOCKER_BUILDKIT=1`). Offre build paralleli, caching avanzato e output multi-piattaforma. Per le pipeline, l'utilizzo tramite `buildx` e' raccomandato:

```yaml
# GitHub Actions con BuildKit/buildx
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
    provenance: true
    sbom: true
```

L'opzione `cache-from: type=gha` utilizza la GitHub Actions cache come layer cache per BuildKit, accelerando significativamente le build successive. L'opzione `provenance: true` genera automaticamente attestation SLSA.

### 12.2 Vulnerability Scanning con Trivy e Grype

Il vulnerability scanning delle immagini container deve avvenire prima del push al registry di produzione. Due scanner open source dominano il mercato:

**Trivy** (Aqua Security): scanner completo che analizza container image, filesystem, repository Git, cluster Kubernetes e configurazioni IaC. Supporta la generazione di SBOM e la verifica di policy personalizzate:

```yaml
# GitHub Actions - Trivy scan
- name: Scan image for vulnerabilities
  uses: aquasecurity/trivy-action@0.28.0
  with:
    image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'          # Fallisce se trova CRITICAL o HIGH

- name: Upload Trivy scan results
  uses: github/codeql-action/upload-sarif@v3
  if: always()
  with:
    sarif_file: 'trivy-results.sarif'
```

**Grype** (Anchore): scanner focalizzato esclusivamente sulla vulnerabilita' delle dipendenze, con database aggiornato frequentemente e basso tasso di falsi positivi. Spesso usato in combinazione con **Syft** per la generazione di SBOM.

**Pipeline completa Build-Scan-Sign-Push:**

```yaml
# Pipeline container sicura end-to-end
jobs:
  container:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        uses: docker/build-push-action@v6
        id: build
        with:
          context: .
          push: false
          load: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Scan for vulnerabilities (Trivy)
        uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          exit-code: '1'
          severity: 'CRITICAL'

      - name: Push to registry
        run: docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Sign image (cosign keyless)
        uses: sigstore/cosign-installer@v3
      - run: cosign sign --yes ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}

      - name: Generate and attach SBOM
        uses: anchore/sbom-action@v0
        with:
          image: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### 12.3 Admission Controller e Policy Enforcement

Gli **Admission Controller** in Kubernetes verificano le policy di sicurezza prima che un pod venga creato. In un contesto CI/CD, garantiscono che solo immagini firmate e scansionate possano essere distribuite:

**Kyverno** e' un policy engine Kubernetes-native che definisce policy come risorse Kubernetes:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: check-cosign-signature
      match:
        any:
          - resources:
              kinds: ["Pod"]
      verifyImages:
        - imageReferences:
            - "ghcr.io/org/*"
          attestors:
            - entries:
                - keyless:
                    issuer: "https://token.actions.githubusercontent.com"
                    subject: "https://github.com/org/*"
                    rekor:
                      url: "https://rekor.sigstore.dev"
```

Questa policy rifiuta qualsiasi pod che utilizzi immagini `ghcr.io/org/*` senza firma cosign valida proveniente da GitHub Actions. La combinazione pipeline CI (build → scan → sign → push) + admission controller (verify) crea una catena di fiducia completa dal codice al cluster.

---

## 13. Secret Management nelle Pipeline

### 13.1 Piattaforme CI/CD Native

Ogni piattaforma CI/CD offre un meccanismo nativo per la gestione dei secrets:

**GitHub Actions Encrypted Secrets**: secrets criptati a riposo con libsodium sealed box. Disponibili a livello di repository, environment o organizzazione. Non appaiono nei log (masking automatico). Limite: non supportano rotazione automatica ne' audit granulare sull'accesso.

**GitLab CI/CD Variables**: variabili marcate come "masked" e/o "protected". Le variabili "protected" sono disponibili solo su branch/tag protetti. Le variabili "masked" vengono offuscate nei log. Supportano scope per environment.

**Jenkins Credentials**: plugin nativo con storage criptato. Supporta tipi diversi (username/password, SSH key, secret text, secret file, certificate). Le credenziali sono referenziate per ID e iniettate tramite il binding `withCredentials`.

**Limiti comuni dei secret nativi:**

- Nessuna rotazione automatica (manuale o tramite script)
- Audit limitato (chi ha letto quale secret, quando)
- Nessun supporto per secret dinamici (credenziali generate on-demand con scadenza)
- Duplicazione dei secret tra pipeline e ambienti

### 13.2 HashiCorp Vault Integration

**HashiCorp Vault** risolve i limiti dei secret nativi offrendo secret dinamici, rotazione automatica, audit trail completo e accesso basato su policy. L'integrazione con le pipeline CI/CD avviene tramite diversi pattern:

**Pattern 1 — OIDC Authentication (raccomandato):**

La pipeline si autentica a Vault tramite il token OIDC della piattaforma CI/CD, senza alcun secret pre-condiviso:

```yaml
# GitHub Actions + Vault OIDC
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Import secrets from Vault
        uses: hashicorp/vault-action@v3
        with:
          url: https://vault.example.com
          method: jwt
          role: github-actions-deploy
          jwtGithubAudience: https://vault.example.com
          secrets: |
            secret/data/production/db password | DB_PASSWORD ;
            secret/data/production/api key | API_KEY

      - name: Deploy
        run: ./deploy.sh
        env:
          DB_PASSWORD: ${{ steps.vault.outputs.DB_PASSWORD }}
          API_KEY: ${{ steps.vault.outputs.API_KEY }}
```

**Pattern 2 — Dynamic Secrets:**

Vault genera credenziali database on-demand con scadenza automatica. Ogni esecuzione della pipeline ottiene credenziali uniche che vengono revocate al termine:

```yaml
- name: Get dynamic DB credentials
  uses: hashicorp/vault-action@v3
  with:
    url: https://vault.example.com
    method: jwt
    role: ci-db-access
    secrets: |
      database/creds/ci-role username | DB_USER ;
      database/creds/ci-role password | DB_PASS

- name: Run migrations
  run: flyway -url=$DB_URL -user=$DB_USER -password=$DB_PASS migrate
  env:
    DB_USER: ${{ steps.vault.outputs.DB_USER }}
    DB_PASS: ${{ steps.vault.outputs.DB_PASS }}
```

### 13.3 External Secrets Operator (ESO)

L'**External Secrets Operator** e' un controller Kubernetes che sincronizza i secret da provider esterni (Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) verso Kubernetes Secret nativi:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-credentials
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: api-credentials
    creationPolicy: Owner
  data:
    - secretKey: db-password
      remoteRef:
        key: secret/data/production/db
        property: password
    - secretKey: api-key
      remoteRef:
        key: secret/data/production/api
        property: key
```

ESO riconcilia periodicamente i secret (ogni `refreshInterval`), garantendo che le rotazioni nel vault si propaghino automaticamente ai pod Kubernetes senza restart. La combinazione Vault + ESO + GitOps elimina completamente i secret dal repository Git e dalla configurazione della pipeline.

### 13.4 Prevenzione dei Secret Leak

Strumenti per rilevare secret accidentalmente committati nel codice:

- **gitleaks**: scanner open source che analizza la cronologia Git per pattern di secret (API key, password, token). Configurabile con regole custom.
- **truffleHog**: analizza entropy e pattern per individuare secret nei repository.
- **git-secrets**: hook pre-commit che blocca il commit se contiene pattern sospetti.

```yaml
# Pre-commit hook con gitleaks
- name: Scan for secrets
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

La scansione per secret deve avvenire sia come pre-commit hook locale sia come step nella pipeline CI, implementando difesa in profondita'.

---

## 14. Infrastructure as Code nelle Pipeline

### 14.1 Terraform/OpenTofu in CI/CD

L'integrazione di **Terraform** (o del fork open source **OpenTofu**) nelle pipeline CI/CD segue il pattern **plan-on-PR, apply-on-merge**:

```yaml
# GitHub Actions - Terraform CI/CD
jobs:
  terraform-plan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      id-token: write
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0

      - name: Terraform Init
        run: terraform init -backend-config=backend-prod.hcl
        working-directory: infrastructure/

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        working-directory: infrastructure/

      - name: Comment PR with plan
        uses: actions/github-script@v7
        with:
          script: |
            const plan = `${{ steps.plan.outputs.stdout }}`;
            const truncated = plan.length > 60000
              ? plan.substring(0, 60000) + '\n\n... (truncated)'
              : plan;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `#### Terraform Plan\n\`\`\`\n${truncated}\n\`\`\``
            });

  terraform-apply:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0
      - run: terraform init -backend-config=backend-prod.hcl
        working-directory: infrastructure/
      - run: terraform apply -auto-approve
        working-directory: infrastructure/
```

Il plan viene eseguito su ogni pull request e il risultato pubblicato come commento, permettendo la review delle modifiche infrastrutturali prima del merge. L'apply viene eseguito solo dopo il merge su main, con environment protection rules che richiedono approvazione manuale.

### 14.2 Drift Detection

Il **drift detection** verifica che lo stato reale dell'infrastruttura corrisponda a quello dichiarato nel codice. Terraform plan eseguito periodicamente (non solo su PR) rivela modifiche manuali non tracciate:

```yaml
# Scheduled drift detection
name: Infrastructure Drift Detection
on:
  schedule:
    - cron: '0 8 * * 1-5'    # Lun-Ven alle 08:00

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
        working-directory: infrastructure/
      - name: Check for drift
        id: plan
        run: |
          terraform plan -detailed-exitcode -no-color 2>&1 | tee plan_output.txt
          EXIT_CODE=${PIPESTATUS[0]}
          if [ $EXIT_CODE -eq 2 ]; then
            echo "drift_detected=true" >> "$GITHUB_OUTPUT"
          fi
        working-directory: infrastructure/
        continue-on-error: true

      - name: Alert on drift
        if: steps.plan.outputs.drift_detected == 'true'
        run: |
          curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d '{"text":"ALERT: Infrastructure drift rilevato. Verificare il plan output."}'
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
```

Il codice di uscita `2` di `terraform plan -detailed-exitcode` indica che esistono differenze tra lo stato dichiarato e quello reale. Un'alerting automatico notifica il team per investigare e correggere il drift.

### 14.3 Policy as Code con OPA e Sentinel

**Open Policy Agent (OPA)** e **Sentinel** (HashiCorp) permettono di definire policy di compliance come codice, verificate automaticamente nella pipeline prima dell'apply:

```rego
# policy/terraform.rego - OPA/Conftest
package main

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  not resource.change.after.server_side_encryption_configuration
  msg := sprintf("S3 bucket '%s' deve avere encryption abilitata", [resource.address])
}

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_security_group_rule"
  resource.change.after.cidr_blocks[_] == "0.0.0.0/0"
  resource.change.after.type == "ingress"
  msg := sprintf("Security group '%s': ingress 0.0.0.0/0 non consentito", [resource.address])
}
```

```yaml
# Step nella pipeline
- name: Terraform plan (JSON)
  run: terraform plan -out=tfplan && terraform show -json tfplan > plan.json

- name: Validate policies
  run: conftest test plan.json --policy policy/ --fail-on-warn
```

---

## 15. CI/CD Observability Avanzata

### 15.1 DORA Metrics — Implementazione Pratica

Oltre alla definizione delle DORA metrics (trattata in sezione 9.3), l'implementazione pratica richiede l'instrumentazione della pipeline per raccogliere dati precisi.

**Deployment Frequency** si calcola contando i deployment riusciti in produzione per unita' di tempo. L'instrumentazione avviene registrando un evento a ogni deployment:

```yaml
# Step post-deployment per registrare il deployment
- name: Record deployment event
  run: |
    curl -X POST "$METRICS_ENDPOINT/deployments" \
      -H 'Content-Type: application/json' \
      -d '{
        "service": "${{ github.repository }}",
        "environment": "production",
        "sha": "${{ github.sha }}",
        "deployed_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "deployer": "${{ github.actor }}",
        "pipeline_id": "${{ github.run_id }}"
      }'
```

**Lead Time for Changes** si calcola come differenza tra il timestamp del primo commit (nel merge commit o nella PR) e il timestamp del deployment in produzione. Richiede la correlazione tra commit, pipeline e deployment event.

**Change Failure Rate** richiede la marcatura esplicita dei deployment falliti. Un deployment e' considerato "fallito" se causa un rollback, un hotfix o un incidente entro una finestra temporale definita (tipicamente 24-72 ore).

**Time to Restore Service (MTTR)** si calcola come la durata tra l'apertura di un incidente e il suo ripristino. L'integrazione con sistemi di incident management (PagerDuty, Opsgenie, incident.io) e' essenziale per la raccolta automatica di questo dato.

**Quinta metrica DORA (2025):** il report DORA 2025 ha introdotto una quinta metrica: **Reliability**, misurata come la capacita' del team di raggiungere i propri SLO (Service Level Objectives). Questa metrica lega direttamente le performance di delivery all'esperienza utente.

### 15.2 Pipeline Telemetry con OpenTelemetry

L'applicazione dei principi di osservabilita' alla pipeline stessa (non solo all'applicazione) permette di diagnosticare bottleneck, flaky test e inefficienze. **OpenTelemetry** puo' essere utilizzato per instrumentare le pipeline:

```yaml
# GitHub Actions - Export pipeline telemetry
- name: Export trace
  uses: inception-health/otel-export-trace-action@v2
  with:
    otlpEndpoint: ${{ secrets.OTEL_ENDPOINT }}
    otlpHeaders: ${{ secrets.OTEL_HEADERS }}
    githubToken: ${{ secrets.GITHUB_TOKEN }}
```

Le metriche chiave da monitorare sulla pipeline:

| Metrica | Descrizione | Target |
|---|---|---|
| Pipeline Duration (p50, p95) | Tempo totale dall'attivazione al completamento | < 10 min (CI), < 30 min (CD) |
| Queue Wait Time | Tempo di attesa per un runner disponibile | < 30 sec |
| Stage Duration | Tempo di ciascuno stage | Identificare bottleneck |
| Failure Rate | Percentuale di pipeline fallite | < 10% |
| Flaky Test Rate | Test che falliscono in modo non deterministico | < 1% |
| Cache Hit Rate | Percentuale di hit della cache di dipendenze | > 90% |
| Cost per Build | Costo in minuti/crediti per esecuzione | Trend decrescente |

### 15.3 Dashboard e Alerting

Una dashboard di CI/CD observability dovrebbe includere:

- **Panoramica real-time**: pipeline in esecuzione, in coda, completate/fallite nelle ultime 24 ore.
- **Trend settimanali**: durata media, tasso di successo, DORA metrics, costo cumulativo.
- **Drill-down per servizio/team**: disaggregazione delle metriche per team o micro-servizio.
- **Alert**: notifica quando la durata supera l'SLO, quando il failure rate eccede la soglia, o quando il queue time indica necessita' di scaling dei runner.

GitLab fornisce analytics integrati nella sezione CI/CD Analytics del progetto (pipeline success rate, duration, frequency). Per GitHub Actions, strumenti come **Grafana** con il plugin GitHub Actions o soluzioni dedicate come **Sleuth**, **LinearB** o **Faros AI** calcolano le DORA metrics aggregando dati da GitHub API, deployment events e incident management.

---

## 16. CI/CD Performance Optimization

### 16.1 Strategie di Caching

Il caching e' la leva piu' efficace per ridurre la durata della pipeline. Le strategie variano per piattaforma ma seguono principi comuni.

**Cache delle dipendenze:**

```yaml
# GitHub Actions - Cache multi-layer
- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: |
      node_modules/
      ~/.npm
    key: deps-${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}
    restore-keys: |
      deps-${{ runner.os }}-node-
      deps-${{ runner.os }}-

# GitLab CI - Cache con policy
cache:
  - key:
      files: [package-lock.json]
    paths: [node_modules/]
    policy: pull
  - key:
      files: [package-lock.json]
    paths: [node_modules/]
    policy: push
    when: on_success
```

**Cache dei layer Docker con BuildKit:**

```yaml
# GitHub Actions - Docker layer cache via GitHub Actions cache
- uses: docker/build-push-action@v6
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Cache dei risultati dei test:**

Framework come Jest, Vitest e pytest supportano la cache dei risultati dei test. I test il cui codice sorgente e le cui dipendenze non sono cambiati possono essere saltati, riducendo drasticamente i tempi:

```yaml
- name: Cache test results
  uses: actions/cache@v4
  with:
    path: |
      .jest-cache/
      .pytest_cache/
    key: test-cache-${{ runner.os }}-${{ hashFiles('src/**', 'tests/**') }}
```

**Anti-pattern di caching da evitare:**

- Non cacheare file che cambiano frequentemente (build output, artefatti generati)
- Non cacheare directory troppo grandi (la compressione/decompressione supera il tempo risparmiato)
- Non ignorare l'invalidazione: una cache stale puo' mascherare problemi reali
- Non usare chiavi di cache troppo generiche (cache condivisa tra branch non correlati)

### 16.2 Parallelismo e Sharding

La parallelizzazione distribuisce il lavoro su piu' runner o piu' processi, riducendo il tempo wall-clock. Tre livelli di parallelismo:

**Parallelismo a livello di job:**

```yaml
# GitHub Actions - Job paralleli
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]
  unit-test:
    runs-on: ubuntu-latest
    steps: [...]
  type-check:
    runs-on: ubuntu-latest
    steps: [...]
  # lint, unit-test e type-check eseguono in parallelo
  integration-test:
    needs: [lint, unit-test, type-check]
    runs-on: ubuntu-latest
    steps: [...]
```

**Sharding dei test (partizionamento):**

```yaml
# GitHub Actions - Test sharding con Jest
jobs:
  test:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx jest --shard=${{ matrix.shard }}/4
```

```yaml
# GitLab CI - Test paralleli nativi
test:
  stage: test
  parallel: 4
  script:
    - npx jest --shard=${CI_NODE_INDEX}/${CI_NODE_TOTAL}
```

**Sharding intelligente basato sulla durata storica:**

Strumenti come **jest-split-tests**, **pytest-split** e **Knapsack Pro** distribuiscono i test tra shard in modo bilanciato basandosi sui tempi di esecuzione storici. Senza bilanciamento, uno shard potrebbe ricevere tutti i test lenti, vanificando il beneficio della parallelizzazione:

```yaml
# Jest con split bilanciato
- name: Split tests by timing
  run: |
    npx jest --listTests | \
    npx jest-split-tests \
      --shard-index ${{ matrix.shard-1 }} \
      --shard-count 4 \
      --timing-file test-timings.json \
      > tests-to-run.txt
    npx jest $(cat tests-to-run.txt)
```

### 16.3 Selective Testing e Affected Analysis

L'**affected analysis** determina quali test devono essere eseguiti in base ai file modificati, evitando di eseguire l'intera suite di test per ogni commit:

**Monorepo con Nx/Turborepo:**

```yaml
# GitHub Actions - Nx affected
- name: Run affected tests only
  run: npx nx affected --target=test --base=origin/main --head=HEAD

# Turborepo
- name: Run affected tests
  run: npx turbo run test --filter='...[origin/main]'
```

**Selective testing basato su path:**

```yaml
# GitLab CI - Job condizionale per directory
test-frontend:
  stage: test
  script: npm run test:frontend
  rules:
    - changes:
        - 'frontend/**'
        - 'shared/**'

test-backend:
  stage: test
  script: npm run test:backend
  rules:
    - changes:
        - 'backend/**'
        - 'shared/**'
```

**Jest `--changedSince`:**

```yaml
- name: Run tests for changed files only
  run: npx jest --changedSince=origin/main --passWithNoTests
```

### 16.4 Ottimizzazione delle Immagini Base

Le immagini Docker utilizzate come runner/executor influenzano significativamente i tempi di avvio della pipeline:

- Preferire immagini **Alpine** o **distroless** per dimensioni minime e download rapido.
- Creare **immagini base custom** con gli strumenti preinstallati, evitando di scaricarli ad ogni esecuzione.
- Utilizzare immagini **multi-arch** solo se necessario (il pull di manifesti multi-arch aggiunge overhead).
- Pinnare le immagini al **digest SHA** (non al tag) per riproducibilita' e per beneficiare della cache dei layer.

```dockerfile
# Immagine base custom per pipeline Node.js
FROM node:20-alpine@sha256:a1b2c3d4e5f6...
RUN apk add --no-cache git openssh-client curl jq \
    && npm install -g npm@latest
# Pre-installare strumenti evita il download ad ogni pipeline run
```

### 16.5 Monorepo CI/CD Optimization

I monorepo presentano sfide specifiche per le pipeline CI/CD: senza ottimizzazione, ogni commit attiva la build e i test di tutti i progetti, anche quelli non impattati.

**Strategie di ottimizzazione:**

1. **Path-based triggering**: attivare solo i job relativi ai file modificati.
2. **Dependency graph analysis**: strumenti come Nx e Turborepo analizzano il grafo delle dipendenze per determinare i progetti impattati (direttamente e transitivamente).
3. **Remote caching**: Nx Cloud e Turborepo Remote Cache condividono i risultati delle build tra sviluppatori e pipeline CI, evitando la ricompilazione di artefatti gia' prodotti da un collega.
4. **Incremental builds**: compilare solo i moduli modificati riutilizzando gli output precedenti.

```yaml
# GitHub Actions - Monorepo con Nx
jobs:
  determine-affected:
    runs-on: ubuntu-latest
    outputs:
      affected-projects: ${{ steps.affected.outputs.projects }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: npm ci
      - id: affected
        run: echo "projects=$(npx nx show projects --affected --base=origin/main --json)" >> "$GITHUB_OUTPUT"

  test:
    needs: determine-affected
    if: needs.determine-affected.outputs.affected-projects != '[]'
    strategy:
      matrix:
        project: ${{ fromJson(needs.determine-affected.outputs.affected-projects) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx nx test ${{ matrix.project }}
```

Questo pattern genera un job di test per ciascun progetto impattato, eseguendoli in parallelo. Se nessun progetto e' impattato, l'intera pipeline viene saltata.

---

## Esercizi

1. **Pipeline GitHub Actions base** — Creare un workflow GitHub Actions per un progetto Node.js che esegua: lint, test, build e push dell'immagine Docker su GitHub Container Registry. Pinnare tutte le action a SHA e configurare `permissions: {}` minime. Verificare che il workflow completi in meno di 5 minuti.

2. **OIDC authentication con AWS** — Configurare un workflow GitHub Actions che utilizzi OIDC per autenticarsi su AWS senza credenziali long-lived. Deployare un'immagine container su ECS Fargate. Verificare con CloudTrail che le credenziali temporanee siano effettivamente utilizzate.

3. **GitOps con ArgoCD** — Installare ArgoCD su un cluster Kubernetes locale (kind o k3d). Configurare un'Application che sincronizzi i manifest da un repository Git. Eseguire un deployment modificando il manifest nel repository e verificare la sincronizzazione automatica. Testare il rollback con `git revert`.

4. **Pipeline multi-stage con promozione** — Progettare una pipeline GitLab CI con 5 stage (build, test, scan, deploy-staging, deploy-production). Implementare la promozione manuale da staging a produzione con environment protection rules. Includere smoke test automatici post-deployment che attivano rollback automatico.

5. **DORA metrics dashboard** — Implementare la raccolta delle 4 DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, Time to Restore Service) per una pipeline esistente. Creare un dashboard Grafana che visualizzi i trend settimanali e definire SLO per ciascuna metrica.

6. **Supply chain security end-to-end** — Costruire una pipeline GitHub Actions che implementi il ciclo completo Build → Scan (Trivy) → Sign (cosign keyless) → SBOM (Syft) → Push → Attestation (actions/attest-build-provenance). Configurare una policy Kyverno nel cluster Kubernetes che rifiuti qualsiasi pod con immagini prive di firma cosign valida. Verificare che il deployment di un'immagine non firmata venga bloccato dall'admission controller. Documentare l'intero flusso con gli hash SHA256 di ogni artefatto.

7. **GitLab CI parent-child con monorepo** — Creare un progetto monorepo con tre componenti (frontend React, backend Node.js, servizio Python). Configurare un parent pipeline che generi dinamicamente i child pipeline in base ai file modificati nel commit. Verificare che una modifica solo al frontend attivi esclusivamente la pipeline frontend, senza eseguire build e test di backend e Python. Misurare il risparmio di tempo rispetto alla pipeline monolitica che esegue tutto.

8. **Progressive delivery con Argo Rollouts** — Installare Argo Rollouts su un cluster Kubernetes (kind o k3d). Creare un Rollout con strategia canary a 3 step (10% → 50% → 100%) con AnalysisTemplate che verifichi il success rate HTTP tramite Prometheus. Simulare un deployment con errori (container che restituisce HTTP 500 al 30% delle richieste) e verificare che il rollback automatico si attivi correttamente. Confrontare il comportamento con un Rollout senza analysis (promozione cieca).

9. **Secret management con Vault e OIDC** — Installare HashiCorp Vault in modalita' dev su un cluster Kubernetes. Configurare l'autenticazione JWT/OIDC per GitHub Actions. Creare un workflow che si autentichi a Vault tramite OIDC (senza secret pre-condivisi), recuperi credenziali database dinamiche e le utilizzi per eseguire una migrazione. Verificare nel Vault audit log che le credenziali siano state revocate dopo il completamento della pipeline.

10. **Pipeline performance optimization** — Prendere una pipeline CI esistente con tempo di esecuzione superiore a 15 minuti. Applicare sistematicamente le tecniche di ottimizzazione: caching delle dipendenze, parallelizzazione dei test con sharding, selective testing basato su affected analysis, ottimizzazione dell'immagine base. Misurare la durata prima e dopo ogni ottimizzazione, documentando il risparmio percentuale di ciascun intervento. L'obiettivo e' ridurre la durata sotto i 5 minuti.

11. **Terraform in CI/CD con drift detection** — Configurare una pipeline per un progetto Terraform che implementi: plan commentato sulla pull request, apply automatico dopo il merge su main con environment protection rules, drift detection schedulato ogni 8 ore con notifica Slack. Aggiungere una policy OPA (tramite Conftest) che blocchi la creazione di security group con ingress `0.0.0.0/0` e bucket S3 senza encryption. Verificare che un plan non conforme venga rifiutato dalla pipeline.

12. **Reusable workflows e composite actions** — Creare una libreria di workflow riutilizzabili per un'organizzazione GitHub composta da: (a) un composite action che esegua setup, lint e test per progetti Node.js, (b) un reusable workflow per il build e push di container image con SBOM e firma cosign, (c) un reusable workflow per il deployment GitOps che aggiorni il manifesto nel repository ArgoCD. Integrare i tre componenti in una pipeline completa per un progetto applicativo. Documentare le differenze osservate tra composite action e reusable workflow in termini di visibilita' nell'UI, gestione dei secrets e flessibilita'.

---

## Letture e Riferimenti

### Documentazione ufficiale

- GitHub Actions Documentation: <https://docs.github.com/en/actions> (consultato: 2026-05-24)
- GitLab CI/CD Documentation: <https://docs.gitlab.com/ee/ci/> (consultato: 2026-05-24)
- ArgoCD Documentation: <https://argo-cd.readthedocs.io/en/stable/> (consultato: 2026-05-24)
- Flux CD Documentation: <https://fluxcd.io/docs/> (consultato: 2026-05-24)
- DORA — State of DevOps Research: <https://dora.dev/> (consultato: 2026-05-24)
- GitHub — Security hardening for Actions: <https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect> (consultato: 2026-05-24)
- Jenkins Pipeline Documentation: <https://www.jenkins.io/doc/book/pipeline/> (consultato: 2026-05-24)

### Supply Chain e Sicurezza

- SLSA Framework: <https://slsa.dev/> (consultato: 2026-05-24)
- Sigstore Documentation: <https://docs.sigstore.dev/> (consultato: 2026-05-24)
- Cosign Documentation: <https://docs.sigstore.dev/cosign/overview/> (consultato: 2026-05-24)
- GitHub Artifact Attestation: <https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations> (consultato: 2026-05-24)
- Kyverno Documentation: <https://kyverno.io/docs/> (consultato: 2026-05-24)
- Trivy Documentation: <https://aquasecurity.github.io/trivy/> (consultato: 2026-05-24)

### GitOps e Progressive Delivery

- Argo Rollouts Documentation: <https://argo-rollouts.readthedocs.io/en/stable/> (consultato: 2026-05-24)
- Flagger Documentation: <https://flagger.app/> (consultato: 2026-05-24)
- External Secrets Operator: <https://external-secrets.io/> (consultato: 2026-05-24)
- HashiCorp Vault Documentation: <https://developer.hashicorp.com/vault/docs> (consultato: 2026-05-24)

### DORA e Observability

- DORA — State of DevOps Report 2025: <https://dora.dev/research/> (consultato: 2026-05-24)
- OpenTelemetry CI/CD Observability: <https://opentelemetry.io/docs/concepts/signals/> (consultato: 2026-05-24)

### Libri

- Humble, J.; Farley, D. — *Continuous Delivery*, Addison-Wesley, 2010
- Forsgren, N.; Humble, J.; Kim, G. — *Accelerate*, IT Revolution Press, 2018
- Davis, J.; Daniels, K. — *Effective DevOps*, O'Reilly, 2016
- Bass, L.; Weber, I.; Zhu, L. — *DevOps: A Software Architect's Perspective*, Addison-Wesley, 2015
- Morris, K. — *Infrastructure as Code*, O'Reilly, 2020

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con questo modulo |
|--------|--------|-----------------------------|
| [04-infrastructure-as-code](04-infrastructure-as-code.md) | Infrastructure as Code | Pipeline IaC per provisioning infrastruttura |
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Target di deployment per le pipeline CI/CD |
| [06-docker-avanzato](06-docker-avanzato.md) | Docker Avanzato | Build e push immagini container nella pipeline |
| [08-monitoring-observability](08-monitoring-observability.md) | Monitoring e Observability | Verifica post-deployment e DORA metrics |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza Piattaforme | Shift-left security: SAST, DAST, dependency scan |
| [20-supply-chain-slsa-cosign](20-supply-chain-slsa-cosign.md) | Supply Chain, SLSA e Cosign | Attestation e firma artefatti nella pipeline |
| [15-SECRETS-MANAGEMENT](../15-SECRETS-MANAGEMENT/) | Gestione dei Secrets | Vault, ESO, OIDC per pipeline e cluster |
| [03-git-branching](03-git-branching.md) | Git Branching | Trunk-based vs GitFlow e impatto sulle pipeline CI/CD |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **CI (Continuous Integration)** | Pratica di integrare frequentemente il codice in un repository condiviso, con build e test automatici ad ogni commit |
| **CD (Continuous Delivery/Deployment)** | Estensione della CI che automatizza il rilascio del software fino alla produzione (Deployment) o fino a un ambiente pre-produzione con approvazione manuale (Delivery) |
| **SHA pinning** | Tecnica di fissare le dipendenze (action, immagini) a un hash SHA specifico anziché a un tag mutabile, garantendo riproducibilità e sicurezza |
| **OIDC** | OpenID Connect — protocollo di autenticazione federata che consente alle pipeline CI/CD di ottenere credenziali temporanee da cloud provider senza secret long-lived |
| **GitOps** | Metodologia operativa che utilizza Git come single source of truth per lo stato desiderato dell'infrastruttura e delle applicazioni |
| **ArgoCD** | Controller GitOps per Kubernetes che sincronizza continuamente lo stato del cluster con le definizioni dichiarative in un repository Git |
| **DORA metrics** | Quattro metriche chiave per misurare le performance del software delivery: Deployment Frequency, Lead Time, Change Failure Rate, MTTR |
| **Canary deployment** | Strategia di rilascio che espone gradualmente una nuova versione a una percentuale crescente di traffico prima del rollout completo |
| **Blue-green deployment** | Strategia con due ambienti identici (blue e green) che consente il passaggio istantaneo tra versioni e rollback immediato |
| **Pipeline as Code** | Pratica di definire la pipeline CI/CD in file versionati nel repository (Jenkinsfile, workflow YAML) anziché tramite configurazione manuale |
| **Artefatto immutabile** | Build artifact (immagine container, pacchetto) costruito una sola volta e promosso attraverso gli ambienti senza ricostruzione |
| **Feature flag** | Meccanismo che consente di attivare/disattivare funzionalità in produzione senza deployment, separando il rilascio dal deployment |
| **Smoke test** | Test post-deployment leggero che verifica che le funzionalità critiche dell'applicazione siano operative nell'ambiente target |
| **Trunk-based development** | Modello di branching in cui tutti gli sviluppatori integrano nel branch principale frequentemente, con feature flag per gestire le funzionalità incomplete |
| **SLSA (Supply-chain Levels for Software Artifacts)** | Framework di sicurezza che definisce livelli incrementali di garanzia sulla provenienza e integrita' degli artefatti software, dalla documentazione del build (L1) fino alla build ermetica con dipendenze verificate (L4) |
| **Sigstore** | Progetto open source CNCF che fornisce strumenti per la firma e verifica crittografica degli artefatti software, composto da Cosign (firma), Fulcio (CA effimera) e Rekor (transparency log) |
| **Cosign** | Strumento CLI del progetto Sigstore per firmare e verificare container image e artefatti OCI, con supporto per firma keyless basata su identita' OIDC |
| **SBOM (Software Bill of Materials)** | Inventario completo dei componenti software inclusi in un artefatto (librerie, framework, versioni, licenze) in formato standard SPDX o CycloneDX |
| **Composite Action** | In GitHub Actions, un tipo di action personalizzata che raggruppa piu' step in un'unica unita' riutilizzabile a livello di step, definita in un file action.yml |
| **Reusable Workflow** | In GitHub Actions, un workflow completo riutilizzabile invocabile da altri workflow tramite il trigger workflow_call, operante a livello di job con runs-on proprio |
| **DAG Pipeline** | In GitLab CI, pipeline che utilizza la keyword needs per definire dipendenze dirette tra job, permettendo l'esecuzione parallela di job in stage diversi senza attendere il completamento dell'intero stage precedente |
| **Parent-Child Pipeline** | In GitLab CI, architettura pipeline dove un parent pipeline attiva sotto-pipeline indipendenti (child), ciascuna definita in un file YAML separato, utile per monorepo e pipeline complesse |
| **Dynamic Child Pipeline** | Variante delle parent-child pipeline dove il file di configurazione del child viene generato a runtime, permettendo pipeline adattive basate sui file modificati |
| **JCasC (Jenkins Configuration as Code)** | Plugin Jenkins che permette di definire l'intera configurazione di Jenkins in un file YAML versionato, eliminando la configurazione manuale tramite interfaccia web |
| **Kaniko** | Strumento per il build di container image in userspace senza Docker daemon e senza privilegi elevati, raccomandato per pipeline su Kubernetes |
| **BuildKit** | Backend di build di nuova generazione per Docker che offre build paralleli, caching avanzato e generazione di attestation SLSA |
| **Trivy** | Scanner di sicurezza open source (Aqua Security) per container image, filesystem, repository Git e cluster Kubernetes, con supporto SBOM e policy |
| **Kyverno** | Policy engine Kubernetes-native che definisce policy di ammissione come risorse Kubernetes, utilizzato per verificare firme di immagini e standard di sicurezza |
| **External Secrets Operator (ESO)** | Controller Kubernetes che sincronizza secret da provider esterni (Vault, AWS SM, Azure KV) verso Kubernetes Secret nativi, con riconciliazione periodica |
| **Argo Rollouts** | Controller Kubernetes dell'ecosistema ArgoCD che implementa strategie di deployment avanzate (canary, blue-green) con analisi metrica e promozione/rollback automatici |
| **Flagger** | Operatore Kubernetes dell'ecosistema Flux per progressive delivery, che gestisce deployment canary e primary manipolando service mesh o ingress per il traffic shifting |
| **Flux CD** | Strumento GitOps CNCF per Kubernetes con architettura modulare a controller indipendenti (Source, Kustomize, Helm, Notification, Image Automation) |
| **Affected Analysis** | Tecnica di ottimizzazione CI che determina quali test e build eseguire basandosi sui file modificati e sul grafo delle dipendenze, evitando l'esecuzione dell'intera suite |
| **Test Sharding** | Partizionamento della suite di test in sotto-insiemi eseguiti in parallelo su runner separati, riducendo il tempo wall-clock proporzionalmente al numero di shard |
| **Drift Detection** | Verifica periodica che lo stato reale dell'infrastruttura corrisponda a quello dichiarato nel codice IaC, rilevando modifiche manuali non tracciate |
| **Policy as Code** | Pratica di definire policy di compliance e sicurezza come codice (OPA/Rego, Sentinel) verificato automaticamente nella pipeline prima dell'applicazione di modifiche infrastrutturali |
| **Provenance** | In contesto SLSA, documento che descrive come un artefatto e' stato costruito: sorgente, build system, parametri, dipendenze, in formato in-toto attestation |
| **Keyless Signing** | Modalita' di firma crittografica (Sigstore/Cosign) dove l'identita' del firmatario e' verificata tramite OIDC invece di chiavi private gestite manualmente |

> **Nota**: questa guida copre i principali strumenti e pattern CI/CD. Per approfondimenti specifici su GitHub Actions, consultare `07-GITHUB-E-GITACTIONS/04-github-actions.md`. Per la gestione dei secrets nelle pipeline, fare riferimento a `15-SECRETS-MANAGEMENT/`. Per l'integrazione con Kubernetes, vedere `05-KUBERNETES/`.
