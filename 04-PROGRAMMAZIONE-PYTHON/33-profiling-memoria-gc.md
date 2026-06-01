---
corso: "Programmazione Python"
fase: "5 — Qualità e Manutenzione"
modulo: "33"
titolo: "Profiling, Memoria e Garbage Collection"
versione: "Python 3.12+ / cProfile / tracemalloc / py-spy / scalene"
livello: "Avanzato"
prerequisiti:
  - "25 — Performance"
  - "07 — Error Handling e Logging"
  - "10 — Programmazione Asincrona"
obiettivi:
  - "Profilare codice Python con cProfile, py-spy e scalene"
  - "Analizzare consumo di memoria con tracemalloc e memray"
  - "Comprendere il garbage collector CPython: reference counting e cycle detector"
  - "Identificare e risolvere memory leak in applicazioni long-running"
  - "Ottimizzare allocazioni con __slots__, intern e buffer protocol"
  - "Monitorare performance e memoria in produzione"
tag: [profiling, memoria, garbage-collection, cProfile, tracemalloc, py-spy, scalene, memray]
---

# Profiling, Memoria e Garbage Collection — Guida Completa

> **Modulo 33** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Performance](25-performance.md), [Error Handling](07-error-handling-e-logging.md), [Programmazione Asincrona](10-programmazione-asincrona.md)
>
> Al termine di questo modulo saprai:
> 1. Profilare codice Python con cProfile, py-spy e scalene
> 2. Analizzare consumo di memoria con tracemalloc e memray
> 3. Comprendere il garbage collector CPython: reference counting e cycle detector
> 4. Identificare e risolvere memory leak in applicazioni long-running
> 5. Ottimizzare allocazioni con `__slots__`, `intern` e buffer protocol
> 6. Monitorare performance e memoria in produzione
>
> **Tempo stimato:** 6-8 ore · **Livello:** Avanzato

## Idee guida

1. **Measure first:** ogni intervento sulla memoria o sulle performance parte dal profiling, mai dall'intuizione.
2. **CPython ha due meccanismi di deallocazione:** reference counting (immediato, deterministico) e generational GC (per i cicli).
3. **tracemalloc e il punto di partenza** per la memory analysis: built-in, zero dipendenze, snapshot diff.
4. **py-spy e scalene** per il CPU profiling in produzione: sample-based, basso overhead, nessuna modifica al codice.
5. **Il garbage collector generazionale** raccoglie gen-0 frequentemente e gen-2 raramente — il tuning dei threshold ha impatto diretto su latenza e throughput.
6. **Memory leak in Python** esistono eccome: reference cycle, cache globali, closure catturate, `__del__` mal implementati.
7. **`__slots__`, generatori, memoryview, struct** sono strumenti concreti per ridurre il consumo di memoria.
8. **Il profiling in produzione** (continuous profiling) e oggi praticabile con overhead < 2% usando strumenti come Pyroscope e py-spy.


## Indice

1. [Il modello di memoria CPython](#il-modello-di-memoria-cpython)
2. [Layout degli oggetti Python in memoria](#layout-degli-oggetti-python-in-memoria)
3. [Reference counting](#reference-counting)
4. [Garbage collector generazionale](#garbage-collector-generazionale)
5. [Il modulo gc](#il-modulo-gc)
6. [CPU profiling](#cpu-profiling)
7. [Memory profiling](#memory-profiling)
8. [Weak references](#weak-references)
9. [__slots__](#__slots__)
10. [String interning e integer caching](#string-interning-e-integer-caching)
11. [Strutture dati memory-efficient](#strutture-dati-memory-efficient)
12. [Generatori e processing di grandi dataset](#generatori-e-processing-di-grandi-dataset)
13. [Semantica di copia](#semantica-di-copia)
14. [Flusso di lavoro per il profiling](#flusso-di-lavoro-per-il-profiling)
15. [Profiling in produzione](#profiling-in-produzione)
16. [Benchmarking](#benchmarking)
17. [Pattern di ottimizzazione memoria](#pattern-di-ottimizzazione-memoria)
18. [Memory leak: cause, rilevamento, risoluzione](#memory-leak-cause-rilevamento-risoluzione)
19. [Troubleshooting](#troubleshooting)
20. [FAQ](#faq)
21. [Glossario](#glossario)
22. [Esercizi](#esercizi)
23. [Letture consigliate](#letture-consigliate)

---

## Il modello di memoria CPython

CPython — l'implementazione di riferimento di Python — gestisce la memoria attraverso un sistema stratificato che combina l'allocatore del sistema operativo, un allocatore custom ottimizzato per piccoli oggetti e due meccanismi di deallocazione complementari.

### Gerarchia degli allocatori

Il sistema di allocazione di CPython opera su tre livelli:

```
+-----------------------------------------------------+
|  Livello 3: Object-specific allocators               |
|  (list, dict, tuple, frame, ecc.)                    |
+-----------------------------------------------------+
|  Livello 2: Python object allocator (pymalloc)       |
|  Arena -> Pool -> Block                              |
+-----------------------------------------------------+
|  Livello 1: Python raw memory allocator              |
|  (PyMem_RawMalloc, wrappa malloc/realloc/free)       |
+-----------------------------------------------------+
|  Livello 0: OS allocator                             |
|  (malloc/free, mmap, VirtualAlloc, ecc.)             |
+-----------------------------------------------------+
```

**Livello 0 — OS allocator:** il sistema operativo fornisce `malloc()`, `free()` e varianti. CPython li usa direttamente solo per allocazioni > 512 bytes.

**Livello 1 — Raw memory allocator:** `PyMem_RawMalloc`, `PyMem_RawRealloc`, `PyMem_RawFree`. Wrappers sottili attorno a `malloc()` del sistema. Usati quando serve memoria non tracciata dal GC (buffer interni del runtime, strutture C ausiliarie).

**Livello 2 — pymalloc (Object allocator):** l'allocatore custom di CPython, ottimizzato per oggetti piccoli (fino a 512 bytes). Questo e il cuore del sistema: riduce drasticamente il numero di chiamate a `malloc()` del sistema operativo, che sono costose.

**Livello 3 — Object-specific allocators:** allocatori specializzati per tipi specifici. Ad esempio, le tuple piccole usano una free list interna: quando una tupla viene deallocata, la memoria non viene restituita al sistema ma tenuta pronta per la prossima tupla della stessa dimensione.

### pymalloc: Arena, Pool, Block

pymalloc organizza la memoria in tre unita gerarchiche:

```
Arena (256 KiB)
├── Pool 0 (4 KiB) — size class: 16 bytes
│   ├── Block 0 (16 bytes) — [occupato]
│   ├── Block 1 (16 bytes) — [libero]
│   ├── Block 2 (16 bytes) — [occupato]
│   └── ...
├── Pool 1 (4 KiB) — size class: 32 bytes
│   ├── Block 0 (32 bytes) — [occupato]
│   └── ...
├── Pool 2 (4 KiB) — size class: 48 bytes
│   └── ...
└── ... (fino a 64 pool per arena)
```

**Arena (256 KiB):** l'unita piu grande allocata dal sistema operativo. Ogni arena contiene fino a 64 pool. Le arene vengono ordinate per "utilizzo": CPython preferisce allocare da arene piu piene, cosi le arene quasi vuote possono essere restituite al sistema operativo. Questo e un dettaglio implementativo cruciale: la memoria viene effettivamente liberata solo quando un'intera arena e vuota.

**Pool (4 KiB, una pagina di memoria):** ogni pool gestisce blocchi di una sola dimensione (la *size class*). Un pool per blocchi da 32 bytes contiene solo blocchi da 32 bytes. Questo elimina la frammentazione interna al pool.

**Block (8-512 bytes, multipli di 8):** l'unita minima di allocazione. Le size class disponibili sono:

```python
# Size class di pymalloc (CPython 3.12+)
# Index  Size    Request range
#   0     8      1-8 bytes
#   1    16      9-16 bytes
#   2    24      17-24 bytes
#   3    32      25-32 bytes
#   ...
#  63   512     505-512 bytes

# Ogni richiesta viene arrotondata alla size class successiva
# Richiesta di 13 bytes -> allocazione di 16 bytes (size class 1)
# Richiesta di 100 bytes -> allocazione di 104 bytes (size class 12)
```

**Perche 512 bytes come soglia?** Oggetti piu grandi di 512 bytes passano direttamente a `malloc()` del sistema. La soglia bilancia due fattori: sotto 512 bytes, pymalloc e significativamente piu veloce di malloc; sopra, l'overhead della gestione delle arene non giustifica il vantaggio.

### Visualizzazione della memoria di un processo Python

```python
import sys

# Dimensione base di oggetti comuni
print(f"int(0):        {sys.getsizeof(0)} bytes")        # 28 bytes
print(f"int(1):        {sys.getsizeof(1)} bytes")        # 28 bytes
print(f"int(2**30):    {sys.getsizeof(2**30)} bytes")    # 32 bytes
print(f"float(0.0):    {sys.getsizeof(0.0)} bytes")      # 24 bytes
print(f"str(''):       {sys.getsizeof('')} bytes")        # 49 bytes
print(f"str('a'):      {sys.getsizeof('a')} bytes")      # 50 bytes
print(f"list([]):      {sys.getsizeof([])} bytes")        # 56 bytes
print(f"dict({{}}):      {sys.getsizeof({})} bytes")      # 64 bytes
print(f"tuple(()):     {sys.getsizeof(())} bytes")       # 40 bytes
print(f"set():         {sys.getsizeof(set())} bytes")    # 216 bytes
print(f"None:          {sys.getsizeof(None)} bytes")     # 16 bytes
print(f"True:          {sys.getsizeof(True)} bytes")     # 28 bytes

# Attenzione: sys.getsizeof() non conta i riferimenti contenuti
lista = [1, 2, 3]
print(f"\nlist([1,2,3]) shallow: {sys.getsizeof(lista)} bytes")
# Ma la dimensione reale include i 3 interi referenziati
dimensione_totale = sys.getsizeof(lista) + sum(sys.getsizeof(x) for x in lista)
print(f"list([1,2,3]) deep:    {dimensione_totale} bytes")
```

### Free list e riciclo di oggetti

CPython mantiene *free list* interne per i tipi piu comuni, evitando di deallocare e riallocare continuamente:

```python
# Le tuple piccole (0-19 elementi) usano free list
# Quando una tupla viene deallocata, la sua memoria resta in una free list
# La prossima tupla della stessa dimensione la riusa

import sys

# Dimostrazione: id() riusa indirizzi
t1 = (1, 2, 3)
addr1 = id(t1)
del t1

t2 = (4, 5, 6)
addr2 = id(t2)

# Spesso addr1 == addr2: stessa memoria riciclata
print(f"Stesso indirizzo: {addr1 == addr2}")

# Anche float, int piccoli e frame object usano free list
# Questo e il motivo per cui creare/distruggere tuple in un loop
# e molto piu veloce di quanto ci si aspetterebbe
```

### Oggetti immortali (PEP 683, Python 3.12+)

A partire da CPython 3.12, alcuni oggetti vengono marcati come *immortali*: il loro reference count non viene mai modificato, e non partecipano al ciclo di incremento/decremento di `ob_refcnt`. L'implementazione usa un valore sentinella speciale nel campo `ob_refcnt` — quando il runtime rileva questo valore, salta completamente le operazioni `Py_INCREF` e `Py_DECREF`.

**Quali oggetti sono immortali:**
- `None`, `True`, `False`
- Interi piccoli pre-allocati (-5 a 256)
- Stringhe internate dal runtime (nomi di built-in, keyword, ecc.)
- Oggetti tipo (`int`, `str`, `list`, `dict`, ecc.)
- Costanti globali del runtime (`Ellipsis`, `NotImplemented`)

**Motivazione — Meta/Instagram e il modello pre-fork:**

Il problema originale che ha motivato PEP 683 e il *copy-on-write* nei server pre-fork. In un'architettura come quella di gunicorn o uWSGI, il processo master carica l'applicazione Python e poi esegue `fork()`. I processi figli condividono le pagine di memoria del padre tramite copy-on-write del kernel. Tuttavia, ogni volta che il reference count di un oggetto condiviso viene modificato (anche solo incrementato e decrementato durante un'operazione temporanea), la pagina di memoria che contiene quell'oggetto viene copiata per il processo figlio. Con milioni di oggetti condivisi, questo annulla il vantaggio del copy-on-write, causando un consumo di memoria significativo.

Con gli oggetti immortali, gli oggetti condivisi non subiscono aggiornamenti al refcount, le pagine di memoria restano condivise tra i processi figli, e il consumo di memoria post-fork si riduce drasticamente.

```python
import sys

# In CPython 3.12+, gli oggetti immortali hanno un refcount speciale
# Il valore esatto del sentinella e un dettaglio implementativo
# ma si puo osservare il comportamento:

none_ref = sys.getrefcount(None)
print(f"refcount di None: {none_ref}")
# In 3.12+ il valore e estremamente alto (sentinella)
# In 3.11 e precedenti, e un valore "normale" (migliaia)

# Verifica: incrementare riferimenti a None non cambia il refcount
refs = [None] * 10_000
none_ref_dopo = sys.getrefcount(None)
print(f"refcount di None dopo 10k ref: {none_ref_dopo}")
# In 3.12+: identico (immortale, non viene modificato)
# In 3.11-: leggermente incrementato
```

**Impatto sulle prestazioni:**

L'introduzione degli oggetti immortali in 3.12 ha aggiunto un controllo extra nelle operazioni `Py_INCREF`/`Py_DECREF` per verificare se l'oggetto e immortale. Questo ha causato una regressione di performance in alcuni workload (fino al 4-5% in micro-benchmark). In CPython 3.13, sono state introdotte ottimizzazioni che saltano il controllo di immortalita per oggetti che sono quasi certamente non immortali (istanze di classi utente, oggetti lista, ecc.), riducendo l'overhead a livelli trascurabili.

**Interazione con `gc.freeze()`:**

`gc.freeze()` e gli oggetti immortali risolvono problemi simili ma a livelli diversi. `gc.freeze()` opera a livello del garbage collector generazionale (esclude gli oggetti dal tracking GC), mentre gli oggetti immortali operano a livello del reference counting (eliminano le scritture in `ob_refcnt`). In un server pre-fork, si usano entrambi: `gc.freeze()` per evitare scansioni GC inutili nei figli, e gli oggetti immortali per evitare copy-on-write causato dal refcounting.

---

## Layout degli oggetti Python in memoria

Ogni oggetto Python in CPython e rappresentato internamente come una struct C. Capire questa struttura e fondamentale per comprendere l'overhead di memoria e le ottimizzazioni possibili.

### PyObject: la struttura base

Tutti gli oggetti Python derivano da `PyObject`:

```c
// Struttura base (oggetti senza reference count variabile)
typedef struct _object {
    Py_ssize_t ob_refcnt;    // Reference count (8 bytes su 64-bit)
    PyTypeObject *ob_type;   // Puntatore al tipo (8 bytes su 64-bit)
} PyObject;                  // Totale: 16 bytes di header

// Struttura per oggetti di dimensione variabile (list, str, tuple, ecc.)
typedef struct {
    Py_ssize_t ob_refcnt;    // Reference count
    PyTypeObject *ob_type;   // Puntatore al tipo
    Py_ssize_t ob_size;      // Numero di elementi (8 bytes)
} PyVarObject;               // Totale: 24 bytes di header
```

Ogni singolo oggetto Python ha almeno 16 bytes di overhead solo per l'header. Per un intero, l'overhead e particolarmente visibile:

```python
import sys

# Un int C occupa 4 bytes (32 bit) o 8 bytes (64 bit)
# Un int Python occupa almeno 28 bytes!
# Header PyObject: 16 bytes
# ob_digit (valore): almeno 4 bytes
# Padding/allineamento: 8 bytes
print(sys.getsizeof(42))  # 28 bytes — 7x un int C a 32 bit

# Confronto con un array C-style
import array
arr = array.array('i', range(1000))  # 1000 int a 4 bytes ciascuno
lista = list(range(1000))

print(f"array.array: {sys.getsizeof(arr)} bytes")       # ~4056 bytes
print(f"list:        {sys.getsizeof(lista)} bytes")      # ~8056 bytes (puntatori)
# Ma la list contiene riferimenti a 1000 oggetti int separati:
dim_lista_reale = sys.getsizeof(lista) + sum(sys.getsizeof(x) for x in lista)
print(f"list (deep): {dim_lista_reale} bytes")           # ~36056 bytes
# array.array: 7x piu efficiente in memoria
```

### Layout di un dizionario

Il dizionario e la struttura dati piu importante di Python (usata internamente per namespace, attributi, moduli, ecc.). Il suo layout in memoria e complesso:

```python
import sys

# Dizionario vuoto: pre-alloca spazio per le prime 8 chiavi
d = {}
print(f"dict vuoto: {sys.getsizeof(d)} bytes")  # 64 bytes

# Aggiunta di chiavi: la dimensione cresce a scatti
for i in range(20):
    d[f"key_{i}"] = i
    if i in (0, 4, 5, 10, 15):
        print(f"dict con {i+1} chiavi: {sys.getsizeof(d)} bytes")

# Il dizionario raddoppia la sua tabella hash quando il fattore
# di carico supera 2/3. Le ridimensionamenti avvengono a:
# 8 -> 16 -> 32 -> 64 -> 128 -> ...
```

#### Compact dict (CPython 3.6+)

A partire da CPython 3.6 il dizionario usa un layout *compact* a due livelli che riduce il consumo di memoria del 20-25 % rispetto all'implementazione precedente e preserva l'ordine di inserimento (garantito dal linguaggio da Python 3.7).

**Architettura split index/entries.** Il vecchio layout allocava un array di `PyDictKeyEntry` sparso: ogni slot occupava `~3 puntatori` (hash, key, value), e i bucket vuoti sprecavano lo stesso spazio di quelli pieni. Il layout compact separa la struttura in due parti:

1. **Indice hash** (`dk_indices`): un array denso di interi la cui dimensione dipende dal numero di bucket. Se il dizionario ha fino a 128 bucket l'array usa `int8_t` (1 byte ciascuno); fino a 32768 usa `int16_t`; oltre usa `int32_t` o `int64_t`. Ogni valore e un indice nell'array delle entry, oppure `-1` (DKIX_EMPTY) o `-2` (DKIX_DUMMY, per gestire le cancellazioni).

2. **Array delle entry** (`dk_entries`): un array contiguo di `PyDictKeyEntry` che contiene solo le entry effettivamente inserite, nell'ordine di inserimento. Nessun bucket vuoto intercalato.

**Lookup:** il hash della chiave viene usato per trovare la posizione nell'indice; l'indice punta alla entry effettiva nell'array entries. Le collisioni vengono gestite con open addressing e perturbazione del hash, come nell'implementazione classica.

**Key-sharing dict (`split dict`).** Quando piu istanze della stessa classe hanno esattamente gli stessi attributi (caso comune), CPython puo condividere l'array delle chiavi (`dk_keys`) tra tutte le istanze, allocando solo un array di valori per istanza. Questo meccanismo, chiamato *key-sharing dict*, riduce drasticamente il consumo di memoria per oggetti ripetitivi:

```python
import sys

class Punto:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

# Tutte le istanze condividono le stesse chiavi ('x', 'y', 'z')
# CPython alloca dk_keys una sola volta
punti = [Punto(i, i+1, i+2) for i in range(10_000)]

# Il key-sharing si rompe se un'istanza aggiunge attributi extra:
punti[0].extra = "ops"  # Ora punti[0] ha un dict autonomo
# Le altre 9999 istanze continuano a condividere le chiavi
```

> **Nota pratica:** il key-sharing funziona solo se tutti gli attributi vengono assegnati in `__init__` nello stesso ordine. Aggiungere attributi dinamicamente o in ordine diverso forza CPython a creare un dict autonomo per quell'istanza, vanificando l'ottimizzazione.

### Layout di una classe con e senza __slots__

```python
import sys

class PuntoNormale:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class PuntoSlots:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

p_norm = PuntoNormale(1.0, 2.0, 3.0)
p_slot = PuntoSlots(1.0, 2.0, 3.0)

# Dimensione dell'istanza stessa
print(f"PuntoNormale: {sys.getsizeof(p_norm)} bytes")  # ~48 bytes
print(f"PuntoSlots:   {sys.getsizeof(p_slot)} bytes")  # ~64 bytes (apparente)

# Ma PuntoNormale ha anche un __dict__
print(f"PuntoNormale.__dict__: {sys.getsizeof(p_norm.__dict__)} bytes")  # ~104 bytes
# Totale reale PuntoNormale: ~152 bytes
# Totale reale PuntoSlots: ~64 bytes (niente __dict__)

# Con 1 milione di istanze:
# PuntoNormale: ~152 MB
# PuntoSlots:   ~64 MB — risparmio del 58%
```

---

## Reference counting

Il reference counting e il meccanismo *primario* di gestione della memoria in CPython. Ogni oggetto mantiene un contatore (`ob_refcnt`) che traccia quanti riferimenti puntano a quell'oggetto. Quando il contatore raggiunge zero, l'oggetto viene deallocato immediatamente.

### Come funziona

```python
import sys

# sys.getrefcount() restituisce il reference count
# (il valore include il riferimento temporaneo passato alla funzione stessa)
a = []
print(sys.getrefcount(a))  # 2: 'a' + argomento di getrefcount()

b = a  # Crea un secondo riferimento
print(sys.getrefcount(a))  # 3: 'a' + 'b' + argomento

c = [a, a, a]  # Tre riferimenti aggiuntivi nella lista
print(sys.getrefcount(a))  # 6: 'a' + 'b' + 3 in 'c' + argomento

del b  # Rimuove un riferimento
print(sys.getrefcount(a))  # 5

c.pop()  # Rimuove un elemento dalla lista
print(sys.getrefcount(a))  # 4
```

### Operazioni che incrementano il reference count

```python
import sys

class Esempio:
    pass

obj = Esempio()
print(f"Dopo creazione:            {sys.getrefcount(obj)}")  # 2

# 1. Assegnamento a una variabile
ref = obj
print(f"Dopo assegnamento:         {sys.getrefcount(obj)}")  # 3

# 2. Inserimento in un container
lista = [obj]
print(f"Dopo inserimento in list:  {sys.getrefcount(obj)}")  # 4

# 3. Passaggio come argomento a funzione
def conta_ref(x):
    print(f"Dentro la funzione:        {sys.getrefcount(x)}")  # 6

conta_ref(obj)  # +1 per argomento, +1 per parametro locale

# 4. Creazione di un attributo
class Container:
    pass

c = Container()
c.dato = obj
print(f"Dopo assegnamento attr:    {sys.getrefcount(obj)}")  # 5

# Pulizia
del ref, lista, c
print(f"Dopo pulizia:              {sys.getrefcount(obj)}")  # 2
```

### Operazioni che decrementano il reference count

```python
import sys

obj = object()
refs = []

# Accumula riferimenti
for _ in range(5):
    refs.append(obj)
print(f"Con 5 ref in lista: {sys.getrefcount(obj)}")  # 8

# Decremento tramite:
# 1. del statement
# 2. Riassegnamento della variabile
# 3. Uscita da uno scope (funzione che termina)
# 4. Rimozione da un container
# 5. Distruzione del container

refs.pop()
print(f"Dopo pop():         {sys.getrefcount(obj)}")  # 7

refs.clear()
print(f"Dopo clear():       {sys.getrefcount(obj)}")  # 3

del refs
print(f"Dopo del refs:      {sys.getrefcount(obj)}")  # 2
```

### Limitazione: i reference cycle

Il reference counting da solo non puo gestire i cicli di riferimento:

```python
import gc

# Ciclo semplice: A -> B -> A
a = {}
b = {}
a['ref'] = b
b['ref'] = a

# Ora a e b si riferiscono a vicenda
# Se cancelliamo i nomi, il refcount non arriva mai a zero:
# a ha refcount 1 (da b['ref']), b ha refcount 1 (da a['ref'])
del a, b
# Senza il garbage collector generazionale, questa memoria
# sarebbe perduta per sempre (memory leak)

# Verifica che il GC li raccoglie
gc.collect()  # Raccoglie i cicli orfani

# Ciclo piu subdolo: oggetto che riferisce se stesso
class Nodo:
    def __init__(self):
        self.figli = []

n = Nodo()
n.figli.append(n)  # Ciclo: n -> n.figli -> n
del n  # refcount di n non arriva a zero (n.figli lo mantiene vivo)
gc.collect()  # Servira il GC per raccoglierlo
```

### ctypes per ispezionare il refcount reale

```python
import ctypes
import sys

# sys.getrefcount() aggiunge 1 al conteggio reale
# Per vedere il valore raw, si puo usare ctypes
obj = "test_refcount"
obj_id = id(obj)

# Il refcount e il primo campo di PyObject
# Su CPython 64-bit, e un Py_ssize_t (8 bytes) all'offset 0
refcount_reale = ctypes.c_ssize_t.from_address(obj_id).value
refcount_sys = sys.getrefcount(obj)

print(f"ctypes refcount: {refcount_reale}")
print(f"sys.getrefcount: {refcount_sys}")
print(f"Differenza:      {refcount_sys - refcount_reale}")  # Sempre 1
```

---

## Garbage collector generazionale

Il garbage collector (GC) generazionale di CPython esiste per un solo motivo: raccogliere gli oggetti coinvolti in reference cycle che il reference counting non riesce a deallocare. Non e un sostituto del reference counting — e un complemento.

### Ipotesi generazionale

Il GC si basa sull'*ipotesi generazionale*: la maggior parte degli oggetti ha vita breve. Quelli che sopravvivono a una collezione probabilmente vivranno a lungo. Di conseguenza, conviene ispezionare frequentemente gli oggetti giovani e raramente quelli vecchi.

CPython usa tre generazioni:

```
Generazione 0 (giovani)
│  Oggetti appena creati
│  Raccolta: frequente (ogni ~700 allocazioni nette)
│
Generazione 1 (intermedi)
│  Sopravvissuti a gen-0
│  Raccolta: meno frequente (ogni ~10 raccolte gen-0)
│
Generazione 2 (vecchi)
   Sopravvissuti a gen-1
   Raccolta: rara (ogni ~10 raccolte gen-1)
```

### Algoritmo di raccolta

Il GC usa un algoritmo di **mark-and-sweep** adattato:

1. **Trova i candidati:** tutti gli oggetti container nella generazione in esame (dict, list, tuple, set, istanze di classi, ecc.). Gli oggetti non-container (int, float, str) non possono contenere riferimenti e quindi non possono formare cicli — vengono ignorati.

2. **Copia i refcount:** per ogni oggetto candidato, copia il refcount in un campo temporaneo (`gc_refs`).

3. **Decrementa i riferimenti interni:** per ogni riferimento da un candidato a un altro candidato, decrementa `gc_refs` del referenziato. Dopo questo passo, gli oggetti con `gc_refs == 0` non hanno riferimenti esterni alla generazione — sono potenzialmente raccoglibili.

4. **Trova gli oggetti raggiungibili:** partendo dagli oggetti con `gc_refs > 0` (raggiungibili dall'esterno), marca come raggiungibili tutti gli oggetti che possono essere raggiunti seguendo i riferimenti.

5. **Raccogli:** gli oggetti non raggiungibili vengono deallocati. Quelli raggiungibili vengono promossi alla generazione successiva.

```python
import gc

# Visualizza il comportamento del GC
gc.set_debug(gc.DEBUG_STATS)  # Stampa statistiche ad ogni raccolta

# Crea oggetti per forzare una raccolta
for i in range(1000):
    d = {}
    d['self'] = d  # Ciclo
    del d

# Le statistiche mostreranno quanti oggetti sono stati raccolti
gc.set_debug(0)  # Disabilita il debug
```

### Quando viene attivato il GC

Il GC non viene eseguito a intervalli di tempo, ma in base al conteggio delle allocazioni:

```python
import gc

# threshold = (soglia_gen0, soglia_gen1, soglia_gen2)
soglie = gc.get_threshold()
print(f"Threshold: {soglie}")  # Default: (700, 10, 10)

# Significato:
# - Gen-0 viene raccolta quando: allocazioni - deallocazioni >= 700
# - Gen-1 viene raccolta quando: gen-0 e stata raccolta 10 volte
# - Gen-2 viene raccolta quando: gen-1 e stata raccolta 10 volte

# Contatori attuali
contatori = gc.get_count()
print(f"Contatori: {contatori}")
# (allocazioni_nette_gen0, raccolte_gen0_dall_ultima_gen1, raccolte_gen1_dall_ultima_gen2)
```

### Oggetti con finalizer (`__del__`)

Gli oggetti con un metodo `__del__` (finalizer) creano complicazioni per il GC:

```python
import gc

class Risorsa:
    def __init__(self, nome):
        self.nome = nome
        self.partner = None

    def __del__(self):
        print(f"Finalizzazione di {self.nome}")

# Crea un ciclo tra due oggetti con __del__
r1 = Risorsa("R1")
r2 = Risorsa("R2")
r1.partner = r2
r2.partner = r1

del r1, r2

# In CPython 3.4+, il GC PUO raccogliere cicli con __del__
# (prima di 3.4, venivano messi in gc.garbage e mai deallocati)
# Ma l'ordine di chiamata dei __del__ non e garantito
raccolti = gc.collect()
print(f"Oggetti raccolti: {raccolti}")
```

**Regola pratica:** evitare `__del__` quando possibile. Usare context manager (`__enter__`/`__exit__`) o `weakref.finalize()` come alternative piu sicure.

---

## Il modulo gc

Il modulo `gc` fornisce il controllo programmatico sul garbage collector generazionale. E lo strumento fondamentale per il tuning del GC in applicazioni long-running.

### API principali

```python
import gc

# ── Stato del GC ──────────────────────────────────────────
print(f"GC abilitato:    {gc.isenabled()}")     # True di default
print(f"Threshold:       {gc.get_threshold()}")  # (700, 10, 10)
print(f"Contatori:       {gc.get_count()}")      # (n, n, n)

# ── Statistiche (CPython 3.4+) ────────────────────────────
stats = gc.get_stats()
for i, gen in enumerate(stats):
    print(f"Gen {i}: collections={gen['collections']}, "
          f"collected={gen['collected']}, "
          f"uncollectable={gen['uncollectable']}")

# ── Raccolta manuale ──────────────────────────────────────
gc.collect()            # Raccolta completa (tutte le generazioni)
gc.collect(0)           # Solo generazione 0
gc.collect(1)           # Generazione 0 e 1
gc.collect(2)           # Tutte le generazioni (equivalente a gc.collect())

# ── Oggetti tracciati ─────────────────────────────────────
tutti_gli_oggetti = gc.get_objects()
print(f"Oggetti tracciati dal GC: {len(tutti_gli_oggetti)}")

# ── Referrer e referenti ──────────────────────────────────
target = [1, 2, 3]
referrer = gc.get_referrers(target)    # Chi riferisce target?
referenti = gc.get_referents(target)   # Cosa riferisce target?
```

### Tuning dei threshold

Il tuning dei threshold e la leva principale per ottimizzare il comportamento del GC:

```python
import gc
import time

# ── Scenario 1: applicazione real-time (bassa latenza) ────
# Raccogli piu spesso per evitare pause lunghe
gc.set_threshold(100, 5, 5)
# Effetto: raccolte piu frequenti, ma piu brevi
# Pause GC: <1ms tipicamente

# ── Scenario 2: batch processing (massimo throughput) ─────
# Raccogli meno spesso per ridurre l'overhead del GC
gc.set_threshold(50000, 50, 50)
# Effetto: poche raccolte, ma potenzialmente piu lunghe
# Attenzione: il consumo di memoria puo crescere

# ── Scenario 3: disabilitare il GC (con cautela!) ─────────
# Utile per batch job senza reference cycle
gc.disable()
try:
    # ... elaborazione batch ...
    pass
finally:
    gc.enable()
    gc.collect()  # Raccolta manuale alla fine

# ── Benchmark: impatto del GC ─────────────────────────────
def benchmark_gc(threshold, iterazioni=100_000):
    gc.set_threshold(*threshold)
    gc.collect()

    start = time.perf_counter()
    for _ in range(iterazioni):
        d = {"a": 1, "b": [2, 3]}
    elapsed = time.perf_counter() - start

    stats = gc.get_stats()
    raccolte = sum(s['collections'] for s in stats)
    return elapsed, raccolte

print("Threshold         | Tempo (s) | Raccolte GC")
print("-" * 50)
for thresh in [(700, 10, 10), (100, 5, 5), (50000, 50, 50)]:
    gc.set_threshold(700, 10, 10)
    gc.collect()
    t, r = benchmark_gc(thresh)
    print(f"{str(thresh):<18}| {t:.4f}    | {r}")

# Ripristina i default
gc.set_threshold(700, 10, 10)
```

### gc.freeze() e gc.unfreeze() (CPython 3.7+)

```python
import gc

# gc.freeze() sposta tutti gli oggetti attuali fuori dal tracking del GC
# Utile dopo il fork: il processo figlio non deve ri-scansionare
# gli oggetti del processo padre

# Esempio: server pre-fork (come gunicorn)
# Nel processo principale, dopo il caricamento iniziale:
gc.collect()    # Pulisci tutto prima del freeze
gc.freeze()     # Gli oggetti attuali non saranno piu ispezionati dal GC

# os.fork() qui — il figlio eredita gli oggetti congelati
# Il GC del figlio ispezionera solo i *nuovi* oggetti

# Per ripristinare:
gc.unfreeze()   # Rimette gli oggetti congelati nel tracking

# Conteggio oggetti congelati
print(f"Oggetti congelati: {gc.get_freeze_count()}")
```

### Callback del GC

```python
import gc

def gc_callback(phase, info):
    """Callback invocato prima e dopo ogni raccolta."""
    if phase == "start":
        print(f"GC start: generazione {info['generation']}, "
              f"oggetti tracciati: {info.get('collected', '?')}")
    elif phase == "stop":
        print(f"GC stop: raccolti {info['collected']}, "
              f"non raccoglibili {info['uncollectable']}")

gc.callbacks.append(gc_callback)

# Forza una raccolta per vedere il callback in azione
gc.collect()

# Rimuovi il callback
gc.callbacks.remove(gc_callback)
```

### Debugging avanzato con gc.get_referrers e gc.get_referents

Quando si indaga un memory leak, `gc.get_referrers()` e `gc.get_referents()` permettono di navigare il grafo dei riferimenti in entrambe le direzioni: chi tiene in vita un oggetto e cosa un oggetto tiene in vita.

```python
import gc

class Cache:
    def __init__(self):
        self.dati = {}

class Elemento:
    def __init__(self, valore):
        self.valore = valore

cache = Cache()
elem = Elemento("importante")
cache.dati["k1"] = elem

# ── get_referrers: chi punta a elem? ────────────────────────
referrers = gc.get_referrers(elem)
# Filtra il rumore: frame dello stack corrente, moduli, ecc.
referrers_utili = [
    r for r in referrers
    if not isinstance(r, (type, dict))  # filtra i __dict__ di modulo/frame
    or (isinstance(r, dict) and any(v is elem for v in r.values()))
]
print(f"Referrers di elem: {len(referrers)} totali, "
      f"{len(referrers_utili)} utili")

# ── get_referents: cosa tiene in vita elem? ──────────────────
referents = gc.get_referents(elem)
print(f"Referents di elem: {referents}")
# Output: [{'valore': 'importante'}]  — il __dict__ dell'istanza

# ── Chain walking: risalire la catena di ownership ───────────
def trova_catena_ownership(target, max_depth=5):
    """Risale la catena dei referrers fino alla radice."""
    visitati = set()
    catena = []
    corrente = target

    for _ in range(max_depth):
        referrers = [
            r for r in gc.get_referrers(corrente)
            if id(r) not in visitati and not isinstance(r, type)
        ]
        if not referrers:
            break
        prossimo = referrers[0]
        catena.append((type(prossimo).__name__, id(prossimo)))
        visitati.add(id(prossimo))
        corrente = prossimo

    return catena

catena = trova_catena_ownership(elem)
print("Catena di ownership:")
for tipo, oid in catena:
    print(f"  <- {tipo} (id={oid})")
```

> **Attenzione:** `gc.get_referrers()` restituisce anche il frame corrente dell'interprete e i namespace dei moduli. Filtrare sempre il risultato per evitare falsi positivi. In produzione, preferire `objgraph.show_backrefs()` che gestisce automaticamente il filtraggio e produce grafi visuali.

---

## CPU profiling

Il CPU profiling identifica *dove* il programma spende tempo di CPU. Come visto nel Modulo 25, cProfile e il punto di partenza. Qui approfondiamo gli strumenti avanzati e i workflow specifici per l'analisi dettagliata.

### Profiling deterministico vs statistico

| Caratteristica | Deterministico | Statistico |
|---------------|---------------|-----------|
| Strumenti | cProfile, profile | py-spy, scalene, pyinstrument |
| Meccanismo | Traccia ogni chiamata a funzione | Campiona lo stack a intervalli |
| Overhead | 10-30% | 1-5% |
| Granularita | Per funzione | Per funzione o per riga |
| Produzione | Sconsigliato | Adatto |
| Modifica codice | A volte necessaria | Mai |

### cProfile: analisi approfondita

```python
import cProfile
import pstats
import io
from pstats import SortKey

def elabora_dati(n):
    """Funzione con diversi hotspot intenzionali."""
    risultato = calcola_valori(n)
    aggregato = aggrega(risultato)
    return formatta(aggregato)

def calcola_valori(n):
    return [x ** 2 + x * 3 for x in range(n)]

def aggrega(valori):
    from collections import Counter
    buckets = Counter()
    for v in valori:
        buckets[v % 100] += 1
    return dict(buckets.most_common(20))

def formatta(dati):
    return "\n".join(f"{k}: {v}" for k, v in dati.items())

# ── Profiling con output in-memory ────────────────────────
profiler = cProfile.Profile()
profiler.enable()
risultato = elabora_dati(500_000)
profiler.disable()

# Analisi con pstats
stream = io.StringIO()
stats = pstats.Stats(profiler, stream=stream)
stats.strip_dirs()  # Rimuovi i path completi

# Ordinamenti utili
stats.sort_stats(SortKey.CUMULATIVE)
stats.print_stats(15)
print(stream.getvalue())

# ── Significato delle colonne ─────────────────────────────
# ncalls    — numero di chiamate
# tottime   — tempo totale nella funzione (esclude le sotto-funzioni)
# percall   — tottime / ncalls
# cumtime   — tempo cumulativo (include le sotto-funzioni)
# percall   — cumtime / ncalls
# filename:lineno(function) — dove si trova la funzione
```

### pstats: analisi programmatica

```python
import cProfile
import pstats

# Salva il profiling su file per analisi successiva
cProfile.run('elabora_dati(500_000)', 'output.prof')

# Carica e analizza
stats = pstats.Stats('output.prof')
stats.strip_dirs()

# Filtra per pattern
stats.sort_stats('cumulative')
stats.print_stats('elabora')  # Solo funzioni che contengono "elabora"

# Callers e callees
stats.print_callers('aggrega')   # Chi chiama aggrega()?
stats.print_callees('elabora_dati')  # Cosa chiama elabora_dati()?

# Combina piu profiling
stats2 = pstats.Stats('altro_profiling.prof')
stats.add(stats2)  # Somma i dati
stats.print_stats(10)
```

### Visualizzazione con snakeviz

```bash
# Installazione
pip install snakeviz

# Genera il file .prof
python -m cProfile -o output.prof mio_script.py

# Lancia il visualizzatore interattivo nel browser
snakeviz output.prof
# Apre http://localhost:8080/snakeviz/<path>
# Mostra un grafico icicle/sunburst navigabile
```

```python
# Generazione programmatica del file .prof per snakeviz
import cProfile

with cProfile.Profile() as profiler:
    risultato = funzione_costosa()

profiler.dump_stats("analisi.prof")
# Poi: snakeviz analisi.prof
```

### Visualizzazione con KCacheGrind (via pyprof2calltree)

```bash
# Installazione
pip install pyprof2calltree
# Su Debian/Ubuntu: apt install kcachegrind

# Genera il profiling
python -m cProfile -o output.prof mio_script.py

# Converti nel formato callgrind
pyprof2calltree -i output.prof -o callgrind.out

# Visualizza con KCacheGrind
kcachegrind callgrind.out
```

### line_profiler: profiling riga per riga

```bash
pip install line_profiler
```

```python
# Decorare le funzioni da profilare con @profile
# line_profiler inietta il decoratore @profile automaticamente

# mio_modulo.py
@profile
def funzione_critica(dati):
    risultato = []                        # Line 4
    for elemento in dati:                 # Line 5
        if elemento > 0:                  # Line 6
            valore = elemento ** 2        # Line 7
            risultato.append(valore)      # Line 8
    return sum(risultato)                 # Line 9

funzione_critica(list(range(-5000, 5000)))
```

```bash
# Esecuzione
kernprof -l -v mio_modulo.py

# Output tipico:
# Line #  Hits    Time  Per Hit  % Time  Line Contents
# =====================================================
#      4     1     0.5    0.5      0.0    risultato = []
#      5 10001  1523.0    0.2     12.1    for elemento in dati:
#      6 10000  1245.0    0.1      9.9    if elemento > 0:
#      7  5000  6543.0    1.3     52.0    valore = elemento ** 2
#      8  5000  3267.0    0.7     26.0    risultato.append(valore)
#      9     1     0.3    0.3      0.0    return sum(risultato)
```

### py-spy: profiling senza modifiche al codice

py-spy e un sample profiler scritto in Rust che si aggancia a un processo Python in esecuzione senza modificarlo. Ideale per la produzione.

```bash
# Installazione
pip install py-spy

# ── Flame graph SVG ───────────────────────────────────────
py-spy record -o flamegraph.svg --pid 12345
py-spy record -o flamegraph.svg -- python mio_script.py

# ── Top: vista live simile a htop ─────────────────────────
py-spy top --pid 12345

# ── Dump: stack trace istantaneo ──────────────────────────
py-spy dump --pid 12345

# ── Opzioni avanzate ──────────────────────────────────────
# Frequenza di campionamento (default: 100 Hz)
py-spy record --rate 1000 -o hires.svg -- python mio_script.py

# Includi subprocessi
py-spy record --subprocesses -o multi.svg -- python mio_script.py

# Formato speedscope (alternativa a flame graph)
py-spy record -f speedscope -o profile.speedscope -- python mio_script.py
# Visualizza su https://www.speedscope.app/

# Profiling di codice nativo (C extensions)
py-spy record --native -o nativo.svg -- python mio_script.py
```

### Come leggere un flame graph

```
# Un flame graph si legge dal basso verso l'alto:
#
# ┌──────────────────────────────────────────────┐
# │              calcola_hash (35%)              │  <- Hotspot!
# ├────────────────────────┬─────────────────────┤
# │   elabora_batch (60%)  │ scrivi_output (15%) │
# ├────────────────────────┴─────────────────────┤
# │                  main (100%)                 │  <- Entry point
# └──────────────────────────────────────────────┘
#
# Larghezza = percentuale di tempo CPU
# Altezza = profondita dello stack
# Colore = modulo o tipo (varia per strumento)
#
# L'hotspot e la funzione piu larga vicino alla cima:
# indica dove il CPU spende effettivamente il tempo
# (non solo dove transita il controllo di flusso)
```

### scalene: profiler ibrido CPU + memoria + GPU

```bash
pip install scalene

# Profiling completo (CPU + memoria + copia)
scalene mio_script.py

# Solo CPU
scalene --cpu-only mio_script.py

# Output HTML interattivo
scalene --html --outfile report.html mio_script.py

# Profiling di un modulo specifico
scalene --profile-only mio_modulo mio_script.py

# Riduzione overhead
scalene --reduced-profile mio_script.py
```

scalene distingue tra tempo Python, tempo C/nativo e tempo di sistema (I/O), e traccia le allocazioni di memoria per riga. E uno degli strumenti piu informativi per capire dove va il tempo e la memoria contemporaneamente.

### pyinstrument: profiling leggibile

```bash
pip install pyinstrument

# Da riga di comando
pyinstrument mio_script.py

# Output HTML
pyinstrument --html -o report.html mio_script.py
```

```python
# Uso programmatico
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# ... codice da profilare ...

profiler.stop()
print(profiler.output_text(unicode=True, color=True))

# In un web framework (ad esempio FastAPI middleware)
from pyinstrument import Profiler
from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.middleware("http")
async def profiling_middleware(request: Request, call_next):
    if request.query_params.get("profile"):
        profiler = Profiler(async_mode="enabled")
        profiler.start()
        response = await call_next(request)
        profiler.stop()
        return Response(
            content=profiler.output_html(),
            media_type="text/html"
        )
    return await call_next(request)
```

---

## Memory profiling

Il memory profiling identifica *dove* il programma consuma memoria e *come* il consumo evolve nel tempo. E complementare al CPU profiling e fondamentale per applicazioni long-running.

### tracemalloc: il punto di partenza

tracemalloc e integrato nella standard library (CPython 3.4+). Traccia ogni allocazione di memoria con il traceback del punto di allocazione.

```python
import tracemalloc

# ── Avvia il tracciamento ─────────────────────────────────
tracemalloc.start(25)  # 25 frame di traceback (default: 1)

# ── Snapshot e analisi ────────────────────────────────────
def operazione_costosa():
    return {f"chiave_{i}": list(range(100)) for i in range(1000)}

snap1 = tracemalloc.take_snapshot()
dati = operazione_costosa()
snap2 = tracemalloc.take_snapshot()

# Top 10 linee per consumo di memoria
print("=== Top 10 per linea ===")
top_stats = snap2.compare_to(snap1, 'lineno')
for stat in top_stats[:10]:
    print(stat)

# Top 10 per file
print("\n=== Top 10 per file ===")
top_stats = snap2.compare_to(snap1, 'filename')
for stat in top_stats[:10]:
    print(stat)

# Top 10 con traceback completo
print("\n=== Top 10 con traceback ===")
top_stats = snap2.compare_to(snap1, 'traceback')
for stat in top_stats[:3]:
    print(f"\n{stat}")
    for line in stat.traceback.format():
        print(f"  {line}")
```

### tracemalloc: filtri e analisi avanzata

```python
import tracemalloc

tracemalloc.start()

# ... codice che alloca memoria ...

snapshot = tracemalloc.take_snapshot()

# Filtra per escludere i moduli di tracemalloc stesso
filtri = [
    tracemalloc.Filter(False, tracemalloc.__file__),      # Escludi tracemalloc
    tracemalloc.Filter(False, "<frozen importlib.*>"),     # Escludi importlib
    tracemalloc.Filter(True, "mio_progetto/*"),            # Solo il mio codice
]
snapshot_filtrato = snapshot.filter_traces(filtri)

# Statistiche per traceback
stats = snapshot_filtrato.statistics('traceback')
for stat in stats[:5]:
    print(f"\n{stat.count} blocchi, {stat.size / 1024:.1f} KiB")
    for line in stat.traceback.format():
        print(f"  {line}")

# Dimensione totale e picco
corrente, picco = tracemalloc.get_traced_memory()
print(f"\nMemoria corrente: {corrente / 1024 / 1024:.1f} MiB")
print(f"Memoria picco:    {picco / 1024 / 1024:.1f} MiB")

tracemalloc.stop()
```

### tracemalloc: monitoraggio periodico

```python
import tracemalloc
import time
import threading

class MemoryMonitor:
    """Monitora il consumo di memoria periodicamente."""

    def __init__(self, intervallo_secondi=5.0):
        self.intervallo = intervallo_secondi
        self._attivo = False
        self._thread = None
        self._snapshots = []

    def avvia(self):
        tracemalloc.start()
        self._attivo = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def ferma(self):
        self._attivo = False
        if self._thread:
            self._thread.join(timeout=self.intervallo + 1)
        return self._snapshots

    def _loop(self):
        while self._attivo:
            snap = tracemalloc.take_snapshot()
            corrente, picco = tracemalloc.get_traced_memory()
            self._snapshots.append({
                'timestamp': time.time(),
                'snapshot': snap,
                'corrente_mib': corrente / 1024 / 1024,
                'picco_mib': picco / 1024 / 1024,
            })
            time.sleep(self.intervallo)

# Uso
monitor = MemoryMonitor(intervallo_secondi=2.0)
monitor.avvia()

# ... lavoro lungo ...
time.sleep(10)

risultati = monitor.ferma()
for r in risultati:
    print(f"t={r['timestamp']:.0f} corrente={r['corrente_mib']:.1f} MiB "
          f"picco={r['picco_mib']:.1f} MiB")
```

### memory_profiler: profiling riga per riga

```bash
pip install memory_profiler
```

```python
# mio_modulo.py
from memory_profiler import profile

@profile
def elabora():
    lista_grande = [0] * 1_000_000       # ~8 MiB
    dizionario = {i: i**2 for i in range(100_000)}  # ~5 MiB
    del lista_grande                       # Libera ~8 MiB
    risultato = list(dizionario.values())  # ~0.8 MiB
    return risultato

elabora()
```

```bash
# Esecuzione
python -m memory_profiler mio_modulo.py

# Output:
# Line #    Mem usage    Increment  Occurrences   Line Contents
# ============================================================
#      4     45.2 MiB     45.2 MiB      1   def elabora():
#      5     53.2 MiB      8.0 MiB      1       lista_grande = [0] * 1_000_000
#      6     58.4 MiB      5.2 MiB      1       dizionario = {i: i**2 ...}
#      7     50.4 MiB     -8.0 MiB      1       del lista_grande
#      8     51.2 MiB      0.8 MiB      1       risultato = list(dizionario.values())
#      9     51.2 MiB      0.0 MiB      1       return risultato
```

```python
# Monitoraggio continuo con mprof
# mprof run mio_script.py
# mprof plot  # genera grafico temporale
```

### objgraph: visualizzazione del grafo degli oggetti

```bash
pip install objgraph graphviz
```

```python
import objgraph

# ── Tipi di oggetto piu comuni ────────────────────────────
objgraph.show_most_common_types(limit=15)
# Output:
# dict        12345
# list        8765
# tuple       6543
# ...

# ── Crescita degli oggetti ────────────────────────────────
objgraph.show_growth(limit=10)
# ... operazione ...
objgraph.show_growth(limit=10)
# Mostra solo i tipi che sono cresciuti tra le due chiamate

# ── Trovare i leaker ─────────────────────────────────────
# Trova le catene di riferimento che mantengono vivo un oggetto
class MioOggetto:
    pass

obj = MioOggetto()
lista_nascosta = [obj]  # Riferimento che impedisce la deallocazione

# Mostra la catena di back-reference dal modulo al nostro oggetto
objgraph.show_backrefs(
    obj,
    max_depth=5,
    filename='backrefs.png'  # Genera un'immagine PNG
)

# Mostra i riferimenti in avanti
objgraph.show_refs(
    obj,
    max_depth=3,
    filename='refs.png'
)

# Trova tutti gli oggetti di un tipo specifico
tutti = objgraph.by_type('MioOggetto')
print(f"Istanze di MioOggetto: {len(tutti)}")
```

### pympler: analisi della dimensione reale degli oggetti

```bash
pip install pympler
```

```python
from pympler import asizeof, tracker, summary, muppy

# ── asizeof: dimensione profonda (ricorsiva) ──────────────
class Utente:
    def __init__(self, nome, email, cronologia):
        self.nome = nome
        self.email = email
        self.cronologia = cronologia

u = Utente("Mario", "mario@example.com", list(range(1000)))

import sys
print(f"sys.getsizeof (shallow): {sys.getsizeof(u)} bytes")
print(f"asizeof (deep):          {asizeof.asizeof(u)} bytes")
# asizeof include ricorsivamente tutti gli oggetti referenziati

# Dimensioni flat vs referenziata
print(f"asizeof flat:  {asizeof.flatsize(u)} bytes")
print(f"asizeof ref:   {asizeof.asizeof(u)} bytes")

# ── tracker: tracciamento delle differenze ────────────────
tr = tracker.SummaryTracker()

# Prima snapshot (baseline)
tr.print_diff()

# Alloca oggetti
grandi_dati = [list(range(100)) for _ in range(1000)]

# Seconda snapshot: mostra cosa e cambiato
tr.print_diff()
# Output:
#                  types |   # objects |   total size
# ===================== | =========== | ============
#                  list  |        1001 |    980.5 KiB
#                  int   |        1000 |     27.3 KiB

# ── muppy: tutti gli oggetti in memoria ───────────────────
tutti = muppy.get_objects()
somm = summary.summarize(tutti)
summary.print_(somm, limit=15)
```

### Memray: profilazione nativa delle allocazioni

Memray (sviluppato da Bloomberg) e un memory profiler per CPython che traccia *tutte* le allocazioni, incluse quelle native di estensioni C/C++/Rust — un punto cieco di `tracemalloc` e `memory_profiler` che vedono solo le allocazioni passate per l'allocatore Python.

```bash
# Installazione (solo Linux e macOS, non supporta Windows)
pip install memray

# ── Profilazione offline ──────────────────────────────────
# Registra le allocazioni in un file binario
memray run -o output.bin mio_script.py

# Genera un flame graph interattivo HTML
memray flamegraph output.bin -o flamegraph.html

# Report tabellare delle allocazioni piu grandi
memray table output.bin --biggest-allocs 20

# Report statistico (simile a tracemalloc ma con allocazioni native)
memray stats output.bin

# Report ad albero per modulo/funzione
memray tree output.bin

# ── Live attach a un processo in esecuzione ───────────────
# Memray puo agganciarsi a un processo Python gia in esecuzione:
memray attach <PID>
# Apre un TUI (Text UI) con aggiornamenti in tempo reale
# delle allocazioni — utile per diagnosticare leak in produzione

# ── Profilazione live con TUI ─────────────────────────────
memray run --live mio_script.py
# Mostra un flame graph testuale aggiornato in tempo reale
```

**Punti di forza di Memray:**
- Traccia allocazioni C native (NumPy, Pandas, librerie CFFI) invisibili ad altri profiler Python.
- L'overhead e basso (~10-15 %) rispetto a `memory_profiler` (~2-3x rallentamento).
- `memray attach` permette di agganciare un processo in produzione senza riavviarlo.
- Genera flame graph, diagrammi temporali e report statistici direttamente da CLI.

### Fil: profilazione della memoria di picco

Fil (File Imports and Loads profiler, di Itamar Turner-Trauring) si concentra sul **picco di utilizzo della memoria** piuttosto che sulle allocazioni individuali. Questo lo rende ideale per rispondere alla domanda "perche il mio script usa 8 GiB?" quando il problema e un picco transitorio, non un leak.

```bash
# Installazione (Linux e macOS)
pip install filprofiler

# Profilazione — genera automaticamente un flame graph
fil-profile run mio_script.py
# Output: una directory fil-result/ con un flame graph SVG interattivo
# Il flame graph mostra lo stack trace al momento del picco di memoria

# Confronto tra due run
fil-profile run --output run_v1 script_vecchio.py
fil-profile run --output run_v2 script_nuovo.py
# Confronto manuale dei flame graph per vedere se il picco e cambiato
```

**Differenze chiave rispetto a Memray e tracemalloc:**

| Caratteristica | tracemalloc | Memray | Fil |
|---------------|-------------|--------|-----|
| Allocazioni native C | No | Si | Si |
| Focus | Tutte le alloc | Tutte le alloc | Solo picco |
| Overhead | Basso (~5%) | Medio (~15%) | Alto (~2x) |
| Attach a processo | No | Si | No |
| Output principale | Snapshot + diff | Flame graph + TUI | Flame graph picco |
| Uso ideale | Sviluppo, CI | Produzione, debug | Data science, batch |

> **Consiglio pratico:** usare `tracemalloc` durante lo sviluppo per snapshot rapidi, `memray` in produzione per diagnosi con attach live, e `fil-profile` per script batch o pipeline di data science dove il collo di bottiglia e il picco di memoria.

---

## Weak references

Le weak reference (riferimenti deboli) permettono di riferire un oggetto *senza* incrementare il suo reference count. L'oggetto puo essere deallocato anche se esistono weak reference che puntano a esso. Sono lo strumento chiave per implementare cache, observer pattern e strutture dati che non devono impedire la garbage collection.

### Basi del modulo weakref

```python
import weakref

class Risorsa:
    def __init__(self, nome):
        self.nome = nome

    def __repr__(self):
        return f"Risorsa({self.nome!r})"

# Crea una weak reference
r = Risorsa("database_conn")
ref = weakref.ref(r)

# Accesso tramite la weak reference (chiamata come funzione)
print(ref())     # Risorsa('database_conn')
print(ref() is r)  # True

# Dopo la deallocazione, la weak reference restituisce None
del r
print(ref())     # None

# ── Callback alla deallocazione ───────────────────────────
def notifica_deallocazione(ref):
    print(f"Oggetto deallocato! ref={ref}")

r2 = Risorsa("cache_entry")
ref2 = weakref.ref(r2, notifica_deallocazione)
del r2  # Stampa: "Oggetto deallocato! ref=<weakref ...>"
```

### weakref.finalize: alternativa sicura a __del__

```python
import weakref
import tempfile
import os

class FileTemporaneo:
    """Classe che crea un file temporaneo e lo pulisce alla deallocazione."""

    def __init__(self, contenuto):
        self.path = tempfile.mktemp()
        with open(self.path, 'w') as f:
            f.write(contenuto)

        # Registra il finalizer — piu sicuro di __del__
        # Funziona anche in presence di reference cycle
        self._finalizer = weakref.finalize(
            self, self._cleanup, self.path
        )

    @staticmethod
    def _cleanup(path):
        if os.path.exists(path):
            os.unlink(path)
            print(f"File {path} rimosso")

    def rimuovi(self):
        """Rimozione esplicita (preferibile)."""
        self._finalizer()

# Uso
ft = FileTemporaneo("dati temporanei")
del ft  # Il finalizer viene chiamato automaticamente
```

### WeakValueDictionary e WeakKeyDictionary

```python
import weakref

# ── WeakValueDictionary: cache che non impedisce il GC ────
class Entita:
    def __init__(self, id_, nome):
        self.id_ = id_
        self.nome = nome

    def __repr__(self):
        return f"Entita({self.id_}, {self.nome!r})"

# Cache con weak values: gli oggetti possono essere raccolti dal GC
cache = weakref.WeakValueDictionary()

e1 = Entita(1, "Alice")
e2 = Entita(2, "Bob")
cache[1] = e1
cache[2] = e2

print(f"Cache: {dict(cache)}")    # {1: Entita(1, 'Alice'), 2: Entita(2, 'Bob')}
print(f"Dimensione: {len(cache)}")  # 2

# Se l'oggetto non e piu referenziato altrove, scompare dalla cache
del e1
import gc; gc.collect()

print(f"Cache dopo del e1: {dict(cache)}")  # {2: Entita(2, 'Bob')}
print(f"Dimensione: {len(cache)}")          # 1

# ── WeakKeyDictionary: metadati associati a oggetti ───────
# Utile per associare dati extra a oggetti senza modificarli
metadati = weakref.WeakKeyDictionary()

obj = Entita(3, "Charlie")
metadati[obj] = {"creato": "2026-01-15", "accessi": 42}

print(metadati[obj])  # {'creato': '2026-01-15', 'accessi': 42}

del obj
gc.collect()
print(f"Metadati rimasti: {len(metadati)}")  # 0 — chiave sparita
```

### WeakSet

```python
import weakref

class Sessione:
    _sessioni_attive = weakref.WeakSet()

    def __init__(self, utente):
        self.utente = utente
        Sessione._sessioni_attive.add(self)

    @classmethod
    def conteggio_attive(cls):
        return len(cls._sessioni_attive)

s1 = Sessione("Alice")
s2 = Sessione("Bob")
print(f"Sessioni attive: {Sessione.conteggio_attive()}")  # 2

del s1
import gc; gc.collect()
print(f"Sessioni attive: {Sessione.conteggio_attive()}")  # 1
# La sessione di Alice e stata raccolta automaticamente
```

### Pattern avanzati: invalidazione cache con weakref callback

Le weak reference accettano un argomento `callback` che viene invocato quando l'oggetto referenziato viene deallocato. Questo meccanismo permette di implementare cache auto-invalidanti senza polling e senza timer.

```python
import weakref
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cache")

class CacheInvalidante:
    """Cache che si ripulisce automaticamente quando gli oggetti muoiono."""

    def __init__(self, nome="default"):
        self.nome = nome
        self._store = {}        # chiave -> weakref con callback
        self._metriche = {"hit": 0, "miss": 0, "evict": 0}

    def _on_evict(self, chiave):
        """Crea il callback di invalidazione per una chiave specifica."""
        def _callback(ref):
            self._store.pop(chiave, None)
            self._metriche["evict"] += 1
            log.info(f"[{self.nome}] evict chiave={chiave}, "
                     f"totale_evict={self._metriche['evict']}")
        return _callback

    def inserisci(self, chiave, oggetto):
        self._store[chiave] = weakref.ref(oggetto, self._on_evict(chiave))

    def ottieni(self, chiave):
        ref = self._store.get(chiave)
        if ref is None:
            self._metriche["miss"] += 1
            return None
        valore = ref()
        if valore is None:
            # Il callback potrebbe non essere ancora stato chiamato
            self._store.pop(chiave, None)
            self._metriche["miss"] += 1
            return None
        self._metriche["hit"] += 1
        return valore

    @property
    def stats(self):
        return dict(self._metriche, dimensione=len(self._store))


# Uso
class Modello:
    def __init__(self, mid, dati):
        self.mid = mid
        self.dati = dati

cache = CacheInvalidante("modelli")
m1 = Modello(1, [0]*1000)
m2 = Modello(2, [0]*2000)

cache.inserisci(1, m1)
cache.inserisci(2, m2)
print(cache.stats)  # dimensione=2, hit=0, miss=0, evict=0

del m1           # il callback rimuove la chiave 1 dalla cache
gc.collect()
print(cache.stats)  # dimensione=1, evict=1
```

Il pattern e particolarmente utile per cache di modelli ML, connessioni a risorse esterne o qualsiasi oggetto pesante la cui durata e governata dal chiamante. Il callback garantisce che la cache non contenga mai riferimenti stantii, eliminando la necessita di un thread di pulizia periodica.

### Limitazioni delle weak reference

```python
import weakref

# NON tutti gli oggetti supportano weak reference:
# - int, str, tuple, NoneType: NO
# - list, dict, set: NO (di default)
# - Istanze di classi utente: SI
# - Istanze di classi con __slots__: SI (se includono __weakref__)

class ConSlots:
    __slots__ = ('x', '__weakref__')  # Deve includere __weakref__

class SenzaWeakref:
    __slots__ = ('x',)  # Niente __weakref__ -> no weak ref

c = ConSlots()
ref = weakref.ref(c)  # OK

s = SenzaWeakref()
try:
    ref = weakref.ref(s)  # TypeError!
except TypeError as e:
    print(f"Errore: {e}")
```

---

## __slots__

`__slots__` e un meccanismo che sostituisce il dizionario `__dict__` delle istanze con un layout fisso in memoria. Il risparmio e significativo quando si creano milioni di istanze.

### Funzionamento base

```python
import sys

class PuntoDict:
    """Classe standard con __dict__."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PuntoSlots:
    """Classe con __slots__ — niente __dict__."""
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

pd = PuntoDict(1.0, 2.0)
ps = PuntoSlots(1.0, 2.0)

# Confronto dimensioni
dim_pd = sys.getsizeof(pd) + sys.getsizeof(pd.__dict__)
dim_ps = sys.getsizeof(ps)
print(f"PuntoDict (istanza + __dict__): {dim_pd} bytes")
print(f"PuntoSlots:                     {dim_ps} bytes")
print(f"Risparmio per istanza:          {dim_pd - dim_ps} bytes "
      f"({(1 - dim_ps/dim_pd)*100:.0f}%)")

# Con 10 milioni di istanze
n = 10_000_000
print(f"\n{n:,} istanze:")
print(f"  PuntoDict: ~{n * dim_pd / 1024 / 1024:.0f} MiB")
print(f"  PuntoSlots: ~{n * dim_ps / 1024 / 1024:.0f} MiB")
```

### Accesso leggermente piu veloce

```python
import timeit

class NodoDict:
    def __init__(self, valore):
        self.valore = valore

class NodoSlots:
    __slots__ = ('valore',)
    def __init__(self, valore):
        self.valore = valore

nd = NodoDict(42)
ns = NodoSlots(42)

# Benchmark accesso attributo
t_dict = timeit.timeit('nd.valore', globals={'nd': nd}, number=10_000_000)
t_slots = timeit.timeit('ns.valore', globals={'ns': ns}, number=10_000_000)

print(f"__dict__: {t_dict:.3f}s")
print(f"__slots__: {t_slots:.3f}s")
print(f"Speedup: {t_dict/t_slots:.2f}x")
# Tipicamente 10-30% piu veloce
```

### Limitazioni di __slots__

```python
# 1. Nessun attributo dinamico
class Rigido:
    __slots__ = ('x', 'y')

r = Rigido()
r.x = 1
try:
    r.z = 3  # AttributeError!
except AttributeError as e:
    print(f"1. {e}")

# 2. Ereditarieta: la sottoclasse DEVE dichiarare i suoi __slots__
class Base:
    __slots__ = ('a',)

class Derivata(Base):
    __slots__ = ('b',)  # Solo i nuovi attributi!
    # Se non dichiara __slots__, avra un __dict__ (vanificando il risparmio)

class DerivataConDict(Base):
    pass  # Ha __dict__ -> nessun risparmio di memoria

d1 = Derivata()
d1.a = 1
d1.b = 2

d2 = DerivataConDict()
d2.a = 1
d2.qualsiasi = "funziona"  # Ha __dict__
print(f"2. Derivata ha __dict__: {hasattr(d1, '__dict__')}")     # False
print(f"   DerivataConDict ha __dict__: {hasattr(d2, '__dict__')}")  # True

# 3. Multipla ereditarieta: entrambe le basi NON possono avere __slots__ non vuoti
class A:
    __slots__ = ('x',)

class B:
    __slots__ = ('y',)

try:
    class C(A, B):
        __slots__ = ()
    c = C()
    c.x = 1
    c.y = 2  # Funziona in molti casi
except TypeError as e:
    print(f"3. {e}")

# 4. Nessun default value nei __slots__ (usare __init__ o class var)
class ConDefault:
    __slots__ = ('valore',)
    # valore = 42  # Questo creerebbe un attributo di classe, NON un default

# 5. Pickle: richiede __getstate__/__setstate__ o protocol >= 2
import pickle

class Serializzabile:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

s = Serializzabile(1, 2)
dati = pickle.dumps(s, protocol=2)
s2 = pickle.loads(dati)
print(f"5. Pickle: x={s2.x}, y={s2.y}")
```

### Quando usare __slots__

```python
# USI IDEALI:
# - Classi con milioni di istanze (nodi di grafi, record, punti)
# - Data transfer objects semplici
# - Classi value-object immutabili
# - Inner loop dove l'accesso agli attributi e critico

# EVITARE QUANDO:
# - La classe ha pochi istanze
# - Serve aggiungere attributi dinamicamente (plugin, monkey patching)
# - La classe e una base per ereditarieta complessa
# - La classe usa metaclassi incompatibili

# ALTERNATIVA MODERNA: dataclass con slots=True (Python 3.10+)
from dataclasses import dataclass

@dataclass(slots=True)
class Punto3D:
    x: float
    y: float
    z: float

p = Punto3D(1.0, 2.0, 3.0)
print(f"Punto3D.__slots__: {Punto3D.__slots__}")
print(f"Ha __dict__: {hasattr(p, '__dict__')}")  # False
```

---

## String interning e integer caching

CPython ottimizza l'uso di memoria e le comparazioni per stringhe e interi comuni attraverso meccanismi di caching automatico.

### Integer caching

```python
# CPython pre-alloca gli interi da -5 a 256 al momento dell'avvio
# Tutti i riferimenti a questi valori puntano allo stesso oggetto

a = 256
b = 256
print(f"a is b (256): {a is b}")  # True — stesso oggetto

a = 257
b = 257
print(f"a is b (257): {a is b}")  # False — oggetti diversi
# (potrebbe essere True nel REPL a causa di ottimizzazioni del compilatore)

a = -5
b = -5
print(f"a is b (-5):  {a is b}")  # True — pre-allocato

a = -6
b = -6
print(f"a is b (-6):  {a is b}")  # False — fuori range

# Implicazione: in un loop che usa interi piccoli, non vengono
# creati nuovi oggetti int — il risparmio di memoria e automatico
import sys

# Verifica: tutti gli interi 0-256 hanno lo stesso id
ids_piccoli = set()
for i in range(257):
    ids_piccoli.add(id(i))
print(f"ID univoci per 0-256: {len(ids_piccoli)}")  # 257

# Per confrontare valori, usare SEMPRE == e MAI is
# 'is' confronta l'identita (indirizzo in memoria), non il valore
```

### String interning

```python
import sys

# CPython interna automaticamente:
# 1. Stringhe che sembrano identificatori (lettere, cifre, underscore)
# 2. Stringhe letterali nel bytecode
# 3. Nomi di attributi e variabili

a = "hello"
b = "hello"
print(f"'hello' is 'hello': {a is b}")  # True — internata

# Stringhe con spazi o caratteri speciali NON vengono internate
a = "hello world"
b = "hello world"
print(f"'hello world' is 'hello world': {a is b}")  # Potrebbe essere True o False

# Interning manuale con sys.intern()
a = sys.intern("hello world!!")
b = sys.intern("hello world!!")
print(f"intern: {a is b}")  # True — forzatamente internata

# Caso d'uso: confronto rapido di stringhe ripetute
# Senza interning: confronto O(n) carattere per carattere
# Con interning: confronto O(1) per identita (is)

# Esempio: parsing di log con campi ripetitivi
def parse_log_ottimizzato(righe):
    """Parse di log con interning dei campi ripetuti."""
    risultati = []
    for riga in righe:
        parti = riga.split()
        record = {
            'livello': sys.intern(parti[0]),   # INFO, WARN, ERROR — pochi valori
            'modulo': sys.intern(parti[1]),     # auth, api, db — pochi valori
            'messaggio': parti[2],              # NON internare — troppi valori unici
        }
        risultati.append(record)
    return risultati

# Il risparmio e significativo con milioni di righe:
# senza intern: ogni "INFO" e un oggetto str separato
# con intern: tutti i "INFO" puntano allo stesso oggetto
```

### Ottimizzazioni del compilatore per costanti

```python
# Il compilatore CPython (peephole optimizer) ottimizza le costanti:

# Constant folding — calcolo a compile time
import dis

def esempio():
    x = 3 * 7 * 24 * 60 * 60  # Calcolato a compile time
    return x

dis.dis(esempio)
# LOAD_CONST 1814400   (gia calcolato!)

# Tuple costanti vengono condivise
def f():
    return (1, 2, 3)

def g():
    return (1, 2, 3)

# f() e g() possono restituire lo stesso oggetto tuple
# Il compilatore puo decidere di condividere la costante
```

---

## Strutture dati memory-efficient

Python offre diverse strutture dati ottimizzate per il consumo di memoria, utili quando si lavora con grandi quantita di dati omogenei.

### array.array: array tipizzati C-style

```python
import array
import sys

# array.array usa storage contiguo come un array C
# Ogni elemento occupa un numero fisso di bytes (niente overhead PyObject)

# Tipo 'i' = signed int (4 bytes per elemento)
arr = array.array('i', range(10_000))
lst = list(range(10_000))

dim_arr = sys.getsizeof(arr)
dim_lst = sys.getsizeof(lst) + sum(sys.getsizeof(x) for x in lst)

print(f"array.array: {dim_arr:>10,} bytes ({dim_arr/1024:.1f} KiB)")
print(f"list:        {dim_lst:>10,} bytes ({dim_lst/1024:.1f} KiB)")
print(f"Risparmio:   {(1 - dim_arr/dim_lst)*100:.0f}%")

# Codici tipo principali:
# 'b' = signed char (1 byte),  'B' = unsigned char (1 byte)
# 'h' = signed short (2 bytes), 'H' = unsigned short (2 bytes)
# 'i' = signed int (2-4 bytes), 'I' = unsigned int (2-4 bytes)
# 'l' = signed long (4 bytes),  'L' = unsigned long (4 bytes)
# 'q' = signed long long (8 bytes), 'Q' = unsigned long long (8 bytes)
# 'f' = float (4 bytes),        'd' = double (8 bytes)

# Operazioni base
arr = array.array('d', [1.0, 2.5, 3.7])
arr.append(4.2)
arr.extend([5.0, 6.1])
print(f"Somma: {sum(arr)}")

# Conversione da/a bytes
dati_bytes = arr.tobytes()
arr2 = array.array('d')
arr2.frombytes(dati_bytes)
```

### memoryview: accesso zero-copy

```python
# memoryview permette di accedere ai dati binari senza copiarli
# Fondamentale per l'I/O ad alte prestazioni

data = bytearray(b"Hello, Python Memory Management!")

# Crea una view — nessuna copia dei dati
view = memoryview(data)

# Slicing di un memoryview crea un'altra view (non una copia!)
sotto_view = view[7:13]
print(bytes(sotto_view))  # b'Python'

# Modificare la view modifica i dati originali
sotto_view[0] = ord('C')
print(data)  # bytearray(b'Hello, Cython Memory Management!')

# ── Uso pratico: I/O efficiente ───────────────────────────
import array

def elabora_chunk(buffer, start, end):
    """Elabora un chunk del buffer senza copiarlo."""
    chunk = memoryview(buffer)[start:end]
    # ... elaborazione sul chunk ...
    return sum(chunk)

buf = array.array('B', range(256))  # 256 bytes
risultato = elabora_chunk(buf, 10, 50)
print(f"Somma chunk [10:50]: {risultato}")

# ── memoryview con struct ─────────────────────────────────
import struct

# Interpreta i bytes come strutture C
dati = bytearray(16)
struct.pack_into('iif', dati, 0, 42, 100, 3.14)

mv = memoryview(dati)
# Cast a un formato specifico
valori = struct.unpack_from('iif', mv)
print(f"Valori: {valori}")  # (42, 100, 3.140000104904175)
```

### struct: packing binario efficiente

```python
import struct
import sys

# struct.pack converte valori Python in bytes compatti
# Utile per protocolli binari, file format, IPC

# Un "record" come oggetto Python
class RecordPython:
    def __init__(self, id_, valore, flag):
        self.id_ = id_          # int
        self.valore = valore    # float
        self.flag = flag         # bool

# Lo stesso record come bytes con struct
formato = 'i d ?'  # int(4) + double(8) + bool(1) = 13 bytes (+ padding)

record_obj = RecordPython(42, 3.14, True)
record_bytes = struct.pack(formato, 42, 3.14, True)

dim_obj = sys.getsizeof(record_obj) + sys.getsizeof(record_obj.__dict__)
dim_bytes = len(record_bytes)

print(f"Oggetto Python: {dim_obj} bytes")
print(f"struct.pack:    {dim_bytes} bytes")
print(f"Risparmio:      {(1 - dim_bytes/dim_obj)*100:.0f}%")

# Unpack per leggere i valori
id_, valore, flag = struct.unpack(formato, record_bytes)
print(f"Unpacked: id={id_}, valore={valore}, flag={flag}")

# ── Batch di record ───────────────────────────────────────
# Con struct si possono impacchettare migliaia di record
# in un singolo buffer di bytes
n_record = 100_000
buffer = bytearray(struct.calcsize(formato) * n_record)
for i in range(n_record):
    struct.pack_into(formato, buffer, i * struct.calcsize(formato),
                     i, float(i) * 0.1, i % 2 == 0)

print(f"Buffer per {n_record:,} record: {len(buffer):,} bytes "
      f"({len(buffer)/1024/1024:.1f} MiB)")
```

### numpy arrays (per dati numerici)

```python
import sys

# numpy e lo standard de facto per dati numerici in Python
try:
    import numpy as np

    # Confronto: lista Python vs numpy array
    n = 1_000_000
    lista = list(range(n))
    arr = np.arange(n, dtype=np.int32)

    dim_lista = sys.getsizeof(lista) + n * sys.getsizeof(0)
    dim_arr = arr.nbytes + sys.getsizeof(arr)

    print(f"Lista Python: {dim_lista / 1024 / 1024:.1f} MiB")
    print(f"NumPy array:  {dim_arr / 1024 / 1024:.1f} MiB")
    print(f"Risparmio:    {(1 - dim_arr/dim_lista)*100:.0f}%")

    # numpy opera in bulk senza creare oggetti Python intermedi
    # Non solo meno memoria, ma ordini di grandezza piu veloce

    # Tipi con dimensioni diverse
    for dtype in [np.int8, np.int16, np.int32, np.int64, np.float32, np.float64]:
        arr = np.zeros(n, dtype=dtype)
        print(f"  {str(dtype):>15}: {arr.nbytes / 1024 / 1024:.1f} MiB")

except ImportError:
    print("numpy non installato")
```

### collections.namedtuple e typing.NamedTuple

```python
import sys
from collections import namedtuple
from typing import NamedTuple

# NamedTuple: immutabile, leggero, niente __dict__
Punto = namedtuple('Punto', ['x', 'y', 'z'])

class PuntoCls:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

p_nt = Punto(1.0, 2.0, 3.0)
p_cls = PuntoCls(1.0, 2.0, 3.0)

print(f"namedtuple: {sys.getsizeof(p_nt)} bytes")
print(f"classe:     {sys.getsizeof(p_cls) + sys.getsizeof(p_cls.__dict__)} bytes")

# typing.NamedTuple: sintassi moderna con type hints
class Coordinata(NamedTuple):
    x: float
    y: float
    z: float
    nome: str = "origine"  # Default value

c = Coordinata(1.0, 2.0, 3.0)
print(f"NamedTuple: {sys.getsizeof(c)} bytes")
print(f"Accesso: x={c.x}, y={c.y}, z={c.z}, nome={c.nome}")
```

---

## Generatori e processing di grandi dataset

I generatori sono lo strumento principale per elaborare grandi quantita di dati senza caricarli interamente in memoria. Un generatore produce valori uno alla volta (lazy evaluation), mantenendo il consumo di memoria costante indipendentemente dalla dimensione dell'input.

### Confronto: lista vs generatore

```python
import sys
import tracemalloc

# ── Lista: tutto in memoria ───────────────────────────────
def quadrati_lista(n):
    return [x ** 2 for x in range(n)]

# ── Generatore: un elemento alla volta ────────────────────
def quadrati_gen(n):
    for x in range(n):
        yield x ** 2

# Confronto memoria
n = 10_000_000

tracemalloc.start()
snap1 = tracemalloc.take_snapshot()

# Con lista
risultato_lista = quadrati_lista(n)
snap2 = tracemalloc.take_snapshot()
top = snap2.compare_to(snap1, 'lineno')
mem_lista = sum(s.size for s in top if s.size > 0)

del risultato_lista
tracemalloc.clear_traces()
snap3 = tracemalloc.take_snapshot()

# Con generatore
risultato_gen = quadrati_gen(n)
snap4 = tracemalloc.take_snapshot()
top = snap4.compare_to(snap3, 'lineno')
mem_gen = sum(s.size for s in top if s.size > 0)

print(f"Lista:      {mem_lista / 1024 / 1024:.1f} MiB")
print(f"Generatore: {mem_gen / 1024:.1f} KiB")

tracemalloc.stop()

# Il generatore occupa memoria costante (~200 bytes)
# indipendentemente da n — 10 milioni o 10 miliardi
```

### Pipeline di generatori

```python
import csv
from pathlib import Path
from typing import Generator, Iterator

def leggi_righe(path: str) -> Generator[str, None, None]:
    """Legge un file riga per riga senza caricarlo in memoria."""
    with open(path, 'r') as f:
        for riga in f:
            yield riga.rstrip('\n')

def filtra_non_vuote(righe: Iterator[str]) -> Generator[str, None, None]:
    """Filtra le righe vuote."""
    for riga in righe:
        if riga.strip():
            yield riga

def parse_csv_lazy(righe: Iterator[str]) -> Generator[dict, None, None]:
    """Parse CSV lazy — una riga alla volta."""
    reader = csv.DictReader(righe)
    yield from reader

def filtra_per_campo(records: Iterator[dict], campo: str,
                     valore: str) -> Generator[dict, None, None]:
    """Filtra i record per un campo specifico."""
    for record in records:
        if record.get(campo) == valore:
            yield record

# ── Pipeline completa ─────────────────────────────────────
# Ogni step elabora un elemento alla volta
# Memoria usata: O(1) indipendentemente dalla dimensione del file

# pipeline = filtra_per_campo(
#     parse_csv_lazy(
#         filtra_non_vuote(
#             leggi_righe("enorme_dataset.csv")
#         )
#     ),
#     campo="stato",
#     valore="attivo"
# )
# for record in pipeline:
#     elabora(record)
```

### itertools per elaborazione lazy

```python
import itertools

# itertools opera su generatori senza materializzare liste intermedie

# islice: prendi i primi N elementi
primi_100 = itertools.islice(range(10_000_000), 100)

# chain: concatena iterabili senza copiarli
combinati = itertools.chain(range(1000), range(2000), range(3000))

# groupby: raggruppa elementi adiacenti
dati = sorted([(1, 'a'), (1, 'b'), (2, 'c'), (2, 'd')])
for chiave, gruppo in itertools.groupby(dati, key=lambda x: x[0]):
    print(f"Gruppo {chiave}: {list(gruppo)}")

# batched (Python 3.12+): elabora a batch
# from itertools import batched
# for batch in batched(range(1_000_000), 1000):
#     elabora_batch(batch)  # batch e una tupla di 1000 elementi

# Fallback per Python < 3.12
def batched(iterable, n):
    """Equivalente di itertools.batched per Python < 3.12."""
    it = iter(iterable)
    while True:
        batch = tuple(itertools.islice(it, n))
        if not batch:
            return
        yield batch

# Uso: elabora 10 milioni di record in batch da 10.000
# Memoria: O(batch_size), non O(n)
for batch in batched(range(10_000_000), 10_000):
    _ = sum(batch)  # Elaborazione del batch
```

---

## Semantica di copia

La comprensione di come Python copia gli oggetti e fondamentale per evitare sia bug sottili (modifiche inattese a dati condivisi) sia consumo di memoria non necessario (copie ridondanti).

### Assegnamento: nessuna copia

```python
# L'assegnamento in Python NON copia mai l'oggetto
# Crea solo un nuovo riferimento allo stesso oggetto

originale = [1, [2, 3], {'a': 4}]
riferimento = originale

# Stessa identita in memoria
print(f"Stesso oggetto: {originale is riferimento}")  # True
print(f"id: {id(originale)} == {id(riferimento)}")

# Modifiche visibili da entrambi i nomi
riferimento.append(5)
print(f"originale: {originale}")  # [1, [2, 3], {'a': 4}, 5]
```

### Shallow copy: copia superficiale

```python
import copy

originale = [1, [2, 3], {'a': 4}]

# Modi per creare una shallow copy
copia1 = originale.copy()       # Metodo .copy()
copia2 = list(originale)         # Costruttore
copia3 = originale[:]            # Slicing
copia4 = copy.copy(originale)    # copy.copy()

# La shallow copy crea un nuovo container, ma i contenuti
# sono gli stessi oggetti (condivisi)
print(f"Container diverso: {originale is not copia1}")  # True
print(f"Contenuto condiviso: {originale[1] is copia1[1]}")  # True

# Modifiche al container non si propagano
copia1.append(999)
print(f"originale: {originale}")  # Invariato
print(f"copia1:    {copia1}")     # Ha 999

# MA modifiche agli oggetti INTERNI si propagano!
copia1[1].append(99)
print(f"originale[1]: {originale[1]}")  # [2, 3, 99] — MODIFICATO!
print(f"copia1[1]:    {copia1[1]}")     # [2, 3, 99]
```

### Deep copy: copia profonda

```python
import copy
import sys

originale = [1, [2, 3], {'a': [4, 5]}]

# Deep copy: crea copie ricorsive di tutti gli oggetti
copia_profonda = copy.deepcopy(originale)

# Container e contenuti sono tutti oggetti diversi
print(f"Container diverso: {originale is not copia_profonda}")     # True
print(f"Lista interna diversa: {originale[1] is not copia_profonda[1]}")  # True
print(f"Dict interno diverso: {originale[2] is not copia_profonda[2]}")   # True

# Modifiche completamente indipendenti
copia_profonda[1].append(99)
copia_profonda[2]['a'].append(99)
print(f"originale: {originale}")          # Invariato
print(f"copia:     {copia_profonda}")     # Modificata

# ATTENZIONE: deepcopy gestisce correttamente i cicli
ciclico = [1, 2]
ciclico.append(ciclico)  # Ciclo!

copia_ciclica = copy.deepcopy(ciclico)
# Non va in loop infinito — deepcopy traccia gli oggetti gia copiati
print(f"Ciclo preservato: {copia_ciclica[2] is copia_ciclica}")  # True
```

### Implicazioni per la memoria

```python
import copy
import sys
from pympler import asizeof  # pip install pympler

# Confronto costi di memoria
grande_struttura = {
    f"chiave_{i}": list(range(100))
    for i in range(1000)
}

# Stima dimensioni
dim_originale = asizeof.asizeof(grande_struttura)
dim_shallow = asizeof.asizeof(copy.copy(grande_struttura))
dim_deep = asizeof.asizeof(copy.deepcopy(grande_struttura))

print(f"Originale:    {dim_originale / 1024 / 1024:.1f} MiB")
print(f"Shallow copy: i nuovi bytes sono solo il container esterno")
print(f"Deep copy:    {dim_deep / 1024 / 1024:.1f} MiB (raddoppia!)")

# Regola: usa shallow copy quando i contenuti sono immutabili
# Usa deep copy solo quando devi modificare gli oggetti interni
# Non copiare affatto quando non serve — il modo piu efficiente
```

---

## Flusso di lavoro per il profiling

Un approccio sistematico al profiling evita di perdere tempo a ottimizzare le parti sbagliate del codice.

### Workflow in 7 passi

```
Passo 1: DEFINISCI l'obiettivo misurabile
         "Ridurre il tempo di risposta P99 da 800ms a 200ms"
         "Ridurre il consumo di memoria RSS da 2 GiB a 500 MiB"
                    │
                    ▼
Passo 2: MISURA la baseline
         cProfile per CPU, tracemalloc per memoria
         Salva i risultati come riferimento
                    │
                    ▼
Passo 3: IDENTIFICA il collo di bottiglia
         Il 90% del tempo e speso nel 10% del codice
         Cerca le funzioni con alto cumtime
                    │
                    ▼
Passo 4: FORMULA un'ipotesi
         "Questa funzione e lenta perche alloca troppi oggetti"
         "Questo loop e O(n^2) e dovrebbe essere O(n)"
                    │
                    ▼
Passo 5: APPLICA una singola modifica
         Non cambiare 10 cose contemporaneamente!
                    │
                    ▼
Passo 6: MISURA di nuovo
         Confronta con la baseline
         L'ipotesi era corretta?
                    │
                    ▼
Passo 7: RIPETI o FERMA
         Obiettivo raggiunto? -> STOP
         No? -> Torna al Passo 3
```

### Esempio pratico: ottimizzazione di un endpoint API

```python
import cProfile
import pstats
import tracemalloc
import time

# ── Passo 1: Baseline CPU ────────────────────────────────
def profila_endpoint():
    """Simula il profiling di un endpoint."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Simula la logica dell'endpoint
    risultato = endpoint_handler(richiesta_esempio())

    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(20)

    return risultato

# ── Passo 2: Baseline memoria ────────────────────────────
def profila_memoria_endpoint():
    """Profila la memoria dell'endpoint."""
    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()

    risultato = endpoint_handler(richiesta_esempio())

    snap2 = tracemalloc.take_snapshot()
    top = snap2.compare_to(snap1, 'lineno')

    print("Top 10 allocazioni:")
    for stat in top[:10]:
        print(f"  {stat}")

    corrente, picco = tracemalloc.get_traced_memory()
    print(f"\nMemoria corrente: {corrente / 1024:.1f} KiB")
    print(f"Memoria picco:    {picco / 1024:.1f} KiB")

    tracemalloc.stop()
    return risultato

# ── Passo 3: Automatizzare il confronto ──────────────────
class ProfilingContext:
    """Context manager per profiling combinato CPU + memoria."""

    def __init__(self, nome="profiling"):
        self.nome = nome
        self.profiler = cProfile.Profile()

    def __enter__(self):
        tracemalloc.start()
        self._snap_start = tracemalloc.take_snapshot()
        self._time_start = time.perf_counter()
        self.profiler.enable()
        return self

    def __exit__(self, *exc):
        self.profiler.disable()
        self.elapsed = time.perf_counter() - self._time_start
        self._snap_end = tracemalloc.take_snapshot()
        self.corrente, self.picco = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.mem_diff = self._snap_end.compare_to(self._snap_start, 'lineno')

    def report(self, top_n=10):
        print(f"\n{'='*60}")
        print(f"Profiling: {self.nome}")
        print(f"{'='*60}")
        print(f"Tempo totale: {self.elapsed:.4f}s")
        print(f"Memoria picco: {self.picco / 1024 / 1024:.2f} MiB")
        print(f"\nTop {top_n} CPU:")
        stats = pstats.Stats(self.profiler)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(top_n)
        print(f"\nTop {top_n} allocazioni memoria:")
        for stat in self.mem_diff[:top_n]:
            print(f"  {stat}")

# Uso
# with ProfilingContext("endpoint /api/users") as ctx:
#     risultato = endpoint_handler(richiesta)
# ctx.report()
```

### Profiling I/O: identificare colli di bottiglia I/O

```python
import time
import functools
from contextlib import contextmanager

# ── Decorator per misurare l'I/O ──────────────────────────
def misura_io(func):
    """Decorator che misura il tempo speso in I/O."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        risultato = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[I/O] {func.__name__}: {elapsed:.4f}s")
        return risultato
    return wrapper

# ── Context manager per misurare sezioni ──────────────────
@contextmanager
def timer(nome):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"[Timer] {nome}: {elapsed:.4f}s")

# ── Uso ───────────────────────────────────────────────────
@misura_io
def query_database(query):
    """Simula una query al database."""
    time.sleep(0.05)
    return [{"id": i} for i in range(100)]

@misura_io
def chiama_servizio_esterno(url):
    """Simula una chiamata HTTP."""
    time.sleep(0.1)
    return {"status": "ok"}

def handler():
    with timer("handler totale"):
        with timer("database"):
            dati = query_database("SELECT * FROM users")
        with timer("servizio esterno"):
            risposta = chiama_servizio_esterno("https://api.esempio.com/check")
        with timer("elaborazione"):
            risultato = [d['id'] ** 2 for d in dati]
    return risultato

handler()
# Output:
# [I/O] query_database: 0.0503s
# [Timer] database: 0.0504s
# [I/O] chiama_servizio_esterno: 0.1001s
# [Timer] servizio esterno: 0.1002s
# [Timer] elaborazione: 0.0001s
# [Timer] handler totale: 0.1508s
# -> Il collo di bottiglia e il servizio esterno (66% del tempo)
```

---

## Profiling in produzione

Il profiling in produzione richiede strumenti con overhead minimo (< 2%) che possono funzionare continuamente senza impatto percepibile sugli utenti.

### py-spy in produzione

```bash
# py-spy ha overhead < 1% e non richiede modifiche al codice
# Puo agganciarsi a processi in esecuzione

# Flame graph di 30 secondi su un server in produzione
py-spy record --duration 30 --pid $(pgrep -f "gunicorn") \
    --output /tmp/prod_profile.svg

# Campionamento a bassa frequenza per ridurre l'overhead
py-spy record --rate 10 --duration 60 --pid 12345 \
    --output /tmp/low_overhead.svg

# Dump istantaneo dello stack (zero overhead)
py-spy dump --pid 12345 > /tmp/stack_dump.txt
```

### Continuous profiling con Pyroscope

```python
# Pyroscope: continuous profiling as a service
# pip install pyroscope-io

import pyroscope

# Configurazione base
pyroscope.configure(
    application_name="mia-app-python",
    server_address="http://pyroscope-server:4040",
    sample_rate=100,          # 100 Hz
    detect_subprocesses=True,
    tags={
        "environment": "production",
        "version": "1.2.3",
        "region": "eu-west-1",
    },
)

# Il profiling avviene automaticamente in background
# I dati vengono inviati al server Pyroscope per aggregazione
# e visualizzazione (flame graph temporali, confronto tra deploy)

# Tagging dinamico per isolare le richieste
def handle_request(request):
    with pyroscope.tag_wrapper({
        "endpoint": request.path,
        "method": request.method,
    }):
        return process_request(request)
```

#### Grafana Pyroscope: architettura e integrazione

A partire dal 2023 Pyroscope e stato acquisito da Grafana Labs e fuso con Grafana Phlare (un progetto precedente di continuous profiling ispirato a Google-Wide Profiling). Il risultato e **Grafana Pyroscope**, un backend unico che accetta dati di profiling da SDK nativi, Grafana Alloy (l'agente di raccolta unificato che ha sostituito Grafana Agent) e push diretti via API.

**Architettura.** Pyroscope si integra con lo stack Grafana (Loki per i log, Tempo per le trace, Mimir per le metriche) tramite *exemplar link* e *label matching*. Quando si analizza una trace lenta in Tempo, un link diretto porta al flame graph Pyroscope corrispondente a quella finestra temporale e a quei label — eliminando il bisogno di correlare manualmente profiling e trace.

**Grafana Alloy (auto-strumentazione).** Alloy supporta la raccolta automatica di profili Python senza modificare il codice dell'applicazione. Basta configurare un target scraping nel file di configurazione di Alloy:

```yaml
# Configurazione Alloy per scraping dei profili Python
# Richiede che l'applicazione esponga un endpoint pprof-compatibile
# (ad esempio tramite py-spy in modalita http)
pyroscope.scrape "python_app" {
  targets    = [{"__address__" = "localhost:8080", "service_name" = "mia-app"}]
  profiling_config {
    profile.process_cpu { enabled = true }
    profile.memory      { enabled = true }
  }
  forward_to = [pyroscope.write.default.receiver]
}

pyroscope.write "default" {
  endpoint {
    url = "http://pyroscope:4040"
  }
}
```

**Confronto flame graph.** Grafana Pyroscope offre la funzionalita di *comparison view*: si selezionano due finestre temporali (ad esempio prima e dopo un deploy) e il flame graph mostra in verde le funzioni che consumano meno risorse nella versione nuova e in rosso quelle che ne consumano di piu. Questa visualizzazione differenziale e fondamentale per validare l'efficacia di un'ottimizzazione o individuare regressioni introdotte da un rilascio.

**Grafana Cloud.** Per chi non vuole gestire l'infrastruttura, Grafana Cloud offre Pyroscope come servizio gestito con retention configurabile e accesso diretto dal dashboard di Grafana. L'SDK Python (`pyroscope-io`) si configura puntando all'endpoint cloud anziche a un'istanza locale:

```python
pyroscope.configure(
    application_name="mia-app",
    server_address="https://<instance>.grafana.net",
    auth_token="glc_...",  # Token Grafana Cloud
    tags={"env": "prod", "version": "2.1.0"},
)
```

### Profiling a basso overhead con perf e eBPF

```bash
# perf: profiler del kernel Linux — overhead minimo
# Richiede privilegi root e kernel con debug symbols

# Profiling di un processo Python
perf record -g -p $(pgrep -f "python mia_app.py") -- sleep 30
perf report

# Con stack Python leggibili (richiede Python compilato con --enable-profiling)
# o usando py-spy come alternativa piu pratica
```

### Profiling di applicazioni async

```python
import asyncio
import cProfile
import time

# ── Profiling async con cProfile ──────────────────────────
# cProfile funziona con async ma non mostra i tempi di attesa I/O
# Utile per identificare il codice CPU-bound nelle coroutine

async def operazione_async():
    await asyncio.sleep(0.1)  # I/O simulato
    return sum(range(100_000))  # CPU-bound

profiler = cProfile.Profile()
profiler.enable()
asyncio.run(operazione_async())
profiler.disable()

import pstats
stats = pstats.Stats(profiler)
stats.strip_dirs()
stats.sort_stats('cumulative')
stats.print_stats(10)

# ── Profiling dei tempi di attesa nelle coroutine ─────────
async def profila_coroutine(coro, nome="coro"):
    """Wrapper per misurare il tempo totale di una coroutine."""
    start = time.perf_counter()
    risultato = await coro
    elapsed = time.perf_counter() - start
    print(f"[Async] {nome}: {elapsed:.4f}s")
    return risultato

# ── yappi: profiler con supporto nativo per async ─────────
# pip install yappi
# import yappi
#
# yappi.set_clock_type("wall")  # Wall time per includere l'I/O wait
# yappi.start()
# asyncio.run(main())
# yappi.stop()
#
# stats = yappi.get_func_stats()
# stats.print_all()
# stats.save("async_profile.prof", type="pstat")
```

---

## Benchmarking

Il benchmarking misura le prestazioni in modo riproducibile e statisticamente rigoroso. A differenza del profiling (che identifica *dove*), il benchmarking quantifica *quanto*.

### timeit: microbenchmark

```python
import timeit

# ── Da riga di comando ────────────────────────────────────
# python -m timeit -n 1000 -r 5 "sum(range(10000))"
# python -m timeit -s "import math" "math.sqrt(42)"

# ── Uso programmatico ────────────────────────────────────
# Confronto: lista vs generatore per sum()
t_lista = timeit.timeit('sum([x**2 for x in range(1000)])', number=10000)
t_gen = timeit.timeit('sum(x**2 for x in range(1000))', number=10000)

print(f"Lista comprehension: {t_lista:.4f}s")
print(f"Generator expression: {t_gen:.4f}s")
print(f"Vincitore: {'lista' if t_lista < t_gen else 'generatore'}")

# ── Setup separato (non misurato) ─────────────────────────
risultato = timeit.timeit(
    stmt='sorted(dati)',
    setup='import random; dati = [random.randint(0, 10000) for _ in range(10000)]',
    number=100
)
print(f"Sorting 10k int: {risultato/100*1000:.2f}ms per iterazione")

# ── Autorange per trovare automaticamente il numero di iterazioni ──
timer = timeit.Timer('"-".join(str(n) for n in range(100))')
numero, tempo = timer.autorange()
print(f"{numero} iterazioni in {tempo:.4f}s "
      f"({tempo/numero*1_000_000:.2f} us/iter)")
```

### pytest-benchmark: benchmark nella suite di test

```bash
pip install pytest-benchmark
```

```python
# test_performance.py

def fibonacci_ricorsivo(n):
    if n < 2:
        return n
    return fibonacci_ricorsivo(n - 1) + fibonacci_ricorsivo(n - 2)

def fibonacci_iterativo(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# ── Test benchmark ────────────────────────────────────────
def test_fibonacci_ricorsivo(benchmark):
    risultato = benchmark(fibonacci_ricorsivo, 20)
    assert risultato == 6765

def test_fibonacci_iterativo(benchmark):
    risultato = benchmark(fibonacci_iterativo, 20)
    assert risultato == 6765

# Esecuzione: pytest test_performance.py --benchmark-compare
# Output: tabella con min, max, mean, stddev, rounds

# ── Benchmark con setup ───────────────────────────────────
def test_sorting_benchmark(benchmark):
    import random
    dati = [random.randint(0, 10000) for _ in range(10000)]

    # pedantic=True: minimo 5 rounds, 5 iterazioni per round
    risultato = benchmark.pedantic(
        sorted,
        args=(dati,),
        rounds=10,
        iterations=5,
    )
    assert len(risultato) == 10000

# ── Confronto tra run ─────────────────────────────────────
# pytest --benchmark-save=baseline test_performance.py
# ... modifica il codice ...
# pytest --benchmark-compare=baseline test_performance.py
# -> mostra la regressione/miglioramento percentuale
```

### Rigore statistico nei benchmark

```python
import timeit
import statistics

def benchmark_rigoroso(stmt, setup='pass', n_campioni=30, n_iter=1000):
    """Esegue un benchmark con analisi statistica."""
    tempi = []
    for _ in range(n_campioni):
        t = timeit.timeit(stmt, setup=setup, number=n_iter)
        tempi.append(t / n_iter)  # Tempo per singola iterazione

    media = statistics.mean(tempi)
    mediana = statistics.median(tempi)
    deviazione = statistics.stdev(tempi)
    minimo = min(tempi)

    print(f"Risultati ({n_campioni} campioni, {n_iter} iter/campione):")
    print(f"  Media:      {media*1_000_000:.2f} us")
    print(f"  Mediana:    {mediana*1_000_000:.2f} us")
    print(f"  Std dev:    {deviazione*1_000_000:.2f} us")
    print(f"  Min:        {minimo*1_000_000:.2f} us")
    print(f"  CoV:        {deviazione/media*100:.1f}%")

    if deviazione/media > 0.10:
        print("  ATTENZIONE: alta varianza (CoV > 10%)")
        print("  Possibili cause: thermal throttling, GC, altri processi")

    return tempi

# Confronto due implementazioni con rigore statistico
print("=== dict lookup ===")
benchmark_rigoroso("d.get('chiave')", "d = {'chiave': 42}")

print("\n=== try/except KeyError ===")
benchmark_rigoroso(
    "try:\n    d['chiave']\nexcept KeyError:\n    pass",
    "d = {'chiave': 42}"
)
```

---

## Pattern di ottimizzazione memoria

Pattern concreti per ridurre il consumo di memoria in scenari comuni.

### Lazy loading di attributi pesanti

```python
class Documento:
    """Carica il contenuto pesante solo quando serve."""

    def __init__(self, path):
        self.path = path
        self._contenuto = None  # Non caricato

    @property
    def contenuto(self):
        if self._contenuto is None:
            with open(self.path) as f:
                self._contenuto = f.read()
        return self._contenuto

    def libera_memoria(self):
        """Libera il contenuto caricato."""
        self._contenuto = None

# Con descriptor per il pattern generico
class LazyAttribute:
    """Descriptor per attributi caricati on-demand."""

    def __init__(self, loader):
        self.loader = loader
        self.attr_name = None

    def __set_name__(self, owner, name):
        self.attr_name = f"_lazy_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if not hasattr(obj, self.attr_name):
            setattr(obj, self.attr_name, self.loader(obj))
        return getattr(obj, self.attr_name)

class Report:
    def _carica_dati(self):
        # Simula caricamento costoso
        return list(range(1_000_000))

    dati = LazyAttribute(_carica_dati)

r = Report()
# r.dati non e stato caricato fino a qui
# print(r.dati)  # Ora viene caricato
```

### Flyweight pattern con __slots__

```python
import sys

class Colore:
    """Flyweight: condividi istanze per valori identici."""
    __slots__ = ('r', 'g', 'b')
    _cache = {}

    def __new__(cls, r, g, b):
        chiave = (r, g, b)
        if chiave not in cls._cache:
            istanza = super().__new__(cls)
            istanza.r = r
            istanza.g = g
            istanza.b = b
            cls._cache[chiave] = istanza
        return cls._cache[chiave]

# Tutte le istanze con gli stessi valori sono lo stesso oggetto
c1 = Colore(255, 0, 0)
c2 = Colore(255, 0, 0)
c3 = Colore(0, 255, 0)

print(f"c1 is c2: {c1 is c2}")  # True — stessa istanza
print(f"c1 is c3: {c1 is c3}")  # False — valori diversi
print(f"Istanze in cache: {len(Colore._cache)}")  # 2
```

### Object pool

```python
from collections import deque
from contextlib import contextmanager

class ObjectPool:
    """Pool di oggetti riusabili per evitare allocazione/deallocazione."""

    def __init__(self, factory, max_size=100):
        self._factory = factory
        self._pool = deque(maxlen=max_size)
        self._in_uso = 0

    @contextmanager
    def acquire(self):
        """Prendi un oggetto dal pool (o creane uno nuovo)."""
        if self._pool:
            obj = self._pool.popleft()
        else:
            obj = self._factory()
        self._in_uso += 1
        try:
            yield obj
        finally:
            self._in_uso -= 1
            self._pool.append(obj)

    @property
    def stats(self):
        return {
            'disponibili': len(self._pool),
            'in_uso': self._in_uso,
        }

# Uso: pool di buffer riusabili
pool = ObjectPool(lambda: bytearray(4096), max_size=50)

with pool.acquire() as buffer:
    buffer[:5] = b"hello"
    # ... usa il buffer ...
# Il buffer viene restituito al pool, non deallocato
print(f"Pool: {pool.stats}")
```

### Compressione in-memory

```python
import zlib
import sys
import pickle

class DatiCompressi:
    """Mantiene i dati compressi in memoria, decomprime on-demand."""
    __slots__ = ('_dati_compressi', '_dimensione_originale')

    def __init__(self, dati):
        serializzati = pickle.dumps(dati)
        self._dimensione_originale = len(serializzati)
        self._dati_compressi = zlib.compress(serializzati, level=6)

    @property
    def dati(self):
        return pickle.loads(zlib.decompress(self._dati_compressi))

    @property
    def risparmio(self):
        compressa = len(self._dati_compressi)
        return 1 - compressa / self._dimensione_originale

# Esempio: compressione di dati ripetitivi
dati_originali = [{"tipo": "log", "livello": "INFO",
                    "messaggio": f"Evento {i}"} for i in range(100_000)]

dim_originale = sys.getsizeof(pickle.dumps(dati_originali))
compressi = DatiCompressi(dati_originali)
dim_compressa = sys.getsizeof(compressi._dati_compressi)

print(f"Originale:   {dim_originale / 1024 / 1024:.1f} MiB")
print(f"Compressa:   {dim_compressa / 1024 / 1024:.1f} MiB")
print(f"Risparmio:   {compressi.risparmio*100:.0f}%")

# Accesso: decomprime al volo
# primi_10 = compressi.dati[:10]
```

---

## Memory leak: cause, rilevamento, risoluzione

I memory leak in Python sono piu comuni di quanto si pensi. Anche con la garbage collection automatica, diversi pattern possono causare un consumo di memoria che cresce indefinitamente.

### Causa 1: reference cycle con risorse esterne

```python
import gc
import weakref

# ── Problema ──────────────────────────────────────────────
class Padre:
    def __init__(self):
        self.figlio = Figlio(self)

class Figlio:
    def __init__(self, padre):
        self.padre = padre  # Ciclo: Padre <-> Figlio

# Il GC raccogliera il ciclo, MA se una delle classi gestisce
# risorse esterne (file, socket, connessioni DB), il timing
# della deallocazione e imprevedibile

# ── Soluzione: weak reference ─────────────────────────────
class PadreFix:
    def __init__(self):
        self.figlio = FiglioFix(self)

class FiglioFix:
    def __init__(self, padre):
        self._padre_ref = weakref.ref(padre)  # Niente ciclo!

    @property
    def padre(self):
        p = self._padre_ref()
        if p is None:
            raise RuntimeError("Padre deallocato")
        return p
```

### Causa 2: cache globali non limitate

```python
import functools
import weakref

# ── Problema: cache che cresce senza limiti ───────────────
_cache_globale = {}

def get_utente(id_):
    if id_ not in _cache_globale:
        _cache_globale[id_] = carica_da_db(id_)  # Mai rimosso!
    return _cache_globale[id_]

# Dopo milioni di richieste, _cache_globale occupa GiB di memoria

# ── Soluzione 1: LRU cache con dimensione massima ────────
@functools.lru_cache(maxsize=10_000)
def get_utente_fix1(id_):
    return carica_da_db(id_)

# Info sulla cache
print(get_utente_fix1.cache_info())
# CacheInfo(hits=..., misses=..., maxsize=10000, currsize=...)

# Pulizia manuale
get_utente_fix1.cache_clear()

# ── Soluzione 2: WeakValueDictionary ──────────────────────
_cache_weak = weakref.WeakValueDictionary()

def get_utente_fix2(id_):
    utente = _cache_weak.get(id_)
    if utente is None:
        utente = carica_da_db(id_)
        _cache_weak[id_] = utente
    return utente

# Quando nessuno usa piu un utente, viene automaticamente
# rimosso dalla cache

# ── Soluzione 3: cache con TTL ────────────────────────────
import time
from collections import OrderedDict

class TTLCache:
    """Cache con scadenza temporale."""
    def __init__(self, maxsize=1000, ttl_seconds=300):
        self._cache = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl_seconds

    def get(self, chiave):
        if chiave in self._cache:
            valore, timestamp = self._cache[chiave]
            if time.monotonic() - timestamp < self._ttl:
                self._cache.move_to_end(chiave)
                return valore
            del self._cache[chiave]
        return None

    def set(self, chiave, valore):
        if len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)  # Rimuovi il piu vecchio
        self._cache[chiave] = (valore, time.monotonic())

def carica_da_db(id_):
    """Placeholder."""
    return {"id": id_, "nome": f"Utente_{id_}"}
```

### Causa 3: closure che catturano variabili grandi

```python
import sys

# ── Problema: closure che mantiene vivo un oggetto grande ─
def crea_handler():
    dati_enormi = list(range(1_000_000))  # 8+ MiB

    def handler(indice):
        return dati_enormi[indice]  # Cattura TUTTA la lista!

    return handler

h = crea_handler()
# dati_enormi non puo essere deallocata perche h la riferisce
# tramite la closure, anche se h usa solo un indice alla volta

# ── Soluzione: cattura solo quello che serve ──────────────
def crea_handler_fix():
    dati_enormi = list(range(1_000_000))
    # Pre-calcola il risultato o usa un lookup minimo
    lookup = {i: dati_enormi[i] for i in range(100)}  # Solo i necessari
    del dati_enormi  # Libera esplicitamente

    def handler(indice):
        return lookup[indice]

    return handler
```

### Causa 4: `__del__` che impedisce la raccolta

```python
import gc

# ── Problema: __del__ con side effect che crea nuovi riferimenti ──
class ProblematicDel:
    _tutti = []

    def __del__(self):
        # Errore: ricrea un riferimento all'oggetto!
        ProblematicDel._tutti.append(self)

# Anche se il GC identifica questo come raccoglibile,
# il __del__ "resuscita" l'oggetto

# ── Soluzione: usare weakref.finalize ─────────────────────
import weakref

class CleanDel:
    def __init__(self, risorsa):
        self.risorsa = risorsa
        self._finalizer = weakref.finalize(
            self, CleanDel._cleanup, risorsa
        )

    @staticmethod
    def _cleanup(risorsa):
        risorsa.close()  # Pulizia senza riferimento a self
```

### Causa 5: thread-local storage non pulito

```python
import threading

# ── Problema: dati thread-local che crescono ──────────────
_local = threading.local()

def gestisci_richiesta(richiesta):
    # Accumula dati nel thread-local senza mai pulirli
    if not hasattr(_local, 'cronologia'):
        _local.cronologia = []
    _local.cronologia.append(richiesta)  # Cresce per sempre!

# ── Soluzione: pulizia esplicita ──────────────────────────
def gestisci_richiesta_fix(richiesta):
    try:
        _local.richiesta_corrente = richiesta
        # ... elaborazione ...
    finally:
        if hasattr(_local, 'richiesta_corrente'):
            del _local.richiesta_corrente
```

### Rilevamento con objgraph

```python
import objgraph
import gc

# ── Workflow per trovare memory leak ──────────────────────

# 1. Scatta una baseline
objgraph.show_most_common_types(limit=10)

# 2. Esegui le operazioni sospette
# ... codice che potrebbe avere leak ...

# 3. Mostra la crescita
objgraph.show_growth(limit=10)
# Output:
# dict       +1234
# list       +567
# MioOggetto +500  <- Sospetto!

# 4. Indaga gli oggetti sospetti
sospetti = objgraph.by_type('MioOggetto')
print(f"Istanze di MioOggetto: {len(sospetti)}")

# 5. Trova la catena di riferimenti che li mantiene vivi
if sospetti:
    objgraph.show_chain(
        objgraph.find_backref_chain(
            sospetti[0],
            objgraph.is_proper_module
        ),
        filename='leak_chain.png'
    )
```

### Script diagnostico per memory leak

```python
import gc
import sys
import tracemalloc
from collections import Counter

def diagnosi_memoria(soglia_crescita_kb=100, intervallo_secondi=5):
    """Diagnostica automatica per memory leak."""
    tracemalloc.start(10)
    gc.collect()

    snap_precedente = tracemalloc.take_snapshot()
    tipi_precedenti = Counter(type(o).__name__ for o in gc.get_objects())

    import time
    print("Monitoraggio memoria avviato...")
    print(f"Intervallo: {intervallo_secondi}s, soglia: {soglia_crescita_kb} KiB")

    while True:
        time.sleep(intervallo_secondi)
        gc.collect()

        # Analisi tracemalloc
        snap_corrente = tracemalloc.take_snapshot()
        diff = snap_corrente.compare_to(snap_precedente, 'lineno')
        crescita_totale = sum(s.size_diff for s in diff if s.size_diff > 0)

        if crescita_totale > soglia_crescita_kb * 1024:
            print(f"\n{'='*60}")
            print(f"CRESCITA RILEVATA: +{crescita_totale / 1024:.1f} KiB")
            for stat in diff[:5]:
                if stat.size_diff > 0:
                    print(f"  {stat}")

        # Analisi tipi di oggetti
        tipi_correnti = Counter(type(o).__name__ for o in gc.get_objects())
        crescite = {
            tipo: tipi_correnti[tipo] - tipi_precedenti.get(tipo, 0)
            for tipo in tipi_correnti
            if tipi_correnti[tipo] - tipi_precedenti.get(tipo, 0) > 10
        }
        if crescite:
            top = sorted(crescite.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"Tipi in crescita: {top}")

        snap_precedente = snap_corrente
        tipi_precedenti = tipi_correnti

# diagnosi_memoria()  # Esegui in un thread separato
```

---

## Troubleshooting

### Problema 1: il processo Python consuma troppa memoria

**Sintomi:** RSS (Resident Set Size) cresce oltre le aspettative. `top`/`htop` mostra consumo elevato.

**Diagnosi:**

```bash
# Controlla RSS del processo
ps -p <PID> -o rss,vsz,pid,cmd

# Monitora nel tempo
while true; do ps -p <PID> -o rss= | awk '{print strftime("%H:%M:%S"), $1/1024, "MiB"}'; sleep 5; done
```

```python
import tracemalloc, gc

tracemalloc.start()
gc.collect()
snap = tracemalloc.take_snapshot()
for stat in snap.statistics('lineno')[:10]:
    print(stat)
```

**Cause comuni:** cache non limitate, accumulo in liste globali, caricamento di file interi in memoria.

### Problema 2: il GC causa pause (latency spikes)

**Sintomi:** latenza P99 elevata con spike periodici. Correlazione con le raccolte gen-2.

**Diagnosi:**

```python
import gc, time

def gc_callback(phase, info):
    if phase == "start":
        gc_callback._start = time.perf_counter()
    elif phase == "stop":
        elapsed = time.perf_counter() - gc_callback._start
        if elapsed > 0.010:  # > 10ms
            print(f"GC pausa lunga: {elapsed*1000:.1f}ms "
                  f"gen={info['generation']} collected={info['collected']}")

gc.callbacks.append(gc_callback)
```

**Soluzioni:** abbassa il threshold gen-0, usa `gc.freeze()` dopo il fork, riduci i reference cycle.

### Problema 3: cProfile mostra tutto il tempo in una funzione

**Sintomi:** `tottime` alto per una singola funzione, ma non e chiaro quale riga sia il bottleneck.

**Soluzione:** usa `line_profiler` per il profiling riga-per-riga.

```bash
kernprof -l -v mio_modulo.py
```

### Problema 4: il profiling mostra il tempo nel GC

**Sintomi:** tempo significativo speso in `gc.collect()` o nelle funzioni di garbage collection.

**Soluzione:**

```python
import gc

# Riduci i reference cycle
# Usa __slots__ e weak references
# Alza il threshold se accettabile
gc.set_threshold(1400, 15, 15)

# In casi estremi, disabilita il GC durante le operazioni batch
gc.disable()
try:
    batch_processing()
finally:
    gc.enable()
    gc.collect()
```

### Problema 5: memory_profiler mostra crescita costante

**Sintomi:** la colonna "Increment" e sempre positiva, la memoria non cala mai.

**Cause probabili:** global state, memoizzazione senza limiti, observer pattern senza cleanup.

### Problema 6: sys.getsizeof() restituisce valori inaspettati

**Sintomi:** `sys.getsizeof(dict_grande)` restituisce un valore molto inferiore alla dimensione reale.

**Spiegazione:** `sys.getsizeof()` misura solo la dimensione *shallow* del container, non dei contenuti.

```python
from pympler import asizeof

d = {i: list(range(100)) for i in range(1000)}
print(f"getsizeof (shallow): {sys.getsizeof(d) / 1024:.1f} KiB")
print(f"asizeof (deep):      {asizeof.asizeof(d) / 1024:.1f} KiB")
```

### Problema 7: flame graph piatto (nessun hotspot chiaro)

**Sintomi:** il flame graph non ha torri evidenti, il tempo e distribuito uniformemente.

**Interpretazione:** il codice e gia ben bilanciato, oppure il bottleneck e I/O (non CPU). Usa un profiler wall-clock (py-spy con `--idle`) invece di CPU-only.

### Problema 8: il processo non restituisce memoria al sistema operativo

**Sintomi:** dopo `del` e `gc.collect()`, `top` mostra ancora lo stesso RSS.

**Spiegazione:** pymalloc rilascia memoria al sistema solo quando un'intera arena (256 KiB) e vuota. La frammentazione interna puo impedire il rilascio.

```python
# Workaround: usa malloc direttamente per allocazioni grandi
# Oppure usa mmap per dati che devono essere restituiti al sistema

import mmap

# mmap restituisce la memoria al sistema operativo alla chiusura
mm = mmap.mmap(-1, 100 * 1024 * 1024)  # 100 MiB
# ... usa mm ...
mm.close()  # La memoria viene restituita immediatamente
```

### Problema 9: prestazioni degradano nel tempo (long-running process)

**Sintomi:** risposta piu lenta dopo ore/giorni di esecuzione.

**Cause:** frammentazione della memoria, accumulo di oggetti nella gen-2, cache che crescono.

**Diagnosi:**

```python
import gc

stats = gc.get_stats()
for i, gen in enumerate(stats):
    print(f"Gen {i}: collections={gen['collections']}, "
          f"collected={gen['collected']}, "
          f"uncollectable={gen['uncollectable']}")

# Se uncollectable > 0: hai reference cycle con __del__
# Se collected gen-2 e alto: troppi oggetti long-lived
```

### Problema 10: scalene mostra alto tempo in "C/native"

**Sintomi:** la colonna "C" di scalene e predominante, il codice Python puro e trascurabile.

**Interpretazione:** il bottleneck e in una C extension (numpy, pandas, libreria crittografica, ecc.). L'ottimizzazione deve avvenire a quel livello (scelta di API diverse, batch size, parallelismo).

### Problema 11: alta varianza nei benchmark

**Sintomi:** timeit restituisce valori molto diversi tra esecuzioni successive.

**Cause:** GC che interviene, thermal throttling, CPU frequency scaling, processi concorrenti.

```python
import gc
import timeit

# Disabilita GC durante il benchmark
gc.disable()
try:
    risultato = timeit.timeit('sum(range(10000))', number=100000)
finally:
    gc.enable()

# Usa il minimo, non la media
tempi = timeit.repeat('sum(range(10000))', number=10000, repeat=10)
print(f"Min: {min(tempi):.4f}s")
# Il minimo e il valore piu affidabile: rappresenta l'esecuzione
# meno disturbata da fattori esterni
```

### Problema 12: il programma e lento ma cProfile non mostra nulla

**Sintomi:** cProfile mostra tempi bassi per tutte le funzioni, ma il programma impiega molto.

**Causa probabile:** il tempo e speso in I/O (rete, disco, sleep). cProfile misura il CPU time, non il wall time.

**Soluzione:** usa `py-spy record --idle` o pyinstrument (misurano il wall time).

### Problema 13: tracemalloc rallenta troppo il programma

**Sintomi:** con `tracemalloc.start()` il programma diventa 2-5x piu lento.

**Mitigazione:**

```python
import tracemalloc

# Limita il numero di frame nel traceback
tracemalloc.start(1)  # Solo 1 frame (default), minimo overhead

# Campiona invece di tracciare tutto
# Usa tracemalloc solo per sessioni diagnostiche brevi
```

### Problema 14: il garbage collector non raccoglie alcuni cicli

**Sintomi:** `gc.garbage` contiene oggetti dopo `gc.collect()`.

**Causa:** in CPython < 3.4, oggetti con `__del__` in un ciclo non venivano raccolti. In 3.4+, vengono raccolti ma con ordine non deterministico dei finalizer.

```python
import gc

gc.collect()
if gc.garbage:
    print(f"Oggetti non raccoglibili: {len(gc.garbage)}")
    for obj in gc.garbage[:5]:
        print(f"  tipo={type(obj).__name__}, id={id(obj)}")
    # Pulizia manuale
    gc.garbage.clear()
```

### Problema 15: uso di memoria elevato con multiprocessing

**Sintomi:** ogni processo worker duplica i dati del processo padre.

**Soluzione:**

```python
import multiprocessing as mp

# Usa shared memory (Python 3.8+)
from multiprocessing import shared_memory

# Crea un blocco di memoria condivisa
shm = shared_memory.SharedMemory(create=True, size=1024 * 1024)

# I worker accedono agli stessi dati senza copiarli
# shm_name = shm.name  # Passa il nome ai worker

# Oppure usa fork (Linux) con gc.freeze()
import gc
gc.collect()
gc.freeze()  # Previene copy-on-write inutile dopo il fork
```

### Problema 16: pandas DataFrame consuma troppa memoria

**Sintomi:** un CSV da 500 MiB genera un DataFrame da 2+ GiB.

**Soluzioni:**

```python
# 1. Specifica i tipi espliciti
import pandas as pd

dtypes = {
    'id': 'int32',           # Invece di int64
    'nome': 'category',       # Invece di object/str
    'valore': 'float32',      # Invece di float64
    'flag': 'bool',           # Invece di object
}
df = pd.read_csv('grande.csv', dtype=dtypes)

# 2. Carica solo le colonne necessarie
df = pd.read_csv('grande.csv', usecols=['id', 'valore'])

# 3. Elabora in chunk
for chunk in pd.read_csv('enorme.csv', chunksize=100_000):
    elabora(chunk)
```

---

## FAQ

### 1. Reference counting o garbage collection: quale viene usato?

Entrambi. Il reference counting e il meccanismo primario: dealloca gli oggetti immediatamente quando il contatore raggiunge zero. Il garbage collector generazionale e il meccanismo secondario: si occupa esclusivamente dei reference cycle che il refcounting non riesce a risolvere. Per la stragrande maggioranza degli oggetti (90%+), il reference counting e sufficiente e la deallocazione e immediata e deterministica.

### 2. Posso disabilitare il garbage collector?

Si, con `gc.disable()`. E sicuro se il codice non crea reference cycle (ad esempio, batch processing con tipi semplici). Instagram ha notoriamente disabilitato il GC in produzione con successo. Ma e rischioso per codice generico — se si creano cicli senza GC, si ha un memory leak. Regola: disabilita solo se capisci esattamente le implicazioni e hai testato il comportamento.

### 3. `__slots__` migliora sempre le prestazioni?

Migliora l'uso di memoria e velocizza leggermente l'accesso agli attributi. Ma non e gratis: perde la flessibilita di `__dict__` (niente attributi dinamici, complicazioni con l'ereditarieta). Usalo quando hai molte istanze (migliaia+) della stessa classe. Per classi con poche istanze, il risparmio e trascurabile.

### 4. Qual e la differenza tra `sys.getsizeof()` e `pympler.asizeof()`?

`sys.getsizeof()` misura la dimensione *shallow* — solo l'oggetto stesso, non i contenuti referenziati. `asizeof()` misura la dimensione *deep* — include ricorsivamente tutti gli oggetti raggiungibili. Per un `dict` con 1000 liste come valori, `sys.getsizeof()` restituisce solo la dimensione della tabella hash del dict, mentre `asizeof()` include anche le 1000 liste e i loro contenuti.

### 5. Quando devo usare `tracemalloc` e quando `memory_profiler`?

`tracemalloc` e built-in, piu preciso (traccia per punto di allocazione) e adatto per la diagnostica programmatica. `memory_profiler` mostra il consumo per riga di codice in un formato leggibile, ideale per l'analisi manuale durante lo sviluppo. Usa `tracemalloc` come primo strumento, poi `memory_profiler` per analisi riga-per-riga di funzioni specifiche.

### 6. Perche il processo Python non restituisce memoria al sistema operativo?

CPython usa pymalloc, che alloca memoria in arene da 256 KiB. La memoria viene restituita al sistema solo quando un'intera arena e completamente vuota. Se anche un singolo blocco di un'arena e in uso, l'intera arena resta allocata. Questa e una forma di frammentazione interna. Per allocazioni grandi (> 512 bytes), la memoria viene gestita direttamente da `malloc()`/`free()` del sistema e viene restituita normalmente.

### 7. Come profilo un'applicazione Django/FastAPI in produzione?

Usa py-spy per il CPU profiling (zero overhead, si aggancia al processo in esecuzione). Per il memory profiling, usa `tracemalloc` con un endpoint diagnostico protetto. Per il continuous profiling, integra Pyroscope. Non usare cProfile in produzione — l'overhead e troppo alto.

### 8. `del x` libera la memoria immediatamente?

`del x` rimuove il *nome* `x` dallo scope e decrementa il reference count dell'oggetto. Se il refcount raggiunge zero, l'oggetto viene deallocato immediatamente (in CPython). Se altri riferimenti esistono, l'oggetto sopravvive. Se l'oggetto e in un reference cycle, servira il GC per raccoglierlo. Anche dopo la deallocazione, la memoria potrebbe non essere restituita al sistema operativo (vedi FAQ #6).

### 9. Qual e l'overhead di memoria di una classe Python vuota?

Un'istanza di una classe vuota con `__dict__` occupa circa 48 bytes (istanza) + 64 bytes (dict vuoto) = 112 bytes su CPython 3.12 a 64 bit. Con `__slots__ = ()`, scende a circa 16 bytes (solo l'header PyObject). Ogni attributo aggiunge 8 bytes (il puntatore) piu la dimensione dell'oggetto referenziato.

### 10. `weakref.ref` funziona con tutti gli oggetti?

No. Non funziona con tipi built-in immutabili come `int`, `str`, `tuple`, `NoneType`, `bool`. Non funziona con `list`, `dict`, `set` di default. Funziona con istanze di classi definite dall'utente. Per le classi con `__slots__`, `__weakref__` deve essere esplicitamente incluso negli slot.

### 11. Come si legge l'output di cProfile?

Le colonne chiave sono: `tottime` (tempo nella funzione sola, senza sotto-funzioni), `cumtime` (tempo totale incluse le sotto-funzioni), `ncalls` (numero di chiamate). Ordina per `cumtime` per trovare le funzioni che hanno piu impatto complessivo. Ordina per `tottime` per trovare dove il CPU lavora effettivamente. Se `ncalls` e molto alto, il problema potrebbe essere che la funzione viene chiamata troppe volte.

### 12. Quali sono i threshold del GC ottimali?

Non esiste una risposta universale. I default `(700, 10, 10)` funzionano bene per la maggior parte delle applicazioni. Per bassa latenza, abbassa il threshold gen-0 (es. `(100, 5, 5)`) per avere raccolte piu frequenti ma piu brevi. Per alto throughput batch, alza il threshold (es. `(10000, 20, 20)`) per ridurre l'overhead del GC. Misura sempre l'impatto reale con il tuo workload.

### 13. Posso profilare codice C extension con py-spy?

Si, con il flag `--native`. py-spy mostrera anche i frame delle C extension nel flame graph. Questo e utile per capire se il bottleneck e nel codice Python o nella libreria C sottostante (numpy, pandas, ecc.).

### 14. Perche `gc.collect()` non raccoglie tutti gli oggetti?

`gc.collect()` raccoglie solo gli oggetti coinvolti in reference cycle. Gli oggetti ancora referenziati (refcount > 0) non vengono raccolti — non sono garbage. Inoltre, gli oggetti con `__del__` in cicli possono complicare la raccolta (anche se dal 3.4 vengono gestiti). Controlla `gc.garbage` dopo `gc.collect()` per vedere gli oggetti non raccoglibili.

### 15. Quale profiler devo usare per un progetto nuovo?

Segui questa gerarchia: (1) `cProfile` per una panoramica veloce; (2) `py-spy` per flame graph senza modificare il codice; (3) `line_profiler` per analisi riga-per-riga di funzioni specifiche; (4) `scalene` per profiling simultaneo CPU + memoria + copia; (5) `tracemalloc` per investigare problemi di memoria specifici. Nella maggior parte dei casi, cProfile + tracemalloc coprono l'80% dei bisogni.

### 16. Come evito memory leak nelle closure?

Non catturare variabili che non servono. Se la closure deve accedere a un oggetto grande, passa solo il dato necessario (non l'intero oggetto). Usa `weakref` se la closure deve riferire un oggetto senza impedirne la deallocazione. Evita di creare closure in loop che catturano la variabile del loop (un classico bug Python).

### 17. `copy.deepcopy()` e lento. Alternative?

Se i dati sono serializzabili, `pickle.loads(pickle.dumps(obj))` puo essere piu veloce per strutture grandi. Per dati semplici (dict/list di tipi primitivi), `json.loads(json.dumps(obj))` e un'alternativa. Per dataclass, implementa un metodo `clone()` custom che copi solo i campi necessari. Ma misura prima: spesso `deepcopy` non e il vero bottleneck.

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Arena** | Blocco di 256 KiB allocato dal sistema operativo, suddiviso in pool da pymalloc. |
| **Block** | Unita minima di allocazione in pymalloc (8-512 bytes, multipli di 8). |
| **cProfile** | Profiler deterministico nella standard library. Traccia ogni chiamata a funzione. |
| **Continuous profiling** | Profiling a basso overhead che opera costantemente in produzione. |
| **Deep copy** | Copia ricorsiva di un oggetto e di tutti gli oggetti referenziati (`copy.deepcopy()`). |
| **Deterministic profiler** | Profiler che intercetta ogni chiamata a funzione. Alto overhead ma completo. |
| **Flame graph** | Visualizzazione dell'uso CPU dove la larghezza indica il tempo e l'altezza la profondita dello stack. |
| **Free list** | Cache interna di CPython per riusare la memoria di oggetti deallocati dello stesso tipo. |
| **gc.collect()** | Forza una raccolta manuale del garbage collector generazionale. |
| **gc.freeze()** | Sposta gli oggetti attuali fuori dal tracking del GC (utile pre-fork). |
| **gc.get_stats()** | Restituisce statistiche sulle raccolte per ogni generazione. |
| **gc.set_threshold()** | Configura le soglie di attivazione per le tre generazioni del GC. |
| **Generational GC** | GC con tre generazioni (gen-0, gen-1, gen-2). Raccoglie frequentemente gli oggetti giovani. |
| **Integer caching** | CPython pre-alloca gli interi da -5 a 256 per evitare allocazioni ripetute. |
| **line_profiler** | Profiler che misura il tempo per singola riga di codice. |
| **Mark-and-sweep** | Algoritmo di GC: marca gli oggetti raggiungibili, poi dealloca i non marcati. |
| **memoryview** | Oggetto che espone il buffer protocol per accesso zero-copy ai dati binari. |
| **memory_profiler** | Strumento che misura il consumo di memoria per riga di codice. |
| **ob_refcnt** | Campo di PyObject che mantiene il reference count dell'oggetto. |
| **objgraph** | Libreria per visualizzare il grafo dei riferimenti tra oggetti Python. |
| **Pool** | Pagina di 4 KiB all'interno di un'arena, gestisce blocchi di una sola size class. |
| **py-spy** | Sample profiler scritto in Rust. Si aggancia a processi in esecuzione senza modifiche. |
| **pymalloc** | Allocatore di memoria custom di CPython, ottimizzato per oggetti piccoli (<= 512 bytes). |
| **pympler** | Libreria per misurare la dimensione profonda (ricorsiva) degli oggetti Python. |
| **PyObject** | Struttura C base di tutti gli oggetti Python (contiene refcount e tipo). |
| **Pyroscope** | Piattaforma di continuous profiling per applicazioni in produzione. |
| **Reference counting** | Meccanismo primario di deallocazione: ogni oggetto tiene il conto dei riferimenti. |
| **Reference cycle** | Catena di riferimenti circolari (A -> B -> A). Richiede il GC per essere raccolta. |
| **RSS (Resident Set Size)** | Memoria fisica effettivamente usata dal processo (visibile in `top`/`ps`). |
| **Sample profiler** | Profiler che campiona lo stack a intervalli regolari. Basso overhead. |
| **scalene** | Profiler ibrido che traccia CPU, memoria e operazioni di copia per riga. |
| **Shallow copy** | Copia del container esterno, ma i contenuti sono condivisi (`copy.copy()`). |
| **Size class** | Dimensione fissa dei blocchi in un pool pymalloc (8, 16, 24, ..., 512 bytes). |
| **__slots__** | Attributo di classe che sostituisce `__dict__` con un layout fisso, risparmiando memoria. |
| **snakeviz** | Visualizzatore interattivo nel browser per file .prof di cProfile. |
| **String interning** | Ottimizzazione che condivide un'unica copia delle stringhe identiche in memoria. |
| **tracemalloc** | Modulo standard per tracciare le allocazioni di memoria con traceback. |
| **VSZ (Virtual Size)** | Memoria virtuale totale del processo (include pagine non ancora caricate). |
| **Weak reference** | Riferimento che non incrementa il refcount: l'oggetto puo essere deallocato. |
| **WeakValueDictionary** | Dizionario i cui valori sono weak reference — si auto-pulisce. |

---

## Esercizi

### Esercizio 1 — Profiling CPU con cProfile
Scrivi uno script che genera 100.000 numeri casuali, li ordina, calcola la media e la deviazione standard. Profilalo con cProfile, salva l'output in un file `.prof` e visualizzalo con snakeviz. Identifica la funzione piu costosa.

### Esercizio 2 — Memory leak detection
Crea intenzionalmente un memory leak con un reference cycle tra due classi (`Server` e `Connection`). Usa `objgraph.show_growth()` per rilevarlo, poi correggi il leak usando `weakref`.

### Esercizio 3 — __slots__ benchmark
Crea due versioni di una classe `Particella` (con e senza `__slots__`) con attributi `x`, `y`, `z`, `massa`, `velocita`. Crea 5 milioni di istanze di ciascuna e misura: (a) il tempo di creazione, (b) la memoria totale usata con `tracemalloc`, (c) il tempo di accesso agli attributi.

### Esercizio 4 — Pipeline di generatori
Implementa una pipeline di generatori che elabora un file CSV di 1+ GiB riga per riga: (1) leggi, (2) filtra righe invalide, (3) trasforma i campi, (4) aggrega i risultati. Verifica con `tracemalloc` che il consumo di memoria e costante indipendentemente dalla dimensione del file.

### Esercizio 5 — GC tuning per latenza
Scrivi un server HTTP semplice con `http.server` che gestisce richieste. Misura la latenza P99 con i threshold GC di default. Poi sperimenta con `gc.set_threshold(100, 5, 5)` e `gc.disable()` + raccolta manuale periodica. Confronta i risultati.

### Esercizio 6 — Flame graph analysis
Avvia un'applicazione FastAPI sotto carico (con `wrk` o `ab`) e genera un flame graph con py-spy. Identifica l'hotspot dal flame graph, ottimizza il codice e genera un secondo flame graph per verificare il miglioramento.

### Esercizio 7 — TTL cache vs LRU cache
Implementa una `TTLCache` e confrontala con `functools.lru_cache` in uno scenario con 100.000 chiavi uniche e accesso zipfiano (alcune chiavi molto piu frequenti). Misura hit rate, consumo di memoria e latenza di lookup.

### Esercizio 8 — tracemalloc diagnostico
Scrivi un programma che simula un server long-running (loop principale con sleep). Ogni iterazione: (a) scatta uno snapshot con `tracemalloc`, (b) confronta con lo snapshot precedente, (c) emette un alert se la crescita supera una soglia. Inietta un leak graduale e verifica che il sistema lo rilevi.

---

## Letture consigliate

- **tracemalloc documentation.** https://docs.python.org/3/library/tracemalloc.html
- **gc module documentation.** https://docs.python.org/3/library/gc.html
- **weakref module documentation.** https://docs.python.org/3/library/weakref.html
- **py-spy.** https://github.com/benfred/py-spy
- **scalene.** https://github.com/plasma-umass/scalene
- **memory_profiler.** https://github.com/pythonprofilers/memory_profiler
- **objgraph.** https://mg.pov.lt/objgraph/
- **pympler.** https://github.com/pympler/pympler
- **pyinstrument.** https://github.com/joerick/pyinstrument
- **snakeviz.** https://jiffyclub.github.io/snakeviz/
- **Pyroscope.** https://pyroscope.io/
- **CPython source: obmalloc.c.** https://github.com/python/cpython/blob/main/Objects/obmalloc.c
- **PEP 442: Safe object finalization.** https://peps.python.org/pep-0442/
- **Instagram: dismissing the GC.** https://instagram-engineering.com/dismissing-python-garbage-collection-at-instagram-4dca40b29172

---

> **Nota finale:** la gestione della memoria e il profiling sono competenze che distinguono un programmatore Python competente da uno esperto. L'errore piu comune e ignorare questi aspetti fino a quando un problema si manifesta in produzione. L'approccio corretto e integrare il profiling nel workflow di sviluppo: misurare durante lo sviluppo, monitorare in produzione e intervenire chirurgicamente quando i dati lo giustificano. Python offre un ecosistema di strumenti maturi per ogni livello di analisi — dalla diagnostica rapida con `tracemalloc` al continuous profiling con Pyroscope. La chiave e usare lo strumento giusto al momento giusto e basare ogni decisione su dati misurati, non su intuizioni.
