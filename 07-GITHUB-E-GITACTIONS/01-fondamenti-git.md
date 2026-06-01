---
corso: "GitHub e Git Actions"
fase: "1 — Fondamenti Git"
modulo: 1
titolo: "Fondamenti Git — Guida Completa"
versione: "Git 2.47"
livello: "Intermedio"
prerequisiti: ["Uso base della riga di comando", "Concetti fondamentali di file system"]
obiettivi:
  - "Comprendere l'architettura DAG e il content-addressable storage di Git"
  - "Padroneggiare la three-tree architecture: working tree, index e repository"
  - "Utilizzare reflog, reset e bisect per il recovery e il debugging"
  - "Eseguire merge, rebase e cherry-pick con consapevolezza dei trade-off"
  - "Configurare Git a livello system, global e local con precedenza corretta"
tag: [git, vcs, dag, sha, staging, merge, rebase, reflog, bisect, config]
---

# Fondamenti Git — Guida Completa

> **Modulo 01** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Spiegare come Git modella la storia come grafo aciclico diretto (DAG) di commit
> 2. Distinguere tra working tree, staging area (index) e repository, e gestire i flussi tra i tre stati
> 3. Utilizzare reflog, `git reset` e `git bisect` per recuperare lavoro perso e individuare regressioni
> 4. Eseguire merge, rebase interattivo e cherry-pick scegliendo la strategia appropriata al contesto
> 5. Configurare Git a livello system/global/local e comprendere la catena di precedenza

## Idee guida
1. **Git e DAG di commit; non e snapshot/diff.**
2. **Working tree → index (staging) → repo: 3 stati.**
3. **`git log --graph --oneline` per visualize history.**
4. **`git rebase -i` per cleanup history; mai su shared branch.**
5. **Content-addressable storage: ogni oggetto è identificato dal suo hash SHA.**
6. **Reflog è la rete di sicurezza: niente è veramente perso finché esiste nel reflog.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Git — Il Modello DAG](#architettura-git--il-modello-dag)
- [Content-Addressable Storage e SHA-1](#content-addressable-storage-e-sha-1)
- [Oggetti Git: Blob, Tree, Commit, Tag](#oggetti-git-blob-tree-commit-tag)
- [La Three-Tree Architecture](#la-three-tree-architecture)
- [Concetti Base](#concetti-base)
- [Branching e Merge](#branching-e-merge)
- [Strategie di Merge](#strategie-di-merge)
- [Rebase — Fondamenti e Interactive Rebase](#rebase--fondamenti-e-interactive-rebase)
- [Cherry-Pick](#cherry-pick)
- [Operazioni Avanzate](#operazioni-avanzate)
- [Reflog — La Rete di Sicurezza](#reflog--la-rete-di-sicurezza)
- [Git Bisect — Trovare Bug con Ricerca Binaria](#git-bisect--trovare-bug-con-ricerca-binaria)
- [Interni Git — Struttura .git/](#interni-git--struttura-git)
- [Configurazione — Livelli e Precedenza](#configurazione--livelli-e-precedenza)
- [Alias Git](#alias-git)
- [Credential Helper](#credential-helper)
- [Funzionalità Speciali](#funzionalità-speciali)
- [Troubleshooting Git](#troubleshooting-git)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Esercizi Pratici](#esercizi-pratici)

---

## Panoramica

Git è un sistema di version control distribuito creato da Linus Torvalds nel 2005 per gestire lo sviluppo del kernel Linux. A differenza dei sistemi centralizzati (SVN, CVS), ogni clone è un repository completo con tutta la cronologia — non esiste un singolo punto di fallimento.

### Principi fondamentali

- **Distribuito**: ogni sviluppatore ha una copia completa del repository, inclusa tutta la storia.
- **Basato su snapshot**: ogni commit cattura lo stato completo del progetto, non le differenze incrementali.
- **Integrità crittografica**: ogni oggetto è identificato da un hash SHA, garantendo che nessuna modifica passi inosservata.
- **Branching leggero**: creare un branch è un'operazione istantanea (è solo un puntatore a un commit).
- **Staging area esplicita**: permette di selezionare esattamente cosa includere in un commit.

### Differenze rispetto a sistemi centralizzati

| Caratteristica | Git (distribuito) | SVN (centralizzato) |
|---|---|---|
| Repository | Ogni clone è completo | Singolo server centrale |
| Lavoro offline | Completo (commit, branch, log) | Solo lettura file locali |
| Branching | Istantaneo (puntatore) | Costoso (copia directory) |
| Velocità | Operazioni locali velocissime | Dipende dalla rete |
| Backup | Ogni clone è un backup | Singolo punto di fallimento |
| Integrità | Hash SHA su ogni oggetto | Numeri di revisione sequenziali |

### Perché Git ha vinto

1. **Performance**: le operazioni comuni (commit, diff, log, branch) sono locali e istantanee.
2. **Flessibilità nei workflow**: supporta centralizzato, feature-branch, fork-based, trunk-based.
3. **Ecosistema**: GitHub, GitLab, Bitbucket hanno costruito intere piattaforme attorno a Git.
4. **Comunità**: la documentazione, i tool, e il supporto sono vastissimi.

---

## Architettura Git — Il Modello DAG

### Cos'è un DAG (Directed Acyclic Graph)

La cronologia di Git è un **grafo aciclico diretto** (DAG). Ogni commit è un nodo nel grafo, e le frecce (edge) puntano dal commit figlio al commit genitore (parent).

```
Proprietà del DAG:

1. DIRETTO (Directed):
   Ogni arco ha una direzione — dal figlio al genitore.
   Il commit C punta al suo parent B, B punta ad A.

   A ← B ← C ← D    (la freccia indica "il mio parent è...")

2. ACICLICO (Acyclic):
   Non esistono cicli. Non puoi tornare indietro seguendo
   i puntatori parent. Ogni cammino ha un inizio (root commit)
   e una fine (HEAD o tip del branch).

3. GRAFO (Graph):
   Non è una lista lineare. Un commit può avere:
   - 0 parent → root commit (il primo commit del repo)
   - 1 parent → commit normale
   - 2+ parent → merge commit
```

### Visualizzazione del DAG

```
Cronologia lineare semplice:

  A ← B ← C ← D          (main)
                ↑
               HEAD

Branching e merge:

  A ← B ← C ← F ← G      (main)
       ↑       ↑
       └─ D ← E            (feature — merged in F)

  F è un merge commit con DUE parent: C e E.

Branching multiplo:

  A ← B ← C ← G ← H      (main)
       ↑       ↑
       ├─ D ← E            (feature-1 — merged in G)
       ↑
       └─ F                 (feature-2 — ancora attivo)

Divergenza e convergenza:

       ┌─ D ← E ────────┐
  A ← B ← C ← F ← G ← H (merge di feature ed E insieme)
            ↑        ↑
            └── I ───┘
```

### Perché il DAG è importante

1. **Determinismo**: dato un commit SHA, l'intero sotto-grafo (tutta la storia precedente) è determinato e immutabile.
2. **Merge intelligence**: Git usa il DAG per trovare il **merge base** (l'antenato comune più recente) e calcolare il three-way merge.
3. **Reachability**: un commit è "raggiungibile" da un ref (branch, tag, HEAD) se esiste un cammino nel DAG. Commit non raggiungibili diventano candidati per la garbage collection.
4. **Parallelismo**: il DAG cattura naturalmente lo sviluppo parallelo senza imporre un ordine lineare.

### Come i branch si mappano sul DAG

Un branch in Git non è una copia del codice — è un **puntatore mobile** a un commit nel DAG.

```
refs/heads/main    → punta al commit G
refs/heads/feature → punta al commit E

  A ← B ← C ← G      ← main (HEAD)
       ↑
       └─ D ← E       ← feature

Quando fai un commit su "feature":
  - Git crea un nuovo commit F con parent E
  - Aggiorna refs/heads/feature da E a F

  A ← B ← C ← G      ← main
       ↑
       └─ D ← E ← F   ← feature (HEAD)

Quando fai merge di feature in main:
  - Git crea un merge commit H con parent G e F
  - Aggiorna refs/heads/main da G a H

  A ← B ← C ← G ← H  ← main (HEAD)
       ↑            ↑
       └─ D ← E ← F   ← feature
```

---

## Content-Addressable Storage e SHA-1

### Il concetto

Git è fondamentalmente un **content-addressable filesystem**: un sistema chiave-valore dove la chiave è un hash SHA-1 (o SHA-256 nelle versioni recenti) del contenuto.

```
Content-Addressable = la chiave è derivata dal contenuto stesso

Contenuto del file "hello.txt":     "Hello, World!\n"
                                           │
                                           ▼
                              SHA-1 hash del contenuto
                                           │
                                           ▼
                              8ab686eafeb1f44702738c8b0f24f2567c36da6d
                              └──────────────────────────────────────┘
                                    Questa è la "chiave" (object ID)
```

### Come funziona l'hashing

```bash
# Git calcola l'hash aggiungendo un header al contenuto:
# header = "tipo dimensione\0"
# hash = SHA-1(header + contenuto)

# Esempio per un blob:
echo -n "Hello, World!" | git hash-object --stdin
# Output: 8ab686eafeb1f44702738c8b0f24f2567c36da6d

# Lo stesso contenuto produce SEMPRE lo stesso hash
# Non importa il nome del file, la data, o chi lo ha creato

# Verificare manualmente (senza Git):
printf "blob 13\0Hello, World!" | sha1sum
# Stesso hash!
```

### Proprietà fondamentali

1. **Determinismo**: lo stesso contenuto produce sempre lo stesso hash, ovunque e in qualsiasi momento.
2. **Unicità pratica**: due contenuti diversi producono hash diversi (le collisioni SHA-1 sono computazionalmente impraticabili per Git).
3. **Integrità**: se anche un singolo bit cambia nel contenuto, l'hash è completamente diverso.
4. **Deduplicazione naturale**: se due file hanno lo stesso contenuto, Git li memorizza una sola volta come un unico blob.

### SHA-1 vs SHA-256

```
SHA-1 (legacy, ancora default):
- 160 bit → 40 caratteri esadecimali
- Esempio: 8ab686eafeb1f44702738c8b0f24f2567c36da6d
- Collisioni teoriche note (SHAttered, 2017)
- Per Git, il rischio pratico è trascurabile

SHA-256 (futuro, sperimentale in Git 2.42+):
- 256 bit → 64 caratteri esadecimali
- Nessuna collisione nota
- Attivabile con: git init --object-format=sha256
- Non ancora compatibile con tutti i server/hosting

In pratica: SHA-1 è ancora sicuro per l'uso in Git.
Le collisioni note richiedono attacchi mirati con file PDF
appositamente costruiti — irrilevante per codice sorgente.
```

### Abbreviazione degli hash

```bash
# Git accetta hash abbreviati (purché univoci nel repo):
git show 8ab686e          # Primi 7 caratteri (di solito sufficienti)
git show 8ab686eafe       # Più caratteri per repo grandi

# Controllare la lunghezza minima univoca:
git rev-parse --short HEAD
# Output: a1b2c3d (Git sceglie la lunghezza minima univoca)

# In repo molto grandi (kernel Linux), servono 12+ caratteri
# per evitare ambiguità.
```

---

## Oggetti Git: Blob, Tree, Commit, Tag

### I quattro tipi di oggetto

Git ha esattamente quattro tipi di oggetto, tutti memorizzati nel content-addressable store:

```
BLOB (Binary Large Object)
├── Contiene: il contenuto di un file (senza nome, senza permessi)
├── Hash: SHA-1 del contenuto (con header "blob <size>\0")
└── Nota: due file con lo stesso contenuto → un solo blob

TREE
├── Contiene: lista di entry (modo, tipo, hash, nome)
├── Rappresenta: una directory
├── Ogni entry punta a: un blob (file) o un altro tree (sotto-directory)
└── Include: permessi Unix (100644 file, 100755 eseguibile, 040000 dir)

COMMIT
├── Contiene: puntatore a un tree (root), parent(s), autore, committer,
│   timestamp, messaggio
├── Rappresenta: uno snapshot dell'intero progetto in un momento
└── Parent: 0 (root), 1 (normale), 2+ (merge)

TAG (annotated)
├── Contiene: puntatore a un oggetto (di solito commit), tagger,
│   timestamp, messaggio, opzionalmente firma GPG
├── Rappresenta: un nome permanente per un punto nella storia
└── Differenza da lightweight tag: lightweight è solo un ref file,
    annotated è un oggetto completo
```

### Blob — Il contenuto dei file

```bash
# Creare un blob manualmente:
echo "Ciao mondo" | git hash-object -w --stdin
# Output: <sha> — l'oggetto è ora in .git/objects/

# Il blob NON contiene il nome del file!
# Lo stesso blob può apparire con nomi diversi in tree diversi.

# Verificare il tipo:
git cat-file -t <sha>
# Output: blob

# Leggere il contenuto:
git cat-file -p <sha>
# Output: Ciao mondo

# Verificare la dimensione:
git cat-file -s <sha>
# Output: 11 (bytes)
```

### Tree — Le directory

```bash
# Ispezionare il tree del commit corrente:
git cat-file -p HEAD^{tree}
# Output:
# 100644 blob a1b2c3d...   README.md
# 100644 blob d4e5f6a...   package.json
# 040000 tree b7c8d9e...   src/

# Ogni riga ha: permessi tipo hash nome
# 100644 = file normale
# 100755 = file eseguibile
# 040000 = sotto-directory (altro tree)
# 120000 = symlink
# 160000 = submodule (commit in un altro repo)

# Ispezionare il sotto-tree src/:
git cat-file -p b7c8d9e
# Output:
# 100644 blob f0a1b2c...   index.ts
# 100644 blob 3d4e5f6...   utils.ts
# 040000 tree 789abc0...   components/

# Il tree è ricorsivo: cattura l'intera struttura del filesystem.
```

### Rappresentazione grafica della struttura

```
commit abc1234
│
├── tree: def5678 (root)
│   │
│   ├── blob: aaa1111  →  README.md       (100644)
│   ├── blob: bbb2222  →  package.json    (100644)
│   ├── blob: ccc3333  →  .gitignore      (100644)
│   │
│   └── tree: ddd4444  →  src/
│       │
│       ├── blob: eee5555  →  index.ts     (100644)
│       ├── blob: fff6666  →  utils.ts     (100644)
│       │
│       └── tree: ggg7777  →  components/
│           │
│           ├── blob: hhh8888  →  App.tsx   (100644)
│           └── blob: iii9999  →  Nav.tsx   (100644)
│
├── parent: 987fedc (commit precedente)
├── author: Renan <email> 1716300000 +0200
├── committer: Renan <email> 1716300000 +0200
└── message: "feat: add navigation component"
```

### Commit — Lo snapshot

```bash
# Ispezionare un commit:
git cat-file -p HEAD
# Output:
# tree def567890abcdef1234567890abcdef12345678
# parent 987fedcba0987654321098765432109876543210
# author Renan <email> 1716300000 +0200
# committer Renan <email> 1716300000 +0200
#
# feat: add navigation component

# Il campo "tree" punta allo snapshot COMPLETO del progetto.
# Il campo "parent" punta al commit precedente → forma il DAG.
# author = chi ha scritto il codice
# committer = chi ha creato il commit (possono differire in cherry-pick, rebase)
# Il timestamp è Unix epoch + timezone offset.

# Merge commit con due parent:
git cat-file -p <merge-commit-sha>
# tree ...
# parent aaa111...    (primo parent — il branch IN CUI hai mergiato)
# parent bbb222...    (secondo parent — il branch CHE hai mergiato)
# ...

# Root commit (nessun parent):
git cat-file -p $(git rev-list --max-parents=0 HEAD)
# tree ...
# author ...
# committer ...
# Initial commit
# (nessuna riga "parent")
```

### Tag — Puntatori permanenti

```bash
# Lightweight tag (solo un file ref, nessun oggetto):
git tag v1.0.0
# Crea .git/refs/tags/v1.0.0 contenente lo SHA del commit
# NON crea un oggetto tag

# Annotated tag (crea un oggetto tag completo):
git tag -a v1.0.0 -m "Release 1.0.0 — prima release stabile"
# Crea un oggetto tag in .git/objects/

# Ispezionare un annotated tag:
git cat-file -p v1.0.0
# object abc123... (il commit a cui punta)
# type commit
# tag v1.0.0
# tagger Renan <email> 1716300000 +0200
#
# Release 1.0.0 — prima release stabile

# Tag con firma GPG:
git tag -s v1.0.0 -m "Signed release"
# Richiede chiave GPG configurata

# Quando usare quale:
# Lightweight → marker temporaneo, uso interno
# Annotated  → release, milestone, qualsiasi tag che altri vedranno
# Signed     → release in contesti dove l'integrità è critica
```

---

## La Three-Tree Architecture

### I tre alberi di Git

Git gestisce i file attraverso tre "alberi" (tree). Comprendere questo modello è fondamentale per capire come funzionano `add`, `commit`, `reset`, `checkout` e `restore`.

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   WORKING DIRECTORY │     │   STAGING AREA       │     │   REPOSITORY        │
│   (Working Tree)    │     │   (Index)            │     │   (HEAD)            │
│                     │     │                      │     │                     │
│   I file su disco   │     │   Lo snapshot        │     │   L'ultimo commit   │
│   che vedi e        │ ──> │   preparato per il   │ ──> │   (punta al tree    │
│   modifichi         │ add │   prossimo commit    │ cmt │   dell'ultimo       │
│                     │     │                      │     │   commit)           │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘

     git add ──────────────────>
     git commit ──────────────────────────────────────>
     git checkout / restore <──────────────────────────
     git reset ──────────────<──────────────────────────
```

### Working Directory (Working Tree)

```
Il Working Directory è la directory nel filesystem dove vedi i file.
È l'unico albero che puoi modificare direttamente.

Stati possibili per un file nel working directory:

1. UNTRACKED   → Git non lo conosce (nuovo file, non ancora `git add`)
2. TRACKED     → Git lo conosce (è nel repository)
   ├── UNMODIFIED → Uguale alla versione in staging/HEAD
   ├── MODIFIED   → Diverso dalla versione in staging
   └── DELETED    → Cancellato dal filesystem ma ancora in staging/HEAD
```

### Staging Area (Index)

```
L'Index è un file binario (.git/index) che contiene lo snapshot
del prossimo commit. È una "zona di preparazione".

Perché esiste?
1. Permette commit parziali: puoi aggiungere solo alcuni file/hunk
2. Permette revisione prima del commit: git diff --staged
3. Separa "cosa ho modificato" da "cosa voglio committare"
4. Abilita operazioni come git add -p (staging interattivo per hunk)

L'index NON contiene i file stessi — contiene:
- Percorso del file
- Hash SHA del blob corrispondente
- Metadati (permessi, timestamp)
```

```bash
# Ispezionare l'index:
git ls-files --stage
# Output:
# 100644 a1b2c3d4e5f6... 0   README.md
# 100644 f6e5d4c3b2a1... 0   src/index.ts
#
# Il numero dopo l'hash (0) è lo "stage number":
# 0 = normale
# 1 = merge base (durante conflitto)
# 2 = ours (durante conflitto)
# 3 = theirs (durante conflitto)
```

### Repository (HEAD / Commit History)

```
Il Repository è il database di oggetti in .git/objects/.
HEAD punta al branch corrente, che punta all'ultimo commit.

HEAD → refs/heads/main → commit abc123 → tree def456 → file contents

Quando fai git commit:
1. Git crea un tree dall'index
2. Crea un commit che punta a quel tree
3. Aggiorna il ref del branch corrente al nuovo commit
4. HEAD continua a puntare al branch (che ora punta al nuovo commit)
```

### Come i comandi muovono dati tra i tre alberi

```bash
# git add: Working Dir → Index
git add file.txt
# Copia lo stato corrente di file.txt nell'index

# git commit: Index → Repository
git commit -m "msg"
# Crea un commit dal contenuto dell'index

# git checkout / git restore: Repository → Working Dir
git restore file.txt
# Copia la versione dall'index al working dir
git restore --source HEAD file.txt
# Copia la versione dal commit al working dir

# git reset --soft HEAD~1: sposta solo HEAD
# Index e Working Dir invariati
# Effetto: "uncommit" — il commit sparisce ma i file restano staged

# git reset --mixed HEAD~1: sposta HEAD e resetta Index
# Working Dir invariato
# Effetto: "uncommit + unstage" — file modificati ma non staged

# git reset --hard HEAD~1: sposta HEAD, resetta Index e Working Dir
# Effetto: tutto torna allo stato del commit precedente
# PERICOLOSO: le modifiche non committate sono perse!
```

### Diagramma dei movimenti

```
                    git reset --soft
                 ◄──────────────────
                                    │
  Working Dir      Index       HEAD/Repo
  ───────────      ─────       ────────
       │              │             │
       │  git add     │             │
       ├─────────────►│             │
       │              │  git commit │
       │              ├────────────►│
       │              │             │
       │  git restore │             │
       │◄─────────────┤             │
       │              │             │
       │         git reset --mixed  │
       │              │◄────────────┤
       │              │             │
       │         git reset --hard   │
       │◄─────────────┤◄────────────┤
       │              │             │
       │    git checkout <file>     │
       │◄───────────────────────────┤
```

---

## Concetti Base

### Init, Clone e Configurazione Repo

```bash
# Creare nuovo repository
git init
git init --bare /path/to/repo.git    # Bare repo (per server, senza working directory)
git init --initial-branch=main       # Specificare nome del branch iniziale

# Cosa succede con git init:
# 1. Crea la directory .git/ con tutta la struttura interna
# 2. Crea il file HEAD con "ref: refs/heads/main"
# 3. Crea le directory objects/ e refs/
# 4. Il repository è vuoto — nessun commit ancora

# Clonare
git clone git@github.com:user/repo.git
git clone git@github.com:user/repo.git mia-cartella    # Nome custom
git clone --depth 1 URL                                  # Shallow clone (solo ultimo commit)
git clone --branch develop URL                           # Clone specifico branch
git clone --filter=blob:none URL                         # Blobless clone (scarica blob on-demand)
git clone --mirror URL                                   # Mirror clone (tutto, inclusi ref interni)

# Differenze tra tipi di clone:
# --depth 1    → solo l'ultimo commit, utile per CI
# --filter=blob:none → scarica tree e commit, blob solo quando servono
# --mirror     → copia esatta per backup, include refs/notes, hooks ecc.

# Remote
git remote -v                          # Elencare remote
git remote add origin URL              # Aggiungere remote
git remote set-url origin NEW_URL      # Cambiare URL
git remote add upstream URL            # Aggiungere upstream (per fork)
git remote rename origin old-origin    # Rinominare remote
git remote remove upstream             # Rimuovere remote
git remote show origin                 # Dettagli remote (branch tracked, stale)

# Verificare la connessione:
git ls-remote origin                   # Lista ref del remote
git remote update                      # Aggiorna tutti i remote
```

### Staging, Commit e Cronologia — Deep Dive

```bash
# ═══════════════════════════════════════════
# STATUS — cosa è cambiato?
# ═══════════════════════════════════════════
git status
git status -s                          # Short format
# Output -s:
# M  file.txt    → Modificato e staged (M nella colonna sinistra)
#  M file.txt    → Modificato ma non staged (M nella colonna destra)
# MM file.txt    → Staged E poi modificato ancora
# A  file.txt    → Nuovo file staged
# ?? file.txt    → Untracked
# D  file.txt    → Cancellato
# R  file.txt    → Rinominato
git status --porcelain                 # Output machine-readable
git status -b                          # Mostra branch e tracking info

# ═══════════════════════════════════════════
# DIFF — cosa è cambiato esattamente?
# ═══════════════════════════════════════════

# Diff tra i tre alberi:
git diff                               # Working dir vs Index (staging)
git diff --staged                      # Index vs HEAD (ultimo commit)
git diff HEAD                          # Working dir vs HEAD (tutto ciò che è cambiato)

# Diff tra branch/commit:
git diff main..feature                 # Differenze tra tip di main e tip di feature
git diff main...feature                # Differenze dalla base comune di main e feature
# NOTA: due punti (..) = diff tra i due endpoint
#        tre punti (...) = diff dalla merge base

# Opzioni di formattazione:
git diff --stat                        # Sommario (file e righe cambiate)
git diff --shortstat                   # Solo totali (+/- righe)
git diff --name-only                   # Solo nomi file
git diff --name-status                 # Nomi file con stato (M/A/D/R)
git diff --word-diff                   # Diff a livello di parola (non di riga)
git diff --color-words                 # Parole cambiate colorate inline
git diff --diff-filter=M               # Solo file modificati (M=modified, A=added, D=deleted)

# Diff per file specifici:
git diff -- path/to/file.txt           # Un file specifico
git diff HEAD~3..HEAD -- src/          # Una directory negli ultimi 3 commit
git diff --no-index file1 file2        # Diff tra due file qualsiasi (anche fuori dal repo)

# Diff con contesto personalizzato:
git diff -U5                           # 5 righe di contesto (default 3)
git diff --ignore-space-change         # Ignora modifiche di whitespace
git diff --ignore-all-space            # Ignora completamente gli spazi
git diff --ignore-blank-lines          # Ignora righe vuote

# ═══════════════════════════════════════════
# ADD — preparare per il commit
# ═══════════════════════════════════════════
git add file.txt                       # File specifico
git add src/                           # Directory (ricorsivo)
git add -A                             # Tutto (nuovo, modificato, cancellato)
git add -p                             # Interattivo: scegliere hunk per hunk
git add -u                             # Solo modificati e cancellati (no nuovi)
git add '*.js'                         # Pattern glob (tutti i .js ricorsivamente)
git add -N file.txt                    # Intent to add: segna come tracked senza staging

# git add -p (patch mode) — comandi nell'editor:
# y = stage this hunk
# n = skip this hunk
# s = split into smaller hunks
# e = edit manually
# q = quit (non staging remaining hunks)

# ═══════════════════════════════════════════
# COMMIT — creare uno snapshot
# ═══════════════════════════════════════════
git commit -m "Messaggio conciso"
git commit                             # Apre editor per messaggio lungo
git commit -am "Messaggio"             # Add + commit (solo file tracked)
git commit --amend                     # Modificare ultimo commit (message o contenuto)
git commit --amend --no-edit           # Aggiungere file all'ultimo commit senza cambiare messaggio
git commit --allow-empty -m "trigger"  # Commit vuoto (utile per trigger CI)
git commit -v                          # Mostra diff nell'editor del commit
git commit --date="2026-01-15T10:00:00" -m "msg"  # Data custom

# Anatomia di un buon messaggio di commit:
#
# <tipo>(scope): descrizione imperativa breve (max 72 char)
#
# Corpo opzionale che spiega il PERCHÉ della modifica,
# non il COSA (quello è visibile nel diff).
# Wrappato a 72 caratteri per riga.
#
# Refs: #123
# BREAKING CHANGE: descrivere se è un breaking change

# ═══════════════════════════════════════════
# LOG — esplorare la cronologia
# ═══════════════════════════════════════════
git log                                # Cronologia completa
git log --oneline                      # Una riga per commit
git log --oneline --graph --all        # Grafico con tutti i branch
git log -5                             # Ultimi 5 commit
git log --author="Nome"                # Per autore
git log --since="2024-01-01"           # Da una data
git log --until="2024-12-31"           # Fino a una data
git log --since="2 weeks ago"          # Formato relativo
git log --grep="fix"                   # Cerca nel messaggio
git log -p                             # Con diff
git log -- path/to/file                # Cronologia di un file
git log --stat                         # Con sommario modifiche
git log --follow -- old-name.txt       # Segui rename del file
git shortlog -sn                       # Commit count per autore
git log --format="%h %an %s"           # Formato custom

# Formati custom utili:
git log --format="%h %ad %an: %s" --date=short    # Hash data autore: messaggio
git log --format="%C(yellow)%h%C(reset) %C(blue)%ad%C(reset) %s" --date=relative

# Filtri avanzati:
git log --all --oneline --graph --decorate    # Vista completa del DAG
git log --diff-filter=D -- .                  # Commit che hanno cancellato file
git log --merges                              # Solo merge commit
git log --no-merges                           # Escludi merge commit
git log --first-parent                        # Solo la linea principale (ignora merge)
git log -S "functionName"                     # Commit che hanno aggiunto/rimosso "functionName" (pickaxe)
git log -G "regex_pattern"                    # Come -S ma con regex
git log main..feature                         # Commit in feature non in main
git log feature..main                         # Commit in main non in feature

# ═══════════════════════════════════════════
# SHOW — dettaglio di un commit
# ═══════════════════════════════════════════
git show abc1234                       # Commit specifico
git show HEAD~3                        # 3 commit fa
git show main:src/file.txt             # File in un altro branch
git show HEAD~2:path/to/file           # File com'era 2 commit fa
git show :0:file.txt                   # File nella staging area (index)
```

### Riferimenti in Git (Refs)

```bash
# HEAD: puntatore al branch corrente (o a un commit in detached HEAD state)
# HEAD~N: N commit prima di HEAD seguendo il primo parent
# HEAD^N: l'N-esimo parent di HEAD (utile per merge commit)

# Notazione:
# HEAD~1 = HEAD^  = parent di HEAD
# HEAD~2         = "nonno" di HEAD (genitore del genitore)
# HEAD^2         = secondo parent di HEAD (se è un merge commit)
# HEAD~2^2       = secondo parent del nonno

# Esempi con merge commit (M ha parent A e B):
#   A ← M (merge)
#        ↑
#        B
# M^1 = A (primo parent)
# M^2 = B (secondo parent)
# M~1 = A (equivale a M^1)
# M~2 = parent di A

# Ref speciali:
# @{upstream} o @{u}  = branch remoto tracked
# @{push}             = branch remoto di push
# HEAD@{1}            = stato precedente di HEAD (reflog)
# main@{yesterday}    = dove era main ieri (reflog)
# main@{2024-01-15}   = dove era main in quella data

# Intervalli:
# A..B     = commit raggiungibili da B ma non da A
# A...B    = commit raggiungibili da A o B, ma non entrambi (symmetric diff)
# ^A B     = equivale a A..B
```

### Push, Pull e Sync

```bash
# ═══════════════════════════════════════════
# PUSH — inviare commit al remote
# ═══════════════════════════════════════════
git push                               # Push branch corrente
git push origin main                   # Push specifico
git push -u origin feature-x           # Push e set upstream tracking
git push --tags                        # Push tutti i tag
git push origin --delete old-branch    # Eliminare branch remoto
git push --force-with-lease            # Force push sicuro (fallisce se altri hanno pushato)
git push --force-with-lease --force-if-includes  # Ancora più sicuro (verifica fetch recente)

# ATTENZIONE: git push --force riscrive la storia remota!
# Usare SOLO su branch personali. Mai su main/develop condivisi.
# --force-with-lease è SEMPRE preferibile a --force.

# Push di un tag specifico:
git push origin v1.0.0                 # Singolo tag
git push origin --tags                 # Tutti i tag

# ═══════════════════════════════════════════
# PULL = fetch + merge (o fetch + rebase)
# ═══════════════════════════════════════════
git pull                               # Pull branch corrente
git pull --rebase                      # Pull con rebase anziché merge
git pull --rebase=merges               # Rebase preservando merge commit locali
git pull origin main                   # Pull specifico
git pull --autostash                   # Stash automatico prima del pull

# Configurare pull --rebase come default:
# git config --global pull.rebase true

# ═══════════════════════════════════════════
# FETCH — scarica senza merge
# ═══════════════════════════════════════════
git fetch                              # Scarica tutto dal remote
git fetch --prune                      # Rimuove riferimenti a branch remoti cancellati
git fetch --prune --prune-tags         # Rimuove anche tag remoti cancellati
git fetch origin feature-x             # Fetch specifico branch
git fetch --all                        # Fetch da tutti i remote
git fetch --dry-run                    # Mostra cosa scaricherebbe senza farlo

# ═══════════════════════════════════════════
# TAG — marker permanenti nella storia
# ═══════════════════════════════════════════
git tag v1.0.0                         # Lightweight tag
git tag -a v1.0.0 -m "Release 1.0.0"  # Annotated tag (consigliato)
git tag -l "v1.*"                      # Elencare tag con pattern
git tag -l --sort=-version:refname     # Ordinare per versione (desc)
git push origin v1.0.0                 # Push singolo tag
git push origin --tags                 # Push tutti i tag
git tag -d v1.0.0                      # Eliminare tag locale
git push origin :refs/tags/v1.0.0      # Eliminare tag remoto
git tag -a v1.0.0 abc1234 -m "Tag retroattivo"  # Tag su commit passato
```

---

## Branching e Merge

### Gestione Branch

```bash
# ═══════════════════════════════════════════
# BRANCH — operazioni sui branch
# ═══════════════════════════════════════════
git branch                             # Elencare branch locali
git branch -a                          # Tutti (locali + remoti)
git branch -v                          # Con ultimo commit
git branch -vv                         # Con upstream tracking info
git branch feature-x                   # Creare branch (senza switchare)
git branch feature-x abc1234           # Creare da commit specifico
git branch -d feature-x               # Eliminare (se merged)
git branch -D feature-x               # Eliminare (forzato, anche se non merged)
git branch -m old-name new-name        # Rinominare
git branch --merged                    # Branch già merged in HEAD
git branch --no-merged                 # Branch non ancora merged
git branch --contains abc1234          # Branch che contengono un commit
git branch --set-upstream-to=origin/main main  # Set tracking

# ═══════════════════════════════════════════
# SWITCH / CHECKOUT — cambiare branch
# ═══════════════════════════════════════════
git switch feature-x                   # Cambiare branch (moderno, Git 2.23+)
git switch -c feature-x               # Creare e cambiare
git switch -c feature-x origin/feature-x  # Creare da branch remoto
git switch --detach abc1234            # Detached HEAD su commit
git switch -                           # Tornare al branch precedente

git checkout feature-x                 # Cambiare branch (classico)
git checkout -b feature-x             # Creare e cambiare (classico)
git checkout -- file.txt               # Scartare modifiche a un file
# NOTA: git checkout è sovraccarico (branch + file).
# Preferire git switch per branch e git restore per file.

# ═══════════════════════════════════════════
# Detached HEAD
# ═══════════════════════════════════════════
# Succede quando HEAD punta a un commit anziché a un branch.
# È utile per ispezionare commit passati, ma i commit fatti
# in detached HEAD non sono su nessun branch!

git checkout abc1234                   # Detached HEAD
# "Sei in detached HEAD state..."
# Per salvare il lavoro:
git switch -c new-branch               # Crea branch dal punto corrente
```

### Merge — Tipi e Comportamento

```bash
# ═══════════════════════════════════════════
# MERGE — integrare branch
# ═══════════════════════════════════════════
git merge feature-x                    # Merge feature-x nel branch corrente
git merge --no-ff feature-x            # Forza merge commit (anche se fast-forward possibile)
git merge --squash feature-x           # Squash tutti i commit in uno + staging (senza commit)
git merge --abort                      # Annullare merge in corso (durante conflitto)
git merge --no-commit feature-x        # Merge senza committare (per revisione)
git merge -m "Messaggio custom" feature-x  # Merge con messaggio personalizzato
```

### Risoluzione Conflitti

```bash
# Quando Git non può fare merge automatico:
# 1. git status → mostra file in conflitto (both modified)
# 2. Aprire i file → cercare marcatori:

# <<<<<<< HEAD
# contenuto del branch corrente (ours)
# =======
# contenuto del branch in merge (theirs)
# >>>>>>> feature-x

# 3. Risolvere manualmente:
#    - Rimuovere i marcatori <<<<<<<, =======, >>>>>>>
#    - Tenere il codice corretto (può essere un mix di entrambi)
# 4. git add file_risolto.txt
# 5. git commit (o git merge --continue)

# Tool per merge visuale
git mergetool                          # Apre tool configurato
# Configurare:
# git config --global merge.tool vscode
# git config --global mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'

# Risolvere automaticamente preferendo una versione:
git checkout --ours file.txt           # Mantieni la versione corrente
git checkout --theirs file.txt         # Mantieni la versione dell'altro branch
git add file.txt

# Verificare che i conflitti siano tutti risolti:
git diff --check                       # Controlla marcatori residui
```

---

## Strategie di Merge

Git supporta diverse strategie di merge, ognuna adatta a situazioni specifiche.

### Fast-Forward Merge

```
Situazione: main non ha commit nuovi dopo il punto di branch.

PRIMA:
  A ← B ← C           ← main
            ↑
            └─ D ← E   ← feature

DOPO (git merge feature):
  A ← B ← C ← D ← E   ← main, feature

Nessun merge commit viene creato!
main viene semplicemente spostato avanti (fast-forward).

Questo succede quando la storia è lineare.
```

```bash
# Fast-forward merge (default quando possibile):
git switch main
git merge feature-x
# "Fast-forward" nel messaggio

# Per IMPEDIRE fast-forward (creare sempre merge commit):
git merge --no-ff feature-x
# Utile quando vuoi preservare la storia del branch

# Per RICHIEDERE fast-forward (fallire se non possibile):
git merge --ff-only feature-x
# Utile in script che non vogliono gestire conflitti
```

### Recursive Merge (ora ort)

```
Situazione: entrambi i branch hanno commit nuovi.

PRIMA:
  A ← B ← C ← F       ← main
            ↑
            └─ D ← E   ← feature

DOPO (git merge feature):
  A ← B ← C ← F ← G   ← main
            ↑       ↑
            └─ D ← E    ← feature

G è un merge commit con due parent: F e E.
La strategia "recursive" (o "ort" in Git 2.33+) è il default.
```

```bash
# Recursive merge (default per merge a 2 vie):
git merge feature-x
# Git trova il merge base (B), fa three-way merge:
# base (B) vs ours (F) vs theirs (E)

# ort (Ostensibly Recursive's Twin) — sostituto moderno di recursive:
# Stesso risultato, ma più veloce e gestisce meglio casi edge.
# Default da Git 2.33+. Selezionare esplicitamente:
git merge -s ort feature-x

# Opzioni per la strategia recursive/ort:
git merge -X patience feature-x       # Algoritmo diff "patience" (migliore per refactoring)
git merge -X diff-algorithm=histogram feature-x  # Alternativa a patience
git merge -X ignore-space-change feature-x       # Ignora modifiche di whitespace
```

### Octopus Merge

```
Merge di 3+ branch in un singolo merge commit.
Usato raramente manualmente — Git lo usa internamente
per merge di più branch contemporaneamente.

PRIMA:
  A ← B ← C           ← main
       ↑
       ├─ D ← E       ← feature-1
       ↑
       └─ F ← G       ← feature-2

DOPO (git merge feature-1 feature-2):
  A ← B ← C ← H       ← main
       ↑       ↑↑
       ├─ D ← E│       ← feature-1
       ↑        │
       └─ F ← G        ← feature-2

H ha TRE parent: C, E, G.
```

```bash
# Octopus merge (merge multipli in uno):
git switch main
git merge feature-1 feature-2 feature-3
# NOTA: octopus merge NON gestisce conflitti.
# Se c'è conflitto, fallisce. Usare solo per merge semplici.
```

### Ours Strategy

```bash
# Strategia "ours" — ignora completamente le modifiche dell'altro branch:
git merge -s ours feature-x
# Crea un merge commit, ma il tree è identico al branch corrente.
# I cambiamenti di feature-x sono SCARTATI.
# Utile quando vuoi "chiudere" un branch senza le sue modifiche.

# NON confondere con l'opzione -X ours:
git merge -X ours feature-x
# Usa la strategia recursive/ort ma in caso di CONFLITTO
# preferisce la versione "nostra" (branch corrente).
# I cambiamenti non conflittuali vengono comunque merged!
```

### Theirs Option

```bash
# Non esiste una strategia "theirs" (git merge -s theirs non esiste).
# Ma esiste l'opzione -X theirs:
git merge -X theirs feature-x
# In caso di conflitto, preferisce la versione dell'altro branch.
# I cambiamenti non conflittuali vengono merged normalmente.
```

### Confronto strategie di merge

```
| Strategia      | Quando                        | Conflitti          |
|----------------|-------------------------------|--------------------|
| fast-forward   | Storia lineare                | Impossibili        |
| recursive/ort  | Due branch divergenti         | Risolti manualmente|
| octopus        | 3+ branch semplici            | Non gestiti        |
| ours           | Scartare un branch            | Ignorati           |
| -X ours/theirs | Auto-risolvere conflitti      | Risolti automatico |
```

---

## Rebase — Fondamenti e Interactive Rebase

### Concetto di Rebase

```
Il rebase "riapplica" i commit di un branch sopra un altro base point.
Il risultato è una storia lineare, senza merge commit.

PRIMA del rebase:
  A ← B ← C ← F       ← main
            ↑
            └─ D ← E   ← feature

DOPO git rebase main (eseguito da feature):
  A ← B ← C ← F       ← main
                  ↑
                  └─ D' ← E'   ← feature

D' e E' sono NUOVI commit (hash diversi) con lo stesso contenuto di D e E
ma con un parent diverso (F anziché C).

I commit originali D e E diventano unreachable (garbage collected).
```

### Quando usare rebase vs merge

```
REBASE:
✅ Branch locale non pushato — riscrivere la storia è sicuro
✅ Aggiornare feature branch con le ultime modifiche di main
✅ Pulire la storia prima di aprire PR
✅ Mantenere cronologia lineare e leggibile

MERGE:
✅ Branch condiviso con altri — mai riscrivere storia pubblica
✅ Preservare il contesto di quando e come le modifiche sono state integrate
✅ Quando la storia non lineare è informativa
✅ Merge di branch di release/hotfix in main

REGOLA D'ORO:
Non fare mai rebase di commit che sono stati pushati e condivisi.
Se altri hanno basato il loro lavoro sui tuoi commit,
il rebase crea duplicati e confusione.
```

### Comandi Rebase

```bash
# Rebase semplice:
git switch feature
git rebase main                        # Riapplica commit di feature sopra main

# Rebase con gestione conflitti:
# 1. Git si ferma al primo conflitto
# 2. Risolvere il conflitto nel file
# 3. git add file_risolto.txt
# 4. git rebase --continue
# 5. Ripetere per ogni conflitto

git rebase --abort                     # Annullare rebase (tornare allo stato pre-rebase)
git rebase --skip                      # Saltare il commit corrente (scarta le sue modifiche)

# Rebase su commit specifico:
git rebase --onto new-base old-base feature
# Prende i commit tra old-base e feature, li riapplica su new-base

# Esempio --onto:
# Spostare feature da develop a main:
git rebase --onto main develop feature
```

### Interactive Rebase

```bash
# Interactive rebase — riscrivere, riordinare, unire, eliminare commit:
git rebase -i HEAD~5                   # Ultimi 5 commit
git rebase -i main                     # Tutti i commit dopo main

# L'editor mostra:
# pick a1b2c3d feat: add user model
# pick d4e5f6a fix: typo in user model
# pick 7890abc feat: add user controller
# pick bcd1234 wip: debug logging
# pick ef56789 feat: add user routes

# Comandi disponibili:
# pick (p)   → mantieni commit così com'è
# reword (r) → mantieni commit, cambia messaggio
# edit (e)   → fermati a questo commit per modificarlo
# squash (s) → unisci al commit precedente, mantieni entrambi i messaggi
# fixup (f)  → unisci al commit precedente, scarta questo messaggio
# drop (d)   → elimina il commit completamente
# exec (x)   → esegui un comando shell
# break (b)  → fermati qui (continua con --continue)

# Esempio: pulire la storia prima di PR
# Risultato desiderato nell'editor:
# pick a1b2c3d feat: add user model
# fixup d4e5f6a fix: typo in user model          ← unisci a precedente
# pick 7890abc feat: add user controller
# drop bcd1234 wip: debug logging                 ← elimina
# pick ef56789 feat: add user routes

# Puoi anche RIORDINARE le righe per cambiare l'ordine dei commit!
```

### Autosquash

```bash
# Workflow per fix rapidi da squashare automaticamente:

# 1. Fare il commit di fix con --fixup:
git commit --fixup=a1b2c3d -m "fix: correct field name"
# Crea un commit con messaggio "fixup! feat: add user model"

# 2. Fare rebase con --autosquash:
git rebase -i --autosquash main
# Git automaticamente mette il fixup sotto il commit corretto
# e lo segna come "fixup" anziché "pick"

# Rendere autosquash il default:
# git config --global rebase.autosquash true
```

---

## Cherry-Pick

### Concetto e Uso

```
Cherry-pick copia un singolo commit (o più commit) da un branch a un altro.
Il commit risultante ha lo stesso diff ma un hash diverso.

PRIMA:
  A ← B ← C           ← main
       ↑
       └─ D ← E ← F   ← feature

DOPO git cherry-pick E (eseguito da main):
  A ← B ← C ← E'      ← main
       ↑
       └─ D ← E ← F   ← feature

E' ha lo stesso contenuto (diff) di E ma hash diverso
perché il parent è C anziché D.
```

```bash
# Cherry-pick singolo commit:
git cherry-pick abc1234

# Cherry-pick multipli (in ordine):
git cherry-pick abc1234 def5678

# Cherry-pick un range:
git cherry-pick A..B                   # Dalla commit dopo A fino a B (incluso)
git cherry-pick A^..B                  # Da A (incluso) fino a B (incluso)

# Cherry-pick senza committare (solo staging):
git cherry-pick abc1234 --no-commit
# Utile per combinare più cherry-pick in un unico commit

# Cherry-pick preservando info sull'origine:
git cherry-pick -x abc1234
# Aggiunge "(cherry picked from commit abc1234)" al messaggio

# Gestire conflitti durante cherry-pick:
git cherry-pick --abort                # Annullare
git cherry-pick --continue             # Dopo aver risolto conflitti
git cherry-pick --skip                 # Saltare questo commit
```

### Quando usare cherry-pick

```
BUONI USI:
✅ Portare un hotfix da main a release branch
✅ Recuperare un singolo commit utile da un branch abbandonato
✅ Backport di bugfix a versioni precedenti

CATTIVI USI (preferire merge o rebase):
❌ Portare molti commit tra branch — crea duplicati nel DAG
❌ Come sostituto sistematico del merge — la storia diventa confusa
❌ Feature intere — i commit perdono il contesto originale
```

---

## Operazioni Avanzate

### Stash

```bash
# STASH — salvare temporaneamente le modifiche non committate
git stash                              # Salva modifiche tracked e pulisce working dir
git stash push -m "descrizione"        # Con messaggio descrittivo
git stash -u                           # Include untracked files
git stash -a                           # Include anche file ignorati (.gitignore)
git stash --keep-index                 # Stash solo modifiche non staged (mantieni staged)

# Gestire stash multipli:
git stash list                         # Elencare stash (stack LIFO)
# stash@{0}: On main: descrizione
# stash@{1}: On feature: altro lavoro
# stash@{2}: WIP on main: abc1234

git stash pop                          # Applicare e rimuovere ultimo stash
git stash pop stash@{2}                # Applicare e rimuovere stash specifico
git stash apply stash@{2}              # Applicare senza rimuovere
git stash drop stash@{0}              # Eliminare uno stash
git stash clear                        # Eliminare tutti gli stash

# Ispezionare uno stash:
git stash show                         # Sommario (file modificati)
git stash show -p stash@{0}           # Diff completo
git stash show --name-only stash@{0}  # Solo nomi file

# Creare branch da stash:
git stash branch new-branch stash@{0}  # Crea branch, applica stash, lo rimuove

# Stash parziale (solo alcuni file):
git stash push -m "partial" -- file1.txt file2.txt
```

### Reset, Revert e Restore

```bash
# ═══════════════════════════════════════════
# RESET — spostare HEAD e modificare staging/working dir
# ═══════════════════════════════════════════

# I tre livelli di reset:
git reset --soft HEAD~1
# Sposta HEAD indietro di 1 commit
# Index (staging): INVARIATO — i cambiamenti restano staged
# Working Dir: INVARIATO
# Uso: "uncommit" per modificare il commit

git reset --mixed HEAD~1               # (default, equivale a git reset HEAD~1)
# Sposta HEAD indietro di 1 commit
# Index: RESETTATO — i cambiamenti diventano unstaged
# Working Dir: INVARIATO
# Uso: "uncommit + unstage" ma mantieni le modifiche

git reset --hard HEAD~1
# Sposta HEAD indietro di 1 commit
# Index: RESETTATO
# Working Dir: RESETTATO — modifiche PERSE!
# Uso: scartare completamente un commit
# PERICOLOSO: le modifiche non committate sono irrecuperabili!

# Reset di singoli file:
git reset HEAD file.txt                # Unstage un file (equivale a git restore --staged)
git reset abc1234 -- file.txt          # Unstage e ripristina a versione di quel commit

# ═══════════════════════════════════════════
# REVERT — creare un commit che annulla un precedente
# ═══════════════════════════════════════════
git revert abc1234                     # Annulla un commit (crea nuovo commit)
git revert abc1234 --no-commit         # Annulla senza committare subito
git revert HEAD~3..HEAD                # Annulla gli ultimi 3 commit (uno per uno)
git revert -m 1 <merge-commit>        # Revert di un merge commit
# -m 1 = tieni il primo parent (main), annulla il merge

# DIFFERENZA FONDAMENTALE:
# reset riscrive la storia (pericoloso su branch condivisi)
# revert aggiunge alla storia (sicuro su branch condivisi)

# ═══════════════════════════════════════════
# RESTORE (Git 2.23+) — ripristinare file
# ═══════════════════════════════════════════
git restore file.txt                   # Scarta modifiche nel working dir
git restore --staged file.txt          # Unstage file (come git reset HEAD file.txt)
git restore --source HEAD~2 file.txt   # Ripristina file da 2 commit fa
git restore --source main file.txt     # Ripristina file dalla versione in main
git restore --staged --worktree file.txt  # Unstage E scarta modifiche

# Restore di directory:
git restore src/                       # Scarta tutte le modifiche in src/
git restore .                          # Scarta tutte le modifiche (PERICOLOSO!)
```

### Worktree

```bash
# WORKTREE — multiple working directory per lo stesso repo
# Utile per lavorare su più branch contemporaneamente senza stash

git worktree add ../hotfix-branch hotfix/critical  # Creare worktree da branch
git worktree add ../new-feature -b feature-x       # Creare worktree con nuovo branch
git worktree add ../review abc1234                 # Creare worktree da commit

git worktree list                                    # Elencare worktree
git worktree remove ../hotfix-branch                # Rimuovere worktree
git worktree prune                                   # Pulire riferimenti a worktree orfani

# Ogni worktree ha il suo working dir e index, ma condivide
# lo stesso .git (oggetti, ref, hooks). È più efficiente di
# clonare il repo una seconda volta.
```

### Clean

```bash
# CLEAN — rimuovere file non tracciati dal working directory
git clean -n                           # Dry run (mostra cosa rimuoverebbe)
git clean -f                           # Rimuovi file non tracciati
git clean -fd                          # Rimuovi file e directory non tracciati
git clean -fx                          # Rimuovi tutto, inclusi file ignorati da .gitignore
git clean -fX                          # Rimuovi SOLO file ignorati

# ATTENZIONE: git clean è irreversibile!
# Fare SEMPRE git clean -n prima per verificare.
```

---

## Reflog — La Rete di Sicurezza

### Cos'è il reflog

```
Il reflog (reference log) registra OGNI movimento di HEAD e dei branch tip.
Anche dopo reset --hard, rebase, o branch cancellati, i commit
restano nel reflog per almeno 90 giorni (default).

Il reflog è LOCALE — non viene mai pushato o clonato.
Esiste solo nel tuo repository.
```

### Comandi Reflog

```bash
# Visualizzare il reflog:
git reflog                             # Reflog di HEAD
git reflog show main                   # Reflog di un branch specifico
git reflog show --date=iso             # Con timestamp ISO

# Output tipico:
# a1b2c3d HEAD@{0}: commit: feat: add user routes
# d4e5f6a HEAD@{1}: rebase (finish): returning to refs/heads/feature
# 7890abc HEAD@{2}: rebase (pick): feat: add controller
# bcd1234 HEAD@{3}: rebase (start): checkout main
# ef56789 HEAD@{4}: commit: wip: debug
# 1234567 HEAD@{5}: checkout: moving from main to feature

# Ogni entry mostra:
# SHA → il commit a cui HEAD puntava
# HEAD@{N} → posizione nel reflog (0 = attuale)
# Operazione → cosa ha causato il movimento
```

### Scenari di Recovery con Reflog

```bash
# ═══════════════════════════════════════════
# Scenario 1: Recupero dopo reset --hard
# ═══════════════════════════════════════════
# Hai fatto git reset --hard e perso commit
git reflog
# Trova il commit prima del reset, es. HEAD@{3}
git reset --hard HEAD@{3}              # Ripristina allo stato precedente
# Oppure crea un branch di recovery:
git branch recovered HEAD@{3}

# ═══════════════════════════════════════════
# Scenario 2: Recupero dopo rebase andato male
# ═══════════════════════════════════════════
# Il rebase ha distrutto la storia
git reflog
# Trova lo stato prima del rebase (rebase (start))
git reset --hard HEAD@{N}             # Dove N è la posizione pre-rebase

# ═══════════════════════════════════════════
# Scenario 3: Branch cancellato per errore
# ═══════════════════════════════════════════
git branch -D feature-important       # Ops!
git reflog
# Trova l'ultimo commit del branch cancellato
git branch feature-important HEAD@{N}  # Ricrea il branch

# ═══════════════════════════════════════════
# Scenario 4: Commit perso dopo amend
# ═══════════════════════════════════════════
# git commit --amend ha sostituito il commit precedente
git reflog
# Il commit originale (pre-amend) è ancora lì
git show HEAD@{1}                      # Vedere il commit originale
git diff HEAD HEAD@{1}                 # Confrontare amend vs originale

# ═══════════════════════════════════════════
# Scenario 5: Trovare quando un branch puntava a un commit
# ═══════════════════════════════════════════
git reflog show main --date=relative
# Mostra tutta la storia di dove main ha puntato nel tempo
```

### Configurazione scadenza reflog

```bash
# Il reflog ha una scadenza (default: 90 giorni per commit raggiungibili,
# 30 giorni per commit non raggiungibili)

# Verificare configurazione:
git config gc.reflogExpire              # Default: 90 giorni
git config gc.reflogExpireUnreachable   # Default: 30 giorni

# Cambiare scadenza:
git config --global gc.reflogExpire "180 days"
git config --global gc.reflogExpireUnreachable "90 days"

# Pulire reflog manualmente (quasi mai necessario):
git reflog expire --expire=90.days.ago --all
```

---

## Git Bisect — Trovare Bug con Ricerca Binaria

### Concetto

```
git bisect usa la ricerca binaria sulla cronologia dei commit
per trovare il PRIMO commit che ha introdotto un bug.

Se hai 1024 commit tra "funzionava" e "non funziona",
bisect lo trova in ~10 passi (log2(1024) = 10).
```

### Bisect Manuale

```bash
# 1. Iniziare bisect:
git bisect start

# 2. Marcare il commit corrente come "bad" (ha il bug):
git bisect bad
# Oppure specificare un commit: git bisect bad abc1234

# 3. Marcare un commit dove il bug NON c'era:
git bisect good v1.0.0
# Oppure: git bisect good abc1234

# 4. Git fa checkout di un commit a metà strada:
# "Bisecting: 127 revisions left to test after this (roughly 7 steps)"

# 5. Testare se il bug è presente:
#    Se il bug c'è: git bisect bad
#    Se il bug NON c'è: git bisect good

# 6. Ripetere step 4-5 finché Git trova il colpevole:
# "abc1234 is the first bad commit"
# "commit abc1234
# Author: ...
# Date: ...
# 
#     refactor: change validation logic"

# 7. Terminare bisect e tornare al branch originale:
git bisect reset

# Se un commit non è testabile (es. non compila):
git bisect skip                        # Salta il commit corrente
```

### Bisect Automatizzato

```bash
# Automatizzare bisect con uno script di test:
git bisect start HEAD v1.0.0           # bad = HEAD, good = v1.0.0

git bisect run ./test_script.sh
# Lo script deve uscire con:
# Exit 0 → good (il bug NON c'è)
# Exit 1-124,126-127 → bad (il bug C'È)
# Exit 125 → skip (commit non testabile)

# Esempio con test unitario:
git bisect run npm test -- --grep="login validation"

# Esempio con script custom:
git bisect run bash -c 'make && ./run_test && echo PASS || exit 1'

# Esempio con verifica compilazione:
git bisect run make

# Al termine, Git mostra il primo commit bad e fa reset automaticamente.
```

### Bisect con nuovi termini (Git 2.36+)

```bash
# Invece di good/bad, puoi usare termini custom:
git bisect start --term-old=slow --term-new=fast

# Utile per trovare commit di MIGLIORAMENTO (non bug):
git bisect slow HEAD~50    # Era lento
git bisect fast HEAD       # Ora è veloce
# Git trova il commit che ha migliorato la performance
```

### Esempio pratico completo

```bash
# Scenario: il login non funziona. Funzionava alla versione v2.0.0.

git bisect start
git bisect bad HEAD                    # La versione corrente è rotta
git bisect good v2.0.0                 # v2.0.0 funzionava

# Git: "Bisecting: 47 revisions left (roughly 6 steps)"
# Git fa checkout del commit a metà

# Test: apri l'app, prova il login...
# Login funziona → git bisect good
# Git: "Bisecting: 23 revisions left (roughly 5 steps)"

# Test: login NON funziona → git bisect bad
# Git: "Bisecting: 11 revisions left (roughly 4 steps)"

# ... continua fino a ...
# Git: "abc1234 is the first bad commit"
# Commit message: "refactor: update session handling middleware"

git bisect log                         # Vedere il log della sessione bisect
git bisect reset                       # Tornare al branch originale

# Ora sai che il bug è stato introdotto nel commit abc1234.
# Puoi esaminare il diff: git show abc1234
```

---

## Interni Git — Struttura .git/

### Anatomia completa della directory .git/

```
.git/
├── HEAD                    → Ref al branch corrente: "ref: refs/heads/main"
│                             Oppure SHA diretto in detached HEAD state
│
├── config                  → Configurazione locale del repository
│                             [core], [remote "origin"], [branch "main"], ecc.
│
├── description             → Descrizione del repo (usato da Gitweb)
│
├── index                   → Staging area (file binario)
│                             Contiene: path, hash, stage number, permessi
│
├── packed-refs             → Ref compressi in un file (ottimizzazione)
│
├── FETCH_HEAD              → Ultimo fetch (branch/commit scaricati)
├── ORIG_HEAD               → HEAD prima di operazioni pericolose (merge, rebase)
├── MERGE_HEAD              → Commit in fase di merge (presente solo durante merge)
├── REBASE_HEAD             → Commit in fase di rebase
├── CHERRY_PICK_HEAD        → Commit in fase di cherry-pick
│
├── objects/                → Database oggetti (content-addressable store)
│   ├── pack/               → Packfile compressi (oggetti impacchettati)
│   │   ├── pack-<sha>.pack → File dati compresso
│   │   └── pack-<sha>.idx  → Indice del packfile
│   ├── info/               → Informazioni ausiliarie
│   │   └── packs           → Lista dei packfile
│   └── ab/                 → Oggetti loose (primi 2 char SHA = dir)
│       └── cdef1234...     → Contenuto dell'oggetto (compresso zlib)
│
├── refs/                   → Riferimenti (puntatori a commit)
│   ├── heads/              → Branch locali
│   │   ├── main            → SHA dell'ultimo commit di main
│   │   └── feature-x       → SHA dell'ultimo commit di feature-x
│   ├── remotes/            → Branch remoti (tracking)
│   │   └── origin/
│   │       ├── main
│   │       └── feature-x
│   ├── tags/               → Tag
│   │   ├── v1.0.0          → SHA (lightweight) o SHA dell'oggetto tag (annotated)
│   │   └── v2.0.0
│   └── stash               → Ultimo stash
│
├── logs/                   → Reflog (storia dei ref)
│   ├── HEAD                → Reflog di HEAD
│   └── refs/
│       └── heads/
│           ├── main         → Reflog di main
│           └── feature-x    → Reflog di feature-x
│
├── hooks/                  → Git hooks (script eseguiti su eventi)
│   ├── pre-commit.sample
│   ├── commit-msg.sample
│   ├── pre-push.sample
│   └── ...
│
├── info/
│   ├── exclude             → Pattern da ignorare (come .gitignore locale)
│   └── refs                → Informazioni ausiliarie
│
└── modules/                → Submodules (se presenti)
    └── vendor/lib/         → .git del submodule
```

### Oggetti loose vs packfile

```bash
# Oggetti LOOSE: singoli file in objects/ab/cdef1234...
# Formato: zlib(header + contenuto)
# Pro: accesso diretto per SHA
# Contro: molti file piccoli, inefficiente per repo grandi

# PACKFILE: oggetti compressi insieme in objects/pack/
# Git fa pack automaticamente durante push, gc, e quando
# ci sono troppi oggetti loose.
# Usa delta compression: memorizza solo le differenze tra
# oggetti simili.

# Forzare packing:
git gc                                 # Garbage collection + pack
git repack -ad                         # Repack aggressivo

# Statistiche oggetti:
git count-objects -vH
# count: 1234         → oggetti loose
# size: 5.60 MiB      → dimensione loose
# in-pack: 56789      → oggetti in packfile
# packs: 3            → numero packfile
# size-pack: 123 MiB  → dimensione packfile
# prune-packable: 0   → loose che possono essere packati
# garbage: 0
```

### Ispezionare oggetti a basso livello

```bash
# Tipo di un oggetto:
git cat-file -t abc1234
# blob, tree, commit, o tag

# Contenuto di un oggetto:
git cat-file -p abc1234

# Dimensione di un oggetto:
git cat-file -s abc1234

# Verificare se un oggetto esiste:
git cat-file -e abc1234 && echo "exists" || echo "not found"

# SHA completo da abbreviato:
git rev-parse abc1234
# Output: abc1234567890abcdef1234567890abcdef12345678

# SHA di HEAD:
git rev-parse HEAD

# SHA del tree di un commit:
git rev-parse HEAD^{tree}

# Tutti gli oggetti nel repo:
git rev-list --all --objects

# Verificare integrità:
git fsck                               # File system check
git fsck --unreachable                 # Mostra oggetti non raggiungibili
git fsck --dangling                    # Mostra oggetti dangling
```

### Garbage Collection e Manutenzione

```bash
# GC standard (eseguita automaticamente periodicamente):
git gc
# Comprime oggetti loose in packfile
# Rimuove oggetti unreachable scaduti
# Comprime reflog

# GC aggressiva (ricompatta tutto da zero):
git gc --aggressive
# Più lenta ma produce packfile più piccoli
# Utile dopo grandi rimozioni (git filter-branch, BFG)

# Pulizia oggetti unreachable:
git prune                              # Rimuovi oggetti unreachable
git prune --expire now                 # Rimuovi TUTTI quelli unreachable (pericoloso)

# Verificare integrità:
git fsck --full                        # Check completo
git fsck --no-reflogs                  # Ignora reflog (trova più unreachable)

# Manutenzione programmata (Git 2.30+):
git maintenance start                  # Avvia manutenzione in background
git maintenance stop                   # Ferma manutenzione in background
# Esegue automaticamente: gc, prefetch, commit-graph, loose-objects, pack-refs
```

---

## Configurazione — Livelli e Precedenza

### I tre livelli di configurazione

```
Git ha tre livelli di configurazione, con precedenza crescente:

1. SYSTEM  → /etc/gitconfig (o $(prefix)/etc/gitconfig)
             Applicato a TUTTI gli utenti del sistema.
             Raramente modificato manualmente.

2. GLOBAL  → ~/.gitconfig (o ~/.config/git/config)
             Applicato a TUTTI i repository dell'utente corrente.
             Identità, editor, alias, preferenze personali.

3. LOCAL   → .git/config (nella directory del repository)
             Applicato SOLO a questo repository.
             Override specifici per progetto.

4. WORKTREE → .git/config.worktree (Git 2.20+)
              Applicato solo a un worktree specifico.

Precedenza: worktree > local > global > system
(il più specifico vince)
```

```bash
# Leggere configurazione per livello:
git config --system --list             # Configurazione sistema
git config --global --list             # Configurazione utente
git config --local --list              # Configurazione repository
git config --list --show-origin        # Tutto con indicazione del file sorgente
git config --list --show-scope         # Tutto con indicazione del livello

# Impostare valori:
git config --global user.name "Renan Augusto Macena"
git config --global user.email "email@example.com"
git config --local core.autocrlf input

# Rimuovere un valore:
git config --global --unset alias.st

# Editare direttamente il file di config:
git config --global --edit             # Apre ~/.gitconfig nell'editor
git config --local --edit              # Apre .git/config nell'editor
```

### Configurazione essenziale

```bash
# ═══════════════════════════════════════════
# Identità (OBBLIGATORIA)
# ═══════════════════════════════════════════
git config --global user.name "Renan Augusto Macena"
git config --global user.email "email@example.com"

# ═══════════════════════════════════════════
# Editor
# ═══════════════════════════════════════════
git config --global core.editor "code --wait"    # VS Code
git config --global core.editor "vim"             # Vim
git config --global core.editor "nano"            # Nano
git config --global core.editor "nvim"            # Neovim

# ═══════════════════════════════════════════
# Line endings
# ═══════════════════════════════════════════
# Linux/macOS:
git config --global core.autocrlf input
# Windows:
git config --global core.autocrlf true
# Disabilitare (gestire manualmente con .gitattributes):
git config --global core.autocrlf false

# ═══════════════════════════════════════════
# Default branch name
# ═══════════════════════════════════════════
git config --global init.defaultBranch main

# ═══════════════════════════════════════════
# Pull strategy
# ═══════════════════════════════════════════
git config --global pull.rebase true          # Rebase di default
git config --global pull.ff only               # Solo fast-forward (fallisce se diverge)

# ═══════════════════════════════════════════
# Push behavior
# ═══════════════════════════════════════════
git config --global push.default current       # Push branch corrente a omonimo remoto
git config --global push.autoSetupRemote true  # Auto set upstream al primo push (Git 2.37+)

# ═══════════════════════════════════════════
# Merge e diff
# ═══════════════════════════════════════════
git config --global merge.conflictStyle zdiff3  # Mostra merge base nei conflitti (Git 2.35+)
git config --global diff.algorithm histogram    # Algoritmo diff migliore per refactoring
git config --global diff.colorMoved default     # Evidenzia righe spostate

# ═══════════════════════════════════════════
# Sicurezza e verifica
# ═══════════════════════════════════════════
git config --global transfer.fsckObjects true   # Verifica oggetti durante fetch/push
git config --global fetch.fsckObjects true
git config --global receive.fsckObjects true

# ═══════════════════════════════════════════
# Performance
# ═══════════════════════════════════════════
git config --global core.fsmonitor true         # File system monitor (Git 2.37+)
git config --global core.untrackedCache true    # Cache per untracked files
git config --global feature.manyFiles true      # Ottimizzazioni per repo grandi

# ═══════════════════════════════════════════
# Colori
# ═══════════════════════════════════════════
git config --global color.ui auto               # Colori automatici (default)
```

### .gitignore

```bash
# File .gitignore nella root del repository

# Pattern comuni:
*.log                    # Tutti i file .log
*.tmp
*.swp
.DS_Store               # macOS
Thumbs.db               # Windows
node_modules/           # Dipendenze Node.js
__pycache__/            # Python bytecode
*.pyc
.env                    # Variabili ambiente (SEGRETI!)
.env.local
.env.*.local
dist/                   # Build output
build/
out/
coverage/               # Test coverage
*.exe
*.dll
*.so
*.dylib

# IDE
.idea/                  # JetBrains
.vscode/                # VS Code (se non condiviso)
*.sublime-workspace

# Negazione (includere un file altrimenti ignorato)
!important.log

# Pattern avanzati:
**/logs                 # Directory "logs" a qualsiasi profondità
**/logs/*.log           # File .log in qualsiasi directory "logs"
foo/**/bar              # foo/bar, foo/a/bar, foo/a/b/bar

# .gitignore globale (per tutti i repo, pattern personali)
git config --global core.excludesFile ~/.gitignore_global

# .git/info/exclude — ignorare file SOLO in questo repo senza modificare .gitignore
# Utile per file personali (note, script locali) che non vuoi committare

# Ignorare file già tracciati:
git rm --cached file.txt               # Rimuovi dal tracking ma mantieni su disco
git rm -r --cached directory/          # Per directory
# Poi aggiungi a .gitignore

# Verificare se un file è ignorato:
git check-ignore -v file.txt           # Mostra la regola che lo ignora
git status --ignored                   # Mostra file ignorati
```

### .gitattributes

```bash
# Gestire come Git tratta i file specifici

# Line endings
* text=auto                          # Git sceglie automaticamente
*.sh text eol=lf                     # Sempre LF (Unix)
*.bat text eol=crlf                  # Sempre CRLF (Windows)
*.ps1 text eol=crlf                  # PowerShell su Windows

# Binary files (non fare diff/merge)
*.png binary
*.jpg binary
*.gif binary
*.ico binary
*.pdf binary
*.zip binary
*.gz binary
*.tar binary

# Git LFS
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text

# Diff driver custom (per file che hanno diff speciali)
*.md diff=markdown
*.css diff=css
*.html diff=html

# Merge strategy per file specifici (sempre prendere la nostra versione):
database.sqlite merge=ours
package-lock.json merge=ours

# Export ignore (non includere in git archive):
.gitattributes export-ignore
.gitignore export-ignore
.github/ export-ignore
tests/ export-ignore

# Linguist (per GitHub language stats)
docs/* linguist-documentation
vendor/* linguist-vendored
*.generated.ts linguist-generated
```

### Git Hooks

```bash
# Hooks: script eseguiti automaticamente in risposta a eventi Git
# Directory: .git/hooks/ (locale, non condivisi con il team)

# ═══════════════════════════════════════════
# Hook principali
# ═══════════════════════════════════════════

# pre-commit — Prima del commit
# Uso: linting, formatting, test rapidi, check segreti
# Exit 0 = procedi, Exit non-0 = annulla commit

# commit-msg — Dopo che l'utente scrive il messaggio
# Uso: validare formato messaggio (Conventional Commits)
# Riceve il file con il messaggio come argomento

# pre-push — Prima del push
# Uso: test completi, check di sicurezza
# Exit non-0 = annulla push

# post-merge — Dopo un merge
# Uso: npm install se package.json è cambiato, migrazioni DB

# post-checkout — Dopo checkout/switch
# Uso: ricostruire file generati, notifiche

# prepare-commit-msg — Prima di aprire l'editor per il commit
# Uso: pre-popolare il messaggio di commit (es. branch name)

# ═══════════════════════════════════════════
# Esempio: pre-commit hook
# ═══════════════════════════════════════════
# File: .git/hooks/pre-commit (deve essere eseguibile: chmod +x)

#!/bin/bash
# Verificare che non ci siano segreti committati
if git diff --staged --name-only | xargs grep -l 'API_KEY\|SECRET\|PASSWORD' 2>/dev/null; then
    echo "ERRORE: Possibili segreti nei file staged!"
    exit 1
fi

# Eseguire linter
npm run lint --quiet
if [ $? -ne 0 ]; then
    echo "Linting failed. Fix errors before committing."
    exit 1
fi

# ═══════════════════════════════════════════
# Esempio: commit-msg hook (validazione Conventional Commits)
# ═══════════════════════════════════════════
#!/bin/bash
MSG=$(cat "$1")
PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,72}"
if ! echo "$MSG" | grep -qE "$PATTERN"; then
    echo "ERRORE: Il messaggio non segue Conventional Commits"
    echo "Formato: <type>(scope): <description>"
    exit 1
fi

# ═══════════════════════════════════════════
# Tool per gestire hooks nel team
# ═══════════════════════════════════════════

# Husky (Node.js):
npx husky init
echo "npm test" > .husky/pre-commit

# Pre-commit (Python):
# pip install pre-commit
# .pre-commit-config.yaml nel repo
# pre-commit install

# Lefthook (Go, multi-linguaggio):
# Veloce, configurazione YAML semplice
# lefthook install
```

---

## Alias Git

### Cos'è un alias

```
Gli alias permettono di creare scorciatoie per comandi Git frequenti.
Sono salvati nella configurazione Git (global o local).
```

### Alias essenziali

```bash
# ═══════════════════════════════════════════
# Alias di base — scorciatoie
# ═══════════════════════════════════════════
git config --global alias.st "status"
git config --global alias.co "checkout"
git config --global alias.sw "switch"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.cp "cherry-pick"
git config --global alias.df "diff"
git config --global alias.ds "diff --staged"
git config --global alias.last "log -1 HEAD"
git config --global alias.unstage "restore --staged"

# ═══════════════════════════════════════════
# Alias per log — visualizzazione
# ═══════════════════════════════════════════
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.ll "log --pretty=format:'%C(yellow)%h%C(reset) %C(blue)%ad%C(reset) %C(green)%an%C(reset) %s' --date=short"
git config --global alias.who "shortlog -sn --no-merges"
git config --global alias.today "log --since='midnight' --oneline"

# ═══════════════════════════════════════════
# Alias per workflow
# ═══════════════════════════════════════════
git config --global alias.amend "commit --amend --no-edit"
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.wip "commit -am 'chore: WIP'"
git config --global alias.cleanup "branch --merged | grep -v '\\*\\|main\\|develop' | xargs git branch -d"

# ═══════════════════════════════════════════
# Alias con comandi shell (prefisso !)
# ═══════════════════════════════════════════
git config --global alias.root '!pwd'
git config --global alias.aliases '!git config --get-regexp alias | sort'
git config --global alias.ignore '!gi() { curl -sL https://www.toptal.com/developers/gitignore/api/$@ ;}; gi'

# Usare gli alias:
git st                                 # = git status
git lg                                 # = git log --oneline --graph --all --decorate
git amend                              # = git commit --amend --no-edit
git undo                               # = git reset --soft HEAD~1

# Elencare tutti gli alias configurati:
git config --get-regexp '^alias\.'
```

---

## Credential Helper

### Metodi di autenticazione

```bash
# ═══════════════════════════════════════════
# SSH (consigliato)
# ═══════════════════════════════════════════

# Generare chiave SSH:
ssh-keygen -t ed25519 -C "email@example.com"
# -t ed25519 = algoritmo moderno (preferito a RSA)
# La chiave privata va in ~/.ssh/id_ed25519
# La chiave pubblica va in ~/.ssh/id_ed25519.pub

# Aggiungere all'ssh-agent:
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Aggiungere la chiave pubblica a GitHub:
# Copiare il contenuto di ~/.ssh/id_ed25519.pub
# GitHub → Settings → SSH and GPG keys → New SSH key

# Testare la connessione:
ssh -T git@github.com
# "Hi username! You've been authenticated..."

# Usare URL SSH per clonare:
git clone git@github.com:user/repo.git
# Se il repo usa HTTPS, cambiare:
git remote set-url origin git@github.com:user/repo.git

# ═══════════════════════════════════════════
# HTTPS con credential helper
# ═══════════════════════════════════════════

# Memorizzare credenziali in memoria (timeout in secondi):
git config --global credential.helper 'cache --timeout=3600'
# Credenziali cached per 1 ora

# Memorizzare credenziali su disco (in chiaro — NON consigliato):
git config --global credential.helper store
# Salva in ~/.git-credentials in chiaro!

# macOS Keychain:
git config --global credential.helper osxkeychain

# Windows Credential Manager:
git config --global credential.helper manager

# Linux — libsecret (GNOME Keyring):
git config --global credential.helper /usr/lib/git-core/git-credential-libsecret

# ═══════════════════════════════════════════
# GitHub CLI (gh) — alternativa moderna
# ═══════════════════════════════════════════
gh auth login
# Configura automaticamente il credential helper
# Supporta HTTPS e SSH

# Verificare stato autenticazione:
gh auth status

# ═══════════════════════════════════════════
# Multiple identità (lavoro vs personale)
# ═══════════════════════════════════════════

# Configurazione condizionale in ~/.gitconfig:
# [includeIf "gitdir:~/work/"]
#     path = ~/.gitconfig-work
# [includeIf "gitdir:~/personal/"]
#     path = ~/.gitconfig-personal

# ~/.gitconfig-work:
# [user]
#     name = Renan (Work)
#     email = renan@company.com
# [core]
#     sshCommand = "ssh -i ~/.ssh/id_ed25519_work"

# ~/.gitconfig-personal:
# [user]
#     name = Renan Augusto Macena
#     email = personal@email.com
```

### GPG Signing

```bash
# Firmare commit e tag con GPG:

# Generare chiave GPG:
gpg --full-generate-key
# Scegliere: RSA e RSA, 4096 bit, no scadenza

# Elencare chiavi:
gpg --list-secret-keys --keyid-format=long
# sec   rsa4096/ABC1234DEF567890 2024-01-01

# Configurare Git per firmare:
git config --global user.signingkey ABC1234DEF567890
git config --global commit.gpgsign true    # Firma tutti i commit automaticamente
git config --global tag.gpgsign true       # Firma tutti i tag automaticamente

# Commit firmato:
git commit -S -m "feat: signed commit"
# Il flag -S è opzionale se gpgsign=true

# Verificare firma:
git log --show-signature
git verify-commit abc1234
git verify-tag v1.0.0
```

---

## Funzionalità Speciali

### Git LFS (Large File Storage)

```bash
# Per file grandi (> 50MB): immagini, video, dataset, binari

# Setup (una volta per utente):
git lfs install

# Tracciare tipi di file:
git lfs track "*.psd"                  # Photoshop
git lfs track "*.zip"                  # Archivi
git lfs track "data/*.csv"             # CSV nella directory data/
# Ogni git lfs track aggiorna .gitattributes

# Workflow normale dopo il setup:
git add .gitattributes
git add file.psd
git commit -m "feat: add design file with LFS"
git push

# Gestione:
git lfs ls-files                       # Elencare file LFS
git lfs status                         # Stato
git lfs fetch                          # Scarica blob LFS senza checkout
git lfs pull                           # Scarica e checkout blob LFS
git lfs prune                          # Rimuovi blob LFS locali non referenziati

# Migrare file esistenti a LFS:
git lfs migrate import --include="*.psd" --everything
# ATTENZIONE: riscrive la storia! Richiede force push.

# Informazioni:
git lfs env                            # Configurazione LFS
git lfs logs last                      # Ultimo log di errore
```

### Submodules

```bash
# Includere un repository dentro un altro
# Utile per dipendenze, librerie condivise, documentazione esterna

# Aggiungere un submodule:
git submodule add git@github.com:user/lib.git vendor/lib
# Crea: .gitmodules (config), vendor/lib/ (worktree del submodule)

# Clonare repo con submodules:
git clone --recurse-submodules URL
# Oppure dopo clone normale:
git submodule init
git submodule update

# Aggiornare submodule all'ultimo commit del suo remote:
git submodule update --remote vendor/lib
git add vendor/lib
git commit -m "chore: update vendor/lib submodule"

# Aggiornare TUTTI i submodules:
git submodule update --remote --merge

# Rimuovere submodule:
git submodule deinit vendor/lib
git rm vendor/lib
rm -rf .git/modules/vendor/lib

# Status dei submodules:
git submodule status
git submodule foreach 'git status'     # Esegui comando in ogni submodule
```

### Sparse Checkout

```bash
# Clonare solo parte di un repository (per monorepo grandi)

# Setup:
git clone --filter=blob:none --sparse URL
cd repo
git sparse-checkout init --cone        # Modalità cone (percorsi semplici)
git sparse-checkout set src/myproject docs/myproject
# Scarica solo le directory specificate

# Aggiungere directory:
git sparse-checkout add tests/myproject

# Vedere cosa è incluso:
git sparse-checkout list

# Disabilitare (tornare a checkout completo):
git sparse-checkout disable
```

### Git Grep

```bash
# Ricerca nel contenuto del repository (più veloce di grep perché usa l'index)

git grep "pattern"                     # Cerca nel working directory
git grep "pattern" HEAD                # Cerca nell'ultimo commit
git grep "pattern" v1.0.0              # Cerca in un tag specifico
git grep -n "pattern"                  # Con numeri di riga
git grep -c "pattern"                  # Conteggio per file
git grep -l "pattern"                  # Solo nomi file
git grep -w "pattern"                  # Solo parole intere
git grep -e "pattern1" --and -e "pattern2"  # Entrambi nella stessa riga
git grep "pattern" -- '*.py'           # Solo in file Python
```

---

## Troubleshooting Git

### 1. "Ho fatto commit nel branch sbagliato"

```bash
# Se NON hai ancora pushato:

# Opzione A: spostare l'ultimo commit
git reset --soft HEAD~1                # Uncommit (mantieni staging)
git stash                              # Salva le modifiche
git switch correct-branch              # Vai al branch corretto
git stash pop                          # Applica le modifiche
git commit -m "stesso messaggio"       # Committa nel branch giusto

# Opzione B: cherry-pick
git switch correct-branch
git cherry-pick wrong-branch           # Copia l'ultimo commit di wrong-branch
git switch wrong-branch
git reset --hard HEAD~1                # Rimuovi dal branch sbagliato
```

### 2. "Ho perso un commit dopo reset --hard"

```bash
git reflog
# Trova lo SHA del commit perso, es. HEAD@{3}
git reset --hard HEAD@{3}              # Ripristina
# Oppure crea un branch:
git branch recovered HEAD@{3}
```

### 3. "Merge conflict su file binario"

```bash
# Git non può fare merge di binari automaticamente.
git checkout --ours file.bin           # Mantieni il tuo
git checkout --theirs file.bin         # Mantieni l'altro
git add file.bin
git commit
```

### 4. "Push rifiutato (non fast-forward)"

```bash
# Qualcun altro ha pushato prima di te.
git fetch origin
git rebase origin/main                 # Rebase le tue modifiche sopra
git push
# Oppure:
git pull --rebase
git push
# MAI --force su branch condivisi. Se necessario:
git push --force-with-lease            # Fallisce se altri hanno pushato nel frattempo
```

### 5. "Repository troppo grande / clone lento"

```bash
git clone --depth 1 URL                # Shallow clone
git clone --filter=blob:none URL       # Blobless clone
git gc --aggressive                    # Ottimizza repo esistente
# Verificare se file grandi dovrebbero essere in Git LFS:
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | grep blob | sort -k3 -n -r | head -20
```

### 6. "Credenziali richieste ad ogni push"

```bash
# Usare SSH anziché HTTPS:
git remote set-url origin git@github.com:user/repo.git
# Oppure configurare credential helper (vedi sezione Credential Helper)
```

### 7. "File cancellato per errore — come recuperare?"

```bash
# File cancellato ma non committato:
git restore file.txt                   # Ripristina dalla staging area

# File cancellato e committato:
git log --diff-filter=D --name-only    # Trova in quale commit è stato cancellato
git restore --source=<sha>~1 -- path/to/file.txt  # Ripristina dal commit precedente
```

### 8. "Ho modificato il file sbagliato"

```bash
# Scartare modifiche a un file specifico:
git restore file.txt                   # Ripristina all'ultima versione staged
git restore --source HEAD file.txt     # Ripristina all'ultimo commit
```

### 9. "Voglio annullare un merge già completato"

```bash
# Se NON hai pushato:
git reset --hard HEAD~1                # Annulla il merge commit

# Se HAI pushato (branch condiviso):
git revert -m 1 <merge-commit-sha>    # Crea un commit che annulla il merge
# -m 1 = mantieni il primo parent (il branch in cui hai mergiato)
```

### 10. "Rebase ha creato un disastro"

```bash
# PRIMA opzione: abort se il rebase è in corso
git rebase --abort

# SECONDA opzione: usare il reflog
git reflog
git reset --hard HEAD@{N}             # Torna allo stato pre-rebase
```

### 11. "Commit troppo grande — come dividerlo?"

```bash
# Interactive rebase per editare il commit:
git rebase -i HEAD~1
# Cambia "pick" in "edit"
# Git si ferma al commit

git reset HEAD~1                       # Uncommit + unstage
git add file1.txt                      # Stage primo gruppo
git commit -m "feat: prima parte"
git add file2.txt                      # Stage secondo gruppo
git commit -m "feat: seconda parte"
git rebase --continue
```

### 12. "Ho pushato un segreto (API key, password)"

```bash
# PASSO 1: RUOTA IL SEGRETO IMMEDIATAMENTE.
# Il segreto è compromesso anche se lo rimuovi dalla storia.

# PASSO 2: Rimuovi dalla storia con BFG Repo Cleaner:
# (più veloce e sicuro di git filter-branch)
bfg --replace-text passwords.txt repo.git
# passwords.txt contiene i segreti da rimuovere

# Oppure con git filter-repo (moderno):
git filter-repo --invert-paths --path file-with-secret.txt
# Oppure sostituire testo:
git filter-repo --replace-text expressions.txt

# PASSO 3: Force push (richiede coordinamento col team):
git push --force --all
git push --force --tags

# PASSO 4: Tutti nel team devono ri-clonare il repo.
```

### 13. "git pull dice 'refusing to merge unrelated histories'"

```bash
# Succede quando due repository senza storia comune vengono combinati.
git pull origin main --allow-unrelated-histories
# Poi risolvere eventuali conflitti e committare.
```

### 14. "Il file è troppo grande per GitHub (>100MB)"

```bash
# Opzione 1: Git LFS
git lfs track "*.large"
git add .gitattributes
git add file.large
git commit -m "feat: add large file with LFS"

# Opzione 2: rimuovere dalla storia se già committato
git filter-repo --invert-paths --path path/to/large-file
```

### 15. "Voglio modificare l'autore di commit passati"

```bash
# Ultimo commit:
git commit --amend --author="Nome <email@example.com>"

# Commit più vecchi — con rebase interattivo:
git rebase -i <commit-prima>
# Cambia "pick" in "edit" per i commit da modificare
git commit --amend --author="Nome <email@example.com>"
git rebase --continue

# ATTENZIONE: riscrive la storia! Non fare su branch condivisi.
```

### 16. "Detached HEAD — cosa fare?"

```bash
# Stai lavorando su un commit senza branch.

# Se hai già committato e vuoi salvare:
git switch -c my-new-branch            # Crea branch dal punto corrente

# Se vuoi solo tornare al branch:
git switch main                        # Torna a main

# I commit fatti in detached HEAD senza branch saranno garbage collected!
```

### 17. "git status è lentissimo"

```bash
# Per repo grandi:
git config core.fsmonitor true         # Abilita filesystem monitor
git config core.untrackedCache true    # Cache per file non tracciati

# Oppure usare:
git status -uno                        # Ignora file non tracciati
```

### 18. ".gitignore non funziona su file già tracciati"

```bash
# .gitignore si applica solo a file NON tracciati.
# Per file già nel repo:
git rm --cached file.txt               # Rimuovi dal tracking (mantieni su disco)
# Poi aggiungi a .gitignore e committa.
```

### 19. "Voglio vedere cosa è cambiato in un file nel tempo"

```bash
git log -p -- path/to/file             # Cronologia con diff
git log --follow -p -- path/to/file    # Segue anche i rename
git blame path/to/file                 # Chi ha scritto ogni riga
git blame -L 10,20 path/to/file        # Solo righe 10-20
git blame -w path/to/file              # Ignora whitespace
```

### 20. "Come faccio a sapere quali branch sono stati merged?"

```bash
git branch --merged main               # Branch merged in main
git branch --no-merged main            # Branch NON merged in main
git branch -r --merged main            # Branch remoti merged in main

# Pulizia branch merged:
git branch --merged main | grep -v '^[ *]*main$' | xargs git branch -d
```

### 21. "Come creare un patch e applicarlo?"

```bash
# Creare patch:
git diff > changes.patch               # Diff non staged
git diff --staged > staged.patch       # Diff staged
git format-patch -3                    # Ultimi 3 commit come patch email
git format-patch main..feature         # Tutti i commit da feature

# Applicare patch:
git apply changes.patch                # Applica diff
git apply --check changes.patch        # Dry run (verifica se applicabile)
git am < 0001-commit-message.patch     # Applica format-patch (preserva commit)
```

### 22. "Come esportare il repo senza .git?"

```bash
git archive --format=tar.gz --output=project.tar.gz HEAD
git archive --format=zip --output=project.zip HEAD
git archive --format=zip HEAD -- src/ docs/  # Solo certe directory
```

---

## FAQ — Domande Frequenti

### Q1: Qual è la differenza tra `git merge` e `git rebase`?

**Merge** crea un nuovo commit (merge commit) che unisce le due linee di storia. La storia non lineare è preservata.

**Rebase** riapplica i commit di un branch sopra un altro, creando una storia lineare. I commit originali sono sostituiti da nuovi commit con hash diversi.

Regola generale: rebase per branch locali non condivisi, merge per branch condivisi.

### Q2: Quando usare `--force-with-lease` vs `--force`?

`--force` sovrascrive il branch remoto incondizionatamente — può cancellare commit di altri.

`--force-with-lease` fallisce se qualcuno ha pushato dopo il tuo ultimo fetch — è una salvaguardia. Usa sempre `--force-with-lease` al posto di `--force`.

### Q3: Che differenza c'è tra `git pull` e `git fetch`?

`git fetch` scarica i commit dal remote senza toccare il working directory o il branch corrente.

`git pull` = `git fetch` + `git merge` (o `git fetch` + `git rebase` con `--rebase`).

Preferire `git fetch` + merge/rebase manuale per avere più controllo.

### Q4: Cosa significa "detached HEAD"?

HEAD punta direttamente a un commit anziché a un branch. Succede quando fai checkout di un commit, un tag, o un branch remoto. I commit fatti in questo stato non sono su nessun branch e verranno garbage collected se non crei un branch.

### Q5: Come funziona `git stash` internamente?

`git stash` crea due (o tre con `-u`) commit speciali: uno per le modifiche nell'index, uno per le modifiche nel working tree, e opzionalmente uno per i file untracked. Questi commit sono collegati al ref `refs/stash` come stack LIFO.

### Q6: Che differenza c'è tra `git reset` e `git revert`?

`git reset` sposta HEAD e opzionalmente modifica index e working directory. Riscrive la storia — pericoloso su branch condivisi.

`git revert` crea un NUOVO commit che annulla le modifiche di un commit precedente. Sicuro su branch condivisi perché aggiunge alla storia.

### Q7: Come funziona la three-way merge?

Git trova il **merge base** (l'antenato comune più recente), poi confronta le modifiche di ciascun branch rispetto alla base. Se una modifica è in un solo branch, viene accettata automaticamente. Se entrambi hanno modificato la stessa area, Git segnala un conflitto.

### Q8: Cos'è un "fast-forward" merge?

Si verifica quando il branch target (es. main) non ha commit nuovi dopo il punto di biforcazione. Git semplicemente sposta il puntatore del branch in avanti — nessun merge commit necessario. Usa `--no-ff` per forzare un merge commit anche in questo caso.

### Q9: Posso cambiare il messaggio di un commit vecchio?

Sì, con interactive rebase: `git rebase -i <commit-prima>` e cambia `pick` in `reword`. Ma questo riscrive la storia — tutti i commit successivi avranno hash diversi. Non fare su branch già condivisi.

### Q10: Che differenza c'è tra `git rm` e cancellare il file?

`rm file.txt` cancella il file dal filesystem ma Git lo vede come "deleted" (non staged). `git rm file.txt` cancella il file E lo stage per il commit in un unico passaggio.

### Q11: Come funziona `git bisect` con test automatici?

Dopo `git bisect start <bad> <good>`, usa `git bisect run <script>`. Lo script deve uscire con codice 0 (good), 1-124/126-127 (bad), o 125 (skip). Git esegue la ricerca binaria automaticamente.

### Q12: Posso usare Git senza GitHub?

Assolutamente sì. Git è un tool locale che funziona senza nessun server remoto. GitHub/GitLab/Bitbucket sono piattaforme di hosting — Git funziona perfettamente con server propri, o anche solo in locale.

### Q13: Che differenza c'è tra `checkout`, `switch` e `restore`?

`git checkout` è il comando classico che fa troppe cose: cambia branch E ripristina file. Git 2.23 ha introdotto:
- `git switch` — solo per cambiare branch
- `git restore` — solo per ripristinare file

Preferire `switch` e `restore` per chiarezza.

### Q14: Come gestire i conflitti con file binari?

Git non può fare merge automatico di file binari. Devi scegliere manualmente: `git checkout --ours file.bin` (tua versione) o `git checkout --theirs file.bin` (loro versione). Poi `git add` e commit. Per workflow collaborativi su binari, considerare Git LFS con file locking.

### Q15: Cosa succede se due persone pushano contemporaneamente?

Il secondo push fallisce con "non fast-forward". Il secondo sviluppatore deve fare `git fetch` + `git rebase` (o `git pull --rebase`) e poi pushare di nuovo. Git non perde mai dati — forza la risoluzione dei conflitti prima del push.

### Q16: Come faccio a trovare un file che esisteva ma è stato cancellato?

```bash
# Trova il commit che ha cancellato il file:
git log --diff-filter=D --name-only -- '**/filename*'
# Ripristina:
git restore --source=<sha>~1 -- path/to/file
```

### Q17: Perché `git log` non mostra tutti i commit dopo un merge?

`git log` segue il primo parent di default. Per vedere tutti i commit inclusi i merge:
```bash
git log --all --graph                  # Tutti i branch, con grafo
git log --first-parent                 # Solo la linea principale
```

### Q18: Come funzionano i packfile e la garbage collection in Git?

Git inizialmente memorizza ogni oggetto come un file individuale (loose object) nella directory `.git/objects/`. Quando il numero di loose object cresce, Git li comprime in **packfile** (`.git/objects/pack/*.pack`), un formato binario altamente ottimizzato che usa la compressione delta — memorizza le differenze tra oggetti simili anziché copie intere. Questo riduce drasticamente lo spazio su disco: un repository con migliaia di commit può occupare una frazione dello spazio dei file sorgente.

```bash
# Forzare il packing manuale:
git gc                          # Garbage collection + packing
git gc --aggressive             # Packing più aggressivo (lento, usare raramente)
git repack -a -d                # Repack senza gc completo
git count-objects -vH           # Statistiche sugli oggetti

# Output tipico di count-objects:
# count: 42           ← loose objects
# size: 168.00 KiB    ← dimensione loose objects
# in-pack: 18934      ← oggetti nei packfile
# packs: 2            ← numero di packfile
# size-pack: 12.40 MiB ← dimensione totale packfile
```

La **garbage collection** rimuove gli oggetti non raggiungibili (commit orfani dopo un rebase o reset, blob non referenziati). Git non elimina immediatamente questi oggetti: restano nel repository per un periodo configurabile (`gc.pruneExpire`, default 2 settimane), permettendo il recupero tramite reflog. Il comando `git fsck --unreachable` elenca tutti gli oggetti non raggiungibili senza eliminarli.

### Q19: Che differenza c'è tra shallow clone e partial clone?

Entrambi riducono la dimensione del clone, ma con strategie diverse:

- **Shallow clone** (`git clone --depth=N`): scarica solo gli ultimi N commit. La storia precedente è assente. Utile per CI/CD dove serve solo il codice corrente. Limitazioni: `git log` mostra solo N commit, `git blame` potrebbe essere incompleto, merge e rebase possono fallire se richiedono storia più profonda.

- **Partial clone** (`git clone --filter=blob:none`): scarica tutti i commit e i tree, ma omette i blob (contenuto dei file) fino a quando non vengono richiesti. Questo mantiene la storia completa del DAG, permettendo `git log`, `git blame` e operazioni sulla storia senza limitazioni. I blob vengono scaricati on-demand quando si accede ai file. Richiede Git 2.22+ e un server che supporti il protocollo v2.

```bash
# Shallow: solo ultimi 10 commit
git clone --depth=10 https://github.com/org/repo.git

# Partial: no blob, scaricamento on-demand
git clone --filter=blob:none https://github.com/org/repo.git

# Treeless: no blob e no tree, massima riduzione (Git 2.20+)
git clone --filter=tree:0 https://github.com/org/repo.git

# Convertire shallow in full:
git fetch --unshallow
```

Per repository di grandi dimensioni (monorepo con decine di GB), il partial clone con `--filter=blob:none` è la strategia raccomandata per gli sviluppatori, mentre lo shallow clone con `--depth=1` è preferibile per i pipeline CI/CD che non necessitano della storia.

### Q20: Come funziona `git worktree` e quando usarlo?

`git worktree` permette di avere più working tree collegati allo stesso repository. Ogni worktree può avere un branch diverso checked out contemporaneamente, senza duplicare l'intera directory `.git/`. Questo è particolarmente utile per:

1. **Code review**: mantenere il proprio lavoro su un branch mentre si revisiona un altro senza dover fare stash o commit temporanei.
2. **Build paralleli**: eseguire build di branch diversi in contemporanea.
3. **Hotfix urgenti**: passare rapidamente a un branch di rilascio senza interrompere il lavoro in corso.

```bash
# Creare un worktree per un branch esistente:
git worktree add ../hotfix-branch hotfix/critical-fix

# Creare un worktree con un nuovo branch:
git worktree add -b feature/nuova ../feature-dir main

# Elencare tutti i worktree:
git worktree list

# Rimuovere un worktree (dopo aver finito):
git worktree remove ../hotfix-branch

# Pulire worktree orfani (directory cancellate manualmente):
git worktree prune
```

Ogni worktree ha il proprio HEAD, index e working directory, ma condivide il database degli oggetti (`.git/objects/`) e i ref. Questo significa che un commit fatto in un worktree è immediatamente visibile dagli altri. La limitazione principale è che due worktree non possono avere lo stesso branch checked out simultaneamente.

### Q21: Come si gestiscono i file di grandi dimensioni con Git LFS?

Git Large File Storage (LFS) sostituisce i file di grandi dimensioni (asset binari, dataset, modelli ML) con puntatori di testo nel repository, mentre il contenuto reale viene memorizzato su un server LFS separato.

```bash
# Installazione e configurazione:
git lfs install

# Tracciare tipi di file:
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "modelli/**/*.bin"

# Il file .gitattributes viene aggiornato automaticamente:
# *.psd filter=lfs diff=lfs merge=lfs -text

# Verificare quali file sono gestiti da LFS:
git lfs ls-files

# Migrazione di file esistenti a LFS (riscrive la storia):
git lfs migrate import --include="*.psd" --everything
```

Senza LFS, un singolo file binario di 100 MB viene duplicato in ogni commit che lo modifica, gonfiando il repository in modo irreversibile (anche dopo la cancellazione). Con LFS, ogni versione del file è memorizzata una sola volta sul server LFS e il repository Git contiene solo i puntatori. Il download avviene on-demand durante il checkout, riducendo drasticamente i tempi di clone. Il costo è una dipendenza dal server LFS per l'accesso ai contenuti binari — in ambienti offline o con connettività limitata, questo può rappresentare un vincolo operativo.

### Q22: Come verificare l'integrità di un repository Git?

```bash
# Verifica completa dell'integrità:
git fsck --full                    # Controlla tutti gli oggetti
git fsck --connectivity-only       # Solo raggiungibilità (più veloce)

# Verificare che il repository non sia corrotto:
git fsck --no-dangling             # Ignora oggetti orfani (normali)

# Riparare un repository con indice corrotto:
rm .git/index
git reset                          # Ricostruisce l'indice dal HEAD

# Recuperare da un packfile corrotto:
git unpack-objects < .git/objects/pack/pack-*.pack
git repack -a -d
```

`git fsck` esegue un controllo di integrità strutturale: verifica che ogni oggetto sia valido, che gli hash corrispondano al contenuto, che i puntatori parent/tree siano consistenti e che non ci siano riferimenti a oggetti mancanti. È buona pratica eseguirlo periodicamente su repository critici, specialmente dopo crash di sistema, interruzioni di corrente o trasferimenti tra filesystem diversi.

---

## Esercizi Pratici

### Esercizio 1: Esplorare gli oggetti Git

```bash
# Obiettivo: capire come Git memorizza i dati internamente

# 1. Creare un repo vuoto e il primo file:
mkdir git-lab && cd git-lab
git init
echo "Ciao" > saluto.txt
git add saluto.txt

# 2. Ispezionare l'index:
git ls-files --stage
# Annotare l'hash del blob

# 3. Leggere il blob:
git cat-file -t <hash>          # Deve dire "blob"
git cat-file -p <hash>          # Deve mostrare "Ciao"

# 4. Committare e ispezionare il commit:
git commit -m "feat: primo commit"
git cat-file -p HEAD            # Mostra tree, author, message
git cat-file -p HEAD^{tree}     # Mostra il tree del commit

# 5. Modificare il file e vedere come cambia:
echo "Mondo" >> saluto.txt
git add saluto.txt
git ls-files --stage            # Hash diverso dal passo 2!

# Domanda: perché l'hash è diverso anche se il file ha lo stesso nome?
```

### Esercizio 2: Three-Tree Architecture

```bash
# Obiettivo: verificare la differenza tra i tre alberi

# 1. Creare un file e committarlo:
echo "versione 1" > test.txt
git add test.txt
git commit -m "v1"

# 2. Modificare senza staging:
echo "versione 2" > test.txt
git diff                        # Working dir vs Index → mostra diff
git diff --staged               # Index vs HEAD → nessuna differenza

# 3. Staging senza commit:
git add test.txt
git diff                        # Nessuna differenza (working = index)
git diff --staged               # Index vs HEAD → mostra diff

# 4. Testare i tre livelli di reset:
git commit -m "v2"
echo "versione 3" > test.txt
git add test.txt
git commit -m "v3"

# Ora test.txt ha "versione 3" in tutti e tre gli alberi
git reset --soft HEAD~1         # HEAD torna a v2, index e working hanno v3
git status                      # Mostra: "Changes to be committed: test.txt"

git reset --mixed HEAD          # Index torna a v2 (HEAD è già a v2)
git status                      # Mostra: "Changes not staged: test.txt"

# Domanda: cosa mostra git diff e git diff --staged in ogni fase?
```

### Esercizio 3: DAG e Merge

```bash
# Obiettivo: creare un DAG con branch e merge, poi visualizzarlo

# 1. Creare storia lineare:
git init dag-lab && cd dag-lab
echo "A" > file.txt && git add . && git commit -m "A"
echo "B" > file.txt && git add . && git commit -m "B"

# 2. Creare branch e divergere:
git switch -c feature
echo "C-feature" > feature.txt && git add . && git commit -m "C (feature)"
echo "D-feature" >> feature.txt && git add . && git commit -m "D (feature)"

git switch main
echo "C-main" > main.txt && git add . && git commit -m "C (main)"

# 3. Visualizzare il DAG:
git log --oneline --graph --all

# 4. Merge e osservare il risultato:
git merge feature -m "Merge feature"
git log --oneline --graph --all

# 5. Contare i parent del merge commit:
git cat-file -p HEAD    # Dovrebbe mostrare due righe "parent"

# Domanda: qual è il merge base? Come lo trovi?
# Suggerimento: git merge-base main feature (da eseguire PRIMA del merge)
```

### Esercizio 4: Rebase vs Merge

```bash
# Obiettivo: confrontare il risultato di rebase e merge

# 1. Setup: creare due branch identici
git init rebase-lab && cd rebase-lab
echo "base" > file.txt && git add . && git commit -m "base"

git switch -c feature-merge
echo "feature" > feature.txt && git add . && git commit -m "feat: add feature"

git switch main
git switch -c feature-rebase
git cherry-pick feature-merge          # Stesso commit su entrambi i branch

# 2. Aggiungere commit su main:
git switch main
echo "main update" > main.txt && git add . && git commit -m "chore: main update"

# 3. Merge:
git switch -c main-merge main
git merge feature-merge --no-ff
git log --oneline --graph

# 4. Rebase:
git switch feature-rebase
git rebase main
git switch main
git merge feature-rebase               # Ora è fast-forward!
git log --oneline --graph

# Confronta i due grafi: merge crea un merge commit, rebase linearizza.
```

### Esercizio 5: Recovery con Reflog

```bash
# Obiettivo: perdere e recuperare un commit

# 1. Creare commit da "perdere":
git init reflog-lab && cd reflog-lab
echo "importante" > secret.txt && git add . && git commit -m "commit importante"
echo "altro" > altro.txt && git add . && git commit -m "commit successivo"

# 2. "Perdere" il primo commit:
git reset --hard HEAD~2                # Torna all'inizio (perdi entrambi)

# 3. Verificare che i file siano spariti:
ls                                     # Vuoto!

# 4. Recuperare con reflog:
git reflog                             # Trova "commit importante"
git reset --hard HEAD@{2}              # Recupera!
ls                                     # I file sono tornati!

# 5. Alternativa: creare branch dal reflog:
git reset --hard HEAD~2                # Perdi di nuovo
git branch salvati HEAD@{1}            # Crea branch senza cambiare HEAD
git switch salvati                     # Vai al branch con i file
```

### Esercizio 6: Bisect

```bash
# Obiettivo: trovare il commit che ha introdotto un "bug"

# 1. Setup: creare 10 commit, uno dei quali introduce un bug
git init bisect-lab && cd bisect-lab
for i in $(seq 1 10); do
    echo "commit $i" >> log.txt
    if [ $i -eq 6 ]; then
        echo "BUG" > bug.txt          # Il "bug" appare al commit 6
    fi
    git add . && git commit -m "commit $i"
done

# 2. Bisect manuale:
git bisect start
git bisect bad HEAD                    # L'ultimo commit ha il bug
git bisect good HEAD~9                 # Il primo commit era OK

# 3. Ad ogni checkpoint, testare:
# Se bug.txt esiste → git bisect bad
# Se bug.txt NON esiste → git bisect good
# (controllare con: ls bug.txt 2>/dev/null && echo BAD || echo GOOD)

# 4. Git dovrebbe trovare "commit 6" come primo commit bad

# 5. Bisect automatizzato:
git bisect reset
git bisect start HEAD HEAD~9
git bisect run bash -c 'test ! -f bug.txt'
# Lo script esce con 0 se bug.txt non esiste (good), 1 se esiste (bad)

git bisect reset
```

### Esercizio 7: Configurazione multi-livello

```bash
# Obiettivo: capire la precedenza delle configurazioni

# 1. Impostare un valore a livello global:
git config --global user.name "Global Name"

# 2. Impostare un valore diverso a livello local:
git init config-lab && cd config-lab
git config --local user.name "Local Name"

# 3. Verificare quale vince:
git config user.name                   # Deve mostrare "Local Name"
git config --show-origin user.name     # Mostra il file sorgente
git config --show-scope user.name      # Mostra "local"

# 4. Rimuovere il valore locale:
git config --local --unset user.name
git config user.name                   # Ora mostra "Global Name"

# 5. Elencare tutta la configurazione con sorgente:
git config --list --show-origin --show-scope

# Ripulire:
git config --global user.name "Renan Augusto Macena"
```

### Esercizio 8: Interactive Rebase per pulizia storia

```bash
# Obiettivo: usare rebase interattivo per pulire la storia prima di una PR

# 1. Setup: simulare una sessione di sviluppo disordinata
git init rebase-cleanup && cd rebase-cleanup
echo "base" > app.txt && git add . && git commit -m "feat: initial app"

echo "feature v1" >> app.txt && git add . && git commit -m "feat: add feature"
echo "typo fix" >> app.txt && git add . && git commit -m "fix: typo"
echo "debug log" >> app.txt && git add . && git commit -m "wip: debug"
echo "feature v2" >> app.txt && git add . && git commit -m "feat: improve feature"
echo "remove debug" >> app.txt && git add . && git commit -m "chore: remove debug"

# 2. Vedere la storia:
git log --oneline
# Sei commit — troppi per una feature semplice

# 3. Rebase interattivo per pulire:
# git rebase -i HEAD~5
# Nell'editor:
# pick  feat: add feature
# fixup fix: typo               ← unisci al precedente
# drop  wip: debug              ← elimina
# pick  feat: improve feature
# fixup chore: remove debug     ← unisci al precedente

# 4. Risultato: 2 commit puliti anziché 5 disordinati
git log --oneline

# Domanda: perché gli hash dei commit sono cambiati?
# Risposta: il rebase crea NUOVI commit con parent diversi.
```

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Git Reference Manual**: https://git-scm.com/docs — Riferimento completo di ogni comando Git con opzioni e esempi.
- **Pro Git Book (2nd Edition)**: https://git-scm.com/book/en/v2 — Libro ufficiale gratuito, copre dai fondamenti agli internals. Disponibile anche in italiano.
- **Git Internals — Plumbing and Porcelain**: https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain — Capitolo dedicato agli oggetti interni (blob, tree, commit, tag).
- **Git Configuration**: https://git-scm.com/docs/git-config — Documentazione completa di tutte le variabili di configurazione.
- **Git Workflows — Atlassian**: https://www.atlassian.com/git/tutorials/comparing-workflows — Confronto visivo tra workflow Git (centralizzato, feature branch, gitflow, forking).

### Libri consigliati

- **"Pro Git" — Scott Chacon, Ben Straub** (Apress, 2nd ed.) — Il riferimento definitivo per Git, dagli snapshot ai packfile. Gratuito online.
- **"Version Control with Git" — Prem Kumar Ponuthorai, Jon Loeliger** (O'Reilly, 3rd ed.) — Approccio pratico con focus su branching, merging e risoluzione conflitti.
- **"Git Pocket Guide" — Richard E. Silverman** (O'Reilly) — Riferimento compatto per i comandi più usati, ideale come quick reference.

---

## Riferimenti Incrociati

| Modulo | File | Relazione |
|--------|------|-----------|
| 02 | [02-strategie-branching.md](02-strategie-branching.md) | Applica i fondamenti di branching e merge trattati qui a strategie di team |
| 06 | [06-git-branching-merge-avanzato.md](06-git-branching-merge-avanzato.md) | Approfondisce merge strategies, rebase avanzato e rerere |
| 07 | [07-git-interni-oggetti-refs.md](07-git-interni-oggetti-refs.md) | Espande il content-addressable storage e la struttura interna di Git |
| 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) | Automazione locale con hook pre-commit, pre-push e commit-msg |
| 10 | [10-git-stash-reset-recovery.md](10-git-stash-reset-recovery.md) | Tecniche avanzate di recovery con stash, reset e reflog |
| 11 | [11-gitignore-gitattributes-config.md](11-gitignore-gitattributes-config.md) | Configurazione avanzata: .gitignore, .gitattributes e merge driver |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **DAG** | Directed Acyclic Graph — struttura dati che modella la storia dei commit in Git come grafo orientato senza cicli |
| **SHA-1 / SHA-256** | Funzioni hash crittografiche usate da Git per identificare univocamente ogni oggetto (blob, tree, commit, tag) |
| **Blob** | Oggetto Git che contiene il contenuto di un singolo file, senza metadati (nome, permessi) |
| **Tree** | Oggetto Git che rappresenta una directory: contiene riferimenti a blob (file) e altri tree (sottodirectory) |
| **Commit** | Oggetto Git che punta a un tree (snapshot), ai commit parent e contiene metadati (autore, data, messaggio) |
| **Index (Staging Area)** | Area intermedia tra working tree e repository dove si preparano i file per il prossimo commit |
| **Working Tree** | La copia di lavoro dei file sul filesystem locale, dove si effettuano le modifiche |
| **Reflog** | Log locale delle variazioni di ogni riferimento (HEAD, branch), utile per recuperare commit apparentemente persi |
| **Rebase** | Operazione che riapplica una sequenza di commit su una nuova base, riscrivendo la storia |
| **Cherry-pick** | Copia un singolo commit da un branch a un altro creando un nuovo commit con lo stesso diff |
| **Fast-forward** | Tipo di merge in cui il branch di destinazione viene semplicemente spostato avanti, senza creare un merge commit |
| **Bisect** | Comando che esegue una ricerca binaria nella storia dei commit per individuare il commit che ha introdotto un bug |
| **Detached HEAD** | Stato in cui HEAD punta direttamente a un commit anziché a un branch, i nuovi commit non appartengono a nessun branch |
| **Content-addressable storage** | Meccanismo per cui ogni oggetto è memorizzato usando il proprio hash come chiave — identico contenuto = identico indirizzo |
| **Packfile** | Formato di compressione delta usato da Git per ridurre lo spazio su disco raggruppando oggetti simili |
