# 00 — Git per Pythonisti

> **Lingua:** italiano · **Aggiornamento:** 2026-07-15
> **Versioni:** Git 2.45+ · GitHub CLI 2.52+ · pre-commit 3.x · git-cliff 2.x · uv 0.7+
> **Collegato a:** moduli [08-testing](08-testing.md), [18-sicurezza](18-sicurezza.md), [23-packaging-distribuzione](23-packaging-distribuzione.md), [24-virtual-environments](24-virtual-environments.md), [27-ci-cd-per-python](27-ci-cd-per-python.md), [31-osservabilita-otel-prometheus](31-osservabilita-otel-prometheus.md), [32-packaging-distribuzione](32-packaging-distribuzione.md)
> **Prerequisiti:** nessuno — documento fondamentale del corso

---

## Idee guida

1. **Git è il sistema nervoso di ogni progetto Python professionale** — non un accessorio opzionale.
2. **Commit atomici, messaggi descrittivi, branch per feature** — tre abitudini che separano il professionista dal dilettante.
3. **`.gitignore` corretto fin dal primo `git init`** — prevenire è meglio che curare con `git filter-repo`.
4. **pre-commit hooks come prima linea di difesa** — ruff, mypy e test leggeri prima di ogni push.
5. **Conventional Commits + git-cliff = changelog automatico e versioning senza sforzo.**
6. **Nessun segreto nel repository, mai** — gitleaks in CI come rete di sicurezza.
7. **GitHub Actions per Python: lint → typecheck → test → audit → publish — pipeline ripetibile e documentata.**

---

## Indice

1. [Panoramica](#1-panoramica)
2. [Perché il Controllo Versione](#2-perché-il-controllo-versione)
3. [Installazione e Configurazione](#3-installazione-e-configurazione)
   - [3.1 Installazione su Windows](#31-installazione-su-windows)
   - [3.2 Installazione su macOS](#32-installazione-su-macos)
   - [3.3 Installazione su Linux](#33-installazione-su-linux)
   - [3.4 Configurazione Globale](#34-configurazione-globale)
   - [3.5 SSH Key per GitHub](#35-ssh-key-per-github)
   - [3.6 GitHub CLI](#36-github-cli)
4. [Il Modello Dati di Git](#4-il-modello-dati-di-git)
5. [Flusso di Lavoro Fondamentale](#5-flusso-di-lavoro-fondamentale)
   - [5.1 init, add, commit](#51-init-add-commit)
   - [5.2 status, log, diff](#52-status-log-diff)
   - [5.3 .gitignore per Python](#53-gitignore-per-python)
   - [5.4 Annullare Modifiche](#54-annullare-modifiche)
6. [Branch e Merge](#6-branch-e-merge)
   - [6.1 Concetto di Branch](#61-concetto-di-branch)
   - [6.2 Feature Branch Workflow](#62-feature-branch-workflow)
   - [6.3 Merge — Fast-Forward e 3-Way](#63-merge--fast-forward-e-3-way)
   - [6.4 Risoluzione Conflitti](#64-risoluzione-conflitti)
   - [6.5 Merge vs Rebase](#65-merge-vs-rebase)
7. [GitHub — Remote Repository](#7-github--remote-repository)
   - [7.1 clone, remote, push, pull, fetch](#71-clone-remote-push-pull-fetch)
   - [7.2 Fork e Pull Request Workflow](#72-fork-e-pull-request-workflow)
   - [7.3 GitHub CLI Essenziale](#73-github-cli-essenziale)
8. [Tag e Versioning Semantico](#8-tag-e-versioning-semantico)
9. [pre-commit Hooks](#9-pre-commit-hooks)
10. [GitHub Actions per Python](#10-github-actions-per-python)
11. [Convenzioni e Changelog](#11-convenzioni-e-changelog)
12. [Comandi Avanzati](#12-comandi-avanzati)
13. [Integrazione con Strumenti Python](#13-integrazione-con-strumenti-python)
14. [Sicurezza e Secrets](#14-sicurezza-e-secrets)
15. [Riferimenti e Letture Consigliate](#15-riferimenti-e-letture-consigliate)

---

## 1. Panoramica

Git è un sistema di controllo versione distribuito creato da Linus Torvalds nel 2005 per gestire il codice sorgente del kernel Linux. In meno di vent'anni è diventato lo strumento più utilizzato al mondo per la gestione del codice: secondo il Stack Overflow Developer Survey 2024, oltre il 96% degli sviluppatori professionisti usa Git quotidianamente.

Per uno sviluppatore Python, Git non è solo uno strumento di backup avanzato. È l'infrastruttura su cui poggiano:

- la **collaborazione** (pull request, code review, fork)
- il **rilascio** (tag, versioning, Trusted Publishers su PyPI)
- la **qualità** (pre-commit hooks, CI/CD, branch protection)
- la **sicurezza** (secret scanning, firma dei commit, SBOM)
- la **documentazione** (changelog, commit history come audit trail)

Questo documento copre Git dall'installazione ai comandi avanzati, sempre con il punto di vista di chi lavora quotidianamente con Python e il suo ecosistema. I concetti di packaging (`pyproject.toml`, wheel, sdist) sono trattati in [23-packaging-distribuzione.md](23-packaging-distribuzione.md); la CI/CD completa è in [27-ci-cd-per-python.md](27-ci-cd-per-python.md); la sicurezza della supply chain in [18-sicurezza.md](18-sicurezza.md).

---

## 2. Perché il Controllo Versione

### Breve storia

| Anno | Sistema | Modello | Note |
|------|---------|---------|------|
| 1972 | SCCS | Locale | First VCS, Bell Labs |
| 1982 | RCS | Locale | File locking, diff/patch |
| 1990 | CVS | Centralizzato | Merge, branch, multi-utente |
| 2000 | Subversion (SVN) | Centralizzato | Atomic commit, directory versioning |
| 2000 | BitKeeper | Distribuito | Usato per Linux kernel (proprietario) |
| 2005 | **Git** | **Distribuito** | Linus Torvalds, dopo la revoca di BitKeeper |
| 2005 | Mercurial (hg) | Distribuito | Alternativa a Git, usata da Python e Mozilla |
| 2008 | GitHub | Hosting Git | SaaS, pull request, social coding |

### Distribuito vs Centralizzato

Il vantaggio fondamentale di Git rispetto a CVS/SVN è la **natura distribuita**: ogni clone è un repository completo con tutta la storia. Questo significa:

- **Lavoro offline** — commit, branch, log, diff funzionano senza connessione di rete
- **Nessun single point of failure** — il repository non dipende da un server centrale
- **Branch leggeri** — creare un branch in Git costa O(1) (è solo un puntatore a un commit)
- **Velocità** — la maggior parte delle operazioni avviene localmente su disco

### Perché Git è critico per i Python developer

Un progetto Python moderno tocca Git in almeno quindici punti diversi:

```
pyproject.toml          → versioning (hatch, bump-my-version)
.pre-commit-config.yaml → hooks automatici (ruff, mypy, pytest)
.github/workflows/      → CI/CD (GitHub Actions)
CHANGELOG.md            → generato da git-cliff dalla commit history
requirements.txt        → git hash come anchor per dipendenze da VCS
setup.cfg / flit        → SCM versioning automatico dal tag Git
PyPI Trusted Publishers → identità del workflow verificata dal repository
git tag v1.2.3          → trigger per il rilascio automatico su PyPI
```

Senza una comprensione solida di Git, i moduli [23](23-packaging-distribuzione.md), [27](27-ci-cd-per-python.md) e [32](32-packaging-distribuzione.md) rimangono superficiali.

---

## 3. Installazione e Configurazione

### 3.1 Installazione su Windows

**Metodo raccomandato — winget (Windows Package Manager):**

```powershell
# Installazione
winget install --id Git.Git -e --source winget

# Verifica
git --version
# git version 2.45.2.windows.1
```

**Git for Windows** include:
- `git.exe` — il CLI Git
- **Git Bash** — ambiente POSIX (bash, ssh, curl, openssl)
- **Git GUI** — interfaccia grafica minimale
- **Git Credential Manager** — gestione credenziali sicura

**Opzione alternativa — Scoop:**

```powershell
scoop install git
```

**Configurazione line endings su Windows:**

```powershell
# Converti LF → CRLF al checkout, CRLF → LF al commit
# Comportamento raccomandato per sviluppatori Windows
git config --global core.autocrlf true
```

> **Best practice Python:** i file Python usano LF (`\n`). Se lavori in un team misto Windows/Linux/macOS, imposta `core.autocrlf = input` su Linux/macOS e `true` su Windows, oppure gestisci gli endings con `.gitattributes` (vedi sezione [14](#14-sicurezza-e-secrets)).

### 3.2 Installazione su macOS

**Metodo raccomandato — Homebrew:**

```bash
# Homebrew deve essere già installato (https://brew.sh)
brew install git

# Verifica che sia il git di Homebrew, non quello di Apple
which git
# /opt/homebrew/bin/git

git --version
# git version 2.45.2
```

**Alternative:**

```bash
# Xcode Command Line Tools (include git Apple)
xcode-select --install

# MacPorts
sudo port install git
```

### 3.3 Installazione su Linux

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install git

# Fedora / RHEL / CentOS Stream
sudo dnf install git

# Arch Linux / Manjaro
sudo pacman -S git

# openSUSE
sudo zypper install git

# Verifica
git --version
```

**Ultima versione da sorgente (se il package manager è indietro):**

```bash
sudo add-apt-repository ppa:git-core/ppa   # Ubuntu
sudo apt update && sudo apt install git
```

### 3.4 Configurazione Globale

La configurazione globale risiede in `~/.gitconfig`. Questi comandi vanno eseguiti una volta dopo l'installazione.

**Identità — obbligatoria:**

```bash
git config --global user.name "Mario Rossi"
git config --global user.email "mario.rossi@example.com"
```

**Editor predefinito:**

```bash
# VS Code
git config --global core.editor "code --wait"

# Neovim
git config --global core.editor "nvim"

# nano (comodo per chi non vuole configurare Vim)
git config --global core.editor "nano"
```

**Diff e merge tool:**

```bash
# VS Code come diff/merge tool
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
```

**Alias utili:**

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.lg "log --oneline --decorate --graph --all"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.unstage "restore --staged"
```

**Default branch name:**

```bash
# Modern standard: main invece di master
git config --global init.defaultBranch main
```

**Pull behavior:**

```bash
# Rebase invece di merge al pull (evita merge commit inutili)
git config --global pull.rebase true
```

**Il file `~/.gitconfig` risultante:**

```ini
[user]
    name = Mario Rossi
    email = mario.rossi@example.com

[core]
    editor = code --wait
    autocrlf = input      # Linux/macOS; su Windows usa: true

[init]
    defaultBranch = main

[pull]
    rebase = true

[diff]
    tool = vscode

[difftool "vscode"]
    cmd = code --wait --diff $LOCAL $REMOTE

[merge]
    tool = vscode

[mergetool "vscode"]
    cmd = code --wait $MERGED

[alias]
    st = status
    co = checkout
    br = branch
    lg = log --oneline --decorate --graph --all
    last = log -1 HEAD --stat
    unstage = restore --staged
```

**Verifica configurazione:**

```bash
git config --list --show-origin
```

### 3.5 SSH Key per GitHub

HTTPS funziona ma richiede di inserire le credenziali (o usare il Credential Manager). SSH è più comodo per uso quotidiano.

**Generare una chiave SSH (algoritmo Ed25519, raccomandato):**

```bash
# -t ed25519: algoritmo moderno (più sicuro e veloce di RSA 4096)
# -C: commento identificativo (di solito la tua email)
ssh-keygen -t ed25519 -C "mario.rossi@example.com"

# Output:
# Generating public/private ed25519 key pair.
# Enter file in which to save the key (~/.ssh/id_ed25519):  [Invio]
# Enter passphrase (empty for no passphrase): [scegli una passphrase]
# Enter same passphrase again: [ripeti]
# Your identification has been saved in /home/mario/.ssh/id_ed25519
# Your public key has been saved in /home/mario/.ssh/id_ed25519.pub
```

**Avviare ssh-agent e aggiungere la chiave:**

```bash
# Linux/macOS
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Windows (Git Bash)
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519
```

**Copiare la chiave pubblica:**

```bash
# Linux
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard
# oppure:
cat ~/.ssh/id_ed25519.pub

# macOS
pbcopy < ~/.ssh/id_ed25519.pub

# Windows (Git Bash)
clip < ~/.ssh/id_ed25519.pub
```

**Aggiungere la chiave a GitHub:**
1. GitHub → Settings → SSH and GPG keys → New SSH key
2. Incolla la chiave pubblica (inizia con `ssh-ed25519`)
3. Dai un nome descrittivo (es. "MacBook Pro lavoro")

**Configurare `~/.ssh/config` per più account:**

```
# Account principale
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519

# Account aziendale
Host github-lavoro
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_lavoro
```

Con questa configurazione, i repository aziendali si clonano come:
```bash
git clone git@github-lavoro:mia-azienda/repo.git
```

**Verifica connessione:**

```bash
ssh -T git@github.com
# Hi mario-rossi! You've successfully authenticated,
# but GitHub does not provide shell access.
```

### 3.6 GitHub CLI

`gh` è lo strumento ufficiale GitHub da riga di comando. Indispensabile per creare PR, review, release e gestire Actions senza aprire il browser.

```bash
# Installazione
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh

# Windows
winget install --id GitHub.cli

# Autenticazione
gh auth login
# ? What account do you want to log into? GitHub.com
# ? What is your preferred protocol for Git operations? SSH
# ? Upload your SSH public key to your GitHub account? ~/.ssh/id_ed25519.pub
# ? How would you like to authenticate GitHub CLI? Login with a web browser

# Verifica
gh auth status
```

---

## 4. Il Modello Dati di Git

Capire come Git funziona internamente aiuta a prevenire errori e a usare i comandi avanzati con fiducia.

### Object Store

Git è essenzialmente un **database chiave-valore content-addressable**. Ogni oggetto è identificato dall'hash SHA-1 (o SHA-256 nelle versioni moderne) del suo contenuto.

Esistono quattro tipi di oggetti:

| Tipo | Descrizione | Esempio |
|------|-------------|---------|
| **blob** | Contenuto di un file | `git cat-file -p abc123` |
| **tree** | Directory: elenco di blob e altri tree | Corrisponde a una cartella |
| **commit** | Snapshot + metadati (autore, data, messaggio, parent) | Ogni `git commit` crea un oggetto commit |
| **tag** | Puntatore annotato a un commit (con firma GPG opzionale) | `git tag -a v1.0.0` |

```
commit abc123
│
├── tree def456
│   ├── blob 111aaa  → src/__init__.py
│   ├── blob 222bbb  → src/models.py
│   └── tree 333ccc  → tests/
│       └── blob 444ddd → tests/test_models.py
│
└── parent 789xyz   (commit precedente)
```

**Ispezionare gli oggetti internamente:**

```bash
# Tipo di un oggetto
git cat-file -t HEAD
# commit

# Contenuto di un commit
git cat-file -p HEAD
# tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904
# parent f1e2d3c...
# author Mario Rossi <mario@example.com> 1720000000 +0200
# committer Mario Rossi <mario@example.com> 1720000000 +0200
#
# feat: aggiunge validazione input utente

# Oggetti nel repository
git count-objects -vH
```

### Refs (Riferimenti)

I **ref** sono alias leggibili per gli hash SHA-1. Si trovano in `.git/refs/`.

```
.git/
├── HEAD              → ref: refs/heads/main  (puntatore al branch corrente)
├── refs/
│   ├── heads/
│   │   ├── main      → abc123...   (branch locale)
│   │   └── feature/login → def456...
│   ├── remotes/
│   │   └── origin/
│   │       ├── main  → xyz789...   (tracking branch)
│   │       └── HEAD
│   └── tags/
│       └── v1.0.0    → ghi012...
```

### Staging Area (Index)

Lo **staging area** (anche detto *index*) è la caratteristica più incompresa di Git. È uno strato intermedio tra la working directory e il repository:

```
Working Directory  →  [git add]  →  Staging Area  →  [git commit]  →  Repository
(file modificati)                   (index/.git/index)                  (commit obj)
```

Questo design permette commit parziali: puoi modificare tre file ma committarne solo due.

### Il DAG (Directed Acyclic Graph)

La storia di Git è un **grafo aciclico orientato** di commit. Ogni commit punta al padre (o ai padri nel caso di un merge commit). Non esistono cicli.

```
A ← B ← C ← D (main)
          ↑
          └── E ← F (feature/login)
```

Visualizzare il DAG:

```bash
git log --oneline --decorate --graph --all
# * f3a2b1c (HEAD -> main, origin/main) fix: corregge validazione email
# * 8e4d2a0 feat: aggiunge endpoint /users
# | * 2c1f9b3 (feature/login) feat: login con OAuth2
# | * 7a3e1d2 feat: aggiunge form di login
# |/
# * 1b4c8f0 chore: inizializzazione progetto
```

---

## 5. Flusso di Lavoro Fondamentale

### 5.1 init, add, commit

**Inizializzare un nuovo repository:**

```bash
# Creare directory e inizializzare Git
mkdir mio-progetto-python
cd mio-progetto-python
git init
# Initialized empty Git repository in /home/mario/mio-progetto-python/.git/

# Oppure: creare repository in una directory esistente
cd progetto-esistente
git init
```

**Struttura tipica di un progetto Python al momento del `git init`:**

```bash
# Inizializzare con uv (raccomandato - vedi 24-virtual-environments.md)
uv init mio-progetto-python
cd mio-progetto-python
git init
git add .
git commit -m "chore: inizializzazione progetto con uv"
```

**Aggiungere file alla staging area:**

```bash
# Aggiungere un file specifico
git add src/models.py

# Aggiungere tutti i file modificati
git add .

# Aggiungere in modo interattivo (scegli chunk per chunk)
git add -p src/models.py

# Aggiungere tutti i file .py
git add "*.py"

# Aggiungere una directory
git add tests/
```

**Creare un commit:**

```bash
# Commit con messaggio inline
git commit -m "feat: aggiunge modello User con validazione email"

# Commit con editor (per messaggi lunghi)
git commit

# Commit saltando la staging area (solo file già tracciati)
git commit -am "fix: corregge logica di autenticazione"
```

**Esempio di sessione completa:**

```bash
$ mkdir api-progetto && cd api-progetto
$ git init
Initialized empty Git repository in /home/mario/api-progetto/.git/

$ uv init .
Initialized project `api-progetto` at `/home/mario/api-progetto`

$ cat > src/api_progetto/models.py << 'EOF'
from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
    name: str
EOF

$ git add .
$ git status
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .python-version
        new file:   README.md
        new file:   pyproject.toml
        new file:   src/api_progetto/__init__.py
        new file:   src/api_progetto/models.py

$ git commit -m "chore: inizializzazione progetto con uv e modello User"
[main (root-commit) 4f2a1b3] chore: inizializzazione progetto con uv e modello User
 5 files changed, 42 insertions(+)
 create mode 100644 .python-version
 create mode 100644 README.md
 create mode 100644 pyproject.toml
 create mode 100644 src/api_progetto/__init__.py
 create mode 100644 src/api_progetto/models.py
```

### 5.2 status, log, diff

**`git status` — stato della working directory:**

```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   src/api_progetto/models.py

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   tests/test_models.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        src/api_progetto/services.py

# Versione compatta
$ git status -s
M  src/api_progetto/models.py    # staged (M verde)
 M tests/test_models.py           # not staged (M rosso)
?? src/api_progetto/services.py   # untracked
```

**`git log` — storia dei commit:**

```bash
# Log standard
git log

# Compatto — un commit per riga
git log --oneline
# 4f2a1b3 chore: inizializzazione progetto
# a1b2c3d feat: aggiunge endpoint /users
# ...

# Con grafo e tutti i branch
git log --oneline --decorate --graph --all

# Con statistiche file
git log --stat

# Con diff completo (patch)
git log -p

# Ultimi N commit
git log -5

# Commit di un autore
git log --author="Mario Rossi"

# Commit che toccano un file
git log --follow -- src/api_progetto/models.py

# Commit in un range di date
git log --after="2026-01-01" --before="2026-07-01"

# Ricerca nel messaggio di commit
git log --grep="feat:"

# Ricerca nel contenuto (pickaxe)
git log -S "def validate_email"
```

**`git diff` — differenze:**

```bash
# Diff working directory vs staging area (modifiche NON staged)
git diff

# Diff staging area vs ultimo commit (modifiche staged)
git diff --staged
# oppure:
git diff --cached

# Diff tra due commit
git diff abc123 def456

# Diff tra branch
git diff main feature/login

# Diff di un file specifico
git diff -- src/api_progetto/models.py

# Diff con statistiche (senza contenuto)
git diff --stat HEAD~3

# Output in formato word-diff (utile per documentazione/testi)
git diff --word-diff
```

### 5.3 .gitignore per Python

Il file `.gitignore` alla radice del repository specifica i pattern di file e directory che Git deve ignorare.

**`.gitignore` completo per un progetto Python moderno:**

```gitignore
# ============================================================
# Python — bytecode e cache
# ============================================================
__pycache__/
*.py[cod]
*$py.class
*.so
*.pyd

# ============================================================
# Virtual environments
# ============================================================
.venv/
venv/
env/
ENV/
.env.local

# uv
.uv/

# Poetry
.poetry/

# ============================================================
# Distribution / Packaging
# ============================================================
dist/
build/
*.egg-info/
*.egg
MANIFEST
wheels/
share/python-wheels/
.installed.cfg

# ============================================================
# Testing
# ============================================================
.pytest_cache/
.coverage
.coverage.*
coverage.xml
htmlcov/
.tox/
.nox/

# ============================================================
# Type checkers
# ============================================================
.mypy_cache/
.pytype/
.pyre/
pyrightconfig.json  # Non ignorare se stai configurando pyright

# ============================================================
# Linting e formatting
# ============================================================
.ruff_cache/

# ============================================================
# Ambienti e segreti — CRITICO
# ============================================================
.env
.env.*
!.env.example      # .env.example è ok: non contiene segreti reali
*.key
*.pem
secrets.yaml
secrets.json

# ============================================================
# Editor e IDE
# ============================================================
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store          # macOS
Thumbs.db          # Windows

# ============================================================
# Jupyter Notebook
# ============================================================
.ipynb_checkpoints/
*.ipynb            # Rimuovi se vuoi tracciare i notebook

# ============================================================
# Documentazione generata
# ============================================================
site/              # MkDocs
docs/_build/       # Sphinx
```

**Creare un `.gitignore` con `gh` o da GitHub:**

```bash
# Usando GitHub CLI
gh api repos/github/gitignore/templates/Python \
  --jq '.source' > .gitignore

# Oppure tramite gitignore.io (curl)
curl -sL https://www.toptal.com/developers/gitignore/api/python,venv,macos,windows,linux \
  > .gitignore
```

**Pattern avanzati:**

```gitignore
# Ignora tutti i file .log ovunque
**/*.log

# Ignora solo in una directory specifica
/logs/*.log

# Non ignorare un file specifico (negation)
!important.log

# Ignora directory ma non i file con quel nome
build/

# Ignora file con quel nome ovunque
*.pyc
```

**Controllare cosa viene ignorato:**

```bash
# Lista file ignorati
git status --ignored

# Perché un file viene ignorato
git check-ignore -v percorso/al/file.pyc
# .gitignore:3:*.py[cod]   percorso/al/file.pyc
```

**Aggiungere file già tracciati a `.gitignore`:**

```bash
# Se un file è già nel repository e vuoi ignorarlo:
git rm --cached percorso/al/file.env
echo "*.env" >> .gitignore
git add .gitignore
git commit -m "chore: aggiunge .env a .gitignore"
```

> **Nota:** `git rm --cached` rimuove il file dal repository ma NON dal filesystem locale.

### 5.4 Annullare Modifiche

Questa è l'area in cui gli sviluppatori commettono più errori. La tabella seguente chiarisce quale comando usare in base alla situazione.

| Situazione | Comando | Sicuro? |
|-----------|---------|---------|
| Scartare modifiche in working dir (un file) | `git restore file.py` | Sì* |
| Scartare TUTTE le modifiche non staged | `git restore .` | Sì* |
| Rimuovere un file dalla staging area | `git restore --staged file.py` | Sì |
| Modificare il messaggio dell'ultimo commit | `git commit --amend -m "..."`  | Solo locale |
| Annullare l'ultimo commit ma tenere le modifiche | `git reset --soft HEAD~1` | Solo locale |
| Annullare l'ultimo commit e svuotare staging | `git reset HEAD~1` | Solo locale |
| Annullare l'ultimo commit e scartare tutto | `git reset --hard HEAD~1` | Pericoloso |
| Creare un commit che annulla un commit passato | `git revert abc123` | Sì (sicuro anche in remoto) |

*"Sì" = non perde dati già committati. Le modifiche non committate vengono perse senza conferma.

```bash
# Annullare modifiche non staged a un file
git restore src/models.py

# Annullare tutte le modifiche non staged
git restore .

# Rimuovere dalla staging area senza perdere le modifiche
git restore --staged src/models.py

# Annullare l'ultimo commit mantenendo le modifiche in staging
git reset --soft HEAD~1

# Annullare l'ultimo commit (modifiche tornano non staged)
git reset HEAD~1

# PERICOLOSO: annullare commit e perdere le modifiche
git reset --hard HEAD~1

# Creare un commit inverso (safe per branch condivisi)
git revert HEAD
git revert abc123def456   # annulla un commit specifico
```

> **Best practice:** Usa sempre `git revert` per annullare commit già presenti su un branch condiviso (origin/main). Non usare mai `git reset --hard` su branch condivisi: riscrive la storia e causa problemi a tutti gli altri.

---

## 6. Branch e Merge

### 6.1 Concetto di Branch

Un **branch** in Git è semplicemente un puntatore leggero a un commit. Creare un branch significa creare un file di 41 byte in `.git/refs/heads/`. Questa leggerezza è fondamentale: in Git si usa un branch per ogni feature, fix, esperimento.

```bash
# Elenco branch locali
git branch
# * main
#   feature/login
#   fix/validazione-email

# Elenco branch locali e remoti
git branch -a
# * main
#   feature/login
#   remotes/origin/main
#   remotes/origin/feature/login

# Branch con ultimo commit
git branch -v
# * main         4f2a1b3 chore: inizializzazione progetto
#   feature/login a1b2c3d feat: aggiunge form di login
```

### 6.2 Feature Branch Workflow

Il **Feature Branch Workflow** è il pattern standard per i team che usano GitHub/GitLab:

```
main  ─────────────────────────────────────── (sempre stabile, rilasciabile)
         │                         ↑
         └─ feature/login ─────────┘
               │  commit  commit  commit  merge
```

**Ciclo di vita completo:**

```bash
# 1. Aggiornare main locale
git switch main
git pull origin main

# 2. Creare il branch feature
git switch -c feature/autenticazione-oauth

# -c crea e fa il checkout del nuovo branch
# Il branch parte dall'attuale HEAD (main)

# 3. Lavorare sul branch
# ... modifiche ai file ...
git add src/auth/oauth.py tests/test_oauth.py
git commit -m "feat(auth): aggiunge provider OAuth2 Google"

# ... altre modifiche ...
git add src/auth/middleware.py
git commit -m "feat(auth): aggiunge middleware di autenticazione JWT"

# 4. Push del branch su origin
git push -u origin feature/autenticazione-oauth

# 5. Aprire una Pull Request (vedi sezione 7)
gh pr create --title "feat: autenticazione OAuth2" \
  --body "Aggiunge login con Google via OAuth2. Closes #42."

# 6. Dopo il merge della PR, pulizia locale
git switch main
git pull origin main
git branch -d feature/autenticazione-oauth         # elimina branch locale
git push origin --delete feature/autenticazione-oauth  # elimina branch remoto
```

**Naming convention per i branch:**

| Tipo | Pattern | Esempio |
|------|---------|---------|
| Feature | `feature/<descrizione>` | `feature/login-oauth` |
| Bug fix | `fix/<descrizione>` | `fix/validazione-email-null` |
| Hotfix produzione | `hotfix/<descrizione>` | `hotfix/sql-injection-login` |
| Release | `release/<versione>` | `release/2.1.0` |
| Refactoring | `refactor/<descrizione>` | `refactor/modello-utente` |
| Documentazione | `docs/<descrizione>` | `docs/guida-installazione` |

### 6.3 Merge — Fast-Forward e 3-Way

**Fast-Forward Merge** — nessun commit di merge creato:

```
Prima:
main  → A → B → C
feature          → D → E

Dopo (fast-forward):
main  → A → B → C → D → E
```

Si verifica quando il branch da mergiare è avanti rispetto al base branch senza divergenza.

**3-Way Merge** — crea un merge commit:

```
Prima:
main    → A → B → C → F
feature          → D → E

Dopo (3-way merge, crea commit M):
main    → A → B → C → F → M
feature          → D → E ──┘
```

```bash
# Merge standard (preferisce fast-forward quando possibile)
git merge feature/autenticazione-oauth

# Forza sempre un merge commit (utile per tracciare la storia delle feature)
git merge --no-ff feature/autenticazione-oauth

# Squash merge (combina tutti i commit del branch in uno solo)
git merge --squash feature/autenticazione-oauth
git commit -m "feat: autenticazione OAuth2 (squash)"
```

> **Best practice Python:** Per le librerie open source, `--no-ff` nella PR rende la storia più leggibile (si vede dove inizia e finisce ogni feature). Per progetti con Conventional Commits e `python-semantic-release`, i commit squashed con messaggio convenzionale sono preferibili.

### 6.4 Risoluzione Conflitti

Un conflitto avviene quando due branch hanno modificato le stesse righe dello stesso file.

```bash
$ git merge feature/login
Auto-merging src/api_progetto/models.py
CONFLICT (content): Merge conflict in src/api_progetto/models.py
Automatic merge failed; fix conflicts and then commit the result.
```

**Il file in conflitto:**

```python
<<<<<<< HEAD
class User:
    def validate_email(self, email: str) -> bool:
        import re
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
=======
class User:
    def validate_email(self, email: str) -> bool:
        from email_validator import validate_email
        try:
            validate_email(email)
            return True
        except Exception:
            return False
>>>>>>> feature/login
```

**Markers del conflitto:**
- `<<<<<<< HEAD` — inizio della versione locale (HEAD)
- `=======` — separatore
- `>>>>>>> feature/login` — fine della versione del branch che si sta mergiando

**Risoluzione manuale:**

```python
# Scegli una versione, o crea una versione combinata:
class User:
    def validate_email(self, email: str) -> bool:
        """Valida email usando email-validator con fallback regex."""
        try:
            from email_validator import validate_email, EmailNotValidError
            validate_email(email)
            return True
        except ImportError:
            import re
            return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
        except Exception:
            return False
```

**Completare il merge:**

```bash
# Dopo aver risolto il conflitto
git add src/api_progetto/models.py

# Verificare che non ci siano altri conflitti
git status

# Completare il merge
git commit
# Il messaggio di merge è pre-compilato, puoi modificarlo

# Oppure abortire il merge e ricominciare
git merge --abort
```

**Tool grafici per la risoluzione:**

```bash
# VS Code (raccomandato)
git mergetool

# vimdiff
git mergetool --tool=vimdiff

# IntelliJ / PyCharm — integrazione nativa
```

### 6.5 Merge vs Rebase

| Aspetto | `git merge` | `git rebase` |
|---------|-------------|--------------|
| Storia | Non lineare (merge commit) | Lineare (riscrittura dei commit) |
| SHA dei commit | Invariati | Cambiati (nuovi hash) |
| Conflitti | Una volta sola | A ogni commit riapplicato |
| Sicurezza su branch condivisi | Sì | **No** — non usare su branch pubblici |
| Tracciabilità feature | Sì (merge commit) | No (storia flat) |
| Preferito da | GitHub flow, team numerosi | Maintainer di librerie, storia pulita |

```bash
# Rebase del branch feature su main aggiornato
git switch feature/login
git rebase main

# Se ci sono conflitti durante il rebase:
# Risolvi il conflitto, poi:
git add file-in-conflitto.py
git rebase --continue

# Oppure salta il commit corrente (raramente corretto)
git rebase --skip

# Oppure abbandona il rebase
git rebase --abort
```

> **Regola d'oro:** Non fare mai rebase di commit già pushati su un branch condiviso (origin/main, origin/develop). Il rebase riscrive gli SHA dei commit, causando divergenza per chiunque abbia già clonato quei commit.

---

## 7. GitHub — Remote Repository

### 7.1 clone, remote, push, pull, fetch

**Clonare un repository:**

```bash
# HTTPS (richiede credenziali o token)
git clone https://github.com/utente/repo.git

# SSH (richiede chiave SSH configurata — raccomandato)
git clone git@github.com:utente/repo.git

# Con nome directory personalizzato
git clone git@github.com:utente/repo.git mio-nome-locale

# Solo un branch specifico (più veloce per repo grandi)
git clone --branch main --single-branch git@github.com:utente/repo.git

# Clone superficiale (senza tutta la storia — utile in CI)
git clone --depth 1 git@github.com:utente/repo.git
```

**Gestire i remote:**

```bash
# Elenco remote
git remote -v
# origin  git@github.com:mario-rossi/api-progetto.git (fetch)
# origin  git@github.com:mario-rossi/api-progetto.git (push)

# Aggiungere un remote
git remote add upstream git@github.com:organizzazione/api-progetto.git

# Rinominare
git remote rename origin vecchio

# Rimuovere
git remote remove vecchio

# Cambiare URL (es. da HTTPS a SSH)
git remote set-url origin git@github.com:mario-rossi/api-progetto.git
```

**fetch, pull, push:**

```bash
# fetch: scarica le modifiche remote SENZA integrarle nella working dir
git fetch origin
git fetch --all         # tutti i remote
git fetch --prune       # rimuove tracking branch di branch remoti eliminati

# pull: fetch + merge (o rebase se pull.rebase=true)
git pull origin main
git pull                # usa il tracking branch configurato

# push
git push origin main
git push -u origin feature/login   # -u imposta il tracking branch
git push                           # usa il tracking branch

# Force push (PERICOLOSO su branch condivisi — solo per branch personali)
git push --force-with-lease        # più sicuro di --force: fallisce se qualcuno ha pushato nel frattempo

# Push di tag
git push origin v1.2.3             # push di un tag specifico
git push origin --tags             # push di tutti i tag locali
```

**Dopo un fetch, vedere le differenze:**

```bash
git fetch origin
git log HEAD..origin/main --oneline    # commit su origin non ancora in locale
git diff HEAD..origin/main             # diff completo
git merge origin/main                  # integrare le modifiche
```

### 7.2 Fork e Pull Request Workflow

Il **Fork + PR workflow** è il pattern standard per contribuire a progetti open source e per team che usano branch protection su `main`.

```
Repository originale (upstream)
    origin/main ─────────────────────────────
                │                           ↑
                fork                        PR
                │                           │
    Il tuo fork (origin)               gh pr create
    origin/main ──────────────────────────
                         │
                    feature/branch
```

**Workflow completo:**

```bash
# 1. Fork del repository su GitHub (UI o CLI)
gh repo fork organizzazione/repo --clone --remote

# Questo crea:
# - fork su github.com/tuo-utente/repo
# - clone locale con origin → il tuo fork
# - upstream → repository originale

# 2. Creare branch feature
git switch -c feature/nuova-funzionalita

# 3. Modifiche e commit
git add .
git commit -m "feat: aggiunge nuova funzionalità"

# 4. Sincronizzare con upstream prima del push
git fetch upstream
git rebase upstream/main

# 5. Push su origin (il tuo fork)
git push -u origin feature/nuova-funzionalita

# 6. Aprire PR verso upstream
gh pr create \
  --repo organizzazione/repo \
  --title "feat: nuova funzionalità" \
  --body "Closes #123. Aggiunge X perché Y."
```

### 7.3 GitHub CLI Essenziale

```bash
# Creare PR
gh pr create --fill           # usa il commit message come titolo/corpo
gh pr create --draft          # PR in bozza

# Elenco PR
gh pr list
gh pr list --state merged

# Checkout di una PR (per review locale)
gh pr checkout 42

# Review di una PR
gh pr review 42 --approve
gh pr review 42 --request-changes --body "Manca la gestione dell'errore a riga 47"

# Merge di una PR
gh pr merge 42 --squash       # squash merge
gh pr merge 42 --rebase       # rebase merge
gh pr merge 42 --merge        # merge commit

# Status dei workflow CI/CD
gh run list
gh run watch                  # streaming log dell'esecuzione corrente

# Creare una release
gh release create v1.2.3 dist/*.whl dist/*.tar.gz \
  --title "v1.2.3 — Autenticazione OAuth" \
  --notes "$(git-cliff --tag v1.2.3 --unreleased --strip all)"
```

---

## 8. Tag e Versioning Semantico

### 8.1 Tag leggeri vs annotati

Git supporta due tipi di tag:

| Tipo | Comando | Oggetto Git | Firmabile GPG | Uso consigliato |
|------|---------|------------|---------------|-----------------|
| Leggero | `git tag v1.0.0` | ref a commit | No | Test locali, segnalibri temporanei |
| Annotato | `git tag -a v1.0.0 -m "..."` | oggetto tag | Sì | Release ufficiali — **sempre usare** |

```bash
# Tag annotato (raccomandato per release)
git tag -a v1.2.3 -m "Release v1.2.3 — fix autenticazione OAuth"

# Tag annotato con firma GPG
git tag -s v1.2.3 -m "Release v1.2.3"

# Tag leggero
git tag v1.2.3-dev

# Elenco tag
git tag
git tag -l "v1.*"       # filtra per pattern

# Informazioni su un tag annotato
git show v1.2.3

# Tag su un commit specifico (non HEAD)
git tag -a v1.2.2 abc123 -m "Hotfix autenticazione"

# Push tag
git push origin v1.2.3
git push origin --tags

# Eliminare un tag
git tag -d v1.2.3-dev
git push origin --delete v1.2.3-dev
```

### 8.2 Semantic Versioning (SemVer)

**Semantic Versioning** (`semver.org`) definisce un contratto con gli utenti tramite il numero di versione `MAJOR.MINOR.PATCH`:

| Componente | Significato | Incrementa quando... |
|------------|-------------|----------------------|
| **MAJOR** | Breaking change | L'API pubblica cambia in modo incompatibile |
| **MINOR** | Nuova funzionalità | Nuove funzionalità backward-compatible |
| **PATCH** | Bug fix | Bug fix backward-compatible |

**Esempi:**

```
1.0.0         → Release iniziale stabile
1.1.0         → Nuova funzionalità backward-compatible
1.1.1         → Bug fix
2.0.0         → Breaking change (rimozione API o cambio signature)
1.0.0-alpha.1 → Pre-release
1.0.0-beta.2  → Beta
1.0.0-rc.1    → Release candidate
1.0.0+build.42 → Build metadata (ignorata per precedenza)
```

### 8.3 PEP 440 — Versioning Python

**PEP 440** è lo standard Python per le versioni di pacchetto (compatibile ma non identico a SemVer):

```
1.2.3          → Release normale
1.2.3.post1    → Post-release (correzione di errore nel processo di rilascio)
1.2.3a1        → Alpha
1.2.3b2        → Beta
1.2.3rc1       → Release candidate
1.2.3.dev0     → Development version
```

**In `pyproject.toml`:**

```toml
[project]
name = "mio-pacchetto"
version = "1.2.3"

# Dipendenze con vincoli di versione
dependencies = [
    "pydantic>=2.0,<3.0",       # >=2.0 e <3.0
    "fastapi~=0.110",            # >=0.110, <0.111 (compatible release)
    "requests>=2.28",
]
```

### 8.4 Automazione del Versioning

**`bump-my-version` (strumento consigliato):**

```bash
# Installazione
uv add --dev bump-my-version

# Configurazione in pyproject.toml
```

```toml
[tool.bumpversion]
current_version = "1.2.3"
commit = true
tag = true
tag_name = "v{new_version}"
message = "chore(release): bump version {current_version} → {new_version}"

[[tool.bumpversion.files]]
filename = "src/mio_pacchetto/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'
```

```bash
# Incrementare versione
bump-my-version bump patch     # 1.2.3 → 1.2.4
bump-my-version bump minor     # 1.2.3 → 1.3.0
bump-my-version bump major     # 1.2.3 → 2.0.0

# Anteprima senza eseguire
bump-my-version bump patch --dry-run
```

**`hatch` versioning da SCM (tag Git):**

```toml
[tool.hatch.version]
source = "vcs"           # legge la versione dall'ultimo tag Git

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
```

Con questo setup `hatch version` riporta la versione derivata dal tag Git più recente.

---

## 9. pre-commit Hooks

### 9.1 Cosa sono i Git Hooks

Git hooks sono script eseguiti automaticamente in corrispondenza di eventi specifici del lifecycle Git.

| Hook | Quando viene eseguito | Uso tipico |
|------|-----------------------|-----------|
| `pre-commit` | Prima di creare il commit | Lint, format, typecheck |
| `commit-msg` | Dopo il messaggio di commit | Validare il formato del messaggio |
| `pre-push` | Prima del push | Test, security scan |
| `post-merge` | Dopo un merge | Reinstallare dipendenze |
| `prepare-commit-msg` | Prima dell'editor del messaggio | Aggiungere template |

I hook risiedono in `.git/hooks/` e sono script eseguibili (bash, Python, qualsiasi cosa). Problema: `.git/` non viene tracciato dal repository, quindi i hook non vengono condivisi con il team.

### 9.2 Il Framework pre-commit

`pre-commit` risolve il problema della condivisione: i hook sono definiti in `.pre-commit-config.yaml`, che fa parte del repository.

```bash
# Installazione
uv add --dev pre-commit

# Installazione dei hook nel repository locale
pre-commit install

# Installazione hook per commit-msg (Conventional Commits)
pre-commit install --hook-type commit-msg

# Esecuzione manuale su tutti i file (utile per la prima configurazione)
pre-commit run --all-files

# Esecuzione su file staged
pre-commit run
```

### 9.3 Configurazione `.pre-commit-config.yaml`

```yaml
# .pre-commit-config.yaml
# Vedi https://pre-commit.com per la documentazione completa

default_language_version:
  python: python3.12

repos:
  # ────────────────────────────────────────────────────────
  # Hook generici (qualità file)
  # ────────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace          # rimuove spazi finali
      - id: end-of-file-fixer            # assicura newline finale
      - id: check-yaml                   # valida YAML
      - id: check-toml                   # valida TOML
      - id: check-json                   # valida JSON
      - id: check-merge-conflict         # blocca se ci sono marker di merge
      - id: check-added-large-files      # blocca file > 500KB
        args: ["--maxkb=500"]
      - id: no-commit-to-branch          # blocca commit diretti su main
        args: ["--branch", "main", "--branch", "master"]
      - id: detect-private-key           # cerca chiavi private nel codice
      - id: debug-statements             # cerca pdb, breakpoint() nel codice Python

  # ────────────────────────────────────────────────────────
  # Ruff — linting e formatting (Python)
  # ────────────────────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.7
    hooks:
      - id: ruff                         # linting
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format                  # formatting (sostituisce black)

  # ────────────────────────────────────────────────────────
  # mypy — type checking
  # ────────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-requests
        args: [--strict, --ignore-missing-imports]

  # ────────────────────────────────────────────────────────
  # Sicurezza
  # ────────────────────────────────────────────────────────
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  # ────────────────────────────────────────────────────────
  # Conventional Commits — validazione messaggio
  # ────────────────────────────────────────────────────────
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert]
```

**Aggiornare i hook alle versioni più recenti:**

```bash
pre-commit autoupdate
```

### 9.4 Hook personalizzati in Python

```yaml
# .pre-commit-config.yaml — hook locale
repos:
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (test veloci)
        entry: uv run pytest tests/unit/ -x -q --no-header
        language: system
        pass_filenames: false
        stages: [pre-commit]

      - id: check-migrations
        name: verifica migrazioni Alembic
        entry: python scripts/check_migrations.py
        language: python
        files: ^(src/.*models\.py|alembic/)
        pass_filenames: false
```

**Script di verifica migrazioni:**

```python
# scripts/check_migrations.py
"""Verifica che tutte le migrazioni Alembic siano aggiornate."""
import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        ["alembic", "check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERRORE: le migrazioni Alembic non sono aggiornate.")
        print("Esegui: alembic revision --autogenerate -m 'descrizione'")
        print(result.stdout)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

> **Cross-reference:** La configurazione completa di pre-commit in CI è trattata in [27-ci-cd-per-python.md — sezione Pre-commit Framework](27-ci-cd-per-python.md#pre-commit-framework).

---

## 10. GitHub Actions per Python

GitHub Actions è la piattaforma CI/CD integrata in GitHub. La configurazione risiede in `.github/workflows/*.yml`. Per la guida completa vedi [27-ci-cd-per-python.md](27-ci-cd-per-python.md). Qui viene presentata la pipeline essenziale.

### 10.1 Pipeline CI Base

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  quality:
    name: Qualità del codice
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Installa uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
          enable-cache: true

      - name: Configura Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Installa dipendenze
        run: uv sync --frozen --all-extras

      - name: Lint con ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Type check con mypy
        run: uv run mypy src/

      - name: Test con pytest
        run: |
          uv run pytest \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            -v

      - name: Audit sicurezza
        run: uv run pip-audit

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12'
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
```

### 10.2 Workflow di Release su PyPI con Trusted Publishers

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

permissions:
  contents: write   # per creare la GitHub Release
  id-token: write   # per OIDC Trusted Publishers

jobs:
  build:
    name: Build pacchetto
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # necessario per hatch-vcs versioning

      - uses: astral-sh/setup-uv@v3

      - name: Build wheel e sdist
        run: uv build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    name: Pubblica su PyPI
    runs-on: ubuntu-latest
    needs: build
    environment:
      name: pypi
      url: https://pypi.org/p/mio-pacchetto
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish su PyPI (Trusted Publishers)
        uses: pypa/gh-action-pypi-publish@release/v1

  release:
    name: Crea GitHub Release
    runs-on: ubuntu-latest
    needs: publish
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Genera changelog con git-cliff
        id: changelog
        run: |
          pip install git-cliff
          git-cliff --current --strip all > RELEASE_NOTES.md

      - name: Crea Release
        uses: softprops/action-gh-release@v2
        with:
          body_path: RELEASE_NOTES.md
          files: dist/*
```

> **Cross-reference:** Trusted Publishers OIDC, configurazione di ambienti GitHub, e strategie di caching avanzate sono in [27-ci-cd-per-python.md](27-ci-cd-per-python.md). Il processo di build del pacchetto è in [23-packaging-distribuzione.md](23-packaging-distribuzione.md) e [32-packaging-distribuzione.md](32-packaging-distribuzione.md).

---

## 11. Convenzioni e Changelog

### 11.1 Conventional Commits

**Conventional Commits** (`conventionalcommits.org`) è una specifica per i messaggi di commit che abilita la generazione automatica del changelog e il versioning semantico.

**Formato:**

```
<tipo>[scope opzionale]: <descrizione>

[corpo opzionale]

[footer opzionale]
```

**Tipi standard:**

| Tipo | Descrizione | SemVer |
|------|-------------|--------|
| `feat` | Nuova funzionalità | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Solo documentazione | — |
| `style` | Formattazione, spazi (no logica) | — |
| `refactor` | Refactoring (no feature, no fix) | — |
| `perf` | Miglioramento performance | PATCH |
| `test` | Aggiunta/modifica test | — |
| `chore` | Build, CI, dipendenze | — |
| `ci` | Modifiche CI/CD | — |
| `build` | Build system | — |
| `revert` | Revert di un commit | — |

**Breaking changes:**

```
feat!: rimuove supporto Python 3.10

BREAKING CHANGE: la versione minima richiesta è ora Python 3.11.
Aggiorna il tuo ambiente prima di fare l'upgrade.
```

Il `!` dopo il tipo e il footer `BREAKING CHANGE:` triggerano un incremento MAJOR.

**Esempi di commit message corretti:**

```bash
# Feature con scope
git commit -m "feat(auth): aggiunge login con Google OAuth2"

# Bug fix con riferimento a issue
git commit -m "fix(models): corregge validazione email con caratteri speciali

Closes #42.

La regex precedente non gestiva correttamente indirizzi come
user+tag@sub.domain.com. Sostituita con email-validator."

# Chore senza scope
git commit -m "chore: aggiorna dipendenze a novembre 2026"

# Breaking change
git commit -m "feat(api)!: rinomina endpoint /user → /users

BREAKING CHANGE: tutti i client devono aggiornare il path
dell'endpoint da /user/{id} a /users/{id}."

# Revert
git commit -m "revert: feat(auth): aggiunge login con Google OAuth2

Reverts commit abc123def456.
Temporaneamente rimosso per problemi con la libreria google-auth."
```

### 11.2 commitizen — Commit Interattivo

`commitizen` guida lo sviluppatore nella scrittura di commit convenzionali.

```bash
# Installazione
uv add --dev commitizen

# Commit interattivo
cz commit
# ? Select the type of change you are committing (Use arrow keys)
# ❯ feat     - A new feature
#   fix      - A bug fix
#   docs     - Documentation only changes
#   style    - Changes that do not affect meaning of code
#   ...
# ? What is the scope of this change? (class or file name): auth
# ? Write a short description: aggiunge login con Google OAuth2
# ? Provide a longer description? (press [enter] to skip): ...

# Bump versione automatico da Conventional Commits
cz bump
# tag: v1.3.0

# Configurazione in pyproject.toml
```

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "1.2.3"
tag_format = "v$version"
version_files = [
    "pyproject.toml:^version",
    "src/mio_pacchetto/__init__.py:^__version__",
]
update_changelog_on_bump = true
changelog_format = "angular"
```

### 11.3 git-cliff — Changelog Automatico

`git-cliff` genera `CHANGELOG.md` dalla storia dei commit convenzionali.

```bash
# Installazione
# macOS
brew install git-cliff

# Da cargo (Rust)
cargo install git-cliff

# Come tool Python
uv tool install git-cliff

# Generare il changelog completo
git-cliff --output CHANGELOG.md

# Solo le modifiche non ancora nel changelog (unreleased)
git-cliff --unreleased

# Per una release specifica
git-cliff --tag v1.3.0

# Stripping dei metadati per release notes
git-cliff --current --strip all
```

**Configurazione `cliff.toml`:**

```toml
[changelog]
header = """
# Changelog\n
Tutte le modifiche notevoli al progetto sono documentate qui.\n
"""
body = """
{% if version %}\
## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
## [Unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
### {{ group | upper_first }}
{% for commit in commits %}
- {% if commit.scope %}**{{ commit.scope }}**: {% endif %}\
{{ commit.message | upper_first }}\
{% if commit.breaking %} [**BREAKING**]{% endif %} \
([{{ commit.id | truncate(length=7, end="") }}]({{ remote.url }}/commit/{{ commit.id }}))\
{% endfor %}
{% endfor %}\n
"""
footer = ""
trim = true

[git]
conventional_commits = true
filter_unconventional = true
split_commits = false
commit_parsers = [
  { message = "^feat", group = "Nuove funzionalità" },
  { message = "^fix", group = "Bug fix" },
  { message = "^perf", group = "Performance" },
  { message = "^refactor", group = "Refactoring" },
  { message = "^docs", group = "Documentazione" },
  { message = "^chore\\(release\\)", skip = true },
  { message = "^chore", group = "Manutenzione" },
]
filter_commits = false
tag_pattern = "v[0-9].*"
```

---

## 12. Comandi Avanzati

### 12.1 stash — Salvataggio Temporaneo

`git stash` salva le modifiche non committate (working dir + staging area) in uno stack temporaneo.

```bash
# Salvare le modifiche correnti
git stash
# Saved working directory and index state WIP on main: 4f2a1b3

# Salva con un messaggio descrittivo
git stash push -m "WIP: refactoring modello User"

# Includere file untracked nello stash
git stash push --include-untracked

# Elenco stash
git stash list
# stash@{0}: WIP on main: WIP: refactoring modello User
# stash@{1}: WIP on feature/login: abc123 feat: aggiunge form

# Applicare l'ultimo stash (lo rimuove dallo stack)
git stash pop

# Applicare lo stash senza rimuoverlo
git stash apply stash@{0}

# Applicare uno stash specifico
git stash pop stash@{1}

# Eliminare uno stash
git stash drop stash@{0}

# Eliminare tutti gli stash
git stash clear

# Vedere il contenuto di uno stash
git stash show -p stash@{0}

# Creare un branch dallo stash
git stash branch nuova-feature stash@{0}
```

**Scenario tipico:**

```bash
# Stai lavorando su un bug fix, arriva una richiesta urgente
git stash push -m "WIP: fix validazione email"

# Risolvi il problema urgente
git switch main
git switch -c hotfix/sql-injection
# ... modifiche urgenti ...
git commit -m "fix: corregge SQL injection in query di ricerca"
git push

# Torna al lavoro precedente
git switch feature/validazione-email
git stash pop
```

### 12.2 cherry-pick

`cherry-pick` applica le modifiche di uno o più commit specifici sul branch corrente.

```bash
# Applicare un commit specifico
git cherry-pick abc123

# Applicare più commit
git cherry-pick abc123 def456 ghi789

# Applicare un range di commit
git cherry-pick abc123..ghi789    # esclude abc123
git cherry-pick abc123^..ghi789   # include abc123

# Cherry-pick senza creare commit (solo staging)
git cherry-pick --no-commit abc123

# In caso di conflitto durante cherry-pick
# Risolvi il conflitto, poi:
git cherry-pick --continue
# Oppure abbandona
git cherry-pick --abort
```

**Scenario tipico — backport di un fix:**

```bash
# Il fix è stato applicato su main come commit abc123
# Deve essere backportato su release/1.2.x

git switch release/1.2.x
git cherry-pick abc123
# [release/1.2.x f3e2d1c] fix: corregge SQL injection in query di ricerca
```

### 12.3 rebase Interattivo

Il **rebase interattivo** (`git rebase -i`) permette di riscrivere la storia locale prima di pushare.

```bash
# Rebase interattivo degli ultimi 4 commit
git rebase -i HEAD~4

# O da un commit specifico
git rebase -i abc123
```

**L'editor mostra:**

```
pick a1b2c3d feat: aggiunge struttura progetto
pick e4f5g6h feat: aggiunge modello User
pick i7j8k9l fix: typo nel messaggio di errore
pick m1n2o3p fix: corregge validazione email

# Comandi:
# p, pick   = usa il commit così com'è
# r, reword = usa il commit, ma modifica il messaggio
# e, edit   = usa il commit, ma fermati per modificare
# s, squash = fonde con il commit precedente
# f, fixup  = come squash, ma scarta il messaggio di questo commit
# d, drop   = rimuove il commit
# b, break  = fermati qui
```

**Esempio — squash di commit di fix in feat:**

```
pick a1b2c3d feat: aggiunge modello User
f    e4f5g6h fix: typo nel messaggio di errore
f    i7j8k9l fix: corregge validazione email
```

Risultato: un unico commit pulito `feat: aggiunge modello User`.

> **Attenzione:** rebase interattivo riscrive gli SHA. Usarlo **solo** su commit non ancora pushati.

### 12.4 bisect — Binary Search per i Bug

`git bisect` usa la ricerca binaria per trovare il commit che ha introdotto un bug.

```bash
# Avviare la sessione bisect
git bisect start

# Marcare il commit corrente come "bad" (contiene il bug)
git bisect bad

# Marcare un commit precedente noto come "good" (non ha il bug)
git bisect good v1.2.0
# Bisecting: 15 revisions left to test after this (roughly 4 steps)
# [abc123] feat: aggiunge endpoint /users

# Git fa checkout a un commit intermedio
# Testa se il bug è presente, poi:
git bisect good    # se questo commit non ha il bug
git bisect bad     # se questo commit ha il bug

# Continua fino a quando Git identifica il commit colpevole:
# abc123def456 is the first bad commit

# Terminare la sessione bisect (torna a HEAD)
git bisect reset
```

**Bisect automatico con uno script:**

```bash
# Script che ritorna 0 = good, 1 = bad
git bisect start
git bisect bad HEAD
git bisect good v1.2.0
git bisect run python scripts/test_regressione.py
```

```python
# scripts/test_regressione.py
"""Testa la regressione: ritorna 0 se OK, 1 se bug presente."""
import sys
from mio_pacchetto.models import User

try:
    user = User(id=1, email="test@example.com", name="Test")
    assert user.validate_email("invalid") is False
    assert user.validate_email("valid@example.com") is True
    sys.exit(0)    # good
except (AssertionError, Exception):
    sys.exit(1)    # bad
```

### 12.5 reflog — Rete di Sicurezza

Il **reflog** registra ogni movimento di HEAD, permettendo di recuperare commit "persi" (dopo reset --hard, rebase sbagliato, ecc.).

```bash
# Vedere il reflog di HEAD
git reflog
# abc123 HEAD@{0}: commit: feat: aggiunge autenticazione
# def456 HEAD@{1}: reset: moving to HEAD~1
# ghi789 HEAD@{2}: commit: feat: aggiunge endpoint utenti
# ...

# Recuperare un commit "perso" dopo reset --hard
git reset --hard HEAD@{2}

# Creare un branch da un reflog entry
git branch branch-salvato HEAD@{3}
```

> Il reflog è **locale** e ha scadenza (default: 90 giorni per commit raggiungibili, 30 giorni per quelli non raggiungibili). Non è un backup del repository remoto.

### 12.6 worktree — Più Working Directory

`git worktree` permette di avere più checkout dello stesso repository in directory diverse — utile per lavorare su branch multipli contemporaneamente senza il costo dello stash/switch.

```bash
# Aggiungere un worktree per un branch esistente
git worktree add ../hotfix-1.2.4 hotfix/1.2.4

# Creare un worktree con un nuovo branch
git worktree add -b feature/nuova ../nuova-feature main

# Elenco worktree
git worktree list

# Rimuovere un worktree
git worktree remove ../hotfix-1.2.4
```

**Scenario tipico:**

```bash
# Stai lavorando su feature/oauth nel repo principale
# Arriva un hotfix urgente su release/1.2.x

git worktree add ../hotfix-release release/1.2.x
cd ../hotfix-release
# ... applica il fix ...
git commit -m "fix: corregge crash su input None"
git push origin release/1.2.x
cd ../repo-principale
git worktree remove ../hotfix-release
# Torni al lavoro sulla feature senza aver toccato nulla
```

---

## 13. Integrazione con Strumenti Python

### 13.1 uv — Dependency Management con Git

`uv` è il gestore di dipendenze e ambienti Python moderno (vedi [24-virtual-environments.md](24-virtual-environments.md)).

**Dipendenze da repository Git:**

```toml
# pyproject.toml — dipendenza da Git
[project]
dependencies = [
    # Branch specifico
    "mia-libreria @ git+https://github.com/utente/mia-libreria.git@main",
    # Tag specifico
    "mia-libreria @ git+https://github.com/utente/mia-libreria.git@v1.2.3",
    # Commit specifico (più riproducibile)
    "mia-libreria @ git+https://github.com/utente/mia-libreria.git@abc123def456",
]
```

```bash
# Installare dipendenze da Git con uv
uv add "git+https://github.com/utente/repo.git@v1.2.3"

# uv.lock garantisce la riproducibilità
uv sync --frozen   # usa esattamente le versioni nel lockfile
```

**Workflow standard con uv e Git:**

```bash
# Inizializzare progetto
uv init progetto
cd progetto
git init
git add .
git commit -m "chore: inizializzazione con uv"

# Aggiungere dipendenza
uv add fastapi
git add pyproject.toml uv.lock
git commit -m "chore: aggiunge fastapi come dipendenza"

# Il lockfile deve sempre essere committato nel repository
# Non aggiungere uv.lock al .gitignore
```

### 13.2 hatch — Build e Versioning

```toml
# pyproject.toml con hatch
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"                    # legge la versione dal tag Git

[tool.hatch.build.hooks.vcs]
version-file = "src/mio_pacchetto/_version.py"
```

```python
# src/mio_pacchetto/__init__.py
from mio_pacchetto._version import __version__  # generato automaticamente da hatch-vcs

__all__ = ["__version__"]
```

```bash
# Vedere la versione corrente (derivata dal tag Git)
hatch version
# 1.2.3.dev4+g4f2a1b3

# Dopo aver creato un tag
git tag -a v1.3.0 -m "Release v1.3.0"
hatch version
# 1.3.0

# Build del pacchetto
hatch build
# [sdist] dist/mio_pacchetto-1.3.0.tar.gz
# [wheel] dist/mio_pacchetto-1.3.0-py3-none-any.whl
```

### 13.3 poetry — Gestione con Git

```bash
# poetry.lock deve essere committato
git add poetry.lock pyproject.toml
git commit -m "chore: aggiorna lockfile poetry"

# Dipendenza da Git in poetry
poetry add git+https://github.com/utente/repo.git#v1.2.3

# Aggiornare una dipendenza specifica
poetry update requests
git add poetry.lock
git commit -m "chore(deps): aggiorna requests a 2.32.0"
```

### 13.4 Pattern per il Changelog delle Dipendenze

```bash
# Vedere tutte le modifiche al lockfile nell'ultimo mese
git log --oneline --after="30 days ago" -- uv.lock poetry.lock requirements*.txt

# Diff dettagliato del lockfile (utile per security audit)
git diff v1.2.0..v1.3.0 -- uv.lock | grep "^[+-]" | grep -v "^---\|^+++"
```

---

## 14. Sicurezza e Secrets

> **Cross-reference:** La sicurezza della supply chain Python (SBOM, pip-audit, Trusted Publishers) è trattata in dettaglio in [18-sicurezza.md](18-sicurezza.md).

### 14.1 La Regola Fondamentale

**Non mettere mai segreti in un repository Git.** Una volta committato, un segreto è potenzialmente compromesso anche se rimosso in seguito — la storia di Git conserva ogni commit.

Segreti che non devono mai entrare in Git:
- API key (AWS, OpenAI, Stripe, ecc.)
- Password di database
- Token OAuth
- Chiavi private SSH/TLS
- Cookie di sessione
- Credenziali SMTP

**Pattern corretto — variabili d'ambiente con `.env`:**

```bash
# .env (NON nel repository)
DATABASE_URL=postgresql://user:password@localhost/db
SECRET_KEY=super-secret-key-32-chars-min
STRIPE_SECRET_KEY=sk_live_...

# .env.example (SÌ nel repository)
DATABASE_URL=postgresql://user:password@localhost/db_name
SECRET_KEY=cambia-questa-chiave-in-produzione
STRIPE_SECRET_KEY=sk_live_...
```

```python
# src/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    stripe_secret_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 14.2 gitleaks — Scansione Automatica

`gitleaks` cerca pattern di segreti nella storia Git e nei file staged.

```bash
# Installazione
# macOS
brew install gitleaks

# Linux
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_x64.tar.gz
tar -xzf gitleaks_8.18.4_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/

# Scansione del repository (storia completa)
gitleaks detect --source .

# Scansione dei soli file staged (per hook pre-commit)
gitleaks protect --staged

# Scansione con report JSON
gitleaks detect --report-format json --report-path gitleaks-report.json
```

**Configurazione `.gitleaks.toml` per ridurre falsi positivi:**

```toml
[extend]
useDefault = true

[[rules]]
id = "chiave-test"
description = "Chiave di test nei fixture — non è un segreto reale"
regex = '''STRIPE_TEST_KEY=sk_test_[a-zA-Z0-9]{24}'''
# Ignora questa regola nei file di test
[rules.allowlists]
  paths = ["tests/fixtures/.*"]

[[allowlists]]
id = "variabili-esempio"
description = "File .env.example con valori placeholder"
paths = [".env.example", "docs/configurazione.md"]
```

### 14.3 GitHub Secret Scanning

GitHub analizza automaticamente ogni push cercando pattern di segreti noti (token GitHub, chiavi AWS, ecc.) e avvisa il proprietario del repository via email se ne trova.

Per abilitare/configurare:
- Repository → Settings → Security → Secret scanning

Per aggiungere pattern personalizzati (GitHub Advanced Security):

```yaml
# .github/secret_scanning.yml
paths-ignore:
  - "tests/fixtures/**"
  - "docs/**"
```

### 14.4 .gitattributes

`.gitattributes` controlla il comportamento di Git su specifici tipi di file: line endings, diff, merge strategy.

```gitattributes
# .gitattributes

# Normalizzazione line endings: LF nel repository, CRLF su Windows al checkout
* text=auto

# File Python: sempre LF
*.py text eol=lf
*.pyi text eol=lf
*.toml text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf
*.md text eol=lf

# File binari: non toccare i line endings
*.png binary
*.jpg binary
*.gif binary
*.ico binary
*.pdf binary
*.whl binary
*.gz binary

# File lock: non fare diff verboso (troppo rumoroso)
uv.lock -diff
poetry.lock -diff

# Merge strategy per file che non devono essere mergiati automaticamente
CHANGELOG.md merge=ours
```

**Configurare driver di diff personalizzati:**

```bash
# diff per file SQLAlchemy models (mostra solo la sezione python)
git config --global diff.python.xfuncname '^(class |def )'
```

```gitattributes
*.py diff=python
```

### 14.5 Rimuovere Segreti dalla Storia Git

Se un segreto è stato accidentalmente committato:

**Passo 1 — Revocare immediatamente il segreto** (prima di qualsiasi altra cosa).

**Passo 2 — Rimuovere dalla storia con `git filter-repo`:**

```bash
# Installazione
uv tool install git-filter-repo

# Rimuovere un file dalla storia completa
git filter-repo --path-glob "*.env" --invert-paths

# Sostituire una stringa in tutta la storia
git filter-repo --replace-text <(echo "sk_live_abc123def456==>***REMOVED***")

# Force push (necessario, attenzione!)
git push origin --force --all
git push origin --force --tags
```

**Passo 3 — Notificare il team.** Tutti devono fare un nuovo clone fresco — i loro repository locali contengono ancora la storia compromessa.

> **BFG Repo Cleaner** è un'alternativa più semplice ma meno potente di `git filter-repo`. Per nuovi progetti usa sempre `git filter-repo`.

### 14.6 Firma dei Commit con GPG / SSH

La firma dei commit garantisce che il commit provenga veramente dall'autore dichiarato.

```bash
# Generare chiave GPG
gpg --full-generate-key

# Ottenere l'ID della chiave
gpg --list-secret-keys --keyid-format=long

# Configurare Git per firmare con GPG
git config --global user.signingkey TUA_KEY_ID
git config --global commit.gpgsign true    # firma tutti i commit automaticamente

# Firmare un commit manualmente
git commit -S -m "feat: aggiunge autenticazione"

# Alternativa moderna — firma con chiave SSH (Git 2.34+)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

GitHub mostra il badge **"Verified"** accanto ai commit firmati.

---

## 15. Riferimenti e Letture Consigliate

### Documentazione Ufficiale

| Risorsa | URL | Note |
|---------|-----|------|
| Git Reference | `https://git-scm.com/docs` | Documentazione ufficiale completa |
| Pro Git Book | `https://git-scm.com/book` | Libro completo, gratuito online, in italiano |
| GitHub Docs | `https://docs.github.com` | Guide GitHub, Actions, CLI |
| GitHub CLI Manual | `https://cli.github.com/manual` | Riferimento `gh` completo |
| Conventional Commits | `https://conventionalcommits.org` | Specifica v1.0.0 |

### Strumenti

| Strumento | URL | Funzione |
|-----------|-----|----------|
| pre-commit | `https://pre-commit.com` | Framework hook |
| gitleaks | `https://github.com/gitleaks/gitleaks` | Secret scanning |
| git-cliff | `https://git-cliff.org` | Generatore changelog |
| commitizen | `https://commitizen-tools.github.io/commitizen` | Commit guidato |
| bump-my-version | `https://github.com/callowayproject/bump-my-version` | Versioning automatico |
| git-filter-repo | `https://github.com/newren/git-filter-repo` | Riscrittura storia |
| gitignore.io | `https://gitignore.io` | Generatore .gitignore |

### Letture Consigliate

- **Pro Git** (Chacon, Straub) — la bibbia di Git, disponibile gratuitamente su `git-scm.com/book`
- **Git Internals** (capitolo 10 di Pro Git) — per capire il modello dati in profondità
- **Oh Shit, Git!** (`ohshitgit.com`) — come uscire da situazioni difficili, spiegato semplicemente
- **Dangit, Git!** — versione senza parolacce del precedente

### Moduli del Corso Collegati

| Modulo | Contenuto rilevante |
|--------|---------------------|
| [08-testing.md](08-testing.md) | pytest, coverage — integrazione con pre-commit e CI |
| [18-sicurezza.md](18-sicurezza.md) | Supply chain security, SBOM, pip-audit, secret management |
| [23-packaging-distribuzione.md](23-packaging-distribuzione.md) | pyproject.toml, wheel, sdist, tag Git come versione |
| [24-virtual-environments.md](24-virtual-environments.md) | uv, poetry, hatch — gestione ambienti e dipendenze |
| [27-ci-cd-per-python.md](27-ci-cd-per-python.md) | GitHub Actions completo, GitLab CI, tox, nox, release automation |
| [31-osservabilita-otel-prometheus.md](31-osservabilita-otel-prometheus.md) | Deployment in produzione — il punto di arrivo della pipeline CI/CD |
| [32-packaging-distribuzione.md](32-packaging-distribuzione.md) | Distribuzione avanzata, Trusted Publishers, PyPI |

---

## Appendice A — Cheat Sheet dei Comandi Principali

### Setup e Configurazione

```bash
git config --global user.name "Nome Cognome"
git config --global user.email "email@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --list --show-origin
```

### Repository

```bash
git init                              # nuovo repository
git clone URL                         # clona da remoto
git clone --depth 1 URL               # clone superficiale
```

### Ciclo di lavoro base

```bash
git status                            # stato working dir
git status -s                         # compatto
git add file.py                       # staging un file
git add .                             # staging tutto
git add -p file.py                    # staging interattivo (chunk)
git commit -m "tipo: messaggio"       # commit
git commit --amend -m "nuovo msg"     # modifica ultimo commit (solo locale)
```

### Log e Diff

```bash
git log --oneline                     # log compatto
git log --oneline --graph --all       # log con grafo
git log --follow -- file.py           # log di un file
git diff                              # modifiche non staged
git diff --staged                     # modifiche staged
git diff main..feature                # diff tra branch
git show abc123                       # contenuto di un commit
```

### Branch

```bash
git branch                            # elenco branch locali
git switch -c feature/nome            # crea e vai al branch
git switch main                       # cambia branch
git merge feature/nome                # merge nel branch corrente
git merge --no-ff feature/nome        # merge con merge commit
git branch -d feature/nome            # elimina branch (sicuro)
git branch -D feature/nome            # elimina branch (forza)
```

### Remote

```bash
git remote -v                         # elenco remote
git fetch origin                      # scarica senza mergiare
git pull                              # fetch + merge/rebase
git push -u origin feature/nome       # push con tracking
git push origin --delete feature/nome # elimina branch remoto
```

### Tag

```bash
git tag                               # elenco tag
git tag -a v1.2.3 -m "Release"        # tag annotato
git push origin v1.2.3               # push tag
git push origin --tags               # push tutti i tag
git tag -d v1.2.3                    # elimina tag locale
```

### Annullare Modifiche

```bash
git restore file.py                   # scarta modifiche non staged
git restore --staged file.py          # rimuove da staging area
git reset --soft HEAD~1               # annulla commit (staged)
git reset HEAD~1                      # annulla commit (unstaged)
git revert abc123                     # commit inverso (sicuro)
```

### Avanzati

```bash
git stash                             # salva modifiche temporaneamente
git stash pop                         # ripristina ultime modifiche
git cherry-pick abc123                # applica commit specifico
git rebase -i HEAD~4                  # rebase interattivo
git bisect start && git bisect bad && git bisect good v1.0
git reflog                            # log movimenti di HEAD
git worktree add ../path branch       # worktree aggiuntivo
```

---

## Appendice B — .gitignore Minimo per Progetto Python

Copia questo file come punto di partenza per qualsiasi nuovo progetto Python:

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
*.pyd

# Virtual environments
.venv/
venv/

# uv
.uv/

# Build
dist/
build/
*.egg-info/

# Testing
.pytest_cache/
.coverage
coverage.xml
htmlcov/
.tox/
.nox/

# Type checkers
.mypy_cache/
.ruff_cache/

# Segreti — CRITICO
.env
.env.*
!.env.example

# Editor
.idea/
.vscode/
*.swp
.DS_Store
```

---

## Appendice C — Tabella di Emergenza

| Problema | Soluzione |
|---------|-----------|
| Ho committato su `main` invece di un branch | `git branch feature/nome && git reset --soft HEAD~1 && git switch feature/nome && git commit` |
| Ho fatto `reset --hard` e ho perso commit | `git reflog` → trovare il commit → `git reset --hard HEAD@{N}` |
| Ho committato un segreto | Revoca il segreto → `git filter-repo --replace-text ...` → force push → nuovo clone per tutti |
| Ho fatto merge del branch sbagliato | `git merge --abort` (se in corso) oppure `git revert -m 1 MERGE_COMMIT_SHA` |
| Il mio push è stato rifiutato | `git pull --rebase origin main` → risolvi eventuali conflitti → `git push` |
| Ho modificato i file sbagliati | `git restore file-sbagliato.py` (se non staged) oppure `git restore --staged file-sbagliato.py` |
| Non ricordo su quale branch sono | `git branch` oppure `git status` |
| Ho bisogno di stare su `main` per un hotfix | `git stash` → `git switch main` → fix → `git switch -` → `git stash pop` |
| Voglio vedere le modifiche prima del commit | `git diff --staged` |
| Ho fatto push di un commit sbagliato | `git revert HEAD` → `git push` (MAI `git reset --hard` + force push su main) |

---

*Documento parte del corso "Python Professionale — dal linguaggio alla produzione" · Aggiornamento: 2026-07-15*
