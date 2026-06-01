---
corso: "Programmazione Python"
fase: "6 — DevOps e Distribuzione"
modulo: "32"
titolo: "Packaging Avanzato"
versione: "setuptools 75+ / hatchling 1.x / maturin 1.x / uv 0.7+"
livello: "Avanzato"
prerequisiti:
  - "23 — Packaging e Distribuzione"
  - "24 — Virtual Environments"
  - "27 — CI/CD"
obiettivi:
  - "Comprendere build backend interni: setuptools, hatchling, flit, maturin"
  - "Costruire wheel platform-specific con estensioni C/Rust"
  - "Gestire monorepo Python con uv workspace"
  - "Configurare build matrix multi-piattaforma nella CI"
  - "Pubblicare pacchetti con Trusted Publishers e attestazioni"
  - "Implementare plugin e extensibility pattern per pacchetti"
tag: [packaging-avanzato, wheel, build-backend, maturin, monorepo, uv-workspace, estensioni-native]
---

# Packaging Avanzato — Build Backend, Wheel Platform, uv, Monorepo, Estensioni Native

> **Modulo 32** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Packaging e Distribuzione](23-packaging-distribuzione.md), [Virtual Environments](24-virtual-environments.md), [CI/CD](27-ci-cd-per-python.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere build backend interni: setuptools, hatchling, flit, maturin
> 2. Costruire wheel platform-specific con estensioni C/Rust
> 3. Gestire monorepo Python con uv workspace
> 4. Configurare build matrix multi-piattaforma nella CI
> 5. Pubblicare pacchetti con Trusted Publishers e attestazioni
> 6. Implementare plugin e extensibility pattern per pacchetti
>
> **Tempo stimato:** 6-8 ore · **Livello:** Avanzato
> Questo modulo presuppone familiarita con `pyproject.toml`, la struttura progetto src layout,
> i concetti base di wheel/sdist e la pubblicazione su PyPI. Qui si approfondiscono gli aspetti
> avanzati: build backend a confronto, wheel platform-specific, estensioni native, monorepo,
> namespace packages, sistemi a plugin, risoluzione dipendenze, uv, Conda e troubleshooting.

---

## Idee guida

1. **`pyproject.toml` e il centro di gravita** — PEP 517/518/621/660 definiscono un ecosistema
   dichiarativo, portabile e interoperabile tra build backend diversi.
2. **I wheel platform-specific (manylinux, musllinux, macOS universal2) richiedono toolchain dedicati**
   — cibuildwheel automatizza la compilazione cross-platform in CI.
3. **uv sostituisce pip + pip-tools + virtualenv** — resolver deterministico, lockfile nativo,
   workspace monorepo, ordini di grandezza piu veloce.
4. **Le estensioni native (C, C++, Rust) ampliano Python** — Cython, pybind11, cffi, maturin/PyO3
   coprono casi d'uso diversi con trade-off distinti.
5. **La pubblicazione sicura usa OIDC (Trusted Publishers)** — nessun token statico, nessun segreto
   da ruotare, audit trail completo.

---

## Indice

1. [Ecosistema PEP moderno](#ecosistema-pep-moderno)
2. [Build backend a confronto](#build-backend-a-confronto)
3. [pyproject.toml — approfondimento](#pyprojecttoml--approfondimento)
4. [Source distribution vs wheel](#source-distribution-vs-wheel)
5. [Wheel platform-specific e manylinux](#wheel-platform-specific-e-manylinux)
6. [PEP 660 — editable install standard](#pep-660--editable-install-standard)
7. [Pubblicazione su PyPI e release automation](#pubblicazione-su-pypi-e-release-automation)
8. [Supply chain security — Sigstore e attestazioni digitali](#supply-chain-security--sigstore-e-attestazioni-digitali)
9. [Registri privati](#registri-privati)
10. [Monorepo packaging](#monorepo-packaging)
11. [Namespace packages](#namespace-packages)
12. [Entry points e sistemi a plugin](#entry-points-e-sistemi-a-plugin)
13. [Optional dependencies e extras](#optional-dependencies-e-extras)
14. [Estensioni C e C++](#estensioni-c-e-c)
15. [Estensioni Rust con maturin e PyO3](#estensioni-rust-con-maturin-e-pyo3)
16. [Gestione versione avanzata](#gestione-versione-avanzata)
17. [uv — installer e resolver moderno](#uv--installer-e-resolver-moderno)
18. [Risoluzione dipendenze](#risoluzione-dipendenze)
19. [Distribuzione containerizzata](#distribuzione-containerizzata)
20. [Distribuzione binaria](#distribuzione-binaria)
21. [Conda packaging](#conda-packaging)
22. [Troubleshooting](#troubleshooting)
23. [FAQ](#faq)
24. [Step-by-step — pubblicare il primo pacchetto su PyPI](#step-by-step--pubblicare-il-primo-pacchetto-su-pypi)
25. [Glossario](#glossario)
26. [Letture consigliate](#letture-consigliate)

---

## Ecosistema PEP moderno

Il packaging Python moderno poggia su una serie di PEP interconnessi. Il Modulo 23 introduce
PEP 517, 518 e 621; qui completiamo il quadro con i PEP che definiscono l'architettura avanzata.

### PEP 517 — interfaccia build backend

PEP 517 definisce l'interfaccia minima che un build backend deve esporre. Un frontend (pip, build,
uv) invoca queste funzioni in un ambiente isolato:

```python
# Interfaccia obbligatoria
def build_wheel(wheel_directory, config_settings=None, metadata_directory=None) -> str: ...
def build_sdist(sdist_directory, config_settings=None) -> str: ...

# Interfaccia opzionale (per build incrementali)
def get_requires_for_build_wheel(config_settings=None) -> list[str]: ...
def get_requires_for_build_sdist(config_settings=None) -> list[str]: ...
def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None) -> str: ...
```

Il punto chiave e che **qualsiasi** modulo Python che espone queste funzioni puo fungere da backend.
Questo ha permesso la nascita di hatchling, flit-core, maturin e altri backend specializzati senza
modificare pip o il modulo `build`.

### PEP 518 — dichiarazione dipendenze di build

PEP 518 risolve il "bootstrap problem": come fa pip a sapere quali strumenti servono per costruire
un pacchetto prima ancora di costruirlo? La risposta e la tabella `[build-system]` in
`pyproject.toml`, letta **prima** di qualsiasi altra operazione:

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel", "cython>=3.0"]
build-backend = "setuptools.build_meta"
```

Pip crea un ambiente virtuale temporaneo, installa le dipendenze dichiarate in `requires`, poi
invoca il backend dichiarato in `build-backend`. Questo garantisce isolamento: le dipendenze di
build del progetto A non interferiscono con quelle del progetto B.

Il campo opzionale `backend-path` permette di usare un backend locale (non pubblicato su PyPI):

```toml
[build-system]
requires = []
build-backend = "my_build_backend"
backend-path = ["build_support"]
```

### PEP 621 — metadati progetto standard

PEP 621 standardizza la tabella `[project]`, rendendo i metadati portabili tra backend diversi.
Prima di PEP 621, ogni backend aveva la propria sintassi: Poetry usava `[tool.poetry]`, Flit
usava `[tool.flit.metadata]`, setuptools usava `setup.cfg` o `setup.py`. Ora tutti leggono
`[project]`.

Campi chiave non coperti nel Modulo 23:

```toml
[project]
name = "my-package"
dynamic = ["version"]          # campi calcolati a build-time dal backend

# Licenza con identificatore SPDX (PEP 639, adottato da PyPI 2024+)
license = "MIT"
# Oppure in formato legacy:
# license = {text = "MIT"}
# license = {file = "LICENSE"}

# Specifier Python con vincoli precisi
requires-python = ">=3.11,<4"

# Dipendenze con marker di piattaforma
dependencies = [
    "httpx>=0.27",
    "uvloop>=0.19; sys_platform == 'linux'",
    "winloop>=0.1; sys_platform == 'win32'",
    "importlib-metadata>=7.0; python_version < '3.12'",
]
```

Il campo `dynamic` e fondamentale: dichiara quali campi saranno forniti dal build backend anziche
essere statici nel TOML. L'esempio piu comune e `version` quando si usa setuptools-scm o hatch-vcs.

### PEP 660 — editable install standard

PEP 660 standardizza le installazioni editable (`pip install -e .`), che prima di questo PEP
erano un'implementazione interna di setuptools senza specifica formale. Il PEP definisce un hook
aggiuntivo nell'interfaccia PEP 517:

```python
def build_editable(wheel_directory, config_settings=None, metadata_directory=None) -> str: ...
```

Il backend produce un wheel "editable" che, una volta installato, reindirizza le importazioni alla
directory sorgente del progetto. Due strategie di implementazione coesistono:

- **pth file** — un file `.pth` in `site-packages` che aggiunge la directory sorgente a `sys.path`.
  E la strategia usata da setuptools e flit. Semplice ma non isolata: tutto il contenuto della
  directory sorgente diventa importabile, non solo il pacchetto.

- **import hook** — un finder/loader personalizzato registrato in `sys.meta_path`. Usato da
  hatchling in modalita strict. Solo il pacchetto dichiarato e importabile, simulando fedelmente
  il comportamento del pacchetto installato.

```bash
# Installazione editable con pip (invoca build_editable del backend)
pip install -e .

# Con uv
uv pip install -e .

# Con opzioni specifiche del backend
pip install -e . --config-settings editable-mode=strict
```

### PEP 639 — metadati licenza SPDX

PEP 639 (accettato 2024) introduce il campo `license` come stringa SPDX invece del formato
legacy `{text = "..."}`. PyPI supporta entrambi i formati, ma il formato SPDX e il futuro:

```toml
# Formato PEP 639 (moderno)
license = "MIT"
license = "Apache-2.0 OR MIT"
license = "GPL-3.0-only"

# Con file di licenza espliciti
license-files = ["LICENSE", "NOTICE"]
```

### PEP 685 — normalizzazione nomi extras

PEP 685 standardizza la normalizzazione dei nomi degli extras: lettere minuscole, trattini e
underscore normalizzati a trattini, punti normalizzati a trattini. Questo significa che
`pip install my-package[DEV]`, `pip install my-package[dev]` e `pip install my-package[Dev]`
sono tutti equivalenti.

---

## Build backend a confronto

Il Modulo 23 presenta setuptools, hatchling, poetry-core e flit-core. Qui aggiungiamo PDM e
maturin, e forniamo una matrice decisionale avanzata.

### Matrice comparativa

| Criterio | setuptools | hatchling | flit-core | PDM (pdm-backend) | maturin | poetry-core |
|----------|-----------|-----------|-----------|-------------------|---------|-------------|
| PEP 621 nativo | Si (v75+) | Si | Si | Si | Si | Parziale |
| PEP 660 editable | Si | Si (strict/lenient) | Si | Si | Si | Si |
| Estensioni C/C++ | Si | Via hook | No | Via hook | No (Rust only) | No |
| Estensioni Rust | Via hook | Via hook | No | Via hook | Nativo | No |
| Versioning dinamico | setuptools-scm | hatch-vcs | No | pdm-backend | Cargo.toml | poetry-dynamic-versioning |
| Build hook | Si (cmdclass) | Si (hatch hook) | No | Si | Si (Cargo) | No |
| Velocita build | Media | Veloce | Molto veloce | Veloce | Media (compilazione Rust) | Veloce |
| Curva apprendimento | Media | Bassa | Molto bassa | Bassa | Media-alta | Bassa |
| Uso consigliato | Progetti legacy, estensioni C | Progetti nuovi puri Python | Librerie minimali | Progetti con PEP 582 | Estensioni Rust | Chi vuole lock file integrato |

### PDM e pdm-backend

PDM (Python Dependency Manager) e un gestore di pacchetti moderno che adotta pienamente
PEP 621 e offre un proprio build backend `pdm-backend`:

```toml
[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[project]
name = "my-pdm-project"
dynamic = ["version"]
dependencies = ["httpx>=0.27"]

[tool.pdm.version]
source = "scm"                # versione da tag git

[tool.pdm.build]
includes = ["src/my_package"]
source-includes = ["tests", "README.md"]
```

PDM offre funzionalita simili a Poetry ma con aderenza totale agli standard PEP:

```bash
# Inizializzare un progetto
pdm init

# Aggiungere dipendenze
pdm add httpx pydantic
pdm add -dG test pytest pytest-cov

# Installare (crea pdm.lock)
pdm install

# Eseguire comandi nel contesto del progetto
pdm run python -m my_package
pdm run pytest

# Pubblicare
pdm publish
```

Il file `pdm.lock` usa il formato TOML e registra hash SHA256 per ogni artefatto, garantendo
integrita oltre alla riproducibilita.

### Criteri di scelta

**Scegliere setuptools quando:**
- Il progetto ha estensioni C/C++ con build complessi
- Si mantiene un progetto legacy che usa gia setup.py/setup.cfg
- Servono feature avanzate come `cmdclass` personalizzate

**Scegliere hatchling quando:**
- Si inizia un nuovo progetto Python puro
- Si vuole versioning dinamico senza dipendenze extra pesanti
- Si usa Hatch come project manager (ambienti, matrici di test)

**Scegliere flit-core quando:**
- La libreria e piccola, pura Python, senza build complessi
- Si vuole la configurazione piu minimale possibile
- Non servono build hook o versioning dinamico

**Scegliere pdm-backend quando:**
- Si vuole piena aderenza PEP 621 con lock file integrato
- Si preferisce un'alternativa a Poetry con standard aperti
- Si lavora in un team che adotta PDM come tool di gestione

**Scegliere maturin quando:**
- Il progetto contiene estensioni Rust (PyO3/pyo3)
- Si vuole compilazione Rust integrata nel workflow Python
- Si sviluppa un binding Python per una libreria Rust

---

## pyproject.toml — approfondimento

Il Modulo 23 copre la struttura base di `[project]`, `[build-system]` e `[tool.*]`. Qui
approfondiamo pattern avanzati.

### Campi dinamici

Il campo `dynamic` in `[project]` dichiara quali metadati saranno forniti dal build backend.
Il backend li calcola al momento del build:

```toml
[project]
name = "analytics-engine"
dynamic = ["version", "readme"]

# La versione viene da setuptools-scm
[tool.setuptools_scm]
version_scheme = "post-release"
local_scheme = "node-and-date"
write_to = "src/analytics_engine/_version.py"
write_to_template = "__version__ = \"{version}\"\n"

# Il readme viene assemblato da piu file
[tool.setuptools.dynamic]
readme = {file = ["README.md", "CHANGELOG.md"], content-type = "text/markdown"}
```

I campi che possono essere dinamici secondo PEP 621: `version`, `description`, `readme`,
`requires-python`, `license`, `authors`, `maintainers`, `keywords`, `classifiers`,
`urls`, `scripts`, `gui-scripts`, `entry-points`, `dependencies`, `optional-dependencies`.

In pratica, `version` e il campo dinamico piu comune. Rendere dinamiche le `dependencies` e
sconsigliato perche impedisce ai tool di analisi statica (come `pip-audit`, `dependabot`) di
leggere le dipendenze senza invocare il build backend.

### Pattern avanzati [tool.*]

La sezione `[tool.*]` e riservata a strumenti di terze parti. Ogni strumento usa il proprio
namespace (es. `[tool.ruff]`, `[tool.pytest.ini_options]`). Pattern avanzati:

```toml
# Coverage con branch coverage e report multipli
[tool.coverage.run]
source = ["src/my_package"]
branch = true
parallel = true
omit = ["*/tests/*", "*/_version.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@overload",
    "raise NotImplementedError",
    "\\.\\.\\.",
]

[tool.coverage.paths]
source = [
    "src/my_package",
    "*/site-packages/my_package",
]

# Ruff con regole per-file diverse
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D", "ANN101", "COM812", "ISC001"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN"]      # assert e no type hints nei test
"scripts/**/*.py" = ["T201", "INP001"]  # print e no __init__.py negli script
"**/conftest.py" = ["ANN"]

# Mypy con overrides per-modulo
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
allow_untyped_defs = true
disable_error_code = ["no-untyped-def"]

[[tool.mypy.overrides]]
module = ["boto3.*", "botocore.*"]
ignore_missing_imports = true
```

### Inclusione dati non-Python

Ogni backend gestisce i file dati (JSON, YAML, template, modelli ML) in modo leggermente diverso:

```toml
# setuptools
[tool.setuptools.package-data]
my_package = [
    "data/*.json",
    "data/*.yaml",
    "templates/**/*.html",
    "py.typed",
    "models/*.onnx",
]

[tool.setuptools.exclude-package-data]
my_package = ["data/test_*"]

# hatchling
[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]

[tool.hatch.build.targets.wheel.force-include]
"config/defaults.yaml" = "my_package/config/defaults.yaml"

[tool.hatch.build.targets.sdist]
include = ["/src", "/tests", "/README.md"]
exclude = ["**/__pycache__", "**/*.pyc"]

# flit — include automaticamente tutto dentro il pacchetto
# esclude pattern comuni (__pycache__, .git, ecc.)
# per esclusioni esplicite:
[tool.flit.sdist]
exclude = ["tests/", "docs/"]
```

### MANIFEST.in per sdist

Con setuptools, il file `MANIFEST.in` controlla cosa viene incluso nella source distribution.
Hatchling e flit usano i propri meccanismi (vedi sopra):

```
# MANIFEST.in
include LICENSE README.md CHANGELOG.md
include pyproject.toml
recursive-include src *.py *.pyi py.typed
recursive-include src/my_package/data *.json *.yaml
recursive-include tests *.py
graft docs
prune docs/_build
global-exclude __pycache__ *.pyc *.pyo .DS_Store
```

La tendenza moderna e eliminare `MANIFEST.in` migrando a hatchling o configurando
`[tool.setuptools.packages.find]` con attenzione. setuptools moderno con `pyproject.toml`
include automaticamente molti file comuni, riducendo la necessita di MANIFEST.in esplicito.

---

## Source distribution vs wheel

### Anatomia di un wheel

Un wheel e un archivio ZIP con estensione `.whl`. Il nome segue la convenzione:

```
{distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
```

Esempi:

```
# Puro Python, compatibile con qualsiasi interprete Python 3
my_package-1.0.0-py3-none-any.whl

# Python 3.12 con ABI stabile, per Linux x86_64
my_package-1.0.0-cp312-cp312-linux_x86_64.whl

# Python 3.12, manylinux 2.17 (glibc 2.17+), x86_64
numpy-2.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

# macOS universal2 (arm64 + x86_64)
my_package-1.0.0-cp312-cp312-macosx_11_0_universal2.whl

# Windows AMD64
my_package-1.0.0-cp312-cp312-win_amd64.whl
```

**Tag Python** (`cp312`): interprete e versione. `cp` = CPython, `pp` = PyPy.

**Tag ABI** (`cp312`): versione ABI. Per pacchetti puri Python e `none`. Per estensioni native
indica la versione dell'ABI C di Python.

**Tag piattaforma** (`manylinux_2_17_x86_64`): sistema operativo e architettura. `any` per
pacchetti puri Python.

### Struttura interna del wheel

```
my_package-1.0.0-py3-none-any.whl (ZIP)
├── my_package/
│   ├── __init__.py
│   ├── core.py
│   ├── utils.py
│   └── data/
│       └── config.json
├── my_package-1.0.0.dist-info/
│   ├── METADATA           # metadati del pacchetto (PEP 566)
│   ├── WHEEL              # metadati del wheel (versione formato, tag)
│   ├── RECORD             # hash SHA256 e dimensione di ogni file
│   ├── entry_points.txt   # entry point (console_scripts, ecc.)
│   ├── top_level.txt      # pacchetti top-level
│   └── LICENSE
```

Il file `RECORD` contiene la lista di tutti i file con hash crittografico:

```
my_package/__init__.py,sha256=abc123...,1234
my_package/core.py,sha256=def456...,5678
my_package-1.0.0.dist-info/METADATA,sha256=ghi789...,2048
my_package-1.0.0.dist-info/RECORD,,
```

### Anatomia di una source distribution

Una sdist (`.tar.gz`) contiene i sorgenti del progetto piu i metadati necessari per invocare
il build backend:

```
my_package-1.0.0.tar.gz
├── my_package-1.0.0/
│   ├── pyproject.toml         # obbligatorio
│   ├── PKG-INFO               # metadati pre-generati
│   ├── README.md
│   ├── LICENSE
│   ├── src/
│   │   └── my_package/
│   │       ├── __init__.py
│   │       ├── core.py
│   │       └── utils.py
│   └── tests/
│       └── test_core.py
```

Quando pip installa da sdist, esegue il build backend per generare un wheel temporaneo,
poi installa quel wheel. Se la sdist contiene estensioni C, questa fase richiede un compilatore.

### Quando servono entrambi

| Artefatto | Installazione | Richiede compilatore | Uso principale |
|-----------|--------------|---------------------|----------------|
| wheel | Velocissima (unzip + copia) | No | Installazione standard |
| sdist | Lenta (build + install) | Si (se estensioni native) | Fallback, audit, build da sorgente |

Best practice: pubblicare **sempre entrambi**. Il wheel copre il caso comune; la sdist serve per:
- Piattaforme senza wheel pre-compilato
- Audit di sicurezza del codice sorgente
- Build riproducibili da sorgente
- Distribuzione Linux con policy (Debian, Fedora) che richiedono compilazione da sorgente

---

## Wheel platform-specific e manylinux

### Il problema della portabilita su Linux

Linux non ha una ABI stabile tra distribuzioni. Un `.so` compilato su Ubuntu 24.04 potrebbe non
funzionare su CentOS 7 perche dipende da una versione di glibc piu recente. Il progetto
**manylinux** risolve questo problema definendo un set minimo di librerie e versioni che un wheel
puo assumere presenti sul sistema target.

### Standard manylinux

| Tag | Requisito glibc | Copertura |
|-----|-----------------|-----------|
| `manylinux1` | glibc 2.5 | CentOS 5+ (deprecato) |
| `manylinux2010` | glibc 2.12 | CentOS 6+ (deprecato) |
| `manylinux2014` | glibc 2.17 | CentOS 7+ |
| `manylinux_2_24` | glibc 2.24 | Debian 9+ |
| `manylinux_2_28` | glibc 2.28 | Debian 10+, Ubuntu 20.04+ |
| `manylinux_2_31` | glibc 2.31 | Debian 11+, Ubuntu 20.04+ |
| `manylinux_2_35` | glibc 2.35 | Ubuntu 22.04+ |

**musllinux** e l'equivalente per distribuzioni basate su musl libc (Alpine Linux):

| Tag | Requisito musl |
|-----|----------------|
| `musllinux_1_1` | musl 1.1+ |
| `musllinux_1_2` | musl 1.2+ |

### auditwheel — riparazione wheel Linux

`auditwheel` analizza un wheel Linux e lo rende conforme allo standard manylinux copiando le
librerie condivise necessarie all'interno del wheel stesso:

```bash
# Installare auditwheel
pip install auditwheel

# Analizzare un wheel
auditwheel show dist/my_package-1.0.0-cp312-cp312-linux_x86_64.whl

# Output tipico:
# my_package-1.0.0-cp312-cp312-linux_x86_64.whl is consistent with:
#     linux_x86_64
# Libraries needed:
#     libcrypto.so.3 => /lib/x86_64-linux-gnu/libcrypto.so.3
#     libssl.so.3 => /lib/x86_64-linux-gnu/libssl.so.3

# Riparare il wheel per manylinux_2_28
auditwheel repair dist/my_package-1.0.0-cp312-cp312-linux_x86_64.whl \
    --plat manylinux_2_28_x86_64 \
    --wheel-dir dist-repaired/

# Il wheel riparato contiene le librerie all'interno:
# my_package-1.0.0-cp312-cp312-manylinux_2_28_x86_64.whl
#   └── my_package.libs/
#       ├── libcrypto.so.3
#       └── libssl.so.3
```

`auditwheel` usa `patchelf` per modificare gli rpath delle librerie condivise, facendole puntare
alla directory interna del wheel. Questo rende il wheel autosufficiente.

### delocate — equivalente per macOS

Su macOS, `delocate` svolge la stessa funzione di `auditwheel`:

```bash
pip install delocate

# Analizzare
delocate-listdeps dist/my_package-1.0.0-cp312-cp312-macosx_14_0_arm64.whl

# Riparare
delocate-wheel -w dist-repaired/ dist/my_package-1.0.0-cp312-cp312-macosx_14_0_arm64.whl
```

### Wheel universal2 per macOS

Un wheel `universal2` contiene codice nativo per entrambe le architetture macOS (arm64 e x86_64)
in un unico fat binary:

```bash
# Compilare per universal2
ARCHFLAGS="-arch arm64 -arch x86_64" pip wheel . --no-deps

# Oppure con cibuildwheel (vedi sotto)
CIBW_ARCHS_MACOS="universal2" cibuildwheel --platform macos
```

### cibuildwheel — automazione CI

`cibuildwheel` e lo strumento standard per compilare wheel platform-specific in CI. Gestisce
la creazione di ambienti isolati per ogni combinazione Python version + piattaforma + architettura:

```toml
# pyproject.toml
[tool.cibuildwheel]
# Versioni Python da supportare
build = "cp311-* cp312-* cp313-*"
skip = "pp* *-musllinux_i686"

# Test dopo la compilazione
test-requires = "pytest"
test-command = "pytest {project}/tests -x"

[tool.cibuildwheel.linux]
# Immagine Docker per la compilazione
manylinux-x86_64-image = "manylinux_2_28"
manylinux-aarch64-image = "manylinux_2_28"

# Variabili d'ambiente per la compilazione
environment = { CFLAGS="-O2 -march=x86-64-v2" }

# Comando prima del build (installare dipendenze sistema)
before-build = "yum install -y openssl-devel || apk add openssl-dev"

[tool.cibuildwheel.macos]
archs = "x86_64 arm64 universal2"

[tool.cibuildwheel.windows]
archs = "AMD64 ARM64"
```

Workflow GitHub Actions completo:

```yaml
# .github/workflows/wheels.yml
name: Build wheels

on:
  push:
    tags: ["v*"]

jobs:
  build-wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Build wheels
        uses: pypa/cibuildwheel@v2.21
        env:
          CIBW_BUILD: "cp311-* cp312-* cp313-*"
          CIBW_SKIP: "pp* *-musllinux_i686"
          CIBW_TEST_REQUIRES: pytest
          CIBW_TEST_COMMAND: "pytest {project}/tests -x"

      - uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}
          path: wheelhouse/*.whl

  build-sdist:
    name: Build source distribution
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pipx run build --sdist
      - uses: actions/upload-artifact@v4
        with:
          name: sdist
          path: dist/*.tar.gz

  publish:
    needs: [build-wheels, build-sdist]
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: dist
          merge-multiple: true
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Questo workflow:
1. Compila wheel per Linux, macOS e Windows con multiple versioni Python
2. Genera la source distribution
3. Pubblica tutto su PyPI tramite Trusted Publishers (OIDC)

### ABI stabile (abi3) e Limited API

L'ABI stabile di CPython, definita in PEP 384, permette di compilare un modulo di estensione
**una sola volta** per una versione minima di Python e di utilizzarlo su tutte le versioni
successive senza ricompilazione. Questo riduce drasticamente il numero di wheel da pubblicare:
invece di un wheel per cp311, cp312, cp313, cp314, si pubblica un unico wheel con tag
`cp3x-abi3-<platform>`.

**Come funziona:** la Limited API e un sottoinsieme dell'API C di Python che garantisce stabilita
binaria. Un'estensione compilata contro la Limited API di CPython 3.11 funziona su 3.12, 3.13
e versioni future senza modifiche, perche le strutture dati e le funzioni esposte mantengono la
stessa disposizione in memoria e la stessa firma.

**Compilazione con `Py_LIMITED_API`:**

Per usare la Limited API, il codice sorgente C deve definire la macro `Py_LIMITED_API` prima
di includere `Python.h`:

```c
// my_extension.c
#define Py_LIMITED_API 0x030B0000  // Python 3.11+
#include <Python.h>

static PyObject* my_function(PyObject* self, PyObject* args) {
    // Usare solo funzioni della Limited API
    const char* input;
    if (!PyArg_ParseTuple(args, "s", &input))
        return NULL;
    return PyUnicode_FromFormat("Elaborato: %s", input);
}

static PyMethodDef methods[] = {
    {"my_function", my_function, METH_VARARGS, "Funzione di esempio"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "my_ext", NULL, -1, methods
};

PyMODINIT_FUNC PyInit_my_ext(void) {
    return PyModule_Create(&module);
}
```

**Configurazione setuptools per abi3:**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"
```

```python
# setup.py
from setuptools import setup, Extension

setup(
    ext_modules=[
        Extension(
            "my_package.my_ext",
            sources=["src/my_package/my_ext.c"],
            define_macros=[("Py_LIMITED_API", "0x030B0000")],
            py_limited_api=True,
        )
    ],
    options={"bdist_wheel": {"py_limited_api": "cp311"}},
)
```

Il wheel risultante avra il nome `my_package-1.0.0-cp311-abi3-linux_x86_64.whl` e sara
installabile su Python 3.11, 3.12, 3.13+ senza ricompilazione.

**Configurazione cibuildwheel per abi3:**

```toml
[tool.cibuildwheel]
# Compilare solo per una versione (il wheel e compatibile con le successive)
build = "cp311-*"

[tool.cibuildwheel.config-settings]
# Passare la configurazione al backend
"setup-args" = "--build-option=--py-limited-api=cp311"
```

**Verifica con abi3audit:**

`abi3audit` verifica che un wheel abi3 usi effettivamente solo le funzioni della Limited API.
Se il codice chiama funzioni non incluse nella Limited API, il wheel potrebbe crashare su
versioni future di Python:

```bash
pip install abi3audit

# Verificare un wheel locale
abi3audit dist/my_package-1.0.0-cp311-abi3-linux_x86_64.whl

# Verificare un pacchetto da PyPI
abi3audit --verbose cryptography

# Output di esempio per un wheel conforme:
# my_package-1.0.0-cp311-abi3-linux_x86_64.whl: OK
#   my_package/my_ext.cpython-311-x86_64-linux-gnu.so: ABI3 compatible (cp311+)
```

**Limitazioni della Limited API:**

Non tutte le funzionalita dell'API C sono disponibili nella Limited API. Le esclusioni principali:

- Accesso diretto ai campi di `PyObject` (es. `ob_refcnt`, `ob_type`)
- Macro che espongono dettagli implementativi (es. `PyTuple_GET_ITEM`)
- API per il GIL free-threading (PEP 703)
- Alcune funzioni di recente introduzione non ancora stabilizzate

Per il free-threaded Python (PEP 703, sperimentale in 3.13+), PEP 803 propone una variante
`abi3t` che rende opaca la struttura `PyObject`, necessaria perche il free-threaded Python
cambia il layout di `PyObject`. PEP 809 propone inoltre un'evoluzione futura (`abi2026`) che
risolve incompatibilita note nell'attuale abi3.

**Quando usare abi3:**

- Estensioni C con logica semplice che non richiede API interne di CPython
- Pacchetti con molte piattaforme target (riduce il numero di wheel da 15+ a 5)
- Librerie crittografiche o di parsing che vogliono massima compatibilita
- Non adatto per estensioni che usano pesantemente NumPy C API o API interne di CPython

---

## PEP 660 — editable install standard

### Motivazione

Prima di PEP 660, `pip install -e .` funzionava solo con setuptools tramite un meccanismo
non standardizzato (`setup.py develop`). Questo creava un legame diretto tra pip e setuptools,
impedendo l'uso di installazioni editable con altri backend.

PEP 660 (accettato 2022) definisce un hook standard `build_editable()` che qualsiasi backend
puo implementare. Il risultato e un wheel "editable" — un wheel che, una volta installato,
reindirizza le importazioni ai sorgenti del progetto.

### Strategie di implementazione

I backend implementano l'editable install con strategie diverse:

**Strategia pth (setuptools, flit):**

```
# In site-packages dopo pip install -e .
my_package-1.0.0.dist-info/          # metadati standard
__editable__.my_package-1.0.0.pth    # contiene: /path/to/project/src
```

Il file `.pth` aggiunge `/path/to/project/src` a `sys.path`. Tutto il contenuto di quella
directory diventa importabile — non solo il pacchetto dichiarato.

**Strategia import hook — modalita strict (hatchling):**

```
# In site-packages dopo pip install -e . con hatchling strict
my_package-1.0.0.dist-info/
_my_package_editable_finder.py        # import hook personalizzato
__editable__.my_package-1.0.0.pth    # attiva il finder
```

Il finder personalizzato intercetta solo le importazioni del pacchetto dichiarato e le
reindirizza ai sorgenti. Tutto il resto non e importabile — comportamento identico a
un'installazione non-editable.

### Configurazione per backend

```bash
# setuptools (pth strategy, default)
pip install -e .

# hatchling — modalita lenient (pth, default)
pip install -e .

# hatchling — modalita strict (import hook)
pip install -e . --config-settings editable-mode=strict

# flit (pth strategy)
pip install -e .
# oppure
flit install --symlink    # alternativa: symlink invece di pth

# PDM
pdm install --dev         # installazione editable implicita

# uv
uv pip install -e .
```

### Quando usare la modalita strict

La modalita strict e consigliata per:
- Librerie destinate alla pubblicazione — assicura che i test importino solo cio che sara
  disponibile dopo l'installazione standard
- Progetti con struttura complessa — previene importazioni accidentali da directory sorgente
- CI/CD — un test in modalita strict fallisce immediatamente se un file non e incluso nel
  pacchetto, rivelando problemi di packaging prima della pubblicazione

### Internals — come funzionano i file .pth

I file `.pth` sono un meccanismo di Python (non di pip o setuptools): al caricamento
dell'interprete, `site.py` legge tutti i file `.pth` in `site-packages` e:

1. Se la riga contiene un percorso valido, lo aggiunge a `sys.path`
2. Se la riga inizia con `import`, la esegue come codice Python

Questo secondo comportamento e quello sfruttato dai finder personalizzati:

```python
# __editable__.my_package-1.0.0.pth (generato da hatchling in modalita strict)
import _my_package_editable_finder; _my_package_editable_finder.install()
```

Il finder si registra in `sys.meta_path` e intercetta tutte le importazioni che corrispondono
al nome del pacchetto, risolvendo il modulo dal sorgente originale:

```python
# Semplificazione del meccanismo interno del finder
class _EditableFinder:
    _MAPPING = {
        "my_package": "/home/user/project/src/my_package",
        "my_package.utils": "/home/user/project/src/my_package/utils",
    }

    @classmethod
    def find_spec(cls, name, path=None, target=None):
        if name in cls._MAPPING or any(
            name.startswith(k + ".") for k in cls._MAPPING
        ):
            # Restituisce ModuleSpec che punta al sorgente
            origin = cls._resolve_path(name)
            return importlib.util.spec_from_file_location(name, origin)
        return None  # non gestito, passa al finder successivo
```

### Il pacchetto `editables`

Il pacchetto `editables` (usato internamente da flit e hatchling) fornisce un'API pulita per
generare il boilerplate degli editable install:

```python
from editables import EditableProject

project = EditableProject("my_package", "/home/user/project/src")

# Genera i file per site-packages
for filename, content in project.files():
    print(f"{filename}:")
    print(content)

# Output:
# __editable__.my_package-1.0.0.pth:
# import _my_package_editable_finder; _my_package_editable_finder.install()
#
# _my_package_editable_finder.py:
# [codice del finder personalizzato]
```

### Diagnostica delle installazioni editable

```bash
# Verificare se un pacchetto e installato in modalita editable
pip show my-package
# Location: /home/user/project/src  (editable)
# vs
# Location: /usr/lib/python3.12/site-packages  (standard)

# Elencare tutti i pacchetti editable
pip list --editable

# Con uv
uv pip list | grep "editable"

# Verificare il file .pth attivo
python -c "
import site
for p in site.getsitepackages():
    import os
    for f in os.listdir(p):
        if f.startswith('__editable__'):
            print(f'{p}/{f}')
"
```

---

## Pubblicazione su PyPI e release automation

Il Modulo 23 copre i fondamentali di twine e Trusted Publishers. Qui approfondiamo l'automazione
del ciclo di release.

### Trusted Publishers — meccanismo OIDC

Il funzionamento interno: quando GitHub Actions esegue un workflow, richiede un token OIDC a
GitHub, che lo firma con la propria chiave privata. Il workflow invia questo token a PyPI,
che lo verifica contro la chiave pubblica di GitHub e controlla i claim (repository, workflow,
environment). Se tutto corrisponde alla configurazione del Trusted Publisher, PyPI emette un
token temporaneo per il caricamento.

Configurazione su PyPI:
1. Accedere a pypi.org -> Your Projects -> Manage -> Publishing
2. "Add a new pending publisher" (per pacchetti non ancora pubblicati) oppure
   "Add publisher" (per pacchetti esistenti)
3. Compilare: GitHub repository owner, repository name, workflow filename, environment name

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
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build twine
      - run: python -m build
      - run: twine check dist/*
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish-testpypi:
    needs: build
    runs-on: ubuntu-latest
    environment: testpypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

  publish-pypi:
    needs: publish-testpypi
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Questo workflow pubblica prima su TestPyPI (con environment `testpypi`), poi su PyPI
(con environment `pypi`). L'environment GitHub Actions agisce come gate: si possono
configurare approvazioni manuali, timeout e restrizioni di branch.

### Release automation con semantic-release

`python-semantic-release` automatizza l'intero ciclo: analisi commit, bump versione,
changelog, tag git, pubblicazione:

```toml
# pyproject.toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/my_package/__init__.py:__version__"]
branch = "main"
commit_message = "chore(release): {version}"
build_command = "pip install build && python -m build"

[tool.semantic_release.changelog]
template_dir = "templates"
changelog_file = "CHANGELOG.md"

[tool.semantic_release.remote]
type = "github"
token = { env = "GH_TOKEN" }

[tool.semantic_release.publish]
upload_to_pypi = true
```

```yaml
# .github/workflows/semantic-release.yml
name: Semantic Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install python-semantic-release
      - name: Release
        run: semantic-release version --no-vcs-release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Publish
        if: steps.release.outputs.released == 'true'
        uses: pypa/gh-action-pypi-publish@release/v1
```

Il workflow analizza i commit dalla release precedente:
- `feat: ...` -> bump minor
- `fix: ...` -> bump patch
- `feat!: ...` o `BREAKING CHANGE:` nel body -> bump major

### Verifica pre-pubblicazione

```bash
# Controllare la struttura del pacchetto
twine check dist/*

# Verificare i metadati
python -c "
import zipfile, sys
whl = sys.argv[1]
with zipfile.ZipFile(whl) as z:
    for name in z.namelist():
        if name.endswith('METADATA'):
            print(z.read(name).decode())
" dist/*.whl

# Testare l'installazione in ambiente pulito
python -m venv /tmp/test-install
/tmp/test-install/bin/pip install dist/*.whl
/tmp/test-install/bin/python -c "import my_package; print(my_package.__version__)"

# Installare da TestPyPI e verificare
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    my-package
```

---

## Supply chain security — Sigstore e attestazioni digitali

La sicurezza della supply chain e diventata una priorita assoluta dopo attacchi ad alta visibilita
(SolarWinds, event-stream, codecov). L'ecosistema Python ha risposto con meccanismi crittografici
moderni che sostituiscono il vecchio sistema PGP, rimosso da PyPI nel 2023.

### Il problema della fiducia

Quando un utente esegue `pip install my-package`, si fida implicitamente di una catena:
1. Lo sviluppatore ha scritto il codice
2. Il codice e stato compilato correttamente
3. L'artefatto su PyPI corrisponde al codice sorgente
4. Nessuno ha manomesso il pacchetto durante il caricamento

Prima di PEP 740, non esisteva un modo standard per verificare crittograficamente nessuno
di questi passaggi. Le firme PGP erano opzionali, raramente usate e mai verificate da pip.

### PEP 740 — attestazioni di integrità per PyPI

PEP 740 (accettato nel 2024) introduce il concetto di **attestazioni digitali** per i pacchetti
PyPI. Un'attestazione e un documento firmato crittograficamente che lega un artefatto (wheel o
sdist) alla specifica esecuzione CI che lo ha prodotto.

Il meccanismo si basa su tre componenti:

1. **Sigstore** — infrastruttura di firma keyless (senza gestione chiavi)
2. **OIDC identity** — l'identita del publisher viene dall'identity provider CI (GitHub, GitLab)
3. **Transparency log (Rekor)** — registro pubblico immutabile di tutte le firme

```
Flusso di attestazione PEP 740:

  Developer push tag v1.2.0
       │
       ▼
  GitHub Actions workflow (Trusted Publisher)
       │
       ├─ Build wheel + sdist
       │
       ├─ Richiede OIDC token a GitHub
       │
       ├─ Sigstore firma l'artefatto con identita OIDC
       │    (nessuna chiave privata da gestire)
       │
       ├─ Attestazione registrata su Rekor (transparency log)
       │
       └─ Upload su PyPI con attestazione allegata
              │
              ▼
         PyPI verifica l'attestazione e la pubblica
```

### Abilitare le attestazioni con GitHub Actions

A partire dalla versione 1.11 di `gh-action-pypi-publish`, le attestazioni sono abilitate
**automaticamente** quando si usa Trusted Publishing con OIDC:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write       # richiesto per OIDC
  contents: read
  attestations: write   # richiesto per attestazioni GitHub

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

      # Genera attestazione GitHub per ogni artefatto
      - uses: actions/attest-build-provenance@v2
        with:
          subject-path: "dist/*"

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      # Le attestazioni Sigstore vengono generate automaticamente
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Verifica delle attestazioni

```bash
# Installare il tool di verifica
pip install pypi-attestations

# Verificare un pacchetto scaricato
python -m pypi_attestations verify my-package-1.2.0.tar.gz \
    --identity "https://github.com/owner/repo/.github/workflows/publish.yml@refs/tags/v1.2.0"

# Scaricare e verificare le attestazioni da PyPI
python -m pypi_attestations download my-package==1.2.0

# Ispezionare il contenuto di un'attestazione
python -m pypi_attestations inspect my-package-1.2.0.tar.gz.sigstore.json
```

Le attestazioni PyPI sono consultabili anche via API REST:

```bash
# Ottenere le attestazioni per un file specifico
curl -s https://pypi.org/simple/my-package/ \
    -H "Accept: application/vnd.pypi.simple.v1+json" | \
    python -m json.tool

# Verificare con sigstore-python direttamente
pip install sigstore
python -m sigstore verify identity \
    --cert-identity "https://github.com/owner/repo/.github/workflows/publish.yml@refs/tags/v1.2.0" \
    --cert-oidc-issuer "https://token.actions.githubusercontent.com" \
    dist/my-package-1.2.0.tar.gz
```

### pip e la verifica futura

Al momento (2025), pip non verifica automaticamente le attestazioni durante l'installazione.
Il piano prevede l'integrazione graduale:

1. **Fase attuale:** i publisher generano attestazioni, PyPI le archivia e le espone via API
2. **Fase prossima:** pip permettera `--require-attestation` per richiedere attestazioni verificate
3. **Fase finale:** le attestazioni diventeranno il default per pacchetti con Trusted Publisher

### Confronto con altri ecosistemi

| Aspetto | Python (PEP 740) | npm (Provenance) | Go (sumdb) |
|---------|-------------------|-------------------|------------|
| Firma | Sigstore (keyless) | Sigstore | Transparency log |
| Identita | OIDC CI provider | OIDC CI provider | Checksum database |
| Log pubblico | Rekor | Rekor | sum.golang.org |
| Obbligatorio | No (opt-in) | No (opt-in) | Si (default) |
| Copertura | wheel + sdist | tarball | Moduli Go |

### Best practice per la supply chain Python

```bash
# 1. Usare SEMPRE Trusted Publishers (mai token statici)
#    Configurare su pypi.org/manage/project/<name>/settings/publishing/

# 2. Pinnare le dipendenze con hash
pip install --require-hashes -r requirements.txt

# 3. Audit delle dipendenze
pip install pip-audit
pip-audit --require-hashes -r requirements.txt

# 4. Usare uv con verifica hash automatica
uv sync  # verifica hash dal lockfile automaticamente

# 5. Scansione vulnerabilita nel CI
# .github/workflows/audit.yml
# - uses: pypa/gh-action-pip-audit@v1.1.0
#   with:
#     inputs: requirements.txt
```

---

## Registri privati

Il Modulo 23 presenta devpi e AWS CodeArtifact. Qui aggiungiamo le soluzioni mancanti e
approfondiamo devpi come soluzione self-hosted completa.

### devpi — approfondimento

devpi e il server PyPI self-hosted piu maturo dell'ecosistema Python. Combina tre funzionalita
in un unico sistema: **proxy cache** verso PyPI, **indice privato** per pacchetti interni e
**staging area** per test pre-pubblicazione.

#### Architettura e installazione

```bash
# Installare devpi (server + client + web UI)
pip install devpi-server devpi-client devpi-web

# Inizializzare il server (crea database locale)
devpi-server --init

# Avviare il server
devpi-server --host 0.0.0.0 --port 3141

# Primo accesso: configurare il client
devpi use http://localhost:3141
devpi login root --password=""    # password iniziale vuota
devpi user -m root password=<nuova_password>
```

#### Gerarchia degli indici

devpi organizza i pacchetti in una gerarchia **utente/indice**. Ogni indice puo ereditare
da altri indici, creando una catena di fallback:

```
root/pypi        ← mirror/cache di pypi.org (creato automaticamente)
  ↑ eredita
company/stable   ← pacchetti interni approvati per produzione
  ↑ eredita
company/staging  ← pacchetti in fase di test/review
  ↑ eredita
dev/sandbox      ← pacchetti sperimentali dello sviluppatore
```

```bash
# Creare un utente
devpi user -c company password=secret

# Creare l'indice stable che eredita da root/pypi
devpi index -c company/stable bases=root/pypi

# Creare l'indice staging che eredita da stable
devpi index -c company/staging bases=company/stable

# Usare l'indice staging come default
devpi use company/staging
```

Quando pip cerca un pacchetto nell'indice `company/staging`:
1. Cerca prima in `company/staging`
2. Se non lo trova, cerca in `company/stable`
3. Se non lo trova, cerca in `root/pypi` (cache di pypi.org)

#### Caching proxy

Come proxy cache, devpi scarica i pacchetti da PyPI alla prima richiesta e li serve dalla cache
per le richieste successive. Vantaggi:
- **Velocita**: installazioni interne 10-100x piu veloci dopo il primo download
- **Resilienza**: i pacchetti cachati restano disponibili anche se PyPI non e raggiungibile
- **Audit**: log completo di tutti i pacchetti installati nell'organizzazione

```bash
# Configurare pip per usare devpi come indice
pip config set global.index-url http://devpi.internal:3141/company/stable/+simple/

# Con uv
uv pip install --index-url http://devpi.internal:3141/company/stable/+simple/ httpx
```

#### Upload e promozione

```bash
# Upload diretto all'indice staging
devpi use company/staging
devpi upload dist/*

# Testare il pacchetto dall'indice staging
pip install my-package --index-url http://devpi.internal:3141/company/staging/+simple/

# Promuovere a stable (copia senza re-upload)
devpi push my-package==1.2.0 company/stable
```

#### Deployment con Docker

```yaml
# docker-compose.yml
services:
  devpi:
    image: python:3.12-slim
    command: >
      bash -c "pip install devpi-server devpi-web &&
               devpi-server --init || true &&
               devpi-server --host 0.0.0.0 --port 3141
                 --serverdir /data"
    volumes:
      - devpi-data:/data
    ports:
      - "3141:3141"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3141/+api"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  devpi-data:
```

Per ambienti di produzione, aggiungere nginx come reverse proxy con TLS:

```nginx
# /etc/nginx/sites-available/devpi
server {
    listen 443 ssl;
    server_name devpi.company.com;

    ssl_certificate     /etc/ssl/certs/devpi.pem;
    ssl_certificate_key /etc/ssl/private/devpi.key;

    client_max_body_size 100M;     # per upload di wheel grandi

    location / {
        proxy_pass http://127.0.0.1:3141;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### JFrog Artifactory

Artifactory e la soluzione enterprise piu diffusa per repository di artefatti. Supporta PyPI,
npm, Maven, Docker e decine di altri formati in un'unica piattaforma:

```bash
# Configurazione pip
pip config set global.index-url \
    https://company.jfrog.io/artifactory/api/pypi/python-local/simple/

# Upload con twine
twine upload \
    --repository-url https://company.jfrog.io/artifactory/api/pypi/python-local/ \
    -u $ARTIFACTORY_USER \
    -p $ARTIFACTORY_TOKEN \
    dist/*

# In pip.conf
[global]
index-url = https://company.jfrog.io/artifactory/api/pypi/python-virtual/simple/
trusted-host = company.jfrog.io
```

Artifactory supporta "virtual repositories" che aggregano piu sorgenti (PyPI pubblico +
repository privati) dietro un unico URL. Il client pip fa una sola richiesta e Artifactory
cerca in tutti i repository configurati.

### GitLab Package Registry

GitLab offre un registro PyPI integrato in ogni progetto o gruppo:

```bash
# Configurazione per un progetto specifico
pip config set global.extra-index-url \
    https://gitlab.com/api/v4/projects/<project_id>/packages/pypi/simple/ \
    --trusted-host gitlab.com

# Upload con twine
# In ~/.pypirc
[gitlab]
repository = https://gitlab.com/api/v4/projects/<project_id>/packages/pypi
username = __token__
password = <personal_access_token_o_deploy_token>

twine upload --repository gitlab dist/*

# Per un gruppo (tutti i pacchetti del gruppo accessibili con un URL)
pip install my-internal-package \
    --extra-index-url https://__token__:<token>@gitlab.com/api/v4/groups/<group_id>/-/packages/pypi/simple/
```

### Google Artifact Registry

```bash
# Autenticazione
gcloud auth application-default login

# Configurazione pip (keyring-based)
pip install keyrings.google-artifactregistry-auth

# In pip.conf
[global]
extra-index-url = https://us-python.pkg.dev/my-project/my-repo/simple/

# Upload
twine upload \
    --repository-url https://us-python.pkg.dev/my-project/my-repo/ \
    dist/*
```

### Configurazione uv con registri privati

uv supporta registri privati tramite variabili d'ambiente o `uv.toml`:

```toml
# uv.toml (nella root del progetto)
[[index]]
name = "internal"
url = "https://pypi.internal.company.com/simple/"

[[index]]
name = "pypi"
url = "https://pypi.org/simple/"
default = true
```

```bash
# Autenticazione via variabile d'ambiente
UV_INDEX_INTERNAL_USERNAME=__token__ \
UV_INDEX_INTERNAL_PASSWORD=secret \
uv sync
```

### Sicurezza dei registri privati

Avvertenze critiche nell'uso di `--extra-index-url`:

```bash
# PERICOLOSO: dependency confusion attack
# Se un pacchetto "internal-utils" esiste anche su PyPI (malevolo),
# pip potrebbe installare la versione pubblica
pip install internal-utils --extra-index-url https://pypi.internal.com/simple/

# SICURO: usare --index-url (sostituisce PyPI completamente)
pip install internal-utils --index-url https://pypi.internal.com/simple/

# SICURO: usare un virtual repository che filtra i nomi
# (Artifactory, Nexus supportano questa funzionalita)

# SICURO: pinning hash nel requirements.txt
internal-utils==1.2.0 \
    --hash=sha256:abc123...
```

La **dependency confusion** e un attacco dove un attaccante pubblica un pacchetto su PyPI con lo
stesso nome di un pacchetto interno aziendale ma con versione superiore. Se pip cerca sia su PyPI
che sull'indice privato, installa la versione piu alta — quella malevola. Le contromisure sono:
- Usare `--index-url` invece di `--extra-index-url`
- Riservare i nomi dei pacchetti interni su PyPI (pubblicare placeholder)
- Usare hash pinning nei requirements
- Configurare virtual repository con scope di nomi

---

## Monorepo packaging

### Struttura monorepo

In un monorepo, piu pacchetti Python coabitano nello stesso repository git. Ogni pacchetto ha il
proprio `pyproject.toml` e puo dipendere dagli altri:

```
monorepo/
├── pyproject.toml              # workspace root (opzionale, dipende dal tool)
├── packages/
│   ├── core/
│   │   ├── pyproject.toml
│   │   └── src/core/
│   │       └── __init__.py
│   ├── api/
│   │   ├── pyproject.toml      # dipende da "core"
│   │   └── src/api/
│   │       └── __init__.py
│   └── cli/
│       ├── pyproject.toml      # dipende da "core"
│       └── src/cli/
│           └── __init__.py
└── uv.lock                     # lockfile condiviso (se si usa uv)
```

### uv workspaces

uv supporta workspace nativi, ispirati ai workspace di Cargo (Rust):

```toml
# pyproject.toml (root del monorepo)
[project]
name = "my-monorepo"
version = "0.0.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.5",
]
```

```toml
# packages/core/pyproject.toml
[project]
name = "my-core"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```toml
# packages/api/pyproject.toml
[project]
name = "my-api"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "my-core",              # risolto dal workspace
    "fastapi>=0.115",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv.sources]
my-core = { workspace = true }
```

```bash
# Dalla root del monorepo
uv sync                        # installa tutte le dipendenze di tutti i pacchetti
uv run --package my-api pytest # esegue pytest nel contesto di my-api
uv build --package my-core     # build del solo pacchetto core
uv lock                        # aggiorna il lockfile condiviso
```

Il lockfile `uv.lock` e unico per l'intero workspace: garantisce che tutti i pacchetti usino
le stesse versioni delle dipendenze condivise.

### Hatch workspaces (hatch-monorepo)

Hatch non ha un concetto nativo di workspace, ma il plugin `hatch-monorepo` aggiunge questa
funzionalita:

```toml
# pyproject.toml (root)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-monorepo"
version = "0.0.0"

[tool.hatch.env]
requires = ["hatch-monorepo"]

[tool.hatch.envs.default]
features = ["all"]
```

In alternativa, si possono gestire ambienti Hatch separati che installano pacchetti fratelli
in modalita editable:

```toml
# packages/api/pyproject.toml
[tool.hatch.envs.default]
dependencies = [
    "pytest>=8.0",
]

[tool.hatch.envs.default.env-vars]
PIP_FIND_LINKS = "../../packages/core/dist"

[tool.hatch.envs.default.scripts]
test = "pytest tests/"
```

### Strategie per monorepo

| Strategia | Tool | Lock file | Pubblicazione separata |
|-----------|------|-----------|----------------------|
| Workspace uv | uv | `uv.lock` condiviso | Si, con `uv build --package X` |
| Poetry con path deps | Poetry | `poetry.lock` per pacchetto | Si, con override |
| PDM con path deps | PDM | `pdm.lock` per pacchetto | Si |
| pip-tools manuale | pip-compile | `requirements.txt` per pacchetto | Si |
| Pants / Bazel | Build system dedicato | Integrato | Si |

Per la maggior parte dei team, **uv workspaces** e la scelta raccomandata nel 2025/2026: lock
file condiviso, risoluzione deterministica, velocita di installazione.

### Pants e Bazel — build system per monorepo grandi

Per monorepo con centinaia di pacchetti e migliaia di file, i workspace di uv o Poetry possono
non bastare. I **build system dedicati** offrono funzionalita avanzate:

**Pants** (sviluppato da Toolchain, ex Twitter):
- Analisi automatica delle dipendenze tra moduli Python (nessuna dichiarazione manuale)
- **Build incrementale**: ricompila solo cio che e cambiato (cache fine-grained)
- **Esecuzione remota**: distribuisce build e test su cluster (Remote Execution API)
- Supporto nativo per Python, Go, Java, Shell, Docker
- Generazione automatica dei lockfile per pacchetti individuali
- Integrazione con pytest: esegue solo i test impattati dalle modifiche

**Bazel** (sviluppato da Google):
- Modello BUILD file esplicito: ogni directory dichiara i propri target
- **Ermeticita**: build completamente isolati e riproducibili
- Supporto multi-linguaggio nativo (C++, Java, Go, Python, Rust)
- Scalabilita estrema (usato internamente da Google su miliardi di righe di codice)
- `rules_python` per l'integrazione Python

| Aspetto | uv workspace | Pants | Bazel |
|---------|-------------|-------|-------|
| Setup iniziale | Minimo | Medio | Alto |
| Curva di apprendimento | Bassa | Media | Alta |
| Scala raccomandata | 2-30 pacchetti | 10-200+ pacchetti | 50-1000+ pacchetti |
| Cache remota | No | Si | Si |
| Analisi dipendenze auto | No | Si | No (esplicito) |
| Esecuzione remota | No | Si | Si |
| Linguaggi supportati | Solo Python | Multi | Multi |

Per team Python-only con meno di ~30 pacchetti, uv workspace e sufficiente. Pants diventa
vantaggioso quando il monorepo cresce e il costo della CI aumenta significativamente. Bazel
e giustificato per organizzazioni grandi con infrastruttura dedicata e monorepo multi-linguaggio.

---

## Namespace packages

### Concetto

Un namespace package e un pacchetto Python distribuito su piu distribuzioni separate che condividono
un prefisso comune. Esempio classico: il namespace `google.cloud` contiene `google.cloud.storage`,
`google.cloud.bigquery`, `google.cloud.pubsub` — ciascuno installabile separatamente ma tutti
sotto lo stesso namespace.

```bash
pip install google-cloud-storage    # fornisce google.cloud.storage
pip install google-cloud-bigquery   # fornisce google.cloud.bigquery
# Entrambi coesistono sotto "google.cloud" senza conflitti
```

### Implicit namespace packages (PEP 420)

Dal Python 3.3, una directory senza `__init__.py` e automaticamente un namespace package. Questa
e la modalita raccomandata:

```
# Distribuzione A: company-auth
src/
└── company/
    └── auth/
        ├── __init__.py
        └── tokens.py

# Distribuzione B: company-logging
src/
└── company/
    └── logging/
        ├── __init__.py
        └── handlers.py

# Nota: company/ NON ha __init__.py in nessuna delle due distribuzioni
```

```toml
# company-auth/pyproject.toml
[project]
name = "company-auth"

[tool.setuptools.packages.find]
where = ["src"]
# setuptools rileva automaticamente company.auth come namespace package
```

Dopo aver installato entrambi:
```python
from company.auth.tokens import create_jwt
from company.logging.handlers import JsonHandler
# Funziona perche "company" e un namespace package implicito
```

### Errore comune: __init__.py nel namespace

L'errore piu frequente e aggiungere `__init__.py` nella directory del namespace:

```
# SBAGLIATO: company/__init__.py esiste
src/
└── company/
    ├── __init__.py       # <-- QUESTO ROMPE IL NAMESPACE
    └── auth/
        ├── __init__.py
        └── tokens.py
```

Se `company/__init__.py` esiste in una distribuzione ma non nell'altra, Python vedra solo
i sotto-pacchetti della distribuzione che ha l'`__init__.py`. Le importazioni dall'altra
distribuzione falliranno con `ModuleNotFoundError`.

### pkgutil-style namespace packages (legacy)

Prima di Python 3.3, i namespace package richiedevano un `__init__.py` speciale con
`pkgutil.extend_path`:

```python
# company/__init__.py (in ogni distribuzione)
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
```

Oppure con `pkg_resources` (setuptools):

```python
# company/__init__.py
__import__('pkg_resources').declare_namespace(__name__)
```

Entrambi gli approcci sono **deprecati**. I nuovi progetti devono usare implicit namespace
packages (nessun `__init__.py` nella directory del namespace).

### Configurazione per backend

```toml
# setuptools — nessuna configurazione speciale necessaria con find
[tool.setuptools.packages.find]
where = ["src"]
namespaces = true    # default true per setuptools moderno

# hatchling
[tool.hatch.build.targets.wheel]
packages = ["src/company"]

# flit — i namespace package impliciti funzionano automaticamente
```

### Quando usare namespace packages

**Usare quando:**
- Piu team o distribuzioni contribuiscono sotto un prefisso aziendale comune
- Plugin o estensioni di un framework devono vivere sotto un namespace condiviso
- Si sta creando un ecosistema di pacchetti correlati (es. `mycompany.services.*`)

**Non usare quando:**
- Un singolo team mantiene tutto il codice — usare un pacchetto normale
- Il "namespace" ha un solo membro — non aggiunge valore, aggiunge complessita

---

## Entry points e sistemi a plugin

### console_scripts e gui_scripts

Il Modulo 23 presenta `[project.scripts]`. Qui approfondiamo il meccanismo sottostante e i
sistemi a plugin.

Gli entry point sono metadati registrati nel `dist-info` del pacchetto installato. Pip li legge
e crea wrapper script nel PATH. Il file `entry_points.txt` nel dist-info contiene:

```ini
[console_scripts]
my-tool = my_package.cli:main
my-tool-admin = my_package.admin:cli

[gui_scripts]
my-gui = my_package.gui:launch
```

La differenza tra `console_scripts` e `gui_scripts` e rilevante solo su Windows: un gui_script
non apre una finestra console.

### Entry point come sistema a plugin

Oltre a console_scripts, gli entry point supportano **gruppi arbitrari** — il meccanismo standard
per sistemi a plugin in Python:

```toml
# Plugin A: my-formatter-json/pyproject.toml
[project]
name = "my-formatter-json"
dependencies = ["my-app>=2.0"]

[project.entry-points."my_app.formatters"]
json = "my_formatter_json:JsonFormatter"

# Plugin B: my-formatter-xml/pyproject.toml
[project]
name = "my-formatter-xml"
dependencies = ["my-app>=2.0"]

[project.entry-points."my_app.formatters"]
xml = "my_formatter_xml:XmlFormatter"
```

L'applicazione host scopre e carica i plugin a runtime:

```python
# my_app/plugin_manager.py
from importlib.metadata import entry_points

def load_formatters() -> dict[str, type]:
    """Scopre tutti i formatter registrati come entry point."""
    formatters = {}
    eps = entry_points(group="my_app.formatters")
    for ep in eps:
        # ep.name = "json", ep.value = "my_formatter_json:JsonFormatter"
        formatter_class = ep.load()  # importa il modulo e restituisce la classe
        formatters[ep.name] = formatter_class
    return formatters

def format_data(data: dict, format_name: str) -> str:
    """Formatta i dati usando il plugin registrato."""
    formatters = load_formatters()
    if format_name not in formatters:
        available = ", ".join(formatters.keys())
        raise ValueError(
            f"Formato '{format_name}' non trovato. Disponibili: {available}"
        )
    formatter = formatters[format_name]()
    return formatter.format(data)
```

### Protocollo plugin — best practice

```python
# my_app/protocols.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class FormatterPlugin(Protocol):
    """Protocollo che tutti i plugin formatter devono implementare."""

    name: str

    def format(self, data: dict) -> str: ...
    def supports_streaming(self) -> bool: ...
```

```python
# my_app/plugin_manager.py (versione robusta)
from importlib.metadata import entry_points
from my_app.protocols import FormatterPlugin

def load_formatters() -> dict[str, FormatterPlugin]:
    formatters = {}
    for ep in entry_points(group="my_app.formatters"):
        try:
            cls = ep.load()
        except Exception:
            # log warning, skip plugin malformato
            continue

        if not isinstance(cls, type) or not issubclass(cls, FormatterPlugin):
            # log warning: plugin non conforme al protocollo
            continue

        instance = cls()
        formatters[ep.name] = instance
    return formatters
```

### Confronto con altri meccanismi di plugin

| Meccanismo | Discovery | Installazione separata | Standard |
|------------|-----------|----------------------|----------|
| entry_points | Automatico via metadata | Si (pip install) | PEP 631 |
| importlib plugins | Scan directory | No (copia manuale) | No |
| Plugin config file | Lettura file | No | No |
| Decorator registry | Import time | No | No |

Gli entry point sono il meccanismo raccomandato: non richiedono che l'applicazione host conosca
in anticipo i plugin disponibili, funzionano con il sistema di packaging standard e supportano
installazione/rimozione tramite pip.

---

## Optional dependencies e extras

### Definizione

Le optional dependencies (extras) permettono di installare dipendenze aggiuntive per funzionalita
opzionali:

```toml
[project.optional-dependencies]
# Gruppo per sviluppo
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-xdist>=3.5",
    "mypy>=1.10",
    "ruff>=0.5",
]

# Gruppo per documentazione
docs = [
    "sphinx>=7.0",
    "sphinx-rtd-theme>=2.0",
    "myst-parser>=3.0",
    "sphinxcontrib-mermaid>=0.9",
]

# Gruppi per feature opzionali
postgres = ["asyncpg>=0.29", "psycopg[binary]>=3.1"]
redis = ["redis[hiredis]>=5.0"]
s3 = ["boto3>=1.34", "aiobotocore>=2.12"]

# Meta-gruppi che aggregano altri gruppi
all = [
    "my-package[postgres,redis,s3]",
]

# Gruppo con marker di piattaforma
perf = [
    "uvloop>=0.19; sys_platform != 'win32'",
    "winloop>=0.1; sys_platform == 'win32'",
]
```

### Uso

```bash
# Installare con un extra
pip install my-package[postgres]

# Installare con piu extras
pip install my-package[postgres,redis]

# Installare tutti gli extras
pip install my-package[all]

# In requirements.txt
my-package[postgres,redis]==1.2.0

# Con uv
uv pip install "my-package[postgres]"
uv add "my-package[postgres]"
```

### Pattern: import condizionale

Nel codice del pacchetto, gestire l'assenza di dipendenze opzionali con import condizionali:

```python
# my_package/backends/postgres.py
from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]

if TYPE_CHECKING:
    import asyncpg as asyncpg_mod

def get_postgres_pool() -> asyncpg_mod.Pool:
    if asyncpg is None:
        raise ImportError(
            "asyncpg non installato. Installa con: pip install my-package[postgres]"
        )
    return asyncpg.create_pool(...)
```

### Pattern: factory basato su extras disponibili

```python
# my_package/cache.py
from importlib.metadata import requires, PackageNotFoundError

def get_cache_backend(preference: str = "auto"):
    """Seleziona il backend cache in base agli extras installati."""
    if preference == "redis" or (preference == "auto" and _is_installed("redis")):
        from my_package.backends.redis_cache import RedisCache
        return RedisCache()
    # Fallback a cache in-memory (sempre disponibile)
    from my_package.backends.memory_cache import MemoryCache
    return MemoryCache()

def _is_installed(package: str) -> bool:
    try:
        __import__(package)
        return True
    except ImportError:
        return False
```

---

## Estensioni C e C++

### Cython

Cython compila codice Python (con annotazioni di tipo opzionali) in C, che viene poi compilato
in un modulo di estensione nativo. E il tool piu maturo per accelerare codice Python
computazionalmente intensivo:

```python
# src/my_package/_fast_ops.pyx (file Cython)
import cython

@cython.boundscheck(False)
@cython.wraparound(False)
def dot_product(double[:] a, double[:] b) -> double:
    """Prodotto scalare ottimizzato con typed memoryview."""
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef double result = 0.0

    if a.shape[0] != b.shape[0]:
        raise ValueError("Vettori di lunghezza diversa")

    for i in range(n):
        result += a[i] * b[i]
    return result
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75.0", "cython>=3.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-fast-package"
version = "1.0.0"

[tool.setuptools]
ext-modules = [
    {name = "my_package._fast_ops", sources = ["src/my_package/_fast_ops.pyx"]}
]
```

Per build complessi con Cython, un `setup.py` minimale resta la soluzione piu flessibile:

```python
# setup.py (solo per configurazione estensioni Cython)
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        "src/my_package/_fast_ops.pyx",
        compiler_directives={
            "boundscheck": False,
            "wraparound": False,
            "language_level": "3",
        },
    ),
)
```

### cffi — C Foreign Function Interface

cffi permette di chiamare funzioni C da Python senza scrivere codice C wrapper. Due modalita:

**ABI mode (runtime, senza compilazione):**

```python
# my_package/ffi.py
from cffi import FFI

ffi = FFI()

# Dichiarazione dell'interfaccia C
ffi.cdef("""
    double sqrt(double x);
    int printf(const char *format, ...);
""")

# Caricamento della libreria
lib = ffi.dlopen("libm.so.6")  # Linux
# lib = ffi.dlopen("libm.dylib")  # macOS

result = lib.sqrt(2.0)
print(f"sqrt(2) = {result}")    # 1.4142135623730951
```

**API mode (compilazione, piu veloce):**

```python
# my_package/_build_ffi.py (eseguito a build time)
from cffi import FFI

ffi = FFI()

ffi.cdef("""
    typedef struct {
        double x;
        double y;
    } Point;

    double distance(Point a, Point b);
""")

ffi.set_source(
    "my_package._geometry",    # nome del modulo generato
    """
    #include <math.h>

    typedef struct {
        double x;
        double y;
    } Point;

    double distance(Point a, Point b) {
        double dx = a.x - b.x;
        double dy = a.y - b.y;
        return sqrt(dx*dx + dy*dy);
    }
    """,
    libraries=["m"],
)

if __name__ == "__main__":
    ffi.compile(verbose=True)
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75.0", "cffi>=1.16", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
cffi-modules = ["src/my_package/_build_ffi.py:ffi"]
```

### pybind11 — binding C++ moderno

pybind11 crea binding Python per codice C++ usando template C++ moderno. E il tool standard
per esporre librerie C++ a Python:

```cpp
// src/cpp/fast_math.cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>

namespace py = pybind11;

double fast_distance(
    py::array_t<double> a,
    py::array_t<double> b
) {
    auto ra = a.unchecked<1>();
    auto rb = b.unchecked<1>();

    if (ra.size() != rb.size()) {
        throw std::runtime_error("Array di lunghezza diversa");
    }

    double sum = 0.0;
    for (py::ssize_t i = 0; i < ra.size(); i++) {
        double diff = ra(i) - rb(i);
        sum += diff * diff;
    }
    return std::sqrt(sum);
}

PYBIND11_MODULE(_fast_math, m) {
    m.doc() = "Operazioni matematiche ottimizzate";
    m.def("fast_distance", &fast_distance,
          "Calcola la distanza euclidea tra due vettori",
          py::arg("a"), py::arg("b"));
}
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=75.0", "pybind11>=2.12", "wheel"]
build-backend = "setuptools.build_meta"
```

```python
# setup.py (per estensioni pybind11)
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "my_package._fast_math",
        ["src/cpp/fast_math.cpp"],
        define_macros=[("VERSION_INFO", "1.0.0")],
        cxx_std=17,
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
```

### Confronto tool per estensioni native

| Tool | Linguaggio sorgente | Complessita setup | Prestazioni | Uso tipico |
|------|---------------------|-------------------|-------------|------------|
| Cython | Python + tipi C | Media | Ottime | Accelerare codice Python esistente |
| cffi | C (interfaccia) | Bassa | Buone | Chiamare librerie C esistenti |
| pybind11 | C++ | Media-alta | Ottime | Binding per librerie C++ |
| maturin/PyO3 | Rust | Media | Eccellenti | Nuove estensioni ad alte prestazioni |
| ctypes (stdlib) | C (interfaccia) | Bassa | Moderate | Chiamate C semplici, nessuna dipendenza |

---

## Estensioni Rust con maturin e PyO3

### Perche Rust per le estensioni Python

L'adozione di Rust nell'ecosistema Python e in forte crescita. Tool critici come ruff (linter),
uv (package manager), pydantic-core (validazione), polars (DataFrame) e cryptography (crittografia)
sono scritti in Rust. I vantaggi:

- **Memory safety senza garbage collector** — nessun segfault, nessun memory leak
- **Prestazioni comparabili al C** — zero-cost abstractions
- **Toolchain moderno** — Cargo, test integrati, documentazione, clippy
- **Cross-compilation semplificata** — maturin gestisce la compilazione per tutte le piattaforme

### Setup progetto Rust + Python

```bash
# Creare un nuovo progetto maturin
pip install maturin
maturin init --bindings pyo3

# Struttura generata:
# my-rust-ext/
# ├── Cargo.toml
# ├── pyproject.toml
# ├── src/
# │   └── lib.rs          # codice Rust
# └── python/
#     └── my_rust_ext/
#         └── __init__.py  # wrapper Python (opzionale)
```

```toml
# Cargo.toml
[package]
name = "my-rust-ext"
version = "0.1.0"
edition = "2021"

[lib]
name = "my_rust_ext"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
```

```toml
# pyproject.toml
[build-system]
requires = ["maturin>=1.7"]
build-backend = "maturin"

[project]
name = "my-rust-ext"
requires-python = ">=3.11"
dynamic = ["version"]

[tool.maturin]
features = ["pyo3/extension-module"]
python-source = "python"
module-name = "my_rust_ext._core"
```

```rust
// src/lib.rs
use pyo3::prelude::*;
use pyo3::types::PyList;

/// Calcola la somma degli elementi di una lista.
#[pyfunction]
fn fast_sum(values: &Bound<'_, PyList>) -> PyResult<f64> {
    let mut total = 0.0;
    for item in values.iter() {
        total += item.extract::<f64>()?;
    }
    Ok(total)
}

/// Ricerca binaria in un vettore ordinato.
#[pyfunction]
fn binary_search(haystack: Vec<i64>, needle: i64) -> Option<usize> {
    haystack.binary_search(&needle).ok()
}

/// Modulo Python.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_sum, m)?)?;
    m.add_function(wrap_pyfunction!(binary_search, m)?)?;
    Ok(())
}
```

```python
# python/my_rust_ext/__init__.py
from my_rust_ext._core import fast_sum, binary_search

__all__ = ["fast_sum", "binary_search"]
```

### Comandi maturin

```bash
# Sviluppo (installa in-place, ricompila ad ogni modifica)
maturin develop --release

# Build wheel per la piattaforma corrente
maturin build --release

# Build per manylinux (dentro container Docker)
maturin build --release --manylinux 2_28

# Pubblicare su PyPI
maturin publish

# Build per piattaforme multiple con zig (cross-compilation)
maturin build --release --target x86_64-unknown-linux-gnu --zig
maturin build --release --target aarch64-unknown-linux-gnu --zig
```

### CI/CD con maturin

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  id-token: write

jobs:
  linux:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        target: [x86_64, aarch64]
    steps:
      - uses: actions/checkout@v4
      - uses: PyO3/maturin-action@v1
        with:
          target: ${{ matrix.target }}
          args: --release --out dist
          manylinux: "2_28"
      - uses: actions/upload-artifact@v4
        with:
          name: wheels-linux-${{ matrix.target }}
          path: dist

  macos:
    runs-on: macos-latest
    strategy:
      matrix:
        target: [x86_64, aarch64]
    steps:
      - uses: actions/checkout@v4
      - uses: PyO3/maturin-action@v1
        with:
          target: ${{ matrix.target }}
          args: --release --out dist
      - uses: actions/upload-artifact@v4
        with:
          name: wheels-macos-${{ matrix.target }}
          path: dist

  windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: PyO3/maturin-action@v1
        with:
          args: --release --out dist
      - uses: actions/upload-artifact@v4
        with:
          name: wheels-windows
          path: dist

  sdist:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: PyO3/maturin-action@v1
        with:
          command: sdist
          args: --out dist
      - uses: actions/upload-artifact@v4
        with:
          name: sdist
          path: dist

  publish:
    needs: [linux, macos, windows, sdist]
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: dist
          merge-multiple: true
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

## Gestione versione avanzata

Il Modulo 23 introduce SemVer, CalVer e setuptools-scm. Qui completiamo con gli altri tool.

### hatch-vcs (Hatch Version Control System)

Plugin per hatchling che legge la versione dai tag git:

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "my-package"
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "src/my_package/_version.py"
```

Il file `_version.py` viene generato automaticamente al build time:

```python
# src/my_package/_version.py (generato automaticamente)
__version__ = version = "1.2.0"
__version_tuple__ = version_tuple = (1, 2, 0)
```

### PDM dynamic versioning

```toml
[project]
name = "my-package"
dynamic = ["version"]

[tool.pdm.version]
source = "scm"
write_to = "my_package/_version.py"
write_template = "__version__ = '{}'\n"
```

### importlib.metadata — leggere la versione a runtime

L'approccio moderno per accedere alla versione a runtime senza duplicarla:

```python
# src/my_package/__init__.py
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("my-package")
except PackageNotFoundError:
    # Pacchetto non installato (es. durante sviluppo senza editable install)
    __version__ = "0.0.0-dev"
```

Questo funziona perche `importlib.metadata.version()` legge il campo `Version` dal file
`METADATA` nel `dist-info` del pacchetto installato — lo stesso valore definito in
`pyproject.toml` o calcolato dal backend.

### Matrice comparativa versioning

| Tool | Backend | Fonte verita | Genera file | Lock su tag |
|------|---------|-------------|-------------|-------------|
| setuptools-scm | setuptools | git tag | Si | Si |
| hatch-vcs | hatchling | git tag | Si | Si |
| pdm-backend scm | pdm-backend | git tag | Si | Si |
| poetry-dynamic-versioning | poetry-core | git tag | Si | Si |
| bump-my-version | qualsiasi | file config | Si (multi-file) | No (bump manuale) |
| python-semantic-release | qualsiasi | commit msg | Si | Si (auto-bump) |

---

## uv — installer e resolver moderno

### Panoramica

uv (di Astral, gli stessi autori di ruff) e un package manager e resolver Python scritto in Rust.
E un ordine di grandezza piu veloce di pip e sostituisce pip, pip-tools, virtualenv e pyenv in un
unico binario:

```bash
# Installazione (standalone, non richiede Python)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Oppure con pip (ma la versione standalone e preferibile)
pip install uv
```

### Comandi fondamentali

```bash
# Gestione Python
uv python install 3.12        # installa Python 3.12 (via python-build-standalone)
uv python list                 # elenca le versioni disponibili
uv python pin 3.12             # fissa la versione nel progetto

# Inizializzazione progetto
uv init my-project             # crea pyproject.toml + struttura base
uv init --lib my-library       # crea una libreria con src layout

# Gestione dipendenze
uv add httpx pydantic          # aggiunge dipendenze e aggiorna uv.lock
uv add --dev pytest ruff       # aggiunge dipendenze dev
uv add "numpy>=2.0"            # con version specifier
uv remove httpx                # rimuove una dipendenza
uv lock                        # rigenera uv.lock senza installare
uv sync                        # installa esattamente le versioni in uv.lock
uv sync --frozen               # installa senza aggiornare il lock file

# Esecuzione
uv run python script.py        # esegue nel venv del progetto
uv run pytest                  # esegue pytest nel venv del progetto
uv run --with httpx script.py  # esegue con dipendenza temporanea

# Build e pubblicazione
uv build                       # genera sdist + wheel
uv build --wheel               # solo wheel
uv publish                     # pubblica su PyPI

# Compatibilita pip
uv pip install httpx            # drop-in replacement di pip install
uv pip compile requirements.in  # equivalente a pip-compile
uv pip sync requirements.txt    # installa esattamente le versioni listate

# Tool globali
uv tool install ruff            # installa tool CLI in ambiente isolato
uv tool run black .             # esegue tool senza installare permanentemente
uvx black .                     # shortcut per uv tool run
```

### uv.lock — formato lockfile

Il lockfile `uv.lock` e un file TOML leggibile che registra la risoluzione completa delle
dipendenze:

```toml
# uv.lock (esempio semplificato)
version = 1
requires-python = ">=3.12"

[[package]]
name = "httpx"
version = "0.27.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "certifi" },
    { name = "httpcore" },
    { name = "idna" },
    { name = "sniffio" },
]
sdist = { url = "...", hash = "sha256:abc123..." }

[[package.wheels]]
url = "..."
hash = "sha256:def456..."

[[package]]
name = "anyio"
version = "4.6.2"
source = { registry = "https://pypi.org/simple" }
# ...
```

Caratteristiche del lockfile:
- **Deterministico** — la stessa risoluzione produce lo stesso file
- **Cross-platform** — contiene le risoluzioni per tutte le piattaforme supportate
- **Verificabile** — hash SHA256 per ogni artefatto
- **Committabile** — va sempre committato nel repository

### uv vs pip vs poetry — confronto pratica

| Operazione | pip | Poetry | uv |
|------------|-----|--------|----|
| Installare dipendenze | `pip install -r requirements.txt` | `poetry install` | `uv sync` |
| Aggiungere dipendenza | (modifica manuale + `pip install`) | `poetry add httpx` | `uv add httpx` |
| Lock file | `pip-compile` (pip-tools) | `poetry lock` | `uv lock` |
| Creare venv | `python -m venv .venv` | automatico | automatico |
| Build | `python -m build` | `poetry build` | `uv build` |
| Pubblicare | `twine upload` | `poetry publish` | `uv publish` |
| Velocita install (cold) | ~30s | ~25s | ~2s |
| Velocita install (cached) | ~10s | ~8s | <1s |
| Resolver | Backtracking (lento) | SAT solver | SAT solver (Rust, molto veloce) |

### Configurazione avanzata uv

```toml
# pyproject.toml
[tool.uv]
# Dipendenze dev (non incluse nel pacchetto pubblicato)
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "mypy>=1.10",
    "ruff>=0.5",
]

# Gruppi di dipendenze
[tool.uv.dependency-groups]
test = ["pytest>=8.0", "pytest-cov>=5.0"]
lint = ["ruff>=0.5", "mypy>=1.10"]
docs = ["sphinx>=7.0", "myst-parser>=3.0"]

# Vincoli globali (applicati a tutte le risoluzioni)
[tool.uv.constraint-dependencies]
numpy = ">=2.0"     # forza numpy 2.0+ ovunque

# Override (forza versioni specifiche, ignora vincoli)
[tool.uv.override-dependencies]
# Utile per fix di sicurezza urgenti
certifi = ">=2024.8.30"

# Sorgenti personalizzate per pacchetti
[tool.uv.sources]
my-internal-lib = { git = "https://github.com/company/my-lib.git", tag = "v1.0.0" }
my-workspace-pkg = { workspace = true }
my-local-dep = { path = "../other-project", editable = true }
```

---

## Risoluzione dipendenze

### Come funziona il resolver di pip

Pip usa un resolver con **backtracking**: prova a trovare un set di versioni compatibili per
tutte le dipendenze. Se incontra un conflitto, torna indietro e prova una versione diversa.

```
Risoluzione di: my-app che dipende da A>=1.0 e B>=2.0
A 1.2 richiede C>=3.0
B 2.1 richiede C<3.0        # CONFLITTO!
Backtrack: prova B 2.0
B 2.0 richiede C>=2.5,<3.5  # compatibile con C>=3.0
Risolto: A==1.2, B==2.0, C==3.4
```

Il backtracking puo essere lento con alberi di dipendenze profondi e vincoli stretti. In casi
patologici, pip puo impiegare minuti per risolvere.

### PubGrub — l'algoritmo moderno di risoluzione

PubGrub e l'algoritmo di risoluzione dipendenze sviluppato originariamente per il package
manager Dart (pub). E stato adottato da **uv** (via `pubgrub-rs`), **Poetry** (via Mixology,
la sua implementazione Python) e altri tool moderni come sostituto del semplice backtracking.

#### Conflict-Driven Clause Learning (CDCL)

A differenza del backtracking semplice di pip, PubGrub usa una tecnica derivata dai SAT solver
chiamata **Conflict-Driven Clause Learning**. Quando incontra un conflitto:

1. **Analizza la causa radice** — non torna semplicemente indietro di un passo, ma identifica
   *perche* il conflitto si e verificato
2. **Genera una clausola di incompatibilita** — un vincolo logico che impedisce di ripetere
   lo stesso errore in futuro
3. **Salta direttamente** alla decisione responsabile — backjumping invece di backtracking

```
Esempio PubGrub vs backtracking:

Dipendenze:
  app richiede A>=1.0, B>=1.0
  A 2.0 richiede C>=3.0
  A 1.0 richiede C>=2.0
  B 2.0 richiede D>=1.0
  B 1.0 richiede D>=1.0
  D 1.0 richiede C<2.5

Backtracking (pip):
  Prova A=2.0, B=2.0, D=1.0 → C>=3.0 AND C<2.5 → conflitto
  Backtrack B=1.0, D=1.0 → C>=3.0 AND C<2.5 → conflitto (stessa causa!)
  Backtrack A=1.0, B=2.0, D=1.0 → C>=2.0 AND C<2.5 → C=2.4 ✓
  Totale: 3 tentativi

PubGrub:
  Prova A=2.0, B=2.0, D=1.0 → C>=3.0 AND C<2.5 → conflitto
  Impara: "se D>=1.0 allora C<2.5, quindi A=2.0 (richiede C>=3.0) e incompatibile con D>=1.0"
  Backjump ad A: prova A=1.0 → C>=2.0 AND C<2.5 → C=2.4 ✓
  Totale: 2 tentativi (skip B=1.0 perche irrilevante)
```

Su grafi di dipendenze reali con centinaia di pacchetti, la differenza tra backtracking e
PubGrub puo essere di ordini di grandezza.

#### Risoluzione universale di uv

uv estende PubGrub con il concetto di **forking resolver**: quando un pacchetto ha dipendenze
diverse per piattaforme diverse (tramite environment marker come `sys_platform` o
`python_version`), uv biforca l'albero di risoluzione e risolve ogni ramo indipendentemente.

Il risultato e un **lockfile universale** (`uv.lock`) valido per tutte le piattaforme:

```toml
# Estratto da uv.lock
[[package]]
name = "my-package"
version = "1.2.0"

[[package.dependencies]]
name = "pywin32"
version = ">=306"
marker = "sys_platform == 'win32'"

[[package.dependencies]]
name = "uvloop"
version = ">=0.19"
marker = "sys_platform != 'win32'"
```

Questo elimina la necessita di generare lockfile separati per Linux, macOS e Windows.

#### Poetry e Mixology

Poetry usa **Mixology**, la propria implementazione di PubGrub in Python. Mixology segue
lo stesso algoritmo CDCL ma ha alcune differenze rispetto all'implementazione Rust di uv:

- **Velocita**: Mixology (Python) e circa 10-100x piu lento di `pubgrub-rs` (Rust) su grafi
  di dipendenze grandi
- **Metadata fetching**: Poetry scarica i metadati uno alla volta; uv li scarica in parallelo
- **Caching**: uv usa una cache globale deduplicata; Poetry ha una cache per progetto

```bash
# Confronto tempi di risoluzione (progetto con ~200 dipendenze):
# pip:    45-120 secondi (backtracking)
# poetry: 15-30 secondi (Mixology/PubGrub in Python)
# uv:     0.5-2 secondi (pubgrub-rs in Rust, fetch parallelo)
```

### Lock file a confronto

| Formato | Tool | Cross-platform | Hash verification | Leggibile |
|---------|------|----------------|-------------------|-----------|
| `requirements.txt` (pinned) | pip-tools, pip freeze | No | Si (`--hash`) | Si |
| `poetry.lock` | Poetry | Si (con marker) | Si | Si (TOML) |
| `uv.lock` | uv | Si | Si | Si (TOML) |
| `pdm.lock` | PDM | Si | Si | Si (TOML) |
| `Pipfile.lock` | pipenv | Si | Si | No (JSON verboso) |

### pip-tools — lock file per pip

pip-tools fornisce `pip-compile` (genera lock file) e `pip-sync` (installa esattamente il lock):

```bash
pip install pip-tools

# requirements.in (dipendenze dirette)
# httpx>=0.27
# pydantic>=2.0
# click>=8.1

# Generare il lock file
pip-compile requirements.in --output-file requirements.txt \
    --generate-hashes \
    --strip-extras \
    --resolver=backtracking

# Il risultato (requirements.txt):
# httpx==0.27.2 \
#     --hash=sha256:abc123...
# pydantic==2.9.0 \
#     --hash=sha256:def456...
# click==8.1.7 \
#     --hash=sha256:ghi789...
# anyio==4.6.2 \
#     --hash=sha256:...
# ... (tutte le dipendenze transitive)

# Installare esattamente le versioni lockate
pip-sync requirements.txt

# Lock file separati per ambienti diversi
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt
```

### Risoluzione conflitti — strategie

```bash
# Diagnosticare conflitti
pip install --dry-run my-package 2>&1 | grep "conflicting"

# Con uv (output piu chiaro)
uv pip install my-package --dry-run

# Forzare la risoluzione (pip)
pip install my-package --force-reinstall

# Mostrare l'albero delle dipendenze
pip install pipdeptree
pipdeptree --packages my-package

# Con uv
uv pip tree
```

---

## Distribuzione containerizzata

Il Modulo 23 presenta il Dockerfile base con multi-stage build. Qui approfondiamo pattern
avanzati.

### Multi-stage con uv

```dockerfile
# syntax=docker/dockerfile:1

# Stage 1: build
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Installare dipendenze prima (cache layer Docker)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copiare sorgenti e installare il progetto
COPY src/ src/
COPY README.md LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Stage 2: runtime (immagine minimale)
FROM python:3.12-slim

WORKDIR /app

# Copiare solo il virtualenv dal builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Utente non-root
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

ENTRYPOINT ["my-tool"]
CMD ["--help"]
```

Punti chiave:
- `UV_COMPILE_BYTECODE=1` — pre-compila i file .py in .pyc (avvio piu rapido)
- `UV_LINK_MODE=copy` — copia i file invece di usare hardlink (necessario per multi-stage)
- `--mount=type=cache` — cache Docker per la directory cache di uv tra build
- Installazione in due step: prima le dipendenze (cambiano raramente), poi i sorgenti (cambiano
  spesso). Questo sfrutta il layer caching di Docker.

### Immagine distroless

Per la massima sicurezza, usare un'immagine distroless (senza shell, senza package manager):

```dockerfile
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
COPY README.md ./
RUN uv sync --frozen --no-dev --no-editable

# Runtime distroless
FROM gcr.io/distroless/python3-debian12

COPY --from=builder /app/.venv/lib/python3.12/site-packages /usr/lib/python3.12/site-packages
COPY --from=builder /app/.venv/bin/my-tool /usr/local/bin/my-tool

ENTRYPOINT ["my-tool"]
```

### .dockerignore per progetti Python

```
# .dockerignore
.git
.github
.venv
__pycache__
*.pyc
*.pyo
.mypy_cache
.pytest_cache
.ruff_cache
dist/
build/
*.egg-info
.env
.env.*
tests/
docs/
*.md
!README.md
```

### Docker per test CI

```dockerfile
# Dockerfile.test
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
RUN uv sync --frozen

CMD ["uv", "run", "pytest", "--cov=my_package", "--cov-report=xml"]
```

---

## Distribuzione binaria

Il Modulo 23 copre in dettaglio PyInstaller, Nuitka, cx_Freeze e Briefcase.
Qui forniamo una matrice decisionale sintetica.

### Matrice comparativa

| Criterio | PyInstaller | Nuitka | cx_Freeze | Briefcase |
|----------|-------------|--------|-----------|-----------|
| Tipo output | Bundle + interprete | Compilato nativo | Bundle + interprete | App nativa |
| Onefile | Si | Si | No | No |
| Prestazioni avvio | Medio (onefile: lento) | Rapido | Medio | Rapido |
| Protezione codice | Bassa (decompilabile) | Alta (C compilato) | Bassa | Media |
| Cross-compilation | No | No | No | No |
| Mobile | No | No | No | Si (iOS/Android) |
| Installer nativo | No (serve NSIS/WiX) | No | No | Si (.dmg, .msi, .deb) |
| Complessita setup | Bassa | Media | Media | Media |
| Maturita | Alta | Media-alta | Media | Media |

### Quando usare quale

- **CLI tool per sviluppatori** -> PyInstaller `--onefile` (semplicita distribuzione)
- **Applicazione server** -> Docker (non serve eseguibile standalone)
- **Desktop GUI** -> Briefcase (installer nativi per ogni piattaforma)
- **Codice proprietario sensibile** -> Nuitka (compilazione nativa, difficile da decompilare)
- **Distribuzione interna** -> wheel + pip install (il modo piu semplice)

---

## Conda packaging

### Panoramica

Conda e un package manager e environment manager indipendente da PyPI. A differenza di pip,
Conda gestisce pacchetti in qualsiasi linguaggio (Python, R, C++, CUDA) e risolve le dipendenze
a livello di sistema, non solo Python. Questo lo rende essenziale per il mondo scientifico dove
le dipendenze includono librerie native complesse (BLAS, LAPACK, CUDA, MKL).

### meta.yaml — la ricetta Conda

La ricetta Conda e un file YAML che descrive come costruire il pacchetto:

```yaml
# conda-recipe/meta.yaml
{% set name = "my-science-tool" %}
{% set version = "1.2.0" %}

package:
  name: {{ name }}
  version: {{ version }}

source:
  url: https://pypi.io/packages/source/m/{{ name }}/{{ name }}-{{ version }}.tar.gz
  sha256: abc123def456...

build:
  number: 0
  noarch: python                   # per pacchetti puri Python
  script: {{ PYTHON }} -m pip install . -vv --no-deps --no-build-isolation
  entry_points:
    - my-tool = my_science_tool.cli:main

requirements:
  host:
    - python >=3.11
    - pip
    - setuptools >=75.0
  run:
    - python >=3.11
    - numpy >=2.0
    - scipy >=1.14
    - matplotlib-base >=3.9

test:
  imports:
    - my_science_tool
    - my_science_tool.analysis
  commands:
    - my-tool --version
  requires:
    - pytest
  source_files:
    - tests/
  commands:
    - pytest tests/ -x

about:
  home: https://github.com/user/my-science-tool
  license: MIT
  license_file: LICENSE
  summary: Strumento per analisi scientifica avanzata
  description: |
    My Science Tool fornisce algoritmi ottimizzati per
    l'analisi di dati spettroscopici e cromatografici.

extra:
  recipe-maintainers:
    - github-username
```

### conda-build

```bash
# Installare conda-build
conda install conda-build

# Costruire il pacchetto
conda build conda-recipe/

# Costruire per piu versioni Python
conda build conda-recipe/ --python 3.11
conda build conda-recipe/ --python 3.12
conda build conda-recipe/ --python 3.13

# Installare il pacchetto compilato localmente
conda install --use-local my-science-tool

# Caricare su Anaconda.org (canale personale)
anaconda upload /path/to/my-science-tool-1.2.0-py312_0.tar.bz2
```

### Contribuire a conda-forge

conda-forge e il repository community piu grande di pacchetti Conda. Contribuire un pacchetto:

1. **Fork e clone del repository staged-recipes:**

```bash
gh repo fork conda-forge/staged-recipes
git clone https://github.com/YOUR_USER/staged-recipes
```

2. **Creare la ricetta:**

```bash
cd staged-recipes
mkdir recipes/my-science-tool
# Creare meta.yaml nella directory
```

3. **Testare localmente:**

```bash
# Con Docker (simulazione dell'ambiente CI conda-forge)
python build-locally.py
```

4. **Aprire una Pull Request** su `conda-forge/staged-recipes`. I bot di conda-forge
   verificano la ricetta, eseguono il build su tutte le piattaforme e, una volta approvata
   e merged, creano un repository dedicato (`conda-forge/my-science-tool-feedstock`).

5. **Manutenzione:** aggiornamenti successivi si fanno con PR al feedstock. I bot conda-forge
   spesso creano PR automatiche quando una nuova versione appare su PyPI.

### conda-forge vs PyPI

| Aspetto | PyPI | conda-forge |
|---------|------|-------------|
| Formato pacchetto | wheel (.whl), sdist (.tar.gz) | conda (.conda, .tar.bz2) |
| Dipendenze native | Solo Python (build da sorgente) | Qualsiasi (C, Fortran, CUDA) |
| Resolver | pip backtracking | conda/mamba SAT solver |
| Ambienti | venv, virtualenv | conda env |
| Governance | PyPA, PSF | conda-forge community |
| Uso principale | Sviluppo web/software | Data science, ML, ricerca |

### Grayskull — generazione automatica ricette

```bash
# Grayskull genera una ricetta conda da un pacchetto PyPI
pip install grayskull

# Generare ricetta
grayskull pypi my-package

# Output: my-package/meta.yaml (da rivedere e adattare)
```

### pixi — il package manager Conda moderno

pixi (sviluppato da prefix.dev) e un package manager compatibile con l'ecosistema Conda
scritto in Rust. Risolve le principali limitazioni dell'esperienza utente classica di conda:

```bash
# Installare pixi
curl -fsSL https://pixi.sh/install.sh | bash

# Inizializzare un progetto
pixi init my-science-project
cd my-science-project

# Aggiungere dipendenze (conda-forge + PyPI)
pixi add numpy scipy matplotlib
pixi add --pypi pandas-stubs     # pacchetti PyPI via --pypi

# Eseguire comandi nell'ambiente
pixi run python train.py

# Definire task riutilizzabili
pixi task add train "python train.py --epochs 50"
pixi run train
```

Il file di progetto e `pixi.toml` (o la sezione `[tool.pixi]` in `pyproject.toml`):

```toml
# pixi.toml
[project]
name = "my-science-project"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[dependencies]
python = ">=3.11"
numpy = ">=2.0"
scipy = ">=1.14"
cuda-toolkit = { version = ">=12.0", platform = "linux-64" }

[pypi-dependencies]
my-internal-lib = { path = "../my-lib", editable = true }

[feature.test.dependencies]
pytest = ">=8.0"

[environments]
test = ["test"]

[tasks]
train = "python train.py"
test = "pytest tests/ -v"
```

Vantaggi di pixi rispetto a conda/mamba:

| Aspetto | conda/mamba | pixi |
|---------|-------------|------|
| Velocita risoluzione | 5-30 secondi | 0.5-3 secondi |
| Lockfile nativo | No (serve conda-lock) | Si (`pixi.lock`) |
| Task runner | No | Si |
| Multi-piattaforma | Manuale | Dichiarativo |
| Dipendenze PyPI | No (solo canali conda) | Si (via `--pypi`) |
| Attivazione globale | `conda activate env` | `pixi run <cmd>` (implicita) |

### conda-lock — lockfile riproducibili per Conda

conda-lock genera lockfile cross-platform per ambienti Conda, garantendo riproducibilita
completa. E utile quando si usa conda/mamba direttamente (pixi ha il lockfile integrato).

```bash
# Installare conda-lock
pip install conda-lock
# oppure
conda install -c conda-forge conda-lock

# Generare lockfile da environment.yml
conda-lock lock --file environment.yml \
    --platform linux-64 --platform osx-arm64

# Output: conda-lock.yml (formato unificato per tutte le piattaforme)

# Installare da lockfile
conda-lock install conda-lock.yml

# Generare lockfile con supporto pip (dipendenze miste)
conda-lock lock --file environment.yml --pip-support
```

File sorgente per conda-lock:

```yaml
# environment.yml
name: research-env
channels:
  - conda-forge
dependencies:
  - python >=3.11
  - numpy >=2.0
  - scipy >=1.14
  - pytorch >=2.4
  - cuda-toolkit >=12.0    # solo per linux-64
  - pip:
      - transformers >=4.40  # pacchetto PyPI
      - wandb
```

```bash
# Aggiornare singoli pacchetti mantenendo il lock
conda-lock lock --update numpy

# Verificare che il lockfile sia aggiornato
conda-lock check --file environment.yml
```

---

## Troubleshooting

### 1. ModuleNotFoundError dopo pip install

**Sintomo:** `pip install my-package` ha successo, ma `import my_package` fallisce.

**Cause possibili:**
- Il pacchetto e installato in un ambiente virtuale diverso da quello in uso
- Il nome del pacchetto su PyPI (`my-package`) e diverso dal nome del modulo (`my_package`)
- File `__init__.py` mancante in una sotto-directory
- src layout senza `[tool.setuptools.packages.find] where = ["src"]`

**Diagnosi:**

```bash
# Verificare dove e installato
pip show my-package
python -c "import my_package; print(my_package.__file__)"
which python    # confermare l'interprete attivo
```

### 2. Il wheel non include file dati

**Sintomo:** il pacchetto installato non trova file JSON, YAML, template o altri dati.

**Fix per setuptools:**

```toml
[tool.setuptools.package-data]
my_package = ["data/*.json", "templates/**/*.html"]
```

**Fix per hatchling:**

```toml
[tool.hatch.build.targets.wheel.force-include]
"data/config.json" = "my_package/data/config.json"
```

**Verifica:** ispezionare il contenuto del wheel:

```bash
python -m zipfile -l dist/my_package-1.0.0-py3-none-any.whl
```

### 3. Version mismatch tra pyproject.toml e __version__

**Sintomo:** `my_package.__version__` mostra un valore diverso da quello in `pyproject.toml`.

**Fix:** usare `importlib.metadata.version()` come singola fonte di verita (vedi sezione
Gestione versione avanzata).

### 4. Build fallisce con "No module named setuptools"

**Sintomo:** `python -m build` fallisce perche setuptools non e trovato.

**Causa:** manca la sezione `[build-system]` in `pyproject.toml`, oppure e malformata.

**Fix:** assicurarsi che `pyproject.toml` contenga:

```toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"
```

### 5. "Multiple top-level packages discovered" con setuptools

**Sintomo:** setuptools trova pacchetti inattesi (es. `tests`, `docs`, `examples`).

**Fix:**

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["my_package*"]
exclude = ["tests*", "docs*"]
```

### 6. Editable install non riflette le modifiche

**Sintomo:** dopo `pip install -e .`, le modifiche al codice non sono visibili.

**Cause:**
- Cache bytecode: eliminare `__pycache__` e file `.pyc`
- Import da site-packages invece che dai sorgenti (src layout senza editable install)
- Backend non supporta PEP 660

**Fix:**

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
pip install -e . --force-reinstall --no-deps
```

### 7. auditwheel repair fallisce

**Sintomo:** `auditwheel repair` non riesce a riparare il wheel.

**Cause comuni:**
- Libreria non trovata (`cannot find library`)
- Libreria troppo recente per il tag manylinux target
- Libreria esclusa dalla blacklist di auditwheel (es. `libpython`)

**Fix:**

```bash
# Verificare le dipendenze del .so
ldd dist/*.so

# Installare la libreria mancante nel container di build
# oppure usare un tag manylinux piu recente
auditwheel repair --plat manylinux_2_35_x86_64 dist/*.whl
```

### 8. Conflitto di dipendenze con extra-index-url

**Sintomo:** pip installa un pacchetto da PyPI invece che dal registro privato.

**Fix:** usare `--index-url` (sostituisce PyPI) invece di `--extra-index-url` (aggiunge).
Vedi sezione Sicurezza dei registri privati.

### 9. "Invalid distribution" o "File already exists" su PyPI

**Sintomo:** twine upload fallisce con errore 400.

**Cause:**
- La versione esiste gia su PyPI (non si puo sovrascrivere)
- Metadati malformati

**Fix:**

```bash
# Verificare i metadati
twine check dist/*

# Incrementare la versione prima di ripubblicare
# PyPI NON permette il re-upload della stessa versione
```

### 10. Cython: "numpy/arrayobject.h not found"

**Sintomo:** la compilazione Cython fallisce cercando header NumPy.

**Fix:**

```toml
[build-system]
requires = ["setuptools>=75.0", "cython>=3.0", "numpy>=2.0", "wheel"]
build-backend = "setuptools.build_meta"
```

E nel codice Cython, importare correttamente:

```python
# setup.py
import numpy as np
from Cython.Build import cythonize
from setuptools import setup, Extension

extensions = [
    Extension(
        "my_package._fast",
        ["src/my_package/_fast.pyx"],
        include_dirs=[np.get_include()],
    )
]

setup(ext_modules=cythonize(extensions))
```

### 11. poetry.lock e uv.lock in conflitto

**Sintomo:** il progetto ha sia `poetry.lock` che `uv.lock`, e le versioni divergono.

**Fix:** scegliere un tool e eliminare l'altro lock file. Se si migra da Poetry a uv:

```bash
# Verificare che pyproject.toml usi [project] (PEP 621)
# Se usa [tool.poetry], migrare prima i metadati

# Generare il lock file uv
uv lock

# Verificare che l'installazione funzioni
uv sync
uv run pytest

# Rimuovere poetry.lock
rm poetry.lock
```

### 12. "Unsupported platform tag" nell'installazione wheel

**Sintomo:** pip rifiuta di installare un wheel perche il platform tag non corrisponde.

**Fix:**

```bash
# Verificare il platform tag del wheel
python -c "import packaging.tags; print(list(packaging.tags.sys_tags())[:5])"

# Se serve forzare (non raccomandato per produzione):
pip install my_package.whl --force-reinstall --no-deps
```

### 13. uv sync fallisce con "No solution found"

**Sintomo:** uv non riesce a risolvere le dipendenze.

**Diagnosi:**

```bash
# Visualizzare il conflitto dettagliato
uv lock --verbose

# Provare con vincoli rilassati
uv lock --resolution lowest
```

### 14. Il pacchetto non trova le risorse dopo PyInstaller

**Sintomo:** `FileNotFoundError` per file dati quando eseguito come binario PyInstaller.

**Fix:** usare `sys._MEIPASS` per i percorsi (vedi Modulo 23, sezione PyInstaller).
In alternativa, usare `importlib.resources` (piu moderno):

```python
from importlib.resources import files

# Leggere un file dati incluso nel pacchetto
config_text = files("my_package.data").joinpath("config.json").read_text()
```

### 15. conda install e pip install: conflitto

**Sintomo:** l'ambiente Conda si corrompe dopo aver usato pip install.

**Best practice:**

```bash
# Installare via conda prima, pip solo per cio che non esiste su conda
conda install numpy scipy matplotlib
pip install my-niche-package     # solo se non su conda-forge

# MAI: conda install X dopo pip install X (sovrascritture parziali)
```

### 16. Build cache corrotta

**Sintomo:** il build produce risultati inconsistenti o errori inspiegabili.

**Fix:**

```bash
# Pulire tutte le cache
rm -rf build/ dist/ *.egg-info src/*.egg-info
find . -type d -name __pycache__ -exec rm -rf {} +
pip cache purge
uv cache clean    # se si usa uv
```

---

## FAQ

### 1. Devo ancora scrivere un setup.py?

No, per la stragrande maggioranza dei progetti. `pyproject.toml` con PEP 621 e sufficiente.
L'unico caso in cui setup.py resta necessario e per estensioni C/C++ con logica di build
complessa che richiede `cmdclass` personalizzate o chiamate a `cythonize()`. Anche in quel caso,
il setup.py puo essere minimale (solo le estensioni) con i metadati in `pyproject.toml`.

### 2. Poetry o uv?

Per progetti nuovi nel 2025/2026, uv e la scelta raccomandata: e piu veloce, aderisce
completamente agli standard PEP, supporta workspace, e il lock file e cross-platform. Poetry
resta valido per progetti esistenti che lo usano gia, ma la tendenza dell'ecosistema e verso uv.

### 3. Devo pubblicare sia wheel che sdist?

Si, sempre. Il wheel garantisce installazione rapida; la sdist serve come fallback per
piattaforme senza wheel pre-compilato e per audit di sicurezza. `python -m build` e
`uv build` producono entrambi per default.

### 4. Come gestisco dipendenze con estensioni native (numpy, scipy)?

Per librerie Python pure che dipendono da numpy: dichiarare `numpy>=2.0` nelle dipendenze.
Pip/uv installano il wheel pre-compilato. Per estensioni proprie che linkano contro numpy
a build time: aggiungere numpy in `[build-system] requires` e usare l'ABI stabile se possibile.

### 5. Cos'e il Trusted Publisher e perche dovrei usarlo?

Trusted Publisher e il meccanismo OIDC di PyPI che elimina API token statici. Configuri su PyPI
quale repository GitHub e workflow sono autorizzati a pubblicare, e GitHub Actions ottiene un
token temporaneo ad ogni esecuzione. Vantaggi: nessun token da gestire, nessun rischio di leak,
audit trail completo. E il metodo raccomandato da PyPI.

### 6. Come faccio a testare il pacchetto prima di pubblicare su PyPI?

```bash
# 1. Build
uv build    # oppure python -m build

# 2. Verificare i metadati
twine check dist/*

# 3. Testare in ambiente pulito
python -m venv /tmp/test-env
/tmp/test-env/bin/pip install dist/*.whl
/tmp/test-env/bin/python -c "import my_package; print(my_package.__version__)"

# 4. Pubblicare su TestPyPI
twine upload --repository testpypi dist/*

# 5. Testare da TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    my-package
```

### 7. Quando usare namespace packages?

Quando piu distribuzioni indipendenti devono condividere un prefisso di pacchetto comune
(es. `company.auth`, `company.logging`). Non usarli per un singolo progetto con sotto-pacchetti
— in quel caso un pacchetto normale con `__init__.py` e la scelta corretta.

### 8. Qual e la differenza tra `--index-url` e `--extra-index-url`?

`--index-url` **sostituisce** PyPI: pip cerca solo nell'indice specificato.
`--extra-index-url` **aggiunge** un indice: pip cerca sia su PyPI che sull'indice aggiuntivo.
`--extra-index-url` e vulnerabile a dependency confusion attack (vedi sezione Registri privati).

### 9. Come faccio a distribuire un pacchetto con estensioni C per tutte le piattaforme?

Usare cibuildwheel in CI. Cibuildwheel compila wheel per ogni combinazione piattaforma/architettura
/versione Python in ambienti isolati (Docker per Linux, macchine native per macOS e Windows).
Vedere la sezione cibuildwheel per la configurazione completa.

### 10. Posso usare conda e pip insieme?

Si, ma con cautela. Regola: installare prima tutto il possibile via conda, poi usare pip solo
per pacchetti non disponibili su conda-forge. Non mescolare mai: non fare `conda install X`
dopo `pip install X` per lo stesso pacchetto. Considerare `conda-lock` per lock file riproducibili
in ambienti Conda.

### 11. Come migro da setup.py a pyproject.toml?

```bash
# 1. Installare ini2toml per la conversione automatica
pip install ini2toml[full]

# 2. Convertire (se si ha setup.cfg)
ini2toml --output-file pyproject.toml setup.cfg

# 3. Per setup.py: analizzare manualmente i campi e mapparli a [project]
# Non esiste un convertitore automatico affidabile per setup.py arbitrario

# 4. Verificare
python -m build
twine check dist/*

# 5. Rimuovere i file legacy
rm setup.py setup.cfg MANIFEST.in  # solo dopo verifica
```

### 12. Come gestisco i monorepo con pacchetti interdipendenti?

Usare uv workspaces (raccomandato 2025/2026): un `pyproject.toml` root con
`[tool.uv.workspace]`, un `pyproject.toml` per ogni pacchetto, e `[tool.uv.sources]` per le
dipendenze interne. Vedere la sezione Monorepo packaging.

### 13. Qual e la differenza tra `requires-python` e le dipendenze Python?

`requires-python = ">=3.11"` e una dichiarazione del pacchetto: "questo pacchetto funziona
solo con Python 3.11+". Pip rifiuta l'installazione su Python 3.10. Non e una dipendenza
installabile — e un filtro.

### 14. Come uso uv in Docker?

Copiare il binario uv dall'immagine ufficiale e usarlo per installare le dipendenze.
Pattern raccomandato con layer caching:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable
```

Vedere la sezione Distribuzione containerizzata per il Dockerfile completo.

### 15. Il mio pacchetto funziona in locale ma non dopo pip install. Perche?

Le cause piu comuni:
1. **File dati non inclusi** — verificare `[tool.setuptools.package-data]` o equivalente
2. **Import relativo errato** — usare import assoluti (`from my_package.utils import X`)
3. **Dipendenza non dichiarata** — il pacchetto funziona perche la dipendenza e installata
   nell'ambiente di sviluppo ma non e dichiarata in `[project] dependencies`
4. **src layout senza configurazione** — manca `where = ["src"]` nella configurazione di
   discovery dei pacchetti

Testare sempre in un ambiente virtuale pulito prima di pubblicare.

### 16. Come faccio a creare un plugin per un'applicazione che usa entry points?

Creare un pacchetto separato con un entry point nel gruppo corretto:

```toml
[project.entry-points."app_name.plugins"]
my_plugin = "my_plugin_package:MyPlugin"
```

L'applicazione host scopre il plugin automaticamente via `importlib.metadata.entry_points()`.
Vedere la sezione Entry points e sistemi a plugin.

---

## Step-by-step — pubblicare il primo pacchetto su PyPI

Questa guida pratica copre l'intero processo dalla creazione del progetto alla pubblicazione.

### Step 1: creare la struttura del progetto

```bash
mkdir my-first-package && cd my-first-package

# Oppure con uv (crea pyproject.toml + struttura automaticamente)
uv init --lib my-first-package
cd my-first-package
```

Struttura target:

```
my-first-package/
├── src/
│   └── my_first_package/
│       ├── __init__.py
│       ├── core.py
│       └── py.typed
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── pyproject.toml
├── README.md
└── LICENSE
```

### Step 2: scrivere pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-first-package"
version = "0.1.0"
description = "Il mio primo pacchetto Python"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    {name = "Il Tuo Nome", email = "tu@example.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "License :: OSI Approved :: MIT License",
    "Typing :: Typed",
]
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5"]

[project.urls]
Repository = "https://github.com/tuo-user/my-first-package"

[tool.hatch.build.targets.wheel]
packages = ["src/my_first_package"]
```

### Step 3: scrivere il codice

```python
# src/my_first_package/__init__.py
"""My First Package — una libreria di esempio."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("my-first-package")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from my_first_package.core import greet

__all__ = ["greet", "__version__"]
```

```python
# src/my_first_package/core.py
"""Funzionalita principali."""


def greet(name: str) -> str:
    """Genera un saluto personalizzato.

    Args:
        name: Il nome della persona da salutare.

    Returns:
        Una stringa di saluto.

    Raises:
        ValueError: Se il nome e vuoto.
    """
    if not name or not name.strip():
        raise ValueError("Il nome non puo essere vuoto")
    return f"Ciao, {name.strip()}!"
```

```python
# src/my_first_package/py.typed
# File vuoto — segnala che il pacchetto include type hints
```

### Step 4: scrivere i test

```python
# tests/test_core.py
import pytest
from my_first_package import greet


def test_greet_valid_name():
    assert greet("Mario") == "Ciao, Mario!"


def test_greet_strips_whitespace():
    assert greet("  Mario  ") == "Ciao, Mario!"


def test_greet_empty_name_raises():
    with pytest.raises(ValueError, match="vuoto"):
        greet("")


def test_greet_whitespace_only_raises():
    with pytest.raises(ValueError, match="vuoto"):
        greet("   ")
```

### Step 5: build e verifica locale

```bash
# Installare le dipendenze di sviluppo
uv sync    # oppure pip install -e ".[dev]"

# Eseguire i test
uv run pytest tests/ -v    # oppure pytest tests/ -v

# Build del pacchetto
uv build    # oppure python -m build

# Verificare il pacchetto
pip install twine
twine check dist/*

# Testare in ambiente pulito
python -m venv /tmp/test-install
/tmp/test-install/bin/pip install dist/my_first_package-0.1.0-py3-none-any.whl
/tmp/test-install/bin/python -c "from my_first_package import greet; print(greet('Mondo'))"
# Output: Ciao, Mondo!
```

### Step 6: pubblicare su TestPyPI

```bash
# Creare account su test.pypi.org (se non ne hai uno)

# Caricare su TestPyPI
twine upload --repository testpypi dist/*
# Inserire username (__token__) e password (il token API)

# Verificare l'installazione da TestPyPI
pip install --index-url https://test.pypi.org/simple/ my-first-package
python -c "from my_first_package import greet; print(greet('TestPyPI'))"
```

### Step 7: pubblicare su PyPI

```bash
# Dopo aver verificato su TestPyPI
twine upload dist/*
# Inserire username (__token__) e password (il token API)

# Verificare l'installazione da PyPI
pip install my-first-package
python -c "from my_first_package import greet; print(greet('PyPI'))"
```

### Step 8: configurare Trusted Publisher (opzionale ma raccomandato)

1. Su pypi.org: Your Projects -> my-first-package -> Manage -> Publishing
2. "Add a new publisher": GitHub repository owner, repository name, workflow name, environment
3. Creare il workflow GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish

on:
  push:
    tags: ["v*"]

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

4. Per pubblicare una nuova versione:

```bash
# Aggiornare la versione in pyproject.toml
# Commit e tag
git add -A && git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push && git push --tags
# Il workflow si attiva automaticamente e pubblica su PyPI
```

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **abi3** | Stable ABI di Python (PEP 384). Un wheel abi3 funziona su tutte le versioni CPython >= quella minima specificata. |
| **abi3audit** | Tool che verifica che un wheel abi3 non usi simboli fuori dalla Limited API. |
| **ABI tag** | Etichetta nel nome del wheel che identifica la versione dell'Application Binary Interface di Python (es. `cp312`). |
| **attestazione digitale** | Documento firmato crittograficamente (PEP 740) che lega un artefatto PyPI alla CI che lo ha prodotto. |
| **auditwheel** | Tool che analizza e ripara wheel Linux per conformita manylinux. |
| **backend di build** | Modulo Python che implementa l'interfaccia PEP 517 (`build_wheel`, `build_sdist`). |
| **CalVer** | Schema di versioning basato sulla data (es. `2025.1.0`). |
| **CDCL** | Conflict-Driven Clause Learning — tecnica SAT solver usata da PubGrub per risolvere dipendenze. |
| **cibuildwheel** | Tool per compilare wheel platform-specific in CI per tutte le piattaforme. |
| **conda-forge** | Repository community di pacchetti Conda con build automatizzati. |
| **conda-lock** | Tool per generare lockfile riproducibili cross-platform per ambienti Conda. |
| **Cython** | Compilatore che traduce Python con annotazioni di tipo in codice C. |
| **delocate** | Equivalente macOS di auditwheel per la riparazione delle dipendenze native. |
| **dependency confusion** | Attacco dove un pacchetto malevolo su PyPI ha lo stesso nome di uno privato. |
| **devpi** | Server PyPI self-hosted con proxy cache, indici privati e staging area. |
| **dist-info** | Directory in `site-packages` contenente metadati del pacchetto installato. |
| **editable install** | Installazione (`pip install -e .`) che reindirizza le importazioni ai sorgenti del progetto. |
| **entry point** | Metadato registrato nel dist-info che associa un nome a una funzione Python. |
| **extras** | Gruppi di dipendenze opzionali installabili con `pip install pkg[extra]`. |
| **frontend di build** | Tool (pip, build, uv) che invoca il backend per costruire pacchetti. |
| **Limited API** | Sottoinsieme dell'API C di Python garantito stabile attraverso le versioni (PEP 384). |
| **lock file** | File che registra le versioni esatte di tutte le dipendenze risolte. |
| **manylinux** | Standard per wheel Linux portabili, basato su requisiti minimi di glibc. |
| **maturin** | Build backend per pacchetti Python con estensioni Rust (PyO3). |
| **meta.yaml** | File ricetta per la costruzione di pacchetti Conda. |
| **musllinux** | Standard per wheel Linux su distribuzioni musl libc (Alpine). |
| **namespace package** | Pacchetto senza `__init__.py` che puo essere distribuito su piu pacchetti. |
| **OIDC** | OpenID Connect — protocollo di autenticazione usato da Trusted Publishers. |
| **PEP 384** | Definisce la Limited/Stable ABI per estensioni C Python. |
| **PEP 517** | Specifica l'interfaccia standard tra frontend e backend di build. |
| **PEP 518** | Specifica la dichiarazione delle dipendenze di build in `pyproject.toml`. |
| **PEP 621** | Standardizza la tabella `[project]` in `pyproject.toml`. |
| **PEP 639** | Introduce identificatori SPDX per le licenze in `pyproject.toml`. |
| **PEP 660** | Standardizza le installazioni editable tramite hook `build_editable`. |
| **PEP 740** | Introduce attestazioni digitali per artefatti PyPI tramite Sigstore. |
| **PEP 803** | Propone abi3t — Stable ABI per il free-threaded Python (no GIL). |
| **pixi** | Package manager Conda moderno scritto in Rust con lockfile nativo e task runner. |
| **platform tag** | Etichetta nel nome del wheel che identifica OS e architettura. |
| **PubGrub** | Algoritmo di risoluzione dipendenze basato su CDCL, usato da uv e Poetry. |
| **pybind11** | Libreria C++ header-only per creare binding Python per codice C++. |
| **PyO3** | Libreria Rust per creare estensioni Python native. |
| **Rekor** | Transparency log pubblico di Sigstore che registra tutte le firme crittografiche. |
| **SAT solver** | Algoritmo di soddisfacibilita booleana usato per risolvere dipendenze. |
| **sdist** | Source distribution — archivio dei sorgenti che richiede build per l'installazione. |
| **SemVer** | Semantic Versioning — schema MAJOR.MINOR.PATCH. |
| **setuptools-scm** | Plugin che deriva la versione del pacchetto dai tag git. |
| **Sigstore** | Infrastruttura di firma keyless usata da PEP 740 per attestazioni PyPI. |
| **Trusted Publisher** | Meccanismo OIDC di PyPI per pubblicazione senza token statici. |
| **universal2** | Wheel macOS con codice nativo per arm64 e x86_64 in un unico fat binary. |
| **uv** | Package manager Python scritto in Rust (Astral). Sostituisce pip, pip-tools, virtualenv. |
| **wheel** | Formato di distribuzione binaria Python (archivio ZIP con estensione `.whl`). |
| **workspace** | Configurazione monorepo dove piu pacchetti condividono lock file e risoluzione. |

---

## Letture consigliate

- Python Packaging User Guide. https://packaging.python.org/
- PyPI Trusted Publishers. https://docs.pypi.org/trusted-publishers/
- uv Documentation. https://docs.astral.sh/uv/
- Hatch Documentation. https://hatch.pypa.dev/
- PDM Documentation. https://pdm-project.org/
- maturin Documentation. https://www.maturin.rs/
- cibuildwheel Documentation. https://cibuildwheel.pypa.io/
- PyO3 User Guide. https://pyo3.rs/
- pybind11 Documentation. https://pybind11.readthedocs.io/
- Cython Documentation. https://cython.readthedocs.io/
- conda-forge Documentation. https://conda-forge.org/docs/
- pixi Documentation. https://pixi.sh/latest/
- conda-lock Documentation. https://conda.github.io/conda-lock/
- devpi Documentation. https://devpi.net/docs/devpi/devpi/stable/
- Sigstore — Python client. https://github.com/sigstore/sigstore-python
- pypi-attestations. https://github.com/trailofbits/pypi-attestations
- PubGrub — version solving algorithm. https://github.com/dart-lang/pub/blob/master/doc/solver.md
- abi3audit. https://github.com/trailofbits/abi3audit
- PEP 384 — Defining a Stable ABI. https://peps.python.org/pep-0384/
- PEP 517. https://peps.python.org/pep-0517/
- PEP 518. https://peps.python.org/pep-0518/
- PEP 621. https://peps.python.org/pep-0621/
- PEP 660. https://peps.python.org/pep-0660/
- PEP 639. https://peps.python.org/pep-0639/
- PEP 740 — Index support for digital attestations. https://peps.python.org/pep-0740/
- PEP 803 — abi3 for free-threaded CPython. https://peps.python.org/pep-0803/
