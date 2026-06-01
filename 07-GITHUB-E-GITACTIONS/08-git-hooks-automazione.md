---
corso: "GitHub e Git Actions"
fase: "2 — Configurazione Git"
modulo: "08"
titolo: "Git Hooks e Automazione"
versione: "Git 2.47+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti Git"
  - "07 — Git Internals: Oggetti e Refs"
obiettivi:
  - "Comprendere il ciclo di vita dei Git hooks client-side e server-side"
  - "Configurare pre-commit, commit-msg e pre-push hook per gate di qualità"
  - "Utilizzare il framework pre-commit (Python) per hook portabili e condivisibili"
  - "Integrare Husky e lint-staged in progetti JavaScript/TypeScript"
  - "Implementare hook server-side per enforcement centralizzato delle policy"
tag: [git, hooks, pre-commit, husky, lint-staged, commitlint, automazione, ci]
---

# Git Hooks e Automazione — Guida Approfondita

> **Modulo 08** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti Git](01-fondamenti-git.md), [Git Internals](07-git-interni-oggetti-refs.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere il ciclo di vita dei Git hooks client-side e server-side
> 2. Configurare pre-commit, commit-msg e pre-push hook per gate di qualità
> 3. Utilizzare il framework pre-commit (Python) per hook portabili e condivisibili
> 4. Integrare Husky e lint-staged in progetti JavaScript/TypeScript
> 5. Implementare hook server-side per enforcement centralizzato delle policy
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **pre-commit hook: lint, format, typecheck.**
2. **pre-commit framework (Python tool) gestisce hook portable.**
3. **`commit-msg` hook valida convenzionali (feat, fix, etc.).**
4. **Server-side hook (`pre-receive`, `post-receive`) per enforcement central.**


## Indice
- [Panoramica](#panoramica)
- [Fondamenti dei Git Hooks](#fondamenti-dei-git-hooks)
- [Hooks Client-Side](#hooks-client-side)
- [Hooks Server-Side](#hooks-server-side)
- [Scrivere Hook Scripts in Bash](#scrivere-hook-scripts-in-bash)
- [Scrivere Hook Scripts in Python](#scrivere-hook-scripts-in-python)
- [Pre-commit Framework](#pre-commit-framework)
- [Husky per Progetti JavaScript](#husky-per-progetti-javascript)
- [Lefthook](#lefthook)
- [Strategie di Distribuzione degli Hooks](#strategie-di-distribuzione-degli-hooks)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

I Git hooks sono script che vengono eseguiti automaticamente in risposta a specifici eventi nel ciclo di vita di Git. Rappresentano uno dei meccanismi di automazione più potenti e sottovalutati di Git, consentendo di personalizzare e automatizzare praticamente qualsiasi aspetto del workflow di versionamento. Dalla validazione del codice prima di un commit, all'invio di notifiche dopo un push, alla verifica delle policy di sicurezza prima dell'accettazione di codice su un server, i hooks permettono di implementare controlli di qualità e automazioni direttamente nel flusso di lavoro Git.

I hooks si dividono in due categorie principali: **client-side** (eseguiti sul computer dello sviluppatore) e **server-side** (eseguiti sul server che ospita il repository). Questa distinzione è fondamentale perché i hooks client-side possono essere bypassati dallo sviluppatore (con `--no-verify`), mentre i hooks server-side sono obbligatori e non aggirabili.

Un hook è semplicemente un file eseguibile posizionato nella directory `.git/hooks/` del repository. Git installa automaticamente degli script di esempio (con estensione `.sample`) quando si inizializza un repository. Per attivare un hook, è sufficiente rimuovere l'estensione `.sample` e rendere il file eseguibile.

```bash
# Visualizzare gli hook di esempio
ls .git/hooks/
# applypatch-msg.sample     pre-merge-commit.sample
# commit-msg.sample         pre-push.sample
# fsmonitor-watchman.sample pre-rebase.sample
# post-update.sample        prepare-commit-msg.sample
# pre-applypatch.sample     push-to-checkout.sample
# pre-commit.sample         update.sample

# Attivare un hook
cp .git/hooks/pre-commit.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Configurare una directory alternativa per gli hooks
git config core.hooksPath .githooks
```

---

## Fondamenti dei Git Hooks

### Meccanismo di Esecuzione

Quando Git esegue un hook, lo lancia come un processo separato con determinate variabili d'ambiente e argomenti. Il codice di uscita (exit code) dello script determina il comportamento di Git:

- **Exit code 0**: L'operazione procede normalmente
- **Exit code diverso da 0**: L'operazione viene interrotta (per gli hooks che lo supportano)

```bash
#!/bin/bash
# Un hook che blocca sempre l'operazione
echo "Operazione bloccata dal hook!"
exit 1

# Un hook che permette sempre l'operazione
echo "Check superato."
exit 0
```

### Variabili d'Ambiente

Git imposta diverse variabili d'ambiente quando esegue gli hooks:

```bash
# Variabili d'ambiente comuni
GIT_DIR          # Path alla directory .git
GIT_WORK_TREE    # Path alla working directory
GIT_AUTHOR_NAME  # Nome dell'autore (per commit hooks)
GIT_AUTHOR_EMAIL # Email dell'autore
GIT_AUTHOR_DATE  # Data dell'autore
GIT_INDEX_FILE   # Path all'index file
```

### Ordine di Esecuzione

Per un'operazione di commit tipica, gli hooks vengono eseguiti in questo ordine:

1. `pre-commit` — Prima della creazione del commit
2. `prepare-commit-msg` — Dopo la generazione del messaggio predefinito, prima dell'editor
3. `commit-msg` — Dopo che l'utente ha inserito il messaggio
4. `post-commit` — Dopo la creazione del commit

Per un'operazione di push:

1. `pre-push` — Prima dell'invio al remote
2. (sul server) `pre-receive` — Prima dell'accettazione
3. (sul server) `update` — Per ogni branch aggiornato
4. (sul server) `post-receive` — Dopo l'accettazione
5. (sul server) `post-update` — Dopo l'aggiornamento dei riferimenti

---

## Hooks Client-Side

### pre-commit

Il hook `pre-commit` viene eseguito prima della creazione di un commit, prima ancora che l'editor del messaggio venga aperto. È il luogo ideale per controlli di qualità del codice.

```bash
#!/bin/bash
# .git/hooks/pre-commit
# Controlla che non ci siano file con conflitti di merge non risolti

# Verificare la presenza di marker di conflitto
if git diff --cached --diff-filter=ACM | grep -E "^[<>=]{7}" > /dev/null; then
    echo "ERRORE: Marker di conflitto trovati nei file staged!"
    echo "Risolvere i conflitti prima di committare."
    exit 1
fi

# Verificare che non ci siano file con TODO critici
if git diff --cached | grep -i "FIXME\|HACK\|XXX" > /dev/null; then
    echo "ATTENZIONE: Trovati FIXME/HACK/XXX nel codice."
    echo "Risolvere prima di committare o usare git commit --no-verify per bypassare."
    exit 1
fi

# Eseguire il linter per i file JavaScript staged
STAGED_JS_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.js$')
if [ -n "$STAGED_JS_FILES" ]; then
    echo "Esecuzione ESLint sui file JavaScript staged..."
    npx eslint $STAGED_JS_FILES
    if [ $? -ne 0 ]; then
        echo "ERRORE: ESLint ha trovato errori. Correggere prima di committare."
        exit 1
    fi
fi

# Verificare che non ci siano chiavi API o segreti nei file staged
PATTERNS="(?i)(api[_-]?key|secret|password|token|private[_-]?key)\s*[=:]\s*['\"][^'\"]{8,}"
if git diff --cached -U0 | grep -P "$PATTERNS" > /dev/null; then
    echo "ERRORE: Possibili segreti trovati nei file staged!"
    echo "Rimuovere le credenziali dal codice."
    exit 1
fi

# Verificare la dimensione dei file staged
MAX_SIZE=5242880  # 5 MB
for file in $(git diff --cached --name-only --diff-filter=ACM); do
    size=$(wc -c < "$file" 2>/dev/null || echo 0)
    if [ "$size" -gt "$MAX_SIZE" ]; then
        echo "ERRORE: Il file $file è troppo grande ($(($size / 1024 / 1024)) MB)."
        echo "Considerare l'uso di Git LFS per file grandi."
        exit 1
    fi
done

echo "Pre-commit checks superati."
exit 0
```

### prepare-commit-msg

Questo hook viene eseguito dopo la generazione del messaggio predefinito ma prima che l'editor venga aperto. Riceve come argomenti il path del file temporaneo con il messaggio, il tipo di commit e l'hash SHA-1 (per amend).

```bash
#!/bin/bash
# .git/hooks/prepare-commit-msg

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2
SHA1=$3

# Aggiungere automaticamente il nome del branch al messaggio
BRANCH_NAME=$(git symbolic-ref --short HEAD 2>/dev/null)

# Estrarre il numero del ticket dal nome del branch
# Esempio: feature/JIRA-123-descrizione → JIRA-123
TICKET=$(echo "$BRANCH_NAME" | grep -oE '[A-Z]+-[0-9]+')

if [ -n "$TICKET" ]; then
    # Verificare che il ticket non sia già nel messaggio
    if ! grep -q "$TICKET" "$COMMIT_MSG_FILE"; then
        # Aggiungere il ticket all'inizio del messaggio
        sed -i.bak "1s/^/[$TICKET] /" "$COMMIT_MSG_FILE"
    fi
fi

# Per merge commit, non modificare il messaggio predefinito
if [ "$COMMIT_SOURCE" = "merge" ]; then
    exit 0
fi

# Aggiungere un template se il messaggio è vuoto
if [ "$COMMIT_SOURCE" = "" ]; then
    cat << 'EOF' >> "$COMMIT_MSG_FILE"

# Formato: <tipo>(<scope>): <descrizione>
#
# Tipi: feat, fix, docs, style, refactor, test, chore
# Scope: componente o area del progetto
#
# Esempio: feat(auth): aggiungere login con OAuth2
EOF
fi
```

### commit-msg

Il hook `commit-msg` viene eseguito dopo che l'utente ha inserito il messaggio di commit. Riceve il path del file temporaneo con il messaggio come argomento. È il luogo ideale per validare il formato del messaggio.

```bash
#!/bin/bash
# .git/hooks/commit-msg

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Validare il formato Conventional Commits
PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,72}$"

# Ignorare merge commit
if echo "$COMMIT_MSG" | head -1 | grep -q "^Merge"; then
    exit 0
fi

# Controllare la prima riga
FIRST_LINE=$(echo "$COMMIT_MSG" | head -1)

if ! echo "$FIRST_LINE" | grep -qE "$PATTERN"; then
    echo "ERRORE: Il messaggio di commit non rispetta il formato Conventional Commits."
    echo ""
    echo "Formato richiesto: <tipo>(<scope>): <descrizione>"
    echo ""
    echo "Tipi validi: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
    echo ""
    echo "Esempio: feat(auth): aggiungere supporto OAuth2"
    echo ""
    echo "Il tuo messaggio: $FIRST_LINE"
    exit 1
fi

# Verificare la lunghezza della prima riga (max 72 caratteri)
if [ ${#FIRST_LINE} -gt 72 ]; then
    echo "ERRORE: La prima riga del messaggio è troppo lunga (${#FIRST_LINE} caratteri, max 72)."
    exit 1
fi

# Verificare che la prima lettera della descrizione sia minuscola
DESC=$(echo "$FIRST_LINE" | sed 's/^[^:]*: //')
if echo "$DESC" | grep -q "^[A-Z]"; then
    echo "ATTENZIONE: La descrizione dovrebbe iniziare con lettera minuscola."
    echo "Attuale: $DESC"
    # Non bloccare, solo avvertire
fi

echo "Messaggio di commit valido."
exit 0
```

### post-commit

Il hook `post-commit` viene eseguito dopo la creazione del commit. Non può influenzare il commit (l'operazione è già completata), ma è utile per notifiche e azioni post-commit.

```bash
#!/bin/bash
# .git/hooks/post-commit

# Notifica desktop dopo un commit
COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_HASH=$(git log -1 --pretty=%h)
BRANCH=$(git symbolic-ref --short HEAD)

# Linux (notify-send)
if command -v notify-send &> /dev/null; then
    notify-send "Git Commit" "[$BRANCH] $COMMIT_HASH: $COMMIT_MSG"
fi

# macOS (osascript)
if command -v osascript &> /dev/null; then
    osascript -e "display notification \"$COMMIT_HASH: $COMMIT_MSG\" with title \"Git Commit su $BRANCH\""
fi

# Aggiornare un file di log
echo "$(date '+%Y-%m-%d %H:%M:%S') | $BRANCH | $COMMIT_HASH | $COMMIT_MSG" >> ~/.git-commit-log

exit 0
```

### pre-push

Il hook `pre-push` viene eseguito prima che i dati vengano inviati al remote. Riceve il nome e l'URL del remote come argomenti, e le informazioni sugli aggiornamenti su stdin.

```bash
#!/bin/bash
# .git/hooks/pre-push

REMOTE=$1
URL=$2

# Impedire push diretti a main/master
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
PROTECTED_BRANCHES="^(main|master|develop|release/.*)$"

while read local_ref local_sha remote_ref remote_sha; do
    remote_branch=$(echo "$remote_ref" | sed 's|refs/heads/||')

    if echo "$remote_branch" | grep -qE "$PROTECTED_BRANCHES"; then
        echo "ERRORE: Push diretto a '$remote_branch' non è permesso!"
        echo "Creare una pull request per integrare le modifiche."
        exit 1
    fi
done

# Eseguire i test prima del push
echo "Esecuzione dei test prima del push..."
if [ -f "package.json" ]; then
    npm test
    if [ $? -ne 0 ]; then
        echo "ERRORE: I test sono falliti. Correggere prima di pushare."
        exit 1
    fi
elif [ -f "pytest.ini" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    python -m pytest
    if [ $? -ne 0 ]; then
        echo "ERRORE: I test sono falliti. Correggere prima di pushare."
        exit 1
    fi
fi

# Verificare che non si stia pushando commit WIP
if git log @{u}..HEAD --oneline 2>/dev/null | grep -qi "WIP\|work in progress\|fixup!\|squash!"; then
    echo "ATTENZIONE: Commit WIP/fixup!/squash! trovati."
    echo "Eseguire un rebase interattivo per pulire la cronologia."
    read -p "Continuare comunque? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Pre-push checks superati."
exit 0
```

### pre-rebase

```bash
#!/bin/bash
# .git/hooks/pre-rebase
# Impedire il rebase di branch condivisi

UPSTREAM=$1
BRANCH=$2

if [ -z "$BRANCH" ]; then
    BRANCH=$(git symbolic-ref --short HEAD)
fi

# Branch che non dovrebbero mai essere rebasati
PROTECTED="^(main|master|develop|release/.*)$"

if echo "$BRANCH" | grep -qE "$PROTECTED"; then
    echo "ERRORE: Non è permesso il rebase del branch protetto '$BRANCH'."
    exit 1
fi

exit 0
```

### post-checkout

Il hook `post-checkout` viene eseguito dopo un'operazione di checkout riuscita (`git checkout`, `git switch`). Riceve tre argomenti: il ref precedente, il nuovo ref e un flag che indica se si tratta di un checkout di branch (1) o di un checkout di file (0). È utile per configurare l'ambiente di lavoro in base al branch, ripulire artefatti generati o aggiornare dipendenze.

```bash
#!/bin/bash
# .git/hooks/post-checkout

PREV_HEAD=$1
NEW_HEAD=$2
BRANCH_CHECKOUT=$3

# Eseguire solo per checkout di branch, non di file singoli
if [ "$BRANCH_CHECKOUT" != "1" ]; then
    exit 0
fi

BRANCH_NAME=$(git symbolic-ref --short HEAD 2>/dev/null)

echo "Checkout completato: branch $BRANCH_NAME"

# Pulire artefatti di build precedenti
if [ -d "dist" ]; then
    echo "Pulizia directory dist/..."
    rm -rf dist/
fi

if [ -d "__pycache__" ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
fi

# Reinstallare dipendenze se il lockfile è cambiato
if git diff --name-only "$PREV_HEAD" "$NEW_HEAD" | grep -q "package-lock.json\|yarn.lock\|pnpm-lock.yaml"; then
    echo "Lockfile cambiato. Reinstallazione dipendenze Node.js..."
    if [ -f "pnpm-lock.yaml" ]; then
        pnpm install --frozen-lockfile
    elif [ -f "yarn.lock" ]; then
        yarn install --frozen-lockfile
    elif [ -f "package-lock.json" ]; then
        npm ci
    fi
fi

if git diff --name-only "$PREV_HEAD" "$NEW_HEAD" | grep -q "requirements.txt\|Pipfile.lock\|poetry.lock"; then
    echo "Lockfile Python cambiato. Reinstallazione dipendenze..."
    if [ -f "poetry.lock" ]; then
        poetry install --no-interaction
    elif [ -f "Pipfile.lock" ]; then
        pipenv install --deploy
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
fi

# Eseguire migrazioni del database se ci sono cambiamenti ai file di migrazione
if git diff --name-only "$PREV_HEAD" "$NEW_HEAD" | grep -q "migrations/"; then
    echo "File di migrazione cambiati. Eseguire le migrazioni del database."
fi

# Configurazione ambiente-specifica per branch
case "$BRANCH_NAME" in
    develop|staging)
        echo "Ambiente: STAGING"
        [ -f ".env.staging" ] && cp .env.staging .env.local
        ;;
    main|master)
        echo "Ambiente: PRODUCTION"
        [ -f ".env.production" ] && cp .env.production .env.local
        ;;
    feature/*)
        echo "Ambiente: DEVELOPMENT"
        [ -f ".env.development" ] && cp .env.development .env.local
        ;;
esac

exit 0
```

### post-merge

Il hook `post-merge` viene eseguito dopo un merge riuscito (incluso `git pull`, che internamente esegue un merge). Riceve un singolo argomento: un flag che indica se il merge è stato un squash merge (1) o un merge normale (0). Non può influenzare il merge (è già completato), ma è ideale per aggiornare dipendenze e notificare cambiamenti.

```bash
#!/bin/bash
# .git/hooks/post-merge

SQUASH_MERGE=$1

# Rilevare cambiamenti nei lockfile e reinstallare
changed_files=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD)

# Node.js: reinstallare se package-lock.json è cambiato
if echo "$changed_files" | grep -qE "package-lock\.json|yarn\.lock|pnpm-lock\.yaml"; then
    echo "==> Dipendenze Node.js aggiornate. Esecuzione install..."
    if [ -f "pnpm-lock.yaml" ]; then
        pnpm install --frozen-lockfile
    elif [ -f "yarn.lock" ]; then
        yarn install --frozen-lockfile
    elif [ -f "package-lock.json" ]; then
        npm ci
    fi
fi

# Python: reinstallare se requirements è cambiato
if echo "$changed_files" | grep -qE "requirements.*\.txt|Pipfile\.lock|poetry\.lock|pyproject\.toml"; then
    echo "==> Dipendenze Python aggiornate. Esecuzione install..."
    if [ -f "poetry.lock" ]; then
        poetry install --no-interaction
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
fi

# Go: riscaricare moduli se go.sum è cambiato
if echo "$changed_files" | grep -q "go.sum"; then
    echo "==> Moduli Go aggiornati. Esecuzione go mod download..."
    go mod download
fi

# Rust: ricompilare se Cargo.lock è cambiato
if echo "$changed_files" | grep -q "Cargo.lock"; then
    echo "==> Dipendenze Rust aggiornate. Esecuzione cargo fetch..."
    cargo fetch
fi

# Migrazioni database
if echo "$changed_files" | grep -qE "migrations/|alembic/"; then
    echo ""
    echo "=========================================================="
    echo "  ATTENZIONE: File di migrazione cambiati!"
    echo "  Eseguire le migrazioni del database prima di continuare."
    echo "=========================================================="
    echo ""
fi

# Notifica se la configurazione CI è cambiata
if echo "$changed_files" | grep -qE "\.github/workflows/|\.gitlab-ci\.yml|Jenkinsfile"; then
    echo "==> Configurazione CI/CD aggiornata. Verificare le pipeline."
fi

exit 0
```

### pre-auto-gc

Il hook `pre-auto-gc` viene invocato da `git gc --auto`. Se esce con un codice diverso da 0, il garbage collection automatico viene annullato. Questo hook è utile per prevenire il gc durante operazioni critiche o per inviare notifiche quando il repository necessita di manutenzione.

```bash
#!/bin/bash
# .git/hooks/pre-auto-gc

# Impedire gc automatico durante ore di lavoro intensive
HOUR=$(date +%H)
if [ "$HOUR" -ge 9 ] && [ "$HOUR" -le 17 ]; then
    echo "GC automatico posticipato: ore lavorative (${HOUR}:00)."
    echo "Il GC verrà eseguito automaticamente fuori orario."
    exit 1
fi

# Notificare il team se il repository è diventato molto grande
REPO_SIZE=$(du -sm .git | cut -f1)
if [ "$REPO_SIZE" -gt 500 ]; then
    echo "ATTENZIONE: Repository .git è ${REPO_SIZE} MB."
    echo "Considerare l'uso di git-filter-repo o BFG per ripulire la storia."
fi

exit 0
```

### fsmonitor-watchman

Il hook `fsmonitor-watchman` viene invocato quando la configurazione `core.fsmonitor` è impostata. Questo hook comunica con Facebook Watchman per accelerare le operazioni `git status` su repository molto grandi, riducendo drasticamente il numero di file che Git deve ispezionare.

```bash
# Abilitare fsmonitor con Watchman
git config core.fsmonitor .git/hooks/fsmonitor-watchman

# Git fornisce un hook di esempio:
# .git/hooks/fsmonitor-watchman.sample
# È scritto in Perl e comunica con il daemon Watchman

# Per repository molto grandi (>100k file), l'accelerazione è significativa:
# - git status senza fsmonitor: ~5 secondi
# - git status con fsmonitor:   ~0.2 secondi

# In alternativa, Git 2.37+ supporta il built-in file system monitor:
git config core.fsmonitor true
git config core.untrackedcache true
```

### Catalogo Completo degli Hook Client-Side

La seguente tabella fornisce un riferimento rapido per tutti gli hook client-side disponibili in Git 2.47+:

| Hook | Evento | Argomenti | Può Bloccare | Caso d'Uso Tipico |
|------|--------|-----------|--------------|-------------------|
| `applypatch-msg` | `git am` — prima di applicare una patch | File del messaggio | Sì | Validare il messaggio della patch |
| `pre-applypatch` | `git am` — dopo l'applicazione, prima del commit | Nessuno | Sì | Verificare lo stato del working tree |
| `post-applypatch` | `git am` — dopo il commit della patch | Nessuno | No | Notifiche, CI trigger |
| `pre-commit` | Prima della creazione del commit | Nessuno | Sì | Lint, format, test rapidi |
| `prepare-commit-msg` | Dopo il messaggio predefinito, prima dell'editor | File msg, tipo, SHA1 | Sì | Template, ticket injection |
| `commit-msg` | Dopo l'inserimento del messaggio | File del messaggio | Sì | Validazione Conventional Commits |
| `post-commit` | Dopo la creazione del commit | Nessuno | No | Notifiche, log |
| `pre-rebase` | Prima di un rebase | Upstream, branch | Sì | Protezione branch condivisi |
| `post-rewrite` | Dopo `git commit --amend` o `git rebase` | Tipo di comando | No | Aggiornamento riferimenti esterni |
| `post-checkout` | Dopo un checkout riuscito | Ref prec., nuovo ref, flag branch | No | Setup ambiente, pulizia |
| `post-merge` | Dopo un merge riuscito | Flag squash | No | Reinstallazione dipendenze |
| `pre-push` | Prima dell'invio al remote | Nome remote, URL | Sì | Test, verifica commit |
| `pre-auto-gc` | Prima del garbage collection automatico | Nessuno | Sì | Posticipare gc, notifiche |
| `post-index-change` | Dopo modifica dell'index | Flag updated-workdir, updated-skipworktree | No | Monitoraggio index |
| `reference-transaction` | Durante transazione sui riferimenti | Stato (prepared/committed/aborted) | Sì (solo in prepared) | Auditing riferimenti |
| `fsmonitor-watchman` | Query al filesystem monitor | Versione, timestamp/token | No | Accelerazione `git status` |

---

## Hooks Server-Side

### pre-receive

Il hook `pre-receive` è il gatekeeper definitivo sul server. Viene eseguito una sola volta per ogni push e riceve su stdin le informazioni su tutti i riferimenti che stanno per essere aggiornati. Se esce con un codice diverso da 0, l'intero push viene rifiutato.

```bash
#!/bin/bash
# hooks/pre-receive (sul server)

while read oldrev newrev refname; do
    # Impedire push forzati (non fast-forward) su branch protetti
    if [ "$oldrev" != "0000000000000000000000000000000000000000" ]; then
        BRANCH=$(echo "$refname" | sed 's|refs/heads/||')

        if echo "$BRANCH" | grep -qE "^(main|master|develop)$"; then
            # Verificare che sia fast-forward
            MERGE_BASE=$(git merge-base "$oldrev" "$newrev" 2>/dev/null)
            if [ "$MERGE_BASE" != "$oldrev" ]; then
                echo "ERRORE: Push forzato non permesso su '$BRANCH'."
                echo "Usare una pull request per integrare le modifiche."
                exit 1
            fi
        fi
    fi

    # Verificare la dimensione dei file nel push
    if [ "$newrev" != "0000000000000000000000000000000000000000" ]; then
        MAX_FILE_SIZE=10485760  # 10 MB
        LARGE_FILES=$(git rev-list "$oldrev..$newrev" 2>/dev/null | while read rev; do
            git diff-tree -r --diff-filter=ACM "$rev" 2>/dev/null | while read mode_old mode_new hash_old hash_new status name; do
                size=$(git cat-file -s "$hash_new" 2>/dev/null || echo 0)
                if [ "$size" -gt "$MAX_FILE_SIZE" ]; then
                    echo "$name ($((size / 1024 / 1024)) MB)"
                fi
            done
        done)

        if [ -n "$LARGE_FILES" ]; then
            echo "ERRORE: File troppo grandi nel push:"
            echo "$LARGE_FILES"
            echo "Usare Git LFS per file grandi."
            exit 1
        fi
    fi

    # Verificare i messaggi di commit
    if [ "$newrev" != "0000000000000000000000000000000000000000" ] && \
       [ "$oldrev" != "0000000000000000000000000000000000000000" ]; then
        PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
        BAD_COMMITS=$(git log --format="%H %s" "$oldrev..$newrev" | while read hash msg; do
            if ! echo "$msg" | grep -qE "$PATTERN"; then
                echo "  $hash: $msg"
            fi
        done)

        if [ -n "$BAD_COMMITS" ]; then
            echo "ERRORE: Commit con messaggi non conformi:"
            echo "$BAD_COMMITS"
            echo ""
            echo "Formato richiesto: <tipo>: <descrizione>"
            exit 1
        fi
    fi
done

exit 0
```

### update

Il hook `update` viene eseguito una volta per ogni branch aggiornato nel push. Riceve tre argomenti: il nome del riferimento, il vecchio SHA-1 e il nuovo SHA-1. A differenza di `pre-receive`, può accettare o rifiutare aggiornamenti individuali.

```bash
#!/bin/bash
# hooks/update (sul server)

REFNAME=$1
OLDREV=$2
NEWREV=$3

BRANCH=$(echo "$REFNAME" | sed 's|refs/heads/||')

# Impedire la creazione di branch con nomi non conformi
if [ "$OLDREV" = "0000000000000000000000000000000000000000" ]; then
    BRANCH_PATTERN="^(main|develop|feature/.+|bugfix/.+|hotfix/.+|release/.+)$"
    if ! echo "$BRANCH" | grep -qE "$BRANCH_PATTERN"; then
        echo "ERRORE: Il nome del branch '$BRANCH' non è conforme."
        echo "Pattern accettati: main, develop, feature/*, bugfix/*, hotfix/*, release/*"
        exit 1
    fi
fi

# Impedire la cancellazione di branch protetti
if [ "$NEWREV" = "0000000000000000000000000000000000000000" ]; then
    if echo "$BRANCH" | grep -qE "^(main|master|develop)$"; then
        echo "ERRORE: Non è permesso cancellare il branch '$BRANCH'."
        exit 1
    fi
fi

# Verificare che i commit siano firmati (per branch protetti)
if echo "$BRANCH" | grep -qE "^(main|release/)"; then
    UNSIGNED=$(git log --format="%H" "$OLDREV..$NEWREV" 2>/dev/null | while read hash; do
        if ! git verify-commit "$hash" 2>/dev/null; then
            echo "$hash"
        fi
    done)

    if [ -n "$UNSIGNED" ]; then
        echo "ERRORE: Commit non firmati trovati per il branch protetto '$BRANCH':"
        echo "$UNSIGNED"
        exit 1
    fi
fi

exit 0
```

### post-receive

Il hook `post-receive` viene eseguito dopo che tutti i riferimenti sono stati aggiornati. Non può rifiutare il push (è già completato), ma è ideale per notifiche, deployment automatici e trigger di CI/CD.

```bash
#!/bin/bash
# hooks/post-receive (sul server)

while read oldrev newrev refname; do
    BRANCH=$(echo "$refname" | sed 's|refs/heads/||')

    # Deployment automatico per il branch main
    if [ "$BRANCH" = "main" ]; then
        echo "Avvio deployment per main..."
        DEPLOY_DIR="/var/www/production"
        GIT_WORK_TREE="$DEPLOY_DIR" git checkout -f main
        cd "$DEPLOY_DIR"

        # Eseguire comandi post-deployment
        if [ -f "package.json" ]; then
            npm install --production
            npm run build
        fi

        # Riavviare il servizio
        sudo systemctl restart myapp

        echo "Deployment completato!"
    fi

    # Deployment per branch develop (staging)
    if [ "$BRANCH" = "develop" ]; then
        echo "Avvio deployment per staging..."
        STAGING_DIR="/var/www/staging"
        GIT_WORK_TREE="$STAGING_DIR" git checkout -f develop
        echo "Deployment staging completato!"
    fi

    # Notifica Slack
    COMMIT_MSG=$(git log -1 --format="%s" "$newrev")
    AUTHOR=$(git log -1 --format="%an" "$newrev")

    curl -s -X POST -H 'Content-type: application/json' \
        --data "{
            \"text\": \"Push su $BRANCH da $AUTHOR: $COMMIT_MSG\"
        }" \
        "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 &

    # Trigger CI/CD
    if [ -n "$CI_TRIGGER_URL" ]; then
        curl -s -X POST "$CI_TRIGGER_URL" \
            -H "Authorization: Bearer $CI_TOKEN" \
            -d "{\"branch\": \"$BRANCH\", \"commit\": \"$newrev\"}" > /dev/null 2>&1 &
    fi
done

exit 0
```

---

## Scrivere Hook Scripts in Bash

### Pattern Comuni per Hooks Bash

```bash
#!/bin/bash
set -euo pipefail  # Uscire su errore, variabili non definite, pipe failure

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funzioni di utilità
error() { echo -e "${RED}ERRORE: $1${NC}" >&2; }
warn()  { echo -e "${YELLOW}ATTENZIONE: $1${NC}" >&2; }
info()  { echo -e "${GREEN}$1${NC}"; }

# Ottenere i file staged
get_staged_files() {
    local filter="${1:-ACM}"  # Added, Copied, Modified
    local pattern="${2:-.*}"  # Tutti i file per default
    git diff --cached --name-only --diff-filter="$filter" | grep -E "$pattern" || true
}

# Esempio di uso
JS_FILES=$(get_staged_files "ACM" '\.(js|jsx|ts|tsx)$')
PY_FILES=$(get_staged_files "ACM" '\.py$')

if [ -n "$JS_FILES" ]; then
    info "Controllo file JavaScript/TypeScript..."
    echo "$JS_FILES" | xargs npx eslint --fix
    echo "$JS_FILES" | xargs git add  # Re-stage dei file corretti
fi

if [ -n "$PY_FILES" ]; then
    info "Controllo file Python..."
    echo "$PY_FILES" | xargs python -m flake8
    echo "$PY_FILES" | xargs python -m black --check
fi

info "Tutti i controlli superati!"
exit 0
```

### Hook con Supporto per Stash Parziale

Un pattern avanzato per hooks pre-commit che devono lavorare solo sui file staged, senza essere influenzati dalle modifiche non staged:

```bash
#!/bin/bash
# Pre-commit hook con stash delle modifiche non staged

# Salvare le modifiche non staged
STASH_NAME="pre-commit-$(date +%s)"
git stash save -q --keep-index "$STASH_NAME"

# Funzione di cleanup
cleanup() {
    # Ripristinare le modifiche non staged
    STASH_ID=$(git stash list | grep "$STASH_NAME" | head -1 | cut -d: -f1)
    if [ -n "$STASH_ID" ]; then
        git stash pop -q "$STASH_ID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Eseguire i controlli sui file staged
npm run lint-staged
TEST_RESULT=$?

exit $TEST_RESULT
```

---

## Scrivere Hook Scripts in Python

### Hook Pre-commit in Python

```python
#!/usr/bin/env python3
"""Pre-commit hook per validazione del codice."""

import subprocess
import sys
import re
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Eseguire un comando e restituire exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def get_staged_files(extensions: list[str] | None = None) -> list[str]:
    """Ottenere la lista dei file staged, filtrati per estensione."""
    _, stdout, _ = run_command(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    )
    files = [f.strip() for f in stdout.strip().split("\n") if f.strip()]
    if extensions:
        files = [f for f in files if Path(f).suffix in extensions]
    return files

def check_no_debug_statements(files: list[str]) -> bool:
    """Verificare che non ci siano statement di debug."""
    debug_patterns = [
        r'\bconsole\.log\b',
        r'\bdebugger\b',
        r'\bprint\s*\(',       # Python print (potrebbe avere falsi positivi)
        r'\bbreakpoint\s*\(',  # Python breakpoint
        r'\bpdb\.set_trace\b',
    ]
    has_errors = False
    for file in files:
        try:
            content = Path(file).read_text()
            for i, line in enumerate(content.split("\n"), 1):
                for pattern in debug_patterns:
                    if re.search(pattern, line):
                        print(f"  {file}:{i}: {line.strip()}")
                        has_errors = True
        except (FileNotFoundError, PermissionError):
            continue
    return not has_errors

def check_file_size(files: list[str], max_size_mb: float = 5.0) -> bool:
    """Verificare che i file non superino la dimensione massima."""
    max_size = int(max_size_mb * 1024 * 1024)
    has_errors = False
    for file in files:
        path = Path(file)
        if path.exists() and path.stat().st_size > max_size:
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  {file}: {size_mb:.1f} MB (max: {max_size_mb} MB)")
            has_errors = True
    return not has_errors

def check_no_secrets(files: list[str]) -> bool:
    """Verificare che non ci siano segreti nei file."""
    secret_patterns = [
        (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*["\'][^"\']{8,}', "Possibile API key/secret"),
        (r'(?i)password\s*[=:]\s*["\'][^"\']{4,}', "Possibile password hardcoded"),
        (r'AKIA[0-9A-Z]{16}', "Possibile AWS Access Key"),
        (r'(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "Chiave privata"),
    ]
    has_errors = False
    for file in files:
        try:
            content = Path(file).read_text()
            for i, line in enumerate(content.split("\n"), 1):
                for pattern, description in secret_patterns:
                    if re.search(pattern, line):
                        print(f"  {file}:{i}: {description}")
                        has_errors = True
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            continue
    return not has_errors

def main() -> int:
    """Funzione principale del hook."""
    all_files = get_staged_files()
    if not all_files:
        return 0

    checks = [
        ("Controllo statement di debug", check_no_debug_statements, all_files),
        ("Controllo dimensione file", check_file_size, all_files),
        ("Controllo segreti", check_no_secrets, all_files),
    ]

    all_passed = True
    for name, check_fn, files in checks:
        print(f"\n🔍 {name}...")
        if not check_fn(files):
            print(f"  ❌ {name}: FALLITO")
            all_passed = False
        else:
            print(f"  ✅ {name}: OK")

    if not all_passed:
        print("\n❌ Pre-commit check falliti. Correggere gli errori prima di committare.")
        print("Usare 'git commit --no-verify' per bypassare (sconsigliato).")
        return 1

    print("\n✅ Tutti i pre-commit check superati!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## Pre-commit Framework

### Introduzione al Framework

Il framework **pre-commit** (https://pre-commit.com) è lo standard de facto per la gestione degli hooks in progetti multi-linguaggio. Fornisce un sistema di plugin con centinaia di hooks predefiniti per diversi linguaggi e strumenti.

### Installazione e Configurazione

```bash
# Installazione tramite pip
pip install pre-commit

# Installazione tramite pipx (consigliato per tool CLI)
pipx install pre-commit

# Installazione tramite Homebrew (macOS)
brew install pre-commit

# Verificare l'installazione
pre-commit --version
```

### File di Configurazione

Il framework si configura tramite un file `.pre-commit-config.yaml` nella root del repository:

```yaml
# .pre-commit-config.yaml
# Vedi https://pre-commit.com per ulteriori informazioni
# Vedi https://pre-commit.com/hooks.html per più hooks

repos:
  # Hook predefiniti del framework
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace        # Rimuovere spazi finali
      - id: end-of-file-fixer          # Assicurare newline finale
      - id: check-yaml                  # Validare file YAML
      - id: check-json                  # Validare file JSON
      - id: check-toml                  # Validare file TOML
      - id: check-added-large-files     # Bloccare file grandi
        args: ['--maxkb=500']
      - id: check-merge-conflict        # Bloccare marker di conflitto
      - id: detect-private-key          # Rilevare chiavi private
      - id: no-commit-to-branch         # Bloccare commit su branch protetti
        args: ['--branch', 'main', '--branch', 'master']
      - id: check-case-conflict         # Rilevare conflitti di case nel filesystem
      - id: mixed-line-ending           # Verificare line endings consistenti

  # Python: Black formatter
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.12

  # Python: Ruff linter (sostituto veloce di flake8/isort)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Python: mypy type checker
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  # JavaScript/TypeScript: ESLint
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        additional_dependencies:
          - eslint@8.56.0
          - eslint-config-prettier@9.1.0

  # Prettier (multi-linguaggio)
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, css, json, yaml, markdown]

  # Shell: shellcheck
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck

  # Docker: hadolint
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker

  # Sicurezza: gitleaks (rilevamento segreti)
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks

  # Terraform
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.86.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint

  # Hook locale personalizzato
  - repo: local
    hooks:
      - id: run-tests
        name: Run unit tests
        entry: npm test
        language: system
        pass_filenames: false
        always_run: true
        stages: [push]  # Eseguire solo al push, non al commit

# Configurazione globale
default_language_version:
  python: python3.12
  node: "20.11.0"

default_stages: [commit]

# File da escludere globalmente
exclude: |
  (?x)^(
    .*\.min\.js|
    .*\.min\.css|
    vendor/.*|
    node_modules/.*
  )$
```

### Comandi Principali

```bash
# Installare gli hooks nel repository
pre-commit install

# Installare hooks per diversi stage
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg

# Eseguire tutti gli hooks su tutti i file
pre-commit run --all-files

# Eseguire un hook specifico
pre-commit run black --all-files

# Aggiornare le versioni dei repository degli hooks
pre-commit autoupdate

# Eseguire hooks solo sui file staged
pre-commit run

# Pulire la cache
pre-commit clean

# Disinstallare gli hooks
pre-commit uninstall
```

---

## Husky per Progetti JavaScript

### Installazione e Configurazione

**Husky** è il gestore di hooks più popolare nell'ecosistema JavaScript/Node.js. La versione moderna (v9+) usa un approccio basato su file nella directory `.husky/`.

```bash
# Installazione
npm install --save-dev husky

# Inizializzazione
npx husky init

# Questo crea:
# - .husky/ directory
# - .husky/pre-commit (script di esempio)
# - Aggiunge "prepare": "husky" al package.json
```

### Configurazione degli Hooks

```bash
# .husky/pre-commit
npm run lint-staged

# .husky/commit-msg
npx --no -- commitlint --edit $1

# .husky/pre-push
npm test
```

### Integrazione con lint-staged

**lint-staged** esegue linter solo sui file staged, migliorando drasticamente le performance:

```bash
npm install --save-dev lint-staged
```

```json
// package.json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,scss}": [
      "prettier --write"
    ],
    "*.{json,yaml,yml,md}": [
      "prettier --write"
    ]
  }
}
```

### Integrazione con Commitlint

```bash
npm install --save-dev @commitlint/cli @commitlint/config-conventional
```

```javascript
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
  },
};
```

---

## Lefthook

### Introduzione a Lefthook

**Lefthook** è un gestore di hooks veloce e multi-linguaggio scritto in Go. È significativamente più veloce di Husky e del framework pre-commit per l'esecuzione parallela degli hooks.

```bash
# Installazione
# macOS
brew install lefthook

# npm
npm install lefthook --save-dev

# Go
go install github.com/evilmartians/lefthook@latest

# Inizializzazione
lefthook install
```

### Configurazione

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    eslint:
      glob: "*.{js,jsx,ts,tsx}"
      run: npx eslint --fix {staged_files}
      stage_fixed: true
    prettier:
      glob: "*.{js,jsx,ts,tsx,css,json,yaml,md}"
      run: npx prettier --write {staged_files}
      stage_fixed: true
    python-lint:
      glob: "*.py"
      run: ruff check --fix {staged_files}
      stage_fixed: true
    python-format:
      glob: "*.py"
      run: black {staged_files}
      stage_fixed: true
    check-secrets:
      run: gitleaks protect --staged --verbose

commit-msg:
  commands:
    commitlint:
      run: npx commitlint --edit {1}

pre-push:
  parallel: true
  commands:
    test:
      run: npm test
    type-check:
      run: npx tsc --noEmit
    security-audit:
      run: npm audit --audit-level=high

# Skippare hooks in CI
skip:
  - merge
  - rebase
```

### Vantaggi di Lefthook

- **Esecuzione parallela**: I comandi vengono eseguiti in parallelo per default
- **Stage automatico**: I file corretti possono essere ri-staged automaticamente
- **Multi-linguaggio**: Nessuna dipendenza da Node.js o Python
- **Configurazione dichiarativa**: File YAML semplice e leggibile
- **Performance**: Scritto in Go, estremamente veloce
- **Glob pattern**: Supporto nativo per pattern di file

---

## Strategie di Distribuzione degli Hooks

### Problema della Distribuzione

I Git hooks risiedono in `.git/hooks/`, che non è versionato. Questo crea il problema di come distribuire e sincronizzare gli hooks tra tutti i membri del team.

### Strategia 1: core.hooksPath

La soluzione più semplice è usare la configurazione `core.hooksPath` per puntare a una directory versionata:

```bash
# Creare una directory per gli hooks nel repository
mkdir -p .githooks

# Copiare gli hooks nella directory
cp .git/hooks/pre-commit .githooks/
chmod +x .githooks/*

# Configurare Git per usare la directory versionata
git config core.hooksPath .githooks

# Documentare nel README o nello script di setup
echo "git config core.hooksPath .githooks" >> setup.sh
```

### Strategia 2: Framework Dedicato

Usare un framework come pre-commit, Husky o Lefthook che gestisce automaticamente l'installazione degli hooks:

```bash
# pre-commit: aggiungere al CI/setup
pre-commit install --install-hooks

# Husky: automatico tramite "prepare" script in package.json
# "prepare": "husky"

# Lefthook: automatico tramite postinstall
# "postinstall": "lefthook install"
```

### Strategia 3: Template Directory

Configurare una template directory globale che viene usata quando si inizializzano o clonano repository:

```bash
# Creare la template directory
mkdir -p ~/.git-templates/hooks
cp pre-commit ~/.git-templates/hooks/
chmod +x ~/.git-templates/hooks/*

# Configurare Git per usare il template
git config --global init.templateDir ~/.git-templates

# I nuovi repository avranno automaticamente gli hooks
git init nuovo-progetto
# nuovo-progetto/.git/hooks/ conterrà gli hooks dal template
```

### Strategia 4: Makefile o Script di Setup

```makefile
# Makefile
.PHONY: setup install-hooks

setup: install-hooks
	@echo "Setup completato"

install-hooks:
	@echo "Installazione hooks..."
	@cp .githooks/* .git/hooks/ 2>/dev/null || true
	@chmod +x .git/hooks/* 2>/dev/null || true
	@echo "Hooks installati."
```

---

## Best Practices

### Principi Generali

1. **Hook veloci**: I hooks pre-commit dovrebbero completarsi in secondi, non minuti. Se un check è lento, spostarlo al pre-push o al CI.

2. **Exit code corretti**: Usare sempre exit code 0 per successo e diverso da 0 per fallimento. Non dimenticare `set -e` in Bash.

3. **Output informativo**: Mostrare messaggi chiari su cosa è andato storto e come correggere il problema. Includere il comando per bypassare l'hook quando appropriato.

4. **Bypassabilità documentata**: Documentare quando e come usare `--no-verify`, ma scoraggiarne l'uso abituale.

5. **Idempotenza**: Gli hooks dovrebbero essere sicuri da eseguire multiple volte senza effetti collaterali.

### Sicurezza

1. **Non fidarsi dei hooks client-side per la sicurezza**: I hooks client-side possono essere bypassati. Le policy di sicurezza devono essere implementate come hooks server-side o nel CI.

2. **Validare gli input**: Gli hooks server-side ricevono dati potenzialmente non fidati. Validare e sanitizzare tutti gli input.

3. **Non esporre segreti**: Gli hooks non dovrebbero stampare segreti, token o credenziali nell'output.

### Performance

1. **Linting incrementale**: Eseguire i linter solo sui file modificati, non sull'intero progetto.

2. **Esecuzione parallela**: Quando possibile, eseguire i controlli in parallelo.

3. **Caching**: Usare cache per strumenti come ESLint, mypy e ruff che supportano il caching.

4. **Skip condizionale**: Saltare controlli che non sono rilevanti per i file modificati.

---

## Troubleshooting

### Hook Non Eseguito

```bash
# Verificare i permessi
ls -la .git/hooks/pre-commit
# Deve essere eseguibile: -rwxr-xr-x

chmod +x .git/hooks/pre-commit

# Verificare lo shebang
head -1 .git/hooks/pre-commit
# Deve essere #!/bin/bash o #!/usr/bin/env python3

# Verificare il path degli hooks
git config core.hooksPath
# Se configurato, gli hooks devono essere nella directory specificata

# Verificare che non sia stato usato --no-verify
# Non c'è un modo per verificare post-hoc
```

### Hook Fallisce con Errore di Ambiente

```bash
# Problema: il hook non trova un comando (es. npx, python)
# Causa: PATH diverso nell'ambiente dell'hook

# Soluzione: Specificare il path completo
#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
# oppure
/usr/local/bin/npx eslint .
```

### Hook Lento

```bash
# Diagnostica: misurare il tempo di esecuzione
time .git/hooks/pre-commit

# Soluzione: profilare e ottimizzare
# Eseguire solo sui file staged, non su tutto il progetto
# Usare caching dove possibile
# Spostare controlli lenti al pre-push
```

### Conflitto tra Framework

```bash
# Se si usano sia Husky che pre-commit:
# Scegliere uno solo. Non mescolare i framework.

# Disinstallare pre-commit
pre-commit uninstall

# Oppure disinstallare Husky
npx husky uninstall
npm uninstall husky
```

---

## Conventional Commits e Automazione del Versionamento

### La Specifica Conventional Commits

La specifica **Conventional Commits** (https://www.conventionalcommits.org/) fornisce un set leggero di regole per creare una cronologia di commit esplicita e leggibile dalle macchine. È stata progettata per integrarsi perfettamente con il **Semantic Versioning** (SemVer), descrivendo nel messaggio di commit le feature aggiunte, i bug corretti e le breaking changes introdotte.

Il formato del messaggio è il seguente:

```
<tipo>[scope opzionale][!]: <descrizione>

[corpo opzionale]

[footer opzionali]
```

#### Tipi Standard

| Tipo | Descrizione | Bump SemVer |
|------|-------------|-------------|
| `feat` | Nuova funzionalità | MINOR (0.x.0) |
| `fix` | Correzione di un bug | PATCH (0.0.x) |
| `docs` | Modifiche alla documentazione | Nessuno |
| `style` | Formattazione, punto e virgola mancanti, etc. | Nessuno |
| `refactor` | Ristrutturazione del codice senza cambiamenti funzionali | Nessuno |
| `perf` | Miglioramento delle performance | PATCH |
| `test` | Aggiunta o correzione di test | Nessuno |
| `build` | Cambiamenti al sistema di build (webpack, npm, etc.) | Nessuno |
| `ci` | Cambiamenti alla configurazione CI/CD | Nessuno |
| `chore` | Manutenzione, aggiornamento dipendenze | Nessuno |
| `revert` | Annullamento di un commit precedente | Dipende dal commit annullato |

L'aggiunta di `!` dopo il tipo/scope, oppure l'inclusione di un footer `BREAKING CHANGE:`, indica una **breaking change** che produce un bump MAJOR (x.0.0).

#### Esempi Completi

```
feat(auth): aggiungere autenticazione OAuth2 con Google

Implementata l'autenticazione tramite Google OAuth2 come provider alternativo.
L'utente può ora accedere con il proprio account Google oltre alle
credenziali tradizionali email/password.

Closes #142
```

```
fix(api): correggere race condition nella cache delle sessioni

La cache delle sessioni poteva restituire dati stantii quando due
richieste concorrenti invalidavano la stessa entry. Aggiunto un
mutex per sincronizzare l'accesso alla cache.

Fixes #891
```

```
feat(api)!: rimuovere endpoint v1 deprecati

BREAKING CHANGE: Gli endpoint /api/v1/* sono stati rimossi.
Migrare a /api/v2/* seguendo la guida di migrazione in docs/migration-v2.md.
```

### Hook commit-msg Avanzato per Conventional Commits

Un hook `commit-msg` più sofisticato che gestisce scenari reali come merge commit, revert, fixup, e validazione approfondita del formato:

```bash
#!/bin/bash
# .git/hooks/commit-msg — Validazione avanzata Conventional Commits

set -euo pipefail

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")
FIRST_LINE=$(echo "$COMMIT_MSG" | head -1)

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

error() { echo -e "${RED}ERRORE:${NC} $1" >&2; }
warn()  { echo -e "${YELLOW}ATTENZIONE:${NC} $1" >&2; }
info()  { echo -e "${GREEN}OK:${NC} $1"; }

# Esclusioni: merge commit, revert, fixup, squash, WIP
SKIP_PATTERNS="^(Merge|Revert|fixup!|squash!|amend!|WIP)"
if echo "$FIRST_LINE" | grep -qE "$SKIP_PATTERNS"; then
    info "Commit speciale rilevato, validazione skippata."
    exit 0
fi

# Pattern Conventional Commits
# tipo(scope opzionale)!: descrizione
PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9_-]+\))?(!)?: .{1,}"

if ! echo "$FIRST_LINE" | grep -qE "$PATTERN"; then
    error "Il messaggio non rispetta il formato Conventional Commits."
    echo ""
    echo -e "${CYAN}Formato richiesto:${NC} <tipo>(<scope>): <descrizione>"
    echo ""
    echo "Tipi validi: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
    echo ""
    echo -e "Esempio:   ${GREEN}feat(auth): aggiungere login con OAuth2${NC}"
    echo -e "Esempio:   ${GREEN}fix: correggere crash all'avvio su Windows${NC}"
    echo -e "Esempio:   ${GREEN}feat(api)!: rimuovere endpoint v1 deprecati${NC}"
    echo ""
    echo -e "Il tuo messaggio: ${RED}$FIRST_LINE${NC}"
    exit 1
fi

# Verificare la lunghezza della prima riga (max 72 caratteri)
FIRST_LINE_LEN=${#FIRST_LINE}
if [ "$FIRST_LINE_LEN" -gt 72 ]; then
    error "La prima riga è troppo lunga ($FIRST_LINE_LEN caratteri, max 72)."
    echo "  Spostare i dettagli nel corpo del messaggio."
    exit 1
fi

# Verificare che la descrizione non inizi con lettera maiuscola
DESC=$(echo "$FIRST_LINE" | sed 's/^[^:]*: //')
if echo "$DESC" | grep -q "^[A-Z]"; then
    warn "La descrizione dovrebbe iniziare con lettera minuscola."
    warn "  Attuale: \"$DESC\""
    # Non bloccare, solo avvertire
fi

# Verificare che la descrizione non termini con punto
if echo "$DESC" | grep -q '\.$'; then
    warn "La descrizione non dovrebbe terminare con un punto."
fi

# Verificare la separazione tra prima riga e corpo
LINES=$(echo "$COMMIT_MSG" | wc -l)
if [ "$LINES" -gt 1 ]; then
    SECOND_LINE=$(echo "$COMMIT_MSG" | sed -n '2p')
    if [ -n "$SECOND_LINE" ]; then
        error "La seconda riga deve essere vuota (separa header e body)."
        exit 1
    fi
fi

# Verificare la lunghezza delle righe del body (max 100 caratteri)
if [ "$LINES" -gt 2 ]; then
    LINE_NUM=0
    while IFS= read -r line; do
        LINE_NUM=$((LINE_NUM + 1))
        if [ "$LINE_NUM" -gt 2 ] && [ ${#line} -gt 100 ]; then
            warn "Riga $LINE_NUM del body supera 100 caratteri (${#line})."
        fi
    done <<< "$COMMIT_MSG"
fi

# Verificare footer per BREAKING CHANGE
if echo "$COMMIT_MSG" | grep -q "BREAKING CHANGE:"; then
    if ! echo "$FIRST_LINE" | grep -q "!:"; then
        warn "BREAKING CHANGE nel body ma '!' mancante nel tipo. Considerare l'aggiunta."
    fi
fi

info "Messaggio di commit valido: $FIRST_LINE"
exit 0
```

### Hook commit-msg in Python con Validazione Regex Avanzata

```python
#!/usr/bin/env python3
"""Hook commit-msg con validazione Conventional Commits avanzata."""

import re
import sys
from pathlib import Path

# Configurazione
MAX_HEADER_LENGTH = 72
MAX_BODY_LINE_LENGTH = 100
VALID_TYPES = [
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert",
]
VALID_SCOPES = None  # None = qualsiasi scope accettato
# Per limitare: VALID_SCOPES = ["api", "auth", "core", "db", "ui"]

# Pattern per messaggi da escludere dalla validazione
SKIP_PATTERNS = [
    r"^Merge\s",
    r"^Revert\s",
    r"^fixup!\s",
    r"^squash!\s",
    r"^amend!\s",
    r"^WIP",
    r"^Initial commit$",
]

CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(?P<type>" + "|".join(VALID_TYPES) + r")"
    r"(?:\((?P<scope>[a-z0-9_/-]+)\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.+)$"
)


class CommitLintError:
    """Rappresenta un errore di validazione del commit."""

    def __init__(self, level: str, message: str):
        self.level = level  # "error" o "warning"
        self.message = message

    def __str__(self) -> str:
        prefix = "\033[0;31mERRORE\033[0m" if self.level == "error" else "\033[1;33mATTENZIONE\033[0m"
        return f"  {prefix}: {self.message}"


def validate_commit_message(msg: str) -> list[CommitLintError]:
    """Validare un messaggio di commit secondo Conventional Commits."""
    errors: list[CommitLintError] = []
    lines = msg.strip().split("\n")

    if not lines:
        errors.append(CommitLintError("error", "Messaggio di commit vuoto."))
        return errors

    header = lines[0]

    # Controllare se il messaggio deve essere escluso dalla validazione
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, header):
            return []

    # Validare il formato dell'header
    match = CONVENTIONAL_COMMIT_REGEX.match(header)
    if not match:
        errors.append(CommitLintError(
            "error",
            f"Header non conforme a Conventional Commits: \"{header}\""
        ))
        errors.append(CommitLintError(
            "error",
            f"Formato richiesto: <tipo>(<scope>): <descrizione>"
        ))
        errors.append(CommitLintError(
            "error",
            f"Tipi validi: {', '.join(VALID_TYPES)}"
        ))
        return errors

    # Validare lo scope se la lista è definita
    scope = match.group("scope")
    if VALID_SCOPES is not None and scope and scope not in VALID_SCOPES:
        errors.append(CommitLintError(
            "error",
            f"Scope \"{scope}\" non valido. Scopes permessi: {', '.join(VALID_SCOPES)}"
        ))

    # Validare la lunghezza dell'header
    if len(header) > MAX_HEADER_LENGTH:
        errors.append(CommitLintError(
            "error",
            f"Header troppo lungo ({len(header)} caratteri, max {MAX_HEADER_LENGTH})."
        ))

    # Validare la descrizione
    description = match.group("description")
    if description[0].isupper():
        errors.append(CommitLintError(
            "warning",
            "La descrizione dovrebbe iniziare con lettera minuscola."
        ))

    if description.endswith("."):
        errors.append(CommitLintError(
            "warning",
            "La descrizione non dovrebbe terminare con un punto."
        ))

    if len(description) < 3:
        errors.append(CommitLintError(
            "error",
            "La descrizione è troppo corta (minimo 3 caratteri)."
        ))

    # Validare la riga vuota tra header e body
    if len(lines) > 1 and lines[1].strip():
        errors.append(CommitLintError(
            "error",
            "La seconda riga deve essere vuota (separa header e body)."
        ))

    # Validare la lunghezza delle righe del body
    for i, line in enumerate(lines[2:], start=3):
        if len(line) > MAX_BODY_LINE_LENGTH:
            errors.append(CommitLintError(
                "warning",
                f"Riga {i} del body supera {MAX_BODY_LINE_LENGTH} caratteri ({len(line)})."
            ))

    # Verificare coerenza BREAKING CHANGE
    has_breaking_footer = any(
        line.startswith("BREAKING CHANGE:") or line.startswith("BREAKING-CHANGE:")
        for line in lines
    )
    has_breaking_marker = match.group("breaking") == "!"

    if has_breaking_footer and not has_breaking_marker:
        errors.append(CommitLintError(
            "warning",
            "BREAKING CHANGE nel footer ma '!' mancante nell'header."
        ))

    return errors


def main() -> int:
    """Entry point del hook."""
    if len(sys.argv) < 2:
        print("Uso: commit-msg <file-messaggio>", file=sys.stderr)
        return 1

    msg_file = Path(sys.argv[1])
    try:
        msg = msg_file.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError) as e:
        print(f"Impossibile leggere il file del messaggio: {e}", file=sys.stderr)
        return 1

    errors = validate_commit_message(msg)

    if not errors:
        header = msg.strip().split("\n")[0]
        print(f"\033[0;32mOK\033[0m: {header}")
        return 0

    print("\nValidazione messaggio di commit:")
    has_blocking = False
    for err in errors:
        print(str(err))
        if err.level == "error":
            has_blocking = True

    if has_blocking:
        print(f"\nUsare 'git commit --no-verify' per bypassare (sconsigliato).")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Automazione del Changelog e del Versionamento

I Conventional Commits abilitano l'automazione completa del ciclo di rilascio: dal calcolo automatico della versione alla generazione del changelog, fino alla creazione delle release su GitHub.

#### Strumenti per l'Automazione

| Strumento | Stato | Descrizione |
|-----------|-------|-------------|
| **release-please** | Attivo, raccomandato | Strumento di Google per GitHub. Crea PR di release con changelog automatico. |
| **semantic-release** | Attivo | Automazione completa: versione, changelog, pubblicazione npm/PyPI. |
| **standard-version** | **Deprecato** | Predecessore di release-please. Non usare per nuovi progetti. |
| **conventional-changelog** | Attivo | Libreria CLI per generare changelog da commit convenzionali. |
| **commitizen** | Attivo | CLI interattiva per comporre commit convenzionali con prompt guidati. |

#### Integrazione release-please con GitHub Actions

```yaml
# .github/workflows/release-please.yml
name: release-please
on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: node  # oppure: python, go, rust, etc.
          # token: ${{ secrets.RELEASE_PLEASE_TOKEN }}  # se serve un PAT
```

Quando si fa push su `main`, release-please analizza i commit convenzionali e crea automaticamente una pull request con il changelog aggiornato e il bump di versione appropriato. Al merge della PR, viene creata la release su GitHub con il tag corrispondente.

#### Flusso Completo: dal Commit alla Release

```
1. Sviluppatore fa commit con formato convenzionale
   │
   ▼
2. Hook commit-msg valida il formato localmente
   │
   ▼
3. Push al remote → CI/CD esegue validazione server-side
   │
   ▼
4. Merge su main → release-please analizza i commit
   │
   ▼
5. release-please crea PR di release con:
   ├── Bump della versione (package.json, pyproject.toml, etc.)
   ├── Aggiornamento CHANGELOG.md
   └── Tag di release calcolato da SemVer
   │
   ▼
6. Merge della PR di release → Tag e Release su GitHub
```

### Configurazione Commitlint Avanzata

Per progetti che richiedono regole di validazione specifiche, commitlint offre una configurazione granulare:

```javascript
// commitlint.config.mjs
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Tipi personalizzati
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert',
      'wip',     // Work in progress (solo su branch feature)
      'release', // Commit di release
    ]],

    // Scope obbligatorio per feat e fix
    'scope-empty': [1, 'never'],
    'scope-enum': [1, 'always', [
      'api', 'auth', 'core', 'db', 'ui', 'cli',
      'config', 'deps', 'docker', 'docs', 'infra',
    ]],

    // Lunghezze
    'header-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
    'footer-max-line-length': [2, 'always', 100],

    // Stile della descrizione
    'subject-case': [2, 'always', 'lower-case'],
    'subject-full-stop': [2, 'never', '.'],
    'subject-min-length': [2, 'always', 10],

    // Body e footer
    'body-leading-blank': [2, 'always'],
    'footer-leading-blank': [2, 'always'],

    // Tipo deve essere minuscolo
    'type-case': [2, 'always', 'lower-case'],
  },

  // Plugin personalizzati
  plugins: [
    {
      rules: {
        // Regola personalizzata: richiedere riferimento a issue per feat/fix
        'references-required': (parsed) => {
          const { type, footer } = parsed;
          if (['feat', 'fix'].includes(type)) {
            const hasReference = footer && /(?:Closes|Fixes|Refs)\s+#\d+/.test(footer);
            if (!hasReference) {
              return [false, 'feat e fix richiedono un riferimento a issue (Closes #123)'];
            }
          }
          return [true];
        },
      },
    },
  ],
};
```

### Commitizen: Commit Interattivi Guidati

**Commitizen** è uno strumento CLI che guida lo sviluppatore nella composizione di messaggi di commit convenzionali tramite prompt interattivi:

```bash
# Installazione
npm install -g commitizen
npm install -D cz-conventional-changelog

# Configurazione in package.json
# "config": {
#   "commitizen": {
#     "path": "cz-conventional-changelog"
#   }
# }

# Uso: al posto di "git commit", eseguire:
npx cz
# oppure, se installato globalmente:
git cz

# Output interattivo:
# ? Select the type of change: (Use arrow keys)
# ❯ feat:     A new feature
#   fix:      A bug fix
#   docs:     Documentation only changes
#   style:    Changes that do not affect meaning
#   refactor: A code change without fix or feature
#   perf:     A code change that improves performance
#   test:     Adding missing tests
```

Per Python, è disponibile `commitizen` tramite pip:

```bash
# Installazione
pip install commitizen

# Configurazione in pyproject.toml
# [tool.commitizen]
# name = "cz_conventional_commits"
# version = "1.0.0"
# tag_format = "v$version"

# Uso
cz commit

# Bump automatico della versione
cz bump
```

---

## Rilevamento di Segreti e Sicurezza negli Hook

### Il Problema della Fuoriuscita di Segreti

L'inserimento accidentale di credenziali nel codice sorgente è una delle vulnerabilità più comuni e pericolose. Una volta che un segreto viene committato, rimane nella cronologia Git anche se viene rimosso in un commit successivo. I Git hooks rappresentano la prima linea di difesa contro questa minaccia, intercettando i segreti prima che raggiungano il repository remoto.

### Gitleaks: Scanner di Segreti Veloce

**Gitleaks** è lo scanner di segreti open-source più utilizzato come pre-commit hook. Scritto in Go, è estremamente veloce e produce output in formato SARIF compatibile con GitHub Advanced Security.

```bash
# Installazione
# macOS
brew install gitleaks

# Linux
wget https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_linux_x64 -O gitleaks
chmod +x gitleaks && sudo mv gitleaks /usr/local/bin/

# Scansione dei file staged
gitleaks protect --staged --verbose

# Scansione dell'intera cronologia
gitleaks detect --verbose

# Scansione con report SARIF
gitleaks detect --report-format sarif --report-path gitleaks-report.sarif
```

#### Configurazione Personalizzata di Gitleaks

```toml
# .gitleaks.toml — Configurazione personalizzata per il progetto
title = "Gitleaks Config"

# Regole personalizzate per il progetto
[[rules]]
id = "custom-api-key"
description = "Rilevamento API key personalizzate"
regex = '''(?i)(MY_PROJECT_API_KEY|MY_PROJECT_SECRET)\s*[=:]\s*['"][^'"]{16,}['"]'''
tags = ["key", "custom"]

[[rules]]
id = "internal-service-token"
description = "Token per servizi interni"
regex = '''svc_[a-zA-Z0-9]{32,}'''
tags = ["token", "internal"]

# File e percorsi da escludere
[allowlist]
paths = [
    '''test/fixtures/.*''',
    '''docs/examples/.*''',
    '''\.env\.example''',
    '''\.env\.template''',
]

# Pattern da escludere (falsi positivi noti)
regexes = [
    '''EXAMPLE_KEY_DO_NOT_USE''',
    '''test-api-key-12345''',
    '''fake-secret-for-testing''',
]

# Commit specifici da escludere
commits = [
    "abc123def456",  # commit noto con falso positivo
]
```

#### Integrazione di Gitleaks con pre-commit Framework

```yaml
# .pre-commit-config.yaml — Aggiungere Gitleaks
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

### TruffleHog: Scansione Profonda con Verifica dei Segreti

**TruffleHog** si distingue da Gitleaks per la capacità di **verificare** se i segreti rilevati sono effettivamente attivi, testandoli contro le rispettive API. Questo riduce drasticamente i falsi positivi.

```bash
# Installazione
brew install trufflehog

# Scansione del repository locale
trufflehog git file://. --since-commit HEAD~10

# Scansione con verifica dei segreti (contatta le API)
trufflehog git file://. --only-verified

# Scansione di un repository GitHub
trufflehog github --repo https://github.com/org/repo --only-verified
```

### Strategia di Difesa a Più Livelli

La best practice per la protezione dai segreti prevede una strategia a più livelli, dove ogni livello copre le debolezze degli altri:

```
Livello 1: SVILUPPATORE
├── Pre-commit hook con Gitleaks (veloce, <1 secondo)
├── .gitignore configurato per escludere .env, *.pem, *.key
└── Editor con plugin di rilevamento segreti

Livello 2: CI/CD
├── TruffleHog in pipeline CI con --only-verified
├── GitHub Secret Scanning (se disponibile)
└── SARIF upload per dashboard centralizzata

Livello 3: SERVER
├── Pre-receive hook per scansione server-side
├── GitHub Advanced Security / GitLab Secret Detection
└── Alerting e rotazione automatica dei segreti esposti

Livello 4: MONITORAGGIO
├── Scansione periodica dell'intera cronologia
├── Audit dei segreti in .env condivisi
└── Rotazione programmata delle credenziali
```

### Hook Pre-commit per Rilevamento Segreti Personalizzato

Quando gli strumenti dedicati non sono disponibili, un hook personalizzato può fornire una protezione base:

```python
#!/usr/bin/env python3
"""Pre-commit hook per rilevamento segreti senza dipendenze esterne."""

import re
import subprocess
import sys
from pathlib import Path

# Pattern di segreti noti
SECRET_PATTERNS = [
    # AWS
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)aws_secret_access_key\s*[=:]\s*['\"][^'\"]{20,}", "AWS Secret Key"),

    # GitHub
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"ghs_[a-zA-Z0-9]{36}", "GitHub App Installation Token"),
    (r"ghu_[a-zA-Z0-9]{36}", "GitHub User-to-Server Token"),
    (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "GitHub Fine-Grained PAT"),

    # Generici
    (r"(?i)-----BEGIN\s+(RSA|DSA|EC|OPENSSH)?\s*PRIVATE\s+KEY-----", "Chiave privata"),
    (r"(?i)(api[_-]?key|api[_-]?secret|access[_-]?token)\s*[=:]\s*['\"][^'\"]{16,}", "API Key/Token generico"),
    (r"(?i)password\s*[=:]\s*['\"][^'\"]{8,}", "Password hardcoded"),

    # Database
    (r"(?i)(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@", "Connection string con credenziali"),

    # Slack, Stripe, etc.
    (r"xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}", "Slack Bot Token"),
    (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe Live Secret Key"),
    (r"rk_live_[a-zA-Z0-9]{24,}", "Stripe Live Restricted Key"),

    # JWT
    (r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "JSON Web Token"),
]

# File da ignorare
IGNORE_PATTERNS = [
    r"\.env\.example$",
    r"\.env\.template$",
    r"test/fixtures/",
    r"__snapshots__/",
    r"\.lock$",
    r"\.min\.js$",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"pnpm-lock\.yaml$",
]

def get_staged_files() -> list[str]:
    """Ottenere i file staged."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

def should_ignore(filepath: str) -> bool:
    """Verificare se un file deve essere ignorato."""
    return any(re.search(p, filepath) for p in IGNORE_PATTERNS)

def scan_file(filepath: str) -> list[tuple[int, str, str]]:
    """Scansionare un file per segreti. Restituisce [(riga, match, descrizione)]."""
    findings = []
    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(content.split("\n"), 1):
            # Ignorare commenti e righe commentate
            stripped = line.strip()
            if stripped.startswith(("#", "//", "/*", "*", "<!--")):
                continue
            for pattern, description in SECRET_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    # Mascherare il segreto trovato nell'output
                    secret = match.group()
                    masked = secret[:8] + "..." + secret[-4:] if len(secret) > 16 else "***"
                    findings.append((i, masked, description))
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        pass
    return findings

def main() -> int:
    """Entry point."""
    files = get_staged_files()
    if not files:
        return 0

    all_findings: dict[str, list[tuple[int, str, str]]] = {}
    for f in files:
        if should_ignore(f):
            continue
        findings = scan_file(f)
        if findings:
            all_findings[f] = findings

    if not all_findings:
        print("\033[0;32mNessun segreto rilevato nei file staged.\033[0m")
        return 0

    print("\n\033[0;31m" + "=" * 60)
    print("  SEGRETI RILEVATI NEI FILE STAGED!")
    print("=" * 60 + "\033[0m\n")

    for filepath, findings in all_findings.items():
        print(f"  \033[1m{filepath}\033[0m")
        for line_num, masked, description in findings:
            print(f"    Riga {line_num}: {description} ({masked})")
        print()

    print("\033[0;31mCommit bloccato.\033[0m Rimuovere i segreti prima di committare.")
    print("Usare variabili d'ambiente o un secret manager.")
    print("\nPer bypassare (sconsigliato): git commit --no-verify")
    return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## Integrazione con CI/CD

### Perché Replicare gli Hook nella CI

I Git hooks client-side possono essere bypassati con `--no-verify`. Per questo motivo, i controlli critici devono essere replicati nella pipeline CI/CD, che funge da rete di sicurezza definitiva. La CI non può essere aggirata dallo sviluppatore e fornisce enforcement centralizzato delle policy del team.

La strategia raccomandata è:

| Controllo | Hook Client-Side | CI/CD | Motivazione |
|-----------|-----------------|-------|-------------|
| Formattazione codice | pre-commit | Sì | Feedback istantaneo + enforcement |
| Linting | pre-commit | Sì | Feedback istantaneo + enforcement |
| Type checking | pre-commit (opzionale) | Sì | Può essere lento localmente |
| Test unitari | pre-push | Sì | Troppo lento per pre-commit |
| Test integrazione | No | Sì | Richiede infrastruttura |
| Secret scanning | pre-commit | Sì | Difesa a più livelli |
| Validazione commit msg | commit-msg | Sì | Enforcement server-side |
| Analisi sicurezza | No | Sì | Richiede strumenti complessi |
| Build completa | No | Sì | Richiede ambiente controllato |

### Pre-commit Framework in GitHub Actions

Il framework pre-commit offre una GitHub Action ufficiale per eseguire gli stessi hook della configurazione locale nella pipeline CI:

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit Checks
on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # Cache degli hook pre-commit per velocizzare le esecuzioni successive
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - uses: pre-commit/action@v3.0.1
        # Per eseguire solo sui file modificati nella PR:
        # with:
        #   extra_args: --files $(git diff --name-only ${{ github.event.pull_request.base.sha }})
```

### Validazione Commit Messages nella CI

Per garantire che tutti i commit in una PR rispettino il formato Conventional Commits, anche se l'hook commit-msg locale è stato bypassato:

```yaml
# .github/workflows/commitlint.yml
name: Commit Message Lint
on:
  pull_request:
    branches: [main, develop]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necessario per accedere alla cronologia dei commit

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - run: npm install @commitlint/cli @commitlint/config-conventional

      # Validare tutti i commit nella PR
      - run: npx commitlint --from ${{ github.event.pull_request.base.sha }} --to HEAD --verbose
```

### Secret Scanning nella CI

```yaml
# .github/workflows/secrets-scan.yml
name: Secret Scanning
on:
  pull_request:
  push:
    branches: [main]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}  # opzionale per report SARIF

  trufflehog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: TruffleHog Scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified
```

### Pipeline CI Completa con Hook Replicati

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate
on:
  pull_request:
    branches: [main, develop]

concurrency:
  group: quality-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # Job 1: Lint e Format (replica pre-commit hook)
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm format:check
      - run: pnpm tsc --noEmit

  # Job 2: Test (replica pre-push hook)
  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm test -- --coverage
      - name: Verificare copertura minima
        run: |
          COVERAGE=$(pnpm test -- --coverage --coverageReporters=text-summary | grep "Statements" | awk '{print $3}' | tr -d '%')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Copertura insufficiente: ${COVERAGE}% (minimo 80%)"
            exit 1
          fi

  # Job 3: Commit Messages (replica commit-msg hook)
  commit-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm install @commitlint/cli @commitlint/config-conventional
      - run: npx commitlint --from ${{ github.event.pull_request.base.sha }} --to HEAD

  # Job 4: Security (replica secret scanning hook)
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Hook per Monorepo

### Sfide degli Hook nei Monorepo

I monorepo presentano sfide uniche per i Git hooks perché contengono molteplici progetti, spesso in linguaggi diversi, all'interno di un unico repository. Eseguire tutti gli hook su ogni commit, indipendentemente da quali file sono stati modificati, risulta in tempi di commit inaccettabili e in feedback irrilevante.

La soluzione è implementare **hook selettivi** che eseguano solo i controlli pertinenti ai file effettivamente modificati.

### Lefthook per Monorepo

Lefthook è particolarmente adatto ai monorepo grazie al supporto nativo per il parallelismo e i glob pattern:

```yaml
# lefthook.yml — Configurazione per monorepo
pre-commit:
  parallel: true
  commands:
    # Frontend (React/TypeScript)
    frontend-lint:
      root: "packages/frontend/"
      glob: "*.{ts,tsx,js,jsx}"
      run: cd packages/frontend && npx eslint --fix {staged_files}
      stage_fixed: true

    frontend-format:
      root: "packages/frontend/"
      glob: "*.{ts,tsx,js,jsx,css,json}"
      run: cd packages/frontend && npx prettier --write {staged_files}
      stage_fixed: true

    frontend-types:
      root: "packages/frontend/"
      glob: "*.{ts,tsx}"
      run: cd packages/frontend && npx tsc --noEmit
      # Eseguire solo se file TS sono stati modificati
      skip:
        - merge
        - rebase

    # Backend (Python)
    backend-lint:
      root: "packages/backend/"
      glob: "*.py"
      run: cd packages/backend && ruff check --fix {staged_files}
      stage_fixed: true

    backend-format:
      root: "packages/backend/"
      glob: "*.py"
      run: cd packages/backend && black {staged_files}
      stage_fixed: true

    backend-types:
      root: "packages/backend/"
      glob: "*.py"
      run: cd packages/backend && mypy {staged_files}

    # Infrastruttura (Terraform)
    infra-fmt:
      root: "infra/"
      glob: "*.tf"
      run: cd infra && terraform fmt {staged_files}
      stage_fixed: true

    infra-validate:
      root: "infra/"
      glob: "*.tf"
      run: cd infra && terraform validate

    # Sicurezza globale
    secrets:
      run: gitleaks protect --staged --verbose

commit-msg:
  commands:
    commitlint:
      run: npx commitlint --edit {1}

pre-push:
  parallel: true
  commands:
    frontend-test:
      root: "packages/frontend/"
      run: cd packages/frontend && npm test
      # Eseguire solo se file frontend sono cambiati dall'ultimo push
      skip:
        - merge

    backend-test:
      root: "packages/backend/"
      run: cd packages/backend && python -m pytest
      skip:
        - merge
```

### Script Bash per Hook Selettivi in Monorepo

Per monorepo senza framework dedicato, un approccio con script bash che rileva automaticamente quali pacchetti sono stati modificati:

```bash
#!/bin/bash
# .githooks/pre-commit — Hook selettivo per monorepo
set -euo pipefail

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[HOOK]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; }

# Ottenere i file staged
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED_FILES" ]; then
    info "Nessun file staged. Niente da controllare."
    exit 0
fi

EXIT_CODE=0

# Determinare quali pacchetti sono stati modificati
MODIFIED_PACKAGES=$(echo "$STAGED_FILES" | grep "^packages/" | cut -d/ -f2 | sort -u)

# Eseguire controlli per ogni pacchetto modificato
for pkg in $MODIFIED_PACKAGES; do
    PKG_DIR="packages/$pkg"
    if [ ! -d "$PKG_DIR" ]; then
        continue
    fi

    info "Controllo pacchetto: $pkg"

    # Ottenere i file staged di questo pacchetto
    PKG_FILES=$(echo "$STAGED_FILES" | grep "^$PKG_DIR/")

    # Rilevare il linguaggio del pacchetto
    if [ -f "$PKG_DIR/package.json" ]; then
        # Node.js / TypeScript
        JS_FILES=$(echo "$PKG_FILES" | grep -E '\.(js|jsx|ts|tsx)$' || true)
        if [ -n "$JS_FILES" ]; then
            info "  ESLint su $pkg..."
            if ! (cd "$PKG_DIR" && echo "$JS_FILES" | sed "s|$PKG_DIR/||g" | xargs npx eslint --fix 2>/dev/null); then
                fail "  ESLint fallito per $pkg"
                EXIT_CODE=1
            else
                ok "  ESLint $pkg"
            fi
        fi

    elif [ -f "$PKG_DIR/pyproject.toml" ] || [ -f "$PKG_DIR/setup.py" ]; then
        # Python
        PY_FILES=$(echo "$PKG_FILES" | grep -E '\.py$' || true)
        if [ -n "$PY_FILES" ]; then
            info "  Ruff su $pkg..."
            if ! (cd "$PKG_DIR" && echo "$PY_FILES" | sed "s|$PKG_DIR/||g" | xargs ruff check --fix 2>/dev/null); then
                fail "  Ruff fallito per $pkg"
                EXIT_CODE=1
            else
                ok "  Ruff $pkg"
            fi
        fi

    elif [ -f "$PKG_DIR/go.mod" ]; then
        # Go
        GO_FILES=$(echo "$PKG_FILES" | grep -E '\.go$' || true)
        if [ -n "$GO_FILES" ]; then
            info "  gofmt su $pkg..."
            if ! (cd "$PKG_DIR" && gofmt -l -w $GO_FILES 2>/dev/null); then
                fail "  gofmt fallito per $pkg"
                EXIT_CODE=1
            else
                ok "  gofmt $pkg"
            fi
        fi
    fi
done

# Controlli globali (non specifici di pacchetto)
ROOT_FILES=$(echo "$STAGED_FILES" | grep -v "^packages/" || true)
if [ -n "$ROOT_FILES" ]; then
    # YAML validation
    YAML_FILES=$(echo "$ROOT_FILES" | grep -E '\.(yaml|yml)$' || true)
    if [ -n "$YAML_FILES" ]; then
        info "Validazione YAML..."
        for f in $YAML_FILES; do
            if ! python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null; then
                fail "YAML non valido: $f"
                EXIT_CODE=1
            fi
        done
    fi
fi

# Secret scanning globale
info "Scansione segreti..."
if command -v gitleaks &>/dev/null; then
    if ! gitleaks protect --staged --no-banner 2>/dev/null; then
        fail "Segreti rilevati! Rimuovere prima di committare."
        EXIT_CODE=1
    else
        ok "Nessun segreto rilevato."
    fi
fi

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    fail "Pre-commit fallito. Correggere gli errori sopra."
    echo "  Usare 'git commit --no-verify' per bypassare (sconsigliato)."
fi

exit $EXIT_CODE
```

### Mookme: Hook Manager Dedicato per Monorepo

**Mookme** è un gestore di hook progettato specificamente per i monorepo. Ogni sotto-progetto definisce i propri hook in una directory `.hooks/`, e Mookme esegue solo gli hook relativi ai file modificati:

```bash
# Installazione
npm install -g @mookme/mookme

# Inizializzazione
mookme init

# Struttura del monorepo con Mookme:
# monorepo/
# ├── .hooks/              ← Hook globali
# │   └── pre-commit.json
# ├── packages/
# │   ├── frontend/
# │   │   └── .hooks/      ← Hook specifici frontend
# │   │       └── pre-commit.json
# │   └── backend/
# │       └── .hooks/      ← Hook specifici backend
# │           └── pre-commit.json
```

```json
// packages/frontend/.hooks/pre-commit.json
{
  "steps": [
    {
      "name": "ESLint",
      "command": "npx eslint --fix {staged_files}",
      "onlyOn": "**/*.{ts,tsx,js,jsx}"
    },
    {
      "name": "Prettier",
      "command": "npx prettier --write {staged_files}",
      "onlyOn": "**/*.{ts,tsx,css,json}"
    },
    {
      "name": "Type Check",
      "command": "npx tsc --noEmit"
    }
  ]
}
```

---

## Confronto tra Framework di Gestione Hook

### Tabella Comparativa Dettagliata

| Caratteristica | **pre-commit** | **Husky** | **Lefthook** | **Mookme** |
|---------------|---------------|-----------|------------|-----------|
| **Linguaggio** | Python | JavaScript | Go | JavaScript |
| **Dimensione** | ~5 MB (con env) | ~2 kB (gzip) | ~3 MB (binario) | ~1 MB |
| **Dipendenze runtime** | Python 3.x | Node.js | Nessuna (binario) | Node.js |
| **Esecuzione parallela** | No (sequenziale) | No (sequenziale) | Sì (nativo) | Sì |
| **Isolamento ambienti** | Sì (virtualenv per hook) | No | No | No |
| **Multi-linguaggio** | Sì (eccellente) | Solo Node.js | Sì | Solo Node.js |
| **Ecosistema hook** | Vastissimo (1000+ hook) | Limitato | Limitato | Limitato |
| **Monorepo** | Parziale | Parziale | Buono | Ottimo |
| **Stage automatico** | Sì (fix & re-add) | Via lint-staged | Sì (stage_fixed) | Sì |
| **Configurazione** | YAML | Shell scripts | YAML | JSON |
| **Cache hook** | Sì | N/A | Sì | No |
| **CI/CD Action** | Ufficiale | Non ufficiale | Non ufficiale | No |
| **NPM downloads/sett.** | N/A (pip) | ~7M | ~200k | ~5k |
| **Hook predefiniti** | 1000+ da repo esterni | Nessuno | Nessuno | Nessuno |
| **Aggiornamento auto** | `pre-commit autoupdate` | Manuale | Manuale | Manuale |

### Quando Usare Quale Framework

#### Pre-commit Framework (Python)

**Scegliere quando:**
- Il progetto è multi-linguaggio (Python + JS + Go + Terraform + ...)
- Si desidera il più ampio ecosistema di hook predefiniti
- Si necessita di isolamento degli ambienti (ogni hook in un virtualenv separato)
- Il team include sviluppatori che non usano Node.js
- Si vuole la stessa configurazione in locale e nella CI (via pre-commit/action)

**Evitare quando:**
- Il progetto è puramente JavaScript/TypeScript
- La velocità di esecuzione è critica (sequenziale, non parallelo)
- Non si vuole dipendere da Python nell'ambiente di sviluppo

#### Husky (JavaScript)

**Scegliere quando:**
- Il progetto è prevalentemente JavaScript/TypeScript
- Si vuole una configurazione minimale e familiare per sviluppatori frontend
- Si usa già lint-staged per il linting dei file staged
- Il team è composto principalmente da sviluppatori Node.js
- Si desidera la soluzione più diffusa e documentata nell'ecosistema JS

**Evitare quando:**
- Il progetto non usa Node.js
- Si necessita di esecuzione parallela degli hook
- Il progetto è un monorepo complesso multi-linguaggio

#### Lefthook (Go)

**Scegliere quando:**
- La performance è prioritaria (esecuzione parallela nativa)
- Il progetto è un monorepo con frontend, backend e infra
- Non si vuole una dipendenza runtime (binario standalone)
- Si necessita di configurazione dichiarativa avanzata
- Si desidera sostituire Husky + lint-staged con un singolo strumento

**Evitare quando:**
- Si necessita di un ampio ecosistema di hook predefiniti
- Il team è abituato a Husky e non vuole cambiare
- Si ha bisogno di isolamento degli ambienti per gli hook

### Migrazione tra Framework

#### Da Husky a Lefthook

```bash
# 1. Disinstallare Husky
npm uninstall husky
rm -rf .husky

# 2. Rimuovere "prepare": "husky" da package.json

# 3. Installare Lefthook
npm install lefthook --save-dev

# 4. Creare lefthook.yml (equivalente della configurazione Husky)
cat > lefthook.yml << 'EOF'
pre-commit:
  parallel: true
  commands:
    lint-staged:
      glob: "*.{js,jsx,ts,tsx}"
      run: npx eslint --fix {staged_files} && npx prettier --write {staged_files}
      stage_fixed: true

commit-msg:
  commands:
    commitlint:
      run: npx commitlint --edit {1}

pre-push:
  commands:
    test:
      run: npm test
EOF

# 5. Installare gli hooks
npx lefthook install

# 6. Aggiungere a package.json
# "postinstall": "lefthook install"
```

#### Da pre-commit a Lefthook

```bash
# 1. Disinstallare pre-commit
pre-commit uninstall
# Mantenere .pre-commit-config.yaml come riferimento

# 2. Tradurre la configurazione
# Ogni hook in .pre-commit-config.yaml diventa un comando in lefthook.yml

# Esempio: da pre-commit-config.yaml
# repos:
#   - repo: https://github.com/psf/black
#     rev: 24.1.1
#     hooks:
#       - id: black

# A lefthook.yml:
# pre-commit:
#   commands:
#     black:
#       glob: "*.py"
#       run: black {staged_files}
#       stage_fixed: true
```

---

## Pattern Avanzati per Hook

### Hook con Test Selettivi Basati sulle Modifiche

Un pattern avanzato è l'esecuzione di test solo per i moduli effettivamente modificati, riducendo drasticamente il tempo di feedback:

```bash
#!/bin/bash
# .git/hooks/pre-push — Test selettivi basati sui file modificati

set -euo pipefail

REMOTE=$1
URL=$2

# Trovare i file modificati rispetto al branch target
TARGET_BRANCH="origin/main"
CHANGED_FILES=$(git diff --name-only "$TARGET_BRANCH"...HEAD 2>/dev/null || git diff --name-only HEAD~5...HEAD)

echo "File modificati:"
echo "$CHANGED_FILES" | head -20

# Determinare quali test eseguire
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false

# Se i file sorgente sono cambiati, eseguire test unitari
if echo "$CHANGED_FILES" | grep -qE "^src/"; then
    RUN_UNIT=true
fi

# Se i file API sono cambiati, eseguire test di integrazione
if echo "$CHANGED_FILES" | grep -qE "^src/(api|routes|controllers)/"; then
    RUN_INTEGRATION=true
fi

# Se i file di configurazione critica sono cambiati, eseguire tutto
if echo "$CHANGED_FILES" | grep -qE "^(package\.json|tsconfig\.json|docker-compose|\.env)"; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
fi

# Se i test E2E stessi sono cambiati, eseguire E2E
if echo "$CHANGED_FILES" | grep -qE "^(e2e|cypress|playwright)/"; then
    RUN_E2E=true
fi

EXIT_CODE=0

if $RUN_UNIT; then
    echo "=> Esecuzione test unitari..."
    npm run test:unit || EXIT_CODE=1
fi

if $RUN_INTEGRATION; then
    echo "=> Esecuzione test di integrazione..."
    npm run test:integration || EXIT_CODE=1
fi

if $RUN_E2E; then
    echo "=> Esecuzione test E2E..."
    npm run test:e2e || EXIT_CODE=1
fi

if ! $RUN_UNIT && ! $RUN_INTEGRATION && ! $RUN_E2E; then
    echo "Nessun test necessario per le modifiche correnti."
fi

exit $EXIT_CODE
```

### Hook con Cache per Performance

```bash
#!/bin/bash
# Pre-commit hook con cache basata su hash dei file
# Evita di ri-eseguire controlli su file non modificati

set -euo pipefail

CACHE_DIR=".git/hook-cache"
mkdir -p "$CACHE_DIR"

check_cached() {
    local file=$1
    local tool=$2
    local current_hash
    current_hash=$(git hash-object "$file" 2>/dev/null || echo "none")
    local cache_file="$CACHE_DIR/${tool}_$(echo "$file" | md5sum | cut -d' ' -f1)"

    if [ -f "$cache_file" ] && [ "$(cat "$cache_file")" = "$current_hash" ]; then
        return 0  # Già controllato con lo stesso contenuto
    fi
    return 1  # Necessita controllo
}

update_cache() {
    local file=$1
    local tool=$2
    local current_hash
    current_hash=$(git hash-object "$file" 2>/dev/null || echo "none")
    local cache_file="$CACHE_DIR/${tool}_$(echo "$file" | md5sum | cut -d' ' -f1)"
    echo "$current_hash" > "$cache_file"
}

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
EXIT_CODE=0

for file in $STAGED_FILES; do
    case "$file" in
        *.py)
            if ! check_cached "$file" "ruff"; then
                if ruff check "$file" 2>/dev/null; then
                    update_cache "$file" "ruff"
                else
                    EXIT_CODE=1
                fi
            fi
            ;;
        *.ts|*.tsx|*.js|*.jsx)
            if ! check_cached "$file" "eslint"; then
                if npx eslint "$file" 2>/dev/null; then
                    update_cache "$file" "eslint"
                else
                    EXIT_CODE=1
                fi
            fi
            ;;
    esac
done

exit $EXIT_CODE
```

### Hook con Timeout per Prevenire Blocchi

```bash
#!/bin/bash
# Pre-commit hook con timeout per prevenire blocchi infiniti

set -euo pipefail

TIMEOUT_SECONDS=30

run_with_timeout() {
    local name=$1
    shift
    local cmd="$@"

    echo "Esecuzione: $name (timeout: ${TIMEOUT_SECONDS}s)..."

    if timeout "$TIMEOUT_SECONDS" bash -c "$cmd" 2>&1; then
        echo "  OK: $name completato."
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo "  TIMEOUT: $name ha superato ${TIMEOUT_SECONDS}s. Skippato."
            return 0  # Non bloccare per timeout, solo avvertire
        else
            echo "  FALLITO: $name (exit code: $exit_code)"
            return 1
        fi
    fi
}

EXIT_CODE=0

run_with_timeout "ESLint" "npx eslint --fix \$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|ts|tsx|jsx)$' | tr '\n' ' ')" || EXIT_CODE=1

run_with_timeout "Prettier" "npx prettier --check \$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|ts|tsx|jsx|css|json|md)$' | tr '\n' ' ')" || EXIT_CODE=1

run_with_timeout "Secret Scan" "gitleaks protect --staged --no-banner" || EXIT_CODE=1

exit $EXIT_CODE
```

### Hook con Bypass Condizionale

Un pattern utile per permettere bypass parziali senza disabilitare tutti i controlli:

```bash
#!/bin/bash
# Pre-commit hook con bypass selettivo via variabili d'ambiente

set -euo pipefail

# Variabili di bypass:
# SKIP_LINT=1 git commit -m "..."      → salta il linting
# SKIP_FORMAT=1 git commit -m "..."    → salta la formattazione
# SKIP_TESTS=1 git commit -m "..."     → salta i test
# SKIP_SECRETS=1 git commit -m "..."   → salta scansione segreti (sconsigliato)

EXIT_CODE=0

# Linting
if [ "${SKIP_LINT:-0}" != "1" ]; then
    echo "=> Linting..."
    STAGED_JS=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|ts|tsx|jsx)$' || true)
    if [ -n "$STAGED_JS" ]; then
        echo "$STAGED_JS" | xargs npx eslint --fix || EXIT_CODE=1
    fi
else
    echo "=> Linting: SKIPPATO (SKIP_LINT=1)"
fi

# Formattazione
if [ "${SKIP_FORMAT:-0}" != "1" ]; then
    echo "=> Formattazione..."
    STAGED_ALL=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|ts|tsx|jsx|css|json|md)$' || true)
    if [ -n "$STAGED_ALL" ]; then
        echo "$STAGED_ALL" | xargs npx prettier --write || EXIT_CODE=1
        echo "$STAGED_ALL" | xargs git add  # Re-stage file formattati
    fi
else
    echo "=> Formattazione: SKIPPATA (SKIP_FORMAT=1)"
fi

# Test rapidi
if [ "${SKIP_TESTS:-0}" != "1" ]; then
    echo "=> Test rapidi..."
    npm run test:fast 2>/dev/null || EXIT_CODE=1
else
    echo "=> Test: SKIPPATI (SKIP_TESTS=1)"
fi

# Scansione segreti (MAI skippare in produzione)
if [ "${SKIP_SECRETS:-0}" != "1" ]; then
    echo "=> Scansione segreti..."
    gitleaks protect --staged --no-banner 2>/dev/null || EXIT_CODE=1
else
    echo "=> Scansione segreti: SKIPPATA (SKIP_SECRETS=1)"
    echo "   ATTENZIONE: Scansione segreti disabilitata. Usare con cautela."
fi

exit $EXIT_CODE
```

---

## Hook in Ambienti Enterprise e su Piattaforme Git

### GitLab Server Hooks

GitLab supporta hook server-side sia globali (applicati a tutti i repository dell'istanza) sia per singolo progetto. A partire da GitLab 15.11+, la configurazione avviene tramite il comando `gitaly`:

```bash
# Struttura delle directory per hook GitLab
# Per progetto (richiede accesso al filesystem del server):
/var/opt/gitlab/git-data/repositories/@hashed/<hash>/<hash>.git/custom_hooks/
├── pre-receive.d/
│   ├── 01-check-commit-messages
│   └── 02-check-file-sizes
├── update.d/
│   └── 01-check-branch-names
└── post-receive.d/
    └── 01-notify-slack

# Hook globali (applicati a tutti i repository):
/opt/gitlab/embedded/service/gitlab-shell/hooks/
```

#### Esempio di Hook GitLab Pre-receive

```bash
#!/bin/bash
# custom_hooks/pre-receive.d/01-enforce-policy
# Hook GitLab per enforcement delle policy aziendali

set -euo pipefail

# GitLab imposta variabili d'ambiente aggiuntive:
# GL_ID           — ID dell'utente (es. "user-123")
# GL_USERNAME     — Username GitLab
# GL_REPOSITORY   — Path del repository
# GL_PROJECT_PATH — Path del progetto (es. "group/subgroup/project")
# GL_PROTOCOL     — Protocollo (ssh, http, web)

echo "Policy check per utente: $GL_USERNAME"
echo "Repository: ${GL_PROJECT_PATH:-unknown}"

while read oldrev newrev refname; do
    BRANCH=$(echo "$refname" | sed 's|refs/heads/||')

    # Policy 1: Solo maintainer possono pushare su main
    if [ "$BRANCH" = "main" ]; then
        # In un ambiente reale, verificare contro un servizio di autorizzazione
        echo "ERRORE: Push diretto su main non consentito."
        echo "Creare una Merge Request per integrare le modifiche."
        exit 1
    fi

    # Policy 2: Branch naming convention
    BRANCH_PATTERN="^(main|develop|feature/.+|bugfix/.+|hotfix/.+|release/[0-9]+\.[0-9]+)$"
    if [ "$oldrev" = "0000000000000000000000000000000000000000" ]; then
        if ! echo "$BRANCH" | grep -qE "$BRANCH_PATTERN"; then
            echo "ERRORE: Nome branch '$BRANCH' non conforme."
            echo "Pattern accettati: feature/*, bugfix/*, hotfix/*, release/X.Y"
            exit 1
        fi
    fi

    # Policy 3: Dimensione massima commit
    if [ "$newrev" != "0000000000000000000000000000000000000000" ] && \
       [ "$oldrev" != "0000000000000000000000000000000000000000" ]; then
        MAX_DIFF_SIZE=10485760  # 10 MB di diff
        DIFF_SIZE=$(git diff --stat "$oldrev..$newrev" | tail -1 | awk '{print $4+$6}')
        if [ "${DIFF_SIZE:-0}" -gt "$MAX_DIFF_SIZE" ]; then
            echo "ERRORE: Push troppo grande. Suddividere in commit più piccoli."
            exit 1
        fi
    fi
done

exit 0
```

### GitHub Enterprise Server Pre-receive Hooks

GitHub Enterprise Server supporta hook pre-receive configurabili tramite l'interfaccia di amministrazione. Gli hook vengono eseguiti in un ambiente Docker isolato con un timeout fisso di 5 secondi (condiviso tra tutti gli hook).

```bash
#!/bin/bash
# Pre-receive hook per GitHub Enterprise Server
# Vincoli: timeout 5 secondi, ambiente isolato, nessuna chiamata API esterna

while read oldrev newrev refname; do
    # Non verificare le cancellazioni di branch
    if [ "$newrev" = "0000000000000000000000000000000000000000" ]; then
        continue
    fi

    BRANCH=$(echo "$refname" | sed 's|refs/heads/||')

    # Verificare Conventional Commits (veloce, senza dipendenze)
    if [ "$oldrev" != "0000000000000000000000000000000000000000" ]; then
        PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
        BAD=$(git log --format="%s" "$oldrev..$newrev" | grep -cvE "$PATTERN" || true)
        if [ "$BAD" -gt 0 ]; then
            echo "::error::Commit non conformi a Conventional Commits rilevati."
            exit 1
        fi
    fi

    # Bloccare file binari grandi (senza Git LFS)
    if [ "$oldrev" = "0000000000000000000000000000000000000000" ]; then
        FILES=$(git diff-tree -r --name-only "$newrev")
    else
        FILES=$(git diff --name-only "$oldrev" "$newrev")
    fi

    for f in $FILES; do
        # Controllare estensioni di file binari grandi
        if echo "$f" | grep -qiE '\.(zip|tar|gz|rar|7z|iso|dmg|exe|dll|so|dylib|jar|war|mp4|avi|mov)$'; then
            SIZE=$(git cat-file -s "$newrev:$f" 2>/dev/null || echo 0)
            if [ "$SIZE" -gt 5242880 ]; then  # 5 MB
                echo "::error::File binario troppo grande: $f ($(($SIZE / 1024 / 1024)) MB). Usare Git LFS."
                exit 1
            fi
        fi
    done
done

exit 0
```

### Gitea e Forgejo: Hook Server-Side

Gitea (e il suo fork Forgejo) supportano hook server-side simili a GitLab, con la possibilità di configurarli tramite l'interfaccia web o direttamente nel filesystem:

```bash
# Percorso degli hooks in Gitea:
# /data/gitea/repositories/<owner>/<repo>.git/hooks/
# oppure, per hook personalizzati:
# /data/gitea/repositories/<owner>/<repo>.git/hooks/pre-receive.d/

# Gitea imposta variabili d'ambiente specifiche:
# GITEA_REPO_NAME      — Nome del repository
# GITEA_REPO_USER_NAME — Username del proprietario
# GITEA_PUSHER_NAME    — Username di chi sta pushando
# GITEA_PUSHER_EMAIL   — Email di chi sta pushando
```

### Timeout e Performance degli Hook Server-Side

Gli hook server-side devono rispettare vincoli di performance rigorosi per non degradare l'esperienza dell'utente:

| Piattaforma | Timeout | Note |
|-------------|---------|------|
| **GitHub Enterprise** | 5 secondi (totale) | Condiviso tra tutti gli hook. Nessuna chiamata API esterna. |
| **GitLab** | 10 secondi (default) | Configurabile in gitlab.rb. |
| **Gitea/Forgejo** | Configurabile | Default generoso, ma da limitare in produzione. |
| **Bitbucket Server** | 30 secondi (default) | Configurabile per amministratori. |
| **Self-hosted (bare)** | Nessun limite | Responsabilità dell'amministratore. Impostare `ulimit`. |

**Regole di performance per hook server-side:**

1. Non effettuare chiamate a servizi esterni (API, webhook)
2. Non eseguire build o test completi
3. Limitarsi a verifiche basate su dati Git (commit, diff, ref)
4. Usare `git rev-list`, `git log`, `git diff-tree` per efficienza
5. Evitare `git diff` su diff molto grandi — usare `--stat` o `--name-only`
6. Se necessario elaborazione complessa, delegare a un servizio asincrono via post-receive

---

## Debugging e Diagnosi Avanzata degli Hook

### Variabili di Trace di Git

Git fornisce variabili d'ambiente per il debugging dettagliato dell'esecuzione degli hook e di altre operazioni interne:

```bash
# Attivare il trace completo di Git
GIT_TRACE=1 git commit -m "test: debug hook"

# Trace specifico per le performance (tempo di esecuzione)
GIT_TRACE_PERFORMANCE=1 git commit -m "test: perf trace"

# Trace della risoluzione dei path
GIT_TRACE_SETUP=1 git commit -m "test: setup trace"

# Combinare più trace per diagnosi completa
GIT_TRACE=2 GIT_TRACE_PERFORMANCE=1 GIT_TRACE_SETUP=1 git commit -m "test: full debug"

# Trace dell'esecuzione dei comandi Git con output su file
GIT_TRACE=1 git commit -m "test" 2>/tmp/git-trace.log
cat /tmp/git-trace.log
```

### Tecnica di Debug con set -x

Aggiungere `set -x` all'inizio di un hook Bash per stampare ogni comando prima della sua esecuzione:

```bash
#!/bin/bash
# .git/hooks/pre-commit — Versione di debug
set -x  # Stampa ogni comando prima dell'esecuzione
set -euo pipefail

# Stampare informazioni sull'ambiente
echo "=== DEBUG INFO ==="
echo "PATH: $PATH"
echo "PWD: $(pwd)"
echo "GIT_DIR: ${GIT_DIR:-non impostato}"
echo "GIT_WORK_TREE: ${GIT_WORK_TREE:-non impostato}"
echo "GIT_INDEX_FILE: ${GIT_INDEX_FILE:-non impostato}"
echo "Shell: $SHELL"
echo "Bash version: $BASH_VERSION"
echo "Node version: $(node --version 2>/dev/null || echo 'non trovato')"
echo "Python version: $(python3 --version 2>/dev/null || echo 'non trovato')"
echo "================"

# Il resto dell'hook...
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
echo "File staged: $STAGED_FILES"

# Rimuovere set -x quando il debug è completato
```

### Esecuzione Manuale degli Hook

Per testare un hook senza eseguire un vero commit o push:

```bash
# Eseguire manualmente un pre-commit hook
.git/hooks/pre-commit

# Eseguire un commit-msg hook con un file di messaggio di test
echo "feat: test message" > /tmp/test-commit-msg
.git/hooks/commit-msg /tmp/test-commit-msg
echo "Exit code: $?"

# Eseguire un pre-push hook con input simulato
echo "refs/heads/main $(git rev-parse HEAD) refs/heads/main $(git rev-parse HEAD~1)" | \
    .git/hooks/pre-push origin https://github.com/user/repo.git

# Eseguire con variabili d'ambiente di Git
GIT_DIR=$(git rev-parse --git-dir) \
GIT_WORK_TREE=$(git rev-parse --show-toplevel) \
.git/hooks/pre-commit
```

### Diagnostica dei Problemi Comuni

#### Problema: Hook Non Trovato o Non Eseguito

```bash
# 1. Verificare che il file esista e sia eseguibile
ls -la .git/hooks/pre-commit
# Deve mostrare: -rwxr-xr-x

# 2. Verificare lo shebang
head -1 .git/hooks/pre-commit
# Deve essere: #!/bin/bash o #!/usr/bin/env python3

# 3. Verificare core.hooksPath
git config core.hooksPath
# Se impostato, gli hooks devono essere in quella directory

# 4. Verificare che non ci siano file .sample che sovrascrivono
ls .git/hooks/pre-commit*
# Se esiste pre-commit.sample MA NON pre-commit, il hook non è attivo

# 5. Verificare se un framework gestisce gli hooks
cat .git/hooks/pre-commit | head -5
# Potrebbe contenere: "# husky" o "# pre-commit" che indica gestione esterna
```

#### Problema: Hook Fallisce per PATH o Ambiente

```bash
# Il problema più comune: comandi non trovati nell'ambiente dell'hook
# Causa: l'hook viene eseguito con un PATH minimale

# Soluzione 1: Specificare il PATH completo all'inizio dell'hook
#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$HOME/.nvm/versions/node/v22/bin:$PATH"

# Soluzione 2: Usare il path assoluto per i comandi
/usr/local/bin/npx eslint .
/usr/bin/python3 -m pytest

# Soluzione 3: Source del profilo (non sempre raccomandato)
#!/bin/bash
source ~/.bashrc 2>/dev/null || true
# oppure per nvm:
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
```

#### Problema: Line Endings Windows (CRLF)

```bash
# Sintomo: /bin/bash^M: bad interpreter: No such file or directory
# Causa: hook creato su Windows con line endings CRLF

# Soluzione: convertire a LF
sed -i 's/\r$//' .git/hooks/pre-commit

# Oppure con dos2unix
dos2unix .git/hooks/pre-commit

# Prevenzione: configurare Git per gestire i line endings
git config --global core.autocrlf input  # Linux/macOS
git config --global core.autocrlf true   # Windows
```

#### Problema: Hook Interattivo che Blocca la CI

```bash
# Sintomo: hook con "read" o prompt interattivi blocca la CI
# Causa: l'hook tenta di leggere input dall'utente

# Soluzione: verificare se si è in un ambiente interattivo
#!/bin/bash
if [ -t 0 ]; then
    # Terminale interattivo: chiedere conferma
    read -p "Continuare? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    # Non interattivo (CI/CD): procedere senza conferma
    echo "Ambiente non interattivo rilevato. Continuando..."
fi
```

#### Problema: Hook Lento che Rallenta il Workflow

```bash
# Diagnostica: misurare il tempo di ogni sezione dell'hook
#!/bin/bash
time_start() { START_TIME=$(date +%s%N); }
time_end() {
    local END_TIME=$(date +%s%N)
    local ELAPSED=$(( (END_TIME - START_TIME) / 1000000 ))
    echo "  Tempo: ${ELAPSED}ms"
}

time_start
echo "=> ESLint..."
npx eslint $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx)$')
time_end

time_start
echo "=> Prettier..."
npx prettier --check $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|css|json)$')
time_end

time_start
echo "=> Type check..."
npx tsc --noEmit
time_end

# Suggerimenti per velocizzare:
# 1. Usare --cache con ESLint: npx eslint --cache
# 2. Eseguire solo sui file staged, non su tutto il progetto
# 3. Spostare type check e test al pre-push
# 4. Usare Lefthook per esecuzione parallela
# 5. Considerare swc/esbuild per type check più veloce
```

### Log Strutturato per Hook

Per ambienti di produzione dove il debugging post-mortem è necessario:

```bash
#!/bin/bash
# Hook con logging strutturato

LOG_FILE="${GIT_DIR:-$(git rev-parse --git-dir)}/hooks.log"

log() {
    local level=$1
    shift
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "detached")
    local user=$(git config user.name)
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"hook\":\"pre-commit\",\"branch\":\"$branch\",\"user\":\"$user\",\"message\":\"$*\"}" >> "$LOG_FILE"
}

log "INFO" "Hook pre-commit avviato"

# Eseguire i controlli...
if ! npx eslint --cache $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ts|tsx)$' | tr '\n' ' ') 2>/dev/null; then
    log "ERROR" "ESLint fallito"
    exit 1
fi
log "INFO" "ESLint superato"

log "INFO" "Hook pre-commit completato con successo"
exit 0
```

---

## Configurazione Pre-commit Framework Avanzata

### Hook per Linguaggi Specifici

#### Configurazione Completa per Progetto Python

```yaml
# .pre-commit-config.yaml — Progetto Python avanzato
repos:
  # Hook generici
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ['--branch', 'main']
      - id: check-ast               # Verifica che i file Python siano sintatticamente validi
      - id: debug-statements         # Rileva breakpoint(), pdb, ipdb
      - id: check-docstring-first    # Docstring deve essere il primo statement

  # Ruff: linter + formatter ultra-veloce (sostituto di flake8+isort+black)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # MyPy: type checking statico
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-requests
          - types-PyYAML
          - pydantic
        args: [--strict, --ignore-missing-imports]

  # Bandit: analisi sicurezza per Python
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.0
    hooks:
      - id: bandit
        args: [-r, --severity-level=medium]
        exclude: tests/

  # Vulture: rilevamento codice morto
  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.13
    hooks:
      - id: vulture
        args: [src/, --min-confidence=80]

  # Pydocstyle: validazione docstring
  - repo: https://github.com/PyCQA/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
        args: [--convention=google]

  # Sicurezza: gitleaks
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Hook locale per test
  - repo: local
    hooks:
      - id: pytest-fast
        name: Run fast tests
        entry: python -m pytest tests/ -x -q --timeout=30 -m "not slow"
        language: system
        types: [python]
        pass_filenames: false
        stages: [push]

default_language_version:
  python: python3.12

ci:
  autofix_prs: true
  autoupdate_schedule: weekly
```

#### Configurazione Completa per Progetto Go

```yaml
# .pre-commit-config.yaml — Progetto Go
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  # Go: formatting e analisi statica
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-vet
      - id: go-imports
      - id: go-build
      - id: golangci-lint
        args: [--timeout=5m]

  # Go: rilevamento errori non gestiti
  - repo: local
    hooks:
      - id: go-errcheck
        name: Go errcheck
        entry: errcheck ./...
        language: system
        types: [go]
        pass_filenames: false

      - id: go-staticcheck
        name: Go staticcheck
        entry: staticcheck ./...
        language: system
        types: [go]
        pass_filenames: false

      - id: go-test
        name: Go test
        entry: go test -race -short ./...
        language: system
        types: [go]
        pass_filenames: false
        stages: [push]

  # Sicurezza Go
  - repo: local
    hooks:
      - id: govulncheck
        name: Go vulnerability check
        entry: govulncheck ./...
        language: system
        types: [go]
        pass_filenames: false
        stages: [push]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

### Scrivere Hook Personalizzati per il Framework Pre-commit

Per creare hook personalizzati riutilizzabili come repository separato, servono due file: lo script dell'hook e il manifesto `.pre-commit-hooks.yaml`.

#### Struttura del Repository Hook

```
my-custom-hooks/
├── .pre-commit-hooks.yaml    ← Manifesto degli hook disponibili
├── hooks/
│   ├── check-fixme.sh        ← Script Bash
│   ├── validate-schema.py    ← Script Python
│   └── check-license.sh      ← Script Bash
├── setup.py                  ← Per hook Python con dipendenze
└── README.md
```

#### Manifesto degli Hook

```yaml
# .pre-commit-hooks.yaml
- id: check-fixme
  name: Check for FIXME/TODO/HACK comments
  description: Blocca commit con commenti FIXME, TODO o HACK
  entry: hooks/check-fixme.sh
  language: script
  types: [text]

- id: validate-json-schema
  name: Validate JSON against schema
  description: Valida file JSON contro uno schema definito
  entry: hooks/validate-schema.py
  language: python
  types: [json]
  additional_dependencies: ['jsonschema>=4.0']

- id: check-license-header
  name: Check license header
  description: Verifica la presenza dell'header di licenza nei file sorgente
  entry: hooks/check-license.sh
  language: script
  types_or: [python, javascript, typescript, go, rust]
```

#### Script dell'Hook

```bash
#!/bin/bash
# hooks/check-fixme.sh — Verifica commenti FIXME/TODO/HACK
set -euo pipefail

PATTERNS="FIXME|TODO|HACK|XXX|WORKAROUND"
EXIT_CODE=0

for file in "$@"; do
    if grep -nE "\b($PATTERNS)\b" "$file" 2>/dev/null; then
        echo "ERRORE: Commenti temporanei trovati in $file"
        EXIT_CODE=1
    fi
done

exit $EXIT_CODE
```

#### Uso del Repository Hook Personalizzato

```yaml
# .pre-commit-config.yaml — nel progetto che usa gli hook
repos:
  - repo: https://github.com/mio-team/my-custom-hooks
    rev: v1.2.0
    hooks:
      - id: check-fixme
      - id: validate-json-schema
        args: ['--schema', 'schemas/config.schema.json']
      - id: check-license-header
```

### Configurazione pre-commit.ci

**pre-commit.ci** è un servizio cloud che esegue automaticamente gli hook del framework pre-commit nelle pull request su GitHub, senza dover configurare GitHub Actions manualmente:

```yaml
# .pre-commit-config.yaml — Configurazione per pre-commit.ci
ci:
  # Creare automaticamente PR con fix di formattazione
  autofix_prs: true
  autofix_commit_msg: "style: correzioni automatiche da pre-commit.ci"

  # Aggiornare automaticamente le versioni degli hook
  autoupdate_schedule: weekly
  autoupdate_commit_msg: "chore: aggiornamento hook pre-commit"

  # Branch dove eseguire autoupdate
  autoupdate_branch: develop

  # Hook da skippare nella CI (es. hook locali)
  skip:
    - run-tests     # Eseguire i test nella CI principale, non in pre-commit.ci
    - mypy           # Type check lento, meglio nella CI principale
```

---

## Husky v9: Configurazione Avanzata e Pattern Moderni

### Architettura di Husky v9

Husky v9 ha radicalmente semplificato l'architettura rispetto alle versioni precedenti. Gli hook sono semplici script shell nella directory `.husky/`, senza JSON di configurazione né logica di routing complessa.

```
progetto/
├── .husky/
│   ├── _/                    ← Directory interna di Husky (non modificare)
│   │   └── husky.sh          ← Script di bootstrap
│   ├── pre-commit            ← Script shell eseguibile
│   ├── commit-msg            ← Script shell eseguibile
│   └── pre-push              ← Script shell eseguibile
├── package.json
├── commitlint.config.mjs
└── ...
```

### lint-staged: Configurazione Avanzata

lint-staged v15+ offre configurazioni avanzate tramite file dedicati o funzioni JavaScript:

```javascript
// lint-staged.config.mjs — Configurazione avanzata con funzioni
export default {
  // Pattern semplice: array di comandi
  '*.{js,jsx,ts,tsx}': [
    'eslint --fix --cache',
    'prettier --write',
  ],

  // Pattern con funzione per logica condizionale
  '*.{ts,tsx}': (filenames) => {
    // Eseguire type check solo se sono stati modificati più di 5 file
    const cmds = [
      `eslint --fix --cache ${filenames.join(' ')}`,
      `prettier --write ${filenames.join(' ')}`,
    ];

    if (filenames.length > 5) {
      cmds.push('tsc --noEmit');
    }

    return cmds;
  },

  // CSS/SCSS
  '*.{css,scss}': [
    'stylelint --fix',
    'prettier --write',
  ],

  // JSON, YAML, Markdown
  '*.{json,yaml,yml}': ['prettier --write'],
  '*.md': ['prettier --write', 'markdownlint --fix'],

  // Immagini: ottimizzazione
  '*.{png,jpg,jpeg,gif,svg}': [
    'imagemin-lint-staged',
  ],

  // Python (se presente nel progetto)
  '*.py': [
    'ruff check --fix',
    'ruff format',
  ],

  // Dockerfile
  'Dockerfile*': ['hadolint'],

  // Shell scripts
  '*.sh': ['shellcheck'],
};
```

#### lint-staged con Configurazione per Monorepo

```javascript
// lint-staged.config.mjs — Monorepo con workspace
import path from 'path';

export default {
  '*.{js,jsx,ts,tsx}': (filenames) => {
    // Raggruppare i file per pacchetto
    const byPackage = {};
    for (const file of filenames) {
      const parts = file.split(path.sep);
      if (parts[0] === 'packages' && parts.length > 2) {
        const pkg = parts[1];
        if (!byPackage[pkg]) byPackage[pkg] = [];
        byPackage[pkg].push(file);
      }
    }

    // Eseguire lint per ogni pacchetto separatamente
    const commands = [];
    for (const [pkg, files] of Object.entries(byPackage)) {
      commands.push(
        `cd packages/${pkg} && npx eslint --fix ${files.map(f => path.relative(`packages/${pkg}`, f)).join(' ')}`
      );
    }

    return commands;
  },
};
```

### Husky con Variabili d'Ambiente e Condizioni

```bash
# .husky/pre-commit — Hook condizionale

# Saltare hooks nella CI
[ -n "$CI" ] && exit 0

# Saltare se si sta facendo un merge
[ -f .git/MERGE_HEAD ] && exit 0

# Saltare se si sta facendo un rebase
[ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] && exit 0

# Eseguire lint-staged solo se ci sono file staged
STAGED=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$STAGED" ] && exit 0

npx lint-staged
```

```bash
# .husky/pre-push — Hook con test selettivi

# Saltare nella CI
[ -n "$CI" ] && exit 0

# Eseguire test solo se file sorgente sono cambiati
REMOTE=$1
URL=$2

# Ottenere i file cambiati rispetto al remote
CHANGED=$(git diff --name-only "origin/main"...HEAD 2>/dev/null || echo "")

if echo "$CHANGED" | grep -qE '\.(ts|tsx|js|jsx)$'; then
    echo "File sorgente modificati. Esecuzione test..."
    npm test
else
    echo "Nessun file sorgente modificato. Test skippati."
fi
```

---

## Riferimenti

- **Git Documentation — githooks**: https://git-scm.com/docs/githooks
- **Pre-commit Framework**: https://pre-commit.com
- **Husky**: https://typicode.github.io/husky/
- **Lefthook**: https://github.com/evilmartians/lefthook
- **lint-staged**: https://github.com/lint-staged/lint-staged
- **Commitlint**: https://commitlint.js.org/
- **Gitleaks**: https://github.com/gitleaks/gitleaks
- **Git Pro Book — Customizing Git Hooks**: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- **Conventional Commits**: https://www.conventionalcommits.org/

---

## Esercizi

### Esercizio 1: Pre-commit Hook Manuale

```bash
# Obiettivo: scrivere un pre-commit hook da zero senza framework

# 1. Creare un repository di test:
git init hook-lab && cd hook-lab
echo "console.log('hello')" > app.js
git add . && git commit -m "init"

# 2. Creare un pre-commit hook che:
#    a) Verifica che nessun file committato contenga "TODO" o "FIXME"
#    b) Controlla che i file .js non contengano console.log
#    c) Verifica che nessun file superi 500 righe
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
set -euo pipefail

FILES=$(git diff --cached --name-only --diff-filter=ACM)

for f in $FILES; do
    if grep -qE 'TODO|FIXME' "$f"; then
        echo "ERRORE: $f contiene TODO/FIXME"
        exit 1
    fi
    if [[ "$f" == *.js ]] && grep -q 'console.log' "$f"; then
        echo "ERRORE: $f contiene console.log"
        exit 1
    fi
    LINES=$(wc -l < "$f")
    if [ "$LINES" -gt 500 ]; then
        echo "ERRORE: $f supera 500 righe ($LINES)"
        exit 1
    fi
done
HOOK
chmod +x .git/hooks/pre-commit

# 3. Testare il hook con un commit che viola le regole
# 4. Testare il bypass con git commit --no-verify (e spiegare perché è rischioso)
```

### Esercizio 2: Framework pre-commit con Configurazione Multi-Linguaggio

```bash
# Obiettivo: configurare pre-commit framework per un progetto poliglotta

# 1. Installare pre-commit:
pip install pre-commit

# 2. Creare un repository con file Python e YAML:
git init precommit-lab && cd precommit-lab
echo "import os,sys" > app.py
echo "key: value" > config.yaml
git add . && git commit -m "init"

# 3. Creare .pre-commit-config.yaml con:
#    - black (Python formatter)
#    - ruff (Python linter)
#    - check-yaml (validazione YAML)
#    - trailing-whitespace
#    - end-of-file-fixer
#    - detect-private-key (sicurezza)

# 4. Installare e eseguire:
pre-commit install
pre-commit run --all-files

# 5. Verificare che black riformatti app.py automaticamente
# 6. Aggiungere un file con whitespace trailing e osservare la correzione
```

### Esercizio 3: Husky + lint-staged + commitlint

```bash
# Obiettivo: configurare la toolchain JavaScript completa per commit quality

# 1. Creare un progetto Node.js:
mkdir husky-lab && cd husky-lab
npm init -y
git init

# 2. Installare le dipendenze:
npm install -D husky lint-staged @commitlint/cli @commitlint/config-conventional
npm install -D prettier eslint

# 3. Configurare Husky:
npx husky init

# 4. Configurare lint-staged in package.json:
#    "*.{js,ts}": ["eslint --fix", "prettier --write"],
#    "*.{json,md}": ["prettier --write"]

# 5. Configurare commitlint:
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# 6. Creare hook:
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
echo "npx lint-staged" > .husky/pre-commit

# 7. Testare con un commit che viola Conventional Commits:
echo "const x = 1" > app.js
git add . && git commit -m "did stuff"  # Deve fallire
git commit -m "feat: add initial app"   # Deve passare
```

### Esercizio 4: Hook commit-msg per Validazione Avanzata

```bash
# Obiettivo: scrivere un commit-msg hook con validazione personalizzata

# 1. Creare un hook commit-msg in Python:
cat > .git/hooks/commit-msg << 'HOOK'
#!/usr/bin/env python3
import sys
import re

msg_file = sys.argv[1]
with open(msg_file) as f:
    msg = f.read().strip()

# Validare Conventional Commits
pattern = r'^(feat|fix|refactor|docs|test|chore|perf|ci)(\(.+\))?!?: .{3,72}$'
first_line = msg.split('\n')[0]

if not re.match(pattern, first_line):
    print(f"ERRORE: '{first_line}' non rispetta Conventional Commits")
    print("Formato: <type>(<scope>): <description>")
    print("Tipi: feat, fix, refactor, docs, test, chore, perf, ci")
    sys.exit(1)

# Verificare che il body sia separato da una riga vuota
lines = msg.split('\n')
if len(lines) > 1 and lines[1] != '':
    print("ERRORE: il body deve essere separato dalla prima riga da una riga vuota")
    sys.exit(1)

print(f"OK: {first_line}")
HOOK
chmod +x .git/hooks/commit-msg

# 2. Testare con vari formati di messaggio
# 3. Verificare che i merge commit passino senza validazione
# 4. Estendere con controllo della lunghezza del body (max 72 char per riga)
```

### Esercizio 5: Hook Server-Side Simulato

```bash
# Obiettivo: simulare un pre-receive hook per policy di repository

# 1. Creare un bare repository (simula il server):
git init --bare /tmp/server-repo.git

# 2. Creare un pre-receive hook:
cat > /tmp/server-repo.git/hooks/pre-receive << 'HOOK'
#!/bin/bash
while read oldrev newrev refname; do
    # Bloccare push diretti a main
    if [ "$refname" = "refs/heads/main" ]; then
        echo "ERRORE: push diretto a main non consentito. Usa una pull request."
        exit 1
    fi

    # Bloccare commit senza firma GPG (se disponibile)
    # Bloccare file > 10MB
    if [ "$oldrev" = "0000000000000000000000000000000000000000" ]; then
        COMMITS=$(git rev-list "$newrev")
    else
        COMMITS=$(git rev-list "$oldrev..$newrev")
    fi

    for commit in $COMMITS; do
        FILES=$(git diff-tree --no-commit-id -r --name-only "$commit")
        for file in $FILES; do
            SIZE=$(git cat-file -s "$(git ls-tree -r "$commit" -- "$file" | awk '{print $3}')" 2>/dev/null || echo 0)
            if [ "$SIZE" -gt 10485760 ]; then
                echo "ERRORE: $file nel commit $commit supera 10MB"
                exit 1
            fi
        done
    done
done
HOOK
chmod +x /tmp/server-repo.git/hooks/pre-receive

# 3. Clonare e testare:
git clone /tmp/server-repo.git /tmp/client-repo
cd /tmp/client-repo
echo "test" > file.txt && git add . && git commit -m "feat: test"
git push origin main  # Deve fallire

# 4. Creare un branch feature e pushare con successo
git checkout -b feature/test
git push origin feature/test  # Deve passare
```

---

## Letture consigliate

- **Git Pro Book — Customizing Git Hooks** — https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks (consultato: 2026-05-24). Capitolo ufficiale che descrive tutti gli hook disponibili con esempi pratici.

- **Pre-commit Framework Documentation** — https://pre-commit.com (consultato: 2026-05-24). Documentazione completa del framework Python per la gestione di hook portabili e multi-linguaggio.

- **Husky Documentation** — https://typicode.github.io/husky/ (consultato: 2026-05-24). Guida ufficiale per l'integrazione di Git hooks in progetti Node.js.

- **Commitlint Documentation** — https://commitlint.js.org/ (consultato: 2026-05-24). Strumento per la validazione dei messaggi di commit secondo lo standard Conventional Commits.

- **Lefthook — Fast Git Hooks Manager** — https://github.com/evilmartians/lefthook (consultato: 2026-05-24). Alternativa performante a Husky, scritta in Go, con supporto per parallelismo e configurazione YAML.

- **Conventional Commits Specification** — https://www.conventionalcommits.org/ (consultato: 2026-05-24). Specifica dello standard per messaggi di commit strutturati, compatibile con semver e changelog automatici.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti Git: ciclo commit, staging area | 01 | [01-fondamenti-git.md](01-fondamenti-git.md) |
| Git Internals: struttura di .git/, oggetti | 07 | [07-git-interni-oggetti-refs.md](07-git-interni-oggetti-refs.md) |
| Gitignore, Gitattributes e Configurazione | 11 | [11-gitignore-gitattributes-config.md](11-gitignore-gitattributes-config.md) |
| Workflow di team: protezione branch, review | 20 | [20-git-workflow-team-guida-completa.md](20-git-workflow-team-guida-completa.md) |
| GitHub Actions: automazione CI/CD | 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) |
| GitHub Security Scanning: secret scanning | 16 | [16-github-security-scanning.md](16-github-security-scanning.md) |
| Supply Chain e Attestation: firma e provenienza | 27 | [27-supply-chain-attestation-slsa.md](27-supply-chain-attestation-slsa.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **client-side hook** | Hook eseguito sul repository locale dello sviluppatore (pre-commit, commit-msg, pre-push). Non può essere imposto centralmente. |
| **commit-msg hook** | Hook che riceve il file del messaggio di commit come argomento. Usato per validare il formato del messaggio (es. Conventional Commits). |
| **Conventional Commits** | Specifica per messaggi di commit strutturati nel formato `<type>(<scope>): <description>`. Consente generazione automatica di changelog e versionamento semantico. |
| **Husky** | Strumento Node.js per gestire Git hooks in progetti JavaScript/TypeScript. Usa file nella directory `.husky/` per definire gli hook. |
| **lefthook** | Gestore di Git hooks scritto in Go, alternativa a Husky. Supporta esecuzione parallela degli hook e configurazione dichiarativa YAML. |
| **lint-staged** | Strumento Node.js che esegue linter e formatter solo sui file attualmente in staging (`git add`), evitando di processare l'intero progetto. |
| **pre-commit (framework)** | Framework Python per la gestione di Git hooks multi-linguaggio. Usa `.pre-commit-config.yaml` per definire hook da repository esterni. |
| **pre-commit hook** | Hook Git eseguito prima che il commit venga creato. Exit code non-zero blocca il commit. Usato per lint, format, test rapidi. |
| **pre-push hook** | Hook Git eseguito prima del push al remote. Riceve informazioni sul remote e sui ref da pushare. Usato per test più costosi. |
| **pre-receive hook** | Hook server-side eseguito quando il server riceve un push. Può accettare o rifiutare l'intero push. Usato per policy enforcement centralizzato. |
| **post-receive hook** | Hook server-side eseguito dopo che il push è stato accettato. Non può rifiutare il push. Usato per notifiche, deploy automatici, CI trigger. |
| **server-side hook** | Hook eseguito sul repository remoto (pre-receive, update, post-receive). Fornisce enforcement centralizzato delle policy del team. |
| **shebang** | Prima riga di uno script hook (es. `#!/bin/bash`, `#!/usr/bin/env python3`) che indica al sistema operativo quale interprete usare per eseguire lo script. |
