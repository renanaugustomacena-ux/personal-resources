---
corso: "GitHub e Git Actions"
fase: "2 — Configurazione Git"
modulo: "11"
titolo: "Gitignore, Gitattributes e Configurazione"
versione: "Git 2.47+"
livello: "Intermedio"
prerequisiti:
  - "01 — Fondamenti Git"
  - "07 — Git Internals: Oggetti e Refs"
obiettivi:
  - "Scrivere regole .gitignore efficaci e comprendere la precedenza dei pattern"
  - "Configurare .gitattributes per line endings, linguist, merge driver e LFS tracking"
  - "Padroneggiare i 3 livelli di git config (system, global, local) e i conditional includes"
  - "Utilizzare .mailmap per normalizzare le identità degli autori nella cronologia"
  - "Configurare alias, credential helper e firme GPG per un workflow professionale"
tag: [git, gitignore, gitattributes, git-config, mailmap, credential, gpg, eol]
---

# Gitignore, Gitattributes e Configurazione — Guida Approfondita

> **Modulo 11** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti Git](01-fondamenti-git.md), [Git Internals](07-git-interni-oggetti-refs.md)
>
> Al termine di questo modulo saprai:
> 1. Scrivere regole `.gitignore` efficaci e comprendere la precedenza dei pattern
> 2. Configurare `.gitattributes` per line endings, linguist, merge driver e LFS tracking
> 3. Padroneggiare i 3 livelli di `git config` (system, global, local) e i conditional includes
> 4. Utilizzare `.mailmap` per normalizzare le identità degli autori nella cronologia
> 5. Configurare alias, credential helper e firme GPG per un workflow professionale
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **`.gitignore` per nuovi file; `git rm --cached` per file gia tracked.**
2. **`.gitattributes` per text/binary, eol, merge driver.**
3. **`git config` 3 livelli: system/global/local.** Local override global.
4. **GitHub gitignore templates: https://github.com/github/gitignore.**
5. **`.mailmap` normalizza autori nel log.** Unifica identita multiple.
6. **Hooks client/server-side per automatizzare gate di qualita.**


## Indice
- [Panoramica](#panoramica)
- [.gitignore: Esclusione dei File](#gitignore-esclusione-dei-file)
- [Global Gitignore](#global-gitignore)
- [.gitattributes: Attributi dei File](#gitattributes-attributi-dei-file)
- [Git Config: Sistema, Globale e Locale](#git-config-sistema-globale-e-locale)
- [Conditional Includes](#conditional-includes)
- [Aliases](#aliases)
- [Credential Helpers](#credential-helpers)
- [Configurazione di Editor, Diff e Merge Tool](#configurazione-di-editor-diff-e-merge-tool)
- [.mailmap: Normalizzazione degli Autori](#mailmap-normalizzazione-degli-autori)
- [Git Hooks: Client-Side e Server-Side](#git-hooks-client-side-e-server-side)
- [Hooks Client-Side in Dettaglio](#hooks-client-side-in-dettaglio)
- [Hooks Server-Side in Dettaglio](#hooks-server-side-in-dettaglio)
- [Hooks con Husky e lint-staged](#hooks-con-husky-e-lint-staged)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande Frequenti (Q&A)](#domande-frequenti-qa)
- [Esercizi](#esercizi)
- [Riferimenti](#riferimenti)

---

## Panoramica

La configurazione corretta di Git e un aspetto spesso sottovalutato che ha un impatto significativo sulla produttivita e sulla qualita del workflow di versionamento. Questa guida esplora in profondita i file di configurazione principali — `.gitignore`, `.gitattributes`, `.mailmap`, i vari livelli di `git config` — e le funzionalita avanzate come gli aliases, i credential helpers, la configurazione degli strumenti di diff e merge, e soprattutto il sistema di hooks che consente di automatizzare gate di qualita in ogni fase del workflow Git.

Una configurazione ben curata previene problemi comuni come file binari committati accidentalmente, conflitti di line endings tra sistemi operativi diversi, credenziali esposte nel repository, identita autore inconsistenti e inefficienze nel workflow quotidiano. Investire tempo nella configurazione iniziale ripaga enormemente nel lungo termine.

I file di configurazione di Git si dividono in due categorie: quelli **versionati nel repository** (`.gitignore`, `.gitattributes`, `.mailmap`, file di hooks) che devono essere condivisi tra tutti i collaboratori, e quelli **locali all'utente** (`~/.gitconfig`, `.git/config`, `.git/info/exclude`) che contengono preferenze personali.

---

## .gitignore: Esclusione dei File

### Sintassi dei Pattern

Il file `.gitignore` usa una sintassi di pattern basata su glob per specificare quali file e directory devono essere ignorati da Git. I pattern vengono applicati relativamente alla posizione del file `.gitignore`.

```gitignore
# Commenti iniziano con #

# Pattern semplici
*.log                   # Ignorare tutti i file .log
*.tmp                   # Ignorare tutti i file .tmp
*.swp                   # Ignorare file swap di Vim

# Directory
node_modules/           # Ignorare la directory node_modules (trailing slash = solo directory)
dist/                   # Ignorare la directory dist
build/                  # Ignorare la directory build
.cache/                 # Ignorare cache directory

# Glob pattern
*.py[cod]               # Ignorare .pyc, .pyo, .pyd
*.[oa]                  # Ignorare .o e .a (oggetti compilati)
doc/**/*.pdf            # Ignorare PDF nelle sottodirectory di doc/

# Wildcard
debug[0-9].log          # debug0.log, debug1.log, ..., debug9.log
temp-*                  # Qualsiasi file che inizia con temp-

# Double star (globstar)
**/logs                 # Qualsiasi directory chiamata "logs" a qualsiasi profondita
**/logs/debug.log       # debug.log in qualsiasi directory "logs"
logs/**                 # Tutto dentro la directory logs
a/**/z                  # a/z, a/b/z, a/b/c/z, ecc.

# Negazione (eccezione)
*.log                   # Ignorare tutti i .log
!important.log          # MA NON important.log

# Ignorare tutto tranne
/*                      # Ignorare tutto nella root
!/.gitignore            # Eccetto .gitignore
!/src/                  # Eccetto la directory src
!/package.json          # Eccetto package.json

# Directory-only pattern
# Il trailing slash indica "solo se e una directory"
build/                  # Ignora la directory build/ ma non un file chiamato build
```

### Regole di Precedenza dei Pattern

L'ordine delle regole in `.gitignore` e importante. Un pattern successivo puo annullare uno precedente tramite negazione:

```gitignore
# Regola: l'ultimo pattern che matcha vince

# Caso 1: Escludere tutto in build/ tranne un file specifico
build/                  # Ignora tutto in build/
!build/deploy.sh        # ERRORE: non funziona! Se la directory e ignorata,
                        # Git non esplora il suo contenuto

# Soluzione corretta: ignorare il contenuto, non la directory
build/*                 # Ignora il contenuto di build/ (nota: * non /)
!build/deploy.sh        # Ora funziona: la directory build/ e tracciata

# Caso 2: Negazione annullata da pattern successivo
*.log                   # Ignora tutti i .log
!debug.log              # Eccezione per debug.log
logs/                   # Ma ignora la directory logs/
# Risultato: debug.log nella root e tracciato,
# ma logs/debug.log e ignorato perche logs/ e ignorata
```

### Pattern Avanzati

```gitignore
# Ignorare file in una directory specifica senza ricorsione
/config/secrets.yml     # Solo in /config/, non in sub/config/

# Ignorare tutto in una directory tranne file specifici
data/*                  # Ignorare tutto in data/
!data/.gitkeep          # Mantenere il placeholder
!data/README.md         # Mantenere il README

# Pattern per IDE e editor
.idea/                  # JetBrains IDE
.vscode/                # Visual Studio Code (opzionale, alcuni lo versionano)
*.sublime-project
*.sublime-workspace
.project                # Eclipse
.classpath              # Eclipse

# Pattern per sistemi operativi
.DS_Store               # macOS
._*                     # macOS resource forks
Thumbs.db               # Windows
Desktop.ini             # Windows
*~                      # Linux backup files

# Pattern per linguaggi specifici
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.eggs/
*.egg
.Python
env/
venv/
.venv/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-store/

# Java
*.class
*.jar
*.war
target/
.gradle/

# Go
/vendor/
*.exe
*.exe~
*.dll
*.so
*.dylib

# Rust
/target/
Cargo.lock              # Solo per librerie, non per binari

# Ambiente e segreti
.env
.env.local
.env.*.local
*.pem
*.key
credentials.json
service-account.json
```

### Precedenza e Livelli di .gitignore

Git applica i pattern `.gitignore` da multiple fonti, con la seguente precedenza (dalla piu alta alla piu bassa):

1. **Pattern dalla linea di comando** (es. `git add --force`)
2. **`.gitignore` nella stessa directory** del file
3. **`.gitignore` nelle directory parent** fino alla root del repository
4. **`$GIT_DIR/info/exclude`** (locale, non condiviso — ideale per ignore personali)
5. **`core.excludesFile`** (globale, per utente)

```bash
# Verificare perche un file e ignorato
git check-ignore -v path/to/file
# .gitignore:5:*.log    path/to/file.log
# Mostra il file, la riga e il pattern che causa l'esclusione

# Verificare se un file e ignorato
git check-ignore path/to/file
# Se produce output, il file e ignorato

# Verificare piu file
git check-ignore -v *.log src/*.tmp build/

# Verificare tutti i file ignorati nel repository
git status --ignored --short

# Verificare tutti i file ignorati ricorsivamente
git ls-files --others --ignored --exclude-standard
```

### Ignorare File Gia Tracciati

`.gitignore` funziona solo per file **non tracciati**. Per smettere di tracciare un file gia committato:

```bash
# Rimuovere il file dall'index ma mantenerlo sul disco
git rm --cached file-da-ignorare.log

# Rimuovere un'intera directory
git rm -r --cached node_modules/

# Poi aggiungere il pattern a .gitignore
echo "file-da-ignorare.log" >> .gitignore

# Committare
git add .gitignore
git commit -m "chore: rimuovere file dal tracking e aggiornare .gitignore"
```

### $GIT_DIR/info/exclude

Il file `.git/info/exclude` funziona esattamente come `.gitignore` ma non e versionato. E il posto giusto per pattern personali che non devono essere condivisi (es. file di configurazione IDE specifici, note personali):

```bash
# Aggiungere un pattern locale
echo "my-notes.txt" >> .git/info/exclude
echo ".my-scripts/" >> .git/info/exclude

# Questi pattern funzionano solo nel repository corrente
# e non sono visibili ad altri collaboratori
```

### Template .gitignore per Progetto

```bash
# Generare un .gitignore ottimale con gitignore.io
curl -sL https://www.toptal.com/developers/gitignore/api/node,python,java,macos,linux,windows > .gitignore

# Usare i template ufficiali GitHub
curl -sL https://raw.githubusercontent.com/github/gitignore/main/Node.gitignore > .gitignore

# Combinare piu template
cat <(curl -sL .../Node.gitignore) <(curl -sL .../Python.gitignore) > .gitignore
```

---

## Global Gitignore

Il global gitignore contiene pattern che dovrebbero essere ignorati in **tutti** i repository di un utente. E il luogo ideale per file specifici dell'IDE e del sistema operativo.

```bash
# Configurare il path del global gitignore
git config --global core.excludesFile ~/.gitignore_global

# Creare il file
cat > ~/.gitignore_global << 'EOF'
# macOS
.DS_Store
._*
.Spotlight-V100
.Trashes

# Windows
Thumbs.db
Desktop.ini
$RECYCLE.BIN/

# Linux
*~
.directory

# IDE: JetBrains
.idea/
*.iml
*.iws
*.ipr

# IDE: VS Code
.vscode/
*.code-workspace

# IDE: Vim
*.swp
*.swo
*~
Session.vim

# IDE: Emacs
*~
\#*\#
.#*

# Tags
tags
TAGS
.tags

# Direnv
.envrc
.direnv/
EOF
```

La distinzione e importante: il `.gitignore` nel repository contiene pattern specifici del progetto (come `node_modules/` per progetti Node.js). Il global gitignore contiene pattern specifici dell'ambiente di sviluppo dell'utente. Non inserire mai pattern IDE nel `.gitignore` del progetto — ogni sviluppatore deve configurare il proprio global gitignore.

---

## .gitattributes: Attributi dei File

### Fondamenti

Il file `.gitattributes` assegna attributi ai file in base al loro path. Questi attributi controllano come Git gestisce i file durante operazioni come diff, merge, checkout e archivio.

```gitattributes
# Formato: pattern attributo1 attributo2 ...

# Line endings
* text=auto                    # Git decide automaticamente (consigliato)
*.sh text eol=lf               # Forzare LF per script shell
*.bat text eol=crlf            # Forzare CRLF per batch file Windows
*.ps1 text eol=crlf            # Forzare CRLF per PowerShell

# File binari
*.png binary                   # Trattare come binario
*.jpg binary
*.gif binary
*.ico binary
*.zip binary
*.pdf binary
*.woff binary
*.woff2 binary
*.ttf binary
*.eot binary

# Linguist (per le statistiche GitHub)
*.html linguist-detectable     # Contare HTML nelle statistiche
docs/* linguist-documentation  # Marcare come documentazione
vendor/* linguist-vendored     # Marcare come codice vendored
```

### Gestione dei Line Endings

Il problema dei line endings (LF su Unix/macOS vs CRLF su Windows) e una delle fonti piu comuni di diff inutili e conflitti. `.gitattributes` fornisce la soluzione definitiva.

```gitattributes
# Regola base: normalizzazione automatica
* text=auto

# File di testo specifici
*.c text
*.h text
*.js text
*.ts text
*.py text
*.rb text
*.java text
*.cs text
*.go text
*.rs text
*.md text
*.txt text
*.yml text
*.yaml text
*.json text
*.xml text
*.html text
*.css text
*.scss text
*.sql text

# File che devono mantenere LF anche su Windows
*.sh text eol=lf
Makefile text eol=lf
Dockerfile text eol=lf
*.dockerfile text eol=lf
.editorconfig text eol=lf
.gitattributes text eol=lf
.gitignore text eol=lf

# File che devono mantenere CRLF
*.sln text eol=crlf
*.csproj text eol=crlf
*.bat text eol=crlf
*.cmd text eol=crlf

# File binari (nessuna normalizzazione)
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.bmp binary
*.tiff binary
*.ico binary
*.svg text
*.pdf binary
*.zip binary
*.gz binary
*.tar binary
*.7z binary
*.rar binary
*.mp3 binary
*.mp4 binary
*.avi binary
*.mov binary
*.flv binary
*.fla binary
*.psd binary
*.ai binary
*.sketch binary
```

### Come Funziona text=auto

Quando si specifica `* text=auto`, Git usa un'euristica per determinare se un file e di testo o binario:

1. Legge i primi 8000 byte del file
2. Se contiene un byte NUL (`\0`), lo classifica come binario
3. Se e testo, normalizza i line endings: in repository memorizza LF, in checkout usa il line ending nativo dell'OS (o quello specificato in `.gitattributes`)

```bash
# Dopo aver aggiunto o modificato .gitattributes, rinormalizzare:
git add --renormalize .
git status
# Mostra i file i cui line endings sono stati corretti
git commit -m "chore: normalizzare line endings"
```

### Diff Drivers Personalizzati

Git permette di configurare driver di diff personalizzati per tipi di file specifici. Questo e particolarmente utile per file binari che hanno una rappresentazione testuale.

```gitattributes
# Usare diff driver personalizzati
*.plist diff=plist
*.docx diff=docx
*.pdf diff=pdf
*.png diff=exif
*.xlsx diff=xlsx
*.sqlite diff=sqlite
```

```bash
# Configurare i diff drivers

# Diff per file plist (macOS)
git config diff.plist.textconv "plutil -convert xml1 -o -"

# Diff per immagini (mostra metadati EXIF)
git config diff.exif.textconv "exiftool"

# Diff per PDF (converte in testo)
git config diff.pdf.textconv "pdftotext -layout"

# Diff per documenti Word
git config diff.docx.textconv "pandoc --to=plain"

# Diff per Excel (richiede ssconvert di gnumeric)
git config diff.xlsx.textconv "ssconvert --export-type=Gnumeric_stf:stf_csv"

# Diff per database SQLite
git config diff.sqlite.textconv "sqlite3 /dev/stdin .dump <"

# Verifica: ora git diff mostra differenze leggibili per questi file
git diff HEAD~1 -- documento.pdf
```

### Merge Strategies per File

```gitattributes
# Non tentare il merge automatico per file specifici
database.sql merge=ours        # Mantenere sempre la nostra versione
package-lock.json merge=ours   # Rigenerare il lock file dopo il merge
yarn.lock merge=ours
pnpm-lock.yaml merge=ours

# Merge driver personalizzato per CHANGELOG
CHANGELOG.md merge=union       # Combinare le righe di entrambe le versioni

# Merge driver per file di configurazione con sezioni ordinate
*.po merge=merge-po            # Per file gettext .po
```

```bash
# Configurare il merge driver "ours"
git config merge.ours.driver true
# Il driver "true" restituisce sempre 0 (successo), mantenendo la nostra versione

# Merge driver personalizzato
git config merge.custom.name "Custom merge driver"
git config merge.custom.driver "custom-merge-tool %O %A %B %L %P"
# %O = ancestor, %A = ours, %B = theirs, %L = conflict marker size, %P = path

# Merge driver per file PO (gettext)
git config merge.merge-po.driver "msgmerge --no-fuzzy-matching -o %A %A %B"
```

### Linguist Attributes per GitHub

GitHub usa la libreria **Linguist** per determinare le statistiche linguistiche del repository. `.gitattributes` puo sovrascrivere queste determinazioni.

```gitattributes
# Ignorare file generati nelle statistiche
*.min.js linguist-generated
*.min.css linguist-generated
dist/* linguist-generated
coverage/* linguist-generated
*.g.dart linguist-generated     # Flutter generated files
*.freezed.dart linguist-generated

# Marcare codice di terze parti
vendor/* linguist-vendored
third-party/* linguist-vendored

# Marcare come documentazione
docs/* linguist-documentation
*.md linguist-documentation

# Forzare il riconoscimento del linguaggio
*.h linguist-language=C          # Trattare .h come C (non C++ o Objective-C)
Dockerfile.* linguist-language=Dockerfile
*.jsonc linguist-language=JSON

# Rendere un file rilevabile (contato nelle statistiche)
*.html linguist-detectable
```

### Export Attributes

Controllare cosa viene incluso negli archivi creati con `git archive`:

```gitattributes
# Escludere file dagli archivi
.gitignore export-ignore
.gitattributes export-ignore
.github/ export-ignore
tests/ export-ignore
docs/ export-ignore
*.test.js export-ignore
*.spec.ts export-ignore
Makefile export-ignore
jest.config.* export-ignore
.eslintrc.* export-ignore
.prettierrc export-ignore

# Includere la versione negli archivi
*.txt export-subst
# In un file con export-subst, $Format:...$ viene espanso
# Esempio in VERSION.txt: $Format:%H$
# Diventa l'hash completo del commit nell'archivio
```

```bash
# Creare un archivio che rispetta export-ignore e export-subst
git archive --format=tar.gz --prefix=project-v1.0/ HEAD > release.tar.gz

# Verificare cosa viene incluso
git archive --list HEAD
```

### Filter Attributes (clean/smudge)

I filtri clean/smudge permettono di trasformare il contenuto dei file durante checkout (smudge) e commit (clean). Caso d'uso classico: rimuovere dati sensibili dai file prima del commit.

```gitattributes
# Applicare filtro personalizzato
*.config filter=strip-secrets
database.yml filter=strip-secrets
```

```bash
# Configurare il filtro
git config filter.strip-secrets.clean "sed 's/password=.*/password=REDACTED/'"
git config filter.strip-secrets.smudge cat

# Il filtro clean viene applicato quando il file e aggiunto all'index (git add)
# Il filtro smudge viene applicato quando il file e estratto nel working tree (git checkout)

# Caso d'uso: git-crypt per crittografare file sensibili
# git-crypt usa filter attributes per cifrare trasparentemente
*.key filter=git-crypt diff=git-crypt
*.secret filter=git-crypt diff=git-crypt
```

---

## Git Config: Sistema, Globale e Locale

### I Tre Livelli di Configurazione

Git ha tre livelli di configurazione, con precedenza crescente:

```bash
# Sistema (tutti gli utenti)
git config --system <key> <value>
# File: /etc/gitconfig

# Globale (utente corrente, tutti i repository)
git config --global <key> <value>
# File: ~/.gitconfig o ~/.config/git/config

# Locale (repository corrente)
git config --local <key> <value>
# File: .git/config

# Worktree (singolo worktree in un repo multi-worktree)
git config --worktree <key> <value>
# File: .git/config.worktree

# Visualizzare tutte le configurazioni con la loro origine
git config --list --show-origin

# Visualizzare una configurazione specifica con origine e scope
git config --show-origin --show-scope user.name
# file:/home/user/.gitconfig    global    Mario Rossi

# Rimuovere una configurazione
git config --global --unset user.name

# Rimuovere una sezione intera
git config --global --remove-section alias
```

### Configurazioni Essenziali

```bash
# Identita
git config --global user.name "Mario Rossi"
git config --global user.email "mario.rossi@example.com"

# Editor predefinito
git config --global core.editor "vim"
git config --global core.editor "code --wait"     # VS Code
git config --global core.editor "nano"
git config --global core.editor "subl -n -w"      # Sublime Text

# Line endings
git config --global core.autocrlf input    # macOS/Linux
git config --global core.autocrlf true     # Windows

# Colore
git config --global color.ui auto

# Branch predefinito
git config --global init.defaultBranch main

# Pull strategy
git config --global pull.rebase true       # Rebase invece di merge durante pull
git config --global pull.ff only           # Solo fast-forward durante pull

# Push strategy
git config --global push.default current   # Push del branch corrente al remote omonimo
git config --global push.autoSetupRemote true  # Creare automaticamente il tracking

# Rebase
git config --global rebase.autoSquash true
git config --global rebase.autoStash true  # Stash automatico prima del rebase

# Merge
git config --global merge.conflictstyle zdiff3  # Mostra anche ancestor nel conflitto
git config --global rerere.enabled true          # Ricorda risoluzioni di conflitti

# Diff
git config --global diff.algorithm histogram  # Algoritmo di diff migliore
git config --global diff.colorMoved default   # Evidenziare righe spostate

# Performance
git config --global core.fsmonitor true
git config --global core.untrackedCache true
git config --global feature.manyFiles true     # Ottimizzazioni per repository grandi

# Fetch
git config --global fetch.prune true           # Pulire branch remoti eliminati
git config --global fetch.writeCommitGraph true

# Sicurezza — verificare oggetti durante transfer
git config --global transfer.fsckObjects true
git config --global receive.fsckObjects true
git config --global fetch.fsckObjects true

# GPG Signing
git config --global commit.gpgsign true
git config --global tag.gpgSign true
git config --global gpg.format ssh                    # Usare SSH key per firmare
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

---

## Conditional Includes

Git supporta include condizionali per applicare configurazioni diverse in base alla directory, al branch o al remote:

```ini
# ~/.gitconfig

[user]
    name = Mario Rossi
    email = mario@personal.com

# Per repository sotto ~/work/ — usa email aziendale
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work

# Per repository sotto ~/opensource/ — usa email personale con GPG
[includeIf "gitdir:~/opensource/"]
    path = ~/.gitconfig-opensource

# Condizionale basata sul branch (Git 2.36+)
[includeIf "onbranch:release/**"]
    path = ~/.gitconfig-release

# Condizionale basata sul remote (Git 2.36+)
[includeIf "hasconfig:remote.*.url:git@github.com:myorg/**"]
    path = ~/.gitconfig-myorg
```

```ini
# ~/.gitconfig-work
[user]
    email = mario.rossi@azienda.com
[commit]
    gpgsign = true
[core]
    sshCommand = ssh -i ~/.ssh/id_work -F /dev/null
```

```ini
# ~/.gitconfig-opensource
[user]
    email = mario@personal.com
    signingkey = ~/.ssh/id_opensource.pub
```

### Verifica Conditional Includes

```bash
# Verificare quale configurazione e effettiva in un repository
cd ~/work/project-a
git config user.email
# Output: mario.rossi@azienda.com

cd ~/personal/hobby
git config user.email
# Output: mario@personal.com

# Verificare tutte le configurazioni con la loro origine
git config --list --show-origin | grep user
```

---

## Aliases

### Aliases Fondamentali

```bash
# Status abbreviato
git config --global alias.st "status -sb"

# Log compatto
git config --global alias.lg "log --graph --oneline --all --decorate"
git config --global alias.ll "log --oneline -15"

# Branch
git config --global alias.br "branch"
git config --global alias.co "checkout"
git config --global alias.sw "switch"

# Commit
git config --global alias.ci "commit"
git config --global alias.ca "commit --amend"
git config --global alias.can "commit --amend --no-edit"

# Diff
git config --global alias.df "diff"
git config --global alias.ds "diff --staged"
git config --global alias.dw "diff --word-diff"
```

### Aliases Avanzati

```bash
# Ultimo commit
git config --global alias.last "log -1 HEAD --format='%H %s'"

# Unfare l'ultimo commit (soft reset)
git config --global alias.undo "reset --soft HEAD~1"

# Chi ha modificato cosa
git config --global alias.who "shortlog -sn --no-merges"

# Commit di oggi
git config --global alias.today "log --since=midnight --oneline --no-merges"

# File modificati nell'ultimo commit
git config --global alias.changed "diff-tree --no-commit-id --name-only -r HEAD"

# Aliases con comandi shell (prefisso !)
git config --global alias.root '!pwd'
git config --global alias.exec '!exec '

# Trovare branch che contengono un commit
git config --global alias.contains "branch -a --contains"

# Pulire branch merged
git config --global alias.cleanup '!git branch --merged main | grep -v "main\|develop" | xargs -r git branch -d'

# Stash con data
git config --global alias.sl "stash list --format='%gd (%cr): %gs'"

# Alias complesso: log con statistiche
git config --global alias.report '!git log --format="%an" --since="1 month ago" | sort | uniq -c | sort -rn'

# Log con tree visuale colorato
git config --global alias.tree 'log --graph --abbrev-commit --decorate --format=format:"%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(auto)%d%C(reset)"'

# Trovare l'ultimo commit che ha toccato un file
git config --global alias.when '!f() { git log -1 --format="%ai %s" -- "$1"; }; f'

# Diff statistico tra branch
git config --global alias.stat 'diff --stat'

# Lista branch ordinati per ultima modifica
git config --global alias.recent '!git for-each-ref --sort=-committerdate refs/heads/ --format="%(committerdate:short) %(refname:short)" | head -20'

# Contare linee di codice per autore
git config --global alias.blame-stats '!git ls-files | xargs -I{} git blame --line-porcelain {} | grep "^author " | sort | uniq -c | sort -rn'
```

### Aliases nel File di Configurazione

```ini
# ~/.gitconfig
[alias]
    st = status -sb
    lg = log --graph --oneline --all --decorate
    co = checkout
    ci = commit
    br = branch
    undo = reset --soft HEAD~1
    who = shortlog -sn --no-merges
    cleanup = "!git branch --merged main | grep -v 'main\\|develop' | xargs -r git branch -d"
    recent = "!git for-each-ref --sort=-committerdate refs/heads/ --format='%(committerdate:short) %(refname:short)' | head -20"
    # Alias multi-riga con shell function
    fixup = "!f() { git commit --fixup=$1 && GIT_SEQUENCE_EDITOR=: git rebase --autosquash $1~1; }; f"
```

---

## Credential Helpers

### Tipi di Credential Helper

I credential helpers memorizzano le credenziali per evitare di reinserirle ad ogni operazione con i remote.

```bash
# Cache in memoria (predefinito: 15 minuti)
git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=3600'  # 1 ora

# Store su file (NON SICURO: password in chiaro in ~/.git-credentials)
git config --global credential.helper store
# Usare SOLO in ambienti isolati (CI, container effimeri)

# macOS Keychain
git config --global credential.helper osxkeychain

# Windows Credential Manager
git config --global credential.helper manager

# Linux: libsecret (GNOME Keyring)
git config --global credential.helper /usr/lib/git-core/git-credential-libsecret

# Linux: KDE Wallet
git config --global credential.helper /usr/lib/git-core/git-credential-kwallet

# GitHub CLI come credential helper (raccomandato per GitHub)
gh auth setup-git
# Configura automaticamente gh come credential helper
```

### Credential per Host Specifici

```ini
# ~/.gitconfig
[credential "https://github.com"]
    helper = !gh auth git-credential
    username = mariorossi

[credential "https://gitlab.com"]
    helper = store

[credential "https://git.azienda.com"]
    helper = osxkeychain
```

### Token di Accesso Personale

Con l'eliminazione dell'autenticazione via password su GitHub (agosto 2021), i Personal Access Token (PAT) sono il metodo standard per HTTPS:

```bash
# Fine-Grained PAT (raccomandato — permessi granulari per repository)
# Creare su GitHub: Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens

# Classic PAT (deprecating — permessi per scope)
# Settings > Developer Settings > Personal Access Tokens > Tokens (classic)

# Usare il PAT come password durante il primo push
git push origin main
# Username: mariorossi
# Password: github_pat_xxxxxxxxxxxx  (il PAT)

# Alternativa: SSH key (nessun PAT necessario)
git remote set-url origin git@github.com:org/repo.git
```

---

## Configurazione di Editor, Diff e Merge Tool

### Editor

```bash
# VS Code
git config --global core.editor "code --wait"

# Vim
git config --global core.editor vim

# Nano
git config --global core.editor nano

# Sublime Text
git config --global core.editor "subl -n -w"

# IntelliJ IDEA
git config --global core.editor "idea --wait"

# Neovim
git config --global core.editor nvim

# Helix
git config --global core.editor "hx"
```

### Diff Tool

```bash
# Configurare il diff tool
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'

# Meld
git config --global diff.tool meld

# Beyond Compare
git config --global diff.tool bc
git config --global difftool.bc.path "/usr/bin/bcompare"

# Non chiedere conferma prima di aprire il diff tool
git config --global difftool.prompt false

# Uso
git difftool                    # Diff della working directory
git difftool --staged           # Diff dei file staged
git difftool main..feature      # Diff tra branch
```

### Merge Tool

```bash
# VS Code
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'

# Meld
git config --global merge.tool meld

# IntelliJ IDEA
git config --global merge.tool intellij
git config --global mergetool.intellij.cmd 'idea merge $LOCAL $REMOTE $BASE $MERGED'
git config --global mergetool.intellij.trustExitCode true

# Non creare file .orig di backup
git config --global mergetool.keepBackup false

# Non chiedere conferma
git config --global mergetool.prompt false

# Uso durante un conflitto
git mergetool
```

### Pager: delta

`delta` e un pager per diff che offre syntax highlighting, navigazione e diff visivamente migliori:

```bash
# Installare delta
# macOS: brew install git-delta
# Ubuntu: apt install git-delta (o da GitHub releases)
# Arch: pacman -S git-delta

# Configurazione
git config --global core.pager delta
git config --global interactive.diffFilter "delta --color-only"
git config --global delta.navigate true
git config --global delta.side-by-side true
git config --global delta.line-numbers true
git config --global merge.conflictstyle zdiff3
```

### Configurazione Completa di Esempio

```ini
# ~/.gitconfig completo

[user]
    name = Mario Rossi
    email = mario@example.com
    signingkey = ~/.ssh/id_ed25519.pub

[core]
    editor = code --wait
    autocrlf = input
    excludesFile = ~/.gitignore_global
    pager = delta
    fsmonitor = true
    untrackedCache = true

[init]
    defaultBranch = main

[pull]
    rebase = true
    ff = only

[push]
    default = current
    autoSetupRemote = true

[fetch]
    prune = true
    writeCommitGraph = true

[rebase]
    autoSquash = true
    autoStash = true

[merge]
    tool = vscode
    conflictstyle = zdiff3

[mergetool "vscode"]
    cmd = code --wait --merge $REMOTE $LOCAL $BASE $MERGED

[diff]
    tool = vscode
    algorithm = histogram
    colorMoved = default

[difftool "vscode"]
    cmd = code --wait --diff $LOCAL $REMOTE

[rerere]
    enabled = true

[color]
    ui = auto

[commit]
    gpgsign = true

[tag]
    gpgSign = true

[gpg]
    format = ssh

[credential "https://github.com"]
    helper = !gh auth git-credential

[delta]
    navigate = true
    side-by-side = true
    line-numbers = true

[alias]
    st = status -sb
    lg = log --graph --oneline --all --decorate
    co = checkout
    ci = commit
    br = branch
    undo = reset --soft HEAD~1
    last = log -1 HEAD --format='%H %s'
    recent = "!git for-each-ref --sort=-committerdate refs/heads/ --format='%(committerdate:short) %(refname:short)' | head -20"

[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work

[transfer]
    fsckObjects = true
[receive]
    fsckObjects = true
```

---

## .mailmap: Normalizzazione degli Autori

### Cos'e .mailmap

Il file `.mailmap`, posizionato nella root del repository, permette di normalizzare i nomi e gli indirizzi email degli autori mostrati in `git log`, `git shortlog` e `git blame`. E essenziale quando un collaboratore ha cambiato nome, email, o ha committato con identita diverse nel tempo.

### Formato del File

```mailmap
# Formato base: NomeCorretto <EmailCorretta>
# Mappa tutte le entry con quell'email al nome corretto

# Formato 1: Correggere il nome per un'email esistente
Mario Rossi <mario.rossi@azienda.com>
# Tutti i commit con mario.rossi@azienda.com mostreranno "Mario Rossi"

# Formato 2: Correggere nome ed email
Mario Rossi <mario@esempio.it> <mrossi@vecchia-email.com>
# I commit con mrossi@vecchia-email.com mostreranno
# "Mario Rossi <mario@esempio.it>"

# Formato 3: Mappare nome+email vecchi a nome+email nuovi
Mario Rossi <mario@esempio.it> M. Rossi <m.rossi@gmail.com>
# Ogni commit con autore "M. Rossi <m.rossi@gmail.com>" viene
# visualizzato come "Mario Rossi <mario@esempio.it>"

# Formato 4: Solo email (senza cambiare il nome)
<mario@esempio.it> <mrossi@vecchia-email.com>
# Cambia solo l'email, mantiene il nome originale del commit
```

### Esempio Pratico

```mailmap
# .mailmap — Normalizzazione autori del progetto

# Mario ha cambiato email quando ha cambiato azienda
Mario Rossi <mario@nuova-azienda.com> <mario.rossi@vecchia-azienda.com>
Mario Rossi <mario@nuova-azienda.com> <mario@gmail.com>
Mario Rossi <mario@nuova-azienda.com> <mrossi@hotmail.com>

# Giulia ha un errore di battitura nel nome in alcuni commit
Giulia Bianchi <giulia@azienda.com> Giuila Bianchi <giulia@azienda.com>
Giulia Bianchi <giulia@azienda.com> giulia <giulia@azienda.com>

# Bot che si vuole escludere dalle statistiche
# (non si puo escludere con mailmap, ma si puo rinominare)
dependabot[bot] <dependabot@github.com> dependabot-preview[bot] <dependabot-preview@github.com>
```

### Verifica e Utilizzo

```bash
# Verificare che il mailmap funzioni
git shortlog -sn
# Mostra autori consolidati con il mailmap applicato

# Senza mailmap (per confronto)
git shortlog -sn --no-mailmap

# Verificare un mapping specifico
git check-mailmap "M. Rossi <m.rossi@gmail.com>"
# Output: Mario Rossi <mario@esempio.it>

# Utilizzare un mailmap esterno (non nel repository)
git config mailmap.file /path/to/external-mailmap

# Utilizzare un mailmap da un blob nel repository
git config mailmap.blob HEAD:.mailmap
```

### Quando Usare .mailmap

- **Contributori con email multiple**: sviluppatori che committano da diversi ambienti (lavoro, casa, CI)
- **Correzione errori**: nomi con typo, email sbagliate
- **Cambio identita**: matrimonio, cambio azienda, rebranding
- **Unificazione account bot**: bot che hanno cambiato nome/email nelle versioni successive
- **Conformita GDPR**: in teoria si potrebbe anonimizzare, ma il mailmap non modifica i commit — solo la visualizzazione

---

## Git Hooks: Client-Side e Server-Side

### Panoramica del Sistema di Hooks

I Git hooks sono script eseguiti automaticamente in risposta a specifici eventi nel workflow Git. Sono il meccanismo principale per implementare gate di qualita, policy di commit, e automazioni locali senza dipendere da CI/CD esterno.

Gli hooks risiedono nella directory `.git/hooks/` (non versionata per default). Ogni hook e un file eseguibile il cui nome corrisponde all'evento:

```bash
# Struttura hooks
.git/hooks/
├── applypatch-msg.sample
├── commit-msg.sample
├── post-update.sample
├── pre-applypatch.sample
├── pre-commit.sample
├── pre-merge-commit.sample
├── pre-push.sample
├── pre-rebase.sample
├── pre-receive.sample
├── prepare-commit-msg.sample
├── push-to-checkout.sample
└── update.sample

# I file .sample non vengono eseguiti — rimuovere l'estensione per attivarli
```

### Comportamento degli Hooks

- Se un hook **restituisce un exit code non-zero**, l'operazione Git viene **abortita** (per gli hooks "pre-*")
- Gli hooks post-* sono informativi: non possono bloccare l'operazione gia avvenuta
- Gli hooks devono essere **eseguibili**: `chmod +x .git/hooks/pre-commit`
- Possono essere scritti in qualsiasi linguaggio (bash, python, ruby, node, etc.)
- Per default NON sono condivisi (`.git/hooks/` non e versionato)

### Condividere Hooks nel Team

```bash
# Metodo 1: core.hooksPath (Git 2.9+, raccomandato)
# Posizionare gli hooks in una directory versionata
mkdir -p .githooks
git config core.hooksPath .githooks
# Ora Git cerca gli hooks in .githooks/ invece di .git/hooks/

# Ogni membro del team deve eseguire:
git config core.hooksPath .githooks
# Oppure automatizzare con Makefile/script di setup

# Metodo 2: Makefile che copia gli hooks
# Makefile
setup:
    cp scripts/hooks/* .git/hooks/
    chmod +x .git/hooks/*

# Metodo 3: npm post-install (per progetti Node.js)
# package.json
{
  "scripts": {
    "prepare": "cp scripts/hooks/* .git/hooks/ && chmod +x .git/hooks/*"
  }
}
```

---

## Hooks Client-Side in Dettaglio

### pre-commit

Eseguito prima che Git crei il commit. Ideale per linting, formatting e controlli rapidi. Se restituisce non-zero, il commit e abortito.

```bash
#!/bin/bash
# .githooks/pre-commit — Gate di qualita pre-commit

set -euo pipefail

echo "=== Pre-commit checks ==="

# 1. Verifica che non ci siano file con segreti
SECRETS_PATTERN='(password|secret|api_key|private_key|access_token)\s*[:=]\s*["\x27][^"\x27]+'
if git diff --cached --name-only | xargs grep -lEi "$SECRETS_PATTERN" 2>/dev/null; then
    echo "ERRORE: possibili segreti hardcoded nei file staged."
    echo "Rimuovere i segreti e usare variabili d'ambiente."
    exit 1
fi

# 2. Verifica che non ci siano TODO critici
if git diff --cached --diff-filter=ACM | grep -n 'FIXME\|HACK\|XXX'; then
    echo "WARNING: trovati marker critici (FIXME/HACK/XXX)."
    echo "Risolvere prima di committare o usare --no-verify per bypassare."
    exit 1
fi

# 3. Verifica dimensione file
MAX_SIZE=5242880  # 5 MB
while IFS= read -r file; do
    size=$(wc -c < "$file" 2>/dev/null || echo 0)
    if (( size > MAX_SIZE )); then
        echo "ERRORE: $file supera 5 MB ($size bytes). Usare Git LFS."
        exit 1
    fi
done < <(git diff --cached --name-only --diff-filter=ACM)

# 4. Verifica che i file Python rispettino Black
if command -v black &>/dev/null; then
    python_files=$(git diff --cached --name-only --diff-filter=ACM -- '*.py')
    if [[ -n "$python_files" ]]; then
        echo "$python_files" | xargs black --check --quiet 2>/dev/null || {
            echo "ERRORE: file Python non formattati. Eseguire: black ."
            exit 1
        }
    fi
fi

# 5. Verifica che i file JS/TS passino ESLint
if command -v npx &>/dev/null && [[ -f ".eslintrc.js" || -f "eslint.config.js" ]]; then
    js_files=$(git diff --cached --name-only --diff-filter=ACM -- '*.js' '*.ts' '*.tsx' '*.jsx')
    if [[ -n "$js_files" ]]; then
        echo "$js_files" | xargs npx eslint --quiet || {
            echo "ERRORE: ESLint ha trovato errori."
            exit 1
        }
    fi
fi

echo "=== Pre-commit checks passed ==="
```

### prepare-commit-msg

Eseguito dopo che Git crea il messaggio di commit predefinito ma prima che l'editor si apra. Permette di manipolare il messaggio proposto. Riceve come argomento il path del file contenente il messaggio.

```bash
#!/bin/bash
# .githooks/prepare-commit-msg
# Aggiunge il nome del branch come prefisso al messaggio

COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="$2"

# Non modificare merge commits o amend
if [[ "$COMMIT_SOURCE" == "merge" ]] || [[ "$COMMIT_SOURCE" == "squash" ]]; then
    exit 0
fi

# Estrai ticket dal nome del branch (es. feature/JIRA-123-descrizione)
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
TICKET=$(echo "$BRANCH" | grep -oP '[A-Z]+-\d+' | head -1)

if [[ -n "$TICKET" ]]; then
    # Aggiungi il ticket solo se non e gia presente
    if ! grep -q "$TICKET" "$COMMIT_MSG_FILE"; then
        sed -i "1s/^/[$TICKET] /" "$COMMIT_MSG_FILE"
    fi
fi
```

### commit-msg

Eseguito dopo che l'utente ha scritto il messaggio di commit. Usato per validare il formato del messaggio. Riceve il path del file con il messaggio.

```bash
#!/bin/bash
# .githooks/commit-msg — Valida il formato Conventional Commits

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Pattern Conventional Commits
PATTERN='^(feat|fix|refactor|docs|test|chore|perf|ci|build|style|revert)(\(.+\))?: .{3,}'

# Ignora merge commits
if echo "$COMMIT_MSG" | head -1 | grep -qP '^Merge '; then
    exit 0
fi

# Valida la prima riga
FIRST_LINE=$(head -1 "$COMMIT_MSG_FILE")

if ! echo "$FIRST_LINE" | grep -qP "$PATTERN"; then
    echo ""
    echo "ERRORE: Il messaggio di commit non segue il formato Conventional Commits."
    echo ""
    echo "Formato atteso: <tipo>[(scope)]: <descrizione>"
    echo ""
    echo "Tipi validi: feat, fix, refactor, docs, test, chore, perf, ci, build, style, revert"
    echo ""
    echo "Esempi:"
    echo "  feat: aggiungere autenticazione OAuth2"
    echo "  fix(auth): correggere validazione token scaduto"
    echo "  docs: aggiornare guida installazione"
    echo ""
    echo "Il tuo messaggio: $FIRST_LINE"
    echo ""
    exit 1
fi

# Verifica lunghezza prima riga (max 72 caratteri)
if (( ${#FIRST_LINE} > 72 )); then
    echo "ERRORE: La prima riga del commit supera 72 caratteri (${#FIRST_LINE})."
    echo "Abbreviare il messaggio o spostare dettagli nel body."
    exit 1
fi
```

### pre-push

Eseguito prima del push al remote. Riceve il nome e l'URL del remote su stdin. Ideale per eseguire test prima di pushare.

```bash
#!/bin/bash
# .githooks/pre-push — Verifica prima del push

REMOTE="$1"
URL="$2"

echo "=== Pre-push checks (remote: $REMOTE) ==="

# 1. Non pushare direttamente a main/master
while read -r local_ref local_sha remote_ref remote_sha; do
    if echo "$remote_ref" | grep -qP 'refs/heads/(main|master)$'; then
        echo "ERRORE: push diretto a main/master non consentito."
        echo "Creare una PR invece."
        exit 1
    fi
done

# 2. Eseguire i test prima del push (se non troppo lenti)
if [[ -f "package.json" ]] && grep -q '"test"' package.json; then
    echo "Esecuzione test..."
    npm test --silent || {
        echo "ERRORE: i test falliscono. Correggere prima di pushare."
        exit 1
    }
fi

echo "=== Pre-push checks passed ==="
```

### post-commit, post-checkout, post-merge

Hooks informativi che non possono bloccare l'operazione ma sono utili per notifiche e side-effects:

```bash
#!/bin/bash
# .githooks/post-commit — Notifica dopo commit

COMMIT_MSG=$(git log -1 --format='%s')
AUTHOR=$(git log -1 --format='%an')
echo "Commit creato: $COMMIT_MSG (by $AUTHOR)"

# Aggiornare ctags dopo un commit (per navigazione IDE)
if command -v ctags &>/dev/null; then
    ctags -R --exclude=node_modules --exclude=.git &
fi
```

```bash
#!/bin/bash
# .githooks/post-checkout — Azioni dopo checkout

PREV_HEAD="$1"
NEW_HEAD="$2"
BRANCH_CHECKOUT="$3"  # 1 se branch checkout, 0 se file checkout

if [[ "$BRANCH_CHECKOUT" == "1" ]]; then
    # Reinstallare dipendenze se il lockfile e cambiato
    if ! git diff --quiet "$PREV_HEAD" "$NEW_HEAD" -- package-lock.json 2>/dev/null; then
        echo "package-lock.json cambiato. Reinstallazione dipendenze..."
        npm ci
    fi

    if ! git diff --quiet "$PREV_HEAD" "$NEW_HEAD" -- requirements.txt 2>/dev/null; then
        echo "requirements.txt cambiato. Reinstallazione dipendenze..."
        pip install -r requirements.txt
    fi
fi
```

---

## Hooks Server-Side in Dettaglio

Gli hooks server-side vengono eseguiti sul server che riceve il push (es. un bare repository o una piattaforma come GitLab self-hosted). Sono il meccanismo per implementare policy aziendali.

### pre-receive

Eseguito una volta prima di accettare qualsiasi ref pushato. Riceve le ref su stdin. Se restituisce non-zero, **tutti** i push vengono rifiutati.

```bash
#!/bin/bash
# hooks/pre-receive — Policy server-side

while read -r old_sha new_sha ref; do
    # 1. Bloccare force-push a branch protetti
    if echo "$ref" | grep -qP 'refs/heads/(main|master|release/.*)$'; then
        if [[ "$old_sha" != "0000000000000000000000000000000000000000" ]]; then
            # Verifica che il nuovo SHA sia un discendente del vecchio
            if ! git merge-base --is-ancestor "$old_sha" "$new_sha" 2>/dev/null; then
                echo "ERRORE: force-push a $ref non consentito."
                echo "Usare una Pull Request per modificare branch protetti."
                exit 1
            fi
        fi
    fi

    # 2. Verifica dimensione massima dei file
    if [[ "$new_sha" != "0000000000000000000000000000000000000000" ]]; then
        MAX_SIZE=10485760  # 10 MB
        while IFS= read -r line; do
            sha=$(echo "$line" | awk '{print $1}')
            size=$(git cat-file -s "$sha" 2>/dev/null || echo 0)
            if (( size > MAX_SIZE )); then
                path=$(echo "$line" | awk '{print $4}')
                echo "ERRORE: il file $path supera 10 MB ($size bytes)."
                echo "Usare Git LFS per file grandi."
                exit 1
            fi
        done < <(git diff --raw "$old_sha" "$new_sha" 2>/dev/null | grep -v '^:' || true)
    fi

    # 3. Verifica formato commit message
    if [[ "$new_sha" != "0000000000000000000000000000000000000000" ]]; then
        git log "$old_sha..$new_sha" --format='%s' 2>/dev/null | while read -r msg; do
            if ! echo "$msg" | grep -qP '^(feat|fix|refactor|docs|test|chore|perf|ci)'; then
                if ! echo "$msg" | grep -qP '^Merge '; then
                    echo "ERRORE: commit message non segue Conventional Commits: $msg"
                    exit 1
                fi
            fi
        done
    fi
done
```

### update

Simile a pre-receive ma eseguito **per ogni ref** individualmente. Permette di accettare alcune ref e rifiutarne altre nello stesso push.

```bash
#!/bin/bash
# hooks/update — Policy per-ref

REF="$1"
OLD_SHA="$2"
NEW_SHA="$3"

# Bloccare eliminazione di tag
if echo "$REF" | grep -q 'refs/tags/' && [[ "$NEW_SHA" == "0000000000000000000000000000000000000000" ]]; then
    echo "ERRORE: eliminazione di tag non consentita su questo server."
    exit 1
fi

# Bloccare push a branch "archived/*"
if echo "$REF" | grep -q 'refs/heads/archived/'; then
    echo "ERRORE: il branch $REF e archiviato e non accetta push."
    exit 1
fi

exit 0  # Accetta questa ref
```

### post-receive

Eseguito dopo che tutti i ref sono stati aggiornati. Non puo rifiutare il push. Usato per notifiche, deploy, trigger CI.

```bash
#!/bin/bash
# hooks/post-receive — Azioni post-push

while read -r old_sha new_sha ref; do
    BRANCH=$(echo "$ref" | sed 's|refs/heads/||')

    # Deploy automatico se push a main
    if [[ "$BRANCH" == "main" ]]; then
        echo "=== Deploy automatico a produzione ==="
        GIT_WORK_TREE=/var/www/app git checkout -f main
        cd /var/www/app && ./deploy.sh
    fi

    # Notifica Slack
    AUTHOR=$(git log -1 --format='%an' "$new_sha")
    COMMITS=$(git log "$old_sha..$new_sha" --oneline | wc -l)
    curl -s -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\": \"$AUTHOR ha pushato $COMMITS commit a $BRANCH\"}"
done
```

---

## Hooks con Husky e lint-staged

Per progetti Node.js, Husky e lo standard de facto per gestire Git hooks in modo versionato e portabile.

### Setup Husky (v9+)

```bash
# Installare Husky
npm install --save-dev husky

# Inizializzare
npx husky init
# Crea la directory .husky/ e configura prepare script

# Il file .husky/pre-commit viene creato con contenuto di default
```

```json
// package.json (dopo husky init)
{
  "scripts": {
    "prepare": "husky"
  }
}
```

### Configurazione Hooks con Husky

```bash
# .husky/pre-commit
npx lint-staged

# .husky/commit-msg
npx commitlint --edit "$1"

# .husky/pre-push
npm test
```

### lint-staged: Linting Solo dei File Staged

lint-staged esegue linter/formatter solo sui file che stanno per essere committati, riducendo drasticamente i tempi:

```bash
npm install --save-dev lint-staged
```

```json
// package.json
{
  "lint-staged": {
    "*.{js,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,scss}": [
      "stylelint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml}": [
      "prettier --write"
    ],
    "*.py": [
      "black",
      "ruff check --fix"
    ]
  }
}
```

### commitlint: Validazione Messaggi

```bash
npm install --save-dev @commitlint/{cli,config-conventional}

# Creare configurazione
echo "export default { extends: ['@commitlint/config-conventional'] };" > commitlint.config.js
```

```javascript
// commitlint.config.js — configurazione avanzata
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'refactor', 'docs', 'test',
      'chore', 'perf', 'ci', 'build', 'style', 'revert'
    ]],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [1, 'always', 100],
    'scope-enum': [1, 'always', ['auth', 'api', 'ui', 'db', 'ci']],
  }
};
```

---

## Template .gitignore Completi per Linguaggio

La sezione seguente fornisce template `.gitignore` completi e annotati per i principali linguaggi e framework. Ogni template e stato compilato a partire dai repository ufficiali GitHub (`github/gitignore`), dalla documentazione dei framework e dalle best practice consolidate della community. I commenti spiegano la ragione di ogni pattern per facilitare la personalizzazione.

### Python — Django / Flask / FastAPI

```gitignore
# ============================
# Python .gitignore completo
# Django, Flask, FastAPI, Celery
# ============================

# --- Byte-compiled / optimized / DLL ---
__pycache__/
*.py[cod]
*$py.class

# --- C extensions compilate ---
*.so

# --- Distribuzione / packaging ---
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# --- PyInstaller ---
*.manifest
*.spec

# --- Installer logs ---
pip-log.txt
pip-delete-this-directory.txt

# --- Test e copertura ---
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# --- Traduzioni (compilate) ---
*.mo
*.pot

# --- Virtual environments ---
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.python-version

# --- Pyenv ---
.python-version

# --- pipenv / poetry ---
Pipfile.lock            # Opzionale: versionare in progetti applicativi
# poetry.lock           # Versionare per applicazioni, ignorare per librerie

# --- Celery ---
celerybeat-schedule
celerybeat.pid

# --- SageMath ---
*.sage.py

# --- Spyder IDE ---
.spyderproject
.spyproject

# --- Rope ---
.ropeproject

# --- mkdocs ---
/site

# --- mypy / pyright ---
.mypy_cache/
.dmypy.json
dmypy.json
.pyright/
pyrightconfig.json

# --- ruff ---
.ruff_cache/

# --- Jupyter Notebook ---
.ipynb_checkpoints

# === Django-specific ===
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/
static_collected/
*.pot

# === Flask-specific ===
instance/
.webassets-cache

# === FastAPI-specific ===
# Nessun pattern addizionale rispetto a Python base

# --- Ambiente e segreti ---
.env
.env.local
.env.*.local
.env.production
.flaskenv
*.pem
*.key
*.crt
credentials.json
service-account*.json
```

### Node.js — React / Next.js / TypeScript / Vue

```gitignore
# ============================
# Node.js .gitignore completo
# React, Next.js, Vue, Angular, TypeScript
# ============================

# --- Dipendenze ---
node_modules/
.pnp
.pnp.js
.pnp.cjs
.pnp.loader.mjs

# --- Testing ---
coverage/
*.lcov
.nyc_output

# --- Next.js ---
.next/
out/

# --- Nuxt.js ---
.nuxt
dist

# --- Gatsby ---
.cache/
public

# --- Vue.js ---
.vue-press
.vuepress/dist

# --- Angular ---
.angular/

# --- Build generici ---
build/
dist/
*.tsbuildinfo

# --- Turbo ---
.turbo

# --- Vercel ---
.vercel

# --- TypeScript ---
*.tsbuildinfo
next-env.d.ts

# --- Cache e temp ---
.eslintcache
.stylelintcache
*.swp
*.swo
*~

# --- Debug log ---
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.pnpm-store/
lerna-debug.log*

# --- Lock files (nota: versionare il lockfile del package manager scelto) ---
# NON ignorare package-lock.json o yarn.lock o pnpm-lock.yaml
# Ignorare quelli degli altri package manager se ne usate uno solo

# --- Ambiente e segreti ---
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
!.env.example

# --- Storybook ---
storybook-static

# --- PWA ---
sw.*
workbox-*

# --- Misc ---
*.pid
*.seed
*.pid.lock

# --- Sentry ---
.sentryclirc

# --- Playwright ---
/test-results/
/playwright-report/
/blob-report/
/playwright/.cache/
```

### Java / Kotlin — Spring Boot / Gradle / Maven

```gitignore
# ============================
# Java / Kotlin .gitignore completo
# Spring Boot, Gradle, Maven, JPA
# ============================

# --- Compilati ---
*.class
*.jar
*.war
*.ear
*.nar

# --- Maven ---
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties
.mvn/wrapper/maven-wrapper.jar

# --- Gradle ---
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar
!gradle/wrapper/gradle-wrapper.properties
!**/src/main/**/build/
!**/src/test/**/build/

# --- Kotlin ---
*.kotlin_module

# --- Spring Boot ---
application-local.yml
application-local.properties
application-secrets.yml
*.log

# --- IDE: IntelliJ IDEA ---
.idea/
*.iml
*.iws
*.ipr
out/
# Nota: NON ignorare .idea/codeStyles o .idea/inspectionProfiles
# se il team vuole condividere le configurazioni di stile

# --- IDE: Eclipse ---
.project
.classpath
.settings/
bin/

# --- IDE: NetBeans ---
/nbproject/private/
/nbbuild/
/dist/
/nbdist/
/.nb-gradle/

# --- IDE: VS Code ---
.vscode/
*.code-workspace

# --- Ambiente ---
.env
*.pem
*.key
*.jks
*.p12
truststore.jks
keystore.jks

# --- Wrapper ---
# I file del wrapper Gradle/Maven DEVONO essere versionati
# per garantire build riproducibili. Non ignorarli.

# --- Test ---
/test-output/
*.exec
```

### Go (Golang)

```gitignore
# ============================
# Go .gitignore completo
# ============================

# --- Binari ---
# I binari Go vengono compilati senza estensione su Unix
# e con .exe su Windows
*.exe
*.exe~
*.dll
*.so
*.dylib

# --- Directory di output ---
/bin/
/out/

# --- Test ---
*.test
*.out
coverage.txt
coverage.html
*.coverprofile

# --- Vendor (opzionale) ---
# Versionare vendor/ se si usa vendoring esplicito
# Ignorare se si usa il module proxy
# vendor/

# --- Go workspace ---
go.work
go.work.sum

# --- Profiling ---
*.prof
*.pprof
*.trace
cpu.out
mem.out
trace.out

# --- CGo ---
_cgo_defun.c
_cgo_gotypes.go
_cgo_export.*
_testmain.go

# --- Ambiente ---
.env
.env.local
*.pem

# --- Tool output ---
.golangci-lint-cache/
```

### Rust

```gitignore
# ============================
# Rust .gitignore completo
# ============================

# --- Build output ---
/target/
debug/
release/

# --- Cargo.lock ---
# VERSIONARE per binari e applicazioni
# IGNORARE per librerie (crate)
# Cargo.lock

# --- Backup files ---
**/*.rs.bk
*.pdb

# --- IDE ---
.idea/
.vscode/
*.swp
*.swo

# --- Profiling ---
flamegraph.svg
perf.data
perf.data.old

# --- Ambiente ---
.env
.env.local

# --- Coverage ---
*.profraw
*.profdata
tarpaulin-report.html
lcov.info
```

### C / C++ con CMake

```gitignore
# ============================
# C/C++ con CMake .gitignore completo
# ============================

# --- Prerequisiti ---
*.d

# --- Oggetti compilati ---
*.slo
*.lo
*.o
*.obj

# --- Oggetti precompilati ---
*.gch
*.pch

# --- Librerie compilate ---
*.lib
*.a
*.la
*.lai

# --- Shared objects ---
*.dll
*.so
*.so.*
*.dylib

# --- Eseguibili ---
*.exe
*.out
*.app

# --- CMake ---
CMakeLists.txt.user
CMakeCache.txt
CMakeFiles/
CMakeScripts/
Testing/
Makefile
cmake_install.cmake
install_manifest.txt
compile_commands.json
CTestTestfile.cmake
_deps/
cmake-build-*/

# --- Build directory ---
build/
out/
Build/

# --- Package config ---
*.pc

# --- Conan ---
conan/
conanbuildinfo.*
conaninfo.txt
graph_info.json

# --- vcpkg ---
vcpkg_installed/

# --- IDE: CLion ---
.idea/
cmake-build-debug/
cmake-build-release/

# --- Coverage ---
*.gcno
*.gcda
*.gcov
```

### PHP / Laravel / Symfony

```gitignore
# ============================
# PHP .gitignore completo
# Laravel, Symfony, WordPress
# ============================

# --- Dipendenze ---
/vendor/

# --- Ambiente ---
.env
.env.backup
.env.production
!.env.example

# --- Laravel ---
/public/hot
/public/storage
/storage/*.key
/storage/framework/cache/data/*
/storage/framework/sessions/*
/storage/framework/views/*
/storage/logs/*
/bootstrap/cache/*
Homestead.json
Homestead.yaml
auth.json
npm-debug.log
yarn-error.log
/.fleet
/.idea
/.vscode

# --- Symfony ---
/var/
/vendor/
/.env.local
/.env.local.php
/.env.*.local
/config/secrets/prod/prod.decrypt.private.php
/public/bundles/

# --- Composer ---
composer.phar

# --- PHPUnit ---
.phpunit.result.cache
.phpunit.cache/

# --- PHP CS Fixer ---
.php-cs-fixer.cache
.php_cs.cache

# --- PHPStan ---
phpstan-baseline.neon

# --- IDE ---
.idea/
.vscode/
*.swp
```

### Swift / iOS / macOS (Xcode)

```gitignore
# ============================
# Swift / iOS .gitignore completo
# Xcode, SwiftPM, CocoaPods
# ============================

# --- Xcode ---
build/
DerivedData/
*.pbxuser
!default.pbxuser
*.mode1v3
!default.mode1v3
*.mode2v3
!default.mode2v3
*.perspectivev3
!default.perspectivev3
xcuserdata/
*.moved-aside
*.xccheckout
*.xcscmblueprint
*.xcworkspace
!default.xcworkspace

# --- Swift Package Manager ---
.build/
.swiftpm/
Packages/
Package.resolved

# --- CocoaPods ---
Pods/
!Podfile.lock

# --- Carthage ---
Carthage/Build/
Carthage/Checkouts/

# --- Fastlane ---
fastlane/report.xml
fastlane/Preview.html
fastlane/screenshots/**/*.png
fastlane/test_output

# --- Code injection ---
iOSInjectionProject/

# --- Playgrounds ---
timeline.xctimeline
playground.xcworkspace

# --- Profiling ---
*.gcno
*.gcda
```

### Android / Kotlin Multiplatform

```gitignore
# ============================
# Android .gitignore completo
# Android Studio, Gradle, Kotlin
# ============================

# --- Gradle ---
*.iml
.gradle/
/local.properties
/.idea/caches
/.idea/libraries
/.idea/modules.xml
/.idea/workspace.xml
/.idea/navEditor.xml
/.idea/assetWizardSettings.xml
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
local.properties

# --- Android Studio ---
*.apk
*.aab
*.ap_
*.dex
*.class
/gen/
/out/

# --- Proguard ---
proguard/

# --- Log ---
*.log

# --- Signing ---
*.jks
*.keystore
signing.properties
keystore.properties

# --- Firebase ---
google-services.json      # NON committare se contiene chiavi sensibili

# --- Kotlin Multiplatform ---
.kotlin/
kotlin-js-store/
```

### Docker / DevOps / Terraform

```gitignore
# ============================
# Docker / DevOps .gitignore completo
# Docker, Kubernetes, Terraform, Ansible
# ============================

# --- Docker ---
# Di norma NON si ignora il Dockerfile
# Ma si ignorano file temporanei Docker
docker-compose.override.yml
.docker/

# --- Terraform ---
# Directory di stato locale
.terraform/
.terraform.lock.hcl

# File di stato (CONTENGONO SEGRETI)
*.tfstate
*.tfstate.*
*.tfstate.backup

# Piano di esecuzione
*.tfplan

# Override locali
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Variabili con segreti
*.auto.tfvars
terraform.tfvars    # Ignorare solo se contiene segreti

# Crash log
crash.log
crash.*.log

# --- Kubernetes ---
# Ignorare file di configurazione con segreti
*-secret.yaml
*.kubeconfig

# --- Ansible ---
*.retry
inventory/*_private
vault-password

# --- Helm ---
charts/*.tgz

# --- CI/CD ---
# Di norma i file CI (.github/workflows/, .gitlab-ci.yml) si versionano
# Ignorare solo artefatti locali
.act/
```

### Unity (Game Development)

```gitignore
# ============================
# Unity .gitignore completo
# ============================

# --- Directory generate ---
/[Ll]ibrary/
/[Tt]emp/
/[Oo]bj/
/[Bb]uild/
/[Bb]uilds/
/[Ll]ogs/
/[Uu]ser[Ss]ettings/

# --- MemoryCaptures ---
/[Mm]emoryCaptures/

# --- Recordings ---
/[Rr]ecordings/

# --- Asset Store Tools ---
/[Aa]sset[Ss]tore[Tt]ools*/

# --- Autogenerated VS/MD/Rider solution ---
ExportedObj/
.consulo/
*.csproj
*.unityproj
*.sln
*.suo
*.tmp
*.user
*.userprefs
*.pidb
*.booproj
*.svd
*.pdb
*.mdb
*.opendb
*.VC.db

# --- Unity3D generated meta ---
*.pidb.meta
*.pdb.meta
*.mdb.meta

# --- Sysinfo ---
sysinfo.txt

# --- Crashlytics ---
crashlytics-build.properties

# --- Builds ---
*.apk
*.aab
*.unitypackage
*.app

# --- Plastic SCM ---
ignore.conf
*.private.0
*.private
```

### Unreal Engine (C++)

```gitignore
# ============================
# Unreal Engine .gitignore completo
# UE5 / UE4
# ============================

# --- Directory generate localmente ---
Binaries/
DerivedDataCache/
Intermediate/
Saved/
Build/

# --- Visual Studio ---
.vs/
*.sln
*.suo
*.opensdf
*.sdf
*.VC.db
*.VC.opendb

# --- Rider ---
.idea/

# --- Compilati ---
*.pdb
*.obj

# --- Asset cache ---
*.VC.db.lock

# --- Cartelle piattaforma ---
/Platforms/
# Decommentare per ignorare piattaforme specifiche:
# /Platforms/Android/
# /Platforms/IOS/

# NOTA: per progetti Unreal Engine e fortemente consigliato
# usare Git LFS per i file .uasset e .umap (vedere la sezione
# "Git LFS con .gitattributes" piu avanti)
```

---

## Git LFS con .gitattributes — Guida Completa

Git Large File Storage (LFS) e un'estensione di Git progettata per gestire file di grandi dimensioni — asset grafici, video, dataset, modelli 3D — sostituendoli nel repository con piccoli file di puntamento (pointer) e memorizzando il contenuto effettivo su un server remoto dedicato. La configurazione di LFS avviene interamente tramite `.gitattributes`.

### Installazione e Setup Iniziale

```bash
# Installare Git LFS
# macOS
brew install git-lfs

# Ubuntu/Debian
sudo apt install git-lfs

# Windows (con Chocolatey)
choco install git-lfs

# Inizializzare Git LFS per l'utente corrente
git lfs install
# Installa gli hook necessari (pre-push, post-checkout, post-commit, post-merge)

# Inizializzare in un repository specifico
cd /path/to/repo
git lfs install --local
```

### Tracking dei File con git lfs track

Il comando `git lfs track` aggiunge le entry necessarie in `.gitattributes`. E fondamentale eseguirlo **prima** di committare i file grandi per evitare la necessita di migrazioni successive.

```bash
# Tracciare per estensione (metodo raccomandato)
git lfs track "*.psd"
git lfs track "*.png"
git lfs track "*.jpg"
git lfs track "*.mp4"
git lfs track "*.zip"
git lfs track "*.fbx"
git lfs track "*.blend"

# Tracciare per directory
git lfs track "assets/videos/**"
git lfs track "data/models/**"

# Tracciare un file specifico
git lfs track "data/large-dataset.csv"

# Visualizzare i pattern tracciati
git lfs track
# Listing tracked patterns
#     *.psd (.gitattributes)
#     *.png (.gitattributes)

# Smettere di tracciare
git lfs untrack "*.png"

# Verificare lo stato LFS
git lfs status
git lfs ls-files              # File attualmente gestiti da LFS
git lfs ls-files --all        # Tutti i file LFS nell'intera storia
```

### Struttura .gitattributes per LFS

Quando si esegue `git lfs track`, il `.gitattributes` viene aggiornato con un formato specifico:

```gitattributes
# ============================
# Git LFS Tracking
# ============================

# --- Immagini ---
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text
*.psd filter=lfs diff=lfs merge=lfs -text
*.ai filter=lfs diff=lfs merge=lfs -text
*.svg filter=lfs diff=lfs merge=lfs -text
*.ico filter=lfs diff=lfs merge=lfs -text
*.tiff filter=lfs diff=lfs merge=lfs -text
*.bmp filter=lfs diff=lfs merge=lfs -text
*.webp filter=lfs diff=lfs merge=lfs -text
*.avif filter=lfs diff=lfs merge=lfs -text

# --- Video ---
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text
*.webm filter=lfs diff=lfs merge=lfs -text

# --- Audio ---
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text

# --- Font ---
*.woff filter=lfs diff=lfs merge=lfs -text
*.woff2 filter=lfs diff=lfs merge=lfs -text
*.ttf filter=lfs diff=lfs merge=lfs -text
*.otf filter=lfs diff=lfs merge=lfs -text
*.eot filter=lfs diff=lfs merge=lfs -text

# --- Archivi ---
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
*.rar filter=lfs diff=lfs merge=lfs -text

# --- 3D / Game ---
*.fbx filter=lfs diff=lfs merge=lfs -text
*.blend filter=lfs diff=lfs merge=lfs -text
*.obj filter=lfs diff=lfs merge=lfs -text
*.uasset filter=lfs diff=lfs merge=lfs -text
*.umap filter=lfs diff=lfs merge=lfs -text
*.unity filter=lfs diff=lfs merge=lfs -text
*.prefab filter=lfs diff=lfs merge=lfs -text

# --- Dataset ---
*.csv filter=lfs diff=lfs merge=lfs -text
*.parquet filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.hdf5 filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.model filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text

# --- Documenti ---
*.pdf filter=lfs diff=lfs merge=lfs -text
*.docx filter=lfs diff=lfs merge=lfs -text
*.xlsx filter=lfs diff=lfs merge=lfs -text
*.pptx filter=lfs diff=lfs merge=lfs -text
```

Ogni entry LFS specifica quattro attributi:
- **`filter=lfs`**: attiva il filtro clean/smudge di LFS (sostituisce il contenuto con un pointer al commit e lo ripristina al checkout)
- **`diff=lfs`**: usa il diff driver di LFS per mostrare le differenze
- **`merge=lfs`**: usa il merge driver di LFS durante i merge
- **`-text`**: disabilita la normalizzazione dei line endings (critico per i binari)

### Migrazione di File Esistenti a LFS

Se file grandi sono gia stati committati senza LFS, e necessario migrare la storia:

```bash
# Analizzare quali file beneficerebbero di LFS
git lfs migrate info --everything
# Output:
# migrate: Sorting commits: ..., done.
# migrate: Examining commits: 100% (1230/1230), done.
# *.psd   524 MB    12/12 files(s)  100%
# *.png   128 MB   245/245 files(s)  100%
# *.mp4    89 MB     3/3 files(s)   100%

# Analizzare solo file sopra una certa dimensione
git lfs migrate info --everything --above=5mb

# Migrare file specifici (RISCRIVE LA STORIA!)
git lfs migrate import --everything --include="*.psd,*.png,*.mp4"
# ATTENZIONE: tutti i commit hash cambiano.
# Tutti i collaboratori devono ri-clonare il repository.

# Migrazione con --fixup (usa i pattern da .gitattributes corrente)
git lfs migrate import --fixup
# Converte solo i file che .gitattributes dice dovrebbero essere LFS
# ma che attualmente non sono pointer LFS

# Migrazione solo di branch specifici
git lfs migrate import --include="*.psd" --include-ref=refs/heads/main

# Verificare la migrazione
git lfs ls-files
```

### File Locking con LFS

Per file binari che non possono essere mergiati (PSD, DOCX, asset 3D), Git LFS offre un meccanismo di file locking:

```bash
# Configurare il locking
git lfs install

# Dichiarare file come lockable in .gitattributes
# I file lockable diventano read-only nel working tree fino al lock
echo '*.psd lockable' >> .gitattributes
echo '*.blend lockable' >> .gitattributes

# Ottenere il lock su un file
git lfs lock assets/hero-banner.psd
# Locked assets/hero-banner.psd

# Visualizzare i lock attivi
git lfs locks
# ID    Path                        Owner        Locked At
# 1     assets/hero-banner.psd      mariorossi   2026-05-24T10:30:00Z

# Rilasciare il lock
git lfs unlock assets/hero-banner.psd

# Forzare il rilascio (admin)
git lfs unlock assets/hero-banner.psd --force

# Verificare lock prima del push (automatico con l'hook pre-push di LFS)
git lfs pre-push
```

### Ottimizzazione LFS in CI/CD

In ambienti CI/CD, spesso non e necessario scaricare i file LFS effettivi (es. i test non hanno bisogno delle immagini):

```bash
# Clonare senza scaricare i file LFS (variabile d'ambiente)
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/org/repo.git

# Scaricare selettivamente solo i file LFS necessari
git lfs pull --include="src/assets/icons/**"
git lfs pull --exclude="*.mp4,*.mov"

# Configurare fetch include/exclude a livello di repo
git config lfs.fetchinclude "src/assets/**"
git config lfs.fetchexclude "data/training/**,*.mp4"

# Verificare la dimensione dello storage LFS
git lfs env
```

### Best Practice LFS

1. **Configurare LFS prima del primo commit di file grandi** — migrare successivamente riscrive la storia e richiede ri-clone da parte di tutti i collaboratori.

2. **Non tracciare file auto-generati con LFS** — artefatti di build, binari compilati e asset generati dovrebbero stare in `.gitignore`, non in LFS. LFS e per asset sorgente creati da esseri umani.

3. **Raggruppare i pattern per tipo** — organizzare le entry LFS nel `.gitattributes` in sezioni logiche (immagini, video, font, dataset) per facilitare la manutenzione.

4. **Usare `lockable` per file non mergiabili** — previene conflitti su file binari che non possono essere risolti con merge a tre vie.

5. **Ottimizzare CI/CD con `GIT_LFS_SKIP_SMUDGE`** — risparmiare banda e tempo nei pipeline dove i file LFS non sono necessari.

6. **Mantenere il `.gitattributes` nella root** — eseguire sempre `git lfs track` dalla root del repository per centralizzare i pattern.

---

## Firma dei Commit con SSH e GPG — Guida Completa

La firma crittografica dei commit garantisce l'autenticita e l'integrita delle modifiche. A partire da Git 2.34, e possibile firmare i commit con chiavi SSH (oltre a GPG), semplificando enormemente il processo poiche la maggior parte degli sviluppatori possiede gia una chiave SSH.

### Firma con Chiave SSH (Raccomandato dal 2024)

La firma SSH e diventata il metodo preferito per la sua semplicita: non richiede l'installazione di GPG, non necessita di un keyserver, e usa le stesse chiavi gia impiegate per l'autenticazione Git.

#### Configurazione

```bash
# 1. Generare una chiave SSH dedicata alla firma (opzionale ma consigliato)
#    Si puo usare la stessa chiave usata per autenticazione
ssh-keygen -t ed25519 -C "mario@esempio.it" -f ~/.ssh/id_sign_ed25519

# 2. Configurare Git per usare SSH come formato di firma
git config --global gpg.format ssh

# 3. Specificare la chiave pubblica per la firma
git config --global user.signingkey ~/.ssh/id_sign_ed25519.pub

# 4. Abilitare la firma automatica per tutti i commit
git config --global commit.gpgsign true

# 5. Abilitare la firma automatica per tutti i tag
git config --global tag.gpgSign true
```

#### File allowed_signers per la Verifica Locale

Per verificare le firme SSH localmente, Git necessita di un file `allowed_signers` che mappa email a chiavi pubbliche:

```bash
# 1. Creare il file allowed_signers
mkdir -p ~/.config/git

# Formato: email namespaces="git" tipo-chiave chiave-pubblica
cat > ~/.config/git/allowed_signers << 'EOF'
mario@esempio.it namespaces="git" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
giulia@azienda.com namespaces="git" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
bot@ci.azienda.com namespaces="git" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
EOF

# 2. Configurare Git per usare il file
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers

# 3. Verificare una firma
git log --show-signature -1
# commit abc1234 (HEAD -> main)
# Good "git" signature for mario@esempio.it with ED25519 key SHA256:xxxx
# Author: Mario Rossi <mario@esempio.it>

# 4. Verificare un tag firmato
git tag -v v1.0.0
```

#### Registrare la Chiave su GitHub/GitLab

```bash
# GitHub — aggiungere come "Signing Key" (non "Authentication Key")
# Settings > SSH and GPG keys > New SSH key > Key type: Signing Key

# Copiare la chiave pubblica
cat ~/.ssh/id_sign_ed25519.pub | pbcopy    # macOS
cat ~/.ssh/id_sign_ed25519.pub | xclip     # Linux

# GitLab — aggiungere con usage type "Signing"
# Preferences > SSH Keys > Usage type: Signing (or Authentication & Signing)

# Verificare che i commit mostrino "Verified" su GitHub
git log --show-signature
```

#### Usare la Stessa Chiave per Autenticazione e Firma

```bash
# Se si vuole usare una sola chiave per entrambi gli scopi
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global gpg.format ssh
git config --global commit.gpgsign true

# La chiave deve essere registrata su GitHub sia come
# Authentication key sia come Signing key
```

### Firma con GPG (Metodo Tradizionale)

GPG offre funzionalita che SSH non ha: scadenza delle chiavi, revoca, e una rete di fiducia (web of trust). Rimane il metodo preferito in contesti aziendali con infrastruttura PKI.

#### Configurazione GPG

```bash
# 1. Generare una chiave GPG
gpg --full-generate-key
# Scegliere: (1) RSA and RSA, 4096 bit, scadenza 1-2 anni
# Inserire nome ed email (deve corrispondere alla email Git)

# 2. Trovare l'ID della chiave
gpg --list-secret-keys --keyid-format=long
# sec   rsa4096/3AA5C34371567BD2 2026-05-24 [SC] [scade: 2028-05-24]
#       ABCDEF1234567890ABCDEF1234567890ABCDEF12
# uid           [ultimate] Mario Rossi <mario@esempio.it>
# ssb   rsa4096/42B317FD4BA89E7A 2026-05-24 [E]

# L'ID della chiave e "3AA5C34371567BD2" (dopo rsa4096/)

# 3. Configurare Git
git config --global gpg.format openpgp   # default, puo essere omesso
git config --global user.signingkey 3AA5C34371567BD2
git config --global commit.gpgsign true
git config --global tag.gpgSign true

# 4. Esportare la chiave pubblica per GitHub/GitLab
gpg --armor --export 3AA5C34371567BD2
# Copiare l'output e aggiungerlo su GitHub: Settings > SSH and GPG keys > New GPG key

# 5. Configurare GPG agent per caching della passphrase
echo "default-cache-ttl 3600" >> ~/.gnupg/gpg-agent.conf
echo "max-cache-ttl 86400" >> ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent
```

#### Risoluzione Problemi GPG

```bash
# Problema: "error: gpg failed to sign the data"
# Soluzione 1: specificare il TTY
export GPG_TTY=$(tty)
echo 'export GPG_TTY=$(tty)' >> ~/.bashrc

# Soluzione 2: pinentry non funziona in terminale non-interattivo
echo "pinentry-mode loopback" >> ~/.gnupg/gpg-agent.conf
echo "allow-loopback-pinentry" >> ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent

# Soluzione 3: la chiave e scaduta
gpg --edit-key 3AA5C34371567BD2
# gpg> expire
# (impostare nuova scadenza)
# gpg> save

# Verificare una firma GPG
git log --show-signature -1
# gpg: Signature made Fri 24 May 2026 10:30:00 AM CEST
# gpg:                using RSA key 3AA5C34371567BD2
# gpg: Good signature from "Mario Rossi <mario@esempio.it>" [ultimate]
```

### Confronto SSH vs GPG per la Firma

| Caratteristica | SSH | GPG |
|----------------|-----|-----|
| **Setup** | Semplice (2-3 comandi) | Complesso (generazione chiave, passphrase, agent) |
| **Scadenza chiave** | Non supportata | Supportata con notifica automatica |
| **Revoca** | Rimuovere da allowed_signers | Certificato di revoca pubblicabile |
| **Web of Trust** | Non supportato | Supportato |
| **Supporto GitHub** | Si (dal 2022) | Si (storico) |
| **Supporto GitLab** | Si (dal 16.x) | Si (storico) |
| **Overhead** | Nessuno (gia installato) | Richiede installazione GPG |
| **Caso d'uso ideale** | Progetti personali e team piccoli | Enterprise con PKI, compliance |
| **Requisito Git** | Git 2.34+ | Qualsiasi versione |

### Configurazione Completa nel .gitconfig

```ini
# ~/.gitconfig — sezione firma

# === Opzione A: Firma SSH (raccomandata) ===
[gpg]
    format = ssh

[gpg "ssh"]
    allowedSignersFile = ~/.config/git/allowed_signers

[user]
    signingkey = ~/.ssh/id_ed25519.pub

[commit]
    gpgsign = true

[tag]
    gpgSign = true

# === Opzione B: Firma GPG ===
# [gpg]
#     format = openpgp
#
# [user]
#     signingkey = 3AA5C34371567BD2
#
# [commit]
#     gpgsign = true
#
# [tag]
#     gpgSign = true
```

---

## Configurazione Avanzata di Git

Oltre alle impostazioni fondamentali, Git offre configurazioni avanzate per la performance, la sicurezza e la gestione di repository di grandi dimensioni.

### git maintenance — Manutenzione Automatica del Repository

A partire da Git 2.29, il comando `git maintenance` automatizza le operazioni di ottimizzazione che in precedenza richiedevano intervento manuale.

```bash
# Registrare il repository per manutenzione schedulata
git maintenance register
# Aggiunge il repository alla lista di manutenzione e
# configura un cron job (o launchd su macOS, Task Scheduler su Windows)

# Attivita programmate:
# - prefetch: scarica oggetti dai remote in background (ogni ora)
# - commit-graph: aggiorna il commit graph (ogni ora)
# - gc: garbage collection (giornaliera)
# - loose-objects: raggruppa oggetti sciolti (giornaliera)
# - incremental-repack: repack incrementale dei packfile (giornaliera)
# - pack-refs: compatta le refs (giornaliera)

# Eseguire manutenzione manualmente
git maintenance run --task=gc
git maintenance run --task=commit-graph
git maintenance run --task=prefetch

# Configurare la frequenza
git config maintenance.gc.schedule daily
git config maintenance.commit-graph.schedule hourly
git config maintenance.prefetch.schedule hourly

# Verificare lo stato
git maintenance status

# Rimuovere il repository dalla manutenzione
git maintenance unregister
```

### Configurazione delle Performance

```bash
# --- File System Monitor (FSMonitor) ---
# Usa un demone per monitorare i cambiamenti al filesystem
# riducendo drasticamente i tempi di git status su repo grandi
git config --global core.fsmonitor true
git config --global core.untrackedCache true

# Abilitare l'update index in parallelo (Git 2.40+)
git config --global index.threads true

# --- feature.manyFiles ---
# Abilita un bundle di ottimizzazioni per repository con molti file:
# - core.untrackedCache = true
# - index.version = 4 (formato indice compatto)
git config --global feature.manyFiles true

# --- Commit Graph ---
# Accelera operazioni che attraversano la storia (log, merge-base, blame)
git config --global fetch.writeCommitGraph true
git config --global core.commitGraph true

# --- Multi-Pack Index (MIDX) ---
# Velocizza operazioni con molti packfile
git config --global core.multiPackIndex true

# --- column.ui ---
# Mostra output (branch, tag, status) in formato colonna
git config --global column.ui auto
# git branch mostra i branch in colonne invece che in lista verticale

# --- Paginazione ---
git config --global pager.branch false      # Non paginare l'output di branch
git config --global pager.tag false         # Non paginare l'output di tag
```

### Configurazione della Sicurezza

```bash
# --- safe.directory ---
# Proteggere contro attacchi tramite repository con proprietario diverso
# Git 2.35.2+ rifiuta di operare in repository non di proprieta dell'utente
git config --global safe.directory /path/to/trusted/repo
# ATTENZIONE: usare '*' disabilita completamente il controllo — sconsigliato

# --- Restrizioni di protocollo ---
# Controllare quali protocolli Git puo usare
git config --global protocol.file.allow always
git config --global protocol.https.allow always
git config --global protocol.ssh.allow always
git config --global protocol.git.allow never     # Protocollo git:// non cifrato — disabilitare

# --- Verifica degli oggetti durante transfer ---
git config --global transfer.fsckObjects true
git config --global receive.fsckObjects true
git config --global fetch.fsckObjects true
# Rallenta leggermente clone/fetch, ma previene corruzione silenziosa

# --- Protezione symlink ---
git config --global core.symlinks false
# Disabilitare se non necessari (previene symlink attacks su Windows)

# --- HTTP ---
git config --global http.sslVerify true          # Mai disabilitare in produzione
git config --global http.postBuffer 524288000    # 500 MB per push di repo grandi
```

### Sparse Checkout per Monorepo

Lo sparse checkout permette di materializzare solo un sottoinsieme del repository nel working tree, ideale per monorepo dove ogni sviluppatore lavora su una porzione specifica.

```bash
# Clone parziale + sparse checkout (workflow ottimale per monorepo)
git clone --filter=blob:none --sparse https://github.com/org/monorepo.git
cd monorepo

# Abilitare il cone mode (raccomandato — piu veloce e prevedibile)
git sparse-checkout set --cone

# Selezionare le directory da materializzare
git sparse-checkout set frontend/app backend/api shared/utils
# Il working tree contiene SOLO queste directory (+ root files)

# Aggiungere directory in seguito
git sparse-checkout add docs/api mobile/ios

# Visualizzare i pattern attivi
git sparse-checkout list
# frontend/app
# backend/api
# shared/utils
# docs/api
# mobile/ios

# Disabilitare sparse checkout (ripristinare tutti i file)
git sparse-checkout disable
```

Il flag `--filter=blob:none` crea un **clone parziale** (partial clone): Git scarica solo i commit e i tree, scaricando i blob (contenuto dei file) su richiesta quando necessari. Combinato con sparse checkout, un monorepo di 30 GB puo ridursi a un clone iniziale di pochi MB.

```bash
# Verificare le dimensioni del clone
du -sh .git/
# 12M    .git/     (invece di 3.2G con clone completo)

# I file vengono scaricati on-demand:
git show HEAD:backend/payments/service.py
# Git scarica il blob al momento della richiesta
```

### Scalar — Acceleratore per Repository Grandi

Scalar (integrato in Git dalla versione 2.38) e un tool sviluppato da Microsoft per automatizzare la configurazione ottimale di Git per repository molto grandi:

```bash
# Clonare con Scalar (abilita automaticamente tutte le ottimizzazioni)
scalar clone https://github.com/org/huge-repo.git
# Scalar configura automaticamente:
# - partial clone (--filter=blob:none)
# - sparse checkout
# - fsmonitor
# - commit-graph
# - multipack index
# - background maintenance

# Registrare un repository esistente
scalar register

# Verificare lo stato
scalar list
scalar diagnose

# Deregistrare
scalar unregister
```

### Configurazioni Utili per il Workflow Quotidiano

```bash
# --- Rebase interattivo: aprire l'editor con istruzioni ---
git config --global rebase.instructionFormat "(%ai) %s [%an]"
# Mostra data, messaggio e autore nel rebase interattivo

# --- Stash: mostrare file non tracciati ---
git config --global stash.showIncludeUntracked true

# --- Log: formato predefinito ---
git config --global log.date iso-local
# Date in formato ISO 8601 con timezone locale

# --- Diff: rilevare rinominazioni ---
git config --global diff.renames copies
# Rileva sia rinominazioni che copie di file

# --- Status: mostrare stash count ---
git config --global status.showStash true
# git status mostra quanti stash entry esistono

# --- Branch: ordinamento ---
git config --global branch.sort -committerdate
# Ordina i branch per data dell'ultimo commit (piu recente prima)

# --- Tag: ordinamento ---
git config --global tag.sort -version:refname
# Ordina i tag per versione semantica decrescente

# --- Submodule: aggiornamento ricorsivo ---
git config --global submodule.recurse true
# git pull, git checkout, ecc. aggiornano automaticamente i submodule

# --- Advice: disabilitare messaggi per utenti esperti ---
git config --global advice.detachedHead false
git config --global advice.pushUpdateRejected false
git config --global advice.statusHints false
```

---

## .gitattributes Completo — Template di Riferimento

I template seguenti combinano tutte le funzionalita di `.gitattributes` — normalizzazione EOL, attributi binari, linguist overrides, merge strategies, export rules e LFS — in configurazioni pronte per l'uso.

### Template Multi-Linguaggio Completo

```gitattributes
# =============================================================
# .gitattributes — Template multi-linguaggio
# Normalizzazione EOL, binari, linguist, merge, export, LFS
# =============================================================

# --- Normalizzazione automatica (OBBLIGATORIO come prima riga) ---
* text=auto

# =======================
# FILE DI TESTO PER TIPO
# =======================

# --- Sorgenti ---
*.c text diff=c
*.h text diff=c
*.cpp text diff=cpp
*.hpp text diff=cpp
*.cc text diff=cpp
*.cxx text diff=cpp
*.java text diff=java
*.kt text diff=kotlin
*.kts text diff=kotlin
*.scala text diff=scala
*.go text diff=golang
*.rs text diff=rust
*.py text diff=python
*.rb text diff=ruby
*.pl text diff=perl
*.pm text diff=perl
*.php text diff=php
*.cs text diff=csharp
*.swift text diff=swift
*.dart text diff=dart
*.lua text
*.r text
*.R text

# --- Web ---
*.js text
*.jsx text
*.ts text
*.tsx text
*.mjs text
*.cjs text
*.vue text
*.svelte text
*.astro text
*.html text diff=html
*.htm text diff=html
*.css text diff=css
*.scss text diff=css
*.sass text
*.less text
*.styl text

# --- Config ---
*.json text
*.jsonc text
*.json5 text
*.yaml text
*.yml text
*.toml text
*.ini text
*.cfg text
*.conf text
*.properties text
*.xml text
*.plist text diff=plist

# --- Documentation ---
*.md text diff=markdown
*.mdx text diff=markdown
*.txt text
*.rst text
*.adoc text
*.tex text diff=tex
*.bib text diff=bibtex

# --- Data ---
*.csv text
*.tsv text
*.sql text

# --- Shell / Script ---
*.sh text eol=lf
*.bash text eol=lf
*.zsh text eol=lf
*.fish text eol=lf
*.csh text eol=lf
*.ksh text eol=lf
Makefile text eol=lf
makefile text eol=lf
*.mk text eol=lf

# --- Docker ---
Dockerfile text eol=lf
Dockerfile.* text eol=lf
*.dockerfile text eol=lf
docker-compose*.yml text
.dockerignore text eol=lf

# --- CI/CD ---
Jenkinsfile text eol=lf
.travis.yml text
.gitlab-ci.yml text
Procfile text eol=lf
Vagrantfile text eol=lf

# --- Git ---
.gitattributes text eol=lf
.gitignore text eol=lf
.gitmodules text eol=lf
.mailmap text eol=lf

# --- Editor config ---
.editorconfig text eol=lf
.prettierrc text
.eslintrc text
.stylelintrc text

# --- Windows-specific (CRLF) ---
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
*.psm1 text eol=crlf
*.psd1 text eol=crlf
*.sln text eol=crlf
*.csproj text eol=crlf
*.vbproj text eol=crlf
*.fsproj text eol=crlf
*.dbproj text eol=crlf
*.vcxproj text eol=crlf
*.props text eol=crlf
*.targets text eol=crlf

# ==================
# FILE BINARI
# ==================

# --- Immagini ---
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.bmp binary
*.tiff binary
*.tif binary
*.ico binary
*.webp binary
*.avif binary
*.heic binary
*.heif binary
*.svg text
*.eps binary
*.psd binary
*.ai binary
*.sketch binary
*.fig binary
*.xd binary

# --- Font ---
*.woff binary
*.woff2 binary
*.ttf binary
*.otf binary
*.eot binary

# --- Audio ---
*.mp3 binary
*.wav binary
*.ogg binary
*.flac binary
*.aac binary
*.m4a binary
*.wma binary

# --- Video ---
*.mp4 binary
*.avi binary
*.mov binary
*.mkv binary
*.wmv binary
*.flv binary
*.webm binary
*.m4v binary

# --- Archivi ---
*.zip binary
*.tar binary
*.tar.gz binary
*.tgz binary
*.gz binary
*.bz2 binary
*.xz binary
*.7z binary
*.rar binary
*.jar binary
*.war binary
*.ear binary

# --- Eseguibili ---
*.exe binary
*.dll binary
*.so binary
*.dylib binary
*.app binary

# --- Database ---
*.sqlite binary
*.sqlite3 binary
*.db binary
*.mdb binary

# --- Documenti ---
*.pdf binary
*.doc binary
*.docx binary
*.xls binary
*.xlsx binary
*.ppt binary
*.pptx binary
*.odt binary
*.ods binary
*.odp binary

# --- Certificati ---
*.p12 binary
*.pfx binary
*.cer binary
*.der binary

# ==================
# MERGE STRATEGIES
# ==================

# Lock file — non fare merge automatico
package-lock.json merge=ours
yarn.lock merge=ours
pnpm-lock.yaml merge=ours
Pipfile.lock merge=ours
poetry.lock merge=ours
Gemfile.lock merge=ours
composer.lock merge=ours
Cargo.lock merge=ours
go.sum merge=ours

# Changelog — unire le righe di entrambi
CHANGELOG.md merge=union
HISTORY.md merge=union

# ==================
# LINGUIST (GitHub)
# ==================

# --- File generati (non contati nelle statistiche, collassati nei diff) ---
*.min.js linguist-generated
*.min.css linguist-generated
*.map linguist-generated
*.lock linguist-generated
*.g.dart linguist-generated
*.freezed.dart linguist-generated
*.gen.go linguist-generated
*_generated.go linguist-generated
*.pb.go linguist-generated
**/generated/** linguist-generated
dist/** linguist-generated
coverage/** linguist-generated

# --- Codice di terze parti (non contato nelle statistiche) ---
vendor/** linguist-vendored
third_party/** linguist-vendored
node_modules/** linguist-vendored
bower_components/** linguist-vendored

# --- Documentazione ---
docs/** linguist-documentation
*.md linguist-documentation

# --- Override linguaggio ---
*.h linguist-language=C
Dockerfile.* linguist-language=Dockerfile
*.jsonc linguist-language=JSON

# --- Rendere rilevabile ---
*.html linguist-detectable

# ==================
# EXPORT (git archive)
# ==================

.gitignore export-ignore
.gitattributes export-ignore
.github/ export-ignore
.gitlab/ export-ignore
.circleci/ export-ignore
tests/ export-ignore
__tests__/ export-ignore
spec/ export-ignore
test/ export-ignore
*.test.js export-ignore
*.test.ts export-ignore
*.spec.js export-ignore
*.spec.ts export-ignore
*_test.go export-ignore
*_test.py export-ignore
jest.config.* export-ignore
vitest.config.* export-ignore
.eslintrc* export-ignore
.prettierrc* export-ignore
.stylelintrc* export-ignore
.editorconfig export-ignore
Makefile export-ignore
docker-compose*.yml export-ignore
Dockerfile export-ignore
.dockerignore export-ignore
.env.example export-ignore
CONTRIBUTING.md export-ignore
CODE_OF_CONDUCT.md export-ignore
```

### Template per Progetto Unity con LFS

```gitattributes
# =============================================================
# .gitattributes — Unity con Git LFS
# =============================================================

# Normalizzazione
* text=auto

# Unity YAML
*.unity text merge=unityyamlmerge eol=lf
*.prefab text merge=unityyamlmerge eol=lf
*.asset text merge=unityyamlmerge eol=lf
*.meta text eol=lf
*.controller text eol=lf
*.anim text eol=lf
*.overrideController text eol=lf
*.physicMaterial text eol=lf
*.physicsMaterial2D text eol=lf
*.playable text eol=lf
*.mat text eol=lf
*.mask text eol=lf
*.flare text eol=lf
*.lighting text eol=lf
*.giparams text eol=lf
*.renderTexture text eol=lf
*.spriteatlas text eol=lf
*.terrainlayer text eol=lf
*.mixer text eol=lf
*.signal text eol=lf
*.inputactions text eol=lf

# Script
*.cs text diff=csharp
*.cginc text
*.shader text
*.hlsl text
*.compute text

# LFS — Asset binari
*.cubemap filter=lfs diff=lfs merge=lfs -text
*.unitypackage filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.psd filter=lfs diff=lfs merge=lfs -text
*.tga filter=lfs diff=lfs merge=lfs -text
*.tif filter=lfs diff=lfs merge=lfs -text
*.hdr filter=lfs diff=lfs merge=lfs -text
*.exr filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text
*.fbx filter=lfs diff=lfs merge=lfs -text
*.obj filter=lfs diff=lfs merge=lfs -text
*.blend filter=lfs diff=lfs merge=lfs -text
*.dae filter=lfs diff=lfs merge=lfs -text
*.3ds filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.ttf filter=lfs diff=lfs merge=lfs -text
*.otf filter=lfs diff=lfs merge=lfs -text
*.dll filter=lfs diff=lfs merge=lfs -text
*.a filter=lfs diff=lfs merge=lfs -text
*.so filter=lfs diff=lfs merge=lfs -text
*.reason filter=lfs diff=lfs merge=lfs -text

# Linguist
*.cs linguist-detectable
*.shader linguist-detectable
```

---

## Configurazione Git per Ambienti Multi-Piattaforma

Lavorare con team distribuiti su macOS, Linux e Windows richiede una configurazione attenta per evitare problemi di compatibilita.

### Strategia EOL Cross-Platform

La configurazione dei line endings deve essere coerente tra tutti i membri del team. La strategia raccomandata e:

```bash
# 1. .gitattributes nel repository (AUTORITA' FINALE)
#    Definire * text=auto e specificare eol per file specifici

# 2. Configurazione locale di backup (ciascun sviluppatore)
# macOS / Linux:
git config --global core.autocrlf input
# Converte CRLF -> LF al commit, non modifica al checkout

# Windows:
git config --global core.autocrlf true
# Converte LF -> CRLF al checkout, CRLF -> LF al commit

# 3. Verificare la coerenza dopo configurazione
git diff --check
# Segnala spazi bianchi e line ending inconsistenti
```

### Gestione dei Permessi File

Git traccia solo il bit di esecuzione (`chmod +x`), non i permessi Unix completi. Su Windows, dove il concetto di permesso di esecuzione non esiste nativamente, questa differenza puo causare problemi:

```bash
# Disabilitare il tracking dei permessi (utile su Windows o filesystem montati)
git config core.fileMode false

# Rendere un file eseguibile nel repository
git update-index --chmod=+x script.sh

# Verificare i permessi tracciati
git ls-files -s script.sh
# 100755 abc1234... 0    script.sh   (755 = eseguibile)
# 100644 abc1234... 0    config.yml  (644 = non eseguibile)
```

### Case Sensitivity

macOS e Windows usano filesystem case-insensitive per default, mentre Linux e case-sensitive. Questo puo causare problemi con file che differiscono solo per maiuscole/minuscole:

```bash
# Verificare la configurazione
git config core.ignoreCase
# true su macOS/Windows per default, false su Linux

# Rinominare un file cambiando solo il case
# (non funziona con mv su filesystem case-insensitive)
git mv MyFile.js myFile.js
# Se git mv non funziona:
git mv MyFile.js temp-file.js
git mv temp-file.js myFile.js

# Abilitare la sensibilita al case su macOS/Windows
# ATTENZIONE: puo causare problemi se esistono file che differiscono solo per case
git config core.ignoreCase false
```

### Path Lunghi su Windows

Windows ha un limite di 260 caratteri per i path. Per repository con path profondi (comune in progetti Java e Node.js):

```bash
# Abilitare path lunghi su Windows
git config --global core.longpaths true

# Inoltre, abilitare il supporto nel sistema operativo:
# Eseguire come Administrator:
# reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1
```

### Encoding dei Nomi File

```bash
# Visualizzare correttamente nomi file con caratteri non-ASCII
git config --global core.quotePath false
# Senza questa impostazione, Git mostra caratteri non-ASCII come escape sequences:
# "file\303\250.txt" invece di "file.txt"

# Configurare la pagina di codifica per messaggi di log
git config --global i18n.logOutputEncoding utf-8
git config --global i18n.commitEncoding utf-8
```

---

## Automazione della Configurazione Iniziale

Per team e organizzazioni, e fondamentale automatizzare il setup della configurazione Git per garantire coerenza tra tutti gli sviluppatori.

### Script di Setup per Nuovo Sviluppatore

```bash
#!/bin/bash
# setup-git.sh — Configurazione Git per nuovi membri del team
# Eseguire: bash setup-git.sh "Nome Cognome" "email@azienda.com"

set -euo pipefail

NAME="${1:?Uso: setup-git.sh 'Nome Cognome' 'email@azienda.com'}"
EMAIL="${2:?Specificare l'email}"

echo "=== Configurazione Git per $NAME ==="

# Identita
git config --global user.name "$NAME"
git config --global user.email "$EMAIL"

# Editor (personalizzabile)
git config --global core.editor "code --wait"

# Branch predefinito
git config --global init.defaultBranch main

# Pull con rebase
git config --global pull.rebase true

# Push
git config --global push.default current
git config --global push.autoSetupRemote true

# Merge
git config --global merge.conflictstyle zdiff3
git config --global rerere.enabled true

# Diff
git config --global diff.algorithm histogram
git config --global diff.colorMoved default
git config --global diff.renames copies

# Performance
git config --global core.fsmonitor true
git config --global core.untrackedCache true
git config --global feature.manyFiles true
git config --global fetch.prune true
git config --global fetch.writeCommitGraph true

# Sicurezza
git config --global transfer.fsckObjects true
git config --global receive.fsckObjects true
git config --global fetch.fsckObjects true
git config --global protocol.git.allow never

# Rebase
git config --global rebase.autoSquash true
git config --global rebase.autoStash true

# Stash
git config --global stash.showIncludeUntracked true

# Branch sort
git config --global branch.sort -committerdate

# Submodule
git config --global submodule.recurse true

# Colore
git config --global color.ui auto

# Column UI
git config --global column.ui auto

# Global gitignore
GITIGNORE_GLOBAL="$HOME/.gitignore_global"
if [[ ! -f "$GITIGNORE_GLOBAL" ]]; then
    cat > "$GITIGNORE_GLOBAL" << 'GITEOF'
# macOS
.DS_Store
._*
.Spotlight-V100
.Trashes

# Windows
Thumbs.db
Desktop.ini
$RECYCLE.BIN/

# Linux
*~
.directory

# IDE
.idea/
*.iml
.vscode/
*.code-workspace
*.swp
*.swo

# Tags
tags
TAGS

# Direnv
.envrc
.direnv/
GITEOF
    git config --global core.excludesFile "$GITIGNORE_GLOBAL"
    echo "Creato $GITIGNORE_GLOBAL"
fi

# Aliases essenziali
git config --global alias.st "status -sb"
git config --global alias.lg "log --graph --oneline --all --decorate"
git config --global alias.ll "log --oneline -15"
git config --global alias.co "checkout"
git config --global alias.sw "switch"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.last "log -1 HEAD --format='%H %s'"
git config --global alias.recent '!git for-each-ref --sort=-committerdate refs/heads/ --format="%(committerdate:short) %(refname:short)" | head -20'

echo ""
echo "=== Setup completato ==="
echo "Verificare con: git config --list --show-origin"
echo ""
echo "Prossimi passi:"
echo "  1. Generare SSH key: ssh-keygen -t ed25519 -C '$EMAIL'"
echo "  2. Aggiungere la chiave a GitHub/GitLab"
echo "  3. Configurare firma commit: git config --global gpg.format ssh"
echo "  4. Installare delta (opzionale): https://github.com/dandavison/delta"
```

### Makefile per Progetti con Hooks

```makefile
# Makefile — setup automatico per il progetto

.PHONY: setup hooks lint test

setup: hooks
	@echo "Progetto configurato correttamente"

hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/*
	@echo "Git hooks configurati"

lint:
	@echo "Esecuzione linting..."
	# Aggiungere comandi lint specifici del progetto

test:
	@echo "Esecuzione test..."
	# Aggiungere comandi test specifici del progetto
```

---

## Prevenzione dei Segreti nei Commit

Il `.gitignore` previene il tracciamento di file come `.env` o `credentials.json`, ma non ispeziona il *contenuto* dei file staged. Un segreto hardcoded all'interno di un file sorgente — una API key in una costante, un token OAuth in un test fixture, una password in un file di configurazione YAML — supera il `.gitignore` senza alcun ostacolo. Una volta che un segreto entra nella cronologia Git, la rimozione e complessa e costosa: ogni commit hash cambia, tutti i collaboratori devono ri-clonare, e il segreto potrebbe gia essere stato copiato in fork, CI cache o mirror. La difesa efficace opera a livello di contenuto, non di filename.

### git-secrets — Scansione Pattern-Based

`git-secrets`, sviluppato da AWS Labs, intercetta i commit che contengono pattern configurabili (chiavi AWS, token generici, password). Si installa come hook `pre-commit` nativo.

```bash
# Installazione
# macOS
brew install git-secrets

# Linux (da sorgente)
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets && sudo make install

# Registrare gli hook nel repository corrente
git secrets --install
# Installa pre-commit, commit-msg e prepare-commit-msg hooks

# Aggiungere i pattern AWS predefiniti
git secrets --register-aws

# Aggiungere pattern personalizzati
git secrets --add 'PRIVATE_KEY\s*[:=]'
git secrets --add 'ghp_[A-Za-z0-9_]{36}'          # GitHub PAT (classic)
git secrets --add 'github_pat_[A-Za-z0-9_]{82}'   # GitHub PAT (fine-grained)
git secrets --add 'sk-[A-Za-z0-9]{48}'             # OpenAI API key
git secrets --add 'xoxb-[0-9]+-[A-Za-z0-9]+'       # Slack bot token

# Consentire falsi positivi noti (es. placeholder in documentazione)
git secrets --add --allowed 'EXAMPLE_KEY_DO_NOT_USE'
git secrets --add --allowed '\.example$'

# Scansionare la cronologia esistente
git secrets --scan-history
# Esamina ogni commit per pattern sospetti

# Scansionare manualmente i file staged
git secrets --scan
```

### gitleaks — Scanner Standalone con Configurazione TOML

`gitleaks` e uno scanner di segreti veloce e configurabile che opera sia come tool da linea di comando sia come step CI. Supporta scansione della cronologia completa e dei file staged pre-commit.

```bash
# Installazione
brew install gitleaks                  # macOS
# Linux: scaricare il binario da https://github.com/gitleaks/gitleaks/releases

# Scansionare il repository corrente (tutti i commit)
gitleaks detect --source . --verbose

# Scansionare solo i file staged (ideale per pre-commit)
gitleaks protect --staged --verbose

# Usare come hook pre-commit (in .githooks/pre-commit o .husky/pre-commit)
# gitleaks protect --staged --verbose --exit-code 1

# Configurazione personalizzata: gitleaks.toml nella root del progetto
```

```toml
# gitleaks.toml — configurazione personalizzata
title = "Regole di scansione segreti del progetto"

# Regola personalizzata per token interni
[[rules]]
id = "internal-api-token"
description = "Token API interno dell'azienda"
regex = '''INTERNAL_TOKEN_[A-Z0-9]{32}'''
secretGroup = 0

# Allowlist globale: percorsi e pattern da ignorare
[allowlist]
description = "Falsi positivi noti"
paths = [
  '''docs/examples/.*\.md$''',
  '''test/fixtures/mock-credentials\.json$''',
]
regexes = [
  '''PLACEHOLDER_VALUE''',
  '''test-api-key-not-real''',
]
```

### detect-secrets — Approccio Baseline di Yelp

`detect-secrets` di Yelp adotta un approccio diverso: genera una *baseline* dei segreti gia presenti nel codebase, e le scansioni successive segnalano solo segreti **nuovi**. Questo evita di affrontare segreti storici prima di poter adottare lo strumento — un pragmatismo utile nei progetti legacy.

```bash
# Installazione
pip install detect-secrets

# Generare la baseline iniziale
detect-secrets scan > .secrets.baseline

# Audit interattivo della baseline
detect-secrets audit .secrets.baseline
# Per ogni finding rispondere: true positive, false positive o skip

# Scansionare file staged confrontando con la baseline
detect-secrets-hook --baseline .secrets.baseline
# Restituisce exit code 1 se trova segreti nuovi non presenti nella baseline

# Integrazione pre-commit (nel file .pre-commit-config.yaml)
# - repo: https://github.com/Yelp/detect-secrets
#   rev: v1.5.0
#   hooks:
#     - id: detect-secrets
#       args: ['--baseline', '.secrets.baseline']
```

### trufflehog — Scansione Entropica della Cronologia

`trufflehog` di Truffle Security analizza la cronologia Git usando sia pattern regex sia analisi entropica — identifica stringhe ad alta entropia (casualita) che probabilmente sono chiavi o token, anche senza corrispondenza con pattern noti.

```bash
# Installazione
brew install trufflehog   # macOS
# Linux: scaricare da https://github.com/trufflesecurity/trufflehog/releases

# Scansionare l'intera cronologia del repository locale
trufflehog git file://. --only-verified
# --only-verified testa attivamente se i segreti sono ancora validi
# (connette alle API — usare con cautela e autorizzazione)

# Scansionare un repository remoto
trufflehog git https://github.com/org/repo.git --json > findings.json

# Scansionare solo le differenze tra due commit
trufflehog git file://. --since-commit=abc1234 --branch=main
```

### Risposta di Emergenza: Rimozione dei Segreti dalla Cronologia

Se un segreto e gia stato committato, il semplice `git rm` non basta — il segreto resta raggiungibile nella cronologia. La rimozione richiede la riscrittura della storia con `git filter-repo` (successore di `git filter-branch`, significativamente piu veloce e sicuro).

```bash
# Installazione
pip install git-filter-repo

# Rimuovere un file dalla INTERA cronologia
git filter-repo --invert-paths --path config/secrets.yml
# ATTENZIONE: riscrive tutti i commit hash.
# Tutti i collaboratori devono ri-clonare.

# Sostituire una stringa specifica in tutta la cronologia
git filter-repo --replace-text <(echo 'sk-REAL_API_KEY==>REDACTED')

# Dopo la riscrittura:
# 1. Revocare immediatamente il segreto esposto (rotazione chiave/token)
# 2. Force-push di tutti i branch al remote
# 3. Notificare i collaboratori di ri-clonare
# 4. Verificare che fork e mirror non conservino il segreto
# 5. Controllare CI cache, artifact storage e log per copie del segreto
```

La rotazione del segreto e **sempre obbligatoria**, indipendentemente dalla velocita di rimozione dalla cronologia. GitHub offre inoltre Secret Scanning e Push Protection a livello di piattaforma per intercettare segreti noti prima che raggiungano il remote — approfondimento nel [Modulo 16: GitHub Security Scanning](16-github-security-scanning.md).

### Strategia di Difesa a Livelli

La prevenzione dei segreti nei commit si articola su piu livelli complementari, ciascuno con un ruolo specifico:

| Livello | Strumento | Quando agisce |
|---------|-----------|---------------|
| **Editor** | Plugin IDE (es. GitLens secret detection) | Durante la scrittura del codice |
| **Pre-commit locale** | git-secrets, gitleaks, detect-secrets | Prima che il commit venga creato localmente |
| **Push protection** | GitHub Push Protection, GitLab Secret Detection | Al momento del push al remote |
| **CI/CD** | gitleaks in pipeline, trufflehog | Durante il build/deploy |
| **Monitoraggio continuo** | GitHub Secret Scanning, Snyk | Post-push, scansione continua del repository |

Nessun singolo livello e sufficiente da solo. L'hook `pre-commit` locale e la prima linea di difesa, ma puo essere bypassato con `--no-verify`. La push protection server-side e il gate che non puo essere aggirato dallo sviluppatore individuale. La scansione continua in CI e il monitoraggio della piattaforma rilevano segreti che hanno superato le difese precedenti.

---

## Best Practices

### .gitignore

1. **Iniziare con un template**: Usare https://gitignore.io o i template GitHub per generare un `.gitignore` appropriato per il linguaggio e framework del progetto.

2. **Separare le responsabilita**: Il `.gitignore` del repository contiene pattern del progetto (`node_modules/`, `dist/`, `*.pyc`). Il global gitignore contiene pattern dell'ambiente (`.DS_Store`, `.idea/`).

3. **Non ignorare file di configurazione condivisi**: `.editorconfig`, `.prettierrc`, `eslint.config.js`, `tsconfig.json` devono essere versionati perche definiscono standard del progetto.

4. **Documentare le eccezioni**: Se un pattern usa la negazione (`!`), aggiungere un commento che spiega perche.

5. **Verificare periodicamente**: `git status --ignored` per individuare file che dovrebbero o non dovrebbero essere ignorati.

### .gitattributes

1. **Sempre includere `* text=auto`**: La normalizzazione automatica dei line endings previene la maggior parte dei problemi cross-platform.

2. **Marcare esplicitamente i binari**: Anche se Git e abbastanza bravo nel riconoscerli, e meglio essere espliciti per evitare che un file binario venga trattato come testo.

3. **Versionare .gitattributes**: Deve essere nel repository perche tutti i collaboratori ne beneficino.

4. **Configurare diff driver per binari**: Se il progetto contiene PDF, immagini, o documenti Office, configurare diff driver testuali per rendere i diff leggibili.

### Git Config

1. **Configurare l'identita per primo**: `user.name` e `user.email` sono obbligatori e devono essere corretti.

2. **Usare conditional includes**: Per separare configurazioni personali e lavorative senza rischio di committare con l'email sbagliata.

3. **Abilitare le performance features**: `fsmonitor`, `untrackedCache` e `feature.manyFiles` per repository grandi.

4. **Configurare `pull.rebase true`**: Previene merge commit inutili durante il pull.

5. **Abilitare `rerere`**: Ricorda le risoluzioni dei conflitti e le riapplica automaticamente.

### .mailmap

1. **Versionare sempre .mailmap**: Tutti i collaboratori devono vedere gli stessi nomi normalizzati.

2. **Aggiornare al cambio email**: Quando un collaboratore cambia email, aggiungere il mapping immediatamente.

3. **Non usare per riscrivere la storia**: `.mailmap` cambia solo la visualizzazione, non i commit. Per correzioni permanenti serve `git filter-repo`.

### Hooks

1. **Hooks veloci**: Il pre-commit deve completare in meno di 5 secondi. Se il lint e lento, usare lint-staged per lintare solo i file staged.

2. **Permettere il bypass**: `git commit --no-verify` deve essere disponibile per emergenze, ma l'uso deve essere eccezionale e giustificato.

3. **Versionare gli hooks**: Usare `.githooks/` con `core.hooksPath` o Husky per garantire che tutti i collaboratori usino gli stessi hooks.

4. **Non duplicare CI**: Gli hooks client-side sono una rete di sicurezza, non un sostituto della CI. La CI resta l'autorita finale.

---

## Troubleshooting

### File Ignorato Ma Ancora Tracciato

```bash
# Il file appare in git status nonostante sia in .gitignore
# Causa: il file era gia tracciato prima di essere aggiunto a .gitignore

git rm --cached file-da-ignorare
git commit -m "chore: rimuovere file dal tracking"
```

### Line Endings Inconsistenti

```bash
# Normalizzare i line endings nell'intero repository
# 1. Assicurarsi che .gitattributes sia configurato con * text=auto
# 2. Rinormalizzare
git add --renormalize .
git commit -m "chore: normalizzare line endings"

# Verificare line endings di un file specifico
file path/to/file
# Output: ASCII text, with CRLF line terminators  ← indica CRLF

# Verificare con hexdump
hexdump -C path/to/file | grep "0d 0a"
# 0d 0a = CR LF
```

### Configurazione Non Applicata

```bash
# Verificare da dove viene una configurazione
git config --show-origin --show-scope user.email
# file:/home/user/.gitconfig    global    mario@personal.com

# Verificare se c'e un override locale
git config --local --list

# Verificare tutti i livelli
git config --list --show-origin --show-scope | sort
```

### Credential Non Memorizzate

```bash
# Verificare il credential helper configurato
git config credential.helper

# Testare il credential helper
echo "protocol=https\nhost=github.com\n" | git credential fill

# Resettare le credenziali salvate (macOS)
git credential-osxkeychain erase <<EOF
protocol=https
host=github.com
EOF

# Resettare le credenziali (Windows)
git credential-manager erase <<EOF
protocol=https
host=github.com
EOF
```

### Hook Non Eseguito

```bash
# Verificare che l'hook sia eseguibile
ls -la .git/hooks/pre-commit
# Se manca la x: chmod +x .git/hooks/pre-commit

# Verificare core.hooksPath
git config core.hooksPath
# Se impostato, Git cerca gli hooks in quella directory

# Verificare lo shebang
head -1 .git/hooks/pre-commit
# Deve essere #!/bin/bash o #!/usr/bin/env python3 etc.

# Debug dell'hook
bash -x .git/hooks/pre-commit
# Mostra ogni comando eseguito

# Verificare che l'hook non sia bypassato
# Il flag --no-verify salta pre-commit e commit-msg
```

### Mailmap Non Funzionante

```bash
# Verificare che il file sia nella root del repository
ls -la .mailmap

# Verificare la sintassi con check-mailmap
git check-mailmap "Nome <email>"

# Verificare che non ci siano caratteri BOM o encoding errati
file .mailmap
# Deve essere: UTF-8 Unicode text

# Il mailmap non funziona con git log --format se si usa %ae/%an
# Usare %aE/%aN (maiuscolo) per i valori mapped
git log --format='%aN <%aE>'
```

---

## Domande Frequenti (Q&A)

**D: `.gitignore` vs `.git/info/exclude` — quando usare quale?**

R: `.gitignore` e versionato e condiviso con il team. Contiene pattern specifici del progetto. `.git/info/exclude` e locale e non condiviso. Contiene pattern personali dell'utente (es. `my-test-data/`). Il global gitignore (`core.excludesFile`) contiene pattern dell'ambiente (IDE, OS).

**D: Posso ignorare un file gia committato aggiungendolo a `.gitignore`?**

R: No. `.gitignore` agisce solo sui file non tracciati. Per smettere di tracciare un file gia committato: `git rm --cached <file>`, aggiungere a `.gitignore`, committare.

**D: Come faccio a versionare una directory vuota?**

R: Git non traccia directory vuote. La convenzione e aggiungere un file `.gitkeep` (vuoto) nella directory. Il nome `.gitkeep` non ha significato speciale per Git — e solo una convenzione. In alternativa, aggiungere un `.gitignore` nella directory con contenuto `*` e `!.gitignore`.

**D: `text=auto` vs `text` — qual e la differenza?**

R: `text` forza Git a trattare il file come testo, normalizzando sempre i line endings. `text=auto` lascia che Git determini automaticamente se il file e testo o binario. `text=auto` e piu sicuro perche non rischia di corrompere file binari.

**D: Come funziona `merge.conflictstyle zdiff3`?**

R: `zdiff3` mostra tre sezioni nel conflitto: la versione originale (ancestor), la nostra versione (ours) e la loro versione (theirs). Questo fornisce piu contesto per risolvere i conflitti. Senza zdiff3, il conflitto mostra solo ours vs theirs.

**D: Come impedisco che un hook blocchi tutti?**

R: Gli hooks client-side possono essere bypassati con `--no-verify`. Per gli hooks server-side, la responsabilita e dell'admin. Best practice: testare gli hooks in un ambiente non critico prima di deployarli in produzione. Includere messaggi di errore chiari che spiegano come correggere il problema.

**D: `git config --global` modifica quale file esattamente?**

R: Di default `~/.gitconfig`. Se esiste `$XDG_CONFIG_HOME/git/config` (tipicamente `~/.config/git/config`) e `~/.gitconfig` non esiste, viene usato quello. Se entrambi esistono, `~/.gitconfig` ha precedenza.

**D: Come verifico che il mio `.gitattributes` funzioni?**

R: `git check-attr -a -- path/to/file` mostra tutti gli attributi effettivi applicati a un file.

**D: `rerere` cosa fa esattamente?**

R: `rerere` (REuse REcorded REsolution) registra come hai risolto un conflitto di merge. Se lo stesso conflitto si ripresenta (es. durante un rebase), Git lo risolve automaticamente usando la risoluzione precedente. Attivare con `git config rerere.enabled true`.

---

## Esercizi

### Esercizio 1: Setup Completo

Configurare da zero un ambiente Git professionale:
1. Creare `~/.gitconfig` con identita, editor, pull.rebase, push.autoSetupRemote, delta come pager, firma SSH
2. Creare `~/.gitignore_global` con pattern per il proprio OS e IDE
3. Verificare con `git config --list --show-origin` che tutte le configurazioni siano corrette

### Esercizio 2: .gitattributes per Progetto Multi-Linguaggio

Creare un `.gitattributes` per un progetto che contiene Python, JavaScript, SQL, immagini e PDF:
1. Normalizzazione line endings con `text=auto`
2. Forzare LF per script shell e Makefile
3. Marcare correttamente tutti i binari
4. Configurare diff driver per PDF (`pdftotext`)
5. Configurare merge strategy `ours` per `poetry.lock`
6. Escludere la directory `tests/` dagli archivi (`export-ignore`)

### Esercizio 3: .mailmap

Dato un repository dove `git shortlog -sn` mostra:
```
   45  Mario Rossi
   23  mario <mario@gmail.com>
   12  M. Rossi <mrossi@work.com>
    8  dependabot[bot]
    3  dependabot-preview[bot]
```
Creare un `.mailmap` che unifica le identita di Mario e dei bot.

### Esercizio 4: Hook pre-commit

Scrivere un hook `pre-commit` che:
1. Verifica che nessun file staged contenga la stringa `console.log` (per file `.js`/`.ts`)
2. Verifica che nessun file staged superi 500 righe
3. Verifica che non ci siano file `.env` staged
4. Mostra un messaggio chiaro per ogni violazione trovata

### Esercizio 5: Hook commit-msg con Conventional Commits

Scrivere un hook `commit-msg` che:
1. Valida il formato Conventional Commits
2. Verifica che la prima riga non superi 72 caratteri
3. Verifica che il body (se presente) sia separato dalla prima riga da una riga vuota
4. Accetta merge commits senza validazione

### Esercizio 6: Conditional Includes

Configurare `~/.gitconfig` con conditional includes per:
1. Repository sotto `~/work/` usano email aziendale e GPG signing
2. Repository sotto `~/personal/` usano email personale senza signing
3. Verificare con `git config user.email` in entrambi i contesti

---

## Riferimenti

- **Git Documentation — gitignore**: https://git-scm.com/docs/gitignore
- **Git Documentation — gitattributes**: https://git-scm.com/docs/gitattributes
- **Git Documentation — git-config**: https://git-scm.com/docs/git-config
- **Git Documentation — githooks**: https://git-scm.com/docs/githooks
- **Git Documentation — gitmailmap**: https://git-scm.com/docs/gitmailmap
- **GitHub — gitignore Templates**: https://github.com/github/gitignore
- **gitignore.io**: https://www.toptal.com/developers/gitignore
- **GitHub Linguist**: https://github.com/github/linguist
- **Git Credential Storage**: https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage
- **Git Pro Book — Customizing Git**: https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration
- **Git Pro Book — Git Hooks**: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- **EditorConfig**: https://editorconfig.org/
- **Delta (diff pager)**: https://github.com/dandavison/delta
- **Husky**: https://typicode.github.io/husky/
- **lint-staged**: https://github.com/lint-staged/lint-staged
- **commitlint**: https://commitlint.js.org/
- **Conventional Commits**: https://www.conventionalcommits.org/

---

## Letture consigliate

- **Git Pro Book — Customizing Git: Git Configuration** — https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration (consultato: 2026-05-24). Capitolo ufficiale sulla configurazione multi-livello di Git con tutte le opzioni disponibili.

- **Git Documentation — gitignore** — https://git-scm.com/docs/gitignore (consultato: 2026-05-24). Specifica ufficiale dei pattern di esclusione con regole di precedenza e negazione.

- **Git Documentation — gitattributes** — https://git-scm.com/docs/gitattributes (consultato: 2026-05-24). Documentazione completa degli attributi dei file: conversione EOL, merge driver, diff driver, LFS filter.

- **GitHub — gitignore Templates** — https://github.com/github/gitignore (consultato: 2026-05-24). Collezione ufficiale di template `.gitignore` per ogni linguaggio, framework e IDE.

- **gitignore.io** — https://www.toptal.com/developers/gitignore (consultato: 2026-05-24). Generatore web di `.gitignore` combinando tecnologie, IDE e sistemi operativi.

- **Git Credential Storage** — https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage (consultato: 2026-05-24). Guida ai credential helper (cache, store, osxkeychain, manager) per gestione sicura delle credenziali.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti Git: init, clone, working tree | 01 | [01-fondamenti-git.md](01-fondamenti-git.md) |
| Git Internals: blob, tree, oggetti, .git/ | 07 | [07-git-interni-oggetti-refs.md](07-git-interni-oggetti-refs.md) |
| Git Hooks: pre-commit, commit-msg, automazione | 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) |
| Git LFS: tracking con .gitattributes | 09 | [09-git-lfs-submodules-monorepo.md](09-git-lfs-submodules-monorepo.md) |
| Git Stash, Reset e Recovery: alias utili, config | 10 | [10-git-stash-reset-recovery.md](10-git-stash-reset-recovery.md) |
| GitHub Repository Management: settings, template | 12 | [12-github-repository-management.md](12-github-repository-management.md) |
| GitHub Security Scanning: secret detection | 16 | [16-github-security-scanning.md](16-github-security-scanning.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **`.gitignore`** | File che definisce pattern di esclusione per file e directory che Git non deve tracciare. Supporta glob, negazione (`!`) e directory (`/`). |
| **`.gitattributes`** | File che assegna attributi ai path del repository: conversione EOL, merge driver personalizzati, diff driver, linguist override e LFS filter. |
| **conditional include** | Direttiva `[includeIf]` in `~/.gitconfig` che carica configurazioni diverse in base al path del repository, al branch o al remote URL. |
| **credential helper** | Componente di Git che memorizza le credenziali di autenticazione. Tipi: `cache` (RAM temporanea), `store` (file in chiaro), `osxkeychain`, `manager` (cross-platform). |
| **EOL (End of Line)** | Carattere di fine riga: LF (`\n`) su Unix/macOS, CRLF (`\r\n`) su Windows. `.gitattributes` controlla la conversione automatica con `text=auto`. |
| **git config** | Comando per leggere e scrivere la configurazione di Git. Opera su 3 livelli: `--system` (tutti gli utenti), `--global` (utente corrente), `--local` (repository corrente). |
| **global gitignore** | File di esclusione globale (es. `~/.config/git/ignore`) che si applica a tutti i repository dell'utente. Configurato con `core.excludesFile`. |
| **GPG signing** | Firma crittografica dei commit e dei tag con chiave GPG (o SSH da Git 2.34). Verificabile con `git log --show-signature`. |
| **linguist** | Strumento GitHub che rileva il linguaggio dei file per le statistiche del repository. Sovrascrivibile con `.gitattributes` (es. `*.js linguist-vendored`). |
| **`.mailmap`** | File che normalizza nomi e indirizzi email degli autori nella cronologia Git. Utile quando un autore ha usato identità multiple nel tempo. |
| **merge driver** | Programma personalizzato invocato da Git per risolvere conflitti su file specifici. Definito in `.gitattributes` e configurato in `.gitconfig`. |
| **negation pattern** | Pattern `.gitignore` prefissato con `!` che re-include un file precedentemente escluso. Es: `!important.log` include `important.log` anche se `*.log` lo escluderebbe. |
| **sparse-checkout** | Funzionalità Git che materializza nel working tree solo un sottoinsieme dei file. Interagisce con `.gitignore` per definire cosa è visibile. |
| **text/binary attribute** | Attributo `.gitattributes` che indica se un file è testo (soggetto a conversione EOL) o binario (trattato come blob opaco senza conversione). |
