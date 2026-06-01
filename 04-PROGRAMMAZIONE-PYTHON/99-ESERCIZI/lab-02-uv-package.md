# Lab 02 — Creare e Pubblicare una Libreria Python con uv e Trusted Publishers

> **Moduli di riferimento:** [23-packaging-distribuzione.md](../23-packaging-distribuzione.md) (base), [32-packaging-distribuzione.md](../32-packaging-distribuzione.md) (avanzato)
> **Tempo stimato:** 4-5 ore
> **Livello:** proficient
> **Prerequisiti:** completamento moduli 01, 08, [09](../09-type-hints-e-mypy.md), [23](../23-packaging-distribuzione.md), [24](../24-virtual-environments.md); account GitHub e PyPI; `uv` >= 0.7 installato
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Il team backend ha accumulato utility di validazione dati duplicate in almeno quattro microservizi.
Il tech lead chiede di estrarre la logica in una libreria interna, `validapy`, con le seguenti specifiche:

- src-layout PEP 621
- type hints strict con mypy
- test suite pytest >= 80 % coverage
- CI con GitHub Actions (lint, type-check, test, build)
- pubblicazione automatica su PyPI via Trusted Publishers (OIDC, zero secret)

---

## Obiettivi di Apprendimento

1. Inizializzare un progetto libreria con `uv init --lib` e layout `src/`.
2. Scrivere un `pyproject.toml` PEP 621 completo.
3. Applicare type hints strict e configurare mypy in modalita rigorosa.
4. Costruire una test suite pytest con copertura >= 80 %.
5. Configurare ruff (linter + formatter) nel `pyproject.toml`.
6. Impostare pre-commit hooks per ruff e mypy.
7. Generare wheel + sdist con `uv build` e lockfile con `uv lock`.
8. Utilizzare PEP 660 editable install per sviluppo locale.
9. Creare una pipeline GitHub Actions completa.
10. Configurare Trusted Publishers OIDC su PyPI e pubblicare con `uv publish`.
11. Gestire il versionamento della libreria.
12. Comprendere le implicazioni manylinux per estensioni binarie.

---

## Parte 1 — Inizializzazione del Progetto (20 min)

### 1.1 Creare il progetto con uv

```bash
uv init --lib validapy
cd validapy
```

`uv init --lib` genera automaticamente il src-layout:

```
validapy/
├── pyproject.toml
├── README.md
└── src/
    └── validapy/
        ├── __init__.py
        └── py.typed        # PEP 561 marker
```

### 1.2 Configurare pyproject.toml (PEP 621)

Sostituire il contenuto generato con una configurazione completa:

```toml
[project]
name = "validapy"
version = "0.1.0"
description = "Utility di validazione dati per microservizi Python."
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [{ name = "Il Tuo Nome", email = "nome@example.com" }]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]

[project.urls]
Repository = "https://github.com/tuonome/validapy"
Issues = "https://github.com/tuonome/validapy/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/validapy"]
```

### 1.3 Aggiungere le dipendenze di sviluppo

```bash
uv add --dev pytest pytest-cov mypy ruff pre-commit
```

Verificare che `uv.lock` sia stato generato:

```bash
ls -la uv.lock
cat uv.lock | head -20
```

---

## Parte 2 — Scrivere la Libreria (40 min)

### 2.1 Modulo principale: validatori

Creare `src/validapy/validators.py`:

```python
"""Validatori di dati riutilizzabili con type hints strict."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

_EMAIL_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
_CODICE_FISCALE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$"
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Risultato immutabile di una validazione."""
    is_valid: bool
    field: str
    message: str

    def __bool__(self) -> bool:
        return self.is_valid


def validate_email(value: str, *, field: str = "email") -> ValidationResult:
    """Valida un indirizzo email."""
    if not value or not value.strip():
        return ValidationResult(is_valid=False, field=field, message="Campo obbligatorio.")
    if not _EMAIL_RE.match(value.strip()):
        return ValidationResult(is_valid=False, field=field, message="Formato email non valido.")
    return ValidationResult(is_valid=True, field=field, message="OK")


def validate_codice_fiscale(value: str, *, field: str = "codice_fiscale") -> ValidationResult:
    """Valida un codice fiscale italiano (formato sintattico)."""
    normalized = value.strip().upper()
    if len(normalized) != 16:
        return ValidationResult(
            is_valid=False, field=field, message="Il codice fiscale deve avere 16 caratteri."
        )
    if not _CODICE_FISCALE_RE.match(normalized):
        return ValidationResult(
            is_valid=False, field=field, message="Formato codice fiscale non valido."
        )
    return ValidationResult(is_valid=True, field=field, message="OK")


def validate_range(
    value: int | float,
    *,
    min_val: int | float | None = None,
    max_val: int | float | None = None,
    field: str = "value",
) -> ValidationResult:
    """Valida che un valore numerico sia entro un intervallo."""
    if min_val is not None and value < min_val:
        return ValidationResult(is_valid=False, field=field, message=f"Deve essere >= {min_val}.")
    if max_val is not None and value > max_val:
        return ValidationResult(is_valid=False, field=field, message=f"Deve essere <= {max_val}.")
    return ValidationResult(is_valid=True, field=field, message="OK")
```

### 2.2 Modulo composto: pipeline di validazione

Creare `src/validapy/pipeline.py`:

```python
"""Pipeline di validazione composabile."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from validapy.validators import ValidationResult

ValidatorFn = Callable[..., ValidationResult]


def run_validators(
    validators: Sequence[tuple[ValidatorFn, dict[str, Any]]],
) -> list[ValidationResult]:
    """Esegue una sequenza di validatori, raccoglie tutti i risultati."""
    return [fn(**kwargs) for fn, kwargs in validators]


def all_valid(results: Sequence[ValidationResult]) -> bool:
    """True se tutti i risultati sono validi."""
    return all(results)


def collect_errors(results: Sequence[ValidationResult]) -> list[ValidationResult]:
    """Filtra solo i risultati non validi."""
    return [r for r in results if not r.is_valid]
```

### 2.3 Esporre l'API pubblica

Aggiornare `src/validapy/__init__.py`:

```python
"""validapy — Utility di validazione dati."""

from validapy.pipeline import all_valid, collect_errors, run_validators
from validapy.validators import (
    ValidationResult,
    validate_codice_fiscale,
    validate_email,
    validate_range,
)

__all__ = [
    "ValidationResult",
    "all_valid",
    "collect_errors",
    "run_validators",
    "validate_codice_fiscale",
    "validate_email",
    "validate_range",
]
```

Verificare il marker PEP 561:

```bash
ls src/validapy/py.typed   # deve esistere; se mancante:
touch src/validapy/py.typed
```

---

## Parte 3 — Type Hints e mypy Strict (20 min)

### 3.1 Configurare mypy nel pyproject.toml

Aggiungere al `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### 3.2 Eseguire la verifica

```bash
uv run mypy src/
```

Target: zero errori. Se il codice della Parte 2 e stato scritto correttamente, il check passa
al primo tentativo. Correggere ogni finding prima di procedere.

> **Riferimento:** [09-type-hints-e-mypy.md](../09-type-hints-e-mypy.md) per approfondimenti su
> `Protocol`, `TypeVar`, `reveal_type()`.

---

## Parte 4 — Test Suite con pytest (40 min)

### 4.1 Struttura test

```
tests/
├── __init__.py
├── conftest.py
├── test_validators.py
└── test_pipeline.py
```

### 4.2 test_validators.py

```python
from __future__ import annotations

import pytest
from validapy.validators import validate_codice_fiscale, validate_email, validate_range


class TestValidateEmail:
    def test_valid_email(self) -> None:
        result = validate_email("user@example.com")
        assert result.is_valid
        assert result.field == "email"

    def test_empty_string_fails(self) -> None:
        assert not validate_email("").is_valid

    def test_missing_at_sign(self) -> None:
        assert not validate_email("userexample.com").is_valid

    def test_custom_field_name(self) -> None:
        assert validate_email("bad", field="contact_email").field == "contact_email"

    @pytest.mark.parametrize("addr", ["a@b.co", "test.user+tag@domain.org"])
    def test_valid_formats(self, addr: str) -> None:
        assert validate_email(addr).is_valid


class TestValidateCodiceFiscale:
    def test_valid_cf(self) -> None:
        assert validate_codice_fiscale("RSSMRA85M01H501Z").is_valid

    def test_too_short(self) -> None:
        assert not validate_codice_fiscale("RSSMRA").is_valid

    def test_lowercase_normalized(self) -> None:
        assert validate_codice_fiscale("rssmra85m01h501z").is_valid


class TestValidateRange:
    def test_within_range(self) -> None:
        assert validate_range(5, min_val=1, max_val=10).is_valid

    def test_below_min(self) -> None:
        assert not validate_range(0, min_val=1).is_valid

    def test_above_max(self) -> None:
        assert not validate_range(100, max_val=50).is_valid
```

### 4.3 test_pipeline.py

```python
from __future__ import annotations

from validapy.pipeline import all_valid, collect_errors, run_validators
from validapy.validators import validate_email, validate_range


class TestPipeline:
    def test_all_pass(self) -> None:
        results = run_validators([
            (validate_email, {"value": "ok@test.com"}),
            (validate_range, {"value": 5, "min_val": 1, "max_val": 10}),
        ])
        assert all_valid(results)
        assert collect_errors(results) == []

    def test_mixed_results(self) -> None:
        results = run_validators([
            (validate_email, {"value": "bad"}),
            (validate_range, {"value": 5, "min_val": 1, "max_val": 10}),
        ])
        assert not all_valid(results)
        assert len(collect_errors(results)) == 1

    def test_empty_validators(self) -> None:
        assert all_valid(run_validators([]))
```

### 4.4 Eseguire i test con coverage

```bash
uv run pytest tests/ -v --cov=validapy --cov-report=term-missing --cov-fail-under=80
```

Target: tutti i test verdi, copertura >= 80 %. Aggiungere test fino a raggiungere il target.

---

## Parte 5 — Configurazione ruff (15 min)

### 5.1 Aggiungere la configurazione al pyproject.toml

```toml
[tool.ruff]
target-version = "py312"
line-length = 99
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "SIM", "RUF", "S", "ANN", "D"]
ignore = ["D100", "D104", "ANN101", "S101"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "ANN", "D"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 5.2 Verificare

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Correggere ogni finding. ruff e il linter e formatter del progetto — non usare altri strumenti.

---

## Parte 6 — Pre-commit Hooks (15 min)

### 6.1 Creare `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        additional_dependencies: []
        args: [--config-file=pyproject.toml]
        pass_filenames: false

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
```

> **Nota:** pinnare le `rev` a tag specifici. Prima di usare i valori sopra,
> verificare le versioni correnti su ogni repository.

### 6.2 Installare e testare

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Ogni hook deve passare. Correggere e ri-eseguire fino a zero errori.

---

## Parte 7 — Build e Lockfile (20 min)

### 7.1 Generare il lockfile deterministico

```bash
uv lock
```

`uv.lock` fissa le versioni esatte di tutte le dipendenze (dirette e transitive).
Committare sempre questo file — garantisce build riproducibili.

### 7.2 PEP 660 — Editable install

Per lo sviluppo locale, installare in modalita editable:

```bash
uv pip install -e ".[dev]"
```

Oppure, con uv:

```bash
uv sync
```

`uv sync` installa il progetto in modalita editable di default nel virtualenv del progetto.
Le modifiche ai sorgenti in `src/` sono immediatamente disponibili senza reinstallare.

### 7.3 Build wheel e sdist

```bash
uv build
```

Output in `dist/`:

```
dist/
├── validapy-0.1.0-py3-none-any.whl
└── validapy-0.1.0.tar.gz
```

Verificare il contenuto del wheel:

```bash
unzip -l dist/validapy-0.1.0-py3-none-any.whl
```

Il wheel deve contenere `validapy/`, `validapy/py.typed`, e i moduli `.py`.
Non deve contenere `tests/`, `.pre-commit-config.yaml`, o file di configurazione.

---

## Parte 8 — Gestione Versione (15 min)

### 8.1 Strategia single-source

La versione e definita in un unico punto: `pyproject.toml`. Per esporla a runtime:

```python
# src/validapy/__init__.py  (aggiungere in testa)
from importlib.metadata import version

__version__ = version("validapy")
```

### 8.2 Bump di versione

Per ogni release, aggiornare `version` in `pyproject.toml`:

```toml
version = "0.2.0"
```

Committare, taggare, e ricostruire:

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
uv build
```

> Per progetti con molti collaboratori, considerare `python-semantic-release` o `bump-my-version`.
> Per una libreria piccola, il bump manuale e sufficiente e piu trasparente.

---

## Parte 9 — GitHub Actions CI (30 min)

### 9.1 Creare `.github/workflows/ci.yml`

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
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Installare uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "latest"

      - name: Configurare Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Installare dipendenze
        run: uv sync --frozen

      - name: Lint (ruff)
        run: uv run ruff check src/ tests/

      - name: Format check (ruff)
        run: uv run ruff format --check src/ tests/

      - name: Type check (mypy)
        run: uv run mypy src/

      - name: Test con coverage
        run: uv run pytest tests/ -v --cov=validapy --cov-report=xml --cov-fail-under=80

      - name: Build
        run: uv build
```

### 9.2 Workflow di pubblicazione

Creare `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write    # Necessario per OIDC Trusted Publishers

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          version: "latest"

      - run: uv python install 3.12

      - run: uv sync --frozen

      - name: Lint + Type check + Test
        run: |
          uv run ruff check src/ tests/
          uv run mypy src/
          uv run pytest tests/ --cov=validapy --cov-fail-under=80

      - name: Build
        run: uv build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi

    steps:
      - uses: astral-sh/setup-uv@v5
        with:
          version: "latest"

      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish via Trusted Publisher
        run: uv publish --trusted-publishing always dist/*
```

> **Riferimento:** [27-ci-cd-per-python.md](../27-ci-cd-per-python.md) per approfondimenti
> su pipeline, matrix strategy, caching.

---

## Parte 10 — Trusted Publishers su PyPI (30 min)

### 10.1 Che cos'e Trusted Publishing

Trusted Publishers elimina i token API da PyPI usando OpenID Connect (OIDC):
GitHub Actions ottiene un token OIDC dal proprio identity provider, PyPI lo verifica
contro il publisher registrato. Se repo, workflow e environment corrispondono,
la pubblicazione e autorizzata. Zero secret da gestire o ruotare.

### 10.2 Configurazione su PyPI

1. Accedere a https://pypi.org e navigare al progetto `validapy`.
   - Se il pacchetto non esiste ancora, usare "Pending Publisher" sotto il proprio account.
2. Andare in **Publishing** > **Add a new publisher**.
3. Compilare:
   - **Owner:** `tuonome` (username/org GitHub)
   - **Repository:** `validapy`
   - **Workflow name:** `publish.yml`
   - **Environment:** `pypi`
4. Salvare.

### 10.3 Configurazione GitHub Environment

1. Nel repository GitHub, andare in **Settings** > **Environments**.
2. Creare l'environment `pypi`.
3. Aggiungere una **protection rule**: richiedere approvazione manuale (opzionale ma consigliato).
4. Non servono secret — OIDC gestisce tutto.

### 10.4 Prima pubblicazione

```bash
# Creare una release su GitHub (via UI o CLI):
gh release create v0.1.0 --title "v0.1.0" --notes "Release iniziale."
```

Il workflow `publish.yml` si attiva automaticamente, costruisce, verifica, e pubblica.

Verificare su https://pypi.org/project/validapy/ che il pacchetto sia disponibile.

### 10.5 TestPyPI (consigliato per il primo tentativo)

Per testare senza inquinare PyPI di produzione:

1. Registrare il Trusted Publisher anche su https://test.pypi.org.
2. Modificare temporaneamente il workflow:

```yaml
      - name: Publish to TestPyPI
        run: uv publish --trusted-publishing always --publish-url https://test.pypi.org/legacy/ dist/*
```

3. Verificare l'installazione:

```bash
uv pip install --index-url https://test.pypi.org/simple/ validapy
```

---

## Parte 11 — Considerazioni manylinux per Estensioni Binarie (15 min)

> Questa sezione e concettuale. La libreria `validapy` e pure-Python (`py3-none-any.whl`).
> Le informazioni seguenti si applicano quando una libreria include estensioni C/C++/Rust.

### 11.1 Quando serve manylinux

Se il pacchetto include codice compilato (`.so`, `.pyd`), il wheel non puo essere `any`:

```
# Wheel pure-Python:
validapy-0.1.0-py3-none-any.whl

# Wheel con estensione binaria:
validapy-0.1.0-cp312-cp312-manylinux_2_17_x86_64.whl
```

### 11.2 Strumenti per build binari

| Strumento | Uso |
|-----------|-----|
| `cibuildwheel` | Build automatizzato multi-piattaforma in CI |
| `maturin` | Build per estensioni Rust (PyO3) |
| `meson-python` | Build per estensioni C/C++ via Meson |

### 11.3 Tag manylinux

| Tag | glibc | Uso tipico |
|-----|-------|------------|
| `manylinux_2_17` | RHEL 7+ | Il piu comune |
| `manylinux_2_28` | RHEL 8+ | Librerie con glibc recente |
| `musllinux_1_2` | musl | Alpine Linux |

Per `validapy` (pure-Python) nessuna di queste si applica. Se in futuro si aggiungesse
un modulo C, valutare `cibuildwheel` e `auditwheel repair`.

> **Riferimento:** [32-packaging-distribuzione.md](../32-packaging-distribuzione.md) per
> dettagli su build system, PEP 517, e gestione estensioni native.

---

## Parte 12 — Verifica Finale (20 min)

### 12.1 Checklist completa dal terminale

```bash
# 1. Lint
uv run ruff check src/ tests/

# 2. Format
uv run ruff format --check src/ tests/

# 3. Type check
uv run mypy src/

# 4. Test + coverage
uv run pytest tests/ -v --cov=validapy --cov-report=term-missing --cov-fail-under=80

# 5. Build
uv build

# 6. Verificare contenuto wheel
unzip -l dist/validapy-*.whl

# 7. Verificare lockfile
uv lock --check

# 8. Pre-commit su tutti i file
uv run pre-commit run --all-files
```

Tutti i comandi devono terminare con exit code 0.

### 12.2 Installazione di verifica

In un ambiente separato, testare l'installazione dal wheel locale:

```bash
cd /tmp
uv venv test-install
source test-install/bin/activate
uv pip install /path/to/validapy/dist/validapy-0.1.0-py3-none-any.whl
python -c "from validapy import validate_email; print(validate_email('test@ok.com'))"
deactivate
rm -rf test-install
```

---

## Deliverable

- [ ] Repository Git con struttura src-layout completa
- [ ] `pyproject.toml` PEP 621 con configurazione ruff e mypy
- [ ] Codice libreria in `src/validapy/` con type hints strict (zero errori mypy)
- [ ] Marker `py.typed` (PEP 561) presente
- [ ] Test suite in `tests/` con copertura >= 80 %
- [ ] `uv.lock` committato e verificabile con `uv lock --check`
- [ ] `.pre-commit-config.yaml` con hook ruff e mypy funzionanti
- [ ] `.github/workflows/ci.yml` — lint, type-check, test, build su Python 3.12 e 3.13
- [ ] `.github/workflows/publish.yml` — pubblicazione OIDC senza secret
- [ ] Trusted Publisher configurato su PyPI (o TestPyPI)
- [ ] Almeno una release pubblicata con successo
- [ ] Wheel e sdist in `dist/` verificati

---

## Criteri di Valutazione

| Criterio | Peso | Sufficiente | Buono | Eccellente |
|----------|------|-------------|-------|------------|
| `pyproject.toml` PEP 621 completo | 10 % | Campi minimi (name, version) | + classifiers, urls, requires-python | + build-system configurato, tool sections complete |
| Type hints e mypy strict | 15 % | Annotazioni parziali, mypy base | Annotazioni complete, mypy strict zero errori | + `py.typed`, generics corretti, Protocol se utile |
| Test suite e coverage | 20 % | >= 60 % coverage, test base | >= 80 %, parametrize, edge cases | >= 90 %, fixture, test negativi, boundary |
| Configurazione ruff | 10 % | select base (E, F) | + isort, pyupgrade, bugbear | + bandit, pydocstyle, per-file-ignores |
| Pre-commit hooks | 5 % | ruff presente | + mypy, trailing-whitespace | + check-toml, check-yaml, rev pinnate |
| CI pipeline | 15 % | Workflow base funzionante | + matrix Python, --frozen | + artifact upload, step separati |
| Trusted Publishers OIDC | 15 % | Configurazione descritta | TestPyPI funzionante | PyPI produzione con environment protection |
| Build e lockfile | 5 % | `uv build` funzionante | + `uv lock --check` passa | + contenuto wheel verificato |
| Struttura progetto | 5 % | src-layout presente | + README, LICENSE, .gitignore | + struttura pulita, no file superflui |

---

## Riferimenti

- [23-packaging-distribuzione.md](../23-packaging-distribuzione.md) — packaging base, `pyproject.toml`, wheel vs sdist
- [32-packaging-distribuzione.md](../32-packaging-distribuzione.md) — packaging avanzato, build backend, PEP 517/660
- [24-virtual-environments.md](../24-virtual-environments.md) — venv, `uv sync`, isolamento dipendenze
- [27-ci-cd-per-python.md](../27-ci-cd-per-python.md) — GitHub Actions, matrix, pipeline Python
- [09-type-hints-e-mypy.md](../09-type-hints-e-mypy.md) — type hints, mypy strict, `py.typed`
- PEP 621 — Project metadata: https://peps.python.org/pep-0621/
- PEP 660 — Editable installs: https://peps.python.org/pep-0660/
- PEP 561 — Typed packages: https://peps.python.org/pep-0561/
- uv documentazione: https://docs.astral.sh/uv/
- PyPI Trusted Publishers: https://docs.pypi.org/trusted-publishers/
