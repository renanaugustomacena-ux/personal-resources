# Tutorial: Strutture Dati Avanzate — Dal Principiante all'Esperto

> **Companion to:** `03-strutture-dati-avanzate.md`
> **Scope:** collections (Counter, defaultdict, OrderedDict, ChainMap, deque, namedtuple, UserDict/UserList), heapq, bisect, array, memoryview, enum, complessita Big-O
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md` completato
> **Durata stimata:** 25-30 ore
> **Lingua:** Italiano
> **Versione Python:** >= 3.12

---

## Indice

- [Parte A — Perche esistono strutture diverse?](#parte-a)
  - [Counter — Analogia: inventario del negozio](#counter)
  - [defaultdict — Analogia: frigorifero intelligente](#defaultdict)
  - [deque — Analogia: fila al supermercato bidirezionale](#deque)
  - [namedtuple — Analogia: modulo compilato vs foglio bianco](#namedtuple)
  - [OrderedDict — Dizionario con memoria dell'ordine](#ordereddict)
  - [ChainMap — Configurazioni a livelli](#chainmap)
- [Parte B — Strutture per efficienza](#parte-b)
  - [heapq — Analogia: pronto soccorso con triage](#heapq)
  - [bisect — Analogia: elenco telefonico](#bisect)
  - [array vs list vs NumPy](#array)
  - [memoryview — Analogia: finestra su un muro](#memoryview)
  - [enum — Analogia: semaforo](#enum)
- [Parte C — 10 Esercizi pratici](#parte-c)
- [Parte D — Livello esperto e riepilogo](#parte-d)

---

## Parte A — Perche esistono strutture diverse? {#parte-a}

### La cassetta degli attrezzi

Immagina un falegname. Ha a disposizione: un martello, un cacciavite, una sega, una pialla, delle pinze. Ogni strumento esiste per un motivo preciso. Usare il martello al posto della sega non e sbagliato in assoluto, ma rende il lavoro lento, impreciso e faticoso.

In Python accade la stessa cosa. Le strutture dati built-in piu comuni sono:

| Struttura | Strumento equivalente |
|-----------|----------------------|
| `list` | Martello: versatile, adatto a tutto |
| `dict` | Cassetto con etichette: accesso rapido per nome |
| `set` | Setaccio: elimina i duplicati |
| `tuple` | Vite serrata: immutabile, sicura |

Ma quando i progetti crescono emergono esigenze piu specifiche:

- "Ho bisogno di contare quante volte appare ogni parola in un testo."
- "Voglio aggiungere e rimuovere elementi da entrambe le estremita di una lista in modo efficiente."
- "Ho bisogno di trovare sempre l'elemento piu urgente in una lista di task."

Per questi casi Python offre il modulo `collections`, il modulo `heapq`, `bisect`, `array`, `enum` e molti altri. Questo tutorial li esplora uno per uno, con analogie concrete e misurazioni di prestazione.

---

### La notazione Big-O — glossario rapido

Prima di iniziare, ripassiamo la notazione Big-O che useremo per ogni struttura:

| Notazione | Significato | Esempio pratico |
|-----------|-------------|-----------------|
| O(1) | Costante: sempre veloce, qualunque sia la dimensione | `dict[chiave]` |
| O(log n) | Logaritmico: raddoppiare i dati aggiunge solo 1 passo | ricerca binaria |
| O(n) | Lineare: raddoppiare i dati raddoppia il tempo | scorrere una lista |
| O(n log n) | Lineare-logaritmico | ordinamento con `sorted()` |
| O(n^2) | Quadratico: raddoppiare i dati quadruplica il tempo | bubble sort |

**Regola pratica:** nel dubbio, misura. La teoria guida la scelta, ma il profiler conferma.

---

## Counter — Analogia: inventario del negozio {#counter}

### Cosa e Counter?

Immagina di gestire un negozio di frutta. Ogni mattina il corriere arriva con una scatola piena di frutta mescolata. Tu devi sapere: quante mele ci sono? Quante banane? Quante arance?

Con una lista normale dovresti:
1. Creare un dizionario vuoto
2. Scorrere tutta la frutta uno per uno
3. Per ogni frutto controllare se la chiave esiste gia
4. Incrementare il conteggio o inizializzarlo

Con `Counter` tutto questo avviene in una sola riga.

`Counter` e una sottoclasse di `dict` del modulo `collections`, progettata specificamente per contare elementi hashable.

### Complessita Big-O di Counter

| Operazione | Complessita | Note |
|------------|-------------|------|
| Creazione da iterabile | O(n) | n = lunghezza dell'iterabile |
| Accesso `c[chiave]` | O(1) | Come un dict normale |
| `most_common(k)` | O(n log k) | n = elementi totali, k = quanti ne vuoi |
| `update(altro)` | O(m) | m = lunghezza di `altro` |
| Somma `+`, differenza `-` | O(n + m) | Unisce i due counter |

### Creazione e accesso base

```python
from collections import Counter

# Analogia: la cassa arriva con questa frutta
corriere = ['mela', 'banana', 'mela', 'arancia', 'mela', 'banana', 'pera']

# Counter conta tutto automaticamente
inventario = Counter(corriere)
print(inventario)
# Output atteso:
# Counter({'mela': 3, 'banana': 2, 'arancia': 1, 'pera': 1})

# Quante mele ci sono?
print(inventario['mela'])   # 3

# Chiave inesistente: restituisce 0 (non KeyError!)
print(inventario['kiwi'])   # 0
```

> **Differenza chiave rispetto a dict normale:** accedere a una chiave inesistente restituisce `0`, non lancia `KeyError`. Questo lo rende sicuro nei loop di conteggio.

### most_common — i prodotti piu venduti

```python
from collections import Counter

vendite_settimana = Counter({
    'mela': 150,
    'banana': 89,
    'arancia': 210,
    'pera': 45,
    'kiwi': 178,
    'mango': 32
})

# I 3 prodotti piu venduti
print("Top 3 prodotti:")
for prodotto, quantita in vendite_settimana.most_common(3):
    print(f"  {prodotto}: {quantita} pezzi")
# Output atteso:
# Top 3 prodotti:
#   arancia: 210 pezzi
#   kiwi: 178 pezzi
#   mela: 150 pezzi

# I 2 prodotti meno venduti (slice dalla fine)
print("Prodotti da riordinare:")
for prodotto, quantita in vendite_settimana.most_common()[:-3:-1]:
    print(f"  {prodotto}: {quantita} pezzi")
# Output atteso:
# Prodotti da riordinare:
#   mango: 32 pezzi
#   pera: 45 pezzi
```

### Operazioni aritmetiche — fusione di inventari

```python
from collections import Counter

# Inventario deposito A (Roma)
deposito_roma = Counter(mele=50, banane=30, arance=20)

# Inventario deposito B (Milano)
deposito_milano = Counter(mele=30, banane=40, pere=15)

# Unione totale degli stock
totale = deposito_roma + deposito_milano
print("Stock totale:", totale)
# Output atteso:
# Stock totale: Counter({'banane': 70, 'mele': 80, 'arance': 20, 'pere': 15})

# Differenza: cosa ha Roma che Milano non ha?
differenza = deposito_roma - deposito_milano
print("Solo a Roma:", differenza)
# Output atteso:
# Solo a Roma: Counter({'arance': 20, 'mele': 20})

# Intersezione: il minimo disponibile in entrambi (scorta sicura)
comune = deposito_roma & deposito_milano
print("Scorta comune:", comune)
# Output atteso:
# Scorta comune: Counter({'banane': 30, 'mele': 30})

# Unione (il massimo disponibile in almeno un deposito)
massimo = deposito_roma | deposito_milano
print("Massimo disponibile:", massimo)
# Output atteso:
# Massimo disponibile: Counter({'mele': 50, 'banane': 40, 'arance': 20, 'pere': 15})
```

### Analisi frequenza parole in un testo

```python
from collections import Counter

testo = """
Nel mezzo del cammin di nostra vita
mi ritrovai per una selva oscura
che la diritta via era smarrita
ahi quanto a dir qual era e cosa dura
esta selva selvaggia e aspra e forte
che nel pensier rinova la paura
"""

# Pulizia e tokenizzazione
parole = testo.lower().split()
parole_pulite = [p.strip('.,!?') for p in parole if len(p) > 2]

frequenze = Counter(parole_pulite)

print(f"Parole uniche: {len(frequenze)}")
print(f"Parole totali: {frequenze.total()}")
print("\nLe 5 piu frequenti:")
for parola, conteggio in frequenze.most_common(5):
    print(f"  '{parola}': {conteggio} volte")
# Output atteso (approssimativo):
# Parole uniche: 36
# Parole totali: 40
# Le 5 piu frequenti:
#   'che': 3 volte
#   'selva': 2 volte
#   'nel': 2 volte
#   'era': 2 volte
#   'quanto': 1 volte
```

### elements() e subtract()

```python
from collections import Counter

c = Counter(a=3, b=1, c=2)

# elements(): iteratore che "espande" ogni elemento per il suo conteggio
print(sorted(c.elements()))
# Output atteso: ['a', 'a', 'a', 'b', 'c', 'c']

# subtract(): riduce i conteggi (puo andare negativo!)
c.subtract({'a': 2, 'b': 1, 'd': 1})
print(c)
# Output atteso: Counter({'c': 2, 'a': 1, 'b': 0, 'd': -1})
# NOTA: update() aggiunge, subtract() sottrae. I negativi sono consentiti.
```

### Quando usare Counter

Usa `Counter` quando devi:
- Contare frequenze di elementi in una sequenza
- Trovare i k elementi piu o meno frequenti
- Confrontare distribuzioni (somma, differenza, intersezione di conteggi)
- Analizzare testi, log, eventi

Non usare `Counter` quando:
- Vuoi solo verificare se un elemento esiste (usa `set`)
- Hai un dizionario con valori generici, non conteggi (usa `dict`)

---

## defaultdict — Analogia: frigorifero intelligente {#defaultdict}

### Cosa e defaultdict?

Immagina un frigorifero magico. Ogni volta che cerchi qualcosa che non c'e — per esempio "succo di arancia" — invece di dirti "non ce n'e", lui crea automaticamente una confezione vuota di succo di arancia e te la mette in mano. Tu la riempi quanto vuoi.

Questo e esattamente come funziona `defaultdict`: ogni volta che accedi a una chiave che non esiste, invece di lanciare un `KeyError`, crea automaticamente un valore di default usando una funzione che tu specifichi.

### Complessita Big-O di defaultdict

Le complessita sono identiche a `dict`, perche `defaultdict` e una sua sottoclasse:

| Operazione | Complessita |
|------------|-------------|
| Accesso / inserimento `d[k]` | O(1) medio |
| Verifica `k in d` | O(1) |
| Iterazione | O(n) |
| Rimozione `del d[k]` | O(1) |

L'unica differenza rispetto a `dict` e che l'accesso a una chiave mancante ha un piccolo overhead per invocare la `default_factory`.

### Il problema senza defaultdict

```python
# APPROCCIO CLASSICO — verboso e soggetto a errori

studenti = [
    ('Alice', 'matematica'),
    ('Bob', 'fisica'),
    ('Alice', 'informatica'),
    ('Carlo', 'matematica'),
    ('Bob', 'informatica'),
    ('Alice', 'fisica'),
]

# Raggruppare per nome — approccio con dict normale
per_nome = {}
for nome, materia in studenti:
    if nome not in per_nome:    # controllo esplicito ogni volta
        per_nome[nome] = []
    per_nome[nome].append(materia)

print(per_nome)
# Output atteso:
# {'Alice': ['matematica', 'informatica', 'fisica'],
#  'Bob': ['fisica', 'informatica'],
#  'Carlo': ['matematica']}
```

### Il problema con defaultdict

```python
from collections import defaultdict

studenti = [
    ('Alice', 'matematica'),
    ('Bob', 'fisica'),
    ('Alice', 'informatica'),
    ('Carlo', 'matematica'),
    ('Bob', 'informatica'),
    ('Alice', 'fisica'),
]

# Con defaultdict(list) il frigorifero crea la lista automaticamente
per_nome = defaultdict(list)
for nome, materia in studenti:
    per_nome[nome].append(materia)  # niente controllo if!

print(dict(per_nome))
# Output atteso:
# {'Alice': ['matematica', 'informatica', 'fisica'],
#  'Bob': ['fisica', 'informatica'],
#  'Carlo': ['matematica']}
```

### Factory functions — cosa si puo usare come default

La `default_factory` e qualsiasi callable (funzione, classe, lambda) che non richiede argomenti:

```python
from collections import defaultdict

# list: valore default e una lista vuota []
d_lista = defaultdict(list)
d_lista['frutti'].append('mela')
d_lista['frutti'].append('pera')
print(d_lista)
# Output atteso: defaultdict(<class 'list'>, {'frutti': ['mela', 'pera']})

# int: valore default e 0 (perfetto per conteggi)
conteggio = defaultdict(int)
for lettera in 'abracadabra':
    conteggio[lettera] += 1
print(dict(conteggio))
# Output atteso: {'a': 5, 'b': 2, 'r': 2, 'c': 1, 'd': 1}

# set: valore default e un insieme vuoto set()
indice_inverso = defaultdict(set)
documenti = {
    'doc1': ['python', 'programmazione'],
    'doc2': ['python', 'web'],
    'doc3': ['programmazione', 'algoritmi'],
}
for doc_id, parole in documenti.items():
    for parola in parole:
        indice_inverso[parola].add(doc_id)
print(dict(indice_inverso))
# Output atteso:
# {'python': {'doc1', 'doc2'},
#  'programmazione': {'doc1', 'doc3'},
#  'web': {'doc2'},
#  'algoritmi': {'doc3'}}

# lambda: valore default personalizzato
prezzi = defaultdict(lambda: 9.99)  # prezzo default 9.99
prezzi['mela'] = 1.50
print(prezzi['mela'])    # 1.50
print(prezzi['banana'])  # 9.99 (default creato al volo)
```

### Struttura annidata: dizionario di dizionari automatico

Questo e uno dei pattern piu potenti: un defaultdict che crea automaticamente altri defaultdict, formando un albero di profondita arbitraria.

```python
from collections import defaultdict

# Un dizionario annidato che si crea da solo (albero infinito)
def crea_albero():
    return defaultdict(crea_albero)

catalogo = crea_albero()

# Aggiunta senza dover creare le strutture intermedie
catalogo['elettronica']['smartphone']['iPhone15'] = {'prezzo': 1299, 'stock': 50}
catalogo['elettronica']['laptop']['MacBook'] = {'prezzo': 1999, 'stock': 12}
catalogo['alimentari']['frutta']['mele'] = {'prezzo': 2.50, 'stock': 100}

# Accesso naturale come se le chiavi esistessero sempre
print(catalogo['elettronica']['smartphone']['iPhone15'])
# Output atteso: {'prezzo': 1299, 'stock': 50}
```

### Raggruppamento avanzato con defaultdict

```python
from collections import defaultdict

vendite = [
    {'venditore': 'Alice', 'mese': 'gennaio', 'importo': 5200},
    {'venditore': 'Bob', 'mese': 'gennaio', 'importo': 3100},
    {'venditore': 'Alice', 'mese': 'febbraio', 'importo': 4800},
    {'venditore': 'Carlo', 'mese': 'gennaio', 'importo': 6000},
    {'venditore': 'Bob', 'mese': 'febbraio', 'importo': 3900},
    {'venditore': 'Carlo', 'mese': 'febbraio', 'importo': 5500},
]

# Raggruppamento per venditore
per_venditore = defaultdict(list)
for v in vendite:
    per_venditore[v['venditore']].append(v['importo'])

for venditore, importi in sorted(per_venditore.items()):
    totale = sum(importi)
    media = totale / len(importi)
    print(f"{venditore}: totale={totale:,} | media={media:,.0f}")
# Output atteso:
# Alice: totale=10000 | media=5,000
# Bob: totale=7000 | media=3,500
# Carlo: totale=11500 | media=5,750
```

### missing — come funziona internamente

```python
from collections import defaultdict

d = defaultdict(list)

# Cosa succede quando accediamo a una chiave mancante?
# Python chiama d.__missing__('chiave_inesistente')
# che a sua volta chiama default_factory() e salva il risultato

print('x' in d)   # False — non ancora creata
val = d['x']      # qui defaultdict crea [] e lo salva
print('x' in d)   # True — ora esiste!
print(d['x'])     # []

# ATTENZIONE: get() NON invoca __missing__
d2 = defaultdict(int)
result = d2.get('chiave_assente')
print(result)  # None, NON 0
print('chiave_assente' in d2)  # False — get() non ha creato la chiave
```

### Quando usare defaultdict

Usa `defaultdict` quando:
- Stai raggruppando elementi per categoria
- Stai costruendo un indice inverso (parola -> lista di documenti)
- Stai contando con pattern `d[k] += 1` (anche Counter e meglio per solo conteggi)
- Hai strutture annidate che si devono creare automaticamente

Non usare `defaultdict` quando:
- Vuoi che un KeyError ti avvisi di chiavi errate (usa `dict` normale)
- La factory non deve essere chiamata mai inconsapevolmente (usa `dict.setdefault()` puntualmente)

---

## Riepilogo Parte A — Blocco 1

In questo primo blocco abbiamo esplorato:

1. **Perche esistono strutture diverse**: ogni struttura e uno strumento progettato per un problema specifico. Usare quella sbagliata non e un errore fatale, ma e come tagliare il pane con le forbici.

2. **Counter**: il cassiere automatico che conta tutto. Creazione O(n), accesso O(1), `most_common` O(n log k). Perfetto per frequenze, analisi di testi, confronto di distribuzioni.

3. **defaultdict**: il frigorifero che crea automaticamente quello che cerchi. Stesse complessita di `dict`, con il vantaggio di eliminare le verifiche `if chiave not in d`.

Nel prossimo blocco vedremo:
- `deque` (la fila bidirezionale)
- `namedtuple` (il modulo compilato)
- `OrderedDict` e `ChainMap`

---

## deque — Analogia: fila al supermercato bidirezionale {#deque}

### Cosa e deque?

Immagina la cassa di un supermercato. I clienti entrano in coda da una parte (in fondo) ed escono dall'altra (davanti). Questa e una coda normale — FIFO (First In, First Out).

Ora immagina una cassa speciale: i clienti con le carte gia pronte possono unirsi anche davanti alla coda (VIP pass), e in certi momenti il cassiere puo rispedire indietro l'ultimo cliente in coda. Questa e una **coda bidirezionale** — e esattamente quello che e `deque` (double-ended queue, pronuncia "deck").

Con una `list` normale:
- `append()` e `pop()` in coda: O(1) — veloce
- `insert(0, x)` e `pop(0)` in testa: **O(n)** — lento! Ogni elemento deve spostarsi

Con `deque`:
- `append()` e `pop()` in coda: O(1)
- `appendleft()` e `popleft()` in testa: **O(1)** — altrettanto veloce!

### Complessita Big-O di deque

| Operazione | Complessita | Note |
|------------|-------------|------|
| append o appendleft | O(1) | Aggiunta a destra o sinistra |
| pop o popleft | O(1) | Rimozione da destra o sinistra |
| Accesso per indice d[i] | O(n) | Non ottimizzato come list! |
| rotate(k) | O(k) | Rotazione circolare |
| len(d) | O(1) | |
| Ricerca x in d | O(n) | Scansione lineare |

**Attenzione:** accedere a `d[i]` in una deque e O(n), non O(1) come nelle liste. Se hai bisogno di accesso per indice frequente, usa una `list`. La deque eccelle per inserimenti e rimozioni alle estremita.

### Creazione e operazioni fondamentali

```python
from collections import deque

# Creazione da una lista
fila_cassa = deque(['Luca', 'Maria', 'Giovanni'])
print(fila_cassa)
# Output atteso: deque(['Luca', 'Maria', 'Giovanni'])

# Nuovo cliente in coda normale (da destra)
fila_cassa.append('Francesca')
print(fila_cassa)
# Output atteso: deque(['Luca', 'Maria', 'Giovanni', 'Francesca'])

# Cliente VIP: entra davanti (da sinistra)
fila_cassa.appendleft('Direttore')
print(fila_cassa)
# Output atteso: deque(['Direttore', 'Luca', 'Maria', 'Giovanni', 'Francesca'])

# Il cassiere serve il primo (pop da sinistra)
servito = fila_cassa.popleft()
print(f"Servito: {servito}")
# Output atteso: Servito: Direttore

# Il cassiere richiama l'ultimo (pop da destra)
richiamato = fila_cassa.pop()
print(f"Richiamato: {richiamato}")
# Output atteso: Richiamato: Francesca

print(fila_cassa)
# Output atteso: deque(['Luca', 'Maria', 'Giovanni'])
```

### maxlen — buffer circolare

Uno degli usi piu potenti di `deque` e come **buffer circolare**: una finestra scorrevole che tiene sempre solo gli ultimi N elementi.

```python
from collections import deque

# Buffer che tiene solo gli ultimi 5 log di sistema
log_sistema = deque(maxlen=5)

for i in range(10):
    log_sistema.append(f"Evento-{i}")
    # Quando supera maxlen=5, l'elemento piu vecchio viene rimosso automaticamente

print(log_sistema)
# Output atteso:
# deque(['Evento-5', 'Evento-6', 'Evento-7', 'Evento-8', 'Evento-9'], maxlen=5)

# Applicazione: sliding window per media mobile
temperature = deque(maxlen=3)
letture = [22.1, 22.5, 23.0, 23.8, 24.1, 22.9]

for t in letture:
    temperature.append(t)
    if len(temperature) == 3:
        media = sum(temperature) / 3
        print(f"Media ultimi 3: {media:.2f} gradi C")
# Output atteso:
# Media ultimi 3: 22.53 gradi C
# Media ultimi 3: 23.10 gradi C
# Media ultimi 3: 23.63 gradi C
# Media ultimi 3: 23.60 gradi C
```

### rotate — rotazione circolare

```python
from collections import deque

giorni = deque(['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'])

# Rotazione a destra di 2: gli ultimi 2 vanno in testa
giorni.rotate(2)
print(giorni)
# Output atteso: deque(['Sab', 'Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven'])

# Rotazione a sinistra di 1: il primo va in coda
giorni.rotate(-1)
print(giorni)
# Output atteso: deque(['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'])
```

### Confronto prestazionale: list vs deque

```python
from collections import deque
import time

N = 100_000

# TEST: inserimento in testa
lista = []
t0 = time.perf_counter()
for i in range(N):
    lista.insert(0, i)
t_lista = time.perf_counter() - t0

coda = deque()
t0 = time.perf_counter()
for i in range(N):
    coda.appendleft(i)
t_deque = time.perf_counter() - t0

print(f"list.insert(0,x) x{N:,}: {t_lista:.3f}s")
print(f"deque.appendleft(x) x{N:,}: {t_deque:.3f}s")
rapporto = t_lista / t_deque if t_deque > 0 else float('inf')
print(f"deque e circa {rapporto:.0f}x piu veloce")
# Output atteso (hardware moderno):
# list.insert(0,x) x100,000: 2.847s
# deque.appendleft(x) x100,000: 0.008s
# deque e circa 356x piu veloce
```

### Caso d'uso: coda BFS

```python
from collections import deque

def bfs(grafo: dict, partenza: str) -> list:
    """Visita in ampiezza usando deque come coda efficiente."""
    visitati = set()
    coda = deque([partenza])
    visitati.add(partenza)
    ordine_visita = []

    while coda:
        nodo = coda.popleft()   # O(1) — cruciale per le prestazioni di BFS
        ordine_visita.append(nodo)
        for vicino in grafo.get(nodo, []):
            if vicino not in visitati:
                visitati.add(vicino)
                coda.append(vicino)

    return ordine_visita

grafo = {
    'A': ['B', 'C'],
    'B': ['D', 'E'],
    'C': ['F'],
    'D': [],
    'E': ['F'],
    'F': []
}

print(bfs(grafo, 'A'))
# Output atteso: ['A', 'B', 'C', 'D', 'E', 'F']
```

### Quando usare deque

Usa `deque` quando:
- Hai bisogno di inserire e rimuovere da **entrambe** le estremita frequentemente
- Implementi una coda FIFO, uno stack LIFO o una coda bidirezionale
- Hai bisogno di un buffer circolare con dimensione massima fissa (maxlen)
- Implementi BFS, DFS iterativo, sliding window

Non usare `deque` quando:
- Hai bisogno di accesso per indice frequente (usa list)
- Vuoi solo uno stack: list con append()/pop() e altrettanto veloce

---

## namedtuple — Analogia: modulo compilato vs foglio bianco {#namedtuple}

### Cosa e namedtuple?

Immagina di archiviare le informazioni di uno studente con una tupla normale:

```python
studente = ('Alice', 'Rossi', 'A12345', 28.5)
print(studente[2])   # qual e l'indice 2? — poco chiaro
```

Questo e il **foglio bianco**: ci puoi scrivere tutto, ma dopo non sai cosa c'e scritto senza rileggere tutto dall'inizio.

Con `namedtuple` e come un **modulo compilato** con campi etichettati:

```python
from collections import namedtuple

Studente = namedtuple('Studente', ['nome', 'cognome', 'matricola', 'media'])
alice = Studente('Alice', 'Rossi', 'A12345', 28.5)
print(alice.matricola)   # 'A12345' — chiaro e leggibile
```

### Complessita Big-O di namedtuple

`namedtuple` e una sottoclasse di `tuple`. Le sue complessita sono identiche:

| Operazione | Complessita |
|------------|-------------|
| Accesso per nome nt.campo | O(1) |
| Accesso per indice nt[i] | O(1) |
| Creazione | O(n) — n = numero di campi |
| Confronto con == | O(n) |
| Hashing | O(n) calcolato una volta, poi cached |
| Memoria | Minima — e una tupla, senza __dict__ |

### Creazione e sintassi

```python
from collections import namedtuple

# Sintassi 1: lista di nomi
Punto = namedtuple('Punto', ['x', 'y', 'z'])

# Sintassi 2: stringa separata da spazi
Colore = namedtuple('Colore', 'rosso verde blu')

# Sintassi 3: stringa separata da virgole
Prodotto = namedtuple('Prodotto', 'nome, prezzo, categoria')

# Creazione di istanze
p = Punto(1.5, 2.7, 0.0)
prod = Prodotto('Mela', 1.50, 'frutta')

# Accesso per nome (come un oggetto)
print(f"Coordinate: x={p.x}, y={p.y}, z={p.z}")
# Output atteso: Coordinate: x=1.5, y=2.7, z=0.0

# Accesso per indice (come una tupla)
print(f"Prezzo: {prod[1]}")
# Output atteso: Prezzo: 1.5

# Unpacking (come una tupla)
nome, prezzo, categoria = prod
print(f"{nome} ({categoria}): euro {prezzo}")
# Output atteso: Mela (frutta): euro 1.5
```

### Metodi speciali di namedtuple

```python
from collections import namedtuple

Studente = namedtuple('Studente', ['nome', 'matricola', 'media'])
alice = Studente('Alice', 'A12345', 28.5)

# _asdict(): converte in dizionario (utile per serializzazione)
d = alice._asdict()
print(d)
# Output atteso: {'nome': 'Alice', 'matricola': 'A12345', 'media': 28.5}

# _replace(): crea una NUOVA istanza con alcuni campi modificati
# (l'originale e immutabile e resta invariata)
alice_promossa = alice._replace(media=30.0)
print(alice)          # Studente(nome='Alice', matricola='A12345', media=28.5)
print(alice_promossa) # Studente(nome='Alice', matricola='A12345', media=30.0)

# _fields: nomi dei campi come tupla
print(Studente._fields)
# Output atteso: ('nome', 'matricola', 'media')

# _make(): crea istanza da qualsiasi iterabile
riga_csv = ['Bob', 'B99001', '25.3']
bob = Studente._make(riga_csv)
print(bob)
# Output atteso: Studente(nome='Bob', matricola='B99001', media='25.3')
```

### Valori di default

```python
from collections import namedtuple

# I default si applicano agli ULTIMI N campi
Connessione = namedtuple(
    'Connessione',
    ['host', 'porta', 'protocollo'],
    defaults=['localhost', 5432, 'tcp']
)

c1 = Connessione()
print(c1)
# Output atteso: Connessione(host='localhost', porta=5432, protocollo='tcp')

c2 = Connessione(host='db.produzione.it')
print(c2)
# Output atteso: Connessione(host='db.produzione.it', porta=5432, protocollo='tcp')
```

### typing.NamedTuple — la versione moderna con type hints

```python
from typing import NamedTuple

class Dipendente(NamedTuple):
    nome: str
    reparto: str
    stipendio: float
    anni_esperienza: int = 0  # valore di default

laura = Dipendente('Laura', 'Ingegneria', 52000.0, 7)
marco = Dipendente('Marco', 'Marketing', 38000.0)

print(laura)
# Output atteso: Dipendente(nome='Laura', reparto='Ingegneria', stipendio=52000.0, anni_esperienza=7)

print(marco.anni_esperienza)   # 0

# Si comporta come tuple: hashable, confrontabile, unpackable
print(hash(laura))   # un numero hash valido
a, b, c, d = laura   # unpacking funziona
```

### namedtuple vs dataclass: guida rapida

| Quando usare | namedtuple / NamedTuple | dataclass |
|--------------|------------------------|-----------|
| Dati immutabili | Perfetto | Solo con frozen=True |
| Accesso per indice | Si (e una tupla) | No |
| Unpacking | Si | No |
| Metodi personalizzati | Limitati | Pieno supporto |
| Ereditarieta | Fragile | Pieno supporto |
| Memoria | Minima (tupla) | Maggiore (ha __dict__) |

**Regola pratica:** usa `NamedTuple` per record di dati semplici e immutabili. Usa `@dataclass` per entita di dominio con logica e comportamento.

### Caso d'uso: parsing CSV con NamedTuple

```python
from typing import NamedTuple
import csv
from io import StringIO
from collections import defaultdict

class Transazione(NamedTuple):
    data: str
    importo: float
    categoria: str
    descrizione: str

csv_raw = """data,importo,categoria,descrizione
2026-01-15,45.50,alimentari,Supermercato Coop
2026-01-16,12.00,trasporti,Autobus mensile
2026-01-17,89.99,elettronica,Cavo USB-C
2026-01-18,200.00,stipendio,Accredito febbraio
"""

reader = csv.DictReader(StringIO(csv_raw))
transazioni = [
    Transazione(
        data=row['data'],
        importo=float(row['importo']),
        categoria=row['categoria'],
        descrizione=row['descrizione']
    )
    for row in reader
]

# Totale per categoria
per_categoria = defaultdict(float)
for t in transazioni:
    per_categoria[t.categoria] += t.importo

for cat, totale in sorted(per_categoria.items()):
    print(f"  {cat}: euro {totale:.2f}")
# Output atteso:
#   alimentari: euro 45.50
#   elettronica: euro 89.99
#   stipendio: euro 200.00
#   trasporti: euro 12.00
```

---

## OrderedDict — Dizionario con memoria dell'ordine {#ordereddict}

### Cosa e OrderedDict e perche esiste ancora?

Dalla versione 3.7, i `dict` normali mantengono gia l'ordine di inserimento. Allora perche esiste ancora `OrderedDict`?

La risposta sta in due funzionalita uniche:

1. **`move_to_end()`**: sposta una chiave in cima o in fondo in O(1)
2. **Confronto order-sensitive**: due `OrderedDict` sono uguali solo se hanno le stesse chiavi nello stesso ordine

```python
from collections import OrderedDict

# Con dict normale: confronto order-agnostic
d1 = {'a': 1, 'b': 2}
d2 = {'b': 2, 'a': 1}
print(d1 == d2)   # True — stessi elementi, diverso ordine

# Con OrderedDict: il confronto e order-sensitive
od1 = OrderedDict([('a', 1), ('b', 2)])
od2 = OrderedDict([('b', 2), ('a', 1)])
print(od1 == od2)   # False — stesso contenuto, ordine diverso
```

### Complessita Big-O di OrderedDict

| Operazione | Complessita | Note |
|------------|-------------|------|
| Inserimento od[k] = v | O(1) | |
| Accesso od[k] | O(1) | |
| move_to_end(k) | O(1) | Doubly-linked list interna |
| popitem(last=True/False) | O(1) | Da inizio o da fine |
| Memoria | Circa 50% in piu di dict | Due puntatori aggiuntivi per entry |

### Operazioni specifiche

```python
from collections import OrderedDict

negozio = OrderedDict()
negozio['mela'] = 3
negozio['banana'] = 7
negozio['pera'] = 2
negozio['kiwi'] = 5

print("Ordine originale:", list(negozio.keys()))
# Output atteso: ['mela', 'banana', 'pera', 'kiwi']

# move_to_end: sposta 'mela' in fondo
negozio.move_to_end('mela')
print("Dopo move_to_end('mela'):", list(negozio.keys()))
# Output atteso: ['banana', 'pera', 'kiwi', 'mela']

# move_to_end con last=False: sposta in testa
negozio.move_to_end('mela', last=False)
print("Dopo move_to_end('mela', last=False):", list(negozio.keys()))
# Output atteso: ['mela', 'banana', 'pera', 'kiwi']

# popitem rimuove e restituisce l'ultimo o il primo
ultimo = negozio.popitem(last=True)
print(f"Rimosso (ultimo): {ultimo}")
# Output atteso: Rimosso (ultimo): ('kiwi', 5)

primo = negozio.popitem(last=False)
print(f"Rimosso (primo): {primo}")
# Output atteso: Rimosso (primo): ('mela', 3)
```

### Caso d'uso principale: Cache LRU

```python
from collections import OrderedDict
from typing import Any, Optional

class CacheLRU:
    """Cache Least Recently Used implementata con OrderedDict."""

    def __init__(self, capacita: int):
        if capacita <= 0:
            raise ValueError("La capacita deve essere positiva")
        self._capacita = capacita
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def get(self, chiave: str) -> Optional[Any]:
        """Legge dalla cache. Se esiste, lo marca come piu recente."""
        if chiave not in self._cache:
            return None
        self._cache.move_to_end(chiave)  # sposta in cima
        return self._cache[chiave]

    def put(self, chiave: str, valore: Any) -> None:
        """Inserisce in cache. Se piena, rimuove il meno recente."""
        if chiave in self._cache:
            self._cache.move_to_end(chiave)
        self._cache[chiave] = valore
        if len(self._cache) > self._capacita:
            self._cache.popitem(last=False)  # rimuove il piu vecchio

    def __repr__(self) -> str:
        return f"CacheLRU({dict(self._cache)})"

# Test
cache = CacheLRU(capacita=3)
cache.put('home', 'pagina home')
cache.put('about', 'pagina about')
cache.put('contatti', 'pagina contatti')
print(cache)

cache.get('home')   # home diventa la piu recente
cache.put('blog', 'pagina blog')  # about viene rimossa (la meno recente)
print(cache)
# Output atteso:
# CacheLRU({'home': 'pagina home', 'about': 'pagina about', 'contatti': 'pagina contatti'})
# CacheLRU({'contatti': 'pagina contatti', 'home': 'pagina home', 'blog': 'pagina blog'})
```

---

## ChainMap — Configurazioni a livelli {#chainmap}

### Cosa e ChainMap?

Immagina di cercare un documento. Prima guardi sulla tua scrivania. Se non lo trovi, guardi nel cassetto. Se neanche li, guardi nell'archivio comune. La ricerca si ferma alla prima corrispondenza trovata.

`ChainMap` raggruppa piu dizionari in una vista unica. La ricerca attraversa i dizionari nell'ordine in cui li hai forniti.

```python
from collections import ChainMap

config_sessione = {'font_size': 16}
config_utente   = {'tema': 'scuro', 'font_size': 14}
config_default  = {'tema': 'chiaro', 'lingua': 'it', 'font_size': 12}

config = ChainMap(config_sessione, config_utente, config_default)

print(config['font_size'])  # 16  (dalla sessione, massima priorita)
print(config['tema'])       # scuro (dall'utente)
print(config['lingua'])     # it   (solo nel default)
```

### Complessita Big-O di ChainMap

| Operazione | Complessita | Note |
|------------|-------------|------|
| Creazione | O(1) | Nessuna copia dei dati |
| Lettura chain[k] | O(k) medio | k = numero mappe attraversate |
| Scrittura chain[k] = v | O(1) | Solo sulla PRIMA mappa |
| Cancellazione | O(1) | Solo dalla prima mappa |
| Iterazione | O(n) | n = chiavi totali uniche |

### Regola fondamentale: le scritture vanno sempre nella prima mappa

```python
from collections import ChainMap

base = {'x': 1, 'y': 2}
overlay = {}
chain = ChainMap(overlay, base)

# La scrittura va SEMPRE nel primo mapping
chain['x'] = 99
print(f"overlay: {overlay}")   # {'x': 99}
print(f"base:    {base}")      # {'x': 1} — invariato!

# Leggere: si vede il valore dell'overlay
print(chain['x'])  # 99

# Per rimuovere, usiamo il metodo diretto su overlay
# chain['y'] non puo essere cancellato (non e' nell'overlay)
# ma overlay['y'] non esiste — solo base lo ha
```

### new_child e parents — scope annidati

```python
from collections import ChainMap

# Modello di scope per un mini-interprete
scope_globale = {'pi': 3.14159, 'debug': False}
scope = ChainMap(scope_globale)

# Entrata in una funzione: nuovo scope figlio
scope = scope.new_child({'x': 10, 'y': 20})
print(scope['pi'])   # 3.14159 — variabile globale visibile
print(scope['x'])    # 10 — variabile locale

# Entrata in una funzione annidata: ombreggia 'x'
scope = scope.new_child({'x': 99, 'z': 5})
print(scope['x'])    # 99 — shadow della variabile locale esterna
print(scope['y'])    # 20 — dall'ambito esterno

# Ritorno dalla funzione annidata
scope = scope.parents
print(scope['x'])    # 10 — ripristinato
print('z' in scope)  # False — 'z' era solo nella funzione annidata

# Ritorno dalla funzione esterna
scope = scope.parents
print('x' in scope)  # False — 'x' era locale
print(scope['pi'])   # 3.14159 — globale sempre visibile

# Output atteso (in sequenza):
# 3.14159, 10, 99, 20, 10, False, False, 3.14159
```

### ChainMap vs merge di dizionari

```python
from collections import ChainMap

base = {'a': 1, 'b': 2}
extra = {'b': 99, 'c': 3}

# Merge con ** (copia statica — snapshot)
merged = {**base, **extra}
base['a'] = 100
print(merged['a'])   # 1 — non vede la modifica (copia)

# ChainMap (vista live)
chain = ChainMap(extra, base)
print(chain['a'])    # 100 — vede la modifica a base!
```

| Aspetto | ChainMap | Merge con ** |
|---------|----------|--------------|
| Costo creazione | O(1) | O(n) copia tutto |
| Propagazione modifiche | Si (vista live) | No (copia) |
| Ispezione per livello | Si con .maps | No |
| Scrittura | Solo prima mappa | Sul dizionario risultante |
| Caso ideale | Config a livelli, scope | Merge definitivo e semplice |

### Quando usare ChainMap

Usa `ChainMap` quando:
- Hai configurazioni a livelli (default, utente, sessione, CLI)
- Vuoi modellare scope di variabili per un interprete
- Hai bisogno di override temporanei senza copiare dati

Non usare `ChainMap` quando:
- Vuoi un solo dizionario finale (usa `{**d1, **d2}`)
- Hai accessi molto frequenti (ogni ricerca attraversa tutti i livelli)

---

## Riepilogo Parte A — Blocco 2

In questo secondo blocco abbiamo completato la Parte A con:

4. **deque**: coda bidirezionale. Inserimento e rimozione O(1) da entrambi i lati. Ideale per BFS, buffer circolari con maxlen, sliding window. Attenzione: accesso per indice e O(n).

5. **namedtuple / NamedTuple**: modulo compilato. Immutabile, leggero (e una tupla), accessibile per nome e per indice, con unpacking. Preferire `typing.NamedTuple` per i type hints.

6. **OrderedDict**: dizionario con confronto order-sensitive e `move_to_end()` O(1). Caso d'uso principale: cache LRU manuale.

7. **ChainMap**: vista live su piu dizionari. Ricerca sequenziale, scrittura solo sul primo layer. Ideale per configurazioni a livelli e scope annidati.

Nel Blocco 3 (Parte B) esploreremo le strutture orientate all'efficienza algoritmica: `heapq`, `bisect`, `array`, `memoryview` ed `enum`.


---

## Parte B — Strutture per efficienza algoritmica {#parte-b}

---

## heapq — Analogia: pronto soccorso con triage {#heapq}

### Cosa e heapq?

Immagina il pronto soccorso di un ospedale. Quando arrivano i pazienti, non vengono visitati in ordine di arrivo, ma in ordine di gravita: chi ha una crisi cardiaca viene visto prima di chi ha un taglio al dito, anche se e arrivato dopo.

Questo sistema si chiama **triage**: assegnare una priorita a ogni paziente e trattare sempre prima quello piu grave.

Il modulo `heapq` implementa esattamente questo sistema: una **coda di priorita** (priority queue) dove puoi sempre estrarre l'elemento con il valore minore in O(log n).

**Struttura dati interna:** un min-heap e un albero binario completo dove ogni nodo padre e minore o uguale ai suoi figli. Python lo rappresenta con una lista normale. L'elemento all'indice 0 e sempre il minimo.

```
         1
       /   \
      3     2
     / \   / \
    5   4 8   7
```

In lista: `[1, 3, 2, 5, 4, 8, 7]` — l'heap e implicito nella struttura.

### Complessita Big-O di heapq

| Operazione | Complessita | Note |
|------------|-------------|------|
| `heappush(h, x)` | O(log n) | Inserimento mantenendo heap property |
| `heappop(h)` | O(log n) | Estrazione del minimo |
| `heapify(lista)` | O(n) | Trasforma lista in heap in-place |
| `heappushpop(h, x)` | O(log n) | push + pop combinati (piu veloce) |
| `nlargest(k, data)` | O(n log k) | I k elementi piu grandi |
| `nsmallest(k, data)` | O(n log k) | I k elementi piu piccoli |
| Lettura minimo `h[0]` | O(1) | Senza rimozione |

### Operazioni fondamentali

```python
import heapq

# heapify: trasforma una lista qualsiasi in un heap (in-place)
pazienti = [5, 3, 8, 1, 9, 2, 7]
heapq.heapify(pazienti)
print(pazienti)
# Output atteso: [1, 3, 2, 5, 9, 8, 7]
# NOTA: la lista non e' ordinata! Il heap garantisce solo che pazienti[0] e' il minimo

# heappush: inserisce un nuovo paziente mantenendo l'ordinamento
heapq.heappush(pazienti, 0)
print(pazienti[0])
# Output atteso: 0  (nuovo minimo)

# heappop: estrae e rimuove il paziente piu urgente (il minimo)
urgente = heapq.heappop(pazienti)
print(urgente)
# Output atteso: 0

# Lettura senza rimozione: pazienti[0] e' sempre il minimo
print(pazienti[0])
# Output atteso: 1  (il prossimo minimo)
```

### Il triage in codice: coda di priorita

```python
import heapq
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class Paziente:
    priorita: int         # 1 = critico, 5 = non urgente
    numero_arrivo: int    # per rompere i pareggi (chi e' arrivato prima)
    nome: str = field(compare=False)
    sintomi: str = field(compare=False)

class ProntoSoccorso:
    def __init__(self):
        self._coda: list[Paziente] = []
        self._contatore = 0

    def ammetti(self, nome: str, sintomi: str, priorita: int) -> None:
        """Ammette un nuovo paziente con la sua priorita di triage."""
        paziente = Paziente(
            priorita=priorita,
            numero_arrivo=self._contatore,
            nome=nome,
            sintomi=sintomi
        )
        heapq.heappush(self._coda, paziente)
        self._contatore += 1
        print(f"  [AMMESSO] {nome} — priorita {priorita} — '{sintomi}'")

    def chiama_prossimo(self) -> Paziente | None:
        """Chiama il paziente piu urgente."""
        if not self._coda:
            return None
        return heapq.heappop(self._coda)

    def __len__(self) -> int:
        return len(self._coda)

# Simulazione
ps = ProntoSoccorso()
print("Arrivi in ordine casuale:")
ps.ammetti("Mario", "taglio lieve", priorita=4)
ps.ammetti("Laura", "infarto sospetto", priorita=1)
ps.ammetti("Giovanni", "febbre alta", priorita=3)
ps.ammetti("Elena", "frattura", priorita=2)
ps.ammetti("Carlo", "mal di testa", priorita=5)

print("\nOrdine di visita (per priorita):")
while len(ps) > 0:
    p = ps.chiama_prossimo()
    print(f"  -> {p.nome} (priorita {p.priorita}): {p.sintomi}")

# Output atteso:
# Arrivi in ordine casuale:
#   [AMMESSO] Mario — priorita 4 — 'taglio lieve'
#   [AMMESSO] Laura — priorita 1 — 'infarto sospetto'
#   ...
# Ordine di visita (per priorita):
#   -> Laura (priorita 1): infarto sospetto
#   -> Elena (priorita 2): frattura
#   -> Giovanni (priorita 3): febbre alta
#   -> Mario (priorita 4): taglio lieve
#   -> Carlo (priorita 5): mal di testa
```

### nlargest e nsmallest

```python
import heapq

punteggi_gara = [85, 92, 78, 95, 88, 72, 90, 98, 65, 82]

# I 3 migliori punteggi (podio)
podio = heapq.nlargest(3, punteggi_gara)
print("Podio:", podio)
# Output atteso: Podio: [98, 95, 92]

# I 3 peggiori punteggi (eliminati)
eliminati = heapq.nsmallest(3, punteggi_gara)
print("Eliminati:", eliminati)
# Output atteso: Eliminati: [65, 72, 78]

# Con key: i 2 studenti con la media piu alta
studenti = [
    {'nome': 'Alice', 'media': 28.5},
    {'nome': 'Bob', 'media': 25.0},
    {'nome': 'Carlo', 'media': 30.0},
    {'nome': 'Diana', 'media': 27.3},
]
top2 = heapq.nlargest(2, studenti, key=lambda s: s['media'])
print([s['nome'] for s in top2])
# Output atteso: ['Carlo', 'Alice']
```

**Quando usare nlargest/nsmallest vs sorted:**
- `k` molto piccolo rispetto a `n`: usa `heapq.nlargest(k, data)` — O(n log k)
- `k` vicino a `n`: usa `sorted(data, reverse=True)[:k]` — O(n log n) ma piu semplice
- `k == 1`: usa `max(data)` o `min(data)` — O(n), il piu veloce

### Max-heap: il trucco della negazione

`heapq` implementa solo un min-heap. Per simulare un max-heap, nega i valori:

```python
import heapq

max_heap = []
valori = [5, 3, 8, 1, 9, 2]

# Inserisci i negativi
for v in valori:
    heapq.heappush(max_heap, -v)

# Estrai il massimo (negate il segno)
massimo = -heapq.heappop(max_heap)
print(massimo)   # 9

secondo = -heapq.heappop(max_heap)
print(secondo)   # 8
```

---

## bisect — Analogia: elenco telefonico {#bisect}

### Cosa e bisect?

Prima dei motori di ricerca digitali, trovare un numero sull'elenco telefonico era un'arte. Non iniziavi dalla prima pagina: aprivi il libro a meta, guardavi la lettera, capivi se il cognome che cercavi veniva prima o dopo, poi dimezzavi ancora quella meta, e cosi via.

In pochi passaggi (al massimo 20 per un milione di nomi) trovavi il numero. Questo algoritmo si chiama **ricerca binaria** e il modulo `bisect` la implementa per liste Python ordinate.

### Complessita Big-O di bisect

| Operazione | Complessita | Note |
|------------|-------------|------|
| `bisect_left(a, x)` | O(log n) | Trova posizione di inserimento |
| `bisect_right(a, x)` | O(log n) | Come sopra, a destra dei duplicati |
| `insort_left(a, x)` | O(n) | Inserisce in posizione (shift O(n)) |
| `insort_right(a, x)` | O(n) | Come sopra, a destra dei duplicati |

**Nota importante:** la ricerca e O(log n), ma l'inserimento rimane O(n) perche spostare elementi in una lista e lineare. Per inserimenti frequenti su grandi dataset, usa la libreria `sortedcontainers`.

### Operazioni base

```python
import bisect

elenco = [10, 20, 30, 40, 50]

# bisect_left: dove andrebbe inserito 30 (a sinistra dei duplicati)
pos = bisect.bisect_left(elenco, 30)
print(pos)   # 2
# Output: l'indice 2 e dove c'e' gia 30

# bisect_right (alias bisect): dove andrebbe inserito 30 (a destra dei duplicati)
pos = bisect.bisect_right(elenco, 30)
print(pos)   # 3
# Output: dopo il 30 esistente

# bisect per valore non presente
pos_25 = bisect.bisect_left(elenco, 25)
print(pos_25)   # 2
# Output: 25 andrebbe tra 20 (indice 1) e 30 (indice 2)

# insort: inserisce mantenendo l'ordine
bisect.insort(elenco, 25)
print(elenco)
# Output atteso: [10, 20, 25, 30, 40, 50]

bisect.insort(elenco, 30)
print(elenco)
# Output atteso: [10, 20, 25, 30, 30, 40, 50]
```

### Pattern 1: ricerca binaria su lista ordinata

```python
import bisect

def cerca_binaria(sequenza: list, valore) -> int:
    """Ricerca binaria. Restituisce l'indice o -1 se non trovato."""
    i = bisect.bisect_left(sequenza, valore)
    if i < len(sequenza) and sequenza[i] == valore:
        return i
    return -1

dati = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]

print(cerca_binaria(dati, 23))    # 5
print(cerca_binaria(dati, 24))    # -1
print(cerca_binaria(dati, 2))     # 0
print(cerca_binaria(dati, 91))    # 9
```

### Pattern 2: mappatura a intervalli (voti scolastici)

Uno degli usi piu eleganti di `bisect`: mappare un valore numerico alla sua categoria senza catene di `if-elif`.

```python
import bisect

def assegna_voto(punteggio: int) -> str:
    """Mappa un punteggio 0-100 a un voto letterale."""
    # La soglia e la SINISTRA del voto superiore
    soglie = [60, 70, 80, 90]
    voti   = ['F', 'D', 'C', 'B', 'A']
    return voti[bisect.bisect(soglie, punteggio)]

for p in [0, 59, 60, 65, 70, 77, 80, 85, 90, 95, 100]:
    print(f"{p:3d} -> {assegna_voto(p)}")
# Output atteso:
#   0 -> F
#  59 -> F
#  60 -> D
#  65 -> D
#  70 -> C
#  77 -> C
#  80 -> B
#  85 -> B
#  90 -> A
#  95 -> A
# 100 -> A
```

### Pattern 3: lista sempre ordinata

```python
import bisect

class ListaOrdinata:
    """Lista che mantiene sempre l'ordine. Inserimento O(n), ricerca O(log n)."""

    def __init__(self, iterable=()):
        self._dati = sorted(iterable)

    def aggiungi(self, valore) -> None:
        bisect.insort(self._dati, valore)

    def rimuovi(self, valore) -> None:
        i = bisect.bisect_left(self._dati, valore)
        if i < len(self._dati) and self._dati[i] == valore:
            self._dati.pop(i)
        else:
            raise ValueError(f"{valore!r} non trovato")

    def __contains__(self, valore) -> bool:
        i = bisect.bisect_left(self._dati, valore)
        return i < len(self._dati) and self._dati[i] == valore

    def __repr__(self) -> str:
        return f"ListaOrdinata({self._dati})"

sl = ListaOrdinata([5, 2, 8, 1, 9])
sl.aggiungi(3)
sl.aggiungi(7)
print(sl)
# Output atteso: ListaOrdinata([1, 2, 3, 5, 7, 8, 9])

print(3 in sl)    # True
print(6 in sl)    # False
sl.rimuovi(5)
print(sl)
# Output atteso: ListaOrdinata([1, 2, 3, 7, 8, 9])
```

---

## array vs list vs NumPy {#array}

### La domanda: perche avere tre modi per memorizzare numeri?

In Python hai tre modi per memorizzare una sequenza di numeri:

| | `list` | `array.array` | `numpy.ndarray` |
|-|--------|---------------|-----------------|
| Tipi | Qualsiasi oggetto Python | Un solo tipo C (int, float...) | Un solo tipo numerico |
| Memoria | Alta (ogni elemento e' un PyObject) | Bassa (valori C puri) | Bassa + layout ottimizzato |
| Velocita' calcoli | Lenta (loop Python) | Lenta (loop Python) | Molto veloce (C/BLAS vettorizzato) |
| Flessibilita' | Massima | Bassa | Media |
| Interop C/binario | No | Si | Si |
| Installazione | Built-in | Built-in | pip install numpy |

### Quando usare array.array

```python
from array import array
import sys

# Creazione: 'i' = signed int (4 byte), 'd' = double (8 byte)
# Codici principali: 'b' char, 'h' short, 'i' int, 'l' long, 'f' float, 'd' double
numeri = array('i', [1, 2, 3, 4, 5, 100_000])

# Operazioni simili a list
numeri.append(6)
numeri.extend([7, 8, 9])
print(numeri[2])         # 3
print(numeri.tolist())   # [1, 2, 3, 4, 5, 100000, 6, 7, 8, 9]

# DIFFERENZA CHIAVE: il tipo e' forzato
try:
    numeri.append(3.14)  # TypeError: intero richiesto
except TypeError as e:
    print(f"Errore: {e}")
```

### Confronto di memoria reale

```python
import sys
from array import array

N = 100_000

# list di interi
lista_int = list(range(N))

# array di interi (tipo 'i' = 4 byte per elemento)
array_int = array('i', range(N))

mem_lista = sys.getsizeof(lista_int)
mem_array = sys.getsizeof(array_int)

print(f"list:  {mem_lista:>10,} byte")
print(f"array: {mem_array:>10,} byte")
print(f"Risparmio: {(mem_lista - mem_array) / mem_lista * 100:.1f}%")

# Output atteso (64-bit Python):
# list:     800,056 byte
# array:    400,064 byte
# Risparmio: 50.0%

# Ma c'e' anche l'overhead per-elemento della list!
# Ogni int in una list e' un oggetto Python da ~28 byte.
# Totale reale lista: ~800.056 + ~2.800.000 byte per i PyObject
# array: solo 400.064 byte totali
# Risparmio reale: ~87%
```

### Quando usare cosa

- **`list`**: quando hai elementi eterogenei, quando la flessibilita e prioritaria, per la maggior parte del codice Python quotidiano
- **`array.array`**: quando hai migliaia/milioni di numeri omogenei, per I/O binario con codice C, per risparmio di memoria senza dipendenze
- **`numpy.ndarray`**: quando hai bisogno di calcoli numerici vettorizzati (somme, prodotti matriciali, FFT), analisi dati, machine learning

---

## memoryview — Analogia: finestra su un muro {#memoryview}

### Cosa e memoryview?

Immagina un muro lungo 100 metri. Vuoi vedere la sezione tra il metro 30 e il metro 50. Puoi:

**Opzione A (senza memoryview):** costruire un nuovo muro di 20 metri, copiarci la sezione che ti interessa, e poi guardarla.

**Opzione B (con memoryview):** mettere una finestra nel muro originale tra il metro 30 e il metro 50. Guardi la stessa parete, senza costruire nulla di nuovo.

`memoryview` e la finestra: ti permette di lavorare su porzioni di un buffer di byte senza copiarlo.

### Complessita Big-O di memoryview

| Operazione | Complessita senza memoryview | Con memoryview |
|------------|------------------------------|----------------|
| Slicing `data[a:b]` | O(b-a) — copia b-a byte | O(1) — nessuna copia |
| Lettura elemento | O(1) | O(1) |
| Scrittura elemento (se writable) | O(1) | O(1) |
| Creazione della vista | — | O(1) |

### Utilizzo base

```python
# Senza memoryview: ogni slice crea una copia
dati = b'\x00' * 10_000_000   # 10 MB di byte
parte_copia = dati[1_000:2_000]   # COPIA 1000 byte

# Con memoryview: slice a costo zero
vista = memoryview(dati)
parte_mv = vista[1_000:2_000]   # NESSUNA COPIA — punta alla stessa memoria

print(len(parte_mv))            # 1000
print(bytes(parte_mv[:5]))      # b'\x00\x00\x00\x00\x00'
```

### Parsing binario senza copie

```python
import struct

# Simulare un pacchetto di rete: header (8 byte) + payload (1016 byte)
pacchetto = bytearray(1024)
struct.pack_into('!HIH', pacchetto, 0, 1, 1016, 0xABCD)

mv = memoryview(pacchetto)
header  = mv[:8]      # vista sull'header
payload = mv[8:]      # vista sul payload

versione, lunghezza, checksum = struct.unpack_from('!HIH', header)
print(f"Versione: {versione}")
print(f"Lunghezza payload: {lunghezza} byte")
print(f"Checksum: {checksum:#06x}")
# Output atteso:
# Versione: 1
# Lunghezza payload: 1016 byte
# Checksum: 0xabcd

# Modifica in-place (bytearray e' writable)
mv[0] = 2   # cambia il primo byte direttamente nel pacchetto originale
print(pacchetto[0])   # 2 — la modifica e' avvenuta nel buffer originale!
```

### memoryview con array tipizzati

```python
from array import array

a = array('i', [1, 2, 3, 4, 5, 6, 7, 8])
mv = memoryview(a)

# Slicing senza copia
sotto_array = mv[2:5]
print(list(sotto_array))   # [3, 4, 5]

# Modifica in-place
mv[0] = 99
print(a[0])   # 99 — la modifica si riflette nell'array originale

# Cast a byte per analisi binaria (little-endian su x86)
mv_bytes = mv.cast('B')
print(mv_bytes.tolist()[:4])
# Output (per valore 99 in little-endian 32-bit): [99, 0, 0, 0]
```

### Quando usare memoryview

Usa `memoryview` quando:
- Stai parsando file binari grandi (WAV, BMP, MP4, pacchetti TCP)
- Vuoi lavorare su sottoinsiemi di grandi buffer senza copiarli
- Vuoi modificare in-place una porzione di un buffer (bytearray o array)
- Scrivi codice ad alte prestazioni dove la copia dei dati e un collo di bottiglia

Non usare `memoryview` quando:
- Stai lavorando con file di testo o stringhe (usa `str` e il file I/O standard)
- La semplicita e prioritaria sulla memoria
- Il buffer e piccolo (la copia e trascurabile)

---

## enum — Analogia: semaforo {#enum}

### Cosa e enum?

Un semaforo ha tre stati: ROSSO, GIALLO, VERDE. Non ha uno stato "4". Non ha uno stato "giallo chiaro" o "rosso scuro". Gli stati sono **finiti, nominati e mutuamente esclusivi**.

Senza `enum`, potresti rappresentare questi stati con interi (0, 1, 2) o stringhe ('rosso', 'giallo', 'verde'). Ma nulla ti impedisce di scrivere `stato = 99` o `stato = 'viola'` — errori silenziosi difficili da trovare.

`enum` risolve questo problema: definisce un insieme chiuso di valori nominati, con controllo a compile-time.

```python
from enum import Enum, auto

class Semaforo(Enum):
    ROSSO  = auto()   # auto() assegna automaticamente 1, 2, 3...
    GIALLO = auto()
    VERDE  = auto()

print(Semaforo.ROSSO)          # Semaforo.ROSSO
print(Semaforo.ROSSO.value)    # 1
print(Semaforo.ROSSO.name)     # 'ROSSO'
print(type(Semaforo.ROSSO))    # <enum 'Semaforo'>
```

### Complessita e overhead di enum

Gli enum non sono strutture dati nel senso algoritmico. Non hanno complessita O(n). Sono:
- **Confronto** `==` : O(1) (confronto di identita)
- **Lookup per nome** `Semaforo['ROSSO']` : O(1)
- **Lookup per valore** `Semaforo(1)` : O(1)
- **Iterazione** `for s in Semaforo` : O(n) dove n = numero di membri

### Tipi di Enum

```python
from enum import Enum, IntEnum, Flag, auto

# Enum base: membri non sono interi direttamente
class Colore(Enum):
    ROSSO = 1
    VERDE = 2
    BLU = 3

# IntEnum: i valori sono interi reali (compatibili con API che richiedono int)
class Priorita(IntEnum):
    BASSA  = 1
    MEDIA  = 2
    ALTA   = 3

# Confronto tra IntEnum e int e' consentito
print(Priorita.ALTA > 2)         # True  (IntEnum si comporta come int)
print(Priorita.ALTA == 3)        # True

# Flag: per bitmask combinabili
class Permesso(Flag):
    LETTURA   = auto()   # 1
    SCRITTURA = auto()   # 2
    ESECUZIONE = auto()  # 4

# Combinare permessi con |
permessi_admin = Permesso.LETTURA | Permesso.SCRITTURA | Permesso.ESECUZIONE
permessi_guest = Permesso.LETTURA

print(permessi_admin)   # Permesso.LETTURA|SCRITTURA|ESECUZIONE
print(Permesso.LETTURA in permessi_admin)   # True
print(Permesso.SCRITTURA in permessi_guest) # False
```

### Il semaforo completo: transizioni di stato

```python
from enum import Enum, auto

class StatoSemaforo(Enum):
    ROSSO  = auto()
    GIALLO = auto()
    VERDE  = auto()

# Dizionario di transizioni: quale stato viene dopo?
TRANSIZIONI: dict[StatoSemaforo, StatoSemaforo] = {
    StatoSemaforo.VERDE:  StatoSemaforo.GIALLO,
    StatoSemaforo.GIALLO: StatoSemaforo.ROSSO,
    StatoSemaforo.ROSSO:  StatoSemaforo.VERDE,
}

def prossimo_stato(attuale: StatoSemaforo) -> StatoSemaforo:
    return TRANSIZIONI[attuale]

# Simulazione di 6 cicli
stato = StatoSemaforo.ROSSO
for _ in range(6):
    print(f"  Stato attuale: {stato.name}")
    stato = prossimo_stato(stato)

# Output atteso:
#   Stato attuale: ROSSO
#   Stato attuale: VERDE
#   Stato attuale: GIALLO
#   Stato attuale: ROSSO
#   Stato attuale: VERDE
#   Stato attuale: GIALLO
```

### Pattern: enum con metodi e dati aggiuntivi

```python
from enum import Enum

class Pianeta(Enum):
    MERCURIO = (3.303e+23, 2.4397e6)
    VENERE   = (4.869e+24, 6.0518e6)
    TERRA    = (5.976e+24, 6.37814e6)
    MARTE    = (6.421e+23, 3.3972e6)

    def __init__(self, massa: float, raggio: float):
        self.massa = massa    # in kg
        self.raggio = raggio  # in m

    def gravita_superficiale(self) -> float:
        """Accelerazione gravitazionale in m/s^2."""
        G = 6.67430e-11
        return G * self.massa / (self.raggio ** 2)

    def peso_su(self, massa_kg: float) -> float:
        """Peso di un oggetto in Newton su questo pianeta."""
        return massa_kg * self.gravita_superficiale()

# Test: quanto peso 70 kg su ogni pianeta?
for pianeta in Pianeta:
    peso = pianeta.peso_su(70)
    print(f"  {pianeta.name:10}: {peso:.1f} N")

# Output atteso:
#   MERCURIO  : 263.3 N
#   VENERE    : 665.5 N
#   TERRA     : 686.0 N
#   MARTE     : 263.1 N
```

### Accesso e confronto

```python
from enum import Enum

class Direzione(Enum):
    NORD = 'N'
    SUD  = 'S'
    EST  = 'E'
    OVEST = 'O'

# Accesso per nome
d = Direzione['NORD']
print(d)   # Direzione.NORD

# Accesso per valore
d2 = Direzione('S')
print(d2)  # Direzione.SUD

# Confronto di identita (usa 'is', non '==')
print(Direzione.NORD is Direzione.NORD)   # True
print(Direzione.NORD == Direzione.NORD)   # True
print(Direzione.NORD is Direzione.SUD)    # False

# Iterazione
print("Tutte le direzioni:")
for d in Direzione:
    print(f"  {d.name}: {d.value}")
# Output:
#   NORD: N
#   SUD: S
#   EST: E
#   OVEST: O

# Protezione da valori invalidi
try:
    Direzione('X')   # ValueError!
except ValueError as e:
    print(f"Errore: {e}")
# Output: Errore: 'X' is not a valid Direzione
```

### Quando usare enum

Usa `enum` quando:
- Hai un insieme finito e fisso di valori nominati (stati, direzioni, colori, livelli)
- Vuoi protezione da valori invalidi a runtime
- Vuoi codice leggibile con nomi espliciti invece di numeri magici
- Implementi macchine a stati finiti
- Vuoi switch-like behavior con dizionari di transizione

Non usare `enum` quando:
- I valori sono dinamici e non noti a priori (usa `dict` o una classe normale)
- Hai bisogno di un semplice intero o stringa in un contesto semplice
- Stai usando API esterne che richiedono tipi primitivi (usa `IntEnum` per compatibilita)

---

## Riepilogo Parte B — Blocco 3

In questo terzo blocco abbiamo esplorato la Parte B, dedicata all'efficienza algoritmica:

8. **heapq**: coda di priorita (min-heap). Estrazione del minimo O(log n). Ideale per triage, scheduling, algoritmo di Dijkstra, k-esimo elemento piu grande/piccolo.

9. **bisect**: ricerca binaria su lista ordinata. Ricerca O(log n), inserimento O(n). Ideale per ricerche, mappatura a intervalli, liste sempre ordinate quando gli inserimenti sono rari.

10. **array.array**: array omogeneo tipizzato. Stesso footprint della memoria C (4-8 byte per elemento vs ~28 per i PyObject). Ideale per grandi dataset numerici, I/O binario, interop con C.

11. **memoryview**: finestra zero-copy su buffer di byte. Slicing O(1) invece di O(n). Ideale per parsing binario, protocolli di rete, elaborazione di grandi buffer.

12. **enum**: insieme chiuso di valori nominati. Protegge da valori invalidi, sostituisce i "magic numbers", abilita macchine a stati leggibili.

Nel Blocco 4 troverai 10 esercizi pratici che combinano tutte queste strutture.


---

## Parte C — 10 Esercizi Pratici {#parte-c}

> Ogni esercizio include: descrizione del problema, struttura dati da usare, scheletro del codice, output atteso, e soluzione completa.

---

### Esercizio 1: Leaderboard con heapq

**Problema:** Implementa una leaderboard per un gioco online. I giocatori possono registrare il loro punteggio in qualsiasi momento. La leaderboard deve:
- Permettere di aggiungere un punteggio per un giocatore
- Restituire sempre i top-K giocatori
- Aggiornare il punteggio se il giocatore ha gia giocato (mantieni il massimo)

**Struttura dati:** `heapq` + `dict`

```python
import heapq

class Leaderboard:
    def __init__(self, top_k: int = 10):
        self._top_k = top_k
        self._punteggi: dict[str, int] = {}   # giocatore -> punteggio massimo

    def registra(self, giocatore: str, punteggio: int) -> None:
        """Registra un punteggio. Tiene il massimo per ogni giocatore."""
        if punteggio > self._punteggi.get(giocatore, -1):
            self._punteggi[giocatore] = punteggio

    def top(self, k: int | None = None) -> list[tuple[str, int]]:
        """Restituisce i migliori k giocatori come lista di (nome, punteggio)."""
        n = k or self._top_k
        return heapq.nlargest(n, self._punteggi.items(), key=lambda x: x[1])

    def posizione(self, giocatore: str) -> int | None:
        """Restituisce la posizione in classifica (1-based) o None se non presente."""
        if giocatore not in self._punteggi:
            return None
        classifica = sorted(self._punteggi.values(), reverse=True)
        return classifica.index(self._punteggi[giocatore]) + 1

# Test
lb = Leaderboard(top_k=3)
lb.registra('Alice', 8500)
lb.registra('Bob', 6200)
lb.registra('Carlo', 9100)
lb.registra('Diana', 7800)
lb.registra('Alice', 9500)   # aggiornamento: Alice ora ha 9500

print("Top 3:")
for nome, score in lb.top(3):
    print(f"  {nome}: {score:,}")

print(f"\nPosizione di Bob: {lb.posizione('Bob')}")
print(f"Posizione di Alice: {lb.posizione('Alice')}")

# Output atteso:
# Top 3:
#   Alice: 9,500
#   Carlo: 9,100
#   Diana: 7,800
#
# Posizione di Bob: 4
# Posizione di Alice: 1
```

---

### Esercizio 2: Analizzatore di testo con Counter

**Problema:** Analizza un testo e produci un report che include:
- Le 10 parole piu frequenti (escluse stop words)
- La frequenza relativa di ogni parola (percentuale)
- Le coppie di parole (bigrammi) piu frequenti
- Statistiche di base (totale parole, parole uniche, densita lessicale)

**Struttura dati:** `Counter` + `zip`

```python
from collections import Counter
import re

STOP_WORDS = {
    'il', 'lo', 'la', 'le', 'gli', 'i', 'un', 'una', 'uno',
    'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
    'e', 'o', 'ma', 'se', 'che', 'non', 'si', 'ne', 'ci',
    'del', 'della', 'dei', 'degli', 'delle', 'al', 'alla',
    'dal', 'dalla', 'nel', 'nella', 'sul', 'sulla', 'col'
}

def analizza_testo(testo: str, top_n: int = 10) -> dict:
    """
    Analizza un testo e restituisce statistiche di frequenza.
    """
    # Tokenizzazione e normalizzazione
    parole_raw = re.findall(r'\b[a-zA-Zà-ùÀ-Ù]+\b', testo.lower())

    # Parole significative (escluse stop words)
    parole_significative = [p for p in parole_raw if p not in STOP_WORDS and len(p) > 2]

    # Conteggio frequenze
    freq = Counter(parole_significative)
    freq_raw = Counter(parole_raw)

    # Bigrammi (coppie di parole consecutive)
    bigrammi = Counter(zip(parole_significative, parole_significative[1:]))

    totale = len(parole_raw)
    uniche = len(freq)

    return {
        'totale_parole': totale,
        'parole_uniche': uniche,
        'densita_lessicale': uniche / totale if totale > 0 else 0,
        'top_parole': freq.most_common(top_n),
        'top_bigrammi': bigrammi.most_common(5),
    }

def stampa_report(analisi: dict) -> None:
    print(f"Statistiche di base:")
    print(f"  Parole totali:  {analisi['totale_parole']:,}")
    print(f"  Parole uniche:  {analisi['parole_uniche']:,}")
    print(f"  Densita lessic: {analisi['densita_lessicale']:.1%}")

    print(f"\nTop {len(analisi['top_parole'])} parole:")
    totale = analisi['totale_parole']
    for parola, count in analisi['top_parole']:
        barra = '#' * int(count / max(c for _, c in analisi['top_parole']) * 20)
        print(f"  {parola:20} {count:4d} ({count/totale:.1%}) {barra}")

    print(f"\nTop bigrammi:")
    for (w1, w2), count in analisi['top_bigrammi']:
        print(f"  '{w1} {w2}': {count}x")

# Test
testo_esempio = """
Python e un linguaggio di programmazione interpretato versatile potente.
Python viene usato per la programmazione web, per l'analisi dei dati
e per il machine learning. Python ha una sintassi chiara e leggibile.
La comunita Python e grande e attiva. Python e ideale per i principianti
e per i programmatori esperti. Imparare Python e divertente e utile.
"""

analisi = analizza_testo(testo_esempio)
stampa_report(analisi)

# Output atteso (estratto):
# Statistiche di base:
#   Parole totali:  37
#   Parole uniche:  22
#   Densita lessic: 59.5%
# Top 10 parole:
#   python               7 (18.9%) ####################
#   programmazione       3  (8.1%) ########
#   ...
```

---

### Esercizio 3: Cache LRU con OrderedDict

**Problema:** Implementa una cache LRU che:
- Supporti `get(key)` e `put(key, value)` con capacita massima
- Supporti scadenza per ogni elemento (TTL in secondi)
- Fornisca statistiche: hit rate, miss rate, evictions
- Supporti `invalidate(key)` per rimozione esplicita

**Struttura dati:** `OrderedDict` + `time`

```python
from collections import OrderedDict
from typing import Any, Optional
import time

class CacheLRUConTTL:
    """Cache LRU con supporto per time-to-live e statistiche."""

    def __init__(self, capacita: int, ttl_default: float = 60.0):
        if capacita <= 0:
            raise ValueError("La capacita deve essere positiva")
        self._capacita = capacita
        self._ttl_default = ttl_default
        # Valore memorizzato: (dato, scadenza_timestamp)
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._hit = 0
        self._miss = 0
        self._eviction = 0

    def get(self, chiave: str) -> Optional[Any]:
        """Legge dalla cache. Restituisce None se assente o scaduto."""
        if chiave not in self._cache:
            self._miss += 1
            return None

        dato, scadenza = self._cache[chiave]

        # Verifica TTL
        if time.monotonic() > scadenza:
            self._cache.__delitem__(chiave)
            self._miss += 1
            return None

        # Hit: sposta in cima (piu recente)
        self._cache.move_to_end(chiave)
        self._hit += 1
        return dato

    def put(self, chiave: str, valore: Any, ttl: Optional[float] = None) -> None:
        """Inserisce in cache con TTL opzionale."""
        scadenza = time.monotonic() + (ttl or self._ttl_default)

        if chiave in self._cache:
            self._cache.move_to_end(chiave)
        self._cache[chiave] = (valore, scadenza)

        # Eviction del piu vecchio se supera la capacita
        if len(self._cache) > self._capacita:
            self._cache.popitem(last=False)
            self._eviction += 1

    def invalidate(self, chiave: str) -> bool:
        """Rimuove esplicitamente una chiave. Restituisce True se esisteva."""
        if chiave in self._cache:
            self._cache.__delitem__(chiave)
            return True
        return False

    @property
    def statistiche(self) -> dict:
        totale = self._hit + self._miss
        return {
            'hit':      self._hit,
            'miss':     self._miss,
            'hit_rate': self._hit / totale if totale > 0 else 0.0,
            'eviction': self._eviction,
            'elementi': len(self._cache),
        }

# Test
cache = CacheLRUConTTL(capacita=3, ttl_default=1.0)

cache.put('a', 'valore_A')
cache.put('b', 'valore_B')
cache.put('c', 'valore_C')

print(cache.get('a'))    # valore_A (hit)
print(cache.get('x'))    # None (miss)

cache.put('d', 'valore_D')   # 'b' viene rimosso (il meno recente dopo 'a')

print(cache.get('b'))    # None (evicted)
print(cache.get('c'))    # valore_C (hit)

stats = cache.statistiche
print(f"\nStatistiche: hit={stats['hit']}, miss={stats['miss']}, "
      f"hit_rate={stats['hit_rate']:.0%}, evictions={stats['eviction']}")

# Output atteso:
# valore_A
# None
# None
# valore_C
# Statistiche: hit=2, miss=2, hit_rate=50%, evictions=1
```

---

### Esercizio 4: Rubrica con defaultdict

**Problema:** Implementa una rubrica che:
- Raggruppa i contatti per la prima lettera del cognome
- Permette ricerche per nome parziale
- Produce una lista ordinata per cognome
- Conta i contatti per lettera

**Struttura dati:** `defaultdict(list)` + `namedtuple`

```python
from collections import defaultdict, Counter
from typing import NamedTuple
import re

class Contatto(NamedTuple):
    nome: str
    cognome: str
    telefono: str
    email: str = ''

class Rubrica:
    def __init__(self):
        # Dizionario lettera -> lista di contatti
        self._per_lettera: defaultdict[str, list[Contatto]] = defaultdict(list)

    def aggiungi(self, contatto: Contatto) -> None:
        """Aggiunge un contatto indicizzato per prima lettera del cognome."""
        lettera = contatto.cognome[0].upper()
        self._per_lettera[lettera].append(contatto)

    def cerca_per_nome(self, query: str) -> list[Contatto]:
        """Cerca contatti per nome o cognome (case-insensitive, match parziale)."""
        query_lower = query.lower()
        risultati = []
        for contatti in self._per_lettera.values():
            for c in contatti:
                if query_lower in c.nome.lower() or query_lower in c.cognome.lower():
                    risultati.append(c)
        return sorted(risultati, key=lambda c: (c.cognome, c.nome))

    def lettera(self, lettera: str) -> list[Contatto]:
        """Restituisce tutti i contatti per una lettera, ordinati per cognome."""
        return sorted(self._per_lettera.get(lettera.upper(), []),
                      key=lambda c: (c.cognome, c.nome))

    def statistiche(self) -> dict:
        conteggi = {k: len(v) for k, v in sorted(self._per_lettera.items())}
        totale = sum(conteggi.values())
        return {'per_lettera': conteggi, 'totale': totale}

    def tutti_ordinati(self) -> list[Contatto]:
        """Lista completa ordinata per cognome, poi nome."""
        tutti = []
        for contatti in self._per_lettera.values():
            tutti.extend(contatti)
        return sorted(tutti, key=lambda c: (c.cognome, c.nome))

# Test
rubrica = Rubrica()
contatti = [
    Contatto('Mario', 'Rossi', '333-111', 'mario.rossi@email.it'),
    Contatto('Anna', 'Rossi', '333-222', 'anna.rossi@email.it'),
    Contatto('Luigi', 'Bianchi', '333-333'),
    Contatto('Sara', 'Ferrari', '333-444'),
    Contatto('Marco', 'Bianchi', '333-555'),
    Contatto('Elena', 'Romano', '333-666'),
]
for c in contatti:
    rubrica.aggiungi(c)

print("Contatti con 'Rossi':")
for c in rubrica.cerca_per_nome('Rossi'):
    print(f"  {c.cognome} {c.nome}: {c.telefono}")

print("\nLettera B:")
for c in rubrica.lettera('B'):
    print(f"  {c.cognome} {c.nome}: {c.telefono}")

stats = rubrica.statistiche()
print(f"\nTotale contatti: {stats['totale']}")
print(f"Distribuzione: {stats['per_lettera']}")

# Output atteso:
# Contatti con 'Rossi':
#   Rossi Anna: 333-222
#   Rossi Mario: 333-111
#
# Lettera B:
#   Bianchi Luigi: 333-333
#   Bianchi Marco: 333-555
#
# Totale contatti: 6
# Distribuzione: {'B': 2, 'F': 1, 'R': 2, 'R': ...}
```

---

### Esercizio 5: Agenda con deque come buffer circolare

**Problema:** Implementa una "cronologia azioni" per un editor di testo:
- Buffer circolare degli ultimi N comandi eseguiti
- Funzione undo: annulla l'ultimo comando
- Funzione redo: ripete l'ultimo comando annullato
- Snapshot dello stato attuale

**Struttura dati:** `deque(maxlen=...)` per la cronologia + stack per il redo

```python
from collections import deque
from typing import Callable, Any
from dataclasses import dataclass

@dataclass
class Comando:
    """Rappresenta un comando reversibile."""
    descrizione: str
    esegui: Callable[[], Any]
    annulla: Callable[[], Any]

class EditorConCronologia:
    """Editor di testo con undo/redo e cronologia limitata."""

    def __init__(self, max_cronologia: int = 20):
        self._testo = ""
        # Buffer circolare: tiene solo gli ultimi max_cronologia comandi
        self._cronologia: deque[Comando] = deque(maxlen=max_cronologia)
        # Stack redo: i comandi annullati (non limitato)
        self._redo_stack: list[Comando] = []

    def esegui(self, comando: Comando) -> None:
        """Esegue un comando e lo aggiunge alla cronologia."""
        comando.esegui()
        self._cronologia.append(comando)
        # Eseguire un nuovo comando svuota il redo stack
        self._redo_stack.clear()
        print(f"  [ESEGUITO] {comando.descrizione}")

    def undo(self) -> bool:
        """Annulla l'ultimo comando. Restituisce False se non c'e' nulla da annullare."""
        if not self._cronologia:
            print("  [UNDO] Nessuna azione da annullare")
            return False
        comando = self._cronologia.pop()
        comando.annulla()
        self._redo_stack.append(comando)
        print(f"  [UNDO] {comando.descrizione}")
        return True

    def redo(self) -> bool:
        """Ripete l'ultimo comando annullato."""
        if not self._redo_stack:
            print("  [REDO] Nessuna azione da ripetere")
            return False
        comando = self._redo_stack.pop()
        comando.esegui()
        self._cronologia.append(comando)
        print(f"  [REDO] {comando.descrizione}")
        return True

    @property
    def testo(self) -> str:
        return self._testo

    def cronologia_str(self) -> list[str]:
        return [c.descrizione for c in self._cronologia]

# Helper per creare comandi di testo
def cmd_inserisci(editor: EditorConCronologia, testo: str, posizione: int) -> Comando:
    """Comando: inserisci testo a una posizione."""
    def esegui():
        editor._testo = editor._testo[:posizione] + testo + editor._testo[posizione:]
    def annulla():
        editor._testo = editor._testo[:posizione] + editor._testo[posizione + len(testo):]
    return Comando(f"Inserisci '{testo}' a pos {posizione}", esegui, annulla)

def cmd_cancella(editor: EditorConCronologia, inizio: int, fine: int) -> Comando:
    """Comando: cancella testo da inizio a fine."""
    testo_cancellato = [editor._testo[inizio:fine]]  # lista per catturare il valore
    def esegui():
        testo_cancellato[0] = editor._testo[inizio:fine]
        editor._testo = editor._testo[:inizio] + editor._testo[fine:]
    def annulla():
        editor._testo = editor._testo[:inizio] + testo_cancellato[0] + editor._testo[inizio:]
    return Comando(f"Cancella [{inizio}:{fine}]", esegui, annulla)

# Test
editor = EditorConCronologia(max_cronologia=5)

editor.esegui(cmd_inserisci(editor, "Ciao ", 0))
editor.esegui(cmd_inserisci(editor, "mondo", 5))
editor.esegui(cmd_inserisci(editor, "!", 10))
print(f"\nTesto: '{editor.testo}'")
# Output: Testo: 'Ciao mondo!'

editor.undo()
print(f"Dopo undo: '{editor.testo}'")
# Output: Dopo undo: 'Ciao mondo'

editor.undo()
print(f"Dopo undo: '{editor.testo}'")
# Output: Dopo undo: 'Ciao '

editor.redo()
print(f"Dopo redo: '{editor.testo}'")
# Output: Dopo redo: 'Ciao mondo'

print(f"\nCronologia: {editor.cronologia_str()}")
```

---

### Esercizio 6: Ricerca binaria con bisect

**Problema:** Implementa un sistema di scheduling per prenotazioni orarie:
- Slot disponibili ogni 30 minuti dalle 9:00 alle 18:00
- Trovare il primo slot libero a partire da un orario richiesto
- Aggiungere e rimuovere prenotazioni mantenendo la lista ordinata
- Trovare slot liberi in un intervallo

**Struttura dati:** `bisect` su lista ordinata di slot occupati

```python
import bisect
from datetime import time, timedelta, datetime

def minuti(h: int, m: int) -> int:
    """Converte ore:minuti in minuti dall'inizio della giornata."""
    return h * 60 + m

def da_minuti(m: int) -> str:
    """Converte minuti in stringa oraria HH:MM."""
    return f"{m // 60:02d}:{m % 60:02d}"

class Agenda:
    """Sistema di prenotazioni con slot da 30 minuti."""

    # Slot disponibili: 9:00, 9:30, 10:00, ... 17:30 (18:00 escluso)
    SLOT = [minuti(9, 0) + i * 30 for i in range(18)]  # 18 slot

    def __init__(self):
        # Lista ORDINATA degli slot occupati (in minuti)
        self._occupati: list[int] = []

    def prenota(self, orario: str) -> bool:
        """
        Prenota uno slot. Formato orario: 'HH:MM'.
        Restituisce True se disponibile e prenotato, False se occupato.
        """
        h, m = map(int, orario.split(':'))
        slot_richiesto = minuti(h, m)

        if slot_richiesto not in self.SLOT:
            raise ValueError(f"Slot {orario} non valido. Usare incrementi di 30 minuti tra 09:00 e 17:30")

        i = bisect.bisect_left(self._occupati, slot_richiesto)
        if i < len(self._occupati) and self._occupati[i] == slot_richiesto:
            return False  # gia' occupato

        bisect.insort(self._occupati, slot_richiesto)
        return True

    def libera(self, orario: str) -> bool:
        """Cancella una prenotazione. Restituisce True se era prenotata."""
        h, m = map(int, orario.split(':'))
        slot = minuti(h, m)
        i = bisect.bisect_left(self._occupati, slot)
        if i < len(self._occupati) and self._occupati[i] == slot:
            self._occupati.pop(i)
            return True
        return False

    def prossimo_libero(self, da_orario: str) -> str | None:
        """Primo slot libero a partire da da_orario (incluso)."""
        h, m = map(int, da_orario.split(':'))
        da = minuti(h, m)

        for slot in self.SLOT:
            if slot < da:
                continue
            i = bisect.bisect_left(self._occupati, slot)
            if i >= len(self._occupati) or self._occupati[i] != slot:
                return da_minuti(slot)  # slot libero trovato
        return None  # nessuno slot libero nel resto della giornata

    def slot_liberi(self, dalle: str, alle: str) -> list[str]:
        """Lista degli slot liberi nell'intervallo [dalle, alle]."""
        h1, m1 = map(int, dalle.split(':'))
        h2, m2 = map(int, alle.split(':'))
        da, a = minuti(h1, m1), minuti(h2, m2)
        return [
            da_minuti(s) for s in self.SLOT
            if da <= s <= a and s not in self._occupati
        ]

# Test
agenda = Agenda()
print("Prenotazioni:")
print(f"  09:00 -> {agenda.prenota('09:00')}")   # True
print(f"  09:00 -> {agenda.prenota('09:00')}")   # False (gia' occupato)
print(f"  10:00 -> {agenda.prenota('10:00')}")   # True
print(f"  10:30 -> {agenda.prenota('10:30')}")   # True

print(f"\nProssimo libero da 09:30: {agenda.prossimo_libero('09:30')}")
# Output: 09:30

print(f"Prossimo libero da 10:00: {agenda.prossimo_libero('10:00')}")
# Output: 11:00 (10:00 e 10:30 sono occupati)

print(f"\nSlot liberi 09:00-11:00: {agenda.slot_liberi('09:00', '11:00')}")
# Output: ['09:30', '11:00']
```

---

### Esercizio 7: Parsing log con namedtuple

**Problema:** Analizza file di log nel formato:
`[TIMESTAMP] [LIVELLO] [COMPONENTE] Messaggio`

Produci:
- Conteggio errori per componente
- Timeline degli eventi critici
- Durata media tra eventi dello stesso tipo

**Struttura dati:** `namedtuple` per le righe di log + `Counter` + `defaultdict`

```python
from typing import NamedTuple
from collections import Counter, defaultdict
from datetime import datetime
import re

class RigaLog(NamedTuple):
    timestamp: datetime
    livello: str
    componente: str
    messaggio: str

def parsa_log(riga: str) -> RigaLog | None:
    """Parsa una riga di log nel formato standard."""
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[(\w+)\] (.+)'
    match = re.match(pattern, riga.strip())
    if not match:
        return None

    ts_str, livello, componente, messaggio = match.groups()
    ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    return RigaLog(timestamp=ts, livello=livello, componente=componente, messaggio=messaggio)

def analizza_log(righe: list[str]) -> dict:
    """Analizza una lista di righe di log e restituisce statistiche."""
    voci = [r for riga in righe if (r := parsa_log(riga)) is not None]

    # Conteggio per livello
    per_livello = Counter(v.livello for v in voci)

    # Errori per componente
    errori_per_comp = Counter(
        v.componente for v in voci
        if v.livello in ('ERROR', 'CRITICAL')
    )

    # Ultimi N eventi CRITICAL
    critici = sorted(
        [v for v in voci if v.livello == 'CRITICAL'],
        key=lambda v: v.timestamp,
        reverse=True
    )

    # Prima e ultima occorrenza per componente
    per_componente: defaultdict[str, list[RigaLog]] = defaultdict(list)
    for v in voci:
        per_componente[v.componente].append(v)

    return {
        'totale': len(voci),
        'per_livello': dict(per_livello),
        'errori_per_componente': errori_per_comp.most_common(),
        'ultimi_critici': critici[:5],
        'componenti_attivi': list(per_componente.keys()),
    }

# Test
log_esempio = """
[2026-07-15 09:00:01] [INFO] [WebServer] Avvio del server
[2026-07-15 09:00:05] [INFO] [Database] Connessione stabilita
[2026-07-15 09:01:23] [WARNING] [WebServer] Alta latenza rilevata
[2026-07-15 09:02:45] [ERROR] [Database] Timeout query: SELECT * FROM users
[2026-07-15 09:03:00] [INFO] [WebServer] 100 richieste elaborate
[2026-07-15 09:05:12] [ERROR] [WebServer] Connessione rifiutata da 192.168.1.50
[2026-07-15 09:07:33] [CRITICAL] [Database] Connessione persa — tentativo di recovery
[2026-07-15 09:08:01] [ERROR] [Cache] Cache miss rate oltre soglia: 89%
[2026-07-15 09:09:15] [INFO] [Database] Recovery completato
""".strip().split('\n')

analisi = analizza_log(log_esempio)

print(f"Totale eventi: {analisi['totale']}")
print(f"Per livello: {analisi['per_livello']}")
print(f"Errori per componente: {analisi['errori_per_componente']}")
print(f"Componenti: {analisi['componenti_attivi']}")

if analisi['ultimi_critici']:
    print("\nUltimi eventi critici:")
    for v in analisi['ultimi_critici']:
        print(f"  [{v.timestamp}] [{v.componente}] {v.messaggio}")

# Output atteso:
# Totale eventi: 9
# Per livello: {'INFO': 4, 'WARNING': 1, 'ERROR': 3, 'CRITICAL': 1}
# Errori per componente: [('Database', 2), ('WebServer', 1), ('Cache', 1)]
# Componenti: ['WebServer', 'Database', 'Cache']
```

---

### Esercizio 8: Macchina a stati con enum

**Problema:** Implementa una macchina a stati per gestire il ciclo di vita di un ordine e-commerce:
- Stati: IN_ATTESA, CONFERMATO, IN_PREPARAZIONE, SPEDITO, CONSEGNATO, ANNULLATO
- Transizioni valide per ogni stato
- Log di ogni transizione con timestamp
- Calcolo del tempo in ogni stato

**Struttura dati:** `enum` + `defaultdict` + `deque` per la cronologia

```python
from enum import Enum, auto
from collections import deque
from typing import NamedTuple
from datetime import datetime

class StatoOrdine(Enum):
    IN_ATTESA     = auto()
    CONFERMATO    = auto()
    IN_PREPARAZIONE = auto()
    SPEDITO       = auto()
    CONSEGNATO    = auto()
    ANNULLATO     = auto()

class Transizione(NamedTuple):
    da: StatoOrdine
    a: StatoOrdine
    timestamp: datetime
    nota: str = ''

# Grafo delle transizioni valide
TRANSIZIONI_VALIDE: dict[StatoOrdine, set[StatoOrdine]] = {
    StatoOrdine.IN_ATTESA:      {StatoOrdine.CONFERMATO, StatoOrdine.ANNULLATO},
    StatoOrdine.CONFERMATO:     {StatoOrdine.IN_PREPARAZIONE, StatoOrdine.ANNULLATO},
    StatoOrdine.IN_PREPARAZIONE:{StatoOrdine.SPEDITO, StatoOrdine.ANNULLATO},
    StatoOrdine.SPEDITO:        {StatoOrdine.CONSEGNATO},
    StatoOrdine.CONSEGNATO:     set(),   # stato terminale
    StatoOrdine.ANNULLATO:      set(),   # stato terminale
}

class Ordine:
    def __init__(self, id_ordine: str):
        self.id = id_ordine
        self._stato = StatoOrdine.IN_ATTESA
        self._cronologia: deque[Transizione] = deque()
        self._entrata_stato = datetime.now()

    @property
    def stato(self) -> StatoOrdine:
        return self._stato

    def transita(self, nuovo_stato: StatoOrdine, nota: str = '') -> bool:
        """Esegue una transizione di stato. Restituisce False se non valida."""
        if nuovo_stato not in TRANSIZIONI_VALIDE.get(self._stato, set()):
            print(f"  [ERRORE] Transizione non valida: {self._stato.name} -> {nuovo_stato.name}")
            return False

        transizione = Transizione(
            da=self._stato,
            a=nuovo_stato,
            timestamp=datetime.now(),
            nota=nota
        )
        self._cronologia.append(transizione)
        self._stato = nuovo_stato
        self._entrata_stato = datetime.now()
        print(f"  [OK] Ordine {self.id}: {transizione.da.name} -> {transizione.a.name}")
        return True

    def cronologia(self) -> list[Transizione]:
        return list(self._cronologia)

    def e_terminato(self) -> bool:
        return self._stato in (StatoOrdine.CONSEGNATO, StatoOrdine.ANNULLATO)

# Test
ordine = Ordine('ORD-2026-001')
print(f"Stato iniziale: {ordine.stato.name}\n")

ordine.transita(StatoOrdine.CONFERMATO, "Pagamento ricevuto")
ordine.transita(StatoOrdine.IN_PREPARAZIONE, "Magazzino Roma")
ordine.transita(StatoOrdine.CONSEGNATO, "Salto illegale!")   # NON valido
ordine.transita(StatoOrdine.SPEDITO, "Corriere SDA")
ordine.transita(StatoOrdine.CONSEGNATO, "Firmato da portiere")

print(f"\nStato finale: {ordine.stato.name}")
print(f"Terminato: {ordine.e_terminato()}")
print(f"\nCronologia ({len(ordine.cronologia())} transizioni):")
for t in ordine.cronologia():
    print(f"  {t.da.name:20} -> {t.a.name:20}  '{t.nota}'")

# Output atteso:
# Stato iniziale: IN_ATTESA
#
#   [OK] Ordine ORD-2026-001: IN_ATTESA -> CONFERMATO
#   [OK] Ordine ORD-2026-001: CONFERMATO -> IN_PREPARAZIONE
#   [ERRORE] Transizione non valida: IN_PREPARAZIONE -> CONSEGNATO
#   [OK] Ordine ORD-2026-001: IN_PREPARAZIONE -> SPEDITO
#   [OK] Ordine ORD-2026-001: SPEDITO -> CONSEGNATO
#
# Stato finale: CONSEGNATO
# Terminato: True
```

---

### Esercizio 9: UserDict con validazione

**Problema:** Implementa un `ConfigDict` che estende `UserDict` per:
- Validare i tipi e i valori al momento dell'inserimento
- Supportare valori di default per chiavi obbligatorie
- Notificare i listener quando un valore cambia
- Serializzare/deserializzare in formato JSON

**Struttura dati:** `UserDict` + `dict` per lo schema

```python
from collections import UserDict
from typing import Any, Callable
import json

class ConfigDict(UserDict):
    """Dizionario di configurazione con validazione e notifiche."""

    def __init__(self, schema: dict[str, dict], **kwargs):
        """
        schema: {
            'chiave': {
                'tipo': type,
                'min': valore_minimo (opzionale),
                'max': valore_massimo (opzionale),
                'default': valore_default (opzionale),
                'obbligatorio': bool
            }
        }
        """
        self._schema = schema
        self._listeners: list[Callable[[str, Any, Any], None]] = []
        super().__init__()

        # Applica i valori di default per le chiavi obbligatorie
        for chiave, regole in schema.items():
            if 'default' in regole:
                self.data[chiave] = regole['default']

        # Imposta i valori iniziali (con validazione)
        for k, v in kwargs.items():
            self[k] = v

    def __setitem__(self, chiave: str, valore: Any) -> None:
        if chiave in self._schema:
            regole = self._schema[chiave]
            tipo = regole.get('tipo')

            # Validazione tipo
            if tipo and not isinstance(valore, tipo):
                raise TypeError(
                    f"'{chiave}' deve essere {tipo.__name__}, ricevuto {type(valore).__name__}"
                )

            # Validazione range
            if 'min' in regole and valore < regole['min']:
                raise ValueError(f"'{chiave}' deve essere >= {regole['min']}")
            if 'max' in regole and valore > regole['max']:
                raise ValueError(f"'{chiave}' deve essere <= {regole['max']}")

        vecchio_valore = self.data.get(chiave)
        super().__setitem__(chiave, valore)

        # Notifica listeners solo se il valore e' cambiato
        if vecchio_valore != valore:
            for listener in self._listeners:
                listener(chiave, vecchio_valore, valore)

    def aggiungi_listener(self, fn: Callable[[str, Any, Any], None]) -> None:
        """Registra una funzione da chiamare quando un valore cambia."""
        self._listeners.append(fn)

    def valida_completo(self) -> list[str]:
        """Verifica che tutte le chiavi obbligatorie siano presenti."""
        errori = []
        for chiave, regole in self._schema.items():
            if regole.get('obbligatorio') and chiave not in self.data:
                errori.append(f"Chiave obbligatoria mancante: '{chiave}'")
        return errori

    def to_json(self) -> str:
        return json.dumps(dict(self.data), indent=2, ensure_ascii=False)

# Test
SCHEMA = {
    'host':       {'tipo': str, 'obbligatorio': True},
    'porta':      {'tipo': int, 'min': 1, 'max': 65535, 'default': 5432},
    'timeout':    {'tipo': float, 'min': 0.1, 'max': 30.0, 'default': 5.0},
    'debug':      {'tipo': bool, 'default': False},
    'max_conn':   {'tipo': int, 'min': 1, 'max': 100, 'default': 10},
}

log_cambiamenti: list[str] = []

def on_change(chiave: str, vecchio: Any, nuovo: Any) -> None:
    log_cambiamenti.append(f"{chiave}: {vecchio!r} -> {nuovo!r}")

config = ConfigDict(SCHEMA, host='localhost')
config.aggiungi_listener(on_change)

config['porta'] = 3306
config['debug'] = True
config['max_conn'] = 25

print("Configurazione corrente:")
print(config.to_json())

print("\nCambiamenti registrati:")
for c in log_cambiamenti:
    print(f"  {c}")

# Test errori
try:
    config['porta'] = 99999  # fuori range
except ValueError as e:
    print(f"\nErrore validazione: {e}")

try:
    config['porta'] = '3307'  # tipo sbagliato
except TypeError as e:
    print(f"Errore tipo: {e}")

# Output atteso (estratto):
# Configurazione corrente:
# {
#   "porta": 3306,
#   "timeout": 5.0,
#   "debug": true,
#   "max_conn": 25,
#   "host": "localhost"
# }
```

---

### Esercizio 10: Pipeline con ChainMap

**Problema:** Implementa un sistema di configurazione per una pipeline di elaborazione dati con:
- Configurazione base (costanti dell'azienda)
- Configurazione per ambiente (dev/staging/produzione)
- Override per singolo job
- Override da riga di comando (argomenti CLI)

Ogni livello puo sovrascrivere solo alcune chiavi. La pipeline deve sempre vedere il valore con la priorita piu alta disponibile.

**Struttura dati:** `ChainMap` + gestione di livelli

```python
from collections import ChainMap
import json

# Livello 0: default aziendali (non modificabili)
CONFIG_AZIENDA = {
    'timeout_http': 30,
    'retry_max': 3,
    'log_level': 'INFO',
    'encoding': 'utf-8',
    'batch_size': 100,
    'output_format': 'json',
    'autore': 'DataTeam',
}

# Livello 1: configurazione per ambiente
CONFIG_AMBIENTI = {
    'dev': {
        'log_level': 'DEBUG',
        'batch_size': 10,
        'dry_run': True,
    },
    'staging': {
        'log_level': 'WARNING',
        'batch_size': 50,
        'dry_run': True,
    },
    'prod': {
        'log_level': 'ERROR',
        'batch_size': 500,
        'dry_run': False,
    },
}

class ConfigPipeline:
    """Sistema di configurazione a livelli per pipeline di dati."""

    def __init__(self, ambiente: str):
        if ambiente not in CONFIG_AMBIENTI:
            raise ValueError(f"Ambiente '{ambiente}' non riconosciuto. Usa: {list(CONFIG_AMBIENTI)}")

        self._ambiente = ambiente
        self._config_job: dict = {}
        self._config_cli: dict = {}

        # ChainMap: CLI > Job > Ambiente > Azienda
        self._chain = ChainMap(
            self._config_cli,
            self._config_job,
            CONFIG_AMBIENTI[ambiente],
            CONFIG_AZIENDA
        )

    def imposta_job(self, **kwargs) -> None:
        """Override a livello di job (sovrascrive ambiente, ma non CLI)."""
        self._config_job.update(kwargs)

    def imposta_cli(self, **kwargs) -> None:
        """Override da riga di comando (massima priorita)."""
        self._config_cli.update(kwargs)

    def get(self, chiave: str, default=None):
        return self._chain.get(chiave, default)

    def __getitem__(self, chiave: str):
        return self._chain[chiave]

    def ispezione(self) -> None:
        """Mostra la risoluzione di ogni chiave per livello."""
        tutte_le_chiavi = set()
        for m in self._chain.maps:
            tutte_le_chiavi.update(m.keys())

        print(f"Configurazione pipeline ({self._ambiente}):")
        print(f"  {'CHIAVE':20} {'VALORE':20} {'DA'}")
        print(f"  {'-'*20} {'-'*20} {'-'*15}")

        for chiave in sorted(tutte_le_chiavi):
            valore = self._chain[chiave]
            # Trova da quale livello viene
            nomi_livelli = ['CLI', 'JOB', self._ambiente.upper(), 'AZIENDA']
            sorgente = 'AZIENDA'
            for livello, nome in zip(self._chain.maps, nomi_livelli):
                if chiave in livello:
                    sorgente = nome
                    break
            print(f"  {chiave:20} {str(valore):20} {sorgente}")

# Test
pipeline = ConfigPipeline(ambiente='dev')
pipeline.ispezione()

print("\n--- Dopo override job ---")
pipeline.imposta_job(batch_size=25, output_format='parquet')
pipeline.ispezione()

print("\n--- Dopo override CLI ---")
pipeline.imposta_cli(log_level='DEBUG', batch_size=5)
pipeline.ispezione()

print(f"\nbatch_size effettivo: {pipeline['batch_size']}")
print(f"log_level effettivo: {pipeline['log_level']}")

# Output atteso (estratto):
# Configurazione pipeline (dev):
#   CHIAVE               VALORE               DA
#   -------------------- -------------------- ---------------
#   autore               DataTeam             AZIENDA
#   batch_size           10                   dev
#   dry_run              True                 dev
#   encoding             utf-8                AZIENDA
#   log_level            DEBUG                dev
#   ...
```

---

## Riepilogo Parte C — Blocco 4

I 10 esercizi coprono le strutture principali in contesti reali:

| # | Esercizio | Strutture usate |
|---|-----------|-----------------|
| 1 | Leaderboard | `heapq` + `dict` |
| 2 | Analizzatore testo | `Counter` |
| 3 | Cache LRU + TTL | `OrderedDict` |
| 4 | Rubrica | `defaultdict` + `NamedTuple` |
| 5 | Editor undo/redo | `deque` come buffer circolare |
| 6 | Agenda prenotazioni | `bisect` |
| 7 | Parser log | `NamedTuple` + `Counter` + `defaultdict` |
| 8 | Macchina stati ordine | `enum` + `NamedTuple` |
| 9 | ConfigDict validato | `UserDict` |
| 10 | Pipeline a livelli | `ChainMap` |

Nel Blocco 5 (Parte D) troverai le tecniche da esperto: LinkedList, BinaryTree, internals di dict/set, `weakref`, `TypedDict`, checklist e tabella di riferimento rapido.


---

## Parte D — Livello Esperto e Riepilogo Finale {#parte-d}

---

## Implementazione da zero: LinkedList

Una linked list (lista concatenata) e una struttura dati in cui ogni elemento (nodo) contiene un valore e un puntatore al nodo successivo. Non esiste nella standard library Python (la `list` e un array dinamico), ma comprenderne l'implementazione e fondamentale per capire le strutture dati in generale.

### Complessita della LinkedList

| Operazione | LinkedList | list Python |
|------------|-----------|-------------|
| Accesso per indice | O(n) | O(1) |
| Inserimento in testa | O(1) | O(n) |
| Inserimento in coda | O(1) se tail noto | O(1) amortizzato |
| Inserimento in mezzo | O(1) dopo ricerca + O(n) ricerca | O(n) |
| Rimozione in testa | O(1) | O(n) |
| Ricerca per valore | O(n) | O(n) |
| Memoria per elemento | 2 puntatori aggiuntivi per nodo | 1 puntatore per slot |

### Implementazione: SinglyLinkedList

```python
from typing import Optional, Iterator, TypeVar

T = TypeVar('T')

class Nodo:
    """Nodo di una lista semplicemente concatenata."""
    __slots__ = ('valore', 'successivo')

    def __init__(self, valore):
        self.valore = valore
        self.successivo: Optional['Nodo'] = None

class ListaConcatenata:
    """Lista semplicemente concatenata con testa e coda tracciate."""

    def __init__(self):
        self._testa: Optional[Nodo] = None
        self._coda: Optional[Nodo] = None
        self._dimensione: int = 0

    def aggiungi_in_testa(self, valore) -> None:
        """O(1) — inserimento in testa."""
        nuovo = Nodo(valore)
        nuovo.successivo = self._testa
        self._testa = nuovo
        if self._coda is None:
            self._coda = nuovo
        self._dimensione += 1

    def aggiungi_in_coda(self, valore) -> None:
        """O(1) — inserimento in coda (coda tracciata)."""
        nuovo = Nodo(valore)
        if self._coda is None:
            self._testa = self._coda = nuovo
        else:
            self._coda.successivo = nuovo
            self._coda = nuovo
        self._dimensione += 1

    def rimuovi_in_testa(self):
        """O(1) — rimozione dalla testa."""
        if self._testa is None:
            raise IndexError("Lista vuota")
        valore = self._testa.valore
        self._testa = self._testa.successivo
        if self._testa is None:
            self._coda = None
        self._dimensione -= 1
        return valore

    def cerca(self, valore) -> bool:
        """O(n) — ricerca lineare."""
        nodo = self._testa
        while nodo is not None:
            if nodo.valore == valore:
                return True
            nodo = nodo.successivo
        return False

    def inverti(self) -> None:
        """O(n) — inversione in-place senza copia."""
        precedente = None
        corrente = self._testa
        self._coda = self._testa
        while corrente is not None:
            successivo = corrente.successivo
            corrente.successivo = precedente
            precedente = corrente
            corrente = successivo
        self._testa = precedente

    def __len__(self) -> int:
        return self._dimensione

    def __iter__(self) -> Iterator:
        nodo = self._testa
        while nodo is not None:
            yield nodo.valore
            nodo = nodo.successivo

    def __repr__(self) -> str:
        elementi = list(self)
        return ' -> '.join(str(e) for e in elementi) + ' -> None'

# Test
ll = ListaConcatenata()
for v in [1, 2, 3, 4, 5]:
    ll.aggiungi_in_coda(v)

print(ll)
# Output atteso: 1 -> 2 -> 3 -> 4 -> 5 -> None

ll.aggiungi_in_testa(0)
print(ll)
# Output atteso: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> None

print(ll.rimuovi_in_testa())   # 0
print(ll.cerca(3))             # True
print(ll.cerca(99))            # False

ll.inverti()
print(ll)
# Output atteso: 5 -> 4 -> 3 -> 2 -> 1 -> None
```

---

## Implementazione da zero: BinarySearchTree

```python
from typing import Optional, Iterator
from collections import deque

class NodoBST:
    """Nodo di un albero binario di ricerca."""
    __slots__ = ('valore', 'sinistro', 'destro')

    def __init__(self, valore):
        self.valore = valore
        self.sinistro: Optional['NodoBST'] = None
        self.destro: Optional['NodoBST'] = None

class AlberoBST:
    """Albero Binario di Ricerca con attraversamenti e operazioni base."""

    def __init__(self):
        self._radice: Optional[NodoBST] = None
        self._dimensione = 0

    def inserisci(self, valore) -> None:
        """O(log n) media, O(n) peggiore (albero sbilanciato)."""
        self._radice = self._inserisci_ricorsivo(self._radice, valore)

    def _inserisci_ricorsivo(self, nodo: Optional[NodoBST], valore) -> NodoBST:
        if nodo is None:
            self._dimensione += 1
            return NodoBST(valore)
        if valore < nodo.valore:
            nodo.sinistro = self._inserisci_ricorsivo(nodo.sinistro, valore)
        elif valore > nodo.valore:
            nodo.destro = self._inserisci_ricorsivo(nodo.destro, valore)
        # duplicati ignorati
        return nodo

    def cerca(self, valore) -> bool:
        """O(log n) media."""
        nodo = self._radice
        while nodo is not None:
            if valore == nodo.valore:
                return True
            nodo = nodo.sinistro if valore < nodo.valore else nodo.destro
        return False

    def minimo(self):
        """O(log n) — il nodo piu a sinistra."""
        if self._radice is None:
            return None
        nodo = self._radice
        while nodo.sinistro is not None:
            nodo = nodo.sinistro
        return nodo.valore

    def massimo(self):
        """O(log n) — il nodo piu a destra."""
        if self._radice is None:
            return None
        nodo = self._radice
        while nodo.destro is not None:
            nodo = nodo.destro
        return nodo.valore

    def inorder(self) -> list:
        """O(n) — restituisce gli elementi in ordine crescente."""
        risultato = []
        self._inorder_ricorsivo(self._radice, risultato)
        return risultato

    def _inorder_ricorsivo(self, nodo: Optional[NodoBST], acc: list) -> None:
        if nodo is not None:
            self._inorder_ricorsivo(nodo.sinistro, acc)
            acc.append(nodo.valore)
            self._inorder_ricorsivo(nodo.destro, acc)

    def bfs(self) -> list:
        """O(n) — attraversamento in ampiezza (livello per livello)."""
        if self._radice is None:
            return []
        risultato = []
        coda = deque([self._radice])
        while coda:
            nodo = coda.popleft()
            risultato.append(nodo.valore)
            if nodo.sinistro:
                coda.append(nodo.sinistro)
            if nodo.destro:
                coda.append(nodo.destro)
        return risultato

    def altezza(self) -> int:
        """O(n) — altezza dell'albero."""
        def h(nodo: Optional[NodoBST]) -> int:
            if nodo is None:
                return -1
            return 1 + max(h(nodo.sinistro), h(nodo.destro))
        return h(self._radice)

    def __len__(self) -> int:
        return self._dimensione

# Test
bst = AlberoBST()
for v in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
    bst.inserisci(v)

print("In-order:", bst.inorder())    # [1, 3, 4, 6, 7, 8, 10, 13, 14]
print("BFS:", bst.bfs())             # [8, 3, 10, 1, 6, 14, 4, 7, 13]
print("Min:", bst.minimo())          # 1
print("Max:", bst.massimo())         # 14
print("Altezza:", bst.altezza())     # 3
print("Cerca 6:", bst.cerca(6))      # True
print("Cerca 99:", bst.cerca(99))    # False
print("Dimensione:", len(bst))       # 9
```

---

## Internals di dict e set: hash table, collision, resize

Capire come `dict` e `set` funzionano internamente ti aiuta a usarli correttamente e a evitare errori sottili.

### Come funziona una hash table

```python
# Quando scrivi d['chiave'] = valore, Python:
# 1. Calcola hash('chiave') → un intero (es. 3713082716806266542)
# 2. Riduce l'hash all'indice del bucket: indice = hash % dimensione_tabella
# 3. Inserisce (chiave, valore) nel bucket

# Puoi vedere il valore hash di qualsiasi oggetto hashable:
print(hash('ciao'))        # es. 7023887836818924390
print(hash(42))            # 42 (gli interi sono il loro stesso hash)
print(hash(3.14))          # 322818021289917443

# Oggetti uguali devono avere lo stesso hash
print(hash(1) == hash(1.0))  # True (1 == 1.0 in Python)
```

### Collisioni: due chiavi, stesso bucket

```python
# Quando due chiavi hanno lo stesso indice di bucket (collisione),
# Python usa open addressing con sondaggio quadratico per trovare il prossimo slot libero.

# Esempio di collisione artificiale:
class ChiaveCollidente:
    def __init__(self, valore):
        self.valore = valore

    def __hash__(self):
        return 42   # TUTTE le istanze hanno lo stesso hash!

    def __eq__(self, other):
        return isinstance(other, ChiaveCollidente) and self.valore == other.valore

# Con tutte le stesse hash, il dict degenera a O(n) per ricerca
d = {}
for i in range(5):
    d[ChiaveCollidente(i)] = i

# In produzione: MAI fare hash costante! E' un bug di performance.
# Il comportamento corretto e: oggetti uguali hanno lo stesso hash,
# ma oggetti diversi devono avere hash DIVERSI il piu possibile.
```

### Resize: quando il dict cresce

```python
import sys

# Il dict si ridimensiona quando il load factor supera circa 2/3
d = {}
dimensioni = []
for i in range(200):
    d[i] = i
    s = sys.getsizeof(d)
    if not dimensioni or dimensioni[-1] != s:
        dimensioni.append((len(d), s))

print("Ridimensionamenti del dict:")
for n_elementi, dimensione in dimensioni:
    print(f"  {n_elementi:4d} elementi -> {dimensione:6d} byte")

# Output (semplificato):
#    1 elementi ->    240 byte
#    6 elementi ->    368 byte
#   11 elementi ->    648 byte
#   22 elementi ->   1176 byte
#   ...
# Ogni resize raddoppia (circa) la capacita interna
```

### Contratto hashable: __hash__ e __eq__

```python
from dataclasses import dataclass

# REGOLA FONDAMENTALE:
# Se a == b, allora hash(a) == hash(b)
# L'inverso NON vale: hash(a) == hash(b) non implica a == b

@dataclass(frozen=True)   # frozen=True genera __hash__ automaticamente
class Coordinate:
    lat: float
    lon: float

# Ora Coordinate e hashable e puo essere usata come chiave dict o elemento set
roma = Coordinate(41.9028, 12.4964)
milano = Coordinate(45.4654, 9.1859)

distanze = {roma: 'capitale', milano: 'metropoli'}
print(distanze[Coordinate(41.9028, 12.4964)])   # 'capitale'
```

---

## weakref.WeakValueDictionary

Un `WeakValueDictionary` mantiene riferimenti DEBOLI ai suoi valori. Quando l'unico riferimento rimasto a un oggetto e quello del dizionario, l'oggetto viene raccolt dal garbage collector e la chiave viene rimossa automaticamente dal dizionario.

```python
import weakref
import gc

class Risorsa:
    def __init__(self, nome: str):
        self.nome = nome

    def __repr__(self) -> str:
        return f"Risorsa('{self.nome}')"

# WeakValueDictionary: le chiavi spariscono quando i valori non hanno piu riferimenti forti
cache = weakref.WeakValueDictionary()

r1 = Risorsa('database')
r2 = Risorsa('filesystem')

cache['db'] = r1
cache['fs'] = r2

print(f"Cache: {dict(cache)}")
# Output: Cache: {'db': Risorsa('database'), 'fs': Risorsa('filesystem')}

# Rimuovi il riferimento forte a r1
del r1
gc.collect()   # forza la raccolta (di solito avviene automaticamente)

print(f"Dopo del r1: {dict(cache)}")
# Output: Dopo del r1: {'fs': Risorsa('filesystem')}
# 'db' e' sparito automaticamente!

# QUANDO USARE WeakValueDictionary:
# - Cache dove gli oggetti possono essere ricreati se necessario
# - Registry di oggetti attivi senza impedire la loro garbage collection
# - Implementare il pattern Observer senza memory leak
```

---

## queue.Queue thread-safe

Il modulo `queue` fornisce code thread-safe. Usa lock interni: piu thread possono leggere e scrivere simultaneamente senza corrompere i dati.

```python
from queue import Queue, Empty
import threading
import time

def produttore(coda: Queue, n_elementi: int, nome: str) -> None:
    """Thread produttore: genera elementi e li mette in coda."""
    for i in range(n_elementi):
        elemento = f"{nome}-item-{i}"
        coda.put(elemento)   # blocca se la coda e' piena (maxsize)
        print(f"[{nome}] Prodotto: {elemento}")
        time.sleep(0.05)
    coda.put(None)   # segnale di terminazione

def consumatore(coda: Queue, nome: str) -> None:
    """Thread consumatore: elabora elementi dalla coda."""
    while True:
        try:
            elemento = coda.get(timeout=2.0)   # timeout per evitare blocchi infiniti
            if elemento is None:
                break
            print(f"  [{nome}] Consumato: {elemento}")
            coda.task_done()   # segnala che l'elemento e' stato elaborato
        except Empty:
            print(f"  [{nome}] Timeout — nessun elemento disponibile")
            break

# Esempio: produttore singolo, 2 consumatori
coda = Queue(maxsize=5)

t_prod = threading.Thread(target=produttore, args=(coda, 6, 'Prod'))
t_cons1 = threading.Thread(target=consumatore, args=(coda, 'Cons-A'))
t_cons2 = threading.Thread(target=consumatore, args=(coda, 'Cons-B'))

t_prod.start()
t_cons1.start()
t_cons2.start()

t_prod.join()
t_cons1.join()
t_cons2.join()

print("Pipeline completata.")

# NOTA: queue.Queue e' per thread. Per processi, usa multiprocessing.Queue.
# Per coroutine async, usa asyncio.Queue.
```

---

## TypedDict e NamedTuple tipizzata

### TypedDict — dizionario con tipo strutturato

`TypedDict` non crea un nuovo tipo a runtime: e ancora un `dict` normale. La differenza e solo per i type checker (mypy, Pyright): permettono di specificare quale struttura deve avere un dizionario.

```python
from typing import TypedDict, Required, NotRequired

class ConfigDatabase(TypedDict):
    host: str
    porta: int
    database: str

class ConfigDatabaseEstesa(TypedDict, total=False):
    """total=False rende tutti i campi opzionali."""
    host: str
    porta: int
    database: str
    utente: str
    password: str
    ssl: bool

# TypedDict con campi obbligatori e opzionali misti
class ConfigConnessione(TypedDict):
    host: Required[str]      # obbligatorio
    porta: Required[int]     # obbligatorio
    ssl: NotRequired[bool]   # opzionale (Python 3.11+)

# A runtime e' un dict normale
config: ConfigDatabase = {
    'host': 'localhost',
    'porta': 5432,
    'database': 'mio_db'
}

# Mypy ti avvertirebbe qui se il tipo fosse sbagliato
config['porta'] = 'non-un-intero'  # a runtime va, mypy segnala errore

# Differenza con NamedTuple:
# TypedDict = dict normale (mutabile, non hashable, accesso per chiave stringa)
# NamedTuple = tupla (immutabile, hashable, accesso per nome come attributo)

print(type(config))   # <class 'dict'>
```

### NamedTuple tipizzata con validazione

```python
from typing import NamedTuple

class Vettore3D(NamedTuple):
    x: float
    y: float
    z: float = 0.0   # componente z opzionale

    def magnitudine(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalizza(self) -> 'Vettore3D':
        m = self.magnitudine()
        if m == 0:
            raise ValueError("Impossibile normalizzare un vettore zero")
        return Vettore3D(self.x / m, self.y / m, self.z / m)

    def prodotto_scalare(self, altro: 'Vettore3D') -> float:
        return self.x * altro.x + self.y * altro.y + self.z * altro.z

v1 = Vettore3D(3.0, 4.0)
v2 = Vettore3D(1.0, 0.0, 0.0)

print(f"v1 = {v1}")
print(f"Magnitudine: {v1.magnitudine():.2f}")   # 5.00
print(f"v1 normalizzato: {v1.normalizza()}")
print(f"Prodotto scalare v1 . v2: {v1.prodotto_scalare(v2):.2f}")

# Output atteso:
# v1 = Vettore3D(x=3.0, y=4.0, z=0.0)
# Magnitudine: 5.00
# v1 normalizzato: Vettore3D(x=0.6, y=0.8, z=0.0)
# Prodotto scalare v1 . v2: 3.00
```

---

## Checklist finale: 30+ punti per dominare le strutture dati avanzate

### Sezione 1 — Fondamentali (punti 1-10)

- [ ] 1. Conosco la differenza tra O(1), O(log n), O(n) e so applicarla alla scelta della struttura
- [ ] 2. So quando una `list` e sufficiente e quando devo usare un'alternativa
- [ ] 3. Importo `Counter`, `defaultdict`, `OrderedDict`, `deque`, `ChainMap`, `namedtuple` da `collections`
- [ ] 4. Uso `Counter` per contare frequenze senza scrivere loop espliciti
- [ ] 5. Uso `defaultdict` per evitare i pattern `if chiave not in d: d[chiave] = []`
- [ ] 6. Uso `deque` quando inserisco o rimuovo frequentemente da entrambe le estremita
- [ ] 7. Uso `namedtuple` o `NamedTuple` per record di dati immutabili leggeri
- [ ] 8. Conosco `_asdict()`, `_replace()`, `_make()`, `_fields` di namedtuple
- [ ] 9. So perche `OrderedDict` esiste ancora dopo Python 3.7 (move_to_end, confronto order-sensitive)
- [ ] 10. Uso `ChainMap` per configurazioni a livelli invece di mergiare dizionari

### Sezione 2 — Efficienza algoritmica (punti 11-20)

- [ ] 11. Uso `heapq.heappush`/`heappop` per code di priorita (non ordino tutta la lista ogni volta)
- [ ] 12. Conosco il trucco della negazione per max-heap con `heapq`
- [ ] 13. Uso `heapq.nlargest(k, data)` invece di `sorted(data)[-k:]` per k piccolo
- [ ] 14. Uso `bisect.bisect_left`/`bisect_right` per ricerche su liste ordinate
- [ ] 15. Uso `bisect.insort` per inserire mantenendo l'ordine
- [ ] 16. So quando usare `array.array` invece di `list` per risparmio di memoria
- [ ] 17. Conosco i codici di tipo di `array` ('i', 'd', 'f', 'b')
- [ ] 18. Uso `memoryview` per lavorare su porzioni di buffer senza copiarli
- [ ] 19. Uso `enum` per insiemi finiti di valori nominati invece di costanti stringa/int
- [ ] 20. Conosco `IntEnum`, `Flag`, `auto()` e i metodi `.name`, `.value`

### Sezione 3 — Livello avanzato (punti 21-30)

- [ ] 21. So implementare una LinkedList con inserimento O(1) in testa e coda
- [ ] 22. So implementare un BST con inserimento, ricerca, e attraversamenti in/pre/post-order
- [ ] 23. Capisco che `dict` usa una hash table e so scrivere `__hash__` e `__eq__` correttamente
- [ ] 24. So che oggetti uguali devono avere lo stesso hash (contratto hashable)
- [ ] 25. Conosco `weakref.WeakValueDictionary` e quando evita memory leak
- [ ] 26. Uso `queue.Queue` per comunicazione thread-safe tra produttori e consumatori
- [ ] 27. Uso `TypedDict` per annotare dizionari strutturati senza creare nuovi tipi runtime
- [ ] 28. Estendo `UserDict` o `UserList` invece di `dict`/`list` direttamente quando override metodi
- [ ] 29. Conosco `sortedcontainers.SortedList` per inserimenti O(log n) su liste ordinate
- [ ] 30. Scelgo la struttura dati prima di scrivere il codice, non dopo

### Punti bonus

- [ ] 31. Profilo la memoria con `sys.getsizeof()` e `tracemalloc` prima di ottimizzare
- [ ] 32. Conosco `types.MappingProxyType` per esporre dizionari in sola lettura
- [ ] 33. Uso `@dataclass(frozen=True, slots=True)` per record immutabili con metodi
- [ ] 34. So che `heapq.merge()` fa merge di iterabili ordinati senza caricare tutto in memoria
- [ ] 35. Conosco il pattern `nodo -> sentinel -> nodo` per semplificare operazioni su linked list

---

## Tabella di riferimento: Problema -> Struttura Giusta

| Problema | Struttura consigliata | Alternativa | Note |
|----------|-----------------------|-------------|------|
| Contare frequenze di elementi | `Counter` | `defaultdict(int)` | `Counter` ha `most_common`, operazioni aritmetiche |
| Raggruppare per categoria | `defaultdict(list)` | `dict` con setdefault | Piu leggibile, nessun controllo if |
| Record immutabile leggero | `NamedTuple` | `@dataclass(frozen=True)` | NamedTuple e una tupla, indicizzabile |
| Cache con eviction LRU | `OrderedDict` | `functools.lru_cache` | OrderedDict per cache manuali con invalidazione |
| Configurazioni a livelli | `ChainMap` | `{**d1, **d2, **d3}` | ChainMap aggiorna dinamicamente, merge no |
| Coda bidirezionale efficiente | `deque` | `list` | deque ha O(1) su entrambi i lati |
| Buffer circolare (sliding window) | `deque(maxlen=N)` | lista con indice manuale | Automatico: i piu vecchi vengono rimossi |
| Coda di priorita (min-heap) | `heapq` | `queue.PriorityQueue` | heapq non thread-safe, PriorityQueue si |
| Trovare top-k elementi | `heapq.nlargest/nsmallest` | `sorted()[-k:]` | heapq e migliore per k piccolo |
| Ricerca su lista ordinata | `bisect.bisect_left` | ricerca lineare | O(log n) vs O(n) |
| Lista sempre ordinata, pochi inserimenti | `bisect.insort` + lista | `SortedList` di sortedcontainers | insort O(log n) ricerca, O(n) inserimento |
| Lista sempre ordinata, molti inserimenti | `SortedList` (sortedcontainers) | AVL tree custom | O(log n) per tutto |
| Array di milioni di numeri omogenei | `array.array` | `numpy.ndarray` | array per storage, numpy per calcoli |
| Parsing di buffer binari grandi | `memoryview` + `struct` | `bytes` slicing | memoryview = zero-copy |
| Insiemi finiti di stati/valori | `enum.Enum` | costanti stringa/int | Protezione da valori invalidi |
| Stati combinabili (bitmask) | `enum.Flag` | interi con bitwise OR | Leggibile e type-safe |
| Override metodi dict/list | `UserDict` / `UserList` | sottoclasse diretta | User* garantisce che tutti i metodi usino override |
| Dizionario in sola lettura | `types.MappingProxyType` | copia con `dict()` | Vista live, nessuna copia |
| Cache senza impedire GC | `weakref.WeakValueDictionary` | `dict` normale | Gli oggetti senza altri riferimenti vengono rimossi |
| Coda thread-safe | `queue.Queue` | `deque` con lock manuale | Queue ha lock interni e `task_done()` |
| Comunicazione tra coroutine | `asyncio.Queue` | `queue.Queue` (non-async) | asyncio.Queue non e' thread-safe |
| Dati con history (undo) | strutture persistenti (`pyrsistent`) | copia manuale | Structural sharing: O(log n) invece di O(n) |

---

## Glossario

**array.array**: Contenitore omogeneo tipizzato per valori numerici C. Occupa molto meno memoria di una lista Python per lo stesso numero di elementi numerici.

**Big-O**: Notazione per descrivere la complessita computazionale di un algoritmo in funzione della dimensione dell'input n. Misura il comportamento asintotico (al crescere di n).

**bisect**: Modulo della standard library che implementa la ricerca binaria su liste ordinate. `bisect_left`/`bisect_right` trovano il punto di inserimento in O(log n); `insort` inserisce mantenendo l'ordine.

**Buffer circolare**: Struttura a dimensione fissa in cui i nuovi elementi sovrascrivono i piu vecchi. In Python: `deque(maxlen=N)`.

**ChainMap**: Classe del modulo `collections` che raggruppa piu dizionari in una vista unica. La ricerca avviene in sequenza; le scritture vanno solo nel primo mapping.

**Collision (hash)**: Situazione in cui due chiavi diverse producono lo stesso indice di bucket in una hash table. Python risolve le collisioni con open addressing.

**Counter**: Sottoclasse di `dict` per contare elementi hashable. Supporta operazioni aritmetiche (somma, differenza, intersezione, unione) tra counter e il metodo `most_common`.

**defaultdict**: Sottoclasse di `dict` che crea automaticamente un valore di default quando si accede a una chiave inesistente, usando una `default_factory` fornita alla creazione.

**deque**: (double-ended queue) Coda a doppia estremita del modulo `collections`. Garantisce O(1) per inserimento e rimozione da entrambi i lati, a differenza della lista (O(n) in testa).

**enum**: Modulo che permette di definire insiemi chiusi di valori nominati. `Enum` per valori generici, `IntEnum` per compatibilita con int, `Flag` per bitmask combinabili.

**GC (Garbage Collector)**: Meccanismo Python per liberare la memoria degli oggetti non piu referenziati. In CPython e basato su reference counting con un ciclo di rilevamento per riferimenti circolari.

**Hash table**: Struttura dati che implementa un mapping chiave-valore con accesso medio O(1). `dict` e `set` in Python sono implementati come hash table.

**heapq**: Modulo della standard library che implementa un min-heap su una lista Python. `heappush` e `heappop` mantengono la proprieta dell'heap in O(log n). `heapify` costruisce un heap in O(n).

**LinkedList**: Lista concatenata. Ogni nodo contiene un valore e un puntatore al nodo successivo. Inserimento O(1) in testa, accesso per indice O(n).

**memoryview**: Oggetto Python che fornisce una vista zero-copy su un buffer di byte (bytes, bytearray, array). Lo slicing su un memoryview non copia i dati.

**Min-heap**: Albero binario completo dove ogni nodo padre e minore o uguale ai figli. L'elemento minimo e sempre alla radice (indice 0 nella rappresentazione lista).

**namedtuple**: Sottoclasse di tuple con campi accessibili per nome. Immutabile, leggera, non ha `__dict__`. La versione moderna `typing.NamedTuple` aggiunge i type hints.

**OrderedDict**: Dizionario che mantiene l'ordine di inserimento e offre `move_to_end()` O(1) e confronto order-sensitive. Utile per cache LRU manuali.

**SortedList**: Da `sortedcontainers`. Lista sempre ordinata con inserimento, rimozione e ricerca O(log n) grazie a una struttura interna simile a un B-tree.

**TypedDict**: Forma di annotazione per dizionari con struttura nota. Non crea un nuovo tipo a runtime (e ancora un `dict`), ma abilita il controllo di tipo statico.

**UserDict / UserList / UserString**: Classi wrapper del modulo `collections` che delegano a un attributo `.data` interno. Sicure per l'override di `__setitem__`, `__delitem__` a differenza della sottoclasse diretta.

**weakref**: Modulo per riferimenti deboli. `WeakValueDictionary` mantiene valori con riferimenti deboli: quando un oggetto non ha altri riferimenti forti, viene rimosso automaticamente dal dizionario.

**Zero-copy**: Tecnica per elaborare dati senza copiarli in memoria. `memoryview` permette slicing zero-copy su buffer di byte.

---

## Cosa viene dopo

Hai completato il Tutorial 03 — Strutture Dati Avanzate. Ecco il percorso consigliato:

- **Tutorial 04 — Algoritmi e Complessita:** ordinamento (quicksort, mergesort, timsort), ricerca (BFS/DFS completo, A*), programmazione dinamica, greedy algorithms
- **Tutorial 05 — Programmazione Funzionale:** `map`, `filter`, `reduce`, `itertools`, generatori avanzati, funzioni pure, immutabilita
- **Tutorial 06 — Concorrenza:** `threading`, `multiprocessing`, `asyncio`, `concurrent.futures`, GIL e quando conta
- **Sorgente di riferimento:** `03-strutture-dati-avanzate.md` — la guida completa con sezioni aggiuntive su Trie, Bloom Filter, Dijkstra, pyrsistent e sortedcontainers

---

*Fine Tutorial 03 — Strutture Dati Avanzate*
*Durata totale stimata: 25-30 ore*
*Livello: principiante con basi Python, esperto in strutture dati alla fine*

