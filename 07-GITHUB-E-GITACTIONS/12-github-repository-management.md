---
corso: "GitHub e Git Actions"
fase: "3 — Piattaforma GitHub"
modulo: "12"
titolo: "GitHub Repository Management"
versione: "GitHub 2024"
livello: "intermedio"
prerequisiti:
  - "conoscenza base di Git (commit, branch, merge)"
  - "account GitHub con almeno un repository"
  - "familiarita con la riga di comando e gh CLI"
obiettivi:
  - "configurare repository con settings, visibilita e feature toggle via API"
  - "implementare branch protection rules e rulesets per governance del codice"
  - "gestire CODEOWNERS per automazione delle code review per path"
  - "creare e utilizzare repository template per standardizzare i progetti"
  - "automatizzare la governance dei repository con GitHub API e Terraform"
tag: [github, repository, branch-protection, rulesets, CODEOWNERS, template, governance, API]
---

# GitHub Repository Management — Guida Approfondita

> **Modulo 12** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Configurare repository con settings, visibilita e feature toggle via API
> 2. Implementare branch protection rules e rulesets per governance del codice
> 3. Gestire CODEOWNERS per automazione delle code review per path
> 4. Creare e utilizzare repository template per standardizzare i progetti
> 5. Automatizzare la governance dei repository con GitHub API e Terraform
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **Branch protection rules: require PR, status checks, signed commits.**
2. **CODEOWNERS: per-path review automation.**
3. **Branch protection-as-code: Terraform GitHub provider o `gh api`.**
4. **Repo settings via API > GUI per audit/replay.**


## Indice
- [Panoramica](#panoramica)
- [Ciclo di Vita del Repository](#ciclo-di-vita-del-repository)
- [Creazione e Configurazione dei Repository](#creazione-e-configurazione-dei-repository)
- [Repository Settings — Configurazione Avanzata](#repository-settings--configurazione-avanzata)
- [Branch Protection Rules](#branch-protection-rules)
- [Rulesets: La Nuova Generazione di Protezione](#rulesets-la-nuova-generazione-di-protezione)
- [Push Rules — Protezione a Livello di Contenuto](#push-rules--protezione-a-livello-di-contenuto)
- [CODEOWNERS](#codeowners)
- [Strategie Avanzate CODEOWNERS per Monorepo](#strategie-avanzate-codeowners-per-monorepo)
- [Repository Templates](#repository-templates)
- [Custom Properties — Classificazione e Metadata Strutturata](#custom-properties--classificazione-e-metadata-strutturata)
- [Automazione della Governance con GitHub API](#automazione-della-governance-con-github-api)
- [GitHub Environments e Deployment Protection](#github-environments-e-deployment-protection)
- [Custom Deployment Protection Rules](#custom-deployment-protection-rules)
- [Repository Security — Configurazione Completa](#repository-security--configurazione-completa)
- [GitHub Apps per la Gestione dei Repository](#github-apps-per-la-gestione-dei-repository)
- [Inner Source e Repository con Visibilità Internal](#inner-source-e-repository-con-visibilità-internal)
- [Repository Policies a Livello Enterprise](#repository-policies-a-livello-enterprise)
- [Archiviazione, Trasferimento e Cancellazione dei Repository](#archiviazione-trasferimento-e-cancellazione-dei-repository)
- [Backup e Disaster Recovery dei Repository](#backup-e-disaster-recovery-dei-repository)
- [Topics, Descrizione e Metadata](#topics-descrizione-e-metadata)
- [Autolink References — Collegamento a Risorse Esterne](#autolink-references--collegamento-a-risorse-esterne)
- [Security Policy: SECURITY.md](#security-policy-securitymd)
- [README Best Practices](#readme-best-practices)
- [Selezione della Licenza](#selezione-della-licenza)
- [Best Practices](#best-practices)
- [Convenzioni di Naming per i Repository](#convenzioni-di-naming-per-i-repository)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Riferimenti](#riferimenti)

---

## Panoramica

La gestione efficace di un repository GitHub va ben oltre la semplice memorizzazione del codice. Comprende la configurazione delle regole di protezione dei branch, la definizione dei proprietari del codice, la creazione di template riutilizzabili, la documentazione del progetto e l'impostazione delle policy di sicurezza. Questa guida esplora in profondità tutti gli aspetti della gestione di un repository GitHub, dalle configurazioni di base alle funzionalità avanzate come i rulesets e i repository templates.

Una configurazione corretta del repository fin dall'inizio del progetto stabilisce le fondamenta per un workflow collaborativo efficiente, una code review strutturata e una gestione delle release prevedibile. La negligenza in questa fase iniziale porta invariabilmente a problemi che crescono esponenzialmente con la dimensione del team e la complessità del progetto.

---

## Ciclo di Vita del Repository

Ogni repository attraversa fasi distinte durante la sua esistenza. Comprendere questo ciclo di vita è essenziale per applicare le policy corrette in ogni fase e garantire una governance coerente a livello organizzativo.

### Le Fasi del Ciclo di Vita

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Creazione   │───▶│ Sviluppo     │───▶│ Maturità     │───▶│ Manutenzione │───▶│ Fine Vita    │
│              │    │ Attivo       │    │              │    │              │    │              │
│ • Template   │    │ • CI/CD      │    │ • Stable     │    │ • Security   │    │ • Archive    │
│ • Settings   │    │ • Branch     │    │ • Release    │    │   patches    │    │ • Transfer   │
│ • Rulesets   │    │   protection │    │   cadence    │    │ • Dependabot │    │ • Delete     │
│ • CODEOWNERS │    │ • Code review│    │ • Full docs  │    │ • Minimal    │    │ • Fork       │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Fase 1 — Creazione e Bootstrap

La fase di creazione stabilisce le fondamenta. Un repository creato senza configurazione iniziale accumula debito tecnico organizzativo che diventa progressivamente più costoso da risolvere. I passi critici in questa fase includono:

- **Selezione del template**: Utilizzare un repository template che includa `.github/`, `CODEOWNERS`, workflow CI/CD, file di configurazione del linter e del formatter.
- **Configurazione immediata delle regole**: Applicare branch protection o rulesets sul branch `main` prima del primo commit di funzionalità.
- **Documentazione iniziale**: README con istruzioni di setup, CONTRIBUTING con le regole del progetto, SECURITY.md con il processo di segnalazione, LICENSE con la licenza scelta.
- **Custom properties**: Assegnare le proprietà personalizzate dell'organizzazione (team responsabile, classificazione di sicurezza, dominio funzionale) per abilitare il targeting con rulesets.

### Fase 2 — Sviluppo Attivo

Durante lo sviluppo attivo, le regole di governance devono bilanciare protezione e velocità. Le configurazioni tipiche includono:

- Branch protection con almeno 1 reviewer richiesto e status check CI obbligatori.
- CODEOWNERS aggiornato man mano che la struttura del progetto evolve.
- Dependabot configurato per aggiornamenti settimanali delle dipendenze.
- Secret scanning e push protection abilitati.
- Environment di staging con deployment automatico, environment di produzione con approvazione manuale.

### Fase 3 — Maturità

Un repository maturo ha una cadenza di release stabilita, documentazione completa e processi ben definiti. Le configurazioni diventano più restrittive:

- Rulesets con almeno 2 reviewer richiesti e code owner review obbligatorio.
- Status check estesi (build, test, lint, security scan, coverage).
- Tag protection per le release con pattern `v*`.
- Cronologia lineare obbligatoria per facilitare il debugging con `git bisect`.
- Audit periodico degli accessi e delle regole.

### Fase 4 — Manutenzione

Nella fase di manutenzione, il repository riceve solo patch di sicurezza e bug fix critici. Le configurazioni si concentrano sulla stabilità:

- Riduzione del numero di contributor attivi con permessi di push.
- Enfasi su Dependabot per aggiornamenti di sicurezza automatici.
- Review meno frequenti ma più rigorose.
- Documentazione dello stato "maintenance mode" nel README.

### Fase 5 — Fine Vita

La fase finale prevede una delle seguenti azioni: archiviazione (read-only permanente), trasferimento (cambio di proprietà), cancellazione (rimozione definitiva) o fork (preservazione della comunità). Ogni opzione ha implicazioni diverse per gli utenti dipendenti dal repository, e la scelta deve essere comunicata in anticipo.

```bash
# Verificare lo stato del ciclo di vita di un repository
gh api repos/{owner}/{repo} --jq '{
  name: .name,
  created_at: .created_at,
  updated_at: .updated_at,
  pushed_at: .pushed_at,
  archived: .archived,
  disabled: .disabled,
  open_issues: .open_issues_count,
  forks: .forks_count,
  stargazers: .stargazers_count,
  size_kb: .size,
  default_branch: .default_branch
}'

# Calcolare l'età del repository e il tempo dall'ultimo push
gh api repos/{owner}/{repo} --jq '
  "Creato: \(.created_at) | Ultimo push: \(.pushed_at) | Archiviato: \(.archived)"'
```

### Indicatori per la Transizione di Fase

| Indicatore | Da | A | Azione |
|---|---|---|---|
| Nessun commit in 6+ mesi | Sviluppo Attivo | Manutenzione | Ridurre contributor, abilitare solo security patches |
| Nessun commit in 12+ mesi | Manutenzione | Fine Vita | Valutare archiviazione |
| CVE critiche non risolte in 30 giorni | Qualsiasi | Urgenza | Escalation, valutare archiviazione se nessun maintainer |
| Fork attivo con più contributor | Fine Vita | N/A | Comunicare il fork come successore |
| Dipendenze major EOL | Maturità | Manutenzione | Pianificare migrazione o archiviazione |

---

## Creazione e Configurazione dei Repository

### Creazione tramite UI e CLI

```bash
# Creare un repository con gh CLI
gh repo create my-project --public --description "Descrizione del progetto" --clone

# Repository privato con .gitignore e licenza
gh repo create my-project --private \
  --gitignore Node \
  --license MIT \
  --description "Progetto aziendale" \
  --clone

# Creare da un template
gh repo create my-project --template org/template-repo --clone

# Creare all'interno di un'organizzazione
gh repo create my-org/my-project --public --clone

# Visualizzare le impostazioni del repository
gh repo view --json name,description,visibility,defaultBranchRef
```

### Configurazione Post-Creazione

```bash
# Configurare il branch predefinito
gh api repos/{owner}/{repo} -X PATCH -f default_branch=main

# Abilitare/disabilitare features
gh repo edit --enable-wiki=false
gh repo edit --enable-issues=true
gh repo edit --enable-projects=true
gh repo edit --enable-discussions=true

# Configurare merge strategies permesse
gh repo edit --enable-merge-commit=true
gh repo edit --enable-squash-merge=true
gh repo edit --enable-rebase-merge=false

# Abilitare auto-delete dei branch dopo il merge
gh repo edit --delete-branch-on-merge=true

# Configurare il template del messaggio di squash merge
gh api repos/{owner}/{repo} -X PATCH \
  -f squash_merge_commit_title="PR_TITLE" \
  -f squash_merge_commit_message="PR_BODY"
```

### Impostazioni del Repository

Le impostazioni chiave da configurare in Settings > General:

1. **Default branch**: Il branch principale (tipicamente `main`)
2. **Features**: Issues, Projects, Wiki, Discussions, Sponsorships
3. **Pull Requests**: Merge strategies permesse, auto-merge, branch deletion
4. **Danger Zone**: Visibility, transfer, archive, delete

```bash
# Archiviare un repository
gh repo archive my-org/old-project

# Trasferire un repository
gh api repos/{owner}/{repo}/transfer -X POST -f new_owner="new-org"

# Cambiare visibilità
gh repo edit --visibility private
```

---

## Repository Settings — Configurazione Avanzata

### Merge Strategies e Commit Squashing

La scelta delle merge strategies permesse ha un impatto significativo sulla qualità della cronologia git:

```bash
# Configurazione completa delle merge strategies
gh api repos/{owner}/{repo} -X PATCH \
  -F allow_merge_commit=true \
  -F allow_squash_merge=true \
  -F allow_rebase_merge=false \
  -F allow_auto_merge=true \
  -F delete_branch_on_merge=true \
  -F squash_merge_commit_title="PR_TITLE" \
  -F squash_merge_commit_message="PR_BODY" \
  -F merge_commit_title="PR_TITLE" \
  -F merge_commit_message="PR_BODY" \
  -F allow_update_branch=true

# Strategie:
# merge_commit: Crea un merge commit (preserva cronologia completa del branch)
# squash:       Comprime tutti i commit in uno (cronologia lineare e pulita)
# rebase:       Ri-applica i commit sul branch base (cronologia lineare senza merge commit)
```

| Strategia | Cronologia | Uso Consigliato |
|-----------|------------|-----------------|
| Merge commit | Completa (con merge commit) | Branch longevi, feature complesse |
| Squash merge | Lineare (1 commit per PR) | Feature piccole, team grandi |
| Rebase merge | Lineare (commit originali) | Team piccoli, commit atomici |

### Auto-Merge

L'auto-merge consente di configurare una PR per il merge automatico appena tutte le condizioni (status checks, approvazioni) sono soddisfatte:

```bash
# Abilitare auto-merge sul repository
gh api repos/{owner}/{repo} -X PATCH -F allow_auto_merge=true

# Abilitare auto-merge su una PR specifica
gh pr merge <pr-number> --auto --squash

# Disabilitare auto-merge su una PR
gh pr merge <pr-number> --disable-auto
```

### Repository Insights e Metriche

```bash
# Statistiche dei contributor
gh api repos/{owner}/{repo}/stats/contributors --jq '
  .[] | {author: .author.login, commits: .total, additions: ([.weeks[].a] | add), deletions: ([.weeks[].d] | add)}'

# Frequenza dei commit (ultimi 52 settimane)
gh api repos/{owner}/{repo}/stats/commit_activity --jq '.[-4:] | .[] | {week: .week, total: .total}'

# Code frequency (aggiunte/rimozioni per settimana)
gh api repos/{owner}/{repo}/stats/code_frequency --jq '.[-4:]'

# Attività di punch card (distribuzione oraria dei commit)
gh api repos/{owner}/{repo}/stats/punch_card

# Community profile (completezza della documentazione)
gh api repos/{owner}/{repo}/community/profile --jq '{
  health_percentage: .health_percentage,
  has_readme: (.files.readme != null),
  has_contributing: (.files.contributing != null),
  has_license: (.files.license != null),
  has_code_of_conduct: (.files.code_of_conduct != null),
  has_security: (.files.security != null),
  has_issue_template: (.files.issue_template != null),
  has_pr_template: (.files.pull_request_template != null)
}'
```

### Repository Traffic e Analytics Avanzate

Oltre alle statistiche sui contributor e sulla frequenza dei commit, GitHub offre un modulo dedicato al traffico del repository, accessibile nella tab Insights > Traffic. Queste metriche misurano la visibilita e la popolarita del repository e sono disponibili per i repository pubblici su tutti i piani e per i repository privati su GitHub Pro, GitHub Team e GitHub Enterprise Cloud.

#### Metriche di Traffico Disponibili

| Metrica | Descrizione | Aggiornamento | Retentione |
|---|---|---|---|
| Views | Numero totale di visualizzazioni della pagina del repository | Ogni ora | 14 giorni |
| Unique visitors | Numero di visitatori unici (deduplificati per utente) | Ogni ora | 14 giorni |
| Clones | Numero totale di clone (`git clone`) eseguiti | Ogni ora | 14 giorni |
| Unique cloners | Numero di utenti unici che hanno clonato il repository | Ogni ora | 14 giorni |
| Referring sites | Siti web che hanno generato traffico verso il repository | Giornaliero | 14 giorni |
| Popular content | Pagine del repository piu visitate (file, directory) | Giornaliero | 14 giorni |

La limitazione principale delle metriche di traffico e la retentione di soli 14 giorni. Per analisi a lungo termine e necessario esportare periodicamente i dati e salvarli in un sistema esterno.

#### Accesso alle Metriche di Traffico via API

```bash
# Visualizzazioni del repository (ultimi 14 giorni)
gh api repos/{owner}/{repo}/traffic/views --jq '{
  count: .count,
  uniques: .uniques,
  daily: [.views[] | {timestamp: .timestamp, count: .count, uniques: .uniques}]
}'

# Clone del repository (ultimi 14 giorni)
gh api repos/{owner}/{repo}/traffic/clones --jq '{
  count: .count,
  uniques: .uniques,
  daily: [.clones[] | {timestamp: .timestamp, count: .count, uniques: .uniques}]
}'

# Siti referrer (top 10)
gh api repos/{owner}/{repo}/traffic/popular/referrers --jq '
  .[] | "\(.referrer): \(.count) views (\(.uniques) unique)"'

# Contenuti piu visitati (top 10 percorsi)
gh api repos/{owner}/{repo}/traffic/popular/paths --jq '
  .[] | "\(.path): \(.count) views (\(.uniques) unique)"'
```

#### Script per la Raccolta Storica del Traffico

Poiche GitHub conserva i dati di traffico solo per 14 giorni, e consigliabile implementare un job automatizzato che esporti le metriche periodicamente. Lo script seguente salva i dati in formato JSON con timestamp, consentendo l'aggregazione storica in un database o file flat:

```bash
#!/usr/bin/env bash
# Esportazione periodica delle metriche di traffico GitHub
# Eseguire via cron ogni settimana: 0 6 * * 1 /path/to/traffic-export.sh

set -euo pipefail

ORG="my-org"
DATA_DIR="/var/data/github-traffic"
DATE=$(date -u +%Y-%m-%d)

mkdir -p "$DATA_DIR"

gh repo list "$ORG" --limit 200 --json name --jq '.[].name' | while read -r repo; do
  REPO_DIR="$DATA_DIR/$repo"
  mkdir -p "$REPO_DIR"

  # Views
  gh api "repos/$ORG/$repo/traffic/views" 2>/dev/null \
    > "$REPO_DIR/views-$DATE.json" || true

  # Clones
  gh api "repos/$ORG/$repo/traffic/clones" 2>/dev/null \
    > "$REPO_DIR/clones-$DATE.json" || true

  # Referrers
  gh api "repos/$ORG/$repo/traffic/popular/referrers" 2>/dev/null \
    > "$REPO_DIR/referrers-$DATE.json" || true

  # Popular paths
  gh api "repos/$ORG/$repo/traffic/popular/paths" 2>/dev/null \
    > "$REPO_DIR/paths-$DATE.json" || true
done

echo "Esportazione completata: $DATA_DIR (data: $DATE)"
```

#### Automazione con GitHub Actions

```yaml
# .github/workflows/traffic-collector.yml
name: Traffic Data Collector

on:
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedi alle 06:00 UTC
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Collect traffic data
        env:
          GH_TOKEN: ${{ secrets.TRAFFIC_TOKEN }}
        run: |
          mkdir -p traffic-data
          DATE=$(date -u +%Y-%m-%d)
          gh api repos/${{ github.repository }}/traffic/views > "traffic-data/views-$DATE.json"
          gh api repos/${{ github.repository }}/traffic/clones > "traffic-data/clones-$DATE.json"
          gh api repos/${{ github.repository }}/traffic/popular/referrers > "traffic-data/referrers-$DATE.json"

      - name: Commit traffic data
        run: |
          git config user.name "traffic-bot"
          git config user.email "bot@example.com"
          git add traffic-data/
          git diff --staged --quiet || git commit -m "chore: collect traffic data $(date -u +%Y-%m-%d)"
          git push
```

Le metriche di traffico sono particolarmente utili per valutare l'efficacia della documentazione, misurare l'impatto di annunci o rilasci, identificare i canali di scoperta principali e comprendere quali parti del repository attirano maggiore attenzione dalla comunita.

### Gestione dei Collaboratori e Permessi

```bash
# Invitare un collaboratore (repository personale)
gh api repos/{owner}/{repo}/collaborators/{username} -X PUT -f permission=push

# Livelli di permesso:
# pull     — Read-only (clone, fork)
# triage   — Read + gestione issues/PR (no push)
# push     — Read + Write (push, merge PR)
# maintain — Push + gestione repository (no admin)
# admin    — Accesso completo

# Listare i collaboratori con i loro permessi
gh api repos/{owner}/{repo}/collaborators --jq '.[] | {login: .login, permission: .role_name}'

# Per organizzazioni: gestire i team
gh api orgs/{org}/teams/{team}/repos/{owner}/{repo} -X PUT -f permission=push

# Verificare i permessi di un utente specifico
gh api repos/{owner}/{repo}/collaborators/{username}/permission --jq '.permission'
```

### Webhooks e Notifications

```bash
# Creare un webhook per notifiche
gh api repos/{owner}/{repo}/hooks -X POST \
  --input - << 'EOF'
{
  "name": "web",
  "active": true,
  "events": ["push", "pull_request", "issues", "release"],
  "config": {
    "url": "https://webhook.example.com/github",
    "content_type": "json",
    "secret": "webhook-secret-value",
    "insecure_ssl": "0"
  }
}
EOF

# Listare i webhook configurati
gh api repos/{owner}/{repo}/hooks --jq '.[] | {id: .id, url: .config.url, events: .events, active: .active}'

# Testare un webhook (re-delivery dell'ultimo payload)
gh api repos/{owner}/{repo}/hooks/{hook_id}/tests -X POST
```

---

## Branch Protection Rules

### Configurazione delle Regole

Le branch protection rules proteggono branch specifici da modifiche non autorizzate. Si configurano in Settings > Branches > Branch protection rules.

```bash
# Creare una branch protection rule via API
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci/build", "ci/test", "ci/lint"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
```

### Regole Dettagliate

#### Required Pull Request Reviews

```yaml
# Configurazione concettuale
required_pull_request_reviews:
  required_approving_review_count: 2    # Minimo 2 approvazioni
  dismiss_stale_reviews: true           # Invalidare approvazioni dopo nuovi push
  require_code_owner_reviews: true      # Richiesta approvazione dei code owners
  require_last_push_approval: true      # L'ultimo pusher non può auto-approvare
  dismissal_restrictions:               # Chi può dismissare le review
    users: ["team-lead"]
    teams: ["senior-devs"]
  bypass_pull_request_allowances:       # Chi può bypassare le PR
    users: ["release-bot"]
    teams: ["release-managers"]
```

#### Required Status Checks

```yaml
required_status_checks:
  strict: true                          # Branch deve essere aggiornato prima del merge
  contexts:
    - "ci/build"                        # Nome del check richiesto
    - "ci/test"
    - "ci/lint"
    - "security/codeql"
    - "codecov/project"
```

L'opzione `strict: true` è particolarmente importante: richiede che il branch sia aggiornato con il branch base prima del merge, garantendo che i test passino anche con le ultime modifiche del branch base.

#### Required Linear History

Quando abilitata, questa opzione impedisce i merge commit, forzando l'uso di squash merge o rebase merge. Questo produce una cronologia lineare più leggibile.

#### Required Signed Commits

```bash
# Configurare la firma GPG dei commit
git config --global commit.gpgsign true
git config --global user.signingkey ABC123DEF456

# Verificare la firma di un commit
git verify-commit HEAD

# Visualizzare le firme nel log
git log --show-signature
```

#### Lock Branch e Allow Specific Actors

```yaml
# Lock branch: rendere il branch read-only
lock_branch: true

# Permettere solo ad attori specifici di pushare
restrictions:
  users: ["deploy-bot"]
  teams: ["release-managers"]
  apps: ["github-actions"]
```

---

## Rulesets: La Nuova Generazione di Protezione

### Cos'è un Ruleset

I rulesets (introdotti nel 2023) sono la versione evoluta delle branch protection rules. Offrono maggiore flessibilità, supporto per tag, regole a livello di organizzazione e la possibilità di applicare regole a pattern multipli di branch.

### Configurazione dei Rulesets

```bash
# Creare un ruleset via API
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Production Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main", "refs/heads/release/**"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "deletion"
    },
    {
      "type": "non_fast_forward"
    },
    {
      "type": "required_linear_history"
    },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          { "context": "ci/build" },
          { "context": "ci/test" },
          { "context": "security/scan" }
        ]
      }
    },
    {
      "type": "commit_message_pattern",
      "parameters": {
        "operator": "must_match",
        "pattern": "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\(.+\\))?: .+"
      }
    },
    {
      "type": "committer_email_pattern",
      "parameters": {
        "operator": "must_match",
        "pattern": ".*@azienda\\.com$"
      }
    }
  ],
  "bypass_actors": [
    {
      "actor_id": 1,
      "actor_type": "Team",
      "bypass_mode": "always"
    }
  ]
}
EOF
```

### Vantaggi dei Rulesets rispetto alle Branch Protection Rules

| Aspetto | Branch Protection | Rulesets |
|---------|-------------------|----------|
| Scope | Singolo branch/pattern | Pattern multipli di branch e tag |
| Livello | Repository | Repository e organizzazione |
| Bypass | Limitato | Granulare per attore |
| Enforcement | Sempre attivo | active, evaluate (dry-run), disabled |
| Pattern commit msg | No | Sì |
| Pattern email | No | Sì |
| Import/Export | No | Sì (JSON) |
| Audit | Limitato | Completo |

### Rulesets a Livello di Organizzazione

```bash
# Creare un ruleset a livello di organizzazione
gh api orgs/{org}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Org-wide Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "repository_name": {
      "include": ["*"],
      "exclude": ["sandbox-*", "test-*"]
    },
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true
      }
    }
  ]
}
EOF
```

---

## Push Rules — Protezione a Livello di Contenuto

### Cosa Sono le Push Rules

Le push rules, disponibili in generale dal settembre 2024, sono un tipo speciale di ruleset che opera a livello di contenuto dei commit anziché a livello di branch o tag. Mentre le branch protection rules e i rulesets standard controllano chi può fare push e in quali condizioni, le push rules controllano cosa può essere pushato, indipendentemente dal branch di destinazione.

La caratteristica fondamentale delle push rules è che si applicano all'intero fork network del repository. Se un repository ha push rules abilitate, queste si propagano automaticamente a tutti i fork, garantendo che le restrizioni non possano essere aggirate forkando il repository e pushando contenuti non conformi.

### Tipi di Push Rules Disponibili

#### Restrizione per Percorsi di File

Impedisce commit che includono modifiche in percorsi specifici. Questa regola è particolarmente utile per proteggere file di configurazione sensibili, workflow CI/CD o directory con accesso ristretto:

```bash
# Creare un ruleset con push rules per percorsi di file
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Protect Sensitive Paths",
  "target": "push",
  "enforcement": "active",
  "rules": [
    {
      "type": "file_path_restriction",
      "parameters": {
        "restricted_file_paths": [
          ".github/workflows/**",
          "terraform/**",
          "*.pem",
          "*.key",
          ".env*",
          "config/production.yml"
        ]
      }
    }
  ],
  "bypass_actors": [
    {
      "actor_id": 1,
      "actor_type": "Team",
      "bypass_mode": "always"
    }
  ]
}
EOF
```

#### Restrizione per Estensioni di File

Impedisce commit che includono file con estensioni specifiche. Utile per prevenire l'inclusione accidentale di binari, file compilati o file di backup:

```bash
# Push rule per bloccare estensioni non desiderate
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Block Unwanted Extensions",
  "target": "push",
  "enforcement": "active",
  "rules": [
    {
      "type": "file_extension_restriction",
      "parameters": {
        "restricted_file_extensions": [
          ".exe", ".dll", ".so", ".dylib",
          ".jar", ".war", ".ear",
          ".zip", ".tar", ".gz", ".rar",
          ".bak", ".swp", ".tmp",
          ".env", ".pem", ".key", ".p12"
        ]
      }
    }
  ]
}
EOF
```

#### Restrizione per Dimensione dei File

Impedisce commit che includono file che superano un limite di dimensione specificato. Questa regola previene l'inserimento accidentale di binari pesanti o dataset nel repository:

```bash
# Push rule per limitare la dimensione massima dei file
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "File Size Limit",
  "target": "push",
  "enforcement": "active",
  "rules": [
    {
      "type": "max_file_size",
      "parameters": {
        "max_file_size": 10485760
      }
    }
  ]
}
EOF
# max_file_size è in byte: 10485760 = 10 MB
```

#### Restrizione per Lunghezza del Percorso

Impedisce commit con percorsi di file che superano un numero massimo di caratteri, prevenendo problemi di compatibilità cross-platform (ad esempio Windows ha un limite di 260 caratteri per i percorsi):

```bash
# Push rule per limitare la lunghezza dei percorsi
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Path Length Limit",
  "target": "push",
  "enforcement": "active",
  "rules": [
    {
      "type": "file_path_length",
      "parameters": {
        "max_file_path_length": 200
      }
    }
  ]
}
EOF
```

### Push Rules Combinate — Esempio Completo

Un approccio production-grade combina tutte le push rules in un unico ruleset per una protezione completa:

```bash
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Comprehensive Push Protection",
  "target": "push",
  "enforcement": "evaluate",
  "rules": [
    {
      "type": "file_path_restriction",
      "parameters": {
        "restricted_file_paths": [
          ".github/workflows/**",
          "infrastructure/**",
          "deploy/**"
        ]
      }
    },
    {
      "type": "file_extension_restriction",
      "parameters": {
        "restricted_file_extensions": [".exe", ".dll", ".env", ".pem", ".key"]
      }
    },
    {
      "type": "max_file_size",
      "parameters": {
        "max_file_size": 5242880
      }
    },
    {
      "type": "file_path_length",
      "parameters": {
        "max_file_path_length": 200
      }
    }
  ],
  "bypass_actors": [
    {
      "actor_id": 1,
      "actor_type": "OrganizationAdmin",
      "bypass_mode": "always"
    },
    {
      "actor_id": 5,
      "actor_type": "Team",
      "bypass_mode": "pull_request"
    }
  ]
}
EOF
# Nota: enforcement "evaluate" per testare senza bloccare.
# Passare ad "active" dopo aver verificato che non ci siano falsi positivi.
```

### Differenze tra Push Rules e Branch/Tag Rulesets

| Aspetto | Branch/Tag Rulesets | Push Rules |
|---------|---------------------|------------|
| Target | Branch o tag specifici | Tutti i push al repository |
| Scope | Singolo repository | Repository + tutti i fork |
| Controllo | Chi può pushare, requisiti PR/review | Cosa può essere pushato (file, dimensioni, estensioni) |
| Pattern | Branch/tag name pattern | File path pattern (fnmatch) |
| Disponibilità | Free (repo), Team/Enterprise (org) | Team (privati), Enterprise Cloud (interni) |

---

## CODEOWNERS

### Sintassi e Configurazione

Il file `CODEOWNERS` definisce automaticamente i reviewer richiesti per le pull request in base ai file modificati. Deve essere posizionato in `.github/CODEOWNERS`, `CODEOWNERS` nella root, o `docs/CODEOWNERS`.

```
# .github/CODEOWNERS

# Sintassi: pattern  @owner1 @owner2

# Default owner per tutto il repository
*                           @team-lead

# Proprietari per directory specifiche
/src/frontend/              @frontend-team
/src/backend/               @backend-team
/src/api/                   @api-team @backend-team
/infrastructure/            @devops-team
/docs/                      @docs-team

# Proprietari per tipi di file
*.js                        @frontend-team
*.ts                        @frontend-team
*.py                        @backend-team
*.go                        @backend-team
*.tf                        @devops-team
*.yml                       @devops-team

# File critici che richiedono approvazione di specifici individui
/src/security/              @security-lead @cto
/.github/workflows/         @devops-team @security-lead
/package.json               @frontend-lead
/Dockerfile                 @devops-team

# Configurazione e CI/CD
/.github/                   @devops-team
/terraform/                 @devops-team @infra-lead

# Database migrations
/migrations/                @dba-team @backend-lead

# Ignorare pattern (nessun owner richiesto)
/tests/fixtures/            # Nessuno — chiunque può modificare
```

### Regole Importanti

1. L'ultima regola che matcha ha la precedenza (ordine bottom-to-top)
2. I pattern supportano la stessa sintassi di `.gitignore`
3. Gli owner possono essere utenti (`@username`), team (`@org/team-name`) o email
4. Per essere effettivo, richiede che "Require review from Code Owners" sia abilitato nelle branch protection rules

```bash
# Verificare i CODEOWNERS di un file
gh api repos/{owner}/{repo}/codeowners/errors
# Mostra eventuali errori di sintassi nel file CODEOWNERS
```

---

## Strategie Avanzate CODEOWNERS per Monorepo

### Sfide dei Monorepo

Nei monorepo di grandi dimensioni, il file CODEOWNERS può diventare rapidamente complesso e difficile da mantenere. Le sfide principali includono:

- **Conflitti di proprietà**: File che matchano più pattern con owner diversi.
- **Review fatigue**: Team che ricevono troppe richieste di review per file non critici.
- **Scalabilità**: File CODEOWNERS con centinaia di regole che diventano ingestibili.
- **Onboarding**: Nuovi sviluppatori che non capiscono chi è responsabile di cosa.

### Pattern Avanzati per Monorepo Multi-Team

```
# .github/CODEOWNERS — Monorepo Enterprise

# ================================================================
# REGOLA GLOBALE — Catch-all per file non coperti da regole specifiche
# ================================================================
*                                       @org/platform-team

# ================================================================
# INFRASTRUTTURA E CI/CD — Accesso ristretto
# ================================================================
/.github/                               @org/platform-team
/.github/workflows/                     @org/devops-team @org/security-team
/.github/CODEOWNERS                     @org/engineering-leads
/infrastructure/                        @org/devops-team
/infrastructure/production/             @org/devops-team @org/sre-team
/infrastructure/modules/                @org/devops-team
*.tf                                    @org/devops-team
*.tfvars                                @org/devops-team @org/security-team
/docker/                                @org/devops-team
Dockerfile*                             @org/devops-team

# ================================================================
# PACCHETTI CONDIVISI — Librerie interne
# ================================================================
/packages/shared-ui/                    @org/design-system-team
/packages/shared-utils/                 @org/platform-team
/packages/auth-sdk/                     @org/auth-team @org/security-team
/packages/api-client/                   @org/api-team

# ================================================================
# SERVIZI — Microservizi nel monorepo
# ================================================================
/services/user-service/                 @org/user-team
/services/payment-service/              @org/payments-team @org/security-team
/services/notification-service/         @org/notifications-team
/services/analytics-service/            @org/data-team

# ================================================================
# FRONTEND — Applicazioni web
# ================================================================
/apps/web-app/                          @org/frontend-team
/apps/web-app/src/components/           @org/frontend-team @org/design-system-team
/apps/admin-dashboard/                  @org/internal-tools-team
/apps/mobile-web/                       @org/mobile-team

# ================================================================
# CONFIGURAZIONE ROOT — File di alto impatto
# ================================================================
package.json                            @org/platform-team
pnpm-workspace.yaml                     @org/platform-team
tsconfig.base.json                      @org/platform-team
.eslintrc.*                             @org/platform-team
.prettierrc*                            @org/platform-team

# ================================================================
# DATABASE — Migrazioni e schema
# ================================================================
**/migrations/                          @org/dba-team
**/schema.prisma                        @org/dba-team @org/backend-leads
**/schema.sql                           @org/dba-team

# ================================================================
# SICUREZZA — File che richiedono review di sicurezza
# ================================================================
**/auth/                                @org/security-team
**/crypto/                              @org/security-team
**/permissions/                         @org/security-team
SECURITY.md                             @org/security-team
**/security/**                          @org/security-team

# ================================================================
# DOCUMENTAZIONE — Nessun blocco, review opzionale
# ================================================================
/docs/                                  @org/docs-team
*.md                                    # Nessun owner obbligatorio per i .md generici
README.md                               @org/docs-team
CONTRIBUTING.md                         @org/engineering-leads
```

### Gestire la Review Load con Team Routing

GitHub supporta il review assignment per team, che distribuisce automaticamente le richieste di review tra i membri del team anziché assegnarle all'intero team:

```bash
# Configurare il review assignment per un team
# Settings → Teams → [team] → Code review

# Opzioni disponibili:
# 1. "Auto assignment" — Distribuisce automaticamente le review
#    - Round robin: Assegna in rotazione
#    - Load balance: Assegna a chi ha meno review pendenti
# 2. Numero di reviewer richiesti (subset del team)
# 3. Notifica solo i reviewer assegnati (non tutto il team)
# 4. Skip members su PR proprie
```

Per team di grandi dimensioni (10+ membri), il load balancing evita che tutti ricevano notifiche per ogni PR, concentrando le review su un subset rotante.

### Validazione Automatica del CODEOWNERS

```bash
#!/usr/bin/env bash
# Script per validare il file CODEOWNERS prima del commit

CODEOWNERS_FILE=".github/CODEOWNERS"

echo "=== Validazione CODEOWNERS ==="

# 1. Verificare che il file esista
if [ ! -f "$CODEOWNERS_FILE" ]; then
  echo "ERRORE: $CODEOWNERS_FILE non trovato"
  exit 1
fi

# 2. Verificare errori di sintassi via API (richiede repo push)
errors=$(gh api repos/{owner}/{repo}/codeowners/errors 2>/dev/null)
error_count=$(echo "$errors" | jq '.errors | length' 2>/dev/null)
if [ "$error_count" -gt 0 ]; then
  echo "ERRORE: $error_count errori di sintassi trovati:"
  echo "$errors" | jq -r '.errors[] | "  Riga \(.line): \(.message)"'
  exit 1
fi

# 3. Verificare che tutti i team referenziati esistano
grep -oP '@\S+/\S+' "$CODEOWNERS_FILE" | sort -u | while read -r team; do
  org=$(echo "$team" | cut -d/ -f1 | tr -d '@')
  team_slug=$(echo "$team" | cut -d/ -f2)
  result=$(gh api "orgs/$org/teams/$team_slug" 2>/dev/null)
  if [ $? -ne 0 ]; then
    echo "WARNING: Team $team non trovato o non accessibile"
  fi
done

# 4. Verificare che non ci siano pattern duplicati
duplicates=$(grep -v '^#' "$CODEOWNERS_FILE" | grep -v '^\s*$' | \
  awk '{print $1}' | sort | uniq -d)
if [ -n "$duplicates" ]; then
  echo "WARNING: Pattern duplicati (l'ultimo sovrascrive i precedenti):"
  echo "$duplicates" | while read -r dup; do
    echo "  $dup"
  done
fi

echo "Validazione completata."
```

### Rulesets con Required Review per Team Specifici (Novembre 2025)

A partire da novembre 2025, i rulesets supportano la richiesta di review da team specifici per file e cartelle specifiche, complementando il CODEOWNERS con una policy enforcement separata:

```bash
# Ruleset che richiede review da team specifici per percorsi critici
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Security Team Review for Auth Code",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main", "refs/heads/release/**"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "require_code_owner_review": true,
        "required_review_thread_resolution": true
      }
    }
  ]
}
EOF
```

La differenza chiave tra CODEOWNERS e rulesets con required review per team è che CODEOWNERS definisce la proprietà (chi viene notificato e assegnato), mentre i rulesets definiscono la policy (chi deve approvare affinché il merge sia permesso). Usare entrambi in combinazione offre il massimo controllo.

---

## Repository Templates

### Creare un Template Repository

Un template repository è un blueprint per nuovi progetti. Contiene la struttura delle directory, i file di configurazione, i workflow CI/CD e tutto ciò che dovrebbe essere standardizzato.

```bash
# Marcare un repository come template
gh api repos/{owner}/{repo} -X PATCH -F is_template=true

# Struttura tipica di un template
template-node/
├── .github/
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── codeql.yml
├── .gitattributes
├── .gitignore
├── .editorconfig
├── .prettierrc
├── .eslintrc.js
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── package.json
├── tsconfig.json
└── src/
    └── index.ts
```

### Usare un Template

```bash
# Creare un repository da un template
gh repo create my-new-project --template org/template-node --clone

# Via web: "Use this template" button sulla pagina del repository

# Differenza rispetto al fork:
# - Template: crea un repository pulito senza cronologia
# - Fork: mantiene tutta la cronologia e il collegamento upstream
```

---

## Custom Properties — Classificazione e Metadata Strutturata

### Cosa Sono le Custom Properties

Le custom properties (disponibili in GA dal febbraio 2024, con aggiornamenti significativi nel 2025-2026) sono campi di metadata strutturata che è possibile aggiungere ai repository all'interno di un'organizzazione. Consentono di classificare, categorizzare e filtrare i repository in modo programmatico, e si integrano direttamente con i rulesets per il targeting condizionale.

A differenza dei topics (tag informali e non strutturati), le custom properties hanno uno schema definito a livello di organizzazione o enterprise, con tipi di dati validati e valori opzionalmente obbligatori. Questo le rende adatte per la governance formale.

### Tipi di Custom Properties Supportati

| Tipo | Descrizione | Esempio |
|---|---|---|
| `string` | Testo libero | `"Descrizione del servizio"` |
| `single_select` | Singola selezione da valori predefiniti | `"production"`, `"staging"`, `"development"` |
| `multi_select` | Selezione multipla da valori predefiniti | `["frontend", "backend"]` |
| `true_false` | Booleano | `true` / `false` |
| `url` | URL con validazione (dicembre 2025) | `"https://docs.example.com"` |

### Creare e Gestire Custom Properties via API

```bash
# Creare una custom property a livello di organizzazione
gh api orgs/{org}/properties/schema -X PUT \
  --input - << 'EOF'
[
  {
    "property_name": "service_tier",
    "value_type": "single_select",
    "required": true,
    "default_value": "standard",
    "description": "Classificazione del livello di servizio del repository",
    "allowed_values": ["critical", "high", "standard", "experimental"]
  },
  {
    "property_name": "owning_team",
    "value_type": "string",
    "required": true,
    "description": "Team responsabile del repository"
  },
  {
    "property_name": "compliance_scope",
    "value_type": "multi_select",
    "required": false,
    "description": "Framework di compliance applicabili",
    "allowed_values": ["SOC2", "GDPR", "HIPAA", "PCI-DSS", "ISO27001"]
  },
  {
    "property_name": "contains_pii",
    "value_type": "true_false",
    "required": true,
    "default_value": "false",
    "description": "Indica se il repository gestisce dati personali"
  },
  {
    "property_name": "documentation_url",
    "value_type": "url",
    "required": false,
    "description": "URL della documentazione del servizio"
  }
]
EOF

# Assegnare valori di custom properties a un repository specifico
gh api repos/{org}/{repo}/properties/values -X PATCH \
  --input - << 'EOF'
{
  "properties": [
    {"property_name": "service_tier", "value": "critical"},
    {"property_name": "owning_team", "value": "payments-team"},
    {"property_name": "compliance_scope", "value": ["SOC2", "PCI-DSS"]},
    {"property_name": "contains_pii", "value": "true"},
    {"property_name": "documentation_url", "value": "https://docs.internal.com/payments"}
  ]
}
EOF

# Leggere le custom properties di un repository
gh api repos/{org}/{repo}/properties/values --jq '
  .[] | "\(.property_name): \(.value)"'

# Listare tutti i repository con una specifica proprietà
gh api orgs/{org}/properties/values --jq '
  .[] | select(.properties[] | select(.property_name == "service_tier" and .value == "critical")) | .repository_full_name'
```

### Rulesets Basati su Custom Properties

L'integrazione tra custom properties e rulesets consente di applicare regole di governance condizionali basate sulla classificazione del repository, senza dover elencare singolarmente ogni repository:

```bash
# Ruleset che si applica solo ai repository "critical"
gh api orgs/{org}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Critical Service Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "repository_property": [
      {
        "name": "service_tier",
        "property_values": ["critical"],
        "source": "custom"
      }
    ],
    "ref_name": {
      "include": ["refs/heads/main", "refs/heads/release/**"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 3,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "ci/build"},
          {"context": "ci/test"},
          {"context": "ci/lint"},
          {"context": "security/sast"},
          {"context": "security/dast"},
          {"context": "compliance/audit"}
        ]
      }
    },
    {"type": "required_signatures"},
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {"type": "required_linear_history"}
  ]
}
EOF

# Ruleset meno restrittivo per repository "experimental"
gh api orgs/{org}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Experimental Repos - Minimal Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "repository_property": [
      {
        "name": "service_tier",
        "property_values": ["experimental"],
        "source": "custom"
      }
    ],
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": false
      }
    },
    {"type": "deletion"}
  ]
}
EOF
```

### Organization Custom Properties (Gennaio 2026 GA)

Le organization custom properties estendono il concetto ai livello enterprise, permettendo agli amministratori dell'enterprise di definire proprietà a livello di organizzazione (non solo di repository). Questo consente di classificare le organizzazioni per dipartimento, regione geografica, requisiti di compliance o qualsiasi altro criterio rilevante, e di applicare rulesets enterprise-wide basati su queste classificazioni.

```bash
# Esempio: Creare proprietà a livello enterprise per le organizzazioni
# (Richiede GitHub Enterprise Cloud)
gh api enterprises/{enterprise}/properties/schema -X PUT \
  --input - << 'EOF'
[
  {
    "property_name": "department",
    "value_type": "single_select",
    "required": true,
    "allowed_values": ["engineering", "data-science", "security", "platform"]
  },
  {
    "property_name": "region",
    "value_type": "single_select",
    "required": true,
    "allowed_values": ["eu-west", "us-east", "ap-southeast"]
  }
]
EOF
```

---

## Automazione della Governance con GitHub API

### Repository-as-Code con Terraform

La configurazione dei repository può essere gestita come codice usando il Terraform GitHub Provider, garantendo riproducibilità e audit trail:

```hcl
# Terraform configuration per un repository GitHub
terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = "my-org"
  # Token via GITHUB_TOKEN env var
}

resource "github_repository" "main_app" {
  name        = "main-application"
  description = "Applicazione principale dell'organizzazione"
  visibility  = "private"

  has_issues      = true
  has_projects    = true
  has_wiki        = false
  has_discussions  = true
  has_downloads   = false

  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = false
  allow_auto_merge       = true
  delete_branch_on_merge = true

  squash_merge_commit_title   = "PR_TITLE"
  squash_merge_commit_message = "PR_BODY"

  vulnerability_alerts                    = true
  security_and_analysis {
    secret_scanning {
      status = "enabled"
    }
    secret_scanning_push_protection {
      status = "enabled"
    }
  }

  template {
    owner      = "my-org"
    repository = "template-typescript"
  }
}

resource "github_branch_protection" "main" {
  repository_id = github_repository.main_app.node_id
  pattern       = "main"

  required_status_checks {
    strict   = true
    contexts = ["ci/build", "ci/test", "ci/lint", "security/codeql"]
  }

  required_pull_request_reviews {
    required_approving_review_count = 2
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = true
    require_last_push_approval      = true
  }

  enforce_admins         = true
  required_linear_history = true
  allows_force_pushes    = false
  allows_deletions       = false

  required_conversation_resolution = true
}

resource "github_repository_ruleset" "production" {
  name        = "Production Protection"
  repository  = github_repository.main_app.name
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["~DEFAULT_BRANCH", "refs/heads/release/**"]
      exclude = []
    }
  }

  rules {
    deletion         = true
    non_fast_forward = true

    pull_request {
      required_approving_review_count   = 2
      dismiss_stale_reviews_on_push     = true
      require_code_owner_review         = true
      require_last_push_approval        = true
      required_review_thread_resolution = true
    }
  }
}
```

### Script di Audit per Conformità dei Repository

```bash
#!/usr/bin/env bash
# Audit di conformità per tutti i repository di un'organizzazione

ORG="my-org"

echo "=== Repository Compliance Audit ==="
echo "Org: $ORG  |  Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

gh repo list "$ORG" --limit 500 --json name,visibility,defaultBranchRef \
  --jq '.[] | .name' | while read -r repo; do

  echo "--- $repo ---"

  # Verificare branch protection su main
  protection=$(gh api "repos/$ORG/$repo/branches/main/protection" 2>/dev/null)
  if [ $? -eq 0 ]; then
    reviews=$(echo "$protection" | jq -r '.required_pull_request_reviews.required_approving_review_count // 0')
    strict=$(echo "$protection" | jq -r '.required_status_checks.strict // false')
    enforce_admins=$(echo "$protection" | jq -r '.enforce_admins.enabled // false')
    echo "  Branch protection: YES  |  Reviews: $reviews  |  Strict: $strict  |  Enforce admins: $enforce_admins"
  else
    echo "  Branch protection: NO  [NON CONFORME]"
  fi

  # Verificare secret scanning
  settings=$(gh api "repos/$ORG/$repo" --jq '.security_and_analysis // empty' 2>/dev/null)
  secret_scanning=$(echo "$settings" | jq -r '.secret_scanning.status // "disabled"' 2>/dev/null)
  push_protection=$(echo "$settings" | jq -r '.secret_scanning_push_protection.status // "disabled"' 2>/dev/null)
  echo "  Secret scanning: $secret_scanning  |  Push protection: $push_protection"

  # Verificare CODEOWNERS
  codeowners=$(gh api "repos/$ORG/$repo/contents/.github/CODEOWNERS" 2>/dev/null)
  if [ $? -eq 0 ]; then
    echo "  CODEOWNERS: YES"
  else
    echo "  CODEOWNERS: NO  [RACCOMANDATO]"
  fi

  echo ""
done
```

---

## GitHub Environments e Deployment Protection

### Configurazione degli Environments

Gli environments in GitHub definiscono target di deployment con regole di protezione specifiche:

```bash
# Creare un environment
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

# Creare un environment di staging (meno restrittivo)
gh api repos/{owner}/{repo}/environments/staging -X PUT \
  --input - << 'EOF'
{
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
EOF

# Aggiungere una branch policy custom all'environment staging
gh api repos/{owner}/{repo}/environments/staging/deployment-branch-policies -X POST \
  -f name="release/*" -f type="branch"

# Listare gli environments
gh api repos/{owner}/{repo}/environments --jq '.environments[] | {name: .name, protection_rules: [.protection_rules[].type]}'
```

### Environment Secrets e Variables

```bash
# Aggiungere un secret all'environment (richiede encryption con la public key)
# Ottenere la public key dell'environment
gh api repos/{owner}/{repo}/environments/production/secrets/public-key

# Aggiungere una variabile (non cifrata) all'environment
gh api repos/{owner}/{repo}/environments/production/variables -X POST \
  -f name="DEPLOY_REGION" -f value="eu-west-1"

# Listare le variabili dell'environment
gh api repos/{owner}/{repo}/environments/production/variables --jq '.variables[] | {name: .name, value: .value}'
```

---

## Custom Deployment Protection Rules

### Architettura delle Custom Protection Rules

Le custom deployment protection rules, introdotte in public beta nel 2023 e progressivamente migliorate fino al 2025, consentono di integrare gate di approvazione automatizzati forniti da servizi di terze parti (come Datadog, Honeycomb, ServiceNow, PagerDuty) nel processo di deployment. Sono implementate tramite GitHub Apps e operano come middleware tra il workflow di deployment e il servizio esterno.

Il flusso operativo è il seguente:

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Workflow    │───▶│  GitHub      │───▶│  GitHub App  │───▶│  Servizio    │
│  step con   │    │  POST evento │    │  (Custom     │    │  Esterno     │
│  environment│    │  deployment_ │    │  Protection  │    │  (Datadog,   │
│             │    │  protection_ │    │  Rule)       │    │  Honeycomb)  │
│             │    │  rule        │    │              │    │              │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                              │                    │
                                              │◀───────────────────┘
                                              │  Approve/Reject
                                              ▼
                                       ┌──────────────┐
                                       │  Deployment  │
                                       │  procede o   │
                                       │  viene       │
                                       │  bloccato    │
                                       └──────────────┘
```

### Configurazione di una Custom Protection Rule

```bash
# 1. La GitHub App deve essere installata sul repository
# 2. Abilitare la custom protection rule sull'environment

# Listare le apps con deployment protection rule disponibili
gh api repos/{owner}/{repo}/environments/production/deployment_protection_rules \
  --jq '.custom_deployment_protection_rules[] | {app: .app.slug, id: .id, enabled: .enabled}'

# Abilitare una custom protection rule su un environment
gh api repos/{owner}/{repo}/environments/production/deployment_protection_rules -X POST \
  -F integration_id=12345

# Ogni environment può avere al massimo 6 custom protection rules simultanee
```

### Esempio: Workflow con Deployment Gate

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build && npm test

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    # Questo job si ferma qui finché:
    # 1. I reviewer manuali approvano
    # 2. Il wait_timer scade
    # 3. TUTTE le custom protection rules approvano
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          echo "Deploying to production..."
          # Il deploy procede solo se tutti i gate sono passati
```

### Casi d'Uso Comuni per Custom Protection Rules

| Servizio | Gate | Descrizione |
|---|---|---|
| **Datadog** | Monitors OK | Verifica che tutti i monitor Datadog siano in stato "OK" prima del deploy |
| **Honeycomb** | SLO compliance | Verifica che gli SLO siano rispettati prima di introdurre nuovo codice |
| **PagerDuty** | Nessun incidente attivo | Blocca deploy se ci sono incidenti P1/P2 in corso |
| **ServiceNow** | Change request approvato | Verifica che un change ticket sia stato approvato prima del deploy |
| **Jira** | Issue linkate resolved | Verifica che tutte le issue linkate alla release siano in stato "Done" |
| **Custom** | Canary analysis | Analisi automatica dei canary deploy prima del rollout completo |

### Creare una Custom Deployment Protection Rule (GitHub App)

Per implementare una custom protection rule personalizzata, è necessario creare una GitHub App che risponda all'evento `deployment_protection_rule`:

```bash
# La GitHub App riceve un webhook POST con payload:
# {
#   "action": "requested",
#   "environment": "production",
#   "deployment_callback_url": "https://api.github.com/...",
#   "deployment": { ... }
# }

# La App risponde con approve o reject:
# POST al deployment_callback_url
# Body: { "environment_name": "production", "state": "approved", "comment": "All checks passed" }
# Oppure: { "environment_name": "production", "state": "rejected", "comment": "SLO violation detected" }
```

---

## Repository Security — Configurazione Completa

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
      time: "09:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "automated"
    ignore:
      - dependency-name: "eslint"
        versions: ["9.x"]
    groups:
      dev-dependencies:
        patterns: ["@types/*", "eslint-*", "prettier"]
        update-types: ["minor", "patch"]
      production-dependencies:
        dependency-type: "production"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "ci"
      - "automated"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Secret Scanning e Push Protection

```bash
# Abilitare secret scanning
gh api repos/{owner}/{repo} -X PATCH \
  --input - << 'EOF'
{
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"}
  }
}
EOF

# Verificare gli alert di secret scanning
gh api repos/{owner}/{repo}/secret-scanning/alerts --jq '
  .[] | {number: .number, state: .state, secret_type: .secret_type, created_at: .created_at}'

# Custom patterns per secret scanning (organizzazione)
gh api orgs/{org}/secret-scanning/custom-patterns -X POST \
  --input - << 'EOF'
{
  "name": "Internal API Key",
  "pattern": "IKEY-[a-zA-Z0-9]{32}",
  "scope": "all"
}
EOF
```

### Code Scanning con CodeQL

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read

    strategy:
      matrix:
        language: ['javascript-typescript', 'python']

    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

---

## GitHub Apps per la Gestione dei Repository

### Perché Preferire le GitHub Apps ai Personal Access Token

Le GitHub Apps sono il meccanismo raccomandato da GitHub per l'automazione della gestione dei repository, in sostituzione dei Personal Access Token (PAT). Le ragioni principali sono:

| Aspetto | Personal Access Token (PAT) | GitHub App |
|---|---|---|
| **Legame** | Utente personale | Organizzazione/repository |
| **Permessi** | Scope ampi (repo, admin:org) | Granulari per risorsa |
| **Rate limit** | 5.000 req/h per utente | 5.000 req/h per installazione |
| **Scadenza token** | Configurabile, non auto-rotante | Token di installazione con scadenza breve (1h) |
| **Audit** | Azioni attribuite all'utente | Azioni attribuite alla App |
| **Revoca** | Rimuove accesso a tutto | Per-installazione |
| **Rischio** | Se l'utente lascia l'azienda, il token è orfano | Indipendente dagli utenti |

### Creare una GitHub App per Repository Management

```bash
# Creazione di una GitHub App via API (richiede un utente autenticato)
# Tipicamente si crea tramite UI: Settings → Developer settings → GitHub Apps → New

# Permessi minimi raccomandati per repository management:
# Repository permissions:
#   - Administration: Read & Write
#   - Contents: Read
#   - Metadata: Read (obbligatorio)
#   - Pull requests: Read & Write
#   - Workflows: Read & Write
#
# Organization permissions:
#   - Members: Read
#   - Administration: Read

# Dopo l'installazione, generare un token di installazione:
# 1. Creare un JWT dal private key della App
# 2. Ottenere l'installation_id

# Listare le installazioni della App
gh api app/installations --jq '.[] | {id: .id, account: .account.login, target_type: .target_type}'

# Creare un installation access token
gh api app/installations/{installation_id}/access_tokens -X POST \
  --input - << 'EOF'
{
  "repositories": ["my-repo"],
  "permissions": {
    "administration": "write",
    "contents": "read",
    "pull_requests": "write"
  }
}
EOF
# Il token restituito è valido per 1 ora
```

### Enterprise-Level GitHub Apps (Luglio 2025)

A partire da luglio 2025, le GitHub Apps supportano l'accesso a livello enterprise con nuove API per l'automazione delle installazioni. I nuovi permessi enterprise permettono di:

- **Enterprise organization installations**: Visualizzare, creare, modificare e rimuovere installazioni in ogni organizzazione dell'enterprise.
- **Enterprise organization installation repositories**: Modificare a quali repository un'installazione ha accesso, senza la possibilità di installare nuove app.

```bash
# Esempio: Installare automaticamente una GitHub App su tutte le organizzazioni dell'enterprise
# (Richiede il permesso "Enterprise organization installations: write")

# Listare le organizzazioni dell'enterprise
gh api enterprises/{enterprise}/organizations --jq '.[] | .login' | while read -r org; do
  echo "Installando app su $org..."
  gh api app/installations -X POST \
    -f target_type="Organization" \
    -f target_id="$(gh api orgs/$org --jq '.id')"
done
```

### Controllo delle Installazioni (Dicembre 2025 GA)

A partire da dicembre 2025 (GA), gli owner delle organizzazioni possono impedire agli admin dei repository di installare GitHub Apps autonomamente, garantendo che solo gli organization owner possano approvare le installazioni:

```bash
# Verificare la policy di installazione delle app
gh api orgs/{org} --jq '.members_can_install_apps'

# Questa impostazione si configura in:
# Organization Settings → Third-party access → GitHub Apps → Installation policy
# Opzioni: "Allow all members" | "Only organization owners"
```

### Automazione con GitHub App: Esempio Completo

```bash
#!/usr/bin/env bash
# Script che usa una GitHub App per applicare configurazioni standard
# a tutti i nuovi repository dell'organizzazione

# Prerequisiti:
# - GitHub App con permessi Administration: write, Contents: read
# - Installation token già ottenuto e salvato in $GH_APP_TOKEN

ORG="my-org"
export GH_TOKEN="$GH_APP_TOKEN"

# Ottenere i repository creati nell'ultima settimana senza branch protection
SINCE=$(date -u -d "7 days ago" +%Y-%m-%dT%H:%M:%SZ)

gh api "orgs/$ORG/repos?sort=created&direction=desc&per_page=50" \
  --jq ".[] | select(.created_at > \"$SINCE\") | .name" | while read -r repo; do

  echo "=== Configurando $repo ==="

  # Verificare se la branch protection esiste già
  if ! gh api "repos/$ORG/$repo/branches/main/protection" >/dev/null 2>&1; then
    echo "  Applicando branch protection su main..."
    gh api "repos/$ORG/$repo/branches/main/protection" -X PUT \
      --input - << 'PROT'
{
  "required_status_checks": {"strict": true, "contexts": []},
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
PROT
  fi

  # Abilitare secret scanning
  gh api "repos/$ORG/$repo" -X PATCH \
    --input - << 'SEC'
{
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"}
  }
}
SEC

  # Abilitare auto-delete dei branch
  gh repo edit "$ORG/$repo" --delete-branch-on-merge=true

  echo "  Configurazione completata."
done
```

---

## Inner Source e Repository con Visibilità Internal

### Il Concetto di Inner Source

L'inner source applica le pratiche dell'open source all'interno dei confini dell'organizzazione o dell'enterprise. GitHub supporta questo modello attraverso la visibilità "internal", disponibile per GitHub Enterprise Cloud e GitHub Enterprise Server.

Un repository con visibilità "internal" è visibile a tutti i membri dell'enterprise ma non al pubblico. Questo consente:

- **Riutilizzo del codice**: Qualsiasi team dell'enterprise può scoprire, leggere e forkare librerie interne.
- **Contribuzione cross-team**: Sviluppatori di team diversi possono inviare PR a repository di cui non sono maintainer diretti.
- **Trasparenza**: Visibilità completa del codice elimina i silos informativi tra i team.
- **Standard condivisi**: Le best practice si propagano organicamente attraverso la visibilità del codice.

### Configurazione della Visibilità Internal

```bash
# Creare un repository con visibilità internal
gh repo create my-org/shared-library --internal --clone

# Cambiare un repository privato a internal
gh api repos/{org}/{repo} -X PATCH -f visibility="internal"

# ATTENZIONE: il passaggio da privato a internal rende il repository
# visibile a TUTTI i membri dell'enterprise, non solo all'organizzazione.
# Verificare che non contenga secret o dati sensibili prima del cambio.
```

### Policy di Forking per Inner Source

La configurazione delle policy di forking è fondamentale per l'inner source. Per default, i fork di repository privati non sono permessi, e i fork di repository interni creano repository privati nell'account personale dell'utente. Queste impostazioni possono essere modificate:

```bash
# Abilitare il forking di repository privati/interni a livello di organizzazione
# Organization Settings → Member privileges → Repository forking

# Configurare la policy di forking a livello enterprise
# Enterprise Settings → Policies → Repository forking
# Opzioni:
# - Allow forking of private and internal repositories
# - Do not allow forking of private and internal repositories
# - Allow organization owners to decide

# Abilitare il fork nella stessa organizzazione
# (migliora l'inner source evitando fork in account personali)
gh api repos/{org}/{repo} -X PATCH -F allow_forking=true

# Verificare la policy di forking di un repository
gh api repos/{org}/{repo} --jq '{
  allow_forking: .allow_forking,
  visibility: .visibility,
  fork: .fork,
  forks_count: .forks_count
}'
```

### Best Practices per Inner Source

1. **CONTRIBUTING.md dettagliato**: Ogni repository interno dovrebbe avere istruzioni chiare per i contributor esterni al team.
2. **Issue template per contribuzioni esterne**: Creare un template "External Contribution" che guidi i contributor cross-team.
3. **CODEOWNERS con team dedicato**: Assegnare almeno un team come owner per garantire review tempestive delle PR esterne.
4. **Label "good first issue"**: Marcare issue accessibili per incoraggiare le prime contribuzioni.
5. **Documentazione API interna**: Documentare le interfacce pubbliche con esempi d'uso.
6. **Custom properties**: Usare proprietà come `innersource: true` per identificare i repository aperti alla contribuzione interna.

---

## Repository Policies a Livello Enterprise

### Panoramica delle Enterprise Policies

Le enterprise policies permettono agli amministratori dell'enterprise di imporre restrizioni a livello globale su tutte le organizzazioni e i repository, garantendo conformità senza dipendere dalla configurazione individuale di ogni organization owner.

### Categorie di Policy

#### Policy sulla Creazione dei Repository

```bash
# Configurazione a livello enterprise
# Enterprise Settings → Policies → Repositories

# Chi può creare repository:
# - All members: Tutti i membri possono creare repo (meno restrittivo)
# - Admin only: Solo gli admin delle organizzazioni possono creare repo
# - Disabled: Nessuno può creare repo (gestione centralizzata)
# - Let organization owners decide (delega)

# Chi può creare repository pubblici vs privati vs interni:
# Configurabile separatamente per ogni tipo di visibilità
```

#### Policy sulla Cancellazione e Trasferimento

```bash
# Limitare chi può cancellare repository
# Enterprise Settings → Policies → Repositories → Repository deletion

# Opzioni:
# - Members with admin permissions (default)
# - Organization owners only
# - Enterprise owners only (più restrittivo)

# Limitare chi può trasferire repository
# Enterprise Settings → Policies → Repositories → Repository transfer

# Il trasferimento fuori dall'enterprise può essere bloccato completamente
```

#### Policy sulla Visibilità

```bash
# Impedire il cambio di visibilità dei repository
# Enterprise Settings → Policies → Repositories → Repository visibility change

# Questa policy è critica per la sicurezza: impedisce che un admin di organizzazione
# cambi accidentalmente un repository privato in pubblico, esponendo codice proprietario.

# Verificare la policy corrente
gh api enterprises/{enterprise}/settings --jq '.members_can_change_repository_visibility'
```

#### Policy sui Nomi dei Repository

```bash
# Le repository policies possono anche imporre convenzioni di naming
# tramite rulesets enterprise-level con condizioni su repository_name

# Esempio: Bloccare repository con nomi che non seguono la convenzione
gh api enterprises/{enterprise}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Repository Naming Convention",
  "enforcement": "active",
  "conditions": {
    "repository_name": {
      "include": ["*"],
      "exclude": []
    }
  }
}
EOF
```

### Audit Log per Repository Management

L'audit log dell'enterprise registra tutte le azioni di gestione dei repository, fornendo un trail di audit completo per la conformità:

```bash
# Cercare eventi di repository management nell'audit log
gh api orgs/{org}/audit-log?phrase=action:repo \
  --jq '.[] | {action: .action, actor: .actor, repo: .repo, created_at: .created_at}' \
  | head -20

# Filtrare per azioni specifiche
# action:repo.create     — Creazione repository
# action:repo.destroy    — Cancellazione repository
# action:repo.transfer   — Trasferimento repository
# action:repo.archived   — Archiviazione repository
# action:repo.visibility — Cambio visibilità
# action:repo.access     — Cambio permessi
# action:protected_branch.create  — Creazione branch protection
# action:protected_branch.destroy — Rimozione branch protection

# Esportare l'audit log per compliance
gh api orgs/{org}/audit-log?phrase=action:repo \
  --paginate --jq '.[] | [.created_at, .action, .actor, .repo] | @csv' > audit-repo-actions.csv
```

---

## Archiviazione, Trasferimento e Cancellazione dei Repository

### Archiviazione

L'archiviazione rende un repository completamente read-only: nessun push, nessuna PR, nessuna issue, nessun commento. È la scelta preferita rispetto alla cancellazione quando il codice potrebbe avere valore storico o quando altri progetti dipendono da esso.

```bash
# Archiviare un repository
gh repo archive my-org/legacy-project --yes

# Verificare lo stato di archiviazione
gh api repos/{owner}/{repo} --jq '.archived'

# Dis-archiviare (richiede admin)
gh repo unarchive my-org/legacy-project --yes

# Archiviare in massa repository inattivi
INACTIVITY_THRESHOLD=$(date -u -d "18 months ago" +%Y-%m-%dT%H:%M:%SZ)
gh repo list my-org --limit 500 --json name,pushedAt --jq "
  .[] | select(.pushedAt < \"$INACTIVITY_THRESHOLD\") | .name
" | while read -r repo; do
  echo "Archiviando $repo (ultimo push prima di $INACTIVITY_THRESHOLD)..."
  gh repo archive "my-org/$repo" --yes
done
```

#### Cosa Preserva l'Archiviazione

| Elemento | Preservato | Accessibile |
|---|---|---|
| Codice sorgente | Si | Read-only |
| Cronologia commit | Si | Read-only |
| Issues e PR | Si | Read-only (no nuove) |
| Wiki | Si | Read-only |
| Stars e watchers | Si | Si |
| Forks esistenti | Si | Operativi (indipendenti) |
| GitHub Pages | Si | Pubblicato |
| Packages | Si | Download consentito |
| Actions | No | Workflow non eseguibili |
| Webhooks | No | Non inviati |

### Trasferimento

Il trasferimento sposta un repository da un owner (utente o organizzazione) a un altro. Preserva il codice, le issues, le PR, le stars e i watchers. Non preserva le branch protection rules, gli environment secrets, i deploy keys e le installazioni di GitHub App.

```bash
# Trasferire un repository a un'altra organizzazione
gh api repos/{owner}/{repo}/transfer -X POST \
  -f new_owner="target-org"

# Trasferire con team specificati (opzionale)
gh api repos/{owner}/{repo}/transfer -X POST \
  --input - << 'EOF'
{
  "new_owner": "target-org",
  "team_ids": [12345, 67890]
}
EOF

# IMPORTANTE: Dopo il trasferimento
# 1. GitHub crea un redirect automatico dal vecchio URL al nuovo
# 2. Il redirect funziona per clone, push, pull e pagine web
# 3. Il redirect può essere eliminato se un nuovo repository viene creato
#    con lo stesso nome nello stesso namespace

# Checklist pre-trasferimento:
# □ Esportare branch protection rules
# □ Esportare rulesets
# □ Documentare environment secrets (i valori non sono leggibili via API)
# □ Documentare deploy keys
# □ Notificare i collaboratori
# □ Verificare che le GitHub App necessarie siano installate nella org target
# □ Aggiornare i riferimenti nei workflow CI/CD di altri repository
```

### Cancellazione

La cancellazione rimuove definitivamente un repository. GitHub mantiene i repository cancellati per 90 giorni, durante i quali è possibile il ripristino. Dopo i 90 giorni, la cancellazione è irreversibile.

```bash
# Cancellare un repository (richiede admin)
gh repo delete my-org/obsolete-project --yes

# ATTENZIONE: Questa operazione:
# - Rimuove tutto il codice, issues, PR, wiki, packages, releases
# - Rimuove le GitHub Pages
# - Rimuove i webhook e le notifiche
# - Invalida i link condivisi
# - I fork rimangono operativi ma perdono il collegamento upstream

# Ripristinare un repository cancellato (entro 90 giorni)
# Disponibile solo via UI: Settings → Deleted repositories → Restore
# Oppure via API:
gh api repos/{owner}/{repo}/restore -X PATCH

# Verificare i repository cancellati di recente
gh api orgs/{org}/repos?type=deleted --jq '.[] | {name: .name, deleted_at: .deleted_at}'
```

### Strategia di Fine Vita Raccomandata

```
1. COMUNICARE: Aprire una issue "Repository End of Life" con timeline
2. DEPRECARE: Aggiungere un banner di deprecazione nel README
3. ARCHIVARE: Dopo il periodo di avviso, archiviare il repository
4. MANTENERE: Tenere il repository archiviato per almeno 12 mesi
5. CANCELLARE: Solo se non ci sono fork attivi o dipendenze esterne
```

---

## Backup e Disaster Recovery dei Repository

### Strategia di Backup

Nonostante GitHub offra alta disponibilità e ridondanza, un backup indipendente dei repository critici è essenziale per la conformità e la business continuity. I rischi da mitigare includono: cancellazione accidentale, compromissione dell'account, force push distruttivi, guasti del servizio GitHub, e requisiti regolamentari di data retention.

### Backup Completo con Script

```bash
#!/usr/bin/env bash
# Script di backup completo per repository GitHub
# Include: codice, wiki, issues, PR, releases

set -euo pipefail

ORG="my-org"
BACKUP_DIR="/backup/github/$(date -u +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

echo "=== GitHub Backup — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

gh repo list "$ORG" --limit 500 --json name,visibility --jq '.[].name' | while read -r repo; do
  REPO_DIR="$BACKUP_DIR/$repo"
  mkdir -p "$REPO_DIR"

  echo "--- Backup di $repo ---"

  # 1. Clone completo del repository (tutti i branch e tag)
  git clone --mirror "https://github.com/$ORG/$repo.git" "$REPO_DIR/repo.git" 2>/dev/null || true

  # 2. Clone del wiki (se esiste)
  git clone --mirror "https://github.com/$ORG/$repo.wiki.git" "$REPO_DIR/wiki.git" 2>/dev/null || true

  # 3. Esportare issues
  gh api "repos/$ORG/$repo/issues?state=all&per_page=100" --paginate \
    > "$REPO_DIR/issues.json" 2>/dev/null || true

  # 4. Esportare pull requests
  gh api "repos/$ORG/$repo/pulls?state=all&per_page=100" --paginate \
    > "$REPO_DIR/pulls.json" 2>/dev/null || true

  # 5. Esportare releases
  gh api "repos/$ORG/$repo/releases?per_page=100" --paginate \
    > "$REPO_DIR/releases.json" 2>/dev/null || true

  # 6. Esportare branch protection
  gh api "repos/$ORG/$repo/branches/main/protection" \
    > "$REPO_DIR/branch-protection.json" 2>/dev/null || true

  # 7. Esportare rulesets
  gh api "repos/$ORG/$repo/rulesets" \
    > "$REPO_DIR/rulesets.json" 2>/dev/null || true

  # 8. Esportare environments
  gh api "repos/$ORG/$repo/environments" \
    > "$REPO_DIR/environments.json" 2>/dev/null || true

  echo "  Backup completato in $REPO_DIR"
done

# Comprimere il backup
echo "Comprimendo il backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
echo "Backup salvato in $BACKUP_DIR.tar.gz"

# Calcolare e salvare il checksum
sha256sum "$BACKUP_DIR.tar.gz" > "$BACKUP_DIR.tar.gz.sha256"
echo "Checksum: $(cat $BACKUP_DIR.tar.gz.sha256)"
```

### Automazione del Backup con GitHub Actions

```yaml
# .github/workflows/backup.yml
name: Repository Backup

on:
  schedule:
    - cron: '0 2 * * 0'  # Ogni domenica alle 02:00 UTC
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Clone repository (mirror)
        run: |
          git clone --mirror https://x-access-token:${{ secrets.BACKUP_TOKEN }}@github.com/${{ github.repository }}.git repo.git

      - name: Create backup archive
        run: |
          tar -czf "backup-$(date -u +%Y%m%d).tar.gz" repo.git

      - name: Upload to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 cp "backup-$(date -u +%Y%m%d).tar.gz" \
            "s3://github-backups/${{ github.repository }}/$(date -u +%Y%m%d).tar.gz"
```

### Recovery da Backup

```bash
# Ripristinare un repository da un backup mirror
# 1. Creare un nuovo repository vuoto
gh repo create my-org/restored-project --private

# 2. Pushare dal backup mirror
cd /backup/github/2026-05-24/my-project/repo.git
git push --mirror https://github.com/my-org/restored-project.git

# 3. Ripristinare la branch protection dal backup
cat branch-protection.json | gh api repos/my-org/restored-project/branches/main/protection \
  -X PUT --input -

# 4. Ripristinare i rulesets
cat rulesets.json | jq '.[]' | while read -r ruleset; do
  echo "$ruleset" | gh api repos/my-org/restored-project/rulesets -X POST --input -
done
```

### Piano di Disaster Recovery

| Scenario | RTO | RPO | Procedura |
|---|---|---|---|
| Cancellazione accidentale singolo repo | < 1h | 0 (entro 90 giorni) | Restore via UI/API |
| Force push distruttivo | < 30min | 0 (reflog) | `git reflog` + push correttivo |
| Compromissione account admin | < 4h | Ultimo backup | Rotazione credenziali + restore |
| Outage GitHub prolungato (> 4h) | Dipende da SLA | Ultimo backup | Clone da backup, mirror alternativo |
| Cancellazione organizzazione | < 24h | Ultimo backup | Contattare GitHub Support + restore da backup |

---

## Topics, Descrizione e Metadata

### Topics

I topics sono etichette che rendono il repository più facilmente trovabile su GitHub.

```bash
# Impostare i topics
gh repo edit --add-topic "typescript,react,monorepo,ci-cd"

# Rimuovere un topic
gh repo edit --remove-topic "old-topic"

# Visualizzare i topics
gh repo view --json repositoryTopics
```

### Descrizione e Homepage

```bash
# Impostare la descrizione
gh repo edit --description "Framework TypeScript per applicazioni enterprise"

# Impostare l'homepage
gh repo edit --homepage "https://docs.myproject.com"
```

### Social Preview

L'immagine social preview viene mostrata quando il link al repository è condiviso sui social media. Si configura in Settings > General > Social preview. Dimensione consigliata: 1280x640 pixel.

---

## Autolink References — Collegamento a Risorse Esterne

### Cosa Sono gli Autolink References

Gli autolink references sono una funzionalita di GitHub che consente di creare collegamenti automatici tra riferimenti testuali nei commit, nelle issue, nelle PR e nelle release e risorse esterne come ticket Jira, issue Zendesk, story Shortcut o qualsiasi sistema di project management o bug tracking con URL prevedibili. Quando un collaboratore scrive un riferimento come `JIRA-1234` in un messaggio di commit o nel corpo di una PR, GitHub lo trasforma automaticamente in un link cliccabile verso il sistema esterno configurato.

Questa funzionalita e disponibile per tutti i tipi di repository e si configura in Settings > Integrations > Autolink references. Solo gli utenti con permessi di amministrazione possono creare o modificare le configurazioni degli autolink.

### Configurazione tramite UI e API

#### Configurazione via UI

Per aggiungere un autolink reference tramite la UI di GitHub:

1. Navigare su Settings del repository
2. Nella sezione "Integrations" della sidebar, selezionare "Autolink references"
3. Fare clic su "Add autolink reference"
4. Selezionare il formato dell'identificatore: **Numeric** (solo numeri, es. `JIRA-123`) o **Alphanumeric** (numeri e lettere, es. `TICKET-abc123`)
5. Inserire il prefisso di riferimento (es. `JIRA-`, `ZD-`, `STORY-`)
6. Inserire l'URL target usando il placeholder `<num>` per l'identificatore

#### Configurazione via API

```bash
# Creare un autolink reference per Jira
gh api repos/{owner}/{repo}/autolinks -X POST \
  -f key_prefix="JIRA-" \
  -f url_template="https://my-org.atlassian.net/browse/JIRA-<num>" \
  -F is_alphanumeric=false

# Creare un autolink per Zendesk
gh api repos/{owner}/{repo}/autolinks -X POST \
  -f key_prefix="ZD-" \
  -f url_template="https://my-org.zendesk.com/agent/tickets/<num>" \
  -F is_alphanumeric=false

# Creare un autolink alfanumerico per un sistema interno
gh api repos/{owner}/{repo}/autolinks -X POST \
  -f key_prefix="INCIDENT-" \
  -f url_template="https://incidents.internal.com/view/<num>" \
  -F is_alphanumeric=true

# Listare tutti gli autolink configurati
gh api repos/{owner}/{repo}/autolinks --jq '
  .[] | {id: .id, prefix: .key_prefix, url: .url_template, alphanumeric: .is_alphanumeric}'

# Eliminare un autolink
gh api repos/{owner}/{repo}/autolinks/{autolink_id} -X DELETE
```

### Esempi di Integrazione Comuni

| Sistema Esterno | Prefisso | URL Template | Formato |
|---|---|---|---|
| Jira | `JIRA-` | `https://org.atlassian.net/browse/JIRA-<num>` | Numeric |
| Zendesk | `ZD-` | `https://org.zendesk.com/agent/tickets/<num>` | Numeric |
| Linear | `LIN-` | `https://linear.app/org/issue/LIN-<num>` | Alphanumeric |
| Shortcut | `SC-` | `https://app.shortcut.com/org/story/<num>` | Numeric |
| ServiceNow | `INC` | `https://org.service-now.com/incident.do?sys_id=<num>` | Alphanumeric |
| PagerDuty | `PD-` | `https://org.pagerduty.com/incidents/<num>` | Alphanumeric |

### Regole e Limitazioni

- **Prefissi univoci**: Due autolink non possono avere prefissi che si sovrappongono. Ad esempio, non e possibile avere contemporaneamente `TICKET` e `TICK` come prefissi, perche la stringa `TICKET123` matcherebbe entrambi.
- **Solo admin**: La creazione e modifica degli autolink e riservata agli utenti con permessi di amministratore sul repository.
- **Nessun supporto a livello organizzazione**: Al momento della stesura (maggio 2026), GitHub non supporta la configurazione degli autolink a livello di organizzazione. Ogni repository deve essere configurato individualmente, il che puo richiedere automazione via API per organizzazioni con molti repository.
- **Contesto di rendering**: Gli autolink funzionano nei commit message, nei corpi delle issue e PR, nelle release notes e nei commenti. Non funzionano nel codice sorgente o nei file README.

### Automazione degli Autolink per l'Intera Organizzazione

Per configurare gli stessi autolink su tutti i repository di un'organizzazione, e necessario uno script che iteri sui repository e applichi la configurazione:

```bash
#!/usr/bin/env bash
# Applicare autolink references standard a tutti i repository di un'organizzazione

ORG="my-org"

# Definire gli autolink standard
declare -A AUTOLINKS
AUTOLINKS["JIRA-"]="https://$ORG.atlassian.net/browse/JIRA-<num>"
AUTOLINKS["ZD-"]="https://$ORG.zendesk.com/agent/tickets/<num>"

gh repo list "$ORG" --limit 500 --json name --jq '.[].name' | while read -r repo; do
  for prefix in "${!AUTOLINKS[@]}"; do
    url="${AUTOLINKS[$prefix]}"

    # Verificare se l'autolink esiste gia
    existing=$(gh api "repos/$ORG/$repo/autolinks" --jq \
      ".[] | select(.key_prefix == \"$prefix\") | .id" 2>/dev/null)

    if [ -z "$existing" ]; then
      echo "Aggiungendo $prefix a $repo..."
      gh api "repos/$ORG/$repo/autolinks" -X POST \
        -f key_prefix="$prefix" \
        -f url_template="$url" \
        -F is_alphanumeric=false 2>/dev/null || true
    else
      echo "Autolink $prefix gia presente su $repo (id: $existing)"
    fi
  done
done
```

L'integrazione degli autolink con i sistemi di issue tracking e project management esterni migliora significativamente la tracciabilita tra il codice e le richieste di business, facilitando audit, code review e root cause analysis.

---

## Security Policy: SECURITY.md

### Struttura del File

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.x.x  | :white_check_mark: |
| 2.x.x  | :white_check_mark: |
| 1.x.x  | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security
vulnerability, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email security@myproject.com with details
3. Or use GitHub's private vulnerability reporting feature

### What to Include

- Type of vulnerability (XSS, SQL injection, authentication bypass, etc.)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Development**: Within 2 weeks for critical issues
- **Public Disclosure**: 90 days after report (coordinated disclosure)

### Recognition

We maintain a security hall of fame for responsible disclosures.
Reporters will be credited in the security advisory (unless they
prefer anonymity).

## Security Best Practices

When contributing to this project:

- Never commit secrets, API keys, or credentials
- Use parameterized queries for database access
- Validate and sanitize all user input
- Follow the principle of least privilege
- Keep dependencies up to date
```

### Private Vulnerability Reporting

GitHub supporta il reporting privato delle vulnerabilità direttamente nell'interfaccia:

```bash
# Abilitare il private vulnerability reporting
gh api repos/{owner}/{repo} -X PATCH \
  -F security_and_analysis[secret_scanning_push_protection][status]="enabled"
```

---

## README Best Practices

### Struttura di un README Efficace

```markdown
# Project Name

[![CI](https://github.com/org/repo/actions/workflows/ci.yml/badge.svg)](...)
[![Coverage](https://codecov.io/gh/org/repo/branch/main/graph/badge.svg)](...)
[![npm version](https://badge.fury.io/js/package-name.svg)](...)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](...)

> One-line description of what this project does and why it matters.

## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Features
- Feature 1: Brief description
- Feature 2: Brief description
- Feature 3: Brief description

## Quick Start

```bash
npm install my-package
```

```javascript
import { MyClass } from 'my-package';
const instance = new MyClass({ option: 'value' });
```

## Installation

### Prerequisites
- Node.js >= 18
- npm >= 9

### Steps
```bash
git clone https://github.com/org/repo.git
cd repo
npm install
npm run build
```

## Usage
[Detailed usage examples with code]

## API Reference
[Auto-generated or manually curated API documentation]

## Configuration
[Configuration options with descriptions and defaults]

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
This project is licensed under the MIT License - see [LICENSE](LICENSE).
```

### Regole per un README Efficace

1. **Prima impressione**: Il README è la prima cosa che i visitatori vedono. Deve comunicare immediatamente cosa fa il progetto e perché è utile.
2. **Quick start**: Permettere agli utenti di iniziare in meno di 5 minuti.
3. **Badges**: Mostrare lo stato della CI, la copertura dei test, la versione e la licenza.
4. **Esempi reali**: Includere codice di esempio funzionante, non pseudocodice.
5. **Aggiornamento**: Mantenere il README sincronizzato con il codice. Un README obsoleto è peggio di nessun README.

---

## Selezione della Licenza

### Licenze Comuni

| Licenza | Permissiva | Copyleft | Uso Commerciale | Patent Grant |
|---------|-----------|----------|-----------------|--------------|
| MIT | Sì | No | Sì | No |
| Apache 2.0 | Sì | No | Sì | Sì |
| GPL 3.0 | No | Forte | Sì | Sì |
| LGPL 3.0 | Parziale | Debole | Sì | Sì |
| BSD 2/3 | Sì | No | Sì | No |
| MPL 2.0 | Parziale | Per-file | Sì | Sì |
| AGPL 3.0 | No | Forte (network) | Sì | Sì |
| Unlicense | Sì | No | Sì | No |

### Guida alla Scelta

- **Librerie/SDK**: MIT o Apache 2.0 (massima adozione)
- **Progetti con patent concerns**: Apache 2.0 (include patent grant)
- **Software che deve restare open source**: GPL 3.0
- **Librerie usate in software proprietario**: LGPL 3.0
- **SaaS che deve restare open source**: AGPL 3.0
- **Pubblico dominio**: Unlicense o CC0

```bash
# Aggiungere una licenza durante la creazione del repository
gh repo create my-project --license MIT

# Aggiungere una licenza a un repository esistente
# Usare il wizard GitHub: Add file > Create new file > LICENSE
# GitHub offre un template selector
```

---

## Best Practices

### Configurazione Iniziale del Repository

1. **Branch protection dal giorno uno**: Configurare le regole di protezione per `main` immediatamente dopo la creazione del repository, anche per team di una persona.

2. **CODEOWNERS definiti**: Stabilire la proprietà del codice fin dall'inizio. Questo diventa progressivamente più difficile man mano che il progetto cresce.

3. **Template di Issue e PR**: Configurare i template per standardizzare le segnalazioni e le richieste di modifica.

4. **CI/CD integrata**: Collegare i workflow di GitHub Actions e configurarli come required status checks.

5. **Documentazione minimale**: README, CONTRIBUTING, SECURITY e LICENSE devono essere presenti dal primo commit.

### Gestione Continua

1. **Review periodica delle regole**: Rivedere le branch protection rules e i rulesets trimestralmente per adattarli all'evoluzione del team.

2. **Audit degli accessi**: Verificare regolarmente chi ha accesso al repository e con quali permessi.

3. **Pulizia dei branch**: Abilitare l'auto-delete dei branch dopo il merge e pulire periodicamente i branch stale.

4. **Monitorare le metriche**: Usare GitHub Insights per monitorare la frequenza dei commit, le PR e le issue.

5. **Vulnerability alerts attivi**: Abilitare Dependabot alerts e secret scanning su tutti i repository, inclusi quelli privati.

6. **Tag protection**: Proteggere i tag di release con rulesets per impedire la cancellazione o sovrascrittura accidentale.

7. **Backup dei repository**: Implementare un backup periodico dei repository critici, inclusi issues, PR e wiki, usando `gh repo clone` o tool di terze parti come `github-backup`.

### Organizzazione dei Repository in Scala

```bash
# Script per verificare la conformità di tutti i repository di un'organizzazione
ORG="my-org"

echo "Repository senza branch protection su main:"
gh repo list "$ORG" --limit 500 --json name --jq '.[].name' | while read -r repo; do
  protection=$(gh api "repos/$ORG/$repo/branches/main/protection" 2>/dev/null)
  if [ $? -ne 0 ]; then
    echo "  - $ORG/$repo"
  fi
done

echo ""
echo "Repository senza CODEOWNERS:"
gh repo list "$ORG" --limit 500 --json name --jq '.[].name' | while read -r repo; do
  codeowners=$(gh api "repos/$ORG/$repo/contents/.github/CODEOWNERS" 2>/dev/null)
  if [ $? -ne 0 ]; then
    echo "  - $ORG/$repo"
  fi
done

echo ""
echo "Repository con secret scanning disabilitato:"
gh repo list "$ORG" --limit 500 --json name,securityAndAnalysis --jq '
  .[] | select(.securityAndAnalysis.secretScanning.status != "enabled") | .name' 2>/dev/null
```

---

## Convenzioni di Naming per i Repository

### Importanza di una Convenzione di Naming

In organizzazioni con decine o centinaia di repository, l'assenza di una convenzione di naming coerente genera confusione, rallenta l'onboarding dei nuovi sviluppatori e rende difficile la ricerca e la classificazione dei progetti. Una convenzione ben definita consente ai team di identificare immediatamente lo scopo, il tipo e il dominio di un repository dal suo nome, senza dover aprire il README.

Le convenzioni di naming dovrebbero essere documentate nel CONTRIBUTING.md dell'organizzazione o in un repository dedicato alla governance (ad esempio `my-org/engineering-standards`) e applicate tramite automazione.

### Regole Fondamentali

| Regola | Esempio Corretto | Esempio Errato | Motivazione |
|---|---|---|---|
| Solo caratteri minuscoli | `payment-service` | `Payment-Service` | Evita ambiguita su filesystem case-sensitive/insensitive |
| Separazione con trattini | `user-auth-api` | `user_auth_api` | Il trattino e la convenzione standard di GitHub |
| Nessun carattere speciale | `data-pipeline` | `data.pipeline!` | Compatibilita con URL, CLI e script |
| Nessun numero di versione | `billing-service` | `billing-service-v2` | Le versioni si gestiscono con tag e release |
| Nomi descrittivi e concisi | `invoice-generator` | `ig` oppure `the-new-invoice-generator-project-rewrite` | Chiarezza senza eccessiva verbosita |

### Pattern di Naming Strutturato

Per organizzazioni di grandi dimensioni, e consigliabile adottare un pattern strutturato che codifichi informazioni chiave nel nome del repository:

```
{progetto}-{tipo}-{servizio}-{variante}
```

#### Componenti del Pattern

| Componente | Descrizione | Valori Esempio |
|---|---|---|
| `{progetto}` | Nome del progetto o dominio di business | `payments`, `crm`, `platform` |
| `{tipo}` | Tipo di artefatto | `api`, `web`, `lib`, `cli`, `infra`, `docs`, `mobile` |
| `{servizio}` | Nome specifico del servizio o componente | `gateway`, `auth`, `notifications` |
| `{variante}` | Variante opzionale (frontend framework, language) | `react`, `go`, `terraform` |

#### Esempi Pratici

```
# Microservizi
payments-api-gateway
payments-api-processor
payments-lib-sdk-node

# Frontend
crm-web-dashboard
crm-mobile-app-react-native

# Infrastruttura
platform-infra-terraform
platform-infra-kubernetes

# Librerie condivise
shared-lib-auth
shared-lib-logging

# Documentazione
platform-docs-engineering
platform-docs-runbooks

# Tool e CLI
platform-cli-deploy
devtools-cli-scaffold
```

### Naming per Tipologie Speciali

| Tipologia | Convenzione | Esempio |
|---|---|---|
| Template repository | `template-{stack}` | `template-typescript-api`, `template-python-fastapi` |
| Repository di configurazione | `config-{scope}` | `config-eslint`, `config-terraform-modules` |
| GitHub Actions custom | `action-{funzione}` | `action-deploy-ecs`, `action-notify-slack` |
| Fork per contribuzione | Mantenere il nome originale | `forked-repo-name` (automatico da GitHub) |
| Repository di sperimentazione | `sandbox-{descrizione}` o `spike-{descrizione}` | `sandbox-graphql-federation` |
| Meta-repository (governance) | `.github` oppure `engineering-standards` | `.github` (repository speciale dell'organizzazione) |

### Enforcement Automatizzato delle Convenzioni di Naming

L'enforcement delle convenzioni puo essere implementato a diversi livelli:

#### Livello 1 — Documentazione e Review Manuale

Il livello piu semplice consiste nel documentare le convenzioni e verificarle durante la review delle richieste di creazione repository. Questo approccio e sufficiente per organizzazioni piccole (meno di 20 repository).

#### Livello 2 — Webhook di Validazione

Per organizzazioni di medie dimensioni, un webhook sull'evento `repository.created` puo verificare automaticamente che il nome del nuovo repository rispetti la convenzione e notificare il creatore o un admin in caso di violazione:

```bash
# Esempio di logica di validazione (estratto da un webhook handler)
# Il webhook riceve l'evento "repository.created" e verifica il naming

REPO_NAME="$1"
VALID_PATTERN='^[a-z][a-z0-9]*(-[a-z0-9]+)*$'

if [[ ! "$REPO_NAME" =~ $VALID_PATTERN ]]; then
  echo "VIOLAZIONE: Il repository '$REPO_NAME' non rispetta la convenzione di naming."
  echo "Il nome deve essere composto solo da caratteri minuscoli, numeri e trattini."
  # Inviare notifica al creatore e all'admin
fi

# Verificare il pattern strutturato (opzionale, per organizzazioni con regole piu rigide)
STRUCTURED_PATTERN='^[a-z]+-[a-z]+-[a-z]+(-[a-z]+)?$'
if [[ ! "$REPO_NAME" =~ $STRUCTURED_PATTERN ]]; then
  echo "WARNING: Il nome '$REPO_NAME' non segue il pattern {progetto}-{tipo}-{servizio}."
fi
```

#### Livello 3 — Rulesets Enterprise con Condizioni sui Nomi

A livello enterprise, i rulesets possono essere configurati con condizioni `repository_name` che applicano regole differenziate in base al prefisso del nome del repository. Questo non impedisce la creazione di repository con nomi non conformi, ma permette di applicare automaticamente le regole di governance corrette ai repository che seguono la convenzione:

```bash
# Ruleset che si applica solo ai repository di produzione (prefisso corretto)
gh api orgs/{org}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Production Naming Convention Enforcement",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "repository_name": {
      "include": ["*-api-*", "*-web-*", "*-lib-*"],
      "exclude": ["sandbox-*", "spike-*", "template-*"]
    },
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 2,
        "require_code_owner_review": true
      }
    },
    {"type": "deletion"},
    {"type": "non_fast_forward"}
  ]
}
EOF
```

### Anti-Pattern di Naming da Evitare

| Anti-Pattern | Problema | Alternativa |
|---|---|---|
| `my-project` / `test-repo` | Non descrittivo, impossibile da trovare | Usare nomi che descrivono lo scopo |
| `new-api` / `old-api` | Relativo e temporaneo | Usare il dominio funzionale, non l'eta |
| `johns-service` | Legato a una persona, non al dominio | Usare il team o il dominio di business |
| `v2-rewrite` | Versione nel nome | Usare branch o tag per le versioni |
| `ProjectNameHere` | CamelCase non convenzionale su GitHub | Convertire in `project-name-here` |
| `repo1`, `repo2`, `repo3` | Nessun significato semantico | Usare nomi che riflettono la funzione |

Una convenzione di naming ben applicata riduce il carico cognitivo durante la navigazione dell'organizzazione, migliora la scopribilita dei repository tramite ricerca e facilita l'automazione delle policy basate su pattern di nome.

---

## Troubleshooting

### Branch Protection Blocca il Merge

```bash
# Verificare quali status checks sono falliti
gh pr checks <pr-number>

# Verificare le regole di protezione
gh api repos/{owner}/{repo}/branches/main/protection

# Se un admin deve bypassare
# Settings > Branches > Uncheck "Include administrators"
```

### CODEOWNERS Non Funziona

```bash
# Verificare errori di sintassi
gh api repos/{owner}/{repo}/codeowners/errors

# Cause comuni:
# 1. Il file non è in .github/, root, o docs/
# 2. "Require review from Code Owners" non è abilitato
# 3. I team/utenti referenziati non hanno accesso al repository
# 4. Pattern di glob errato
```

### Template Repository Non Visibile

```bash
# Verificare che il repository sia marcato come template
gh api repos/{owner}/{repo} --jq '.is_template'

# Se false, attivarlo
gh api repos/{owner}/{repo} -X PATCH -F is_template=true
```

### Status Check Mancante — PR Non Mergiabile

**Sintomi**: Una PR non può essere mergiata perché un required status check non compare. Il check non si avvia o risulta "Expected".

**Causa**: Il workflow che produce il check non è stato triggerato (filtri `on:` non corrispondono), il nome del check è diverso da quello configurato nella branch protection, oppure il workflow ha un errore di sintassi.

**Soluzione**:

```bash
# Verificare i check attesi vs quelli presenti
gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks --jq '.contexts'

# Verificare i check sulla PR
gh pr checks <pr-number>

# Verificare che il nome del job corrisponda al context richiesto
# Il context di un check è: "workflow-name / job-name" per Actions
# Oppure il nome del check esterno per tool di terze parti

# Rieseguire manualmente un workflow
gh workflow run ci.yml --ref <branch-name>

# Se il check viene da un'app esterna, verificare la configurazione
gh api repos/{owner}/{repo}/check-runs --jq '.check_runs[] | {name: .name, status: .status, conclusion: .conclusion}'
```

### Ruleset Non Si Applica Come Previsto

**Sintomi**: Un ruleset configurato non blocca le operazioni che dovrebbe bloccare (push diretti, merge senza review) o blocca operazioni che non dovrebbe bloccare.

**Causa**: Il pattern dei branch nel ruleset non corrisponde al branch target, l'enforcement è in modalità "evaluate" (dry-run) anziché "active", oppure l'utente ha un bypass configurato.

**Soluzione**:

```bash
# Listare i rulesets del repository
gh api repos/{owner}/{repo}/rulesets --jq '.[] | {id: .id, name: .name, enforcement: .enforcement, target: .target}'

# Verificare i dettagli di un ruleset specifico
gh api repos/{owner}/{repo}/rulesets/{ruleset_id} --jq '{
  name: .name,
  enforcement: .enforcement,
  conditions: .conditions,
  rules: [.rules[].type],
  bypass_actors: .bypass_actors
}'

# Verificare le valutazioni del ruleset per un branch
gh api repos/{owner}/{repo}/rules/branches/main --jq '.[] | {type: .type, ruleset_id: .ruleset_id}'
```

### Secret Scanning Alert — Falso Positivo

**Sintomi**: Secret scanning segnala un secret in un file che contiene un valore di esempio, un placeholder o un token di test non valido.

**Causa**: I pattern di secret scanning sono progettati per minimizzare i falsi negativi, il che significa che possono generare falsi positivi per stringhe che assomigliano a secret reali.

**Soluzione**:

```bash
# Chiudere un alert come falso positivo
gh api repos/{owner}/{repo}/secret-scanning/alerts/{alert_number} -X PATCH \
  -f state="resolved" -f resolution="false_positive"

# Risoluzioni disponibili: false_positive, wont_fix, revoked, used_in_tests

# Per evitare futuri falsi positivi: usare commenti inline
# git-secret-scanning: ignore (in un commento nel codice)
```

### Dependabot PR Non Create

**Sintomi**: Dependabot è configurato ma non crea PR per le dipendenze obsolete.

**Causa**: Il file `dependabot.yml` ha errori di sintassi, il package ecosystem non è supportato, il `directory` è errato, oppure `open-pull-requests-limit` è raggiunto.

**Soluzione**:

```bash
# Verificare lo stato di Dependabot
gh api repos/{owner}/{repo}/vulnerability-alerts -X GET

# Verificare i log di Dependabot
# Settings → Code security and analysis → Dependabot → View logs

# Forzare un check manuale
gh api repos/{owner}/{repo}/dependabot/alerts --jq '
  .[:5] | .[] | {number: .number, dependency: .dependency.package.name, severity: .security_advisory.severity}'

# Verificare la validità del file dependabot.yml
# Il file DEVE essere in .github/dependabot.yml (non nella root)
```

### Merge Conflict Ricorrente su File Auto-Generati

**Sintomi**: Conflitti frequenti su file come `package-lock.json`, `yarn.lock`, `Gemfile.lock` o file di migrazione database.

**Causa**: Più branch modificano le dipendenze contemporaneamente, generando conflitti nei lock file.

**Soluzione**:

```bash
# Configurare merge strategy per lock file in .gitattributes
echo "package-lock.json merge=ours" >> .gitattributes
echo "yarn.lock merge=ours" >> .gitattributes

# Oppure rigenerare il lock file dopo il merge
# Nel workflow CI:
# - name: Regenerate lock file
#   if: github.event.pull_request.base.ref == 'main'
#   run: |
#     npm install --package-lock-only
#     git add package-lock.json
#     git diff --staged --quiet || git commit -m "chore: regenerate lock file"
```

### Environment Deployment Bloccato — Reviewer Non Disponibile

**Sintomi**: Un deployment verso l'environment di produzione è in attesa di approvazione, ma i reviewer designati non sono disponibili.

**Causa**: L'environment richiede approvazione da reviewer specifici che potrebbero essere in ferie, fuori orario o non più parte del team.

**Soluzione**:

```bash
# Verificare i reviewer richiesti per l'environment
gh api repos/{owner}/{repo}/environments/production --jq '
  .protection_rules[] | select(.type == "required_reviewers") | .reviewers'

# Aggiornare i reviewer (aggiungere backup reviewer)
gh api repos/{owner}/{repo}/environments/production -X PUT \
  --input - << 'EOF'
{
  "reviewers": [
    {"type": "User", "id": 12345},
    {"type": "User", "id": 67890},
    {"type": "Team", "id": 11111}
  ]
}
EOF

# Approvare manualmente un deployment pending (come reviewer)
gh api repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments -X POST \
  --input - << 'EOF'
{
  "environment_ids": [123456],
  "state": "approved",
  "comment": "Approved - reviewed changes in PR #42"
}
EOF
```

### Review Dismissed Dopo Force Push

**Sintomi**: Le review approvate vengono automaticamente dismissed dopo un force push o un rebase del branch della PR.

**Causa**: La branch protection ha "Dismiss stale pull request approvals when new commits are pushed" abilitato. Un force push (es. `git push --force-with-lease` dopo un rebase interattivo) invalida tutte le review precedenti.

**Soluzione**:

```bash
# Verificare se la regola è attiva
gh api repos/{owner}/{repo}/branches/main/protection/required_pull_request_reviews \
  --jq '.dismiss_stale_reviews'

# Best practice: usare rebase-merge o squash-merge nella configurazione del repo
# per evitare la necessità di force push durante il ciclo di review.

# Se il force push era necessario, richiedere una nuova review:
gh pr edit <pr-number> --add-reviewer @team-name

# Alternativa: usare i rulesets (2023+) che permettono di configurare
# "dismiss stale reviews on push" separatamente dal force push policy
```

### Repository Transfer Perde le Branch Protection Rules

**Sintomi**: Dopo il transfer di un repository ad un'altra organizzazione o utente, le branch protection rules, i rulesets, gli environment e i secrets non sono più configurati.

**Causa**: Il transfer preserva code, issues, PR, stars e watchers, ma le branch protection rules, gli environment secrets, i deploy keys e le GitHub App installations non vengono trasferiti automaticamente.

**Soluzione**:

```bash
# PRIMA del transfer: esportare la configurazione
# 1. Branch protection
gh api repos/{owner}/{repo}/branches/main/protection > branch-protection-backup.json

# 2. Rulesets
gh api repos/{owner}/{repo}/rulesets --jq '.[] | .id' | while read id; do
  gh api repos/{owner}/{repo}/rulesets/$id > "ruleset-$id-backup.json"
done

# 3. Environments
gh api repos/{owner}/{repo}/environments --jq '.environments[].name' > environments-backup.txt

# 4. Secrets (solo i nomi, non i valori!)
gh secret list --json name --jq '.[].name' > secrets-names-backup.txt

# DOPO il transfer: riapplicare la configurazione
# Le branch protection e i rulesets devono essere ricreati manualmente
# I secrets devono essere reinseriti con i valori originali
```

### Webhook Delivery Failures — Payload Non Ricevuto

**Sintomi**: Un webhook configurato non invia notifiche all'endpoint esterno. Le integrazioni (Slack, Jenkins, JIRA) non ricevono gli eventi.

**Causa**: L'endpoint restituisce un codice HTTP diverso da 2xx, il DNS del target non è risolvibile da GitHub, il certificato SSL è invalido o scaduto, oppure il payload supera il limite di 25 MB.

**Soluzione**:

```bash
# Verificare i delivery recenti del webhook
gh api repos/{owner}/{repo}/hooks --jq '.[] | {id: .id, url: .config.url, active: .active}'

# Verificare i delivery falliti per un webhook specifico
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries --jq '
  .[:10] | .[] | {id: .id, status_code: .status_code, event: .event, delivered_at: .delivered_at}'

# Visualizzare il dettaglio di un delivery fallito
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id} --jq '{
  request: .request.headers,
  response_code: .status_code,
  response_body: .response.body
}'

# Re-inviare un delivery fallito
gh api repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}/attempts -X POST
```

### CODEOWNERS: Team Non Riceve Notifiche di Review

**Sintomi**: Il file CODEOWNERS è configurato con un team (es. `@org/backend-team`), ma i membri del team non vengono assegnati come reviewer né ricevono notifiche.

**Causa**: Il team non ha accesso al repository, il team referenziato nel CODEOWNERS non esiste o ha un typo nel nome, oppure il team ha le notifiche di review disabilitate nelle impostazioni individuali.

**Soluzione**:

```bash
# Verificare errori di sintassi nel CODEOWNERS
gh api repos/{owner}/{repo}/codeowners/errors --jq '.errors[] | {line: .line, message: .message}'

# Verificare che il team abbia accesso al repository
gh api orgs/{org}/teams/{team-slug}/repos --jq '.[] | select(.name == "repo-name") | .permissions'

# Se il team non ha accesso, aggiungerlo
gh api orgs/{org}/teams/{team-slug}/repos/{owner}/{repo} -X PUT -f permission=push

# Verificare le impostazioni di review assignment del team
# Settings → Teams → [team] → Code review → Assign:
# "Notify entire team" vs "Route to specific members" (round robin)
```

### Actions Workflow Non Triggera su Branch Protetto

**Sintomi**: Un push su un branch protetto non avvia il workflow CI/CD atteso. Il workflow funziona su branch non protetti.

**Causa**: I push diretti al branch protetto sono bloccati dalla branch protection, quindi il trigger `on: push` non scatta. Se il push avviene tramite merge di PR, il trigger deve essere `on: pull_request` o il merge method deve essere configurato. Inoltre, workflow file modificati in una PR non vengono eseguiti con la versione della PR per motivi di sicurezza.

**Soluzione**:

```bash
# Verificare quale trigger è configurato nel workflow
gh api repos/{owner}/{repo}/contents/.github/workflows/ci.yml --jq '.content' | base64 -d | head -20

# Per branch protetti, usare il trigger pull_request + push su merge:
# on:
#   pull_request:
#     branches: [main]
#   push:
#     branches: [main]

# Verificare che il workflow sia nel default branch
# I workflow vengono letti dal default branch, non dal branch della PR
# (eccezione: pull_request trigger legge il workflow dal merge ref)

# Verificare i run recenti
gh run list --workflow=ci.yml --limit=5
```

### Signed Commit Rifiutato dalla Branch Protection

**Sintomi**: Un commit firmato con GPG/SSH viene rifiutato dalla branch protection con "Commit signature does not match committer". Il push fallisce nonostante la firma sia presente.

**Causa**: La chiave GPG/SSH non è associata all'email del committer su GitHub, la chiave è scaduta, oppure il committer email nel commit non corrisponde a nessun email verificato nel profilo GitHub.

**Soluzione**:

```bash
# Verificare che il commit sia firmato correttamente
git log --show-signature -1

# Verificare che l'email del commit corrisponda a un email verificato su GitHub
git config user.email
# L'email deve comparire in: Settings → Emails → verified

# Verificare la chiave GPG
gpg --list-secret-keys --keyid-format LONG
gh api user/gpg_keys --jq '.[].key_id'

# Se la chiave è scaduta, aggiornare la data di scadenza
gpg --edit-key <KEY_ID>
# > expire → selezionare la nuova data → save

# Per SSH signing (Git 2.34+):
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub
git config commit.gpgsign true
```

---

## FAQ — Domande Frequenti

### 1. Qual è la differenza tra branch protection rules e rulesets?

Le branch protection rules sono il meccanismo legacy — operano su un singolo pattern di branch per repository. I rulesets (2023+) sono il successore: supportano pattern multipli, tag protection, enforcement a livello di organizzazione, modalità evaluate (dry-run), pattern per commit message e email, bypass granulare per attore, e import/export JSON. Per nuovi setup, usare i rulesets.

### 2. CODEOWNERS funziona se i team referenziati non hanno accesso al repository?

No. I team devono avere almeno accesso in lettura (read) al repository per essere assegnati come reviewer tramite CODEOWNERS. Se un team nel CODEOWNERS non ha accesso al repository, la rule viene ignorata silenziosamente. Verificare con `gh api repos/{owner}/{repo}/codeowners/errors`.

### 3. Posso avere più file CODEOWNERS? Quale ha la precedenza?

GitHub cerca il file CODEOWNERS in tre posizioni, in ordine di priorità: `.github/CODEOWNERS`, `CODEOWNERS` nella root, `docs/CODEOWNERS`. Solo il primo file trovato viene utilizzato — non vengono mergiati. Best practice: usare sempre `.github/CODEOWNERS`.

### 4. Come impedisco il push diretto a main senza PR?

Abilitare "Require a pull request before merging" nelle branch protection rules o nei rulesets. Per impedire anche agli admin di bypassare, abilitare "Do not allow bypassing the above settings" (branch protection) o non includere admin nei bypass actors (rulesets).

### 5. Posso proteggere i tag come proteggo i branch?

Sì, tramite rulesets. I rulesets supportano `"target": "tag"` che permette di applicare regole come `deletion` e `non_fast_forward` ai tag, impedendo la cancellazione o sovrascrittura di tag di release.

### 6. Come gestisco i repository archived? Possono ricevere PR?

Un repository archived è completamente read-only: nessun push, nessuna PR, nessuna issue. Per riaprire temporaneamente per una patch critica:

```bash
# Dis-archiviare
gh repo unarchive my-org/old-project --yes
# ... applicare la patch ...
# Re-archiviare
gh repo archive my-org/old-project --yes
```

### 7. Secret scanning cattura tutti i tipi di secret?

No, ma copre la maggior parte. GitHub supporta pattern per >200 tipi di token (AWS, Azure, GCP, Stripe, Slack, ecc.) in partnership con i provider. Per secret proprietari dell'organizzazione, configurare custom patterns con regex a livello di organizzazione.

### 8. Come migro le branch protection rules ai rulesets?

Non esiste una migrazione automatica. Il processo è manuale:
1. Esportare le regole attuali: `gh api repos/{owner}/{repo}/branches/main/protection`
2. Creare un ruleset equivalente con le stesse regole
3. Testare con `enforcement: "evaluate"` per verificare che il comportamento sia identico
4. Passare a `enforcement: "active"`
5. Rimuovere le branch protection rules legacy

### 9. Posso limitare chi può creare repository nell'organizzazione?

Sì. In Organization Settings → Member privileges → Repository creation, è possibile configurare chi può creare repository (All members, Admin only, None) e il tipo (Public, Private, Internal).

### 10. Come funziona il fork di un repository privato?

Per default, i fork di repository privati non sono permessi. L'amministratore dell'organizzazione deve abilitare "Allow forking of private repositories" in Organization Settings → Member privileges. I fork di repository privati restano privati e visibili solo ai membri con accesso.

### 11. Posso impedire il force push solo su determinati branch?

Sì. Le branch protection rules e i rulesets supportano `allow_force_pushes: false` e la regola `non_fast_forward` rispettivamente. Applicare la protezione solo ai branch che necessitano di cronologia immutabile (main, release/*).

### 12. Come configuro le notifiche per i cambiamenti al repository settings?

GitHub emette eventi webhook per `repository` (con actions come `edited`, `deleted`, `transferred`). Configurare un webhook con l'evento `repository` e processare il payload per generare alert. Per audit a livello di organizzazione, abilitare l'Audit Log.

### 13. Qual è il limite di dimensione per un repository GitHub?

GitHub raccomanda di mantenere i repository sotto 5 GB. Il limite per singolo file è 100 MB (con warning a 50 MB). Per file grandi, usare Git LFS. Per monitorare la dimensione: `gh api repos/{owner}/{repo} --jq '.size'` (in KB).

### 14. Come gestisco le GitHub Apps vs Personal Access Tokens per l'automazione?

Le GitHub Apps sono preferibili perché: hanno permessi granulari per repository, rate limit più alto (5000 req/hr per installazione), non sono legate a un utente personale, e generano token con scadenza breve. I PAT (fine-grained) sono adatti per automazioni personali o script one-off.

### 15. Come forzo la firma dei commit su tutti i repository dell'organizzazione?

Creare un ruleset a livello di organizzazione con la regola `commit_author_email_pattern` e `required_signatures`. Questo impone la firma GPG o SSH su tutti i commit prima del merge.

```bash
gh api orgs/{org}/rulesets -X POST \
  --input - << 'EOF'
{
  "name": "Require Signed Commits",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "repository_name": {"include": ["*"], "exclude": []},
    "ref_name": {"include": ["refs/heads/main"], "exclude": []}
  },
  "rules": [
    {"type": "required_signatures"}
  ]
}
EOF
```

---

## Esercizi

### Esercizio 1 — Branch Protection Rules Completa

**Obiettivo:** Configurare protezione branch production-grade su un repository di test.

1. Creare un repository pubblico con un branch `main` e un branch `develop`
2. Configurare branch protection su `main` con: require PR (almeno 1 reviewer), require status checks (`ci/test`), require signed commits, require linear history
3. Configurare branch protection su `develop` con: require PR (nessun reviewer obbligatorio), require status checks
4. Tentare un push diretto su `main` e verificare il rifiuto
5. Creare una PR da `develop` a `main` e verificare che i check obbligatori vengano richiesti

### Esercizio 2 — CODEOWNERS per Monorepo

**Obiettivo:** Implementare una strategia CODEOWNERS per un monorepo multi-team.

1. Creare una struttura di directory con: `frontend/`, `backend/`, `infra/`, `docs/`, `.github/`
2. Scrivere un file `CODEOWNERS` che assegna: team-frontend per `frontend/`, team-backend per `backend/`, team-devops per `infra/` e `*.yml`, team-docs per `docs/`
3. Configurare una regola catch-all per i file non coperti
4. Creare PR che toccano file in directory diverse e verificare che i reviewer corretti vengano assegnati automaticamente
5. Testare il comportamento con file che matchano piu regole (ultima regola vince)

### Esercizio 3 — Repository Template

**Obiettivo:** Creare un repository template riutilizzabile per microservizi.

1. Creare un repository con struttura standard: `src/`, `tests/`, `docs/`, `.github/workflows/`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`
2. Includere un `README.md` template con sezioni placeholder (descrizione, setup, API, deploy)
3. Includere workflow CI/CD base, `.gitignore`, `.editorconfig`, `LICENSE`
4. Marcare il repository come template nelle settings
5. Generare un nuovo repository dal template e verificare che tutti i file vengano copiati correttamente (senza la storia Git del template)

### Esercizio 4 — Rulesets Organization-Level

**Obiettivo:** Configurare rulesets a livello organizzazione con la REST API.

1. Creare un ruleset via `gh api` che si applichi a tutti i repository dell'organizzazione
2. Il ruleset deve: richiedere PR review, bloccare force-push, richiedere status check `lint` e `test`
3. Configurare bypass actors per il team `release-managers`
4. Verificare il ruleset con `gh api orgs/{org}/rulesets` e testare che le regole vengano applicate
5. Creare un secondo ruleset per tag con pattern `v*` che richieda firma dei commit

### Esercizio 5 — Governance Audit Automatizzato

**Obiettivo:** Creare uno script di audit che verifichi la conformita dei repository.

1. Scrivere uno script Bash che usa `gh api` per elencare tutti i repository di un'organizzazione
2. Per ogni repository verificare: branch protection attiva su `main`, CODEOWNERS presente, license file presente, Dependabot configurato, secret scanning abilitato
3. Generare un report CSV con colonne: `repo, branch_protection, codeowners, license, dependabot, secret_scanning, compliant`
4. Marcare come `compliant=true` solo i repository che soddisfano tutti i criteri
5. Testare lo script su almeno 3 repository con configurazioni diverse

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Docs — Managing Repositories** — Guida completa alla gestione dei repository GitHub. <https://docs.github.com/en/repositories> (consultato: 2026-05-24)
- **GitHub Docs — Branch Protection Rules** — Configurazione delle regole di protezione branch. <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository> (consultato: 2026-05-24)
- **GitHub Docs — Rulesets** — La nuova generazione di protezione branch a livello repository e organizzazione. <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets> (consultato: 2026-05-24)
- **GitHub Docs — CODEOWNERS** — Automazione dell'assegnazione dei reviewer per path. <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners> (consultato: 2026-05-24)
- **GitHub Docs — Repository Templates** — Creazione e utilizzo di template per nuovi repository. <https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository> (consultato: 2026-05-24)
- **GitHub Docs — Security Advisories** — Gestione delle vulnerabilita di sicurezza nei repository. <https://docs.github.com/en/code-security/security-advisories> (consultato: 2026-05-24)
- **Choose a License** — Guida alla scelta della licenza open source. <https://choosealicense.com/> (consultato: 2026-05-24)
- **SPDX License List** — Lista standardizzata degli identificatori di licenza. <https://spdx.org/licenses/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Chacon S., Straub B., *Pro Git* (2nd ed.), Apress, 2014. Disponibile gratuitamente su <https://git-scm.com/book>.
- Beer B., *Introducing GitHub* (2nd ed.), O'Reilly, 2018.
- Loeliger J., McCullough M., *Version Control with Git* (3rd ed.), O'Reilly, 2022.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [06 — Git Branching e Merge Avanzato](06-git-branching-merge-avanzato.md) | Le branch protection rules si applicano alle strategie di branching trattate in questo modulo |
| [11 — Gitignore, Gitattributes e Config](11-gitignore-gitattributes-config.md) | I file di configurazione repository (.gitignore, .gitattributes) completano la governance trattata qui |
| [13 — Issues, Projects e Collaborazione](13-github-issues-projects-collaboration.md) | La collaborazione tramite PR e code review si basa sulle protezioni branch configurate in questo modulo |
| [15 — GitHub API, CLI e Webhooks](15-github-api-cli-webhooks.md) | L'automazione della governance utilizza le API e la CLI trattate in questo modulo |
| [16 — GitHub Security e Scanning](16-github-security-scanning.md) | Le security policy del repository si integrano con le feature di scanning e protezione |
| [20 — Git Workflow Team](20-git-workflow-team-guida-completa.md) | I workflow di team dipendono dalle branch protection e dai CODEOWNERS configurati qui |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Branch protection rule** | Regola configurata su un branch che impone vincoli (PR obbligatorie, status check, firma commit) prima di consentire il merge o il push. |
| **Ruleset** | Evoluzione delle branch protection: set di regole applicabili a livello repository o organizzazione con supporto per bypass actors e condizioni granulari. |
| **CODEOWNERS** | File nel repository (`.github/CODEOWNERS`) che mappa pattern di percorso a team o utenti, assegnando automaticamente i reviewer alle pull request. |
| **Repository template** | Repository contrassegnato come modello che puo essere usato per generare nuovi repository con la stessa struttura di file ma senza la storia Git. |
| **Status check** | Verifica esterna (CI, linter, test) il cui risultato viene riportato a GitHub e puo essere reso obbligatorio per il merge tramite branch protection. |
| **Required reviewer** | Numero minimo di approvazioni richieste su una pull request prima che il merge sia consentito dalla branch protection rule. |
| **Linear history** | Vincolo che impedisce merge commit, richiedendo squash o rebase per mantenere una cronologia lineare sul branch protetto. |
| **Signed commit** | Commit firmato crittograficamente (GPG o SSH) che verifica l'identita dell'autore. Puo essere reso obbligatorio dalla branch protection. |
| **Force push** | Operazione `git push --force` che sovrascrive la storia remota. Le branch protection possono bloccarla per prevenire perdita di dati. |
| **Bypass actor** | Utente, team o app autorizzato a ignorare le regole di un ruleset (es. bot di release, team di amministratori). |
| **Repository visibility** | Impostazione che determina se un repository e pubblico (visibile a tutti), privato (solo collaboratori) o interno (visibile all'organizzazione). |
| **Auto-merge** | Funzionalita che esegue automaticamente il merge di una PR quando tutti i required status check e le review sono soddisfatti. |
| **Governance** | Insieme di policy, regole e automazioni che garantiscono la qualita, la sicurezza e la conformita del codice in un repository o organizzazione. |
| **Terraform provider** | Plugin Terraform (es. `hashicorp/github`) che consente di gestire risorse GitHub (repository, branch protection, team) come Infrastructure as Code. |
| **Compliance audit** | Verifica sistematica che i repository rispettino le policy organizzative (protezioni branch, licenze, scanning di sicurezza). |
