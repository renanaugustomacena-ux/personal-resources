# Tutorial 33 — Profiling Avanzato in Python: py-spy, Austin, SnakeViz

> **Companion a:** `33-profiling.md`
> **Scope:** py-spy, Austin, SnakeViz, memory-profiler, tracemalloc, profiling in produzione
> **Prerequisiti:** `tutorial_25_performance.md`, `tutorial_26_docker.md`
> **Durata stimata:** 10-14 ore

---

## Mappa concettuale

```
Profiling avanzato Python
│
├── Profiler sampling (basso overhead, produzione)
│   ├── py-spy — flame graph, nessuna modifica codice
│   └── Austin — flame graph ultra-veloce
│
├── Profiler deterministici (sviluppo)
│   ├── cProfile — conteggio chiamate e tempo
│   ├── line_profiler (@profile) — riga per riga
│   └── SnakeViz — visualizzazione cProfile
│
├── Memory profiling
│   ├── tracemalloc — allocazioni Python
│   ├── memory-profiler — RSS per riga
│   ├── objgraph — reference graph, leak detection
│   └── pympler — dimensione oggetti precisa
│
├── Profiling asincrono
│   ├── py-spy su asyncio — funziona!
│   └── aiomonitor — live introspection event loop
│
└── Workflow di ottimizzazione
    ├── Misura baseline
    ├── Identifica collo di bottiglia
    ├── Ottimizza UN punto alla volta
    └── Verifica miglioramento
```

---

# Parte A — py-spy: profiler di produzione

---

## A1. Flame graph senza modifiche al codice

```bash
# Installazione (root non richiesto su Linux con SYS_PTRACE)
pip install py-spy

# Profile di un processo in esecuzione
# Trova il PID: ps aux | grep python
py-spy record -o profile.svg --pid 12345 --duration 30

# Profila un nuovo processo
py-spy record -o profile.svg -- python mio_script.py

# Top live (come top per Python)
py-spy top --pid 12345

# Dump dello stack in questo momento
py-spy dump --pid 12345

# Profiling in Docker
docker exec -it mio-container py-spy record \
  -o /tmp/profile.svg \
  --pid $(pgrep -n python) \
  --duration 60

# Configurazione per produzione Docker (Dockerfile)
# Aggiungi SYS_PTRACE capability al container
# docker run --cap-add SYS_PTRACE ...
```

> **Analogia:** py-spy è come fare una radiografia a un paziente che cammina — non devi fermare il paziente (il processo Python) per vedere cosa succede dentro. Campiona lo stack trace 100 volte al secondo e produce un flame graph dove la larghezza di ogni barra indica quanto tempo viene speso in quella funzione.

---

## A2. Interpretare il flame graph

```
Flame graph — lettura:
│
├── Asse X — percentuale del tempo totale (non è cronologico!)
├── Asse Y — depth dello stack (basso = caller, alto = callee)
├── Larghezza blocco = % tempo speso in quella funzione (incluso callee)
│
├── CERCA:
│   ├── Blocchi larghi in alto → funzioni lente foglia
│   ├── Blocchi larghi in basso → chiamanti costosi
│   └── "Plateau" larghi → dove il tempo sta davvero
│
└── IGNORA:
    ├── Funzioni in cima ma strette → veloci
    └── main() largo ma tutto delegato → OK
```

```python
# Script da profilare
import time
import random

def sort_grosso():
    dati = [random.random() for _ in range(1_000_000)]
    return sorted(dati)

def somma_inutile():
    return sum(i**2 for i in range(500_000))

def lavoro_principale():
    for _ in range(10):
        sort_grosso()     # questo occupa ~70% del tempo
        somma_inutile()   # questo ~30%

if __name__ == "__main__":
    lavoro_principale()

# py-spy record -o profile.svg -- python script.py
# Apri profile.svg nel browser
# sort_grosso() sarà la barra più larga
```

---

# Parte B — cProfile + SnakeViz

---

## B1. cProfile per analisi dettagliata

```python
import cProfile
import pstats
import io

def analizza_con_cprofile(funzione, *args, **kwargs):
    """Profilazione con output formattato."""
    pr = cProfile.Profile()
    pr.enable()
    risultato = funzione(*args, **kwargs)
    pr.disable()

    stream = io.StringIO()
    stats = pstats.Stats(pr, stream=stream)

    # Ordina per tempo cumulativo (funzioni più costose in cima)
    stats.sort_stats("cumulative")
    stats.print_stats(20)

    print("=== Top 20 funzioni per tempo cumulativo ===")
    print(stream.getvalue())

    # Salva per SnakeViz
    pr.dump_stats("profile.prof")

    return risultato

# SnakeViz — visualizzazione interattiva web
# pip install snakeviz
# snakeviz profile.prof
# Apre http://localhost:8080 con sunburst e icicle chart interattivi
```

---

# Parte C — Memory profiling

---

## C1. tracemalloc: trovare memory leak

```python
import tracemalloc
import gc

class Leaker:
    """Classe che crea un memory leak (riferimento circolare)."""
    def __init__(self, nome: str) -> None:
        self.nome = nome
        self.ref = None   # verrà usato per creare ciclo

def crea_leak():
    oggetti = []
    for i in range(1000):
        a = Leaker(f"a-{i}")
        b = Leaker(f"b-{i}")
        a.ref = b    # a → b
        b.ref = a    # b → a (ciclo!)
        oggetti.append(a)
    return oggetti

# Profiling con tracemalloc
tracemalloc.start()

# Prendi snapshot baseline
snapshot1 = tracemalloc.take_snapshot()

_ = crea_leak()

# Forza garbage collection
gc.collect()

snapshot2 = tracemalloc.take_snapshot()

# Confronta i due snapshot
top_stats = snapshot2.compare_to(snapshot1, "lineno")
print("Top 10 allocazioni:")
for stat in top_stats[:10]:
    print(f"  {stat}")

# Usa tracemalloc per trovare dove vengono creati oggetti
tracemalloc.stop()
```

---

## C2. objgraph: visualizzare reference graph

```python
# pip install objgraph
import objgraph
import gc

def conta_oggetti():
    """Mostra i tipi di oggetti più comuni in memoria."""
    objgraph.show_most_common_types(limit=15)

def trova_crescita():
    """Trova tipi di oggetti che sono cresciuti."""
    # Esegui del codice
    oggetti_prima = objgraph.growth()
    # ... esegui operazioni
    oggetti_dopo = objgraph.growth()
    return [(tipo, n, delta) for tipo, n, delta in oggetti_dopo if delta > 0]

def traccia_riferimenti(oggetto):
    """Crea un grafo di tutti i riferimenti a un oggetto."""
    objgraph.show_backrefs(
        oggetto,
        max_depth=5,
        filename="backrefs.png",
    )

# Memory profiling continuo
import linecache
import os

def mostra_top_allocazioni():
    """Mostra le 10 linee di codice che allocano di più."""
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    for stat in top_stats[:10]:
        frame = stat.traceback[0]
        filename = frame.filename
        lineno = frame.lineno
        line = linecache.getline(filename, lineno).strip()
        print(f"{stat.size / 1024:.1f} KiB — {filename}:{lineno}: {line}")
```

---

# Parte D — Profiling asincrono

---

## D1. py-spy su applicazioni asyncio

```python
# py-spy funziona con asyncio senza problemi
# Il flame graph mostrerà coroutine come funzioni normali

# aiomonitor: live introspection dell'event loop
# pip install aiomonitor

import asyncio
import aiomonitor

async def worker(n: int) -> None:
    await asyncio.sleep(n * 0.1)
    return n

async def main():
    # Avvia aiomonitor su porta 50101
    with aiomonitor.start_monitor(loop=asyncio.get_event_loop()):
        tasks = [asyncio.create_task(worker(i)) for i in range(100)]
        await asyncio.gather(*tasks)

asyncio.run(main())
# Poi: telnet localhost 50101
# Comandi: help, ps, where, cancel <id>
```

---

# Parte E — Workflow di ottimizzazione

---

## E1. Processo sistematico

```python
import time
import statistics
from typing import Callable

def benchmark(fn: Callable, *args, n: int = 10, **kwargs) -> dict:
    """Benchmark ripetuto per misura stabile."""
    tempi = []
    for _ in range(n):
        inizio = time.perf_counter()
        fn(*args, **kwargs)
        tempi.append(time.perf_counter() - inizio)

    return {
        "media_ms": statistics.mean(tempi) * 1000,
        "mediana_ms": statistics.median(tempi) * 1000,
        "stdev_ms": statistics.stdev(tempi) * 1000,
        "min_ms": min(tempi) * 1000,
        "max_ms": max(tempi) * 1000,
    }

# 1. Misura baseline
def implementazione_originale(dati: list) -> list:
    risultato = []
    for x in dati:
        if x > 0:
            risultato.append(x * 2)
    return risultato

# 2. Implementa ottimizzazione
def implementazione_ottimizzata(dati: list) -> list:
    return [x * 2 for x in dati if x > 0]   # list comprehension

# 3. Confronto
dati = list(range(-500, 500))
baseline = benchmark(implementazione_originale, dati)
ottimizzata = benchmark(implementazione_ottimizzata, dati)

print(f"Baseline: {baseline['mediana_ms']:.3f}ms")
print(f"Ottimizzata: {ottimizzata['mediana_ms']:.3f}ms")
speedup = baseline['mediana_ms'] / ottimizzata['mediana_ms']
print(f"Speedup: {speedup:.1f}x")
```

---

## Riepilogo

## Strumenti per scenario

| Scenario | Strumento | Perché |
|---|---|---|
| Codice lento in sviluppo | cProfile + SnakeViz | Dettaglio funzione per funzione |
| Produzione senza fermare il processo | py-spy | Zero overhead, PID attach |
| Riga per riga | line_profiler | Pinpoint esatto |
| Memory leak | tracemalloc + objgraph | Visualizza riferimenti |
| RSS crescente nel tempo | memory-profiler | Plot RSS vs tempo |
| Asyncio lento | py-spy + aiomonitor | Funziona con coroutine |

## Regole d'oro profiling

1. **Misura sempre** prima e dopo — numeri, non sensazioni
2. **Usa dati realistici** — benchmark con dati toy inganna
3. **Ottimizza un collo di bottiglia alla volta** — evita di confondere le misure
4. **Ferma quando hai abbastanza** — il 20% del tempo dà l'80% dei guadagni
5. **La leggibilità viene prima** — non sacrificare il codice pulito per microottimizzazioni

Con questo tutorial si conclude il percorso completo del campo `04-PROGRAMMAZIONE-PYTHON`.
