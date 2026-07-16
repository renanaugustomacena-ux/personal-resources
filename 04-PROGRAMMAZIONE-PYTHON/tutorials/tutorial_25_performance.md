# Tutorial 25 — Performance Python: Profilazione, Ottimizzazione, Concorrenza

> **Companion a:** `25-performance.md`
> **Scope:** cProfile, line_profiler, memory_profiler, Cython, Numba, multiprocessing, ottimizzazioni
> **Prerequisiti:** `tutorial_10_programmazione_asincrona.md`, `tutorial_14_data_processing.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Performance Python
│
├── Misura prima di ottimizzare
│   ├── timeit — micro-benchmark
│   ├── cProfile — profiler integrato
│   ├── py-spy — profiler campionamento
│   └── line_profiler — riga per riga
│
├── Memoria
│   ├── memory_profiler — uso per riga
│   ├── tracemalloc — alloc Python
│   ├── objgraph — object graph
│   └── sys.getsizeof — dimensione oggetti
│
├── Ottimizzazioni pure Python
│   ├── List comprehension vs loop
│   ├── Generatori per dati grandi
│   ├── __slots__ per classi
│   ├── functools.cache / lru_cache
│   └── Strutture dati giuste
│
├── Estensioni native
│   ├── NumPy — array C
│   ├── Cython — Python → C
│   ├── Numba — JIT compilation
│   └── ctypes / cffi — C libraries
│
└── Parallelismo
    ├── threading — I/O-bound
    ├── multiprocessing — CPU-bound (bypassa GIL)
    ├── concurrent.futures — API unificata
    └── asyncio — I/O-bound asincrono
```

---

# Parte A — Misura prima di ottimizzare

---

## A1. timeit e benchmark

```python
import timeit
import time

# timeit — micro-benchmark
# Misura il tempo medio di una piccola operazione

# Concatenazione: join vs +
lista_parole = ["hello"] * 1000

def unisci_con_join(parole: list) -> str:
    return " ".join(parole)

def unisci_con_plus(parole: list) -> str:
    risultato = ""
    for p in parole:
        risultato += p + " "
    return risultato

tempo_join = timeit.timeit(lambda: unisci_con_join(lista_parole), number=10_000)
tempo_plus = timeit.timeit(lambda: unisci_con_plus(lista_parole), number=10_000)
print(f"join: {tempo_join:.3f}s — +: {tempo_plus:.3f}s — speedup: {tempo_plus/tempo_join:.1f}x")

# Confronto strutture dati
def cerca_in_lista(elementi: list, target: str) -> bool:
    return target in elementi

def cerca_in_set(elementi: set, target: str) -> bool:
    return target in elementi

grandi_lista = list(range(1_000_000))
grande_set = set(grandi_lista)
target = 999_999

t_lista = timeit.timeit(lambda: cerca_in_lista(grandi_lista, target), number=100)
t_set = timeit.timeit(lambda: cerca_in_set(grande_set, target), number=100)
print(f"Lista: {t_lista:.4f}s — Set: {t_set:.6f}s — speedup: {t_lista/t_set:.0f}x")
```

> **Analogia:** Ottimizzare senza misurare è come fare una dieta eliminando a caso degli alimenti. Prima misura (cProfile/line_profiler), trova dove è il problema reale (il "collo di bottiglia"), poi ottimizza SOLO quello. Nella maggior parte dei programmi, il 90% del tempo viene speso nel 10% del codice.

---

## A2. cProfile: profiler integrato

```python
import cProfile
import pstats
import io

def funzione_lenta():
    return sum(i ** 2 for i in range(100_000))

def funzione_media():
    return [i * 2 for i in range(10_000)]

def main_da_profilare():
    for _ in range(10):
        funzione_lenta()
    for _ in range(100):
        funzione_media()

# Profilazione programmatica
profiler = cProfile.Profile()
profiler.enable()
main_da_profilare()
profiler.disable()

# Stampa statistiche ordinate per tempo cumulativo
stream = io.StringIO()
stats = pstats.Stats(profiler, stream=stream)
stats.sort_stats("cumulative")
stats.print_stats(20)   # top 20 funzioni
print(stream.getvalue())

# Da riga di comando:
# python -m cProfile -s cumulative mio_script.py
# python -m cProfile -o output.prof mio_script.py
# snakeviz output.prof  # visualizzazione web (pip install snakeviz)
```

---

## A3. memory_profiler

```python
# pip install memory-profiler
from memory_profiler import profile

@profile
def funzione_con_memoria():
    # memory_profiler mostra l'uso di RAM riga per riga
    lista = [i ** 2 for i in range(1_000_000)]   # ~8 MB
    del lista
    dizionario = {i: str(i) for i in range(100_000)}
    return dizionario

# Da riga di comando:
# python -m memory_profiler mio_script.py

# tracemalloc — integrato in Python
import tracemalloc

tracemalloc.start()
risultato = [i ** 2 for i in range(1_000_000)]
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")
for stat in top_stats[:10]:
    print(stat)
```

---

# Parte B — Ottimizzazioni Python

---

## B1. Strutture dati e algoritmi

```python
import collections
import heapq
from functools import lru_cache

# 1. Set per ricerca O(1) invece di list O(n)
def conta_unici_list(dati: list) -> int:
    contati = []
    for x in dati:
        if x not in contati:   # O(n) per ogni elemento!
            contati.append(x)
    return len(contati)

def conta_unici_set(dati: list) -> int:
    return len(set(dati))   # O(n) totale

# 2. deque per code efficiente
from collections import deque

coda = deque()
coda.appendleft("primo")   # O(1)
coda.pop()                  # O(1)

# 3. heapq per priority queue
import heapq
task_queue = []
heapq.heappush(task_queue, (1, "alta priorità"))
heapq.heappush(task_queue, (5, "bassa priorità"))
heapq.heappush(task_queue, (3, "media priorità"))
priorita, task = heapq.heappop(task_queue)   # estrae il minimo

# 4. lru_cache per memoizzazione
@lru_cache(maxsize=512)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Python 3.9+ — cache senza limite (più veloce per funzioni pure)
from functools import cache

@cache
def costosa(n: int) -> int:
    import time; time.sleep(0.01)   # simulazione
    return n ** 2
```

---

## B2. Generatori vs liste

```python
import sys

# Lista — carica tutto in memoria
def quadrati_lista(n: int) -> list[int]:
    return [i ** 2 for i in range(n)]

# Generatore — produce un elemento alla volta
def quadrati_gen(n: int):
    for i in range(n):
        yield i ** 2

n = 1_000_000
lista = quadrati_lista(n)
gen = quadrati_gen(n)

print(f"Lista: {sys.getsizeof(lista) / 1024 / 1024:.1f} MB")
print(f"Generatore: {sys.getsizeof(gen)} bytes")

# Quando usare generatori:
# - Dati troppo grandi per la RAM
# - Pipeline di trasformazione
# - Risultati parziali (lazy evaluation)

# Pipeline con generatori
import csv

def leggi_csv(percorso: str):
    with open(percorso, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        yield from reader   # genera una riga alla volta

def filtra_attivi(righe):
    for riga in righe:
        if riga.get("attivo") == "True":
            yield riga

def estrai_email(righe):
    for riga in righe:
        yield riga["email"]

# Composizione: nessuna riga viene caricata tutta in memoria
# emails = list(estrai_email(filtra_attivi(leggi_csv("utenti.csv"))))
```

---

# Parte C — Parallelismo CPU-bound

---

## C1. multiprocessing

```python
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

def calcola_blocco(args: tuple) -> int:
    inizio, fine = args
    return sum(i ** 2 for i in range(inizio, fine))

def somma_quadrati_parallela(n: int) -> int:
    """Divide il lavoro tra N processi."""
    n_cpu = os.cpu_count() or 4
    blocco = n // n_cpu
    range_list = [
        (i * blocco, (i + 1) * blocco if i < n_cpu - 1 else n)
        for i in range(n_cpu)
    ]

    with ProcessPoolExecutor(max_workers=n_cpu) as executor:
        risultati = list(executor.map(calcola_blocco, range_list))

    return sum(risultati)

# as_completed — processa i risultati man mano che arrivano
def elabora_file_parallelo(file_list: list[str]) -> list[dict]:
    risultati = []
    with ProcessPoolExecutor() as executor:
        future_to_file = {
            executor.submit(processa_file, f): f
            for f in file_list
        }
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                risultato = future.result()
                risultati.append(risultato)
            except Exception as e:
                print(f"Errore per {file}: {e}")
    return risultati

def processa_file(percorso: str) -> dict:
    # Operazione CPU-bound simulata
    return {"file": percorso, "righe": 100}
```

---

## C2. Numba: JIT compilation

```python
# pip install numba
from numba import njit, prange
import numpy as np

# @njit: compila a C al primo call (LLVM)
@njit
def somma_quadrati_numba(arr: np.ndarray) -> float:
    totale = 0.0
    for x in arr:
        totale += x ** 2
    return totale

# @njit(parallel=True): parallelizza automaticamente
@njit(parallel=True)
def somma_quadrati_parallela(arr: np.ndarray) -> float:
    return np.sum(arr ** 2)

# Confronto prestazioni
import timeit
arr = np.random.random(10_000_000)

# Prima chiamata è lenta (compilazione)
_ = somma_quadrati_numba(arr)

t_python = timeit.timeit(lambda: sum(x**2 for x in arr), number=3)
t_numpy = timeit.timeit(lambda: np.sum(arr**2), number=100)
t_numba = timeit.timeit(lambda: somma_quadrati_numba(arr), number=100)

print(f"Python: {t_python:.3f}s — NumPy: {t_numpy:.4f}s — Numba: {t_numba:.4f}s")
```

---

# Parte D — __slots__ e ottimizzazioni OOP

---

## D1. __slots__ per classi con molte istanze

```python
import sys

class PuntoNormale:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

class PuntoConSlots:
    __slots__ = ("x", "y")   # no __dict__ per istanza

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

p_norm = PuntoNormale(1.0, 2.0)
p_slots = PuntoConSlots(1.0, 2.0)

print(f"Normale: {sys.getsizeof(p_norm)} bytes + dict")
print(f"Slots: {sys.getsizeof(p_slots)} bytes")
# Slots usa ~40-60% meno memoria per oggetti con molti campi

# 1 milione di punti:
# Normale: ~160 MB
# Slots: ~56 MB
```

---

# Parte E — Riepilogo

## Regola delle ottimizzazioni

1. **Non ottimizzare** prematuramente
2. **Misura** con cProfile o py-spy
3. **Trova** il collo di bottiglia (solitamente 1-2 funzioni)
4. **Ottimizza** solo quel punto
5. **Misura di nuovo** per verificare il miglioramento

## Quick wins comuni

| Problema | Soluzione | Speedup tipico |
|---|---|---|
| Ricerca in lista | Usa set | 100-10.000x |
| Calcolo ripetuto | `@lru_cache` | 10-1000x |
| Loop numerici | NumPy broadcasting | 10-100x |
| CPU-bound | ProcessPoolExecutor | N_CPU x |
| I/O-bound | asyncio / threading | 10-50x |
| Molte istanze | `__slots__` | 2-3x memoria |
| Stringa + | `"".join()` | 10-100x |
| Liste grandi | Generatori | Infinite (streaming) |

## Prossimi passi

- `tutorial_33_profiling.md` — profilazione avanzata con py-spy e SnakeViz
- `tutorial_26_docker.md` — containerizzazione per ambienti riproducibili
