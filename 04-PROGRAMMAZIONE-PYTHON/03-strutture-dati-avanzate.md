---
corso: Programmazione Python
fase: Fondamenti avanzati
versione_python: ">=3.12"
livello: intermedio-avanzato
ultimo_aggiornamento: 2026-05-24
obiettivi:
  - Padroneggiare il modulo collections e ogni suo contenitore specializzato
  - Implementare code di priorita, ricerche binarie e ordinamenti personalizzati con heapq, bisect e sorted
  - Confrontare namedtuple, typing.NamedTuple e dataclass per scegliere in base al contesto
  - Ottimizzare la memoria con __slots__, array, struct, memoryview e frozenset
  - Conoscere strutture specializzate (trie, bloom filter) e sapere quando adottarle
  - Scrivere classi hashable corrette e comprendere il contratto __hash__/__eq__
---

# Strutture Dati Avanzate — Guida Completa

> **Modulo 03** · **Aggiornamento:** 2026-05-23 · **Versione:** Python 3.12+

## Idee guida
1. **collections module: deque, Counter, defaultdict, ChainMap.**
2. **heapq per priority queue.**
3. **bisect per sorted list operations O(log n).**
4. **set/frozenset per membership O(1).**
5. **dataclasses.field offre controllo fine su default_factory, compare, hash e metadata.**
6. **Scegli la struttura in base al profilo di accesso: la complessita asintotica domina sui fattori costanti solo oltre una certa soglia.**
7. **Efficienza di memoria: __slots__, array tipizzati e memoryview riducono il footprint senza sacrificare leggibilita.**


## Mappa concettuale

```
                        ┌──────────────────────────────┐
                        │     Strutture dati Python     │
                        └──────────┬───────────────────┘
               ┌──────────────────┼──────────────────────┐
               ▼                  ▼                      ▼
       ┌───────────┐     ┌───────────────┐      ┌──────────────┐
       │ Sequenze  │     │   Mappature   │      │   Insiemi    │
       └─────┬─────┘     └──────┬────────┘      └──────┬───────┘
             │                  │                      │
   ┌─────┬──┴──┬──────┐  ┌─────┴─────┬──────┐   ┌─────┴──────┐
   │list │deque│array  │  │dict       │Chain │   │set         │
   │tuple│     │struct │  │defaultdict│ Map  │   │frozenset   │
   │named│     │memory │  │OrderedDict│      │   │            │
   │tuple│     │ view  │  │Counter    │      │   │            │
   └─────┘     └───────┘  │UserDict   │      │   └────────────┘
                          └───────────┘      │
                                             │
               ┌─────────────────────────────┼──────────────┐
               ▼                             ▼              ▼
       ┌───────────────┐            ┌────────────┐  ┌───────────────┐
       │  Heap / Code  │            │  Alberi /   │  │  Strutture    │
       │  di priorita  │            │  Grafi      │  │  specializzate│
       │  (heapq,      │            │  (BST,      │  │  (trie, bloom │
       │   queue)      │            │  networkx)  │  │   filter)     │
       └───────────────┘            └────────────┘  └───────────────┘
               │
       ┌───────┴────────┐
       │  Algoritmi     │
       │  (bisect,      │
       │   sorted,      │
       │   hashing)     │
       └────────────────┘
```


Python mette a disposizione un ecosistema ricchissimo di strutture dati che va ben oltre le liste, i dizionari e gli insiemi di base. Questa guida esplora in profondita le strutture dati avanzate della libreria standard e le tecniche fondamentali per implementare strutture personalizzate, fornendo esempi pratici e analisi delle prestazioni per ogni argomento trattato.

---

## Indice

1. [Panoramica](#panoramica)
2. [Collections Module](#collections-module)
   - [namedtuple](#namedtuple)
   - [deque](#deque)
   - [defaultdict](#defaultdict)
   - [OrderedDict](#ordereddict)
   - [Counter](#counter)
   - [ChainMap](#chainmap)
     - [Risoluzione MRO-like con ChainMap](#risoluzione-mro-like-con-chainmap)
   - [UserDict, UserList e UserString](#userdict-userlist-e-userstring)
3. [Confronto: namedtuple vs typing.NamedTuple vs dataclass](#confronto-namedtuple-vs-typingnamedtuple-vs-dataclass)
4. [dataclasses.field in profondita](#dataclassesfield-in-profondita)
5. [Array e Strutture Numeriche](#array-e-strutture-numeriche)
   - [Modulo array](#modulo-array)
   - [Modulo struct](#modulo-struct)
   - [memoryview](#memoryview)
6. [Heap e Code di Priorita](#heap-e-code-di-priorita)
   - [heapq](#heapq)
   - [heapq.merge e pattern avanzati](#heapqmerge-e-pattern-avanzati)
   - [Modulo queue](#modulo-queue)
7. [Ricerca binaria con bisect](#ricerca-binaria-con-bisect)
   - [sortedcontainers in profondita](#sortedcontainers-in-profondita)
8. [frozenset e pattern immutabili](#frozenset-e-pattern-immutabili)
   - [Collezioni immutabili persistenti con pyrsistent](#collezioni-immutabili-persistenti-con-pyrsistent)
9. [Alberi e Grafi](#alberi-e-grafi)
   - [Implementazione Albero Binario](#implementazione-albero-binario)
   - [Implementazione Grafo](#implementazione-grafo)
10. [Strutture Dati Funzionali](#strutture-dati-funzionali)
11. [Strutture Specializzate](#strutture-specializzate)
    - [Trie (Prefix Tree)](#trie-prefix-tree)
    - [Bloom Filter](#bloom-filter)
12. [Algoritmi Fondamentali](#algoritmi-fondamentali)
    - [Ricerca](#ricerca)
    - [Ordinamento](#ordinamento)
    - [Hashing](#hashing)
13. [Tabella comparativa delle prestazioni](#tabella-comparativa-delle-prestazioni)
    - [dict vs OrderedDict vs SortedDict](#dict-vs-ordereddict-vs-sorteddict--confronto-dettagliato)
14. [Efficienza di memoria: __slots__, array, struct, memoryview](#efficienza-di-memoria-slots-array-struct-memoryview)
    - [Profilazione della memoria](#profilazione-della-memoria-sysgetsizeof-pympler-e-tracemalloc)
15. [Typing per Strutture Dati](#typing-per-strutture-dati)
16. [Structural Pattern Matching con strutture dati](#structural-pattern-matching-con-strutture-dati-python-310)
17. [Best Practices](#best-practices)
18. [Troubleshooting](#troubleshooting)
19. [Esercizi](#esercizi)
20. [Letture e fonti primarie](#letture-e-fonti-primarie)
21. [Cross-link](#cross-link)
22. [Glossario](#glossario)

---

## Panoramica

Le strutture dati fondamentali di Python — `list`, `dict`, `set` e `tuple` — coprono la maggior parte dei casi d'uso quotidiani. Tuttavia, man mano che i progetti crescono in complessita, emergono esigenze che richiedono strumenti piu specifici: code efficienti a doppia estremita, dizionari con valori predefiniti, contatori specializzati, code di priorita e strutture ad albero o a grafo.

La libreria standard di Python offre il modulo `collections`, che contiene implementazioni ottimizzate e pronte all'uso per molti di questi scenari. Per le strutture piu complesse — alberi, grafi, heap — Python fornisce moduli dedicati come `heapq` e `queue`, oppure consente di costruire implementazioni personalizzate sfruttando le classi.

La scelta della struttura dati corretta ha un impatto diretto sulle prestazioni dell'applicazione. Un'operazione che con una lista richiede tempo O(n) potrebbe scendere a O(1) con un dizionario o a O(log n) con un heap. Comprendere le caratteristiche di ciascuna struttura e il contesto appropriato per il suo utilizzo e una competenza fondamentale per ogni sviluppatore Python.

---

## Collections Module

Il modulo `collections` estende i tipi built-in di Python con contenitori specializzati ad alte prestazioni. Per utilizzarlo, e sufficiente importare la classe desiderata.

```python
from collections import namedtuple, deque, defaultdict, OrderedDict, Counter, ChainMap
```

### namedtuple

Le `namedtuple` sono sottoclassi di `tuple` che permettono di accedere ai campi tramite nome anziche tramite indice. Sono immutabili, leggere in memoria e perfette per rappresentare record di dati semplici.

#### Creazione e accesso

```python
from collections import namedtuple

# Definizione della namedtuple
Punto = namedtuple('Punto', ['x', 'y', 'z'])

# Creazione di un'istanza
p = Punto(1.0, 2.5, 3.7)

# Accesso per nome
print(p.x)       # 1.0
print(p.y)       # 2.5

# Accesso per indice (come una tupla normale)
print(p[0])      # 1.0
print(p[2])      # 3.7

# Unpacking
x, y, z = p
print(f"Coordinate: {x}, {y}, {z}")
```

Si possono anche specificare i campi come stringa separata da spazi o virgole:

```python
Studente = namedtuple('Studente', 'nome cognome matricola media')
s = Studente('Marco', 'Rossi', 'A12345', 28.5)
```

#### Metodi speciali

```python
# _asdict() — converte in dizionario ordinato
print(p._asdict())
# {'x': 1.0, 'y': 2.5, 'z': 3.7}

# _replace() — crea una nuova istanza con valori modificati (immutabilita preservata)
p2 = p._replace(z=10.0)
print(p2)  # Punto(x=1.0, y=2.5, z=10.0)

# _fields — tupla con i nomi dei campi
print(Punto._fields)  # ('x', 'y', 'z')

# _make() — crea un'istanza da un iterabile
dati = [4.0, 5.0, 6.0]
p3 = Punto._make(dati)
print(p3)  # Punto(x=4.0, y=5.0, z=6.0)

# Valori predefiniti (Python 3.6.1+)
Connessione = namedtuple('Connessione', ['host', 'porta', 'protocollo'], defaults=['localhost', 8080, 'tcp'])
c = Connessione()
print(c)  # Connessione(host='localhost', porta=8080, protocollo='tcp')
```

#### Typing con NamedTuple

A partire da Python 3.6, e possibile definire namedtuple tipizzate con la sintassi basata su classi, che risulta piu leggibile e supporta le annotazioni di tipo:

```python
from typing import NamedTuple

class Dipendente(NamedTuple):
    nome: str
    reparto: str
    stipendio: float
    anni_esperienza: int = 0  # valore predefinito

d = Dipendente('Laura', 'Ingegneria', 45000.0, 5)
print(d.nome)                # Laura
print(d.anni_esperienza)     # 5
```

Questa forma e preferibile rispetto alla funzione `namedtuple()` perche integra le annotazioni di tipo, facilitando l'uso con strumenti come `mypy`.

---

### deque

La `deque` (double-ended queue, coda a doppia estremita) e ottimizzata per inserimenti e rimozioni rapide da entrambe le estremita. Con una lista standard, `append()` e `pop()` in coda sono O(1), ma `insert(0, x)` e `pop(0)` sono O(n). La `deque` risolve questo problema garantendo O(1) su entrambi i lati.

#### Operazioni fondamentali

```python
from collections import deque

# Creazione
d = deque([1, 2, 3, 4, 5])

# Aggiunta agli estremi
d.append(6)          # Aggiunge a destra: deque([1, 2, 3, 4, 5, 6])
d.appendleft(0)      # Aggiunge a sinistra: deque([0, 1, 2, 3, 4, 5, 6])

# Rimozione dagli estremi
d.pop()              # Rimuove da destra: 6
d.popleft()          # Rimuove da sinistra: 0

# Estensione
d.extend([7, 8, 9])          # Estende a destra
d.extendleft([-3, -2, -1])   # Estende a sinistra (ordine invertito!)
```

#### maxlen e rotazione

```python
# Deque con dimensione massima — buffer circolare
buffer = deque(maxlen=5)
for i in range(10):
    buffer.append(i)
print(buffer)  # deque([5, 6, 7, 8, 9], maxlen=5)
# Gli elementi piu vecchi vengono automaticamente scartati

# Rotazione
d = deque([1, 2, 3, 4, 5])
d.rotate(2)    # Ruota a destra di 2 posizioni
print(d)       # deque([4, 5, 1, 2, 3])

d.rotate(-1)   # Ruota a sinistra di 1 posizione
print(d)       # deque([5, 1, 2, 3, 4])
```

#### Confronto prestazionale con list

```python
from collections import deque
import time

n = 100_000

# Inserimento in testa — list
lista = []
inizio = time.perf_counter()
for i in range(n):
    lista.insert(0, i)
tempo_lista = time.perf_counter() - inizio

# Inserimento in testa — deque
coda = deque()
inizio = time.perf_counter()
for i in range(n):
    coda.appendleft(i)
tempo_deque = time.perf_counter() - inizio

print(f"list.insert(0, x): {tempo_lista:.4f}s")   # ~3-5 secondi
print(f"deque.appendleft(x): {tempo_deque:.4f}s")  # ~0.01 secondi
```

La differenza e drammatica: per 100.000 inserimenti in testa, la `deque` e centinaia di volte piu veloce della lista.

---

### defaultdict

Il `defaultdict` e un dizionario che genera automaticamente un valore predefinito quando si accede a una chiave inesistente, eliminando la necessita di controllare l'esistenza della chiave o di usare `setdefault()`.

#### Funzioni factory

```python
from collections import defaultdict

# Lista come valore predefinito
gruppi = defaultdict(list)
coppie = [('frutta', 'mela'), ('verdura', 'carota'), ('frutta', 'banana'), ('verdura', 'spinaci')]
for categoria, elemento in coppie:
    gruppi[categoria].append(elemento)
print(dict(gruppi))
# {'frutta': ['mela', 'banana'], 'verdura': ['carota', 'spinaci']}

# Intero come valore predefinito (utile per conteggi)
conteggio = defaultdict(int)
parole = "il gatto e il cane e il pesce".split()
for parola in parole:
    conteggio[parola] += 1
print(dict(conteggio))
# {'il': 3, 'gatto': 1, 'e': 2, 'cane': 1, 'pesce': 1}

# Set come valore predefinito
indice_inverso = defaultdict(set)
documenti = {1: ['python', 'dati'], 2: ['python', 'web'], 3: ['dati', 'ml']}
for doc_id, parole_chiave in documenti.items():
    for parola in parole_chiave:
        indice_inverso[parola].add(doc_id)
print(dict(indice_inverso))
# {'python': {1, 2}, 'dati': {1, 3}, 'web': {2}, 'ml': {3}}
```

#### defaultdict annidati

```python
# Struttura annidata con lambda
albero = lambda: defaultdict(albero)
tassonomia = albero()

tassonomia['animali']['mammiferi']['cane'] = 'Canis lupus familiaris'
tassonomia['animali']['mammiferi']['gatto'] = 'Felis catus'
tassonomia['animali']['uccelli']['aquila'] = 'Aquila chrysaetos'

import json
print(json.dumps(tassonomia, indent=2))
```

#### Caso d'uso: raggruppamento avanzato

```python
from collections import defaultdict

# Raggruppamento di studenti per voto
studenti = [
    ('Alice', 'A'), ('Bob', 'B'), ('Carlo', 'A'),
    ('Diana', 'C'), ('Elena', 'B'), ('Franco', 'A')
]

per_voto = defaultdict(list)
for nome, voto in studenti:
    per_voto[voto].append(nome)

for voto in sorted(per_voto):
    print(f"Voto {voto}: {', '.join(per_voto[voto])}")
# Voto A: Alice, Carlo, Franco
# Voto B: Bob, Elena
# Voto C: Diana
```

---

### OrderedDict

`OrderedDict` e un dizionario che mantiene l'ordine di inserimento degli elementi. A partire da Python 3.7, i dizionari standard (`dict`) conservano anch'essi l'ordine di inserimento, ma `OrderedDict` offre funzionalita aggiuntive e un comportamento diverso per il confronto.

#### Operazioni specifiche

```python
from collections import OrderedDict

od = OrderedDict()
od['banana'] = 3
od['mela'] = 1
od['arancia'] = 2

# move_to_end — sposta un elemento alla fine o all'inizio
od.move_to_end('banana')           # Sposta 'banana' alla fine
print(list(od.keys()))             # ['mela', 'arancia', 'banana']

od.move_to_end('banana', last=False)  # Sposta 'banana' all'inizio
print(list(od.keys()))                # ['banana', 'mela', 'arancia']

# popitem — rimuove l'ultimo o il primo elemento
ultimo = od.popitem(last=True)     # Rimuove l'ultimo
primo = od.popitem(last=False)     # Rimuove il primo
```

#### Comportamento nel confronto

La differenza cruciale tra `OrderedDict` e `dict` riguarda l'uguaglianza: due `OrderedDict` sono uguali solo se hanno gli stessi elementi nello stesso ordine, mentre due `dict` sono uguali se contengono gli stessi elementi indipendentemente dall'ordine di inserimento.

```python
from collections import OrderedDict

od1 = OrderedDict([('a', 1), ('b', 2)])
od2 = OrderedDict([('b', 2), ('a', 1)])

print(od1 == od2)  # False — ordine diverso

d1 = {'a': 1, 'b': 2}
d2 = {'b': 2, 'a': 1}
print(d1 == d2)    # True — stesso contenuto
```

#### Quando usare OrderedDict al posto di dict

- Quando l'ordine degli elementi deve influenzare il confronto di uguaglianza.
- Quando si necessita di `move_to_end()` per riordinare le chiavi.
- Quando si implementa una cache LRU (Least Recently Used) personalizzata.
- Per compatibilita con codice che deve funzionare su Python < 3.7.

#### Internals di OrderedDict

Internamente, `OrderedDict` mantiene una lista doppiamente concatenata (doubly-linked list) che traccia l'ordine di inserimento delle chiavi, in aggiunta alla hash table standard del `dict`. Questo spiega perche `move_to_end()` e O(1): la lista concatenata permette di spostare un nodo senza toccare la hash table sottostante. Il costo e un overhead di memoria di circa il 50% rispetto a un `dict` standard (due puntatori aggiuntivi per ogni entry, piu il nodo sentinella della lista concatenata).

```python
import sys
from collections import OrderedDict

d = dict.fromkeys(range(1000))
od = OrderedDict.fromkeys(range(1000))

print(f"dict:        {sys.getsizeof(d):>8} byte")
print(f"OrderedDict: {sys.getsizeof(od):>8} byte")
# OrderedDict occupa circa il 50% in piu
```

Quando l'uguaglianza order-sensitive non serve e `move_to_end()` non e necessario, il `dict` standard e preferibile per minor consumo di memoria e velocita marginalmente superiore.

---

### Counter

`Counter` e una sottoclasse di `dict` progettata specificamente per il conteggio di elementi hashable. Risulta estremamente utile per analisi di frequenza, elaborazione di testi e aggregazione di dati.

#### Creazione e operazioni base

```python
from collections import Counter

# Da una lista
c = Counter(['rosso', 'blu', 'rosso', 'verde', 'blu', 'rosso'])
print(c)  # Counter({'rosso': 3, 'blu': 2, 'verde': 1})

# Da una stringa
c2 = Counter('abracadabra')
print(c2)  # Counter({'a': 5, 'b': 2, 'r': 2, 'c': 1, 'd': 1})

# Da keyword arguments
c3 = Counter(gatti=4, cani=8, pesci=2)
```

#### Metodi principali

```python
c = Counter('abracadabra')

# most_common(n) — restituisce i n elementi piu frequenti
print(c.most_common(3))
# [('a', 5), ('b', 2), ('r', 2)]

# elements() — iteratore che ripete ogni elemento per il suo conteggio
print(sorted(c.elements()))
# ['a', 'a', 'a', 'a', 'a', 'b', 'b', 'c', 'd', 'r', 'r']

# Aggiornamento
c.update('aabbcc')     # Aggiunge conteggi
c.subtract('abc')      # Sottrae conteggi

# total() — somma di tutti i conteggi (Python 3.10+)
print(c.total())
```

#### Operazioni aritmetiche

```python
from collections import Counter

inventario_roma = Counter(mele=50, banane=30, arance=20)
inventario_milano = Counter(mele=30, banane=40, pere=15)

# Somma dei conteggi
totale = inventario_roma + inventario_milano
print(totale)
# Counter({'mele': 80, 'banane': 70, 'arance': 20, 'pere': 15})

# Differenza (mantiene solo valori positivi)
differenza = inventario_roma - inventario_milano
print(differenza)
# Counter({'arance': 20, 'mele': 20})

# Intersezione (minimo tra i conteggi)
comune = inventario_roma & inventario_milano
print(comune)
# Counter({'mele': 30, 'banane': 30})

# Unione (massimo tra i conteggi)
unione = inventario_roma | inventario_milano
print(unione)
# Counter({'mele': 50, 'banane': 40, 'arance': 20, 'pere': 15})
```

#### Esempi pratici

```python
from collections import Counter

# Analisi di frequenza delle parole in un testo
testo = """Python e un linguaggio di programmazione potente e versatile.
Python e usato per lo sviluppo web, l'analisi dei dati e il machine learning.
Python e amato dalla comunita per la sua semplicita."""

parole = testo.lower().split()
frequenze = Counter(parole)
print("Le 5 parole piu frequenti:")
for parola, conteggio in frequenze.most_common(5):
    print(f"  {parola}: {conteggio}")

# Analisi dei log
log_entries = [
    'ERROR: connessione fallita',
    'WARNING: memoria alta',
    'ERROR: timeout',
    'INFO: avvio servizio',
    'ERROR: connessione fallita',
    'WARNING: disco pieno',
    'ERROR: connessione fallita',
]
livelli = Counter(entry.split(':')[0] for entry in log_entries)
print(livelli)
# Counter({'ERROR': 4, 'WARNING': 2, 'INFO': 1})
```

---

### ChainMap

`ChainMap` raggruppa piu dizionari in un'unica vista, cercando le chiavi in sequenza attraverso tutti i dizionari. Non crea un nuovo dizionario unito, ma mantiene riferimenti ai dizionari originali.

```python
from collections import ChainMap

# Configurazione a livelli: locale sovrascrive globale
config_default = {'tema': 'chiaro', 'lingua': 'it', 'font_size': 12}
config_utente = {'tema': 'scuro', 'font_size': 14}
config_sessione = {'font_size': 16}

config = ChainMap(config_sessione, config_utente, config_default)

# La ricerca segue l'ordine: sessione -> utente -> default
print(config['font_size'])   # 16 (dalla sessione)
print(config['tema'])        # 'scuro' (dall'utente)
print(config['lingua'])      # 'it' (dal default)
```

#### new_child e parents

```python
# new_child() — aggiunge un nuovo dizionario in cima alla catena
config_temp = config.new_child({'lingua': 'en', 'debug': True})
print(config_temp['lingua'])   # 'en'
print(config_temp['tema'])     # 'scuro'

# parents — restituisce un ChainMap senza il primo dizionario
genitori = config.parents
print(genitori['font_size'])   # 14 (dall'utente, la sessione e stata esclusa)
```

`ChainMap` e particolarmente utile per gestire contesti di configurazione stratificati, ambienti di variabili annidate e scope di ricerca gerarchici.

#### ChainMap: deep dive — scritture, cancellazioni e maps

Le scritture e le cancellazioni su un `ChainMap` operano **esclusivamente sul primo mapping della catena** (il "child"). Questo e un comportamento intenzionale: i mapping sottostanti restano immutati, il che rende `ChainMap` sicuro per scope annidati.

```python
from collections import ChainMap

base = {'x': 1, 'y': 2}
overlay = {}
chain = ChainMap(overlay, base)

# La scrittura va nel primo mapping (overlay)
chain['x'] = 99
print(overlay)   # {'x': 99}
print(base)      # {'x': 1} — invariato

# La cancellazione opera solo sul primo mapping
del chain['x']
print(chain['x'])  # 1 — torna a leggere da base

# Tentare di cancellare una chiave che esiste solo in base:
try:
    del chain['y']   # KeyError: non e in overlay
except KeyError:
    print("'y' non e nel primo mapping")
```

L'attributo `maps` e la lista dei mapping sottostanti ed e direttamente accessibile e mutabile:

```python
from collections import ChainMap

c = ChainMap({'a': 1}, {'b': 2}, {'c': 3})
print(c.maps)       # [{'a': 1}, {'b': 2}, {'c': 3}]
print(list(c))      # ['c', 'b', 'a'] — chiavi da tutti i mapping, deduplicate

# Inserire un nuovo livello tra i mapping esistenti
c.maps.insert(1, {'a': 100, 'd': 4})
print(c['a'])       # 1 — il primo mapping vince ancora
print(c['d'])       # 4 — dal mapping appena inserito
```

**Caso d'uso avanzato: scope di variabili per un interprete.** Un interprete di un linguaggio di scripting puo modellare gli scope delle variabili con `ChainMap`: ogni chiamata a funzione crea un `new_child()`, e il ritorno dalla funzione usa `parents` per ripristinare lo scope precedente.

```python
from collections import ChainMap

globali = {'pi': 3.14159, 'e': 2.71828}
scope = ChainMap(globali)

# Entrata in una funzione: nuovo scope figlio
scope = scope.new_child({'x': 10, 'y': 20})
print(scope['x'])    # 10 — locale
print(scope['pi'])   # 3.14159 — globale

# Entrata in una funzione annidata
scope = scope.new_child({'x': 99})
print(scope['x'])    # 99 — shadow della variabile locale esterna

# Ritorno dalla funzione annidata
scope = scope.parents
print(scope['x'])    # 10 — ripristinato

# Ritorno dalla funzione esterna
scope = scope.parents
print('x' in scope)  # False — x non esiste nello scope globale
```

#### Risoluzione MRO-like con ChainMap

Il meccanismo di risoluzione di `ChainMap` segue lo stesso principio del Method Resolution Order (MRO) di Python: la prima mappa che contiene la chiave vince, esattamente come la prima classe nella gerarchia MRO che definisce un metodo prevale sulle classi successive. Questo pattern puo essere sfruttato per implementare sistemi di configurazione a livelli, override di temi, o pipeline di trasformazione dove ogni livello puo sovrascrivere selettivamente le impostazioni del livello precedente.

```python
from collections import ChainMap

# Configurazione multi-livello: progetto > utente > default
default = {
    'tema': 'chiaro',
    'lingua': 'it',
    'font_size': 14,
    'debug': False,
    'max_connessioni': 10,
}

utente = {
    'tema': 'scuro',
    'font_size': 16,
}

progetto = {
    'debug': True,
    'max_connessioni': 50,
}

config = ChainMap(progetto, utente, default)

# Risoluzione: progetto > utente > default
print(config['tema'])              # 'scuro' — da utente (progetto non lo definisce)
print(config['debug'])             # True — da progetto (override del default False)
print(config['lingua'])            # 'it' — da default (nessun override)
print(config['font_size'])         # 16 — da utente
print(config['max_connessioni'])   # 50 — da progetto
```

La differenza fondamentale rispetto a `{**default, **utente, **progetto}` e che `ChainMap` mantiene i dizionari separati. Questo significa che:

- Le modifiche al dizionario originale si riflettono immediatamente nella ChainMap.
- Si puo ispezionare ogni livello separatamente con `.maps`.
- Si puo rimuovere un livello senza ricostruire l'intero dizionario.

```python
# Ispezione dei livelli
print(config.maps)
# [{'debug': True, 'max_connessioni': 50},
#  {'tema': 'scuro', 'font_size': 16},
#  {'tema': 'chiaro', 'lingua': 'it', 'font_size': 14, ...}]

# Aggiunta dinamica di un livello "override temporaneo"
override_sessione = {'lingua': 'en', 'debug': False}
config_sessione = config.new_child(override_sessione)
print(config_sessione['lingua'])   # 'en' — override di sessione
print(config_sessione['tema'])     # 'scuro' — propagato da utente

# La scrittura avviene SOLO sulla prima mappa (child)
config_sessione['nuova_chiave'] = 'valore'
print('nuova_chiave' in override_sessione)  # True
print('nuova_chiave' in progetto)           # False — le mappe interne sono intatte
```

#### ChainMap vs merge di dizionari — quando scegliere

| Aspetto | `ChainMap` | `{**d1, **d2, **d3}` |
|---------|-----------|---------------------|
| Propagazione modifiche | Si (vista live) | No (copia statica) |
| Costo di creazione | O(1) — nessuna copia | O(n) — copia tutte le chiavi |
| Ispezione per livello | Si (`.maps`) | No (informazione persa) |
| Scrittura | Solo sulla prima mappa | Sul dizionario risultante |
| Iterazione | Piu lenta (attraversa tutte le mappe) | Piu veloce (singolo dict) |

Usare `ChainMap` quando i livelli sono semanticamente distinti e la propagazione delle modifiche e desiderata. Usare il merge quando serve un singolo dizionario statico senza legami con le fonti originali.

---

### UserDict, UserList e UserString

Il modulo `collections` espone tre classi wrapper progettate per semplificare la sottoclassificazione dei tipi built-in. Sottoclassificare direttamente `dict`, `list` o `str` e problematico: i metodi C-level (come `__setitem__` chiamato da `update()` in `dict`) non sempre invocano le versioni Python sovrascitte, causando comportamenti incoerenti. `UserDict`, `UserList` e `UserString` risolvono il problema delegando a un attributo `.data` interno.

#### UserDict

```python
from collections import UserDict

class DizionarioAudit(UserDict):
    """Dizionario che logga ogni modifica."""

    def __setitem__(self, chiave, valore):
        print(f"SET: {chiave!r} = {valore!r}")
        super().__setitem__(chiave, valore)

    def __delitem__(self, chiave):
        print(f"DEL: {chiave!r}")
        super().__delitem__(chiave)

audit = DizionarioAudit(a=1, b=2)
# SET: a = 1
# SET: b = 2

audit['c'] = 3       # SET: 'c' = 3
audit.update({'d': 4})  # SET: 'd' = 4 — correttamente intercettato
del audit['a']        # DEL: 'a'

# L'attributo .data contiene il dict sottostante
print(audit.data)     # {'b': 2, 'c': 3, 'd': 4}
```

Se si fosse sottoclassificato `dict` direttamente, `update()` non avrebbe invocato `__setitem__` personalizzato su CPython, perche `dict.update()` e implementato in C e bypassa il dispatch Python.

#### UserList

```python
from collections import UserList

class ListaValidata(UserList):
    """Lista che accetta solo interi positivi."""

    def _valida(self, valore):
        if not isinstance(valore, int) or valore <= 0:
            raise ValueError(f"Atteso intero positivo, ricevuto {valore!r}")

    def __setitem__(self, indice, valore):
        if isinstance(indice, slice):
            for v in valore:
                self._valida(v)
        else:
            self._valida(valore)
        super().__setitem__(indice, valore)

    def append(self, valore):
        self._valida(valore)
        super().append(valore)

    def extend(self, valori):
        for v in valori:
            self._valida(v)
        super().extend(valori)

    def insert(self, indice, valore):
        self._valida(valore)
        super().insert(indice, valore)

lv = ListaValidata([1, 2, 3])
lv.append(4)      # OK
try:
    lv.append(-1)  # ValueError
except ValueError as e:
    print(e)
```

#### Quando usare User* vs sottoclassificare direttamente

| Scenario | Scelta |
|----------|--------|
| Override di `__setitem__`, `__delitem__`, `__getitem__` | `UserDict` / `UserList` |
| Aggiunta di nuovi metodi senza override | Sottoclasse diretta OK |
| Necessita di compatibilita con C extension che richiedono `dict` esatto | Sottoclasse diretta o composizione |
| `isinstance(obj, dict)` deve essere `True` | Sottoclasse diretta (`UserDict` non e un `dict`) |

> **Nota:** `UserString` segue lo stesso pattern per le stringhe. E utile per creare tipi stringa specializzati con validazione o trasformazione automatica.

---

## Confronto: namedtuple vs typing.NamedTuple vs dataclass

Tre modi per definire record di dati in Python, ognuno con compromessi diversi.

| Caratteristica | `collections.namedtuple()` | `typing.NamedTuple` | `@dataclass` |
|---|---|---|---|
| **Sintassi** | Funzione factory | Classe con ereditarieta | Decoratore su classe |
| **Immutabilita** | Si (e una tupla) | Si (e una tupla) | No (default); `frozen=True` la rende immutabile |
| **Type hints** | No (solo `defaults=`) | Si | Si |
| **Metodi custom** | Limitati (si possono aggiungere con ereditarieta) | Si, in-line nella classe | Si, pieno supporto |
| **`__hash__`** | Automatico (immutabile) | Automatico (immutabile) | Solo se `frozen=True` o `unsafe_hash=True` |
| **`__eq__`** | Confronto per valore (come tupla) | Confronto per valore (come tupla) | Confronto campo-per-campo |
| **Unpacking `*`/indice** | Si (e una tupla) | Si (e una tupla) | No (non e una sequenza) |
| **Ereditarieta** | Fragile (cambiare i campi rompe la gerarchia) | Fragile (stessi limiti della tupla) | Pieno supporto |
| **`__slots__`** | Impliciti (tupla non ha `__dict__`) | Impliciti | `slots=True` (Python 3.10+) |
| **Memoria** | Minima (tupla) | Minima (tupla) | Maggiore (ha `__dict__` senza `slots=True`) |
| **Versione minima** | Python 2.6 | Python 3.6 | Python 3.7 |

```python
# I tre approcci per lo stesso record:
from collections import namedtuple
from typing import NamedTuple
from dataclasses import dataclass

# 1. collections.namedtuple
Punto1 = namedtuple('Punto1', ['x', 'y'])

# 2. typing.NamedTuple
class Punto2(NamedTuple):
    x: float
    y: float

# 3. dataclass (frozen per immutabilita)
@dataclass(frozen=True, slots=True)
class Punto3:
    x: float
    y: float

# Differenze osservabili
p1 = Punto1(1.0, 2.0)
p2 = Punto2(1.0, 2.0)
p3 = Punto3(1.0, 2.0)

print(p1[0])     # 1.0 — indicizzabile (e una tupla)
print(p2[0])     # 1.0 — indicizzabile (e una tupla)
# p3[0]          # TypeError — dataclass non e indicizzabile

x, y = p1        # unpacking funziona
x, y = p2        # unpacking funziona
# x, y = p3      # TypeError — dataclass non e unpacking-friendly

print(hash(p1))  # OK — immutabile
print(hash(p2))  # OK — immutabile
print(hash(p3))  # OK — frozen=True
```

**Regola pratica:** preferire `typing.NamedTuple` per record immutabili leggeri che beneficiano dell'unpacking; preferire `@dataclass` per entita di dominio con logica, metodi, mutabilita controllata o ereditarieta. Usare `collections.namedtuple()` solo per codice legacy o dove la retrocompatibilita pre-3.6 e necessaria.

---

## dataclasses.field in profondita

La funzione `dataclasses.field()` offre controllo granulare sulla configurazione di ogni campo di una dataclass. Senza `field()`, i campi assumono tutti i default: sono confrontabili, inclusi nella `repr`, e partecipano all'hashing (se la dataclass e `frozen`).

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Task:
    titolo: str
    priorita: int = 0
    tag: list[str] = field(default_factory=list)  # OBBLIGATORIO per mutable default
    _id_interno: int = field(default=0, repr=False, compare=False)
    metadata: dict[str, Any] = field(
        default_factory=dict,
        metadata={'descrizione': 'Metadati aggiuntivi del task'}
    )

t1 = Task("Implementare login", priorita=1, tag=["auth", "backend"])
t2 = Task("Implementare login", priorita=1, tag=["auth", "backend"], _id_interno=999)

print(t1)           # Task(titolo='Implementare login', priorita=1, tag=['auth', 'backend'], metadata={})
print(t1 == t2)     # True — _id_interno e escluso dal confronto (compare=False)
```

#### Parametri di field()

| Parametro | Default | Effetto |
|-----------|---------|---------|
| `default` | `MISSING` | Valore predefinito del campo |
| `default_factory` | `MISSING` | Callable che produce il default (per tipi mutabili) |
| `repr` | `True` | Includere nella rappresentazione `__repr__` |
| `hash` | `None` | `None` = segue `compare`; `True`/`False` sovrascrive |
| `init` | `True` | Includere nel `__init__` generato |
| `compare` | `True` | Includere in `__eq__` e nei confronti |
| `kw_only` | `False` | Campo keyword-only nel `__init__` (Python 3.10+) |
| `metadata` | `None` | Mapping di metadati arbitrari (non usato da dataclasses, utile per framework) |

#### default_factory: perche non si possono usare mutable default direttamente

```python
from dataclasses import dataclass, field

# ERRORE — Python lo blocca intenzionalmente:
# @dataclass
# class Errato:
#     elementi: list[int] = []   # ValueError: mutable default non consentito

# CORRETTO — default_factory crea una nuova lista per ogni istanza:
@dataclass
class Corretto:
    elementi: list[int] = field(default_factory=list)

c1 = Corretto()
c2 = Corretto()
c1.elementi.append(1)
print(c1.elementi)   # [1]
print(c2.elementi)   # [] — correttamente indipendente
```

#### field con init=False: campi calcolati

```python
from dataclasses import dataclass, field

@dataclass
class Rettangolo:
    larghezza: float
    altezza: float
    area: float = field(init=False)

    def __post_init__(self):
        self.area = self.larghezza * self.altezza

r = Rettangolo(5.0, 3.0)
print(r)       # Rettangolo(larghezza=5.0, altezza=3.0, area=15.0)
print(r.area)  # 15.0
```

#### metadata: annotare i campi per framework e validazione

```python
from dataclasses import dataclass, field, fields

@dataclass
class Utente:
    nome: str = field(metadata={'max_length': 100, 'required': True})
    email: str = field(metadata={'pattern': r'^[\w.-]+@[\w.-]+\.\w+$', 'required': True})
    eta: int = field(default=0, metadata={'min': 0, 'max': 150})

# I metadata sono accessibili tramite fields():
for f in fields(Utente):
    print(f"{f.name}: {f.metadata}")
# nome: {'max_length': 100, 'required': True}
# email: {'pattern': '^[\\w.-]+@[\\w.-]+\\.\\w+$', 'required': True}
# eta: {'min': 0, 'max': 150}
```

Framework come Pydantic, marshmallow e cattrs sfruttano `metadata` per derivare regole di validazione e serializzazione dai campi delle dataclass.

---

## Array e Strutture Numeriche

### Modulo array

Il modulo `array` fornisce array tipizzati, simili alle liste ma vincolati a contenere elementi di un unico tipo numerico. Occupano significativamente meno memoria rispetto alle liste di interi o float.

```python
from array import array

# Creazione con codice di tipo
# 'i' = signed int, 'f' = float, 'd' = double, 'b' = signed char
interi = array('i', [1, 2, 3, 4, 5])
reali = array('d', [1.1, 2.2, 3.3])

# Operazioni simili alle liste
interi.append(6)
interi.extend([7, 8, 9])
print(interi[2])         # 3
interi.insert(0, 0)

# Conversione
lista = interi.tolist()
byte_data = interi.tobytes()

# Errore di tipo — il tipo e forzato
try:
    interi.append(3.14)  # TypeError
except TypeError as e:
    print(f"Errore: {e}")
```

#### Codici di tipo principali

| Codice | Tipo C          | Dimensione minima (byte) |
|--------|-----------------|--------------------------|
| `'b'`  | signed char     | 1                        |
| `'B'`  | unsigned char   | 1                        |
| `'h'`  | signed short    | 2                        |
| `'H'`  | unsigned short  | 2                        |
| `'i'`  | signed int      | 2                        |
| `'I'`  | unsigned int    | 2                        |
| `'l'`  | signed long     | 4                        |
| `'f'`  | float           | 4                        |
| `'d'`  | double          | 8                        |

#### Quando usare array al posto di list

- Quando si memorizzano grandi quantita di dati numerici omogenei.
- Quando il risparmio di memoria e critico.
- Per l'interfaccia con codice C o per l'I/O binario.
- Per calcoli numerici intensivi, considerare `numpy.ndarray` che e ancora piu efficiente.

#### array vs list: confronto di memoria

```python
import sys
from array import array

n = 100_000

lista_int = list(range(n))
array_int = array('i', range(n))

# Memoria dell'oggetto contenitore
mem_lista = sys.getsizeof(lista_int)
mem_array = sys.getsizeof(array_int)
print(f"list:  {mem_lista:>10,} byte")    # ~800,056
print(f"array: {mem_array:>10,} byte")    # ~400,064

# Ma la lista ha overhead per-elemento: ogni int e un oggetto Python separato.
# La memoria TOTALE della lista include n oggetti PyObject (28 byte ciascuno su x64).
# L'array usa 4 byte per intero (tipo 'i'), senza overhead per-elemento.
# Risparmio reale: ~95% per array di int rispetto a list di int.
```

> **Nota:** se si lavora con array numerici di grandi dimensioni e si necessita di operazioni vettoriali (somme, prodotti, slice avanzati), NumPy `ndarray` e la scelta corretta. Il modulo `array` e pensato per storage compatto e interoperabilita con C, non per calcolo numerico.

### Modulo struct

Il modulo `struct` permette di convertire tra valori Python e strutture dati binarie in formato C. E essenziale per leggere e scrivere file binari e per la comunicazione di rete a basso livello.

```python
import struct

# Packing — da valori Python a byte
# 'i' = int (4 byte), 'f' = float (4 byte), '10s' = stringa di 10 byte
dati_binari = struct.pack('if10s', 42, 3.14, b'Ciao mondo')
print(len(dati_binari))   # 18 byte

# Unpacking — da byte a valori Python
numero, decimale, testo = struct.unpack('if10s', dati_binari)
print(numero)              # 42
print(decimale)            # 3.140000104904175 (precisione float)
print(testo.strip(b'\x00').decode())  # 'Ciao mondo'

# Calcolo della dimensione
print(struct.calcsize('if10s'))   # 18

# Byte order: '<' little-endian, '>' big-endian, '!' network (big-endian)
dati_rete = struct.pack('!HI', 8080, 192168001)
porta, indirizzo = struct.unpack('!HI', dati_rete)
```

Un caso d'uso comune e la lettura di intestazioni di file binari (ad esempio BMP, WAV) o la serializzazione di pacchetti di rete.

### memoryview

`memoryview` crea una "vista" su un buffer di byte (`bytes`, `bytearray`, `array.array`) senza copiare i dati. E fondamentale per l'elaborazione efficiente di dati binari di grandi dimensioni, dove lo slicing di `bytes` produrrebbe copie costose.

```python
# Senza memoryview: ogni slice crea una copia
dati = b'\x00' * 10_000_000   # 10 MB
parte = dati[1000:2000]       # copia 1000 byte

# Con memoryview: slice a costo zero (zero-copy)
vista = memoryview(dati)
parte_mv = vista[1000:2000]   # nessuna copia — stessa memoria sottostante
print(len(parte_mv))          # 1000
print(bytes(parte_mv[:5]))    # b'\x00\x00\x00\x00\x00'
```

#### memoryview con struct per parsing binario

```python
import struct

# Simulare un pacchetto di rete con header + payload
pacchetto = bytearray(1024)
# Header: 2 byte versione, 4 byte lunghezza, 2 byte checksum
struct.pack_into('!HIH', pacchetto, 0, 1, 1016, 0xABCD)

mv = memoryview(pacchetto)
header = mv[:8]
payload = mv[8:]

versione, lunghezza, checksum = struct.unpack_from('!HIH', header)
print(f"Versione: {versione}, Payload: {lunghezza} byte, Checksum: {checksum:#06x}")
# Versione: 1, Payload: 1016 byte, Checksum: 0xabcd
```

#### memoryview con array tipizzati

```python
from array import array

a = array('i', [1, 2, 3, 4, 5, 6, 7, 8])
mv = memoryview(a)

# Cast a byte per ispezionare la rappresentazione binaria
mv_bytes = mv.cast('B')
print(mv_bytes.tolist()[:8])  # primi 8 byte (primi 2 int su little-endian)

# Slicing senza copia
sotto_array = mv[2:5]
print(sotto_array.tolist())   # [3, 4, 5]

# Modifica in-place (se il buffer e writable)
mv[0] = 99
print(a[0])                   # 99 — la modifica si riflette nell'array originale
```

**Quando usare memoryview:** parsing di file binari, protocolli di rete, elaborazione di immagini/audio, qualsiasi scenario in cui si opera su slice di grandi buffer e la copia dei dati sarebbe un collo di bottiglia. Per la maggior parte del codice applicativo, `bytes` e `bytearray` sono sufficienti.

---

## Heap e Code di Priorita

### heapq

Il modulo `heapq` implementa un min-heap (coda di priorita minima) utilizzando una lista Python ordinaria. In un min-heap, l'elemento piu piccolo si trova sempre all'indice 0.

#### Operazioni fondamentali

```python
import heapq

# Creazione tramite heapify
dati = [5, 3, 8, 1, 9, 2, 7]
heapq.heapify(dati)     # Trasforma la lista in un heap in-place — O(n)
print(dati)              # [1, 3, 2, 5, 9, 8, 7]

# heappush — inserisce mantenendo la proprieta heap — O(log n)
heapq.heappush(dati, 0)
print(dati[0])           # 0

# heappop — rimuove e restituisce il minimo — O(log n)
minimo = heapq.heappop(dati)
print(minimo)            # 0

# heappushpop — push + pop in un'unica operazione (piu efficiente)
risultato = heapq.heappushpop(dati, 4)

# heapreplace — pop + push in un'unica operazione
risultato = heapq.heapreplace(dati, 6)
```

#### nlargest e nsmallest

```python
import heapq

punteggi = [85, 92, 78, 95, 88, 72, 90, 98, 65, 82]

# I 3 punteggi piu alti
migliori = heapq.nlargest(3, punteggi)
print(migliori)   # [98, 95, 92]

# I 3 punteggi piu bassi
peggiori = heapq.nsmallest(3, punteggi)
print(peggiori)   # [65, 72, 78]

# Con chiave personalizzata
studenti = [
    {'nome': 'Alice', 'media': 28.5},
    {'nome': 'Bob', 'media': 25.0},
    {'nome': 'Carlo', 'media': 30.0},
    {'nome': 'Diana', 'media': 27.3},
]
top2 = heapq.nlargest(2, studenti, key=lambda s: s['media'])
print([s['nome'] for s in top2])  # ['Carlo', 'Alice']
```

**Quando usare nlargest/nsmallest vs sorted:** se `n` e piccolo rispetto alla dimensione della lista, `heapq.nlargest(n, data)` e O(N log n) — piu efficiente di `sorted(data)[-n:]` che e O(N log N). Se `n` e vicino a `N`, `sorted()` e preferibile. Se `n == 1`, usare `min()` / `max()` che sono O(N) senza overhead.

#### Min-heap e trucco per max-heap

Poiche `heapq` implementa solo un min-heap, per ottenere un max-heap si negano i valori:

```python
import heapq

# Max-heap tramite negazione
max_heap = []
valori = [5, 3, 8, 1, 9, 2]

for v in valori:
    heapq.heappush(max_heap, -v)    # Inserisci il negativo

# Estrarre il massimo
massimo = -heapq.heappop(max_heap)   # Nega di nuovo
print(massimo)   # 9
```

#### Implementazione di una coda di priorita

```python
import heapq
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class ElementoPriorita:
    priorita: int
    ordine_inserimento: int = field(compare=True)
    dato: Any = field(compare=False)

class CodaPriorita:
    def __init__(self):
        self._coda = []
        self._contatore = 0

    def inserisci(self, elemento, priorita):
        entry = ElementoPriorita(priorita, self._contatore, elemento)
        heapq.heappush(self._coda, entry)
        self._contatore += 1

    def estrai(self):
        if self._coda:
            return heapq.heappop(self._coda).dato
        raise IndexError("Coda vuota")

    def __len__(self):
        return len(self._coda)

    def __bool__(self):
        return bool(self._coda)

# Utilizzo
coda = CodaPriorita()
coda.inserisci("compito normale", priorita=3)
coda.inserisci("bug critico", priorita=1)
coda.inserisci("miglioramento", priorita=5)
coda.inserisci("bug importante", priorita=2)

while coda:
    print(coda.estrai())
# bug critico
# bug importante
# compito normale
# miglioramento
```

---

### heapq.merge e pattern avanzati

#### heapq.merge — unione di iterabili ordinati

`heapq.merge()` unisce piu iterabili gia ordinati in un unico iteratore ordinato, senza caricare tutto in memoria. E particolarmente utile per il merge di file di log ordinati per timestamp o per l'implementazione di merge sort esterno.

```python
import heapq

# Merge di sequenze ordinate
log_server_1 = [
    (1, "avvio server 1"),
    (3, "richiesta ricevuta"),
    (7, "risposta inviata"),
]
log_server_2 = [
    (2, "avvio server 2"),
    (5, "errore connessione"),
    (8, "recovery completato"),
]
log_server_3 = [
    (4, "health check"),
    (6, "scaling up"),
    (9, "metriche inviate"),
]

# Merge senza caricare tutto in memoria — produce un iteratore lazy
for timestamp, messaggio in heapq.merge(log_server_1, log_server_2, log_server_3):
    print(f"[{timestamp}] {messaggio}")
# [1] avvio server 1
# [2] avvio server 2
# [3] richiesta ricevuta
# ...in ordine di timestamp
```

#### merge con chiave personalizzata

```python
import heapq

file_a = [
    {"ts": "2026-05-01", "evento": "login"},
    {"ts": "2026-05-03", "evento": "acquisto"},
]
file_b = [
    {"ts": "2026-05-02", "evento": "logout"},
    {"ts": "2026-05-04", "evento": "supporto"},
]

for record in heapq.merge(file_a, file_b, key=lambda r: r["ts"]):
    print(f"{record['ts']}: {record['evento']}")
```

#### merge per external sort (sort di file piu grandi della RAM)

```python
import heapq
import tempfile
from pathlib import Path

def external_sort(input_path: str, output_path: str, chunk_size: int = 100_000):
    """Ordina un file troppo grande per la RAM usando merge sort esterno."""
    file_temporanei = []

    # Fase 1: spezza in chunk ordinati
    with open(input_path, 'r', encoding='utf-8') as f:
        while True:
            righe = []
            for _ in range(chunk_size):
                riga = f.readline()
                if not riga:
                    break
                righe.append(riga)
            if not righe:
                break
            righe.sort()
            tmp = tempfile.NamedTemporaryFile(
                mode='w', suffix='.sorted', delete=False, encoding='utf-8'
            )
            tmp.writelines(righe)
            tmp.close()
            file_temporanei.append(tmp.name)

    # Fase 2: merge dei chunk ordinati
    handles = [open(f, 'r', encoding='utf-8') for f in file_temporanei]
    with open(output_path, 'w', encoding='utf-8') as out:
        for riga in heapq.merge(*handles):
            out.write(riga)

    # Pulizia
    for h in handles:
        h.close()
    for f in file_temporanei:
        Path(f).unlink()
```

---

### Modulo queue

Il modulo `queue` fornisce code thread-safe, progettate per la comunicazione tra thread in programmi concorrenti.

#### Queue, LifoQueue, PriorityQueue

```python
from queue import Queue, LifoQueue, PriorityQueue

# Queue — FIFO (First In, First Out)
coda_fifo = Queue(maxsize=10)
coda_fifo.put("primo")
coda_fifo.put("secondo")
coda_fifo.put("terzo")
print(coda_fifo.get())   # 'primo'

# LifoQueue — LIFO (Last In, First Out) — si comporta come uno stack
stack = LifoQueue()
stack.put("primo")
stack.put("secondo")
stack.put("terzo")
print(stack.get())       # 'terzo'

# PriorityQueue — ordina per priorita
pq = PriorityQueue()
pq.put((2, "media priorita"))
pq.put((1, "alta priorita"))
pq.put((3, "bassa priorita"))
print(pq.get())          # (1, 'alta priorita')
```

#### Operazioni thread-safe

```python
from queue import Queue
import threading
import time

coda = Queue()

def produttore(coda, n_elementi):
    for i in range(n_elementi):
        elemento = f"elemento_{i}"
        coda.put(elemento)
        print(f"Prodotto: {elemento}")
        time.sleep(0.1)
    coda.put(None)  # Segnale di terminazione

def consumatore(coda):
    while True:
        elemento = coda.get()       # Blocca fino a quando un elemento e disponibile
        if elemento is None:
            break
        print(f"Consumato: {elemento}")
        coda.task_done()            # Segnala che l'elaborazione e completata

# Avvio dei thread
t_prod = threading.Thread(target=produttore, args=(coda, 5))
t_cons = threading.Thread(target=consumatore, args=(coda,))
t_prod.start()
t_cons.start()
t_prod.join()
t_cons.join()
```

#### asyncio.Queue

Per la programmazione asincrona, `asyncio` fornisce le proprie code, non thread-safe ma sicure per l'uso con coroutine:

```python
import asyncio

async def produttore_async(coda: asyncio.Queue):
    for i in range(5):
        await asyncio.sleep(0.1)
        await coda.put(f"dato_{i}")
    await coda.put(None)

async def consumatore_async(coda: asyncio.Queue):
    while True:
        elemento = await coda.get()
        if elemento is None:
            break
        print(f"Elaborato: {elemento}")

async def main():
    coda = asyncio.Queue(maxsize=3)
    await asyncio.gather(
        produttore_async(coda),
        consumatore_async(coda)
    )

asyncio.run(main())
```

---

## Ricerca binaria con bisect

Il modulo `bisect` fornisce funzioni per mantenere una lista ordinata senza doverla riordinare dopo ogni inserimento. Internamente usa la ricerca binaria (O(log n) per la ricerca, O(n) per l'inserimento a causa dello shift degli elementi).

### bisect_left, bisect_right e insort

```python
import bisect

dati = [10, 20, 30, 40, 50]

# bisect_left: punto di inserimento a sinistra (prima di eventuali duplicati)
print(bisect.bisect_left(dati, 30))    # 2
print(bisect.bisect_left(dati, 25))    # 2

# bisect_right (alias bisect): punto di inserimento a destra (dopo eventuali duplicati)
print(bisect.bisect_right(dati, 30))   # 3
print(bisect.bisect(dati, 30))         # 3 — alias di bisect_right

# insort_left: inserisce mantenendo l'ordine (a sinistra dei duplicati)
bisect.insort_left(dati, 25)
print(dati)   # [10, 20, 25, 30, 40, 50]

# insort_right (alias insort): inserisce a destra dei duplicati
bisect.insort(dati, 30)
print(dati)   # [10, 20, 25, 30, 30, 40, 50]
```

### Pattern: ricerca binaria con bisect

```python
import bisect

def cerca_binaria(sequenza_ordinata: list, valore) -> int:
    """Ricerca binaria che restituisce l'indice o -1."""
    i = bisect.bisect_left(sequenza_ordinata, valore)
    if i < len(sequenza_ordinata) and sequenza_ordinata[i] == valore:
        return i
    return -1

dati = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
print(cerca_binaria(dati, 23))   # 5
print(cerca_binaria(dati, 24))   # -1
```

### Pattern: mappatura a intervalli (grade assignment)

```python
import bisect

def assegna_voto(punteggio: int) -> str:
    """Mappa un punteggio 0-100 a un voto letterale."""
    soglie = [60, 70, 80, 90]
    voti = ['F', 'D', 'C', 'B', 'A']
    return voti[bisect.bisect(soglie, punteggio)]

for p in [33, 65, 77, 85, 92, 100]:
    print(f"{p}: {assegna_voto(p)}")
# 33: F, 65: D, 77: C, 85: B, 92: A, 100: A
```

### Pattern: SortedList con bisect

```python
import bisect

class SortedList:
    """Lista sempre ordinata con inserimento O(n) e ricerca O(log n)."""

    def __init__(self, iterable=()):
        self._dati = sorted(iterable)

    def add(self, valore):
        bisect.insort(self._dati, valore)

    def remove(self, valore):
        i = bisect.bisect_left(self._dati, valore)
        if i < len(self._dati) and self._dati[i] == valore:
            del self._dati[i]
        else:
            raise ValueError(f"{valore!r} non trovato")

    def __contains__(self, valore):
        i = bisect.bisect_left(self._dati, valore)
        return i < len(self._dati) and self._dati[i] == valore

    def __getitem__(self, indice):
        return self._dati[indice]

    def __len__(self):
        return len(self._dati)

    def __repr__(self):
        return f"SortedList({self._dati})"

sl = SortedList([5, 2, 8, 1, 9])
sl.add(3)
sl.add(7)
print(sl)         # SortedList([1, 2, 3, 5, 7, 8, 9])
print(3 in sl)    # True
print(sl[0])      # 1 (il minimo)
print(sl[-1])     # 9 (il massimo)
```

> **Nota:** per uso in produzione con inserimenti/rimozioni frequenti su grandi dataset, la libreria `sortedcontainers` (SortedList, SortedDict, SortedSet) offre implementazioni basate su B-tree con complessita O(log n) anche per l'inserimento, superando bisect+list che resta O(n) a causa del shift degli elementi.

### sortedcontainers in profondita

La libreria `sortedcontainers` (pure-Python, nessuna dipendenza C) implementa `SortedList`, `SortedDict` e `SortedSet` usando una struttura interna simile a un B-tree: una "lista di liste" dove i dati sono distribuiti in segmenti (chunk) di dimensione controllata. Ogni operazione di inserimento, rimozione e ricerca ha complessita O(log n). L'overhead di memoria e circa 4 byte per oggetto — trascurabile rispetto ai benefici.

#### SortedList

`SortedList` mantiene gli elementi sempre ordinati. Supporta l'accesso per indice in O(log n), lo slicing, e iterazione per intervallo con `irange()`.

```python
from sortedcontainers import SortedList

sl = SortedList([5, 2, 8, 1, 9, 3])
print(sl)         # SortedList([1, 2, 3, 5, 8, 9])

sl.add(4)
sl.add(7)
print(sl)         # SortedList([1, 2, 3, 4, 5, 7, 8, 9])

# Accesso per indice — O(log n)
print(sl[0])      # 1 (minimo)
print(sl[-1])     # 9 (massimo)
print(sl[3])      # 4

# Rimozione — O(log n)
sl.remove(5)
sl.discard(100)   # Non solleva errore se assente

# Ricerca per intervallo — O(log n + k), dove k = numero di risultati
print(list(sl.irange(3, 8)))  # [3, 4, 7, 8]

# Ricerca binaria: indice di inserimento
print(sl.bisect_left(4))   # 2 — indice dove 4 si trova/andrebbe
print(sl.bisect_right(4))  # 3

# Conteggio
print(sl.count(4))  # 1
```

#### SortedDict

`SortedDict` combina un dizionario hash-based con un indice ordinato sulle chiavi. Le operazioni di lookup per chiave restano O(1) in media (hash table), mentre l'iterazione e l'accesso per posizione sono O(log n).

```python
from sortedcontainers import SortedDict

sd = SortedDict({'banana': 3, 'mela': 7, 'arancia': 2, 'kiwi': 5})

# Iterazione gia ordinata per chiave
for chiave, valore in sd.items():
    print(f"{chiave}: {valore}")
# arancia: 2, banana: 3, kiwi: 5, mela: 7

# peekitem() — accesso al minimo/massimo senza rimozione
print(sd.peekitem(0))    # ('arancia', 2) — chiave minima
print(sd.peekitem(-1))   # ('mela', 7) — chiave massima

# popitem() — estrazione con rimozione
primo = sd.popitem(0)    # ('arancia', 2) — rimosso
print(sd)                # SortedDict({'banana': 3, 'kiwi': 5, 'mela': 7})

# Accesso per indice di chiave
print(sd.iloc[0])        # 'banana' — prima chiave
print(sd.iloc[-1])       # 'mela' — ultima chiave

# Intervallo di chiavi
print(list(sd.irange('b', 'l')))  # ['banana', 'kiwi']
```

#### SortedSet

`SortedSet` combina le proprieta di un `set` (unicita, operazioni insiemistiche) con l'ordinamento automatico.

```python
from sortedcontainers import SortedSet

ss = SortedSet([3, 1, 4, 1, 5, 9, 2, 6])
print(ss)         # SortedSet([1, 2, 3, 4, 5, 6, 9])

ss.add(7)
ss.discard(4)
print(ss)         # SortedSet([1, 2, 3, 5, 6, 7, 9])

# Operazioni insiemistiche — il risultato resta ordinato
ss2 = SortedSet([2, 4, 6, 8])
print(ss & ss2)   # SortedSet([2, 6])
print(ss | ss2)   # SortedSet([1, 2, 3, 4, 5, 6, 7, 8, 9])

# Accesso per indice
print(ss[0])      # 1 (minimo)
print(ss[-1])     # 9 (massimo)

# Iterazione per intervallo
print(list(ss.irange(3, 7)))  # [3, 5, 6, 7]
```

#### Ordinamento personalizzato con key

Tutte le strutture accettano un parametro `key` per definire l'ordinamento, analogo al `key` di `sorted()`.

```python
from sortedcontainers import SortedList

# Ordinamento per lunghezza della stringa
parole = SortedList(key=len)
parole.update(['mela', 'kiwi', 'banana', 'uva', 'arancia'])
print(parole)  # SortedList(['uva', 'mela', 'kiwi', 'banana', 'arancia'], key=<built-in function len>)

# Ordinamento inverso
numeri = SortedList(key=lambda x: -x)
numeri.update([3, 1, 4, 1, 5])
print(numeri)  # SortedList([5, 4, 3, 1, 1], key=...)
```

---

## frozenset e pattern immutabili

### frozenset in profondita

`frozenset` e la versione immutabile di `set`. Supporta tutte le operazioni degli insiemi (unione, intersezione, differenza) ma non puo essere modificato dopo la creazione.

```python
# Creazione
colori_primari = frozenset(['rosso', 'blu', 'giallo'])
colori_secondari = frozenset(['verde', 'arancione', 'viola'])

# Operazioni insiemistiche (restituiscono nuovi frozenset)
tutti = colori_primari | colori_secondari
comuni = colori_primari & colori_secondari   # frozenset() — vuoto

# Utilizzo come chiave di dizionario (impossibile con set)
gruppi = {
    frozenset(['Alice', 'Bob']): 'Squadra A',
    frozenset(['Carlo', 'Diana']): 'Squadra B',
}
print(gruppi[frozenset(['Alice', 'Bob'])])   # 'Squadra A'

# Utilizzo in insiemi di insiemi
insieme_di_insiemi = {frozenset([1, 2]), frozenset([3, 4]), frozenset([1, 2])}
print(len(insieme_di_insiemi))   # 2 — i duplicati vengono rimossi
```

### Pattern immutabili con frozenset

#### Configurazione di permessi

```python
# I permessi di un ruolo sono immutabili dopo la definizione
PERMESSI_ADMIN = frozenset(['read', 'write', 'delete', 'admin'])
PERMESSI_EDITOR = frozenset(['read', 'write'])
PERMESSI_VIEWER = frozenset(['read'])

def ha_permesso(ruolo_permessi: frozenset, azione: str) -> bool:
    return azione in ruolo_permessi

# Operazioni sugli insiemi per calcolare differenze
permessi_extra_admin = PERMESSI_ADMIN - PERMESSI_EDITOR
print(permessi_extra_admin)   # frozenset({'delete', 'admin'})

# frozenset come chiave per cache
cache_permessi: dict[frozenset[str], list[str]] = {}
cache_permessi[PERMESSI_EDITOR] = ['pagina_edit', 'dashboard']
```

#### Deduplicazione di insiemi

```python
# Problema: trovare combinazioni uniche di ingredienti
ricette = [
    {'pomodoro', 'mozzarella', 'basilico'},
    {'mozzarella', 'basilico', 'pomodoro'},  # stessa combinazione, ordine diverso
    {'prosciutto', 'mozzarella'},
    {'mozzarella', 'prosciutto'},              # duplicato
]

combinazioni_uniche = {frozenset(r) for r in ricette}
print(len(combinazioni_uniche))   # 2
for c in combinazioni_uniche:
    print(sorted(c))
```

---

## Alberi e Grafi

### Implementazione Albero Binario

Un albero binario e una struttura dati gerarchica in cui ogni nodo ha al massimo due figli. L'albero binario di ricerca (BST — Binary Search Tree) impone che il figlio sinistro contenga valori minori e il figlio destro valori maggiori.

#### Classe Nodo e operazioni BST

```python
from typing import Optional, List
from collections import deque

class NodoAlbero:
    def __init__(self, valore):
        self.valore = valore
        self.sinistro: Optional[NodoAlbero] = None
        self.destro: Optional[NodoAlbero] = None

class AlberoBinarioRicerca:
    def __init__(self):
        self.radice: Optional[NodoAlbero] = None

    def inserisci(self, valore) -> None:
        """Inserisce un valore nel BST."""
        if self.radice is None:
            self.radice = NodoAlbero(valore)
        else:
            self._inserisci_ricorsivo(self.radice, valore)

    def _inserisci_ricorsivo(self, nodo: NodoAlbero, valore) -> None:
        if valore < nodo.valore:
            if nodo.sinistro is None:
                nodo.sinistro = NodoAlbero(valore)
            else:
                self._inserisci_ricorsivo(nodo.sinistro, valore)
        elif valore > nodo.valore:
            if nodo.destro is None:
                nodo.destro = NodoAlbero(valore)
            else:
                self._inserisci_ricorsivo(nodo.destro, valore)
        # Valori duplicati vengono ignorati

    def cerca(self, valore) -> bool:
        """Restituisce True se il valore esiste nel BST."""
        return self._cerca_ricorsivo(self.radice, valore)

    def _cerca_ricorsivo(self, nodo: Optional[NodoAlbero], valore) -> bool:
        if nodo is None:
            return False
        if valore == nodo.valore:
            return True
        elif valore < nodo.valore:
            return self._cerca_ricorsivo(nodo.sinistro, valore)
        else:
            return self._cerca_ricorsivo(nodo.destro, valore)

    # --- Attraversamenti ---

    def inorder(self) -> List:
        """Attraversamento in-order (sinistro, radice, destro) — produce valori ordinati."""
        risultato = []
        self._inorder(self.radice, risultato)
        return risultato

    def _inorder(self, nodo: Optional[NodoAlbero], risultato: List) -> None:
        if nodo:
            self._inorder(nodo.sinistro, risultato)
            risultato.append(nodo.valore)
            self._inorder(nodo.destro, risultato)

    def preorder(self) -> List:
        """Attraversamento pre-order (radice, sinistro, destro)."""
        risultato = []
        self._preorder(self.radice, risultato)
        return risultato

    def _preorder(self, nodo: Optional[NodoAlbero], risultato: List) -> None:
        if nodo:
            risultato.append(nodo.valore)
            self._preorder(nodo.sinistro, risultato)
            self._preorder(nodo.destro, risultato)

    def postorder(self) -> List:
        """Attraversamento post-order (sinistro, destro, radice)."""
        risultato = []
        self._postorder(self.radice, risultato)
        return risultato

    def _postorder(self, nodo: Optional[NodoAlbero], risultato: List) -> None:
        if nodo:
            self._postorder(nodo.sinistro, risultato)
            self._postorder(nodo.destro, risultato)
            risultato.append(nodo.valore)

    def bfs(self) -> List:
        """Attraversamento in ampiezza (BFS — Breadth-First Search)."""
        if self.radice is None:
            return []
        risultato = []
        coda = deque([self.radice])
        while coda:
            nodo = coda.popleft()
            risultato.append(nodo.valore)
            if nodo.sinistro:
                coda.append(nodo.sinistro)
            if nodo.destro:
                coda.append(nodo.destro)
        return risultato

# Utilizzo
bst = AlberoBinarioRicerca()
for v in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
    bst.inserisci(v)

print("In-order:  ", bst.inorder())    # [1, 3, 4, 6, 7, 8, 10, 13, 14]
print("Pre-order: ", bst.preorder())   # [8, 3, 1, 6, 4, 7, 10, 14, 13]
print("Post-order:", bst.postorder())  # [1, 4, 7, 6, 3, 13, 14, 10, 8]
print("BFS:       ", bst.bfs())        # [8, 3, 10, 1, 6, 14, 4, 7, 13]
print("Cerca 6:   ", bst.cerca(6))     # True
print("Cerca 15:  ", bst.cerca(15))    # False
```

---

### Implementazione Grafo

Un grafo e composto da nodi (vertici) e archi (connessioni tra i nodi). La rappresentazione piu comune in Python e la lista di adiacenza, implementata con un dizionario.

#### Rappresentazione con lista di adiacenza

```python
from collections import defaultdict, deque
from typing import Dict, List, Set, Optional, Tuple
import heapq

class Grafo:
    def __init__(self, orientato: bool = False):
        self.adiacenza: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.orientato = orientato

    def aggiungi_arco(self, origine: str, destinazione: str, peso: float = 1.0) -> None:
        """Aggiunge un arco al grafo."""
        self.adiacenza[origine].append((destinazione, peso))
        if not self.orientato:
            self.adiacenza[destinazione].append((origine, peso))
        # Assicura che il nodo destinazione esista nel grafo
        if destinazione not in self.adiacenza:
            self.adiacenza[destinazione] = []

    def bfs(self, partenza: str) -> List[str]:
        """Attraversamento in ampiezza (BFS)."""
        visitati: Set[str] = set()
        coda = deque([partenza])
        visitati.add(partenza)
        ordine = []

        while coda:
            nodo = coda.popleft()
            ordine.append(nodo)
            for vicino, _ in self.adiacenza[nodo]:
                if vicino not in visitati:
                    visitati.add(vicino)
                    coda.append(vicino)
        return ordine

    def dfs(self, partenza: str) -> List[str]:
        """Attraversamento in profondita (DFS) — versione iterativa."""
        visitati: Set[str] = set()
        stack = [partenza]
        ordine = []

        while stack:
            nodo = stack.pop()
            if nodo not in visitati:
                visitati.add(nodo)
                ordine.append(nodo)
                # Aggiungi i vicini in ordine inverso per visitarli nell'ordine naturale
                for vicino, _ in reversed(self.adiacenza[nodo]):
                    if vicino not in visitati:
                        stack.append(vicino)
        return ordine

    def dijkstra(self, partenza: str) -> Dict[str, Tuple[float, List[str]]]:
        """
        Algoritmo di Dijkstra per il cammino minimo.
        Restituisce un dizionario {nodo: (distanza, percorso)}.
        """
        distanze: Dict[str, float] = {nodo: float('inf') for nodo in self.adiacenza}
        distanze[partenza] = 0
        predecessori: Dict[str, Optional[str]] = {nodo: None for nodo in self.adiacenza}
        heap = [(0, partenza)]
        visitati: Set[str] = set()

        while heap:
            distanza_corrente, nodo_corrente = heapq.heappop(heap)

            if nodo_corrente in visitati:
                continue
            visitati.add(nodo_corrente)

            for vicino, peso in self.adiacenza[nodo_corrente]:
                nuova_distanza = distanza_corrente + peso
                if nuova_distanza < distanze[vicino]:
                    distanze[vicino] = nuova_distanza
                    predecessori[vicino] = nodo_corrente
                    heapq.heappush(heap, (nuova_distanza, vicino))

        # Ricostruisci i percorsi
        risultato = {}
        for nodo in self.adiacenza:
            percorso = []
            corrente = nodo
            while corrente is not None:
                percorso.append(corrente)
                corrente = predecessori[corrente]
            percorso.reverse()
            risultato[nodo] = (distanze[nodo], percorso)

        return risultato

    def __repr__(self) -> str:
        linee = []
        for nodo, vicini in self.adiacenza.items():
            connessioni = ', '.join(f"{v}({p})" for v, p in vicini)
            linee.append(f"  {nodo} -> [{connessioni}]")
        return "Grafo:\n" + "\n".join(linee)

# Utilizzo
g = Grafo(orientato=False)
g.aggiungi_arco('Roma', 'Firenze', 270)
g.aggiungi_arco('Roma', 'Napoli', 225)
g.aggiungi_arco('Firenze', 'Bologna', 105)
g.aggiungi_arco('Bologna', 'Milano', 215)
g.aggiungi_arco('Firenze', 'Milano', 305)
g.aggiungi_arco('Napoli', 'Bari', 265)

print("BFS da Roma:", g.bfs('Roma'))
print("DFS da Roma:", g.dfs('Roma'))

print("\nCammini minimi da Roma (Dijkstra):")
cammini = g.dijkstra('Roma')
for citta, (distanza, percorso) in cammini.items():
    print(f"  {citta}: {distanza} km — {' -> '.join(percorso)}")
```

#### Panoramica della libreria networkx

Per grafi complessi, la libreria `networkx` offre un'API ricca e algoritmi avanzati:

```python
# pip install networkx
import networkx as nx

# Creazione del grafo
G = nx.Graph()
G.add_weighted_edges_from([
    ('Roma', 'Firenze', 270),
    ('Roma', 'Napoli', 225),
    ('Firenze', 'Bologna', 105),
    ('Bologna', 'Milano', 215),
])

# Cammino minimo
percorso = nx.shortest_path(G, 'Roma', 'Milano', weight='weight')
distanza = nx.shortest_path_length(G, 'Roma', 'Milano', weight='weight')
print(f"Percorso: {' -> '.join(percorso)}, Distanza: {distanza}")

# Proprieta del grafo
print(f"Nodi: {G.number_of_nodes()}")
print(f"Archi: {G.number_of_edges()}")
print(f"Grado di Roma: {G.degree('Roma')}")
print(f"Connesso: {nx.is_connected(G)}")

# Algoritmi avanzati
centralita = nx.betweenness_centrality(G)
print(f"Centralita: {centralita}")
```

`networkx` supporta grafi orientati (`DiGraph`), multigrafi, attributi su nodi e archi, e decine di algoritmi (componenti connesse, cicli euleriani, flusso massimo, isomorfismo e molto altro).

---

## Strutture Dati Funzionali

Le strutture dati immutabili sono fondamentali nella programmazione funzionale e offrono vantaggi in termini di sicurezza, prevedibilita e possibilita di utilizzo come chiavi di dizionari o elementi di insiemi.

### frozenset

`frozenset` e la versione immutabile di `set`. Supporta tutte le operazioni degli insiemi (unione, intersezione, differenza) ma non puo essere modificato dopo la creazione.

```python
# Creazione
colori_primari = frozenset(['rosso', 'blu', 'giallo'])
colori_secondari = frozenset(['verde', 'arancione', 'viola'])

# Operazioni insiemistiche (restituiscono nuovi frozenset)
tutti = colori_primari | colori_secondari
comuni = colori_primari & colori_secondari   # frozenset() — vuoto

# Utilizzo come chiave di dizionario (impossibile con set)
gruppi = {
    frozenset(['Alice', 'Bob']): 'Squadra A',
    frozenset(['Carlo', 'Diana']): 'Squadra B',
}
print(gruppi[frozenset(['Alice', 'Bob'])])   # 'Squadra A'

# Utilizzo in insiemi di insiemi
insieme_di_insiemi = {frozenset([1, 2]), frozenset([3, 4]), frozenset([1, 2])}
print(len(insieme_di_insiemi))   # 2 — i duplicati vengono rimossi
```

### tuple come record immutabile

Le tuple sono la struttura dati immutabile piu semplice di Python. Combinate con l'unpacking, fungono da record leggeri:

```python
# Tuple come record
coordinate = (45.4642, 9.1900)   # Milano
latitudine, longitudine = coordinate

# Tuple con nome (namedtuple) per maggiore chiarezza
# (vedi sezione namedtuple sopra)

# Tuple come chiavi composte di dizionario
griglia = {}
griglia[(0, 0)] = 'origine'
griglia[(1, 2)] = 'punto A'

# Tuple immutabili in contesti funzionali
def trasla(punto: tuple, dx: float, dy: float) -> tuple:
    """Restituisce un nuovo punto traslato (non modifica l'originale)."""
    return (punto[0] + dx, punto[1] + dy)

p1 = (3.0, 4.0)
p2 = trasla(p1, 1.0, -2.0)
print(p1)   # (3.0, 4.0) — invariato
print(p2)   # (4.0, 2.0) — nuovo punto
```

### types.MappingProxyType (dizionario in sola lettura)

`MappingProxyType` crea una vista di sola lettura su un dizionario esistente, impedendo modifiche accidentali.

```python
from types import MappingProxyType

# Dizionario originale (modificabile)
_configurazione = {
    'database': 'postgresql',
    'host': 'localhost',
    'porta': 5432,
    'max_connessioni': 20
}

# Vista di sola lettura
configurazione = MappingProxyType(_configurazione)

# Lettura consentita
print(configurazione['database'])   # 'postgresql'
print(configurazione.get('porta'))  # 5432
print(len(configurazione))          # 4

# Scrittura vietata
try:
    configurazione['porta'] = 3306   # TypeError
except TypeError as e:
    print(f"Errore: {e}")

# Le modifiche al dizionario originale si riflettono nella vista
_configurazione['max_connessioni'] = 50
print(configurazione['max_connessioni'])   # 50
```

Questo pattern e utile per esporre configurazioni o dati interni di una classe senza rischiare modifiche indesiderate dall'esterno.

### Collezioni immutabili persistenti con pyrsistent

La libreria `pyrsistent` implementa strutture dati *persistenti* (nel senso funzionale): ogni modifica restituisce una nuova versione della struttura, mentre la precedente resta intatta e accessibile. Internamente usa *hash array mapped tries* (HAMT) con un branching factor di 32, ottenendo complessita O(log32 n) per accesso e aggiornamento — in pratica quasi O(1) per dataset realistici. L'implementazione include un'estensione C che la rende 2-20 volte piu veloce della controparte pure-Python.

#### PVector — lista immutabile

`PVector` e l'equivalente immutabile di `list`. L'append e ammortizzato O(1), l'accesso per indice e O(log32 n), e ogni operazione restituisce un nuovo vettore senza copiare l'intera struttura (structural sharing).

```python
from pyrsistent import pvector

v1 = pvector([1, 2, 3, 4, 5])
v2 = v1.append(6)           # Nuovo vettore: [1, 2, 3, 4, 5, 6]
v3 = v1.set(0, 99)          # Nuovo vettore: [99, 2, 3, 4, 5]

print(v1)  # pvector([1, 2, 3, 4, 5]) — invariato
print(v2)  # pvector([1, 2, 3, 4, 5, 6])
print(v3)  # pvector([99, 2, 3, 4, 5])

# Slicing, iterazione, len() funzionano come per le liste
print(v2[3])     # 4
print(len(v2))   # 6
```

#### PMap — dizionario immutabile

`PMap` e l'equivalente immutabile di `dict`. Ogni `set()` o `remove()` restituisce un nuovo mapping. A differenza di `MappingProxyType`, `PMap` e una struttura dati indipendente — non una vista su un dizionario mutabile.

```python
from pyrsistent import pmap

m1 = pmap({'host': 'localhost', 'porta': 5432})
m2 = m1.set('porta', 3306)
m3 = m2.set('database', 'produzione')

print(m1)  # pmap({'host': 'localhost', 'porta': 5432}) — invariato
print(m3)  # pmap({'host': 'localhost', 'porta': 3306, 'database': 'produzione'})

# Rimozione di chiave
m4 = m3.remove('database')
print(m4)  # pmap({'host': 'localhost', 'porta': 3306})
```

#### PSet — insieme immutabile

`PSet` e l'equivalente persistente di `frozenset`, con l'aggiunta di operazioni `.add()` e `.remove()` che restituiscono nuovi insiemi.

```python
from pyrsistent import pset

s1 = pset([1, 2, 3])
s2 = s1.add(4)
s3 = s1.remove(2)

print(s1)  # pset([1, 2, 3]) — invariato
print(s2)  # pset([1, 2, 3, 4])
print(s3)  # pset([1, 3])
```

#### Evolver — mutazione transazionale

Quando serve costruire una struttura immutabile con molte modifiche consecutive, creare un nuovo oggetto per ogni operazione sarebbe inefficiente. L'*evolver* fornisce un'interfaccia mutabile temporanea che alla fine produce un'unica versione immutabile.

```python
from pyrsistent import pvector, pmap

# Evolver per PVector
v = pvector([1, 2, 3])
e = v.evolver()
e.append(4)
e.append(5)
e[0] = 10
v2 = e.persistent()  # Materializza il risultato
print(v2)  # pvector([10, 2, 3, 4, 5])
print(v)   # pvector([1, 2, 3]) — invariato

# Evolver per PMap
m = pmap({'a': 1, 'b': 2})
e = m.evolver()
e['c'] = 3
e['a'] = 100
del e['b']
m2 = e.persistent()
print(m2)  # pmap({'a': 100, 'c': 3})
```

#### freeze e thaw — conversione bidirezionale

`freeze()` converte ricorsivamente strutture Python mutabili nelle corrispondenti strutture pyrsistent. `thaw()` esegue la conversione inversa.

```python
from pyrsistent import freeze, thaw

dati_mutabili = {
    'utenti': [
        {'nome': 'Alice', 'ruoli': ['admin', 'editor']},
        {'nome': 'Bob', 'ruoli': ['viewer']},
    ]
}

immutabile = freeze(dati_mutabili)
# PMap con PVector annidati — completamente immutabile
print(type(immutabile))             # <class 'pyrsistent._pmap.PMap'>
print(type(immutabile['utenti']))   # <class 'pyrsistent._pvector.PVector'>

# Riconversione per interoperare con API che richiedono tipi nativi
mutabile = thaw(immutabile)
print(type(mutabile))  # <class 'dict'>
```

#### Quando usare pyrsistent

| Scenario | Consigliato |
|----------|-------------|
| Undo/redo (mantenere versioni precedenti) | Si — structural sharing rende economico |
| Dati condivisi tra thread senza lock | Si — l'immutabilita elimina le race condition |
| Configurazioni immutabili con aggiornamenti frequenti | Si — evolver per batch, poi persistent() |
| Hot path con milioni di operazioni al secondo | Valutare — il costo O(log32 n) puo non essere trascurabile |
| Interoperabilita con API che richiedono dict/list | Usare thaw() al confine, freeze() internamente |

---

## Strutture Specializzate

### Trie (Prefix Tree)

Un trie (prefix tree) e una struttura dati ad albero in cui ogni nodo rappresenta un carattere di una stringa. I trie eccellono nella ricerca per prefisso, nell'autocompletamento e nella verifica di appartenenza di parole a un vocabolario. La complessita di ricerca e O(m), dove m e la lunghezza della stringa cercata, indipendente dal numero di parole nel trie.

```python
from typing import Optional

class NodoTrie:
    __slots__ = ('figli', 'fine_parola', 'conteggio')

    def __init__(self):
        self.figli: dict[str, NodoTrie] = {}
        self.fine_parola: bool = False
        self.conteggio: int = 0   # quante parole passano per questo nodo

class Trie:
    def __init__(self):
        self.radice = NodoTrie()

    def inserisci(self, parola: str) -> None:
        nodo = self.radice
        for carattere in parola:
            if carattere not in nodo.figli:
                nodo.figli[carattere] = NodoTrie()
            nodo = nodo.figli[carattere]
            nodo.conteggio += 1
        nodo.fine_parola = True

    def cerca(self, parola: str) -> bool:
        """Restituisce True se la parola esatta esiste nel trie."""
        nodo = self._trova_nodo(parola)
        return nodo is not None and nodo.fine_parola

    def inizia_con(self, prefisso: str) -> bool:
        """Restituisce True se esiste almeno una parola con questo prefisso."""
        return self._trova_nodo(prefisso) is not None

    def conta_con_prefisso(self, prefisso: str) -> int:
        """Conta le parole che iniziano con il prefisso dato."""
        nodo = self._trova_nodo(prefisso)
        return nodo.conteggio if nodo else 0

    def autocompletamento(self, prefisso: str, max_risultati: int = 10) -> list[str]:
        """Restituisce le parole che iniziano con il prefisso dato."""
        nodo = self._trova_nodo(prefisso)
        if nodo is None:
            return []
        risultati: list[str] = []
        self._raccogli_parole(nodo, prefisso, risultati, max_risultati)
        return risultati

    def _trova_nodo(self, prefisso: str) -> Optional[NodoTrie]:
        nodo = self.radice
        for carattere in prefisso:
            if carattere not in nodo.figli:
                return None
            nodo = nodo.figli[carattere]
        return nodo

    def _raccogli_parole(
        self, nodo: NodoTrie, prefisso: str,
        risultati: list[str], max_risultati: int
    ) -> None:
        if len(risultati) >= max_risultati:
            return
        if nodo.fine_parola:
            risultati.append(prefisso)
        for carattere in sorted(nodo.figli):
            self._raccogli_parole(
                nodo.figli[carattere], prefisso + carattere,
                risultati, max_risultati
            )

# Utilizzo
vocabolario = Trie()
parole = ["python", "programmazione", "programma", "progetto",
          "prova", "produzione", "pandas", "pip"]

for p in parole:
    vocabolario.inserisci(p)

print(vocabolario.cerca("python"))              # True
print(vocabolario.cerca("pyth"))                # False
print(vocabolario.inizia_con("pro"))            # True
print(vocabolario.conta_con_prefisso("pro"))    # 4
print(vocabolario.autocompletamento("pro"))
# ['produzione', 'progetto', 'programma', 'programmazione', 'prova']
```

**Quando usare un trie:** autocompletamento, spell checking, prefix matching su grandi vocabolari, routing di URL, analisi lessicale. Per la semplice verifica di appartenenza senza necessita di ricerca per prefisso, un `set` e piu semplice e spesso piu veloce.

### Bloom Filter

Un bloom filter e una struttura dati probabilistica che risponde alla domanda "questo elemento e nel set?" con due possibili risposte: "probabilmente si" o "sicuramente no". Non produce falsi negativi, ma puo produrre falsi positivi con una probabilita controllabile. Occupa una quantita di memoria fissa, indipendente dal numero di elementi.

```python
import hashlib
import math
from typing import Any

class BloomFilter:
    """Bloom filter con tasso di falsi positivi configurabile."""

    def __init__(self, capacita_attesa: int, tasso_falsi_positivi: float = 0.01):
        # Calcolo dimensione ottimale del bit array
        # Formula: m = -(n * ln(p)) / (ln(2))^2
        self.dimensione = self._calcola_dimensione(capacita_attesa, tasso_falsi_positivi)
        # Numero ottimale di funzioni hash
        # Formula: k = (m/n) * ln(2)
        self.num_hash = self._calcola_num_hash(self.dimensione, capacita_attesa)
        self.bit_array = bytearray(self.dimensione)
        self._conteggio = 0

    @staticmethod
    def _calcola_dimensione(n: int, p: float) -> int:
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m) + 1

    @staticmethod
    def _calcola_num_hash(m: int, n: int) -> int:
        k = (m / n) * math.log(2)
        return max(1, int(k))

    def _hash_values(self, elemento: Any) -> list[int]:
        """Genera k posizioni hash per l'elemento."""
        posizioni = []
        for i in range(self.num_hash):
            h = hashlib.sha256(f"{elemento}:{i}".encode()).hexdigest()
            posizioni.append(int(h, 16) % self.dimensione)
        return posizioni

    def aggiungi(self, elemento: Any) -> None:
        for pos in self._hash_values(elemento):
            self.bit_array[pos] = 1
        self._conteggio += 1

    def potrebbe_contenere(self, elemento: Any) -> bool:
        """True = probabilmente presente; False = sicuramente assente."""
        return all(self.bit_array[pos] for pos in self._hash_values(elemento))

    @property
    def elementi_inseriti(self) -> int:
        return self._conteggio

# Utilizzo
bf = BloomFilter(capacita_attesa=10_000, tasso_falsi_positivi=0.01)

# Inserire URL gia visitati
url_visitati = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]
for url in url_visitati:
    bf.aggiungi(url)

# Verificare se un URL e gia stato visitato
print(bf.potrebbe_contenere("https://example.com/page1"))   # True
print(bf.potrebbe_contenere("https://example.com/page99"))  # False (sicuramente no)
print(bf.potrebbe_contenere("https://example.com/page2"))   # True
```

**Quando usare un bloom filter:** deduplicazione di URL in web crawler, cache lookup negativo (evitare query al database per chiavi sicuramente assenti), rilevamento di spam, sistemi di raccomandazione (filtrare contenuti gia visti). La libreria `pybloom-live` offre un'implementazione pronta per la produzione con auto-scaling.

---

## Algoritmi Fondamentali

### Ricerca

#### Ricerca lineare

La ricerca lineare scorre ogni elemento della sequenza fino a trovare quello cercato. Ha complessita O(n).

```python
def ricerca_lineare(sequenza, obiettivo):
    """Restituisce l'indice dell'obiettivo o -1 se non trovato."""
    for i, elemento in enumerate(sequenza):
        if elemento == obiettivo:
            return i
    return -1

dati = [15, 3, 28, 7, 42, 11]
print(ricerca_lineare(dati, 42))   # 4
print(ricerca_lineare(dati, 99))   # -1
```

#### Ricerca binaria e modulo bisect

La ricerca binaria opera su sequenze ordinate e ha complessita O(log n). Il modulo `bisect` fornisce un'implementazione efficiente scritta in C.

```python
import bisect

# Ricerca binaria manuale
def ricerca_binaria(sequenza_ordinata, obiettivo):
    """Restituisce l'indice dell'obiettivo o -1 se non trovato."""
    sinistra, destra = 0, len(sequenza_ordinata) - 1
    while sinistra <= destra:
        centro = (sinistra + destra) // 2
        if sequenza_ordinata[centro] == obiettivo:
            return centro
        elif sequenza_ordinata[centro] < obiettivo:
            sinistra = centro + 1
        else:
            destra = centro - 1
    return -1

# Utilizzo del modulo bisect
dati_ordinati = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]

# bisect_left — trova il punto di inserimento a sinistra
pos = bisect.bisect_left(dati_ordinati, 23)
print(pos)   # 5

# Verifica se l'elemento esiste
def cerca_con_bisect(sequenza, obiettivo):
    pos = bisect.bisect_left(sequenza, obiettivo)
    if pos < len(sequenza) and sequenza[pos] == obiettivo:
        return pos
    return -1

print(cerca_con_bisect(dati_ordinati, 23))   # 5
print(cerca_con_bisect(dati_ordinati, 24))   # -1

# insort — inserisce mantenendo l'ordine
bisect.insort(dati_ordinati, 20)
print(dati_ordinati)
# [2, 5, 8, 12, 16, 20, 23, 38, 56, 72, 91]

# Caso d'uso: assegnazione di voti basata su soglie
def assegna_voto(punteggio):
    soglie = [60, 70, 80, 90]
    voti = ['F', 'D', 'C', 'B', 'A']
    indice = bisect.bisect(soglie, punteggio)
    return voti[indice]

punteggi = [33, 65, 77, 85, 92]
for p in punteggi:
    print(f"Punteggio {p}: Voto {assegna_voto(p)}")
```

---

### Ordinamento

#### sorted() e Timsort

La funzione `sorted()` di Python utilizza internamente l'algoritmo Timsort, un algoritmo ibrido che combina merge sort e insertion sort. Ha complessita O(n log n) nel caso peggiore e O(n) nel caso migliore (dati gia quasi ordinati).

```python
# Ordinamento base
numeri = [3, 1, 4, 1, 5, 9, 2, 6]
ordinati = sorted(numeri)              # Nuova lista: [1, 1, 2, 3, 4, 5, 6, 9]
numeri.sort()                           # In-place

# Ordinamento inverso
decrescente = sorted(numeri, reverse=True)

# Funzione key
parole = ['banana', 'Mela', 'ciliegia', 'Dattero']
per_lunghezza = sorted(parole, key=len)
case_insensitive = sorted(parole, key=str.lower)
```

#### Stabilita di sorted() e Timsort

Timsort e un algoritmo **stabile**: gli elementi con la stessa chiave mantengono l'ordine relativo che avevano nella sequenza originale. Questa proprieta e fondamentale perche permette di ottenere ordinamenti multi-criterio concatenando piu chiamate a `sort()`.

```python
from operator import itemgetter

record = [
    ("Alice", "IT", 55000),
    ("Bob", "HR", 48000),
    ("Carlo", "IT", 62000),
    ("Diana", "HR", 51000),
    ("Elena", "IT", 55000),
]

# Ordinamento stabile multi-criterio: prima per stipendio (asc), poi per reparto (asc)
# Siccome sort e stabile, si ordina PRIMA per il criterio secondario, POI per il primario
record_ordinati = sorted(record, key=itemgetter(2))        # per stipendio
record_ordinati = sorted(record_ordinati, key=itemgetter(1))  # per reparto

for r in record_ordinati:
    print(f"  {r[1]} — {r[0]}: {r[2]}")
# HR — Bob: 48000
# HR — Diana: 51000
# IT — Alice: 55000
# IT — Elena: 55000    ← Alice prima di Elena: ordine originale preservato
# IT — Carlo: 62000
```

#### Ordinamento con chiavi personalizzate

```python
from operator import itemgetter, attrgetter

# Lista di dizionari
dipendenti = [
    {'nome': 'Alice', 'reparto': 'IT', 'stipendio': 55000},
    {'nome': 'Bob', 'reparto': 'HR', 'stipendio': 48000},
    {'nome': 'Carlo', 'reparto': 'IT', 'stipendio': 62000},
    {'nome': 'Diana', 'reparto': 'HR', 'stipendio': 51000},
]

# Ordinamento per stipendio
per_stipendio = sorted(dipendenti, key=itemgetter('stipendio'))

# Ordinamento multi-livello: prima per reparto, poi per stipendio decrescente
multi = sorted(dipendenti, key=lambda d: (d['reparto'], -d['stipendio']))
for d in multi:
    print(f"  {d['reparto']} — {d['nome']}: {d['stipendio']}")

# Ordinamento stabile — mantiene l'ordine relativo degli elementi uguali
# Questo permette di concatenare piu sort()
dipendenti.sort(key=itemgetter('stipendio'), reverse=True)
dipendenti.sort(key=itemgetter('reparto'))
# Risultato: ordinati per reparto, e all'interno di ogni reparto per stipendio decrescente

# Ordinamento personalizzato con functools.cmp_to_key
from functools import cmp_to_key

def confronta_versioni(v1: str, v2: str) -> int:
    """Confronta stringhe di versione come '1.2.3' e '1.10.1'."""
    parti1 = [int(x) for x in v1.split('.')]
    parti2 = [int(x) for x in v2.split('.')]
    for a, b in zip(parti1, parti2):
        if a < b:
            return -1
        if a > b:
            return 1
    return len(parti1) - len(parti2)

versioni = ['1.10.1', '1.2.3', '2.0.0', '1.2.10', '1.2.3']
ordinate = sorted(versioni, key=cmp_to_key(confronta_versioni))
print(ordinate)   # ['1.2.3', '1.2.3', '1.2.10', '1.10.1', '2.0.0']
```

#### operator.itemgetter e attrgetter in dettaglio

`operator.itemgetter` e `operator.attrgetter` sono callable factory dal modulo `operator` che creano funzioni di accesso ottimizzate, piu veloci delle lambda equivalenti perche implementate in C.

```python
from operator import itemgetter, attrgetter
from dataclasses import dataclass

# itemgetter — accesso per indice o chiave
get_nome = itemgetter('nome')
get_nome_e_stipendio = itemgetter('nome', 'stipendio')  # restituisce una tupla

d = {'nome': 'Alice', 'stipendio': 55000, 'reparto': 'IT'}
print(get_nome(d))               # 'Alice'
print(get_nome_e_stipendio(d))   # ('Alice', 55000)

# Ordinamento multi-chiave con singola itemgetter
dipendenti = [
    {'nome': 'Alice', 'reparto': 'IT', 'stipendio': 55000},
    {'nome': 'Bob', 'reparto': 'HR', 'stipendio': 48000},
    {'nome': 'Carlo', 'reparto': 'IT', 'stipendio': 62000},
]
# Ordina per reparto (asc), poi per stipendio (asc)
ordinati = sorted(dipendenti, key=itemgetter('reparto', 'stipendio'))

# attrgetter — accesso per attributo (per oggetti)
@dataclass
class Prodotto:
    nome: str
    prezzo: float
    categoria: str

prodotti = [
    Prodotto("Laptop", 999.0, "Elettronica"),
    Prodotto("Libro", 15.0, "Cultura"),
    Prodotto("Mouse", 25.0, "Elettronica"),
]

# Ordina per categoria, poi per prezzo
ordinati = sorted(prodotti, key=attrgetter('categoria', 'prezzo'))
for p in ordinati:
    print(f"  {p.categoria} — {p.nome}: {p.prezzo}")
```

---

### Hashing

L'hashing e il meccanismo fondamentale dietro dizionari e insiemi in Python. Comprendere il contratto tra `__hash__` e `__eq__` e essenziale per creare oggetti personalizzati utilizzabili come chiavi di dizionari o elementi di insiemi.

#### Il contratto __hash__ e __eq__

Le regole fondamentali sono:
1. Se `a == b`, allora `hash(a) == hash(b)` (obbligatorio).
2. Se `hash(a) == hash(b)`, non e necessario che `a == b` (collisione ammessa).
3. Un oggetto deve essere immutabile per essere hashable in modo affidabile.

```python
class Moneta:
    def __init__(self, valore: int, valuta: str):
        self.valore = valore
        self.valuta = valuta

    def __eq__(self, other):
        if not isinstance(other, Moneta):
            return NotImplemented
        return self.valore == other.valore and self.valuta == other.valuta

    def __hash__(self):
        return hash((self.valore, self.valuta))

    def __repr__(self):
        return f"Moneta({self.valore}, '{self.valuta}')"

# Utilizzo come chiave di dizionario
tassi_cambio = {
    Moneta(1, 'EUR'): 1.0,
    Moneta(1, 'USD'): 0.92,
    Moneta(1, 'GBP'): 1.17,
}

chiave = Moneta(1, 'EUR')
print(tassi_cambio[chiave])   # 1.0

# Utilizzo in un insieme
portafoglio = {Moneta(1, 'EUR'), Moneta(5, 'EUR'), Moneta(1, 'EUR')}
print(len(portafoglio))   # 2 — il duplicato viene rimosso
```

#### Collisioni hash

Le collisioni si verificano quando due oggetti diversi producono lo stesso valore hash. Python le gestisce internamente (i dizionari usano open addressing), ma un'eccessiva frequenza di collisioni degrada le prestazioni da O(1) a O(n).

```python
# Esempio di collisione intenzionale (a scopo didattico)
class CollideSempre:
    def __init__(self, valore):
        self.valore = valore

    def __hash__(self):
        return 42  # Stesso hash per tutti — pessimo

    def __eq__(self, other):
        return isinstance(other, CollideSempre) and self.valore == other.valore

# Funziona, ma le prestazioni del dizionario degradano a O(n)
d = {CollideSempre(i): i for i in range(100)}
```

Una buona funzione hash deve:
- Distribuire i valori uniformemente nello spazio hash.
- Essere veloce da calcolare.
- Considerare tutti gli attributi significativi dell'oggetto.
- Rispettare il contratto con `__eq__`.

### Pattern avanzati per oggetti hashable

#### dataclass con frozen=True — hash automatico

Quando si usa `@dataclass(frozen=True)`, Python genera automaticamente `__hash__` e `__eq__` basati su tutti i campi. Questo e il modo piu sicuro e idiomatico per creare oggetti hashable.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Coordinata:
    latitudine: float
    longitudine: float
    altitudine: float = 0.0

# Hash generato automaticamente da tutti i campi
c1 = Coordinata(45.4642, 9.1900)
c2 = Coordinata(45.4642, 9.1900)

print(c1 == c2)         # True
print(hash(c1) == hash(c2))  # True (stessi valori = stesso hash)

# Utilizzabile come chiave di dizionario
distanze = {
    Coordinata(45.4642, 9.1900): "Milano",
    Coordinata(41.9028, 12.4964): "Roma",
}
print(distanze[Coordinata(41.9028, 12.4964)])  # Roma
```

#### Hash selettivo: escludere campi dall'uguaglianza

In alcuni casi, certi campi non devono partecipare al confronto di uguaglianza ne al calcolo dell'hash (ad esempio, campi di cache, timestamp, o metadati).

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Documento:
    titolo: str
    contenuto: str
    # Escluso da __eq__ e __hash__
    data_accesso: str = field(compare=False, hash=False, default="")

d1 = Documento("Contratto", "Testo...", "2026-01-01")
d2 = Documento("Contratto", "Testo...", "2026-05-24")
print(d1 == d2)  # True — data_accesso ignorata
```

#### Rendere una classe esplicitamente non-hashable

Se una classe mutabile non deve essere usata come chiave di dizionario o elemento di set, impostare `__hash__ = None` causa un `TypeError` chiaro.

```python
class Buffer:
    __hash__ = None  # Esplicitamente non-hashable

    def __init__(self, dati: list):
        self.dati = dati

    def __eq__(self, other):
        return isinstance(other, Buffer) and self.dati == other.dati

b = Buffer([1, 2, 3])
try:
    {b: "valore"}  # TypeError: unhashable type: 'Buffer'
except TypeError as e:
    print(f"Errore atteso: {e}")
```

#### Hash basato su tuple — pattern canonico

Per classi custom che non usano dataclass, il pattern piu sicuro e delegare l'hash a una tupla degli attributi significativi. Non usare XOR bit a bit (`^`) tra gli hash dei singoli campi: produce collisioni sistematiche quando i campi hanno lo stesso tipo.

```python
class Segmento:
    def __init__(self, inizio: float, fine: float, etichetta: str):
        self.inizio = inizio
        self.fine = fine
        self.etichetta = etichetta

    def __eq__(self, other):
        if not isinstance(other, Segmento):
            return NotImplemented
        return (self.inizio, self.fine, self.etichetta) == \
               (other.inizio, other.fine, other.etichetta)

    def __hash__(self):
        return hash((self.inizio, self.fine, self.etichetta))

    def __repr__(self):
        return f"Segmento({self.inizio}, {self.fine}, '{self.etichetta}')"

# Perche hash(tuple) e non XOR:
# hash(a) ^ hash(b) == hash(b) ^ hash(a) — simmetrico, troppe collisioni
# hash((a, b)) != hash((b, a)) — ordine preservato, distribuzione migliore
```

#### Il contratto hash-equality in pratica

Il contratto fondamentale e: **se `a == b`, allora `hash(a) == hash(b)`**. Il contrario non deve necessariamente valere (collisioni sono ammesse). Violare questo contratto causa bug silenziosi nei dizionari e negli insiemi — un oggetto inserito potrebbe non essere piu ritrovabile.

```python
# ERRORE COMUNE: __eq__ senza __hash__ coerente
class ErroreSubdolo:
    def __init__(self, nome: str, versione: int):
        self.nome = nome
        self.versione = versione

    def __eq__(self, other):
        # Confronta solo il nome
        return isinstance(other, ErroreSubdolo) and self.nome == other.nome

    def __hash__(self):
        # Hash usa nome E versione — viola il contratto!
        return hash((self.nome, self.versione))

a = ErroreSubdolo("lib", 1)
b = ErroreSubdolo("lib", 2)
print(a == b)             # True (confronto su nome)
print(hash(a) == hash(b)) # False! — contratto violato
s = {a}
print(b in s)             # Risultato imprevedibile — bug silenzioso
```

La regola pratica: gli attributi usati in `__hash__` devono essere un **sottoinsieme** (non un sovrainsieme) degli attributi usati in `__eq__`.

---

## Tabella comparativa delle prestazioni

### dict vs defaultdict vs Counter — operazioni comuni

| Operazione | `dict` | `defaultdict` | `Counter` |
|---|---|---|---|
| Creazione vuota | `{}` | `defaultdict(factory)` | `Counter()` |
| Accesso chiave esistente | O(1) | O(1) | O(1) |
| Accesso chiave mancante | `KeyError` | Crea default, O(1) | Restituisce `0`, O(1) |
| `setdefault()` | O(1) | Non necessario | Non necessario |
| Conteggio (incremento) | `d[k] = d.get(k, 0) + 1` | `d[k] += 1` | `c[k] += 1` o `c.update(iterable)` |
| Top-N per frequenza | Manuale: `sorted(d.items(), key=...)` | Manuale come dict | `c.most_common(n)` — ottimizzato con heapq |
| Somma di due contatori | Manuale | Manuale | `c1 + c2` |
| Intersezione / unione | Manuale | Manuale | `c1 & c2` / `c1 \| c2` |
| `total()` | `sum(d.values())` | `sum(d.values())` | `c.total()` (Python 3.10+) |
| Overhead di memoria | Baseline | ~uguale a dict | ~uguale a dict |

### Quando scegliere quale struttura

| Caso d'uso | Struttura consigliata |
|---|---|
| Lookup chiave-valore generico | `dict` |
| Raggruppamento (chiave -> lista di valori) | `defaultdict(list)` |
| Conteggio elementi | `Counter` |
| Conteggio + operazioni aritmetiche tra contatori | `Counter` |
| Indice inverso (chiave -> set di ID) | `defaultdict(set)` |
| Dizionario annidato a profondita arbitraria | `defaultdict(lambda: defaultdict(...))` |
| Confronto order-sensitive | `OrderedDict` |
| Configurazione a livelli/scope | `ChainMap` |
| Sottoclasse di dict con override consistente | `UserDict` |

### Complessita delle strutture principali

| Struttura | Accesso | Ricerca | Inserimento | Cancellazione | Note |
|---|---|---|---|---|---|
| `list` | O(1) idx | O(n) | O(1) append, O(n) insert | O(n) | Array dinamico |
| `deque` | O(n) idx | O(n) | O(1) entrambi i lati | O(1) entrambi i lati | Doubly-linked blocks |
| `dict` | O(1) avg | O(1) avg | O(1) avg | O(1) avg | Hash table |
| `set` | — | O(1) avg | O(1) avg | O(1) avg | Hash table |
| `heapq` | O(1) min | O(n) | O(log n) | O(log n) pop | Array-based binary heap |
| `bisect` (sorted list) | O(1) idx | O(log n) | O(n) | O(n) | Ricerca binaria + shift |
| `sortedcontainers.SortedList` | O(log n) | O(log n) | O(log n) | O(log n) | B-tree-like |

### dict vs OrderedDict vs SortedDict — confronto dettagliato

Da Python 3.7+ `dict` preserva l'ordine di inserimento, ma `OrderedDict` offre funzionalita aggiuntive: `move_to_end()`, confronto order-sensitive e supporto nativo per l'inversione. `SortedDict` da `sortedcontainers` mantiene le chiavi ordinate automaticamente per valore, non per ordine di inserimento.

| Caratteristica | `dict` | `OrderedDict` | `SortedDict` |
|---|---|---|---|
| Ordine | Inserimento (3.7+) | Inserimento (esplicito) | Per chiave (ordinato) |
| `move_to_end(key)` | No | Si | No (l'ordine dipende dal valore) |
| `popitem(last=True/False)` | Solo `last=True` (LIFO) | Si, entrambe le direzioni | `popitem()` / `peekitem()` con indice |
| Confronto `==` | Solo valori | Ordine + valori | Solo valori |
| Iterazione ordinata per chiave | `sorted(d)` — O(n log n) | `sorted(d)` — O(n log n) | Nativo — O(n) |
| Ricerca per intervallo (range) | Manuale | Manuale | `irange(min, max)` — O(log n + k) |
| k-esimo elemento per chiave | Manuale — O(n log n) | Manuale — O(n log n) | `sd.iloc[k]` — O(log n) |
| Inserimento | O(1) avg | O(1) avg | O(log n) |
| Cancellazione | O(1) avg | O(1) avg | O(log n) |
| Overhead di memoria | Baseline | ~1.5x dict (linked list interna) | ~2x dict (indice B-tree) |
| Dipendenza esterna | No | No (stdlib) | Si (`pip install sortedcontainers`) |

#### Quando scegliere quale

- **`dict`**: scelta predefinita per lookup chiave-valore. Ordine di inserimento sufficiente nella maggior parte dei casi.
- **`OrderedDict`**: quando serve `move_to_end()` (es. cache LRU manuale), confronto tra dizionari che deve rispettare l'ordine, o serializzazione dove l'ordine e semanticamente significativo.
- **`SortedDict`**: quando le chiavi devono restare ordinate per valore (es. serie temporali, intervalli, leaderboard). Le query per intervallo (`irange`) e l'accesso per indice (`iloc`) lo rendono ideale per dati che richiedono sia lookup O(1)-like sia ordinamento continuo.

```python
from sortedcontainers import SortedDict

# Serie temporale con chiavi timestamp ordinate
serie = SortedDict()
serie['2026-01-01'] = 100
serie['2026-03-15'] = 250
serie['2026-02-10'] = 180
serie['2026-04-20'] = 310

# Iterazione gia ordinata per chiave
for data, valore in serie.items():
    print(f"{data}: {valore}")
# 2026-01-01: 100, 2026-02-10: 180, 2026-03-15: 250, 2026-04-20: 310

# Query per intervallo: solo Q1 2026
q1 = list(serie.irange('2026-01-01', '2026-03-31'))
print(q1)  # ['2026-01-01', '2026-02-10', '2026-03-15']

# Accesso per indice: chiave piu recente
print(serie.iloc[-1])  # '2026-04-20'
```

---

## Efficienza di memoria: __slots__, array, struct, memoryview

### __slots__

Per default, ogni istanza di una classe Python ha un `__dict__` — un dizionario che mappa i nomi degli attributi ai loro valori. Questo dizionario consuma circa 100-200 byte per istanza vuota (piu 50-80 byte per ogni attributo). Quando si creano milioni di istanze con un set fisso di attributi, `__slots__` elimina il `__dict__` e alloca lo spazio per gli attributi direttamente nella struttura dell'oggetto.

```python
import sys

class PuntoConDict:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class PuntoConSlots:
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

p_dict = PuntoConDict(1.0, 2.0)
p_slots = PuntoConSlots(1.0, 2.0)

print(f"Con __dict__:  {sys.getsizeof(p_dict) + sys.getsizeof(p_dict.__dict__)} byte")
print(f"Con __slots__: {sys.getsizeof(p_slots)} byte")
# Tipicamente: ~150 vs ~56 byte — ~60% di risparmio

# __slots__ impedisce attributi dinamici
try:
    p_slots.z = 3.0   # AttributeError
except AttributeError as e:
    print(f"Errore: {e}")

# hasattr su __dict__ per verificare se una classe usa slots
print(hasattr(p_dict, '__dict__'))    # True
print(hasattr(p_slots, '__dict__'))   # False
```

#### __slots__ con ereditarieta

```python
class Base:
    __slots__ = ('x',)

class Derivata(Base):
    __slots__ = ('y',)   # AGGIUNGE slot, non sovrascrive

d = Derivata()
d.x = 1
d.y = 2
# d.z = 3  # AttributeError — nessun __dict__

# ATTENZIONE: se la classe derivata non definisce __slots__,
# ottiene un __dict__ automaticamente, vanificando il risparmio
class DerivataConDict(Base):
    pass  # Ha __dict__ + slot 'x' — ibrido

dd = DerivataConDict()
dd.x = 1
dd.z = 3   # OK — ha __dict__
```

#### __slots__ con dataclass (Python 3.10+)

```python
from dataclasses import dataclass

@dataclass(slots=True)
class Vettore3D:
    x: float
    y: float
    z: float

v = Vettore3D(1.0, 2.0, 3.0)
print(hasattr(v, '__dict__'))  # False
# v.w = 4.0                   # AttributeError
```

#### Riepilogo: quando usare __slots__

| Scenario | Usare `__slots__`? |
|----------|-------------------|
| Milioni di istanze con attributi fissi | Si, risparmio significativo |
| Poche istanze, attributi dinamici necessari | No |
| Classe base per ereditarieta profonda | Attenzione: ogni livello deve definire i propri slot |
| dataclass Python 3.10+ | Si, con `@dataclass(slots=True)` |
| Mixin, metaclassi, framework di serializzazione | Verificare compatibilita |

### Profilazione della memoria: sys.getsizeof, pympler e tracemalloc

Misurare il consumo di memoria delle strutture dati e fondamentale per ottimizzare applicazioni che gestiscono milioni di oggetti. Python offre tre strumenti complementari con granularita diverse.

#### sys.getsizeof — misura superficiale

`sys.getsizeof()` restituisce la dimensione in byte dell'oggetto stesso, **senza includere gli oggetti referenziati**. Per un dizionario, riporta la dimensione della hash table interna, ma non la memoria occupata dalle chiavi e dai valori.

```python
import sys

lista = [1, 2, 3, 4, 5]
dizionario = {'a': 1, 'b': 2, 'c': 3}
insieme = {1, 2, 3, 4, 5}

print(f"list:  {sys.getsizeof(lista)} byte")    # ~96 byte (solo array di puntatori)
print(f"dict:  {sys.getsizeof(dizionario)} byte")  # ~232 byte (hash table)
print(f"set:   {sys.getsizeof(insieme)} byte")   # ~216 byte (hash table)

# Attenzione: non include la memoria dei contenuti
grande = {'x': list(range(10_000))}
print(f"dict shallow: {sys.getsizeof(grande)} byte")  # ~64 byte — fuorviante!
```

#### pympler.asizeof — misura ricorsiva (deep size)

La libreria `pympler` attraversa ricorsivamente tutti gli oggetti referenziati, fornendo la dimensione totale effettiva. Questo e il valore da usare quando si vuole capire quanta memoria occupa realmente una struttura dati complessa.

```python
from pympler import asizeof

lista_annidata = [[i for i in range(100)] for _ in range(100)]
diz_complesso = {f"chiave_{i}": list(range(50)) for i in range(100)}

print(f"Lista annidata (shallow): {sys.getsizeof(lista_annidata)} byte")
print(f"Lista annidata (deep):    {asizeof.asizeof(lista_annidata)} byte")

print(f"Dict complesso (shallow): {sys.getsizeof(diz_complesso)} byte")
print(f"Dict complesso (deep):    {asizeof.asizeof(diz_complesso)} byte")
```

Il confronto tra `sys.getsizeof` e `pympler.asizeof` rivela quanto la misura superficiale puo essere fuorviante per strutture annidate.

| Funzione | Che cosa misura | Velocita | Uso tipico |
|----------|----------------|----------|------------|
| `sys.getsizeof()` | Solo l'oggetto diretto (shallow) | Molto veloce | Confronto rapido tra tipi |
| `pympler.asizeof()` | Oggetto + tutti i riferimenti (deep) | Piu lenta | Profilazione accurata |
| `tracemalloc` | Allocazioni per file/linea nel tempo | Media | Individuare memory leak |

#### tracemalloc — tracciamento delle allocazioni

`tracemalloc` e un modulo della libreria standard che registra dove vengono allocati i blocchi di memoria, permettendo di individuare le linee di codice responsabili del maggior consumo e di confrontare snapshot nel tempo per rilevare memory leak.

```python
import tracemalloc

tracemalloc.start()

# Codice da profilare
dati = {i: [x**2 for x in range(100)] for i in range(1000)}

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 5 allocazioni:")
for stat in top_stats[:5]:
    print(f"  {stat}")

# Confronto tra snapshot per individuare leak
snapshot1 = tracemalloc.take_snapshot()
# ... operazioni successive ...
snapshot2 = tracemalloc.take_snapshot()

differenze = snapshot2.compare_to(snapshot1, 'lineno')
for diff in differenze[:5]:
    print(f"  {diff}")
```

#### Confronto pratico: list vs tuple vs __slots__

```python
import sys
from pympler import asizeof

class PuntoDict:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

class PuntoSlots:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

confronto = {
    'tuple(1,2,3)':     (1, 2, 3),
    'list[1,2,3]':      [1, 2, 3],
    'dict(x=1,y=2,z=3)': {'x': 1, 'y': 2, 'z': 3},
    'PuntoDict(1,2,3)': PuntoDict(1, 2, 3),
    'PuntoSlots(1,2,3)': PuntoSlots(1, 2, 3),
}

print(f"{'Struttura':<25} {'shallow':>10} {'deep':>10}")
print("-" * 47)
for nome, obj in confronto.items():
    shallow = sys.getsizeof(obj)
    deep = asizeof.asizeof(obj)
    print(f"{nome:<25} {shallow:>8} B {deep:>8} B")
```

Questa tabella evidenzia il vantaggio delle tuple e degli `__slots__` per strutture con molte istanze e attributi fissi.

---

## Typing per Strutture Dati

Il sistema di type hints di Python permette di annotare le strutture dati con i tipi attesi, migliorando la leggibilita del codice e abilitando il controllo statico con strumenti come `mypy`.

### Tipi base per i contenitori

```python
from typing import List, Dict, Set, Tuple, FrozenSet

# Liste tipizzate
numeri: List[int] = [1, 2, 3, 4]
nomi: List[str] = ['Alice', 'Bob']

# Dizionari tipizzati
eta: Dict[str, int] = {'Alice': 30, 'Bob': 25}

# Insiemi tipizzati
tags: Set[str] = {'python', 'coding', 'tutorial'}
permessi: FrozenSet[str] = frozenset(['lettura', 'scrittura'])

# Tuple tipizzate
# Lunghezza fissa con tipi specifici
coordinate: Tuple[float, float] = (45.46, 9.19)

# Lunghezza variabile con tipo uniforme
valori: Tuple[int, ...] = (1, 2, 3, 4, 5)
```

A partire da Python 3.9, e possibile utilizzare direttamente i tipi built-in senza importare da `typing`:

```python
# Python 3.9+
numeri: list[int] = [1, 2, 3]
mappa: dict[str, int] = {'a': 1}
insieme: set[str] = {'x', 'y'}
coppia: tuple[int, str] = (42, 'risposta')
```

### Optional, Union e altri tipi avanzati

```python
from typing import Optional, Union

# Optional — il valore potrebbe essere None
def trova_utente(user_id: int) -> Optional[str]:
    """Restituisce il nome dell'utente o None."""
    utenti = {1: 'Alice', 2: 'Bob'}
    return utenti.get(user_id)

# Union — puo essere di piu tipi
def processa_input(dato: Union[str, int, float]) -> str:
    return str(dato)

# Python 3.10+ — sintassi con |
def processa_input_nuovo(dato: str | int | float) -> str:
    return str(dato)
```

### TypeVar e Generic

```python
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class Pila(Generic[T]):
    """Pila generica tipizzata."""

    def __init__(self) -> None:
        self._elementi: List[T] = []

    def push(self, elemento: T) -> None:
        self._elementi.append(elemento)

    def pop(self) -> T:
        if not self._elementi:
            raise IndexError("La pila e vuota")
        return self._elementi.pop()

    def peek(self) -> T:
        if not self._elementi:
            raise IndexError("La pila e vuota")
        return self._elementi[-1]

    def e_vuota(self) -> bool:
        return len(self._elementi) == 0

    def __len__(self) -> int:
        return len(self._elementi)

    def __repr__(self) -> str:
        return f"Pila({self._elementi})"

# Utilizzo con tipi specifici
pila_interi: Pila[int] = Pila()
pila_interi.push(1)
pila_interi.push(2)
pila_interi.push(3)
print(pila_interi.pop())   # 3

pila_stringhe: Pila[str] = Pila()
pila_stringhe.push("ciao")
pila_stringhe.push("mondo")
print(pila_stringhe.peek())  # 'mondo'
```

### Classi generiche personalizzate

```python
from typing import TypeVar, Generic, Dict, Optional, Iterator

K = TypeVar('K')
V = TypeVar('V')

class CacheLRU(Generic[K, V]):
    """Cache LRU generica con capacita limitata."""

    def __init__(self, capacita: int) -> None:
        self._capacita = capacita
        self._cache: Dict[K, V] = {}
        self._ordine: list[K] = []

    def get(self, chiave: K) -> Optional[V]:
        if chiave in self._cache:
            self._ordine.remove(chiave)
            self._ordine.append(chiave)
            return self._cache[chiave]
        return None

    def put(self, chiave: K, valore: V) -> None:
        if chiave in self._cache:
            self._ordine.remove(chiave)
        elif len(self._cache) >= self._capacita:
            chiave_vecchia = self._ordine.pop(0)
            del self._cache[chiave_vecchia]
        self._cache[chiave] = valore
        self._ordine.append(chiave)

    def __contains__(self, chiave: K) -> bool:
        return chiave in self._cache

    def __len__(self) -> int:
        return len(self._cache)

    def __iter__(self) -> Iterator[K]:
        return iter(self._ordine)

# Utilizzo
cache: CacheLRU[str, int] = CacheLRU(capacita=3)
cache.put("a", 1)
cache.put("b", 2)
cache.put("c", 3)
cache.put("d", 4)       # 'a' viene rimosso (la cache e piena)
print(cache.get("b"))   # 2
print("a" in cache)     # False
print("d" in cache)     # True
```

---

## Structural Pattern Matching con strutture dati (Python 3.10+)

A partire da Python 3.10, l'istruzione `match`/`case` (PEP 634) consente di destrutturare e ispezionare strutture dati complesse in modo dichiarativo. A differenza di una catena di `if`/`elif`, il pattern matching opera sulla *forma* dei dati — sequenze, mapping, dataclass, classi annidate — rendendo il codice piu leggibile e meno soggetto a errori.

### Matching su sequenze

Il matching di sequenze utilizza la sintassi delle liste o delle tuple per catturare elementi individuali, sotto-sequenze con `*rest`, e lunghezze specifiche.

```python
def analizza_comando(comando: list[str]) -> str:
    match comando:
        case ["quit"]:
            return "Uscita dal programma."
        case ["salva", nome_file]:
            return f"Salvataggio in {nome_file}."
        case ["copia", origine, destinazione]:
            return f"Copia da {origine} a {destinazione}."
        case ["carica", *file_multipli] if len(file_multipli) >= 1:
            return f"Caricamento di {len(file_multipli)} file."
        case []:
            return "Nessun comando specificato."
        case _:
            return f"Comando non riconosciuto: {comando}"

print(analizza_comando(["salva", "report.csv"]))
# Salvataggio in report.csv.
print(analizza_comando(["carica", "a.txt", "b.txt", "c.txt"]))
# Caricamento di 3 file.
```

### Matching su mapping (dizionari)

Il matching su mapping estrae chiavi specifiche e ignora le altre. Questo pattern e particolarmente utile per analizzare JSON, configurazioni e messaggi di protocollo.

```python
def gestisci_evento(evento: dict) -> str:
    match evento:
        case {"tipo": "login", "utente": nome, "ip": indirizzo}:
            return f"Login di {nome} da {indirizzo}"
        case {"tipo": "errore", "codice": codice, "messaggio": msg}:
            return f"Errore {codice}: {msg}"
        case {"tipo": "errore", "codice": codice}:
            return f"Errore {codice} senza dettagli"
        case {"tipo": tipo, **resto}:
            return f"Evento generico '{tipo}' con {len(resto)} campi extra"
        case _:
            return "Evento non riconosciuto"

print(gestisci_evento({"tipo": "login", "utente": "Alice", "ip": "10.0.0.1"}))
# Login di Alice da 10.0.0.1
print(gestisci_evento({"tipo": "metrica", "valore": 42, "unita": "ms"}))
# Evento generico 'metrica' con 2 campi extra
```

### Matching su dataclass e classi

Il pattern matching puo destrutturare istanze di `dataclass` e classi con `__match_args__`, verificando sia il tipo sia i valori degli attributi in un'unica espressione.

```python
from dataclasses import dataclass

@dataclass
class Punto:
    x: float
    y: float

@dataclass
class Cerchio:
    centro: Punto
    raggio: float

@dataclass
class Rettangolo:
    origine: Punto
    larghezza: float
    altezza: float

def descrivi_forma(forma) -> str:
    match forma:
        case Cerchio(centro=Punto(x=0, y=0), raggio=r):
            return f"Cerchio centrato nell'origine con raggio {r}"
        case Cerchio(centro=Punto(x=cx, y=cy), raggio=r) if r > 100:
            return f"Cerchio grande (r={r}) in ({cx}, {cy})"
        case Cerchio(centro=c, raggio=r):
            return f"Cerchio in ({c.x}, {c.y}), raggio={r}"
        case Rettangolo(origine=o, larghezza=w, altezza=h) if w == h:
            return f"Quadrato {w}x{h} in ({o.x}, {o.y})"
        case Rettangolo(origine=o, larghezza=w, altezza=h):
            return f"Rettangolo {w}x{h} in ({o.x}, {o.y})"
        case _:
            return "Forma sconosciuta"

print(descrivi_forma(Cerchio(Punto(0, 0), 5)))
# Cerchio centrato nell'origine con raggio 5
print(descrivi_forma(Rettangolo(Punto(1, 2), 10, 10)))
# Quadrato 10x10 in (1, 2)
```

### Guard clause e pattern composti

Le *guard clause* (`if` dopo il pattern) aggiungono condizioni booleane arbitrarie senza appesantire il pattern stesso. I pattern composti con `|` (OR) permettono di raggruppare casi con la stessa logica.

```python
def classifica_temperatura(lettura: dict) -> str:
    match lettura:
        case {"valore": v, "unita": "C"} if v < 0:
            return "Sotto zero (Celsius)"
        case {"valore": v, "unita": "C" | "F"} if v > 1000:
            return "Valore fuori scala — possibile errore sensore"
        case {"valore": v, "unita": "C"}:
            return f"Temperatura: {v}°C"
        case {"valore": v, "unita": "F"}:
            celsius = (v - 32) * 5 / 9
            return f"Temperatura: {v}°F ({celsius:.1f}°C)"

print(classifica_temperatura({"valore": -10, "unita": "C"}))
# Sotto zero (Celsius)
```

### Quando preferire il pattern matching

Il pattern matching non sostituisce ogni `if`/`elif`. Risulta vantaggioso quando:

- I dati hanno **forme diverse** (varianti di messaggi, AST, protocolli).
- Serve **destrutturazione annidata** (JSON complesso, alberi di nodi).
- Il controllo dipende dal **tipo e dai valori** simultaneamente.
- Una catena di `isinstance` + accesso a attributi diventa prolissa.

Evitare di usarlo per semplici confronti di uguaglianza o condizioni puramente booleane, dove un `if`/`elif` tradizionale resta piu chiaro e idiomatico.

---

## Best Practices

Segui queste otto best practice per scegliere e utilizzare le strutture dati in modo efficace nei tuoi progetti Python.

**1. Scegli la struttura dati in base al pattern di accesso, non in base alla comodita.**
Prima di decidere quale struttura utilizzare, analizza le operazioni che verranno eseguite piu frequentemente. Se il collo di bottiglia e l'inserimento e la rimozione in testa, usa una `deque` invece di una lista. Se devi cercare per chiave, usa un dizionario (O(1)) piuttosto che iterare su una lista (O(n)). Una scelta consapevole della struttura dati puo trasformare un algoritmo lento in uno veloce senza alcuna modifica alla logica.

**2. Conosci la complessita temporale delle operazioni piu comuni.**
Ogni struttura dati ha un profilo prestazionale specifico. Le operazioni `append` e `pop` in coda a una lista sono O(1), ma `insert(0, x)` e O(n). In un dizionario, lettura, inserimento e cancellazione sono in media O(1). In un heap, inserimento e estrazione sono O(log n). Tieni a mente queste complessita quando progetti i tuoi algoritmi, specialmente per grandi quantita di dati.

**3. Preferisci le strutture immutabili quando i dati non devono cambiare.**
Le tuple, le `namedtuple`, i `frozenset` e i `MappingProxyType` impediscono modifiche accidentali, rendono il codice piu sicuro e prevedibile, e possono essere utilizzati come chiavi di dizionari o elementi di insiemi. L'immutabilita facilita anche il ragionamento sul codice concorrente, perche i dati immutabili possono essere condivisi tra thread senza rischi di race condition.

**4. Usa il modulo collections prima di implementare soluzioni personalizzate.**
Prima di scrivere una classe contatore, un dizionario con valori predefiniti o una coda a doppia estremita da zero, verifica se `collections` offre gia una soluzione. Le implementazioni del modulo `collections` sono scritte in C, testate a fondo e ottimizzate per le prestazioni. Il codice che le utilizza risulta anche piu idiomatico e leggibile per gli altri sviluppatori Python.

**5. Annota i tipi delle strutture dati con i type hints.**
Le annotazioni di tipo non solo rendono il codice autodocumentante, ma permettono a strumenti come `mypy` di individuare errori prima dell'esecuzione. Usa `list[int]` invece di `list`, `dict[str, float]` invece di `dict`, e crea classi generiche con `Generic[T]` quando costruisci contenitori riutilizzabili. Le annotazioni di tipo sono particolarmente preziose nelle API pubbliche e nelle funzioni condivise tra team.

**6. Profila prima di ottimizzare — non indovinare il collo di bottiglia.**
Non sostituire tutte le liste con dizionari o deque "per sicurezza". Usa `timeit`, `cProfile` o `line_profiler` per misurare le prestazioni effettive del tuo codice e identifica i colli di bottiglia reali. Spesso, la struttura dati piu semplice e sufficientemente veloce per il caso d'uso specifico, e l'ottimizzazione prematura aggiunge complessita senza benefici concreti.

**7. Sfrutta le strutture dati thread-safe del modulo queue per la concorrenza.**
In programmi multi-thread, non usare liste o dizionari standard per comunicare tra thread senza sincronizzazione esplicita. Le classi `Queue`, `LifoQueue` e `PriorityQueue` del modulo `queue` gestiscono internamente il locking, evitando race condition e deadlock. Per il codice asincrono con `asyncio`, usa le code equivalenti di `asyncio.Queue`.

**8. Documenta le invarianti e le aspettative sulla struttura dati.**
Se una funzione si aspetta una lista ordinata per la ricerca binaria, documentalo. Se un dizionario deve avere certe chiavi obbligatorie, usa un `TypedDict` o una `dataclass`. Se la struttura dati ha vincoli di dimensione o di tipo, rendili espliciti nel codice o nelle annotazioni. Una struttura dati ben documentata previene una classe intera di bug e riduce il tempo di debug.

---

## Troubleshooting

### Problema: `TypeError: unhashable type: 'list'` come chiave di dizionario o in set

**Causa:** le liste sono mutabili, quindi non hashable. Solo oggetti immutabili possono essere chiavi di dizionari o elementi di set.

**Soluzione:** convertire in tupla (`tuple(lista)`) o, per insiemi, in `frozenset(insieme)`.

```python
# Errore
# d = {[1, 2, 3]: "valore"}   # TypeError

# Soluzione
d = {(1, 2, 3): "valore"}     # OK — tupla e hashable
d = {frozenset([1, 2, 3]): "valore"}  # OK — frozenset e hashable
```

### Problema: `defaultdict` crea entry indesiderate durante il check di esistenza

**Causa:** accedere a una chiave inesistente con `d[k]` crea automaticamente l'entry con il valore default.

**Soluzione:** usare `k in d` o `d.get(k)` per il check senza side-effect.

```python
from collections import defaultdict

d = defaultdict(list)
d['a'].append(1)

# SBAGLIATO — crea entry 'b' con lista vuota
if d['b']:
    pass
print('b' in d)   # True — entry creata!

# CORRETTO — non crea entry
d2 = defaultdict(list)
d2['a'].append(1)
if d2.get('b'):
    pass
print('b' in d2)  # False
```

### Problema: `heapq` con oggetti non confrontabili

**Causa:** quando due elementi hanno la stessa priorita, `heapq` prova a confrontare il dato (tiebreaker), che potrebbe non supportare `<`.

**Soluzione:** usare un contatore di inserimento come tiebreaker (come nell'esempio `CodaPriorita` sopra), oppure wrappare con una dataclass `order=True` e `compare=False` sul campo dato.

### Problema: `Counter` con conteggi negativi dopo `subtract()`

**Causa:** `subtract()` puo produrre conteggi negativi o zero, che restano nel Counter.

**Soluzione:** filtrare con `+c` (unario +) che rimuove le entry con conteggio <= 0.

```python
from collections import Counter

c = Counter(a=3, b=1, c=0, d=-2)
print(+c)   # Counter({'a': 3, 'b': 1}) — solo valori positivi
```

### Problema: `namedtuple._replace()` non modifica l'originale

**Causa:** `_replace()` restituisce una **nuova** istanza. La namedtuple e immutabile.

**Soluzione:** assegnare il risultato a una variabile.

```python
from collections import namedtuple

Punto = namedtuple('Punto', ['x', 'y'])
p = Punto(1, 2)
p._replace(x=10)   # SBAGLIATO — il risultato viene scartato
p = p._replace(x=10)  # CORRETTO — riassegna
```

### Problema: `__slots__` e pickle

**Causa:** `pickle` di default cerca `__dict__` per serializzare. Con `__slots__`, `__dict__` non esiste.

**Soluzione:** implementare `__getstate__` e `__setstate__`, oppure usare `__slots__` con dataclass (che gestisce la serializzazione).

```python
class PuntoSlots:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getstate__(self):
        return {'x': self.x, 'y': self.y}

    def __setstate__(self, stato):
        self.x = stato['x']
        self.y = stato['y']

import pickle
p = PuntoSlots(1, 2)
data = pickle.dumps(p)
p2 = pickle.loads(data)
print(p2.x, p2.y)   # 1 2
```

---

## Esercizi

### Esercizio 1 — Frequency analyzer
Scrivere una funzione che, dato un testo, restituisca le N parole piu frequenti escludendo una stopword list configurabile. Usare `Counter` e restituire una lista di tuple `(parola, conteggio)`.

### Esercizio 2 — LRU Cache con OrderedDict
Implementare una classe `LRUCache` con capacita fissa usando `OrderedDict` e i suoi metodi `move_to_end()` e `popitem()`. La cache deve avere metodi `get(chiave)` e `put(chiave, valore)` con complessita O(1).

### Esercizio 3 — Merge sorted files
Dati N file di testo, ciascuno contenente una riga per numero gia ordinato, scrivere un programma che li unisca in un unico file ordinato usando `heapq.merge()`. Misurare il consumo di memoria con `tracemalloc`.

### Esercizio 4 — Trie autocompletamento
Estendere la classe `Trie` di questa guida aggiungendo:
- un metodo `rimuovi(parola)` che elimina una parola senza rompere altre parole che condividono il prefisso
- un metodo `parole_con_distanza(parola, max_distanza)` che restituisce parole con distanza di Levenshtein <= `max_distanza` (fuzzy search)

### Esercizio 5 — Confronto memoria
Creare 1 milione di punti 3D (x, y, z) usando:
a) `namedtuple`
b) `@dataclass`
c) `@dataclass(slots=True)`
d) classe con `__slots__`
e) `tuple` semplice

Misurare la memoria totale con `tracemalloc` e il tempo di creazione con `timeit`. Presentare i risultati in una tabella.

### Esercizio 6 — Priority queue con cancellazione
Estendere la classe `CodaPriorita` aggiungendo un metodo `cancella(elemento)` che rimuove un elemento dalla coda senza violare la proprieta heap. Suggerimento: usare il pattern "lazy deletion" con un set di elementi cancellati.

### Esercizio 7 — ChainMap configuration system
Implementare un sistema di configurazione a 4 livelli (default, file, environment, CLI) usando `ChainMap`. Il sistema deve:
- caricare default hardcoded
- sovrascrivere con un file TOML
- sovrascrivere con variabili d'ambiente con prefisso `APP_`
- sovrascrivere con argomenti CLI

### Esercizio 8 — Bloom filter benchmark
Implementare un benchmark che confronti le prestazioni di lookup per:
a) `set` Python standard
b) `BloomFilter` (da questa guida)
c) `frozenset`

con 100.000 e 1.000.000 di elementi. Misurare: tempo di inserimento, tempo di lookup, memoria usata, tasso di falsi positivi del bloom filter.

---

## Letture e fonti primarie

- **Python docs — collections module:** https://docs.python.org/3/library/collections.html — documentazione ufficiale di namedtuple, deque, defaultdict, OrderedDict, Counter, ChainMap, UserDict, UserList, UserString
- **Python docs — heapq:** https://docs.python.org/3/library/heapq.html — algoritmo heap, nlargest, nsmallest, merge
- **Python docs — bisect:** https://docs.python.org/3/library/bisect.html — ricerca binaria e inserimento ordinato
- **Python docs — array:** https://docs.python.org/3/library/array.html — array tipizzati
- **Python docs — struct:** https://docs.python.org/3/library/struct.html — packing/unpacking binario
- **Python docs — dataclasses:** https://docs.python.org/3/library/dataclasses.html — dataclass e field()
- **Python docs — typing:** https://docs.python.org/3/library/typing.html — NamedTuple, Generic, TypeVar
- **PEP 557 — Data Classes:** https://peps.python.org/pep-0557/ — motivazione e design delle dataclass
- **PEP 3107 / PEP 484 — Type Hints:** https://peps.python.org/pep-0484/ — sistema di annotazioni di tipo
- **sortedcontainers:** https://grantjenks.com/docs/sortedcontainers/ — SortedList, SortedDict, SortedSet con complessita O(log n)
- **pyrsistent:** https://pyrsistent.readthedocs.io/ — strutture dati persistenti immutabili (PVector, PMap, PSet, evolver)
- **pympler:** https://pympler.readthedocs.io/ — profilazione della memoria Python con asizeof, tracker, muppy
- **Python docs — tracemalloc:** https://docs.python.org/3/library/tracemalloc.html — tracciamento allocazioni di memoria
- **PEP 634 — Structural Pattern Matching:** https://peps.python.org/pep-0634/ — specifica del pattern matching (match/case)
- **PEP 636 — Pattern Matching Tutorial:** https://peps.python.org/pep-0636/ — tutorial ufficiale con esempi pratici
- **Timsort — Wikipedia:** https://en.wikipedia.org/wiki/Timsort — descrizione dell'algoritmo ibrido usato da sorted()
- **Python docs — queue:** https://docs.python.org/3/library/queue.html — code thread-safe

---

## Cross-link

- `04-PROGRAMMAZIONE-PYTHON/01-fondamenti-python.md` — tipi di base: list, dict, set, tuple
- `04-PROGRAMMAZIONE-PYTHON/02-funzioni-e-decoratori.md` — lambda, funzioni key per sorted(), functools
- `04-PROGRAMMAZIONE-PYTHON/04-oop-classi-ereditarieta.md` — __hash__, __eq__, __slots__, ereditarieta
- `04-PROGRAMMAZIONE-PYTHON/05-gestione-file-io.md` — struct per I/O binario, mmap per memory-mapped files
- `04-PROGRAMMAZIONE-PYTHON/06-testing-pytest.md` — test delle strutture dati personalizzate
- `04-PROGRAMMAZIONE-PYTHON/10-concorrenza-parallelismo.md` — queue.Queue, asyncio.Queue, thread-safety

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Amortizzato** | Complessita media per operazione su una sequenza di N operazioni; `list.append()` e O(1) amortizzato perche il ridimensionamento O(n) avviene raramente |
| **Bloom filter** | Struttura dati probabilistica che risponde "probabilmente si" o "sicuramente no" alla domanda di appartenenza, con falsi positivi controllabili |
| **BST** | Binary Search Tree — albero binario in cui i valori a sinistra sono minori e quelli a destra sono maggiori |
| **Collisione hash** | Quando due oggetti diversi producono lo stesso valore hash; gestita internamente da dict/set con open addressing |
| **default_factory** | Callable passato a `defaultdict` o `dataclasses.field` che genera il valore di default per chiavi/campi mancanti |
| **Deque** | Double-ended queue — coda a doppia estremita con inserimento/rimozione O(1) da entrambi i lati |
| **Hashable** | Oggetto che implementa `__hash__()` e `__eq__()` e il cui hash non cambia durante il suo ciclo di vita |
| **Heap** | Albero binario completo dove il padre e sempre minore (min-heap) o maggiore (max-heap) dei figli |
| **Immutabile** | Oggetto il cui stato non puo essere modificato dopo la creazione (es. tuple, frozenset, str) |
| **insort** | Funzione di `bisect` che inserisce un elemento in una lista ordinata mantenendo l'ordinamento |
| **MappingProxyType** | Vista di sola lettura su un dizionario, da `types` — impedisce modifiche accidentali |
| **memoryview** | Oggetto che espone il buffer protocol, permettendo slicing zero-copy su bytes/bytearray/array |
| **Timsort** | Algoritmo di ordinamento ibrido (merge sort + insertion sort) usato da `sorted()` e `list.sort()`, stabile e adattivo |
| **Trie** | Struttura dati ad albero per stringhe dove ogni nodo rappresenta un carattere; eccelle nella ricerca per prefisso |
| **Pattern matching** | Istruzione `match`/`case` (Python 3.10+, PEP 634) per destrutturare e ispezionare la forma dei dati — sequenze, mapping, classi |
| **Persistente (struttura dati)** | Struttura immutabile che preserva le versioni precedenti dopo ogni modifica tramite structural sharing |
| **PVector/PMap/PSet** | Strutture dati persistenti dalla libreria pyrsistent — equivalenti immutabili di list, dict e set |
| **Evolver** | Interfaccia mutabile temporanea di pyrsistent per applicare batch di modifiche e materializzare il risultato con `.persistent()` |
| **sortedcontainers** | Libreria pure-Python con SortedList, SortedDict, SortedSet — operazioni O(log n) su collezioni ordinate |
| **Structural sharing** | Tecnica in cui le versioni immutabili condividono sotto-alberi invariati, riducendo il costo di copia |
| **sys.getsizeof** | Funzione stdlib che misura la dimensione shallow (diretta) di un oggetto in byte, senza includere i riferimenti |
| **pympler.asizeof** | Funzione della libreria pympler che misura la dimensione deep (ricorsiva) di un oggetto, includendo tutti gli oggetti referenziati |
| **tracemalloc** | Modulo stdlib per tracciare le allocazioni di memoria per file e linea, utile per individuare memory leak |
| **`__slots__`** | Attributo di classe che definisce un set fisso di attributi, eliminando `__dict__` e riducendo il consumo di memoria |
| **Zero-copy** | Tecnica che evita la duplicazione dei dati in memoria durante operazioni di slicing o trasferimento |

---

> **Nota finale:** le strutture dati avanzate non sono uno strumento da usare sempre e comunque. Sono strumenti da usare *quando servono*. La chiarezza del codice viene sempre prima dell'ottimizzazione. Scegli la struttura piu semplice che soddisfa i requisiti, e passa a una piu avanzata solo quando i dati o le prestazioni lo richiedono.
