---
corso: "Programmazione Python"
fase: "2 — Intermedio-Avanzato"
modulo: "04"
titolo: "Decoratori, Generatori e Context Manager"
versione: "Python 3.12+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti del Linguaggio"
  - "03 — Funzioni e Scope"
  - "02 — OOP"
obiettivi:
  - "Padroneggiare il pattern decorator in tutte le sue forme"
  - "Comprendere gli internals dei generatori inclusi send/throw/close"
  - "Utilizzare yield from per delegazione a sotto-generatori"
  - "Sfruttare itertools per pipeline efficienti in memoria"
  - "Implementare context manager con protocollo e contextlib"
  - "Combinare i tre pattern in architetture di produzione"
tag: [decoratori, generatori, context-manager, itertools, yield-from, functools, contextlib]
---

# Decoratori, Generatori e Context Manager — Guida Completa

> **Modulo 04** · **Aggiornamento:** 2026-05-24 · **Versione:** Python 3.12+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti](01-fondamenti-linguaggio.md), [Funzioni e Scope](03-funzioni-scope.md), [OOP](02-oop.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare il pattern decorator in tutte le sue forme: funzionale, parametrico, class-based, stacking
> 2. Comprendere gli internals dei generatori inclusi `send()`, `throw()`, `close()` e il protocollo coroutine
> 3. Utilizzare `yield from` per la delegazione a sotto-generatori con gestione del valore di ritorno
> 4. Sfruttare `itertools` per pipeline di dati composte ed efficienti in memoria
> 5. Implementare context manager sia tramite protocollo `__enter__`/`__exit__` sia tramite `contextlib`
> 6. Combinare i tre pattern in architetture di produzione: pipeline, middleware, resource management
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Mappa concettuale

```
                      ┌─────────────────────────────────────────────┐
                      │        META-PROGRAMMING PYTHON              │
                      └────────────────────┬────────────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
     ┌────────────────┐          ┌──────────────────┐         ┌────────────────┐
     │   DECORATORI   │          │   GENERATORI     │         │ CONTEXT MANAGER│
     │                │          │                  │         │                │
     │ @functools.wraps│         │ yield / yield    │         │ __enter__      │
     │ closure pattern│          │ from             │         │ __exit__       │
     │ __call__       │          │ send/throw/close │         │ @contextmanager│
     └───────┬────────┘          └────────┬─────────┘         └───────┬────────┘
             │                            │                           │
     ┌───────┴────────┐          ┌────────┴─────────┐         ┌───────┴────────┐
     │  Funzionali    │          │  Lazy evaluation  │         │  contextlib    │
     │  Parametrici   │          │  Pipeline dati    │         │  ExitStack     │
     │  Class-based   │          │  itertools        │         │  suppress      │
     │  Stacking      │          │  Async generators │         │  Async CM      │
     └────────────────┘          └──────────────────┘         └────────────────┘
              │                            │                           │
              └────────────────────────────┼───────────────────────────┘
                                           ▼
                              ┌──────────────────────┐
                              │   COMPOSIZIONE       │
                              │                      │
                              │ Decorator + CM       │
                              │ Generator + Decorator│
                              │ Pipeline completa    │
                              └──────────────────────┘
```

## Idee guida
1. **`@functools.wraps` mandatory in decorator.** Preserve metadata.
2. **Generators per lazy evaluation; memory-efficient.**
3. **`contextlib.contextmanager` decorator per CM rapidi.**
4. **`async with` per async context manager.**


## Indice

1. [Panoramica](#panoramica)
2. [Decoratori](#decoratori)
   - [Fondamenti](#fondamenti)
   - [Decoratori con Argomenti](#decoratori-con-argomenti)
   - [Decoratori Pratici](#decoratori-pratici)
   - [Decoratori di Classe](#decoratori-di-classe)
   - [Stacking Decoratori](#stacking-decoratori)
   - [Decorator Stack: Ordine di Esecuzione e Interazione con wraps](#decorator-stack-ordine-di-esecuzione-e-interazione-con-wraps)
   - [Decoratori Class-Based Avanzati](#decoratori-class-based-avanzati)
   - [Decoratori Parametrici: Factory Pattern e Parametri Opzionali](#decoratori-parametrici-factory-pattern-e-parametri-opzionali)
3. [Generatori](#generatori)
   - [Fondamenti dei Generatori](#fondamenti-dei-generatori)
   - [Generator Expressions](#generator-expressions)
   - [yield from](#yield-from)
   - [Generatori Pratici](#generatori-pratici)
   - [Generatori Bidirezionali](#generatori-bidirezionali)
   - [Generator Internals: send(), throw(), close()](#generator-internals-send-throw-close)
   - [yield from: Delegazione Avanzata e Valore di Ritorno](#yield-from-delegazione-avanzata-e-valore-di-ritorno)
   - [Generatori Asincroni](#generatori-asincroni)
4. [Iteratori](#iteratori)
   - [Protocollo Iterator](#protocollo-iterator)
   - [itertools Deep Dive](#itertools-deep-dive)
   - [itertools Avanzato: accumulate, chain.from_iterable, batched](#itertools-avanzato-accumulate-chainfrom_iterable-batched)
5. [Context Manager](#context-manager)
   - [Fondamenti dei Context Manager](#fondamenti-dei-context-manager)
   - [contextlib](#contextlib)
   - [Context Manager Pratici](#context-manager-pratici)
   - [Async Context Manager](#async-context-manager)
   - [Context Manager Protocol: Gestione Eccezioni Avanzata](#context-manager-protocol-gestione-eccezioni-avanzata)
   - [contextlib Avanzato: ExitStack, AsyncExitStack, aclosing](#contextlib-avanzato-exitstack-asyncexitstack-aclosing)
6. [Combinare i Pattern](#combinare-i-pattern)
7. [Pattern Pratici di Produzione](#pattern-pratici-di-produzione)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Esercizi](#esercizi)
11. [Letture e Riferimenti](#letture-e-riferimenti)
12. [Cross-link](#cross-link)
13. [Glossario](#glossario)

---

## Panoramica

Decoratori, generatori e context manager rappresentano tre dei pattern piu potenti e idiomatici offerti da Python. Ciascuno di essi affronta un problema distinto — la modifica del comportamento di funzioni e classi, la produzione pigra di sequenze di valori e la gestione sicura di risorse — ma condividono una filosofia comune: rendere il codice piu leggibile, riutilizzabile e robusto senza sacrificare la semplicita.

I **decoratori** permettono di estendere o alterare il comportamento di funzioni e classi in modo dichiarativo, senza modificare il codice sorgente originale. Sono fondamentali per l'applicazione trasversale di logica come logging, caching, autenticazione e validazione.

I **generatori** introducono il concetto di valutazione lazy: producono valori uno alla volta, su richiesta, evitando di caricare in memoria intere sequenze. Questo li rende indispensabili quando si lavora con dataset di grandi dimensioni, stream infiniti o pipeline di elaborazione dati.

I **context manager** garantiscono che le risorse — file, connessioni a database, lock — vengano acquisite e rilasciate in modo prevedibile e sicuro, anche in presenza di eccezioni. Il costrutto `with` e diventato il modo standard in Python per gestire qualsiasi risorsa che richieda setup e teardown espliciti.

Questa guida esplora ciascun pattern in profondita, partendo dai fondamenti teorici fino ad arrivare a implementazioni pratiche pronte per la produzione. Alla fine del percorso vedremo come questi tre pattern possano essere combinati per creare soluzioni eleganti e potenti.

---

## Decoratori

### Fondamenti

#### Funzioni come Oggetti di Prima Classe

In Python le funzioni sono oggetti di prima classe (first-class objects). Cio significa che possono essere assegnate a variabili, passate come argomenti ad altre funzioni, restituite da funzioni e memorizzate in strutture dati.

```python
def saluta(nome):
    return f"Ciao, {nome}!"

# Assegnazione a variabile
mia_funzione = saluta
print(mia_funzione("Marco"))  # Ciao, Marco!

# Passaggio come argomento
def esegui(func, valore):
    return func(valore)

print(esegui(saluta, "Anna"))  # Ciao, Anna!

# Restituzione da funzione
def crea_saluto(prefisso):
    def saluta_con_prefisso(nome):
        return f"{prefisso}, {nome}!"
    return saluta_con_prefisso

saluto_formale = crea_saluto("Buongiorno")
print(saluto_formale("Dottore"))  # Buongiorno, Dottore!
```

Questa proprieta e il fondamento su cui si costruiscono i decoratori.

#### Ripasso sulle Closures

Una closure si verifica quando una funzione interna cattura e ricorda le variabili dell'ambiente in cui e stata definita, anche dopo che la funzione esterna ha terminato la propria esecuzione.

```python
def contatore(inizio=0):
    conteggio = inizio
    def incrementa():
        nonlocal conteggio
        conteggio += 1
        return conteggio
    return incrementa

conta = contatore(10)
print(conta())  # 11
print(conta())  # 12
print(conta())  # 13
```

La funzione `incrementa` e una closure: mantiene un riferimento a `conteggio` anche dopo che `contatore` ha restituito il risultato.

#### Decoratore Semplice (Wrapper Function)

Un decoratore e una funzione che accetta una funzione come argomento e restituisce una nuova funzione che tipicamente estende il comportamento di quella originale.

```python
def mio_decoratore(func):
    def wrapper(*args, **kwargs):
        print(f"Prima di chiamare {func.__name__}")
        risultato = func(*args, **kwargs)
        print(f"Dopo aver chiamato {func.__name__}")
        return risultato
    return wrapper

def somma(a, b):
    return a + b

# Applicazione manuale del decoratore
somma_decorata = mio_decoratore(somma)
print(somma_decorata(3, 5))
# Prima di chiamare somma
# Dopo aver chiamato somma
# 8
```

#### Syntactic Sugar con @

Python offre una sintassi abbreviata per applicare i decoratori: il simbolo `@` posto immediatamente prima della definizione della funzione.

```python
@mio_decoratore
def moltiplica(a, b):
    return a * b

# Equivale esattamente a:
# moltiplica = mio_decoratore(moltiplica)

print(moltiplica(4, 6))
# Prima di chiamare moltiplica
# Dopo aver chiamato moltiplica
# 24
```

La forma `@decoratore` e esclusivamente syntactic sugar: non introduce alcun meccanismo nuovo, ma rende il codice significativamente piu leggibile e dichiarativo.

---

### Decoratori con Argomenti

#### Pattern a Tre Livelli di Annidamento

Quando un decoratore deve accettare argomenti propri, e necessario aggiungere un ulteriore livello di annidamento. La funzione piu esterna accetta gli argomenti del decoratore, quella intermedia accetta la funzione da decorare, e quella piu interna (wrapper) gestisce gli argomenti della funzione decorata.

```python
def ripeti(n_volte):
    """Decoratore che esegue la funzione n_volte."""
    def decoratore(func):
        def wrapper(*args, **kwargs):
            risultati = []
            for _ in range(n_volte):
                risultato = func(*args, **kwargs)
                risultati.append(risultato)
            return risultati
        return wrapper
    return decoratore

@ripeti(n_volte=3)
def saluta(nome):
    print(f"Ciao {nome}!")
    return nome

saluta("Luca")
# Ciao Luca!
# Ciao Luca!
# Ciao Luca!
```

#### functools.wraps — Preservare i Metadati

Quando si applica un decoratore, la funzione originale viene sostituita dal wrapper. Questo causa la perdita dei metadati originali come `__name__`, `__doc__` e `__module__`. Il decoratore `functools.wraps` risolve questo problema copiando i metadati dalla funzione originale al wrapper.

```python
import functools

def mio_decoratore(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Documentazione del wrapper."""
        return func(*args, **kwargs)
    return wrapper

@mio_decoratore
def calcola_area(raggio):
    """Calcola l'area di un cerchio dato il raggio."""
    import math
    return math.pi * raggio ** 2

# Senza @wraps: calcola_area.__name__ == 'wrapper'
# Con @wraps: calcola_area.__name__ == 'calcola_area'
print(calcola_area.__name__)  # calcola_area
print(calcola_area.__doc__)   # Calcola l'area di un cerchio dato il raggio.
```

Utilizzare `@functools.wraps` e considerato una best practice irrinunciabile in qualsiasi decoratore di produzione.

---

### Decoratori Pratici

#### @timer — Misurazione del Tempo di Esecuzione

```python
import functools
import time

def timer(func):
    """Misura e stampa il tempo di esecuzione della funzione."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        risultato = func(*args, **kwargs)
        fine = time.perf_counter()
        durata = fine - inizio
        print(f"[TIMER] {func.__name__} eseguita in {durata:.4f} secondi")
        return risultato
    return wrapper

@timer
def ordina_lista(dimensione):
    """Crea e ordina una lista di numeri casuali."""
    import random
    dati = [random.randint(0, 1_000_000) for _ in range(dimensione)]
    return sorted(dati)

ordina_lista(500_000)
# [TIMER] ordina_lista eseguita in 0.3821 secondi
```

#### @retry — Riprova con Tentativi Massimi e Ritardo

```python
import functools
import time
import logging

logger = logging.getLogger(__name__)

def retry(max_retries=3, delay=1.0, eccezioni=(Exception,)):
    """Riprova la funzione in caso di eccezione.

    Args:
        max_retries: Numero massimo di tentativi.
        delay: Secondi di attesa tra un tentativo e l'altro.
        eccezioni: Tupla di eccezioni che attivano il retry.
    """
    def decoratore(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_errore = None
            for tentativo in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except eccezioni as e:
                    ultimo_errore = e
                    logger.warning(
                        f"[RETRY] {func.__name__} - Tentativo {tentativo}/{max_retries} "
                        f"fallito: {e}"
                    )
                    if tentativo < max_retries:
                        time.sleep(delay)
            raise ultimo_errore
        return wrapper
    return decoratore

@retry(max_retries=3, delay=0.5, eccezioni=(ConnectionError, TimeoutError))
def scarica_dati(url):
    """Simula il download di dati da un URL."""
    import random
    if random.random() < 0.7:
        raise ConnectionError(f"Impossibile connettersi a {url}")
    return {"status": "ok", "dati": [1, 2, 3]}
```

#### @cache / @lru_cache — Memoizzazione

```python
import functools

# Implementazione manuale di @cache
def cache(func):
    """Decoratore di memoizzazione semplice."""
    memo = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in memo:
            memo[args] = func(*args)
        return memo[args]
    wrapper.cache = memo
    wrapper.cache_clear = memo.clear
    return wrapper

@cache
def fibonacci(n):
    """Calcola il numero di Fibonacci n-esimo."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(100))  # 354224848179261915075
print(f"Elementi in cache: {len(fibonacci.cache)}")

# Uso di functools.lru_cache (dalla libreria standard)
@functools.lru_cache(maxsize=128)
def fattoriale(n):
    """Calcola il fattoriale con cache LRU."""
    if n <= 1:
        return 1
    return n * fattoriale(n - 1)

print(fattoriale(20))        # 2432902008176640000
print(fattoriale.cache_info())  # CacheInfo(hits=0, misses=21, maxsize=128, currsize=21)
```

A partire da Python 3.9, `functools.cache` offre una cache illimitata senza il parametro `maxsize`.

#### functools.cache vs lru_cache — Confronto Approfondito

Python offre due decoratori di memoizzazione nella libreria standard. Comprendere le differenze tra `functools.cache` (introdotto in Python 3.9, PEP 611) e `functools.lru_cache` (disponibile da Python 3.2) e essenziale per scegliere lo strumento giusto in ciascun contesto.

##### Architettura Interna

`functools.cache` e implementato internamente come `lru_cache(maxsize=None)`. La differenza cruciale e che, senza limite di dimensione, l'implementazione salta completamente la contabilita LRU (Least Recently Used): non mantiene una linked list per tracciare l'ordine di accesso, non esegue operazioni di riordinamento a ogni hit, e non confronta la dimensione corrente con un massimo. Questo si traduce in circa il 40% di velocita in piu sulle cache hit rispetto a `lru_cache` con maxsize impostato.

```python
import functools
import timeit

# functools.cache — cache illimitata, nessun overhead LRU
@functools.cache
def fibonacci_cache(n: int) -> int:
    if n < 2:
        return n
    return fibonacci_cache(n - 1) + fibonacci_cache(n - 2)

# functools.lru_cache — cache con limite e contabilita LRU
@functools.lru_cache(maxsize=256)
def fibonacci_lru(n: int) -> int:
    if n < 2:
        return n
    return fibonacci_lru(n - 1) + fibonacci_lru(n - 2)

# Benchmark (dopo il warm-up)
fibonacci_cache(100)
fibonacci_lru(100)

t_cache = timeit.timeit(lambda: fibonacci_cache(50), number=100_000)
t_lru = timeit.timeit(lambda: fibonacci_lru(50), number=100_000)
print(f"cache: {t_cache:.4f}s, lru_cache: {t_lru:.4f}s")
# cache risulta tipicamente ~30-40% piu veloce sulle hit
```

##### Quando Usare l'Uno o l'Altro

| Criterio | `functools.cache` | `functools.lru_cache(maxsize=N)` |
|----------|-------------------|-----------------------------------|
| Dimensione della cache | Illimitata (cresce senza limiti) | Limitata a `maxsize` entry |
| Eviction | Nessuna — tutti i risultati restano in memoria | LRU — i risultati meno recenti vengono rimossi |
| Overhead per hit | Minimo (~40% piu veloce) | Contabilita LRU a ogni accesso |
| Rischio memory leak | Si, se lo spazio degli input e ampio | No, la memoria e limitata da `maxsize` |
| `cache_info()` | Disponibile (hits, misses, currsize) | Disponibile (hits, misses, maxsize, currsize) |
| Thread safety | Si (GIL protegge il dict interno) | Si (lock dedicato) |
| Argomenti hashable | Obbligatorio | Obbligatorio |

```python
# REGOLA PRATICA:
# - @cache per algoritmi ricorsivi, spazi di input piccoli e finiti,
#   script a breve vita dove la memoria non e un vincolo
# - @lru_cache(maxsize=N) per servizi long-running, API, funzioni
#   con spazi di input potenzialmente infiniti

# Esempio: servizio long-running con lru_cache
@functools.lru_cache(maxsize=1024)
def cerca_utente(user_id: int) -> dict:
    """Cache con limite per un servizio che gira per ore/giorni."""
    return interroga_database(user_id)

# Esempio: script batch con cache
@functools.cache
def calcola_coefficiente(n: int, k: int) -> int:
    """Cache illimitata per script a vita breve."""
    if k == 0 or k == n:
        return 1
    return calcola_coefficiente(n - 1, k - 1) + calcola_coefficiente(n - 1, k)
```

##### typed=True in lru_cache

A partire da Python 3.8, `lru_cache` supporta il parametro `typed=True`, che tratta argomenti di tipo diverso come entry distinte nella cache. Questo e rilevante quando `f(3)` e `f(3.0)` dovrebbero restituire risultati diversi.

```python
@functools.lru_cache(maxsize=128, typed=True)
def formatta_valore(v):
    return f"{type(v).__name__}: {v}"

print(formatta_valore(3))    # "int: 3"
print(formatta_valore(3.0))  # "float: 3.0"  (entry separata in cache)
```

##### Confronto con cachetools (Terze Parti)

Per esigenze piu avanzate — TTL (Time-To-Live), politiche di eviction LFU (Least Frequently Used), cache con dimensioni basate sul peso degli elementi, o supporto asincrono — la libreria `cachetools` (licenza MIT, manutenzione attiva) estende il panorama. Non fa parte della libreria standard, ma e il riferimento de facto per caching avanzato in Python.

```python
# pip install cachetools
from cachetools import TTLCache, LFUCache, cached
import threading

# Cache con TTL: gli elementi scadono dopo 300 secondi
cache_ttl = TTLCache(maxsize=256, ttl=300)
lock = threading.Lock()

@cached(cache=cache_ttl, lock=lock)
def ottieni_prezzo(simbolo: str) -> float:
    """I prezzi scadono dalla cache dopo 5 minuti."""
    return chiama_api_borsa(simbolo)

# Cache LFU: rimuove gli elementi meno frequentemente usati
cache_lfu = LFUCache(maxsize=128)

@cached(cache=cache_lfu)
def traduci_termine(termine: str, lingua: str) -> str:
    """I termini piu usati restano in cache piu a lungo."""
    return chiama_servizio_traduzione(termine, lingua)
```

| Caratteristica | `functools.cache` | `functools.lru_cache` | `cachetools` |
|----------------|--------------------|-----------------------|--------------|
| Libreria | standard | standard | terze parti |
| TTL | No | No | Si (`TTLCache`) |
| LFU | No | No | Si (`LFUCache`) |
| Dimensione pesata | No | No | Si (parametro `getsizeof`) |
| Async nativo | No | No | Parziale (con lock async) |
| Thread safety built-in | Parziale (GIL) | Si (lock) | Si (parametro `lock`) |

#### @deprecated — Avviso di Funzione Obsoleta

```python
import functools
import warnings

def deprecated(motivo=""):
    """Segna una funzione come deprecata, emettendo un avviso al suo utilizzo."""
    def decoratore(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            messaggio = f"{func.__name__} e deprecata."
            if motivo:
                messaggio += f" {motivo}"
            warnings.warn(messaggio, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decoratore

@deprecated(motivo="Usare calcola_totale_v2() al suo posto.")
def calcola_totale(prezzi):
    """Calcola il totale dei prezzi."""
    return sum(prezzi)

# L'uso genera un warning:
# DeprecationWarning: calcola_totale e deprecata. Usare calcola_totale_v2() al suo posto.
totale = calcola_totale([10.5, 20.0, 15.75])
```

#### @validate_types — Controllo dei Tipi a Runtime

```python
import functools
import inspect

def validate_types(func):
    """Valida i tipi degli argomenti a runtime usando le type hints."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        hints = func.__annotations__
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        for nome_param, valore in bound.arguments.items():
            if nome_param in hints and nome_param != 'return':
                tipo_atteso = hints[nome_param]
                if not isinstance(valore, tipo_atteso):
                    raise TypeError(
                        f"Parametro '{nome_param}' di {func.__name__}: "
                        f"atteso {tipo_atteso.__name__}, "
                        f"ricevuto {type(valore).__name__}"
                    )

        risultato = func(*args, **kwargs)

        if 'return' in hints:
            tipo_ritorno = hints['return']
            if not isinstance(risultato, tipo_ritorno):
                raise TypeError(
                    f"Valore di ritorno di {func.__name__}: "
                    f"atteso {tipo_ritorno.__name__}, "
                    f"ricevuto {type(risultato).__name__}"
                )
        return risultato
    return wrapper

@validate_types
def somma_interi(a: int, b: int) -> int:
    return a + b

print(somma_interi(3, 5))    # 8
# somma_interi(3, "5")       # TypeError: Parametro 'b' di somma_interi: atteso int, ricevuto str
```

#### @log_calls — Logging delle Chiamate a Funzione

```python
import functools
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_calls(livello=logging.DEBUG):
    """Registra ogni chiamata alla funzione con argomenti e risultato."""
    def decoratore(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            firma = ", ".join(args_repr + kwargs_repr)
            logger.log(livello, f"Chiamata: {func.__name__}({firma})")
            try:
                risultato = func(*args, **kwargs)
                logger.log(livello, f"Ritorno: {func.__name__} -> {risultato!r}")
                return risultato
            except Exception as e:
                logger.exception(f"Eccezione in {func.__name__}: {e}")
                raise
        return wrapper
    return decoratore

@log_calls(livello=logging.INFO)
def dividi(a, b):
    return a / b

dividi(10, 3)
# INFO: Chiamata: dividi(10, 3)
# INFO: Ritorno: dividi -> 3.3333333333333335
```

#### @singleton — Decoratore di Classe

```python
import functools

def singleton(cls):
    """Garantisce che una classe abbia una sola istanza (Singleton pattern)."""
    istanze = {}
    @functools.wraps(cls, updated=[])
    def get_istanza(*args, **kwargs):
        if cls not in istanze:
            istanze[cls] = cls(*args, **kwargs)
        return istanze[cls]
    return get_istanza

@singleton
class DatabaseConfig:
    def __init__(self, host="localhost", porta=5432):
        self.host = host
        self.porta = porta
        print(f"Configurazione creata: {host}:{porta}")

config1 = DatabaseConfig("db.esempio.it", 3306)
# Configurazione creata: db.esempio.it:3306
config2 = DatabaseConfig()  # Non stampa nulla: restituisce l'istanza esistente
print(config1 is config2)   # True
```

#### @rate_limit — Limitazione della Frequenza di Chiamate API

```python
import functools
import time
from collections import deque

def rate_limit(max_chiamate, periodo_secondi):
    """Limita il numero di chiamate a una funzione entro un periodo di tempo."""
    def decoratore(func):
        chiamate = deque()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            adesso = time.monotonic()
            # Rimuovi le chiamate al di fuori della finestra temporale
            while chiamate and chiamate[0] <= adesso - periodo_secondi:
                chiamate.popleft()

            if len(chiamate) >= max_chiamate:
                tempo_attesa = periodo_secondi - (adesso - chiamate[0])
                raise RuntimeError(
                    f"Limite di frequenza superato per {func.__name__}. "
                    f"Riprova tra {tempo_attesa:.1f} secondi."
                )

            chiamate.append(adesso)
            return func(*args, **kwargs)
        return wrapper
    return decoratore

@rate_limit(max_chiamate=5, periodo_secondi=60)
def chiama_api(endpoint):
    """Simula una chiamata API con rate limiting."""
    return {"endpoint": endpoint, "status": 200}
```

---

### Decoratori con `__init_subclass__` — Alternativa ai Metaclass

#### Registrazione Automatica delle Sottoclassi (PEP 487)

Introdotto con PEP 487 in Python 3.6, `__init_subclass__` offre un meccanismo pulito per eseguire logica quando una classe viene creata come sottoclasse. E un'alternativa leggera ai metaclass per i casi d'uso piu comuni: registri di plugin, validazione di classi, e applicazione di vincoli strutturali.

```python
from typing import ClassVar

class PluginBase:
    """Base per un sistema di plugin con registrazione automatica."""
    _registro: ClassVar[dict[str, type]] = {}

    def __init_subclass__(cls, *, tipo_plugin: str = "", **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if tipo_plugin:
            cls._registro[tipo_plugin] = cls
            cls.tipo_plugin = tipo_plugin

    @classmethod
    def crea(cls, tipo: str, *args, **kwargs):
        """Factory method: crea un plugin per tipo registrato."""
        if tipo not in cls._registro:
            tipi = ", ".join(cls._registro.keys())
            raise ValueError(f"Plugin '{tipo}' sconosciuto. Disponibili: {tipi}")
        return cls._registro[tipo](*args, **kwargs)


class PluginCSV(PluginBase, tipo_plugin="csv"):
    def carica(self, percorso: str) -> list:
        return [f"riga da {percorso}"]


class PluginJSON(PluginBase, tipo_plugin="json"):
    def carica(self, percorso: str) -> dict:
        return {"fonte": percorso}


class PluginParquet(PluginBase, tipo_plugin="parquet"):
    def carica(self, percorso: str) -> list:
        return [{"colonna": "dati", "fonte": percorso}]


# La registrazione avviene automaticamente alla definizione della classe
plugin = PluginBase.crea("json")
print(plugin.carica("dati.json"))  # {'fonte': 'dati.json'}
print(PluginBase._registro)
# {'csv': <class 'PluginCSV'>, 'json': <class 'PluginJSON'>, 'parquet': <class 'PluginParquet'>}
```

#### Validazione di Interfaccia con `__init_subclass__`

Si puo usare `__init_subclass__` per imporre che le sottoclassi implementino determinati metodi o attributi, ottenendo un controllo simile alle Abstract Base Classes ma con messaggi di errore piu chiari e immediati (al momento della definizione della classe, non all'istanziazione):

```python
class Serializzabile:
    """Base che impone l'implementazione dei metodi di serializzazione."""

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        # Controlla solo classi concrete (non astratte intermedie)
        if not getattr(cls, '_astratta', False):
            metodi_richiesti = ('serializza', 'deserializza')
            mancanti = [m for m in metodi_richiesti if m not in cls.__dict__]
            if mancanti:
                raise TypeError(
                    f"{cls.__name__} deve implementare: {', '.join(mancanti)}"
                )

class Modello(Serializzabile):
    _astratta = True  # Classe intermedia, non validata


class Utente(Modello):
    def serializza(self) -> dict:
        return {"nome": self.nome}

    def deserializza(self, dati: dict) -> "Utente":
        self.nome = dati["nome"]
        return self

# class MalDefinita(Modello):
#     pass
# TypeError: MalDefinita deve implementare: serializza, deserializza
```

#### `__init_subclass__` vs Metaclass vs Decoratore di Classe

| Criterio | `__init_subclass__` | Metaclass | Decoratore di classe |
|----------|---------------------|-----------|---------------------|
| Complessita | Bassa | Alta | Bassa |
| Ereditarietà | Automatica | Automatica (conflitti possibili) | Non ereditato |
| Momento di esecuzione | Alla definizione della sottoclasse | Alla creazione della classe | Dopo la definizione della classe |
| Caso d'uso principale | Registri, hook semplici, validazione | Controllo totale sulla creazione | Trasformazione una-tantum |
| Compatibilità | Python 3.6+ | Tutte le versioni | Tutte le versioni |
| Conflitti multipli | Cooperativo con `super()` | Un solo metaclass per gerarchia | Composizione libera |

> **Regola pratica:** usare `__init_subclass__` quando serve un hook alla creazione delle sottoclassi. Ricorrere ai metaclass solo quando serve controllo sulla creazione della classe stessa (es. modifica del namespace della classe, intercettazione di `__new__`). Usare decoratori di classe per trasformazioni che non devono propagarsi alle sottoclassi.

---

### Decoratori di Classe

#### Classe come Decoratore (con `__call__`)

Una classe puo funzionare come decoratore se implementa il metodo `__call__`. Questo approccio e utile quando il decoratore deve mantenere uno stato interno complesso.

```python
import functools
import time

class ContaChiamate:
    """Decoratore che conta quante volte una funzione viene chiamata."""

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.num_chiamate = 0

    def __call__(self, *args, **kwargs):
        self.num_chiamate += 1
        print(f"{self.func.__name__} chiamata {self.num_chiamate} volta/e")
        return self.func(*args, **kwargs)

    def reset(self):
        self.num_chiamate = 0

@ContaChiamate
def processa_dati(dati):
    return [x * 2 for x in dati]

processa_dati([1, 2, 3])  # processa_dati chiamata 1 volta/e
processa_dati([4, 5, 6])  # processa_dati chiamata 2 volta/e
print(processa_dati.num_chiamate)  # 2
processa_dati.reset()
```

#### Decorare Classi

I decoratori non si applicano solo alle funzioni: possono anche decorare intere classi. L'esempio piu noto nella libreria standard e `@dataclass`.

```python
from dataclasses import dataclass

@dataclass
class Punto:
    x: float
    y: float
    z: float = 0.0

# @dataclass genera automaticamente __init__, __repr__, __eq__, ecc.
p = Punto(1.0, 2.0)
print(p)  # Punto(x=1.0, y=2.0, z=0.0)

# Decoratore di classe personalizzato
def aggiungi_repr(cls):
    """Aggiunge un metodo __repr__ leggibile a qualsiasi classe."""
    def __repr__(self):
        attributi = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items()
        )
        return f"{cls.__name__}({attributi})"
    cls.__repr__ = __repr__
    return cls

@aggiungi_repr
class Configurazione:
    def __init__(self, tema="chiaro", lingua="it"):
        self.tema = tema
        self.lingua = lingua

print(Configurazione())  # Configurazione(tema='chiaro', lingua='it')
```

#### Decoratori per Metodi: @staticmethod, @classmethod, @property

Python fornisce tre decoratori built-in fondamentali per i metodi delle classi.

```python
class Temperatura:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        """Getter per la temperatura in Celsius."""
        return self._celsius

    @celsius.setter
    def celsius(self, valore):
        if valore < -273.15:
            raise ValueError("La temperatura non puo essere inferiore allo zero assoluto")
        self._celsius = valore

    @property
    def fahrenheit(self):
        """Proprieta calcolata: Fahrenheit."""
        return self._celsius * 9 / 5 + 32

    @classmethod
    def da_fahrenheit(cls, f):
        """Metodo factory: crea un'istanza da gradi Fahrenheit."""
        return cls((f - 32) * 5 / 9)

    @staticmethod
    def e_valida(temperatura):
        """Verifica se una temperatura e fisicamente valida."""
        return temperatura >= -273.15

t = Temperatura(100)
print(t.fahrenheit)              # 212.0
t2 = Temperatura.da_fahrenheit(32)
print(t2.celsius)                # 0.0
print(Temperatura.e_valida(-300)) # False
```

---

### Stacking Decoratori

Quando si applicano piu decoratori a una stessa funzione, l'ordine di applicazione e dal basso verso l'alto (il decoratore piu vicino alla funzione viene applicato per primo), ma l'esecuzione avviene dall'alto verso il basso.

```python
def grassetto(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return f"<b>{func(*args, **kwargs)}</b>"
    return wrapper

def corsivo(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return f"<i>{func(*args, **kwargs)}</i>"
    return wrapper

@grassetto
@corsivo
def saluta(nome):
    return f"Ciao, {nome}"

# Equivale a: grassetto(corsivo(saluta))
print(saluta("Mondo"))  # <b><i>Ciao, Mondo</i></b>
```

Un pattern di stacking comune in produzione:

```python
@app.route("/api/utenti", methods=["GET"])
@richiedi_autenticazione
@rate_limit(max_chiamate=100, periodo_secondi=60)
@log_calls()
@timer
def lista_utenti():
    """Restituisce la lista degli utenti."""
    return get_tutti_utenti()
```

L'ordine e significativo: il routing deve essere il piu esterno, l'autenticazione prima del rate limiting, e il timer piu vicino alla funzione per misurare solo il suo tempo effettivo.

---

### Decorator Stack: Ordine di Esecuzione e Interazione con wraps

Quando si impilano piu decoratori, l'interazione con `functools.wraps` merita attenzione specifica. Ogni livello di decoratore crea un nuovo wrapper; senza `@wraps` a ogni livello, i metadati vengono persi progressivamente.

#### Visualizzare l'ordine di esecuzione

```python
import functools

def decoratore_a(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  [A] prima — func visibile: {func.__name__}")
        risultato = func(*args, **kwargs)
        print(f"  [A] dopo")
        return risultato
    return wrapper

def decoratore_b(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  [B] prima — func visibile: {func.__name__}")
        risultato = func(*args, **kwargs)
        print(f"  [B] dopo")
        return risultato
    return wrapper

def decoratore_c(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  [C] prima — func visibile: {func.__name__}")
        risultato = func(*args, **kwargs)
        print(f"  [C] dopo")
        return risultato
    return wrapper

@decoratore_a
@decoratore_b
@decoratore_c
def operazione():
    """Funzione target."""
    print("  [operazione] eseguita")
    return 42

# Ordine di APPLICAZIONE (build-time): C, B, A (dal basso verso l'alto)
# Ordine di ESECUZIONE (call-time): A, B, C, operazione, C, B, A
operazione()
#   [A] prima — func visibile: operazione
#   [B] prima — func visibile: operazione
#   [C] prima — func visibile: operazione
#   [operazione] eseguita
#   [C] dopo
#   [B] dopo
#   [A] dopo
```

Nota: grazie a `@functools.wraps`, tutti i wrapper vedono `func.__name__` come `"operazione"`, non come `"wrapper"`.

#### Catena __wrapped__

`functools.wraps` imposta l'attributo `__wrapped__` sul wrapper, consentendo di risalire alla funzione originale:

```python
print(operazione.__wrapped__)                      # <function operazione>
print(operazione.__wrapped__.__wrapped__)           # <function operazione>
print(operazione.__wrapped__.__wrapped__.__wrapped__) # <function operazione>

# Accesso diretto alla funzione originale (bypassa tutti i decoratori)
originale = operazione.__wrapped__.__wrapped__.__wrapped__
originale()  # Esegue operazione() senza decoratori
```

#### Pattern: decoratore consapevole della posizione nello stack

```python
import functools

def decoratore_posizionale(posizione):
    """Decoratore che sa la propria posizione nello stack."""
    def decoratore(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[Posizione {posizione}] Entrando")
            risultato = func(*args, **kwargs)
            print(f"[Posizione {posizione}] Uscendo")
            return risultato
        wrapper._posizione_stack = posizione
        return wrapper
    return decoratore
```

---

### Decoratori Class-Based Avanzati

#### Decoratore con Stato e Descrittore

Quando un decoratore class-based deve funzionare correttamente con i metodi di istanza, deve implementare il protocollo **descriptor** (`__get__`). Senza `__get__`, il metodo non riceve `self` correttamente.

```python
import functools
from types import MethodType

class ContaChiamateMetodo:
    """Decoratore class-based che funziona sia con funzioni che con metodi."""

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.contatore = 0

    def __call__(self, *args, **kwargs):
        self.contatore += 1
        return self.func(*args, **kwargs)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Restituisce un bound method
        return MethodType(self, obj)

    def reset(self):
        self.contatore = 0

class MioServizio:
    @ContaChiamateMetodo
    def elabora(self, dati):
        return [x * 2 for x in dati]

servizio = MioServizio()
servizio.elabora([1, 2, 3])
servizio.elabora([4, 5])
print(MioServizio.elabora.contatore)  # 2
```

#### Decoratore Class-Based con Parametri

Quando un decoratore class-based deve accettare parametri, `__init__` riceve i parametri e `__call__` riceve la funzione da decorare:

```python
import functools
import time

class RateLimiter:
    """Decoratore class-based per rate limiting con stato persistente."""

    def __init__(self, max_chiamate: int, finestra_secondi: float):
        self.max_chiamate = max_chiamate
        self.finestra = finestra_secondi
        self.chiamate: dict[str, list[float]] = {}

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            chiave = func.__qualname__
            adesso = time.monotonic()

            if chiave not in self.chiamate:
                self.chiamate[chiave] = []

            # Rimuovi chiamate vecchie
            self.chiamate[chiave] = [
                t for t in self.chiamate[chiave]
                if adesso - t < self.finestra
            ]

            if len(self.chiamate[chiave]) >= self.max_chiamate:
                raise RuntimeError(
                    f"Rate limit raggiunto per {func.__name__}: "
                    f"{self.max_chiamate} chiamate in {self.finestra}s"
                )

            self.chiamate[chiave].append(adesso)
            return func(*args, **kwargs)
        return wrapper

    def statistiche(self):
        """Restituisce le statistiche di utilizzo."""
        return {k: len(v) for k, v in self.chiamate.items()}

limiter = RateLimiter(max_chiamate=10, finestra_secondi=60)

@limiter
def chiama_servizio_esterno(endpoint: str) -> dict:
    return {"status": "ok", "endpoint": endpoint}

# Le statistiche sono accessibili dall'istanza del decoratore
# print(limiter.statistiche())
```

---

### Il Protocollo Descriptor — Fondamento dei Decoratori Class-Based

I decoratori class-based funzionano correttamente con i metodi di istanza solo grazie al **protocollo descriptor** (PEP 252). Comprendere questo protocollo e essenziale per scrivere decoratori class-based robusti e per capire come funzionano internamente `property`, `staticmethod`, `classmethod` e i metodi bound stessi.

#### I Tre Metodi del Protocollo

Il protocollo descriptor si basa su tre metodi speciali che una classe puo implementare:

```python
from typing import Any

class DescriptorCompleto:
    """Esempio di data descriptor — implementa sia __get__ sia __set__."""

    def __set_name__(self, owner: type, name: str) -> None:
        """Chiamato automaticamente quando il descriptor viene assegnato a un attributo di classe.
        Introdotto in Python 3.6 (PEP 487).
        """
        self.nome_pubblico = name
        self.nome_privato = f"_{name}"

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Chiamato quando si accede all'attributo.

        - obj is None: accesso dalla classe (es. Classe.attr)
        - obj is not None: accesso da un'istanza (es. istanza.attr)
        """
        if obj is None:
            return self  # Accesso dalla classe: restituisci il descriptor stesso
        return getattr(obj, self.nome_privato, None)

    def __set__(self, obj: Any, valore: Any) -> None:
        """Chiamato quando si assegna un valore all'attributo."""
        setattr(obj, self.nome_privato, valore)

    def __delete__(self, obj: Any) -> None:
        """Chiamato quando si elimina l'attributo con del."""
        delattr(obj, self.nome_privato)
```

#### Data Descriptor vs Non-Data Descriptor

La distinzione fondamentale nel protocollo descriptor e tra **data descriptor** e **non-data descriptor**. Questa differenza determina la priorita nella risoluzione degli attributi:

| Tipo | Metodi implementati | Priorita nella lookup |
|------|---------------------|-----------------------|
| Data descriptor | `__get__` + `__set__` e/o `__delete__` | **Massima** — prevale anche su `__dict__` dell'istanza |
| Non-data descriptor | Solo `__get__` | **Bassa** — `__dict__` dell'istanza prevale |

La catena di risoluzione degli attributi in Python (Method Resolution Order per i descriptor) segue questo ordine:

1. **Data descriptor** definiti nella classe (o nelle sue classi base)
2. **Variabili di istanza** (`obj.__dict__`)
3. **Non-data descriptor** e attributi di classe

```python
class ValidatoPositivo:
    """Data descriptor: valida che il valore sia positivo."""

    def __set_name__(self, owner, name):
        self.nome = name
        self._nome_storage = f"_desc_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._nome_storage, 0)

    def __set__(self, obj, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError(f"{self.nome}: atteso numerico, ricevuto {type(valore).__name__}")
        if valore <= 0:
            raise ValueError(f"{self.nome}: deve essere positivo, ricevuto {valore}")
        setattr(obj, self._nome_storage, valore)

    def __delete__(self, obj):
        raise AttributeError(f"{self.nome}: non puo essere eliminato")


class Prodotto:
    prezzo = ValidatoPositivo()
    quantita = ValidatoPositivo()

    def __init__(self, nome: str, prezzo: float, quantita: int):
        self.nome = nome
        self.prezzo = prezzo      # Passa attraverso ValidatoPositivo.__set__
        self.quantita = quantita  # Idem

    @property
    def totale(self) -> float:
        return self.prezzo * self.quantita


p = Prodotto("Widget", 9.99, 100)
# p.prezzo = -5  # ValueError: prezzo: deve essere positivo, ricevuto -5
# p.prezzo = "abc"  # TypeError: prezzo: atteso numerico, ricevuto str
```

#### Come property, staticmethod e classmethod Usano i Descriptor

I decorator built-in di Python sono in realta implementati come descriptor:

- **`property`**: e un data descriptor (implementa `__get__`, `__set__`, `__delete__`). Ecco perche `property` prevale sempre su attributi di istanza con lo stesso nome.

- **`staticmethod`**: e un non-data descriptor (solo `__get__`). Restituisce la funzione originale senza modificarla — nessun binding a `self` o `cls`.

- **`classmethod`**: e un non-data descriptor (solo `__get__`). Il suo `__get__` fa il binding della funzione alla **classe** anziche all'istanza.

- **Metodi regolari**: le funzioni stesse sono non-data descriptor. Il metodo `function.__get__(obj, type)` restituisce un **bound method** — ecco il meccanismo con cui `self` viene passato automaticamente.

```python
class MetodoManuale:
    """Emulazione semplificata di come funzionano i metodi bound."""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func  # Accesso dalla classe: funzione non-bound
        # Accesso dall'istanza: restituisci un bound method
        import functools
        return functools.partial(self.func, obj)


class Esempio:
    @MetodoManuale
    def saluta(self, nome: str) -> str:
        return f"Ciao, {nome}!"

e = Esempio()
print(e.saluta("mondo"))   # Ciao, mondo! — self viene iniettato automaticamente
print(Esempio.saluta)       # <function saluta at 0x...> — funzione non-bound
```

#### Descriptor con Cache Lazy (Pattern Produzione)

Un pattern molto usato nei framework (Django, SQLAlchemy, attrs) e il **lazy descriptor** che calcola un valore costoso solo al primo accesso e lo memorizza nell'istanza:

```python
class LazyProperty:
    """Non-data descriptor con cache nell'istanza.

    Calcola il valore al primo accesso, poi lo memorizza in __dict__.
    Poiche e un non-data descriptor, __dict__ prevale nei successivi accessi.
    """

    def __init__(self, func):
        self.func = func
        self.nome_attr = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Calcola e memorizza nell'istanza
        valore = self.func(obj)
        # Dopo questo, obj.__dict__[self.nome_attr] prevale (non-data descriptor)
        setattr(obj, self.nome_attr, valore)
        return valore


class Report:
    def __init__(self, dati: list[float]):
        self.dati = dati

    @LazyProperty
    def statistiche(self) -> dict:
        """Calcolo costoso eseguito solo al primo accesso."""
        import statistics
        return {
            "media": statistics.mean(self.dati),
            "mediana": statistics.median(self.dati),
            "dev_std": statistics.stdev(self.dati) if len(self.dati) > 1 else 0.0,
            "n": len(self.dati),
        }

r = Report([1.5, 2.3, 4.1, 3.7, 2.9])
# r.statistiche → primo accesso: calcola e memorizza
# r.statistiche → accessi successivi: legge da __dict__ (nessun ricalcolo)
```

> **Nota:** A partire da Python 3.8, `functools.cached_property` fornisce esattamente questo pattern nella standard library, con gestione thread-safe inclusa. Preferire `cached_property` al descriptor manuale nei casi standard.

#### Descriptor Generico con Validazione Componibile

Un pattern di produzione avanzato consiste nel creare descriptor riutilizzabili con validatori componibili. Questo approccio e usato internamente da framework come Django (field validators), attrs/pydantic (field types) e SQLAlchemy (column types):

```python
from typing import Callable, Any

class Campo:
    """Descriptor generico con pipeline di validazione componibile.

    I validatori sono funzioni che ricevono (nome_campo, valore) e sollevano
    un'eccezione se la validazione fallisce.
    """

    def __init__(self, *validatori: Callable[[str, Any], None], default: Any = None):
        self.validatori = validatori
        self.default = default

    def __set_name__(self, owner: type, name: str) -> None:
        self.nome_pubblico = name
        self.nome_privato = f"_campo_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.nome_privato, self.default)

    def __set__(self, obj, valore):
        for validatore in self.validatori:
            validatore(self.nome_pubblico, valore)
        setattr(obj, self.nome_privato, valore)


# Validatori riutilizzabili
def tipo_richiesto(*tipi: type):
    def valida(nome: str, valore: Any) -> None:
        if not isinstance(valore, tipi):
            nomi = " | ".join(t.__name__ for t in tipi)
            raise TypeError(f"{nome}: atteso {nomi}, ricevuto {type(valore).__name__}")
    return valida


def intervallo(minimo: float | None = None, massimo: float | None = None):
    def valida(nome: str, valore: Any) -> None:
        if minimo is not None and valore < minimo:
            raise ValueError(f"{nome}: minimo {minimo}, ricevuto {valore}")
        if massimo is not None and valore > massimo:
            raise ValueError(f"{nome}: massimo {massimo}, ricevuto {valore}")
    return valida


def lunghezza_stringa(min_len: int = 0, max_len: int = 255):
    def valida(nome: str, valore: Any) -> None:
        if not isinstance(valore, str):
            raise TypeError(f"{nome}: atteso str")
        if not (min_len <= len(valore) <= max_len):
            raise ValueError(f"{nome}: lunghezza deve essere {min_len}-{max_len}, e {len(valore)}")
    return valida


# Composizione dei validatori nei campi della classe
class Dipendente:
    nome = Campo(tipo_richiesto(str), lunghezza_stringa(2, 100))
    eta = Campo(tipo_richiesto(int), intervallo(minimo=18, massimo=120))
    stipendio = Campo(tipo_richiesto(int, float), intervallo(minimo=0))

    def __init__(self, nome: str, eta: int, stipendio: float):
        self.nome = nome
        self.eta = eta
        self.stipendio = stipendio


d = Dipendente("Mario Rossi", 35, 45000.0)
# Dipendente("", 35, 45000.0)  → ValueError: nome: lunghezza deve essere 2-100, e 0
# Dipendente("Mario", 15, 45000.0)  → ValueError: eta: minimo 18, ricevuto 15
```

Questo pattern elimina la duplicazione di logica di validazione e permette di comporre vincoli complessi a partire da validatori atomici, seguendo il principio di composizione sopra ereditarieta.

---

### Decoratori Parametrici: Factory Pattern e Parametri Opzionali

#### Il Problema dei Parametri Opzionali

Un pattern frequente e creare un decoratore che possa essere usato sia con sia senza parentesi:

```python
import functools

def decoratore_flessibile(func=None, *, prefisso="LOG", livello="INFO"):
    """Decoratore che funziona con e senza argomenti.

    Uso: @decoratore_flessibile
         @decoratore_flessibile()
         @decoratore_flessibile(prefisso="DEBUG")
    """
    def decoratore(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            print(f"[{prefisso}:{livello}] Chiamata a {f.__name__}")
            return f(*args, **kwargs)
        return wrapper

    if func is not None:
        # Chiamato senza parentesi: @decoratore_flessibile
        return decoratore(func)
    # Chiamato con parentesi: @decoratore_flessibile(prefisso="X")
    return decoratore

@decoratore_flessibile
def funzione_a():
    pass

@decoratore_flessibile(prefisso="AUDIT", livello="WARNING")
def funzione_b():
    pass

funzione_a()  # [LOG:INFO] Chiamata a funzione_a
funzione_b()  # [AUDIT:WARNING] Chiamata a funzione_b
```

Il trucco sta nel primo parametro `func=None` e nell'uso di keyword-only arguments (`*`): se il decoratore viene invocato senza parentesi, `func` riceve la funzione da decorare direttamente; se viene invocato con parentesi, `func` resta `None` e si restituisce il decoratore interno.

#### Factory di Decoratori

Quando i decoratori condividono logica comune ma differiscono in comportamento, si puo usare una factory:

```python
import functools
import logging

def crea_decoratore_log(logger_name: str, livello: int = logging.INFO):
    """Factory che genera decoratori di logging personalizzati."""
    logger = logging.getLogger(logger_name)

    def decoratore(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(livello, f"Inizio: {func.__name__}")
            try:
                risultato = func(*args, **kwargs)
                logger.log(livello, f"Fine: {func.__name__} -> successo")
                return risultato
            except Exception as e:
                logger.error(f"Errore in {func.__name__}: {e}")
                raise
        return wrapper
    return decoratore

# Factory produce decoratori specializzati
log_autenticazione = crea_decoratore_log("auth", logging.WARNING)
log_pagamenti = crea_decoratore_log("payment", logging.CRITICAL)
log_api = crea_decoratore_log("api", logging.DEBUG)

@log_pagamenti
def processa_pagamento(importo, valuta="EUR"):
    return {"importo": importo, "valuta": valuta, "stato": "completato"}
```

---

## Generatori

### Fondamenti dei Generatori

#### La Keyword yield

Un generatore e una funzione speciale che utilizza `yield` al posto di (o in aggiunta a) `return`. Quando Python incontra `yield`, la funzione non termina: il suo stato viene sospeso e il valore indicato viene prodotto come prossimo elemento della sequenza.

```python
def conta_fino_a(n):
    """Generatore che conta da 1 a n."""
    i = 1
    while i <= n:
        yield i
        i += 1

# Uso con ciclo for
for numero in conta_fino_a(5):
    print(numero, end=" ")  # 1 2 3 4 5
```

#### Generator Function vs Generator Object

E fondamentale distinguere tra la funzione generatore e l'oggetto generatore. Chiamare la funzione non esegue il suo corpo: crea e restituisce un oggetto generatore.

```python
def mio_generatore():
    print("Inizio")
    yield 1
    print("Dopo il primo yield")
    yield 2
    print("Fine")

# La funzione generatore
print(type(mio_generatore))    # <class 'function'>

# L'oggetto generatore
gen = mio_generatore()
print(type(gen))               # <class 'generator'>

# Solo ora il codice viene eseguito, passo dopo passo
print(next(gen))  # Stampa "Inizio", poi produce 1
print(next(gen))  # Stampa "Dopo il primo yield", poi produce 2
# next(gen)       # Stampa "Fine", poi solleva StopIteration
```

#### next() e StopIteration

La funzione built-in `next()` avanza il generatore fino al prossimo `yield`. Quando il generatore non ha piu valori da produrre, solleva l'eccezione `StopIteration`.

```python
gen = conta_fino_a(3)

print(next(gen))  # 1
print(next(gen))  # 2
print(next(gen))  # 3

try:
    next(gen)
except StopIteration:
    print("Il generatore e esaurito")

# next() accetta un valore di default per evitare StopIteration
gen2 = conta_fino_a(1)
print(next(gen2))              # 1
print(next(gen2, "finito"))    # finito
```

#### Stati del Generatore

Un generatore attraversa diversi stati durante il suo ciclo di vita:

```python
import inspect

def esempio_stati():
    yield 1
    yield 2

gen = esempio_stati()

print(inspect.getgeneratorstate(gen))  # GEN_CREATED (creato, mai avviato)

next(gen)
print(inspect.getgeneratorstate(gen))  # GEN_SUSPENDED (sospeso su un yield)

next(gen)
try:
    next(gen)
except StopIteration:
    pass
print(inspect.getgeneratorstate(gen))  # GEN_CLOSED (terminato)
```

Gli stati possibili sono: `GEN_CREATED`, `GEN_RUNNING`, `GEN_SUSPENDED` e `GEN_CLOSED`.

---

### Generator Expressions

#### Sintassi: Parentesi Tonde vs Quadre

Le generator expressions offrono una sintassi compatta per creare generatori, analoga alle list comprehension ma con parentesi tonde.

```python
# List comprehension (parentesi quadre) - crea tutta la lista in memoria
lista_quadrati = [x ** 2 for x in range(1_000_000)]

# Generator expression (parentesi tonde) - valutazione lazy
gen_quadrati = (x ** 2 for x in range(1_000_000))

print(type(lista_quadrati))  # <class 'list'>
print(type(gen_quadrati))    # <class 'generator'>
```

#### Confronto di Memoria

```python
import sys

# La lista occupa memoria per tutti gli elementi
lista = [x ** 2 for x in range(100_000)]
print(f"Lista: {sys.getsizeof(lista):,} byte")  # ~800,000 byte

# Il generatore occupa memoria costante indipendentemente dalla dimensione
gen = (x ** 2 for x in range(100_000))
print(f"Generatore: {sys.getsizeof(gen):,} byte")  # ~200 byte
```

#### Valutazione Lazy

I valori vengono calcolati solo quando richiesti. Questo comportamento e particolarmente vantaggioso quando non e necessario elaborare tutti gli elementi.

```python
def elabora_pesante(x):
    """Simula un'elaborazione costosa."""
    import time
    time.sleep(0.01)
    return x ** 2

# Con la lista, TUTTE le elaborazioni avvengono subito
# risultati_lista = [elabora_pesante(x) for x in range(1000)]  # ~10 secondi

# Con il generatore, si elabora solo cio che serve
risultati_gen = (elabora_pesante(x) for x in range(1000))

# Prendiamo solo i primi 5 risultati: ~0.05 secondi
from itertools import islice
primi_cinque = list(islice(risultati_gen, 5))
print(primi_cinque)  # [0, 1, 4, 9, 16]
```

---

### yield from

#### Delegare a Sotto-Generatori

La sintassi `yield from` permette a un generatore di delegare la produzione di valori a un altro iterabile o sotto-generatore, semplificando notevolmente il codice.

```python
def gen_numeri():
    yield from range(3)       # 0, 1, 2
    yield from range(10, 13)  # 10, 11, 12

print(list(gen_numeri()))  # [0, 1, 2, 10, 11, 12]

# Senza yield from, il codice equivalente sarebbe:
def gen_numeri_manuale():
    for i in range(3):
        yield i
    for i in range(10, 13):
        yield i
```

#### Casi d'Uso

```python
# Appiattimento di strutture annidate
def appiattisci(struttura):
    """Appiattisce una struttura annidata arbitrariamente."""
    for elemento in struttura:
        if isinstance(elemento, (list, tuple)):
            yield from appiattisci(elemento)
        else:
            yield elemento

dati = [1, [2, 3, [4, 5]], [6, [7, 8, [9]]]]
print(list(appiattisci(dati)))  # [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Traversata di alberi
def visita_in_ordine(nodo):
    """Visita in-order di un albero binario."""
    if nodo is None:
        return
    yield from visita_in_ordine(nodo.sinistro)
    yield nodo.valore
    yield from visita_in_ordine(nodo.destro)
```

---

### Generatori Pratici

#### Lettura di File Riga per Riga (Memory Efficient)

```python
def leggi_file_grande(percorso, dimensione_chunk=8192):
    """Legge un file di grandi dimensioni senza caricarlo tutto in memoria."""
    with open(percorso, 'r', encoding='utf-8') as f:
        for riga in f:
            yield riga.rstrip('\n')

def cerca_in_file(percorso, pattern):
    """Cerca un pattern in un file di qualsiasi dimensione."""
    for numero_riga, riga in enumerate(leggi_file_grande(percorso), 1):
        if pattern in riga:
            yield (numero_riga, riga)
```

#### Sequenze Infinite

```python
def fibonacci():
    """Genera la sequenza di Fibonacci all'infinito."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Prendi i primi 15 numeri di Fibonacci
from itertools import islice
print(list(islice(fibonacci(), 15)))
# [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]

def numeri_primi():
    """Genera numeri primi all'infinito (Crivello incrementale)."""
    yield 2
    compositi = {}
    candidato = 3
    while True:
        if candidato not in compositi:
            yield candidato
            compositi[candidato * candidato] = [candidato]
        else:
            for primo in compositi[candidato]:
                compositi.setdefault(candidato + 2 * primo, []).append(primo)
            del compositi[candidato]
        candidato += 2

print(list(islice(numeri_primi(), 20)))
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
```

#### Pipeline di Dati (Producer-Consumer)

```python
def leggi_log(percorso):
    """Produttore: legge righe dal file di log."""
    with open(percorso) as f:
        yield from f

def filtra_errori(righe):
    """Filtro: seleziona solo le righe di errore."""
    for riga in righe:
        if "ERROR" in riga:
            yield riga

def estrai_messaggio(righe):
    """Trasformatore: estrae il messaggio di errore."""
    for riga in righe:
        parti = riga.split(" - ", maxsplit=1)
        if len(parti) == 2:
            yield parti[1].strip()

def pipeline_log(percorso):
    """Pipeline completa di elaborazione log."""
    righe = leggi_log(percorso)
    errori = filtra_errori(righe)
    messaggi = estrai_messaggio(errori)
    return messaggi

# Uso: ogni riga viene elaborata attraverso tutti gli stadi
# senza mai caricare l'intero file in memoria
# for messaggio in pipeline_log("/var/log/app.log"):
#     print(messaggio)
```

#### Finestra Scorrevole (Sliding Window)

```python
from collections import deque

def finestra_scorrevole(iterabile, dimensione):
    """Genera sotto-sequenze consecutive di lunghezza fissa."""
    it = iter(iterabile)
    finestra = deque(maxlen=dimensione)

    # Riempi la prima finestra
    for _ in range(dimensione):
        finestra.append(next(it))
    yield tuple(finestra)

    # Scorri
    for elemento in it:
        finestra.append(elemento)
        yield tuple(finestra)

dati = [1, 2, 3, 4, 5, 6, 7]
for gruppo in finestra_scorrevole(dati, 3):
    print(gruppo)
# (1, 2, 3)
# (2, 3, 4)
# (3, 4, 5)
# (4, 5, 6)
# (5, 6, 7)
```

#### Appiattimento di Strutture Annidate

```python
def appiattisci_dizionari(dati, prefisso=""):
    """Appiattisce un dizionario annidato in coppie chiave-valore piatte."""
    for chiave, valore in dati.items():
        chiave_completa = f"{prefisso}.{chiave}" if prefisso else chiave
        if isinstance(valore, dict):
            yield from appiattisci_dizionari(valore, chiave_completa)
        else:
            yield (chiave_completa, valore)

config = {
    "database": {
        "host": "localhost",
        "porta": 5432,
        "credenziali": {
            "utente": "admin",
            "password": "segreta"
        }
    },
    "debug": True
}

piatto = dict(appiattisci_dizionari(config))
print(piatto)
# {'database.host': 'localhost', 'database.porta': 5432,
#  'database.credenziali.utente': 'admin',
#  'database.credenziali.password': 'segreta', 'debug': True}
```

#### Elaborazione CSV/Log

```python
import csv

def elabora_csv(percorso, delimitatore=','):
    """Genera dizionari da un file CSV, riga per riga."""
    with open(percorso, 'r', encoding='utf-8') as f:
        lettore = csv.DictReader(f, delimiter=delimitatore)
        for riga in lettore:
            yield riga

def filtra_e_trasforma(righe, campo_filtro, valore_filtro):
    """Filtra righe CSV e trasforma i dati."""
    for riga in righe:
        if riga.get(campo_filtro) == valore_filtro:
            yield {k: v.strip() for k, v in riga.items()}

# Pipeline di elaborazione CSV
# righe = elabora_csv("vendite.csv")
# vendite_milano = filtra_e_trasforma(righe, "citta", "Milano")
# for vendita in vendite_milano:
#     print(vendita)
```

---

### Generatori Bidirezionali

#### Il Metodo send()

Il metodo `send()` permette di inviare valori all'interno di un generatore. Il valore inviato diventa il risultato dell'espressione `yield` all'interno del generatore.

```python
def accumulatore():
    """Generatore che accumula valori ricevuti tramite send()."""
    totale = 0
    while True:
        valore = yield totale
        if valore is None:
            break
        totale += valore

acc = accumulatore()
next(acc)          # Avvia il generatore (primo yield restituisce 0)
print(acc.send(10))  # 10
print(acc.send(20))  # 30
print(acc.send(5))   # 35
```

La prima chiamata deve essere `next()` (o `send(None)`) per avanzare il generatore fino al primo `yield`.

#### throw() e close()

```python
def generatore_robusto():
    """Dimostra la gestione di throw() e close()."""
    try:
        while True:
            try:
                valore = yield
                print(f"Ricevuto: {valore}")
            except ValueError as e:
                print(f"Errore gestito: {e}")
    except GeneratorExit:
        print("Generatore chiuso. Pulizia in corso...")

gen = generatore_robusto()
next(gen)
gen.send("dati validi")    # Ricevuto: dati validi
gen.throw(ValueError, "dato non valido")  # Errore gestito: dato non valido
gen.send("ancora valido")  # Ricevuto: ancora valido
gen.close()                # Generatore chiuso. Pulizia in corso...
```

#### Pattern Coroutine (Pre-asyncio)

Prima dell'introduzione di `asyncio`, i generatori venivano usati come coroutine per implementare la concorrenza cooperativa.

```python
def coroutine(func):
    """Decoratore che avvia automaticamente una coroutine."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)  # Avanza al primo yield
        return gen
    return wrapper

@coroutine
def media_mobile():
    """Calcola la media mobile dei valori ricevuti."""
    totale = 0.0
    conteggio = 0
    media = None
    while True:
        valore = yield media
        totale += valore
        conteggio += 1
        media = totale / conteggio

avg = media_mobile()
print(avg.send(10))   # 10.0
print(avg.send(20))   # 15.0
print(avg.send(30))   # 20.0
print(avg.send(40))   # 25.0
```

---

### Generator Internals: send(), throw(), close()

#### Il Protocollo Completo del Generatore

Un generatore implementa l'interfaccia `collections.abc.Generator`, che comprende quattro metodi: `__next__()`, `send()`, `throw()` e `close()`. Questi metodi definiscono il **protocollo coroutine** e permettono comunicazione bidirezionale tra il chiamante e il generatore.

```python
import collections.abc

def mio_gen():
    yield 1

gen = mio_gen()
print(isinstance(gen, collections.abc.Generator))  # True

# Metodi disponibili
print(hasattr(gen, 'send'))   # True
print(hasattr(gen, 'throw'))  # True
print(hasattr(gen, 'close'))  # True
```

#### send() — Semantica Precisa

`send(value)` fa due cose atomicamente: (1) riprende l'esecuzione del generatore, (2) il valore passato diventa il risultato dell'espressione `yield` corrente. Il generatore avanza fino al prossimo `yield`, il cui operando diventa il valore restituito da `send()`.

```python
def pipeline_interattiva():
    """Generatore che processa comandi ricevuti via send()."""
    risultato = None
    while True:
        comando = yield risultato
        if comando is None:
            continue
        operazione, *argomenti = comando.split()
        if operazione == "UPPER":
            risultato = " ".join(argomenti).upper()
        elif operazione == "REVERSE":
            risultato = " ".join(argomenti)[::-1]
        elif operazione == "COUNT":
            risultato = str(len(argomenti))
        else:
            risultato = f"Comando sconosciuto: {operazione}"

proc = pipeline_interattiva()
next(proc)  # Avvio
print(proc.send("UPPER ciao mondo"))      # CIAO MONDO
print(proc.send("REVERSE python"))        # nohtyp
print(proc.send("COUNT a b c d e"))       # 5
```

#### throw() — Iniettare Eccezioni

`throw(type, value, traceback)` inietta un'eccezione nel punto in cui il generatore e sospeso. Se il generatore cattura l'eccezione, l'esecuzione continua fino al prossimo `yield`; altrimenti l'eccezione si propaga al chiamante.

```python
def generatore_con_recovery():
    """Generatore che gestisce diverse eccezioni iniettate."""
    conteggio = 0
    while True:
        try:
            valore = yield conteggio
            conteggio += 1
        except ValueError:
            print("ValueError catturato: reset del conteggio")
            conteggio = 0
        except RuntimeError as e:
            print(f"RuntimeError catturato: {e}")
            # Continua senza reset

gen = generatore_con_recovery()
print(next(gen))                    # 0
print(gen.send("a"))                # 1
print(gen.send("b"))                # 2
print(gen.throw(ValueError))        # ValueError catturato: reset del conteggio → 0
print(gen.send("c"))                # 1
print(gen.throw(RuntimeError, "warning"))  # RuntimeError catturato: warning → 1
```

#### close() — Terminazione Pulita

`close()` inietta `GeneratorExit` nel generatore. Il generatore deve terminare (con `return` o sollevando `GeneratorExit`/`StopIteration`). Se il generatore cattura `GeneratorExit` e fa `yield` invece di terminare, viene sollevato `RuntimeError`.

```python
def generatore_con_cleanup():
    """Generatore con logica di cleanup nel finally."""
    risorsa = {"aperta": True, "operazioni": 0}
    try:
        while True:
            valore = yield risorsa["operazioni"]
            risorsa["operazioni"] += 1
    except GeneratorExit:
        # NON fare yield qui — causerebbe RuntimeError
        risorsa["aperta"] = False
        print(f"Cleanup: {risorsa['operazioni']} operazioni completate")
    finally:
        print("Finally eseguito")

gen = generatore_con_cleanup()
next(gen)
gen.send("op1")
gen.send("op2")
gen.close()
# Cleanup: 2 operazioni completate
# Finally eseguito
```

---

### yield from: Delegazione Avanzata e Valore di Ritorno

#### Il Valore di Ritorno di yield from

Un aspetto poco noto di `yield from` (PEP 380) e che cattura il **valore di ritorno** del sotto-generatore. Quando il sotto-generatore termina con `return valore`, quel valore diventa il risultato dell'espressione `yield from`.

```python
def sotto_generatore():
    """Sotto-generatore che produce valori e restituisce un risultato finale."""
    totale = 0
    while True:
        valore = yield
        if valore is None:
            return totale  # Il return diventa il risultato di yield from
        totale += valore

def delegatore():
    """Generatore che delega a un sotto-generatore e usa il suo valore di ritorno."""
    print("Inizio delegazione")
    risultato = yield from sotto_generatore()
    print(f"Il sotto-generatore ha restituito: {risultato}")
    yield risultato

gen = delegatore()
next(gen)           # Avvia delegatore → avvia sotto_generatore
gen.send(10)        # Inviato al sotto_generatore
gen.send(20)        # Inviato al sotto_generatore
gen.send(30)        # Inviato al sotto_generatore
try:
    gen.send(None)  # sotto_generatore fa return 60
except StopIteration as e:
    pass
# Inizio delegazione
# Il sotto-generatore ha restituito: 60
```

#### Propagazione Bidirezionale

`yield from` propaga automaticamente `send()`, `throw()` e `close()` dal chiamante esterno al sotto-generatore, senza bisogno di codice boilerplate:

```python
def sotto_gen_robusto():
    """Sotto-generatore che gestisce throw() e close()."""
    try:
        while True:
            try:
                valore = yield
                print(f"  sotto-gen ricevuto: {valore}")
            except ValueError as e:
                print(f"  sotto-gen gestito ValueError: {e}")
    except GeneratorExit:
        print("  sotto-gen: cleanup")
        return "cleanup completato"

def wrapper():
    """yield from propaga send/throw/close automaticamente."""
    risultato = yield from sotto_gen_robusto()
    print(f"  wrapper: sotto-gen ha restituito '{risultato}'")

gen = wrapper()
next(gen)
gen.send("dati")                   #   sotto-gen ricevuto: dati
gen.throw(ValueError, "errore")    #   sotto-gen gestito ValueError: errore
gen.close()                        #   sotto-gen: cleanup
```

#### yield from: Pattern Avanzati di Delegazione

Oltre all'uso base, `yield from` abilita pattern sofisticati di composizione che sarebbero estremamente verbosi senza questa sintassi. La propagazione bidirezionale di `send()`, `throw()` e `close()` rende possibile costruire pipeline di generatori multi-livello in cui ogni stadio e completamente trasparente.

##### Pipeline di Aggregazione Multi-Stadio

```python
from typing import Generator

def raccoglitore() -> Generator[None, float, list[float]]:
    """Sotto-generatore: raccoglie valori finche non riceve None."""
    valori = []
    while True:
        v = yield
        if v is None:
            return valori
        valori.append(v)


def statistiche_per_gruppo() -> Generator[None, float | str, dict[str, dict]]:
    """Generatore delegante: raggruppa valori e calcola statistiche.

    Protocollo:
    - send(float): aggiunge valore al gruppo corrente
    - send(None): chiude il gruppo corrente
    - send("fine"): termina tutti i gruppi e produce risultato
    """
    import statistics
    gruppi: dict[str, list[float]] = {}
    numero_gruppo = 0

    while True:
        numero_gruppo += 1
        nome = f"gruppo_{numero_gruppo}"

        # Delega al raccoglitore: yield from gestisce send/throw/close
        valori = yield from raccoglitore()
        gruppi[nome] = valori

        # Dopo il return del sotto-generatore, il controllo torna qui
        segnale = yield  # Attende prossima istruzione
        if segnale == "fine":
            # Calcola statistiche finali
            risultato = {}
            for g, vals in gruppi.items():
                if vals:
                    risultato[g] = {
                        "n": len(vals),
                        "media": statistics.mean(vals),
                        "somma": sum(vals),
                    }
            return risultato


def supervisore():
    """Generatore top-level che delega a statistiche_per_gruppo."""
    risultato = yield from statistiche_per_gruppo()
    yield risultato  # Rende disponibile il risultato finale


gen = supervisore()
next(gen)

# Gruppo 1
gen.send(10.0)
gen.send(20.0)
gen.send(30.0)
gen.send(None)       # Chiude gruppo 1

# Segnale per continuare
gen.send("continua")  # non e "fine", crea nuovo gruppo

# Gruppo 2
gen.send(100.0)
gen.send(200.0)
gen.send(None)       # Chiude gruppo 2

# Termina
try:
    risultato = gen.send("fine")
    print(risultato)
except StopIteration as e:
    print(e.value)
```

##### Appiattimento Ricorsivo con yield from

`yield from` rende naturale l'appiattimento di strutture annidate arbitrariamente, un pattern comune nell'attraversamento di alberi e strutture gerarchiche:

```python
from collections.abc import Iterable

def appiattisci(iterabile, tipi_esclusi=(str, bytes)):
    """Appiattisce ricorsivamente strutture annidate.

    tipi_esclusi evita di scomporre stringhe e bytes in caratteri singoli.
    """
    for elemento in iterabile:
        if isinstance(elemento, Iterable) and not isinstance(elemento, tipi_esclusi):
            yield from appiattisci(elemento, tipi_esclusi)
        else:
            yield elemento


dati_complessi = [1, [2, 3, [4, 5]], "ciao", [6, [7, [8, 9]]], (10, 11)]
print(list(appiattisci(dati_complessi)))
# [1, 2, 3, 4, 5, 'ciao', 6, 7, 8, 9, 10, 11]
```

##### yield from vs for Loop Manuale — Cosa si Guadagna

Senza `yield from`, la delegazione a un sotto-generatore richiede codice boilerplate che deve gestire manualmente ogni aspetto della propagazione. Questo confronto illustra la differenza:

```python
# SENZA yield from — propagazione manuale (verboso e soggetto a errori)
def delegatore_manuale(sotto_gen):
    """Emula yield from senza usarlo — solo per scopo didattico."""
    it = iter(sotto_gen)
    try:
        valore_yield = next(it)
    except StopIteration as e:
        return e.value

    while True:
        try:
            valore_inviato = yield valore_yield
        except GeneratorExit:
            it.close()
            return
        except BaseException as e:
            try:
                valore_yield = it.throw(type(e), e)
            except StopIteration as stop:
                return stop.value
        else:
            try:
                if valore_inviato is None:
                    valore_yield = next(it)
                else:
                    valore_yield = it.send(valore_inviato)
            except StopIteration as stop:
                return stop.value


# CON yield from — una sola riga
def delegatore_pulito(sotto_gen):
    """Equivalente semantico: yield from gestisce tutto."""
    return (yield from sotto_gen)
```

Il codice del `delegatore_manuale` sono circa 25 righe di logica delicata. `yield from` comprime tutta quella semantica in un'espressione leggibile. Inoltre, `yield from` gestisce correttamente casi limite che il codice manuale spesso trascura (come `throw()` su un generatore che non ha un handler per quell'eccezione).

##### Evoluzione Storica: dai Generatori-Coroutine ad async/await

La relazione tra `yield from` e `async/await` e una delle transizioni architetturali piu importanti di Python:

| PEP | Python | Innovazione |
|-----|--------|-------------|
| PEP 255 | 2.2 | Generatori semplici (`yield`) |
| PEP 342 | 2.5 | Coroutine basate su generatori (`send()`, `throw()`) |
| PEP 380 | 3.3 | `yield from` — delegazione trasparente |
| PEP 3156 | 3.4 | `asyncio` con `@asyncio.coroutine` + `yield from` |
| PEP 492 | 3.5 | `async def` / `await` — sintassi nativa |
| PEP 525 | 3.6 | Generatori asincroni (`async def` + `yield`) |

La transizione da PEP 3156 a PEP 492 e istruttiva. In Python 3.4, le coroutine asyncio si scrivevano cosi:

```python
import asyncio

# Python 3.4 — generatore-coroutine (deprecato da 3.8, rimosso in 3.11)
@asyncio.coroutine
def vecchio_stile():
    risultato = yield from asyncio.sleep(1)
    return risultato

# Python 3.5+ — sintassi nativa (raccomandata)
async def nuovo_stile():
    risultato = await asyncio.sleep(1)
    return risultato
```

`yield from` resta fondamentale per la composizione di generatori sincroni. Per il codice asincrono, `async/await` e la sintassi raccomandata da Python 3.5+. Le coroutine basate su generatori (`@asyncio.coroutine` + `yield from`) sono state deprecate in Python 3.8 e rimosse in Python 3.11.

---

### Generatori Asincroni

#### async for e yield in async def

Python 3.6+ (PEP 525) introduce i **generatori asincroni**: funzioni `async def` che contengono `yield`. Si consumano con `async for`.

```python
import asyncio

async def stream_dati(url: str, n_pagine: int):
    """Generatore asincrono che simula lo streaming di dati da un'API."""
    for pagina in range(1, n_pagine + 1):
        await asyncio.sleep(0.1)  # Simula latenza di rete
        dati = [{"id": i, "pagina": pagina} for i in range(3)]
        yield dati

async def main():
    async for blocco in stream_dati("https://api.esempio.it/dati", 3):
        print(f"Ricevuti {len(blocco)} elementi dalla pagina {blocco[0]['pagina']}")

# asyncio.run(main())
```

#### aclose() — Chiusura di Generatori Asincroni

I generatori asincroni richiedono una chiusura esplicita con `aclose()` per garantire il cleanup delle risorse asincrone. Il ciclo `async for` chiama `aclose()` automaticamente.

```python
import asyncio

async def monitor_eventi():
    """Generatore asincrono con risorse che richiedono cleanup."""
    print("Monitor: apertura connessione")
    try:
        contatore = 0
        while True:
            await asyncio.sleep(0.5)
            contatore += 1
            yield {"evento": contatore, "timestamp": asyncio.get_event_loop().time()}
    except GeneratorError:
        pass
    finally:
        print("Monitor: chiusura connessione")
        await asyncio.sleep(0.1)  # Cleanup asincrono

async def main():
    gen = monitor_eventi()
    # Prendi solo 3 eventi
    for _ in range(3):
        evento = await gen.__anext__()
        print(f"Evento: {evento['evento']}")
    await gen.aclose()  # Cleanup esplicito

# asyncio.run(main())
```

#### contextlib.aclosing (Python 3.10+)

Per garantire la chiusura di generatori asincroni, `contextlib.aclosing` fornisce un context manager asincrono:

```python
from contextlib import aclosing

async def main():
    async with aclosing(monitor_eventi()) as eventi:
        async for evento in eventi:
            print(evento)
            if evento["evento"] >= 3:
                break
    # aclose() viene chiamato automaticamente

# asyncio.run(main())
```

---

## Iteratori

### Protocollo Iterator

#### `__iter__` e `__next__`

Un oggetto e un iteratore se implementa due metodi: `__iter__()` (che restituisce se stesso) e `__next__()` (che restituisce il prossimo valore o solleva `StopIteration`).

```python
class ContatoreInverso:
    """Iteratore personalizzato che conta all'indietro."""

    def __init__(self, inizio):
        self.corrente = inizio

    def __iter__(self):
        return self

    def __next__(self):
        if self.corrente <= 0:
            raise StopIteration
        self.corrente -= 1
        return self.corrente + 1

for n in ContatoreInverso(5):
    print(n, end=" ")  # 5 4 3 2 1
```

#### Classe Iterator Personalizzata

```python
class RangeConSalto:
    """Iterabile personalizzato simile a range con salti variabili."""

    def __init__(self, inizio, fine, salto_iniziale=1, incremento_salto=0):
        self.inizio = inizio
        self.fine = fine
        self.salto_iniziale = salto_iniziale
        self.incremento_salto = incremento_salto

    def __iter__(self):
        """Restituisce un nuovo iteratore ad ogni iterazione."""
        corrente = self.inizio
        salto = self.salto_iniziale
        while corrente < self.fine:
            yield corrente
            corrente += salto
            salto += self.incremento_salto

# L'iterabile puo essere iterato piu volte
sequenza = RangeConSalto(0, 50, salto_iniziale=1, incremento_salto=1)
print(list(sequenza))  # [0, 1, 3, 6, 10, 15, 21, 28, 36, 45]
print(list(sequenza))  # [0, 1, 3, 6, 10, 15, 21, 28, 36, 45] (funziona di nuovo)
```

#### Differenza tra Iterable e Iterator

Un **iterable** e un oggetto che ha un metodo `__iter__()` che restituisce un iteratore. Un **iterator** e un oggetto che ha sia `__iter__()` (che restituisce se stesso) sia `__next__()`. Ogni iteratore e un iterable, ma non ogni iterable e un iteratore.

```python
lista = [1, 2, 3]           # Iterable, non iterator
iteratore = iter(lista)      # Iterator (e anche iterable)

print(hasattr(lista, '__iter__'))       # True
print(hasattr(lista, '__next__'))       # False (iterable, non iterator)
print(hasattr(iteratore, '__iter__'))   # True
print(hasattr(iteratore, '__next__'))   # True (iterator)
```

---

### itertools Deep Dive

Il modulo `itertools` fornisce un insieme di strumenti efficienti per lavorare con iteratori. Tutte le funzioni producono iteratori lazy.

#### Iteratori Infiniti

```python
from itertools import count, cycle, repeat

# count: conta all'infinito partendo da un valore con un passo
for i in count(10, 2.5):
    if i > 20:
        break
    print(i, end=" ")  # 10 12.5 15.0 17.5 20.0

# cycle: ripete ciclicamente un iterabile
colori = cycle(["rosso", "verde", "blu"])
print([next(colori) for _ in range(7)])
# ['rosso', 'verde', 'blu', 'rosso', 'verde', 'blu', 'rosso']

# repeat: ripete un valore (opzionalmente un numero fisso di volte)
print(list(repeat("ciao", 3)))  # ['ciao', 'ciao', 'ciao']
```

#### Iteratori Finiti

```python
from itertools import (
    chain, compress, dropwhile, takewhile,
    groupby, islice, starmap, tee
)

# chain: concatena piu iterabili
print(list(chain([1, 2], [3, 4], [5])))  # [1, 2, 3, 4, 5]

# compress: filtra usando una maschera booleana
dati = ['a', 'b', 'c', 'd', 'e']
maschera = [1, 0, 1, 0, 1]
print(list(compress(dati, maschera)))  # ['a', 'c', 'e']

# dropwhile / takewhile: scarta/prende finche la condizione e vera
numeri = [1, 3, 5, 2, 4, 6, 1]
print(list(dropwhile(lambda x: x < 4, numeri)))   # [5, 2, 4, 6, 1]
print(list(takewhile(lambda x: x < 4, numeri)))   # [1, 3]

# groupby: raggruppa elementi consecutivi con la stessa chiave
dati_ordinati = sorted(["mela", "mango", "banana", "arancia", "ananas"], key=len)
for lunghezza, gruppo in groupby(dati_ordinati, key=len):
    print(f"Lunghezza {lunghezza}: {list(gruppo)}")

# islice: slice per iteratori (senza creare una lista)
print(list(islice(count(), 5, 15, 3)))  # [5, 8, 11, 14]

# starmap: come map ma spacchetta le tuple come argomenti
from operator import mul
print(list(starmap(mul, [(2, 3), (4, 5), (6, 7)])))  # [6, 20, 42]

# tee: duplica un iteratore in n copie indipendenti
originale = iter(range(5))
copia1, copia2 = tee(originale, 2)
print(list(copia1))  # [0, 1, 2, 3, 4]
print(list(copia2))  # [0, 1, 2, 3, 4]
```

#### Iteratori Combinatorici

```python
from itertools import product, permutations, combinations, combinations_with_replacement

# product: prodotto cartesiano
print(list(product("AB", "12")))
# [('A', '1'), ('A', '2'), ('B', '1'), ('B', '2')]

# permutations: permutazioni (ordine conta)
print(list(permutations("ABC", 2)))
# [('A', 'B'), ('A', 'C'), ('B', 'A'), ('B', 'C'), ('C', 'A'), ('C', 'B')]

# combinations: combinazioni (ordine non conta, senza ripetizione)
print(list(combinations("ABCD", 2)))
# [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D'), ('C', 'D')]

# combinations_with_replacement: combinazioni con ripetizione
print(list(combinations_with_replacement("AB", 3)))
# [('A', 'A', 'A'), ('A', 'A', 'B'), ('A', 'B', 'B'), ('B', 'B', 'B')]
```

#### Ricette dalla Documentazione di itertools

```python
from itertools import chain, islice, tee

def prendi_a_coppie(iterabile):
    """Restituisce coppie sovrapposte: (s0,s1), (s1,s2), (s2,s3), ..."""
    a, b = tee(iterabile)
    next(b, None)
    return zip(a, b)

print(list(prendi_a_coppie([1, 2, 3, 4, 5])))
# [(1, 2), (2, 3), (3, 4), (4, 5)]

def raggruppa_in_blocchi(iterabile, n):
    """Raggruppa un iterabile in blocchi di dimensione n."""
    it = iter(iterabile)
    while True:
        blocco = list(islice(it, n))
        if not blocco:
            break
        yield blocco

print(list(raggruppa_in_blocchi(range(10), 3)))
# [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

def appiattisci_un_livello(lista_di_liste):
    """Appiattisce un livello di annidamento."""
    return chain.from_iterable(lista_di_liste)

print(list(appiattisci_un_livello([[1, 2], [3, 4], [5]])))
# [1, 2, 3, 4, 5]
```

---

### itertools Avanzato: accumulate, chain.from_iterable, batched

#### accumulate — Riduzione Incrementale

`accumulate` produce somme parziali (o applicazioni cumulative di una funzione binaria). E la versione lazy di `functools.reduce` che emette tutti i risultati intermedi.

```python
from itertools import accumulate
import operator

# Somme parziali (default)
print(list(accumulate([1, 2, 3, 4, 5])))
# [1, 3, 6, 10, 15]

# Prodotti parziali
print(list(accumulate([1, 2, 3, 4, 5], operator.mul)))
# [1, 2, 6, 24, 120]

# Massimo cumulativo
print(list(accumulate([3, 1, 4, 1, 5, 9, 2, 6], max)))
# [3, 3, 4, 4, 5, 9, 9, 9]

# Con valore iniziale (Python 3.8+)
print(list(accumulate([1, 2, 3], initial=100)))
# [100, 101, 103, 106]

# Caso d'uso: calcolo del saldo progressivo
movimenti = [1000, -200, 500, -100, -300, 800]
saldi = list(accumulate(movimenti))
print(f"Saldi progressivi: {saldi}")
# [1000, 800, 1300, 1200, 900, 1700]
```

#### chain.from_iterable — Appiattimento Lazy

`chain.from_iterable` consuma un singolo iterabile di iterabili, rendendolo piu efficiente di `chain(*iterabili)` quando l'input e gia un iteratore:

```python
from itertools import chain

# chain.from_iterable: accetta un iterabile di iterabili
matrice = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(list(chain.from_iterable(matrice)))
# [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Utile con generatori: non materializza la lista esterna
def genera_blocchi():
    for i in range(3):
        yield range(i * 3, i * 3 + 3)

print(list(chain.from_iterable(genera_blocchi())))
# [0, 1, 2, 3, 4, 5, 6, 7, 8]
```

#### batched — Raggruppamento in Batch (Python 3.12+)

Python 3.12 introduce `itertools.batched`, che raggruppa un iterabile in tuple di dimensione fissa:

```python
from itertools import batched

# Raggruppamento in batch di 3
print(list(batched("ABCDEFGH", 3)))
# [('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'H')]

# Utile per bulk operations
elementi = range(100)
for batch in batched(elementi, 10):
    # processa_batch(batch)  # Invia 10 elementi alla volta
    pass

# Pre-3.12: equivalente manuale
def batched_compat(iterabile, n):
    from itertools import islice
    it = iter(iterabile)
    while batch := tuple(islice(it, n)):
        yield batch
```

#### tee — Attenzione alla Memoria

`tee` crea copie indipendenti di un iteratore, ma **memorizza internamente** gli elementi consumati da un iteratore e non ancora consumati dagli altri. Se un iteratore avanza molto piu degli altri, il consumo di memoria puo diventare significativo.

```python
from itertools import tee

# Pattern sicuro: consumare le copie in parallelo
originale = iter(range(1_000_000))
it1, it2 = tee(originale)

# BENE: consumo parallelo
for a, b in zip(it1, it2):
    pass  # Memoria costante

# MALE: consumo sequenziale con iteratore grande
# list(it1)  # Memorizza 1M elementi internamente per it2
# list(it2)  # Solo ora libera la memoria
```

---

## Context Manager

### Fondamenti dei Context Manager

#### L'Istruzione with

L'istruzione `with` garantisce che le operazioni di setup e teardown vengano eseguite in modo affidabile, anche in presenza di eccezioni. E il modo idiomatico in Python per gestire risorse.

```python
# Pattern classico senza with (fragile)
f = open("dati.txt", "r")
try:
    contenuto = f.read()
finally:
    f.close()

# Con with (sicuro e idiomatico)
with open("dati.txt", "r") as f:
    contenuto = f.read()
# f.close() viene chiamato automaticamente, anche in caso di eccezione
```

#### Il Protocollo `__enter__` e `__exit__`

Un context manager e qualsiasi oggetto che implementa i metodi `__enter__` e `__exit__`.

```python
class GestoreRisorsa:
    """Context manager personalizzato."""

    def __init__(self, nome):
        self.nome = nome
        print(f"[INIT] Risorsa '{nome}' creata")

    def __enter__(self):
        print(f"[ENTER] Risorsa '{self.nome}' acquisita")
        return self  # L'oggetto assegnato con 'as'

    def __exit__(self, tipo_eccezione, valore_eccezione, traceback):
        print(f"[EXIT] Risorsa '{self.nome}' rilasciata")
        if tipo_eccezione is not None:
            print(f"[EXIT] Eccezione gestita: {tipo_eccezione.__name__}: {valore_eccezione}")
        return False  # Non sopprimere l'eccezione

with GestoreRisorsa("database") as risorsa:
    print(f"Uso la risorsa: {risorsa.nome}")
# [INIT] Risorsa 'database' creata
# [ENTER] Risorsa 'database' acquisita
# Uso la risorsa: database
# [EXIT] Risorsa 'database' rilasciata
```

#### Gestione delle Eccezioni in `__exit__`

Il metodo `__exit__` riceve tre argomenti che descrivono l'eventuale eccezione verificatasi nel blocco `with`. Restituendo `True`, l'eccezione viene soppressa; restituendo `False` (o `None`), l'eccezione viene propagata.

```python
class SopprimiErrori:
    """Context manager che sopprime eccezioni specifiche."""

    def __init__(self, *eccezioni_da_sopprimere):
        self.eccezioni = eccezioni_da_sopprimere

    def __enter__(self):
        return self

    def __exit__(self, tipo_eccezione, valore, traceback):
        if tipo_eccezione is not None and issubclass(tipo_eccezione, self.eccezioni):
            print(f"Eccezione soppressa: {tipo_eccezione.__name__}: {valore}")
            return True  # Sopprime l'eccezione
        return False  # Propaga l'eccezione

with SopprimiErrori(ValueError, TypeError):
    int("non_un_numero")  # ValueError soppressa
    print("Questa riga non viene eseguita")

print("Il programma continua normalmente")
```

---

### contextlib

Il modulo `contextlib` della libreria standard offre strumenti per creare e lavorare con i context manager in modo piu semplice.

#### @contextmanager — Context Manager Basato su Generatore

Il decoratore `@contextmanager` permette di creare un context manager usando una funzione generatore con un singolo `yield`, eliminando la necessita di scrivere una classe con `__enter__` e `__exit__`.

```python
from contextlib import contextmanager

@contextmanager
def gestisci_connessione(host, porta):
    """Context manager per una connessione simulata."""
    print(f"Connessione a {host}:{porta}...")
    connessione = {"host": host, "porta": porta, "attiva": True}
    try:
        yield connessione  # Valore assegnato con 'as'
    except Exception as e:
        print(f"Errore durante la connessione: {e}")
        raise
    finally:
        connessione["attiva"] = False
        print(f"Disconnessione da {host}:{porta}")

with gestisci_connessione("localhost", 5432) as conn:
    print(f"Connessione attiva: {conn['attiva']}")
# Connessione a localhost:5432...
# Connessione attiva: True
# Disconnessione da localhost:5432
```

Il codice prima di `yield` corrisponde a `__enter__`, il valore di `yield` e cio che viene assegnato con `as`, e il codice nel blocco `finally` corrisponde a `__exit__`.

#### suppress()

Sopprime eccezioni specifiche in modo conciso.

```python
from contextlib import suppress
import os

# Invece di try/except/pass
with suppress(FileNotFoundError):
    os.remove("file_inesistente.tmp")

# Equivalente a:
# try:
#     os.remove("file_inesistente.tmp")
# except FileNotFoundError:
#     pass
```

#### redirect_stdout / redirect_stderr

Redirige temporaneamente l'output standard o di errore.

```python
from contextlib import redirect_stdout, redirect_stderr
import io

# Cattura l'output di una funzione
buffer = io.StringIO()
with redirect_stdout(buffer):
    print("Questo va nel buffer")
    print("Anche questo")

output_catturato = buffer.getvalue()
print(f"Catturato: {output_catturato!r}")

# Redirige l'output su un file
with open("output.log", "w") as f:
    with redirect_stderr(f):
        import warnings
        warnings.warn("Questo warning va nel file")
```

#### closing()

Garantisce che venga chiamato il metodo `close()` di un oggetto.

```python
from contextlib import closing
from urllib.request import urlopen

# urlopen non e direttamente un context manager in tutte le versioni
with closing(urlopen("https://example.com")) as pagina:
    contenuto = pagina.read()
```

#### ExitStack

`ExitStack` gestisce dinamicamente un numero variabile di context manager. E particolarmente utile quando il numero di risorse da gestire non e noto a compile time.

```python
from contextlib import ExitStack

def elabora_file_multipli(percorsi):
    """Apre e elabora un numero variabile di file."""
    with ExitStack() as stack:
        file_aperti = [
            stack.enter_context(open(percorso, 'r'))
            for percorso in percorsi
        ]
        # Tutti i file vengono chiusi automaticamente all'uscita dal with
        for f in file_aperti:
            prima_riga = f.readline()
            print(f"{f.name}: {prima_riga.strip()}")

# ExitStack permette anche di registrare callback di cleanup
with ExitStack() as stack:
    stack.callback(print, "Terzo cleanup")
    stack.callback(print, "Secondo cleanup")
    stack.callback(print, "Primo cleanup")
# Primo cleanup
# Secondo cleanup
# Terzo cleanup
# (i callback vengono eseguiti in ordine LIFO)
```

#### nullcontext()

Un context manager che non fa nulla. Utile come placeholder quando un context manager e opzionale.

```python
from contextlib import nullcontext

def elabora(dati, file_output=None):
    """Scrive su file se specificato, altrimenti su stdout."""
    cm = open(file_output, 'w') if file_output else nullcontext()
    with cm as f:
        import sys
        destinazione = f if file_output else sys.stdout
        for elemento in dati:
            print(elemento, file=destinazione)
```

#### contextlib.chdir — Cambio Directory Temporaneo (Python 3.11+)

Introdotto in Python 3.11, `contextlib.chdir` e un context manager rientrante che cambia la directory di lavoro corrente e la ripristina automaticamente all'uscita. Sostituisce il pattern manuale `os.chdir()` + `try/finally`:

```python
import os
from contextlib import chdir

# PRIMA di Python 3.11 — pattern manuale soggetto a errori
def lavorazione_in_directory_vecchio(percorso: str):
    originale = os.getcwd()
    try:
        os.chdir(percorso)
        # operazioni nella nuova directory
        contenuti = os.listdir(".")
        return contenuti
    finally:
        os.chdir(originale)  # Facile dimenticare!


# DA Python 3.11 — pulito e sicuro
def lavorazione_in_directory(percorso: str):
    with chdir(percorso):
        contenuti = os.listdir(".")
        return contenuti
    # La directory originale e gia ripristinata


# chdir e rientrante: si possono annidare le chiamate
with chdir("/tmp"):
    print(f"In /tmp: {os.getcwd()}")
    with chdir("/var"):
        print(f"In /var: {os.getcwd()}")
    print(f"Tornati a /tmp: {os.getcwd()}")
# Tornati alla directory originale
```

> **Attenzione thread-safety:** `os.chdir()` modifica la directory dell'intero processo, non solo del thread corrente. In applicazioni multi-threaded, `chdir` puo causare race condition. Usare percorsi assoluti e meglio in contesti concorrenti.

#### contextlib.aclosing — Cleanup di Generatori Asincroni (Python 3.10+)

`contextlib.aclosing` (PEP 533, disponibile da Python 3.10) e l'equivalente asincrono di `contextlib.closing`. Garantisce che `aclose()` venga chiamato su un generatore asincrono o qualsiasi oggetto con metodo `aclose()`, anche in caso di eccezione:

```python
import asyncio
from contextlib import aclosing

async def stream_eventi(url: str):
    """Generatore asincrono che simula uno stream di eventi."""
    contatore = 0
    try:
        while True:
            await asyncio.sleep(0.1)
            contatore += 1
            yield {"id": contatore, "tipo": "evento", "url": url}
    finally:
        # Cleanup: chiude connessione, rilascia risorse
        print(f"Stream chiuso dopo {contatore} eventi")
        await asyncio.sleep(0.05)  # Simula cleanup asincrono


async def consuma_eventi():
    # SENZA aclosing: se break o eccezione, aclose() potrebbe non essere chiamato
    # con async for: il runtime lo chiama, ma non in tutti i percorsi di errore

    # CON aclosing: cleanup garantito
    async with aclosing(stream_eventi("https://api.esempio.it/stream")) as stream:
        async for evento in stream:
            print(f"Evento #{evento['id']}")
            if evento["id"] >= 5:
                break  # aclose() viene chiamato automaticamente
    # Stream chiuso dopo 5 eventi


# asyncio.run(consuma_eventi())
```

`aclosing` e particolarmente critico nei seguenti scenari:

- Generatori asincroni che mantengono connessioni di rete
- Stream di database con cursori aperti
- WebSocket handler che richiedono un messaggio di chiusura
- Qualsiasi risorsa asincrona che necessita di cleanup esplicito

#### Riepilogo Utilita contextlib per Versione

La tabella seguente riassume le utilita principali di `contextlib` per versione di Python, utile come riferimento rapido per decidere quali funzionalita sono disponibili nel proprio progetto:

| Utilita | Versione Python | Tipo | Uso principale |
|---------|----------------|------|----------------|
| `contextmanager` | 2.5+ | Decoratore | CM da generatore (sync) |
| `closing` | 2.5+ | CM | Chiude oggetti con `.close()` |
| `suppress` | 3.4+ | CM | Sopprime eccezioni specifiche |
| `redirect_stdout` | 3.4+ | CM | Redirige stdout temporaneamente |
| `redirect_stderr` | 3.5+ | CM | Redirige stderr temporaneamente |
| `ExitStack` | 3.3+ | CM | Gestione dinamica risorse sync |
| `AsyncExitStack` | 3.7+ | CM async | Gestione dinamica risorse async |
| `nullcontext` | 3.7+ | CM | Placeholder no-op |
| `asynccontextmanager` | 3.7+ | Decoratore | CM da generatore (async) |
| `aclosing` | 3.10+ | CM async | Chiude oggetti con `.aclose()` |
| `chdir` | 3.11+ | CM | Cambio directory temporaneo |

> **Nota sulla compatibilita:** se il progetto deve supportare versioni di Python precedenti alla 3.10, `aclosing` puo essere implementato manualmente in poche righe come `asynccontextmanager` wrapper attorno a un `try/finally` con `await obj.aclose()`. Per `chdir`, il pattern `os.getcwd()` + `try/finally` + `os.chdir()` resta l'alternativa.

---

### Context Manager Pratici

#### Gestione della Connessione al Database

```python
from contextlib import contextmanager

@contextmanager
def connessione_database(dsn):
    """Gestisce connessione e transazione al database."""
    import sqlite3
    conn = sqlite3.connect(dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@contextmanager
def cursore_database(dsn):
    """Fornisce un cursore con gestione automatica della transazione."""
    with connessione_database(dsn) as conn:
        cursore = conn.cursor()
        try:
            yield cursore
        except Exception:
            raise  # Il rollback e gestito da connessione_database

# Uso
# with cursore_database("miodb.sqlite") as cur:
#     cur.execute("INSERT INTO utenti (nome) VALUES (?)", ("Mario",))
#     cur.execute("SELECT * FROM utenti")
#     print(cur.fetchall())
```

#### File Locking

```python
import fcntl
from contextlib import contextmanager

@contextmanager
def file_lock(percorso):
    """Acquisisce un lock esclusivo su un file."""
    lock_file = open(percorso + ".lock", 'w')
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        print(f"Lock acquisito su {percorso}")
        yield lock_file
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
        print(f"Lock rilasciato su {percorso}")

# with file_lock("/tmp/risorsa_condivisa"):
#     # Operazioni protette dal lock
#     pass
```

#### Directory e File Temporanei

```python
import tempfile
import os
from contextlib import contextmanager

@contextmanager
def directory_di_lavoro_temporanea():
    """Crea una directory temporanea e la rimuove al termine."""
    import shutil
    dir_temp = tempfile.mkdtemp(prefix="lavoro_")
    print(f"Directory temporanea creata: {dir_temp}")
    try:
        yield dir_temp
    finally:
        shutil.rmtree(dir_temp)
        print(f"Directory temporanea rimossa: {dir_temp}")

# with directory_di_lavoro_temporanea() as dir_lavoro:
#     percorso_file = os.path.join(dir_lavoro, "temp.txt")
#     with open(percorso_file, "w") as f:
#         f.write("Dati temporanei")
```

#### Timer Context Manager

```python
import time
from contextlib import contextmanager

@contextmanager
def misura_tempo(etichetta="Blocco"):
    """Misura il tempo di esecuzione di un blocco di codice."""
    inizio = time.perf_counter()
    yield
    fine = time.perf_counter()
    print(f"[{etichetta}] Completato in {fine - inizio:.4f} secondi")

with misura_tempo("Ordinamento"):
    dati = list(range(1_000_000, 0, -1))
    dati.sort()
# [Ordinamento] Completato in 0.0523 secondi
```

#### Gestione delle Transazioni

```python
from contextlib import contextmanager

class Transazione:
    """Simula una transazione con supporto a commit e rollback."""

    def __init__(self):
        self.operazioni = []
        self.operazioni_compensative = []
        self._committed = False

    def esegui(self, azione, compensazione):
        """Registra ed esegue un'azione con la sua compensazione."""
        azione()
        self.operazioni.append(azione)
        self.operazioni_compensative.append(compensazione)

    def commit(self):
        self._committed = True
        self.operazioni_compensative.clear()

    def rollback(self):
        for compensazione in reversed(self.operazioni_compensative):
            compensazione()
        self.operazioni_compensative.clear()

@contextmanager
def transazione():
    """Context manager per gestire transazioni."""
    tx = Transazione()
    try:
        yield tx
        tx.commit()
        print("Transazione completata con successo")
    except Exception as e:
        tx.rollback()
        print(f"Transazione annullata a causa di: {e}")
        raise
```

#### Cambio di Directory

```python
import os
from contextlib import contextmanager

@contextmanager
def cambia_directory(percorso):
    """Cambia temporaneamente la directory di lavoro."""
    directory_originale = os.getcwd()
    try:
        os.chdir(percorso)
        yield percorso
    finally:
        os.chdir(directory_originale)

# with cambia_directory("/tmp"):
#     print(os.getcwd())  # /tmp
# print(os.getcwd())  # directory originale ripristinata
```

---

### Async Context Manager

#### `__aenter__` e `__aexit__`

I context manager asincroni utilizzano `async with` e implementano i metodi `__aenter__` e `__aexit__` come coroutine.

```python
import asyncio

class ConnessioneAsincrona:
    """Context manager asincrono per connessioni di rete."""

    def __init__(self, host, porta):
        self.host = host
        self.porta = porta
        self.connessione = None

    async def __aenter__(self):
        print(f"Connessione asincrona a {self.host}:{self.porta}...")
        await asyncio.sleep(0.1)  # Simula connessione
        self.connessione = {"host": self.host, "porta": self.porta}
        return self.connessione

    async def __aexit__(self, tipo_eccezione, valore, traceback):
        print(f"Chiusura connessione asincrona a {self.host}:{self.porta}")
        await asyncio.sleep(0.05)  # Simula chiusura
        self.connessione = None
        return False

async def main():
    async with ConnessioneAsincrona("api.esempio.it", 443) as conn:
        print(f"Connesso a: {conn}")
        await asyncio.sleep(0.1)  # Simula operazione

# asyncio.run(main())
```

#### @asynccontextmanager

Analogamente a `@contextmanager`, `contextlib` offre `@asynccontextmanager` per creare context manager asincroni con generatori.

```python
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def sessione_database_async(dsn):
    """Context manager asincrono per sessioni di database."""
    print(f"Apertura sessione asincrona: {dsn}")
    sessione = {"dsn": dsn, "attiva": True}
    await asyncio.sleep(0.1)  # Simula connessione
    try:
        yield sessione
    except Exception as e:
        print(f"Errore nella sessione: {e}")
        raise
    finally:
        sessione["attiva"] = False
        await asyncio.sleep(0.05)  # Simula chiusura
        print(f"Sessione chiusa: {dsn}")

async def operazione_database():
    async with sessione_database_async("postgresql://localhost/miodb") as sess:
        print(f"Sessione attiva: {sess['attiva']}")
        # await sess.execute(...)

# asyncio.run(operazione_database())
```

---

### Context Manager Protocol: Gestione Eccezioni Avanzata

#### Soppressione Selettiva e Logging

Il metodo `__exit__` riceve informazioni precise sull'eccezione che consente pattern di gestione sofisticati:

```python
import logging
import traceback as tb_module

logger = logging.getLogger(__name__)

class GestoreEccezioniAvanzato:
    """Context manager con gestione eccezioni granulare."""

    def __init__(self, *, sopprimi=(), logga=(), rilancia_come=None):
        self.sopprimi = sopprimi
        self.logga = logga
        self.rilancia_come = rilancia_come

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False

        # Logging delle eccezioni specificate
        if issubclass(exc_type, self.logga):
            logger.error(
                f"Eccezione catturata: {exc_type.__name__}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
            )

        # Soppressione
        if issubclass(exc_type, self.sopprimi):
            return True

        # Ri-lancio con tipo diverso
        if self.rilancia_come is not None:
            raise self.rilancia_come(str(exc_val)) from exc_val

        return False

# Uso: logga FileNotFoundError e sopprimilo, ma rilancia ValueError come RuntimeError
with GestoreEccezioniAvanzato(
    sopprimi=(FileNotFoundError,),
    logga=(FileNotFoundError, ValueError),
    rilancia_come=RuntimeError,
):
    # open("file_inesistente.txt")  # Soppressa dopo il log
    pass
```

#### Context Manager Rientrante vs Non-Rientrante

Un context manager **rientrante** puo essere usato in piu blocchi `with` annidati. La maggior parte dei context manager custom non e rientrante per default:

```python
from contextlib import contextmanager

@contextmanager
def cm_rientrante():
    """Context manager rientrante: supporta annidamento."""
    print("  enter")
    yield
    print("  exit")

# Funziona: ogni invocazione crea un'istanza indipendente
with cm_rientrante():
    with cm_rientrante():
        print("  annidato")

# contextlib.suppress e un esempio di CM rientrante dalla stdlib
from contextlib import suppress
soppressore = suppress(ValueError)
with soppressore:
    with soppressore:
        raise ValueError("test")
```

---

### contextlib Avanzato: ExitStack, AsyncExitStack, aclosing

#### ExitStack come Gestore di Cleanup Complesso

`ExitStack` eccelle nella gestione di scenari dove le risorse vengono acquisite incrementalmente e un fallimento in mezzo richiede il rollback delle risorse gia acquisite:

```python
from contextlib import ExitStack

def inizializza_sistema(config: dict) -> dict:
    """Acquisisce risorse incrementalmente con rollback su errore."""
    risorse = {}
    with ExitStack() as stack:
        # Se apri_db fallisce, nessun cleanup necessario
        db = apri_connessione_db(config["db_dsn"])
        stack.callback(db.close)
        risorse["db"] = db

        # Se apri_cache fallisce, db viene chiuso automaticamente
        cache = apri_connessione_cache(config["cache_url"])
        stack.callback(cache.disconnect)
        risorse["cache"] = cache

        # Se apri_queue fallisce, cache e db vengono chiusi
        queue = apri_connessione_queue(config["queue_url"])
        stack.callback(queue.close)
        risorse["queue"] = queue

        # Tutto OK: trasferisci la responsabilita al chiamante
        stack.pop_all()  # Nessun cleanup da ExitStack

    return risorse  # Il chiamante gestisce il cleanup
```

#### AsyncExitStack

Per risorse asincrone, `AsyncExitStack` offre le stesse funzionalita in contesto `async`:

```python
from contextlib import AsyncExitStack
import asyncio

async def pipeline_asincrona():
    async with AsyncExitStack() as stack:
        db = await stack.enter_async_context(
            sessione_database_async("postgresql://localhost/db")
        )
        cache = await stack.enter_async_context(
            connessione_cache_async("redis://localhost")
        )
        # Entrambe chiuse automaticamente, in ordine LIFO
```

#### ExitStack: Pattern pop_all() per Trasferimento di Responsabilita

Il metodo `pop_all()` e uno degli aspetti piu potenti di `ExitStack`. Trasferisce tutte le callback di cleanup registrate a un **nuovo** `ExitStack`, lasciando quello originale vuoto. Questo pattern e fondamentale per il "two-phase initialization" dove si acquisiscono risorse in una fase e si trasferisce la responsabilita di cleanup al chiamante:

```python
from contextlib import ExitStack

class ServerApplicazione:
    """Server che acquisisce risorse con rollback automatico su errore."""

    def __init__(self):
        self._cleanup_stack = ExitStack()
        self._risorse: dict = {}

    def avvia(self, config: dict) -> None:
        """Avvia il server acquisendo risorse incrementalmente."""
        with ExitStack() as stack_temporaneo:
            # Fase 1: acquisizione risorse (se fallisce → rollback automatico)
            db = apri_db(config["db"])
            stack_temporaneo.callback(db.close)
            self._risorse["db"] = db

            cache = apri_cache(config["cache"])
            stack_temporaneo.callback(cache.disconnect)
            self._risorse["cache"] = cache

            worker_pool = crea_pool(config["workers"])
            stack_temporaneo.callback(worker_pool.shutdown)
            self._risorse["workers"] = worker_pool

            # Fase 2: tutto OK → trasferisci responsabilita
            self._cleanup_stack = stack_temporaneo.pop_all()
            # stack_temporaneo e ora vuoto, non chiudera nulla

    def ferma(self) -> None:
        """Ferma il server rilasciando tutte le risorse (ordine LIFO)."""
        self._cleanup_stack.close()
```

#### ExitStack.enter_context() e callback()

`ExitStack` fornisce due modi principali per registrare risorse:

```python
from contextlib import ExitStack, contextmanager

@contextmanager
def risorsa_monitorata(nome: str):
    print(f"  Acquisita: {nome}")
    try:
        yield nome
    finally:
        print(f"  Rilasciata: {nome}")

with ExitStack() as stack:
    # enter_context(): per context manager che producono un valore
    r1 = stack.enter_context(risorsa_monitorata("database"))
    r2 = stack.enter_context(risorsa_monitorata("cache"))

    # callback(): per funzioni di cleanup semplici
    stack.callback(print, "  Cleanup personalizzato 1")
    stack.callback(print, "  Cleanup personalizzato 2")

    print(f"  Risorse attive: {r1}, {r2}")

# Output (ordine LIFO):
#   Acquisita: database
#   Acquisita: cache
#   Risorse attive: database, cache
#   Cleanup personalizzato 2
#   Cleanup personalizzato 1
#   Rilasciata: cache
#   Rilasciata: database
```

#### AsyncExitStack: Gestione Risorse Asincrone Complesse

`AsyncExitStack` supporta sia context manager sincroni sia asincroni nella stessa struttura, un requisito frequente nelle applicazioni web e nei servizi:

```python
import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

@asynccontextmanager
async def pool_connessioni_async(dsn: str, min_conn: int = 2, max_conn: int = 10):
    """Simula un pool di connessioni async con lifecycle management."""
    print(f"Pool: apertura ({min_conn}-{max_conn} connessioni) → {dsn}")
    pool = {"dsn": dsn, "attive": min_conn}
    try:
        yield pool
    finally:
        print(f"Pool: chiusura {pool['attive']} connessioni → {dsn}")
        await asyncio.sleep(0.05)  # Simula cleanup asincrono


async def avvia_servizio(config: dict):
    """Avvia un servizio con risorse eterogenee (sync + async)."""
    async with AsyncExitStack() as stack:
        # Context manager asincrono
        db_pool = await stack.enter_async_context(
            pool_connessioni_async(config["db_dsn"])
        )

        # Context manager sincrono nella stessa stack
        log_file = stack.enter_context(
            open(config["log_path"], "a")
        )

        # Callback asincrona
        async def notifica_shutdown():
            print("Invio notifica shutdown...")
            await asyncio.sleep(0.02)

        stack.push_async_callback(notifica_shutdown)

        # Callback sincrona
        stack.callback(print, "Cleanup finale sincrono")

        print(f"Servizio avviato: db={db_pool['dsn']}, log={log_file.name}")
        # ... logica del servizio ...

    # All'uscita: callback async → callback sync → CM sync → CM async (LIFO)


# asyncio.run(avvia_servizio({"db_dsn": "postgresql://...", "log_path": "/tmp/app.log"}))
```

---

## Combinare i Pattern

I tre pattern — decoratori, generatori e context manager — possono essere combinati per creare soluzioni eleganti e potenti. Vediamo alcuni esempi di composizione.

### Decoratore che Usa un Context Manager

```python
import functools
import time
from contextlib import contextmanager

@contextmanager
def ambiente_monitorato(nome_funzione):
    """Context manager per il monitoraggio."""
    inizio = time.perf_counter()
    print(f"[INIZIO] {nome_funzione}")
    try:
        yield
    finally:
        durata = time.perf_counter() - inizio
        print(f"[FINE] {nome_funzione} - {durata:.4f}s")

def monitora(func):
    """Decoratore che usa il context manager ambiente_monitorato."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with ambiente_monitorato(func.__name__):
            return func(*args, **kwargs)
    return wrapper

@monitora
def calcolo_lungo():
    """Funzione che viene monitorata automaticamente."""
    total = sum(i ** 2 for i in range(1_000_000))
    return total
```

### Context Manager Basato su Generatore (contextlib)

Questo pattern e gia stato presentato nella sezione `contextlib` ed e di per se la combinazione naturale di generatori e context manager. Approfondiamo un caso piu complesso con gestione dello stato.

```python
from contextlib import contextmanager

@contextmanager
def ambiente_test(nome_test, dati_fixture=None):
    """Prepara un ambiente di test con fixture e teardown."""
    print(f"=== Setup: {nome_test} ===")
    ambiente = {
        "nome": nome_test,
        "dati": dati_fixture or {},
        "risultati": [],
        "errori": []
    }

    try:
        yield ambiente
    except AssertionError as e:
        ambiente["errori"].append(str(e))
        print(f"FALLITO: {e}")
    finally:
        n_risultati = len(ambiente["risultati"])
        n_errori = len(ambiente["errori"])
        stato = "PASSATO" if n_errori == 0 else "FALLITO"
        print(f"=== Teardown: {nome_test} [{stato}] ===")
        print(f"    Risultati: {n_risultati}, Errori: {n_errori}")
```

### Generatore Decorato

```python
import functools

def limita_produzione(max_elementi):
    """Decoratore che limita il numero di elementi prodotti da un generatore."""
    def decoratore(gen_func):
        @functools.wraps(gen_func)
        def wrapper(*args, **kwargs):
            gen = gen_func(*args, **kwargs)
            for i, valore in enumerate(gen):
                if i >= max_elementi:
                    break
                yield valore
        return wrapper
    return decoratore

def registra_generatore(gen_func):
    """Decoratore che registra ogni valore prodotto dal generatore."""
    @functools.wraps(gen_func)
    def wrapper(*args, **kwargs):
        gen = gen_func(*args, **kwargs)
        for valore in gen:
            print(f"[GEN {gen_func.__name__}] Prodotto: {valore}")
            yield valore
    return wrapper

@registra_generatore
@limita_produzione(10)
def numeri_naturali():
    """Genera numeri naturali all'infinito."""
    n = 1
    while True:
        yield n
        n += 1

print(list(numeri_naturali()))
# [GEN numeri_naturali] Prodotto: 1
# [GEN numeri_naturali] Prodotto: 2
# ...
# [GEN numeri_naturali] Prodotto: 10
# [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

### Esempio Completo: Pipeline di Elaborazione Dati

Questo esempio combina tutti e tre i pattern in una pipeline di elaborazione dati realistica.

```python
import functools
import time
from contextlib import contextmanager

# --- DECORATORE: misura le performance di ogni stadio della pipeline ---
def stadio_pipeline(nome_stadio):
    """Decoratore che misura e registra le performance di uno stadio."""
    def decoratore(gen_func):
        @functools.wraps(gen_func)
        def wrapper(*args, **kwargs):
            conteggio = 0
            inizio = time.perf_counter()
            for elemento in gen_func(*args, **kwargs):
                conteggio += 1
                yield elemento
            durata = time.perf_counter() - inizio
            print(f"  [{nome_stadio}] {conteggio} elementi in {durata:.4f}s")
        return wrapper
    return decoratore

# --- CONTEXT MANAGER: gestisce il ciclo di vita della pipeline ---
@contextmanager
def pipeline_elaborazione(nome):
    """Context manager per gestire l'intera pipeline."""
    print(f"\n{'='*50}")
    print(f"Pipeline: {nome}")
    print(f"{'='*50}")
    inizio = time.perf_counter()
    try:
        yield
    finally:
        durata = time.perf_counter() - inizio
        print(f"{'='*50}")
        print(f"Pipeline '{nome}' completata in {durata:.4f}s")
        print(f"{'='*50}\n")

# --- GENERATORI: stadi della pipeline ---
def genera_dati(n):
    """Generatore sorgente: produce dati grezzi."""
    for i in range(n):
        yield {"id": i, "valore": i * 3.14, "valido": i % 3 != 0}

@stadio_pipeline("Filtraggio")
def filtra_validi(flusso):
    """Generatore filtro: seleziona solo i dati validi."""
    for dato in flusso:
        if dato["valido"]:
            yield dato

@stadio_pipeline("Trasformazione")
def trasforma(flusso):
    """Generatore trasformatore: arricchisce i dati."""
    for dato in flusso:
        dato["valore_trasformato"] = round(dato["valore"] ** 2, 2)
        yield dato

@stadio_pipeline("Aggregazione")
def aggrega(flusso, dimensione_batch=10):
    """Generatore aggregatore: raggruppa in batch."""
    batch = []
    for dato in flusso:
        batch.append(dato)
        if len(batch) >= dimensione_batch:
            yield batch
            batch = []
    if batch:
        yield batch

# --- ESECUZIONE: combina tutto ---
with pipeline_elaborazione("Elaborazione Dati Completa"):
    sorgente = genera_dati(100)
    validi = filtra_validi(sorgente)
    trasformati = trasforma(validi)
    risultati = list(aggrega(trasformati, dimensione_batch=5))
    print(f"  Batch prodotti: {len(risultati)}")
```

Questo esempio dimostra la sinergia tra i tre pattern: il decoratore `@stadio_pipeline` aggiunge trasparenza a ogni stadio senza modificarne la logica; i generatori permettono l'elaborazione lazy dei dati attraverso gli stadi; il context manager `pipeline_elaborazione` gestisce il ciclo di vita complessivo della pipeline con setup e teardown garantiti.

---

## Pattern Pratici di Produzione

### Retry con Backoff Esponenziale

Un pattern di produzione che combina decoratore parametrico, logging strutturato e backoff esponenziale con jitter:

```python
import functools
import time
import random
import logging

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    eccezioni: tuple[type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
):
    """Decoratore retry con backoff esponenziale e jitter.

    Implementa il pattern "exponential backoff with full jitter"
    raccomandato da AWS Architecture Blog.
    """
    def decoratore(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for tentativo in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except eccezioni as e:
                    if tentativo == max_retries:
                        logger.error(
                            f"{func.__name__}: fallito dopo {max_retries} tentativi. "
                            f"Ultimo errore: {e}"
                        )
                        raise

                    delay = min(base_delay * (backoff_factor ** (tentativo - 1)), max_delay)
                    jitter = random.uniform(0, delay)
                    logger.warning(
                        f"{func.__name__}: tentativo {tentativo}/{max_retries} fallito "
                        f"({e}). Retry tra {jitter:.2f}s"
                    )
                    time.sleep(jitter)
        return wrapper
    return decoratore

@retry_with_backoff(max_retries=5, eccezioni=(ConnectionError, TimeoutError))
def chiama_servizio_remoto(endpoint: str) -> dict:
    """Chiamata a servizio esterno con retry automatico."""
    ...
```

### Caching Decorator con TTL

```python
import functools
import time
from threading import Lock

def cache_con_ttl(ttl_secondi: float = 300.0, maxsize: int = 128):
    """Decoratore di cache con time-to-live e dimensione massima."""
    def decoratore(func):
        cache: dict[tuple, tuple[float, object]] = {}
        lock = Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            chiave = args + tuple(sorted(kwargs.items()))
            adesso = time.monotonic()

            with lock:
                if chiave in cache:
                    timestamp, valore = cache[chiave]
                    if adesso - timestamp < ttl_secondi:
                        return valore
                    del cache[chiave]

            risultato = func(*args, **kwargs)

            with lock:
                if len(cache) >= maxsize:
                    # Rimuovi l'entry piu vecchia
                    piu_vecchia = min(cache, key=lambda k: cache[k][0])
                    del cache[piu_vecchia]
                cache[chiave] = (adesso, risultato)

            return risultato

        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            "size": len(cache), "maxsize": maxsize, "ttl": ttl_secondi
        }
        return wrapper
    return decoratore

@cache_con_ttl(ttl_secondi=60.0)
def ottieni_configurazione(servizio: str) -> dict:
    """Carica configurazione con cache di 60 secondi."""
    ...
```

### Circuit Breaker — Protezione dai Servizi Instabili

Il pattern Circuit Breaker (ispirato al design di Michael Nygard in *Release It!*) protegge un sistema dal chiamare ripetutamente un servizio guasto. Implementato come decoratore, opera con tre stati:

- **CLOSED** (chiuso): operazione normale, le chiamate passano al servizio
- **OPEN** (aperto): il servizio e considerato guasto, le chiamate falliscono immediatamente senza tentare la connessione
- **HALF-OPEN** (semi-aperto): dopo un timeout di attesa, permette un numero limitato di chiamate di test per verificare se il servizio si e ripreso

```python
import functools
import time
import threading
from enum import Enum

class StatoCircuito(Enum):
    CHIUSO = "chiuso"        # Operazione normale
    APERTO = "aperto"        # Servizio guasto, fallimento immediato
    SEMI_APERTO = "semi_aperto"  # Test di ripresa


class CircuitBreakerAperto(Exception):
    """Eccezione sollevata quando il circuit breaker e aperto."""


def circuit_breaker(
    soglia_errori: int = 5,
    timeout_recupero: float = 30.0,
    eccezioni_monitorate: tuple[type[Exception], ...] = (Exception,),
):
    """Decoratore Circuit Breaker con gestione degli stati.

    Args:
        soglia_errori: numero di errori consecutivi per aprire il circuito
        timeout_recupero: secondi prima di passare a semi-aperto
        eccezioni_monitorate: solo queste eccezioni incrementano il contatore
    """
    def decoratore(func):
        # Stato condiviso (thread-safe)
        lock = threading.Lock()
        stato = {"corrente": StatoCircuito.CHIUSO}
        contatore_errori = {"n": 0}
        ultimo_errore = {"ts": 0.0}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                adesso = time.monotonic()

                if stato["corrente"] == StatoCircuito.APERTO:
                    # Verifica se il timeout di recupero e scaduto
                    if adesso - ultimo_errore["ts"] >= timeout_recupero:
                        stato["corrente"] = StatoCircuito.SEMI_APERTO
                    else:
                        tempo_restante = timeout_recupero - (adesso - ultimo_errore["ts"])
                        raise CircuitBreakerAperto(
                            f"{func.__name__}: circuito aperto, "
                            f"riprova tra {tempo_restante:.1f}s"
                        )

            # Tenta la chiamata
            try:
                risultato = func(*args, **kwargs)
            except eccezioni_monitorate as e:
                with lock:
                    contatore_errori["n"] += 1
                    ultimo_errore["ts"] = time.monotonic()

                    if contatore_errori["n"] >= soglia_errori:
                        stato["corrente"] = StatoCircuito.APERTO
                raise
            else:
                # Successo: resetta il circuito
                with lock:
                    contatore_errori["n"] = 0
                    stato["corrente"] = StatoCircuito.CHIUSO
                return risultato

        # Metodi di introspezione
        wrapper.stato = lambda: stato["corrente"]
        wrapper.errori = lambda: contatore_errori["n"]
        wrapper.reset = lambda: (
            stato.update(corrente=StatoCircuito.CHIUSO),
            contatore_errori.update(n=0),
        )

        return wrapper
    return decoratore


@circuit_breaker(soglia_errori=3, timeout_recupero=10.0, eccezioni_monitorate=(ConnectionError,))
def interroga_servizio(endpoint: str) -> dict:
    """Chiamata a servizio esterno protetta da circuit breaker."""
    ...

# interroga_servizio.stato()   → StatoCircuito.CHIUSO
# interroga_servizio.errori()  → 0
# interroga_servizio.reset()   → resetta manualmente il circuito
```

### Feature Flag — Toggle Condizionale di Funzionalita

Il pattern Feature Flag (o Feature Toggle) permette di abilitare o disabilitare funzionalita senza deploy, utile per rollout graduali, A/B testing e gestione di funzionalita sperimentali:

```python
import functools
from typing import Callable, Any

class FeatureFlags:
    """Gestore centralizzato di feature flags."""

    def __init__(self):
        self._flags: dict[str, bool] = {}
        self._fallback: dict[str, Callable] = {}

    def imposta(self, nome: str, attivo: bool) -> None:
        self._flags[nome] = attivo

    def attivo(self, nome: str) -> bool:
        return self._flags.get(nome, False)

    def richiede(
        self,
        nome_flag: str,
        fallback: Callable | None = None,
        messaggio: str = "",
    ):
        """Decoratore che esegue la funzione solo se il flag e attivo.

        Args:
            nome_flag: nome del feature flag da verificare
            fallback: funzione alternativa se il flag e disattivato
            messaggio: messaggio di log quando il flag e disattivato
        """
        def decoratore(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.attivo(nome_flag):
                    return func(*args, **kwargs)
                elif fallback is not None:
                    return fallback(*args, **kwargs)
                else:
                    import logging
                    logging.getLogger(__name__).info(
                        f"Feature '{nome_flag}' disattivata"
                        f"{': ' + messaggio if messaggio else ''}"
                    )
                    return None
            return wrapper
        return decoratore


# Uso pratico
flags = FeatureFlags()
flags.imposta("nuovo_algoritmo_ricerca", False)
flags.imposta("notifiche_push", True)


def ricerca_classica(query: str) -> list:
    return [f"risultato classico per '{query}'"]


@flags.richiede("nuovo_algoritmo_ricerca", fallback=ricerca_classica)
def ricerca_avanzata(query: str) -> list:
    """Nuovo algoritmo di ricerca (in fase di testing)."""
    return [f"risultato avanzato per '{query}'"]


@flags.richiede("notifiche_push")
def invia_notifica(utente: str, messaggio: str) -> dict:
    return {"utente": utente, "inviato": True}


# ricerca_avanzata("python")  → usa ricerca_classica (flag disattivato)
# flags.imposta("nuovo_algoritmo_ricerca", True)
# ricerca_avanzata("python")  → usa ricerca_avanzata (flag attivato)
```

---

## Best Practices

1. **Usare sempre `functools.wraps` nei decoratori.** Senza questo decoratore, la funzione decorata perde i propri metadati originali (`__name__`, `__doc__`, `__module__`), rendendo il debugging e l'introspezione estremamente difficili. E una riga di codice che previene ore di confusione.

2. **Preferire i generatori alle liste quando la dimensione dei dati non e nota a priori.** Se si lavora con file di grandi dimensioni, risultati di query al database o stream di rete, i generatori consumano memoria costante indipendentemente dalla quantita di dati. Costruire una lista di milioni di elementi quando ne servono pochi e uno spreco di risorse evitabile.

3. **Usare `with` per qualsiasi risorsa che richiede cleanup.** File, connessioni di rete, lock, transazioni di database: ogni risorsa che deve essere rilasciata esplicitamente dovrebbe essere gestita tramite un context manager. L'istruzione `with` garantisce il rilascio anche in presenza di eccezioni, eliminando una delle cause piu comuni di resource leak.

4. **Preferire `@contextmanager` alle classi per context manager semplici.** Il decoratore `@contextmanager` di `contextlib` produce codice piu conciso e leggibile quando la logica di setup/teardown e lineare. Le classi con `__enter__`/`__exit__` restano preferibili quando il context manager deve mantenere stato complesso o essere ereditato.

5. **Non abusare dei decoratori: la leggibilita viene prima.** Uno stack di cinque o sei decoratori su una singola funzione rende il codice difficile da seguire e da debuggare. Se la logica dei decoratori diventa troppo complessa, potrebbe essere piu chiaro estrarre la funzionalita in classi o in una pipeline esplicita.

6. **Documentare chiaramente se un decoratore altera il tipo di ritorno.** Se un decoratore modifica il valore restituito dalla funzione decorata (ad esempio restituendo una lista invece di un singolo valore, o wrappando il risultato), questo deve essere documentato esplicitamente. Le sorprese nei tipi di ritorno sono una fonte comune di bug.

7. **Ricordare che i generatori sono monouso.** Un generatore, una volta esaurito, non puo essere riavviato. Se si necessita di iterare piu volte sugli stessi dati, occorre o creare un nuovo generatore, o convertire i risultati in una lista, oppure implementare un iterable (classe con `__iter__` che restituisce un nuovo iteratore a ogni chiamata).

8. **Gestire le eccezioni in modo esplicito nei context manager.** Il metodo `__exit__` riceve informazioni sull'eccezione. Decidere consapevolmente se sopprimere o propagare un'eccezione e documentare la scelta. Un context manager che sopprime eccezioni silenziosamente puo nascondere bug gravi.

9. **Sfruttare `itertools` invece di reinventare la ruota.** Il modulo `itertools` fornisce implementazioni ottimizzate in C per i pattern di iterazione piu comuni. Prima di scrivere un generatore personalizzato per operazioni come raggruppamento, concatenazione o filtraggio, verificare se `itertools` offre gia una soluzione.

10. **Testare i decoratori separatamente dalla logica decorata.** Un decoratore e una unita di codice indipendente e dovrebbe avere i propri test unitari. Testare sia il decoratore in isolamento (verificando che modifichi correttamente il comportamento) sia le funzioni decorate (verificando che il risultato complessivo sia corretto) garantisce un copertura completa.

---

## Troubleshooting

### Problema: il decoratore perde i metadati della funzione

**Sintomo:** `funzione_decorata.__name__` restituisce `"wrapper"` invece del nome originale.

**Causa:** manca `@functools.wraps(func)` nel wrapper.

**Soluzione:**
```python
# SBAGLIATO
def decoratore(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# CORRETTO
def decoratore(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

### Problema: il decoratore class-based non funziona con i metodi di istanza

**Sintomo:** `TypeError: metodo() missing 1 required positional argument: 'self'`.

**Causa:** la classe decoratore non implementa `__get__`, quindi non supporta il protocollo descriptor necessario per i metodi bound.

**Soluzione:** implementare `__get__` come mostrato nella sezione [Decoratori Class-Based Avanzati](#decoratori-class-based-avanzati).

### Problema: il generatore sembra non produrre nulla

**Sintomo:** nessun output dalla funzione generatore.

**Causa:** si e assegnata la funzione generatore a una variabile ma non si e iterato sull'oggetto restituito. Chiamare la funzione generatore crea l'oggetto; non esegue il codice.

**Soluzione:**
```python
# SBAGLIATO
risultato = mio_generatore()  # Crea l'oggetto, nessun codice eseguito

# CORRETTO
for elemento in mio_generatore():
    print(elemento)
```

### Problema: StopIteration si propaga silenziosamente in Python 3.7+

**Sintomo:** un generatore termina inaspettatamente senza produrre tutti i valori attesi.

**Causa:** dal PEP 479 (obbligatorio da Python 3.7), un `StopIteration` non catturato dentro un generatore viene convertito in `RuntimeError`. Ma codice che chiama `next()` senza default dentro un generatore puo terminarlo prematuramente.

**Soluzione:**
```python
# SBAGLIATO
def mio_gen(it):
    while True:
        yield next(it)  # StopIteration → RuntimeError

# CORRETTO
def mio_gen(it):
    for elemento in it:
        yield elemento
    # oppure
    yield from it
```

### Problema: ExitStack callback non vengono eseguiti nell'ordine atteso

**Sintomo:** i callback di cleanup vengono eseguiti in ordine inverso rispetto a quello di registrazione.

**Causa:** `ExitStack` segue la semantica LIFO (Last In, First Out), come un blocco `finally` annidato. Questo e il comportamento corretto e intenzionale.

### Problema: context manager @contextmanager non sopprime le eccezioni

**Sintomo:** l'eccezione si propaga anche se si e cercato di catturarla nel generatore.

**Causa:** per sopprimere un'eccezione in un `@contextmanager`, il generatore deve catturarla e **non** rilanciarla. Il `yield` deve essere dentro un `try/except`:

```python
@contextmanager
def sopprimi_errore():
    try:
        yield
    except ValueError:
        pass  # Soppressa
    # NON fare: except ValueError: raise
```

---

## Esercizi

### Esercizio 1 — Decoratore @throttle
Implementare un decoratore `@throttle(min_intervallo)` che garantisce un intervallo minimo in secondi tra chiamate consecutive alla stessa funzione. Se la funzione viene chiamata troppo presto, il decoratore deve attendere il tempo residuo prima di eseguirla. Usare `@functools.wraps` e `time.monotonic`.

### Esercizio 2 — Generatore di numeri di Fibonacci con reset
Creare un generatore bidirezionale di Fibonacci che supporti `send("reset")` per ripartire da (0, 1). Il generatore deve anche gestire `close()` stampando il numero di valori prodotti.

### Esercizio 3 — Context manager per transazioni idempotenti
Implementare un context manager class-based che registri operazioni con relative compensazioni. In caso di eccezione, deve eseguire le compensazioni in ordine LIFO. Aggiungere supporto per operazioni annidate (sotto-transazioni).

### Esercizio 4 — Pipeline di elaborazione log
Combinare generatori, un decoratore `@stadio_pipeline` e un context manager per costruire una pipeline che: (a) legge righe da un file, (b) filtra per livello (ERROR, WARNING), (c) estrae timestamp e messaggio, (d) raggruppa in batch da 100. Ogni stadio deve riportare il numero di elementi elaborati.

### Esercizio 5 — yield from con aggregazione
Scrivere un sotto-generatore che accumula statistiche (media, minimo, massimo) sui valori ricevuti tramite `send()` e le restituisce con `return`. Il generatore delegante deve usare `yield from` per ottenere il risultato finale.

### Esercizio 6 — Decoratore @retry asincrono
Adattare il decoratore `@retry_with_backoff` per funzioni `async def`. Deve usare `asyncio.sleep` al posto di `time.sleep` e preservare la firma asincrona della funzione decorata.

---

## Letture e Riferimenti

- [Python Data Model — Documentazione ufficiale](https://docs.python.org/3/reference/datamodel.html) — Sezioni su `__enter__`, `__exit__`, `__call__`, `__iter__`, `__next__`
- [PEP 318 — Decorators for Functions and Methods](https://peps.python.org/pep-0318/) — Introduzione dei decoratori
- [PEP 380 — Syntax for Delegating to a Subgenerator](https://peps.python.org/pep-0380/) — `yield from`
- [PEP 342 — Coroutines via Enhanced Generators](https://peps.python.org/pep-0342/) — `send()`, `throw()`, `close()`
- [PEP 343 — The "with" Statement](https://peps.python.org/pep-0343/) — Context manager protocol
- [PEP 479 — Change StopIteration handling inside generators](https://peps.python.org/pep-0479/)
- [PEP 525 — Asynchronous Generators](https://peps.python.org/pep-0525/)
- [contextlib — Documentazione ufficiale](https://docs.python.org/3/library/contextlib.html)
- [itertools — Documentazione ufficiale](https://docs.python.org/3/library/itertools.html) — Include le ricette ufficiali
- [functools — Documentazione ufficiale](https://docs.python.org/3/library/functools.html) — `wraps`, `lru_cache`, `cache`
- Ramalho, L. — *Fluent Python*, 2nd ed. (O'Reilly, 2022) — Capitoli 9 (decoratori), 17 (iteratori/generatori), 18 (context manager)

---

## Cross-link

- **09-type-hints-e-mypy.md** — Typing di decoratori con `ParamSpec`, generatori con `Generator[Y, S, R]`, context manager con `__exit__` tipizzato
- **10-programmazione-asincrona.md** — `async for`, `async with`, generatori asincroni in contesto asyncio
- **08-testing.md** — Testing di decoratori, fixture pytest come context manager
- **07-error-handling-e-logging.md** — Gestione eccezioni in `__exit__`, pattern di logging strutturato
- **02-oop.md** — Protocollo descriptor (`__get__`), `__call__`, dunder methods

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Closure** | Funzione interna che cattura e mantiene riferimento alle variabili della funzione esterna che l'ha creata, anche dopo che quest'ultima ha terminato |
| **Context Manager** | Oggetto che implementa `__enter__` e `__exit__`, usato con `with` per garantire setup e teardown sicuri |
| **Coroutine** | Funzione che puo sospendere e riprendere la propria esecuzione; in Python pre-3.5, implementata tramite generatori con `send()` |
| **Decorator** | Funzione (o classe callable) che accetta una funzione/classe e ne restituisce una versione modificata; applicata con la sintassi `@` |
| **Descriptor** | Oggetto che implementa `__get__`, `__set__` e/o `__delete__`; controlla come un attributo viene letto, scritto o eliminato |
| **ExitStack** | Context manager di `contextlib` che gestisce un numero dinamico di context manager e callback di cleanup |
| **Generator** | Funzione che usa `yield` per produrre valori lazy; l'oggetto restituito implementa il protocollo iterator |
| **Generator Expression** | Espressione con sintassi simile alla list comprehension ma con parentesi tonde; crea un generatore lazy |
| **Iterable** | Oggetto con `__iter__()` che restituisce un iteratore; liste, tuple, stringhe, dizionari sono iterabili |
| **Iterator** | Oggetto con `__iter__()` e `__next__()`; produce valori uno alla volta fino a sollevare `StopIteration` |
| **Lazy Evaluation** | Strategia di valutazione che ritarda il calcolo di un'espressione fino al momento in cui il suo valore e effettivamente necessario |
| **Memoizzazione** | Tecnica di caching che memorizza i risultati di chiamate a funzione per evitare ricalcoli con gli stessi argomenti |
| **StopIteration** | Eccezione sollevata da `__next__()` quando l'iteratore e esaurito; il ciclo `for` la cattura automaticamente |
| **Wrapper** | Funzione interna al decoratore che avvolge la funzione originale, estendendone il comportamento |
| **yield from** | Sintassi che delega l'iterazione a un sotto-generatore, propagando automaticamente `send()`, `throw()`, `close()` e il valore di ritorno |

---

> **Nota finale:** Decoratori, generatori e context manager sono strumenti che, usati con giudizio, elevano significativamente la qualita del codice Python. La chiave e comprendere non solo la meccanica di ciascun pattern, ma anche quando e appropriato applicarlo. Un codice che li utilizza correttamente risulta piu pulito, piu sicuro e piu facile da mantenere nel tempo.
