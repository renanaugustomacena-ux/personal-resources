---
corso: "GitHub e Git Actions"
fase: "1 — Fondamenti Git"
modulo: "07"
titolo: "Git Internals: Oggetti e Refs"
versione: "Git 2.47+"
livello: "Avanzato"
prerequisiti:
  - "01 — Fondamenti Git"
  - "06 — Git Branching e Merge Avanzato"
obiettivi:
  - "Comprendere il modello a 4 oggetti di Git (blob, tree, commit, tag)"
  - "Esplorare il content-addressable storage e la struttura di .git/objects/"
  - "Manipolare refs, HEAD, symbolic refs e packed-refs"
  - "Analizzare i transfer protocol (smart HTTP, SSH, pack protocol)"
  - "Diagnosticare e recuperare repository corrotti con git fsck e reflog"
tag: [git, internals, oggetti, refs, sha-1, sha-256, pack, fsck, transfer-protocol]
---

# Git Internals: Oggetti e Refs — Guida Approfondita

> **Modulo 07** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti Git](01-fondamenti-git.md), [Git Branching e Merge Avanzato](06-git-branching-merge-avanzato.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere il modello a 4 oggetti di Git (blob, tree, commit, tag)
> 2. Esplorare il content-addressable storage e la struttura di `.git/objects/`
> 3. Manipolare refs, HEAD, symbolic refs e packed-refs
> 4. Analizzare i transfer protocol (smart HTTP, SSH, pack protocol)
> 5. Diagnosticare e recuperare repository corrotti con `git fsck` e reflog
>
> **Tempo stimato:** 10-12 ore · **Livello:** Avanzato

## Idee guida
1. **4 oggetti git: blob (file content), tree (directory), commit (snapshot+meta), tag (annotated tag).**
2. **`.git/objects/` content-addressed by SHA-1 (transitioning to SHA-256).**
3. **Refs sono pointer: `.git/refs/heads/main`.**
4. **`git cat-file -p <sha>` esplora oggetti.**
5. **Transfer protocols (smart HTTP, SSH, pack protocol) governano push/fetch.**
6. **`git fsck` + recovery: dal dangling commit al repository corrotto.**


## Indice
- [Panoramica](#panoramica)
- [Il Modello a Oggetti di Git](#il-modello-a-oggetti-di-git)
- [Blob: Il Contenuto dei File](#blob-il-contenuto-dei-file)
- [Tree: La Struttura delle Directory](#tree-la-struttura-delle-directory)
- [Commit: Gli Snapshot della Cronologia](#commit-gli-snapshot-della-cronologia)
- [Tag: Annotazioni Permanenti](#tag-annotazioni-permanenti)
- [SHA-1 Hashing e Content-Addressable Storage](#sha-1-hashing-e-content-addressable-storage)
- [Packfiles e Delta Compression](#packfiles-e-delta-compression)
- [Refs: Branch, Tag, HEAD e Riferimenti Speciali](#refs-branch-tag-head-e-riferimenti-speciali)
- [Reflog: La Rete di Sicurezza](#reflog-la-rete-di-sicurezza)
- [Garbage Collection](#garbage-collection)
- [Index e Staging Area Internals](#index-e-staging-area-internals)
- [Transfer Protocols](#transfer-protocols)
- [Git Fsck: Verifica dell'Integrità e Recovery Avanzato](#git-fsck-verifica-dellintegrità-e-recovery-avanzato)
- [Grafting, Replace e Shallow Clone](#grafting-replace-e-shallow-clone)
- [Worktrees e Internals Multi-Working-Tree](#worktrees-e-internals-multi-working-tree)
- [Commit Graph e Bloom Filter](#commit-graph-e-bloom-filter)
- [Reachability Bitmaps e EWAH Compression](#reachability-bitmaps-e-ewah-compression)
- [Reftable: Il Nuovo Backend per i Riferimenti](#reftable-il-nuovo-backend-per-i-riferimenti)
- [Cruft Packs e Gestione Oggetti Non Raggiungibili](#cruft-packs-e-gestione-oggetti-non-raggiungibili)
- [Git Bundle: Trasferimento Offline e Backup](#git-bundle-trasferimento-offline-e-backup)
- [Sparse Index e Sparse Checkout Internals](#sparse-index-e-sparse-checkout-internals)
- [Git Maintenance: Manutenzione Automatizzata](#git-maintenance-manutenzione-automatizzata)
- [Verso Git 3.0: SHA-256 e Reftable di Default](#verso-git-30-sha-256-e-reftable-di-default)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande e Risposte](#domande-e-risposte)
- [Esercizi](#esercizi)
- [Riferimenti](#riferimenti)

---

## Panoramica

Git è fondamentalmente un content-addressable filesystem con un'interfaccia di versionamento costruita sopra di esso. Comprendere i meccanismi interni di Git — come gli oggetti vengono memorizzati, come i riferimenti funzionano e come la garbage collection mantiene il repository pulito — è essenziale per risolvere problemi complessi, ottimizzare le performance e capire veramente cosa accade dietro le quinte quando si eseguono comandi Git quotidiani.

A differenza di molti sistemi di versionamento che memorizzano le differenze (delta) tra versioni successive dei file, Git memorizza snapshot completi del progetto ad ogni commit. Questa scelta progettuale, combinata con l'uso intensivo di compressione e deduplicazione basata su hash, rende Git estremamente efficiente sia in termini di velocità che di spazio di archiviazione.

La directory `.git` è il cuore di ogni repository Git. Contiene tutti gli oggetti, i riferimenti, la configurazione e i metadati necessari per ricostruire qualsiasi versione del progetto. Esplorare questa directory è il modo migliore per comprendere come Git funziona internamente.

```bash
# Struttura della directory .git
.git/
├── HEAD              # Riferimento al branch corrente
├── config            # Configurazione locale del repository
├── description       # Descrizione (usata da GitWeb)
├── hooks/            # Script di hook
├── index             # Staging area (file binario)
├── info/             # Informazioni aggiuntive (exclude, etc.)
│   ├── exclude       # Pattern di esclusione locali (come .gitignore ma non versionato)
│   ├── refs          # Cache dei riferimenti
│   └── packs         # Lista dei packfile
├── logs/             # Log delle operazioni (reflog)
│   ├── HEAD          # Reflog di HEAD
│   └── refs/         # Reflog per ogni branch
├── objects/          # Database degli oggetti
│   ├── info/         # Metadati sugli oggetti
│   │   ├── alternates  # Percorsi a object store condivisi
│   │   └── packs       # Informazioni sui packfile disponibili
│   └── pack/         # Packfiles (oggetti compressi)
│       ├── pack-xxx.pack  # Packfile binario
│       ├── pack-xxx.idx   # Indice del packfile
│       └── multi-pack-index  # Indice multi-pack (opzionale)
├── packed-refs       # Riferimenti compressi in un file unico
├── shallow           # Lista dei commit shallow (se clone parziale)
├── refs/             # Riferimenti (branch, tag, remoti)
│   ├── heads/        # Branch locali
│   ├── remotes/      # Branch remoti
│   └── tags/         # Tag
├── commit-graph      # Grafo dei commit accelerato (opzionale)
└── worktrees/        # Metadata per worktree aggiuntivi
```

### Comandi Plumbing vs Porcelain

Git distingue tra comandi **porcelain** (interfaccia utente: `commit`, `push`, `log`) e comandi **plumbing** (componenti interni: `cat-file`, `hash-object`, `update-ref`, `write-tree`). I comandi porcelain sono costruiti sui plumbing. Comprendere i plumbing è fondamentale per capire cosa succede dietro ogni operazione quotidiana.

```bash
# Porcelain → Plumbing equivalente
# git add file.txt →
git hash-object -w file.txt
git update-index --add --cacheinfo 100644 <hash> file.txt

# git commit -m "msg" →
git write-tree
echo "msg" | git commit-tree <tree-hash> -p HEAD
git update-ref HEAD <commit-hash>

# git branch new-branch →
git update-ref refs/heads/new-branch HEAD

# git tag v1.0 →
git update-ref refs/tags/v1.0 HEAD
```

---

## Il Modello a Oggetti di Git

Git gestisce quattro tipi fondamentali di oggetti: **blob**, **tree**, **commit** e **tag**. Ogni oggetto è identificato univocamente dal suo hash SHA-1 (un valore esadecimale di 40 caratteri). Questo hash viene calcolato dal contenuto dell'oggetto stesso, rendendo Git un sistema content-addressable: due oggetti con lo stesso contenuto avranno sempre lo stesso hash, indipendentemente dal loro nome o posizione.

```bash
# Visualizzare il tipo di un oggetto
git cat-file -t abc1234
# Output: blob, tree, commit, o tag

# Visualizzare il contenuto di un oggetto
git cat-file -p abc1234

# Visualizzare la dimensione di un oggetto
git cat-file -s abc1234

# Batch mode: ispezionare molti oggetti
git cat-file --batch <<'EOF'
HEAD
HEAD^{tree}
HEAD:README.md
EOF

# Batch check (solo tipo e dimensione)
git cat-file --batch-check <<'EOF'
HEAD
HEAD^{tree}
EOF
```

La relazione tra i quattro tipi di oggetti forma un grafo aciclico diretto (DAG — Directed Acyclic Graph):

```
commit → tree → blob
  │        └──→ tree → blob
  │                  → blob
  └──→ commit (parent)
         └──→ tree → ...

tag → commit
```

### Integrità End-to-End

L'hash di un commit include l'hash del suo tree, che a sua volta include gli hash dei blob e tree figli. Modificare un singolo byte in qualsiasi file storico invaliderebbe la catena di hash fino alla radice. Questa proprietà rende Git un **Merkle tree**, dove l'hash del commit è un digest crittografico dell'intero snapshot del progetto e della sua cronologia.

---

## Blob: Il Contenuto dei File

Un **blob** (Binary Large Object) rappresenta il contenuto di un singolo file. Non contiene il nome del file, i permessi o qualsiasi metadato — solo i byte grezzi del contenuto. Due file con contenuto identico, anche in directory diverse o con nomi diversi, condividono lo stesso blob.

```bash
# Creare un blob manualmente
echo "Hello, Git internals!" | git hash-object -w --stdin
# Output: 8ab686eafeb1f44702738c8b0f24f2567c36da6d

# Il blob viene memorizzato in .git/objects/
# I primi 2 caratteri dell'hash formano il nome della directory
# I restanti 38 formano il nome del file
ls .git/objects/8a/
# Output: b686eafeb1f44702738c8b0f24f2567c36da6d

# Leggere il contenuto di un blob
git cat-file -p 8ab686ea
# Output: Hello, Git internals!

# Calcolare l'hash senza memorizzare
echo "Hello, Git internals!" | git hash-object --stdin
# Output: 8ab686eafeb1f44702738c8b0f24f2567c36da6d

# Creare blob da un file
git hash-object -w README.md
```

### Come Git Calcola l'Hash di un Blob

Git non calcola l'hash semplicemente dal contenuto del file. Antepone un header composto dal tipo dell'oggetto, uno spazio, la dimensione in byte del contenuto e un byte null.

```bash
# Formula: SHA-1("blob <dimensione>\0<contenuto>")
# Per il nostro esempio: SHA-1("blob 22\0Hello, Git internals!\n")

# Verifica con openssl
printf "blob 22\0Hello, Git internals!\n" | openssl sha1
# Output: 8ab686eafeb1f44702738c8b0f24f2567c36da6d

# Verifica con Python
python3 -c "
import hashlib
content = b'Hello, Git internals!\n'
header = f'blob {len(content)}\0'.encode()
print(hashlib.sha1(header + content).hexdigest())
"
```

### Compressione degli Oggetti

Ogni oggetto loose (non packato) è compresso con zlib prima di essere memorizzato su disco. Questo riduce significativamente lo spazio di archiviazione senza richiedere alcuna operazione esplicita da parte dell'utente.

```bash
# Verificare la compressione di un oggetto
python3 -c "
import zlib
with open('.git/objects/8a/b686eafeb1f44702738c8b0f24f2567c36da6d', 'rb') as f:
    raw = f.read()
    decompressed = zlib.decompress(raw)
    print(f'Compresso: {len(raw)} byte')
    print(f'Decompresso: {len(decompressed)} byte')
    print(f'Contenuto: {decompressed}')
"
# Output: b'blob 22\x00Hello, Git internals!\n'
```

### Deduplicazione Automatica

```bash
# Due file identici in directory diverse → stesso blob
echo "contenuto identico" > dir1/file.txt
echo "contenuto identico" > dir2/file.txt
git add dir1/file.txt dir2/file.txt

# Verifica: stesso hash blob
git ls-files -s dir1/file.txt dir2/file.txt
# 100644 abc123... 0    dir1/file.txt
# 100644 abc123... 0    dir2/file.txt  ← stesso hash
# Un solo blob memorizzato, referenziato da due tree entry
```

---

## Tree: La Struttura delle Directory

Un **tree** rappresenta una directory. Contiene una lista di entry, ognuna delle quali associa un nome file (o directory), i permessi Unix e l'hash dell'oggetto corrispondente (blob per i file, tree per le sottodirectory).

```bash
# Visualizzare il tree di un commit
git cat-file -p main^{tree}
# Output:
# 100644 blob a1b2c3d...   README.md
# 100644 blob d4e5f6g...   package.json
# 040000 tree h7i8j9k...   src
# 100755 blob l0m1n2o...   scripts/deploy.sh

# Visualizzare un tree ricorsivamente
git ls-tree -r main
# Mostra tutti i file in tutte le sottodirectory

# Visualizzare con dimensioni
git ls-tree -r -l main
# Include la dimensione di ogni blob

# Solo i nomi dei file
git ls-tree --name-only main
```

### Permessi nei Tree

Git traccia un sottoinsieme dei permessi Unix:

| Modo | Significato |
|------|-------------|
| `100644` | File regolare non eseguibile |
| `100755` | File regolare eseguibile |
| `120000` | Symbolic link |
| `040000` | Directory (tree) |
| `160000` | Gitlink (submodule) |

Git non traccia permessi più granulari (come i permessi di gruppo o altri). Sui sistemi Windows, tutti i file vengono tipicamente trattati come `100644`.

### Formato Binario del Tree

Il formato interno di un tree è binario (non testuale come commit e tag):

```
<modo> <nome>\0<20-byte SHA-1>
<modo> <nome>\0<20-byte SHA-1>
...
```

```bash
# Visualizzare il formato grezzo
python3 -c "
import zlib, os
# Trova un tree object
# Sostituire con un hash reale del proprio repository
tree_path = '.git/objects/XX/YYYYYY...'
with open(tree_path, 'rb') as f:
    data = zlib.decompress(f.read())
    # Header: 'tree <size>\0'
    # Entries: '<mode> <name>\0<20-byte-sha1>'
    print(data[:100])
"
```

### Creazione Manuale di Tree

Per scopi educativi, è possibile creare tree manualmente usando i comandi plumbing di Git:

```bash
# Aggiungere un blob all'index
git update-index --add --cacheinfo 100644 \
  8ab686eafeb1f44702738c8b0f24f2567c36da6d hello.txt

# Scrivere l'index come tree
TREE_HASH=$(git write-tree)
echo "Tree creato: $TREE_HASH"

# Leggere un tree nell'index
git read-tree --prefix=sottodirectory/ "$TREE_HASH"

# Creare un tree con più entry
git update-index --add --cacheinfo 100644 $(echo "file 1" | git hash-object -w --stdin) file1.txt
git update-index --add --cacheinfo 100644 $(echo "file 2" | git hash-object -w --stdin) file2.txt
git write-tree
```

---

## Commit: Gli Snapshot della Cronologia

Un **commit** è l'oggetto che lega tutto insieme. Contiene un riferimento al tree (lo snapshot del progetto), riferimenti ai commit parent, il nome e l'email dell'autore e del committer, i rispettivi timestamp e il messaggio di commit.

```bash
# Visualizzare il contenuto grezzo di un commit
git cat-file -p HEAD
# Output:
# tree 4b825dc642cb6eb9a060e54bf899d69f7e0e7f6c
# parent a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
# author Mario Rossi <mario@example.com> 1700000000 +0100
# committer Mario Rossi <mario@example.com> 1700000000 +0100
#
# Aggiungere funzionalità di autenticazione
```

### Struttura del Commit

```
commit <dimensione>\0
tree <hash-del-tree>
parent <hash-del-parent>          (opzionale, assente nel primo commit)
parent <hash-del-secondo-parent>  (presente nei merge commit)
author <nome> <email> <timestamp> <timezone>
committer <nome> <email> <timestamp> <timezone>
gpgsig -----BEGIN PGP SIGNATURE-----
 ...                               (opzionale, se firmato)
 -----END PGP SIGNATURE-----

<messaggio-di-commit>
```

La distinzione tra **author** e **committer** è significativa:
- L'**author** è chi ha creato le modifiche originali
- Il **committer** è chi ha applicato le modifiche al repository

Queste informazioni possono differire, ad esempio quando si applica una patch creata da qualcun altro, o dopo un rebase (il committer cambia, l'autore rimane lo stesso).

```bash
# Esempio pratico: applicare una patch da un collaboratore
git am patch-da-collaboratore.patch
# author = collaboratore originale
# committer = chi ha applicato la patch

# Dopo un rebase
git rebase main
# author = invariato (chi ha scritto il commit originale)
# committer = chi ha eseguito il rebase, con nuovo timestamp

# Visualizzare la differenza
git log --format="%H%nAuthor: %an <%ae> %ad%nCommitter: %cn <%ce> %cd%n" -1
```

### Creazione Manuale di Commit

```bash
# Creare un commit usando i comandi plumbing
echo "Messaggio di commit" | git commit-tree <hash-tree> -p <hash-parent>
# Output: hash del nuovo commit

# Primo commit (senza parent)
echo "Commit iniziale" | git commit-tree <hash-tree>

# Merge commit (due parent)
echo "Merge feature into main" | git commit-tree <hash-tree> -p <parent1> -p <parent2>

# Impostare autore diverso dal committer
GIT_AUTHOR_NAME="Alice" GIT_AUTHOR_EMAIL="alice@example.com" \
  GIT_AUTHOR_DATE="2024-01-15T10:30:00+0100" \
  echo "Commit di Alice" | git commit-tree <hash-tree> -p HEAD
```

### Merge Commit

Un merge commit è un commit con più di un parent. Il primo parent è tipicamente il branch in cui si è eseguito il merge, il secondo è il branch che è stato mergiato.

```bash
git cat-file -p <merge-commit-hash>
# tree 4b825dc...
# parent a1b2c3d...    ← primo parent (branch target)
# parent d4e5f6g...    ← secondo parent (branch mergiato)
# author ...
# committer ...
#
# Merge branch 'feature' into main

# Octopus merge (più di due parent)
# Usato per mergiare più branch simultaneamente
git merge feature1 feature2 feature3
# Crea un commit con 4 parent: HEAD + 3 branch
```

### Signed Commit

I commit possono essere firmati con GPG o SSH per verificarne l'autenticità:

```bash
# Firmare un commit
git commit -S -m "Commit firmato"

# Verificare la firma
git verify-commit HEAD
git log --show-signature -1

# Il campo gpgsig è parte del contenuto grezzo del commit
# ma NON è incluso nel calcolo dell'hash del commit
```

---

## Tag: Annotazioni Permanenti

Git supporta due tipi di tag: **lightweight** e **annotated**. Solo i tag annotated creano un oggetto tag nel database.

### Lightweight Tag

Un lightweight tag è semplicemente un riferimento (file in `.git/refs/tags/`) che punta direttamente a un commit. Non ha metadati propri.

```bash
git tag v1.0.0-rc1
# Crea solo .git/refs/tags/v1.0.0-rc1 contenente l'hash del commit

# Internamente:
cat .git/refs/tags/v1.0.0-rc1
# abc123def456...  (l'hash del commit)
```

### Annotated Tag

Un annotated tag crea un oggetto tag separato che contiene il tagger (nome, email, timestamp), un messaggio e un riferimento all'oggetto taggato (tipicamente un commit).

```bash
git tag -a v1.0.0 -m "Release versione 1.0.0"

# Visualizzare l'oggetto tag
git cat-file -p v1.0.0
# Output:
# object a1b2c3d...              ← hash del commit taggato
# type commit
# tag v1.0.0
# tagger Mario Rossi <mario@example.com> 1700000000 +0100
#
# Release versione 1.0.0

# Un tag può anche essere firmato con GPG
git tag -s v1.0.0 -m "Release firmata"
# Aggiunge una firma GPG all'oggetto tag

# Verificare un tag firmato
git verify-tag v1.0.0

# Un tag può puntare a qualsiasi tipo di oggetto (non solo commit)
# Tag su un blob (caso raro ma valido):
git tag -a special-config v1.0.0:config.yml -m "Config speciale"
# Tag su un tree:
git tag -a snapshot-tree HEAD^{tree} -m "Tree snapshot"
```

### Differenza nel Dereferenziamento

```bash
# Lightweight tag → commit direttamente
git cat-file -t v1.0.0-rc1
# commit

# Annotated tag → oggetto tag che punta al commit
git cat-file -t v1.0.0
# tag
git cat-file -p v1.0.0 | head -1
# object abc123...  (il commit)

# Dereferenziare il tag all'oggetto finale
git rev-parse v1.0.0^{}
# abc123...  (l'hash del commit)
# La sintassi ^{} "pela" i tag fino all'oggetto non-tag sottostante
```

---

## SHA-1 Hashing e Content-Addressable Storage

### Il Principio del Content-Addressable Storage

In Git, ogni oggetto è identificato dal suo contenuto attraverso un hash crittografico. Questo approccio ha diverse proprietà fondamentali:

1. **Deduplicazione automatica**: Due oggetti identici hanno lo stesso hash e vengono memorizzati una sola volta
2. **Verifica dell'integrità**: L'hash funge da checksum — qualsiasi corruzione è immediatamente rilevabile
3. **Immutabilità**: Non è possibile modificare un oggetto senza cambiarne l'hash
4. **Efficienza della rete**: Due repository possono determinare rapidamente quali oggetti mancano confrontando gli hash

### Da SHA-1 a SHA-256

Git ha storicamente usato SHA-1, un algoritmo di hash che produce valori di 160 bit (40 caratteri esadecimali). Sebbene SHA-1 sia stato dimostrato vulnerabile ad attacchi di collisione (SHAttered attack, 2017), Git implementa contromisure specifiche (hardened SHA-1) e sta gradualmente migrando a SHA-256.

```bash
# Verificare quale algoritmo di hash usa il repository
git rev-parse --show-object-format
# Output: sha1 (o sha256 per repository più recenti)

# Creare un repository con SHA-256
git init --object-format=sha256 nuovo-repo

# SHA-256 produce hash di 64 caratteri esadecimali
# Esempio: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
```

### Hardened SHA-1

Dopo l'attacco SHAttered (2017), Git ha implementato un SHA-1 "hardened" che rileva e blocca collisioni note:

```bash
# Git usa SHA-1DC (SHA-1 with collision detection)
# Se una collisione viene rilevata, l'operazione fallisce:
# fatal: SHA1 collision detected
# L'implementazione controlla i vettori di attacco SHAttered
# e produce un hash diverso (non-standard) per input malevoli

# Verifica quale implementazione SHA-1 usa la tua versione di Git
git version
# Git 2.45+ supporta SHA-256 come alternativa completa
```

### Abbreviazione degli Hash

Git permette di usare abbreviazioni degli hash, purché siano univoche nel repository:

```bash
# Trovare l'hash minimo univoco
git rev-parse --short HEAD
# Output: a1b2c3d (tipicamente 7-12 caratteri)

# Specificare la lunghezza minima
git rev-parse --short=12 HEAD

# In repository molto grandi, servono più caratteri per l'univocità
# Il kernel Linux richiede circa 12 caratteri
git config core.abbrev 12

# Calcolo probabilità collisione (Birthday Paradox)
# Per n oggetti e hash di b bit:
# P(collisione) ≈ n²/2^(b+1)
# Con 1M oggetti e abbreviazione 7 hex (28 bit):
# P ≈ 10^12 / 2^29 ≈ 1800 → quasi certa collisione
# Con abbreviazione 12 hex (48 bit):
# P ≈ 10^12 / 2^49 ≈ 0.002 → trascurabile
```

---

## Packfiles e Delta Compression

### Loose Objects vs Packed Objects

Quando Git crea nuovi oggetti, li memorizza come **loose objects** — file individuali compressi con zlib nella directory `.git/objects/`. Questo è efficiente per oggetti individuali ma inefficiente per repository con molti oggetti.

Git periodicamente "impacchetta" i loose objects in **packfiles** — file binari ottimizzati che contengono molti oggetti con delta compression.

```bash
# Visualizzare le statistiche degli oggetti
git count-objects -v
# count: 150          ← loose objects
# size: 600           ← dimensione loose objects in KiB
# in-pack: 50000      ← oggetti nei packfiles
# packs: 3            ← numero di packfiles
# size-pack: 45000    ← dimensione packfiles in KiB
# prune-packable: 0   ← loose objects che possono essere eliminati
# garbage: 0          ← file spazzatura in objects/
# size-garbage: 0

# Forzare il packing degli oggetti
git gc
# Oppure
git repack -a -d

# Visualizzare il contenuto di un packfile
git verify-pack -v .git/objects/pack/pack-abc123.idx
```

### Delta Compression

Nei packfiles, Git usa la **delta compression**: invece di memorizzare l'intero contenuto di ogni oggetto, memorizza le differenze (delta) rispetto a un oggetto base simile. Questo è particolarmente efficace per file che cambiano poco tra una versione e l'altra.

```bash
# Visualizzare i delta in un packfile
git verify-pack -v .git/objects/pack/pack-abc123.idx | head -20
# hash tipo dimensione dim-in-pack offset [depth base-hash]
# a1b2... blob 15000 4500 12345
# d4e5... blob 200   80   67890 1 a1b2...
# Il secondo blob è un delta del primo (200 byte effettivi, 80 compressi)

# Statistiche delta
git verify-pack -v .git/objects/pack/pack-abc123.idx | \
  awk '/^[0-9a-f]/ && NF==7 {depth[$7]++} END {for(d in depth) print d, depth[d]}' | sort -n
```

L'algoritmo di delta compression di Git è sofisticato:
- Cerca oggetti simili per tipo e dimensione
- Non è limitato a versioni successive dello stesso file
- Può creare catene di delta (delta di un delta) fino a una profondità configurabile
- Sceglie la base che produce il delta più piccolo

```bash
# Configurare la profondità massima dei delta
git config pack.depth 50       # Predefinito: 50

# Configurare la dimensione della finestra di ricerca
git config pack.window 250     # Predefinito: 10

# Repack aggressivo (più lento, più compresso)
git repack -a -d --depth=250 --window=250

# Dimensione massima degli oggetti da deltificare
git config pack.bigFileThreshold 512m
# Oggetti > 512 MiB non vengono usati come base per delta
```

### Formato del Packfile

Il packfile ha un formato binario specifico:

```
┌────────────────────────────────────────────────────────┐
│ PACK signature (4 byte: "PACK")                        │
│ Version (4 byte: 2)                                    │
│ Number of objects (4 byte)                             │
├────────────────────────────────────────────────────────┤
│ Object 1: [type+size varint] [data compresso zlib]     │
│ Object 2: [type+size varint] [data compresso zlib]     │
│ ...                                                    │
│ Object N: [OFS_DELTA/REF_DELTA tipo] [base] [delta]   │
├────────────────────────────────────────────────────────┤
│ SHA-1 checksum del packfile (20 byte)                  │
└────────────────────────────────────────────────────────┘
```

Tipi di entry nel packfile:
- **OBJ_COMMIT** (1), **OBJ_TREE** (2), **OBJ_BLOB** (3), **OBJ_TAG** (4): oggetti completi
- **OBJ_OFS_DELTA** (6): delta con offset nel packfile (più efficiente)
- **OBJ_REF_DELTA** (7): delta con riferimento hash (usato nella rete)

### Index del Packfile

Ogni packfile (`.pack`) ha un file indice associato (`.idx`) che permette l'accesso random veloce agli oggetti all'interno del packfile.

```bash
# Generare l'indice per un packfile
git index-pack .git/objects/pack/pack-abc123.pack

# Multi-pack index (Git 2.34+)
git multi-pack-index write
# Crea un singolo indice che copre tutti i packfiles

# Verificare l'integrità del multi-pack-index
git multi-pack-index verify

# Repack con geometric repacking (Git 2.36+)
git repack --geometric=2 -d
# Combina packfile piccoli mantenendo i grandi
# Riduce il numero di packfile senza riprocessare tutto
```

### Thin Packs e Network Transfers

Quando Git invia dati in rete (push/fetch), usa **thin packs**: packfile che contengono delta referenzianti oggetti che il ricevente dovrebbe già avere. Il ricevente poi "ingrassa" il thin pack aggiungendo le basi mancanti:

```bash
# Un thin pack durante un fetch potrebbe contenere:
# OBJ_REF_DELTA che referenziano blob già presenti nel repo locale
# Il ricevente usa git index-pack --fix-thin per risolverli

# Ispezionare un pack ricevuto dalla rete
git index-pack --fix-thin --stdin < incoming.pack
```

---

## Refs: Branch, Tag, HEAD e Riferimenti Speciali

### Anatomia dei Riferimenti

I riferimenti (refs) sono puntatori con nomi leggibili agli hash degli oggetti Git. Invece di memorizzare hash SHA-1, i riferimenti forniscono nomi stabili e significativi.

```bash
# Tutti i riferimenti vivono sotto .git/refs/
.git/refs/
├── heads/          # Branch locali
│   ├── main        # Contiene: hash del commit più recente di main
│   ├── develop
│   └── feature/auth
├── remotes/        # Branch remoti (tracking)
│   └── origin/
│       ├── main
│       └── develop
├── tags/           # Tag
│   ├── v1.0.0
│   └── v2.0.0
└── stash           # Ultimo stash
```

### Packed Refs

Quando un repository ha molti riferimenti, Git li consolida in un file unico `.git/packed-refs` per efficienza:

```bash
# Contenuto di .git/packed-refs
cat .git/packed-refs
# # pack-refs with: peeled fully-peeled sorted
# abc123def456 refs/heads/main
# def456abc789 refs/heads/develop
# 111222333444 refs/tags/v1.0.0
# ^aaa111bbb222  ← "peeled" tag (l'oggetto commit puntato dal tag)

# Quando un ref esiste sia come file che in packed-refs,
# il file ha precedenza (è più recente)

# Forzare il packing dei riferimenti
git pack-refs --all
```

### Manipolazione dei Riferimenti

```bash
# Aggiornare un riferimento
git update-ref refs/heads/main abc1234

# Aggiornamento condizionale (Compare-and-Swap)
git update-ref refs/heads/main <nuovo-hash> <hash-atteso>
# Fallisce se il ref non punta a <hash-atteso>
# Essenziale per operazioni concorrenti sicure

# Eliminare un riferimento
git update-ref -d refs/heads/branch-da-rimuovere

# Listare tutti i riferimenti
git for-each-ref
# Formattazione personalizzata
git for-each-ref --format='%(refname:short) %(objecttype) %(objectname:short) %(creatordate:iso)' refs/heads/

# Riferimenti simbolici
git symbolic-ref HEAD
# Output: refs/heads/main

git symbolic-ref HEAD refs/heads/develop
# Cambia il branch corrente a develop (senza checkout)
```

### Riferimenti Speciali

Git mantiene diversi riferimenti speciali nella root di `.git/`:

| Riferimento | Descrizione | Quando Esiste |
|-------------|-------------|---------------|
| `HEAD` | Branch o commit corrente | Sempre |
| `ORIG_HEAD` | HEAD prima di merge/rebase/reset | Dopo operazioni "pericolose" |
| `FETCH_HEAD` | Risultato dell'ultimo fetch | Dopo git fetch |
| `MERGE_HEAD` | Commit in fase di merge | Durante un merge |
| `CHERRY_PICK_HEAD` | Commit in fase di cherry-pick | Durante un cherry-pick |
| `REVERT_HEAD` | Commit in fase di revert | Durante un revert |
| `BISECT_HEAD` | Commit corrente durante bisect | Durante git bisect |

### Detached HEAD

Quando HEAD punta direttamente a un commit invece che a un branch, si è in stato "detached HEAD":

```bash
# HEAD normalmente è un symbolic ref
cat .git/HEAD
# ref: refs/heads/main

# Detached HEAD
git checkout abc1234
cat .git/HEAD
# abc1234def456...  (hash diretto, non un ref)

# I commit fatti in detached HEAD diventano orfani
# quando si fa checkout di un branch diverso
# Recuperabili via reflog finché non scadono
```

### Ref Specifications

Le refspec definiscono la mappatura tra riferimenti locali e remoti. Sono usate nei comandi fetch e push.

```bash
# Formato: +<src>:<dst>
# Il + significa force update

# Fetch refspec tipica (in .git/config)
[remote "origin"]
    fetch = +refs/heads/*:refs/remotes/origin/*

# Push refspec
git push origin main:main
# Pusha il branch locale main al branch remoto main

# Fetch di un singolo branch
git fetch origin +refs/heads/feature:refs/remotes/origin/feature

# Fetch dei pull request di GitHub
git fetch origin +refs/pull/*/head:refs/remotes/origin/pr/*
# Permette di fare checkout delle PR come branch locali
git checkout pr/42

# Fetch delle merge ref di GitHub (risultato del merge test)
git fetch origin +refs/pull/*/merge:refs/remotes/origin/pr-merge/*

# Push con refspec per creare un branch remoto con nome diverso
git push origin local-branch:remote-name

# Delete un branch remoto via refspec vuota
git push origin :branch-da-eliminare
# Equivale a: git push origin --delete branch-da-eliminare

# Refspec per fetch selettivo (partial clone)
git clone --filter=blob:none --single-branch --branch main <url>
# Fetch solo i commit e tree, blob scaricati on-demand
```

---

## Reflog: La Rete di Sicurezza

### Cos'è il Reflog

Il reflog registra ogni modifica ai riferimenti locali (branch e HEAD). È la rete di sicurezza definitiva di Git: anche quando un commit sembra "perso" (dopo un reset hard, un rebase o un branch eliminato), il reflog lo conserva per un periodo configurabile.

```bash
# Visualizzare il reflog di HEAD
git reflog
# a1b2c3d HEAD@{0}: commit: Aggiornare il README
# d4e5f6g HEAD@{1}: checkout: moving from feature to main
# h7i8j9k HEAD@{2}: commit: Implementare login
# l0m1n2o HEAD@{3}: rebase (finish): returning to refs/heads/feature

# Reflog di un branch specifico
git reflog show main

# Reflog con date
git reflog --date=iso
# a1b2c3d HEAD@{2024-01-15 10:30:00 +0100}: commit: ...

# Reflog con relative date
git reflog --date=relative
# a1b2c3d HEAD@{2 hours ago}: commit: ...

# Contare le entry nel reflog
git reflog | wc -l
```

### Formato Interno del Reflog

```bash
# Il reflog è memorizzato in file di testo sotto .git/logs/
cat .git/logs/HEAD
# old-sha new-sha Name <email> timestamp timezone\taction: details

# Esempio:
# 0000000 abc1234 Mario <m@ex.com> 1700000000 +0100  commit (initial): first commit
# abc1234 def5678 Mario <m@ex.com> 1700001000 +0100  commit: second commit

# Reflog per branch
cat .git/logs/refs/heads/main
```

### Recupero con il Reflog

```bash
# Recuperare un commit dopo un reset --hard
git reset --hard HEAD~3    # Oops, persi 3 commit!
git reflog                  # Trovare l'hash del commit perso
git reset --hard HEAD@{1}  # Tornare allo stato precedente

# Recuperare un branch eliminato
git branch -D feature-importante    # Oops!
git reflog                            # Trovare l'ultimo commit del branch
git checkout -b feature-importante HEAD@{5}

# Recuperare dopo un rebase andato male
git reflog
# Trovare il commit prima del rebase (tipicamente "rebase (start)")
git reset --hard HEAD@{n}

# Recuperare un file specifico da un reflog entry
git show HEAD@{3}:path/to/file.txt > file_recuperato.txt

# Recuperare usando il reflog di un branch specifico
git reflog show feature
git checkout -b feature-recovered feature@{2}
```

### Reflog e Stash

```bash
# Ogni stash crea entry nel reflog di refs/stash
git reflog show stash
# abc123 stash@{0}: WIP on main: abc123 fix bug
# def456 stash@{1}: On develop: save work

# Se lo stash è stato droppato, si può recuperare via reflog
git stash drop stash@{0}
git fsck --unreachable | grep commit
# Trovare il commit dello stash tra gli unreachable
git stash apply <hash-commit-stash>
```

### Configurazione del Reflog

```bash
# Durata di conservazione dei reflog (predefinito: 90 giorni)
git config gc.reflogExpire 180.days

# Durata per reflog di commit non raggiungibili (predefinito: 30 giorni)
git config gc.reflogExpireUnreachable 60.days

# Disabilitare la scadenza del reflog
git config gc.reflogExpire never

# Scadenza per branch specifico
git config gc.refs/heads/main.reflogExpire never
# Il reflog di main non scade mai
```

---

## Garbage Collection

### Come Funziona la Garbage Collection

La garbage collection (GC) di Git rimuove gli oggetti non raggiungibili dal database e ottimizza il repository comprimendo i loose objects in packfiles.

Un oggetto è considerato **non raggiungibile** se nessun riferimento (branch, tag, reflog) lo punta direttamente o indirettamente. Questo include commit orfani (dopo un rebase o reset), blob mai committati e tree non referenziati.

```bash
# Eseguire la garbage collection
git gc

# GC aggressiva (più lenta, migliore compressione)
git gc --aggressive

# GC con pruning immediato (ATTENZIONE: rimuove oggetti non raggiungibili)
git gc --prune=now

# Visualizzare cosa verrebbe rimosso
git fsck --unreachable
git prune --dry-run

# GC automatica (verifica se necessaria, poi esegue)
git gc --auto
```

### Pipeline della GC

La GC esegue internamente diversi passaggi:

```bash
# 1. Pack dei loose objects
git repack -a -d
# Combina tutti i loose objects in un packfile

# 2. Rimozione dei loose objects ridondanti
git prune-packed
# Rimuove loose objects che esistono già nei packfile

# 3. Rimozione degli oggetti non raggiungibili scaduti
git prune --expire=2.weeks.ago
# Rimuove oggetti non raggiungibili creati più di 2 settimane fa

# 4. Pack dei riferimenti
git pack-refs --all
# Consolida i file ref in packed-refs

# 5. Pulizia reflog
git reflog expire --expire=90.days --all
# Rimuove entry del reflog più vecchie di 90 giorni

# 6. Scrittura commit-graph (se abilitato)
git commit-graph write --reachable
```

### Tempistiche della GC

Git esegue la GC automaticamente in determinate condizioni:

```bash
# Numero di loose objects che attivano la GC automatica (predefinito: 6700)
git config gc.auto 6700

# Numero di packfiles che attivano il repack automatico (predefinito: 50)
git config gc.autoPackLimit 50

# Disabilitare la GC automatica
git config gc.auto 0

# Durata prima del pruning degli oggetti non raggiungibili (predefinito: 2 settimane)
git config gc.pruneExpire 2.weeks.ago

# Durata prima di scadere i reflog unreachable (predefinito: 30 giorni)
git config gc.reflogExpireUnreachable 30.days

# Durata prima di scadere i reflog reachable (predefinito: 90 giorni)
git config gc.reflogExpire 90.days
```

### Protezione degli Oggetti

Gli oggetti sono protetti dalla GC finché sono raggiungibili da:
- Qualsiasi branch (locale o remoto)
- Qualsiasi tag
- Entry nel reflog
- L'index (staging area)
- Commit in fase di cherry-pick, merge, rebase
- File in `.git/shallow`
- Worktree aggiuntivi

```bash
# Forzare Git a mantenere un oggetto specifico
# Creare un tag (anche leggero) è sufficiente
git tag keep-this abc1234

# Oppure creare un branch
git branch salvataggio abc1234

# Oppure creare un ref custom
git update-ref refs/keep/important-commit abc1234
```

### GC su Server e Repository Condivisi

```bash
# Su server Git (bare repo), la GC è critica per le performance
# Configurazione tipica per un server con molti push:
git config gc.auto 256            # GC automatica più frequente
git config gc.autoPackLimit 10    # Repack con meno packfile
git config gc.bigPackThreshold 256m  # Non riprocessare pack grandi
git config gc.writeCommitGraph true  # Aggiornare il commit-graph

# Maintenance schedulata (Git 2.30+)
git maintenance register
git maintenance start
# Esegue GC, prefetch, commit-graph, loose-objects in background
# via cron job automatico
```

---

## Index e Staging Area Internals

### La Struttura dell'Index

L'**index** (o staging area, o cache) è un file binario (`.git/index`) che funge da area intermedia tra il working tree e il repository. Contiene una lista ordinata di path con i loro metadata (permessi, timestamp, dimensione, hash del blob).

```bash
# Visualizzare il contenuto dell'index
git ls-files --stage
# 100644 a1b2c3d... 0    README.md
# 100644 d4e5f6g... 0    src/app.js
# 100644 h7i8j9k... 0    src/utils.js

# Il numero dopo l'hash è lo "stage number":
# 0 = normale
# 1 = antenato comune (durante un conflitto)
# 2 = nostro (HEAD/ours)
# 3 = loro (branch in merge/theirs)

# Visualizzare l'index con dettagli stat()
git ls-files --debug
```

### L'Index durante i Conflitti

Durante un merge con conflitti, l'index contiene fino a tre versioni di ogni file in conflitto:

```bash
# Durante un conflitto
git ls-files -u  # Mostra solo i file unmerged
# 100644 base... 1    src/app.js    ← versione dell'antenato comune
# 100644 ours... 2    src/app.js    ← nostra versione (HEAD)
# 100644 thrs... 3    src/app.js    ← loro versione (branch mergiato)

# Estrarre una versione specifica
git show :1:src/app.js > app-base.js     # Antenato comune
git show :2:src/app.js > app-ours.js     # Nostra versione
git show :3:src/app.js > app-theirs.js   # Loro versione

# Risolvere il conflitto per un singolo file con ours/theirs
git checkout --ours src/app.js
# oppure
git checkout --theirs src/app.js
# poi
git add src/app.js  # Rimuove le entry stage 1/2/3, scrive stage 0
```

### Operazioni sull'Index

```bash
# Aggiungere un file all'index
git update-index --add --cacheinfo 100644 <hash> <path>

# Rimuovere un file dall'index
git update-index --force-remove <path>

# Marcare un file come "assume-unchanged" (skip nei diff)
git update-index --assume-unchanged <path>

# Rimuovere il flag assume-unchanged
git update-index --no-assume-unchanged <path>

# Marcare un file come "skip-worktree" (più robusto di assume-unchanged)
git update-index --skip-worktree <path>

# Visualizzare i file con flag speciali
git ls-files -v
# h = assume-unchanged
# S = skip-worktree
# H = cached (normale)

# Listare tutti i file assume-unchanged
git ls-files -v | grep '^h'

# Listare tutti i file skip-worktree
git ls-files -v | grep '^S'
```

### assume-unchanged vs skip-worktree

```bash
# assume-unchanged:
# - Dice a Git "non controllare questo file per modifiche"
# - Performance optimization (evita stat() costose)
# - Git PUÒ comunque resettare il flag (es. durante un merge)
# - Uso: file grandi che non cambiano spesso

# skip-worktree:
# - Dice a Git "ignora questo file anche se è modificato"
# - Semantica più forte, il flag non viene mai resettato automaticamente
# - Uso: file di configurazione locale, .env con override locali
# - Sopravvive a checkout, pull, merge

# Esempio pratico:
# Config con credenziali locali che non vanno committate
git update-index --skip-worktree config/database.yml
# Modifica database.yml localmente
# git status non lo mostra come modificato
```

### Formato Binario dell'Index (gitformat-index)

Il file `.git/index` ha un formato binario specifico con header, entry, estensioni opzionali e un checksum:

```bash
# Struttura del file index:
# ┌──────────────────────────────────────────────────────────┐
# │ Header (12 byte)                                          │
# │   - Signature: "DIRC" (4 byte)                           │
# │   - Version: 2, 3 o 4 (4 byte, network byte order)       │
# │   - Numero di entry (4 byte, network byte order)          │
# ├──────────────────────────────────────────────────────────┤
# │ Entry 1 (dimensione variabile, minimo 62 byte)            │
# │   - ctime seconds (4 byte) + nanoseconds (4 byte)         │
# │   - mtime seconds (4 byte) + nanoseconds (4 byte)         │
# │   - dev (4 byte)                                          │
# │   - ino (4 byte)                                          │
# │   - mode (4 byte): permessi del file                      │
# │   - uid (4 byte)                                          │
# │   - gid (4 byte)                                          │
# │   - file size (4 byte)                                     │
# │   - SHA-1 dell'oggetto blob (20 byte)                     │
# │   - flags (2 byte): assume-valid, stage, name length      │
# │   - extended flags (2 byte, se version >= 3)               │
# │   - entry path name (variabile, null-terminated)           │
# │   - padding a multiplo di 8 byte (version 2/3)            │
# ├──────────────────────────────────────────────────────────┤
# │ Entry 2 ... Entry N (ordinate per path name)              │
# ├──────────────────────────────────────────────────────────┤
# │ Extensions (opzionali, dimensione variabile)               │
# │   - Ogni estensione: signature(4) + size(4) + data        │
# ├──────────────────────────────────────────────────────────┤
# │ SHA-1 checksum dell'intero contenuto precedente (20 byte) │
# └──────────────────────────────────────────────────────────┘

# Ispezionare il formato dell'index:
git ls-files --debug | head -30
# Mostra i campi stat() per ogni entry

# Version 4 dell'index:
# Usa prefix compression per i path name (come reftable)
# Path consecutivi condividono prefissi → risparmio ~25% di spazio
git update-index --index-version 4
```

### Estensioni dell'Index

L'index supporta diverse estensioni opzionali che migliorano le performance:

```bash
# Estensioni principali:

# TREE: cache dei tree corrispondenti alle directory
# Accelera git write-tree: non deve ricalcolare i tree
# Signature: { 'T', 'R', 'E', 'E' }
# Contiene: path, entry count, subtree count, SHA-1 del tree

# REUC: Resolve Undo — salva le versioni di conflitto dopo risoluzione
# Signature: { 'R', 'E', 'U', 'C' }
# Permette di ripristinare un conflitto risolto con:
git checkout -m path/to/file  # Ri-crea il conflitto

# UNTR: Untracked cache — cache dei file non tracciati
# Signature: { 'U', 'N', 'T', 'R' }
# Accelera git status evitando di scandire directory invariate
git config core.untrackedCache true

# EOIE: End of Index Entry — offset della fine delle entry
# Permette il parsing parallelo delle entry e delle estensioni

# IEOT: Index Entry Offset Table — tabella degli offset delle entry
# Signature: { 'I', 'E', 'O', 'T' }
# Permette il parsing multi-thread dell'index
git config index.threads true  # Abilita il parsing parallelo

# sdir: Sparse Directory entry (per sparse index)
# Indica che una entry rappresenta una directory collassata

# Verificare la versione e le estensioni dell'index:
python3 -c "
import struct
with open('.git/index', 'rb') as f:
    sig = f.read(4)
    ver = struct.unpack('>I', f.read(4))[0]
    entries = struct.unpack('>I', f.read(4))[0]
    print(f'Signature: {sig}')
    print(f'Version: {ver}')
    print(f'Entries: {entries}')
"
```

### Split Index

Per repository di grandi dimensioni, Git supporta lo split index, che divide l'index in una parte condivisa e una parte con le modifiche recenti:

```bash
# Abilitare lo split index
git update-index --split-index

# Configurare la percentuale di modifiche prima di riscrivere l'index condiviso
git config splitIndex.maxPercentChange 20

# Formato:
# .git/index → piccolo, contiene solo i delta
# .git/sharedindex.xxxx → grande, condiviso, read-only
# Migliora le performance di git status su repository con >100k file
```

---

## Transfer Protocols

Git supporta diversi protocolli per il trasferimento degli oggetti tra repository. Comprendere questi protocolli è fondamentale per diagnosticare problemi di rete, ottimizzare le performance dei trasferimenti e configurare server Git personalizzati.

### Protocolli Disponibili

| Protocollo | URL Formato | Porta | Autenticazione | Performance |
|-----------|------------|-------|----------------|-------------|
| Smart HTTP | `https://host/repo.git` | 443 | Qualsiasi (Basic, SAML, OAuth) | Buona |
| SSH | `git@host:repo.git` | 22 | Chiave SSH | Eccellente |
| Git Protocol | `git://host/repo.git` | 9418 | Nessuna | Eccellente |
| Dumb HTTP | `http://host/repo.git` | 80 | Basic/nessuna | Scarsa |
| File | `/path/to/repo.git` | — | Filesystem | Locale |

### Smart HTTP Protocol

Il protocollo Smart HTTP è il più utilizzato (GitHub, GitLab, Bitbucket lo usano di default). Opera tramite due endpoint:

```bash
# Discovery: il client chiede le capability e i riferimenti
# GET /repo.git/info/refs?service=git-upload-pack
# Il server risponde con:
# - Le proprie capability (multi_ack, side-band-64k, thin-pack, ...)
# - La lista dei riferimenti con i rispettivi hash

# Esempio di risposta discovery (formato pkt-line):
# 001e# service=git-upload-pack\n
# 0000
# 00abHASH HEAD\0multi_ack thin-pack side-band side-band-64k ofs-delta ...
# 003fHASH refs/heads/main
# 003fHASH refs/heads/develop
# 0000

# Upload (fetch): il client invia i "want" e i "have"
# POST /repo.git/git-upload-pack
# Content-Type: application/x-git-upload-pack-request
# Body:
# 0032want HASH capability-list
# 0032want HASH
# 0000
# 0032have HASH
# 0032have HASH
# 0000
# 0009done

# Il server risponde con un packfile contenente gli oggetti mancanti

# Receive (push): il client invia gli aggiornamenti e il packfile
# POST /repo.git/git-receive-pack
# Content-Type: application/x-git-receive-pack-request
```

### Formato pkt-line

Git usa il formato **pkt-line** per la comunicazione di protocollo. Ogni riga è preceduta da 4 byte esadecimali che indicano la lunghezza totale della riga (inclusi i 4 byte stessi):

```bash
# Formato: LLLL<payload>
# LLLL = lunghezza in hex, incluso LLLL stesso
# 0000 = flush-pkt (separatore)

# Esempio:
# 0006a\n   → 6 byte totali: "0006" + "a\n"
# 0000      → flush

# Decodificare pkt-line manualmente (debug):
GIT_CURL_VERBOSE=1 git fetch 2>&1 | head -50

# Git Protocol v2 (più efficiente):
# Il client può filtrare i ref richiesti lato server
git -c protocol.version=2 fetch origin main
# Solo i ref matching vengono inviati (risparmia bandwidth su repo con migliaia di branch)

# Verificare quale versione del protocollo viene usata
GIT_TRACE_PACKET=1 git fetch 2>&1 | head -20
```

### SSH Protocol

SSH è il protocollo preferito per repository privati. Git esegue `git-upload-pack` o `git-receive-pack` direttamente sul server remoto:

```bash
# Il flusso SSH:
# 1. Il client apre una connessione SSH al server
# 2. Esegue: ssh git@host "git-upload-pack '/path/to/repo.git'"
# 3. Da qui in poi, il protocollo è identico al Git Protocol (pkt-line)

# Debugging SSH
GIT_SSH_COMMAND="ssh -v" git fetch origin

# Specificare una chiave SSH diversa
GIT_SSH_COMMAND="ssh -i ~/.ssh/deploy_key" git clone git@github.com:org/repo.git

# Configurare SSH multiplexing per performance
# ~/.ssh/config
# Host github.com
#     ControlMaster auto
#     ControlPath ~/.ssh/sockets/%r@%h-%p
#     ControlPersist 600

# SSH con porta non-standard
git clone ssh://git@host:2222/repo.git
```

### Git Protocol (Native)

Il protocollo nativo `git://` è il più semplice e veloce, ma non ha autenticazione né crittografia. Usato tipicamente per mirror pubblici di sola lettura:

```bash
# Il server ascolta sulla porta 9418
# Avviare un server Git Protocol:
git daemon --reuseaddr --base-path=/srv/git/ /srv/git/

# Il protocollo è identico a Smart HTTP nella fase di negoziazione
# ma senza overhead HTTP

# Abilitare l'export di un repository
touch /srv/git/repo.git/git-daemon-export-ok

# Limitare a sola lettura (predefinito):
# git daemon serve git-upload-pack ma NON git-receive-pack
```

### Dumb HTTP Protocol (Legacy)

Il protocollo "Dumb HTTP" è il più vecchio e meno efficiente. Non ha negoziazione — il client scarica file statici:

```bash
# Il client scarica oggetti uno alla volta:
# 1. GET /repo.git/info/refs → lista dei riferimenti (testo statico)
# 2. GET /repo.git/HEAD → il branch corrente
# 3. Per ogni oggetto necessario:
#    GET /repo.git/objects/ab/cdef123456... → oggetto loose
#    oppure
#    GET /repo.git/objects/info/packs → lista dei packfile
#    GET /repo.git/objects/pack/pack-xxx.idx → indice
#    GET /repo.git/objects/pack/pack-xxx.pack → packfile

# Nessuna negoziazione → scarica potenzialmente molti più dati del necessario

# Preparare un repository per Dumb HTTP:
git update-server-info
# Aggiorna info/refs e objects/info/packs
# Va eseguito come hook post-receive sul server

# Post-receive hook per Dumb HTTP:
#!/bin/bash
git update-server-info
```

### Negoziazione: "Want" e "Have"

Il cuore del protocollo di trasferimento è la negoziazione tra client e server per determinare quali oggetti devono essere trasferiti:

```bash
# FETCH (git-upload-pack):
# 1. Server invia lista ref → client vede cosa ha il server
# 2. Client invia "want" → hash degli oggetti desiderati
# 3. Client invia "have" → hash degli oggetti già posseduti
# 4. Server calcola il set minimo di oggetti da inviare
# 5. Server invia un packfile con gli oggetti mancanti

# PUSH (git-receive-pack):
# 1. Server invia lista ref → client vede lo stato corrente
# 2. Client invia update commands: "old-hash new-hash refname"
# 3. Client invia un packfile con gli oggetti necessari
# 4. Server esegue gli hook (pre-receive, update, post-receive)
# 5. Server aggiorna i riferimenti

# Capability: multi_ack
# Permette negoziazione iterativa — il server conferma quali "have"
# corrispondono a oggetti noti, permettendo al client di raffinare
# la lista. Riduce significativamente la dimensione del packfile.

# Capability: shallow
# Supporta clone/fetch parziali (--depth N)
# Il client può richiedere solo gli ultimi N commit

# Visualizzare la negoziazione
GIT_TRACE_PACKET=1 git fetch origin 2>&1 | grep -E "want|have|done|ACK"
```

### Protocol v2

Git Protocol v2 (introdotto in Git 2.18) migliora l'efficienza della negoziazione:

```bash
# Differenze chiave rispetto a v1:
# 1. Server-side filtering dei ref (il client chiede solo ref specifici)
# 2. Protocollo basato su capability advertisement migliorato
# 3. Supporto per comandi estensibili (ls-refs, fetch, server-option)

# Abilitare Protocol v2 (predefinito da Git 2.26+)
git config protocol.version 2

# Forzare v2 per un singolo comando
git -c protocol.version=2 fetch origin

# Benefici per repository grandi:
# Un repository con 100.000 branch in v1 invia TUTTI i ref al discovery
# In v2, il client può chiedere solo "refs/heads/main" → enormemente più veloce

# Esempio di ls-refs in v2
GIT_TRACE_PACKET=1 git -c protocol.version=2 ls-remote origin 2>&1 | head -30
```

### Partial Clone e Promisor Packs

Git 2.19+ supporta **partial clone**: il client può richiedere solo un sottoinsieme degli oggetti, scaricando il resto on-demand:

```bash
# Clone senza blob (scaricati on-demand al checkout)
git clone --filter=blob:none https://github.com/org/repo.git

# Clone senza blob grandi (solo blob < 1 MiB)
git clone --filter=blob:limit=1m https://github.com/org/repo.git

# Clone senza tree (solo commit, tree e blob scaricati on-demand)
git clone --filter=tree:0 https://github.com/org/repo.git

# Il remote che ha fornito il partial clone è un "promisor remote"
# Git lo contatta automaticamente quando serve un oggetto mancante

# Verificare lo stato di un partial clone
git config remote.origin.promisor  # true
git config remote.origin.partialclonefilter  # blob:none

# Prefetch selettivo
git fetch --filter=blob:none origin

# Disabilitare il download on-demand (per lavoro offline)
git config remote.origin.promisor false
```

---

## Git Fsck: Verifica dell'Integrità e Recovery Avanzato

### Cos'è Git Fsck

Il comando `git fsck` (filesystem check) verifica l'integrità del database degli oggetti Git, identificando oggetti corrotti, riferimenti rotti e oggetti non raggiungibili.

```bash
# Verifica base dell'integrità
git fsck
# Checking object directories: 100% (256/256), done.
# Checking objects: 100% (15234/15234), done.

# Verifica completa con oggetti non raggiungibili
git fsck --unreachable
# unreachable blob a1b2c3d...
# unreachable commit d4e5f6g...

# Verifica con connettività completa
git fsck --full
# Verifica anche i packfiles (più lento)

# Solo errori, senza oggetti non raggiungibili
git fsck --no-dangling

# Verifica in modalità strict
git fsck --strict
# Controlla anche che gli oggetti siano nel formato corretto
# Rileva problemi di formato che --full non trova

# Verifica connettività (più veloce di fsck --full)
git fsck --connectivity-only
# Non verifica i blob, solo la connettività del grafo commit→tree
```

### Tipi di Problemi Rilevati da Fsck

```bash
# 1. Oggetti corrotti
# error: sha1 mismatch abc1234...
# → Il contenuto dell'oggetto non corrisponde al suo hash

# 2. Oggetti mancanti (missing)
# error: unable to find abc1234...
# broken link from tree def5678... to blob abc1234...
# → Un tree referenzia un blob che non esiste

# 3. Oggetti dangling (orfani ma non corrotti)
# dangling commit abc1234...
# dangling blob def5678...
# → Oggetti non raggiungibili da nessun ref (normali dopo rebase/reset)

# 4. Problemi di formato
# error: bad date in commit abc1234...
# error: invalid author/committer line in commit abc1234...
# → Il formato interno dell'oggetto non è valido

# 5. Oggetti duplicati
# warning: refname refs/heads/test is not well-formed
# → Problemi con i nomi dei riferimenti

# Elencare solo i problemi reali (non i dangling):
git fsck --no-dangling --no-progress 2>&1 | grep -v "^Checking"
```

### Recovery Avanzato di Oggetti Corrotti

```bash
# Scenario 1: loose object corrotto, ma esiste nel packfile di un remote
git fsck 2>&1 | grep "corrupt"
# error: sha1 mismatch in objects/ab/cdef123456...

# Passo 1: rimuovere l'oggetto corrotto
rm .git/objects/ab/cdef123456...

# Passo 2: recuperare dal remote
git fetch origin
# Git scarica gli oggetti mancanti

# Passo 3: verificare
git fsck

# Scenario 2: packfile corrotto
# error: packfile .git/objects/pack/pack-xxx.pack does not match index

# Passo 1: verificare il packfile
git verify-pack -v .git/objects/pack/pack-xxx.idx 2>&1 | tail -5

# Passo 2: se l'indice è corrotto ma il pack è integro
rm .git/objects/pack/pack-xxx.idx
git index-pack .git/objects/pack/pack-xxx.pack

# Passo 3: se il pack è corrotto, recuperare gli oggetti salvabili
git unpack-objects --recover < .git/objects/pack/pack-xxx.pack

# Scenario 3: HEAD o branch corrotto
cat .git/HEAD
# Se vuoto o corrotto:
echo "ref: refs/heads/main" > .git/HEAD

cat .git/refs/heads/main
# Se vuoto o corrotto, recuperare da reflog:
git reflog show main 2>/dev/null || \
  cat .git/logs/refs/heads/main | tail -1 | awk '{print $2}'
```

### Trovare e Recuperare Oggetti Persi

```bash
# Trovare commit "dangling" (orfani)
git fsck --lost-found
# I commit e i blob trovati vengono salvati in .git/lost-found/
# .git/lost-found/commit/ → commit orfani
# .git/lost-found/other/  → blob e tree orfani

# Esaminare i commit trovati
ls .git/lost-found/commit/
git show <hash-trovato>

# Recuperare un commit trovato
git branch recuperato <hash-commit-trovato>

# Script di recovery: trovare e mostrare tutti i commit persi
git fsck --unreachable --no-reflogs | grep "unreachable commit" | \
  awk '{print $3}' | while read hash; do
    echo "=== Commit $hash ==="
    git log --oneline --no-walk "$hash" 2>/dev/null
done

# Cercare un commit perso per contenuto del messaggio
git fsck --unreachable | grep "unreachable commit" | \
  awk '{print $3}' | xargs git log --oneline --no-walk 2>/dev/null | \
  grep "parola chiave"

# Cercare un blob perso per contenuto
git fsck --unreachable | grep "unreachable blob" | \
  awk '{print $3}' | while read hash; do
    if git cat-file -p "$hash" 2>/dev/null | grep -q "stringa cercata"; then
        echo "Trovato in blob $hash"
        git cat-file -p "$hash"
    fi
done
```

### Recovery da Disco Corrotto

```bash
# Scenario: corruzione hardware, filesystem journal crash

# Passo 1: backup dello stato attuale (anche se corrotto)
cp -a .git .git-backup-$(date +%Y%m%d)

# Passo 2: identificare il danno
git fsck --full 2>&1 | tee fsck-report.txt

# Passo 3: rimuovere oggetti corrotti (loose)
grep "corrupt\|sha1 mismatch" fsck-report.txt | \
  grep -oP '[0-9a-f]{40}' | while read hash; do
    dir=$(echo "$hash" | cut -c1-2)
    file=$(echo "$hash" | cut -c3-)
    rm -f ".git/objects/$dir/$file"
done

# Passo 4: ricostruire dal remote
git fetch --all

# Passo 5: verificare
git fsck --full

# Passo 6: se il remote non ha tutto (es. branch locali non pushati):
# Provare a recuperare da reflog e lost-found
git fsck --lost-found
# Esaminare .git/lost-found/commit/ per i commit mancanti

# Passo 7: reclonare come ultima risorsa
# Ma prima salvare:
# - .git/config (configurazione locale)
# - .git/hooks/ (hook personalizzati)
# - working tree modifiche non committate
git stash 2>/dev/null  # se possibile
git diff > unsaved-changes.patch 2>/dev/null
```

---

## Grafting, Replace e Shallow Clone

### Graft Points

I graft points permettono di modificare la parentela apparente dei commit senza riscrivere la cronologia:

```bash
# File: .git/info/grafts (deprecato, usare replace)
# Formato: <commit-hash> <parent1-hash> <parent2-hash> ...

# Esempio: rendere orfano un commit (rimuovere il parent)
echo "abc123" > .git/info/grafts
# Il commit abc123 ora appare come root commit

# Rendere permanente un graft
git filter-branch --tag-name-filter cat -- --all
# Riscrive la cronologia incorporando i graft
```

### Git Replace

`git replace` è il successore moderno dei graft:

```bash
# Sostituire un commit con un altro
git replace <commit-da-sostituire> <commit-sostituto>

# Uso tipico: unire due repository preservando la cronologia
# Il progetto ha una cronologia vecchia in repo-old e nuova in repo-new
# 1. Importare gli oggetti del vecchio repo
git fetch /path/to/repo-old main:refs/old-main

# 2. Trovare il commit "ponte" e il commit "base"
# ponte = primo commit del nuovo repo
# base = ultimo commit del vecchio repo
PONTE=$(git rev-list --reverse main | head -1)
BASE=$(git rev-list refs/old-main | head -1)

# 3. Creare un commit sostitutivo con il parent corretto
git replace --graft "$PONTE" "$BASE"

# Ora git log mostra la cronologia unificata
git log --oneline

# Verificare i replace attivi
git replace -l

# Rimuovere un replace
git replace -d <hash>

# I replace sono memorizzati in refs/replace/
ls .git/refs/replace/
```

### Shallow Clone

Un shallow clone scarica solo gli ultimi N commit, riducendo drasticamente la dimensione:

```bash
# Clone con profondità limitata
git clone --depth 1 https://github.com/org/repo.git
# Scarica solo l'ultimo commit

# Lo stato shallow è registrato in .git/shallow
cat .git/shallow
# abc123def456... ← gli hash dei commit "boundary" (ultimi scaricati)

# I commit boundary non hanno parent (appaiono come root commit)
git log --oneline
# abc123 (HEAD -> main) Latest commit
# def456 Second to last
# Nessun commit più vecchio disponibile

# "Deepen" la cronologia
git fetch --deepen=10
# Scarica altri 10 commit

# Rendere il clone completo (unshallow)
git fetch --unshallow

# Shallow clone per CI/CD (velocità massima)
git clone --depth 1 --single-branch --branch main <url>
# Scarica solo l'ultimo commit del branch main
```

---

## Worktrees e Internals Multi-Working-Tree

### Cos'è un Worktree

Git 2.5+ supporta **multiple working trees** collegati allo stesso repository. Utile per lavorare su più branch simultaneamente senza clonare:

```bash
# Creare un worktree aggiuntivo
git worktree add ../feature-branch feature
# Crea una directory ../feature-branch con il checkout di "feature"

# Listare i worktree
git worktree list
# /home/user/project        abc1234 [main]
# /home/user/feature-branch def5678 [feature]

# Rimuovere un worktree
git worktree remove ../feature-branch

# Worktree con branch temporaneo
git worktree add --detach ../hotfix HEAD
```

### Internals dei Worktree

```bash
# I worktree condividono lo stesso .git/objects/ e .git/refs/
# Ogni worktree ha il proprio:
# - HEAD
# - index
# - working tree

# La directory .git del worktree secondario è un file:
cat ../feature-branch/.git
# gitdir: /home/user/project/.git/worktrees/feature-branch

# Metadata del worktree nel repository principale:
ls .git/worktrees/feature-branch/
# HEAD        ← branch checkout in questo worktree
# index       ← staging area separata
# gitdir      ← percorso al working tree
# commondir   ← percorso alla directory .git condivisa

# Constraint: non è possibile avere lo stesso branch
# checked out in due worktree contemporaneamente
git worktree add ../test main
# fatal: 'main' is already checked out at '/home/user/project'
```

---

## Commit Graph e Bloom Filter

### Commit-Graph File

Il commit-graph è un file binario opzionale che accelera le operazioni che attraversano la cronologia dei commit (log, merge-base, reachability check):

```bash
# Scrivere il commit-graph
git commit-graph write --reachable
# Crea .git/objects/info/commit-graph

# Con changed-path Bloom filter (accelera git log -- <path>)
git commit-graph write --reachable --changed-paths

# Abilitare la scrittura automatica durante fetch
git config fetch.writeCommitGraph true

# Il commit-graph contiene per ogni commit:
# - Hash del commit
# - Hash del tree root
# - Hash dei parent (con supporto per >2 parent = octopus merge)
# - Generation number (per query di raggiungibilità veloci)
# - Commit timestamp
# - Bloom filter per i path modificati (opzionale)

# Verificare il commit-graph
git commit-graph verify

# Statistiche
git commit-graph read
```

### Generation Numbers

I generation numbers accelerano le query di raggiungibilità:

```bash
# Senza commit-graph:
# "Il commit A è antenato del commit B?"
# → Bisogna attraversare tutto il grafo, O(n)

# Con generation numbers:
# gen(commit) = 1 + max(gen(parent1), gen(parent2), ...)
# Se gen(A) > gen(B), A NON può essere antenato di B
# Taglio immediato senza attraversare il grafo

# Topological level (generation number v1):
# Conta la lunghezza del percorso più lungo alla root

# Corrected commit date (generation number v2):
# Usa i timestamp dei commit corretti per monotonia
# Più preciso per grafi larghi e piatti
```

### Changed-Path Bloom Filters

```bash
# Un Bloom filter per commit indica QUALI percorsi sono stati modificati
# git log -- path/to/file.txt può saltare commit che sicuramente
# non toccano quel percorso, senza ispezionare il tree diff

# Beneficio tipico: 10-100x speedup su git log --follow <file>
# su repository grandi

# Esempio benchmark:
time git log --oneline -- deep/nested/file.txt
# Senza Bloom: 15s
# Con Bloom: 0.2s

# Verificare se i Bloom filter sono presenti:
git commit-graph read | grep "Bloom"
```

---

## Reachability Bitmaps e EWAH Compression

### Cos'è un Reachability Bitmap

I reachability bitmaps sono una struttura dati opzionale che accelera drasticamente le operazioni di attraversamento del grafo degli oggetti Git. Ogni bitmap rappresenta l'insieme degli oggetti raggiungibili da un dato commit come una sequenza di bit: il bit alla posizione *i* è impostato a 1 se il commit può raggiungere l'oggetto *i*-esimo nel packfile, altrimenti è 0.

Senza bitmaps, per rispondere alla domanda "quali oggetti sono raggiungibili dal commit X?" Git deve attraversare il grafo commit → tree → blob, un'operazione O(n) nel numero degli oggetti. Con i bitmaps, la risposta è un semplice lookup in un array di bit, con complessità O(1) per singolo oggetto.

```bash
# Generare i bitmaps per un packfile
git repack -a -d --write-bitmap-index

# Verificare la presenza dei bitmap
ls .git/objects/pack/*.bitmap
# pack-abc123.bitmap

# I bitmaps sono particolarmente utili su server Git
# dove accelerano le operazioni di fetch e clone
# GitHub usa bitmaps su tutti i repository

# Verificare se un repack genera bitmap
GIT_TRACE=1 git repack -a -d -b 2>&1 | grep bitmap
```

### Come Funzionano le Operazioni Bitwise

L'efficienza dei bitmaps deriva dalla possibilità di eseguire operazioni logiche sui bit per calcolare insiemi di oggetti:

```bash
# Scenario: git fetch chiede "dammi gli oggetti raggiungibili da A ma non da B"
# Senza bitmap:
#   1. Attraversa tutto il grafo da A → raccoglie set(A)
#   2. Attraversa tutto il grafo da B → raccoglie set(B)
#   3. Calcola set(A) - set(B) → oggetti da inviare
#   Complessità: O(|set(A)| + |set(B)|)

# Con bitmap:
#   1. Leggi bitmap(A) e bitmap(B)
#   2. Calcola bitmap(A) AND NOT bitmap(B)
#   3. I bit rimanenti a 1 sono gli oggetti da inviare
#   Complessità: O(bitmap_size / word_size) — ordini di grandezza più veloce

# L'unione di raggiungibilità tra commit:
# bitmap(A) OR bitmap(B) → tutti gli oggetti raggiungibili da A o B

# L'intersezione:
# bitmap(A) AND bitmap(B) → oggetti raggiungibili da entrambi
```

### EWAH Compression (Enhanced Word-Aligned Hybrid)

I bitmaps grezzi sarebbero enormi: un repository con 1 milione di oggetti richiederebbe ~125 KiB per bitmap. Git comprime i bitmaps usando l'algoritmo **EWAH** (Enhanced Word-Aligned Hybrid), un metodo di Run-Length Encoding a 64 bit ottimizzato per query veloci.

```bash
# Formato EWAH serializzato:
# ┌─────────────────────────────────────────────────┐
# │ 4 byte: numero di bit del bitmap non compresso   │
# │ 4 byte: numero di word compresse                 │
# │ N × 8 byte: word compresse                       │
# │   - Run-Length Word: codifica sequenze lunghe     │
# │     di bit identici (tutti 0 o tutti 1)          │
# │   - Literal Word: 64 bit di dati effettivi       │
# └─────────────────────────────────────────────────┘

# L'ordinamento degli oggetti nel packfile è cruciale:
# Oggetti simili vicini nel pack → lunghe sequenze di bit identici
# → compressione EWAH molto efficiente
# Questo è il motivo per cui Git ordina gli oggetti per tipo e nome
# prima di creare il packfile

# Il formato EWAH è compatibile con la libreria JavaEWAH
# usata da JGit, garantendo interoperabilità tra
# l'implementazione C di Git e quella Java
```

### Bitmap e Ordinamento degli Oggetti

L'efficacia della compressione EWAH dipende strettamente dall'ordine in cui gli oggetti sono disposti nel packfile. Git utilizza il **pack order** — gli oggetti sono ordinati prima per tipo, poi per nome del percorso, poi per dimensione. Questo produce raggruppamenti naturali: tutti i blob del file `README.md` attraverso la cronologia sono vicini, il che significa che i bit corrispondenti nel bitmap tendono ad essere adiacenti, creando lunghe sequenze di 0 o 1 consecutive che EWAH comprime efficientemente.

```bash
# Configurare il bitmap walk per le operazioni di fetch
git config pack.useBitmaps true    # Predefinito: true

# Numero di commit selezionati per avere un bitmap
# Non ogni commit ha un bitmap — solo un sottoinsieme scelto euristicamente
# Tipicamente: commit raggiungibili da branch tip, tag, e commit a intervalli regolari
git config pack.writeBitmapLookupTable true  # Git 2.42+
# Scrive una tabella di lookup per accelerare la ricerca del bitmap più vicino
# a un commit che non ha un bitmap proprio

# Verificare le statistiche dei bitmap
git rev-list --count --use-bitmap-index --objects HEAD
# Usa i bitmap se disponibili — enormemente più veloce

# Benchmark con e senza bitmap
time git rev-list --objects --all --use-bitmap-index | wc -l
time git rev-list --objects --all --no-use-bitmap-index | wc -l
```

### Multi-Pack Bitmap e MIDX

A partire da Git 2.34+, i bitmaps funzionano anche con il multi-pack-index (MIDX), estendendo il concetto di pseudo-pack:

```bash
# Scrivere un MIDX con bitmap
git multi-pack-index write --bitmap

# Il MIDX definisce un "pseudo-pack" — la concatenazione de-duplicata
# degli oggetti di tutti i packfile, ordinati per pack order
# I bitmap si riferiscono alla posizione degli oggetti in questo pseudo-pack

# Git 2.47+: MIDX incrementale con catena di livelli
# Ogni livello MIDX può avere il proprio file .bitmap
# Permette di aggiornare i bitmap senza riscrivere l'intero MIDX

# Verificare lo stato del MIDX e bitmap
git multi-pack-index verify

# Reverse index: mappa posizione nel MIDX ↔ posizione nel pseudo-pack
# Necessario perché i bitmap usano l'ordinamento pseudo-pack
# ma il MIDX usa l'ordinamento lessicografico per hash
ls .git/objects/pack/multi-pack-index*
```

---

## Reftable: Il Nuovo Backend per i Riferimenti

### Limitazioni del Backend "files"

Il backend tradizionale "files" per i riferimenti (dove ogni ref è un file in `.git/refs/`) ha diverse limitazioni che diventano problematiche su repository di grandi dimensioni:

1. **Performance**: Un repository con 100.000 branch richiede 100.000 file nella directory `refs/heads/`. Operazioni come `git for-each-ref` devono leggere ognuno di questi file, causando migliaia di syscall `open()`/`read()`/`close()`.

2. **Atomicità**: Aggiornare più riferimenti simultaneamente non è atomico con il backend files. Ogni file viene aggiornato indipendentemente — un crash a metà di un `git fetch` può lasciare i riferimenti in uno stato inconsistente.

3. **Case-sensitivity**: Su filesystem case-insensitive (Windows, macOS), i branch `Feature` e `feature` collidono perché mappano allo stesso percorso del filesystem.

4. **Nomi gerarchici**: Non è possibile avere sia `refs/heads/foo` (file) che `refs/heads/foo/bar` (file dentro directory `foo/`). Il filesystem non permette che `foo` sia contemporaneamente un file e una directory.

```bash
# Dimostrare il problema case-sensitivity su macOS/Windows:
git branch Feature
git branch feature
# error: unable to create branch 'feature':
# A branch named 'Feature' already exists

# Dimostrare il conflitto gerarchico:
git branch release
git branch release/v1.0
# error: cannot lock ref 'refs/heads/release/v1.0':
# 'refs/heads/release' exists; cannot create 'refs/heads/release/v1.0'
```

### Architettura del Reftable

Il formato **reftable** (originariamente sviluppato da Google per JGit/Gerrit) risolve tutti questi problemi usando un formato binario basato su blocchi:

```
┌─────────────────────────────────────────────────────────┐
│ File Header (24 byte)                                    │
│   - magic: "REFT"                                        │
│   - version (1)                                          │
│   - block_size                                           │
├─────────────────────────────────────────────────────────┤
│ Ref Block 0                                              │
│   ┌───────────────────────────────────────────────────┐  │
│   │ Block header: tipo (ref), numero entry             │  │
│   │ Entry: prefix_len + suffix + valore                │  │
│   │ Entry: prefix_len + suffix + valore                │  │
│   │ ...                                                │  │
│   │ Restart table (per binary search nel blocco)       │  │
│   └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ Ref Block 1                                              │
│   ...                                                    │
├─────────────────────────────────────────────────────────┤
│ Log Block 0 (reflog entries, opzionale)                  │
│   ...                                                    │
├─────────────────────────────────────────────────────────┤
│ Index Block (se più di un ref block)                     │
│   - Tabella degli offset dei blocchi                     │
│   - Permette binary search tra blocchi                   │
├─────────────────────────────────────────────────────────┤
│ Footer                                                   │
│   - Statistiche, offset dell'indice, checksum            │
└─────────────────────────────────────────────────────────┘
```

### Compattazione Geometrica

Il backend reftable usa un modello append-only con **compattazione geometrica**. Ogni scrittura crea un nuovo file reftable. Quando il numero di file supera una soglia, Git li fonde (compatta) in file più grandi:

```bash
# I file reftable sono memorizzati in .git/reftable/
ls .git/reftable/
# 0x000000000001.ref
# 0x000000000002.ref
# tables.list         ← lista dei file reftable attivi, in ordine

# La compattazione è geometrica:
# File piccoli vengono fusi frequentemente
# File grandi vengono fusi raramente
# Il rapporto tra dimensioni successive è tipicamente 2:1
# Questo ammortizza il costo delle scritture su molte operazioni

# Esempio di compattazione:
# Scrittura 1: crea file A (1 entry)
# Scrittura 2: crea file B (1 entry)
# Scrittura 3: crea file C (1 entry) → compatta A+B+C in D (3 entry)
# Scrittura 4: crea file E (1 entry)
# Scrittura 5: crea file F (1 entry)
# Scrittura 6: crea file G (1 entry) → compatta E+F+G in H (3 entry)
#              → compatta D+H in I (6 entry)
```

### Creare un Repository con Reftable

```bash
# Inizializzare un repository con backend reftable
git init --ref-format=reftable nuovo-repo
cd nuovo-repo

# Verificare il backend in uso
git config extensions.refStorage
# reftable

# Confronto performance su repository con molti ref:
# Backend files:   git for-each-ref → ~2 secondi (100k ref)
# Backend reftable: git for-each-ref → ~0.05 secondi (100k ref)

# Il reftable memorizza anche i reflog nello stesso formato binario
# eliminando la necessità dei file sotto .git/logs/

# Vantaggi chiave:
# - Lookup O(log n) per binary search su blocchi
# - Aggiornamenti atomici multi-ref garantiti dal formato
# - Nessun conflitto case-sensitivity o gerarchico
# - Reflog integrati nello stesso file
# - Compressione per prefisso dei nomi dei ref
```

### Prefix Compression nei Blocchi

All'interno di un singolo blocco, i nomi dei riferimenti sono compressi per prefisso. Poiché i riferimenti sono ordinati, nomi consecutivi condividono spesso un prefisso lungo:

```bash
# Esempio di prefix compression:
# refs/heads/feature/auth        → memorizzato completo
# refs/heads/feature/backend     → prefix_len=21, suffix="backend"
# refs/heads/feature/frontend    → prefix_len=21, suffix="frontend"
# refs/heads/main                → prefix_len=11, suffix="main"

# La restart table permette il binary search all'interno del blocco
# senza decomprimere tutte le entry precedenti
# Tipicamente ogni 16 entry c'è un restart point
```

---

## Cruft Packs e Gestione Oggetti Non Raggiungibili

### Il Problema dei Loose Objects Non Raggiungibili

Quando Git esegue operazioni come rebase, amend o filter-branch, gli oggetti originali diventano non raggiungibili ma non vengono eliminati immediatamente. Tradizionalmente, questi oggetti rimanevano come loose objects nella directory `.git/objects/`, ognuno in un file separato compresso con zlib. Su repository con molta attività di riscrittura della cronologia, migliaia di loose objects non raggiungibili potevano accumularsi, degradando le performance.

### Come Funzionano i Cruft Packs

A partire da Git 2.37, la garbage collection usa i **cruft packs** come strategia predefinita per gestire gli oggetti non raggiungibili. Invece di mantenerli come loose objects, Git li raggruppa in un packfile speciale accompagnato da un file `.mtimes` che registra l'ultima volta che ogni oggetto è stato referenziato:

```bash
# Struttura di un cruft pack:
ls .git/objects/pack/
# pack-abc123.pack       ← packfile con oggetti raggiungibili
# pack-abc123.idx        ← indice del packfile principale
# pack-def456.pack       ← cruft pack (oggetti non raggiungibili)
# pack-def456.idx        ← indice del cruft pack
# pack-def456.mtimes     ← timestamp di modifica per ogni oggetto nel cruft pack

# Formato del file .mtimes:
# ┌────────────────────────────────────────────┐
# │ Header: "MTME" (magic) + version (1)       │
# │ Hash version (1 per SHA-1, 2 per SHA-256)  │
# ├────────────────────────────────────────────┤
# │ N × 4 byte: epoch timestamp (uint32)        │
# │   uno per ogni oggetto nel .idx associato   │
# │   ordinati come gli oggetti nell'indice     │
# ├────────────────────────────────────────────┤
# │ Checksum del file                           │
# └────────────────────────────────────────────┘

# Forzare la creazione di un cruft pack
git gc --cruft
# Equivalente a: git repack --cruft -d

# Controllare che git gc usi cruft packs (predefinito da Git 2.37)
git config gc.cruftPacks
# true (predefinito)
```

### Scadenza degli Oggetti nel Cruft Pack

Il file `.mtimes` permette a Git di determinare l'età di ogni oggetto non raggiungibile senza esaminare i timestamp del filesystem. Quando `git gc` esegue il pruning, confronta l'mtime di ogni oggetto nel cruft pack con la soglia configurata:

```bash
# Eseguire GC con scadenza degli oggetti nel cruft pack
git gc --cruft --prune=2.weeks.ago
# Rimuove dal cruft pack gli oggetti con mtime > 2 settimane fa

# L'oggetto rimane nel cruft pack finché non scade
# Questo è più sicuro di eliminare i loose objects:
# - Meno file da gestire sul filesystem
# - Timestamp affidabili (non dipendono dal filesystem)
# - Più efficiente di migliaia di loose objects separati

# Configurare la scadenza
git config gc.cruftExpire 30.days
# Gli oggetti nel cruft pack più vecchi di 30 giorni vengono eliminati al prossimo gc

# Disabilitare completamente il pruning dal cruft pack
git config gc.cruftExpire never
```

### Vantaggi Rispetto all'Approccio Tradizionale

```bash
# Approccio tradizionale (pre-Git 2.37):
# 1. Oggetti non raggiungibili = loose objects separati
# 2. Migliaia di file in .git/objects/XX/
# 3. Timestamp basati sul filesystem (inaffidabili su alcuni FS)
# 4. stat() costose per determinare l'età di ogni oggetto
# 5. Race condition: un oggetto loose può essere eliminato
#    mentre un altro processo lo sta referenziando

# Approccio cruft pack:
# 1. Un solo packfile per tutti gli oggetti non raggiungibili
# 2. Timestamp in un file .mtimes dedicato (affidabili)
# 3. Nessuna race condition: il packfile è atomico
# 4. Delta compression tra oggetti non raggiungibili
# 5. Performance prevedibili indipendenti dal numero di oggetti

# Scenario tipico dove i cruft pack brillano:
# Repository CI/CD con molti force-push:
# Ogni force-push rende non raggiungibili i commit precedenti
# Senza cruft pack: centinaia di loose objects dopo ogni push
# Con cruft pack: un singolo packfile aggiornato periodicamente
```

---

## Git Bundle: Trasferimento Offline e Backup

### Cos'è un Git Bundle

Un **bundle** è un file binario che incapsula oggetti Git (commit, tree, blob) e riferimenti in un formato ottimizzato per il trasferimento offline. A differenza di un archivio tar/zip della directory `.git`, un bundle è un packfile con un header che descrive i riferimenti contenuti, ed è direttamente utilizzabile dai comandi Git come `clone`, `fetch` e `ls-remote`.

```bash
# Creare un bundle completo del repository
git bundle create repo-completo.bundle --all
# Include tutti i branch, tag e la cronologia completa

# Creare un bundle di un singolo branch
git bundle create main-only.bundle main

# Creare un bundle incrementale (solo i commit dopo un certo punto)
git bundle create aggiornamento.bundle main ^v1.0.0
# Include solo i commit su main che non sono antenati di v1.0.0

# Verificare l'integrità di un bundle
git bundle verify repo-completo.bundle
# The bundle contains 3 refs, with 1500 objects.
# The bundle records a complete history.
# repo-completo.bundle is okay

# Listare i riferimenti contenuti in un bundle
git bundle list-heads repo-completo.bundle
# abc123 refs/heads/main
# def456 refs/heads/develop
# 111222 refs/tags/v1.0.0
```

### Formato Interno del Bundle

```bash
# Il formato del bundle è:
# ┌─────────────────────────────────────────────┐
# │ Signature: "# v3 git bundle\n"              │
# │   (v3 supporta capability come filter)      │
# ├─────────────────────────────────────────────┤
# │ Capabilities (v3):                           │
# │   @filter=blob:none                          │
# │   @object-format=sha256                      │
# ├─────────────────────────────────────────────┤
# │ Prerequisites (per bundle incrementali):     │
# │   -<hash> <commento>                         │
# │   (oggetti che il ricevente DEVE avere)      │
# ├─────────────────────────────────────────────┤
# │ References:                                  │
# │   <hash> <refname>                           │
# ├─────────────────────────────────────────────┤
# │ Riga vuota                                  │
# ├─────────────────────────────────────────────┤
# │ Packfile binario (stesso formato di .pack)   │
# └─────────────────────────────────────────────┘

# Visualizzare l'header di un bundle (parte testuale)
head -20 repo-completo.bundle
# Le righe di testo precedono il packfile binario
```

### Casi d'Uso Pratici

```bash
# Caso 1: Trasferimento a macchina senza rete
# Sulla macchina connessa:
git bundle create /media/usb/progetto.bundle --all
# Sulla macchina isolata:
git clone /media/usb/progetto.bundle progetto
cd progetto
git remote set-url origin git@server:org/progetto.git
# Quando la rete sarà disponibile, fetch dal remote reale

# Caso 2: Backup incrementale giornaliero
# Creare il bundle base (primo giorno)
git bundle create /backup/base.bundle --all
git tag -f ultimo-backup HEAD

# Ogni giorno successivo:
git bundle create /backup/incrementale-$(date +%Y%m%d).bundle \
  --all ^ultimo-backup
git tag -f ultimo-backup HEAD

# Ripristinare da backup incrementali:
git clone /backup/base.bundle progetto-ripristinato
cd progetto-ripristinato
git bundle verify /backup/incrementale-20260101.bundle
git fetch /backup/incrementale-20260101.bundle 'refs/heads/*:refs/heads/*'

# Caso 3: Bundle con filtro (Git v3 bundle, 2.42+)
git bundle create filtered.bundle --all --filter=blob:none
# Crea un bundle senza blob — utile per trasferire solo la cronologia
# Il ricevente dovrà poi scaricare i blob on-demand

# Caso 4: Distribuzione di una release specifica
git bundle create release-v2.bundle v2.0.0
# Include solo gli oggetti necessari per ricostruire v2.0.0
```

---

## Sparse Index e Sparse Checkout Internals

### Sparse Checkout e Cone Mode

Lo **sparse checkout** permette di materializzare solo un sottoinsieme dei file nel working tree, utile per monorepo con milioni di file dove ogni sviluppatore lavora su un modulo specifico. La **cone mode** (introdotta in Git 2.25) è una versione ottimizzata che ragiona per directory intere invece che per pattern gitignore arbitrari:

```bash
# Abilitare sparse checkout in cone mode
git sparse-checkout init --cone

# Specificare le directory da materializzare
git sparse-checkout set packages/frontend docs/
# Solo i file in packages/frontend/ e docs/ sono nel working tree
# Più i file nella root (sempre presenti in cone mode)

# Visualizzare la configurazione sparse corrente
git sparse-checkout list
# packages/frontend
# docs

# Aggiungere una directory senza rimuovere le esistenti
git sparse-checkout add packages/shared

# Cone mode vs non-cone mode:
# Cone mode:
#   - Ragiona per directory intere (include tutto dentro o niente)
#   - Pattern matching O(1) per file (basta verificare il prefisso del path)
#   - Include sempre i file nella root directory
#   - Richiesto per sparse index
#
# Non-cone mode:
#   - Pattern gitignore arbitrari (include singoli file specifici)
#   - Pattern matching O(n) per file (valuta tutti i pattern)
#   - Più flessibile ma molto più lento su repository grandi
```

### Sparse Index: Ottimizzazione dell'Index per Monorepo

Lo **sparse index** (Git 2.32+) è un'ottimizzazione che riduce la dimensione dell'index collassando le directory fuori dallo sparse checkout in singole entry:

```bash
# Abilitare lo sparse index
git sparse-checkout init --cone --sparse-index
# oppure, su un repository esistente con sparse checkout:
git config index.sparse true

# Senza sparse index (index denso):
# L'index contiene TUTTI i file del repository, anche quelli fuori dal cone
# git ls-files --stage | wc -l
# 2,000,000 entry (per un monorepo grande)

# Con sparse index:
# Le directory fuori dal cone sono collassate in una singola entry tree
# git ls-files --stage | wc -l
# 5,000 entry (solo i file nel cone + entry tree per il resto)

# Formato dell'entry tree nello sparse index:
git ls-files --stage
# 100644 blob abc123 0    packages/frontend/index.ts  ← file nel cone
# 100644 blob def456 0    packages/frontend/app.ts    ← file nel cone
# 040000 tree 111222 0    packages/backend/           ← directory collassata
# 040000 tree 333444 0    packages/mobile/            ← directory collassata

# Il flag SKIP_WORKTREE è impostato sulle entry collassate
git ls-files -t
# H packages/frontend/index.ts    ← H = nel working tree
# S packages/backend/              ← S = skip-worktree (collassato)

# Impatto sulle performance di git status:
# Index denso:  git status su monorepo con 2M file → ~15 secondi
# Sparse index: git status su stesso monorepo con 5K file nel cone → ~0.3 secondi
# Speedup: ~50x
```

### Interazione con i Comandi Git

```bash
# git add: funziona solo su file nel cone
git add packages/backend/file.txt
# error: pathspec matches file outside of sparse checkout cone

# git diff: ignora le directory collassate
git diff
# Mostra solo i diff per i file nel cone

# git stash: preserva lo stato sparse
git stash
# Salva solo le modifiche ai file nel cone

# Espandere temporaneamente il cone per un'operazione:
git sparse-checkout add packages/backend
# Materializza i file di packages/backend/
# L'entry tree nel sparse index viene espansa in entry file individuali

# Per monorepo con milioni di file, combinare sparse index con:
# - Partial clone (--filter=blob:none)
# - Filesystem monitor (core.fsmonitor)
# Per ottenere performance paragonabili a un repository piccolo
```

---

## Git Maintenance: Manutenzione Automatizzata

### Architettura del Sottosistema Maintenance

Il comando `git maintenance` (Git 2.30+) fornisce un framework per l'esecuzione automatizzata di task di manutenzione del repository. A differenza di `git gc`, che esegue tutti i task in un singolo passaggio, `git maintenance` esegue task individuali con scheduling separati, minimizzando l'interruzione delle operazioni normali.

```bash
# Registrare un repository per la manutenzione automatica
git maintenance register
# Aggiunge il repository alla lista globale in ~/.gitconfig

# Avviare il daemon di manutenzione in background
git maintenance start
# Configura un cron job (o launchd su macOS, Task Scheduler su Windows)
# che esegue i task secondo la strategia di scheduling configurata

# Verificare lo stato della manutenzione
git maintenance run --task=gc --auto
# Esegue gc solo se necessario

# Fermare la manutenzione automatica
git maintenance stop
# Rimuove il cron job

# De-registrare un repository
git maintenance unregister
```

### I Sei Task di Manutenzione

```bash
# 1. commit-graph: aggiorna il commit-graph incrementalmente
git maintenance run --task=commit-graph
# Scheduling: ogni ora nella strategia incrementale
# Sicuro da eseguire durante operazioni Git concorrenti
# Usa scrittura incrementale (non riscrive l'intero commit-graph)

# 2. prefetch: scarica oggetti dai remote senza aggiornare i ref
git maintenance run --task=prefetch
# Scheduling: ogni ora
# I ref vengono salvati sotto refs/prefetch/ (non refs/remotes/)
# Non modifica i remote-tracking branch
# Scopo: preparare gli oggetti per un fetch futuro che sarà istantaneo

# 3. loose-objects: consolida i loose objects in packfile
git maintenance run --task=loose-objects
# Scheduling: giornaliero
# Step 1: elimina loose objects che esistono già nei packfile
# Step 2: crea un pack "loose-" con i rimanenti loose objects
# Safe: mai elimina un oggetto che potrebbe essere in uso

# 4. incremental-repack: ottimizza i packfile tramite MIDX
git maintenance run --task=incremental-repack
# Scheduling: giornaliero
# Step 1: git multi-pack-index expire (elimina pack non referenziati)
# Step 2: git multi-pack-index repack (fonde piccoli pack in grandi)
# Non riprocessa l'intero repository — solo i pack piccoli

# 5. gc: garbage collection completa (tradizionale)
git maintenance run --task=gc
# Scheduling: non programmato nella strategia incrementale
# Eseguito solo su richiesta o quando auto-trigger è attivo

# 6. pack-refs: consolida i file ref in packed-refs
git maintenance run --task=pack-refs
# Scheduling: non programmato separatamente (parte di gc)
# Riduce il numero di file nella directory refs/
```

### Strategia di Scheduling Incrementale

```bash
# La strategia incrementale è il default di git maintenance start:
# ┌────────────────────────────────────────────────┐
# │ Ogni ora:                                       │
# │   - commit-graph (aggiornamento incrementale)   │
# │   - prefetch (scarica oggetti dai remote)       │
# │                                                 │
# │ Ogni giorno:                                    │
# │   - loose-objects (consolida in pack)            │
# │   - incremental-repack (ottimizza pack via MIDX)│
# │                                                 │
# │ Ogni settimana:                                 │
# │   - pack-refs (consolida riferimenti)            │
# └────────────────────────────────────────────────┘

# Configurare la strategia
git config maintenance.strategy incremental

# Configurare task individuali:
git config maintenance.commit-graph.enabled true
git config maintenance.commit-graph.schedule hourly

git config maintenance.prefetch.enabled true
git config maintenance.prefetch.schedule hourly

git config maintenance.loose-objects.enabled true
git config maintenance.loose-objects.schedule daily

git config maintenance.incremental-repack.enabled true
git config maintenance.incremental-repack.schedule daily

# Git 2.53+: verificare proattivamente se la manutenzione è necessaria
git maintenance is-needed
# Restituisce exit code 0 se almeno un task dovrebbe essere eseguito
# Utile in script di automazione per evitare esecuzioni inutili
```

### Scheduling su Diversi Sistemi Operativi

```bash
# Linux: cron
# git maintenance start crea entry in crontab
crontab -l | grep maintenance
# 0 1-23 * * * "/usr/bin/git" --exec-path="/usr/lib/git-core" \
#   for-each-repo --config=maintenance.repo maintenance run --schedule=hourly
# 0 0 * * * "/usr/bin/git" ... maintenance run --schedule=daily
# 0 0 * * 0 "/usr/bin/git" ... maintenance run --schedule=weekly

# macOS: launchd
# Crea file plist in ~/Library/LaunchAgents/
ls ~/Library/LaunchAgents/org.git-scm.git.*.plist

# Windows: Task Scheduler
# Crea task pianificati nel Task Scheduler di Windows
# Visibili in Task Scheduler → Task Scheduler Library

# Il scheduling è randomizzato al minuto per distribuire il carico
# quando molti client condividono un server (es. CI/CD)
```

---

## Verso Git 3.0: SHA-256 e Reftable di Default

### La Roadmap di Git 3.0

Git 3.0, previsto per la fine del 2026, introdurrà due cambiamenti fondamentali per i nuovi repository: SHA-256 come algoritmo di hash predefinito e reftable come backend predefinito per i riferimenti. Questi cambiamenti non influenzano i repository esistenti, che continueranno a funzionare con SHA-1 e il backend files.

```bash
# Git 2.48-2.51 hanno preparato il terreno per Git 3.0:
# - SHA-256 testato in produzione (non ancora default)
# - Reftable stabilizzato e pronto per la produzione
# - Flag di compatibilità per testare le breaking changes

# Testare il comportamento di Git 3.0 oggi:
GIT_TEST_DEFAULT_HASH=sha256 git init test-sha256
cd test-sha256
echo "test" > file.txt
git add file.txt
git commit -m "test SHA-256"
git rev-parse HEAD
# Output: hash di 64 caratteri (SHA-256) invece di 40 (SHA-1)

# Testare reftable:
git init --ref-format=reftable test-reftable
ls test-reftable/.git/reftable/
# tables.list
```

### Interoperabilità SHA-1 ↔ SHA-256

Git è progettato per permettere la comunicazione tra repository SHA-1 e SHA-256. Il piano di transizione prevede un meccanismo di mappatura bidirezionale:

```bash
# Il file hash-function-transition.txt descrive il meccanismo:
# 1. Ogni oggetto SHA-256 include una mappatura al suo hash SHA-1 equivalente
# 2. La mappatura è memorizzata in un file lookup table nel repository
# 3. Durante push/fetch, Git converte gli hash automaticamente

# Stato attuale dell'interoperabilità (2026):
# - git clone tra SHA-1 e SHA-256: supportato sperimentalmente
# - git push tra SHA-1 e SHA-256: supportato sperimentalmente
# - GitHub/GitLab supporto SHA-256: in fase di sviluppo, non ancora in produzione
# - La raccomandazione è continuare con SHA-1 per repository esistenti
#   e monitorare l'adozione dell'ecosistema

# Perché SHA-256 e non SHA-3 o BLAKE2?
# - SHA-256: ampiamente supportato da hardware (Intel SHA Extensions)
# - SHA-256: implementazioni mature e audite
# - SHA-256: bilancia sicurezza e performance per il caso d'uso Git
# - NIST ha deprecato SHA-1 nel 2011; SHA-256 è lo standard raccomandato
```

### Impatto Pratico della Migrazione

```bash
# Cosa cambia per lo sviluppatore quando un repository usa SHA-256:
# 1. Gli hash sono di 64 caratteri invece di 40
#    abc123def456... (SHA-1, 40 char)
#    abc123def456abc123def456abc123def456abc123def456abc123def456abcdef12 (SHA-256, 64 char)

# 2. Le abbreviazioni devono essere più lunghe per l'univocità
git config core.abbrev 16  # Raccomandato per SHA-256

# 3. Script e tool che parsificano hash devono essere aggiornati
#    Regex per SHA-1: [0-9a-f]{40}
#    Regex per SHA-256: [0-9a-f]{64}

# 4. Il formato degli oggetti rimane identico
#    Solo l'algoritmo di hash dell'header cambia
#    "blob 22\0contenuto" → SHA-256 invece di SHA-1

# 5. I submodule possono usare un hash diverso dal repository principale
#    Un repo SHA-256 può avere submodule SHA-1 e viceversa

# Verifica del formato corrente:
git rev-parse --show-object-format
# sha1     (repository tradizionale)
# sha256   (repository SHA-256)
```

---

## Best Practices

### Manutenzione del Repository

1. **Eseguire `git gc` periodicamente**: Per repository con attività intensa, eseguire `git gc` settimanalmente per mantenere le performance ottimali. Per la maggior parte dei repository, la GC automatica è sufficiente.

2. **Monitorare le dimensioni del repository**: Usare `git count-objects -v` e `git rev-list --objects --all | wc -l` per monitorare la crescita del repository. Una crescita inattesa potrebbe indicare file binari grandi committati accidentalmente.

3. **Verificare l'integrità periodicamente**: Eseguire `git fsck` dopo operazioni critiche o se si sospettano problemi di corruzione.

4. **Non disabilitare il reflog**: Il reflog è una rete di sicurezza essenziale. Mantenere le durate di conservazione predefinite o aumentarle per repository critici.

5. **Usare le packed-refs**: Per repository con molti branch, le packed refs migliorano le performance delle operazioni di lettura.

6. **Abilitare il commit-graph**: Per repository con cronologia lunga, il commit-graph accelera significativamente `git log`, `git merge-base` e query di raggiungibilità.

7. **Usare `git maintenance`**: Da Git 2.30, il sottosistema maintenance automatizza GC, commit-graph, prefetch e pulizia loose objects con scheduling in background.

### Comprensione degli Internals

1. **Studiare i comandi plumbing**: Familiarizzarsi con `cat-file`, `ls-tree`, `update-ref`, `hash-object` e `write-tree` per comprendere cosa fanno i comandi porcelain dietro le quinte.

2. **Esplorare `.git/`**: Navigare la directory `.git` è il modo migliore per interiorizzare come Git funziona. Ogni file e directory ha un ruolo specifico e documentato.

3. **Comprendere il DAG**: La struttura a grafo aciclico diretto è la chiave per capire branching, merging, reachability e garbage collection.

4. **Conoscere i transfer protocol**: Sapere come Git negozia i trasferimenti aiuta a diagnosticare problemi di rete e ottimizzare CI/CD pipelines.

### Performance

1. **Configurare `core.preloadIndex`**: Per repository grandi su filesystem lenti, abilitare il precaricamento dell'index per velocizzare `git status`.

2. **Usare il filesystem monitor**: Con `core.fsmonitor`, Git può usare un daemon per monitorare i cambiamenti nel filesystem, velocizzando drasticamente `git status` su repository grandi.

```bash
git config core.fsmonitor true
git config core.untrackedCache true
```

3. **Considerare il commit graph**: Il commit graph accelera le operazioni che attraversano la cronologia dei commit.

```bash
git commit-graph write --reachable --changed-paths
git config fetch.writeCommitGraph true
```

4. **Partial clone per CI/CD**: Usare `--filter=blob:none` per pipeline che necessitano solo della cronologia dei commit.

5. **Sparse checkout per monorepo**: Combinare partial clone con sparse checkout per scaricare solo i file necessari.

```bash
git clone --filter=blob:none --sparse https://github.com/org/monorepo.git
cd monorepo
git sparse-checkout set packages/my-package
```

---

## Troubleshooting

### Repository Corrotto

```bash
# Sintomo: errori durante operazioni Git
# fatal: loose object abc1234 is corrupt

# Passo 1: Identificare il danno
git fsck --full 2>&1 | tee /tmp/fsck-report.txt
cat /tmp/fsck-report.txt

# Passo 2: Classificare il danno
grep -c "corrupt\|broken\|missing" /tmp/fsck-report.txt
# Se pochi oggetti → recovery selettivo
# Se molti → reclonare

# Passo 3: Se il remote è disponibile, recuperare da lì
git fetch origin
git checkout -f HEAD

# Passo 4: Se necessario, clonare nuovamente
git clone --mirror <url> temp-clone
cp temp-clone/objects/pack/* .git/objects/pack/
```

### Repository Troppo Grande

```bash
# Trovare i file più grandi nella cronologia
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  sort -rnk2 | \
  head -20

# Rimuovere file grandi dalla cronologia con git-filter-repo
pip install git-filter-repo
git filter-repo --path path/to/large-file --invert-paths

# Riscrivere la cronologia per rimuovere blob grandi
git filter-repo --strip-blobs-bigger-than 10M

# Trovare estensioni che occupano più spazio
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  awk '{size=$2; ext=$3; sub(/.*\./,".",ext); sizes[ext]+=size} END {for(e in sizes) printf "%10d %s\n", sizes[e], e}' | \
  sort -rn | head -20
```

### Index Corrotto

```bash
# Sintomo: errori relativi all'index
# fatal: index file corrupt

# Ricostruire l'index dal HEAD
rm .git/index
git reset HEAD

# Se anche reset fallisce:
rm .git/index
git read-tree HEAD
git checkout-index -a
```

### Reflog Perso

```bash
# Se il reflog è stato eliminato o è scaduto
# Usare git fsck per trovare commit orfani
git fsck --lost-found
# Esaminare .git/lost-found/commit/

# Cercare tra i dangling commits
git fsck --unreachable | grep "commit" | \
  awk '{print $3}' | xargs -I{} git log --oneline --no-walk {} 2>/dev/null
```

### Performance Degradata

```bash
# Verificare il numero di loose objects
git count-objects -v

# Se troppi loose objects, eseguire gc
git gc --aggressive

# Verificare e ottimizzare i packfiles
git repack -a -d -f --depth=250 --window=250

# Rigenerare il commit graph
git commit-graph write --reachable --changed-paths

# Verificare il numero di packfile
find .git/objects/pack -name "*.pack" | wc -l
# Se > 50, git gc dovrebbe consolidarli
```

### Fetch/Push Lento

```bash
# Diagnosticare problemi di trasferimento
GIT_TRACE=1 GIT_TRACE_PACKET=1 GIT_CURL_VERBOSE=1 git fetch 2>&1 | head -100

# Possibili cause:
# 1. Troppi ref → usare protocol v2
git config protocol.version 2

# 2. Packfile troppo grande → usare partial clone
# 3. Rete lenta → verificare SSH multiplexing

# Misurare il tempo di negoziazione vs trasferimento
GIT_TRACE_PERFORMANCE=1 git fetch 2>&1

# Ridurre il numero di ref negoziati
git fetch --refmap='+refs/heads/main:refs/remotes/origin/main' origin main
```

### Merge-Base Lento su Cronologia Lunga

```bash
# Se git merge-base è lento su repository con >100k commit
# Abilitare il commit-graph
git commit-graph write --reachable

# Verificare che il commit-graph sia usato
GIT_TRACE=1 git merge-base main develop 2>&1 | grep commit-graph

# Se il commit-graph non viene usato, verificare:
git config core.commitGraph  # deve essere true (predefinito)
```

---

## Domande e Risposte

### D1: Perché Git usa gli hash e non numeri di revisione sequenziali come SVN?

Gli hash SHA-1 derivano dal contenuto, il che rende Git intrinsecamente distribuito: due sviluppatori possono creare commit indipendentemente senza coordinazione. Con numeri sequenziali, servirebbe un server centrale per assegnare il numero successivo. Inoltre, l'hash è un checksum: garantisce l'integrità dell'intera catena. Un numero sequenziale non rileva corruzione. Lo svantaggio è che gli hash sono meno leggibili — per questo Git supporta abbreviazioni univoche e tag.

### D2: Cosa succede realmente quando faccio `git commit`?

1. Git calcola l'hash SHA-1 di ogni file modificato nella staging area e crea i blob corrispondenti.
2. Costruisce un tree che mappa i nomi dei file ai blob.
3. Crea un oggetto commit che referenzia il tree, il commit parent (HEAD attuale), autore, committer e messaggio.
4. Aggiorna il ref del branch corrente (`refs/heads/main`) per puntare al nuovo commit.
5. Aggiorna HEAD (se è un symbolic ref, rimane inalterato; il branch puntato è quello aggiornato).
6. Aggiunge un'entry nel reflog.

### D3: È possibile avere una collisione SHA-1 accidentale?

La probabilità di una collisione casuale SHA-1 con 2^80 oggetti è circa 50%. Per contesto, se Git creasse 1 miliardo di oggetti al secondo, servirebbero circa 36 mila miliardi di anni. La collisione intenzionale (attacco) è stata dimostrata nel 2017, ma Git usa SHA-1DC che rileva e blocca vettori di attacco noti. La migrazione a SHA-256 eliminerà completamente il rischio.

### D4: Perché `git gc` non rimuove subito i commit dopo un rebase?

I commit "vecchi" (pre-rebase) rimangono protetti dal reflog per 30 giorni (predefinito per entry non raggiungibili). Questo è una rete di sicurezza: se il rebase ha causato problemi, puoi recuperare con `git reset --hard ORIG_HEAD` o tramite reflog. Dopo la scadenza del reflog, la successiva GC li rimuoverà.

### D5: Come funziona il `--depth` di shallow clone internamente?

Git aggiunge gli hash dei commit "boundary" al file `.git/shallow`. Questi commit appaiono senza parent, come root commit artificiali. Il protocollo di trasferimento include la capability `shallow` che permette al client di comunicare al server i propri commit shallow. Il server usa questa informazione per calcolare il packfile necessario. Operazioni come `git log` funzionano normalmente ma si fermano ai boundary.

### D6: Posso convertire un repository da SHA-1 a SHA-256?

Ad oggi (2026), la conversione diretta non è ancora pienamente supportata. `git init --object-format=sha256` crea un nuovo repository con SHA-256, ma il tooling per convertire un repository esistente è in sviluppo. GitHub e GitLab non supportano ancora SHA-256 come formato primario. La raccomandazione è continuare con SHA-1 per repository esistenti e monitorare lo stato della transizione.

### D7: Qual è la differenza pratica tra `git repack -a -d` e `git gc`?

`git gc` è un wrapper che esegue `repack`, `prune`, `pack-refs`, `reflog expire` e `commit-graph write`. Se si vuole solo ricompattare gli oggetti senza toccare reflog e riferimenti, `git repack -a -d` è sufficiente. `git gc --aggressive` usa parametri di repack più aggressivi (`--depth=250 --window=250`) e può impiegare molto più tempo su repository grandi.

### D8: Come posso verificare che un clone sia identico al repository originale?

```bash
# Confrontare gli hash di tutti gli oggetti
# Sul repository originale:
git rev-list --objects --all | sort > /tmp/original.txt

# Sul clone:
git rev-list --objects --all | sort > /tmp/clone.txt

# Confrontare:
diff /tmp/original.txt /tmp/clone.txt
# Se l'output è vuoto, i repository contengono gli stessi oggetti
```

### D9: Perché il multi-pack-index (MIDX) migliora le performance?

Senza MIDX, quando Git cerca un oggetto nei packfile, deve cercare in ogni file `.idx` in sequenza — O(p × log n) dove p è il numero di packfile. Con MIDX, un singolo indice copre tutti i packfile — O(log N) dove N è il numero totale di oggetti. Su repository con decine di packfile, il miglioramento è significativo.

---

## Esercizi

### Esercizio 1: Esplorazione del Modello a Oggetti

Creare un repository vuoto e costruire manualmente la struttura blob → tree → commit usando solo comandi plumbing:

```bash
# 1. Inizializzare un repository vuoto
# 2. Creare due blob con hash-object -w
# 3. Costruire un tree con update-index e write-tree
# 4. Creare un commit con commit-tree
# 5. Aggiornare refs/heads/main con update-ref
# 6. Verificare con git log che il commit sia visibile
# 7. Ispezionare ogni oggetto con cat-file -p e -t
```

### Esercizio 2: Delta Compression

Creare un file di 10 KiB, committarlo, modificarlo leggermente (cambiare 10 byte), committare di nuovo. Poi:

```bash
# 1. Verificare che i due blob siano loose objects separati
# 2. Eseguire git gc
# 3. Verificare con git verify-pack -v che uno dei blob sia ora un delta dell'altro
# 4. Annotare il rapporto di compressione (dimensione delta vs dimensione originale)
# 5. Ripetere con git repack --depth=1 e osservare come cambia
```

### Esercizio 3: Recovery con Fsck e Reflog

Simulare la "perdita" di commit e recuperarli:

```bash
# 1. Creare un repository con 5 commit
# 2. Eseguire git reset --hard HEAD~3 (perdere 3 commit)
# 3. Verificare che git log mostra solo 2 commit
# 4. Usare git reflog per trovare l'hash del commit perso
# 5. Recuperare con git reset --hard HEAD@{1}
# 6. Usare git fsck --unreachable per trovare commit orfani
# 7. Eliminare il branch, poi recuperarlo da fsck --lost-found
```

### Esercizio 4: Transfer Protocol Analysis

Analizzare il protocollo di trasferimento durante un fetch:

```bash
# 1. Clonare un repository pubblico piccolo
# 2. Eseguire un fetch con GIT_TRACE_PACKET=1 e salvare l'output
# 3. Identificare: discovery phase, want/have negoziazione, packfile transfer
# 4. Contare quanti round-trip sono necessari
# 5. Ripetere con protocol.version=2 e confrontare
```

### Esercizio 5: Partial Clone e Sparse Checkout

Sperimentare con partial clone:

```bash
# 1. Clonare un repository con --filter=blob:none
# 2. Verificare la dimensione del clone vs un clone completo
# 3. Fare checkout di un file e osservare il download on-demand
# 4. Abilitare sparse-checkout e limitare a una sottodirectory
# 5. Verificare con git count-objects -v quanti blob sono stati scaricati
```

### Esercizio 6: Commit-Graph e Performance

Misurare l'impatto del commit-graph su un repository con cronologia lunga:

```bash
# 1. Clonare un repository con >10k commit (es. un progetto open source)
# 2. Misurare il tempo di git log --oneline | wc -l (senza commit-graph)
# 3. Scrivere il commit-graph: git commit-graph write --reachable --changed-paths
# 4. Misurare di nuovo lo stesso comando
# 5. Misurare git merge-base con e senza commit-graph
# 6. Confrontare i tempi e calcolare lo speedup
```

---

## Riferimenti

- **Git Pro Book — Git Internals**: https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain
- **Git Pro Book — Transfer Protocols**: https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
- **Git Documentation — git-cat-file**: https://git-scm.com/docs/git-cat-file
- **Git Documentation — git-fsck**: https://git-scm.com/docs/git-fsck
- **Git Documentation — gitformat-pack**: https://git-scm.com/docs/gitformat-pack
- **Git Documentation — gitformat-index**: https://git-scm.com/docs/gitformat-index
- **Git Documentation — gitprotocol-pack**: https://git-scm.com/docs/gitprotocol-pack
- **Git Documentation — gitprotocol-v2**: https://git-scm.com/docs/gitprotocol-v2
- **Git Documentation — git-commit-graph**: https://git-scm.com/docs/git-commit-graph
- **Git Documentation — git-multi-pack-index**: https://git-scm.com/docs/git-multi-pack-index
- **Git Documentation — git-maintenance**: https://git-scm.com/docs/git-maintenance
- **Git Documentation — partial-clone**: https://git-scm.com/docs/partial-clone
- **Git Source Code**: https://github.com/git/git
- **SHA-1 Transition Plan**: https://git-scm.com/docs/hash-function-transition
- **Scaling Git at Microsoft**: https://devblogs.microsoft.com/devops/the-largest-git-repo-on-the-planet/
- **Noise Protocol Framework**: https://noiseprotocol.org/

---

## Letture consigliate

- **Git Pro Book — Git Internals** — https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain (consultato: 2026-05-24). Capitolo fondamentale che spiega la distinzione tra comandi plumbing e porcelain e la struttura interna di `.git/`.

- **Git Pro Book — Git Objects** — https://git-scm.com/book/en/v2/Git-Internals-Git-Objects (consultato: 2026-05-24). Trattamento ufficiale dei 4 tipi di oggetti con esempi di creazione manuale.

- **Git Pro Book — Transfer Protocols** — https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols (consultato: 2026-05-24). Descrizione dettagliata dei protocolli smart HTTP e SSH per push/fetch.

- **"Git from the Bottom Up" di John Wiegley** — https://jwiegley.github.io/git-from-the-bottom-up/ (consultato: 2026-05-24). Saggio completo che costruisce la comprensione di Git partendo dagli oggetti fino ai comandi di alto livello.

- **SHA-1 Transition Plan** — https://git-scm.com/docs/hash-function-transition (consultato: 2026-05-24). Documento tecnico sulla migrazione da SHA-1 a SHA-256 nel formato degli oggetti Git.

- **Git Documentation — gitformat-pack** — https://git-scm.com/docs/gitformat-pack (consultato: 2026-05-24). Specifica del formato dei packfile usati per compressione e trasferimento.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti Git: staging area, working tree, DAG | 01 | [01-fondamenti-git.md](01-fondamenti-git.md) |
| Branching e Merge: refs/heads, HEAD, fast-forward | 06 | [06-git-branching-merge-avanzato.md](06-git-branching-merge-avanzato.md) |
| Stash, Reset e Recovery: reflog, dangling commit | 10 | [10-git-stash-reset-recovery.md](10-git-stash-reset-recovery.md) |
| LFS, Submodules e Monorepo: gestione oggetti grandi | 09 | [09-git-lfs-submodules-monorepo.md](09-git-lfs-submodules-monorepo.md) |
| Gitignore, Gitattributes e Configurazione | 11 | [11-gitignore-gitattributes-config.md](11-gitignore-gitattributes-config.md) |
| GitHub Security Scanning: analisi del repository | 16 | [16-github-security-scanning.md](16-github-security-scanning.md) |
| CodeQL e Advanced Security | 28 | [28-codeql-advanced-security.md](28-codeql-advanced-security.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **blob** | Oggetto Git che memorizza il contenuto grezzo di un file senza metadati (nome, permessi). Identificato dall'hash SHA del contenuto. |
| **commit object** | Oggetto Git che rappresenta uno snapshot del repository: punta a un tree, contiene autore, committer, messaggio e riferimenti ai parent commit. |
| **content-addressable storage** | Modello di archiviazione in cui ogni oggetto è identificato dall'hash crittografico del suo contenuto. Due contenuti identici producono lo stesso hash e sono memorizzati una sola volta. |
| **dangling object** | Oggetto Git (commit, blob, tree) che non è raggiungibile da nessun ref. Viene eventualmente rimosso dal garbage collector (`git gc`). |
| **fsck** | Comando `git fsck` (File System Check) che verifica l'integrità del database degli oggetti, identificando oggetti corrotti, dangling e missing. |
| **HEAD** | Ref speciale che punta al commit corrente o (più comunemente) a un branch. In stato "detached HEAD", punta direttamente a un commit. |
| **loose object** | Oggetto Git memorizzato come file singolo in `.git/objects/XX/YYYY...`. Viene compresso in packfile durante `git gc` o `git repack`. |
| **packfile** | File binario (`.pack`) che memorizza molteplici oggetti Git compressi con delta encoding. Usato per storage efficiente e trasferimento di rete. |
| **pack index** | File (`.idx`) associato a un packfile che contiene l'indice degli oggetti per lookup rapido per hash. |
| **reflog** | Log locale che registra ogni spostamento di un ref (branch, HEAD). Accessibile con `git reflog`. I record scadono dopo 90 giorni (default). |
| **refs** | File in `.git/refs/` che mappano nomi leggibili (branch, tag) a SHA di commit. Es: `.git/refs/heads/main` contiene l'hash dell'ultimo commit di `main`. |
| **SHA-1** | Funzione hash crittografica (160 bit, 40 caratteri hex) usata da Git per identificare gli oggetti. In fase di transizione verso SHA-256. |
| **symbolic ref** | Ref che punta a un altro ref invece che a un hash. L'esempio principale è HEAD che punta a `refs/heads/main`. |
| **tree** | Oggetto Git che rappresenta una directory: contiene una lista di blob (file) e altri tree (sottodirectory) con i rispettivi nomi e permessi. |
| **transfer protocol** | Protocollo di comunicazione tra client e server Git durante push/fetch. Include smart HTTP, SSH e il pack protocol v2. |
