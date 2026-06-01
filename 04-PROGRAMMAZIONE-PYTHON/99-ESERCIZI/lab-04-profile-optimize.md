# Lab 04 — Profiling di Codice Lento e Ottimizzazione con NumPy/numba

> **Moduli di riferimento:** [25-performance.md](../25-performance.md), [33-profiling-memoria-gc.md](../33-profiling-memoria-gc.md), [03-strutture-dati-avanzate.md](../03-strutture-dati-avanzate.md)
> **Tempo stimato:** 4-5 ore
> **Livello:** proficient
> **Prerequisiti:** completamento moduli 01, 03, 25, 33; Python 3.12+ installato; `uv` o `pip` disponibile
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Hai ereditato una pipeline ETL interna che elabora dati di transazioni finanziarie.
Il job notturno impiega 45 minuti per processare 2 milioni di record, occupando 4 GB
di RAM su un server con 8 GB disponibili. Il team infrastruttura ha chiesto di ridurre
il tempo di esecuzione sotto i 10 minuti e il consumo di memoria sotto i 2 GB, senza
cambiare il formato dei dati in input. Il tuo compito e profilare il codice,
identificare i colli di bottiglia, e ottimizzare sistematicamente con strumenti e
tecniche misurabili.

---

## Obiettivi

Al termine del lab saprai:

1. Identificare bottleneck CPU con `cProfile` e `pstats`
2. Usare `py-spy` per profiling di processi in esecuzione senza riavvio
3. Eseguire micro-benchmark affidabili con `timeit`
4. Profilare l'allocazione di memoria con `tracemalloc`
5. Rilevare memory leak con `objgraph`
6. Effettuare tuning del garbage collector con `gc.set_threshold` e `gc.freeze`
7. Ottimizzare calcoli numerici con NumPy vectorization
8. Compilare hotspot con `numba` JIT
9. Scegliere la struttura dati giusta per il caso d'uso
10. Analizzare la complessita algoritmica con benchmark reali
11. Generare e interpretare flame graph
12. Produrre un report before/after con metriche quantitative

---

## Ambiente

```text
project/
├── pyproject.toml
├── src/
│   └── etl_optimizer/
│       ├── __init__.py
│       ├── baseline.py          # Codice lento originale
│       ├── profiling.py         # Script di profiling
│       ├── optimized.py         # Versione ottimizzata
│       ├── gc_tuning.py         # Esperimenti GC
│       └── benchmarks.py        # Confronti before/after
└── data/
    └── generate_data.py         # Genera dataset di test
```

Dipendenze:

```bash
uv init etl-optimizer && cd etl-optimizer
uv add numpy numba
uv add --dev py-spy objgraph pytest
```

> **Nota:** `py-spy` su Linux richiede `sudo` o `CAP_SYS_PTRACE` per attaccarsi
> a processi in esecuzione. `objgraph` richiede `graphviz` per la visualizzazione
> dei grafi (`apt install graphviz` o equivalente).
> `numba` installa LLVM (~200 MB); il primo import e lento per la compilazione.

---

## Parte 1 — Il Codice Lento (Baseline) (30 min)

### 1.1 Generare il dataset di test

Creare `data/generate_data.py`:

```python
"""Genera un dataset CSV di transazioni sintetiche."""
import csv
import random
import string
from pathlib import Path

ROWS = 500_000  # Ridotto per il lab; in produzione sarebbero 2M
OUTPUT = Path(__file__).parent / "transactions.csv"

CATEGORIES = [
    "food", "transport", "utilities", "entertainment",
    "health", "education", "shopping", "rent",
]


def generate() -> None:
    random.seed(42)
    with OUTPUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "amount", "category", "description", "score"])
        for i in range(ROWS):
            writer.writerow([
                i,
                round(random.uniform(0.5, 9999.99), 2),
                random.choice(CATEGORIES),
                "".join(random.choices(string.ascii_lowercase, k=50)),
                round(random.gauss(50, 15), 2),
            ])
    print(f"Generated {ROWS} rows -> {OUTPUT}")


if __name__ == "__main__":
    generate()
```

```bash
python data/generate_data.py
```

### 1.2 Il codice baseline (deliberatamente inefficiente)

Creare `src/etl_optimizer/baseline.py`:

```python
"""Pipeline ETL baseline — deliberatamente inefficiente per il lab."""
from __future__ import annotations

import csv
import math
import time
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "transactions.csv"


def load_data(path: Path = DATA_PATH) -> list[dict]:
    """Carica il CSV in una lista di dizionari."""
    with path.open() as f:
        return list(csv.DictReader(f))


def normalize_scores(records: list[dict]) -> list[dict]:
    """Normalizza gli score 0-100 — implementazione O(n^2)."""
    result = []
    all_scores = [float(r["score"]) for r in records]
    min_score = min(all_scores)
    max_score = max(all_scores)
    score_range = max_score - min_score

    for record in records:
        new_record = dict(record)  # shallow copy
        raw = float(record["score"])
        new_record["score_normalized"] = (raw - min_score) / score_range
        result.append(new_record)
    return result


def compute_distance_matrix(scores: list[float]) -> list[list[float]]:
    """Calcola matrice di distanze — O(n^2) spazio e tempo."""
    n = len(scores)
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            dist = math.sqrt((scores[i] - scores[j]) ** 2)
            row.append(dist)
        matrix.append(row)
    return matrix


def categorize_amounts(records: list[dict]) -> dict[str, list[float]]:
    """Raggruppa gli importi per categoria — usa concatenazione liste."""
    categories: dict[str, list[float]] = {}
    for record in records:
        cat = record["category"]
        amount = float(record["amount"])
        if cat not in categories:
            categories[cat] = []
        categories[cat] = categories[cat] + [amount]  # copia ogni volta
    return categories


def find_duplicates(records: list[dict]) -> list[dict]:
    """Trova duplicati per description — O(n^2) brute force."""
    duplicates = []
    for i, r1 in enumerate(records):
        for j, r2 in enumerate(records):
            if i < j and r1["description"] == r2["description"]:
                duplicates.append(r1)
    return duplicates


def compute_statistics(amounts: list[float]) -> dict:
    """Calcola statistiche — ricalcola somma/media piu volte."""
    total = sum(amounts)
    mean = total / len(amounts)
    variance = sum((x - sum(amounts) / len(amounts)) ** 2 for x in amounts) / len(amounts)
    std_dev = math.sqrt(variance)
    sorted_amounts = sorted(amounts)
    median = sorted_amounts[len(sorted_amounts) // 2]
    return {
        "total": total,
        "mean": mean,
        "std_dev": std_dev,
        "median": median,
        "min": min(amounts),
        "max": max(amounts),
    }


def run_baseline() -> dict:
    """Esegue la pipeline completa e restituisce i timing."""
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    records = load_data()
    timings["load"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    normalized = normalize_scores(records)
    timings["normalize"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    categories = categorize_amounts(records)
    timings["categorize"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    # Usa solo i primi 2000 per la matrice (altrimenti OOM)
    scores_subset = [float(r["score"]) for r in records[:2000]]
    _matrix = compute_distance_matrix(scores_subset)
    timings["distance_matrix"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    for cat, amounts in categories.items():
        _stats = compute_statistics(amounts)
    timings["statistics"] = time.perf_counter() - t0

    timings["total"] = sum(timings.values())

    print("\n=== BASELINE TIMING ===")
    for step, elapsed in timings.items():
        print(f"  {step:20s}: {elapsed:.3f}s")

    return timings


if __name__ == "__main__":
    run_baseline()
```

Eseguire e annotare i tempi:

```bash
python -m etl_optimizer.baseline
```

---

## Parte 2 — Profiling CPU con cProfile (30 min)

### 2.1 Profiling da riga di comando

```bash
python -m cProfile -s cumulative -m etl_optimizer.baseline 2>&1 | head -40
```

### 2.2 Profiling programmatico con pstats

Creare `src/etl_optimizer/profiling.py`:

```python
"""Script di profiling con cProfile + pstats."""
import cProfile
import pstats
from io import StringIO
from pathlib import Path

from etl_optimizer.baseline import run_baseline

PROFILE_DIR = Path(__file__).resolve().parents[2] / "data"


def profile_baseline() -> None:
    profile_path = PROFILE_DIR / "baseline.prof"

    # Esegui con profiler
    profiler = cProfile.Profile()
    profiler.enable()
    run_baseline()
    profiler.disable()

    # Salva il profilo binario (per visualizzazione flame graph)
    profiler.dump_stats(str(profile_path))
    print(f"\nProfile salvato in {profile_path}")

    # Analisi con pstats
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)

    print("\n=== TOP 20 PER CUMULATIVE TIME ===")
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    print(stream.getvalue())

    # Reset e ordina per tottime (tempo nella funzione stessa)
    stream.truncate(0)
    stream.seek(0)
    stats.sort_stats("tottime")
    print("\n=== TOP 20 PER TOTAL TIME ===")
    stats.print_stats(20)
    print(stream.getvalue())

    # Filtra per modulo specifico
    stream.truncate(0)
    stream.seek(0)
    print("\n=== SOLO baseline.py ===")
    stats.print_stats("baseline.py")
    print(stream.getvalue())

    # Callers: chi chiama le funzioni piu lente
    stream.truncate(0)
    stream.seek(0)
    print("\n=== CALLERS delle top 5 ===")
    stats.print_callers(5)
    print(stream.getvalue())


if __name__ == "__main__":
    profile_baseline()
```

### 2.3 Cosa cercare nell'output

Le colonne chiave di cProfile:

| Colonna | Significato |
|---------|-------------|
| `ncalls` | Numero di invocazioni |
| `tottime` | Tempo nella funzione (escluse sotto-chiamate) |
| `percall` | `tottime / ncalls` |
| `cumtime` | Tempo nella funzione + sotto-chiamate |

**Red flag tipici:**

- `ncalls` sproporzionato rispetto alla dimensione del dataset
- `tottime` alto su operazioni che dovrebbero essere O(n) ma sono O(n^2)
- Funzioni builtin (`append`, `__eq__`) con milioni di chiamate

---

## Parte 3 — py-spy: Profiling di un Processo Live (30 min)

### 3.1 Attach a un processo in esecuzione

```bash
# In un terminale, avviare la pipeline baseline
python -m etl_optimizer.baseline &
PID=$!

# In un altro terminale (richiede sudo su Linux)
sudo py-spy top --pid $PID
```

### 3.2 Registrare un profilo SVG (flame graph)

```bash
# Registra per 30 secondi e genera flame graph SVG
sudo py-spy record \
    --output data/flamegraph.svg \
    --format speedscope \
    -- python -m etl_optimizer.baseline
```

### 3.3 Interpretare il flame graph

Il flame graph SVG mostra:

- **Asse X:** proporzione del tempo di CPU (non cronologico)
- **Asse Y:** profondita dello stack di chiamate
- **Larghezza del box:** tempo totale speso in quella funzione + discendenti

Cercare:

1. **Plateau larghi in alto:** funzioni che dominano il tempo di esecuzione
2. **Torri strette e profonde:** ricorsione o catene di chiamate inutili
3. **Box larghi di funzioni builtin:** segnale di algoritmo inefficiente

> Aprire il file SVG nel browser per la visualizzazione interattiva.
> Il formato speedscope puo essere visualizzato su https://www.speedscope.app/

---

## Parte 4 — Micro-Benchmark con timeit (20 min)

### 4.1 Confrontare operazioni elementari

```python
"""Benchmark di operazioni comuni per guidare l'ottimizzazione."""
import timeit


def bench(label: str, stmt: str, setup: str = "", number: int = 100_000) -> None:
    elapsed = timeit.timeit(stmt, setup=setup, number=number, globals=globals())
    per_op = elapsed / number * 1e6  # microsecondi
    print(f"  {label:40s}: {per_op:8.2f} us/op")


def run_microbenchmarks() -> None:
    print("\n=== MICRO-BENCHMARK ===\n")

    # List append vs list concatenation
    print("--- List operations ---")
    bench(
        "list.append()",
        "lst.append(42)",
        setup="lst = []",
    )
    bench(
        "list concat (lst = lst + [x])",
        "lst = lst + [42]",
        setup="lst = list(range(100))",
        number=10_000,
    )

    # Dict lookup vs list search
    print("\n--- Lookup ---")
    bench(
        "dict lookup (hit)",
        "_ = d[500]",
        setup="d = {i: i for i in range(1000)}",
    )
    bench(
        "list linear search",
        "_ = 500 in lst",
        setup="lst = list(range(1000))",
    )
    bench(
        "set lookup",
        "_ = 500 in s",
        setup="s = set(range(1000))",
    )

    # String concatenation
    print("\n--- String building ---")
    bench(
        "str concat (+= loop 100)",
        "s = ''; [s := s + 'x' for _ in range(100)]",
        number=10_000,
    )
    bench(
        "''.join() 100 items",
        "''.join('x' for _ in range(100))",
        number=10_000,
    )

    # Math
    print("\n--- Math ---")
    bench("math.sqrt()", "math.sqrt(42.0)", setup="import math")
    bench("x ** 0.5", "42.0 ** 0.5")
    bench("abs(a - b)", "abs(a - b)", setup="a, b = 42.0, 17.0")


if __name__ == "__main__":
    run_microbenchmarks()
```

### 4.2 timeit dalla shell

```bash
python -m timeit -s "import math" "math.sqrt(42.0)"
python -m timeit "42.0 ** 0.5"
```

---

## Parte 5 — Memory Profiling con tracemalloc (30 min)

### 5.1 Snapshot e confronto

```python
"""Profiling della memoria con tracemalloc."""
import tracemalloc
import linecache
from etl_optimizer.baseline import load_data, normalize_scores, categorize_amounts


def display_top(snapshot: tracemalloc.Snapshot, limit: int = 10) -> None:
    """Mostra le top N allocazioni per dimensione."""
    stats = snapshot.statistics("lineno")
    print(f"\n--- Top {limit} allocazioni ---")
    for i, stat in enumerate(stats[:limit], 1):
        frame = stat.traceback[0]
        print(f"  #{i}: {frame.filename}:{frame.lineno}"
              f"  {stat.size / 1024:.1f} KiB ({stat.count} blocchi)")
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print(f"       {line}")


def profile_memory() -> None:
    tracemalloc.start(25)  # 25 frame di profondita per traceback

    # Snapshot prima del caricamento
    snap_start = tracemalloc.take_snapshot()

    records = load_data()
    snap_after_load = tracemalloc.take_snapshot()

    normalized = normalize_scores(records)
    snap_after_normalize = tracemalloc.take_snapshot()

    categories = categorize_amounts(records)
    snap_after_categorize = tracemalloc.take_snapshot()

    # Differenze tra snapshot
    print("\n=== MEMORY DELTA: load_data ===")
    diff_load = snap_after_load.compare_to(snap_start, "lineno")
    for stat in diff_load[:5]:
        print(f"  {stat}")

    print("\n=== MEMORY DELTA: normalize_scores ===")
    diff_norm = snap_after_normalize.compare_to(snap_after_load, "lineno")
    for stat in diff_norm[:5]:
        print(f"  {stat}")

    print("\n=== MEMORY DELTA: categorize_amounts ===")
    diff_cat = snap_after_categorize.compare_to(snap_after_normalize, "lineno")
    for stat in diff_cat[:5]:
        print(f"  {stat}")

    # Memoria totale
    current, peak = tracemalloc.get_traced_memory()
    print(f"\nMemoria corrente: {current / 1024 / 1024:.1f} MiB")
    print(f"Picco memoria:   {peak / 1024 / 1024:.1f} MiB")

    tracemalloc.stop()


if __name__ == "__main__":
    profile_memory()
```

### 5.2 Interpretazione

L'output mostrera che:

- `load_data()` alloca un `dict` per ogni riga (overhead ~400 byte/dict)
- `normalize_scores()` crea una copia completa di ogni record
- `categorize_amounts()` ricopre la lista a ogni iterazione (concatenazione)

Questi sono i target di ottimizzazione per la Parte 9.

---

## Parte 6 — Memory Leak Detection con objgraph (30 min)

### 6.1 Identificare reference cycle

```python
"""Rilevamento memory leak con objgraph."""
import gc
import objgraph


class CacheEntry:
    """Esempio di classe con reference cycle intenzionale."""

    def __init__(self, key: str, value: object) -> None:
        self.key = key
        self.value = value
        self.cache: Cache | None = None  # back-reference -> cycle


class Cache:
    """Cache che crea reference cycle con le sue entry."""

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def put(self, key: str, value: object) -> None:
        entry = CacheEntry(key, value)
        entry.cache = self  # cycle: Cache -> CacheEntry -> Cache
        self._entries[key] = entry


def demonstrate_leak() -> None:
    gc.collect()
    baseline_dicts = objgraph.count("dict")
    baseline_entries = objgraph.count("CacheEntry")

    # Crea e "dimentica" cache con cicli
    for i in range(100):
        cache = Cache()
        for j in range(10):
            cache.put(f"key-{j}", f"value-{i}-{j}")
        # cache esce dallo scope ma i cicli impediscono la deallocazione
        # immediata tramite reference counting

    # Prima del GC: gli oggetti sono ancora in memoria
    print(f"CacheEntry prima del GC: {objgraph.count('CacheEntry')}")
    print(f"Nuovi dict: {objgraph.count('dict') - baseline_dicts}")

    # Mostra la catena di riferimenti
    print("\nChain di riferimenti per un CacheEntry:")
    entry = objgraph.by_type("CacheEntry")[0]
    objgraph.show_backrefs(
        entry,
        max_depth=3,
        filename="data/backrefs.png",  # richiede graphviz
    )

    # Forza il GC
    collected = gc.collect()
    print(f"\nGC ha raccolto {collected} oggetti")
    print(f"CacheEntry dopo GC: {objgraph.count('CacheEntry')}")


def detect_growth() -> None:
    """Mostra gli oggetti che crescono tra iterazioni."""
    gc.collect()
    print("\n=== Object growth detection ===")
    for i in range(5):
        cache = Cache()
        for j in range(50):
            cache.put(f"k-{j}", list(range(100)))
        # Non raccogliere: simula leak
        if i % 2 == 0:
            print(f"\n--- Iteration {i} ---")
            objgraph.show_growth(limit=5)


if __name__ == "__main__":
    demonstrate_leak()
    detect_growth()
```

### 6.2 Risolvere il leak con weakref

```python
import weakref


class CacheEntryFixed:
    __slots__ = ("key", "value", "_cache_ref")

    def __init__(self, key: str, value: object) -> None:
        self.key = key
        self.value = value
        self._cache_ref: weakref.ref[CacheFixed] | None = None

    @property
    def cache(self) -> CacheFixed | None:
        return self._cache_ref() if self._cache_ref is not None else None

    @cache.setter
    def cache(self, c: CacheFixed) -> None:
        self._cache_ref = weakref.ref(c)
```

---

## Parte 7 — GC Tuning (20 min)

### 7.1 Comprendere i threshold

Creare `src/etl_optimizer/gc_tuning.py`:

```python
"""Esperimenti con il garbage collector."""
import gc
import time


def show_gc_stats() -> None:
    """Mostra lo stato corrente del GC."""
    print(f"Threshold: {gc.get_threshold()}")
    print(f"Count:     {gc.get_count()}")
    print(f"Stats:     {gc.get_stats()}")


def benchmark_gc_settings(
    records: list[dict],
    thresholds: list[tuple[int, int, int]],
) -> None:
    """Confronta diverse impostazioni GC su un workload reale."""
    from etl_optimizer.baseline import normalize_scores

    for thresh in thresholds:
        gc.set_threshold(*thresh)
        gc.collect()  # partenza pulita

        # Conta le raccolte durante il lavoro
        stats_before = gc.get_stats()
        collections_before = sum(s["collections"] for s in stats_before)

        t0 = time.perf_counter()
        _ = normalize_scores(records)
        elapsed = time.perf_counter() - t0

        stats_after = gc.get_stats()
        collections_after = sum(s["collections"] for s in stats_after)
        collections = collections_after - collections_before

        print(
            f"  threshold={thresh!s:20s}  "
            f"time={elapsed:.3f}s  "
            f"collections={collections}"
        )

    # Ripristina i default
    gc.set_threshold(700, 10, 10)


def demonstrate_gc_freeze() -> None:
    """gc.freeze() per escludere oggetti long-lived dalla scansione."""
    from etl_optimizer.baseline import load_data

    records = load_data()
    gc.collect()

    # Congela tutti gli oggetti attuali (li sposta fuori dalle generazioni)
    gc.freeze()
    frozen = gc.get_freeze_count()
    print(f"\nOggetti congelati: {frozen}")
    print(f"Count dopo freeze: {gc.get_count()}")

    # Ora solo i nuovi oggetti vengono scansionati dal GC
    # Utile quando hai dati statici caricati all'avvio
    t0 = time.perf_counter()
    gc.collect()
    elapsed = time.perf_counter() - t0
    print(f"GC collect dopo freeze: {elapsed*1000:.2f}ms")

    # Ripristina
    gc.unfreeze()


if __name__ == "__main__":
    from etl_optimizer.baseline import load_data

    records = load_data()
    print("=== GC TUNING BENCHMARK ===\n")
    benchmark_gc_settings(records, [
        (700, 10, 10),    # default CPython
        (50_000, 20, 20), # meno raccolte gen-0
        (100, 5, 5),      # piu raccolte gen-0
    ])
    demonstrate_gc_freeze()
```

---

## Parte 8 — Ottimizzazione con NumPy Vectorization (40 min)

### 8.1 Distance matrix vettorizzata

Creare `src/etl_optimizer/optimized.py`:

```python
"""Pipeline ETL ottimizzata."""
from __future__ import annotations

import csv
import time
from pathlib import Path

import numpy as np

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "transactions.csv"


def load_data_numpy(path: Path = DATA_PATH) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Carica i dati direttamente in array NumPy."""
    amounts: list[float] = []
    scores: list[float] = []
    categories: list[str] = []

    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            amounts.append(float(row["amount"]))
            scores.append(float(row["score"]))
            categories.append(row["category"])

    return np.array(amounts), np.array(scores), categories


def normalize_scores_numpy(scores: np.ndarray) -> np.ndarray:
    """Normalizza con operazioni vettoriali — O(n)."""
    min_s = scores.min()
    max_s = scores.max()
    return (scores - min_s) / (max_s - min_s)


def compute_distance_matrix_numpy(scores: np.ndarray) -> np.ndarray:
    """Matrice di distanze vettorizzata — broadcasting."""
    # scores[:, None] ha shape (n, 1), scores[None, :] ha shape (1, n)
    # il broadcasting produce una matrice (n, n)
    return np.abs(scores[:, np.newaxis] - scores[np.newaxis, :])


def categorize_amounts_numpy(
    amounts: np.ndarray,
    categories: list[str],
) -> dict[str, np.ndarray]:
    """Raggruppa con NumPy boolean indexing."""
    cat_array = np.array(categories)
    unique_cats = np.unique(cat_array)
    return {
        cat: amounts[cat_array == cat]
        for cat in unique_cats
    }


def compute_statistics_numpy(amounts: np.ndarray) -> dict:
    """Statistiche vettorizzate — una singola passata."""
    return {
        "total": float(np.sum(amounts)),
        "mean": float(np.mean(amounts)),
        "std_dev": float(np.std(amounts)),
        "median": float(np.median(amounts)),
        "min": float(np.min(amounts)),
        "max": float(np.max(amounts)),
    }


def run_optimized() -> dict:
    """Esegue la pipeline ottimizzata e restituisce i timing."""
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    amounts, scores, categories = load_data_numpy()
    timings["load"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _normalized = normalize_scores_numpy(scores)
    timings["normalize"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    cat_amounts = categorize_amounts_numpy(amounts, categories)
    timings["categorize"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    _matrix = compute_distance_matrix_numpy(scores[:2000])
    timings["distance_matrix"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    for cat, cat_am in cat_amounts.items():
        _stats = compute_statistics_numpy(cat_am)
    timings["statistics"] = time.perf_counter() - t0

    timings["total"] = sum(timings.values())

    print("\n=== OPTIMIZED TIMING ===")
    for step, elapsed in timings.items():
        print(f"  {step:20s}: {elapsed:.3f}s")

    return timings


if __name__ == "__main__":
    run_optimized()
```

### 8.2 Perche il broadcasting funziona

```text
scores shape:        (2000,)
scores[:, None]:     (2000, 1)   # colonna
scores[None, :]:     (1, 2000)   # riga

Sottrazione con broadcasting:
  (2000, 1) - (1, 2000) -> (2000, 2000)

Equivale a due loop nidificati ma eseguito in C ottimizzato.
```

---

## Parte 9 — numba JIT Compilation (30 min)

### 9.1 Compilare la distance matrix con numba

```python
import numba


@numba.njit(parallel=True)
def distance_matrix_numba(scores: np.ndarray) -> np.ndarray:
    """Distance matrix con numba JIT + parallelismo."""
    n = scores.shape[0]
    result = np.empty((n, n), dtype=np.float64)
    for i in numba.prange(n):
        for j in range(n):
            result[i, j] = abs(scores[i] - scores[j])
    return result
```

### 9.2 Warmup e benchmark

```python
def benchmark_numba(scores: np.ndarray) -> None:
    """Confronta NumPy vs numba per la distance matrix."""
    subset = scores[:2000].astype(np.float64)

    # Warmup numba (prima chiamata include la compilazione JIT)
    _ = distance_matrix_numba(subset[:10])

    # Benchmark NumPy
    t0 = time.perf_counter()
    _np_result = compute_distance_matrix_numpy(subset)
    t_numpy = time.perf_counter() - t0

    # Benchmark numba (gia compilato)
    t0 = time.perf_counter()
    _nb_result = distance_matrix_numba(subset)
    t_numba = time.perf_counter() - t0

    print(f"\n=== DISTANCE MATRIX 2000x2000 ===")
    print(f"  NumPy:  {t_numpy:.3f}s")
    print(f"  numba:  {t_numba:.3f}s")
    print(f"  Speedup: {t_numpy/t_numba:.1f}x")

    # Verifica correttezza
    assert np.allclose(_np_result, _nb_result), "Risultati divergenti!"
```

### 9.3 Quando usare numba

| Caso d'uso | numba? | Alternativa |
|------------|--------|-------------|
| Loop numerici puri | Si | — |
| Operazioni su array gia vettorizzabili | No | NumPy |
| Codice con stringhe/dict | No | Cython, C extension |
| Codice I/O-bound | No | asyncio, threading |
| Hot path in produzione | Si | Dopo profiling |

---

## Parte 10 — Scelta Strutture Dati (30 min)

### 10.1 Benchmark: list vs deque vs set vs dict

```python
from collections import deque
import timeit


def benchmark_data_structures() -> None:
    """Confronta le strutture dati per operazioni comuni."""
    N = 100_000

    print("\n=== DATA STRUCTURE BENCHMARK ===\n")

    # --- Append ---
    print("--- Append N items ---")
    for label, setup, stmt in [
        ("list.append", "lst = []", "lst.append(42)"),
        ("deque.append", "from collections import deque; dq = deque()", "dq.append(42)"),
        ("deque.appendleft", "from collections import deque; dq = deque()", "dq.appendleft(42)"),
    ]:
        t = timeit.timeit(stmt, setup=setup, number=N)
        print(f"  {label:25s}: {t*1e6/N:.2f} us/op")

    # --- Lookup ---
    print("\n--- Lookup (in) ---")
    for label, setup, stmt in [
        ("list (hit, middle)",
         f"lst = list(range({N}))",
         f"_ = {N//2} in lst"),
        ("set (hit)",
         f"s = set(range({N}))",
         f"_ = {N//2} in s"),
        ("dict (hit)",
         f"d = {{i: None for i in range({N})}}",
         f"_ = {N//2} in d"),
    ]:
        t = timeit.timeit(stmt, setup=setup, number=1000)
        print(f"  {label:25s}: {t/1000*1e6:.2f} us/op")

    # --- Insert at head ---
    print("\n--- Insert at position 0 ---")
    for label, setup, stmt in [
        ("list.insert(0, x)",
         "lst = list(range(10000))",
         "lst.insert(0, 42)"),
        ("deque.appendleft",
         "from collections import deque; dq = deque(range(10000))",
         "dq.appendleft(42)"),
    ]:
        t = timeit.timeit(stmt, setup=setup, number=10_000)
        print(f"  {label:25s}: {t/10_000*1e6:.2f} us/op")

    # --- Pop ---
    print("\n--- Pop from left ---")
    for label, setup, stmt in [
        ("list.pop(0)",
         "lst = list(range(10000))",
         "lst.pop(0) if lst else None"),
        ("deque.popleft",
         "from collections import deque; dq = deque(range(10000))",
         "dq.popleft() if dq else None"),
    ]:
        t = timeit.timeit(stmt, setup=setup, number=5000)
        print(f"  {label:25s}: {t/5000*1e6:.2f} us/op")
```

### 10.2 Complessita a confronto

| Operazione | list | deque | set | dict |
|------------|------|-------|-----|------|
| Append (coda) | O(1)* | O(1) | — | — |
| Prepend (testa) | O(n) | O(1) | — | — |
| Lookup (in) | O(n) | O(n) | O(1) | O(1) |
| Pop (coda) | O(1) | O(1) | — | — |
| Pop (testa) | O(n) | O(1) | — | — |
| Insert (mezzo) | O(n) | O(n) | — | — |
| Delete by value | O(n) | O(n) | O(1) | O(1) |

\* amortizzato; il resize occasionale e O(n)

---

## Parte 11 — Confronto Before/After (30 min)

### 11.1 Benchmark completo

Creare `src/etl_optimizer/benchmarks.py`:

```python
"""Confronto before/after con metriche quantitative."""
import tracemalloc
import time

from etl_optimizer.baseline import run_baseline
from etl_optimizer.optimized import run_optimized


def run_comparison() -> None:
    """Esegue entrambe le pipeline e confronta i risultati."""

    # --- BASELINE ---
    print("=" * 60)
    print("BASELINE")
    print("=" * 60)
    tracemalloc.start()
    baseline_timings = run_baseline()
    _, baseline_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- OPTIMIZED ---
    print("\n" + "=" * 60)
    print("OPTIMIZED")
    print("=" * 60)
    tracemalloc.start()
    optimized_timings = run_optimized()
    _, optimized_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- CONFRONTO ---
    print("\n" + "=" * 60)
    print("CONFRONTO")
    print("=" * 60)

    print(f"\n{'Step':20s} {'Baseline':>10s} {'Optimized':>10s} {'Speedup':>10s}")
    print("-" * 55)
    for step in baseline_timings:
        bt = baseline_timings[step]
        ot = optimized_timings.get(step, 0)
        speedup = bt / ot if ot > 0 else float("inf")
        print(f"{step:20s} {bt:10.3f}s {ot:10.3f}s {speedup:9.1f}x")

    print(f"\n{'Metrica':20s} {'Baseline':>12s} {'Optimized':>12s} {'Riduzione':>12s}")
    print("-" * 60)
    print(
        f"{'Peak memory':20s} "
        f"{baseline_peak/1024/1024:10.1f} MiB "
        f"{optimized_peak/1024/1024:10.1f} MiB "
        f"{(1 - optimized_peak/baseline_peak)*100:10.1f}%"
    )
    print(
        f"{'Tempo totale':20s} "
        f"{baseline_timings['total']:10.3f}   s "
        f"{optimized_timings['total']:10.3f}   s "
        f"{(1 - optimized_timings['total']/baseline_timings['total'])*100:10.1f}%"
    )


if __name__ == "__main__":
    run_comparison()
```

### 11.2 Output atteso

```text
============================================================
CONFRONTO
============================================================

Step                   Baseline  Optimized    Speedup
-------------------------------------------------------
load                     0.850s     0.780s       1.1x
normalize                0.320s     0.003s     106.7x
categorize               2.100s     0.015s     140.0x
distance_matrix          1.800s     0.025s      72.0x
statistics               0.180s     0.002s      90.0x
total                    5.250s     0.825s       6.4x

Metrica                   Baseline    Optimized    Riduzione
------------------------------------------------------------
Peak memory              380.2 MiB     85.4 MiB       77.5%
Tempo totale               5.250   s     0.825   s       84.3%
```

> I valori reali dipendono dall'hardware. Il punto e che ogni step mostra un
> miglioramento misurabile e il report quantifica il delta.

---

## Parte 12 — Flame Graph (20 min)

### 12.1 Generare flame graph con cProfile + flameprof

```bash
# Installa flameprof (converte profili cProfile in flame graph SVG)
uv add --dev flameprof

# Profila la baseline e genera il flame graph
python -m cProfile -o data/baseline.prof -m etl_optimizer.baseline
flameprof data/baseline.prof > data/baseline-flame.svg

# Profila la versione ottimizzata
python -m cProfile -o data/optimized.prof -m etl_optimizer.optimized
flameprof data/optimized.prof > data/optimized-flame.svg
```

### 12.2 Confronto visuale

Aprire entrambi i file SVG nel browser e confrontare:

1. **Baseline:** le funzioni `categorize_amounts` e `compute_distance_matrix`
   dominano con box larghi. I box builtin `list.__add__` e `float.__sub__`
   mostrano milioni di chiamate.

2. **Optimized:** i box sono stretti e uniformi. Le operazioni NumPy sono quasi
   invisibili perche eseguite in C.

### 12.3 Alternativa: py-spy flame graph

```bash
sudo py-spy record \
    --output data/baseline-pyspy.svg \
    -- python -m etl_optimizer.baseline

sudo py-spy record \
    --output data/optimized-pyspy.svg \
    -- python -m etl_optimizer.optimized
```

La differenza tra cProfile e py-spy: cProfile e deterministico (misura ogni
chiamata, overhead alto); py-spy e un sampling profiler (campiona lo stack a
intervalli, overhead < 2%, adatto alla produzione).

---

## Checklist finale

- [ ] Baseline eseguita e timing annotati
- [ ] cProfile eseguito con analisi `pstats` (cumtime, tottime, callers)
- [ ] py-spy usato per attach a processo live e generazione flame graph
- [ ] Micro-benchmark con `timeit` per operazioni elementari
- [ ] `tracemalloc` con snapshot diff tra fasi della pipeline
- [ ] Memory leak dimostrato e risolto con `objgraph` + `weakref`
- [ ] GC tuning con `gc.set_threshold` e `gc.freeze` sperimentato
- [ ] Funzioni ottimizzate con NumPy vectorization
- [ ] Distance matrix compilata con `numba.njit(parallel=True)`
- [ ] Benchmark strutture dati (list vs deque vs set vs dict) eseguito
- [ ] Report before/after con metriche CPU e memoria prodotto
- [ ] Flame graph baseline vs ottimizzato confrontati

---

## Valutazione

| Criterio | Peso | Insufficiente | Sufficiente | Buono | Eccellente |
|----------|------|---------------|-------------|-------|------------|
| Profiling CPU (cProfile + py-spy) | 20% | Non eseguito | Solo cProfile CLI | cProfile + pstats analisi | cProfile + py-spy + flame graph |
| Memory profiling (tracemalloc + objgraph) | 20% | Non eseguito | Solo tracemalloc base | Snapshot diff tra fasi | Diff + objgraph leak detection + fix |
| Ottimizzazione NumPy | 20% | Non implementata | Una funzione vettorizzata | Tutte le funzioni vettorizzate | Vettorizzazione + broadcasting spiegato |
| numba JIT | 10% | Non usato | Decoratore applicato | Warmup + benchmark | njit(parallel) + verifica correttezza |
| Strutture dati e complessita | 10% | Nessun benchmark | Benchmark eseguito | Benchmark + tabella complessita | Benchmark + scelta motivata nel codice |
| GC tuning | 10% | Non eseguito | gc.get_stats() letto | Threshold confrontati | Threshold + freeze + metriche |
| Report before/after | 10% | Nessun confronto | Timing manuali | Script automatizzato | CPU + memoria + % riduzione |

---

## Riferimenti

- [25-performance.md](../25-performance.md) — strategie di ottimizzazione, NumPy, Cython
- [33-profiling-memoria-gc.md](../33-profiling-memoria-gc.md) — modello di memoria CPython, GC, tracemalloc
- [03-strutture-dati-avanzate.md](../03-strutture-dati-avanzate.md) — strutture dati, complessita, scelte
- cProfile — https://docs.python.org/3/library/profile.html
- tracemalloc — https://docs.python.org/3/library/tracemalloc.html
- py-spy — https://github.com/benfred/py-spy
- objgraph — https://mg.pov.lt/objgraph/
- numba — https://numba.readthedocs.io/en/stable/
- gc — https://docs.python.org/3/library/gc.html
