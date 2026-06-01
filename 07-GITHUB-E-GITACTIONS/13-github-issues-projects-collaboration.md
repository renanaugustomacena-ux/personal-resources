---
corso: "GitHub e Git Actions"
fase: "3 — Piattaforma GitHub"
modulo: "13"
titolo: "GitHub Issues, Projects e Collaborazione"
versione: "GitHub 2024"
livello: "intermedio"
prerequisiti:
  - "account GitHub con repository attivo"
  - "esperienza base con pull request e branch"
  - "familiarita con Markdown"
obiettivi:
  - "configurare issue templates e form per standardizzare le segnalazioni"
  - "gestire il ciclo di vita delle issue con labels, milestones e automazioni"
  - "utilizzare GitHub Projects v2 con viste tabellari, board e automazioni"
  - "implementare code review efficaci con suggerimenti inline e CODEOWNERS"
  - "scegliere tra Discussions, Issues e Wiki per diversi tipi di comunicazione"
tag: [github, issues, projects, pull-request, code-review, discussions, collaborazione, milestones]
---

# GitHub Issues, Projects e Collaborazione — Guida Approfondita

> **Modulo 13** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Configurare issue templates e form per standardizzare le segnalazioni
> 2. Gestire il ciclo di vita delle issue con labels, milestones e automazioni
> 3. Utilizzare GitHub Projects v2 con viste tabellari, board e automazioni
> 4. Implementare code review efficaci con suggerimenti inline e CODEOWNERS
> 5. Scegliere tra Discussions, Issues e Wiki per diversi tipi di comunicazione
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **Issue templates riducono garbage tickets.**
2. **Projects v2 (beta GA 2024): tabular views, automations.**
3. **Discussions per Q&A (vs issues per bug/feature).**
4. **Labels + milestones per filtering.**


## Indice
- [Panoramica](#panoramica)
- [Issues: Gestione dei Task e Bug](#issues-gestione-dei-task-e-bug)
- [Issue Templates](#issue-templates)
- [Labels, Milestones e Assignees](#labels-milestones-e-assignees)
- [Issue Types (GA 2025)](#issue-types-ga-2025)
- [Sub-Issues e Gerarchia del Lavoro](#sub-issues-e-gerarchia-del-lavoro)
- [GitHub Projects v2](#github-projects-v2)
- [Projects v2: API GraphQL e Automazione Avanzata](#projects-v2-api-graphql-e-automazione-avanzata)
- [Projects v2: Insights, Chart e Status Updates](#projects-v2-insights-chart-e-status-updates)
- [Pull Requests Avanzate](#pull-requests-avanzate)
- [Merge Queue](#merge-queue)
- [Code Review Best Practices](#code-review-best-practices)
- [Discussions](#discussions)
- [Wiki](#wiki)
- [CODEOWNERS e Review Assignment](#codeowners-e-review-assignment)
- [Repository Rulesets e Required Reviewers](#repository-rulesets-e-required-reviewers)
- [IssueOps: Issues come Interfaccia di Automazione](#issueops-issues-come-interfaccia-di-automazione)
- [Automazione Avanzata con GitHub Actions](#automazione-avanzata-con-github-actions)
- [Progetti Cross-Repository e Organizzazione Enterprise](#progetti-cross-repository-e-organizzazione-enterprise)
- [Strategie di Collaborazione per Team](#strategie-di-collaborazione-per-team)
- [Best Practices](#best-practices)
- [Anti-Pattern e Errori Comuni](#anti-pattern-e-errori-comuni)
- [Troubleshooting](#troubleshooting)
- [Esercizi](#esercizi)
- [Riferimenti](#riferimenti)

---

## Panoramica

La collaborazione efficace in un progetto software richiede strumenti strutturati per la comunicazione, il tracciamento del lavoro e la revisione del codice. GitHub offre un ecosistema integrato di strumenti — Issues, Projects, Pull Requests, Discussions e Wiki — che, configurati correttamente, trasformano un repository da semplice contenitore di codice a piattaforma di gestione del progetto completa.

Questa guida esplora in profondità ciascuno di questi strumenti, le best practices per la code review, le strategie di organizzazione del lavoro con GitHub Projects v2 e le tecniche avanzate per la collaborazione in team di qualsiasi dimensione.

### Evoluzione dell'Ecosistema (2024-2026)

L'ecosistema di GitHub Issues e Projects ha subito una trasformazione significativa tra il 2024 e il 2026. Le novità principali includono:

- **Issue Types (GA aprile 2025)**: classificazione standardizzata delle issue a livello organizzazione con tipi predefiniti (Bug, Task, Feature) e personalizzabili.
- **Sub-Issues (GA aprile 2025)**: gerarchia parent-child fino a otto livelli di profondità, sostituzione ufficiale delle Tasklist deprecate ad aprile 2025.
- **Required Reviewer Rule nei Rulesets (GA febbraio 2026)**: controllo granulare su chi deve approvare le modifiche, con supporto per pattern di negazione (`!`).
- **AI Labeler e Moderator (settembre 2025)**: triage automatico delle issue tramite GitHub Models inference API integrato in GitHub Actions.
- **Merge Queue migliorata**: automazione del merge con validazione sequenziale contro il branch target aggiornato.
- **Projects v2 Insights**: grafici storici (burn-up, velocity) e status updates per la comunicazione con gli stakeholder.
- **IssueOps**: pattern emergente che utilizza Issues come interfaccia per l'automazione CI/CD tramite commenti, label e cambi di stato.

Questa guida copre sia le funzionalità consolidate sia queste innovazioni recenti, fornendo esempi pratici e configurazioni pronte per l'uso.

### Mappa Decisionale: Quale Strumento Usare

| Scenario | Strumento Consigliato | Motivazione |
|---|---|---|
| Bug report con passi per riprodurre | Issue con template YAML | Campi strutturati, validazione, label automatiche |
| Proposta di design o RFC | Discussion (categoria Ideas) | Conversazione aperta, non richiede azione immediata |
| Domanda tecnica di supporto | Discussion (categoria Q&A) | Risposta marcabile, non inquina la lista issue |
| Task di implementazione | Issue con tipo "Task" | Tracciabile in Projects, assegnabile, collegabile a PR |
| Epica con sotto-attività | Issue parent con sub-issues | Gerarchia fino a 8 livelli, progresso aggregato |
| Pianificazione sprint | Projects v2 con vista Board | Kanban con automazioni di stato |
| Roadmap trimestrale | Projects v2 con vista Roadmap | Timeline con iterazioni e date |
| Documentazione tecnica persistente | Wiki o docs/ nel repo | Versionata, ricercabile, strutturata |
| Annunci e release notes | Discussion (Announcements) | Solo maintainer possono creare, commenti aperti |
| Approvazione deployment | IssueOps con Actions | Workflow tracciabile, audit trail, approvazione tramite commenti |

---

## Issues: Gestione dei Task e Bug

### Creazione e Gestione

```bash
# Creare un'issue da CLI
gh issue create --title "Bug: Login fallisce con caratteri speciali" \
  --body "## Descrizione\nIl login fallisce quando la password contiene &" \
  --label "bug,priority:high" \
  --assignee "@me" \
  --milestone "v2.1"

# Listare le issue
gh issue list
gh issue list --label "bug" --state open
gh issue list --assignee "@me" --state open

# Visualizzare un'issue
gh issue view 42

# Commentare un'issue
gh issue comment 42 --body "Confermato il bug. La causa è nel parser URL."

# Chiudere un'issue
gh issue close 42 --comment "Risolto con PR #45"

# Riaprire un'issue
gh issue reopen 42

# Trasferire un'issue a un altro repository
gh issue transfer 42 org/altro-repo

# Pin di un'issue (massimo 3)
gh api repos/{owner}/{repo}/issues/42/pin -X POST
```

### Linking tra Issues e PR

GitHub supporta il linking automatico tra issues e pull requests attraverso parole chiave nel messaggio di commit o nel corpo della PR:

```markdown
<!-- Nel corpo della PR o nel messaggio di commit -->
Fixes #42
Closes #42
Resolves #42

<!-- Linking multiplo -->
Fixes #42, closes #43, resolves #44

<!-- Cross-repository -->
Fixes org/repo#42

<!-- Solo riferimento (senza auto-close) -->
Related to #42
See also #43
```

### Task Lists nelle Issues

```markdown
## Checklist di Implementazione

- [x] Analisi dei requisiti
- [x] Design dell'API
- [ ] Implementazione backend
  - [x] Modello dati
  - [ ] Controller
  - [ ] Middleware di autenticazione
- [ ] Implementazione frontend
- [ ] Test unitari
- [ ] Test di integrazione
- [ ] Documentazione

<!-- Le task lists mostrano il progresso nella lista delle issues -->
<!-- Esempio: 3/7 task completate (42%) -->
```

### Sub-Issues e Tasklist Tracking (Beta)

GitHub supporta le sub-issues per scomporre issue complesse:

```markdown
<!-- Nella issue parent -->
## Sub-tasks

```[tasklist]
- [ ] #101 Implementare autenticazione
- [ ] #102 Implementare autorizzazione
- [ ] #103 Aggiungere rate limiting
```
```

> **Nota (aprile 2025):** Le tasklist in formato `[tasklist]` sono state deprecate il 30 aprile 2025. La funzionalità è stata sostituita dalle **sub-issues**, trattate nella sezione dedicata più avanti in questo modulo.

### Ricerca Avanzata delle Issues

GitHub supporta una sintassi di ricerca potente per filtrare le issue:

```bash
# Ricerca per label multiple (AND)
gh issue list --label "bug" --label "priority:high"

# Ricerca con query avanzata
gh issue list --search "is:open label:bug assignee:@me sort:updated-desc"

# Ricerca per milestone
gh issue list --milestone "v2.1.0" --state all

# Ricerca per autore
gh issue list --search "is:open author:username"

# Ricerca per menzione
gh issue list --search "is:open mentions:username"

# Ricerca per data
gh issue list --search "is:open created:>2025-01-01"

# Ricerca per numero di commenti
gh issue list --search "is:open comments:>5"

# Ricerca con esclusione
gh issue list --search "is:open -label:wontfix -label:duplicate"

# Ricerca per tipo di issue (GA 2025)
gh issue list --search "is:open type:bug"
gh issue list --search "is:open type:feature"

# Ricerca cross-repository nell'organizzazione
gh search issues "org:my-org is:open label:security" --limit 50
```

### Issue Pinning e Locking

Le issue pinned appaiono in cima alla lista delle issue, utili per annunci importanti o bug critici:

```bash
# Pinnare un'issue (massimo 3 per repository)
gh api repos/{owner}/{repo}/issues/42/pin -X POST

# Rimuovere il pin
gh api repos/{owner}/{repo}/issues/42/pin -X DELETE

# Lockare un'issue (impedisce nuovi commenti)
gh issue lock 42 --reason "resolved"
# Motivi disponibili: off-topic, too heated, resolved, spam

# Sbloccare un'issue
gh issue unlock 42
```

### Operazioni Batch sulle Issues

Per gestire grandi volumi di issue, è possibile eseguire operazioni batch tramite la CLI:

```bash
# Chiudere tutte le issue con una label specifica
gh issue list --label "wontfix" --state open --json number -q '.[].number' | \
  xargs -I {} gh issue close {} --comment "Chiusa come wontfix durante il triage."

# Aggiungere una label a tutte le issue aperte senza label di priorità
gh issue list --state open --json number,labels \
  -q '.[] | select(.labels | map(.name) | any(startswith("priority:")) | not) | .number' | \
  xargs -I {} gh issue edit {} --add-label "priority:needs-triage"

# Trasferire tutte le issue con una label a un altro repository
gh issue list --label "moved-to-v2" --state open --json number -q '.[].number' | \
  xargs -I {} gh issue transfer {} org/new-repo

# Assegnare tutte le issue di un milestone a un utente
gh issue list --milestone "v2.1.0" --state open --json number -q '.[].number' | \
  xargs -I {} gh issue edit {} --add-assignee "dev-lead"
```

### Timeline e Audit Trail

Ogni issue mantiene una timeline completa di tutti gli eventi. Questo è fondamentale per il tracking e l'audit:

```bash
# Visualizzare la timeline completa di un'issue
gh api repos/{owner}/{repo}/issues/42/timeline --paginate | \
  jq '.[] | {event: .event, created_at: .created_at, actor: .actor.login}'

# Tipi di eventi nella timeline:
# - commented: nuovo commento
# - labeled / unlabeled: aggiunta/rimozione label
# - assigned / unassigned: assegnazione/rimozione assignee
# - milestoned / demilestoned: aggiunta/rimozione milestone
# - closed / reopened: chiusura/riapertura
# - referenced: riferimento da un commit
# - cross-referenced: riferimento da un'altra issue o PR
# - renamed: cambio titolo
# - locked / unlocked: blocco/sblocco commenti
# - transferred: trasferimento a un altro repository
# - connected / disconnected: collegamento/scollegamento con PR
```

---

## Issue Templates

### Form-based Templates (YAML)

I template basati su YAML forniscono form strutturati con campi definiti:

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Bug Report
description: Segnalare un bug nel software
title: "[Bug]: "
labels: ["bug", "triage"]
assignees:
  - team-lead
body:
  - type: markdown
    attributes:
      value: |
        Grazie per la segnalazione! Compilare tutti i campi per aiutarci a risolvere il bug.

  - type: input
    id: version
    attributes:
      label: Versione
      description: Quale versione del software stai usando?
      placeholder: "es. 2.1.0"
    validations:
      required: true

  - type: dropdown
    id: environment
    attributes:
      label: Ambiente
      description: In quale ambiente si verifica il bug?
      options:
        - Produzione
        - Staging
        - Sviluppo
        - Locale
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Descrizione del Bug
      description: Descrizione chiara e concisa del bug
      placeholder: "Cosa è successo? Cosa ti aspettavi?"
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Passi per Riprodurre
      description: Passi dettagliati per riprodurre il bug
      value: |
        1. Andare a '...'
        2. Cliccare su '...'
        3. Scorrere fino a '...'
        4. Vedere l'errore
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Comportamento Atteso
      description: Cosa ti aspettavi che succedesse?
    validations:
      required: true

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots
      description: Se applicabile, aggiungere screenshots

  - type: textarea
    id: logs
    attributes:
      label: Log e Messaggi di Errore
      description: Copiare eventuali log o messaggi di errore
      render: shell

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: Ho verificato che non esiste già un'issue simile
          required: true
        - label: Ho incluso passi per riprodurre il bug
          required: true
```

```yaml
# .github/ISSUE_TEMPLATE/feature_request.yml
name: Feature Request
description: Proporre una nuova funzionalità
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problema
      description: Quale problema risolve questa feature?
      placeholder: "Sono frustrato quando..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Soluzione Proposta
      description: Descrizione della soluzione desiderata
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternative Considerate
      description: Altre soluzioni considerate e perché non sono ideali

  - type: dropdown
    id: priority
    attributes:
      label: Priorità Percepita
      options:
        - Bassa — Nice to have
        - Media — Miglioramento significativo
        - Alta — Blocca il lavoro
        - Critica — Impatto su produzione
```

### Template Config

```yaml
# .github/ISSUE_TEMPLATE/config.yml
blank_issues_enabled: false  # Non permettere issue senza template
contact_links:
  - name: Domande Generali
    url: https://github.com/org/repo/discussions
    about: Per domande generali, usa GitHub Discussions
  - name: Supporto
    url: https://support.example.com
    about: Per supporto tecnico, contatta il team
  - name: Sicurezza
    url: https://github.com/org/repo/security/advisories/new
    about: Per segnalare vulnerabilità di sicurezza
```

### Template Avanzati: Security Report

```yaml
# .github/ISSUE_TEMPLATE/security_vulnerability.yml
name: Security Vulnerability Report
description: Segnalare una vulnerabilità di sicurezza (NON usare per issue pubbliche)
title: "[Security]: "
labels: ["type:security", "priority:critical"]
assignees:
  - security-lead
body:
  - type: markdown
    attributes:
      value: |
        ⚠️ **IMPORTANTE**: Se la vulnerabilità è critica, usa invece il
        [Security Advisory privato](https://github.com/org/repo/security/advisories/new).
        Questa form crea un'issue PUBBLICA.

  - type: dropdown
    id: severity
    attributes:
      label: Severità stimata (CVSS)
      options:
        - Critical (9.0-10.0)
        - High (7.0-8.9)
        - Medium (4.0-6.9)
        - Low (0.1-3.9)
        - Informational
    validations:
      required: true

  - type: input
    id: cwe
    attributes:
      label: CWE ID (se noto)
      description: "Identificatore Common Weakness Enumeration"
      placeholder: "es. CWE-79 (XSS), CWE-89 (SQL Injection)"

  - type: textarea
    id: description
    attributes:
      label: Descrizione della Vulnerabilità
      description: Descrizione tecnica della vulnerabilità trovata
    validations:
      required: true

  - type: textarea
    id: poc
    attributes:
      label: Proof of Concept
      description: Passi per riprodurre la vulnerabilità
      render: shell
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impatto
      description: Quale impatto ha questa vulnerabilità? (Confidenzialità, Integrità, Disponibilità)
    validations:
      required: true

  - type: textarea
    id: remediation
    attributes:
      label: Suggerimento di Remediation
      description: Se hai un suggerimento su come risolvere la vulnerabilità

  - type: checkboxes
    id: disclosure
    attributes:
      label: Responsible Disclosure
      options:
        - label: Confermo che questa segnalazione segue la policy di responsible disclosure
          required: true
        - label: Sono disponibile a collaborare per risolvere la vulnerabilità
```

### Template Avanzati: Documentation Update

```yaml
# .github/ISSUE_TEMPLATE/documentation.yml
name: Documentation Update
description: Segnalare documentazione mancante, errata o da migliorare
title: "[Docs]: "
labels: ["documentation"]
body:
  - type: dropdown
    id: doc-type
    attributes:
      label: Tipo di aggiornamento
      options:
        - Documentazione mancante
        - Documentazione errata
        - Documentazione obsoleta
        - Miglioramento documentazione esistente
        - Nuovo tutorial o guida
    validations:
      required: true

  - type: input
    id: doc-url
    attributes:
      label: URL o percorso del file
      description: Link alla pagina di documentazione o percorso del file nel repository
      placeholder: "es. docs/api/authentication.md o https://docs.example.com/api/auth"
    validations:
      required: true

  - type: textarea
    id: current-content
    attributes:
      label: Contenuto attuale (se errato)
      description: Cosa dice attualmente la documentazione?

  - type: textarea
    id: expected-content
    attributes:
      label: Contenuto corretto o richiesto
      description: Cosa dovrebbe dire la documentazione?
    validations:
      required: true

  - type: textarea
    id: context
    attributes:
      label: Contesto aggiuntivo
      description: Perché è importante questo aggiornamento?
```

### Validazione Avanzata con issue-ops/validator

Per scenari di validazione più complessi, è possibile utilizzare l'action `issue-ops/validator` che verifica i campi dell'issue rispetto a regole personalizzate:

```yaml
# .github/workflows/validate-issue.yml
name: Validate Issue Form

on:
  issues:
    types: [opened, edited]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Issue
        uses: issue-ops/validator@v2
        id: validate
        with:
          issue-number: ${{ github.event.issue.number }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          workspace: ${{ github.workspace }}

      - name: Comment on Invalid Issue
        if: steps.validate.outputs.result == 'failure'
        uses: peter-evans/create-or-update-comment@v4
        with:
          issue-number: ${{ github.event.issue.number }}
          body: |
            ⚠️ **Validazione fallita**

            L'issue non rispetta i requisiti del template. Per favore:
            ${{ steps.validate.outputs.errors }}

            Modifica l'issue per correggere i campi indicati.
```

### Template Markdown Legacy vs YAML Forms

GitHub supporta ancora i template Markdown tradizionali oltre ai form YAML. Le differenze principali:

| Aspetto | Markdown Template (.md) | YAML Form (.yml) |
|---|---|---|
| Campi tipizzati | No, testo libero | Sì (input, textarea, dropdown, checkboxes) |
| Validazione required | No | Sì, per campo |
| Layout strutturato | Dipende dall'utente | Garantito dal form |
| Supporto frontmatter | Sì (name, about, title, labels, assignees) | Sì, con più opzioni |
| Rendering | Markdown precompilato | Form HTML interattivo |
| Complessità | Semplice | Moderata |
| Caso d'uso ideale | Progetti semplici, contributori tecnici | Progetti con molti contributori, triage strutturato |

```markdown
<!-- .github/ISSUE_TEMPLATE/simple-bug.md — Template Markdown legacy -->
---
name: Simple Bug Report
about: Quick bug report for experienced contributors
title: "[Bug] "
labels: bug
assignees: ''
---

**Descrizione del bug**
<!-- Descrizione chiara del bug -->

**Passi per riprodurre**
1.
2.
3.

**Comportamento atteso**
<!-- Cosa dovrebbe succedere -->

**Screenshots**
<!-- Se applicabile -->

**Ambiente**
- OS: [es. macOS 15.2]
- Browser: [es. Firefox 134]
- Versione: [es. 2.1.0]
```

---

## Labels, Milestones e Assignees

### Sistema di Labels Strutturato

```bash
# Creare labels programmaticamente
gh label create "bug" --color "d73a4a" --description "Qualcosa non funziona"
gh label create "enhancement" --color "a2eeef" --description "Nuova funzionalità"
gh label create "documentation" --color "0075ca" --description "Miglioramenti alla documentazione"

# Labels di priorità
gh label create "priority:critical" --color "b60205" --description "Richiede attenzione immediata"
gh label create "priority:high" --color "d93f0b" --description "Da risolvere nel sprint corrente"
gh label create "priority:medium" --color "fbca04" --description "Da risolvere nel prossimo sprint"
gh label create "priority:low" --color "0e8a16" --description "Nice to have"

# Labels di tipo
gh label create "type:bug" --color "d73a4a" --description "Bug report"
gh label create "type:feature" --color "a2eeef" --description "Feature request"
gh label create "type:refactor" --color "d4c5f9" --description "Refactoring del codice"
gh label create "type:tech-debt" --color "e4e669" --description "Debito tecnico"
gh label create "type:security" --color "ee0701" --description "Issue di sicurezza"

# Labels di stato
gh label create "status:triage" --color "ededed" --description "In attesa di valutazione"
gh label create "status:in-progress" --color "1d76db" --description "In lavorazione"
gh label create "status:blocked" --color "b60205" --description "Bloccato da dipendenza"
gh label create "status:needs-review" --color "fbca04" --description "In attesa di review"

# Labels di area
gh label create "area:frontend" --color "5319e7" --description "Riguarda il frontend"
gh label create "area:backend" --color "006b75" --description "Riguarda il backend"
gh label create "area:infrastructure" --color "1d76db" --description "Riguarda l'infrastruttura"
gh label create "area:database" --color "e99695" --description "Riguarda il database"
```

### Milestones

```bash
# Creare una milestone
gh api repos/{owner}/{repo}/milestones -X POST \
  -f title="v2.1.0" \
  -f description="Release con miglioramenti di sicurezza e performance" \
  -f due_on="2024-06-30T23:59:59Z"

# Assegnare un'issue a una milestone
gh issue edit 42 --milestone "v2.1.0"

# Listare le milestones
gh api repos/{owner}/{repo}/milestones

# Chiudere una milestone
gh api repos/{owner}/{repo}/milestones/1 -X PATCH -f state="closed"
```

### Sincronizzazione Labels tra Repository

Per mantenere un set di label coerente in tutti i repository di un'organizzazione, è possibile utilizzare uno script di sincronizzazione:

```bash
#!/usr/bin/env bash
# sync-labels.sh — Sincronizza le label da un file YAML a tutti i repo dell'org

ORG="my-org"
LABEL_FILE="labels.yml"

# Formato del file labels.yml:
# - name: "type:bug"
#   color: "d73a4a"
#   description: "Bug report"
# - name: "type:feature"
#   color: "a2eeef"
#   description: "Feature request"

# Ottenere la lista dei repository
REPOS=$(gh repo list "$ORG" --json name -q '.[].name' --limit 200)

for REPO in $REPOS; do
  echo "Sincronizzazione label per $ORG/$REPO..."

  # Leggere le label dal file YAML e crearle/aggiornarle
  yq eval '.[]' "$LABEL_FILE" -o json | \
  while IFS= read -r label; do
    NAME=$(echo "$label" | jq -r '.name')
    COLOR=$(echo "$label" | jq -r '.color')
    DESC=$(echo "$label" | jq -r '.description')

    # Tentare di creare; se esiste, aggiornare
    gh label create "$NAME" \
      --color "$COLOR" \
      --description "$DESC" \
      --repo "$ORG/$REPO" 2>/dev/null || \
    gh label edit "$NAME" \
      --color "$COLOR" \
      --description "$DESC" \
      --repo "$ORG/$REPO" 2>/dev/null
  done
done
```

### Strategia di Labels Avanzata

Una strategia di label efficace utilizza prefissi per creare un sistema tassonomico chiaro. La convenzione più diffusa usa il formato `categoria:valore`:

```
# Struttura tassonomica raccomandata

## Tipo di lavoro (type:)
type:bug          — Errore nel software
type:feature      — Nuova funzionalità
type:refactor     — Ristrutturazione del codice
type:docs         — Documentazione
type:chore        — Manutenzione, dipendenze
type:perf         — Ottimizzazione prestazioni
type:security     — Vulnerabilità o hardening
type:tech-debt    — Debito tecnico da saldare

## Priorità (priority:)
priority:critical — Blocca la produzione, richiede fix immediato
priority:high     — Da risolvere nello sprint corrente
priority:medium   — Da pianificare nel prossimo sprint
priority:low      — Nice to have, backlog

## Stato del workflow (status:)
status:triage     — In attesa di valutazione
status:accepted   — Accettata, pronta per lavorazione
status:blocked    — Bloccata da dipendenza esterna
status:wontfix    — Non verrà risolta (con motivazione)
status:duplicate  — Duplicata di un'altra issue

## Area del progetto (area:)
area:frontend     — Interfaccia utente
area:backend      — Logica server e API
area:database     — Schema, query, migrazioni
area:infra        — CI/CD, deployment, cloud
area:mobile       — App mobile
area:docs         — Documentazione

## Effort stimato (effort:)
effort:small      — < 2 ore
effort:medium     — 2-8 ore
effort:large      — 1-3 giorni
effort:epic       — > 3 giorni (probabilmente da suddividere)

## Esperienza richiesta (experience:)
good-first-issue  — Adatta a nuovi contributori
help-wanted       — Si cerca aiuto dalla community
```

### Milestones: Strategie di Utilizzo

Le milestone possono essere utilizzate con strategie diverse a seconda del modello di lavoro:

**Modello Release-Based:**
```bash
# Milestone per ogni release
gh api repos/{owner}/{repo}/milestones -X POST \
  -f title="v3.0.0" \
  -f description="Major release con nuovo sistema di autenticazione" \
  -f due_on="2025-09-30T23:59:59Z"

gh api repos/{owner}/{repo}/milestones -X POST \
  -f title="v3.0.1" \
  -f description="Hotfix per vulnerabilità critica" \
  -f due_on="2025-10-07T23:59:59Z"
```

**Modello Sprint-Based:**
```bash
# Milestone per ogni sprint
gh api repos/{owner}/{repo}/milestones -X POST \
  -f title="Sprint 2025-W40" \
  -f description="Sprint 40: Focus su performance e stabilità" \
  -f due_on="2025-10-05T23:59:59Z"
```

**Monitoraggio progresso milestone:**
```bash
# Visualizzare il progresso di una milestone
gh api repos/{owner}/{repo}/milestones/1 | \
  jq '{title, open_issues, closed_issues,
       progress: ((.closed_issues / (.open_issues + .closed_issues)) * 100 | round),
       due_on}'

# Esempio output:
# {
#   "title": "v3.0.0",
#   "open_issues": 12,
#   "closed_issues": 38,
#   "progress": 76,
#   "due_on": "2025-09-30T23:59:59Z"
# }
```

---

## Issue Types (GA 2025)

A partire da aprile 2025, GitHub ha introdotto gli **Issue Types** come funzionalità GA (Generally Available). Gli Issue Types forniscono una classificazione standardizzata delle issue a livello di organizzazione, con un linguaggio condiviso tra tutti i repository.

### Tipi Predefiniti

GitHub fornisce tre tipi predefiniti che possono essere personalizzati:

| Tipo | Icona | Descrizione | Uso tipico |
|---|---|---|---|
| Bug | 🔴 | Qualcosa non funziona come previsto | Segnalazioni di errori |
| Task | 🟢 | Attività da completare | Lavoro pianificato, chore |
| Feature | 🟣 | Nuova funzionalità o miglioramento | Enhancement, nuove capacità |

### Configurazione a Livello Organizzazione

Gli Issue Types vengono gestiti a livello di organizzazione dall'amministratore:

```
Settings > Planning > Issue types
```

È possibile aggiungere tipi personalizzati, modificare quelli predefiniti, impostare colori e icone, e definire quali tipi sono disponibili per i repository dell'organizzazione.

### Gestione Programmatica via REST API

A partire da marzo 2025, GitHub ha aggiunto il supporto REST API per gli Issue Types:

```bash
# Listare gli issue types dell'organizzazione
gh api orgs/{org}/issue-types

# Creare un nuovo issue type
gh api orgs/{org}/issue-types -X POST \
  -f name="Epic" \
  -f description="Iniziativa di alto livello con sub-issues" \
  -f color="0052CC" \
  -F is_enabled=true

# Aggiornare un issue type
gh api orgs/{org}/issue-types/{type_id} -X PATCH \
  -f name="Epic" \
  -f description="Descrizione aggiornata"

# Eliminare un issue type
gh api orgs/{org}/issue-types/{type_id} -X DELETE

# Impostare il tipo su una issue specifica
gh api repos/{owner}/{repo}/issues/42 -X PATCH \
  -f issue_type="Bug"
```

### Impostazione Programmatica del Tipo

Per impostare il tipo su una issue tramite script:

```bash
# Trovare l'ID del tipo desiderato
TYPE_ID=$(gh api orgs/{org}/issue-types \
  --jq '.[] | select(.name == "Bug") | .id')

# Applicare il tipo a un'issue
gh api repos/{owner}/{repo}/issues/42 -X PATCH \
  --field issue_type="$TYPE_ID"
```

### Filtraggio per Tipo in Projects v2

Nelle viste di Projects v2, è possibile filtrare e raggruppare gli item per tipo di issue, permettendo viste come "tutti i Bug aperti" o "tutte le Feature in progress". Questo è particolarmente utile nella vista Board per separare il backlog dei bug dalla roadmap delle feature.

### Limitazioni Attuali

- I tipi sono definiti solo a livello organizzazione, non per singolo repository.
- I repository personali (non organizzazione) non supportano ancora i tipi personalizzati.
- Non esiste una UI per mappare automaticamente un template YAML a un tipo specifico (la mappatura è manuale).

---

## Sub-Issues e Gerarchia del Lavoro

Le **sub-issues** (GA aprile 2025) rappresentano il sistema ufficiale di GitHub per creare gerarchie di lavoro parent-child. Sostituiscono le tasklist (deprecate il 30 aprile 2025) e offrono un'esperienza integrata nella UI delle issue.

### Creare Sub-Issues

Le sub-issues si creano dalla sezione dedicata nell'issue parent, accessibile tramite il pulsante "Add sub-issue" nella UI oppure via API:

```bash
# Aggiungere una sub-issue a una issue parent
gh api repos/{owner}/{repo}/issues/100/sub_issues -X POST \
  -f sub_issue_id="$(gh api repos/{owner}/{repo}/issues/101 --jq '.id')"

# Creare una nuova issue e aggiungerla come sub-issue
gh issue create --title "Implementare login OAuth2" \
  --body "Sub-task dell'issue #100" \
  --label "type:task" \
  --assignee "dev-1"
# Poi aggiungere come sub-issue dalla UI o via API

# Rimuovere una sub-issue
gh api repos/{owner}/{repo}/issues/100/sub_issues/{sub_issue_id} -X DELETE
```

### Gerarchia Multi-Livello

Le sub-issues supportano fino a **otto livelli di gerarchia**, permettendo la decomposizione di lavoro complesso:

```
Epic: Riprogettazione Sistema di Autenticazione (#100)
├── Feature: OAuth2 Provider (#101)
│   ├── Task: Implementare flow Authorization Code (#110)
│   ├── Task: Implementare refresh token (#111)
│   └── Task: Aggiungere provider Google (#112)
├── Feature: MFA (Multi-Factor Authentication) (#102)
│   ├── Task: TOTP (Time-based OTP) (#120)
│   ├── Task: WebAuthn/FIDO2 (#121)
│   └── Task: Recovery codes (#122)
├── Feature: Session Management (#103)
│   ├── Task: Token rotation (#130)
│   └── Task: Device tracking (#131)
└── Task: Documentazione API autenticazione (#104)
```

### Progresso Aggregato

L'issue parent mostra automaticamente una barra di progresso basata sulle sub-issues completate. Nelle viste di Projects v2, il progresso è visibile direttamente nella riga dell'item, facilitando il monitoraggio dello stato delle epiche.

### Conversione da Checklist a Sub-Issues

A partire da febbraio 2025, è possibile convertire direttamente gli item di una checklist Markdown in sub-issues. Dalla UI, selezionare un item della checklist e cliccare "Convert to sub-issue". Questo crea una nuova issue con il testo dell'item come titolo e la collega automaticamente come sub-issue.

### Pattern di Utilizzo delle Sub-Issues

**Pattern 1 — Epic Decomposition:**
L'issue di livello più alto descrive l'obiettivo di business. Le sub-issues di primo livello rappresentano le feature necessarie. Le sub-issues di secondo livello sono i task implementativi.

**Pattern 2 — Incident Response:**
L'issue parent traccia l'incidente. Le sub-issues tracciano le azioni: investigazione, fix, comunicazione, post-mortem.

**Pattern 3 — Release Checklist:**
L'issue parent rappresenta la release. Le sub-issues rappresentano ogni step della release checklist: code freeze, QA, staging deploy, prod deploy, smoke test, announcement.

---

## GitHub Projects v2

### Creare e Configurare un Progetto

GitHub Projects v2 è un sistema di gestione progetto flessibile integrato con Issues e Pull Requests.

```bash
# Creare un progetto
gh project create --title "Sprint 2024-Q1" --owner "@me"

# Creare un progetto per un'organizzazione
gh project create --title "Product Roadmap" --owner "my-org"

# Listare i progetti
gh project list --owner "@me"

# Aggiungere un'issue a un progetto
gh project item-add <project-number> --owner "@me" --url https://github.com/org/repo/issues/42
```

### Views (Viste)

Projects v2 supporta diverse viste per organizzare gli stessi dati in modi diversi:

1. **Table View**: Vista tabulare simile a un foglio di calcolo
2. **Board View**: Vista Kanban con colonne per stato
3. **Roadmap View**: Vista timeline per la pianificazione temporale

### Custom Fields

```bash
# Aggiungere campi personalizzati
# Tramite UI: Project Settings > Custom fields

# Tipi di campi disponibili:
# - Text: campo di testo libero
# - Number: campo numerico
# - Date: selettore di data
# - Single select: dropdown con opzioni predefinite
# - Iteration: per sprint/iterazioni con date

# Esempio di configurazione:
# Campo: "Sprint" (Iteration, 2 settimane)
# Campo: "Story Points" (Number)
# Campo: "Team" (Single select: Frontend, Backend, DevOps)
# Campo: "Priority" (Single select: P0, P1, P2, P3)
```

### Automazioni Built-in

Projects v2 offre automazioni per aggiornare automaticamente lo stato degli item:

```yaml
# Automazioni disponibili (configurabili nella UI):

# Quando un'issue viene aggiunta al progetto:
# → Imposta stato a "Triage"

# Quando una PR viene aperta:
# → Imposta stato a "In Progress"

# Quando un'issue viene chiusa:
# → Imposta stato a "Done"

# Quando una PR viene mergiata:
# → Imposta stato a "Done"

# Quando una PR viene chiusa senza merge:
# → Imposta stato a "Archived"
```

### Workflow Automatizzati con GitHub Actions

```yaml
# .github/workflows/project-automation.yml
name: Auto-add to Project

on:
  issues:
    types: [opened]
  pull_request:
    types: [opened]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v0.5.0
        with:
          project-url: https://github.com/orgs/my-org/projects/1
          github-token: ${{ secrets.PROJECT_TOKEN }}
          labeled: "bug,enhancement"      # Solo issue/PR con queste label
          label-operator: OR
```

### Workflow Avanzati: Aggiornamento Stato nel Project

```yaml
# .github/workflows/project-status-update.yml
name: Update Project Item Status

on:
  pull_request:
    types: [opened, closed, converted_to_draft, ready_for_review]

env:
  PROJECT_NUMBER: 1
  ORG: my-org

jobs:
  update-status:
    runs-on: ubuntu-latest
    steps:
      - name: Get Project Data
        env:
          GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
        run: |
          # Ottenere l'ID del progetto
          PROJECT_ID=$(gh api graphql -f query='
            query($org: String!, $number: Int!) {
              organization(login: $org) {
                projectV2(number: $number) {
                  id
                  fields(first: 20) {
                    nodes {
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options { id name }
                      }
                    }
                  }
                }
              }
            }' -f org="$ORG" -F number="$PROJECT_NUMBER" \
            --jq '.data.organization.projectV2.id')
          echo "PROJECT_ID=$PROJECT_ID" >> "$GITHUB_ENV"

      - name: Set Status Based on PR Event
        env:
          GH_TOKEN: ${{ secrets.PROJECT_TOKEN }}
        run: |
          case "${{ github.event.action }}" in
            opened|ready_for_review)
              STATUS="In Review"
              ;;
            converted_to_draft)
              STATUS="In Progress"
              ;;
            closed)
              if [ "${{ github.event.pull_request.merged }}" = "true" ]; then
                STATUS="Done"
              else
                STATUS="Cancelled"
              fi
              ;;
          esac
          echo "Setting status to: $STATUS"
          # Qui seguirebbe la mutation GraphQL per aggiornare lo stato
```

### Filtri e Raggruppamenti nelle Viste

Le viste di Projects v2 supportano filtri potenti per organizzare gli item:

```
# Filtri nella vista Table o Board

# Per stato
status:"In Progress"

# Per label
label:bug

# Per assegnatario
assignee:username

# Per milestone
milestone:"v2.1.0"

# Per repository (utile in progetti cross-repo)
repo:org/frontend

# Per tipo di issue (GA 2025)
type:Bug

# Per iterazione/sprint
iteration:"Sprint 42"

# Combinazioni con operatori
status:"In Progress",assignee:@me
label:bug,-label:wontfix
no:assignee,label:needs-triage

# Per campi custom
priority:P0
team:Backend

# Per data
created:>2025-01-01
updated:<2025-06-01
```

### Slicing nelle Viste Board

Nella vista Board, il **slicing** permette di dividere la board in corsie orizzontali basate su un campo. Ad esempio, uno slice per `Team` mostra corsie separate per Frontend, Backend e DevOps, ciascuna con le proprie colonne di stato.

### Vista Roadmap: Configurazione Avanzata

La vista Roadmap visualizza gli item su una timeline, con supporto per:

- **Date field**: campo data utilizzato per posizionare gli item sulla timeline
- **Zoom level**: giorno, settimana, mese, trimestre
- **Raggruppamento**: per milestone, iterazione, team o qualsiasi campo single-select
- **Dipendenze visive**: le relazioni tra item sono visualizzate con frecce

```
# Configurazione vista Roadmap (tramite UI)
# 1. Layout: Roadmap
# 2. Date field: Start Date / Target Date
# 3. Group by: Milestone
# 4. Zoom: Month
# 5. Markers: Today line attiva
```

---

## Projects v2: API GraphQL e Automazione Avanzata

L'API GraphQL di GitHub è l'interfaccia primaria per l'automazione di Projects v2. Consente operazioni complete: creare progetti, aggiungere item, aggiornare campi custom, gestire viste.

### Autenticazione e Prerequisiti

```bash
# Il token deve avere lo scope "project" (read:project per le query,
# project per le mutation)

# Verificare i permessi del token
gh auth status

# Se necessario, aggiungere lo scope
gh auth refresh -s project
```

### Query: Ottenere i Dati del Progetto

```graphql
# Ottenere il progetto con tutti i campi e le opzioni
query GetProject($org: String!, $number: Int!) {
  organization(login: $org) {
    projectV2(number: $number) {
      id
      title
      shortDescription
      url
      closed
      items(first: 100) {
        totalCount
        nodes {
          id
          content {
            ... on Issue {
              title
              number
              state
              url
              labels(first: 10) {
                nodes { name }
              }
              assignees(first: 5) {
                nodes { login }
              }
            }
            ... on PullRequest {
              title
              number
              state
              url
            }
            ... on DraftIssue {
              title
              body
            }
          }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldIterationValue {
                title
                startDate
                duration
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
      fields(first: 20) {
        nodes {
          ... on ProjectV2Field {
            id
            name
            dataType
          }
          ... on ProjectV2SingleSelectField {
            id
            name
            options { id name }
          }
          ... on ProjectV2IterationField {
            id
            name
            configuration {
              iterations { id title startDate duration }
              completedIterations { id title startDate duration }
            }
          }
        }
      }
    }
  }
}
```

### Mutation: Aggiungere un Item al Progetto

```graphql
# Aggiungere un'issue o PR esistente al progetto
mutation AddItemToProject($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {
    projectId: $projectId
    contentId: $contentId
  }) {
    item {
      id
    }
  }
}
```

```bash
# Esecuzione dalla CLI
ISSUE_NODE_ID=$(gh api repos/{owner}/{repo}/issues/42 --jq '.node_id')

gh api graphql -f query='
  mutation($projectId: ID!, $contentId: ID!) {
    addProjectV2ItemById(input: {
      projectId: $projectId
      contentId: $contentId
    }) {
      item { id }
    }
  }' -f projectId="$PROJECT_ID" -f contentId="$ISSUE_NODE_ID"
```

### Mutation: Aggiornare un Campo Single-Select (Status)

```graphql
mutation UpdateItemStatus(
  $projectId: ID!
  $itemId: ID!
  $fieldId: ID!
  $optionId: String!
) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId
    itemId: $itemId
    fieldId: $fieldId
    value: { singleSelectOptionId: $optionId }
  }) {
    projectV2Item {
      id
    }
  }
}
```

### Mutation: Aggiornare Campi Multipli con Alias

```graphql
# Aggiornare stato, priorità e data in una singola richiesta
mutation UpdateMultipleFields(
  $project: ID!
  $item: ID!
  $statusField: ID!
  $statusValue: String!
  $priorityField: ID!
  $priorityValue: String!
  $dateField: ID!
  $dateValue: Date!
  $pointsField: ID!
  $pointsValue: Float!
) {
  set_status: updateProjectV2ItemFieldValue(input: {
    projectId: $project
    itemId: $item
    fieldId: $statusField
    value: { singleSelectOptionId: $statusValue }
  }) { projectV2Item { id } }

  set_priority: updateProjectV2ItemFieldValue(input: {
    projectId: $project
    itemId: $item
    fieldId: $priorityField
    value: { singleSelectOptionId: $priorityValue }
  }) { projectV2Item { id } }

  set_date: updateProjectV2ItemFieldValue(input: {
    projectId: $project
    itemId: $item
    fieldId: $dateField
    value: { date: $dateValue }
  }) { projectV2Item { id } }

  set_points: updateProjectV2ItemFieldValue(input: {
    projectId: $project
    itemId: $item
    fieldId: $pointsField
    value: { number: $pointsValue }
  }) { projectV2Item { id } }
}
```

### Mutation: Creare un Draft Issue nel Progetto

```graphql
mutation AddDraftIssue($projectId: ID!) {
  addProjectV2DraftIssue(input: {
    projectId: $projectId
    title: "Investigare latenza API endpoint /users"
    body: "La latenza media è salita da 50ms a 200ms nell'ultima settimana."
  }) {
    projectV2Item {
      id
    }
  }
}
```

### Mutation: Archiviare un Item

```graphql
mutation ArchiveItem($projectId: ID!, $itemId: ID!) {
  archiveProjectV2Item(input: {
    projectId: $projectId
    itemId: $itemId
  }) {
    item { id }
  }
}
```

### Script Completo: Sincronizzazione Sprint

```bash
#!/usr/bin/env bash
# move-to-next-sprint.sh — Sposta le issue non completate al prossimo sprint

set -euo pipefail

ORG="my-org"
PROJECT_NUMBER=1

# Ottenere i dati del progetto
PROJECT_DATA=$(gh api graphql -f query='
  query($org: String!, $number: Int!) {
    organization(login: $org) {
      projectV2(number: $number) {
        id
        fields(first: 20) {
          nodes {
            ... on ProjectV2IterationField {
              id
              name
              configuration {
                iterations { id title startDate }
              }
            }
            ... on ProjectV2SingleSelectField {
              id
              name
              options { id name }
            }
          }
        }
        items(first: 100) {
          nodes {
            id
            fieldValues(first: 10) {
              nodes {
                ... on ProjectV2ItemFieldSingleSelectValue {
                  name
                  field { ... on ProjectV2FieldCommon { name } }
                }
                ... on ProjectV2ItemFieldIterationValue {
                  title
                  field { ... on ProjectV2FieldCommon { name } }
                }
              }
            }
          }
        }
      }
    }
  }' -f org="$ORG" -F number="$PROJECT_NUMBER")

# Estrarre gli ID necessari
PROJECT_ID=$(echo "$PROJECT_DATA" | jq -r '.data.organization.projectV2.id')
ITERATION_FIELD_ID=$(echo "$PROJECT_DATA" | \
  jq -r '.data.organization.projectV2.fields.nodes[]
    | select(.name == "Sprint") | .id')
NEXT_SPRINT_ID=$(echo "$PROJECT_DATA" | \
  jq -r '.data.organization.projectV2.fields.nodes[]
    | select(.name == "Sprint")
    | .configuration.iterations[0].id')

# Trovare gli item non completati dello sprint corrente
echo "$PROJECT_DATA" | jq -r '
  .data.organization.projectV2.items.nodes[]
  | select(.fieldValues.nodes[]
    | select(.field.name == "Status" and .name != "Done"))
  | .id' | while read -r ITEM_ID; do

  echo "Spostamento item $ITEM_ID al prossimo sprint..."
  gh api graphql -f query='
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $iterationId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId
        itemId: $itemId
        fieldId: $fieldId
        value: { iterationId: $iterationId }
      }) { projectV2Item { id } }
    }' \
    -f projectId="$PROJECT_ID" \
    -f itemId="$ITEM_ID" \
    -f fieldId="$ITERATION_FIELD_ID" \
    -f iterationId="$NEXT_SPRINT_ID"
done

echo "Sincronizzazione sprint completata."
```

### Limitazioni dell'API GraphQL per Projects v2

È importante conoscere le limitazioni dell'API per evitare errori:

1. **Proprietà vs Campi Custom**: non è possibile aggiornare Assignees, Labels, Milestone o Repository tramite `updateProjectV2ItemFieldValue`, perché queste sono proprietà dell'issue/PR, non del project item.
2. **Operazioni separate**: non si può aggiungere un item e aggiornarne i campi nella stessa mutation; occorre prima `addProjectV2ItemById`, poi `updateProjectV2ItemFieldValue`.
3. **Rate limiting**: le query GraphQL sono soggette al rate limit di GitHub (5.000 punti/ora per token autenticato).
4. **Paginazione**: i risultati sono paginati. Per progetti grandi, è necessario gestire i cursor di paginazione.
5. **Nessun webhook nativo per cambi di campo custom**: i webhook coprono eventi base (item added, removed) ma non i cambi di campi custom specifici.

---

## Projects v2: Insights, Chart e Status Updates

### Grafici e Metriche

Projects v2 offre una sezione **Insights** con grafici configurabili per monitorare lo stato del progetto.

#### Tipi di Grafico

| Tipo | Descrizione | Uso tipico |
|---|---|---|
| **Current chart** | Snapshot dell'attuale distribuzione degli item | Distribuzione per stato, per assegnatario, per priorità |
| **Historical chart (Burn-up)** | Andamento nel tempo degli item completati | Monitoraggio progresso verso un obiettivo |

#### Creare un Grafico Current

Dalla tab "Insights" del progetto:

1. Cliccare "New chart"
2. Selezionare il tipo "Bar" o "Stacked bar" o "Column"
3. Configurare:
   - **X-axis**: il campo da usare come asse X (es. Status, Assignee, Priority)
   - **Group by**: raggruppamento opzionale (es. raggruppare per Team nel grafico per Status)
   - **Filter**: filtrare gli item (es. solo issue, solo sprint corrente)
4. Dare un nome descrittivo al grafico

#### Esempio di Grafici Utili

```
# Grafico 1: Distribuzione per Status
# Tipo: Stacked bar
# X-axis: Status
# Group by: Priority
# → Mostra quanti item per stato, suddivisi per priorità

# Grafico 2: Carico di lavoro per sviluppatore
# Tipo: Bar
# X-axis: Assignee
# Group by: Status
# Filter: iteration:@current
# → Mostra quanti item ha ciascun sviluppatore nello sprint corrente

# Grafico 3: Burn-up sprint
# Tipo: Historical (Burn up)
# Filter: iteration:@current
# → Mostra il progresso nel tempo dello sprint

# Grafico 4: Bug backlog trend
# Tipo: Historical (Burn up)
# Filter: label:bug
# → Mostra l'andamento del backlog bug nel tempo
```

### Status Updates

I **status updates** permettono di condividere aggiornamenti di alto livello sullo stato del progetto con gli stakeholder:

```
# Dalla UI del progetto:
# 1. Cliccare "Add update"
# 2. Selezionare lo stato: On track, At risk, Off track
# 3. Impostare Start date e Target date
# 4. Scrivere un aggiornamento testuale
# 5. Menzionare utenti o team con @mention
# 6. Pubblicare

# Gli aggiornamenti sono visibili a chiunque abbia accesso in lettura
# al progetto e gli utenti possono iscriversi per ricevere notifiche.
```

Esempio di status update strutturato:

```markdown
## Status Update — Sprint 42 (settimana 3/3)

**Stato:** 🟡 At Risk

**Progresso:** 75% (15/20 issue completate)

**Rischi:**
- La migrazione del database (#234) ha richiesto 3 giorni extra
- Il team frontend è ridotto per ferie

**Prossimi passi:**
- @backend-team completare l'integrazione API entro venerdì
- @frontend-team allineare le chiamate con la nuova API

**Decisioni necessarie:**
- Confermare se posticipare il deploy a lunedì (@product-manager)
```

---

## Pull Requests Avanzate

### Draft Pull Requests

Le draft PR indicano che il lavoro è in corso e non è pronto per la review:

```bash
# Creare una draft PR
gh pr create --title "feat: implementare OAuth2" --draft

# Convertire una draft in PR pronta
gh pr ready <pr-number>

# Convertire una PR pronta in draft
gh api repos/{owner}/{repo}/pulls/<pr-number> -X PATCH -F draft=true
```

### Pull Request Templates

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->

## Descrizione

<!-- Descrizione chiara delle modifiche -->

## Tipo di Modifica

- [ ] Bug fix (modifica non breaking che risolve un problema)
- [ ] Nuova feature (modifica non breaking che aggiunge funzionalità)
- [ ] Breaking change (modifica che altera il comportamento esistente)
- [ ] Refactoring (modifica che non altera il comportamento)
- [ ] Documentazione
- [ ] CI/CD

## Issue Correlate

<!-- Collegare le issue: Fixes #123, Relates to #456 -->

## Come È Stato Testato?

<!-- Descrivere i test eseguiti -->

- [ ] Test unitari
- [ ] Test di integrazione
- [ ] Test manuali

## Checklist

- [ ] Il codice segue le convenzioni del progetto
- [ ] Ho aggiunto test che coprono le modifiche
- [ ] Tutti i test esistenti passano
- [ ] Ho aggiornato la documentazione (se necessario)
- [ ] Ho verificato che non ci siano regressioni
- [ ] Ho verificato che non ci siano segreti nel codice

## Screenshots (se applicabile)

<!-- Aggiungere screenshots per modifiche UI -->
```

### Suggested Changes nelle Review

Durante la review, i reviewer possono suggerire modifiche specifiche direttamente nel codice:

```markdown
<!-- In un commento di review -->
```suggestion
const result = items.filter(item => item.active)
  .map(item => item.name)
  .sort();
```

<!-- Il suggerimento può essere accettato con un click ("Commit suggestion") -->
<!-- Più suggerimenti possono essere raggruppati in un singolo commit ("Add suggestion to batch") -->
```

### Auto-Merge

L'auto-merge permette di mergere automaticamente una PR quando tutti i required checks passano e tutte le review sono approvate:

```bash
# Abilitare auto-merge su una PR
gh pr merge <pr-number> --auto --squash

# Con merge commit
gh pr merge <pr-number> --auto --merge

# Con rebase
gh pr merge <pr-number> --auto --rebase

# Disabilitare auto-merge
gh pr merge <pr-number> --disable-auto
```

---

## Merge Queue

La **merge queue** è un meccanismo che automatizza il merge delle pull request garantendo che ogni PR venga testata contro la versione più aggiornata del branch target, incluse le PR già in coda. Questo elimina il problema delle "merge races" dove due PR passano i check individualmente ma sono incompatibili tra loro.

### Come Funziona

1. Una PR passa tutti i required checks e ottiene le approvazioni necessarie.
2. L'autore (o un utente con accesso write) aggiunge la PR alla merge queue.
3. La merge queue crea un branch temporaneo che include il branch target aggiornato + le modifiche della PR + le modifiche delle PR precedenti in coda.
4. I required checks vengono eseguiti su questo branch temporaneo.
5. Se tutti i check passano, la PR viene mergiata automaticamente.
6. Se un check fallisce, la PR viene rimossa dalla coda e le PR successive vengono ri-testate.

### Configurazione

```bash
# Prerequisiti:
# 1. Branch protection rule attiva sul branch target
# 2. Required status checks configurati
# 3. Merge queue abilitata nelle branch protection rules

# Abilitare la merge queue (richiede branch protection)
# Settings > Branches > Branch protection rule > Require merge queue

# Parametri configurabili:
# - Merge method: merge, squash, rebase
# - Build concurrency: numero massimo di PR testate in parallelo (1-100)
# - Minimum/Maximum group size: dimensione del batch di PR
# - Wait time: tempo di attesa prima di avviare il build (0-360 minuti)
# - Status check timeout: timeout per i check (5-360 minuti)
```

### Aggiungere una PR alla Merge Queue

```bash
# Aggiungere una PR alla merge queue dalla CLI
gh pr merge <pr-number> --merge-queue

# Verificare lo stato della merge queue
gh api repos/{owner}/{repo}/merge-queue

# Rimuovere una PR dalla merge queue
# (dalla UI: pulsante "Remove from queue")
```

### Merge Queue con Branch Protection Rules

```yaml
# Configurazione tipica branch protection per merge queue:
# Branch: main
# Settings:
#   - Require a pull request before merging: ON
#     - Required approvals: 2
#     - Dismiss stale pull request approvals: ON
#   - Require status checks to pass before merging: ON
#     - Status checks: ci/build, ci/test, ci/lint
#     - Require branches to be up to date: OFF (la merge queue gestisce questo)
#   - Require merge queue: ON
#     - Build concurrency: 5
#     - Merge method: squash
```

### Vantaggi della Merge Queue

| Senza Merge Queue | Con Merge Queue |
|---|---|
| Ogni sviluppatore deve aggiornare manualmente il branch prima del merge | La coda aggiorna automaticamente e testa contro la versione più recente |
| PR incompatibili possono essere mergiati se i check passano individualmente | Le incompatibilità vengono rilevate prima del merge |
| Il merge diventa un'operazione manuale soggetta a errore | Il merge è completamente automatizzato dopo l'approvazione |
| Su branch ad alto traffico, "merge races" frequenti | Nessuna race condition, ordine garantito |

---

## Code Review Best Practices

### Per il Reviewer

1. **Comprendere il contesto**: Leggere la descrizione della PR, le issue correlate e la discussione prima di guardare il codice.

2. **Review strutturata**:
   - Prima passata: comprendere l'architettura e il design delle modifiche
   - Seconda passata: verificare la correttezza logica
   - Terza passata: dettagli (naming, stile, edge cases)

3. **Feedback costruttivo**:
   - Distinguere tra suggerimenti e richieste obbligatorie
   - Usare prefissi: `nit:` per nitpick, `suggestion:` per suggerimenti, `question:` per domande
   - Proporre alternative, non solo criticare

4. **Tempestività**: Completare le review entro 24 ore lavorative. Una PR che aspetta review per giorni blocca il lavoro.

5. **Scope**: Focalizzarsi sulle modifiche della PR. Non richiedere refactoring di codice pre-esistente non correlato.

### Per l'Autore della PR

1. **PR piccole**: Idealmente meno di 400 righe modificate. PR grandi hanno review di bassa qualità.

2. **Descrizione completa**: Spiegare il perché delle modifiche, non solo il cosa. Includere contesto e decisioni di design.

3. **Self-review**: Rivedere il proprio codice prima di richiedere la review altrui. Rimuovere codice di debug, commenti temporanei e import inutilizzati.

4. **Rispondere a tutti i commenti**: Ogni commento merita una risposta, anche solo "Done" o "Good point, fixed".

5. **Non pushare durante la review**: Se possibile, attendere il completamento della review prima di pushare nuove modifiche.

### Livelli di Approvazione

```
# Modello di review a più livelli

## Level 1: Peer Review (obbligatorio)
- Uno sviluppatore del team
- Focus: logica, test, stile

## Level 2: Code Owner Review (per aree critiche)
- Definito in CODEOWNERS
- Focus: architettura, compatibilità, sicurezza

## Level 3: Security Review (per modifiche sensibili)
- Team di sicurezza
- Focus: vulnerabilità, gestione dati sensibili
```

### Metriche di Code Review

Monitorare le metriche di code review aiuta a identificare colli di bottiglia e migliorare il processo:

```bash
# Tempo medio di prima review (in ore)
gh pr list --state merged --json number,createdAt,reviews \
  --limit 50 -q '
  [.[] | select(.reviews | length > 0) |
   { pr: .number,
     hours: ((.reviews[0].submittedAt | fromdateiso8601) -
             (.createdAt | fromdateiso8601)) / 3600
   }] | (map(.hours) | add / length | . * 10 | round / 10)'

# PR che aspettano review da più di 24 ore
gh pr list --state open --json number,title,createdAt,reviewRequests \
  -q '.[] | select(.reviewRequests | length > 0) |
      select((.createdAt | fromdateiso8601) < (now - 86400)) |
      {number, title}'
```

### Review Comments: Convenzioni di Prefisso

Un sistema di prefissi nei commenti di review rende chiara l'intenzione e la severità del feedback:

| Prefisso | Significato | Azione richiesta |
|---|---|---|
| `blocking:` | Problema che impedisce il merge | Deve essere risolto prima del merge |
| `nit:` | Nitpick, dettaglio minore | Opzionale, facoltativo risolvere |
| `suggestion:` | Proposta di alternativa | Valutare l'adozione |
| `question:` | Richiesta di chiarimento | Rispondere con spiegazione |
| `praise:` | Complimento per codice ben scritto | Nessuna azione, rinforzo positivo |
| `thought:` | Riflessione senza azione richiesta | Opzionale, spunto per il futuro |
| `todo:` | Azione da fare (possibilmente in issue separata) | Creare issue di follow-up |
| `security:` | Potenziale problema di sicurezza | Valutare con attenzione, blocca se critico |

Esempio di commento con prefisso:

```markdown
`nit:` Il nome della variabile `d` è poco descrittivo. Suggerisco `durationMs` per chiarezza.

`blocking:` Questa query SQL è vulnerabile a SQL injection.
Usare parametri preparati:
```suggestion
const result = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
```

`question:` Perché usiamo `setTimeout` qui invece di un debounce?
C'è un requisito specifico per l'esecuzione ritardata?
```

### Code Review Automation con GitHub Actions

```yaml
# .github/workflows/auto-review-checks.yml
name: PR Quality Checks

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  pr-size-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check PR Size
        run: |
          ADDITIONS=$(gh pr view ${{ github.event.pull_request.number }} \
            --json additions -q '.additions')
          DELETIONS=$(gh pr view ${{ github.event.pull_request.number }} \
            --json deletions -q '.deletions')
          TOTAL=$((ADDITIONS + DELETIONS))

          if [ "$TOTAL" -gt 800 ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "⚠️ **PR grande** ($TOTAL righe modificate).
              Le PR > 800 righe hanno review di bassa qualità.
              Considerare la suddivisione in PR più piccole."
          elif [ "$TOTAL" -gt 400 ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "📏 PR di dimensione media ($TOTAL righe).
              Accettabile, ma la suddivisione migliora la qualità della review."
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  checklist-validation:
    runs-on: ubuntu-latest
    steps:
      - name: Verify PR Template Checklist
        uses: actions/github-script@v7
        with:
          script: |
            const pr = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number
            });
            const body = pr.data.body || '';
            const unchecked = (body.match(/- \[ \]/g) || []).length;
            if (unchecked > 0) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: `⚠️ La PR ha **${unchecked}** item della checklist non completati. Verificare prima di richiedere la review.`
              });
            }
```

### Copilot Code Review

A partire dal 2025, GitHub Copilot offre una funzionalita di **code review automatica** che analizza il diff delle pull request e pubblica commenti inline, in modo analogo a un reviewer umano. Questa funzionalita e disponibile per gli utenti con licenza GitHub Copilot Enterprise o Business e puo essere configurata sia per richieste manuali sia per esecuzione automatica su ogni PR.

#### Abilitazione della Review Automatica

La review automatica si configura tramite i **repository rulesets**. A partire da settembre 2025, la regola "Automatically request Copilot code review" e diventata un **repository rule indipendente**, separata dal requisito "Require a pull request before merging". Questo consente di adottare le review automatiche senza dover necessariamente imporre policy di merge gating.

```
# Percorso di configurazione nella UI:
# Repository Settings > Code and automation > Rules > Rulesets
# → Aggiungere la regola: "Automatically request Copilot code review"
#
# Sotto-impostazioni disponibili:
# - Run on each push: riesegue la review quando vengono pushati nuovi commit
# - Run on drafts: esegue la review anche sulle draft PR
```

La regola indipendente consente scenari flessibili: ad esempio, un repository che non richiede PR obbligatorie (per progetti interni o sperimentali) puo comunque beneficiare della review automatica su ogni PR aperta.

#### Istruzioni Personalizzate

Copilot code review supporta istruzioni personalizzate tramite il file `.github/copilot-code-review-instructions.md`. Questo file permette di guidare il comportamento del reviewer AI in base alle convenzioni e alle priorita del progetto:

```markdown
<!-- .github/copilot-code-review-instructions.md -->

## Priorita di Review

- Commentare solo quando la confidenza di un problema reale e superiore all'80%.
- Focalizzarsi su bug, vulnerabilita di sicurezza e violazioni delle convenzioni del progetto.
- Non commentare su preferenze stilistiche (formattazione, naming soggettivo) a meno che non violino le regole del progetto.

## Regole Specifiche

- Segnalare query SQL costruite con concatenazione di stringhe (rischio SQL injection).
- Verificare che le API endpoint abbiano validazione dell'input.
- Segnalare l'uso di `innerHTML` o `dangerouslySetInnerHTML` senza sanitizzazione.
- Verificare che i secret non siano hardcoded nel codice sorgente.
- Controllare che le funzioni async gestiscano correttamente gli errori (try/catch o .catch()).

## Contesto del Progetto

- Il backend usa Node.js con Express e TypeScript.
- Il frontend usa React con Next.js.
- Lo stile di codice segue le convenzioni definite in `.eslintrc.js`.
- I test sono scritti con Jest e devono seguire il pattern AAA (Arrange-Act-Assert).
```

Le istruzioni possono essere sia globali (per tutto il repository) sia **path-specific**, permettendo regole diverse per aree diverse del codebase (ad esempio, regole piu stringenti per il codice di autenticazione).

#### Limitazioni Importanti

Copilot code review ha una limitazione critica per i workflow di approvazione: la review di Copilot pubblica sempre un commento di tipo **"Comment"**, mai "Approve" o "Request changes". Questo significa che:

- Le review di Copilot **non contano** nel requisito di approvazioni obbligatorie per il merge.
- Le review di Copilot **non bloccano** il merge della PR.
- Copilot **non puo sostituire** i reviewer umani nei workflow con required approvals.

In pratica, Copilot code review funge da "primo filtro" che identifica problemi evidenti prima che il reviewer umano inizi la propria revisione, riducendo il carico cognitivo del reviewer e accelerando il ciclo di feedback.

#### Richiesta Manuale di Review

Oltre alla modalita automatica, e possibile richiedere una review di Copilot manualmente dalla UI della PR, aggiungendo "Copilot" come reviewer dalla sezione "Reviewers". La review viene eseguita in pochi secondi e i commenti appaiono inline come quelli di un reviewer umano.

```bash
# Dalla CLI, la richiesta manuale non e ancora supportata direttamente.
# Utilizzare la UI: PR > Reviewers > Copilot

# Verificare lo stato della review di Copilot
gh pr view <pr-number> --json reviews \
  --jq '.reviews[] | select(.author.login == "copilot-pull-request-reviewer")'
```

#### Best Practices per Copilot Code Review

1. **Istruzioni concise**: limitare il file di istruzioni a massimo 1.000 righe per garantire che Copilot le elabori completamente.
2. **Regole azionabili**: preferire regole concrete ("segnala query SQL con concatenazione") a regole vaghe ("verifica la sicurezza").
3. **Complementarieta**: usare Copilot come primo filtro, non come sostituto del reviewer umano. Il valore e nella cattura di bug banali e violazioni di convenzioni.
4. **Feedback loop**: se Copilot produce falsi positivi ricorrenti, aggiornare le istruzioni per escludere quei pattern.
5. **Monitoraggio costi**: a partire da giugno 2026, le esecuzioni di Copilot code review consumano minuti di GitHub Actions. Monitorare l'utilizzo per evitare sorprese nella fatturazione.

---

## Discussions

### Categorie di Discussion

GitHub Discussions fornisce un forum strutturato per conversazioni che non sono bug o feature request:

```bash
# Le categorie predefinite includono:
# - Announcements: Annunci dal team (solo maintainer possono creare)
# - General: Discussioni generali
# - Ideas: Proposte e brainstorming
# - Polls: Sondaggi con opzioni di voto
# - Q&A: Domande con risposta marcabile come "Answer"
# - Show and Tell: Condivisione di progetti e risultati
```

### Uso Strategico delle Discussions

1. **Q&A per supporto**: Dirigere le domande di supporto nelle Discussions invece che nelle Issues
2. **RFC (Request for Comments)**: Usare le discussions per proposte di design prima di creare le issues
3. **Announcements per comunicazioni**: Release notes, breaking changes, roadmap updates
4. **Polls per decisioni**: Coinvolgere la community nelle decisioni di design

```bash
# Convertire un'issue in discussion (dalla UI)
# Issue > menu laterale > "Transfer to discussion"
# Selezionare la categoria appropriata

# Creare una discussion da CLI
gh api repos/{owner}/{repo}/discussions -X POST \
  -f title="RFC: Migrazione da REST a GraphQL" \
  -f body="## Proposta\n\nMigrare l'API pubblica da REST a GraphQL..." \
  -f category_id="CATEGORY_NODE_ID"
```

### Configurazione Avanzata delle Categorie

Le categorie possono essere personalizzate per riflettere le esigenze del progetto. Ogni repository o organizzazione supporta fino a 25 categorie, ciascuna con un formato specifico:

| Formato | Descrizione | Caso d'uso |
|---|---|---|
| **Open-ended** | Discussione libera, nessuna risposta "accettata" | General, Ideas, Show and Tell |
| **Question/Answer** | Una risposta può essere marcata come "Answer" | Q&A, Troubleshooting, How-to |
| **Announcement** | Solo i maintainer possono creare post, tutti possono commentare | Release notes, Breaking changes, Policy |
| **Poll** | Sondaggio con opzioni di voto | Decisioni di design, Preferenze community |

```bash
# Configurazione categorie raccomandata per un progetto software:

# 1. Announcements (Announcement format)
#    → Release notes, breaking changes, roadmap updates
#    → Solo maintainer possono creare, la community commenta

# 2. Q&A (Question/Answer format)
#    → Domande tecniche con risposta marcabile
#    → Alternativa a StackOverflow per il progetto

# 3. Ideas & RFCs (Open-ended format)
#    → Proposte di nuove funzionalità
#    → Request for Comments su decisioni di design

# 4. Show and Tell (Open-ended format)
#    → Condivisione di progetti costruiti con il software
#    → Demo, tutorial, integrazioni della community

# 5. Troubleshooting (Question/Answer format)
#    → Problemi di configurazione e setup
#    → Errori comuni e soluzioni

# 6. Polls (Poll format)
#    → Votazioni su decisioni di design
#    → Feedback su priorità delle feature

# 7. General (Open-ended format)
#    → Tutto ciò che non rientra nelle altre categorie
```

### Moderazione e Community Guidelines

```markdown
<!-- Esempio di post pinned in Announcements -->
# Linee Guida della Community

Benvenuto nelle Discussions del progetto! Ecco le regole:

## Prima di aprire una Discussion
1. **Cercare** se la domanda è già stata posta
2. **Scegliere la categoria giusta** (Q&A per domande, Ideas per proposte)
3. **Fornire contesto**: versione, OS, configurazione

## Formato Q&A
- Descrivere il problema chiaramente
- Includere codice rilevante in blocchi di codice
- Marcare la risposta accettata quando il problema è risolto

## Rispetto
- Seguire il [Code of Conduct](CODE_OF_CONDUCT.md)
- Essere costruttivi nelle critiche
- Ringraziare chi aiuta
```

### Discussions a Livello Organizzazione

Le Discussions possono essere abilitate a livello di organizzazione (non solo repository), creando un forum centralizzato per l'intera organizzazione. Questo è utile per:

- Comunicazioni cross-team
- Policy e procedure organizzative
- Decisioni che impattano più repository
- Onboarding di nuovi membri

```bash
# Abilitare le Discussions per l'organizzazione:
# Organization Settings > Discussions > Enable
# Selezionare il repository che ospiterà le Discussions dell'organizzazione
```

### Integrazione Discussions con Actions

È possibile automatizzare azioni basate sugli eventi delle Discussions:

```yaml
# .github/workflows/discussion-automation.yml
name: Discussion Automation

on:
  discussion:
    types: [created, answered]
  discussion_comment:
    types: [created]

jobs:
  welcome-new-discussion:
    if: github.event.action == 'created'
    runs-on: ubuntu-latest
    steps:
      - name: Welcome Message
        uses: peter-evans/create-or-update-comment@v4
        with:
          issue-number: ${{ github.event.discussion.number }}
          body: |
            Grazie per aver aperto questa discussione!

            Un maintainer risponderà il prima possibile.
            Nel frattempo, verifica che:
            - [ ] Hai cercato tra le discussioni esistenti
            - [ ] Hai fornito tutti i dettagli necessari

  notify-answered:
    if: github.event.action == 'answered'
    runs-on: ubuntu-latest
    steps:
      - name: Log Answered Discussion
        run: |
          echo "Discussion #${{ github.event.discussion.number }} answered"
          echo "Title: ${{ github.event.discussion.title }}"
          echo "Category: ${{ github.event.discussion.category.name }}"
```

---

## Wiki

### Configurazione e Uso

Il Wiki di GitHub è un repository Git separato associato al repository principale. Ogni pagina è un file Markdown.

```bash
# Clonare il wiki
git clone https://github.com/org/repo.wiki.git

# Il wiki è un repository Git standard
cd repo.wiki
ls
# Home.md
# Getting-Started.md
# API-Reference.md
# _Sidebar.md
# _Footer.md
```

### Struttura del Wiki

```markdown
<!-- _Sidebar.md - Navigazione laterale -->
**Navigazione**

* [[Home]]
* [[Getting Started]]
  * [[Installation]]
  * [[Configuration]]
* [[API Reference]]
  * [[Authentication]]
  * [[Endpoints]]
* [[Contributing]]
* [[FAQ]]

<!-- _Footer.md - Footer comune -->
---
[Home](Home) | [API](API-Reference) | [Contributing](Contributing)
```

### Wiki vs Documentation Site

| Aspetto | Wiki | Docs Site (Pages) |
|---------|------|-------------------|
| Editing | Browser o Git | Git only |
| Design | GitHub standard | Personalizzabile |
| Ricerca | Integrata | Dipende dal tool |
| Versionamento | Git | Git |
| Contributi | Semplice | Richiede PR |
| SEO | Limitato | Completo |
| Adatto per | Documentazione interna | Documentazione pubblica |

---

## CODEOWNERS e Review Assignment

### Review Assignment Automatico

Combinando CODEOWNERS con la configurazione del team, è possibile automatizzare l'assegnazione delle review:

```
# .github/CODEOWNERS
# L'ordine conta: l'ultimo pattern che matcha ha la precedenza

# Default: team di sviluppo
*                               @org/dev-team

# Frontend
/src/frontend/                  @org/frontend-team
/src/components/                @org/frontend-team

# Backend
/src/api/                       @org/backend-team
/src/services/                  @org/backend-team

# Infrastruttura
/terraform/                     @org/devops-team
/.github/workflows/             @org/devops-team
/Dockerfile                     @org/devops-team

# Sicurezza
/src/auth/                      @org/security-team
/src/crypto/                    @org/security-team
```

### Team Review Assignment

Nelle impostazioni del team su GitHub, è possibile configurare l'algoritmo di assegnazione:

1. **Round Robin**: Assegna ciclicamente ai membri del team
2. **Load Balance**: Assegna al membro con meno review pendenti

```bash
# Configurare la review assignment del team
# Settings > Organization > Teams > [team] > Code review
# - Enable auto assignment: On
# - Algorithm: Load balance
# - Number of reviewers: 2
# - Skip members: On (non assegnare a chi è in vacanza)
```

---

## Repository Rulesets e Required Reviewers

I **Repository Rulesets** (GA 2023, con aggiunte significative nel 2025-2026) rappresentano l'evoluzione delle branch protection rules. Offrono un sistema centralizzato per definire policy su branch e tag, con capacità avanzate rispetto alle regole di protezione tradizionali.

### Differenze tra Branch Protection Rules e Rulesets

| Aspetto | Branch Protection Rules | Repository Rulesets |
|---|---|---|
| Scope | Singolo branch o pattern | Branch, tag, o entrambi |
| Gestione | Per repository | Per repository o per organizzazione |
| Bypass | Solo per admin | Lista bypass esplicita (utenti, team, app) |
| Layering | Una regola per pattern | Più ruleset applicabili allo stesso branch |
| API | REST | REST con capacità avanzate |
| Required reviews | Per numero | Per numero + per team specifico (2025) |
| File path rules | Non disponibile | Pattern di file con negazione (2025) |

### Required Reviewer Rule (GA Febbraio 2026)

La **required reviewer rule** nei rulesets permette di richiedere l'approvazione da team specifici per file o percorsi specifici:

```yaml
# Esempio di configurazione ruleset (concettuale — la configurazione
# avviene tramite UI o API REST)

# Ruleset: "Security Review"
# Target: branches matching "main", "release/*"
# Rules:
#   Required reviewers:
#     - security-team must approve changes to:
#       - "src/auth/**"
#       - "src/crypto/**"
#       - "*.sql"
#       - "!*.test.sql"  # Negazione: i file test non richiedono review security
#     - data-team must approve changes to:
#       - "migrations/**"
#       - "src/models/**"
#   Minimum approvals: 2
```

```bash
# Creare un ruleset via API
gh api repos/{owner}/{repo}/rulesets -X POST \
  --input - <<'EOF'
{
  "name": "Production Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main", "refs/heads/release/*"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [
          { "context": "ci/build" },
          { "context": "ci/test" },
          { "context": "security/scan" }
        ],
        "strict_required_status_checks_policy": true
      }
    }
  ],
  "bypass_actors": [
    {
      "actor_id": 1,
      "actor_type": "RepositoryRole",
      "bypass_mode": "always"
    }
  ]
}
EOF

# Listare i rulesets del repository
gh api repos/{owner}/{repo}/rulesets

# Visualizzare un ruleset specifico
gh api repos/{owner}/{repo}/rulesets/{ruleset_id}
```

### CODEOWNERS vs Required Reviewer Rule

Le due funzionalità sono complementari:

- **CODEOWNERS** definisce la **proprietà** del codice. Quando un file viene modificato, il proprietario viene automaticamente richiesto come reviewer. Supporta utenti individuali.
- **Required Reviewer Rule** definisce la **policy di approvazione**. Specifica quali team DEVONO approvare prima del merge. Non supporta utenti individuali, solo team. Supporta pattern di negazione con `!`.

```
# CODEOWNERS — proprietà e richiesta automatica di review
/src/auth/          @org/security-team @alice
/src/payments/      @org/payments-team @bob

# Required Reviewer Rule — obbligo di approvazione
# Rule 1: security-team DEVE approvare /src/auth/**
# Rule 2: payments-team DEVE approvare /src/payments/**
# Rule 3: dba-team DEVE approvare *.sql, !*_test.sql
```

---

## IssueOps: Issues come Interfaccia di Automazione

**IssueOps** è un pattern che utilizza GitHub Issues e Pull Requests come interfaccia per attivare workflow automatizzati tramite GitHub Actions. Il nome richiama ChatOps ma usa le issue come mezzo di comunicazione.

### Principi Fondamentali

1. **Issue come trigger**: l'apertura di un'issue, un commento specifico, o un cambio di label attiva un workflow.
2. **Stato come macchina a stati**: l'issue attraversa stati definiti (submitted → validated → approved → executed → completed).
3. **Commenti come log**: i risultati delle automazioni vengono postati come commenti sull'issue.
4. **Label come segnali**: le label vengono aggiunte/rimosse automaticamente per indicare lo stato.

### Pattern: Approvazione Deployment

```yaml
# .github/workflows/deploy-approval.yml
name: Deployment Approval via Issue

on:
  issue_comment:
    types: [created]

jobs:
  deploy:
    if: |
      github.event.issue.labels.*.name == 'deploy-request' &&
      contains(github.event.comment.body, '/approve-deploy')
    runs-on: ubuntu-latest
    steps:
      - name: Verify Approver
        id: verify
        uses: actions/github-script@v7
        with:
          script: |
            const approverTeam = 'deploy-approvers';
            const org = context.repo.owner;
            const commenter = context.payload.comment.user.login;

            // Verificare che il commenter sia nel team degli approvatori
            try {
              const membership = await github.rest.teams.getMembershipForUserInOrg({
                org: org,
                team_slug: approverTeam,
                username: commenter
              });
              if (membership.data.state !== 'active') {
                throw new Error('Non membro attivo');
              }
              core.setOutput('approved', 'true');
            } catch (e) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: `⛔ @${commenter} non ha i permessi per approvare i deployment.`
              });
              core.setOutput('approved', 'false');
            }

      - name: Execute Deployment
        if: steps.verify.outputs.approved == 'true'
        run: |
          echo "Deployment approvato. Esecuzione in corso..."
          # Qui inserire i comandi di deployment

      - name: Update Issue
        if: steps.verify.outputs.approved == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: '✅ Deployment completato con successo.'
            });
            await github.rest.issues.update({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              state: 'closed',
              labels: ['deploy-completed']
            });
```

### Pattern: Provisioning Risorse

```yaml
# .github/ISSUE_TEMPLATE/resource-request.yml
name: Resource Request
description: Richiedere la creazione di risorse cloud
title: "[Resource]: "
labels: ["resource-request", "needs-approval"]
body:
  - type: dropdown
    id: resource-type
    attributes:
      label: Tipo di Risorsa
      options:
        - S3 Bucket
        - RDS Database
        - Lambda Function
        - ECS Service
    validations:
      required: true

  - type: dropdown
    id: environment
    attributes:
      label: Ambiente
      options:
        - development
        - staging
        - production
    validations:
      required: true

  - type: input
    id: resource-name
    attributes:
      label: Nome della Risorsa
      placeholder: "es. user-uploads-bucket"
    validations:
      required: true

  - type: textarea
    id: justification
    attributes:
      label: Giustificazione
      description: Perché serve questa risorsa?
    validations:
      required: true
```

```yaml
# .github/workflows/resource-provisioning.yml
name: Resource Provisioning

on:
  issues:
    types: [labeled]

jobs:
  provision:
    if: github.event.label.name == 'approved'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Parse Issue
        id: parse
        uses: issue-ops/parser@v1
        with:
          issue-form-template: resource-request.yml

      - name: Provision Resource
        run: |
          RESOURCE_TYPE="${{ steps.parse.outputs.resource-type }}"
          ENVIRONMENT="${{ steps.parse.outputs.environment }}"
          RESOURCE_NAME="${{ steps.parse.outputs.resource-name }}"

          echo "Provisioning $RESOURCE_TYPE: $RESOURCE_NAME in $ENVIRONMENT"
          # Qui inserire i comandi di provisioning (Terraform, CloudFormation, ecc.)

      - name: Report Success
        uses: peter-evans/create-or-update-comment@v4
        with:
          issue-number: ${{ github.event.issue.number }}
          body: |
            ✅ **Risorsa creata con successo**

            - Tipo: ${{ steps.parse.outputs.resource-type }}
            - Nome: ${{ steps.parse.outputs.resource-name }}
            - Ambiente: ${{ steps.parse.outputs.environment }}
```

### Sicurezza di IssueOps

Considerazioni di sicurezza fondamentali per i workflow IssueOps:

1. **Validare il mittente**: verificare sempre che l'utente che attiva l'azione abbia i permessi necessari (membership nel team, ruolo nel repository).
2. **Sanitizzare l'input**: i contenuti delle issue sono input utente non fidato. Non iniettarli direttamente nei comandi shell.
3. **Permessi minimi**: il token del workflow deve avere solo i permessi strettamente necessari.
4. **Audit trail**: ogni azione deve essere loggata come commento sull'issue per tracciabilità.
5. **Approvazione esplicita**: per azioni distruttive (deployment in produzione, eliminazione risorse), richiedere sempre un'approvazione esplicita.

---

## Automazione Avanzata con GitHub Actions

### Auto-Label sulle Nuove Issue

```yaml
# .github/workflows/auto-label.yml
name: Auto Label Issues

on:
  issues:
    types: [opened, edited]

jobs:
  label:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Apply Labels Based on Content
        uses: actions/github-script@v7
        with:
          script: |
            const issue = context.payload.issue;
            const title = issue.title.toLowerCase();
            const body = (issue.body || '').toLowerCase();
            const labelsToAdd = [];

            // Rilevamento per parole chiave nel titolo
            if (title.includes('[bug]') || title.includes('bug:')) {
              labelsToAdd.push('type:bug');
            }
            if (title.includes('[feature]') || title.includes('feat:')) {
              labelsToAdd.push('type:feature');
            }
            if (title.includes('[docs]')) {
              labelsToAdd.push('documentation');
            }
            if (title.includes('[security]')) {
              labelsToAdd.push('type:security', 'priority:critical');
            }

            // Rilevamento per contenuto del body
            if (body.includes('produzione') || body.includes('production')) {
              labelsToAdd.push('priority:high');
            }
            if (body.includes('crash') || body.includes('data loss')) {
              labelsToAdd.push('priority:critical');
            }

            // Aggiungere label area basate su percorsi di file menzionati
            if (body.includes('src/frontend') || body.includes('component')) {
              labelsToAdd.push('area:frontend');
            }
            if (body.includes('src/api') || body.includes('endpoint')) {
              labelsToAdd.push('area:backend');
            }

            // Aggiungere label triage se nessuna priorità è stata assegnata
            if (!labelsToAdd.some(l => l.startsWith('priority:'))) {
              labelsToAdd.push('status:triage');
            }

            if (labelsToAdd.length > 0) {
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                labels: labelsToAdd
              });
            }
```

### Auto-Assignment Basato su Label

```yaml
# .github/workflows/auto-assign.yml
name: Auto Assign Issues

on:
  issues:
    types: [labeled]

jobs:
  assign:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Assign Based on Label
        uses: actions/github-script@v7
        with:
          script: |
            const label = context.payload.label.name;
            const assignments = {
              'area:frontend': ['frontend-dev-1', 'frontend-dev-2'],
              'area:backend': ['backend-dev-1', 'backend-dev-2'],
              'area:infra': ['devops-1'],
              'area:database': ['dba-1'],
              'type:security': ['security-lead'],
            };

            const assignees = assignments[label];
            if (assignees) {
              // Round-robin: assegnare al primo disponibile
              // In produzione, verificare il carico di lavoro corrente
              await github.rest.issues.addAssignees({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.payload.issue.number,
                assignees: [assignees[0]]
              });
            }
```

### Aggiunta Automatica a Projects

```yaml
# .github/workflows/add-to-project.yml
name: Auto Add to Project

on:
  issues:
    types: [opened]
  pull_request:
    types: [opened]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1.0.2
        with:
          project-url: https://github.com/orgs/my-org/projects/1
          github-token: ${{ secrets.PROJECT_TOKEN }}
          labeled: "bug,enhancement,type:feature,type:bug"
          label-operator: OR
```

### Triage Automatico con AI (Settembre 2025)

A partire da settembre 2025, GitHub ha introdotto l'**AI Labeler e Moderator** che utilizza la GitHub Models inference API per il triage automatico delle issue:

```yaml
# .github/workflows/ai-triage.yml
name: AI Issue Triage

on:
  issues:
    types: [opened]

jobs:
  triage:
    runs-on: ubuntu-latest
    permissions:
      issues: write
      models: read
    steps:
      - name: AI Classification
        uses: github/issue-labeler@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          model: "gpt-4o"  # Modello GitHub Models
          labels: |
            type:bug - Il contenuto descrive un malfunzionamento
            type:feature - Il contenuto propone una nuova funzionalità
            type:docs - Il contenuto riguarda documentazione
            type:question - Il contenuto è una domanda
          confidence-threshold: 0.8
```

> **Nota**: questa funzionalità richiede accesso a GitHub Models ed è soggetta a limiti di utilizzo.

### Stale Issue Management

```yaml
# .github/workflows/stale-issues.yml
name: Close Stale Issues

on:
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedì alle 06:00

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          stale-issue-message: |
            Questa issue è stata inattiva per 60 giorni.
            Verrà chiusa automaticamente tra 14 giorni se non ci saranno aggiornamenti.
            Se l'issue è ancora rilevante, aggiungere un commento.
          stale-issue-label: 'status:stale'
          close-issue-message: |
            Questa issue è stata chiusa per inattività.
            Se il problema persiste, aprire una nuova issue con informazioni aggiornate.
          days-before-stale: 60
          days-before-close: 14
          exempt-issue-labels: 'priority:critical,priority:high,status:blocked'
          exempt-all-milestones: true
```

---

## Progetti Cross-Repository e Organizzazione Enterprise

### Progetti a Livello Organizzazione

I GitHub Projects possono essere creati a livello di organizzazione per tracciare il lavoro attraverso molteplici repository. Questo è fondamentale per team che lavorano su microservizi, monorepo multi-progetto, o ecosistemi di librerie.

```bash
# Creare un progetto a livello organizzazione
gh project create --title "Q3 2025 Roadmap" --owner "my-org"

# Aggiungere issue da repository diversi
gh project item-add 1 --owner "my-org" \
  --url https://github.com/my-org/frontend/issues/42
gh project item-add 1 --owner "my-org" \
  --url https://github.com/my-org/backend/issues/78
gh project item-add 1 --owner "my-org" \
  --url https://github.com/my-org/infrastructure/issues/15
```

### Struttura Raccomandata per Organizzazioni

```
Organizzazione: my-org
│
├── Project: "Product Roadmap" (livello org)
│   ├── Vista: Board per Status
│   ├── Vista: Roadmap per Quarter
│   ├── Vista: Table per Team
│   └── Issue da: frontend, backend, mobile, infra
│
├── Project: "Sprint Board" (livello org)
│   ├── Vista: Board per Status (sprint corrente)
│   ├── Vista: Table per Sviluppatore
│   └── Filtro: iteration:@current
│
├── Project: "Bug Tracker" (livello org)
│   ├── Vista: Board per Priorità
│   ├── Vista: Table per Repository
│   └── Filtro: label:bug
│
└── Project per repository specifico (livello repo)
    └── Per lavoro interno al singolo repository
```

### Automazione Cross-Repository

```yaml
# .github/workflows/cross-repo-sync.yml
# Workflow che sincronizza lo stato delle issue tra repository
name: Cross-Repo Issue Sync

on:
  issues:
    types: [closed]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Check for Cross-Repo References
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.CROSS_REPO_TOKEN }}
          script: |
            const issue = context.payload.issue;
            const body = issue.body || '';

            // Cercare riferimenti a issue in altri repository
            const crossRefRegex = /depends-on:\s*([\w-]+\/[\w-]+)#(\d+)/gi;
            let match;

            while ((match = crossRefRegex.exec(body)) !== null) {
              const [, repo, issueNumber] = match;
              const [owner, repoName] = repo.split('/');

              // Commentare sulla issue correlata
              await github.rest.issues.createComment({
                owner: owner,
                repo: repoName,
                issue_number: parseInt(issueNumber),
                body: `ℹ️ L'issue dipendente ${context.repo.owner}/${context.repo.repo}#${issue.number} è stata chiusa.`
              });
            }
```

### Sfide del Tracking Cross-Repository

Le milestone sono definite a livello di repository, non di organizzazione. Questo crea sfide quando si traccia il progresso di una release che coinvolge più repository:

**Strategia 1 — Milestone con stesso nome in ogni repository:**
```bash
# Creare la stessa milestone in tutti i repository
for REPO in frontend backend mobile infrastructure; do
  gh api repos/my-org/$REPO/milestones -X POST \
    -f title="v3.0.0" \
    -f description="Release Q3 2025" \
    -f due_on="2025-09-30T23:59:59Z"
done
```

**Strategia 2 — Issue tracker centralizzato:**
Usare un repository dedicato (es. `my-org/project-tracker`) con issue che aggregano il lavoro cross-repo tramite sub-issues o riferimenti.

**Strategia 3 — Projects v2 come aggregatore:**
Il progetto a livello organizzazione con la vista Table raggruppata per repository fornisce una visione unificata senza duplicazione di milestone.

---

## Strategie di Collaborazione per Team

### Inner Source

L'**inner source** applica i principi dell'open source all'interno di un'organizzazione. Le pratiche chiave:

1. **Repository interni visibili**: tutti i repository sono accessibili a tutti i dipendenti (non necessariamente modificabili).
2. **Contributing guidelines**: ogni repository ha un `CONTRIBUTING.md` che spiega come contribuire.
3. **Issue come punto di ingresso**: le issue con label `good-first-issue` o `help-wanted` invitano contribuzioni da altri team.
4. **Cross-team PR**: le PR da sviluppatori di altri team sono benvenute e hanno un processo di review definito.

### Modelli di Branching e Collaborazione

| Modello | Issue Flow | Adatto per |
|---|---|---|
| **GitHub Flow** | Issue → Branch → PR → Review → Merge → Close | Team piccoli, deployment continuo |
| **Git Flow** | Issue → Feature branch → Develop → Release → Main | Release pianificate, versioni multiple |
| **Trunk-Based** | Issue → Short-lived branch → PR → Merge (< 1 giorno) | Team maturi, CI/CD avanzato |

### Workflow di Triage Strutturato

```
# Processo di triage settimanale

## 1. Raccolta (5 min)
- Filtrare: is:open label:status:triage
- Ordinare per data di creazione (più vecchie prima)

## 2. Categorizzazione (15 min per issue)
Per ogni issue:
a. Assegnare il tipo: bug, feature, docs, chore
b. Assegnare la priorità: P0 (critica) → P3 (backlog)
c. Assegnare l'area: frontend, backend, infra, database
d. Stimare l'effort: small, medium, large, epic
e. Assegnare la milestone (se applicabile)
f. Rimuovere label "status:triage", aggiungere "status:accepted"

## 3. Assegnazione (5 min)
- Assegnare le issue P0 e P1 immediatamente
- Le issue P2 vanno nello sprint corrente se c'è capacità
- Le issue P3 restano nel backlog

## 4. Chiusura (5 min)
- Chiudere come "not planned" le issue duplicate o wontfix
- Convertire in Discussion le issue che sono domande
- Trasferire le issue al repository corretto se necessario
```

### Comunicazione Asincrona Efficace

Per team distribuiti su fusi orari diversi, la comunicazione asincrona è fondamentale:

1. **Issue come fonte di verità**: tutte le decisioni tecniche vengono documentate nell'issue o nella PR pertinente, non in chat.
2. **Aggiornamenti di stato**: usare i commenti dell'issue per aggiornamenti di progresso, non canali di comunicazione esterni.
3. **Decision records**: le decisioni di design importanti vengono documentate in una Discussion (categoria Ideas/RFCs) o in un ADR (Architecture Decision Record) nel repository.
4. **Weekly digest automatico**: un workflow che genera un riepilogo settimanale delle attività del progetto.

```yaml
# .github/workflows/weekly-digest.yml
name: Weekly Digest

on:
  schedule:
    - cron: '0 8 * * 5'  # Ogni venerdì alle 08:00

jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Digest
        uses: actions/github-script@v7
        with:
          script: |
            const oneWeekAgo = new Date();
            oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
            const since = oneWeekAgo.toISOString();

            // Issue aperte questa settimana
            const newIssues = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              since: since,
              state: 'all',
              sort: 'created',
              direction: 'desc'
            });

            // PR merged questa settimana
            const mergedPRs = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'closed',
              sort: 'updated',
              direction: 'desc'
            });

            const openedThisWeek = newIssues.data.filter(i =>
              !i.pull_request && new Date(i.created_at) > oneWeekAgo
            );
            const closedThisWeek = newIssues.data.filter(i =>
              !i.pull_request && i.state === 'closed' &&
              new Date(i.closed_at) > oneWeekAgo
            );
            const merged = mergedPRs.data.filter(pr =>
              pr.merged_at && new Date(pr.merged_at) > oneWeekAgo
            );

            let body = `# Weekly Digest — ${new Date().toISOString().slice(0,10)}\n\n`;
            body += `## Riepilogo\n`;
            body += `- Issue aperte: **${openedThisWeek.length}**\n`;
            body += `- Issue chiuse: **${closedThisWeek.length}**\n`;
            body += `- PR merged: **${merged.length}**\n\n`;

            // Creare una discussion con il digest
            console.log(body);
```

---

## Best Practices

### Issues

1. **Un'issue per problema**: Non combinare problemi diversi nella stessa issue.
2. **Template obbligatori**: Disabilitare le blank issues e fornire template strutturati.
3. **Triage regolare**: Dedicare tempo settimanale al triage delle nuove issue.
4. **Chiusura motivata**: Quando si chiude un'issue, spiegare sempre il motivo.

### Projects

1. **Viste per audience**: Creare viste diverse per sviluppatori (dettaglio tecnico) e stakeholder (overview).
2. **Iterazioni definite**: Usare i campi Iteration per gestire gli sprint.
3. **Automazione**: Configurare le automazioni per ridurre il lavoro manuale di aggiornamento degli stati.

### Pull Requests

1. **PR piccole e frequenti**: Meglio 5 PR da 100 righe che 1 PR da 500 righe.
2. **Draft PR per il WIP**: Usare draft PR per condividere il lavoro in corso senza richiedere review.
3. **Conventional PR titles**: Usare lo stesso formato dei commit (`feat:`, `fix:`, ecc.) per i titoli delle PR.

### Discussions

1. **Categorie strutturate fin dall'inizio**: Creare categorie specifiche (Q&A, Announcements, Ideas, Show and Tell, RFC) prima che il progetto riceva traffico. Categorie chiare riducono le issue aperte per domande generiche e indirizzano le conversazioni nel canale corretto.
2. **Q&A con risposte accettate**: Nella categoria Q&A, segnare sempre la risposta accettata. Questo trasforma la discussion in una knowledge base ricercabile e aiuta gli utenti futuri a trovare la soluzione senza aprire duplicati.
3. **Pin strategico**: Pinnare al massimo 3-4 discussion per categoria. Un eccesso di pin annulla il loro scopo. Riservare i pin per: linee guida della community, FAQ aggiornate, roadmap pubblica e annunci critici.
4. **Collegamento bidirezionale Issue-Discussion**: Quando una discussion genera un'idea implementabile, convertirla in issue mantenendo il link alla discussion originale. Questo preserva il contesto della decisione e permette agli stakeholder di seguire l'evoluzione dall'idea all'implementazione.
5. **Moderazione proattiva**: Configurare le Discussion Labels per categorizzare ulteriormente i thread. Usare il lock sulle discussion risolte da tempo per evitare che vengano rianimate con informazioni obsolete. Trasferire le discussion fuori tema nella categoria corretta invece di chiuderle.
6. **Organization-level Discussions**: Per le organizzazioni con piu repository, abilitare le Discussions a livello organizzazione per conversazioni cross-progetto come RFC architetturali, standard di codifica condivisi e retrospettive di team.

### Code Review

1. **CODEOWNERS granulare**: Definire ownership a livello di directory e pattern di file, non solo a livello di repository. Un singolo `* @team-leads` genera colli di bottiglia; ownership specifico come `/src/auth/** @security-team` distribuisce il carico e garantisce competenza pertinente.
2. **Review assignment automatico**: Configurare il round-robin o load-balancing nelle impostazioni del team per distribuire equamente le review. Evitare che un singolo senior reviewer diventi il bottleneck del team.
3. **Tempo massimo di review**: Stabilire una convenzione di team per il tempo massimo di risposta alle review request (es. 24 ore lavorative). Monitorare con le metriche di GitHub Insights o strumenti esterni. Le PR che stagnano in review degradano la velocity del team piu di qualsiasi debito tecnico.
4. **Suggestion block come standard**: Preferire sempre i `suggestion` block ai commenti testuali quando si propone una modifica specifica. Il reviewer scrive il codice corretto nel blocco suggestion e l'autore lo applica con un click, eliminando ambiguita e cicli di review inutili.
5. **Review incrementale per PR grandi**: Per PR inevitabilmente grandi (migrazioni, refactoring), usare la funzionalita "Viewed" per marcare i file gia revisionati. Il reviewer puo procedere file per file senza perdere il punto.
6. **Self-review prima di richiedere review**: L'autore dovrebbe sempre fare una self-review della propria PR prima di assegnare reviewer. Controllare il diff nella UI di GitHub spesso rivela problemi non visibili nell'IDE: file dimenticati, conflitti di merge residui, commenti di debug rimasti.
7. **Copilot Code Review come primo filtro**: Usare Copilot Code Review come review automatica per catturare problemi stilistici e bug ovvi prima della review umana. Questo libera tempo ai reviewer umani per concentrarsi su logica, architettura e decisioni di design.

### Collaborazione Asincrona

1. **Documentare le decisioni, non solo il codice**: Ogni decisione architetturale significativa dovrebbe essere registrata in un ADR (Architecture Decision Record) o in una Discussion dedicata. Il codice mostra *cosa* e stato fatto; la documentazione spiega *perche*.
2. **Timezone-aware workflow**: In team distribuiti, evitare di assegnare review a fine giornata del reviewer. Usare le GitHub Actions per notificare le review pending all'inizio della giornata lavorativa di ciascun timezone.
3. **Status updates regolari nei Projects**: Usare la funzionalita Status Updates di Projects v2 per comunicare il progresso settimanale agli stakeholder senza richiedere meeting sincroni. Includere: lavoro completato, blocchi attuali, prossimi passi.
4. **Issue come single source of truth**: Mantenere ogni issue aggiornata con lo stato corrente. Non affidarsi a canali Slack o email per comunicare aggiornamenti — le informazioni devono vivere nell'issue dove sono ricercabili e contestualizzate.
5. **Cross-repository collaboration**: Per progetti multi-repo, usare Projects a livello organizzazione che aggregano issue da repository diversi. Questo fornisce una vista unificata del progresso senza duplicare le issue.
6. **Retrospettive tracciabili**: Usare le Discussions con categoria dedicata per le retrospettive. A differenza dei documenti condivisi, le discussion mantengono la cronologia e sono ricercabili nel contesto del repository.

---

## Anti-Pattern e Errori Comuni

Questa sezione documenta gli errori ricorrenti nella gestione di issue, progetti e collaborazione su GitHub. Ogni anti-pattern include la descrizione del problema, le conseguenze e la soluzione raccomandata.

### Anti-Pattern nelle Issue

#### Issue Omnibus

**Problema**: Una singola issue che copre troppi aspetti — "Migliorare il modulo di autenticazione" che include bug fix, nuove feature, refactoring e aggiornamento documentazione.

**Conseguenze**: Impossibile assegnare a un singolo sprint, difficile da tracciare, non chiudibile in modo atomico. La progress bar della milestone resta bloccata perche l'issue rimane aperta per settimane.

**Soluzione**: Scomporre in issue atomiche. Usare i Sub-Issues (o Tasklist prima della deprecazione) per creare una gerarchia: una issue epica di tracking con sotto-issue specifiche, ciascuna assegnabile e chiudibile indipendentemente.

#### Label Soup

**Problema**: Proliferazione incontrollata di label senza naming convention. Il repository accumula `bug`, `Bug`, `BUG`, `type:bug`, `tipo-bug` e varianti simili.

**Conseguenze**: Filtraggio inutilizzabile, metriche di triage inaffidabili, nuovo contribuente confuso dalla scelta tra label apparentemente equivalenti.

**Soluzione**: Definire un set di label standardizzato con prefissi categorici (`type/`, `priority/`, `status/`, `area/`) e sincronizzarlo con script `gh label create` o GitHub Actions. Disabilitare la creazione di label non standard tramite convenzione di team.

#### Issue Senza Contesto

**Problema**: Issue aperte con descrizioni come "Non funziona" o "Fix the login" senza passi per riprodurre, versione, ambiente o screenshot.

**Conseguenze**: Il developer deve fare reverse engineering del problema, spesso con scambi di commenti che durano giorni. Il tempo di risoluzione si moltiplica.

**Soluzione**: Rendere obbligatori i template YAML form con campi required. Disabilitare le blank issue in `config.yml`. I campi `textarea` con placeholder e campi `dropdown` per versione/OS eliminano le issue incomplete.

#### Milestone Come Etichette

**Problema**: Usare le milestone come semplici tag categorici (es. "Frontend", "Backend") invece che come obiettivi temporali con scadenza.

**Conseguenze**: Le milestone non hanno mai una data di completamento, la percentuale di progresso non ha significato, e il team perde visibilita sui rilasci futuri.

**Soluzione**: Le milestone devono rappresentare rilasci o obiettivi con data di scadenza. Per la categorizzazione usare le label. Per il raggruppamento tematico usare i Projects.

### Anti-Pattern nei Projects

#### Project Board Cimitero

**Problema**: Board creata con entusiasmo, popolata inizialmente, poi abbandonata. Le card non riflettono lo stato reale del lavoro.

**Conseguenze**: Il team torna a tracciare il lavoro su Slack, fogli condivisi o nella mente di singoli developer. Il project board diventa un artefatto decorativo che inganna gli stakeholder.

**Soluzione**: Configurare le automazioni built-in (issue closed → Done, PR opened → In Progress) per ridurre l'aggiornamento manuale. Integrare l'aggiornamento del board nel workflow quotidiano. Se il board non viene usato dopo 2 sprint, analizzare perche: spesso il problema e la granularita delle colonne o la mancanza di viste utili.

#### Campi Custom Eccessivi

**Problema**: Aggiungere decine di campi custom (effort, business value, risk score, customer impact, department, quarter, OKR...) per ogni item.

**Conseguenze**: L'overhead di compilazione supera il beneficio informativo. I developer smettono di aggiornare i campi, rendendo i dati inaffidabili. Le viste diventano illeggibili.

**Soluzione**: Iniziare con il minimo indispensabile: Status, Priority, Iteration, Assignee. Aggiungere campi solo quando un bisogno concreto e dimostrato. Regola pratica: se un campo non viene usato per filtrare o raggruppare almeno settimanalmente, rimuoverlo.

#### Automazioni Fragili

**Problema**: Workflow Actions complessi che gestiscono le transizioni di stato del Project con logica custom, token con scope eccessivi e nessun error handling.

**Conseguenze**: Un cambio nelle API di GitHub o un token scaduto blocca silenziosamente tutte le automazioni. Il team non se ne accorge finche il board non diverge dalla realta.

**Soluzione**: Preferire le automazioni built-in di Projects v2 per i casi standard. Per logica custom, usare l'azione ufficiale `actions/github-script` con error handling esplicito, retry e notifiche di fallimento. Verificare periodicamente che le automazioni funzionino con un issue di test.

### Anti-Pattern nelle Pull Request

#### PR Monolitica

**Problema**: Una singola PR con 50+ file modificati, 2000+ righe di diff, che tocca autenticazione, database, UI e configurazione CI.

**Conseguenze**: Nessun reviewer riesce a fare una revisione approfondita. La review diventa superficiale ("LGTM" senza vera analisi). Bug critici passano inosservati. Il merge e rischioso e il rollback complesso.

**Soluzione**: Suddividere in PR atomiche per area funzionale. Usare stacked PRs (PR che dipendono l'una dall'altra) per mantenere la sequenza logica. Impostare una soft limit di 400 righe di diff come guideline di team.

#### Review Ping-Pong

**Problema**: Il reviewer lascia 3 commenti, l'autore li risolve ma introduce nuovi problemi, il reviewer trova altri 3 commenti, il ciclo continua per giorni.

**Conseguenze**: Frustrazione bilaterale, tempi di merge che si allungano, contesto perso tra un ciclo e l'altro.

**Soluzione**: L'autore deve fare self-review prima di assegnare reviewer. Il reviewer deve lasciare tutti i commenti in una singola review pass, non a goccia. Usare la severity (nit, suggestion, blocking) per permettere all'autore di prioritizzare. Per problemi architetturali, fare una breve chiamata sincrona invece di iterare via commenti.

#### CODEOWNERS Troppo Ampio

**Problema**: Un singolo `* @team-lead` nel file CODEOWNERS che assegna la stessa persona come reviewer obbligatorio per ogni PR.

**Conseguenze**: Il team lead diventa un bottleneck permanente. Le PR stagnano in attesa di review. Il team lead non riesce a fare review approfondite a causa del volume.

**Soluzione**: Distribuire l'ownership per directory e area funzionale. Usare team GitHub (es. `@org/frontend-team`, `@org/api-team`) invece di utenti singoli. Configurare il review assignment con round-robin nel team.

#### Ignorare la Merge Queue

**Problema**: Fare merge diretto senza usare la merge queue in branch con required checks, causando fallimenti intermittenti quando due PR in parallelo modificano aree correlate.

**Conseguenze**: Il branch principale si rompe dopo il merge. I check CI passano sulla PR ma falliscono su `main` perche le PR non erano state testate insieme.

**Soluzione**: Abilitare la Merge Queue che testa automaticamente le PR in sequenza o in batch contro la versione aggiornata di `main`. Configurare `merge_group` come trigger nei workflow CI. Accettare il leggero aumento del tempo di merge in cambio della stabilita del branch principale.

### Anti-Pattern nella Collaborazione

#### Comunicazione Shadow

**Problema**: Decisioni importanti prese su Slack, in chiamate non documentate o in email, senza registrazione nella issue o nella PR corrispondente.

**Conseguenze**: I nuovi membri del team non trovano il contesto delle decisioni. Le stesse discussioni si ripetono. Il "perche" delle scelte architetturali si perde.

**Soluzione**: Usare la regola "se non e nella issue, non e successo". Dopo ogni decisione presa fuori da GitHub, aggiungere un commento riassuntivo nella issue pertinente con il razionale e i partecipanti alla decisione.

#### Notification Fatigue

**Problema**: Tutti gli sviluppatori sono sottoscritti a tutti i repository. Le notifiche GitHub superano le centinaia al giorno.

**Conseguenze**: Le notifiche vengono ignorate in massa. Le review request urgenti si perdono nel rumore. Il developer sviluppa l'abitudine di non leggere le notifiche GitHub.

**Soluzione**: Configurare le subscription per repository selettivamente. Usare il filtro "Participating and @mentions" come default. Creare filtri email dedicati. Usare la Scheduled Notification Digest per i repository non critici. Nelle notifiche, menzionare esplicitamente (`@username`) solo chi deve agire.

---

## Troubleshooting

### Issue Template Non Visualizzato

```bash
# Verificare il percorso
# Deve essere in .github/ISSUE_TEMPLATE/
ls .github/ISSUE_TEMPLATE/

# Verificare la sintassi YAML
yamllint .github/ISSUE_TEMPLATE/bug_report.yml

# Verificare che config.yml sia corretto
cat .github/ISSUE_TEMPLATE/config.yml
```

### Auto-Merge Non Funziona

```bash
# Prerequisiti:
# 1. Auto-merge deve essere abilitato nelle repo settings
# 2. Branch protection rules con required checks devono essere configurate
# 3. Il branch deve essere aggiornato con il base branch (se strict è abilitato)

# Verificare
gh repo edit --enable-auto-merge=true
```

### Projects: Item Non Aggiornato

```bash
# Verificare le automazioni configurate
# Project Settings > Workflows

# Verificare i permessi del token
# Il token deve avere scope "project" per le automazioni con Actions
```

### CODEOWNERS Non Assegna i Reviewer

```bash
# 1. Verificare che il file CODEOWNERS sia nel percorso corretto
# Deve trovarsi in uno di: .github/CODEOWNERS, docs/CODEOWNERS, CODEOWNERS (root)
ls .github/CODEOWNERS docs/CODEOWNERS CODEOWNERS 2>/dev/null

# 2. Verificare la sintassi — errori comuni:
#    - Pattern senza owner: /src/auth/
#    - Owner inesistente: /src/ @utente-che-non-esiste
#    - Spazi nei percorsi senza escape
cat .github/CODEOWNERS

# 3. Verificare che branch protection richieda review da CODEOWNERS
gh api repos/{owner}/{repo}/branches/main/protection \
  --jq '.required_pull_request_reviews.require_code_owner_reviews'
# Deve restituire "true"

# 4. Verificare che gli owner siano membri dell'organizzazione
# con permessi di lettura sul repository
gh api orgs/{org}/members --jq '.[].login' | grep "expected-reviewer"

# 5. Verificare che il pattern matchi i file modificati nella PR
# Testare il matching con git:
git diff --name-only main...HEAD
# Confrontare i percorsi con i pattern nel CODEOWNERS
```

**Cause comuni**: Il file CODEOWNERS contiene un pattern che non matcha i file nella PR (es. `*.ts` nel CODEOWNERS ma i file modificati sono `.tsx`). L'ordine dei pattern conta — l'ultimo match vince, non il primo.

### Merge Queue Fallisce sui Check

```bash
# La merge queue crea un branch temporaneo (gh-readonly-queue/main/pr-XXX)
# che include i cambiamenti di tutte le PR in coda.

# 1. Verificare che i workflow CI abbiano il trigger merge_group:
# In .github/workflows/ci.yml:
# on:
#   pull_request:
#   merge_group:    <-- NECESSARIO per merge queue

# 2. Verificare che i required checks corrispondano
# Il nome del check nel workflow CI deve corrispondere esattamente
# al nome configurato come required status check
gh api repos/{owner}/{repo}/branches/main/protection \
  --jq '.required_status_checks.checks[].context'

# 3. Se i check passano sulla PR ma falliscono nella merge queue,
# il problema e tipicamente un conflitto tra PR in coda.
# Soluzione: ridurre max_entries_to_build o usare merge_method: squash

# 4. Verificare i log del merge group
gh run list --branch "gh-readonly-queue/main/*" --limit 5
```

**Causa principale**: Il workflow CI non include `merge_group` tra i trigger. Senza questo trigger, i check non vengono eseguiti sul branch temporaneo della merge queue, causando un timeout che blocca il merge.

### Sub-Issues Non Mostrano il Progresso

```bash
# I sub-issues (successori delle tasklist) mostrano il progresso
# nella issue padre solo se configurati correttamente.

# 1. Verificare che i sub-issues siano collegati correttamente
# Nella issue padre, la sezione "Sub-issues" deve mostrare le issue figlie
gh issue view 123 --json body,title

# 2. Il progresso si aggiorna automaticamente quando:
#    - Un sub-issue viene chiuso (incrementa la percentuale)
#    - Un sub-issue viene riaperto (decrementa la percentuale)
#    - Un sub-issue viene rimosso dal parent

# 3. Se il progresso non si aggiorna:
#    - Verificare di usare sub-issues nativi, non semplici link o checkbox
#    - Le tasklist Markdown (- [ ] #123) sono in fase di deprecazione
#    - Usare il comando "Add sub-issue" dalla UI o API

# 4. Verificare via API
gh api graphql -f query='
  query {
    node(id: "ISSUE_NODE_ID") {
      ... on Issue {
        subIssues(first: 10) {
          nodes { title state }
        }
      }
    }
  }
'
```

### Projects Automation Non Si Attiva

```bash
# Le automazioni built-in di Projects v2 possono non attivarsi per:

# 1. Item aggiunto manualmente vs tramite issue/PR
#    Le automazioni "Item added" si attivano solo per issue/PR aggiunte,
#    non per draft items creati nel project stesso.

# 2. Token insufficienti negli Actions workflow
#    Le automazioni via Actions richiedono un token con scope "project"
#    Il GITHUB_TOKEN standard NON ha questo scope.
#    Usare un PAT o GitHub App con permesso "Organization projects: read/write"

# 3. Automazione disabilitata
#    Verificare in Project Settings > Workflows che l'automazione sia attiva
#    Ogni automazione ha un toggle on/off individuale

# 4. Rate limiting sulle API GraphQL
#    Le automazioni che usano l'API GraphQL di Projects v2 sono soggette
#    al rate limit di 5000 punti/ora. Verificare:
gh api rate_limit --jq '.resources.graphql'

# 5. Webhook delivery failures
#    Se l'automazione e basata su webhook, verificare i delivery recenti:
#    Settings > Webhooks > Recent Deliveries
#    Cercare response code != 200
```

### Discussion Non Appare nella Ricerca

```bash
# Le Discussions usano un indice di ricerca separato dalle Issue.

# 1. Verificare che Discussions sia abilitato nel repository
gh api repos/{owner}/{repo} --jq '.has_discussions'

# 2. La ricerca nelle Discussions richiede il qualificatore specifico:
# Nella barra di ricerca GitHub: "is:discussion keyword"
# Non: "keyword" (cerca solo in issue e PR per default)

# 3. Per cercare via CLI:
gh search issues --include-discussions "keyword repo:{owner}/{repo}"

# 4. Le Discussions appena create possono richiedere alcuni minuti
# per essere indicizzate nel motore di ricerca GitHub.
# Non e un bug — e latenza di indicizzazione.
```

---

## Esercizi

### Esercizio 1 — Issue Templates e Form YAML

**Obiettivo:** Creare un set completo di issue templates per un progetto open source.

1. Creare tre template in `.github/ISSUE_TEMPLATE/`: `bug_report.yml`, `feature_request.yml`, `documentation.yml`
2. Ogni template deve usare il formato YAML form con campi tipizzati (`textarea`, `dropdown`, `checkboxes`, `input`)
3. Il bug report deve richiedere: descrizione, passi per riprodurre, comportamento atteso vs attuale, versione, OS, screenshot opzionale
4. Configurare `config.yml` con link esterni (es. Discussions per domande generiche)
5. Creare una PR e verificare che il selettore di template appaia correttamente nella pagina "New Issue"

### Esercizio 2 — GitHub Projects v2 Sprint Board

**Obiettivo:** Configurare un Projects v2 per gestire uno sprint di 2 settimane.

1. Creare un Project a livello organizzazione con campi custom: `Priority` (single select: P0-P3), `Sprint` (iteration: 2 settimane), `Size` (number), `Team` (single select)
2. Creare tre viste: Board (raggruppato per Status), Table (raggruppato per Priority), Roadmap (per Sprint)
3. Configurare automazioni built-in: issue aperta → status "Todo", PR collegata → status "In Progress", PR merged → status "Done"
4. Aggiungere almeno 10 issue con label, priority e assegnazione a sprint
5. Verificare che il filtraggio per team, priority e sprint funzioni correttamente

### Esercizio 3 — Pull Request Workflow Completo

**Obiettivo:** Implementare un ciclo completo di PR con code review strutturata.

1. Creare un `PULL_REQUEST_TEMPLATE.md` con sezioni: descrizione, tipo di cambio, checklist (test, docs, breaking changes), issue collegata
2. Creare una PR con almeno 3 file modificati e richiedere una review
3. Come reviewer: lasciare commenti su linee specifiche, un suggerimento inline (`suggestion` block), e una richiesta di modifica
4. Come autore: applicare il suggerimento, rispondere ai commenti, pushare i fix
5. Come reviewer: approvare la PR e verificare che il merge sia consentito

### Esercizio 4 — Labels e Milestones Automation

**Obiettivo:** Creare un sistema di label standardizzato e automatizzare l'assegnazione.

1. Definire un set di label in un file `labels.yml` con categorie: `type/` (bug, feature, docs, chore), `priority/` (critical, high, medium, low), `status/` (needs-triage, in-progress, blocked)
2. Scrivere uno script con `gh label create` che sincronizza le label dal file YAML
3. Creare una milestone per il prossimo rilascio con data di scadenza e descrizione
4. Configurare un GitHub Action che assegna automaticamente la label `needs-triage` alle nuove issue senza label
5. Verificare che le issue vengano tracciate nella milestone e che il progresso percentuale sia corretto

### Esercizio 5 — Discussions e Knowledge Base

**Obiettivo:** Configurare Discussions come Q&A e knowledge base per un progetto.

1. Abilitare Discussions nel repository e configurare le categorie: Announcements, Q&A, Ideas, Show and Tell
2. Creare un post "pinned" nella categoria Announcements con le regole della community
3. Creare almeno 3 discussion nella categoria Q&A e marcare le risposte accettate
4. Configurare un GitHub Action che converte automaticamente le Discussion con label `accepted-answer` in pagine Wiki
5. Confrontare quando usare Issues vs Discussions vs Wiki e documentare le linee guida nel README

---

## Letture e Riferimenti

### Documentazione ufficiale

- **GitHub Docs — Issues** — Guida completa alla creazione e gestione delle issue. <https://docs.github.com/en/issues> (consultato: 2026-05-24)
- **GitHub Docs — Projects** — Planning e tracking con GitHub Projects v2. <https://docs.github.com/en/issues/planning-and-tracking-with-projects> (consultato: 2026-05-24)
- **GitHub Docs — Pull Requests** — Workflow completo delle pull request. <https://docs.github.com/en/pull-requests> (consultato: 2026-05-24)
- **GitHub Docs — Discussions** — Forum integrato per la community del progetto. <https://docs.github.com/en/discussions> (consultato: 2026-05-24)
- **GitHub Docs — Wiki** — Documentazione collaborativa integrata nel repository. <https://docs.github.com/en/communities/documenting-your-project-with-wikis> (consultato: 2026-05-24)
- **GitHub Docs — Code Review** — Best practice per la revisione del codice su GitHub. <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests> (consultato: 2026-05-24)
- **Google Engineering — Code Review Best Practices** — Linee guida di Google per code review efficaci. <https://google.github.io/eng-practices/review/> (consultato: 2026-05-24)
- **Conventional Commits** — Specifica per messaggi di commit strutturati. <https://www.conventionalcommits.org/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Chacon S., Straub B., *Pro Git* (2nd ed.), Apress, 2014. Disponibile gratuitamente su <https://git-scm.com/book>.
- Winters T., Manshreck T., Wright H., *Software Engineering at Google*, O'Reilly, 2020. Capitoli su code review e collaborazione.
- Forsgren N., Humble J., Kim G., *Accelerate*, IT Revolution Press, 2018. Metriche e pratiche per team ad alte prestazioni.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [12 — Repository Management](12-github-repository-management.md) | Le branch protection e i CODEOWNERS configurati nel modulo 12 determinano i requisiti di review sulle PR |
| [14 — Packages, Pages e Releases](14-github-packages-pages-releases.md) | Le release si collegano alle milestone e alle issue chiuse trattate in questo modulo |
| [15 — GitHub API, CLI e Webhooks](15-github-api-cli-webhooks.md) | L'automazione di issue e projects utilizza le API e la CLI trattate nel modulo 15 |
| [17 — GitHub Actions Workflow e Sintassi](17-github-actions-workflow-sintassi.md) | I workflow Actions automatizzano label, triage e transizioni di stato nei Projects |
| [20 — Git Workflow Team](20-git-workflow-team-guida-completa.md) | I workflow di team si basano sulle pratiche di collaborazione e code review trattate qui |
| [22 — Copilot, Codespaces e Enterprise](22-github-copilot-codespaces-enterprise.md) | Copilot assiste nella code review e Codespaces fornisce ambienti di sviluppo per le PR |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Issue** | Unita di lavoro tracciabile in un repository GitHub: bug, feature request, task o qualsiasi attivita che richiede azione. |
| **Issue template** | File YAML o Markdown in `.github/ISSUE_TEMPLATE/` che precompila la struttura di una nuova issue con campi predefiniti. |
| **Label** | Etichetta colorata assegnata a issue e PR per categorizzarle (tipo, priorita, stato, area). Filtrabile e ricercabile. |
| **Milestone** | Raggruppamento di issue e PR associate a un obiettivo con scadenza temporale, con tracking automatico del progresso percentuale. |
| **GitHub Projects v2** | Sistema di project management integrato con viste tabellari, board Kanban, roadmap e campi custom tipizzati. |
| **Pull request** | Richiesta di merge di un branch in un altro, con supporto per code review, discussione, CI check e approvazione. |
| **Code review** | Processo di revisione del codice in una PR tramite commenti inline, suggerimenti, richieste di modifica e approvazione. |
| **Suggestion block** | Blocco Markdown in un commento di review che propone una modifica specifica al codice, applicabile con un click. |
| **Draft PR** | Pull request in stato bozza che segnala lavoro in corso e non puo essere mergiata finche non viene marcata come "Ready for review". |
| **Discussion** | Forum integrato nel repository per Q&A, annunci e conversazioni che non sono task (a differenza delle issue). |
| **Assignee** | Utente assegnato come responsabile di una issue o PR. Massimo 10 assignee per issue. |
| **Triage** | Processo di valutazione e categorizzazione delle nuove issue: assegnare label, priority, milestone e responsabile. |
| **Iteration field** | Campo custom di Projects v2 che rappresenta un ciclo temporale (sprint), con date di inizio e fine configurabili. |
| **Auto-merge** | Funzionalita che esegue automaticamente il merge di una PR quando tutti i check obbligatori e le review sono soddisfatti. |
| **CODEOWNERS** | File che mappa percorsi del repository a team o utenti, assegnando automaticamente i reviewer alle PR che modificano quei percorsi. |
