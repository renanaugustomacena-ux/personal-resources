---
corso: "Programmazione Python"
fase: "6 — DevOps e Distribuzione"
modulo: "24"
titolo: "Virtual Environments e Gestione Dipendenze"
versione: "venv 3.12+ / uv 0.7+ / pip-tools 7.x / Poetry 1.8+"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "05 — Gestione File e I/O"
obiettivi:
  - "Creare e gestire ambienti virtuali con venv e uv"
  - "Comprendere il lockfile e la riproducibilita delle dipendenze"
  - "Confrontare pip, pip-tools, Poetry e uv per workflow diversi"
  - "Configurare pyproject.toml per la gestione delle dipendenze"
  - "Gestire dipendenze in monorepo e workspace"
  - "Risolvere conflitti di dipendenze e vulnerability scanning"
tag: [venv, uv, pip, Poetry, pip-tools, dipendenze, lockfile, pyproject-toml]
---

# Virtual Environments e Gestione Dipendenze --- Guida Completa

> **Modulo 24** · **Aggiornamento:** 2026-05-24 · **Versione:** venv 3.12+ / uv 0.7+ / pip-tools 7.x / Poetry 1.8+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Gestione File e I/O](05-gestione-file-io.md)
>
> Al termine di questo modulo saprai:
> 1. Creare e gestire ambienti virtuali con `venv` e `uv`
> 2. Comprendere il lockfile e la riproducibilita delle dipendenze
> 3. Confrontare pip, pip-tools, Poetry e uv per workflow diversi
> 4. Configurare `pyproject.toml` per la gestione delle dipendenze
> 5. Gestire dipendenze in monorepo e workspace
> 6. Risolvere conflitti di dipendenze e vulnerability scanning
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **uv > poetry > pipenv per nuovi progetti.** Speed + lock + venv built-in.
2. **`uv venv` + `uv pip install` workflow standard.**
3. **`uv lock` per reproducible install.**
4. **Mai `pip install` global.**
5. **Lock file sempre committato.** Garanzia di build identici tra dev, CI e prod.
6. **Dependency resolution e un problema NP-completo.** Conoscere gli algoritmi aiuta a diagnosticare conflitti.
7. **CI caching riduce i tempi del 60-80%.** Cache path espliciti per ogni tool.


## Mappa concettuale

```
                        ┌─────────────────────┐
                        │    pyproject.toml    │
                        │  (fonte di verita)   │
                        └──────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
              ▼                    ▼                     ▼
     ┌────────────────┐  ┌────────────────┐   ┌────────────────┐
     │   Build System │  │  Dipendenze    │   │   Metadata     │
     │ hatchling/flit │  │  dirette +     │   │  name/version/ │
     │   setuptools   │  │  gruppi (dev)  │   │  license/urls  │
     └────────┬───────┘  └───────┬────────┘   └────────────────┘
              │                  │
              │          ┌───────┴────────┐
              │          │   Resolver     │
              │          │ (backtracking) │
              │          └───────┬────────┘
              │                  │
              │          ┌───────▼────────┐
              │          │   Lock File    │
              │          │  uv.lock /     │
              │          │  poetry.lock / │
              │          │  requirements  │
              │          │   .txt pinned  │
              │          └───────┬────────┘
              │                  │
              │          ┌───────▼────────┐
              │          │   venv / .venv │
              │          │  (isolamento)  │
              │          └───────┬────────┘
              │                  │
              │     ┌────────────┼──────────────┐
              │     │            │              │
              │     ▼            ▼              ▼
              │  bin/python  lib/site-packages  pyvenv.cfg
              │  (symlink)   (pacchetti)        (config)
              │
              └──────► wheel / sdist ──► PyPI / registry
```


## Indice

1. [Panoramica](#panoramica)
2. [venv (Standard Library)](#venv-standard-library)
3. [pip](#pip)
4. [Poetry](#poetry)
5. [uv (Il Futuro)](#uv-il-futuro)
6. [Pyenv](#pyenv)
7. [conda](#conda)
8. [pipx](#pipx)
9. [Confronto Strumenti](#confronto-strumenti)
10. [Docker come Environment](#docker-come-environment)
11. [Best Practices](#best-practices)
12. [Internals di venv: symlink, pyvenv.cfg, startup discovery](#internals-di-venv)
13. [uv Deep Dive](#uv-deep-dive)
14. [PEP 735 — Dependency Groups](#pep-735--dependency-groups)
15. [uv Workspaces](#uv-workspaces)
16. [pip-tools Deep Dive](#pip-tools-deep-dive)
17. [Formati di Lock File a confronto](#formati-di-lock-file)
18. [Algoritmi di Dependency Resolution](#algoritmi-di-dependency-resolution)
19. [Installazioni Riproducibili](#installazioni-riproducibili)
20. [CI Caching Patterns](#ci-caching-patterns)
21. [Devcontainers e Codespaces per Python](#devcontainers-e-codespaces-per-python)
22. [Esercizi](#esercizi)
23. [Letture e Riferimenti](#letture-e-riferimenti)
24. [Moduli Correlati](#moduli-correlati)
25. [Glossario](#glossario)

---

## Panoramica

### Perche gli Ambienti Virtuali Sono Essenziali

Chiunque abbia lavorato su piu di un progetto Python ha incontrato prima o poi il cosiddetto **dependency hell**: il progetto A richiede `requests==2.28.0`, mentre il progetto B necessita di `requests==2.31.0`. Senza un meccanismo di isolamento, installare le dipendenze di un progetto puo rompere silenziosamente un altro.

Gli ambienti virtuali risolvono questo problema creando **copie isolate dell'interprete Python e delle sue librerie** per ogni progetto. Ogni ambiente ha la propria directory `site-packages`, il proprio binario `python` e il proprio `pip`. Questo significa che le dipendenze installate in un ambiente non influenzano ne l'installazione globale di Python ne gli altri ambienti.

I vantaggi principali sono:

- **Isolamento completo**: ogni progetto ha le proprie dipendenze, senza conflitti.
- **Riproducibilita**: grazie ai file di lock e ai requirements, chiunque puo ricreare esattamente lo stesso ambiente.
- **Sicurezza**: non si modifica l'installazione di sistema di Python, evitando di corrompere strumenti del sistema operativo che dipendono da Python.
- **Collaborazione**: i file di configurazione delle dipendenze possono essere condivisi via version control, garantendo che tutto il team lavori con le stesse versioni.

### Il Concetto di Isolamento delle Dipendenze

L'isolamento funziona su un principio semplice: quando si attiva un ambiente virtuale, il sistema modifica la variabile d'ambiente `PATH` in modo che il binario `python` dell'ambiente virtuale venga trovato prima di quello di sistema. Ogni chiamata a `pip install` installa i pacchetti nella directory `site-packages` locale dell'ambiente, non in quella globale.

```
Sistema globale:          /usr/lib/python3.12/site-packages/
Ambiente virtuale A:      /home/user/progetto-a/.venv/lib/python3.12/site-packages/
Ambiente virtuale B:      /home/user/progetto-b/.venv/lib/python3.12/site-packages/
```

Ogni ambiente e una "bolla" indipendente. Quando lo si disattiva, si torna al Python di sistema come se nulla fosse cambiato.

### Storia: da virtualenv a venv ai Tool Moderni

La storia degli ambienti virtuali in Python riflette l'evoluzione dell'ecosistema:

- **virtualenv (2007)**: il primo strumento per creare ambienti isolati, creato da Ian Bicking. Era un pacchetto di terze parti che copiava fisicamente l'interprete Python. Rimane ancora oggi utilizzabile e offre funzionalita aggiuntive rispetto a `venv`.
- **venv (Python 3.3, PEP 405)**: la risposta ufficiale della standard library. Piu leggero di `virtualenv` perche usa symlink invece di copie. Diventa lo strumento raccomandato per la maggior parte dei casi d'uso.
- **pipenv (2017)**: tentativo di unificare `pip` e `virtualenv` con un file `Pipfile` dichiarativo. Ha avuto un periodo di grande popolarita ma ha poi sofferto di problemi di manutenzione e lentezza.
- **Poetry (2018)**: strumento completo per la gestione dei progetti Python, con risoluzione delle dipendenze, build system e pubblicazione. Usa `pyproject.toml` ed e diventato molto popolare.
- **uv (2024)**: scritto in Rust dal team di Astral (gli stessi di Ruff), promette di essere il sostituto universale di `pip`, `pip-tools`, `virtualenv`, `pipx` e altro. Estremamente veloce, rappresenta la direzione futura dell'ecosistema.

---

## venv (Standard Library)

Il modulo `venv` e incluso nella standard library di Python a partire dalla versione 3.3 ed e lo strumento ufficiale per la creazione di ambienti virtuali. Non richiede installazione aggiuntiva.

### Creazione di un Ambiente Virtuale

```bash
# Sintassi di base
python -m venv .venv

# Con accesso ai pacchetti di sistema (sconsigliato nella maggior parte dei casi)
python -m venv --system-site-packages .venv

# Senza pip (ambiente minimale)
python -m venv --without-pip .venv

# Con una versione specifica di Python (se installata)
python3.12 -m venv .venv

# Con prompt personalizzato
python -m venv --prompt "mio-progetto" .venv
```

Il comando crea una directory `.venv` con la seguente struttura:

```
.venv/
├── bin/                    # Linux/macOS (Scripts/ su Windows)
│   ├── activate            # Script di attivazione bash
│   ├── activate.csh        # Script per csh/tcsh
│   ├── activate.fish       # Script per fish shell
│   ├── pip                 # pip locale
│   ├── pip3                # pip3 locale
│   └── python -> python3   # Symlink al Python di sistema
├── include/                # Header files C per compilazione
├── lib/
│   └── python3.12/
│       └── site-packages/  # Pacchetti installati nell'ambiente
└── pyvenv.cfg              # Configurazione dell'ambiente
```

### Attivazione

L'attivazione modifica temporaneamente il `PATH` della shell corrente:

```bash
# Linux / macOS (bash/zsh)
source .venv/bin/activate

# Windows (cmd.exe)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Fish shell
source .venv/bin/activate.fish

# Nushell
overlay use .venv/bin/activate.nu
```

Dopo l'attivazione, il prompt della shell mostra il nome dell'ambiente:

```bash
(.venv) user@host:~/progetto$
```

### Disattivazione

```bash
deactivate
```

Il comando `deactivate` ripristina il `PATH` originale e rimuove l'indicatore dal prompt.

### Come Funziona Internamente

Il meccanismo e elegante nella sua semplicita:

1. **Symlink**: su Linux/macOS, il binario `python` nell'ambiente e un symlink al Python di sistema. Questo rende la creazione veloce e leggera in termini di spazio su disco.
2. **pyvenv.cfg**: file di configurazione nella root dell'ambiente che definisce il comportamento:

```ini
home = /usr/bin
include-system-site-packages = false
version = 3.12.3
executable = /usr/bin/python3.12
command = /usr/bin/python3.12 -m venv /home/user/progetto/.venv
```

3. **Modifica del PATH**: lo script `activate` prepone la directory `bin/` dell'ambiente al `PATH`, facendo si che `python` e `pip` puntino alle versioni locali.
4. **site-packages isolato**: Python, all'avvio, rileva il file `pyvenv.cfg` e configura `sys.path` per usare il `site-packages` locale.

### Convenzioni di Denominazione

La convenzione piu diffusa e usare `.venv` come nome della directory:

- Il punto iniziale la rende nascosta su sistemi Unix.
- E riconosciuta automaticamente da IDE come VS Code e PyCharm.
- E gia inclusa nei template `.gitignore` standard per Python.

Alternative comuni sono `venv`, `env` e `.env` (quest'ultima e sconsigliata perche puo confondersi con i file di variabili d'ambiente).

**Importante**: la directory dell'ambiente virtuale non va mai inclusa nel version control. Aggiungere `.venv/` al file `.gitignore`.

---

## pip

`pip` (Pip Installs Packages) e il gestore di pacchetti standard di Python e il punto di partenza per la gestione delle dipendenze.

### Fondamenti

#### Comandi Essenziali

```bash
# Installare un pacchetto
pip install requests

# Installare una versione specifica
pip install requests==2.31.0

# Installare con vincoli di versione
pip install "requests>=2.28,<3.0"

# Aggiornare un pacchetto
pip install --upgrade requests

# Disinstallare
pip uninstall requests

# Elencare i pacchetti installati
pip list

# Mostrare dettagli di un pacchetto
pip show requests

# Mostrare pacchetti obsoleti
pip list --outdated

# Congelare le dipendenze correnti
pip freeze
```

#### requirements.txt

Il file `requirements.txt` e il formato tradizionale per dichiarare le dipendenze:

```txt
# Versione esatta (pinning) - raccomandato per le applicazioni
requests==2.31.0
flask==3.0.2
sqlalchemy==2.0.25

# Vincoli di versione
requests>=2.28.0,<3.0.0
flask~=3.0.0          # Equivale a >=3.0.0, <3.1.0

# Senza vincolo (sconsigliato per produzione)
requests

# Da URL
https://example.com/pacchetto-1.0.tar.gz

# Da repository git
git+https://github.com/user/repo.git@main#egg=pacchetto
git+https://github.com/user/repo.git@v1.2.3#egg=pacchetto
git+ssh://git@github.com/user/repo.git@commit_hash#egg=pacchetto

# Dipendenze condizionali per piattaforma
pywin32>=300; sys_platform == "win32"
uvloop>=0.19.0; sys_platform != "win32"

# Includi un altro file di requirements
-r requirements-base.txt

# Vincoli da file esterno
-c constraints.txt
```

Installazione da requirements.txt:

```bash
pip install -r requirements.txt
```

#### Editable Install

L'installazione in modalita "editable" e fondamentale durante lo sviluppo:

```bash
# Installa il pacchetto corrente in modalita sviluppo
pip install -e .

# Con dipendenze extra
pip install -e ".[dev,test]"

# Da un percorso locale
pip install -e /percorso/al/pacchetto
```

In modalita editable, le modifiche al codice sorgente sono immediatamente disponibili senza reinstallazione. pip crea un collegamento al codice sorgente nella directory `site-packages` invece di copiare i file.

#### Installazione da Diverse Fonti

```bash
# Da PyPI (default)
pip install requests

# Da un file locale (wheel o sdist)
pip install ./pacchetto-1.0.0-py3-none-any.whl
pip install ./pacchetto-1.0.0.tar.gz

# Da un URL diretto
pip install https://files.example.com/pacchetto-1.0.0.tar.gz

# Da un repository Git
pip install git+https://github.com/user/repo.git
pip install git+https://github.com/user/repo.git@branch
pip install git+https://github.com/user/repo.git@tag
pip install git+https://github.com/user/repo.git@commit

# Da un indice privato
pip install --index-url https://pypi.privato.com/simple/ pacchetto
pip install --extra-index-url https://pypi.privato.com/simple/ pacchetto
```

### Gestione Dipendenze

#### Pattern requirements-dev.txt

Un pattern molto comune e separare le dipendenze di produzione da quelle di sviluppo:

```txt
# requirements.txt (produzione)
flask==3.0.2
sqlalchemy==2.0.25
gunicorn==21.2.0
```

```txt
# requirements-dev.txt (sviluppo)
-r requirements.txt
pytest==8.0.0
pytest-cov==4.1.0
mypy==1.8.0
ruff==0.2.0
black==24.1.0
pre-commit==3.6.0
```

```bash
# In produzione
pip install -r requirements.txt

# In sviluppo
pip install -r requirements-dev.txt
```

#### File di Constraints

I file di constraints fissano le versioni senza installare direttamente i pacchetti:

```txt
# constraints.txt
numpy==1.26.3
pandas==2.1.5
```

```bash
pip install -c constraints.txt scikit-learn
# scikit-learn verra installato, e se richiede numpy o pandas,
# verranno usate esattamente le versioni nel constraints file
```

I constraints sono utili per garantire coerenza nelle versioni delle dipendenze transitive in ambienti con molti progetti.

#### Hash Checking

Per ambienti ad alta sicurezza, pip supporta la verifica degli hash:

```txt
# requirements.txt con hash
requests==2.31.0 \
    --hash=sha256:942c5a758f98d790eaed1a29cb6eefc7f0edf3fcb0fce8aea3fbd5951d XXXX
```

```bash
# Generare requirements con hash
pip freeze | pip hash > requirements.txt

# Installare con verifica obbligatoria degli hash
pip install --require-hashes -r requirements.txt
```

L'opzione `--require-hashes` garantisce che ogni pacchetto installato corrisponda esattamente all'hash dichiarato, prevenendo attacchi di tipo supply chain.

### pip-tools

`pip-tools` e un insieme di utility che risolvono il problema fondamentale di `pip freeze`: la mancanza di distinzione tra dipendenze dirette e transitive.

```bash
pip install pip-tools
```

#### pip-compile

Trasforma un file `.in` con le dipendenze dirette in un file `.txt` completamente risolto:

```txt
# requirements.in (dipendenze dirette dichiarate dallo sviluppatore)
flask
sqlalchemy
celery
```

```bash
# Compila le dipendenze risolvendo tutte le versioni
pip-compile requirements.in

# Con una versione specifica di Python come target
pip-compile --python-version 3.12 requirements.in

# Aggiornare tutte le dipendenze
pip-compile --upgrade requirements.in

# Aggiornare un singolo pacchetto
pip-compile --upgrade-package flask requirements.in

# Generare hash per sicurezza
pip-compile --generate-hashes requirements.in
```

Il file generato `requirements.txt` conterrai pin esatti e annotazioni sulle dipendenze:

```txt
#
# This file is autogenerated by pip-compile with Python 3.12
# by the following command:
#
#    pip-compile requirements.in
#
blinker==1.7.0
    # via flask
celery==5.3.6
    # via -r requirements.in
click==8.1.7
    # via
    #   celery
    #   flask
flask==3.0.2
    # via -r requirements.in
# ... altre dipendenze con annotazioni
```

#### pip-sync

Sincronizza l'ambiente virtuale con il file requirements, **rimuovendo** i pacchetti non dichiarati:

```bash
# Sincronizzare con un singolo file
pip-sync requirements.txt

# Sincronizzare con piu file
pip-sync requirements.txt requirements-dev.txt
```

A differenza di `pip install -r`, `pip-sync` garantisce che l'ambiente contenga **esattamente** i pacchetti dichiarati, ne di piu ne di meno.

#### Layered Requirements

Un workflow comune con pip-tools prevede livelli di requirements:

```txt
# requirements.in
flask
sqlalchemy
```

```txt
# requirements-dev.in
-r requirements.in
pytest
mypy
ruff
```

```txt
# requirements-ci.in
-r requirements-dev.in
coverage
pytest-xdist
```

```bash
# Compilare in ordine
pip-compile requirements.in
pip-compile requirements-dev.in
pip-compile requirements-ci.in
```

#### Workflow Completo con pip-tools

```bash
# 1. Creare l'ambiente
python -m venv .venv
source .venv/bin/activate

# 2. Installare pip-tools
pip install pip-tools

# 3. Dichiarare le dipendenze dirette
echo "flask\nsqlalchemy" > requirements.in

# 4. Compilare (risolvere e fissare le versioni)
pip-compile requirements.in

# 5. Sincronizzare l'ambiente
pip-sync requirements.txt

# 6. Quando si aggiunge una dipendenza
echo "celery" >> requirements.in
pip-compile requirements.in
pip-sync requirements.txt

# 7. Aggiornamento periodico
pip-compile --upgrade requirements.in
pip-sync requirements.txt
```

---

## Poetry

Poetry e uno strumento completo per la gestione dei progetti Python che unifica la gestione delle dipendenze, il build system e la pubblicazione in un unico tool coerente.

### Fondamenti

#### Installazione

```bash
# Metodo raccomandato (installer ufficiale)
curl -sSL https://install.python-poetry.org | python3 -

# Con pipx (isolato dal sistema)
pipx install poetry

# Verifica
poetry --version
```

#### Creazione di un Progetto

```bash
# Creare un nuovo progetto da zero
poetry new mio-progetto
# Genera:
# mio-progetto/
# ├── pyproject.toml
# ├── README.md
# ├── mio_progetto/
# │   └── __init__.py
# └── tests/
#     └── __init__.py

# Inizializzare Poetry in un progetto esistente
cd progetto-esistente
poetry init
# Guida interattiva per configurare pyproject.toml
```

#### pyproject.toml

Il cuore di un progetto Poetry:

```toml
[tool.poetry]
name = "mio-progetto"
version = "0.1.0"
description = "Un progetto di esempio"
authors = ["Nome Cognome <email@esempio.com>"]
readme = "README.md"
license = "MIT"
packages = [{include = "mio_progetto"}]

[tool.poetry.dependencies]
python = "^3.10"
flask = "^3.0.0"
sqlalchemy = "^2.0.0"
requests = {version = "^2.31.0", optional = true}

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
mypy = "^1.8.0"
ruff = "^0.2.0"

[tool.poetry.group.test.dependencies]
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.23.0"
faker = "^22.0.0"

[tool.poetry.group.docs.dependencies]
sphinx = "^7.2.0"
sphinx-rtd-theme = "^2.0.0"

[tool.poetry.extras]
http = ["requests"]

[tool.poetry.scripts]
mio-cli = "mio_progetto.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### Comandi Essenziali

```bash
# Installare tutte le dipendenze (crea .venv e poetry.lock)
poetry install

# Installare senza le dipendenze di sviluppo
poetry install --without dev

# Installare solo un gruppo specifico
poetry install --only test

# Aggiungere una dipendenza
poetry add flask

# Aggiungere una dipendenza di sviluppo
poetry add --group dev pytest

# Aggiungere con vincoli
poetry add "requests>=2.28,<3.0"

# Rimuovere una dipendenza
poetry remove flask

# Aggiornare le dipendenze
poetry update

# Aggiornare un pacchetto specifico
poetry update flask

# Mostrare le dipendenze come albero
poetry show --tree

# Mostrare pacchetti obsoleti
poetry show --outdated

# Eseguire un comando nell'ambiente virtuale
poetry run python script.py
poetry run pytest

# Aprire una shell nell'ambiente virtuale
poetry shell
```

#### poetry.lock

Il file `poetry.lock` e generato automaticamente e contiene le versioni esatte di tutte le dipendenze (dirette e transitive) con i relativi hash. **Deve essere incluso nel version control** per garantire build riproducibili.

```bash
# Rigenerare il lock file senza installare
poetry lock

# Aggiornare il lock file con le ultime versioni compatibili
poetry lock --no-update  # Solo rigenera
poetry update            # Aggiorna e rigenera
```

### Funzionalita Avanzate

#### Gruppi di Dipendenze

I gruppi permettono di organizzare le dipendenze per scopo:

```toml
[tool.poetry.group.dev.dependencies]
ruff = "^0.2.0"
mypy = "^1.8.0"
pre-commit = "^3.6.0"

[tool.poetry.group.test.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"

[tool.poetry.group.docs.dependencies]
sphinx = "^7.2.0"

[tool.poetry.group.docs]
optional = true  # Non installato di default
```

```bash
# Installare tutto tranne docs
poetry install --without docs

# Installare solo test
poetry install --only test

# Installare includendo il gruppo opzionale docs
poetry install --with docs
```

#### Vincoli di Versione

Poetry supporta una sintassi ricca per i vincoli:

```toml
[tool.poetry.dependencies]
# Caret (^): permette aggiornamenti che non cambiano la cifra non-zero piu a sinistra
flask = "^3.0.0"        # >=3.0.0, <4.0.0
celery = "^5.3.6"       # >=5.3.6, <6.0.0
utils = "^0.2.3"        # >=0.2.3, <0.3.0 (attenzione: versioni 0.x!)

# Tilde (~): permette aggiornamenti patch
flask = "~3.0.0"        # >=3.0.0, <3.1.0
flask = "~3.0"          # >=3.0.0, <3.1.0

# Esatta
flask = "3.0.2"         # Esattamente 3.0.2

# Wildcard
flask = "3.0.*"         # >=3.0.0, <3.1.0

# Intervalli
flask = ">=3.0.0,<3.2.0"

# Combinazioni
flask = ">=3.0.0,<4.0.0,!=3.0.1"
```

#### Extras

Gli extras permettono di installare dipendenze opzionali:

```toml
[tool.poetry.extras]
postgres = ["psycopg2-binary"]
redis = ["redis", "hiredis"]
all = ["psycopg2-binary", "redis", "hiredis"]
```

```bash
# Installare con extras
poetry install --extras "postgres redis"
poetry install --all-extras
```

#### Scripts

Definire comandi eseguibili:

```toml
[tool.poetry.scripts]
mio-cli = "mio_progetto.cli:main"
migrate = "mio_progetto.db:run_migrations"
```

Dopo l'installazione, `mio-cli` sara disponibile come comando nel PATH.

#### Pubblicazione su PyPI

```bash
# Build del pacchetto
poetry build
# Genera dist/mio-progetto-0.1.0.tar.gz e dist/mio_progetto-0.1.0-py3-none-any.whl

# Configurare le credenziali PyPI
poetry config pypi-token.pypi pypi-xxxxxxxxxxxxxxxx

# Pubblicare
poetry publish

# Build e pubblicazione in un passo
poetry publish --build

# Pubblicare su un repository privato
poetry config repositories.privato https://pypi.privato.com/simple/
poetry publish --repository privato
```

#### Gestione degli Ambienti Virtuali

```bash
# Poetry crea automaticamente l'ambiente in una directory centralizzata
# Per cambiare questo comportamento e creare .venv nel progetto:
poetry config virtualenvs.in-project true

# Vedere il percorso dell'ambiente virtuale
poetry env info

# Elencare gli ambienti
poetry env list

# Usare una versione specifica di Python
poetry env use python3.12

# Rimuovere un ambiente
poetry env remove python3.12
```

---

## uv (Il Futuro)

`uv` e uno strumento scritto in Rust dal team di Astral (creatori di Ruff) che mira a sostituire `pip`, `pip-tools`, `virtualenv`, `pipx` e gestire interi progetti Python. La sua velocita e l'aspetto piu evidente: le operazioni sono tipicamente **10-100 volte piu veloci** rispetto agli equivalenti in pip.

### Fondamenti

#### Installazione

```bash
# Installer ufficiale (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Con pip (se necessario)
pip install uv

# Con Homebrew
brew install uv

# Verifica
uv --version
```

#### Comandi Base

```bash
# Creare un ambiente virtuale
uv venv

# Creare con una versione specifica di Python
uv venv --python 3.12

# Creare con nome personalizzato
uv venv .venv-test

# Installare pacchetti (compatibile con pip)
uv pip install flask
uv pip install -r requirements.txt

# Disinstallare
uv pip uninstall flask

# Elencare pacchetti
uv pip list

# Congelare
uv pip freeze

# Compilare requirements (come pip-compile)
uv pip compile requirements.in -o requirements.txt

# Sincronizzare (come pip-sync)
uv pip sync requirements.txt
```

#### Confronto di Velocita con pip

Per dare un'idea concreta delle differenze di performance:

```
Operazione               pip          uv
-----------------------------------------
Creare venv              2.5s         0.01s
Installare flask         8.2s         0.4s
Installare numpy         12.1s        0.8s
pip-compile (50 deps)    45s          1.2s
Risolvere dipendenze     30s+         <1s
Cold install (no cache)  120s         5s
```

Queste differenze diventano particolarmente significative nelle pipeline CI/CD, dove il tempo di installazione delle dipendenze puo rappresentare una parte sostanziale del tempo totale di build.

#### uv run

`uv run` esegue un comando nell'ambiente del progetto, creandolo automaticamente se necessario:

```bash
# Esegue uno script Python nel contesto del progetto
uv run python script.py

# Esegue pytest
uv run pytest

# Esegue con dipendenze aggiuntive temporanee
uv run --with httpx python script.py

# Esegue uno script con dipendenze inline (PEP 723)
uv run script_con_deps.py
```

### Gestione Progetti

#### Inizializzazione

```bash
# Inizializzare un nuovo progetto
uv init mio-progetto

# Inizializzare nella directory corrente
uv init

# Inizializzare come libreria
uv init --lib mio-progetto

# Struttura generata
# mio-progetto/
# ├── pyproject.toml
# ├── README.md
# └── src/
#     └── mio_progetto/
#         └── __init__.py
```

Il `pyproject.toml` generato:

```toml
[project]
name = "mio-progetto"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Gestione Dipendenze

```bash
# Aggiungere una dipendenza
uv add flask
uv add "sqlalchemy>=2.0"

# Aggiungere una dipendenza di sviluppo
uv add --dev pytest ruff mypy

# Aggiungere un gruppo di dipendenze
uv add --group test pytest-cov faker

# Rimuovere una dipendenza
uv remove flask

# Aggiornare le dipendenze
uv lock --upgrade

# Sincronizzare l'ambiente con il lock file
uv sync
```

#### uv.lock

Il file `uv.lock` e l'equivalente di `poetry.lock`: contiene le versioni esatte risolte di tutte le dipendenze. E generato automaticamente e deve essere committato nel version control.

```bash
# Generare/aggiornare il lock file
uv lock

# Aggiornare un pacchetto specifico
uv lock --upgrade-package flask

# Installare esattamente le versioni nel lock
uv sync
```

#### uv tool (Sostituto di pipx)

`uv tool` gestisce strumenti CLI installati globalmente in ambienti isolati:

```bash
# Installare uno strumento CLI
uv tool install ruff
uv tool install black
uv tool install httpie

# Eseguire uno strumento senza installarlo permanentemente
uv tool run cowsay "Ciao!"
uvx cowsay "Ciao!"  # Alias per uv tool run

# Elencare strumenti installati
uv tool list

# Aggiornare
uv tool upgrade ruff

# Disinstallare
uv tool uninstall ruff
```

#### Gestione delle Versioni di Python

`uv` puo anche gestire le installazioni di Python, sostituendo parzialmente `pyenv`:

```bash
# Installare una versione di Python
uv python install 3.12

# Elencare le versioni disponibili
uv python list

# Fissare la versione per il progetto
uv python pin 3.12
```

---

## Pyenv

`pyenv` e lo strumento di riferimento per gestire **multiple versioni di Python** sulla stessa macchina. Non gestisce pacchetti o ambienti virtuali (a meno di usare il plugin `pyenv-virtualenv`), ma si concentra esclusivamente sulla gestione dell'interprete.

### Installazione

```bash
# Linux/macOS con installer automatico
curl https://pyenv.run | bash

# macOS con Homebrew
brew install pyenv

# Aggiungere al profilo della shell (~/.bashrc o ~/.zshrc)
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Su Linux, prima di compilare Python, installare le dipendenze di build:

```bash
# Debian/Ubuntu
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev
```

### Gestione delle Versioni di Python

```bash
# Elencare tutte le versioni installabili
pyenv install --list

# Filtrare per versione
pyenv install --list | grep "3.12"

# Installare una versione
pyenv install 3.12.3

# Installare piu versioni
pyenv install 3.11.8
pyenv install 3.10.14

# Elencare le versioni installate
pyenv versions

# Disinstallare
pyenv uninstall 3.10.14
```

### Selezione della Versione

pyenv offre tre livelli di priorita per la selezione della versione:

```bash
# Globale (default per tutto il sistema utente)
pyenv global 3.12.3

# Locale (per la directory corrente e sottodirectory)
pyenv local 3.11.8
# Crea un file .python-version nella directory corrente

# Shell (solo per la sessione corrente)
pyenv shell 3.10.14

# Verificare quale versione e attiva
pyenv version
python --version
```

L'ordine di priorita e: **shell > local > global**.

### File .python-version

Quando si esegue `pyenv local 3.12.3`, viene creato un file `.python-version` nella directory corrente:

```
3.12.3
```

Questo file va incluso nel version control per garantire che tutto il team usi la stessa versione di Python. Molti strumenti moderni (incluso `uv`) riconoscono questo file.

### Plugin pyenv-virtualenv

Il plugin aggiunge la gestione degli ambienti virtuali a pyenv:

```bash
# Installazione
git clone https://github.com/pyenv/pyenv-virtualenv.git \
  $(pyenv root)/plugins/pyenv-virtualenv

# Aggiungere al profilo della shell
eval "$(pyenv virtualenv-init -)"

# Creare un ambiente virtuale
pyenv virtualenv 3.12.3 mio-progetto

# Attivare
pyenv activate mio-progetto

# Impostare come locale (attivazione automatica)
pyenv local mio-progetto

# Disattivare
pyenv deactivate

# Elencare ambienti
pyenv virtualenvs

# Eliminare
pyenv virtualenv-delete mio-progetto
```

---

## conda

`conda` e un sistema di gestione dei pacchetti e degli ambienti che va oltre Python: puo gestire pacchetti in qualsiasi linguaggio e, soprattutto, gestisce le dipendenze binarie e le librerie C/C++ in modo nativo.

### Miniconda vs Anaconda

- **Miniconda**: installazione minimale che include solo `conda`, Python e pochi pacchetti base. **Raccomandato** per la maggior parte degli usi.
- **Anaconda**: distribuzione completa che include circa 250+ pacchetti preinstallati (NumPy, Pandas, Scikit-learn, Jupyter, ecc.). Occupa diversi GB di spazio. Utile per chi vuole tutto pronto all'uso.

```bash
# Installare Miniconda (Linux)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### Comandi Principali

```bash
# Creare un ambiente
conda create --name mio-ambiente python=3.12

# Creare con pacchetti iniziali
conda create --name data-science python=3.12 numpy pandas matplotlib

# Attivare
conda activate mio-ambiente

# Disattivare
conda deactivate

# Installare pacchetti
conda install numpy pandas scikit-learn

# Installare da un canale specifico
conda install -c conda-forge opencv

# Aggiornare
conda update numpy
conda update --all

# Elencare pacchetti
conda list

# Elencare ambienti
conda env list

# Rimuovere un ambiente
conda env remove --name mio-ambiente

# Esportare l'ambiente
conda env export > environment.yml

# Ricreare da file
conda env create -f environment.yml
```

### environment.yml

Il file dichiarativo per gli ambienti conda:

```yaml
name: mio-progetto
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - numpy=1.26.*
  - pandas=2.1.*
  - scikit-learn=1.4.*
  - matplotlib=3.8.*
  - jupyter=1.0.*
  # Pacchetti pip (per quelli non disponibili su conda)
  - pip:
    - fastapi==0.109.0
    - uvicorn==0.27.0
```

### conda vs pip

| Aspetto | conda | pip |
|---------|-------|-----|
| Linguaggi | Multi-linguaggio | Solo Python |
| Dipendenze C/C++ | Gestite nativamente | Richiede compilazione |
| Risoluzione | SAT solver | Resolver (dal 2020) |
| Repository | Anaconda/conda-forge | PyPI |
| Ambienti | Integrato | Richiede venv separato |
| Velocita | Lento | Medio (uv: veloce) |

### Quando Usare conda

conda e particolarmente indicato in queste situazioni:

- **Data Science e Machine Learning**: librerie come NumPy, SciPy, TensorFlow e PyTorch hanno dipendenze C/Fortran complesse che conda gestisce nativamente.
- **Dipendenze non-Python**: quando il progetto necessita di librerie come CUDA, OpenCV, GDAL o FFmpeg.
- **Ambienti cross-platform**: conda garantisce compatibilita binaria tra sistemi operativi.
- **Calcolo scientifico**: ambienti con MKL, BLAS, LAPACK ottimizzati.

**Consiglio pratico**: usare conda per le dipendenze "pesanti" (librerie con estensioni C) e pip per i pacchetti puramente Python all'interno dell'ambiente conda.

---

## pipx

`pipx` e uno strumento specializzato nell'installazione di **applicazioni CLI Python** in ambienti virtuali isolati. Ogni strumento installato vive nel proprio ambiente, evitando conflitti tra le dipendenze dei diversi tool.

### Installazione

```bash
# Con pip
pip install --user pipx
pipx ensurepath

# Su Ubuntu/Debian
sudo apt install pipx
pipx ensurepath

# Con Homebrew
brew install pipx
pipx ensurepath
```

### Comandi Principali

```bash
# Installare uno strumento CLI
pipx install black
pipx install ruff
pipx install httpie
pipx install cookiecutter

# Eseguire uno strumento senza installarlo (temporaneo)
pipx run cowsay "Ciao dal mondo Python!"
pipx run --python 3.11 black --check .

# Iniettare dipendenze aggiuntive in un ambiente esistente
pipx inject jupyterlab jupyterlab-vim
pipx inject ansible boto3

# Elencare strumenti installati
pipx list

# Aggiornare
pipx upgrade black
pipx upgrade-all

# Disinstallare
pipx uninstall black

# Reinstallare tutti (utile dopo upgrade di Python)
pipx reinstall-all
```

### Casi d'Uso Tipici

pipx e ideale per:

- **Linter e formatter**: `ruff`, `black`, `isort`, `flake8`, `mypy`
- **Strumenti di progetto**: `cookiecutter`, `pre-commit`, `tox`, `nox`
- **Utility di rete**: `httpie`, `glances`, `pgcli`
- **Strumenti di documentazione**: `sphinx`, `mkdocs`

La regola pratica e: se uno strumento e un **comando da terminale** che si usa in diversi progetti, installarlo con `pipx`. Se e una **libreria** che viene importata nel codice, installarlo con `pip` nell'ambiente virtuale del progetto.

**Nota**: `uv tool` e il successore spirituale di `pipx`, con la stessa funzionalita ma velocita molto superiore.

---

## Confronto Strumenti

| Strumento | Scopo Principale | Pro | Contro |
|-----------|-----------------|-----|--------|
| **venv + pip** | Ambiente base + installazione pacchetti | Incluso nella stdlib; nessuna dipendenza esterna; semplice da capire | Nessun lock file; no distinzione dipendenze dirette/transitive; risoluzione lenta |
| **pip-tools** | Gestione requirements evoluta | Distinzione dirette/transitive; pin deterministici; pip-sync per pulizia | Richiede installazione separata; no gestione ambienti; no build system |
| **Poetry** | Gestione completa del progetto | All-in-one (deps, build, publish); lock file; gruppi di dipendenze; ottimo DX | Risoluzione lenta; curva di apprendimento; a volte conflitti con l'ecosistema pyproject.toml |
| **uv** | Sostituto universale veloce | Estremamente veloce (10-100x); sostituisce pip, pip-tools, venv, pipx; gestione Python integrata | Progetto giovane; ecosistema plugin limitato; alcune funzionalita ancora in evoluzione |
| **conda** | Ambienti multi-linguaggio | Gestisce dipendenze C/Fortran; ottimo per data science; cross-platform | Lento; repository separato da PyPI; ambienti pesanti; risoluzione complessa |
| **pipx** | Strumenti CLI isolati | Isolamento perfetto per tool CLI; semplice | Solo per applicazioni CLI; non per librerie |

### Quale Scegliere?

- **Principiante o progetto semplice**: `venv` + `pip` con `requirements.txt`
- **Progetto medio con team**: `pip-tools` o `Poetry`
- **Progetto nuovo nel 2025/2026**: `uv` (la direzione dell'ecosistema)
- **Data science / ML**: `conda` (Miniconda) + `pip` per pacchetti Python-only
- **Strumenti CLI globali**: `pipx` o `uv tool`

### uv vs Poetry vs PDM vs Hatch — Confronto Dettagliato

Oltre agli strumenti trattati nelle sezioni precedenti, l'ecosistema Python include anche **PDM** e **Hatch**, entrambi meritevoli di attenzione. PDM (Python Development Master) segue fedelmente gli standard PEP ed offre un approccio simile a npm per Python, con supporto opzionale per ambienti senza virtualenv tramite PEP 582 (sperimentale). Hatch e il progetto ufficiale della Python Packaging Authority (PyPA) per il build system `hatchling`, e include un task runner, gestione ambienti multipli e versionamento automatico.

La tabella seguente confronta i quattro strumenti su dimensioni chiave per la scelta in un progetto reale:

| Caratteristica | **uv** | **Poetry** | **PDM** | **Hatch** |
|----------------|--------|------------|---------|-----------|
| **Linguaggio** | Rust | Python | Python | Python |
| **Velocita installazione** | 10-100x pip | ~1x pip | ~2x pip | ~1x pip |
| **Aderenza PEP 621** | Completa | Parziale (`[tool.poetry]`) | Completa | Completa |
| **PEP 735 (dependency groups)** | Si (0.4.27+) | No (issue aperta) | Si (2.20+) | No |
| **PEP 723 (inline scripts)** | Si (`uv run`) | No | No | No |
| **Lock file** | `uv.lock` (TOML) | `poetry.lock` (TOML) | `pdm.lock` (TOML) | Nessuno nativo |
| **Build backend** | `uv_build` / `hatchling` | `poetry-core` | `pdm-backend` | `hatchling` |
| **Gestione Python** | Si (`uv python install`) | No | No | No |
| **Workspace/monorepo** | Si (`tool.uv.workspace`) | No (multi-project limitato) | No | Si (ambienti multipli) |
| **Sostituto pipx** | Si (`uv tool`) | No | No | No |
| **Pubblicazione PyPI** | Si (`uv publish`) | Si (`poetry publish`) | Si (`pdm publish`) | Si (`hatch publish`) |
| **Plugin ecosystem** | Limitato | Ampio | Medio | Medio |
| **Maturita** | Giovane (2024) | Maturo (2018) | Maturo (2021) | Maturo (2022) |
| **Task runner** | No | No | Si (`pdm run`) | Si (`hatch run`) |

**Raccomandazioni per scenario:**

- **Nuovo progetto greenfield (2025+):** `uv` e la scelta predefinita. Velocita superiore, aderenza agli standard, gestione Python integrata e lock file cross-platform. Il progetto e giovane ma sostenuto da Astral (stesso team di Ruff) con finanziamenti significativi e adozione in rapida crescita.

- **Progetto esistente con Poetry:** nessuna urgenza di migrare. Poetry e maturo, ben documentato e ha un ecosistema di plugin consolidato. La migrazione a uv e possibile ma non necessaria finche Poetry soddisfa le esigenze del team. Il punto debole principale di Poetry e la non-conformita a PEP 621: usa `[tool.poetry.dependencies]` invece di `[project.dependencies]`, creando lock-in nell'ecosistema Poetry.

- **Progetto che richiede aderenza rigorosa agli standard:** `PDM` o `uv`. Entrambi seguono PEP 621, PEP 631 e PEP 735. PDM offre un task runner integrato e un'esperienza simile a npm/yarn. `uv` aggiunge velocita e gestione Python, ma ha un ecosistema plugin piu limitato.

- **Sviluppo di librerie con ambienti test multipli:** `Hatch`. Il sistema di ambienti di Hatch permette di definire matrici di test (versioni Python, dipendenze opzionali) direttamente nella configurazione, senza bisogno di tox o nox. Come build backend, `hatchling` e lo standard de facto raccomandato dal PyPA.

- **Benchmark di velocita reale** (installazione Django + Celery + Pandas + scikit-learn):

| Tool | Tempo | Fattore |
|------|-------|---------|
| uv | ~8s | 1x |
| PDM | ~38s | 4.7x |
| Poetry | ~50s | 6.2x |
| pip | ~90s | 11.2x |

Questi numeri si traducono direttamente in tempi di CI piu brevi e in un'esperienza di sviluppo piu fluida, soprattutto per i progetti con molte dipendenze.

---

## Docker come Environment

Docker offre un livello di isolamento superiore agli ambienti virtuali: non solo le dipendenze Python, ma l'intero sistema operativo e riproducibile.

### Dockerfile per Progetti Python

Un Dockerfile di base per un'applicazione Python:

```dockerfile
FROM python:3.12-slim

# Impostare variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Installare dipendenze di sistema se necessario
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiare e installare dipendenze prima del codice (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiare il codice sorgente
COPY . .

# Esporre la porta
EXPOSE 8000

# Comando di avvio
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000"]
```

### Multi-Stage Build

Le build multi-stage riducono drasticamente la dimensione dell'immagine finale:

```dockerfile
# ---- Stage 1: Build ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Installare dipendenze di build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Creare un virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Installare dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: Runtime ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Installare solo le librerie runtime necessarie
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiare il virtual environment dal builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiare il codice sorgente
COPY . .

# Utente non-root per sicurezza
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

Con `uv` le build Docker diventano ancora piu veloci:

```dockerfile
FROM python:3.12-slim

# Installare uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copiare file di progetto
COPY pyproject.toml uv.lock ./

# Installare dipendenze (sfrutta la cache Docker)
RUN uv sync --frozen --no-dev --no-install-project

# Copiare codice sorgente
COPY . .

# Installare il progetto
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "gunicorn", "app:create_app()", "--bind", "0.0.0.0:8000"]
```

### .dockerignore

Essenziale per evitare di copiare file non necessari nel contesto di build:

```
# Ambienti virtuali
.venv/
venv/
env/

# Cache Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/

# File di configurazione locale
.env
*.local

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# Test e documentazione
tests/
docs/
*.md
```

### Immagini di Sviluppo vs Produzione

```yaml
# docker-compose.yml
services:
  # Immagine di sviluppo
  app-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app                    # Mount del codice per hot-reload
      - /app/.venv                # Escludere il venv dal mount
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
    ports:
      - "8000:8000"
      - "5678:5678"              # Debugger

  # Immagine di produzione
  app-prod:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - FLASK_ENV=production
    ports:
      - "8000:8000"
    restart: unless-stopped
```

---

## Best Practices

### 1. Usare Sempre un Ambiente Virtuale

Non installare mai pacchetti nel Python di sistema. Ogni progetto, anche il piu piccolo, merita il proprio ambiente isolato. Su molte distribuzioni Linux, installare pacchetti globalmente con pip puo corrompere strumenti di sistema.

```bash
# Primo passo di ogni nuovo progetto
python -m venv .venv
source .venv/bin/activate
```

### 2. Fissare le Versioni delle Dipendenze

Per le **applicazioni** (web app, servizi, script), usare versioni esatte (pinning). Per le **librerie** destinate ad essere importate da altri, usare vincoli piu flessibili.

```txt
# Applicazione: versioni esatte
flask==3.0.2
sqlalchemy==2.0.25

# Libreria (pyproject.toml): vincoli flessibili
[project]
dependencies = [
    "requests>=2.28,<3",
]
```

### 3. Committare i Lock File

I file `poetry.lock`, `uv.lock` o i `requirements.txt` generati da `pip-compile` devono essere inclusi nel version control. Garantiscono che ogni sviluppatore e ogni ambiente (CI, staging, produzione) usi esattamente le stesse versioni.

### 4. Separare le Dipendenze per Ambiente

Mantenere separate le dipendenze di produzione, sviluppo e test:

```bash
# Con pip-tools
requirements.in          # Produzione
requirements-dev.in      # Sviluppo (include produzione)
requirements-test.in     # Test (include sviluppo)

# Con Poetry / uv
[tool.poetry.group.dev.dependencies]   # o [dependency-groups] con uv
[tool.poetry.group.test.dependencies]
```

### 5. Non Committare l'Ambiente Virtuale

L'ambiente virtuale e un artefatto locale e non va mai incluso nel repository. Assicurarsi che `.venv/` sia nel `.gitignore`:

```gitignore
# Ambienti virtuali
.venv/
venv/
env/
.env/
```

### 6. Aggiornare Regolarmente le Dipendenze

Le dipendenze obsolete rappresentano un rischio di sicurezza. Stabilire una cadenza regolare (settimanale o bisettimanale) per controllare e applicare gli aggiornamenti:

```bash
# Controllare aggiornamenti disponibili
pip list --outdated
poetry show --outdated
uv pip list --outdated

# Aggiornare con pip-tools
pip-compile --upgrade requirements.in

# Aggiornare con Poetry
poetry update

# Aggiornare con uv
uv lock --upgrade
```

Utilizzare strumenti come Dependabot o Renovate per automatizzare la creazione di pull request con gli aggiornamenti delle dipendenze.

### 7. Specificare la Versione di Python

Dichiarare sempre la versione di Python richiesta dal progetto:

```toml
# pyproject.toml
[project]
requires-python = ">=3.10"
```

```
# .python-version (per pyenv/uv)
3.12.3
```

Questo evita errori difficili da diagnosticare causati dall'uso di una versione di Python incompatibile.

### 8. Usare pyproject.toml come Fonte Unica di Verita

Il formato `pyproject.toml` (PEP 621) e lo standard moderno per la configurazione dei progetti Python. Consolidare qui tutte le informazioni: metadati, dipendenze, configurazione degli strumenti.

```toml
[project]
name = "mio-progetto"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "flask>=3.0",
    "sqlalchemy>=2.0",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 88

[tool.mypy]
strict = true
```

### 9. Verificare la Riproducibilita

Periodicamente, testare che l'ambiente possa essere ricreato da zero:

```bash
# Eliminare l'ambiente
rm -rf .venv

# Ricreare
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # o poetry install, o uv sync

# Verificare che tutto funzioni
pytest
```

Questo passaggio e fondamentale anche nelle pipeline CI/CD, dove l'ambiente viene sempre creato da zero.

### 10. Documentare la Procedura di Setup

Nel README del progetto, includere sempre istruzioni chiare per configurare l'ambiente di sviluppo:

```bash
# Setup del progetto
git clone https://github.com/utente/progetto.git
cd progetto
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
pytest  # Verificare che tutto funzioni
```

Con strumenti piu moderni, il setup si semplifica enormemente:

```bash
# Con uv
git clone https://github.com/utente/progetto.git
cd progetto
uv sync
uv run pytest
```

Piu semplice e la procedura di setup, piu velocemente un nuovo membro del team diventa produttivo.

---

## Internals di venv

Questa sezione approfondisce i meccanismi interni di `venv`, utili per diagnosticare problemi e comprendere come l'isolamento viene effettivamente implementato a livello di interprete CPython.

### Algoritmo di startup discovery

Quando si avvia l'interprete Python, prima ancora di eseguire il codice utente, CPython esegue una procedura di **startup discovery** per determinare i percorsi di ricerca dei moduli. La sequenza, definita in `Modules/getpath.py` nel sorgente CPython, funziona cosi:

1. **Trova l'eseguibile**: CPython determina il percorso assoluto del binario `python` in esecuzione, risolvendo eventuali symlink.
2. **Cerca `pyvenv.cfg`**: a partire dalla directory dell'eseguibile, risale la gerarchia alla ricerca del file `pyvenv.cfg`. Se il binario e in `.venv/bin/python`, cerca `.venv/pyvenv.cfg` e poi `.venv/bin/pyvenv.cfg`.
3. **Applica la configurazione**: se `pyvenv.cfg` viene trovato, i suoi campi vengono letti e usati per configurare `sys.prefix`, `sys.exec_prefix` e `sys.path`.
4. **Configura site-packages**: il modulo `site` (caricato automaticamente all'avvio) usa `sys.prefix` per aggiungere il `site-packages` corretto a `sys.path`.

Questo meccanismo spiega perche l'attivazione del venv non e strettamente necessaria: basta invocare direttamente `.venv/bin/python` e l'interprete scoprira automaticamente l'ambiente.

```bash
# Queste due invocazioni sono equivalenti:
source .venv/bin/activate && python script.py
.venv/bin/python script.py
```

La differenza e che `activate` modifica anche `PATH` e la variabile `VIRTUAL_ENV`, che alcuni tool (pip, uv, IDE) usano per rilevare l'ambiente attivo.

### Il file pyvenv.cfg in dettaglio

Il file `pyvenv.cfg` e un semplice file chiave-valore (formato INI senza sezioni). I campi riconosciuti da CPython 3.12+ sono:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `home` | path | Directory contenente l'interprete Python di base (non il symlink). CPython usa questo valore per localizzare la standard library. |
| `include-system-site-packages` | bool | Se `true`, l'ambiente ha accesso anche ai pacchetti installati nel Python di sistema. Default: `false`. |
| `version` | stringa | Versione di Python usata per creare il venv (informativa). |
| `executable` | path | Percorso completo all'eseguibile Python di base. Aggiunto in Python 3.11. |
| `command` | stringa | Il comando usato per creare il venv. Aggiunto in Python 3.11, puramente informativo. |
| `prompt` | stringa | Il testo mostrato nel prompt della shell quando il venv e attivo. Se omesso, viene usato il nome della directory. |

Esempio completo di `pyvenv.cfg`:

```ini
home = /usr/bin
include-system-site-packages = false
version = 3.12.3
executable = /usr/bin/python3.12
command = /usr/bin/python3.12 -m venv --prompt mio-prog /home/user/progetto/.venv
prompt = mio-prog
```

Il campo `home` e il piu critico: se diventa invalido (ad esempio dopo la disinstallazione della versione di Python usata), l'intero venv smette di funzionare. In questo caso, la soluzione e ricreare il venv con la nuova versione di Python.

### Symlink vs copia

Su Linux e macOS, `venv` crea per default **symlink** al binario Python di sistema. Su Windows, dove i symlink richiedono privilegi speciali, `venv` **copia** il binario.

```bash
# Verifica se il binario e un symlink
ls -la .venv/bin/python
# lrwxrwxrwx 1 user user 16 Jan 15 10:00 .venv/bin/python -> /usr/bin/python3.12

# Il flag --copies forza la copia anche su Linux
python -m venv --copies .venv
```

La strategia symlink ha due vantaggi: la creazione e quasi istantanea e lo spazio su disco e trascurabile. Lo svantaggio e che il venv dipende dall'installazione di sistema: se si aggiorna Python (ad esempio da 3.12.3 a 3.12.4), il symlink punta automaticamente alla nuova versione. Questo e generalmente positivo per le patch release, ma puo causare problemi se si disinstalla completamente la versione originale.

### Lo script activate dissezionato

Lo script `activate` per bash esegue queste operazioni:

1. Salva il `PATH` corrente in `_OLD_VIRTUAL_PATH`.
2. Salva il `PS1` (prompt) corrente in `_OLD_VIRTUAL_PS1`.
3. Imposta la variabile `VIRTUAL_ENV` al percorso assoluto del venv.
4. Prepone `$VIRTUAL_ENV/bin` al `PATH`.
5. Modifica `PS1` per mostrare il nome dell'ambiente.
6. Disabilita `PYTHONHOME` se impostato (altrimenti interferirebbe con il venv).
7. Definisce la funzione `deactivate` che ripristina tutte le variabili originali.

```bash
# Verificare le variabili dopo l'attivazione
echo $VIRTUAL_ENV    # /home/user/progetto/.venv
echo $PATH           # /home/user/progetto/.venv/bin:/usr/bin:...
which python         # /home/user/progetto/.venv/bin/python
python -c "import sys; print(sys.prefix)"   # /home/user/progetto/.venv
python -c "import sys; print(sys.base_prefix)"  # /usr
```

La distinzione tra `sys.prefix` e `sys.base_prefix` e il meccanismo fondamentale: in un venv, `sys.prefix` punta al venv mentre `sys.base_prefix` punta all'installazione originale. Nel Python di sistema, sono identici. Questa distinzione e usata da pip per determinare dove installare i pacchetti.

### Ricreare un venv rotto

Un venv puo rompersi per diversi motivi: versione di Python rimossa, venv spostato su un percorso diverso, aggiornamento di sistema. La soluzione standard:

```bash
# Opzione 1: ricreare con --clear (sovrascrive)
python -m venv --clear .venv

# Opzione 2: aggiornare (mantiene i pacchetti installati)
python -m venv --upgrade .venv

# Opzione 3: eliminare e ricreare da lock file
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # o uv sync, o poetry install
```

L'opzione `--upgrade` e utile quando si aggiorna Python da una patch release alla successiva (es. 3.12.3 -> 3.12.4). Aggiorna il binario e `pyvenv.cfg` senza toccare `site-packages`.

### Differenze con virtualenv

Il pacchetto `virtualenv` (terze parti) offre funzionalita aggiuntive rispetto al `venv` della stdlib:

| Aspetto | venv (stdlib) | virtualenv |
|---------|---------------|------------|
| Creazione | Medio-lenta | Veloce (seed con app-data) |
| Python discover | Solo il Python corrente | Cerca tutte le versioni installate |
| Plugin | Nessuno | Supporto plugin via setuptools |
| Seed packages | pip + setuptools | Configurabile (pip/setuptools/wheel) |
| Cross-version | No | Si (puo creare venv per Python diversi) |
| Copia vs symlink | Configurabile | Configurabile, default piu intelligente |
| Attivazione | bash/fish/csh/nushell | bash/fish/csh/PowerShell/nushell/batch |

Per la maggior parte dei progetti, `venv` e sufficiente. `virtualenv` e utile quando si necessita di velocita nella creazione ripetuta di venv (test matrix, CI) o di supporto cross-version.

---

## uv Deep Dive

Questa sezione approfondisce le funzionalita avanzate di `uv` che vanno oltre i comandi base gia coperti.

### Architettura interna

`uv` e scritto interamente in Rust e compila in un singolo binario statico senza dipendenze runtime. L'architettura sfrutta:

- **Parallelismo**: download, decompressione e installazione avvengono in parallelo su tutti i core disponibili.
- **Cache globale**: tutti i pacchetti scaricati sono cached in `~/.cache/uv/` (Linux) o `~/Library/Caches/uv/` (macOS). La cache e condivisa tra tutti i progetti.
- **Copy-on-Write / Hardlink**: quando possibile, uv usa hardlink o CoW (su filesystem APFS/Btrfs) invece di copiare i file, rendendo le installazioni quasi istantanee se il pacchetto e gia in cache.
- **Resolver PubGrub**: l'algoritmo di risoluzione delle dipendenze e basato su PubGrub (lo stesso usato da Dart/pub), noto per produrre messaggi di errore chiari quando la risoluzione fallisce.

### uv venv — dettagli

```bash
# Crea venv con seed packages (pip)
uv venv --seed

# Crea venv con prompt personalizzato
uv venv --prompt "api-server"

# Crea venv con versione Python specifica (scarica se necessario)
uv venv --python 3.13

# Crea venv in una directory specifica
uv venv /tmp/test-env

# Crea venv senza relocatable path (per containerizzazione)
uv venv --python 3.12 --relocatable
```

Il flag `--seed` installa pip nel venv, necessario solo se si intende usare `pip install` manualmente all'interno dell'ambiente. Per il workflow `uv pip install`, pip non e necessario.

### uv pip compile — pip-tools compatibile

`uv pip compile` e un sostituto drop-in di `pip-compile` con la stessa interfaccia ma velocita molto superiore:

```bash
# Compilazione base
uv pip compile requirements.in -o requirements.txt

# Con hash per verifica integrita
uv pip compile --generate-hashes requirements.in -o requirements.txt

# Target specifico di Python (cross-compilation)
uv pip compile --python-version 3.11 requirements.in -o requirements.txt

# Target specifico di piattaforma
uv pip compile --python-platform linux requirements.in -o requirements.txt

# Annotazioni minime (senza commenti sulle dipendenze transitive)
uv pip compile --no-annotate requirements.in -o requirements.txt

# Aggiornamento selettivo
uv pip compile --upgrade-package flask requirements.in -o requirements.txt

# Output in formato uv (con marker resolution)
uv pip compile --universal requirements.in -o requirements.txt
```

Il flag `--universal` produce un lock file che funziona su tutte le piattaforme, includendo i marker di piattaforma per le dipendenze condizionali. Questo e particolarmente utile per i team con sviluppatori su sistemi operativi diversi.

### uv pip sync

```bash
# Sincronizza l'ambiente con il file requirements
uv pip sync requirements.txt

# Sincronizza nel Python di sistema (utile in Docker)
uv pip sync --system requirements.txt

# Sincronizza con verifica hash
uv pip sync --require-hashes requirements.txt
```

Il flag `--system` e fondamentale per Docker: installa i pacchetti direttamente nel Python del container senza creare un venv, comportamento desiderato nei Dockerfile dove il container stesso e l'ambiente isolato.

### uv run — PEP 723 inline script metadata

PEP 723 permette di dichiarare le dipendenze direttamente nello script Python. `uv run` le rileva e crea automaticamente un ambiente temporaneo:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
#     "rich>=13.0",
# ]
# ///

import httpx
from rich import print as rprint

response = httpx.get("https://httpbin.org/get")
rprint(response.json())
```

```bash
# uv rileva il blocco PEP 723 e installa le dipendenze automaticamente
uv run script_con_deps.py
```

Questo pattern e ideale per script standalone, notebook-like workflows e automazione. Non serve `pyproject.toml`, non serve `requirements.txt`, non serve creare un ambiente manualmente.

#### PEP 723 — approfondimento

Il blocco di metadati inline deve seguire il formato TOML e deve essere racchiuso tra `# /// script` e `# ///`. La specifica completa e definita nel PEP 723 (accettato in Python 3.12+). Oltre a `dependencies` e `requires-python`, il blocco puo contenere qualsiasi campo valido della specifica dei metadati di script, inclusi tool settings:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas>=2.2",
#     "matplotlib>=3.9",
#     "seaborn>=0.13",
# ]
#
# [tool.uv]
# extra-index-url = ["https://pypi.privato.com/simple/"]
#
# [tool.uv.sources]
# pandas = { index = "private" }
# ///

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Lo script puo usare le dipendenze senza setup esterno
df = pd.read_csv("dati.csv")
sns.histplot(data=df, x="valore")
plt.savefig("output.png")
print("Grafico generato.")
```

L'ambiente temporaneo creato da `uv run` e cached: esecuzioni successive con lo stesso blocco di metadati non riscaricare le dipendenze. La cache e invalidata solo quando il blocco di metadati cambia.

**Casi d'uso principali per PEP 723:**

- **Script di automazione one-off**: deploy scripts, data migration, report generator che devono essere autocontenuti.
- **Condivisione di snippet**: uno script condiviso via Slack, email o gist funziona senza istruzioni di setup. Il destinatario esegue `uv run script.py` e tutto funziona.
- **Notebook-like workflow**: per analisi dati rapide dove creare un progetto completo con `pyproject.toml` e eccessivo.
- **CI/CD utilities**: script ausiliari nella pipeline che necessitano di dipendenze non presenti nel progetto principale.
- **Prototyping**: sperimentazione rapida con librerie senza inquinare il progetto.

```bash
# Esecuzione con versione specifica di Python
uv run --python 3.13 script.py

# Aggiunta di dipendenze extra dalla CLI (senza modificare lo script)
uv run --with "tabulate>=0.9" script.py

# Esecuzione di uno script remoto con metadati inline
uv run https://gist.githubusercontent.com/user/abc123/raw/script.py

# Creazione di uno script PEP 723 tramite uv init
uv init --script analisi.py --python ">=3.12"
# Poi aggiungere dipendenze:
uv add --script analisi.py pandas matplotlib
```

Il comando `uv init --script` crea uno scaffold con il blocco PEP 723 gia inserito, e `uv add --script` aggiunge dipendenze al blocco esistente senza editare manualmente il file. Questo workflow e particolarmente comodo per creare script autocontenuti con il minimo sforzo.

### uv tool — gestione CLI globale

`uv tool` gestisce tool CLI in ambienti isolati, come `pipx` ma piu veloce:

```bash
# Installa un tool con dipendenze extra
uv tool install "jupyter[lab]"

# Installa una versione specifica
uv tool install "ruff==0.8.4"

# Installa con un Python specifico
uv tool install --python 3.12 black

# Aggiorna tutti i tool
uv tool upgrade --all

# Mostra dove sono installati i tool
uv tool dir

# Esegui un tool senza installare (alias: uvx)
uvx ruff check .
uvx --from "httpie" http GET https://httpbin.org/get

# Esegui con dipendenze aggiuntive
uvx --with rich pytest tests/
```

Il comando `uvx` e un alias per `uv tool run` e rappresenta il pattern piu pratico per eseguire tool una tantum senza inquinare il sistema.

### uv python — gestione interpreti

```bash
# Elenca le versioni di Python disponibili per il download
uv python list --all-versions

# Installa Python 3.13 (download automatico da python-build-standalone)
uv python install 3.13

# Installa piu versioni
uv python install 3.11 3.12 3.13

# Fissa la versione per il progetto (scrive .python-version)
uv python pin 3.12

# Trova l'interprete che uv userebbe
uv python find 3.12
```

A differenza di `pyenv`, che compila Python dai sorgenti (processo lungo e che richiede dipendenze di build), `uv python install` scarica build precompilate dal progetto `python-build-standalone` di Gregory Szorc. L'installazione richiede pochi secondi.

### uv in Docker

Pattern ottimali per l'uso di uv nei Dockerfile:

```dockerfile
FROM python:3.12-slim

# Copia il binario uv dall'immagine ufficiale
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

# Variabili d'ambiente per Docker
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Layer 1: solo file di dipendenze (cambia raramente)
COPY pyproject.toml uv.lock ./

# Layer 2: installa dipendenze (cached se lock non cambia)
RUN uv sync --frozen --no-dev --no-install-project

# Layer 3: codice sorgente (cambia spesso)
COPY . .

# Layer 4: installa il progetto stesso
RUN uv sync --frozen --no-dev

USER 1000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Le variabili d'ambiente chiave:
- `UV_COMPILE_BYTECODE=1`: pre-compila i file `.pyc` per startup piu veloce del container.
- `UV_LINK_MODE=copy`: evita hardlink che non funzionano tra layer Docker.
- `UV_PYTHON_DOWNLOADS=never`: impedisce download accidentali di Python nel container.

### Configurazione di uv

`uv` legge la configurazione da `pyproject.toml`, `uv.toml` e variabili d'ambiente:

```toml
# pyproject.toml
[tool.uv]
# Indice privato aggiuntivo
extra-index-url = ["https://pypi.privato.com/simple/"]

# Vincoli globali
constraint-dependencies = ["numpy<2"]

# Override per forzare una versione
override-dependencies = ["cryptography==42.0.0"]

# Esclusioni dal lock per specifiche piattaforme
[tool.uv.sources]
torch = { index = "pytorch-cu121" }

[[tool.uv.index]]
name = "pytorch-cu121"
url = "https://download.pytorch.org/whl/cu121"
explicit = true
```

---

## PEP 735 — Dependency Groups

PEP 735, accettato nell'ottobre 2024, introduce la tabella `[dependency-groups]` in `pyproject.toml` come meccanismo standard per dichiarare gruppi di dipendenze non distribuite con il pacchetto. A differenza di `[project.optional-dependencies]` (extras), che vengono inclusi nei metadati del pacchetto e sono installabili dagli utenti finali tramite `pip install pacchetto[extra]`, i dependency groups sono destinati esclusivamente agli sviluppatori del progetto: test, linting, documentazione, CI.

### Sintassi e semantica

```toml
[dependency-groups]
test = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.24",
    "coverage[toml]>=7.6",
]
lint = [
    "ruff>=0.8",
    "mypy>=1.13",
]
docs = [
    "sphinx>=8.0",
    "sphinx-autodoc-typehints",
    "furo",
]
# Include-group: un gruppo puo includere altri gruppi
dev = [
    {include-group = "test"},
    {include-group = "lint"},
    {include-group = "docs"},
    "ipython>=8.0",
    "debugpy",
]
```

La direttiva `{include-group = "nome"}` permette di comporre gruppi senza duplicazione. Il gruppo `dev` nell'esempio sopra include tutte le dipendenze di test, lint e docs, piu tool aggiuntivi per lo sviluppo interattivo. L'inclusione e transitiva: se `test` include un ipotetico gruppo `fixtures`, anche `dev` lo eredita.

### Differenza con optional-dependencies

| Aspetto | `[project.optional-dependencies]` | `[dependency-groups]` |
|---------|-----------------------------------|-----------------------|
| Scopo | Funzionalita opzionali per l'utente finale | Dipendenze di sviluppo per i maintainer |
| Nei metadati del pacchetto | Si — incluse in PKG-INFO/METADATA | No — solo in pyproject.toml |
| Installabili via pip | `pip install pkg[extra]` | `pip install --dependency-group test` |
| Include-group | Non supportato | `{include-group = "..."}` |
| Caso d'uso tipico | `pip install fastapi[standard]` | `pip install --dependency-group dev` |
| Specifica | PEP 508 | PEP 735 |

La regola pratica: se l'utente finale potrebbe voler installare un subset di dipendenze, si usano gli extras. Se le dipendenze servono solo durante lo sviluppo, si usano i dependency groups.

### Supporto negli strumenti

Il supporto per PEP 735 e in rapida espansione:

- **uv 0.4.27+**: supporto nativo. `uv sync --group test` installa il gruppo test. `uv sync --all-groups` installa tutti i gruppi. `uv lock` include i dependency groups nel lock file. `uv add --group lint ruff` aggiunge una dipendenza a un gruppo specifico.
- **pip 25.1+**: `pip install --dependency-group test` installa i dependency groups direttamente da `pyproject.toml`.
- **Poetry**: al momento (2025) non supporta PEP 735. Poetry usa `[tool.poetry.group.dev.dependencies]` come alternativa proprietaria con semantica simile ma formato diverso.
- **PDM**: supporto completo tramite `pdm install -G test`.
- **Hatch**: supporto tramite environments, con mapping ai dependency groups.

```bash
# Installazione con uv
uv sync --group test              # installa dipendenze progetto + gruppo test
uv sync --group test --group lint # installa piu gruppi
uv sync --all-groups              # installa tutti i gruppi
uv sync --only-group test         # installa SOLO il gruppo test, senza il progetto

# Aggiunta di dipendenze a un gruppo
uv add --group test pytest-xdist
uv add --group lint ruff

# Rimozione
uv remove --group test pytest-xdist

# Installazione con pip 25.1+
pip install --dependency-group test
pip install --dependency-group dev
```

### Migrazione da extras a dependency groups

Se il progetto attualmente usa `[project.optional-dependencies]` per le dipendenze di sviluppo, la migrazione e semplice:

```toml
# PRIMA — uso improprio degli extras per dev deps
[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

# DOPO — corretto uso dei dependency groups
[dependency-groups]
dev = ["pytest", "ruff", "mypy"]
```

In CI, sostituire `pip install -e '.[dev]'` con `pip install --dependency-group dev` (pip 25.1+) o `uv sync --group dev`. Il vantaggio e che le dipendenze di sviluppo non inquinano piu i metadati del pacchetto distribuito.

---

## uv Workspaces

Per i monorepo Python — repository che contengono piu pacchetti correlati — `uv` offre il concetto di **workspace**, ispirato ai workspace di Cargo (Rust) e npm/pnpm (Node.js). Un workspace permette a piu pacchetti di condividere un singolo `uv.lock` e di referenziarsi come dipendenze editabili.

### Struttura di un workspace

```
monorepo/
├── pyproject.toml          # Root workspace
├── uv.lock                 # Lock file condiviso
├── packages/
│   ├── core/
│   │   ├── pyproject.toml  # Pacchetto membro
│   │   └── src/core/
│   ├── api/
│   │   ├── pyproject.toml  # Pacchetto membro
│   │   └── src/api/
│   └── worker/
│       ├── pyproject.toml  # Pacchetto membro
│       └── src/worker/
└── tools/
    └── scripts/
        └── pyproject.toml  # Tool interno
```

### Configurazione del workspace root

```toml
# pyproject.toml (root)
[project]
name = "monorepo"
version = "0.0.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = [
    "packages/*",
    "tools/*",
]
exclude = [
    "packages/deprecated-*",
]
```

Il pattern `members = ["packages/*"]` include automaticamente tutti i sotto-progetti nella directory `packages/`. Il campo `exclude` permette di escludere pacchetti specifici senza rimuoverli dal filesystem.

### Dipendenze tra membri del workspace

I pacchetti all'interno del workspace possono dipendere l'uno dall'altro come editable installs automatici:

```toml
# packages/api/pyproject.toml
[project]
name = "api"
version = "1.0.0"
dependencies = [
    "core",        # Riferimento al membro "core" del workspace
    "fastapi>=0.115",
    "uvicorn>=0.32",
]

[tool.uv.sources]
core = { workspace = true }  # Specifica che "core" e un membro del workspace
```

La direttiva `{ workspace = true }` dice a uv di risolvere `core` come editable install dal workspace invece di cercarlo su PyPI. Questo significa che le modifiche al codice di `core` sono immediatamente visibili in `api` senza reinstallazione.

### Comandi workspace

```bash
# Lock di tutto il workspace (un singolo uv.lock)
uv lock

# Sync di un membro specifico
uv sync --package api

# Sync di tutti i membri
uv sync --all-packages

# Esegui test per un membro specifico
uv run --package api pytest

# Aggiungi una dipendenza a un membro specifico
uv add --package worker celery

# Esegui un comando in tutti i pacchetti
for pkg in packages/*/; do
    echo "=== $(basename $pkg) ==="
    uv run --package "$(basename $pkg)" pytest
done
```

### Lock file condiviso

Il vantaggio principale dei workspace e il **singolo `uv.lock`** per tutto il monorepo. Questo garantisce che tutti i pacchetti usino le stesse versioni delle dipendenze condivise, eliminando il rischio di conflitti di versione a runtime. Se `core` e `api` dipendono entrambi da `pydantic`, la versione e risolta una sola volta e condivisa.

Questo approccio ha un trade-off: un aggiornamento a una dipendenza condivisa richiede la verifica di compatibilita con tutti i membri del workspace. Per mitigare, si possono usare `constraint-dependencies` nel root `pyproject.toml` per vincolare le versioni critiche.

### Workspace e CI/CD

In CI, i workspace permettono di eseguire test selettivi basati sui file modificati:

```yaml
# GitHub Actions — test selettivi per workspace
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.changes.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
      - id: changes
        uses: dorny/paths-filter@v3
        with:
          filters: |
            core:
              - 'packages/core/**'
            api:
              - 'packages/api/**'
              - 'packages/core/**'  # api dipende da core
            worker:
              - 'packages/worker/**'
              - 'packages/core/**'

  test:
    needs: detect-changes
    strategy:
      matrix:
        package: ${{ fromJson(needs.detect-changes.outputs.packages) }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --package ${{ matrix.package }}
      - run: uv run --package ${{ matrix.package }} pytest
```

Questo pattern esegue i test solo per i pacchetti effettivamente modificati (e le loro dipendenze), riducendo drasticamente i tempi di CI nei monorepo di grandi dimensioni.

---

## pip-tools Deep Dive

### Strategia multi-layer avanzata

Per progetti complessi, la strategia multi-layer con pip-tools permette una gestione granulare delle dipendenze per ogni contesto:

```
requirements/
├── base.in          # Dipendenze runtime (produzione)
├── base.txt         # Compilato da base.in
├── dev.in           # Sviluppo: -c base.txt + tool dev
├── dev.txt          # Compilato da dev.in
├── test.in          # Test: -c dev.txt + tool test
├── test.txt         # Compilato da test.in
├── ci.in            # CI: -c test.txt + coverage/xdist
├── ci.txt           # Compilato da ci.in
└── typing.in        # Type stubs separati
```

Il flag `-c` (constraints) e fondamentale: a differenza di `-r` (requirements), i constraints non installano pacchetti ma vincolano le versioni. Questo garantisce che tutti i layer usino le stesse versioni per le dipendenze condivise.

```txt
# requirements/dev.in
-c base.txt
pytest
mypy
ruff
debugpy
```

```bash
# Compilazione ordinata (il layer successivo vincola il precedente)
cd requirements
uv pip compile base.in -o base.txt
uv pip compile dev.in -o dev.txt
uv pip compile test.in -o test.txt
uv pip compile ci.in -o ci.txt
```

### pip-compile con pyproject.toml

A partire da pip-tools 7.0, `pip-compile` supporta direttamente `pyproject.toml` come input:

```bash
# Compila le dipendenze dal pyproject.toml
pip-compile pyproject.toml -o requirements.txt

# Compila includendo gli optional-dependencies "dev"
pip-compile --extra dev pyproject.toml -o requirements-dev.txt

# Con uv (equivalente)
uv pip compile pyproject.toml -o requirements.txt
uv pip compile --extra dev pyproject.toml -o requirements-dev.txt
```

Questo permette di mantenere `pyproject.toml` come fonte unica di verita per le dipendenze, generando i `requirements.txt` pinned solo per il deploy e la CI.

### Automazione degli aggiornamenti

```bash
# Script per aggiornamento controllato delle dipendenze
#!/usr/bin/env bash
set -euo pipefail

echo "=== Aggiornamento dipendenze ==="

# Salva lo stato corrente
cp requirements.txt requirements.txt.bak

# Aggiorna tutte le dipendenze
uv pip compile --upgrade requirements.in -o requirements.txt

# Mostra le differenze
diff requirements.txt.bak requirements.txt || true

# Sincronizza l'ambiente
uv pip sync requirements.txt

# Esegui i test
pytest tests/ -x --tb=short

# Se i test passano, rimuovi il backup
rm requirements.txt.bak
echo "=== Aggiornamento completato con successo ==="
```

### Gestione di indici privati

```bash
# pip-compile con indice privato
pip-compile \
    --index-url https://pypi.org/simple/ \
    --extra-index-url https://pypi.privato.com/simple/ \
    --trusted-host pypi.privato.com \
    requirements.in

# Equivalente con uv
uv pip compile \
    --extra-index-url https://pypi.privato.com/simple/ \
    requirements.in -o requirements.txt
```

---

## Formati di Lock File

I lock file sono il meccanismo fondamentale per garantire installazioni riproducibili. Ogni tool dell'ecosistema Python usa un formato diverso, con trade-off specifici.

### Confronto dei formati

| Caratteristica | requirements.txt (pip-compile) | poetry.lock | uv.lock | Pipfile.lock |
|----------------|-------------------------------|-------------|---------|--------------|
| Formato | Testo piano | TOML | TOML | JSON |
| Hash integrita | Opzionale (--generate-hashes) | Sempre | Sempre | Sempre |
| Cross-platform | No (singola piattaforma) | Si | Si | Si |
| Cross-Python | No (singola versione) | Si | Si | Si |
| Marker resolution | Parziale | Completa | Completa | Completa |
| Dimensione tipica | ~2 KB | ~50 KB | ~30 KB | ~80 KB |
| Leggibilita | Alta | Media | Media | Bassa |
| Ecosistema | Universale | Solo Poetry | Solo uv | Solo pipenv |
| Velocita install | pip: media, uv: veloce | poetry: lenta | uv: velocissima | pipenv: lenta |

### requirements.txt pinned (pip-compile)

Vantaggi:
- Universale: qualsiasi tool Python lo legge.
- Leggibile: ogni riga e un pacchetto con versione.
- Le annotazioni `# via` mostrano la catena di dipendenze.
- Compatibile con Docker, CI, deploy tradizionali.

Svantaggi:
- Single-platform: un `requirements.txt` generato su Linux puo differire da uno generato su macOS (dipendenze platform-specific).
- Nessun metadata sul resolver usato o sulla versione Python.

```txt
# Esempio di output pip-compile
certifi==2024.2.2
    # via requests
charset-normalizer==3.3.2
    # via requests
idna==3.6
    # via requests
requests==2.31.0
    # via -r requirements.in
urllib3==2.2.0
    # via requests
```

### poetry.lock

Il lock file di Poetry e in formato TOML e contiene informazioni ricche per ogni pacchetto:

```toml
[[package]]
name = "requests"
version = "2.31.0"
description = "Python HTTP for Humans."
python-versions = ">=3.7"

[package.dependencies]
certifi = ">=2017.4.17"
charset-normalizer = ">=2,<4"
idna = ">=2.5,<4"
urllib3 = ">=1.21.1,<3"

[package.extras]
security = ["pyOpenSSL (>=0.14)"]

[[package]]
name = "certifi"
version = "2024.2.2"
description = "Python package for providing Mozilla's CA Bundle."
python-versions = ">=3.6"

[metadata]
lock-version = "2.0"
python-versions = "^3.10"
content-hash = "abc123..."
```

Il campo `content-hash` e un hash del `pyproject.toml`: se cambia il pyproject.toml, Poetry sa che il lock deve essere rigenerato.

### uv.lock

Il lock file di uv e anch'esso TOML ma con una struttura ottimizzata per la velocita di lettura:

```toml
version = 1
requires-python = ">=3.12"

[[package]]
name = "requests"
version = "2.31.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "certifi" },
    { name = "charset-normalizer" },
    { name = "idna" },
    { name = "urllib3" },
]
sdist = { url = "...", hash = "sha256:..." }
wheels = [
    { url = "...", hash = "sha256:..." },
]
```

`uv.lock` include URL e hash sia per sdist che per wheel, permettendo installazioni verificate senza ulteriori query alla rete.

### Quale formato scegliere

- **Progetti con team misti (tool diversi)**: `requirements.txt` via pip-compile o `uv pip compile`. Universale, tutti gli strumenti lo leggono.
- **Progetti Poetry**: `poetry.lock`. Generato e gestito automaticamente.
- **Progetti uv**: `uv.lock`. Il piu veloce e completo.
- **Librerie open source**: `pyproject.toml` con vincoli flessibili + `uv.lock` o `requirements.txt` per la CI. Le librerie non dovrebbero imporre versioni esatte ai consumatori.

---

## Algoritmi di Dependency Resolution

La risoluzione delle dipendenze e un problema computazionalmente complesso. Comprendere gli algoritmi aiuta a diagnosticare conflitti e a scrivere vincoli che si risolvono correttamente.

### Il problema della risoluzione

Data una lista di dipendenze dirette con vincoli di versione, il resolver deve trovare un insieme di versioni concrete che soddisfi simultaneamente tutti i vincoli, inclusi quelli delle dipendenze transitive.

Esempio di conflitto:

```
progetto richiede:
    A>=1.0
    B>=2.0

A 1.0 richiede: C>=1.0,<2.0
B 2.0 richiede: C>=2.0

Non esiste una versione di C che soddisfi entrambi i vincoli.
```

### Backtracking resolver (pip)

pip (dalla versione 20.3, rilasciata nel 2020) usa un **backtracking resolver**. L'algoritmo:

1. Seleziona la prima dipendenza non risolta.
2. Prova la versione piu recente compatibile.
3. Aggiunge le dipendenze transitive del pacchetto selezionato.
4. Se un conflitto viene rilevato, torna indietro (backtrack) e prova la versione precedente.
5. Ripete fino a trovare una soluzione o esaurire le opzioni.

Il problema: nel caso peggiore, il numero di combinazioni da esplorare cresce esponenzialmente. pip mitiga questo con euristiche (provare prima le versioni piu recenti) ma non garantisce tempi prevedibili.

```bash
# pip mostra il progresso del resolver
pip install --verbose "dipendenza-complessa"
# INFO: ... pip is looking at multiple versions of X ...
# INFO: ... This is taking longer than usual. ...
```

### PubGrub (uv, Dart)

uv usa l'algoritmo **PubGrub**, sviluppato originariamente per il package manager di Dart. PubGrub e un solver basato su **unit propagation** e **conflict-driven clause learning** (CDCL), ispirato ai SAT solver moderni.

Vantaggi rispetto al backtracking puro:

- **Apprendimento dei conflitti**: quando un conflitto viene trovato, PubGrub deduce una "clausola" che impedisce di esplorare combinazioni simili in futuro.
- **Messaggi di errore chiari**: PubGrub puo spiegare esattamente perche la risoluzione fallisce, mostrando la catena di incompatibilita.
- **Performance prevedibile**: il learning previene l'esplosione combinatoria nella maggior parte dei casi pratici.

Esempio di messaggio di errore PubGrub (via uv):

```
error: Because myproject depends on A>=1.0 and B>=2.0,
  and A 1.0 depends on C>=1.0,<2.0,
  and B 2.0 depends on C>=2.0,
  we can conclude that myproject's requirements are unsatisfiable.
```

### SAT solver (conda)

conda usa un solver basato sulla Satisfiability (SAT), il problema di determinare se esiste un assegnamento di valori booleani che soddisfa una formula logica. Le dipendenze vengono tradotte in clausole booleane e risolte con un SAT solver (originariamente `pycosat`, ora `libmamba`).

Il SAT solving e piu general-purpose ma anche piu lento per il caso specifico delle dipendenze di pacchetti. La transizione di conda al solver `libmamba` (basato su libsolv) ha migliorato significativamente le performance.

### Strategie per evitare conflitti

1. **Vincoli flessibili per le librerie**: non pinnare versioni esatte nelle dipendenze delle librerie. Usare lower bounds (`>=1.0`) e upper bounds solo quando necessario (`<3.0`).

2. **Constraints file per allineamento**: usare file di constraints per allineare le versioni tra piu progetti senza forzare l'installazione.

3. **Override espliciti**: quando un conflitto non e risolvibile, usare override per forzare una versione specifica (con uv: `tool.uv.override-dependencies`).

4. **Aggiornamento incrementale**: aggiornare un pacchetto alla volta e verificare la risoluzione ad ogni passo, piuttosto che aggiornare tutto in blocco.

---

## Installazioni Riproducibili

Un'installazione riproducibile garantisce che, dato lo stesso input (codice + lock file), si ottenga sempre lo stesso ambiente, indipendentemente da quando, dove e da chi viene eseguita.

### I tre livelli di riproducibilita

**Livello 1 — Version pinning**: il lock file contiene versioni esatte. Questo e il livello minimo e copre la maggior parte dei casi.

```txt
requests==2.31.0
flask==3.0.2
```

**Livello 2 — Hash verification**: oltre alle versioni, il lock file contiene gli hash SHA256 dei pacchetti. Questo previene attacchi supply chain dove un pacchetto viene sostituito sul registry.

```txt
requests==2.31.0 \
    --hash=sha256:942c5a758f98d790eaed1a29cb6eefc7f0edf3fcb0fce8aea3fbd5951d...
```

```bash
# pip con verifica hash
pip install --require-hashes -r requirements.txt

# uv pip compile con hash
uv pip compile --generate-hashes requirements.in -o requirements.txt
```

**Livello 3 — Full determinism**: oltre a versioni e hash, si fissano anche la versione esatta di Python, il sistema operativo e l'architettura. Questo livello e raggiungibile solo con Docker o ambienti simili.

```dockerfile
# Immagine Python con digest fisso = stessa immagine sempre
FROM python:3.12.3-slim@sha256:abc123def456...
COPY requirements.txt .
RUN pip install --require-hashes --no-deps -r requirements.txt
```

### Pattern per la riproducibilita

**Pattern 1: pip-tools + hash**

```bash
# Genera requirements con hash
uv pip compile --generate-hashes requirements.in -o requirements.txt

# Installa con verifica obbligatoria
uv pip sync --require-hashes requirements.txt
```

**Pattern 2: uv lock + uv sync**

```bash
# Il lock file uv.lock include sempre gli hash
uv lock
uv sync --frozen  # --frozen impedisce aggiornamenti del lock
```

**Pattern 3: Poetry lock + install**

```bash
poetry lock
poetry install --no-update  # installa esattamente dal lock
```

### Verifica della riproducibilita

```bash
# Script per verificare la riproducibilita
#!/usr/bin/env bash
set -euo pipefail

# Crea due ambienti identici
uv venv /tmp/env-a
uv venv /tmp/env-b

# Installa in entrambi
VIRTUAL_ENV=/tmp/env-a uv pip sync requirements.txt
VIRTUAL_ENV=/tmp/env-b uv pip sync requirements.txt

# Confronta i pacchetti installati
diff <(VIRTUAL_ENV=/tmp/env-a uv pip freeze | sort) \
     <(VIRTUAL_ENV=/tmp/env-b uv pip freeze | sort)

echo "Ambienti identici: $?"

# Cleanup
rm -rf /tmp/env-a /tmp/env-b
```

### uv export — esportazione cross-format

`uv export` permette di esportare le dipendenze risolte dal `uv.lock` in formati compatibili con altri tool, garantendo interoperabilita senza sacrificare la riproducibilita:

```bash
# Esportazione in formato requirements.txt (per deploy tradizionali)
uv export --format requirements-txt > requirements.txt

# Esportazione con hash (per massima sicurezza)
uv export --format requirements-txt --generate-hashes > requirements.txt

# Esportazione solo delle dipendenze di produzione
uv export --format requirements-txt --no-dev > requirements-prod.txt

# Esportazione per una piattaforma specifica
uv export --format requirements-txt --python-platform linux --python-version 3.12 \
    > requirements-linux.txt

# Esportazione con gruppi specifici
uv export --format requirements-txt --group test > requirements-test.txt
```

Questo pattern e particolarmente utile in scenari dove il sistema di deploy non supporta `uv.lock` nativamente (es. AWS Lambda, Google Cloud Functions, sistemi legacy). Il file esportato contiene le versioni esatte e, con `--generate-hashes`, gli hash SHA256 per verifica di integrita.

### Riproducibilita cross-platform

La riproducibilita cross-platform e complessa perche molte dipendenze Python hanno componenti compilati che variano per sistema operativo e architettura. Le strategie principali:

**1. Lock file universale (uv):**

```bash
# Il lock file uv.lock e "universale" per default:
# contiene i marker per tutte le piattaforme
uv lock
# Risultato: un singolo uv.lock che funziona su Linux, macOS, Windows
```

Il `uv.lock` include le risoluzioni per tutte le combinazioni piattaforma/architettura, annotate con marker PEP 508. Questo significa che lo stesso lock file produce installazioni corrette su qualsiasi piattaforma supportata.

**2. Lock file per piattaforma (pip-tools):**

```bash
# Se la risoluzione universale non e disponibile, generare lock separati
uv pip compile --python-platform linux --python-version 3.12 \
    requirements.in -o requirements-linux-312.txt
uv pip compile --python-platform macos --python-version 3.12 \
    requirements.in -o requirements-macos-312.txt
```

**3. Docker come equalizzatore:**

Per eliminare completamente le differenze di piattaforma, tutti gli sviluppatori e la CI usano lo stesso container Docker. Questo garantisce che l'ambiente sia identico byte per byte, indipendentemente dal sistema host.

### Supply chain security per le dipendenze Python

La sicurezza della supply chain e diventata critica dopo incidenti come l'attacco a PyPI del 2023 (typosquatting su pacchetti popolari) e la compromissione di `ua-parser-js` in npm. Per Python, le difese principali sono:

**Hash verification** (gia coperta sopra) verifica che il contenuto del pacchetto non sia stato alterato dopo la generazione del lock file. Ma non copre il caso in cui il maintainer stesso pubblica codice malevolo.

**Auditing delle dipendenze:**

```bash
# pip-audit — verifica vulnerabilita note (database OSV)
uvx pip-audit -r requirements.txt
uvx pip-audit --desc on  # con descrizione delle vulnerabilita

# Integrazione con uv
uv run pip-audit

# Output in formato JSON (per CI/automazione)
uvx pip-audit --format json -o audit-report.json
```

**SBOM (Software Bill of Materials):**

```bash
# Genera un SBOM in formato CycloneDX
uvx cyclonedx-bom -r requirements.txt -o sbom.json --format json

# O dal pyproject.toml
uvx cyclonedx-bom -p --pyproject pyproject.toml -o sbom.json
```

L'SBOM e un inventario completo di tutte le dipendenze (dirette e transitive) con versioni e licenze. E sempre piu richiesto per compliance (EU Cyber Resilience Act, US Executive Order 14028) e permette di reagire rapidamente quando viene scoperta una vulnerabilita in una dipendenza transitiva.

**Pinning dell'indice:**

```toml
# pyproject.toml — vincola l'indice per prevenire dependency confusion
[tool.uv]
index-url = "https://pypi.org/simple/"
# Nessun --extra-index-url in produzione: previene dependency confusion
# Per pacchetti privati, usare un indice dedicato con priorita
```

La **dependency confusion** avviene quando un pacchetto privato ha lo stesso nome di un pacchetto pubblico su PyPI, e il resolver installa quello pubblico (malevolo). La difesa e usare un singolo indice per produzione e configurare indici privati con namespace dedicati.

---

## CI Caching Patterns

Il caching delle dipendenze nelle pipeline CI/CD e fondamentale per ridurre i tempi di build. Ogni tool ha un path di cache specifico.

### Path di cache per tool

| Tool | Linux cache path | macOS cache path | Cache key strategy |
|------|------------------|------------------|--------------------|
| pip | `~/.cache/pip` | `~/Library/Caches/pip` | Hash di `requirements*.txt` |
| uv | `~/.cache/uv` | `~/Library/Caches/uv` | Hash di `uv.lock` o `requirements*.txt` |
| Poetry | `~/.cache/pypoetry` | `~/Library/Caches/pypoetry` | Hash di `poetry.lock` |
| conda | `~/.conda/pkgs` | `~/.conda/pkgs` | Hash di `environment.yml` |
| pre-commit | `~/.cache/pre-commit` | `~/Library/Caches/pre-commit` | Hash di `.pre-commit-config.yaml` |

### GitHub Actions — caching pip

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: "pip"
    cache-dependency-path: |
      requirements.txt
      requirements-dev.txt
```

La cache integrata di `setup-python` e la soluzione piu semplice. Per un controllo piu granulare:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-${{ matrix.python-version }}-
      ${{ runner.os }}-pip-
```

### GitHub Actions — caching uv

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v5
  with:
    version: "0.7.x"
    enable-cache: true
    cache-dependency-glob: "uv.lock"

- name: Install dependencies
  run: uv sync --frozen
```

L'action `astral-sh/setup-uv` gestisce automaticamente il caching della cache globale di uv. Per un controllo manuale:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}
    restore-keys: |
      ${{ runner.os }}-uv-

- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Sync dependencies
  run: uv sync --frozen
```

### GitHub Actions — caching Poetry

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pypoetry
      .venv
    key: ${{ runner.os }}-poetry-${{ hashFiles('poetry.lock') }}
    restore-keys: |
      ${{ runner.os }}-poetry-

- name: Install Poetry
  run: pipx install poetry

- name: Configure Poetry
  run: poetry config virtualenvs.in-project true

- name: Install dependencies
  run: poetry install --no-interaction
```

### Caching con venv completo

Un pattern alternativo e cachare l'intero venv invece della sola cache dei pacchetti. Questo elimina il tempo di installazione quando la cache hit e completa:

```yaml
- uses: actions/cache@v4
  id: cache-venv
  with:
    path: .venv
    key: ${{ runner.os }}-venv-${{ matrix.python-version }}-${{ hashFiles('requirements.txt') }}

- name: Create venv and install
  if: steps.cache-venv.outputs.cache-hit != 'true'
  run: |
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
```

Attenzione: questo pattern funziona solo se la versione di Python e la stessa. Il campo `matrix.python-version` nella cache key previene problemi di incompatibilita.

### Metriche di impatto

Tempi tipici di installazione dipendenze in CI (progetto medio, ~50 dipendenze):

| Scenario | pip (no cache) | pip (cached) | uv (no cache) | uv (cached) |
|----------|----------------|--------------|----------------|-------------|
| Prima esecuzione | 45-60s | N/A | 3-5s | N/A |
| Esecuzioni successive | 45-60s | 10-15s | 3-5s | 1-2s |
| Cache hit completo venv | N/A | 2-3s | N/A | <1s |

La combinazione uv + caching riduce i tempi di installazione a valori trascurabili, rendendo la pipeline CI piu veloce e riducendo i costi per i repository privati con minuti a pagamento.

### Pattern per Docker CI caching

Per le build Docker nella CI, il caching dei layer richiede strategie specifiche:

```yaml
# GitHub Actions con cache GHA per Docker
- uses: docker/build-push-action@v6
  with:
    context: .
    push: false
    cache-from: type=gha
    cache-to: type=gha,mode=max

# Alternativa: cache con registry
- uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    cache-from: type=registry,ref=ghcr.io/org/app:buildcache
    cache-to: type=registry,ref=ghcr.io/org/app:buildcache,mode=max
```

Nel Dockerfile, il caching delle dipendenze pip/uv con BuildKit mount:

```dockerfile
# BuildKit mount cache per uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# BuildKit mount cache per pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
```

Il mount cache di BuildKit persiste tra build successive sullo stesso host, evitando di scaricare nuovamente i pacchetti gia presenti.

---

## Devcontainers e Codespaces per Python

I **Development Containers** (devcontainers) sono ambienti di sviluppo containerizzati definiti da un file di configurazione `.devcontainer/devcontainer.json`. Originariamente sviluppati per VS Code, sono ora uno **standard aperto** supportato da JetBrains, GitHub Codespaces, DevPod e altri IDE. Per i progetti Python, rappresentano il livello massimo di riproducibilita dell'ambiente di sviluppo.

### Perche usare i devcontainers per Python

Il problema classico degli ambienti Python — "funziona sulla mia macchina" — ha radici profonde: versione di Python diversa, librerie di sistema mancanti (libpq-dev, libffi-dev), tool CLI non installati (redis-cli, psql), configurazione dell'IDE non allineata. I devcontainers risolvono tutto questo codificando l'intero ambiente nello stesso repository del progetto.

**Vantaggi concreti:**

- **Onboarding zero-effort**: un nuovo sviluppatore esegue "Reopen in Container" e ha un ambiente funzionante in 2-3 minuti, indipendentemente dal suo sistema operativo.
- **Parita dev/CI/prod**: lo stesso container base puo essere usato in sviluppo, CI e produzione, eliminando intere classi di bug.
- **Dipendenze di sistema incluse**: compilatori C, librerie di sviluppo, database client, tool CLI — tutto dichiarato nel Dockerfile del devcontainer.
- **Configurazione IDE versionata**: estensioni, settings, formatter, linter — tutto nel repository.

### Configurazione base

```
.devcontainer/
├── devcontainer.json
├── Dockerfile           # Opzionale: immagine custom
└── post-create.sh       # Opzionale: script post-creazione
```

```jsonc
// .devcontainer/devcontainer.json
{
    "name": "Python Project",
    "image": "mcr.microsoft.com/devcontainers/python:1-3.12-bookworm",

    // Features: componenti aggiuntivi installabili
    "features": {
        "ghcr.io/astral-sh/devcontainer-features/uv:1": {
            "version": "latest"
        },
        "ghcr.io/devcontainers/features/docker-in-docker:2": {},
        "ghcr.io/devcontainers/features/github-cli:1": {},
        "ghcr.io/devcontainers/features/node:1": {
            "version": "22"
        }
    },

    // Comandi post-creazione
    "postCreateCommand": "uv sync && uv run pre-commit install",
    "postStartCommand": "uv run python manage.py migrate --check",

    // Configurazione VS Code
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "charliermarsh.ruff",
                "tamasfe.even-better-toml",
                "ms-python.debugpy",
                "ryanluker.vscode-coverage-gutters"
            ],
            "settings": {
                "python.defaultInterpreterPath": ".venv/bin/python",
                "python.testing.pytestEnabled": true,
                "[python]": {
                    "editor.defaultFormatter": "charliermarsh.ruff",
                    "editor.formatOnSave": true,
                    "editor.codeActionsOnSave": {
                        "source.fixAll.ruff": "explicit",
                        "source.organizeImports.ruff": "explicit"
                    }
                }
            }
        }
    },

    // Port forwarding automatico
    "forwardPorts": [8000, 5432, 6379],
    "portsAttributes": {
        "8000": { "label": "API Server", "onAutoForward": "notify" },
        "5432": { "label": "PostgreSQL", "onAutoForward": "silent" }
    },

    // Mount del volume per la cache uv (persiste tra rebuild)
    "mounts": [
        "source=devcontainer-uv-cache,target=/root/.cache/uv,type=volume"
    ],

    // Variabili d'ambiente
    "containerEnv": {
        "UV_LINK_MODE": "copy",
        "PYTHONDONTWRITEBYTECODE": "1"
    }
}
```

### Devcontainer con Dockerfile personalizzato

Per progetti con dipendenze di sistema complesse, si usa un Dockerfile dedicato:

```jsonc
// .devcontainer/devcontainer.json
{
    "name": "ML Project",
    "build": {
        "dockerfile": "Dockerfile",
        "context": "..",
        "args": {
            "PYTHON_VERSION": "3.12"
        }
    },
    "postCreateCommand": "uv sync --all-groups"
}
```

```dockerfile
# .devcontainer/Dockerfile
ARG PYTHON_VERSION=3.12
FROM mcr.microsoft.com/devcontainers/python:1-${PYTHON_VERSION}-bookworm

# Dipendenze di sistema per pacchetti scientifici
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    libhdf5-dev \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Installa uv
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

# Pre-scarica Python build standalone per velocizzare la prima esecuzione
RUN uv python install ${PYTHON_VERSION}
```

### GitHub Codespaces

GitHub Codespaces crea un devcontainer nel cloud, accessibile dal browser o da VS Code. Per i progetti Python, il file `devcontainer.json` definisce automaticamente l'ambiente Codespace:

```jsonc
// Aggiungere al devcontainer.json per Codespaces
{
    // Tipo di macchina consigliato
    "hostRequirements": {
        "cpus": 4,
        "memory": "8gb",
        "storage": "32gb"
    },

    // Prebuilds: ambiente pre-costruito per avvio istantaneo
    // Configurabili in Settings > Codespaces > Prebuild configuration
    // Trigger: push su main, push su PR, o schedule
}
```

I **prebuilds** sono il punto di forza di Codespaces: eseguono il Dockerfile e i `postCreateCommand` in anticipo, cosi quando uno sviluppatore apre un Codespace, l'ambiente e gia pronto. Il tempo di avvio passa da 3-5 minuti a 10-15 secondi.

**Pattern per team distribuiti:**

1. Configurare i prebuilds per il branch `main` e per le PR.
2. Usare `uv sync --frozen` nel `postCreateCommand` per garantire che il lock file sia rispettato.
3. Montare un volume per la cache di uv per accelerare i rebuild.
4. Documentare nel README: "Per contribuire: apri in Codespace" con un badge link.
5. Configurare dotfiles personali via Settings > Codespaces > Dotfiles per preferenze individuali (shell, alias, git config).

### Devcontainers e ambienti virtuali

All'interno di un devcontainer, l'uso di un venv resta raccomandato per due motivi:

1. **Separazione progetto/sistema**: anche nel container, installare pacchetti nel Python di sistema puo creare conflitti con tool pre-installati.
2. **Compatibilita IDE**: VS Code e Pylance si aspettano un interprete in `.venv/bin/python` per l'IntelliSense.

Il `postCreateCommand: "uv sync"` crea automaticamente il `.venv` e installa le dipendenze. Il setting `python.defaultInterpreterPath: ".venv/bin/python"` configura l'IDE per usarlo.

### Devcontainers vs Docker Compose per sviluppo

Per progetti che richiedono servizi (database, cache, message broker), si puo integrare Docker Compose:

```jsonc
{
    "name": "Full Stack Python",
    "dockerComposeFile": "docker-compose.yml",
    "service": "app",
    "workspaceFolder": "/workspace",
    "postCreateCommand": "uv sync --all-groups",
    "forwardPorts": [8000, 5432, 6379]
}
```

```yaml
# .devcontainer/docker-compose.yml
services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
      - uv-cache:/root/.cache/uv
    command: sleep infinity

  db:
    image: postgres:17
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
  uv-cache:
```

Questo pattern offre il meglio di entrambi i mondi: un ambiente di sviluppo completamente configurato con servizi ausiliari, il tutto dichiarato nel repository e riproducibile con un solo click.

### Troubleshooting devcontainers

Problemi comuni e soluzioni:

- **Build lenta**: usare i prebuilds di Codespaces o `devcontainer build --cache-from` per cachare i layer Docker. Le features si installano in sequenza — raggruppare le dipendenze di sistema nel Dockerfile e limitato a 3-4 features.
- **Estensioni non caricate**: verificare che i nomi siano corretti nel campo `extensions` (usare l'ID completo es. `charliermarsh.ruff`, non solo `ruff`). Alcune estensioni richiedono il reload della finestra.
- **Volume mount lento su macOS**: usare `:cached` nel mount bind (gia default in devcontainer). Per file system intensivi (node_modules, .venv), preferire named volumes.
- **Permessi**: se i file creati nel container hanno permessi root, aggiungere `"remoteUser": "vscode"` nel `devcontainer.json`. Assicurarsi che il Dockerfile crei l'utente con lo stesso UID/GID dell'host.
- **Porta gia in uso**: configurare `"portsAttributes"` con `"onAutoForward": "ignore"` per porte che non devono essere forwardate automaticamente. Usare `"requireLocalPort": true` per forzare una porta specifica.
- **Git credentials**: il devcontainer inoltra automaticamente le credenziali Git dall'host (SSH agent, credential manager). Se non funziona, verificare che `ssh-agent` sia in esecuzione sull'host e che la chiave SSH sia aggiunta.

---

## Esercizi

### Esercizio 1 — Migrazione da pip freeze a pip-tools

Scenario: hai ereditato un progetto con un `requirements.txt` generato da `pip freeze` contenente 87 dipendenze (dirette e transitive mescolate). Il tuo compito e separare le dipendenze dirette dalle transitive.

**Procedura:**
1. Crea un nuovo venv vuoto.
2. Installa le dipendenze dal `requirements.txt` originale.
3. Usa `pip show <pacchetto>` per identificare le dipendenze dirette (quelle importate nel codice).
4. Crea un file `requirements.in` con solo le dipendenze dirette.
5. Esegui `uv pip compile requirements.in -o requirements-new.txt`.
6. Confronta `requirements-new.txt` con l'originale.
7. Verifica che l'applicazione funzioni con le nuove dipendenze.

**Variante avanzata:** automatizza l'identificazione delle dipendenze dirette analizzando gli import nel codice sorgente con `pipreqs` o grep.

### Esercizio 2 — uv workflow completo

Crea un progetto Python completo usando esclusivamente `uv`:

1. `uv init --lib mia-libreria`
2. Aggiungi dipendenze: `uv add httpx pydantic`
3. Aggiungi dipendenze dev: `uv add --dev pytest ruff mypy`
4. Scrivi un modulo che usi `httpx` e `pydantic`.
5. Scrivi un test con pytest.
6. Esegui: `uv run pytest`
7. Esegui: `uv run ruff check .`
8. Crea uno script PEP 723 standalone con dipendenze inline.
9. Eseguilo con `uv run script.py`.

### Esercizio 3 — Lock file cross-platform

Obiettivo: generare un `requirements.txt` che funzioni sia su Linux che su macOS.

1. Crea un `requirements.in` con dipendenze che hanno varianti platform-specific (es. `uvloop`, `pywin32`).
2. Compila con `uv pip compile --universal requirements.in -o requirements.txt`.
3. Esamina il file generato: osserva i marker di piattaforma.
4. Verifica che il file si installi correttamente su entrambe le piattaforme (o in container Docker con OS diversi).

### Esercizio 4 — CI pipeline con caching

Scrivi un workflow GitHub Actions completo per un progetto Python che:

1. Usa `uv` per la gestione delle dipendenze.
2. Esegue test su Python 3.11, 3.12 e 3.13.
3. Implementa caching della cache di uv.
4. Esegue ruff, mypy e pytest in job separati.
5. Misura e riporta i tempi di installazione con e senza cache.

### Esercizio 5 — Dependency resolution debugging

Dato il seguente `pyproject.toml`:

```toml
[project]
dependencies = [
    "django>=4.2",
    "djangorestframework>=3.14",
    "celery>=5.3",
    "kombu>=5.3",
]
```

1. Esegui `uv lock` e osserva le versioni risolte.
2. Aggiungi un vincolo incompatibile: `"kombu<5.3"`.
3. Osserva il messaggio di errore di uv (PubGrub).
4. Diagnostica il conflitto e proponi una soluzione.

### Esercizio 6 — Confronto performance tool

Crea un benchmark che misuri i tempi di:
- Creazione venv: `python -m venv` vs `uv venv`
- Installazione dipendenze: `pip install` vs `uv pip install`
- Compilazione requirements: `pip-compile` vs `uv pip compile`
- Risoluzione dipendenze: pip resolver vs uv PubGrub

Usa un `requirements.in` con almeno 20 dipendenze dirette.

### Esercizio 7 — Installazione riproducibile verificata

1. Genera un `requirements.txt` con hash: `uv pip compile --generate-hashes requirements.in -o requirements.txt`.
2. Installa con `uv pip sync --require-hashes requirements.txt`.
3. Modifica manualmente un hash nel file.
4. Tenta la reinstallazione e osserva l'errore.
5. Discuti gli scenari in cui la verifica hash previene attacchi reali.

### Esercizio 8 — PEP 735 Dependency Groups

Obiettivo: migrare un progetto da `[project.optional-dependencies]` a `[dependency-groups]`.

1. Crea un progetto con `uv init --lib esercizio-pep735`.
2. Aggiungi dipendenze runtime: `uv add httpx pydantic`.
3. Crea un gruppo `test`: `uv add --group test pytest pytest-cov hypothesis`.
4. Crea un gruppo `lint`: `uv add --group lint ruff mypy`.
5. Crea un gruppo `dev` che include `test` e `lint` piu `ipython`:
   - Modifica manualmente `pyproject.toml` per aggiungere `{include-group = "test"}` e `{include-group = "lint"}`.
6. Verifica con `uv sync --group dev` che tutte le dipendenze siano installate.
7. Verifica con `uv sync --only-group test` che vengano installate solo le dipendenze di test.
8. Confronta il `pyproject.toml` risultante con un equivalente che usa `[project.optional-dependencies]`.

### Esercizio 9 — uv Workspace monorepo

Crea un monorepo con tre pacchetti interconnessi:

1. Crea la struttura:
   ```bash
   mkdir -p monorepo/packages/{models,services,api}
   cd monorepo
   uv init
   ```
2. Configura il workspace nel `pyproject.toml` root con `members = ["packages/*"]`.
3. Inizializza ogni pacchetto: `uv init --lib packages/models`, ecc.
4. Fai dipendere `services` da `models` e `api` da `services`:
   - In `packages/services/pyproject.toml`: aggiungi `models` come dipendenza con `[tool.uv.sources] models = { workspace = true }`.
   - In `packages/api/pyproject.toml`: aggiungi `services` con lo stesso pattern.
5. Esegui `uv lock` e osserva il singolo `uv.lock` generato.
6. Esegui `uv sync --package api` e verifica che tutti e tre i pacchetti siano installati come editable.
7. Scrivi un test in `api` che importa da `models` transitivamente attraverso `services`.
8. Esegui `uv run --package api pytest` e verifica che il test passi.

### Esercizio 10 — Devcontainer Python completo

Crea un devcontainer per un progetto Python con FastAPI e PostgreSQL:

1. Crea la directory `.devcontainer/` nel progetto.
2. Scrivi un `devcontainer.json` che:
   - Usi l'immagine base `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`.
   - Aggiunga le features per uv e GitHub CLI.
   - Configuri VS Code con estensioni Python, Ruff e Pylance.
   - Esegua `uv sync` come `postCreateCommand`.
   - Forwardi la porta 8000.
3. Crea un `docker-compose.yml` che includa il servizio `app` e un servizio `db` con PostgreSQL.
4. Testa aprendo il progetto in un devcontainer (VS Code: "Reopen in Container" o `devcontainer up`).
5. Verifica che `uv run uvicorn app.main:app --reload` funzioni all'interno del container con connessione al database.

### Esercizio 11 — Supply chain audit

Esegui un audit completo della supply chain di un progetto esistente:

1. Genera i requirements con hash: `uv export --format requirements-txt --generate-hashes > requirements.txt`.
2. Esegui `uvx pip-audit -r requirements.txt` e analizza le vulnerabilita trovate.
3. Genera un SBOM in formato CycloneDX: `uvx cyclonedx-bom -r requirements.txt -o sbom.json`.
4. Analizza il SBOM: quante dipendenze transitive ha il progetto? Quali licenze sono presenti?
5. Simula un attacco di dependency confusion: crea un `requirements.in` con un pacchetto dal nome simile a uno popolare (es. `requets` invece di `requests`). Osserva come il resolver reagisce.
6. Configura `[tool.uv]` per vincolare l'indice a `https://pypi.org/simple/` senza extra-index-url.

---

## Letture e Riferimenti

1. **PEP 405** — Python Virtual Environments.
   `https://peps.python.org/pep-0405/`

2. **PEP 668** — Marking Python base environments as "externally managed".
   `https://peps.python.org/pep-0668/`

3. **PEP 723** — Inline script metadata.
   `https://peps.python.org/pep-0723/`

4. **PEP 621** — Storing project metadata in pyproject.toml.
   `https://peps.python.org/pep-0621/`

5. **PEP 735** — Dependency Groups.
   `https://peps.python.org/pep-0735/`

6. **uv documentation** — Getting Started, Concepts, Configuration.
   `https://docs.astral.sh/uv/`

7. **pip documentation** — User Guide, Reference.
   `https://pip.pypa.io/en/stable/`

8. **pip-tools documentation**.
   `https://pip-tools.readthedocs.io/en/latest/`

9. **Poetry documentation** — Basic usage, Managing dependencies.
   `https://python-poetry.org/docs/`

10. **venv module documentation** — Python standard library.
    `https://docs.python.org/3/library/venv.html`

11. **PubGrub algorithm** — Version solving made easy (Natalie Weizenbaum).
    `https://nex3.medium.com/pubgrub-2fb6470504f`

12. **Python Packaging User Guide** — Tutorials, Guides, Discussions.
    `https://packaging.python.org/`

13. **pyenv GitHub repository** — Installation and usage.
    `https://github.com/pyenv/pyenv`

14. **conda documentation** — Managing environments.
    `https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html`

15. **Dependabot documentation** — Automated dependency updates.
    `https://docs.github.com/en/code-security/dependabot`

16. **Development Containers specification** — Devcontainer standard aperto.
    `https://containers.dev/`

17. **PDM documentation** — A modern Python package and dependency manager.
    `https://pdm-project.org/en/latest/`

18. **Hatch documentation** — Modern, extensible Python project manager.
    `https://hatch.pypa.io/latest/`

19. **pip-audit** — Auditing Python environments for known vulnerabilities.
    `https://github.com/pypa/pip-audit`

20. **CycloneDX Python** — SBOM generation for Python projects.
    `https://github.com/CycloneDX/cyclonedx-python`

21. **python-build-standalone** — Prebuilt CPython distributions by Gregory Szorc.
    `https://github.com/indygreg/python-build-standalone`

22. **PEP 508** — Dependency specification for Python packages (markers, extras, URL references).
    `https://peps.python.org/pep-0508/`

23. **GitHub Codespaces documentation** — Cloud development environments.
    `https://docs.github.com/en/codespaces`

24. **DevPod** — Open source client-only tool for devcontainers.
    `https://devpod.sh/`

---

## Moduli Correlati

- **Modulo 23 — Packaging e Distribuzione**: creazione di pacchetti wheel/sdist, pyproject.toml come build input.
- **Modulo 25 — Performance**: profiling e ottimizzazione; le scelte di dipendenze influenzano la performance.
- **Modulo 26 — Docker per Python**: containerizzazione come livello superiore di isolamento; uv in Docker.
- **Modulo 27 — CI/CD per Python**: caching delle dipendenze in GitHub Actions; `uv sync --frozen` in pipeline.
- **Modulo 22 — Tooling Moderno**: ruff, mypy e altri strumenti installati via `uv tool` o `pipx`.

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Ambiente virtuale (venv)** | Directory isolata contenente un interprete Python e una copia indipendente di `site-packages`, creata con `python -m venv` o tool equivalenti. |
| **Backtracking resolver** | Algoritmo di risoluzione dipendenze che prova combinazioni di versioni e torna indietro quando incontra un conflitto. Usato da pip. |
| **Constraint file** | File che vincola le versioni dei pacchetti senza installarli direttamente. Usato con `pip install -c constraints.txt`. |
| **Dependency hell** | Situazione in cui due o piu pacchetti richiedono versioni incompatibili della stessa dipendenza. |
| **Dependency resolution** | Processo di trovare un insieme coerente di versioni che soddisfi tutti i vincoli delle dipendenze dirette e transitive. |
| **Dipendenza diretta** | Pacchetto esplicitamente richiesto dal progetto nel file di configurazione. |
| **Dipendenza transitiva** | Pacchetto richiesto da una dipendenza diretta (non elencato esplicitamente nel progetto). |
| **Editable install** | Installazione in modalita sviluppo (`pip install -e .`) che crea un link al codice sorgente invece di copiarlo. |
| **Hash verification** | Verifica dell'integrita dei pacchetti confrontando l'hash SHA256 del file scaricato con quello atteso nel lock file. |
| **Hardlink** | Collegamento diretto al blocco dati di un file su disco; usato da uv per evitare copie ridondanti dei pacchetti. |
| **Lock file** | File generato dal resolver che contiene le versioni esatte di tutte le dipendenze (dirette e transitive) con hash di verifica. |
| **Marker** | Espressione condizionale nei requirements che specifica quando una dipendenza e necessaria (es. `sys_platform == "win32"`). |
| **pip-compile** | Comando di pip-tools che risolve le dipendenze da un file `.in` e produce un file `.txt` con versioni pinnate. |
| **pip-sync** | Comando di pip-tools che sincronizza l'ambiente con il file requirements, rimuovendo pacchetti non dichiarati. |
| **PEP 405** | Python Enhancement Proposal che definisce il meccanismo degli ambienti virtuali nella standard library. |
| **PEP 668** | PEP che introduce il marcatore `EXTERNALLY-MANAGED` per impedire modifiche accidentali al Python di sistema con pip. |
| **PEP 723** | PEP che definisce i metadati inline negli script Python (dipendenze dichiarate come commento nello script). |
| **PubGrub** | Algoritmo di risoluzione dipendenze basato su CDCL (Conflict-Driven Clause Learning), usato da uv. |
| **pyvenv.cfg** | File di configurazione nella root di un venv che CPython usa durante lo startup per determinare i percorsi di ricerca. |
| **Resolver** | Componente del package manager che determina le versioni concrete da installare dato un insieme di vincoli. |
| **SAT solver** | Solver per il problema di soddisfacibilita booleana; usato da conda per la risoluzione delle dipendenze. |
| **Seed packages** | Pacchetti installati automaticamente in un nuovo venv (tipicamente pip e setuptools). |
| **site-packages** | Directory dove Python installa i pacchetti di terze parti. Ogni venv ha il proprio site-packages isolato. |
| **Supply chain attack** | Attacco in cui un pacchetto legittimo viene sostituito con una versione malevola nel registry o durante il download. |
| **Symlink** | Collegamento simbolico; usato da venv per puntare al binario Python di sistema senza copiarlo. |
| **sys.prefix** | Attributo di sys che indica la directory del venv attivo; in un venv, differisce da `sys.base_prefix`. |
| **Universal lock** | Lock file che include marker per tutte le piattaforme, generato con `--universal`. |
| **uv.lock** | Lock file nativo di uv in formato TOML, con hash integrati e supporto cross-platform. |
| **Wheel** | Formato di distribuzione binaria per pacchetti Python (file `.whl`), piu veloce da installare rispetto a sdist. |
| **BuildKit** | Backend di build avanzato per Docker che supporta cache mount, build secrets e parallelismo migliorato. Necessario per `RUN --mount=type=cache`. |
| **Copy-on-Write (CoW)** | Tecnica di ottimizzazione del filesystem dove un file viene copiato solo quando viene modificato. Usato da uv su APFS (macOS) e Btrfs (Linux) per installazioni quasi istantanee. |
| **Dependency confusion** | Attacco supply chain dove un pacchetto privato viene sostituito da uno malevolo con lo stesso nome su un indice pubblico come PyPI. |
| **Dependency group** | Gruppo di dipendenze di sviluppo dichiarato in `[dependency-groups]` nel `pyproject.toml` (PEP 735). Non viene distribuito con il pacchetto. |
| **Devcontainer** | Ambiente di sviluppo containerizzato definito da `.devcontainer/devcontainer.json`. Standard aperto supportato da VS Code, JetBrains, GitHub Codespaces e DevPod. |
| **GitHub Codespaces** | Servizio cloud di GitHub che crea istanze di sviluppo remote basate sulla configurazione devcontainer del repository. |
| **include-group** | Direttiva in PEP 735 che permette a un dependency group di includere transitivamente tutti i pacchetti di un altro gruppo. |
| **Monorepo** | Repository che contiene piu pacchetti o progetti correlati. In uv, gestibile con il sistema di workspace. |
| **PEP 621** | PEP che standardizza la dichiarazione dei metadati del progetto nel `pyproject.toml` sotto la tabella `[project]`. |
| **PEP 735** | PEP che introduce i dependency groups (`[dependency-groups]` in `pyproject.toml`) per dipendenze di sviluppo non distribuite con il pacchetto. Accettato ottobre 2024. |
| **Prebuild** | In GitHub Codespaces, un ambiente pre-costruito che esegue il Dockerfile e i comandi di setup in anticipo, riducendo il tempo di avvio a pochi secondi. |
| **python-build-standalone** | Progetto che fornisce build precompilate di CPython per tutte le piattaforme, usato da `uv python install` per installare Python senza compilare dai sorgenti. |
| **SBOM (Software Bill of Materials)** | Inventario completo e leggibile da macchina di tutte le componenti software (dipendenze, versioni, licenze) di un progetto. Richiesto da normative come EU CRA e US EO 14028. |
| **Workspace** | In uv, un meccanismo per gestire monorepo Python con un singolo lock file condiviso e dipendenze editabili tra i pacchetti membri. Ispirato ai workspace di Cargo e npm. |
