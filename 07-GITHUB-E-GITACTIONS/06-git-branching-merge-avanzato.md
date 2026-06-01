---
corso: "GitHub e Git Actions"
fase: "1 — Fondamenti Git"
modulo: "06"
titolo: "Git Branching e Merge Avanzato"
versione: "Git 2.47+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti Git"
  - "02 — Strategie di Branching"
obiettivi:
  - "Comprendere le differenze tra merge strategies (recursive, ort, octopus, ours)"
  - "Applicare rebase interattivo per riscrivere la cronologia in modo sicuro"
  - "Usare cherry-pick e revert per gestire commit selettivi su branch multipli"
  - "Risolvere merge conflict complessi con strumenti diff3 e rerere"
  - "Scegliere il workflow di branching adeguato al team (Git Flow, GitHub Flow, Trunk-Based)"
tag: [git, branching, merge, rebase, cherry-pick, revert, conflict-resolution, git-flow]
---

# Git Branching e Merge Avanzato — Guida Approfondita

> **Modulo 06** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti Git](01-fondamenti-git.md), [Strategie di Branching](02-strategie-branching.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere le differenze tra merge strategies (recursive, ort, octopus, ours)
> 2. Applicare rebase interattivo per riscrivere la cronologia in modo sicuro
> 3. Usare cherry-pick e revert per gestire commit selettivi su branch multipli
> 4. Risolvere merge conflict complessi con strumenti diff3 e rerere
> 5. Scegliere il workflow di branching adeguato al team (Git Flow, GitHub Flow, Trunk-Based)
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **Merge vs rebase: history vs cleanliness.**
2. **`git cherry-pick` per portare commit specific.**
3. **`git revert` per undo public commit.**
4. **`git reflog` salva quando reset/rebase distrugge.**


## Indice
- [Panoramica](#panoramica)
- [Branch Internals: Refs e HEAD](#branch-internals-refs-e-head)
- [Merge Strategies in Dettaglio](#merge-strategies-in-dettaglio)
- [Gestione dei Merge Conflicts](#gestione-dei-merge-conflicts)
- [Rebase Interattivo](#rebase-interattivo)
- [Rebase vs Merge: Matrice Decisionale](#rebase-vs-merge-matrice-decisionale)
- [Cherry-Pick Avanzato](#cherry-pick-avanzato)
- [Workflow di Branching: Modelli Completi](#workflow-di-branching-modelli-completi)
- [Riferimento Comandi Completo](#riferimento-comandi-completo)
- [Git Bisect: Debugging con Ricerca Binaria](#git-bisect-debugging-con-ricerca-binaria)
- [Git Worktree: Directory di Lavoro Multiple](#git-worktree-directory-di-lavoro-multiple)
- [Rebase --onto: Scenari Avanzati](#rebase---onto-scenari-avanzati)
- [Stacked Branches e --update-refs](#stacked-branches-e---update-refs)
- [Rerere Avanzato: Workflow e Strategie](#rerere-avanzato-workflow-e-strategie)
- [Risoluzione Conflitti Avanzata: Strumenti e Tecniche](#risoluzione-conflitti-avanzata-strumenti-e-tecniche)
- [Prevenzione dei Conflitti su Larga Scala](#prevenzione-dei-conflitti-su-larga-scala)
- [Sparse-Checkout e Branching nei Monorepo](#sparse-checkout-e-branching-nei-monorepo)
- [Git Replace e Grafts: Manipolazione della Cronologia](#git-replace-e-grafts-manipolazione-della-cronologia)
- [Ort Strategy: Internals e Performance](#ort-strategy-internals-e-performance)
- [Anti-Pattern](#anti-pattern)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Riferimenti](#riferimenti)

---

## Panoramica

Il branching e il merging rappresentano le operazioni fondamentali che rendono Git uno strumento di versionamento distribuito estremamente potente. Mentre i concetti di base sono relativamente semplici — creare un branch, lavorarci, unirlo al ramo principale — la padronanza delle strategie avanzate di merge, del rebase interattivo e delle tecniche di cherry-pick distingue un utilizzatore competente da un esperto. Questa guida esplora in profondità i meccanismi interni del branching in Git, le diverse strategie di merge disponibili, le tecniche di risoluzione dei conflitti e le operazioni avanzate di manipolazione della cronologia.

Comprendere come Git gestisce i branch a livello di implementazione interna è essenziale per prendere decisioni informate su quale strategia adottare in ogni situazione. Un branch in Git non è una copia dei file, ma semplicemente un puntatore mobile a un commit specifico. Questa leggerezza rende la creazione e la gestione dei branch estremamente efficiente, con un costo computazionale e di storage praticamente nullo.

---

## Branch Internals: Refs e HEAD

### Come Git Rappresenta i Branch

In Git, un branch è implementato come un file di testo nella directory `.git/refs/heads/` che contiene l'hash SHA-1 (o SHA-256 nei repository più recenti) del commit a cui il branch punta. Quando si crea un nuovo branch, Git crea semplicemente un nuovo file con il nome del branch contenente l'hash del commit corrente.

```bash
# Visualizzare il contenuto di un riferimento di branch
cat .git/refs/heads/main
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0

# Equivalente usando il comando Git
git rev-parse main
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0

# Creare un branch manualmente (sconsigliato, ma illustrativo)
echo "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0" > .git/refs/heads/nuovo-branch
```

### Il Ruolo di HEAD

HEAD è un riferimento simbolico speciale che indica quale branch è attualmente attivo (checked out). Si trova in `.git/HEAD` e normalmente contiene un riferimento a un branch, non direttamente a un commit.

```bash
# Visualizzare HEAD
cat .git/HEAD
# Output: ref: refs/heads/main

# Quando HEAD punta direttamente a un commit (detached HEAD)
git checkout a1b2c3d
cat .git/HEAD
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

Lo stato di **detached HEAD** si verifica quando HEAD punta direttamente a un commit invece che a un branch. Questo accade quando si esegue il checkout di un commit specifico, di un tag, o di un branch remoto senza creare un branch locale. In questo stato, qualsiasi commit creato non sarà raggiungibile da nessun branch e potrebbe essere raccolto dal garbage collector.

```bash
# Entrare in stato detached HEAD
git checkout v1.0.0
# Warning: You are in 'detached HEAD' state...

# Creare un branch dal detached HEAD per preservare il lavoro
git checkout -b hotfix-from-tag

# Tornare a un branch esistente
git checkout main
```

### Packed Refs

Per repository con molti branch, Git può "compattare" i riferimenti in un singolo file `.git/packed-refs` per migliorare le performance. Questo file contiene una mappatura hash-nome per tutti i riferimenti.

```bash
# Forzare il packing dei riferimenti
git pack-refs --all

# Visualizzare i packed refs
cat .git/packed-refs
# # pack-refs with: peeled fully-peeled sorted
# a1b2c3d... refs/heads/main
# d4e5f6g... refs/heads/develop
# h7i8j9k... refs/tags/v1.0.0
```

### Riferimenti Speciali

Oltre a HEAD, Git mantiene diversi riferimenti speciali che sono utili in operazioni avanzate:

- **ORIG_HEAD**: salvato prima di operazioni "pericolose" come merge e rebase, permette di tornare allo stato precedente
- **FETCH_HEAD**: il risultato dell'ultimo `git fetch`, utile per merge manuali
- **MERGE_HEAD**: presente durante un merge in corso, punta al commit che si sta unendo
- **CHERRY_PICK_HEAD**: presente durante un cherry-pick in corso

```bash
# Dopo un merge, annullarlo usando ORIG_HEAD
git merge feature-branch
# Se il merge non è soddisfacente:
git reset --hard ORIG_HEAD

# Usare FETCH_HEAD per merge manuale
git fetch origin feature-branch
git merge FETCH_HEAD
```

---

## Merge Strategies in Dettaglio

### Fast-Forward Merge

Il fast-forward merge è la strategia più semplice. Si verifica quando il branch di destinazione non ha ricevuto nuovi commit da quando il branch sorgente è stato creato. In questo caso, Git semplicemente sposta il puntatore del branch di destinazione al commit più recente del branch sorgente.

```bash
# Situazione iniziale:
# main: A---B---C
# feature:         D---E---F

# Fast-forward merge
git checkout main
git merge feature
# main: A---B---C---D---E---F

# Forzare un merge commit anche quando il fast-forward è possibile
git merge --no-ff feature
# main: A---B---C-----------M
#                 \         /
#                  D---E---F
```

L'opzione `--no-ff` (no fast-forward) è particolarmente utile nei workflow Git Flow perché preserva la topologia del branch nel grafo della cronologia, rendendo chiaro dove un feature branch è iniziato e finito.

### Recursive Strategy (Strategia Ricorsiva)

La strategia ricorsiva è quella predefinita quando si uniscono due branch che hanno divergito. Git identifica un antenato comune (merge base) e applica un three-way merge confrontando le modifiche di entrambi i branch rispetto all'antenato.

```bash
# Situazione con branch divergenti:
# main:    A---B---C---G---H
# feature:      \
#                D---E---F

git checkout main
git merge feature
# Git usa la strategia recursive automaticamente

# Specificare esplicitamente la strategia
git merge -s recursive feature

# Opzioni della strategia recursive
git merge -s recursive -X patience feature   # Algoritmo di diff più lento ma migliore
git merge -s recursive -X ours feature       # In caso di conflitto, preferisci il nostro codice
git merge -s recursive -X theirs feature     # In caso di conflitto, preferisci il loro codice
```

La strategia ricorsiva gestisce i casi in cui ci sono più antenati comuni (criss-cross merges) creando un merge virtuale degli antenati prima di procedere con il three-way merge effettivo. Questo approccio ricorsivo è ciò che dà il nome alla strategia.

### Octopus Strategy

La strategia octopus è progettata per unire più di due branch contemporaneamente. È la strategia predefinita quando si specificano più branch nel comando merge. Tuttavia, non è in grado di gestire conflitti che richiedono risoluzione manuale.

```bash
# Unire tre branch contemporaneamente
git merge feature-a feature-b feature-c
# Git usa automaticamente la strategia octopus

# Specificare esplicitamente
git merge -s octopus feature-a feature-b feature-c
```

Questa strategia è particolarmente utile nell'integrazione continua quando si devono combinare molteplici branch di feature che non hanno modifiche sovrapposte. Se si verifica un conflitto, l'octopus merge fallisce e si deve procedere con merge individuali.

### Ort Strategy

A partire da Git 2.33, la strategia **ort** (Ostensibly Recursive's Twin) è stata introdotta come sostituto più performante della strategia recursive. È scritta da zero con focus sulla performance e sulla correttezza.

```bash
# Usare la strategia ort esplicitamente
git merge -s ort feature-branch

# Con opzioni
git merge -s ort -X patience feature-branch

# Configurare ort come strategia predefinita
git config merge.strategy ort
```

La strategia ort offre miglioramenti significativi nella gestione dei rinominamenti di file, nella velocità di esecuzione per repository di grandi dimensioni e nella correttezza dei risultati di merge in scenari complessi.

### Subtree Strategy

La strategia subtree è utilizzata quando si vuole unire un progetto in una sottodirectory di un altro progetto. È la base del comando `git subtree`.

```bash
# Aggiungere un progetto come sottodirectory
git remote add libreria https://github.com/org/libreria.git
git fetch libreria
git merge -s subtree --allow-unrelated-histories libreria/main
```

---

## Gestione dei Merge Conflicts

### Anatomia di un Conflitto

Quando Git non riesce a risolvere automaticamente le differenze tra due branch, crea dei marker di conflitto nel file interessato. Questi marker delimitano le sezioni contrastanti dei due branch.

```
<<<<<<< HEAD
Codice dal branch corrente (il nostro)
Questa riga è stata modificata nel branch main.
=======
Codice dal branch in merge (il loro)
Questa riga è stata modificata nel feature branch.
>>>>>>> feature-branch
```

Con l'opzione `diff3`, Git mostra anche il contenuto originale dell'antenato comune, fornendo più contesto per la risoluzione:

```bash
# Abilitare lo stile diff3 per i conflitti
git config merge.conflictstyle diff3
```

Il risultato sarà:

```
<<<<<<< HEAD
Codice dal branch corrente
||||||| merged common ancestor
Codice originale dall'antenato comune
=======
Codice dal branch in merge
>>>>>>> feature-branch
```

Lo stile **zdiff3** (introdotto in Git 2.35) è ancora più informativo, eliminando le parti comuni tra le versioni in conflitto:

```bash
git config merge.conflictstyle zdiff3
```

### Workflow di Risoluzione dei Conflitti

La risoluzione dei conflitti segue un flusso di lavoro preciso:

```bash
# 1. Tentare il merge
git merge feature-branch
# Auto-merging src/app.js
# CONFLICT (content): Merge conflict in src/app.js
# Automatic merge failed; fix conflicts and then commit the result.

# 2. Verificare lo stato
git status
# Both modified: src/app.js

# 3. Visualizzare i conflitti
git diff
# Mostra i marker di conflitto

# 4. Risolvere i conflitti (manualmente o con un tool)
# Opzione A: Editare il file manualmente rimuovendo i marker
# Opzione B: Usare un merge tool
git mergetool

# 5. Dopo la risoluzione, aggiungere il file
git add src/app.js

# 6. Completare il merge
git commit
# Git apre l'editor con un messaggio di merge predefinito

# Alternativa: Abortire il merge se necessario
git merge --abort
```

### Merge Tool Configurazione

Git supporta diversi strumenti grafici per la risoluzione dei conflitti:

```bash
# Configurare vimdiff come merge tool
git config merge.tool vimdiff

# Configurare VS Code come merge tool
git config merge.tool vscode
git config mergetool.vscode.cmd 'code --wait $MERGED'

# Configurare meld
git config merge.tool meld

# Configurare IntelliJ IDEA
git config merge.tool intellij
git config mergetool.intellij.cmd 'idea merge $LOCAL $REMOTE $BASE $MERGED'

# Non creare file .orig di backup dopo la risoluzione
git config mergetool.keepBackup false
```

### Rerere: Reuse Recorded Resolution

La funzionalità **rerere** (reuse recorded resolution) è estremamente utile quando si affrontano conflitti ripetitivi, come durante un rebase lungo o quando si uniscono regolarmente gli stessi branch. Git registra come si risolvono i conflitti e applica automaticamente la stessa risoluzione in futuro.

```bash
# Abilitare rerere
git config rerere.enabled true

# Dopo aver risolto un conflitto, Git lo registra automaticamente
# La prossima volta che lo stesso conflitto si presenta, Git lo risolve automaticamente

# Visualizzare le risoluzioni registrate
git rerere status

# Visualizzare i diff delle risoluzioni
git rerere diff

# Dimenticare una risoluzione specifica
git rerere forget src/app.js

# La directory delle risoluzioni registrate
ls .git/rr-cache/
```

Rerere è particolarmente prezioso nei seguenti scenari:
- Rebase frequenti di branch di lunga durata
- Workflow che richiedono merge ripetuti (come l'integrazione periodica di un branch di sviluppo)
- Testing di merge prima dell'integrazione effettiva

---

## Rebase Interattivo

### Fondamenti del Rebase

Il rebase riscrive la cronologia dei commit spostando una serie di commit su una nuova base. A differenza del merge, che preserva la topologia originale, il rebase crea nuovi commit con gli stessi changeset ma con parent diversi.

```bash
# Rebase di base
git checkout feature
git rebase main
# Equivalente a: prendi tutti i commit di feature che non sono in main
# e riapplicali sopra main

# Prima del rebase:
# main:    A---B---C
# feature:      \
#                D---E---F

# Dopo il rebase:
# main:    A---B---C
# feature:              D'---E'---F'
```

### Rebase Interattivo: Comandi Disponibili

Il rebase interattivo è uno degli strumenti più potenti per la pulizia della cronologia dei commit. Si attiva con l'opzione `-i` (interactive).

```bash
# Rebase interattivo degli ultimi 5 commit
git rebase -i HEAD~5

# Rebase interattivo fino a un commit specifico
git rebase -i abc1234

# Rebase interattivo su un branch
git rebase -i main
```

Quando si esegue un rebase interattivo, Git apre un editor con la lista dei commit e i comandi disponibili:

```
pick a1b2c3d Aggiungere autenticazione utente
pick d4e5f6g Correggere typo nel login
pick h7i8j9k Aggiungere validazione email
pick l0m1n2o WIP: refactoring temporaneo
pick p3q4r5s Completare il refactoring dell'auth

# Rebase abc1234..p3q4r5s onto abc1234 (5 commands)
#
# Commands:
# p, pick   = use commit
# r, reword = use commit, but edit the commit message
# e, edit   = use commit, but stop for amending
# s, squash = use commit, but meld into previous commit
# f, fixup  = like "squash", but discard this commit's log message
# x, exec   = run command (the rest of the line) using shell
# b, break  = stop here (continue rebase later with 'git rebase --continue')
# d, drop   = remove commit
# l, label  = label current HEAD with a name
# t, reset  = reset HEAD to a label
```

### Pick

Il comando `pick` mantiene il commit così com'è. È il comando predefinito per tutti i commit nella lista.

```bash
pick a1b2c3d Aggiungere autenticazione utente
pick d4e5f6g Correggere typo nel login
# Entrambi i commit vengono applicati senza modifiche
```

### Reword

Il comando `reword` permette di modificare il messaggio di un commit senza cambiarne il contenuto. Git si fermerà dopo ogni commit con `reword` per permettere la modifica del messaggio.

```bash
reword a1b2c3d Aggiungere autenticazione utente
# Git aprirà l'editor per modificare questo messaggio
pick d4e5f6g Correggere typo nel login
```

### Squash

Il comando `squash` unisce un commit con quello precedente, combinando anche i messaggi di commit. È utile per consolidare una serie di piccoli commit in uno più significativo.

```bash
pick a1b2c3d Aggiungere autenticazione utente
squash d4e5f6g Correggere typo nel login
squash h7i8j9k Aggiungere validazione email
# I tre commit vengono fusi in uno solo
# Git aprirà l'editor con tutti e tre i messaggi combinati
```

### Fixup

Il comando `fixup` è simile a `squash`, ma scarta il messaggio del commit che viene fuso. È ideale per incorporare piccole correzioni nel commit principale.

```bash
pick a1b2c3d Aggiungere autenticazione utente
fixup d4e5f6g Correggere typo nel login
# Il risultato è un singolo commit con il messaggio del primo
```

Git 2.32 ha introdotto `fixup -C` che mantiene il messaggio del commit fixup invece di scartarlo:

```bash
pick a1b2c3d Vecchio messaggio
fixup -C d4e5f6g Nuovo messaggio migliore
# Il risultato usa "Nuovo messaggio migliore"
```

### Edit

Il comando `edit` ferma il rebase dopo l'applicazione del commit, permettendo di modificarne il contenuto. È utile per dividere un commit in più commit o per apportare modifiche al codice.

```bash
pick a1b2c3d Aggiungere autenticazione utente
edit h7i8j9k Commit troppo grande da dividere
pick l0m1n2o Altro commit

# Quando Git si ferma al commit "edit":
# 1. Modificare i file necessari
git reset HEAD~1                    # Annullare il commit mantenendo le modifiche
git add src/auth.js
git commit -m "Aggiungere modulo di autenticazione"
git add src/validation.js
git commit -m "Aggiungere validazione input"
git rebase --continue               # Continuare il rebase
```

### Drop

Il comando `drop` rimuove completamente un commit dalla cronologia. Equivale a cancellare la riga dalla lista.

```bash
pick a1b2c3d Aggiungere autenticazione utente
drop d4e5f6g Commit da rimuovere completamente
pick h7i8j9k Aggiungere validazione email
```

### Exec

Il comando `exec` permette di eseguire un comando shell tra un commit e l'altro. È utile per verificare che ogni commit nella cronologia sia compilabile.

```bash
pick a1b2c3d Aggiungere autenticazione utente
exec npm test
pick d4e5f6g Aggiungere validazione email
exec npm test
# Se un test fallisce, il rebase si ferma per la correzione
```

### Autosquash

L'opzione `--autosquash` automatizza l'organizzazione dei commit quando si usano convenzioni di naming specifiche:

```bash
# Creare un commit fixup per un commit specifico
git commit --fixup=a1b2c3d
# Crea un commit con messaggio "fixup! <messaggio del commit a1b2c3d>"

# Creare un commit squash
git commit --squash=a1b2c3d
# Crea un commit con messaggio "squash! <messaggio del commit a1b2c3d>"

# Il rebase autosquash li riordina automaticamente
git rebase -i --autosquash main
# I commit fixup! e squash! vengono posizionati automaticamente dopo il loro target

# Abilitare autosquash come comportamento predefinito
git config rebase.autoSquash true
```

---

## Rebase vs Merge: Matrice Decisionale

La scelta tra rebase e merge è una delle decisioni più dibattute nel workflow Git. Entrambi gli approcci hanno vantaggi e svantaggi specifici.

### Quando Usare Merge

| Scenario | Motivazione |
|----------|-------------|
| Branch condivisi con altri sviluppatori | Il merge non riscrive la cronologia condivisa |
| Preservare il contesto del feature branch | Il merge commit documenta quando e cosa è stato integrato |
| Branch di lunga durata (release, develop) | La cronologia topologica è informativa |
| Quando la cronologia dettagliata è importante | Ogni commit è preservato nel suo contesto originale |
| Branch pubblici (main, develop) | Mai riscrivere la cronologia pubblica |

### Quando Usare Rebase

| Scenario | Motivazione |
|----------|-------------|
| Branch locali non condivisi | La cronologia lineare è più leggibile |
| Pulizia prima del merge | Squash dei commit WIP, reword dei messaggi |
| Aggiornamento del feature branch | Portare le ultime modifiche di main nel feature branch |
| Cronologia lineare desiderata | Bisect funziona meglio con cronologia lineare |
| Piccole feature/fix | Non necessitano del contesto di un merge commit |

### Regola d'Oro del Rebase

**Non eseguire mai il rebase di commit che sono stati condivisi con altri.** Il rebase crea nuovi commit con hash diversi. Se altri sviluppatori hanno basato il loro lavoro sui commit originali, il rebase causerà conflitti e confusione.

```bash
# SICURO: Rebase del proprio branch locale su main aggiornato
git checkout feature-mia
git rebase main

# PERICOLOSO: Rebase di un branch condiviso
git checkout feature-team
git rebase main
git push --force  # Questo distruggerà il lavoro degli altri!

# MENO PERICOLOSO: Force push con lease
git push --force-with-lease
# Fallisce se qualcuno ha pushato nel frattempo
```

### Workflow Ibrido Consigliato

Il workflow ibrido combina i vantaggi di entrambi gli approcci:

1. **Sviluppo locale**: Usare rebase per mantenere il branch aggiornato con main
2. **Pulizia pre-merge**: Usare rebase interattivo per consolidare i commit
3. **Integrazione**: Usare merge `--no-ff` per creare un merge commit che documenta l'integrazione
4. **Cronologia pulita**: Ogni feature branch ha commit atomici e significativi

```bash
# 1. Aggiornare il feature branch con le ultime modifiche di main
git checkout feature-branch
git rebase main

# 2. Pulire la cronologia dei commit
git rebase -i main
# Squash commit WIP, reword messaggi poco chiari

# 3. Merge nel branch principale con merge commit
git checkout main
git merge --no-ff feature-branch -m "Merge feature: autenticazione OAuth2"
```

---

## Cherry-Pick Avanzato

### Fondamenti del Cherry-Pick

Il cherry-pick applica le modifiche di un commit specifico sul branch corrente, creando un nuovo commit con lo stesso changeset ma un hash diverso.

```bash
# Cherry-pick di un singolo commit
git cherry-pick abc1234

# Cherry-pick senza commit automatico (staging only)
git cherry-pick --no-commit abc1234

# Cherry-pick mantenendo il riferimento al commit originale
git cherry-pick -x abc1234
# Aggiunge "(cherry picked from commit abc1234)" al messaggio
```

### Cherry-Pick con Range

Git permette di cherry-pick di una serie di commit usando la notazione con i due punti:

```bash
# Cherry-pick di un range di commit (esclusivo del primo, inclusivo dell'ultimo)
git cherry-pick abc1234..def5678

# Cherry-pick di un range inclusivo (nota il ^, che include il primo commit)
git cherry-pick abc1234^..def5678

# Cherry-pick di più commit non consecutivi
git cherry-pick abc1234 def5678 ghi9012

# Cherry-pick dall'ultimo commit di un branch
git cherry-pick feature-branch
# Equivale a cherry-pick del commit a cui punta feature-branch
```

### Gestione dei Conflitti nel Cherry-Pick

```bash
# Se un cherry-pick causa un conflitto
git cherry-pick abc1234
# CONFLICT...

# Risolvere il conflitto e continuare
git add file-risolto.js
git cherry-pick --continue

# Oppure abortire
git cherry-pick --abort

# Saltare un commit problematico in un range
git cherry-pick --skip
```

### Cherry-Pick di Merge Commits

I merge commit hanno due o più parent. Per fare cherry-pick di un merge commit, è necessario specificare quale parent considerare come "mainline":

```bash
# Cherry-pick di un merge commit
# -m 1 significa "usa il primo parent come mainline"
git cherry-pick -m 1 abc1234

# -m 2 per il secondo parent
git cherry-pick -m 2 abc1234
```

Il numero del parent corrisponde all'ordine mostrato in `git log`:

```bash
git log --format="%H %P" abc1234
# abc1234... parent1... parent2...
# -m 1 = parent1 (tipicamente il branch di destinazione del merge)
# -m 2 = parent2 (tipicamente il branch che è stato mergiato)
```

### Uso Strategico del Cherry-Pick

Il cherry-pick è particolarmente utile in questi scenari:

- **Hotfix**: Applicare una correzione critica dal branch develop a main/production senza portare tutte le altre modifiche
- **Backporting**: Portare feature specifiche a versioni precedenti del software
- **Recupero selettivo**: Estrarre commit utili da un branch che verrà abbandonato
- **Release management**: Costruire release branch selezionando commit specifici

```bash
# Esempio: Hotfix workflow
git checkout main
git cherry-pick -x hotfix-commit-hash
git tag -a v1.0.1 -m "Hotfix: correzione critica sicurezza"
git push origin main --tags

# Backport a una versione precedente
git checkout release/1.x
git cherry-pick -x abc1234
git push origin release/1.x
```

---

## Workflow di Branching: Modelli Completi

### Git Flow

Git Flow è il modello di branching più strutturato, progettato da Vincent Driessen nel 2010. È ideale per software con release pianificate e versioni multiple in supporto simultaneo.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GIT FLOW                                    │
│                                                                     │
│  main     ──●──────────────────●───────────────────●──────────     │
│             │                  ↑                   ↑                │
│             │            merge │             merge │                │
│  release    │         ●──●──●──┘          ●──●──●──┘                │
│             │         ↑                   ↑                        │
│             │   merge │             merge │                        │
│  develop  ──●──●──●──●──●──●──●──●──●──●──●──●──●──●──●──────     │
│                ↑        ↑        ↑                                  │
│          merge │  merge │  merge │                                  │
│  feature  ●──●─┘   ●──●─┘  ●──●─┘                                  │
│                                                                     │
│  hotfix     ●──●──→ merge in main E develop                        │
│                                                                     │
│  Branch             Origine        Merge In       Naming            │
│  ──────             ───────        ────────       ──────            │
│  main               —              —              main              │
│  develop             main           —              develop           │
│  feature/*           develop        develop        feature/AUTH-123  │
│  release/*           develop        main+develop   release/1.2.0    │
│  hotfix/*            main           main+develop   hotfix/CVE-2024  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

```bash
# Inizializzare Git Flow
git flow init

# Feature
git flow feature start oauth2-authentication
# ... sviluppo ...
git flow feature finish oauth2-authentication

# Release
git flow release start 1.2.0
# ... bugfix, version bump ...
git flow release finish 1.2.0

# Hotfix
git flow hotfix start critical-security-fix
# ... fix ...
git flow hotfix finish critical-security-fix
```

### GitHub Flow

GitHub Flow è un modello semplificato usato dalla maggior parte dei team che praticano Continuous Delivery. C'è solo `main` e feature branch. Ogni modifica passa per una Pull Request.

```
┌─────────────────────────────────────────────────────────────────────┐
│                       GITHUB FLOW                                   │
│                                                                     │
│  main     ──●──────●──────────────●──────────────●──────────       │
│             │      ↑              ↑              ↑                  │
│             │  PR merge       PR merge       PR merge               │
│  feature    │  ●──●──●        ●──●           ●──●──●──●             │
│             │                                                       │
│  Regole:                                                            │
│  1. main è sempre deployable                                       │
│  2. Branch dal main per qualsiasi modifica                         │
│  3. Commit frequenti, push al remote                               │
│  4. Aprire una PR per feedback e review                            │
│  5. Merge in main solo dopo review e CI green                      │
│  6. Deploy immediatamente dopo il merge                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Trunk-Based Development

Trunk-Based Development (TBD) è il modello preferito da team ad alte performance (Google, Meta). Gli sviluppatori committano direttamente sul trunk (main) o tramite branch di brevissima durata (< 1 giorno).

```
┌─────────────────────────────────────────────────────────────────────┐
│               TRUNK-BASED DEVELOPMENT                               │
│                                                                     │
│  main     ──●──●──●──●──●──●──●──●──●──●──●──●──●──●──────        │
│                ↑     ↑        ↑     ↑                               │
│            merge merge    merge merge                               │
│  short-     ●──┘  ●──┘     ●──┘  ●──┘                              │
│  lived                                                              │
│  branches   (< 1 giorno, < 200 righe)                              │
│                                                                     │
│  release    ──────●──●──────────────────                            │
│  branch          ↑  (solo cherry-pick di fix)                      │
│                  │                                                   │
│  (creato         │                                                   │
│   dal main      ─┘                                                   │
│   per release)                                                      │
│                                                                     │
│  Caratteristiche:                                                   │
│  - Feature flags per codice non pronto                             │
│  - CI/CD obbligatoria con test rapidi                              │
│  - Nessun branch di lunga durata                                   │
│  - Release da tag o release branch (solo fix)                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Confronto dei Modelli

| Aspetto | Git Flow | GitHub Flow | Trunk-Based |
|---------|----------|-------------|-------------|
| Complessità | Alta | Bassa | Minima |
| Release | Pianificate | Continue | Continue |
| Branch vita | Giorni/settimane | Giorni | Ore |
| Versioni multiple | Sì | No | Via release branch |
| Feature flags | Non necessari | Opzionali | Essenziali |
| CI/CD | Consigliata | Obbligatoria | Obbligatoria |
| Team size ideale | Medio/grande | Qualsiasi | Qualsiasi |
| Caso d'uso | Software tradizionale | SaaS, web app | Alto throughput |

### Three-Way Merge: Internals

Il three-way merge è il cuore di `git merge`. Comprendere il suo funzionamento è essenziale per risolvere conflitti.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREE-WAY MERGE INTERNALS                     │
│                                                                  │
│                    Base (Antenato Comune)                        │
│                    ┌──────────────┐                              │
│                    │ function() { │                              │
│                    │   return 1;  │                              │
│                    │ }            │                              │
│                    └──────┬───────┘                              │
│                           │                                      │
│                    ┌──────┴──────┐                               │
│                    │             │                                │
│              ┌─────▼─────┐ ┌────▼──────┐                        │
│              │  Ours      │ │  Theirs   │                        │
│              │  (HEAD)    │ │  (merge)  │                        │
│              ├───────────┤ ├───────────┤                        │
│              │ function(){│ │ function(){│                       │
│              │  return 2; │ │  return 1; │  ← Non modificato    │
│              │ }          │ │  // added  │                       │
│              │            │ │ }          │                        │
│              └─────┬──────┘ └─────┬─────┘                       │
│                    │              │                               │
│                    └──────┬───────┘                              │
│                           │                                      │
│                    ┌──────▼───────┐                              │
│                    │  Risultato   │                              │
│                    ├──────────────┤                              │
│                    │ function() { │                              │
│                    │   return 2;  │  ← Da ours (modificato)     │
│                    │   // added   │  ← Da theirs (aggiunto)     │
│                    │ }            │                              │
│                    └──────────────┘                              │
│                                                                  │
│  Regole del three-way merge:                                    │
│  1. Se solo un lato ha modificato → prendi la modifica          │
│  2. Se entrambi hanno la stessa modifica → ok, prendi una       │
│  3. Se entrambi hanno modifiche DIVERSE → CONFLITTO             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Rebase Step-by-Step: Cosa Succede Internamente

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REBASE STEP BY STEP                               │
│                                                                     │
│  PRIMA:                                                             │
│  main:    A───B───C───G───H                                        │
│  feature:      └───D───E───F                                       │
│                                                                     │
│  git checkout feature && git rebase main                            │
│                                                                     │
│  PASSO 1: Git identifica il merge base (B)                         │
│           e i commit da riapplicare (D, E, F)                      │
│                                                                     │
│  PASSO 2: Git resetta feature a H (tip di main)                    │
│  main:    A───B───C───G───H                                        │
│  feature:                  ↑ (HEAD qui ora)                        │
│                                                                     │
│  PASSO 3: Riapplica D come D' (nuovo hash, stesso diff)           │
│  main:    A───B───C───G───H                                        │
│  feature:                  └───D'                                   │
│                                                                     │
│  PASSO 4: Riapplica E come E'                                      │
│  feature:                  └───D'───E'                              │
│                                                                     │
│  PASSO 5: Riapplica F come F'                                      │
│  feature:                  └───D'───E'───F'                         │
│                                                                     │
│  DOPO:                                                              │
│  main:    A───B───C───G───H                                        │
│  feature:                  └───D'───E'───F'                         │
│                                                                     │
│  NOTA: D', E', F' hanno hash DIVERSI da D, E, F                   │
│        perché il parent è cambiato.                                │
│        I commit originali D, E, F diventano unreachable            │
│        e verranno rimossi dal garbage collector.                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Riferimento Comandi Completo

### Opzioni Complete di `git merge`

| Opzione | Descrizione |
|---------|-------------|
| `--no-ff` | Crea sempre un merge commit (disabilita fast-forward) |
| `--ff-only` | Merge solo se è possibile il fast-forward |
| `--squash` | Squash tutti i commit in uno, non crea merge commit |
| `--no-commit` | Esegue il merge ma non committare (permette modifiche) |
| `-s <strategy>` | Specifica la strategia di merge (recursive, ort, subtree, octopus) |
| `-X <option>` | Opzione per la strategia (`ours`, `theirs`, `patience`, `ignore-space-change`) |
| `--allow-unrelated-histories` | Permette merge di cronologie senza antenato comune |
| `--abort` | Annulla un merge in corso |
| `--continue` | Continua un merge dopo risoluzione conflitti |
| `--quit` | Annulla senza ripristinare lo stato pre-merge |
| `--no-verify` | Salta gli hook pre-merge |
| `-m <msg>` | Messaggio per il merge commit |
| `--stat` / `--no-stat` | Mostra/nascondi il diffstat dopo il merge |
| `--log[=<n>]` | Include i messaggi dei commit mergiati nel merge commit |
| `--signoff` | Aggiunge Signed-off-by |
| `--autostash` | Stash automatico prima e pop dopo il merge |
| `--into-name <branch>` | Nome del branch per il messaggio di merge |

### Opzioni Complete di `git rebase`

| Opzione | Descrizione |
|---------|-------------|
| `-i`, `--interactive` | Rebase interattivo |
| `--onto <newbase>` | Riapplica su una base diversa dal branch upstream |
| `--autosquash` | Riordina automaticamente commit fixup!/squash! |
| `--autostash` | Stash automatico prima e pop dopo |
| `--keep-empty` | Mantiene commit vuoti |
| `--rebase-merges` | Preserva la topologia dei merge nella cronologia |
| `--no-rebase-merges` | Linearizza (default) |
| `--exec <cmd>` | Esegue un comando dopo ogni commit |
| `--root` | Rebase dalla radice della cronologia |
| `--abort` | Annulla il rebase in corso |
| `--continue` | Continua dopo risoluzione conflitti |
| `--skip` | Salta il commit corrente |
| `--quit` | Annulla senza ripristinare lo stato originale |
| `-X <option>` | Opzione strategia (`ours`, `theirs`, `patience`) |
| `--empty=<action>` | Cosa fare con commit vuoti: drop, keep, ask |
| `--no-verify` | Salta gli hook |
| `--fork-point` / `--no-fork-point` | Usa/non usa il fork point per determinare la base |
| `--update-refs` | Aggiorna i branch che puntano ai commit rebasati |
| `--reschedule-failed-exec` | Ripianifica exec falliti (da Git 2.25) |

### Opzioni Complete di `git cherry-pick`

| Opzione | Descrizione |
|---------|-------------|
| `-x` | Aggiunge "(cherry picked from commit ...)" al messaggio |
| `-n`, `--no-commit` | Applica senza committare (solo staging) |
| `-e`, `--edit` | Modifica il messaggio del commit |
| `-m <parent>`, `--mainline <parent>` | Parent mainline per merge commit |
| `-s`, `--signoff` | Aggiunge Signed-off-by |
| `--ff` | Fast-forward se possibile |
| `--allow-empty` | Permette commit vuoti |
| `--allow-empty-message` | Permette messaggi vuoti |
| `--strategy=<strategy>` | Strategia di merge |
| `-X <option>` | Opzione strategia |
| `--continue` | Continua dopo risoluzione conflitti |
| `--abort` | Annulla il cherry-pick |
| `--skip` | Salta il commit corrente |
| `--quit` | Annulla senza ripristinare |
| `--rerere-autoupdate` | Aggiorna con risoluzioni rerere |

### Opzioni Complete di `git branch`

| Opzione | Descrizione |
|---------|-------------|
| `-a`, `--all` | Mostra branch locali e remoti |
| `-r`, `--remotes` | Mostra solo branch remoti |
| `-v`, `--verbose` | Mostra hash e messaggio dell'ultimo commit |
| `-vv` | Verbose + tracking info |
| `--list <pattern>` | Filtra per pattern (es. `feature/*`) |
| `-d <branch>` | Elimina branch mergiato |
| `-D <branch>` | Forza eliminazione branch |
| `-m <old> <new>` | Rinomina branch |
| `-M <old> <new>` | Forza rinomina |
| `-c <old> <new>` | Copia branch |
| `--contains <commit>` | Branch che contengono il commit |
| `--no-contains <commit>` | Branch che NON contengono il commit |
| `--merged [<commit>]` | Branch mergiati nel commit |
| `--no-merged [<commit>]` | Branch non mergiati |
| `--sort=<key>` | Ordina (es. `-committerdate`, `authorname`) |
| `--format=<format>` | Formato output personalizzato |
| `-u <upstream>`, `--set-upstream-to=<upstream>` | Configura tracking |
| `--unset-upstream` | Rimuove tracking |
| `--points-at <object>` | Branch che puntano all'oggetto |
| `--show-current` | Mostra il branch corrente |

---

## Git Bisect: Debugging con Ricerca Binaria

### Concetti Fondamentali

`git bisect` è uno strumento di debugging che utilizza la ricerca binaria per identificare il commit esatto che ha introdotto un bug o una regressione. Dato un range di commit tra uno stato "buono" (good) e uno "cattivo" (bad), bisect dimezza sistematicamente lo spazio di ricerca ad ogni passo, riducendo il numero di commit da verificare da N a log₂(N). Per un range di 1024 commit, bastano solo 10 passaggi invece di controllare ogni singolo commit.

```bash
# Workflow base di git bisect
git bisect start

# Indicare il commit in cui il bug è presente
git bisect bad HEAD

# Indicare l'ultimo commit noto in cui il bug non era presente
git bisect good v2.0.0

# Git esegue il checkout del commit a metà strada
# Bisecting: 512 revisions left to test after this (roughly 9 steps)
# [abc1234...] Some commit message

# Testare se il bug è presente in questo commit
# Se il bug È presente:
git bisect bad
# Se il bug NON è presente:
git bisect good

# Ripetere fino a quando Git identifica il commit colpevole
# abc1234 is the first bad commit
# commit abc1234
# Author: Developer <dev@example.com>
# Date:   Mon Jan 15 14:30:00 2026 +0100
#
#     refactor: cambiare logica di validazione input

# Al termine, tornare allo stato originale
git bisect reset
```

### Terminologia Personalizzata

A partire da Git 2.36, `git bisect` supporta termini personalizzati per scenari dove "good" e "bad" non sono appropriati. Ad esempio, quando si cerca il commit che ha introdotto un miglioramento delle performance, il commit "buono" è in realtà quello "veloce" e il "cattivo" è quello "lento".

```bash
# Usare termini personalizzati
git bisect start --term-old=slow --term-new=fast

# Indicare gli estremi
git bisect fast HEAD          # HEAD ha le performance migliori
git bisect slow v1.0.0        # v1.0.0 era più lento

# Durante la ricerca, usare i termini personalizzati
git bisect slow               # Questo commit è ancora lento
git bisect fast               # Questo commit è già veloce

# Alternativa: usare old/new al posto di good/bad
git bisect start --term-old=old --term-new=new
git bisect old v1.0.0
git bisect new HEAD
```

### Bisect Automatizzato con Script

La potenza reale di `git bisect` emerge con l'automazione tramite `git bisect run`. Si fornisce uno script o un comando che testa automaticamente ogni commit, e Git esegue l'intera ricerca binaria senza intervento manuale.

```bash
# Bisect automatico con un test script
git bisect start
git bisect bad HEAD
git bisect good v2.0.0

# Eseguire un test automatico ad ogni passo
git bisect run npm test

# Oppure con uno script personalizzato
git bisect run ./test-regression.sh
```

Lo script deve rispettare le seguenti convenzioni per i codici di uscita:

| Codice di Uscita | Significato |
|------------------|-------------|
| `0` | Il commit è "good" — il bug NON è presente |
| `1-124`, `126-127` | Il commit è "bad" — il bug È presente |
| `125` | Il commit non è testabile — bisect lo salta (`skip`) |
| `128+` | Errore fatale — bisect si interrompe |

```bash
#!/bin/bash
# test-regression.sh — Script per bisect automatico

# 1. Compilare il progetto
# Se la compilazione fallisce, il commit non è testabile
make clean && make || exit 125

# 2. Eseguire il test specifico per la regressione
./run-specific-test.sh
EXIT_CODE=$?

# 3. Restituire il codice appropriato
if [ $EXIT_CODE -eq 0 ]; then
    exit 0    # good: il test passa, il bug non è presente
else
    exit 1    # bad: il test fallisce, il bug è presente
fi
```

### Esempio Pratico: Trovare una Regressione di Performance

```bash
#!/bin/bash
# perf-regression-test.sh — Cerca il commit che ha degradato le performance

# Compilare (skip se non compila)
npm install --silent 2>/dev/null || exit 125
npm run build --silent 2>/dev/null || exit 125

# Eseguire il benchmark
RESULT=$(node benchmark.js 2>/dev/null)
EXEC_TIME=$(echo "$RESULT" | grep "execution_time" | awk '{print $2}')

# Confrontare con la soglia (in millisecondi)
THRESHOLD=500
if [ "$EXEC_TIME" -lt "$THRESHOLD" ]; then
    echo "Performance OK: ${EXEC_TIME}ms < ${THRESHOLD}ms"
    exit 0    # good
else
    echo "Performance DEGRADATA: ${EXEC_TIME}ms >= ${THRESHOLD}ms"
    exit 1    # bad
fi
```

```bash
# Eseguire il bisect automatico con lo script
git bisect start
git bisect bad HEAD
git bisect good v1.5.0
git bisect run ./perf-regression-test.sh

# Risultato:
# running ./perf-regression-test.sh
# Performance OK: 320ms < 500ms
# Bisecting: 128 revisions left to test...
# ...
# Performance DEGRADATA: 750ms >= 500ms
# Bisecting: 64 revisions left to test...
# ...
# abc1234def5678 is the first bad commit
```

### Saltare Commit Non Testabili

Durante un bisect manuale, alcuni commit potrebbero non essere compilabili o testabili (ad esempio, commit intermedi di un refactoring). Il comando `skip` permette di saltarli senza invalidare la ricerca.

```bash
# Saltare un singolo commit
git bisect skip

# Saltare un range di commit
git bisect skip v2.1.0..v2.2.0

# Saltare il commit corrente e specificare un range aggiuntivo
git bisect skip abc1234 def5678
```

Attenzione: saltare troppi commit consecutivi può impedire a Git di identificare il commit esatto. In tal caso, Git restituisce un range di commit sospetti invece di un singolo commit.

### Bisect Log e Replay

Git registra ogni passo del bisect in un log che può essere salvato, esaminato e riprodotto. Questo è utile per documentare il debugging o per ripetere la ricerca dopo una correzione.

```bash
# Salvare il log del bisect corrente
git bisect log > bisect-session.log

# Visualizzare il log
cat bisect-session.log
# git bisect start
# # good: [abc1234...] Release v2.0.0
# git bisect good abc1234
# # bad: [def5678...] HEAD
# git bisect bad def5678
# # good: [ghi9012...] Some intermediate commit
# git bisect good ghi9012

# Riprodurre una sessione di bisect
git bisect replay bisect-session.log

# Utile quando si è marcato un commit erroneamente
# 1. Salvare il log
git bisect log > session.log
# 2. Editare il file rimuovendo o correggendo la riga errata
# 3. Ricominciare
git bisect reset
git bisect replay session.log
```

### Bisect con Percorsi Specifici

Quando il bug riguarda solo una parte del codice, è possibile limitare il bisect a percorsi specifici per velocizzare la ricerca:

```bash
# Limitare il bisect a file o directory specifiche
git bisect start -- src/auth/ src/middleware/

# Oppure specificare i percorsi nel comando start completo
git bisect start HEAD v2.0.0 -- src/auth/

# Combinare con bisect run
git bisect start HEAD v2.0.0 -- src/auth/
git bisect run npm test -- --grep "authentication"
```

### Visualizzare i Risultati del Bisect

```bash
# Dopo il bisect, visualizzare i commit rimasti da testare
git bisect visualize

# Equivalente a git log con il range del bisect
git bisect visualize --oneline

# Mostrare le statistiche del bisect
git bisect visualize --stat
```

---

## Git Worktree: Directory di Lavoro Multiple

### Concetti Fondamentali

`git worktree` permette di avere multiple directory di lavoro (working trees) associate allo stesso repository Git. Ogni worktree ha il proprio working directory, index e HEAD, ma condivide lo stesso database di oggetti, refs e configurazione del repository principale. Questo elimina la necessità di fare `git stash` o di clonare il repository più volte per lavorare su branch diversi contemporaneamente.

```bash
# Creare un nuovo worktree per un branch esistente
git worktree add ../hotfix-directory hotfix/SEC-123

# Creare un nuovo worktree con un nuovo branch
git worktree add -b feature/new-api ../new-api-directory

# Creare un worktree per un tag (detached HEAD)
git worktree add ../release-test v3.0.0

# Listare tutti i worktree
git worktree list
# /home/dev/project          abc1234 [main]
# /home/dev/hotfix-directory  def5678 [hotfix/SEC-123]
# /home/dev/new-api-directory ghi9012 [feature/new-api]
```

### Setup Consigliato: Bare Repository

Il pattern più efficace per l'uso dei worktree è partire da un bare repository. Un bare repository contiene solo i dati Git senza file di lavoro, e serve come hub centrale per tutti i worktree.

```bash
# Clonare come bare repository
git clone --bare https://github.com/org/project.git project.git

# Entrare nella directory del bare repo
cd project.git

# Creare worktree per il branch principale
git worktree add ../project-main main

# Creare worktree per lo sviluppo
git worktree add ../project-develop develop

# Creare worktree per una feature
git worktree add -b feature/oauth ../project-oauth

# Struttura risultante:
# project.git/           ← bare repository (hub)
# project-main/          ← worktree per main
# project-develop/       ← worktree per develop
# project-oauth/         ← worktree per feature/oauth
```

Questo pattern offre diversi vantaggi:

1. **Nessun worktree "principale"** — tutti i worktree sono equivalenti
2. **Separazione netta** — il bare repo non ha un working directory proprio, evitando confusione
3. **Performance** — tutti i worktree condividono un singolo object store, senza duplicazione dei dati
4. **Indipendenza** — ogni worktree può eseguire build, test e server senza interferire con gli altri

### Casi d'Uso Pratici

#### Revisione di Pull Request senza Perdere il Contesto

```bash
# Si sta lavorando su una feature
# Un collega chiede una review urgente

# Creare un worktree per la PR senza toccare il lavoro corrente
git fetch origin pull/42/head:pr-42
git worktree add ../review-pr-42 pr-42

# Andare nella directory della PR
cd ../review-pr-42

# Eseguire i test, esaminare il codice
npm install && npm test

# Quando la review è completata, rimuovere il worktree
cd ../project
git worktree remove ../review-pr-42
git branch -D pr-42
```

#### Hotfix Urgente durante lo Sviluppo di una Feature

```bash
# Lavoro corrente su feature/payment
# Arriva un bug critico in produzione

# Creare un worktree per l'hotfix partendo da main
git worktree add -b hotfix/critical-fix ../hotfix main

cd ../hotfix
# Correggere il bug
vim src/auth.js
git add src/auth.js
git commit -m "fix: correggere bypass autenticazione in endpoint /api/admin"
git push origin hotfix/critical-fix

# Tornare alla feature
cd ../project
# Il lavoro sulla feature è esattamente dove l'avevi lasciato

# Dopo il merge dell'hotfix, rimuovere il worktree
git worktree remove ../hotfix
```

#### Testing Parallelo su Branch Multipli

```bash
# Testare la stessa suite di test su branch diversi contemporaneamente
git worktree add ../test-main main
git worktree add ../test-develop develop
git worktree add ../test-feature feature/new-api

# In terminali separati:
# Terminale 1:
cd ../test-main && npm test
# Terminale 2:
cd ../test-develop && npm test
# Terminale 3:
cd ../test-feature && npm test

# Confrontare i risultati senza dover switchare branch
```

### Gestione dei Worktree

```bash
# Listare worktree con dettagli
git worktree list --porcelain

# Rimuovere un worktree
git worktree remove ../old-worktree

# Rimuovere forzatamente (se ha modifiche non committate)
git worktree remove --force ../old-worktree

# Pulire worktree orfani (directory cancellate manualmente)
git worktree prune

# Riparare i percorsi dei worktree (utile dopo spostamenti di directory)
git worktree repair

# Bloccare un worktree per impedirne la rimozione automatica
git worktree lock ../important-worktree
git worktree lock --reason "Esperimento in corso" ../experiment

# Sbloccare un worktree
git worktree unlock ../important-worktree
```

### Limitazioni dei Worktree

1. **Un branch per worktree**: Non è possibile avere lo stesso branch checked out in due worktree contemporaneamente. Git restituisce un errore esplicito.
2. **Submoduli**: Il supporto per i submoduli nei worktree secondari è migliorato nelle versioni recenti di Git (2.46+), ma può richiedere configurazione aggiuntiva.
3. **Hooks**: Gli hook sono condivisi dal repository principale. Se un worktree necessita di hook diversi, è necessaria una configurazione manuale.
4. **IDE**: Alcuni IDE non riconoscono automaticamente i worktree collegati. Aprire la directory del worktree come progetto separato di solito risolve il problema.

### Worktree e AI Agent (Pattern 2025-2026)

Una tendenza emergente nel 2025-2026 è l'uso di worktree per isolare il lavoro di agenti AI paralleli. Ogni agente lavora nel proprio worktree su un branch dedicato, senza interferire con gli altri agenti o con il lavoro manuale dello sviluppatore.

```bash
# Creare worktree per agenti AI paralleli
git worktree add -b agent/auth-refactor ../agent-auth
git worktree add -b agent/test-coverage ../agent-tests
git worktree add -b agent/docs-update ../agent-docs

# Ogni agente lavora in isolamento nel proprio worktree
# Al termine, i risultati vengono integrati tramite PR
```

---

## Rebase --onto: Scenari Avanzati

### Anatomia del Comando

Il comando `git rebase --onto` ha la seguente sintassi:

```
git rebase --onto <nuova-base> <vecchia-base> [<branch>]
```

Significato: "Prendi i commit di `<branch>` (o del branch corrente) che non sono raggiungibili da `<vecchia-base>` e riapplicali su `<nuova-base>`".

### Scenario 1: Spostare un Feature Branch sulla Base Corretta

Un errore comune è creare un feature branch partendo dal branch sbagliato. Il branch è partito da `develop` ma doveva partire da `main`.

```bash
# Situazione iniziale:
# main:       A---B---C
# develop:         \---D---E
# feature:              \---F---G---H  (partito da develop per errore)

# Spostare F-G-H da develop a main
git rebase --onto main develop feature

# Risultato:
# main:       A---B---C---F'---G'---H'
# develop:         \---D---E
# feature ora punta a H' (basato su C, non su E)
```

Passo per passo:
1. Git identifica i commit di `feature` non raggiungibili da `develop`: F, G, H
2. Git resetta `feature` al tip di `main` (commit C)
3. Git riapplica F come F', G come G', H come H' sopra C

### Scenario 2: Rimuovere Commit Intermedi

`--onto` può anche rimuovere una serie di commit dal mezzo della cronologia.

```bash
# Situazione: la cronologia ha commit che non vogliamo
# feature: A---B---C---D---E---F---G
#                   ^^^^^^^^^^^
#                   D, E, F sono commit di debug da rimuovere

# Rimuovere D, E, F mantenendo G
git rebase --onto C F feature

# Risultato:
# feature: A---B---C---G'
# I commit D, E, F sono stati eliminati
```

Spiegazione: "Prendi i commit di `feature` che non sono raggiungibili da `F` (cioè solo G) e riapplicali su `C`".

### Scenario 3: Estrazione di una Sotto-Feature

Quando un feature branch contiene lavoro per due feature distinte e si vuole separare una in un branch indipendente.

```bash
# Situazione:
# main:       A---B---C
# feature:         \---D---E---F---G---H
#                       ^^^^^^^^       ^^^
#                       feature-1      feature-2

# Creare un branch per feature-2 basato su main
git branch feature-2 feature    # feature-2 punta a H
git rebase --onto main F feature-2

# Risultato:
# main:       A---B---C
# feature:         \---D---E---F---G---H
# feature-2:      \---G'---H'  (basato direttamente su C)
```

### Scenario 4: Aggiornamento di una Catena di Branch

In un workflow con branch impilati (stacked branches), aggiornare la base richiede l'aggiornamento a cascata di tutti i branch della catena.

```bash
# Situazione:
# main:     A---B---C---X---Y  (nuovi commit X, Y su main)
# feature-1:     \---D---E
# feature-2:          \---F---G
# feature-3:               \---H---I

# Passo 1: aggiornare feature-1 su main
git rebase --onto main C feature-1
# main:     A---B---C---X---Y
# feature-1:                 \---D'---E'

# Passo 2: aggiornare feature-2 su feature-1
git rebase --onto feature-1 E feature-2
# feature-2:                      \---F'---G'

# Passo 3: aggiornare feature-3 su feature-2
git rebase --onto feature-2 G feature-3
# feature-3:                           \---H'---I'
```

Questo processo manuale è tedioso e soggetto a errori. La sezione successiva mostra come `--update-refs` lo automatizza.

---

## Stacked Branches e --update-refs

### Il Problema dei Branch Impilati

I branch impilati (stacked branches o stacked PRs) sono una tecnica in cui una serie di feature branch sono costruite uno sopra l'altro, formando una catena. Questo approccio è utile per suddividere una feature grande in pull request più piccole e revisionabili.

```
# Struttura di branch impilati:
# main:       A---B---C
# feature/step-1:  \---D---E
# feature/step-2:       \---F---G
# feature/step-3:            \---H---I
```

Il problema emerge quando `main` riceve nuovi commit e si deve aggiornare l'intera catena. Senza `--update-refs`, è necessario eseguire un rebase per ogni branch nella catena, nell'ordine corretto, specificando manualmente i riferimenti `--onto`.

### La Soluzione: --update-refs

Introdotto in Git 2.38, il flag `--update-refs` automatizza l'aggiornamento dei puntatori dei branch durante il rebase. Quando si esegue il rebase del branch alla fine della catena, tutti i branch intermedi vengono aggiornati automaticamente.

```bash
# Configurare --update-refs come comportamento predefinito
git config --global rebase.updateRefs true

# Eseguire il rebase dal branch finale della catena
git checkout feature/step-3
git rebase --update-refs main

# Git automaticamente:
# 1. Rebasa tutti i commit D-I su main
# 2. Aggiorna feature/step-1 per puntare dopo E'
# 3. Aggiorna feature/step-2 per puntare dopo G'
# 4. feature/step-3 punta dopo I'

# Risultato:
# main:              A---B---C---X---Y
# feature/step-1:                    \---D'---E'
# feature/step-2:                         \---F'---G'
# feature/step-3:                              \---H'---I'
```

### Rebase Interattivo con --update-refs

L'opzione `--update-refs` funziona anche con il rebase interattivo. Git inserisce automaticamente direttive `update-ref` nella lista dei comandi del rebase.

```bash
git checkout feature/step-3
git rebase -i --update-refs main

# La lista del rebase interattivo mostrerà:
pick D Implementare modulo base
pick E Aggiungere test modulo base
update-ref refs/heads/feature/step-1
pick F Aggiungere endpoint API
pick G Test endpoint API
update-ref refs/heads/feature/step-2
pick H Aggiungere interfaccia utente
pick I Test interfaccia utente

# È possibile riordinare, squashare, editare i commit
# Le direttive update-ref vengono eseguite automaticamente
```

### Workflow Pratico con Branch Impilati

```bash
# 1. Creare la catena di branch
git checkout main
git checkout -b feature/database-schema
# ... implementare schema ...
git commit -am "feat: aggiungere schema tabelle utenti e permessi"

git checkout -b feature/api-endpoints
# ... implementare API ...
git commit -am "feat: aggiungere endpoint CRUD utenti"

git checkout -b feature/frontend-ui
# ... implementare UI ...
git commit -am "feat: aggiungere pagina gestione utenti"

# 2. Main riceve nuovi commit
git checkout main
git pull origin main

# 3. Aggiornare tutta la catena con un solo comando
git checkout feature/frontend-ui
git rebase --update-refs main

# 4. Push di tutti i branch aggiornati
git push --force-with-lease origin feature/database-schema
git push --force-with-lease origin feature/api-endpoints
git push --force-with-lease origin feature/frontend-ui

# 5. Quando il primo PR viene mergiato, aggiornare la catena rimanente
git checkout feature/frontend-ui
git rebase --update-refs main
```

---

## Rerere Avanzato: Workflow e Strategie

### Come Funziona Rerere Internamente

Quando `rerere` è abilitato, Git registra lo stato del conflitto prima e dopo la risoluzione manuale nella directory `.git/rr-cache/`. Ogni conflitto ha un hash univoco basato sul contenuto delle parti in conflitto. Quando lo stesso conflitto si ripresenta (stesso contenuto conflittuale), Git applica automaticamente la risoluzione precedente tramite un three-way merge tra il conflitto originale registrato, la risoluzione registrata e il nuovo conflitto.

```bash
# Struttura di .git/rr-cache/
ls .git/rr-cache/
# 4a8b9c2d3e5f/
# ├── preimage    ← stato del file CON i marker di conflitto
# └── postimage   ← stato del file DOPO la risoluzione manuale

# 7f1e2d3c4b5a/
# ├── preimage
# └── postimage
```

### Workflow: Test di Integrazione con Rerere

Un workflow avanzato con `rerere` consiste nel "preparare" le risoluzioni dei conflitti prima del merge effettivo. Si esegue un merge di prova, si risolvono i conflitti (che vengono registrati da rerere), si annulla il merge, e quando il merge reale avviene, `rerere` risolve tutto automaticamente.

```bash
# 1. Abilitare rerere
git config rerere.enabled true

# 2. Eseguire un merge di prova
git checkout main
git merge --no-commit feature-branch
# CONFLICT (content): Merge conflict in src/config.js

# 3. Risolvere tutti i conflitti manualmente
vim src/config.js
git add src/config.js
# rerere registra la risoluzione

# 4. Annullare il merge di prova
git merge --abort
# La risoluzione resta registrata in .git/rr-cache/

# 5. Quando il merge reale avviene (es. dopo code review):
git merge feature-branch
# Recorded resolution for 'src/config.js'.
# La risoluzione viene applicata AUTOMATICAMENTE

# 6. Verificare e committare
git diff   # Controllare la risoluzione automatica
git add src/config.js
git commit
```

### Rerere nel Contesto di Rebase Lunghi

Quando si fa rebase di un branch con molti commit, lo stesso conflitto può ripresentarsi per ogni commit. Con `rerere`, la risoluzione viene applicata automaticamente a ogni occorrenza.

```bash
# Senza rerere: risolvere lo stesso conflitto N volte durante il rebase
git rebase main
# CONFLICT in file.js — risolvere manualmente
git add file.js && git rebase --continue
# CONFLICT in file.js — risolvere manualmente (stesso conflitto!)
git add file.js && git rebase --continue
# ... ripetere per ogni commit che tocca file.js

# Con rerere: risolvere una sola volta
git config rerere.enabled true
git rebase main
# CONFLICT in file.js — risolvere manualmente la prima volta
git add file.js && git rebase --continue
# Recorded resolution for 'file.js'.
# CONFLICT in file.js — rerere la risolve automaticamente!
# Resolved 'file.js' using previous resolution.
git add file.js && git rebase --continue
# ... automatico per ogni occorrenza successiva
```

### Gestione delle Risoluzioni Errate

```bash
# Dimenticare una risoluzione errata per un file specifico
git rerere forget src/config.js

# Dimenticare tutte le risoluzioni
rm -rf .git/rr-cache/*

# Verificare lo stato di rerere
git rerere status
# src/config.js

# Visualizzare il diff tra la risoluzione registrata e lo stato corrente
git rerere diff

# Applicare manualmente una risoluzione registrata
git rerere
# Senza argomenti, tenta di applicare le risoluzioni registrate ai conflitti correnti
```

### Condividere le Risoluzioni tra Sviluppatori

Le risoluzioni registrate da `rerere` sono locali per definizione, ma possono essere condivise tra sviluppatori per evitare che ognuno debba risolvere gli stessi conflitti. Un approccio consiste nel committare la directory `rr-cache` in un repository separato.

```bash
# Sviluppatore A: esportare le risoluzioni
tar -czf rerere-resolutions.tar.gz .git/rr-cache/
# Condividere il file via canale sicuro

# Sviluppatore B: importare le risoluzioni
cd /path/to/project
tar -xzf rerere-resolutions.tar.gz
# Ora anche B ha le stesse risoluzioni registrate
```

---

## Risoluzione Conflitti Avanzata: Strumenti e Tecniche

### Stili di Conflitto a Confronto

Git supporta diversi stili per la visualizzazione dei conflitti. La scelta dello stile influenza significativamente la capacità di risolvere i conflitti in modo informato.

```bash
# Stile merge (default) — mostra solo le due versioni
git config merge.conflictstyle merge
```

```
<<<<<<< HEAD
const timeout = 5000;
=======
const timeout = 3000;
>>>>>>> feature
```

```bash
# Stile diff3 — mostra anche l'antenato comune
git config merge.conflictstyle diff3
```

```
<<<<<<< HEAD
const timeout = 5000;
||||||| merged common ancestor
const timeout = 10000;
=======
const timeout = 3000;
>>>>>>> feature
```

```bash
# Stile zdiff3 (Git 2.35+) — diff3 senza parti ridondanti
git config merge.conflictstyle zdiff3
```

Lo stile `zdiff3` è raccomandato come configurazione globale perché fornisce il massimo contesto eliminando le parti comuni che complicano la lettura. Mostrando l'antenato comune, è immediatamente chiaro quale branch ha fatto quale modifica: nell'esempio sopra, il valore originale era `10000`, HEAD lo ha ridotto a `5000` e feature lo ha ridotto a `3000`.

### Risoluzione per File Interi

Quando si sa in anticipo quale versione di un file intero adottare, è possibile risolvere il conflitto senza editare il file:

```bash
# Accettare la versione del branch corrente (ours)
git checkout --ours src/config.js
git add src/config.js

# Accettare la versione del branch in merge (theirs)
git checkout --theirs src/config.js
git add src/config.js

# Accettare la versione dell'antenato comune (base)
git checkout --merge src/config.js    # Ripristina i marker di conflitto

# Usare la versione di un commit specifico
git checkout abc1234 -- src/config.js
git add src/config.js
```

### Merge Tool Avanzati: Configurazione Completa

```bash
# Configurazione completa per VS Code come merge tool (2025+)
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd \
    'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'
git config --global mergetool.keepBackup false
git config --global mergetool.prompt false

# Configurazione per Neovim con diffview
git config --global merge.tool nvimdiff
git config --global mergetool.nvimdiff.layout \
    "(LOCAL,BASE,REMOTE)/MERGED"

# Configurazione per IntelliJ IDEA / JetBrains
git config --global merge.tool intellij
git config --global mergetool.intellij.cmd \
    'idea merge "$LOCAL" "$REMOTE" "$BASE" "$MERGED"'
git config --global mergetool.intellij.trustExitCode true

# Configurazione per Meld (Linux)
git config --global merge.tool meld
git config --global mergetool.meld.cmd \
    'meld "$LOCAL" "$BASE" "$REMOTE" --output "$MERGED"'
```

### Diff Tool per Analisi Pre-Merge

Prima di eseguire un merge, è buona pratica analizzare le differenze per anticipare i conflitti:

```bash
# Visualizzare le differenze tra due branch
git diff main...feature-branch

# Visualizzare solo i file che saranno modificati
git diff --name-only main...feature-branch

# Visualizzare le statistiche delle modifiche
git diff --stat main...feature-branch

# Simulare il merge senza eseguirlo (dry run)
git merge --no-commit --no-ff feature-branch
git diff --cached    # Vedere il risultato del merge
git merge --abort    # Annullare senza conseguenze

# Identificare i file che causeranno conflitti
git merge-tree $(git merge-base main feature) main feature
# Mostra il risultato del merge inclusi i conflitti, senza modificare il working tree
```

### Risoluzione Conflitti in File Binari

I file binari (immagini, PDF, file compilati) non possono essere mergiati con i marker di conflitto testuali. Git offre strategie specifiche.

```bash
# Per file binari, scegliere una delle due versioni
git checkout --ours assets/logo.png
git checkout --theirs assets/logo.png

# Configurare driver di merge personalizzati per tipi di file
# In .gitattributes:
# *.png merge=binary
# *.lock merge=ours

# Configurare un driver "ours" che mantiene sempre la versione corrente
git config merge.ours.driver true
# In .gitattributes:
# package-lock.json merge=ours
# yarn.lock merge=ours
```

### Strategia di Risoluzione Sistematica

Per merge complessi con molti conflitti, è utile seguire un approccio sistematico:

```bash
# 1. Contare e listare tutti i file in conflitto
git diff --name-only --diff-filter=U
# Output:
# src/auth/login.js
# src/config/database.js
# src/models/user.js
# tests/auth.test.js

# 2. Raggruppare per tipo di conflitto
git diff --name-only --diff-filter=U | while read file; do
    echo "=== $file ==="
    grep -c "<<<<<<< HEAD" "$file" 2>/dev/null || echo "binary conflict"
done

# 3. Risolvere prima i conflitti più semplici (pochi marker)
# 4. Poi i conflitti strutturali (refactoring vs modifica)
# 5. Infine i conflitti semantici (logica divergente)

# 6. Verificare dopo ogni risoluzione
git add src/auth/login.js
npm test -- --grep "auth"    # Testare il modulo appena risolto

# 7. Completare il merge solo quando tutti i test passano
git commit
```

---

## Prevenzione dei Conflitti su Larga Scala

### Strategia di Integrazione Continua dei Branch

La prevenzione dei conflitti è più efficace della risoluzione. Team ad alte performance adottano strategie specifiche per minimizzare la frequenza e la complessità dei conflitti.

#### Rebase Mattutino

```bash
# Ogni mattina, prima di iniziare a lavorare
git checkout feature-branch
git fetch origin main
git rebase origin/main

# Automatizzare con un alias
git config --global alias.morning-sync \
    '!git fetch origin main && git rebase origin/main'
# Uso: git morning-sync
```

Questa pratica riduce drasticamente i conflitti perché le divergenze tra branch vengono mantenute piccole. Un team di 50 sviluppatori che pratica il rebase mattutino su un monorepo sperimenta conflitti rari e sempre di piccola entità.

#### Code Ownership e File Boundaries

Organizzare il codice in modo che i team diversi lavorino su file diversi riduce i conflitti alla radice. Usare il file `CODEOWNERS` di GitHub per definire i proprietari di ciascuna area del codice.

```bash
# .github/CODEOWNERS
# Team Auth possiede tutto il modulo di autenticazione
/src/auth/            @team-auth
/tests/auth/          @team-auth

# Team API possiede gli endpoint
/src/api/             @team-api
/tests/api/           @team-api

# File condivisi richiedono review di entrambi i team
/src/shared/          @team-auth @team-api
```

#### Merge Queue e Merge Train

Le merge queue (GitHub) e i merge train (GitLab) serializzano i merge per evitare conflitti tra PR che passano la CI individualmente ma conflittano tra loro.

```
# Senza merge queue:
# PR #1 (CI green) + PR #2 (CI green) → merge entrambe → CONFLITTO!

# Con merge queue:
# PR #1 entra in coda → merge in main
# PR #2 viene rebasata su main aggiornato → CI → merge
# Nessun conflitto possibile

# GitHub: abilitare nelle Branch Protection Rules
# Settings → Branches → Require merge queue
```

### Formattazione Automatica Pre-Commit

Una causa frequente di conflitti "falsi" è la formattazione inconsistente del codice. Due sviluppatori che modificano lo stesso file con stili diversi generano conflitti che non riguardano la logica ma solo gli spazi, le virgole e le parentesi.

```bash
# Configurare un formatter automatico come pre-commit hook
# .husky/pre-commit
npx prettier --write --staged
npx eslint --fix --staged

# Oppure con git config
git config core.autocrlf input    # Normalizzare i line ending
```

### Gitattributes per la Prevenzione

```bash
# .gitattributes — regole di merge per file specifici

# File di lock: mantieni sempre la versione corrente
package-lock.json merge=ours
yarn.lock merge=ours
pnpm-lock.yaml merge=ours
Cargo.lock merge=ours
Gemfile.lock merge=ours

# File generati: non tentare il merge testuale
*.min.js binary
*.min.css binary
dist/** binary

# Normalizzazione line endings per prevenire conflitti spuri
*.js text eol=lf
*.ts text eol=lf
*.json text eol=lf
*.css text eol=lf
*.html text eol=lf
*.md text eol=lf
```

---

## Sparse-Checkout e Branching nei Monorepo

### Problema: Branching in Repository Enormi

Nei monorepo di grandi dimensioni (centinaia di migliaia di file, decine di GB), le operazioni di branching e merge sono penalizzate dalla dimensione del working tree. Uno sviluppatore che lavora su un singolo microservizio non ha bisogno di fare checkout di tutto il repository.

### Sparse-Checkout: Lavorare Solo su Ciò che Serve

```bash
# 1. Clone parziale del repository (senza scaricare tutti i blob)
git clone --filter=blob:none --sparse https://github.com/org/monorepo.git
cd monorepo

# 2. Configurare sparse-checkout in modalità cone (default)
git sparse-checkout init --cone

# 3. Specificare le directory di interesse
git sparse-checkout set services/auth services/shared libs/common

# 4. Verificare la configurazione
git sparse-checkout list
# services/auth
# services/shared
# libs/common

# Il working tree contiene SOLO queste directory
# Ma git log, git blame, git bisect funzionano su TUTTA la cronologia
```

### Branching con Sparse-Checkout

Le operazioni di branching funzionano normalmente con lo sparse-checkout, ma ci sono considerazioni importanti da tenere a mente.

```bash
# Creare un branch: funziona normalmente
git checkout -b feature/auth-refactor

# Merge: funziona, ma attenzione ai conflitti in file fuori dallo sparse-checkout
git checkout main
git merge feature/auth-refactor
# Se il merge tocca file fuori dallo sparse-checkout,
# Git li materializza temporaneamente per risolvere i conflitti

# Aggiungere directory temporaneamente per un merge
git sparse-checkout add services/billing
git merge feature/billing-update
# Opzionalmente, rimuovere dopo il merge
git sparse-checkout set services/auth services/shared libs/common
```

### Partial Clone + Sparse-Checkout + Worktree

La combinazione di queste tre funzionalità è particolarmente potente nei monorepo. Ogni worktree può avere una configurazione sparse-checkout diversa.

```bash
# Clone parziale (base)
git clone --bare --filter=blob:none https://github.com/org/monorepo.git monorepo.git
cd monorepo.git

# Worktree per il team auth
git worktree add ../auth-team main
cd ../auth-team
git sparse-checkout init --cone
git sparse-checkout set services/auth libs/common

# Worktree per il team billing
cd ../monorepo.git
git worktree add ../billing-team main
cd ../billing-team
git sparse-checkout init --cone
git sparse-checkout set services/billing libs/common

# Ogni team vede solo la propria porzione del monorepo
# ma condivide lo stesso object store
```

---

## Git Replace e Grafts: Manipolazione della Cronologia

### Concetti Fondamentali

`git replace` permette di sostituire un qualsiasi oggetto Git (commit, tree, blob, tag) con un altro oggetto dello stesso tipo. A differenza del rebase, che crea nuovi commit, `git replace` crea una sostituzione virtuale che lascia l'oggetto originale intatto. Le sostituzioni sono memorizzate come refs in `refs/replace/` e possono essere condivise tra repository.

```bash
# Sostituire un commit con un altro
git replace <commit-originale> <commit-sostitutivo>

# Listare tutte le sostituzioni
git replace -l

# Rimuovere una sostituzione
git replace -d <commit-originale>

# Creare un oggetto sostitutivo (commit con parent diversi)
git replace --graft <commit> <nuovo-parent-1> [<nuovo-parent-2>...]
```

### Caso d'Uso: Innestare Cronologie Separate

Quando si migra da un altro sistema di versionamento (SVN, Mercurial, Perforce), spesso si importa solo la cronologia recente. `git replace --graft` permette di collegare la cronologia importata alla cronologia precedente senza riscrivere gli hash.

```bash
# Repository A: cronologia vecchia (importata da SVN)
# ultimo commit: OLD_LAST

# Repository B: cronologia nuova (lavoro in Git)
# primo commit: NEW_FIRST (senza parent, è un root commit)

# Collegare le due cronologie
cd repo-nuovo
git remote add old-history ../repo-vecchio
git fetch old-history

# Innestare: NEW_FIRST diventa figlio di OLD_LAST
git replace --graft NEW_FIRST OLD_LAST

# Ora git log mostra la cronologia completa
git log --oneline
# ... commit recenti ...
# NEW_FIRST  Primo commit nel nuovo repo
# OLD_LAST   Ultimo commit dalla migrazione SVN
# ... commit vecchi da SVN ...

# Per rendere la sostituzione permanente:
git filter-branch -- --all
# Oppure con il più moderno git-filter-repo:
# git filter-repo --force
```

### Caso d'Uso: Ridurre la Dimensione del Repository

Per repository con cronologia molto lunga, è possibile usare `git replace` per creare un punto di taglio senza perdere l'accesso alla cronologia completa.

```bash
# Identificare un commit di taglio (es. il primo commit dell'anno corrente)
CUT_POINT=$(git rev-list --after="2026-01-01" --reverse HEAD | head -1)

# Creare un commit shallow (senza parent) con lo stesso tree
git replace --graft $CUT_POINT

# Per gli sviluppatori che non necessitano della cronologia vecchia:
git clone --shallow-since="2026-01-01" https://github.com/org/repo.git

# Per chi necessita della cronologia completa:
git fetch --unshallow
```

### Differenza tra Replace e Graft Legacy

Il vecchio sistema di grafts (`.git/info/grafts`) è deprecato in favore di `git replace --graft`. La differenza principale è che i replace refs sono oggetti Git veri e propri, possono essere condivisi via `git push` e `git fetch`, e sono più robusti.

```bash
# Vecchio sistema (deprecato):
echo "<commit-hash> <nuovo-parent-hash>" >> .git/info/grafts

# Nuovo sistema (raccomandato):
git replace --graft <commit-hash> <nuovo-parent-hash>

# Condividere i replace refs con altri sviluppatori
git push origin 'refs/replace/*'

# Ricevere i replace refs
git fetch origin 'refs/replace/*:refs/replace/*'
```

---

## Ort Strategy: Internals e Performance

### Architettura Interna della Strategia Ort

La strategia ort (Ostensibly Recursive's Twin) è stata riscritta completamente da Elijah Newren come sostituto di `recursive`. A partire da Git 2.50, `recursive` è un sinonimo di `ort` — il vecchio codice non viene più utilizzato.

Le differenze architetturali principali rispetto a `recursive`:

1. **Operazioni in memoria**: ort esegue il merge interamente in memoria senza scrivere file intermedi nel working tree. Questo elimina il costo delle operazioni I/O che rallentavano `recursive` nei repository grandi.

2. **Gestione superiore dei rename**: ort utilizza un algoritmo di rilevamento dei rinominamenti significativamente più efficiente, con complessità O(n log n) invece di O(n²) nei casi peggiori.

3. **Parallelismo**: l'architettura di ort è predisposta per l'esecuzione parallela delle operazioni di confronto dei tree, anche se il parallelismo completo non è ancora implementato in tutte le code path.

### Performance Misurate

I benchmark di GitHub su repository di produzione mostrano miglioramenti significativi:

```
# Benchmark su repository con 100.000+ file
# Strategia recursive:
#   Merge medio: 12.5 secondi
#   P99: 45 secondi
#   Rename detection: 8.2 secondi

# Strategia ort:
#   Merge medio: 1.2 secondi (10x più veloce)
#   P99: 9 secondi (5x più veloce)
#   Rename detection: 0.4 secondi (20x più veloce)
```

Nei test di GitHub su 730.000 istanze di rebase, il tempo totale è passato da 512 ore con la vecchia implementazione a 33 ore con ort — una riduzione del 93%.

### Opzioni Specifiche di Ort

```bash
# Soglia di rilevamento dei rinominamenti
git merge -s ort -X rename-threshold=30 feature
# Abbassare la soglia per rilevare rename con modifiche significative

# Limite dei file da considerare per il rename detection
git merge -s ort -X diff-algorithm=histogram feature
# Usare l'algoritmo histogram per diff più accurati

# Ignorare le differenze di whitespace nei conflitti
git merge -s ort -X ignore-space-change feature
git merge -s ort -X ignore-all-space feature
git merge -s ort -X ignore-space-at-eol feature

# Combinare più opzioni
git merge -s ort \
    -X patience \
    -X rename-threshold=30 \
    -X ignore-space-change \
    feature-branch
```

### Git Replay: Il Successore di Rebase per i Server

Accanto a ort, GitHub ha sviluppato `git replay`, un nuovo sottocomando che esegue operazioni di tipo rebase interamente in memoria, senza necessità di un working tree. Questo è utilizzato internamente da GitHub per le operazioni di merge e rebase lato server.

```bash
# git replay non è ancora un comando user-facing stabile
# ma è disponibile in Git 2.44+
git replay --onto main feature~5..feature

# La differenza con rebase:
# - replay non richiede un working tree
# - replay non aggiorna HEAD o refs
# - replay restituisce gli hash dei nuovi commit su stdout
# - ideale per automazione e scripting server-side
```

---

## Anti-Pattern

### 1. Rebase di Branch Condivisi

Fare rebase di un branch su cui lavorano più sviluppatori riscrive gli hash dei commit. Tutti gli altri sviluppatori si ritrovano con una cronologia divergente e devono fare un merge manuale o un reset. Questo è il peccato capitale del rebasing.

```bash
# SBAGLIATO: rebase di un branch condiviso
git checkout feature-team
git rebase main
git push --force    # Distrugge il lavoro degli altri!

# CORRETTO: merge per branch condivisi
git checkout feature-team
git merge main
git push
```

### 2. Merge Commit Giganti (Big Bang Integration)

Accumulare settimane di sviluppo su branch separati e poi mergiare tutto in una volta produce merge commit enormi con decine di conflitti. L'integrazione diventa un evento traumatico invece che una routine.

```bash
# SBAGLIATO: branch di lunga durata mergiato alla fine
# feature-branch: 150 commit, 3 settimane, 80 file modificati
git merge feature-branch    # 45 conflitti...

# CORRETTO: merge frequenti (almeno giornalieri)
git checkout feature-branch
git merge main              # Ogni giorno, conflitti piccoli e gestibili
```

### 3. Cherry-Pick al Posto di Merge

Usare cherry-pick sistematicamente invece di merge per portare modifiche tra branch crea commit duplicati nella cronologia. Git non riconosce che sono la stessa modifica e può generare conflitti falsi nei merge successivi.

```bash
# SBAGLIATO: cherry-pick seriale
git checkout main
git cherry-pick abc1234
git cherry-pick def5678
git cherry-pick ghi9012    # Duplica 3 commit nella cronologia

# CORRETTO: merge del branch
git checkout main
git merge feature-branch --no-ff
```

### 4. Branch Senza Naming Convention

Branch con nomi come `test`, `fix`, `new`, `temp` non comunicano lo scopo, l'autore o il contesto. In team grandi, diventano indistinguibili e vengono abbandonati.

```bash
# SBAGLIATO
git checkout -b fix
git checkout -b test2
git checkout -b temp-stuff

# CORRETTO: prefisso/contesto
git checkout -b feature/AUTH-123-oauth2-login
git checkout -b bugfix/CORE-456-null-pointer-exception
git checkout -b hotfix/SEC-789-sql-injection
```

### 5. Force Push Senza `--force-with-lease`

`--force` sovrascrive il remote indiscriminatamente. `--force-with-lease` sovrascrive solo se il remote è nello stato atteso. Se qualcuno ha pushato nel frattempo, il push fallisce in sicurezza.

```bash
# SBAGLIATO: force push cieco
git push --force origin feature

# CORRETTO: force push con verifica
git push --force-with-lease origin feature
```

### 6. Non Usare `--no-ff` per Feature Branch

Il fast-forward merge perde la topologia del feature branch nella cronologia. Diventa impossibile distinguere dove un feature branch è iniziato e finito.

```bash
# SBAGLIATO: fast-forward (default)
git merge feature    # Cronologia: A-B-C-D-E-F (lineare, no contesto)

# CORRETTO: merge commit esplicito
git merge --no-ff feature -m "Merge feature: autenticazione OAuth2"
# Cronologia con topologia preservata
```

### 7. Rebase Interattivo Senza Backup

Il rebase interattivo riscrive la cronologia. Se si commette un errore (drop del commit sbagliato, squash errato), il recupero è possibile tramite reflog ma stressante.

```bash
# SBAGLIATO: rebase interattivo direttamente
git rebase -i HEAD~10    # "Oops, ho droppato il commit sbagliato"

# CORRETTO: creare un branch di backup prima
git branch backup/feature-pre-rebase
git rebase -i HEAD~10
# Se qualcosa va storto:
git reset --hard backup/feature-pre-rebase
```

### 8. Merge di Branch con Cronologia Non Correlata Senza `--allow-unrelated-histories`

Tentare di mergiare due repository o branch senza antenato comune senza il flag esplicito fallisce con un errore confuso.

### 9. Non Abilitare `rerere` in Team con Merge Frequenti

Senza `rerere`, lo stesso conflitto viene risolto manualmente ogni volta. In workflow con rebase frequenti o branch di integrazione periodica, questo spreca tempo significativo.

```bash
# Abilitare globalmente
git config --global rerere.enabled true
```

### 10. Octopus Merge per Branch con Conflitti

La strategia octopus non gestisce conflitti manuali. Usarla quando ci sono modifiche sovrapposte risulta in un fallimento silenzioso e confusione.

---

## Best Practices

### Strategia di Branching

1. **Mantenere i branch di feature brevi**: Branch con vita lunga accumulano divergenza e conflitti. Idealmente, un feature branch non dovrebbe durare più di qualche giorno.

2. **Aggiornare frequentemente**: Rebase o merge del branch principale nel feature branch almeno una volta al giorno per minimizzare la divergenza.

3. **Un branch per ogni feature/fix**: Non mischiare modifiche non correlate nello stesso branch. Ogni branch dovrebbe avere un obiettivo chiaro e delimitato.

4. **Naming convention consistente**: Usare prefissi come `feature/`, `bugfix/`, `hotfix/`, `release/` per i branch. Esempio: `feature/oauth2-authentication`.

### Pulizia della Cronologia

1. **Commit atomici**: Ogni commit dovrebbe rappresentare un cambiamento logico completo e auto-consistente. Dovrebbe essere possibile fare revert di un singolo commit senza rompere il sistema.

2. **Messaggi di commit significativi**: Usare il formato Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, ecc.) per messaggi chiari e processabili automaticamente.

3. **Squash dei commit WIP**: Prima di aprire una pull request, usare il rebase interattivo per consolidare commit temporanei come "WIP", "fix typo", "debug".

4. **Non riscrivere la cronologia pubblica**: Una volta che i commit sono stati pushati su un branch condiviso, non usare rebase o force push.

### Merge

1. **Preferire `--no-ff` per feature branch**: I merge commit forniscono contesto storico su quando e cosa è stato integrato.

2. **Abilitare rerere**: Riduce il lavoro ripetitivo nella risoluzione dei conflitti.

3. **Usare merge.conflictstyle zdiff3**: Fornisce più contesto durante la risoluzione dei conflitti.

4. **Verificare il merge prima del push**: Dopo un merge, eseguire i test prima di pushare per assicurarsi che l'integrazione sia corretta.

---

## Troubleshooting

### 1. Merge Fallito con Troppi Conflitti

```bash
# Abortire il merge
git merge --abort

# Strategia alternativa: merge incrementale
# Invece di unire tutto in una volta, unire piccole porzioni
git merge --no-commit feature-branch
# Risolvere i conflitti file per file
git checkout --theirs path/to/file1.js  # Accettare la loro versione
git checkout --ours path/to/file2.js    # Mantenere la nostra versione
git add -A
git commit

# Strategia 2: merge parziale con squash
git merge --squash feature-branch
# Tutti i commit diventano staged, risolvere i conflitti una volta sola
```

### 2. Rebase con Molti Conflitti

```bash
# Se il rebase genera conflitti ad ogni commit:
git rebase --abort

# Alternativa 1: Squash prima, poi rebase
git rebase -i HEAD~10  # Squash i commit in uno solo
git rebase main         # Rebase del singolo commit (un solo conflitto)

# Alternativa 2: merge al posto di rebase
git merge main          # Unico conflitto, non ripetuto per ogni commit

# Alternativa 3: --strategy-option per auto-risolvere
git rebase -X theirs main    # Preferisci la versione di main in caso di conflitto
git rebase -X ours main      # Preferisci la nostra versione
```

### 3. Recupero dopo un Rebase Errato

```bash
# Usare ORIG_HEAD per tornare allo stato pre-rebase
git reset --hard ORIG_HEAD

# Se ORIG_HEAD non è disponibile, usare il reflog
git reflog
# Cercare "rebase (start)" o il commit precedente al rebase
# a1b2c3d HEAD@{0}: rebase (finish)
# ...
# z9y8x7w HEAD@{8}: rebase (start)
# ORIGINAL HEAD@{9}: commit: stato prima del rebase
git reset --hard HEAD@{9}
```

### 4. Detached HEAD Accidentale

```bash
# Sintomo: "You are in 'detached HEAD' state"
# Causa: checkout di un tag, commit hash, o branch remoto

# Se hai fatto commit in detached HEAD:
git branch salvataggio-lavoro    # Salva i commit in un branch
git switch main                  # Torna al branch desiderato
git merge salvataggio-lavoro     # Integra se necessario

# Se non hai fatto commit, semplicemente:
git switch main

# Se hai fatto commit e te ne sei accorto tardi:
git reflog | head -10
# Cercare i commit fatti in detached HEAD
git branch recovery abc1234      # abc1234 = ultimo commit detached
```

### 5. Conflitti Ricorrenti con lo Stesso File

```bash
# Abilitare rerere per registrare le risoluzioni
git config rerere.enabled true

# Verificare che rerere stia funzionando
git rerere status
git rerere diff

# Dimenticare una risoluzione errata
git rerere forget path/to/file.js

# Se un file cambia troppo frequentemente in modo conflittuale,
# considerare la riorganizzazione del codice per ridurre le aree di sovrapposizione
```

### 6. Cherry-Pick che Non Si Applica Pulitamente

```bash
# Usare --strategy-option per gestire i conflitti
git cherry-pick --strategy-option=theirs abc1234

# Oppure applicare come patch
git format-patch -1 abc1234
git apply --3way 0001-*.patch

# Per cherry-pick di un merge commit:
git cherry-pick -m 1 abc1234    # Specifica il parent mainline

# Se il cherry-pick crea conflitti irrisolvibili:
git cherry-pick --abort
# Creare una patch manuale
git diff abc1234~1 abc1234 -- path/to/file.js | git apply
```

### 7. Branch Divergenti dopo Force Push di un Altro Sviluppatore

```bash
# Sintomo: "Your branch and 'origin/feature' have diverged"
# Causa: qualcuno ha fatto force push e la tua copia locale è basata
# sui commit vecchi

# Diagnosi
git log --oneline HEAD..origin/feature    # Commit nel remote che non hai
git log --oneline origin/feature..HEAD    # Commit tuoi che non sono nel remote

# Soluzione 1: Rinunciare ai tuoi commit locali
git reset --hard origin/feature

# Soluzione 2: Rebase i tuoi commit sulla nuova cronologia
git rebase origin/feature

# Soluzione 3: Merge (crea un merge commit)
git merge origin/feature
```

### 8. Merge Undo dopo il Push

```bash
# Sintomo: ho mergiato feature in main e pushato, ma il merge era sbagliato
# NON usare reset perché il push è già avvenuto

# Soluzione: revertire il merge commit
git revert -m 1 <merge-commit-hash>
git push

# ATTENZIONE: dopo il revert, un successivo merge dello stesso branch
# NON porterà le modifiche (Git le considera già integrate)
# Per reintrodurre: revertire il revert
git revert <hash-del-revert>
git merge feature-branch    # Ora funziona
```

### 9. Rebase `--onto` per Spostare una Catena di Commit

```bash
# Sintomo: il feature branch è partito dal branch sbagliato
# e devo spostarlo su un altro branch

# Situazione:
# main:     A---B---C
# develop:       \---D---E
# feature:             \---F---G  (partito da develop per errore)

# Voglio spostare F-G da develop a main
git rebase --onto main develop feature
# Risultato:
# main:     A---B---C---F'---G'
# develop:       \---D---E
```

### 10. Octopus Merge che Fallisce

```bash
# Sintomo: "Merge with strategy octopus failed"
# Causa: la strategia octopus non gestisce conflitti manuali

# Soluzione: merge sequenziali
git merge feature-a
git merge feature-b
git merge feature-c
# Risolvere i conflitti uno alla volta
```

### 11. Branch Protection Impedisce il Push dopo Rebase

```bash
# Sintomo: "remote: error: Cannot force-push to a protected branch"
# Causa: main/develop ha branch protection che impedisce force push

# Soluzione 1: creare una PR (workflow standard)
git push origin feature-branch
# Creare PR da feature-branch a main

# Soluzione 2: se il rebase era su un feature branch tuo
git push --force-with-lease origin feature-branch
# Funziona perché i feature branch non sono protetti (di solito)
```

### 12. Commit Perso durante un Rebase Interattivo

```bash
# Sintomo: ho droppato o squashato il commit sbagliato

# Passo 1: NON fare panic
# Il reflog ha tutto

# Passo 2: trovare il commit nel reflog
git reflog | head -20
# Cercare "rebase (start)" per trovare lo stato pre-rebase
git reset --hard HEAD@{n}    # n = indice dello stato pre-rebase

# Passo 3: riprovare il rebase con più cautela
git branch backup/pre-rebase
git rebase -i main
```

### 13. Merge di Branch con Cronologia Non Correlata

```bash
# Sintomo: "fatal: refusing to merge unrelated histories"
# Causa: i due branch non hanno un antenato comune
# (tipico quando si uniscono due repository separati)

# Soluzione
git merge other-branch --allow-unrelated-histories

# Questo creerà un merge commit con due root commit
# Utile per: unire repo, importare da svn, combinare progetti
```

### 14. Rebase Preservando i Merge Commit

```bash
# Sintomo: il rebase linearizza tutto e perde la topologia dei merge
# Causa: il rebase di default elimina i merge commit

# Soluzione: --rebase-merges (Git 2.18+)
git rebase --rebase-merges main
# Preserva la struttura dei merge nella cronologia rebasata

# Vecchia opzione (deprecata): --preserve-merges
```

### 15. `git merge --squash` Non Crea il Merge Commit

```bash
# Sintomo: dopo git merge --squash, il commit non ha due parent
# Causa: --squash è by design — crea un commit normale, non un merge commit

# Se serve un merge commit con cronologia squashata:
# Opzione 1: usare --squash e accettare il commit non-merge
git merge --squash feature
git commit -m "feat: implementare feature X (squashed)"

# Opzione 2: merge --no-ff per preservare la topologia
git merge --no-ff feature

# Opzione 3: rebase interattivo + merge --no-ff
git checkout feature
git rebase -i main       # Squash/cleanup dei commit
git checkout main
git merge --no-ff feature
```

### 16. Criss-Cross Merge (Più Antenati Comuni)

```bash
# Sintomo: merge produce risultati inattesi o conflitti inspiegabili
# Causa: la cronologia ha un pattern "criss-cross" con più merge base

# Diagnosi: trovare il merge base
git merge-base --all main feature
# Se restituisce più hash, c'è un criss-cross

# Soluzione: la strategia recursive/ort gestisce questo automaticamente
# creando un merge virtuale degli antenati
# Se i risultati sono inattesi, provare con strategia diversa:
git merge -s ort feature
# Oppure risolvere manualmente con --no-commit
git merge --no-commit feature
```

---

## FAQ

### 1. Quando devo usare merge e quando rebase?

**Merge** per branch condivisi e per preservare il contesto storico. **Rebase** per branch locali non condivisi e per pulire la cronologia prima del merge. La regola d'oro: mai fare rebase di commit già pushati e condivisi. Workflow consigliato: rebase locale per aggiornare il feature branch, poi merge `--no-ff` per integrare in main.

### 2. `git merge --squash` è diverso da `git rebase -i` con squash?

Sì. `merge --squash` prende tutte le modifiche del branch e le mette come staged nel branch corrente, pronte per un singolo commit (senza parent merge). `rebase -i` con squash modifica la cronologia del feature branch, unendo i commit selezionati. Il primo perde la cronologia del branch; il secondo la consolida in modo controllato.

### 3. Cosa sono i "virtual merge bases" nella strategia recursive?

Quando due branch hanno più di un antenato comune (pattern criss-cross), Git non può fare un semplice three-way merge. La strategia recursive crea un merge "virtuale" degli antenati comuni prima di procedere. Questo merge virtuale diventa la base per il three-way merge effettivo. Il processo è ricorsivo se i virtual merge base hanno a loro volta più antenati.

### 4. Qual è la differenza tra `--force` e `--force-with-lease`?

`--force` sovrascrive il remote indiscriminatamente, anche se qualcuno ha pushato nel frattempo. `--force-with-lease` verifica che il remote sia nello stato che ti aspetti (basato sull'ultimo fetch); se qualcuno ha pushato nel frattempo, il push fallisce. Sempre preferire `--force-with-lease`.

### 5. Come funziona `git rebase --onto`?

`--onto` permette di spostare una catena di commit da un punto a un altro. La sintassi è `git rebase --onto <newbase> <oldbase> <branch>`. "Prendi i commit di `<branch>` che non sono in `<oldbase>` e riapplicali su `<newbase>`". Utile per spostare un feature branch da develop a main, o per rimuovere commit intermedi.

### 6. Posso annullare un merge dopo il commit ma prima del push?

Sì. `git reset --hard HEAD~1` rimuove il merge commit e riporta HEAD al commit precedente. Sicuro perché il push non è ancora avvenuto. Dopo il push, usare `git revert -m 1 <merge-hash>` perché `reset` richiederebbe un force push.

### 7. Cos'è il "fork point" nel rebase?

Il fork point è il punto in cui il feature branch si è separato dal branch upstream. Git 2.24+ usa l'algoritmo fork-point (basato sul reflog del branch upstream) per determinare automaticamente quali commit riapplicare durante il rebase. Questo è più accurato del semplice merge-base quando il branch upstream è stato rebased o resettato. Disabilitabile con `--no-fork-point`.

### 8. Come faccio a sapere se un branch è stato mergiato?

```bash
# Branch mergiati nel branch corrente
git branch --merged

# Branch NON mergiati
git branch --no-merged

# Branch mergiati in un branch specifico
git branch --merged main

# Verificare un branch specifico
git merge-base --is-ancestor feature main && echo "Mergiato" || echo "Non mergiato"
```

### 9. Che differenza c'è tra la strategia `ort` e `recursive`?

`ort` (Ostensibly Recursive's Twin) è il successore di `recursive`, introdotto in Git 2.33. È riscritto da zero con focus su performance e correttezza. Vantaggi concreti: 3-5x più veloce su repository grandi, gestione superiore dei rename di file, meno edge case con risultati errati. Da Git 2.34+, `ort` è la strategia predefinita.

### 10. Come faccio merge di due branch che hanno file rinominati in modo diverso?

Git rileva automaticamente i rename (basato sulla somiglianza del contenuto). Se la detection fallisce, aumentare la soglia:

```bash
git merge -X rename-threshold=50 feature    # 50% somiglianza
# Default è 50%. Abbassare per essere più aggressivi nel rilevamento
```

### 11. Perché dopo un `git merge --squash` il branch risulta "non mergiato"?

Perché `--squash` non crea un merge commit con due parent. Git non ha modo di sapere che le modifiche sono state integrate. Il branch originale appare ancora in `git branch --no-merged`. Questo è by design: la cronologia dice che il merge non è avvenuto. Dopo il merge squash, cancellare il branch manualmente con `git branch -D feature`.

### 12. Come posso fare cherry-pick di una serie di commit saltandone alcuni?

```bash
# Cherry-pick selettivo
git cherry-pick abc1234 ghi9012 mno3456
# Salta def5678, jkl0123, etc.

# Oppure con range e skip
git cherry-pick abc1234..mno3456
# Se un commit è problematico durante il range:
git cherry-pick --skip
```

### 13. Come funziona `git merge --autostash`?

Git 2.27+ supporta `--autostash` per merge: stasha automaticamente le modifiche locali prima del merge e le riapplica dopo. Utile quando si vuole fare `git pull --rebase` o merge con modifiche locali non committate. Configurabile come default: `git config merge.autoStash true`.

### 14. Come verifico il merge base tra due branch?

```bash
git merge-base main feature
# Restituisce l'hash del commit antenato comune

# Se ci sono più antenati comuni (criss-cross):
git merge-base --all main feature

# Visualizzare nel grafo:
git log --graph --oneline main feature
```

### 15. Posso fare rebase di un branch con merge commit preservando i merge?

Sì, con `--rebase-merges` (Git 2.18+). Questo ricrea la topologia dei merge nella cronologia rebasata. La vecchia opzione `--preserve-merges` è deprecata e meno corretta. Nota: i merge commit riCreati avranno hash diversi dagli originali.

### 16. Cosa succede se due sviluppatori fanno rebase dello stesso branch?

Caos. Il primo che pusha (con `--force-with-lease`) vince. Il secondo sviluppatore si ritrova con una cronologia locale che diverge dal remote. Deve resettare al remote (`git reset --hard origin/branch`) e riapplicare le proprie modifiche. Questo è il motivo per cui la regola d'oro dice "non fare rebase di branch condivisi".

---

## Riferimenti

- **Git Pro Book — Branching and Merging**: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
- **Git Documentation — git-merge**: https://git-scm.com/docs/git-merge
- **Git Documentation — git-rebase**: https://git-scm.com/docs/git-rebase
- **Git Documentation — git-cherry-pick**: https://git-scm.com/docs/git-cherry-pick
- **Git Internals — Git References**: https://git-scm.com/book/en/v2/Git-Internals-Git-References
- **Atlassian — Merging vs Rebasing**: https://www.atlassian.com/git/tutorials/merging-vs-rebasing
- **Git Documentation — rerere**: https://git-scm.com/docs/git-rerere
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Git Documentation — git-format-patch**: https://git-scm.com/docs/git-format-patch

---

## Esercizi

### Esercizio 1: Merge Strategies a Confronto

```bash
# Obiettivo: osservare il comportamento delle diverse strategie di merge

# 1. Creare un repository con due branch divergenti:
git init merge-lab && cd merge-lab
echo "base" > file.txt && git add . && git commit -m "init"
git checkout -b feature
echo "feature line" >> file.txt && git commit -am "feat: add feature"
git checkout main
echo "main line" >> file.txt && git commit -am "fix: main fix"

# 2. Merge con strategia recursive (default):
git merge feature
# Osservare il conflitto — risolverlo manualmente

# 3. Ripetere con --strategy=ours:
git reset --hard HEAD~1
git merge --strategy=ours feature
# Osservare: il contenuto di feature è ignorato completamente

# 4. Ripetere con --no-ff per forzare il merge commit:
git reset --hard HEAD~1
# Risolvere conflitto e:
git merge --no-ff feature

# 5. Confrontare git log --graph --oneline per ciascun caso
```

### Esercizio 2: Rebase Interattivo per Pulizia della Cronologia

```bash
# Obiettivo: pulire una cronologia disordinata prima di una pull request

# 1. Setup con commit disordinati:
git init rebase-lab && cd rebase-lab
echo "v1" > app.txt && git add . && git commit -m "feat: initial app"
echo "v2" >> app.txt && git commit -am "wip: work in progress"
echo "v3" >> app.txt && git commit -am "fix: typo in app"
echo "v4" >> app.txt && git commit -am "feat: add validation"
echo "v5" >> app.txt && git commit -am "wip: debug logging"
echo "v6" >> app.txt && git commit -am "chore: remove debug"

# 2. Usare rebase interattivo per:
#    - squash i commit wip nel commit feat precedente
#    - drop il commit di debug
#    - reword il messaggio del primo commit
# git rebase -i HEAD~5

# 3. Verificare che la cronologia risultante contenga solo commit significativi
# 4. Osservare che gli hash sono cambiati rispetto ai commit originali
# 5. Spiegare perché il rebase crea NUOVI commit
```

### Esercizio 3: Cherry-Pick Selettivo tra Branch

```bash
# Obiettivo: portare un hotfix da main a un release branch senza merge

# 1. Setup:
git init cherry-lab && cd cherry-lab
echo "v1.0" > app.txt && git add . && git commit -m "release: v1.0"
git checkout -b release/1.0

# 2. Aggiungere commit su main:
git checkout main
echo "feature A" >> app.txt && git commit -am "feat: feature A"
echo "hotfix critical" >> app.txt && git commit -am "fix: critical security bug"
echo "feature B" >> app.txt && git commit -am "feat: feature B"

# 3. Cherry-pick SOLO il commit del hotfix su release/1.0:
git checkout release/1.0
git cherry-pick <sha-del-fix>

# 4. Verificare con git log che solo il fix è presente
# 5. Provare cherry-pick con --no-commit per staging senza commit
# 6. Discutere: quando cherry-pick è preferibile a merge?
```

### Esercizio 4: Risoluzione Conflict con rerere

```bash
# Obiettivo: attivare rerere e riusare risoluzioni di conflitti ricorrenti

# 1. Abilitare rerere:
git config --global rerere.enabled true

# 2. Creare un conflitto noto:
git init rerere-lab && cd rerere-lab
echo "original" > config.txt && git add . && git commit -m "init"
git checkout -b dev
echo "dev value" > config.txt && git commit -am "dev: change config"
git checkout main
echo "main value" > config.txt && git commit -am "main: change config"

# 3. Merge e risolvere il conflitto manualmente:
git merge dev
# Risolvere il conflitto, git add, git commit
# rerere memorizza la risoluzione

# 4. Annullare il merge e ripeterlo:
git reset --hard HEAD~1
git merge dev
# Osservare: rerere applica la risoluzione automaticamente

# 5. Verificare con: git rerere status e git rerere diff
```

### Esercizio 5: Workflow Git Flow Completo

```bash
# Obiettivo: simulare un ciclo completo Git Flow

# 1. Setup:
git init gitflow-lab && cd gitflow-lab
echo "v0" > app.txt && git add . && git commit -m "init"
git checkout -b develop

# 2. Feature branch:
git checkout -b feature/login develop
echo "login" >> app.txt && git commit -am "feat: add login"
git checkout develop && git merge --no-ff feature/login

# 3. Release branch:
git checkout -b release/1.0 develop
echo "v1.0" > VERSION && git add . && git commit -m "bump: v1.0"
git checkout main && git merge --no-ff release/1.0
git tag -a v1.0 -m "Release 1.0"
git checkout develop && git merge --no-ff release/1.0

# 4. Hotfix:
git checkout -b hotfix/1.0.1 main
echo "fix" >> app.txt && git commit -am "fix: critical bug"
git checkout main && git merge --no-ff hotfix/1.0.1
git tag -a v1.0.1 -m "Hotfix 1.0.1"
git checkout develop && git merge --no-ff hotfix/1.0.1

# 5. Visualizzare la cronologia completa:
git log --graph --oneline --all --decorate
```

---

## Letture consigliate

- **Git Pro Book — Branching and Merging** — https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging (consultato: 2026-05-24). Trattamento ufficiale delle operazioni di merge e branching in Git.

- **Git Pro Book — Rebasing** — https://git-scm.com/book/en/v2/Git-Branching-Rebasing (consultato: 2026-05-24). Guida approfondita al rebase con regole d'oro e casi d'uso.

- **Atlassian — Merging vs Rebasing** — https://www.atlassian.com/git/tutorials/merging-vs-rebasing (consultato: 2026-05-24). Confronto pratico tra le due strategie con diagrammi chiari.

- **"A successful Git branching model" di Vincent Driessen** — https://nvie.com/posts/a-successful-git-branching-model/ (consultato: 2026-05-24). L'articolo originale che ha definito il Git Flow model.

- **Trunk-Based Development** — https://trunkbaseddevelopment.com/ (consultato: 2026-05-24). Documentazione completa sul trunk-based development come alternativa a Git Flow.

- **Git Documentation — git-rerere** — https://git-scm.com/docs/git-rerere (consultato: 2026-05-24). Documentazione ufficiale del meccanismo di riuso delle risoluzioni dei conflitti.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti Git: staging, commit, DAG | 01 | [01-fondamenti-git.md](01-fondamenti-git.md) |
| Strategie di branching: Git Flow, GitHub Flow, Trunk-Based | 02 | [02-strategie-branching.md](02-strategie-branching.md) |
| Git Internals: oggetti, refs, HEAD | 07 | [07-git-interni-oggetti-refs.md](07-git-interni-oggetti-refs.md) |
| Git Stash, Reset e Recovery (reflog, reset) | 10 | [10-git-stash-reset-recovery.md](10-git-stash-reset-recovery.md) |
| Git Hooks e Automazione (pre-commit, commit-msg) | 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) |
| Workflow di team: code review, CI, protezione branch | 20 | [20-git-workflow-team-guida-completa.md](20-git-workflow-team-guida-completa.md) |
| GitHub Actions CI/CD: automazione merge e deploy | 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **cherry-pick** | Comando Git che applica le modifiche introdotte da un singolo commit su un altro branch, creando un nuovo commit con hash diverso. |
| **conflict marker** | Indicatori (`<<<<<<<`, `=======`, `>>>>>>>`) inseriti da Git nel file quando due branch modificano le stesse righe in modo incompatibile. |
| **fast-forward** | Tipo di merge in cui il branch di destinazione viene semplicemente spostato in avanti al commit del branch sorgente, senza creare un merge commit. Possibile solo se non c'è divergenza. |
| **Git Flow** | Modello di branching proposto da Vincent Driessen che utilizza branch `main`, `develop`, `feature/*`, `release/*` e `hotfix/*` con regole precise di merge. |
| **merge commit** | Commit speciale con due o più parent che rappresenta l'unione di due branch divergenti. Creato automaticamente da `git merge` quando fast-forward non è possibile. |
| **merge strategy** | Algoritmo usato da Git per combinare le modifiche di due branch. Le principali: `ort` (default da Git 2.34), `recursive`, `octopus`, `ours`, `subtree`. |
| **ort** | "Ostensibly Recursive's Twin" — strategia di merge introdotta in Git 2.34 come sostituto più performante di `recursive`. Gestisce meglio rinominamenti e conflitti complessi. |
| **rebase** | Operazione che riapplica i commit di un branch su una nuova base, riscrivendo la cronologia. Produce una storia lineare ma modifica gli hash dei commit. |
| **rebase interattivo** | Modalità di rebase (`git rebase -i`) che permette di riordinare, squashare, modificare o eliminare commit individualmente prima di riapplicarli. |
| **rerere** | "Reuse Recorded Resolution" — funzionalità Git che memorizza le risoluzioni manuali dei conflitti e le riapplica automaticamente quando lo stesso conflitto si ripresenta. |
| **revert** | Comando Git che crea un nuovo commit che annulla le modifiche introdotte da un commit precedente, preservando la cronologia pubblica. |
| **three-way merge** | Algoritmo di merge che confronta le modifiche di due branch rispetto al loro antenato comune (merge base) per determinare il risultato. |
| **Trunk-Based Development** | Modello di branching in cui tutti gli sviluppatori lavorano su un unico branch principale con feature flag, evitando branch di lunga durata. |
| **`--force-with-lease`** | Flag di `git push` che verifica che il remote non sia stato aggiornato da altri prima di sovrascrivere. Alternativa sicura a `--force`. |

---

## Evoluzione della Strategia ORT e git-replay (2025-2026)

La strategia di merge ORT (Ostensibly Recursive's Twin), introdotta come default in Git 2.34, ha continuato a ricevere miglioramenti significativi nelle versioni successive. GitHub ha integrato merge-ort per la gestione dei merge commit nel proprio backend, ottenendo risultati prestazionali notevoli: durante i test condotti su oltre 730.000 istanze, le operazioni di rebase con la precedente implementazione libgit2 hanno richiesto 2,56 ore di tempo di calcolo, mentre con merge-ort lo stesso carico è stato completato in meno di 10 minuti, con un risparmio stimato di circa 479 ore complessive.

L'applicazione di merge-ort ai rebase è stata resa possibile attraverso un nuovo sottocomando sperimentale chiamato `git-replay`, sviluppato da Elijah Newren, l'autore originale di merge-ort. A differenza del rebase tradizionale che opera commit per commit con cherry-pick sequenziali, `git-replay` riapplica intere catene di commit sfruttando direttamente l'engine ORT, garantendo una gestione superiore dei rinominamenti di file e dei conflitti complessi che coinvolgono spostamenti di directory.

```bash
# Esempio concettuale di git-replay (sottocomando sperimentale)
# Riapplica i commit da old-base a HEAD sulla nuova base
git replay --onto new-base old-base..HEAD
```

La transizione a merge-ort è stata articolata in due fasi distinte: la prima ha coperto le operazioni di merge, la seconda le operazioni di rebase. I piani futuri includono l'estensione dell'engine ORT anche alle operazioni di squash e revert, nonché l'esplorazione di nuove funzionalità di prodotto che sfruttino la maggiore accuratezza nella rilevazione dei rinominamenti. Per i team che lavorano su repository di grandi dimensioni con frequenti operazioni di merge e rebase, assicurarsi di utilizzare Git 2.34 o successivo è fondamentale per beneficiare automaticamente di questi miglioramenti prestazionali. La configurazione `merge.conflictStyle = zdiff3`, combinata con ORT, offre inoltre una visualizzazione dei conflitti più chiara che include il contenuto dell'antenato comune, facilitando la risoluzione manuale nei casi in cui l'algoritmo non riesce a procedere automaticamente.|
