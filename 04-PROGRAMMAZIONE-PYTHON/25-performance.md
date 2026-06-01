---
corso: Programmazione Python
fase: 5 — Qualità e Manutenzione
modulo: "25"
versione: Python 3.12+
livello: intermedio-avanzato
prerequisiti:
  - completamento moduli 01-04 (fondamenti, OOP, strutture dati, decoratori/generatori)
  - conoscenza base di asyncio (modulo 10)
  - familiarità con pytest (modulo 08)
obiettivi:
  - utilizzare cProfile, line_profiler, py-spy e memory_profiler per individuare colli di bottiglia
  - applicare ottimizzazioni algoritmiche e di strutture dati guidate dai dati di profiling
  - scegliere il modello di concorrenza corretto (threading, multiprocessing, asyncio)
  - utilizzare NumPy, Polars e Numba per l'elaborazione dati ad alte prestazioni
  - scrivere estensioni C con Cython, mypyc o ctypes quando necessario
  - integrare benchmark automatizzati nella CI con pytest-benchmark
tag:
  - performance
  - profiling
  - cprofile
  - numba
  - cython
  - concorrenza
  - ottimizzazione
---

# Performance e Ottimizzazione — Guida Completa

> **Modulo 25** · **Aggiornamento:** 2026-05-24

> **Modulo del corso:** Programmazione Python
> **Prerequisiti:** [01-fondamenti-linguaggio.md](01-fondamenti-linguaggio.md), [03-strutture-dati-avanzate.md](03-strutture-dati-avanzate.md), [10-programmazione-asincrona.md](10-programmazione-asincrona.md)
> **Obiettivi di apprendimento:**
> 1. Utilizzare cProfile, line_profiler, py-spy e memory_profiler per individuare colli di bottiglia
> 2. Applicare ottimizzazioni algoritmiche e di strutture dati guidate dai dati di profiling
> 3. Scegliere il modello di concorrenza corretto (threading, multiprocessing, asyncio)
> 4. Utilizzare NumPy, Polars e Numba per elaborazione dati ad alte prestazioni
> 5. Scrivere estensioni C con Cython, mypyc o ctypes quando necessario
> 6. Integrare benchmark automatizzati nella CI con pytest-benchmark
> **Tempo stimato:** lettura 60 min · lab 120 min
> **Livello:** intermedio-avanzato
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida
1. **Measure first: cProfile, py-spy.**
2. **Avoid premature optimization; readability prima.**
3. **NumPy/Polars per data ops; numba JIT per hotspot.**
4. **Cython/mypyc/Rust extension per ultimate.**


## Indice

1. [Panoramica](#panoramica)
2. [Profiling](#profiling)
3. [Ottimizzazione Strutture Dati](#ottimizzazione-strutture-dati)
4. [Ottimizzazione Codice Python](#ottimizzazione-codice-python)
5. [Concorrenza e Parallelismo](#concorrenza-e-parallelismo)
6. [Estensioni C](#estensioni-c)
7. [Compilazione e Alternative](#compilazione-e-alternative)
8. [Performance per Dominio](#performance-per-dominio)
9. [Best Practices](#best-practices)
10. [Confronto Strumenti di Profiling](#confronto-strumenti-di-profiling)
11. [Python 3.13+ Free-Threaded Mode e JIT Compiler](#python-313-free-threaded-mode-e-jit-compiler)
12. [Cython 3.0 — Approfondimento](#cython-30--approfondimento)
13. [Estensioni Rust con PyO3 e Maturin](#estensioni-rust-con-pyo3-e-maturin)
14. [Numba — Approfondimento Avanzato](#numba--approfondimento-avanzato)
15. [Ottimizzazione della Memoria](#ottimizzazione-della-memoria)
16. [Pattern di Ottimizzazione Algoritmica](#pattern-di-ottimizzazione-algoritmica)
17. [Ottimizzazione I/O-Bound Avanzata](#ottimizzazione-io-bound-avanzata)
18. [Ottimizzazione CPU-Bound Avanzata](#ottimizzazione-cpu-bound-avanzata)
19. [Ottimizzazione delle Stringhe](#ottimizzazione-delle-stringhe)
20. [Selezione Avanzata delle Strutture Dati](#selezione-avanzata-delle-strutture-dati)
21. [Ottimizzazione Query Database da Python](#ottimizzazione-query-database-da-python)
22. [Strategie di Caching Avanzate](#strategie-di-caching-avanzate)

---

## Panoramica

La performance del software e un argomento che genera dibattiti appassionati tra i programmatori. Da un lato, scrivere codice veloce e una competenza fondamentale; dall'altro, ottimizzare prematuramente e una delle trappole piu pericolose nello sviluppo software. Questa guida affronta l'argomento con un approccio sistematico: prima misurare, poi ottimizzare, e solo dove serve davvero.

### "Premature optimization is the root of all evil"

Donald Knuth pronuncio questa celebre frase nel 1974, e rimane attuale a distanza di decenni. Il concetto fondamentale e che l'ottimizzazione prematura — cioe intervenire sulle prestazioni prima di avere dati concreti — produce codice piu complesso, meno leggibile e spesso non piu veloce.

La regola d'oro e semplice: **scrivi prima codice corretto e leggibile, poi misura, poi ottimizza solo i colli di bottiglia reali**. Nella stragrande maggioranza dei casi, il 90% del tempo di esecuzione e concentrato nel 10% del codice (o meno). Ottimizzare il restante 90% del codice non produce benefici percepibili ma degrada la manutenibilita.

Quando ha senso ottimizzare:
- Il software non soddisfa i requisiti di performance stabiliti
- Il profiling ha identificato un collo di bottiglia specifico
- L'operazione viene eseguita milioni di volte (loop interni, hot paths)
- Le risorse del sistema sono vincolate (embedded, serverless con limiti di memoria)

Quando NON ha senso ottimizzare:
- Il codice viene eseguito una sola volta (script di setup, migrazioni)
- La differenza e nell'ordine dei microsecondi e l'operazione avviene raramente
- L'ottimizzazione rende il codice significativamente meno leggibile
- Non hai misurato e stai procedendo per intuizione

### Profile First, Optimize Second

Il flusso di lavoro corretto per l'ottimizzazione segue sempre lo stesso schema:

1. **Definisci obiettivi misurabili** — "La risposta API deve completarsi entro 200ms al 99esimo percentile"
2. **Misura lo stato attuale** — esegui il profiling per avere una baseline
3. **Identifica i colli di bottiglia** — trova dove il tempo viene effettivamente speso
4. **Ottimizza il punto critico** — applica una singola modifica
5. **Misura di nuovo** — verifica che l'ottimizzazione abbia prodotto il miglioramento atteso
6. **Ripeti** — torna al punto 3 finche gli obiettivi non sono raggiunti

### Ripasso della notazione Big-O

La notazione Big-O descrive il comportamento asintotico di un algoritmo, cioe come cresce il tempo di esecuzione al crescere dell'input. Non misura il tempo assoluto, ma l'ordine di grandezza della crescita.

| Notazione | Nome | Esempio |
|-----------|------|---------|
| O(1) | Costante | Accesso a dict per chiave |
| O(log n) | Logaritmico | Ricerca binaria |
| O(n) | Lineare | Ricerca in lista |
| O(n log n) | Linearitmico | Sorting (timsort) |
| O(n^2) | Quadratico | Loop annidati |
| O(2^n) | Esponenziale | Sottoinsiemi di un insieme |
| O(n!) | Fattoriale | Permutazioni |

La scelta dell'algoritmo e della struttura dati corretta e spesso l'ottimizzazione piu significativa che si possa fare. Passare da O(n^2) a O(n log n) ha un impatto enormemente superiore rispetto a qualsiasi micro-ottimizzazione a livello di codice.

---

## Profiling

Il profiling e l'atto di misurare dove il programma spende il proprio tempo e la propria memoria. Senza profiling, ogni ottimizzazione e una congettura. Python offre un ricco ecosistema di strumenti di profiling, ognuno adatto a scenari diversi.

### cProfile

cProfile e il profiler deterministico incluso nella libreria standard di Python. Traccia ogni chiamata a funzione, registrando quante volte viene invocata e quanto tempo impiega. E lo strumento da utilizzare come primo approccio al profiling.

**Esecuzione da riga di comando:**

```bash
# Profiling di uno script completo
python -m cProfile mio_script.py

# Ordinamento per tempo cumulativo
python -m cProfile -s cumtime mio_script.py

# Salvataggio output in un file per analisi successiva
python -m cProfile -o output.prof mio_script.py
```

**Esecuzione programmatica:**

```python
import cProfile
import pstats

def funzione_da_profilare():
    risultato = []
    for i in range(10000):
        risultato.append(i ** 2)
    return sum(risultato)

# Profiling di una singola funzione
profiler = cProfile.Profile()
profiler.enable()
funzione_da_profilare()
profiler.disable()

# Stampa risultati ordinati per tempo cumulativo
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(20)  # prime 20 righe
```

**Interpretazione dell'output:**

L'output di cProfile presenta diverse colonne, ognuna con un significato specifico:

- **ncalls** — numero di chiamate alla funzione. Se appare come `10/3`, significa 10 chiamate totali di cui 3 non ricorsive
- **tottime** — tempo totale speso nella funzione, escluso il tempo delle sotto-funzioni chiamate. Questo valore indica quanto lavoro la funzione stessa compie
- **percall** — tottime diviso ncalls
- **cumtime** — tempo cumulativo speso nella funzione, incluso il tempo di tutte le sotto-funzioni. Questo valore indica l'impatto complessivo della funzione
- **percall** — cumtime diviso ncalls (primitivi)

La differenza tra tottime e cumtime e cruciale. Una funzione con alto cumtime ma basso tottime e semplicemente un coordinatore che delega il lavoro a sotto-funzioni. Il collo di bottiglia reale va cercato nelle funzioni con alto tottime.

**pstats per ordinamento e filtraggio:**

```python
import pstats

# Caricamento da file
stats = pstats.Stats("output.prof")

# Rimuovi percorsi lunghi per output piu leggibile
stats.strip_dirs()

# Ordina per tottime e mostra le prime 10
stats.sort_stats("tottime")
stats.print_stats(10)

# Filtra per nome funzione
stats.print_stats("mio_modulo")

# Mostra chi chiama una funzione specifica
stats.print_callers("funzione_lenta")

# Mostra cosa viene chiamato da una funzione
stats.print_callees("funzione_principale")
```

**snakeviz per la visualizzazione:**

snakeviz e uno strumento di visualizzazione che genera grafici interattivi nel browser a partire dai dati di cProfile. E particolarmente utile per esplorare visivamente la gerarchia delle chiamate.

```bash
pip install snakeviz

# Genera il file di profiling
python -m cProfile -o output.prof mio_script.py

# Apri la visualizzazione nel browser
snakeviz output.prof
```

snakeviz mostra un grafico sunburst o icicle dove le dimensioni dei blocchi sono proporzionali al tempo di esecuzione, rendendo immediatamente visibile dove il tempo viene speso.

### line_profiler

Mentre cProfile opera a livello di funzione, line_profiler misura il tempo di esecuzione di ogni singola riga di codice. E lo strumento ideale quando hai gia identificato la funzione problematica con cProfile e vuoi capire esattamente quale riga causa il rallentamento.

```bash
pip install line_profiler
```

**Utilizzo con il decoratore @profile:**

```python
# file: mio_modulo.py
@profile
def elabora_dati(dati):
    risultati = []
    for elemento in dati:                    # riga 4
        valore = elemento ** 2               # riga 5
        if valore > 1000:                    # riga 6
            risultati.append(valore)         # riga 7
    return sorted(risultati)                 # riga 8
```

```bash
# Esecuzione con kernprof
kernprof -l -v mio_modulo.py
```

L'output mostra per ogni riga: il numero di esecuzioni, il tempo totale, il tempo per esecuzione e la percentuale sul totale. Questo livello di dettaglio permette di individuare esattamente la riga responsabile del rallentamento.

**Analisi riga per riga:**

L'output tipico di line_profiler si presenta cosi:

```
Line #  Hits       Time  Per Hit  % Time  Line Contents
     4  10000    5000.0      0.5    10.0  for elemento in dati:
     5  10000   15000.0      1.5    30.0  valore = elemento ** 2
     6  10000    8000.0      0.8    16.0  if valore > 1000:
     7   5000    4000.0      0.8     8.0  risultati.append(valore)
     8      1   18000.0  18000.0    36.0  return sorted(risultati)
```

In questo esempio, la riga con `sorted()` consuma il 36% del tempo. Sostituire il sorting con un approccio diverso (ad esempio, usare un heap) potrebbe essere l'ottimizzazione piu impattante.

### memory_profiler

memory_profiler traccia il consumo di memoria del programma, riga per riga. E fondamentale quando il problema non e la velocita ma l'uso eccessivo di RAM, tipico quando si elaborano grandi dataset.

```bash
pip install memory_profiler
```

```python
from memory_profiler import profile

@profile
def carica_dati_grandi():
    # Carica tutto in memoria
    dati = [i ** 2 for i in range(1_000_000)]     # ~8 MB
    filtrati = [x for x in dati if x > 500_000]   # ~7 MB aggiuntivi
    return sum(filtrati)
```

```bash
python -m memory_profiler mio_script.py
```

**mprof per grafici nel tempo:**

```bash
# Registra l'uso di memoria nel tempo
mprof run mio_script.py

# Genera il grafico
mprof plot
```

mprof produce un grafico che mostra l'evoluzione della memoria nel tempo, rendendo visibili i picchi di consumo e le eventuali memory leak.

### py-spy

py-spy e un sampling profiler scritto in Rust che si collega a un processo Python in esecuzione senza richiedere modifiche al codice ne rallentare significativamente il programma. E lo strumento ideale per il profiling in ambiente di produzione.

```bash
pip install py-spy
```

**Flame graph:**

```bash
# Genera un flame graph SVG interattivo
py-spy record -o profile.svg -- python mio_script.py

# Collega a un processo Python gia in esecuzione
py-spy record -o profile.svg --pid 12345
```

I flame graph sono una rappresentazione visiva della call stack: ogni riga rappresenta un livello della stack e la larghezza dei blocchi e proporzionale al tempo speso in quella funzione. Le "fiamme" piu larghe in cima sono i colli di bottiglia.

**Visualizzazione top-like:**

```bash
# Modalita interattiva simile a top/htop
py-spy top -- python mio_script.py

# Collega a processo esistente
py-spy top --pid 12345
```

Questa modalita mostra in tempo reale le funzioni che consumano piu CPU, aggiornando la visualizzazione continuamente come il comando `top` di Linux.

**Profiling in produzione:**

py-spy e progettato per l'uso in produzione grazie al suo overhead estremamente basso (tipicamente sotto l'1%). Non richiede di riavviare il processo ne di modificare il codice, e puo collegarsi e scollegarsi dinamicamente.

### timeit

timeit e il modulo della libreria standard per il microbenchmarking — cioe la misurazione precisa di piccoli frammenti di codice. Esegue il codice molte volte e calcola statistiche affidabili, gestendo automaticamente le interferenze del garbage collector.

```bash
# Da riga di comando
python -m timeit "sum(range(1000))"
python -m timeit -s "import math" "math.sqrt(144)"
```

```python
import timeit

# Utilizzo programmatico
tempo = timeit.timeit(
    stmt="sum(range(1000))",
    number=10000
)
print(f"Tempo totale: {tempo:.4f}s")
print(f"Tempo medio: {tempo/10000:.6f}s")

# Con setup
tempo = timeit.timeit(
    stmt="math.sqrt(144)",
    setup="import math",
    number=100000
)

# Confronto tra approcci
tempo_lista = timeit.timeit(
    "[x**2 for x in range(1000)]",
    number=1000
)
tempo_map = timeit.timeit(
    "list(map(lambda x: x**2, range(1000)))",
    number=1000
)
print(f"List comprehension: {tempo_lista:.4f}s")
print(f"map + lambda:       {tempo_map:.4f}s")
```

**Best practice per il microbenchmarking:**

- Esegui sempre un numero sufficiente di ripetizioni per ottenere risultati stabili
- Usa il parametro `setup` per il codice di inizializzazione che non deve essere misurato
- Confronta sempre almeno due approcci per avere un riferimento relativo
- Ricorda che i risultati di timeit su frammenti isolati non sempre riflettono le performance reali in un'applicazione completa
- Evita di trarre conclusioni da differenze inferiori al 10-15%, potrebbero essere rumore statistico

### Benchmark con pytest-benchmark

pytest-benchmark integra il benchmarking nel flusso di testing con pytest, fornendo analisi statistiche rigorose e la possibilita di confrontare le performance tra diverse esecuzioni nel tempo.

```bash
pip install pytest-benchmark
```

```python
# test_performance.py

def algoritmo_v1(dati):
    return sorted(set(dati))

def algoritmo_v2(dati):
    visti = set()
    risultato = []
    for x in dati:
        if x not in visti:
            visti.add(x)
            risultato.append(x)
    return sorted(risultato)

def test_benchmark_v1(benchmark):
    dati = list(range(1000)) * 10
    benchmark(algoritmo_v1, dati)

def test_benchmark_v2(benchmark):
    dati = list(range(1000)) * 10
    benchmark(algoritmo_v2, dati)
```

```bash
# Esecuzione dei benchmark
pytest test_performance.py --benchmark-only

# Salvataggio risultati per confronti futuri
pytest test_performance.py --benchmark-save=baseline

# Confronto con la baseline
pytest test_performance.py --benchmark-compare=0001_baseline
```

pytest-benchmark produce un report dettagliato con min, max, media, deviazione standard e percentili, permettendo confronti statisticamente significativi tra diverse implementazioni.

---

## Ottimizzazione Strutture Dati

La scelta della struttura dati appropriata e spesso l'ottimizzazione con il maggiore impatto. Una struttura dati sbagliata puo trasformare un'operazione O(1) in O(n), causando degradi di performance drammatici su grandi volumi di dati.

### List vs Tuple

Le liste e le tuple sono entrambe sequenze ordinate, ma hanno caratteristiche di performance diverse.

```python
import sys
import timeit

# Memoria: le tuple usano meno memoria
lista = [1, 2, 3, 4, 5]
tupla = (1, 2, 3, 4, 5)
print(f"Lista: {sys.getsizeof(lista)} bytes")   # ~96 bytes
print(f"Tupla: {sys.getsizeof(tupla)} bytes")   # ~80 bytes

# Creazione: le tuple sono piu veloci da creare
timeit.timeit("[1, 2, 3, 4, 5]", number=1_000_000)     # ~0.08s
timeit.timeit("(1, 2, 3, 4, 5)", number=1_000_000)     # ~0.01s

# Accesso: performance essenzialmente identiche
timeit.timeit("x[3]", setup="x = [1,2,3,4,5]", number=10_000_000)
timeit.timeit("x[3]", setup="x = (1,2,3,4,5)", number=10_000_000)
```

Le tuple sono piu efficienti in memoria perche sono immutabili: CPython puo fare ottimizzazioni come il caching di tuple piccole e l'allocazione in blocchi contigui. Usa le tuple quando i dati non devono essere modificati.

### Dict vs defaultdict vs Counter

```python
from collections import defaultdict, Counter

# Conteggio classico con dict — verbose e lento
parole = ["cane", "gatto", "cane", "uccello", "gatto", "cane"]

conteggio = {}
for parola in parole:
    if parola in conteggio:
        conteggio[parola] += 1
    else:
        conteggio[parola] = 1

# defaultdict — piu pulito e leggermente piu veloce
conteggio = defaultdict(int)
for parola in parole:
    conteggio[parola] += 1

# Counter — il piu conciso e ottimizzato per il conteggio
conteggio = Counter(parole)
# Counter ha anche metodi utili come most_common()
print(conteggio.most_common(2))  # [('cane', 3), ('gatto', 2)]
```

Counter e implementato in C in CPython, rendendolo significativamente piu veloce di qualsiasi implementazione manuale per il conteggio di elementi.

### Set per test di appartenenza

Questa e una delle ottimizzazioni piu comuni e impattanti. Verificare se un elemento esiste in un set e O(1) in media, mentre in una lista e O(n).

```python
import timeit

# Preparazione dati
dati_lista = list(range(100_000))
dati_set = set(range(100_000))

# Test di appartenenza: O(n) con lista
timeit.timeit("99999 in dati", globals={"dati": dati_lista}, number=1000)
# ~1.2 secondi

# Test di appartenenza: O(1) con set
timeit.timeit("99999 in dati", globals={"dati": dati_set}, number=1000)
# ~0.00003 secondi

# Impatto pratico: filtrare elementi
def filtra_con_lista(dati, ammessi):
    return [x for x in dati if x in ammessi]  # O(n * m)

def filtra_con_set(dati, ammessi):
    ammessi_set = set(ammessi)
    return [x for x in dati if x in ammessi_set]  # O(n + m)
```

**Regola pratica:** ogni volta che verifichi l'appartenenza in una collezione con piu di qualche decina di elementi, converti la collezione in un set.

### deque per operazioni FIFO/LIFO

```python
from collections import deque
import timeit

# list.insert(0, x) e O(n) — sposta tutti gli elementi
# deque.appendleft(x) e O(1) — operazione in tempo costante

lista = []
coda = deque()

# Inserimento in testa: lista vs deque
timeit.timeit("l.insert(0, 1)", globals={"l": list(range(10000))}, number=10000)
# ~0.5 secondi — O(n) per ogni inserimento

timeit.timeit("d.appendleft(1)", globals={"d": deque(range(10000))}, number=10000)
# ~0.001 secondi — O(1) per ogni inserimento

# deque con dimensione massima — utile per buffer circolari
buffer = deque(maxlen=5)
for i in range(10):
    buffer.append(i)
print(buffer)  # deque([5, 6, 7, 8, 9], maxlen=5)
```

deque e la scelta corretta per code (FIFO), stack (LIFO), e buffer circolari. La lista e invece preferibile quando servono accessi random frequenti per indice.

### heapq per code di priorita

```python
import heapq

# Heap minimo — l'elemento piu piccolo e sempre in cima
numeri = [3, 1, 4, 1, 5, 9, 2, 6]
heapq.heapify(numeri)  # Trasforma in heap in O(n)

# Estrai il minimo in O(log n)
print(heapq.heappop(numeri))  # 1

# Inserisci un elemento in O(log n)
heapq.heappush(numeri, 0)

# I k elementi piu grandi/piccoli
dati = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
print(heapq.nlargest(3, dati))    # [9, 6, 5]
print(heapq.nsmallest(3, dati))   # [1, 1, 2]

# Per k piccolo rispetto a n, nlargest/nsmallest sono O(n log k)
# Molto piu efficienti di sorted(dati)[:k] che e O(n log n)
```

### bisect per liste ordinate

```python
import bisect

# Inserimento mantenendo l'ordine — O(log n) per la ricerca
dati_ordinati = [1, 3, 5, 7, 9, 11, 13]

# Trova la posizione di inserimento
posizione = bisect.bisect_left(dati_ordinati, 6)
print(posizione)  # 3

# Inserisci mantenendo l'ordine
bisect.insort(dati_ordinati, 6)
print(dati_ordinati)  # [1, 3, 5, 6, 7, 9, 11, 13]

# Ricerca binaria manuale con bisect
def ricerca_binaria(lista_ordinata, valore):
    i = bisect.bisect_left(lista_ordinata, valore)
    if i != len(lista_ordinata) and lista_ordinata[i] == valore:
        return i
    return -1
```

### array.array vs list per dati numerici

```python
import array
import sys

# Lista Python: ogni elemento e un oggetto Python completo
lista_numeri = list(range(1_000_000))
print(f"Lista: {sys.getsizeof(lista_numeri) / 1024 / 1024:.1f} MB")
# ~8.0 MB (ogni int e un oggetto da ~28 bytes + puntatore da 8 bytes)

# array.array: memorizza valori grezzi come in C
arr_numeri = array.array("l", range(1_000_000))
print(f"Array: {sys.getsizeof(arr_numeri) / 1024 / 1024:.1f} MB")
# ~7.6 MB (8 bytes per long, senza overhead oggetto)

# Per performance numeriche intensive, numpy e la scelta migliore
import numpy as np
np_numeri = np.arange(1_000_000, dtype=np.int64)
print(f"NumPy: {np_numeri.nbytes / 1024 / 1024:.1f} MB")
# ~7.6 MB, ma con operazioni vettorizzate molto piu veloci
```

### Tabella decisionale per la scelta della struttura dati

| Operazione | Struttura Consigliata | Complessita |
|------------|----------------------|-------------|
| Accesso per indice | list, tuple | O(1) |
| Inserimento/rimozione in coda | list, deque | O(1) |
| Inserimento/rimozione in testa | deque | O(1) |
| Test di appartenenza | set, frozenset | O(1) media |
| Mapping chiave-valore | dict | O(1) media |
| Conteggio elementi | Counter | O(n) creazione, O(1) accesso |
| Ordinamento continuo | heapq, bisect | O(log n) inserimento |
| Dati numerici omogenei | array.array, numpy | O(1) accesso |
| Buffer circolare | deque(maxlen=N) | O(1) tutte le operazioni |
| Coda di priorita | heapq | O(log n) push/pop |

---

## Ottimizzazione Codice Python

### Tecniche Generali

#### Comprehension vs loop espliciti

Le comprehension non sono solo piu concise — sono anche significativamente piu veloci dei loop equivalenti perche il loop interno viene eseguito a livello C nell'interprete.

```python
import timeit

# Loop tradizionale
def quadrati_loop(n):
    risultato = []
    for i in range(n):
        risultato.append(i ** 2)
    return risultato

# List comprehension
def quadrati_comp(n):
    return [i ** 2 for i in range(n)]

# Benchmark
timeit.timeit("quadrati_loop(10000)", globals=globals(), number=1000)   # ~1.8s
timeit.timeit("quadrati_comp(10000)", globals=globals(), number=1000)   # ~1.2s
# La comprehension e circa il 30-40% piu veloce

# Dict comprehension
quadrati_dict = {x: x**2 for x in range(100)}

# Set comprehension
valori_unici = {x % 10 for x in range(1000)}
```

#### Generator expression per grandi volumi di dati

Quando i dati sono troppo grandi per stare in memoria, le generator expression permettono di elaborarli in streaming senza allocare l'intera struttura.

```python
import sys

# List comprehension: alloca tutto in memoria
lista = [x ** 2 for x in range(1_000_000)]
print(f"Lista: {sys.getsizeof(lista)} bytes")  # ~8.4 MB

# Generator expression: usa memoria costante
gen = (x ** 2 for x in range(1_000_000))
print(f"Generator: {sys.getsizeof(gen)} bytes")  # ~200 bytes

# Uso pratico: somma di un milione di quadrati
# NON fare questo (alloca la lista intermedia):
totale = sum([x ** 2 for x in range(1_000_000)])

# Fare questo (streaming, memoria costante):
totale = sum(x ** 2 for x in range(1_000_000))
```

#### Variabili locali vs globali

L'accesso alle variabili locali e significativamente piu veloce in CPython perche vengono memorizzate in un array (LOAD_FAST) anziche in un dizionario (LOAD_GLOBAL).

```python
import timeit
import math

# Accesso globale — lento
def calcolo_globale(n):
    risultato = 0
    for i in range(n):
        risultato += math.sqrt(i)  # lookup globale ad ogni iterazione
    return risultato

# Accesso locale — veloce
def calcolo_locale(n):
    sqrt = math.sqrt  # copia riferimento in variabile locale
    risultato = 0
    for i in range(n):
        risultato += sqrt(i)  # lookup locale, molto piu veloce
    return risultato

# Differenza misurabile su loop stretti
timeit.timeit("calcolo_globale(100000)", globals=globals(), number=100)
timeit.timeit("calcolo_locale(100000)", globals=globals(), number=100)
# Il calcolo locale e circa il 15-20% piu veloce
```

#### Funzioni built-in ottimizzate

Le funzioni built-in di Python (map, filter, sum, any, all, min, max) sono implementate in C e sono quasi sempre piu veloci dei loop equivalenti.

```python
numeri = list(range(1_000_000))

# sum() e implementato in C — molto veloce
totale = sum(numeri)

# any() e all() cortocircuitano (si fermano al primo risultato)
ha_negativi = any(x < 0 for x in numeri)  # si ferma al primo True
tutti_positivi = all(x >= 0 for x in numeri)  # si ferma al primo False

# min() e max() — piu veloci di sorted()[0] e sorted()[-1]
minimo = min(numeri)
massimo = max(numeri)

# map() con funzioni C e piu veloce delle comprehension
# (ma con lambda la differenza svanisce)
import math
radici = list(map(math.sqrt, numeri))  # map + funzione C: veloce
```

#### Concatenazione di stringhe

```python
import timeit

# SBAGLIATO: concatenazione con + in un loop — O(n^2)
def concat_plus(parole):
    risultato = ""
    for parola in parole:
        risultato += parola + " "  # crea una nuova stringa ad ogni iterazione
    return risultato

# CORRETTO: str.join() — O(n)
def concat_join(parole):
    return " ".join(parole)  # alloca una sola volta

parole = ["parola"] * 10000
timeit.timeit("concat_plus(parole)", globals=globals(), number=100)   # ~0.15s
timeit.timeit("concat_join(parole)", globals=globals(), number=100)   # ~0.005s
# join() e circa 30 volte piu veloce
```

#### f-string vs format vs operatore %

```python
nome = "Mario"
eta = 30

# f-string — il piu veloce e leggibile (Python 3.6+)
msg = f"Mi chiamo {nome} e ho {eta} anni"

# str.format() — leggermente piu lento
msg = "Mi chiamo {} e ho {} anni".format(nome, eta)

# operatore % — legacy, performance simili a format
msg = "Mi chiamo %s e ho %d anni" % (nome, eta)

# Le f-string sono circa il 20-30% piu veloci di format()
# perche vengono compilate direttamente nel bytecode
```

#### Evitare creazione di oggetti non necessari

```python
# SBAGLIATO: crea un nuovo set ad ogni iterazione
def verifica_lento(elementi, valori_ammessi):
    for elem in elementi:
        if elem in set(valori_ammessi):  # set creato N volte!
            yield elem

# CORRETTO: crea il set una sola volta
def verifica_veloce(elementi, valori_ammessi):
    ammessi = set(valori_ammessi)  # creato una sola volta
    for elem in elementi:
        if elem in ammessi:
            yield elem
```

#### __slots__ per le classi

Per le classi con molte istanze, `__slots__` riduce drasticamente l'uso di memoria e velocizza l'accesso agli attributi eliminando il dizionario `__dict__` di ogni istanza.

```python
import sys

class PuntoNormale:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PuntoSlots:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

p1 = PuntoNormale(1, 2)
p2 = PuntoSlots(1, 2)

print(f"Normale: {sys.getsizeof(p1)} + {sys.getsizeof(p1.__dict__)} bytes")
# ~48 + ~104 = 152 bytes
print(f"Slots:   {sys.getsizeof(p2)} bytes")
# ~56 bytes — circa il 63% in meno

# Con un milione di istanze, il risparmio e di circa 90 MB
```

### Caching

Il caching permette di evitare il ricalcolo di risultati gia ottenuti, scambiando memoria per velocita. Python offre strumenti built-in eleganti per implementare il caching.

#### functools.lru_cache

```python
from functools import lru_cache
import timeit

# Senza cache: calcolo esponenziale O(2^n)
def fibonacci_lento(n):
    if n < 2:
        return n
    return fibonacci_lento(n - 1) + fibonacci_lento(n - 2)

# Con cache: calcolo lineare O(n)
@lru_cache(maxsize=128)
def fibonacci_veloce(n):
    if n < 2:
        return n
    return fibonacci_veloce(n - 1) + fibonacci_veloce(n - 2)

# fibonacci_lento(35) impiega secondi
# fibonacci_veloce(35) impiega microsecondi

# Statistiche della cache
print(fibonacci_veloce.cache_info())
# CacheInfo(hits=33, misses=36, maxsize=128, currsize=36)

# Svuotamento della cache
fibonacci_veloce.cache_clear()
```

#### functools.cache (Python 3.9+)

```python
from functools import cache

# cache e equivalente a lru_cache(maxsize=None)
# Non ha limite di dimensione — la cache cresce indefinitamente
@cache
def fattoriale(n):
    return n * fattoriale(n - 1) if n else 1
```

#### Strategie di caching personalizzate

```python
import time
from functools import wraps

# Cache con scadenza temporale (TTL)
def cache_con_ttl(ttl_secondi=60):
    def decoratore(func):
        _cache = {}

        @wraps(func)
        def wrapper(*args):
            ora = time.time()
            if args in _cache:
                risultato, timestamp = _cache[args]
                if ora - timestamp < ttl_secondi:
                    return risultato
            risultato = func(*args)
            _cache[args] = (risultato, ora)
            return risultato

        wrapper.cache_clear = lambda: _cache.clear()
        return wrapper
    return decoratore

@cache_con_ttl(ttl_secondi=300)
def dati_da_api(endpoint):
    # Simulazione chiamata costosa
    return {"dati": "risultato"}
```

#### Invalidazione della cache

L'invalidazione della cache e notoriamente uno dei problemi piu difficili in informatica. Strategie comuni:

- **TTL (Time To Live)** — la cache scade dopo un tempo prefissato
- **LRU (Least Recently Used)** — gli elementi meno usati vengono rimossi quando la cache e piena
- **Invalidazione esplicita** — il codice che modifica i dati invalida la cache corrispondente
- **Versioning** — ogni modifica incrementa una versione, la cache e valida solo per la versione corrente

### Lazy Evaluation

La valutazione lazy ritarda il calcolo fino al momento in cui il risultato e effettivamente necessario, risparmiando tempo e memoria quando non tutti i risultati vengono consumati.

#### Generatori

```python
# Generatore: calcola un valore alla volta
def numeri_primi(limite):
    for num in range(2, limite):
        if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
            yield num

# I primi non vengono calcolati finche non servono
primi = numeri_primi(1_000_000)

# Prendi solo i primi 10
from itertools import islice
primi_dieci = list(islice(primi, 10))
# Ha calcolato solo i primi necessari, non tutti fino a un milione
```

#### itertools

```python
from itertools import chain, islice, groupby, product, combinations, permutations

# chain: concatena iterabili senza creare liste intermedie
tutti = chain(range(1000), range(2000), range(3000))

# islice: slice su iteratori (non carica tutto in memoria)
primi_100 = list(islice(range(1_000_000_000), 100))

# groupby: raggruppa elementi consecutivi
dati = [("A", 1), ("A", 2), ("B", 3), ("B", 4), ("A", 5)]
dati_ordinati = sorted(dati, key=lambda x: x[0])
for chiave, gruppo in groupby(dati_ordinati, key=lambda x: x[0]):
    print(f"{chiave}: {list(gruppo)}")

# product: prodotto cartesiano (evita loop annidati)
for x, y in product(range(10), range(10)):
    pass  # equivale a due for annidati ma piu pulito

# combinations e permutations
list(combinations([1, 2, 3, 4], 2))  # [(1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]
list(permutations([1, 2, 3], 2))     # [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]
```

#### Proprieta lazy con @cached_property

```python
from functools import cached_property

class AnalisiDati:
    def __init__(self, dati):
        self._dati = dati

    @cached_property
    def statistiche(self):
        """Calcolato una sola volta, al primo accesso."""
        print("Calcolo statistiche...")
        return {
            "media": sum(self._dati) / len(self._dati),
            "minimo": min(self._dati),
            "massimo": max(self._dati),
        }

analisi = AnalisiDati(list(range(1_000_000)))
# Le statistiche non sono ancora calcolate
print(analisi.statistiche)  # "Calcolo statistiche..." — calcolato ora
print(analisi.statistiche)  # nessun output — usa il valore cached
```

---

## Concorrenza e Parallelismo

Python offre diversi modelli per l'esecuzione concorrente e parallela, ognuno adatto a scenari specifici. La scelta corretta dipende dalla natura del carico di lavoro.

### threading (I/O-bound)

Il modulo threading crea thread all'interno dello stesso processo. A causa del GIL (Global Interpreter Lock), i thread Python non possono eseguire bytecode Python in parallelo, ma sono efficaci per operazioni I/O-bound perche il GIL viene rilasciato durante le operazioni di I/O.

```python
import threading
import requests
import time

urls = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
]

# Sequenziale: ~4 secondi
def scarica_sequenziale():
    return [requests.get(url) for url in urls]

# Con threading: ~1 secondo
def scarica_con_thread():
    risultati = [None] * len(urls)

    def scarica(indice, url):
        risultati[indice] = requests.get(url)

    threads = [
        threading.Thread(target=scarica, args=(i, url))
        for i, url in enumerate(urls)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return risultati
```

### multiprocessing (CPU-bound)

Il modulo multiprocessing crea processi separati, ognuno con il proprio interprete Python e GIL. Questo permette il vero parallelismo su CPU multi-core, ideale per calcoli intensivi.

```python
from multiprocessing import Pool, cpu_count
import math

def calcolo_pesante(n):
    """Funzione CPU-intensive."""
    return sum(math.sqrt(i) for i in range(n))

numeri = [10_000_000] * 8

# Sequenziale
risultati_seq = [calcolo_pesante(n) for n in numeri]

# Parallelo con Pool
with Pool(processes=cpu_count()) as pool:
    risultati_par = pool.map(calcolo_pesante, numeri)

# Su una macchina a 8 core, il tempo si riduce di circa 6-7x
# (il parallelismo non e mai perfetto a causa dell'overhead)
```

### concurrent.futures

concurrent.futures fornisce un'interfaccia di alto livello uniforme per threading e multiprocessing, semplificando il codice e gestendo automaticamente il pool di worker.

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import requests

# ThreadPoolExecutor per I/O-bound
def scarica_pagina(url):
    risposta = requests.get(url)
    return url, risposta.status_code

urls = ["https://example.com"] * 10

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(scarica_pagina, url): url for url in urls}
    for future in as_completed(futures):
        url, status = future.result()
        print(f"{url}: {status}")

# ProcessPoolExecutor per CPU-bound
def elabora_blocco(dati):
    return sum(x ** 2 for x in dati)

blocchi = [list(range(i * 100000, (i + 1) * 100000)) for i in range(8)]

with ProcessPoolExecutor() as executor:
    risultati = list(executor.map(elabora_blocco, blocchi))
    totale = sum(risultati)
```

### asyncio (I/O-bound ad alta concorrenza)

asyncio permette di gestire migliaia di operazioni I/O concorrenti con un singolo thread, usando la programmazione asincrona basata su coroutine. E la scelta ottimale quando la concorrenza e molto alta (migliaia di connessioni di rete simultanee).

```python
import asyncio
import aiohttp

async def scarica_pagina(session, url):
    async with session.get(url) as risposta:
        return await risposta.text()

async def scarica_tutte(urls):
    async with aiohttp.ClientSession() as session:
        task = [scarica_pagina(session, url) for url in urls]
        return await asyncio.gather(*task)

# Gestisce migliaia di richieste concorrenti con risorse minime
urls = [f"https://httpbin.org/get?id={i}" for i in range(100)]
risultati = asyncio.run(scarica_tutte(urls))
```

### Quando usare quale approccio — diagramma decisionale

```
Il tuo lavoro e...

CPU-bound (calcoli matematici, elaborazione dati)?
    ├── Necessita di condivisione di stato complessa?
    │   └── threading + Lock (ma attenzione al GIL)
    ├── Elaborazione indipendente su blocchi di dati?
    │   └── multiprocessing / ProcessPoolExecutor
    └── Calcolo numerico su array?
        └── NumPy/Numba (vettorizzazione)

I/O-bound (rete, file, database)?
    ├── Poche operazioni concorrenti (<100)?
    │   └── threading / ThreadPoolExecutor
    ├── Molte operazioni concorrenti (>100)?
    │   └── asyncio
    └── Mix di I/O e CPU?
        └── asyncio + ProcessPoolExecutor
```

---

## Estensioni C

Quando l'ottimizzazione del codice Python puro non e sufficiente, e possibile scrivere le parti critiche in C o C++ e chiamarle da Python. Questo approccio combina la produttivita di Python con le performance del codice nativo.

### ctypes

ctypes permette di chiamare funzioni da librerie condivise (shared libraries) senza scrivere codice wrapper in C. E incluso nella libreria standard.

```python
import ctypes
import os

# Creazione di una libreria C
# file: calcoli.c
# double somma_array(double* arr, int n) {
#     double somma = 0;
#     for (int i = 0; i < n; i++) somma += arr[i];
#     return somma;
# }

# Compilazione: gcc -shared -o calcoli.so -fPIC calcoli.c

# Caricamento della libreria
lib = ctypes.CDLL("./calcoli.so")

# Definizione dei tipi
lib.somma_array.restype = ctypes.c_double
lib.somma_array.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]

# Creazione dell'array e chiamata
n = 1000000
ArrayType = ctypes.c_double * n
arr = ArrayType(*range(n))
risultato = lib.somma_array(arr, n)
```

### Cython

Cython e un linguaggio che estende Python con dichiarazioni di tipo in stile C. Il codice Cython viene compilato in C e poi in codice macchina nativo, ottenendo performance vicine al C puro mantenendo una sintassi molto simile a Python.

```python
# file: calcoli.pyx
def somma_quadrati_python(n):
    """Versione Python pura — lenta."""
    totale = 0
    for i in range(n):
        totale += i * i
    return totale

def somma_quadrati_cython(int n):
    """Versione Cython con tipi dichiarati — veloce."""
    cdef long long totale = 0
    cdef int i
    for i in range(n):
        totale += i * i
    return totale
```

```python
# file: setup.py
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("calcoli.pyx")
)
```

```bash
# Compilazione
python setup.py build_ext --inplace
```

La versione Cython con tipo dichiarato puo essere 50-100x piu veloce della versione Python pura, perche il compilatore genera un loop in C puro senza l'overhead dell'interprete Python.

### cffi

cffi (C Foreign Function Interface) offre due modalita di utilizzo per interfacciarsi con codice C.

```python
from cffi import FFI

ffi = FFI()

# Modalita ABI — carica una libreria compilata
ffi.cdef("double sqrt(double x);")
lib = ffi.dlopen("libm.so.6")
print(lib.sqrt(144.0))  # 12.0

# Modalita API — compila il codice C direttamente
ffi.cdef("int somma(int a, int b);")
lib = ffi.verify("""
    int somma(int a, int b) {
        return a + b;
    }
""")
print(lib.somma(3, 4))  # 7
```

La modalita API e generalmente preferita perche verifica la correttezza delle dichiarazioni a tempo di compilazione anziche a runtime.

### pybind11

pybind11 e la scelta moderna per creare binding Python da codice C++. Usa le funzionalita del C++11 per generare automaticamente il codice wrapper.

```cpp
// file: modulo.cpp
#include <pybind11/pybind11.h>
#include <cmath>

double somma_quadrati(int n) {
    double totale = 0;
    for (int i = 0; i < n; i++) {
        totale += (double)i * i;
    }
    return totale;
}

PYBIND11_MODULE(modulo, m) {
    m.def("somma_quadrati", &somma_quadrati,
          "Calcola la somma dei quadrati da 0 a n-1");
}
```

```python
# Utilizzo in Python
import modulo
risultato = modulo.somma_quadrati(1_000_000)
```

---

## Compilazione e Alternative

Quando ottimizzare il codice Python non basta, esistono strumenti che compilano Python (o un suo sottoinsieme) in codice macchina nativo, eliminando l'overhead dell'interprete.

### Numba

Numba e un compilatore JIT (Just-In-Time) che traduce funzioni Python numeriche in codice macchina nativo usando LLVM. E particolarmente efficace per il calcolo numerico e scientifico.

```python
from numba import jit, njit
import numpy as np

# @jit — compila la funzione alla prima chiamata
@jit(nopython=True)
def somma_quadrati(n):
    totale = 0.0
    for i in range(n):
        totale += i * i
    return totale

# La prima chiamata e lenta (compilazione), le successive sono veloci
risultato = somma_quadrati(10_000_000)  # Prima chiamata: compilazione
risultato = somma_quadrati(10_000_000)  # Successive: velocita nativa

# @njit e un alias per @jit(nopython=True)
@njit
def elabora_array(arr):
    risultato = np.empty_like(arr)
    for i in range(len(arr)):
        risultato[i] = arr[i] ** 2 + 2 * arr[i] + 1
    return risultato

dati = np.random.random(1_000_000)
risultato = elabora_array(dati)
```

**Accelerazione GPU con @cuda.jit:**

```python
from numba import cuda
import numpy as np

@cuda.jit
def kernel_somma(a, b, risultato):
    i = cuda.grid(1)
    if i < risultato.shape[0]:
        risultato[i] = a[i] + b[i]

n = 1_000_000
a = np.random.random(n).astype(np.float32)
b = np.random.random(n).astype(np.float32)
risultato = np.empty(n, dtype=np.float32)

# Trasferisci i dati sulla GPU
a_device = cuda.to_device(a)
b_device = cuda.to_device(b)
risultato_device = cuda.device_array(n, dtype=np.float32)

# Esegui il kernel
threads_per_block = 256
blocks_per_grid = (n + threads_per_block - 1) // threads_per_block
kernel_somma[blocks_per_grid, threads_per_block](a_device, b_device, risultato_device)

risultato = risultato_device.copy_to_host()
```

### PyPy

PyPy e un interprete Python alternativo dotato di un compilatore JIT che puo rendere il codice Python puro significativamente piu veloce (tipicamente 5-10x, in alcuni casi fino a 100x) senza alcuna modifica al codice.

```bash
# Installazione
# Scarica da https://www.pypy.org/download.html

# Esecuzione
pypy3 mio_script.py

# PyPy e compatibile con la maggior parte del codice Python puro
# ma puo avere problemi con estensioni C (numpy, scipy, ecc.)
# Verifica la compatibilita su https://packages.pypy.org/
```

**Quando usare PyPy:**

- Il codice e Python puro (senza estensioni C critiche)
- Il programma ha loop stretti con molte iterazioni
- Il costo dell'overhead dell'interprete CPython e il collo di bottiglia
- Non si vuole modificare il codice sorgente

**Quando NON usare PyPy:**

- Il progetto dipende pesantemente da estensioni C (numpy, scipy, pandas)
- Il tempo di avvio e critico (PyPy ha un warm-up piu lungo)
- Il programma e gia dominato da I/O

### mypyc

mypyc compila moduli Python annotati con type hint in estensioni C native, sfruttando le informazioni di tipo per generare codice efficiente.

```python
# file: calcoli.py
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b
```

```bash
# Compilazione con mypyc
mypyc calcoli.py

# Il modulo compilato viene usato automaticamente con import
python -c "from calcoli import fibonacci; print(fibonacci(40))"
```

mypyc produce accelerazioni tipiche del 2-5x rispetto a CPython, con il vantaggio di non richiedere modifiche alla sintassi — basta che il codice sia annotato con type hint standard.

---

## Performance per Dominio

### I/O

Le operazioni di I/O sono spesso il collo di bottiglia principale delle applicazioni. Ottimizzare l'I/O puo produrre miglioramenti drammatici.

**Buffered vs unbuffered I/O:**

```python
import io

# I/O bufferizzato (default) — raggruppa le scritture
with open("output.txt", "w", buffering=8192) as f:
    for i in range(100000):
        f.write(f"riga {i}\n")  # scritte raggruppate in blocchi da 8KB

# I/O non bufferizzato — ogni write va al sistema operativo
# Utile solo quando serve sincronizzazione immediata (es. log critici)
with open("output.bin", "wb", buffering=0) as f:
    f.write(b"dato critico")

# Lettura efficiente di file grandi — riga per riga (streaming)
def conta_righe(percorso):
    conteggio = 0
    with open(percorso) as f:
        for riga in f:  # iteratore: carica una riga alla volta
            conteggio += 1
    return conteggio

# NON fare: carica tutto in memoria
# with open(percorso) as f:
#     righe = f.readlines()  # TUTTO in memoria
#     conteggio = len(righe)
```

**mmap per file di grandi dimensioni:**

```python
import mmap

def cerca_in_file_grande(percorso, pattern):
    """Cerca un pattern in un file grande usando mmap."""
    with open(percorso, "rb") as f:
        # mmap mappa il file nella memoria virtuale
        # il sistema operativo carica le pagine on-demand
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            indice = mm.find(pattern.encode())
            if indice != -1:
                # Leggi il contesto intorno alla posizione trovata
                inizio = max(0, indice - 50)
                fine = min(len(mm), indice + 50)
                return mm[inizio:fine].decode(errors="replace")
    return None
```

mmap e particolarmente efficace per file di dimensioni nell'ordine dei gigabyte perche il sistema operativo gestisce il caricamento delle pagine in modo trasparente, senza caricare l'intero file in memoria.

**Async I/O per operazioni di rete:**

```python
import asyncio
import aiofiles

async def elabora_file_asincrono(percorsi):
    """Legge piu file in parallelo con aiofiles."""
    async def leggi_file(percorso):
        async with aiofiles.open(percorso, mode="r") as f:
            return await f.read()

    task = [leggi_file(p) for p in percorsi]
    return await asyncio.gather(*task)
```

### Database

Le operazioni su database sono tra le piu critiche per le performance di un'applicazione. Piccole ottimizzazioni possono avere un impatto enorme.

**Connection pooling:**

```python
from sqlalchemy import create_engine

# SBAGLIATO: nuova connessione per ogni operazione
# Ogni connessione richiede handshake TCP, autenticazione, ecc.

# CORRETTO: pool di connessioni riutilizzabili
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,           # connessioni mantenute nel pool
    max_overflow=20,        # connessioni extra in caso di picco
    pool_timeout=30,        # timeout per ottenere una connessione
    pool_recycle=1800,      # ricicla connessioni ogni 30 minuti
    pool_pre_ping=True,     # verifica che la connessione sia attiva
)
```

**Operazioni batch:**

```python
# SBAGLIATO: un INSERT per ogni record — lentissimo
for utente in utenti:
    cursor.execute(
        "INSERT INTO utenti (nome, email) VALUES (%s, %s)",
        (utente["nome"], utente["email"])
    )

# CORRETTO: batch INSERT — ordini di grandezza piu veloce
cursor.executemany(
    "INSERT INTO utenti (nome, email) VALUES (%s, %s)",
    [(u["nome"], u["email"]) for u in utenti]
)

# ANCORA MEGLIO con PostgreSQL: COPY
import io
buffer = io.StringIO()
for u in utenti:
    buffer.write(f"{u['nome']}\t{u['email']}\n")
buffer.seek(0)
cursor.copy_from(buffer, "utenti", columns=("nome", "email"))
```

**Ottimizzazione delle query:**

```python
# SBAGLIATO: N+1 query problem
ordini = session.query(Ordine).all()
for ordine in ordini:
    print(ordine.cliente.nome)  # una query per ogni ordine!

# CORRETTO: eager loading con joinedload
from sqlalchemy.orm import joinedload

ordini = session.query(Ordine).options(
    joinedload(Ordine.cliente)
).all()
for ordine in ordini:
    print(ordine.cliente.nome)  # nessuna query aggiuntiva

# Seleziona solo le colonne necessarie
nomi = session.query(Utente.nome, Utente.email).all()
# Piu efficiente di session.query(Utente).all() se servono solo nome e email

# Usa EXPLAIN per capire il piano di esecuzione
risultato = session.execute("EXPLAIN ANALYZE SELECT * FROM utenti WHERE email = 'test@example.com'")
```

**ORM vs raw SQL:**

L'ORM offre comodita e sicurezza (protezione da SQL injection, portabilita tra database), ma introduce un overhead. Per le operazioni critiche, il raw SQL puo essere significativamente piu veloce.

```python
# ORM — comodo ma piu lento
risultati = session.query(Utente).filter(Utente.eta > 18).all()

# Raw SQL — piu veloce per query complesse
risultati = session.execute(
    "SELECT * FROM utenti WHERE eta > :eta",
    {"eta": 18}
).fetchall()

# Regola pratica: usa l'ORM per il 95% delle operazioni
# e il raw SQL per il 5% delle query critiche per le performance
```

### Web

Le applicazioni web hanno esigenze specifiche di performance legate alla latenza percepita dall'utente e al throughput del server.

**Response caching:**

```python
from functools import lru_cache
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Cache a livello applicazione
@lru_cache(maxsize=1000)
def get_prodotto_cached(prodotto_id: int):
    # Simula query al database
    return {"id": prodotto_id, "nome": f"Prodotto {prodotto_id}"}

@app.get("/prodotti/{prodotto_id}")
async def get_prodotto(prodotto_id: int):
    return get_prodotto_cached(prodotto_id)

# Cache HTTP con header appropriati
@app.get("/catalogo")
async def get_catalogo():
    catalogo = genera_catalogo()
    return JSONResponse(
        content=catalogo,
        headers={
            "Cache-Control": "public, max-age=3600",  # cache per 1 ora
            "ETag": calcola_etag(catalogo),
        }
    )
```

**Connection pooling per servizi esterni:**

```python
import httpx

# Crea un client con pool di connessioni persistenti
# Riutilizza le connessioni TCP esistenti (evita handshake ripetuti)
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    ),
    timeout=httpx.Timeout(10.0)
)

async def chiama_servizio(endpoint):
    risposta = await client.get(f"https://api.esempio.com/{endpoint}")
    return risposta.json()
```

**Framework asincroni:**

Per applicazioni con alta concorrenza (migliaia di richieste simultanee), i framework asincroni come FastAPI, Starlette e aiohttp offrono throughput significativamente superiore rispetto ai framework sincroni come Flask e Django tradizionale.

```python
# FastAPI: framework asincrono ad alte prestazioni
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/elabora")
async def elabora():
    # Operazioni I/O concorrenti
    risultati = await asyncio.gather(
        chiama_servizio_a(),
        chiama_servizio_b(),
        query_database(),
    )
    return {"risultati": risultati}
```

---

## Best Practices

Le seguenti dieci best practice riassumono i principi fondamentali per scrivere codice Python performante, dall'approccio metodologico alle tecniche specifiche.

**1. Misura prima di ottimizzare.** Non indovinare dove sono i colli di bottiglia. Usa sempre cProfile, line_profiler o py-spy per identificare i punti critici con dati concreti. L'intuizione del programmatore e notoriamente inaffidabile quando si tratta di performance. Il codice che sembra lento spesso non lo e, e viceversa.

**2. Scegli la struttura dati corretta.** La scelta della struttura dati ha un impatto ordini di grandezza superiore a qualsiasi micro-ottimizzazione. Usa set per i test di appartenenza, deque per le code, heapq per le priorita, dict per i lookup. Consultare la tabella Big-O prima di scegliere una struttura dati dovrebbe diventare un'abitudine automatica.

**3. Preferisci le comprehension e le funzioni built-in.** Le list/dict/set comprehension e le funzioni come sum(), any(), all(), min(), max() sono implementate in C e significativamente piu veloci dei loop Python equivalenti. Usale sistematicamente come prima scelta.

**4. Usa i generatori per dati grandi.** Quando elabori dataset che non devono stare interamente in memoria, usa generator expression e itertools invece di costruire liste intermedie. Questo riduce il consumo di memoria da O(n) a O(1) e spesso migliora anche la velocita grazie alla migliore localita di cache.

**5. Applica il caching dove ha senso.** functools.lru_cache e functools.cache possono trasformare un algoritmo esponenziale in uno lineare con una singola riga di codice. Identifica le funzioni pure (stesse input, stesso output) che vengono chiamate ripetutamente con gli stessi argomenti e applica il caching.

**6. Scegli il modello di concorrenza giusto.** Per I/O-bound con poche connessioni usa threading; per I/O-bound con molte connessioni usa asyncio; per CPU-bound usa multiprocessing. Non usare threading per lavoro CPU-intensive (il GIL lo impedisce) e non usare multiprocessing per lavoro I/O-bound (l'overhead dei processi e inutile).

**7. Ottimizza l'I/O prima del codice.** Nella maggior parte delle applicazioni reali, l'I/O (rete, disco, database) domina il tempo di esecuzione. Usa connection pooling, batch operations, query ottimizzate e caching prima di ottimizzare i loop Python. L'impatto e generalmente molto maggiore.

**8. Evita la creazione di oggetti non necessari.** Ogni oggetto Python ha un overhead di almeno 28 bytes e richiede allocazione/deallocazione dal garbage collector. In loop stretti, riusa gli oggetti dove possibile, usa __slots__ per le classi con molte istanze e preferisci le tuple alle liste per dati immutabili.

**9. Considera le alternative a CPython per i casi estremi.** Quando l'ottimizzazione del codice Python non basta, valuta Numba per il calcolo numerico, Cython per il codice critico, PyPy per l'accelerazione generale e ctypes/cffi/pybind11 per integrare codice C/C++ esistente. Ogni strumento ha il suo ambito ideale.

**10. Automatizza il monitoraggio delle performance.** Integra pytest-benchmark nella suite di test per rilevare automaticamente le regressioni di performance. Definisci budget di performance (tempo massimo di risposta, memoria massima) e monitorali in CI/CD. Le regressioni individuate presto sono molto piu facili da correggere di quelle scoperte in produzione.

---

> **Nota finale:** l'ottimizzazione e un processo iterativo e basato sui dati. Resisti alla tentazione di ottimizzare il codice durante la prima stesura. Scrivi codice corretto, leggibile e ben testato. Poi, quando i requisiti di performance non sono soddisfatti, misura, identifica i colli di bottiglia e ottimizza chirurgicamente. Questo approccio disciplinato produce codice che e sia veloce che manutenibile nel tempo.
---

## Confronto Strumenti di Profiling

La scelta dello strumento di profiling giusto dipende dallo scenario specifico. Ogni tool ha punti di forza e limitazioni che lo rendono ideale per determinati contesti e meno adatto per altri. Questa sezione fornisce un confronto sistematico tra i principali strumenti disponibili nell'ecosistema Python, andando oltre i tool gia trattati nelle sezioni precedenti (cProfile, line_profiler, memory_profiler, py-spy, timeit, pytest-benchmark).

### Tabella comparativa dei profiler

| Strumento | Tipo | Misura | Overhead | Produzione | Output |
|-----------|------|--------|----------|------------|--------|
| cProfile | deterministico | CPU (funzione) | medio (10-30%) | no | testo, pstats |
| line_profiler | deterministico | CPU (riga) | alto (200%+) | no | testo |
| memory_profiler | deterministico | RAM (riga) | alto (100%+) | no | testo, grafico |
| py-spy | sampling | CPU (funzione) | basso (<1%) | si | flame graph, top |
| Scalene | sampling | CPU+RAM+GPU (riga) | basso (~35%) | si | HTML, testo |
| Pyinstrument | sampling | wall-clock (call tree) | basso (~5%) | si | HTML, testo, JSON |
| Austin | sampling | CPU+RAM (frame) | basso (<1%) | si | flame graph, speedscope |
| tracemalloc | deterministico | RAM (allocazioni) | medio (10-25%) | no | testo, snapshot |
| yappi | deterministico | CPU/wall (thread-aware) | medio (20-40%) | no | testo, pstats |

### Scalene — profiling CPU, memoria e GPU

Scalene e un profiler di nuova generazione sviluppato all'Universita del Massachusetts Amherst. Si distingue da tutti gli altri profiler Python per la capacita di misurare simultaneamente CPU, memoria e utilizzo GPU a livello di riga, con un overhead contenuto nell'ordine del 35%.

**Installazione e utilizzo base:**

```bash
pip install scalene

# Profiling completo di uno script
scalene mio_script.py

# Output HTML per visualizzazione interattiva
scalene --html --- mio_script.py > report.html

# Profiling solo CPU (senza memoria)
scalene --cpu-only mio_script.py

# Profiling di una porzione di codice specifica
scalene --profile-interval 0.01 mio_script.py
```

**Caratteristiche distintive:**

La separazione Python/nativo e la funzionalita piu potente di Scalene. Per ogni riga di codice, il profiler distingue il tempo speso nell'interprete Python dal tempo speso in codice nativo (librerie C/C++ come NumPy). Questa informazione e cruciale perche suggerisce strategie di ottimizzazione completamente diverse: se il tempo e dominato da Python puro, si puo vettorizzare con NumPy; se e gia in codice nativo, serve un approccio architetturale diverso.

```python
# Scalene mostra la suddivisione Python vs nativo per ogni riga
# Esempio di output Scalene:
#
#  Line | Time  | Time   | Time  | Memory  |
#       | Python| native | GPU   |         |
#  -----+-------+--------+-------+---------+
#    15 |  85%  |   5%   |   0%  |  +2.1MB | dati = [calcola(x) for x in range(N)]
#    16 |   2%  |  93%   |   0%  |  +0.0MB | risultato = np.array(dati)
#    17 |   0%  |   3%   |  92%  |  +0.5MB | output = modello_gpu(risultato)
```

**Rilevamento memory leak:**

Scalene identifica automaticamente le righe di codice che causano probabili memory leak analizzando i pattern di allocazione nel tempo. Le righe che allocano memoria continuamente senza deallocazione corrispondente vengono segnalate con un indicatore visivo nel report.

**Suggerimenti AI-powered:**

A partire dalla versione 2.0, Scalene integra un sistema di suggerimenti basato su AI che analizza i risultati del profiling e propone ottimizzazioni specifiche. Supporta diversi provider (OpenAI, Azure, Ollama per modelli locali) e genera proposte concrete come la sostituzione di loop con operazioni vettorizzate o l'uso di strutture dati piu efficienti.

### Pyinstrument — profiling wall-clock con output leggibile

Pyinstrument e un sampling profiler che si concentra sulla leggibilita dell'output. Anziche produrre tabelle dense di dati, genera un albero delle chiamate che mostra chiaramente la gerarchia delle funzioni e il tempo speso in ciascuna.

```bash
pip install pyinstrument
```

**Utilizzo da riga di comando:**

```bash
# Profiling di uno script
pyinstrument mio_script.py

# Output HTML interattivo
pyinstrument -r html -o profile.html mio_script.py

# Output JSON per analisi programmatica
pyinstrument -r json mio_script.py

# Profiling solo per una durata specifica
pyinstrument --interval 0.001 mio_script.py
```

**Utilizzo programmatico — particolarmente utile in web application:**

```python
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# Codice da profilare
risultato = funzione_costosa()

profiler.stop()

# Output come albero delle chiamate
print(profiler.output_text(unicode=True))

# Oppure salva come HTML
with open("profilo.html", "w") as f:
    f.write(profiler.output_html())
```

**Integrazione con framework web:**

```python
# Integrazione con Django — middleware per profiling on-demand
# settings.py: MIDDLEWARE += ["pyinstrument.middleware.ProfilerMiddleware"]
# Aggiungere ?profile alla URL per attivare il profiling

# Integrazione con FastAPI
from pyinstrument import Profiler
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def profiling_middleware(request: Request, call_next):
    if request.query_params.get("profile"):
        profiler = Profiler(interval=0.001, async_mode="enabled")
        profiler.start()
        response = await call_next(request)
        profiler.stop()
        return HTMLResponse(profiler.output_html())
    return await call_next(request)
```

Pyinstrument misura il wall-clock time (tempo reale trascorso), non il tempo CPU. Questo significa che le attese I/O (rete, disco, sleep) appaiono nel profilo. Questo comportamento e intenzionale: mostra dove l'utente effettivamente aspetta, indipendentemente dal fatto che la CPU sia attiva o meno.

### Austin — sampling profiler a zero modifiche

Austin e un sampling profiler sviluppato da P403n1x87 che opera a livello di sistema operativo, senza richiedere alcuna modifica al codice Python ne alcuna libreria aggiuntiva nel processo target. Si collega al processo Python dall'esterno e campiona lo stack frame a intervalli regolari.

```bash
# Installazione (varia per piattaforma)
# Ubuntu/Debian
sudo snap install austin --classic

# macOS
brew install austin

# pip (versione Python)
pip install austin-dist
```

**Utilizzo base:**

```bash
# Profiling di uno script
austin python mio_script.py

# Campionamento a intervalli personalizzati (microsecondi)
austin -i 100 python mio_script.py

# Collegamento a processo esistente
austin -p 12345

# Output in formato flame graph (per FlameGraph o speedscope)
austin -o profile.austin python mio_script.py

# Profiling con memoria
austin -m python mio_script.py
```

**Analisi con austin-tui:**

```bash
# Interfaccia terminale interattiva (simile a htop)
pip install austin-tui
austin-tui python mio_script.py

# Conversione in formato flame graph
pip install austin-python
austin2speedscope profile.austin profile.json
```

Austin e particolarmente adatto per il profiling in produzione perche non richiede il riavvio del processo, non introduce dipendenze nel codice, e ha un overhead quasi nullo. La capacita di collegarsi a processi gia in esecuzione lo rende complementare a py-spy.

### Quando usare quale profiler — guida decisionale

```
Ho bisogno di profilare...

Performance generica di uno script?
    └── Pyinstrument (output leggibile, basso overhead)

Riga specifica in una funzione gia identificata?
    └── line_profiler (precisione massima)

Applicazione in produzione senza riavvio?
    ├── py-spy (flame graph, top-like)
    └── Austin (zero dipendenze, memoria inclusa)

Sia CPU che memoria contemporaneamente?
    └── Scalene (CPU+RAM+GPU, separazione Python/nativo)

Consumo di memoria e leak?
    ├── memory_profiler (analisi riga per riga)
    └── tracemalloc (snapshot e confronto allocazioni)

Web application con profiling on-demand?
    └── Pyinstrument (middleware Django/FastAPI/Flask)

Primo approccio a un codice sconosciuto?
    └── cProfile + snakeviz (incluso in stdlib, nessuna installazione)
```

---

## Python 3.13+ Free-Threaded Mode e JIT Compiler

Python 3.13, rilasciato a ottobre 2024, ha introdotto due cambiamenti fondamentali che rappresentano la piu grande evoluzione architetturale di CPython dalla sua nascita: il supporto sperimentale per l'esecuzione senza Global Interpreter Lock (GIL) e un compilatore JIT sperimentale basato sulla tecnica copy-and-patch. Questi cambiamenti non sono abilitati di default ma segnano l'inizio di una transizione pluriennale che trasformera le performance di Python.

### PEP 703 — Il GIL diventa opzionale

Il Global Interpreter Lock (GIL) e stato fin dalla nascita di CPython il meccanismo che impedisce l'esecuzione parallela di bytecode Python su thread multipli. Sebbene il GIL semplifichi la gestione della memoria e renda thread-safe molte operazioni interne, rappresenta il limite fondamentale delle performance di Python per carichi CPU-bound multi-thread.

PEP 703, proposto da Sam Gross e accettato dal Python Steering Council a luglio 2023, rende il GIL opzionale attraverso un piano in tre fasi:

**Fase 1 — Python 3.13 (ottobre 2024):** il supporto free-threaded e sperimentale. Richiede una build separata di CPython compilata con il flag `--disable-gil`. I binari free-threaded sono identificati dal suffisso "t" (es. `python3.13t`). L'obiettivo di questa fase e permettere all'ecosistema di adattarsi senza rompere la compatibilita.

**Fase 2 — Python 3.14 (ottobre 2025):** il supporto free-threaded diventa ufficialmente supportato (non piu sperimentale). PEP 779, accettato a giugno 2025, definisce i criteri che devono essere soddisfatti per questa transizione: stabilita sufficiente, copertura adeguata delle librerie principali, e performance single-thread comparabili alla build tradizionale.

**Fase 3 — futuro (stimato Python 3.16+):** il free-threaded mode diventa la build di default, con il GIL disponibile come opzione di fallback per la retrocompatibilita.

**Come funziona internamente:**

La rimozione del GIL richiede cambiamenti profondi nel runtime di CPython. Le principali modifiche includono:

- **Reference counting biased:** ogni oggetto ha un contatore di riferimenti che il thread proprietario gestisce senza lock, mentre gli altri thread usano contatori atomici separati. Questo riduce drasticamente la contention rispetto a un semplice contatore atomico condiviso.
- **Immortalizzazione degli oggetti:** gli oggetti ad alta contention (None, True, False, interi piccoli, stringhe interned) vengono marcati come immortali — il loro reference count non viene mai modificato, eliminando la contention su questi oggetti frequentissimi.
- **Lock a grana fine:** le strutture dati interne di CPython (dizionari, liste, ecc.) usano lock individuali anziche il singolo GIL globale.
- **Garbage collector thread-safe:** il garbage collector ciclico e stato riscritto per funzionare in modo thread-safe senza richiedere il GIL.
- **Deferred reference counting:** alcuni decrementi del reference count vengono differiti per ridurre la contention e consentire ottimizzazioni batch.

**Utilizzo pratico del free-threaded mode:**

```bash
# Installazione della build free-threaded (esempio con pyenv)
# Le build free-threaded usano il suffisso "t"
pyenv install 3.13t
pyenv shell 3.13t

# Verifica che il GIL sia disabilitato
python3.13t -c "import sys; print(sys._is_gil_enabled())"
# Output: False

# La variabile d'ambiente PYTHON_GIL permette il controllo runtime
PYTHON_GIL=0 python3.13t mio_script.py  # GIL disabilitato
PYTHON_GIL=1 python3.13t mio_script.py  # GIL abilitato (fallback)
```

**Esempio di vero parallelismo con thread:**

```python
import threading
import time
import sys

def calcolo_pesante(n: int) -> float:
    """Funzione CPU-bound pura."""
    totale = 0.0
    for i in range(n):
        totale += (i ** 0.5) * (i ** 0.3)
    return totale

def benchmark_threading(n_thread: int, lavoro_per_thread: int):
    threads = []
    inizio = time.perf_counter()
    for _ in range(n_thread):
        t = threading.Thread(target=calcolo_pesante, args=(lavoro_per_thread,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    fine = time.perf_counter()
    return fine - inizio

# Con GIL (CPython tradizionale): 4 thread ≈ stesso tempo di 1 thread
# Senza GIL (Python 3.13t): 4 thread ≈ 4x piu veloce su 4 core
print(f"GIL abilitato: {sys._is_gil_enabled()}")
tempo = benchmark_threading(4, 5_000_000)
print(f"4 thread: {tempo:.2f}s")
```

**Impatto sull'ecosistema:**

La transizione al free-threaded Python richiede che le estensioni C vengano adattate. Le estensioni che fanno affidamento implicito sul GIL per la thread-safety devono aggiungere la propria sincronizzazione. Al momento della scrittura (maggio 2026), le librerie principali dell'ecosistema scientifico (NumPy, pandas, scikit-learn) hanno gia iniziato il lavoro di adattamento. Il sito py-free-threading.github.io traccia lo stato di compatibilita delle librerie principali.

**Attenzione:** non usare il free-threaded mode in produzione senza aver verificato che tutte le dipendenze lo supportino. Il fallback con `PYTHON_GIL=1` e disponibile per i casi in cui una libreria causa crash o comportamenti anomali.

### PEP 744 — JIT compiler sperimentale

PEP 744, proposto da Brandt Bucher e Savannah Ostrowski nell'aprile 2024, introduce un compilatore JIT sperimentale in CPython basato sulla tecnica **copy-and-patch**. Questo JIT non mira a competere con i JIT sofisticati di PyPy o Java HotSpot, ma piuttosto a fornire un'infrastruttura su cui costruire ottimizzazioni future incrementali.

**Come funziona il copy-and-patch JIT:**

Il processo di compilazione avviene in due fasi distinte:

1. **Build time:** LLVM compila ciascuna micro-operazione (uop) dell'interprete specializzato di CPython in un blob di codice macchina nativo. Questi blob sono dei template precompilati per ogni architettura target (x86-64, ARM64).

2. **Runtime:** quando una sequenza di micro-operazioni viene eseguita frequentemente (hot path), il JIT copia i template precompilati in sequenza e applica delle "patch" per collegare i riferimenti tra un template e l'altro (costanti, puntatori, salti). Il risultato e codice macchina nativo eseguibile direttamente dalla CPU.

Questa tecnica e molto piu semplice di un JIT tradizionale che genera codice IR e lo ottimizza — il copy-and-patch produce codice meno ottimale ma con un costo di compilazione praticamente nullo.

**Stato attuale e performance:**

Al momento della scrittura (maggio 2026), il JIT e ancora sperimentale e non abilitato di default. I benchmark mostrano miglioramenti modesti (1-9% su macro-benchmark) nella versione iniziale, ma l'infrastruttura e progettata per abilitare ottimizzazioni piu aggressive nelle versioni future.

```bash
# Compilazione di CPython con JIT abilitato
# (richiede LLVM 18+ installato)
./configure --enable-experimental-jit
make

# Verifica che il JIT sia attivo
python -c "import sys; print(sys._jit)"
```

**Roadmap futura del JIT:**

Per Python 3.15 e successive, i piani includono: supporto per lo stack unwinding nel JIT (necessario per exception handling efficiente), thread-safety del JIT (integrazione con il free-threaded mode), e ottimizzazioni piu aggressive come l'inlining di funzioni e la rimozione di type check ridondanti.

**Interazione tra JIT e free-threaded mode:**

Il JIT e il free-threaded mode sono sviluppati come funzionalita indipendenti ma complementari. In futuro, la combinazione di entrambi potrebbe produrre accelerazioni significative: il JIT genera codice nativo piu veloce, e il free-threaded mode permette di eseguirlo su core multipli senza la serializzazione del GIL. Tuttavia, rendere il JIT thread-safe e un lavoro in corso che richiede attenzione alla sincronizzazione degli accessi alle strutture dati del JIT stesso.

**Nota sulla sostenibilita del progetto:** Microsoft ha ridotto il supporto al team Faster CPython nel 2025, il che ha rallentato lo sviluppo del JIT. Il progetto continua come effort della comunita Python, ma i tempi della roadmap potrebbero essere influenzati da questa riduzione di risorse.

---

## Cython 3.0 — Approfondimento

La sezione precedente su Cython (in "Estensioni C") ha introdotto le basi della compilazione Cython. Questa sezione approfondisce le funzionalita avanzate introdotte con Cython 3.0 (rilasciato a luglio 2023) e le tecniche per ottenere le massime performance.

### Novita di Cython 3.0

Cython 3.0 rappresenta un salto generazionale rispetto alla serie 0.29.x. I cambiamenti principali sono:

**Sintassi Python 3 di default:** Cython 3.0 adotta la semantica Python 3 per default (divisione, operatore potenza, print, classi). Il codice scritto per Cython 0.29.x puo richiedere adattamenti.

**Pure Python mode esteso:** la maggior parte delle funzionalita Cython e ora accessibile in "pure Python mode", permettendo di scrivere codice che funziona sia come Python puro sia come Cython compilato. Questo si ottiene tramite il modulo `cython` e i decoratori/annotazioni di tipo.

```python
# Pure Python mode — funziona con Python puro E con Cython
import cython

@cython.cfunc
@cython.returns(cython.double)
@cython.locals(n=cython.int, totale=cython.double, i=cython.int)
def somma_quadrati(n: cython.int) -> cython.double:
    totale: cython.double = 0.0
    i: cython.int
    for i in range(n):
        totale += i * i
    return totale
```

**Gestione eccezioni migliorata:** in Cython 3.0, le funzioni C implementate in Cython propagano le eccezioni per default. Nelle versioni precedenti, le eccezioni venivano silenziosamente ignorate se il programmatore dimenticava di aggiungere una dichiarazione `except` nella firma della funzione. Questo cambiamento elimina un'intera classe di bug sottili.

**Supporto NumPy ufunc:** Cython 3.0 permette di creare NumPy ufunc direttamente, trasformando una semplice funzione numerica Cython in una funzione che opera elemento per elemento su array NumPy interi con performance nativa.

**Supporto Limited API:** il supporto preliminare per la Limited API di CPython significa che i moduli compilati con Cython saranno compatibili con versioni future di Python senza ricompilazione. Questo riduce drasticamente il costo di manutenzione delle estensioni.

**Supporto free-threading:** Cython sta aggiungendo progressivamente il supporto per le build free-threaded di Python 3.13+. La documentazione ufficiale traccia lo stato delle funzionalita compatibili.

### Typed memoryview per dati numerici

I typed memoryview sono la funzionalita piu potente di Cython per il calcolo numerico ad alte prestazioni. Forniscono accesso diretto alla memoria degli array NumPy (e di qualsiasi buffer protocol) senza l'overhead dell'interfaccia Python.

```python
# file: elaborazione.pyx
import numpy as np
cimport numpy as cnp

def media_mobile_cython(double[:] dati, int finestra):
    """Media mobile con typed memoryview — prestazioni vicine al C."""
    cdef int n = dati.shape[0]
    cdef int i, j
    cdef double somma
    cdef double[:] risultato = np.empty(n - finestra + 1, dtype=np.float64)

    for i in range(n - finestra + 1):
        somma = 0.0
        for j in range(finestra):
            somma += dati[i + j]
        risultato[i] = somma / finestra

    return np.asarray(risultato)
```

I typed memoryview offrono diversi vantaggi rispetto alla vecchia sintassi `np.ndarray`:

- Supportano qualsiasi oggetto che implementa il buffer protocol, non solo array NumPy
- Permettono lo slicing senza copia dei dati
- Supportano layout di memoria contigui (C-contiguous e Fortran-contiguous)
- Il controllo dei limiti (bounds checking) puo essere disabilitato con `@cython.boundscheck(False)` per le massime performance

```python
# file: matrice.pyx
import cython

@cython.boundscheck(False)
@cython.wraparound(False)
def prodotto_matrice(double[:, :] A, double[:, :] B):
    """Prodotto matrice con ottimizzazioni aggressive."""
    cdef int M = A.shape[0]
    cdef int K = A.shape[1]
    cdef int N = B.shape[1]
    cdef int i, j, k
    cdef double somma

    import numpy as np
    cdef double[:, :] C = np.zeros((M, N), dtype=np.float64)

    for i in range(M):
        for j in range(N):
            somma = 0.0
            for k in range(K):
                somma += A[i, k] * B[k, j]
            C[i, j] = somma

    return np.asarray(C)
```

### Profiling del codice Cython

Cython genera un report HTML che mostra il grado di "ottimizzazione" di ogni riga con una scala di colore: giallo intenso indica che la riga coinvolge molte chiamate all'API C di Python (lenta), bianco indica codice C puro (veloce).

```bash
# Genera il report di annotazione HTML
cython -a modulo.pyx

# Apri modulo.html nel browser per visualizzare
# le righe gialle (lente) e bianche (veloci)
```

Questo strumento e indispensabile per identificare le righe che non vengono ottimizzate dal compilatore Cython e necessitano di dichiarazioni di tipo aggiuntive.

---

## Estensioni Rust con PyO3 e Maturin

Rust sta emergendo come alternativa moderna a C e C++ per scrivere estensioni Python ad alte prestazioni. Il vantaggio fondamentale di Rust rispetto a C e la safety garantita dal compilatore: memory safety senza garbage collector, assenza di data race a compile time, e un sistema di tipi che previene intere classi di bug comuni nelle estensioni C tradizionali.

L'ecosistema Rust-Python si basa su due strumenti principali:

- **PyO3** — il crate Rust che fornisce i binding per l'API C di Python, permettendo di scrivere moduli Python nativi in Rust
- **maturin** — lo strumento di build e packaging che compila il codice Rust, genera il modulo Python e produce wheel distribuibili

### Configurazione del progetto

Un progetto di estensione Rust per Python richiede una struttura standard:

```
mio-modulo-rust/
├── Cargo.toml
├── pyproject.toml
└── src/
    └── lib.rs
```

**Cargo.toml:**

```toml
[package]
name = "mio_modulo"
version = "0.1.0"
edition = "2021"

[lib]
name = "mio_modulo"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
rayon = "1.10"    # per parallelismo (opzionale)
```

**pyproject.toml:**

```toml
[build-system]
requires = ["maturin>=1.8,<2.0"]
build-backend = "maturin"

[project]
name = "mio-modulo"
requires-python = ">=3.9"

[tool.maturin]
features = ["pyo3/extension-module"]
```

### Scrittura di funzioni Rust esposte a Python

```rust
// src/lib.rs
use pyo3::prelude::*;

/// Calcola la somma dei quadrati — versione Rust.
/// Da Python: import mio_modulo; mio_modulo.somma_quadrati(1_000_000)
#[pyfunction]
fn somma_quadrati(n: u64) -> f64 {
    let mut totale: f64 = 0.0;
    for i in 0..n {
        totale += (i as f64) * (i as f64);
    }
    totale
}

/// Filtra elementi maggiori di una soglia.
/// Dimostra la conversione Vec<f64> <-> list Python.
#[pyfunction]
fn filtra_maggiori(dati: Vec<f64>, soglia: f64) -> Vec<f64> {
    dati.into_iter().filter(|&x| x > soglia).collect()
}

/// Conta le occorrenze di una parola in un testo.
#[pyfunction]
fn conta_occorrenze(testo: &str, parola: &str) -> usize {
    testo.matches(parola).count()
}

/// Modulo Python esposto da Rust.
#[pymodule]
fn mio_modulo(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(somma_quadrati, m)?)?;
    m.add_function(wrap_pyfunction!(filtra_maggiori, m)?)?;
    m.add_function(wrap_pyfunction!(conta_occorrenze, m)?)?;
    Ok(())
}
```

### Build e installazione

```bash
# Installazione di maturin
pip install maturin

# Build in modalita sviluppo (installa direttamente nel venv)
maturin develop --release

# Build wheel per distribuzione
maturin build --release

# Il modulo e pronto per l'uso
python -c "import mio_modulo; print(mio_modulo.somma_quadrati(10_000_000))"
```

Il flag `--release` e essenziale: le build debug di Rust sono 10-20x piu lente delle build release. Dimenticare questo flag e la causa piu comune di benchmark deludenti con PyO3.

### Parallelismo con rayon

Il vantaggio piu significativo di Rust rispetto a C per le estensioni Python e la facilita con cui si implementa il parallelismo sicuro grazie al crate rayon. Rayon fornisce parallelismo data-parallel con garanzie di assenza di data race a compile time.

```rust
use pyo3::prelude::*;
use rayon::prelude::*;

/// Calcolo parallelo su array di dati.
/// Rayon distribuisce automaticamente il lavoro sui core disponibili.
/// Il GIL viene rilasciato durante l'esecuzione Rust.
#[pyfunction]
fn elabora_parallelo(py: Python<'_>, dati: Vec<f64>) -> Vec<f64> {
    // py.allow_threads rilascia il GIL per la durata del blocco
    py.allow_threads(|| {
        dati.par_iter()
            .map(|&x| {
                // Calcolo pesante su ogni elemento
                let mut risultato = x;
                for _ in 0..100 {
                    risultato = risultato.sqrt() * risultato.ln().abs();
                }
                risultato
            })
            .collect()
    })
}
```

Il pattern `py.allow_threads(|| { ... })` e fondamentale: rilascia il GIL durante l'esecuzione del codice Rust, permettendo ad altri thread Python di procedere contemporaneamente. Senza questo wrapper, il codice Rust manterrebbe il GIL e annullerebbe il vantaggio del parallelismo.

### Confronto performance Python vs Cython vs Rust (PyO3)

Per un calcolo tipico (somma dei quadrati di 10 milioni di numeri):

| Implementazione | Tempo relativo | Note |
|-----------------|---------------|------|
| Python puro (loop) | 100x (baseline) | ~2.5s |
| NumPy vettorizzato | ~3x | overhead allocazione array |
| Cython con tipi | ~1.5x | vicino al C |
| Rust (PyO3) single-thread | ~1.2x | leggermente piu veloce di Cython |
| Rust (PyO3 + rayon) 8 core | ~0.2x | parallelismo reale |

Le performance di Rust single-thread sono comparabili a Cython. Il vantaggio reale di Rust emerge con il parallelismo (rayon) e la safety: il compilatore Rust impedisce data race e use-after-free a compile time, mentre in C/Cython questi bug si manifestano solo a runtime (se si e fortunati).

### Quando preferire Rust a C/Cython

Scegli Rust (PyO3) quando:

- Il codice richiede parallelismo intensivo (rayon e superiore a OpenMP per ergonomia)
- La sicurezza della memoria e critica (codice che gestisce dati utente, rete, parsing)
- Il progetto deve essere distribuito come wheel cross-platform (maturin genera wheel per tutte le piattaforme)
- Vuoi un ecosistema di dipendenze moderno (crates.io vs header C manuali)

Scegli Cython quando:

- Il progetto ha gia codice Cython o wrapper C esistenti
- Il team ha esperienza C/C++ ma non Rust
- L'estensione e piccola e la curva di apprendimento di Rust non e giustificata
- Serve interoperabilita diretta con librerie C esistenti

---

## Numba — Approfondimento Avanzato

La sezione precedente (in "Compilazione e Alternative") ha introdotto `@jit` e `@njit` per il calcolo numerico base. Questa sezione approfondisce le tecniche avanzate di Numba per ottenere le massime performance.

### @vectorize — creare ufunc personalizzate

Il decoratore `@vectorize` trasforma una funzione scalare in una NumPy ufunc che opera elemento per elemento su array interi, con compilazione nativa e supporto per la parallelizzazione automatica.

```python
from numba import vectorize, float64, int64
import numpy as np

# ufunc che opera su singoli elementi — Numba la applica all'array intero
@vectorize([float64(float64, float64)], target="parallel")
def distanza_euclidea_componente(a, b):
    return (a - b) ** 2

# Utilizzo — opera su array interi senza loop Python
punti_a = np.random.random(10_000_000)
punti_b = np.random.random(10_000_000)
distanze = np.sqrt(distanza_euclidea_componente(punti_a, punti_b))

# Il target "parallel" distribuisce il calcolo su tutti i core
# target "cpu" usa un singolo core
# target "cuda" esegue su GPU NVIDIA
```

### @guvectorize — ufunc generalizzate

Mentre `@vectorize` opera su scalari, `@guvectorize` opera su sotto-array, permettendo operazioni piu complesse come prodotti matrice-vettore, convoluzioni, o aggregazioni su finestre.

```python
from numba import guvectorize, float64
import numpy as np

@guvectorize(
    [(float64[:], float64, float64[:])],
    "(n),()->(n)",  # layout: input array, scalare -> output array
    target="parallel",
)
def normalizza_array(arr, fattore, risultato):
    """Normalizza ogni sotto-array per un fattore."""
    n = arr.shape[0]
    for i in range(n):
        risultato[i] = arr[i] / fattore

# Opera su batch di array
dati = np.random.random((1000, 500))
fattori = np.random.random(1000) + 1.0
normalizzati = normalizza_array(dati, fattori)
```

### parallel=True e prange

Il flag `parallel=True` combinato con `prange` (parallel range) permette di parallelizzare loop espliciti su CPU multi-core:

```python
from numba import njit, prange
import numpy as np

@njit(parallel=True)
def calcolo_parallelo(matrice):
    """Loop parallelizzato esplicitamente con prange."""
    n, m = matrice.shape
    risultato = np.empty(n, dtype=np.float64)

    # prange distribuisce le iterazioni sui core disponibili
    for i in prange(n):
        somma = 0.0
        for j in range(m):
            somma += matrice[i, j] ** 2
        risultato[i] = np.sqrt(somma)

    return risultato

# Benchmark: 4-6x piu veloce di @njit senza parallel su 8 core
matrice = np.random.random((10000, 1000))
norme = calcolo_parallelo(matrice)
```

### Cache della compilazione e AOT

Per evitare il costo della compilazione JIT alla prima esecuzione, Numba supporta il caching su disco e la compilazione Ahead-Of-Time (AOT):

```python
# Cache JIT su disco — la compilazione avviene solo la prima volta
@njit(cache=True)
def funzione_cached(x):
    return x ** 2 + 2 * x + 1

# AOT compilation con @cc
from numba.pycc import CC

cc = CC("modulo_precompilato")

@cc.export("somma_quadrati", "f8(i8)")
def somma_quadrati(n):
    totale = 0.0
    for i in range(n):
        totale += i * i
    return totale

# Genera il modulo compilato
# cc.compile()
# Poi: import modulo_precompilato
```

### Limitazioni di Numba

Numba supporta un sottoinsieme di Python e NumPy. Le funzionalita non supportate in `nopython` mode includono:

- Dizionari (supporto limitato dalla versione 0.43)
- Set (supporto limitato)
- Classi Python generiche (supportate solo le classi `@jitclass`)
- Operazioni su stringhe (supporto parziale)
- Librerie esterne non-NumPy

La regola pratica: se il codice coinvolge prevalentemente loop numerici su array, Numba e eccellente. Se coinvolge strutture dati complesse, manipolazione di stringhe o logica di business, Cython o PyO3 sono scelte migliori.

---

## Ottimizzazione della Memoria

La gestione efficiente della memoria e un aspetto critico delle performance Python che va oltre la velocita di esecuzione. Questa sezione approfondisce le tecniche di riduzione del consumo di memoria, complementando la trattazione di `__slots__` gia presente nella sezione "Ottimizzazione Codice Python".

### String interning in CPython

CPython mantiene un pool interno di stringhe interned — stringhe che vengono allocate una sola volta e condivise tra tutti i riferimenti. Questo meccanismo ottimizza sia la memoria (una sola copia della stringa in RAM) sia la velocita di confronto (il confronto tra stringhe interned si riduce a un confronto di puntatori, O(1) anziche O(n)).

CPython interna automaticamente:

- Stringhe letterali nel codice sorgente che matchano il pattern `[a-zA-Z0-9_]*` (identificatori Python validi)
- Nomi di attributi, nomi di variabili, nomi di moduli
- Chiavi di dizionario che sono stringhe brevi

```python
import sys

# Stringhe interned automaticamente (identificatori)
a = "hello_world"
b = "hello_world"
print(a is b)  # True — stesso oggetto in memoria

# Stringhe NON interned automaticamente (spazi, caratteri speciali)
a = "hello world"
b = "hello world"
print(a is b)  # False in contesti dinamici — copie separate

# Interning manuale per stringhe frequenti
a = sys.intern("hello world")
b = sys.intern("hello world")
print(a is b)  # True — forzato interning

# Caso d'uso pratico: chiavi di dizionario ripetute migliaia di volte
chiavi = [sys.intern(f"campo_{i}") for i in range(100)]
# Risparmia memoria quando le stesse chiavi appaiono in migliaia di record
```

L'interning manuale con `sys.intern()` e utile quando si elaborano dataset con molte stringhe ripetute (es. colonne di un CSV con valori categorici). Il risparmio puo essere significativo: per un dataset con 1 milione di record ognuno con 10 campi stringa, l'interning puo ridurre il consumo di memoria del 60-80%.

### Compact dict di CPython 3.6+

A partire da Python 3.6, CPython usa un'implementazione di dizionario compatta che separa la tabella hash dagli entry effettivi. Questa implementazione:

- Riduce l'uso di memoria del 20-25% rispetto alla vecchia implementazione
- Preserva l'ordine di inserimento (diventato garanzia del linguaggio in Python 3.7)
- Migliora la localita di cache perche le entry sono memorizzate in un array contiguo

```python
import sys

# La struttura interna di un dict compatto:
# 1. Array di indici (int8/int16/int32 a seconda della dimensione)
# 2. Array contiguo di entry (hash, key, value)

d = {"a": 1, "b": 2, "c": 3}
print(sys.getsizeof(d))  # ~232 bytes in CPython 3.12

# Per dati tabulari con chiavi ripetitive, usare chiavi brevi
# risparma memoria sia nell'hash che nella stringa
buono = {"n": "Mario", "e": 30}      # chiavi corte
meno_buono = {"nome": "Mario", "eta": 30}  # chiavi piu lunghe

# Per molti record con le stesse chiavi, considerare namedtuple o dataclass
from collections import namedtuple
Persona = namedtuple("Persona", ["nome", "eta"])
p = Persona("Mario", 30)
print(sys.getsizeof(p))  # ~64 bytes — molto meno di un dict
```

### Generator vs lista — impatto sulla memoria

La scelta tra generatore e lista ha un impatto diretto sulla memoria proporzionale alla dimensione dei dati. Il pattern e gia stato introdotto in "Ottimizzazione Codice Python", ma qui approfondiamo l'analisi con `tracemalloc`.

```python
import tracemalloc

# Misurazione precisa con tracemalloc
tracemalloc.start()

# Approccio lista — allocazione proporzionale a N
snapshot_prima = tracemalloc.take_snapshot()
dati_lista = [x ** 2 for x in range(1_000_000)]
totale_lista = sum(dati_lista)
snapshot_dopo_lista = tracemalloc.take_snapshot()

# Confronto allocazioni
stats = snapshot_dopo_lista.compare_to(snapshot_prima, "lineno")
for stat in stats[:3]:
    print(stat)
# Output tipico: ~8 MB allocati per la lista

tracemalloc.clear_traces()
tracemalloc.start()

# Approccio generatore — memoria costante
snapshot_prima = tracemalloc.take_snapshot()
totale_gen = sum(x ** 2 for x in range(1_000_000))
snapshot_dopo_gen = tracemalloc.take_snapshot()

stats = snapshot_dopo_gen.compare_to(snapshot_prima, "lineno")
for stat in stats[:3]:
    print(stat)
# Output tipico: pochi KB allocati
```

### Pattern per ridurre l'impronta di memoria

**Uso di array.array per dati numerici omogenei** (gia introdotto nella sezione strutture dati, qui il focus e sul risparmio di memoria):

```python
import sys
import array

# Confronto memoria per 100,000 interi
n = 100_000

# Lista Python: ~28 bytes per oggetto int + ~8 bytes per puntatore
lista = list(range(n))
mem_lista = sys.getsizeof(lista) + sum(sys.getsizeof(x) for x in lista)
print(f"Lista: {mem_lista / 1024:.0f} KB")  # ~3,500 KB

# array.array: ~8 bytes per long (senza overhead oggetto)
arr = array.array("l", range(n))
print(f"array: {sys.getsizeof(arr) / 1024:.0f} KB")  # ~781 KB

# numpy.ndarray: ~8 bytes per int64
import numpy as np
nparr = np.arange(n, dtype=np.int64)
print(f"NumPy: {nparr.nbytes / 1024:.0f} KB")  # ~781 KB
```

**Sostituzione di dizionari con namedtuple o dataclass con slots:**

```python
import sys
from typing import NamedTuple
from dataclasses import dataclass

# Dizionario — ~232 bytes per record
record_dict = {"nome": "Mario", "eta": 30, "citta": "Roma"}

# NamedTuple — ~72 bytes per record
class Record(NamedTuple):
    nome: str
    eta: int
    citta: str

record_nt = Record("Mario", 30, "Roma")

# dataclass con slots — ~56 bytes per record (Python 3.10+)
@dataclass(slots=True)
class RecordDC:
    nome: str
    eta: int
    citta: str

record_dc = RecordDC("Mario", 30, "Roma")
# Con 1 milione di record, la differenza e ~170 MB (dict) vs ~56 MB (dataclass slots)
```

---

## Pattern di Ottimizzazione Algoritmica

L'ottimizzazione algoritmica produce miglioramenti ordini di grandezza superiori a qualsiasi micro-ottimizzazione. Questa sezione presenta pattern ricorrenti che si applicano trasversalmente a diversi domini.

### Memoization oltre la ricorsione

Il pattern di memoization (gia introdotto con `lru_cache` per la ricorsione) si applica efficacemente a molti scenari non ricorsivi dove funzioni pure vengono invocate ripetutamente con gli stessi argomenti.

```python
from functools import lru_cache
import re

# Pattern: compilazione regex memoizzata
@lru_cache(maxsize=256)
def compila_pattern(pattern: str) -> re.Pattern:
    """Compila il pattern regex una sola volta per ogni pattern unico."""
    return re.compile(pattern)

# Senza cache: re.compile() viene chiamato ad ogni invocazione
# Con cache: la regex compilata e riutilizzata

# Pattern: risultati di parsing memoizzati
@lru_cache(maxsize=1024)
def parse_indirizzo(indirizzo: str) -> tuple:
    """Parse costoso di un indirizzo — cached per stringhe ripetute."""
    # Simulazione di parsing complesso
    parti = indirizzo.split(",")
    return tuple(p.strip() for p in parti)
```

### Two-pointer technique

La tecnica dei due puntatori riduce la complessita da O(n^2) a O(n) per molti problemi su sequenze ordinate.

```python
def due_somma_ordinata(numeri: list[int], target: int) -> tuple[int, int] | None:
    """Trova due numeri che sommano a target in una lista ordinata.
    O(n) con due puntatori vs O(n^2) con forza bruta."""
    sinistra = 0
    destra = len(numeri) - 1

    while sinistra < destra:
        somma = numeri[sinistra] + numeri[destra]
        if somma == target:
            return (sinistra, destra)
        elif somma < target:
            sinistra += 1
        else:
            destra -= 1

    return None

def rimuovi_duplicati_inplace(numeri: list[int]) -> int:
    """Rimuove duplicati da lista ordinata in-place. O(n) tempo, O(1) spazio."""
    if not numeri:
        return 0
    pos_scrittura = 1
    for i in range(1, len(numeri)):
        if numeri[i] != numeri[i - 1]:
            numeri[pos_scrittura] = numeri[i]
            pos_scrittura += 1
    return pos_scrittura
```

### Sliding window

La finestra scorrevole e un pattern che evita il ricalcolo completo di aggregazioni su sotto-sequenze consecutive.

```python
def massimo_somma_finestra(dati: list[float], k: int) -> float:
    """Trova la somma massima di k elementi consecutivi.
    O(n) con sliding window vs O(n*k) con forza bruta."""
    if len(dati) < k:
        raise ValueError("Dati insufficienti per la finestra")

    # Calcola la somma della prima finestra
    somma_finestra = sum(dati[:k])
    massimo = somma_finestra

    # Scorri la finestra: aggiungi il nuovo elemento, rimuovi il vecchio
    for i in range(k, len(dati)):
        somma_finestra += dati[i] - dati[i - k]
        if somma_finestra > massimo:
            massimo = somma_finestra

    return massimo
```

### Precalcolo e lookup table

Quando una funzione costosa viene chiamata con un dominio finito di input, precalcolare tutti i risultati in una tabella e drammaticamente piu veloce.

```python
import math

# LENTO: calcola sin() ad ogni accesso
def calcola_lento(angoli_gradi: list[int]) -> list[float]:
    return [math.sin(math.radians(a)) for a in angoli_gradi]

# VELOCE: precalcola la tabella una sola volta
_SENO_TABLE = {a: math.sin(math.radians(a)) for a in range(360)}

def calcola_veloce(angoli_gradi: list[int]) -> list[float]:
    return [_SENO_TABLE[a % 360] for a in angoli_gradi]

# Speedup: ~5x per angoli interi, piu il dominio e piccolo piu conviene
```

### Early termination e short-circuit

Interrompere il calcolo non appena il risultato e determinato puo risparmiare enormi quantita di lavoro.

```python
def contiene_anomalia(dati: list[float], soglia: float) -> bool:
    """Termina al primo valore anomalo trovato — O(1) nel caso migliore."""
    return any(abs(x) > soglia for x in dati)
    # any() cortocircuita al primo True

def tutti_validi(record: list[dict]) -> bool:
    """Verifica che tutti i record siano validi — termina al primo invalido."""
    return all(
        record.get("nome") and record.get("email") and "@" in record["email"]
        for record in record
    )
    # all() cortocircuita al primo False

# Pattern: ricerca con ordine ottimizzato
def cerca_in_fonti(query: str) -> str | None:
    """Cerca nella fonte piu veloce per prima."""
    # Cache locale (microsecondi)
    risultato = cache_locale.get(query)
    if risultato:
        return risultato

    # Cache distribuita (millisecondi)
    risultato = redis_cache.get(query)
    if risultato:
        cache_locale[query] = risultato
        return risultato

    # Database (decine di millisecondi)
    risultato = database.query(query)
    if risultato:
        redis_cache.set(query, risultato)
        cache_locale[query] = risultato
        return risultato

    return None
```

---

## Ottimizzazione I/O-Bound Avanzata

La sezione "Concorrenza e Parallelismo" ha introdotto asyncio per l'I/O concorrente. Questa sezione approfondisce le tecniche avanzate per massimizzare le performance I/O-bound.

### uvloop — event loop ad alte prestazioni

uvloop e un event loop drop-in replacement per asyncio, implementato in Cython sopra libuv (la stessa libreria usata da Node.js). I benchmark mostrano un throughput 2-4x superiore rispetto al loop asyncio di default, con riduzioni della latenza di coda fino al 60%.

```python
import asyncio

# Installazione: pip install uvloop

# Metodo 1: sostituzione globale del loop (raccomandato)
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Metodo 2: uvloop.run() (Python 3.12+)
import uvloop

async def main():
    # Il codice asyncio non richiede alcuna modifica
    await asyncio.sleep(0.1)

uvloop.run(main())

# Metodo 3: per framework web, molti lo integrano automaticamente
# uvicorn server.py --loop uvloop
```

uvloop e particolarmente efficace per applicazioni con alto volume di connessioni di rete (web server, API gateway, proxy). Non porta benefici significativi per applicazioni dominate da CPU o da poche operazioni I/O.

### Connection pooling avanzato

Il connection pooling riusa connessioni TCP esistenti anziche stabilirne di nuove per ogni operazione. Questo elimina il costo dell'handshake TCP (e TLS se applicabile), che puo essere nell'ordine dei 10-100ms per connessione.

```python
# Connection pooling per PostgreSQL con asyncpg
import asyncpg

async def setup_pool():
    # Il pool mantiene connessioni pronte per l'uso
    pool = await asyncpg.create_pool(
        dsn="postgresql://user:pass@localhost/db",
        min_size=5,          # connessioni minime mantenute
        max_size=20,         # connessioni massime
        max_inactive_connection_lifetime=300.0,  # timeout inattivita
        command_timeout=30.0,  # timeout per query
    )
    return pool

async def query_con_pool(pool: asyncpg.Pool):
    # Il pool gestisce automaticamente il checkout/checkin
    async with pool.acquire() as conn:
        righe = await conn.fetch("SELECT * FROM utenti WHERE attivo = $1", True)
        return righe

# Connection pooling per HTTP con httpx
import httpx

# Client persistente con pool di connessioni
client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,       # connessioni totali nel pool
        max_keepalive_connections=20,  # connessioni keep-alive
    ),
    timeout=httpx.Timeout(
        connect=5.0,    # timeout connessione
        read=30.0,      # timeout lettura
        write=10.0,     # timeout scrittura
        pool=10.0,      # timeout attesa connessione dal pool
    ),
    http2=True,  # HTTP/2 multiplexing riduce ulteriormente le connessioni
)

# Connection pooling per Redis con redis-py async
import redis.asyncio as aioredis

pool_redis = aioredis.ConnectionPool.from_url(
    "redis://localhost:6379",
    max_connections=50,
    decode_responses=True,
)
redis_client = aioredis.Redis(connection_pool=pool_redis)
```

### Batching e pipelining

Il batching raggruppa operazioni multiple in una singola richiesta di rete, ammortizzando la latenza su molte operazioni.

```python
import asyncio
import asyncpg

async def inserimento_batch(pool: asyncpg.Pool, records: list[tuple]):
    """Inserimento batch — ordini di grandezza piu veloce di INSERT singoli."""
    async with pool.acquire() as conn:
        # copy_records_to_table usa il protocollo COPY di PostgreSQL
        # ~50x piu veloce di INSERT individuali
        await conn.copy_records_to_table(
            "utenti",
            records=records,
            columns=["nome", "email", "eta"],
        )

# Pipelining Redis — invio di comandi multipli senza attendere risposte
async def operazioni_pipeline(redis_client):
    """Pipeline Redis — riduce la latenza di rete da N roundtrip a 1."""
    async with redis_client.pipeline(transaction=False) as pipe:
        for i in range(1000):
            pipe.set(f"chiave:{i}", f"valore:{i}")
            pipe.expire(f"chiave:{i}", 3600)
        risultati = await pipe.execute()
    # 1000 SET + 1000 EXPIRE in ~2ms vs ~2000ms con comandi singoli
```

### Timeout e circuit breaker

In sistemi distribuiti, gestire i timeout e fondamentale per evitare che un servizio lento blocchi l'intera applicazione.

```python
import asyncio

async def chiamata_con_timeout(coro, timeout_secondi: float, fallback=None):
    """Wrapper con timeout — evita attese infinite su servizi non responsivi."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_secondi)
    except asyncio.TimeoutError:
        return fallback

# Pattern circuit breaker semplificato
class CircuitBreaker:
    """Interrompe le chiamate a un servizio dopo troppi fallimenti consecutivi."""

    def __init__(self, soglia_fallimenti: int = 5, tempo_reset: float = 60.0):
        self._fallimenti = 0
        self._soglia = soglia_fallimenti
        self._tempo_reset = tempo_reset
        self._aperto_da: float | None = None

    async def esegui(self, coro):
        import time
        if self._aperto_da is not None:
            if time.monotonic() - self._aperto_da < self._tempo_reset:
                raise RuntimeError("Circuit breaker aperto")
            self._aperto_da = None
            self._fallimenti = 0

        try:
            risultato = await coro
            self._fallimenti = 0
            return risultato
        except Exception:
            self._fallimenti += 1
            if self._fallimenti >= self._soglia:
                self._aperto_da = time.monotonic()
            raise
```

---

## Ottimizzazione CPU-Bound Avanzata

La sezione "Concorrenza e Parallelismo" ha introdotto multiprocessing e ProcessPoolExecutor. Questa sezione approfondisce le tecniche avanzate per massimizzare le performance CPU-bound.

### shared_memory per dati condivisi ad alte prestazioni

Il modulo `multiprocessing.shared_memory` (Python 3.8+) permette a processi multipli di accedere alla stessa regione di memoria senza serializzazione (pickle). Questo elimina il costo della copia dei dati tra processi, che puo essere proibitivo per dataset di grandi dimensioni.

```python
from multiprocessing import shared_memory, Process
import numpy as np

def worker_shared_memory(shm_name: str, shape: tuple, dtype, start: int, end: int):
    """Worker che accede a un array NumPy in shared memory."""
    # Collega alla shared memory esistente (nessuna copia)
    shm = shared_memory.SharedMemory(name=shm_name)
    arr = np.ndarray(shape, dtype=dtype, buffer=shm.buf)

    # Opera direttamente sulla memoria condivisa
    for i in range(start, end):
        arr[i] = arr[i] ** 2 + 1

    shm.close()

def elabora_con_shared_memory():
    """Elaborazione parallela senza copia dei dati tra processi."""
    n = 10_000_000
    dtype = np.float64

    # Crea l'array in shared memory
    shm = shared_memory.SharedMemory(create=True, size=n * np.dtype(dtype).itemsize)
    arr = np.ndarray((n,), dtype=dtype, buffer=shm.buf)
    arr[:] = np.random.random(n)  # popola i dati

    # Distribuisci il lavoro tra processi
    n_workers = 4
    chunk = n // n_workers
    processi = []

    for i in range(n_workers):
        p = Process(
            target=worker_shared_memory,
            args=(shm.name, (n,), dtype, i * chunk, (i + 1) * chunk),
        )
        processi.append(p)
        p.start()

    for p in processi:
        p.join()

    risultato = arr.copy()  # copia prima di deallocare

    # Cleanup obbligatorio
    shm.close()
    shm.unlink()

    return risultato
```

### Ottimizzazione di ProcessPoolExecutor

`ProcessPoolExecutor` supporta parametri di tuning che possono migliorare significativamente le performance in base al tipo di carico.

```python
from concurrent.futures import ProcessPoolExecutor
import os

def elabora_blocco(blocco: list[float]) -> float:
    return sum(x ** 2 for x in blocco)

# Dati da elaborare
dati = [list(range(i * 1000, (i + 1) * 1000)) for i in range(10000)]

# chunksize: numero di task inviati a ciascun worker in blocco
# Per molti task piccoli, un chunksize grande riduce l'overhead IPC
with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
    # chunksize=1 (default): un task per volta → alto overhead IPC
    # chunksize=100: 100 task per volta → overhead ridotto 100x
    risultati = list(executor.map(elabora_blocco, dati, chunksize=100))

# initializer: codice eseguito una volta per worker (setup pesante)
import pickle

def init_worker():
    """Carica il modello ML una sola volta per worker."""
    global _modello
    with open("modello.pkl", "rb") as f:
        _modello = pickle.load(f)

def predici(dati):
    return _modello.predict(dati)

with ProcessPoolExecutor(
    max_workers=4,
    initializer=init_worker,       # eseguito una volta per worker
    max_tasks_per_child=1000,      # riavvia worker ogni 1000 task (previene leak)
) as executor:
    predizioni = list(executor.map(predici, batch_dati))
```

### Dimensionamento del pool di worker

La scelta del numero ottimale di worker dipende dal tipo di carico:

```python
import os

cpu_count = os.cpu_count()  # core fisici + logici (hyperthreading)

# CPU-bound puro: N worker = N core fisici
# L'hyperthreading non aiuta per lavoro CPU-bound
# Su Linux: core fisici = cpu_count // 2 (con HT abilitato)
n_workers_cpu = max(1, cpu_count - 1)  # lascia 1 core per il processo principale

# Mix CPU + I/O: N worker = N core * 1.5-2
n_workers_misto = int(cpu_count * 1.5)

# Regola empirica: misura con diversi valori di max_workers
# e scegli quello che minimizza il tempo totale
```

---

## Ottimizzazione delle Stringhe

Le operazioni su stringhe sono onnipresenti nel software e spesso sottovalutate come fonte di inefficienza. Questa sezione presenta le tecniche piu impattanti per ottimizzare il lavoro con le stringhe in Python.

### Concatenazione efficiente

La regola fondamentale (gia introdotta in "Ottimizzazione Codice Python") e usare `str.join()` anziche `+=` in loop. Qui approfondiamo i casi meno ovvi.

```python
import io

# Per costruzione incrementale di testo complesso, StringIO e piu efficiente
def genera_report_stringio(record: list[dict]) -> str:
    """StringIO per costruzione incrementale — meglio di join() per output complessi."""
    buffer = io.StringIO()
    buffer.write("REPORT\n")
    buffer.write("=" * 40 + "\n")
    for r in record:
        buffer.write(f"Nome: {r['nome']}\n")
        buffer.write(f"Valore: {r['valore']:.2f}\n")
        buffer.write("-" * 20 + "\n")
    return buffer.getvalue()

# Per output binario, BytesIO
def genera_output_binario(dati: list[bytes]) -> bytes:
    buffer = io.BytesIO()
    for chunk in dati:
        buffer.write(chunk)
    return buffer.getvalue()
```

### Ricerca e pattern matching

```python
import re
from functools import lru_cache

# Precompilazione regex — evita ricompilazione ad ogni chiamata
# re.compile() ha un cache interno limitato a 512 pattern,
# ma la precompilazione esplicita e piu chiara e controllabile
PATTERN_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PATTERN_IP = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

def estrai_email(testo: str) -> list[str]:
    return PATTERN_EMAIL.findall(testo)

# Per ricerca semplice di sottostringhe, str.find() e str.count()
# sono piu veloci di regex
def conta_parola_veloce(testo: str, parola: str) -> int:
    return testo.count(parola)  # implementato in C, ~10x piu veloce di regex

# str.startswith() e str.endswith() accettano tuple per match multipli
def classifica_file(nome: str) -> str:
    if nome.endswith((".py", ".pyx", ".pyi")):
        return "python"
    elif nome.endswith((".rs", ".toml")):
        return "rust"
    elif nome.endswith((".c", ".h", ".cpp")):
        return "c/c++"
    return "altro"
```

### Encoding e decoding efficiente

```python
# Per elaborazione di testo in byte (parsing di protocolli, log, ecc.)
# lavorare direttamente con bytes evita il costo di encoding/decoding

def conta_righe_veloce(percorso: str) -> int:
    """Conta righe in modalita binaria — piu veloce di modalita testo."""
    with open(percorso, "rb") as f:
        return sum(1 for _ in f)
    # ~30% piu veloce della lettura in modalita testo
    # perche evita la decodifica UTF-8 di ogni riga

def cerca_pattern_binario(percorso: str, pattern: bytes) -> list[int]:
    """Cerca un pattern in un file binario — evita la decodifica."""
    posizioni = []
    with open(percorso, "rb") as f:
        contenuto = f.read()
        inizio = 0
        while True:
            pos = contenuto.find(pattern, inizio)
            if pos == -1:
                break
            posizioni.append(pos)
            inizio = pos + 1
    return posizioni
```

---

## Selezione Avanzata delle Strutture Dati

La sezione "Ottimizzazione Strutture Dati" ha trattato le strutture fondamentali. Questa sezione approfondisce i casi d'uso avanzati e le situazioni in cui la scelta meno ovvia e quella corretta.

### frozenset per insiemi immutabili

```python
# frozenset e hashabile e puo essere usato come chiave di dizionario
# Utile per caching di risultati basati su combinazioni di parametri
from functools import lru_cache

@lru_cache(maxsize=1024)
def calcola_per_combinazione(parametri: frozenset) -> float:
    """Cache basata su combinazione di parametri (ordine irrilevante)."""
    return sum(parametri) / len(parametri)

# frozenset e leggermente piu efficiente in memoria di set
# e il test di appartenenza rimane O(1)
categorie_valide = frozenset({"A", "B", "C", "D", "E"})
```

### OrderedDict vs dict per LRU manuale

```python
from collections import OrderedDict

class LRUCacheManuale:
    """LRU cache con OrderedDict — utile quando serve accesso alla struttura."""

    def __init__(self, capacita: int):
        self._cache: OrderedDict = OrderedDict()
        self._capacita = capacita

    def get(self, chiave):
        if chiave in self._cache:
            self._cache.move_to_end(chiave)  # O(1) — aggiorna la posizione
            return self._cache[chiave]
        return None

    def put(self, chiave, valore):
        if chiave in self._cache:
            self._cache.move_to_end(chiave)
        self._cache[chiave] = valore
        if len(self._cache) > self._capacita:
            self._cache.popitem(last=False)  # rimuove il meno recente
```

### defaultdict con factory complesse

```python
from collections import defaultdict

# defaultdict con contatori annidati — evita check di esistenza ripetitivi
conteggi_per_categoria = defaultdict(lambda: defaultdict(int))

eventi = [("login", "successo"), ("login", "fallimento"), ("api", "successo")]
for tipo, esito in eventi:
    conteggi_per_categoria[tipo][esito] += 1

# defaultdict con liste — pattern di raggruppamento
indice_invertito = defaultdict(list)
documenti = [
    (1, "python performance ottimizzazione"),
    (2, "python asyncio concorrenza"),
    (3, "rust performance sicurezza"),
]
for doc_id, testo in documenti:
    for parola in testo.split():
        indice_invertito[parola].append(doc_id)
```

### ChainMap per scope annidati

```python
from collections import ChainMap

# ChainMap cerca nelle mappe in ordine — utile per configurazione a livelli
defaults = {"debug": False, "timeout": 30, "retries": 3}
ambiente = {"timeout": 10}
override_utente = {"debug": True}

config = ChainMap(override_utente, ambiente, defaults)
print(config["debug"])    # True (da override_utente)
print(config["timeout"])  # 10 (da ambiente)
print(config["retries"])  # 3 (da defaults)
# Nessuna copia dei dizionari — cerca in cascata
```

---

## Ottimizzazione Query Database da Python

La sezione "Performance per Dominio > Database" ha introdotto connection pooling, batch operations e il problema N+1. Questa sezione approfondisce le tecniche di ottimizzazione delle query dal lato Python.

### Paginazione efficiente con cursori

```python
# SBAGLIATO: OFFSET per paginazione — diventa lento per pagine alte
# "SELECT * FROM ordini ORDER BY id OFFSET 100000 LIMIT 100"
# Il database deve scansionare e scartare 100,000 righe

# CORRETTO: paginazione con cursore (keyset pagination)
async def pagina_cursore(pool, ultimo_id: int = 0, limite: int = 100):
    """Paginazione O(log n) con keyset anziche O(n) con OFFSET."""
    async with pool.acquire() as conn:
        righe = await conn.fetch(
            "SELECT * FROM ordini WHERE id > $1 ORDER BY id LIMIT $2",
            ultimo_id, limite,
        )
        return righe

# Server-side cursor per dataset enormi
async def stream_risultati(pool, query: str):
    """Streaming di risultati senza caricare tutto in memoria."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            async for record in conn.cursor(query):
                yield record
```

### Indici e EXPLAIN ANALYZE

```python
# Wrapper per analisi del piano di esecuzione
async def analizza_query(pool, query: str, *args):
    """Esegue EXPLAIN ANALYZE e restituisce il piano."""
    async with pool.acquire() as conn:
        piano = await conn.fetch(f"EXPLAIN ANALYZE {query}", *args)
        for riga in piano:
            print(riga["QUERY PLAN"])

# Regole pratiche per gli indici:
# 1. Indice su ogni colonna usata in WHERE, JOIN, ORDER BY frequenti
# 2. Indice composto per query con condizioni multiple
# 3. Indice parziale per query che filtrano sempre per una condizione
# 4. Monitorare la dimensione degli indici — indici inutilizzati consumano spazio

# Esempio: indice parziale per utenti attivi (se il 90% e inattivo)
# CREATE INDEX idx_utenti_attivi ON utenti(email) WHERE attivo = true;
```

### Prepared statements

```python
# Prepared statement — il database compila la query una sola volta
async def query_preparata(pool):
    """Prepared statement per query ripetute — elimina il costo di parsing."""
    async with pool.acquire() as conn:
        # Il database compila e ottimizza la query una sola volta
        stmt = await conn.prepare(
            "SELECT * FROM ordini WHERE cliente_id = $1 AND stato = $2"
        )
        # Esecuzioni successive usano il piano precompilato
        for cliente_id in range(1, 1000):
            righe = await stmt.fetch(cliente_id, "completato")
```

### Caching dei risultati delle query

```python
import hashlib
import json

async def query_con_cache(pool, redis_client, query: str, params: tuple,
                          ttl: int = 300) -> list:
    """Cache dei risultati delle query in Redis con TTL."""
    # Genera una chiave cache unica basata su query e parametri
    cache_key = "query:" + hashlib.sha256(
        f"{query}:{params}".encode()
    ).hexdigest()[:16]

    # Cerca in cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Esegui la query
    async with pool.acquire() as conn:
        righe = await conn.fetch(query, *params)
        risultato = [dict(r) for r in righe]

    # Salva in cache con TTL
    await redis_client.setex(cache_key, ttl, json.dumps(risultato, default=str))

    return risultato
```

---

## Strategie di Caching Avanzate

La sezione "Caching" in "Ottimizzazione Codice Python" ha introdotto `lru_cache` e `cache` della libreria standard. Questa sezione approfondisce le strategie di caching per applicazioni di produzione, dove i requisiti vanno oltre il caching in-process.

### Caching a strati

Le applicazioni di produzione tipicamente usano una gerarchia di cache, dalla piu veloce (e costosa per byte) alla piu lenta (ma capiente):

```python
import time
from functools import lru_cache
from typing import Any

class CacheGerarchica:
    """Cache a strati: L1 (in-process) → L2 (Redis) → L3 (database)."""

    def __init__(self, redis_client, db_pool):
        self._redis = redis_client
        self._db = db_pool
        self._l1: dict[str, tuple[Any, float]] = {}
        self._l1_ttl = 60  # 60 secondi per L1

    async def get(self, chiave: str) -> Any | None:
        # L1: in-process dict (microsecondi)
        if chiave in self._l1:
            valore, timestamp = self._l1[chiave]
            if time.monotonic() - timestamp < self._l1_ttl:
                return valore
            del self._l1[chiave]

        # L2: Redis (millisecondi)
        valore = await self._redis.get(chiave)
        if valore is not None:
            self._l1[chiave] = (valore, time.monotonic())
            return valore

        # L3: Database (decine di millisecondi)
        async with self._db.acquire() as conn:
            riga = await conn.fetchrow(
                "SELECT valore FROM cache_tabella WHERE chiave = $1", chiave
            )
            if riga:
                valore = riga["valore"]
                # Popola cache L2 e L1
                await self._redis.setex(chiave, 300, valore)
                self._l1[chiave] = (valore, time.monotonic())
                return valore

        return None
```

### Caching distribuito con Redis

Per applicazioni multi-processo o multi-server, Redis fornisce un cache condiviso con performance eccellenti (~0.1ms per operazione in LAN).

```python
import redis.asyncio as aioredis
import json
import hashlib
from functools import wraps

def redis_cache(redis_client, prefix: str = "cache", ttl: int = 300):
    """Decoratore per caching distribuito con Redis."""
    def decoratore(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Genera chiave cache deterministica
            chiave_dati = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
            chiave = f"{prefix}:{func.__name__}:{hashlib.md5(chiave_dati.encode()).hexdigest()}"

            # Cerca in cache
            risultato_cached = await redis_client.get(chiave)
            if risultato_cached is not None:
                return json.loads(risultato_cached)

            # Esegui la funzione
            risultato = await func(*args, **kwargs)

            # Salva in cache
            await redis_client.setex(chiave, ttl, json.dumps(risultato, default=str))

            return risultato
        return wrapper
    return decoratore

# Utilizzo
pool_redis = aioredis.ConnectionPool.from_url("redis://localhost:6379")
client_redis = aioredis.Redis(connection_pool=pool_redis)

@redis_cache(client_redis, prefix="api", ttl=600)
async def get_dati_costosi(utente_id: int) -> dict:
    """Funzione costosa — risultato cached in Redis per 10 minuti."""
    # ... query complessa al database
    return {"utente_id": utente_id, "dati": "risultato"}
```

### Invalidazione della cache — pattern Write-Through e Write-Behind

L'invalidazione della cache e la sfida piu complessa del caching. I due pattern principali:

```python
# Pattern Write-Through: aggiorna cache e database insieme
async def aggiorna_utente_write_through(pool, redis_client, utente_id: int, dati: dict):
    """Write-Through: il dato e sempre consistente tra cache e database."""
    async with pool.acquire() as conn:
        # Aggiorna il database
        await conn.execute(
            "UPDATE utenti SET nome=$1, email=$2 WHERE id=$3",
            dati["nome"], dati["email"], utente_id,
        )
    # Aggiorna la cache (non invalida — aggiorna)
    await redis_client.setex(
        f"utente:{utente_id}", 300, json.dumps(dati)
    )

# Pattern Cache-Aside (Lazy Loading): invalida e ricarica on-demand
async def aggiorna_utente_cache_aside(pool, redis_client, utente_id: int, dati: dict):
    """Cache-Aside: invalida la cache, verra ricaricata alla prossima lettura."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE utenti SET nome=$1, email=$2 WHERE id=$3",
            dati["nome"], dati["email"], utente_id,
        )
    # Invalida la cache — la prossima lettura ricarichera dal database
    await redis_client.delete(f"utente:{utente_id}")
```

### Cache warming e preloading

```python
async def riscalda_cache(pool, redis_client):
    """Pre-carica i dati piu frequentemente acceduti nella cache all'avvio."""
    async with pool.acquire() as conn:
        # Carica i top 1000 prodotti per visite
        prodotti = await conn.fetch(
            "SELECT * FROM prodotti ORDER BY visite DESC LIMIT 1000"
        )
        pipe = redis_client.pipeline(transaction=False)
        for p in prodotti:
            chiave = f"prodotto:{p['id']}"
            pipe.setex(chiave, 3600, json.dumps(dict(p), default=str))
        await pipe.execute()
        # 1000 prodotti caricati in cache in ~5ms con pipelining
```

### Monitoring del cache hit rate

Il rapporto tra cache hit e cache miss e la metrica fondamentale per valutare l'efficacia di una strategia di caching. Un hit rate sotto il 90% per dati di lettura frequente suggerisce problemi nella strategia di caching (TTL troppo breve, chiavi troppo granulari, o pattern di accesso non adatti al caching).

```python
class CacheMonitor:
    """Monitoraggio del hit rate della cache."""

    def __init__(self):
        self._hits = 0
        self._misses = 0

    def registra_hit(self):
        self._hits += 1

    def registra_miss(self):
        self._misses += 1

    @property
    def hit_rate(self) -> float:
        totale = self._hits + self._misses
        if totale == 0:
            return 0.0
        return self._hits / totale

    def report(self) -> str:
        totale = self._hits + self._misses
        return (
            f"Cache stats: {self._hits} hits, {self._misses} misses, "
            f"hit rate: {self.hit_rate:.1%}, totale: {totale}"
        )
```

---

## Esercizi di Consolidamento

**Esercizio 1 — Profiling base:**
Prendi una funzione che calcola i numeri primi fino a N (crivello di Eratostene vs divisione trial) e profilala con `cProfile`. Identifica il collo di bottiglia, ottimizza e misura il miglioramento. Documenta il prima/dopo con output di `cProfile.run()`.

**Esercizio 2 — Memory profiling:**
Scrivi uno script che carica un file CSV da 100 MB in tre modi diversi: `csv.reader` con lista, `csv.reader` con generatore, e `polars.read_csv`. Misura il consumo di memoria di ciascun approccio con `tracemalloc`. Confronta i risultati in una tabella.

**Esercizio 3 — Concurrency shootout:**
Implementa uno scraper che scarica 50 URL. Confronta tre implementazioni: threading (`concurrent.futures.ThreadPoolExecutor`), asyncio (`aiohttp`), e multiprocessing. Misura il tempo totale e il consumo di risorse. Spiega perche una soluzione e migliore delle altre per questo caso d'uso.

**Esercizio 4 — Numba JIT:**
Prendi una funzione di calcolo numerico CPU-intensive (es. calcolo di Mandelbrot) e applicale `@numba.jit(nopython=True)`. Confronta le performance con l'implementazione Python pura e con una versione NumPy vectorizzata. Presenta i risultati con `pytest-benchmark`.

**Esercizio 5 — CI performance gate:**
Configura `pytest-benchmark` nella CI per una libreria Python. Definisci un benchmark per almeno 3 funzioni critiche. Configura la pipeline per fallire se una funzione regredisce di piu del 20% rispetto alla baseline. Usa `--benchmark-autosave` e `--benchmark-compare`.

---

## Letture e Riferimenti

### Fonti Primarie

- **cProfile — Deterministic Profiling** — https://docs.python.org/3/library/profile.html (consultato: 2026-05-24). Profiler deterministico della libreria standard: API, interpretazione output, `pstats`.

- **tracemalloc — Trace memory allocations** — https://docs.python.org/3/library/tracemalloc.html (consultato: 2026-05-24). Tracciamento allocazioni memoria: snapshot, confronto, top allocators.

- **concurrent.futures** — https://docs.python.org/3/library/concurrent.futures.html (consultato: 2026-05-24). `ThreadPoolExecutor`, `ProcessPoolExecutor`, `Future`, `as_completed`.

- **Numba Documentation** — https://numba.readthedocs.io/ (consultato: 2026-05-24). JIT compiler per Python numerico: `@jit`, `@njit`, GPU, typing.

- **Cython Documentation** — https://cython.readthedocs.io/ (consultato: 2026-05-24). Compilatore Python→C: `cdef`, typed memoryviews, wrapping C/C++.

- **py-spy** — https://github.com/benfred/py-spy (consultato: 2026-05-24). Sampling profiler per Python: flame graph, top, no overhead.

- **scalene** — https://github.com/plasma-umass/scalene (consultato: 2026-05-24). Profiler CPU+memoria+GPU con linee di codice, separazione Python/C.

- **pytest-benchmark** — https://pytest-benchmark.readthedocs.io/ (consultato: 2026-05-24). Plugin pytest per benchmark: statistiche, confronto, CI integration.

### Testi Consigliati

- **"High Performance Python" di Micha Gorelick e Ian Ozsvald (2a ed., O'Reilly)** — Profiling, concurrency, Cython, Numba, GPU computing, cluster computing.

- **"Fluent Python" di Luciano Ramalho (2a ed., O'Reilly)** — Capitoli su concurrency, iteratori, generatori, data model performance.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Strutture dati: complessità, deque, heapq | 03 | [03-strutture-dati-avanzate.md](03-strutture-dati-avanzate.md) |
| Decoratori (caching con lru_cache) | 04 | [04-decoratori-generatori-context-manager.md](04-decoratori-generatori-context-manager.md) |
| Programmazione asincrona (asyncio) | 10 | [10-programmazione-asincrona.md](10-programmazione-asincrona.md) |
| Data processing (pandas, polars, NumPy) | 14 | [14-data-processing.md](14-data-processing.md) |
| Testing (pytest, benchmark) | 08 | [08-testing.md](08-testing.md) |
| Profiling memoria e GC | 33 | [33-profiling-memoria-gc.md](33-profiling-memoria-gc.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Big-O** | Notazione per descrivere la complessità asintotica di un algoritmo (O(1), O(n), O(n²), O(log n)). |
| **branch coverage** | Misura che verifica che ogni ramo condizionale (if/else) sia stato attraversato dai test. |
| **cold start** | Prima esecuzione di una funzione JIT-compiled (Numba) dove il tempo di compilazione domina. |
| **Cython** | Linguaggio che estende Python con dichiarazioni di tipo C per compilare in codice nativo. |
| **flame graph** | Visualizzazione gerarchica del call stack che mostra dove il tempo viene speso nell'esecuzione. |
| **GIL** | Global Interpreter Lock — mutex di CPython che limita il parallelismo dei thread Python. |
| **hot path** | Porzione di codice eseguita molto frequentemente, candidata primaria per l'ottimizzazione. |
| **JIT** | Just-In-Time compilation — compilazione del codice al momento dell'esecuzione (Numba, PyPy). |
| **memoization** | Tecnica di caching dei risultati di funzioni pure per evitare ricalcoli (`functools.lru_cache`). |
| **Numba** | Compilatore JIT per Python numerico che traduce funzioni Python in codice macchina LLVM. |
| **profiling** | Misurazione sistematica delle performance: tempo CPU, allocazioni memoria, chiamate a funzione. |
| **sampling profiler** | Profiler che campiona periodicamente il call stack senza modificare il codice (py-spy, scalene). |
| **vectorization** | Applicazione di operazioni su array interi anziche elemento per elemento (NumPy, Polars). |
