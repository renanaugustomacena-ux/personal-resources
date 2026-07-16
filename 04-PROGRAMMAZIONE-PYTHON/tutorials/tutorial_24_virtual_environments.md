# Tutorial 24 — Ambienti Virtuali e Gestione Dipendenze

> **Companion a:** `24-virtual-environments.md`
> **Scope:** venv, uv, conda, pip, gestione dipendenze, isolation, reproducibility
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`
> **Durata stimata:** 8-12 ore
> **Stack:** Python 3.12+, uv 0.4+

---

## Mappa concettuale

```
Gestione Ambienti Python
│
├── Problema: conflitti di dipendenze
│   └── Progetto A usa numpy 1.x, Progetto B usa numpy 2.x
│
├── Soluzioni
│   ├── venv — stdlib, semplice
│   ├── virtualenv — più veloce di venv
│   ├── conda — ambienti + pacchetti non-Python
│   └── uv — moderno, ultra-veloce (Rust)
│
├── uv — workflow completo
│   ├── uv init — nuovo progetto
│   ├── uv add/remove — dipendenze
│   ├── uv sync — sincronizza da lockfile
│   ├── uv run — esegui nel venv
│   └── uv python — gestione versioni Python
│
├── Lockfile — riproducibilità
│   ├── uv.lock — generato da uv
│   ├── requirements.txt — classico
│   └── pip-tools — requirements.in → requirements.txt
│
└── Best practice
    ├── Un venv per progetto
    ├── Lockfile in version control
    ├── Dipendenze pin-nate in produzione
    └── Separare dev da produzione
```

---

# Parte A — venv: fondamentali

---

## A1. venv workflow base

```bash
# Creazione ambiente virtuale
python -m venv .venv

# Attivazione
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Verifica (dopo attivazione)
which python           # → .venv/bin/python
python --version       # versione nel venv
pip list               # pacchetti installati

# Installazione pacchetti
pip install httpx pydantic
pip install -r requirements.txt

# Generare requirements.txt (frozen)
pip freeze > requirements.txt

# Disattivazione
deactivate

# Eliminazione (è solo una directory)
rm -rf .venv
```

> **Analogia:** Un ambiente virtuale è come un ufficio dedicato per ogni progetto. Invece di condividere i libri (pacchetti) tra tutti, ogni ufficio ha la propria libreria con le versioni esatte che servono. Puoi avere FastAPI 0.100 in un ufficio e FastAPI 0.115 in un altro, senza che si sovrappongano.

---

# Parte B — uv: workflow moderno

---

## B1. uv per nuovi progetti

```bash
# Installazione uv
pip install uv   # oppure
curl -LsSf https://astral.sh/uv/install.sh | sh

# Nuovo progetto
uv init mio-progetto
cd mio-progetto
# Struttura creata:
# pyproject.toml
# src/mio_progetto/__init__.py
# .python-version    ← versione Python per il progetto

# Gestire versione Python
uv python install 3.12       # scarica Python 3.12
uv python pin 3.12           # imposta per questo progetto

# Aggiungere dipendenze
uv add httpx                 # dipendenza di produzione
uv add pydantic ">=2.0"      # con vincolo versione
uv add --dev pytest ruff     # dipendenze di sviluppo
uv add --group docs mkdocs   # gruppo opzionale

# Rimuovere
uv remove httpx

# Sincronizzare (installa da uv.lock)
uv sync                      # produzione + dev
uv sync --only-group prod    # solo produzione

# Eseguire comandi nel venv senza attivare
uv run python -m pytest
uv run python src/main.py
uv run mypy src/
```

---

## B2. uv.lock — riproducibilità

```bash
# uv.lock è generato automaticamente e va in git
git add uv.lock

# In CI — installa esattamente ciò che c'è nel lockfile
uv sync --frozen   # fallisce se uv.lock non è aggiornato

# Aggiornare dipendenze
uv upgrade                   # aggiorna tutte
uv upgrade httpx             # aggiorna solo httpx
uv upgrade --conservative    # solo aggiornamenti sicuri

# Export per deploy senza uv
uv export --format requirements-txt > requirements.txt
uv export --no-dev > requirements-prod.txt
```

---

# Parte C — conda per data science

---

## C1. conda per ambienti con dipendenze non-Python

```bash
# conda installa anche librerie C/Fortran (numpy, scipy, opencv)
# Utile quando pip non basta

# Nuovo ambiente
conda create -n datasci python=3.12
conda activate datasci

# Installazione (prova conda prima, poi pip per il resto)
conda install numpy scipy matplotlib
conda install -c conda-forge polars
pip install additional-package

# Esporta ambiente
conda env export > environment.yml
conda env export --no-builds > environment-portable.yml

# Ricrea da file
conda env create -f environment.yml

# Lista ambienti
conda env list

# Rimuovi
conda env remove -n datasci
```

---

# Parte D — Best practices produzione

---

## D1. Separare dev da produzione

```toml
# pyproject.toml — approccio moderno con gruppi
[project]
dependencies = [
    "fastapi>=0.115",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-anyio",
    "ruff>=0.4",
    "mypy>=1.10",
]
test = [
    "pytest>=8.0",
    "pytest-cov",
    "httpx",   # per TestClient
]
docs = [
    "mkdocs",
    "mkdocs-material",
]
```

```bash
# Produzione
uv sync --no-dev       # solo dipendenze [project.dependencies]

# CI
uv sync --group test   # + test dependencies

# Sviluppo locale
uv sync                # tutto
```

---

## D2. .python-version e CI

```bash
# .python-version (letto da uv, pyenv, etc.)
3.12.7

# .github/workflows/test.yml
# jobs.test.strategy.matrix.python-version: ["3.12", "3.13"]
```

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --frozen --group test
      - run: uv run pytest --cov
```

---

# Parte E — Riepilogo

## Confronto strumenti

| Strumento | Velocità | Lockfile | Python multi-ver | Non-Python |
|---|---|---|---|---|
| venv + pip | Lento | No (freeze) | No | No |
| poetry | Medio | poetry.lock | Via pyenv | No |
| **uv** | Velocissimo | uv.lock | Sì (built-in) | No |
| conda | Medio | environment.yml | Sì | Sì |

## Comandi uv essenziali

```bash
uv init            # nuovo progetto
uv add PKG         # aggiungi dipendenza
uv remove PKG      # rimuovi
uv sync            # installa da lockfile
uv sync --frozen   # CI (errore se lockfile non aggiornato)
uv run CMD         # esegui nel venv
uv python install  # installa Python
uv build           # crea wheel/sdist
uv publish         # pubblica su PyPI
```

## Prossimi passi

- `tutorial_23_packaging.md` — pubblicare il tuo pacchetto
- `tutorial_27_ci_cd.md` — pipeline che usa `uv sync --frozen`
