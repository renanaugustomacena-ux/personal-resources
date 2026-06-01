---
corso: "GitHub e Git Actions"
fase: "3 — Piattaforma GitHub"
modulo: 3
titolo: "Piattaforma GitHub — Guida Completa"
versione: "GitHub 2026"
livello: "Avanzato"
prerequisiti: ["01-fondamenti-git", "02-strategie-branching", "Familiarità con l'interfaccia web GitHub"]
obiettivi:
  - "Configurare organizzazioni, team e permessi granulari su GitHub"
  - "Gestire repository con branch protection, rulesets e template"
  - "Utilizzare Issues, Projects v2 e milestones per il project management"
  - "Padroneggiare il workflow di Pull Request e Code Review"
  - "Automatizzare operazioni con GitHub CLI e GitHub Apps"
tag: [github, organizzazioni, permessi, pull-request, code-review, projects-v2, github-cli, github-apps, 2fa]
---

# Piattaforma GitHub — Guida Completa

> **Modulo 03** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Configurare organizzazioni GitHub con team, ruoli e policy di sicurezza (2FA obbligatorio)
> 2. Gestire repository con branch protection rules, rulesets e template standardizzati
> 3. Organizzare il lavoro con Issues, Projects v2 (Board, Table, Roadmap) e milestones
> 4. Condurre code review efficaci tramite Pull Request con reviewer assignment e CODEOWNERS
> 5. Automatizzare operazioni quotidiane con `gh` CLI e integrare GitHub Apps per workflow avanzati

## Idee guida
1. **GitHub Enterprise Cloud / Server / EMU: 3 piani.**
2. **Organization > User per progetti seri.**
3. **2FA mandatory dal 2024.**
4. **Audit log API per compliance.**


## Indice

- [Panoramica](#panoramica)
- [Architettura della Piattaforma](#architettura-della-piattaforma)
- [Gestione Repository](#gestione-repository)
- [Organizations, Teams e Permessi](#organizations-teams-e-permessi)
- [Issues e Project Management](#issues-e-project-management)
- [Pull Request e Code Review](#pull-request-e-code-review)
- [GitHub CLI (gh)](#github-cli-gh)
- [GitHub API](#github-api)
- [Sicurezza GitHub](#sicurezza-github)
- [GitHub Apps vs Personal Access Tokens](#github-apps-vs-personal-access-tokens)
- [Funzionalità Avanzate](#funzionalità-avanzate)
- [Anti-Pattern](#anti-pattern)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Riferimenti](#riferimenti)

---

## Panoramica

GitHub è la piattaforma di hosting Git più utilizzata al mondo, con funzionalità di collaborazione, project management, CI/CD (Actions), sicurezza (Dependabot, CodeQL), e hosting (Pages, Packages). È il centro dell'ecosistema open source e sempre più usato nelle enterprise.

### Piani GitHub

| Piano | Target | Caratteristiche Chiave |
|-------|--------|----------------------|
| **Free** | Individui/OSS | Repo illimitati, Actions 2000 min/mese, Codespaces 120 ore/mese |
| **Pro** | Individui power-user | Tutto Free + branch protection avanzata, insights, 3000 min Actions |
| **Team** | Organizzazioni | Tutto Pro + team, CODEOWNERS obbligatorio, 3000 min Actions |
| **Enterprise Cloud** | Grandi aziende | Tutto Team + SAML SSO, audit log, SCIM, IP allow list |
| **Enterprise Server** | On-premise | Self-hosted, controllo infrastruttura, LDAP/SAML |
| **EMU (Enterprise Managed Users)** | Enterprise con IdP | Account gestiti dal provider di identità, nessun account personale |

### Flusso di Lavoro Tipico sulla Piattaforma

```
┌─────────────────────────────────────────────────────────────┐
│                    GITHUB PLATFORM FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Developer        GitHub              CI/CD       Reviewer  │
│  ─────────        ──────              ─────       ────────  │
│      │                │                  │            │      │
│      │── push ──────►│                  │            │      │
│      │               │── trigger ─────►│            │      │
│      │               │                  │── run ──► │      │
│      │               │◄── status ──────│            │      │
│      │── open PR ──►│                  │            │      │
│      │               │── notify ──────────────────►│      │
│      │               │                  │            │      │
│      │               │◄── review ─────────────────│      │
│      │               │── merge ────────►│            │      │
│      │               │                  │── deploy ►│      │
│      │               │                  │            │      │
└─────────────────────────────────────────────────────────────┘
```

---

## Architettura della Piattaforma

### Struttura Gerarchica

```
┌───────────────────────────────────────────────────┐
│                  ENTERPRISE                       │
│  ┌─────────────────────────────────────────────┐  │
│  │              ORGANIZATION                   │  │
│  │  ┌───────────────┐  ┌───────────────────┐   │  │
│  │  │   TEAM        │  │      TEAM         │   │  │
│  │  │  ┌─────────┐  │  │  ┌─────────────┐  │   │  │
│  │  │  │  REPO   │  │  │  │    REPO      │  │   │  │
│  │  │  │ branch  │  │  │  │   branch     │  │   │  │
│  │  │  │ issues  │  │  │  │   issues     │  │   │  │
│  │  │  │ actions │  │  │  │   actions    │  │   │  │
│  │  │  └─────────┘  │  │  └─────────────┘  │   │  │
│  │  └───────────────┘  └───────────────────┘   │  │
│  └─────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────┘
```

### Componenti Fondamentali

- **Repository**: Unità base di storage. Contiene codice, issues, PR, Actions, Packages, wiki, discussions.
- **Organization**: Contenitore per team e repository. Gestisce permessi, billing, sicurezza centralizzata.
- **Team**: Gruppo di utenti con permessi specifici su un set di repository.
- **Project**: Board Kanban/Table/Roadmap cross-repository per project management.
- **Actions**: CI/CD integrato con runner GitHub-hosted o self-hosted.
- **Packages**: Registry per npm, Docker (GHCR), Maven, NuGet, RubyGems.
- **Pages**: Hosting statico gratuito con HTTPS automatico.
- **Codespaces**: Ambienti di sviluppo cloud con VS Code.
- **Copilot**: Assistente AI per il coding (disponibile su piani Pro/Enterprise).

---

## Gestione Repository

### Configurazione Repository

```bash
# Creare repository
gh repo create my-project --public --clone
gh repo create my-project --private --add-readme --license mit --gitignore Node

# Creare repository in un'organizzazione
gh repo create my-org/my-project --private --team backend-team

# File importanti nella root:
# README.md          → Documentazione principale
# LICENSE            → Licenza del progetto
# .gitignore         → File da ignorare
# CODEOWNERS         → Chi deve fare review per area di codice
# CONTRIBUTING.md    → Guida per contribuire
# SECURITY.md        → Policy di sicurezza (vulnerability reporting)
# .github/
# ├── ISSUE_TEMPLATE/        → Template per issues
# ├── PULL_REQUEST_TEMPLATE.md → Template per PR
# ├── FUNDING.yml            → Link sponsorizzazione
# ├── dependabot.yml         → Configurazione Dependabot
# └── workflows/             → GitHub Actions workflow
```

### Opzioni del Comando `gh repo create`

| Opzione | Descrizione |
|---------|-------------|
| `--public` | Repository pubblico |
| `--private` | Repository privato |
| `--internal` | Repository interno (solo Enterprise) |
| `--clone` | Clona il repo dopo la creazione |
| `--add-readme` | Aggiunge un README.md predefinito |
| `--license <tipo>` | Aggiunge licenza (mit, apache-2.0, gpl-3.0, etc.) |
| `--gitignore <lang>` | Aggiunge .gitignore per il linguaggio specificato |
| `--template <repo>` | Crea da un template repository |
| `--team <team>` | Assegna team con accesso (solo org) |
| `--description <desc>` | Descrizione del repository |
| `--homepage <url>` | URL homepage del progetto |
| `--disable-issues` | Disabilita la sezione issues |
| `--disable-wiki` | Disabilita la wiki |

### Branch Protection Rules

```bash
# Settings → Branches → Add branch protection rule

# Pattern: main (o main, release/*)
# Opzioni consigliate:
# ✅ Require a pull request before merging
#    ✅ Require approvals: 1 (o 2 per team grandi)
#    ✅ Dismiss stale reviews when new commits are pushed
#    ✅ Require review from Code Owners
# ✅ Require status checks to pass before merging
#    ✅ Require branches to be up to date
#    → Aggiungere: CI test, lint, build
# ✅ Require signed commits (opzionale, per alta sicurezza)
# ✅ Require linear history (forza squash o rebase)
# ✅ Include administrators (anche admin devono seguire le regole)
# ❌ Allow force pushes (MAI su main)
# ❌ Allow deletions (MAI su main)

# Via gh CLI (GitHub CLI):
gh api repos/{owner}/{repo}/branches/main/protection -X PUT -F \
    required_status_checks='{"strict":true,"contexts":["ci"]}' \
    required_pull_request_reviews='{"required_approving_review_count":1}'
```

### Rulesets (Successore delle Branch Protection Rules)

A partire dal 2023, GitHub ha introdotto i **Repository Rulesets** come evoluzione delle branch protection rules. I rulesets offrono:

- Applicazione a livello di organizzazione (non solo singolo repo)
- Targeting tramite pattern (branch e tag)
- Bypass list configurabile
- Enforcement modes: Active, Evaluate (dry-run), Disabled
- Supporto per regole su tag (non solo branch)

```bash
# Creare un ruleset via API
gh api repos/{owner}/{repo}/rulesets -X POST -F name="main-protection" \
    -F target="branch" \
    -F enforcement="active" \
    -F conditions='{"ref_name":{"include":["refs/heads/main"],"exclude":[]}}' \
    -F rules='[
        {"type":"pull_request","parameters":{"required_approving_review_count":1}},
        {"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"ci"}]}},
        {"type":"deletion"},
        {"type":"non_fast_forward"}
    ]'

# Elencare i rulesets
gh api repos/{owner}/{repo}/rulesets
```

### CODEOWNERS

```bash
# .github/CODEOWNERS
# Definisce chi deve approvare le PR per specifiche aree di codice

# Formato: <pattern> <owner1> <owner2>
*                    @team-leads          # Default: team leads per tutto
/src/api/            @backend-team        # Backend team per API
/src/frontend/       @frontend-team       # Frontend team
/infrastructure/     @devops-team         # DevOps per infrastruttura
*.sql                @dba-team            # DBA per file SQL
/docs/               @tech-writers        # Technical writers per docs
Dockerfile           @devops-team
.github/workflows/   @devops-team         # DevOps per CI/CD
```

### Funzionamento Interno di CODEOWNERS

```
┌──────────────────────────────────────────────────────┐
│                   PR SUBMITTED                       │
│                       │                              │
│          ┌────────────▼────────────┐                 │
│          │  Analizza file modificati│                 │
│          └────────────┬────────────┘                 │
│                       │                              │
│     ┌─────────────────▼──────────────────┐           │
│     │ Cerca match in CODEOWNERS          │           │
│     │ (dal pattern più specifico          │           │
│     │  al meno specifico, ultima match   │           │
│     │  vince)                            │           │
│     └─────────────────┬──────────────────┘           │
│                       │                              │
│     ┌─────────────────▼──────────────────┐           │
│     │ Assegna reviewers automaticamente  │           │
│     └─────────────────┬──────────────────┘           │
│                       │                              │
│     ┌─────────────────▼──────────────────┐           │
│     │ Se branch protection richiede      │           │
│     │ "Require review from Code Owners"  │           │
│     │ → blocca merge senza approvazione  │           │
│     │   di almeno un CODEOWNER           │           │
│     └────────────────────────────────────┘           │
└──────────────────────────────────────────────────────┘
```

**Regole di priorità CODEOWNERS:**
- L'ultimo pattern che matcha un file vince (bottom-up)
- Le directory più specifiche sovrascrivono quelle generiche
- Pattern senza owner (riga vuota) rimuovono l'ownership

---

## Organizations, Teams e Permessi

### Livelli di Permesso Repository

| Livello | Read | Triage | Write | Maintain | Admin |
|---------|------|--------|-------|----------|-------|
| Vedere codice / issues / PR | ✅ | ✅ | ✅ | ✅ | ✅ |
| Clonare e fork | ✅ | ✅ | ✅ | ✅ | ✅ |
| Gestire issues e label | ❌ | ✅ | ✅ | ✅ | ✅ |
| Pushare codice | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gestire branch protection | ❌ | ❌ | ❌ | ✅ | ✅ |
| Gestire settings del repo | ❌ | ❌ | ❌ | ❌ | ✅ |
| Eliminare il repo | ❌ | ❌ | ❌ | ❌ | ✅ |

### Gestione Teams

```bash
# Creare un team
gh api orgs/{org}/teams -X POST -f name="backend-team" \
    -f description="Backend developers" -f privacy="closed"

# Aggiungere membri
gh api orgs/{org}/teams/{team}/memberships/{username} -X PUT -f role="member"

# Assegnare un team a un repository
gh api orgs/{org}/teams/{team}/repos/{owner}/{repo} -X PUT \
    -f permission="push"

# Struttura team nidificata
# engineering (parent)
#   ├── backend-team (child)
#   ├── frontend-team (child)
#   └── devops-team (child)
# I child team ereditano i permessi del parent (ma possono aggiungerne)
```

### Audit Log

L'audit log registra tutte le azioni amministrative nell'organizzazione. Essenziale per compliance (SOC 2, GDPR, HIPAA).

```bash
# Consultare l'audit log via API
gh api orgs/{org}/audit-log --paginate \
    --jq '.[] | "\(.created_at) \(.action) \(.actor)"'

# Filtri comuni
gh api "orgs/{org}/audit-log?phrase=action:org.update_member" --paginate
gh api "orgs/{org}/audit-log?phrase=action:repo.destroy" --paginate
gh api "orgs/{org}/audit-log?phrase=actor:username" --paginate

# Streaming dell'audit log (Enterprise Cloud)
# Settings → Audit log → Log streaming
# Destinazioni supportate: Azure Blob, AWS S3, Datadog, Splunk, Google Cloud
```

---

## Issues e Project Management

### Issues

```bash
# Creare issue
gh issue create --title "Bug: login failure on Safari" \
    --body "Steps to reproduce: ..." --label "bug,priority:high" --assignee "mrossi"

# Elencare issues
gh issue list
gh issue list --label "bug" --state open
gh issue list --assignee "@me"

# Visualizzare
gh issue view 42

# Chiudere
gh issue close 42 --comment "Fixed in #45"

# Trasferire a un altro repository
gh issue transfer 42 owner/other-repo

# Pin di un issue importante (max 3 pin per repo)
gh api repos/{owner}/{repo}/issues/42/pin -X POST

# Cercare issues con query avanzate
gh issue list --search "is:open label:bug sort:updated-desc"
gh issue list --search "no:assignee label:good-first-issue"
```

### Issue Template con YAML Forms

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Bug Report
description: Report a bug
labels: ["bug"]
assignees: []
body:
  - type: markdown
    attributes:
      value: "## Informazioni sul Bug"

  - type: textarea
    id: description
    attributes:
      label: Descrizione del bug
      description: Una descrizione chiara del problema
      placeholder: "Cosa succede? Cosa ti aspettavi?"
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: Passi per riprodurre
      description: Elenca i passi per riprodurre il problema
      value: |
        1. Vai a '...'
        2. Clicca su '...'
        3. Scrolla fino a '...'
        4. Vedi l'errore
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Gravità
      options:
        - Critical
        - High
        - Medium
        - Low
    validations:
      required: true

  - type: input
    id: version
    attributes:
      label: Versione
      description: Quale versione dell'applicazione?
      placeholder: "v1.2.3"

  - type: dropdown
    id: browser
    attributes:
      label: Browser
      multiple: true
      options:
        - Chrome
        - Firefox
        - Safari
        - Edge
        - Altro

  - type: textarea
    id: logs
    attributes:
      label: Log / Screenshot
      description: Allega log o screenshot rilevanti
      render: bash

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: Ho cercato issue duplicati
          required: true
        - label: Ho provato con l'ultima versione
```

### GitHub Projects (v2)

```bash
# Projects v2 usa viste personalizzabili (Board, Table, Roadmap)

# Creare progetto
gh project create --owner "@me" --title "Sprint 2024-Q1"

# Viste tipiche:
# Board (Kanban): Todo → In Progress → Review → Done
# Table: con campi custom (Priority, Sprint, Estimate)
# Roadmap: timeline con date

# Automazione:
# - Issue creata → aggiunta automaticamente a "Todo"
# - PR linked → sposta a "In Progress"
# - PR merged → sposta a "Done"

# Campi custom: Priority, Sprint, Effort, Team

# Elencare progetti
gh project list --owner "@me"
gh project list --owner "my-org"

# Aggiungere un item al progetto
gh project item-add <project-number> --owner "@me" --url <issue-or-pr-url>
```

### Projects v2: Automazioni Built-in

| Trigger | Azione | Configurazione |
|---------|--------|---------------|
| Issue aperto | Aggiungi a progetto, imposta status "Todo" | Settings → Workflows |
| PR aperta | Aggiungi a progetto, imposta status "In Progress" | Settings → Workflows |
| PR merged | Imposta status "Done" | Settings → Workflows |
| Issue chiuso | Imposta status "Done" | Settings → Workflows |
| Review richiesta | Imposta status "In Review" | Settings → Workflows |
| Item aggiunto | Imposta campo custom | Settings → Workflows |

---

## Pull Request e Code Review

### Creare e Gestire PR

```bash
# Creare PR
gh pr create --title "Add user authentication" \
    --body "## Summary
- Implement OAuth2 login
- Add session management
- Add logout endpoint

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing on staging" \
    --reviewer "gbianchi,team-leads" --label "feature" --milestone "v1.2"

# Creare PR draft
gh pr create --draft --title "WIP: nuovo sistema di cache"

# Creare PR con base branch diverso da default
gh pr create --base develop --title "Feature per develop"

# Elencare PR
gh pr list
gh pr list --state merged --author "@me"
gh pr list --search "review:required"

# Visualizzare
gh pr view 45
gh pr diff 45
gh pr checks 45    # Stato CI checks

# Review
gh pr review 45 --approve
gh pr review 45 --request-changes --body "Please fix the SQL injection in line 42"
gh pr review 45 --comment --body "Looks good overall, minor suggestion on line 15"

# Merge
gh pr merge 45 --squash --delete-branch
gh pr merge 45 --rebase
gh pr merge 45 --merge

# Merge con auto-merge (completa quando tutti i check passano)
gh pr merge 45 --auto --squash --delete-branch
```

### Opzioni del Comando `gh pr create`

| Opzione | Descrizione |
|---------|-------------|
| `--title <titolo>` | Titolo della PR |
| `--body <testo>` | Corpo della PR (Markdown) |
| `--body-file <path>` | Corpo da file |
| `--base <branch>` | Branch di destinazione |
| `--head <branch>` | Branch sorgente |
| `--reviewer <utenti>` | Reviewers da assegnare (separati da virgola) |
| `--assignee <utenti>` | Assignees |
| `--label <labels>` | Labels (separati da virgola) |
| `--milestone <nome>` | Milestone da associare |
| `--project <nome>` | Project da associare |
| `--draft` | Crea come draft PR |
| `--fill` | Auto-compila titolo e corpo dal commit |
| `--web` | Apre nel browser per completare la creazione |
| `--template <file>` | Usa un template specifico |

### PR Template

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->
## Summary
<!-- Describe your changes -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## Related Issues
<!-- Closes #42, Fixes #13 -->

## Test Plan
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots
<!-- If applicable, add screenshots -->

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] No secrets or credentials in code
- [ ] Performance impact considered
```

### Code Review Best Practices

```
Per il reviewer:
1. Capire il contesto (leggere la descrizione PR e gli issue linked)
2. Verificare: correttezza logica, edge cases, sicurezza, performance
3. Commenti costruttivi con suggerimenti, non solo critiche
4. Distinguere: "must fix" (blocking) vs "nit" (suggestion)
5. Approvare quando è "buono abbastanza", non quando è "perfetto"

Per l'autore:
1. PR piccole (< 400 righe) → review più efficace
2. Descrizione chiara con contesto e test plan
3. Self-review prima di richiedere review
4. Rispondere a tutti i commenti
5. Non pushare force durante la review (rende difficile seguire le modifiche)
```

### Merge Queue

La **Merge Queue** (GitHub Enterprise / Team) automatizza il merge delle PR garantendo che passino tutti i check **dopo** essere state rebased sull'ultimo main:

```
┌─────────────────────────────────────────────────────┐
│                  MERGE QUEUE                        │
│                                                     │
│  PR #45 ──► Queue ──► Rebase su main ──► CI run    │
│  PR #46 ──► Queue ──► Rebase su PR#45 ──► CI run   │
│  PR #47 ──► Queue ──► Rebase su PR#46 ──► CI run   │
│                                    │                │
│                              ┌─────▼──────┐         │
│                              │ CI passa?  │         │
│                              └─────┬──────┘         │
│                                    │                │
│                        ┌──── Sì ───┼─── No ────┐    │
│                        ▼           │           ▼    │
│                   Fast-forward     │      PR rimossa│
│                   merge a main     │      dalla coda│
└─────────────────────────────────────────────────────┘
```

```bash
# Abilitare merge queue:
# Settings → General → Pull Requests → ✅ Allow merge queue

# Aggiungere una PR alla merge queue
gh pr merge 45 --merge-queue

# La merge queue può raggruppare più PR (batch mode)
# per ridurre il numero di CI run
```

---

## GitHub CLI (gh)

### Installazione e Autenticazione

```bash
# Installazione
# macOS
brew install gh
# Linux (apt)
sudo apt install gh
# Windows
winget install --id GitHub.cli

# Autenticazione
gh auth login                          # Interattivo (browser o token)
gh auth login --with-token < token.txt # Da file
gh auth status                         # Verificare lo stato
gh auth refresh --scopes admin:org     # Aggiungere scope OAuth

# Impostare l'editor preferito
gh config set editor "code --wait"

# Impostare il protocollo preferito (ssh vs https)
gh config set git_protocol ssh
```

### Comandi Principali

```bash
# REPOSITORY
gh repo create                         # Interattivo
gh repo clone owner/repo
gh repo fork owner/repo --clone
gh repo view --web                     # Apre nel browser
gh repo list owner                     # Lista repo di un utente/org
gh repo archive owner/repo             # Archiviare un repo
gh repo rename new-name                # Rinominare

# ISSUES
gh issue create
gh issue list --state open --label "bug"
gh issue view 42
gh issue close 42
gh issue reopen 42
gh issue edit 42 --add-label "priority:high"
gh issue transfer 42 owner/other-repo

# PULL REQUESTS
gh pr create
gh pr list
gh pr view 45
gh pr checkout 45                      # Checkout locale di una PR
gh pr diff 45
gh pr merge 45 --squash --delete-branch
gh pr ready 45                         # Segna come ready (era draft)
gh pr close 45                         # Chiudere senza merge
gh pr reopen 45                        # Riaprire

# WORKFLOW (GitHub Actions)
gh run list                            # Elencare esecuzioni workflow
gh run view 12345                      # Dettaglio
gh run watch 12345                     # Segui in tempo reale
gh run rerun 12345                     # Rieseguire
gh run rerun 12345 --failed            # Rieseguire solo i job falliti
gh workflow list                       # Elencare workflow
gh workflow run deploy.yml             # Trigger manuale
gh workflow run deploy.yml -f env=staging  # Con input

# RELEASES
gh release create v1.2.0 --title "Release 1.2.0" --notes "Changelog..."
gh release create v1.2.0 --generate-notes   # Note auto-generate
gh release create v1.2.0 --prerelease       # Pre-release
gh release create v1.2.0 ./build/*.zip      # Con asset allegati
gh release list
gh release download v1.2.0
gh release delete v1.2.0 --yes              # Eliminare release

# GIST
gh gist create file.txt --public --desc "My snippet"
gh gist create file1.txt file2.py           # Multi-file gist
gh gist list
gh gist view <id>
gh gist edit <id>

# SEARCH
gh search repos "language:python stars:>1000"
gh search issues "label:bug state:open repo:owner/repo"
gh search code "func main" --language go
gh search prs "review:approved author:@me"

# API DIRETTA
gh api repos/{owner}/{repo}/issues
gh api repos/{owner}/{repo}/pulls/45/reviews
gh api graphql -f query='{ viewer { login } }'

# ALIAS CUSTOM
gh alias set co 'pr checkout'
gh alias set prc 'pr create --fill'
gh alias set mine 'issue list --assignee @me'
gh alias set review 'pr list --search "review-requested:@me"'
```

### Estensioni `gh`

```bash
# Installare estensioni dalla community
gh extension install dlvhdr/gh-dash       # Dashboard TUI
gh extension install mislav/gh-branch     # Gestione branch interattiva
gh extension install github/gh-copilot    # Copilot CLI

# Elencare estensioni installate
gh extension list

# Cercare estensioni
gh extension search "dashboard"

# Aggiornare tutte
gh extension upgrade --all
```

---

## GitHub API

### REST API

```bash
# Autenticazione: token (PAT) o GitHub App

# Esempi con gh api (usa il token di gh auth)
gh api repos/owner/repo
gh api repos/owner/repo/issues --method POST \
    -f title="Bug report" -f body="Description" -f labels[]="bug"

# Con curl
curl -H "Authorization: token ghp_xxxx" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/owner/repo/issues

# Paginazione
gh api repos/owner/repo/issues --paginate --jq '.[].title'

# Rate limit
gh api rate_limit
# Limite: 5000 richieste/ora per token autenticato
# 60 richieste/ora senza autenticazione
```

### Rate Limiting in Dettaglio

```
┌─────────────────────────────────────────────────────┐
│               GITHUB API RATE LIMITS                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Tipo Autenticazione        Limite                  │
│  ──────────────────────     ─────────────           │
│  Non autenticato            60 req/ora              │
│  PAT (classic)              5,000 req/ora           │
│  PAT (fine-grained)         5,000 req/ora           │
│  GitHub App (installation)  5,000 req/ora + scaling │
│  GitHub App (user token)    5,000 req/ora           │
│  GITHUB_TOKEN (Actions)     1,000 req/ora           │
│                                                     │
│  Secondary rate limit:                              │
│  - Max 100 richieste concorrenti                    │
│  - Max 900 punti/minuto per content-creating        │
│  - Max 90 secondi di CPU/minuto (search)            │
│                                                     │
│  Header da controllare:                             │
│  X-RateLimit-Limit: 5000                            │
│  X-RateLimit-Remaining: 4998                        │
│  X-RateLimit-Reset: 1672531200 (Unix timestamp)     │
│  X-RateLimit-Used: 2                                │
│  Retry-After: 60 (se rate limited)                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

```bash
# Verificare il rate limit
gh api rate_limit --jq '.rate | "Remaining: \(.remaining)/\(.limit)"'

# Gestire la paginazione con jq
gh api repos/{owner}/{repo}/issues --paginate \
    --jq '.[] | {number, title, state}' | head -50

# Paginazione manuale con Link header
curl -I -H "Authorization: token ghp_xxxx" \
    "https://api.github.com/repos/owner/repo/issues?per_page=100&page=1"
# Link: <...?page=2>; rel="next", <...?page=5>; rel="last"
```

### GraphQL API

```bash
# Più efficiente del REST per query complesse

gh api graphql -f query='
  query {
    repository(owner: "owner", name: "repo") {
      issues(first: 10, states: OPEN) {
        nodes {
          title
          number
          labels(first: 5) {
            nodes { name }
          }
        }
      }
    }
  }
'

# Esempio: ottenere PR con review e check status
gh api graphql -f query='
  query {
    repository(owner: "owner", name: "repo") {
      pullRequests(first: 5, states: OPEN) {
        nodes {
          title
          number
          reviews(first: 5) {
            nodes { state author { login } }
          }
          commits(last: 1) {
            nodes {
              commit {
                statusCheckRollup {
                  state
                }
              }
            }
          }
        }
      }
    }
  }
'

# Vantaggio GraphQL: una singola richiesta che in REST
# richiederebbe 5+ chiamate (PR list + reviews + checks per ciascuna)
```

### Webhooks

```bash
# Webhooks notificano il tuo server quando avvengono eventi su GitHub
# Settings → Webhooks → Add webhook

# Payload URL: https://myserver.com/github-webhook
# Content type: application/json
# Secret: shared secret per validare le richieste
# Events: push, pull_request, issues, release, etc.

# Eventi più comuni:
# push               → Nuovo push a un branch
# pull_request        → PR aperta/chiusa/merged/review
# issues              → Issue creata/chiusa/modificata
# release             → Nuova release
# workflow_run        → Workflow completato
# check_run           → Check completato
# deployment          → Deploy avviato
# deployment_status   → Stato deploy aggiornato

# Validazione webhook (Python esempio):
# import hmac, hashlib
# signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
# expected = f"sha256={signature}"
# if not hmac.compare_digest(expected, request.headers['X-Hub-Signature-256']):
#     return 403
```

---

## Sicurezza GitHub

### Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "devops-team"
    labels:
      - "dependencies"
    # Raggruppare aggiornamenti correlati in una singola PR
    groups:
      dev-dependencies:
        patterns:
          - "@types/*"
          - "eslint*"
          - "prettier"
        update-types:
          - "minor"
          - "patch"

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "monthly"
```

### Secret Scanning e CodeQL

```bash
# SECRET SCANNING (automatico su repo pubblici, opt-in su privati)
# Rileva credenziali committate per errore: API keys, token, password
# Settings → Code security → Secret scanning: Enabled

# Pattern supportati (200+ tipi):
# - GitHub PAT (ghp_*, gho_*, ghu_*, ghs_*, ghr_*)
# - AWS Access Key ID / Secret
# - Azure Storage Key
# - Google Cloud API Key
# - Stripe API Key
# - Slack Token
# - Database connection strings
# E molti altri...

# CODEQL (analisi statica del codice per vulnerabilità)
# Settings → Code security → Code scanning: Enable CodeQL
# Oppure configurare workflow Actions:
# .github/workflows/codeql.yml (template disponibile in Actions tab)

# PUSH PROTECTION
# Blocca push che contengono segreti rilevati
# Settings → Code security → Push protection: Enabled

# Se un push viene bloccato:
# remote: error: GH013: Repository rule violations found
# Opzioni:
# 1. Rimuovere il segreto e ri-pushare
# 2. Bypassare (se falso positivo) — richiede permesso

# SECURITY ADVISORIES
# Repository → Security → Advisories
# Per segnalare vulnerabilità in modo responsabile

# SECURITY.md
# Indica come segnalare vulnerabilità al progetto
```

### 2FA Obbligatoria

Dal 2024, GitHub richiede 2FA per tutti gli account che contribuiscono a codice. Opzioni disponibili:

- **TOTP App** (Authy, 1Password, Bitwarden): Consigliata
- **SMS**: Meno sicuro (vulnerabile a SIM swapping)
- **Security Key** (YubiKey, Titan): Più sicuro
- **Passkey**: Supporto nativo dal 2023
- **GitHub Mobile**: Notifica push per approvazione

```bash
# Verificare stato 2FA via API
gh api user --jq '.two_factor_authentication'

# Configurare: Settings → Password and authentication → Enable two-factor authentication
```

---

## GitHub Apps vs Personal Access Tokens

### Confronto

```
┌──────────────────────────────────────────────────────────────┐
│              GitHub Apps vs PAT vs Fine-Grained PAT          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Caratteristica    │ Classic PAT  │ Fine-Grained │ App      │
│  ──────────────────┼──────────────┼──────────────┼──────────│
│  Scopo             │ Utente       │ Utente       │ Servizio │
│  Permessi          │ Coarse       │ Granulari    │ Granulari│
│  Scadenza          │ Opzionale    │ Obbligatoria │ 1 ora    │
│  Rate limit        │ 5000/h       │ 5000/h       │ 5000/h+  │
│  IP restrictions   │ No           │ No           │ Sì       │
│  Audit trail       │ Limitato     │ Sì           │ Completo │
│  Multi-repo scope  │ Tutto/niente │ Per-repo     │ Per-repo │
│  Rotazione auto    │ No           │ No           │ Sì       │
│  Webhook events    │ No           │ No           │ Sì       │
│                                                              │
│  Raccomandazione:                                            │
│  ─ Automazione CI → GitHub App o GITHUB_TOKEN                │
│  ─ Script personali → Fine-Grained PAT                      │
│  ─ Classic PAT → Deprecare quando possibile                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Creare un Fine-Grained PAT

```bash
# Settings → Developer settings → Personal access tokens → Fine-grained tokens

# Selezionare:
# - Resource owner: tuo utente o organizzazione
# - Repository access: Only select repositories (scegliere i repo)
# - Permissions: selezionare solo ciò che serve
#   Es. per CI: Contents (read/write), Pull requests (read/write)

# Usare nelle automazioni:
export GITHUB_TOKEN="github_pat_xxxx..."
gh auth login --with-token <<< "$GITHUB_TOKEN"
```

---

## Funzionalità Avanzate

### GitHub Pages

```bash
# Hosting statico gratuito da un repository

# Settings → Pages → Source: Deploy from a branch (main, /docs o /)
# O: GitHub Actions (per build con Jekyll, Hugo, Next.js, etc.)

# URL: https://username.github.io/repo-name
# Custom domain: Settings → Pages → Custom domain
# HTTPS automatico con Let's Encrypt

# Jekyll (default, build automatico):
# Aggiungere un file _config.yml nella root

# Static site con Actions (esempio per Hugo):
# .github/workflows/pages.yml
# name: Deploy Hugo site
# on:
#   push:
#     branches: [main]
# jobs:
#   build:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v4
#       - uses: peaceiris/actions-hugo@v2
#         with: { hugo-version: 'latest' }
#       - run: hugo --minify
#       - uses: actions/upload-pages-artifact@v3
#         with: { path: ./public }
#   deploy:
#     needs: build
#     permissions: { pages: write, id-token: write }
#     environment: { name: github-pages }
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/deploy-pages@v4
```

### GitHub Packages e Container Registry

```bash
# Pubblicare pacchetti npm, Docker, Maven, NuGet, RubyGems

# Docker (GHCR - GitHub Container Registry)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker build -t ghcr.io/owner/image:latest .
docker push ghcr.io/owner/image:latest

# Rendere un package pubblico:
# Packages → Package settings → Change visibility → Public

# npm
echo "//npm.pkg.github.com/:_authToken=$GITHUB_TOKEN" >> .npmrc
echo "@owner:registry=https://npm.pkg.github.com" >> .npmrc
npm publish

# Pulizia automatica di versioni vecchie (via API)
gh api orgs/{org}/packages/container/{package}/versions --paginate \
    --jq '.[] | select(.metadata.container.tags | length == 0) | .id' \
    | xargs -I{} gh api orgs/{org}/packages/container/{package}/versions/{} -X DELETE
```

### GitHub Codespaces

```bash
# Ambiente di sviluppo cloud (VS Code nel browser o locale)
# Configurazione: .devcontainer/devcontainer.json

# devcontainer.json esempio:
# {
#   "name": "Node.js Dev",
#   "image": "mcr.microsoft.com/devcontainers/javascript-node:18",
#   "features": {
#     "ghcr.io/devcontainers/features/docker-in-docker:2": {},
#     "ghcr.io/devcontainers/features/github-cli:1": {}
#   },
#   "postCreateCommand": "npm install",
#   "customizations": {
#     "vscode": {
#       "extensions": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"],
#       "settings": { "editor.formatOnSave": true }
#     }
#   },
#   "forwardPorts": [3000, 5432],
#   "portsAttributes": {
#     "3000": { "label": "App", "onAutoForward": "openBrowser" }
#   }
# }

gh codespace create --repo owner/repo --machine largePremiumLinux
gh codespace create --repo owner/repo --devcontainer-path .devcontainer/devcontainer.json
gh codespace list
gh codespace ssh -c codespace-name
gh codespace stop -c codespace-name
gh codespace delete -c codespace-name

# Prebuilds (riducono il tempo di avvio):
# Settings → Codespaces → Set up prebuild
# Trigger: push su branch, configurazione cambiata
```

### GitHub Discussions

```bash
# Forum integrato nel repository per Q&A, annunci, idee
# Settings → Features → ✅ Discussions

# Categorie predefinite:
# - Announcements (solo maintainer)
# - General (discussioni aperte)
# - Ideas (proposte feature)
# - Q&A (domande con risposte accettate)
# - Show and Tell (demo, showcase)

# Via API
gh api repos/{owner}/{repo}/discussions --jq '.[].title'
```

---

## Anti-Pattern

### 1. Usare Classic PAT con Scope `repo` per Tutto

Classic PAT con scope `repo` dà accesso completo a TUTTI i repository. Usare Fine-Grained PAT con permessi per-repository.

### 2. Non Configurare Branch Protection su `main`

Senza protezione, chiunque con write access può pushare direttamente su main, fare force push o eliminare il branch. Sempre abilitare almeno: PR obbligatoria + 1 approvazione + status checks.

### 3. Committare Segreti e Poi Fare `git rm`

`git rm` rimuove il file dal working tree ma il segreto resta nella cronologia. Serve un rewrite della cronologia con `git filter-repo` o BFG Repo-Cleaner, più rotazione del segreto.

### 4. Repository Monolitico Senza CODEOWNERS

In team grandi, senza CODEOWNERS chiunque può approvare qualsiasi PR. Risultato: review superficiali, bug in produzione. Definire ownership per area.

### 5. Issues Senza Template

Issues senza struttura richiedono molti round-trip per raccogliere informazioni. Template YAML con campi obbligatori riducono il lavoro per tutti.

### 6. PR Giganti (> 1000 righe)

PR oltre 1000 righe ricevono review superficiali ("LGTM"). Dividere in PR più piccole, ciascuna con un obiettivo chiaro.

### 7. Ignorare Dependabot

Lasciare le PR di Dependabot in coda senza mergiare accumula debito di sicurezza. Configurare auto-merge per patch updates e review settimanale per minor/major.

### 8. Non Usare `gh` CLI per Operazioni Ripetitive

Aprire il browser per ogni operazione (creare issue, controllare CI, fare review) è lento. `gh` automatizza tutto dalla shell.

### 9. Fork Stale Non Sincronizzati

Forkare un repo e non sincronizzarlo per mesi rende i contributi molto difficili. Sincronizzare regolarmente: `gh repo sync owner/fork`.

### 10. Webhook Senza Validazione del Secret

Webhook senza validazione della firma HMAC permettono a chiunque di inviare payload falsi al server. Sempre validare `X-Hub-Signature-256`.

---

## Best Practices

1. **Branch protection su main**: PR obbligatoria, almeno 1 approvazione, CI passing
2. **CODEOWNERS per ogni area**: garantisce che le persone giuste facciano review
3. **Templates per Issues e PR**: standardizzano il formato e riducono informazioni mancanti
4. **Dependabot attivo**: aggiornamenti automatici delle dipendenze, sicurezza inclusa
5. **Secret scanning + push protection**: previene leak di credenziali
6. **Squash merge**: mantiene cronologia main pulita e leggibile
7. **Releases con changelog**: tag semantico + note generate automaticamente
8. **GitHub CLI per automazione**: `gh` è più veloce dell'interfaccia web per operazioni ripetitive
9. **Fine-Grained PAT**: migrare dai Classic PAT per permessi granulari
10. **Audit log monitoring**: configurare streaming per compliance e incident response
11. **Merge Queue per team grandi**: evita merge di PR con main non aggiornato
12. **Rulesets organizzativi**: regole uniformi su tutti i repository dell'organizzazione
13. **Codespaces con prebuild**: ambienti di sviluppo pronti in secondi
14. **GitHub Projects v2**: project management senza strumenti esterni
15. **2FA con security key**: livello di sicurezza più alto per tutti i membri

---

## Troubleshooting

### 1. PR Merge Bloccato — Status Checks Non Passano

```bash
# Sintomo: "Some checks haven't completed yet" anche se la CI è passata
# Causa: il nome del check nella branch protection non corrisponde
#         a quello generato dal workflow

# Diagnosi
gh pr checks 45
gh api repos/{owner}/{repo}/commits/{sha}/status
gh api repos/{owner}/{repo}/commits/{sha}/check-runs --jq '.check_runs[].name'

# Soluzione: aggiornare il nome del check nella branch protection
# Settings → Branches → Edit rule → Status checks
# Cercare il nome esatto del check (case-sensitive)
```

### 2. Push Rifiutato — Secret Detected

```bash
# Sintomo: remote: error: GH013: Repository rule violations found
# Causa: push protection ha rilevato un segreto nel codice

# Soluzione 1: Rimuovere il segreto
git reset --soft HEAD~1
# Rimuovere il segreto dal file
git add -A && git commit -m "fix: rimuovere credenziali"

# Soluzione 2: Se è un falso positivo
# Seguire il link nel messaggio di errore per bypassare
# (richiede permesso "bypass secret scanning push protection")
```

### 3. Dependabot PR con Conflitti

```bash
# Sintomo: Dependabot PR mostra "This branch has conflicts"
# Causa: il lockfile è stato modificato sia su main che da Dependabot

# Soluzione: chiedere a Dependabot di ricreare la PR
# Commentare sulla PR: @dependabot recreate
# Altri comandi: @dependabot rebase, @dependabot merge
```

### 4. GitHub Actions Workflow Non Si Attiva

```bash
# Cause comuni:
# 1. Il file workflow non è su default branch (per trigger push/PR)
# 2. Errore di sintassi nel YAML
# 3. Workflow disabilitato

# Diagnosi
gh workflow list
gh workflow view deploy.yml

# Abilitare un workflow disabilitato
gh workflow enable deploy.yml

# Verificare la sintassi YAML
# Usare il VS Code extension: GitHub Actions
# O validare online: https://rhysd.github.io/actionlint/
```

### 5. Rate Limit Exceeded sull'API

```bash
# Sintomo: 403 Forbidden con messaggio "API rate limit exceeded"

# Diagnosi
gh api rate_limit --jq '.rate'

# Soluzioni:
# 1. Aspettare il reset (controllare X-RateLimit-Reset header)
# 2. Usare conditional requests (If-None-Match / ETag)
# 3. Usare GraphQL invece di REST (una query vs molte richieste)
# 4. Per CI: usare GITHUB_TOKEN invece di PAT (rate limit separato)
# 5. Per app: migrare a GitHub App (rate limit più alto e scaling)
```

### 6. Clone Lento per Repository Grande

```bash
# Soluzione 1: Shallow clone
git clone --depth 1 https://github.com/org/large-repo.git

# Soluzione 2: Partial clone
git clone --filter=blob:none https://github.com/org/large-repo.git

# Soluzione 3: Sparse checkout
git clone --filter=blob:none --sparse https://github.com/org/large-repo.git
cd large-repo
git sparse-checkout set src/my-module
```

### 7. CODEOWNERS Non Assegna Reviewers

```bash
# Cause comuni:
# 1. File CODEOWNERS nella posizione sbagliata (deve essere in .github/, root, o docs/)
# 2. Utente/team non ha accesso al repository
# 3. Errore di sintassi nel pattern

# Diagnosi: GitHub mostra errori nel tab "Settings → Branches"
# Verifica: creare una PR di test e controllare i reviewers assegnati

# Il pattern deve usare il formato GitHub (@username o @org/team)
# Non email, non nomi display
```

### 8. Fork Non Sincronizzato con Upstream

```bash
# Sintomo: "This branch is X commits behind upstream:main"

# Soluzione 1: Via web
# Cliccare "Sync fork" → "Update branch" nella pagina del fork

# Soluzione 2: Via CLI
gh repo sync owner/fork -b main

# Soluzione 3: Manuale
git remote add upstream https://github.com/original/repo.git
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### 9. GitHub Pages Non Si Aggiorna

```bash
# Cause comuni:
# 1. Build Jekyll fallita (controllare Actions tab)
# 2. File _config.yml con errore di sintassi
# 3. Branch o directory sorgente configurati erroneamente
# 4. Cache del CDN (aspettare qualche minuto)

# Diagnosi
gh api repos/{owner}/{repo}/pages --jq '.status'
gh run list --workflow pages-build-deployment
```

### 10. Webhook Non Riceve Eventi

```bash
# Diagnosi: Settings → Webhooks → Recent Deliveries
# Controllare response code e body

# Cause comuni:
# 1. URL non raggiungibile (firewall, DNS, HTTPS)
# 2. Timeout (GitHub aspetta max 10 secondi per risposta)
# 3. Secret configurato erroneamente
# 4. Eventi non selezionati

# Test manuale
gh api repos/{owner}/{repo}/hooks --jq '.[].config.url'
# Redeliver un webhook fallito dall'interfaccia web
```

### 11. PR Review Stale dopo Force Push

```bash
# Sintomo: le review vengono dismiss dopo un force push
# Causa: "Dismiss stale reviews" è abilitato nella branch protection

# Soluzione: non fare force push durante la review
# Se necessario, pushare commit incrementali
# Se il force push è intenzionale, richiedere nuova review

# Alternativa: disabilitare "Dismiss stale reviews" se il team
# ha fiducia nel processo (non consigliato per team grandi)
```

### 12. Two-Factor Authentication Locked Out

```bash
# Se si perde accesso al 2FA:
# 1. Usare recovery codes (generati durante il setup)
# 2. Usare un dispositivo verificato per generare TOTP
# 3. Contattare GitHub Support con verifica identità

# Prevenzione:
# - Salvare i recovery codes in un password manager
# - Configurare più metodi 2FA (TOTP + security key)
# - Configurare fallback number per SMS
```

### 13. GitHub Actions — Permission Denied nell'Organizzazione

```bash
# Sintomo: workflow fallisce con "Resource not accessible by integration"
# Causa: permessi GITHUB_TOKEN restrittivi a livello org

# Soluzione org-level:
# Organization → Settings → Actions → General →
# Workflow permissions → Read and write permissions

# Soluzione per-workflow (esplicita):
# permissions:
#   contents: write
#   pull-requests: write
#   issues: write
```

### 14. Repository Archived Accidentally

```bash
# Soluzione: unarchive via API
gh api repos/{owner}/{repo} -X PATCH -F archived=false

# Via web: Settings → Danger Zone → Unarchive this repository
```

### 15. Errore "Repository Not Found" con Token Valido

```bash
# Cause:
# 1. PAT non ha accesso al repository (Fine-Grained PAT: controllare repo list)
# 2. SSO non autorizzato (Enterprise Cloud: cliccare "Authorize" vicino al token)
# 3. Repository è privato e il token non ha scope 'repo'

# Diagnosi
gh auth status
gh api repos/{owner}/{repo} 2>&1

# Per Enterprise con SSO:
# Settings → Developer settings → Personal access tokens →
# Cliccare "Configure SSO" vicino al token → Authorize per l'org
```

### 16. Branch Protection Rules Non Si Applicano ad Admin

```bash
# Causa: "Include administrators" non è abilitato

# Soluzione:
# Settings → Branches → Edit rule →
# ✅ Do not allow bypassing the above settings
# (Precedentemente: "Include administrators")
```

---

## FAQ

### 1. Qual è la differenza tra GitHub Free e Team per le organizzazioni?

Team aggiunge: branch protection rules avanzate (CODEOWNERS obbligatorio, draft PR, multiple reviewers), 3000 minuti Actions (vs 2000), Pages da repo privati, e supporto email. Per team professionali, Team è il minimo. Free va bene per progetti open source o individuali.

### 2. Posso migrare da GitLab/Bitbucket a GitHub mantenendo la cronologia?

Sì. `gh repo create --source <local-path> --push` pusha un repo locale esistente. Per migrare issues, PR, e wiki, usare i migration tool ufficiali: `gh importer` per GitLab, o gli API endpoint di importazione. La cronologia Git si mantiene integralmente.

### 3. GitHub Actions è gratuito per repository pubblici?

Sì, completamente gratuito e senza limiti di minuti per repository pubblici. Per repository privati, ogni piano ha un budget mensile di minuti (Free: 2000, Team: 3000, Enterprise: 50000). I runner self-hosted non consumano minuti.

### 4. Come funziona il billing di GitHub Actions per OS diversi?

I minuti hanno un moltiplicatore per OS: Linux = 1x, Windows = 2x, macOS = 10x. Quindi 1000 minuti su macOS equivalgono a 10000 minuti del budget. Per questo motivo, eseguire la CI su Linux quando possibile e usare macOS solo per build iOS/macOS specifiche.

### 5. Qual è la dimensione massima di un repository GitHub?

Il limite soft è 1 GB, il limite hard è 5 GB. I singoli file hanno un limite di 100 MB (usare Git LFS per file più grandi). I push sono limitati a 2 GB. Per repository molto grandi, usare partial clone e sparse checkout.

### 6. Come posso rendere un repository privato pubblico (o viceversa)?

Settings → General → Danger Zone → Change visibility. Attenzione: rendere pubblico un repo privato espone tutta la cronologia, inclusi eventuali segreti committati per errore. Eseguire una pulizia della cronologia prima della pubblicazione.

### 7. Cos'è il GITHUB_TOKEN e come si differenzia da un PAT?

`GITHUB_TOKEN` è un token automatico generato per ogni workflow run in GitHub Actions. Ha scope limitato al repository corrente, scade alla fine del workflow, e ha un rate limit separato (1000 req/ora). Non richiede configurazione manuale. Un PAT è un token personale con scope configurabile, usato per automazioni esterne.

### 8. Come funziona il draft PR e quando usarlo?

Un draft PR è una PR non pronta per la review. Non può essere mergiata e i CODEOWNERS non vengono notificati. Usarlo per: ottenere feedback anticipato, mostrare il lavoro in corso, eseguire la CI prima della review formale. Convertire a "Ready for review" quando pronto.

### 9. Posso recuperare un repository eliminato?

Sì, entro 90 giorni per i repository privati di un'organizzazione (Settings → Deleted repositories → Restore). Per account personali o dopo 90 giorni, contattare GitHub Support. Non c'è garanzia di recupero per repository pubblici eliminati.

### 10. Come gestisco i segreti per GitHub Actions?

Settings → Secrets and variables → Actions. I segreti sono criptati e non visibili dopo il salvataggio. Usare secrets per-environment per deploy multi-stage (staging vs production). Le Actions dei fork non hanno accesso ai segreti del repository principale.

### 11. Qual è la differenza tra GitHub Projects v1 e v2?

Projects v1 (classico) è deprecato. Projects v2 offre: viste multiple (Board, Table, Roadmap), campi custom (testo, numero, data, selezione), automazioni built-in, workflows personalizzati, aggregazione cross-repository, e API GraphQL. Migrare a v2 se ancora su v1.

### 12. Come posso forzare tutti i membri dell'org ad usare 2FA?

Organization → Settings → Authentication security → ✅ Require two-factor authentication. I membri senza 2FA vengono rimossi dall'organizzazione (ma possono rientrare dopo aver abilitato 2FA). Dare un periodo di grazia e comunicare in anticipo.

### 13. Cosa sono le GitHub Apps e quando servono?

GitHub Apps sono integrazioni con permessi granulari, rate limit separato, e audit trail completo. Usarle quando: serve automazione non legata a un utente, serve più del rate limit di un PAT, serve un'integrazione installabile da altri. Per script personali, un Fine-Grained PAT è sufficiente.

### 14. Come configuro le notifiche per non essere sommerso?

Settings → Notifications → Custom routing. Configurare: email per menzioni dirette, web per review richieste, disabilitare per watching automatico. Usare `gh` CLI: `gh notification list --filter "reason:mention"`. Fare unwatch dei repo non rilevanti.

### 15. Come gestisco i fork nel contesto di un'organizzazione Enterprise?

Enterprise Cloud permette di configurare la fork policy a livello org: disabilitare fork esterni, permettere solo fork interni, o permettere fork verso organizzazioni specifiche. Settings → Member privileges → Repository forking.

### 16. Esiste un modo per fare backup automatico dei repository GitHub?

Sì, diverse strategie: 1) Mirror clone con cron job (`git clone --mirror` + push a backup remote); 2) GitHub Archive Program (per repo pubblici significativi); 3) Strumenti come `ghbackup` o `github-backup`; 4) GitHub API per esportare issues, wiki, e metadata oltre al codice.

### 17. Come funziona il GitHub Container Registry (GHCR) rispetto a Docker Hub?

GHCR è integrato con GitHub: autenticazione via GITHUB_TOKEN, permessi ereditati dal repository, visibilità configurabile (public/private), nessun rate limit per pull da Actions. Docker Hub ha rate limit aggressivi per utenti free (100 pull/6h). GHCR è preferibile per workflow GitHub Actions.

---

## Riferimenti

- **GitHub Documentation**: https://docs.github.com
- **GitHub CLI Manual**: https://cli.github.com/manual/
- **GitHub REST API**: https://docs.github.com/en/rest
- **GitHub GraphQL API**: https://docs.github.com/en/graphql
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **GitHub Security Features**: https://docs.github.com/en/code-security
- **GitHub Rulesets**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets
- **GitHub Apps Documentation**: https://docs.github.com/en/apps
- **GitHub Codespaces**: https://docs.github.com/en/codespaces
- **GitHub Packages**: https://docs.github.com/en/packages
- **GitHub Projects v2**: https://docs.github.com/en/issues/planning-and-tracking-with-projects

---

## Esercizi

### Esercizio 1: Configurazione Organizzazione e Team

```bash
# Obiettivo: creare una struttura organizzativa completa con team e permessi

# 1. Creare un'organizzazione (via web) e configurare:
#    - 2FA obbligatorio (Settings → Authentication security)
#    - Base permission: Read (Settings → Member privileges)
#    - Fork policy: disabilitare fork esterni

# 2. Creare team con gerarchia:
gh api orgs/MY-ORG/teams -f name="engineering" -f privacy="closed"
gh api orgs/MY-ORG/teams -f name="frontend" -f privacy="closed" -f parent_team_id=PARENT_ID
gh api orgs/MY-ORG/teams -f name="backend" -f privacy="closed" -f parent_team_id=PARENT_ID

# 3. Assegnare repository ai team con permessi differenziati:
gh api orgs/MY-ORG/teams/frontend/repos/MY-ORG/webapp -X PUT -f permission="push"
gh api orgs/MY-ORG/teams/backend/repos/MY-ORG/api-server -X PUT -f permission="push"

# 4. Verificare la struttura:
gh api orgs/MY-ORG/teams --jq '.[].name'
gh api orgs/MY-ORG/teams/frontend/members --jq '.[].login'
```

### Esercizio 2: Repository Setup con Template e Branch Protection

```bash
# Obiettivo: creare un repository da template con governance completa

# 1. Creare un template repository con:
#    - README.md, LICENSE, .gitignore
#    - CONTRIBUTING.md, CODE_OF_CONDUCT.md
#    - .github/ISSUE_TEMPLATE/ (bug_report.md, feature_request.md)
#    - .github/PULL_REQUEST_TEMPLATE.md

# 2. Creare un nuovo repo dal template:
gh repo create my-project --template MY-ORG/template-repo --public

# 3. Configurare branch protection su main:
gh api repos/MY-ORG/my-project/branches/main/protection -X PUT \
  -f "required_status_checks[strict]=true" \
  -f "required_status_checks[contexts][]=ci/test" \
  -f "enforce_admins=true" \
  -f "required_pull_request_reviews[required_approving_review_count]=2" \
  -f "required_pull_request_reviews[dismiss_stale_reviews]=true"

# 4. Creare CODEOWNERS:
# echo "* @MY-ORG/engineering" > CODEOWNERS
# echo "frontend/ @MY-ORG/frontend" >> CODEOWNERS
# echo "backend/ @MY-ORG/backend" >> CODEOWNERS

# 5. Verificare le regole:
gh api repos/MY-ORG/my-project/branches/main/protection --jq '.required_pull_request_reviews'
```

### Esercizio 3: Workflow Pull Request Completo

```bash
# Obiettivo: simulare un ciclo completo di PR con review, feedback e merge

# 1. Creare un feature branch e aprire una PR:
git checkout -b feat/user-auth
echo "auth module" > auth.py
git add auth.py && git commit -m "feat: add user auth module"
git push -u origin feat/user-auth
gh pr create --title "feat: add user authentication" \
  --body "## Summary\n- Adds auth module\n\n## Test Plan\n- [ ] Unit tests\n- [ ] Integration test" \
  --reviewer reviewer-username \
  --label "feature"

# 2. Simulare una review con commenti:
gh pr review --comment --body "Consider using bcrypt for password hashing"

# 3. Rispondere al feedback, pushare un fix:
echo "bcrypt hashing" >> auth.py
git add auth.py && git commit -m "fix: use bcrypt for password hashing"
git push

# 4. Approvare e fare merge con squash:
gh pr review --approve --body "LGTM after bcrypt change"
gh pr merge --squash --delete-branch

# 5. Verificare il risultato:
git checkout main && git pull
git log --oneline -5
```

### Esercizio 4: GitHub CLI Power User

```bash
# Obiettivo: padroneggiare gh per operazioni quotidiane

# 1. Issue management:
gh issue create --title "Bug: login failure" --label "bug,priority:high" --assignee @me
gh issue list --label "bug" --state open
gh issue close 42 --comment "Fixed in PR #45"

# 2. PR dashboard personalizzata:
gh pr list --search "is:open review-requested:@me"
gh pr list --search "is:open draft:false label:ready-for-review"

# 3. Alias personalizzati:
gh alias set prs-review 'pr list --search "is:open review-requested:@me"'
gh alias set my-issues 'issue list --assignee @me --state open'

# 4. API diretta per operazioni avanzate:
gh api repos/:owner/:repo/traffic/views --jq '.views[-7:][] | "\(.timestamp): \(.count)"'
gh api repos/:owner/:repo/stats/contributors --jq '.[0] | "\(.author.login): \(.total) commits"'

# 5. Notifiche filtrate:
gh api notifications --jq '.[] | select(.reason=="review_requested") | .subject.title'
```

### Esercizio 5: Projects v2 e Automazione

```bash
# Obiettivo: creare un project board con campi custom e automazione

# 1. Creare un Project v2 a livello organizzazione:
gh project create --owner MY-ORG --title "Q3 Roadmap"

# 2. Aggiungere campi custom:
#    Via web: Project Settings → Fields
#    - Priority: Single select (P0, P1, P2, P3)
#    - Effort: Number (story points)
#    - Sprint: Iteration (2 settimane)
#    - Team: Single select (Frontend, Backend, DevOps)

# 3. Aggiungere issue al project:
gh project item-add PROJECT_NUMBER --owner MY-ORG --url https://github.com/MY-ORG/repo/issues/1

# 4. Configurare automazioni built-in:
#    - Issue aperta → Status: Todo
#    - PR linked → Status: In Progress
#    - PR merged → Status: Done

# 5. Creare viste personalizzate:
#    - Board view: raggruppato per Status
#    - Table view: filtrato per Sprint corrente
#    - Roadmap view: raggruppato per Team
```

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Documentation**: https://docs.github.com — Hub centrale per tutta la documentazione GitHub.
- **GitHub CLI Manual**: https://cli.github.com/manual/ — Riferimento completo per il comando `gh` con tutti i subcommand.
- **GitHub REST API**: https://docs.github.com/en/rest — Documentazione API REST con esempi per ogni endpoint.
- **GitHub GraphQL API**: https://docs.github.com/en/graphql — API GraphQL per query complesse e mutazioni.
- **GitHub Apps Documentation**: https://docs.github.com/en/apps — Guida alla creazione e configurazione di GitHub Apps.
- **GitHub Security Features**: https://docs.github.com/en/code-security — Overview delle funzionalità di sicurezza (Dependabot, CodeQL, secret scanning).
- **GitHub Codespaces**: https://docs.github.com/en/codespaces — Ambienti di sviluppo cloud-based integrati con GitHub.

### Libri consigliati

- **"Learning GitHub Actions" — Brent Laster** (O'Reilly) — Include capitoli sulla piattaforma GitHub e integrazione con Actions.
- **"GitHub For Dummies" — Sarah Guthals, Phil Haack** (Wiley) — Introduzione completa alla piattaforma per team che adottano GitHub.
- **"Git for Teams" — Emma Jane Hogbin Westby** (O'Reilly) — Focus su collaborazione, code review e workflow di team su GitHub.

---

## Riferimenti Incrociati

| Modulo | File | Relazione |
|--------|------|-----------|
| 12 | [12-github-repository-management.md](12-github-repository-management.md) | Approfondisce la gestione repository: template, rulesets, topics e archiving |
| 13 | [13-github-issues-projects-collaboration.md](13-github-issues-projects-collaboration.md) | Dettaglio su Issues, Projects v2, milestones e automazioni di collaborazione |
| 14 | [14-github-packages-pages-releases.md](14-github-packages-pages-releases.md) | GitHub Packages, Pages e Releases come estensioni della piattaforma |
| 15 | [15-github-api-cli-webhooks.md](15-github-api-cli-webhooks.md) | Approfondimento API REST/GraphQL, webhook e integrazioni programmatiche |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Dependabot, secret scanning e CodeQL come feature di sicurezza della piattaforma |
| 22 | [22-github-copilot-codespaces-enterprise.md](22-github-copilot-codespaces-enterprise.md) | Copilot, Codespaces e funzionalità Enterprise Cloud/Server |

---

## GitHub Copilot — Assistente AI Integrato

### Panoramica dei Piani Copilot

GitHub Copilot è l'assistente AI di GitHub che fornisce suggerimenti di codice in tempo reale, chat contestualizzata e automazione di task di sviluppo. Dal 2025 i piani sono stati ristrutturati per offrire maggiore flessibilità.

| Piano | Prezzo | Target | Caratteristiche Principali |
|-------|--------|--------|---------------------------|
| **Free** | $0 | Individui | 2.000 suggerimenti inline/mese, accesso limitato a chat |
| **Pro** | $10/mese | Sviluppatori individuali | Suggerimenti illimitati, modelli premium, chat avanzata |
| **Pro+** | $39/mese | Power user | Modelli AI avanzati, limiti estesi, $39 in crediti AI mensili |
| **Student** | $0 | Studenti verificati | Completamenti illimitati, modelli aggiuntivi |
| **Business** | $19/utente/mese | Organizzazioni (Free/Team) | Agente cloud Copilot, gestione centralizzata, policy di controllo |
| **Enterprise** | $39/utente/mese | Enterprise Cloud | Tutto Business + personalizzazione knowledge base, analytics avanzati |

### Transizione alla Fatturazione Basata su Utilizzo (Giugno 2026)

A partire dal 1 giugno 2026, GitHub Copilot passa dalla fatturazione basata su richieste a quella basata su utilizzo (usage-based billing). Ogni piano include un'allocazione mensile di **GitHub AI Credits**:

```
┌──────────────────────────────────────────────────────────────┐
│           COPILOT BILLING TRANSITION — GIUGNO 2026           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Cosa cambia:                                                │
│  ─────────────                                               │
│  • Ogni piano include crediti AI mensili                     │
│  • L'utilizzo è calcolato su consumo di token               │
│    (input, output, cached tokens)                            │
│  • I piani a pagamento possono acquistare crediti extra      │
│                                                              │
│  Cosa NON cambia:                                            │
│  ────────────────                                            │
│  • Code completions e next edit suggestions restano          │
│    illimitati per tutti i piani a pagamento                  │
│  • Il meccanismo di conteggio esistente per completamenti    │
│    rimane invariato                                          │
│                                                              │
│  Supporto promozionale:                                      │
│  ──────────────────────                                      │
│  • Clienti Business/Enterprise esistenti ricevono            │
│    crediti promozionali per giugno, luglio, agosto 2026      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Copilot Coding Agent e Workflow Agentici

Nel 2026 GitHub ha introdotto il **Copilot Coding Agent**, un agente software autonomo che opera in background per completare task di sviluppo assegnati, similmente a un collega sviluppatore. Questo agente gestisce task di complessità bassa-media, permettendo al team di concentrarsi su lavori più complessi.

```bash
# Agentic Workflows — workflow descritti in linguaggio naturale
# che il CLI compila in workflow GitHub Actions

# Installare gh CLI con supporto agentic workflows
gh extension install github/gh-aw

# Creare un workflow agentico (file Markdown in .github/workflows/)
# Il file descrive gli obiettivi di automazione in linguaggio naturale
# gh aw compila il Markdown in un .lock.yml eseguibile

# Esempio: compilare un workflow agentico
gh aw compile .github/workflows/auto-review.md

# I workflow agentici supportano:
# - GitHub Copilot
# - Claude (Anthropic)
# - Gemini (Google)
# - OpenAI Codex
# per job event-triggered e schedulati

# Copilot CLI in modalità autopilot (GA da marzo 2026):
# Esegue tool, comandi e iterazioni senza approvazione manuale
# Riservato a task fidati dove l'intervento umano non è necessario
```

**Caratteristiche principali dell'agente:**

- **Esecuzione autonoma**: lavora in background all'interno di GitHub Actions
- **Guardrail di sicurezza**: design security-first con controlli integrati
- **Event-triggered**: risponde a eventi come apertura issue, commenti, PR
- **Scheduled**: esecuzione programmata per task ricorrenti (triage, documentazione, code quality)
- **Multi-provider**: supporta più provider AI, non solo Copilot

### Gestione Agent Skills via CLI

Dal aprile 2026, il comando `gh skill` permette di gestire agent skills:

```bash
# Scoprire skill disponibili
gh skill search "code review"

# Installare una skill
gh skill install owner/skill-repo

# Elencare skill installate
gh skill list

# Pubblicare una skill
gh skill publish

# Le skill sono portabili tra agent host:
# GitHub Copilot, Claude Code, Cursor, Codex, Gemini CLI
```

---

## GitHub Sponsors — Finanziamento Open Source

### Come Funziona GitHub Sponsors

GitHub Sponsors consente alla comunità di sviluppatori di supportare finanziariamente le persone e le organizzazioni che progettano, costruiscono e mantengono i progetti open source da cui dipendono, direttamente su GitHub.

```
┌──────────────────────────────────────────────────────────────┐
│                   GITHUB SPONSORS FLOW                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Sponsor ──► Sceglie tier ──► Pagamento ──► Developer/Org   │
│                                                              │
│  Tier disponibili:                                           │
│  ─────────────────                                           │
│  • Fino a 10 tier one-time (pagamento singolo)               │
│  • Fino a 10 tier mensili (recurring)                        │
│  • Ogni tier con importo e benefit personalizzabili          │
│                                                              │
│  Commissioni:                                                │
│  ────────────                                                │
│  • Sponsorship da account personali: 0% (100% al dev)       │
│  • Sponsorship da account organizzazione: fino al 6%        │
│                                                              │
│  Pagamento:                                                  │
│  ──────────                                                  │
│  • Via conto bancario diretto                                │
│  • Via fiscal host (per organizzazioni senza conto)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Configurazione GitHub Sponsors

```bash
# Requisiti per diventare "sponsored developer":
# 1. Contribuire a un progetto open source
# 2. Risiedere in una regione supportata
# 3. Avere 2FA abilitato
# 4. Completare il profilo sponsorship
# 5. Fornire informazioni bancarie e fiscali

# Passaggi di configurazione:
# Settings → Sponsors → Get started
# 1. Compilare "Profile details" con bio e descrizione
# 2. Sezione "Introduction": descrizione del lavoro finanziato
# 3. Creare i tier di sponsorship con benefit
# 4. Sottomettere informazioni bancarie e fiscali
# 5. Attendere approvazione

# Sponsor da organizzazione:
# Organization Settings → Sponsors → Set up sponsoring
# Permette all'organizzazione di sponsorizzare sviluppatori e progetti

# Esempio di tier setup:
# $5/mese  → Nome nel README
# $15/mese → Accesso anticipato a release beta
# $50/mese → Sessione di supporto mensile 1:1
# $100/mese → Logo nel README + priorità bug fix

# FUNDING.yml per collegare sponsor button al repo:
# .github/FUNDING.yml
# github: [username]
# patreon: username
# open_collective: project-name
# ko_fi: username
# custom: ["https://example.com/donate"]
```

### Sponsor Dashboard e Analytics

I maintainer sponsorizzati hanno accesso a un dashboard che mostra:

- **Sponsor attivi**: numero e lista di sponsor correnti
- **Revenue mensile/annuale**: entrate aggregate con trend
- **Tier distribution**: distribuzione degli sponsor per tier
- **Churn rate**: tasso di cancellazione delle sponsorship
- **Geo-distribution**: provenienza geografica degli sponsor

---

## GitHub Education — Programma Educativo

### GitHub Education per Studenti

Gli studenti verificati ricevono accesso gratuito a strumenti professionali per sviluppatori.

| Benefit | Dettaglio |
|---------|-----------|
| **GitHub Copilot Student** | Completamenti illimitati e modelli aggiuntivi, gratuito |
| **GitHub Codespaces** | Fino a 180 ore core/mese per account personali |
| **Student Developer Pack** | 100+ offerte: crediti cloud, strumenti, servizi gratuiti |
| **GitHub Pro** | Equivalente al piano Pro per la durata degli studi |
| **Campus Expert** | Programma di leadership per studenti che promuovono la community |

```bash
# Requisiti per applicare come studente:
# 1. Essere iscritto a un istituto di istruzione accreditato
# 2. Avere un indirizzo email istituzionale (.edu o equivalente)
#    OPPURE documenti che provino l'iscrizione
# 3. Avere un account GitHub
# 4. Avere almeno 13 anni

# Applicazione: github.com/education → Get benefits → Students
# Verifica: automatica per email .edu, manuale per altri documenti
# Rinnovo: annuale, richiede ri-verifica dell'iscrizione
```

### GitHub Education per Insegnanti

| Benefit | Dettaglio |
|---------|-----------|
| **GitHub Team gratuito** | Utenti illimitati e repository privati per la classe |
| **GitHub Copilot Pro** | Gratuito per docenti verificati |
| **GitHub Classroom** | Creazione e gestione di compiti, grading automatico |
| **Integrazione LMS** | Sincronizzazione con Learning Management Systems (Canvas, Moodle, etc.) |
| **Codespaces per Classroom** | IDE pronto all'uso per ogni studente |

```bash
# GitHub Classroom — Workflow tipico
# 1. Creare un'organizzazione per il corso
# 2. Collegare a GitHub Classroom (classroom.github.com)
# 3. Creare un assignment con template repository
# 4. Condividere il link di invito con gli studenti
# 5. Ogni studente riceve un repo fork automatico
# 6. L'autograding verifica i submission via GitHub Actions
# 7. L'insegnante vede risultati aggregati nella dashboard

# Autograding example (test runner in workflow):
# .github/classroom/autograding.json
# {
#   "tests": [
#     {
#       "name": "Test funzione somma",
#       "setup": "pip install pytest",
#       "run": "pytest test_somma.py -v",
#       "timeout": 10,
#       "points": 20
#     },
#     {
#       "name": "Test funzione media",
#       "setup": "",
#       "run": "pytest test_media.py -v",
#       "timeout": 10,
#       "points": 30
#     }
#   ]
# }
```

---

## GitHub Mobile — Sviluppo in Mobilità

### Funzionalità Principali

GitHub Mobile è disponibile come app nativa per **iOS** e **Android**, progettata per operazioni ad alto impatto in mobilità.

| Funzionalità | Descrizione |
|-------------|-------------|
| **Notifiche** | Gestione notifiche con filtri, swipe actions, mark-as-read |
| **Code Search** | Ricerca codice nel repository direttamente dall'app |
| **PR Review** | Visualizzare diff, lasciare commenti, approvare/richiedere modifiche |
| **Issue Management** | Creare, commentare, assegnare e chiudere issue |
| **2FA via app** | Autenticazione a due fattori tramite notifica push |
| **Copilot Chat** | Chat AI contestualizzata al repository |
| **Merge PR** | Merge di pull request con squash/rebase/merge commit |
| **Workflow Status** | Monitoraggio stato dei workflow GitHub Actions |
| **Social Login** | Accesso via Google e Apple |
| **Universal Links (iOS)** | Link GitHub aprono direttamente nell'app |

### Copilot Chat su Mobile

Dal 2025, GitHub Mobile integra Copilot Chat, permettendo di:

```
• Fare domande sul codice di un repository
• Chiedere spiegazioni di funzioni o classi
• Generare snippet di codice
• Assegnare issue a Copilot direttamente dall'app mobile
• Ricevere suggerimenti contestualizzati al repository corrente
```

### Enterprise Support

GitHub Mobile supporta sia **GitHub Enterprise Cloud** che **GitHub Enterprise Server** con i requisiti di versione appropriati, permettendo ai team enterprise di gestire workflow critici anche in mobilità.

---

## GitHub Desktop — Interfaccia Grafica per Git

### Caratteristiche Principali

GitHub Desktop è un'applicazione gratuita e open source per **Windows** e **macOS** che semplifica i flussi di lavoro Git con un'interfaccia grafica intuitiva.

```
┌──────────────────────────────────────────────────────────────┐
│                    GITHUB DESKTOP WORKFLOW                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │  Clone   │───►│  Branch  │───►│  Edit    │               │
│  │  Repo    │    │  Create  │    │  Files   │               │
│  └──────────┘    └──────────┘    └────┬─────┘               │
│                                       │                      │
│                                       ▼                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │  Push    │◄───│  Commit  │◄───│  Stage   │               │
│  │  Remote  │    │  Changes │    │  Changes │               │
│  └────┬─────┘    └──────────┘    └──────────┘               │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────┐    ┌──────────┐                               │
│  │  Open PR │───►│  Merge   │                               │
│  │  on Web  │    │  on Web  │                               │
│  └──────────┘    └──────────┘                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

| Funzionalità | Dettaglio |
|-------------|-----------|
| **Visualizzazione diff** | Vista grafica delle modifiche con evidenziazione sintassi |
| **Commit parziale** | Selezione di singole righe da includere nel commit |
| **Branch management** | Creazione, switch e merge di branch con interfaccia visuale |
| **Conflict resolution** | Apertura dell'editor preferito per risolvere conflitti |
| **History view** | Cronologia dei commit con diff interattivo |
| **Stash** | Salvataggio temporaneo di modifiche non committate |
| **Cherry-pick** | Selezione di commit specifici da altri branch |
| **Rebase** | Rebase interattivo con interfaccia grafica |
| **Co-authoring** | Aggiunta di co-autori ai commit |
| **Repository list** | Gestione centralizzata di tutti i repository locali |
| **Drag and drop** | Trascina file per aggiungerli al repository |

### Quando Usare GitHub Desktop vs CLI

```
Desktop consigliato per:
• Sviluppatori che preferiscono interfacce grafiche
• Visualizzazione e commit di modifiche selettive (singole righe)
• Principianti che stanno imparando Git
• Situazioni dove la visualizzazione del diff è critica
• Gestione di conflitti di merge complessi

CLI (gh) consigliato per:
• Automazione e scripting
• Operazioni batch su più repository
• Integrazione in pipeline CI/CD
• Utenti avanzati che preferiscono la velocità della shell
• Operazioni che richiedono API diretta
• Server e ambienti headless
```

---

## Codespaces — Approfondimento Avanzato

### Dev Container Configuration Avanzata

I Dev Container sono container Docker configurati per fornire un ambiente di sviluppo completo e riproducibile. Il file primario di configurazione è `devcontainer.json`.

```jsonc
// .devcontainer/devcontainer.json — Configurazione avanzata
{
  "name": "Full-Stack Dev Environment",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20",

  // Features: componenti aggiuntivi plug-and-play
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.12"
    },
    "ghcr.io/devcontainers/features/postgresql:1": {}
  },

  // Lifecycle commands (ordine di esecuzione):
  // 1. onCreateCommand — solo alla prima creazione
  // 2. updateContentCommand — incluso nei prebuild
  // 3. postCreateCommand — dopo creazione, NON nei prebuild
  // 4. postStartCommand — ad ogni avvio
  // 5. postAttachCommand — quando VS Code si connette

  "onCreateCommand": "echo 'Codespace created at $(date)'",
  "updateContentCommand": "npm ci && npm run build",
  "postCreateCommand": "npm run db:migrate && npm run db:seed",
  "postStartCommand": "npm run dev &",

  // VS Code customizations
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-python.python",
        "bradlc.vscode-tailwindcss",
        "github.copilot"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "typescript.preferences.importModuleSpecifier": "relative"
      }
    }
  },

  // Port forwarding
  "forwardPorts": [3000, 5432, 6379],
  "portsAttributes": {
    "3000": {
      "label": "Frontend",
      "onAutoForward": "openBrowser"
    },
    "5432": {
      "label": "PostgreSQL",
      "onAutoForward": "silent"
    },
    "6379": {
      "label": "Redis",
      "onAutoForward": "silent"
    }
  },

  // Secrets: referenziare variabili di ambiente
  // configurate in Settings → Codespaces → Secrets
  "remoteEnv": {
    "DATABASE_URL": "${localEnv:DATABASE_URL}",
    "API_KEY": "${localEnv:API_KEY}"
  }
}
```

### Strategia di Prebuild Ottimale

```
┌──────────────────────────────────────────────────────────────┐
│               CODESPACES PREBUILD STRATEGY                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Trigger consigliati:                                        │
│  ────────────────────                                        │
│  main branch      → "Every push" (sempre aggiornato)        │
│  feature branches → "Configuration change only"              │
│                      (riduce consumo Actions minutes)        │
│  release branches → "Scheduled" (es. ogni 6 ore)            │
│                                                              │
│  Ottimizzazione regionale:                                   │
│  ─────────────────────────                                   │
│  • Abilitare prebuild SOLO per le regioni usate dal team    │
│  • Sviluppatori impostano la regione default in:            │
│    Settings → Codespaces → Default region                   │
│                                                              │
│  Lifecycle commands nei prebuild:                            │
│  ────────────────────────────────                            │
│  • updateContentCommand → eseguito nel prebuild             │
│    (inserire installazione dipendenze pesanti qui)           │
│  • postCreateCommand → NON eseguito nel prebuild            │
│    (eseguito solo quando il dev crea il codespace)           │
│                                                              │
│  Impatto performance tipico:                                 │
│  ──────────────────────────                                  │
│  • Senza prebuild: 5-15 minuti per repository grandi        │
│  • Con prebuild: sotto 1 minuto                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Gestione Codespaces via CLI
gh codespace create --repo owner/repo --machine largePremiumLinux \
    --devcontainer-path .devcontainer/devcontainer.json

# Macchine disponibili (tipiche):
# basicLinux32gb     — 2 core, 8GB RAM, 32GB storage
# standardLinux32gb  — 4 core, 16GB RAM, 32GB storage
# premiumLinux       — 8 core, 32GB RAM, 64GB storage
# largePremiumLinux  — 16 core, 64GB RAM, 128GB storage
# (Disponibilità varia per organizzazione e piano)

# Elencare codespace con dettagli macchina
gh codespace list --json name,machineName,state

# Forwarding porta locale
gh codespace ports forward 3000:3000 -c my-codespace

# Copiare file da/verso codespace
gh codespace cp local-file.txt remote:/workspace/file.txt -c my-codespace
gh codespace cp remote:/workspace/output.log ./output.log -c my-codespace

# Eseguire comandi nel codespace
gh codespace ssh -c my-codespace -- "npm test"

# Configurare prebuild (via web):
# Settings → Codespaces → Set up prebuild
# Selezionare branch, regione, trigger
```

---

## GitHub Discussions — Community Management Avanzato

### Architettura delle Discussions

GitHub Discussions fornisce uno spazio separato per conversazioni ongoing, domande e idee, riducendo il carico di gestione sulle issue e pull request. Funziona sia a livello di repository che di organizzazione.

```
┌──────────────────────────────────────────────────────────────┐
│               DISCUSSIONS vs ISSUES vs PR                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Discussions:                                                │
│  • Conversazioni aperte, Q&A, brainstorming                 │
│  • Non hanno stato (open/closed) vincolante                 │
│  • Supportano upvote e risposte accettate                   │
│  • Poll integrati per votazioni                             │
│  • Categorie personalizzabili                                │
│  • Cross-repo (a livello organizzazione)                     │
│                                                              │
│  Issues:                                                     │
│  • Task specifici con ciclo di vita (open/closed)            │
│  • Assegnabili a persone                                     │
│  • Collegabili a PR e milestone                              │
│  • Template YAML strutturati                                 │
│  • Integrabili in Projects v2                                │
│                                                              │
│  Pull Requests:                                              │
│  • Proposte di modifica codice                               │
│  • Code review con approvazione/richiesta modifiche          │
│  • Status checks CI/CD                                       │
│  • Merge con diverse strategie                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Categorie e Formati

| Categoria | Formato | Uso |
|-----------|---------|-----|
| **Announcements** | Annuncio | Solo maintainer possono creare, community risponde |
| **General** | Discussione aperta | Conversazioni libere sulla community |
| **Ideas** | Proposta | Feature request con upvote per prioritizzazione |
| **Q&A** | Domanda/Risposta | Domande con risposte accettate (marcate dal poster) |
| **Show and Tell** | Showcase | Demo, showcase, progetti completati |
| **Polls** | Sondaggio | Fino a 8 opzioni per sondaggio, votazione pubblica |

### Polls — Dettaglio

```bash
# I poll supportano:
# - Fino a 8 opzioni di risposta
# - Visibilità pubblica (repo pubblico) o ristretta (repo privato)
# - Solo utenti loggati possono votare
# - Risultati visibili in tempo reale
# - Non è possibile modificare le opzioni dopo la creazione

# Creazione via web:
# Discussions → New Discussion → Selezionare categoria "Polls"
# Inserire domanda e opzioni

# Via API (GraphQL):
gh api graphql -f query='
  mutation {
    createDiscussion(input: {
      repositoryId: "REPO_ID",
      categoryId: "CATEGORY_ID",
      title: "Quale framework preferite per il frontend?",
      body: "Votate il vostro framework preferito per il prossimo progetto."
    }) {
      discussion { url }
    }
  }
'
```

### Community Health Dashboard

GitHub fornisce un dashboard di salute della community che mostra metriche operative:

- **Utenti unici**: conteggio di utenti che hanno interagito nel periodo selezionato
- **Reazioni**: distribuzione di emoji reactions su discussions
- **Upvote**: tendenza dei voti sulle proposte
- **Risposte accettate**: percentuale di Q&A con risposta marcata
- **Tempo medio di risposta**: latenza dalla domanda alla prima risposta
- **Top contributors**: classifica dei contributori più attivi

### Discussions a Livello Organizzazione

```bash
# Le Discussions organizzative permettono conversazioni cross-repo
# Utili per:
# - Annunci a tutta l'organizzazione
# - RFC (Request for Comments) su decisioni architetturali
# - Discussioni su standard e pratiche condivise
# - Onboarding guide per nuovi membri

# Abilitare:
# Organization → Settings → Discussions → ✅ Enable discussions

# Le discussions organizzative hanno le stesse categorie
# dei repository ma sono accessibili a tutti i membri dell'org
```

---

## Ruoli Custom e Governance Avanzata

### Custom Repository Roles

Le organizzazioni su GitHub Enterprise Cloud possono creare **ruoli repository custom** per un controllo più granulare rispetto ai 5 ruoli base (Read, Triage, Write, Maintain, Admin).

```bash
# Creare un ruolo custom (fino a 20 per organizzazione)
# Organization → Settings → Repository roles → New role

# Esempio: "Security Reviewer" role
# Basato su: Read
# Permessi aggiuntivi:
# ✅ View code scanning alerts
# ✅ Dismiss code scanning alerts
# ✅ View secret scanning alerts
# ✅ Dismiss secret scanning alerts
# ✅ View Dependabot alerts
# ❌ Push codice
# ❌ Gestire settings

# Esempio: "Release Manager" role
# Basato su: Write
# Permessi aggiuntivi:
# ✅ Manage releases
# ✅ Edit repository metadata
# ✅ Manage GitHub Pages
# ❌ Manage branch protection
# ❌ Manage repository settings

# Assegnare il ruolo a un team:
gh api orgs/{org}/teams/{team}/repos/{owner}/{repo} -X PUT \
    -f role_name="security-reviewer"
```

### Custom Organization Roles

Dal 2023 (GA), le organizzazioni possono creare ruoli custom anche a livello organizzazione, non solo repository.

| Permesso | Descrizione | Uso tipico |
|----------|-------------|-----------|
| **Manage organization members** | Aggiungere/rimuovere membri | HR team |
| **Manage organization billing** | Gestire fatturazione e piani | Finance team |
| **Manage organization webhooks** | Creare e modificare webhook | DevOps team |
| **Manage organization projects** | Gestire Projects v2 org-level | PM team |
| **View organization audit log** | Consultare l'audit log | Compliance team |
| **Manage organization custom roles** | Creare e modificare ruoli custom | Security team |

### Enterprise-Level Custom Roles (Agosto 2025)

Da agosto 2025, gli enterprise owner possono creare ruoli custom a livello enterprise, disponibili in tutte le organizzazioni dell'enterprise:

```
┌──────────────────────────────────────────────────────────────┐
│          ENTERPRISE CUSTOM ROLES HIERARCHY                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Enterprise Owner                                            │
│  └─ Crea ruoli custom enterprise                            │
│     └─ Disponibili in TUTTE le org dell'enterprise          │
│        └─ Org Owner assegna i ruoli ai membri               │
│                                                              │
│  Vantaggi:                                                   │
│  ─────────                                                   │
│  • Standardizzazione dei ruoli cross-organizzazione         │
│  • Supporto compliance: stessi ruoli ovunque                │
│  • Movimento consistente dei membri tra organizzazioni      │
│  • Limite aumentato a 20 ruoli custom per tipo              │
│                                                              │
│  Nuove funzionalità enterprise governance (2025):           │
│  ───────────────────────────────────────────────             │
│  • Enterprise Security Manager (ruolo predefinito)          │
│  • Bypass permissions granulari per rulesets                │
│  • Assegnazione ruoli a enterprise teams e utenti           │
│  • Enterprise teams per governance cross-org                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Gestione Notifiche — Strategie per Team

### Tipologie di Notifica

GitHub genera notifiche in tre scenari principali:

| Tipo | Trigger | Default |
|------|---------|---------|
| **Participating** | Menzione diretta (@user), assegnazione, review richiesta | Attivo |
| **Watching** | Qualsiasi attività su repo watched | Configurabile |
| **Custom** | Regole specifiche per repo/org | Manuale |

### Canali di Consegna

```
┌──────────────────────────────────────────────────────────────┐
│               NOTIFICATION DELIVERY CHANNELS                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Canale          │ Uso consigliato                           │
│  ────────────────┼────────────────────────────────────       │
│  GitHub Web      │ Inbox principale, triage quotidiano       │
│  Email           │ Menzioni dirette, review richieste        │
│  GitHub Mobile   │ Approvazioni urgenti, notifiche push      │
│  gh CLI          │ Scripting, automazione, filtraggio        │
│  Slack/Teams     │ Integrazione team (via GitHub App)        │
│                                                              │
│  Routing personalizzato (Settings → Notifications):         │
│  ──────────────────────────────────────────────────          │
│  • Email diversa per organizzazione diversa                 │
│  • Web-only per watching, email per menzioni                │
│  • Scheduled digest (riassunto periodico)                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Filtri Inbox

```bash
# Filtrare notifiche via web inbox
# Filtri supportati:

# Per autore
author:username

# Per motivo della notifica
reason:review-requested
reason:mention
reason:assign
reason:comment
reason:team-mention
reason:subscribed
reason:ci-activity

# Per organizzazione
org:my-organization

# Per repository
repo:owner/repo

# Per tipo
is:unread
is:read
is:issue
is:pull-request
is:discussion

# Combinare filtri
reason:review-requested org:my-org is:unread

# Via gh CLI — filtrare notifiche
gh api notifications --jq '.[] | select(.reason=="review_requested") | .subject.title'

# Elencare notifiche non lette
gh api notifications --jq '.[] | select(.unread==true) | "\(.repository.full_name): \(.subject.title)"'

# Marcare come letta
gh api notifications/threads/{thread_id} -X PATCH

# Gestione watching
gh api user/subscriptions --jq '.[].full_name'

# Smettere di seguire un repo
gh api repos/{owner}/{repo}/subscription -X DELETE
```

### Strategia Anti-Overload

```
Workflow consigliato per team grandi:

1. AUDIT INIZIALE
   - Controllare repos watched: Settings → Notifications → Watched repositories
   - Fare unwatch di repo non rilevanti (un click per ciascuno)
   - Impostare "Participating and @mentions" come default per nuovi repo

2. ROUTING PER ORGANIZZAZIONE
   - Email lavoro per org aziendale
   - Email personale per progetti OSS
   - Web-only per repo secondari

3. TRIAGE QUOTIDIANO
   - Mattina: filtrare per reason:review-requested (priorità alta)
   - Metà giornata: reason:mention e reason:assign
   - Fine giornata: bulk "mark as read" per reason:subscribed

4. AUTOMAZIONE
   - gh alias set notif-review 'api notifications --jq "..."'
   - Webhook → Slack per notifiche team-critical
   - Cron job per report settimanale notifiche pendenti
```

---

## Enterprise Managed Users (EMU) — Identità Gestita

### Architettura EMU

Enterprise Managed Users è un modello di gestione identità dove gli account utente sono interamente gestiti dal provider di identità (IdP) dell'organizzazione, senza account personali GitHub.

```
┌──────────────────────────────────────────────────────────────┐
│              ENTERPRISE MANAGED USERS ARCHITECTURE           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Identity Provider (IdP)                                     │
│  ┌───────────────────┐                                       │
│  │  Entra ID / Okta  │                                       │
│  │  / PingFederate   │                                       │
│  └────────┬──────────┘                                       │
│           │                                                  │
│     SAML SSO │ SCIM Provisioning                             │
│           │                                                  │
│  ┌────────▼──────────────────────────────────────┐           │
│  │          GitHub Enterprise Cloud               │           │
│  │  ┌────────────────────────────────────────┐   │           │
│  │  │  Enterprise Account                     │   │           │
│  │  │  ┌──────────────┐  ┌──────────────┐    │   │           │
│  │  │  │   Org A      │  │   Org B      │    │   │           │
│  │  │  │  (managed)   │  │  (managed)   │    │   │           │
│  │  │  └──────────────┘  └──────────────┘    │   │           │
│  │  │                                         │   │           │
│  │  │  Utenti: SHORTCODE_username             │   │           │
│  │  │  (nessun account personale)             │   │           │
│  │  └────────────────────────────────────────┘   │           │
│  └───────────────────────────────────────────────┘           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Configurazione SAML + SCIM

```bash
# Passaggio 1: Accesso come setup user
# Username: SHORTCODE_admin (es. mycompany_admin)
# Questo è l'unico utente locale; tutti gli altri sono gestiti dall'IdP

# Passaggio 2: Configurare SAML SSO
# Enterprise Settings → Authentication security → SAML single sign-on
# - Sign on URL: endpoint HTTPS del tuo IdP
# - Issuer: SAML issuer URL del IdP
# - Public Certificate: certificato del IdP per verificare risposte SAML

# Passaggio 3: Configurare SCIM provisioning
# L'IdP usa SCIM per:
# - Creare account utente su GitHub
# - Aggiungere utenti all'enterprise
# - Assegnare utenti a gruppi/org
# - Aggiornare attributi utente
# - Disattivare/rimuovere utenti

# Provider IdP supportati con integrazione "paved-path":
# - Microsoft Entra ID (Azure AD)
# - Okta
# - PingFederate

# ATTENZIONE: la combinazione di Okta e Entra ID
# (uno per SSO e l'altro per SCIM) NON è supportata.
# L'API SCIM restituirà un errore se questa combinazione è configurata.

# Passaggio 4: Verificare il provisioning
gh api /scim/v2/enterprises/{enterprise}/Users --jq '.Resources[].userName'
```

### EMU vs SAML SSO Standard

| Caratteristica | EMU | SAML SSO Standard |
|----------------|-----|-------------------|
| **Account utente** | Gestito dall'IdP, formato SHORTCODE_username | Account personale GitHub esistente |
| **Contributi fuori enterprise** | Non permessi | Permessi (account personale) |
| **Deprovisioning** | Automatico via SCIM (account disattivato) | Manuale o semi-automatico |
| **Fork verso account personale** | Non permesso | Configurabile |
| **Conformità** | Massima (controllo totale) | Buona (dipende dalla policy) |
| **Setup user** | SHORTCODE_admin (unico locale) | Non necessario |
| **Naming convention** | Forzata (SHORTCODE_username) | Libera |
| **Complessità setup** | Alta (richiede IdP partner) | Media |

---

## Sicurezza Avanzata — GitHub Advanced Security (GHAS)

### Ristrutturazione GHAS 2025

Dal 1 aprile 2025, GitHub Advanced Security è disponibile come due prodotti standalone separati:

```
┌──────────────────────────────────────────────────────────────┐
│          GHAS RESTRUCTURING — APRILE 2025                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────┐ ┌───────────────────────────┐ │
│  │   GitHub Secret           │ │   GitHub Code             │ │
│  │   Protection              │ │   Security                │ │
│  │   $19/mese per committer  │ │   $30/mese per committer  │ │
│  │   attivo                  │ │   attivo                  │ │
│  │                           │ │                           │ │
│  │   Include:                │ │   Include:                │ │
│  │   • Push protection       │ │   • Code scanning         │ │
│  │   • Secret scanning       │ │   • Copilot Autofix       │ │
│  │   • AI detection (low     │ │   • Security campaigns    │ │
│  │     false positive)       │ │   • Dependency Review     │ │
│  │   • Security insights     │ │     Action                │ │
│  │                           │ │   • Analisi statica       │ │
│  │                           │ │     (SAST)                │ │
│  └───────────────────────────┘ └───────────────────────────┘ │
│                                                              │
│  Novità:                                                     │
│  • Disponibili per clienti GitHub Team (prima solo           │
│    Enterprise)                                               │
│  • Modello consumption-based pay-as-you-go                   │
│  • Acquistabili separatamente o insieme                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Artifact Attestations e Supply Chain Security

GitHub Artifact Attestations lega un artefatto (con nome e digest) a un predicato di provenienza SLSA usando il formato in-toto, con firma verificabile tramite certificato Sigstore a breve durata.

```bash
# Livelli SLSA raggiungibili:
# - Artifact Attestations da solo: SLSA v1.0 Build Level 2
# - Attestations + Reusable Workflows: SLSA v1.0 Build Level 3

# Generare attestation di build provenance in un workflow:
# .github/workflows/build-attest.yml
# name: Build and Attest
# on: push
# jobs:
#   build:
#     runs-on: ubuntu-latest
#     permissions:
#       id-token: write
#       contents: read
#       attestations: write
#     steps:
#       - uses: actions/checkout@v4
#       - run: npm ci && npm run build
#       - uses: actions/attest-build-provenance@v2
#         with:
#           subject-path: './dist/**'

# Verificare un'attestation
gh attestation verify ./dist/app.js --owner owner

# Generare attestation con SBOM (Software Bill of Materials)
# L'SBOM associa al build la lista delle dipendenze open source,
# fornendo trasparenza e compliance

# Disponibilità:
# - Free/Pro/Team: solo repo pubblici
# - Enterprise Cloud: repo pubblici, privati e interni
```

### Push Protection Avanzata

```bash
# Push Protection blocca push contenenti segreti prima che raggiungano
# il repository. Dal 2025, include rilevamento AI con basso tasso
# di falsi positivi.

# Flusso quando un push viene bloccato:
#
# 1. Developer fa push
# 2. GitHub analizza il contenuto in tempo reale
# 3. Se rileva un segreto → blocca il push
# 4. Mostra messaggio di errore con:
#    - Tipo di segreto rilevato
#    - Posizione nel codice (file:riga)
#    - Link per bypassare (se falso positivo)
#
# Opzioni dopo il blocco:
# a) Rimuovere il segreto e ri-pushare (consigliato)
# b) Bypassare con motivazione (richiede permesso specifico)
#    Motivazioni valide: "false positive", "used in tests", "will fix later"
# c) Contattare l'admin per approvazione bypass

# Configurare push protection a livello organizzazione:
# Organization → Settings → Code security → Push protection
# ✅ Enable push protection for all repositories

# Pattern custom per secret scanning (Enterprise):
gh api orgs/{org}/secret-scanning/custom-patterns -X POST \
    -f name="Internal API Key" \
    -f pattern="INTERNAL-KEY-[A-Za-z0-9]{32}" \
    -f secret_type="custom"
```

---

## Visibilità Repository e Fork Policy

### Livelli di Visibilità

| Visibilità | Chi può vedere | Chi può contribuire | Disponibilità |
|-----------|----------------|---------------------|---------------|
| **Public** | Tutti | Tutti (via fork + PR) | Tutti i piani |
| **Private** | Solo collaboratori espliciti | Solo collaboratori | Tutti i piani |
| **Internal** | Tutti i membri dell'enterprise | Membri enterprise | Solo Enterprise Cloud |

### Regole di Fork

```
┌──────────────────────────────────────────────────────────────┐
│                    FORK VISIBILITY RULES                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Repository Pubblico:                                        │
│  • Tutti i fork sono SEMPRE pubblici                         │
│  • Non è possibile rendere privato il fork di un repo       │
│    pubblico                                                  │
│  • Il network di fork condivide la stessa visibilità        │
│                                                              │
│  Repository Privato:                                         │
│  • Fork privati ereditano la struttura di permessi           │
│    dell'upstream                                             │
│  • L'owner dell'upstream mantiene controllo sul codice      │
│  • Fork policy configurabile a livello org                  │
│                                                              │
│  Repository Interno:                                         │
│  • Fork supporta un solo livello (no fork di fork)          │
│  • Non è possibile forkare un fork privato di un repo       │
│    interno                                                   │
│  • Accesso enterprise-wide semplificato                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Configurazione Fork Policy

```bash
# A livello di organizzazione:
# Organization → Settings → Member privileges → Repository forking
# Opzioni:
# ❌ Disable forking (nessun fork permesso)
# ✅ Allow forking of private repositories
# ✅ Allow forking to external organizations (Enterprise)
# ✅ Allow forking only within the enterprise (Enterprise)

# A livello di singolo repository:
# Repository → Settings → General → Features
# ✅ Allow forking

# Via API:
gh api repos/{owner}/{repo} -X PATCH -F allow_forking=true

# Enterprise fork policy:
# Enterprise → Settings → Policies → Repository policies
# Controlla dove i membri possono forkare repository privati/interni
```

### Cambiare Visibilità — Rischi e Precauzioni

```bash
# Rendere pubblico un repo privato:
# ⚠️ ATTENZIONE: espone TUTTA la cronologia Git
# ⚠️ Inclusi commit con segreti già rimossi dal working tree

# Checklist pre-pubblicazione:
# 1. Scansionare la cronologia per segreti:
git log --all --full-history -p | grep -i "api_key\|password\|secret\|token"

# 2. Usare git filter-repo per pulire la cronologia se necessario
# 3. Rotare tutti i segreti che potrebbero essere stati committati
# 4. Verificare che LICENSE sia appropriata per codice pubblico
# 5. Rimuovere dati proprietari, nomi clienti, URL interni
# 6. Controllare .gitignore per file sensibili

# Rendere privato un repo pubblico:
# • I fork esistenti restano pubblici (non vengono resi privati)
# • Le GitHub Pages vengono disabilitate
# • Le Stars e i Watchers perdono accesso
```

---

## GitHub Apps — Creazione e Marketplace

### Architettura di una GitHub App

```
┌──────────────────────────────────────────────────────────────┐
│                  GITHUB APP ARCHITECTURE                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌──────────────┐    ┌──────────────┐   │
│  │  GitHub      │     │  Your Server │    │  GitHub API  │   │
│  │  Platform    │     │  (Backend)   │    │  REST/GraphQL│   │
│  └──────┬──────┘     └──────┬───────┘    └──────┬───────┘   │
│         │                    │                    │           │
│   Webhook ─────────────►  Receive   ──────────►  Call API   │
│   Events                  Events                 (JWT auth)  │
│   (push, PR,              Process                            │
│    issue, etc.)           Logic                              │
│         │                    │                    │           │
│         │              ┌─────▼──────┐             │           │
│         │              │ Actions:   │             │           │
│         │              │ • Comment  │◄────────────┘           │
│         │              │ • Label    │                         │
│         │              │ • Merge    │                         │
│         │              │ • Deploy   │                         │
│         │              └────────────┘                         │
│         │                                                    │
│   Installation                                               │
│   Token (1 ora) ←─── JWT signed with private key            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Best Practices per GitHub Apps

```bash
# Principi di sicurezza:
# 1. Richiedere permessi MINIMI necessari
# 2. Sottoscrivere webhook events invece di polling (risparmia rate limit)
# 3. Validare SEMPRE la firma webhook (X-Hub-Signature-256)
# 4. Token di installazione scadono dopo 1 ora → gestire refresh
# 5. Ruotare la private key periodicamente

# Struttura permessi consigliata per casi d'uso comuni:

# Bot CI/CD:
# - Contents: read
# - Pull requests: write
# - Checks: write
# - Statuses: write
# - Webhooks: push, pull_request

# Bot di triage:
# - Issues: write
# - Pull requests: write
# - Labels: read/write
# - Webhooks: issues, pull_request

# Security scanner:
# - Contents: read
# - Security events: read/write
# - Pull requests: write (per creare PR di fix)
# - Webhooks: push, repository

# Listare le app installate nell'organizzazione:
gh api orgs/{org}/installations --jq '.installations[] | "\(.app_slug): \(.permissions | keys)"'
```

### Pubblicazione su GitHub Marketplace

```bash
# Requisiti per la pubblicazione:
# 1. App in un repository pubblico
# 2. Listino prezzi definito (free, flat-rate, o per-unit)
# 3. Accettazione del GitHub Marketplace Developer Agreement
# 4. Logo, descrizione, documentazione utente
# 5. Link a privacy policy e terms of service

# Processo di pubblicazione:
# 1. Developer Settings → GitHub Apps → selezionare l'app
# 2. Sezione "Marketplace listing" → Create draft listing
# 3. Compilare: nome, descrizione, categorie, pricing plans
# 4. Aggiungere screenshot e documentazione
# 5. Sottomettere per review

# Customer experience best practices:
# - L'app deve funzionare sia su account personali che organizzazioni
# - Documentazione chiara su setup e configurazione
# - Materiali marketing accurati rispetto al comportamento reale
# - Supporto per trial period (14 giorni gratuiti per piani a pagamento)
```

---

## GitHub CLI — Automazione Avanzata e Scripting

### Pattern di Scripting con `gh`

```bash
# PATTERN 1: Bulk operations su issues
# Chiudere tutte le issue con label "wontfix" più vecchie di 90 giorni
gh issue list --label "wontfix" --state open --json number,createdAt \
    --jq '.[] | select((.createdAt | fromdateiso8601) < (now - 7776000)) | .number' \
    | xargs -I{} gh issue close {} --comment "Closing stale wontfix issue"

# PATTERN 2: Report settimanale PR
# Generare report di tutte le PR mergiare questa settimana
gh pr list --state merged --search "merged:>=$(date -d '7 days ago' +%Y-%m-%d)" \
    --json title,author,mergedAt,url \
    --jq '.[] | "[\(.mergedAt[:10])] \(.title) by @\(.author.login)"'

# PATTERN 3: Cross-repo operations
# Creare la stessa label in tutti i repo di un'organizzazione
gh repo list MY-ORG --json nameWithOwner --jq '.[].nameWithOwner' \
    | xargs -I{} gh label create "security:critical" \
        --repo {} --color "B60205" --description "Critical security issue"

# PATTERN 4: CI status dashboard
# Controllare lo stato CI di tutti i repo con workflow falliti
gh repo list MY-ORG --json nameWithOwner --jq '.[].nameWithOwner' \
    | while read repo; do
        status=$(gh run list --repo "$repo" --limit 1 --json conclusion --jq '.[0].conclusion' 2>/dev/null)
        if [ "$status" = "failure" ]; then
            echo "❌ $repo — ultimo workflow FALLITO"
        fi
    done

# PATTERN 5: Dependency audit
# Elencare tutti i repo con Dependabot alerts aperti
gh api orgs/MY-ORG/dependabot/alerts --paginate \
    --jq '.[] | select(.state=="open") | "\(.repository.full_name): \(.security_advisory.summary)"'
```

### Alias Avanzati

```bash
# Dashboard personale
gh alias set dashboard 'pr list --search "is:open review-requested:@me" --json title,url,updatedAt --jq ".[] | \"[\(.updatedAt[:10])] \(.title) → \(.url)\""'

# Creare PR con auto-fill e reviewer automatico
gh alias set qpr 'pr create --fill --reviewer team-leads'

# Statistiche commit settimanali
gh alias set weekly-stats '!gh api repos/{owner}/{repo}/stats/commit_activity --jq ".[0] | \"Week total: \(.total) commits | Days: \(.days | map(tostring) | join(\", \"))\""'

# Quick release con note auto-generate
gh alias set qrelease '!gh release create "$1" --generate-notes --title "Release $1"'

# Cleanup: eliminare branch merged
gh alias set cleanup '!git branch --merged main | grep -v main | xargs -r git branch -d && echo "Cleaned up merged branches"'

# Notifiche review pendenti
gh alias set reviews 'pr list --search "is:open review-requested:@me" --json title,number --jq ".[] | \"#\(.number) \(.title)\""'
```

### Estensioni CLI Essenziali

| Estensione | Comando Install | Funzionalità |
|-----------|-----------------|--------------|
| **gh-dash** | `gh extension install dlvhdr/gh-dash` | Dashboard TUI interattiva per PR e issue |
| **gh-branch** | `gh extension install mislav/gh-branch` | Gestione branch interattiva con fuzzy search |
| **gh-copilot** | `gh extension install github/gh-copilot` | Copilot CLI (deprecazione annunciata settembre 2025, integrato nel core) |
| **gh-poi** | `gh extension install seachicken/gh-poi` | Pulizia branch locali già merged |
| **gh-markdown-preview** | `gh extension install yusukebe/gh-markdown-preview` | Preview Markdown nel terminale |
| **gh-notify** | `gh extension install meiji163/gh-notify` | Gestione notifiche avanzata da CLI |

```bash
# Creare un'estensione custom
gh extension create gh-my-tool
# Genera: gh-my-tool/gh-my-tool (script bash eseguibile)

# Struttura di un'estensione Go precompilata:
# gh-my-tool/
# ├── main.go          → Entry point
# ├── go.mod           → Dipendenze (usa go-gh per accesso CLI internals)
# └── .github/
#     └── workflows/
#         └── release.yml → Usa gh-extension-precompile action

# Pubblicare un'estensione:
# 1. Repository deve chiamarsi gh-<nome>
# 2. Contenere un eseguibile con lo stesso nome
# 3. gh extension install owner/gh-<nome> → installabile da chiunque
```

---

## Repository Template e Configurazioni Organizzative

### Template Repository

I template repository permettono di generare nuovi repository con la stessa struttura di directory, file e impostazioni.

```bash
# Creare un template repository:
# Repository → Settings → General → ✅ Template repository

# Creare un repo da template via CLI:
gh repo create my-new-project --template MY-ORG/node-template --public --clone

# Contenuto tipico di un template repository:
# ├── .github/
# │   ├── ISSUE_TEMPLATE/
# │   │   ├── bug_report.yml
# │   │   └── feature_request.yml
# │   ├── PULL_REQUEST_TEMPLATE.md
# │   ├── dependabot.yml
# │   ├── CODEOWNERS
# │   └── workflows/
# │       ├── ci.yml
# │       ├── release.yml
# │       └── codeql.yml
# ├── .devcontainer/
# │   └── devcontainer.json
# ├── src/
# ├── tests/
# ├── .editorconfig
# ├── .eslintrc.json
# ├── .prettierrc
# ├── .gitignore
# ├── LICENSE
# ├── README.md
# ├── CONTRIBUTING.md
# ├── SECURITY.md
# └── package.json

# Differenza da fork:
# Template: nuovo repo indipendente, nessun link all'upstream
# Fork: repo collegato all'upstream, possibilità di sync e PR
```

### Configurazione `.github` Repository

Ogni organizzazione può avere un repository speciale chiamato `.github` che contiene configurazioni predefinite per tutti i repository dell'organizzazione.

```bash
# Repository .github dell'organizzazione
# Contiene file di default che si applicano a TUTTI i repo
# se il singolo repo non ha il suo override

# MY-ORG/.github/
# ├── profile/
# │   └── README.md              → Profilo pubblico dell'organizzazione
# ├── ISSUE_TEMPLATE/
# │   ├── bug_report.yml         → Template issue default per tutti i repo
# │   └── feature_request.yml
# ├── PULL_REQUEST_TEMPLATE.md   → Template PR default
# ├── CONTRIBUTING.md             → Guida contribuzione default
# ├── CODE_OF_CONDUCT.md          → Codice di condotta default
# ├── SECURITY.md                 → Policy sicurezza default
# ├── FUNDING.yml                 → Sponsor default
# └── SUPPORT.md                  → Informazioni supporto default

# Priorità: file nel singolo repo > file nel repo .github dell'org
```

---

## Confronto Piattaforme — GitHub vs GitLab vs Bitbucket

| Caratteristica | GitHub | GitLab | Bitbucket |
|----------------|--------|--------|-----------|
| **CI/CD** | GitHub Actions | GitLab CI/CD | Bitbucket Pipelines |
| **Registry pacchetti** | GitHub Packages (npm, Docker, Maven, etc.) | GitLab Registry | Solo Docker |
| **Project management** | Projects v2, Issues | Boards, Epics, Milestones | Jira integration |
| **Code review** | Pull Requests + CODEOWNERS | Merge Requests + Code Owners | Pull Requests |
| **Security scanning** | GHAS (Secret + Code Security) | SAST/DAST/Secret Detection inclusi | Solo add-on |
| **AI assistant** | Copilot (completamenti + chat + agent) | Duo (completamenti + chat) | Limitato |
| **Hosting statico** | GitHub Pages | GitLab Pages | Nessuno nativo |
| **Dev environments** | Codespaces | Web IDE + Remote Dev | Cloud IDE (limitato) |
| **Self-hosted** | Enterprise Server | Community Edition (gratuito) | Data Center |
| **Prezzo team** | Free / $4 utente/mese (Team) | Free / $29 utente/mese (Premium) | Free / $5 utente/mese |
| **Community OSS** | Dominante (100M+ sviluppatori) | Forte nel DevOps | Minore |
| **Marketplace** | GitHub Marketplace (apps + actions) | Nessuno (solo integrazioni) | Atlassian Marketplace |

---

## Migrazione verso GitHub

### Strategie di Migrazione

```bash
# Da GitLab a GitHub:
# 1. Migrare il codice (cronologia Git mantenuta integralmente)
git clone --mirror https://gitlab.com/org/repo.git
cd repo.git
git remote set-url origin https://github.com/org/repo.git
git push --mirror

# 2. Migrare issue e PR con GitHub Importer
# github.com/new/import → inserire URL GitLab

# 3. Migrare CI/CD: convertire .gitlab-ci.yml → .github/workflows/
#    Mappatura chiave:
#    GitLab stages → GitHub jobs con needs
#    GitLab variables → GitHub secrets + env
#    GitLab runners → GitHub runners (hosted o self-hosted)

# Da Bitbucket a GitHub:
# 1. Import via web: github.com/new/import → URL Bitbucket
# 2. Import include: codice, branch, commit history
# 3. Wiki e issue richiedono tool separati

# Da Azure DevOps a GitHub:
gh repo create new-repo --private
git clone --mirror https://dev.azure.com/org/project/_git/repo
cd repo.git
git remote set-url origin https://github.com/org/new-repo.git
git push --mirror

# Strumenti di migrazione ufficiali GitHub:
# - GitHub Enterprise Importer (GEI): per migrazioni enterprise-scale
# - GitHub CLI importer: gh gei (estensione per migrazioni automatizzate)
# - GitHub API endpoints di importazione

# Post-migrazione checklist:
# ✅ Verificare cronologia commit intatta
# ✅ Configurare branch protection
# ✅ Impostare CODEOWNERS
# ✅ Configurare GitHub Actions (CI/CD)
# ✅ Configurare Dependabot
# ✅ Abilitare secret scanning
# ✅ Aggiornare URL nei README e documentazione
# ✅ Configurare webhook per integrazioni esterne
# ✅ Migrare secrets/variabili d'ambiente
# ✅ Informare il team e aggiornare i remote locali
```

---

## Metriche e Insights del Repository

### Repository Insights

```bash
# Traffic (visite e cloni):
gh api repos/{owner}/{repo}/traffic/views --jq '.views[] | "\(.timestamp[:10]): \(.count) views (\(.uniques) unique)"'
gh api repos/{owner}/{repo}/traffic/clones --jq '.clones[] | "\(.timestamp[:10]): \(.count) clones"'

# Referral sources:
gh api repos/{owner}/{repo}/traffic/popular/referrers --jq '.[] | "\(.referrer): \(.count) views"'

# Contenuti popolari:
gh api repos/{owner}/{repo}/traffic/popular/paths --jq '.[] | "\(.path): \(.count) views"'

# Statistiche contributori:
gh api repos/{owner}/{repo}/stats/contributors --jq '.[].author.login'

# Frequenza commit (ultimi 52 weeks):
gh api repos/{owner}/{repo}/stats/commit_activity --jq '.[-4:] | .[] | "Week \(.week | todate): \(.total) commits"'

# Code frequency (aggiunte/rimozioni per settimana):
gh api repos/{owner}/{repo}/stats/code_frequency --jq '.[-4:] | .[] | "Week: +\(.[1]) -\(.[2]) lines"'

# Partecipazione (owner vs others):
gh api repos/{owner}/{repo}/stats/participation --jq '"Owner: \(.owner | add) commits | All: \(.all | add) commits (last 52 weeks)"'
```

### Organization Insights

```bash
# Audit log per compliance:
gh api orgs/{org}/audit-log --paginate --jq '.[] | "\(.created_at) | \(.action) | \(.actor)"' | head -50

# Membri dell'organizzazione:
gh api orgs/{org}/members --jq '.[].login'

# Team e composizione:
gh api orgs/{org}/teams --jq '.[] | "\(.name): \(.members_count) members"'

# Repository dell'organizzazione con statistiche:
gh repo list {org} --json name,stargazerCount,forkCount,updatedAt \
    --jq '.[] | "\(.name) ★\(.stargazerCount) 🍴\(.forkCount) updated:\(.updatedAt[:10])"'
```

### Agent Skills con GitHub CLI

A partire dal 2026, GitHub ha introdotto il comando `gh skill` per la gestione delle agent skills direttamente dalla riga di comando. Le agent skills sono set portabili di istruzioni, script e risorse che insegnano agli agenti AI come eseguire compiti specifici, e funzionano su più host tra cui GitHub Copilot, Claude Code, Cursor, Codex e Gemini CLI. I sottocomandi principali includono `gh skill install` per installare una skill da un repository, `gh skill search` per cercare skills disponibili, `gh skill publish` per pubblicare una nuova skill, `gh skill update` per aggiornare le skills installate, e `gh skill preview` per visualizzare un'anteprima locale prima della pubblicazione. Il flag `--allow-hidden-dirs` consente di gestire skills collocate in directory nascoste (con prefisso punto). Questa funzionalità è compatibile anche con ambienti GitHub Enterprise Cloud con data residency, estendendo la portata della CLI negli scenari enterprise più restrittivi.

```bash
# Cercare skills disponibili
gh skill search "code review"

# Installare una skill da un repository
gh skill install owner/repo-skill

# Pubblicare una skill dal repository corrente
gh skill publish

# Anteprima locale di una skill (anche in directory nascoste)
gh skill preview --allow-hidden-dirs
```

Inoltre, dalla versione 2.50.0, la GitHub CLI produce Build Provenance Attestation per ogni build, abilitando una traccia crittograficamente verificabile che riconduce al repository GitHub di origine, alla revisione git e alle istruzioni di build utilizzate. Questo rafforza significativamente la supply chain security per tutti i progetti che distribuiscono artefatti tramite `gh release`.

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Organization** | Entità GitHub che raggruppa repository, team e membri con permessi centralizzati e policy di sicurezza |
| **Team** | Gruppo di membri all'interno di un'organizzazione con permessi specifici sui repository assegnati |
| **Branch Protection Rule** | Regola che impedisce push diretti su un branch e richiede condizioni (review, status check) prima del merge |
| **Ruleset** | Evoluzione delle branch protection con targeting flessibile (pattern branch/tag) e gestione a livello org |
| **CODEOWNERS** | File che mappa path a team/utenti, assegnando automaticamente reviewer alle Pull Request |
| **Pull Request (PR)** | Meccanismo per proporre modifiche, richiedere review e discutere il codice prima del merge |
| **Code Review** | Processo di revisione del codice da parte di peer che verificano qualità, sicurezza e correttezza |
| **GitHub CLI (gh)** | Strumento da riga di comando ufficiale per interagire con GitHub senza usare l'interfaccia web |
| **Fine-Grained PAT** | Personal Access Token con permessi granulari per repository e operazioni specifiche |
| **GitHub App** | Integrazione con permessi dedicati, rate limit separato e audit trail, non legata a un utente |
| **Projects v2** | Sistema di project management GitHub con viste multiple (Board, Table, Roadmap) e campi custom |
| **Issue Template** | File YAML/Markdown che pre-compila il form di creazione issue con campi strutturati |
| **GitHub Container Registry (GHCR)** | Registry per immagini container integrato con GitHub, autenticazione via GITHUB_TOKEN |
| **2FA (Two-Factor Authentication)** | Autenticazione a due fattori obbligatoria per organizzazioni GitHub dal 2024 |
