---
corso: "Programmazione Python"
modulo: "00"
titolo: "Ambiente e Setup su Windows"
versione: "Python 3.12+ / uv 0.7+ / VS Code 1.90+ / Git 2.45+"
livello: "Prerequisito — da completare prima del Modulo 01"
prerequisiti: []
obiettivi:
  - "Installare Python 3.12+ su Windows con il metodo appropriato al proprio flusso di lavoro"
  - "Configurare l'ambiente PATH in modo corretto e verificarne il funzionamento"
  - "Allestire VS Code come editor Python professionale con estensioni e impostazioni ottimali"
  - "Installare e configurare Git per il version control"
  - "Preparare PowerShell per lo sviluppo Python (Execution Policy, profilo)"
  - "Avviare e verificare una prima sessione interattiva nel REPL"
  - "Adottare una struttura di directory di progetto coerente fin dall'inizio"
tag:
  - setup
  - windows
  - installazione
  - python-org
  - microsoft-store
  - uv
  - PATH
  - vscode
  - pylance
  - git
  - powershell
  - REPL
  - virtual-environment
---

# 00 — Ambiente e Setup su Windows

> **Modulo 00** · **Versione:** Python 3.12+ / uv 0.7+ / VS Code 1.90+ / Git 2.45+ · **Aggiornamento:** 2026-07-15

> ### Obiettivi di apprendimento
>
> Questo è il documento di riferimento per la configurazione dell'ambiente di sviluppo Python su Windows 10 e Windows 11. Deve essere completato **prima** di affrontare qualsiasi altro modulo del corso.
>
> Al termine di questo setup avrai:
> 1. Python 3.12+ installato e raggiungibile da qualsiasi terminale
> 2. `uv` installato come gestore di progetti e ambienti virtuali
> 3. VS Code configurato con le estensioni Python essenziali
> 4. Git installato e configurato con identità e credenziali
> 5. PowerShell pronto a eseguire script e attivare ambienti virtuali
> 6. Un primo progetto Python funzionante come prova di collaudo
>
> **Tempo stimato:** 60-90 minuti per uno studente che parte da zero.
> **Prerequisiti:** Nessuno — questo è il punto di partenza assoluto.

## Idee guida

1. **uv è il metodo raccomandato.** Installa Python, gestisce ambienti virtuali e dipendenze in un solo strumento, è scritto in Rust, e risolve dipendenze 10-100x più veloce di pip.
2. **PATH esplicito e verificato.** Un PATH mal configurato è la causa numero uno di problemi di setup su Windows. Verificare sempre con `where python` e `where uv`.
3. **VS Code con Pylance e Ruff.** Pylance offre inferenza di tipi superiore; Ruff sostituisce flake8, isort e black con un singolo strumento velocissimo.
4. **Execution Policy RemoteSigned.** Su Windows, la policy di PowerShell blocca per default l'attivazione degli ambienti virtuali. Va modificata una volta sola a livello utente.
5. **Una directory di progetto, un ambiente virtuale.** Mai installare dipendenze nel Python di sistema; ogni progetto ha il proprio `.venv` isolato.
6. **Git configurato prima di scrivere codice.** Nome, email e credential manager configurati correttamente fin dall'inizio evitano problemi di autenticazione e di storia dei commit.

---

## Panoramica — Schema del Setup

```
Windows 10/11
│
├── PowerShell 7 (pwsh)
│   ├── Execution Policy: RemoteSigned (utente)
│   └── $PROFILE: alias, attivazione automatica venv
│
├── Python Runtime
│   ├── Metodo A — python.org        (MSI installer)
│   ├── Metodo B — Microsoft Store   (sandbox, limitato)
│   └── Metodo C — uv  ◄── RACCOMANDATO
│       ├── uv python install 3.12
│       └── uv gestisce: venv, pip, lock, build, publish
│
├── Visual Studio Code
│   ├── ms-python.python             (runtime integration)
│   ├── ms-python.vscode-pylance     (type checker, IntelliSense)
│   ├── ms-python.debugpy            (debugger)
│   └── charliermarsh.ruff           (linter + formatter)
│
└── Git for Windows
    ├── git config --global user.name
    ├── git config --global user.email
    └── Git Credential Manager (GCM) — integrato da 2.39+
```

---

## Indice

1. [Cos'è Python](#1-cosè-python)
2. [Metodi di Installazione su Windows](#2-metodi-di-installazione-su-windows)
   - [2.1 Via python.org (Metodo Classico)](#21-via-pythonorg-metodo-classico)
   - [2.2 Via Microsoft Store](#22-via-microsoft-store)
   - [2.3 Via uv (Raccomandato)](#23-via-uv-raccomandato)
   - [2.4 Tabella di Confronto](#24-tabella-di-confronto)
3. [Verifica dell'Installazione](#3-verifica-dellinstallazione)
4. [Configurazione PATH](#4-configurazione-path)
   - [4.1 Come funziona il PATH su Windows](#41-come-funziona-il-path-su-windows)
   - [4.2 Verifica del PATH corrente](#42-verifica-del-path-corrente)
   - [4.3 Aggiunta manuale al PATH](#43-aggiunta-manuale-al-path)
   - [4.4 Problemi Comuni e Risoluzione](#44-problemi-comuni-e-risoluzione)
5. [Editor: Visual Studio Code](#5-editor-visual-studio-code)
   - [5.1 Installazione VS Code](#51-installazione-vs-code)
   - [5.2 Estensioni Python Essenziali](#52-estensioni-python-essenziali)
   - [5.3 Configurazione settings.json](#53-configurazione-settingsjson)
   - [5.4 Selezione dell'Interprete](#54-selezione-dellinterprete)
   - [5.5 Configurazione del Debugger](#55-configurazione-del-debugger)
6. [Git su Windows](#6-git-su-windows)
   - [6.1 Installazione](#61-installazione)
   - [6.2 Configurazione Iniziale](#62-configurazione-iniziale)
   - [6.3 Configurazione SSH (opzionale ma consigliato)](#63-configurazione-ssh-opzionale-ma-consigliato)
   - [6.4 File .gitignore Globale per Python](#64-file-gitignore-globale-per-python)
7. [PowerShell per Sviluppo Python](#7-powershell-per-sviluppo-python)
   - [7.1 PowerShell 7 vs Windows PowerShell 5.1](#71-powershell-7-vs-windows-powershell-51)
   - [7.2 Execution Policy](#72-execution-policy)
   - [7.3 Profilo PowerShell](#73-profilo-powershell)
   - [7.4 Windows Terminal (Raccomandato)](#74-windows-terminal-raccomandato)
8. [Prima Sessione Interattiva (REPL)](#8-prima-sessione-interattiva-repl)
   - [8.1 Il REPL Standard](#81-il-repl-standard)
   - [8.2 Comandi di Diagnostica nel REPL](#82-comandi-di-diagnostica-nel-repl)
   - [8.3 Uso Pratico del REPL per l'Apprendimento](#83-uso-pratico-del-repl-per-lapprendimento)
   - [8.5 IPython come REPL Avanzato](#85-ipython-come-repl-avanzato)
9. [Struttura delle Directory di Progetto](#9-struttura-delle-directory-di-progetto)
   - [9.1 Script Singolo](#91-script-singolo)
   - [9.2 Progetto con Libreria](#92-progetto-con-libreria)
   - [9.3 Applicazione Flask/FastAPI](#93-applicazione-flaskfastapi)
   - [9.4 Convenzioni di Naming](#94-convenzioni-di-naming)
10. [Checklist Verifica Setup](#10-checklist-verifica-setup)
11. [Troubleshooting — Problemi Frequenti](#11-troubleshooting--problemi-frequenti)
12. [WSL2 — Windows Subsystem for Linux](#12-wsl2--windows-subsystem-for-linux-alternativa-avanzata)
13. [Riferimenti](#13-riferimenti)

---

## 1. Cos'è Python

Python è un linguaggio di programmazione interpretato, ad alto livello e general-purpose, creato da Guido van Rossum e rilasciato per la prima volta nel 1991. La sua filosofia di design, sintetizzata nello *Zen of Python* (`import this` nel REPL), privilegia la leggibilità del codice e la produttività del programmatore rispetto alle prestazioni grezze.

### Perché Python su Windows richiede attenzione

A differenza di sistemi Linux e macOS — dove Python è spesso preinstallato a livello di sistema — su Windows l'installazione di Python richiede scelte consapevoli. Le decisioni prese in questa fase condizionano l'intero flusso di lavoro:

- **Quale interprete usare:** Windows non include Python. Esistono almeno tre percorsi di installazione, ognuno con implicazioni diverse su PATH, permessi e compatibilità.
- **Gestione degli ambienti virtuali:** L'Execution Policy di PowerShell può bloccare l'attivazione dei virtual environment se non viene configurata correttamente.
- **Versioni multiple:** Può essere necessario mantenere più versioni di Python in parallelo (es. 3.11 per un progetto legacy, 3.12 per uno nuovo). `uv` gestisce questo scenario nativamente.

### Versione Raccomandata

Questo corso richiede **Python 3.12 o superiore**. Le funzionalità trattate includono:

| Versione | Novità rilevanti per il corso |
|----------|-------------------------------|
| 3.10 | `match`/`case` (Structural Pattern Matching), `X \| Y` nei type hint |
| 3.11 | `ExceptionGroup`, `except*`, miglioramenti prestazioni (~25% più veloce) |
| 3.12 | `type` statement per alias, generics semplificati, `@override`, `**kwargs` tipizzati |
| 3.13 | Free-threading sperimentale (GIL opzionale), JIT sperimentale |

> **Consiglio:** Installa Python 3.12.x per massima stabilità. Python 3.13 è supportato ma alcune librerie di terze parti potrebbero non aver ancora completato la migrazione.

---

## 2. Metodi di Installazione su Windows

Esistono tre percorsi principali per installare Python su Windows. Il metodo corretto dipende dal contesto: sviluppo professionale, ambienti aziendali con restrizioni, o uso occasionale. La sezione [2.4 Tabella di Confronto](#24-tabella-di-confronto) riassume i trade-off.

---

### 2.1 Via python.org (Metodo Classico)

Il metodo tradizionale prevede il download del programma di installazione ufficiale da [python.org](https://www.python.org/downloads/). È il percorso più documentato e adatto a chi preferisce il controllo diretto.

#### Procedura

**Passaggio 1 — Download dell'installer**

Accedi a [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/) e scarica la versione più recente della serie 3.12.x. Scegli il file `Windows installer (64-bit)` (formato `.exe`).

**Passaggio 2 — Avvio dell'installer**

Avvia il file scaricato **come amministratore** (tasto destro → "Esegui come amministratore"). Questo garantisce che Python venga installato per tutti gli utenti del sistema.

> **Importante:** nella prima schermata dell'installer, spunta **obbligatoriamente** la casella **"Add Python to PATH"** prima di procedere. Se dimentichi questo passaggio, dovrai configurare il PATH manualmente (vedi [Sezione 4](#4-configurazione-path)).

**Passaggio 3 — Personalizza l'installazione**

Clicca su "Customize installation" invece di "Install Now" per avere il controllo completo:

- **Optional Features:** mantieni tutte le opzioni selezionate (pip, tcl/tk, test suite, py launcher).
- **Advanced Options:**
  - Spunta "Install for all users" (richiede privilegi amministratore).
  - Spunta "Add Python to environment variables".
  - Nota il percorso di installazione (`C:\Program Files\Python312\`) — sarà utile in seguito.

**Passaggio 4 — Verifica**

Apri una nuova finestra di PowerShell (è necessario aprirne una nuova per aggiornare il PATH) e digita:

```powershell
python --version
```

L'output atteso è simile a `Python 3.12.7`.

#### Note sull'Installer python.org

- L'installer include **pip** (il gestore di pacchetti standard) e **IDLE** (un editor minimale integrato, sconsigliato per uso professionale).
- Il **Python Launcher for Windows** (`py.exe`) viene installato automaticamente. Permette di selezionare la versione desiderata con la sintassi `py -3.12 script.py`.
- Per aggiornare Python a una versione successiva, è sufficiente eseguire il nuovo installer che sovrascriverà quello precedente.

---

### 2.2 Via Microsoft Store

Microsoft Store offre un pacchetto Python mantenuto dalla Python Software Foundation. L'installazione è rapida e non richiede privilegi amministratore.

#### Procedura

```powershell
# Oppure aprire Microsoft Store e cercare "Python 3.12"
winget install --id=Python.Python.3.12 -e
```

Alternativamente, digita `python` o `python3` in PowerShell: se Python non è installato, Windows 10/11 mostra automaticamente una finestra del Microsoft Store con la versione disponibile.

#### Limitazioni Significative

Il pacchetto Microsoft Store ha alcune restrizioni che lo rendono **inadatto allo sviluppo professionale**:

| Limitazione | Impatto pratico |
|-------------|-----------------|
| Installato in una sandbox utente (AppData) | Percorsi non standard, difficoltà con strumenti che cercano Python in `C:\` |
| Aggiornamenti automatici del sistema operativo | Una versione patch potrebbe cambiare senza preavviso |
| Alcuni moduli C non funzionano correttamente | Problemi con `ctypes`, alcuni driver di database |
| pip install potrebbe richiedere `--user` | Conflitti con ambienti virtuali |

**Quando usarlo:** Prototipazione rapida, ambienti scolastici senza accesso amministratore, utenti non tecnici che vogliono solo eseguire uno script Python.

**Quando evitarlo:** Sviluppo professionale, lavoro con librerie native (NumPy, cryptography), ambienti CI/CD.

---

### 2.3 Via uv (Raccomandato)

`uv` è un gestore di progetti Python scritto in Rust, sviluppato da [Astral](https://astral.sh/) (gli stessi autori di `ruff`). È il metodo **raccomandato da questo corso** perché:

- Installa e gestisce più versioni di Python in parallelo.
- Sostituisce `pip`, `pip-tools`, `virtualenv`, `poetry` e `pyenv` con un unico strumento.
- Risolve le dipendenze 10-100x più velocemente di pip grazie all'implementazione in Rust.
- Genera e rispetta lock file riproducibili (`uv.lock`).
- Funziona correttamente anche senza un Python preinstallato sul sistema.

> `uv` è trattato in modo approfondito nel **Modulo 24 — Virtual Environments e Gestione Dipendenze**. Qui ne vediamo l'installazione e l'uso base.

#### Passaggio 1 — Installazione di uv

**Metodo A — PowerShell (consigliato, non richiede Python preinstallato):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Questo script scarica il binario `uv.exe` e lo aggiunge al PATH dell'utente corrente (`%USERPROFILE%\.local\bin`).

**Metodo B — winget (se disponibile su Windows 11 o aggiornato):**

```powershell
winget install --id astral-sh.uv -e
```

**Metodo C — se pip è già disponibile:**

```powershell
pip install uv
```

> Questo metodo installa uv come pacchetto Python nel sistema, ma è meno portabile del Metodo A.

**Verifica dell'installazione di uv:**

```powershell
uv --version
# Output atteso: uv 0.7.x (o superiore)
```

#### Passaggio 2 — Installazione di Python tramite uv

Con `uv` installato, è possibile installare Python senza visitare python.org:

```powershell
# Installa la versione più recente di Python 3.12
uv python install 3.12

# Oppure specifica una versione patch esatta
uv python install 3.12.7

# Elenca le versioni disponibili per l'installazione
uv python list

# Elenca le versioni installate sul sistema
uv python list --only-installed
```

Python viene installato in `%USERPROFILE%\.local\share\uv\python\` — una directory gestita interamente da `uv`, che non interferisce con eventuali installazioni python.org.

#### Passaggio 3 — Verifica

```powershell
uv run python --version
# Output: Python 3.12.7

# uv run avvia Python nell'ambiente gestito da uv
# senza dover attivare manualmente un venv
uv run python -c "import sys; print(sys.executable)"
```

#### Aggiornare uv

```powershell
uv self update
```

#### Comandi uv Essenziali per il Lavoro Quotidiano

Questa tabella riassume i comandi `uv` che userai ogni giorno. Una versione approfondita di ciascuno è nel Modulo 24.

| Comando | Descrizione |
|---------|-------------|
| `uv python install 3.12` | Installa Python 3.12 (gestito da uv) |
| `uv python list` | Elenca le versioni Python disponibili e installate |
| `uv init nome-progetto` | Crea un nuovo progetto con struttura standard |
| `uv venv` | Crea un ambiente virtuale `.venv` nella directory corrente |
| `uv add requests` | Aggiunge una dipendenza al progetto |
| `uv add --dev pytest ruff` | Aggiunge dipendenze di sviluppo |
| `uv remove requests` | Rimuove una dipendenza |
| `uv sync` | Sincronizza il venv con il lock file |
| `uv lock` | Aggiorna il file `uv.lock` |
| `uv run python script.py` | Esegue lo script nel venv del progetto |
| `uv run pytest` | Esegue pytest nel venv del progetto |
| `uv pip install requests` | Installa nel venv attivo (compatibilità pip) |
| `uv pip list` | Lista i pacchetti installati nel venv |
| `uv tool install ruff` | Installa un tool globale (non in un progetto) |
| `uv tool run black script.py` | Esegue un tool senza installarlo permanentemente |
| `uv self update` | Aggiorna uv stesso all'ultima versione |

#### uv e pyproject.toml

Quando esegui `uv init` o `uv add`, il file `pyproject.toml` viene creato e mantenuto automaticamente. Ecco un esempio tipico generato da uv:

```toml
[project]
name = "mio-progetto"
version = "0.1.0"
description = "Descrizione breve del progetto"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.32.0",
    "pydantic>=2.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.5.0",
    "mypy>=1.10.0",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

> Il file `pyproject.toml` è il punto di verità unico per la configurazione di un progetto Python moderno: sostituisce `setup.py`, `setup.cfg`, `requirements.txt`, `.flake8`, `mypy.ini` e altri file di configurazione separati. È definito dalla PEP 518 e ampliato dalle PEP 517 e 621.

#### Flusso di Lavoro Tipico con uv

```powershell
# --- Giorno 1: creazione progetto ---
uv init mio-progetto --python 3.12
cd mio-progetto
uv add fastapi uvicorn[standard]
uv add --dev pytest httpx ruff mypy

# --- Ogni giorno: avvio del lavoro ---
# Con uv non è necessario attivare il venv per eseguire il codice:
uv run python -m mio_progetto
uv run uvicorn mio_progetto.main:app --reload
uv run pytest

# Oppure attiva il venv per una sessione interattiva:
.\.venv\Scripts\Activate.ps1
python  # → REPL nel venv
ruff check .
mypy .
deactivate

# --- Dopo aver modificato le dipendenze ---
uv lock          # aggiorna uv.lock
uv sync          # aggiorna il venv per allinearlo al lock file

# --- Onboarding di un collega su un progetto esistente ---
git clone https://github.com/org/mio-progetto.git
cd mio-progetto
uv sync          # installa esattamente le versioni nel lock file
uv run pytest    # verifica che tutto funzioni
```

---

### 2.4 Tabella di Confronto

| Criterio | python.org | Microsoft Store | uv |
|----------|-----------|----------------|----|
| Privilegi richiesti | Amministratore (consigliato) | Nessuno | Nessuno |
| PATH configurato automaticamente | Sì (se spuntato) | Sì | Sì (directory utente) |
| Versioni multiple in parallelo | No (richiede pyenv) | No | Sì, nativo |
| Gestione ambienti virtuali | Solo con venv/pip | Solo con venv/pip | Integrata |
| Gestione dipendenze con lock file | No (richiede pip-tools) | No | Sì (uv.lock) |
| Aggiornamenti controllati | Manuali | Automatici del SO | `uv self update` |
| Librerie native (C extensions) | Completo | Limitato | Completo |
| Adatto a CI/CD | Sì | No | Sì (eccellente) |
| Consigliato per questo corso | Alternativa valida | No | **Sì** |

---

## 3. Verifica dell'Installazione

Dopo aver completato l'installazione (con qualsiasi metodo), apri una nuova finestra di PowerShell ed esegui le seguenti verifiche.

### Verifica 1 — Versione di Python

```powershell
python --version
# Atteso: Python 3.12.x

# Su alcuni sistemi, potrebbe essere necessario usare python3
python3 --version
```

Se il comando non viene riconosciuto, il PATH non è configurato correttamente. Vai alla [Sezione 4](#4-configurazione-path).

### Verifica 2 — Percorso dell'Eseguibile

```powershell
where.exe python
# Esempio output (python.org):  C:\Program Files\Python312\python.exe
# Esempio output (uv):          C:\Users\<utente>\.local\share\uv\python\cpython-3.12.7-windows-x86_64-none\python.exe
# Esempio output (Store):       C:\Users\<utente>\AppData\Local\Microsoft\WindowsApps\python.exe
```

> **Attenzione:** `where.exe python` potrebbe restituire più righe se esistono installazioni multiple. La prima riga indica quale Python viene eseguito quando digiti `python`. Se l'ordine non è quello desiderato, consulta la [Sezione 4.3](#43-aggiunta-manuale-al-path).

### Verifica 3 — pip

```powershell
python -m pip --version
# Atteso: pip 24.x from C:\...\site-packages\pip (python 3.12)
```

> Con `uv`, pip è disponibile ma raramente necessario: usa `uv pip install` invece.

### Verifica 4 — Moduli della Libreria Standard

```powershell
python -c "import sys, os, pathlib, json, re; print('Libreria standard: OK')"
# Atteso: Libreria standard: OK
```

### Verifica 5 — Creazione di un Ambiente Virtuale

```powershell
# Crea un ambiente virtuale di test
python -m venv C:\Temp\test-venv

# Attiva l'ambiente (PowerShell)
C:\Temp\test-venv\Scripts\Activate.ps1

# Verifica che il prompt cambi: (test-venv) PS C:\...>
python --version

# Disattiva
deactivate

# Pulizia
Remove-Item -Recurse -Force C:\Temp\test-venv
```

Se l'attivazione fallisce con un errore di Execution Policy, vai alla [Sezione 7.2](#72-execution-policy).

---

## 4. Configurazione PATH

### 4.1 Come funziona il PATH su Windows

Il **PATH** è una variabile d'ambiente che elenca le directory in cui Windows cerca gli eseguibili quando digiti un comando nel terminale. Quando scrivi `python`, il sistema scorre le directory nel PATH nell'ordine in cui sono elencate e usa il primo `python.exe` che trova.

Su Windows esistono due livelli di PATH:
- **PATH di Sistema** (valido per tutti gli utenti): richiede privilegi amministratore per essere modificato.
- **PATH dell'Utente** (valido solo per l'utente corrente): non richiede privilegi amministratore.

Il PATH finale effettivo è la concatenazione di `PATH Utente + PATH Sistema`. Le directory del PATH Utente hanno **priorità più alta** (vengono cercate prima) rispetto a quelle di Sistema.

### 4.2 Verifica del PATH corrente

```powershell
# Mostra il PATH utente formattato (una directory per riga)
$env:PATH -split ';' | Where-Object { $_ -like '*python*' -or $_ -like '*uv*' -or $_ -like '*Python*' }

# Mostra tutte le directory del PATH (per debugging completo)
$env:PATH -split ';' | ForEach-Object { $_ }

# Verifica quale python e quale uv vengono trovati per primi
where.exe python
where.exe uv
where.exe pip
```

### 4.3 Aggiunta manuale al PATH

Ci sono tre metodi per aggiungere una directory al PATH su Windows.

#### Metodo A — Interfaccia Grafica (Pannello di Controllo)

1. Premi `Win + R`, digita `sysdm.cpl`, premi Invio.
2. Clicca sulla scheda **"Avanzate"**.
3. Clicca sul pulsante **"Variabili d'ambiente..."**.
4. Nella sezione **"Variabili utente"** (non Variabili di sistema), fai doppio clic su `Path`.
5. Clicca **"Nuovo"** e inserisci il percorso desiderato (es. `C:\Program Files\Python312\`).
6. Clicca OK su tutte le finestre.
7. Apri una nuova finestra di PowerShell per applicare le modifiche.

> Aggiungi sempre le directory nell'ordine corretto. Le voci più in alto hanno priorità più alta.

#### Metodo B — PowerShell (permanente, solo utente corrente)

```powershell
# Aggiunge una directory al PATH utente in modo permanente
$pythonPath = "C:\Program Files\Python312\"
$scriptPath = "C:\Program Files\Python312\Scripts\"

$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")

# Controlla che non sia già presente
if ($currentPath -notlike "*$pythonPath*") {
    [Environment]::SetEnvironmentVariable(
        "PATH",
        "$pythonPath;$scriptPath;$currentPath",
        "User"
    )
    Write-Host "PATH aggiornato. Apri una nuova finestra PowerShell."
} else {
    Write-Host "Il percorso è già nel PATH."
}
```

#### Metodo C — uv gestisce il PATH automaticamente

Con `uv`, il PATH viene gestito automaticamente durante l'installazione. Il comando `uv python install` configura il PATH dell'utente senza richiedere intervento manuale.

```powershell
# Se uv è installato ma non trovato nel PATH della sessione corrente
# (accade raramente dopo la prima installazione), riavvia il terminale.

# Per forzare il ricaricamento del PATH nella sessione corrente:
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("PATH", "User")
```

### 4.4 Problemi Comuni e Risoluzione

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `python` non trovato dopo l'installazione | Terminale aperto prima dell'aggiunta al PATH | Aprire una nuova finestra del terminale |
| `python` punta alla versione sbagliata | Più installazioni con ordine errato nel PATH | Spostare la directory corretta all'inizio del PATH |
| `pip` non trovato | `Scripts\` non nel PATH | Aggiungere `C:\Program Files\Python312\Scripts\` al PATH |
| `where python` mostra lo stub di Windows | Python Launcher senza Python reale installato | Installare Python reale o disabilitare lo stub (`%USERPROFILE%\AppData\Local\Microsoft\WindowsApps`) |
| Errore `permission denied` su pip install | pip nel Python di sistema, nessun venv attivo | Usare sempre ambienti virtuali o `uv pip install` |

#### Disabilitare gli stub Python di Windows

Windows 10/11 include degli stub (`python.exe`, `python3.exe`) nella directory `%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\` che reindirizzano al Microsoft Store. Se hai installato Python tramite python.org o uv, questi stub potrebbero causare conflitti.

Per disabilitarli:
1. Apri **Impostazioni** → **App** → **App e funzionalità**.
2. Clicca su **"Alias di esecuzione app"**.
3. Disabilita i toggle per `python.exe` e `python3.exe`.

---

## 5. Editor: Visual Studio Code

Visual Studio Code è l'editor raccomandato per questo corso. È gratuito, open-source, multipiattaforma, e il suo ecosistema di estensioni per Python è il più maturo disponibile.

> **Alternativa:** PyCharm Professional (a pagamento) offre funzionalità simili con una maggiore integrazione out-of-the-box. PyCharm Community è gratuito ma più limitato. VS Code con le estensioni corrette è competitivo con PyCharm Professional in quasi tutti gli scenari.

### 5.1 Installazione VS Code

**Metodo consigliato — winget:**

```powershell
winget install -e --id Microsoft.VisualStudioCode
```

**Metodo manuale:** Scarica l'installer da [https://code.visualstudio.com/](https://code.visualstudio.com/).

Scegli il **"System Installer"** (non "User Installer") se hai privilegi amministratore: installa VS Code per tutti gli utenti e integra il comando `code` nel PATH di sistema.

#### Verifica dell'installazione

```powershell
code --version
# Output simile a: 1.90.x
#                  commit-hash
#                  x64
```

> Se il comando `code` non viene trovato, chiudi e riapri il terminale. Se il problema persiste, aggiungi `C:\Users\<utente>\AppData\Local\Programs\Microsoft VS Code\bin\` al PATH utente.

### 5.2 Estensioni Python Essenziali

#### Installazione via riga di comando (metodo più rapido)

```powershell
# Estensioni obbligatorie
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension charliermarsh.ruff

# Estensioni fortemente consigliate
code --install-extension tamasfe.even-better-toml
code --install-extension redhat.vscode-yaml
code --install-extension ms-toolsai.jupyter

# Estensioni opzionali ma utili
code --install-extension eamodio.gitlens
code --install-extension mhutchie.git-graph
code --install-extension ms-azuretools.vscode-docker
```

#### Descrizione delle Estensioni

| ID Estensione | Nome | Funzione |
|---------------|------|----------|
| `ms-python.python` | Python | Integrazione runtime Python: selezione interprete, esecuzione, testing, REPL integrato |
| `ms-python.vscode-pylance` | Pylance | Language server avanzato: IntelliSense, inferenza di tipi, navigazione codice, import automatici |
| `ms-python.debugpy` | Python Debugger | Debug con breakpoint, watch, call stack, variabili locali; sostituisce il vecchio debugger integrato |
| `charliermarsh.ruff` | Ruff | Linter + formatter ultraveloce (Rust): sostituisce flake8, isort, black con un singolo strumento |
| `tamasfe.even-better-toml` | Even Better TOML | Syntax highlighting, validazione e autocompletamento per `pyproject.toml` |
| `redhat.vscode-yaml` | YAML | Supporto YAML con schema validation (utile per CI/CD, Docker Compose) |
| `ms-toolsai.jupyter` | Jupyter | Notebook Jupyter integrati nell'editor |

#### Perché Pylance e non il checker di tipo di base

L'estensione `ms-python.python` include un language server di base (Jedi). Pylance è un language server separato sviluppato da Microsoft che offre:

- Inferenza di tipi molto più precisa, basata su **Pyright** (il type checker statico di Microsoft).
- **Auto-import** automatico suggerisce e aggiunge `import` mancanti.
- Navigazione tra simboli (`Go to Definition`, `Find All References`) molto più accurata.
- Supporto completo per i **Protocol** e i **TypeVar** di Python 3.12.
- **Inlay hints**: mostra i tipi inferiti direttamente nel codice senza annotarli manualmente.

### 5.3 Configurazione settings.json

Apri le impostazioni di VS Code con `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)" e inserisci la seguente configurazione:

```json
{
    // --- Python ---
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,

    // --- Pylance ---
    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.inlayHints.variableTypes": true,
    "python.analysis.inlayHints.functionReturnTypes": true,
    "python.analysis.inlayHints.parameterNames": "All",
    "python.analysis.inlayHints.parameterTypes": true,
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.autoFormatStrings": true,

    // --- Ruff (linter + formatter) ---
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "ruff.lint.enable": true,
    "ruff.organizeImports": true,

    // --- Editor generale ---
    "editor.rulers": [88],
    "editor.renderWhitespace": "trailing",
    "editor.suggestSelection": "first",
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.trimAutoWhitespace": true,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.trimFinalNewlines": true,

    // --- Terminale ---
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "terminal.integrated.shellIntegration.enabled": true,

    // --- File Explorer ---
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.ruff_cache": true,
        "**/.mypy_cache": true
    }
}
```

> **Nota sul formatter:** `"editor.rulers": [88]` mostra una linea guida verticale a colonna 88, che è il limite di lunghezza riga predefinito di `ruff` (compatibile con `black`). PEP 8 raccomanda 79 caratteri, ma 88-100 è la norma nei progetti moderni.

### 5.4 Selezione dell'Interprete

VS Code deve sapere quale Python usare per IntelliSense, il type checker e l'esecuzione. La selezione dell'interprete è **per workspace** (per cartella di progetto), non globale.

**Metodo 1 — Tramite Command Palette:**
1. Apri la cartella di progetto con VS Code (`File` → `Open Folder`).
2. Premi `Ctrl+Shift+P` → digita "Python: Select Interpreter".
3. Seleziona il Python del virtual environment del progetto (cercato automaticamente in `.venv`).

**Metodo 2 — Creazione del venv con uv (automatico):**

```powershell
# Dalla cartella del progetto
uv init
uv venv
# VS Code rileva automaticamente il .venv nella cartella del progetto
```

**Metodo 3 — File .python-version:**

`uv` (e `pyenv`) riconoscono un file `.python-version` nella root del progetto che specifica la versione Python da usare:

```powershell
# Crea il file .python-version
"3.12" | Out-File -Encoding utf8 .python-version
```

### 5.5 Scorciatoie da Tastiera Essenziali per Python in VS Code

Queste sono le scorciatoie più usate nel lavoro quotidiano con VS Code su Python. Su Windows, `Ctrl` corrisponde alla combinazione principale.

| Azione | Scorciatoia Windows |
|--------|---------------------|
| Command Palette | `Ctrl+Shift+P` |
| Selezione interprete Python | `Ctrl+Shift+P` → "Python: Select Interpreter" |
| Esegui file Python corrente | `Ctrl+F5` (senza debug) / `F5` (con debug) |
| Apri terminale integrato | `` Ctrl+` `` |
| Vai alla definizione | `F12` |
| Vai ai riferimenti | `Shift+F12` |
| Rinomina simbolo (refactoring) | `F2` |
| Formatta documento (Ruff) | `Shift+Alt+F` |
| Organizza import (Ruff) | `Shift+Alt+O` |
| Mostra problemi di tipo (Pylance) | `Ctrl+Shift+M` |
| Quick fix / auto-import | `Ctrl+.` |
| Commenta/decommenta riga | `Ctrl+/` |
| Duplica riga | `Shift+Alt+↓` |
| Sposta riga su/giù | `Alt+↑` / `Alt+↓` |
| Cerca nel file corrente | `Ctrl+F` |
| Cerca in tutti i file | `Ctrl+Shift+F` |
| Sostituisci nel file corrente | `Ctrl+H` |
| Apri file per nome | `Ctrl+P` |
| Cursori multipli | `Alt+Click` |
| Seleziona occorrenza successiva | `Ctrl+D` |
| Seleziona tutte le occorrenze | `Ctrl+Shift+L` |
| Vai alla riga N | `Ctrl+G` |
| Split editor | `Ctrl+\` |
| Toggle esplora file | `Ctrl+Shift+E` |
| Toggle test explorer | `Ctrl+Shift+T` (con estensione Python) |
| Apri REPL Python integrato | `Ctrl+Shift+P` → "Python: Start REPL" |

### 5.7 Configurazione del Debugger

Il file `launch.json` configura le sessioni di debug. VS Code lo crea automaticamente la prima volta che premi `F5`.

Crea il file `.vscode/launch.json` nella cartella del progetto con questa configurazione base:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: File corrente",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: Modulo (uv run)",
            "type": "debugpy",
            "request": "launch",
            "module": "${workspaceFolderBasename}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "FastAPI: uvicorn",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload", "--port", "8000"],
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

---

## 6. Git su Windows

Git è il sistema di controllo di versione standard per lo sviluppo software. Anche per il lavoro individuale, l'uso di Git è considerato una pratica professionale fondamentale: permette di tornare a versioni precedenti del codice, sperimentare in branch separati, e condividere il lavoro su piattaforme come GitHub o GitLab.

### 6.1 Installazione

**Metodo consigliato — winget:**

```powershell
winget install -e --id Git.Git
```

**Metodo manuale:** Scarica l'installer da [https://git-scm.com/download/win](https://git-scm.com/download/win).

#### Opzioni Chiave dell'Installer

L'installer di Git per Windows presenta molte schermate. Ecco le scelte consigliate per un setup professionale:

| Schermata | Opzione consigliata | Nota |
|-----------|--------------------|----|
| Default editor | Visual Studio Code | Cambia l'editor predefinito per i messaggi di commit |
| Initial branch name | `main` | Allineato con la convenzione GitHub/GitLab moderna |
| PATH environment | "Git from the command line and 3rd-party software" | Rende `git` disponibile in PowerShell e CMD |
| SSH executable | "Use bundled OpenSSH" | OpenSSH integrato, più semplice da gestire |
| HTTPS transport backend | "Use the OpenSSL library" | Standard per la maggior parte degli ambienti |
| Line ending conversion | "Checkout Windows-style, commit Unix-style (CRLF→LF)" | Evita problemi di CRLF nei repository condivisi con Linux/macOS |
| Terminal emulator | "Use Windows' default console window" | Compatibile con Windows Terminal |
| Credential helper | "Git Credential Manager" | Integrato da Git 2.39+, gestisce autenticazione GitHub/GitLab |

**Verifica:**

```powershell
git --version
# Output atteso: git version 2.45.x.windows.1
```

### 6.2 Configurazione Iniziale

La configurazione globale di Git è memorizzata in `%USERPROFILE%\.gitconfig`. Va eseguita **una volta sola** per macchina, non per progetto.

```powershell
# Identità (obbligatorio — appare nei commit)
git config --global user.name "Nome Cognome"
git config --global user.email "tua-email@esempio.com"

# Editor per i messaggi di commit
git config --global core.editor "code --wait"

# Branch predefinito per i nuovi repository
git config --global init.defaultBranch main

# Gestione dei fine riga (CRLF → LF al commit, LF al checkout su Windows)
git config --global core.autocrlf true

# Mostra i diff in modo più leggibile
git config --global core.pager "less -FX"

# Pull rebase di default (evita merge commit non necessari)
git config --global pull.rebase true

# Push solo il branch corrente (più sicuro)
git config --global push.default current

# Abilita i colori nell'output
git config --global color.ui auto

# Verifica la configurazione
git config --global --list
```

> **Note sull'email:** Se usi GitHub, puoi usare l'email privata fornita da GitHub (`<id>+<username>@users.noreply.github.com`) per non esporre la tua email reale nei commit pubblici. Trovala in Settings → Emails → "Keep my email address private".

### 6.3 Flusso di Lavoro Git Essenziale per i Progetti del Corso

Questo non è un corso Git, ma ogni modulo prevede l'uso del version control. Ecco i comandi minimi necessari.

#### Inizializzare un Nuovo Repository

```powershell
# Dalla directory del progetto
git init
git add .
git commit -m "feat: struttura iniziale del progetto"
```

#### Ciclo di Vita di una Modifica

```powershell
# 1. Verifica cosa è cambiato
git status
git diff              # mostra le modifiche non ancora staged

# 2. Aggiungi i file modificati all'area di staging
git add src/mio_progetto/models.py   # file specifico
git add src/                          # intera directory
git add -p                            # interattivo: scegli le modifiche da staging

# 3. Verifica cosa verrà committato
git diff --cached

# 4. Crea il commit
git commit -m "feat(models): aggiunge validazione campo email"

# 5. Annulla l'ultimo commit (mantiene le modifiche nel working tree)
git reset HEAD~1
```

#### Convenzione per i Messaggi di Commit

Questo corso adotta [Conventional Commits](https://www.conventionalcommits.org/):

```
tipo(scope): descrizione breve in imperative mood

Corpo opzionale: spiega il "perché", non il "cosa".
Il "cosa" è già nel diff.
```

| Tipo | Uso |
|------|-----|
| `feat` | Nuova funzionalità |
| `fix` | Correzione di un bug |
| `refactor` | Refactoring senza cambiamento di comportamento |
| `test` | Aggiunta o modifica di test |
| `docs` | Solo documentazione |
| `chore` | Manutenzione (aggiornamento dipendenze, CI, ecc.) |
| `perf` | Ottimizzazione delle prestazioni |
| `style` | Formattazione, spazi (senza cambio logico) |

#### Lavorare con Branch

```powershell
# Crea e passa a un nuovo branch
git checkout -b feature/aggiunge-autenticazione
# oppure (Git 2.23+):
git switch -c feature/aggiunge-autenticazione

# Lista tutti i branch
git branch -a

# Torna al branch principale
git switch main

# Unisci il branch nel main (dopo review)
git switch main
git merge --no-ff feature/aggiunge-autenticazione -m "feat: aggiunge autenticazione JWT"

# Cancella il branch locale
git branch -d feature/aggiunge-autenticazione
```

#### Storia e Navigazione

```powershell
# Mostra la storia dei commit (formato compatto)
git log --oneline --graph --decorate --all

# Mostra le modifiche di un commit specifico
git show <hash>

# Cerca un commit per messaggio
git log --oneline --grep="autenticazione"

# Cerca chi ha modificato una riga specifica
git blame src/mio_progetto/auth.py

# Torna a un commit precedente (per ispezione, senza modificare il branch)
git checkout <hash>
git checkout -          # torna al branch precedente
```

#### Annullare Errori Comuni

```powershell
# Annulla modifiche non staged (ATTENZIONE: irreversibile)
git restore src/mio_progetto/models.py

# Annulla staging di un file
git restore --staged src/mio_progetto/models.py

# Annulla l'ultimo commit mantenendo le modifiche (sicuro)
git reset HEAD~1

# Crea un commit di annullamento (per commit già pushati)
git revert HEAD
```

> **Regola d'oro:** Non usare mai `git reset --hard` o `git push --force` su branch condivisi. Queste operazioni riscrivono la storia e causano problemi ai collaboratori.

### 6.5 Configurazione SSH (opzionale ma consigliato)

L'autenticazione SSH è più sicura e comoda dell'autenticazione HTTPS per operazioni frequenti su GitHub/GitLab.

**Generazione della chiave SSH:**

```powershell
# Genera una nuova coppia di chiavi SSH (ed25519 è il formato moderno raccomandato)
ssh-keygen -t ed25519 -C "tua-email@esempio.com" -f "$HOME\.ssh\id_ed25519"

# Quando chiede la passphrase, inseriscine una robusta (non lasciare vuota)
```

**Avvio dell'SSH Agent:**

```powershell
# Avvia il servizio ssh-agent (da eseguire una volta come amministratore)
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent

# Aggiungi la chiave all'agente
ssh-add "$HOME\.ssh\id_ed25519"
```

**Copia la chiave pubblica:**

```powershell
Get-Content "$HOME\.ssh\id_ed25519.pub" | Set-Clipboard
```

Vai su GitHub → Settings → SSH and GPG keys → New SSH key, e incolla la chiave.

**Verifica la connessione:**

```powershell
ssh -T git@github.com
# Output atteso: Hi <username>! You've successfully authenticated...
```

### 6.6 File .gitignore Globale per Python

Un file `.gitignore` globale evita di includere accidentalmente file temporanei di Python in qualsiasi repository.

```powershell
# Crea il file
New-Item -ItemType File -Path "$HOME\.gitignore_global" -Force

# Configura Git per usarlo
git config --global core.excludesfile "$HOME\.gitignore_global"
```

Contenuto del file `~/.gitignore_global`:

```gitignore
# === Python ===
__pycache__/
*.py[cod]
*$py.class
*.pyo
*.pyd

# Distribuzione e packaging
.Python
build/
dist/
eggs/
*.egg-info/
*.egg
wheels/

# Ambienti virtuali
.venv/
venv/
ENV/
env.bak/
.env

# uv
.uv/
uv.lock

# Type checkers
.mypy_cache/
.pyright/
.dmypy.json

# Linter e formatter
.ruff_cache/

# Test e coverage
.pytest_cache/
.coverage
htmlcov/
.tox/
coverage.xml

# Jupyter
.ipynb_checkpoints/

# === Editor ===
.vscode/settings.json
.idea/
*.iml
*.sublime-project
*.sublime-workspace
*~
*.swp
*.swo

# === Sistema ===
.DS_Store
Thumbs.db
desktop.ini
*.lnk
```

> **Nota:** Non aggiungere `.vscode/launch.json` al `.gitignore` globale — è utile condividerlo nel repository del progetto. Aggiungi invece `.vscode/settings.json` (contiene percorsi locali specifici della macchina).

---

## 7. PowerShell per Sviluppo Python

Windows offre due versioni di PowerShell:
- **Windows PowerShell 5.1**: preinstallato su Windows 10/11, basato su .NET Framework. Eseguibile: `powershell.exe`.
- **PowerShell 7+**: versione moderna, cross-platform, basata su .NET 6+. Eseguibile: `pwsh.exe`.

### 7.1 PowerShell 7 vs Windows PowerShell 5.1

Per lo sviluppo Python, **PowerShell 7 è fortemente raccomandato**. Le differenze rilevanti:

| Caratteristica | Windows PowerShell 5.1 | PowerShell 7+ |
|----------------|------------------------|---------------|
| Operatori pipeline `&&` e `\|\|` | Non disponibili | Disponibili |
| Compatibilità con script moderni | Limitata | Completa |
| Aggiornamenti attivi | No (solo security patch) | Sì |
| Supporto su Linux/macOS | No | Sì (utile per script CI/CD portabili) |
| Performance generale | Minore | Migliore |

**Installazione di PowerShell 7:**

```powershell
winget install --id Microsoft.PowerShell -e
```

Dopo l'installazione, il terminale `pwsh.exe` è disponibile. Configuralo come shell predefinita in Windows Terminal (vedi [Sezione 7.4](#74-windows-terminal-raccomandato)).

### 7.2 Execution Policy

La **Execution Policy** di PowerShell è un meccanismo di sicurezza che controlla quali script possono essere eseguiti. Per default su Windows, la policy è `Restricted` (nessuno script) o `AllSigned` (solo script firmati digitalmente).

Gli script di attivazione degli ambienti virtuali Python (`.venv\Scripts\Activate.ps1`) non sono firmati digitalmente, quindi **verranno bloccati** dalla policy predefinita. Questo è il problema più comune nei setup Python su Windows.

#### Verifica della Policy Corrente

```powershell
Get-ExecutionPolicy -List
# Output mostra la policy per ogni scope (MachinePolicy, UserPolicy, Process, CurrentUser, LocalMachine)
```

#### Modifica della Policy (solo utente corrente)

```powershell
# Imposta RemoteSigned per l'utente corrente
# RemoteSigned: script locali eseguiti liberamente; script scaricati da Internet devono essere firmati
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verifica
Get-ExecutionPolicy -Scope CurrentUser
# Output atteso: RemoteSigned
```

> **Perché `RemoteSigned` e non `Unrestricted`?** `RemoteSigned` è il bilanciamento corretto tra sicurezza e usabilità: permette di eseguire script locali (come il tuo codice e gli script di attivazione del venv) senza disabilitare completamente le protezioni. `Unrestricted` rimuove ogni controllo e non è raccomandato.

> **Nota aziendale:** In ambienti aziendali, la policy potrebbe essere imposta dal dominio (`MachinePolicy` o `UserPolicy`), nel qual caso non è possibile modificarla senza l'intervento dell'IT. In quel caso, usa `uv run` invece di attivare il venv direttamente.

#### Attivazione di un Ambiente Virtuale dopo la Configurazione

```powershell
# Attivazione (PowerShell 5.1 e 7)
.\.venv\Scripts\Activate.ps1

# Il prompt cambia per mostrare il nome del venv:
# (.venv) PS C:\tuoprogetto>

# Disattivazione
deactivate
```

### 7.3 Profilo PowerShell

Il **profilo PowerShell** è uno script eseguito automaticamente all'avvio di ogni sessione PowerShell. È l'equivalente del `.bashrc` o `.zshrc` su Linux.

La variabile `$PROFILE` contiene il percorso del file di profilo:

```powershell
# Mostra il percorso del profilo
$PROFILE
# Output tipico: C:\Users\<utente>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1

# Verifica se il profilo esiste
Test-Path $PROFILE

# Crea il profilo se non esiste
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}

# Apri il profilo in VS Code
code $PROFILE
```

#### Contenuto Raccomandato del Profilo

```powershell
# ====================================================================
# PowerShell Profile — Sviluppo Python
# Percorso: $PROFILE
# ====================================================================

# --- Encoding ---
# Imposta UTF-8 come encoding predefinito per l'output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# --- Alias utili per Python ---
Set-Alias -Name py -Value python
Set-Alias -Name ipy -Value ipython -ErrorAction SilentlyContinue

# --- Funzione: attiva il venv nella directory corrente ---
function Activate-Venv {
    $venvPaths = @(".venv\Scripts\Activate.ps1", "venv\Scripts\Activate.ps1")
    foreach ($path in $venvPaths) {
        if (Test-Path $path) {
            & $path
            return
        }
    }
    Write-Warning "Nessun ambiente virtuale trovato nella directory corrente."
}
Set-Alias -Name activate -Value Activate-Venv

# --- Funzione: crea un nuovo progetto Python con uv ---
function New-PythonProject {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name
    )
    uv init $Name
    Set-Location $Name
    uv venv
    Write-Host "Progetto '$Name' creato. Attiva il venv con: activate" -ForegroundColor Green
}
Set-Alias -Name newpy -Value New-PythonProject

# --- Funzione: aggiorna uv e gli strumenti globali ---
function Update-PythonTools {
    Write-Host "Aggiornamento uv..." -ForegroundColor Cyan
    uv self update
    Write-Host "Aggiornamento strumenti globali..." -ForegroundColor Cyan
    uv tool upgrade --all
    Write-Host "Completato." -ForegroundColor Green
}

# --- Messaggio di benvenuto (opzionale) ---
# Write-Host "Python dev environment loaded." -ForegroundColor DarkGray
```

### 7.4 Windows Terminal (Raccomandato)

**Windows Terminal** è il terminale moderno di Microsoft: supporta tab multiple, profili per shell diverse, temi, rendering GPU e split pane. Su Windows 11 è preinstallato; su Windows 10 si installa dal Microsoft Store o con winget.

```powershell
winget install --id Microsoft.WindowsTerminal -e
```

#### Configurazione del Profilo PowerShell 7 come Default

1. Apri Windows Terminal.
2. Clicca sulla freccia accanto al `+` nella barra dei tab → "Settings" (`Ctrl+,`).
3. In **"Default profile"**, seleziona **"PowerShell"** (la versione 7, non "Windows PowerShell").
4. Salva le impostazioni.

#### Scorciatoie Utili in Windows Terminal

| Scorciatoia | Azione |
|-------------|--------|
| `Ctrl+Shift+T` | Nuovo tab (profilo default) |
| `Ctrl+Shift+1` / `2` / `3` | Nuovo tab con profilo specifico |
| `Ctrl+Shift+W` | Chiudi tab corrente |
| `Alt+Shift+-` | Split orizzontale |
| `Alt+Shift++` | Split verticale |
| `Ctrl+Shift+F` | Cerca nel terminale |
| `Ctrl+Shift+P` | Command palette |

---

## 8. Prima Sessione Interattiva (REPL)

Il **REPL** (Read-Eval-Print Loop) è l'ambiente interattivo di Python: inserisci un'espressione, Python la valuta e ne stampa il risultato. È lo strumento ideale per esplorare il linguaggio, testare snippets, e verificare il funzionamento delle API.

### 8.1 Il REPL Standard

```powershell
# Avvio del REPL
python
# oppure con uv (usa la versione gestita da uv)
uv run python
```

L'output di avvio del REPL mostra le informazioni sull'interprete:

```
Python 3.12.7 (main, Oct  1 2024, 15:17:31) [MSC v.1941 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Il simbolo `>>>` è il prompt del REPL (indica che è pronto per ricevere input).

#### Comandi Base nel REPL

```python
# Aritmetica
>>> 2 + 3
5
>>> 10 / 3
3.3333333333333335
>>> 10 // 3       # divisione intera
3
>>> 10 % 3        # modulo
1
>>> 2 ** 10       # potenza
1024

# Stringhe
>>> "Ciao, " + "Python!"
'Ciao, Python!'
>>> "Python" * 3
'PythonPythonPython'
>>> f"2 + 3 = {2 + 3}"
'2 + 3 = 5'

# Liste
>>> [1, 2, 3] + [4, 5]
[1, 2, 3, 4, 5]
>>> sorted([3, 1, 2])
[1, 2, 3]

# Uscita dal REPL
>>> exit()
# oppure: Ctrl+Z + Invio su Windows (EOF)
# oppure: Ctrl+D su Linux/macOS
```

### 8.2 Comandi di Diagnostica nel REPL

Questi comandi verificano che l'ambiente sia configurato correttamente:

```python
>>> import sys

# Versione di Python
>>> sys.version
'3.12.7 (main, Oct  1 2024, 15:17:31) [MSC v.1941 64 bit (AMD64)]'

# Percorso dell'eseguibile
>>> sys.executable
'C:\\Users\\utente\\.local\\share\\uv\\python\\cpython-3.12.7-windows-x86_64-none\\python.exe'

# Percorsi di ricerca dei moduli
>>> sys.path
['', 'C:\\...\\python312.zip', 'C:\\...\\Lib', 'C:\\...\\DLLs', ...]

# Piattaforma
>>> sys.platform
'win32'

# Encoding predefinito
>>> sys.getdefaultencoding()
'utf-8'

# Encoding del filesystem (importante per i nomi di file)
>>> sys.getfilesystemencoding()
'utf-8'

# Informazioni sull'implementazione
>>> import platform
>>> platform.python_implementation()
'CPython'
>>> platform.architecture()
('64bit', 'WindowsPE')
>>> platform.machine()
'AMD64'

# Directory dei pacchetti installati
>>> import site
>>> site.getsitepackages()
['C:\\...\\Lib\\site-packages']

# Verifica Zen di Python
>>> import this
```

### 8.3 Uso Pratico del REPL per l'Apprendimento

Il REPL è lo strumento più efficace per esplorare il linguaggio mentre si studia. Ecco pattern d'uso specifici per ogni fase del corso.

#### Esplorazione di Oggetti e API

```python
# Scopri cosa fa un oggetto con help()
>>> help(str.split)
# Mostra la docstring completa di str.split

# Scopri tutti i metodi di un oggetto con dir()
>>> dir([])        # metodi di una lista
>>> [m for m in dir([]) if not m.startswith('_')]
['append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']

# Controlla il tipo di qualsiasi oggetto
>>> type(42)
<class 'int'>
>>> type(3.14)
<class 'float'>
>>> type("ciao")
<class 'str'>
>>> type([1, 2, 3])
<class 'list'>
>>> type(None)
<class 'NoneType'>

# isinstance() per verifiche di tipo
>>> isinstance(42, int)
True
>>> isinstance(42, (int, float))   # verifica contro più tipi
True
```

#### Esplorare le Strutture Dati

```python
# Test rapido di comprehension
>>> [x**2 for x in range(10)]
[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

>>> {k: v for k, v in zip("abc", [1, 2, 3])}
{'a': 1, 'b': 2, 'c': 3}

>>> {x for x in [1, 2, 2, 3, 3, 3]}
{1, 2, 3}

# Test di slicing
>>> s = "Hello, World!"
>>> s[:5]
'Hello'
>>> s[-6:]
'orld!'
>>> s[::2]
'Hlo ol!'
>>> s[::-1]     # inversione
'!dlroW ,olleH'

# Unpacking
>>> a, b, *rest = [1, 2, 3, 4, 5]
>>> a, b, rest
(1, 2, [3, 4, 5])
```

#### Misurare le Prestazioni

```python
>>> import timeit

# Confronta due implementazioni
>>> timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
0.12...

>>> timeit.timeit('"-".join([str(n) for n in range(100)])', number=10000)
0.09...   # la list comprehension è più veloce del generator per join

# Misura veloce di una singola operazione
>>> timeit.timeit(lambda: sorted(range(100)), number=10000)
```

#### Testare Espressioni Regolari

```python
>>> import re
>>> pattern = re.compile(r'\b\w{4}\b')   # parole di esattamente 4 caratteri
>>> pattern.findall("Il gatto nero miagola")
['gatto', 'nero']

>>> re.match(r'^\d{3}-\d{2}-\d{4}$', '123-45-6789')
<re.Match object; span=(0, 11), match='123-45-6789'>

>>> re.match(r'^\d{3}-\d{2}-\d{4}$', '123456789')   # None (nessun match)
```

#### Navigare la Libreria Standard

```python
>>> import os
>>> os.getcwd()                          # directory corrente
'C:\\Users\\utente\\progetti\\mio-progetto'

>>> import pathlib
>>> p = pathlib.Path.home()              # directory home
>>> list(p.glob("*.txt"))               # file .txt nella home

>>> import json
>>> json.dumps({"chiave": [1, 2, 3]}, indent=2)
'{\n  "chiave": [\n    1,\n    2,\n    3\n  ]\n}'

>>> import datetime
>>> datetime.date.today()
datetime.date(2026, 7, 15)
>>> datetime.datetime.now().isoformat()
'2026-07-15T14:32:01.123456'
```

### 8.5 IPython come REPL Avanzato

**IPython** è un REPL molto più potente del REPL standard, con syntax highlighting, autocompletamento avanzato, history persistente tra sessioni, e numerosi comandi magici (`%`).

```powershell
# Installazione con uv (in un tool globale, senza inquinare i progetti)
uv tool install ipython

# Avvio
ipython
```

Caratteristiche principali di IPython:

```python
In [1]: # Syntax highlighting colorato

In [2]: # Autocompletamento con Tab: scrivi 'im' e premi Tab
import

In [3]: # Comandi magici
%timeit sorted(range(1000))     # misura le prestazioni
%time sum(range(1_000_000))     # misura una singola esecuzione
%history                         # mostra la storia dei comandi
%pwd                             # directory corrente
%ls                              # lista file

In [4]: # Help rapido con ? e ??
import os
os.path.join?        # mostra docstring
os.path.join??       # mostra il codice sorgente

In [5]: # Shell escape con !
!dir                 # esegue un comando di sistema
!python --version

In [6]: # Output precedente
In [6]: 2 + 2
Out[6]: 4
In [7]: _ + 1       # _ contiene l'ultimo output
Out[7]: 5
```

---

## 9. Struttura delle Directory di Progetto

Una struttura coerente delle directory rende i progetti manutenibili, facilita la collaborazione e rispetta le convenzioni della comunità Python.

### 9.1 Script Singolo

Per script autonomi (automazione, utility, script di one-shot):

```
mio-script/
├── .python-version      # versione Python richiesta (per uv/pyenv)
├── .gitignore
├── main.py              # oppure il nome descrittivo dello script
└── README.md
```

Con `uv`, si può eseguire direttamente senza creare un progetto formale:

```powershell
uv run main.py
```

### 9.2 Progetto con Libreria

Per librerie riutilizzabili o applicazioni strutturate (la struttura raccomandata da `uv init`):

```
mio-progetto/
├── .python-version          # es. "3.12"
├── .venv/                   # ambiente virtuale (NON committare)
├── src/
│   └── mio_progetto/        # nome del pacchetto (snake_case)
│       ├── __init__.py
│       ├── core.py
│       ├── utils.py
│       └── models.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core.py
│   └── test_utils.py
├── .gitignore
├── pyproject.toml           # configurazione progetto (build, dipendenze, tool)
├── uv.lock                  # lock file (committare sempre)
└── README.md
```

**Creazione con uv:**

```powershell
# Crea la struttura automaticamente
uv init mio-progetto --lib
cd mio-progetto

# Crea e attiva il venv
uv venv
.\.venv\Scripts\Activate.ps1

# Aggiunge una dipendenza
uv add requests

# Aggiunge una dipendenza di sviluppo
uv add --dev pytest ruff mypy
```

### 9.3 Applicazione Flask/FastAPI

Per applicazioni web (API REST, microservizi):

```
mia-api/
├── .python-version
├── .venv/
├── src/
│   └── mia_api/
│       ├── __init__.py
│       ├── main.py              # entry point dell'applicazione
│       ├── config.py            # configurazione da variabili d'ambiente
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── routers/             # (FastAPI) o blueprints (Flask)
│       │   ├── __init__.py
│       │   └── users.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── user_service.py
│       └── db/
│           ├── __init__.py
│           └── session.py
├── tests/
│   ├── conftest.py
│   ├── test_routers/
│   └── test_services/
├── .env.example             # template delle variabili d'ambiente (committare)
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

> **Mai committare il file `.env` reale.** Contiene secrets (chiavi API, password del database). Solo `.env.example` (senza valori reali) va nel repository.

### 9.4 Convenzioni di Naming

| Elemento | Convenzione | Esempio |
|----------|-------------|---------|
| Directory del progetto | kebab-case | `mio-progetto-web` |
| Pacchetto Python (directory src/) | snake_case | `mio_progetto_web` |
| File Python | snake_case | `user_service.py` |
| Classi | PascalCase | `UserService` |
| Funzioni e metodi | snake_case | `get_user_by_id` |
| Costanti | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Variabili private | `_prefisso` | `_cache` |
| Variabili "molto private" (name mangling) | `__prefisso` | `__secret_key` |
| Moduli di test | `test_` prefisso | `test_user_service.py` |
| Fixture pytest | snake_case | `mock_database` |

---

## 10. Checklist Verifica Setup

Esegui questa checklist al termine del setup. Ogni voce deve risultare verificata prima di procedere con il Modulo 01.

### Setup di Base

```powershell
# 1. Python raggiungibile da PowerShell
python --version
# Atteso: Python 3.12.x o superiore
```

- [ ] `python --version` restituisce `Python 3.12.x` o superiore

```powershell
# 2. uv installato e funzionante
uv --version
# Atteso: uv 0.7.x o superiore
```

- [ ] `uv --version` restituisce la versione corrente

```powershell
# 3. pip funzionante
python -m pip --version
# Atteso: pip 24.x from ... (python 3.12)
```

- [ ] `python -m pip --version` restituisce una versione compatibile

```powershell
# 4. Git installato
git --version
# Atteso: git version 2.45.x
```

- [ ] `git --version` restituisce una versione 2.39 o superiore

```powershell
# 5. VS Code raggiungibile dalla riga di comando
code --version
```

- [ ] `code --version` restituisce la versione corrente

### Configurazione PATH

```powershell
# 6. Python trovato nel PATH
where.exe python
# Atteso: un solo percorso (o il percorso corretto come primo)
```

- [ ] `where.exe python` mostra il percorso corretto

```powershell
# 7. uv trovato nel PATH
where.exe uv
```

- [ ] `where.exe uv` mostra il percorso corretto

### PowerShell e Ambienti Virtuali

```powershell
# 8. Execution Policy configurata
Get-ExecutionPolicy -Scope CurrentUser
# Atteso: RemoteSigned
```

- [ ] `Get-ExecutionPolicy -Scope CurrentUser` restituisce `RemoteSigned`

```powershell
# 9. Creazione e attivazione di un venv
mkdir C:\Temp\test-py && cd C:\Temp\test-py
uv venv
.\.venv\Scripts\Activate.ps1
python --version
deactivate
cd .. && Remove-Item -Recurse -Force test-py
```

- [ ] L'ambiente virtuale si crea e si attiva senza errori

### Git

```powershell
# 10. Identità Git configurata
git config --global user.name
git config --global user.email
```

- [ ] `git config --global user.name` restituisce il tuo nome
- [ ] `git config --global user.email` restituisce la tua email

```powershell
# 11. Credential manager configurato
git config --global credential.helper
# Atteso: manager
```

- [ ] `git config --global credential.helper` restituisce `manager`

### Progetto di Collaudo Completo

Crea un progetto minimo end-to-end per verificare che tutto funzioni insieme:

```powershell
# 12. Creazione progetto con uv
mkdir $HOME\progetti
cd $HOME\progetti
uv init hello-python
cd hello-python

# 13. Inizializzazione repository Git
git init
git add .
git commit -m "Initial commit: hello-python"

# 14. Creazione e attivazione venv
uv venv
.\.venv\Scripts\Activate.ps1
```

- [ ] Il progetto viene creato senza errori
- [ ] Il repository Git viene inizializzato
- [ ] Il venv si attiva (il prompt mostra `(hello-python)`)

```powershell
# 15. Apertura in VS Code
code .
```

In VS Code:
- [ ] VS Code apre la cartella del progetto
- [ ] VS Code seleziona automaticamente il Python in `.venv`
- [ ] Non ci sono errori di estensioni nella barra di stato

```python
# 16. Esecuzione del file hello.py (creato da uv init)
# Il file src/hello_python/__init__.py contiene codice base
# Crea un main.py per il test
```

```powershell
# Crea e testa un file Python semplice
@"
def saluta(nome: str) -> str:
    return f"Ciao, {nome}!"

if __name__ == "__main__":
    messaggio = saluta("Python")
    print(messaggio)
    assert messaggio == "Ciao, Python!", "Test fallito"
    print("Tutti i test superati.")
"@ | Out-File -Encoding utf8 main.py

python main.py
# Atteso:
# Ciao, Python!
# Tutti i test superati.
```

- [ ] `python main.py` esegue senza errori e stampa i messaggi attesi

```powershell
# 17. Pulizia (opzionale)
cd ..
Remove-Item -Recurse -Force hello-python
```

Se tutti i punti della checklist sono verificati, il setup è completo e sei pronto per il Modulo 01.

---

## 11. Troubleshooting — Problemi Frequenti

### Problema: `python` non trovato dopo l'installazione

**Sintomo:**
```
python : The term 'python' is not recognized as the name of a cmdlet...
```

**Cause e soluzioni:**

1. Terminale aperto prima dell'installazione: **chiudi e riapri PowerShell**.
2. "Add Python to PATH" non era spuntato durante l'installazione: aggiungi manualmente (vedi [Sezione 4.3](#43-aggiunta-manuale-al-path)) oppure reinstalla.
3. Gli stub di Windows Store interferiscono: disabilitali (vedi [Sezione 4.4](#44-problemi-comuni-e-risoluzione)).

---

### Problema: Errore di Execution Policy all'attivazione del venv

**Sintomo:**
```
.\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```

**Soluzione:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Se la policy è bloccata dal dominio:
```powershell
# Alternativa: esegui il venv tramite uv senza attivarlo
uv run python script.py
uv run pytest
uv run uvicorn app.main:app
```

---

### Problema: VS Code non trova il Python del venv

**Sintomo:** Pylance mostra errori di import per i pacchetti installati nel venv.

**Soluzioni:**
1. `Ctrl+Shift+P` → "Python: Select Interpreter" → seleziona `.\.venv\Scripts\python.exe`.
2. Verifica che il file `.vscode/settings.json` del progetto contenga:
   ```json
   {
       "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe"
   }
   ```
3. Riavvia VS Code completamente (non solo la finestra).

---

### Problema: `uv` non trovato dopo l'installazione

**Sintomo:**
```
uv : The term 'uv' is not recognized...
```

**Soluzione:**
```powershell
# Aggiungi manualmente la directory di uv al PATH
$uvPath = "$env:USERPROFILE\.local\bin"
[Environment]::SetEnvironmentVariable(
    "PATH",
    "$uvPath;$([Environment]::GetEnvironmentVariable('PATH', 'User'))",
    "User"
)
# Riapri il terminale
```

---

### Problema: Conflitto tra versioni Python

**Sintomo:** `python --version` mostra la versione sbagliata nonostante si sia installata quella giusta.

**Diagnosi:**
```powershell
where.exe python
# Se mostra più righe, la prima ha priorità
```

**Soluzione con uv:**
```powershell
# uv gestisce le versioni per progetto tramite .python-version
# In ogni progetto, specifica la versione:
"3.12" | Out-File -Encoding utf8 .python-version

# uv usa automaticamente la versione specificata
uv run python --version  # Python 3.12.x
```

**Soluzione manuale (senza uv):**
Modifica l'ordine delle directory nel PATH (metti la versione desiderata per prima).

---

### Problema: pip installa nel Python di sistema invece del venv

**Sintomo:** `pip install requests` installa globalmente anche se un venv è stato creato.

**Causa:** Il venv non è attivato.

**Soluzione:**
```powershell
# Verifica se un venv è attivo
$env:VIRTUAL_ENV
# Se vuoto, nessun venv è attivo

# Attiva il venv
.\.venv\Scripts\Activate.ps1

# Oppure usa sempre uv run / uv pip per isolare le operazioni
uv pip install requests
```

---

### Problema: Caratteri non-ASCII nel terminale (encoding)

**Sintomo:** Caratteri come `à`, `è`, `ü` vengono visualizzati come `?` o sequenze strane.

**Soluzione:**
```powershell
# Imposta UTF-8 nella sessione corrente
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001  # cambia la code page di Windows a UTF-8

# Per rendere la modifica permanente, aggiungila al profilo PowerShell:
Add-Content $PROFILE '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8'
Add-Content $PROFILE '$OutputEncoding = [System.Text.Encoding]::UTF8'
```

---

### Problema: `git push` chiede username e password ogni volta

**Sintomo:** GitHub chiede le credenziali ad ogni operazione remota.

**Soluzione — usa Git Credential Manager:**
```powershell
git config --global credential.helper manager

# Poi esegui un push: si aprirà un browser per autenticarti con GitHub
git push origin main
# Le credenziali vengono salvate nel Credential Manager di Windows
```

**Alternativa — usa SSH:**
Segui la [Sezione 6.3](#63-configurazione-ssh-opzionale-ma-consigliato) per configurare l'autenticazione SSH, che non richiede credenziali ad ogni push.

---

## 12. WSL2 — Windows Subsystem for Linux (Alternativa Avanzata)

**WSL2** (Windows Subsystem for Linux, versione 2) è un ambiente Linux completo eseguito all'interno di Windows tramite un kernel Linux reale. Non è necessario per questo corso, ma è menzionato perché molti sviluppatori Python professionali lo utilizzano su Windows per:

- Comportamento identico alla produzione (i server di produzione sono tipicamente Linux).
- Strumenti come `make`, `gcc`, librerie di sistema che su Windows richiedono configurazione aggiuntiva.
- Performance di I/O migliori per operazioni intensive su file.
- Compatibilità nativa con Docker Desktop.

### Quando Usare WSL2

| Scenario | Setup Raccomandato |
|----------|-------------------|
| Apprendimento di Python, corso base | Windows nativo con uv (questo documento) |
| Sviluppo web con FastAPI/Django | Windows nativo con uv è sufficiente |
| Data science con pandas/NumPy | Windows nativo con uv è sufficiente |
| Librerie con dipendenze native complesse | WSL2 può semplificare l'installazione |
| Sviluppo DevOps (Docker, Kubernetes, Ansible) | WSL2 fortemente consigliato |
| Contribuzione a progetti open source Linux | WSL2 consigliato per parità con la CI |

### Installazione di WSL2 (solo se necessario)

```powershell
# Abilita WSL2 (richiede riavvio)
wsl --install

# Installa Ubuntu 24.04 LTS (distribuzione raccomandata)
wsl --install -d Ubuntu-24.04

# Verifica la versione WSL
wsl --version
```

### Python in WSL2

All'interno di WSL2, Python si installa come su un sistema Linux standard:

```bash
# All'interno della shell WSL2 (bash/zsh)

# Metodo WSL2 raccomandato: uv (stesso strumento, stesso flusso)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
uv init mio-progetto
cd mio-progetto
uv venv
source .venv/bin/activate
```

> **Nota:** In WSL2, i comandi di attivazione del venv usano la sintassi Linux (`source .venv/bin/activate`) invece di quella PowerShell (`.\.venv\Scripts\Activate.ps1`). VS Code supporta nativamente WSL2 tramite l'estensione **WSL** (`ms-vscode-remote.remote-wsl`).

### Interoperabilità Windows-WSL2

```powershell
# Dalla PowerShell Windows: esegui un comando in WSL2
wsl python3 --version
wsl ls -la /home/utente

# Da WSL2: accedi ai file Windows
ls /mnt/c/Users/utente/progetti

# Da Windows: accedi ai file WSL2 (tramite UNC path)
\\wsl.localhost\Ubuntu\home\utente\
```

> **Importante:** Le prestazioni sono migliori quando i file risiedono nel filesystem nativo dell'ambiente in uso. Lavorare su file Windows (`/mnt/c/`) da WSL2 è significativamente più lento rispetto a lavorare direttamente nel filesystem WSL2 (`/home/`).

---

## 13. Riferimenti

### Documentazione Ufficiale

| Risorsa | URL |
|---------|-----|
| Python — Documentazione ufficiale | https://docs.python.org/3/ |
| Python — Download per Windows | https://www.python.org/downloads/windows/ |
| Python — FAQ su Windows | https://docs.python.org/3/faq/windows.html |
| Python — Using Python on Windows | https://docs.python.org/3/using/windows.html |
| uv — Documentazione | https://docs.astral.sh/uv/ |
| uv — Installazione | https://docs.astral.sh/uv/getting-started/installation/ |
| VS Code — Python Tutorial | https://code.visualstudio.com/docs/python/python-tutorial |
| VS Code — Pylance | https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance |
| Ruff — Documentazione | https://docs.astral.sh/ruff/ |
| Git for Windows | https://git-scm.com/download/win |
| Git Credential Manager | https://github.com/git-ecosystem/git-credential-manager |
| PowerShell 7 | https://github.com/PowerShell/PowerShell |
| Windows Terminal | https://github.com/microsoft/terminal |

### PEP di Riferimento

| PEP | Titolo | Rilevanza per questo modulo |
|-----|--------|-----------------------------|
| PEP 20 | The Zen of Python | Filosofia fondamentale |
| PEP 8 | Style Guide for Python Code | Convenzioni di stile |
| PEP 518 | Specifying Minimum Build System Requirements for Python Projects | `pyproject.toml` |
| PEP 517 | A build-system independent format for source trees | Build system moderno |
| PEP 621 | Storing project metadata in pyproject.toml | Metadati di progetto |
| PEP 723 | Inline script metadata | Script con dipendenze inline (uv) |

### Moduli Correlati in Questo Corso

| Modulo | Titolo | Connessione |
|--------|--------|-------------|
| [01](01-fondamenti-linguaggio.md) | Fondamenti del Linguaggio | Primo modulo dopo questo setup |
| [24](24-virtual-environments.md) | Virtual Environments e Gestione Dipendenze | Approfondimento su uv, venv, pip-tools, Poetry |
| [22](22-clean-code.md) | Clean Code | PEP 8, strumenti di linting e formatting (ruff, black) |
| [08](08-testing.md) | Testing | pytest, configurazione test in VS Code |
| [27](27-ci-cd-per-python.md) | CI/CD per Python | Automazione del setup in ambienti CI |

### Strumenti Menzionati

| Strumento | Versione minima | Installazione |
|-----------|----------------|---------------|
| Python | 3.12.0 | `uv python install 3.12` |
| uv | 0.7.0 | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| VS Code | 1.90.0 | `winget install Microsoft.VisualStudioCode` |
| Pylance | latest | `code --install-extension ms-python.vscode-pylance` |
| Ruff | 0.5.0 | `uv tool install ruff` o estensione VS Code |
| Git | 2.39.0 | `winget install Git.Git` |
| PowerShell | 7.4.0 | `winget install Microsoft.PowerShell` |
| Windows Terminal | 1.19.0 | `winget install Microsoft.WindowsTerminal` |
| IPython | 8.x | `uv tool install ipython` |

---

*Documento parte del corso "Programmazione Python Professionale" — Modulo 00*
*Versione: 2026-07-15 · Piattaforma: Windows 10/11 · Python: 3.12+*
