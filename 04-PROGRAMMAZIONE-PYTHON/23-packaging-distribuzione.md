---
corso: "Programmazione Python"
fase: "6 — DevOps e Distribuzione"
modulo: "23"
titolo: "Packaging e Distribuzione"
versione: "setuptools 75+ / hatchling 1.x / uv 0.7+"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "24 — Virtual Environments"
  - "06 — Moduli e Pacchetti"
obiettivi:
  - "Configurare pyproject.toml con build backend moderni"
  - "Costruire e pubblicare pacchetti su PyPI e registri privati"
  - "Gestire versioning semantico e changelog automatizzato"
  - "Creare distribuzioni wheel e sdist conformi agli standard"
  - "Pubblicare con Trusted Publishers e firmare con sigstore"
  - "Automatizzare il release workflow con CI/CD"
tag: [packaging, pyproject-toml, PyPI, wheel, setuptools, hatchling, uv, versioning]
---

# Packaging e Distribuzione — Guida Completa

> **Modulo 23** · **Aggiornamento:** 2026-05-24 · **Versione:** setuptools 75+ / hatchling 1.x / uv 0.7+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Virtual Environments](24-virtual-environments.md), [Moduli e Pacchetti](06-regex-e-text-processing.md)
>
> Al termine di questo modulo saprai:
> 1. Configurare `pyproject.toml` con build backend moderni (setuptools, hatchling, flit)
> 2. Costruire e pubblicare pacchetti su PyPI e registri privati
> 3. Gestire versioning semantico e changelog automatizzato
> 4. Creare distribuzioni wheel e sdist conformi agli standard PEP
> 5. Pubblicare con Trusted Publishers e firmare con sigstore
> 6. Automatizzare il release workflow con CI/CD
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio

## Idee guida
1. **`pyproject.toml` (PEP 621) standard moderno.**
2. **`uv build` > `python -m build` per speed.**
3. **manylinux/universal2 wheels per portabilita.**
4. **PyPI Trusted Publishers (OIDC) > API token.**
5. **Wheel = zip rinominato: layout deterministico, RECORD, METADATA standard.**
6. **Semantic versioning (PEP 440) come contratto con gli utenti.**
7. **Namespace packages (PEP 420) per ecosistemi multi-pacchetto.**


## Mappa concettuale

```
                        ┌─────────────────────┐
                        │   pyproject.toml     │
                        │   (PEP 518/621)      │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
             ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
             │ [project]  │ │[build-sys] │ │ [tool.*] │
             │ metadati   │ │ backend    │ │ config   │
             │ deps       │ │ requires   │ │ ruff/mypy│
             │ scripts    │ │            │ │ pytest   │
             └──────┬─────┘ └─────┬──────┘ └──────────┘
                    │             │
                    │      ┌──────▼──────┐
                    │      │ Build       │
                    │      │ backend     │
                    │      │ setuptools  │
                    │      │ hatchling   │
                    │      │ flit/poetry │
                    │      └──────┬──────┘
                    │             │
              ┌─────▼─────┐ ┌────▼─────┐
              │  sdist     │ │  wheel   │
              │ .tar.gz    │ │  .whl    │
              └─────┬─────┘ └────┬─────┘
                    │            │
                    └──────┬─────┘
                           │
                    ┌──────▼──────┐
                    │ Distribuzione│
                    │ PyPI/privato│
                    │ twine/OIDC  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼────┐ ┌────▼──────┐
        │ pip      │ │ uv     │ │ eseguibili │
        │ install  │ │ add    │ │ PyInstaller│
        └──────────┘ └────────┘ │ Nuitka     │
                                └────────────┘
```


## Indice

1. [Panoramica](#panoramica)
2. [Struttura Progetto](#struttura-progetto)
   - [Layout Standard](#layout-standard)
   - [src layout vs flat layout](#src-layout-vs-flat-layout)
   - [File speciali: \_\_init\_\_.py, \_\_main\_\_.py, \_\_version\_\_](#file-speciali)
3. [pyproject.toml](#pyprojecttoml)
   - [Configurazione Completa](#configurazione-completa)
   - [Esempio Completo](#esempio-completo-pyprojecttoml)
4. [Build System](#build-system)
   - [setuptools](#setuptools)
   - [Hatchling](#hatchling)
   - [Poetry](#poetry)
   - [Flit](#flit)
5. [Evoluzione: da setup.py a pyproject.toml](#evoluzione-da-setuppy-a-pyprojecttoml)
6. [Versioning](#versioning)
   - [PEP 440 in dettaglio](#pep-440-in-dettaglio)
7. [Build e Distribuzione](#build-e-distribuzione)
   - [Creazione Pacchetto](#creazione-pacchetto)
   - [Formato Wheel — Internals](#formato-wheel--internals)
   - [Source Distribution e MANIFEST.in](#source-distribution-e-manifestin)
   - [PyPI](#pypi)
   - [Private Package Index](#private-package-index)
8. [Entry Points e Console Scripts](#entry-points-e-console-scripts)
9. [Classifiers PyPI](#classifiers-pypi)
10. [Namespace Packages](#namespace-packages)
11. [Editable Installs](#editable-installs)
12. [Distribuzione Eseguibili](#distribuzione-eseguibili)
    - [PyInstaller](#pyinstaller)
    - [Nuitka](#nuitka)
    - [cx_Freeze](#cx_freeze)
    - [Briefcase (BeeWare)](#briefcase-beeware)
13. [Distribuzione Interna](#distribuzione-interna)
14. [pyproject.toml Deep-Dive](#pyprojecttoml-deep-dive)
    - [Campi statici e dinamici](#campi-statici-e-dinamici)
    - [Optional dependencies avanzate](#optional-dependencies-avanzate)
    - [Licenze secondo PEP 639](#licenze-secondo-pep-639)
15. [Confronto Build Backends](#confronto-build-backends)
    - [setuptools vs hatchling vs flit vs maturin vs pdm-backend](#setuptools-vs-hatchling-vs-flit-vs-maturin-vs-pdm-backend)
    - [uv_build — il nuovo backend di Astral](#uv_build--il-nuovo-backend-di-astral)
16. [uv come Package Manager](#uv-come-package-manager)
    - [Workspace e monorepo](#workspace-e-monorepo)
    - [Lockfile universale](#lockfile-universale)
    - [Script runner con dipendenze inline](#script-runner-con-dipendenze-inline)
17. [Strategie di Versioning Avanzate](#strategie-di-versioning-avanzate)
    - [SemVer vs CalVer in pratica](#semver-vs-calver-in-pratica)
    - [setuptools-scm in dettaglio](#setuptools-scm-in-dettaglio)
    - [bump-my-version e automazione](#bump-my-version-e-automazione)
18. [Estensioni C e Binarie](#estensioni-c-e-binarie)
    - [Cython build moderno](#cython-build-moderno)
    - [CFFI per interfacce C](#cffi-per-interfacce-c)
    - [Maturin e PyO3 per Rust](#maturin-e-pyo3-per-rust)
    - [cibuildwheel per CI](#cibuildwheel-per-ci)
19. [Wheels e sdist — Internals Avanzati](#wheels-e-sdist--internals-avanzati)
    - [Platform tags in dettaglio](#platform-tags-in-dettaglio)
    - [manylinux e musllinux](#manylinux-e-musllinux)
    - [Packaging per piattaforme multiple](#packaging-per-piattaforme-multiple)
20. [Private PyPI Avanzato](#private-pypi-avanzato)
    - [devpi in produzione](#devpi-in-produzione)
    - [JFrog Artifactory](#jfrog-artifactory)
    - [AWS CodeArtifact avanzato](#aws-codeartifact-avanzato)
21. [Pubblicazione Automatica e Sicurezza](#pubblicazione-automatica-e-sicurezza)
    - [Trusted Publishers in dettaglio](#trusted-publishers-in-dettaglio)
    - [Sigstore e firma dei pacchetti](#sigstore-e-firma-dei-pacchetti)
    - [OIDC internals](#oidc-internals)
22. [Monorepo Packaging](#monorepo-packaging)
    - [Struttura monorepo Python](#struttura-monorepo-python)
    - [uv workspace in pratica](#uv-workspace-in-pratica)
    - [Release coordination](#release-coordination)
23. [Best Practices](#best-practices)
24. [Esercizi](#esercizi)
25. [Letture](#letture)
26. [Moduli Correlati](#moduli-correlati)
27. [Glossario](#glossario)

---

## Panoramica

Il packaging Python ha attraversato una trasformazione profonda nell'ultimo decennio. Per anni, `setup.py` — un file Python eseguibile che invocava `setuptools.setup()` — era l'unico modo per definire un pacchetto. Questo approccio presentava problemi strutturali: il file di configurazione era codice arbitrario, il che rendeva impossibile l'analisi statica dei metadati e creava rischi di sicurezza (l'esecuzione di `setup.py` poteva avere effetti collaterali). Inoltre, non esisteva un modo standard per dichiarare le dipendenze di build prima di eseguire il build stesso — un problema circolare noto come "bootstrap problem".

Tre PEP fondamentali hanno risolto queste problematiche e definito l'architettura moderna:

**PEP 518 (2016)** — ha introdotto il file `pyproject.toml` e la tabella `[build-system]`. Per la prima volta, un progetto poteva dichiarare in modo statico quali strumenti servivano per la fase di build (`requires`) e quale backend utilizzare (`build-backend`). Questo ha rotto il ciclo di dipendenza circolare: pip legge `pyproject.toml`, installa le dipendenze di build in un ambiente isolato, quindi invoca il backend dichiarato.

**PEP 517 (2017)** — ha definito l'interfaccia standard tra un frontend di build (come `pip` o `build`) e un backend di build (come `setuptools`, `hatchling`, `flit`). L'interfaccia si riduce a poche funzioni Python: `build_wheel()`, `build_sdist()`, `get_requires_for_build_wheel()`. Qualsiasi strumento che implementi queste funzioni puo fungere da backend, creando un ecosistema aperto e competitivo.

**PEP 621 (2020)** — ha standardizzato la tabella `[project]` all'interno di `pyproject.toml`, definendo campi come `name`, `version`, `description`, `dependencies`, `authors`, `license`. Prima di questo PEP, ogni build system utilizzava la propria sezione di configurazione (Poetry usava `[tool.poetry]`, Flit usava `[tool.flit]`), rendendo i metadati non portabili tra strumenti diversi.

Il risultato di questa evoluzione e un ecosistema dove `pyproject.toml` e il centro di gravita: un singolo file TOML contiene i metadati del progetto, le dipendenze, la configurazione del build system e le impostazioni di strumenti come pytest, mypy, ruff e black. Non serve piu scrivere codice Python per configurare il packaging — basta una dichiarazione statica leggibile sia dagli esseri umani che dalle macchine.

| Periodo | Approccio | File principale | Problemi |
|---------|-----------|-----------------|----------|
| 2000-2014 | distutils/setuptools | setup.py | Codice arbitrario, nessun isolamento build |
| 2014-2018 | setuptools + pip | setup.py + setup.cfg | Ancora codice eseguibile, no standard metadati |
| 2018-2021 | PEP 517/518 | pyproject.toml + setup.cfg | Transizione incompleta, doppia configurazione |
| 2021-oggi | PEP 621 completo | pyproject.toml | Standard moderno, dichiarativo, portabile |

---

## Struttura Progetto

### Layout Standard

Un progetto Python professionale segue una struttura prevedibile che facilita la navigazione, il testing e il packaging. La struttura raccomandata dalla documentazione ufficiale di Python Packaging Authority (PyPA) e la seguente:

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core.py
│       ├── utils.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core.py
│   ├── test_utils.py
│   └── test_cli.py
├── docs/
│   ├── conf.py
│   └── index.rst
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
└── .gitignore
```

Ogni directory ha un ruolo preciso. `src/` contiene il codice sorgente del pacchetto, isolato dal resto del progetto. `tests/` contiene i test, separati dal codice di produzione. `docs/` ospita la documentazione (tipicamente generata con Sphinx o MkDocs). Nella root del progetto si trovano i file di configurazione: `pyproject.toml` per il packaging e gli strumenti di sviluppo, `README.md` per la descrizione del progetto, `LICENSE` per la licenza, `CHANGELOG.md` per il registro delle modifiche.

### src layout vs flat layout

Esistono due approcci principali per organizzare il codice sorgente: il **src layout** e il **flat layout**.

**Flat layout** — il pacchetto si trova direttamente nella root del progetto:

```
my-project/
├── my_package/
│   ├── __init__.py
│   └── core.py
├── tests/
└── pyproject.toml
```

**src layout** — il pacchetto si trova dentro la directory `src/`:

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── core.py
├── tests/
└── pyproject.toml
```

| Aspetto | src layout | flat layout |
|---------|------------|-------------|
| Isolamento | Il pacchetto non e importabile dalla root senza installazione | Il pacchetto e importabile direttamente dalla root |
| Test affidabili | I test importano sempre il pacchetto installato | I test potrebbero importare il sorgente locale invece del pacchetto installato |
| Semplicita | Richiede `pip install -e .` per lo sviluppo | Funziona immediatamente senza installazione |
| Adozione | Raccomandato da PyPA, pytest, setuptools | Usato storicamente, ancora comune in progetti piccoli |
| Rischio errori | Minimo: se i test passano, il pacchetto installato funziona | Possibile: i test passano localmente ma il pacchetto installato fallisce |

La raccomandazione moderna e chiara: **usare il src layout**. Il costo iniziale (un livello di directory in piu, necessita di installazione editable) e trascurabile rispetto al beneficio di test che riflettono fedelmente l'esperienza dell'utente finale. Il flat layout resta accettabile per script semplici e prototipi, ma per qualsiasi progetto destinato alla distribuzione il src layout e la scelta corretta.

### File speciali

**`__init__.py`** — marca una directory come pacchetto Python. Puo essere vuoto o contenere codice di inizializzazione, re-export di simboli pubblici e definizione della versione:

```python
# src/my_package/__init__.py
"""My Package — una libreria per l'elaborazione dati."""

from my_package.core import process_data, validate_input
from my_package.utils import format_output

__version__ = "1.2.0"
__all__ = ["process_data", "validate_input", "format_output"]
```

La variabile `__all__` controlla cosa viene esportato con `from my_package import *`. Definirla esplicitamente e una pratica di igiene dell'API pubblica.

**`__main__.py`** — rende il pacchetto eseguibile con `python -m my_package`. E il punto di ingresso naturale per pacchetti che hanno una componente CLI:

```python
# src/my_package/__main__.py
"""Entry point per l'esecuzione diretta: python -m my_package"""

import sys
from my_package.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

**`__version__`** — la versione del pacchetto. Puo essere definita staticamente in `__init__.py`, letta dinamicamente da `pyproject.toml` usando `importlib.metadata`, oppure generata automaticamente da tag git:

```python
# Approccio moderno: leggere la versione dai metadati del pacchetto installato
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("my-package")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
```

Questo approccio e superiore perche la versione viene definita in un solo posto (`pyproject.toml`) ed e sempre sincronizzata con i metadati del pacchetto installato.

---

## pyproject.toml

### Configurazione Completa

Il file `pyproject.toml` e il cuore del progetto moderno. Utilizza il formato TOML (Tom's Obvious Minimal Language), progettato per essere leggibile e non ambiguo. La struttura si divide in sezioni con ruoli distinti.

**`[build-system]`** — dichiara il backend di build e le sue dipendenze. Questa sezione e letta per prima da pip e dal modulo `build`:

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"
```

I principali backend disponibili:

| Backend | requires | build-backend |
|---------|----------|---------------|
| setuptools | `["setuptools>=75.0", "wheel"]` | `"setuptools.build_meta"` |
| hatchling | `["hatchling"]` | `"hatchling.build"` |
| flit-core | `["flit_core>=3.4"]` | `"flit_core.buildapi"` |
| poetry-core | `["poetry-core>=1.0.0"]` | `"poetry.core.masonry.api"` |
| maturin | `["maturin>=1.0"]` | `"maturin"` |

`maturin` e un caso speciale: e il backend per pacchetti Python con estensioni scritte in Rust (usando PyO3). E particolarmente rilevante nel contesto della crescente adozione di Rust nell'ecosistema Python (ruff, uv, pydantic-core sono tutti scritti in Rust).

**`[project]`** — contiene i metadati del progetto secondo PEP 621. Questa e la sezione piu importante:

```toml
[project]
name = "my-awesome-tool"
version = "1.2.0"
description = "Uno strumento per l'elaborazione automatica dei dati"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Mario Rossi", email = "mario.rossi@example.com"},
]
maintainers = [
    {name = "Team Sviluppo", email = "dev@example.com"},
]
keywords = ["data", "processing", "automation"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries",
    "Typing :: Typed",
]
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0,<3.0",
    "rich>=13.0",
    "click>=8.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-asyncio>=0.24",
    "mypy>=1.10",
    "ruff>=0.5",
]
docs = [
    "sphinx>=7.0",
    "sphinx-rtd-theme>=2.0",
    "myst-parser>=3.0",
]

[project.urls]
Homepage = "https://github.com/mrossi/my-awesome-tool"
Documentation = "https://my-awesome-tool.readthedocs.io"
Repository = "https://github.com/mrossi/my-awesome-tool"
Changelog = "https://github.com/mrossi/my-awesome-tool/blob/main/CHANGELOG.md"
Issues = "https://github.com/mrossi/my-awesome-tool/issues"

[project.scripts]
my-tool = "my_awesome_tool.cli:main"
my-tool-admin = "my_awesome_tool.admin:main"

[project.gui-scripts]
my-tool-gui = "my_awesome_tool.gui:launch"
```

Il campo `dependencies` usa la sintassi PEP 508 per gli specifier di versione. Le optional-dependencies definiscono gruppi installabili con `pip install my-awesome-tool[dev]` o `pip install my-awesome-tool[dev,docs]`. Gli `scripts` creano comandi eseguibili nel PATH dell'utente al momento dell'installazione — e il meccanismo standard per distribuire CLI tools.

**`[tool.*]`** — sezioni dedicate alla configurazione degli strumenti di sviluppo. Concentrare tutta la configurazione in `pyproject.toml` evita la proliferazione di file (`pytest.ini`, `mypy.ini`, `.flake8`, ecc.):

```toml
[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
my_awesome_tool = ["data/*.json", "templates/*.html"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-ra -q --strict-markers --cov=my_awesome_tool"
markers = [
    "slow: test che richiedono tempo",
    "integration: test di integrazione",
]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = "tests.*"
allow_untyped_defs = true

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "RUF"]

[tool.ruff.lint.isort]
known-first-party = ["my_awesome_tool"]

[tool.black]
line-length = 100
target-version = ["py312"]
```

### Esempio Completo pyproject.toml

Ecco un `pyproject.toml` completo e realistico per un progetto di medie dimensioni che utilizza setuptools come backend:

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dataflow"
version = "2.1.0"
description = "Pipeline di elaborazione dati configurabile e scalabile"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.11"
authors = [{name = "DataTeam", email = "data@example.com"}]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "pydantic>=2.5",
    "httpx>=0.27",
    "structlog>=24.1",
    "tenacity>=8.2",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0", "mypy>=1.10", "ruff>=0.5"]
postgres = ["asyncpg>=0.29", "psycopg[binary]>=3.1"]
redis = ["redis>=5.0"]
all = ["dataflow[postgres,redis]"]

[project.scripts]
dataflow = "dataflow.cli:app"

[project.urls]
Repository = "https://github.com/datateam/dataflow"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --cov=dataflow --cov-report=term-missing"

[tool.mypy]
python_version = "3.12"
strict = true

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D", "ANN101", "ANN102", "COM812", "ISC001"]
```

---

## Build System

### setuptools

setuptools e il build system piu maturo e ancora il piu utilizzato nell'ecosistema Python. Le versioni moderne (75+) supportano pienamente `pyproject.toml` e il PEP 621, rendendo superflui `setup.py` e `setup.cfg` per la maggior parte dei progetti.

**Configurazione moderna con pyproject.toml:**

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
include = ["my_package*"]
exclude = ["tests*"]

[tool.setuptools.package-data]
my_package = [
    "data/*.json",
    "data/*.yaml",
    "templates/**/*.html",
    "py.typed",
]
```

La direttiva `packages.find` con `where = ["src"]` configura il discovery automatico dei pacchetti all'interno della directory `src/`. Il campo `package-data` specifica file non-Python da includere nel pacchetto — configurazioni, template, dati statici.

**setup.cfg (legacy ma ancora diffuso):**

Molti progetti consolidati usano ancora `setup.cfg` come formato dichiarativo complementare. E un formato INI che precede l'adozione di TOML:

```ini
[metadata]
name = my-package
version = attr: my_package.__version__
description = Una descrizione del pacchetto
long_description = file: README.md
long_description_content_type = text/markdown
license = MIT

[options]
package_dir =
    = src
packages = find:
python_requires = >=3.10
install_requires =
    requests>=2.28
    click>=8.0

[options.packages.find]
where = src

[options.entry_points]
console_scripts =
    my-tool = my_package.cli:main
```

La direttiva `version = attr: my_package.__version__` legge la versione dinamicamente dall'attributo `__version__` del pacchetto. Questo pattern, sebbene ancora funzionante, sta cedendo il passo alla definizione statica in `pyproject.toml` o al versioning dinamico basato su tag git.

**Entry points** sono il meccanismo standard per creare comandi eseguibili. Quando un utente installa il pacchetto con `pip install my-package`, pip crea automaticamente un wrapper script nel PATH che invoca la funzione specificata:

```python
# src/my_package/cli.py
import click

@click.command()
@click.option("--verbose", "-v", is_flag=True)
def main(verbose: bool) -> None:
    """Punto di ingresso del tool."""
    if verbose:
        click.echo("Modalita verbose attivata")
    click.echo("Esecuzione completata")
```

### Hatchling

Hatch e un build system e project manager moderno che ha guadagnato rapidamente adozione. Il suo backend `hatchling` e leggero, veloce e offre funzionalita avanzate come il versioning dinamico e i build hooks.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-tool"
dynamic = ["version"]
# ... altri metadati PEP 621

[tool.hatch.version]
path = "src/my_tool/__about__.py"

[tool.hatch.build.targets.wheel]
packages = ["src/my_tool"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/README.md",
    "/LICENSE",
]
```

Il file `__about__.py` contiene semplicemente `__version__ = "1.0.0"` e hatchling lo legge automaticamente. I build hooks permettono di eseguire codice personalizzato durante il processo di build — utile per generare codice, compilare asset o eseguire trasformazioni:

```toml
[tool.hatch.build.hooks.custom]
path = "build_hooks.py"
```

Hatch offre anche gestione degli ambienti virtuali integrata con il comando `hatch env`:

```bash
# Creare e attivare un ambiente
hatch env create
hatch shell

# Eseguire comandi in un ambiente specifico
hatch run test
hatch run lint:check

# Eseguire su piu versioni Python
hatch run all:test
```

### Poetry

Poetry e il tool piu opinato dell'ecosistema: gestisce dipendenze, ambienti virtuali, build e pubblicazione in un singolo strumento coerente. Utilizza la propria sezione `[tool.poetry]` per la configurazione, sebbene supporti anche il PEP 621.

```bash
# Inizializzare un nuovo progetto
poetry init

# Aggiungere dipendenze
poetry add httpx pydantic
poetry add --group dev pytest mypy ruff

# Installare tutte le dipendenze
poetry install

# Aggiornare le dipendenze
poetry update

# Build del pacchetto
poetry build

# Pubblicare su PyPI
poetry publish
```

La configurazione in `pyproject.toml`:

```toml
[tool.poetry]
name = "my-project"
version = "1.0.0"
description = "Descrizione del progetto"
authors = ["Mario Rossi <mario@example.com>"]
readme = "README.md"
packages = [{include = "my_package", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
httpx = "^0.27"
pydantic = ">=2.0,<3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
mypy = "^1.10"
ruff = ">=0.5"

[tool.poetry.group.docs.dependencies]
sphinx = "^7.0"

[tool.poetry.scripts]
my-tool = "my_package.cli:main"
```

Il file `poetry.lock` e un elemento cruciale: registra le versioni esatte di tutte le dipendenze (dirette e transitive) risolte da Poetry. Questo lock file va committato nel repository per garantire build riproducibili. Quando un collega esegue `poetry install`, ottiene esattamente le stesse versioni — non "la piu recente compatibile", ma la versione specifica registrata nel lock.

I **dependency groups** permettono di organizzare le dipendenze per contesto. Il gruppo `dev` e il piu comune, ma si possono definire gruppi personalizzati (`docs`, `test`, `lint`) e installarli selettivamente:

```bash
# Solo dipendenze di produzione
poetry install --only main

# Produzione + dev
poetry install --with dev

# Tutto tranne docs
poetry install --without docs
```

### Flit

Flit e il build system minimalista per eccellenza. Se il progetto e una libreria Python pura (nessuna estensione C, nessun dato complesso), Flit riduce la configurazione al minimo assoluto:

```toml
[build-system]
requires = ["flit_core>=3.4"]
build-backend = "flit_core.buildapi"

[project]
name = "my-library"
version = "1.0.0"
description = "Una libreria semplice e pulita"
requires-python = ">=3.10"
dependencies = ["httpx>=0.27"]

[project.scripts]
my-lib = "my_library:main"
```

Flit non richiede configurazione aggiuntiva per il discovery dei pacchetti — deduce automaticamente la struttura dal nome del progetto. La pubblicazione su PyPI e altrettanto diretta:

```bash
# Build e pubblicazione in un solo comando
flit publish

# Solo build
flit build

# Installazione in modalita sviluppo
flit install --symlink
```

Flit e ideale per librerie piccole e medie che non necessitano di funzionalita avanzate di build. La sua semplicita e il suo punto di forza: meno configurazione significa meno cose che possono andare storte.

---

## Evoluzione: da setup.py a pyproject.toml

La transizione da `setup.py` a `pyproject.toml` non e stata istantanea. Comprendere l'evoluzione aiuta a mantenere progetti legacy e a capire perche certi pattern esistono.

### L'era setup.py (2000-2018)

Il file `setup.py` era codice Python arbitrario che invocava `setuptools.setup()`:

```python
# setup.py — stile legacy, NON usare per nuovi progetti
from setuptools import setup, find_packages

setup(
    name="my-package",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.28",
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "my-tool=my_package.cli:main",
        ],
    },
    python_requires=">=3.8",
)
```

Problemi fondamentali di `setup.py`:

1. **Esecuzione arbitraria** — `pip install` doveva eseguire `setup.py` per scoprire i metadati. Un `setup.py` malevolo poteva eseguire codice arbitrario sulla macchina dell'utente durante `pip install`.

2. **Bootstrap problem** — `setup.py` poteva importare il pacchetto stesso per leggere `__version__`, ma il pacchetto non era ancora installato durante il build. Questo creava dipendenze circolari.

3. **Nessuna analisi statica** — strumenti come pip, PyPI e IDE non potevano leggere i metadati senza eseguire il file. La risoluzione delle dipendenze richiedeva l'esecuzione di codice Python.

4. **Dipendenze di build non dichiarate** — se `setup.py` importava `numpy` per il build (comune nei pacchetti scientifici), non c'era modo di dichiararlo prima dell'esecuzione.

### La transizione (2018-2021)

Il PEP 518 ha risolto il bootstrap problem introducendo `[build-system]` in `pyproject.toml`. Il PEP 517 ha definito l'interfaccia tra frontend e backend. Ma molti progetti usavano ancora `setup.cfg` per i metadati dichiarativi accanto a un `setup.py` minimale:

```python
# setup.py minimale dell'era di transizione
from setuptools import setup
setup()  # tutti i metadati in setup.cfg
```

```ini
# setup.cfg — metadati dichiarativi
[metadata]
name = my-package
version = attr: my_package.__version__
```

### Lo stato attuale (2021-oggi)

Con il PEP 621 e setuptools 75+, `pyproject.toml` e completamente autosufficiente. La migrazione da `setup.py` a `pyproject.toml` segue questi passi:

```bash
# 1. Generare pyproject.toml da setup.py/setup.cfg esistenti
# Lo strumento ini2toml automatizza la conversione
pip install ini2toml[full]
ini2toml --output-file pyproject.toml setup.cfg

# 2. Verificare la conversione
python -m build
twine check dist/*

# 3. Rimuovere i file legacy
rm setup.py setup.cfg MANIFEST.in  # MANIFEST.in solo se non necessario
```

**Guida alla migrazione dei campi principali:**

| setup.py / setup.cfg | pyproject.toml |
|----------------------|----------------|
| `name = "pkg"` | `[project] name = "pkg"` |
| `version = "1.0"` | `[project] version = "1.0"` |
| `install_requires = [...]` | `[project] dependencies = [...]` |
| `extras_require = {...}` | `[project.optional-dependencies]` |
| `entry_points = {"console_scripts": [...]}` | `[project.scripts]` |
| `python_requires = ">=3.10"` | `[project] requires-python = ">=3.10"` |
| `package_dir = {"": "src"}` | `[tool.setuptools.packages.find] where = ["src"]` |
| `package_data = {...}` | `[tool.setuptools.package-data]` |

---

## Versioning

La scelta di uno schema di versioning e una decisione architetturale che influenza il flusso di lavoro dell'intero team. Lo standard di fatto nell'ecosistema Python (e in gran parte del software open source) e il **Semantic Versioning (SemVer)**.

**Semantic Versioning (SemVer)** — il formato e `MAJOR.MINOR.PATCH`:

- **MAJOR** — incrementato per modifiche incompatibili all'API pubblica. Un utente che aggiorna da 1.x a 2.x deve aspettarsi che il proprio codice possa rompersi.
- **MINOR** — incrementato per nuove funzionalita retrocompatibili. Un utente che aggiorna da 1.1 a 1.2 non dovrebbe avere problemi.
- **PATCH** — incrementato per bugfix retrocompatibili. Nessuna nuova funzionalita, solo correzioni.

Suffissi pre-release seguono la versione base: `1.0.0a1` (alpha), `1.0.0b1` (beta), `1.0.0rc1` (release candidate). Python definisce la propria normalizzazione delle versioni nel PEP 440, che e compatibile con SemVer ma aggiunge regole specifiche:

```
1.0.0           # release stabile
1.0.0a1         # alpha 1
1.0.0b2         # beta 2
1.0.0rc1        # release candidate 1
1.0.0.post1     # post-release (correzione documentazione, rebuild)
1.0.0.dev1      # development release
```

### PEP 440 in dettaglio

Il PEP 440 ("Version Identification and Dependency Specification") definisce il formato canonico delle versioni Python. La comprensione dettagliata di questo PEP e essenziale per chi pubblica pacchetti, perche pip e PyPI rifiutano versioni non conformi.

**Formato canonico:**

```
N[.N]+[{a|b|rc}N][.postN][.devN]
```

**Segmenti della versione:**

| Segmento | Significato | Esempio | Ordine |
|----------|-------------|---------|--------|
| `N.N.N` | Release | `1.2.3` | base |
| `.devN` | Development release | `1.2.3.dev1` | prima di alpha |
| `aN` | Alpha | `1.2.3a1` | prima di beta |
| `bN` | Beta | `1.2.3b1` | prima di rc |
| `rcN` | Release candidate | `1.2.3rc1` | prima di release |
| `.postN` | Post-release | `1.2.3.post1` | dopo release |

**Ordinamento completo:**

```
1.0.0.dev1 < 1.0.0a1 < 1.0.0a2 < 1.0.0b1 < 1.0.0rc1 < 1.0.0 < 1.0.0.post1 < 1.0.1.dev1
```

**Normalizzazione** — il PEP 440 definisce regole di normalizzazione per garantire che forme diverse della stessa versione vengano riconosciute come equivalenti:

```python
# Queste forme sono tutte equivalenti dopo normalizzazione:
"1.0.0"       # forma canonica
"1.0"         # normalizzata in 1.0.0
"1.0.0.0"     # normalizzata in 1.0.0
"v1.0.0"      # il prefisso "v" viene rimosso
"1.0.0-1"     # normalizzata in 1.0.0.post1
"1.0.0_1"     # normalizzata in 1.0.0.post1
```

**Version specifiers (PEP 508):**

```python
# Specifier di versione usati nelle dipendenze
"requests>=2.28"          # compatibile: >= 2.28.0
"requests>=2.28,<3.0"     # intervallo esplicito
"requests~=2.28.0"        # compatibile: >= 2.28.0, < 2.29.0
"requests~=2.28"          # compatibile: >= 2.28, < 3.0
"requests==2.31.0"        # esatta
"requests!=2.30.0"        # esclusione
"requests===2.31.0"       # identita arbitraria (evitare)
```

L'operatore `~=` (compatibile) e particolarmente utile: `~=X.Y` equivale a `>=X.Y, <(X+1).0`, mentre `~=X.Y.Z` equivale a `>=X.Y.Z, <X.(Y+1).0`. Questo riflette esattamente la semantica di SemVer.

**Calendar Versioning (CalVer)** — alcuni progetti usano la data come versione: `2025.1`, `2025.3.15`, `24.1.0`. Questo schema e adatto per progetti dove il concetto di "retrocompatibilita" e meno significativo (distribuzioni, strumenti con release regolari). Esempi noti: Ubuntu (`24.04`), pip (`24.2`), black (`24.8.0`).

**Versioning dinamico da tag git** — l'approccio piu robusto per evitare la duplicazione della versione. Lo strumento `setuptools-scm` legge la versione dal tag git piu recente:

```toml
[build-system]
requires = ["setuptools>=75.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
dynamic = ["version"]

[tool.setuptools_scm]
version_scheme = "guess-next-dev"
local_scheme = "node-and-date"
```

Con questa configurazione, quando si crea un tag `v1.2.0` e si esegue il build, la versione del pacchetto sara automaticamente `1.2.0`. Se ci sono commit dopo il tag, la versione diventa qualcosa come `1.2.1.dev3+g1a2b3c4` — indicando che siamo 3 commit dopo la versione 1.2.0, con hash `1a2b3c4`. Per Hatchling esiste un plugin equivalente: `hatch-vcs`.

**Strumenti di bump automatico:**

```bash
# bump2version (bump-my-version) — aggiorna la versione in piu file
bump-my-version bump minor  # 1.2.0 -> 1.3.0
bump-my-version bump major  # 1.3.0 -> 2.0.0
bump-my-version bump patch  # 2.0.0 -> 2.0.1

# python-semantic-release — analizza i commit message (Conventional Commits)
# e determina automaticamente il tipo di bump
semantic-release version
semantic-release publish
```

`python-semantic-release` e particolarmente potente in contesti CI/CD: analizza i messaggi di commit (formato Conventional Commits: `feat:`, `fix:`, `BREAKING CHANGE:`), determina se servono un bump major, minor o patch, aggiorna la versione, crea il tag git e pubblica su PyPI — tutto automaticamente.

---

## Build e Distribuzione

### Creazione Pacchetto

Il modulo `build` (installabile con `pip install build`) e il frontend standard per la creazione di pacchetti:

```bash
# Build completo: source distribution + wheel
python -m build

# Solo wheel
python -m build --wheel

# Solo source distribution
python -m build --sdist

# Output in una directory specifica
python -m build --outdir packages/

# Con uv (significativamente piu veloce)
uv build
uv build --wheel
uv build --sdist
```

Il comando produce due artefatti nella directory `dist/`:

**Wheel (`.whl`)** — un archivio ZIP rinominato con estensione `.whl`. Contiene il codice Python gia organizzato nella struttura finale, pronto per essere estratto nel `site-packages`. L'installazione di un wheel e rapidissima perche non richiede alcuna fase di build — solo decompressione e copia. Il nome del file segue il formato `{name}-{version}-{python_tag}-{abi_tag}-{platform_tag}.whl`:

```
my_package-1.2.0-py3-none-any.whl        # pacchetto puro Python
numpy-1.26.4-cp312-cp312-linux_x86_64.whl # con estensioni C compilate
```

**Source Distribution (`.tar.gz`)** — un archivio dei sorgenti completi. Richiede una fase di build al momento dell'installazione. E necessario per pacchetti con estensioni C/Rust quando non e disponibile un wheel pre-compilato per la piattaforma dell'utente.

La prassi e pubblicare sempre entrambi. Il wheel garantisce installazione rapida per la maggior parte degli utenti; la source distribution serve come fallback e per scopi di audit del codice.

### Formato Wheel — Internals

Il formato wheel e definito dal PEP 427. Comprendere la struttura interna e utile per il debugging di problemi di packaging e per la creazione di tooling personalizzato.

**Struttura interna di un wheel:**

Un file `.whl` e un archivio ZIP con una struttura precisa. Estraendo `my_package-1.2.0-py3-none-any.whl`:

```
my_package/
├── __init__.py
├── core.py
├── utils.py
├── data/
│   └── config.json
└── py.typed
my_package-1.2.0.dist-info/
├── METADATA
├── WHEEL
├── RECORD
├── entry_points.txt
├── top_level.txt
└── LICENSE
```

**METADATA** — contiene i metadati del pacchetto nel formato definito dal PEP 566/643. E il formato che PyPI legge per visualizzare la pagina del pacchetto:

```
Metadata-Version: 2.1
Name: my-package
Version: 1.2.0
Summary: Una libreria per l'elaborazione dati
Home-page: https://github.com/user/my-package
Author: Mario Rossi
Author-email: mario@example.com
License: MIT
Requires-Python: >=3.10
Classifier: Development Status :: 4 - Beta
Classifier: Programming Language :: Python :: 3
Requires-Dist: httpx>=0.27
Requires-Dist: pydantic>=2.0,<3.0
Provides-Extra: dev
Requires-Dist: pytest>=8.0; extra == "dev"
```

**WHEEL** — metadati specifici del formato wheel:

```
Wheel-Version: 1.0
Generator: setuptools (75.3.0)
Root-Is-Purelib: true
Tag: py3-none-any
```

**RECORD** — manifest SHA256 di ogni file nel wheel, fondamentale per l'integrita dell'installazione:

```
my_package/__init__.py,sha256=abc123...,1024
my_package/core.py,sha256=def456...,5120
my_package-1.2.0.dist-info/METADATA,sha256=ghi789...,2048
my_package-1.2.0.dist-info/RECORD,,
```

Il file RECORD e l'ultima riga del manifest e non include il proprio hash (per ovvie ragioni di circolarita). pip usa RECORD per verificare l'integrita dei file installati e per la disinstallazione pulita del pacchetto.

**Naming convention dei wheel:**

Il nome del file wheel codifica informazioni sulla compatibilita:

```
{distribution}-{version}(-{build_tag})?-{python_tag}-{abi_tag}-{platform_tag}.whl
```

| Tag | Significato | Esempi |
|-----|------------|--------|
| python_tag | Versione Python richiesta | `py3` (qualsiasi 3.x), `cp312` (CPython 3.12) |
| abi_tag | ABI compatibile | `none` (puro Python), `cp312` (estensioni C per CPython 3.12) |
| platform_tag | Piattaforma | `any`, `linux_x86_64`, `macosx_14_0_arm64`, `win_amd64` |

**Tag manylinux:**

Per i wheel con estensioni C su Linux, il tag `manylinux` garantisce compatibilita binaria tra distribuzioni Linux diverse. Il sistema e definito nei PEP 599 (`manylinux2014`) e PEP 600 (`manylinux_2_17`):

```
numpy-1.26.4-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
```

Questo wheel contiene estensioni C compilate per CPython 3.12 su Linux x86_64, compatibili con qualsiasi distribuzione Linux con glibc >= 2.17 (CentOS 7+, Ubuntu 14.04+, Debian 8+).

**Tag macOS universal2:**

Per macOS, il tag `universal2` indica un wheel contenente codice nativo sia per Intel (x86_64) che per Apple Silicon (arm64):

```
cryptography-42.0.0-cp312-cp312-macosx_10_12_universal2.whl
```

**Ispezione di un wheel:**

```bash
# Elencare il contenuto di un wheel
python -m zipfile -l dist/my_package-1.2.0-py3-none-any.whl

# Estrarre un wheel per ispezione
unzip -d wheel_contents dist/my_package-1.2.0-py3-none-any.whl

# Verificare un wheel con check-wheel-contents
pip install check-wheel-contents
check-wheel-contents dist/my_package-1.2.0-py3-none-any.whl

# Mostrare i metadati di un wheel installato
python -c "from importlib.metadata import metadata; print(metadata('my-package'))"
```

### Source Distribution e MANIFEST.in

La source distribution (sdist) e un archivio tar.gz dei file sorgenti del progetto. A differenza del wheel, richiede una fase di build al momento dell'installazione (esecuzione del build backend).

**MANIFEST.in** — controlla quali file vengono inclusi nella sdist. Quando il backend e `setuptools`, i file inclusi di default sono:

- Tutti i file Python nei pacchetti rilevati
- I file specificati in `package-data`
- `pyproject.toml`, `setup.py`, `setup.cfg`
- `README`, `LICENSE`, `CHANGELOG` (con varie estensioni)

Per includere file aggiuntivi o escludere file indesiderati, si usa `MANIFEST.in`:

```
# MANIFEST.in
# Include file aggiuntivi
include LICENSE
include README.md
include CHANGELOG.md
include pyproject.toml

# Include directory ricorsivamente
recursive-include src *.py *.pyi *.typed
recursive-include tests *.py
recursive-include docs *.rst *.py

# Include file di dati
recursive-include src/my_package/data *.json *.yaml

# Escludi pattern
global-exclude *.pyc
global-exclude __pycache__
prune docs/_build
prune .github
```

**Direttive MANIFEST.in:**

| Direttiva | Azione |
|-----------|--------|
| `include file1 file2` | Include file specifici nella root |
| `recursive-include dir pattern` | Include ricorsivamente in una directory |
| `exclude file1 file2` | Escludi file specifici |
| `recursive-exclude dir pattern` | Escludi ricorsivamente |
| `global-include pattern` | Include ovunque |
| `global-exclude pattern` | Escludi ovunque |
| `graft dir` | Include l'intera directory |
| `prune dir` | Escludi l'intera directory |

Con build backend moderni come `hatchling`, il controllo dei file nella sdist avviene tramite `pyproject.toml`:

```toml
[tool.hatch.build.targets.sdist]
include = ["/src", "/tests", "/README.md", "/LICENSE"]
exclude = ["/.github", "/docs/_build"]
```

**Verificare il contenuto della sdist:**

```bash
# Costruire la sdist
python -m build --sdist

# Elencare il contenuto
tar tzf dist/my_package-1.2.0.tar.gz | head -30

# Verificare con check-manifest
pip install check-manifest
check-manifest
```

`check-manifest` confronta il contenuto della sdist con i file nel repository git e segnala file mancanti o extra — uno strumento essenziale per evitare di pubblicare sdist incomplete.

### PyPI

**Python Package Index (PyPI)** e il repository centrale dell'ecosistema Python. Pubblicare su PyPI rende il pacchetto installabile con `pip install nome-pacchetto` da qualsiasi macchina connessa a internet.

**Preparazione:**

1. Creare un account su [pypi.org](https://pypi.org)
2. Generare un API token: Account Settings -> API Tokens -> Add API token
3. Configurare le credenziali locali:

```bash
# File ~/.pypirc
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcm... # il token generato
```

**Pubblicazione con twine:**

```bash
# Installare twine
pip install twine

# Verificare il pacchetto prima della pubblicazione
twine check dist/*

# Caricare su PyPI
twine upload dist/*

# Caricare su TestPyPI (per test)
twine upload --repository testpypi dist/*
```

**TestPyPI** e un'istanza separata di PyPI pensata per il testing. Permette di verificare che il processo di pubblicazione funzioni senza inquinare il repository di produzione. Si crea un account separato su [test.pypi.org](https://test.pypi.org) e si configura in `~/.pypirc`:

```ini
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcm...
```

L'installazione dal TestPyPI richiede un flag esplicito:

```bash
pip install --index-url https://test.pypi.org/simple/ my-package
```

**Trusted Publishers (GitHub Actions OIDC)** — il metodo piu sicuro e moderno per pubblicare su PyPI. Invece di usare API token statici, PyPI verifica l'identita del publisher tramite il protocollo OIDC (OpenID Connect). In pratica, si configura su PyPI quale repository GitHub e quale workflow sono autorizzati a pubblicare, e GitHub Actions ottiene un token temporaneo ad ogni esecuzione:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Nessun token da gestire, nessun segreto da ruotare. La configurazione su PyPI si fa in Publishing -> Add a new publisher, specificando il repository GitHub, il nome del workflow e l'environment.

**Processo di upload — cosa accade internamente:**

1. `twine check dist/*` verifica che i metadati siano validi e che la `long_description` (README) sia renderizzabile.
2. `twine upload` invia i file a PyPI via HTTPS (API legacy) con autenticazione token.
3. PyPI valida il pacchetto: nome disponibile, versione non duplicata, metadati conformi.
4. I file vengono archiviati su CDN (Fastly) e resi disponibili globalmente.
5. L'indice viene aggiornato per riflettere la nuova versione.

### Private Package Index

Per distribuire pacchetti all'interno di un'organizzazione senza pubblicarli su PyPI, esistono diverse soluzioni:

**devpi** — un server PyPI leggero, ideale per team di sviluppo:

```bash
# Installazione e avvio
pip install devpi-server devpi-client
devpi-server --start --init

# Configurazione client
devpi use http://localhost:3141
devpi login root
devpi index -c dev
devpi use root/dev

# Upload di un pacchetto
devpi upload dist/*
```

**AWS CodeArtifact** — servizio gestito di Amazon per repository di pacchetti:

```bash
# Login e configurazione pip
aws codeartifact login --tool pip --repository my-repo \
    --domain my-domain --domain-owner 123456789012

# Dopo il login, pip install funziona normalmente
pip install my-internal-package
```

**Configurazione pip per indice privato:**

```ini
# pip.conf (Linux: ~/.config/pip/pip.conf, macOS: ~/Library/Application Support/pip/pip.conf)
[global]
extra-index-url = https://user:password@pypi.internal.company.com/simple/

# Oppure con variabile d'ambiente
# PIP_EXTRA_INDEX_URL=https://user:password@pypi.internal.company.com/simple/
```

L'opzione `extra-index-url` aggiunge un indice supplementare — pip cerca prima su PyPI, poi sull'indice privato. Per usare esclusivamente l'indice privato, si usa `index-url` al posto di `extra-index-url`.

---

## Entry Points e Console Scripts

Gli entry points sono il meccanismo standard di Python per la registrazione di componenti plug-in e la creazione di comandi eseguibili. Sono definiti dal PEP 621 nella sezione `[project.scripts]` e implementati secondo la specifica del packaging Python.

### Tipi di entry points

**console_scripts** — creano eseguibili da riga di comando:

```toml
[project.scripts]
my-tool = "my_package.cli:main"
my-tool-admin = "my_package.admin:cli"
```

Quando l'utente installa il pacchetto, pip genera wrapper script nella directory `bin/` (Linux/macOS) o `Scripts/` (Windows) dell'ambiente. Lo script generato e simile a:

```python
#!/path/to/python
# -*- coding: utf-8 -*-
import re
import sys
from my_package.cli import main
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
```

**gui_scripts** — identici ai console_scripts ma su Windows non aprono una finestra console:

```toml
[project.gui-scripts]
my-gui = "my_package.gui:launch"
```

**Plugin entry points** — permettono a pacchetti di terze parti di registrare componenti per il vostro framework:

```toml
# Nel pacchetto plugin
[project.entry-points."my_package.plugins"]
csv_handler = "my_plugin_csv:CsvHandler"
json_handler = "my_plugin_json:JsonHandler"
```

```python
# Nel pacchetto principale — discovery dei plugin
from importlib.metadata import entry_points

def load_plugins():
    """Carica tutti i plugin registrati."""
    plugins = {}
    eps = entry_points(group="my_package.plugins")
    for ep in eps:
        plugins[ep.name] = ep.load()
    return plugins
```

### Pattern CLI avanzati

**Click con gruppi di comandi:**

```python
# src/my_package/cli.py
import click

@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """My Tool — utilita per l'elaborazione dati."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default="output.json")
@click.pass_context
def process(ctx: click.Context, input_file: str, output: str) -> None:
    """Elabora un file di input."""
    if ctx.obj["verbose"]:
        click.echo(f"Elaborazione di {input_file}...")
    # ...

@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Mostra lo stato corrente."""
    click.echo("Sistema operativo.")
```

```toml
[project.scripts]
my-tool = "my_package.cli:cli"
```

Questo crea un comando `my-tool` con sottocomandi: `my-tool process file.csv` e `my-tool status`.

---

## Classifiers PyPI

I classifiers sono stringhe strutturate che categorizzano un pacchetto su PyPI. Seguono una tassonomia fissa definita su [pypi.org/classifiers/](https://pypi.org/classifiers/). I classifiers influenzano la ricercabilita del pacchetto su PyPI e forniscono informazioni strutturate agli utenti.

### Tassonomia dei classifiers

I classifiers seguono il formato `Categoria :: Sottocategoria :: Valore` con diverse categorie principali:

**Development Status** — lo stato di maturita del progetto:

```toml
classifiers = [
    # Scegliere UNO di questi
    "Development Status :: 1 - Planning",
    "Development Status :: 2 - Pre-Alpha",
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
    "Development Status :: 5 - Production/Stable",
    "Development Status :: 6 - Mature",
    "Development Status :: 7 - Inactive",
]
```

**Intended Audience** — il pubblico target:

```toml
classifiers = [
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Intended Audience :: System Administrators",
    "Intended Audience :: End Users/Desktop",
]
```

**License** — la licenza del pacchetto:

```toml
classifiers = [
    "License :: OSI Approved :: MIT License",
    "License :: OSI Approved :: Apache Software License",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "License :: OSI Approved :: BSD License",
]
```

**Programming Language** — le versioni Python supportate (dovrebbero corrispondere a `requires-python`):

```toml
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3 :: Only",
]
```

**Topic** — l'area tematica:

```toml
classifiers = [
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Database",
]
```

**Typing** — se il pacchetto fornisce type stubs:

```toml
classifiers = [
    "Typing :: Typed",    # il pacchetto include py.typed e annotazioni
    "Typing :: Stubs Only", # pacchetto di sole type stubs
]
```

**Framework** — framework compatibili:

```toml
classifiers = [
    "Framework :: Django :: 5.0",
    "Framework :: Flask",
    "Framework :: FastAPI",
    "Framework :: Pytest",
]
```

### Set di classifiers raccomandato

Per un pacchetto tipico destinato a sviluppatori Python:

```toml
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Typing :: Typed",
]
```

I classifiers sono facoltativi ma fortemente raccomandati: migliorano la visibilita del pacchetto su PyPI e forniscono informazioni strutturate che tools automatici possono utilizzare.

---

## Namespace Packages

I namespace packages permettono a piu distribuzioni (pacchetti PyPI) di contribuire sotto-pacchetti allo stesso namespace di primo livello. Questo e utile per ecosistemi modulari dove organizzazioni o progetti vogliono un prefisso comune.

### Namespace packages impliciti (PEP 420)

A partire da Python 3.3, i namespace packages sono supportati nativamente senza file `__init__.py` nel pacchetto di primo livello. Questo e il metodo raccomandato:

```
# Distribuzione A: my-org-core
src/
└── my_org/
    └── core/
        ├── __init__.py
        └── engine.py

# Distribuzione B: my-org-utils
src/
└── my_org/
    └── utils/
        ├── __init__.py
        └── helpers.py
```

Nota: `my_org/` NON ha `__init__.py`. Questo permette a Python di trattarlo come namespace package: quando entrambe le distribuzioni sono installate, l'utente puo fare:

```python
from my_org.core import engine
from my_org.utils import helpers
```

**Configurazione pyproject.toml per namespace packages:**

```toml
# my-org-core/pyproject.toml
[project]
name = "my-org-core"
version = "1.0.0"

[tool.setuptools.packages.find]
where = ["src"]
# setuptools rileva automaticamente i namespace packages
```

```toml
# my-org-utils/pyproject.toml
[project]
name = "my-org-utils"
version = "1.0.0"

[tool.setuptools.packages.find]
where = ["src"]
```

### Namespace packages espliciti (legacy)

Il metodo precedente al PEP 420 richiedeva un `__init__.py` speciale in ogni distribuzione:

```python
# my_org/__init__.py — stile legacy pkg_resources
__import__("pkg_resources").declare_namespace(__name__)
```

```python
# my_org/__init__.py — stile legacy pkgutil
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
```

Questi approcci sono deprecati. Per i nuovi progetti, usare esclusivamente i namespace packages impliciti (senza `__init__.py` nel namespace di primo livello).

### Esempi reali

Molti progetti noti usano namespace packages:

- `google-cloud-*` — tutti i pacchetti Google Cloud SDK condividono il namespace `google.cloud`
- `azure-*` — i pacchetti Azure condividono il namespace `azure`
- `zope.*` — i componenti Zope condividono il namespace `zope`

---

## Editable Installs

L'installazione editable (`pip install -e .`) e lo strumento fondamentale per lo sviluppo locale. Permette di modificare il codice sorgente e vedere le modifiche immediatamente senza reinstallare il pacchetto.

### Meccanismo interno

Quando si esegue `pip install -e .`, pip NON copia i file nel `site-packages`. Invece, crea un collegamento che punta alla directory sorgente del progetto. Il meccanismo esatto dipende dal build backend.

**Con setuptools (PEP 660):**

setuptools crea un file `.pth` nella directory `site-packages` che aggiunge la directory sorgente al `sys.path`. Con il src layout:

```
# .venv/lib/python3.12/site-packages/__editable__.my_package-1.0.0.pth
# Contenuto:
/home/user/my-project/src
```

In aggiunta, setuptools genera un finder personalizzato (un `MetaPathFinder`) che gestisce la risoluzione dei moduli. Questo e necessario per supportare correttamente i package data e le risorse.

**Con hatchling:**

Hatchling usa un approccio diverso: genera un import hook nel `site-packages` che redirige le importazioni alla directory sorgente.

### Uso pratico

```bash
# Installazione editable base
pip install -e .

# Con gruppi opzionali
pip install -e ".[dev,test]"

# Con uv (molto piu veloce)
uv pip install -e .
uv pip install -e ".[dev]"

# Con uv sync (il progetto stesso viene installato in editable)
uv sync  # equivalente a pip install -e ".[dev]" se dev e il default group

# Verifica dell'installazione editable
pip show my-package
# Location: /home/user/my-project/src  (punta alla sorgente, non a site-packages)
```

### Limitazioni e considerazioni

1. **File non-Python**: le modifiche ai file di dati (JSON, YAML, template) in `package-data` potrebbero non essere immediatamente visibili. Potrebbe essere necessario reinstallare.

2. **Entry points**: se si aggiungono nuovi `[project.scripts]`, serve una reinstallazione per creare i wrapper script.

3. **Estensioni C**: le modifiche a estensioni C/Cython richiedono ricompilazione (`pip install -e .` ricompila automaticamente).

4. **__pycache__**: i file `.pyc` vengono generati nella directory sorgente, non nel `site-packages`. Aggiungere `__pycache__/` al `.gitignore`.

---

## Distribuzione Eseguibili

Non tutti gli utenti finali hanno Python installato o la capacita di gestire ambienti virtuali. Per applicazioni desktop, tool di sistema e utility destinate a utenti non-sviluppatori, la distribuzione come eseguibile standalone e spesso l'unica opzione praticabile.

### PyInstaller

PyInstaller e lo strumento piu maturo e versatile per creare eseguibili Python. Analizza le importazioni del programma, raccoglie tutte le dipendenze (incluse librerie C condivise) e le impacchetta in un bundle eseguibile.

```bash
# Installazione
pip install pyinstaller

# Creazione eseguibile (directory)
pyinstaller --name my-tool src/my_package/__main__.py

# Creazione eseguibile singolo file
pyinstaller --onefile --name my-tool src/my_package/__main__.py

# Con icona personalizzata
pyinstaller --onefile --name my-tool --icon=icon.ico src/my_package/__main__.py

# Senza console (per applicazioni GUI)
pyinstaller --onefile --windowed --name my-app src/my_package/gui.py
```

**`--onefile`** produce un singolo file eseguibile. All'avvio, l'eseguibile si decomprime in una directory temporanea e poi si esegue. Il vantaggio e la semplicita di distribuzione (un solo file); lo svantaggio e un tempo di avvio piu lungo.

**`--onedir`** (default) produce una directory con l'eseguibile e tutte le dipendenze. L'avvio e istantaneo ma la distribuzione richiede copiare l'intera directory.

**Spec file** — per configurazioni complesse, PyInstaller genera un file `.spec` che puo essere personalizzato:

```python
# my-tool.spec
a = Analysis(
    ['src/my_package/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/my_package/data', 'my_package/data'),
        ('src/my_package/templates', 'my_package/templates'),
    ],
    hiddenimports=[
        'my_package.plugins.csv_handler',
        'my_package.plugins.json_handler',
        'encodings.utf_8',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'unittest'],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,        # includi per --onefile
    a.zipfiles,        # includi per --onefile
    a.datas,           # includi per --onefile
    name='my-tool',
    debug=False,
    strip=True,
    upx=True,
    console=True,
)
```

**Hidden imports** — PyInstaller rileva le importazioni tramite analisi statica. Le importazioni dinamiche (`importlib.import_module()`, `__import__()`) non vengono rilevate automaticamente e vanno dichiarate esplicitamente con `--hidden-import` o nel campo `hiddenimports` dello spec file.

**Data files** — file non-Python (configurazioni, template, immagini) vanno inclusi esplicitamente. Nel codice, il percorso di accesso cambia tra l'esecuzione normale e quella da eseguibile PyInstaller:

```python
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """Restituisce il percorso corretto sia in sviluppo che da eseguibile."""
    if hasattr(sys, '_MEIPASS'):
        # Esecuzione da eseguibile PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # Esecuzione normale
        base_path = Path(__file__).parent
    return base_path / relative_path
```

PyInstaller genera eseguibili specifici per la piattaforma su cui gira. Per creare eseguibili Windows serve una macchina Windows (o una VM), per macOS serve macOS. Non esiste cross-compilation nativa — ma le GitHub Actions con matrix build risolvono elegantemente il problema.

### Nuitka

Nuitka adotta un approccio radicalmente diverso: compila il codice Python in C, poi compila il C in codice macchina nativo. Il risultato e un eseguibile genuinamente compilato, non un interprete Python impacchettato con il bytecode.

```bash
# Installazione
pip install nuitka

# Compilazione standalone (singola directory)
python -m nuitka --standalone --follow-imports \
    --output-dir=build src/my_package/__main__.py

# Compilazione onefile
python -m nuitka --onefile --follow-imports \
    --output-dir=build src/my_package/__main__.py

# Con ottimizzazioni
python -m nuitka --onefile --follow-imports \
    --enable-plugin=anti-bloat \
    --noinclude-pytest-mode=nofollow \
    --noinclude-setuptools-mode=nofollow \
    src/my_package/__main__.py
```

I vantaggi di Nuitka rispetto a PyInstaller includono tempi di avvio piu rapidi (il codice e compilato nativamente), migliore protezione del codice sorgente (non e banale decompilare C compilato) e prestazioni potenzialmente superiori per codice CPU-bound. Lo svantaggio e un tempo di compilazione significativamente piu lungo e la necessita di un compilatore C installato (gcc o MSVC).

### cx_Freeze

cx_Freeze e un'alternativa a PyInstaller con un approccio basato su script di configurazione:

```python
# setup_cx.py
from cx_Freeze import setup, Executable

build_options = {
    "packages": ["my_package"],
    "excludes": ["tkinter", "unittest"],
    "include_files": [
        ("src/my_package/data/", "data/"),
    ],
}

setup(
    name="my-tool",
    version="1.0.0",
    description="Il mio strumento",
    options={"build_exe": build_options},
    executables=[
        Executable(
            "src/my_package/__main__.py",
            target_name="my-tool",
        )
    ],
)
```

```bash
# Build
python setup_cx.py build_exe
```

cx_Freeze non supporta la modalita onefile nativamente, il che lo rende meno adatto per la distribuzione a utenti finali. Resta una buona opzione per ambienti controllati dove l'installazione di una directory e accettabile.

### Briefcase (BeeWare)

Briefcase fa parte del progetto BeeWare e punta alla creazione di applicazioni native multi-piattaforma — non solo eseguibili da riga di comando, ma vere applicazioni con interfaccia grafica che seguono le convenzioni di ciascun sistema operativo.

```bash
# Installazione
pip install briefcase

# Creare un nuovo progetto
briefcase new

# Build per la piattaforma corrente
briefcase build

# Creare un pacchetto distribuibile
briefcase package

# Eseguire in modalita sviluppo
briefcase dev
```

Briefcase genera:
- **macOS**: `.app` bundle e `.dmg` installer
- **Windows**: installer MSI
- **Linux**: AppImage, Flatpak, `.deb`, `.rpm`
- **iOS/Android**: pacchetti nativi (sperimentale)

La configurazione avviene in `pyproject.toml`:

```toml
[tool.briefcase]
project_name = "My Application"
bundle = "com.example.myapp"

[tool.briefcase.app.myapp]
formal_name = "My Application"
description = "Un'applicazione desktop"
sources = ["src/myapp"]
requires = ["httpx>=0.27", "pydantic>=2.0"]

[tool.briefcase.app.myapp.macOS]
requires = ["toga-cocoa>=0.4"]

[tool.briefcase.app.myapp.windows]
requires = ["toga-winforms>=0.4"]

[tool.briefcase.app.myapp.linux]
requires = ["toga-gtk>=0.4"]
```

---

## Distribuzione Interna

In contesti aziendali, la distribuzione di pacchetti Python segue percorsi diversi dalla pubblicazione su PyPI. L'obiettivo e rendere il software disponibile ai colleghi in modo controllato, riproducibile e sicuro.

**Wheel su drive condiviso** — l'approccio piu semplice. Si genera il wheel e si copia su un percorso di rete accessibile al team:

```bash
# Build
python -m build --wheel

# Copia su rete (esempio)
cp dist/my_tool-1.0.0-py3-none-any.whl /mnt/shared/python-packages/

# Installazione da parte del collega
pip install /mnt/shared/python-packages/my_tool-1.0.0-py3-none-any.whl
```

Per un numero ridotto di pacchetti interni con aggiornamenti poco frequenti, questo approccio funziona sorprendentemente bene. Il limite emerge quando i pacchetti crescono di numero e le dipendenze tra di essi diventano complesse.

**pip install da repository git** — pip puo installare direttamente da un URL git, senza bisogno di pubblicare su alcun indice:

```bash
# Da repository pubblico
pip install git+https://github.com/team/my-package.git

# Da branch specifico
pip install git+https://github.com/team/my-package.git@develop

# Da tag specifico
pip install git+https://github.com/team/my-package.git@v1.2.0

# Da commit specifico
pip install git+https://github.com/team/my-package.git@abc123f

# In requirements.txt
my-package @ git+https://github.com/team/my-package.git@v1.2.0
```

Questo approccio e eccellente per team piccoli e dipendenze interne che cambiano frequentemente. Lo svantaggio e che ogni installazione richiede il clone del repository, il che rallenta il processo e richiede accesso git alla macchina di destinazione.

**Server PyPI privato** — per organizzazioni con molti pacchetti interni, un indice privato e la soluzione scalabile. devpi, Artifactory e AWS CodeArtifact (descritti nella sezione precedente) permettono di replicare l'esperienza di PyPI all'interno dell'infrastruttura aziendale.

**Docker images** — per applicazioni server (API, microservizi, worker), Docker e lo standard de facto per la distribuzione. Il Dockerfile per un'applicazione Python segue un pattern consolidato:

```dockerfile
# Fase di build
FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Fase di runtime
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /app/dist/*.whl /tmp/

RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# Utente non-root per sicurezza
RUN useradd --create-home appuser
USER appuser

ENTRYPOINT ["my-tool"]
```

Il multi-stage build separa l'ambiente di compilazione da quello di esecuzione, producendo immagini piu piccole e sicure. Il pacchetto viene costruito come wheel nella prima fase e installato nella seconda, garantendo che l'applicazione nel container sia identica a quella che un utente installerebbe con pip.

Un pattern alternativo utilizza `uv` per installazioni piu veloci nell'immagine Docker:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

ENTRYPOINT ["uv", "run", "my-tool"]
```

---

## pyproject.toml Deep-Dive

La sezione precedente ha introdotto le basi di `pyproject.toml`. Qui approfondiamo ogni aspetto avanzato della specifica, dai campi dinamici alle optional dependencies composte, fino alla nuova gestione delle licenze introdotta dal PEP 639.

### Campi statici e dinamici

Il PEP 621 distingue tra campi **statici** (dichiarati direttamente nel file) e campi **dinamici** (calcolati dal build backend al momento del build). La lista dei campi dinamici va dichiarata esplicitamente nel campo `dynamic`:

```toml
[project]
name = "my-package"
dynamic = ["version", "readme"]
```

Quando un campo e elencato in `dynamic`, il build backend e responsabile di fornirne il valore. Non e possibile dichiarare un campo sia staticamente che in `dynamic` — il builder rifiutera la configurazione.

**Campi che possono essere dinamici:**

| Campo | Statico | Dinamico | Note |
|-------|---------|----------|------|
| `name` | Si | **No** | Sempre statico, obbligatorio |
| `version` | Si | Si | Il caso d'uso principale di `dynamic` |
| `description` | Si | Si | Raramente dinamico |
| `readme` | Si | Si | Utile quando il formato va rilevato |
| `requires-python` | Si | Si | Quasi sempre statico |
| `license` | Si | Si | Tipicamente statico |
| `authors` | Si | Si | Tipicamente statico |
| `maintainers` | Si | Si | Tipicamente statico |
| `keywords` | Si | Si | Tipicamente statico |
| `classifiers` | Si | Si | A volte derivato da `requires-python` |
| `urls` | Si | Si | Tipicamente statico |
| `scripts` | Si | Si | Tipicamente statico |
| `gui-scripts` | Si | Si | Tipicamente statico |
| `entry-points` | Si | Si | Tipicamente statico |
| `dependencies` | Si | Si | A volte derivato da requirements.txt |
| `optional-dependencies` | Si | Si | Tipicamente statico |

In pratica, l'unico campo comunemente dinamico e `version`, gestito da plugin come `setuptools-scm` o `hatch-vcs` che derivano la versione dai tag git.

**Esempio completo con version dinamica (hatchling + hatch-vcs):**

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "analytics-engine"
dynamic = ["version"]
description = "Motore di analisi dati in tempo reale"
readme = {file = "README.md", content-type = "text/markdown"}
requires-python = ">=3.11"
license = {text = "Apache-2.0"}
authors = [
    {name = "DataTeam", email = "data@company.com"},
]
keywords = ["analytics", "streaming", "pipeline"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "src/analytics_engine/_version.py"
```

Con questa configurazione, `hatch-vcs` genera automaticamente il file `_version.py` durante il build, contenente la variabile `__version__` derivata dal tag git piu recente.

**Il campo `readme` — formati supportati:**

Il campo `readme` accetta diverse forme:

```toml
# Stringa semplice — il tipo viene inferito dall'estensione
readme = "README.md"

# Tabella con tipo esplicito
readme = {file = "README.md", content-type = "text/markdown"}

# Testo inline (raro, ma valido)
readme = {text = "Descrizione del pacchetto", content-type = "text/plain"}

# File reStructuredText
readme = {file = "README.rst", content-type = "text/x-rst"}
```

**Il campo `requires-python` — semantica precisa:**

```toml
# Il pacchetto richiede Python 3.11 o superiore
requires-python = ">=3.11"

# Range esplicito — blocca Python 4.x (sconsigliato nella pratica)
requires-python = ">=3.11,<4.0"

# Versione minima con patch
requires-python = ">=3.11.2"
```

pip usa `requires-python` nella risoluzione delle dipendenze: se un pacchetto richiede `>=3.12` e l'utente ha Python 3.11, pip cerchera una versione precedente del pacchetto compatibile con 3.11. Questo e il meccanismo che permette di aggiornare `requires-python` senza rompere gli utenti su versioni vecchie di Python — vedranno semplicemente la versione piu recente compatibile.

### Optional dependencies avanzate

Le optional dependencies (extras) permettono di definire gruppi di dipendenze installabili selettivamente. Il pattern piu avanzato e la composizione di gruppi:

```toml
[project.optional-dependencies]
# Gruppi base
postgres = ["asyncpg>=0.29", "psycopg[binary]>=3.1"]
redis = ["redis[hiredis]>=5.0"]
s3 = ["boto3>=1.34", "s3fs>=2024.1"]
monitoring = ["prometheus-client>=0.20", "opentelemetry-api>=1.24"]

# Gruppi di sviluppo
test = ["pytest>=8.0", "pytest-cov>=5.0", "pytest-asyncio>=0.24", "hypothesis>=6.100"]
lint = ["ruff>=0.5", "mypy>=1.10"]
docs = ["sphinx>=7.0", "sphinx-rtd-theme>=2.0", "myst-parser>=3.0"]
dev = ["my-package[test,lint]"]

# Gruppi composti per deployment
cloud = ["my-package[s3,monitoring]"]
all = ["my-package[postgres,redis,s3,monitoring]"]
```

La notazione `my-package[test,lint]` all'interno di un gruppo e chiamata **self-referencing extra** ed e supportata da PEP 508. Questo permette di comporre gruppi senza duplicare le liste di dipendenze.

**Installazione selettiva:**

```bash
# Solo dipendenze base
pip install my-package

# Con supporto PostgreSQL
pip install my-package[postgres]

# Per lo sviluppo completo
pip install my-package[dev]

# Tutto
pip install my-package[all]

# Multipli espliciti
pip install "my-package[postgres,redis,monitoring]"
```

**Dipendenze condizionali per piattaforma:**

Le dipendenze possono essere condizionate usando environment markers (PEP 508):

```toml
dependencies = [
    "colorama>=0.4; sys_platform == 'win32'",
    "uvloop>=0.19; sys_platform != 'win32'",
    "importlib-metadata>=7.0; python_version < '3.12'",
    "tomli>=2.0; python_version < '3.11'",
]
```

I markers disponibili includono `sys_platform`, `platform_machine`, `python_version`, `implementation_name` e `os_name`. Questi permettono di dichiarare dipendenze che variano per sistema operativo, architettura o versione di Python.

### Licenze secondo PEP 639

Il PEP 639 (accettato nel 2024) modernizza la dichiarazione delle licenze nei pacchetti Python, introducendo il campo `license` con espressioni SPDX e il campo `license-files` per i file di licenza.

**Formato precedente (ancora supportato):**

```toml
[project]
license = {text = "MIT"}
# oppure
license = {file = "LICENSE"}
```

**Formato PEP 639 (raccomandato per nuovi progetti):**

```toml
[project]
license = "MIT"
# oppure per licenze composte (SPDX expression)
license = "MIT OR Apache-2.0"
# oppure
license = "MIT AND BSD-3-Clause"

license-files = ["LICENSE*", "NOTICE"]
```

Le espressioni SPDX permettono di dichiarare licenze composte in modo standard e machine-readable. L'identificatore `MIT OR Apache-2.0` indica dual-licensing, mentre `MIT AND BSD-3-Clause` indica che entrambe le licenze si applicano contemporaneamente.

---

## Confronto Build Backends

### setuptools vs hatchling vs flit vs maturin vs pdm-backend

La scelta del build backend influenza la velocita di build, le funzionalita disponibili e l'estensibilita del processo di packaging. Ogni backend ha punti di forza e casi d'uso ideali.

| Aspetto | setuptools | hatchling | flit-core | maturin | pdm-backend |
|---------|-----------|-----------|-----------|---------|-------------|
| **Maturita** | 20+ anni | 3+ anni | 8+ anni | 5+ anni | 3+ anni |
| **Velocita build** | Media | Veloce | Molto veloce | Dipende da Rust | Veloce |
| **Config zero** | No | Quasi | Si | Quasi | Quasi |
| **Estensioni C** | Si | Via hooks | No | No (solo Rust) | No |
| **Estensioni Rust** | Via setuptools-rust | Via hooks | No | Si (nativo) | No |
| **Build hooks** | Limitati | Si (potenti) | No | Si | Limitati |
| **Versioning VCS** | setuptools-scm | hatch-vcs | No | Cargo.toml | pdm-backend |
| **Editable installs** | PEP 660 | PEP 660 | PEP 660 | PEP 660 | PEP 660 |
| **PEP 621** | Si (v75+) | Si | Si | Si | Si |
| **Dimensione wheel** | Media | Piccola | Piccola | Dipende | Piccola |
| **Plugin system** | Limitato | Esteso | No | No | Limitato |

**Quando scegliere cosa:**

- **setuptools** — progetti legacy, estensioni C native, massima compatibilita con l'ecosistema esistente. E la scelta sicura quando non si sa cosa scegliere.
- **hatchling** — progetti moderni che necessitano di build hooks, versioning VCS, gestione granulare dei file inclusi. Ideale per librerie di medie dimensioni.
- **flit-core** — librerie pure-Python semplici dove la velocita di build e la semplicita di configurazione sono prioritarie. Configurazione quasi zero.
- **maturin** — pacchetti con estensioni Rust (PyO3). L'unica scelta sensata per l'integrazione Python-Rust.
- **pdm-backend** — alternativa a hatchling, parte dell'ecosistema PDM. Buon supporto per il PEP 621.

### uv_build — il nuovo backend di Astral

Dal 2025, Astral (i creatori di uv e ruff) hanno introdotto `uv_build`, un build backend scritto in Rust progettato per integrarsi nativamente con `uv`:

```toml
[build-system]
requires = ["uv_build>=0.6"]
build-backend = "uv_build"

[project]
name = "my-fast-package"
version = "1.0.0"
dependencies = ["httpx>=0.27"]
```

`uv_build` e progettato per il caso d'uso piu comune: pacchetti pure-Python con configurazione minima. La velocita di build e significativamente superiore a setuptools grazie all'implementazione in Rust. Per pacchetti con estensioni C o Rust, o con esigenze di build hooks avanzati, hatchling o maturin restano le scelte migliori.

**Confronto tempi di build tipici (progetto medio pure-Python):**

| Backend | Build wheel | Build sdist | Build wheel+sdist |
|---------|------------|------------|-------------------|
| setuptools | ~2.5s | ~1.8s | ~4.0s |
| hatchling | ~0.8s | ~0.6s | ~1.2s |
| flit-core | ~0.5s | ~0.4s | ~0.8s |
| uv_build | ~0.2s | ~0.15s | ~0.3s |

I tempi sono indicativi e variano in base alla dimensione del progetto e all'hardware. Il vantaggio di `uv_build` e particolarmente evidente in pipeline CI/CD dove il build viene ripetuto frequentemente.

---

## uv come Package Manager

`uv` e il package manager e project manager Python scritto in Rust da Astral. In meno di due anni dalla sua introduzione, e diventato lo strumento di riferimento per la gestione di progetti Python moderni, grazie alla velocita estrema (10-100x rispetto a pip) e all'approccio unificato che sostituisce pip, pip-tools, virtualenv, pyenv e parzialmente poetry/hatch.

### Workspace e monorepo

I workspace di uv sono ispirati a quelli di Cargo (Rust) e permettono di gestire piu pacchetti correlati in un singolo repository con un unico lockfile e un unico ambiente virtuale.

**Struttura di un workspace uv:**

```
my-workspace/
├── pyproject.toml          # root workspace
├── uv.lock                 # lockfile condiviso
├── packages/
│   ├── core/
│   │   ├── pyproject.toml  # membro: my-org-core
│   │   └── src/
│   │       └── my_org/core/
│   ├── api/
│   │   ├── pyproject.toml  # membro: my-org-api
│   │   └── src/
│   │       └── my_org/api/
│   └── cli/
│       ├── pyproject.toml  # membro: my-org-cli
│       └── src/
│           └── my_org/cli/
└── .python-version
```

**Configurazione del workspace root:**

```toml
# pyproject.toml (root)
[project]
name = "my-workspace"
version = "0.0.0"
requires-python = ">=3.11"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.5",
    "mypy>=1.10",
]

[tool.uv.workspace]
members = ["packages/*"]
```

**Configurazione di un membro del workspace:**

```toml
# packages/api/pyproject.toml
[project]
name = "my-org-api"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "my-org-core",      # dipendenza locale dal workspace
    "fastapi>=0.115",
    "uvicorn>=0.32",
]

[tool.uv.sources]
my-org-core = {workspace = true}
```

La direttiva `{workspace = true}` in `[tool.uv.sources]` dice a uv di risolvere la dipendenza `my-org-core` dal workspace locale invece che da PyPI. Questo e fondamentale per lo sviluppo locale: le modifiche a `core` sono immediatamente visibili in `api` senza pubblicazione.

**Comandi workspace:**

```bash
# Sincronizzare l'intero workspace
uv sync

# Eseguire un comando in un membro specifico
uv run --package my-org-api pytest

# Build di un singolo membro
uv build --package my-org-api

# Aggiungere una dipendenza a un membro
uv add --package my-org-api redis

# Lock dell'intero workspace
uv lock
```

### Lockfile universale

Il file `uv.lock` e un lockfile cross-platform che registra le versioni esatte di tutte le dipendenze, incluse quelle transitive. A differenza di `requirements.txt` (che e platform-specific), `uv.lock` registra le risoluzioni per tutte le piattaforme supportate:

```bash
# Generare il lockfile
uv lock

# Aggiornare una dipendenza specifica
uv lock --upgrade-package httpx

# Aggiornare tutte le dipendenze
uv lock --upgrade

# Sincronizzare l'ambiente con il lockfile (senza modificarlo)
uv sync --frozen

# Verificare che il lockfile sia aggiornato
uv lock --check
```

Il lockfile va committato nel repository. Quando un collega clona il progetto e esegue `uv sync`, ottiene esattamente le stesse versioni, indipendentemente dal sistema operativo. Il formato del lockfile e TOML leggibile e include hash per ogni pacchetto, garantendo integrita e riproducibilita.

**Confronto lockfile:**

| Aspetto | uv.lock | poetry.lock | pip-tools (requirements.txt) |
|---------|---------|-------------|------------------------------|
| Cross-platform | Si | Si | No |
| Hash integrita | Si | Si | Opzionale (`--generate-hashes`) |
| Formato | TOML | TOML | Plain text |
| Velocita risoluzione | ~0.5s | ~5-30s | ~3-15s |
| Workspace support | Si | No | No |

### Script runner con dipendenze inline

uv supporta l'esecuzione di script Python con dipendenze dichiarate inline, secondo il PEP 723 ("Inline script metadata"):

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
#     "rich>=13.0",
# ]
# ///

import httpx
from rich.console import Console

console = Console()

def main():
    response = httpx.get("https://api.github.com/zen")
    console.print(f"[bold green]{response.text}[/bold green]")

if __name__ == "__main__":
    main()
```

```bash
# Eseguire lo script — uv installa le dipendenze automaticamente
uv run script.py

# Oppure, se lo shebang e configurato:
chmod +x script.py
./script.py
```

uv crea automaticamente un ambiente isolato con le dipendenze dichiarate, esegue lo script e pulisce. Questo e particolarmente utile per script di automazione, tool one-off e prototipi che non meritano un intero progetto con `pyproject.toml`.

---

## Strategie di Versioning Avanzate

### SemVer vs CalVer in pratica

La scelta tra Semantic Versioning e Calendar Versioning dipende dalla natura del progetto e dal rapporto con gli utenti.

**Quando SemVer e la scelta giusta:**

- **Librerie con API pubblica** — gli utenti dipendono dalla stabilita dell'interfaccia. Un bump major comunica "aspettati breaking changes".
- **SDK e client** — i consumatori devono sapere se aggiornare richiede modifiche al codice.
- **Progetti con backward compatibility promise** — la versione e un contratto semantico.

**Quando CalVer e preferibile:**

- **Applicazioni end-user** — l'utente finale non si preoccupa della retrocompatibilita dell'API.
- **Progetti con rilasci regolari** — la data nella versione comunica la freschezza.
- **Distribuzioni e tool con policy di supporto temporale** — Ubuntu 24.04 comunica chiaramente "rilasciato ad aprile 2024".

**Schemi CalVer comuni:**

```
YYYY.MM.DD    → 2026.05.24        # versione giornaliera
YYYY.MM       → 2026.5            # versione mensile
YYYY.MINOR    → 2026.1, 2026.2    # progressivo annuale
YY.MINOR      → 26.1, 26.2       # anno abbreviato
```

Progetti Python noti che usano CalVer: `pip` (24.2), `black` (24.8.0), `virtualenv` (20.26.3), `twisted` (24.7.0), `ubuntu` (24.04).

**Schema ibrido:**

Alcuni progetti combinano CalVer e SemVer. Ad esempio, `black` usa `YY.M.PATCH` dove l'anno e il mese danno il contesto temporale, ma il patch number permette hotfix senza attendere il mese successivo.

### setuptools-scm in dettaglio

`setuptools-scm` e il plugin standard per derivare la versione del pacchetto dai tag git. Supporta sia setuptools che hatchling (tramite `hatch-vcs`).

**Configurazione completa:**

```toml
[build-system]
requires = ["setuptools>=75.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-library"
dynamic = ["version"]

[tool.setuptools_scm]
# Come calcolare la prossima versione dev
version_scheme = "guess-next-dev"

# Come formattare la parte locale della versione
local_scheme = "node-and-date"

# Prefisso dei tag (default: "v")
tag_regex = "^(?P<prefix>v)?(?P<version>[vV]?\\d+(?:\\.\\d+)*(?:[._-]?\\w+)*)$"

# File dove scrivere la versione (opzionale)
write_to = "src/my_library/_version.py"

# Template per il file generato
write_to_template = "__version__ = \"{version}\"\n"

# Fallback se non ci sono tag
fallback_version = "0.0.0"
```

**Version schemes disponibili:**

| Schema | Comportamento | Esempio (tag v1.2.0, 3 commit dopo) |
|--------|--------------|--------------------------------------|
| `guess-next-dev` | Incrementa patch e aggiunge `.devN` | `1.2.1.dev3` |
| `no-guess-dev` | Mantiene la versione del tag con `.devN` | `1.2.0.dev3` |
| `post-release` | Aggiunge `.postN` | `1.2.0.post3` |
| `calver-by-date` | Usa la data corrente | `2026.5.24.dev3` |
| `python-simplified-semver` | Simile a guess-next-dev | `1.2.1.dev3` |

**Local schemes disponibili:**

| Schema | Formato locale | Esempio |
|--------|---------------|---------|
| `node-and-date` | `+g<hash>.d<date>` | `1.2.1.dev3+g1a2b3c4.d20260524` |
| `node-and-timestamp` | `+g<hash>.d<timestamp>` | `1.2.1.dev3+g1a2b3c4.d20260524143022` |
| `dirty-tag` | `.dirty` se ci sono modifiche non committate | `1.2.1.dev3+g1a2b3c4.dirty` |
| `no-local-version` | Nessuna parte locale | `1.2.1.dev3` |

Per la pubblicazione su PyPI, si deve usare `no-local-version` perche PyPI non accetta versioni con parti locali (`+...`).

### bump-my-version e automazione

`bump-my-version` (successore di `bump2version`) e uno strumento per incrementare la versione in modo coordinato attraverso piu file del progetto:

```toml
# pyproject.toml
[tool.bumpversion]
current_version = "1.2.0"
commit = true
tag = true
tag_name = "v{new_version}"
tag_message = "Release v{new_version}"
message = "release: v{new_version}"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'

[[tool.bumpversion.files]]
filename = "src/my_package/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'

[[tool.bumpversion.files]]
filename = "CHANGELOG.md"
search = "## [Unreleased]"
replace = "## [Unreleased]\n\n## [{new_version}] - {now:%Y-%m-%d}"
```

```bash
# Bump patch: 1.2.0 -> 1.2.1
bump-my-version bump patch

# Bump minor: 1.2.1 -> 1.3.0
bump-my-version bump minor

# Bump major: 1.3.0 -> 2.0.0
bump-my-version bump major

# Bump pre-release: 1.0.0 -> 1.0.0a1
bump-my-version bump pre_l

# Dry run (mostra cosa cambierebbe senza applicare)
bump-my-version bump minor --dry-run --verbose
```

Il vantaggio di `bump-my-version` rispetto a `setuptools-scm` e che aggiorna la versione in piu file contemporaneamente, crea il commit e il tag in un'unica operazione. Lo svantaggio e che la versione va gestita manualmente (o semi-automaticamente con CI), mentre `setuptools-scm` la deriva interamente dai tag git.

---

## Estensioni C e Binarie

Il packaging di estensioni compilate — codice C, C++ o Rust integrato in pacchetti Python — richiede configurazioni specifiche e tool dedicati per garantire la portabilita su piattaforme diverse.

### Cython build moderno

Cython compila codice Python (o un superset tipizzato) in estensioni C native. La configurazione moderna usa `pyproject.toml` con setuptools come backend:

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel", "Cython>=3.0"]
build-backend = "setuptools.build_meta"

[project]
name = "fast-math"
version = "1.0.0"
requires-python = ">=3.11"

[tool.setuptools]
ext-modules = [
    {name = "fast_math._core", sources = ["src/fast_math/_core.pyx"]},
]
```

Per configurazioni piu complesse, un `setup.py` minimale resta necessario per definire le estensioni con opzioni di compilazione avanzate:

```python
# setup.py — solo per estensioni Cython complesse
from setuptools import setup
from Cython.Build import cythonize
import numpy as np

setup(
    ext_modules=cythonize(
        "src/fast_math/_core.pyx",
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "language_level": "3",
        },
    ),
    include_dirs=[np.get_include()],
)
```

**File `.pyx` esempio:**

```cython
# src/fast_math/_core.pyx
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

import numpy as np
cimport numpy as cnp

def fast_dot_product(cnp.ndarray[double, ndim=1] a,
                     cnp.ndarray[double, ndim=1] b):
    """Prodotto scalare ottimizzato con Cython."""
    cdef int n = a.shape[0]
    cdef double result = 0.0
    cdef int i
    for i in range(n):
        result += a[i] * b[i]
    return result
```

Cython 3.0+ supporta il free-threaded mode di Python 3.13+ tramite la direttiva `freethreading_compatible`, permettendo parallelismo reale senza GIL.

### CFFI per interfacce C

CFFI (C Foreign Function Interface) permette di chiamare funzioni C da Python senza scrivere codice C wrapper. E particolarmente utile quando si vuole interfacciare una libreria C esistente:

```python
# build_ffi.py — script di build per CFFI
from cffi import FFI

ffi = FFI()

# Dichiarazione delle funzioni C
ffi.cdef("""
    double fast_sum(double *data, int length);
    int compress(const char *input, int input_len,
                 char *output, int output_len);
""")

# Codice sorgente C
ffi.set_source("my_package._cffi_bindings", """
    #include <stdlib.h>

    double fast_sum(double *data, int length) {
        double sum = 0.0;
        for (int i = 0; i < length; i++) {
            sum += data[i];
        }
        return sum;
    }

    int compress(const char *input, int input_len,
                 char *output, int output_len) {
        // implementazione compressione...
        return 0;
    }
""")

if __name__ == "__main__":
    ffi.compile(verbose=True)
```

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel", "cffi>=1.17"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
cffi-modules = ["build_ffi.py:ffi"]
```

CFFI supporta sia CPython che PyPy, rendendolo la scelta preferita quando la compatibilita con piu interpreti Python e un requisito.

### Maturin e PyO3 per Rust

Maturin e il build backend standard per pacchetti Python con estensioni Rust tramite PyO3. L'integrazione Python-Rust e diventata il nuovo standard per le estensioni ad alte prestazioni, grazie alla sicurezza della memoria garantita da Rust e alle prestazioni comparabili al C.

```toml
# pyproject.toml
[build-system]
requires = ["maturin>=1.7"]
build-backend = "maturin"

[project]
name = "fast-processor"
version = "1.0.0"
requires-python = ">=3.11"
classifiers = [
    "Programming Language :: Rust",
    "Programming Language :: Python :: Implementation :: CPython",
]

[tool.maturin]
features = ["pyo3/extension-module"]
python-source = "python"
module-name = "fast_processor._core"
```

```rust
// src/lib.rs
use pyo3::prelude::*;

#[pyfunction]
fn process_data(data: Vec<f64>) -> PyResult<f64> {
    let sum: f64 = data.iter().sum();
    Ok(sum / data.len() as f64)
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process_data, m)?)?;
    Ok(())
}
```

```bash
# Build in modalita sviluppo
maturin develop

# Build wheel per distribuzione
maturin build --release

# Pubblicazione diretta su PyPI
maturin publish
```

Maturin genera automaticamente wheel per tutte le piattaforme supportate, gestendo la cross-compilation e i tag manylinux senza configurazione aggiuntiva.

### cibuildwheel per CI

`cibuildwheel` e lo strumento standard per costruire wheel binari multi-piattaforma in CI/CD. Genera wheel per CPython e PyPy su Linux (manylinux e musllinux), macOS e Windows:

```toml
# pyproject.toml
[tool.cibuildwheel]
# Versioni Python da testare
build = "cp311-* cp312-* cp313-*"
skip = "*-win32 *-manylinux_i686"

# Test dopo ogni build
test-requires = "pytest"
test-command = "pytest {project}/tests"

[tool.cibuildwheel.linux]
# Utilizzare manylinux2014 per massima compatibilita
manylinux-x86_64-image = "manylinux2014"
manylinux-aarch64-image = "manylinux2014"

# Costruire anche per musllinux (Alpine)
musllinux-x86_64-image = "musllinux_1_2"

[tool.cibuildwheel.macos]
# Supporto Apple Silicon e Intel
archs = ["x86_64", "arm64", "universal2"]

[tool.cibuildwheel.windows]
archs = ["AMD64"]
```

```yaml
# .github/workflows/wheels.yml
name: Build wheels

on:
  release:
    types: [published]

jobs:
  build_wheels:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: pypa/cibuildwheel@v2.22
      - uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}
          path: wheelhouse/*.whl
```

`cibuildwheel` automatizza la creazione di decine di wheel (combinazioni di versione Python, sistema operativo e architettura) in un singolo workflow CI. Utilizza container Docker con immagini manylinux preconfigurate su Linux, e macchine native per macOS e Windows.

---

## Wheels e sdist — Internals Avanzati

### Platform tags in dettaglio

I platform tags codificano nel nome del file wheel le informazioni di compatibilita. Il sistema e definito dai PEP 425 e PEP 427, con estensioni nei PEP 599, 600 e 656.

**Anatomia completa di un tag:**

```
{python_tag}-{abi_tag}-{platform_tag}
```

**Python tags:**

| Tag | Significato |
|-----|------------|
| `py3` | Qualsiasi Python 3.x (pure Python) |
| `py2.py3` | Python 2 e 3 (legacy) |
| `cp312` | CPython 3.12 specifico |
| `cp313` | CPython 3.13 specifico |
| `pp310` | PyPy 3.10 |

**ABI tags:**

| Tag | Significato |
|-----|------------|
| `none` | Nessun requisito ABI (pure Python) |
| `cp312` | ABI CPython 3.12 stabile |
| `abi3` | ABI stabile limitata (compatibile con versioni future) |

L'ABI stabile limitata (`abi3`) e particolarmente interessante: un wheel compilato con `abi3` e `cp311` funziona su CPython 3.11, 3.12, 3.13 e tutte le versioni future, senza ricompilazione. Per abilitarla:

```python
# setup.py
from setuptools import Extension

ext = Extension(
    "my_package._core",
    sources=["src/my_package/_core.c"],
    py_limited_api=True,
    define_macros=[("Py_LIMITED_API", "0x030B0000")],  # 3.11+
)
```

### manylinux e musllinux

**Evoluzione dei tag manylinux:**

| PEP | Tag | glibc minima | Distribuzione base | Status |
|-----|-----|--------------|--------------------|--------|
| 513 | `manylinux1` | 2.5 | CentOS 5 | Deprecato |
| 571 | `manylinux2010` | 2.12 | CentOS 6 | Deprecato |
| 599 | `manylinux2014` | 2.17 | CentOS 7 | Attivo |
| 600 | `manylinux_2_28` | 2.28 | AlmaLinux 8 | Attivo |
| 600 | `manylinux_2_31` | 2.31 | Debian 11 | Attivo |
| 600 | `manylinux_2_35` | 2.35 | Ubuntu 22.04 | Attivo |

Il PEP 600 ha introdotto il formato aperto `manylinux_X_Y` dove X e Y sono la major e minor version di glibc. Questo elimina la necessita di nuovi PEP per ogni nuova baseline.

**musllinux** (PEP 656) e l'equivalente per distribuzioni basate su musl libc (Alpine Linux, Void Linux):

```
my_package-1.0.0-cp312-cp312-musllinux_1_2_x86_64.whl
```

Il tag `musllinux_1_2` indica compatibilita con musl libc 1.2+. Musl mantiene backward compatibility, quindi un wheel compilato con musl 1.1 funziona anche con musl 1.2, ma il contrario non e garantito.

**auditwheel** — lo strumento per verificare e riparare la compatibilita manylinux di un wheel Linux:

```bash
# Verificare la compatibilita
auditwheel show dist/my_package-1.0.0-cp312-cp312-linux_x86_64.whl

# Riparare (bundle delle librerie condivise, applica tag manylinux)
auditwheel repair dist/my_package-1.0.0-cp312-cp312-linux_x86_64.whl \
    --plat manylinux_2_28_x86_64 \
    --wheel-dir dist/

# delocate e l'equivalente per macOS
delocate-wheel -w dist/ dist/my_package-1.0.0-cp312-cp312-macosx_14_0_arm64.whl
```

`auditwheel repair` analizza le dipendenze da librerie condivise (.so), le copia dentro il wheel e aggiorna i path di linking. Il risultato e un wheel self-contained che non dipende da librerie di sistema (tranne glibc e poche altre nella whitelist manylinux).

### Packaging per piattaforme multiple

Per pubblicare un pacchetto che supporti tutte le piattaforme maggiori, la matrice di build tipica e:

| Piattaforma | Architettura | Tag wheel |
|-------------|-------------|-----------|
| Linux glibc | x86_64 | `manylinux_2_28_x86_64` |
| Linux glibc | aarch64 | `manylinux_2_28_aarch64` |
| Linux musl | x86_64 | `musllinux_1_2_x86_64` |
| Linux musl | aarch64 | `musllinux_1_2_aarch64` |
| macOS | x86_64 | `macosx_10_12_x86_64` |
| macOS | arm64 | `macosx_11_0_arm64` |
| macOS | universal2 | `macosx_10_12_universal2` |
| Windows | AMD64 | `win_amd64` |

Per pacchetti pure-Python, un singolo wheel `py3-none-any` copre tutte le piattaforme. Per pacchetti con estensioni compilate, servono wheel separati per ogni combinazione, e `cibuildwheel` e lo strumento standard per automatizzare questa matrice.

---

## Private PyPI Avanzato

### devpi in produzione

`devpi` e un server PyPI leggero e potente, ideale per team di sviluppo e organizzazioni di medie dimensioni. Supporta il mirroring di PyPI, indici multipli per utente e staging di release.

```bash
# Installazione server
pip install devpi-server devpi-web

# Inizializzazione e avvio
devpi-server --init --serverdir /var/devpi
devpi-server --serverdir /var/devpi --host 0.0.0.0 --port 3141

# Configurazione client
pip install devpi-client
devpi use http://devpi.internal:3141
devpi login root --password ''
devpi index -c dev bases=root/pypi
devpi use root/dev

# Upload pacchetti
devpi upload dist/*

# Configurazione pip per usare devpi
pip install --index-url http://devpi.internal:3141/root/dev/+simple/ my-package
```

**Staging workflow con devpi:**

devpi supporta indici multipli con ereditarieta. Un flusso comune:

```bash
# Creare indici per ambienti diversi
devpi index -c staging bases=root/pypi
devpi index -c production bases=root/pypi

# Pubblicare in staging
devpi use root/staging
devpi upload dist/*

# Dopo il testing, promuovere a production
devpi push my-package==1.2.0 root/production
```

### JFrog Artifactory

JFrog Artifactory e la soluzione enterprise per la gestione di repository di pacchetti. Supporta PyPI come uno dei molti formati (npm, Maven, Docker, ecc.) ed e la scelta standard per grandi organizzazioni.

```bash
# Configurazione pip per Artifactory
pip install --index-url https://artifactory.company.com/api/pypi/pypi-virtual/simple/ \
    --trusted-host artifactory.company.com \
    my-internal-package

# Upload con twine
twine upload --repository-url https://artifactory.company.com/api/pypi/pypi-local/ \
    --username $ARTIFACTORY_USER \
    --password $ARTIFACTORY_TOKEN \
    dist/*
```

**Configurazione permanente:**

```ini
# ~/.pip/pip.conf
[global]
index-url = https://artifactory.company.com/api/pypi/pypi-virtual/simple/
trusted-host = artifactory.company.com

# ~/.pypirc
[distutils]
index-servers = artifactory

[artifactory]
repository = https://artifactory.company.com/api/pypi/pypi-local/
username = deploy-bot
password = <token>
```

Artifactory supporta il virtual repository pattern: un singolo endpoint che cerca prima nel repository locale (pacchetti interni), poi proxya le richieste a PyPI per i pacchetti pubblici. Questo semplifica la configurazione lato client.

### AWS CodeArtifact avanzato

AWS CodeArtifact e il servizio gestito di Amazon per repository di pacchetti, integrato nativamente con IAM per l'autenticazione:

```bash
# Login con profilo AWS — genera token temporaneo (12 ore)
aws codeartifact login --tool pip \
    --domain my-org \
    --domain-owner 123456789012 \
    --repository internal-packages \
    --region eu-west-1

# Il comando configura automaticamente pip per usare CodeArtifact
# Equivalente manuale:
export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain my-org \
    --domain-owner 123456789012 \
    --query authorizationToken \
    --output text)

pip install \
    --index-url "https://aws:${CODEARTIFACT_AUTH_TOKEN}@my-org-123456789012.d.codeartifact.eu-west-1.amazonaws.com/pypi/internal-packages/simple/" \
    my-internal-package

# Upload pacchetti
twine upload \
    --repository-url "https://aws:${CODEARTIFACT_AUTH_TOKEN}@my-org-123456789012.d.codeartifact.eu-west-1.amazonaws.com/pypi/internal-packages/" \
    dist/*
```

CodeArtifact supporta l'upstream repository: quando un pacchetto non e trovato nel repository locale, la richiesta viene proxied a PyPI. I pacchetti scaricati da PyPI vengono cached localmente, riducendo la dipendenza dalla disponibilita di PyPI e accelerando le installazioni successive.

---

## Pubblicazione Automatica e Sicurezza

### Trusted Publishers in dettaglio

I Trusted Publishers eliminano la necessita di gestire token API statici per la pubblicazione su PyPI. Il meccanismo si basa su OIDC (OpenID Connect) e supporta diversi provider CI/CD.

**Provider supportati (al 2026):**

| Provider | Status | Note |
|----------|--------|------|
| GitHub Actions | Stabile | Il piu usato, supporto completo |
| GitLab CI/CD | Stabile | gitlab.com e self-hosted (beta) |
| Google Cloud Build | Stabile | Integrazione con GCP |
| ActiveState | Stabile | Per progetti ActiveState |

**Configurazione su PyPI:**

1. Accedere a [pypi.org](https://pypi.org) → Your Projects → Manage → Publishing
2. Aggiungere un nuovo publisher specificando:
   - Repository owner/name (es. `myorg/my-package`)
   - Workflow filename (es. `publish.yml`)
   - Environment name (es. `pypi`)

**Pending publishers** — e possibile configurare il trusted publisher prima ancora di pubblicare la prima versione. PyPI crea un "pending publisher" che verra attivato alla prima pubblicazione dal workflow autorizzato.

**Workflow completo con GitHub Actions:**

```yaml
name: Release to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write   # Necessario per OIDC
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi   # Deve corrispondere alla config su PyPI
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun token da configurare — OIDC gestisce tutto
```

Il job di build e quello di publish sono separati deliberatamente: il build non necessita di permessi OIDC, riducendo la superficie di attacco. Solo il job di publish, protetto dall'environment `pypi`, puo ottenere il token temporaneo.

### Sigstore e firma dei pacchetti

PyPI supporta la firma dei pacchetti con Sigstore, un sistema di firma crittografica keyless sviluppato dalla Linux Foundation. A differenza di GPG (che richiede la gestione di chiavi private), Sigstore genera firme effimere basate sull'identita OIDC del publisher.

```bash
# Firmare un pacchetto con sigstore
pip install sigstore
sigstore sign dist/my_package-1.0.0-py3-none-any.whl

# Verifica della firma
sigstore verify identity \
    --cert-identity "https://github.com/myorg/my-package/.github/workflows/publish.yml@refs/tags/v1.0.0" \
    --cert-oidc-issuer "https://token.actions.githubusercontent.com" \
    dist/my_package-1.0.0-py3-none-any.whl
```

La firma Sigstore attesta che il pacchetto e stato costruito da uno specifico workflow CI, in un momento specifico, dal repository specificato. Questo crea una catena di fiducia verificabile dall'utente finale senza richiedere la distribuzione di chiavi pubbliche.

### OIDC internals

Il flusso OIDC per i Trusted Publishers funziona cosi:

```
1. GitHub Actions genera un OIDC token (JWT) con claims:
   - repository: "myorg/my-package"
   - workflow: "publish.yml"
   - ref: "refs/tags/v1.0.0"
   - environment: "pypi"

2. Il workflow invia il JWT a PyPI:
   POST https://pypi.org/_/oidc/mint-token
   Authorization: Bearer <jwt>

3. PyPI verifica il JWT:
   - Firma valida (chiave pubblica di GitHub)
   - Claims corrispondono a un trusted publisher configurato
   - Token non scaduto

4. PyPI emette un API token temporaneo (15 minuti):
   {"token": "pypi-AgEIcHlwaS5vcm...", "expires": "..."}

5. Il workflow usa il token temporaneo per l'upload:
   twine upload --password <temp-token> dist/*
```

Il token temporaneo ha validita di 15 minuti e permissione limitata al solo progetto configurato. Non puo essere riutilizzato, non puo essere rubato per pubblicare su altri progetti, e scade automaticamente. Questo e significativamente piu sicuro dei token API statici che non scadono e possono essere usati per qualsiasi progetto dell'account.

---

## Monorepo Packaging

### Struttura monorepo Python

Un monorepo Python contiene piu pacchetti correlati in un singolo repository. Questo approccio e comune per organizzazioni con librerie interne interdipendenti, microservizi che condividono codice, o ecosistemi di plugin.

```
my-org-monorepo/
├── pyproject.toml              # workspace root
├── uv.lock                     # lockfile condiviso
├── .python-version             # versione Python del workspace
├── packages/
│   ├── core/
│   │   ├── pyproject.toml      # my-org-core
│   │   ├── src/
│   │   │   └── my_org/
│   │   │       └── core/
│   │   │           ├── __init__.py
│   │   │           ├── models.py
│   │   │           └── utils.py
│   │   └── tests/
│   ├── auth/
│   │   ├── pyproject.toml      # my-org-auth
│   │   ├── src/
│   │   │   └── my_org/
│   │   │       └── auth/
│   │   │           ├── __init__.py
│   │   │           ├── jwt.py
│   │   │           └── oauth.py
│   │   └── tests/
│   ├── api/
│   │   ├── pyproject.toml      # my-org-api
│   │   └── src/
│   │       └── my_org/
│   │           └── api/
│   └── cli/
│       ├── pyproject.toml      # my-org-cli
│       └── src/
│           └── my_org/
│               └── cli/
├── tools/
│   └── scripts/
│       └── release.py
└── docs/
```

**Vantaggi del monorepo:**

- **Visibilita completa** — tutte le modifiche in un singolo PR, review atomiche.
- **Refactoring cross-package** — rinominare un'interfaccia in `core` e aggiornare tutti i consumer in un singolo commit.
- **CI unificata** — una sola pipeline che testa tutti i pacchetti insieme, rilevando incompatibilita prima della pubblicazione.
- **Dipendenze condivise** — un singolo lockfile garantisce che tutti i pacchetti usino le stesse versioni delle dipendenze esterne.

**Svantaggi:**

- **Complessita CI** — serve logica per determinare quali pacchetti ricostruire quando cambia un file.
- **Release coordination** — pubblicare versioni indipendenti richiede tooling specifico.
- **Dimensione repository** — il clone iniziale e piu lento per nuovi contributori.

### uv workspace in pratica

La configurazione dettagliata di un workspace uv per il monorepo sopra descritto:

```toml
# pyproject.toml (root)
[project]
name = "my-org-workspace"
version = "0.0.0"
requires-python = ">=3.11"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "mypy>=1.10",
]

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/experimental-*"]
```

```toml
# packages/auth/pyproject.toml
[project]
name = "my-org-auth"
version = "2.1.0"
requires-python = ">=3.11"
dependencies = [
    "my-org-core>=1.0",
    "pyjwt>=2.8",
    "cryptography>=42.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_org"]

[tool.uv.sources]
my-org-core = {workspace = true}
```

**Comandi quotidiani del workflow monorepo:**

```bash
# Sincronizzare tutte le dipendenze del workspace
uv sync

# Eseguire i test di un singolo pacchetto
uv run --package my-org-auth pytest

# Eseguire i test di tutti i pacchetti
uv run pytest

# Linting su tutto il workspace
uv run ruff check packages/

# Type checking di un pacchetto
uv run --package my-org-api mypy src/

# Build di un pacchetto per la pubblicazione
uv build --package my-org-core

# Aggiungere una dipendenza a un pacchetto
uv add --package my-org-api redis>=5.0
```

### Release coordination

La pubblicazione di pacchetti da un monorepo richiede coordinazione per garantire che le versioni siano compatibili e che le dipendenze interne siano soddisfatte.

**Strategia 1 — Versioning indipendente:**

Ogni pacchetto ha la propria versione. Le dipendenze interne usano specifier di versione espliciti:

```toml
# packages/api/pyproject.toml
dependencies = ["my-org-core>=1.5,<2.0"]
```

Questa strategia e adatta quando i pacchetti hanno cicli di release diversi e clienti diversi. Richiede disciplina nel mantenere la retrocompatibilita delle interfacce interne.

**Strategia 2 — Versioning sincronizzato:**

Tutti i pacchetti condividono la stessa versione. Un bump di versione si applica a tutti contemporaneamente. Semplifica la comunicazione ("tutto alla versione 3.2.0") ma forza release di pacchetti che non sono cambiati.

**Automazione con python-semantic-release in monorepo:**

```toml
# pyproject.toml (root)
[tool.semantic_release]
version_variables = [
    "packages/core/pyproject.toml:version",
    "packages/auth/pyproject.toml:version",
    "packages/api/pyproject.toml:version",
]
branch = "main"
commit_message = "release: v{version}"
```

Un workflow CI tipico per un monorepo:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  id-token: write
  contents: read

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.changes.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: changes
        run: |
          # Determinare quali pacchetti sono cambiati rispetto all'ultimo tag
          CHANGED=$(git diff --name-only HEAD~1 HEAD | grep '^packages/' | cut -d/ -f2 | sort -u | jq -R -s -c 'split("\n")[:-1]')
          echo "packages=$CHANGED" >> $GITHUB_OUTPUT

  build-and-publish:
    needs: detect-changes
    runs-on: ubuntu-latest
    environment: pypi
    strategy:
      matrix:
        package: ${{ fromJson(needs.detect-changes.outputs.packages) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build packages/${{ matrix.package }}
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: packages/${{ matrix.package }}/dist/
```

Questo workflow pubblica automaticamente solo i pacchetti che sono cambiati, evitando pubblicazioni inutili e riducendo il rischio di errori.

---

## Best Practices

**1. Usare sempre pyproject.toml come punto unico di configurazione.** Ogni nuovo progetto dovrebbe avere `pyproject.toml` come unico file di configurazione. Non creare `setup.py`, `setup.cfg`, `pytest.ini`, `mypy.ini`, `.flake8` — tutti questi strumenti supportano la configurazione in `pyproject.toml`. Un singolo file riduce la confusione, semplifica la manutenzione e rende il progetto immediatamente comprensibile a chi lo apre per la prima volta.

**2. Adottare il src layout per qualsiasi progetto destinato alla distribuzione.** Il src layout garantisce che i test importino sempre il pacchetto installato, non i sorgenti locali. Questo elimina un'intera classe di bug dove i test passano in locale ma il pacchetto installato fallisce. Il costo iniziale — un `pip install -e .` in piu — e irrisorio rispetto al beneficio.

**3. Definire la versione in un solo posto.** La duplicazione della versione tra `pyproject.toml`, `__init__.py`, `CHANGELOG.md` e `Dockerfile` e una fonte inesauribile di errori. Usare `setuptools-scm`, `hatch-vcs` o `importlib.metadata` per derivare la versione da un'unica fonte di verita (il tag git o il campo in `pyproject.toml`).

**4. Specificare sempre i limiti inferiori delle dipendenze e, quando necessario, quelli superiori.** Scrivere `httpx>=0.27` e un contratto: il pacchetto funziona con httpx 0.27 e successive. Per dipendenze con storia di breaking changes, aggiungere un limite superiore: `pydantic>=2.0,<3.0`. Non usare mai versioni esatte (`==`) nelle dipendenze di una libreria — questo crea conflitti irrisolvibili quando piu pacchetti dipendono dalla stessa libreria con versioni esatte diverse.

**5. Testare il pacchetto installato, non i sorgenti.** Prima di pubblicare, installare il pacchetto in un ambiente virtuale pulito e verificare che funzioni. Questo test rivela problemi che non emergono durante lo sviluppo: file dati mancanti, importazioni relative errate, dipendenze non dichiarate. Un semplice script in CI che fa `pip install dist/*.whl && python -c "import my_package"` previene molti errori.

**6. Usare TestPyPI prima di pubblicare su PyPI.** Ogni prima pubblicazione (e ogni modifica significativa al packaging) dovrebbe passare da TestPyPI. Un pacchetto pubblicato su PyPI non puo essere rimosso e ripubblicato con la stessa versione — se si scopre un errore dopo la pubblicazione, serve un bump di versione. TestPyPI permette di iterare senza conseguenze.

**7. Configurare Trusted Publishers per la pubblicazione automatica.** L'uso di token API statici per la pubblicazione su PyPI e un rischio di sicurezza: i token possono essere rubati, trapelare nei log, scadere senza preavviso. Trusted Publishers con GitHub Actions OIDC elimina completamente la gestione dei segreti — la pubblicazione avviene solo dal workflow autorizzato, con credenziali temporanee generate al volo.

**8. Includere il file `py.typed` per pacchetti con type hints.** Se il pacchetto contiene type annotations, aggiungere un file vuoto `py.typed` nella root del pacchetto e includerlo in `package-data`. Questo file segnala a mypy e ad altri type checker che il pacchetto fornisce le proprie annotazioni di tipo, abilitando il type checking per gli utenti della libreria. Senza `py.typed`, mypy ignora le annotazioni del pacchetto installato.

**9. Generare sia wheel che source distribution per ogni release.** Il wheel garantisce installazione rapida per la maggior parte degli utenti. La source distribution serve come fallback, per audit di sicurezza e per piattaforme per cui non esiste un wheel pre-compilato. Il comando `python -m build` genera entrambi di default — non c'e motivo per non farlo.

**10. Automatizzare l'intero ciclo di release con CI/CD.** Il processo ideale: un tag git attiva una pipeline che esegue i test su piu versioni Python e sistemi operativi, costruisce il pacchetto, verifica con `twine check`, pubblica su PyPI tramite Trusted Publishers e crea una GitHub Release con note generate automaticamente. Nessun passaggio manuale, nessuna possibilita di errore umano. Strumenti come `python-semantic-release` possono automatizzare anche la scelta della versione basandosi sui messaggi di commit.

---

## Esercizi

### Esercizio 1 — Creare un pacchetto da zero

Creare un pacchetto Python chiamato `textutils` con la seguente struttura:
- src layout
- `pyproject.toml` con setuptools come backend
- Funzioni: `slugify(text: str) -> str`, `word_count(text: str) -> int`, `truncate(text: str, max_len: int) -> str`
- Console script `textutils` che accetta un sottocomando `slugify` e un sottocomando `count`
- Gruppo opzionale `[dev]` con pytest e ruff
- File `py.typed`
- Versione gestita con `importlib.metadata`

Verificare: `pip install -e ".[dev]" && pytest && textutils slugify "Hello World"` deve funzionare.

### Esercizio 2 — Migrare un progetto legacy

Dato un progetto con `setup.py` e `requirements.txt`, migrare a `pyproject.toml`:
1. Convertire tutti i metadati in `[project]`
2. Convertire `install_requires` in `dependencies`
3. Convertire `extras_require` in `[project.optional-dependencies]`
4. Rimuovere `setup.py`, `setup.cfg`, `MANIFEST.in`
5. Verificare con `python -m build && twine check dist/*`
6. Confrontare il contenuto del wheel generato con il vecchio

### Esercizio 3 — Namespace package

Creare due pacchetti separati che condividono un namespace:
- `acme-core` con `acme.core.engine`
- `acme-utils` con `acme.utils.helpers`
- Nessun `__init__.py` in `acme/`
- Verificare che entrambi siano importabili dopo installazione simultanea

### Esercizio 4 — Pipeline di pubblicazione

Configurare una pipeline GitHub Actions completa:
1. Matrix testing su Python 3.11, 3.12, 3.13
2. Linting con ruff, type checking con mypy
3. Build wheel + sdist
4. Verifica con `twine check`
5. Pubblicazione su TestPyPI con Trusted Publishers (tag-triggered)
6. Creazione automatica della GitHub Release

### Esercizio 5 — Eseguibile standalone

Prendere il pacchetto dell'esercizio 1 e creare:
1. Un eseguibile PyInstaller onefile per la piattaforma corrente
2. Un eseguibile Nuitka standalone
3. Confrontare: dimensione file, tempo di avvio, tempo di build
4. Gestire correttamente i data file con `get_resource_path()`

### Esercizio 6 — Wheel inspection

Dato un wheel di un pacchetto noto (es. `httpx`):
1. Scaricarlo senza installarlo: `pip download httpx --no-deps`
2. Estrarre e ispezionare METADATA, WHEEL, RECORD
3. Verificare gli hash in RECORD manualmente con `sha256sum`
4. Identificare le dipendenze dal file METADATA

### Esercizio 7 — Versioning automatico

Configurare `setuptools-scm` in un progetto:
1. Creare un tag `v1.0.0`
2. Fare un commit dopo il tag
3. Verificare che la versione generata sia `1.0.1.dev1+g<hash>`
4. Fare un altro tag `v1.1.0` e verificare che la versione sia `1.1.0`
5. Usare `importlib.metadata.version()` nel codice per leggere la versione a runtime

---

## Letture

- [Python Packaging User Guide](https://packaging.python.org/) — documentazione ufficiale PyPA, la fonte primaria
- [PEP 517 — Build system interface](https://peps.python.org/pep-0517/) — l'interfaccia tra frontend e backend di build
- [PEP 518 — Build system requirements](https://peps.python.org/pep-0518/) — la tabella `[build-system]` in pyproject.toml
- [PEP 621 — Project metadata](https://peps.python.org/pep-0621/) — la tabella `[project]` standardizzata
- [PEP 427 — The Wheel Binary Package Format](https://peps.python.org/pep-0427/) — specifica del formato wheel
- [PEP 440 — Version Identification](https://peps.python.org/pep-0440/) — formato e ordinamento delle versioni Python
- [PEP 660 — Editable installs](https://peps.python.org/pep-0660/) — specifica delle installazioni editable con PEP 517
- [PEP 420 — Implicit namespace packages](https://peps.python.org/pep-0420/) — namespace packages senza `__init__.py`
- [setuptools documentation](https://setuptools.pypa.io/en/latest/) — documentazione ufficiale setuptools
- [Hatch documentation](https://hatch.pypa.io/) — documentazione ufficiale Hatch/Hatchling
- [uv documentation](https://docs.astral.sh/uv/) — documentazione ufficiale uv
- [twine documentation](https://twine.readthedocs.io/) — strumento per la pubblicazione su PyPI
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/) — guida OIDC per PyPI
- [cibuildwheel documentation](https://cibuildwheel.pypa.io/) — strumento per build wheel multi-piattaforma in CI
- [maturin user guide](https://www.maturin.rs/) — build backend per estensioni Rust (PyO3)
- [PEP 639 — License metadata](https://peps.python.org/pep-0639/) — licenze SPDX in pyproject.toml
- [PEP 723 — Inline script metadata](https://peps.python.org/pep-0723/) — metadati inline per script Python
- [PEP 600 — Future manylinux platform tags](https://peps.python.org/pep-0600/) — tag manylinux_x_y
- [PEP 656 — musllinux platform tags](https://peps.python.org/pep-0656/) — tag per distribuzioni basate su musl
- [Sigstore documentation](https://docs.sigstore.dev/) — firma crittografica keyless per pacchetti
- [devpi documentation](https://devpi.net/) — server PyPI leggero per team di sviluppo
- [setuptools-scm documentation](https://setuptools-scm.readthedocs.io/) — versioning automatico da tag git

---

## Moduli Correlati

- **Modulo 24 — Virtual Environments**: gestione ambienti e dipendenze, complemento naturale al packaging
- **Modulo 27 — CI/CD per Python**: automazione build, test e pubblicazione su PyPI
- **Modulo 26 — Docker per Python**: containerizzazione di applicazioni Python, multi-stage build
- **Modulo 25 — Performance**: Cython, mypyc e estensioni C richiedono configurazione di build specifica
- **Modulo 22 — Testing**: pytest e la configurazione `[tool.pytest.ini_options]` in pyproject.toml

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Backend di build** | Libreria Python che implementa l'interfaccia PEP 517 per costruire wheel e sdist (es. setuptools, hatchling, flit) |
| **CalVer** | Calendar Versioning — schema di versioning basato sulla data (es. `2025.1`) |
| **Classifier** | Stringa strutturata che categorizza un pacchetto su PyPI secondo una tassonomia fissa |
| **Console script** | Comando eseguibile generato da pip a partire da un entry point `[project.scripts]` |
| **Editable install** | Installazione in modalita sviluppo (`pip install -e .`) che crea un collegamento ai sorgenti |
| **Entry point** | Meccanismo di registrazione di componenti plug-in e comandi eseguibili nel packaging Python |
| **Frontend di build** | Strumento che invoca il backend di build (es. `pip`, `build`, `uv build`) |
| **Lock file** | File che registra le versioni esatte di tutte le dipendenze risolte (es. `poetry.lock`, `uv.lock`) |
| **MANIFEST.in** | File che controlla quali file sono inclusi nella source distribution (sdist) |
| **manylinux** | Tag di compatibilita binaria per wheel Linux, definito da PEP 599/600 |
| **Namespace package** | Pacchetto che permette a distribuzioni separate di contribuire sotto-pacchetti allo stesso namespace |
| **OIDC** | OpenID Connect — protocollo di autenticazione usato dai Trusted Publishers di PyPI |
| **PEP 440** | Specifica del formato e dell'ordinamento delle versioni Python |
| **PEP 517** | Interfaccia standard tra frontend e backend di build |
| **PEP 518** | Dichiarazione delle dipendenze di build in `pyproject.toml` |
| **PEP 621** | Formato standardizzato per i metadati del progetto in `[project]` |
| **py.typed** | File marker che indica a mypy che il pacchetto fornisce le proprie annotazioni di tipo |
| **PyPI** | Python Package Index — il repository centrale dei pacchetti Python |
| **RECORD** | File manifest nel wheel che elenca tutti i file con i relativi hash SHA256 |
| **sdist** | Source Distribution — archivio tar.gz dei sorgenti che richiede build al momento dell'installazione |
| **SemVer** | Semantic Versioning — schema MAJOR.MINOR.PATCH con regole di retrocompatibilita |
| **src layout** | Struttura progetto con il pacchetto in `src/`, raccomandata per isolamento e test affidabili |
| **TestPyPI** | Istanza separata di PyPI per il testing della pubblicazione |
| **Trusted Publisher** | Meccanismo OIDC di PyPI che elimina la necessita di token API statici |
| **abi3** | ABI stabile limitata di CPython che permette a un wheel compilato di funzionare su piu versioni Python future senza ricompilazione |
| **auditwheel** | Strumento che verifica e ripara la compatibilita manylinux di un wheel Linux, bundlando le librerie condivise necessarie |
| **bump-my-version** | Strumento per incrementare la versione in modo coordinato in piu file del progetto, successore di bump2version |
| **CalVer** | Calendar Versioning — schema di versioning basato sulla data (es. `2025.1`) |
| **CFFI** | C Foreign Function Interface — libreria per chiamare funzioni C da Python senza scrivere codice C wrapper |
| **cibuildwheel** | Strumento per costruire wheel binari multi-piattaforma (manylinux, musllinux, macOS, Windows) in pipeline CI/CD |
| **Cython** | Compilatore statico che traduce codice Python (o un superset tipizzato) in estensioni C native per prestazioni superiori |
| **delocate** | Equivalente macOS di auditwheel, bundle le librerie dinamiche dentro un wheel per renderlo self-contained |
| **dynamic (campo)** | Campo di `[project]` in pyproject.toml il cui valore e calcolato dal build backend al momento del build, anziche dichiarato staticamente |
| **Environment marker** | Espressione PEP 508 che condiziona una dipendenza a runtime/piattaforma (es. `sys_platform == 'win32'`) |
| **maturin** | Build backend specializzato per pacchetti Python con estensioni Rust tramite PyO3 |
| **monorepo** | Repository singolo che contiene piu pacchetti correlati, gestiti con workspace e lockfile condiviso |
| **musllinux** | Tag di compatibilita binaria per wheel Linux su distribuzioni basate su musl libc (es. Alpine), definito dal PEP 656 |
| **PEP 639** | Specifica per la dichiarazione delle licenze con espressioni SPDX in pyproject.toml |
| **PEP 723** | Specifica per metadati inline negli script Python, usata da uv per dipendenze di script standalone |
| **PyO3** | Libreria Rust per scrivere estensioni Python native, usata con maturin come build backend |
| **Self-referencing extra** | Pattern PEP 508 dove un gruppo di optional dependencies referenzia altri gruppi dello stesso pacchetto (es. `my-pkg[test,lint]`) |
| **Sigstore** | Sistema di firma crittografica keyless della Linux Foundation per attestare la provenienza dei pacchetti |
| **SPDX** | Standard per identificatori di licenza machine-readable, usato dal PEP 639 per la dichiarazione delle licenze |
| **uv_build** | Build backend scritto in Rust da Astral, progettato per pacchetti pure-Python con velocita estrema e configurazione minima |
| **uv workspace** | Meccanismo di uv per gestire piu pacchetti Python in un monorepo con lockfile condiviso, ispirato ai workspace Cargo |
| **Wheel** | Formato di distribuzione binario (`.whl`), archivio ZIP con layout standardizzato (PEP 427) |
