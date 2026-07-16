# Tutorial 23 — Packaging Python: pyproject.toml, PyPI, uv

> **Companion a:** `23-packaging.md`
> **Scope:** pyproject.toml, build backend, wheel, PyPI, uv, versioning semantico
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`, `tutorial_24_virtual_environments.md`
> **Durata stimata:** 10-14 ore
> **Stack:** Python 3.12+, uv 0.4+, build, twine, Hatch

---

## Mappa concettuale

```
Packaging Python
│
├── pyproject.toml — standard moderno (PEP 517/518/660)
│   ├── [project] — metadata
│   ├── [project.dependencies] — dipendenze
│   ├── [project.optional-dependencies] — extras
│   ├── [project.scripts] — entry point CLI
│   └── [build-system] — backend build
│
├── Build Backends
│   ├── setuptools — classico, più diffuso
│   ├── hatchling — moderno, Hatch
│   ├── flit — semplice, puro Python
│   └── maturin — pacchetti con Rust
│
├── Distribuzione
│   ├── wheel (.whl) — binario, veloce
│   ├── sdist (.tar.gz) — sorgente
│   ├── PyPI — https://pypi.org
│   └── TestPyPI — test prima di pubblicare
│
├── uv — package manager veloce
│   ├── uv pip install — gestione pacchetti
│   ├── uv venv — ambienti virtuali
│   ├── uv run — esegui nel venv
│   └── uv build/publish — build e upload
│
└── Versioning
    ├── SemVer — MAJOR.MINOR.PATCH
    ├── CalVer — 2024.1, 2024.1.1
    └── bump2version / hatch version
```

---

# Parte A — pyproject.toml completo

---

## A1. Struttura pyproject.toml

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mio-pacchetto"
version = "1.2.3"
description = "Un pacchetto Python di esempio"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Mario Rossi", email = "mario@example.com"},
]
maintainers = [
    {name = "Mario Rossi", email = "mario@example.com"},
]
keywords = ["python", "example", "tutorial"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries",
]
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov",
    "ruff>=0.4",
    "mypy>=1.10",
]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material",
]
all = ["mio-pacchetto[dev,docs]"]

[project.scripts]
miotool = "mio_pacchetto.cli:app"

[project.urls]
Homepage = "https://github.com/utente/mio-pacchetto"
Documentation = "https://mio-pacchetto.readthedocs.io"
Repository = "https://github.com/utente/mio-pacchetto"
"Bug Tracker" = "https://github.com/utente/mio-pacchetto/issues"
Changelog = "https://github.com/utente/mio-pacchetto/blob/main/CHANGELOG.md"

[tool.hatch.version]
path = "src/mio_pacchetto/__init__.py"

[tool.hatch.build.targets.sdist]
include = ["src/", "tests/", "README.md", "CHANGELOG.md"]

[tool.hatch.build.targets.wheel]
packages = ["src/mio_pacchetto"]
```

---

## A2. Struttura del pacchetto (src layout)

```
mio-pacchetto/
├── src/
│   └── mio_pacchetto/
│       ├── __init__.py          # versione, __all__
│       ├── core.py              # logica principale
│       ├── cli.py               # entry point CLI
│       └── py.typed             # marcatore PEP 561 (type stubs inclusi)
├── tests/
│   ├── conftest.py
│   ├── test_core.py
│   └── test_cli.py
├── docs/
│   └── index.md
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── .gitignore
```

```python
# src/mio_pacchetto/__init__.py
"""
Mio Pacchetto — strumento Python di esempio.
"""
__version__ = "1.2.3"
__all__ = ["funzione_principale", "ClassePrincipale"]

from .core import funzione_principale, ClassePrincipale
```

---

# Parte B — Build e pubblicazione

---

## B1. Build con uv

```bash
# Setup progetto con uv
uv init mio-pacchetto
cd mio-pacchetto

# Aggiungere dipendenze
uv add httpx pydantic
uv add --dev pytest ruff mypy

# Costruire il pacchetto
uv build
# Output:
# dist/
#   mio_pacchetto-1.2.3-py3-none-any.whl
#   mio_pacchetto-1.2.3.tar.gz

# Verificare il contenuto del wheel
unzip -l dist/mio_pacchetto-*.whl

# Pubblicare su TestPyPI (prima del release)
uv publish --repository testpypi

# Pubblicare su PyPI
uv publish

# Con credenziali esplicite
uv publish --token pypi-XXXXXXXXXXX
```

---

## B2. Versioning semantico e changelog

```python
# src/mio_pacchetto/__init__.py
__version__ = "1.2.3"
# MAJOR.MINOR.PATCH
# MAJOR: breaking change (API incompatibile)
# MINOR: nuova funzionalità retrocompatibile
# PATCH: bug fix retrocompatibile
```

```bash
# Bump versione con hatch
hatch version patch   # 1.2.3 → 1.2.4
hatch version minor   # 1.2.3 → 1.3.0
hatch version major   # 1.2.3 → 2.0.0

# Pre-release
hatch version rc      # 1.2.3 → 1.2.4rc1
```

```markdown
# CHANGELOG.md (formato Keep a Changelog)

## [Unreleased]

## [1.2.3] - 2024-01-15

### Added
- Nuova funzione `calcola_sconto_bulk()`
- Supporto per autenticazione OAuth2

### Fixed
- Correzione errore di encoding UTF-8 su Windows (#42)

### Changed
- `processa_dati()` ora ritorna un dataclass invece di dict

### Deprecated
- `vecchia_api()` verrà rimossa in 2.0

### Removed
- Rimosso supporto Python 3.10

## [1.2.2] - 2024-01-01
...
```

---

# Parte C — Dipendenze e sicurezza

---

## C1. Lock file e riproducibilità

```bash
# uv genera uv.lock automaticamente
uv sync              # installa da uv.lock (riproducibile)
uv sync --frozen     # errore se uv.lock non è aggiornato (CI)

# Export requirements.txt per compatibilità
uv export --format requirements-txt > requirements.txt
uv export --format requirements-txt --only-group dev > requirements-dev.txt

# Aggiornare dipendenze
uv upgrade           # aggiorna tutto
uv upgrade httpx     # aggiorna solo httpx

# Audit sicurezza dipendenze
pip audit            # cerca CVE nelle dipendenze
uv pip audit         # alternativa uv

# Verifica licenze
pip-licenses --format=markdown
```

---

## C2. py.typed e distribuzione di stub

```python
# src/mio_pacchetto/py.typed
# File vuoto — segnala a mypy che il pacchetto ha tipi inline (PEP 561)

# Verifica che mypy trovi i tipi
# pyproject.toml
[tool.mypy]
packages = ["mio_pacchetto"]

# Tipi esportati devono essere in __all__
# src/mio_pacchetto/core.py
from typing import overload

def processa(dati: str) -> str:
    return dati.upper()

# Se il pacchetto non ha tipi inline, creare file stub:
# src/mio_pacchetto-stubs/core.pyi
def processa(dati: str) -> str: ...
```

---

# Parte D — CI/CD per pacchetti

---

## D1. GitHub Actions per build e publish

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --frozen
      - run: uv run pytest --cov=mio_pacchetto
      - run: uv run mypy src/
      - run: uv run ruff check .
      - run: uv build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # per Trusted Publisher (senza API key)
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

# Parte E — Riepilogo

## Checklist pubblicazione pacchetto

- [ ] `pyproject.toml` con tutti i metadata richiesti
- [ ] Versione semantica aggiornata
- [ ] CHANGELOG.md aggiornato
- [ ] Test passanti con copertura > 80%
- [ ] Type checking mypy senza errori
- [ ] Lint ruff senza warning
- [ ] `py.typed` presente se esporti tipi
- [ ] README.md con installazione, quickstart, esempi
- [ ] Test su TestPyPI prima di produzione
- [ ] Tag git: `git tag v1.2.3 && git push --tags`

## Prossimi passi

- `tutorial_27_ci_cd.md` — pipeline CI/CD completa
- `tutorial_32_packaging_avanzato.md` — plugin, namespace packages, Rust extensions
