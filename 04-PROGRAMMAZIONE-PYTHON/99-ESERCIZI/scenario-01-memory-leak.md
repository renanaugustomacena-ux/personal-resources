# Scenario 01 — Memory Leak in Servizio FastAPI di Produzione

> **Modulo di riferimento:** [33-profiling-memoria-gc.md](../33-profiling-memoria-gc.md), [25-performance.md](../25-performance.md), [10-programmazione-asincrona.md](../10-programmazione-asincrona.md)
> **Tempo stimato:** 2-3 ore
> **Livello:** avanzato
> **Prerequisiti:** completamento moduli 10, 25, 33; familiarita con FastAPI e asyncio
> **Ultimo aggiornamento:** 2026-05-23

---

## Contesto

Un servizio FastAPI in produzione gestisce un'API di catalogo prodotti per un e-commerce.
Il servizio gira su Kubernetes (pod con `limits.memory: 512Mi`) e riceve circa 800 req/s.

Architettura:

```
Client -> nginx -> FastAPI (uvicorn, 4 worker) -> PostgreSQL
                                               -> Redis (session)
```

Il servizio implementa una cache in-memory per le risposte piu frequenti.
Il team ha sviluppato strutture dati custom per la gerarchia categorie-prodotti.

Il deploy e avvenuto 3 giorni fa. Da ieri, OOMKiller ha terminato 2 pod.

---

## Sintomi osservati

1. RSS dei pod cresce linearmente: ~180 MB al boot, ~460 MB dopo 12h
2. Il restart riporta a 180 MB, ma la crescita riprende immediatamente
3. Nessun errore nei log applicativi
4. Le metriche Prometheus mostrano response time stabile (p99 ~45ms)
5. `gc.get_count()` mostra gen-2 con migliaia di oggetti non raccolti

---

## Dati iniziali

### Grafico RSS (Prometheus/Grafana)

```
RSS Memory (MB)
460 |                                                    ___/
    |                                              ___/
400 |                                        ___/
    |                                  ___/
340 |                            ___/
    |                      ___/
280 |                ___/
    |          ___/
220 |    ___/
    | __/
180 |/
    +--+--+--+--+--+--+--+--+--+--+--+--+--> ore
    0  1  2  3  4  5  6  7  8  9  10 11 12
```

### Log excerpt (uvicorn)

```
2026-05-22 03:14:22 INFO     Started server process [1]
2026-05-22 03:14:22 INFO     Waiting for application startup.
2026-05-22 03:14:22 INFO     Application startup complete.
2026-05-22 15:27:01 WARNING  Process memory: 461MB (limit: 512MB)
2026-05-22 15:31:44 ERROR    Worker [1] killed by signal 9 (OOMKiller)
```

### Metriche GC (endpoint /debug/gc)

```json
{
  "gc_counts": [687, 12, 4203],
  "gc_threshold": [700, 10, 10],
  "gc_objects_tracked": 1847293,
  "gc_garbage_len": 0
}
```

Nota: `gc_counts[2]` (gen-2) a 4203 e anomalo. La soglia e 10, quindi
gen-2 ha gia eseguito 420 raccolte complete, ma gli oggetti tracked
crescono continuamente.

---

## Codice sorgente del servizio (versione buggata)

### app.py

```python
"""Servizio catalogo prodotti — versione con memory leak."""

from __future__ import annotations

import gc
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Catalogo Prodotti")

# ---- Cache in-memory SENZA eviction ----

_response_cache: dict[str, Any] = {}


class CategoryNode:
    """Nodo nella gerarchia categorie. BUG: riferimento circolare."""

    def __init__(self, name: str, parent: CategoryNode | None = None):
        self.name = name
        self.parent = parent            # ref verso il genitore
        self.children: list[CategoryNode] = []
        self.products: list[dict] = []
        self._cached_path: str | None = None

        if parent is not None:
            parent.children.append(self)    # il genitore referenzia il figlio

    def full_path(self) -> str:
        if self._cached_path is None:
            parts = []
            node: CategoryNode | None = self
            while node is not None:
                parts.append(node.name)
                node = node.parent
            self._cached_path = " > ".join(reversed(parts))
        return self._cached_path

    def __del__(self):
        # __del__ rende il ciclo NON collectable dal GC generazionale
        # perche CPython non puo determinare un ordine sicuro di finalizzazione
        print(f"Finalizing {self.name}")


class ProductDetail(BaseModel):
    id: int
    name: str
    price: float
    category_path: str


def _build_category_tree(raw: list[dict]) -> CategoryNode:
    """Costruisce albero categorie da dati DB. Crea riferimenti circolari."""
    root = CategoryNode("Root")
    node_map: dict[int, CategoryNode] = {0: root}
    for row in raw:
        parent = node_map.get(row["parent_id"], root)
        node = CategoryNode(row["name"], parent=parent)
        node.products = row.get("products", [])
        node_map[row["id"]] = node
    return root


async def _fetch_categories_from_db() -> list[dict]:
    """Simula query DB che ritorna gerarchia categorie."""
    # In produzione: SELECT * FROM categories JOIN products ...
    return [
        {"id": 1, "parent_id": 0, "name": "Elettronica",
         "products": [{"id": i, "name": f"Prod-{i}", "price": 9.99}
                      for i in range(200)]},
        {"id": 2, "parent_id": 1, "name": "Smartphone",
         "products": [{"id": i, "name": f"Phone-{i}", "price": 499.0}
                      for i in range(200, 500)]},
        {"id": 3, "parent_id": 1, "name": "Laptop",
         "products": [{"id": i, "name": f"Laptop-{i}", "price": 899.0}
                      for i in range(500, 800)]},
        {"id": 4, "parent_id": 0, "name": "Abbigliamento",
         "products": [{"id": i, "name": f"Cloth-{i}", "price": 29.99}
                      for i in range(800, 1200)]},
        {"id": 5, "parent_id": 4, "name": "Uomo",
         "products": [{"id": i, "name": f"M-{i}", "price": 39.99}
                      for i in range(1200, 1500)]},
    ]


@app.get("/api/v1/categories/{category_id}")
async def get_category(category_id: int):
    cache_key = f"cat:{category_id}"

    # BUG 1: cache che cresce all'infinito, mai eviction
    if cache_key not in _response_cache:
        raw = await _fetch_categories_from_db()
        tree = _build_category_tree(raw)       # BUG 2: cicli non collectable
        _response_cache[cache_key] = tree       # ogni variante di key aggiunge

    node = _response_cache[cache_key]
    return {"name": node.name, "path": node.full_path()}


@app.get("/api/v1/products/search")
async def search_products(q: str, page: int = 1):
    cache_key = f"search:{q}:{page}"

    # Ogni combinazione query+page genera una nuova entry
    if cache_key not in _response_cache:
        raw = await _fetch_categories_from_db()
        tree = _build_category_tree(raw)
        _response_cache[cache_key] = tree

    return {"query": q, "page": page, "results": []}


@app.get("/debug/gc")
async def debug_gc():
    return {
        "gc_counts": list(gc.get_count()),
        "gc_threshold": list(gc.get_threshold()),
        "gc_objects_tracked": len(gc.get_objects()),
        "gc_garbage_len": len(gc.garbage),
    }
```

---

## Domande guidate

Prima di consultare la soluzione, rispondi a queste domande:

### D1 — Identificazione del leak

Quanti problemi distinti causano la crescita di memoria? Elencali.

<details>
<summary>Suggerimento</summary>

Cerca due pattern: uno legato alla cache, uno legato al garbage collector.
Nota il metodo `__del__` e i riferimenti `parent`/`children`.

</details>

### D2 — Perche il GC non raccoglie?

Spiega perche `gc.collect()` non libera i `CategoryNode`, anche se
non ci sono piu riferimenti esterni all'albero.

<details>
<summary>Suggerimento</summary>

Consulta la documentazione CPython su `gc.garbage`: quando un oggetto
in un ciclo di riferimenti ha un finalizer (`__del__`), il GC lo
sposta in `gc.garbage` invece di deallocarlo (CPython < 3.4 comportamento).
Da Python 3.4+ i cicli con `__del__` vengono raccolti, ma il `__del__`
puo comunque causare problemi di ordine di finalizzazione e resurrezione.
Verifica se nel codice ci sono pattern che impediscono la raccolta.

</details>

### D3 — Dimensionamento

Se il servizio riceve 800 req/s e ogni albero occupa ~2 MB,
quanta memoria consuma la cache dopo 1 ora assumendo 10% di cache miss?

<details>
<summary>Suggerimento</summary>

800 req/s * 3600s * 0.10 miss rate = 288.000 entry.
Ma la chiave include la query string, quindi le combinazioni uniche
dipendono dalla cardinalita delle query. Anche con deduplicazione
parziale, centinaia di migliaia di alberi da 2 MB ciascuno sono letali.

</details>

### D4 — tracemalloc

Quale sequenza di comandi tracemalloc useresti per identificare
le linee di codice che allocano piu memoria tra due snapshot?

<details>
<summary>Suggerimento</summary>

`tracemalloc.start(25)` per catturare 25 frame di stack.
Snapshot prima e dopo N richieste, poi `snapshot2.compare_to(snapshot1, 'lineno')`.

</details>

### D5 — Soluzione

Proponi una fix che risolva entrambi i problemi.
Quali strutture dati della stdlib useresti?

<details>
<summary>Suggerimento</summary>

`functools.lru_cache` o `cachetools.TTLCache` per la cache con eviction.
`weakref.ref` o `weakref.WeakValueDictionary` per rompere i cicli.

</details>

---

## Diagnosi passo-passo

### Passo 1 — Abilitare tracemalloc in produzione

Aggiungere variabile d'ambiente al deployment:

```yaml
# kubernetes deployment.yaml (excerpt)
env:
  - name: PYTHONTRACEMALLOC
    value: "25"
```

Oppure programmaticamente all'avvio:

```python
import tracemalloc
tracemalloc.start(25)
```

### Passo 2 — Endpoint di diagnostica

```python
import tracemalloc
import linecache

_snapshot_baseline: tracemalloc.Snapshot | None = None


@app.get("/debug/memory/baseline")
async def memory_baseline():
    global _snapshot_baseline
    _snapshot_baseline = tracemalloc.take_snapshot()
    return {"status": "baseline captured", "traced_memory": tracemalloc.get_traced_memory()}


@app.get("/debug/memory/diff")
async def memory_diff():
    if _snapshot_baseline is None:
        return {"error": "call /debug/memory/baseline first"}

    current = tracemalloc.take_snapshot()
    stats = current.compare_to(_snapshot_baseline, "lineno")
    top = []
    for stat in stats[:15]:
        top.append({
            "file": str(stat.traceback),
            "size_diff": stat.size_diff,
            "size": stat.size,
            "count_diff": stat.count_diff,
        })
    return {"top_allocations": top}
```

### Passo 3 — Output di tracemalloc (dopo 1000 richieste)

```
Top 15 differenze di allocazione:
 #1: app.py:86   +187.4 MiB   (918432 nuovi blocchi)
     tree = _build_category_tree(raw)
 #2: app.py:42   +94.2 MiB    (612001 nuovi blocchi)
     parent.children.append(self)
 #3: app.py:38   +47.1 MiB    (306000 nuovi blocchi)
     self.products: list[dict] = []
 #4: app.py:87   +23.5 MiB    (918432 nuovi blocchi)
     _response_cache[cache_key] = tree
```

Interpretazione: la riga 86 (`_build_category_tree`) e la riga 42
(`parent.children.append`) sono i principali allocatori.
La cache (`_response_cache`) conserva tutto indefinitamente.

### Passo 4 — Analisi con objgraph

```python
# Script di diagnostica (eseguire in shell interattiva o endpoint)
import objgraph
import gc

gc.collect()

# Trovare i tipi che crescono
objgraph.show_growth(limit=10)
```

Output tipico:

```
CategoryNode     918432   +918432
list             2341002  +1837201
dict             1456721  +1234001
```

Catena di riferimenti per un singolo `CategoryNode`:

```python
import io

obj = objgraph.by_type("CategoryNode")[0]

# Generare grafo dei riferimenti
objgraph.show_backrefs(
    obj,
    max_depth=5,
    filename="/tmp/category_refs.png",
)
```

Output del grafo (testuale):

```
CategoryNode("Smartphone")
  ^--- .children[1] --- CategoryNode("Elettronica")
  |                        ^--- .parent --- CategoryNode("Smartphone")  # CICLO!
  |                        ^--- .children[0] --- CategoryNode("Root")
  |                               ^--- _response_cache["cat:1"]
  ^--- .parent --- CategoryNode("Elettronica")   # CICLO CONFERMATO
```

Il ciclo `parent <-> children` impedisce al reference counting di
deallocare. Il `__del__` complica ulteriormente la raccolta.

### Passo 5 — Verifica con gc.garbage

```python
import gc

gc.set_debug(gc.DEBUG_SAVEALL)
gc.collect()

print(f"Oggetti non collectable: {len(gc.garbage)}")
print(f"Tipi: {set(type(o).__name__ for o in gc.garbage[:100])}")
```

```
Oggetti non collectable: 0
Tipi: set()
```

Da Python 3.4+ gli oggetti con `__del__` in cicli vengono raccolti
(PEP 442), ma il `__del__` causa overhead e potenziali side-effect
durante la finalizzazione. Il problema principale qui e la cache
che mantiene riferimenti forti, impedendo qualsiasi raccolta.

---

## Soluzione completa

### app_fixed.py

```python
"""Servizio catalogo prodotti — versione corretta."""

from __future__ import annotations

import gc
import weakref
from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Catalogo Prodotti")


# ---- FIX 1: CategoryNode senza cicli forti ----

class CategoryNode:
    """Nodo nella gerarchia categorie. Usa weakref per il parent."""

    __slots__ = ("name", "_parent_ref", "children", "products", "_cached_path")

    def __init__(self, name: str, parent: CategoryNode | None = None):
        self.name = name
        # FIX: weakref al parent rompe il ciclo forte
        self._parent_ref: weakref.ref[CategoryNode] | None = (
            weakref.ref(parent) if parent is not None else None
        )
        self.children: list[CategoryNode] = []
        self.products: list[dict] = []
        self._cached_path: str | None = None

        if parent is not None:
            parent.children.append(self)

    @property
    def parent(self) -> CategoryNode | None:
        if self._parent_ref is None:
            return None
        return self._parent_ref()   # deref weakref, puo ritornare None

    def full_path(self) -> str:
        if self._cached_path is None:
            parts: list[str] = []
            node: CategoryNode | None = self
            while node is not None:
                parts.append(node.name)
                node = node.parent
            self._cached_path = " > ".join(reversed(parts))
        return self._cached_path

    # FIX: rimosso __del__ — non necessario, causa problemi con GC


# ---- FIX 2: Cache con dimensione massima e TTL ----

# Opzione A: lru_cache per funzioni pure
# Opzione B: cachetools.TTLCache per dati con scadenza

from cachetools import TTLCache

# Max 1000 entry, TTL 300 secondi
_response_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=1000, ttl=300)


async def _fetch_categories_from_db() -> list[dict]:
    """Simula query DB."""
    return [
        {"id": 1, "parent_id": 0, "name": "Elettronica",
         "products": [{"id": i, "name": f"Prod-{i}", "price": 9.99}
                      for i in range(200)]},
        {"id": 2, "parent_id": 1, "name": "Smartphone",
         "products": [{"id": i, "name": f"Phone-{i}", "price": 499.0}
                      for i in range(200, 500)]},
        {"id": 3, "parent_id": 1, "name": "Laptop",
         "products": [{"id": i, "name": f"Laptop-{i}", "price": 899.0}
                      for i in range(500, 800)]},
        {"id": 4, "parent_id": 0, "name": "Abbigliamento",
         "products": [{"id": i, "name": f"Cloth-{i}", "price": 29.99}
                      for i in range(800, 1200)]},
        {"id": 5, "parent_id": 4, "name": "Uomo",
         "products": [{"id": i, "name": f"M-{i}", "price": 39.99}
                      for i in range(1200, 1500)]},
    ]


def _build_category_tree(raw: list[dict]) -> CategoryNode:
    """Costruisce albero categorie. Niente cicli forti grazie a weakref."""
    root = CategoryNode("Root")
    node_map: dict[int, CategoryNode] = {0: root}
    for row in raw:
        parent = node_map.get(row["parent_id"], root)
        node = CategoryNode(row["name"], parent=parent)
        node.products = row.get("products", [])
        node_map[row["id"]] = node
    return root


def _serialize_tree(node: CategoryNode) -> dict[str, Any]:
    """Serializza il risultato — cache memorizza dati, non oggetti live."""
    return {
        "name": node.name,
        "path": node.full_path(),
        "children_count": len(node.children),
    }


@app.get("/api/v1/categories/{category_id}")
async def get_category(category_id: int):
    cache_key = f"cat:{category_id}"

    if cache_key not in _response_cache:
        raw = await _fetch_categories_from_db()
        tree = _build_category_tree(raw)
        # FIX: cache memorizza il dict serializzato, non l'albero
        _response_cache[cache_key] = _serialize_tree(tree)
        # tree esce dallo scope e viene deallocato (niente cicli forti)

    return _response_cache[cache_key]


@app.get("/api/v1/products/search")
async def search_products(q: str, page: int = 1):
    # FIX: normalizzare la chiave per ridurre cardinalita
    cache_key = f"search:{q.lower().strip()}:{page}"

    if cache_key not in _response_cache:
        raw = await _fetch_categories_from_db()
        tree = _build_category_tree(raw)
        _response_cache[cache_key] = _serialize_tree(tree)

    return {"query": q, "page": page, "results": _response_cache[cache_key]}


@app.get("/debug/gc")
async def debug_gc():
    gc.collect()
    return {
        "gc_counts": list(gc.get_count()),
        "gc_threshold": list(gc.get_threshold()),
        "gc_objects_tracked": len(gc.get_objects()),
        "gc_garbage_len": len(gc.garbage),
        "cache_size": len(_response_cache),
        "cache_maxsize": _response_cache.maxsize,
        "cache_currsize": _response_cache.currsize,
    }
```

### Differenze chiave

| Aspetto | Prima (bug) | Dopo (fix) |
|---------|-------------|------------|
| Cache | `dict` senza limiti | `TTLCache(maxsize=1000, ttl=300)` |
| Riferimento parent | `self.parent = parent` (forte) | `weakref.ref(parent)` |
| `__del__` | Presente, interferisce con GC | Rimosso |
| Dati in cache | Oggetto `CategoryNode` live | `dict` serializzato |
| Memory layout | Attributi dinamici (`__dict__`) | `__slots__` per efficienza |
| Chiave cache search | Case-sensitive, non normalizzata | `q.lower().strip()` |

---

## Verifica

### Script di test per confermare la fix

```python
"""Test: verifica che la memoria si stabilizzi dopo la fix."""

import asyncio
import tracemalloc
import gc

tracemalloc.start()


async def simulate_load():
    from app_fixed import app
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Warmup
        for i in range(100):
            await client.get(f"/api/v1/categories/{i % 10}")
            await client.get(f"/api/v1/products/search?q=test{i}&page=1")

        snapshot_before = tracemalloc.take_snapshot()
        gc.collect()
        mem_before = tracemalloc.get_traced_memory()[0]

        # Carico sostenuto
        for i in range(5000):
            await client.get(f"/api/v1/categories/{i % 10}")
            await client.get(f"/api/v1/products/search?q=query{i % 50}&page={i % 5}")

        gc.collect()
        snapshot_after = tracemalloc.take_snapshot()
        mem_after = tracemalloc.get_traced_memory()[0]

        delta_mb = (mem_after - mem_before) / (1024 * 1024)
        print(f"Memoria prima:  {mem_before / (1024*1024):.1f} MB")
        print(f"Memoria dopo:   {mem_after / (1024*1024):.1f} MB")
        print(f"Delta:          {delta_mb:.1f} MB")

        # La cache ha maxsize=1000, quindi la memoria deve stabilizzarsi
        assert delta_mb < 10, f"Leak non risolto: delta {delta_mb:.1f} MB"

        # Verificare che non ci siano CategoryNode residui
        import objgraph
        count = objgraph.count("CategoryNode")
        print(f"CategoryNode residui: {count}")
        # Con la fix, gli alberi non in cache vengono deallocati
        assert count < 100, f"Troppi CategoryNode residui: {count}"

        print("PASS: memoria stabile, nessun leak rilevato")


asyncio.run(simulate_load())
```

### Output atteso dopo la fix

```
Memoria prima:  12.3 MB
Memoria dopo:   14.1 MB
Delta:          1.8 MB
CategoryNode residui: 6
PASS: memoria stabile, nessun leak rilevato
```

### Confronto Grafana dopo il deploy

```
RSS Memory (MB) — dopo fix
220 |
    |    ___________________________________________
200 | __/
    |/
180 |
    +--+--+--+--+--+--+--+--+--+--+--+--+--> ore
    0  1  2  3  4  5  6  7  8  9  10 11 12
```

La memoria si stabilizza intorno a 200 MB dopo il warmup della cache.

---

## Lezioni apprese

### 1. Cache senza eviction = memory leak garantito

Una `dict` globale usata come cache senza `maxsize` o TTL cresce
senza limiti. Soluzioni:

- `functools.lru_cache(maxsize=N)` per funzioni pure
- `cachetools.TTLCache` o `cachetools.LRUCache` per cache manuali
- Redis/Memcached per cache condivisa tra processi

### 2. Riferimenti circolari + `__del__` = pericolo

Il reference counting di CPython non gestisce i cicli. Il GC
generazionale li raccoglie, ma `__del__` introduce complicazioni:

- Pre-3.4: cicli con `__del__` erano non collectable (`gc.garbage`)
- Post-3.4 (PEP 442): vengono raccolti, ma ordine di finalizzazione
  non determinabile puo causare bug sottili
- Best practice: usare `weakref` per rompere cicli, evitare `__del__`
  (preferire context manager o `atexit`)

### 3. Cache l'output serializzato, non l'oggetto live

Memorizzare in cache l'oggetto originale mantiene in vita tutto il
grafo di riferimenti. Serializzare (dict, JSON) e cachare il risultato
permette al GC di deallocare le strutture intermedie.

### 4. `__slots__` riduce il footprint

`__slots__` elimina `__dict__` per-istanza, risparmiando ~50-100 byte
per oggetto. Su milioni di istanze, il risparmio e significativo.

### 5. Strumenti di diagnostica

| Strumento | Uso |
|-----------|-----|
| `tracemalloc` | Identificare le linee che allocano piu memoria |
| `objgraph` | Visualizzare catene di riferimenti e cicli |
| `gc.get_count()` | Monitorare pressione sul GC generazionale |
| `gc.set_debug(gc.DEBUG_STATS)` | Log dettagliato delle raccolte GC |
| `pympler.muppy` | Panoramica di tutti gli oggetti in memoria |
| `memray` | Profiler di memoria con timeline visuale |

### 6. Monitoring proattivo

Aggiungere metriche Prometheus per:

```python
from prometheus_client import Gauge

CACHE_SIZE = Gauge("app_cache_entries", "Number of cached entries")
CACHE_MEMORY = Gauge("app_cache_memory_bytes", "Estimated cache memory")
GC_COLLECTIONS = Gauge("app_gc_collections", "GC collection count", ["generation"])
```

Configurare alert su crescita lineare di RSS e su `gc_objects_tracked`
che supera una soglia ragionevole.

---

## Riferimenti

- [Modulo 33 — Profiling memoria e GC](../33-profiling-memoria-gc.md): tracemalloc, objgraph, gc module
- [Modulo 25 — Performance](../25-performance.md): profiling workflow, ottimizzazione
- [Modulo 10 — Programmazione asincrona](../10-programmazione-asincrona.md): FastAPI, uvicorn, asyncio
- PEP 442 — Safe object finalization
- CPython source: `Modules/gcmodule.c` per dettagli implementativi del GC
- `cachetools` documentazione: tipi di cache con policy di eviction
