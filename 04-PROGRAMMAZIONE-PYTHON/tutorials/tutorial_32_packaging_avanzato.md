# Tutorial 32 — Packaging Avanzato: Plugin, Namespace, Estensioni Rust/C

> **Companion a:** `32-packaging-avanzato.md`
> **Scope:** plugin systems, namespace packages, maturin (Rust), Cython, setuptools extensions
> **Prerequisiti:** `tutorial_23_packaging.md`, `tutorial_25_performance.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Packaging Avanzato
│
├── Plugin System
│   ├── Entry Points — registrazione plug-in
│   ├── importlib.metadata — discover plugin
│   └── Plugin con ABC/Protocol
│
├── Namespace Packages (PEP 420)
│   ├── organizzazione.componente.x
│   └── Più pacchetti nello stesso namespace
│
├── Estensioni native
│   ├── Cython — Python → C
│   │   ├── .pyx files
│   │   └── Type annotations per speed
│   ├── maturin — Python + Rust (PyO3)
│   │   ├── Libreria sicura, zero-cost
│   │   └── Tipi condivisi
│   └── cffi / ctypes — bind C libraries
│
├── Build avanzato
│   ├── Build hooks — pre/post build
│   ├── Wheel tags — platform-specific
│   └── cibuildwheel — build su GitHub Actions
│
└── Distribuzione avanzata
    ├── PyPI Trusted Publisher
    ├── Private index (devpi, Artifactory)
    └── Conda packages
```

---

# Parte A — Plugin System con Entry Points

---

## A1. Registrazione e discovery plugin

```toml
# Plugin principale: mio-framework

# pyproject.toml del framework
[project]
name = "mio-framework"
version = "1.0.0"

# pyproject.toml del plugin (pacchetto separato)
[project]
name = "mio-framework-plugin-csv"
version = "0.1.0"
dependencies = ["mio-framework>=1.0"]

[project.entry-points."mio_framework.processori"]
csv = "mio_framework_csv:ProcessatoreCSV"
excel = "mio_framework_csv:ProcessatoreExcel"
```

```python
# Framework: scopre plugin dinamicamente
from importlib.metadata import entry_points
from typing import Protocol

class Processore(Protocol):
    def processa(self, dati: bytes) -> dict: ...

def carica_processori() -> dict[str, type]:
    """Scopre tutti i plugin registrati come entry points."""
    processori: dict[str, type] = {}
    eps = entry_points(group="mio_framework.processori")
    for ep in eps:
        try:
            cls = ep.load()
            processori[ep.name] = cls
            print(f"Plugin caricato: {ep.name} da {ep.value}")
        except Exception as e:
            print(f"Errore caricamento plugin {ep.name}: {e}")
    return processori

def ottieni_processore(nome: str) -> Processore:
    processori = carica_processori()
    if nome not in processori:
        disponibili = list(processori.keys())
        raise ValueError(f"Processore '{nome}' non trovato. Disponibili: {disponibili}")
    return processori[nome]()

# Plugin: implementa il contratto
class ProcessatoreCSV:
    def processa(self, dati: bytes) -> dict:
        import csv, io
        reader = csv.DictReader(io.StringIO(dati.decode("utf-8")))
        return {"righe": list(reader)}

# Test
# pip install mio-framework mio-framework-plugin-csv
# proc = ottieni_processore("csv")
# risultato = proc.processa(b"a,b\n1,2")
```

---

# Parte B — Estensioni Rust con maturin

---

## B1. Modulo Python scritto in Rust

```bash
# Prerequisiti: Rust installato (https://rustup.rs/)
pip install maturin

# Crea progetto maturin
maturin new --bindings pyo3 mio_modulo_rust
cd mio_modulo_rust
# Struttura:
# Cargo.toml
# src/
#   lib.rs
# pyproject.toml
```

```toml
# Cargo.toml
[package]
name = "mio_modulo_rust"
version = "0.1.0"
edition = "2021"

[lib]
name = "mio_modulo_rust"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.21", features = ["extension-module"] }
rayon = "1.10"   # parallelismo in Rust
```

```rust
// src/lib.rs
use pyo3::prelude::*;
use rayon::prelude::*;

/// Somma i quadrati di una lista di numeri — parallelizzata in Rust
#[pyfunction]
fn somma_quadrati(numeri: Vec<f64>) -> f64 {
    numeri.par_iter().map(|x| x * x).sum()
}

/// Conta le occorrenze di ogni parola in un testo
#[pyfunction]
fn conta_parole(testo: &str) -> std::collections::HashMap<String, usize> {
    let mut conteggio = std::collections::HashMap::new();
    for parola in testo.split_whitespace() {
        *conteggio.entry(parola.to_lowercase()).or_insert(0) += 1;
    }
    conteggio
}

/// Classe Python implementata in Rust
#[pyclass]
struct ContatoreSicuro {
    #[pyo3(get)]
    valore: i64,
}

#[pymethods]
impl ContatoreSicuro {
    #[new]
    fn new() -> Self {
        Self { valore: 0 }
    }

    fn incrementa(&mut self) {
        self.valore += 1;
    }

    fn resetta(&mut self) {
        self.valore = 0;
    }
}

/// Modulo Python
#[pymodule]
fn mio_modulo_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(somma_quadrati, m)?)?;
    m.add_function(wrap_pyfunction!(conta_parole, m)?)?;
    m.add_class::<ContatoreSicuro>()?;
    Ok(())
}
```

```bash
# Build per sviluppo
maturin develop

# Build wheel per distribuzione
maturin build --release

# Con GitHub Actions (cibuildwheel):
# Build su linux/mac/windows, arm64/amd64 automaticamente
```

```python
# Uso in Python
import mio_modulo_rust as mru
import numpy as np

dati = np.random.random(10_000_000).tolist()
risultato = mru.somma_quadrati(dati)   # ~10x più veloce del loop Python

parole = mru.conta_parole("il gatto di mario il gatto è bello mario ama il gatto")
print(parole)   # {"il": 3, "gatto": 3, "mario": 2, ...}

c = mru.ContatoreSicuro()
c.incrementa()
c.incrementa()
print(c.valore)   # 2
```

---

# Parte C — Cython

---

## C1. File .pyx e setup

```python
# calcoli.pyx — Cython source
# cython: language_level=3, boundscheck=False, wraparound=False

cimport cython
import numpy as np
cimport numpy as np

# Funzione tipizzata — molto più veloce
def somma_quadrati_cy(double[:] arr) -> double:
    """Somma i quadrati con tipi C — ~50x più veloce del Python puro."""
    cdef:
        Py_ssize_t i, n = arr.shape[0]
        double totale = 0.0

    for i in range(n):
        totale += arr[i] * arr[i]

    return totale

# Classe Cython
cdef class VettoreVeloce:
    cdef double[:] _dati
    cdef readonly Py_ssize_t dimensione

    def __init__(self, dimensione: int):
        import numpy as np
        self._dati = np.zeros(dimensione, dtype=np.float64)
        self.dimensione = dimensione

    def imposta(self, i: int, v: float) -> None:
        self._dati[i] = v

    def ottieni(self, i: int) -> float:
        return self._dati[i]

    def norma(self) -> float:
        cdef double s = 0.0
        cdef Py_ssize_t i
        for i in range(self.dimensione):
            s += self._dati[i] ** 2
        return s ** 0.5
```

```python
# setup.py per Cython (usato con hatchling o maturin)
from setuptools import setup
from Cython.Build import cythonize
import numpy as np

setup(
    ext_modules=cythonize(
        "calcoli.pyx",
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "initializedcheck": False,
        },
    ),
    include_dirs=[np.get_include()],
)

# Build:
# python setup.py build_ext --inplace
# → genera calcoli.cpython-312-x86_64-linux-gnu.so
```

---

# Parte D — Private Package Index

---

## D1. devpi: server privato PyPI

```bash
# Avvia devpi server
docker run -d --name devpi \
  -p 3141:3141 \
  -v devpi_data:/data \
  devpi/devpi:latest

# Configura pip per usare il server privato
pip config set global.index-url http://localhost:3141/root/pypi/+simple/
pip config set global.extra-index-url https://pypi.org/simple/

# Con uv
uv add --index http://localhost:3141/root/pypi/+simple/ mio-pacchetto-privato

# pyproject.toml per più indici
[tool.uv.sources]
pacchetto-privato = { index = "privato" }

[[tool.uv.index]]
name = "privato"
url = "http://localhost:3141/root/pypi/+simple/"
```

---

# Parte E — cibuildwheel per build cross-platform

---

## E1. GitHub Actions con cibuildwheel

```yaml
# .github/workflows/build-wheels.yml
name: Build Wheels

on:
  push:
    tags: ["v*"]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - uses: actions/checkout@v4

      - name: Build wheels
        uses: pypa/cibuildwheel@v2.19
        env:
          CIBW_BUILD: "cp312-* cp313-*"   # Python 3.12 e 3.13
          CIBW_ARCHS_MACOS: "x86_64 arm64"
          CIBW_ARCHS_LINUX: "x86_64 aarch64"
          CIBW_TEST_COMMAND: "pytest {project}/tests"

      - uses: actions/upload-artifact@v4
        with:
          name: wheels-${{ matrix.os }}
          path: ./wheelhouse/*.whl

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: wheels-*
          merge-multiple: true
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

## Riepilogo

## Quando usare estensioni native

| Caso | Strumento | Note |
|---|---|---|
| Loop numerici critici | Cython | Integra con NumPy nativamente |
| Logica sicura, parallela | Rust + maturin | Zero memory unsafe |
| Bind a libreria C | ctypes / cffi | Nessuna compilazione |
| Calcoli scientifici | Numba (@njit) | JIT, nessuna compilazione offline |

## Prossimi passi

- `tutorial_33_profiling.md` — come decidere QUANDO usare estensioni native
