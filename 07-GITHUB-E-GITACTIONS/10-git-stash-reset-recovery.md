---
corso: "GitHub e Git Actions"
fase: "1 — Fondamenti Git"
modulo: "10"
titolo: "Git Stash, Reset e Recovery"
versione: "Git 2.47+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti Git"
  - "06 — Git Branching e Merge Avanzato"
  - "07 — Git Internals: Oggetti e Refs"
obiettivi:
  - "Padroneggiare git stash per salvare e recuperare lavoro temporaneo"
  - "Comprendere le differenze tra git reset --soft, --mixed e --hard"
  - "Utilizzare git reflog per recuperare commit apparentemente persi"
  - "Applicare git bisect per identificare il commit che ha introdotto un bug"
  - "Scegliere tra revert e reset in base al contesto (branch pubblico vs privato)"
tag: [git, stash, reset, revert, reflog, bisect, blame, recovery, undo]
---

# Git Stash, Reset e Recovery — Guida Approfondita

> **Modulo 10** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti Git](01-fondamenti-git.md), [Git Branching e Merge Avanzato](06-git-branching-merge-avanzato.md), [Git Internals](07-git-interni-oggetti-refs.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare git stash per salvare e recuperare lavoro temporaneo
> 2. Comprendere le differenze tra git reset `--soft`, `--mixed` e `--hard`
> 3. Utilizzare git reflog per recuperare commit apparentemente persi
> 4. Applicare git bisect per identificare il commit che ha introdotto un bug
> 5. Scegliere tra revert e reset in base al contesto (branch pubblico vs privato)
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **`git stash` e WIP storage; `git stash list/pop/apply/drop`.**
2. **`git reset --soft/mixed/hard`: 3 livelli severity.**
3. **`git reflog` salvataggio dopo "ho fatto reset --hard sbagliato".**
4. **Mai `git push --force` su shared branch; usa `--force-with-lease`.**


## Indice
- [Panoramica](#panoramica)
- [Git Stash: Salvare il Lavoro Temporaneo](#git-stash-salvare-il-lavoro-temporaneo)
- [Git Reset: Manipolazione della Cronologia](#git-reset-manipolazione-della-cronologia)
- [Git Revert: Annullamento Sicuro](#git-revert-annullamento-sicuro)
- [Reflog Recovery: Recupero dei Commit Persi](#reflog-recovery-recupero-dei-commit-persi)
- [Git Bisect: Ricerca Binaria dei Bug](#git-bisect-ricerca-binaria-dei-bug)
- [Git Blame: Tracciamento delle Modifiche](#git-blame-tracciamento-delle-modifiche)
- [Git Log Avanzato](#git-log-avanzato)
- [Git Clean: Rimozione di File Non Tracciati](#git-clean-rimozione-di-file-non-tracciati)
- [Git Switch e Git Restore: Comandi Moderni](#git-switch-e-git-restore-comandi-moderni)
- [Le Tre Aree di Git: Modello Mentale Completo](#le-tre-aree-di-git-modello-mentale-completo)
- [Git Worktree: Sviluppo Parallelo e Isolamento](#git-worktree-sviluppo-parallelo-e-isolamento)
- [Git Rerere: Risoluzione Automatica dei Conflitti](#git-rerere-risoluzione-automatica-dei-conflitti)
- [Git fsck: Verifica dell'Integrità e Recupero Oggetti](#git-fsck-verifica-dellintegrità-e-recupero-oggetti)
- [ORIG_HEAD e Riferimenti Speciali di Git](#orig_head-e-riferimenti-speciali-di-git)
- [Scenari di Disaster Recovery Completi](#scenari-di-disaster-recovery-completi)
- [Tecniche Avanzate di Analisi del Reflog](#tecniche-avanzate-di-analisi-del-reflog)
- [Riferimento Comandi Completo](#riferimento-comandi-completo)
- [Anti-Pattern](#anti-pattern)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Riferimenti](#riferimenti)

---

## Panoramica

La capacità di recuperare da errori, annullare modifiche e investigare la cronologia è ciò che rende Git uno strumento veramente potente per lo sviluppo software. Questa guida esplora in profondità le operazioni di stash per il salvataggio temporaneo del lavoro, le diverse modalità di reset per la manipolazione della cronologia, il revert per annullamenti sicuri, le tecniche di recovery tramite reflog, l'uso di bisect per la ricerca binaria dei bug, blame per il tracciamento delle modifiche e le funzionalità avanzate di git log per l'esplorazione della cronologia.

Comprendere la differenza tra operazioni "distruttive" (come `reset --hard`) e operazioni "sicure" (come `revert`) è fondamentale per lavorare con confidenza. Altrettanto importante è sapere che Git offre reti di sicurezza (come il reflog) che rendono quasi impossibile la perdita definitiva di dati — purché si sappia dove cercare.

---

## Git Stash: Salvare il Lavoro Temporaneo

### Fondamenti dello Stash

Lo stash è un meccanismo per salvare temporaneamente le modifiche non committate (sia staged che unstaged) e ripristinare la working directory allo stato dell'ultimo commit. È implementato internamente come uno stack di commit speciali.

```bash
# Salvare tutte le modifiche nello stash
git stash
# Saved working directory and index state WIP on main: a1b2c3d ultimo commit

# Salvare con un messaggio descrittivo
git stash save "lavoro parziale su autenticazione OAuth2"
# Oppure (sintassi moderna)
git stash push -m "lavoro parziale su autenticazione OAuth2"

# Salvare includendo i file untracked
git stash -u
# Oppure
git stash push --include-untracked

# Salvare includendo anche i file ignorati
git stash -a
# Oppure
git stash push --all

# Salvare solo file specifici
git stash push -m "solo i file CSS" -- src/styles/*.css

# Salvare solo le modifiche staged
git stash push --staged
# Disponibile da Git 2.35
```

### Visualizzare e Ispezionare lo Stash

```bash
# Listare tutti gli stash
git stash list
# stash@{0}: On main: lavoro parziale su autenticazione OAuth2
# stash@{1}: WIP on feature: a1b2c3d implementare login
# stash@{2}: On develop: fix temporaneo CSS

# Visualizzare il diff di uno stash
git stash show
# src/auth.js | 15 +++++++++------
# src/utils.js |  3 +++

# Visualizzare il diff completo
git stash show -p
git stash show -p stash@{1}

# Visualizzare i file nello stash
git stash show --stat stash@{0}

# Visualizzare il contenuto di un file specifico dallo stash
git show stash@{0}:src/auth.js
```

### Ripristinare lo Stash

```bash
# Applicare lo stash più recente (mantiene lo stash nello stack)
git stash apply

# Applicare uno stash specifico
git stash apply stash@{2}

# Applicare e rimuovere dallo stack (pop)
git stash pop

# Pop di uno stash specifico
git stash pop stash@{1}

# Applicare preservando lo stato staged
git stash apply --index
# Ripristina sia le modifiche staged che unstaged come erano originariamente

# Applicare lo stash a un nuovo branch
git stash branch nuovo-branch
# Crea un nuovo branch dal commit dove lo stash è stato creato
# Applica lo stash e lo rimuove dallo stack
# Utile quando lo stash ha conflitti con le modifiche correnti

git stash branch nuovo-branch stash@{2}
```

### Gestire lo Stack

```bash
# Rimuovere uno stash specifico
git stash drop stash@{1}

# Rimuovere lo stash più recente
git stash drop

# Eliminare tutti gli stash
git stash clear

# Creare un branch dallo stash senza rimuoverlo
git checkout -b feature-recuperata stash@{0}
```

### Stash Parziale (Interattivo)

```bash
# Stash interattivo: scegliere quali hunk salvare
git stash push -p
# Git mostra ogni hunk e chiede se salvarlo:
# Stash this hunk [y,n,q,a,d,/,e,?]?
# y = sì, n = no, q = esci, a = tutti rimanenti, d = nessuno rimanente
# s = dividi in hunk più piccoli, e = edita manualmente
```

### Internals dello Stash

Lo stash è implementato come una serie di commit speciali. Ogni stash entry è composta da due o tre commit:

1. **Index commit**: Snapshot della staging area
2. **Working tree commit**: Snapshot della working directory (ha come parent il commit corrente e l'index commit)
3. **Untracked commit** (opzionale): File untracked (se usato `-u` o `-a`)

```bash
# Visualizzare la struttura interna di uno stash
git log --oneline --graph stash@{0}
# *   h7i8j9k WIP on main: a1b2c3d ultimo commit
# |\
# | * d4e5f6g index on main: a1b2c3d ultimo commit
# |/
# * a1b2c3d ultimo commit
```

---

## Git Reset: Manipolazione della Cronologia

### Le Tre Modalità di Reset

Il comando `git reset` è uno degli strumenti più potenti e potenzialmente pericolosi di Git. Opera su tre aree: la cronologia dei commit (HEAD), l'index (staging area) e la working directory. Le tre modalità determinano quali di queste aree vengono modificate.

### Reset --soft

`--soft` sposta solo HEAD al commit specificato. L'index e la working directory rimangono invariati. Le modifiche dai commit "rimossi" appaiono come staged.

```bash
# Annullare l'ultimo commit mantenendo le modifiche staged
git reset --soft HEAD~1

# Scenario: Unire gli ultimi 3 commit in uno
git reset --soft HEAD~3
git commit -m "feat: implementazione completa dell'autenticazione"

# Stato dopo reset --soft:
# HEAD      → spostato al commit specificato
# Index     → invariato (le modifiche restano staged)
# Working   → invariata
```

### Reset --mixed (Default)

`--mixed` (la modalità predefinita) sposta HEAD e resetta l'index al commit specificato. La working directory rimane invariata. Le modifiche appaiono come unstaged.

```bash
# Annullare l'ultimo commit e unstage le modifiche
git reset HEAD~1
# Equivalente a:
git reset --mixed HEAD~1

# Unstage un file specifico (senza spostare HEAD)
git reset HEAD file.js
# Equivalente moderno:
git restore --staged file.js

# Stato dopo reset --mixed:
# HEAD      → spostato al commit specificato
# Index     → resettato al commit specificato
# Working   → invariata (le modifiche sono ora unstaged)
```

### Reset --hard

`--hard` sposta HEAD, resetta l'index E la working directory al commit specificato. **Tutte le modifiche non committate vengono perse definitivamente.**

```bash
# ATTENZIONE: Distruttivo! Perdita di dati non committati!
git reset --hard HEAD~1

# Tornare esattamente allo stato del remote
git reset --hard origin/main

# Scartare tutte le modifiche locali (staged e unstaged)
git reset --hard HEAD

# Stato dopo reset --hard:
# HEAD      → spostato al commit specificato
# Index     → resettato al commit specificato
# Working   → resettata al commit specificato
# MODIFICHE NON COMMITTATE → PERSE
```

### Reset di File Specifici

```bash
# Unstage un file (reset dell'index per quel file)
git reset HEAD -- src/app.js

# Ripristinare un file a una versione specifica nell'index
git reset abc1234 -- src/app.js
# Il file nell'index viene aggiornato, la working directory no
# Per completare il ripristino nella working directory:
git checkout -- src/app.js

# Sintassi moderna con git restore
git restore --staged src/app.js          # Unstage
git restore src/app.js                    # Scartare modifiche locali
git restore --source=abc1234 src/app.js  # Ripristinare da un commit specifico
```

### Tabella Riassuntiva

| Modalità | HEAD | Index | Working Directory | Modifiche |
|----------|------|-------|-------------------|-----------|
| `--soft` | Spostato | Invariato | Invariata | Rimangono staged |
| `--mixed` | Spostato | Resettato | Invariata | Rimangono unstaged |
| `--hard` | Spostato | Resettato | Resettata | **PERSE** |

---

## Git Revert: Annullamento Sicuro

### Fondamenti del Revert

A differenza di `reset`, che riscrive la cronologia, `revert` crea un **nuovo commit** che annulla le modifiche di un commit precedente. Questo è sicuro da usare su branch condivisi perché non modifica la cronologia esistente.

```bash
# Revert di un singolo commit
git revert abc1234
# Git apre l'editor per il messaggio del nuovo commit
# Messaggio predefinito: "Revert "<messaggio del commit originale>""

# Revert senza aprire l'editor
git revert --no-edit abc1234

# Revert senza commit automatico (solo staging)
git revert --no-commit abc1234
# Le modifiche inverse vengono staged ma non committate
# Utile per combinare più revert in un singolo commit
```

### Revert di un Range di Commit

```bash
# Revert di più commit (dal più recente al più vecchio)
git revert abc1234..def5678
# Crea un commit di revert per ogni commit nel range

# Revert di più commit in un singolo commit
git revert --no-commit abc1234..def5678
git commit -m "revert: annullare le modifiche da abc1234 a def5678"

# Revert degli ultimi 3 commit
git revert HEAD~3..HEAD
# Oppure, uno alla volta (ordine inverso)
git revert HEAD HEAD~1 HEAD~2
```

### Revert di un Merge Commit

Il revert di un merge commit richiede la specifica del parent da considerare come "mainline":

```bash
# Revert di un merge commit
git revert -m 1 <merge-commit-hash>
# -m 1 = considerare il primo parent come mainline
# Annulla le modifiche introdotte dal secondo parent (il branch mergiato)

# ATTENZIONE: Dopo il revert di un merge, un successivo merge dello stesso branch
# NON reintrodurrà le modifiche (Git le considera già integrate e poi annullate)
# Per reintrodurre le modifiche, bisogna revertire il revert:
git revert <hash-del-revert-commit>
# Poi il merge funzionerà normalmente
```

### Gestione dei Conflitti nel Revert

```bash
# Se il revert causa conflitti
git revert abc1234
# CONFLICT...

# Risolvere i conflitti e continuare
git add file-risolto.js
git revert --continue

# Oppure abortire
git revert --abort

# Saltare il commit corrente in un range
git revert --skip
```

---

## Reflog Recovery: Recupero dei Commit Persi

### Scenari di Recupero

Il reflog è la rete di sicurezza definitiva di Git. Registra ogni modifica a HEAD e ai branch, permettendo il recupero anche dopo operazioni apparentemente distruttive.

### Recupero dopo Reset --hard

```bash
# Scenario: reset --hard accidentale
git reset --hard HEAD~5  # Oops! 5 commit persi!

# Passo 1: Consultare il reflog
git reflog
# a1b2c3d HEAD@{0}: reset: moving to HEAD~5
# f6g7h8i HEAD@{1}: commit: ultimo commit importante
# j9k0l1m HEAD@{2}: commit: penultimo commit
# ...

# Passo 2: Recuperare tornando al commit precedente
git reset --hard HEAD@{1}
# Oppure usando l'hash direttamente
git reset --hard f6g7h8i
```

### Recupero di Branch Eliminati

```bash
# Scenario: branch eliminato accidentalmente
git branch -D feature-importante

# Passo 1: Trovare l'ultimo commit del branch
git reflog | grep feature-importante
# Oppure cercare nei checkout:
git reflog | grep "checkout: moving from feature-importante"

# Passo 2: Ricreare il branch
git checkout -b feature-importante HEAD@{5}
# Oppure con l'hash trovato
git branch feature-importante abc1234
```

### Recupero dopo Rebase Errato

```bash
# Scenario: rebase che ha causato problemi
git reflog
# Cercare "rebase (start)" e il commit precedente
# a1b2c3d HEAD@{0}: rebase (finish): returning to refs/heads/feature
# d4e5f6g HEAD@{1}: rebase (pick): ultimo commit
# ...
# z9y8x7w HEAD@{8}: rebase (start): checkout main
# ORIGINAL HEAD@{9}: commit: stato prima del rebase

git reset --hard HEAD@{9}
```

### Recupero di Stash Eliminati

```bash
# Scenario: stash eliminato con git stash drop o clear
# Gli stash eliminati sono ancora nell'object database per un periodo

# Trovare gli stash orfani
git fsck --unreachable | grep commit
# Oppure
git fsck --lost-found

# Esaminare i commit trovati
git show <hash>

# Applicare uno stash recuperato
git stash apply <hash>
```

### Navigazione Temporale nel Reflog

```bash
# Trovare lo stato del repository a una data specifica
git reflog --date=iso | grep "2024-01-15"

# Recuperare lo stato di un branch a una data specifica
git checkout 'main@{2024-01-15 14:30:00}'

# Vedere la cronologia di un branch specifico
git reflog show feature-branch

# Differenze tra stati temporali
git diff main@{yesterday} main
git diff main@{1.week.ago} main
```

---

## Git Bisect: Ricerca Binaria dei Bug

### Principio di Funzionamento

`git bisect` implementa una ricerca binaria sulla cronologia dei commit per identificare il commit esatto che ha introdotto un bug. Invece di verificare ogni commit linearmente, bisect dimezza lo spazio di ricerca ad ogni passo, rendendo il processo logaritmico.

```bash
# Avviare bisect
git bisect start

# Marcare il commit corrente come "bad" (contiene il bug)
git bisect bad

# Marcare un commit noto come "good" (non contiene il bug)
git bisect good v1.0.0
# Oppure
git bisect good abc1234

# Git fa checkout del commit a metà strada
# Bisecting: 25 revisions left to test after this (roughly 5 steps)
# [d4e5f6g...] Aggiungere feature X

# Testare e marcare
# Se il bug è presente:
git bisect bad
# Se il bug non è presente:
git bisect good

# Ripetere fino a trovare il commit colpevole
# abc1234 is the first bad commit
# commit abc1234
# Author: ...
# Date: ...
#     Modificare il parser JSON

# Terminare bisect e tornare allo stato originale
git bisect reset
```

### Bisect Automatico

Per bug riproducibili con un test automatico, bisect può essere completamente automatizzato:

```bash
# Bisect automatico con un comando di test
git bisect start HEAD v1.0.0
git bisect run npm test

# Con uno script personalizzato
git bisect start HEAD v1.0.0
git bisect run ./test-bug.sh

# Lo script deve restituire:
# 0 = commit buono (good)
# 1-124, 126-127 = commit cattivo (bad)
# 125 = commit da saltare (skip) — es. non compila

# Esempio di script di test
cat > /tmp/test-bug.sh << 'EOF'
#!/bin/bash
# Tentare la build
make 2>/dev/null || exit 125  # Skip se non compila
# Eseguire il test specifico
./run-specific-test.sh
EOF
chmod +x /tmp/test-bug.sh
git bisect run /tmp/test-bug.sh
```

### Bisect con Termini Personalizzati

```bash
# Usare termini personalizzati invece di good/bad
git bisect start --term-old=fast --term-new=slow

git bisect slow HEAD       # Il commit corrente è lento
git bisect fast v1.0.0     # v1.0.0 era veloce

# Utile per trovare regressioni di performance
git bisect slow  # Questo commit è lento
git bisect fast  # Questo commit è veloce
```

### Bisect: Saltare Commit

```bash
# Saltare un commit che non può essere testato (es. non compila)
git bisect skip

# Saltare un range di commit
git bisect skip abc1234..def5678

# Saltare il commit corrente e i suoi vicini
git bisect skip abc1234 def5678 ghi9012
```

### Visualizzare i Risultati

```bash
# Visualizzare il log del bisect
git bisect log

# Salvare il log per replay
git bisect log > bisect-log.txt

# Replay di un bisect precedente
git bisect replay bisect-log.txt

# Visualizzare i commit rimanenti
git bisect visualize
# Apre gitk con i commit rimanenti nel range
```

---

## Git Blame: Tracciamento delle Modifiche

### Utilizzo Base

```bash
# Vedere chi ha modificato ogni riga di un file
git blame src/app.js
# a1b2c3d4 (Mario Rossi  2024-01-15 10:30:00 +0100  1) import express from 'express';
# d4e5f6g7 (Luigi Bianchi 2024-02-20 14:45:00 +0100  2) import cors from 'cors';

# Blame di un range di righe
git blame -L 10,20 src/app.js
git blame -L 10,+5 src/app.js   # 5 righe a partire dalla 10

# Blame con hash abbreviati
git blame --abbrev=8 src/app.js

# Ignorare le modifiche di whitespace
git blame -w src/app.js

# Seguire le righe copiate da altri file
git blame -C src/app.js

# Seguire le righe copiate da altri file in tutti i commit
git blame -C -C -C src/app.js
```

### Blame Avanzato

```bash
# Blame a partire da un commit specifico (ignorare modifiche recenti)
git blame abc1234 -- src/app.js

# Blame con email invece del nome
git blame -e src/app.js

# Blame con formato personalizzato (porcelain)
git blame --porcelain src/app.js

# Ignorare specifici commit nel blame (es. commit di formattazione)
echo "abc1234" >> .git-blame-ignore-revs
echo "def5678" >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs

# Committare il file ignore per il team
git add .git-blame-ignore-revs
git commit -m "chore: aggiungere commit di formattazione alla blame ignore list"
```

### Configurazione su GitHub

GitHub supporta il file `.git-blame-ignore-revs` nativamente. Aggiungere il file alla root del repository e GitHub lo usa automaticamente nella visualizzazione blame.

---

## Git Log Avanzato

### Formattazione dell'Output

```bash
# Log compatto su una riga
git log --oneline

# Log con grafo ASCII
git log --graph --oneline --all

# Log con decorazioni (branch, tag)
git log --graph --oneline --all --decorate

# Formato personalizzato
git log --format="%h %an %ar %s"
# a1b2c3d Mario Rossi 2 hours ago Aggiungere login

# Formato personalizzato elaborato
git log --format="%C(yellow)%h%C(reset) %C(blue)%an%C(reset) %C(green)%ar%C(reset) %s%C(red)%d%C(reset)"

# Log con statistiche
git log --stat

# Log con diff completo
git log -p

# Log con diff di parole (word diff)
git log -p --word-diff
```

### Filtraggio della Cronologia

```bash
# Per autore
git log --author="Mario Rossi"
git log --author="mario@" # Pattern matching

# Per data
git log --after="2024-01-01" --before="2024-06-30"
git log --since="2 weeks ago"
git log --until="yesterday"

# Per messaggio di commit
git log --grep="autenticazione"
git log --grep="fix:" --grep="bug:" --all-match  # AND
git log --grep="fix:\|bug:"                        # OR

# Per contenuto delle modifiche (pickaxe)
git log -S "functionName"           # Commit che aggiungono/rimuovono la stringa
git log -G "regex_pattern"          # Commit con diff che matchano il regex

# Per file modificato
git log -- src/auth.js
git log -- "*.test.js"

# Commit di merge
git log --merges
git log --no-merges

# Primo parent only (linearizza la cronologia)
git log --first-parent

# Limiti
git log -10                # Ultimi 10 commit
git log --skip=5 -10       # 10 commit dopo i primi 5
```

### Range di Commit

```bash
# Commit in branch-a che non sono in branch-b
git log branch-b..branch-a

# Commit in entrambi i branch che non sono nell'altro (symmetric difference)
git log branch-a...branch-b

# Commit raggiungibili da main ma non da HEAD
git log HEAD..main

# Tutti i commit dal fork point
git log main...feature --left-right
# < = commit solo in main
# > = commit solo in feature
```

### Alias Utili per Git Log

```bash
# Configurare alias per log frequenti
git config --global alias.lg "log --graph --oneline --all --decorate"
git config --global alias.ll "log --oneline -15"
git config --global alias.hist "log --pretty=format:'%C(yellow)%h%Creset %ad | %s%d [%an]' --graph --date=short"
git config --global alias.today "log --since=midnight --oneline --no-merges"
git config --global alias.contributors "shortlog -sn --no-merges"

# Uso
git lg
git ll
git hist
git today
git contributors
```

---

## Git Clean: Rimozione di File Non Tracciati

### Fondamenti di Git Clean

`git clean` rimuove i file non tracciati dalla working directory. A differenza di `git reset` e `git checkout`/`git restore`, che operano su file tracciati, `git clean` è l'unico strumento per eliminare file che Git non conosce (nuovi file, artefatti di build, file temporanei).

```bash
# ATTENZIONE: git clean è irreversibile! Non c'è reflog per i file non tracciati.

# Dry run: mostrare cosa verrebbe eliminato (SEMPRE fare prima)
git clean -n
# Would remove build/output.js
# Would remove temp.log
# Would remove src/experimental.ts

# Equivalente
git clean --dry-run

# Rimuovere i file non tracciati (richiede -f per conferma)
git clean -f

# Rimuovere file non tracciati E directory
git clean -fd

# Rimuovere anche i file ignorati (.gitignore)
git clean -fx
# ATTENZIONE: Elimina anche node_modules/, .env, build/, ecc.

# Rimuovere SOLO i file ignorati (preserva i file non tracciati normali)
git clean -fX
# Utile per "pulire la build" senza perdere file nuovi

# Rimuovere file, directory E file ignorati
git clean -fdx

# Modalità interattiva
git clean -i
# Would remove the following items:
#   build/output.js  temp.log  src/experimental.ts
# *** Commands ***
#   1: clean  2: filter by pattern  3: select by numbers  4: ask each one  5: quit
```

### Opzioni Complete di `git clean`

| Opzione | Descrizione |
|---------|-------------|
| `-n`, `--dry-run` | Mostra cosa verrebbe rimosso senza eseguire |
| `-f`, `--force` | Esegue la rimozione (obbligatorio senza `-i`) |
| `-d` | Include le directory non tracciate |
| `-x` | Include i file ignorati da `.gitignore` |
| `-X` | Rimuove SOLO i file ignorati |
| `-i`, `--interactive` | Modalità interattiva |
| `-e <pattern>`, `--exclude=<pattern>` | Esclude file che matchano il pattern |
| `-q`, `--quiet` | Non mostra i file rimossi |

### Pattern di Esclusione

```bash
# Pulire tutto tranne certi file
git clean -fd -e "*.log" -e "config.local.json"

# Pulire solo una directory specifica
git clean -fd -- src/temp/

# Combinare con git reset per un "hard reset completo"
git reset --hard HEAD
git clean -fdx
# Ora la working directory è identica al commit HEAD
# ATTENZIONE: Questo è l'equivalente di "cancella tutto e ricomincia"
```

### Workflow Comuni

```bash
# 1. Reset completo della working directory (come un clone fresco)
git reset --hard HEAD && git clean -fdx

# 2. Pulire artefatti di build senza toccare configurazioni locali
git clean -fdX

# 3. Verifica pre-commit: assicurarsi che il build funziona da zero
git stash -u                    # Salvare il lavoro
git clean -fdx                  # Pulire tutto
npm install && npm run build    # Ricostruire da zero
git clean -fdx                  # Ripulire
git stash pop                   # Ripristinare il lavoro
```

---

## Git Switch e Git Restore: Comandi Moderni

### Perché Git Switch e Restore

Git 2.23 (agosto 2019) ha introdotto `git switch` e `git restore` per separare le responsabilità del vecchio `git checkout`, che faceva troppe cose: cambiava branch, ripristinava file, creava branch, faceva detached HEAD. I nuovi comandi sono più chiari e sicuri.

```
┌──────────────────────────────────────────────────────────────┐
│              VECCHIO: git checkout (sovraccarico)             │
│                                                              │
│  git checkout main         → cambia branch                   │
│  git checkout -b feature   → crea e cambia branch            │
│  git checkout -- file.js   → ripristina file                 │
│  git checkout abc1234      → detached HEAD                   │
│  git checkout abc1234 -- f → ripristina file da commit       │
│                                                              │
│              NUOVO: Separazione delle responsabilità         │
│                                                              │
│  git switch main           → cambia branch                   │
│  git switch -c feature     → crea e cambia branch            │
│  git restore file.js       → ripristina file                 │
│  git switch --detach abc   → detached HEAD (esplicito)       │
│  git restore --source=abc f→ ripristina file da commit       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Git Switch: Gestione Branch

```bash
# Cambiare branch
git switch main
git switch feature/auth

# Creare un nuovo branch e switchare
git switch -c feature/nuova-feature
# Equivalente vecchio: git checkout -b feature/nuova-feature

# Creare un branch da un commit specifico
git switch -c hotfix/fix-123 abc1234

# Creare un branch da un branch remoto
git switch -c local-branch origin/remote-branch

# Tornare al branch precedente
git switch -
# Equivalente: git checkout -

# Detached HEAD (richiede flag esplicito per sicurezza)
git switch --detach v1.0.0
git switch --detach abc1234

# Forzare switch scartando modifiche locali
git switch -f main
# ATTENZIONE: Perde le modifiche non committate

# Switch con merge delle modifiche locali (default)
git switch main
# Se ci sono conflitti, Git rifiuta lo switch
# Usare stash prima, oppure -f per forzare (scarta le modifiche)
```

### Opzioni Complete di `git switch`

| Opzione | Descrizione |
|---------|-------------|
| `-c <branch>` | Crea un nuovo branch e switcha |
| `-C <branch>` | Crea o resetta un branch e switcha |
| `--detach` | Switch in modalità detached HEAD |
| `-f`, `--force` | Forza lo switch scartando le modifiche locali |
| `--discard-changes` | Alias per `--force` |
| `-m`, `--merge` | Merge le modifiche locali con il nuovo branch |
| `--orphan <branch>` | Crea un branch orfano (senza cronologia) |
| `-t`, `--track` | Configura il tracking del branch remoto |
| `--no-track` | Non configurare il tracking |
| `--guess` / `--no-guess` | Indovinare il branch remoto (default: attivo) |
| `-q`, `--quiet` | Sopprime i messaggi di output |

### Git Restore: Ripristino File

```bash
# Ripristinare un file dalla staging area (scarta le modifiche nella working directory)
git restore src/app.js
# Equivalente vecchio: git checkout -- src/app.js

# Ripristinare più file
git restore src/app.js src/utils.js
git restore src/*.js

# Ripristinare tutti i file modificati
git restore .

# Unstage un file (rimuovere dalla staging area)
git restore --staged src/app.js
# Equivalente vecchio: git reset HEAD src/app.js

# Unstage tutti i file
git restore --staged .

# Ripristinare sia staged che working directory
git restore --staged --worktree src/app.js

# Ripristinare da un commit specifico
git restore --source=abc1234 src/app.js
# Il file nella working directory diventa come era nel commit abc1234

# Ripristinare dall'index (staging area) nella working directory
git restore --source=HEAD~3 --staged --worktree src/app.js

# Ripristinare un file cancellato
git restore --source=HEAD~1 file-cancellato.js

# Ripristinare interattivamente (per hunk)
git restore -p src/app.js
# Mostra ogni hunk e chiede se ripristinarlo
```

### Opzioni Complete di `git restore`

| Opzione | Descrizione |
|---------|-------------|
| `-s <source>`, `--source=<tree>` | Specifica il tree da cui ripristinare |
| `-S`, `--staged` | Ripristina nell'index (staging area) |
| `-W`, `--worktree` | Ripristina nella working directory (default) |
| `-p`, `--patch` | Ripristino interattivo per hunk |
| `--ours` | Usa la versione "nostra" durante un conflitto |
| `--theirs` | Usa la versione "loro" durante un conflitto |
| `-m`, `--merge` | Ricrea il conflitto nell'index |
| `--conflict=<style>` | Stile conflitto: merge, diff3, zdiff3 |
| `--ignore-unmerged` | Ignora i file non mergiati |
| `-q`, `--quiet` | Sopprime i messaggi di output |

### Mapping Vecchio → Nuovo

| Vecchio (`checkout` / `reset`) | Nuovo (`switch` / `restore`) |
|-------------------------------|------------------------------|
| `git checkout main` | `git switch main` |
| `git checkout -b feat` | `git switch -c feat` |
| `git checkout -- file.js` | `git restore file.js` |
| `git checkout abc1234 -- file.js` | `git restore --source=abc1234 file.js` |
| `git checkout abc1234` | `git switch --detach abc1234` |
| `git reset HEAD file.js` | `git restore --staged file.js` |
| `git reset HEAD` | `git restore --staged .` |
| `git checkout -p file.js` | `git restore -p file.js` |

---

## Le Tre Aree di Git: Modello Mentale Completo

Comprendere le tre aree di Git è essenziale per padroneggiare `reset`, `restore`, `stash` e `clean`. Ogni operazione agisce su una o più di queste aree.

```
┌───────────────────────────────────────────────────────────────────────┐
│                     LE TRE AREE DI GIT                                │
│                                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────┐          │
│  │  WORKING     │    │   INDEX      │    │   REPOSITORY     │          │
│  │  DIRECTORY   │    │  (STAGING)   │    │   (HEAD)         │          │
│  │             │    │             │    │                  │          │
│  │  I file che │    │  Snapshot   │    │  Cronologia dei  │          │
│  │  vedi e     │    │  del        │    │  commit          │          │
│  │  modifichi  │    │  prossimo   │    │  (immutabile*)   │          │
│  │             │    │  commit     │    │                  │          │
│  └──────┬──────┘    └──────┬──────┘    └────────┬─────────┘          │
│         │                  │                    │                     │
│         │   git add ──────►│                    │                     │
│         │                  │   git commit ─────►│                     │
│         │                  │                    │                     │
│         │◄── git restore ──│                    │                     │
│         │                  │◄── git restore ────│                     │
│         │                  │     --staged       │                     │
│         │                  │                    │                     │
│         │◄────────── git reset --hard ──────────│                     │
│         │                  │◄── git reset ──────│                     │
│         │                  │    --mixed (default)│                     │
│         │                  │                    │◄─ git reset --soft  │
│         │                  │                    │                     │
│         │──── git stash ──────────────────────►│ (stash refs)        │
│         │◄── git stash pop ───────────────────│                     │
│         │                  │                    │                     │
│  git clean ──► /dev/null   │                    │                     │
│  (file non                 │                    │                     │
│   tracciati)               │                    │                     │
│                                                                       │
│  * I commit sono immutabili, ma HEAD e i branch possono muoversi     │
└───────────────────────────────────────────────────────────────────────┘
```

### Mappa delle Operazioni sulle Tre Aree

```
┌────────────────────────────────────────────────────────────────┐
│               EFFETTO DI OGNI COMANDO                          │
│                                                                │
│  Comando                   │ Working │ Index │ HEAD/Commits    │
│  ──────────────────────────┼─────────┼───────┼────────────     │
│  git add                   │    —    │  ✏️   │     —           │
│  git commit                │    —    │   —   │    ✏️           │
│  git reset --soft           │    —    │   —   │    ✏️           │
│  git reset --mixed (def.)  │    —    │  ✏️   │    ✏️           │
│  git reset --hard          │   ✏️   │  ✏️   │    ✏️           │
│  git restore <file>        │   ✏️   │   —   │     —           │
│  git restore --staged      │    —    │  ✏️   │     —           │
│  git restore --staged -W   │   ✏️   │  ✏️   │     —           │
│  git stash                 │   ✏️   │  ✏️   │     —           │
│  git stash pop             │   ✏️   │  ✏️   │     —           │
│  git clean                 │   🗑️   │   —   │     —           │
│  git revert                │   ✏️   │  ✏️   │    ✏️ (nuovo)  │
│  git checkout -- <file>    │   ✏️   │   —   │     —           │
│  git switch <branch>       │   ✏️   │  ✏️   │    ✏️ (HEAD)   │
│                                                                │
│  ✏️ = modificato    🗑️ = rimosso    — = non toccato             │
└────────────────────────────────────────────────────────────────┘
```

---

## Git Worktree: Sviluppo Parallelo e Isolamento

### Concetto Fondamentale

`git worktree` consente di avere **molteplici directory di lavoro** collegate allo stesso repository Git. Ogni worktree ha il proprio HEAD, il proprio index e la propria working directory, ma condivide l'object database, i refs (branch e tag), la configurazione e gli stash con il repository principale. Questo permette di lavorare su più branch contemporaneamente senza dover clonare il repository più volte, risparmiando spazio su disco e mantenendo una singola fonte di verità per gli oggetti Git.

Introdotto in Git 2.5 (luglio 2015), il comando ha ricevuto miglioramenti significativi nelle versioni recenti:

- **Git 2.46** (luglio 2024): aggiunto `worktree.useRelativePaths` e il flag `--relative-paths` per utilizzare percorsi relativi nei link interni tra worktree e repository principale.
- **Git 2.48** (gennaio 2025): `git worktree repair` corregge automaticamente i mismatch tra percorsi assoluti e relativi.

### Creazione e Gestione dei Worktree

```bash
# Creare un worktree per un branch esistente
git worktree add ../hotfix-directory hotfix/critical-fix
# Crea una directory ../hotfix-directory con il branch hotfix/critical-fix checked out

# Creare un worktree con un nuovo branch
git worktree add -b feature/nuova-feature ../feature-dir main
# Crea un nuovo branch feature/nuova-feature basato su main
# e lo checka out nella directory ../feature-dir

# Creare un worktree in stato detached HEAD
git worktree add --detach ../test-dir v2.0.0
# Utile per testare un tag o un commit specifico senza creare un branch

# Listare tutti i worktree attivi
git worktree list
# /home/user/progetto           a1b2c3d [main]
# /home/user/hotfix-directory   d4e5f6g [hotfix/critical-fix]
# /home/user/feature-dir        h7i8j9k [feature/nuova-feature]

# Listare con formato dettagliato
git worktree list --porcelain

# Rimuovere un worktree (dopo aver finito il lavoro)
git worktree remove ../hotfix-directory
# Rimuove la directory e la registrazione del worktree

# Rimuovere forzatamente (se ci sono modifiche non committate)
git worktree remove --force ../hotfix-directory

# Pulire i worktree orfani (directory cancellate manualmente)
git worktree prune
# Rimuove le registrazioni di worktree la cui directory non esiste più

# Riparare i percorsi dopo spostamento del repository
git worktree repair
# Corregge i link interni tra worktree e repository principale
```

### Pattern: Bare Repository con Worktree

Il pattern raccomandato per lavorare esclusivamente con worktree è il **bare repository**, che contiene solo i dati Git senza una working directory propria. Questo evita confusione tra il worktree "principale" e quelli secondari.

```bash
# Clonare come bare repository
git clone --bare https://github.com/user/project.git project.git
cd project.git

# Configurare il fetch per includere tutti i branch remoti
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin

# Creare worktree per ogni contesto di lavoro
git worktree add ../project-main main
git worktree add ../project-develop develop
git worktree add ../project-hotfix hotfix/urgent-fix

# Struttura risultante:
# project.git/          ← bare repo (solo dati Git)
# project-main/         ← worktree per main
# project-develop/      ← worktree per develop
# project-hotfix/       ← worktree per hotfix
```

### Workflow Pratico: Hotfix Durante lo Sviluppo di una Feature

Scenario: si sta lavorando su una feature complessa quando arriva una segnalazione di bug critico in produzione. Senza worktree, bisognerebbe stashare il lavoro, cambiare branch, fare l'hotfix, tornare al branch della feature e ripristinare lo stash. Con worktree, il processo è più pulito e privo di rischi.

```bash
# Stato iniziale: si sta lavorando su feature/auth-oauth2
# con molte modifiche non committate

# Passo 1: Creare un worktree per l'hotfix (senza toccare il lavoro corrente)
git worktree add -b hotfix/fix-login-crash ../hotfix-login origin/main
# Il lavoro sulla feature rimane intatto nella directory corrente

# Passo 2: Spostarsi nel worktree dell'hotfix
cd ../hotfix-login

# Passo 3: Implementare, testare e committare l'hotfix
vim src/auth/login.js       # Correggere il bug
npm test                     # Testare
git add src/auth/login.js
git commit -m "fix: risolvere crash durante il login con credenziali vuote"
git push origin hotfix/fix-login-crash

# Passo 4: Tornare al lavoro sulla feature
cd ../progetto-originale     # La feature è esattamente come l'avevi lasciata

# Passo 5: Rimuovere il worktree dell'hotfix quando il merge è completato
git worktree remove ../hotfix-login
git branch -d hotfix/fix-login-crash
```

### Avvertenza Critica: Stash Globale nei Worktree

Lo stash in Git è **globale** — `refs/stash` è un singolo reflog condiviso tra tutti i worktree dello stesso repository. Questo significa che uno stash creato in un worktree è visibile e applicabile da qualsiasi altro worktree.

```bash
# PERICOLO: Race condition sullo stash condiviso
# Worktree A (feature/auth):
git stash push -m "lavoro auth parziale"     # Diventa stash@{0}

# Worktree B (hotfix/login):
git stash push -m "esperimento hotfix"        # Diventa stash@{0}
                                               # Il precedente diventa stash@{1}

# Worktree A:
git stash pop                                  # POP di stash@{0} che è
                                               # "esperimento hotfix", NON
                                               # "lavoro auth parziale"!

# SOLUZIONE: Non usare stash quando si lavora con più worktree in parallelo
# Usare commit temporanei su branch WIP invece dello stash

# Pattern sicuro con worktree:
git add -A && git commit -m "wip: salvataggio temporaneo stato auth"
# Quando si riprende:
git reset --soft HEAD~1    # Rimuove il commit WIP, mantiene le modifiche staged
```

### Opzioni Complete di `git worktree`

| Sottocomando / Opzione | Descrizione |
|------------------------|-------------|
| `add <path> [<branch>]` | Crea un nuovo worktree e checka out il branch |
| `add -b <new-branch> <path> [<start>]` | Crea un nuovo branch e worktree |
| `add --detach <path> <commit>` | Crea un worktree in stato detached HEAD |
| `list` | Mostra tutti i worktree registrati |
| `list --porcelain` | Output in formato machine-readable |
| `remove <worktree>` | Rimuove un worktree |
| `remove --force <worktree>` | Rimuove un worktree anche con modifiche pendenti |
| `prune` | Rimuove le registrazioni di worktree orfani |
| `prune --dry-run` | Mostra cosa verrebbe rimosso senza eseguire |
| `repair [<path>...]` | Ripara i link interni tra worktree e repository |
| `lock <worktree>` | Blocca un worktree per impedire la rimozione con prune |
| `unlock <worktree>` | Sblocca un worktree precedentemente bloccato |
| `move <worktree> <new-path>` | Sposta un worktree in un nuovo percorso |

---

## Git Rerere: Risoluzione Automatica dei Conflitti

### Principio di Funzionamento

`git rerere` (acronimo di **Re**use **Re**corded **Re**solution) è un meccanismo che consente a Git di **memorizzare come sono stati risolti i conflitti di merge** e di **riapplicare automaticamente** le stesse risoluzioni quando lo stesso conflitto si ripresenta. È particolarmente utile in workflow con branch a lunga vita che vengono periodicamente mergiati o rebasati.

Internamente, rerere salva le risoluzioni nella directory `.git/rr-cache/`, dove ogni conflitto è identificato da un hash calcolato dal contenuto delle due versioni in conflitto (indipendente dal commit o dal branch). Quando Git incontra un conflitto con lo stesso hash, applica automaticamente la risoluzione precedente.

### Abilitare Rerere

```bash
# Abilitare rerere globalmente
git config --global rerere.enabled true

# Abilitare solo per il repository corrente
git config rerere.enabled true

# Abilitare anche l'auto-staging dopo la risoluzione automatica
git config --global rerere.autoupdate true
# Con autoupdate, Git aggiunge automaticamente i file risolti allo staging
# Senza autoupdate, bisogna fare git add manualmente dopo ogni risoluzione

# Verificare la configurazione
git config rerere.enabled
# true

# La directory della cache si trova in:
ls .git/rr-cache/
# Contiene una sottodirectory per ogni conflitto registrato
```

### Workflow con Rerere

```bash
# Scenario: branch feature-a che viene periodicamente rebasato su main

# Primo merge/rebase — conflitto manuale
git checkout feature-a
git rebase main
# CONFLICT (content): Merge conflict in src/config.js
# Recorded preimage for 'src/config.js'   ← rerere ha registrato il conflitto

# Risolvere il conflitto manualmente
vim src/config.js
git add src/config.js
git rebase --continue
# Recorded resolution for 'src/config.js'. ← rerere ha salvato la risoluzione

# Secondo rebase (settimana successiva) — conflitto identico
git rebase main
# CONFLICT (content): Merge conflict in src/config.js
# Resolved 'src/config.js' using previous resolution. ← AUTOMATICO!

# Con rerere.autoupdate=true, il file è già staged
# Senza autoupdate:
git add src/config.js
git rebase --continue
```

### Gestione della Cache Rerere

```bash
# Visualizzare le risoluzioni registrate
git rerere status
# src/config.js

# Visualizzare il diff della risoluzione registrata
git rerere diff
# Mostra la differenza tra il conflitto e la risoluzione

# Dimenticare una risoluzione specifica (se era sbagliata)
git rerere forget src/config.js
# Elimina la risoluzione memorizzata per quel file
# Al prossimo conflitto, Git chiederà di nuovo la risoluzione manuale

# Dimenticare tutte le risoluzioni (reset completo della cache)
rm -rf .git/rr-cache/*

# Pulire le risoluzioni vecchie (default: 15 giorni per non risolte, 60 per risolte)
git rerere gc
```

### Caso d'Uso Avanzato: Testing di Merge Pre-Release

Rerere è particolarmente potente in workflow dove si testano merge di integrazione che poi vengono annullati e rifatti al momento del rilascio effettivo.

```bash
# Merge di test per verificare la compatibilità
git checkout integration-test
git merge feature-a         # Risolvere i conflitti → rerere registra
git merge feature-b         # Risolvere i conflitti → rerere registra
git merge feature-c         # Nessun conflitto

# Testare l'integrazione
npm test
# I test passano → le feature sono compatibili

# Annullare il merge di test
git reset --hard origin/integration-test

# Al momento del rilascio effettivo (giorni/settimane dopo):
git checkout release
git merge feature-a         # Conflitti risolti AUTOMATICAMENTE da rerere
git merge feature-b         # Conflitti risolti AUTOMATICAMENTE da rerere
git merge feature-c         # Nessun conflitto

# Zero lavoro manuale ripetuto!
```

---

## Git fsck: Verifica dell'Integrità e Recupero Oggetti

### Panoramica di git fsck

`git fsck` (acronimo di **f**ile **s**ystem **c**hec**k**) verifica l'integrità dell'object database di Git e identifica oggetti corrotti, dangling (orfani) o mancanti. È lo strumento di ultima istanza per il recupero di dati quando il reflog non è sufficiente — ad esempio quando il reflog è scaduto, il repository è stato clonato di recente, o si cerca un oggetto che non è mai stato puntato da un branch.

### Tipi di Oggetti Problematici

```
┌──────────────────────────────────────────────────────────────────────┐
│                  TIPI DI OGGETTI IN GIT FSCK                         │
│                                                                      │
│  DANGLING (Orfani):                                                  │
│    Oggetti validi che non sono raggiungibili da nessun                │
│    branch, tag, reflog o altro riferimento.                          │
│    Cause comuni: reset --hard, drop di stash, rebase,                │
│    branch eliminati.                                                 │
│                                                                      │
│  UNREACHABLE:                                                        │
│    Oggetti non raggiungibili da nessun branch o tag,                 │
│    ma possibilmente ancora nel reflog.                               │
│    Con --no-reflogs diventano "dangling".                            │
│                                                                      │
│  MISSING:                                                            │
│    Oggetti referenziati da altri oggetti ma assenti                  │
│    dall'object database. Indica corruzione.                          │
│                                                                      │
│  CORRUPT:                                                            │
│    Oggetti il cui contenuto non corrisponde all'hash SHA.            │
│    Indica corruzione del disco o della rete.                         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Comandi fsck Fondamentali

```bash
# Verifica base dell'integrità
git fsck
# Checking object directories: 100% (256/256), done.
# dangling commit a1b2c3d4e5f6...
# dangling blob d4e5f6g7h8i9...

# Verifica completa (include tutti i pack file)
git fsck --full
# Più lento ma più approfondito

# Mostrare tutti gli oggetti non raggiungibili
git fsck --unreachable
# unreachable commit a1b2c3d...
# unreachable blob d4e5f6g...
# unreachable tree h7i8j9k...

# Mostrare oggetti non raggiungibili ignorando il reflog
# (tratta gli oggetti nel reflog come non raggiungibili)
git fsck --unreachable --no-reflogs
# Mostra anche gli oggetti che il reflog tiene in vita

# Scrivere gli oggetti orfani nella directory lost-found
git fsck --lost-found
# I commit orfani vanno in .git/lost-found/commit/
# I blob orfani vanno in .git/lost-found/other/

# Verificare la connettività degli oggetti
git fsck --connectivity-only
# Più veloce: verifica solo che gli oggetti referenziati esistano
# Senza verificare il contenuto di ogni oggetto

# Verifica in modalità silenziosa (solo errori)
git fsck --no-dangling
# Non mostra i dangling object, solo gli errori veri

# Contare gli oggetti non raggiungibili senza elencarli
git fsck --unreachable 2>&1 | grep -c "unreachable"
```

### Walkthrough: Recupero di Stash Eliminati Tramite fsck

Quando uno stash viene eliminato con `git stash drop` o `git stash clear`, il reflog dello stash viene aggiornato ma gli oggetti commit rimangono nell'object database finché la garbage collection non li rimuove. Questa finestra temporale consente il recupero.

```bash
# Scenario: tutti gli stash sono stati eliminati accidentalmente
git stash clear
# Oops! Lo stash con il lavoro di 3 ore è sparito!

# Passo 1: NON eseguire git gc — preservare gli oggetti orfani

# Passo 2: Trovare i commit di stash orfani
git fsck --unreachable | grep commit
# unreachable commit a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
# unreachable commit q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
# unreachable commit g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8

# Passo 3: Identificare quali sono stash (i merge commit con 2-3 parent)
git fsck --unreachable | grep commit | cut -d' ' -f3 | \
  xargs git log --merges --no-walk --oneline
# a1b2c3d WIP on feature: abc1234 implementare autenticazione
# g3h4i5j WIP on main: def5678 aggiornare dipendenze

# Passo 4: Esaminare il contenuto del commit di stash
git show a1b2c3d
# Verifica che sia lo stash cercato

# Passo 5: Visualizzare il diff
git stash show -p a1b2c3d
# Oppure:
git diff a1b2c3d^..a1b2c3d

# Passo 6: Recuperare lo stash
git stash apply a1b2c3d
# Le modifiche dello stash sono ripristinate nella working directory

# Oppure: salvare come nuovo stash
git stash store -m "recuperato: lavoro autenticazione" a1b2c3d
git stash list
# stash@{0}: recuperato: lavoro autenticazione
```

### Walkthrough: Recupero di Commit dopo Reflog Scaduto

Quando il reflog è scaduto (default: 30 giorni per oggetti non raggiungibili, 90 giorni per raggiungibili), i commit persi non appaiono più in `git reflog` ma possono ancora esistere nell'object database.

```bash
# Scenario: un reset --hard fatto 60 giorni fa, reflog scaduto

# Passo 1: Cercare commit non raggiungibili con fsck
git fsck --full --no-reflogs --unreachable | grep commit > /tmp/lost-commits.txt
wc -l /tmp/lost-commits.txt
# 147 commit non raggiungibili trovati

# Passo 2: Filtrare per data approssimativa
while read line; do
    hash=$(echo "$line" | awk '{print $3}')
    date=$(git show -s --format=%ci "$hash" 2>/dev/null)
    echo "$date $hash"
done < /tmp/lost-commits.txt | sort -r | head -20
# 2025-03-15 14:30:00 +0100 a1b2c3d...  ← Probabile candidato
# 2025-03-15 14:25:00 +0100 d4e5f6g...
# 2025-03-14 09:10:00 +0100 h7i8j9k...

# Passo 3: Esaminare i candidati
git show a1b2c3d --stat
# Verifica file modificati e messaggio di commit

# Passo 4: Visualizzare la cronologia del commit trovato
git log --oneline a1b2c3d | head -10
# Verifica che la catena di commit sia coerente

# Passo 5: Recuperare creando un branch
git branch recuperato a1b2c3d
git log --oneline recuperato | head -10
# Il branch "recuperato" ora punta alla cronologia completa
```

### Verifica dell'Integrità dopo Sospetti di Corruzione

```bash
# Scenario: sospetto di corruzione dopo crash del disco, power failure
# o trasferimento di rete interrotto

# Passo 1: Verifica completa
git fsck --full --strict 2>&1 | tee /tmp/fsck-report.txt
# --strict abilita controlli addizionali

# Passo 2: Interpretare i risultati
grep -E "(missing|broken|corrupt)" /tmp/fsck-report.txt
# missing blob a1b2c3d...  ← Un file è corrotto/mancante
# broken link from commit d4e5f6g to tree h7i8j9k  ← Connessione rotta

# Passo 3: Se ci sono oggetti mancanti, tentare il recupero dal remote
git fetch origin
git fsck --full   # Ri-verificare dopo il fetch

# Passo 4: Se la corruzione persiste, ricostruire dall'ultimo clone buono
# Salvare le modifiche locali prima:
git format-patch origin/main --stdout > /tmp/local-patches.txt
# Poi ri-clonare e riapplicare:
cd ..
git clone https://github.com/user/project.git project-clean
cd project-clean
git am /tmp/local-patches.txt
```

---

## ORIG_HEAD e Riferimenti Speciali di Git

### Cos'è ORIG_HEAD

`ORIG_HEAD` è un riferimento speciale che Git crea automaticamente prima di operazioni potenzialmente distruttive. Salva la posizione di HEAD prima dell'operazione, fornendo un "punto di ripristino" immediato. È l'equivalente di un "Ctrl+Z" a livello di Git.

### Comandi che Impostano ORIG_HEAD

| Comando | Quando ORIG_HEAD viene impostato |
|---------|----------------------------------|
| `git merge` | Prima di eseguire il merge |
| `git rebase` | Prima di iniziare il rebase |
| `git reset` | Prima di spostare HEAD |
| `git am` | Prima di applicare le patch |
| `git pull` | Prima del merge implicito (in pull con merge) |

```bash
# Esempio pratico: annullare un merge tramite ORIG_HEAD
git merge feature-branch
# Il merge ha introdotto problemi
git reset --hard ORIG_HEAD
# HEAD torna alla posizione pre-merge

# Esempio: annullare un rebase
git rebase main
# Il rebase ha causato troppi conflitti
git rebase --abort           # Durante il rebase
# Oppure dopo il completamento:
git reset --hard ORIG_HEAD   # Torna allo stato pre-rebase

# Esempio: annullare un reset
git reset --hard HEAD~3
# Ops, troppi commit rimossi
git reset --hard ORIG_HEAD
# Torna allo stato prima del primo reset

# ATTENZIONE: ORIG_HEAD ricorda UN SOLO passo indietro
# Ogni nuova operazione distruttiva sovrascrive il precedente ORIG_HEAD
git merge feature-a           # ORIG_HEAD = stato prima del merge di feature-a
git merge feature-b           # ORIG_HEAD = stato prima del merge di feature-b
                               # Lo stato pre-merge di feature-a è PERSO da ORIG_HEAD
                               # (ma è ancora nel reflog)
```

### Altri Riferimenti Speciali di Git

Git mantiene diversi riferimenti speciali oltre a ORIG_HEAD, ciascuno con un ruolo specifico durante le operazioni in corso:

```bash
# MERGE_HEAD: il commit che viene mergiato
# Esiste solo durante un merge in corso (con conflitti non risolti)
cat .git/MERGE_HEAD            # Hash del commit in fase di merge
# Viene eliminato dopo git merge --continue o git merge --abort

# REBASE_HEAD: il commit che sta per essere applicato nel rebase corrente
cat .git/REBASE_HEAD           # Hash del commit in corso di replay
# Esiste solo durante un rebase interattivo con conflitti

# CHERRY_PICK_HEAD: il commit che sta per essere cherry-pickato
cat .git/CHERRY_PICK_HEAD      # Hash del commit in fase di cherry-pick
# Esiste solo durante un cherry-pick con conflitti

# REVERT_HEAD: il commit che sta per essere revertito
cat .git/REVERT_HEAD           # Hash del commit in fase di revert
# Esiste solo durante un revert con conflitti

# FETCH_HEAD: l'ultimo fetch eseguito
cat .git/FETCH_HEAD            # Risultati dell'ultimo git fetch
# Contiene il branch e l'hash fetchati

# HEAD: il commit o branch corrente
cat .git/HEAD
# ref: refs/heads/main          ← Punta a un branch (normale)
# a1b2c3d4e5f6g7h8i9j0...     ← Punta a un commit (detached HEAD)
```

### Utilizzare ORIG_HEAD nel Workflow Quotidiano

```bash
# Pattern sicuro per operazioni rischiose:
# 1. Annotare lo stato corrente
echo "Pre-operazione: $(git rev-parse HEAD)" >> /tmp/git-safety.log

# 2. Eseguire l'operazione
git rebase -i main

# 3. Verificare il risultato
git log --oneline -5
git diff ORIG_HEAD..HEAD --stat   # Cosa è cambiato rispetto a prima?

# 4. Se il risultato non è soddisfacente:
git reset --hard ORIG_HEAD        # Annullare tutto

# Confrontare HEAD con ORIG_HEAD dopo un merge
git diff ORIG_HEAD HEAD --stat
# Mostra tutti i file modificati dal merge

# Visualizzare i commit aggiunti dal merge
git log ORIG_HEAD..HEAD --oneline
# Lista dei commit introdotti dal merge
```

---

## Scenari di Disaster Recovery Completi

### Scenario 1: Corruzione del File `.git/index`

Il file `index` (staging area) può corrompersi a causa di crash del sistema, power failure o errori del filesystem. I sintomi includono errori come "index file corrupt" o "index file smaller than expected".

```bash
# Sintomi tipici:
git status
# fatal: index file corrupt

# Passo 1: Rimuovere l'index corrotto
rm .git/index

# Passo 2: Ricostruire l'index dall'ultimo commit
git reset
# Oppure:
git read-tree HEAD
# L'index viene ricostruito dal tree del commit HEAD

# Passo 3: Verificare lo stato
git status
# Ora mostra correttamente lo stato della working directory

# Passo 4: Se c'erano modifiche staged prima della corruzione,
# sono perse dall'index ma i file nella working directory sono intatti
# Ri-stage le modifiche necessarie:
git add src/file-modificato.js

# NOTA: Se HEAD stesso è corrotto, recuperare dal reflog o dal remote:
git fetch origin
git reset --hard origin/main
```

### Scenario 2: Recupero dopo Force Push Accidentale su Branch Condiviso

Uno dei disastri più temuti: un force push su un branch condiviso sovrascrive la cronologia remota. Il recupero richiede cooperazione con il team.

```bash
# Situazione: qualcuno ha eseguito git push --force origin main
# sovrascrivendo 10 commit del team

# CASO A: Hai una copia locale aggiornata (stale clone)
# Il tuo local tracking branch ha ancora i commit originali

# Passo 1: Verificare che il tuo branch locale abbia i commit
git log --oneline -15 main
# Confrontare con:
git log --oneline -15 origin/main
# Se main ha più commit di origin/main, hai i commit persi

# Passo 2: Forzare il push dei commit ripristinati
git push --force-with-lease origin main
# Ripristina la cronologia originale sul remote

# CASO B: Non hai una copia locale aggiornata
# Chiedere ai colleghi chi ha i commit nel proprio clone locale

# Passo 3: Un collega con i commit originali esegue:
git push --force-with-lease origin main

# CASO C: Nessuno ha i commit localmente
# Su GitHub/GitLab, gli eventi di push sono registrati
# Contattare il supporto per recuperare i commit dal backup del server

# Passo 4: Tutti i membri del team devono sincronizzarsi
# Ogni membro esegue:
git fetch origin
git reset --hard origin/main
# ATTENZIONE: Questo scarta le modifiche locali non pushate
```

### Scenario 3: Recupero dopo `git clean -fdx` Accidentale

`git clean -fdx` ha rimosso file di configurazione locale (.env, config.local.json), dipendenze (node_modules), cache di build e altri file non tracciati. Non esiste reflog per questa operazione.

```bash
# Valutazione del danno:
# - File di configurazione locale (.env, *.local) → devono essere ricreati
# - Dipendenze (node_modules, vendor) → reinstallabili
# - Cache di build (dist, build, .cache) → ricostruibili
# - File nuovi non committati → PERSI (verificare cestino OS)

# Passo 1: Reinstallare le dipendenze
npm install          # Node.js
pip install -r requirements.txt  # Python
composer install     # PHP
go mod download      # Go

# Passo 2: Ricostruire i file di configurazione locale
cp .env.example .env
# Inserire i valori corretti per le variabili d'ambiente

# Passo 3: Ricostruire la cache di build
npm run build

# Passo 4: Verificare il cestino del sistema operativo per file importanti
ls ~/.local/share/Trash/files/ | grep -i "nome-file-cercato"
# Se trovato:
cp ~/.local/share/Trash/files/file-importante ./

# Passo 5: Prevenzione futura — aggiungere esclusioni di sicurezza
# Creare un alias che esclude sempre i file critici
git config --global alias.purge '!git clean -fd -e .env -e "*.local" -e ".vscode"'
# Uso: git purge (invece di git clean -fdx)
```

### Scenario 4: Repository Gravemente Corrotto

Il repository presenta errori multipli di integrità. La strategia è salvare il massimo possibile e ricostruire da un clone fresco.

```bash
# Sintomi:
git status
# error: object file .git/objects/a1/b2c3d4... is empty
# fatal: loose object a1b2c3d4... is corrupt

# Passo 1: Diagnosticare l'entità della corruzione
git fsck --full 2>&1 | tee /tmp/corruption-report.txt
grep -c "corrupt\|missing\|broken" /tmp/corruption-report.txt
# Contare gli oggetti problematici

# Passo 2: Salvare le modifiche locali non committate
# (se git diff funziona)
git diff > /tmp/local-changes.patch 2>/dev/null
git diff --cached > /tmp/staged-changes.patch 2>/dev/null
# Se git diff non funziona, copiare i file modificati manualmente
cp -r src/ /tmp/src-backup/

# Passo 3: Salvare i branch locali che non sono sul remote
git branch -vv 2>/dev/null | grep -v "\[origin" > /tmp/local-branches.txt

# Passo 4: Salvare gli stash
git stash list 2>/dev/null > /tmp/stash-list.txt
for i in $(seq 0 $(git stash list 2>/dev/null | wc -l)); do
    git stash show -p stash@{$i} > /tmp/stash-$i.patch 2>/dev/null
done

# Passo 5: Clonare fresco dal remote
cd ..
mv progetto progetto-corrotto
git clone https://github.com/user/progetto.git
cd progetto

# Passo 6: Riapplicare le modifiche locali
git apply /tmp/local-changes.patch 2>/dev/null
git apply /tmp/staged-changes.patch 2>/dev/null

# Passo 7: Riapplicare gli stash
for patch in /tmp/stash-*.patch; do
    git stash push -m "recuperato: $(basename $patch)" 2>/dev/null
    git apply "$patch" 2>/dev/null && git stash push -m "recuperato"
done

# Passo 8: Verificare l'integrità del nuovo clone
git fsck --full
```

### Scenario 5: Recupero di un Commit dopo `git commit --amend` Accidentale

Un `git commit --amend` sovrascrive il commit precedente. Il vecchio commit diventa un oggetto orfano ma rimane nell'object database.

```bash
# Situazione: git commit --amend ha sovrascritto un commit con informazioni importanti

# Passo 1: Trovare il commit originale nel reflog
git reflog
# a1b2c3d HEAD@{0}: commit (amend): nuovo messaggio sbagliato
# d4e5f6g HEAD@{1}: commit: messaggio originale importante  ← QUESTO

# Passo 2: Esaminare il commit originale
git show d4e5f6g

# Passo 3: Recuperare il commit originale
# Opzione A: Tornare al commit originale
git reset --soft d4e5f6g

# Opzione B: Creare un branch dal commit originale per esaminarlo
git branch commit-originale d4e5f6g
git diff commit-originale..HEAD   # Confrontare le differenze
```

---

## Tecniche Avanzate di Analisi del Reflog

### Formato e Struttura del Reflog

Il reflog è un log locale che registra ogni modifica a HEAD e ai riferimenti dei branch. Ogni entry contiene il timestamp, l'hash del commit, il tipo di operazione e un messaggio descrittivo. Comprendere la struttura delle entry aiuta a navigare efficacemente la cronologia delle operazioni.

```bash
# Formato base del reflog
git reflog
# a1b2c3d HEAD@{0}: commit: feat: aggiungere autenticazione OAuth2
# d4e5f6g HEAD@{1}: checkout: moving from feature to main
# h7i8j9k HEAD@{2}: commit: fix: correggere errore di parsing
# l3m4n5o HEAD@{3}: rebase (finish): returning to refs/heads/feature
# p6q7r8s HEAD@{4}: rebase (pick): applicare fix parsing
# t9u0v1w HEAD@{5}: rebase (start): checkout main

# Formato con timestamp ISO
git reflog --date=iso
# a1b2c3d HEAD@{2025-03-15 14:30:00 +0100}: commit: feat: ...
# d4e5f6g HEAD@{2025-03-15 14:25:00 +0100}: checkout: ...

# Formato con timestamp relativo
git reflog --date=relative
# a1b2c3d HEAD@{2 hours ago}: commit: feat: ...
# d4e5f6g HEAD@{3 hours ago}: checkout: ...

# Formato con timestamp locale
git reflog --date=local
# a1b2c3d HEAD@{Sat Mar 15 14:30:00 2025}: commit: ...

# Reflog di un branch specifico (non solo HEAD)
git reflog show main
# a1b2c3d main@{0}: merge feature: Fast-forward
# d4e5f6g main@{1}: commit: chore: aggiornare dipendenze

# Reflog dello stash
git reflog show stash
# a1b2c3d stash@{0}: WIP on main: abc1234 ultimo commit
# d4e5f6g stash@{1}: On feature: lavoro parziale CSS

# Reflog di tutti i riferimenti
git reflog --all
```

### Filtraggio e Ricerca nel Reflog

```bash
# Cercare operazioni specifiche nel reflog
git reflog | grep "rebase"
# Mostra tutte le operazioni di rebase

git reflog | grep "reset"
# Mostra tutti i reset eseguiti

git reflog | grep "checkout: moving from feature"
# Mostra quando si è lasciato il branch "feature"

# Cercare per hash parziale
git reflog | grep "a1b2"

# Cercare nel reflog con date specifiche
git reflog --date=iso | grep "2025-03-15"
# Tutte le operazioni del 15 marzo 2025

# Combinare grep con git show per analisi dettagliata
git reflog --oneline | grep "commit:" | head -5 | while read hash rest; do
    echo "=== $hash: $rest ==="
    git show --stat "$hash"
    echo
done
```

### Analisi Temporale del Reflog

Git supporta una sintassi potente per accedere allo stato del repository in momenti specifici del passato, utilizzando qualificatori temporali.

```bash
# Stato di HEAD in momenti specifici
git show HEAD@{1.hour.ago}     # Un'ora fa
git show HEAD@{yesterday}       # Ieri
git show HEAD@{2.days.ago}      # Due giorni fa
git show HEAD@{1.week.ago}      # Una settimana fa
git show HEAD@{2025-03-15}      # Data specifica
git show HEAD@{2025-03-15 14:30:00}  # Data e ora specifiche

# Differenze tra stati temporali
git diff HEAD@{yesterday} HEAD
# Mostra tutte le modifiche fatte da ieri

git diff main@{1.week.ago} main --stat
# Mostra i file modificati nell'ultima settimana su main

git log main@{1.month.ago}..main --oneline
# Tutti i commit dell'ultimo mese su main

# Trovare quando un file è stato modificato per l'ultima volta
git log --follow -p -- src/auth.js | head -50
# --follow segue il file anche attraverso rinominazioni

# Confrontare l'evoluzione di un file nel tempo
git diff HEAD@{2.weeks.ago}:src/config.js HEAD:src/config.js
# Mostra come il file config.js è cambiato nelle ultime 2 settimane
```

### Configurazione della Retention del Reflog

```bash
# Visualizzare la configurazione corrente
git config gc.reflogExpire
# Default: 90 days (per entry raggiungibili da branch/tag)

git config gc.reflogExpireUnreachable
# Default: 30 days (per entry non raggiungibili)

# Configurazione raccomandata per ambienti di produzione
git config --global gc.reflogExpire "180 days"
git config --global gc.reflogExpireUnreachable "90 days"

# Per repository critici: retention estesa
git config gc.reflogExpire "365 days"
git config gc.reflogExpireUnreachable "180 days"

# Per repository di test: retention ridotta (risparmio spazio)
git config gc.reflogExpire "30 days"
git config gc.reflogExpireUnreachable "7 days"

# Disabilitare la scadenza del reflog (retention infinita)
# ATTENZIONE: il reflog crescerà indefinitamente
git config gc.reflogExpire never
git config gc.reflogExpireUnreachable never

# Forzare la pulizia del reflog manualmente
git reflog expire --expire=90.days --all
# Rimuove le entry più vecchie di 90 giorni

# Pulizia del reflog per un singolo riferimento
git reflog expire --expire=30.days refs/heads/main
```

### Relazione tra Reflog, Garbage Collection e Recupero

```bash
# La garbage collection di Git opera in questo modo:
# 1. git gc identifica gli oggetti non raggiungibili
# 2. Gli oggetti nel reflog sono considerati "raggiungibili" e preservati
# 3. Dopo la scadenza del reflog, gli oggetti diventano candidati per la rimozione
# 4. git gc --prune=<date> rimuove gli oggetti non raggiungibili più vecchi di <date>

# Configurazione di gc.pruneExpire (diverso da gc.reflogExpire!)
git config gc.pruneExpire
# Default: "2 weeks ago"
# Gli oggetti non raggiungibili (e non nel reflog) sopravvivono 2 settimane

# Cronologia di un oggetto dal commit alla rimozione:
# Giorno 0: Commit creato, raggiungibile da branch
# Giorno X: Reset --hard, commit diventa non raggiungibile
#            MA ancora nel reflog (gc.reflogExpireUnreachable = 30 giorni)
# Giorno X+30: Entry del reflog scade
#              Oggetto diventa "unreachable" per gc
# Giorno X+30+14: gc.pruneExpire (2 settimane) → oggetto rimosso da gc
# TOTALE: ~44 giorni dalla perdita alla rimozione permanente

# Per massimizzare il tempo di recupero:
git config gc.reflogExpireUnreachable "90 days"
git config gc.pruneExpire "30 days"
# TOTALE: ~120 giorni di finestra di recupero

# REGOLA D'ORO: Mai eseguire dopo un errore:
git gc --prune=now   # ELIMINA IMMEDIATAMENTE tutti gli oggetti non raggiungibili
# Usare solo se si è certi di non dover recuperare nulla
```

---

## Riferimento Comandi Completo

### Opzioni Complete di `git stash`

| Sottocomando | Descrizione |
|-------------|-------------|
| `push [-m <msg>]` | Salva le modifiche correnti (default se nessun sottocomando) |
| `push -p` | Stash interattivo per hunk |
| `push --staged` | Stash solo le modifiche staged (Git 2.35+) |
| `push -u` / `--include-untracked` | Include i file non tracciati |
| `push -a` / `--all` | Include anche i file ignorati |
| `push -k` / `--keep-index` | Mantiene le modifiche staged nella working directory |
| `push -- <pathspec>` | Stash solo file specifici |
| `list` | Mostra tutti gli stash |
| `show [stash@{n}]` | Mostra un riassunto delle modifiche |
| `show -p [stash@{n}]` | Mostra il diff completo |
| `apply [stash@{n}]` | Applica senza rimuovere dallo stack |
| `apply --index` | Applica preservando lo stato staged |
| `pop [stash@{n}]` | Applica e rimuove dallo stack |
| `drop [stash@{n}]` | Rimuove uno stash specifico |
| `clear` | Rimuove tutti gli stash |
| `branch <name> [stash@{n}]` | Crea un branch dallo stash |
| `create` | Crea uno stash entry senza salvarlo nella ref |
| `store` | Salva uno stash creato con `create` nella ref |

### Opzioni Complete di `git reset`

| Opzione | Descrizione |
|---------|-------------|
| `--soft` | Sposta solo HEAD, index e working directory invariati |
| `--mixed` | Sposta HEAD e resetta index (default) |
| `--hard` | Sposta HEAD, resetta index e working directory |
| `--merge` | Resetta index e working directory, preserva le modifiche non staged diverse dal target |
| `--keep` | Resetta index e aggiorna working directory, preserva i file con modifiche locali |
| `-p`, `--patch` | Reset interattivo per hunk (solo con `--mixed`) |
| `-N`, `--intent-to-add` | Dopo il reset, segna i file come "intent to add" |
| `-q`, `--quiet` | Sopprime i messaggi di output |
| `--pathspec-from-file=<file>` | Legge i pathspec da un file |

### Opzioni Complete di `git revert`

| Opzione | Descrizione |
|---------|-------------|
| `-e`, `--edit` | Apre l'editor per il messaggio (default) |
| `--no-edit` | Non aprire l'editor, usa il messaggio predefinito |
| `-n`, `--no-commit` | Non committare, solo staging |
| `-m <parent>`, `--mainline <parent>` | Specifica il parent mainline per merge commit |
| `--continue` | Continua dopo risoluzione conflitti |
| `--abort` | Annulla il revert in corso |
| `--skip` | Salta il commit corrente e continua |
| `-s`, `--signoff` | Aggiunge Signed-off-by al messaggio |
| `--strategy=<strategy>` | Usa la strategia di merge specificata |
| `-X <option>`, `--strategy-option=<option>` | Opzione per la strategia di merge |
| `--rerere-autoupdate` | Aggiorna automaticamente con risoluzioni rerere |

### Opzioni Complete di `git bisect`

| Sottocomando | Descrizione |
|-------------|-------------|
| `start [<bad> [<good>...]]` | Avvia il bisect |
| `bad [<rev>]` | Marca un commit come bad |
| `good [<rev>]` | Marca un commit come good |
| `skip [<rev>...]` | Salta un commit non testabile |
| `reset [<commit>]` | Termina il bisect, torna allo stato originale |
| `run <cmd>` | Automatizza il bisect con un comando |
| `log` | Mostra il log del bisect corrente |
| `replay <file>` | Ripete un bisect da un file di log |
| `visualize` | Apre gitk con i commit rimanenti |
| `start --term-old=<t> --term-new=<t>` | Usa termini personalizzati |
| `terms` | Mostra i termini correnti |

### Opzioni Complete di `git blame`

| Opzione | Descrizione |
|---------|-------------|
| `-L <start>,<end>` | Mostra solo il range di righe specificato |
| `-L :<funcname>` | Mostra solo la funzione specificata |
| `-e`, `--show-email` | Mostra email invece del nome |
| `-w` | Ignora le modifiche di whitespace |
| `-M` | Rileva righe spostate all'interno del file |
| `-C` | Rileva righe copiate da altri file |
| `-C -C` | Rileva copie anche da file in commit diversi |
| `-C -C -C` | Rileva copie da qualsiasi file in qualsiasi commit |
| `--since=<date>` | Ignora le modifiche prima della data |
| `--abbrev=<n>` | Lunghezza dell'hash abbreviato |
| `--porcelain` | Output machine-readable |
| `--ignore-rev <rev>` | Ignora un commit specifico |
| `--ignore-revs-file <file>` | Ignora i commit listati nel file |
| `--color-lines` | Colora le righe dello stesso commit |
| `--color-by-age` | Colora in base all'età del commit |

### Opzioni Complete di `git reflog`

| Sottocomando / Opzione | Descrizione |
|------------------------|-------------|
| `show [<ref>]` | Mostra il reflog della ref (default: HEAD) |
| `expire [--expire=<time>]` | Rimuove entry vecchie |
| `delete <ref@{n}>` | Rimuove una entry specifica |
| `exists <ref>` | Verifica se una ref ha un reflog |
| `--date=<format>` | Formato data: relative, iso, local, short |
| `--all` | Mostra i reflog di tutte le ref |
| `-n <number>` | Limita il numero di entry |

---

## Anti-Pattern

### 1. Usare `git stash` come Storage a Lungo Termine

Lo stash è progettato per il salvataggio temporaneo di pochi minuti o ore, non di giorni o settimane. Gli stash accumulati diventano incomprensibili e spesso inapplicabili a causa della divergenza del codice. Se il lavoro deve essere preservato a lungo, creare un branch.

```bash
# SBAGLIATO: stash dimenticati per settimane
git stash list
# stash@{0}: WIP on main: abc1234 (3 settimane fa)
# stash@{1}: WIP on main: def5678 (2 mesi fa)
# stash@{2}: WIP on main: ghi9012 (4 mesi fa) ← irrecuperabile

# CORRETTO: creare un branch per lavoro non immediato
git switch -c wip/esperimento-cache
git add -A && git commit -m "wip: esperimento cache distribuita"
```

### 2. `git reset --hard` Senza Verificare il Reflog

Eseguire `reset --hard` senza prima annotare l'hash corrente o verificare il reflog è come saltare da un aereo senza paracadute. Le modifiche non committate sono perse per sempre.

```bash
# SBAGLIATO: reset --hard impulsivo
git reset --hard HEAD~3    # "Ups, quei commit servivano"

# CORRETTO: annotare prima, verificare poi
git log --oneline -5       # Annotare gli hash
git reflog                 # Verificare lo storico
git reset --hard HEAD~3    # Solo ora, con consapevolezza
```

### 3. `git push --force` su Branch Condivisi

Il force push sovrascrive la cronologia remota. Se altri sviluppatori hanno basato il loro lavoro sui commit sovrascritti, i loro branch diventano inconsistenti e devono essere ricostruiti manualmente.

```bash
# SBAGLIATO: force push su main/develop
git push --force origin main     # Distrugge il lavoro di tutti

# CORRETTO: usare --force-with-lease (almeno)
git push --force-with-lease origin feature/mia-feature
# Fallisce se qualcuno ha pushato nel frattempo

# MIGLIORE: non fare rebase di branch condivisi
```

### 4. `git clean -fdx` Senza Dry Run

`git clean` è irreversibile e non ha reflog. Eseguirlo con `-x` (include file ignorati) senza un dry run preliminare può eliminare configurazioni locali, dipendenze scaricate, cache di build e file di ambiente.

```bash
# SBAGLIATO: clean cieco
git clean -fdx    # Addio node_modules, .env, build cache...

# CORRETTO: sempre dry run prima
git clean -fdx -n    # Vedere cosa verrà eliminato
# Would remove node_modules/
# Would remove .env
# Would remove build/
# Decidere se procedere o usare -e per escludere
git clean -fd -e node_modules -e .env
```

### 5. Non Usare `--index` con `git stash apply`

Quando si fa stash, Git salva separatamente le modifiche staged e unstaged. Senza `--index`, `stash apply` ripristina tutto come unstaged, perdendo la separazione originale.

```bash
# SBAGLIATO: perdere lo stato staged
git add src/importante.js        # Staged
# src/altro.js modificato ma non staged
git stash
git stash apply                  # Tutto diventa unstaged

# CORRETTO: preservare lo stato staged/unstaged
git stash apply --index
```

### 6. `git reset --hard origin/main` come Soluzione a Tutti i Problemi

Resettare duramente al remote è un approccio a forza bruta che perde tutte le modifiche locali. È legittimo solo quando si vuole deliberatamente scartare tutto il lavoro locale.

```bash
# SBAGLIATO: "non funziona più, resetto tutto"
git reset --hard origin/main

# CORRETTO: capire il problema prima
git status                       # Cosa è cambiato?
git diff                         # Quali sono le differenze?
git stash                        # Salvare il lavoro se necessario
git pull --rebase                # Sincronizzare mantenendo i commit locali
```

### 7. Usare `git checkout` per Tutto (Ambiguità)

Il vecchio `git checkout` è sovraccarico di responsabilità. Può cambiare branch, ripristinare file, creare branch e fare detached HEAD. Questo porta ad errori quando un file e un branch hanno lo stesso nome.

```bash
# AMBIGUO: checkout di un file o di un branch?
git checkout feature    # È un branch "feature" o un file "feature"?

# CORRETTO: comandi moderni senza ambiguità
git switch feature              # Branch
git restore feature             # File
```

### 8. Fare `git stash pop` su un Branch Diverso Senza Verificare

Lo stash è stato creato nel contesto di un certo branch. Applicarlo su un branch completamente diverso può causare conflitti difficili da risolvere o introdurre codice nel contesto sbagliato.

```bash
# RISCHIOSO: pop su branch diverso
git switch main
git stash pop    # Stash creato su feature/auth → conflitti probabili

# CORRETTO: usare stash branch per conflitti
git stash branch recovery-from-stash stash@{0}
# Crea un branch dal punto in cui lo stash è stato creato
```

### 9. Ignorare `ORIG_HEAD` dopo Operazioni Pericolose

Git salva automaticamente l'HEAD corrente in `ORIG_HEAD` prima di operazioni potenzialmente distruttive (merge, rebase, reset). Ignorare questo riferimento e procedere con altre operazioni lo sovrascrive, perdendo la possibilità di annullare facilmente.

```bash
# SBAGLIATO: ignorare ORIG_HEAD e procedere
git merge feature-branch       # ORIG_HEAD salvato
git merge another-branch       # ORIG_HEAD sovrascritto! Primo merge non annullabile facilmente

# CORRETTO: verificare dopo ogni operazione
git merge feature-branch
git log --oneline -5           # Tutto ok?
# Se no: git reset --hard ORIG_HEAD
```

### 10. Non Configurare `gc.reflogExpire`

Il reflog ha una scadenza predefinita di 90 giorni per le entry raggiungibili e 30 giorni per quelle non raggiungibili. In ambienti dove gli errori vengono scoperti tardi, queste finestre possono essere troppo brevi.

```bash
# Verificare la configurazione corrente
git config gc.reflogExpire
# Default: 90 giorni

# Estendere per ambienti critici
git config gc.reflogExpire "180 days"
git config gc.reflogExpireUnreachable "90 days"
```

---

## Best Practices

### Stash

1. **Usare messaggi descrittivi**: `git stash push -m "descrizione"` rende la lista degli stash comprensibile.
2. **Non accumulare stash**: Gli stash dovrebbero essere temporanei. Se un lavoro stashato non viene ripreso entro qualche giorno, probabilmente dovrebbe essere un branch.
3. **Preferire `apply` a `pop`**: `apply` mantiene lo stash nello stack come backup. Fare `drop` esplicitamente dopo aver verificato che l'applicazione è corretta.

### Reset

1. **Non usare `reset --hard` su branch condivisi**: Riscrivere la cronologia condivisa causa problemi per tutto il team.
2. **Verificare il reflog prima di un reset hard**: Annotare l'hash corrente prima di operazioni distruttive.
3. **Preferire `revert` per annullamenti su branch condivisi**: `revert` è sicuro perché aggiunge cronologia invece di riscriverla.

### Recovery

1. **Conoscere il reflog**: Familiarizzarsi con `git reflog` prima di averne bisogno. In situazioni di panico, il reflog è il primo strumento da consultare.
2. **Non eseguire `git gc` dopo un errore**: La garbage collection potrebbe rimuovere oggetti che si vuole recuperare.
3. **Agire rapidamente**: Gli oggetti non raggiungibili hanno una scadenza nel reflog (predefinito 30 giorni).

### Bisect

1. **Mantenere commit compilabili**: Se ogni commit nella cronologia è compilabile e testabile, bisect funziona perfettamente.
2. **Automatizzare quando possibile**: `git bisect run` è più rapido e meno soggetto a errori umani.
3. **Usare termini personalizzati**: Per ricerche non legate a bug (performance, dimensione, ecc.), i termini personalizzati rendono il processo più chiaro.

---

## Troubleshooting

### 1. Stash Apply con Conflitti

```bash
# Sintomo: conflitti durante git stash apply
# CONFLICT (content): Merge conflict in src/app.js

# Soluzione 1: Risolvere i conflitti manualmente
git add file-risolto.js
git stash drop stash@{0}    # Rimuovere lo stash dopo la risoluzione

# Soluzione 2: Applicare lo stash su un branch dedicato
git stash branch recovery-branch stash@{0}
# Crea un branch dal commit originale dello stash
# L'applicazione avviene senza conflitti

# Soluzione 3: Applicare solo parti dello stash
git stash show -p stash@{0} | git apply --3way
# Se fallisce, almeno mostra i conflitti come diff
```

### 2. Reset --hard Accidentale

```bash
# Sintomo: "Ho perso i miei commit!"
# REGOLA D'ORO: NON eseguire git gc

# Passo 1: Trovare il commit nel reflog
git reflog
# a1b2c3d HEAD@{0}: reset: moving to HEAD~5
# f6g7h8i HEAD@{1}: commit: ultimo commit importante  ← QUESTO

# Passo 2: Recuperare
git reset --hard HEAD@{1}
# Oppure con l'hash direttamente
git reset --hard f6g7h8i

# Se il reflog è stato pulito, cercare oggetti orfani
git fsck --lost-found --no-reflogs
# I commit trovati saranno in .git/lost-found/commit/
```

### 3. Bisect su Cronologia Non Lineare

```bash
# Sintomo: molti commit non compilano durante bisect
# Causa: merge commit, commit WIP, branch integrati a metà

# Soluzione 1: usare skip per commit non testabili
git bisect skip

# Soluzione 2: script che gestisce i fallimenti di build
git bisect run bash -c 'make 2>/dev/null || exit 125; ./test.sh'
# exit 125 = "skip questo commit"

# Soluzione 3: bisect solo sul primo parent (linearizza)
git bisect start --first-parent HEAD v1.0.0
# Ignora i merge commit, segue solo il branch principale
```

### 4. Blame Mostra il Commit Sbagliato (Commit di Formattazione)

```bash
# Sintomo: git blame mostra un commit di reformattazione
# invece della modifica logica reale

# Soluzione: configurare .git-blame-ignore-revs
echo "abc1234  # reformat: prettier migration" >> .git-blame-ignore-revs
echo "def5678  # chore: apply eslint fixes" >> .git-blame-ignore-revs
git config blame.ignoreRevsFile .git-blame-ignore-revs

# Committare per il team
git add .git-blame-ignore-revs
git commit -m "chore: aggiungere commit di formattazione alla blame ignore list"

# Per un singolo blame
git blame --ignore-rev abc1234 src/app.js
```

### 5. Stash Pop su Branch Sbagliato

```bash
# Sintomo: ho applicato lo stash su main invece che su feature
# e le modifiche sono nel contesto sbagliato

# Se non hai ancora committato:
git stash                    # Ri-stashare le modifiche
git switch feature/auth      # Andare al branch corretto
git stash pop                # Applicare sul branch giusto

# Se hai già committato:
git reset --soft HEAD~1      # Annullare il commit, mantenere staged
git stash                    # Stashare tutto
git switch feature/auth
git stash pop
```

### 6. Reflog Vuoto o Scaduto

```bash
# Sintomo: git reflog non mostra i commit che cerco
# Causa: il reflog ha una scadenza (default 90 giorni)

# Soluzione 1: cercare con fsck
git fsck --unreachable --no-reflogs | grep commit
# unreachable commit abc1234...

# Esaminare i commit trovati
git show abc1234
git log --oneline abc1234

# Soluzione 2: cercare negli oggetti
git log --all --oneline | grep "messaggio cercato"

# Prevenzione: estendere la scadenza del reflog
git config gc.reflogExpire "365 days"
git config gc.reflogExpireUnreachable "180 days"
```

### 7. Stash con File Untracked che Non Appaiono

```bash
# Sintomo: git stash non salva i file nuovi (non tracciati)
# Causa: git stash di default salva solo le modifiche a file tracciati

# Soluzione
git stash push -u -m "include untracked files"
# Oppure
git stash push --include-untracked

# Per includere anche i file ignorati (.gitignore)
git stash push -a
```

### 8. `git clean` Ha Eliminato File Importanti

```bash
# Sintomo: git clean ha rimosso file che servivano
# NOTA: git clean è IRREVERSIBILE — non c'è reflog

# Se i file erano sotto version control in passato:
git checkout HEAD -- path/to/file

# Se i file non erano mai stati tracciati:
# Controllare il cestino del sistema operativo
# Linux: ~/.local/share/Trash/
# macOS: ~/.Trash/

# Se erano file di build riproducibili:
npm install    # o equivalente
make           # ricostruire

# Prevenzione: SEMPRE usare -n (dry-run) prima di -f
git clean -fdn    # Cosa verrebbe eliminato?
```

### 9. Reset --mixed Ha Unstaged Tutto per Errore

```bash
# Sintomo: volevo annullare solo l'ultimo commit ma tutto
# è diventato unstaged (centinaia di file)
# Causa: git reset senza --soft fa --mixed di default

# Soluzione: ri-stage e ricommittare
git add -A
git commit -c ORIG_HEAD    # Riusa il messaggio dell'ultimo commit

# Se volevi solo annullare un commit mantenendo staged:
# Usa --soft la prossima volta
git reset --soft HEAD~1
```

### 10. Revert di un Merge Causa il "Merge già Fatto" Problem

```bash
# Sintomo: dopo aver revertito un merge, un successivo merge
# dello stesso branch non porta le modifiche
# Causa: Git considera le modifiche già "integrate e poi annullate"

# Diagnosi
git log --oneline --graph | head -20
# *   M1 Merge feature into main
# *   R1 Revert "Merge feature into main"
# Ora: git merge feature → "Already up to date"

# Soluzione: revertire il revert prima del re-merge
git revert <hash-del-revert-R1>
# Poi il merge funzionerà normalmente
git merge feature
```

### 11. Bisect Run Restituisce Risultati Inaffidabili

```bash
# Sintomo: bisect identifica un commit che non sembra essere la causa
# Cause possibili:
# 1. Lo script di test non è deterministico (test flaky)
# 2. Lo script non gestisce correttamente i codici di uscita
# 3. Il bug dipende dall'ambiente, non dal codice

# Diagnosi: verificare manualmente il commit trovato
git checkout <commit-trovato>
./test-script.sh && echo "GOOD" || echo "BAD"

# Soluzione: migliorare lo script di test
cat > /tmp/bisect-test.sh << 'SCRIPT'
#!/bin/bash
set -e

# Tentare la build
make clean && make 2>/dev/null || exit 125

# Eseguire il test 3 volte per ridurre i falsi positivi
for i in 1 2 3; do
    if ! ./specific-test.sh; then
        exit 1    # BAD
    fi
done
exit 0    # GOOD
SCRIPT
chmod +x /tmp/bisect-test.sh
git bisect run /tmp/bisect-test.sh
```

### 12. Stash Non Preserva i Permessi dei File

```bash
# Sintomo: dopo stash pop, i file hanno permessi diversi
# Causa: git stash non traccia i permessi execute bit se
# core.fileMode è disabilitato

# Diagnosi
git config core.fileMode
# false → Git non traccia i permessi

# Soluzione: abilitare fileMode
git config core.fileMode true

# Oppure ripristinare i permessi manualmente
chmod +x scripts/*.sh
```

### 13. Recupero di un Branch dopo `git branch -D`

```bash
# Sintomo: eliminato un branch con -D (force delete) per errore

# Passo 1: trovare l'ultimo commit del branch nel reflog
git reflog | grep "checkout: moving from nome-branch"
# a1b2c3d HEAD@{5}: checkout: moving from nome-branch to main

# Passo 2: verificare il commit
git show a1b2c3d --oneline

# Passo 3: ricreare il branch
git branch nome-branch a1b2c3d

# Se non appare nel reflog di HEAD, cercare in tutti i reflog
git reflog --all | grep "nome-branch"
```

### 14. Reset --keep vs --hard: Quale Usare

```bash
# Sintomo: voglio tornare a un commit precedente ma ho modifiche
# locali che non voglio perdere

# --hard: PERDE tutto (modifiche committed e non)
git reset --hard HEAD~3    # PERICOLOSO

# --keep: preserva le modifiche locali se non conflittuali
git reset --keep HEAD~3
# Se un file modificato localmente differisce tra HEAD e HEAD~3:
# fatal: Entry 'file.js' would be overwritten by merge. Cannot merge.
# In questo caso, stashare prima e poi procedere

# --merge: simile a --keep ma per merge in corso
git reset --merge HEAD~3
```

### 15. Git Log Non Mostra Tutti i Commit

```bash
# Sintomo: git log non mostra commit che so esistere
# Causa: git log segue solo il branch corrente per default

# Soluzione 1: mostrare tutti i branch
git log --all --oneline --graph

# Soluzione 2: cercare in tutti i branch per messaggio
git log --all --grep="testo cercato"

# Soluzione 3: cercare per contenuto (pickaxe)
git log --all -S "functionName"

# Soluzione 4: cercare commit non raggiungibili (orfani)
git fsck --unreachable --no-reflogs | grep commit | head -20
```

### 16. `git stash push --staged` Non Funziona

```bash
# Sintomo: error: unknown option `staged`
# Causa: versione di Git troppo vecchia (richiede 2.35+)

# Diagnosi
git --version

# Soluzione per versioni vecchie: workaround manuale
# Creare un commit temporaneo con le modifiche non staged
git stash push -k          # --keep-index: mantiene staged, stasha il resto
# Ora hai le modifiche staged nella working directory
# e le unstaged nello stash
```

### 17. Bisect in Repository con Squash Merge

```bash
# Sintomo: bisect non trova il commit giusto perché
# la cronologia è stata squashata (un singolo commit per feature)
# e il bug è dentro un commit squashato

# Soluzione: bisect identifica il commit squashato
# Poi analizzare la PR originale per trovare il commit specifico
git bisect start HEAD v1.0.0
git bisect run ./test.sh
# Result: abc1234 "feat: implementare autenticazione (#42)"

# Analizzare la PR #42 per il dettaglio
gh pr view 42 --comments
```

---

## FAQ

### 1. Qual è la differenza tra `git stash` e un commit temporaneo?

Lo stash è uno stack LIFO (Last In, First Out) separato dalla cronologia dei commit. Non appare nel log, non influisce sui branch e non viene pushato. Un commit temporaneo (`git commit -m "WIP"`) è un commit normale che appare nella cronologia e viene pushato. Lo stash è preferibile per interruzioni brevi (minuti/ore); un branch con commit WIP è preferibile per lavoro che dura giorni.

### 2. Posso applicare uno stash su un branch diverso da quello dove l'ho creato?

Sì, ma con cautela. Lo stash è un diff rispetto al commit dove è stato creato. Se il branch di destinazione ha lo stesso file in uno stato diverso, ci saranno conflitti. In caso di conflitti, usare `git stash branch <nome> stash@{n}` che crea un branch dal punto originale dello stash e applica le modifiche senza conflitti.

### 3. `git reset --hard` è davvero irreversibile?

No, non del tutto. I commit "persi" rimangono nell'object database e nel reflog per almeno 30 giorni (default `gc.reflogExpireUnreachable`). Finché non si esegue `git gc --prune=now`, i commit sono recuperabili tramite `git reflog`. Tuttavia, le modifiche **non committate** (non staged e non stashate) sono perse per sempre con `reset --hard`.

### 4. Qual è la differenza tra `git reset`, `git restore` e `git revert`?

- **`git reset`**: Sposta HEAD e opzionalmente resetta index e working directory. Riscrive la cronologia.
- **`git restore`**: Ripristina file nella working directory o nell'index da una source specifica. Non tocca HEAD.
- **`git revert`**: Crea un **nuovo commit** che annulla le modifiche di un commit precedente. Non riscrive la cronologia, sicuro per branch condivisi.

### 5. Come faccio a sapere se un commit è nel reflog?

```bash
git reflog | grep <hash-parziale>
# Oppure
git reflog --all | grep <hash-parziale>
# Se non appare nel reflog, cercare con fsck:
git fsck --unreachable | grep <hash-parziale>
```

Il reflog registra ogni modifica a HEAD e ai branch. Se il commit è stato parte di un branch in qualsiasi momento, apparirà nel reflog della ref corrispondente.

### 6. `git stash pop` e `git stash apply`: quale usare?

`pop` = `apply` + `drop`. Se l'applicazione ha successo, lo stash viene rimosso. Se fallisce (conflitti), lo stash rimane. Best practice: usare `apply` per sicurezza, poi `drop` esplicitamente dopo aver verificato che tutto è corretto. Questo evita la perdita dello stash in caso di problemi.

### 7. Come annullo un `git revert` se il revert era sbagliato?

Eseguire un altro `git revert` del commit di revert: `git revert <hash-del-revert>`. Questo crea un terzo commit che riapplica le modifiche originali. È la procedura corretta perché mantiene la cronologia completa e trasparente.

### 8. Perché `git bisect` a volte identifica il commit sbagliato?

Cause comuni: (1) test non deterministici (flaky tests), (2) il bug dipende dall'interazione tra più commit, (3) lo script di test non copre esattamente il bug cercato, (4) commit che non compilano e vengono skippati riducono la precisione. Soluzione: migliorare lo script di test, renderlo deterministico, e verificare manualmente il risultato.

### 9. Come posso vedere cosa c'è in uno stash senza applicarlo?

```bash
git stash show stash@{0}           # Riassunto dei file modificati
git stash show -p stash@{0}        # Diff completo
git show stash@{0}:path/to/file    # Contenuto di un file specifico
git diff stash@{0} HEAD             # Differenze tra stash e HEAD corrente
```

### 10. Il reflog esiste anche sui repository remoti?

No. Il reflog è un meccanismo puramente locale. Ogni clone ha il suo reflog indipendente. Il server remoto (GitHub, GitLab) non espone il reflog. Questo è il motivo per cui `git push --force` è pericoloso: i commit sovrascritti sul remote non sono recuperabili tramite reflog (a meno che qualcun altro non li abbia nel suo reflog locale).

### 11. `git switch` vs `git checkout`: devo migrare?

`git switch` e `git restore` sono stati introdotti in Git 2.23 (agosto 2019) per chiarire le responsabilità di `git checkout`. Non sono un requisito: `checkout` continua a funzionare e non è deprecato. Tuttavia, i nuovi comandi sono più sicuri (switch richiede `--detach` esplicito) e meno ambigui. Per nuovi utenti e nuovi script, usare i nuovi comandi.

### 12. Come recupero un file eliminato diversi commit fa?

```bash
# Trovare il commit che ha eliminato il file
git log --all --diff-filter=D -- path/to/file.js
# commit abc1234 Delete file.js

# Ripristinare dal commit precedente alla cancellazione
git restore --source=abc1234~1 -- path/to/file.js
# Oppure con checkout (vecchia sintassi)
git checkout abc1234~1 -- path/to/file.js
```

### 13. `git reset --soft HEAD~1` è sicuro su branch pushati?

Lo è localmente, ma crea una divergenza con il remote. Se il commit era già stato pushato, il prossimo `git push` fallirà e richiederà `--force`. Usare `git revert` per annullare commit già pushati, che è sicuro per i branch condivisi.

### 14. Come posso stashare solo un file specifico?

```bash
# Stash di file specifici
git stash push -m "solo auth.js" -- src/auth.js

# Stash di più file specifici
git stash push -m "file selezionati" -- src/auth.js src/utils.js

# Stash interattivo (per hunk)
git stash push -p -m "hunk selezionati"
```

### 15. Cosa succede se eseguo `git gc` dopo un `reset --hard`?

`git gc` (garbage collection) rimuove gli oggetti non raggiungibili da nessun branch, tag o reflog. Se il reflog contiene ancora i commit "persi" (default 30 giorni per unreachable), `gc` li preserva. Ma se si esegue `git gc --prune=now`, tutti gli oggetti non raggiungibili vengono eliminati **immediatamente e irreversibilmente**. Non eseguire mai `gc --prune=now` dopo un errore prima di aver tentato il recupero.

### 16. Come funziona `git blame -C` e quando usarlo?

`-C` rileva le righe copiate o spostate da **altri file** nello stesso commit. `-C -C` cerca anche nei commit che hanno creato il file. `-C -C -C` cerca in **qualsiasi commit** nella cronologia. Usarlo quando `blame` attribuisce una riga a un commit di refactoring/spostamento e si vuole trovare l'autore originale della logica.

### 17. Il `git stash` funziona con i merge in corso?

No. Se c'è un merge in corso con conflitti non risolti, `git stash` rifiuta di operare. Bisogna prima risolvere i conflitti e completare il merge (`git merge --continue`) oppure annullare il merge (`git merge --abort`) prima di poter stashare.

### 18. Come posso annullare un `git clean`?

Non è possibile. `git clean` rimuove i file dal filesystem senza passare per Git. Non esiste reflog, stash o altro meccanismo di recupero interno a Git. Le uniche opzioni sono: (1) strumenti di recupero filesystem (TestDisk, PhotoRec), (2) backup esterni, (3) cestino del sistema operativo se non è stato svuotato. Prevenzione: usare SEMPRE `git clean -n` prima di `git clean -f`.

### 19. Lo stash è condiviso tra i worktree?

Sì. `refs/stash` è un singolo reflog globale condiviso tra tutti i worktree dello stesso repository. Uno stash creato nel worktree A è visibile e applicabile dal worktree B. Questo crea una **race condition** quando si lavora su più worktree in parallelo: `git stash pop` nel worktree A potrebbe applicare lo stash creato nel worktree B (quello più recente nello stack). Soluzione: non usare stash con worktree multipli; usare commit temporanei (`git commit -m "wip: ..."`) su branch WIP dedicati.

### 20. Qual è la differenza tra `gc.reflogExpire` e `gc.pruneExpire`?

Sono due soglie di scadenza distinte nella pipeline di garbage collection:
- **`gc.reflogExpire`** (default: 90 giorni): controlla quando le entry del reflog vengono rimosse. Finché un oggetto è nel reflog, è considerato "raggiungibile" e non viene eliminato.
- **`gc.pruneExpire`** (default: 2 settimane): controlla quando gli oggetti non raggiungibili (e non più nel reflog) vengono definitivamente rimossi dall'object database.

La finestra di recupero totale dopo un errore è approssimativamente `gc.reflogExpireUnreachable` + `gc.pruneExpire` (default: 30 giorni + 14 giorni = ~44 giorni).

### 21. Come funziona `git rerere` e quando è utile?

`rerere` (Reuse Recorded Resolution) memorizza automaticamente come sono stati risolti i conflitti di merge e riapplica le stesse risoluzioni quando lo stesso conflitto si ripresenta. Si abilita con `git config rerere.enabled true`. È particolarmente utile con branch a lunga vita che vengono periodicamente rebasati o mergiati, e in workflow dove si testano merge di integrazione che poi vengono annullati e rifatti.

### 22. ORIG_HEAD esiste per sempre?

No. ORIG_HEAD viene sovrascritto ad ogni nuova operazione "pericolosa" (merge, rebase, reset, am). Ricorda **un solo passo indietro**. Se si eseguono due merge consecutivi, ORIG_HEAD punta allo stato prima del secondo merge; lo stato prima del primo merge è recuperabile solo dal reflog. Per sicurezza, prima di operazioni concatenate, annotare l'hash corrente con `git rev-parse HEAD`.

### 23. `git fsck` e `git reflog`: quale usare per il recupero?

Dipende dalla situazione:
- **`git reflog`**: prima scelta. Mostra le operazioni recenti con contesto (tipo di operazione, branch, messaggio). Funziona finché le entry non sono scadute (default 30-90 giorni).
- **`git fsck --unreachable`**: ultima risorsa. Cerca oggetti nell'object database indipendentemente dal reflog. Funziona anche dopo la scadenza del reflog, finché `git gc` non ha rimosso gli oggetti. Più lento e richiede analisi manuale dei commit trovati.

```bash
# Strategia di recupero in ordine:
# 1. Tentare con reflog
git reflog | grep "parola chiave"
# 2. Se il reflog non aiuta, usare fsck
git fsck --unreachable --no-reflogs | grep commit
# 3. Esaminare i candidati
git show <hash>
```

### 24. Come posso vedere la cronologia completa di un branch, inclusi i reset e i rebase?

```bash
# Il reflog del branch mostra ogni operazione
git reflog show nome-branch
# nome-branch@{0}: commit: ultimo commit
# nome-branch@{1}: reset: moving to HEAD~2
# nome-branch@{2}: commit: commit cancellato dal reset
# nome-branch@{3}: rebase (finish): ...
# nome-branch@{4}: rebase (start): ...

# Per visualizzare con date:
git reflog show nome-branch --date=iso
```

Il reflog di un branch è indipendente dal reflog di HEAD. Anche se HEAD si è spostato su un altro branch nel frattempo, il reflog del branch originale conserva la sua cronologia.

### 25. `git worktree` e `.gitignore` — le regole sono condivise?

Sì, tutti i worktree condividono lo stesso `.gitignore` committato nel repository. Tuttavia, ogni worktree può avere il proprio file di esclusione locale in `$GIT_DIR/info/exclude` (dove `$GIT_DIR` è la directory `.git` specifica del worktree, non quella del repository principale). Le regole globali in `~/.config/git/ignore` si applicano a tutti i worktree come a tutti i repository.

### 26. Come posso verificare se un oggetto Git esiste ancora nell'object database?

```bash
# Verificare l'esistenza di un singolo oggetto
git cat-file -t a1b2c3d    # Mostra il tipo (commit, tree, blob, tag)
# Se l'oggetto non esiste: fatal: Not a valid object name

# Verificare e mostrare il contenuto
git cat-file -p a1b2c3d    # Mostra il contenuto dell'oggetto

# Verificare l'esistenza senza output (solo exit code)
git cat-file -e a1b2c3d 2>/dev/null && echo "esiste" || echo "non esiste"
```

---

## Riferimenti

- **Git Documentation — git-stash**: https://git-scm.com/docs/git-stash
- **Git Documentation — git-reset**: https://git-scm.com/docs/git-reset
- **Git Documentation — git-revert**: https://git-scm.com/docs/git-revert
- **Git Documentation — git-bisect**: https://git-scm.com/docs/git-bisect
- **Git Documentation — git-blame**: https://git-scm.com/docs/git-blame
- **Git Documentation — git-log**: https://git-scm.com/docs/git-log
- **Git Documentation — git-reflog**: https://git-scm.com/docs/git-reflog
- **Git Pro Book — Git Tools - Revision Selection**: https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection
- **Git Pro Book — Debugging with Git**: https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git

---

## Esercizi

### Esercizio 1: Stash Workflow Completo

```bash
# Obiettivo: padroneggiare tutte le operazioni di stash

# 1. Setup:
git init stash-lab && cd stash-lab
echo "v1" > app.txt && git add . && git commit -m "init"

# 2. Creare modifiche non committate:
echo "work in progress" >> app.txt
echo "new file" > temp.txt

# 3. Stash con messaggio e file non tracciati:
git stash push -u -m "wip: feature login"

# 4. Verificare che il working tree è pulito:
git status  # Deve essere clean
ls temp.txt 2>/dev/null || echo "temp.txt non esiste"

# 5. Creare un secondo stash:
echo "altra modifica" >> app.txt
git stash push -m "wip: fix bug"

# 6. Esplorare lo stash:
git stash list
git stash show -p stash@{0}
git stash show -p stash@{1}

# 7. Applicare selettivamente:
git stash apply stash@{1}  # Applicare il primo stash (login)
git stash drop stash@{1}   # Rimuoverlo dalla lista

# 8. Creare un branch dallo stash rimanente:
git stash branch bugfix-branch stash@{0}
git log --oneline  # Lo stash è diventato un commit
```

### Esercizio 2: Reset — Tre Livelli di Severità

```bash
# Obiettivo: capire la differenza tra --soft, --mixed e --hard

# 1. Setup con 3 commit:
git init reset-lab && cd reset-lab
echo "v1" > app.txt && git add . && git commit -m "commit 1"
echo "v2" >> app.txt && git add . && git commit -m "commit 2"
echo "v3" >> app.txt && git add . && git commit -m "commit 3"

# 2. Salvare l'hash corrente:
ORIGINAL=$(git rev-parse HEAD)

# 3. Reset --soft (mantiene staging e working tree):
git reset --soft HEAD~1
git status   # commit 3 è in staging (pronto per commit)
git diff --cached  # Mostra le modifiche di commit 3

# 4. Ripristinare e provare --mixed (mantiene solo working tree):
git reset --hard $ORIGINAL
git reset --mixed HEAD~1
git status   # commit 3 è nel working tree (non staged)
git diff     # Mostra le modifiche di commit 3

# 5. Ripristinare e provare --hard (scarta tutto):
git reset --hard $ORIGINAL
git reset --hard HEAD~1
git status   # Tutto pulito — le modifiche di commit 3 sono PERSE
git diff     # Niente

# 6. Recuperare con reflog:
git reflog
git reset --hard $ORIGINAL  # Ripristinato!
```

### Esercizio 3: Reflog Recovery — Salvare un Rebase Fallito

```bash
# Obiettivo: usare reflog per recuperare da un rebase andato male

# 1. Setup:
git init reflog-lab && cd reflog-lab
echo "base" > app.txt && git add . && git commit -m "base"
git checkout -b feature
echo "feature 1" >> app.txt && git commit -am "feat: feature 1"
echo "feature 2" >> app.txt && git commit -am "feat: feature 2"
echo "feature 3" >> app.txt && git commit -am "feat: feature 3"

# 2. Salvare lo stato pre-rebase:
PRE_REBASE=$(git rev-parse HEAD)

# 3. Simulare un rebase problematico:
git checkout main
echo "main change" >> app.txt && git commit -am "fix: main change"
git checkout feature
# Il rebase causerà conflitti:
git rebase main || true

# 4. Decidere che il rebase è andato male:
git rebase --abort

# 5. Verificare che lo stato originale è preservato:
git log --oneline  # Deve corrispondere a $PRE_REBASE

# 6. Se --abort non funzionasse, usare reflog:
git reflog
# Trovare l'entry "checkout: moving from main to feature"
# git reset --hard <hash-pre-rebase>
```

### Esercizio 4: Git Bisect — Trovare il Commit del Bug

```bash
# Obiettivo: usare bisect manuale e automatizzato per trovare un bug

# 1. Setup — simulare una cronologia con un bug introdotto a metà:
git init bisect-lab && cd bisect-lab
for i in $(seq 1 10); do
    echo "commit $i" >> app.txt
    if [ $i -eq 6 ]; then
        echo "BUG_HERE" >> app.txt  # Il bug è nel commit 6
    fi
    git add . && git commit -m "commit $i"
done

# 2. Bisect manuale:
git bisect start
git bisect bad HEAD          # Il commit corrente ha il bug
git bisect good HEAD~9       # Il primo commit era OK

# 3. Ad ogni step, testare:
# Se app.txt contiene "BUG_HERE" → git bisect bad
# Se app.txt NON contiene "BUG_HERE" → git bisect good
# grep -q "BUG_HERE" app.txt && git bisect bad || git bisect good

# 4. Bisect automatizzato con script:
git bisect reset
git bisect start HEAD HEAD~9
git bisect run bash -c '! grep -q BUG_HERE app.txt'
# Lo script esce con 0 se il bug non c'è (good), 1 se c'è (bad)

# 5. Osservare il risultato: Git indica il commit 6
git bisect reset
```

### Esercizio 5: Revert vs Reset — Scelta Strategica

```bash
# Obiettivo: comprendere quando usare revert vs reset

# 1. Setup con branch condiviso:
git init revert-lab && cd revert-lab
echo "v1" > app.txt && git add . && git commit -m "feat: v1"
echo "v2" >> app.txt && git commit -am "feat: v2"
echo "v3 - buggy" >> app.txt && git commit -am "feat: v3 (bug)"
echo "v4" >> app.txt && git commit -am "feat: v4"

# 2. Scenario A — Branch privato (usa reset):
git checkout -b private-fix
git reset --hard HEAD~2  # Rimuovi commit v3 e v4
# La cronologia è riscritta — OK perché il branch è privato

# 3. Scenario B — Branch pubblico (usa revert):
git checkout main
git revert HEAD~1 --no-edit  # Crea un NUOVO commit che annulla v3
git log --oneline  # v4 è preservato, v3 è annullato

# 4. Revert di un merge commit:
git checkout -b merge-test
echo "merge content" >> app.txt && git commit -am "merge content"
git checkout main
git merge --no-ff merge-test -m "merge: merge-test"
# Revert del merge specificando il parent:
git revert HEAD -m 1 --no-edit
git log --graph --oneline

# 5. Discutere: perché non si deve fare reset --hard su un branch condiviso?
```

---

## Letture consigliate

- **Git Pro Book — Reset Demystified** — https://git-scm.com/book/en/v2/Git-Tools-Reset-Demystified (consultato: 2026-05-24). Trattamento approfondito di `git reset` con diagrammi dei tre livelli e interazione con index e working tree.

- **Git Pro Book — Stashing and Cleaning** — https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning (consultato: 2026-05-24). Guida ufficiale a `git stash` con workflow avanzati e `git clean`.

- **Git Pro Book — Debugging with Git** — https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git (consultato: 2026-05-24). Capitolo che copre `git bisect`, `git blame` e `git grep` per il debugging.

- **Git Pro Book — Revision Selection** — https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection (consultato: 2026-05-24). Guida alla sintassi di selezione delle revisioni: `HEAD~N`, `HEAD^`, `@{n}`, range di commit.

- **"How to undo (almost) anything with Git" (GitHub Blog)** — https://github.blog/open-source/git/how-to-undo-almost-anything-with-git/ (consultato: 2026-05-24). Articolo pratico del blog GitHub che cataloga le tecniche di undo per ogni scenario comune.

- **Git Documentation — git-reflog** — https://git-scm.com/docs/git-reflog (consultato: 2026-05-24). Documentazione ufficiale del reflog con opzioni di scadenza e formato output.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Fondamenti Git: staging, working tree, commit | 01 | [01-fondamenti-git.md](01-fondamenti-git.md) |
| Branching e Merge: rebase, cherry-pick, merge | 06 | [06-git-branching-merge-avanzato.md](06-git-branching-merge-avanzato.md) |
| Git Internals: oggetti, refs, HEAD, reflog | 07 | [07-git-interni-oggetti-refs.md](07-git-interni-oggetti-refs.md) |
| Git Hooks: pre-commit, automazione commit | 08 | [08-git-hooks-automazione.md](08-git-hooks-automazione.md) |
| LFS e Submodules: gestione repository complessi | 09 | [09-git-lfs-submodules-monorepo.md](09-git-lfs-submodules-monorepo.md) |
| Gitignore e Configurazione: alias, opzioni reset | 11 | [11-gitignore-gitattributes-config.md](11-gitignore-gitattributes-config.md) |
| Workflow di team: protezione branch, review | 20 | [20-git-workflow-team-guida-completa.md](20-git-workflow-team-guida-completa.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **bisect** | Comando Git che esegue una ricerca binaria nella cronologia dei commit per identificare il primo commit che ha introdotto un bug o una regressione. |
| **blame** | Comando `git blame` che mostra, per ogni riga di un file, l'ultimo commit che l'ha modificata, con autore, data e hash. Utile per tracciare l'origine di una modifica. |
| **detached HEAD** | Stato in cui HEAD punta direttamente a un commit invece che a un branch. I commit creati in questo stato diventano dangling se non si crea un branch. |
| **force-with-lease** | Flag di `git push` che verifica che il remote non sia stato aggiornato da altri prima di sovrascrivere. Alternativa sicura a `--force` per branch personali. |
| **hard reset** | `git reset --hard` — sposta HEAD, resetta l'index e il working tree. Le modifiche non committate sono perse irrecuperabilmente (eccetto tramite reflog per i commit). |
| **mixed reset** | `git reset --mixed` (default) — sposta HEAD e resetta l'index, ma preserva le modifiche nel working tree come unstaged. |
| **reflog** | Log locale che registra ogni spostamento di HEAD e dei branch. Consente di recuperare commit apparentemente persi dopo reset, rebase o operazioni distruttive. I record scadono dopo 90 giorni. |
| **revert** | Comando Git che crea un nuovo commit che annulla le modifiche di un commit precedente. Preserva la cronologia pubblica, a differenza di reset. |
| **soft reset** | `git reset --soft` — sposta HEAD ma preserva sia l'index (staging area) sia il working tree. Le modifiche risultano staged e pronte per il commit. |
| **stash** | Area di storage temporaneo di Git che salva modifiche non committate (staged e unstaged) permettendo di pulire il working tree senza perdere lavoro. |
| **stash pop** | Comando che applica l'ultimo stash al working tree e lo rimuove dalla lista degli stash. Se l'applicazione causa conflitti, lo stash non viene rimosso. |
| **three-tree architecture** | Modello concettuale di Git con tre "alberi": HEAD (ultimo commit), Index (staging area) e Working Tree (file su disco). `git reset` opera su questi tre livelli. |
| **untracked file** | File presente nel working tree ma non nell'index né in nessun commit. Ignorato da `git stash` a meno di usare il flag `-u` (include untracked). |
