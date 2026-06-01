---
corso: "GitHub e Git Actions"
fase: "2 — Branching e Workflow"
modulo: 20
titolo: "Git Workflow per Team: Guida Completa"
versione: "Git 2.47 / GitHub 2024"
livello: "Intermedio-Avanzato"
prerequisiti: ["Strategie di Branching (modulo 02)", "Piattaforma GitHub (modulo 03)", "Pull Request workflow"]
obiettivi:
  - "Configurare un repository di team con branch protection, CODEOWNERS e template PR/issue"
  - "Standardizzare il processo di commit con Conventional Commits e validazione automatica"
  - "Implementare un flusso PR completo con review obbligatoria, check CI e merge strategy"
  - "Gestire release branch, hotfix e backporting in un team distribuito"
  - "Identificare e prevenire anti-pattern comuni nei workflow Git di team"
tag: [git, workflow, team, branch-protection, codeowners, conventional-commits, pull-request, code-review, release, hotfix]
---

# 20 — Git Workflow per Team: Guida Completa

> **Modulo 20** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Configurare un repository di team con branch protection, CODEOWNERS e template PR/issue
> 2. Standardizzare il processo di commit con Conventional Commits e validazione automatica
> 3. Implementare un flusso PR completo con review obbligatoria, check CI e merge strategy
> 4. Gestire release branch, hotfix e backporting in un team distribuito
> 5. Identificare e prevenire anti-pattern comuni nei workflow Git di team

## Idee guida
1. **Standardize commit message convention (Conventional Commits).**
2. **PR review process documented + enforced.**
3. **Squash merge default for feature branches.**
4. **Release branch + hotfix branch process.**


## Indice

1. [Introduzione](#introduzione)
2. [Configurazione di un Repository di Team da Zero](#configurazione-di-un-repository-di-team-da-zero)
3. [Convenzioni di Naming per i Branch](#convenzioni-di-naming-per-i-branch)
4. [Conventional Commits](#conventional-commits)
5. [Template per Pull Request](#template-per-pull-request)
6. [Template per Issue](#template-per-issue)
7. [CODEOWNERS: Assegnazione Automatica dei Reviewer](#codeowners-assegnazione-automatica-dei-reviewer)
8. [Branch Protection Rules](#branch-protection-rules)
9. [Il Processo di Code Review](#il-processo-di-code-review)
10. [Strategie di Merge per Team](#strategie-di-merge-per-team)
11. [Release Management: GitFlow vs Trunk-Based Development](#release-management-gitflow-vs-trunk-based-development)
12. [Gestione degli Hotfix](#gestione-degli-hotfix)
13. [Tag Management e Versionamento Semantico](#tag-management-e-versionamento-semantico)
14. [Generazione Automatica del Changelog](#generazione-automatica-del-changelog)
15. [Workflow Completo di Esempio](#workflow-completo-di-esempio)
16. [Best Practice e Anti-Pattern](#best-practice-e-anti-pattern)
17. [Risoluzione dei Conflitti: Walkthrough Completo](#risoluzione-dei-conflitti-walkthrough-completo)
18. [Monorepo vs Polyrepo: Architettura dei Repository](#monorepo-vs-polyrepo-architettura-dei-repository)
19. [InnerSource: Pratiche Open Source in Azienda](#innersource-pratiche-open-source-in-azienda)
20. [Ship / Show / Ask: Strategia di Branching Adattiva](#ship--show--ask-strategia-di-branching-adattiva)
21. [Stacked Pull Request: PR Incrementali](#stacked-pull-request-pr-incrementali)
22. [Git Worktrees per lo Sviluppo Parallelo](#git-worktrees-per-lo-sviluppo-parallelo)
23. [Feature Flag e Trunk-Based Development Avanzato](#feature-flag-e-trunk-based-development-avanzato)
24. [Sicurezza Git per Team](#sicurezza-git-per-team)
25. [Collezione Completa di Git Alias per il Team](#collezione-completa-di-git-alias-per-il-team)
26. [Onboarding dei Nuovi Sviluppatori](#onboarding-dei-nuovi-sviluppatori)
27. [Riepilogo](#riepilogo)

---

## Introduzione

Lavorare con Git in un team è fondamentalmente diverso dal lavorare da soli. Quando più sviluppatori contribuiscono allo stesso codebase, emergono sfide che semplicemente non esistono nel lavoro individuale: conflitti di merge frequenti, branch divergenti, commit disordinati, rilasci instabili, e la costante necessità di coordinamento. Senza un workflow strutturato, un team di sviluppo può rapidamente trasformarsi in un caos di branch abbandonati, commit con messaggi incomprensibili, e rilasci che nessuno sa esattamente cosa contengano.

Questa guida affronta ogni aspetto del lavoro in team con Git e GitHub, dalla configurazione iniziale del repository fino alla generazione automatica del changelog per ogni rilascio. L'obiettivo è fornire un framework completo che un team possa adottare immediatamente, adattandolo alle proprie esigenze specifiche.

Un workflow efficace per team deve risolvere diversi problemi contemporaneamente: garantire che il codice sulla branch principale sia sempre in uno stato funzionante, permettere a più sviluppatori di lavorare in parallelo senza bloccarsi a vicenda, rendere tracciabile ogni modifica e la ragione per cui è stata fatta, automatizzare tutto ciò che è possibile automatizzare, e fornire un processo chiaro per la revisione e l'approvazione del codice.

Ogni decisione in un workflow di team è un trade-off. Un processo più rigoroso rallenta lo sviluppo quotidiano ma previene problemi gravi. Un processo troppo leggero è veloce ma fragile. La chiave è trovare il giusto equilibrio per il proprio team, e questo equilibrio cambia man mano che il team cresce e il progetto matura.

---

## Configurazione di un Repository di Team da Zero

### Creazione del Repository

La creazione di un repository di team inizia con decisioni architetturali importanti. La prima è la visibilità: per progetti aziendali interni si usa un repository privato all'interno di un'organizzazione GitHub, mentre per progetti open source si usa un repository pubblico.

```bash
# Creare un'organizzazione (via interfaccia web di GitHub)
# Poi creare il repository
gh repo create mia-org/nome-progetto \
  --private \
  --description "Descrizione del progetto" \
  --license MIT \
  --gitignore Node

# Clonare il repository
git clone git@github.com:mia-org/nome-progetto.git
cd nome-progetto
```

### Struttura Iniziale del Repository

Un repository di team ben strutturato deve contenere diversi file di configurazione fin dall'inizio. Questa struttura iniziale comunica al team le aspettative e automatizza i processi.

```
nome-progetto/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── config.yml
│   ├── PULL_REQUEST_TEMPLATE/
│   │   └── pull_request_template.md
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── cd.yml
│   │   └── release.yml
│   ├── CODEOWNERS
│   ├── dependabot.yml
│   └── FUNDING.yml
├── docs/
│   ├── CONTRIBUTING.md
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT.md
├── src/
├── tests/
├── .editorconfig
├── .gitignore
├── .gitattributes
├── CHANGELOG.md
├── LICENSE
├── README.md
└── package.json (o equivalente per il linguaggio)
```

### File `.editorconfig`

L'`.editorconfig` garantisce che tutti i membri del team usino le stesse impostazioni di base per l'editor, indipendentemente dall'IDE che preferiscono.

```ini
# .editorconfig
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

### File `.gitattributes`

```gitattributes
# .gitattributes
# Normalizzazione line endings
* text=auto eol=lf

# File binari
*.png binary
*.jpg binary
*.gif binary
*.ico binary
*.pdf binary

# File che non devono essere differenziati
*.lock linguist-generated
*.min.js linguist-generated
*.min.css linguist-generated

# Merge strategy per file specifici
package-lock.json merge=ours
yarn.lock merge=ours
```

### File `CONTRIBUTING.md`

```markdown
# Guida alla Contribuzione

## Come Contribuire

1. Forkare il repository (contributori esterni) o creare un branch (team interni)
2. Creare un branch con il naming corretto (vedi sotto)
3. Fare commit seguendo le Conventional Commits
4. Aprire una Pull Request usando il template fornito
5. Attendere la review e risolvere i commenti
6. Dopo l'approvazione, il merge viene effettuato dal reviewer

## Branch Naming

- `feature/JIRA-123-descrizione-breve`
- `bugfix/JIRA-456-descrizione-breve`
- `hotfix/JIRA-789-descrizione-breve`

## Commit Messages

Seguiamo le Conventional Commits:
- `feat: aggiungere endpoint di autenticazione`
- `fix: correggere il calcolo del totale carrello`
- `docs: aggiornare la documentazione dell'API`
- `refactor: ristrutturare il modulo di pagamento`
- `test: aggiungere test per il servizio utenti`
- `chore: aggiornare le dipendenze`

## Code Review

- Ogni PR richiede almeno 2 approvazioni
- I reviewer hanno 24 ore lavorative per completare la review
- I commenti devono essere costruttivi e specifici
```

### Configurazione Iniziale di Git per il Team

Ogni membro del team deve configurare Git localmente in modo coerente:

```bash
# Configurazione identità
git config --global user.name "Nome Cognome"
git config --global user.email "email@azienda.com"

# Configurazione merge e rebase
git config --global pull.rebase true
git config --global merge.conflictStyle diff3
git config --global rerere.enabled true

# Configurazione push
git config --global push.default current
git config --global push.autoSetupRemote true

# Alias utili per il team
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.st "status --short --branch"
git config --global alias.co "checkout"
git config --global alias.br "branch --sort=-committerdate"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.unstage "reset HEAD --"
git config --global alias.amend "commit --amend --no-edit"

# Configurazione per firma dei commit (opzionale ma raccomandato)
git config --global commit.gpgsign true
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

---

## Convenzioni di Naming per i Branch

Le convenzioni di naming per i branch sono cruciali per un team. Un nome di branch ben strutturato comunica immediatamente il tipo di lavoro, il ticket associato, e il contesto, senza dover aprire nessuno strumento.

### Schema di Naming Raccomandato

```
<tipo>/<ticket-id>-<descrizione-breve>
```

I tipi di branch più comuni sono:

| Tipo | Uso | Esempio |
|------|-----|---------|
| `feature/` | Nuove funzionalità | `feature/PROJ-123-login-oauth` |
| `bugfix/` | Correzione di bug | `bugfix/PROJ-456-fix-cart-total` |
| `hotfix/` | Fix urgenti in produzione | `hotfix/PROJ-789-fix-payment-crash` |
| `release/` | Preparazione rilascio | `release/v2.3.0` |
| `docs/` | Solo documentazione | `docs/PROJ-101-api-docs` |
| `refactor/` | Ristrutturazione codice | `refactor/PROJ-202-extract-auth-module` |
| `test/` | Aggiunta/modifica test | `test/PROJ-303-add-unit-tests` |
| `chore/` | Manutenzione, dipendenze | `chore/PROJ-404-update-deps` |
| `experiment/` | Prototipi e PoC | `experiment/PROJ-505-try-graphql` |

### Regole per i Nomi dei Branch

```bash
# Buoni nomi di branch
feature/PROJ-123-add-user-authentication
bugfix/PROJ-456-fix-null-pointer-exception
hotfix/PROJ-789-patch-xss-vulnerability

# Cattivi nomi di branch (da evitare)
feature1               # Nessun contesto
fix                    # Troppo generico
johns-branch           # Non descrive il lavoro
Feature/PROJ-123       # Case inconsistente
feature/PROJ-123-add-user-authentication-system-with-oauth2-and-saml  # Troppo lungo
```

### Enforcement Automatico con Git Hooks

Si può creare un hook pre-push che verifica il naming del branch:

```bash
#!/bin/bash
# .git/hooks/pre-push (o meglio, via Husky per l'intero team)

BRANCH_NAME=$(git symbolic-ref --short HEAD)
PATTERN="^(feature|bugfix|hotfix|release|docs|refactor|test|chore|experiment)\/[A-Z]+-[0-9]+-[a-z0-9-]+$"

if [[ "$BRANCH_NAME" == "main" || "$BRANCH_NAME" == "develop" ]]; then
  echo "Push diretto a $BRANCH_NAME non consentito. Usa una Pull Request."
  exit 1
fi

if [[ ! "$BRANCH_NAME" =~ $PATTERN ]]; then
  echo "Errore: il nome del branch '$BRANCH_NAME' non segue la convenzione."
  echo "Formato richiesto: <tipo>/<TICKET-ID>-<descrizione>"
  echo "Esempio: feature/PROJ-123-add-login"
  exit 1
fi

echo "Nome branch valido: $BRANCH_NAME"
exit 0
```

### GitHub Action per Validare il Branch Name

```yaml
# .github/workflows/validate-branch.yml
name: Validate Branch Name

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Verifica naming del branch
        run: |
          BRANCH="${{ github.head_ref }}"
          PATTERN="^(feature|bugfix|hotfix|release|docs|refactor|test|chore|experiment)/[A-Z]+-[0-9]+-[a-z0-9-]+$"

          if [[ "$BRANCH" =~ $PATTERN ]]; then
            echo "✅ Branch name '$BRANCH' è valido"
          else
            echo "❌ Branch name '$BRANCH' non segue la convenzione"
            echo "Formato richiesto: <tipo>/<TICKET-ID>-<descrizione>"
            exit 1
          fi
```

---

## Conventional Commits

Le Conventional Commits sono uno standard per i messaggi di commit che rende possibile l'automazione: generazione automatica del changelog, determinazione automatica della versione semantica, e comunicazione chiara della natura delle modifiche.

### Formato

```
<tipo>[scope opzionale][!]: <descrizione>

[body opzionale]

[footer opzionale]
```

### Tipi di Commit

| Tipo | Significato | Effetto sulla versione |
|------|-------------|----------------------|
| `feat` | Nuova funzionalità | MINOR (1.x.0) |
| `fix` | Correzione bug | PATCH (1.0.x) |
| `docs` | Solo documentazione | Nessuno |
| `style` | Formattazione, no cambi logica | Nessuno |
| `refactor` | Ristrutturazione senza nuove feature o fix | Nessuno |
| `perf` | Miglioramento performance | PATCH |
| `test` | Aggiunta o modifica test | Nessuno |
| `build` | Cambi al sistema di build | Nessuno |
| `ci` | Cambi alla configurazione CI | Nessuno |
| `chore` | Manutenzione generica | Nessuno |
| `revert` | Annullamento di un commit precedente | Dipende |

Il suffisso `!` indica un **BREAKING CHANGE** che incrementa la versione MAJOR (x.0.0).

### Esempi Completi

```bash
# Commit semplice - nuova funzionalità
git commit -m "feat: aggiungere endpoint per il recupero password"

# Commit con scope - indica il modulo interessato
git commit -m "fix(auth): correggere validazione token JWT scaduto"

# Commit con body per spiegare il "perché"
git commit -m "refactor(database): migrare da MySQL a PostgreSQL

La migrazione è necessaria per supportare le query JSONB
richieste dal nuovo modulo di analytics. MySQL non offre
un supporto nativo equivalente per dati semi-strutturati.

Ref: PROJ-567"

# Breaking change con footer
git commit -m "feat(api)!: cambiare formato risposta da XML a JSON

BREAKING CHANGE: tutti i client devono aggiornare il parser
delle risposte. La vecchia API XML sarà disponibile per
6 mesi all'endpoint /api/v1/legacy/.

Migration guide: https://docs.example.com/migration-v3"

# Fix con riferimento al ticket
git commit -m "fix(cart): correggere calcolo sconto con coupon multipli

Il calcolo applicava gli sconti in modo cumulativo anziché
sul prezzo originale. Ora ogni coupon è calcolato sul prezzo
base e poi viene applicato lo sconto maggiore.

Fixes: PROJ-890
Reviewed-by: Marco Rossi"
```

### Enforcement con Commitlint e Husky

```bash
# Installazione
npm install --save-dev @commitlint/cli @commitlint/config-conventional husky

# Configurazione commitlint
cat > commitlint.config.js << 'EOF'
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
    'scope-enum': [1, 'always', [
      'auth', 'api', 'ui', 'database', 'config',
      'cart', 'payment', 'notification', 'docs'
    ]],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
    'subject-case': [2, 'never', ['upper-case', 'pascal-case']],
    'subject-empty': [2, 'never'],
    'type-empty': [2, 'never'],
  },
};
EOF

# Configurazione Husky
npx husky init
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
chmod +x .husky/commit-msg
```

### Validazione in CI con GitHub Actions

```yaml
# .github/workflows/commitlint.yml
name: Lint Commit Messages

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - run: npm install --save-dev @commitlint/cli @commitlint/config-conventional

      - name: Validare commit messages
        run: |
          npx commitlint \
            --from ${{ github.event.pull_request.base.sha }} \
            --to ${{ github.event.pull_request.head.sha }} \
            --verbose
```

---

## Template per Pull Request

I template per le Pull Request standardizzano le informazioni fornite con ogni PR, rendendo più efficace il processo di review. Un buon template guida lo sviluppatore a fornire contesto, documentare le modifiche, e confermare che i controlli necessari sono stati effettuati.

### Template Principale

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE/pull_request_template.md -->

## Descrizione

<!-- Descrivi le modifiche in modo chiaro e conciso. Includi il contesto
     e la motivazione dietro la modifica. -->

## Tipo di Modifica

<!-- Metti una X nella casella appropriata -->

- [ ] Bug fix (modifica non-breaking che risolve un problema)
- [ ] Nuova funzionalità (modifica non-breaking che aggiunge funzionalità)
- [ ] Breaking change (fix o feature che causerebbe il malfunzionamento di funzionalità esistenti)
- [ ] Refactoring (ristrutturazione senza cambi funzionali)
- [ ] Documentazione (solo modifiche alla documentazione)
- [ ] Configurazione CI/CD
- [ ] Dipendenze (aggiornamento o aggiunta dipendenze)

## Ticket Correlati

<!-- Elenca i ticket/issue correlati -->

- Closes #
- Related to #

## Modifiche Effettuate

<!-- Elenca le modifiche principali con un elenco puntato -->

-
-
-

## Screenshot / Video

<!-- Se applicabile, aggiungi screenshot o video delle modifiche UI -->

| Prima | Dopo |
|-------|------|
|       |      |

## Come Testare

<!-- Descrivi i passaggi per testare queste modifiche -->

1.
2.
3.

## Checklist

<!-- Verifica che tutti i punti siano soddisfatti -->

- [ ] Il mio codice segue le linee guida del progetto
- [ ] Ho effettuato una self-review del codice
- [ ] Ho commentato il codice nei punti complessi
- [ ] Ho aggiornato la documentazione (se necessario)
- [ ] Le mie modifiche non generano nuovi warning
- [ ] Ho aggiunto test che dimostrano che la fix/feature funziona
- [ ] I test esistenti e i nuovi passano localmente
- [ ] Le modifiche dipendenti sono state mergiate e pubblicate

## Note per i Reviewer

<!-- Qualsiasi informazione aggiuntiva utile per chi deve fare la review -->
```

### Template Specifici per Tipo

È possibile avere template diversi per tipi diversi di PR. GitHub li mostrerà come opzioni quando si crea una nuova PR.

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE/feature.md -->

## Nuova Funzionalità

### Descrizione della Feature

<!-- Cosa fa questa nuova funzionalità? -->

### User Story

Come [tipo di utente],
Voglio [azione/obiettivo],
In modo da [beneficio].

### Criteri di Accettazione

- [ ] Criterio 1
- [ ] Criterio 2
- [ ] Criterio 3

### Impatto sulle Performance

<!-- Questa feature ha impatto sulle performance? Se sì, come è stato mitigato? -->

### Considerazioni sulla Sicurezza

<!-- Ci sono implicazioni di sicurezza? Input utente? Autenticazione? -->

### Modifiche al Database

<!-- Ci sono migrazioni del database? Sono reversibili? -->

- [ ] Nessuna modifica al database
- [ ] Nuova migrazione (reversibile)
- [ ] Nuova migrazione (NON reversibile - richiede approvazione DBA)

### Feature Flag

- [ ] Questa feature è dietro un feature flag
  - Nome flag: `___`
  - Stato default: `disabled`
```

---

## Template per Issue

I template per le issue guidano chi segnala un bug o richiede una feature a fornire tutte le informazioni necessarie, riducendo il back-and-forth e accelerando la risoluzione.

### Bug Report Template (YAML Format)

```yaml
# .github/ISSUE_TEMPLATE/bug_report.yml
name: Segnalazione Bug
description: Segnala un problema per aiutarci a migliorare
title: "[BUG] "
labels: ["bug", "triage"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Grazie per la segnalazione! Compila i campi seguenti per aiutarci
        a riprodurre e risolvere il problema.

  - type: textarea
    id: description
    attributes:
      label: Descrizione del Bug
      description: Una descrizione chiara e concisa del bug.
      placeholder: Descrivi cosa è successo...
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Passi per Riprodurre
      description: I passaggi per riprodurre il comportamento
      value: |
        1. Vai a '...'
        2. Clicca su '...'
        3. Scorri fino a '...'
        4. Osserva l'errore
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Comportamento Atteso
      description: Cosa ti aspettavi che succedesse
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Comportamento Effettivo
      description: Cosa è successo realmente
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Gravità
      options:
        - Critica (blocca il lavoro / perdita dati)
        - Alta (funzionalità principale non funziona)
        - Media (funzionalità secondaria non funziona)
        - Bassa (problema cosmetico o minor)
    validations:
      required: true

  - type: dropdown
    id: environment
    attributes:
      label: Ambiente
      multiple: true
      options:
        - Produzione
        - Staging
        - Development
        - Locale
    validations:
      required: true

  - type: input
    id: version
    attributes:
      label: Versione
      description: Quale versione del software stai usando?
      placeholder: "es. v2.3.1"
    validations:
      required: true

  - type: dropdown
    id: browser
    attributes:
      label: Browser (se applicabile)
      multiple: true
      options:
        - Chrome
        - Firefox
        - Safari
        - Edge
        - Altro
    validations:
      required: false

  - type: textarea
    id: logs
    attributes:
      label: Log / Stack Trace
      description: Se disponibili, incolla i log o lo stack trace
      render: shell

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshot
      description: Se applicabile, aggiungi screenshot

  - type: checkboxes
    id: terms
    attributes:
      label: Verifiche
      options:
        - label: Ho cercato issue simili già esistenti
          required: true
        - label: Ho provato a riprodurre il bug in un ambiente pulito
          required: false
```

### Feature Request Template

```yaml
# .github/ISSUE_TEMPLATE/feature_request.yml
name: Richiesta Funzionalità
description: Suggerisci una nuova funzionalità
title: "[FEATURE] "
labels: ["enhancement", "triage"]

body:
  - type: textarea
    id: problem
    attributes:
      label: Problema da Risolvere
      description: |
        Descrivi il problema che questa funzionalità risolverebbe.
        Es. "Mi frustra quando..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Soluzione Proposta
      description: Descrivi la soluzione che vorresti
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternative Considerate
      description: Hai considerato soluzioni alternative? Quali?

  - type: dropdown
    id: priority
    attributes:
      label: Priorità Suggerita
      options:
        - Critica (il progetto non può procedere senza)
        - Alta (molto utile, da fare presto)
        - Media (utile, può attendere)
        - Bassa (nice-to-have)
    validations:
      required: true

  - type: textarea
    id: context
    attributes:
      label: Contesto Aggiuntivo
      description: Qualsiasi informazione o contesto aggiuntivo
```

### Configurazione del Chooser

```yaml
# .github/ISSUE_TEMPLATE/config.yml
blank_issues_enabled: false
contact_links:
  - name: Domande Generali
    url: https://github.com/org/progetto/discussions
    about: Per domande generali, usa le Discussioni
  - name: Documentazione
    url: https://docs.example.com
    about: Consulta la documentazione prima di aprire un'issue
```

---

## CODEOWNERS: Assegnazione Automatica dei Reviewer

Il file CODEOWNERS definisce quali persone o team sono responsabili per specifiche parti del codebase. Quando una PR modifica file che rientrano in una regola CODEOWNERS, quei proprietari vengono automaticamente aggiunti come reviewer.

### Struttura del File CODEOWNERS

```gitignore
# .github/CODEOWNERS

# Regola di default: il tech lead revisiona tutto ciò che non ha
# un owner specifico
*                       @mia-org/tech-leads

# Frontend
/src/components/        @mia-org/frontend-team
/src/styles/            @mia-org/frontend-team
/src/pages/             @mia-org/frontend-team
*.tsx                   @mia-org/frontend-team
*.css                   @mia-org/frontend-team

# Backend
/src/api/               @mia-org/backend-team
/src/services/          @mia-org/backend-team
/src/models/            @mia-org/backend-team
/src/middleware/         @mia-org/backend-team

# Database
/migrations/            @mia-org/backend-team @mario-rossi
/src/database/          @mia-org/backend-team

# Infrastructure e DevOps
/terraform/             @mia-org/devops-team
/kubernetes/            @mia-org/devops-team
/docker/                @mia-org/devops-team
Dockerfile              @mia-org/devops-team
docker-compose*.yml     @mia-org/devops-team

# CI/CD
/.github/workflows/     @mia-org/devops-team @mia-org/tech-leads
/.github/actions/       @mia-org/devops-team

# Configurazione e Build
package.json            @mia-org/tech-leads
tsconfig.json           @mia-org/tech-leads
webpack.config.js       @mia-org/frontend-team

# Documentazione
/docs/                  @mia-org/tech-leads
*.md                    @mia-org/tech-leads
README.md               @mia-org/tech-leads

# Sicurezza - richiede review del team sicurezza
/src/auth/              @mia-org/security-team
/src/crypto/            @mia-org/security-team
**/security*            @mia-org/security-team

# File sensibili - richiede review del CTO
.github/CODEOWNERS      @cto-username
LICENSE                 @cto-username
```

### Come Funziona CODEOWNERS

1. Uno sviluppatore apre una PR che modifica file in `/src/api/`
2. GitHub controlla CODEOWNERS e trova che `/src/api/` è owned da `@mia-org/backend-team`
3. GitHub aggiunge automaticamente `@mia-org/backend-team` come reviewer richiesti
4. Se la branch protection richiede review da CODEOWNERS, la PR non può essere mergiata finché un membro del team non approva

### Regole di Precedenza

CODEOWNERS segue una regola semplice: **l'ultima regola che matcha vince**. Questo significa che le regole più specifiche devono essere messe alla fine del file.

```gitignore
# Questo NON funziona come ci si aspetta:
/src/api/auth/    @mia-org/security-team
/src/api/         @mia-org/backend-team
# Risultato: /src/api/auth/ sarà reviewata da backend-team
# perché /src/api/ è l'ultima regola che matcha

# Questo è l'ordine corretto:
/src/api/         @mia-org/backend-team
/src/api/auth/    @mia-org/security-team
# Risultato: /src/api/auth/ sarà reviewata da security-team
```

---

## Branch Protection Rules

Le branch protection rules sono il meccanismo principale per garantire la qualità del codice sulla branch principale. Impediscono push diretti, richiedono review e check superati prima del merge, e proteggono la storia del repository.

### Configurazione via GitHub CLI

```bash
# Protezione base per la branch 'main'
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "ci/lint",
      "ci/test",
      "ci/build",
      "security/snyk"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true,
    "dismissal_restrictions": {
      "users": ["tech-lead-username"],
      "teams": ["tech-leads"]
    }
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "required_signatures": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF
```

### Spiegazione di Ogni Opzione

| Opzione | Valore | Effetto |
|---------|--------|---------|
| `required_status_checks.strict` | `true` | Il branch deve essere aggiornato con base prima del merge |
| `required_status_checks.contexts` | lista | Check CI/CD che devono passare |
| `enforce_admins` | `true` | Anche gli admin devono seguire le regole |
| `required_approving_review_count` | `2` | Servono 2 approvazioni |
| `dismiss_stale_reviews` | `true` | Nuovi push invalidano le approvazioni precedenti |
| `require_code_owner_reviews` | `true` | I CODEOWNERS devono approvare |
| `require_last_push_approval` | `true` | Chi ha pushato per ultimo non può auto-approvare |
| `required_linear_history` | `true` | Forza squash merge o rebase (no merge commit) |
| `allow_force_pushes` | `false` | Impedisce la riscrittura della storia |
| `allow_deletions` | `false` | Impedisce la cancellazione del branch |
| `required_conversation_resolution` | `true` | Tutti i commenti devono essere risolti |
| `required_signatures` | `true` | I commit devono essere firmati |

### Rulesets (Funzionalità Avanzata)

GitHub ha introdotto i Rulesets come sostituto moderno delle branch protection rules, con più flessibilità:

```bash
# Creare un ruleset via API
gh api repos/{owner}/{repo}/rulesets \
  --method POST \
  --input - << 'EOF'
{
  "name": "Protezione Branch Principali",
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
        "require_last_push_approval": true,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          { "context": "ci/test" },
          { "context": "ci/lint" },
          { "context": "ci/build" }
        ]
      }
    },
    {
      "type": "required_linear_history"
    },
    {
      "type": "deletion"
    },
    {
      "type": "non_fast_forward"
    },
    {
      "type": "commit_message_pattern",
      "parameters": {
        "name": "Conventional Commits",
        "negate": false,
        "operator": "regex",
        "pattern": "^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\(.+\\))?!?: .+"
      }
    }
  ]
}
EOF
```

---

## Il Processo di Code Review

La code review è uno dei processi più importanti in un team di sviluppo. Fatta bene, migliora la qualità del codice, diffonde conoscenza nel team, individua bug prima che raggiungano la produzione, e mantiene la coerenza del codebase. Fatta male, diventa un bottleneck che rallenta lo sviluppo e genera frustrazione.

### Cosa Cercare in una Code Review

#### 1. Correttezza

```python
# PROBLEMA: Race condition - due thread possono leggere lo stesso valore
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        current = self.count    # Thread A legge 0
        self.count = current + 1  # Thread B potrebbe aver già incrementato

# SOLUZIONE: Usare un lock
import threading

class Counter:
    def __init__(self):
        self.count = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self.count += 1
```

#### 2. Gestione degli Errori

```javascript
// PROBLEMA: Errore silenzioso
async function fetchUser(id) {
  try {
    const response = await api.get(`/users/${id}`);
    return response.data;
  } catch (error) {
    return null; // L'errore è perso, il chiamante non sa cosa è successo
  }
}

// MEGLIO: Propagare l'errore con contesto
async function fetchUser(id) {
  try {
    const response = await api.get(`/users/${id}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null; // Caso legittimo: utente non trovato
    }
    throw new ApplicationError(
      `Failed to fetch user ${id}`,
      { cause: error, userId: id }
    );
  }
}
```

#### 3. Performance

```sql
-- PROBLEMA: N+1 query
-- Il codice Python fa:
-- for user in users:
--     orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)

-- SOLUZIONE: Una singola query con JOIN
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.active = true;
```

#### 4. Sicurezza

```python
# PROBLEMA: SQL injection
def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)

# SOLUZIONE: Query parametrizzata
def get_user(username):
    query = "SELECT * FROM users WHERE username = %s"
    return db.execute(query, (username,))
```

#### 5. Leggibilità e Manutenibilità

```typescript
// PROBLEMA: Logica complessa in una singola espressione
const result = data.filter(x => x.active && x.age > 18 && !x.banned && x.verified)
  .map(x => ({ ...x, score: x.points * (x.premium ? 2 : 1) + (x.referrals * 5) }))
  .sort((a, b) => b.score - a.score)
  .slice(0, 10);

// MEGLIO: Funzioni con nomi descrittivi
function isEligibleUser(user: User): boolean {
  return user.active && user.age > 18 && !user.banned && user.verified;
}

function calculateScore(user: User): number {
  const premiumMultiplier = user.premium ? 2 : 1;
  const referralBonus = user.referrals * 5;
  return user.points * premiumMultiplier + referralBonus;
}

function getTopUsers(users: User[], limit: number = 10): ScoredUser[] {
  return users
    .filter(isEligibleUser)
    .map(user => ({ ...user, score: calculateScore(user) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
```

### Come Dare Feedback nella Code Review

#### Buon Feedback

```
# Specifico, costruttivo, con alternativa proposta
Questo handler non gestisce il caso in cui `request.body` sia undefined.
Se un client invia una richiesta senza body, `JSON.parse()` qui alla riga 42
lancerebbe un'eccezione non gestita.

Suggerimento:
```javascript
const body = request.body ?? {};
```

# Domanda genuina (non retorica)
Ho notato che stiamo usando `any` per il tipo di ritorno qui.
C'è un motivo specifico? Se il tipo è difficile da definire,
potremmo almeno usare `unknown` per forzare type-checking a valle.
```

#### Cattivo Feedback (da evitare)

```
# Troppo vago
"Questo non mi piace"

# Soggettivo senza motivazione
"Io avrei fatto diversamente"

# Nitpick mascherato da problema serio
"Dovresti usare const invece di let qui" (quando non c'è riassegnazione)

# Passivo-aggressivo
"Sei sicuro che funzioni?"
```

### Livelli di Severità nei Commenti

Un sistema di etichette nei commenti di review aiuta a comunicare la priorità:

```
[blocking] Questa query è vulnerabile a SQL injection. Da correggere prima del merge.

[suggestion] Si potrebbe estrarre questa logica in un utility function per riuso.

[question] Qual è il comportamento atteso quando l'utente non è autenticato?

[nitpick] Naming: `getData` è generico, `fetchUserProfile` sarebbe più descrittivo.

[praise] Ottima gestione degli edge case qui! Il fallback graceful è ben pensato.
```

### Automazione della Review con GitHub Actions

```yaml
# .github/workflows/auto-review.yml
name: Automated Review Checks

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

      - name: Controllare dimensione della PR
        run: |
          ADDITIONS=$(gh pr view ${{ github.event.pull_request.number }} --json additions -q '.additions')
          DELETIONS=$(gh pr view ${{ github.event.pull_request.number }} --json deletions -q '.deletions')
          TOTAL=$((ADDITIONS + DELETIONS))

          echo "Linee modificate: +$ADDITIONS -$DELETIONS (totale: $TOTAL)"

          if [ "$TOTAL" -gt 500 ]; then
            echo "::warning::PR molto grande ($TOTAL linee). Considerare di dividere in PR più piccole."
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "⚠️ Questa PR modifica $TOTAL linee. Le PR grandi sono più difficili da revieware e hanno maggiore probabilità di introdurre bug. Considera di dividere le modifiche in PR più piccole e focalizzate."
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  check-todos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Cercare TODO/FIXME nei file modificati
        run: |
          FILES=$(gh pr view ${{ github.event.pull_request.number }} --json files -q '.files[].path')
          FOUND_TODOS=false

          for file in $FILES; do
            if [ -f "$file" ]; then
              TODOS=$(grep -n "TODO\|FIXME\|HACK\|XXX" "$file" || true)
              if [ -n "$TODOS" ]; then
                echo "::warning file=$file::TODO/FIXME trovati:"
                echo "$TODOS"
                FOUND_TODOS=true
              fi
            fi
          done

          if [ "$FOUND_TODOS" = true ]; then
            echo "::notice::TODO/FIXME trovati nei file modificati. Assicurati che siano intenzionali."
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Strategie di Merge per Team

La strategia di merge influenza direttamente la leggibilità della storia del repository, la facilità di debug con `git bisect`, e la complessità dei rollback. Ogni strategia ha vantaggi e svantaggi.

### Merge Commit (No Fast-Forward)

```bash
git merge --no-ff feature/PROJ-123-add-login
```

```
*   Merge branch 'feature/PROJ-123-add-login'  (merge commit)
|\
| * feat: aggiungere validazione password
| * feat: creare form di login
| * feat: aggiungere servizio autenticazione
|/
*   commit precedente su main
```

**Vantaggi**: Preserva la storia completa, facile vedere raggruppamenti logici, facile revertire un'intera feature con un solo `git revert`.

**Svantaggi**: Storia "rumorosa" con molti merge commit, difficile da leggere in repository molto attivi.

**Quando usarlo**: Team che vogliono preservare il contesto completo di ogni feature; quando i commit intermedi sono significativi e ben scritti.

### Squash Merge

```bash
git merge --squash feature/PROJ-123-add-login
git commit -m "feat: aggiungere sistema di login (#123)"
```

```
* feat: aggiungere sistema di login (#123)  (singolo commit)
* commit precedente su main
```

**Vantaggi**: Storia lineare e pulita, ogni commit su main corrisponde a una feature/fix completa, perfetto per `git bisect`.

**Svantaggi**: Perde la storia dei commit intermedi (disponibile solo nella PR chiusa), i commit intermedi dello sviluppatore spariscono.

**Quando usarlo**: Quando i commit intermedi sono disordinati (WIP, fixup, amend); quando si vuole una storia main impeccabile.

### Rebase Merge

```bash
git rebase main feature/PROJ-123-add-login
git checkout main
git merge --ff-only feature/PROJ-123-add-login
```

```
* feat: aggiungere validazione password
* feat: creare form di login
* feat: aggiungere servizio autenticazione
* commit precedente su main
```

**Vantaggi**: Storia lineare ma preserva i commit individuali, ideale quando ogni commit è significativo.

**Svantaggi**: Riscrive gli hash dei commit, può essere confuso per sviluppatori meno esperti, non preserva il raggruppamento logico.

**Quando usarlo**: Team disciplinati che scrivono commit atomici e significativi.

### Matrice Decisionale

| Criterio | Merge Commit | Squash | Rebase |
|----------|-------------|--------|--------|
| Storia pulita | Bassa | Alta | Alta |
| Preserva commit individuali | Sì | No | Sì |
| Facilità di revert feature | Alta (un revert) | Alta (un revert) | Bassa (N revert) |
| git bisect | Buono | Ottimo | Ottimo |
| Complessità per sviluppatori | Bassa | Bassa | Media |
| Tracciabilità PR | Sempre visibile | Sempre visibile | Richiede convenzione |

### Raccomandazione Pratica

Per la maggior parte dei team, **squash merge** è la scelta più pragmatica:

- Su main, ogni commit è una feature o fix completa
- La storia della PR è preservata nell'interfaccia GitHub
- I messaggi di commit possono seguire le Conventional Commits
- `git bisect` è estremamente efficace

Configurare su GitHub: **Settings > General > Pull Requests** — selezionare solo "Allow squash merging" e impostare il formato del messaggio di default.

---

## Release Management: GitFlow vs Trunk-Based Development

### GitFlow

GitFlow è un modello di branching che utilizza branch dedicati per diverse fasi del ciclo di sviluppo.

```
                 main (produzione)
                   |
    ───────────────●───────────●───────────●──── tag: v1.0, v1.1, v2.0
                  /             \         /
    release/v1.1 ●───●───●──────●        /
                /                \      /
    develop ───●───●───●───●───●──●───●───●────
              / \       \              /
    feature/ ●───●       ●───●───●───●
              \
    hotfix/    ●───● (merge to main AND develop)
```

```bash
# Workflow tipico GitFlow

# 1. Inizio nuova feature
git checkout develop
git pull origin develop
git checkout -b feature/PROJ-123-nuova-feature

# 2. Lavoro sulla feature (commit multipli)
git commit -m "feat: implementare la base della feature"
git commit -m "test: aggiungere unit test per la feature"

# 3. Completamento feature -> merge in develop
git checkout develop
git merge --no-ff feature/PROJ-123-nuova-feature
git push origin develop

# 4. Preparazione release
git checkout -b release/v1.2.0 develop

# 5. Bug fix sulla release (solo fix, no nuove feature)
git commit -m "fix: correggere bug scoperto in QA"

# 6. Finalizzazione release
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# 7. Merge back in develop
git checkout develop
git merge --no-ff release/v1.2.0
git push origin develop
```

**Vantaggi di GitFlow**: Chiara separazione tra sviluppo e produzione, supporta rilasci pianificati, buono per software con release schedulate.

**Svantaggi di GitFlow**: Complesso, molti branch da gestire, i merge possono diventare dolorosi, rallenta il ciclo di rilascio.

### Trunk-Based Development

Nel trunk-based development, tutti gli sviluppatori lavorano su branch di breve durata che partono da `main` e vengono mergiate rapidamente (idealmente entro 1-2 giorni).

```
main ────●────●────●────●────●────●────●────●────
         |   / \  /      |  / \  / \  /
feature  ●──●   ●●       ●●●   ●●   ●●
(short-lived, 1-2 days max)
```

```bash
# Workflow tipico Trunk-Based

# 1. Creare branch dal main
git checkout main
git pull
git checkout -b feature/PROJ-456-add-search

# 2. Lavorare in modo incrementale (max 1-2 giorni)
git commit -m "feat: aggiungere componente search bar"
git push -u origin feature/PROJ-456-add-search

# 3. Aprire PR immediatamente (anche WIP)
gh pr create --title "feat: aggiungere ricerca" --draft

# 4. Feature flag per feature non complete
if (featureFlags.isEnabled('new-search')) {
  // nuovo codice
} else {
  // codice esistente
}

# 5. Merge rapido dopo review
gh pr merge --squash --delete-branch
```

**Vantaggi di Trunk-Based**: Ciclo rapido, merge piccoli e frequenti, riduce i conflitti, supporta continuous deployment, main è sempre rilasciabile.

**Svantaggi di Trunk-Based**: Richiede feature flags, richiede una buona CI/CD pipeline, richiede disciplina nel mantenere PR piccole.

### Confronto e Quando Usare Cosa

| Aspetto | GitFlow | Trunk-Based |
|---------|---------|-------------|
| Frequenza rilasci | Settimanale/Mensile | Continua (più volte al giorno) |
| Dimensione team | Medio-grande | Qualsiasi |
| Maturità CI/CD | Qualsiasi | Alta (richiesta) |
| Feature flags | Non necessari | Spesso necessari |
| Complessità | Alta | Bassa |
| Rischio merge conflict | Alto (branch longevi) | Basso (branch brevi) |
| Adatto a | App mobile, embedded, on-premise | SaaS, web app, microservizi |

---

## Gestione degli Hotfix

Gli hotfix sono correzioni urgenti per problemi in produzione. Richiedono un processo accelerato ma comunque controllato.

### Processo Hotfix

```bash
# 1. Creare branch hotfix dal tag di produzione (o da main)
git checkout main
git pull
git checkout -b hotfix/PROJ-999-fix-payment-crash

# 2. Implementare il fix minimale
# (solo la correzione, niente refactoring o feature aggiuntive)
git commit -m "fix(payment): correggere crash durante elaborazione carta

Il servizio di pagamento andava in crash quando il campo CVV
conteneva caratteri non numerici. Aggiunta validazione input
prima dell'invio al gateway.

Fixes: PROJ-999
Severity: Critical
Impact: 15% delle transazioni fallivano"

# 3. Aggiungere test che dimostra il fix
git commit -m "test(payment): aggiungere test per CVV non numerico"

# 4. Aprire PR con tag urgente
gh pr create \
  --title "hotfix: correggere crash pagamento CVV" \
  --label "hotfix,critical,production" \
  --reviewer "tech-lead,senior-dev" \
  --body "## HOTFIX URGENTE

### Problema
Il 15% delle transazioni fallisce con errore 500 quando il CVV contiene spazi.

### Fix
Aggiunta validazione e sanitizzazione del campo CVV prima dell'invio al payment gateway.

### Test
- [x] Test unitario per CVV con spazi
- [x] Test unitario per CVV con lettere
- [x] Testato manualmente in staging

### Rollback Plan
Revertire questo commit. Nessun cambiamento al database."

# 5. Dopo approvazione e merge, taggare immediatamente
git checkout main
git pull
git tag -a v1.2.1 -m "Hotfix: correggere crash pagamento CVV"
git push origin v1.2.1

# 6. Se si usa GitFlow, assicurarsi che il fix sia anche in develop
git checkout develop
git merge main
git push origin develop
```

### Automazione Hotfix con GitHub Actions

```yaml
# .github/workflows/hotfix-deploy.yml
name: Hotfix Deploy

on:
  pull_request:
    types: [closed]
    branches: [main]

jobs:
  deploy-hotfix:
    if: >
      github.event.pull_request.merged == true &&
      contains(github.event.pull_request.labels.*.name, 'hotfix')
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Eseguire test critici
        run: npm test -- --grep "critical|smoke"

      - name: Deploy in produzione
        run: |
          echo "Deploying hotfix to production..."
          # Script di deploy

      - name: Notificare il team
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚨 HOTFIX deployato in produzione: ${{ github.event.pull_request.title }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Tag Management e Versionamento Semantico

### Versionamento Semantico (SemVer)

Il versionamento semantico segue il formato `MAJOR.MINOR.PATCH`:

- **MAJOR** (x.0.0): Cambiamenti incompatibili con le versioni precedenti (breaking changes)
- **MINOR** (0.x.0): Nuove funzionalità compatibili con le versioni precedenti
- **PATCH** (0.0.x): Correzioni di bug compatibili con le versioni precedenti

Inoltre si possono usare pre-release e build metadata:
- Pre-release: `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.1`
- Build metadata: `1.0.0+build.123`

### Gestione dei Tag

```bash
# Creare un tag annotato (raccomandato per rilasci)
git tag -a v1.2.0 -m "Release v1.2.0

Nuove funzionalità:
- Aggiunto sistema di notifiche push
- Aggiunto export CSV per report

Bug fix:
- Corretto calcolo IVA per paesi extra-UE
- Corretto timeout sessione prematura"

# Pushare i tag
git push origin v1.2.0
# Oppure tutti i tag:
git push origin --tags

# Elencare i tag
git tag --list 'v1.*' --sort=-version:refname

# Verificare un tag firmato
git tag -v v1.2.0

# Eliminare un tag (locale e remoto)
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0

# Creare una release da un tag
gh release create v1.2.0 \
  --title "Release v1.2.0" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

### Automazione del Tagging

```yaml
# .github/workflows/auto-tag.yml
name: Auto Tag on Merge

on:
  push:
    branches: [main]

jobs:
  tag:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Determinare il tipo di bump
        id: bump
        run: |
          # Analizzare i commit dall'ultimo tag
          LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
          COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")

          if echo "$COMMITS" | grep -q "BREAKING CHANGE\|!:"; then
            echo "type=major" >> $GITHUB_OUTPUT
          elif echo "$COMMITS" | grep -q "^feat"; then
            echo "type=minor" >> $GITHUB_OUTPUT
          elif echo "$COMMITS" | grep -q "^fix\|^perf"; then
            echo "type=patch" >> $GITHUB_OUTPUT
          else
            echo "type=none" >> $GITHUB_OUTPUT
          fi
          echo "last_tag=$LAST_TAG" >> $GITHUB_OUTPUT

      - name: Calcolare nuova versione
        if: steps.bump.outputs.type != 'none'
        id: version
        run: |
          LAST="${{ steps.bump.outputs.last_tag }}"
          VERSION="${LAST#v}"
          IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

          case "${{ steps.bump.outputs.type }}" in
            major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
            minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
            patch) PATCH=$((PATCH + 1)) ;;
          esac

          echo "new_tag=v${MAJOR}.${MINOR}.${PATCH}" >> $GITHUB_OUTPUT

      - name: Creare tag e release
        if: steps.bump.outputs.type != 'none'
        run: |
          git tag -a ${{ steps.version.outputs.new_tag }} \
            -m "Release ${{ steps.version.outputs.new_tag }}"
          git push origin ${{ steps.version.outputs.new_tag }}

          gh release create ${{ steps.version.outputs.new_tag }} \
            --generate-notes --latest
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Generazione Automatica del Changelog

### Changelog Manuale con Conventional Commits

Quando si usano le Conventional Commits, il changelog può essere generato automaticamente raggruppando i commit per tipo.

### Usando `conventional-changelog`

```bash
# Installazione
npm install -g conventional-changelog-cli

# Generare il changelog completo
conventional-changelog -p angular -i CHANGELOG.md -s -r 0

# Generare solo l'ultimo rilascio
conventional-changelog -p angular -i CHANGELOG.md -s
```

### Output Tipico del Changelog

```markdown
# Changelog

## [1.3.0](https://github.com/org/repo/compare/v1.2.0...v1.3.0) (2026-04-12)

### Features

* **auth:** aggiungere login con Google OAuth ([#145](https://github.com/org/repo/issues/145)) ([abc1234](https://github.com/org/repo/commit/abc1234))
* **notification:** implementare notifiche push real-time ([#152](https://github.com/org/repo/issues/152)) ([def5678](https://github.com/org/repo/commit/def5678))
* **export:** aggiungere export CSV per tutti i report ([#160](https://github.com/org/repo/issues/160)) ([ghi9012](https://github.com/org/repo/commit/ghi9012))

### Bug Fixes

* **cart:** correggere calcolo IVA per paesi extra-UE ([#148](https://github.com/org/repo/issues/148)) ([jkl3456](https://github.com/org/repo/commit/jkl3456))
* **session:** correggere timeout sessione prematura dopo 5min ([#155](https://github.com/org/repo/issues/155)) ([mno7890](https://github.com/org/repo/commit/mno7890))

### Performance Improvements

* **database:** ottimizzare query report mensile (da 12s a 0.8s) ([#158](https://github.com/org/repo/issues/158)) ([pqr1234](https://github.com/org/repo/commit/pqr1234))

### BREAKING CHANGES

* **api:** il formato di risposta dell'endpoint /users è cambiato da array a oggetto paginato. Aggiornare i client. Guida migrazione: docs/migration-v1.3.md
```

### GitHub Actions per Changelog Automatico

```yaml
# .github/workflows/release.yml
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

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Generare changelog
        id: changelog
        run: |
          npm install conventional-changelog-cli
          npx conventional-changelog -p angular -r 2 -o RELEASE_NOTES.md
          cat RELEASE_NOTES.md

      - name: Creare GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body_path: RELEASE_NOTES.md
          generate_release_notes: false
          draft: false
          prerelease: ${{ contains(github.ref, '-alpha') || contains(github.ref, '-beta') || contains(github.ref, '-rc') }}
```

---

## Workflow Completo di Esempio

Mettiamo tutto insieme in un workflow end-to-end per una feature tipica.

```bash
# === GIORNO 1: Inizio lavoro ===

# 1. Aggiornare main e creare branch
git checkout main
git pull
git checkout -b feature/PROJ-200-user-notifications

# 2. Lavorare sulla feature con commit atomici
# ... scrivere codice ...
git add src/services/notification.ts
git commit -m "feat(notification): creare servizio di notifiche base"

# ... scrivere test ...
git add tests/notification.test.ts
git commit -m "test(notification): aggiungere test unitari per il servizio"

# ... aggiornare UI ...
git add src/components/NotificationBell.tsx
git commit -m "feat(notification): aggiungere componente campanella notifiche"

# 3. Push e creazione PR (anche in stato draft)
git push -u origin feature/PROJ-200-user-notifications
gh pr create --draft \
  --title "feat: sistema di notifiche utente" \
  --body "Implementazione del sistema di notifiche in-app.

## Modifiche
- Servizio notifiche con supporto WebSocket
- Componente UI campanella con badge contatore
- Endpoint API per CRUD notifiche

Closes #200"

# === GIORNO 2: Completamento e review ===

# 4. Completare il lavoro
git add .
git commit -m "feat(notification): aggiungere endpoint API per notifiche"
git push

# 5. Marcare la PR come pronta per review
gh pr ready

# 6. Richiedere review
gh pr edit --add-reviewer mario-rossi,lucia-bianchi

# === REVIEW ===

# 7. Rispondere ai commenti della review
git add src/services/notification.ts
git commit -m "fix(notification): aggiungere rate limiting come richiesto in review"
git push

# === MERGE ===

# 8. Dopo approvazione, merge con squash
gh pr merge --squash --delete-branch

# Il risultato su main è un singolo commit:
# "feat: sistema di notifiche utente (#200)"
```

---

## Best Practice e Anti-Pattern

### Best Practice

1. **Branch di breve durata**: Non più di 2-3 giorni. Se la feature è grande, dividila in parti.
2. **Commit atomici**: Ogni commit fa una cosa sola e lascia il codebase in stato funzionante.
3. **Pull frequenti**: Aggiornare il branch dal main almeno una volta al giorno.
4. **PR piccole**: Idealmente sotto le 400 linee modificate. Le PR grandi sono più difficili da revieware e hanno più probabilità di contenere bug.
5. **Review tempestive**: Rispondere alle richieste di review entro 4-8 ore lavorative.
6. **Self-review prima della PR**: Rileggere il proprio diff prima di chiedere una review.
7. **Test prima del merge**: La CI deve passare, e lo sviluppatore deve aver testato manualmente i casi edge.

### Anti-Pattern

1. **Branch longevo ("feature branch hell")**: Branch che vivono per settimane, accumulando divergenza da main.
2. **"Big bang" merge**: Mergiare migliaia di linee in una volta.
3. **Commit "WIP" su main**: Usare squash merge per evitarlo.
4. **Review superficiale**: Approvare senza leggere il codice (rubber stamping).
5. **Push diretto a main**: Bypassare il processo di PR, anche per "piccole modifiche".
6. **Ignorare i conflitti di merge**: Risolvere i conflitti senza capire il codice dell'altro sviluppatore.
7. **Non aggiornare il branch**: Lavorare su un branch basato su una versione vecchia di main.

---

## Risoluzione dei Conflitti: Walkthrough Completo

I conflitti di merge sono inevitabili quando più sviluppatori lavorano sullo stesso codebase. Un conflitto si verifica quando Git non riesce a determinare automaticamente quale versione del codice mantenere, perché due branch hanno modificato le stesse righe dello stesso file, oppure un branch ha modificato un file che l'altro branch ha eliminato. Invece di temere i conflitti, un team maturo li gestisce come parte normale del flusso di lavoro, con strumenti e processi chiari.

### Configurazione Preventiva

Prima di tutto, configurare Git per rendere i conflitti più facili da comprendere e risolvere:

```bash
# Abilitare il formato diff3 che mostra anche la versione "base" (antenato comune)
# Questo è fondamentale: senza diff3 vedi solo "versione A vs versione B"
# Con diff3 vedi "versione originale → cosa ha fatto A → cosa ha fatto B"
git config --global merge.conflictStyle diff3

# Abilitare rerere (reuse recorded resolution)
# Git ricorda come hai risolto un conflitto e lo riapplica automaticamente
# se incontra lo stesso conflitto in futuro (es. durante rebase ripetuti)
git config --global rerere.enabled true

# Abilitare il log di rerere per debug
git config --global rerere.autoupdate true
```

### Anatomia di un Conflitto con diff3

Quando si verifica un conflitto con `diff3` abilitato, il file mostrerà tre sezioni:

```
<<<<<<< HEAD (il tuo branch corrente)
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
||||||| merged common ancestors (versione originale prima delle modifiche)
function calculateTotal(items) {
  let total = 0;
  for (const item of items) {
    total += item.price;
  }
  return total;
}
=======  (il branch che stai mergiando)
function calculateTotal(items) {
  return items
    .filter(item => item.active)
    .reduce((sum, item) => sum + item.price * item.quantity * (1 - item.discount), 0);
}
>>>>>>> feature/PROJ-456-add-discounts
```

**Analisi del conflitto**: L'originale era un semplice loop che sommava i prezzi. Il branch corrente (HEAD) ha introdotto il calcolo con quantità usando `reduce`. Il branch feature ha aggiunto sia il filtro per item attivi che il calcolo dello sconto. La risoluzione corretta deve integrare entrambe le modifiche: filtro per item attivi, calcolo con quantità, e applicazione dello sconto.

### Walkthrough Passo-Passo: Risoluzione di un Conflitto Reale

Scenario: Due sviluppatori hanno modificato lo stesso file di configurazione API.

```bash
# Passo 1: Aggiornare il branch e tentare il merge
git checkout feature/PROJ-200-user-notifications
git fetch origin
git merge origin/main

# Output:
# Auto-merging src/config/api.ts
# CONFLICT (content): Merge conflict in src/config/api.ts
# Auto-merging src/services/user.ts
# CONFLICT (content): Merge conflict in src/services/user.ts
# Automatic merge failed; fix conflicts and then commit the result.

# Passo 2: Vedere quali file hanno conflitti
git status
# Mostra:
# both modified: src/config/api.ts
# both modified: src/services/user.ts

# Passo 3: Vedere il diff di ogni file in conflitto
git diff --name-only --diff-filter=U

# Passo 4: Usare un merge tool (opzionale ma raccomandato)
# Configurare il merge tool preferito
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'

# Lanciare il merge tool
git mergetool

# Passo 5: Dopo aver risolto manualmente, verificare
# Controllare che non ci siano più marker di conflitto
grep -rn "<<<<<<" src/
grep -rn "======" src/
grep -rn ">>>>>>" src/

# Passo 6: Testare che il codice funzioni
npm test
npm run build

# Passo 7: Completare il merge
git add src/config/api.ts src/services/user.ts
git commit -m "fix: risolvere conflitti merge con main

Integrato le modifiche di rate limiting (main) con il
sistema di notifiche (feature branch). Entrambe le
funzionalità sono preservate.

Conflitti risolti in:
- src/config/api.ts: combinati endpoint notifiche con rate limit config
- src/services/user.ts: integrato notification service con nuovo user model"
```

### Strategie di Risoluzione per Tipo di Conflitto

#### Conflitto su File di Configurazione (package.json, tsconfig.json)

```bash
# Strategia: spesso il conflitto è su versioni di dipendenze
# Accettare la versione più recente e rigenerare il lockfile

# Per package.json: risolvere manualmente scegliendo le versioni corrette
# poi rigenerare il lockfile
npm install   # o yarn install / pnpm install

# Per lockfile: mai risolvere manualmente, rigenerare sempre
git checkout --theirs package-lock.json
npm install
git add package-lock.json
```

#### Conflitto su Migrazioni Database

```bash
# Strategia: le migrazioni NON devono mai essere unite
# Se due branch hanno creato migrazioni con lo stesso numero sequenziale,
# rinumerare quella del branch feature

# Esempio: entrambi i branch hanno creato migration_042_*
# Rinominare la propria a migration_043_*
mv migrations/042_add_notifications.sql migrations/043_add_notifications.sql

# Aggiornare eventuali riferimenti interni alla migrazione
```

#### Conflitto su File Auto-Generati

```bash
# Strategia: rigenerare il file invece di risolvere il conflitto
# Esempi: file .generated.ts, schema GraphQL compilati, documentazione API

# Accettare una versione qualsiasi
git checkout --theirs src/generated/schema.ts

# Poi rigenerare
npm run generate
git add src/generated/schema.ts
```

### Prevenzione dei Conflitti

Le strategie più efficaci per ridurre la frequenza e la complessità dei conflitti sono:

1. **Branch di breve durata**: Mergiare entro 1-2 giorni riduce drasticamente la probabilità di conflitti.
2. **Aggiornamento frequente**: Fare `git pull --rebase origin main` almeno una volta al giorno.
3. **Divisione dei file grandi**: File con più di 500 righe modificati da più sviluppatori sono una fonte costante di conflitti.
4. **Comunicazione nel team**: Se due sviluppatori stanno per modificare la stessa area di codice, coordinarsi in anticipo.
5. **Feature flag**: Permettono di mergiare codice incompleto senza conflitti logici, perché il codice è disattivato.

### Comando `rerere` in Azione

```bash
# Scenario: stai facendo rebase e lo stesso conflitto appare più volte

# Prima risoluzione: Git registra la soluzione
git merge origin/main
# Risolvi il conflitto manualmente in api.ts
git add src/config/api.ts
git commit

# Seconda volta (es. dopo un rebase):
git rebase origin/main
# Git riconosce il conflitto e lo risolve automaticamente!
# Output: "Resolved 'src/config/api.ts' using previous resolution."

# Verificare cosa rerere ha registrato
git rerere diff
git rerere status

# Cancellare una risoluzione registrata (se era sbagliata)
git rerere forget src/config/api.ts
```

### GitHub Action per Rilevamento Conflitti Preventivo

```yaml
# .github/workflows/conflict-detection.yml
name: Conflict Detection

on:
  push:
    branches: [main]

jobs:
  check-open-prs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verificare conflitti nelle PR aperte
        run: |
          OPEN_PRS=$(gh pr list --state open --json number,headRefName -q '.[].number')

          for PR in $OPEN_PRS; do
            BRANCH=$(gh pr view $PR --json headRefName -q '.headRefName')
            echo "Verificando PR #$PR (branch: $BRANCH)..."

            git fetch origin $BRANCH
            if ! git merge-tree $(git merge-base HEAD FETCH_HEAD) HEAD FETCH_HEAD | grep -q "^changed in both"; then
              echo "PR #$PR: nessun conflitto"
            else
              echo "::warning::PR #$PR ($BRANCH) ha potenziali conflitti con main"
              gh pr comment $PR --body "Attenzione: dopo l'ultimo push su main, questo branch potrebbe avere conflitti. Si consiglia di aggiornare il branch con \`git merge origin/main\` o \`git rebase origin/main\`."
            fi
          done
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Monorepo vs Polyrepo: Architettura dei Repository

La scelta tra monorepo (tutti i progetti in un unico repository) e polyrepo (un repository per ogni progetto o servizio) è una decisione architetturale fondamentale che influenza il workflow del team, la CI/CD pipeline, la gestione delle dipendenze, e la cultura di collaborazione. Non esiste una risposta universale: la scelta dipende dalla dimensione del team, dalla struttura del progetto, dal livello di maturità degli strumenti, e dagli obiettivi a lungo termine.

### Cos'è un Monorepo

Un monorepo è un singolo repository Git che contiene il codice di più progetti, servizi, o componenti. Aziende come Google, Meta, Microsoft, e Uber utilizzano monorepo su scala massiva. Tuttavia, un monorepo non significa un monolite: il codice rimane modulare e organizzato, ma vive sotto un unico albero Git.

```
# Struttura tipica monorepo
mia-org-monorepo/
├── apps/
│   ├── web-frontend/          # Applicazione React
│   │   ├── src/
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── mobile-app/            # Applicazione React Native
│   │   ├── src/
│   │   └── package.json
│   └── api-backend/           # Server Node.js/Express
│       ├── src/
│       └── package.json
├── packages/
│   ├── shared-ui/             # Componenti UI condivisi
│   │   ├── src/
│   │   └── package.json
│   ├── shared-utils/          # Utility functions condivise
│   │   ├── src/
│   │   └── package.json
│   └── shared-types/          # TypeScript types condivisi
│       ├── src/
│       └── package.json
├── tools/
│   ├── scripts/               # Script di build/deploy
│   └── generators/            # Code generators
├── nx.json                    # o turbo.json per Turborepo
├── package.json               # Root workspace
└── pnpm-workspace.yaml        # Workspace definition
```

### Cos'è un Polyrepo

Un polyrepo utilizza repository separati per ogni progetto o servizio. Ogni repository ha il proprio ciclo di vita, la propria CI/CD pipeline, e le proprie regole di accesso.

```
# Struttura tipica polyrepo (repository separati)
mia-org/web-frontend       → https://github.com/mia-org/web-frontend
mia-org/mobile-app         → https://github.com/mia-org/mobile-app
mia-org/api-backend        → https://github.com/mia-org/api-backend
mia-org/shared-ui          → https://github.com/mia-org/shared-ui (npm package)
mia-org/shared-utils       → https://github.com/mia-org/shared-utils (npm package)
mia-org/shared-types       → https://github.com/mia-org/shared-types (npm package)
```

### Matrice Decisionale Completa

| Criterio | Monorepo | Polyrepo |
|----------|----------|----------|
| **Modifiche cross-progetto** | Un singolo commit atomico | Richiede PR coordinate su più repository |
| **Condivisione codice** | Import diretto, nessuna pubblicazione | Richiede pacchetti pubblicati su registry |
| **CI/CD** | Pipeline unificata ma richiede tooling per affected-only builds | Pipeline indipendenti per servizio |
| **Tempo di clone** | Lento per repository grandi senza shallow clone | Veloce, si clona solo ciò che serve |
| **Onboarding** | Più facile: un solo clone per tutto | Più complesso: capire quali repo clonare |
| **Ownership del codice** | CODEOWNERS in un file, visibilità totale | Permessi repository nativi, separazione forte |
| **Gestione dipendenze** | Versione unica condivisa, aggiornamenti atomici | Versioni indipendenti, aggiornamenti asincroni |
| **Scalabilità team** | Richiede tooling dedicato (Nx, Turborepo, Bazel) | Scala naturalmente con repository separati |
| **Sicurezza** | Accesso granulare più complesso da gestire | Permessi repository-level nativi |
| **Dimensione ideale team** | 5-200 sviluppatori con buon tooling | Qualsiasi, specialmente team >200 |

### Tooling per Monorepo nel 2025

```bash
# Nx — il più maturo e feature-rich
npx create-nx-workspace@latest mia-org --preset=ts
# Supporta: task caching, affected commands, module boundaries,
# code generators, dependency graph visualization

# Turborepo — il più semplice da adottare
npx create-turbo@latest
# Supporta: task caching (locale e remoto), parallel execution,
# incremental builds, pipeline definitions

# Esempio: turbo.json per definire la pipeline
cat > turbo.json << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["build"]
    },
    "lint": {},
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
EOF
```

### CI Condizionale per Monorepo

```yaml
# .github/workflows/ci-monorepo.yml
name: Monorepo CI

on:
  pull_request:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      web: ${{ steps.filter.outputs.web }}
      api: ${{ steps.filter.outputs.api }}
      shared: ${{ steps.filter.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            web:
              - 'apps/web-frontend/**'
              - 'packages/shared-ui/**'
              - 'packages/shared-types/**'
            api:
              - 'apps/api-backend/**'
              - 'packages/shared-utils/**'
              - 'packages/shared-types/**'
            shared:
              - 'packages/**'

  test-web:
    needs: detect-changes
    if: needs.detect-changes.outputs.web == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx turbo test --filter=web-frontend...

  test-api:
    needs: detect-changes
    if: needs.detect-changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx turbo test --filter=api-backend...

  test-shared:
    needs: detect-changes
    if: needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx turbo test --filter=...shared-*
```

### Quando Scegliere Cosa

**Scegliere monorepo quando:**
- Il team è di dimensione medio-piccola (5-50 sviluppatori) e lavora su componenti strettamente accoppiati
- Si condivide molto codice tra progetti (componenti UI, tipi, utility)
- Si vuole garantire che le modifiche cross-progetto siano atomiche e testate insieme
- Si ha la volontà di investire in tooling (Nx, Turborepo, Bazel)

**Scegliere polyrepo quando:**
- I servizi sono veramente indipendenti con cicli di rilascio diversi
- Team diversi devono avere isolamento completo (anche per ragioni di sicurezza o compliance)
- Il codebase è molto grande e diversificato (linguaggi diversi, framework diversi)
- Si preferisce la semplicità nativa di Git senza tooling aggiuntivo

**Approccio ibrido**: Alcuni team adottano un modello intermedio con un monorepo per i servizi strettamente accoppiati e polyrepo per servizi completamente indipendenti.

---

## InnerSource: Pratiche Open Source in Azienda

InnerSource è l'applicazione delle pratiche e della cultura open source all'interno dei confini di un'organizzazione. Invece di ogni team che lavora in silos con il proprio codice proprietario inaccessibile agli altri, InnerSource promuove la trasparenza, la collaborazione cross-team, e la possibilità per qualsiasi sviluppatore dell'azienda di contribuire a qualsiasi progetto interno.

### Principi Fondamentali

1. **Visibilità del codice**: Tutti i repository sono visibili a tutti gli sviluppatori dell'organizzazione, anche se non possono pushare direttamente.
2. **Contribuzione tramite fork e PR**: Qualsiasi sviluppatore può forkare un repository interno, proporre modifiche via PR, e partecipare alle discussioni.
3. **Trusted Committer**: Ogni progetto ha un "trusted committer" (TC) responsabile di revieware e mergiare le contribuzioni esterne al team.
4. **Documentazione come prerequisito**: Ogni progetto deve avere documentazione sufficiente per permettere a sviluppatori esterni di contribuire.

### Il Ruolo del Trusted Committer

Il Trusted Committer è il ponte tra il team che possiede il progetto e i contributori esterni. Le sue responsabilità includono:

- Revieware le PR dei contributori esterni in tempi ragionevoli (max 48 ore lavorative)
- Fornire feedback costruttivo e dettagliato per aiutare i contributori a migliorare
- Mantenere aggiornata la documentazione per i contributori (`CONTRIBUTING.md`)
- Definire e comunicare gli standard di codice del progetto
- Fare mentoring ai contributori frequenti, potenzialmente promuovendoli a committer

```markdown
<!-- CONTRIBUTING.md per un progetto InnerSource -->

# Come Contribuire a [Nome Progetto]

## Trusted Committers
- @mario-rossi (backend, API)
- @lucia-bianchi (frontend, UI)

## Tempo di risposta
- Review iniziale PR: entro 2 giorni lavorativi
- Follow-up dopo modifiche: entro 1 giorno lavorativo

## Prima di contribuire
1. Controllare le issue aperte per evitare duplicati
2. Per modifiche significative, aprire prima una issue di discussione
3. Leggere le [Guide di Stile](docs/STYLE_GUIDE.md)
4. Seguire le Conventional Commits per i messaggi di commit

## Processo di Contribuzione
1. Forkare il repository (o creare un branch se si ha accesso)
2. Creare il branch: `feature/TEAM-TICKET-descrizione`
3. Implementare la modifica con test
4. Aprire una PR taggando un Trusted Committer
5. Rispondere al feedback entro 3 giorni lavorativi

## Cosa accettiamo
- Bug fix con test di regressione
- Nuove feature allineate alla roadmap (verificare con i TC)
- Miglioramenti alla documentazione
- Miglioramenti alle performance con benchmark

## Cosa NON accettiamo senza discussione preventiva
- Refactoring architetturali
- Nuove dipendenze esterne
- Modifiche alle API pubbliche
- Breaking changes
```

### Configurazione GitHub per InnerSource

```bash
# Configurare la visibilità dei repository nell'organizzazione
# Tutti i repository interni visibili a tutti i membri
# (impostazione a livello di organizzazione su GitHub)

# Creare un template repository per nuovi progetti InnerSource
gh repo create mia-org/template-innersource \
  --internal \
  --template \
  --description "Template per nuovi progetti InnerSource"

# Il template include:
# - README.md con struttura standard
# - CONTRIBUTING.md con processo di contribuzione
# - .github/CODEOWNERS con Trusted Committers
# - .github/ISSUE_TEMPLATE/ con template standard
# - .github/PULL_REQUEST_TEMPLATE.md
# - LICENSE interna
# - docs/ARCHITECTURE.md con overview architetturale
```

### Metriche InnerSource

Per misurare il successo di un programma InnerSource, tracciare:

| Metrica | Target | Come misurare |
|---------|--------|---------------|
| PR da contributori esterni | > 20% del totale | GitHub Insights, filtrare per team |
| Tempo medio prima review | < 48 ore lavorative | Analisi timestamp PR |
| Tasso di accettazione PR esterne | > 60% | PR merge/totale per contributori esterni |
| Numero di progetti con CONTRIBUTING.md | 100% | Script di audit periodico |
| Contributori unici per progetto | Crescita trimestrale | GitHub contributor graph |

### Benefici Misurabili

Le aziende che adottano InnerSource riportano benefici concreti: riduzione del codice duplicato (team diversi che reimplementano la stessa funzionalità), accelerazione dello sviluppo (riuso di componenti testati), miglioramento della qualità del codice (più occhi sul codice), diffusione della conoscenza (gli sviluppatori imparano come lavorano gli altri team), e maggiore soddisfazione degli sviluppatori (libertà di contribuire dove vedono opportunità).

---

## Ship / Show / Ask: Strategia di Branching Adattiva

Ship / Show / Ask è una strategia di branching introdotta da Rouan Wilsenach che supera la dicotomia tradizionale tra "sempre PR con review" e "push diretto su main". L'idea centrale è che non tutte le modifiche hanno lo stesso livello di rischio o incertezza, e il processo di review dovrebbe adattarsi di conseguenza.

### Le Tre Categorie

#### Ship (Spedisci)

Fai la modifica direttamente su main (o la merghi immediatamente senza attendere review). Usi le normali tecniche di Continuous Integration (test automatici, lint, build) per garantire la sicurezza, ma non aspetti feedback umano.

**Quando usare Ship:**
- Correzioni di typo nella documentazione
- Aggiornamento di dipendenze minori (patch version) già testate dalla CI
- Modifiche a file di configurazione non critici
- Aggiunta di test per codice già esistente
- Piccole correzioni di stile o formattazione

#### Show (Mostra)

Fai la modifica su un branch, apri una Pull Request, ma la merghi immediatamente senza attendere l'approvazione di nessuno. La PR resta aperta per permettere ai colleghi di leggere il codice, lasciare commenti, e imparare dalla modifica, ma non blocca il flusso di lavoro.

**Quando usare Show:**
- Refactoring sicuri con buona copertura di test
- Nuove feature piccole e ben definite
- Implementazioni che seguono pattern consolidati nel codebase
- Modifiche che vorresti condividere per diffondere conoscenza

#### Ask (Chiedi)

Fai la modifica su un branch, apri una Pull Request, e attendi il feedback prima di mergiare. Questo è il flusso tradizionale di code review.

**Quando usare Ask:**
- Codice relativo ad autenticazione, autorizzazione, o pagamenti
- Nuovi pattern architetturali non ancora stabiliti nel team
- Aree del codebase con cui non hai familiarità
- Decisioni di design con più alternative possibili
- Qualsiasi breaking change

### Diagramma Decisionale

```
                    ┌──────────────────────────┐
                    │   Ho una modifica da fare │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Sono sicuro che è         │
                    │ corretta e a basso        │
                    │ rischio?                  │
                    └──────┬───────────┬────────┘
                      Sì   │           │  No
                           │           │
              ┌────────────▼──┐    ┌───▼────────────────┐
              │ Qualcuno del  │    │ Ho bisogno di       │
              │ team potrebbe │    │ feedback prima di   │
              │ beneficiare   │    │ procedere?          │
              │ nel vederla?  │    └───┬───────────┬─────┘
              └──┬────────┬───┘       Sì│          │No
                 │Sì      │No          │           │
                 │        │            │           │
           ┌─────▼──┐  ┌─▼────┐  ┌────▼──┐  ┌────▼──┐
           │  SHOW  │  │ SHIP │  │  ASK  │  │ SHOW  │
           └────────┘  └──────┘  └───────┘  └───────┘
```

### Prerequisiti per Adottare Ship / Show / Ask

Questa strategia richiede un alto livello di fiducia e maturità nel team:

1. **Suite di test robusta**: La CI deve catturare regressioni automaticamente.
2. **Cultura di fiducia**: Il team deve fidarsi del giudizio individuale dei colleghi.
3. **Monitoring in produzione**: Se qualcosa sfugge alla CI, il monitoring deve rilevarlo rapidamente.
4. **Facilità di rollback**: Deploy reversibili in pochi minuti.
5. **Feature flag**: Per disaccoppiare il deploy dall'attivazione delle feature.

### Esempio Pratico di Workflow Misto

```bash
# SHIP: Fix typo nella documentazione
git checkout main
git pull
# ... modifica il file ...
git commit -m "docs: correggere typo nel README"
git push origin main

# SHOW: Refactoring del modulo di logging
git checkout -b refactor/PROJ-300-improve-logging
# ... refactoring con test ...
git push -u origin refactor/PROJ-300-improve-logging
gh pr create --title "refactor: migliorare struttura modulo logging" \
  --body "Refactoring del modulo logging per usare pattern strategy.
Tutti i test passano. Mergio subito ma lascio la PR per visibilità."
gh pr merge --squash --delete-branch
# I colleghi possono comunque commentare sulla PR chiusa

# ASK: Nuovo sistema di caching
git checkout -b feature/PROJ-350-add-redis-cache
# ... implementazione ...
git push -u origin feature/PROJ-350-add-redis-cache
gh pr create --title "feat: aggiungere layer di caching Redis" \
  --body "Implementazione del caching con Redis. Vorrei feedback su:
1. La strategia di invalidazione cache (TTL vs event-driven)
2. La gestione del fallback quando Redis non è disponibile
3. L'impatto sulle performance del serializer

Attendo review prima di mergiare."
gh pr edit --add-reviewer senior-dev,team-lead
```

---

## Stacked Pull Request: PR Incrementali

Le Stacked Pull Request (SPR) rappresentano un'evoluzione del workflow tradizionale di PR. Invece di creare una singola PR enorme per una feature complessa, si suddivide il lavoro in una serie di PR piccole e sequenziali, dove ogni PR dipende dalla precedente. Questo approccio risolve uno dei problemi più comuni dei team: le PR troppo grandi che nessuno ha voglia di revieware.

### Il Problema delle PR Grandi

Le ricerche sulla code review mostrano una correlazione diretta tra dimensione della PR e qualità della review. Una PR con 50 righe riceve commenti dettagliati e approfonditi. Una PR con 500 righe riceve un "LGTM" frettoloso. Una PR con 2000 righe non viene nemmeno letta con attenzione. Dividere il lavoro in PR piccole e sequenziali (stacked) mantiene ogni review focalizzata e gestibile.

### Come Funziona lo Stacking

```
main ──────●──────────────────────────────────
            \
             ● PR #1: Aggiungere modello dati (50 righe)
              \
               ● PR #2: Aggiungere repository layer (80 righe)
                \
                 ● PR #3: Aggiungere servizio business logic (120 righe)
                  \
                   ● PR #4: Aggiungere endpoint API (60 righe)
                    \
                     ● PR #5: Aggiungere UI (100 righe)
```

Ogni PR è piccola, focalizzata, e reviewabile in pochi minuti. I reviewer vedono un contesto limitato e possono dare feedback più approfondito.

### Workflow Manuale con Git

```bash
# 1. Creare il primo branch dello stack
git checkout main
git checkout -b stack/PROJ-400-data-model
# ... implementare il modello dati ...
git commit -m "feat(db): aggiungere modello dati per notifiche"
git push -u origin stack/PROJ-400-data-model
gh pr create --title "feat: modello dati notifiche [1/5]" \
  --base main

# 2. Creare il secondo branch basato sul primo
git checkout -b stack/PROJ-400-repository
# ... implementare il repository ...
git commit -m "feat(db): aggiungere repository per notifiche"
git push -u origin stack/PROJ-400-repository
gh pr create --title "feat: repository notifiche [2/5]" \
  --base stack/PROJ-400-data-model  # base = branch precedente nello stack

# 3. Creare il terzo branch basato sul secondo
git checkout -b stack/PROJ-400-service
# ... implementare il servizio ...
git commit -m "feat: aggiungere servizio notifiche"
git push -u origin stack/PROJ-400-service
gh pr create --title "feat: servizio notifiche [3/5]" \
  --base stack/PROJ-400-repository

# 4. Quando la PR #1 viene mergiata in main,
#    aggiornare la base della PR #2 a main:
gh pr edit 2 --base main

# 5. Dopo merge di PR #2, aggiornare la PR #3:
gh pr edit 3 --base main
```

### Workflow con Graphite CLI

Graphite semplifica enormemente la gestione delle stacked PR con il suo CLI `gt`:

```bash
# Installare Graphite CLI
npm install -g @withgraphite/graphite-cli

# Inizializzare nel repository
gt repo init

# Creare lo stack
gt branch create stack/data-model
# ... implementare ...
gt commit create -m "feat(db): aggiungere modello dati"

gt branch create stack/repository
# ... implementare ...
gt commit create -m "feat(db): aggiungere repository"

gt branch create stack/service
# ... implementare ...
gt commit create -m "feat: aggiungere servizio"

# Sottomettere l'intero stack come PR con un singolo comando
gt stack submit

# Dopo che la prima PR dello stack viene mergiata,
# Graphite aggiorna automaticamente le basi delle PR successive
gt stack sync
```

### Best Practice per le Stacked PR

1. **Ogni PR deve essere indipendentemente deployabile**: Anche se il codice non è completo, non deve rompere nulla.
2. **Numerare le PR nello stack**: Usare `[1/N]`, `[2/N]` nel titolo per indicare la posizione.
3. **Linkare le PR**: Nella descrizione di ogni PR, linkare la precedente e la successiva dello stack.
4. **Test ad ogni livello**: Ogni PR deve avere i propri test che passano indipendentemente.
5. **Limite di 5-7 PR per stack**: Più di questo diventa difficile da gestire anche con tooling.

---

## Git Worktrees per lo Sviluppo Parallelo

Git worktrees permettono di avere multiple directory di lavoro collegate allo stesso repository, ognuna con un branch diverso checked out. Questo è particolarmente utile quando si deve lavorare su più cose contemporaneamente: una feature, un bugfix urgente, e la review del codice di un collega, tutto senza fare `stash` o `checkout` continui.

### Come Funzionano i Worktrees

Un worktree è una directory separata collegata allo stesso repository Git (condivide la directory `.git`, l'object store, e la configurazione). Ogni worktree ha il proprio branch checked out, il proprio working tree, e il proprio staging area.

```bash
# Struttura risultante dopo aver creato worktrees
~/progetti/
├── mio-progetto/                    # Worktree principale (main)
│   ├── .git/                        # Repository Git condiviso
│   ├── src/
│   └── package.json
├── mio-progetto-feature-auth/       # Worktree per feature
│   ├── .git → ../mio-progetto/.git  # Collegamento al repo principale
│   ├── src/
│   └── package.json
└── mio-progetto-hotfix/             # Worktree per hotfix
    ├── .git → ../mio-progetto/.git
    ├── src/
    └── package.json
```

### Comandi Essenziali

```bash
# Creare un nuovo worktree per un branch esistente
git worktree add ../mio-progetto-feature feature/PROJ-500-auth

# Creare un nuovo worktree con un nuovo branch
git worktree add -b hotfix/PROJ-600-fix ../mio-progetto-hotfix main

# Elencare tutti i worktrees
git worktree list
# /home/dev/mio-progetto                  abc1234 [main]
# /home/dev/mio-progetto-feature          def5678 [feature/PROJ-500-auth]
# /home/dev/mio-progetto-hotfix           ghi9012 [hotfix/PROJ-600-fix]

# Rimuovere un worktree dopo aver finito
git worktree remove ../mio-progetto-hotfix

# Pulire worktrees orfani (directory cancellata manualmente)
git worktree prune
```

### Scenario Pratico: Interruzione per Hotfix

```bash
# Stai lavorando su una feature...
cd ~/progetti/mio-progetto
# branch: feature/PROJ-500-auth

# Arriva una segnalazione urgente!
# Invece di stash + checkout, crei un worktree:
git worktree add -b hotfix/PROJ-601-crash ../hotfix-crash main

# Apri il worktree in un nuovo terminale/editor
cd ../hotfix-crash
# ... correggi il bug ...
git commit -m "fix: correggere crash al login con SSO"
git push -u origin hotfix/PROJ-601-crash
gh pr create --title "hotfix: crash login SSO" --label hotfix

# Torni al tuo lavoro sulla feature, esattamente dove l'avevi lasciato
cd ~/progetti/mio-progetto
# Il tuo working tree è intatto, nessun stash necessario

# Dopo che l'hotfix è stato mergiato e deployato:
git worktree remove ../hotfix-crash
```

### Convenzioni di Team per i Worktrees

| Convenzione | Raccomandazione |
|-------------|-----------------|
| Directory di base | Tutti i worktrees nella stessa directory padre del progetto principale |
| Naming | `{progetto}-{tipo}-{breve-desc}` es. `api-hotfix-login` |
| Limite | Massimo 3-5 worktrees attivi per sviluppatore |
| Cleanup | Rimuovere i worktrees appena il branch è stato mergiato |
| Node modules | Ogni worktree ha il proprio `node_modules`, quindi eseguire `npm install` in ciascuno |

### Limitazioni da Conoscere

- Non si può avere lo stesso branch checked out in due worktrees contemporaneamente.
- Ogni worktree con le proprie dipendenze installate consuma spazio disco aggiuntivo.
- IDE e editor devono essere configurati per lavorare con directory separate (la maggior parte lo supporta nativamente).
- I git hooks sono condivisi tra tutti i worktrees (sono nella directory `.git` condivisa).

---

## Feature Flag e Trunk-Based Development Avanzato

I feature flag (o feature toggle) sono il meccanismo che rende praticabile il trunk-based development per team di qualsiasi dimensione. Permettono di separare il concetto di "deploy del codice" dal concetto di "attivazione della funzionalità": il codice viene mergiato in main e deployato in produzione, ma la nuova funzionalità rimane disattivata finché non si decide di abilitarla.

### Perché i Feature Flag sono Essenziali

Senza feature flag, il trunk-based development presenta un dilemma: come mergiare codice incompleto in main senza rompere la produzione? I feature flag risolvono questo problema avvolgendo il nuovo codice in un percorso condizionale che viene attivato solo quando il flag è abilitato.

```typescript
// Esempio di feature flag nel codice
import { featureFlags } from '@/lib/feature-flags';

export function UserProfile({ userId }: { userId: string }) {
  const user = useUser(userId);

  return (
    <div>
      <h1>{user.name}</h1>

      {/* Funzionalità esistente, sempre visibile */}
      <UserDetails user={user} />

      {/* Nuova funzionalità, controllata da feature flag */}
      {featureFlags.isEnabled('user-activity-timeline') && (
        <ActivityTimeline userId={userId} />
      )}

      {/* Feature flag con varianti per A/B testing */}
      {featureFlags.getVariant('checkout-flow') === 'new' ? (
        <NewCheckoutFlow />
      ) : (
        <CurrentCheckoutFlow />
      )}
    </div>
  );
}
```

### Ciclo di Vita di un Feature Flag

```
1. CREAZIONE        → Il flag viene definito nel sistema (default: OFF)
2. SVILUPPO         → Il codice viene scritto dentro il blocco del flag
3. TESTING INTERNO  → Il flag viene abilitato per il team di sviluppo
4. CANARY RELEASE   → Il flag viene abilitato per l'1% degli utenti
5. ROLLOUT GRADUALE → 5% → 25% → 50% → 100%
6. PULIZIA          → Il flag viene rimosso e il codice diventa permanente
```

### Implementazione Minimale di un Sistema di Feature Flag

```typescript
// src/lib/feature-flags.ts
// Implementazione semplice per team che non vogliono dipendenze esterne

interface FeatureFlagConfig {
  [key: string]: {
    enabled: boolean;
    enabledForUsers?: string[];
    enabledForPercentage?: number;
    description: string;
    createdAt: string;
    owner: string;
  };
}

const FLAGS: FeatureFlagConfig = {
  'user-activity-timeline': {
    enabled: false,
    enabledForUsers: ['dev-team@azienda.com'],
    description: 'Timeline delle attività utente nella pagina profilo',
    createdAt: '2026-05-01',
    owner: 'team-frontend',
  },
  'new-checkout-flow': {
    enabled: false,
    enabledForPercentage: 10,
    description: 'Nuovo flusso di checkout a singola pagina',
    createdAt: '2026-04-15',
    owner: 'team-payments',
  },
};

export const featureFlags = {
  isEnabled(flagName: string, userId?: string): boolean {
    const flag = FLAGS[flagName];
    if (!flag) return false;
    if (flag.enabled) return true;
    if (userId && flag.enabledForUsers?.includes(userId)) return true;
    if (flag.enabledForPercentage && userId) {
      const hash = simpleHash(userId + flagName);
      return (hash % 100) < flag.enabledForPercentage;
    }
    return false;
  },
};
```

### Disciplina di Pulizia dei Feature Flag

Un pericolo reale dei feature flag è l'accumulo: flag vecchi che nessuno rimuove, codice morto che rimane nel codebase, e complessità crescente nel capire quali percorsi di codice sono effettivamente attivi. La pulizia deve essere sistematica:

```bash
# Script per trovare feature flag vecchi (oltre 90 giorni)
#!/bin/bash
echo "Feature flag da pulire (creati più di 90 giorni fa):"
THRESHOLD=$(date -d "-90 days" +%Y-%m-%d)

grep -rn "featureFlags.isEnabled\|featureFlags.getVariant" src/ | while read -r line; do
  FLAG_NAME=$(echo "$line" | grep -oP "'[a-z-]+'")
  echo "  - $FLAG_NAME trovato in: $(echo "$line" | cut -d: -f1):$(echo "$line" | cut -d: -f2)"
done

echo ""
echo "Azione richiesta: rimuovere il flag e rendere il codice permanente"
echo "oppure eliminare il codice se la feature è stata abbandonata."
```

### GitHub Action per Audit dei Feature Flag

```yaml
# .github/workflows/feature-flag-audit.yml
name: Feature Flag Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Ogni lunedì alle 9:00

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Contare feature flag nel codebase
        run: |
          echo "## Report Feature Flag" > flag-report.md
          echo "" >> flag-report.md

          COUNT=$(grep -rn "featureFlags\.\(isEnabled\|getVariant\)" src/ | wc -l)
          echo "Totale utilizzi di feature flag nel codebase: $COUNT" >> flag-report.md
          echo "" >> flag-report.md

          echo "### Dettaglio per file:" >> flag-report.md
          grep -rn "featureFlags\.\(isEnabled\|getVariant\)" src/ \
            | cut -d: -f1 | sort | uniq -c | sort -rn >> flag-report.md

          cat flag-report.md

      - name: Creare issue se ci sono troppi flag
        if: ${{ env.COUNT > 20 }}
        run: |
          gh issue create \
            --title "chore: pulizia feature flag necessaria ($COUNT flag attivi)" \
            --body "$(cat flag-report.md)" \
            --label "tech-debt,chore"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Sicurezza Git per Team

La sicurezza nel workflow Git va oltre il semplice "non committare le password". In un contesto di team aziendale, la sicurezza del repository Git è parte della supply chain del software: ogni commit che raggiunge la produzione deve essere verificabile nella sua provenienza, integrità, e autorizzazione.

### Firma dei Commit con SSH Key

A partire da Git 2.34, è possibile firmare i commit con le chiavi SSH, che sono più semplici da gestire rispetto alle chiavi GPG tradizionali:

```bash
# Configurare la firma SSH (Git 2.34+)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true

# Configurare il file di chiavi ammesse per la verifica
# Questo file contiene le chiavi SSH pubbliche dei membri del team
mkdir -p ~/.config/git
cat > ~/.config/git/allowed_signers << 'EOF'
mario.rossi@azienda.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
lucia.bianchi@azienda.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
EOF

git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers

# Verificare un commit firmato
git log --show-signature -1
git verify-commit HEAD

# Verificare un tag firmato
git verify-tag v1.2.0
```

### Firma dei Commit con GPG

Per team che preferiscono GPG o devono usarlo per compliance:

```bash
# Generare una chiave GPG
gpg --full-generate-key
# Scegliere: RSA (4096 bit), email aziendale, scadenza 2 anni

# Trovare l'ID della chiave
gpg --list-secret-keys --keyid-format=long
# sec   rsa4096/ABC123DEF456 2026-01-01 [SC] [expires: 2028-01-01]

# Configurare Git
git config --global user.signingkey ABC123DEF456
git config --global commit.gpgsign true
git config --global tag.gpgsign true

# Aggiungere la chiave pubblica a GitHub
gpg --armor --export ABC123DEF456
# Copiare l'output in GitHub > Settings > SSH and GPG keys > New GPG key
```

### Secret Scanning e Prevenzione

```bash
# Installare git-secrets (AWS) per prevenire commit di credenziali
# https://github.com/awslabs/git-secrets
git secrets --install
git secrets --register-aws

# Aggiungere pattern personalizzati per l'azienda
git secrets --add 'PRIVATE_KEY'
git secrets --add 'api[_-]?key[_-]?=.+'
git secrets --add 'password[_-]?=.+'
git secrets --add --allowed 'password=<placeholder>'

# Hook pre-commit che blocca automaticamente i commit con segreti
# git-secrets installa automaticamente l'hook

# Alternativa: usare truffleHog per scansionare la storia del repository
# https://github.com/trufflesecurity/trufflehog
trufflehog git file://./mio-progetto --only-verified
```

### GitHub Action per Scansione di Sicurezza nelle PR

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Scansionare per segreti nei file modificati
        run: |
          FILES=$(git diff --name-only ${{ github.event.pull_request.base.sha }}..HEAD)
          FOUND_SECRETS=false

          for file in $FILES; do
            if [ -f "$file" ]; then
              # Pattern per segreti comuni
              if grep -qE "(api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*['\"][^'\"]+['\"]" "$file"; then
                echo "::error file=$file::Possibile segreto trovato in $file"
                FOUND_SECRETS=true
              fi

              # Pattern per chiavi AWS
              if grep -qE "AKIA[0-9A-Z]{16}" "$file"; then
                echo "::error file=$file::Possibile AWS Access Key trovata in $file"
                FOUND_SECRETS=true
              fi
            fi
          done

          if [ "$FOUND_SECRETS" = true ]; then
            echo "::error::Segreti potenziali trovati. Rimuoverli prima del merge."
            exit 1
          fi

  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Audit delle dipendenze
        run: |
          npm audit --audit-level=high
          if [ $? -ne 0 ]; then
            echo "::warning::Vulnerabilità trovate nelle dipendenze"
          fi

  verify-signatures:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verificare firma dei commit
        run: |
          UNSIGNED=$(git log --format='%H %G?' \
            ${{ github.event.pull_request.base.sha }}..HEAD \
            | grep -v ' G$' | grep -v ' U$')

          if [ -n "$UNSIGNED" ]; then
            echo "::warning::Commit non firmati trovati nella PR:"
            echo "$UNSIGNED"
          fi
```

### Checklist di Sicurezza Git per Team

| Pratica | Priorità | Implementazione |
|---------|----------|-----------------|
| Branch protection su main | Critica | GitHub Settings > Branch Protection |
| Firma dei commit obbligatoria | Alta | `required_signatures: true` nelle branch protection |
| Secret scanning abilitato | Critica | GitHub Settings > Code security |
| Dependabot alerts attivi | Alta | GitHub Settings > Code security |
| 2FA obbligatoria per l'organizzazione | Critica | GitHub Org Settings > Authentication |
| Revisione delle chiavi di deploy | Alta | Audit trimestrale delle deploy keys |
| Audit log monitorato | Media | GitHub Org Settings > Audit log |
| SAML SSO (Enterprise) | Alta | GitHub Enterprise > SAML SSO |
| IP allowlist per push | Media | GitHub Enterprise > IP allow list |
| Pre-commit hook per segreti | Alta | git-secrets o equivalente |

---

## Collezione Completa di Git Alias per il Team

Gli alias Git trasformano comandi lunghi e difficili da ricordare in scorciatoie immediate. Per un team, un set condiviso di alias garantisce che tutti parlino la stessa "lingua" quando usano Git dalla riga di comando. Qui di seguito una collezione organizzata per categoria, pronta per essere condivisa con il team.

### Setup Completo: File `.gitconfig` Condiviso

```ini
# Salvare come team-gitconfig.ini e distribuire al team
# Ogni membro esegue: git config --global --include-if 'gitdir:~/work/**' team-gitconfig.ini

[alias]
    # =========================================
    # NAVIGAZIONE E STATO
    # =========================================

    # Status breve con info branch
    st = status --short --branch

    # Log grafico compatto — la vista più utile per capire la storia
    lg = log --oneline --graph --all --decorate
    lg5 = log --oneline --graph --all --decorate -5
    lg10 = log --oneline --graph --all --decorate -10

    # Log con date relative e autore
    ll = log --pretty=format:'%C(yellow)%h%Creset %C(green)(%cr)%Creset %s %C(bold blue)<%an>%Creset%C(red)%d%Creset' --abbrev-commit

    # Log dei propri commit (sostituire con il proprio nome)
    my = log --author='Nome' --oneline -20

    # Ultimo commit con statistiche
    last = log -1 HEAD --stat

    # Mostrare i branch ordinati per ultimo commit (più recente prima)
    br = branch --sort=-committerdate --format='%(color:yellow)%(refname:short)%(color:reset) %(color:green)(%(committerdate:relative))%(color:reset) %(color:blue)%(authorname)%(color:reset)'

    # =========================================
    # OPERAZIONI QUOTIDIANE
    # =========================================

    # Checkout abbreviato
    co = checkout
    sw = switch
    swc = switch -c

    # Aggiungere tutto e committare
    ac = "!git add -A && git commit -m"

    # Amend senza cambiare il messaggio
    amend = commit --amend --no-edit

    # Unstage un file
    unstage = reset HEAD --

    # Scartare modifiche locali per un file specifico
    discard = checkout --

    # Stash con messaggio
    ss = stash push -m
    sp = stash pop
    sl = stash list

    # =========================================
    # BRANCH E MERGE
    # =========================================

    # Creare branch feature con naming corretto
    feat = "!f() { git switch -c feature/$1; }; f"
    bug = "!f() { git switch -c bugfix/$1; }; f"
    hot = "!f() { git switch -c hotfix/$1; }; f"

    # Aggiornare branch corrente con main (rebase)
    up = "!git fetch origin && git rebase origin/main"

    # Merge con no-fast-forward (preserva il merge commit)
    mnf = merge --no-ff

    # Eliminare branch locali già mergiati in main
    cleanup = "!git branch --merged main | grep -v 'main\\|\\*' | xargs -r git branch -d"

    # Eliminare riferimenti a branch remoti cancellati
    prune-remote = fetch --prune

    # =========================================
    # CODE REVIEW E PR
    # =========================================

    # Vedere il diff della PR (confronto con main)
    pr-diff = "!git diff main...HEAD"

    # Elencare i file modificati rispetto a main
    pr-files = "!git diff --name-only main...HEAD"

    # Statistiche della PR (righe aggiunte/rimosse per file)
    pr-stats = "!git diff --stat main...HEAD"

    # Vedere i commit della PR
    pr-log = "!git log --oneline main..HEAD"

    # =========================================
    # RICERCA E DEBUG
    # =========================================

    # Cercare una stringa in tutti i file tracciati
    find = "!git grep -n"

    # Cercare nei messaggi di commit
    find-commit = "!f() { git log --oneline --grep=\"$1\"; }; f"

    # Trovare chi ha modificato per ultimo una riga
    who = blame -w -M -C -C

    # Trovare in quale commit è stata introdotta una stringa
    when = "!f() { git log -S \"$1\" --oneline; }; f"

    # =========================================
    # SICUREZZA E VERIFICA
    # =========================================

    # Verificare firma dell'ultimo commit
    verify = "!git log --show-signature -1"

    # Mostrare commit non firmati
    unsigned = "!git log --format='%H %G? %s' | grep -v ' G '"

    # =========================================
    # COLLABORAZIONE
    # =========================================

    # Vedere cosa hanno fatto i colleghi oggi
    today = "!git log --all --since='8am' --oneline --format='%C(yellow)%h%Creset %C(green)%cr%Creset %s %C(bold blue)<%an>%Creset'"

    # Vedere chi sta lavorando su cosa (branch attivi)
    wip = "!git for-each-ref --sort=-committerdate --format='%(color:yellow)%(refname:short)%(color:reset) (%(color:green)%(committerdate:relative)%(color:reset)) %(color:blue)%(authorname)%(color:reset)' refs/remotes/origin/"

    # Contare commit per autore
    stats = shortlog -sn --all
```

### Come Distribuire gli Alias al Team

```bash
# Opzione 1: Script di setup per nuovi membri del team
#!/bin/bash
# setup-git-aliases.sh

echo "Configurazione alias Git del team..."

git config --global alias.st "status --short --branch"
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.ll "log --pretty=format:'%C(yellow)%h%Creset %C(green)(%cr)%Creset %s %C(bold blue)<%an>%Creset%C(red)%d%Creset' --abbrev-commit"
git config --global alias.br "branch --sort=-committerdate"
git config --global alias.co "checkout"
git config --global alias.sw "switch"
git config --global alias.amend "commit --amend --no-edit"
git config --global alias.unstage "reset HEAD --"
git config --global alias.up '!git fetch origin && git rebase origin/main'
git config --global alias.cleanup "!git branch --merged main | grep -v 'main\\|\\*' | xargs -r git branch -d"
git config --global alias.pr-diff '!git diff main...HEAD'
git config --global alias.pr-files '!git diff --name-only main...HEAD'
git config --global alias.pr-stats '!git diff --stat main...HEAD'
git config --global alias.today "!git log --all --since='8am' --oneline --format='%C(yellow)%h%Creset %C(green)%cr%Creset %s %C(bold blue)<%an>%Creset'"
git config --global alias.last "log -1 HEAD --stat"

echo "Alias Git configurati con successo!"
echo "Esegui 'git lg' per verificare."

# Opzione 2: Includere un file condiviso
# Nel repository del team, creare .gitconfig-team
# Ogni membro aggiunge al proprio ~/.gitconfig:
# [include]
#     path = ~/work/mio-progetto/.gitconfig-team
```

---

## Onboarding dei Nuovi Sviluppatori

L'onboarding di un nuovo membro del team è il momento in cui la qualità del workflow Git viene messa alla prova. Se il processo è documentato, automatizzato, e chiaro, il nuovo sviluppatore sarà produttivo in giorni, non settimane. Se il processo è basato su "conoscenza tribale" non documentata, ogni onboarding sarà un'esperienza frustrante per tutti.

### Piano di Onboarding in 30/60/90 Giorni

#### Primi 30 Giorni: Imparare

**Settimana 1: Setup e orientamento**

```bash
# Checklist giorno 1 — Setup tecnico
# ─────────────────────────────────────
[ ] Account GitHub aggiunto all'organizzazione
[ ] Accesso ai repository necessari verificato
[ ] SSH key configurata e aggiunta a GitHub
[ ] GPG/SSH key per firma commit configurata
[ ] Git config globale impostata (vedi sezione setup)
[ ] Alias Git del team installati (script setup-git-aliases.sh)
[ ] Editor/IDE configurato con editorconfig
[ ] Repository clonato e progetto avviato in locale
[ ] CI/CD pipeline spiegata
[ ] Canali di comunicazione del team (Slack, Teams) aggiunti

# Checklist giorno 2-5 — Orientamento codebase
[ ] CONTRIBUTING.md letto e compreso
[ ] Architettura del sistema spiegata (docs/ARCHITECTURE.md)
[ ] Convenzioni di naming branch spiegate
[ ] Conventional Commits spiegati
[ ] Processo PR e code review spiegato
[ ] Branch protection rules spiegate
[ ] CODEOWNERS spiegato
[ ] Primo task assegnato (piccola modifica, basso rischio)
```

**Settimana 2-4: Prime contribuzioni**

```bash
# Il nuovo sviluppatore deve completare:
[ ] Prima PR aperta, reviewata, e mergiata
[ ] Prima code review effettuata (come reviewer)
[ ] Partecipato a un planning/standup con il team
[ ] Risolto almeno un conflitto di merge
[ ] Usato correttamente le Conventional Commits
[ ] Compreso il flusso di release (tag, changelog)
```

#### Giorni 31-60: Contribuire

```bash
# Obiettivi del secondo mese:
[ ] Ownership di 2-3 feature di media complessità
[ ] Capacità di fare code review costruttive e approfondite
[ ] Comprensione delle aree principali del codebase
[ ] Contribuito alla documentazione (almeno una miglioria)
[ ] Gestito autonomamente un bugfix dalla segnalazione al deploy
[ ] Partecipato a un processo di release
```

#### Giorni 61-90: Autonomia

```bash
# Obiettivi del terzo mese:
[ ] Ownership di feature complesse end-to-end
[ ] Capacità di gestire hotfix in produzione
[ ] Capacità di onboardare il prossimo nuovo membro (buddy)
[ ] Proposto almeno un miglioramento al workflow o alla documentazione
[ ] Diventato reviewer affidabile per la propria area di competenza
```

### Il Primo Commit: Walkthrough Guidato

Un walkthrough guidato del primo commit è molto più efficace di qualsiasi documentazione scritta. Il mentore (buddy) guida il nuovo sviluppatore attraverso l'intero processo:

```bash
# Il buddy e il nuovo sviluppatore lavorano insieme al primo commit

# 1. Scegliere un task appropriato per il primo commit
#    Ideale: fix di un typo, aggiornamento di un messaggio UI,
#    aggiunta di un test mancante — qualcosa di basso rischio
#    ma che attraversa l'intero processo

# 2. Creare il branch
git checkout main
git pull origin main
git checkout -b docs/PROJ-001-fix-readme-typo

# 3. Fare la modifica
# ... il nuovo sviluppatore modifica il file ...

# 4. Verificare il diff
git diff
# Il buddy spiega ogni riga del diff

# 5. Stage e commit
git add README.md
git commit -m "docs: correggere typo nella sezione installazione"
# Il buddy spiega il formato Conventional Commits

# 6. Push e PR
git push -u origin docs/PROJ-001-fix-readme-typo
gh pr create \
  --title "docs: correggere typo README" \
  --body "Il mio primo commit!

## Modifica
Corretto 'instllazione' → 'installazione' nel README.

## Checklist
- [x] Ho letto CONTRIBUTING.md
- [x] La modifica segue le convenzioni del progetto"

# 7. Il buddy fa la review, spiega il processo,
#    lascia un commento di benvenuto, e approva
# 8. Merge con squash
# 9. Celebrare il primo contributo mergiato!
```

### Sistema di Buddy per l'Onboarding

Il sistema di buddy assegna un membro esperto del team come mentore per ogni nuovo sviluppatore:

| Responsabilità del Buddy | Durata |
|--------------------------|--------|
| Pair programming sul primo task | Settimana 1 |
| Review di tutte le PR del nuovo membro | Settimane 1-4 |
| Sessione settimanale di Q&A (30 min) | Settimane 1-8 |
| Disponibilità per domande su Slack/chat | Mesi 1-3 |
| Feedback all'engineering manager sulla progressione | Fine mese 1, 2, 3 |

### Anti-Pattern dell'Onboarding

1. **"Leggi il codice e chiedi se hai domande"**: Senza struttura, il nuovo membro si sente perso e non sa cosa chiedere.
2. **Task troppo complesso come primo incarico**: Il primo task deve essere un successo garantito per costruire fiducia.
3. **Nessun buddy assegnato**: Il nuovo membro non sa a chi rivolgersi e disturba tutti.
4. **Documentazione inesistente**: Ogni onboarding costa settimane di tempo senior perché tutto è "conoscenza tribale".
5. **Accessi non preparati in anticipo**: Il primo giorno viene speso a risolvere problemi di permessi.
6. **Nessun feedback strutturato**: Senza checkpoint a 30/60/90 giorni, i problemi vengono identificati troppo tardi.

### GitHub Action per Welcomebot

```yaml
# .github/workflows/welcome-new-contributor.yml
name: Welcome New Contributor

on:
  pull_request:
    types: [opened]

jobs:
  welcome:
    runs-on: ubuntu-latest
    steps:
      - name: Controllare se è il primo contributo
        id: check
        run: |
          AUTHOR="${{ github.event.pull_request.user.login }}"
          PR_COUNT=$(gh pr list --author "$AUTHOR" --state all --json number -q 'length')

          if [ "$PR_COUNT" -le 1 ]; then
            echo "first_time=true" >> $GITHUB_OUTPUT
          else
            echo "first_time=false" >> $GITHUB_OUTPUT
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Messaggio di benvenuto
        if: steps.check.outputs.first_time == 'true'
        run: |
          gh pr comment ${{ github.event.pull_request.number }} --body "
          Benvenuto/a nel progetto, @${{ github.event.pull_request.user.login }}!

          Questa sembra essere la tua prima Pull Request. Ecco qualche informazione utile:

          - Assicurati di aver letto le nostre [linee guida per i contributi](CONTRIBUTING.md)
          - I commit devono seguire le [Conventional Commits](https://www.conventionalcommits.org/)
          - La PR sarà reviewata entro 48 ore lavorative
          - Se hai domande, non esitare a chiedere nei commenti

          Grazie per il tuo contributo!"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Riepilogo

Un workflow di team efficace con Git e GitHub si basa su tre pilastri: **automazione** (template, hooks, CI/CD per ridurre l'errore umano), **convenzioni** (naming dei branch, commit messages, processo di review per garantire coerenza), e **protezioni** (branch protection, CODEOWNERS, check obbligatori per prevenire errori). Questi elementi lavorano insieme per creare un sistema dove il codice sulla branch principale è sempre in uno stato rilasciabile, ogni modifica è tracciabile e motivata, e il team può lavorare in parallelo con fiducia reciproca.

La chiave del successo è l'adozione graduale: non implementare tutto in una volta. Iniziare con branch protection e un template PR di base, poi aggiungere Conventional Commits, CODEOWNERS, e automazione man mano che il team acquisisce familiarità con il processo. Un workflow troppo rigido per un team che non è pronto causerà solo frustrazione e workaround.

---

## Esercizi Pratici

### Esercizio 1: Setup Repository di Team da Zero

Configura un repository completo per un team di 5 sviluppatori:

```bash
# 1. Creare il repository su GitHub con README, LICENSE (MIT), .gitignore (Node)
# 2. Configurare branch protection su main:
#    - Require PR with 2 approvals
#    - Require status checks: ci/lint, ci/test
#    - Dismiss stale reviews on new push
#    - Require conversation resolution
#    - Restrict push to team-lead only
# 3. Creare CODEOWNERS:
#    * @org/team-leads
#    /src/api/ @org/backend-team
#    /src/ui/ @org/frontend-team
#    /infra/ @org/devops-team
# 4. Creare template PR e issue (.github/PULL_REQUEST_TEMPLATE.md, .github/ISSUE_TEMPLATE/)
# 5. Configurare labels standard: bug, feature, docs, breaking, dependencies

# Verifica:
# - Push diretto su main → bloccato
# - PR senza review → non mergiabile
# - PR che modifica /src/api/ → richiede review da backend-team
```

**Criteri di successo:** nessun push diretto possibile, CODEOWNERS funzionanti, template visibili nella UI.

### Esercizio 2: Conventional Commits con Validazione

Implementa Conventional Commits con validazione automatica:

```bash
# 1. Installare commitlint e husky nel progetto:
#    npm install -D @commitlint/cli @commitlint/config-conventional husky
# 2. Configurare commitlint.config.js con regole:
#    - type-enum: feat, fix, docs, style, refactor, test, chore, perf, ci, revert
#    - subject-max-length: 72
#    - body-max-line-length: 100
# 3. Configurare husky con commit-msg hook:
#    npx husky add .husky/commit-msg 'npx commitlint --edit $1'
# 4. Aggiungere GitHub Action per validare i commit nella PR:
#    - Usare commitlint-github-action
# 5. Testare:
#    - git commit -m "added stuff" → bloccato da husky
#    - git commit -m "feat: add user authentication" → accettato
#    - PR con commit non convenzionale → check fallisce
```

### Esercizio 3: Flusso PR Completo con Review

Simula un flusso completo di Pull Request con review:

```bash
# 1. Developer A crea branch: git switch -c feat/user-auth
# 2. Developer A implementa la feature con 3 commit atomici:
#    - feat: add auth middleware
#    - feat: add login endpoint
#    - test: add auth integration tests
# 3. Developer A apre PR usando il template:
#    gh pr create --title "feat: add user authentication" --body-file .github/PR_TEMPLATE.md
# 4. CI esegue: lint, test, type-check, security scan
# 5. Developer B fa review:
#    - Trova un bug → richiede changes
#    - Developer A corregge → push ammend + force-with-lease
#    - Developer B approva
# 6. Developer C approva (seconda review richiesta)
# 7. Merge con squash: un solo commit pulito su main
# 8. Branch automaticamente eliminato dopo il merge

# Verifica:
# - La PR mostra le check CI passate
# - Il merge è bloccato finché non ci sono 2 approval
# - Dopo il merge, il branch feature è eliminato
```

### Esercizio 4: Release Branch e Hotfix

Pratica il processo di release e hotfix in un team:

```bash
# 1. Creare release branch da main:
#    git switch -c release/2.0.0
# 2. Applicare fix sulla release branch (solo bugfix, no nuove feature):
#    git commit -m "fix: correct date format in export"
# 3. Completare la release:
#    - Merge release/2.0.0 → main
#    - Tag: v2.0.0
#    - Merge release/2.0.0 → develop (se si usa GitFlow)
# 4. Scoprire un bug critico in produzione:
#    - Creare hotfix/2.0.1 da main
#    - Applicare fix minimale
#    - Merge hotfix → main, tag v2.0.1
#    - Cherry-pick o merge hotfix → develop
# 5. Verificare con:
#    git log --oneline --graph --all
#    git tag -l 'v2.*'
```

### Esercizio 5: Monorepo con CODEOWNERS e Affected CI

Configura un monorepo con ownership e CI condizionale:

```bash
# 1. Struttura:
#    apps/web/     → @org/frontend-team
#    apps/api/     → @org/backend-team
#    libs/shared/  → @org/platform-team (richiede 2 reviewer)
#    infra/        → @org/devops-team
# 2. CODEOWNERS con regole granulari
# 3. CI che esegue test solo per le aree modificate:
#    - Usare dorny/paths-filter@v3 per rilevare i file cambiati
#    - Job condizionali: if needs.changes.outputs.web == 'true'
# 4. Creare PR che modifica solo apps/web/:
#    - Solo frontend-team come reviewer
#    - Solo test frontend eseguiti
# 5. Creare PR che modifica libs/shared/:
#    - Tutti i team come reviewer (shared impatta tutti)
#    - Tutti i test eseguiti

# Verifica:
# - PR web-only: solo CI frontend, solo reviewer frontend
# - PR shared: CI completa, reviewer multipli
```

---

## Letture Consigliate

- **Libro**: "Git for Teams" di Emma Jane Hogbin Westby, O'Reilly Media, 2015 — workflow collaborativi, convenzioni e processi di team
- **Libro**: "Software Engineering at Google" di Titus Winters, Tom Manshreck, Hyrum Wright, O'Reilly Media, 2020 — capitoli su code review e trunk-based development
- **Conventional Commits Specification**: https://www.conventionalcommits.org/en/v1.0.0/ (consultato: 2026-05-24)
- **GitHub Docs — Branch Protection**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-a-branch-protection-rule (consultato: 2026-05-24)
- **GitHub Docs — CODEOWNERS**: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners (consultato: 2026-05-24)
- **Articolo**: "Ship / Show / Ask" di Rouan Wilsenach — https://martinfowler.com/articles/ship-show-ask.html (consultato: 2026-05-24)
- **Articolo**: "Why code reviews matter" — GitHub Blog, https://github.blog/developer-skills/github/why-code-reviews-matter-and-actually-save-time/ (consultato: 2026-05-24)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 02 | [02-strategie-branching.md](02-strategie-branching.md) | Strategie di branching — GitFlow, GitHub Flow, trunk-based |
| 01 | [01-fondamenti-git.md](01-fondamenti-git.md) | Fondamenti Git — merge, rebase, cherry-pick usati nel team workflow |
| 03 | [03-piattaforma-github.md](03-piattaforma-github.md) | Piattaforma GitHub — PR, issues, repository settings |
| 06 | [06-git-branching-merge-avanzato.md](06-git-branching-merge-avanzato.md) | Merge avanzato — risoluzione conflitti, merge strategies |
| 13 | [13-github-issues-projects-collaboration.md](13-github-issues-projects-collaboration.md) | Issues e Projects — project management integrato |
| 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) | Git hooks — automazione locale (commitlint, husky) |
| 11 | [11-gitignore-gitattributes-config.md](11-gitignore-gitattributes-config.md) | Configurazione Git — .gitignore, .gitattributes per il team |
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Workflow CI — check automatici nelle PR |
| 12 | [12-github-repository-management.md](12-github-repository-management.md) | Repository management — branch rules, rulesets |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **Branch protection** | Regole che impediscono push diretti, forzano review e status check prima del merge su branch protetti |
| **CODEOWNERS** | File che associa percorsi del repository a team o utenti responsabili della review automatica |
| **Conventional Commits** | Specifica per messaggi di commit strutturati (type: description) che abilita changelog e versioning automatici |
| **Code review** | Processo di ispezione del codice da parte di colleghi prima del merge, per garantire qualità e sicurezza |
| **Dismiss stale reviews** | Impostazione che invalida le approvazioni esistenti quando vengono pushati nuovi commit sulla PR |
| **Force-with-lease** | Variante sicura di force-push che fallisce se il branch remoto è stato modificato da altri |
| **Hotfix** | Branch di emergenza creato da main/production per correggere un bug critico in produzione |
| **Merge strategy** | Metodo di integrazione del codice: merge commit (preserva storia), squash (commit singolo), rebase (linearizza) |
| **PR template** | Template markdown che standardizza la struttura delle Pull Request (descrizione, testing, checklist) |
| **Release branch** | Branch dedicato alla preparazione di un rilascio, dove si applicano solo bugfix e nessuna nuova feature |
| **Ruleset** | Evoluzione delle branch protection rules su GitHub: più flessibili, supportano pattern matching e bypass |
| **Squash merge** | Strategia di merge che comprime tutti i commit del branch in un singolo commit sul target |
| **Stale review** | Review di approvazione che diventa invalida dopo nuovi push sulla PR, richiedendo nuova approvazione |
| **Trunk-based development** | Strategia di branching dove tutti committano su un singolo branch principale con branch di vita brevissima |
