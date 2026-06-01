---
corso: "GitHub e Git Actions"
fase: "5 — Progetti Pratici"
modulo: 5
titolo: "Progetti Pratici GitHub — Guida Completa"
versione: "GitHub Actions 2026"
livello: "Avanzato"
prerequisiti: ["01-fondamenti-git", "02-strategie-branching", "03-piattaforma-github", "04-github-actions"]
obiettivi:
  - "Progettare un repository team con branch protection, template e CODEOWNERS"
  - "Costruire pipeline CI/CD complete con test, build e deploy multi-ambiente"
  - "Automatizzare release con semantic versioning, changelog e GitHub Releases"
  - "Gestire monorepo con path-filtering, affected analysis e deploy selettivo"
  - "Implementare inner source, IaC e security scanning in progetti reali"
tag: [progetti, ci-cd, release, monorepo, inner-source, iac, security-scanning, codeowners, pipeline]
---

# Progetti Pratici GitHub — Guida Completa

> **Modulo 05** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Progettare e configurare un repository team completo con governance, template e automazioni
> 2. Costruire pipeline CI/CD end-to-end con testing, build, deploy multi-ambiente e rollback
> 3. Automatizzare il ciclo di release con semantic versioning, changelog generato e GitHub Releases
> 4. Implementare strategie monorepo con path-filtering, affected analysis e deploy selettivo
> 5. Integrare inner source, Infrastructure as Code e security scanning in workflow di produzione

## Idee guida
1. **README e front porch del progetto.** Investa.
2. **CONTRIBUTING.md riduce friction PR.**
3. **Issue templates + PR templates standardizzano.**
4. **Project boards per backlog.**


## Indice

- [Panoramica](#panoramica)
- [Progetto 1: Setup Repository Team](#progetto-1-setup-repository-team)
- [Progetto 2: Pipeline CI/CD Completa](#progetto-2-pipeline-cicd-completa)
- [Progetto 3: Automazione Release](#progetto-3-automazione-release)
- [Progetto 4: Monorepo Management](#progetto-4-monorepo-management)
- [Progetto 5: Inner Source e Collaborazione](#progetto-5-inner-source-e-collaborazione)
- [Progetto 6: Infrastruttura come Codice](#progetto-6-infrastruttura-come-codice)
- [Checklist Competenze](#checklist-competenze)
- [Risorse per Esercitazione](#risorse-per-esercitazione)
- [Best Practices Progetti](#best-practices-progetti)

---

## Panoramica

Padroneggiare Git, GitHub e GitHub Actions richiede molto di piu della sola teoria: servono progetti pratici, reali e completi che simulino scenari lavorativi concreti. Questa guida raccoglie sei progetti progressivi, ciascuno pensato come esercitazione autonoma e completa. Ogni progetto include comandi da eseguire, file di configurazione pronti all'uso e spiegazioni dettagliate di ogni passaggio.

L'obiettivo e duplice: costruire competenze tecniche solide e creare un portfolio di repository GitHub che dimostri capacita professionali. Al termine di tutti i progetti, avrai esperienza diretta con branch protection, CI/CD, release automation, monorepo management, governance open source e GitOps.

Prerequisiti consigliati prima di iniziare:

- Git installato e configurato localmente
- Account GitHub con accesso a GitHub Actions
- GitHub CLI (`gh`) installato e autenticato
- Familiarita con YAML e la riga di comando
- Editor di testo o IDE configurato

---

## Progetto 1: Setup Repository Team

### Obiettivo

Creare un repository professionale completo di tutte le configurazioni necessarie per il lavoro in team: protezione dei branch, template per issue e pull request, CODEOWNERS, labels personalizzate, Dependabot e un README con badges.

### Passo 1 — Creazione del repository

```bash
# Creare il repository su GitHub tramite CLI
gh repo create team-project-demo \
  --public \
  --description "Repository dimostrativo per workflow di team" \
  --clone

cd team-project-demo
```

### Passo 2 — Struttura directory professionale

```bash
# Creare la struttura di cartelle standard
mkdir -p src tests docs .github/workflows .github/ISSUE_TEMPLATE

# File iniziali
touch src/.gitkeep tests/.gitkeep docs/.gitkeep
```

### Passo 3 — Configurare CODEOWNERS

Il file CODEOWNERS assegna automaticamente i reviewer in base ai file modificati.

```bash
# .github/CODEOWNERS
```

```text
# Ownership globale — review richiesta per ogni PR
* @team-lead

# Frontend — il team frontend revisiona i file nella cartella ui/
/src/ui/         @org/team-frontend
/src/components/ @org/team-frontend

# Backend — il team backend revisiona API e servizi
/src/api/        @org/team-backend
/src/services/   @org/team-backend

# Infrastruttura — solo il team DevOps puo approvare modifiche CI/CD
/.github/        @org/team-devops
/terraform/      @org/team-devops
/docker/         @org/team-devops

# Documentazione — il tech writer revisiona la docs
/docs/           @tech-writer
README.md        @tech-writer @team-lead
```

### Passo 4 — Issue Templates

Creare template strutturati per bug report e feature request.

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: "Segnalazione Bug"
description: "Segnala un bug o un comportamento inatteso"
title: "[BUG] "
labels: ["bug", "triage"]
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        Grazie per la segnalazione. Compila tutti i campi per aiutarci
        a riprodurre e risolvere il problema rapidamente.
  - type: textarea
    id: descrizione
    attributes:
      label: "Descrizione del bug"
      description: "Descrivi chiaramente il comportamento inatteso."
      placeholder: "Quando clicco su X, succede Y invece di Z..."
    validations:
      required: true
  - type: textarea
    id: riproduzione
    attributes:
      label: "Passi per riprodurre"
      description: "Elenca i passi necessari per riprodurre il bug."
      value: |
        1. Vai a '...'
        2. Clicca su '...'
        3. Scorri fino a '...'
        4. Osserva l'errore
    validations:
      required: true
  - type: dropdown
    id: gravita
    attributes:
      label: "Gravita"
      options:
        - Critica (blocca il lavoro)
        - Alta (impatto significativo)
        - Media (impatto moderato)
        - Bassa (impatto minimo)
    validations:
      required: true
  - type: textarea
    id: ambiente
    attributes:
      label: "Ambiente"
      description: "Sistema operativo, browser, versione dell'app, ecc."
      placeholder: "OS: macOS 14.2, Browser: Chrome 120, App: v2.3.1"
    validations:
      required: true
  - type: textarea
    id: screenshot
    attributes:
      label: "Screenshot o log"
      description: "Allega screenshot o log rilevanti (facoltativo)."
    validations:
      required: false
```

```yaml
# .github/ISSUE_TEMPLATE/feature_request.yml
name: "Richiesta Funzionalita"
description: "Proponi una nuova funzionalita o un miglioramento"
title: "[FEATURE] "
labels: ["enhancement", "triage"]
body:
  - type: textarea
    id: problema
    attributes:
      label: "Problema da risolvere"
      description: "Quale problema o esigenza affronta questa funzionalita?"
    validations:
      required: true
  - type: textarea
    id: soluzione
    attributes:
      label: "Soluzione proposta"
      description: "Descrivi la soluzione che vorresti."
    validations:
      required: true
  - type: textarea
    id: alternative
    attributes:
      label: "Alternative considerate"
      description: "Hai valutato altre soluzioni? Quali e perche le hai scartate?"
    validations:
      required: false
  - type: dropdown
    id: priorita
    attributes:
      label: "Priorita suggerita"
      options:
        - Alta
        - Media
        - Bassa
    validations:
      required: true
```

### Passo 5 — Pull Request Template

```markdown
<!-- .github/pull_request_template.md -->

## Descrizione

<!-- Descrivi brevemente le modifiche apportate e il motivo -->

## Tipo di modifica

- [ ] Bug fix (correzione che non modifica API esistenti)
- [ ] Nuova funzionalita (modifica che aggiunge funzionalita)
- [ ] Breaking change (modifica che altera il comportamento esistente)
- [ ] Refactoring (nessun cambiamento funzionale)
- [ ] Documentazione
- [ ] Configurazione CI/CD

## Issue collegata

Closes #

## Checklist

- [ ] Il codice segue le convenzioni di stile del progetto
- [ ] Ho aggiunto test che coprono le modifiche
- [ ] Tutti i test esistenti passano (`npm test`)
- [ ] Ho aggiornato la documentazione (se necessario)
- [ ] Ho verificato che non ci siano regressioni
- [ ] La PR ha dimensioni ragionevoli (< 400 righe modificate)

## Screenshot (se applicabile)

<!-- Allega screenshot per modifiche UI -->

## Note per i reviewer

<!-- Indica aree specifiche su cui concentrare la review -->
```

### Passo 6 — Labels personalizzate

```bash
# Eliminare le labels di default e crearne di personalizzate
gh label delete "bug" --yes 2>/dev/null
gh label delete "enhancement" --yes 2>/dev/null
gh label delete "documentation" --yes 2>/dev/null

# Labels per tipo
gh label create "bug"           --color "d73a4a" --description "Qualcosa non funziona correttamente"
gh label create "enhancement"   --color "a2eeef" --description "Nuova funzionalita o miglioramento"
gh label create "documentation" --color "0075ca" --description "Modifiche alla documentazione"
gh label create "refactoring"   --color "d4c5f9" --description "Miglioramento codice senza cambio funzionale"
gh label create "security"      --color "e11d48" --description "Problema di sicurezza"

# Labels per priorita
gh label create "priority: critical" --color "b60205" --description "Blocca il rilascio"
gh label create "priority: high"     --color "d93f0b" --description "Da risolvere nel prossimo sprint"
gh label create "priority: medium"   --color "fbca04" --description "Importante ma non urgente"
gh label create "priority: low"      --color "0e8a16" --description "Nice to have"

# Labels per stato
gh label create "triage"             --color "ededed" --description "Da valutare"
gh label create "in progress"        --color "1d76db" --description "In lavorazione"
gh label create "needs review"       --color "5319e7" --description "Pronta per review"
gh label create "blocked"            --color "b60205" --description "Bloccata da dipendenza esterna"
```

### Passo 7 — Configurazione Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Dipendenze npm
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "team-lead"
    labels:
      - "dependencies"
      - "priority: medium"
    commit-message:
      prefix: "deps"
      include: "scope"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "ci/cd"
```

### Passo 8 — Branch Protection Rules

```bash
# Proteggere il branch main tramite CLI
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/test","ci/lint"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null \
  --field required_linear_history=true \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

### Passo 9 — README professionale con badges

```markdown
# Team Project Demo

[![CI](https://github.com/OWNER/team-project-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/team-project-demo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/OWNER/team-project-demo/branch/main/graph/badge.svg)](https://codecov.io/gh/OWNER/team-project-demo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Repository dimostrativo per workflow di team con GitHub Actions.

## Quick Start

...il contenuto del README continua con istruzioni di setup, contribuzione, ecc.
```

### Passo 10 — Commit iniziale e push

```bash
git add -A
git commit -m "chore: setup iniziale repository con configurazione team completa"
git push origin main
```

---

## Progetto 2: Pipeline CI/CD Completa

### Obiettivo

Costruire una pipeline CI/CD completa per un'applicazione Node.js con lint, test, build, deploy a staging e production, caching ottimizzato e matrix testing.

### Passo 1 — Workflow CI (lint, test, build)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

# Cancella esecuzioni precedenti sullo stesso branch/PR
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: "Lint"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"

      - name: Installare dipendenze
        run: npm ci

      - name: Eseguire ESLint
        run: npm run lint

      - name: Controllare formattazione Prettier
        run: npm run format:check

  test:
    name: "Test (Node ${{ matrix.node-version }})"
    runs-on: ubuntu-latest
    # Matrix testing: verificare compatibilita su piu versioni
    strategy:
      fail-fast: false
      matrix:
        node-version: [18, 20, 22]
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: "npm"

      - name: Installare dipendenze
        run: npm ci

      - name: Eseguire test con coverage
        run: npm run test:coverage

      - name: Caricare report coverage
        if: matrix.node-version == 20
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info
          fail_ci_if_error: true

  build:
    name: "Build"
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"

      - name: Installare dipendenze
        run: npm ci

      - name: Build applicazione
        run: npm run build

      # Salvare gli artefatti di build per il deploy successivo
      - name: Upload artefatti build
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7
```

### Passo 2 — Workflow CD (deploy staging e production)

```yaml
# .github/workflows/cd.yml
name: CD

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

jobs:
  deploy-staging:
    name: "Deploy Staging"
    runs-on: ubuntu-latest
    # Eseguire solo se la CI e passata con successo
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    environment:
      name: staging
      url: https://staging.esempio.com
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Scaricare artefatti build dalla CI
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Deploy a staging
        env:
          DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}
          STAGING_HOST: ${{ vars.STAGING_HOST }}
        run: |
          echo "Deploying build artefatti a staging..."
          # Esempio con rsync via SSH
          # rsync -avz --delete dist/ $STAGING_HOST:/var/www/app/

      - name: Smoke test staging
        run: |
          echo "Eseguendo smoke test su staging..."
          # curl --fail https://staging.esempio.com/health || exit 1

      - name: Notifica successo staging
        if: success()
        uses: slackapi/slack-github-action@v1.27.0
        with:
          payload: |
            {
              "text": "Deploy staging completato con successo per commit ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

  deploy-production:
    name: "Deploy Production"
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment:
      name: production
      url: https://www.esempio.com
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Scaricare artefatti build
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Deploy a production
        env:
          DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}
          PROD_HOST: ${{ vars.PROD_HOST }}
        run: |
          echo "Deploying build artefatti a production..."
          # Esempio: deploy su cloud provider
          # aws s3 sync dist/ s3://prod-bucket/ --delete
          # aws cloudfront create-invalidation --distribution-id $CF_ID --paths "/*"

      - name: Smoke test production
        run: |
          echo "Eseguendo smoke test su production..."
          # curl --fail https://www.esempio.com/health || exit 1

  notify-failure:
    name: "Notifica Fallimento"
    runs-on: ubuntu-latest
    needs: [deploy-staging, deploy-production]
    if: failure()
    steps:
      - name: Inviare notifica di fallimento
        uses: slackapi/slack-github-action@v1.27.0
        with:
          payload: |
            {
              "text": ":red_circle: DEPLOY FALLITO per ${{ github.repository }} — Commit: ${{ github.sha }}\nWorkflow: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Passo 3 — Configurazione degli Environments

```bash
# Creare gli environments tramite gh CLI
# Staging: deploy automatico
gh api repos/{owner}/{repo}/environments/staging \
  --method PUT \
  --field wait_timer=0

# Production: richiede approvazione manuale
gh api repos/{owner}/{repo}/environments/production \
  --method PUT \
  --field reviewers='[{"type":"User","id":12345}]' \
  --field wait_timer=5
```

### Note sull'architettura della pipeline

La pipeline segue il pattern "CI passa, CD esegue": il workflow CD si attiva automaticamente solo quando la CI termina con successo sul branch `main`. L'environment `production` richiede approvazione manuale, creando un gate di sicurezza tra staging e produzione. La `concurrency` nella CI garantisce che push successivi rapidi non consumino risorse inutili: le esecuzioni precedenti vengono cancellate.

---

## Progetto 3: Automazione Release

### Obiettivo

Automatizzare completamente il processo di release: enforcement dei conventional commits, generazione automatica del changelog, semantic versioning, creazione della GitHub Release, build e push dell'immagine Docker a GitHub Container Registry (GHCR) e deploy automatico post-release.

### Passo 1 — Conventional Commits Enforcement

```yaml
# .github/workflows/commitlint.yml
name: Commit Lint

on:
  pull_request:
    branches: [main]

jobs:
  commitlint:
    name: "Verifica Conventional Commits"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Installare commitlint
        run: |
          npm install --save-dev @commitlint/cli @commitlint/config-conventional

      - name: Verificare messaggi di commit
        run: |
          npx commitlint \
            --from ${{ github.event.pull_request.base.sha }} \
            --to ${{ github.event.pull_request.head.sha }} \
            --verbose
```

Configurazione commitlint nel progetto:

```javascript
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Tipi ammessi
    'type-enum': [2, 'always', [
      'feat',     // nuova funzionalita
      'fix',      // correzione bug
      'docs',     // documentazione
      'style',    // formattazione (non cambia la logica)
      'refactor', // refactoring codice
      'perf',     // miglioramento prestazioni
      'test',     // aggiunta o modifica test
      'build',    // modifiche al sistema di build
      'ci',       // modifiche alla CI
      'chore',    // manutenzione generica
      'revert'    // revert di un commit precedente
    ]],
    // Lunghezza massima del soggetto
    'subject-max-length': [2, 'always', 72],
    // Il corpo del messaggio deve avere una riga vuota prima
    'body-leading-blank': [2, 'always'],
  }
};
```

### Passo 2 — Workflow Release Automatica

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  packages: write
  pull-requests: write

jobs:
  release:
    name: "Creare Release"
    runs-on: ubuntu-latest
    outputs:
      released: ${{ steps.release.outputs.releases_created }}
      tag: ${{ steps.release.outputs.tag_name }}
      version: ${{ steps.release.outputs.major }}.${{ steps.release.outputs.minor }}.${{ steps.release.outputs.patch }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # release-please analizza i commit e crea automaticamente
      # la PR di release con changelog aggiornato
      - name: Release Please
        id: release
        uses: googleapis/release-please-action@v4
        with:
          release-type: node
          # Configurazione changelog personalizzata
          changelog-types: |
            [
              {"type":"feat","section":"Nuove Funzionalita","hidden":false},
              {"type":"fix","section":"Correzioni Bug","hidden":false},
              {"type":"perf","section":"Miglioramenti Prestazioni","hidden":false},
              {"type":"docs","section":"Documentazione","hidden":false},
              {"type":"refactor","section":"Refactoring","hidden":true},
              {"type":"chore","section":"Manutenzione","hidden":true}
            ]

  docker:
    name: "Build e Push Docker Image"
    runs-on: ubuntu-latest
    needs: release
    # Eseguire solo se release-please ha creato una nuova release
    if: ${{ needs.release.outputs.released == 'true' }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login a GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Estrarre metadata Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            # Tag con la versione semantica
            type=semver,pattern={{version}},value=${{ needs.release.outputs.tag }}
            type=semver,pattern={{major}}.{{minor}},value=${{ needs.release.outputs.tag }}
            type=semver,pattern={{major}},value=${{ needs.release.outputs.tag }}
            # Tag latest per il branch main
            type=raw,value=latest

      - name: Build e push immagine Docker
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          # Multi-platform build
          platforms: linux/amd64,linux/arm64

  deploy-post-release:
    name: "Deploy Post-Release"
    runs-on: ubuntu-latest
    needs: [release, docker]
    if: ${{ needs.release.outputs.released == 'true' }}
    environment:
      name: production
      url: https://www.esempio.com
    steps:
      - name: Deploy nuova versione
        run: |
          echo "Deploying versione ${{ needs.release.outputs.version }}..."
          echo "Immagine: ghcr.io/${{ github.repository }}:${{ needs.release.outputs.version }}"
          # Esempio: aggiornare il deployment Kubernetes
          # kubectl set image deployment/app \
          #   app=ghcr.io/${{ github.repository }}:${{ needs.release.outputs.version }}

      - name: Verificare deploy
        run: |
          echo "Verificando che la nuova versione sia attiva..."
          # curl -s https://www.esempio.com/version | grep "${{ needs.release.outputs.version }}"
```

### Passo 3 — Configurazione release-please

```json
// release-please-config.json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "node",
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true,
  "include-v-in-tag": true,
  "pull-request-title-pattern": "chore: release ${version}",
  "changelog-sections": [
    { "type": "feat", "section": "Nuove Funzionalita" },
    { "type": "fix", "section": "Correzioni Bug" },
    { "type": "perf", "section": "Prestazioni" },
    { "type": "docs", "section": "Documentazione" },
    { "type": "refactor", "section": "Refactoring", "hidden": true },
    { "type": "test", "section": "Test", "hidden": true },
    { "type": "chore", "section": "Manutenzione", "hidden": true }
  ]
}
```

### Flusso complessivo della release

1. Lo sviluppatore crea PR con conventional commits (es. `feat: aggiunta autenticazione OAuth`)
2. La PR viene mergiata su `main`
3. `release-please` analizza i commit e apre una PR di release con il changelog aggiornato
4. Quando la PR di release viene mergiata, `release-please` crea il tag Git e la GitHub Release
5. Il job `docker` costruisce l'immagine e la pubblica su GHCR con i tag di versione
6. Il job `deploy-post-release` esegue il deploy automatico della nuova versione

---

## Progetto 4: Monorepo Management

### Obiettivo

Gestire un monorepo con piu applicazioni e pacchetti condivisi, utilizzando trigger basati sui percorsi per eseguire build e deploy selettivi.

### Passo 1 — Struttura del monorepo

```
monorepo/
├── apps/
│   ├── web/               # Applicazione frontend React
│   │   ├── package.json
│   │   ├── src/
│   │   └── Dockerfile
│   ├── api/               # Servizio backend Node.js
│   │   ├── package.json
│   │   ├── src/
│   │   └── Dockerfile
│   └── admin/             # Pannello di amministrazione
│       ├── package.json
│       ├── src/
│       └── Dockerfile
├── packages/
│   ├── ui/                # Componenti UI condivisi
│   │   ├── package.json
│   │   └── src/
│   ├── utils/             # Utilita condivise
│   │   ├── package.json
│   │   └── src/
│   └── config/            # Configurazioni condivise (ESLint, TS)
│       └── package.json
├── package.json           # Root con workspaces
├── turbo.json             # Configurazione Turborepo (opzionale)
└── .github/
    └── workflows/
        ├── ci-web.yml
        ├── ci-api.yml
        └── ci-shared.yml
```

### Passo 2 — Rilevamento file modificati

```yaml
# .github/workflows/detect-changes.yml
name: Detect Changes

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  detect:
    name: "Rilevare componenti modificati"
    runs-on: ubuntu-latest
    outputs:
      web: ${{ steps.filter.outputs.web }}
      api: ${{ steps.filter.outputs.api }}
      admin: ${{ steps.filter.outputs.admin }}
      shared-ui: ${{ steps.filter.outputs.shared-ui }}
      shared-utils: ${{ steps.filter.outputs.shared-utils }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Rilevare percorsi modificati
        id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            web:
              - 'apps/web/**'
              - 'packages/ui/**'
              - 'packages/utils/**'
              - 'packages/config/**'
            api:
              - 'apps/api/**'
              - 'packages/utils/**'
              - 'packages/config/**'
            admin:
              - 'apps/admin/**'
              - 'packages/ui/**'
              - 'packages/utils/**'
            shared-ui:
              - 'packages/ui/**'
            shared-utils:
              - 'packages/utils/**'

  ci-web:
    name: "CI Web App"
    needs: detect
    if: ${{ needs.detect.outputs.web == 'true' }}
    uses: ./.github/workflows/ci-web.yml

  ci-api:
    name: "CI API Service"
    needs: detect
    if: ${{ needs.detect.outputs.api == 'true' }}
    uses: ./.github/workflows/ci-api.yml

  ci-shared:
    name: "CI Pacchetti Condivisi"
    needs: detect
    if: ${{ needs.detect.outputs.shared-ui == 'true' || needs.detect.outputs.shared-utils == 'true' }}
    uses: ./.github/workflows/ci-shared.yml
```

### Passo 3 — Workflow CI riutilizzabile per singola app

```yaml
# .github/workflows/ci-web.yml
name: CI Web App

on:
  workflow_call:
  # Permettere anche l'esecuzione manuale per debug
  workflow_dispatch:

defaults:
  run:
    working-directory: apps/web

jobs:
  test:
    name: "Test Web App"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "npm"

      # Installare tutte le dipendenze dal root (npm workspaces)
      - name: Installare dipendenze
        run: npm ci
        working-directory: .

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm run test

      - name: Build
        run: npm run build

  docker:
    name: "Build Docker Image Web"
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3

      # Build dell'immagine senza push (solo validazione)
      - name: Build immagine Docker
        uses: docker/build-push-action@v6
        with:
          context: .
          file: apps/web/Dockerfile
          push: false
          tags: monorepo/web:test
          cache-from: type=gha,scope=web
          cache-to: type=gha,scope=web,mode=max
```

### Passo 4 — Deploy indipendente per servizio

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  detect:
    name: "Rilevare modifiche"
    runs-on: ubuntu-latest
    outputs:
      web: ${{ steps.filter.outputs.web }}
      api: ${{ steps.filter.outputs.api }}
    steps:
      - uses: actions/checkout@v4
      - id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            web:
              - 'apps/web/**'
              - 'packages/ui/**'
              - 'packages/utils/**'
            api:
              - 'apps/api/**'
              - 'packages/utils/**'

  deploy-web:
    name: "Deploy Web"
    needs: detect
    if: ${{ needs.detect.outputs.web == 'true' }}
    runs-on: ubuntu-latest
    environment:
      name: production-web
      url: https://www.esempio.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy frontend
        run: |
          echo "Deploying solo il frontend..."
          # npm run deploy --workspace=apps/web

  deploy-api:
    name: "Deploy API"
    needs: detect
    if: ${{ needs.detect.outputs.api == 'true' }}
    runs-on: ubuntu-latest
    environment:
      name: production-api
      url: https://api.esempio.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy backend API
        run: |
          echo "Deploying solo il backend API..."
          # npm run deploy --workspace=apps/api
```

Il vantaggio chiave e che modificare solo il frontend non attiva il build e il deploy del backend e viceversa, risparmiando tempo e risorse CI/CD.

---

## Progetto 5: Inner Source e Collaborazione

### Obiettivo

Configurare un progetto inner source enterprise con governance, automazione delle review, labeling automatico, gestione issue stale e documentazione integrata.

### Passo 1 — CONTRIBUTING.md

```markdown
<!-- CONTRIBUTING.md -->
# Come Contribuire

Grazie per il tuo interesse nel contribuire a questo progetto!

## Processo di Contribuzione

1. **Apri una issue** descrivendo il problema o la funzionalita proposta
2. **Attendi il feedback** del team di maintainer
3. **Crea un fork** del repository (o un branch se hai accesso diretto)
4. **Implementa le modifiche** seguendo le convenzioni del progetto
5. **Scrivi i test** per le modifiche apportate
6. **Apri una Pull Request** collegandola alla issue

## Convenzioni

### Messaggi di Commit
Utilizziamo [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: descrizione` per nuove funzionalita
- `fix: descrizione` per correzioni
- `docs: descrizione` per documentazione
- `refactor: descrizione` per refactoring

### Stile Codice
- Eseguire `npm run lint` prima di ogni commit
- Seguire la configurazione ESLint e Prettier del progetto
- Mantenere la copertura test sopra l'80%

### Pull Request
- Le PR devono essere di dimensioni ragionevoli (< 400 righe)
- Ogni PR deve avere una descrizione chiara e collegamento alla issue
- Almeno una review approvata e richiesta prima del merge
- Tutti i check CI devono passare

## Codice di Condotta
Questo progetto adotta il [Contributor Covenant](https://www.contributor-covenant.org/).
Leggere CODE_OF_CONDUCT.md per i dettagli.
```

### Passo 2 — Automazione con GitHub Actions

```yaml
# .github/workflows/auto-assign.yml
name: Auto Assign

on:
  pull_request:
    types: [opened]

jobs:
  assign:
    name: "Auto-assign reviewer e assignee"
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - name: Auto-assign autore come assignee
        uses: actions/github-script@v7
        with:
          script: |
            // Assegnare l'autore della PR come assignee
            await github.rest.issues.addAssignees({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              assignees: [context.payload.pull_request.user.login]
            });
```

```yaml
# .github/workflows/auto-label.yml
name: Auto Label

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  label:
    name: "Aggiungere labels automatiche in base ai file"
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Labeler
        uses: actions/labeler@v5
        with:
          repo-token: "${{ secrets.GITHUB_TOKEN }}"
          configuration-path: .github/labeler.yml
```

```yaml
# .github/labeler.yml — configurazione per actions/labeler
frontend:
  - changed-files:
    - any-glob-to-any-file: ['src/ui/**', 'src/components/**', '*.css', '*.scss']

backend:
  - changed-files:
    - any-glob-to-any-file: ['src/api/**', 'src/services/**', 'src/middleware/**']

documentation:
  - changed-files:
    - any-glob-to-any-file: ['docs/**', '*.md']

ci/cd:
  - changed-files:
    - any-glob-to-any-file: ['.github/**']

tests:
  - changed-files:
    - any-glob-to-any-file: ['tests/**', '**/*.test.*', '**/*.spec.*']

dependencies:
  - changed-files:
    - any-glob-to-any-file: ['package.json', 'package-lock.json', 'yarn.lock']
```

### Passo 3 — Stale Bot per issue e PR inattive

```yaml
# .github/workflows/stale.yml
name: Stale Issues e PR

on:
  schedule:
    # Eseguire ogni giorno alle 2:00 del mattino (ora di Roma)
    - cron: "0 0 * * *"

permissions:
  issues: write
  pull-requests: write

jobs:
  stale:
    name: "Gestire issue e PR inattive"
    runs-on: ubuntu-latest
    steps:
      - name: Contrassegnare elementi inattivi
        uses: actions/stale@v9
        with:
          # Issue inattive dopo 30 giorni, chiuse dopo altri 7
          days-before-issue-stale: 30
          days-before-issue-close: 7
          stale-issue-label: "stale"
          stale-issue-message: >
            Questa issue e stata inattiva per 30 giorni.
            Verra chiusa automaticamente tra 7 giorni se non ci saranno aggiornamenti.
            Se e ancora rilevante, aggiungi un commento per mantenerla aperta.
          close-issue-message: >
            Questa issue e stata chiusa per inattivita.
            Riaprila se necessario.

          # PR inattive dopo 14 giorni, chiuse dopo altri 7
          days-before-pr-stale: 14
          days-before-pr-close: 7
          stale-pr-label: "stale"
          stale-pr-message: >
            Questa PR e stata inattiva per 14 giorni.
            Verra chiusa automaticamente tra 7 giorni.
            Aggiorna il branch o aggiungi un commento per mantenerla aperta.

          # Non contrassegnare come stale gli elementi con queste labels
          exempt-issue-labels: "priority: critical,priority: high,pinned"
          exempt-pr-labels: "priority: critical,work-in-progress"
```

### Passo 4 — Security scanning integrato

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Scansione settimanale completa
    - cron: "0 3 * * 1"

permissions:
  security-events: write
  contents: read

jobs:
  codeql:
    name: "CodeQL Analysis"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Inizializzare CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript-typescript
          queries: security-extended

      - name: Eseguire analisi CodeQL
        uses: github/codeql-action/analyze@v3

  dependency-review:
    name: "Revisione Dipendenze"
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Revisione dipendenze
        uses: actions/dependency-review-action@v4
        with:
          # Bloccare PR che introducono vulnerabilita critiche o alte
          fail-on-severity: high
          # Rifiutare licenze problematiche
          deny-licenses: GPL-3.0, AGPL-3.0

  secret-scanning:
    name: "Scansione Segreti"
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Scansione segreti con Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Progetto 6: Infrastruttura come Codice

### Obiettivo

Implementare un workflow GitOps per gestire infrastruttura tramite Terraform, con plan automatico su PR, apply su merge, policy as code e drift detection programmato.

### Passo 1 — Struttura del repository IaC

```
infra-repo/
├── environments/
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── compute/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── database/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── policies/
│   ├── tags.rego         # Policy OPA per i tag obbligatori
│   └── security.rego     # Policy OPA per sicurezza
├── .github/
│   └── workflows/
│       ├── terraform-plan.yml
│       ├── terraform-apply.yml
│       └── drift-detection.yml
└── .tflint.hcl
```

### Passo 2 — Workflow Terraform Plan su PR

```yaml
# .github/workflows/terraform-plan.yml
name: Terraform Plan

on:
  pull_request:
    branches: [main]
    paths:
      - 'environments/**'
      - 'modules/**'

permissions:
  contents: read
  pull-requests: write

env:
  TF_VERSION: "1.7.0"
  AWS_REGION: "eu-south-1"

jobs:
  detect-env:
    name: "Rilevare environment modificati"
    runs-on: ubuntu-latest
    outputs:
      staging: ${{ steps.filter.outputs.staging }}
      production: ${{ steps.filter.outputs.production }}
    steps:
      - uses: actions/checkout@v4
      - id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            staging:
              - 'environments/staging/**'
              - 'modules/**'
            production:
              - 'environments/production/**'
              - 'modules/**'

  plan:
    name: "Plan ${{ matrix.environment }}"
    runs-on: ubuntu-latest
    needs: detect-env
    strategy:
      fail-fast: false
      matrix:
        environment: [staging, production]
        exclude:
          - environment: ${{ needs.detect-env.outputs.staging != 'true' && 'staging' || 'none' }}
          - environment: ${{ needs.detect-env.outputs.production != 'true' && 'production' || 'none' }}
    defaults:
      run:
        working-directory: environments/${{ matrix.environment }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configurare credenziali AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets[format('{0}_AWS_ROLE', matrix.environment)] }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        run: terraform init -input=false

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Format Check
        run: terraform fmt -check -recursive

      - name: Terraform Plan
        id: plan
        run: |
          terraform plan -input=false -no-color -out=tfplan \
            2>&1 | tee plan_output.txt
        continue-on-error: true

      - name: Pubblicare plan come commento sulla PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const planOutput = fs.readFileSync(
              'environments/${{ matrix.environment }}/plan_output.txt', 'utf8'
            );
            // Troncare se troppo lungo per un commento GitHub
            const maxLength = 60000;
            const truncated = planOutput.length > maxLength
              ? planOutput.substring(0, maxLength) + '\n\n... (troncato)'
              : planOutput;

            const body = `### Terraform Plan — \`${{ matrix.environment }}\`

            \`\`\`hcl
            ${truncated}
            \`\`\`

            *Stato:* ${{ steps.plan.outcome == 'success' && 'Successo' || 'Fallito' }}
            *Workflow:* [Link](${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID})`;

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body: body
            });

      - name: Verificare esito del plan
        if: steps.plan.outcome == 'failure'
        run: exit 1

  policy-check:
    name: "Policy Check (OPA)"
    runs-on: ubuntu-latest
    needs: detect-env
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Conftest
        uses: open-policy-agent/setup-opa@v2

      - name: Installare Conftest
        run: |
          LATEST=$(curl -s https://api.github.com/repos/open-policy-agent/conftest/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
          wget -q "https://github.com/open-policy-agent/conftest/releases/download/v${LATEST}/conftest_${LATEST}_Linux_x86_64.tar.gz"
          tar xzf conftest_*.tar.gz
          sudo mv conftest /usr/local/bin/

      - name: Verificare policy su staging
        if: needs.detect-env.outputs.staging == 'true'
        run: |
          cd environments/staging
          terraform init -input=false
          terraform plan -input=false -out=tfplan
          terraform show -json tfplan > plan.json
          conftest test plan.json -p ../../policies/
```

### Passo 3 — Workflow Terraform Apply su merge

```yaml
# .github/workflows/terraform-apply.yml
name: Terraform Apply

on:
  push:
    branches: [main]
    paths:
      - 'environments/**'
      - 'modules/**'

permissions:
  contents: read

env:
  TF_VERSION: "1.7.0"
  AWS_REGION: "eu-south-1"

jobs:
  apply-staging:
    name: "Apply Staging"
    runs-on: ubuntu-latest
    environment:
      name: staging-infra
    defaults:
      run:
        working-directory: environments/staging
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configurare credenziali AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.STAGING_AWS_ROLE }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        run: terraform init -input=false

      - name: Terraform Apply
        run: terraform apply -input=false -auto-approve

  apply-production:
    name: "Apply Production"
    runs-on: ubuntu-latest
    needs: apply-staging
    environment:
      name: production-infra
    defaults:
      run:
        working-directory: environments/production
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configurare credenziali AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.PROD_AWS_ROLE }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        run: terraform init -input=false

      - name: Terraform Apply
        run: terraform apply -input=false -auto-approve
```

### Passo 4 — Drift Detection programmato

```yaml
# .github/workflows/drift-detection.yml
name: Drift Detection

on:
  schedule:
    # Eseguire ogni giorno alle 6:00 del mattino ora di Roma
    - cron: "0 4 * * *"
  workflow_dispatch:

permissions:
  contents: read
  issues: write

env:
  TF_VERSION: "1.7.0"
  AWS_REGION: "eu-south-1"

jobs:
  drift:
    name: "Drift Detection — ${{ matrix.environment }}"
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]
    defaults:
      run:
        working-directory: environments/${{ matrix.environment }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configurare credenziali AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets[format('{0}_AWS_ROLE', matrix.environment)] }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        run: terraform init -input=false

      - name: Verificare drift
        id: drift
        run: |
          # -detailed-exitcode: exit 0 = nessun cambiamento, exit 2 = cambiamenti rilevati
          terraform plan -input=false -detailed-exitcode -no-color \
            2>&1 | tee drift_output.txt || echo "exitcode=$?" >> "$GITHUB_OUTPUT"
        continue-on-error: true

      - name: Creare issue se drift rilevato
        if: steps.drift.outputs.exitcode == '2'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const driftOutput = fs.readFileSync(
              'environments/${{ matrix.environment }}/drift_output.txt', 'utf8'
            );
            const truncated = driftOutput.length > 50000
              ? driftOutput.substring(0, 50000) + '\n... (troncato)'
              : driftOutput;

            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Drift rilevato in ${{ matrix.environment }} — ${new Date().toISOString().split('T')[0]}`,
              body: `## Drift dell'infrastruttura rilevato

            **Environment:** \`${{ matrix.environment }}\`
            **Data:** ${new Date().toISOString()}

            ### Dettagli del drift

            \`\`\`hcl
            ${truncated}
            \`\`\`

            ### Azione richiesta
            Verificare se le modifiche sono intenzionali. Se non lo sono, eseguire un \`terraform apply\` per riportare l'infrastruttura allo stato desiderato.`,
              labels: ['drift', 'infra', 'priority: high']
            });
```

### Esempio Policy OPA

```rego
# policies/tags.rego
# Policy: tutte le risorse devono avere i tag obbligatori

package main

# Tag obbligatori per ogni risorsa
required_tags := {"Environment", "Project", "ManagedBy", "Owner"}

# Verificare che tutte le risorse abbiano i tag richiesti
deny[msg] {
    resource := input.resource_changes[_]
    resource.change.actions[_] == "create"

    tags := object.get(resource.change.after, "tags", {})
    missing := required_tags - {key | tags[key]}
    count(missing) > 0

    msg := sprintf(
        "Risorsa '%s' di tipo '%s' manca dei tag obbligatori: %v",
        [resource.address, resource.type, missing]
    )
}
```

```rego
# policies/security.rego
# Policy: regole di sicurezza base per le risorse cloud

package main

# Vietare bucket S3 pubblici
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    resource.change.after.acl == "public-read"

    msg := sprintf(
        "Bucket S3 '%s' non puo avere ACL 'public-read'. Usare policy IAM specifiche.",
        [resource.address]
    )
}

# Vietare security group con accesso SSH aperto a tutto il mondo
deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_security_group_rule"
    resource.change.after.from_port <= 22
    resource.change.after.to_port >= 22
    resource.change.after.cidr_blocks[_] == "0.0.0.0/0"

    msg := sprintf(
        "Security group rule '%s' permette SSH (porta 22) da 0.0.0.0/0. Restringere il CIDR.",
        [resource.address]
    )
}
```

---

## Checklist Competenze

Utilizza questa checklist per tracciare il tuo avanzamento nell'apprendimento. Ogni elemento corrisponde a una competenza verificabile attraverso i progetti pratici.

### Base

- [ ] Inizializzare un repository Git e fare il primo commit
- [ ] Creare e gestire branch (create, switch, delete)
- [ ] Eseguire merge e risolvere conflitti semplici
- [ ] Usare `.gitignore` correttamente per escludere file non necessari
- [ ] Creare un repository su GitHub e collegarlo al locale
- [ ] Aprire una Pull Request con descrizione chiara
- [ ] Eseguire code review e lasciare commenti costruttivi
- [ ] Usare le GitHub Issues per tracciare lavoro e bug
- [ ] Comprendere la differenza tra `fetch`, `pull` e `push`
- [ ] Usare `git log`, `git diff` e `git status` per ispezionare lo stato
- [ ] Creare un workflow GitHub Actions base (es. eseguire test su push)
- [ ] Comprendere la sintassi YAML per i workflow
- [ ] Usare i trigger `on: push` e `on: pull_request`

### Intermedio

- [ ] Configurare branch protection rules su `main`
- [ ] Implementare CODEOWNERS per review automatiche
- [ ] Creare issue templates e PR templates personalizzati
- [ ] Usare labels e milestones per organizzare il lavoro
- [ ] Scrivere workflow con job multipli e dipendenze (`needs`)
- [ ] Usare il caching nelle Actions per velocizzare i build
- [ ] Implementare matrix testing (versioni multiple di runtime)
- [ ] Configurare environments con variabili e segreti
- [ ] Usare `concurrency` per gestire esecuzioni parallele
- [ ] Implementare conventional commits e commitlint
- [ ] Generare changelog automatici con release-please
- [ ] Usare `gh` CLI per operazioni GitHub dalla riga di comando
- [ ] Configurare Dependabot per aggiornamenti automatici dipendenze
- [ ] Implementare workflow riutilizzabili (`workflow_call`)
- [ ] Usare gli artefatti (`upload-artifact` / `download-artifact`)

### Avanzato

- [ ] Gestire un monorepo con path-based triggers e build selettivi
- [ ] Implementare deploy progressivo (staging, approvazione, production)
- [ ] Configurare OIDC per autenticazione senza segreti statici verso cloud provider
- [ ] Implementare GitOps con Terraform (plan su PR, apply su merge)
- [ ] Scrivere policy as code con OPA/Conftest per validare infrastruttura
- [ ] Configurare drift detection programmato con creazione automatica di issue
- [ ] Implementare pipeline Docker multi-stage con push a GHCR
- [ ] Usare composite actions per creare azioni riutilizzabili personalizzate
- [ ] Configurare security scanning completo (CodeQL, Gitleaks, dependency review)
- [ ] Implementare un modello inner source con governance completa
- [ ] Gestire release multi-piattaforma (Docker multi-arch, npm, binari)
- [ ] Configurare GitHub Projects per tracking automatizzato del lavoro
- [ ] Implementare rollback automatico in caso di fallimento del deploy
- [ ] Usare `actions/github-script` per automazioni personalizzate avanzate
- [ ] Configurare self-hosted runners per esigenze specifiche

---

## Risorse per Esercitazione

### Repository di esempio da esplorare

- **github/docs** — Il repository della documentazione ufficiale GitHub. Ottimo esempio di CI/CD, contribuzione open source e automazione.
- **actions/starter-workflows** — Raccolta di workflow GitHub Actions pronti all'uso per diversi linguaggi e framework.
- **github/codeql-action** — Esempio di action complessa per l'analisi di sicurezza del codice.
- **release-please-action** — Automazione release con conventional commits. Studiare il codice sorgente per capire come funziona.
- **dorny/paths-filter** — Action per rilevare file modificati. Essenziale per monorepo e trigger selettivi.

### Documentazione ufficiale

- [GitHub Docs — Actions](https://docs.github.com/en/actions) — Riferimento completo per GitHub Actions con tutorial ed esempi.
- [GitHub Docs — REST API](https://docs.github.com/en/rest) — API REST per integrazioni programmatiche.
- [GitHub CLI Manual](https://cli.github.com/manual/) — Documentazione completa del comando `gh`.
- [Conventional Commits](https://www.conventionalcommits.org/it/) — Specifica dei conventional commits (disponibile in italiano).
- [Semantic Versioning](https://semver.org/lang/it/) — Specifica del semantic versioning (disponibile in italiano).

### Piattaforme di apprendimento

- **GitHub Skills** (https://skills.github.com) — Corsi interattivi ufficiali di GitHub che insegnano usando repository reali. Coprono Actions, Pages, CodeQL e molto altro.
- **The Odin Project** — Progetto open source con sezione dedicata a Git e GitHub per principianti.
- **Learn Git Branching** (https://learngitbranching.js.org) — Visualizzatore interattivo per comprendere branching e merging in modo intuitivo.

### Community e forum

- **GitHub Community Discussions** (https://github.com/orgs/community/discussions) — Forum ufficiale per domande su GitHub e Actions.
- **Stack Overflow** — Tag `github-actions`, `git`, `github` per domande tecniche specifiche.
- **Reddit r/github** — Community per discussioni generali su GitHub e workflow.
- **Dev.to** — Numerosi articoli pratici su GitHub Actions e CI/CD scritti dalla community.

---

## Best Practices Progetti

1. **Iniziare dal progetto piu semplice e procedere in ordine.** Ogni progetto costruisce competenze utilizzate nei successivi. Saltare i progetti base puo creare lacune difficili da colmare.

2. **Creare un repository dedicato per ogni progetto.** Non mescolare i progetti in un unico repository. Avere repository separati permette di sperimentare liberamente senza paura di compromettere il lavoro precedente.

3. **Fare commit frequenti e descrittivi seguendo i conventional commits.** Fin dal primo progetto, adottare conventional commits come abitudine. La disciplina nei messaggi di commit e una competenza professionale fondamentale.

4. **Leggere i log delle Actions quando un workflow fallisce.** Non limitarsi a rieseguire il workflow: analizzare il log completo, comprendere l'errore e correggerlo consapevolmente. Questo e il modo migliore per imparare.

5. **Sperimentare con le variazioni.** Dopo aver completato un progetto, provare a modificarlo: aggiungere un nuovo job, cambiare il trigger, usare un'action diversa. L'esplorazione attiva consolida la comprensione.

6. **Documentare le decisioni prese.** Per ogni configurazione, annotare il motivo della scelta. Perche quel valore di timeout? Perche quel livello di severita per il security scan? La documentazione delle decisioni e preziosa per il futuro.

7. **Usare branch separati per ogni esperimento.** Prima di modificare un workflow funzionante, creare un branch di test. Questo permette di sperimentare senza rischiare di rompere la pipeline principale.

8. **Verificare i costi delle Actions.** GitHub Actions offre un generoso piano gratuito, ma i minuti sono limitati. Monitorare l'utilizzo nella sezione Billing del proprio account, soprattutto quando si usano matrix testing e workflow frequenti.

9. **Implementare sempre un meccanismo di notifica.** Che sia Slack, email o una issue automatica, assicurarsi di essere notificati quando qualcosa fallisce. Una pipeline che fallisce silenziosamente e peggio di nessuna pipeline.

10. **Rivedere periodicamente le configurazioni.** Le Actions vengono aggiornate regolarmente. Controllare le versioni delle actions utilizzate, aggiornare i workflow e rimuovere le configurazioni obsolete. Dependabot puo automatizzare questo processo.

11. **Mantenere i workflow DRY (Don't Repeat Yourself).** Quando la stessa logica appare in piu workflow, estrarre il codice comune in composite actions o workflow riutilizzabili con `workflow_call`. La duplicazione nei workflow e una fonte comune di errori.

12. **Testare i workflow in un fork prima di applicarli al repository principale.** Per workflow critici (deploy, release), creare un fork del repository e testare la pipeline completa prima di integrarla nel progetto reale. Questo evita errori costosi in produzione.

---

## Esercizi

### Esercizio 1: Setup Repository Team da Zero

```bash
# Obiettivo: creare un repository team production-ready in 30 minuti

# 1. Creare il repository con struttura completa:
gh repo create my-team-project --public --clone
cd my-team-project

# 2. Creare la struttura di file governance:
mkdir -p .github/ISSUE_TEMPLATE .github/workflows

cat > .github/ISSUE_TEMPLATE/bug_report.yml << 'YAML'
name: Bug Report
description: Report a bug
labels: ["bug", "triage"]
body:
  - type: textarea
    id: description
    attributes:
      label: Bug Description
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
    validations:
      required: true
  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options: ["Critical", "High", "Medium", "Low"]
YAML

# 3. Creare CODEOWNERS e CONTRIBUTING.md
# 4. Configurare branch protection (vedi Esercizio 2 del modulo 03)
# 5. Aggiungere label personalizzate:
gh label create "priority:critical" --color "B60205" --description "Richiede fix immediato"
gh label create "priority:high" --color "D93F0B"
gh label create "priority:medium" --color "FBCA04"
gh label create "priority:low" --color "0E8A16"

# 6. Creare un project board collegato:
gh project create --title "Sprint Board" --owner @me

# Verifica: il repo deve avere template, protection, labels e project configurati
```

### Esercizio 2: Pipeline CI/CD End-to-End

```yaml
# Obiettivo: costruire una pipeline completa test → build → deploy

# File: .github/workflows/pipeline.yml
name: Full Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  checks: write
  deployments: write

concurrency:
  group: pipeline-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/
      - run: echo "Deploying to staging..."

# Compiti:
# 1. Aggiungere un job deploy-production con needs: [deploy-staging]
# 2. Aggiungere smoke test dopo il deploy staging
# 3. Configurare notifica Slack su fallimento
# 4. Aggiungere badge CI nel README
```

### Esercizio 3: Automazione Release con Semantic Versioning

```yaml
# Obiettivo: automatizzare release con tag, changelog e GitHub Release

# File: .github/workflows/release.yml
name: Release
on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate Changelog
        id: changelog
        run: |
          PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
          if [ -n "$PREV_TAG" ]; then
            CHANGES=$(git log ${PREV_TAG}..HEAD --pretty=format:"- %s (%h)" --no-merges)
          else
            CHANGES=$(git log --pretty=format:"- %s (%h)" --no-merges)
          fi
          echo "changes<<EOF" >> $GITHUB_OUTPUT
          echo "$CHANGES" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body: |
            ## Changelog
            ${{ steps.changelog.outputs.changes }}
          generate_release_notes: true

# Compiti:
# 1. Testare creando tag: git tag v1.0.0 && git push origin v1.0.0
# 2. Aggiungere build step che genera artifact da allegare alla release
# 3. Implementare un workflow che crea il tag automaticamente basato su conventional commits
# 4. Aggiungere validazione che il tag segua semantic versioning
```

### Esercizio 4: Monorepo con Path Filtering

```yaml
# Obiettivo: configurare CI selettiva per monorepo

# File: .github/workflows/monorepo-ci.yml
name: Monorepo CI
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read
  pull-requests: read

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      shared: ${{ steps.filter.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            frontend:
              - 'apps/frontend/**'
            backend:
              - 'apps/backend/**'
            shared:
              - 'libs/shared/**'

  test-frontend:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true' || needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Running frontend tests..."

  test-backend:
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true' || needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Running backend tests..."

# Compiti:
# 1. Creare la struttura monorepo: apps/frontend, apps/backend, libs/shared
# 2. Aggiungere test e build specifici per ogni area
# 3. Aggiungere un job di deploy condizionale per ogni servizio
# 4. Configurare CODEOWNERS per area
# 5. Verificare che modifiche a libs/shared/ triggerino entrambi i test
```

### Esercizio 5: Security Scanning Pipeline

```yaml
# Obiettivo: implementare security scanning integrato nel CI

# File: .github/workflows/security.yml
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedì alle 06:00 UTC

permissions:
  contents: read
  security-events: write

jobs:
  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
        continue-on-error: true
      - run: npm audit --json > audit-report.json || true
      - uses: actions/upload-artifact@v4
        with:
          name: npm-audit
          path: audit-report.json

  codeql-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:javascript"

  secret-scanning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

# Compiti:
# 1. Abilitare Dependabot per il repository (Settings → Code security)
# 2. Configurare dependabot.yml per aggiornamenti settimanali
# 3. Aggiungere SAST con semgrep o altro scanner
# 4. Configurare notifiche per vulnerabilità critiche
# 5. Creare una policy: bloccare merge se security scan fallisce
```

---

## Progetto 7: Contribuzione Open Source — Fork Workflow Completo

### Obiettivo

Padroneggiare il workflow completo di contribuzione a progetti open source: fork, clone, branch, sviluppo, test, pull request e gestione del feedback dei maintainer. Questo progetto simula uno scenario reale di contribuzione a un repository esterno, documentando ogni passaggio critico.

### Contesto e motivazione

La contribuzione open source rappresenta una delle competenze piu richieste nel mercato del lavoro IT. Circa il 75% dei recruiter valuta il profilo GitHub prima ancora di leggere il curriculum. Un portfolio che mostra contribuzioni reali a progetti open source dimostra capacita di collaborazione, comprensione di codebase altrui e padronanza dei workflow Git professionali.

Questo progetto e strutturato come una simulazione completa: si utilizza un repository pubblico reale (o un repository di pratica creato ad hoc) per attraversare tutte le fasi del processo di contribuzione.

### Passo 1 — Identificare il progetto e la issue

Prima di contribuire, occorre identificare un progetto adatto e una issue etichettata come `good first issue` o `help wanted`.

```bash
# Cercare repository con issue accessibili ai nuovi contributori
gh search repos --language=javascript --topic=hacktoberfest --sort=stars --limit=10

# Cercare issue con label specifiche in un repository target
gh search issues --repo=facebook/react --label="good first issue" --state=open --limit=20

# Leggere i dettagli di una issue specifica
gh issue view 12345 --repo=facebook/react

# Verificare che nessuno stia gia lavorando sulla issue
# Controllare i commenti e la presenza di PR collegate
gh issue view 12345 --repo=facebook/react --comments
```

Prima di iniziare a scrivere codice, e fondamentale leggere attentamente i seguenti file del progetto:

- **README.md** — Per comprendere lo scopo e l'architettura del progetto
- **CONTRIBUTING.md** — Per conoscere le convenzioni di stile, i requisiti per le PR e il processo di review
- **CODE_OF_CONDUCT.md** — Per comprendere le aspettative comportamentali della community
- **.github/pull_request_template.md** — Per sapere quali informazioni includere nella PR

### Passo 2 — Fork e configurazione locale

```bash
# Creare il fork del repository su GitHub
gh repo fork facebook/react --clone

cd react

# Verificare i remote configurati
git remote -v
# origin    https://github.com/TUO-USERNAME/react.git (fetch)
# origin    https://github.com/TUO-USERNAME/react.git (push)
# upstream  https://github.com/facebook/react.git (fetch)
# upstream  https://github.com/facebook/react.git (push)

# Se il remote upstream non e stato configurato automaticamente
git remote add upstream https://github.com/facebook/react.git

# Sincronizzare il fork con il repository originale
git fetch upstream
git checkout main
git merge upstream/main

# Installare le dipendenze seguendo le istruzioni del progetto
npm ci
# oppure
yarn install --frozen-lockfile
```

### Passo 3 — Creare un branch dedicato

```bash
# Creare un branch con un nome descrittivo
# Convenzione: tipo/descrizione-breve
git checkout -b fix/spelling-error-in-readme

# Oppure riferito alla issue
git checkout -b fix/issue-12345-validation-error

# Verificare di essere sul branch corretto
git branch --show-current
```

Regole per il naming dei branch:
- Usare prefissi chiari: `fix/`, `feat/`, `docs/`, `refactor/`, `test/`
- Includere il numero della issue quando possibile
- Usare kebab-case
- Mantenere il nome corto ma descrittivo

### Passo 4 — Implementare le modifiche

```bash
# Lavorare sulle modifiche seguendo le convenzioni del progetto
# Esempio: correggere un bug di validazione

# Verificare lo stato delle modifiche
git status

# Aggiungere i file modificati (mai usare git add . senza prima verificare)
git diff --stat
git add src/validation/inputValidator.js
git add tests/validation/inputValidator.test.js

# Commit con messaggio convenzionale e riferimento alla issue
git commit -m "fix: correct input validation for empty strings

The validator was not handling empty strings correctly,
causing a TypeError when users submitted blank form fields.

Added unit tests to cover edge cases.

Closes #12345"
```

### Passo 5 — Sincronizzare e risolvere conflitti

Prima di aprire la PR, e fondamentale sincronizzare il branch con upstream per evitare conflitti.

```bash
# Aggiornare il branch main dal repository originale
git fetch upstream
git checkout main
git merge upstream/main

# Tornare sul branch di lavoro e fare rebase
git checkout fix/issue-12345-validation-error
git rebase main

# Se ci sono conflitti durante il rebase:
# 1. Aprire i file con conflitti e risolverli manualmente
# 2. git add <file-risolto>
# 3. git rebase --continue
# 4. Ripetere fino al completamento

# Verificare che i test passino dopo il rebase
npm test

# Push del branch al fork
git push origin fix/issue-12345-validation-error
```

### Passo 6 — Aprire la Pull Request

```bash
# Creare la PR con gh CLI
gh pr create \
  --repo facebook/react \
  --title "fix: correct input validation for empty strings" \
  --body "$(cat <<'EOF'
## Descrizione

Corregge il bug di validazione per stringhe vuote che causava un TypeError
quando gli utenti inviavano campi form vuoti.

## Modifiche

- Aggiunto controllo per stringhe vuote in `inputValidator.js`
- Aggiunto fallback a stringa vuota per input `null` o `undefined`
- Aggiunti 4 test unitari per coprire i casi edge

## Issue collegata

Closes #12345

## Checklist

- [x] Ho letto CONTRIBUTING.md
- [x] Il codice segue le convenzioni di stile del progetto
- [x] Ho aggiunto test che coprono le modifiche
- [x] Tutti i test esistenti passano
- [x] Ho aggiornato la documentazione (se necessario)

## Screenshot

N/A (modifica solo backend/logica)
EOF
)"
```

### Passo 7 — Gestire il feedback dei maintainer

Dopo l'apertura della PR, i maintainer possono richiedere modifiche. Ecco come gestire il ciclo di review:

```bash
# Leggere i commenti sulla PR
gh pr view 67890 --repo facebook/react --comments

# Applicare le modifiche richieste
git checkout fix/issue-12345-validation-error

# Fare le modifiche richieste dai reviewer
# ...editing...

# Commit delle modifiche con riferimento alla review
git add src/validation/inputValidator.js
git commit -m "fix: address review feedback — use optional chaining

Replaced null check with optional chaining as suggested by @reviewer.
Also simplified the early return logic."

# Push delle modifiche (il push aggiorna automaticamente la PR)
git push origin fix/issue-12345-validation-error

# Rispondere ai commenti sulla PR
gh pr comment 67890 --repo facebook/react \
  --body "Ho applicato le modifiche richieste. In particolare:
- Sostituito il null check con optional chaining
- Semplificata la logica di early return
Grazie per il feedback!"
```

### Passo 8 — Post-merge: pulizia e sincronizzazione

```bash
# Dopo il merge della PR, sincronizzare il fork
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# Eliminare il branch di lavoro localmente e sul fork
git branch -d fix/issue-12345-validation-error
git push origin --delete fix/issue-12345-validation-error

# Verificare che il fork sia pulito e sincronizzato
git log --oneline -5
```

### Errori comuni da evitare

1. **Non leggere CONTRIBUTING.md** — Ogni progetto ha convenzioni diverse. Ignorarle garantisce il rifiuto della PR.
2. **PR troppo grandi** — Le PR con centinaia di righe modificate sono difficili da revisionare. Mantenere le PR piccole e focalizzate.
3. **Force push durante la review** — Non fare `git push --force` dopo che la review e iniziata: i reviewer perdono il contesto dei commenti.
4. **Non testare dopo il rebase** — Il rebase puo introdurre regressioni. Eseguire sempre la suite di test dopo il rebase.
5. **Ignorare la CI** — Se la CI fallisce, correggere prima di chiedere una review.
6. **Commit monolitici** — Preferire commit piccoli e atomici con messaggi chiari.

---

## Progetto 8: Composite Actions e Workflow Riutilizzabili

### Obiettivo

Creare una libreria di azioni composite e workflow riutilizzabili per eliminare la duplicazione tra i workflow CI/CD di piu repository. Questo progetto insegna a progettare azioni modulari, versionarle correttamente e distribuirle nell'organizzazione.

### Contesto architetturale

Le composite actions sono azioni personalizzate scritte interamente in YAML che eseguono piu step all'interno di un singolo step del workflow chiamante. A differenza delle JavaScript actions o Docker actions, le composite actions girano direttamente nel runner senza overhead aggiuntivo. I workflow riutilizzabili (`workflow_call`) invece permettono di riutilizzare interi workflow con piu job.

La differenza chiave:
- **Composite actions** — Raggruppano piu step in uno solo. Ideali per procedure di setup, build step o logica di deploy condivisa.
- **Workflow riutilizzabili** — Riutilizzano workflow interi con piu job. Ideali per pipeline CI/CD complete, workflow multi-job e processi di deployment complessi.

Regola pratica: usare composite actions quando serve riutilizzare una sequenza di step all'interno di un job; usare workflow riutilizzabili quando serve riutilizzare un intero job o un insieme di job.

### Passo 1 — Struttura del repository per azioni condivise

```
shared-actions/
├── actions/
│   ├── setup-node-cached/
│   │   └── action.yml
│   ├── docker-build-push/
│   │   └── action.yml
│   ├── slack-notify/
│   │   └── action.yml
│   ├── terraform-plan/
│   │   └── action.yml
│   └── security-scan/
│       └── action.yml
├── workflows/
│   ├── ci-node.yml
│   ├── ci-python.yml
│   ├── cd-docker.yml
│   └── security-audit.yml
├── CHANGELOG.md
├── README.md
└── .github/
    └── workflows/
        └── test-actions.yml
```

### Passo 2 — Creare una composite action: setup-node-cached

Questa action standardizza il setup di Node.js con caching ottimizzato, installazione dipendenze e verifica dell'ambiente.

```yaml
# actions/setup-node-cached/action.yml
name: "Setup Node.js con Cache"
description: "Configura Node.js con caching npm/pnpm, installa dipendenze e verifica l'ambiente"

inputs:
  node-version:
    description: "Versione di Node.js da installare"
    required: false
    default: "22"
  package-manager:
    description: "Package manager da utilizzare (npm, pnpm, yarn)"
    required: false
    default: "npm"
  working-directory:
    description: "Directory di lavoro per l'installazione"
    required: false
    default: "."
  install-command:
    description: "Comando personalizzato per installare le dipendenze"
    required: false
    default: ""

outputs:
  node-version:
    description: "Versione effettiva di Node.js installata"
    value: ${{ steps.node-info.outputs.version }}
  cache-hit:
    description: "Se la cache delle dipendenze e stata trovata"
    value: ${{ steps.cache-deps.outputs.cache-hit }}

runs:
  using: "composite"
  steps:
    - name: Setup Node.js ${{ inputs.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}

    - name: Setup pnpm (se richiesto)
      if: inputs.package-manager == 'pnpm'
      uses: pnpm/action-setup@v4
      with:
        version: latest

    - name: Ottenere directory cache
      id: cache-dir
      shell: bash
      run: |
        if [ "${{ inputs.package-manager }}" = "pnpm" ]; then
          echo "dir=$(pnpm store path)" >> "$GITHUB_OUTPUT"
        elif [ "${{ inputs.package-manager }}" = "yarn" ]; then
          echo "dir=$(yarn cache dir)" >> "$GITHUB_OUTPUT"
        else
          echo "dir=$(npm config get cache)" >> "$GITHUB_OUTPUT"
        fi

    - name: Cache dipendenze
      id: cache-deps
      uses: actions/cache@v4
      with:
        path: ${{ steps.cache-dir.outputs.dir }}
        key: ${{ runner.os }}-${{ inputs.package-manager }}-${{ hashFiles('**/package-lock.json', '**/pnpm-lock.yaml', '**/yarn.lock') }}
        restore-keys: |
          ${{ runner.os }}-${{ inputs.package-manager }}-

    - name: Installare dipendenze
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: |
        if [ -n "${{ inputs.install-command }}" ]; then
          ${{ inputs.install-command }}
        elif [ "${{ inputs.package-manager }}" = "pnpm" ]; then
          pnpm install --frozen-lockfile
        elif [ "${{ inputs.package-manager }}" = "yarn" ]; then
          yarn install --frozen-lockfile
        else
          npm ci
        fi

    - name: Informazioni Node.js
      id: node-info
      shell: bash
      run: |
        echo "version=$(node --version)" >> "$GITHUB_OUTPUT"
        echo "Node.js: $(node --version)"
        echo "npm: $(npm --version)"
        if command -v pnpm &> /dev/null; then echo "pnpm: $(pnpm --version)"; fi
```

### Passo 3 — Creare una composite action: docker-build-push

```yaml
# actions/docker-build-push/action.yml
name: "Docker Build e Push"
description: "Build multi-platform e push a container registry con caching e metadata"

inputs:
  registry:
    description: "Container registry (ghcr.io, docker.io, ecr)"
    required: false
    default: "ghcr.io"
  image-name:
    description: "Nome dell'immagine (default: github.repository)"
    required: false
    default: ""
  dockerfile:
    description: "Percorso al Dockerfile"
    required: false
    default: "Dockerfile"
  context:
    description: "Contesto di build Docker"
    required: false
    default: "."
  platforms:
    description: "Piattaforme target (separati da virgola)"
    required: false
    default: "linux/amd64,linux/arm64"
  push:
    description: "Se pushare l'immagine al registry"
    required: false
    default: "true"
  build-args:
    description: "Build arguments (uno per riga)"
    required: false
    default: ""
  github-token:
    description: "Token per autenticazione GHCR"
    required: true

outputs:
  image-digest:
    description: "Digest dell'immagine"
    value: ${{ steps.build.outputs.digest }}
  image-tags:
    description: "Tag applicati all'immagine"
    value: ${{ steps.meta.outputs.tags }}
  image-version:
    description: "Versione principale dell'immagine"
    value: ${{ steps.meta.outputs.version }}

runs:
  using: "composite"
  steps:
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Setup QEMU per multi-platform
      uses: docker/setup-qemu-action@v3
      with:
        platforms: ${{ inputs.platforms }}

    - name: Login al container registry
      uses: docker/login-action@v3
      with:
        registry: ${{ inputs.registry }}
        username: ${{ github.actor }}
        password: ${{ inputs.github-token }}

    - name: Estrarre metadata Docker
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ inputs.registry }}/${{ inputs.image-name || github.repository }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix=,format=short
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build e push immagine
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
        build-args: ${{ inputs.build-args }}
        provenance: true
        sbom: true

    - name: Riepilogo immagine
      shell: bash
      run: |
        echo "### Docker Image Build Summary" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "| Proprieta | Valore |" >> $GITHUB_STEP_SUMMARY
        echo "|-----------|--------|" >> $GITHUB_STEP_SUMMARY
        echo "| **Digest** | \`${{ steps.build.outputs.digest }}\` |" >> $GITHUB_STEP_SUMMARY
        echo "| **Piattaforme** | ${{ inputs.platforms }} |" >> $GITHUB_STEP_SUMMARY
        echo "| **Push** | ${{ inputs.push }} |" >> $GITHUB_STEP_SUMMARY
```

### Passo 4 — Creare un workflow riutilizzabile: CI Node.js

```yaml
# workflows/ci-node.yml
name: CI Node.js Riutilizzabile

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: "22"
        description: "Versione di Node.js"
      package-manager:
        type: string
        default: "npm"
        description: "Package manager (npm, pnpm, yarn)"
      working-directory:
        type: string
        default: "."
        description: "Directory di lavoro"
      run-lint:
        type: boolean
        default: true
        description: "Eseguire il linting"
      run-typecheck:
        type: boolean
        default: true
        description: "Eseguire il type checking"
      run-tests:
        type: boolean
        default: true
        description: "Eseguire i test"
      coverage-threshold:
        type: number
        default: 80
        description: "Soglia minima di copertura test (%)"
    secrets:
      CODECOV_TOKEN:
        required: false
        description: "Token per upload coverage a Codecov"

    outputs:
      test-result:
        description: "Risultato dei test (success/failure)"
        value: ${{ jobs.test.result }}
      coverage-percentage:
        description: "Percentuale di copertura test"
        value: ${{ jobs.test.outputs.coverage }}

jobs:
  lint:
    name: "Lint e Format"
    runs-on: ubuntu-latest
    if: ${{ inputs.run-lint }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup ambiente
        uses: ./actions/setup-node-cached
        with:
          node-version: ${{ inputs.node-version }}
          package-manager: ${{ inputs.package-manager }}
          working-directory: ${{ inputs.working-directory }}

      - name: Eseguire ESLint
        run: ${{ inputs.package-manager }} run lint

      - name: Verificare formattazione
        run: ${{ inputs.package-manager }} run format:check
        continue-on-error: true

  typecheck:
    name: "Type Check"
    runs-on: ubuntu-latest
    if: ${{ inputs.run-typecheck }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup ambiente
        uses: ./actions/setup-node-cached
        with:
          node-version: ${{ inputs.node-version }}
          package-manager: ${{ inputs.package-manager }}
          working-directory: ${{ inputs.working-directory }}

      - name: Eseguire TypeScript compiler
        run: ${{ inputs.package-manager }} run typecheck

  test:
    name: "Test e Coverage"
    runs-on: ubuntu-latest
    if: ${{ inputs.run-tests }}
    outputs:
      coverage: ${{ steps.coverage.outputs.percentage }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - name: Checkout codice
        uses: actions/checkout@v4

      - name: Setup ambiente
        uses: ./actions/setup-node-cached
        with:
          node-version: ${{ inputs.node-version }}
          package-manager: ${{ inputs.package-manager }}
          working-directory: ${{ inputs.working-directory }}

      - name: Eseguire test con coverage
        run: ${{ inputs.package-manager }} run test:coverage

      - name: Estrarre percentuale coverage
        id: coverage
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | \
            jq '.total.lines.pct')
          echo "percentage=$COVERAGE" >> "$GITHUB_OUTPUT"
          echo "Copertura: $COVERAGE%"

      - name: Verificare soglia di copertura
        run: |
          COVERAGE=${{ steps.coverage.outputs.percentage }}
          THRESHOLD=${{ inputs.coverage-threshold }}
          if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
            echo "::error::Copertura test ($COVERAGE%) sotto la soglia minima ($THRESHOLD%)"
            exit 1
          fi
          echo "Copertura test ($COVERAGE%) sopra la soglia ($THRESHOLD%)"

      - name: Upload coverage a Codecov
        if: ${{ secrets.CODECOV_TOKEN != '' }}
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info
          fail_ci_if_error: false
```

### Passo 5 — Utilizzare le azioni e i workflow riutilizzabili

Esempio di un workflow chiamante in un repository applicativo che sfrutta sia le composite actions che il workflow riutilizzabile:

```yaml
# In un repository applicativo: .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # Utilizzare il workflow riutilizzabile dal repository condiviso
  ci:
    uses: org/shared-actions/.github/workflows/ci-node.yml@v2.1.0
    with:
      node-version: "22"
      package-manager: "pnpm"
      coverage-threshold: 85
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  # Job aggiuntivo che usa la composite action direttamente
  docker:
    needs: ci
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Build e push Docker
        uses: org/shared-actions/actions/docker-build-push@v2.1.0
        with:
          registry: ghcr.io
          platforms: "linux/amd64,linux/arm64"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Passo 6 — Versionamento delle azioni condivise

Il versionamento e critico per la sicurezza e la stabilita. Seguire queste regole:

```bash
# Creare un tag semantico per ogni release delle azioni
git tag -a v2.1.0 -m "feat: aggiunta azione security-scan, migliorato caching docker"
git push origin v2.1.0

# Aggiornare il tag major per compatibilita (i consumatori usano @v2)
git tag -fa v2 -m "Update v2 tag to v2.1.0"
git push origin v2 --force

# Creare una GitHub Release
gh release create v2.1.0 \
  --title "v2.1.0 — Security Scan Action" \
  --notes "$(cat <<'EOF'
## Novita
- Aggiunta composite action `security-scan` con Trivy e Gitleaks
- Migliorato caching Docker con supporto GHA cache backend
- Aggiunto supporto per pnpm nell'action `setup-node-cached`

## Aggiornamenti
- docker/build-push-action aggiornata a v6
- actions/cache aggiornata a v4

## Breaking Changes
Nessuno. Compatibile con v2.0.x.
EOF
)"
```

**Regola di sicurezza critica**: i consumatori delle azioni dovrebbero sempre pinnare al commit SHA completo per protezione dalla supply chain, non al tag:

```yaml
# SICURO: pinnato al SHA del commit
- uses: org/shared-actions/actions/setup-node-cached@a1b2c3d4e5f6789012345678

# MENO SICURO: pinnato al tag (il tag puo essere spostato)
- uses: org/shared-actions/actions/setup-node-cached@v2.1.0
```

### Testare le azioni prima del rilascio

```yaml
# .github/workflows/test-actions.yml — nel repository delle azioni condivise
name: Test Composite Actions

on:
  pull_request:
    paths:
      - 'actions/**'
  push:
    branches: [main]
    paths:
      - 'actions/**'

jobs:
  test-setup-node:
    name: "Test setup-node-cached"
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [18, 20, 22]
        pm: [npm, pnpm, yarn]
    steps:
      - uses: actions/checkout@v4

      - name: Testare l'azione setup-node-cached
        uses: ./actions/setup-node-cached
        with:
          node-version: ${{ matrix.node }}
          package-manager: ${{ matrix.pm }}

      - name: Verificare installazione
        run: |
          node --version
          echo "Setup completato con Node ${{ matrix.node }} e ${{ matrix.pm }}"

  test-docker-build:
    name: "Test docker-build-push"
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4

      # Creare un Dockerfile di test
      - name: Creare Dockerfile di test
        run: |
          cat > Dockerfile <<'DOCKER'
          FROM node:22-alpine
          WORKDIR /app
          COPY package*.json ./
          RUN npm ci --production
          COPY . .
          CMD ["node", "index.js"]
          DOCKER
          echo '{"name":"test","version":"0.0.1"}' > package.json
          echo 'console.log("test")' > index.js

      - name: Testare l'azione docker-build-push
        uses: ./actions/docker-build-push
        with:
          registry: ghcr.io
          platforms: "linux/amd64"
          push: "false"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Progetto 9: Deploy con Strategie Blue-Green e Canary

### Obiettivo

Implementare strategie di deploy avanzate (blue-green e canary) con GitHub Actions, includendo rollback automatico basato su metriche, smoke test post-deploy e gestione del traffico progressiva. Questo progetto prepara a scenari di deploy zero-downtime in produzione.

### Architettura del deploy blue-green

Il deploy blue-green mantiene due ambienti di produzione identici. In ogni momento, solo uno (il "blue") serve traffico reale. Quando si effettua un deploy, si aggiorna l'ambiente inattivo (il "green"), si eseguono test approfonditi e solo dopo si sposta il traffico. In caso di problemi, il rollback e istantaneo: basta riportare il traffico all'ambiente precedente.

```
Utenti → Load Balancer → [Blue: v1.2.0] (attivo)
                        → [Green: v1.3.0] (standby, in fase di test)

Dopo la validazione:
Utenti → Load Balancer → [Green: v1.3.0] (ora attivo)
                        → [Blue: v1.2.0] (ora standby per rollback)
```

### Passo 1 — Workflow Blue-Green Deploy

```yaml
# .github/workflows/blue-green-deploy.yml
name: Blue-Green Deploy

on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - '*.md'

permissions:
  contents: read
  deployments: write

env:
  APP_NAME: "my-web-app"
  HEALTH_ENDPOINT: "/api/health"
  SMOKE_TEST_TIMEOUT: 120

jobs:
  build:
    name: "Build Artefatti"
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.tag }}
      artifact-name: ${{ steps.version.outputs.artifact }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Determinare versione
        id: version
        run: |
          VERSION=$(git describe --tags --always --dirty)
          echo "tag=$VERSION" >> "$GITHUB_OUTPUT"
          echo "artifact=build-$VERSION" >> "$GITHUB_OUTPUT"
          echo "Versione: $VERSION"

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - run: npm ci
      - run: npm run build

      - name: Upload artefatti
        uses: actions/upload-artifact@v4
        with:
          name: build-${{ steps.version.outputs.tag }}
          path: dist/
          retention-days: 14

  identify-target:
    name: "Identificare ambiente target"
    runs-on: ubuntu-latest
    needs: build
    outputs:
      active: ${{ steps.identify.outputs.active }}
      target: ${{ steps.identify.outputs.target }}
    steps:
      - name: Determinare ambiente attivo e target
        id: identify
        run: |
          # Interrogare il load balancer o il DNS per determinare
          # quale ambiente e attualmente attivo
          # Esempio con AWS:
          # ACTIVE=$(aws elbv2 describe-target-groups ... | jq ...)
          
          # Per simulazione:
          ACTIVE="blue"
          if [ "$ACTIVE" = "blue" ]; then
            TARGET="green"
          else
            TARGET="blue"
          fi
          echo "active=$ACTIVE" >> "$GITHUB_OUTPUT"
          echo "target=$TARGET" >> "$GITHUB_OUTPUT"
          echo "Ambiente attivo: $ACTIVE, Target deploy: $TARGET"

  deploy-target:
    name: "Deploy a ${{ needs.identify-target.outputs.target }}"
    runs-on: ubuntu-latest
    needs: [build, identify-target]
    environment:
      name: ${{ needs.identify-target.outputs.target }}
    steps:
      - uses: actions/checkout@v4

      - name: Scaricare artefatti
        uses: actions/download-artifact@v4
        with:
          name: ${{ needs.build.outputs.artifact-name }}
          path: dist/

      - name: Deploy all'ambiente target
        env:
          TARGET: ${{ needs.identify-target.outputs.target }}
          VERSION: ${{ needs.build.outputs.version }}
        run: |
          echo "Deploying versione $VERSION all'ambiente $TARGET..."
          # Esempio con AWS ECS:
          # aws ecs update-service \
          #   --cluster production \
          #   --service "${APP_NAME}-${TARGET}" \
          #   --force-new-deployment
          
          # Esempio con Kubernetes:
          # kubectl set image deployment/${APP_NAME}-${TARGET} \
          #   app=ghcr.io/${GITHUB_REPOSITORY}:${VERSION}

      - name: Attendere stabilizzazione
        run: |
          echo "Attendendo che l'ambiente ${{ needs.identify-target.outputs.target }} sia stabile..."
          # Esempio: attendere che il deployment Kubernetes sia completo
          # kubectl rollout status deployment/${APP_NAME}-${TARGET} --timeout=300s
          sleep 30

  validate-target:
    name: "Validare ambiente target"
    runs-on: ubuntu-latest
    needs: [identify-target, deploy-target]
    outputs:
      validation-passed: ${{ steps.validate.outputs.passed }}
    steps:
      - name: Smoke test
        id: smoke
        run: |
          TARGET_URL="https://${{ needs.identify-target.outputs.target }}.esempio.com"
          echo "Eseguendo smoke test su $TARGET_URL..."
          
          # Test 1: Health check
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            "${TARGET_URL}${{ env.HEALTH_ENDPOINT }}" \
            --max-time 10 --retry 3 --retry-delay 5)
          
          if [ "$HTTP_CODE" != "200" ]; then
            echo "::error::Health check fallito: HTTP $HTTP_CODE"
            echo "passed=false" >> "$GITHUB_OUTPUT"
            exit 1
          fi
          
          # Test 2: Verifica versione
          DEPLOYED_VERSION=$(curl -s "${TARGET_URL}/api/version" | jq -r '.version')
          echo "Versione deployata: $DEPLOYED_VERSION"
          
          # Test 3: Latenza accettabile
          LATENCY=$(curl -s -o /dev/null -w "%{time_total}" "${TARGET_URL}/")
          echo "Latenza: ${LATENCY}s"
          
          if (( $(echo "$LATENCY > 2.0" | bc -l) )); then
            echo "::warning::Latenza elevata: ${LATENCY}s (soglia: 2.0s)"
          fi
          
          echo "passed=true" >> "$GITHUB_OUTPUT"
          echo "Tutti gli smoke test superati."

      - name: Risultato validazione
        id: validate
        run: echo "passed=${{ steps.smoke.outputs.passed }}" >> "$GITHUB_OUTPUT"

  switch-traffic:
    name: "Switch traffico a ${{ needs.identify-target.outputs.target }}"
    runs-on: ubuntu-latest
    needs: [identify-target, validate-target]
    if: ${{ needs.validate-target.outputs.validation-passed == 'true' }}
    environment:
      name: production
      url: https://www.esempio.com
    steps:
      - name: Spostare traffico all'ambiente target
        env:
          TARGET: ${{ needs.identify-target.outputs.target }}
        run: |
          echo "Spostando il traffico di produzione a $TARGET..."
          # Esempio con AWS Route53:
          # aws route53 change-resource-record-sets \
          #   --hosted-zone-id ZONE_ID \
          #   --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{...}}]}'
          
          # Esempio con Nginx:
          # ssh deploy@lb "sudo ln -sf /etc/nginx/upstream-${TARGET}.conf /etc/nginx/upstream-active.conf && sudo nginx -s reload"

      - name: Verifica post-switch
        run: |
          echo "Verificando che il traffico sia instradato correttamente..."
          sleep 10
          # curl --fail https://www.esempio.com/api/health

      - name: Annotare deployment
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.repos.createDeploymentStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              deployment_id: context.payload.deployment?.id || 0,
              state: 'success',
              description: 'Blue-green deploy completato',
              environment_url: 'https://www.esempio.com'
            });

  rollback:
    name: "Rollback automatico"
    runs-on: ubuntu-latest
    needs: [identify-target, validate-target]
    if: ${{ needs.validate-target.outputs.validation-passed != 'true' }}
    steps:
      - name: Rollback all'ambiente precedente
        env:
          ACTIVE: ${{ needs.identify-target.outputs.active }}
          TARGET: ${{ needs.identify-target.outputs.target }}
        run: |
          echo "::error::Validazione fallita! Rollback in corso..."
          echo "Riportando il traffico a $ACTIVE (annullando deploy su $TARGET)"
          # Il rollback e istantaneo perche l'ambiente blue/green
          # precedente e ancora attivo e funzionante
          
          # Opzionale: scalare a zero l'ambiente target fallito
          # kubectl scale deployment/${APP_NAME}-${TARGET} --replicas=0

      - name: Creare issue per il fallimento
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Deploy fallito — Rollback eseguito (${new Date().toISOString().split('T')[0]})`,
              body: `## Deploy Blue-Green Fallito\n\n**Commit:** ${context.sha}\n**Ambiente target:** ${{ needs.identify-target.outputs.target }}\n**Motivo:** Validazione post-deploy fallita\n\n### Azione\nIl traffico e rimasto sull'ambiente ${{ needs.identify-target.outputs.active }}.\nIndagare la causa del fallimento prima del prossimo deploy.`,
              labels: ['deploy-failure', 'priority: high']
            });

      - name: Notifica fallimento
        run: |
          echo "::error::Deploy blue-green fallito. Rollback completato."
          echo "Ambiente attivo confermato: ${{ needs.identify-target.outputs.active }}"
```

### Passo 2 — Workflow Canary Deploy

Il deploy canary e piu graduale del blue-green: instrada progressivamente una percentuale crescente di traffico alla nuova versione, monitorando le metriche ad ogni step.

```yaml
# .github/workflows/canary-deploy.yml
name: Canary Deploy

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Versione da deployare"
        required: true
        type: string
      initial-percentage:
        description: "Percentuale iniziale di traffico canary"
        required: false
        default: "5"
        type: string
      auto-promote:
        description: "Promozione automatica se le metriche sono buone"
        required: false
        default: true
        type: boolean

permissions:
  contents: read
  deployments: write
  issues: write

env:
  ERROR_THRESHOLD: "1.0"
  LATENCY_P99_THRESHOLD: "500"
  OBSERVATION_WINDOW: "300"

jobs:
  canary-5:
    name: "Canary 5% traffico"
    runs-on: ubuntu-latest
    environment:
      name: canary
    outputs:
      metrics-ok: ${{ steps.check.outputs.ok }}
    steps:
      - uses: actions/checkout@v4

      - name: Deploy versione canary
        run: |
          echo "Deploying ${{ inputs.version }} con ${{ inputs.initial-percentage }}% del traffico..."
          # Esempio con Istio VirtualService:
          # kubectl patch virtualservice my-app --type merge -p '{
          #   "spec": {"http": [{"route": [
          #     {"destination": {"host": "my-app", "subset": "stable"}, "weight": 95},
          #     {"destination": {"host": "my-app", "subset": "canary"}, "weight": 5}
          #   ]}]}
          # }'

      - name: Attendere finestra di osservazione
        run: |
          echo "Osservando metriche per ${{ env.OBSERVATION_WINDOW }} secondi..."
          sleep ${{ env.OBSERVATION_WINDOW }}

      - name: Verificare metriche canary
        id: check
        run: |
          echo "Controllando tasso di errore e latenza..."
          # Esempio: query Prometheus/Datadog
          # ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..', version='canary'}[5m])")
          # P99_LATENCY=$(curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{version='canary'}[5m]))")
          
          ERROR_RATE="0.3"
          P99_LATENCY="250"
          
          if (( $(echo "$ERROR_RATE > ${{ env.ERROR_THRESHOLD }}" | bc -l) )); then
            echo "::error::Tasso di errore troppo alto: ${ERROR_RATE}% (soglia: ${{ env.ERROR_THRESHOLD }}%)"
            echo "ok=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          
          if (( $(echo "$P99_LATENCY > ${{ env.LATENCY_P99_THRESHOLD }}" | bc -l) )); then
            echo "::error::Latenza P99 troppo alta: ${P99_LATENCY}ms (soglia: ${{ env.LATENCY_P99_THRESHOLD }}ms)"
            echo "ok=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
          
          echo "Metriche canary nella norma: errori=${ERROR_RATE}%, P99=${P99_LATENCY}ms"
          echo "ok=true" >> "$GITHUB_OUTPUT"

  canary-25:
    name: "Canary 25% traffico"
    runs-on: ubuntu-latest
    needs: canary-5
    if: ${{ needs.canary-5.outputs.metrics-ok == 'true' && inputs.auto-promote }}
    steps:
      - name: Aumentare traffico a 25%
        run: |
          echo "Incrementando traffico canary al 25%..."
          # Aggiornare i pesi del traffic splitting

      - name: Attendere e verificare
        run: |
          sleep ${{ env.OBSERVATION_WINDOW }}
          echo "Metriche a 25% verificate."

  canary-50:
    name: "Canary 50% traffico"
    runs-on: ubuntu-latest
    needs: canary-25
    steps:
      - name: Aumentare traffico a 50%
        run: |
          echo "Incrementando traffico canary al 50%..."

      - name: Attendere e verificare
        run: |
          sleep ${{ env.OBSERVATION_WINDOW }}
          echo "Metriche a 50% verificate."

  promote:
    name: "Promuovere a 100%"
    runs-on: ubuntu-latest
    needs: canary-50
    environment:
      name: production
    steps:
      - name: Promozione completa
        run: |
          echo "Promuovendo ${{ inputs.version }} al 100% del traffico..."
          # Aggiornare la versione stable e rimuovere il canary

      - name: Verifica finale
        run: |
          echo "Versione ${{ inputs.version }} ora serve il 100% del traffico."

  canary-rollback:
    name: "Rollback Canary"
    runs-on: ubuntu-latest
    needs: canary-5
    if: ${{ needs.canary-5.outputs.metrics-ok != 'true' }}
    steps:
      - name: Rimuovere il canary
        run: |
          echo "::error::Metriche canary fuori soglia. Rollback in corso..."
          echo "Riportando il 100% del traffico alla versione stable..."
          # Rimuovere il subset canary dal traffic splitting

      - name: Creare issue
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Canary deploy fallito per ${{ inputs.version }}`,
              body: `Il canary deploy della versione **${{ inputs.version }}** e stato annullato.\n\nLe metriche hanno superato le soglie configurate durante la fase al 5% del traffico.\n\nIndagare prima di ritentare.`,
              labels: ['canary-failure', 'priority: high']
            });
```

### Confronto delle strategie

| Criterio | Blue-Green | Canary | Rolling |
|----------|-----------|--------|---------|
| Velocita rollback | Istantaneo | Rapido | Lento |
| Costo infrastruttura | Alto (doppio) | Medio | Basso |
| Rischio per gli utenti | Nullo durante switch | Minimo (% piccola) | Progressivo |
| Complessita | Media | Alta | Bassa |
| Osservabilita | Test pre-switch | Metriche in tempo reale | Log incrementali |
| Caso d'uso ideale | Applicazioni critiche | Servizi ad alto traffico | Microservizi interni |

---

## Progetto 10: GitOps con ArgoCD e GitHub Actions

### Obiettivo

Implementare un workflow GitOps completo dove GitHub Actions gestisce la CI (build e test) e ArgoCD gestisce il CD (deploy su Kubernetes). Il repository Git diventa l'unica fonte di verita per lo stato desiderato dell'infrastruttura e delle applicazioni.

### Architettura GitOps

```
Developer → Push codice → GitHub (App Repo)
                            ↓
                    GitHub Actions CI
                    (test, build, push image)
                            ↓
                    Aggiorna manifesto in GitOps Repo
                            ↓
                    ArgoCD rileva il cambiamento
                            ↓
                    ArgoCD sincronizza con il cluster Kubernetes
                            ↓
                    Applicazione aggiornata in produzione
```

Il pattern prevede due repository separati:
1. **App Repo** — Contiene il codice sorgente dell'applicazione, i test e la CI
2. **GitOps Repo** — Contiene i manifesti Kubernetes (o Helm chart) che descrivono lo stato desiderato

### Passo 1 — Struttura del GitOps Repo

```
gitops-repo/
├── apps/
│   ├── web-app/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── staging/
│   │       │   ├── kustomization.yaml
│   │       │   ├── replicas-patch.yaml
│   │       │   └── configmap.yaml
│   │       └── production/
│   │           ├── kustomization.yaml
│   │           ├── replicas-patch.yaml
│   │           └── configmap.yaml
│   └── api-service/
│       ├── base/
│       │   └── ...
│       └── overlays/
│           └── ...
├── infrastructure/
│   ├── cert-manager/
│   ├── ingress-nginx/
│   └── monitoring/
├── argocd/
│   ├── applications/
│   │   ├── web-app-staging.yaml
│   │   ├── web-app-production.yaml
│   │   └── api-service-staging.yaml
│   └── projects/
│       └── default-project.yaml
└── .github/
    └── workflows/
        └── validate-manifests.yml
```

### Passo 2 — Manifesti Kubernetes base

```yaml
# apps/web-app/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
    app.kubernetes.io/name: web-app
    app.kubernetes.io/managed-by: argocd
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web-app
          image: ghcr.io/org/web-app:latest  # Aggiornato dalla CI
          ports:
            - containerPort: 3000
              protocol: TCP
          env:
            - name: NODE_ENV
              value: production
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /api/health
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
      imagePullSecrets:
        - name: ghcr-secret
```

```yaml
# apps/web-app/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production

resources:
  - ../../base

patches:
  - path: replicas-patch.yaml

images:
  - name: ghcr.io/org/web-app
    newTag: "1.2.3"  # Aggiornato automaticamente dalla CI

commonLabels:
  environment: production
```

### Passo 3 — CI che aggiorna il GitOps Repo

Questo workflow nel repository dell'applicazione costruisce l'immagine Docker e poi aggiorna il tag dell'immagine nel repository GitOps, attivando la sincronizzazione di ArgoCD.

```yaml
# Nel App Repo: .github/workflows/ci-gitops.yml
name: CI + GitOps Update

on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - '*.md'

permissions:
  contents: read
  packages: write

env:
  IMAGE_NAME: ghcr.io/${{ github.repository }}
  GITOPS_REPO: org/gitops-repo
  APP_PATH: apps/web-app

jobs:
  test:
    name: "Test"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm test

  build-push:
    name: "Build e Push Immagine"
    runs-on: ubuntu-latest
    needs: test
    outputs:
      image-tag: ${{ steps.tag.outputs.value }}
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Generare tag immagine
        id: tag
        run: |
          SHORT_SHA=$(git rev-parse --short HEAD)
          TIMESTAMP=$(date +%Y%m%d%H%M%S)
          TAG="${TIMESTAMP}-${SHORT_SHA}"
          echo "value=$TAG" >> "$GITHUB_OUTPUT"
          echo "Tag immagine: $TAG"

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build e push
        id: build
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ env.IMAGE_NAME }}:${{ steps.tag.outputs.value }}
            ${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  update-gitops:
    name: "Aggiornare GitOps Repo"
    runs-on: ubuntu-latest
    needs: build-push
    steps:
      - name: Checkout GitOps repository
        uses: actions/checkout@v4
        with:
          repository: ${{ env.GITOPS_REPO }}
          token: ${{ secrets.GITOPS_PAT }}
          path: gitops

      - name: Aggiornare tag immagine con Kustomize
        run: |
          cd gitops/${{ env.APP_PATH }}/overlays/staging
          
          # Usare kustomize per aggiornare il tag dell'immagine
          kustomize edit set image \
            ${{ env.IMAGE_NAME }}:${{ needs.build-push.outputs.image-tag }}
          
          echo "Tag aggiornato a: ${{ needs.build-push.outputs.image-tag }}"
          cat kustomization.yaml

      - name: Commit e push al GitOps repo
        run: |
          cd gitops
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          
          git add .
          git diff --staged --quiet && echo "Nessuna modifica da committare" && exit 0
          
          git commit -m "chore: aggiorna web-app a ${{ needs.build-push.outputs.image-tag }}

          Image: ${{ env.IMAGE_NAME }}:${{ needs.build-push.outputs.image-tag }}
          Digest: ${{ needs.build-push.outputs.image-digest }}
          Source commit: ${{ github.sha }}
          Workflow: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
          
          git push
```

### Passo 4 — Configurazione ArgoCD Application

```yaml
# argocd/applications/web-app-staging.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app-staging
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
  annotations:
    notifications.argoproj.io/subscribe.on-sync-succeeded.slack: deploy-notifications
    notifications.argoproj.io/subscribe.on-sync-failed.slack: deploy-alerts
spec:
  project: default
  source:
    repoURL: https://github.com/org/gitops-repo.git
    targetRevision: main
    path: apps/web-app/overlays/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: staging
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
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

### Passo 5 — Validazione dei manifesti nel GitOps Repo

```yaml
# Nel GitOps Repo: .github/workflows/validate-manifests.yml
name: Validate Manifests

on:
  pull_request:
    paths:
      - 'apps/**'
      - 'infrastructure/**'

jobs:
  validate:
    name: "Validare manifesti Kubernetes"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Kustomize
        uses: imranismail/setup-kustomize@v2

      - name: Setup kubeconform
        run: |
          LATEST=$(curl -s https://api.github.com/repos/yannh/kubeconform/releases/latest | jq -r '.tag_name')
          curl -sL "https://github.com/yannh/kubeconform/releases/download/${LATEST}/kubeconform-linux-amd64.tar.gz" | tar xz
          sudo mv kubeconform /usr/local/bin/

      - name: Validare tutti gli overlay
        run: |
          ERRORS=0
          for overlay_dir in apps/*/overlays/*/; do
            echo "--- Validando: $overlay_dir ---"
            kustomize build "$overlay_dir" | kubeconform \
              -strict \
              -summary \
              -output json \
              -kubernetes-version 1.30.0 || ERRORS=$((ERRORS + 1))
          done
          
          if [ $ERRORS -gt 0 ]; then
            echo "::error::$ERRORS overlay hanno fallito la validazione"
            exit 1
          fi
          echo "Tutti gli overlay sono validi."

      - name: Diff con il cluster (dry-run)
        if: always()
        run: |
          echo "Simulando l'applicazione dei manifesti..."
          for overlay_dir in apps/*/overlays/staging/; do
            echo "--- Dry-run: $overlay_dir ---"
            kustomize build "$overlay_dir" | kubectl diff -f - --server-side 2>/dev/null || true
          done
```

### Vantaggi del pattern GitOps

1. **Auditabilita completa** — Ogni cambiamento all'infrastruttura e tracciabile tramite la storia dei commit Git
2. **Rollback semplice** — Per tornare a una versione precedente basta fare `git revert` sul commit nel GitOps repo
3. **Self-healing** — ArgoCD rileva automaticamente le deviazioni dallo stato desiderato e le corregge
4. **Separazione dei compiti** — La CI (build/test) e separata dal CD (deploy), riducendo la superficie di attacco
5. **Review del deploy** — Le modifiche al GitOps repo passano attraverso PR con review, applicando lo stesso processo di qualita del codice applicativo

---

## Progetto Bonus: Portfolio GitHub Professionale

### Obiettivo

Costruire un profilo GitHub che funzioni come portfolio professionale, configurando il README del profilo, pinnando i repository piu significativi, organizzando i contributi e creando un sito portfolio con GitHub Pages.

### Passo 1 — README del profilo

Il README del profilo e il primo elemento che i recruiter vedono. Creare un repository con lo stesso nome del proprio username GitHub (es. `username/username`).

```markdown
# README.md del repository username/username

## Chi sono

Sviluppatore full-stack con 5 anni di esperienza in architetture cloud-native,
CI/CD e DevOps. Specializzato in TypeScript, Go e infrastruttura Kubernetes.

## Tecnologie

![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Go](https://img.shields.io/badge/-Go-00ADD8?style=flat-square&logo=go&logoColor=white)
![Kubernetes](https://img.shields.io/badge/-Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white)
![Terraform](https://img.shields.io/badge/-Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/-GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)

## Progetti in evidenza

| Progetto | Descrizione | Tech |
|----------|-------------|------|
| [api-gateway](link) | API Gateway con rate limiting e circuit breaker | Go, gRPC |
| [deploy-pipeline](link) | Pipeline CI/CD GitOps per Kubernetes | Actions, ArgoCD |
| [ui-components](link) | Libreria componenti React con Storybook | TypeScript, React |

## Statistiche

![GitHub Stats](https://github-readme-stats.vercel.app/api?username=TUO-USERNAME&show_icons=true&theme=default)
```

### Passo 2 — Pinnare i repository giusti

Selezionare al massimo 6 repository da pinnare, seguendo questi criteri:

1. **Varieta tecnologica** — Mostrare competenze in linguaggi e stack diversi
2. **Qualita del codice** — Repository con test, CI/CD, documentazione e commit puliti
3. **Impatto reale** — Progetti che risolvono problemi concreti, non tutorial clonati
4. **Contribuzioni open source** — Fork di progetti noti con PR mergiate
5. **README professionali** — Ogni repository pinnato deve avere un README completo con badges, screenshot e istruzioni di setup

```bash
# Verificare le statistiche dei propri repository
gh repo list --limit=20 --json name,stargazerCount,forkCount,primaryLanguage \
  --jq '.[] | "\(.name)\t\(.stargazerCount) stelle\t\(.forkCount) fork\t\(.primaryLanguage.name)"'
```

### Passo 3 — Contribuzione regolare e contribution graph

Il grafico delle contribuzioni (la "heat map verde") e un segnale visivo importante. Non si tratta di riempirlo artificialmente, ma di mantenere un ritmo costante di contribuzione reale:

- Commit giornalieri a progetti personali o open source
- Review di PR su progetti della community
- Apertura e gestione di issue
- Aggiornamento documentazione
- Rilascio di nuove versioni

```bash
# Visualizzare le proprie contribuzioni recenti
gh api graphql -f query='
  query {
    viewer {
      contributionsCollection {
        contributionCalendar {
          totalContributions
          weeks {
            contributionDays {
              contributionCount
              date
            }
          }
        }
      }
    }
  }
' --jq '.data.viewer.contributionsCollection.contributionCalendar.totalContributions'
```

### Passo 4 — GitHub Pages come portfolio

```yaml
# .github/workflows/deploy-portfolio.yml
name: Deploy Portfolio

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy su GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## Esercizi Avanzati

### Esercizio 6: Dynamic Matrix per Test Sharding

```yaml
# Obiettivo: creare una matrix dinamica basata sui file modificati

# File: .github/workflows/dynamic-matrix.yml
name: Dynamic Matrix CI

on:
  pull_request:

jobs:
  detect-packages:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
      has-changes: ${{ steps.set-matrix.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Rilevare pacchetti modificati
        id: set-matrix
        run: |
          # Trovare tutti i pacchetti con modifiche rispetto al base branch
          CHANGED_FILES=$(git diff --name-only origin/${{ github.base_ref }}...HEAD)
          
          PACKAGES=()
          for file in $CHANGED_FILES; do
            if [[ $file == packages/* ]]; then
              PKG=$(echo "$file" | cut -d'/' -f2)
              PACKAGES+=("$PKG")
            fi
          done
          
          # Rimuovere duplicati e formattare come JSON
          UNIQUE_PKGS=$(echo "${PACKAGES[@]}" | tr ' ' '\n' | sort -u | jq -R -s -c 'split("\n") | map(select(. != ""))')
          
          if [ "$UNIQUE_PKGS" = "[]" ]; then
            echo "has-changes=false" >> "$GITHUB_OUTPUT"
            echo "matrix={\"package\":[]}" >> "$GITHUB_OUTPUT"
          else
            echo "has-changes=true" >> "$GITHUB_OUTPUT"
            echo "matrix={\"package\":$UNIQUE_PKGS}" >> "$GITHUB_OUTPUT"
          fi
          
          echo "Pacchetti modificati: $UNIQUE_PKGS"

  test-package:
    needs: detect-packages
    if: needs.detect-packages.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.detect-packages.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - name: Test pacchetto ${{ matrix.package }}
        run: npm run test --workspace=packages/${{ matrix.package }}

# Compiti:
# 1. Implementare la struttura monorepo con 3+ pacchetti
# 2. Testare che modifiche a un solo pacchetto eseguano solo quei test
# 3. Aggiungere un job di coverage aggregata che unisce i report
# 4. Aggiungere supporto per dipendenze tra pacchetti
```

### Esercizio 7: Workflow di Promozione Multi-Ambiente

```yaml
# Obiettivo: implementare la promozione di un artefatto attraverso
# staging → pre-production → production con gate manuali

# File: .github/workflows/promotion.yml
name: Environment Promotion

on:
  workflow_dispatch:
    inputs:
      artifact-version:
        description: "Versione dell'artefatto da promuovere"
        required: true
        type: string
      target-environment:
        description: "Ambiente target"
        required: true
        type: choice
        options:
          - staging
          - pre-production
          - production

permissions:
  contents: read
  deployments: write

jobs:
  validate-promotion:
    name: "Validare promozione"
    runs-on: ubuntu-latest
    outputs:
      allowed: ${{ steps.check.outputs.allowed }}
    steps:
      - name: Verificare prerequisiti di promozione
        id: check
        run: |
          TARGET="${{ inputs.target-environment }}"
          VERSION="${{ inputs.artifact-version }}"
          
          # Logica di validazione:
          # - pre-production richiede che staging sia stato deployato
          # - production richiede che pre-production sia stato deployato
          
          case "$TARGET" in
            staging)
              echo "allowed=true" >> "$GITHUB_OUTPUT"
              echo "Promozione a staging: sempre permessa."
              ;;
            pre-production)
              # Verificare che la versione sia presente in staging
              echo "allowed=true" >> "$GITHUB_OUTPUT"
              echo "Verificato: versione $VERSION presente in staging."
              ;;
            production)
              # Verificare che la versione sia presente in pre-production
              echo "allowed=true" >> "$GITHUB_OUTPUT"
              echo "Verificato: versione $VERSION presente in pre-production."
              ;;
            *)
              echo "::error::Ambiente sconosciuto: $TARGET"
              echo "allowed=false" >> "$GITHUB_OUTPUT"
              ;;
          esac

  deploy:
    name: "Deploy a ${{ inputs.target-environment }}"
    needs: validate-promotion
    if: needs.validate-promotion.outputs.allowed == 'true'
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.target-environment }}
    steps:
      - name: Eseguire deploy
        run: |
          echo "Deploying versione ${{ inputs.artifact-version }} a ${{ inputs.target-environment }}..."
          # Deploy effettivo qui

      - name: Smoke test post-deploy
        run: |
          echo "Eseguendo smoke test su ${{ inputs.target-environment }}..."
          # Smoke test specifici per l'ambiente

# Compiti:
# 1. Implementare la logica reale di verifica dei prerequisiti
# 2. Aggiungere un job di integration test dopo il deploy a pre-production
# 3. Aggiungere notifiche Slack per ogni promozione
# 4. Implementare un meccanismo di rollback automatico
# 5. Aggiungere un audit log delle promozioni (chi, quando, quale versione)
```

### Esercizio 8: Self-Hosted Runner con Auto-Scaling

```yaml
# Obiettivo: configurare un self-hosted runner con scaling automatico

# File: runner-deployment.yaml (Kubernetes)
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: org-runner
  namespace: actions-runner-system
spec:
  replicas: 1  # Gestito dall'autoscaler
  template:
    spec:
      organization: my-org
      labels:
        - self-hosted
        - linux
        - x64
        - gpu  # Label personalizzata per job GPU
      ephemeral: true  # Runner effimero: distrutto dopo ogni job
      dockerEnabled: true
      resources:
        limits:
          cpu: "4"
          memory: "8Gi"
        requests:
          cpu: "2"
          memory: "4Gi"
---
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: org-runner-autoscaler
  namespace: actions-runner-system
spec:
  scaleTargetRef:
    kind: RunnerDeployment
    name: org-runner
  minReplicas: 0
  maxReplicas: 10
  scaleDownDelaySecondsAfterScaleOut: 300
  metrics:
    - type: PercentageRunnersBusy
      scaleUpThreshold: "0.75"
      scaleDownThreshold: "0.25"
      scaleUpFactor: "2"
      scaleDownFactor: "0.5"

# Compiti:
# 1. Installare Actions Runner Controller (ARC) nel cluster
# 2. Configurare il runner per l'organizzazione
# 3. Creare un workflow che usa il self-hosted runner:
#    runs-on: [self-hosted, linux, x64]
# 4. Verificare che il runner scala automaticamente con il carico
# 5. Configurare monitoring con Prometheus per tracciare:
#    - Numero di runner attivi
#    - Tempo di attesa in coda dei job
#    - Utilizzo risorse dei runner
# 6. Implementare un runner con GPU per job di ML
```

### Esercizio 9: Security Hardening Avanzato

```yaml
# Obiettivo: implementare le best practice di sicurezza 2026 per GitHub Actions

# File: .github/workflows/hardened-ci.yml
name: Hardened CI

on:
  push:
    branches: [main]
  pull_request:

# Principio del minimo privilegio: permissions esplicite e minimali
permissions:
  contents: read
  checks: write

# Impostare timeout globale per prevenire job bloccati
defaults:
  run:
    shell: bash

jobs:
  security-checks:
    name: "Controlli di sicurezza"
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
        with:
          persist-credentials: false  # Non mantenere il token nel checkout

      # Pinnare TUTTE le actions al SHA del commit, mai al tag
      - uses: actions/setup-node@1d0ff469b7ec7b3cb9d8673fde8c81c9a3be4fac  # v4.2.0
        with:
          node-version: 22

      - name: Installare dipendenze con lockfile verificato
        run: npm ci --ignore-scripts  # Disabilitare script post-install per sicurezza

      - name: Scansione dipendenze
        run: npm audit --audit-level=high

      - name: Scansione segreti nel codice
        uses: gitleaks/gitleaks-action@44c470ffc35caa5c65e0e6b9d20c48391ed0e7a2  # v2.3.7
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Verificare che non ci siano segreti nei log
        run: |
          # Verificare che variabili sensibili siano mascherate
          echo "::add-mask::${{ secrets.GITHUB_TOKEN }}"
          
          # Verificare che non ci siano pattern sospetti nel codice
          if grep -rn "AKIA\|sk-\|ghp_\|gho_\|github_pat_" --include="*.ts" --include="*.js" --include="*.json" .; then
            echo "::error::Possibili segreti trovati nel codice sorgente!"
            exit 1
          fi
          echo "Nessun segreto trovato nel codice."

# Regole di sicurezza applicate:
# 1. Permissions minimali e esplicite (mai usare permissions: write-all)
# 2. Tutte le actions pinnate al SHA del commit
# 3. persist-credentials: false nel checkout
# 4. Timeout su ogni job per prevenire mining di cripto
# 5. npm ci --ignore-scripts per prevenire supply chain attacks
# 6. Scansione segreti automatica
# 7. Mascheratura dei segreti nei log

# Compiti aggiuntivi:
# 1. Implementare OIDC per eliminare i segreti statici verso il cloud provider
# 2. Configurare egress rules per limitare le connessioni di rete dei workflow
# 3. Aggiungere SBOM (Software Bill of Materials) alla build
# 4. Implementare artifact attestation con Sigstore
# 5. Configurare il Dependency Graph per monitorare le dipendenze
# 6. Abilitare la funzionalita di dependency locking dei workflow (2026)
```

### Esercizio 10: Workflow Completo di Revisione Automatica

```yaml
# Obiettivo: creare un workflow che automatizza la revisione del codice
# con metriche di qualita, check di dimensione PR e analisi statica

# File: .github/workflows/pr-review-automation.yml
name: PR Review Automation

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write
  contents: read
  checks: write

jobs:
  pr-size-check:
    name: "Controllo dimensione PR"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Calcolare dimensione PR
        id: size
        run: |
          ADDITIONS=$(git diff --numstat origin/${{ github.base_ref }}...HEAD | awk '{sum+=$1} END {print sum}')
          DELETIONS=$(git diff --numstat origin/${{ github.base_ref }}...HEAD | awk '{sum+=$2} END {print sum}')
          TOTAL=$((ADDITIONS + DELETIONS))
          FILES=$(git diff --name-only origin/${{ github.base_ref }}...HEAD | wc -l)
          
          echo "additions=$ADDITIONS" >> "$GITHUB_OUTPUT"
          echo "deletions=$DELETIONS" >> "$GITHUB_OUTPUT"
          echo "total=$TOTAL" >> "$GITHUB_OUTPUT"
          echo "files=$FILES" >> "$GITHUB_OUTPUT"
          
          # Classificare la dimensione
          if [ "$TOTAL" -lt 50 ]; then
            SIZE="XS"
            COLOR="0e8a16"
          elif [ "$TOTAL" -lt 200 ]; then
            SIZE="S"
            COLOR="2cbe4e"
          elif [ "$TOTAL" -lt 400 ]; then
            SIZE="M"
            COLOR="fbca04"
          elif [ "$TOTAL" -lt 800 ]; then
            SIZE="L"
            COLOR="d93f0b"
          else
            SIZE="XL"
            COLOR="b60205"
          fi
          echo "size=$SIZE" >> "$GITHUB_OUTPUT"
          echo "color=$COLOR" >> "$GITHUB_OUTPUT"

      - name: Applicare label dimensione
        uses: actions/github-script@v7
        with:
          script: |
            const size = '${{ steps.size.outputs.size }}';
            const total = ${{ steps.size.outputs.total }};
            const files = ${{ steps.size.outputs.files }};
            
            // Rimuovere label di dimensione precedenti
            const labels = await github.rest.issues.listLabelsOnIssue({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number
            });
            
            for (const label of labels.data) {
              if (label.name.startsWith('size/')) {
                await github.rest.issues.removeLabel({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: context.issue.number,
                  name: label.name
                });
              }
            }
            
            // Aggiungere la nuova label
            try {
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                labels: [`size/${size}`]
              });
            } catch (e) {
              // Creare la label se non esiste
              await github.rest.issues.createLabel({
                owner: context.repo.owner,
                repo: context.repo.repo,
                name: `size/${size}`,
                color: '${{ steps.size.outputs.color }}'
              });
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                labels: [`size/${size}`]
              });
            }
            
            // Avvertire se la PR e troppo grande
            if (total > 400) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: `### PR di grandi dimensioni rilevata\n\nQuesta PR modifica **${total} righe** in **${files} file**.\n\nLe PR di grandi dimensioni sono piu difficili da revisionare e hanno maggiore probabilita di contenere bug. Considera di suddividerla in PR piu piccole e focalizzate.\n\n| Metrica | Valore |\n|---------|--------|\n| Righe aggiunte | +${{ steps.size.outputs.additions }} |\n| Righe rimosse | -${{ steps.size.outputs.deletions }} |\n| File modificati | ${files} |\n| Dimensione | **${size}** |`
              });
            }

# Compiti:
# 1. Aggiungere un job che verifica la presenza di test per i file modificati
# 2. Aggiungere un check per file con troppo nesting (>4 livelli)
# 3. Aggiungere un check per funzioni troppo lunghe (>50 righe)
# 4. Integrare un linter per i messaggi di commit
# 5. Creare un report di qualita come commento sulla PR
```

---

## Guida alla Risoluzione dei Problemi Comuni

### Problemi di autenticazione e permessi

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `Resource not accessible by integration` | Permessi insufficienti nel workflow | Aggiungere il blocco `permissions` con i permessi necessari |
| `Bad credentials` nel push al GitOps repo | Il `GITHUB_TOKEN` non ha accesso a repository esterni | Usare un Personal Access Token (PAT) salvato nei secrets |
| `denied: permission_denied` nel push Docker | Login al registry mancante o token scaduto | Verificare il login con `docker/login-action` e i permessi `packages: write` |
| OIDC token non accettato dal cloud provider | Trust policy non configurata correttamente | Verificare il subject claim e l'audience nell'OIDC provider del cloud |

### Problemi di performance dei workflow

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Workflow lento (>15 minuti) | Nessun caching configurato | Aggiungere `actions/cache` o il parametro `cache` in `actions/setup-node` |
| Cache miss frequenti | Chiave di cache troppo specifica | Usare `restore-keys` con prefissi progressivamente meno specifici |
| Minuti Actions esauriti | Workflow eseguiti troppo frequentemente | Usare `paths-ignore`, `concurrency` con `cancel-in-progress` e filtraggio branch |
| Build Docker lento | Nessun layer caching | Usare `cache-from: type=gha` e `cache-to: type=gha,mode=max` |
| Test lenti | Esecuzione sequenziale | Implementare test sharding con matrix strategy |

### Problemi di configurazione

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Workflow non si attiva | Trigger `on` non corretto o file in path sbagliato | Verificare il trigger, il nome del branch e il path del workflow |
| `if` condition non funziona | Sintassi errata nell'espressione | Usare `${{ }}` e verificare i tipi (stringa vs booleano) |
| Secret non disponibile nei fork | I secrets non sono condivisi con i fork per sicurezza | Usare `pull_request_target` (con cautela) o richiedere che il contributor usi le proprie secrets |
| Artifact non trovato tra workflow | `workflow_run` non condivide artefatti automaticamente | Usare `actions/download-artifact` con `run-id` e `github-token` |
| Matrix exclude non funziona | Sintassi exclude errata | Verificare che i valori nell'exclude corrispondano esattamente a quelli nella matrix |

### Comandi Git utili per il debug

```bash
# Verificare quali file sono stati modificati in una PR
git diff --name-only origin/main...HEAD

# Verificare la storia dei merge di un branch
git log --oneline --graph --all --decorate -20

# Trovare quale commit ha introdotto un bug (bisect)
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
# Git navighera automaticamente tra i commit; per ogni commit testare e segnalare:
git bisect good  # o git bisect bad
# Alla fine:
git bisect reset

# Recuperare un file cancellato
git log --diff-filter=D --summary -- percorso/al/file
git checkout <commit-prima-della-cancellazione> -- percorso/al/file

# Trovare tutte le PR mergiate nell'ultimo mese
gh pr list --state=merged --limit=50 \
  --json number,title,mergedAt,author \
  --jq '.[] | select(.mergedAt > "2026-04-01") | "\(.number): \(.title) (\(.author.login))"'

# Confrontare la dimensione del repository nel tempo
git rev-list --all --count
git count-objects -vH
```

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Actions Starter Workflows**: https://github.com/actions/starter-workflows — Template ufficiali per CI/CD organizzati per linguaggio e framework.
- **GitHub Docs — Managing Releases**: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository — Guida completa alla gestione delle release.
- **GitHub Docs — CODEOWNERS**: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners — Sintassi e best practice per CODEOWNERS.
- **dorny/paths-filter**: https://github.com/dorny/paths-filter — Action per rilevare file modificati, essenziale per monorepo CI.
- **Conventional Commits**: https://www.conventionalcommits.org/it/ — Specifica per messaggi di commit strutturati (versione italiana).
- **Semantic Versioning 2.0.0**: https://semver.org/lang/it/ — Specifica del semantic versioning (versione italiana).
- **GitHub Skills**: https://skills.github.com — Corsi interattivi ufficiali basati su repository reali.

### Libri consigliati

- **"Learning GitHub Actions" — Brent Laster** (O'Reilly) — Dai fondamenti ai pattern avanzati, con progetti pratici end-to-end.
- **"Continuous Delivery" — Jez Humble, David Farley** (Addison-Wesley) — Il testo fondamentale su pipeline CI/CD, deployment e release engineering.
- **"The DevOps Handbook" — Gene Kim et al.** (IT Revolution, 2nd ed.) — Framework operativo per integrare dev e ops, direttamente applicabile ai progetti.

---

## Riferimenti Incrociati

| Modulo | File | Relazione |
|--------|------|-----------|
| 04 | [04-github-actions.md](04-github-actions.md) | Prerequisito: sintassi workflow, matrix, secrets e caching |
| 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) | Ricette CI/CD pronte all'uso che estendono i progetti qui proposti |
| 20 | [20-git-workflow-team-guida-completa.md](20-git-workflow-team-guida-completa.md) | Workflow operativi per team, complemento diretto al Progetto 1 |
| 24 | [24-devops-completo-con-github.md](24-devops-completo-con-github.md) | Pipeline DevOps end-to-end con GitHub come piattaforma centrale |
| 27 | [27-supply-chain-attestation-slsa.md](27-supply-chain-attestation-slsa.md) | Supply chain security e SLSA, estende il Progetto security scanning |
| 28 | [28-codeql-advanced-security.md](28-codeql-advanced-security.md) | Approfondimento CodeQL per analisi statica avanzata nei progetti |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **CI/CD** | Continuous Integration / Continuous Delivery — pratica di automatizzare test, build e deploy ad ogni commit |
| **Pipeline** | Sequenza ordinata di job (test → build → deploy) che processa il codice dalla commit alla produzione |
| **Release** | Versione pubblicata del software con tag, changelog e artifact scaricabili su GitHub Releases |
| **Semantic Versioning** | Schema di versionamento MAJOR.MINOR.PATCH dove ogni componente ha significato preciso (breaking, feature, fix) |
| **Changelog** | Documento che elenca le modifiche per ogni versione, generabile automaticamente da conventional commits |
| **Monorepo** | Repository singolo che contiene più progetti/servizi, gestito con path filtering e affected analysis |
| **Path Filtering** | Tecnica per eseguire job CI solo quando file in directory specifiche vengono modificati (es. dorny/paths-filter) |
| **CODEOWNERS** | File che mappa path del repository a team/utenti responsabili, assegnati automaticamente come reviewer |
| **Inner Source** | Applicazione delle pratiche open source (fork, PR, review) all'interno di un'organizzazione |
| **Infrastructure as Code (IaC)** | Gestione dell'infrastruttura tramite file di configurazione versionati (Terraform, Pulumi, CloudFormation) |
| **Security Scanning** | Analisi automatica del codice e delle dipendenze per individuare vulnerabilità (SAST, SCA, secret scanning) |
| **Smoke Test** | Test rapido post-deploy che verifica che le funzionalità critiche dell'applicazione siano operative |
| **Dependabot** | Servizio GitHub che apre PR automatiche per aggiornare dipendenze con vulnerabilità note |
| **GitHub Environment** | Configurazione target di deploy con secrets dedicati, reviewer obbligatori e regole di protezione |
| **Composite Action** | Azione personalizzata scritta in YAML che raggruppa piu step in uno solo, riutilizzabile tra workflow |
| **Workflow Riutilizzabile** | Workflow intero invocabile da altri workflow tramite il trigger `workflow_call`, permettendo il riuso di job completi |
| **Blue-Green Deploy** | Strategia di deploy con due ambienti identici (blue e green) dove il traffico viene spostato istantaneamente tra i due |
| **Canary Deploy** | Strategia di deploy progressivo che instrada una percentuale crescente di traffico alla nuova versione monitorando le metriche |
| **GitOps** | Pratica DevOps che usa Git come unica fonte di verita per lo stato desiderato dell'infrastruttura e delle applicazioni |
| **ArgoCD** | Controller Kubernetes che implementa il pattern GitOps, sincronizzando automaticamente i manifesti Git con il cluster |
| **Kustomize** | Tool nativo Kubernetes per personalizzare manifesti YAML tramite overlay senza modificare i file base |
| **OIDC** | OpenID Connect — protocollo di autenticazione che permette ai workflow di ottenere token temporanei senza segreti statici |
| **Self-Hosted Runner** | Runner GitHub Actions eseguito su infrastruttura propria anzi che sui runner cloud di GitHub |
| **Ephemeral Runner** | Runner che viene creato e distrutto per ogni singolo job, garantendo isolamento e pulizia dell'ambiente |
| **Supply Chain Attack** | Attacco alla catena di fornitura del software, che compromette dipendenze, azioni o tool per iniettare codice malevolo |
| **SBOM** | Software Bill of Materials — inventario completo delle dipendenze di un software, usato per audit di sicurezza |
| **Artifact Attestation** | Firma crittografica che certifica la provenienza e l'integrita di un artefatto di build |
| **Drift Detection** | Rilevamento automatico delle differenze tra lo stato desiderato (codice) e lo stato reale dell'infrastruttura |
| **Rolling Update** | Strategia di deploy che aggiorna le istanze una alla volta, mantenendo il servizio disponibile durante l'aggiornamento |
| **Fork Workflow** | Flusso di lavoro open source dove il contributore crea una copia del repository, sviluppa modifiche e propone una PR al progetto originale |
| **Matrix Strategy** | Funzionalita GitHub Actions che esegue lo stesso job con combinazioni diverse di parametri (versioni, OS, configurazioni) in parallelo |
| **Dynamic Matrix** | Matrix generata a runtime tramite `fromJSON()`, permettendo di creare job paralleli basati su condizioni rilevate dinamicamente |
