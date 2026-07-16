# Tutorial: Git per Pythonisti — Dal Principiante all'Esperto

> **Companion to:** `00-git-per-pythonisti.md`
> **Scope:** Controllo versione con Git, repository locale e remoto su GitHub, branch e merge, `.gitignore` per Python, pre-commit hooks, GitHub Actions per CI/CD, Conventional Commits, firma GPG, sicurezza secrets.
> **Prerequisiti:** `tutorial_00_ambiente_setup.md` completato (Git installato, account GitHub creato)
> **Durata stimata:** 15–20 ore
> **Lingua:** Italiano — termini tecnici in inglese dove standard nel settore
> **Versioni di riferimento:** Git 2.45+ · GitHub CLI 2.52+ · pre-commit 3.x · git-cliff 2.x

---

## Indice Generale

- [Prima di Iniziare: Il Problema del documento_finale_V3_QUESTA_SI.docx](#prima-di-iniziare)
- [Parte A: Le Basi Assolute](#parte-a-le-basi-assolute)
  - [A1 — Vocabolario Git con Analogie](#a1--vocabolario-git-con-analogie)
  - [A2 — Installazione e Configurazione Iniziale](#a2--installazione-e-configurazione-iniziale)
  - [A3 — Il Primo Repository](#a3--il-primo-repository)
  - [A4 — Leggere la Storia del Progetto](#a4--leggere-la-storia-del-progetto)
  - [A5 — .gitignore per Python](#a5--gitignore-per-python)
- [Parte B: Comprensione Profonda](#parte-b-comprensione-profonda)
  - [B1 — Come Git Salva i Dati (Internals per Principianti)](#b1--come-git-salva-i-dati)
  - [B2 — Branch: Lavorare in Parallelo](#b2--branch-lavorare-in-parallelo)
  - [B3 — Merge e Conflitti](#b3--merge-e-conflitti)
  - [B4 — GitHub: Il Repository Remoto](#b4--github-il-repository-remoto)
  - [B5 — Pull Request: Il Flusso di Collaborazione](#b5--pull-request-il-flusso-di-collaborazione)
  - [B6 — Git Stash: Metti da Parte il Lavoro](#b6--git-stash-metti-da-parte-il-lavoro)
  - [B7 — Tag: Marcare le Versioni](#b7--tag-marcare-le-versioni)
  - [B8 — pre-commit Hooks con Python](#b8--pre-commit-hooks-con-python)
  - [B9 — Conventional Commits](#b9--conventional-commits)
  - [B10 — GitHub Actions: CI/CD di Base](#b10--github-actions-cicd-di-base)
- [Parte C: Esercizi Pratici Guidati](#parte-c-esercizi-pratici-guidati)
  - [C1 — Primo Repository da Zero (Guidato)](#c1--primo-repository-da-zero-guidato)
  - [C2 — Push su GitHub (Guidato)](#c2--push-su-github-guidato)
  - [C3 — Feature Branch e Merge (Guidato)](#c3--feature-branch-e-merge-guidato)
  - [C4 — Simulare e Risolvere un Conflitto (Guidato)](#c4--simulare-e-risolvere-un-conflitto-guidato)
  - [C5 — .gitignore Completo (Semi-autonomo)](#c5--gitignore-completo-semi-autonomo)
  - [C6 — pre-commit con ruff e mypy (Semi-autonomo)](#c6--pre-commit-con-ruff-e-mypy-semi-autonomo)
  - [C7 — Conventional Commits per una Settimana (Semi-autonomo)](#c7--conventional-commits-per-una-settimana-semi-autonomo)
  - [C8 — GitHub Actions per pytest (Autonomo)](#c8--github-actions-per-pytest-autonomo)
  - [C9 — Fork e Pull Request (Autonomo)](#c9--fork-e-pull-request-autonomo)
  - [C10 — Release con Tag e Changelog (Autonomo, Sfida)](#c10--release-con-tag-e-changelog-autonomo-sfida)
- [Parte D: Approfondimento per Esperti](#parte-d-approfondimento-per-esperti)
  - [D1 — Git Internals Profondi](#d1--git-internals-profondi)
  - [D2 — Rebase Interattivo](#d2--rebase-interattivo)
  - [D3 — git bisect: Trovare il Commit Colpevole](#d3--git-bisect-trovare-il-commit-colpevole)
  - [D4 — Firma Commit con GPG/SSH](#d4--firma-commit-con-gpgssh)
  - [D5 — Secret Scanning e Sicurezza](#d5--secret-scanning-e-sicurezza)
  - [D6 — Monorepo con Git](#d6--monorepo-con-git)
  - [D7 — Git Hook Avanzati](#d7--git-hook-avanzati)
- [Parte E: Riepilogo, Checklist e Prossimi Passi](#parte-e-riepilogo-checklist-e-prossimi-passi)
  - [Checklist Git Essenziale](#checklist-git-essenziale)
  - [Cheat Sheet Comandi Git](#cheat-sheet-comandi-git)
  - [Glossario Git Completo](#glossario-git-completo)
  - [Errori Git Più Comuni e Soluzioni](#errori-git-piu-comuni-e-soluzioni)
  - [Prossimi Passi](#prossimi-passi)

---

## Prima di Iniziare

### Il Problema del `documento_finale_V3_QUESTA_SI.docx`

Immagina questa scena. Hai lavorato per settimane su un documento importante — forse una tesi, una relazione, il codice di un progetto. Con il passare del tempo, la tua cartella è diventata qualcosa di simile a questo:

```
📁 Progetto/
├── codice.py
├── codice_backup.py
├── codice_backup_2.py
├── codice_finale.py
├── codice_finale_VERO.py
├── codice_finale_VERO_questo_funziona.py
├── codice_finale_VERO_questo_funziona_v2.py
├── codice_DEFINITIVO.py
├── codice_DEFINITIVO_con_fix.py
├── codice_DEFINITIVO_con_fix_marzo.py
├── codice_DEFINITIVO_con_fix_marzo_FUNZIONA.py
└── codice_QUESTO_SI_FUNZIONA_DAVVERO_FINALE.py
```

Se ti riconosci in questa descrizione, non sei solo. Questa è la strategia di backup manuale che tutti abbiamo adottato prima di conoscere Git.

Il problema con questo approccio è che:

1. **Non sai quale versione è l'ultima** — dopo settimane di lavoro, il nome del file più lungo non è necessariamente il più recente.

2. **Non sai cosa è cambiato** — se apri `codice_finale_VERO.py` e `codice_DEFINITIVO_con_fix.py`, devi confrontarli a mano riga per riga per capire la differenza.

3. **Hai paura di eliminare file** — cosa succede se cancelli `codice_backup_2.py` e poi scopri che conteneva una funzione importante che non hai copiato nell'ultima versione?

4. **Non puoi tornare indietro con precisione** — se stai lavorando su `codice_QUESTO_SI_FUNZIONA_DAVVERO_FINALE.py` e rompi qualcosa, quale versione devi ripristinare?

5. **La collaborazione è un incubo** — se devi lavorare con un collega, come fate a evitare di sovrascrivervi a vicenda? Email? Dropbox? Il risultato è spesso un disastro.

### Cosa Risolve Git

Git è un **sistema di controllo versione** — un programma che tiene traccia di ogni modifica che fai ai tuoi file, permettendoti di:

- Vedere la storia completa di ogni modifica, con data, autore e descrizione
- Tornare a qualsiasi versione precedente del tuo progetto in pochi secondi
- Lavorare su nuove funzionalità senza rischiare di rompere ciò che già funziona
- Collaborare con altri senza sovrascriversi a vicenda
- Capire esattamente cosa è cambiato tra una versione e l'altra

Con Git, la cartella del tuo progetto contiene un solo file `codice.py`, e Git sa tutto ciò che è mai successo a quel file. Niente duplicati, niente `_finale_VERO_v3.py`.

### Cosa Imparerai in Questo Tutorial

Questo tutorial è diviso in cinque parti:

**Parte A** copre le basi assolute: il vocabolario di Git, l'installazione, come creare il primo repository, come leggere la storia delle modifiche e come ignorare i file che non devono essere tracciati.

**Parte B** ti porta a una comprensione più profonda: come Git salva i dati internamente, come lavorare su più funzionalità contemporaneamente con i branch, come collaborare su GitHub, come automatizzare i controlli di qualità prima di ogni commit, e come generare un changelog automatico.

**Parte C** contiene dieci esercizi pratici, dalla semplicità assoluta fino a sfide che simulano situazioni reali di lavoro professionale.

**Parte D** è per chi vuole diventare esperto: git internals profondi, rebase interattivo, ricerca di bug con bisect, firma dei commit con GPG, sicurezza dei segreti.

**Parte E** è il riepilogo finale: checklist, cheat sheet, glossario completo, errori comuni e cosa fare dopo.

> **Nota pratica:** Questo tutorial assume che tu abbia completato `tutorial_00_ambiente_setup.md`. In particolare, assume che tu abbia Python installato, un terminale funzionante, e un account GitHub. Non è necessario avere Git già installato — lo installeremo nella sezione A2.

---

## Parte A: Le Basi Assolute

Questa parte ti porterà da zero alla capacità di gestire un progetto Python con Git in modo autonomo. Ogni sezione include comandi con output atteso commentato e spiegato riga per riga.

---

### A1 — Vocabolario Git con Analogie

Prima di toccare un solo comando, è importante capire il vocabolario di Git. Ogni sistema tecnico ha il suo gergo, e Git non fa eccezione. La buona notizia è che tutti i concetti di Git hanno un equivalente nel mondo reale che li rende immediatamente intuitivi.

---

#### Repository (o "Repo")

**Definizione tecnica:** Una directory del tuo filesystem che contiene il codice del progetto più una sottocartella nascosta chiamata `.git/` dove Git memorizza tutta la storia del progetto.

**Analogia:** Pensa a un repository come a un **archivio fisico professionale** — come quelli che vedi negli uffici storici o nelle biblioteche. Contiene tutti i documenti correnti (il tuo codice) ma anche una sezione speciale con l'archivio storico di ogni versione di ogni documento che sia mai esistita. Non è solo una cartella — è una cartella con memoria fotografica.

**In pratica:** Quando crei un repository, Git crea una sottocartella nascosta `.git/` nella tua directory di progetto. Questa cartella è il "cervello" di Git per quel progetto. Non la toccare mai manualmente.

---

#### Commit

**Definizione tecnica:** Una fotografia istantanea (snapshot) dell'intero progetto in un momento specifico, con metadati: autore, data, ora, e un messaggio descrittivo scritto dallo sviluppatore.

**Analogia:** Un commit è come **scattare una fotografia del tuo progetto**. Ogni fotografia ha:
- Una data e un'ora (quando hai scattato)
- Un autore (chi ha scattato)
- Una didascalia (il messaggio di commit che descrivi tu stesso)
- Un codice univoco (un hash SHA-1 come `4f2a1b3`)

La differenza fondamentale rispetto a una fotografia normale è che puoi **tornare** a qualsiasi fotografia del passato in qualsiasi momento. Non sono ricordi — sono stati del progetto a cui puoi ritornare.

**Cosa contiene un commit:**

```
Commit: 4f2a1b3
Autore: Mario Rossi <mario@example.com>
Data:   2026-07-15 14:32:00 +0200
Messaggio: aggiunge validazione email per l'utente

Modifiche:
  - src/models.py      (modificato: aggiunte 15 righe)
  - tests/test_models.py (nuovo file: 25 righe)
```

---

#### Working Directory (Directory di Lavoro)

**Definizione tecnica:** La directory del tuo filesystem dove lavori effettivamente — dove apri, modifichi e salvi i file.

**Analogia:** La **scrivania** dove lavori. Metti i documenti sulla scrivania, li modifichi, li scrivi. Quello che vedi sulla scrivania in questo momento è la working directory.

**Cosa significa nella pratica:** Quando modifichi un file con il tuo editor di testo, stai modificando la working directory. Le modifiche non sono ancora "salvate" in Git — sono solo modifiche locali sul tuo computer.

---

#### Staging Area (Area di Preparazione)

**Definizione tecnica:** Uno spazio intermedio tra la working directory e il repository. I file nell'area di staging sono quelli che verranno inclusi nel prossimo commit.

**Analogia:** Immagina di avere modificato cinque documenti sulla scrivania. Prima di "archiviare" definitivamente, metti nel **vassoio da protocollare** solo i documenti che vuoi includere in questa archiviazione. La staging area è quel vassoio.

**Perché esiste:** La staging area è una delle caratteristiche più potenti di Git. Ti permette di lavorare su dieci file ma committarne solo tre — quelli che logicamente appartengono insieme. Questo mantiene la storia del progetto pulita e leggibile.

**Il flusso:**
```
Working Directory  →  [git add]  →  Staging Area  →  [git commit]  →  Repository
(modifichi i file)                 (selezioni cosa)                  (salvi nella storia)
```

---

#### Branch (Ramo)

**Definizione tecnica:** Un puntatore leggero a un commit specifico. Creare un branch non duplica il codice — crea semplicemente un nuovo "filo narrativo" nella storia del progetto.

**Analogia:** Hai un documento importante. Vuoi provare una modifica radicale, ma hai paura di rovinare la versione originale. Fai una **fotocopia** del documento e lavori sulla fotocopia. Se la modifica va bene, sostituisci l'originale con la fotocopia migliorata. Se va male, butti via la fotocopia e l'originale è intatto.

In Git, creare un branch è ancora più efficiente di una fotocopia — Git non duplica i file, ma crea solo un segnalibro che dice "da questo punto in poi, questa è una versione alternativa del progetto".

**Il branch principale:** Per convenzione moderna, il branch principale si chiama `main` (in passato si chiamava `master`). Questo è il ramo "ufficiale" del progetto — la versione che funziona, che è testata, che viene mostrata al mondo.

---

#### Merge (Unione)

**Definizione tecnica:** L'operazione che unisce le modifiche di due branch in uno solo.

**Analogia:** Hai lavorato sulla fotocopia del documento (il branch di feature). Ora vuoi unire le tue modifiche con il documento originale (il branch main). Il **merge** è l'operazione di unione: Git confronta i due documenti e crea una versione che contiene il meglio di entrambi.

**Quando le modifiche non si toccano:** Se hai modificato la pagina 3 e il tuo collega ha modificato la pagina 7, il merge è automatico e senza problemi.

**Quando le modifiche si sovrappongono:** Se entrambi avete modificato la stessa riga dello stesso file, Git non sa quale versione preferire e chiede a te di decidere. Questo si chiama **conflitto** — e impareremo a risolverlo nella sezione B3.

---

#### HEAD

**Definizione tecnica:** Un riferimento speciale che punta al commit corrente — quello su cui stai lavorando "adesso".

**Analogia:** Il segnalibro nel libro che stai leggendo. Indica dove sei nella storia del progetto. Quando passi da un branch all'altro, HEAD si sposta.

**In pratica:** `HEAD` è quasi sempre l'ultimo commit del branch corrente. Quando vedi `HEAD~1` nei comandi Git, significa "un commit prima di HEAD" — l'equivalente di andare indietro di una pagina nel libro.

---

#### Remote (Repository Remoto)

**Definizione tecnica:** Una copia del repository memorizzata su un server remoto (come GitHub), a cui tutti i collaboratori possono accedere.

**Analogia:** Hai il tuo archivio fisico in ufficio (il repository locale sul tuo computer). Il remote è lo **stesso archivio conservato in una cassaforte centralizzata** accessibile a tutto il team. Quando vuoi condividere il tuo lavoro, "carichi" le modifiche dalla tua copia locale alla cassaforte centrale.

**GitHub, GitLab, Bitbucket:** Questi servizi ospitano i repository remoti. GitHub è il più popolare e quello che useremo in questo tutorial. GitHub non è Git — è un servizio che ospita repository Git su Internet.

---

#### .gitignore

**Definizione tecnica:** Un file di testo nella radice del repository che elenca i pattern di file e directory che Git deve ignorare completamente.

**Analogia:** Stai archiviando documenti nel tuo archivio professionale. Ci sono alcune cose che **non** vuoi archiviare: i rifiuti nel cestino, i post-it temporanei, le bozze scarabocchiate. Il `.gitignore` è la lista di "queste cose NON devo fotografare/archiviare".

**Per Python, le cose tipiche da ignorare:**
- `__pycache__/` — file bytecode Python generati automaticamente
- `.venv/` — l'ambiente virtuale (può essere ricreato da `pyproject.toml`)
- `.env` — file con password e chiavi API (mai mettere segreti in Git!)
- `*.pyc` — file compilati Python
- `dist/` e `build/` — file di packaging generati automaticamente

---

#### Clone

**Definizione tecnica:** Il comando che crea una copia locale completa di un repository remoto.

**Analogia:** Qualcuno ha creato un archivio professionale (repository) su GitHub. Tu vuoi lavorarci. Fai una **copia completa** dell'intero archivio sul tuo computer — inclusa tutta la storia. Questa è l'operazione di clone.

---

#### Pull e Push

**Pull:** Scarica le ultime modifiche dal repository remoto e le integra nella tua copia locale. Come "sincronizzare" la tua copia con quella centrale.

**Push:** Carica le tue modifiche locali nel repository remoto. Come "archiviare" il tuo lavoro nella cassaforte centrale.

**Regola pratica:**
- Prima di iniziare a lavorare: `git pull` (porta le ultime novità)
- Dopo aver finito il lavoro: `git push` (condividi il tuo lavoro)

---

#### Riepilogo Visivo del Vocabolario

```
Il tuo computer:
┌─────────────────────────────────────────────────────────────────┐
│  Working Directory    Staging Area    Repository Locale (.git/) │
│  ─────────────────    ────────────    ──────────────────────────│
│  [file modificati]  → [git add] →   [commit 1] → [commit 2]   │
│                                         │                        │
│                      [git commit] ──────┘                        │
└─────────────────────────────────────────────────────────────────┘
                                              │
                                    [git push / git pull]
                                              │
Internet (GitHub/GitLab):         ┌───────────────────────┐
                                  │  Repository Remoto     │
                                  │  [commit 1] → [commit 2]│
                                  └───────────────────────┘
```

---

### A2 — Installazione e Configurazione Iniziale

> **Nota:** Se hai già seguito `tutorial_00_ambiente_setup.md`, potresti avere già Git installato. Verifica con `git --version` nel terminale. Se vedi un numero di versione, vai direttamente alla sezione "Configurazione Globale". Se vedi un errore, procedi con l'installazione.

#### Verifica se Git è già installato

Apri il terminale (su Windows: cerca "PowerShell" o "Git Bash" nel menu Start) e digita:

```powershell
git --version
```

**Se Git è già installato, vedrai qualcosa come:**

```
git version 2.45.2.windows.1
```

**Se Git NON è installato, vedrai:**

```
git : The term 'git' is not recognized as the name of a cmdlet, function,
script file, or operable program.
```

In questo caso, procedi con l'installazione.

---

#### Installazione su Windows

**Metodo raccomandato — winget (Windows Package Manager):**

`winget` è il gestore di pacchetti ufficiale di Windows, disponibile su Windows 10 (versione 1809 o superiore) e Windows 11.

Apri PowerShell come amministratore (tasto destro su PowerShell → "Esegui come amministratore") e digita:

```powershell
winget install --id Git.Git -e --source winget
```

**Cosa fa questo comando:**
- `winget install` — installa un pacchetto
- `--id Git.Git` — specifica il pacchetto Git ufficiale
- `-e` — corrispondenza esatta dell'ID (evita ambiguità)
- `--source winget` — usa il catalogo winget di Microsoft

**Output atteso durante l'installazione:**

```
Found Git [Git.Git] Version 2.45.2
This application is licensed to you by its owner.
Microsoft is not responsible for, nor does it grant any licenses to, third-party packages.
Downloading https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/Git-2.45.2-64-bit.exe
  ██████████████████████████████  57.3 MB / 57.3 MB
Successfully verified installer hash
Starting package install...
Successfully installed
```

**Se preferisci il metodo manuale (download diretto):**

1. Vai su `https://git-scm.com/download/win`
2. Scarica la versione a 64 bit (Git-2.xx.x-64-bit.exe)
3. Esegui l'installer
4. Nelle opzioni, lascia tutti i valori predefiniti (sono già ottimali)
5. Clicca "Next" fino a "Install", poi "Finish"

**Dopo l'installazione, apri un nuovo terminale e verifica:**

```powershell
git --version
```

**Output atteso:**

```
git version 2.45.2.windows.1
```

> **Importante:** Dopo l'installazione di Git, devi aprire un **nuovo** terminale per vedere il comando disponibile. Il terminale già aperto non vedrà i nuovi programmi installati.

---

#### Cosa include Git for Windows

L'installazione di Git su Windows include tre componenti:

1. **git.exe** — il programma principale da riga di comando
2. **Git Bash** — un terminale POSIX (simile a Linux/macOS) che include comandi come `bash`, `ssh`, `curl`
3. **Git Credential Manager** — gestisce le credenziali in modo sicuro (non devi reinserire username e password ogni volta)

Per questo tutorial useremo **PowerShell** o **Git Bash** indifferentemente. Quando i comandi sono gli stessi (e per Git lo sono quasi sempre), mostreremo la versione valida per entrambi.

---

#### Configurazione Globale — Il Tuo Biglietto da Visita

Prima di usare Git per la prima volta, devi configurare la tua identità. Ogni commit che crei includerà il tuo nome e la tua email — questo è fondamentale per tracciare chi ha fatto cosa in un progetto collaborativo.

**Queste configurazioni si fanno una volta sola** e si applicano a tutti i repository sul tuo computer.

---

**Passo 1 — Configurare il nome:**

```bash
git config --global user.name "Mario Rossi"
```

Sostituisci `"Mario Rossi"` con il tuo nome reale. Usa le virgolette se il nome contiene spazi.

**Verifica:**

```bash
git config user.name
```

**Output atteso:**

```
Mario Rossi
```

---

**Passo 2 — Configurare l'email:**

```bash
git config --global user.email "mario.rossi@example.com"
```

Usa l'email che hai utilizzato per creare il tuo account GitHub. Questo è importante perché GitHub collega i commit al tuo profilo tramite l'email.

**Verifica:**

```bash
git config user.email
```

**Output atteso:**

```
mario.rossi@example.com
```

---

**Passo 3 — Configurare l'editor predefinito:**

Quando Git ha bisogno che tu scriva un messaggio (es. per un commit o per risolvere un merge), aprirà automaticamente un editor di testo. Per impostazione predefinita su Windows è Vim — un editor potente ma difficile da usare per i principianti.

**Se usi VS Code (raccomandato):**

```bash
git config --global core.editor "code --wait"
```

Il flag `--wait` dice a Git di aspettare che tu chiuda VS Code prima di continuare.

**Se preferisci Notepad++ su Windows:**

```bash
git config --global core.editor "'C:/Program Files/Notepad++/notepad++.exe' -multiInst -notabbar -nosession -noPlugin"
```

**Se preferisci il Blocco Note di Windows (semplicissimo):**

```bash
git config --global core.editor "notepad"
```

---

**Passo 4 — Impostare il nome del branch principale:**

La convenzione moderna usa `main` invece di `master` come nome del branch principale. Configuriamolo per evitare messaggi di avviso:

```bash
git config --global init.defaultBranch main
```

---

**Passo 5 — Configurare il comportamento di pull:**

```bash
git config --global pull.rebase false
```

Questa impostazione dice a Git di usare il comportamento classico (merge) quando scarichi aggiornamenti. È la scelta più intuitiva per i principianti — lo cambia in `true` più avanti quando avrai capito cosa è il rebase.

---

**Passo 6 — Impostare la gestione dei fine riga (solo Windows):**

Su Windows i file di testo usano `CRLF` come fine riga, mentre Linux e macOS usano solo `LF`. Python e i tool moderni preferiscono `LF`. Questa impostazione converte automaticamente:

```bash
git config --global core.autocrlf true
```

Questo significa: "quando faccio checkout, converti LF in CRLF; quando faccio commit, converti CRLF in LF". Il risultato è che nel repository i file hanno sempre `LF`, ma sul tuo Windows vengono visualizzati con `CRLF`.

---

**Verifica tutta la configurazione:**

```bash
git config --list --show-origin
```

**Output atteso:**

```
file:C:/Users/Mario/.gitconfig    user.name=Mario Rossi
file:C:/Users/Mario/.gitconfig    user.email=mario.rossi@example.com
file:C:/Users/Mario/.gitconfig    core.editor=code --wait
file:C:/Users/Mario/.gitconfig    init.defaultBranch=main
file:C:/Users/Mario/.gitconfig    pull.rebase=false
file:C:/Users/Mario/.gitconfig    core.autocrlf=true
```

> **Cosa significano le colonne:** La prima colonna indica il file di configurazione in cui si trovano le impostazioni. La seconda colonna mostra la chiave, la terza il valore. L'indicazione `file:.../.gitconfig` significa che queste impostazioni sono globali (valgono per tutti i repository).

---

#### Il file .gitconfig

Tutta questa configurazione viene salvata in un file nascosto nella tua home directory. Puoi vedere o modificare questo file direttamente:

```bash
cat ~/.gitconfig
```

**Output atteso (il file risultante):**

```ini
[user]
    name = Mario Rossi
    email = mario.rossi@example.com

[core]
    editor = code --wait
    autocrlf = true

[init]
    defaultBranch = main

[pull]
    rebase = false
```

> **Nota:** `~` è una scorciatoia per "la tua home directory". Su Windows con Git Bash corrisponde a `C:\Users\TuoNome\`. Su Windows con PowerShell usa invece `$HOME` o `%USERPROFILE%`.

---

#### Alias Utili (Opzionale ma Consigliato)

Gli alias sono abbreviazioni per comandi Git che usi spesso. Ne aggiungiamo alcuni molto utili:

```bash
git config --global alias.st status
git config --global alias.lg "log --oneline --decorate --graph --all"
git config --global alias.last "log -1 HEAD --stat"
```

**Cosa fanno:**
- `git st` → equivale a `git status`
- `git lg` → mostra la storia del progetto come grafo compatto
- `git last` → mostra l'ultimo commit con le statistiche dei file modificati

---

### A3 — Il Primo Repository

Ora che Git è installato e configurato, creiamo il nostro primo repository. Faremo tutto dal terminale, spiegando ogni passo e il relativo output.

> **Dove eseguire i comandi:** Apri PowerShell (o Git Bash). Per questo tutorial, useremo PowerShell su Windows. I comandi Git sono identici in entrambi i terminali; differiscono solo i comandi del sistema operativo (`mkdir`, `cd`, ecc.).

---

#### Creare la Directory del Progetto

```powershell
mkdir primo-progetto-git
cd primo-progetto-git
```

**Spiegazione:**
- `mkdir` crea una nuova directory (cartella)
- `cd` entra nella directory appena creata

**Output di mkdir:**

```
    Directory: C:\Users\Mario

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          15/07/2026    14:32                primo-progetto-git
```

**Output di cd:** Nessun output — il terminale cambia semplicemente directory.

---

#### Inizializzare il Repository

```bash
git init
```

**Output atteso:**

```
Initialized empty Git repository in C:/Users/Mario/primo-progetto-git/.git/
```

**Cosa è successo:** Git ha creato la sottocartella `.git/` nella directory corrente. Questa cartella è il cervello del repository — contiene tutta la configurazione e la storia del progetto.

**Verifichiamo cosa c'è dentro `.git/`:**

```bash
ls -la .git/
```

**Output atteso:**

```
total 36
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 ./
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 ../
-rw-r--r-- 1 mario 197609  23 Jul 15 14:32 HEAD
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 config
-rw-r--r-- 1 mario 197609  73 Jul 15 14:32 description
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 hooks/
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 info/
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 objects/
drwxr-xr-x 1 mario 197609   0 Jul 15 14:32 refs/
```

**Cosa contiene `.git/` — spiegato con l'analogia dell'archivio:**

| File/Directory | Contenuto | Analogia |
|----------------|-----------|----------|
| `HEAD` | Puntatore al branch corrente | Il segnalibro "sei qui" |
| `config` | Configurazione locale del repository | Le regole dell'archivio |
| `description` | Descrizione del repository (usata da GitWeb) | L'etichetta sulla copertina dell'archivio |
| `hooks/` | Script eseguiti automaticamente | I controlli automatici prima di archiviare |
| `objects/` | Il database di tutti i contenuti | Il magazzino dove sono conservate tutte le fotografie |
| `refs/` | I puntatori ai branch e ai tag | I segnalibri ai punti importanti della storia |

> **Regola importante:** Non modificare mai manualmente i file nella cartella `.git/`. Git gestisce questi file internamente. Modificarli manualmente può corrompere il repository.

---

#### Il Primo git status

Dopo `git init`, il repository è vuoto. Chiediamo a Git com'è la situazione:

```bash
git status
```

**Output atteso:**

```
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
```

**Spiegazione riga per riga:**

- `On branch main` — Sei sul branch chiamato `main`. Questo è il branch principale, creato automaticamente da `git init` (grazie alla configurazione `init.defaultBranch = main` che abbiamo fatto).

- `No commits yet` — Non hai ancora fatto nessun commit. La storia è vuota — nessuna fotografia del progetto è stata ancora scattata.

- `nothing to commit (create/copy files and use "git add" to track)` — Non c'è niente da committare perché la directory è vuota. Git ti suggerisce cosa fare: crea dei file e usa `git add` per iniziare a tracciarli.

---

#### Creare il Primo File

Creiamo un semplice file Python:

```bash
# Su PowerShell
New-Item -ItemType File -Name "saluta.py"
```

Ora apri `saluta.py` con il tuo editor e scrivi:

```python
# saluta.py
# Il mio primo file Python in un repository Git


def saluta(nome: str) -> str:
    """Restituisce un saluto personalizzato."""
    return f"Ciao, {nome}! Benvenuto nel mondo di Git."


if __name__ == "__main__":
    messaggio = saluta("Mondo")
    print(messaggio)
```

Salva il file.

---

#### git status dopo la creazione del file

```bash
git status
```

**Output atteso:**

```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        saluta.py

nothing added to commit but untracked files present (use "git add" to track)
```

**Spiegazione riga per riga:**

- `On branch main` — Sempre sul branch main.

- `No commits yet` — Ancora nessun commit.

- `Untracked files:` — Git ha rilevato che c'è un nuovo file (`saluta.py`) ma non lo sta ancora tracciando. I file "untracked" sono file che esistono nella working directory ma che Git non conosce.

- `(use "git add <file>..." to include in what will be committed)` — Git stesso ti suggerisce il prossimo passo: usa `git add` per iniziare a tracciare il file.

- `saluta.py` — Il file non tracciato. In un terminale con supporto colori, questo appare in **rosso**.

- `nothing added to commit but untracked files present` — C'è qualcosa nella directory ma non è ancora pronto per essere committato.

---

#### git add — Aggiungere il File alla Staging Area

```bash
git add saluta.py
```

Questo comando non produce output (a meno che non ci siano errori). Verifichiamo cosa è cambiato:

```bash
git status
```

**Output atteso:**

```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   saluta.py
```

**Spiegazione riga per riga:**

- `Changes to be committed:` — Questa sezione mostra i file nella staging area — quelli che verranno inclusi nel prossimo commit. In un terminale con colori, tutto ciò che è in questa sezione appare in **verde**.

- `(use "git rm --cached <file>..." to unstage)` — Git ti dice come rimuovere un file dalla staging area se ci hai messo qualcosa per errore.

- `new file:   saluta.py` — Il file `saluta.py` è stato aggiunto alla staging area. L'etichetta `new file:` indica che è un file nuovo (non una modifica a un file già esistente).

**Il cambiamento di stato:**

```
PRIMA di git add:    saluta.py è "Untracked"  (rosso)
DOPO git add:        saluta.py è "Staged"     (verde)
```

---

#### git commit — Salvare nella Storia

Ora creiamo il primo commit — la prima "fotografia" del progetto:

```bash
git commit -m "feat: aggiunge funzione saluta con type hints"
```

**Spiegazione del comando:**
- `git commit` — Crea un nuovo commit
- `-m "..."` — Specifica il messaggio del commit direttamente nella riga di comando. Senza `-m`, Git aprirebbe l'editor di testo configurato.

**Output atteso:**

```
[main (root-commit) 4f2a1b3] feat: aggiunge funzione saluta con type hints
 1 file changed, 12 insertions(+)
 create mode 100644 saluta.py
```

**Spiegazione dell'output riga per riga:**

- `[main (root-commit) 4f2a1b3]` — Tra le parentesi quadre:
  - `main` — il branch su cui è stato creato il commit
  - `(root-commit)` — questo è il primissimo commit del repository (la "radice" della storia)
  - `4f2a1b3` — le prime 7 cifre dell'hash SHA-1 univoco di questo commit (il tuo sarà diverso)

- `feat: aggiunge funzione saluta con type hints` — il messaggio del commit che hai scritto

- `1 file changed, 12 insertions(+)` — statistiche: 1 file modificato, 12 righe aggiunte

- `create mode 100644 saluta.py` — il file `saluta.py` è stato aggiunto al repository con i permessi `100644` (file normale leggibile da tutti)

---

#### Verificare dopo il Commit

```bash
git status
```

**Output atteso:**

```
On branch main
nothing to commit, working tree clean
```

**Cosa significa:** La staging area è vuota, la working directory non ha modifiche — tutto è stato committato. `working tree clean` è Git che ti dice "tutto è sincronizzato, non c'è niente di non salvato".

---

#### Aggiungere un Secondo Commit

Il progresso si vede solo con più di un commit. Aggiungiamo un secondo file:

```python
# README.md — crea questo file nella stessa directory
```

Crea un file `README.md` (in Markdown) con il seguente contenuto:

```markdown
# Primo Progetto Git

Un semplice progetto Python per imparare Git.

## Come usare

```python
from saluta import saluta

print(saluta("Mario"))
# Output: Ciao, Mario! Benvenuto nel mondo di Git.
```

## Requisiti

- Python 3.10+
```

Salva il file e poi:

```bash
git add README.md
git commit -m "docs: aggiunge README con esempio d'uso"
```

**Output atteso:**

```
[main f8c3a21] docs: aggiunge README con esempio d'uso
 1 file changed, 17 insertions(+)
 create mode 100644 README.md
```

---

#### Aggiungere un Terzo Commit con una Modifica

Ora modifichiamo `saluta.py` per aggiungere una nuova funzione:

```python
# saluta.py — versione aggiornata


def saluta(nome: str) -> str:
    """Restituisce un saluto personalizzato."""
    return f"Ciao, {nome}! Benvenuto nel mondo di Git."


def congeda(nome: str) -> str:
    """Restituisce un commiato personalizzato."""
    return f"Arrivederci, {nome}! Continua a praticare Git."


if __name__ == "__main__":
    print(saluta("Mondo"))
    print(congeda("Mondo"))
```

```bash
git add saluta.py
git commit -m "feat: aggiunge funzione congeda"
```

**Output atteso:**

```
[main 2c9e4b7] feat: aggiunge funzione congeda
 1 file changed, 6 insertions(+), 1 deletion(-)
```

**Nota:** `1 deletion(-)` perché abbiamo rimosso la riga `# saluta.py` (il vecchio commento) e aggiunto le nuove righe. Git conta a livello di riga — se modifichi una riga, è una cancellazione e un'aggiunta.

---

#### Riepilogo del Ciclo Fondamentale

Abbiamo appena eseguito il ciclo fondamentale di Git, che userai centinaia di volte ogni giorno:

```
1. Modifica i file nella working directory
         ↓
2. git add <file>     (aggiungi alla staging area)
         ↓
3. git commit -m "messaggio"  (salva nella storia)
         ↓
4. Ripeti
```

Questo ciclo semplice — **modifica → add → commit** — è il 90% di Git per il 90% del tempo. Tutto il resto che impareremo sono variazioni, ottimizzazioni e casi speciali di questo ciclo base.

---

#### Cosa fare se hai sbagliato il Messaggio del Commit

Se hai appena fatto un commit e ti accorgi di aver scritto il messaggio sbagliato, puoi correggerlo **prima di fare push**:

```bash
git commit --amend -m "feat: aggiunge funzione congeda con type hints"
```

> **Attenzione:** `--amend` riscrive il commit. Usalo **solo** se il commit non è ancora stato condiviso con altri (non ancora pushato su GitHub). Se lo usi su un commit già pushato, creerai problemi ai tuoi collaboratori.

---

#### Cosa fare se hai aggiunto il file sbagliato alla Staging Area

Se hai fatto `git add` per errore su un file che non vuoi committare:

```bash
git restore --staged nome-del-file.py
```

Questo rimuove il file dalla staging area (torna a "untracked" o "modified") senza toccare il contenuto del file.

---

#### Cosa fare se vuoi scartare le modifiche a un file

Se hai modificato un file ma vuoi tornare all'ultima versione committata:

```bash
git restore nome-del-file.py
```

> **Attenzione:** Questo scarta le modifiche non salvate **permanentemente**. Non c'è un Ctrl+Z per questo — le modifiche non committate non sono recuperabili (a meno che tu non le abbia messe da parte con `git stash`, che vedremo nella sezione B6).

---

#### Tabella: I Tre Stati di un File in Git

| Stato | Descrizione | Come arrivarci | Come uscire |
|-------|-------------|----------------|-------------|
| **Untracked** | File nuovo, Git non lo conosce | Creare un nuovo file | `git add file` |
| **Staged** | Nell'area di preparazione, pronto per il commit | `git add file` | `git restore --staged file` |
| **Committed** | Salvato nella storia del repository | `git commit` | Modifica il file |
| **Modified** | File tracciato che è stato modificato ma non staged | Modifica il file dopo un commit | `git add file` o `git restore file` |

Rileggere questa tabella più volte — capire questi quattro stati e come si transita tra loro è la chiave per usare Git con sicurezza.

---

> **Checkpoint A3:** A questo punto dovresti avere un repository con tre commit, due file (`saluta.py` e `README.md`), e una comprensione del ciclo modifica → add → commit. Se qualcosa non è chiaro, rileggi questa sezione prima di procedere.

---

## Parte A (continuazione)

### A4 — Leggere la Storia del Progetto

Git non serve solo a salvare le versioni — serve anche a leggere la storia del progetto. In questa sezione imparerai a leggere il log dei commit, a confrontare le versioni, e a ispezionare il contenuto di commit specifici.

---

#### git log — La Storia del Progetto

```bash
git log
```

**Output atteso** (per il nostro repository con tre commit):

```
commit 2c9e4b7a1d3f5e8c2b4a6d9f0e1c3b5a7d9f0e1c (HEAD -> main)
Author: Mario Rossi <mario.rossi@example.com>
Date:   Tue Jul 15 14:45:00 2026 +0200

    feat: aggiunge funzione congeda

commit f8c3a21b4d6e8f0a2b4c6d8e0f2a4c6e8f0a2b4 
Author: Mario Rossi <mario.rossi@example.com>
Date:   Tue Jul 15 14:40:00 2026 +0200

    docs: aggiunge README con esempio d'uso

commit 4f2a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5
Author: Mario Rossi <mario.rossi@example.com>
Date:   Tue Jul 15 14:35:00 2026 +0200

    feat: aggiunge funzione saluta con type hints
```

**Spiegazione di ogni campo:**

- **Prima riga** (`commit 2c9e4b7...`): L'hash SHA-1 completo (40 caratteri) del commit. Identifica univocamente questo commit nel repository. I tuoi hash saranno diversi — sono calcolati dal contenuto del commit.

- `(HEAD -> main)`: Indica che questo è il commit a cui punta `HEAD` (la posizione corrente) e che il branch `main` è qui. Quando fai un nuovo commit, `main` si sposterà in avanti.

- **Riga Author**: Il nome e l'email dell'autore — prese dalla configurazione `git config user.name` e `user.email`.

- **Riga Date**: Data e ora del commit nel formato: `Giorno_settimana Mese Giorno Ora Anno Fuso_orario`. Il fuso orario `+0200` significa CET (ora europea centrale, estate).

- **Messaggio**: Il messaggio che hai scritto con `-m "..."`. Appare rientrato di 4 spazi rispetto al margine sinistro.

---

#### git log --oneline — Il Log Compatto

Per vedere rapidamente la storia senza tutto il dettaglio:

```bash
git log --oneline
```

**Output atteso:**

```
2c9e4b7 (HEAD -> main) feat: aggiunge funzione congeda
f8c3a21 docs: aggiunge README con esempio d'uso
4f2a1b3 feat: aggiunge funzione saluta con type hints
```

**Ogni riga:** Hash abbreviato (7 caratteri) + eventuale posizione di branch/tag + messaggio.

Questo formato è quello che vedrai più spesso — è compatto e informativo. Usalo spesso per orientarti nella storia.

---

#### git log --oneline --graph --all — Il Grafo della Storia

Questo è il comando che useremo più avanti quando avremo più branch. Per ora, con un solo branch, l'output è simile al precedente ma con asterischi:

```bash
git log --oneline --graph --all
```

**Output atteso (con un solo branch):**

```
* 2c9e4b7 (HEAD -> main) feat: aggiunge funzione congeda
* f8c3a21 docs: aggiunge README con esempio d'uso
* 4f2a1b3 feat: aggiunge funzione saluta con type hints
```

**Quando avremo più branch** (lo vedremo nella sezione B2), questo comando diventa fondamentale perché mostra la struttura ad albero della storia:

```
* 3d5f7a9 (HEAD -> main) fix: corregge bug nel messaggio
| * 7b4c2e1 (feature/nuova-funzione) feat: aggiunge terza funzione
|/
* 2c9e4b7 feat: aggiunge funzione congeda
* f8c3a21 docs: aggiunge README con esempio d'uso
* 4f2a1b3 feat: aggiunge funzione saluta con type hints
```

Gli asterischi `*` sono i commit, le barre `|` e `/` mostrano le linee di branch. Questo è il DAG (Directed Acyclic Graph) della storia di Git.

---

#### git log con Filtri

Git log accetta molte opzioni per filtrare la storia. Vediamo le più utili:

**Ultimi N commit:**

```bash
git log -3
```

Mostra solo gli ultimi 3 commit nel formato standard.

---

**Commit con statistiche dei file:**

```bash
git log --stat
```

**Output atteso:**

```
commit 2c9e4b7a1d3f5e8c2b4a6d9f0e1c3b5a7d9f0e1c (HEAD -> main)
Author: Mario Rossi <mario.rossi@example.com>
Date:   Tue Jul 15 14:45:00 2026 +0200

    feat: aggiunge funzione congeda

 saluta.py | 7 +++++++
 1 file changed, 7 insertions(+)
```

La sezione `saluta.py | 7 +++++++` mostra: nome file, numero di righe cambiate, simboli `+` per righe aggiunte.

---

**Commit che hanno modificato un file specifico:**

```bash
git log --oneline -- saluta.py
```

**Output atteso:**

```
2c9e4b7 feat: aggiunge funzione congeda
4f2a1b3 feat: aggiunge funzione saluta con type hints
```

Nota: `f8c3a21` (README.md) non appare perché in quel commit non è stato toccato `saluta.py`.

---

**Ricerca nel contenuto dei commit (pickaxe):**

```bash
git log -S "congeda" --oneline
```

Cerca nel contenuto delle modifiche (non nel messaggio) la stringa `"congeda"`.

**Output atteso:**

```
2c9e4b7 feat: aggiunge funzione congeda
```

Questo è utile per trovare quando è stata introdotta (o rimossa) una funzione specifica.

---

**Ricerca nel messaggio di commit:**

```bash
git log --grep="docs" --oneline
```

**Output atteso:**

```
f8c3a21 docs: aggiunge README con esempio d'uso
```

---

#### git show — Ispezionare un Commit Specifico

```bash
git show 4f2a1b3
```

Mostra il contenuto completo del commit con quell'hash (puoi usare anche le prime 4-7 lettere dell'hash):

**Output atteso:**

```
commit 4f2a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5
Author: Mario Rossi <mario.rossi@example.com>
Date:   Tue Jul 15 14:35:00 2026 +0200

    feat: aggiunge funzione saluta con type hints

diff --git a/saluta.py b/saluta.py
new file mode 100644
index 0000000..7b3c2e1
--- /dev/null
+++ b/saluta.py
@@ -0,0 +1,12 @@
+# saluta.py
+# Il mio primo file Python in un repository Git
+
+
+def saluta(nome: str) -> str:
+    """Restituisce un saluto personalizzato."""
+    return f"Ciao, {nome}! Benvenuto nel mondo di Git."
+
+
+if __name__ == "__main__":
+    messaggio = saluta("Mondo")
+    print(messaggio)
```

**Come leggere un diff:**
- Le righe che iniziano con `+` (verde) sono righe **aggiunte**
- Le righe che iniziano con `-` (rosso) sono righe **rimosse**
- Le righe senza prefisso (bianche) sono **contesto** — mostrano le righe vicine non modificate
- `@@` indica la posizione nel file (numero di riga)

---

#### git diff — Vedere le Modifiche Non Committate

`git diff` mostra le differenze tra diverse versioni del codice. È uno dei comandi più utili per capire cosa sta cambiando.

Prima di tutto, modifichiamo `saluta.py` senza fare commit:

```python
# Aggiungi questa funzione in fondo a saluta.py

def conta_lettere(nome: str) -> int:
    """Conta le lettere nel nome."""
    return len(nome)
```

Ora eseguiamo:

```bash
git diff
```

**Output atteso:**

```
diff --git a/saluta.py b/saluta.py
index 7b3c2e1..9f4d8a2 100644
--- a/saluta.py
+++ b/saluta.py
@@ -11,3 +11,9 @@ if __name__ == "__main__":
     print(saluta("Mondo"))
     print(congeda("Mondo"))
 
+
+def conta_lettere(nome: str) -> int:
+    """Conta le lettere nel nome."""
+    return len(nome)
```

**Interpretazione del diff:**
- `--- a/saluta.py` — versione precedente del file
- `+++ b/saluta.py` — versione attuale del file
- `@@ -11,3 +11,9 @@` — nel file vecchio, il blocco mostra 3 righe a partire dalla riga 11; nel file nuovo, mostra 9 righe a partire dalla riga 11
- Le righe con `+` sono le nuove righe aggiunte

**git diff --staged — Vedere le Modifiche in Staging:**

```bash
git add saluta.py
git diff --staged
```

Dopo `git add`, le modifiche non appaiono più in `git diff` (che mostra solo le modifiche **non staged**). Per vedere le modifiche **staged**, usa `--staged` (o `--cached`, che è sinonimo).

---

#### Tabella Riepilogativa dei Comandi di Ispezione

| Comando | Cosa mostra |
|---------|-------------|
| `git log` | Storia completa dei commit |
| `git log --oneline` | Storia compatta (un commit per riga) |
| `git log --oneline --graph --all` | Storia compatta con grafo dei branch |
| `git log --stat` | Storia con statistiche dei file modificati |
| `git log -- file.py` | Storia dei commit che hanno toccato un file |
| `git log -S "stringa"` | Commit in cui è apparsa o scomparsa una stringa |
| `git show abc123` | Contenuto completo di un commit |
| `git diff` | Modifiche nella working directory non ancora staged |
| `git diff --staged` | Modifiche staged non ancora committate |
| `git diff abc123 def456` | Differenze tra due commit |

---

> **Esercizio breve:** Dopo aver aggiunto la funzione `conta_lettere`, fai il commit con il messaggio `"feat: aggiunge funzione conta_lettere"`. Poi usa `git log --oneline` per verificare che ora hai 4 commit nella storia.

---

### A5 — .gitignore per Python

Ogni progetto Python genera automaticamente file di bytecode, cache, log e artefatti di build. Questi file non appartengono al repository.

Il file `.gitignore` risolve il problema: elenca pattern di file e directory che Git deve ignorare completamente.

#### Perché Configurarlo Prima del Primo Commit

Regola d'oro: **aggiungi `.gitignore` prima del primo `git add .`**

#### Cosa NON Versionare in un Progetto Python

**Bytecode Python:**
- `__pycache__/` — versioni precompilate generate automaticamente. Si ricreano ad ogni esecuzione.
- I file `*.pyc`, `*.pyo`, `*.pyd` — file compilati per diverse versioni Python.

**Ambienti Virtuali:**
- `.venv/`, `venv/`, `env/` — l'ambiente virtuale. Può pesare centinaia di MB. Si ricrea da `pyproject.toml` in pochi secondi.

**Segreti — CRITICO:**
- `.env` — contiene password, API key, token OAuth. **Mai nel repository.** Una volta committato, il segreto è nella storia Git per sempre, anche se rimosso dopo.
- I file `*.key`, `*.pem` — chiavi crittografiche private.

**File di build:**
- `dist/`, `build/`, `*.egg-info/` — si rigenerano con `python -m build`.

**Cache degli strumenti:**
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` — cache locali.


Il file .gitignore di base:

```gitignore
__pycache__/
*.pyc
.venv/
.env
dist/
build/
```

```bash
git add .gitignore
git commit -m "chore: aggiunge .gitignore"
```


Esempio con single quote nell'output:

```bash
git rm --cached .env
```

Output atteso:
```
rm '.env'
```

Questo rimuove il file dall'indice Git ma non dal filesystem.


#### Il .gitignore Completo per Python

Crea nella radice del repository un file `.gitignore`:

```gitignore
# Python bytecode
__pycache__/
*.py[cod]
*$py.class
*.so
*.pyd

# Virtual environments
.venv/
venv/
env/
ENV/
.uv/
.poetry/

# Distribution e build
dist/
build/
*.egg-info/
*.egg
MANIFEST
wheels/

# Testing
.pytest_cache/
.coverage
.coverage.*
coverage.xml
htmlcov/
.tox/
.nox/

# Type checkers e linter
.mypy_cache/
.pytype/
.ruff_cache/

# Segreti - NON committare mai
.env
.env.*
!.env.example
*.key
*.pem
secrets.yaml
secrets.json

# Database locali
*.db
*.sqlite
*.sqlite3

# Editor
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/

# Documentazione generata
site/
docs/_build/

# Log e file temporanei
*.log
logs/
*.tmp
*.bak
```

Committa il file:

```bash
git add .gitignore
git commit -m "chore: aggiunge .gitignore per progetto Python"
```


#### Verificare che un File Viene Ignorato

```bash
mkdir __pycache__
echo "bytecode" > __pycache__/main.cpython-312.pyc
echo "DB_PASSWORD=supersecreta123" > .env
git status
```

**Output atteso:**

```
On branch main
nothing to commit, working tree clean
```

Git non mostra i file ignorati. Per vederli esplicitamente:

```bash
git status --ignored
```

**Output atteso:**

```
On branch main
nothing to commit, working tree clean

Ignored files:
  (use "git add -f <file>..." to include in what will be committed)
        .env
        __pycache__/
```

#### Trovare Perché un File Viene Ignorato

```bash
git check-ignore -v __pycache__/main.cpython-312.pyc
```

**Output atteso:**

```
.gitignore:2:__pycache__/   __pycache__/main.cpython-312.pyc
```

Leggi: "ignorato dalla regola alla riga 2 del `.gitignore`, il pattern è `__pycache__/`".

#### Il Pattern .env.example

Nel `.gitignore` sono presenti queste righe:

```gitignore
.env
.env.*
!.env.example
```

La `!` è una negazione: ignora tutti i file `.env*`, tranne `.env.example`.
Il file `.env.example` è un template con i **nomi** delle variabili (mai i valori)
da committare nel repository per aiutare i collaboratori.

**`.env.example` — va committato:**
```bash
# Copia questo file in .env e riempi con i valori reali
DATABASE_URL=postgresql://utente:PASSWORD@localhost/nome_db
SECRET_KEY=sostituisci-con-chiave-sicura-minimo-32-caratteri
STRIPE_API_KEY=sk_live_inserisci_la_tua_chiave
DEBUG=false
```

#### Rimuovere File Già Tracciati

Se hai già committato un file da ignorare:

```bash
# Passo 1: aggiungi il pattern
echo ".env" >> .gitignore

# Passo 2: rimuovi dall'indice Git (lascia il file sul disco)
git rm --cached .env

# Passo 3: committa
git add .gitignore
git commit -m "chore: rimuove .env dal tracking"
```

Il flag `--cached` è fondamentale: rimuove dal repository ma non dal filesystem.

#### Generatore Automatico

```bash
# Via curl (Python + VS Code + Windows + macOS)
curl -sL "https://www.toptal.com/developers/gitignore/api/python,vscode,windows,macos" > .gitignore
```

---

> **Checkpoint A5:** Hai un repository con `.gitignore` configurato. Conosci il ciclo modifica-add-commit, sai leggere la storia, confrontare versioni, e ignorare i file non necessari. Nella Parte B approfondiamo come Git funziona internamente e come collaborare con il team.


---

## Parte B: Comprensione Profonda

Nella Parte A hai imparato il ciclo base di Git. Nella Parte B andiamo più in profondità: come Git funziona internamente, come lavorare su più cose in parallelo, come collaborare via GitHub, e come automatizzare i controlli di qualità.

---

### B1 — Come Git Salva i Dati (Internals per Principianti)

La maggior parte dei sistemi di backup pensano ai dati come **modifiche a file nel tempo**: tengono traccia dei diff tra versioni successive.

Git è fondamentalmente diverso: pensa ai dati come a **snapshot completi** del filesystem in ogni momento.

---

#### I Quattro Tipi di Oggetto Git

Git è un database chiave-valore. Ogni oggetto riceve una chiave hash SHA-1 calcolata dal suo contenuto.

**1. Blob — Il contenuto di un file**

Un `blob` contiene solo il contenuto puro di un file, nient'altro.
Due file identici in posizioni diverse condividono lo stesso blob.

```
Blob hash: 7b3c2e1a...
Contenuto: def saluta(nome): return f"Ciao, {nome}!"
```

**2. Tree — Una directory**

Un `tree` elenca i file in una directory, con permessi e hash dei blob:

```
Tree hash: 9f4d8a2c...
100644 blob 7b3c2e1a  saluta.py
100644 blob a2b4c6d8  README.md
040000 tree e5f7a9b1  tests/
```

**3. Commit — Lo snapshot con metadati**

Un `commit` punta al tree radice + commit padre + autore + messaggio:

```
Commit hash: 4f2a1b3c...
tree    9f4d8a2c...
parent  f8c3a21b...
author  Mario Rossi <mario@example.com> 1752583800 +0200

feat: aggiunge funzione saluta
```

**4. Tag annotato — Un puntatore permanente**

Un tag annotato punta a un commit e include metadati aggiuntivi.
A differenza di un branch, un tag non si sposta mai.

---

#### Ispezionare gli Oggetti

```bash
# Tipo di un oggetto
git cat-file -t HEAD
```

**Output:** `commit`

```bash
# Contenuto del commit corrente
git cat-file -p HEAD
```

**Output atteso:**
```
tree 9f4d8a2c1e3b5f7a9d2c4e6f8a0b2d4f6a8c0e2
parent f8c3a21b4d6e8f0a2b4c6d8e0f2a4c6e8f0a2b4
author Mario Rossi <mario.rossi@example.com> 1752583800 +0200
committer Mario Rossi <mario.rossi@example.com> 1752583800 +0200

feat: aggiunge funzione congeda
```

```bash
# Contenuto del tree radice
git cat-file -p HEAD^{tree}
```

**Output atteso:**
```
100644 blob a2b4c6d8...  README.md
100644 blob 7b3c2e1a...  saluta.py
```

---

#### Perché Questa Conoscenza È Utile

1. **Non hai paura di perdere dati:** Git non cancella oggetti a meno che non lo chiedi. Dopo `git reset --hard`, i dati esistono ancora nel database e si possono recuperare con `git reflog`.

2. **Capisci i messaggi di errore:** Quando Git dice "detached HEAD", significa che HEAD punta a un hash direttamente invece di puntare a un branch. Non è un errore grave.

3. **Capisci il costo delle operazioni:** Un branch è solo un file da 41 byte. Creare cento branch ha lo stesso costo di creare uno.

---

#### I Refs — I Segnalibri della Storia

I **ref** sono alias leggibili per gli hash SHA-1:

```
.git/HEAD              → ref: refs/heads/main
.git/refs/heads/main   → 2c9e4b7a1d3f... (hash dell'ultimo commit)
.git/refs/tags/v1.0.0  → 4f2a1b3c... (hash del tag)
```

Quando fai un commit, Git aggiorna il file del branch corrente con il nuovo hash. Questo è tutto ciò che succede.

---

### B2 — Branch: Lavorare in Parallelo

Un branch in Git è un **puntatore leggero** a un commit. Creare un branch significa creare un file di 41 byte. Questo è radicalmente diverso da sistemi più vecchi dove un branch copiava l'intera directory.

---

#### Creare e Visualizzare Branch

```bash
# Elenco branch (asterisco = branch corrente)
git branch
```

**Output:**
```
* main
```

```bash
# Crea e vai al nuovo branch
git switch -c feature/traduzione
```

**Output:**
```
Switched to a new branch 'feature/traduzione'
```

```bash
# Alternativa (vecchio stile, ancora funzionante)
git checkout -b feature/traduzione
```

```bash
# Verifica su quale branch sei
git branch
```

**Output:**
```
* feature/traduzione
  main
```

---

#### Lavorare sul Branch

Ora lavori isolato senza toccare main. Aggiungi del codice, poi:

```bash
git add saluta.py
git commit -m "feat(traduzione): aggiunge saluto multilingua"
```

**Output:**
```
[feature/traduzione 7a4b3c2] feat(traduzione): aggiunge saluto multilingua
 1 file changed, 18 insertions(+)
```

---

#### Visualizzare la Storia con i Branch

```bash
git log --oneline --graph --all
```

**Output:**
```
* 7a4b3c2 (HEAD -> feature/traduzione) feat(traduzione): aggiunge saluto multilingua
* 2c9e4b7 (main) feat: aggiunge funzione congeda
* f8c3a21 docs: aggiunge README con esempio d'uso
* 4f2a1b3 feat: aggiunge funzione saluta con type hints
```

Il branch `main` è rimasto indietro. Il branch `feature/traduzione` ha un commit in più.

---

#### Tornare al Branch main

```bash
git switch main
```

Quando cambi branch, Git aggiorna fisicamente i file sul disco. Se apri `saluta.py`, la funzione `saluta_in_lingua` non c'è più — è nel branch `feature/traduzione`, non in `main`.

Questo sorprende sempre i principianti la prima volta!

---

#### Naming Convention per i Branch

| Tipo | Prefisso | Esempio |
|------|----------|---------|
| Nuova funzionalità | `feature/` | `feature/login-oauth2` |
| Bug fix | `fix/` | `fix/validazione-email` |
| Hotfix urgente | `hotfix/` | `hotfix/sql-injection` |
| Refactoring | `refactor/` | `refactor/modello-utente` |
| Documentazione | `docs/` | `docs/guida-installazione` |

Regole: solo minuscole, no spazi (usa `-`), nomi descrittivi.

---

#### Il Feature Branch Workflow

Il pattern standard per lavorare professionalmente:

1. `main` è sempre stabile e rilasciabile — mai commit diretti
2. Ogni funzionalità vive su un branch separato
3. Si merge su main solo quando il lavoro è pronto e testato

```bash
# Ciclo completo
git switch main
git pull                          # aggiorna prima di iniziare
git switch -c feature/nome
# ... lavora ...
git add .
git commit -m "feat: ..."
git switch main
git merge feature/nome
git branch -d feature/nome        # elimina il branch (è mergiato)
```


---

### B3 — Merge e Conflitti

Dopo aver sviluppato su un branch separato, è il momento di unirlo con il branch principale. Questo processo si chiama **merge**.

---

#### Fast-Forward Merge — Il Caso Semplice

Se `main` non ha avuto nuovi commit mentre lavoravi sul branch feature, Git può eseguire un **fast-forward merge**: sposta semplicemente il puntatore `main` in avanti, senza creare un merge commit.

```
PRIMA:  main → A → B → C
                         \
        feature:          D → E

DOPO fast-forward: main → A → B → C → D → E
```

```bash
git switch main
git merge feature/traduzione
```

**Output atteso (fast-forward):**
```
Updating 2c9e4b7..7a4b3c2
Fast-forward
 saluta.py | 18 ++++++++++++++++++
 1 file changed, 18 insertions(+)
```

---

#### 3-Way Merge — Branch Divergenti

Se sia `main` che il branch feature hanno avuto commit, Git crea un **merge commit** con due genitori.

```
PRIMA:  main   → A → B → C → F
        feature         → D → E

DOPO 3-way: main → A → B → C → F → M (merge commit)
                                 D → E ─┘
```

**Output atteso (3-way merge):**
```
Merge made by the 'ort' strategy.
 saluta.py | 8 ++++++++
 1 file changed, 8 insertions(+)
```

```bash
git log --oneline --graph
```

**Output atteso:**
```
*   8b3c4d5 (HEAD -> main) Merge branch 'feature/login'
|\
| * 6a2b1c0 (feature/login) feat: aggiunge validazione login
* | 5d4e3f2 fix: corregge messaggio di errore
|/
* 2c9e4b7 feat: aggiunge funzione congeda
```

---

#### Conflitti — Quando Git Chiede Aiuto

Un **conflitto** avviene quando due branch hanno modificato le **stesse righe dello stesso file**. Git non può scegliere — ti chiede di decidere.

**Il file in conflitto appare così:**

```python
<<<<<<< HEAD
def saluta(nome: str, punteggiatura: str = "!") -> str:
    """Restituisce un saluto personalizzato."""
    return f"Ciao, {nome}{punteggiatura}"
=======
def saluta(nome: str, formale: bool = False) -> str:
    """Restituisce un saluto formale o informale."""
    if formale:
        return f"Buongiorno, {nome}."
    return f"Ciao, {nome}!"
>>>>>>> feature/saluto-v2
```

**I marker del conflitto:**
- `<<<<<<< HEAD` — inizio della versione del branch corrente
- `=======` — il separatore
- `>>>>>>> feature/saluto-v2` — fine della versione che stai mergiando

---

#### Come Risolvere il Conflitto

Hai tre opzioni:

**A) Tenere la versione di HEAD (main):** elimina tutto dal `=======` in giù fino a `>>>>>>>`, e rimuovi la riga `<<<<<<< HEAD`.

**B) Tenere la versione del branch:** elimina tutto da `<<<<<<< HEAD` fino a `=======`, e rimuovi la riga `>>>>>>> feature/saluto-v2`.

**C) Combinare entrambe (la più comune nella pratica):**

```python
def saluta(
    nome: str,
    punteggiatura: str = "!",
    formale: bool = False,
) -> str:
    """Restituisce un saluto, formale o informale."""
    if formale:
        return f"Buongiorno, {nome}."
    return f"Ciao, {nome}{punteggiatura}"
```

Dopo aver risolto il conflitto (eliminando tutti i marker):

```bash
git add saluta.py
git status  # verifica che non ci siano altri conflitti
git commit  # completa il merge (Git suggerisce un messaggio)
```

**Per abortire il merge:**

```bash
git merge --abort
```

---

#### VS Code per i Conflitti

VS Code rileva automaticamente i marker di conflitto e mostra pulsanti:
- "Accept Current Change" — versione HEAD
- "Accept Incoming Change" — versione del branch
- "Accept Both Changes" — tutte e due (concatenate)
- "Compare Changes" — diff a tre pannelli

Questo è molto più comodo che modificare il file manualmente.

---

### B4 — GitHub: Il Repository Remoto

Fino ad ora abbiamo lavorato solo in locale. GitHub permette di fare backup remoto, collaborare con altri, e condividere il codice.

---

#### Creare un Repository su GitHub

1. Vai su `github.com` e accedi
2. Clicca `+` → "New repository"
3. Compila:
   - **Repository name:** il nome del tuo progetto
   - **Visibility:** Public o Private
   - **IMPORTANTE:** NON spuntare "Add README", "Add .gitignore", "Choose license" — li abbiamo già localmente
4. Clicca "Create repository"

GitHub mostra le istruzioni per collegare il tuo repository locale.

---

#### Collegare il Repository Locale

```bash
# Aggiungi GitHub come repository remoto
git remote add origin https://github.com/TUO_USERNAME/primo-progetto-git.git

# Verifica la configurazione
git remote -v
```

**Output atteso:**
```
origin  https://github.com/TUO_USERNAME/primo-progetto-git.git (fetch)
origin  https://github.com/TUO_USERNAME/primo-progetto-git.git (push)
```

`origin` è il nome convenzionale per il remote principale — puoi usarne un altro ma `origin` è lo standard universale.

---

#### git push — Caricare su GitHub

```bash
git push -u origin main
```

Il flag `-u` (o `--set-upstream`) imposta il tracking: da ora puoi usare solo `git push` senza specificare `origin main`.

**Output atteso:**
```
Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Compressing objects: 100% (9/9), done.
Writing objects: 100% (12/12), 1.24 KiB | 1.24 MiB/s, done.
Total 12 (delta 2), reused 0 (delta 0), pack-reused 0
To https://github.com/TUO_USERNAME/primo-progetto-git.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

Vai su GitHub e ricarica la pagina — vedrai il tuo codice!

---

#### git pull — Scaricare da GitHub

```bash
git pull          # scarica e integra le modifiche remote
```

**Scenario tipico:** il tuo collega ha pushato nuove modifiche. Tu fai `git pull` e ottieni le sue modifiche nel repository locale.

---

#### git fetch — Scaricare Senza Integrare

```bash
git fetch origin                        # scarica le info remote
git log HEAD..origin/main --oneline     # vedi i nuovi commit
git merge origin/main                   # integra quando sei pronto
```

`git fetch` è più cauto di `git pull`: scarica le informazioni ma non le applica automaticamente.

---

#### Configurare SSH per GitHub

SSH è più comodo di HTTPS per l'uso quotidiano: non devi mai inserire username e password.

```bash
# Genera la coppia di chiavi SSH (Ed25519 è lo standard moderno)
ssh-keygen -t ed25519 -C "tua.email@example.com"
# Premi Invio per il percorso predefinito
# Inserisci una passphrase sicura (opzionale ma raccomandato)

# Copia la chiave pubblica (Windows Git Bash)
clip < ~/.ssh/id_ed25519.pub

# Aggiungi su GitHub: Settings > SSH keys > New SSH key
# Incolla la chiave pubblica

# Verifica la connessione
ssh -T git@github.com
```

**Output atteso da ssh -T:**
```
Hi TUO_USERNAME! You've successfully authenticated,
but GitHub does not provide shell access.
```

```bash
# Cambia il remote da HTTPS a SSH
git remote set-url origin git@github.com:TUO_USERNAME/primo-progetto-git.git
```


---

### B5 — Pull Request: Il Flusso di Collaborazione

Una **Pull Request** (PR) è una proposta formale di integrare le modifiche di un branch nel branch principale. Su GitHub è anche lo spazio per la code review.

---

#### Perché Aprire una Pull Request

- GitHub mostra automaticamente il diff delle modifiche
- Si possono commentare righe specifiche del codice
- I controlli CI/CD vengono eseguiti automaticamente
- C'è un log storico delle decisioni prese
- Per i team, la PR è obbligatoria: nessuno dovrebbe pushare direttamente su `main`

---

#### Il Flusso Completo

```bash
# 1. Crea il branch e lavora
git switch -c feature/nuova-funzionalita
# ... lavora ...
git commit -m "feat: aggiunge nuova funzionalita"

# 2. Pusha il branch su GitHub
git push -u origin feature/nuova-funzionalita
```

Su GitHub: il banner "Compare & pull request" appare automaticamente.
Clicca su di esso, scrivi il titolo e la descrizione, clicca "Create pull request".

---

#### GitHub CLI — Aprire una PR dal Terminale

```bash
# Installa GitHub CLI (se non lo hai)
# Windows:
winget install --id GitHub.cli

# Autenticati
gh auth login

# Apri una PR interattiva
gh pr create

# Oppure con parametri
gh pr create --title "feat: nuova funzionalita" \
             --body "Aggiunge X che fa Y. Closes #42."
```

---

#### Code Review

Quando la PR è aperta, i revisori possono:
- Commentare righe specifiche del codice
- Approvare con "Approve"
- Richiedere modifiche con "Request changes"
- Fare merge dopo l'approvazione

**Strategie di merge su GitHub:**
1. **Create a merge commit** — crea un merge commit con due genitori
2. **Squash and merge** — combina tutti i commit in uno solo pulito
3. **Rebase and merge** — storia lineare senza merge commit

Per i principianti, "Squash and merge" è spesso la scelta migliore: produce una storia pulita e leggibile.

---

### B6 — Git Stash: Metti da Parte il Lavoro

Hai un lavoro a metà su un branch e devi cambiare branch urgentemente, ma non vuoi committare perché il lavoro non è pronto. `git stash` salva temporaneamente le modifiche non committate.

**Analogia:** Stai cucinando, arriva una telefonata urgente. Metti i piatti nel frigorifero (stash), esci a gestire l'emergenza, poi torni e riprendi la cottura (pop).

---

#### Operazioni Base

```bash
# Salva le modifiche correnti
git stash
```

**Output:**
```
Saved working directory and index state WIP on feature/xyz: 2c9e4b7 feat: ...
```

```bash
# Salva con un messaggio descrittivo
git stash push -m "WIP: aggiunta funzione conta_parole"

# Vedi gli stash salvati
git stash list
```

**Output:**
```
stash@{0}: On feature/xyz: WIP: aggiunta funzione conta_parole
stash@{1}: WIP on main: 4f2a1b3 feat: aggiunge saluta
```

```bash
# Recupera l'ultimo stash e rimuovilo dalla lista
git stash pop

# Applica uno stash specifico senza rimuoverlo
git stash apply stash@{1}

# Vedi il contenuto di uno stash
git stash show -p stash@{0}

# Elimina uno stash
git stash drop stash@{0}
```

---

#### Scenario Tipico

```bash
# Stai lavorando su una feature, arriva un hotfix urgente
git stash push -m "WIP: logica calcolo sconto"

# Risolvi il problema urgente
git switch main
git switch -c hotfix/errore-fatturazione
git add .
git commit -m "fix: corregge calcolo IVA"
git switch main
git merge hotfix/errore-fatturazione
git branch -d hotfix/errore-fatturazione

# Torna al lavoro precedente
git switch feature/calcola-sconto
git stash pop
# Le modifiche sono tornate come le avevi lasciate
```

---

### B7 — Tag: Marcare le Versioni

I tag sono puntatori permanenti a commit specifici, usati principalmente per marcare le release.

---

#### Tag Leggeri vs Tag Annotati

| Caratteristica | Tag Leggero | Tag Annotato |
|----------------|-------------|--------------|
| Comando | `git tag v1.0.0` | `git tag -a v1.0.0 -m "..."` |
| Metadati (autore, data) | No | Si |
| Firmabile GPG | No | Si |
| Uso consigliato | Test locali | **Release ufficiali** |

Per le release, usa sempre i tag annotati.

---

#### Creare e Gestire Tag

```bash
# Tag annotato (per le release)
git tag -a v1.0.0 -m "Prima release stabile"

# Elenco tag
git tag
# v1.0.0

# Dettagli del tag
git show v1.0.0

# Push del tag su GitHub (i tag non si pushano automaticamente)
git push origin v1.0.0

# Push di tutti i tag
git push origin --tags

# Eliminare un tag
git tag -d v1.0.0-beta
```

---

#### Semantic Versioning (SemVer)

Il formato standard per i numeri di versione: `MAJOR.MINOR.PATCH`

| Componente | Quando incrementa | Esempio |
|------------|------------------|---------|
| MAJOR | Breaking change | `1.x.x → 2.0.0` |
| MINOR | Nuova funzionalità backward-compatible | `1.2.x → 1.3.0` |
| PATCH | Bug fix backward-compatible | `1.2.3 → 1.2.4` |

**Esempi pratici:**

```
1.0.0     — Prima release stabile
1.1.0     — Aggiunge la funzione saluta_in_lingua
1.1.1     — Fix: corregge traduzione in tedesco
2.0.0     — Rimuove API vecchia (breaking change)
1.0.0-beta.1  — Beta release
1.0.0-rc.1    — Release candidate
```

---

> **Checkpoint B7:** Ora conosci branch, merge, conflitti, GitHub, Pull Request, stash e tag. Nella prossima sezione vediamo come automatizzare i controlli di qualità con pre-commit hooks.


---

### B8 — pre-commit Hooks con Python

Git hooks sono script eseguiti automaticamente in corrispondenza di eventi del lifecycle Git. Il framework `pre-commit` permette di condividere questi hook con il team tramite un file YAML nel repository.

---

#### Cosa Sono i Git Hooks

I hook risiedono in `.git/hooks/`. Il problema: `.git/` non è versionato, quindi i hook non vengono condivisi automaticamente con il team. `pre-commit` risolve questo problema.

| Hook | Quando scatta | Uso tipico |
|------|--------------|-----------|
| `pre-commit` | Prima di creare il commit | Lint, format, typecheck |
| `commit-msg` | Dopo il messaggio di commit | Validare il formato |
| `pre-push` | Prima del push | Test, security scan |
| `post-merge` | Dopo un merge | Reinstallare dipendenze |

---

#### Installare pre-commit

```bash
# Con uv (raccomandato)
uv add --dev pre-commit

# Con pip
pip install pre-commit

# Installare gli hook nel repository locale
pre-commit install

# Per validare anche i messaggi di commit
pre-commit install --hook-type commit-msg
```

**Output di pre-commit install:**
```
pre-commit installed at .git/hooks/pre-commit
```

---

#### Configurazione .pre-commit-config.yaml

Crea nella radice del repository il file `.pre-commit-config.yaml`:

```yaml
# .pre-commit-config.yaml
default_language_version:
  python: python3.12

repos:
  # Hook generici per la qualita dei file
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace        # rimuove spazi finali
      - id: end-of-file-fixer          # aggiunge newline finale
      - id: check-yaml                 # valida YAML
      - id: check-toml                 # valida TOML
      - id: check-merge-conflict       # blocca se ci sono marker di merge
      - id: check-added-large-files    # blocca file oltre 500KB
        args: ["--maxkb=500"]
      - id: no-commit-to-branch        # blocca commit diretti su main
        args: ["--branch", "main"]
      - id: detect-private-key         # cerca chiavi private nel codice
      - id: debug-statements           # cerca pdb, breakpoint() nel codice

  # Ruff — linting e formatting Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.7
    hooks:
      - id: ruff                       # linting
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format                # formatting

  # mypy — type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
        args: [--strict, --ignore-missing-imports]

  # Conventional Commits — validazione messaggio
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, test, chore, ci, build]
```

---

#### Cosa Succede al Prossimo Commit

```bash
# Aggiungi e committa
git add .
git commit -m "aggiunge funzione senza type hints"
```

**Se ruff trova un problema, il commit viene bloccato:**
```
ruff.....................................................................Failed
- hook id: ruff
- exit code: 1

src/saluta.py:5:1: ANN201 Missing return type annotation for public function
```

Devi correggere il problema, poi fare di nuovo `git add` e `git commit`.

---

#### Eseguire i Hook Manualmente

```bash
# Esegui su tutti i file (utile la prima volta)
pre-commit run --all-files

# Esegui su un hook specifico
pre-commit run ruff --all-files

# Aggiorna tutti gli hook alle versioni più recenti
pre-commit autoupdate
```

---

#### Saltare un Hook in Emergenza

```bash
# ATTENZIONE: usare solo in casi eccezionali
git commit --no-verify -m "WIP: commit urgente senza hook"
```

Usare `--no-verify` saltuariamente è accettabile in casi di emergenza. Usarlo regolarmente annulla il valore degli hook — equivale a disinstallare la sicurezza.

---

#### Hook Personalizzato per pytest

Puoi aggiungere hook locali che eseguono i tuoi test:

```yaml
# Aggiungi a .pre-commit-config.yaml
  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (test veloci, senza integrazioni)
        entry: uv run pytest tests/unit/ -x -q --no-header
        language: system
        pass_filenames: false
        stages: [pre-commit]
```

---

> **Vantaggio:** Con pre-commit configurato, ogni commit passa automaticamente attraverso lint, format check, type check e test veloci. I problemi vengono trovati immediatamente, non in un momento di code review ore dopo.


---

### B9 — Conventional Commits

**Conventional Commits** è una specifica per i messaggi di commit che abilita la generazione automatica del changelog e il versioning semantico.

---

#### Il Formato

```
<tipo>[scope opzionale]: <descrizione breve>

[corpo opzionale: spiegazione più lunga]

[footer opzionale: riferimenti a issue, breaking changes]
```

---

#### I Tipi Standard

| Tipo | Descrizione | Impatto SemVer |
|------|-------------|---------------|
| `feat` | Nuova funzionalità | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Solo documentazione | — |
| `style` | Formattazione, no logica | — |
| `refactor` | Refactoring, no feature, no fix | — |
| `perf` | Miglioramento performance | PATCH |
| `test` | Aggiunta o modifica test | — |
| `chore` | Build, CI, dipendenze | — |
| `ci` | Modifiche CI/CD | — |
| `revert` | Revert di un commit | — |

---

#### Esempi di Commit Corretti

```bash
# Feature con scope
git commit -m "feat(auth): aggiunge login con Google OAuth2"

# Bug fix con riferimento a issue
git commit -m "fix(models): corregge validazione email con caratteri speciali

Closes #42. La regex precedente non gestiva user+tag@sub.domain.com."

# Chore senza scope
git commit -m "chore: aggiorna dipendenze a luglio 2026"

# Breaking change (incrementa MAJOR)
git commit -m "feat(api)!: rinomina endpoint /user a /users

BREAKING CHANGE: tutti i client devono aggiornare il path
da /user/{id} a /users/{id}."

# Documentazione
git commit -m "docs: aggiunge sezione configurazione SSH al README"

# Test
git commit -m "test(auth): aggiunge test per scadenza del token JWT"
```

---

#### Perché Seguire la Convenzione

1. **Changelog automatico:** strumenti come `git-cliff` leggono la storia dei commit e generano `CHANGELOG.md` automaticamente.

2. **Versioning automatico:** `commitizen`, `python-semantic-release` e altri tool incrementano automaticamente il numero di versione basandosi sui tipi di commit.

3. **Storia leggibile:** una storia di commit convenzionale è immediatamente comprensibile a qualsiasi sviluppatore.

---

#### git-cliff — Changelog Automatico

```bash
# Installa git-cliff
uv tool install git-cliff

# Genera il changelog completo
git-cliff --output CHANGELOG.md

# Solo le modifiche non ancora nel changelog
git-cliff --unreleased

# Per una release specifica
git-cliff --tag v1.3.0
```

---

### B10 — GitHub Actions: CI/CD di Base

**CI/CD** sta per Continuous Integration / Continuous Delivery. La CI esegue automaticamente i test ad ogni push, assicurandosi che il codice sia sempre funzionante.

**Analogia:** Una catena di montaggio che controlla automaticamente ogni pezzo prima che arrivi al cliente.

---

#### La Struttura di un Workflow GitHub Actions

I workflow risiedono in `.github/workflows/*.yml`. Sono file YAML che descrivono:
- **Quando** eseguire il workflow (`on: push, pull_request`)
- **Dove** eseguirlo (`runs-on: ubuntu-latest`)
- **Cosa** fare (una serie di `steps`)

---

#### La Pipeline CI di Base per Python

Crea il file `.github/workflows/ci.yml`:

```yaml
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
    name: Qualita del codice
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - name: Checkout del codice
        uses: actions/checkout@v4

      - name: Installa uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
          enable-cache: true

      - name: Configura Python
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
            -v

      - name: Audit sicurezza
        run: uv run pip-audit
```

---

#### Cosa Succede ad Ogni Push

1. GitHub rileva il push su `main` (o la PR verso `main`)
2. Avvia automaticamente il workflow
3. Esegue i passi in ordine: checkout → installa uv → installa dipendenze → lint → typecheck → test → audit
4. Se un passo fallisce, l'intero job fallisce e ricevi una notifica email
5. Sulla PR, viene mostrato lo stato (verde = passa, rosso = fallisce)

---

#### Il Badge di Stato nel README

Aggiungi un badge nel `README.md` per mostrare lo stato della CI:

```markdown
[![CI](https://github.com/TUO_USERNAME/primo-progetto-git/actions/workflows/ci.yml/badge.svg)](https://github.com/TUO_USERNAME/primo-progetto-git/actions/workflows/ci.yml)
```

Questo mostra `passing` (verde) o `failing` (rosso) nella pagina del repository.

---

> **Checkpoint B10:** Ora hai tutti gli strumenti per usare Git in modo professionale: branch, merge, GitHub, PR, pre-commit hooks, Conventional Commits e CI/CD. Nella Parte C mettiamo in pratica tutto con dieci esercizi guidati.


---

## Parte C: Esercizi Pratici Guidati

Questa parte contiene dieci esercizi pratici in ordine crescente di difficoltà. Gli esercizi C1-C4 sono completamente guidati: ogni passo ha il comando esatto e l'output atteso. Gli esercizi C5-C7 sono semi-autonomi: hai le istruzioni generali ma devi trovare i comandi esatti da solo. Gli esercizi C8-C10 sono autonomi: hai solo l'obiettivo.

**Come usare questa parte:**
- Fai gli esercizi in ordine — ognuno si basa sui precedenti
- Ogni esercizio crea una nuova directory di progetto
- Verifica ogni passo prima di andare avanti
- Se resti bloccato su C1-C4, rileggi la sezione teorica corrispondente
- Per C5-C10, prova prima da solo, poi consulta la soluzione suggerita

---

### C1 — Primo Repository da Zero (Guidato)

**Obiettivo:** Creare un repository Git con tre commit, imparare il ciclo base.

**Durata stimata:** 20 minuti

---

#### Passo 1 — Creare la Directory

```bash
# Su Windows PowerShell
mkdir esercizio-c1
cd esercizio-c1

# Verifica che sei nella directory giusta
pwd
```

**Output atteso (esempio):**
```
C:\Users\Mario\esercizio-c1
```

---

#### Passo 2 — Inizializzare il Repository

```bash
git init
```

**Output atteso:**
```
Initialized empty Git repository in C:/Users/Mario/esercizio-c1/.git/
```

```bash
git status
```

**Output atteso:**
```
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
```

---

#### Passo 3 — Il Primo File e il Primo Commit

Crea il file `calcolatrice.py` con questo contenuto:

```python
# calcolatrice.py — una semplice calcolatrice Python


def somma(a: float, b: float) -> float:
    """Restituisce la somma di due numeri."""
    return a + b


if __name__ == "__main__":
    print(somma(3, 4))  # 7.0
```

```bash
git add calcolatrice.py
git status
```

**Output atteso:**
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   calcolatrice.py
```

```bash
git commit -m "feat: aggiunge funzione somma"
```

**Output atteso:**
```
[main (root-commit) a1b2c3d] feat: aggiunge funzione somma
 1 file changed, 9 insertions(+)
 create mode 100644 calcolatrice.py
```

---

#### Passo 4 — Il Secondo Commit

Aggiungi la funzione sottrazione a `calcolatrice.py`:

```python
def sottrazione(a: float, b: float) -> float:
    """Restituisce la differenza di due numeri."""
    return a - b
```

```bash
git add calcolatrice.py
git commit -m "feat: aggiunge funzione sottrazione"
```

---

#### Passo 5 — Il Terzo Commit (un nuovo file)

Crea `README.md`:

```markdown
# Calcolatrice Python

Una semplice calcolatrice in Python.

## Funzioni disponibili
- `somma(a, b)` — somma due numeri
- `sottrazione(a, b)` — sottrae due numeri
```

```bash
git add README.md
git commit -m "docs: aggiunge README con descrizione funzioni"
```

---

#### Passo 6 — Verificare la Storia

```bash
git log --oneline
```

**Output atteso:**
```
c3d4e5f (HEAD -> main) docs: aggiunge README con descrizione funzioni
b2c3d4e feat: aggiunge funzione sottrazione
a1b2c3d feat: aggiunge funzione somma
```

```bash
git log --oneline --graph
```

**Output atteso:**
```
* c3d4e5f (HEAD -> main) docs: aggiunge README con descrizione funzioni
* b2c3d4e feat: aggiunge funzione sottrazione
* a1b2c3d feat: aggiunge funzione somma
```

---

#### Verifica Finale

- [ ] Il repository ha esattamente 3 commit
- [ ] Il messaggio del primo commit è "feat: aggiunge funzione somma"
- [ ] Il terzo commit tocca solo `README.md`
- [ ] `git status` mostra "nothing to commit, working tree clean"

**Comando di verifica:**
```bash
git log --oneline | wc -l
```

**Output atteso:** `3`


---

### C2 — Push su GitHub (Guidato)

**Obiettivo:** Connettere il repository locale dell'esercizio C1 a GitHub e pushare il codice.

**Prerequisiti:** Esercizio C1 completato, account GitHub, GitHub CLI installato (`winget install --id GitHub.cli`)

**Durata stimata:** 20 minuti

---

#### Passo 1 — Autenticarsi con GitHub CLI

```bash
gh auth login
```

Segui il wizard interattivo:
- "What account do you want to log into?" → GitHub.com
- "What is your preferred protocol?" → HTTPS (o SSH se hai già una chiave)
- "Authenticate GitHub CLI" → Login with a web browser
- Premi Invio, si aprirà il browser, accedi con il tuo account GitHub

---

#### Passo 2 — Creare il Repository su GitHub

```bash
# Crea il repository su GitHub direttamente da CLI
gh repo create esercizio-c1 --public --description "Calcolatrice Python - esercizio Git"
```

**Output atteso:**
```
Created repository TUO_USERNAME/esercizio-c1 on GitHub
  https://github.com/TUO_USERNAME/esercizio-c1
```

---

#### Passo 3 — Aggiungere il Remote

```bash
# Aggiungi GitHub come remote (sostituisci TUO_USERNAME)
git remote add origin https://github.com/TUO_USERNAME/esercizio-c1.git

# Verifica
git remote -v
```

**Output atteso:**
```
origin  https://github.com/TUO_USERNAME/esercizio-c1.git (fetch)
origin  https://github.com/TUO_USERNAME/esercizio-c1.git (push)
```

---

#### Passo 4 — Push su GitHub

```bash
git push -u origin main
```

**Output atteso:**
```
Enumerating objects: 8, done.
Counting objects: 100% (8/8), done.
Writing objects: 100% (8/8), 812 bytes | 812.00 KiB/s, done.
To https://github.com/TUO_USERNAME/esercizio-c1.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

#### Passo 5 — Verificare su GitHub

```bash
# Apri il repository nel browser
gh repo view --web
```

Dovresti vedere:
- Il file `calcolatrice.py` con il codice
- Il `README.md` visualizzato automaticamente sotto i file
- I 3 commit nella sezione "commits"

---

#### Passo 6 — Fare un Commit e Pusharlo

Aggiungi la funzione moltiplicazione:

```python
def moltiplicazione(a: float, b: float) -> float:
    """Restituisce il prodotto di due numeri."""
    return a * b
```

```bash
git add calcolatrice.py
git commit -m "feat: aggiunge funzione moltiplicazione"
git push
```

Ora il repository remoto ha 4 commit, sincronizzato con il locale.

---

#### Verifica Finale

- [ ] Il repository è visibile su GitHub
- [ ] Tutti i file sono presenti
- [ ] `git log --oneline` locale corrisponde ai commit su GitHub
- [ ] `git push` senza parametri funziona (tracking configurato)

---

### C3 — Feature Branch e Merge (Guidato)

**Obiettivo:** Creare un branch, lavorarci, e fare il merge su main.

**Prerequisiti:** Esercizio C2 completato

**Durata stimata:** 25 minuti

---

#### Passo 1 — Creare il Branch

Stai lavorando sulla calcolatrice e vuoi aggiungere la divisione, ma è una funzionalità non banale (bisogna gestire la divisione per zero). Usi un branch separato.

```bash
git switch -c feature/divisione
```

**Output atteso:**
```
Switched to a new branch 'feature/divisione'
```

```bash
# Verifica su quale branch sei
git branch
```

**Output atteso:**
```
* feature/divisione
  main
```

---

#### Passo 2 — Prima Modifica sul Branch

Aggiungi la funzione divisione:

```python
def divisione(a: float, b: float) -> float:
    """Restituisce il quoziente di due numeri.

    Raises:
        ValueError: Se b e' zero (divisione per zero non definita).
    """
    if b == 0:
        raise ValueError("Impossibile dividere per zero")
    return a / b
```

```bash
git add calcolatrice.py
git commit -m "feat(divisione): aggiunge funzione con gestione errore"
```

---

#### Passo 3 — Seconda Modifica sul Branch

Aggiungi anche i test per la divisione. Crea il file `test_calcolatrice.py`:

```python
# test_calcolatrice.py
import pytest
from calcolatrice import divisione


def test_divisione_normale():
    assert divisione(10, 2) == 5.0


def test_divisione_per_zero():
    with pytest.raises(ValueError, match="Impossibile dividere per zero"):
        divisione(5, 0)
```

```bash
git add test_calcolatrice.py
git commit -m "test(divisione): aggiunge test per divisione e divisione per zero"
```

---

#### Passo 4 — Visualizzare la Storia

```bash
git log --oneline --graph --all
```

**Output atteso:**
```
* 7f8g9h0 (HEAD -> feature/divisione) test(divisione): aggiunge test
* 6e7f8g9 feat(divisione): aggiunge funzione con gestione errore
* c3d4e5f (main) docs: aggiunge README con descrizione funzioni
* b2c3d4e feat: aggiunge funzione sottrazione
* a1b2c3d feat: aggiunge funzione somma
```

`main` è rimasto al terzo commit, mentre `feature/divisione` è due commit avanti.

---

#### Passo 5 — Tornare a main e Fare il Merge

```bash
git switch main
git merge feature/divisione
```

**Output atteso (fast-forward, perché main non ha avuto nuovi commit):**
```
Updating c3d4e5f..7f8g9h0
Fast-forward
 calcolatrice.py        | 11 +++++++++++
 test_calcolatrice.py   | 14 ++++++++++++++
 2 files changed, 25 insertions(+)
 create mode 100644 test_calcolatrice.py
```

---

#### Passo 6 — Pulizia e Push

```bash
# Elimina il branch locale (è stato mergiato)
git branch -d feature/divisione

# Push del merge su GitHub
git push
```

---

#### Verifica Finale

```bash
git log --oneline
```

**Output atteso:**
```
7f8g9h0 (HEAD -> main, origin/main) test(divisione): aggiunge test
6e7f8g9 feat(divisione): aggiunge funzione con gestione errore
c3d4e5f docs: aggiunge README con descrizione funzioni
b2c3d4e feat: aggiunge funzione sottrazione
a1b2c3d feat: aggiunge funzione somma
```

- [ ] Il branch `feature/divisione` è stato eliminato
- [ ] Il merge è stato pushato su GitHub
- [ ] `calcolatrice.py` contiene le funzioni somma, sottrazione, moltiplicazione, divisione


---

### C4 — Simulare e Risolvere un Conflitto (Guidato)

**Obiettivo:** Creare deliberatamente un conflitto e risolverlo.

**Prerequisiti:** Esercizio C3 completato

**Durata stimata:** 30 minuti

---

#### Passo 1 — Preparare lo Scenario

Sei su `main`. Crea un branch dove modificherai la funzione `somma`:

```bash
git switch -c feature/somma-con-tipo
```

Modifica la funzione `somma` in `calcolatrice.py`:

```python
def somma(a: float, b: float, tipo: str = "float") -> float | int:
    """Restituisce la somma, opzionalmente come intero."""
    risultato = a + b
    return int(risultato) if tipo == "int" else risultato
```

```bash
git add calcolatrice.py
git commit -m "feat(somma): aggiunge parametro tipo per conversione"
```

---

#### Passo 2 — Modificare main Nello Stesso Punto

Torna a main e modifica **la stessa funzione** in modo diverso:

```bash
git switch main
```

Modifica la funzione `somma` in `calcolatrice.py`:

```python
def somma(a: float, b: float, *, arrotonda: int = -1) -> float:
    """Restituisce la somma, opzionalmente arrotondata."""
    risultato = a + b
    if arrotonda >= 0:
        return round(risultato, arrotonda)
    return risultato
```

```bash
git add calcolatrice.py
git commit -m "feat(somma): aggiunge parametro arrotonda"
```

---

#### Passo 3 — Tentare il Merge (Causerà Conflitto)

```bash
git merge feature/somma-con-tipo
```

**Output atteso (conflitto):**
```
Auto-merging calcolatrice.py
CONFLICT (content): Merge conflict in calcolatrice.py
Automatic merge failed; fix conflicts and then commit the result.
```

---

#### Passo 4 — Ispezionare il Conflitto

```bash
git status
```

**Output atteso:**
```
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   calcolatrice.py
```

Apri `calcolatrice.py` e cerca i marker di conflitto. Vedrai qualcosa di simile:

```python
<<<<<<< HEAD
def somma(a: float, b: float, *, arrotonda: int = -1) -> float:
    """Restituisce la somma, opzionalmente arrotondata."""
    risultato = a + b
    if arrotonda >= 0:
        return round(risultato, arrotonda)
    return risultato
=======
def somma(a: float, b: float, tipo: str = "float") -> float | int:
    """Restituisce la somma, opzionalmente come intero."""
    risultato = a + b
    return int(risultato) if tipo == "int" else risultato
>>>>>>> feature/somma-con-tipo
```

---

#### Passo 5 — Risolvere il Conflitto

Decidi di combinare entrambe le funzionalità. Modifica il file eliminando i marker e scrivendo una versione unificata:

```python
def somma(
    a: float,
    b: float,
    *,
    arrotonda: int = -1,
    come_intero: bool = False,
) -> float | int:
    """Restituisce la somma con opzioni di formattazione.

    Args:
        a: Primo addendo.
        b: Secondo addendo.
        arrotonda: Numero di decimali (ignorato se come_intero=True).
        come_intero: Se True, restituisce un intero.
    """
    risultato = a + b
    if come_intero:
        return int(risultato)
    if arrotonda >= 0:
        return round(risultato, arrotonda)
    return risultato
```

---

#### Passo 6 — Completare il Merge

```bash
# Dopo aver risolto e salvato il file
git add calcolatrice.py

# Verifica che non ci siano altri conflitti
git status

# Completa il merge
git commit
```

Git aprirà il tuo editor con un messaggio pre-compilato "Merge branch 'feature/somma-con-tipo'". Accettalo (salva e chiudi l'editor).

---

#### Passo 7 — Verificare il Risultato

```bash
git log --oneline --graph
```

**Output atteso:**
```
*   4f5g6h7 (HEAD -> main) Merge branch 'feature/somma-con-tipo'
|\
| * 3e4f5g6 (feature/somma-con-tipo) feat(somma): aggiunge parametro tipo
* | 2d3e4f5 feat(somma): aggiunge parametro arrotonda
|/
* 7f8g9h0 test(divisione): aggiunge test
...
```

---

#### Verifica Finale

- [ ] `git status` mostra "nothing to commit, working tree clean"
- [ ] La funzione `somma` nel file ha entrambi i parametri: `arrotonda` e `come_intero`
- [ ] Il log mostra un merge commit con due genitori
- [ ] Non ci sono marker di conflitto (no `<<<<<<<`, no `=======`, no `>>>>>>>`) nel file

---

### C5 — .gitignore Completo per un Progetto Python (Semi-autonomo)

**Obiettivo:** Configurare correttamente un `.gitignore` e rimuovere file già tracciati.

**Istruzioni:** Per questo esercizio hai le istruzioni generali ma devi trovare i comandi esatti. Consulta la sezione A5 se necessario.

**Durata stimata:** 25 minuti

---

#### Scenario

Hai un progetto Python che per sbaglio ha già dei file non desiderati nel repository. Devi:
1. Creare un `.gitignore` appropriato
2. Rimuovere i file già tracciati
3. Verificare che tutto funzioni

---

#### Passo 1 — Setup iniziale

```bash
mkdir esercizio-c5
cd esercizio-c5
git init

# Crea un file Python
echo "print('hello')" > main.py

# Crea i file che NON dovresti committare
mkdir __pycache__
echo "bytecode" > __pycache__/main.cpython-312.pyc
echo "DATABASE_URL=postgres://user:password@localhost/db" > .env
mkdir .venv
echo "fake venv" > .venv/fake.txt
mkdir dist
echo "fake wheel" > dist/mypackage-1.0.0-py3-none-any.whl

# Aggiungi e committa TUTTO (sbagliato - includerà anche i file cattivi)
git add .
git status  # vedi cosa sta per essere committato
git commit -m "initial commit (sbagliato - include file non necessari)"
```

Verifica: `git ls-files` mostra tutti i file tracciati, inclusi quelli sbagliati.

---

#### Il Tuo Compito

Ora devi:

1. Creare un file `.gitignore` con i pattern appropriati per escludere `__pycache__`, `.env`, `.venv`, e `dist`
2. Rimuovere i file già tracciati dall'indice Git (senza eliminarli dal disco)
3. Committare la correzione
4. Verificare che `git status` non mostri più i file indesiderati

**Suggerimento 1:** Il comando per rimuovere una directory intera dall'indice Git è simile al comando per un singolo file, ma con l'opzione `-r` (recursive).

**Suggerimento 2:** Per rimuovere più file/directory in un solo comando, puoi elencarli separati da spazi.

**Suggerimento 3:** Usa `git ls-files` per verificare quali file sono ancora tracciati dopo la rimozione.

---

#### Soluzione Guidata

```bash
# 1. Crea il .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.venv/
.env
dist/
build/
*.egg-info/
EOF

# 2. Rimuovi i file già tracciati
git rm --cached -r __pycache__/
git rm --cached .env
git rm --cached -r .venv/
git rm --cached -r dist/

# 3. Committa la correzione
git add .gitignore
git commit -m "chore: aggiunge .gitignore e rimuove file non necessari"

# 4. Verifica
git ls-files
```

**Output atteso di git ls-files:**
```
.gitignore
main.py
```

I file `.env`, `__pycache__/`, `.venv/`, e `dist/` non sono più tracciati.


---

### C6 — pre-commit con ruff e mypy (Semi-autonomo)

**Obiettivo:** Installare e configurare pre-commit, osservare un hook fallire, capire il perche'.

**Istruzioni:** Hai indicazioni generali. Consulta la sezione B8 per i dettagli.

**Durata stimata:** 35 minuti

---

#### Scenario

Configurerai un sistema di controllo automatico che viene eseguito prima di ogni commit per garantire qualita' del codice.

---

#### Passo 1 — Inizializza il Progetto

```bash
mkdir esercizio-c6
cd esercizio-c6
git init

# Crea un ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oppure
.venv\Scripts\activate     # Windows

# Installa le dipendenze
pip install pre-commit ruff mypy
```

---

#### Passo 2 — Crea un File Python con Errori Intenzionali

Crea `qualita.py` con il seguente contenuto (include errori di stile e di tipo):

```python
import os
import sys
import json  # inutilizzato

def calcola(x,y,z):
    risultato=x+y+z
    print(risultato)
    return risultato

def dividi(a, b):
    return a/b  # potrebbe dividere per zero!

class Animale:
    def __init__(self, nome, eta):
        self.nome=nome
        self.eta=eta

    def saluta(self):
        print(f"Ciao, sono {self.nome} e ho {self.eta} anni")

animale = Animale("Fido",3)
animale.saluta()
```

---

#### Passo 3 — Crea il File di Configurazione pre-commit

Crea `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

---

#### Passo 4 — Installa gli Hook

```bash
pre-commit install
```

**Output atteso:**
```
pre-commit installed at .git/hooks/pre-commit
```

---

#### Passo 5 — Tenta un Commit e Osserva il Fallimento

```bash
git add qualita.py .pre-commit-config.yaml
git commit -m "test: aggiunge file con errori intenzionali"
```

Vedrai ruff segnalare problemi. Gli hook `--fix` correggeranno automaticamente alcuni errori.
Dopo la correzione automatica, il commit fallira' ugualmente — devi aggiungere i file corretti:

```bash
# Aggiungi i file corretti da ruff
git add qualita.py
git commit -m "test: aggiunge file con errori intenzionali"
```

---

#### Passo 6 — Il Tuo Compito

Basandoti sull'output degli hook:
1. Correggi manualmente tutti gli errori che ruff non ha corretto automaticamente
2. Aggiungi type hints alla funzione `calcola` e `dividi`
3. Aggiungi `pyproject.toml` con configurazione ruff minimale
4. Fai un commit pulito senza errori

**Suggerimento:** Usa `ruff check qualita.py` per vedere gli errori prima del commit.

---

#### Verifica Finale

- [ ] `pre-commit run --all-files` non mostra errori
- [ ] `git log --oneline` mostra almeno un commit pulito
- [ ] `qualita.py` ha type hints su tutte le funzioni pubbliche
- [ ] Non ci sono import inutilizzati

---

### C7 — Conventional Commits per una Settimana (Semi-autonomo)

**Obiettivo:** Eseguire 10 commit usando la convenzione, poi generare un changelog con git-cliff.

**Durata stimata:** 45 minuti

---

#### Scenario

Simulerai lo sviluppo di una settimana di lavoro su una piccola libreria Python, usando i Conventional Commits per ogni modifica.

---

#### Il Progetto: libreria `mathlib`

Crea la struttura:

```bash
mkdir mathlib-project
cd mathlib-project
git init

mkdir -p src/mathlib tests
touch src/mathlib/__init__.py
touch src/mathlib/base.py
touch tests/__init__.py
touch tests/test_base.py
```

---

#### I 10 Commit da Fare

Eseguili nell'ordine, creando il codice appropriato per ciascuno:

1. `feat(mathlib): inizializza struttura progetto` — crea la struttura base
2. `feat(base): aggiunge funzione somma` — implementa `def somma(a: float, b: float) -> float`
3. `feat(base): aggiunge funzione sottrai` — implementa `def sottrai(a: float, b: float) -> float`
4. `test(base): aggiunge test per somma` — test con pytest
5. `test(base): aggiunge test per sottrai` — test con pytest
6. `feat(base): aggiunge funzione moltiplica` — implementa la funzione
7. `fix(base): corregge divisione per zero in dividi` — implementa con guard clause
8. `docs(base): aggiunge docstring a tutte le funzioni` — docstring Google style
9. `refactor(base): estrae costanti matematiche` — `PI = 3.14159265358979`
10. `chore(deps): aggiunge pyproject.toml con dipendenze` — setup del progetto

---

#### Generare il Changelog

Dopo i 10 commit, installa git-cliff e genera il changelog:

```bash
pip install git-cliff

# Crea la configurazione
cat > cliff.toml << 'EOF'
[changelog]
header = "# Changelog\n\n"
body = """
## {{ version | default(value="Unreleased") }} - {{ timestamp | date(format="%Y-%m-%d") }}
{% for group, commits in commits | group_by(attribute="group") %}
### {{ group | upper_first }}
{% for commit in commits %}
- {{ commit.message }} ([{{ commit.id | truncate(length=7, end="") }}]({{ commit.id }}))\
{% endfor %}
{% endfor %}\n
"""
footer = ""
trim = true

[git]
conventional_commits = true
commit_parsers = [
  { message = "^feat", group = "Funzionalita'" },
  { message = "^fix", group = "Bugfix" },
  { message = "^docs", group = "Documentazione" },
  { message = "^refactor", group = "Refactoring" },
  { message = "^test", group = "Test" },
  { message = "^chore", group = "Manutenzione" },
]
EOF

# Genera il changelog
git cliff -o CHANGELOG.md
cat CHANGELOG.md
```

---

#### Verifica Finale

- [ ] `git log --oneline` mostra esattamente 10 commit (o piu')
- [ ] Tutti i messaggi seguono il formato Conventional Commits
- [ ] `CHANGELOG.md` e' stato generato e contiene sezioni per tipo
- [ ] I commit di tipo `feat` appaiono sotto "Funzionalita'"
- [ ] I commit di tipo `fix` appaiono sotto "Bugfix"


---

### C8 — GitHub Actions per pytest (Autonomo)

**Obiettivo:** Creare un workflow CI che esegue test automatici su ogni push, con badge nel README.

**Livello:** Autonomo — hai solo i requisiti, trova la soluzione.

**Durata stimata:** 40 minuti

---

#### Requisiti

Devi creare un repository GitHub (pubblico) con:

1. Una libreria Python con almeno 3 funzioni testate con pytest
2. Un file `.github/workflows/ci.yml` che:
   - Viene eseguito su `push` a qualsiasi branch e su `pull_request` verso `main`
   - Testa su Python 3.11 e 3.12
   - Esegue `pip install -e ".[test]"` (o equivalente)
   - Esegue `pytest --tb=short`
   - Fallisce se i test falliscono (comportamento predefinito di CI)
3. Un `README.md` con il badge di stato CI

---

#### Struttura Suggerita

```
progetto-c8/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── mylib/
│       ├── __init__.py
│       └── funzioni.py
├── tests/
│   ├── __init__.py
│   └── test_funzioni.py
├── pyproject.toml
└── README.md
```

---

#### Schema del ci.yml (da completare)

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Imposta Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      # Completa i passi rimanenti:
      # - Installa le dipendenze
      # - Esegui pytest
```

---

#### Badge di Stato

Nel README.md aggiungi (sostituisci con i tuoi dati):

```markdown
![CI](https://github.com/TUO-USERNAME/progetto-c8/actions/workflows/ci.yml/badge.svg)
```

---

#### Criteri di Successo

- [ ] Il workflow si avvia automaticamente su push
- [ ] Testa su Python 3.11 E 3.12 (matrix build)
- [ ] Tutti i test passano nel CI
- [ ] Il badge nel README mostra "passing"
- [ ] La pagina GitHub Actions mostra il workflow completato con successo

---

#### Soluzione di Riferimento (ci.yml completo)

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Imposta Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Installa dipendenze
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          pip install -e .

      - name: Esegui test
        run: |
          pytest tests/ -v --tb=short
```

---

### C9 — Fork e Pull Request su Repo Pubblico (Autonomo)

**Obiettivo:** Partecipare a un progetto open source tramite Fork e Pull Request.

**Livello:** Autonomo — simula il workflow reale di contributore open source.

**Durata stimata:** 45 minuti

---

#### Scenario

Trovi un progetto open source su GitHub e vuoi contribuire correggendo un bug o aggiungendo documentazione.

---

#### Passo 1 — Trova un Repo Adatto

Opzione A: Usa il repo del tuo esercizio C8 (se è pubblico)
Opzione B: Cerca su GitHub: `topic:good-first-issue language:python`

---

#### Passo 2 — Fork del Repository

Tramite interfaccia GitHub:
- Clicca il pulsante "Fork" in alto a destra
- Seleziona il tuo account come destinazione

Oppure tramite GitHub CLI:

```bash
gh repo fork OWNER/REPO-NAME --clone
cd REPO-NAME
```

---

#### Passo 3 — Crea un Branch per la Tua Modifica

```bash
# Nomina il branch in modo descrittivo
git switch -c fix/errore-nella-documentazione
# oppure
git switch -c feat/aggiungi-esempio-utilizzo
```

---

#### Passo 4 — Fai la Modifica e Committa

Fai una modifica significativa (anche solo documentazione o un test):

```bash
# Dopo la modifica
git add -p  # aggiungi interattivamente solo le modifiche pertinenti
git commit -m "docs: corregge esempio nella sezione installazione"
```

---

#### Passo 5 — Push e Crea la PR

```bash
git push -u origin fix/errore-nella-documentazione

# Crea la PR via CLI
gh pr create \
  --title "docs: corregge esempio nella sezione installazione" \
  --body "## Problema
L'esempio nella sezione installazione aveva un errore di sintassi.

## Soluzione
Ho corretto il comando pip e verificato che funziona su Python 3.12.

## Test
- [x] Verificato manualmente
" \
  --base main
```

---

#### Criteri di Successo

- [ ] Il fork esiste nel tuo account GitHub
- [ ] La PR e' aperta e visibile su GitHub
- [ ] Il branch della PR ha un nome descrittivo
- [ ] Il messaggio della PR descrive cosa e perche' hai cambiato
- [ ] Il CI della PR (se configurato) passa


---

### C10 — Release con Tag e Changelog (Autonomo, Sfida)

**Obiettivo:** Creare un processo di release professionale con versionamento semantico, changelog automatico e GitHub Release.

**Livello:** Autonomo (Sfida) — questo e' il workflow reale usato dai team professionali.

**Durata stimata:** 60 minuti

---

#### Scenario

Il tuo progetto ha raggiunto una milestone. E' ora di fare la prima release pubblica (v1.0.0) e poi una release con nuove feature (v1.1.0).

---

#### Parte A — Release v1.0.0

```bash
# Assumi di avere il progetto dal C7 o C8
cd mathlib-project  # oppure il tuo progetto

# Verifica che tutto sia committato
git status
git log --oneline

# Crea il tag annotato
git tag -a v1.0.0 -m "Prima release stabile

Funzionalita':
- somma, sottrai, moltiplica, dividi
- Gestione divisione per zero
- Documentazione completa"

# Verifica il tag
git show v1.0.0

# Pubblica il tag su GitHub
git push origin v1.0.0
```

---

#### Parte B — Aggiungi Feature per v1.1.0

Crea un branch per la nuova feature:

```bash
git switch -c feat/potenza
```

Aggiungi la funzione `potenza` alla libreria:

```python
def potenza(base: float, esponente: float) -> float:
    """Restituisce base elevata a esponente.

    Args:
        base: La base del calcolo.
        esponente: L'esponente del calcolo.

    Returns:
        Il risultato di base ** esponente.
    """
    return base ** esponente
```

Aggiungi i test, committa, fai merge su main:

```bash
git add .
git commit -m "feat(base): aggiunge funzione potenza"
git switch main
git merge feat/potenza --no-ff -m "feat: aggiunge funzione potenza (merge)"
```

---

#### Parte C — Release v1.1.0 con Changelog

```bash
# Genera il changelog tra v1.0.0 e HEAD
git cliff v1.0.0..HEAD -o CHANGELOG_1.1.0.md

# Oppure aggiorna il CHANGELOG.md completo
git cliff -o CHANGELOG.md

# Committa il changelog aggiornato
git add CHANGELOG.md
git commit -m "docs(changelog): aggiorna per v1.1.0"

# Crea il tag
git tag -a v1.1.0 -m "Release v1.1.0

Novita':
- Aggiunta funzione potenza (feat)"

# Pubblica
git push origin main
git push origin v1.1.0
```

---

#### Parte D — Crea GitHub Release

```bash
# Crea la release su GitHub con note automatiche
gh release create v1.1.0 \
  --title "v1.1.0 - Funzione Potenza" \
  --notes-file CHANGELOG_1.1.0.md \
  --latest
```

Oppure usa l'interfaccia GitHub:
- Vai su "Releases" → "Draft a new release"
- Tag: v1.1.0
- Titolo: v1.1.0 - Funzione Potenza
- Incolla il contenuto del changelog

---

#### Criteri di Successo

- [ ] `git tag` mostra sia v1.0.0 che v1.1.0
- [ ] `git show v1.0.0` mostra il messaggio annotato con le funzionalita'
- [ ] `CHANGELOG.md` distingue chiaramente le due versioni
- [ ] La pagina GitHub Releases mostra entrambe le release
- [ ] v1.1.0 e' marcata come "Latest release"

---

## Parte D — Argomenti da Esperto

> Questa sezione e' per chi ha completato la Parte C e vuole approfondire gli aspetti avanzati di Git. Non e' necessaria per l'uso quotidiano, ma indispensabile per comprendere Git a fondo.

---

### D1 — Git Internals: Come Git Memorizza Davvero i Dati

Git non e' un sistema di controllo versione tradizionale che memorizza differenze (delta) — e' un **content-addressable filesystem**. Ogni oggetto e' identificato da un hash SHA-1 del suo contenuto.

---

#### I Quattro Tipi di Oggetti Git

```
blob     → contenuto di un file
tree     → directory (lista di blob e tree con nomi)
commit   → snapshot con metadati e puntatori
tag      → riferimento annotato a un commit
```

---

#### Come un Commit Punta a Tutto

Quando esegui `git commit`, Git crea questa catena di oggetti:

```
commit (hash: abc123)
├── tree (hash: def456)          ← snapshot della directory radice
│   ├── blob: README.md         ← contenuto del file README
│   ├── blob: main.py           ← contenuto di main.py
│   └── tree: src/              ← subdirectory
│       ├── blob: utils.py
│       └── blob: models.py
└── parent: ghi789              ← hash del commit precedente
```

---

#### Esplorare gli Oggetti con git cat-file

```bash
# Crea un repository di test
mkdir git-internals-lab
cd git-internals-lab
git init
echo "Hello, Git!" > hello.txt
git add hello.txt
git commit -m "primo commit"

# Trova il hash del commit piu' recente
git log --oneline

# Ispeziona il commit (tipo, contenuto)
git cat-file -t HEAD         # tipo: "commit"
git cat-file -p HEAD         # contenuto del commit

# Esempio output:
# tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904
# author Renan <email> 1720000000 +0000
# committer Renan <email> 1720000000 +0000
#
# primo commit
```

---

#### Ispezionare il Tree

```bash
# Ottieni il hash del tree dal commit
TREE_HASH=$(git cat-file -p HEAD | grep "^tree" | cut -d' ' -f2)
echo "Tree hash: $TREE_HASH"

# Ispeziona il tree
git cat-file -p $TREE_HASH

# Output:
# 100644 blob 8ab686eafeb1f44702738c8b0f24f2567c36da6d    hello.txt
```

---

#### Ispezionare il Blob

```bash
# Ottieni il hash del blob
BLOB_HASH=$(git cat-file -p $TREE_HASH | grep "hello.txt" | cut -d' ' -f3)
echo "Blob hash: $BLOB_HASH"

# Ispeziona il blob (contenuto grezzo del file)
git cat-file -p $BLOB_HASH

# Output:
# Hello, Git!
```

---

#### Pack Files e Delta Compression

Git inizialmente memorizza ogni oggetto come file separato nella directory `.git/objects/`. Con il tempo (o con `git gc`), Git comprime questi oggetti in **pack files** usando delta compression:

```bash
# Vedi gli oggetti loose
ls .git/objects/

# Forza il packing
git gc --aggressive

# Ora gli oggetti sono in pack files
ls .git/objects/pack/
# pack-HASH.idx  ← indice per accesso rapido
# pack-HASH.pack ← dati compressi
```

```bash
# Statistiche del pack file
git count-objects -vH
```

---

#### Garbage Collection

Git tiene traccia degli oggetti "raggiungibili" tramite i refs (branch, tag, HEAD). Gli oggetti non raggiungibili sono candidati per la garbage collection:

```bash
# Vedi quando scadono gli oggetti irraggiungibili
git config gc.reflogExpire           # default: 90 days
git config gc.reflogExpireUnreachable  # default: 30 days

# Esegui garbage collection manuale
git gc
git gc --prune=now  # rimuovi subito gli oggetti scaduti
```


---

### D2 — Interactive Rebase: Riscrivere la Storia

> **Attenzione:** Non usare interactive rebase su commit gia' condivisi (pushati). Modifica solo commit locali o su branch non condivisi.

Il rebase interattivo (`git rebase -i`) e' uno strumento potente per pulire la storia dei commit prima di fare merge o push.

---

#### Quando Usarlo

- Hai fatto 5 "WIP" commits e vuoi farne 1 pulito
- Un messaggio di commit e' sbagliato e vuoi correggerlo
- Vuoi riordinare i commit logicamente
- Vuoi eliminare un commit specifico

---

#### Le Operazioni Disponibili

| Operazione | Abbreviazione | Cosa fa |
|---|---|---|
| `pick` | `p` | Usa il commit as-is |
| `reword` | `r` | Usa il commit ma modifica il messaggio |
| `edit` | `e` | Pausa per modificare il commit |
| `squash` | `s` | Unisci con il commit precedente (mantieni messaggi) |
| `fixup` | `f` | Unisci con il commit precedente (scarta il messaggio) |
| `drop` | `d` | Elimina il commit |
| `exec` | `x` | Esegui un comando shell |

---

#### Esempio Pratico: Squash di 3 Commit WIP

```bash
# Situazione di partenza (git log --oneline):
# a1b2c3d WIP: aggiunge validazione
# e4f5g6h WIP: fix bug nella validazione
# i7j8k9l WIP: corregge typo
# m0n1o2p feat: aggiunge funzione base

# Vogliamo unire i 3 WIP in un singolo commit pulito
git rebase -i HEAD~3
```

L'editor si apre con:

```
pick a1b2c3d WIP: aggiunge validazione
pick e4f5g6h WIP: fix bug nella validazione
pick i7j8k9l WIP: corregge typo

# Rebase m0n1o2p..i7j8k9l onto m0n1o2p (3 commands)
#
# Commands:
# p, pick <commit> = use commit
# r, reword <commit> = use commit, but edit the commit message
# ...
```

Modifica il file in:

```
pick a1b2c3d WIP: aggiunge validazione
squash e4f5g6h WIP: fix bug nella validazione
squash i7j8k9l WIP: corregge typo
```

Salva e chiudi. Git apre un secondo editor per il messaggio del commit unificato:

```
feat(validazione): aggiunge validazione con correzioni

- Aggiunge controllo input non nullo
- Corregge bug con valori negativi
- Normalizza il messaggio di errore
```

---

#### Esempio: Correggere un Messaggio di Commit

```bash
# Modifica il secondo-ultimo commit
git rebase -i HEAD~2
```

Cambia `pick` in `reword` per il commit che vuoi modificare:

```
reword a1b2c3d fix: corregge bug (messaggio vecchio)
pick e4f5g6h test: aggiunge test per il fix
```

Salva. L'editor si riaprira' con il messaggio del commit da modificare.

---

#### Abortire un Rebase

Se qualcosa va storto durante il rebase:

```bash
git rebase --abort
```

Questo riporta il repository allo stato prima del rebase.

---

#### Continuare Dopo un Conflitto

Se durante il rebase c'e' un conflitto:

```bash
# 1. Risolvi il conflitto nel file
# 2. Aggiungi il file risolto
git add file-risolto.py

# 3. Continua il rebase
git rebase --continue
```

---

### D3 — git bisect: Trovare il Commit che Ha Introdotto un Bug

`git bisect` esegue una ricerca binaria nella storia dei commit per trovare quale commit ha introdotto un bug.

---

#### Il Problema

Hai 1000 commit. Il bug non c'era 6 mesi fa. Come trovi quale commit lo ha introdotto?

Con una ricerca lineare: fino a 1000 test.
Con `git bisect` (ricerca binaria): massimo 10 test.

---

#### Workflow Manuale

```bash
# Inizia il bisect
git bisect start

# Indica un commit "cattivo" (con il bug) - di solito HEAD
git bisect bad

# Indica un commit "buono" (senza il bug)
git bisect good v1.0.0
# oppure
git bisect good abc123  # hash di un commit noto come buono
```

Git fa automaticamente il checkout del commit a meta' strada e mostra:

```
Bisecting: 499 revisions left to test after this
(roughly 9 steps)
[hash] messaggio del commit
```

Ora testa manualmente se il bug e' presente:

```bash
# Se il bug E' presente nel commit attuale:
git bisect bad

# Se il bug NON e' presente nel commit attuale:
git bisect good
```

Ripeti finche' Git trova il commit colpevole:

```
abc123 is the first bad commit
commit abc123
Author: ...
Date:   ...

    feat: aggiunge nuova funzionalita' X
```

---

#### Terminare il Bisect

```bash
git bisect reset
```

Questo riporta HEAD al branch originale.

---

#### Bisect Automatico con Script

Se hai un test che riproduce il bug, puoi automatizzare completamente:

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.0.0

# Script di test (exit 0 = buono, exit 1 = cattivo)
git bisect run python tests/test_bug_specifico.py
```

Git eseguira' automaticamente lo script su ogni commit, trovando il colpevole senza intervento manuale.

---

#### Esempio con Script di Test

```python
#!/usr/bin/env python
# test_bug_specifico.py - exit 0 se OK, exit 1 se bug presente
import sys
try:
    from mylib.calcolo import calcola_valore
    risultato = calcola_valore(42)
    if risultato != 84:  # il bug fa restituire un valore sbagliato
        sys.exit(1)
    sys.exit(0)
except Exception:
    sys.exit(1)
```

```bash
git bisect run python test_bug_specifico.py
```


---

### D4 — GPG/SSH Commit Signing: Firma Verificata su GitHub

La firma dei commit permette di verificare che i commit siano stati creati da te (e non da qualcuno che si e' impossessato del tuo accesso).

Su GitHub i commit firmati mostrano il badge **"Verified"** verde.

---

#### Metodo 1: Firma con Chiave SSH (Raccomandato — Piu' Semplice)

Se hai gia' una chiave SSH configurata per GitHub (vedi B4):

```bash
# Configura Git per usare SSH per la firma
git config --global gpg.format ssh

# Specifica quale chiave usare (sostituisci con il percorso della tua chiave)
git config --global user.signingkey ~/.ssh/id_ed25519.pub

# Abilita la firma automatica per tutti i commit
git config --global commit.gpgsign true

# Per i tag
git config --global tag.gpgsign true
```

---

#### Aggiungere la Chiave a GitHub per la Verifica

1. Vai su GitHub → Settings → SSH and GPG keys
2. Clicca "New SSH key"
3. **IMPORTANTE:** Scegli tipo "**Signing Key**" (non "Authentication Key")
4. Incolla il contenuto di `~/.ssh/id_ed25519.pub`

---

#### Testare la Firma

```bash
# Fai un commit di test
echo "test firma" >> README.md
git add README.md
git commit -m "test: verifica firma commit"

# Verifica la firma
git log --show-signature -1
```

**Output atteso:**
```
commit abc123...
Good "git" signature for YOUR@EMAIL.COM with ED25519 key SHA256:XXXX
Author: Renan <your@email.com>
...
```

---

#### Metodo 2: Firma con Chiave GPG (Tradizionale)

```bash
# Genera una chiave GPG (raccomandato: 4096 bit RSA o Ed25519)
gpg --full-generate-key

# Seleziona: (9) ECC (sign only) → (1) Curve 25519
# Nome: Il tuo nome
# Email: la stessa usata in git config user.email
# Scadenza: 0 (no scadenza) o 2y

# Ottieni il fingerprint della chiave
gpg --list-secret-keys --keyid-format=long

# Output esempio:
# sec   ed25519/ABCD1234 2024-01-01 [SC]
#       FINGERPRINT-LUNGO
# uid   [ultimate] Renan <email>

# Esporta la chiave pubblica per GitHub
gpg --armor --export ABCD1234
```

---

#### Configurare Git per Usare GPG

```bash
# Usa il tuo key ID (la parte dopo "ed25519/")
git config --global user.signingkey ABCD1234
git config --global commit.gpgsign true
git config --global tag.gpgsign true

# Su macOS potrebbe servire
git config --global gpg.program gpg
```

---

#### Aggiungere la Chiave GPG a GitHub

1. Copia l'output di `gpg --armor --export ABCD1234`
2. Vai su GitHub → Settings → SSH and GPG keys
3. Clicca "New GPG key"
4. Incolla la chiave pubblica

---

#### Risoluzione Problemi Comuni

**Errore: "error: gpg failed to sign the data"**
```bash
export GPG_TTY=$(tty)
echo "export GPG_TTY=$(tty)" >> ~/.bashrc
```

**Errore: "secret key not available"**
```bash
# Verifica che la chiave nel git config corrisponda a quella GPG
git config user.signingkey
gpg --list-secret-keys
```

---

### D5 — Secret Scanning: Mai Committare Segreti

Uno dei problemi piu' gravi in Git e' committare accidentalmente segreti (password, API key, token) che poi rimangono nella storia per sempre.

---

#### Perche' E' Critico

Un segreto committato anche brevemente e' compromesso perche':
- Rimane nella storia Git anche dopo la rimozione
- Chiunque cloni il repo puo' trovarlo con `git log`
- I bot di GitHub scansionano i push in tempo reale
- I segreti nelle PR pubbliche sono indicizzati dai motori di ricerca

---

#### Strumento 1: gitleaks (Prevenzione Pre-Push)

```bash
# Installa gitleaks
# Linux/Mac via brew:
brew install gitleaks

# Oppure scarica il binario: https://github.com/gitleaks/gitleaks/releases

# Scansiona il repository corrente
gitleaks detect --source . --verbose

# Scansiona uno specifico range di commit
gitleaks detect --log-opts="HEAD~10..HEAD"
```

---

#### Integrare gitleaks come Hook Pre-commit

Aggiungi a `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.18.4
  hooks:
    - id: gitleaks
```

---

#### Strumento 2: git-secrets (Amazon)

```bash
# Installa
brew install git-secrets  # Mac
# Linux: segui https://github.com/awslabs/git-secrets

# Configura per un repo
git secrets --install
git secrets --register-aws  # aggiunge pattern per AWS keys

# Scansiona il repo
git secrets --scan
```

---

#### Cosa Fare Se Hai Gia' Committato un Segreto

**Passo 1 — Invalida Immediatamente il Segreto**
Vai sul servizio (AWS, GitHub, ecc.) e revoca il token/chiave SUBITO. Questo e' il passo piu' importante.

**Passo 2 — Rimuovi dalla Storia con BFG Repo-Cleaner**

BFG e' piu' semplice di `git filter-repo` per rimozioni semplici:

```bash
# Installa BFG (richiede Java)
# Scarica bfg.jar da: https://rtyley.github.io/bfg-repo-cleaner/

# Crea un file con il segreto da rimuovere
echo "IL_TUO_SEGRETO_COMPROMESSO" > segreti_da_rimuovere.txt

# Clona una copia "mirror" del repo
git clone --mirror git@github.com:TUO/REPO.git repo-mirror.git
cd repo-mirror.git

# Esegui BFG
java -jar bfg.jar --replace-text ../segreti_da_rimuovere.txt

# Pulisci e forza il push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

**Passo 3 — Notifica i Collaboratori**
Tutti devono eseguire `git fetch` e rifare il checkout — la storia e' cambiata.

---

#### Prevenzione: il File .env.example

Non committare mai `.env` — committa `.env.example` con i nomi delle variabili ma senza valori reali:

```bash
# .env (in .gitignore - MAI committare)
DATABASE_URL=postgres://user:password@localhost/mydb
API_KEY=sk-live-1234567890abcdef

# .env.example (committato - mostra la struttura)
DATABASE_URL=postgres://USER:PASSWORD@HOST/DBNAME
API_KEY=sk-YOURKEY
```


---

### D6 — Monorepo con Git: Subtree e Submodule

Quando un progetto cresce, potresti voler gestire piu' repository correlati. Git offre due approcci: **subtree** e **submodule**.

---

#### Approccio 1: git subtree (Raccomandato)

Con subtree, il contenuto di un repo esterno viene copiato fisicamente nel tuo repo. Non richiede step aggiuntivi durante il clone.

---

##### Aggiungere un Subtree

```bash
# Aggiunge la libreria comune come subtree nella directory libs/comune
git subtree add \
  --prefix=libs/comune \
  https://github.com/tuo/libreria-comune.git \
  main \
  --squash
```

L'opzione `--squash` comprime tutta la storia del repo esterno in un singolo commit.

---

##### Aggiornare il Subtree

Quando il repo esterno ha aggiornamenti:

```bash
git subtree pull \
  --prefix=libs/comune \
  https://github.com/tuo/libreria-comune.git \
  main \
  --squash
```

---

##### Contribuire al Repo Esterno dal Subtree

Se hai fatto modifiche al codice in `libs/comune` e vuoi inviarle al repo originale:

```bash
git subtree push \
  --prefix=libs/comune \
  https://github.com/tuo/libreria-comune.git \
  main
```

---

##### Struttura di un Monorepo con Subtree

```
mio-progetto/
├── src/
│   └── app/
│       └── main.py
├── libs/
│   └── comune/          ← subtree da github.com/tuo/libreria-comune
│       ├── utils.py
│       └── models.py
├── tests/
└── pyproject.toml
```

---

#### Approccio 2: git submodule

Con submodule, il repo esterno rimane separato. Il tuo repo contiene solo un puntatore all'hash specifico del repo esterno.

---

##### Aggiungere un Submodule

```bash
# Aggiunge il submodule
git submodule add https://github.com/tuo/libreria-comune.git libs/comune
git commit -m "chore: aggiunge libreria-comune come submodule"
```

---

##### Clonare un Repo con Submodule

```bash
# Metodo 1: clone con submodule in un solo comando
git clone --recurse-submodules https://github.com/tuo/progetto.git

# Metodo 2: se hai gia' clonato senza --recurse-submodules
git submodule init
git submodule update
```

---

##### Aggiornare i Submodule

```bash
# Aggiorna tutti i submodule alla versione piu' recente
git submodule update --remote

# Committa il puntatore aggiornato
git add libs/comune
git commit -m "chore: aggiorna libreria-comune all'ultima versione"
```

---

#### Subtree vs Submodule: Quale Scegliere?

| Criterio | Subtree | Submodule |
|---|---|---|
| Clone semplicita' | Semplice (nessun passo aggiuntivo) | Richiede `--recurse-submodules` |
| Separazione del codice | Codice copiato nel repo | Puntatore al repo esterno |
| Modifica del codice esterno | Facile (modifica e push) | Complesso (entrare nel submodule) |
| Storia del repo | Piu' pulita con --squash | Separata e indipendente |
| Raccomandato per | Librerie condivise, utilities | Dipendenze esterne stabili |

---

### D7 — Advanced Git Hooks: Automazione a Ogni Livello

I Git hooks sono script che si eseguono automaticamente in risposta a eventi Git. Sono potentissimi per automazione, validazione e integrazione.

---

#### Dove Vivono i Hook

```bash
ls .git/hooks/
# applypatch-msg   post-commit       pre-applypatch
# commit-msg       post-receive      pre-commit
# fsmonitor-watchman post-rewrite    pre-push
# post-applypatch  post-update       pre-rebase
# prepare-commit-msg  update
```

Un hook e' semplicemente uno script eseguibile. Per attivarlo, crea il file (senza estensione) e rendilo eseguibile:

```bash
touch .git/hooks/mio-hook
chmod +x .git/hooks/mio-hook
```

---

#### Hook Client-Side Principali

**pre-commit** — Eseguito prima del commit. Se esce con codice non-zero, il commit viene annullato.

```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Verifico il codice..."

# Esegui ruff
if ! ruff check .; then
    echo "ERRORE: ruff ha trovato problemi. Commit annullato."
    exit 1
fi

# Verifica che non ci siano secret comuni
if grep -r "API_KEY\s*=" --include="*.py" .; then
    echo "ATTENZIONE: Trovata possibile API key nel codice!"
    exit 1
fi

echo "Controlli superati."
exit 0
```

---

**commit-msg** — Riceve il messaggio di commit come argomento. Usato per validare il formato.

```bash
#!/bin/bash
# .git/hooks/commit-msg
COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat $COMMIT_MSG_FILE)

# Verifica formato Conventional Commits
PATTERN="^(feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert)(\([a-z]+\))?: .+"

if ! echo "$COMMIT_MSG" | grep -qE "$PATTERN"; then
    echo "ERRORE: Il messaggio di commit non segue Conventional Commits."
    echo "Formato atteso: tipo(scope): descrizione"
    echo "Esempi:"
    echo "  feat(auth): aggiunge login OAuth"
    echo "  fix(api): corregge timeout richiesta"
    exit 1
fi

exit 0
```

---

**pre-push** — Eseguito prima del push. Riceve remote e URL come argomenti.

```bash
#!/bin/bash
# .git/hooks/pre-push
REMOTE=$1
URL=$2

# Impedisci push diretto a main/master
CURRENT_BRANCH=$(git symbolic-ref HEAD | sed 's|refs/heads/||')
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    echo "ERRORE: Push diretto a $CURRENT_BRANCH non consentito!"
    echo "Usa un branch e crea una Pull Request."
    exit 1
fi

# Esegui i test prima del push
echo "Eseguo i test prima del push..."
if ! python -m pytest tests/ -q; then
    echo "ERRORE: I test sono falliti. Push annullato."
    exit 1
fi

echo "Push consentito."
exit 0
```

---

**prepare-commit-msg** — Eseguito dopo che Git prepara il messaggio di default, prima dell'editor.

```bash
#!/bin/bash
# .git/hooks/prepare-commit-msg
# Aggiunge automaticamente il nome del branch al messaggio

COMMIT_MSG_FILE=$1
COMMIT_MSG_SOURCE=$2

if [[ "$COMMIT_MSG_SOURCE" == "" ]]; then
    # Solo per commit normali (non merge, squash, ecc.)
    BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
    
    # Estrai il ticket dal nome del branch (es. "feature/PROJ-123-descrizione")
    TICKET=$(echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+')
    
    if [[ -n "$TICKET" ]]; then
        sed -i.bak "1s/^/$TICKET: /" "$COMMIT_MSG_FILE"
    fi
fi
```

---

#### Hook Server-Side (su Git Server/GitHub)

Questi hook vengono eseguiti sul server, non sul client:

| Hook | Quando | Uso Tipico |
|---|---|---|
| `pre-receive` | Prima di accettare push | Validazione branch policy, size limits |
| `update` | Per ogni branch aggiornato | Autorizzazione per branch specifici |
| `post-receive` | Dopo aver accettato push | Notifiche, deploy automatico, CI trigger |

> I server-side hook non sono configurabili su GitHub standard. Sono disponibili su GitHub Enterprise, GitLab, o server Git autogestiti.

---

#### Distribuire Hook con il Team

I file in `.git/hooks/` non vengono committati (`.git/` e' ignorato). Per distribuire hook al team:

**Soluzione 1: pre-commit framework** (consigliato — vedi B8)

**Soluzione 2: Cartella hook committata**

```bash
# Crea una cartella per gli hook
mkdir -p .githooks
cp .git/hooks/commit-msg .githooks/
git add .githooks/
git commit -m "chore: aggiunge hook condivisi del team"

# Ogni sviluppatore esegue una sola volta:
git config core.hooksPath .githooks
chmod +x .githooks/*
```

Aggiungi al README:
```markdown
## Setup

Dopo il clone, configura gli hook:
\`\`\`bash
git config core.hooksPath .githooks
chmod +x .githooks/*
\`\`\`
```


---

## Parte E — Riferimento Rapido

> Questa sezione e' il tuo manuale da consultare ogni giorno. Non devi memorizzare tutto — torna qui quando ne hai bisogno.

---

### E1 — Checklist Git Essenziale

Usa questa checklist per ogni progetto Python che inizi.

---

#### Setup Iniziale Progetto

- [ ] `git init` eseguito nella radice del progetto
- [ ] `.gitignore` configurato per Python (include `__pycache__`, `.venv`, `.env`, `dist`, `*.pyc`)
- [ ] `git config user.name` e `user.email` configurati (globale o locale)
- [ ] Branch principale chiamato `main` (non `master`)
- [ ] Primo commit include solo i file essenziali

#### GitHub e Remote

- [ ] Repository GitHub creato (pubblico o privato)
- [ ] Chiave SSH generata e aggiunta a GitHub (tipo "Authentication Key")
- [ ] `git remote add origin git@github.com:USER/REPO.git` configurato
- [ ] `git push -u origin main` eseguito con successo
- [ ] Chiave SSH di firma aggiunta a GitHub (tipo "Signing Key") — opzionale

#### Workflow Quotidiano

- [ ] Ogni nuova feature/bugfix inizia su un branch separato
- [ ] I messaggi di commit seguono Conventional Commits
- [ ] `git status` consultato prima di ogni `git add`
- [ ] `git diff --staged` controllato prima di ogni `git commit`
- [ ] `git pull --rebase` usato per sincronizzare con il remote

#### Qualita' del Codice

- [ ] `pre-commit` installato e configurato
- [ ] `.pre-commit-config.yaml` include almeno ruff e trailing-whitespace
- [ ] `pre-commit run --all-files` pulito su tutta la codebase
- [ ] Nessun file `.env` con segreti reali nei commit

#### Pull Request

- [ ] Il titolo della PR segue Conventional Commits
- [ ] La descrizione spiega "cosa" e "perche'" (non solo "come")
- [ ] I test passano nel CI prima del merge
- [ ] Almeno un reviewer ha approvato la PR

#### Release

- [ ] `CHANGELOG.md` aggiornato prima di ogni release
- [ ] Tag annotato creato con `git tag -a vX.Y.Z -m "..."`
- [ ] Tag pushato con `git push origin vX.Y.Z`
- [ ] GitHub Release creata con le note di rilascio

#### Sicurezza

- [ ] Nessun segreto nei commit (API key, password, token)
- [ ] `.env.example` committato al posto di `.env`
- [ ] gitleaks o equivalente configurato come hook pre-commit
- [ ] Commit signing abilitato

---

### E2 — Cheat Sheet Comandi Git

#### Inizializzazione e Configurazione

| Comando | Descrizione |
|---|---|
| `git init` | Inizializza un repository Git |
| `git clone URL` | Clona un repository remoto |
| `git config --global user.name "Nome"` | Imposta il nome utente globale |
| `git config --global user.email "email"` | Imposta l'email globale |
| `git config --list` | Mostra tutta la configurazione |
| `git config --global alias.st status` | Crea un alias `git st` |

#### Staging e Commit

| Comando | Descrizione |
|---|---|
| `git status` | Mostra lo stato del working tree |
| `git add FILE` | Aggiunge un file allo staging |
| `git add -p` | Aggiunge interattivamente parti di file |
| `git add .` | Aggiunge tutti i file modificati |
| `git commit -m "messaggio"` | Crea un commit |
| `git commit --amend` | Modifica l'ultimo commit (solo locale) |
| `git reset HEAD FILE` | Rimuove un file dallo staging |
| `git diff` | Mostra modifiche non staged |
| `git diff --staged` | Mostra modifiche staged |

#### Branch

| Comando | Descrizione |
|---|---|
| `git branch` | Elenca i branch locali |
| `git branch -a` | Elenca tutti i branch (inclusi remoti) |
| `git switch -c NOME` | Crea e vai al nuovo branch |
| `git switch NOME` | Cambia branch |
| `git branch -d NOME` | Elimina un branch (sicuro) |
| `git branch -D NOME` | Forza l'eliminazione di un branch |
| `git merge BRANCH` | Fai merge del branch nel corrente |
| `git merge --no-ff BRANCH` | Merge con commit di merge esplicito |
| `git rebase BRANCH` | Rebasa il corrente su BRANCH |

#### Storia

| Comando | Descrizione |
|---|---|
| `git log --oneline` | Storia compatta |
| `git log --oneline --graph` | Storia con visualizzazione grafica |
| `git log --oneline --all` | Storia di tutti i branch |
| `git show HASH` | Mostra i dettagli di un commit |
| `git diff HASH1 HASH2` | Differenze tra due commit |
| `git blame FILE` | Chi ha scritto ogni riga |


#### Remote e Sincronizzazione

| Comando | Descrizione |
|---|---|
| `git remote add origin URL` | Aggiunge un remote |
| `git remote -v` | Mostra i remote configurati |
| `git push -u origin BRANCH` | Push e imposta il tracking |
| `git push` | Push al remote configurato |
| `git push --tags` | Push di tutti i tag |
| `git pull` | Fetch e merge dal remote |
| `git pull --rebase` | Fetch e rebase dal remote |
| `git fetch` | Scarica senza fare merge |
| `git fetch --prune` | Scarica e rimuove branch remoti cancellati |

#### Stash

| Comando | Descrizione |
|---|---|
| `git stash` | Salva le modifiche temporaneamente |
| `git stash push -m "descrizione"` | Stash con messaggio |
| `git stash list` | Elenca gli stash |
| `git stash pop` | Ripristina l'ultimo stash |
| `git stash apply stash@{1}` | Applica uno stash specifico |
| `git stash show -p` | Mostra le modifiche dello stash |
| `git stash drop stash@{0}` | Elimina uno stash specifico |
| `git stash clear` | Elimina tutti gli stash |

#### Tag

| Comando | Descrizione |
|---|---|
| `git tag` | Elenca tutti i tag |
| `git tag -a v1.0.0 -m "msg"` | Crea tag annotato |
| `git tag -l "v1.*"` | Filtra i tag |
| `git show v1.0.0` | Mostra dettagli del tag |
| `git push origin v1.0.0` | Pubblica un tag specifico |
| `git push --tags` | Pubblica tutti i tag |
| `git tag -d v1.0.0` | Elimina tag localmente |

#### Undoing e Correzioni

| Comando | Descrizione |
|---|---|
| `git restore FILE` | Scarta modifiche nel working dir |
| `git restore --staged FILE` | Rimuove file dallo staging |
| `git revert HASH` | Annulla un commit (crea nuovo commit) |
| `git reset --soft HEAD~1` | Annulla ultimo commit (mantieni staged) |
| `git reset --mixed HEAD~1` | Annulla ultimo commit (mantieni modified) |
| `git reset --hard HEAD~1` | Annulla ultimo commit (scarta tutto) |

#### Avanzati

| Comando | Descrizione |
|---|---|
| `git rebase -i HEAD~N` | Rebase interattivo degli ultimi N commit |
| `git cherry-pick HASH` | Applica un commit specifico al branch corrente |
| `git bisect start` | Inizia la ricerca binaria per un bug |
| `git reflog` | Storia di tutti i movimenti di HEAD |


---

### E3 — Glossario Git Completo

**Blob (Binary Large Object)**
Tipo di oggetto Git che rappresenta il contenuto di un file. Il blob non memorizza il nome del file: quello e il compito del tree.

**Branch**
Un puntatore mobile a un commit. Creare un branch significa creare un nuovo puntatore. Il branch avanza automaticamente a ogni nuovo commit.

**Checkout**
Operazione che aggiorna il working directory con il contenuto di un branch, tag, o commit. Con Git moderno, preferire `git switch` per cambiare branch e `git restore` per i file.

**Cherry-pick**
Operazione che applica le modifiche di un singolo commit da un branch a un altro, creando un nuovo commit con lo stesso contenuto ma un hash diverso.

**Clone**
Copia completa di un repository, inclusa tutta la storia, tutti i branch e tutti i tag. Un clone e' un repository a tutti gli effetti.

**Commit**
Snapshot dell'intero progetto in un momento specifico. Ogni commit ha: un hash SHA-1 univoco, un autore, una data, un messaggio, e un puntatore al commit genitore.

**Conflict (Conflitto)**
Situazione in cui Git non puo' fare merge automaticamente di due branch perche' entrambi hanno modificato lo stesso punto di uno stesso file in modi incompatibili.

**DAG (Directed Acyclic Graph)**
La struttura matematica che descrive la storia di Git. Ogni commit punta al suo genitore, formando un grafo diretto senza cicli.

**Detached HEAD**
Stato in cui HEAD punta direttamente a un hash di commit invece che a un branch. I commit fatti in questo stato possono essere persi se ci si sposta altrove.

**Fast-forward**
Tipo di merge possibile quando il branch di destinazione non ha nuovi commit rispetto al momento del branching. Git sposta semplicemente il puntatore avanti, senza creare un merge commit.

**Fetch**
Scarica oggetti e refs dal remote senza modificare il working directory o i branch locali. Sicuro da eseguire in qualsiasi momento.

**Fork**
Copia di un repository nel proprio account GitHub. Usato per contribuire a progetti altrui: si lavora sulla propria copia e si propongono modifiche tramite Pull Request.

**HEAD**
Puntatore speciale che indica "dove sei adesso" nel repository. Normalmente punta a un branch. Se punta direttamente a un hash, sei in "detached HEAD".

**Hook**
Script eseguito automaticamente in risposta a eventi Git specifici (pre-commit, post-merge, pre-push). Usati per automazione, validazione e integrazione.

**Index (Indice)**
Altro nome per la staging area. Il file binario in `.git/index` memorizza lo snapshot preparato per il prossimo commit.

**Merge**
Operazione che unisce la storia di due branch. Puo' essere fast-forward o three-way merge, che crea un merge commit con due genitori.

**Object (Oggetto)**
L'unita' fondamentale di storage in Git. Ci sono quattro tipi: blob, tree, commit, tag. Ogni oggetto e' identificato da un hash SHA-1 del suo contenuto.

**Origin**
Nome convenzionale per il remote principale. Potresti chiamarlo con qualsiasi altro nome.

**Pull**
Combinazione di `fetch` e `merge` (o `rebase` con `--rebase`). Scarica e integra le modifiche dal remote.

**Pull Request (PR)**
Meccanismo GitHub per proporre modifiche da un branch a un altro. Non e' una funzione Git nativa ma di GitHub/GitLab.

**Push**
Carica i commit locali al remote. Fallisce se il remote ha commit che non hai localmente: devi fare `pull` prima.

**Rebase**
Operazione che "riapplica" i commit di un branch sopra un altro punto. Riscrive la storia (i commit ottengono nuovi hash) invece di creare un merge commit.

**Ref**
Puntatore con nome a un oggetto Git (di solito un commit). I branch e i tag sono refs. Vivono in `.git/refs/`.

**Remote**
Un repository Git remoto. Puo' essere su GitHub, GitLab, un server privato, o anche un'altra cartella locale.

**Repository**
La directory `.git/` e tutto il suo contenuto: tutta la storia, tutti gli oggetti, tutta la configurazione.

**SHA-1**
L'algoritmo di hash usato da Git per identificare gli oggetti. Produce un hash di 40 caratteri esadecimali.

**Staging Area**
Area intermedia tra il working directory e il repository. `git add` sposta i file nella staging area; `git commit` crea un commit con il contenuto della staging area.

**Stash**
Meccanismo per salvare temporaneamente le modifiche non committate senza creare un commit. Lo stash e' locale.

**Tag**
Puntatore fisso a un commit, usato per segnare release o milestone. A differenza dei branch, i tag non si spostano.

**Three-way Merge**
Tipo di merge che usa tre snapshot: il commit genitore comune, la punta del branch corrente, e la punta del branch da mergeare.

**Working Directory (Working Tree)**
I tuoi file come li vedi nel filesystem. Git confronta il working directory con la staging area e con il repository.

