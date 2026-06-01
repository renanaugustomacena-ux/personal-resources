---
corso: "GitHub e Git Actions"
fase: "3 — Piattaforma GitHub"
modulo: "15"
titolo: "GitHub API, CLI e Webhooks"
versione: "GitHub 2024"
livello: "intermedio-avanzato"
prerequisiti:
  - "esperienza con HTTP, REST e JSON"
  - "familiarita con la riga di comando Unix/Bash"
  - "conoscenza base di autenticazione (token, OAuth)"
obiettivi:
  - "automatizzare operazioni GitHub con gh CLI e scripting Bash"
  - "interrogare e modificare risorse tramite REST API v3 e GraphQL API v4"
  - "configurare e proteggere webhook con HMAC-SHA256 e replay protection"
  - "scegliere tra GitHub Apps e OAuth Apps per integrazioni sicure"
  - "utilizzare Octokit SDK per costruire automazioni complesse in JavaScript/Python"
tag: [github, API, CLI, webhooks, GraphQL, REST, Octokit, GitHub-Apps, automazione]
---

# GitHub API, CLI e Webhooks — Guida Approfondita

> **Modulo 15** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Automatizzare operazioni GitHub con gh CLI e scripting Bash
> 2. Interrogare e modificare risorse tramite REST API v3 e GraphQL API v4
> 3. Configurare e proteggere webhook con HMAC-SHA256 e replay protection
> 4. Scegliere tra GitHub Apps e OAuth Apps per integrazioni sicure
> 5. Utilizzare Octokit SDK per costruire automazioni complesse in JavaScript/Python
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **`gh` CLI > `curl https://api.github.com/...` per scripting.**
2. **GraphQL API piu efficiente di REST per query complesse.**
3. **Webhook HMAC-SHA256 verify constant-time mandatory.**
4. **Replay protection: `X-GitHub-Delivery` GUID dedup.**
5. **Rotation procedure: webhook secret 90gg.**


## Indice
- [Panoramica](#panoramica)
- [GitHub CLI (gh)](#github-cli-gh)
- [REST API v3](#rest-api-v3)
- [GraphQL API v4](#graphql-api-v4)
- [Webhooks](#webhooks)
- [GitHub Apps vs OAuth Apps](#github-apps-vs-oauth-apps)
- [Octokit SDK](#octokit-sdk)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

GitHub offre molteplici interfacce programmatiche per interagire con la piattaforma: la CLI `gh` per operazioni quotidiane dal terminale, la REST API v3 per integrazioni HTTP standard, la GraphQL API v4 per query flessibili e ottimizzate, e i webhooks per notifiche push in tempo reale. Questa guida esplora ciascuna di queste interfacce con esempi pratici, pattern di autenticazione e strategie per costruire automazioni robuste.

La scelta dell'interfaccia dipende dal caso d'uso: `gh` per automazioni shell e scripting, REST API per integrazioni semplici e ben documentate, GraphQL per query complesse che richiedono dati da multiple risorse, e webhooks per reazioni in tempo reale agli eventi del repository.

---

## GitHub CLI (gh)

### Installazione e Autenticazione

```bash
# Installazione
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install GitHub.cli

# Autenticazione
gh auth login
# Selezionare: GitHub.com → HTTPS → Login with web browser

# Verificare lo stato
gh auth status

# Token di autenticazione (per scripting)
gh auth token
```

### Comandi Principali

#### Repository

```bash
# Clonare
gh repo clone org/repo

# Creare
gh repo create my-project --public --clone

# Fork
gh repo fork org/repo --clone

# Visualizzare informazioni
gh repo view org/repo
gh repo view --json name,description,url,stargazerCount

# Listare repository
gh repo list my-org --limit 50 --json name,visibility
```

#### Pull Requests

```bash
# Creare una PR
gh pr create --title "feat: add OAuth2" --body "## Summary\n..."

# Listare PR
gh pr list
gh pr list --state closed --label "bug" --json number,title,author

# Visualizzare
gh pr view 42
gh pr view 42 --json mergeable,reviews,statusCheckRollup

# Verificare i checks
gh pr checks 42

# Fare checkout di una PR
gh pr checkout 42

# Review
gh pr review 42 --approve
gh pr review 42 --request-changes --body "Fix the SQL injection"
gh pr review 42 --comment --body "LGTM overall"

# Merge
gh pr merge 42 --squash --delete-branch
gh pr merge 42 --auto --squash

# Diff
gh pr diff 42
```

#### Issues

```bash
# Creare
gh issue create --title "Bug: login fails" --label "bug"

# Listare
gh issue list --assignee "@me" --state open

# Visualizzare
gh issue view 42

# Commentare
gh issue comment 42 --body "Working on this"

# Chiudere
gh issue close 42 --reason "completed"

# Trasferire
gh issue transfer 42 org/other-repo
```

#### API Generica

```bash
# Chiamate REST API arbitrarie
gh api repos/{owner}/{repo}
gh api repos/{owner}/{repo}/pulls --jq '.[].title'

# Con paginazione automatica
gh api repos/{owner}/{repo}/issues --paginate --jq '.[].title'

# POST request
gh api repos/{owner}/{repo}/issues -X POST \
  -f title="Nuova issue" \
  -f body="Corpo dell'issue"

# GraphQL
gh api graphql -f query='
  query {
    repository(owner: "org", name: "repo") {
      issues(first: 10, states: OPEN) {
        nodes { title number }
      }
    }
  }
'
```

### Aliases

```bash
# Creare alias personalizzati
gh alias set pv 'pr view'
gh alias set co 'pr checkout'
gh alias set il 'issue list --assignee @me'

# Alias con argomenti
gh alias set pr-ready 'pr ready $1 && pr merge $1 --auto --squash'

# Alias complessi con shell
gh alias set --shell prs-review 'gh pr list --json number,title,author --jq ".[] | \"#\\(.number) \\(.title) by \\(.author.login)\""'

# Listare gli alias
gh alias list

# Eliminare un alias
gh alias delete pv
```

### Releases e Artefatti

```bash
# Creare una release
gh release create v1.2.0 --title "Release 1.2.0" \
  --notes "## Novita\n- Feature A\n- Fix B"

# Creare una release con artefatti allegati
gh release create v1.2.0 ./dist/app-linux.tar.gz ./dist/app-macos.zip \
  --title "Release 1.2.0" --notes-file CHANGELOG.md

# Creare una release draft
gh release create v1.2.0 --draft --title "Release 1.2.0 (Draft)"

# Creare una pre-release
gh release create v1.2.0-rc1 --prerelease --title "Release Candidate 1"

# Listare le release
gh release list --limit 10

# Visualizzare una release specifica
gh release view v1.2.0

# Scaricare artefatti di una release
gh release download v1.2.0 --pattern "*.tar.gz" --dir ./downloads

# Eliminare una release
gh release delete v1.2.0 --yes

# Caricare artefatti aggiuntivi su una release esistente
gh release upload v1.2.0 ./dist/app-windows.exe
```

### Workflow e Actions

Il comando `gh run` permette di monitorare e gestire i workflow di GitHub Actions direttamente dal terminale, eliminando la necessita di navigare l'interfaccia web per operazioni di routine.

```bash
# Listare le esecuzioni recenti dei workflow
gh run list --limit 20

# Listare con filtri specifici
gh run list --workflow deploy.yml --branch main --status failure

# Output JSON per parsing automatizzato
gh run list --json databaseId,status,conclusion,name,headBranch \
  --jq '.[] | select(.conclusion == "failure") | "\(.databaseId) \(.name) \(.headBranch)"'

# Visualizzare i dettagli di un'esecuzione specifica
gh run view 123456789

# Visualizzare i log di un'esecuzione
gh run view 123456789 --log

# Visualizzare i log di un job specifico (filtrando per nome del job)
gh run view 123456789 --log | grep -A 50 "Run tests"

# Scaricare i log completi
gh run download 123456789

# Scaricare artefatti specifici
gh run download 123456789 --name "test-results"

# Monitorare un'esecuzione in tempo reale (watch)
gh run watch 123456789

# Re-eseguire un workflow fallito
gh run rerun 123456789

# Re-eseguire solo i job falliti
gh run rerun 123456789 --failed

# Cancellare un'esecuzione in corso
gh run cancel 123456789

# Trigger manuale di un workflow con input
gh workflow run deploy.yml -f environment=staging -f version=1.2.0

# Listare i workflow disponibili
gh workflow list

# Visualizzare un workflow
gh workflow view deploy.yml

# Abilitare/disabilitare un workflow
gh workflow enable deploy.yml
gh workflow disable deploy.yml
```

### Secrets e Variables

La gestione di secrets e variabili di ambiente per i workflow Actions e disponibile direttamente dalla CLI, permettendo l'automazione della configurazione di ambienti di deploy e pipeline CI/CD.

```bash
# === SECRETS ===

# Impostare un secret a livello di repository
gh secret set API_KEY --body "sk-abc123..."

# Impostare un secret da file
gh secret set TLS_CERT < certificate.pem

# Impostare un secret da pipe (evita che il valore rimanga nella history)
echo "supersecret" | gh secret set DATABASE_PASSWORD

# Impostare un secret per un ambiente specifico
gh secret set DEPLOY_KEY --env production --body "key-value"

# Impostare un secret a livello di organizzazione
gh secret set ORG_SECRET --org my-org --visibility selected \
  --repos "repo1,repo2,repo3"

# Listare i secrets del repository
gh secret list

# Listare i secrets di un ambiente
gh secret list --env production

# Eliminare un secret
gh secret delete API_KEY

# === VARIABLES ===

# Impostare una variabile
gh variable set APP_VERSION --body "1.2.0"

# Impostare una variabile per un ambiente
gh variable set DEPLOY_URL --env staging --body "https://staging.example.com"

# Listare le variabili
gh variable list

# Eliminare una variabile
gh variable delete APP_VERSION
```

### Cache e Codespace

```bash
# === CACHE (Actions) ===

# Listare le cache del repository
gh cache list

# Listare con ordinamento per dimensione
gh cache list --sort size_in_bytes --order desc

# Eliminare una cache specifica
gh cache delete "cache-key-name"

# Eliminare tutte le cache (utile per debugging)
gh cache delete --all

# === CODESPACE ===

# Creare un codespace
gh codespace create --repo org/repo --branch feature-branch

# Listare i codespace attivi
gh codespace list

# Connettersi via SSH a un codespace
gh codespace ssh --codespace "codespace-name"

# Eseguire un comando in un codespace
gh codespace ssh --codespace "codespace-name" -- "npm test"

# Visualizzare i log del codespace
gh codespace logs --codespace "codespace-name"

# Fermare un codespace
gh codespace stop --codespace "codespace-name"

# Eliminare un codespace
gh codespace delete --codespace "codespace-name"

# Port forwarding dal codespace alla macchina locale
gh codespace ports forward 3000:3000 --codespace "codespace-name"
```

### Stato e Notifiche

```bash
# Visualizzare lo stato complessivo (PR assegnate, review richieste, issue)
gh status

# Listare le notifiche
gh api notifications --jq '.[].subject.title'
```

### Output JSON e Filtering con --jq

Uno dei punti di forza di `gh` per lo scripting e la capacita di emettere output strutturato JSON e filtrarlo con espressioni `--jq` (sintassi jq integrata). Questo permette di costruire pipeline di automazione robuste senza dipendenze esterne.

```bash
# Ottenere tutti i campi disponibili in formato JSON
gh pr list --json number,title,author,labels,createdAt,mergeable

# Filtrare PR per autore specifico
gh pr list --json number,title,author \
  --jq '.[] | select(.author.login == "mariorossi") | "#\(.number) \(.title)"'

# Contare le PR aperte per label
gh pr list --json labels \
  --jq '[.[].labels[].name] | group_by(.) | map({label: .[0], count: length}) | sort_by(.count) | reverse'

# Ottenere la media delle review per PR
gh pr list --state merged --limit 50 --json number,reviews \
  --jq 'map(.reviews | length) | add / length'

# Trovare issue senza assegnazione
gh issue list --json number,title,assignees \
  --jq '.[] | select(.assignees | length == 0) | "#\(.number) \(.title)"'

# Esportare dati in formato CSV
gh pr list --state merged --json number,title,author,mergedAt \
  --jq '.[] | [.number, .title, .author.login, .mergedAt] | @csv'

# Combinare con comandi Unix per report complessi
gh pr list --state merged --limit 100 --json author,createdAt,mergedAt \
  --jq '.[] | {author: .author.login, days: (((.mergedAt | fromdateiso8601) - (.createdAt | fromdateiso8601)) / 86400 | floor)}' \
  | jq -s 'group_by(.author) | map({author: .[0].author, avg_days: (map(.days) | add / length | . * 10 | floor / 10)})'
```

### Scripting Avanzato con gh

Quando si integra `gh` in script Bash complessi, e fondamentale implementare gestione degli errori robusta, logging strutturato, e pattern di retry per operazioni non idempotenti. Di seguito un esempio di script di automazione completo.

```bash
#!/usr/bin/env bash
set -euo pipefail

# === Configurazione ===
readonly ORG="my-org"
readonly LABEL_STALE="stale"
readonly DAYS_STALE=30
readonly LOG_FILE="/tmp/gh-automation-$(date +%Y%m%d).log"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"
}

# === Funzione con retry e exponential backoff ===
gh_with_retry() {
    local max_attempts=3
    local attempt=1
    local delay=2

    while [ $attempt -le $max_attempts ]; do
        if gh "$@" 2>>"$LOG_FILE"; then
            return 0
        fi
        log "WARN: gh $1 fallito (tentativo $attempt/$max_attempts), attendo ${delay}s"
        sleep $delay
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done

    log "ERROR: gh $1 fallito dopo $max_attempts tentativi"
    return 1
}

# === Chiudere le issue stale ===
close_stale_issues() {
    local cutoff_date
    cutoff_date=$(date -u -d "-${DAYS_STALE} days" +%Y-%m-%dT%H:%M:%SZ)

    log "Cercando issue piu vecchie di $DAYS_STALE giorni..."

    local issues
    issues=$(gh_with_retry issue list --repo "${ORG}/repo" \
        --state open --json number,title,updatedAt \
        --jq ".[] | select(.updatedAt < \"${cutoff_date}\") | .number")

    local count=0
    for issue_num in $issues; do
        log "Etichettando issue #${issue_num} come stale"
        gh_with_retry issue edit "$issue_num" --repo "${ORG}/repo" \
            --add-label "$LABEL_STALE"
        gh_with_retry issue comment "$issue_num" --repo "${ORG}/repo" \
            --body "Questa issue e inattiva da oltre ${DAYS_STALE} giorni. Verra chiusa automaticamente tra 7 giorni se non ci saranno aggiornamenti."
        count=$((count + 1))
    done

    log "Issue stale elaborate: $count"
}

# === Report PR pendenti ===
generate_pr_report() {
    log "Generando report PR per ${ORG}..."

    gh_with_retry pr list --repo "${ORG}/repo" \
        --state open --json number,title,author,createdAt,reviewDecision \
        --jq '.[] | "PR #\(.number): \(.title) | Autore: \(.author.login) | Creata: \(.createdAt) | Review: \(.reviewDecision // "PENDING")"'
}

# === Esecuzione ===
log "=== Inizio automazione ==="
close_stale_issues
generate_pr_report
log "=== Fine automazione ==="
```

### Variabili di Ambiente per gh

La CLI `gh` riconosce diverse variabili di ambiente che influenzano il comportamento senza richiedere flag espliciti:

| Variabile | Descrizione |
|-----------|-------------|
| `GH_TOKEN` | Token di autenticazione. Sovrascrive il token della sessione `gh auth login`. |
| `GH_HOST` | Host GitHub da utilizzare (default: `github.com`). Utile per GitHub Enterprise Server. |
| `GH_REPO` | Repository predefinito nel formato `owner/repo`. Evita `-R` in ogni comando. |
| `GH_EDITOR` | Editor per operazioni interattive (es. `vim`, `code --wait`). |
| `GH_PAGER` | Pager per output lungo (default: sistema pager o `less`). |
| `GH_DEBUG` | Se impostato a `1` o `true`, abilita output di debug con header HTTP e dettagli delle richieste. |
| `GH_NO_UPDATE_NOTIFIER` | Disabilita il notificatore di aggiornamenti. |
| `GITHUB_TOKEN` | Alternativa a `GH_TOKEN`, supportata per compatibilita con Actions e altri strumenti. |
| `NO_COLOR` | Se impostato, disabilita l'output colorato (standard per CLI Unix). |

```bash
# Esempio: usare gh in un ambiente CI senza login interattivo
export GH_TOKEN="ghp_xxxxxxxxxxxx"
export GH_REPO="my-org/my-repo"

# Ora tutti i comandi gh usano questo token e repository
gh pr list
gh issue list
gh run list
```

### Extensions

```bash
# Listare le extension disponibili
gh extension browse

# Installare un'extension
gh extension install dlvhdr/gh-dash     # Dashboard interattiva
gh extension install github/gh-copilot  # GitHub Copilot CLI
gh extension install mislav/gh-branch   # Gestione branch avanzata

# Listare extension installate
gh extension list

# Aggiornare
gh extension upgrade --all
```

### Creare un'Extension Personalizzata

Le extension `gh` sono repository GitHub il cui nome inizia con il prefisso `gh-` e contengono un eseguibile con lo stesso nome. Si possono scrivere in qualsiasi linguaggio: Bash, Go (con la libreria `go-gh`), Python, o altri. La libreria `go-gh` fornisce accesso diretto all'autenticazione, all'API client, e al parsing JSON/jq.

```bash
# Creare lo scaffold per una nuova extension
gh extension create my-tool
# Crea il repository gh-my-tool con la struttura base

# Creare un'extension con template Go (consigliato per distribuzioni compilate)
gh extension create --precompiled=go my-tool

# Struttura tipica dell'extension:
# gh-my-tool/
# ├── gh-my-tool          # Eseguibile (per script Bash)
# ├── main.go             # Sorgente (per Go)
# ├── go.mod
# └── README.md

# Esempio di extension Bash minimale (gh-my-tool):
cat << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

# Usa gh api per ottenere dati
gh api repos/{owner}/{repo}/pulls \
  --jq '.[] | "#\(.number) \(.title) [\(.user.login)]"'
SCRIPT

# Installare l'extension in sviluppo locale
cd gh-my-tool && gh extension install .

# Testare l'extension
gh my-tool

# Pubblicare: push del repository su GitHub, poi gli utenti installano con:
# gh extension install username/gh-my-tool
```

### Ecosistema Extension: Evoluzione 2025-2026

L'ecosistema delle extension `gh` si e evoluto significativamente nel biennio 2025-2026, con cambiamenti architetturali importanti che riflettono la direzione strategica di GitHub verso integrazioni piu profonde con l'intelligenza artificiale e l'automazione basata su agenti.

**Installazione senza autenticazione:** A partire dalla versione 2.62 di `gh`, l'installazione delle extension non richiede piu un token di autenticazione valido per scaricare release asset pubblici. Questo significa che e possibile installare extension anche senza aver eseguito `gh auth login`, semplificando significativamente la configurazione in ambienti containerizzati e pipeline CI/CD dove l'autenticazione potrebbe non essere ancora configurata.

```bash
# Installare un'extension senza autenticazione preventiva
# (funziona dalla versione gh 2.62+)
gh extension install dlvhdr/gh-dash

# Verificare la versione di gh
gh --version
# gh version 2.72.0 (2026-05-10)
```

**Installazione automatica delle extension ufficiali:** Quando si esegue un comando che corrisponde a un'extension ufficiale nota ma non ancora installata (come `gh stack` o `gh aw`), la CLI offre automaticamente di installarla invece di mostrare un errore generico. Questo migliora drasticamente l'esperienza utente per le extension first-party distribuite dal team GitHub.

```bash
# Esempio: eseguire gh stack senza averlo installato
gh stack
# Extension github/gh-stack is not installed.
# Would you like to install it? [Y/n]
```

**Agent Skills — la nuova frontiera:** Una delle aggiunte piu significative all'ecosistema `gh` nel 2025-2026 e il concetto di *agent skills*. Le agent skills sono set portatili di istruzioni, script e risorse che insegnano agli agenti AI (come coding assistant) a eseguire compiti specifici. Il nuovo comando `gh skill` consente di scoprire, installare, gestire e pubblicare agent skills direttamente dai repository GitHub.

```bash
# Scoprire skills disponibili
gh skill search "deploy kubernetes"

# Installare una skill
gh skill install org/deploy-k8s-skill

# Listare le skills installate
gh skill list

# Pubblicare una skill dal repository corrente
gh skill publish
```

Le agent skills rappresentano un cambiamento di paradigma: invece di scrivere extension compilate che estendono la CLI, si creano pacchetti di conoscenza strutturata che gli agenti AI possono utilizzare per automatizzare task complessi con contesto e guardrail predefiniti.

**Deprecazione di gh-copilot:** L'extension `gh-copilot`, precedentemente utilizzata per integrare GitHub Copilot nella CLI, ha cessato di funzionare il 25 ottobre 2025. Le sue funzionalita sono state sostituite dalla nuova GitHub Copilot CLI standalone, un assistente AI completamente agentitico che opera come applicazione indipendente. Gli utenti che utilizzavano `gh copilot suggest` o `gh copilot explain` devono migrare al nuovo strumento.

```bash
# DEPRECATO — non funziona piu dal 25/10/2025
gh copilot suggest "find large files in git history"

# NUOVO — utilizzare Copilot CLI standalone
# La nuova CLI ha capacita agentiche complete,
# inclusa l'esecuzione autonoma di comandi e la navigazione del codebase
```

**Sviluppo di extension con go-gh v2:** Per le extension compilate, la libreria `go-gh` v2 fornisce accesso diretto all'autenticazione, al client API, al parsing JSON/jq e alla configurazione dell'utente. Lo scaffolding con `gh extension create --precompiled=go` genera automaticamente la struttura con `go-gh` come dipendenza, inclusi helper per l'output tabulare, la selezione interattiva e la gestione dei colori nel terminale.

```bash
# Creare un'extension Go con template aggiornato
gh extension create --precompiled=go my-analyzer

# Struttura generata:
# gh-my-analyzer/
# ├── main.go             # Entry point con go-gh v2
# ├── go.mod              # Dipendenze (include go-gh)
# ├── go.sum
# └── .github/
#     └── workflows/
#         └── release.yml  # Build automatica multi-piattaforma

# Esempio di utilizzo go-gh v2 nel codice:
# import "github.com/cli/go-gh/v2/pkg/api"
# client, _ := api.DefaultRESTClient()
# var response struct { Login string }
# client.Get("user", &response)
```

### Extension Raccomandate (2025-2026)

| Extension | Descrizione | Stelle |
|-----------|-------------|--------|
| `dlvhdr/gh-dash` | Dashboard interattiva per PR e issue con UI TUI | 7.5k+ |
| `vilmibm/gh-screensaver` | Screensaver ASCII nel terminale | 400+ |
| `seachicken/gh-poi` | Pulizia automatica dei branch locali dopo merge | 350+ |
| `mislav/gh-branch` | Gestione avanzata dei branch | 300+ |
| `actions/gh-actions-cache` | Gestione della cache di GitHub Actions | 327+ |

---

## REST API v3

### Autenticazione

```bash
# Personal Access Token (header)
curl -H "Authorization: Bearer ghp_xxxxxxxxxxxx" \
  https://api.github.com/user

# Token nel URL (sconsigliato)
curl https://api.github.com/user?access_token=ghp_xxxxxxxxxxxx

# GitHub App Installation Token
curl -H "Authorization: Bearer ghs_xxxxxxxxxxxx" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/{owner}/{repo}
```

### Paginazione

La REST API restituisce risultati paginati. I link di navigazione sono nell'header `Link`:

```bash
# Prima pagina (30 risultati per default)
curl -I "https://api.github.com/repos/{owner}/{repo}/issues"
# Link: <https://api.github.com/.../issues?page=2>; rel="next",
#        <https://api.github.com/.../issues?page=5>; rel="last"

# Specificare la dimensione della pagina (max 100)
curl "https://api.github.com/repos/{owner}/{repo}/issues?per_page=100&page=1"

# Paginazione automatica con gh
gh api repos/{owner}/{repo}/issues --paginate
```

### Rate Limits

```bash
# Verificare i rate limits
curl -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/rate_limit

# Output:
# {
#   "resources": {
#     "core": {
#       "limit": 5000,        # Richieste per ora (autenticato)
#       "remaining": 4999,
#       "reset": 1700000000   # Unix timestamp del reset
#     },
#     "search": {
#       "limit": 30,          # Richieste al minuto per search
#       "remaining": 29,
#       "reset": 1700000060
#     },
#     "graphql": {
#       "limit": 5000,
#       "remaining": 4999,
#       "reset": 1700000000
#     }
#   }
# }

# Non autenticato: 60 richieste/ora
# Autenticato PAT: 5000 richieste/ora
# GitHub App: 5000 richieste/ora per installazione
```

### Versioning dell'API

A partire dal 2022, GitHub ha introdotto un sistema di versionamento basato su date di calendario (calendar-based versioning) per la REST API. Ogni versione e identificata dalla data di rilascio (es. `2022-11-28`, `2026-03-10`). Questo approccio permette a GitHub di evolvere l'API introducendo breaking changes in modo controllato, garantendo almeno 24 mesi di supporto per ogni versione precedente.

```bash
# Specificare la versione dell'API tramite header
curl -H "Authorization: Bearer $TOKEN" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/{owner}/{repo}

# Senza l'header, il default e la versione 2022-11-28
# IMPORTANTE: specificare sempre la versione per evitare
# comportamenti inattesi quando GitHub rilascia nuove versioni

# Verificare la versione in uso nella risposta
# L'header di risposta x-github-api-version conferma la versione utilizzata
curl -I -H "Authorization: Bearer $TOKEN" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/zen
# < x-github-api-version: 2026-03-10
```

**Breaking changes nella versione 2026-03-10:**

| Modifica | Dettaglio |
|----------|-----------|
| Campo `cvss` rimosso | Sostituito da `cvss_severities` contenente `cvss_v3` e `cvss_v4` negli advisory |
| Campo `merge_commit_sha` rimosso | Non piu presente nelle risposte degli endpoint pull request |
| Risposta workflow dispatch cambiata | Da `204 No Content` a `200 OK` con dettagli del workflow run |
| Campo singolare `assignee` rimosso | Usare `assignees` (array) negli endpoint issue e pull request |

### Conditional Requests e Caching

Le conditional requests sono fondamentali per ridurre il consumo di rate limit e migliorare le prestazioni delle applicazioni che interrogano frequentemente l'API. Quando il server risponde con `304 Not Modified`, la richiesta non viene conteggiata nel rate limit primario.

```bash
# === ETAG CACHING ===

# Prima richiesta: salvare l'ETag dalla risposta
curl -i -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo} 2>/dev/null \
  | grep -i etag
# ETag: "abc123def456..."

# Richieste successive: includere If-None-Match con l'ETag
curl -H "Authorization: Bearer $TOKEN" \
  -H 'If-None-Match: "abc123def456..."' \
  -w "\nHTTP Status: %{http_code}\n" \
  https://api.github.com/repos/{owner}/{repo}
# Se la risorsa non e cambiata: HTTP Status: 304 (non consuma rate limit)
# Se la risorsa e cambiata: HTTP Status: 200 (nuovo ETag nella risposta)

# === IF-MODIFIED-SINCE ===

# Usare il timestamp dell'ultimo fetch
curl -H "Authorization: Bearer $TOKEN" \
  -H "If-Modified-Since: Thu, 23 May 2026 10:00:00 GMT" \
  https://api.github.com/repos/{owner}/{repo}/issues

# === Script con caching automatico ===
ETAG_FILE="/tmp/gh-etag-cache.json"
CACHE_FILE="/tmp/gh-data-cache.json"

fetch_with_cache() {
    local url="$1"
    local etag=""

    if [ -f "$ETAG_FILE" ]; then
        etag=$(jq -r ".[\"$url\"] // empty" "$ETAG_FILE" 2>/dev/null)
    fi

    local etag_header=""
    if [ -n "$etag" ]; then
        etag_header="-H \"If-None-Match: $etag\""
    fi

    local response
    response=$(curl -s -D - \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2026-03-10" \
        ${etag_header} \
        "$url")

    local http_code
    http_code=$(echo "$response" | head -1 | grep -oP '\d{3}')

    if [ "$http_code" = "304" ]; then
        echo "CACHE HIT per $url"
        cat "$CACHE_FILE"
    else
        local new_etag
        new_etag=$(echo "$response" | grep -i "^etag:" | awk '{print $2}' | tr -d '\r')
        local body
        body=$(echo "$response" | sed -n '/^\r$/,$p' | tail -n +2)

        # Aggiornare cache
        echo "$body" > "$CACHE_FILE"
        jq ". + {\"$url\": \"$new_etag\"}" "$ETAG_FILE" 2>/dev/null > "${ETAG_FILE}.tmp" \
            && mv "${ETAG_FILE}.tmp" "$ETAG_FILE" \
            || echo "{\"$url\": \"$new_etag\"}" > "$ETAG_FILE"

        echo "$body"
    fi
}
```

**Limitazioni importanti del caching con ETag:**

- Gli ETag sono per-pagina, non per-collezione: se una collezione ha 5 pagine, ogni pagina ha il proprio ETag.
- GraphQL non supporta ETag: il caching condizionale e esclusivo della REST API.
- Gli ETag sono associati al token: un nuovo installation token (max TTL 1 ora per GitHub App) invalida gli ETag precedenti.
- Il risparmio reale dipende dalla frequenza di modifica: se i dati cambiano raramente, il caching ETag puo ridurre il consumo di rate limit fino al 90%.

### Secondary Rate Limits

Oltre al rate limit primario (5000 richieste/ora per utenti autenticati), GitHub applica rate limit secondari per prevenire abusi e garantire la disponibilita del servizio. I secondary rate limit non sono legati a un conteggio orario fisso, ma a pattern di utilizzo.

**Trigger dei secondary rate limit:**

| Condizione | Limite |
|------------|--------|
| Richieste concorrenti | Max 100 richieste in parallelo |
| Richieste per endpoint/minuto | Max 900 punti al minuto per endpoint REST |
| Tempo CPU consumato | Max 90 secondi CPU per 60 secondi reali |
| Creazione contenuto | Limiti specifici per creazione issue, commenti, etc. |

```bash
# Quando si colpisce un secondary rate limit, la risposta e 403 o 429
# con il messaggio: "You have exceeded a secondary rate limit"

# Header da controllare nella risposta:
# Retry-After: 60    ← attendere questo numero di secondi prima di riprovare
# X-RateLimit-Remaining: 0

# === Implementazione exponential backoff con jitter ===

retry_with_backoff() {
    local url="$1"
    local max_retries=5
    local base_delay=1

    for ((i=1; i<=max_retries; i++)); do
        local response
        local http_code

        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2026-03-10" \
            "$url")

        http_code=$(echo "$response" | tail -1)
        local body
        body=$(echo "$response" | sed '$d')

        case "$http_code" in
            200|201|204)
                echo "$body"
                return 0
                ;;
            304)
                echo "NOT_MODIFIED"
                return 0
                ;;
            403|429)
                local retry_after
                retry_after=$(curl -sI -H "Authorization: Bearer $TOKEN" "$url" \
                    | grep -i "retry-after" | awk '{print $2}' | tr -d '\r')

                if [ -n "$retry_after" ]; then
                    echo "Rate limited. Attendo ${retry_after}s (Retry-After)" >&2
                    sleep "$retry_after"
                else
                    # Exponential backoff con jitter
                    local delay=$(( base_delay * (2 ** (i - 1)) ))
                    local jitter=$(( RANDOM % delay ))
                    local total_delay=$(( delay + jitter ))
                    echo "Rate limited. Backoff: ${total_delay}s (tentativo $i/$max_retries)" >&2
                    sleep "$total_delay"
                fi
                ;;
            *)
                echo "Errore HTTP $http_code" >&2
                return 1
                ;;
        esac
    done

    echo "Fallito dopo $max_retries tentativi" >&2
    return 1
}
```

### Search API

L'API di ricerca di GitHub permette di cercare attraverso repository, codice, issue, utenti e commit. Ha rate limit dedicati: 30 richieste al minuto per utenti autenticati, 10 per non autenticati.

```bash
# Cercare repository per topic e linguaggio
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/repositories?q=topic:machine-learning+language:python&sort=stars&order=desc&per_page=10"

# Cercare codice (richiede autenticazione)
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/code?q=hmac+sha256+repo:org/repo+extension:py"

# Cercare issue e PR
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/issues?q=is:pr+is:merged+repo:org/repo+merged:>2026-01-01"

# Cercare commit
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/commits?q=author:mariorossi+repo:org/repo&sort=author-date"

# Cercare utenti
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/users?q=location:Italy+type:user&sort=repositories"

# Qualificatori avanzati per la ricerca codice
# filename:   - cercare per nome file
# extension:  - cercare per estensione
# path:       - cercare in un percorso specifico
# size:       - filtrare per dimensione file
# language:   - filtrare per linguaggio
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/code?q=createHmac+filename:webhook+extension:ts+repo:org/repo"
```

### Media Types e Content Negotiation

L'header `Accept` controlla il formato della risposta e puo attivare funzionalita specifiche dell'API. GitHub supporta diversi media type personalizzati.

```bash
# Formato JSON standard (default)
curl -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/{owner}/{repo}

# Ottenere il contenuto raw di un file
curl -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.raw+json" \
  "https://api.github.com/repos/{owner}/{repo}/contents/README.md"

# Ottenere il diff di una PR in formato patch
curl -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.patch" \
  "https://api.github.com/repos/{owner}/{repo}/pulls/42"

# Ottenere il diff in formato diff standard
curl -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.diff" \
  "https://api.github.com/repos/{owner}/{repo}/pulls/42"

# Contenuto HTML renderizzato (per Markdown)
curl -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.html+json" \
  "https://api.github.com/repos/{owner}/{repo}/readme"

# Renderizzare Markdown arbitrario
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/markdown \
  -d '{"text":"# Hello\n\nTesto con **grassetto** e `codice`","mode":"gfm","context":"org/repo"}'
```

### Esempi di Chiamate REST

```bash
# Ottenere informazioni sul repository
curl -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo}

# Listare i branch
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/branches"

# Creare un'issue
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/{owner}/{repo}/issues \
  -d '{"title":"Bug report","body":"Description","labels":["bug"]}'

# Creare un commento su una PR
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/pulls/42/comments \
  -d '{"body":"LGTM!","commit_id":"abc1234","path":"src/app.js","line":10,"side":"RIGHT"}'

# Trigger di un workflow dispatch
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/actions/workflows/deploy.yml/dispatches \
  -d '{"ref":"main","inputs":{"environment":"production"}}'

# Ottenere lo stato dei checks di un commit
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/commits/abc1234/check-runs"

# === Gestione Branch Protection ===

# Ottenere le regole di protezione di un branch
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/branches/main/protection"

# Impostare branch protection
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/{owner}/{repo}/branches/main/protection" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/tests", "ci/lint"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 2,
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": true
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false
  }'

# === Gestione Deploy Keys ===

# Aggiungere una deploy key
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/keys" \
  -d '{"title":"CI Server","key":"ssh-ed25519 AAAA...","read_only":true}'

# Listare le deploy keys
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/keys"

# === Environments ===

# Listare gli ambienti
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/environments"

# Creare/aggiornare un ambiente con regole di protezione
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/environments/production" \
  -d '{
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
  }'
```

---

## GraphQL API v4

### Fondamenti

La GraphQL API permette di richiedere esattamente i dati necessari in una singola query, eliminando l'over-fetching e l'under-fetching tipici delle REST API.

```bash
# Query di base
gh api graphql -f query='
  query {
    viewer {
      login
      name
      email
    }
  }
'

# Query con variabili
gh api graphql -f query='
  query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      name
      description
      stargazerCount
      forkCount
      primaryLanguage { name }
      defaultBranchRef { name }
    }
  }
' -f owner="org" -f name="repo"
```

### Query Complesse

```graphql
# Ottenere PR con review, checks e files modificati
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      title
      state
      author { login }
      createdAt
      mergeable

      reviews(first: 10) {
        nodes {
          author { login }
          state
          body
          submittedAt
        }
      }

      commits(last: 1) {
        nodes {
          commit {
            statusCheckRollup {
              state
              contexts(first: 20) {
                nodes {
                  ... on CheckRun {
                    name
                    conclusion
                    status
                  }
                  ... on StatusContext {
                    context
                    state
                  }
                }
              }
            }
          }
        }
      }

      files(first: 50) {
        nodes {
          path
          additions
          deletions
        }
      }
    }
  }
}
```

### Mutations

```graphql
# Creare un'issue
mutation {
  createIssue(input: {
    repositoryId: "R_xxxx"
    title: "Bug: login fails"
    body: "Description of the bug"
    labelIds: ["LA_xxxx"]
  }) {
    issue {
      number
      url
    }
  }
}

# Aggiungere un commento
mutation {
  addComment(input: {
    subjectId: "I_xxxx"    # ID dell'issue o PR
    body: "Thanks for reporting!"
  }) {
    commentEdge {
      node {
        body
        createdAt
      }
    }
  }
}

# Approvare una PR
mutation {
  addPullRequestReview(input: {
    pullRequestId: "PR_xxxx"
    event: APPROVE
    body: "LGTM!"
  }) {
    pullRequestReview {
      state
    }
  }
}
```

### Global Node IDs

Ogni oggetto in GitHub ha un identificatore globale unico (node ID) accessibile sia via REST che GraphQL. Questo permette di ottenere un ID via REST e utilizzarlo in una mutation GraphQL, o viceversa. A partire dal 2024, GitHub ha migrato i node ID dal formato legacy (MDExxx) al nuovo formato con prefisso tipo (es. `R_`, `PR_`, `I_`).

```bash
# Ottenere il node ID di un repository via REST
curl -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo} \
  | jq '.node_id'
# Output: "R_kgDOxxxxxxxx"

# Usare il node ID in una query GraphQL (direct node lookup)
gh api graphql -f query='
  query($nodeId: ID!) {
    node(id: $nodeId) {
      ... on Repository {
        name
        description
        stargazerCount
      }
    }
  }
' -f nodeId="R_kgDOxxxxxxxx"

# Ottenere il node ID di un'issue via REST e usarlo per una mutation
ISSUE_NODE_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/issues/42 \
  | jq -r '.node_id')

gh api graphql -f query='
  mutation($issueId: ID!) {
    addComment(input: {subjectId: $issueId, body: "Commento via GraphQL"}) {
      commentEdge {
        node { body createdAt }
      }
    }
  }
' -f issueId="$ISSUE_NODE_ID"
```

### Paginazione con Cursori (Relay Connection)

La GraphQL API di GitHub implementa il pattern Relay Connection per la paginazione. Invece di numeri di pagina (come REST), si utilizzano cursori opachi che puntano a posizioni specifiche nel dataset.

```graphql
# Paginazione forward (primo→ultimo) con after/first
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $cursor, states: OPEN, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      edges {
        cursor
        node {
          number
          title
          author { login }
          createdAt
          labels(first: 5) {
            nodes { name color }
          }
        }
      }
    }
  }
}

# Paginazione backward (ultimo→primo) con before/last
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(last: 20, before: $cursor, states: OPEN) {
      pageInfo {
        hasPreviousPage
        startCursor
      }
      edges {
        node { number title }
      }
    }
  }
}
```

```bash
# Script Bash per iterare tutte le pagine
fetch_all_issues() {
    local owner="$1"
    local name="$2"
    local cursor=""
    local has_next="true"
    local all_issues="[]"

    while [ "$has_next" = "true" ]; do
        local cursor_arg=""
        if [ -n "$cursor" ]; then
            cursor_arg="-f cursor=$cursor"
        fi

        local result
        result=$(gh api graphql -f query='
          query($owner: String!, $name: String!, $cursor: String) {
            repository(owner: $owner, name: $name) {
              issues(first: 100, after: $cursor, states: OPEN) {
                pageInfo { hasNextPage endCursor }
                nodes { number title author { login } }
              }
            }
          }
        ' -f owner="$owner" -f name="$name" $cursor_arg)

        local page_issues
        page_issues=$(echo "$result" | jq '.data.repository.issues.nodes')
        all_issues=$(echo "$all_issues $page_issues" | jq -s '.[0] + .[1]')

        has_next=$(echo "$result" | jq -r '.data.repository.issues.pageInfo.hasNextPage')
        cursor=$(echo "$result" | jq -r '.data.repository.issues.pageInfo.endCursor')

        echo "Recuperate $(echo "$all_issues" | jq length) issue..." >&2
    done

    echo "$all_issues"
}

# Utilizzo
fetch_all_issues "my-org" "my-repo" | jq '.[].title'
```

### Fragments e Riutilizzo delle Query

I fragments permettono di definire set di campi riutilizzabili, evitando la duplicazione nelle query complesse.

```graphql
# Definire fragments per set di campi comuni
fragment PullRequestFields on PullRequest {
  number
  title
  state
  author { login avatarUrl }
  createdAt
  mergedAt
  mergeable
  additions
  deletions
  changedFiles
}

fragment ReviewFields on PullRequestReview {
  author { login }
  state
  body
  submittedAt
}

# Usare i fragments in una query
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    openPRs: pullRequests(first: 10, states: OPEN) {
      nodes {
        ...PullRequestFields
        reviews(first: 5) {
          nodes { ...ReviewFields }
        }
      }
    }
    mergedPRs: pullRequests(first: 10, states: MERGED, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        ...PullRequestFields
      }
    }
  }
}

# Inline fragments per union types e interfacce
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 5, states: OPEN) {
      nodes {
        title
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup {
                contexts(first: 20) {
                  nodes {
                    ... on CheckRun {
                      __typename
                      name
                      conclusion
                      detailsUrl
                    }
                    ... on StatusContext {
                      __typename
                      context
                      state
                      targetUrl
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Rate Limit e Costo delle Query GraphQL

A differenza della REST API dove ogni richiesta costa 1 punto, nella GraphQL API il costo dipende dalla complessita della query. Il limite e di 5.000 punti/ora (10.000 per app in organizzazioni Enterprise Cloud) con un massimo di 2.000 punti/minuto.

```graphql
# Includere il campo rateLimit nella query per monitorare il consumo
query {
  rateLimit {
    limit            # Limite totale (5000)
    cost             # Costo di QUESTA query
    remaining        # Punti rimanenti
    resetAt          # Timestamp ISO 8601 del reset
    nodeCount        # Numero di nodi richiesti
  }
  repository(owner: "org", name: "repo") {
    issues(first: 100) {
      nodes {
        title
        labels(first: 10) {
          nodes { name }
        }
      }
    }
  }
}

# Il costo viene calcolato prima dell'esecuzione:
# - Ogni connessione (first/last) aggiunge al costo
# - Il costo = numero di nodi che POTREBBERO essere restituiti
# - Esempio: issues(first: 100) con labels(first: 10) = 100 + (100 * 10) = 1100 punti
```

**Limiti di risorse (introdotti nel 2025):**

GitHub ha introdotto limiti addizionali per evitare query eccessivamente pesanti:

| Limite | Valore |
|--------|--------|
| Max nodi per query | 500.000 |
| Max nodi richiesti (`first`/`last`) | 100 per connessione |
| Max profondita query | ~12 livelli di nesting |
| Timeout query | 10 secondi |
| Max punti/minuto | 2.000 |

**Pattern da evitare:**

```graphql
# SBAGLIATO: query troppo profonda e costosa
query {
  repository(owner: "org", name: "repo") {
    pullRequests(first: 100) {        # 100
      nodes {
        reviews(first: 50) {           # 100 * 50 = 5000
          nodes {
            comments(first: 20) {      # 5000 * 20 = 100000
              nodes { body }
            }
          }
        }
      }
    }
  }
}
# Costo: ~105.100 punti! Superera il limite di risorse.

# CORRETTO: ridurre la profondita e paginare separatamente
query {
  repository(owner: "org", name: "repo") {
    pullRequests(first: 20) {          # 20
      nodes {
        number
        reviews(first: 5) {             # 20 * 5 = 100
          nodes {
            author { login }
            state
          }
        }
      }
    }
  }
}
# Costo: ~120 punti. Poi paginare se servono piu risultati.
```

### Gestione Errori GraphQL

Le risposte GraphQL restituiscono sempre status HTTP 200, anche in caso di errore. Gli errori sono nel campo `errors` della risposta JSON.

```bash
# Risposta con errore parziale
# {
#   "data": {
#     "repository": null
#   },
#   "errors": [
#     {
#       "type": "NOT_FOUND",
#       "path": ["repository"],
#       "locations": [{"line": 2, "column": 3}],
#       "message": "Could not resolve to a Repository with the name 'org/nonexistent'."
#     }
#   ]
# }

# Script per gestire errori GraphQL
graphql_query() {
    local query="$1"
    shift
    local vars=("$@")

    local result
    result=$(gh api graphql -f query="$query" "${vars[@]}" 2>&1)
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo "Errore nella chiamata GraphQL: $result" >&2
        return 1
    fi

    # Verificare se ci sono errori nella risposta
    local errors
    errors=$(echo "$result" | jq -r '.errors // empty')

    if [ -n "$errors" ] && [ "$errors" != "null" ]; then
        echo "Errori GraphQL:" >&2
        echo "$result" | jq '.errors[] | "  [\(.type)] \(.message)"' -r >&2
        return 1
    fi

    echo "$result" | jq '.data'
}

# Utilizzo
graphql_query '
  query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      stargazerCount
      forkCount
    }
  }
' -f owner="org" -f name="repo"
```

### Schema Explorer

```bash
# Esplorare lo schema GraphQL
gh api graphql -f query='
  query {
    __type(name: "Repository") {
      fields {
        name
        description
        type { name kind }
      }
    }
  }
'

# Esplorare i campi di un tipo specifico
gh api graphql -f query='
  query {
    __type(name: "PullRequest") {
      name
      fields {
        name
        type {
          name
          kind
          ofType { name kind }
        }
      }
    }
  }
' | jq '.data.__type.fields[] | "\(.name): \(.type.name // .type.ofType.name)"' -r

# Esplorare le mutation disponibili
gh api graphql -f query='
  query {
    __schema {
      mutationType {
        fields {
          name
          description
        }
      }
    }
  }
' | jq '.data.__schema.mutationType.fields[] | "\(.name): \(.description)"' -r | head -30

# GitHub GraphQL Explorer interattivo:
# https://docs.github.com/en/graphql/overview/explorer
```

### Direttive GraphQL e Tecniche Avanzate

Le direttive GraphQL permettono di modificare dinamicamente la struttura delle query in base a condizioni runtime, senza dover costruire query diverse per ogni scenario. GitHub supporta le direttive standard `@include` e `@skip`, oltre a tecniche avanzate come il field aliasing e il query batching.

#### Direttive Condizionali: @include e @skip

Le direttive `@include(if: Boolean!)` e `@skip(if: Boolean!)` permettono di includere o escludere campi dalla query in base a variabili booleane. Sono particolarmente utili per costruire interfacce utente dove l'utente puo selezionare il livello di dettaglio desiderato.

```graphql
# Query con inclusione condizionale dei dettagli
query($owner: String!, $name: String!, $withReviews: Boolean!, $withFiles: Boolean!) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 20, states: OPEN) {
      nodes {
        number
        title
        author { login }
        createdAt

        # Includi le review solo se richiesto
        reviews(first: 10) @include(if: $withReviews) {
          nodes {
            author { login }
            state
            submittedAt
          }
        }

        # Includi i file modificati solo se richiesto
        files(first: 50) @include(if: $withFiles) {
          nodes {
            path
            additions
            deletions
          }
        }
      }
    }
  }
}
```

```bash
# Utilizzo dalla CLI con variabili condizionali
gh api graphql -f query='
  query($owner: String!, $name: String!, $withReviews: Boolean!, $withFiles: Boolean!) {
    repository(owner: $owner, name: $name) {
      pullRequests(first: 10, states: OPEN) {
        nodes {
          number
          title
          reviews(first: 5) @include(if: $withReviews) {
            nodes { author { login } state }
          }
          files(first: 20) @skip(if: $withReviews) {
            nodes { path additions deletions }
          }
        }
      }
    }
  }
' -f owner="org" -f name="repo" -F withReviews=true -F withFiles=false
# Nota: -F (maiuscolo) per variabili non-stringa (boolean, int)
```

La direttiva `@skip` e l'inversa di `@include`: `@skip(if: true)` equivale a `@include(if: false)`. Si possono usare insieme per creare logiche di rendering mutuamente esclusivo: ad esempio, mostrare le review OPPURE i file, mai entrambi, a seconda di una singola variabile booleana.

#### Field Aliasing

Gli alias permettono di rinominare i campi nella risposta e, soprattutto, di richiedere lo stesso campo piu volte con parametri diversi nella stessa query. Questo e essenziale per confronti e dashboard che necessitano di dati aggregati da prospettive diverse.

```graphql
# Confrontare PR aperte vs chiuse con alias
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    # Alias: stesso campo "pullRequests" con filtri diversi
    openPRs: pullRequests(states: OPEN) {
      totalCount
    }
    closedPRs: pullRequests(states: CLOSED) {
      totalCount
    }
    mergedPRs: pullRequests(states: MERGED) {
      totalCount
    }

    # Alias per issue con label diversi
    bugs: issues(states: OPEN, labels: ["bug"]) {
      totalCount
    }
    features: issues(states: OPEN, labels: ["enhancement"]) {
      totalCount
    }
    criticalBugs: issues(states: OPEN, labels: ["bug", "priority:critical"]) {
      totalCount
    }

    # Statistiche generali del repository
    stars: stargazerCount
    forks: forkCount
  }
}
```

```bash
# Dashboard rapida dal terminale con alias
gh api graphql -f query='
  query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      open: pullRequests(states: OPEN) { totalCount }
      merged: pullRequests(states: MERGED) { totalCount }
      openIssues: issues(states: OPEN) { totalCount }
      closedIssues: issues(states: CLOSED) { totalCount }
    }
  }
' -f owner="org" -f name="repo" \
  | jq '.data.repository | "PR aperte: \(.open.totalCount) | PR merged: \(.merged.totalCount) | Issue aperte: \(.openIssues.totalCount) | Issue chiuse: \(.closedIssues.totalCount)"' -r
```

#### Query Batching: Operazioni Multiple in una Singola Richiesta

GraphQL consente di eseguire operazioni su risorse multiple nella stessa query, riducendo drasticamente il numero di chiamate di rete. Questo e particolarmente vantaggioso quando si devono confrontare o aggregare dati da repository diversi.

```graphql
# Raccogliere statistiche da repository multipli in una singola chiamata
query {
  frontend: repository(owner: "my-org", name: "frontend") {
    stargazerCount
    forkCount
    issues(states: OPEN) { totalCount }
    pullRequests(states: OPEN) { totalCount }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 1) {
            nodes { committedDate message }
          }
        }
      }
    }
  }
  backend: repository(owner: "my-org", name: "backend-api") {
    stargazerCount
    forkCount
    issues(states: OPEN) { totalCount }
    pullRequests(states: OPEN) { totalCount }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 1) {
            nodes { committedDate message }
          }
        }
      }
    }
  }
  infrastructure: repository(owner: "my-org", name: "infra-terraform") {
    stargazerCount
    forkCount
    issues(states: OPEN) { totalCount }
    pullRequests(states: OPEN) { totalCount }
  }
}
```

Questa singola query sostituisce almeno 3 chiamate REST API separate, ciascuna delle quali richiederebbe ulteriori chiamate per issue, PR e commit. Il costo in punti GraphQL rimane contenuto perche il numero di nodi richiesti e basso per ogni repository.

#### Introspection Avanzata con __typename

Il campo meta `__typename` e disponibile su ogni tipo GraphQL e restituisce il nome del tipo concreto dell'oggetto. E utile per distinguere tra tipi in union type e interfacce, e per il debugging delle query.

```graphql
# Identificare il tipo concreto di ogni nodo nel timeline di una PR
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      timelineItems(first: 30) {
        nodes {
          __typename
          ... on PullRequestCommit {
            commit { message abbreviatedOid }
          }
          ... on ReviewRequestedEvent {
            requestedReviewer {
              ... on User { login }
              ... on Team { name }
            }
          }
          ... on IssueComment {
            author { login }
            body
            createdAt
          }
          ... on PullRequestReview {
            author { login }
            state
          }
          ... on MergedEvent {
            actor { login }
            mergeRefName
          }
          ... on LabeledEvent {
            label { name color }
          }
        }
      }
    }
  }
}
```

Questa query recupera l'intera timeline di una PR con tutti i tipi di evento, utilizzando inline fragments per accedere ai campi specifici di ogni tipo. Il campo `__typename` nell'output permette al client di fare dispatching sull'handler appropriato per ogni tipo di evento.

---

## Webhooks

### Configurazione

I webhooks inviano richieste HTTP POST a un URL specificato quando si verificano eventi nel repository.

```bash
# Creare un webhook via API
gh api repos/{owner}/{repo}/hooks -X POST \
  --input - << 'EOF'
{
  "name": "web",
  "active": true,
  "events": ["push", "pull_request", "issues"],
  "config": {
    "url": "https://myserver.com/webhook",
    "content_type": "json",
    "secret": "my-webhook-secret",
    "insecure_ssl": "0"
  }
}
EOF

# Listare i webhooks
gh api repos/{owner}/{repo}/hooks

# Testare un webhook (ping)
gh api repos/{owner}/{repo}/hooks/{hook_id}/pings -X POST

# Visualizzare le delivery recenti
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries
```

### Eventi Principali

| Evento | Descrizione |
|--------|-------------|
| `push` | Commit pushati a un branch |
| `pull_request` | PR aperta, chiusa, mergiata, sincronizzata |
| `issues` | Issue creata, modificata, chiusa |
| `issue_comment` | Commento su issue o PR |
| `create` | Branch o tag creato |
| `delete` | Branch o tag eliminato |
| `release` | Release pubblicata |
| `workflow_run` | Workflow completato |
| `deployment` | Deployment creato |
| `deployment_status` | Status del deployment aggiornato |
| `check_run` | Check run creato o completato |
| `star` | Repository starred/unstarred |
| `fork` | Repository forkato |

### Payload dei Webhook

```json
// Esempio di payload per evento push
{
  "ref": "refs/heads/main",
  "before": "abc1234...",
  "after": "def5678...",
  "repository": {
    "full_name": "org/repo",
    "html_url": "https://github.com/org/repo"
  },
  "pusher": {
    "name": "mariorossi",
    "email": "mario@example.com"
  },
  "commits": [
    {
      "id": "def5678...",
      "message": "feat: add login",
      "author": { "name": "Mario Rossi" },
      "added": ["src/login.js"],
      "modified": ["src/app.js"],
      "removed": []
    }
  ]
}
```

### Sicurezza: Verifica HMAC

Il secret del webhook viene usato per firmare il payload con HMAC-SHA256. Il server deve verificare la firma per assicurarsi che la richiesta provenga da GitHub.

```python
# Server webhook in Python (Flask)
import hmac
import hashlib
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = b'my-webhook-secret'

def verify_signature(payload_body, signature_header):
    """Verificare la firma HMAC-SHA256 del webhook."""
    if not signature_header:
        abort(403, "No signature header")

    hash_object = hmac.new(
        WEBHOOK_SECRET,
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        abort(403, "Invalid signature")

@app.route('/webhook', methods=['POST'])
def webhook():
    verify_signature(
        request.get_data(),
        request.headers.get('X-Hub-Signature-256')
    )

    event = request.headers.get('X-GitHub-Event')
    payload = request.json

    if event == 'push':
        branch = payload['ref'].replace('refs/heads/', '')
        print(f"Push to {branch} by {payload['pusher']['name']}")
        # Trigger deployment, notifica, etc.

    elif event == 'pull_request':
        action = payload['action']
        pr_number = payload['number']
        print(f"PR #{pr_number} {action}")

    return 'OK', 200
```

```javascript
// Server webhook in Node.js (Express)
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json({ verify: (req, res, buf) => { req.rawBody = buf; } }));

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

function verifySignature(req) {
    const signature = req.headers['x-hub-signature-256'];
    if (!signature) throw new Error('No signature');

    const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET);
    const digest = 'sha256=' + hmac.update(req.rawBody).digest('hex');

    if (!crypto.timingSafeEqual(Buffer.from(digest), Buffer.from(signature))) {
        throw new Error('Invalid signature');
    }
}

app.post('/webhook', (req, res) => {
    try {
        verifySignature(req);
    } catch (e) {
        return res.status(403).send(e.message);
    }

    const event = req.headers['x-github-event'];
    const payload = req.body;

    console.log(`Received ${event} event`);

    // Gestire l'evento...

    res.status(200).send('OK');
});

app.listen(3000);
```

### Payload Dettagliati per Evento

Ogni evento webhook ha una struttura payload specifica. Di seguito i payload piu comuni con i campi chiave.

```json
// === Payload: pull_request (evento opened) ===
{
  "action": "opened",
  "number": 42,
  "pull_request": {
    "id": 123456789,
    "node_id": "PR_kwDOxxxxxxxx",
    "html_url": "https://github.com/org/repo/pull/42",
    "title": "feat: add OAuth2 support",
    "state": "open",
    "user": {
      "login": "mariorossi",
      "id": 12345
    },
    "body": "## Summary\nImplement OAuth2 flow...",
    "created_at": "2026-05-24T10:30:00Z",
    "head": {
      "ref": "feature/oauth2",
      "sha": "abc1234def5678..."
    },
    "base": {
      "ref": "main",
      "sha": "def5678abc1234..."
    },
    "draft": false,
    "mergeable": true,
    "additions": 150,
    "deletions": 20,
    "changed_files": 8
  },
  "repository": {
    "full_name": "org/repo",
    "private": true
  },
  "sender": {
    "login": "mariorossi",
    "id": 12345
  }
}
```

```json
// === Payload: issues (evento labeled) ===
{
  "action": "labeled",
  "issue": {
    "number": 99,
    "title": "Bug: login timeout on mobile",
    "state": "open",
    "user": { "login": "developer1" },
    "labels": [
      { "name": "bug", "color": "d73a4a" },
      { "name": "priority:high", "color": "ff0000" }
    ],
    "assignees": [
      { "login": "developer2" }
    ],
    "milestone": {
      "title": "v2.0",
      "due_on": "2026-06-30T00:00:00Z"
    }
  },
  "label": {
    "name": "priority:high",
    "color": "ff0000"
  },
  "repository": { "full_name": "org/repo" },
  "sender": { "login": "teamlead" }
}
```

```json
// === Payload: check_run (evento completed) ===
{
  "action": "completed",
  "check_run": {
    "id": 987654321,
    "name": "CI / Tests",
    "head_sha": "abc1234...",
    "status": "completed",
    "conclusion": "failure",
    "started_at": "2026-05-24T10:30:00Z",
    "completed_at": "2026-05-24T10:35:42Z",
    "output": {
      "title": "3 test failures",
      "summary": "Tests failed in auth module",
      "annotations_count": 3
    },
    "app": {
      "slug": "github-actions",
      "name": "GitHub Actions"
    }
  },
  "repository": { "full_name": "org/repo" }
}
```

```json
// === Payload: deployment_status ===
{
  "action": "created",
  "deployment_status": {
    "state": "success",
    "description": "Deployment finished successfully.",
    "environment": "production",
    "target_url": "https://app.example.com",
    "created_at": "2026-05-24T11:00:00Z"
  },
  "deployment": {
    "ref": "main",
    "sha": "abc1234...",
    "task": "deploy",
    "environment": "production",
    "creator": { "login": "deploy-bot" }
  },
  "repository": { "full_name": "org/repo" }
}
```

### Webhook per Organizzazioni

I webhook a livello di organizzazione ricevono eventi da tutti i repository dell'organizzazione, piu eventi specifici dell'organizzazione stessa (aggiunta membri, creazione team, etc.). Sono essenziali per automazioni centralizzate e audit.

```bash
# Creare un webhook a livello di organizzazione
gh api orgs/{org}/hooks -X POST --input - << 'EOF'
{
  "name": "web",
  "active": true,
  "events": [
    "repository",
    "member",
    "team",
    "push",
    "pull_request",
    "issues",
    "create",
    "delete",
    "organization"
  ],
  "config": {
    "url": "https://myserver.com/org-webhook",
    "content_type": "json",
    "secret": "org-webhook-secret-rotated-2026-05",
    "insecure_ssl": "0"
  }
}
EOF

# Listare i webhook dell'organizzazione
gh api orgs/{org}/hooks

# Aggiornare un webhook dell'organizzazione
gh api orgs/{org}/hooks/{hook_id} -X PATCH \
  -f "active=true" \
  -f 'add_events[]=workflow_run'

# Eliminare un webhook dell'organizzazione
gh api orgs/{org}/hooks/{hook_id} -X DELETE
```

**Eventi esclusivi dei webhook organizzazione:**

| Evento | Descrizione |
|--------|-------------|
| `organization` | Membro aggiunto/rimosso dall'organizzazione |
| `team` | Team creato, eliminato o modificato |
| `team_add` | Repository aggiunto a un team |
| `membership` | Membro aggiunto/rimosso da un team |
| `repository` | Repository creato, eliminato, archiviato, trasferito |
| `org_block` | Utente bloccato/sbloccato dall'organizzazione |
| `installation` | GitHub App installata/disinstallata nell'organizzazione |
| `security_advisory` | Advisory di sicurezza pubblicato o aggiornato |
| `dependabot_alert` | Alert Dependabot creato, risolto o chiuso |
| `code_scanning_alert` | Alert di code scanning creato o risolto |
| `secret_scanning_alert` | Secret scanning ha rilevato un secret esposto |

### Delivery Log e Redelivery

GitHub mantiene un log di tutte le consegne webhook per 30 giorni. Questo e essenziale per il debugging e per riconsegnare payload persi.

```bash
# Listare le delivery recenti di un webhook
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries \
  --jq '.[] | "\(.id) | \(.status_code) | \(.event) | \(.delivered_at)"'

# Visualizzare i dettagli di una delivery specifica
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}

# Visualizzare il payload di una delivery
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id} \
  --jq '.request.payload'

# Visualizzare gli header della richiesta
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id} \
  --jq '.request.headers'

# Redeliver un webhook fallito
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}/attempts \
  -X POST

# Script: trovare e riconsegnare tutti i webhook falliti delle ultime 24 ore
HOOK_ID="12345"
REPO="org/repo"

gh api "repos/${REPO}/hooks/${HOOK_ID}/deliveries" --paginate \
  --jq '.[] | select(.status_code >= 400) | .id' \
  | while read -r delivery_id; do
      echo "Redelivering $delivery_id..."
      gh api "repos/${REPO}/hooks/${HOOK_ID}/deliveries/${delivery_id}/attempts" -X POST
      sleep 1  # Rispettare i rate limit
    done
```

### Replay Protection e Deduplicazione

I webhook possono essere consegnati piu volte in caso di errori di rete o timeout del server. E fondamentale implementare la deduplicazione basata sull'header `X-GitHub-Delivery` per garantire l'idempotenza del processing.

```python
# Implementazione completa con replay protection (Python)
import hmac
import hashlib
import time
import json
from functools import wraps
from flask import Flask, request, abort, jsonify

app = Flask(__name__)

WEBHOOK_SECRET = b'my-webhook-secret'
DELIVERY_CACHE = {}  # In produzione: Redis/Memcached con TTL
DELIVERY_TTL_SECONDS = 86400  # 24 ore
TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 minuti

def cleanup_expired_deliveries():
    """Rimuovere delivery ID scaduti dalla cache."""
    now = time.time()
    expired = [k for k, v in DELIVERY_CACHE.items() if now - v > DELIVERY_TTL_SECONDS]
    for k in expired:
        del DELIVERY_CACHE[k]

def verify_webhook(f):
    """Decorator per la verifica completa del webhook."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Verificare la firma HMAC-SHA256
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            abort(403, 'Missing signature header')

        expected = 'sha256=' + hmac.new(
            WEBHOOK_SECRET,
            msg=request.get_data(),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            abort(403, 'Invalid signature')

        # 2. Replay protection: deduplicazione via X-GitHub-Delivery
        delivery_id = request.headers.get('X-GitHub-Delivery')
        if not delivery_id:
            abort(400, 'Missing delivery ID')

        if delivery_id in DELIVERY_CACHE:
            # Gia processato: rispondere 200 senza rielaborare
            return jsonify({'status': 'already_processed', 'delivery_id': delivery_id}), 200

        # 3. Timestamp validation (protezione replay temporale)
        # GitHub non invia un timestamp dedicato nell'header, ma si puo
        # usare il timestamp del payload per eventi che lo includono
        payload = request.json
        if 'created_at' in payload.get('action', ''):
            event_time = payload.get('created_at', '')
            # Validare che l'evento non sia troppo vecchio

        # 4. Registrare il delivery ID come processato
        DELIVERY_CACHE[delivery_id] = time.time()

        # 5. Pulizia periodica
        cleanup_expired_deliveries()

        return f(*args, **kwargs)
    return decorated

@app.route('/webhook', methods=['POST'])
@verify_webhook
def handle_webhook():
    event = request.headers.get('X-GitHub-Event')
    delivery_id = request.headers.get('X-GitHub-Delivery')
    payload = request.json

    # Dispatch agli handler specifici
    handlers = {
        'push': handle_push,
        'pull_request': handle_pull_request,
        'issues': handle_issues,
        'check_run': handle_check_run,
        'deployment_status': handle_deployment_status,
    }

    handler = handlers.get(event)
    if handler:
        handler(payload, delivery_id)
    else:
        app.logger.info(f'Evento non gestito: {event} (delivery: {delivery_id})')

    return jsonify({'status': 'processed', 'delivery_id': delivery_id}), 200

def handle_push(payload, delivery_id):
    branch = payload['ref'].replace('refs/heads/', '')
    commits = payload.get('commits', [])
    app.logger.info(
        f'[{delivery_id}] Push to {branch}: {len(commits)} commits '
        f'by {payload["pusher"]["name"]}'
    )

def handle_pull_request(payload, delivery_id):
    action = payload['action']
    pr = payload['pull_request']
    app.logger.info(
        f'[{delivery_id}] PR #{pr["number"]} {action}: '
        f'{pr["title"]} by {pr["user"]["login"]}'
    )

def handle_issues(payload, delivery_id):
    action = payload['action']
    issue = payload['issue']
    app.logger.info(
        f'[{delivery_id}] Issue #{issue["number"]} {action}: {issue["title"]}'
    )

def handle_check_run(payload, delivery_id):
    check = payload['check_run']
    app.logger.info(
        f'[{delivery_id}] Check "{check["name"]}": {check["conclusion"]}'
    )

def handle_deployment_status(payload, delivery_id):
    status = payload['deployment_status']
    env = status['environment']
    state = status['state']
    app.logger.info(f'[{delivery_id}] Deploy to {env}: {state}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
```

### Rotazione del Webhook Secret

La rotazione periodica del webhook secret e una pratica di sicurezza fondamentale. Il periodo consigliato e ogni 90 giorni. La rotazione richiede una procedura in due fasi per evitare interruzioni.

```bash
# === Procedura di rotazione in 5 passi ===

# 1. Generare il nuovo secret
NEW_SECRET=$(openssl rand -hex 32)
echo "Nuovo secret generato: $NEW_SECRET"

# 2. Aggiornare il server webhook per accettare ENTRAMBI i secret
# (vecchio e nuovo) durante il periodo di transizione
# Nel codice del server:
```

```python
# Fase 2: Server che accetta entrambi i secret durante la rotazione
WEBHOOK_SECRETS = [
    b'nuovo-secret-2026-05',   # Nuovo (priorita)
    b'vecchio-secret-2026-02', # Vecchio (transizione)
]

def verify_signature_multi(payload_body, signature_header):
    """Verificare la firma contro multipli secret (per rotazione)."""
    if not signature_header:
        return False

    for secret in WEBHOOK_SECRETS:
        expected = 'sha256=' + hmac.new(
            secret,
            msg=payload_body,
            digestmod=hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(expected, signature_header):
            return True

    return False
```

```bash
# 3. Aggiornare il secret su GitHub
gh api repos/{owner}/{repo}/hooks/{hook_id} -X PATCH \
  --input - << EOF
{
  "config": {
    "secret": "$NEW_SECRET"
  }
}
EOF

# 4. Verificare che i webhook funzionino con il nuovo secret
gh api repos/{owner}/{repo}/hooks/{hook_id}/pings -X POST
# Controllare i log del server per confermare la verifica con il nuovo secret

# 5. Dopo 24-48 ore, rimuovere il vecchio secret dal server
# Aggiornare WEBHOOK_SECRETS per contenere solo il nuovo secret
```

**Limiti dei webhook:**

| Limite | Valore |
|--------|--------|
| Webhook per evento per repository | Max 20 |
| Dimensione payload | Max 25 MB |
| Timeout risposta | 10 secondi |
| Tentativi di redelivery | Fino a 3 (automatici) dopo fallimento |
| Retention delivery log | 30 giorni |
| Content types supportati | `application/json`, `application/x-www-form-urlencoded` |

### Strumenti di Proxy per lo Sviluppo Locale

Durante lo sviluppo di integrazioni webhook, il server locale non e raggiungibile da GitHub perche si trova dietro NAT o firewall. Per risolvere questo problema esistono strumenti di proxy che inoltrano i payload webhook dalla rete pubblica alla macchina locale.

#### smee.io

smee.io e un servizio gratuito mantenuto dal team Probot (GitHub) che utilizza Server-Sent Events (SSE) per fare proxy dei payload webhook. Funziona in due fasi: GitHub invia il payload al canale smee.io, e un client locale riceve il payload tramite SSE e lo inoltra all'endpoint locale.

```bash
# 1. Creare un canale su https://smee.io — cliccare "Start a new channel"
# Si ottiene un URL come: https://smee.io/abc123xyz

# 2. Installare il client smee
npm install -g smee-client

# 3. Avviare il proxy locale
smee --url https://smee.io/abc123xyz --target http://localhost:3000/webhook --port 3000

# Oppure con npx senza installazione globale
npx smee-client --url https://smee.io/abc123xyz --target http://localhost:3000/webhook

# 4. Configurare il webhook su GitHub con l'URL smee.io:
# - Webhook URL: https://smee.io/abc123xyz
# - Content type: application/json
# - Secret: il solito secret per HMAC verification
```

**Avvertenze di sicurezza critiche su smee.io:**

- I canali smee.io **non sono autenticati**: chiunque conosca il channel ID puo visualizzare i payload in transito tramite l'interfaccia web. Non utilizzare smee.io per repository con dati sensibili o in produzione.
- smee.io e progettato esclusivamente per sviluppo e testing. Non e un proxy di produzione e non offre garanzie di uptime, throughput o sicurezza.
- La sicurezza dei webhook rimane garantita dalla firma HMAC-SHA256: anche se un attaccante intercetta il payload su smee.io, non puo forgiare payload validi senza conoscere il webhook secret. Pertanto, la verifica `X-Hub-Signature-256` sul server locale resta obbligatoria anche in ambiente di sviluppo.
- Non trasmettere webhook che contengono secret, token, chiavi private o PII attraverso smee.io.

#### gosmee — Alternativa Self-Hosted

Per ambienti dove la sicurezza dei dati in transito e importante, `gosmee` offre un'alternativa open-source a smee.io che puo essere ospitata su infrastruttura propria. Scritto in Go, supporta sia la modalita client che server.

```bash
# Installazione via go
go install github.com/chmouel/gosmee@latest

# Installazione via Homebrew
brew install gosmee

# Utilizzare con un canale smee.io esistente
gosmee client https://smee.io/abc123xyz http://localhost:3000/webhook

# Oppure avviare un server gosmee self-hosted
gosmee server --port 8080

# E puntare il webhook GitHub a https://my-gosmee-server.internal:8080/channel-name
# Il client gosmee si connette al server self-hosted
gosmee client https://my-gosmee-server.internal:8080/channel-name http://localhost:3000/webhook
```

Il vantaggio di `gosmee` self-hosted e che i payload non transitano attraverso servizi esterni: il server puo risiedere sulla stessa rete del team di sviluppo, protetto da VPN o firewall, mantenendo la riservatezza dei dati webhook.

#### Workflow di Sviluppo Webhook Consigliato

Un workflow strutturato per lo sviluppo di integrazioni webhook prevede le seguenti fasi:

1. **Setup canale proxy**: Creare un canale smee.io (sviluppo individuale) o configurare gosmee self-hosted (team).
2. **Configurare il webhook su GitHub** con l'URL del proxy come payload URL.
3. **Avviare il server locale** con il handler webhook in modalita debug (logging verboso di header, payload, risultato verifica HMAC).
4. **Eseguire azioni su GitHub** che generano gli eventi sottoscritti (push, PR, issue) e osservare i payload nel terminale locale.
5. **Ispezionare i payload** nell'interfaccia web di smee.io per verificare la struttura prima di scrivere il codice di parsing.
6. **Iterare sul codice** del handler senza necessita di deploy: ogni modifica locale e immediatamente testabile.
7. **Migrare a produzione**: Sostituire l'URL del proxy con l'URL del server di produzione, verificare con un ping test e controllare le prime delivery nel log GitHub.

### Redelivery Automatica dei Webhook Falliti

GitHub non ripete automaticamente i webhook falliti in modo indefinito: dopo il fallimento iniziale, la consegna viene registrata come fallita nel delivery log (visibile per 30 giorni). Per gestire automaticamente la riconsegna dei webhook falliti, e possibile utilizzare un workflow GitHub Actions che monitora periodicamente lo stato delle delivery e riconsegna quelle fallite.

#### Pattern con GitHub Actions per Redelivery Automatica

Il seguente workflow esegue un controllo periodico delle delivery fallite e le riconsegna automaticamente. Questo pattern e documentato nella documentazione ufficiale GitHub ed e adattabile sia per webhook di repository che per webhook di GitHub App.

```yaml
# .github/workflows/webhook-redelivery.yml
name: Redelivery automatica webhook falliti
on:
  schedule:
    # Eseguire ogni 6 ore
    - cron: '0 */6 * * *'
  workflow_dispatch:
    inputs:
      hours_back:
        description: 'Ore nel passato da controllare'
        required: false
        default: '6'

permissions:
  contents: read

jobs:
  redeliver-failed-webhooks:
    name: Riconsegnare webhook falliti
    runs-on: ubuntu-latest
    steps:
      - name: Controllare e riconsegnare delivery fallite
        env:
          GH_TOKEN: ${{ secrets.WEBHOOK_REDELIVERY_TOKEN }}
          REPO: ${{ github.repository }}
          HOOK_ID: ${{ secrets.WEBHOOK_HOOK_ID }}
          HOURS_BACK: ${{ github.event.inputs.hours_back || '6' }}
        run: |
          set -euo pipefail

          # Calcolare il timestamp di cutoff
          cutoff=$(date -u -d "-${HOURS_BACK} hours" +%Y-%m-%dT%H:%M:%SZ)
          echo "Controllando delivery fallite dopo: $cutoff"

          # Recuperare le delivery recenti
          failed_count=0
          redelivered_count=0

          gh api "repos/${REPO}/hooks/${HOOK_ID}/deliveries" \
            --paginate --jq '.[]' | while IFS= read -r delivery; do

            status_code=$(echo "$delivery" | jq -r '.status_code')
            delivery_id=$(echo "$delivery" | jq -r '.id')
            delivered_at=$(echo "$delivery" | jq -r '.delivered_at')
            event=$(echo "$delivery" | jq -r '.event')

            # Verificare se la delivery e nel range temporale
            if [[ "$delivered_at" < "$cutoff" ]]; then
              continue
            fi

            # Verificare se la delivery e fallita (status >= 400 o non 2xx)
            if [[ "$status_code" -ge 400 ]] || [[ "$status_code" -lt 200 ]]; then
              echo "FALLITA: delivery $delivery_id (evento: $event, status: $status_code, data: $delivered_at)"
              failed_count=$((failed_count + 1))

              # Tentare la riconsegna
              if gh api "repos/${REPO}/hooks/${HOOK_ID}/deliveries/${delivery_id}/attempts" \
                -X POST --silent; then
                echo "  -> Riconsegnata con successo"
                redelivered_count=$((redelivered_count + 1))
              else
                echo "  -> ERRORE nella riconsegna"
              fi

              # Rispettare i rate limit tra le riconsegne
              sleep 2
            fi
          done

          echo ""
          echo "=== Riepilogo ==="
          echo "Delivery fallite trovate: $failed_count"
          echo "Delivery riconsegnate: $redelivered_count"
```

**Requisiti per il workflow:**

- Il token `WEBHOOK_REDELIVERY_TOKEN` deve essere un PAT (o GitHub App token) con permesso `admin:repo_hook` o `admin:org_hook` per i webhook organizzazione.
- Il secret `WEBHOOK_HOOK_ID` contiene l'ID numerico del webhook da monitorare, recuperabile con `gh api repos/{owner}/{repo}/hooks --jq '.[].id'`.
- La finestra temporale di controllo (default 6 ore) deve corrispondere alla frequenza dello schedule per evitare gap o sovrapposizioni eccessive.

#### Script Standalone per Redelivery con Deduplicazione

Per scenari dove il workflow Actions non e praticabile (ad esempio per webhook di organizzazioni gestiti centralmente), e possibile utilizzare uno script standalone che mantiene stato tra le esecuzioni.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Configurazione
REPO="org/repo"
HOOK_ID="12345"
STATE_FILE="/var/lib/webhook-redelivery/last-check.txt"
LOG_FILE="/var/log/webhook-redelivery.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }

# Leggere l'ultimo timestamp controllato
if [ -f "$STATE_FILE" ]; then
    last_check=$(cat "$STATE_FILE")
else
    last_check=$(date -u -d "-24 hours" +%Y-%m-%dT%H:%M:%SZ)
fi

log "Controllando delivery fallite dal: $last_check"

# Raccogliere delivery fallite
failed_deliveries=$(gh api "repos/${REPO}/hooks/${HOOK_ID}/deliveries" \
    --paginate \
    --jq ".[] | select(.status_code >= 400) | select(.delivered_at > \"${last_check}\") | .id")

redelivered=0
for delivery_id in $failed_deliveries; do
    log "Riconsegnando delivery $delivery_id..."
    if gh api "repos/${REPO}/hooks/${HOOK_ID}/deliveries/${delivery_id}/attempts" \
        -X POST --silent 2>>"$LOG_FILE"; then
        log "  OK"
        redelivered=$((redelivered + 1))
    else
        log "  FALLITO"
    fi
    sleep 1
done

# Aggiornare il timestamp dell'ultimo controllo
date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE_FILE"
log "Completato: $redelivered delivery riconsegnate"
```

Questo script puo essere schedulato via cron (`0 */4 * * *`) e mantiene il proprio stato in un file, evitando di riconsegnare delivery gia gestite in esecuzioni precedenti.

**Limiti della redelivery:**

| Limite | Valore |
|--------|--------|
| Finestra massima di redelivery | 3 giorni dalla delivery originale |
| Delivery log retention | 30 giorni |
| Rate limit per redelivery | Soggetto ai normali rate limit API |
| Payload identico all'originale | Si, il payload riconsegnato e identico |
| Nuovo `X-GitHub-Delivery` | Si, ogni redelivery genera un nuovo GUID |

---

## GitHub Apps vs OAuth Apps

### Confronto

| Aspetto | GitHub App | OAuth App |
|---------|-----------|-----------|
| Autenticazione | Installation token | User token |
| Rate limit | Per installazione | Per utente |
| Permessi | Granulari per risorsa | Scope broad |
| Installazione | Per repository/org | Per utente |
| Webhook | Integrato | Separato |
| Bot identity | App name [bot] | User name |
| Best for | Automazioni, CI/CD | Integrazioni utente |

### Creare una GitHub App

```bash
# Registrare una GitHub App
# Settings > Developer settings > GitHub Apps > New GitHub App

# Configurazione necessaria:
# - Nome dell'app
# - Homepage URL
# - Webhook URL
# - Webhook secret
# - Permessi (granulari per ogni tipo di risorsa)
# - Eventi sottoscritti

# Autenticazione come GitHub App:
# 1. Generare un JWT dal private key
# 2. Scambiare il JWT per un installation token
# 3. Usare l'installation token per le API calls
```

```python
# Generare JWT per GitHub App (Python)
import jwt
import time

PRIVATE_KEY = open('private-key.pem', 'r').read()
APP_ID = '12345'

payload = {
    'iat': int(time.time()) - 60,     # Issued at (1 min ago for clock skew)
    'exp': int(time.time()) + 600,     # Expires in 10 minutes
    'iss': APP_ID                       # Issuer (App ID)
}

token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')

# Ottenere installation token
import requests

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json'
}

# Listare le installazioni
resp = requests.get('https://api.github.com/app/installations', headers=headers)
installation_id = resp.json()[0]['id']

# Ottenere il token di installazione
resp = requests.post(
    f'https://api.github.com/app/installations/{installation_id}/access_tokens',
    headers=headers
)
installation_token = resp.json()['token']

# Usare il token per le API calls
headers['Authorization'] = f'Bearer {installation_token}'
resp = requests.get('https://api.github.com/repos/{owner}/{repo}/pulls', headers=headers)
```

### Fine-Grained Personal Access Tokens

A partire da marzo 2025, i fine-grained PAT sono generalmente disponibili (GA) e abilitati di default per tutte le organizzazioni su GitHub. Rispetto ai token classici (`ghp_`), i fine-grained PAT (`github_pat_`) offrono un modello di sicurezza significativamente superiore.

**Confronto tra tipi di token:**

| Caratteristica | Classic PAT (`ghp_`) | Fine-Grained PAT (`github_pat_`) | GitHub App Token (`ghs_`) | OAuth Token |
|---------------|----------------------|----------------------------------|---------------------------|-------------|
| Scope | Broad (repo, admin:org) | Per-repository, per-permesso | Per-installazione, per-permesso | Broad (scope) |
| Scadenza | Opzionale (mai scade) | Obbligatoria (max 1 anno) | 1 ora (auto-rinnovabile) | Mai (fino a revoca) |
| Granularita repo | Tutti i repo dell'utente | Repository specifici selezionabili | Repository dell'installazione | Tutti i repo dell'utente |
| Approvazione org | Non richiesta | Configurabile dall'admin org | Approvazione installazione | Non richiesta |
| Audit log | Limitato | Completo con dettaglio operazioni | Completo | Limitato |
| Prefisso token | `ghp_` | `github_pat_` | `ghs_` | `gho_` |
| Associato a | Utente | Utente (con restrizione org) | App/Installazione | Utente |

```bash
# === Creare un fine-grained PAT via web ===
# Settings > Developer settings > Personal access tokens > Fine-grained tokens

# Configurazione tipica per un token CI/CD:
# - Resource owner: organizzazione target
# - Repository access: "Only select repositories" → selezionare i repo specifici
# - Permissions:
#   - Contents: Read and write (push codice)
#   - Pull requests: Read and write (creare/aggiornare PR)
#   - Actions: Read (monitorare workflow)
#   - Metadata: Read (obbligatorio, sempre incluso)
# - Expiration: 90 giorni (rotazione trimestrale)

# === Verificare i permessi di un token ===
curl -H "Authorization: Bearer github_pat_xxxx..." \
  https://api.github.com/repos/{owner}/{repo} \
  -I 2>/dev/null | grep -i "x-oauth-scopes\|x-accepted-oauth-scopes"
# Fine-grained PAT non usano scope tradizionali:
# l'accesso e determinato dai permessi configurati

# === Limitazioni dei fine-grained PAT (2026) ===
# - Non possono accedere a repository di organizzazioni multiple con un singolo token
# - Non supportano l'accesso come collaboratore esterno a repository di altri
# - Non possono accedere a repository interni dell'enterprise al di fuori dell'organizzazione target
# - Alcuni endpoint enterprise non sono ancora compatibili
```

### Permessi Granulari delle GitHub App

Le GitHub App definiscono permessi a livello di tipo di risorsa, con tre livelli di accesso: nessuno, sola lettura, lettura e scrittura. Questo e molto piu granulare degli scope OAuth.

| Permesso | Risorse Controllate | Livelli |
|----------|---------------------|---------|
| `actions` | Workflow runs, artifacts, cache | Read / Read-Write |
| `contents` | File del repository, commit, branch, tag | Read / Read-Write |
| `issues` | Issue, label, milestone, assignee | Read / Read-Write |
| `pull_requests` | PR, review, commenti PR | Read / Read-Write |
| `checks` | Check runs, check suites | Read / Read-Write |
| `deployments` | Deployment, environment | Read / Read-Write |
| `metadata` | Repository metadata | Read (sempre incluso) |
| `administration` | Impostazioni repository, collaboratori, team | Read / Read-Write |
| `security_events` | Code scanning, secret scanning alert | Read / Read-Write |
| `members` | Membri dell'organizzazione | Read / Read-Write |
| `organization_administration` | Impostazioni organizzazione | Read / Read-Write |
| `webhooks` | Webhook del repository | Read / Read-Write |
| `secrets` | Actions secrets | Read / Read-Write |
| `workflows` | Workflow file (`.github/workflows`) | Read-Write |
| `packages` | GitHub Packages | Read / Read-Write |

### Manifest Flow per GitHub App

Il manifest flow permette di creare GitHub App programmaticamente da un template JSON, utile per strumenti che devono configurare app su molte organizzazioni.

```bash
# Creare una GitHub App tramite manifest flow

# 1. Preparare il manifest JSON
cat > app-manifest.json << 'EOF'
{
  "name": "My Automation Bot",
  "url": "https://myapp.example.com",
  "hook_attributes": {
    "url": "https://myapp.example.com/webhook"
  },
  "redirect_url": "https://myapp.example.com/callback",
  "callback_urls": ["https://myapp.example.com/callback"],
  "public": false,
  "default_permissions": {
    "issues": "write",
    "pull_requests": "write",
    "contents": "read",
    "checks": "write",
    "metadata": "read"
  },
  "default_events": [
    "issues",
    "pull_request",
    "check_run",
    "push"
  ]
}
EOF

# 2. L'utente visita:
# https://github.com/settings/apps/new?manifest=<url-encoded-json>
# oppure per organizzazioni:
# https://github.com/organizations/{org}/settings/apps/new?manifest=<url-encoded-json>

# 3. Dopo l'approvazione, GitHub reindirizza al callback con un codice temporaneo
# 4. Scambiare il codice per le credenziali dell'app (entro 1 ora)
curl -X POST "https://api.github.com/app-manifests/{code}/conversions"
# Risposta contiene: id, pem (private key), webhook_secret, client_id, client_secret
```

### Quando Scegliere Cosa

| Scenario | Soluzione Consigliata | Motivazione |
|----------|----------------------|-------------|
| Script personale di automazione | Fine-grained PAT | Semplice, scoped per repository, scadenza obbligatoria |
| CI/CD pipeline | GitHub App o `GITHUB_TOKEN` | Token a vita breve, permessi granulari |
| Bot che agisce sui repository | GitHub App | Identity separata dall'utente, bot label `[bot]` |
| Login "Accedi con GitHub" | OAuth App | Standard OAuth 2.0, accesso identita utente |
| Integrazione multi-tenant | GitHub App | Installation per org, rate limit scalabile |
| Accesso risorse enterprise | OAuth App | Le GitHub App non hanno ancora permessi enterprise completi |
| Automazione interna team | Fine-grained PAT | Configurazione rapida, revoca facile |
| Marketplace app pubblica | GitHub App | Listing nel marketplace, installazione standardizzata |

### Audit Log API per Compliance e Sicurezza Enterprise

L'Audit Log API di GitHub fornisce accesso programmatico ai log di audit delle organizzazioni e delle enterprise, registrando le azioni eseguite dagli utenti, dagli amministratori e dalle integrazioni. Questi log sono fondamentali per la compliance normativa (SOC 2, ISO 27001, GDPR), la risposta agli incidenti di sicurezza e il monitoraggio continuo delle attivita sulla piattaforma.

#### Accesso ai Log di Audit via REST API

```bash
# Ottenere gli eventi di audit dell'organizzazione (ultimi 90 giorni)
gh api orgs/{org}/audit-log \
  --paginate \
  --jq '.[] | "\(.@timestamp) | \(.action) | \(.actor) | \(.repo)"'

# Filtrare per azione specifica
# Esempio: tutti gli eventi di aggiunta/rimozione membri
gh api "orgs/{org}/audit-log?phrase=action:org.add_member" \
  --jq '.[] | "\(.@timestamp) \(.actor) ha aggiunto \(.user) all organizzazione"'

# Filtrare per attore (chi ha eseguito l'azione)
gh api "orgs/{org}/audit-log?phrase=actor:admin-user" \
  --paginate \
  --jq '.[] | "\(.@timestamp) | \(.action) | \(.repo)"'

# Filtrare per intervallo temporale
gh api "orgs/{org}/audit-log?phrase=created:>2026-05-01" \
  --paginate \
  --jq '.[] | "\(.@timestamp) | \(.action) | \(.actor)"'

# Filtrare per tipo di azione con query complessa
# Esempio: tutte le modifiche alle branch protection rules
gh api "orgs/{org}/audit-log?phrase=action:protected_branch" \
  --paginate \
  --jq '.[] | {timestamp: .["@timestamp"], action: .action, repo: .repo, actor: .actor}'

# Ottenere eventi di sicurezza specifici
# Secret scanning, code scanning, dependabot
gh api "orgs/{org}/audit-log?phrase=action:secret_scanning_alert" \
  --paginate \
  --jq '.[] | "\(.@timestamp) | \(.action) | \(.repo) | \(.actor)"'
```

#### Accesso ai Log di Audit via GraphQL API

La GraphQL API offre accesso ai log di audit delle organizzazioni con la flessibilita tipica di GraphQL per selezionare solo i campi necessari.

```graphql
# Query per gli eventi di audit dell'organizzazione
query($org: String!, $cursor: String) {
  organization(login: $org) {
    auditLog(first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      edges {
        node {
          ... on AuditEntry {
            action
            actorLogin
            createdAt
            operationType
          }
          ... on RepositoryAuditEntryData {
            repositoryName
          }
          ... on OrgAddMemberAuditEntry {
            action
            actorLogin
            userLogin
            permission
            createdAt
          }
          ... on RepoAccessAuditEntry {
            action
            actorLogin
            repositoryName
            visibility
          }
          ... on TeamAddMemberAuditEntry {
            action
            actorLogin
            teamName
            userLogin
          }
        }
      }
    }
  }
}
```

```bash
# Esecuzione dalla CLI con paginazione
gh api graphql -f query='
  query($org: String!) {
    organization(login: $org) {
      auditLog(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
        nodes {
          ... on AuditEntry {
            action
            actorLogin
            createdAt
          }
        }
      }
    }
  }
' -f org="my-org" --jq '.data.organization.auditLog.nodes[] | "\(.createdAt) | \(.action) | \(.actorLogin)"'
```

#### Retention e Limiti dei Log di Audit

| Aspetto | Valore |
|---------|--------|
| Retention eventi standard | 180 giorni |
| Retention eventi Git | 7 giorni |
| API rate limit | Standard (5000 req/ora autenticato) |
| Paginazione | Max 100 risultati per pagina |
| Filtri disponibili | action, actor, repo, created, country, ip |
| Formati export | JSON (API), CSV (interfaccia web) |

**Nota importante:** I log di audit sono disponibili solo per organizzazioni con piano Team o Enterprise. I piani Free e Pro non hanno accesso all'audit log API.

#### Audit Log Streaming per SIEM

Per le organizzazioni Enterprise Cloud, GitHub offre la funzionalita di audit log streaming che trasmette gli eventi in tempo reale verso sistemi SIEM (Security Information and Event Management) esterni. Questo elimina la necessita di polling periodico e garantisce che nessun evento venga perso per superamento della finestra di retention di 180 giorni.

**Endpoint di streaming supportati:**

| Destinazione | Formato | Note |
|-------------|---------|------|
| Amazon S3 | JSON-lines | Integrazione nativa con Athena, CloudWatch |
| Azure Blob Storage | JSON-lines | Integrazione con Azure Sentinel |
| Azure Event Hubs | JSON | Streaming real-time verso Azure Monitor |
| Datadog | Nativo Datadog | Dashboard e alerting predefiniti per GitHub |
| Google Cloud Storage | JSON-lines | Integrazione con BigQuery, Chronicle |
| Splunk HTTP Event Collector | JSON | Integrazione diretta con Splunk Enterprise/Cloud |

```bash
# Verificare la configurazione dello streaming (richiede admin enterprise)
gh api \
  -H "Accept: application/vnd.github+json" \
  /enterprises/{enterprise}/audit-log/streams

# L'output mostra gli stream configurati con il loro stato (enabled/disabled)
```

#### Casi d'Uso per la Compliance

**Monitoraggio accessi e permessi:**

```bash
# Chi ha avuto accesso al repository X negli ultimi 30 giorni?
gh api "orgs/{org}/audit-log?phrase=repo:{org}/{repo}+created:>2026-04-24" \
  --paginate \
  --jq '.[] | select(.action | startswith("repo.")) | "\(.@timestamp) \(.actor): \(.action)"'

# Monitorare le modifiche ai team e ai permessi
gh api "orgs/{org}/audit-log?phrase=action:team+created:>2026-05-01" \
  --paginate \
  --jq '.[] | "\(.@timestamp) | \(.action) | \(.actor) | Team: \(.team)"'

# Tracciare le installazioni/disinstallazioni di GitHub Apps
gh api "orgs/{org}/audit-log?phrase=action:integration_installation" \
  --paginate \
  --jq '.[] | "\(.@timestamp) | \(.action) | App: \(.name) | Attore: \(.actor)"'
```

**Script di export periodico per archivio compliance:**

```bash
#!/usr/bin/env bash
set -euo pipefail

ORG="my-org"
EXPORT_DIR="/var/lib/audit-exports"
TODAY=$(date -u +%Y-%m-%d)
EXPORT_FILE="${EXPORT_DIR}/audit-log-${ORG}-${TODAY}.jsonl"

mkdir -p "$EXPORT_DIR"

echo "Esportando audit log per $ORG (data: $TODAY)..."

gh api "orgs/${ORG}/audit-log?phrase=created:${TODAY}" \
  --paginate \
  --jq '.[]' > "$EXPORT_FILE"

event_count=$(wc -l < "$EXPORT_FILE")
echo "Esportati $event_count eventi in $EXPORT_FILE"

# Comprimere i file piu vecchi di 7 giorni
find "$EXPORT_DIR" -name "*.jsonl" -mtime +7 -exec gzip {} \;

# Verificare integrita con checksum
sha256sum "$EXPORT_FILE" > "${EXPORT_FILE}.sha256"
echo "Checksum salvato in ${EXPORT_FILE}.sha256"
```

L'archiviazione regolare dei log di audit su storage esterno e una best practice critica: la finestra di retention di 180 giorni di GitHub potrebbe non essere sufficiente per i requisiti normativi di molte organizzazioni, che spesso richiedono la conservazione dei log per periodi da 1 a 7 anni.

---

## Octokit SDK

### Octokit.js

```javascript
// Installazione
// npm install @octokit/rest @octokit/auth-app

const { Octokit } = require('@octokit/rest');

// Autenticazione con PAT
const octokit = new Octokit({
    auth: process.env.GITHUB_TOKEN
});

// Listare le PR
async function listPRs() {
    const { data } = await octokit.pulls.list({
        owner: 'org',
        repo: 'repo',
        state: 'open',
        per_page: 100
    });
    return data;
}

// Creare un'issue
async function createIssue(title, body) {
    const { data } = await octokit.issues.create({
        owner: 'org',
        repo: 'repo',
        title,
        body,
        labels: ['bug']
    });
    return data;
}

// Paginazione automatica
const { data: allIssues } = await octokit.paginate(
    octokit.issues.listForRepo,
    { owner: 'org', repo: 'repo', state: 'all', per_page: 100 }
);
```

### Octokit.js Avanzato: Autenticazione GitHub App

```javascript
// npm install @octokit/rest @octokit/auth-app

const { Octokit } = require('@octokit/rest');
const { createAppAuth } = require('@octokit/auth-app');
const fs = require('fs');

// Autenticazione come GitHub App
const octokit = new Octokit({
    authStrategy: createAppAuth,
    auth: {
        appId: process.env.APP_ID,
        privateKey: fs.readFileSync('private-key.pem', 'utf-8'),
        installationId: process.env.INSTALLATION_ID,
    },
});

// Il token viene rinnovato automaticamente quando scade
async function listPullRequests() {
    const { data } = await octokit.pulls.list({
        owner: 'org',
        repo: 'repo',
        state: 'open',
        per_page: 100,
    });
    return data;
}
```

### Octokit.js: Plugin Throttling e Retry

I plugin ufficiali gestiscono automaticamente rate limit, secondary rate limit e retry su errori transitori. Sono fortemente consigliati per qualsiasi applicazione di produzione.

```javascript
// npm install @octokit/rest @octokit/plugin-throttling @octokit/plugin-retry

const { Octokit } = require('@octokit/rest');
const { throttling } = require('@octokit/plugin-throttling');
const { retry } = require('@octokit/plugin-retry');

const MyOctokit = Octokit.plugin(throttling, retry);

const octokit = new MyOctokit({
    auth: process.env.GITHUB_TOKEN,
    userAgent: 'my-automation-bot/1.0',
    throttle: {
        onRateLimit: (retryAfter, options, octokit, retryCount) => {
            octokit.log.warn(
                `Rate limit raggiunto per ${options.method} ${options.url}`
            );
            // Riprovare automaticamente fino a 2 volte
            if (retryCount < 2) {
                octokit.log.info(`Retry dopo ${retryAfter} secondi`);
                return true;
            }
            return false;
        },
        onSecondaryRateLimit: (retryAfter, options, octokit) => {
            octokit.log.warn(
                `Secondary rate limit per ${options.method} ${options.url}`
            );
            // Sempre riprovare per secondary rate limit
            return true;
        },
    },
    retry: {
        doNotRetry: ['429'],  // Gestito dal throttle plugin
    },
});

// Paginazione automatica con iterator
async function getAllIssues(owner, repo) {
    const issues = [];
    for await (const response of octokit.paginate.iterator(
        octokit.issues.listForRepo,
        { owner, repo, state: 'all', per_page: 100 }
    )) {
        issues.push(...response.data);
    }
    return issues;
}

// GraphQL via Octokit
async function getRepoStats(owner, repo) {
    const result = await octokit.graphql(`
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                stargazerCount
                forkCount
                issues(states: OPEN) { totalCount }
                pullRequests(states: OPEN) { totalCount }
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 1) {
                                nodes {
                                    committedDate
                                    message
                                    author { name }
                                }
                            }
                        }
                    }
                }
            }
        }
    `, { owner, repo });
    return result.repository;
}
```

### Octokit Webhooks: Gestione Eventi con Type Safety

```javascript
// npm install @octokit/webhooks

const { Webhooks, createNodeMiddleware } = require('@octokit/webhooks');
const http = require('http');

const webhooks = new Webhooks({
    secret: process.env.WEBHOOK_SECRET,
});

// Handler tipizzati per ogni evento
webhooks.on('push', async ({ id, name, payload }) => {
    const branch = payload.ref.replace('refs/heads/', '');
    console.log(`[${id}] Push to ${branch}: ${payload.commits.length} commits`);
});

webhooks.on('pull_request.opened', async ({ id, payload }) => {
    console.log(`[${id}] PR #${payload.pull_request.number} opened: ${payload.pull_request.title}`);
});

webhooks.on('pull_request.closed', async ({ id, payload }) => {
    if (payload.pull_request.merged) {
        console.log(`[${id}] PR #${payload.pull_request.number} merged`);
    }
});

webhooks.on('issues.opened', async ({ id, payload }) => {
    console.log(`[${id}] Issue #${payload.issue.number}: ${payload.issue.title}`);
});

// Gestione errori globale
webhooks.onError((error) => {
    console.error('Webhook error:', error.message);
});

// Avviare il server con middleware integrato
const middleware = createNodeMiddleware(webhooks, { path: '/webhook' });
http.createServer(middleware).listen(3000, () => {
    console.log('Webhook server listening on port 3000');
});
```

### Octokit per Python

```python
# pip install PyGithub

from github import Github

g = Github(os.environ['GITHUB_TOKEN'])

# Ottenere un repository
repo = g.get_repo("org/repo")

# Listare le PR aperte
pulls = repo.get_pulls(state='open', sort='created', direction='desc')
for pr in pulls:
    print(f"#{pr.number}: {pr.title}")

# Creare un'issue
issue = repo.create_issue(
    title="Bug: login fails",
    body="Description",
    labels=["bug"],
    assignees=["mariorossi"]
)

# Creare un commento su un'issue
issue.create_comment("Working on this!")

# Merge di una PR
pr = repo.get_pull(42)
pr.merge(merge_method='squash')
```

### GitHubKit per Python (SDK Moderno)

GitHubKit e un SDK Python moderno ispirato a Octokit, con tipizzazione completa, supporto async, e generazione automatica dei tipi dall'OpenAPI spec di GitHub. E attivamente sviluppato con la versione 0.15.5 rilasciata nel maggio 2026.

```python
# pip install githubkit

import asyncio
from githubkit import GitHub, TokenAuthStrategy

# Autenticazione con token
gh = GitHub(TokenAuthStrategy(os.environ['GITHUB_TOKEN']))

# Operazioni sincrone
repo = gh.rest.repos.get(owner="org", repo="repo")
print(f"Stars: {repo.parsed_data.stargazers_count}")

# Operazioni asincrone
async def list_open_prs():
    async with GitHub(TokenAuthStrategy(os.environ['GITHUB_TOKEN'])) as gh:
        pulls = await gh.rest.pulls.async_list(
            owner="org",
            repo="repo",
            state="open",
            per_page=100
        )
        for pr in pulls.parsed_data:
            print(f"#{pr.number}: {pr.title} by {pr.user.login}")

asyncio.run(list_open_prs())

# GraphQL con GitHubKit
async def graphql_query():
    async with GitHub(TokenAuthStrategy(os.environ['GITHUB_TOKEN'])) as gh:
        result = await gh.async_graphql("""
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    stargazerCount
                    forkCount
                    issues(states: OPEN) { totalCount }
                }
            }
        """, variables={"owner": "org", "name": "repo"})
        print(result)

asyncio.run(graphql_query())
```

### SDK per Go: go-github

```go
// go get github.com/google/go-github/v62

package main

import (
    "context"
    "fmt"
    "os"

    "github.com/google/go-github/v62/github"
    "golang.org/x/oauth2"
)

func main() {
    ctx := context.Background()

    // Autenticazione con token
    ts := oauth2.StaticTokenSource(
        &oauth2.Token{AccessToken: os.Getenv("GITHUB_TOKEN")},
    )
    tc := oauth2.NewClient(ctx, ts)
    client := github.NewClient(tc)

    // Listare le PR aperte
    pulls, _, err := client.PullRequests.List(ctx, "org", "repo",
        &github.PullRequestListOptions{
            State:       "open",
            Sort:        "created",
            Direction:   "desc",
            ListOptions: github.ListOptions{PerPage: 100},
        })
    if err != nil {
        fmt.Printf("Errore: %v\n", err)
        return
    }

    for _, pr := range pulls {
        fmt.Printf("#%d: %s by %s\n",
            pr.GetNumber(), pr.GetTitle(), pr.GetUser().GetLogin())
    }

    // Creare un'issue
    issue := &github.IssueRequest{
        Title:  github.Ptr("Bug: login fails"),
        Body:   github.Ptr("Description of the bug"),
        Labels: &[]string{"bug"},
    }
    newIssue, _, err := client.Issues.Create(ctx, "org", "repo", issue)
    if err != nil {
        fmt.Printf("Errore creazione issue: %v\n", err)
        return
    }
    fmt.Printf("Issue creata: #%d\n", newIssue.GetNumber())
}
```

---

## Best Practices

### API Usage: Strategie per Applicazioni Robuste

**Caching con Conditional Requests:** Ogni applicazione che interroga l'API GitHub con frequenza superiore a qualche decina di richieste all'ora dovrebbe implementare il caching condizionale tramite ETag. Salvare l'header `ETag` della risposta e includerlo come `If-None-Match` nelle richieste successive permette di ricevere `304 Not Modified` quando i dati non sono cambiati, senza consumare punti del rate limit primario. Per applicazioni che monitorano continuamente lo stato di repository (CI/CD dashboard, bot di notifica), questo puo ridurre il consumo effettivo di rate limit del 70-90%.

```bash
# Pattern pratico: polling con ETag caching
ETAG=""
while true; do
    RESPONSE=$(curl -s -D /dev/stderr \
        -H "Authorization: Bearer $TOKEN" \
        ${ETAG:+-H "If-None-Match: $ETAG"} \
        "https://api.github.com/repos/org/repo/pulls?state=open" 2>&1)

    HTTP_CODE=$(echo "$RESPONSE" | head -1 | grep -oP '\d{3}')
    if [ "$HTTP_CODE" = "304" ]; then
        echo "Nessun cambiamento (304). Rate limit non consumato."
    else
        ETAG=$(echo "$RESPONSE" | grep -i "^etag:" | awk '{print $2}' | tr -d '\r')
        echo "Dati aggiornati. Nuovo ETag: $ETAG"
        # Processare i dati...
    fi
    sleep 60
done
```

**Paginazione completa:** Non assumere mai che la prima pagina contenga tutti i risultati. Un repository con 500 issue aperte restituisce solo le prime 30 nella risposta default. Per la REST API, iterare usando l'header `Link` con `rel="next"` oppure il flag `--paginate` di `gh`. Per GraphQL, usare i cursori `after`/`endCursor` con `hasNextPage`. Un errore comune e richiedere `per_page=100` pensando di ottenere tutto, quando la collezione potrebbe avere migliaia di elementi.

**User-Agent header personalizzato:** GitHub richiede che tutte le richieste API includano un header `User-Agent` valido. Le richieste senza User-Agent vengono rifiutate con `403 Forbidden`. Impostare un User-Agent descrittivo che identifichi l'applicazione (es. `my-ci-bot/1.2.0`) facilita anche il debugging lato GitHub in caso di problemi con il proprio account API.

```bash
# Includere sempre User-Agent nelle richieste curl
curl -H "Authorization: Bearer $TOKEN" \
  -H "User-Agent: my-automation-app/2.0 (contact: team@example.com)" \
  https://api.github.com/repos/org/repo
```

**Monitoraggio proattivo del rate limit:** Invece di attendere di colpire il limite per poi gestire l'errore, monitorare proattivamente gli header `X-RateLimit-Remaining` e `X-RateLimit-Reset` ad ogni risposta. Implementare una soglia di allarme (es. quando remaining scende sotto il 20% del limit) e rallentare le richieste prima di raggiungere il limite. Questo approccio e molto piu affidabile del semplice retry dopo il `429 Too Many Requests`.

```bash
# Funzione che controlla il rate limit prima di ogni chiamata
check_rate_limit() {
    local remaining=$1
    local reset=$2
    local threshold=500  # Soglia di allarme

    if [ "$remaining" -lt "$threshold" ]; then
        local now=$(date +%s)
        local wait=$(( reset - now + 5 ))  # +5s di margine
        if [ "$wait" -gt 0 ]; then
            echo "Rate limit basso ($remaining rimanenti). Pausa di ${wait}s." >&2
            sleep "$wait"
        fi
    fi
}
```

**GraphQL per query complesse:** Preferire GraphQL quando si devono raccogliere dati da risorse correlate. Una singola query GraphQL che recupera PR con le relative review, file modificati e stato dei check equivale a 3-5 chiamate REST separate. Tuttavia, attenzione al costo in punti: una query GraphQL che richiede `first: 100` su connessioni nested puo consumare centinaia o migliaia di punti. Utilizzare il campo `rateLimit` nella query per monitorare il consumo e ottimizzare i valori `first`/`last`.

### Webhooks: Robustezza e Resilienza in Produzione

**Verifica HMAC obbligatoria e constant-time:** Non processare mai un webhook senza aver verificato la firma `X-Hub-Signature-256`. Utilizzare sempre funzioni di confronto constant-time (`hmac.compare_digest` in Python, `crypto.timingSafeEqual` in Node.js) per prevenire timing attack. Un confronto byte-per-byte standard (`==`) puo rivelare informazioni sulla firma corretta attraverso la misurazione del tempo di esecuzione.

**Risposta rapida e processing asincrono:** GitHub considera fallita una delivery che non riceve risposta entro 10 secondi. Il pattern corretto e: ricevere il webhook, verificare la firma HMAC, rispondere immediatamente con `200 OK`, e poi processare il payload in modo asincrono tramite una coda di lavoro (Redis Queue, RabbitMQ, AWS SQS, o anche una semplice tabella database con un worker separato).

```python
# Pattern asincrono con coda in-process (Python)
import threading
import queue

webhook_queue = queue.Queue(maxsize=1000)

def webhook_worker():
    """Worker che processa i webhook dalla coda."""
    while True:
        event, payload, delivery_id = webhook_queue.get()
        try:
            process_event(event, payload, delivery_id)
        except Exception as e:
            logger.error(f"Errore processing {delivery_id}: {e}")
        finally:
            webhook_queue.task_done()

# Avviare 3 worker thread
for _ in range(3):
    t = threading.Thread(target=webhook_worker, daemon=True)
    t.start()

@app.route('/webhook', methods=['POST'])
@verify_hmac
def handle_webhook():
    event = request.headers.get('X-GitHub-Event')
    delivery_id = request.headers.get('X-GitHub-Delivery')

    # Accodare e rispondere immediatamente
    webhook_queue.put((event, request.json, delivery_id))
    return 'Accepted', 202
```

**Idempotenza e deduplicazione:** I webhook possono essere consegnati piu di una volta per vari motivi: redelivery manuale, errori di rete, o failover di GitHub. Ogni delivery ha un GUID unico nell'header `X-GitHub-Delivery`. Mantenere un registro delle delivery processate (Redis SET con TTL di 48 ore, o tabella database) e verificare ogni delivery in arrivo contro questo registro prima del processing. Se il delivery ID e gia presente, rispondere `200 OK` senza rielaborare.

**Logging strutturato:** Ogni webhook ricevuto deve essere loggato con: timestamp UTC ISO 8601, tipo evento (`X-GitHub-Event`), delivery ID (`X-GitHub-Delivery`), risultato della verifica HMAC, e outcome del processing. In produzione, utilizzare logging JSON strutturato per facilitare l'analisi con strumenti come Datadog, ELK Stack o CloudWatch.

### GitHub Apps: Sicurezza e Gestione del Ciclo di Vita

**Principio del minimo privilegio rigoroso:** Richiedere esclusivamente i permessi necessari per la funzionalita dell'app. Un bot che aggiunge label alle PR necessita solo di `pull_requests: write` e `metadata: read`, non di `contents: write` o `administration: write`. Ogni permesso aggiuntivo non necessario amplia la superficie di attacco in caso di compromissione della chiave privata dell'app.

**Rotazione delle chiavi private:** Le chiavi private delle GitHub App non scadono, ma devono essere ruotate periodicamente (ogni 6-12 mesi) e immediatamente in caso di sospetta compromissione. GitHub permette di avere piu chiavi private attive contemporaneamente per la stessa app, facilitando la rotazione senza downtime: generare la nuova chiave, aggiornare il server per usarla, verificare il funzionamento, poi revocare la vecchia chiave.

**Installation token lifecycle:** I token di installazione hanno una durata massima di 1 ora e possono essere configurati con un sottoinsieme dei permessi dell'app e un sottoinsieme dei repository dell'installazione. Per applicazioni con requisiti di sicurezza elevati, richiedere token con permessi ridotti rispetto a quelli disponibili sull'app, limitando il blast radius in caso di token leak.

```python
# Richiedere un installation token con permessi ridotti
import requests

headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Accept': 'application/vnd.github+json'
}

# Token con solo permessi di lettura su un subset di repository
resp = requests.post(
    f'https://api.github.com/app/installations/{installation_id}/access_tokens',
    headers=headers,
    json={
        'repositories': ['repo-a', 'repo-b'],  # Solo questi repository
        'permissions': {
            'contents': 'read',       # Solo lettura
            'pull_requests': 'read'   # Solo lettura
        }
    }
)
scoped_token = resp.json()['token']
# Questo token puo leggere contenuti e PR solo di repo-a e repo-b
# Anche se l'app ha permessi write su tutti i repository dell'installazione
```

### Sicurezza dei Secret e Igiene delle Credenziali

Mantenere una buona igiene nella gestione dei secret e dei token e fondamentale per la sicurezza delle integrazioni GitHub. Le seguenti pratiche dovrebbero essere adottate sistematicamente.

**Checklist di sicurezza per i secret:**

- Non committare mai token, chiavi private o webhook secret nel codice sorgente, nemmeno in repository privati.
- Utilizzare sempre variabili di ambiente o secret manager (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) per la configurazione dei secret.
- Impostare scadenze su tutti i token: fine-grained PAT supportano scadenza obbligatoria fino a 1 anno.
- Monitorare attivamente gli alert di secret scanning di GitHub: se un token viene esposto, ruotarlo immediatamente.
- Utilizzare `GITHUB_TOKEN` automatico nei workflow Actions quando possibile, invece di PAT manuali: il `GITHUB_TOKEN` ha scope limitato al repository corrente e scade automaticamente al termine del workflow.
- Per le GitHub App, proteggere la chiave privata PEM con permessi file restrittivi (`chmod 600`) e non includerla nei container image.

**Monitoraggio e alerting:** Configurare alerting su: consumo anomalo di rate limit (potrebbe indicare credential stuffing), tentativi di autenticazione falliti nei log di audit, e webhook delivery failure rate superiore alla soglia attesa. Integrare questi alert con il sistema di incident response del team.

---

## Troubleshooting

### Rate Limit Raggiunto

```bash
# Verificare lo stato
curl -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/rate_limit

# Attendere il reset
# Controllare X-RateLimit-Reset header per il timestamp del reset

# Usare conditional requests per ridurre il consumo
curl -H "Authorization: Bearer $TOKEN" \
  -H "If-None-Match: \"etag-value\"" \
  https://api.github.com/repos/{owner}/{repo}
# 304 Not Modified = nessun consumo di rate limit
```

### Webhook Non Ricevuto

```bash
# Verificare le delivery recenti
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries

# Verificare che l'URL sia raggiungibile
curl -X POST https://myserver.com/webhook

# Verificare il secret
# Rigenerare il secret se necessario
```

### GraphQL: Query Timeout

```bash
# Le query GraphQL hanno un timeout di 10 secondi
# Ridurre la complessità della query
# Usare la paginazione (first: 10) invece di richiedere tutti i risultati
# Evitare query nested profonde
```

---

## Esercizi

### Esercizio 1 — Automazione con gh CLI

**Obiettivo:** Costruire uno script Bash che automatizza operazioni comuni con `gh`.

1. Scrivere uno script che crea un repository, configura branch protection su `main`, aggiunge label e crea una milestone
2. Lo script deve accettare parametri: nome repo, visibilita (public/private), descrizione
3. Aggiungere una funzione che clona il repository, crea un branch `develop`, pusha e apre una PR draft
4. Implementare error handling per ogni chiamata `gh` con messaggi di errore chiari
5. Testare lo script su almeno 2 repository con configurazioni diverse e verificare il risultato

### Esercizio 2 — GraphQL API per Report

**Obiettivo:** Utilizzare la GraphQL API per generare un report sulle PR di un repository.

1. Scrivere una query GraphQL che recupera le ultime 50 PR merged di un repository con: titolo, autore, data merge, numero di commenti, file modificati, review status
2. Implementare la paginazione con cursori per recuperare piu di 100 risultati
3. Calcolare statistiche: tempo medio di merge (dalla creazione al merge), media commenti per PR, top 5 contributor per numero di PR
4. Generare l'output in formato JSON e CSV
5. Confrontare il numero di chiamate API necessarie con REST vs GraphQL per gli stessi dati

### Esercizio 3 — Webhook Server con Verifica HMAC

**Obiettivo:** Creare un server webhook sicuro che processa eventi GitHub.

1. Scrivere un server HTTP (Node.js o Python) che ascolta su `/webhook` e verifica la firma HMAC-SHA256
2. Implementare la verifica constant-time del header `X-Hub-Signature-256` contro il webhook secret
3. Processare eventi `push`, `pull_request` e `issues` con handler separati
4. Implementare replay protection basata su `X-GitHub-Delivery` (GUID dedup con TTL 24h)
5. Loggare ogni evento ricevuto con timestamp UTC, tipo evento, delivery ID, e risultato della verifica

### Esercizio 4 — GitHub App Minimal

**Obiettivo:** Creare una GitHub App che automatizza il labeling delle PR.

1. Registrare una GitHub App con permessi: pull_request (read/write), issues (read/write)
2. Generare una chiave privata e implementare l'autenticazione JWT → installation token
3. L'app deve assegnare automaticamente label basate sui file modificati: `frontend` per `*.tsx/*.css`, `backend` per `*.py/*.go`, `infra` per `*.yml/*.tf`
4. Implementare il webhook handler che riceve `pull_request.opened` e `pull_request.synchronize`
5. Testare l'app su un repository di test e verificare che le label vengano assegnate correttamente

### Esercizio 5 — Octokit SDK Dashboard

**Obiettivo:** Costruire uno script con Octokit che genera una dashboard organizzazione.

1. Usare `@octokit/rest` (JavaScript) o `PyGithub` (Python) per connettersi all'API
2. Recuperare tutti i repository dell'organizzazione con: stelle, fork, issues aperte, ultimo commit
3. Per ogni repository verificare: branch protection attiva, Dependabot configurato, secret scanning abilitato
4. Generare un report HTML con tabella ordinabile e indicatori colorati (verde/rosso) per ogni controllo
5. Implementare caching locale (file JSON) per ridurre le chiamate API e rispettare i rate limit

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub CLI Manual** — Documentazione completa del comando `gh` con tutti i subcommand. <https://cli.github.com/manual/> (consultato: 2026-05-24)
- **GitHub REST API** — Riferimento completo dell'API REST v3 con endpoint, parametri e esempi. <https://docs.github.com/en/rest> (consultato: 2026-05-24)
- **GitHub GraphQL API** — Documentazione dell'API GraphQL v4 con schema, query e mutations. <https://docs.github.com/en/graphql> (consultato: 2026-05-24)
- **GitHub GraphQL Explorer** — IDE interattivo per esplorare e testare query GraphQL. <https://docs.github.com/en/graphql/overview/explorer> (consultato: 2026-05-24)
- **GitHub Webhooks** — Configurazione e gestione dei webhook con lista completa degli eventi. <https://docs.github.com/en/webhooks> (consultato: 2026-05-24)
- **GitHub Apps** — Guida alla creazione e gestione di GitHub Apps con autenticazione JWT. <https://docs.github.com/en/apps> (consultato: 2026-05-24)
- **GitHub API Rate Limiting** — Limiti di frequenza per REST e GraphQL API con strategie di gestione. <https://docs.github.com/en/rest/overview/rate-limits-for-the-rest-api> (consultato: 2026-05-24)
- **Octokit.js** — SDK JavaScript ufficiale per l'API GitHub. <https://github.com/octokit/octokit.js> (consultato: 2026-05-24)
- **PyGithub** — Libreria Python per l'API GitHub REST. <https://pygithub.readthedocs.io/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Chacon S., Straub B., *Pro Git* (2nd ed.), Apress, 2014. Disponibile gratuitamente su <https://git-scm.com/book>.
- Doglio F., *REST API Development with Node.js* (2nd ed.), Apress, 2018.
- Eve H., *Designing Web APIs*, O'Reilly, 2018. Pattern e best practice per API design.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [12 — Repository Management](12-github-repository-management.md) | Le API e la CLI automatizzano la configurazione dei repository e delle branch protection trattate nel modulo 12 |
| [13 — Issues, Projects e Collaborazione](13-github-issues-projects-collaboration.md) | Le API consentono di automatizzare creazione e gestione di issue, label e milestones |
| [16 — GitHub Security e Scanning](16-github-security-scanning.md) | I webhook notificano eventi di sicurezza (alert Dependabot, secret scanning) per automazione della risposta |
| [17 — GitHub Actions Workflow e Sintassi](17-github-actions-workflow-sintassi.md) | I workflow Actions utilizzano `GITHUB_TOKEN` per interagire con le API dallo stesso repository |
| [22 — Copilot, Codespaces e Enterprise](22-github-copilot-codespaces-enterprise.md) | Le API Enterprise estendono le funzionalita trattate qui con endpoint specifici per organizzazioni |
| [26 — OIDC e Cloud Credentials](26-oidc-cloud-credentials.md) | L'autenticazione OIDC sostituisce i token statici per le integrazioni API con cloud provider |

---

## Glossario

| Termine | Definizione |
|---|---|
| **gh CLI** | Strumento a riga di comando ufficiale di GitHub per interagire con repository, issue, PR, Actions e API direttamente dal terminale. |
| **REST API v3** | API basata su HTTP con endpoint per ogni risorsa GitHub, che utilizza metodi standard (GET, POST, PATCH, DELETE) e risposte JSON. |
| **GraphQL API v4** | API query-based che consente di richiedere solo i campi necessari in una singola chiamata, riducendo over-fetching e numero di richieste. |
| **Webhook** | Callback HTTP che GitHub invia a un URL configurato quando si verificano eventi specifici nel repository (push, PR, issue). |
| **HMAC-SHA256** | Algoritmo di firma crittografica usato per verificare l'autenticita dei payload webhook tramite il header `X-Hub-Signature-256`. |
| **GitHub App** | Applicazione registrata su GitHub con permessi granulari e autenticazione JWT, alternativa superiore alle OAuth App per integrazioni. |
| **OAuth App** | Applicazione che autentica utenti GitHub tramite OAuth 2.0 flow, con permessi a livello utente (meno granulari delle GitHub App). |
| **Installation token** | Token temporaneo generato da una GitHub App per accedere alle risorse di una specifica installazione (organizzazione o repository). |
| **Rate limit** | Limite di frequenza delle chiamate API: 5000/ora per REST autenticato, 5000 punti/ora per GraphQL, resettato ogni ora. |
| **Octokit** | Famiglia di SDK ufficiali GitHub (JavaScript, Ruby, .NET) che forniscono un'interfaccia tipizzata per le API REST e GraphQL. |
| **Pagination** | Meccanismo per recuperare risultati in pagine: `page`/`per_page` per REST, cursori (`after`/`before`) per GraphQL. |
| **Personal access token** | Token generato dall'utente per autenticazione API, con scope configurabili. Fine-grained PAT (2023+) offre permessi per singolo repository. |
| **Webhook secret** | Stringa condivisa tra GitHub e il server webhook, usata per calcolare la firma HMAC e verificare l'autenticita delle richieste. |
| **X-GitHub-Delivery** | Header contenente un GUID unico per ogni consegna webhook, utilizzato per deduplicazione e replay protection. |
| **GraphQL mutation** | Operazione GraphQL che modifica dati (create, update, delete), distinta dalle query che sono di sola lettura. |
