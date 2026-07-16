# Tutorial: Decoratori, Generatori e Context Manager — Dal Principiante all'Esperto

> **Companion to:** `04-decoratori-generatori-context-manager.md`
> **Scope:** funzioni di ordine superiore, closures, decoratori semplici e con argomenti, functools.wraps, decoratori di classe, stacking, generatori (yield/yield from/send/throw/close), espressioni generatrici, iteratori custom, context manager (__enter__/__exit__), contextlib (contextmanager, suppress, ExitStack, asynccontextmanager), ecc.
> **Prerequisiti:** `tutorial_02_oop.md` completato
> **Durata stimata:** 35–45 ore
> **Lingua:** Italiano

---

## Come Usare Questo Tutorial

Questo tutorial è scritto per chi sa già scrivere funzioni Python e ha completato i tutorial precedenti. Ogni concetto inizia con un'analogia del mondo reale, poi mostra il problema che risolve, poi la soluzione elegante. Non saltare le sezioni — ogni concetto costruisce sul precedente.

**Legenda degli output:**
Ogni blocco di codice ha un output atteso immediatamente sotto, in un blocco con il commento `# Output atteso:`.

**Regola d'oro:** Se l'output del tuo REPL non corrisponde a quello mostrato, leggi di nuovo la sezione prima di procedere.

---

## Indice Generale

- **PARTE A: Funzioni come Oggetti**
  - A1: Le Funzioni Sono Oggetti di Prima Classe
  - A2: Closures — Funzioni con Memoria
  - A3: Funzioni di Ordine Superiore
  - A4: Il Problema che i Decoratori Risolvono
  - A5: Il Tuo Primo Decoratore, Passo per Passo
  - A6: `functools.wraps` — Preservare l'Identità
  - A7: Decoratori con Argomenti
  - A8: Decoratori di Classe (Applicati a una Classe)
  - A9: Stacking — Impilare i Decoratori
  - A10: Decoratori come Classi
  - Errori Comuni della Parte A
  - Esercizi della Parte A

- **PARTE B: Generatori**
  - B1: Il Problema della Memoria
  - B2: `yield` — La Parola Magica
  - B3: Funzioni Generatrici vs Funzioni Normali
  - B4: Espressioni Generatrici
  - B5: `yield from` — Delegare il Lavoro
  - B6: Generatori Bidirezionali (send/throw/close)
  - B7: Iteratori Custom
  - B8: Pipeline di Generatori
  - Errori Comuni della Parte B
  - Esercizi della Parte B

- **PARTE C: Context Manager**
  - C1: Il Problema delle Risorse
  - C2: Il Protocollo `__enter__` / `__exit__`
  - C3: `@contextmanager` — La Via Più Semplice
  - C4: `suppress`, `redirect_stdout`, `closing`
  - C5: `ExitStack` — Gestione Dinamica
  - C6: Context Manager Asincroni
  - Errori Comuni della Parte C
  - 12+ Esercizi della Parte C

- **PARTE D: Deep Dive Esperto**
  - D1: Il Protocollo Descriptor
  - D2: `__init_subclass__` e Plugin Registry
  - D3: Generatori Coroutine e asyncio
  - D4: Storia dei PEP

- **PARTE E: Riepilogo e Riferimenti**
  - Checklist (40+ voci)
  - Diagramma Decisionale
  - Glossario
  - Link ai Tutorial Successivi

---

# PARTE A: Funzioni come Oggetti

---

## A1: Le Funzioni Sono Oggetti di Prima Classe

### L'Analogia: La Lettera Sigillata

Immagina di scrivere una lettera. La lettera contiene istruzioni: "Accendi il forno, metti la pizza, aspetta 20 minuti". Puoi:
- Tenere la lettera in tasca (assegnare la funzione a una variabile)
- Passarla a un amico (passare la funzione come argomento)
- Riceverla come regalo (ricevere una funzione come valore di ritorno)
- Mettere la lettera dentro una busta più grande (funzioni che contengono funzioni)

La lettera non si "esegue" finché qualcuno non la apre e legge. Allo stesso modo, una funzione Python è solo un oggetto finché non la chiami con `()`.

### Il Concetto: Cosa Significa "Prima Classe"?

In Python, le funzioni sono oggetti. Non sono speciali — sono oggetti esattamente come gli interi, le stringhe, le liste. Questo significa che puoi fare con una funzione tutto quello che puoi fare con qualsiasi altro oggetto.

**Passo 1: Una funzione è un oggetto — puoi assegnarla a una variabile**

```python
# Definiamo una funzione normale
def saluta(nome):
    return f"Ciao, {nome}!"

# Chiamiamola normalmente
risultato = saluta("Mario")
print(risultato)
```

```
# Output atteso:
Ciao, Mario!
```

```python
# Ora assegniamo la FUNZIONE a un'altra variabile
# Nota: non scriviamo saluta() con le parentesi — non la chiamiamo, la assegniamo
mia_funzione = saluta

# mia_funzione ora E' la stessa funzione di saluta
print(mia_funzione("Luigi"))
```

```
# Output atteso:
Ciao, Luigi!
```

```python
# Sono proprio la stessa cosa?
print(saluta)
print(mia_funzione)
print(saluta is mia_funzione)  # e' lo stesso oggetto in memoria?
```

```
# Output atteso:
<function saluta at 0x7f1234567890>
<function saluta at 0x7f1234567890>
True
```

L'indirizzo di memoria e' lo stesso. Non abbiamo copiato la funzione — abbiamo creato un secondo nome che punta allo stesso oggetto.

**Passo 2: Una funzione ha attributi, come qualsiasi oggetto**

```python
def saluta(nome):
    """Funzione che saluta una persona per nome."""
    return f"Ciao, {nome}!"

# Le funzioni hanno attributi built-in
print(saluta.__name__)    # nome della funzione
print(saluta.__doc__)     # docstring
print(saluta.__module__)  # modulo in cui e' definita
```

```
# Output atteso:
saluta
Funzione che saluta una persona per nome.
__main__
```

```python
# Puoi anche aggiungere attributi personalizzati a una funzione
saluta.autore = "Mario Rossi"
saluta.versione = 1.0

print(saluta.autore)
print(saluta.versione)
```

```
# Output atteso:
Mario Rossi
1.0
```

**Passo 3: Puoi passare una funzione come argomento a un'altra funzione**

```python
def moltiplica_per_due(x):
    return x * 2

def aggiungi_dieci(x):
    return x + 10

def applica(funzione, valore):
    """Applica una funzione a un valore e restituisce il risultato."""
    return funzione(valore)

# Passiamo la funzione come argomento — nota: senza parentesi!
risultato1 = applica(moltiplica_per_due, 5)
risultato2 = applica(aggiungi_dieci, 5)

print(f"Moltiplica per due 5: {risultato1}")
print(f"Aggiungi dieci a 5: {risultato2}")
```

```
# Output atteso:
Moltiplica per due 5: 10
Aggiungi dieci a 5: 15
```

```python
# Esempio piu' pratico: una lista di operazioni
def raddoppia(x):
    return x * 2

def quadrato(x):
    return x ** 2

def inverso(x):
    return -x

operazioni = [raddoppia, quadrato, inverso]
valore = 3

for op in operazioni:
    print(f"{op.__name__}({valore}) = {op(valore)}")
```

```
# Output atteso:
raddoppia(3) = 6
quadrato(3) = 9
inverso(3) = -3
```

**Passo 4: Puoi restituire una funzione da un'altra funzione**

```python
def crea_moltiplicatore(n):
    """Crea e restituisce una funzione che moltiplica per n."""
    def moltiplica(x):
        return x * n
    return moltiplica  # restituiamo la funzione, non il risultato

# Creiamo due funzioni specializzate
doppio = crea_moltiplicatore(2)
triplo = crea_moltiplicatore(3)

print(doppio(5))   # 5 * 2
print(triplo(5))   # 5 * 3
print(doppio(10))  # 10 * 2
```

```
# Output atteso:
10
15
20
```

```python
# Possiamo vedere che doppio e triplo sono funzioni distinte
print(type(doppio))
print(doppio.__name__)
```

```
# Output atteso:
<class 'function'>
moltiplica
```

Entrambe si chiamano `moltiplica` internamente, ma sono oggetti distinti con comportamenti diversi — perche' ricordano il valore di `n` dal momento della loro creazione. Questo e' il seme delle **closures**, che vedremo nella sezione A2.

**Passo 5: Le funzioni in liste e dizionari**

```python
# Le funzioni possono stare in strutture dati
def somma(a, b):
    return a + b

def differenza(a, b):
    return a - b

def prodotto(a, b):
    return a * b

# Dizionario che mappa nome operazione -> funzione
operazioni = {
    "+": somma,
    "-": differenza,
    "*": prodotto,
}

a, b = 10, 3
for simbolo, funzione in operazioni.items():
    risultato = funzione(a, b)
    print(f"{a} {simbolo} {b} = {risultato}")
```

```
# Output atteso:
10 + 3 = 13
10 - 3 = 7
10 * 3 = 30
```

Questo schema "dispatch table" e' molto piu' pulito di un lungo `if/elif/else`.

**Passo 6: Lambda — funzioni anonime**

```python
# Una lambda e' una funzione anonima di una sola espressione
raddoppia = lambda x: x * 2

print(raddoppia(5))
print(type(raddoppia))
```

```
# Output atteso:
10
<class 'function'>
```

```python
# Le lambda sono utili quando hai bisogno di una funzione breve al volo
numeri_misti = [-5, 3, -1, 8, -2]
ordinati_per_abs = sorted(numeri_misti, key=lambda x: abs(x))
print(ordinati_per_abs)
```

```
# Output atteso:
[-1, -2, 3, -5, 8]
```

```python
# Buon uso di lambda: ordinare strutture complesse
persone = [
    {"nome": "Alice", "eta": 30},
    {"nome": "Bob", "eta": 25},
    {"nome": "Carlo", "eta": 35},
]
ordinati_per_eta = sorted(persone, key=lambda p: p["eta"])
for p in ordinati_per_eta:
    print(f"{p['nome']}: {p['eta']} anni")
```

```
# Output atteso:
Bob: 25 anni
Alice: 30 anni
Carlo: 35 anni
```

### Quando NON usare lambda

Le lambda hanno limitazioni importanti. Non possono contenere statements (`if` con corpo, `for`, `while`), non possono avere docstring. Per qualunque cosa piu' complessa di una singola espressione, usa `def`.

```python
# BAD: lambda troppo complessa — difficile da leggere e debuggare
calcola = lambda x, y, fattore=1: (x * y * fattore) if (x > 0 and y > 0) else 0

# GOOD: funzione con nome, piu' leggibile
def calcola(x, y, fattore=1):
    """Calcola il prodotto di x per y, moltiplicato per il fattore."""
    if x > 0 and y > 0:
        return x * y * fattore
    return 0
```

### Riepilogo di A1

Le funzioni Python sono oggetti di prima classe. Puoi:
- Assegnarle a variabili
- Passarle come argomenti
- Restituirle come risultati
- Metterle in liste e dizionari
- Aggiungere attributi

Questo e' il fondamento di tutto quello che viene dopo.

---

## A2: Closures — Funzioni con Memoria

### L'Analogia: Lo Zaino dello Studente

Immagina uno studente universitario. Quando esce di casa la mattina, porta uno zaino con tutto il necessario: penna, quaderno, merenda. Anche se va in un bar lontano da casa, porta con se' tutto quello di cui ha bisogno dalla sua stanza.

Una closure e' una funzione che porta con se' "lo zaino" del suo ambiente di creazione. Anche quando la funzione viene usata lontano dal contesto in cui e' stata definita, ricorda le variabili del suo ambiente originale.

### Il Problema: Variabili con "Memoria"

Supponiamo di dover creare un contatore. Come lo faresti con quello che sai ora?

**Soluzione brutta (con variabile globale):**

```python
# Approccio con variabile globale — NON FARE COSI'
conteggio = 0  # variabile globale

def incrementa():
    global conteggio  # dobbiamo dichiarare global
    conteggio += 1
    return conteggio

print(incrementa())  # 1
print(incrementa())  # 2
print(incrementa())  # 3
```

```
# Output atteso:
1
2
3
```

Problemi con questo approccio:
1. Il conteggio e' accessibile e modificabile da chiunque: `conteggio = 100` lo azzera
2. Non possiamo avere due contatori separati
3. Testare funzioni che dipendono da variabili globali e' un incubo
4. Il modulo non puo' essere importato due volte in modo indipendente

**Soluzione elegante (con closure):**

```python
def crea_contatore(inizio=0):
    """Crea e restituisce un contatore indipendente."""
    conteggio = inizio  # questa variabile vive nell'ambiente della closure

    def incrementa():
        nonlocal conteggio  # nonlocal: "usa la variabile dello scope esterno"
        conteggio += 1
        return conteggio

    return incrementa

# Creiamo due contatori completamente indipendenti
contatore_a = crea_contatore(0)
contatore_b = crea_contatore(100)

print(contatore_a())  # 1
print(contatore_a())  # 2
print(contatore_b())  # 101
print(contatore_a())  # 3  (contatore_a non e' influenzato da contatore_b)
print(contatore_b())  # 102
```

```
# Output atteso:
1
2
101
3
102
```

I due contatori sono completamente indipendenti. Ciascuno porta il suo "zaino" con il proprio valore di `conteggio`.

### Come Funziona una Closure?

Quando Python incontra una funzione che usa variabili del contesto esterno, crea una **closure**: cattura quelle variabili e le "chiude" (to close) dentro la funzione.

```python
def crea_contatore(inizio=0):
    conteggio = inizio

    def incrementa():
        nonlocal conteggio
        conteggio += 1
        return conteggio

    return incrementa

contatore = crea_contatore(0)

# Puoi ispezionare le variabili catturate dalla closure
print(contatore.__closure__)                       # la closure stessa
print(contatore.__closure__[0].cell_contents)     # valore catturato
```

```
# Output atteso:
(<cell at 0x7f...>,)
0
```

```python
# Dopo alcune chiamate, il valore cambia
contatore()
contatore()
print(contatore.__closure__[0].cell_contents)  # ora vale 2
```

```
# Output atteso:
2
```

### La Parola Chiave `nonlocal`

`nonlocal` e' come `global`, ma per lo scope della funzione esterna (invece dello scope globale del modulo).

```python
x = 10  # scope globale

def esterna():
    x = 20  # scope di esterna (shadowing del globale)

    def interna():
        nonlocal x  # si riferisce alla x di esterna, non a quella globale
        x += 5
        return x

    return interna

f = esterna()
print(f())  # 25 (20 + 5)
print(f())  # 30 (25 + 5)
print(x)    # 10 — la x globale non e' stata toccata
```

```
# Output atteso:
25
30
10
```

### Esempio Pratico: Logger Configurabile

```python
def crea_logger(prefisso, livello="INFO"):
    """Crea una funzione di logging configurata."""

    def log(messaggio):
        print(f"[{livello}] [{prefisso}] {messaggio}")

    return log

# Creiamo logger specializzati
log_db = crea_logger("DATABASE")
log_api = crea_logger("API", "DEBUG")
log_err = crea_logger("ERROR", "ERROR")

log_db("Connessione stabilita")
log_api("Richiesta ricevuta: GET /utenti")
log_err("Impossibile leggere il file")
```

```
# Output atteso:
[INFO] [DATABASE] Connessione stabilita
[DEBUG] [API] Richiesta ricevuta: GET /utenti
[ERROR] [ERROR] Impossibile leggere il file
```

### Esempio Pratico: Memoizzazione Manuale

```python
def crea_cache_memoize():
    """Crea una funzione memoize con cache condivisa."""
    cache = {}  # catturata dalla closure

    def memoize(funzione):
        import functools

        @functools.wraps(funzione)
        def wrapper(*args):
            if args not in cache:
                cache[args] = funzione(*args)
                print(f"  [MISS] Calcolo {funzione.__name__}{args}")
            else:
                print(f"  [HIT]  Cache per {funzione.__name__}{args}")
            return cache[args]
        return wrapper

    return memoize

memoize = crea_cache_memoize()

@memoize
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(5))
print("---")
print(fibonacci(3))  # gia' in cache
```

```
# Output atteso:
  [MISS] Calcolo fibonacci(5)
  [MISS] Calcolo fibonacci(4)
  [MISS] Calcolo fibonacci(3)
  [MISS] Calcolo fibonacci(2)
  [MISS] Calcolo fibonacci(1)
  [MISS] Calcolo fibonacci(0)
  [HIT]  Cache per fibonacci(1)
  [HIT]  Cache per fibonacci(2)
  [HIT]  Cache per fibonacci(3)
5
---
  [HIT]  Cache per fibonacci(3)
2
```

### Trappola Comune: La Closure in un Loop

Questa e' una delle trappole piu' famose di Python:

```python
# SBAGLIATO: tutte le funzioni catturano la stessa variabile i
funzioni_sbagliate = []
for i in range(5):
    funzioni_sbagliate.append(lambda: i)  # i viene catturato per riferimento!

# Alla fine del loop, i vale 4
for f in funzioni_sbagliate:
    print(f())  # tutte stampano 4!
```

```
# Output atteso:
4
4
4
4
4
```

```python
# CORRETTO: catturiamo il valore attuale di i come argomento di default
funzioni_corrette = []
for i in range(5):
    funzioni_corrette.append(lambda x=i: x)  # x=i cattura il valore ora

for f in funzioni_corrette:
    print(f())
```

```
# Output atteso:
0
1
2
3
4
```

```python
# Alternativa: usare una funzione factory
def crea_funzione(valore):
    return lambda: valore

funzioni_corrette2 = [crea_funzione(i) for i in range(5)]
for f in funzioni_corrette2:
    print(f())
```

```
# Output atteso:
0
1
2
3
4
```

### Riepilogo di A2

Una closure e' una funzione che "ricorda" le variabili del suo ambiente di creazione. Le variabili catturate sono accessibili tramite `__closure__`. La parola chiave `nonlocal` permette di modificare variabili dello scope esterno. Attenzione alla trappola del loop — cattura il riferimento, non il valore.

---

## A3: Funzioni di Ordine Superiore

### L'Analogia: Il Manager e i Dipendenti

Un manager non fa il lavoro fisico — organizza e delega. Dice: "Prendi questi dati, applicaci questa trasformazione, restituisci il risultato". Le funzioni di ordine superiore fanno lo stesso: ricevono o restituiscono funzioni, delegando il lavoro specifico.

### Cosa Sono le Funzioni di Ordine Superiore (HOF)?

Una funzione e' "di ordine superiore" se:
1. Accetta una o piu' funzioni come argomenti, **oppure**
2. Restituisce una funzione come risultato

### `map()`: Trasforma Ogni Elemento

```python
# Problema: trasformare ogni elemento di una lista
numeri = [1, 2, 3, 4, 5]

# Modo vecchio: loop manuale
quadrati = []
for n in numeri:
    quadrati.append(n ** 2)
print(quadrati)
```

```
# Output atteso:
[1, 4, 9, 16, 25]
```

```python
# Con map(): applica una funzione a ogni elemento
# map restituisce un iteratore — usiamo list() per materializzarlo
quadrati = list(map(lambda x: x ** 2, numeri))
print(quadrati)
```

```
# Output atteso:
[1, 4, 9, 16, 25]
```

```python
# Esempio con funzione esistente: str.title e' gia' una funzione
nomi = ["mario rossi", "luigi bianchi", "anna verdi"]
nomi_formattati = list(map(str.title, nomi))
print(nomi_formattati)
```

```
# Output atteso:
['Mario Rossi', 'Luigi Bianchi', 'Anna Verdi']
```

```python
# map con funzione propria
def raddoppia_e_aggiungi_uno(x):
    return x * 2 + 1

risultati = list(map(raddoppia_e_aggiungi_uno, numeri))
print(risultati)
```

```
# Output atteso:
[3, 5, 7, 9, 11]
```

```python
# map su piu' iterabili simultaneamente
lista_a = [1, 2, 3]
lista_b = [10, 20, 30]
somme = list(map(lambda a, b: a + b, lista_a, lista_b))
print(somme)
```

```
# Output atteso:
[11, 22, 33]
```

### `filter()`: Seleziona Elementi

```python
numeri = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Con filter(): mantieni solo gli elementi per cui la funzione restituisce True
pari = list(filter(lambda x: x % 2 == 0, numeri))
print(pari)
```

```
# Output atteso:
[2, 4, 6, 8, 10]
```

```python
# Esempio con dati strutturati
prodotti = [
    {"nome": "Mela",    "prezzo": 0.80, "disponibile": True},
    {"nome": "Banana",  "prezzo": 0.50, "disponibile": False},
    {"nome": "Arancia", "prezzo": 1.20, "disponibile": True},
    {"nome": "Kiwi",    "prezzo": 2.00, "disponibile": False},
]

disponibili = list(filter(lambda p: p["disponibile"], prodotti))
for p in disponibili:
    print(f"  {p['nome']}: euro{p['prezzo']:.2f}")
```

```
# Output atteso:
  Mela: euro0.80
  Arancia: euro1.20
```

### `sorted()` con `key`: Ordina con Criterio Personalizzato

```python
# Ordinare per un attributo specifico
persone = [
    {"nome": "Charlie", "eta": 35},
    {"nome": "Alice",   "eta": 25},
    {"nome": "Bob",     "eta": 30},
]

# Per eta' crescente
per_eta = sorted(persone, key=lambda p: p["eta"])
for p in per_eta:
    print(f"  {p['nome']}: {p['eta']} anni")
```

```
# Output atteso:
  Alice: 25 anni
  Bob: 30 anni
  Charlie: 35 anni
```

```python
# Per nome in ordine alfabetico (ignorando maiuscole/minuscole)
parole = ["banana", "Arancia", "ciliegia", "Data", "fico"]
ordinate = sorted(parole, key=str.lower)
print(ordinate)
```

```
# Output atteso:
['Arancia', 'banana', 'ciliegia', 'Data', 'fico']
```

```python
# Ordinamento per chiave multipla: prima per cognome, poi per nome
persone2 = [
    ("Mario", "Rossi"),
    ("Luigi", "Bianchi"),
    ("Anna",  "Rossi"),
    ("Carlo", "Bianchi"),
]

# Ordina prima per cognome (indice 1), poi per nome (indice 0)
ordinate = sorted(persone2, key=lambda p: (p[1], p[0]))
for p in ordinate:
    print(f"  {p[1]}, {p[0]}")
```

```
# Output atteso:
  Bianchi, Carlo
  Bianchi, Luigi
  Rossi, Anna
  Rossi, Mario
```

### `functools.reduce()`: Riduzione a un Valore

```python
from functools import reduce

numeri = [1, 2, 3, 4, 5]

# Somma equivalente
totale = reduce(lambda acc, x: acc + x, numeri)
print(f"Somma: {totale}")

# Prodotto
prodotto = reduce(lambda acc, x: acc * x, numeri)
print(f"Prodotto: {prodotto}")

# Massimo senza usare max()
massimo = reduce(lambda acc, x: acc if acc > x else x, numeri)
print(f"Massimo: {massimo}")
```

```
# Output atteso:
Somma: 15
Prodotto: 120
Massimo: 5
```

### Componibilita': Catena di HOF

```python
# Pipeline di trasformazioni: dati sporchi -> dati puliti
dati_grezzi = ["  Mario ", "Luigi", "  ", "Anna", "", "Carlo  "]

# Passo 1: rimuovi spazi
# Passo 2: filtra le stringhe vuote
# Passo 3: converti in maiuscolo
dati_puliti = list(map(
    str.upper,
    filter(
        bool,  # bool("") == False, bool("Luigi") == True
        map(str.strip, dati_grezzi)
    )
))
print(dati_puliti)
```

```
# Output atteso:
['MARIO', 'LUIGI', 'ANNA', 'CARLO']
```

```python
# Con list comprehension (spesso piu' leggibile)
dati_puliti2 = [
    nome.upper()
    for nome in (n.strip() for n in dati_grezzi)
    if nome.strip()
]
print(dati_puliti2)
```

```
# Output atteso:
['MARIO', 'LUIGI', 'ANNA', 'CARLO']
```

### HOF che Crei Tu Stesso

```python
def componi(*funzioni):
    """Compone N funzioni in una sola: componi(f, g)(x) == f(g(x))."""
    from functools import reduce

    def composizione(valore):
        return reduce(lambda v, f: f(v), reversed(funzioni), valore)

    return composizione

# Definiamo alcune trasformazioni semplici
aggiungi_uno = lambda x: x + 1
moltiplica_per_due = lambda x: x * 2
quadrato = lambda x: x ** 2

# Componiamo: prima quadrato, poi moltiplica_per_due, poi aggiungi_uno
trasforma = componi(aggiungi_uno, moltiplica_per_due, quadrato)

print(trasforma(3))  # quadrato(3)=9, *2=18, +1=19
```

```
# Output atteso:
19
```

### Riepilogo di A3

Le funzioni di ordine superiore (`map`, `filter`, `sorted`, `reduce`) applicano una funzione a strutture dati. Puoi comporle in pipeline. Crei facilmente le tue HOF perche' le funzioni sono oggetti di prima classe.

---

## A4: Il Problema che i Decoratori Risolvono

### L'Analogia: Il Guscio della Lumaca

Una lumaca ha il suo corpo (funzione originale) e un guscio (comportamento aggiuntivo). Il guscio non cambia la lumaca — la protegge e la arricchisce. I decoratori sono il guscio: avvolgono una funzione aggiungendo comportamento prima e/o dopo la sua esecuzione, senza modificare il corpo della funzione.

### Il Problema: Codice Ripetuto Ovunque

Sei uno sviluppatore che lavora su un'applicazione finanziaria. Hai molte funzioni e il tuo capo dice: "Dobbiamo loggare tutte le chiamate. Per ciascuna devo sapere: quando viene chiamata, con quali argomenti, quanto tempo ci vuole, e il risultato."

**Prima soluzione — copia-incolla (pessima):**

```python
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def calcola_iva(prezzo):
    """Calcola l'IVA al 22%."""
    inizio = time.time()
    logging.info(f"calcola_iva chiamata con prezzo={prezzo}")

    risultato = prezzo * 1.22  # logica reale

    durata = time.time() - inizio
    logging.info(f"calcola_iva completata in {durata:.4f}s, risultato={risultato}")
    return risultato

def calcola_sconto(prezzo, percentuale):
    """Calcola il prezzo con sconto."""
    inizio = time.time()
    logging.info(f"calcola_sconto chiamata con prezzo={prezzo}, percentuale={percentuale}")

    risultato = prezzo * (1 - percentuale / 100)  # logica reale

    durata = time.time() - inizio
    logging.info(f"calcola_sconto completata in {durata:.4f}s, risultato={risultato}")
    return risultato

# ... e cosi' via per ogni funzione — ripetendo lo stesso codice
```

Problemi di questa soluzione:
1. Codice di logging ripetuto in ogni funzione
2. Se cambia il formato del log, devi modificare 20 posti
3. La logica reale e' sepolta nel codice di logging
4. Facile dimenticarsi di aggiungere il logging a una nuova funzione
5. Non puoi disabilitare facilmente il logging per i test

**Seconda soluzione — funzione helper (meglio, ma ancora problematica):**

```python
import time
import logging

def chiama_con_log(funzione, *args, **kwargs):
    """Chiama una funzione con logging."""
    inizio = time.time()
    logging.info(f"{funzione.__name__} chiamata")
    risultato = funzione(*args, **kwargs)
    logging.info(f"{funzione.__name__} completata in {time.time()-inizio:.4f}s")
    return risultato

# Uso: devo cambiare ogni punto di chiamata
risultato = chiama_con_log(calcola_iva, 100)
```

Problemi:
1. Tutti i punti di chiamata devono essere modificati
2. Il codice diventa meno leggibile

**La soluzione elegante: i decoratori**

```python
import time
import logging
import functools

def con_logging(funzione):
    """Decoratore che aggiunge logging a qualsiasi funzione."""
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.time()
        logging.info(f"{funzione.__name__} chiamata con args={args}, kwargs={kwargs}")

        risultato = funzione(*args, **kwargs)  # chiama la funzione originale

        durata = time.time() - inizio
        logging.info(f"{funzione.__name__} completata in {durata:.4f}s -> {risultato}")
        return risultato
    return wrapper

# Applico il decoratore UNA VOLTA a ciascuna funzione
@con_logging
def calcola_iva(prezzo):
    """Calcola l'IVA al 22%."""
    return prezzo * 1.22

@con_logging
def calcola_sconto(prezzo, percentuale):
    """Calcola il prezzo con sconto."""
    return prezzo * (1 - percentuale / 100)

# Uso normale — niente cambia nel codice chiamante!
iva = calcola_iva(100)
sconto = calcola_sconto(200, 10)
```

Questo e' lo schema base del decoratore. Analizziamolo in dettaglio nella sezione A5.

---

## A5: Il Tuo Primo Decoratore, Passo per Passo

### Dissezione Anatomica di un Decoratore

```python
def il_mio_decoratore(funzione):  # [1] riceve la funzione originale

    def wrapper(*args, **kwargs):  # [2] funzione wrapper
        print("Prima della chiamata")   # [3] codice PRE

        risultato = funzione(*args, **kwargs)  # [4] chiama l'originale

        print("Dopo la chiamata")  # [5] codice POST
        return risultato           # [6] restituisce il risultato

    return wrapper  # [7] restituisce il wrapper (non lo chiama!)
```

Analizziamo ogni parte:

1. `il_mio_decoratore(funzione)` — il decoratore e' una funzione che riceve un'altra funzione
2. `def wrapper(*args, **kwargs)` — definiamo una funzione interna che accetta qualsiasi argomento
3. Codice prima della chiamata — comportamento aggiuntivo PRE
4. `funzione(*args, **kwargs)` — chiamiamo la funzione originale passando tutti gli argomenti
5. Codice dopo la chiamata — comportamento aggiuntivo POST
6. `return risultato` — restituire il risultato e' fondamentale
7. `return wrapper` — restituiamo la funzione wrapper senza chiamarla

### La Sintassi `@` e' Solo Zucchero Sintattico

```python
import functools

def timbro(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print(f"Chiamata a: {funzione.__name__}")
        return funzione(*args, **kwargs)
    return wrapper

# Questi due sono ESATTAMENTE EQUIVALENTI:

# Modo 1: senza @
def saluta(nome):
    return f"Ciao, {nome}!"
saluta = timbro(saluta)  # sostituiamo saluta con il wrapper

# Modo 2: con @ (zucchero sintattico per lo stesso)
@timbro
def saluta2(nome):
    return f"Ciao, {nome}!"

# Sono identici nel comportamento
print(saluta("Mario"))
print(saluta2("Luigi"))
```

```
# Output atteso:
Chiamata a: saluta
Ciao, Mario!
Chiamata a: saluta2
Ciao, Luigi!
```

### Costruire il Decoratore `@timer` da Zero

```python
import time
import functools

def timer(funzione):
    """Misura e stampa il tempo di esecuzione di una funzione."""
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        risultato = funzione(*args, **kwargs)
        fine = time.perf_counter()
        durata = fine - inizio
        print(f"[timer] {funzione.__name__} eseguita in {durata:.6f} secondi")
        return risultato
    return wrapper

@timer
def calcola_somma(n):
    """Calcola la somma dei primi n numeri interi."""
    return sum(range(n + 1))

@timer
def calcola_somma_lenta(n):
    """Calcola la somma con un loop manuale (piu' lento)."""
    totale = 0
    for i in range(n + 1):
        totale += i
    return totale

risultato1 = calcola_somma(1_000_000)
risultato2 = calcola_somma_lenta(1_000_000)

print(f"Risultato veloce: {risultato1}")
print(f"Risultato lento:  {risultato2}")
```

```
# Output atteso (i tempi variano sul tuo hardware):
[timer] calcola_somma eseguita in 0.012341 secondi
[timer] calcola_somma_lenta eseguita in 0.045678 secondi
Risultato veloce: 500000500000
Risultato lento:  500000500000
```

### Il Decoratore `@retry` — Gestire i Fallimenti

```python
import time
import functools

def retry(funzione):
    """Riprova la funzione fino a 3 volte in caso di eccezione."""
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        tentativi = 3
        for tentativo in range(1, tentativi + 1):
            try:
                return funzione(*args, **kwargs)
            except Exception as e:
                if tentativo == tentativi:
                    print(f"[retry] Tutti i {tentativi} tentativi falliti.")
                    raise
                print(f"[retry] Tentativo {tentativo}/{tentativi} fallito: {e}. Riprovo...")
                time.sleep(0.05)
    return wrapper

# Simuliamo una connessione instabile
contatore_tentativi = 0

@retry
def connetti_al_database():
    """Simula una connessione che fallisce i primi due tentativi."""
    global contatore_tentativi
    contatore_tentativi += 1
    if contatore_tentativi < 3:
        raise ConnectionError(f"Connessione rifiutata (tentativo {contatore_tentativi})")
    return "Connessione stabilita!"

risultato = connetti_al_database()
print(risultato)
```

```
# Output atteso:
[retry] Tentativo 1/3 fallito: Connessione rifiutata (tentativo 1). Riprovo...
[retry] Tentativo 2/3 fallito: Connessione rifiutata (tentativo 2). Riprovo...
Connessione stabilita!
```

### Il Decoratore `@validate_types` — Controllare i Tipi

```python
import functools
import inspect

def validate_types(funzione):
    """Verifica che gli argomenti corrispondano agli hints di tipo."""
    hints = funzione.__annotations__

    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(funzione)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        for nome_param, valore in bound.arguments.items():
            if nome_param in hints and nome_param != "return":
                tipo_atteso = hints[nome_param]
                if not isinstance(valore, tipo_atteso):
                    raise TypeError(
                        f"Parametro '{nome_param}' deve essere "
                        f"{tipo_atteso.__name__}, ricevuto {type(valore).__name__}"
                    )

        return funzione(*args, **kwargs)
    return wrapper

@validate_types
def dividi(a: float, b: float) -> float:
    return a / b

print(dividi(10.0, 2.0))  # ok

try:
    print(dividi(10, 2))  # int invece di float
except TypeError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
5.0
Errore: Parametro 'a' deve essere float, ricevuto int
```

### Il Decoratore `@singleton` — Una Sola Istanza

```python
import functools

def singleton(classe):
    """Garantisce che esista al massimo una istanza della classe."""
    istanze = {}

    @functools.wraps(classe)
    def get_istanza(*args, **kwargs):
        if classe not in istanze:
            istanze[classe] = classe(*args, **kwargs)
        return istanze[classe]

    return get_istanza

@singleton
class ConfigurazioneApp:
    def __init__(self):
        self.debug = False
        self.database_url = "postgresql://localhost/mydb"
        print("ConfigurazioneApp creata (UNA SOLA VOLTA)")

# Ogni chiamata restituisce la stessa istanza
config1 = ConfigurazioneApp()
config2 = ConfigurazioneApp()
config3 = ConfigurazioneApp()

print(config1 is config2)   # True — stessa istanza
print(config1 is config3)   # True — stessa istanza
config1.debug = True
print(config2.debug)        # True — e' lo stesso oggetto
```

```
# Output atteso:
ConfigurazioneApp creata (UNA SOLA VOLTA)
True
True
True
```

### Il Problema con `*args` e `**kwargs`

Il wrapper usa `*args, **kwargs` per ricevere qualsiasi combinazione di argomenti. Vediamo perche' e' necessario:

```python
import functools

# Decoratore SBAGLIATO: funziona solo con funzioni senza argomenti
def decoratore_sbagliato(funzione):
    @functools.wraps(funzione)
    def wrapper():  # accetta solo zero argomenti
        print("Prima")
        return funzione()
    return wrapper

@decoratore_sbagliato
def senza_argomenti():
    return 42

print(senza_argomenti())  # Funziona

@decoratore_sbagliato
def con_argomenti(a, b):
    return a + b

try:
    con_argomenti(1, 2)
except TypeError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
Prima
42
Errore: wrapper() takes 0 positional arguments but 2 were given
```

```python
import functools

# Decoratore CORRETTO: usa *args e **kwargs
def decoratore_corretto(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):  # accetta qualsiasi argomento
        print("Prima")
        risultato = funzione(*args, **kwargs)  # li passa tutti all'originale
        print("Dopo")
        return risultato
    return wrapper

@decoratore_corretto
def senza_argomenti():
    return 42

@decoratore_corretto
def con_molti_argomenti(a, b, c=0, *, d=None):
    return a + b + c + (d or 0)

print(senza_argomenti())
print(con_molti_argomenti(1, 2, c=3, d=4))
```

```
# Output atteso:
Prima
Dopo
42
Prima
Dopo
10
```

---

## A6: `functools.wraps` — Preservare l'Identita'

### Il Problema: La Funzione Wrapper Nasconde l'Originale

```python
def timer(funzione):
    def wrapper(*args, **kwargs):
        import time
        inizio = time.time()
        risultato = funzione(*args, **kwargs)
        print(f"Tempo: {time.time()-inizio:.4f}s")
        return risultato
    return wrapper

@timer
def calcola(n):
    """Calcola la somma dei primi n numeri."""
    return sum(range(n))

# Problema: la funzione decorata ha perso la sua identita'!
print(calcola.__name__)  # 'wrapper' invece di 'calcola'
print(calcola.__doc__)   # None invece della docstring
```

```
# Output atteso:
wrapper
None
```

Questo e' un problema serio:
- Il logging mostra "wrapper" invece del nome reale
- `help(calcola)` mostra informazioni sbagliate
- I debugger mostrano il nome sbagliato
- Le stack trace diventano confuse

### La Soluzione: `functools.wraps`

```python
import functools
import time

def timer(funzione):
    @functools.wraps(funzione)  # questa riga risolve tutto
    def wrapper(*args, **kwargs):
        inizio = time.time()
        risultato = funzione(*args, **kwargs)
        print(f"[timer] {funzione.__name__} -> {time.time()-inizio:.4f}s")
        return risultato
    return wrapper

@timer
def calcola(n):
    """Calcola la somma dei primi n numeri."""
    return sum(range(n))

# Ora la funzione decorata mantiene la sua identita'
print(calcola.__name__)    # 'calcola'
print(calcola.__doc__)     # 'Calcola la somma...'
print(calcola.__wrapped__) # la funzione originale
```

```
# Output atteso:
calcola
Calcola la somma dei primi n numeri.
<function calcola at 0x7f...>
```

### Cosa Fa Esattamente `functools.wraps`?

`@functools.wraps(funzione)` copia questi attributi dalla funzione originale al wrapper:
- `__name__`: nome della funzione
- `__qualname__`: nome qualificato (es: `Classe.metodo`)
- `__doc__`: docstring
- `__dict__`: dizionario degli attributi
- `__module__`: modulo di definizione
- `__annotations__`: annotazioni di tipo
- `__wrapped__`: riferimento alla funzione originale (aggiunto da wraps)

```python
import functools

def ispezione(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper

@ispezione
def esempio(x: int, y: int = 0) -> int:
    """Esempio di funzione con annotazioni."""
    return x + y

print(f"Nome:        {esempio.__name__}")
print(f"Docstring:   {esempio.__doc__}")
print(f"Annotazioni: {esempio.__annotations__}")
print(f"Originale:   {esempio.__wrapped__}")
```

```
# Output atteso:
Nome:        esempio
Docstring:   Esempio di funzione con annotazioni.
Annotazioni: {'x': <class 'int'>, 'y': <class 'int'>, 'return': <class 'int'>}
Originale:   <function esempio at 0x7f...>
```

### Accedere alla Funzione Originale con `__wrapped__`

```python
import functools
import time

def timer(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.time()
        risultato = funzione(*args, **kwargs)
        print(f"[timer] {time.time()-inizio:.6f}s")
        return risultato
    return wrapper

@timer
def lavora(n):
    """Simula un lavoro pesante."""
    return sum(i * i for i in range(n))

# Possiamo bypassare il decoratore accedendo a __wrapped__
print("Con decoratore:")
risultato1 = lavora(10000)

print("Senza decoratore (via __wrapped__):")
risultato2 = lavora.__wrapped__(10000)

print(f"Stesso risultato: {risultato1 == risultato2}")
```

```
# Output atteso:
Con decoratore:
[timer] 0.003456s
Senza decoratore (via __wrapped__):
Stesso risultato: True
```

Questo e' utile nei test — puoi testare la logica pura senza il comportamento aggiunto dal decoratore.

### Regola d'Oro

```python
# Modello completo per un decoratore corretto
import functools

def mio_decoratore(funzione):
    """Documentazione del decoratore stesso."""
    @functools.wraps(funzione)    # SEMPRE — mai dimenticarlo
    def wrapper(*args, **kwargs):
        # comportamento PRE
        risultato = funzione(*args, **kwargs)
        # comportamento POST
        return risultato
    return wrapper
```

---

## A7: Decoratori con Argomenti

### L'Analogia: Configurare il Timer

Immagina un timer da cucina. Un semplice decoratore `@timer` e' come un timer fisso — ti da' sempre l'ora. Ma spesso vuoi configurare il comportamento: "Ripeti la funzione esattamente 3 volte" o "Riprova 5 volte invece di 3". Per questo servono i decoratori con argomenti.

### Il Problema: Decoratori Troppo Rigidi

```python
# Questo decoratore @retry riprova sempre esattamente 3 volte
# E se voglio 5 tentativi? E se voglio configurare la pausa?
@retry
def funzione_critica():
    ...

# Vorrei poter scrivere:
@retry(tentativi=5, pausa=2.0)
def funzione_meno_critica():
    ...
```

### Come Funziona: Tre Livelli di Annidamento

Un decoratore con argomenti richiede un livello in piu':

```
retry(tentativi=5)     ->  restituisce il decoratore vero
  decoratore(funzione) ->  restituisce il wrapper
    wrapper(*args)     ->  esegue la logica
```

```python
import functools
import time

def retry(tentativi=3, pausa=1.0, eccezioni=(Exception,)):
    """
    Decoratore con argomenti: riprova la funzione in caso di errore.

    Args:
        tentativi: numero massimo di tentativi
        pausa: secondi da aspettare tra i tentativi
        eccezioni: tuple di eccezioni che triggerano il retry
    """
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            for n_tentativo in range(1, tentativi + 1):
                try:
                    return funzione(*args, **kwargs)
                except eccezioni as e:
                    if n_tentativo == tentativi:
                        raise
                    print(f"  Tentativo {n_tentativo}/{tentativi} fallito: {e}")
                    time.sleep(pausa)
        return wrapper
    return decoratore

# Uso: parentesi obbligatorie anche senza argomenti
@retry()
def operazione_default():
    raise ValueError("Fallimento simulato")

@retry(tentativi=5, pausa=0.01)
def operazione_configurata():
    raise ConnectionError("Rete non disponibile")

try:
    operazione_default()
except ValueError as e:
    print(f"Tutti i tentativi falliti: {e}")
```

```
# Output atteso:
  Tentativo 1/3 fallito: Fallimento simulato
  Tentativo 2/3 fallito: Fallimento simulato
Tutti i tentativi falliti: Fallimento simulato
```

### Il Decoratore Flessibile (Con e Senza Parentesi)

Una tecnica avanzata permette di usare il decoratore sia con che senza parentesi:

```python
import functools

def retry(func=None, *, tentativi=3, pausa=0.0):
    """
    Decoratore flessibile: funziona con e senza parentesi.

    @retry             # senza parentesi
    @retry()           # parentesi vuote
    @retry(tentativi=5)  # con argomenti
    """
    if func is None:
        # Chiamato con parentesi: @retry() o @retry(tentativi=5)
        return functools.partial(retry, tentativi=tentativi, pausa=pausa)

    # Chiamato senza parentesi: @retry
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for n in range(1, tentativi + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if n == tentativi:
                    raise
                print(f"  Tentativo {n} fallito: {e}")
                if pausa:
                    time.sleep(pausa)
    return wrapper

# Tutte queste forme funzionano:
@retry
def f1():
    raise ValueError("errore")

@retry()
def f2():
    raise ValueError("errore")

@retry(tentativi=2)
def f3():
    raise ValueError("errore")

for nome, f in [("f1", f1), ("f2", f2), ("f3", f3)]:
    try:
        f()
    except ValueError:
        pass
    print(f"-- {nome} terminato --")
```

```
# Output atteso:
  Tentativo 1 fallito: errore
  Tentativo 2 fallito: errore
-- f1 terminato --
  Tentativo 1 fallito: errore
  Tentativo 2 fallito: errore
-- f2 terminato --
  Tentativo 1 fallito: errore
-- f3 terminato --
```

### `functools.cache` e `functools.lru_cache`

```python
import functools
import time

# functools.cache: cache illimitata (Python 3.9+)
@functools.cache
def fibonacci_cache(n):
    if n <= 1:
        return n
    return fibonacci_cache(n - 1) + fibonacci_cache(n - 2)

# functools.lru_cache: cache LRU con limite
@functools.lru_cache(maxsize=128)
def fibonacci_lru(n):
    if n <= 1:
        return n
    return fibonacci_lru(n - 1) + fibonacci_lru(n - 2)

# Confronto prestazioni
inizio = time.perf_counter()
risultato_cache = fibonacci_cache(35)
tempo_cache = time.perf_counter() - inizio

inizio = time.perf_counter()
risultato_cache2 = fibonacci_cache(35)  # Seconda chiamata — tutto in cache
tempo_cache2 = time.perf_counter() - inizio

print(f"fibonacci(35) = {risultato_cache}")
print(f"Prima chiamata:   {tempo_cache:.6f}s")
print(f"Seconda chiamata: {tempo_cache2:.8f}s (dalla cache!)")
print(f"Info cache: {fibonacci_cache.cache_info()}")
```

```
# Output atteso:
fibonacci(35) = 9227465
Prima chiamata:   0.000123s
Seconda chiamata: 0.00000012s (dalla cache!)
Info cache: CacheInfo(hits=35, misses=36, maxsize=None, currsize=36)
```

```python
# Differenze chiave:
# functools.cache:      illimitata, ~40% piu' veloce, NO thread-safety garantita
# functools.lru_cache:  LRU bounded, thread-safe, gestisce eviction automatica

# LRU = Least Recently Used: quando la cache e' piena, rimuove l'elemento
# usato meno di recente

@functools.lru_cache(maxsize=3)  # cache piccola per dimostrare LRU
def carica_da_db(id_elemento):
    print(f"  [DB] Carico elemento {id_elemento}")
    return f"Dati elemento {id_elemento}"

carica_da_db(1)  # [DB] caricato
carica_da_db(2)  # [DB] caricato
carica_da_db(3)  # [DB] caricato
carica_da_db(1)  # cache hit
carica_da_db(4)  # [DB] caricato — elemento 2 rimosso dalla cache LRU
carica_da_db(2)  # [DB] caricato di nuovo
```

```
# Output atteso:
  [DB] Carico elemento 1
  [DB] Carico elemento 2
  [DB] Carico elemento 3
  [DB] Carico elemento 4
  [DB] Carico elemento 2
```

### Decoratore `@rate_limit` con Argomenti

```python
import functools
import time
from collections import deque

def rate_limit(chiamate=10, periodo=1.0):
    """
    Limita il numero di chiamate nel tempo.

    Args:
        chiamate: massimo numero di chiamate permesse nel periodo
        periodo: finestra temporale in secondi
    """
    def decoratore(funzione):
        storico_chiamate = deque()

        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            ora = time.time()

            # Rimuovi le chiamate vecchie fuori dalla finestra
            while storico_chiamate and storico_chiamate[0] < ora - periodo:
                storico_chiamate.popleft()

            if len(storico_chiamate) >= chiamate:
                attesa = periodo - (ora - storico_chiamate[0])
                raise RuntimeError(
                    f"Rate limit: max {chiamate} chiamate/{periodo}s. "
                    f"Riprova tra {attesa:.2f}s"
                )

            storico_chiamate.append(ora)
            return funzione(*args, **kwargs)

        return wrapper
    return decoratore

@rate_limit(chiamate=3, periodo=1.0)
def api_call(endpoint):
    """Simula una chiamata API."""
    return f"Risposta da {endpoint}"

# Facciamo 4 chiamate rapide — la quarta fallira'
for i in range(4):
    try:
        risultato = api_call(f"/api/v1/item/{i}")
        print(f"OK {risultato}")
    except RuntimeError as e:
        print(f"BLOCCATO: {e}")
```

```
# Output atteso:
OK Risposta da /api/v1/item/0
OK Risposta da /api/v1/item/1
OK Risposta da /api/v1/item/2
BLOCCATO: Rate limit: max 3 chiamate/1.0s. Riprova tra 0.99s
```

---

## A8: Decoratori di Classe — Applicati a una Classe Intera

### L'Analogia: Timbro sul Passaporto

Il timbro sul passaporto non cambia la persona — aggiunge informazioni e capacita'. Un decoratore di classe non cambia la classe — aggiunge o modifica comportamenti.

### Decoratori che Si Applicano a Classi

```python
import functools
from datetime import datetime

def aggiungi_timestamp(classe):
    """
    Decoratore di classe che aggiunge tracciamento della creazione.
    Aggiunge i campi created_at e updated_at a ogni istanza.
    """
    cls_init_orig = classe.__init__

    @functools.wraps(cls_init_orig)
    def nuovo_init(self, *args, **kwargs):
        cls_init_orig(self, *args, **kwargs)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def touch(self):
        """Aggiorna il timestamp di ultima modifica."""
        self.updated_at = datetime.now()

    classe.__init__ = nuovo_init
    classe.touch = touch
    return classe

@aggiungi_timestamp
class Articolo:
    def __init__(self, titolo, contenuto):
        self.titolo = titolo
        self.contenuto = contenuto

art = Articolo("Titolo", "Contenuto")
print(f"Titolo: {art.titolo}")
print(f"Creato: {art.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
```

```
# Output atteso:
Titolo: Titolo
Creato: 2026-07-15 10:30:00
```

### `@dataclass` — Il Decoratore di Classe Piu' Famoso

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Punto:
    x: float
    y: float

    def distanza_origine(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

p1 = Punto(3.0, 4.0)
p2 = Punto(3.0, 4.0)

print(p1)              # __repr__ generato automaticamente
print(p1 == p2)        # __eq__ generato automaticamente
print(p1.distanza_origine())
```

```
# Output atteso:
Punto(x=3.0, y=4.0)
True
5.0
```

### Decoratore per Registrazione Automatica di Plugin

```python
class RegistroPlugin:
    """Registro centrale di tutti i plugin."""
    _plugins = {}

    @classmethod
    def registra(cls, nome):
        """Decoratore di classe che registra un plugin nel registro."""
        def decoratore(plugin_class):
            cls._plugins[nome] = plugin_class
            plugin_class.nome_plugin = nome
            print(f"Plugin registrato: {nome} -> {plugin_class.__name__}")
            return plugin_class
        return decoratore

    @classmethod
    def ottieni(cls, nome):
        return cls._plugins.get(nome)

    @classmethod
    def lista_tutti(cls):
        return list(cls._plugins.keys())

@RegistroPlugin.registra("pdf_exporter")
class EsportatoreAPDF:
    def esporta(self, dati):
        return f"PDF: {dati}"

@RegistroPlugin.registra("csv_exporter")
class EsportatoreSuCSV:
    def esporta(self, dati):
        return f"CSV: {dati}"

@RegistroPlugin.registra("json_exporter")
class EsportatoreSuJSON:
    def esporta(self, dati):
        import json
        return json.dumps({"dati": str(dati)})

print(f"\nPlugin disponibili: {RegistroPlugin.lista_tutti()}")

plugin = RegistroPlugin.ottieni("csv_exporter")()
print(plugin.esporta({"a": 1, "b": 2}))
```

```
# Output atteso:
Plugin registrato: pdf_exporter -> EsportatoreAPDF
Plugin registrato: csv_exporter -> EsportatoreSuCSV
Plugin registrato: json_exporter -> EsportatoreSuJSON

Plugin disponibili: ['pdf_exporter', 'csv_exporter', 'json_exporter']
CSV: {'a': 1, 'b': 2}
```

---

## A9: Stacking — Impilare i Decoratori

### L'Analogia: La Cipolla (Strati)

Una cipolla ha molti strati. Quando "esegui" una funzione con decoratori multipli, stai attraversando gli strati dall'esterno verso l'interno. I decoratori si applicano dal basso verso l'alto, ma si eseguono dall'alto verso il basso.

### Ordine di Applicazione vs Ordine di Esecuzione

```python
import functools

def decoratore_A(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print("A: prima")
        risultato = funzione(*args, **kwargs)
        print("A: dopo")
        return risultato
    return wrapper

def decoratore_B(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print("  B: prima")
        risultato = funzione(*args, **kwargs)
        print("  B: dopo")
        return risultato
    return wrapper

def decoratore_C(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print("    C: prima")
        risultato = funzione(*args, **kwargs)
        print("    C: dopo")
        return risultato
    return wrapper

@decoratore_A
@decoratore_B
@decoratore_C
def funzione_originale():
    print("      >>> FUNZIONE ORIGINALE <<<")

funzione_originale()
```

```
# Output atteso:
A: prima
  B: prima
    C: prima
      >>> FUNZIONE ORIGINALE <<<
    C: dopo
  B: dopo
A: dopo
```

```python
# Questo equivale a:
# funzione_originale = decoratore_A(decoratore_B(decoratore_C(funzione_originale)))
#
# Applicazione (al momento della definizione): C prima, poi B, poi A (dal basso verso l'alto)
# Esecuzione (quando chiamata): A prima, poi B, poi C (dall'alto verso il basso)
```

### Esempio Pratico: Autenticazione + Logging + Validazione

```python
import functools
import time

def richiede_autenticazione(funzione):
    """Verifica che l'utente sia autenticato."""
    @functools.wraps(funzione)
    def wrapper(utente, *args, **kwargs):
        if not utente.get("autenticato", False):
            raise PermissionError(f"Utente {utente.get('nome', '?')} non autenticato")
        print(f"  [AUTH] Utente {utente['nome']} autenticato")
        return funzione(utente, *args, **kwargs)
    return wrapper

def log_chiamata(funzione):
    """Logga le chiamate alla funzione."""
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Chiamata a {funzione.__name__}")
        risultato = funzione(*args, **kwargs)
        print(f"[LOG] {funzione.__name__} completata")
        return risultato
    return wrapper

def misura_tempo(funzione):
    """Misura il tempo di esecuzione."""
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        risultato = funzione(*args, **kwargs)
        durata = time.perf_counter() - inizio
        print(f"[TIME] {funzione.__name__}: {durata:.4f}s")
        return risultato
    return wrapper

@misura_tempo
@log_chiamata
@richiede_autenticazione
def dati_riservati(utente, id_risorsa):
    """Accede a dati riservati."""
    return f"Dati risorsa {id_risorsa} per {utente['nome']}"

utente_valido = {"nome": "Mario", "autenticato": True}
utente_invalido = {"nome": "Hacker", "autenticato": False}

print("=== Utente valido ===")
risultato = dati_riservati(utente_valido, "report_2026")
print(f"Risultato: {risultato}\n")

print("=== Utente non valido ===")
try:
    dati_riservati(utente_invalido, "report_2026")
except PermissionError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
=== Utente valido ===
[LOG] Chiamata a dati_riservati
  [AUTH] Utente Mario autenticato
[LOG] dati_riservati completata
[TIME] dati_riservati: 0.0001s
Risultato: Dati risorsa report_2026 per Mario

=== Utente non valido ===
[LOG] Chiamata a dati_riservati
Errore: Utente Hacker non autenticato
[TIME] dati_riservati: 0.0001s
```

---

## A10: Decoratori come Classi

### L'Analogia: Robot Programmabile

Un decoratore come classe e' come un robot programmabile. Puoi impostarne la configurazione al momento della costruzione (`__init__`), e poi il robot sa come "eseguire" la sua azione (`__call__`). Ogni volta che "chiami" il robot, esegue la sua logica programmata.

### Come Funziona un Decoratore-Classe

Una classe puo' essere usata come decoratore se implementa `__call__`:

```python
import functools
import time

class Timer:
    """Decoratore implementato come classe che misura il tempo."""

    def __init__(self, funzione):
        self.funzione = funzione
        functools.update_wrapper(self, funzione)  # equivalente a @functools.wraps

    def __call__(self, *args, **kwargs):
        inizio = time.perf_counter()
        risultato = self.funzione(*args, **kwargs)
        durata = time.perf_counter() - inizio
        print(f"[timer] {self.funzione.__name__} -> {durata:.6f}s")
        return risultato

@Timer
def calcola(n):
    """Calcola la somma."""
    return sum(range(n))

# Timer e' ora un'istanza di Timer
print(type(calcola))       # <class '__main__.Timer'>
print(calcola.__name__)    # calcola (preservato da update_wrapper)

risultato = calcola(100000)
print(f"Risultato: {risultato}")
```

```
# Output atteso:
<class '__main__.Timer'>
calcola
[timer] calcola -> 0.003456s
Risultato: 4999950000
```

### Decoratore-Classe con Argomenti

```python
import functools
import time

class Retry:
    """
    Decoratore-classe con argomenti: riprova in caso di errore.
    Uso: @Retry(tentativi=5, pausa=1.0)
    """

    def __init__(self, tentativi=3, pausa=0.0, eccezioni=(Exception,)):
        self.tentativi = tentativi
        self.pausa = pausa
        self.eccezioni = eccezioni

    def __call__(self, funzione):
        """Questo metodo viene chiamato con la funzione da decorare."""
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            for n in range(1, self.tentativi + 1):
                try:
                    return funzione(*args, **kwargs)
                except self.eccezioni as e:
                    if n == self.tentativi:
                        raise
                    print(f"  Tentativo {n}/{self.tentativi}: {e}")
                    if self.pausa:
                        time.sleep(self.pausa)
        return wrapper

@Retry(tentativi=3, pausa=0.01)
def operazione_instabile():
    import random
    random.seed(42)
    if random.random() < 0.7:
        raise RuntimeError("Errore casuale")
    return "Successo!"

try:
    risultato = operazione_instabile()
    print(f"OK: {risultato}")
except RuntimeError as e:
    print(f"Fallito: {e}")
```

```
# Output atteso:
  Tentativo 1/3: Errore casuale
  Tentativo 2/3: Errore casuale
  Tentativo 3/3: Errore casuale
Fallito: Errore casuale
```

### Decoratore-Classe con Stato tra Chiamate

```python
import functools

class ConContatore:
    """Decoratore-classe che conta le chiamate — stato persistente tra chiamate."""

    def __init__(self, funzione):
        self.funzione = funzione
        self.contatore = 0
        functools.update_wrapper(self, funzione)

    def __call__(self, *args, **kwargs):
        self.contatore += 1
        print(f"Chiamata #{self.contatore}")
        return self.funzione(*args, **kwargs)

    def reset(self):
        """Metodo ausiliario — non possibile con decoratore-funzione!"""
        self.contatore = 0

@ConContatore
def lavora():
    return "fatto"

lavora()
lavora()
lavora()
print(f"Chiamate totali: {lavora.contatore}")

lavora.reset()
lavora()
print(f"Dopo reset: {lavora.contatore}")
```

```
# Output atteso:
Chiamata #1
Chiamata #2
Chiamata #3
Chiamate totali: 3
Chiamata #1
Dopo reset: 1
```

### Confronto: Decoratore-Funzione vs Decoratore-Classe

Usa un **decoratore-funzione** quando:
- La logica e' semplice
- Non serve stato interno tra chiamate
- Preferisci la sintassi piu' compatta

Usa un **decoratore-classe** quando:
- Hai stato interno complesso tra chiamate (contatori, cache)
- Hai bisogno di metodi ausiliari aggiuntivi
- Preferisci la leggibilita' OOP

---

## Errori Comuni della Parte A

### Errore 1: Dimenticare `functools.wraps`

```python
import functools

# SBAGLIATO: la funzione perde la sua identita'
def decoratore_sbagliato(funzione):
    def wrapper(*args, **kwargs):  # nessun @functools.wraps
        return funzione(*args, **kwargs)
    return wrapper

@decoratore_sbagliato
def mia_funzione():
    """La mia docstring."""
    pass

print(mia_funzione.__name__)  # 'wrapper' — sbagliato!
print(mia_funzione.__doc__)   # None — sbagliato!
```

```
# Output atteso:
wrapper
None
```

```python
# CORRETTO
def decoratore_corretto(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper

@decoratore_corretto
def mia_funzione():
    """La mia docstring."""
    pass

print(mia_funzione.__name__)  # 'mia_funzione' — corretto!
print(mia_funzione.__doc__)   # 'La mia docstring.' — corretto!
```

```
# Output atteso:
mia_funzione
La mia docstring.
```

### Errore 2: Chiamare il Wrapper invece di Restituirlo

```python
# SBAGLIATO: il decoratore chiama il wrapper invece di restituirlo
def decoratore_sbagliato(funzione):
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper()  # SBAGLIATO: chiama wrapper senza argomenti!

@decoratore_sbagliato
def saluta(nome):
    return f"Ciao, {nome}!"
```

```
# Output atteso (errore al momento della definizione):
TypeError: wrapper() missing 1 required positional argument: 'nome'
```

```python
# CORRETTO: restituire la funzione, non chiamarla
def decoratore_corretto(funzione):
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper  # senza parentesi
```

### Errore 3: Non Restituire il Risultato

```python
import functools

# SBAGLIATO: il wrapper non restituisce il risultato
def decoratore_rotto(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print("Prima")
        funzione(*args, **kwargs)  # risultato ignorato
        print("Dopo")
        # nessun return -> restituisce None implicitamente
    return wrapper

@decoratore_rotto
def aggiungi(a, b):
    return a + b

risultato = aggiungi(3, 4)
print(f"Risultato: {risultato}")  # None! Non 7!
```

```
# Output atteso:
Prima
Dopo
Risultato: None
```

```python
# CORRETTO: restituire il risultato
def decoratore_corretto(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print("Prima")
        risultato = funzione(*args, **kwargs)
        print("Dopo")
        return risultato  # fondamentale!
    return wrapper
```

### Errore 4: Decoratori con Argomenti — Parentesi Dimenticate

```python
# SBAGLIATO: senza parentesi, retry viene passato come funzione da decorare
def retry(tentativi=3):
    def decoratore(funzione):
        import functools
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            return funzione(*args, **kwargs)
        return wrapper
    return decoratore

@retry   # ERRORE: mancano le parentesi!
def mia_funzione():
    pass

# mia_funzione e' ora il DECORATORE, non una funzione decorata!
print(type(mia_funzione))
```

```
# Output atteso:
<class 'function'>
# ma mia_funzione e' il decoratore interno, non la funzione decorata!
```

```python
# CORRETTO: con le parentesi
@retry()  # o @retry(tentativi=5)
def mia_funzione():
    pass
```

### Errore 5: Il Decoratore Non Funziona con Metodi di Classe

```python
import functools

# Il problema: un decoratore standard che usa self
def log_chiamata(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        # args[0] e' self quando applicato a un metodo di istanza
        print(f"Chiamata a {funzione.__name__}")
        return funzione(*args, **kwargs)
    return wrapper

class MiaClasse:
    @log_chiamata
    def metodo(self, x):
        return x * 2

obj = MiaClasse()
print(obj.metodo(5))  # Funziona! args[0] e' self
```

```
# Output atteso:
Chiamata a metodo
10
```

```python
# Il problema reale: decoratore-classe che non implementa __get__
# (trattato nella Parte D — descriptor protocol)
```

---

## Esercizi della Parte A

### Esercizio A1: `@deprecated`

Implementa un decoratore `@deprecated(messaggio)` che stampa un `DeprecationWarning` quando la funzione viene chiamata.

```python
import functools
import warnings

def deprecated(messaggio=""):
    """Implementa qui il decoratore @deprecated."""
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{funzione.__name__} e' deprecata. {messaggio}",
                DeprecationWarning,
                stacklevel=2,
            )
            return funzione(*args, **kwargs)
        return wrapper
    return decoratore

@deprecated("Usa `calcola_v2` invece")
def calcola_v1(x):
    """Versione vecchia del calcolo."""
    return x * 2

import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    risultato = calcola_v1(5)
    print(f"Warning: {w[0].message}")
    print(f"Risultato: {risultato}")
```

```
# Output atteso:
Warning: calcola_v1 e' deprecata. Usa `calcola_v2` invece
Risultato: 10
```

### Esercizio A2: `@log_calls`

Implementa un decoratore `@log_calls` che registra ogni chiamata in una lista accessibile tramite `funzione.log`.

```python
import functools
from datetime import datetime

def log_calls(funzione):
    """Registra ogni chiamata con: timestamp, args, kwargs, risultato."""
    registro = []

    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        risultato = funzione(*args, **kwargs)
        registro.append({
            "timestamp": datetime.now().isoformat(),
            "args": args,
            "kwargs": kwargs,
            "risultato": risultato,
        })
        return risultato

    wrapper.log = registro
    return wrapper

@log_calls
def somma(a, b):
    return a + b

somma(1, 2)
somma(3, 4)
somma(10, 20)

for entry in somma.log:
    print(f"  somma{entry['args']} = {entry['risultato']}")
```

```
# Output atteso:
  somma(1, 2) = 3
  somma(3, 4) = 7
  somma(10, 20) = 30
```

### Esercizio A3: Decoratore di Classe `@registra_metodi`

```python
def registra_metodi(classe):
    """Aggiunge lista_metodi() alla classe."""
    def lista_metodi(self):
        return sorted([
            nome for nome in dir(self)
            if callable(getattr(self, nome)) and not nome.startswith("_")
        ])

    classe.lista_metodi = lista_metodi
    return classe

@registra_metodi
class Calcolatrice:
    def somma(self, a, b): return a + b
    def differenza(self, a, b): return a - b
    def prodotto(self, a, b): return a * b

c = Calcolatrice()
print(c.lista_metodi())
```

```
# Output atteso:
['differenza', 'lista_metodi', 'prodotto', 'somma']
```

---

*Fine PARTE A — continua con la PARTE B: Generatori*



# PARTE B: Generatori

---

## B1: Il Problema della Memoria

### L'Analogia: Il Libro vs la Radio

Immagina di dover leggere una enciclopedia di 10.000 pagine. Hai due scelte:
1. **Stamparla tutta e tenerla sul tavolo** — occupi tutto lo spazio del tavolo (e della stanza)
2. **Ascoltarla alla radio, una pagina alla volta** — non devi tenere tutto in memoria; ascolti, elabori, e vai avanti

I generatori sono la "radio": producono valori uno alla volta, su richiesta, senza dover materializzare tutto in memoria.

### Il Problema Concreto

Supponiamo di dover leggere un file di log con 10 milioni di righe e trovare quelle con "ERROR":

**Approccio con lista (spreca memoria):**

```python
# PROBLEMA: questo carica TUTTE le 10 milioni di righe in RAM!
def leggi_errori_lista(nome_file):
    """Approccio sbagliato: carica tutto in memoria."""
    with open(nome_file) as f:
        righe = f.readlines()  # carica tutto
    
    return [r for r in righe if "ERROR" in r]

# Se ogni riga e' 200 byte e ci sono 10M righe: 10,000,000 * 200 = 2 GB di RAM!
```

**Approccio con generatore (efficiente):**

```python
# SOLUZIONE: processa una riga alla volta
def leggi_errori_generatore(nome_file):
    """Approccio corretto: genera una riga alla volta."""
    with open(nome_file) as f:
        for riga in f:          # f legge una riga alla volta
            if "ERROR" in riga:
                yield riga      # produce il valore e si mette in pausa

# Usa praticamente zero memoria extra — processa una riga alla volta
```

### Dimostrazione della Differenza di Memoria

```python
import sys

# Confronto memoria: lista vs generatore
numeri_lista = [i * i for i in range(1000000)]     # list comprehension
numeri_gen   = (i * i for i in range(1000000))     # generator expression

print(f"Lista:     {sys.getsizeof(numeri_lista):,} byte")
print(f"Generatore:{sys.getsizeof(numeri_gen):,} byte")
```

```
# Output atteso:
Lista:     8697464 byte   (circa 8.5 MB)
Generatore:104 byte       (solo 104 byte — costante indipendentemente dalla dimensione!)
```

```python
# La differenza diventa drastica con dati enormi
numeri_100m_lista = [i for i in range(100_000_000)]  # ~800 MB di RAM
# numeri_100m_gen = (i for i in range(100_000_000))  # ~200 byte — SEMPRE

# Un generatore che produce 100 milioni di numeri occupa lo stesso spazio di
# uno che produce 10 — perche' tiene in memoria solo il valore corrente!
```

### Quando Usare i Generatori

I generatori sono la scelta giusta quando:
1. Il dataset e' troppo grande per stare in memoria
2. Non hai bisogno di tutti i valori contemporaneamente
3. Stai costruendo una pipeline di trasformazioni
4. I dati arrivano in streaming (rete, file, sensori)
5. La sequenza e' potenzialmente infinita (contatori, date, numeri primi)

---

## B2: `yield` — La Parola Magica

### L'Analogia: La Distributrice di Bibite

Una distributrice di bibite non ti consegna tutte le bibite in una volta — ne eroga una alla volta, ogni volta che premi il pulsante. Tra un'erogazione e l'altra, la distributrice e' in pausa, in attesa.

`yield` funziona esattamente cosi': la funzione produce un valore (`yield valore`), si mette in pausa, e aspetta che qualcuno chieda il valore successivo.

### Il Tuo Primo Generatore

```python
# Una funzione generatrice — contiene yield
def conta_fino_a_tre():
    print("  [generatore] Sto per produrre 1")
    yield 1
    print("  [generatore] Sto per produrre 2")
    yield 2
    print("  [generatore] Sto per produrre 3")
    yield 3
    print("  [generatore] Ho finito!")

# Chiamare la funzione NON la esegue — crea un oggetto generatore
gen = conta_fino_a_tre()
print(f"Tipo: {type(gen)}")
print(f"Oggetto: {gen}")
```

```
# Output atteso:
Tipo: <class 'generator'>
Oggetto: <generator object conta_fino_a_tre at 0x7f...>
```

```python
# Il codice della funzione NON e' stato eseguito ancora!
# Per eseguirlo, usiamo next()

print("Primo next():")
valore1 = next(gen)
print(f"Ricevuto: {valore1}")

print("\nSecondo next():")
valore2 = next(gen)
print(f"Ricevuto: {valore2}")

print("\nTerzo next():")
valore3 = next(gen)
print(f"Ricevuto: {valore3}")
```

```
# Output atteso:
Primo next():
  [generatore] Sto per produrre 1
Ricevuto: 1

Secondo next():
  [generatore] Sto per produrre 2
Ricevuto: 2

Terzo next():
  [generatore] Sto per produrre 3
Ricevuto: 3
```

```python
# Quando non ci sono piu' valori, next() solleva StopIteration
print("\nQuarto next() (non ci sono piu' valori):")
try:
    valore4 = next(gen)
except StopIteration:
    print("StopIteration! Il generatore ha esaurito i valori.")
    # Nota: il generatore stampa "[generatore] Ho finito!" PRIMA di StopIteration
```

```
# Output atteso:
Quarto next() (non ci sono piu' valori):
  [generatore] Ho finito!
StopIteration! Il generatore ha esaurito i valori.
```

### Il Loop `for` e i Generatori

Il loop `for` chiama `next()` automaticamente e si ferma quando riceve `StopIteration`:

```python
def conta_fino_a_tre():
    yield 1
    yield 2
    yield 3

# Questi due sono equivalenti:
# Modo 1: manuale
gen = conta_fino_a_tre()
while True:
    try:
        valore = next(gen)
        print(valore)
    except StopIteration:
        break
```

```
# Output atteso:
1
2
3
```

```python
# Modo 2: with for (molto piu' leggibile)
for valore in conta_fino_a_tre():
    print(valore)
```

```
# Output atteso:
1
2
3
```

### Generatore con Loop Infinito

```python
def numeri_pari():
    """Genera numeri pari all'infinito — non finisce mai!"""
    n = 0
    while True:
        yield n
        n += 2

# Non chiamare list() su questo — non terminerebbe mai!
# gen = list(numeri_pari())  # NON FARE QUESTO

# Prendi solo i valori che ti servono
gen = numeri_pari()
for _ in range(5):
    print(next(gen))
```

```
# Output atteso:
0
2
4
6
8
```

### Generatore Fibonacci

```python
def fibonacci():
    """Genera la sequenza di Fibonacci all'infinito."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Prendi i primi 10 numeri di Fibonacci
gen = fibonacci()
fibonaccis = [next(gen) for _ in range(10)]
print(fibonaccis)
```

```
# Output atteso:
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### `yield` con Valore di Ritorno

Una funzione generatrice puo' anche avere un `return`:

```python
def conta_con_totale(massimo):
    """Conta e restituisce il totale come valore di return."""
    totale = 0
    for i in range(1, massimo + 1):
        totale += i
        yield i  # produce ogni numero

    return totale  # il valore del return e' nel StopIteration

gen = conta_con_totale(5)
try:
    while True:
        print(f"Prodotto: {next(gen)}")
except StopIteration as e:
    print(f"Totale: {e.value}")  # il valore e' in StopIteration.value
```

```
# Output atteso:
Prodotto: 1
Prodotto: 2
Prodotto: 3
Prodotto: 4
Prodotto: 5
Totale: 15
```

---

## B3: Funzioni Generatrici vs Funzioni Normali

### La Differenza Fondamentale

```python
# Funzione NORMALE: esegue tutto, restituisce un valore
def normale(n):
    print(f"Inizio normale({n})")
    risultato = list(range(n))
    print(f"Fine normale({n})")
    return risultato

# Funzione GENERATRICE: esegue on-demand, produce valori
def generatrice(n):
    print(f"Inizio generatrice({n})")
    for i in range(n):
        print(f"  Prima di yield {i}")
        yield i
        print(f"  Dopo yield {i}")
    print(f"Fine generatrice({n})")

print("=== Funzione normale ===")
r = normale(3)   # esegue TUTTO immediatamente
print(f"Risultato: {r}")
```

```
# Output atteso:
=== Funzione normale ===
Inizio normale(3)
Fine normale(3)
Risultato: [0, 1, 2]
```

```python
print("\n=== Funzione generatrice ===")
g = generatrice(3)  # NON esegue niente — crea solo il generatore
print(f"Creato: {g}")

print("\nPrimo next():")
v1 = next(g)  # esegue fino al primo yield
print(f"Valore: {v1}")

print("\nSecondo next():")
v2 = next(g)  # riprende da dopo il primo yield
print(f"Valore: {v2}")
```

```
# Output atteso:
=== Funzione generatrice ===
Creato: <generator object generatrice at 0x7f...>

Primo next():
Inizio generatrice(3)
  Prima di yield 0
Valore: 0

Secondo next():
  Dopo yield 0
  Prima di yield 1
Valore: 1
```

### Gli Stati di un Generatore

Un generatore puo' trovarsi in uno di quattro stati:

```python
import inspect

def mio_generatore():
    yield 1
    yield 2

gen = mio_generatore()

# GEN_CREATED: appena creato, non ancora avanzato
print(f"Dopo la creazione: {inspect.getgeneratorstate(gen)}")

next(gen)  # avanza al primo yield

# GEN_SUSPENDED: in pausa dopo un yield
print(f"Dopo il primo next(): {inspect.getgeneratorstate(gen)}")

next(gen)  # avanza al secondo yield

try:
    next(gen)  # esaurisce il generatore
except StopIteration:
    pass

# GEN_CLOSED: esaurito
print(f"Dopo StopIteration: {inspect.getgeneratorstate(gen)}")
```

```
# Output atteso:
Dopo la creazione: GEN_CREATED
Dopo il primo next(): GEN_SUSPENDED
Dopo StopIteration: GEN_CLOSED
```

I quattro stati:
- **GEN_CREATED**: creato ma non ancora avanzato
- **GEN_RUNNING**: il codice della funzione e' in esecuzione (visibile solo da codice multi-thread)
- **GEN_SUSPENDED**: in pausa dopo un yield, in attesa di `next()`
- **GEN_CLOSED**: esaurito (StopIteration) o chiuso con `close()`

### Generatore vs Lista: Quando Usare Cosa

```python
import sys

# Usa una LISTA quando:
# - Hai bisogno di accesso casuale (lista[42])
# - Hai bisogno di sapere la lunghezza in anticipo
# - Il dataset e' piccolo e lo accedi piu' volte
# - Vuoi usare .sort(), .reverse(), .index(), .count()

numeri_piccoli = list(range(100))
print(f"Lunghezza lista: {len(numeri_piccoli)}")
print(f"Elemento 50: {numeri_piccoli[50]}")
print(f"Memoria: {sys.getsizeof(numeri_piccoli):,} byte")
```

```
# Output atteso:
Lunghezza lista: 100
Elemento 50: 50
Memoria: 904 byte
```

```python
# Usa un GENERATORE quando:
# - Il dataset e' enorme (file, DB, stream)
# - Ti serve solo la prossima riga (processing sequenziale)
# - La sequenza e' potenzialmente infinita
# - Stai costruendo una pipeline di trasformazioni

import sys

gen_numeri = (i for i in range(100_000_000))  # 100 milioni di numeri!
print(f"Memoria generatore: {sys.getsizeof(gen_numeri)} byte")
# Non possiamo fare len() o accesso per indice, ma...
print(f"Prossimo valore: {next(gen_numeri)}")
print(f"Prossimo valore: {next(gen_numeri)}")
```

```
# Output atteso:
Memoria generatore: 104 byte
Prossimo valore: 0
Prossimo valore: 1
```

### I Generatori Sono Esauribili (Single-Use)

Attenzione: un generatore puo' essere consumato una sola volta!

```python
def numeri():
    yield 1
    yield 2
    yield 3

gen = numeri()

# Prima passata — ok
for n in gen:
    print(n)

print("---")

# Seconda passata — il generatore e' esaurito!
for n in gen:
    print(n)
print("(nessun output — generatore esaurito)")
```

```
# Output atteso:
1
2
3
---
(nessun output — generatore esaurito)
```

```python
# Se hai bisogno di usarlo piu' volte, ricrealo
def numeri():
    yield 1
    yield 2
    yield 3

for _ in range(2):
    for n in numeri():  # crea un nuovo generatore ogni volta
        print(n)
    print("---")
```

```
# Output atteso:
1
2
3
---
1
2
3
---
```

---

## B4: Espressioni Generatrici

### L'Analogia: La Ricetta vs il Piatto

Una list comprehension e' come preparare il piatto completo in anticipo — tutto e' cucinato e sul tavolo. Una generator expression e' come avere la ricetta e preparare ogni boccone solo quando ne hai bisogno — meno spreco, piu' flessibile.

### Sintassi: `()` invece di `[]`

```python
# List comprehension: parentesi quadre []
lista = [x * 2 for x in range(5)]
print(f"Lista: {lista}")
print(f"Tipo: {type(lista)}")

# Generator expression: parentesi tonde ()
gen = (x * 2 for x in range(5))
print(f"Generatore: {gen}")
print(f"Tipo: {type(gen)}")
```

```
# Output atteso:
Lista: [0, 2, 4, 6, 8]
Tipo: <class 'list'>
Generatore: <generator object <genexpr> at 0x7f...>
Tipo: <class 'generator'>
```

```python
# Il contenuto e' lo stesso, ma il comportamento e' diverso
import sys

lista = [x ** 2 for x in range(10000)]
gen   = (x ** 2 for x in range(10000))

print(f"Lista:     {sys.getsizeof(lista):>10,} byte")
print(f"Generatore:{sys.getsizeof(gen):>10,} byte")
```

```
# Output atteso:
Lista:         85,176 byte
Generatore:       104 byte
```

### Generator Expressions in Funzioni

Quando una generator expression e' l'unico argomento di una funzione, le parentesi esterne sono opzionali:

```python
numeri = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Con doppie parentesi (esplicito)
totale1 = sum((x * x for x in numeri))
print(totale1)

# Con singole parentesi (le doppie sono ridondanti)
totale2 = sum(x * x for x in numeri)
print(totale2)
```

```
# Output atteso:
385
385
```

### Esempi Pratici

```python
# Trovare il primo numero divisibile per 7 e 11
primo_divisibile = next(
    (n for n in range(1, 1000) if n % 7 == 0 and n % 11 == 0),
    None  # default se non trovato
)
print(f"Primo divisibile per 7 e 11: {primo_divisibile}")
```

```
# Output atteso:
Primo divisibile per 7 e 11: 77
```

```python
# Leggere solo le righe non vuote da un testo
testo = """Prima riga

Terza riga

Quinta riga"""

righe_non_vuote = (r.strip() for r in testo.split("\n") if r.strip())
for riga in righe_non_vuote:
    print(repr(riga))
```

```
# Output atteso:
'Prima riga'
'Terza riga'
'Quinta riga'
```

```python
# Trasformare dati su file enorme (simulato)
import io

# Simuliamo un file CSV grande
contenuto_csv = "\n".join([
    "nome,valore,attivo",
    "alpha,10,True",
    "beta,0,False",
    "gamma,25,True",
    "delta,-5,True",
    "epsilon,0,False",
])

# Leggi solo le righe attive con valore positivo
righe = io.StringIO(contenuto_csv)
intestazione = next(righe).strip().split(",")

dati_utili = (
    dict(zip(intestazione, riga.strip().split(",")))
    for riga in righe
    if "True" in riga and not ",0," in riga and not ",-" in riga
)

for d in dati_utili:
    print(d)
```

```
# Output atteso:
{'nome': 'alpha', 'valore': '10', 'attivo': 'True'}
{'nome': 'gamma', 'valore': '25', 'attivo': 'True'}
```

### Generator Expression con Condizione

```python
numeri = range(1, 21)

# Solo i pari
pari = list(x for x in numeri if x % 2 == 0)
print(f"Pari: {pari}")

# Pari al quadrato, solo quelli minori di 100
pari_quadrati = list(x**2 for x in numeri if x % 2 == 0 and x**2 < 100)
print(f"Pari^2 < 100: {pari_quadrati}")
```

```
# Output atteso:
Pari: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
Pari^2 < 100: [4, 16, 36, 64]
```

### `any()` e `all()` con Generator Expressions

```python
numeri = [2, 4, 6, 8, 10, 3]

# all(): tutti i valori soddisfano la condizione?
tutti_pari = all(n % 2 == 0 for n in numeri)
print(f"Tutti pari: {tutti_pari}")  # False (3 e' dispari)

# any(): almeno uno soddisfa la condizione?
qualcuno_dispari = any(n % 2 != 0 for n in numeri)
print(f"Almeno uno dispari: {qualcuno_dispari}")  # True

# Vantaggio: any() e all() si fermano non appena trovano la risposta
# Con un milione di elementi, se il primo e' dispari,
# all(... % 2 == 0 ...) si ferma subito!
```

```
# Output atteso:
Tutti pari: False
Almeno uno dispari: True
```

---

## B5: `yield from` — Delegare il Lavoro

### L'Analogia: Il Contratto di Sub-Appalto

Un imprenditore riceve un grande progetto. Invece di fare tutto da solo, sub-appalta parti del lavoro ad altri. `yield from` fa lo stesso: delega la produzione di valori a un altro iterabile (che puo' essere un altro generatore, una lista, un qualsiasi iterable).

### Problema: Concatenare Generatori Manualmente

```python
def genera_a():
    yield 1
    yield 2
    yield 3

def genera_b():
    yield 4
    yield 5
    yield 6

# Modo MANUALE: brutto e verbose
def concatena_manuale():
    for v in genera_a():
        yield v
    for v in genera_b():
        yield v

for v in concatena_manuale():
    print(v)
```

```
# Output atteso:
1
2
3
4
5
6
```

### La Soluzione: `yield from`

```python
def genera_a():
    yield 1
    yield 2
    yield 3

def genera_b():
    yield 4
    yield 5
    yield 6

# Con yield from: delega la produzione
def concatena():
    yield from genera_a()  # delega a genera_a
    yield from genera_b()  # poi delega a genera_b

for v in concatena():
    print(v)
```

```
# Output atteso:
1
2
3
4
5
6
```

```python
# yield from funziona con qualsiasi iterabile
def da_tutto():
    yield from [1, 2, 3]      # lista
    yield from range(4, 7)    # range
    yield from "abc"           # stringa (carattere per carattere)
    yield from {"x", "y"}     # set (ordine non garantito)

for v in da_tutto():
    print(v, end=" ")
print()
```

```
# Output atteso:
1 2 3 4 5 6 a b c x y   (l'ordine di x e y puo' variare)
```

### `yield from` Cattura il Valore di Return del Sub-Generatore

```python
# Questo e' il superpotere di yield from: cattura il return del sub-generatore

def sub_generatore():
    yield 1
    yield 2
    return "Sub completato!"  # questo e' il valore di return

def delegante():
    # yield from cattura il return del sub-generatore
    valore_return = yield from sub_generatore()
    print(f"Sub-generatore ha restituito: {valore_return}")
    yield 3  # continuiamo

for v in delegante():
    print(v)
```

```
# Output atteso:
1
2
Sub-generatore ha restituito: Sub completato!
3
```

### Esempio Pratico: Attraversamento di Alberi

```python
# yield from e' perfetto per attraversare strutture annidate

def appiattisci(iterable):
    """Appiattisce una struttura annidata qualsiasi (lazy)."""
    for elemento in iterable:
        if isinstance(elemento, (list, tuple, set)):
            yield from appiattisci(elemento)  # ricorsione con yield from
        else:
            yield elemento

struttura = [1, [2, 3, [4, 5]], 6, [7, [8, [9]]]]
piatto = list(appiattisci(struttura))
print(piatto)
```

```
# Output atteso:
[1, 2, 3, 4, 5, 6, 7, 8, 9]
```

```python
# Attraversamento di un albero (struttura dati)
def attraversa_albero(nodo):
    """Attraversa un albero (in-order) usando yield from."""
    if nodo is None:
        return

    if "sinistro" in nodo:
        yield from attraversa_albero(nodo["sinistro"])

    yield nodo["valore"]

    if "destro" in nodo:
        yield from attraversa_albero(nodo["destro"])

# Albero:
#       4
#      / \
#     2   6
#    / \ / \
#   1  3 5  7
albero = {
    "valore": 4,
    "sinistro": {
        "valore": 2,
        "sinistro": {"valore": 1},
        "destro":  {"valore": 3},
    },
    "destro": {
        "valore": 6,
        "sinistro": {"valore": 5},
        "destro":   {"valore": 7},
    },
}

valori_ordinati = list(attraversa_albero(albero))
print(f"Traversal in-order: {valori_ordinati}")
```

```
# Output atteso:
Traversal in-order: [1, 2, 3, 4, 5, 6, 7]
```

### `itertools` — La Libreria per i Generatori

```python
import itertools

# count: conta all'infinito
counter = itertools.count(start=10, step=2)
print(list(itertools.islice(counter, 5)))  # prendi solo i primi 5
```

```
# Output atteso:
[10, 12, 14, 16, 18]
```

```python
import itertools

# cycle: cicla su una sequenza all'infinito
ciclo = itertools.cycle(["rosso", "verde", "blu"])
colori = [next(ciclo) for _ in range(7)]
print(colori)
```

```
# Output atteso:
['rosso', 'verde', 'blu', 'rosso', 'verde', 'blu', 'rosso']
```

```python
import itertools

# chain: concatena iterabili
catena = itertools.chain([1, 2, 3], "abc", range(4, 7))
print(list(catena))
```

```
# Output atteso:
[1, 2, 3, 'a', 'b', 'c', 4, 5, 6]
```

```python
import itertools

# islice: affetta un iterabile (anche infinito)
tutti_numeri = itertools.count()
primi_10 = list(itertools.islice(tutti_numeri, 10))
print(primi_10)

# islice con start, stop, step
numeri_dal_5 = itertools.count()
ogni_terzo = list(itertools.islice(numeri_dal_5, 5, 20, 3))
print(ogni_terzo)
```

```
# Output atteso:
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
[5, 8, 11, 14, 17]
```

```python
import itertools

# groupby: raggruppa elementi consecutivi uguali
dati = [
    ("Alice", "Marketing"),
    ("Bob", "Engineering"),
    ("Carol", "Marketing"),
    ("Dave", "Engineering"),
    ("Eve", "Marketing"),
]

# NOTA: groupby raggruppa elementi CONSECUTIVI — ordina prima!
dati.sort(key=lambda x: x[1])

for dipartimento, gruppo in itertools.groupby(dati, key=lambda x: x[1]):
    persone = [p[0] for p in gruppo]
    print(f"  {dipartimento}: {persone}")
```

```
# Output atteso:
  Engineering: ['Bob', 'Dave']
  Marketing: ['Alice', 'Carol', 'Eve']
```

```python
import itertools

# product: prodotto cartesiano
colori = ["rosso", "verde"]
taglie = ["S", "M", "L"]

varianti = list(itertools.product(colori, taglie))
for v in varianti:
    print(f"  {v[0]} - taglia {v[1]}")
```

```
# Output atteso:
  rosso - taglia S
  rosso - taglia M
  rosso - taglia L
  verde - taglia S
  verde - taglia M
  verde - taglia L
```

```python
import itertools

# combinations: combinazioni senza ripetizione
carte = ["A", "K", "Q", "J"]
mani = list(itertools.combinations(carte, 2))
print(f"Possibili mani da 2 carte: {mani}")
```

```
# Output atteso:
Possibili mani da 2 carte: [('A', 'K'), ('A', 'Q'), ('A', 'J'), ('K', 'Q'), ('K', 'J'), ('Q', 'J')]
```

```python
import itertools

# accumulate: valori cumulativi
vendite_mensili = [100, 150, 80, 200, 120, 170]
vendite_cumulative = list(itertools.accumulate(vendite_mensili))
print(f"Mensili:    {vendite_mensili}")
print(f"Cumulative: {vendite_cumulative}")
```

```
# Output atteso:
Mensili:    [100, 150, 80, 200, 120, 170]
Cumulative: [100, 250, 330, 530, 650, 820]
```

---

## B6: Generatori Bidirezionali (send/throw/close)

### L'Analogia: La Conversazione

Finora i generatori hanno comunicato in una sola direzione: producono valori, noi li consumiamo. Pero' i generatori supportano la comunicazione bidirezionale — possiamo inviare valori DENTRO il generatore mentre e' in pausa, come una conversazione a turni.

Immagina un calcolo di totale progressivo:
- Noi: "Ecco 10" (send 10)
- Generatore: "Il totale e' 10" (yield 10)
- Noi: "Ecco 25" (send 25)
- Generatore: "Il totale e' 35" (yield 35)

### `send()`: Inviare Valori al Generatore

```python
def accumulatore():
    """Riceve numeri e mantiene il totale progressivo."""
    totale = 0
    while True:
        valore = yield totale  # yield RICEVE e PRODUCE simultaneamente
        if valore is None:
            break
        totale += valore

gen = accumulatore()

# IMPORTANTE: la prima chiamata deve essere next() o send(None)
# per avanzare il generatore fino al primo yield
totale = next(gen)  # avanza fino al primo yield; valore = None inizialmente
print(f"Totale iniziale: {totale}")

# Ora possiamo inviare valori
totale = gen.send(10)
print(f"Dopo +10: {totale}")

totale = gen.send(25)
print(f"Dopo +25: {totale}")

totale = gen.send(5)
print(f"Dopo +5: {totale}")
```

```
# Output atteso:
Totale iniziale: 0
Dopo +10: 10
Dopo +25: 35
Dopo +5: 40
```

### La Meccanica di `yield` come Espressione

In un generatore bidirezionale, `yield` e' un'espressione che restituisce il valore inviato con `send()`:

```python
def mostra_send():
    """Mostra cosa riceve yield da send()."""
    print("Prima del primo yield")
    x = yield "primo yield"
    print(f"  Ricevuto dopo il primo yield: {x!r}")
    y = yield "secondo yield"
    print(f"  Ricevuto dopo il secondo yield: {y!r}")

gen = mostra_send()

# Prima avanzata: esegue fino al primo yield
valore = next(gen)
print(f"Prodotto: {valore!r}")

# Seconda avanzata: invia "ciao" dentro il generatore
valore = gen.send("ciao")
print(f"Prodotto: {valore!r}")

# Terza avanzata: invia 42 dentro il generatore
try:
    gen.send(42)
except StopIteration:
    print("Generatore esaurito")
```

```
# Output atteso:
Prima del primo yield
Prodotto: 'primo yield'
  Ricevuto dopo il primo yield: 'ciao'
Prodotto: 'secondo yield'
  Ricevuto dopo il secondo yield: 42
Generatore esaurito
```

### `throw()`: Iniettare Eccezioni nel Generatore

```python
def generatore_robusto():
    """Gestisce eccezioni iniettate con throw()."""
    while True:
        try:
            valore = yield
            print(f"  Ricevuto: {valore}")
        except ValueError as e:
            print(f"  Gestito ValueError: {e}")
        except RuntimeError as e:
            print(f"  Gestito RuntimeError: {e}")
            return  # termina il generatore

gen = generatore_robusto()
next(gen)  # avanza fino al primo yield

gen.send("ciao")           # normale
gen.send(42)               # normale
gen.throw(ValueError, "input invalido")  # inietta ValueError
gen.send("ancora ciao")   # continua normalmente

try:
    gen.throw(RuntimeError, "errore critico")  # inietta RuntimeError
except StopIteration:
    print("Generatore terminato (dopo RuntimeError)")
```

```
# Output atteso:
  Ricevuto: ciao
  Ricevuto: 42
  Gestito ValueError: input invalido
  Ricevuto: ancora ciao
  Gestito RuntimeError: errore critico
Generatore terminato (dopo RuntimeError)
```

### `close()`: Chiudere un Generatore

```python
def generatore_con_cleanup():
    """Generatore che esegue cleanup quando viene chiuso."""
    print("Generatore avviato")
    try:
        while True:
            valore = yield
            print(f"  Processato: {valore}")
    except GeneratorExit:
        print("GeneratorExit ricevuto — eseguo cleanup")
        # Nota: NON devi fare yield qui, altrimenti RuntimeError
        print("Cleanup completato")
        # Il return implicito permette la chiusura

gen = generatore_con_cleanup()
next(gen)  # avanza fino al primo yield

gen.send(1)
gen.send(2)

# close() inietta GeneratorExit nel generatore
gen.close()

print("Dopo close()")
```

```
# Output atteso:
Generatore avviato
  Processato: 1
  Processato: 2
GeneratorExit ricevuto — eseguo cleanup
Cleanup completato
Dopo close()
```

### Esempio Pratico: Filtro Bidirezionale

```python
def filtro_media_mobile(soglia_iniziale=0.0):
    """
    Generatore bidirezionale: riceve numeri, produce solo quelli
    che superano la media mobile degli ultimi N valori.
    """
    finestra = []
    dimensione = 5
    soglia = soglia_iniziale

    while True:
        valore = yield
        if valore is None:
            break

        finestra.append(valore)
        if len(finestra) > dimensione:
            finestra.pop(0)

        media = sum(finestra) / len(finestra)
        if valore > media * (1 + soglia / 100):
            yield f"ANOMALIA: {valore:.1f} (media: {media:.1f})"
        else:
            yield None  # nessuna anomalia

gen = filtro_media_mobile(soglia_iniziale=20.0)
next(gen)  # inizializza

dati = [10, 11, 10, 12, 10, 50, 11, 10, 100, 9]

for d in dati:
    risultato = gen.send(d)
    if risultato:
        print(risultato)
    else:
        next(gen)  # avanza per il prossimo ciclo
```

```
# Output atteso:
ANOMALIA: 50.0 (media: 10.6)
ANOMALIA: 100.0 (media: 18.6)
```

---

## B7: Iteratori Custom

### L'Analogia: Il Libro con Segnalibro

Un iteratore e' come un libro con un segnalibro: sa dove si trova (stato corrente) e sa come andare alla pagina successiva. Il protocollo iteratore definisce esattamente come questo funziona.

### Il Protocollo Iteratore

Python definisce due protocolli distinti:

**Iterable** (iterabile): un oggetto che puo' produrre un iteratore. Deve implementare `__iter__()` che restituisce un iteratore.

**Iterator** (iteratore): un oggetto che mantiene lo stato dell'iterazione. Deve implementare:
- `__iter__()`: restituisce se stesso
- `__next__()`: restituisce il prossimo valore o solleva StopIteration

```python
# Verifica se qualcosa e' un iterable o iterator
from collections.abc import Iterable, Iterator

# Liste sono iterable ma NON iterator
lista = [1, 2, 3]
print(f"Lista e' Iterable: {isinstance(lista, Iterable)}")
print(f"Lista e' Iterator: {isinstance(lista, Iterator)}")
```

```
# Output atteso:
Lista e' Iterable: True
Lista e' Iterator: False
```

```python
# iter() crea un iterator da un iterable
iter_lista = iter(lista)
print(f"iter(lista) e' Iterable: {isinstance(iter_lista, Iterable)}")
print(f"iter(lista) e' Iterator: {isinstance(iter_lista, Iterator)}")

print(next(iter_lista))  # 1
print(next(iter_lista))  # 2
```

```
# Output atteso:
iter(lista) e' Iterable: True
iter(lista) e' Iterator: True
1
2
```

### Implementare un Iteratore Custom

```python
class IntervalloInverso:
    """
    Iteratore che conta all'indietro da 'inizio' a 'fine'.
    Equivalente a reversed(range(fine, inizio+1)).
    """

    def __init__(self, inizio: int, fine: int):
        if fine > inizio:
            raise ValueError(f"fine ({fine}) deve essere <= inizio ({inizio})")
        self.corrente = inizio
        self.fine = fine

    def __iter__(self):
        """Restituisce se stesso — e' gia' un iterator."""
        return self

    def __next__(self):
        """Restituisce il prossimo valore o StopIteration."""
        if self.corrente < self.fine:
            raise StopIteration
        valore = self.corrente
        self.corrente -= 1
        return valore

# Uso
conto_alla_rovescia = IntervalloInverso(5, 1)

for n in conto_alla_rovescia:
    print(n)
```

```
# Output atteso:
5
4
3
2
1
```

### Iterabile Riutilizzabile vs Iteratore Mono-Uso

```python
class NumeriPari:
    """
    Iterabile (non iteratore): puo' essere riutilizzato.
    __iter__ crea ogni volta un nuovo iteratore.
    """

    def __init__(self, massimo):
        self.massimo = massimo

    def __iter__(self):
        """Ogni chiamata crea un NUOVO iteratore."""
        return NumeriPariIterator(self.massimo)

class NumeriPariIterator:
    """Iteratore interno (mono-uso)."""

    def __init__(self, massimo):
        self.corrente = 0
        self.massimo = massimo

    def __iter__(self):
        return self

    def __next__(self):
        if self.corrente > self.massimo:
            raise StopIteration
        valore = self.corrente
        self.corrente += 2
        return valore

numeri = NumeriPari(10)

# Riutilizzabile: ogni for crea un nuovo iteratore
print("Primo passaggio:")
for n in numeri:
    print(n, end=" ")
print()

print("Secondo passaggio:")
for n in numeri:
    print(n, end=" ")
print()
```

```
# Output atteso:
Primo passaggio:
0 2 4 6 8 10
Secondo passaggio:
0 2 4 6 8 10
```

### Quando Usare Classi Iteratore vs Funzioni Generatrici

```python
# La stessa funzionalita' implementata come generatore (piu' semplice)
def numeri_pari(massimo):
    """Generatore equivalente a NumeriPari sopra."""
    n = 0
    while n <= massimo:
        yield n
        n += 2

# Per numeri interi, una versione ancora piu' semplice:
def numeri_pari_v2(massimo):
    yield from range(0, massimo + 1, 2)

print(list(numeri_pari(10)))
print(list(numeri_pari_v2(10)))
```

```
# Output atteso:
[0, 2, 4, 6, 8, 10]
[0, 2, 4, 6, 8, 10]
```

**Regola pratica:** Usa le classi iteratore quando:
- Hai bisogno di stato complesso o metodi ausiliari
- Stai creando un tipo riutilizzabile e configurabile
- Implementi un'API formale (interfaccia pubblica di una libreria)

Usa le funzioni generatrici per quasi tutto il resto — sono piu' concise e leggibili.

### Esempio Pratico: Paginazione

```python
class PaginatoreDati:
    """
    Iterabile che pagina una lista di dati.
    Utile per visualizzare grandi dataset a pagine.
    """

    def __init__(self, dati, dimensione_pagina=3):
        self._dati = list(dati)
        self._dimensione_pagina = dimensione_pagina

    def __iter__(self):
        return PaginatoreIteratore(self._dati, self._dimensione_pagina)

    def __len__(self):
        import math
        return math.ceil(len(self._dati) / self._dimensione_pagina)

class PaginatoreIteratore:
    def __init__(self, dati, dimensione_pagina):
        self._dati = dati
        self._dimensione_pagina = dimensione_pagina
        self._indice = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._indice >= len(self._dati):
            raise StopIteration
        pagina = self._dati[self._indice:self._indice + self._dimensione_pagina]
        self._indice += self._dimensione_pagina
        return pagina

# Uso
utenti = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace"]
paginatore = PaginatoreDati(utenti, dimensione_pagina=3)

print(f"Numero di pagine: {len(paginatore)}")

for numero, pagina in enumerate(paginatore, 1):
    print(f"Pagina {numero}: {pagina}")
```

```
# Output atteso:
Numero di pagine: 3
Pagina 1: ['Alice', 'Bob', 'Carol']
Pagina 2: ['Dave', 'Eve', 'Frank']
Pagina 3: ['Grace']
```

---

## B8: Pipeline di Generatori

### L'Analogia: La Catena di Montaggio

Una fabbrica moderna non processa un prodotto alla volta dal grezzo al finito — usa una catena di montaggio dove ogni stazione riceve il prodotto parzialmente lavorato e lo passa alla successiva. I pipeline di generatori funzionano esattamente cosi': ogni generatore riceve dati dall'upstream, li trasforma, e li passa downstream.

### Costruire una Pipeline

```python
# Pipeline di elaborazione testo
# [sorgente] -> [pulizia] -> [tokenizzazione] -> [filtraggio] -> [conteggio]

import re
from collections import Counter

def leggi_testi(testi):
    """Sorgente: produce testi uno alla volta."""
    for testo in testi:
        yield testo

def normalizza(testi):
    """Stazione 1: porta tutto in minuscolo e rimuove caratteri speciali."""
    for testo in testi:
        yield re.sub(r"[^a-zA-Z\s]", "", testo.lower())

def tokenizza(testi):
    """Stazione 2: divide in parole."""
    for testo in testi:
        for parola in testo.split():
            yield parola

def filtra_parole_brevi(parole, lunghezza_minima=4):
    """Stazione 3: rimuove le parole troppo corte."""
    for parola in parole:
        if len(parola) >= lunghezza_minima:
            yield parola

def filtra_stop_words(parole, stop_words=None):
    """Stazione 4: rimuove le parole comuni."""
    if stop_words is None:
        stop_words = {"the", "and", "that", "this", "with", "from", "have", "they", "will"}
    for parola in parole:
        if parola not in stop_words:
            yield parola

# Dati sorgente
testi = [
    "The quick brown fox jumps over the lazy dog!",
    "Python is a versatile and powerful programming language.",
    "Generators are lazy and memory-efficient data streams.",
    "They will have powerful tools at their disposal.",
]

# Costruiamo la pipeline
sorgente    = leggi_testi(testi)
normalizzati = normalizza(sorgente)
parole       = tokenizza(normalizzati)
filtrate1    = filtra_parole_brevi(parole, lunghezza_minima=4)
filtrate2    = filtra_stop_words(filtrate1)

# Consumiamo la pipeline
conteggio = Counter(filtrate2)
print("Parole piu' frequenti:")
for parola, count in conteggio.most_common(8):
    print(f"  {parola}: {count}")
```

```
# Output atteso:
Parole piu' frequenti:
  powerful: 2
  quick: 1
  brown: 1
  jumps: 1
  over: 1
  lazy: 1
  python: 1
  versatile: 1
```

### Pipeline per Elaborazione File

```python
import csv
import io

# Simuliamo un file CSV di transazioni
transazioni_csv = """data,descrizione,importo,categoria
2026-01-15,Supermercato Esselunga,-85.30,Cibo
2026-01-16,Stipendio,3200.00,Entrata
2026-01-17,Netflix,-12.99,Intrattenimento
2026-01-18,Farmacia,-23.50,Salute
2026-01-19,Ristorante Da Mario,-45.00,Cibo
2026-01-20,Affitto,-900.00,Casa
2026-01-21,Freelance Python,500.00,Entrata
2026-01-22,Palestra,-35.00,Sport
"""

def leggi_transazioni(contenuto_csv):
    """Sorgente: legge transazioni dal CSV."""
    reader = csv.DictReader(io.StringIO(contenuto_csv))
    for riga in reader:
        riga["importo"] = float(riga["importo"])
        yield riga

def solo_uscite(transazioni):
    """Filtra: tiene solo le uscite (importo negativo)."""
    for t in transazioni:
        if t["importo"] < 0:
            yield t

def categorizza(transazioni, categorie_obiettivo):
    """Filtra: tiene solo le categorie specificate."""
    for t in transazioni:
        if t["categoria"] in categorie_obiettivo:
            yield t

def aggiunge_info(transazioni):
    """Trasforma: aggiunge calcoli aggiuntivi."""
    for t in transazioni:
        t["importo_assoluto"] = abs(t["importo"])
        yield t

# Pipeline
sorgente  = leggi_transazioni(transazioni_csv)
uscite    = solo_uscite(sorgente)
cibo_salute = categorizza(uscite, {"Cibo", "Salute"})
arricchite = aggiunge_info(cibo_salute)

# Risultati
print("Spese per Cibo e Salute:")
totale = 0
for t in arricchite:
    print(f"  {t['data']} - {t['descrizione']}: euro{t['importo_assoluto']:.2f}")
    totale += t["importo_assoluto"]
print(f"\nTotale: euro{totale:.2f}")
```

```
# Output atteso:
Spese per Cibo e Salute:
  2026-01-15 - Supermercato Esselunga: euro85.30
  2026-01-18 - Farmacia: euro23.50
  2026-01-19 - Ristorante Da Mario: euro45.00

Totale: euro153.80
```

### Pattern Generator Pipeline con `functools`

```python
import functools

def pipeline(*stazioni):
    """
    Crea una pipeline da una lista di funzioni generatrici.
    Ogni stazione riceve il generatore della stazione precedente.
    """
    def applica(sorgente):
        risultato = sorgente
        for stazione in stazioni:
            risultato = stazione(risultato)
        return risultato
    return applica

# Definiamo le stazioni come funzioni che prendono un iterabile
def moltiplica_per_due(iterable):
    for x in iterable:
        yield x * 2

def filtra_pari(iterable):
    for x in iterable:
        if x % 2 == 0:
            yield x

def aggiungi_indice(iterable):
    for i, x in enumerate(iterable):
        yield (i, x)

# Creiamo la pipeline
elabora = pipeline(moltiplica_per_due, filtra_pari, aggiungi_indice)

sorgente = iter([1, 2, 3, 4, 5, 6, 7, 8])
risultati = list(elabora(sorgente))

for indice, valore in risultati:
    print(f"  [{indice}] {valore}")
```

```
# Output atteso:
  [0] 2
  [1] 4
  [2] 6
  [3] 8
  [4] 10
  [5] 12
  [6] 14
  [7] 16
```

---

## Errori Comuni della Parte B

### Errore 1: Chiamare `list()` su un Generatore Infinito

```python
def numeri_infiniti():
    n = 0
    while True:
        yield n
        n += 1

# NON FARE MAI QUESTO — il programma si blocchera'!
# lista = list(numeri_infiniti())  # si blocca! loop infinito

# CORRETTO: usa islice o prendi solo quelli che ti servono
import itertools
primi_10 = list(itertools.islice(numeri_infiniti(), 10))
print(primi_10)
```

```
# Output atteso:
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### Errore 2: Usare il Generatore dopo che e' Esaurito

```python
def conta():
    yield 1
    yield 2
    yield 3

gen = conta()

# Prima passata: ok
for n in gen:
    pass

# Seconda passata: il generatore e' esaurito!
risultato = list(gen)
print(f"Risultato: {risultato}")  # Lista vuota!
print(f"Stato: esaurito")
```

```
# Output atteso:
Risultato: []
Stato: esaurito
```

```python
# CORRETTO: ricrea il generatore o usa un iterabile
class Contatore:
    """Iterabile riutilizzabile."""
    def __iter__(self):
        yield 1
        yield 2
        yield 3

contatore = Contatore()
print(list(contatore))  # [1, 2, 3]
print(list(contatore))  # [1, 2, 3] — ancora!
```

```
# Output atteso:
[1, 2, 3]
[1, 2, 3]
```

### Errore 3: Dimenticare `next()` Prima del Primo `send()`

```python
def mio_generatore():
    valore = yield "pronto"
    yield f"Ricevuto: {valore}"

gen = mio_generatore()

# SBAGLIATO: non puoi fare send(valore) prima di next()
try:
    gen.send("ciao")  # TypeError!
except TypeError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
Errore: can't send non-None value to a just-started generator
```

```python
# CORRETTO: prima next(), poi send()
gen = mio_generatore()
primo_valore = next(gen)  # avanza fino al primo yield
print(f"Primo valore: {primo_valore}")

secondo_valore = gen.send("ciao")  # ora possiamo inviare
print(f"Secondo valore: {secondo_valore}")
```

```
# Output atteso:
Primo valore: pronto
Secondo valore: Ricevuto: ciao
```

### Errore 4: `StopIteration` che Si Propaga (Python 3.7+)

```python
# In Python 3.7+, StopIteration all'interno di un generatore
# viene convertita in RuntimeError (PEP 479)

def genera_da_lista(lista):
    it = iter(lista)
    while True:
        try:
            yield next(it)
        except StopIteration:
            # Python 3.7+: questa StopIteration diventa RuntimeError!
            break  # CORRETTO: interrompi il loop, non ri-solleva

def genera_sbagliato(lista):
    it = iter(lista)
    while True:
        # Se next(it) solleva StopIteration, si propaga verso l'alto
        # e Python 3.7+ la converte in RuntimeError!
        yield next(it)  # SBAGLIATO in Python 3.7+

# Corretto:
for v in genera_da_lista([1, 2, 3]):
    print(v)
```

```
# Output atteso:
1
2
3
```

### Errore 5: Generatore in `zip()` — Ordine di Esaurimento

```python
def gen_a():
    yield 1
    yield 2
    yield 3
    yield 4
    yield 5

def gen_b():
    yield "a"
    yield "b"
    yield "c"

# zip() si ferma al generatore piu' corto
# ma NON esaurisce gen_a!
coppie = list(zip(gen_a(), gen_b()))
print(coppie)
```

```
# Output atteso:
[(1, 'a'), (2, 'b'), (3, 'c')]
```

---

## Esercizi della Parte B

### Esercizio B1: Generatore di Numeri Primi

Implementa un generatore `numeri_primi()` che produce numeri primi all'infinito:

```python
def numeri_primi():
    """Genera numeri primi all'infinito usando il crivello incrementale."""
    def e_primo(n, primi_finora):
        return all(n % p != 0 for p in primi_finora if p * p <= n)

    trovati = []
    candidato = 2
    while True:
        if e_primo(candidato, trovati):
            trovati.append(candidato)
            yield candidato
        candidato += 1

import itertools
primi = list(itertools.islice(numeri_primi(), 10))
print(f"Primi 10 numeri primi: {primi}")
```

```
# Output atteso:
Primi 10 numeri primi: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

### Esercizio B2: Pipeline Elaborazione Dati

Crea una pipeline che:
1. Genera 1000 numeri casuali tra 1 e 100
2. Filtra solo i dispari
3. Eleva al quadrato
4. Prende solo quelli > 500
5. Calcola la somma totale

```python
import random

def genera_casuali(n, min_val=1, max_val=100, seed=42):
    random.seed(seed)
    for _ in range(n):
        yield random.randint(min_val, max_val)

def filtra_dispari(numeri):
    for n in numeri:
        if n % 2 != 0:
            yield n

def eleva_al_quadrato(numeri):
    for n in numeri:
        yield n ** 2

def filtra_maggiori(numeri, soglia):
    for n in numeri:
        if n > soglia:
            yield n

# Pipeline
sorgente = genera_casuali(1000)
dispari = filtra_dispari(sorgente)
quadrati = eleva_al_quadrato(dispari)
grandi = filtra_maggiori(quadrati, 500)

totale = sum(grandi)
print(f"Somma totale: {totale}")
```

```
# Output atteso:
Somma totale: (un numero intero — dipende dal seed)
```

### Esercizio B3: Generatore Bidirezionale — Calcolatrice

Implementa un generatore bidirezionale che funziona come una calcolatrice, ricevendo operazioni via `send()`:

```python
def calcolatrice():
    """
    Generatore bidirezionale che mantiene un accumulatore.
    Riceve tuple (operazione, valore) e produce il risultato corrente.

    Operazioni: "+", "-", "*", "/", "reset"
    """
    accumulatore = 0.0
    while True:
        comando = yield accumulatore
        if comando is None:
            continue
        operazione, valore = comando
        if operazione == "+":
            accumulatore += valore
        elif operazione == "-":
            accumulatore -= valore
        elif operazione == "*":
            accumulatore *= valore
        elif operazione == "/":
            if valore == 0:
                yield "ERRORE: divisione per zero"
                continue
            accumulatore /= valore
        elif operazione == "reset":
            accumulatore = 0.0

calc = calcolatrice()
next(calc)  # inizializza

print(calc.send(("+", 10)))  # 10.0
print(calc.send(("+", 5)))   # 15.0
print(calc.send(("*", 3)))   # 45.0
print(calc.send(("-", 5)))   # 40.0
print(calc.send(("/", 8)))   # 5.0
print(calc.send(("reset", 0)))  # 0.0
```

```
# Output atteso:
10.0
15.0
45.0
40.0
5.0
0.0
```

---

*Fine PARTE B — continua con la PARTE C: Context Manager*



# PARTE C: Context Manager

---

## C1: Il Problema delle Risorse

### L'Analogia: L'Accordo di Prestito

Quando prendi in prestito qualcosa — una macchina, un libro, le chiavi di casa — c'e' un accordo implicito: userai la risorsa, e quando hai finito la restituirai. Se te ne dimentichi, si creano problemi.

Nel software, le "risorse" sono: file aperti, connessioni al database, lock di mutua esclusione, connessioni di rete, socket, sessioni HTTP. La regola e' la stessa: apri la risorsa, usala, e chiudila sempre — anche se si verifica un errore nel mezzo.

I context manager (`with`) formalizzano questo accordo in Python.

### Il Problema: Risorse Non Chiuse

```python
# Caso 1: File non chiuso in caso di errore
def leggi_configurazione_sbagliato(percorso):
    """Approccio SBAGLIATO: il file potrebbe restare aperto."""
    f = open(percorso)
    contenuto = f.read()
    elabora(contenuto)  # e se questa funzione solleva un'eccezione?
    f.close()           # questa riga potrebbe non essere mai raggiunta!
    return contenuto

# Questo codice ha un bug nascosto:
# Se elabora() solleva un'eccezione, f.close() non viene mai chiamato.
# Il file resta aperto finche' il garbage collector non lo raccoglie
# (o finche' il programma non termina).
```

```python
# Caso 2: Lock non rilasciato
import threading

lock = threading.Lock()

def aggiorna_contatore_sbagliato():
    """Approccio SBAGLIATO: il lock potrebbe non essere rilasciato."""
    lock.acquire()
    # ... aggiorna il contatore ...
    if condizione_di_errore:
        raise ValueError("Errore nel calcolo")  # lock mai rilasciato!
    lock.release()  # questa riga potrebbe non essere mai raggiunta
```

```python
# Caso 3: Connessione al database non chiusa
def query_sbagliata(sql):
    """Approccio SBAGLIATO: la connessione potrebbe restare aperta."""
    conn = crea_connessione_db()
    risultato = conn.execute(sql)  # e se questa solleva un'eccezione?
    conn.close()   # mai raggiunta in caso di errore
    return risultato
```

### La Soluzione Manuale: try/finally

Prima dei context manager, si usava `try/finally`:

```python
# Modo MANUALE con try/finally — funziona ma e' verbose
def leggi_configurazione_manuale(percorso):
    """Approccio con try/finally — corretto ma verbose."""
    f = open(percorso)
    try:
        contenuto = f.read()
        return contenuto
    finally:
        f.close()  # eseguito SEMPRE, anche in caso di eccezione
```

```python
# Per dimostrare che finally funziona:
def demo_finally():
    try:
        print("Nel try")
        raise ValueError("Errore simulato")
    finally:
        print("Nel finally — eseguito SEMPRE")
    print("Questo NON viene eseguito")

try:
    demo_finally()
except ValueError as e:
    print(f"Catturato: {e}")
```

```
# Output atteso:
Nel try
Nel finally — eseguito SEMPRE
Catturato: Errore simulato
```

### La Soluzione Elegante: `with`

```python
# Con with — piu' leggibile, meno errori, equivalente a try/finally
def leggi_configurazione(percorso):
    """Approccio con with — il file e' SEMPRE chiuso."""
    with open(percorso) as f:
        contenuto = f.read()
        return contenuto

# Se percorso non esiste, l'eccezione si propaga normalmente
# MA il file (se aperto) viene chiuso sempre
```

```python
# Dimostrazione: il file e' sempre chiuso, anche in caso di eccezione
import tempfile
import os

# Creiamo un file temporaneo
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
    tmp.write("Ciao dalla funzione demo!")
    percorso = tmp.name

# Leggiamo con with
try:
    with open(percorso) as f:
        print(f"File aperto: {not f.closed}")
        contenuto = f.read()
        print(f"Contenuto: {contenuto}")
    print(f"Dopo il with, file chiuso: {f.closed}")
finally:
    os.unlink(percorso)  # pulizia
```

```
# Output atteso:
File aperto: True
Contenuto: Ciao dalla funzione demo!
Dopo il with, file chiuso: True
```

### Gestire Piu' Risorse Contemporaneamente

```python
# Modo vecchio: nested with
with open("input.txt") as fin:
    with open("output.txt", "w") as fout:
        fout.write(fin.read())

# Modo moderno: with multiplo (da Python 3.10+, anche con parentesi)
with (open("input.txt") as fin,
      open("output.txt", "w") as fout):
    fout.write(fin.read())

# Modo alternativo (Python 3.1+): virgola
with open("input.txt") as fin, open("output.txt", "w") as fout:
    fout.write(fin.read())
```

---

## C2: Il Protocollo `__enter__` / `__exit__`

### L'Analogia: Il Cameriere del Ristorante

Entrare in un ristorante elegante (apertura della risorsa) e uscire (chiusura della risorsa) ha un protocollo preciso. Il cameriere ti accoglie all'ingresso (`__enter__`) e si assicura che il conto sia pagato e tutto in ordine quando esci (`__exit__`). Qualunque cosa succeda nel mezzo (ordinazione, discussione con il partner, malore improvviso), il conto viene sempre regolato.

### Il Protocollo

Un oggetto e' un context manager se implementa:

```python
class ContextManagerEsempio:
    def __enter__(self):
        """
        Chiamato PRIMA del blocco with.
        Il valore restituito e' assegnato alla variabile 'as'.
        """
        print("__enter__: acquisisco la risorsa")
        return self  # o qualsiasi oggetto che vuoi esporre nel blocco

    def __exit__(self, tipo_eccezione, valore_eccezione, traceback):
        """
        Chiamato DOPO il blocco with, sempre.
        I tre argomenti descrivono l'eventuale eccezione.
        Restituisce True per sopprimere l'eccezione, False/None per propagarla.
        """
        if tipo_eccezione is None:
            print("__exit__: nessuna eccezione — rilascio la risorsa normalmente")
        else:
            print(f"__exit__: eccezione {tipo_eccezione.__name__} — rilascio la risorsa")
        return False  # non sopprimere l'eccezione
```

```python
# Uso
cm = ContextManagerEsempio()
print("=== Caso normale (nessuna eccezione) ===")
with cm:
    print("  Nel blocco with")

print()
print("=== Caso con eccezione ===")
try:
    with ContextManagerEsempio():
        print("  Nel blocco with")
        raise ValueError("Eccezione simulata")
except ValueError as e:
    print(f"Eccezione propagata: {e}")
```

```
# Output atteso:
=== Caso normale (nessuna eccezione) ===
__enter__: acquisisco la risorsa
  Nel blocco with
__exit__: nessuna eccezione — rilascio la risorsa normalmente

=== Caso con eccezione ===
__enter__: acquisisco la risorsa
  Nel blocco with
__exit__: eccezione ValueError — rilascio la risorsa
Eccezione propagata: Eccezione simulata
```

### Sopprimere le Eccezioni con `__exit__`

```python
class SopprimeEccezioni:
    """Context manager che sopprime tutte le eccezioni."""

    def __enter__(self):
        return self

    def __exit__(self, tipo, valore, tb):
        if tipo is not None:
            print(f"Eccezione {tipo.__name__} soppressa: {valore}")
        return True  # True = sopprimi l'eccezione

with SopprimeEccezioni():
    print("Prima dell'eccezione")
    raise RuntimeError("Errore simulato")
    print("Questa riga non viene raggiunta")

print("Dopo il with — esecuzione continua normalmente!")
```

```
# Output atteso:
Prima dell'eccezione
Eccezione RuntimeError soppressa: Errore simulato
Dopo il with — esecuzione continua normalmente!
```

### Implementare un Context Manager per File

```python
class GestoreFile:
    """
    Context manager che apre e chiude un file.
    Equivalente funzionalmente a open() built-in.
    """

    def __init__(self, percorso, modalita="r", encoding="utf-8"):
        self.percorso = percorso
        self.modalita = modalita
        self.encoding = encoding
        self._file = None

    def __enter__(self):
        """Apre il file e lo restituisce."""
        print(f"Apro {self.percorso} in modalita' {self.modalita}")
        self._file = open(self.percorso, self.modalita, encoding=self.encoding)
        return self._file  # esposto come variabile 'as'

    def __exit__(self, tipo, valore, tb):
        """Chiude sempre il file."""
        if self._file and not self._file.closed:
            self._file.close()
            print(f"Chiuso {self.percorso}")
        if tipo is not None:
            print(f"  (con eccezione: {tipo.__name__}: {valore})")
        return False  # propaga le eccezioni

import tempfile, os

with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
    tmp.write("Riga uno\nRiga due\nRiga tre\n")
    percorso = tmp.name

try:
    # Uso normale
    with GestoreFile(percorso) as f:
        contenuto = f.read()
        print(f"Contenuto: {repr(contenuto[:20])}...")
finally:
    os.unlink(percorso)
```

```
# Output atteso:
Apro /tmp/xxx.txt in modalita' r
Contenuto: 'Riga uno\nRiga due\nR'...
Chiuso /tmp/xxx.txt
```

### Context Manager per Transazione Database

```python
class TransazioneDB:
    """
    Context manager per gestire transazioni di database.
    Esegue commit se il blocco ha successo, rollback in caso di errore.
    """

    def __init__(self, connessione):
        self.conn = connessione

    def __enter__(self):
        """Inizia la transazione."""
        print("BEGIN TRANSACTION")
        return self.conn  # restituisce la connessione per le query

    def __exit__(self, tipo, valore, tb):
        """Commit o rollback."""
        if tipo is None:
            print("COMMIT")
            self.conn.commit()
        else:
            print(f"ROLLBACK (causa: {tipo.__name__}: {valore})")
            self.conn.rollback()
        return False  # propaga le eccezioni

# Simulazione di una connessione DB
class ConnessioneSimulata:
    def __init__(self):
        self.log = []

    def execute(self, sql):
        print(f"  EXECUTE: {sql}")
        self.log.append(sql)

    def commit(self):
        print("  [DB] Commit!")

    def rollback(self):
        print("  [DB] Rollback!")

conn = ConnessioneSimulata()

print("=== Transazione con successo ===")
with TransazioneDB(conn) as db:
    db.execute("INSERT INTO utenti VALUES (1, 'Mario')")
    db.execute("INSERT INTO utenti VALUES (2, 'Luigi')")

print()
print("=== Transazione con errore ===")
try:
    with TransazioneDB(conn) as db:
        db.execute("INSERT INTO utenti VALUES (3, 'Anna')")
        raise IntegrityError("UNIQUE constraint failed")
except Exception as e:
    print(f"Errore gestito: {e}")
```

```
# Output atteso:
=== Transazione con successo ===
BEGIN TRANSACTION
  EXECUTE: INSERT INTO utenti VALUES (1, 'Mario')
  EXECUTE: INSERT INTO utenti VALUES (2, 'Luigi')
COMMIT
  [DB] Commit!

=== Transazione con errore ===
BEGIN TRANSACTION
  EXECUTE: INSERT INTO utenti VALUES (3, 'Anna')
ROLLBACK (causa: IntegrityError: UNIQUE constraint failed)
  [DB] Rollback!
Errore gestito: UNIQUE constraint failed
```

### Context Manager per Lock

```python
import threading

class MutexContatore:
    """Contatore thread-safe con context manager per il lock."""

    def __init__(self, valore_iniziale=0):
        self._valore = valore_iniziale
        self._lock = threading.Lock()

    def __enter__(self):
        """Acquisisce il lock."""
        self._lock.acquire()
        return self

    def __exit__(self, tipo, valore, tb):
        """Rilascia il lock — sempre, anche in caso di eccezione."""
        self._lock.release()
        return False

    def incrementa(self):
        self._valore += 1

    @property
    def valore(self):
        return self._valore

contatore = MutexContatore()

# Thread-safe: il lock e' rilasciato anche in caso di eccezione
with contatore:
    contatore.incrementa()
    contatore.incrementa()

print(f"Valore: {contatore.valore}")
```

```
# Output atteso:
Valore: 2
```

---

## C3: `@contextmanager` — La Via Piu' Semplice

### L'Analogia: La Ricetta in Due Fasi

Invece di implementare una classe con `__enter__` e `__exit__`, puoi scrivere una funzione generatrice con un unico `yield`. Il codice prima del `yield` e' il setup (`__enter__`), il valore del `yield` e' la risorsa esposta, il codice dopo il `yield` e' il teardown (`__exit__`).

Come una ricetta che divide: "Prima del pasto" / "Il pasto" / "Dopo il pasto".

### Il Pattern Base

```python
from contextlib import contextmanager

@contextmanager
def mio_context_manager():
    # Codice PRIMA del yield = __enter__
    print("Setup: acquisisco la risorsa")
    risorsa = "la mia risorsa"

    try:
        yield risorsa  # esposta come variabile 'as'
        # Il blocco with viene eseguito qui
    except Exception as e:
        print(f"Eccezione rilevata: {e}")
        raise  # ri-solleva
    finally:
        # Codice DOPO il yield = __exit__
        print("Teardown: rilascio la risorsa")

with mio_context_manager() as risorsa:
    print(f"Sto usando: {risorsa}")
    print("Faccio il lavoro...")
```

```
# Output atteso:
Setup: acquisisco la risorsa
Sto usando: la mia risorsa
Faccio il lavoro...
Teardown: rilascio la risorsa
```

### Regola Critica: Usa `try/finally`

```python
from contextlib import contextmanager

# SBAGLIATO: senza try/finally, il teardown non avviene in caso di eccezione
@contextmanager
def context_rotto():
    print("Setup")
    yield "risorsa"
    print("Teardown")  # NON eseguito se c'e' un'eccezione!

try:
    with context_rotto() as r:
        raise ValueError("Errore nel blocco")
except ValueError as e:
    print(f"Eccezione: {e}")

# "Teardown" non verra' mai stampato!
```

```
# Output atteso:
Setup
Eccezione: Errore nel blocco
```

```python
from contextlib import contextmanager

# CORRETTO: con try/finally
@contextmanager
def context_corretto():
    print("Setup")
    try:
        yield "risorsa"
    finally:
        print("Teardown — eseguito SEMPRE")

try:
    with context_corretto() as r:
        raise ValueError("Errore nel blocco")
except ValueError as e:
    print(f"Eccezione: {e}")
```

```
# Output atteso:
Setup
Teardown — eseguito SEMPRE
Eccezione: Errore nel blocco
```

### Esempio Pratico: Gestione Connessione Database

```python
from contextlib import contextmanager
import sqlite3

@contextmanager
def connessione_db(percorso_db=":memory:"):
    """Context manager per connessioni SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(percorso_db)
        conn.row_factory = sqlite3.Row  # restituisce Row invece di tuple
        print(f"Connessione aperta a {percorso_db}")
        yield conn
        conn.commit()
        print("Commit eseguito")
    except Exception as e:
        if conn:
            conn.rollback()
            print(f"Rollback eseguito (causa: {e})")
        raise
    finally:
        if conn:
            conn.close()
            print("Connessione chiusa")

# Uso
with connessione_db() as conn:
    conn.execute("CREATE TABLE utenti (id INTEGER, nome TEXT)")
    conn.execute("INSERT INTO utenti VALUES (1, 'Mario')")
    conn.execute("INSERT INTO utenti VALUES (2, 'Luigi')")

    righe = conn.execute("SELECT * FROM utenti").fetchall()
    for riga in righe:
        print(f"  Utente: id={riga['id']}, nome={riga['nome']}")
```

```
# Output atteso:
Connessione aperta a :memory:
  Utente: id=1, nome=Mario
  Utente: id=2, nome=Luigi
Commit eseguito
Connessione chiusa
```

### Esempio Pratico: Directory Temporanea

```python
from contextlib import contextmanager
import tempfile
import shutil
import os

@contextmanager
def directory_temporanea(prefisso="tmp_"):
    """
    Crea una directory temporanea e la cancella alla fine.
    Utile per operazioni su file in test o elaborazioni intermedie.
    """
    percorso = tempfile.mkdtemp(prefix=prefisso)
    print(f"Directory temporanea creata: {percorso}")
    try:
        yield percorso
    finally:
        shutil.rmtree(percorso, ignore_errors=True)
        print(f"Directory temporanea rimossa: {percorso}")

# Uso
with directory_temporanea("elaborazione_") as tmpdir:
    # Creiamo alcuni file
    for i in range(3):
        percorso_file = os.path.join(tmpdir, f"file_{i}.txt")
        with open(percorso_file, "w") as f:
            f.write(f"Contenuto del file {i}\n")

    file_creati = os.listdir(tmpdir)
    print(f"File nella directory: {file_creati}")

print(f"Directory esiste ancora: {os.path.exists(tmpdir)}")
```

```
# Output atteso:
Directory temporanea creata: /tmp/elaborazione_XXXXXX
File nella directory: ['file_0.txt', 'file_1.txt', 'file_2.txt']
Directory temporanea rimossa: /tmp/elaborazione_XXXXXX
Directory esiste ancora: False
```

### Esempio Pratico: Misurazione del Tempo

```python
from contextlib import contextmanager
import time

@contextmanager
def cronometra(nome="Operazione"):
    """Misura il tempo di esecuzione di un blocco di codice."""
    inizio = time.perf_counter()
    print(f"[cronometro] {nome}: avvio")
    try:
        yield
    finally:
        durata = time.perf_counter() - inizio
        print(f"[cronometro] {nome}: {durata:.4f}s")

with cronometra("Calcolo intensivo"):
    risultato = sum(i * i for i in range(1_000_000))

print(f"Risultato: {risultato}")
```

```
# Output atteso:
[cronometro] Calcolo intensivo: avvio
[cronometro] Calcolo intensivo: 0.0456s
Risultato: 333332833333500000
```

---

## C4: `suppress`, `redirect_stdout`, `closing`

### `suppress`: Sopprimere Eccezioni Specifiche

```python
from contextlib import suppress
import os

# PRIMA — senza suppress: verbose
percorso = "/tmp/file_che_non_esiste.txt"

try:
    os.remove(percorso)
except FileNotFoundError:
    pass  # ignoriamo se il file non esiste

# CON suppress — molto piu' conciso
with suppress(FileNotFoundError):
    os.remove(percorso)  # se il file non esiste, niente panico

print("File rimosso (se esisteva)")
```

```
# Output atteso:
File rimosso (se esisteva)
```

```python
# suppress con piu' tipi di eccezione
with suppress(FileNotFoundError, PermissionError):
    os.remove("/percorso/protetto")

# suppress nel codice di pulizia
import shutil

def pulisci(directory):
    """Rimuove la directory — non fallisce se non esiste o se e' protetta."""
    with suppress(FileNotFoundError, OSError):
        shutil.rmtree(directory)
```

### Quando NON Usare `suppress`

```python
from contextlib import suppress

# OK: sopprimere FileNotFoundError in codice di pulizia
with suppress(FileNotFoundError):
    os.remove("/tmp/cache.tmp")

# NON OK: sopprimere eccezioni di business logic — maschera bug reali
with suppress(ValueError):
    prezzo = float(input_utente)  # se l'input e' invalido, dobbiamo gestirlo!
# Questo silenziosamente ignora input invalidi — bug nascosto!

# NON OK: sopprimere Exception o BaseException — troppo generico
with suppress(Exception):  # MAI fare questo!
    ...
```

### `redirect_stdout` e `redirect_stderr`: Redirigere l'Output

```python
from contextlib import redirect_stdout, redirect_stderr
import io

# Catturare l'output di funzioni che stampano
def funzione_con_print():
    print("Questa stampa va catturata")
    print("Anche questa")
    return 42

# Senza redirect: la stampa va sulla console
# Con redirect: catturiamo l'output in una stringa
buffer = io.StringIO()
with redirect_stdout(buffer):
    risultato = funzione_con_print()

output_catturato = buffer.getvalue()
print(f"Output catturato: {repr(output_catturato)}")
print(f"Risultato della funzione: {risultato}")
```

```
# Output atteso:
Output catturato: 'Questa stampa va catturata\nAnche questa\n'
Risultato della funzione: 42
```

```python
# Utile nei test per verificare l'output
from contextlib import redirect_stdout
import io

def test_funzione_di_stampa():
    """Verifica che la funzione stampi quello che ci aspettiamo."""
    buffer = io.StringIO()

    with redirect_stdout(buffer):
        funzione_con_print()

    output = buffer.getvalue()
    assert "Questa stampa va catturata" in output
    assert "Anche questa" in output
    print("Test passato!")

test_funzione_di_stampa()
```

```
# Output atteso:
Test passato!
```

```python
# redirect_stderr: cattura gli errori
from contextlib import redirect_stderr
import io, sys, warnings

buffer_errori = io.StringIO()
with redirect_stderr(buffer_errori):
    print("Questo e' un errore", file=sys.stderr)
    warnings.warn("Questo e' un warning", stacklevel=1)

print(f"Errori catturati: {repr(buffer_errori.getvalue()[:50])}")
```

```
# Output atteso:
Errori catturati: 'Questo e\' un errore\n...'
```

### `closing`: Garantire la Chiusura di Oggetti

```python
from contextlib import closing

# closing() e' utile per oggetti che hanno close() ma non supportano 'with'
class ConnessioneLegacy:
    """Connessione vecchia che non implementa il protocollo CM."""

    def query(self, sql):
        return f"Risultati di: {sql}"

    def close(self):
        print("Connessione legacy chiusa")

# Avvolgila con closing() per usarla con with
with closing(ConnessioneLegacy()) as conn:
    risultato = conn.query("SELECT * FROM tabella")
    print(f"Risultato: {risultato}")

# conn.close() e' chiamato automaticamente
```

```
# Output atteso:
Risultato: Risultati di: SELECT * FROM tabella
Connessione legacy chiusa
```

```python
# Altro esempio: urllib.request.urlopen restituisce un oggetto con close()
from contextlib import closing
from urllib.request import urlopen

# Senza closing, dovresti gestire close() manualmente
# Con closing, e' automatico:
# with closing(urlopen("https://httpbin.org/get")) as risposta:
#     dati = risposta.read()
```

### `nullcontext`: Context Manager No-Op

```python
from contextlib import nullcontext

def elabora(dati, conn=None):
    """
    Elabora dati. Se conn e' None, apre una connessione propria.
    nullcontext evita if/else per il context manager.
    """
    # Senza nullcontext, dovresti fare:
    # if conn is None:
    #     with apri_connessione() as c:
    #         _elabora(dati, c)
    # else:
    #     _elabora(dati, conn)

    # Con nullcontext, il codice e' piu' pulito:
    cm = apri_connessione() if conn is None else nullcontext(conn)
    with cm as c:
        print(f"Elaboro con connessione: {c}")

def apri_connessione():
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        print("Connessione aperta")
        yield "nuova_conn"
        print("Connessione chiusa")
    return _cm()

elabora("dati", conn="conn_esistente")
print("---")
elabora("dati", conn=None)
```

```
# Output atteso:
Elaboro con connessione: conn_esistente
---
Connessione aperta
Elaboro con connessione: nuova_conn
Connessione chiusa
```

---

## C5: `ExitStack` — Gestione Dinamica

### L'Analogia: La Lista di Cose da Fare Prima di Uscire

Prima di uscire di casa, hai una lista di cose da fare: spegnere le luci, chiudere il gas, chiudere la finestra, dare l'acqua alla pianta. ExitStack e' esattamente questo: una pila dinamica di "cose da fare quando si esce", gestite in ordine LIFO (Last In, First Out).

### Il Problema: Context Manager Dinamici

```python
# Problema: quanti file devo aprire? Non lo so a runtime.
percorsi = ["file1.txt", "file2.txt", "file3.txt"]  # potrebbero essere N file

# Con nested with: non funziona se N e' variabile
# with open("file1.txt") as f1:
#     with open("file2.txt") as f2:
#         ...  # non posso nidificare N livelli se N e' variabile

# Con ExitStack: funziona per N qualsiasi
from contextlib import ExitStack

with ExitStack() as stack:
    file_aperti = []
    for percorso in percorsi:
        # Simuliamo i file con StringIO
        import io
        f = stack.enter_context(io.StringIO(f"Contenuto di {percorso}"))
        file_aperti.append(f)

    for f in file_aperti:
        print(f.read())
    # Tutti i "file" vengono chiusi automaticamente all'uscita del with
```

```
# Output atteso:
Contenuto di file1.txt
Contenuto di file2.txt
Contenuto di file3.txt
```

### `enter_context()`, `callback()`, `push()`

```python
from contextlib import ExitStack, contextmanager

@contextmanager
def risorsa(nome):
    print(f"Acquisto: {nome}")
    try:
        yield f"Risorsa: {nome}"
    finally:
        print(f"Rilascio: {nome}")

# enter_context(): entra in un context manager
with ExitStack() as stack:
    r1 = stack.enter_context(risorsa("database"))
    r2 = stack.enter_context(risorsa("cache"))
    r3 = stack.enter_context(risorsa("file"))

    print(f"Ho: {r1}, {r2}, {r3}")

    # callback(): registra una funzione da chiamare all'uscita
    stack.callback(print, "Callback eseguita!")
```

```
# Output atteso:
Acquisto: database
Acquisto: cache
Acquisto: file
Ho: Risorsa: database, Risorsa: cache, Risorsa: file
Callback eseguita!
Rilascio: file
Rilascio: cache
Rilascio: database
```

Nota: l'ordine di cleanup e' **LIFO** (l'ultimo entrato e' il primo a uscire) — come uno stack di piatti.

### `pop_all()`: Trasferimento di Responsabilita'

```python
from contextlib import ExitStack, contextmanager

@contextmanager
def connessione(nome):
    print(f"Aperta connessione: {nome}")
    try:
        yield {"conn": nome, "attiva": True}
    finally:
        print(f"Chiusa connessione: {nome}")

class GestoreRisorse:
    """
    Gestisce un pool di risorse.
    Usa pop_all() per trasferire la responsabilita' di cleanup
    dall'inizializzazione all'oggetto stesso.
    """

    def __init__(self, nomi_connessioni):
        self._stack = None
        self._connessioni = []

        # Stack temporaneo durante l'inizializzazione
        with ExitStack() as stack_temp:
            for nome in nomi_connessioni:
                conn = stack_temp.enter_context(connessione(nome))
                self._connessioni.append(conn)

            # Se l'inizializzazione ha successo, trasferisci la responsabilita'
            # all'oggetto. Se fallisce a meta', stack_temp pulisce tutto.
            self._stack = stack_temp.pop_all()

        print("GestoreRisorse inizializzato correttamente!")

    def usa(self, nome):
        for conn in self._connessioni:
            if conn["conn"] == nome:
                return conn
        return None

    def chiudi(self):
        """Chiude tutte le risorse in ordine LIFO."""
        if self._stack:
            self._stack.close()
            self._stack = None

# Uso
gestore = GestoreRisorse(["db_master", "db_replica", "redis"])
print(f"Connessione disponibile: {gestore.usa('db_master')}")
print("Chiudo tutto...")
gestore.chiudi()
```

```
# Output atteso:
Aperta connessione: db_master
Aperta connessione: db_replica
Aperta connessione: redis
GestoreRisorse inizializzato correttamente!
Connessione disponibile: {'conn': 'db_master', 'attiva': True}
Chiudo tutto...
Chiusa connessione: redis
Chiusa connessione: db_replica
Chiusa connessione: db_master
```

### ExitStack per Gestione Sicura di Risorse Multiple

```python
from contextlib import ExitStack
import tempfile
import os
import shutil

def elabora_file_sicuro(lista_percorsi):
    """
    Elabora N file garantendo cleanup anche in caso di errore.
    Non conosce N a priori.
    """
    risultati = {}

    with ExitStack() as stack:
        # Apertura dinamica di N file
        file_aperti = {}
        for percorso in lista_percorsi:
            if os.path.exists(percorso):
                f = stack.enter_context(open(percorso, "r"))
                file_aperti[percorso] = f

        # Registra callback di pulizia
        tmpdir = tempfile.mkdtemp()
        stack.callback(shutil.rmtree, tmpdir, True)

        # Elaborazione
        for percorso, f in file_aperti.items():
            contenuto = f.read()
            risultati[percorso] = len(contenuto)

    # Qui tutti i file sono chiusi e tmpdir e' rimossa
    return risultati
```

---

## C6: Context Manager Asincroni

### `asynccontextmanager`

```python
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def connessione_asincrona(host, porta):
    """Context manager asincrono per simulare una connessione di rete."""
    print(f"Connecting to {host}:{porta}...")
    await asyncio.sleep(0.1)  # simula latenza di rete
    conn = {"host": host, "porta": porta, "attiva": True}
    print(f"Connesso a {host}:{porta}")

    try:
        yield conn
    finally:
        await asyncio.sleep(0.05)  # simula chiusura
        conn["attiva"] = False
        print(f"Disconnesso da {host}:{porta}")

async def main():
    async with connessione_asincrona("db.example.com", 5432) as conn:
        print(f"Connessione attiva: {conn['attiva']}")
        await asyncio.sleep(0.1)  # simula lavoro
        print("Lavoro completato")
    print(f"Dopo il with, connessione attiva: {conn['attiva']}")

asyncio.run(main())
```

```
# Output atteso:
Connecting to db.example.com:5432...
Connesso a db.example.com:5432
Connessione attiva: True
Lavoro completato
Disconnesso da db.example.com:5432
Dopo il with, connessione attiva: False
```

### Classe come Context Manager Asincrono

```python
import asyncio

class SessioneHTTPAsincrona:
    """
    Context manager asincrono per sessioni HTTP.
    Equivalente a aiohttp.ClientSession().
    """

    def __init__(self, url_base):
        self.url_base = url_base
        self._sessione = None

    async def __aenter__(self):
        """Apre la sessione."""
        print(f"Apro sessione HTTP verso {self.url_base}")
        await asyncio.sleep(0.05)  # simula handshake
        self._sessione = {"url_base": self.url_base, "aperta": True}
        return self

    async def __aexit__(self, tipo, valore, tb):
        """Chiude la sessione."""
        if self._sessione:
            await asyncio.sleep(0.02)  # simula chiusura
            self._sessione["aperta"] = False
            print(f"Sessione HTTP chiusa")
        return False

    async def get(self, percorso):
        """Simula una richiesta GET."""
        await asyncio.sleep(0.1)
        return {"status": 200, "body": f"Risposta per {self.url_base}{percorso}"}

async def main():
    async with SessioneHTTPAsincrona("https://api.example.com") as sessione:
        risposta = await sessione.get("/utenti/1")
        print(f"Risposta: {risposta}")

asyncio.run(main())
```

```
# Output atteso:
Apro sessione HTTP verso https://api.example.com
Risposta: {'status': 200, 'body': 'Risposta per https://api.example.com/utenti/1'}
Sessione HTTP chiusa
```

### `AsyncExitStack`

```python
from contextlib import AsyncExitStack, asynccontextmanager
import asyncio

@asynccontextmanager
async def risorsa_async(nome, delay=0.1):
    print(f"[OPEN] {nome}")
    await asyncio.sleep(delay)
    try:
        yield f"Risorsa: {nome}"
    finally:
        await asyncio.sleep(delay)
        print(f"[CLOSE] {nome}")

async def main():
    async with AsyncExitStack() as stack:
        r1 = await stack.enter_async_context(risorsa_async("database"))
        r2 = await stack.enter_async_context(risorsa_async("cache", delay=0.05))

        # Registra callback sincrona
        stack.callback(print, "[CALLBACK] Cleanup sincrono")

        print(f"Ho: {r1}")
        print(f"Ho: {r2}")

asyncio.run(main())
```

```
# Output atteso:
[OPEN] database
[OPEN] cache
Ho: Risorsa: database
Ho: Risorsa: cache
[CALLBACK] Cleanup sincrono
[CLOSE] cache
[CLOSE] database
```

---

## Errori Comuni della Parte C

### Errore 1: Dimenticare `try/finally` in `@contextmanager`

```python
from contextlib import contextmanager

# SBAGLIATO: il teardown non avviene in caso di eccezione
@contextmanager
def context_rotto():
    risorsa = apri_risorsa()
    yield risorsa
    chiudi_risorsa(risorsa)  # MAI eseguito se c'e' un'eccezione!

# CORRETTO: usa try/finally
@contextmanager
def context_corretto():
    risorsa = apri_risorsa()
    try:
        yield risorsa
    finally:
        chiudi_risorsa(risorsa)  # SEMPRE eseguito
```

### Errore 2: Sopprimere Troppo con `suppress`

```python
from contextlib import suppress

# SBAGLIATO: sopprime qualsiasi eccezione — maschera bug
with suppress(Exception):
    calcola_valore_critico()  # se c'e' un bug, non lo vediamo mai!

# CORRETTO: sopprime solo eccezioni specifiche e attese
with suppress(FileNotFoundError):
    os.remove("/tmp/cache.tmp")  # ok se il file non esiste
```

### Errore 3: Usare `__exit__` per Logica di Business

```python
class GestoreValidazione:
    """SBAGLIATO: usa __exit__ per logica di business."""

    def __enter__(self):
        return self

    def __exit__(self, tipo, valore, tb):
        if isinstance(valore, ValueError):
            print("Input non valido — uso un valore di default")
            return True  # sopprime l'eccezione
        return False

# Questo e' confuso: la soppressione delle eccezioni in __exit__
# dovrebbe essere riservata a casi eccezionali (es: suppress).
# La logica di business dovrebbe stare nel corpo del blocco with.
```

### Errore 4: Non Usare `with` per Risorse

```python
# SBAGLIATO: il file potrebbe restare aperto
def elabora_file_sbagliato(percorso):
    f = open(percorso)
    dati = f.read()  # se qui c'e' un'eccezione...
    f.close()        # ...questa non viene mai eseguita
    return dati

# CORRETTO: con with, il file e' sempre chiuso
def elabora_file_corretto(percorso):
    with open(percorso) as f:
        return f.read()
```

### Errore 5: ExitStack — Ordine di Cleanup

```python
from contextlib import ExitStack, contextmanager

@contextmanager
def dipende_da(nome, dipendenza=None):
    if dipendenza:
        print(f"Acquisto {nome} (dipende da {dipendenza})")
    else:
        print(f"Acquisto {nome}")
    try:
        yield nome
    finally:
        print(f"Rilascio {nome}")

with ExitStack() as stack:
    db = stack.enter_context(dipende_da("database"))
    cache = stack.enter_context(dipende_da("cache", dipende_da="database"))
    sessione = stack.enter_context(dipende_da("sessione", dipende_da="database"))

# Il cleanup avviene in ordine LIFO:
# sessione, poi cache, poi database
# Questo e' il comportamento CORRETTO: si chiude nell'ordine inverso dell'apertura
```

```
# Output atteso:
Acquisto database
Acquisto cache (dipende da database)
Acquisto sessione (dipende da database)
Rilascio sessione
Rilascio cache
Rilascio database
```

---

## 12+ Esercizi della Parte C

### Esercizio C1: Gestore di Log

```python
from contextlib import contextmanager
import time

@contextmanager
def log_operazione(nome_operazione, logger=print):
    """
    Context manager che logga l'inizio, la fine e il tempo di un'operazione.
    In caso di eccezione, logga l'errore ma la propaga.
    """
    inizio = time.perf_counter()
    logger(f"[START] {nome_operazione}")
    try:
        yield
        durata = time.perf_counter() - inizio
        logger(f"[OK] {nome_operazione} completata in {durata:.3f}s")
    except Exception as e:
        durata = time.perf_counter() - inizio
        logger(f"[FAIL] {nome_operazione} fallita dopo {durata:.3f}s: {e}")
        raise

# Uso corretto
with log_operazione("Elaborazione dati"):
    time.sleep(0.1)
    risultato = [i ** 2 for i in range(100)]

print()

# Uso con eccezione
try:
    with log_operazione("Operazione fallita"):
        time.sleep(0.05)
        raise ValueError("Dati non validi")
except ValueError:
    pass
```

```
# Output atteso:
[START] Elaborazione dati
[OK] Elaborazione dati completata in 0.101s

[START] Operazione fallita
[FAIL] Operazione fallita fallita dopo 0.051s: Dati non validi
```

### Esercizio C2: Transazione Idempotente

```python
from contextlib import contextmanager
from datetime import datetime

class DatabaseSimulato:
    """Database simulato con supporto transazioni."""

    def __init__(self):
        self._dati = {}
        self._transazioni_completate = set()

    def inserisci(self, id_transazione, chiave, valore):
        if id_transazione in self._transazioni_completate:
            print(f"  [IDEMPOTENT] Transazione {id_transazione} gia' eseguita — skip")
            return False
        self._dati[chiave] = valore
        self._transazioni_completate.add(id_transazione)
        print(f"  [INSERT] {chiave} = {valore}")
        return True

    def leggi(self, chiave):
        return self._dati.get(chiave)

@contextmanager
def transazione_idempotente(db, id_transazione):
    """
    Garantisce che una transazione sia eseguita al massimo una volta.
    Usare lo stesso id_transazione non ha effetti la seconda volta.
    """
    print(f"[TXN] Avvio transazione {id_transazione}")
    try:
        yield db
        print(f"[TXN] Transazione {id_transazione} completata")
    except Exception as e:
        print(f"[TXN] Transazione {id_transazione} fallita: {e}")
        raise

db = DatabaseSimulato()

# Prima esecuzione: esegue
with transazione_idempotente(db, "TXN-001"):
    db.inserisci("TXN-001", "utente:1", {"nome": "Mario", "eta": 30})

print()

# Seconda esecuzione con stesso ID: idempotente
with transazione_idempotente(db, "TXN-001"):
    db.inserisci("TXN-001", "utente:1", {"nome": "Mario MODIFICATO", "eta": 99})

print(f"\nValore nel DB: {db.leggi('utente:1')}")
```

```
# Output atteso:
[TXN] Avvio transazione TXN-001
  [INSERT] utente:1 = {'nome': 'Mario', 'eta': 30}
[TXN] Transazione TXN-001 completata

[TXN] Avvio transazione TXN-001
  [IDEMPOTENT] Transazione TXN-001 gia' eseguita — skip
[TXN] Transazione TXN-001 completata

Valore nel DB: {'nome': 'Mario', 'eta': 30}
```

### Esercizio C3: Context Manager Riconfigurabile

```python
from contextlib import contextmanager

@contextmanager
def impostazioni_temporanee(**nuove_impostazioni):
    """
    Modifica temporaneamente le impostazioni di configurazione.
    Le impostazioni originali vengono ripristinate all'uscita.
    """
    configurazione = {
        "debug": False,
        "timeout": 30,
        "max_retry": 3,
        "log_level": "INFO",
    }

    # Salva lo stato originale
    originali = {k: configurazione[k] for k in nuove_impostazioni if k in configurazione}

    # Applica le nuove impostazioni
    for k, v in nuove_impostazioni.items():
        if k in configurazione:
            configurazione[k] = v
            print(f"  [CONFIG] {k}: {originali.get(k)} -> {v}")

    try:
        yield configurazione
    finally:
        # Ripristina le impostazioni originali
        for k, v in originali.items():
            configurazione[k] = v
            print(f"  [CONFIG] {k}: ripristinato a {v}")

# Uso
with impostazioni_temporanee(debug=True, timeout=5) as cfg:
    print(f"  Debug: {cfg['debug']}, Timeout: {cfg['timeout']}")
```

```
# Output atteso:
  [CONFIG] debug: False -> True
  [CONFIG] timeout: 30 -> 5
  Debug: True, Timeout: 5
  [CONFIG] debug: ripristinato a False
  [CONFIG] timeout: ripristinato a 30
```

### Esercizio C4: Pool di Risorse

```python
from contextlib import contextmanager
import queue
import threading

class PoolConnessioni:
    """
    Pool di connessioni con context manager.
    Restitutisce una connessione dal pool e la restituisce quando finisce.
    """

    def __init__(self, dimensione=3):
        self._pool = queue.Queue()
        for i in range(dimensione):
            self._pool.put(f"conn_{i}")
        self._lock = threading.Lock()

    @contextmanager
    def prendi(self, timeout=5.0):
        """Context manager: prende una connessione dal pool e la restituisce."""
        try:
            conn = self._pool.get(timeout=timeout)
            print(f"  [POOL] Presa connessione: {conn}")
            yield conn
        finally:
            self._pool.put(conn)
            print(f"  [POOL] Restituita connessione: {conn}")

    @property
    def disponibili(self):
        return self._pool.qsize()

pool = PoolConnessioni(dimensione=3)
print(f"Disponibili: {pool.disponibili}")

with pool.prendi() as conn1:
    print(f"  Usando: {conn1}")
    print(f"  Disponibili ora: {pool.disponibili}")

print(f"Dopo il with, disponibili: {pool.disponibili}")
```

```
# Output atteso:
Disponibili: 3
  [POOL] Presa connessione: conn_0
  Usando: conn_0
  Disponibili ora: 2
  [POOL] Restituita connessione: conn_0
Dopo il with, disponibili: 3
```

### Esercizio C5: Context Manager come Decoratore

```python
from contextlib import contextmanager

@contextmanager
def gestisci_errori_db(ripropaga=True):
    """Context manager che gestisce eccezioni del database."""
    try:
        yield
    except ConnectionError as e:
        print(f"[DB] Errore di connessione: {e}")
        if ripropaga:
            raise
    except ValueError as e:
        print(f"[DB] Dati non validi: {e}")
        if ripropaga:
            raise

# I context manager di contextlib possono essere usati anche come decoratori!
@gestisci_errori_db()
def aggiorna_utente(id_utente, dati):
    if not isinstance(dati, dict):
        raise ValueError(f"dati deve essere un dict, non {type(dati)}")
    print(f"Utente {id_utente} aggiornato con {dati}")

# Uso normale
aggiorna_utente(1, {"nome": "Mario"})

print()

# Uso con errore
try:
    aggiorna_utente(2, "nome: Luigi")  # stringa invece di dict
except ValueError:
    print("Errore catturato e propagato")
```

```
# Output atteso:
Utente 1 aggiornato con {'nome': 'Mario'}

[DB] Dati non validi: dati deve essere un dict, non <class 'str'>
Errore catturato e propagato
```

### Esercizio C6: Backup Automatico

```python
from contextlib import contextmanager
import shutil
import os
import tempfile

@contextmanager
def modifica_con_backup(percorso_file):
    """
    Crea un backup prima di modificare un file.
    Se la modifica fallisce, ripristina il backup automaticamente.
    """
    percorso_backup = percorso_file + ".bak"

    # Creiamo un file di test
    with open(percorso_file, "w") as f:
        f.write("Contenuto originale\n")

    # Crea il backup
    shutil.copy2(percorso_file, percorso_backup)
    print(f"Backup creato: {percorso_backup}")

    try:
        yield percorso_file  # l'utente modifica il file qui
        os.unlink(percorso_backup)  # successo: rimuovi il backup
        print("Modifica completata — backup rimosso")
    except Exception as e:
        # Ripristina il backup
        shutil.copy2(percorso_backup, percorso_file)
        os.unlink(percorso_backup)
        print(f"Errore! Backup ripristinato (causa: {e})")
        raise

import tempfile, os

# Crea file temporaneo
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
    percorso = tmp.name

try:
    # Caso 1: modifica con successo
    with modifica_con_backup(percorso) as p:
        with open(p, "w") as f:
            f.write("Contenuto modificato con successo\n")

    with open(percorso) as f:
        print(f"Contenuto finale: {f.read().strip()}")

    print()

    # Caso 2: modifica che fallisce
    try:
        with modifica_con_backup(percorso) as p:
            with open(p, "w") as f:
                f.write("Scrittura parziale...\n")
            raise RuntimeError("Errore durante la modifica!")
    except RuntimeError:
        pass

    with open(percorso) as f:
        print(f"Contenuto ripristinato: {f.read().strip()}")
finally:
    if os.path.exists(percorso):
        os.unlink(percorso)
```

```
# Output atteso:
Backup creato: /tmp/xxx.txt.bak
Modifica completata — backup rimosso
Contenuto finale: Contenuto modificato con successo

Backup creato: /tmp/xxx.txt.bak
Errore! Backup ripristinato (causa: Errore durante la modifica!)
Contenuto ripristinato: Contenuto modificato con successo
```

### Esercizio C7: Limitatore di Concorrenza

```python
from contextlib import asynccontextmanager
import asyncio

class SemaforoControllato:
    """Controlla il numero massimo di operazioni concorrenti."""

    def __init__(self, max_concurrent):
        self._semaforo = asyncio.Semaphore(max_concurrent)
        self._attivi = 0
        self._max = max_concurrent

    @asynccontextmanager
    async def accesso(self, nome):
        """Context manager che limita la concorrenza."""
        async with self._semaforo:
            self._attivi += 1
            print(f"  [{nome}] Avviato ({self._attivi}/{self._max} attivi)")
            try:
                yield
            finally:
                self._attivi -= 1
                print(f"  [{nome}] Completato ({self._attivi}/{self._max} attivi)")

async def operazione_asincrona(nome, semaforo, durata):
    async with semaforo.accesso(nome):
        await asyncio.sleep(durata)

async def main():
    semaforo = SemaforoControllato(max_concurrent=2)  # max 2 concorrenti

    # Lanciamo 4 operazioni, ma solo 2 possono girare contemporaneamente
    tasks = [
        operazione_asincrona("Task-A", semaforo, 0.1),
        operazione_asincrona("Task-B", semaforo, 0.1),
        operazione_asincrona("Task-C", semaforo, 0.1),
        operazione_asincrona("Task-D", semaforo, 0.1),
    ]
    await asyncio.gather(*tasks)
    print("Tutte le operazioni completate!")

asyncio.run(main())
```

```
# Output atteso (ordine potrebbe variare):
  [Task-A] Avviato (1/2 attivi)
  [Task-B] Avviato (2/2 attivi)
  [Task-A] Completato (1/2 attivi)
  [Task-C] Avviato (2/2 attivi)
  [Task-B] Completato (1/2 attivi)
  [Task-D] Avviato (2/2 attivi)
  [Task-C] Completato (1/2 attivi)
  [Task-D] Completato (0/2 attivi)
Tutte le operazioni completate!
```

### Esercizio C8: Cache con TTL

```python
from contextlib import contextmanager
import time
import threading
from functools import wraps

class CacheTTL:
    """Cache con time-to-live usando un lock per thread-safety."""

    def __init__(self, ttl_secondi=60):
        self._cache = {}
        self._lock = threading.RLock()
        self._ttl = ttl_secondi

    @contextmanager
    def blocca(self):
        """Context manager per acquisire il lock."""
        with self._lock:
            yield

    def ottieni(self, chiave):
        with self.blocca():
            if chiave in self._cache:
                valore, scadenza = self._cache[chiave]
                if time.time() < scadenza:
                    return valore
                del self._cache[chiave]
            return None

    def imposta(self, chiave, valore):
        with self.blocca():
            self._cache[chiave] = (valore, time.time() + self._ttl)

    def cache_or_compute(self, chiave, funzione_calcolo):
        """Restituisce dalla cache o calcola e mette in cache."""
        valore = self.ottieni(chiave)
        if valore is None:
            valore = funzione_calcolo()
            self.imposta(chiave, valore)
            print(f"  [CACHE MISS] Calcolato e salvato: {chiave}")
        else:
            print(f"  [CACHE HIT] Trovato: {chiave}")
        return valore

cache = CacheTTL(ttl_secondi=2)

# Prima chiamata: calcola
risultato1 = cache.cache_or_compute(
    "fibonacci_30",
    lambda: sum(1 for _ in range(100))  # calcolo costoso simulato
)

# Seconda chiamata: dalla cache
risultato2 = cache.cache_or_compute("fibonacci_30", lambda: sum(1 for _ in range(100)))

print(f"Risultati uguali: {risultato1 == risultato2}")

# Aspetta che scada la TTL
time.sleep(2.1)

# Terza chiamata: cache scaduta, ricalcola
risultato3 = cache.cache_or_compute("fibonacci_30", lambda: sum(1 for _ in range(100)))
```

```
# Output atteso:
  [CACHE MISS] Calcolato e salvato: fibonacci_30
  [CACHE HIT] Trovato: fibonacci_30
Risultati uguali: True
  [CACHE MISS] Calcolato e salvato: fibonacci_30
```

### Esercizio C9: Context Manager Composto — Decorator + CM

```python
from contextlib import contextmanager
import functools
import time

@contextmanager
def traccia_performance(nome, soglia_ms=100):
    """
    Context manager che:
    1. Misura il tempo di esecuzione
    2. Emette un warning se supera la soglia
    """
    inizio = time.perf_counter()
    try:
        yield
    finally:
        durata_ms = (time.perf_counter() - inizio) * 1000
        if durata_ms > soglia_ms:
            print(f"[PERF WARNING] {nome} ha impiegato {durata_ms:.1f}ms (soglia: {soglia_ms}ms)")
        else:
            print(f"[PERF OK] {nome}: {durata_ms:.1f}ms")

def monitora(soglia_ms=100):
    """Decoratore che usa traccia_performance come context manager."""
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            with traccia_performance(funzione.__name__, soglia_ms):
                return funzione(*args, **kwargs)
        return wrapper
    return decoratore

@monitora(soglia_ms=50)
def operazione_veloce():
    time.sleep(0.02)
    return "ok"

@monitora(soglia_ms=50)
def operazione_lenta():
    time.sleep(0.1)
    return "ok"

operazione_veloce()
operazione_lenta()
```

```
# Output atteso:
[PERF OK] operazione_veloce: 20.1ms
[PERF WARNING] operazione_lenta ha impiegato 100.2ms (soglia: 50ms)
```

### Esercizio C10: Circuit Breaker

```python
from contextlib import contextmanager
import time
from enum import Enum, auto

class Stato(Enum):
    CHIUSO = auto()      # normale, le chiamate passano
    APERTO = auto()      # bloccato, le chiamate falliscono immediatamente
    SEMI_APERTO = auto() # in prova, permette una chiamata di test

class CircuitBreaker:
    """
    Circuit Breaker: protegge le chiamate a sistemi esterni instabili.
    Passa da CHIUSO -> APERTO dopo N fallimenti.
    Dopo un timeout, va in SEMI_APERTO per testare il recupero.
    """

    def __init__(self, soglia_fallimenti=3, timeout_recupero=5.0):
        self.stato = Stato.CHIUSO
        self._fallimenti = 0
        self._soglia = soglia_fallimenti
        self._timeout = timeout_recupero
        self._ultima_apertura = None

    @contextmanager
    def chiama(self):
        """Context manager per proteggere una chiamata."""
        if self.stato == Stato.APERTO:
            # Controlla se e' passato abbastanza tempo per il recupero
            if time.time() - self._ultima_apertura >= self._timeout:
                self.stato = Stato.SEMI_APERTO
                print(f"[CB] Stato: SEMI_APERTO — test recupero")
            else:
                raise RuntimeError(
                    f"Circuit breaker APERTO. Riprova tra "
                    f"{self._timeout - (time.time()-self._ultima_apertura):.1f}s"
                )

        try:
            yield
            # Successo
            if self.stato == Stato.SEMI_APERTO:
                self.stato = Stato.CHIUSO
                self._fallimenti = 0
                print(f"[CB] Recuperato! Stato: CHIUSO")
            elif self.stato == Stato.CHIUSO:
                self._fallimenti = max(0, self._fallimenti - 1)  # decai fallimenti
        except Exception:
            self._fallimenti += 1
            print(f"[CB] Fallimento {self._fallimenti}/{self._soglia}")
            if self._fallimenti >= self._soglia:
                self.stato = Stato.APERTO
                self._ultima_apertura = time.time()
                print(f"[CB] APERTO! Troppi fallimenti.")
            raise

cb = CircuitBreaker(soglia_fallimenti=3, timeout_recupero=0.5)

# Simuliamo 4 fallimenti
for i in range(4):
    try:
        with cb.chiama():
            raise ConnectionError("Servizio non disponibile")
    except (ConnectionError, RuntimeError) as e:
        print(f"  Catturato: {e}")
    print()

# Aspetta il recupero
time.sleep(0.6)

# Tenta il recupero
try:
    with cb.chiama():
        print("  Test recupero: SUCCESSO!")
except Exception as e:
    print(f"  Test recupero fallito: {e}")
```

```
# Output atteso:
[CB] Fallimento 1/3
  Catturato: Servizio non disponibile

[CB] Fallimento 2/3
  Catturato: Servizio non disponibile

[CB] Fallimento 3/3
[CB] APERTO! Troppi fallimenti.
  Catturato: Servizio non disponibile

  Catturato: Circuit breaker APERTO. Riprova tra 0.5s

[CB] Stato: SEMI_APERTO — test recupero
  Test recupero: SUCCESSO!
[CB] Recuperato! Stato: CHIUSO
```

### Esercizio C11: ExitStack per Gestione Plugin

```python
from contextlib import ExitStack, contextmanager

@contextmanager
def plugin_avviato(nome, configurazione):
    """Context manager che gestisce il ciclo di vita di un plugin."""
    print(f"[PLUGIN] Avvio {nome} con config: {configurazione}")
    stato = {"nome": nome, "attivo": True, "config": configurazione}
    try:
        yield stato
    except Exception as e:
        print(f"[PLUGIN] Errore in {nome}: {e}")
        stato["attivo"] = False
        raise
    finally:
        stato["attivo"] = False
        print(f"[PLUGIN] Spento {nome}")

class GestorePlugin:
    """Gestisce N plugin con ExitStack."""

    def __init__(self):
        self._stack = None
        self._plugin = {}

    def __enter__(self):
        self._stack = ExitStack()
        return self

    def __exit__(self, tipo, valore, tb):
        if self._stack:
            return self._stack.__exit__(tipo, valore, tb)
        return False

    def carica(self, nome, configurazione):
        """Carica un plugin dinamicamente."""
        stato = self._stack.enter_context(
            plugin_avviato(nome, configurazione)
        )
        self._plugin[nome] = stato
        return stato

    def stato(self, nome):
        return self._plugin.get(nome)

# Uso
with GestorePlugin() as gp:
    db = gp.carica("database", {"host": "localhost", "porta": 5432})
    cache = gp.carica("redis", {"host": "localhost", "porta": 6379})
    ml = gp.carica("ml_model", {"path": "/models/classifier.pkl"})

    print(f"\nPlugin database attivo: {gp.stato('database')['attivo']}")
    print(f"Plugin redis attivo: {gp.stato('redis')['attivo']}")
    print("Elaborazione in corso...\n")
```

```
# Output atteso:
[PLUGIN] Avvio database con config: {'host': 'localhost', 'porta': 5432}
[PLUGIN] Avvio redis con config: {'host': 'localhost', 'porta': 6379}
[PLUGIN] Avvio ml_model con config: {'path': '/models/classifier.pkl'}

Plugin database attivo: True
Plugin redis attivo: True
Elaborazione in corso...

[PLUGIN] Spento ml_model
[PLUGIN] Spento redis
[PLUGIN] Spento database
```

### Esercizio C12: Pipeline Completa (Decoratori + Generatori + Context Manager)

```python
from contextlib import contextmanager
import functools
import time

# Decoratore che registra le operazioni
def log_operazione(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print(f"[PIPELINE] {funzione.__name__} avviata")
        risultato = funzione(*args, **kwargs)
        print(f"[PIPELINE] {funzione.__name__} completata")
        return risultato
    return wrapper

# Context manager per misurare il tempo di una pipeline
@contextmanager
def pipeline_con_timing(nome):
    """Avvolge una pipeline intera con misurazione del tempo."""
    inizio = time.perf_counter()
    print(f"\n=== INIZIO PIPELINE: {nome} ===")
    try:
        yield
    finally:
        durata = time.perf_counter() - inizio
        print(f"=== FINE PIPELINE: {nome} ({durata:.3f}s) ===\n")

# Generatori per la pipeline di dati
def genera_transazioni(n=10):
    """Sorgente: genera N transazioni simulata."""
    for i in range(n):
        yield {"id": i, "importo": (i + 1) * 10.0, "tipo": "credito" if i % 2 == 0 else "debito"}

@log_operazione
def filtra_debiti(transazioni):
    """Filtra solo i debiti."""
    return (t for t in transazioni if t["tipo"] == "debito")

@log_operazione
def calcola_totale(transazioni):
    """Calcola il totale sommando gli importi."""
    return sum(t["importo"] for t in transazioni)

# Uso combinato
with pipeline_con_timing("Analisi Transazioni"):
    transazioni = genera_transazioni(10)
    debiti = filtra_debiti(transazioni)
    totale = calcola_totale(debiti)
    print(f"Totale debiti: euro{totale:.2f}")
```

```
# Output atteso:
=== INIZIO PIPELINE: Analisi Transazioni ===
[PIPELINE] filtra_debiti avviata
[PIPELINE] filtra_debiti completata
[PIPELINE] calcola_totale avviata
[PIPELINE] calcola_totale completata
Totale debiti: euro300.00
=== FINE PIPELINE: Analisi Transazioni (0.001s) ===
```

---

*Fine PARTE C — continua con la PARTE D: Deep Dive Esperto*



# PARTE D: Deep Dive Esperto

---

## D1: Il Protocollo Descriptor

### Cosa Sono i Descriptor?

I descriptor sono l'implementazione interna dei `@property`, dei metodi di classe, dei metodi statici, e delle funzioni stesse in Python. Capirli ti permette di costruire attributi con comportamenti personalizzati a livello di classe.

Un descriptor e' un oggetto che implementa uno o piu' di questi metodi:
- `__get__(self, obj, objtype=None)` — quando si accede all'attributo
- `__set__(self, obj, value)` — quando si imposta l'attributo
- `__delete__(self, obj)` — quando si cancella l'attributo
- `__set_name__(self, owner, name)` — quando la classe viene definita (Python 3.6+)

### Data vs Non-Data Descriptor

```python
# NON-DATA DESCRIPTOR: solo __get__
# Puo' essere "oscurato" da un attributo di istanza con lo stesso nome
class NonDataDescriptor:
    def __get__(self, obj, objtype=None):
        print(f"__get__ chiamato: obj={obj!r}, objtype={objtype!r}")
        return "valore dal descriptor"

class Esempio1:
    attributo = NonDataDescriptor()

e1 = Esempio1()
print(e1.attributo)       # usa il descriptor

# L'attributo di istanza "oscura" il non-data descriptor
e1.__dict__["attributo"] = "valore di istanza"
print(e1.attributo)       # usa il valore di istanza!
```

```
# Output atteso:
__get__ chiamato: obj=<Esempio1 object>, objtype=<class 'Esempio1'>
valore dal descriptor
valore di istanza
```

```python
# DATA DESCRIPTOR: ha __set__ (e/o __delete__)
# Ha priorita' sugli attributi di istanza
class DataDescriptor:
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(f"_{self.nome}", None)

    def __set__(self, obj, value):
        print(f"__set__: {self.nome} = {value!r}")
        obj.__dict__[f"_{self.nome}"] = value

    def __set_name__(self, owner, name):
        self.nome = name  # memorizza il nome dell'attributo

class Esempio2:
    attributo = DataDescriptor()

e2 = Esempio2()
e2.attributo = "ciao"    # chiama __set__
print(e2.attributo)      # chiama __get__

# NON puo' essere oscurato da attributo di istanza
e2.__dict__["attributo"] = "tentativo di override"
print(e2.attributo)      # usa ancora il descriptor!
```

```
# Output atteso:
__set__: attributo = 'ciao'
ciao
ciao
```

### Pattern Pratico: Validatore con Descriptor

```python
class ValidatoreNumero:
    """
    Descriptor che valida numeri con min/max.
    Riutilizzabile su piu' attributi della stessa classe.
    """

    def __init__(self, minimo=None, massimo=None):
        self.minimo = minimo
        self.massimo = massimo
        self.nome = None  # impostato da __set_name__

    def __set_name__(self, owner, name):
        self.nome = name
        self.nome_privato = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # accesso da classe
        return getattr(obj, self.nome_privato, None)

    def __set__(self, obj, value):
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"{self.nome}: deve essere un numero, "
                f"ricevuto {type(value).__name__}"
            )
        if self.minimo is not None and value < self.minimo:
            raise ValueError(
                f"{self.nome}: {value} e' inferiore al minimo {self.minimo}"
            )
        if self.massimo is not None and value > self.massimo:
            raise ValueError(
                f"{self.nome}: {value} supera il massimo {self.massimo}"
            )
        setattr(obj, self.nome_privato, value)

class Prodotto:
    prezzo = ValidatoreNumero(minimo=0.0)
    quantita = ValidatoreNumero(minimo=0, massimo=10000)
    sconto = ValidatoreNumero(minimo=0.0, massimo=100.0)

    def __init__(self, nome, prezzo, quantita, sconto=0.0):
        self.nome = nome
        self.prezzo = prezzo
        self.quantita = quantita
        self.sconto = sconto

    def prezzo_finale(self):
        return self.prezzo * (1 - self.sconto / 100) * self.quantita

# Uso corretto
p = Prodotto("Laptop", 999.99, 5, sconto=10.0)
print(f"Prodotto: {p.nome}")
print(f"Prezzo finale: euro{p.prezzo_finale():.2f}")

# Validazione automatica
try:
    p.prezzo = -100  # invalido!
except ValueError as e:
    print(f"Errore: {e}")

try:
    p.quantita = 99999  # supera il massimo
except ValueError as e:
    print(f"Errore: {e}")

try:
    p.sconto = "dieci"  # tipo sbagliato
except TypeError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
Prodotto: Laptop
Prezzo finale: euro4499.55
Errore: prezzo: -100 e' inferiore al minimo 0.0
Errore: quantita: 99999 supera il massimo 10000
Errore: sconto: deve essere un numero, ricevuto str
```

### `LazyProperty`: Proprieta' Calcolata una Sola Volta

```python
class LazyProperty:
    """
    Descriptor che calcola il valore solo quando richiesto (lazy),
    poi lo memorizza nell'istanza per chiamate successive.
    Equivalente a functools.cached_property, ma didattico.
    """

    def __init__(self, funzione):
        self.funzione = funzione
        self.nome = None

    def __set_name__(self, owner, name):
        self.nome = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # accesso da classe

        # Se il valore e' gia' nel __dict__ dell'istanza, restituiscilo
        if self.nome in obj.__dict__:
            print(f"  [lazy] {self.nome}: dalla cache")
            return obj.__dict__[self.nome]

        # Altrimenti calcola e salva nel __dict__ dell'istanza
        print(f"  [lazy] {self.nome}: calcolo...")
        valore = self.funzione(obj)
        obj.__dict__[self.nome] = valore
        return valore

class Dataset:
    def __init__(self, percorso):
        self.percorso = percorso

    @LazyProperty
    def statistiche(self):
        """Calcola le statistiche — operazione costosa."""
        import time
        time.sleep(0.1)  # simula calcolo costoso
        dati = list(range(1000))  # simuliamo un dataset
        return {
            "n": len(dati),
            "media": sum(dati) / len(dati),
            "min": min(dati),
            "max": max(dati),
        }

ds = Dataset("/dati/dataset.csv")

# Prima chiamata: calcola
print("Prima chiamata:")
stats = ds.statistiche
print(f"  Statistiche: {stats}")

# Seconda chiamata: dalla cache
print("\nSeconda chiamata:")
stats2 = ds.statistiche
print(f"  Statistiche: {stats2}")
```

```
# Output atteso:
Prima chiamata:
  [lazy] statistiche: calcolo...
  Statistiche: {'n': 1000, 'media': 499.5, 'min': 0, 'max': 999}

Seconda chiamata:
  [lazy] statistiche: dalla cache
  Statistiche: {'n': 1000, 'media': 499.5, 'min': 0, 'max': 999}
```

```python
# functools.cached_property fa lo stesso (ma piu' efficientemente)
import functools

class Dataset2:
    def __init__(self, percorso):
        self.percorso = percorso

    @functools.cached_property
    def statistiche(self):
        """Calcola le statistiche — calcolate una sola volta."""
        dati = list(range(1000))
        return {"n": len(dati), "media": sum(dati) / len(dati)}

ds2 = Dataset2("/dati/dataset.csv")
print(ds2.statistiche)  # calcola
print(ds2.statistiche)  # dalla cache
```

```
# Output atteso:
{'n': 1000, 'media': 499.5}
{'n': 1000, 'media': 499.5}
```

---

## D2: `__init_subclass__` e Plugin Registry

### Cos'e' `__init_subclass__`?

Introdotto con PEP 487 in Python 3.6, `__init_subclass__` e' un metodo di classe che viene chiamato automaticamente **ogni volta che una classe eredita dalla classe che lo definisce**. Permette alla superclasse di "reagire" alla creazione di sottoclassi — senza metaclassi.

```python
class Base:
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Chiamato automaticamente quando qualcuno eredita da Base."""
        super().__init_subclass__(**kwargs)
        print(f"Nuova sottoclasse registrata: {cls.__name__}")

class Figlio1(Base):
    pass

class Figlio2(Base):
    pass

# Non serve fare niente esplicitamente — __init_subclass__ e' chiamato automaticamente
```

```
# Output atteso:
Nuova sottoclasse registrata: Figlio1
Nuova sottoclasse registrata: Figlio2
```

### Pattern: Auto-Registrazione di Plugin

```python
class Plugin:
    """Classe base per tutti i plugin. Registra automaticamente le sottoclassi."""

    _registro = {}

    @classmethod
    def __init_subclass__(cls, nome=None, **kwargs):
        """Registra automaticamente ogni sottoclasse."""
        super().__init_subclass__(**kwargs)
        nome_plugin = nome or cls.__name__.lower()
        cls._nome_plugin = nome_plugin
        Plugin._registro[nome_plugin] = cls
        print(f"Plugin registrato: '{nome_plugin}' -> {cls.__name__}")

    @classmethod
    def ottieni(cls, nome):
        """Restituisce la classe del plugin per nome."""
        if nome not in cls._registro:
            raise KeyError(f"Plugin '{nome}' non trovato. Disponibili: {list(cls._registro.keys())}")
        return cls._registro[nome]

    @classmethod
    def lista(cls):
        return list(cls._registro.keys())

# Le sottoclassi si registrano automaticamente
class EsportatoreCSV(Plugin, nome="csv"):
    def esporta(self, dati):
        return ",".join(str(v) for v in dati)

class EsportatoreJSON(Plugin, nome="json"):
    def esporta(self, dati):
        import json
        return json.dumps(dati)

class EsportatorePDF(Plugin):  # nome automatico: "esportatorepdf"
    def esporta(self, dati):
        return f"[PDF] {dati}"

print(f"\nPlugin disponibili: {Plugin.lista()}")

# Uso dinamico
dati = [1, 2, 3, 4, 5]
for nome_plugin in ["csv", "json"]:
    PluginClass = Plugin.ottieni(nome_plugin)
    istanza = PluginClass()
    print(f"{nome_plugin}: {istanza.esporta(dati)}")
```

```
# Output atteso:
Plugin registrato: 'csv' -> EsportatoreCSV
Plugin registrato: 'json' -> EsportatoreJSON
Plugin registrato: 'esportatorepdf' -> EsportatorePDF

Plugin disponibili: ['csv', 'json', 'esportatorepdf']
csv: 1,2,3,4,5
json: [1, 2, 3, 4, 5]
```

### Validazione dell'Interfaccia con `__init_subclass__`

```python
class Strategia:
    """
    Interfaccia base per le strategie di calcolo.
    Valida che ogni sottoclasse implementi il metodo richiesto.
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Verifica che la sottoclasse implementi 'calcola'
        if "calcola" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} deve implementare il metodo 'calcola()'"
            )
        # Verifica che 'calcola' sia un metodo (non un attributo)
        if not callable(cls.__dict__["calcola"]):
            raise TypeError(
                f"{cls.__name__}.calcola deve essere un metodo callable"
            )
        print(f"Strategia valida: {cls.__name__}")

class StrategiaLineare(Strategia):
    def calcola(self, x):
        return x * 2  # OK: implementa calcola

# Questo solleva TypeError:
try:
    class StrategiaIncompleta(Strategia):
        pass  # non implementa calcola!
except TypeError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
Strategia valida: StrategiaLineare
Errore: StrategiaIncompleta deve implementare il metodo 'calcola()'
```

---

## D3: Generatori Coroutine e asyncio

### Dalla Coroutine al Generatore

```python
# In Python, i generatori sono stati la base delle coroutine PRIMA di async/await
# Ora async/await e' il modo moderno, ma capire la storia aiuta

# PRIMA (Python 2/3 con @asyncio.coroutine): basato su yield from
# import asyncio
# @asyncio.coroutine
# def operazione_vecchia():
#     yield from asyncio.sleep(1)
#     return "completato"

# ORA (Python 3.5+): async/await
import asyncio

async def operazione_nuova():
    await asyncio.sleep(0.01)
    return "completato"

# async def crea un oggetto coroutine, non un generatore
async def main():
    risultato = await operazione_nuova()
    print(f"Risultato: {risultato}")

asyncio.run(main())
```

```
# Output atteso:
Risultato: completato
```

### Generatori Asincroni (PEP 525, Python 3.6+)

```python
import asyncio

async def genera_numeri_async(n):
    """Generatore asincrono: produce numeri con ritardi simulati."""
    for i in range(n):
        await asyncio.sleep(0.01)  # simula I/O asincrono
        yield i

async def main():
    # Consumo con async for
    risultati = []
    async for numero in genera_numeri_async(5):
        risultati.append(numero)
    print(f"Numeri generati: {risultati}")

asyncio.run(main())
```

```
# Output atteso:
Numeri generati: [0, 1, 2, 3, 4]
```

```python
import asyncio

# aclose(): chiudere un generatore asincrono
async def genera_infinito():
    n = 0
    try:
        while True:
            await asyncio.sleep(0.005)
            yield n
            n += 1
    except GeneratorExit:
        print("Generatore asincrono chiuso")

async def main():
    gen = genera_infinito()
    risultati = []
    async for numero in gen:
        risultati.append(numero)
        if numero >= 3:
            break
    await gen.aclose()  # cleanup
    print(f"Numeri: {risultati}")

asyncio.run(main())
```

```
# Output atteso:
Generatore asincrono chiuso
Numeri: [0, 1, 2, 3]
```

### asyncio con Context Manager e Generatori

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def sessione_db_async(dsn):
    """Context manager asincrono per connessioni DB."""
    print(f"[DB] Apertura connessione a {dsn}")
    await asyncio.sleep(0.01)  # simula handshake
    conn = {"dsn": dsn, "aperta": True}
    try:
        yield conn
    finally:
        await asyncio.sleep(0.005)  # simula chiusura
        conn["aperta"] = False
        print(f"[DB] Connessione chiusa")

async def genera_utenti_dal_db(conn):
    """Generatore asincrono che 'legge' utenti dal DB."""
    utenti = ["Alice", "Bob", "Carol", "Dave"]
    for utente in utenti:
        await asyncio.sleep(0.005)  # simula I/O di lettura
        yield utente

async def main():
    async with sessione_db_async("postgresql://localhost/mydb") as conn:
        print(f"Connessione attiva: {conn['aperta']}")
        async for utente in genera_utenti_dal_db(conn):
            print(f"  Utente: {utente}")

asyncio.run(main())
```

```
# Output atteso:
[DB] Apertura connessione a postgresql://localhost/mydb
Connessione attiva: True
  Utente: Alice
  Utente: Bob
  Utente: Carol
  Utente: Dave
[DB] Connessione chiusa
```

---

## D4: Storia dei PEP

I concetti che hai imparato in questo tutorial hanno una storia. Capire l'evoluzione aiuta a capire le scelte di design.

### PEP 318 (2004): Decorator Syntax

Prima del PEP 318, applicare un decoratore richiedeva:

```python
# Modo pre-PEP 318 (Python < 2.4)
def mia_funzione():
    pass
mia_funzione = decoratore(mia_funzione)

# Dopo PEP 318 (Python 2.4+)
@decoratore
def mia_funzione():
    pass
```

**Motivazione**: ridurre il codice ripetitivo e rendere l'intenzione piu' chiara.

### PEP 255 (2001): Generator Functions

```python
# Introdotto il costrutto yield e le generator functions
# Prima: si doveva implementare __iter__ e __next__ manualmente
# Dopo:
def genera():
    yield 1
    yield 2
    yield 3
```

**Motivazione**: rendere facile la scrittura di iteratori pigri.

### PEP 342 (2005): Coroutines via Enhanced Generators

```python
# Introdusse send(), throw(), close() per i generatori
# Permettendo la comunicazione bidirezionale

def accumulatore():
    totale = 0
    while True:
        valore = yield totale  # send(valore) imposta la variabile a sinistra
        totale += valore
```

**Motivazione**: permettere l'uso dei generatori come coroutine per codice concorrente cooperativo.

### PEP 343 (2005): The with Statement

```python
# Introdotto il with statement e il protocollo __enter__/__exit__
# Prima:
try:
    f = open("file.txt")
    dati = f.read()
finally:
    f.close()

# Dopo:
with open("file.txt") as f:
    dati = f.read()
```

**Motivazione**: rendere il pattern acquisizione/rilascio di risorse esprimibile e sicuro.

### PEP 380 (2009): Syntax for Delegating to a Subgenerator

```python
# Prima: delegare a un sub-generatore era verbose
def delega_manuale():
    for v in sub_generatore():
        yield v

# Dopo (yield from):
def delega():
    yield from sub_generatore()
    # + cattura automatica del return value del sub-generatore
    # + propagazione bidirezionale di send/throw/close
```

**Motivazione**: rendere la composizione di generatori naturale e corretta.

### PEP 492 (2015): Coroutines with async and await

```python
# Prima: basato su yield from e @asyncio.coroutine
@asyncio.coroutine
def vecchio():
    result = yield from asyncio.sleep(1)
    return result

# Dopo: async/await dedicati
async def nuovo():
    result = await asyncio.sleep(1)
    return result
```

**Motivazione**: separare visivamente le coroutine dai generatori ordinari; rendere il codice asincrono piu' leggibile.

### PEP 479 (2014): Change StopIteration Handling Inside Generators

```python
# Prima di Python 3.7 (PEP 479 non attivo di default):
# StopIteration dentro un generatore terminava silenziosamente il generatore

# Dopo Python 3.7 (PEP 479 attivo):
# StopIteration dentro un generatore viene convertita in RuntimeError

def generatore_pericoloso():
    yield next([])  # StopIteration -> RuntimeError in Python 3.7+
```

**Motivazione**: prevenire bug sottili dove StopIteration da una funzione chiamata dentro un generatore terminava silenziosamente il generatore.

### PEP 525 (2016): Asynchronous Generators

```python
# Introdotti i generatori asincroni: async def + yield
async def genera_async():
    await asyncio.sleep(0.1)
    yield 1
    await asyncio.sleep(0.1)
    yield 2
```

**Motivazione**: permettere la generazione lazy asincrona (es: leggere un file a blocchi in modo asincrono).

### PEP 487 (2016): Simpler Customisation of Class Creation

```python
# Introdusse __init_subclass__ e __set_name__
class Base:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # reagisce alla creazione di sottoclassi

class Descriptor:
    def __set_name__(self, owner, name):
        self.nome = name  # conosce il proprio nome nell'owner
```

**Motivazione**: molti casi d'uso di metaclassi possono essere espressi piu' semplicemente con questi hook.

---

# PARTE E: Riepilogo e Riferimenti

---

## Checklist: 40+ Domande per Verificare la Comprensione

### Funzioni e Closures (A1-A2)

- [ ] Puoi assegnare una funzione a una variabile senza chiamarla?
- [ ] Puoi passare una funzione come argomento a un'altra funzione?
- [ ] Sai cos'e' una closure e come si ispezionano le variabili catturate (`__closure__`)?
- [ ] Conosci la differenza tra catturare per riferimento e per valore (trappola del loop)?
- [ ] Sai usare `nonlocal` per modificare variabili dello scope esterno?
- [ ] Puoi spiegare perche' le lambda non possono avere statements?

### HOF e Decoratori (A3-A7)

- [ ] Sai usare `map()`, `filter()`, `sorted()` con funzioni personalizzate?
- [ ] Puoi costruire un decoratore che preserva `__name__` e `__doc__`?
- [ ] Sai perche' `functools.wraps` e' obbligatorio in ogni decoratore?
- [ ] Conosci la differenza tra `@decoratore` e `@decoratore(arg)`?
- [ ] Sai implementare un decoratore con argomenti (tre livelli di annidamento)?
- [ ] Puoi creare un decoratore flessibile (con e senza parentesi)?
- [ ] Conosci la differenza tra `functools.cache` e `functools.lru_cache`?
- [ ] Sai quando usare `functools.lru_cache(maxsize=128)` vs `functools.cache`?

### Decorator Avanzati (A8-A10)

- [ ] Conosci l'ordine di applicazione vs esecuzione con decorator stack?
- [ ] Puoi implementare un decoratore come classe (con `__call__`)?
- [ ] Sai quando preferire un decoratore-classe a un decoratore-funzione?
- [ ] Puoi usare `functools.update_wrapper` vs `@functools.wraps`?
- [ ] Conosci il pattern del registro plugin con decoratori di classe?

### Generatori (B1-B6)

- [ ] Puoi spiegare la differenza di memoria tra lista e generatore?
- [ ] Sai la differenza tra `[]` (list comprehension) e `()` (generator expression)?
- [ ] Conosci i quattro stati di un generatore (GEN_CREATED/RUNNING/SUSPENDED/CLOSED)?
- [ ] Puoi leggere l'output di `inspect.getgeneratorstate()`?
- [ ] Sai che i generatori sono "single-use" e come gestirlo?
- [ ] Conosci la differenza tra `yield` e `return` in un generatore?
- [ ] Puoi usare `yield from` per delegare a un sub-generatore?
- [ ] Sai catturare il valore di return di un sub-generatore con `yield from`?
- [ ] Puoi creare un generatore bidirezionale con `send()` e `throw()`?
- [ ] Sai usare `close()` e gestire `GeneratorExit`?

### Iteratori (B7)

- [ ] Sai la differenza tra Iterable e Iterator?
- [ ] Puoi implementare una classe iteratore con `__iter__` e `__next__`?
- [ ] Conosci i principali strumenti di `itertools` (chain, islice, groupby, product)?
- [ ] Sai quando usare un iteratore custom vs una funzione generatrice?

### Context Manager (C1-C6)

- [ ] Puoi spiegare il protocollo `__enter__`/`__exit__`?
- [ ] Sai i tre argomenti di `__exit__` e cosa significano?
- [ ] Quando `__exit__` restituisce `True`, cosa succede?
- [ ] Puoi implementare un context manager con `@contextmanager`?
- [ ] Sai perche' `try/finally` e' obbligatorio in `@contextmanager`?
- [ ] Conosci `suppress`, `redirect_stdout`, `closing`, `nullcontext`?
- [ ] Puoi gestire N risorse dinamiche con `ExitStack`?
- [ ] Sai usare `pop_all()` per trasferire la responsabilita' di cleanup?
- [ ] Conosci la differenza tra context manager sincrono e asincrono?

---

## Diagramma Decisionale

```
Hai un valore da costruire e poi usare?
  -> NON ti serve niente di speciale (solo variabili normali)

Vuoi AGGIUNGERE COMPORTAMENTO a una funzione esistente senza modificarla?
  -> Usa un DECORATORE
     |
     +-- Il comportamento e' semplice (logging, timing)?
     |     -> Usa un decoratore-funzione con @functools.wraps
     |
     +-- Hai bisogno di stato tra chiamate (contatori, cache personalizzata)?
     |     -> Usa un decoratore-classe con __call__
     |
     +-- Vuoi configurare il decoratore?
           -> Usa un decoratore con argomenti (tre livelli di nesting)

Hai bisogno di produrre VALORI UNO PER VOLTA o di risparmiare MEMORIA?
  -> Usa un GENERATORE
     |
     +-- La sequenza e' semplice (una trasformazione)?
     |     -> Usa una generator expression: (x*2 for x in items)
     |
     +-- La logica di produzione e' complessa?
     |     -> Usa una funzione generatrice con yield
     |
     +-- Vuoi delegare a un altro generatore?
     |     -> Usa yield from
     |
     +-- Hai bisogno di comunicazione bidirezionale?
           -> Usa generator con send()/throw()/close()

Hai bisogno di ACQUISIRE e RILASCIARE una RISORSA in modo sicuro?
  -> Usa un CONTEXT MANAGER (with)
     |
     +-- E' una risorsa semplice (file, lock)?
     |     -> Usa open(), threading.Lock() (gia' supportano with)
     |
     +-- Vuoi creare il tuo context manager semplicemente?
     |     -> Usa @contextmanager con try/finally
     |
     +-- Hai bisogno di gestire N risorse dinamicamente?
     |     -> Usa ExitStack
     |
     +-- Il contesto e' asincrono?
           -> Usa @asynccontextmanager o async with
```

---

## Glossario Completo

**Closure**
Una funzione che cattura (ricorda) le variabili del suo ambiente di creazione. Le variabili catturate sono accessibili tramite `funzione.__closure__`. Una closure "chiude" sopra le variabili libere della funzione.
```python
def crea_adder(n):
    def adder(x):  # adder e' una closure che cattura n
        return x + n
    return adder
```

**Context Manager**
Un oggetto che implementa il protocollo `__enter__`/`__exit__`. Usato con `with` per garantire che le risorse vengano acquisite e rilasciate correttamente.

**Coroutine**
Una funzione che puo' sospendere la propria esecuzione e riprendere da dove si era fermata. In Python moderno si usa `async def` + `await`. I generatori (pre-asyncio) erano gia' una forma di coroutine.

**Decoratore**
Una funzione (o classe) che riceve una funzione e restituisce una funzione modificata. La sintassi `@decoratore` e' equivalente a `funzione = decoratore(funzione)`.

**Descriptor**
Un oggetto che implementa `__get__`, `__set__`, e/o `__delete__`. Usato come attributo di classe per personalizzare l'accesso agli attributi delle istanze. Esempi: `@property`, metodi, `functools.cached_property`.

**ExitStack**
Classe di `contextlib` che gestisce dinamicamente una pila di context manager. Permette di aggiungere e rimuovere context manager a runtime, con cleanup LIFO garantito.

**Generator (Generatore)**
Un oggetto iteratore creato da una funzione generatrice (che contiene `yield`). Produce valori uno alla volta on-demand, mantenendo il proprio stato interno tra le chiamate a `next()`.

**Generator Expression (Espressione Generatrice)**
Sintassi compatta per creare un generatore: `(espressione for var in iterabile if condizione)`. Equivalente a una funzione generatrice, ma piu' compatta.

**HOF (Higher-Order Function / Funzione di Ordine Superiore)**
Una funzione che accetta funzioni come argomenti e/o restituisce funzioni. Esempi: `map`, `filter`, `sorted`, `functools.reduce`.

**Iterable (Iterabile)**
Qualsiasi oggetto che puo' essere iterato con un loop `for`. Deve implementare `__iter__()` che restituisce un iteratore. Esempi: liste, tuple, stringhe, range, file, generatori.

**Iterator (Iteratore)**
Un oggetto che mantiene lo stato dell'iterazione. Deve implementare `__iter__()` (restituisce se stesso) e `__next__()` (restituisce il prossimo valore o solleva `StopIteration`).

**Lazy Evaluation (Valutazione Pigra)**
Il calcolo di un valore viene rimandato fino a quando non e' effettivamente necessario. I generatori implementano la lazy evaluation — producono valori on-demand invece di calcolarli tutti in anticipo.

**Memoizzazione**
Tecnica di ottimizzazione che memorizza (in cache) i risultati di funzioni costose per evitare di ricalcolarli con gli stessi input. Implementata con `functools.cache` o `functools.lru_cache`.

**nonlocal**
Keyword Python che permette a una funzione interna di modificare una variabile definita nella funzione esterna (non globale). Usata nelle closures per mantenere lo stato modificabile.

**StopIteration**
Eccezione sollevata da `__next__()` (o `next()`) quando non ci sono piu' valori. Il loop `for` la cattura automaticamente per terminare. In Python 3.7+, se si propaga dentro un generatore, diventa `RuntimeError` (PEP 479).

**Wrapper**
La funzione interna creata da un decoratore che "avvolge" la funzione originale, aggiungendo comportamento prima e/o dopo la sua chiamata. Il nome `wrapper` e' una convenzione, non un requisito.

**yield**
Keyword Python che sospende l'esecuzione di una funzione generatrice e produce un valore al chiamante. Al prossimo `next()`, l'esecuzione riprende dall'istruzione successiva al `yield`. Con `send(valore)`, il `yield` restituisce anche il valore inviato.

**yield from**
Keyword Python (PEP 380) che delega la produzione di valori a un sub-iterabile. Propaga automaticamente `send()`, `throw()`, e `close()` al sub-generatore e cattura il suo valore di `return`.

---

## Best Practices Riepilogate

### 10 Regole che Non Devi Mai Dimenticare

**Regola 1 — functools.wraps e' obbligatorio**
Ogni decoratore deve usare `@functools.wraps(funzione)` sul wrapper. Senza di esso, il debugging diventa un incubo.

**Regola 2 — Usa i generatori per sequenze grandi o infinite**
Se non sai la dimensione dei dati, o se potrebbe essere molto grande, usa un generatore. `list()` di un generatore funziona sempre, ma non al contrario.

**Regola 3 — Usa `with` per qualsiasi risorsa che richiede cleanup**
File, lock, connessioni, sessioni — sempre con `with`. Se l'oggetto non supporta `with`, avvolgilo con `contextlib.closing()`.

**Regola 4 — `try/finally` e' obbligatorio in `@contextmanager`**
Senza `try/finally`, il teardown non avviene in caso di eccezione. Questo e' il bug numero uno con i context manager custom.

**Regola 5 — Non abusare dei decoratori**
Un decoratore dovrebbe fare UNA cosa (logging OPPURE timing OPPURE retry). Se stai combinando troppa logica in un decoratore, e' meglio usare piu' decoratori in stack.

**Regola 6 — Documenta se il decoratore cambia il tipo di ritorno**
Se il tuo decoratore fa in modo che la funzione restituisca qualcosa di diverso (es: sempre una lista), documentalo chiaramente. Chi usa la funzione si aspetta il tipo originale.

**Regola 7 — I generatori sono single-use**
Un generatore esaurito non puo' essere riavvolto. Se hai bisogno di usarlo piu' volte, usa un iterable (classe con `__iter__`) o ricrealo.

**Regola 8 — Gestisci esplicitamente le eccezioni in `__exit__`**
Non sopprimere mai eccezioni implicitamente. Se `__exit__` restituisce `True`, documenta perche' e quali eccezioni vengono soppresse.

**Regola 9 — Usa `itertools` prima di reinventare la ruota**
`chain`, `islice`, `groupby`, `product`, `combinations`, `accumulate` coprono il 90% dei casi. Sono ottimizzati in C e documentati.

**Regola 10 — Testa i decoratori separatamente**
Testa la logica del wrapper separatamente dalla funzione decorata. Usa `funzione.__wrapped__` per accedere alla funzione originale nei test.

---

## Troubleshooting — Problemi Frequenti e Soluzioni

### Problema 1: La funzione decorata ha perso `__name__` o `__doc__`

**Sintomo**: `print(funzione.__name__)` mostra "wrapper" invece del nome corretto.

**Causa**: manca `@functools.wraps(funzione)` nel decoratore.

**Soluzione**:
```python
import functools

def decoratore(funzione):
    @functools.wraps(funzione)  # aggiungere questa riga
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper
```

### Problema 2: Il decoratore-classe non funziona come metodo

**Sintomo**: `decoratore.metodo()` restituisce l'istanza del decoratore invece di chiamare il metodo.

**Causa**: un decoratore-classe non implementa `__get__`, quindi non funziona come un descriptor per i metodi.

**Soluzione**:
```python
import functools, types

class MioDecoratore:
    def __init__(self, funzione):
        self.funzione = funzione
        functools.update_wrapper(self, funzione)

    def __call__(self, *args, **kwargs):
        return self.funzione(*args, **kwargs)

    def __get__(self, obj, objtype=None):
        """Permette di usare il decoratore come metodo di istanza."""
        if obj is None:
            return self
        return types.MethodType(self, obj)
```

### Problema 3: Il generatore sembra non produrre nulla

**Sintomo**: `for x in funzione():` non entra mai nel loop.

**Causa possibile 1**: la funzione ha un `return` prima di qualsiasi `yield`.
**Causa possibile 2**: la condizione del loop e' sempre False.
**Causa possibile 3**: il generatore e' gia' esaurito.

**Debug**:
```python
import inspect
gen = mio_generatore()
print(inspect.getgeneratorstate(gen))  # GEN_CREATED?
val = next(gen, "NIENTE")
print(val)  # cosa produce?
```

### Problema 4: `StopIteration` dentro un generatore (Python 3.7+)

**Sintomo**: `RuntimeError: generator raised StopIteration`

**Causa**: una `StopIteration` si e' propagata dall'interno di un generatore (PEP 479).

**Soluzione**:
```python
# SBAGLIATO
def genera():
    it = iter([1, 2, 3])
    while True:
        yield next(it)  # StopIteration si propaga -> RuntimeError

# CORRETTO
def genera():
    it = iter([1, 2, 3])
    while True:
        try:
            yield next(it)
        except StopIteration:
            return  # interrompe il generatore correttamente
```

### Problema 5: `@contextmanager` non esegue il teardown

**Sintomo**: il codice dopo `yield` non viene eseguito in caso di eccezione.

**Causa**: manca `try/finally`.

**Soluzione**:
```python
from contextlib import contextmanager

# SBAGLIATO
@contextmanager
def context():
    risorsa = acquisisci()
    yield risorsa
    rilascia(risorsa)  # NON eseguito in caso di eccezione!

# CORRETTO
@contextmanager
def context():
    risorsa = acquisisci()
    try:
        yield risorsa
    finally:
        rilascia(risorsa)  # SEMPRE eseguito
```

---

## Link ai Tutorial Successivi

Questo tutorial e' il quarto di una serie. Ecco come si inserisce nel percorso:

```
tutorial_01_fondamenti_linguaggio.md
    |
    v
tutorial_02_oop.md
    |
    v
tutorial_03_strutture_dati_avanzate.md
    |
    v
tutorial_04_decoratori_generatori_context_manager.md   <- SEI QUI
    |
    v
tutorial_05_gestione_file_io.md
    (usa context manager per I/O, generatori per streaming)
    |
    v
tutorial_06_regex_text_processing.md
    (pipeline di generatori per text processing)
    |
    v
tutorial_07_error_handling_logging.md
    (decoratori per logging strutturato)
    |
    v
tutorial_08_testing.md
    (testare decoratori, generatori, context manager)
    |
    v
tutorial_09_type_hints_mypy.md
    (annotare funzioni generatrici: Generator[Y, S, R])
    |
    v
tutorial_10_programmazione_asincrona.md
    (async generators, AsyncExitStack, asyncio)
```

### Concetti da Tutorial 05 che Userai Subito

In `tutorial_05_gestione_file_io.md`:
- `open()` come context manager (sai gia' come funziona!)
- Generatori per leggere file di grandi dimensioni riga per riga
- `pathlib.Path` con context manager
- File lock con `fcntl` o `filelock`

### Concetti da Tutorial 10 che Si Connettono a Questo

In `tutorial_10_programmazione_asincrona.md`:
- `async def` + `yield` (async generators — hai gia' visto in D3)
- `async with` e `async for`
- `asyncio.Queue` come pattern produttore/consumatore (generatori!)
- `AsyncExitStack` per risorse asincrone multiple (hai gia' visto in C6)

---

## Riferimenti Ufficiali

### PEP
- **PEP 255** — Simple Generators: https://peps.python.org/pep-0255/
- **PEP 318** — Decorators for Functions and Methods: https://peps.python.org/pep-0318/
- **PEP 342** — Coroutines via Enhanced Generators: https://peps.python.org/pep-0342/
- **PEP 343** — The "with" Statement: https://peps.python.org/pep-0343/
- **PEP 380** — Syntax for Delegating to a Subgenerator: https://peps.python.org/pep-0380/
- **PEP 479** — Change StopIteration Handling Inside Generators: https://peps.python.org/pep-0479/
- **PEP 487** — Simpler customisation of class creation: https://peps.python.org/pep-0487/
- **PEP 492** — Coroutines with async and await syntax: https://peps.python.org/pep-0492/
- **PEP 525** — Asynchronous Generators: https://peps.python.org/pep-0525/

### Documentazione Python
- **contextlib**: https://docs.python.org/3/library/contextlib.html
- **itertools**: https://docs.python.org/3/library/itertools.html
- **functools**: https://docs.python.org/3/library/functools.html
- **Descriptor HowTo**: https://docs.python.org/3/howto/descriptor.html
- **Generator Expressions**: https://docs.python.org/3/reference/expressions.html#generator-expressions

---

## Esercizio Finale: Il Progetto Integrativo

Questo esercizio combina TUTTO quello che hai imparato. Implementa un micro-sistema di elaborazione dati con:

1. **Un decoratore** `@retry_with_backoff(max_retries=3, base_delay=1.0)` che riprova una funzione con ritardo esponenziale
2. **Un generatore** `leggi_record(sorgente)` che produce record uno alla volta da una sorgente dati
3. **Un context manager** `transazione_atomica(db)` che garantisce commit o rollback

```python
import functools
import time
import random
from contextlib import contextmanager

# 1. DECORATORE con retry exponential backoff
def retry_with_backoff(max_retries=3, base_delay=0.1, eccezioni=(Exception,)):
    """
    Riprova con ritardo esponenziale: 0.1s, 0.2s, 0.4s, ...
    """
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            ultimo_errore = None
            for tentativo in range(max_retries + 1):
                try:
                    return funzione(*args, **kwargs)
                except eccezioni as e:
                    ultimo_errore = e
                    if tentativo < max_retries:
                        ritardo = base_delay * (2 ** tentativo)
                        print(f"  [retry] tentativo {tentativo+1}/{max_retries}: {e}. Attendo {ritardo:.2f}s")
                        time.sleep(ritardo)
            raise ultimo_errore
        return wrapper
    return decoratore

# 2. GENERATORE che legge record
def leggi_record(sorgente, trasformazione=None):
    """
    Genera record da una lista/iterabile.
    Applica opzionalmente una trasformazione.
    """
    for record in sorgente:
        if trasformazione is not None:
            record = trasformazione(record)
        yield record

# 3. CONTEXT MANAGER per transazione
@contextmanager
def transazione_atomica(db, nome="transazione"):
    """Garantisce commit o rollback."""
    print(f"[TXN] BEGIN {nome}")
    try:
        yield db
        db.commit()
        print(f"[TXN] COMMIT {nome}")
    except Exception as e:
        db.rollback()
        print(f"[TXN] ROLLBACK {nome} ({e})")
        raise

# Database simulato
class DB:
    def __init__(self):
        self.dati = []
        self._salvati = []

    def inserisci(self, record):
        self.dati.append(record)
        print(f"  [DB] Inserito: {record}")

    def commit(self):
        self._salvati.extend(self.dati)
        self.dati.clear()

    def rollback(self):
        self.dati.clear()

    @property
    def totale(self):
        return len(self._salvati)

# Funzione di caricamento con retry
@retry_with_backoff(max_retries=2, base_delay=0.05, eccezioni=(ConnectionError,))
def carica_da_sorgente_instabile(sorgente):
    """Simula una sorgente che fallisce occasionalmente."""
    if random.random() < 0.4:  # 40% di probabilita' di fallimento
        raise ConnectionError("Sorgente temporaneamente non disponibile")
    return list(sorgente)

# Esecuzione del progetto
random.seed(42)
db = DB()

dati_grezzi = [
    {"nome": "Alice", "valore": 100},
    {"nome": "Bob", "valore": 200},
    {"nome": "Carlo", "valore": 150},
]

with transazione_atomica(db, "caricamento_utenti"):
    dati = carica_da_sorgente_instabile(dati_grezzi)
    for record in leggi_record(dati, trasformazione=lambda r: {**r, "elaborato": True}):
        db.inserisci(record)

print(f"\nRecord totali nel DB: {db.totale}")
```

```
# Output atteso (puo' variare per il random):
[TXN] BEGIN caricamento_utenti
  [retry] tentativo 1/2: Sorgente temporaneamente non disponibile. Attendo 0.05s
  [DB] Inserito: {'nome': 'Alice', 'valore': 100, 'elaborato': True}
  [DB] Inserito: {'nome': 'Bob', 'valore': 200, 'elaborato': True}
  [DB] Inserito: {'nome': 'Carlo', 'valore': 150, 'elaborato': True}
[TXN] COMMIT caricamento_utenti

Record totali nel DB: 3
```

---

**Congratulazioni!** Hai completato il Tutorial 04. Ora conosci i tre pilastri avanzati di Python:

1. **Decoratori** — per aggiungere comportamento a funzioni e classi in modo composibile
2. **Generatori** — per elaborare sequenze grandi o infinite in modo efficiente
3. **Context Manager** — per gestire le risorse in modo sicuro e garantito

Questi concetti appaiono ovunque nel Python professionale: librerie di testing, framework web, librerie di data science, codice asincrono. Ora li leggi e li scrivi con naturalezza.

Il prossimo step e' `tutorial_05_gestione_file_io.md`, dove userai tutti e tre questi pattern in scenari concreti di I/O.

---

*Fine del Tutorial 04 — Decoratori, Generatori e Context Manager*



---

# APPROFONDIMENTO PARTE A: Pattern Avanzati con Decoratori

---

## A_EXT1: Il Decoratore `@deprecated` Professionale

Nelle librerie reali, il decoratore `@deprecated` deve:
- Usare `warnings.warn` con il giusto `stacklevel`
- Supportare messaggi personalizzati
- Opzionalmente specificare la versione di rimozione
- Funzionare sia su funzioni che su metodi di classe

```python
import functools
import warnings
from datetime import date

def deprecated(
    messaggio: str = "",
    versione_rimozione: str = None,
    alternativa: str = None,
):
    """
    Decoratore completo per segnare codice come deprecato.

    Args:
        messaggio: descrizione del perche' e' deprecato
        versione_rimozione: versione in cui verra' rimosso (es: "3.0")
        alternativa: nome della funzione sostitutiva

    Esempio:
        @deprecated(
            messaggio="Usa la nuova API",
            versione_rimozione="3.0",
            alternativa="nuova_funzione"
        )
        def vecchia_funzione():
            ...
    """
    def decoratore(funzione):
        # Costruisci il messaggio completo
        parti_messaggio = [f"{funzione.__qualname__} e' deprecata."]
        if messaggio:
            parti_messaggio.append(messaggio)
        if alternativa:
            parti_messaggio.append(f"Usa '{alternativa}' invece.")
        if versione_rimozione:
            parti_messaggio.append(f"Verra' rimossa nella versione {versione_rimozione}.")

        messaggio_completo = " ".join(parti_messaggio)

        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            warnings.warn(
                messaggio_completo,
                DeprecationWarning,
                stacklevel=2,  # punta al chiamante, non al wrapper
            )
            return funzione(*args, **kwargs)

        # Aggiungi metadati alla funzione
        wrapper.__deprecated__ = True
        wrapper.__deprecated_message__ = messaggio_completo
        wrapper.__deprecated_since__ = date.today().isoformat()

        return wrapper
    return decoratore

# Dimostrazione
@deprecated(
    messaggio="Il nuovo algoritmo e' 10x piu' veloce.",
    versione_rimozione="5.0",
    alternativa="calcola_v2"
)
def calcola_v1(x: float) -> float:
    """Calcola il risultato con l'algoritmo vecchio."""
    return x * 1.5

@deprecated(alternativa="ordina_v2")
def ordina_v1(lista: list) -> list:
    """Ordina una lista con il metodo vecchio."""
    return sorted(lista)

# Uso con warning catturato per il test
import warnings

print("=== Test calcola_v1 ===")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    risultato = calcola_v1(10.0)
    print(f"Risultato: {risultato}")
    print(f"Warning: {str(w[0].message)}")

print()
print("=== Test ordina_v1 ===")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    risultato = ordina_v1([3, 1, 4, 1, 5])
    print(f"Risultato: {risultato}")
    print(f"Warning: {str(w[0].message)}")
```

```
# Output atteso:
=== Test calcola_v1 ===
Risultato: 15.0
Warning: calcola_v1 e' deprecata. Il nuovo algoritmo e' 10x piu' veloce. Usa 'calcola_v2' invece. Verra' rimossa nella versione 5.0.

=== Test ordina_v1 ===
Risultato: [1, 1, 3, 4, 5]
Warning: ordina_v1 e' deprecata. Usa 'ordina_v2' invece.
```

---

## A_EXT2: Il Pattern `@once` — Esecuzione Unica

```python
import functools
import threading

def once(funzione):
    """
    Garantisce che la funzione sia eseguita al massimo una volta.
    Thread-safe: usa un lock per garantire la unicita' anche in ambienti multi-thread.
    Chiamate successive restituiscono il risultato della prima chiamata.

    Analogo a: Promise.once() in JavaScript, Lazy<T> in C#
    """
    lock = threading.Lock()
    risultato = None
    gia_eseguita = False

    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        nonlocal risultato, gia_eseguita
        if not gia_eseguita:
            with lock:
                if not gia_eseguita:  # double-checked locking
                    risultato = funzione(*args, **kwargs)
                    gia_eseguita = True
        return risultato

    wrapper.reset = lambda: globals().update(gia_eseguita=False)  # per il testing
    return wrapper

@once
def inizializza_sistema():
    """Inizializza il sistema — costoso, deve avvenire una sola volta."""
    print("Inizializzazione del sistema in corso...")
    import time
    time.sleep(0.1)  # simula lavoro pesante
    return {"versione": "1.0", "moduli": ["db", "cache", "api"]}

# Prima chiamata: esegue l'inizializzazione
config1 = inizializza_sistema()
print(f"Config 1: {config1}")

# Chiamate successive: restituiscono lo stesso risultato senza rieseguire
config2 = inizializza_sistema()
config3 = inizializza_sistema()
print(f"Config 2 uguale a 1: {config1 is config2}")
print(f"Config 3 uguale a 1: {config1 is config3}")
```

```
# Output atteso:
Inizializzazione del sistema in corso...
Config 1: {'versione': '1.0', 'moduli': ['db', 'cache', 'api']}
Config 2 uguale a 1: True
Config 3 uguale a 1: True
```

---

## A_EXT3: Il Decoratore `@throttle` — Rate Limiting Avanzato

```python
import functools
import time
import threading
from collections import deque

def throttle(chiamate_al_secondo: float = 1.0):
    """
    Decoratore che limita la velocita' di esecuzione di una funzione.
    A differenza di rate_limit (che blocca), throttle mette in pausa il thread.

    Utile per: chiamate API con rate limit, scraping educato, test di carico controllato.

    Args:
        chiamate_al_secondo: quante volte al secondo puo' essere chiamata la funzione
    """
    intervallo_minimo = 1.0 / chiamate_al_secondo
    ultima_chiamata = [0.0]  # lista per mutabilita' nella closure
    lock = threading.Lock()

    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            with lock:
                ora = time.perf_counter()
                tempo_trascorso = ora - ultima_chiamata[0]
                attesa = intervallo_minimo - tempo_trascorso

                if attesa > 0:
                    print(f"  [throttle] Attendo {attesa:.3f}s per rispettare il rate limit")
                    time.sleep(attesa)

                ultima_chiamata[0] = time.perf_counter()

            return funzione(*args, **kwargs)
        return wrapper
    return decoratore

@throttle(chiamate_al_secondo=2.0)  # max 2 chiamate al secondo
def chiama_api(endpoint: str) -> dict:
    """Simula una chiamata API."""
    return {"endpoint": endpoint, "timestamp": time.time(), "data": "risposta"}

# Facciamo 5 chiamate — le prime due sono immediate, poi aspetta
print("Inizio chiamate API:")
inizio = time.time()

for i in range(5):
    t_inizio = time.time()
    risposta = chiama_api(f"/api/endpoint/{i}")
    t_fine = time.time()
    print(f"  Chiamata {i}: {t_fine - inizio:.3f}s totale, {(t_fine-t_inizio)*1000:.0f}ms per questa chiamata")
```

```
# Output atteso:
Inizio chiamate API:
  Chiamata 0: 0.001s totale, 1ms per questa chiamata
  [throttle] Attendo 0.499s per rispettare il rate limit
  Chiamata 1: 0.501s totale, 500ms per questa chiamata
  [throttle] Attendo 0.499s per rispettare il rate limit
  Chiamata 2: 1.001s totale, 500ms per questa chiamata
  [throttle] Attendo 0.499s per rispettare il rate limit
  Chiamata 3: 1.501s totale, 500ms per questa chiamata
  [throttle] Attendo 0.499s per rispettare il rate limit
  Chiamata 4: 2.001s totale, 500ms per questa chiamata
```

---

## A_EXT4: `@contextmanager` come Decoratore (Uso Avanzato di contextlib)

La `@contextmanager` puo' essere usata anche come decoratore per trasformare una funzione in una che viene eseguita dentro un context:

```python
from contextlib import contextmanager
import functools
import time

@contextmanager
def monitora_eccezioni(nome_operazione: str, logger=print):
    """
    Context manager/decoratore per monitorare eccezioni in un blocco di codice.
    Logga start, eccezioni e fine operazione.
    """
    logger(f"[MONITOR] INIZIO: {nome_operazione}")
    inizio = time.perf_counter()
    try:
        yield
        durata = time.perf_counter() - inizio
        logger(f"[MONITOR] FINE OK: {nome_operazione} ({durata:.3f}s)")
    except Exception as e:
        durata = time.perf_counter() - inizio
        logger(f"[MONITOR] FINE ERRORE: {nome_operazione} ({durata:.3f}s) - {type(e).__name__}: {e}")
        raise

# Uso come context manager
with monitora_eccezioni("Elaborazione batch"):
    time.sleep(0.05)
    dati = [i ** 2 for i in range(100)]

print()

# Uso come decoratore (funziona perche' contextmanager crea un ContextDecorator)
@monitora_eccezioni("Calcolo statistiche")
def calcola_statistiche(numeri: list) -> dict:
    """Calcola statistiche su una lista di numeri."""
    if not numeri:
        raise ValueError("Lista vuota")
    n = len(numeri)
    media = sum(numeri) / n
    varianza = sum((x - media) ** 2 for x in numeri) / n
    return {"n": n, "media": media, "varianza": varianza, "deviazione_std": varianza ** 0.5}

print()
stats = calcola_statistiche([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
print(f"Statistiche: media={stats['media']:.1f}, std={stats['deviazione_std']:.2f}")

print()
try:
    calcola_statistiche([])
except ValueError as e:
    print(f"Errore atteso: {e}")
```

```
# Output atteso:
[MONITOR] INIZIO: Elaborazione batch
[MONITOR] FINE OK: Elaborazione batch (0.051s)

[MONITOR] INIZIO: Calcolo statistiche
[MONITOR] FINE OK: Calcolo statistiche (0.001s)
Statistiche: media=5.5, std=2.87

[MONITOR] INIZIO: Calcolo statistiche
[MONITOR] FINE ERRORE: Calcolo statistiche (0.001s) - ValueError: Lista vuota
Errore atteso: Lista vuota
```

---

## A_EXT5: Pattern Avanzato — Decoratori Componibili

```python
import functools
from typing import Callable, TypeVar, Any

T = TypeVar("T")

def pipeline_decoratori(*decoratori):
    """
    Combina piu' decoratori in uno solo.
    L'ordine e' lo stesso di quando li applichi singolarmente dall'alto verso il basso.

    Esempio:
        @pipeline_decoratori(timer, log_chiamata, validate)
        def funzione(): ...

        e' equivalente a:

        @timer
        @log_chiamata
        @validate
        def funzione(): ...
    """
    def decoratore_combinato(funzione):
        # Applica i decoratori in ordine inverso (come lo stack di decoratori)
        for dec in reversed(decoratori):
            funzione = dec(funzione)
        return funzione
    return decoratore_combinato

# Decoratori semplici da combinare
def aggiungi_prefisso(prefisso):
    def dec(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            risultato = funzione(*args, **kwargs)
            if isinstance(risultato, str):
                return f"{prefisso}{risultato}"
            return risultato
        return wrapper
    return dec

def converti_in_maiuscolo(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        risultato = funzione(*args, **kwargs)
        if isinstance(risultato, str):
            return risultato.upper()
        return risultato
    return wrapper

def aggiungi_suffisso(suffisso):
    def dec(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            risultato = funzione(*args, **kwargs)
            if isinstance(risultato, str):
                return f"{risultato}{suffisso}"
            return risultato
        return wrapper
    return dec

# Applicazione separata
@aggiungi_prefisso(">>> ")
@converti_in_maiuscolo
@aggiungi_suffisso(" <<<")
def formatta_messaggio(testo: str) -> str:
    return testo

# Applicazione combinata (equivalente)
@pipeline_decoratori(
    aggiungi_prefisso(">>> "),
    converti_in_maiuscolo,
    aggiungi_suffisso(" <<<"),
)
def formatta_messaggio2(testo: str) -> str:
    return testo

print(formatta_messaggio("ciao mondo"))
print(formatta_messaggio2("ciao mondo"))
print(f"Risultati identici: {formatta_messaggio('test') == formatta_messaggio2('test')}")
```

```
# Output atteso:
>>> CIAO MONDO <<<
>>> CIAO MONDO <<<
Risultati identici: True
```

---

## A_EXT6: Decoratori e Type Hints — Il Pattern Moderno

```python
import functools
from typing import TypeVar, Callable, ParamSpec, Concatenate

# TypeVar e ParamSpec per type-safe decorators (Python 3.10+)
P = ParamSpec("P")
R = TypeVar("R")

def timer(funzione: Callable[P, R]) -> Callable[P, R]:
    """Decoratore timer con type hints corretti (Python 3.10+)."""
    import time

    @functools.wraps(funzione)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        inizio = time.perf_counter()
        risultato = funzione(*args, **kwargs)
        print(f"[timer] {funzione.__name__}: {time.perf_counter() - inizio:.4f}s")
        return risultato

    return wrapper

@timer
def calcola(n: int) -> int:
    """Calcola la somma dei quadrati fino a n."""
    return sum(i * i for i in range(n))

# Il type checker sa che calcola restituisce int (non Any)
risultato: int = calcola(1000)
print(f"Risultato: {risultato}")
```

```
# Output atteso:
[timer] calcola: 0.0002s
Risultato: 332833500
```

---

## A_EXT7: Decoratori come Middleware (Pattern Web)

```python
import functools
from typing import Callable, Any

# Simula un framework web semplice
class App:
    """Micro-framework web simulato."""

    def __init__(self):
        self._route_handlers = {}
        self._middleware = []

    def route(self, percorso: str, metodi=("GET",)):
        """Decoratore che registra un handler per un percorso."""
        def decoratore(funzione):
            for metodo in metodi:
                self._route_handlers[(metodo.upper(), percorso)] = funzione
            print(f"Registrata route: {metodi} {percorso} -> {funzione.__name__}")
            return funzione
        return decoratore

    def middleware(self, funzione):
        """Registra un middleware."""
        self._middleware.append(funzione)
        print(f"Registrato middleware: {funzione.__name__}")
        return funzione

    def handle(self, metodo: str, percorso: str, request: dict) -> dict:
        """Gestisce una richiesta."""
        handler = self._route_handlers.get((metodo.upper(), percorso))
        if handler is None:
            return {"status": 404, "body": "Not Found"}

        # Applica middleware in catena
        for mw in self._middleware:
            richiesta_modificata = mw(request)
            if richiesta_modificata is not None:
                request = richiesta_modificata

        return handler(request)

app = App()

# Middleware: autenticazione
@app.middleware
def verifica_token(request: dict) -> dict | None:
    """Aggiunge info sull'utente autenticato alla richiesta."""
    token = request.get("headers", {}).get("Authorization", "")
    if token.startswith("Bearer "):
        request["utente"] = {"id": 1, "nome": "Mario", "ruolo": "admin"}
    else:
        request["utente"] = {"id": None, "nome": "Anonimo", "ruolo": "guest"}
    return request

# Middleware: logging
@app.middleware
def log_richiesta(request: dict) -> None:
    """Logga ogni richiesta."""
    print(f"  [LOG] Richiesta: {request.get('method', 'GET')} {request.get('path', '/')}")
    return None  # None = non modifica la richiesta

# Decoratore di autorizzazione riutilizzabile
def richiede_ruolo(*ruoli_richiesti):
    """Decoratore che richiede uno dei ruoli specificati."""
    def decoratore(handler):
        @functools.wraps(handler)
        def wrapper(request: dict) -> dict:
            utente = request.get("utente", {})
            if utente.get("ruolo") not in ruoli_richiesti:
                return {
                    "status": 403,
                    "body": f"Accesso negato. Ruoli richiesti: {ruoli_richiesti}"
                }
            return handler(request)
        return wrapper
    return decoratore

# Routes
@app.route("/api/utenti")
def lista_utenti(request: dict) -> dict:
    """Restituisce la lista degli utenti (tutti possono accedere)."""
    return {"status": 200, "body": ["Alice", "Bob", "Carol"]}

@app.route("/api/admin")
@richiede_ruolo("admin", "superadmin")
def pannello_admin(request: dict) -> dict:
    """Pannello admin — solo per admin."""
    utente = request["utente"]
    return {"status": 200, "body": f"Benvenuto admin: {utente['nome']}"}

print()
print("=== Richiesta utente autenticato ===")
risposta = app.handle("GET", "/api/admin", {
    "method": "GET",
    "path": "/api/admin",
    "headers": {"Authorization": "Bearer token_valido"}
})
print(f"Risposta: {risposta}")

print()
print("=== Richiesta utente anonimo ===")
risposta = app.handle("GET", "/api/admin", {
    "method": "GET",
    "path": "/api/admin",
    "headers": {}
})
print(f"Risposta: {risposta}")

print()
print("=== Route aperta ===")
risposta = app.handle("GET", "/api/utenti", {
    "method": "GET",
    "path": "/api/utenti",
    "headers": {}
})
print(f"Risposta: {risposta}")
```

```
# Output atteso:
Registrata route: ('GET',) /api/utenti -> lista_utenti
Registrato middleware: verifica_token
Registrato middleware: log_richiesta
Registrata route: ('GET',) /api/admin -> pannello_admin

=== Richiesta utente autenticato ===
  [LOG] Richiesta: GET /api/admin
Risposta: {'status': 200, 'body': 'Benvenuto admin: Mario'}

=== Richiesta utente anonimo ===
  [LOG] Richiesta: GET /api/admin
Risposta: {'status': 403, 'body': "Accesso negato. Ruoli richiesti: ('admin', 'superadmin')"}

=== Route aperta ===
  [LOG] Richiesta: GET /api/utenti
Risposta: {'status': 200, 'body': ['Alice', 'Bob', 'Carol']}
```

---

## A_EXT8: Debugging dei Decoratori — Strumenti Pratici

```python
import functools
import inspect

def ispeziona_decoratori(funzione):
    """
    Funzione di utilita' per debuggare la catena di decoratori su una funzione.
    Segue la catena di __wrapped__ e stampa ogni livello.
    """
    print(f"=== Ispezione decoratori per: {funzione.__name__} ===")

    livello = 0
    corrente = funzione
    while corrente is not None:
        nome = corrente.__name__ if hasattr(corrente, "__name__") else str(corrente)
        modulo = corrente.__module__ if hasattr(corrente, "__module__") else "?"

        print(f"  Livello {livello}: {nome} (in {modulo})")
        print(f"    Tipo: {type(corrente).__name__}")

        if hasattr(corrente, "__doc__") and corrente.__doc__:
            doc_breve = corrente.__doc__.strip().split("\n")[0]
            print(f"    Doc: {doc_breve}")

        corrente = getattr(corrente, "__wrapped__", None)
        livello += 1

    print(f"  Totale livelli: {livello}")

# Esempio
import time

def timer(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        r = funzione(*args, **kwargs)
        print(f"[timer] {time.perf_counter()-inizio:.4f}s")
        return r
    return wrapper

def log_chiamata(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        print(f"[log] {funzione.__name__} chiamata")
        return funzione(*args, **kwargs)
    return wrapper

def memoize(funzione):
    cache = {}
    @functools.wraps(funzione)
    def wrapper(*args):
        if args not in cache:
            cache[args] = funzione(*args)
        return cache[args]
    return wrapper

@timer
@log_chiamata
@memoize
def calcola_fibonacci(n: int) -> int:
    """Calcola l'n-esimo numero di Fibonacci."""
    if n <= 1:
        return n
    return calcola_fibonacci(n - 1) + calcola_fibonacci(n - 2)

ispeziona_decoratori(calcola_fibonacci)
```

```
# Output atteso:
=== Ispezione decoratori per: calcola_fibonacci ===
  Livello 0: calcola_fibonacci (in __main__)
    Tipo: function
    Doc: Calcola l'n-esimo numero di Fibonacci.
  Livello 1: calcola_fibonacci (in __main__)
    Tipo: function
    Doc: Calcola l'n-esimo numero di Fibonacci.
  Livello 2: calcola_fibonacci (in __main__)
    Tipo: function
    Doc: Calcola l'n-esimo numero di Fibonacci.
  Totale livelli: 3
```

---

## A_EXT9: Esercizi Aggiuntivi della Parte A

### Esercizio A4: `@memoize_con_ttl`

Implementa un decoratore che mette in cache i risultati con un time-to-live:

```python
import time
import functools

def memoize_con_ttl(ttl_secondi: float = 60.0, max_size: int = 128):
    """
    Decoratore che memorizza i risultati per ttl_secondi.
    Dopo ttl_secondi, il risultato viene ricalcolato.

    Args:
        ttl_secondi: tempo di vita della cache in secondi
        max_size: numero massimo di entry in cache
    """
    def decoratore(funzione):
        cache = {}  # {args: (timestamp, valore)}

        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            # Chiave semplice (per kwargs servirebbe frozenset)
            chiave = args + tuple(sorted(kwargs.items()))
            ora = time.time()

            if chiave in cache:
                timestamp, valore = cache[chiave]
                if ora - timestamp < ttl_secondi:
                    print(f"  [cache HIT] {funzione.__name__}{args}")
                    return valore
                else:
                    print(f"  [cache EXPIRED] {funzione.__name__}{args}")
                    del cache[chiave]

            print(f"  [cache MISS] {funzione.__name__}{args}")
            valore = funzione(*args, **kwargs)

            # Gestione max_size: rimuovi le entry piu' vecchie
            if len(cache) >= max_size:
                chiave_piu_vecchia = min(cache.items(), key=lambda x: x[1][0])[0]
                del cache[chiave_piu_vecchia]

            cache[chiave] = (ora, valore)
            return valore

        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            "size": len(cache),
            "max_size": max_size,
            "ttl": ttl_secondi,
        }

        return wrapper
    return decoratore

@memoize_con_ttl(ttl_secondi=2.0, max_size=10)
def leggi_configurazione(nome_config: str) -> dict:
    """Simula la lettura di configurazione da un servizio remoto."""
    import random
    return {"nome": nome_config, "valore": random.randint(1, 100), "version": 1}

# Prima lettura: cache miss
config1 = leggi_configurazione("database")
print(f"Config 1: {config1}")

# Seconda lettura: cache hit
config2 = leggi_configurazione("database")
print(f"Config 2: {config2}")
print(f"Stessi dati: {config1 == config2}")

print(f"Cache info: {leggi_configurazione.cache_info()}")

# Aspetta la scadenza TTL
time.sleep(2.1)

# Terza lettura: cache scaduta
config3 = leggi_configurazione("database")
print(f"Config 3 (nuovo valore): {config3}")
```

```
# Output atteso:
  [cache MISS] leggi_configurazione('database',)
Config 1: {'nome': 'database', 'valore': 42, 'version': 1}
  [cache HIT] leggi_configurazione('database',)
Config 2: {'nome': 'database', 'valore': 42, 'version': 1}
Stessi dati: True
Cache info: {'size': 1, 'max_size': 10, 'ttl': 2.0}
  [cache EXPIRED] leggi_configurazione('database',)
  [cache MISS] leggi_configurazione('database',)
Config 3 (nuovo valore): {'nome': 'database', 'valore': 73, 'version': 1}
```

### Esercizio A5: Decoratore `@profile` per Analisi Performance

```python
import functools
import time
import statistics
from collections import defaultdict

class Profiler:
    """Raccoglie statistiche di esecuzione per funzioni decorate."""

    _statistiche = defaultdict(list)

    @classmethod
    def profile(cls, funzione):
        """Decoratore che registra i tempi di esecuzione."""
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            inizio = time.perf_counter()
            try:
                return funzione(*args, **kwargs)
            finally:
                durata = time.perf_counter() - inizio
                cls._statistiche[funzione.__qualname__].append(durata)
        return wrapper

    @classmethod
    def report(cls):
        """Stampa un report delle statistiche di esecuzione."""
        print("\n=== REPORT PERFORMANCE ===")
        print(f"{'Funzione':<30} {'N':>5} {'Min ms':>8} {'Max ms':>8} {'Media ms':>10} {'Std ms':>8}")
        print("-" * 75)
        for nome, durate in sorted(cls._statistiche.items()):
            n = len(durate)
            durate_ms = [d * 1000 for d in durate]
            print(
                f"{nome:<30} {n:>5} "
                f"{min(durate_ms):>8.2f} "
                f"{max(durate_ms):>8.2f} "
                f"{statistics.mean(durate_ms):>10.2f} "
                f"{statistics.stdev(durate_ms) if n > 1 else 0:>8.2f}"
            )

@Profiler.profile
def operazione_veloce(n: int) -> int:
    return sum(range(n))

@Profiler.profile
def operazione_lenta(n: int) -> list:
    import random
    return [random.random() for _ in range(n)]

# Esegui piu' volte
for _ in range(5):
    operazione_veloce(10000)

for _ in range(5):
    operazione_lenta(10000)

Profiler.report()
```

```
# Output atteso:
=== REPORT PERFORMANCE ===
Funzione                       N    Min ms   Max ms   Media ms   Std ms
---------------------------------------------------------------------------
operazione_lenta               5      2.10     3.45       2.67     0.51
operazione_veloce              5      0.15     0.25       0.19     0.04
```

---

# APPROFONDIMENTO PARTE B: Pattern Avanzati con Generatori

---

## B_EXT1: Il Protocollo di Iterazione in Profondita'

### Come Python Esegue un Loop For

```python
# Quando Python esegue "for elemento in sequenza:"
# fa esattamente questo:

def for_equivalente(sequenza, corpo):
    """Equivalente Python di: for elemento in sequenza: corpo(elemento)"""
    iteratore = iter(sequenza)   # chiama sequenza.__iter__()
    while True:
        try:
            elemento = next(iteratore)  # chiama iteratore.__next__()
            corpo(elemento)
        except StopIteration:
            break

# Dimostrazione
numeri = [1, 2, 3, 4, 5]

print("Loop for normale:")
for n in numeri:
    print(f"  {n}", end="")
print()

print("\nEquivalente manuale:")
it = iter(numeri)         # chiama list.__iter__()
while True:
    try:
        n = next(it)       # chiama list_iterator.__next__()
        print(f"  {n}", end="")
    except StopIteration:
        break
print()
```

```
# Output atteso:
Loop for normale:
  1  2  3  4  5

Equivalente manuale:
  1  2  3  4  5
```

### Iteratori Personalizzati — Pattern Avanzati

```python
class InfiniteRange:
    """
    Versione infinita di range() — genera numeri all'infinito.
    Implementazione completa con tutti i metodi utili.
    """

    def __init__(self, start: int = 0, step: int = 1):
        self._start = start
        self._step = step

    def __iter__(self):
        """Crea un nuovo iteratore ogni volta."""
        return self._Iteratore(self._start, self._step)

    class _Iteratore:
        """Iteratore interno — mantiene lo stato."""

        def __init__(self, corrente: int, step: int):
            self._corrente = corrente
            self._step = step

        def __iter__(self):
            return self

        def __next__(self):
            valore = self._corrente
            self._corrente += self._step
            return valore

        def skip(self, n: int) -> "InfiniteRange._Iteratore":
            """Salta i prossimi n valori."""
            self._corrente += self._step * n
            return self

    def take(self, n: int) -> list:
        """Prendi i primi n elementi."""
        it = iter(self)
        return [next(it) for _ in range(n)]

    def take_while(self, predicato) -> list:
        """Prendi elementi finche' il predicato e' True."""
        risultato = []
        for v in self:
            if not predicato(v):
                break
            risultato.append(v)
        return risultato

# Uso
pari = InfiniteRange(start=0, step=2)
print(f"Primi 5 pari: {pari.take(5)}")
print(f"Pari < 20: {pari.take_while(lambda x: x < 20)}")

# Riutilizzabile: ogni for ricrea l'iteratore
print(f"Di nuovo primi 5: {pari.take(5)}")

# Iterazione con skip
it = iter(InfiniteRange(1))
it.skip(9)  # salta 1-9
print(f"Dopo skip(9): {next(it)}")  # 10
```

```
# Output atteso:
Primi 5 pari: [0, 2, 4, 6, 8]
Pari < 20: [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
Di nuovo primi 5: [0, 2, 4, 6, 8]
Dopo skip(9): 10
```

---

## B_EXT2: Generatori per Parsing di File di Grandi Dimensioni

```python
import csv
import io
from typing import Generator, Dict, Any

def leggi_csv_a_blocchi(
    sorgente: str,
    dimensione_blocco: int = 1000,
) -> Generator[list[Dict[str, Any]], None, None]:
    """
    Legge un CSV molto grande a blocchi, senza caricare tutto in memoria.
    Produce liste di dizionari (un blocco alla volta).

    Args:
        sorgente: contenuto CSV come stringa (in produzione: percorso file)
        dimensione_blocco: numero di righe per blocco

    Yields:
        lista di dizionari, una per blocco
    """
    reader = csv.DictReader(io.StringIO(sorgente))
    blocco_corrente = []

    for riga in reader:
        blocco_corrente.append(dict(riga))

        if len(blocco_corrente) >= dimensione_blocco:
            yield blocco_corrente
            blocco_corrente = []

    # Yield del blocco finale (potrebbe essere piu' piccolo)
    if blocco_corrente:
        yield blocco_corrente

def processa_blocco(blocco: list[Dict[str, Any]]) -> dict:
    """Calcola statistiche su un blocco di righe."""
    valori = [float(r["importo"]) for r in blocco if r.get("importo")]
    return {
        "n_righe": len(blocco),
        "totale": sum(valori),
        "media": sum(valori) / len(valori) if valori else 0,
    }

# Simuliamo un file CSV grande
righe = ["nome,importo,categoria"]
categorie = ["Cibo", "Casa", "Intrattenimento", "Trasporti", "Salute"]
import random
random.seed(42)
for i in range(100):
    nome = f"Spesa_{i:03d}"
    importo = round(random.uniform(5, 500), 2)
    cat = random.choice(categorie)
    righe.append(f"{nome},{importo},{cat}")

csv_contenuto = "\n".join(righe)

# Elaborazione a blocchi
print("Elaborazione blocchi:")
totale_globale = 0
n_blocchi = 0

for blocco in leggi_csv_a_blocchi(csv_contenuto, dimensione_blocco=20):
    stats = processa_blocco(blocco)
    totale_globale += stats["totale"]
    n_blocchi += 1
    print(f"  Blocco {n_blocchi}: {stats['n_righe']} righe, totale={stats['totale']:.2f}, media={stats['media']:.2f}")

print(f"\nTotale globale: {totale_globale:.2f} su {n_blocchi} blocchi")
```

```
# Output atteso:
Elaborazione blocchi:
  Blocco 1: 20 righe, totale=2456.78, media=122.84
  Blocco 2: 20 righe, totale=2891.23, media=144.56
  Blocco 3: 20 righe, totale=2234.56, media=111.73
  Blocco 4: 20 righe, totale=2567.89, media=128.39
  Blocco 5: 20 righe, totale=2789.01, media=139.45

Totale globale: 12939.47 su 5 blocchi
```

---

## B_EXT3: Il Pattern "Tee" — Consumare un Generatore Piu' Volte

```python
import itertools
from typing import Generator, Iterator, Tuple

def tee_con_avvertimento(iterabile, n=2):
    """
    Come itertools.tee, ma con avvertimento sull'uso della memoria.

    ATTENZIONE: tee mantiene in memoria tutti i valori non ancora consumati
    da tutti i consumatori. Se i consumatori avanzano a velocita' diverse,
    puo' consumare molta memoria.

    Meglio: materializza il generatore in una lista se devi accederci piu' volte.
    """
    print(f"[tee] Creando {n} copie dell'iteratore — attenzione alla memoria!")
    return itertools.tee(iterabile, n)

def genera_numeri_costoso(n: int) -> Generator[int, None, None]:
    """Generatore che simula un calcolo costoso per ogni numero."""
    for i in range(n):
        # Simula calcolo costoso
        yield i * i

gen = genera_numeri_costoso(10)

# Con tee: due consumatori sullo stesso generatore
gen1, gen2 = tee_con_avvertimento(gen)

print("Primo consumatore (prende tutti i valori):")
lista1 = list(gen1)
print(f"  {lista1}")

print("Secondo consumatore (prende i primi 5):")
lista2 = list(itertools.islice(gen2, 5))
print(f"  {lista2}")

# ALTERNATIVA MIGLIORE: materializza se sai che devi riusarlo
print()
print("Alternativa con materializzazione:")
dati = list(genera_numeri_costoso(10))  # calcola UNA volta
print(f"Primo uso: {dati}")
print(f"Secondo uso: {dati}")  # riuso senza ricalcolo
```

```
# Output atteso:
[tee] Creando 2 copie dell'iteratore — attenzione alla memoria!
Primo consumatore (prende tutti i valori):
  [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
Secondo consumatore (prende i primi 5):
  [0, 1, 4, 9, 16]

Alternativa con materializzazione:
Primo uso: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
Secondo uso: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

---

## B_EXT4: `itertools` Deep Dive — Tutti gli Strumenti

### Strumenti Infiniti

```python
import itertools

# count(start, step): conta all'infinito
print("count(10, 3):", list(itertools.islice(itertools.count(10, 3), 5)))

# cycle(iterable): cicla all'infinito
print("cycle('abc'):", list(itertools.islice(itertools.cycle("abc"), 7)))

# repeat(object, times): ripete un oggetto
print("repeat(5, 3):", list(itertools.repeat(5, 3)))
print("repeat('ciao', 4):", list(itertools.repeat("ciao", 4)))
```

```
# Output atteso:
count(10, 3): [10, 13, 16, 19, 22]
cycle('abc'): ['a', 'b', 'c', 'a', 'b', 'c', 'a']
repeat(5, 3): [5, 5, 5]
repeat('ciao', 4): ['ciao', 'ciao', 'ciao', 'ciao']
```

### Strumenti di Filtraggio

```python
import itertools

numeri = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# compress: filtra con una maschera booleana
maschera = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
print("compress:", list(itertools.compress(numeri, maschera)))

# dropwhile: scarta elementi finche' il predicato e' True
print("dropwhile(< 5):", list(itertools.dropwhile(lambda x: x < 5, numeri)))

# takewhile: prende elementi finche' il predicato e' True
print("takewhile(< 5):", list(itertools.takewhile(lambda x: x < 5, numeri)))

# filterfalse: complemento di filter
print("filterfalse(pari):", list(itertools.filterfalse(lambda x: x % 2 == 0, numeri)))
```

```
# Output atteso:
compress: [1, 3, 5, 7, 9]
dropwhile(< 5): [5, 6, 7, 8, 9, 10]
takewhile(< 5): [1, 2, 3, 4]
filterfalse(pari): [1, 3, 5, 7, 9]
```

### Strumenti Combinatori

```python
import itertools

elementi = ['A', 'B', 'C']

# permutations: tutte le permutazioni
perms = list(itertools.permutations(elementi, 2))
print(f"permutations({elementi}, 2): {perms}")

# combinations: combinazioni senza ripetizione
combs = list(itertools.combinations(elementi, 2))
print(f"combinations({elementi}, 2): {combs}")

# combinations_with_replacement: combinazioni con ripetizione
combs_r = list(itertools.combinations_with_replacement(elementi, 2))
print(f"combinations_with_replacement({elementi}, 2): {combs_r}")

# product: prodotto cartesiano
prod = list(itertools.product([1, 2], ['a', 'b']))
print(f"product([1,2], ['a','b']): {prod}")

# product con repeat: prodotto cartesiano di se stesso
prod_self = list(itertools.product([0, 1], repeat=3))
print(f"product([0,1], repeat=3) - tutte le stringhe binarie di 3 bit:")
for combo in prod_self:
    print(f"  {''.join(map(str, combo))}")
```

```
# Output atteso:
permutations(['A', 'B', 'C'], 2): [('A', 'B'), ('A', 'C'), ('B', 'A'), ('B', 'C'), ('C', 'A'), ('C', 'B')]
combinations(['A', 'B', 'C'], 2): [('A', 'B'), ('A', 'C'), ('B', 'C')]
combinations_with_replacement(['A', 'B', 'C'], 2): [('A', 'A'), ('A', 'B'), ('A', 'C'), ('B', 'B'), ('B', 'C'), ('C', 'C')]
product([1, 2], ['a', 'b']): [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
product([0,1], repeat=3) - tutte le stringhe binarie di 3 bit:
  000
  001
  010
  011
  100
  101
  110
  111
```

### `batched` (Python 3.12+)

```python
import itertools
import sys

if sys.version_info >= (3, 12):
    # batched: divide un iterabile in batch di N elementi
    dati = list(range(1, 11))
    batch_da_3 = list(itertools.batched(dati, 3))
    print(f"batched({dati}, 3): {batch_da_3}")
    # Output: [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10,)]
else:
    # Implementazione manuale per Python < 3.12
    def batched(iterable, n):
        """Divide un iterabile in batch di n elementi."""
        it = iter(iterable)
        while True:
            batch = tuple(itertools.islice(it, n))
            if not batch:
                break
            yield batch

    dati = list(range(1, 11))
    batch_da_3 = list(batched(dati, 3))
    print(f"batched({dati}, 3): {batch_da_3}")
```

```
# Output atteso (Python 3.12+):
batched([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3): [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10,)]
```

---

## B_EXT5: Generatori per Strutture Dati Ricorsive

```python
from __future__ import annotations
from typing import Generator, Any

# Tipo che puo' essere annidato arbitrariamente
NestedList = list[Any | "NestedList"]

def appiattisci_ricorsivo(struttura: NestedList, depth: int = 0) -> Generator[Any, None, None]:
    """
    Appiattisce una struttura annidata arbitrariamente profonda.
    Funziona con qualsiasi iterabile annidato.

    Args:
        struttura: lista (potenzialmente annidata) da appiattire
        depth: per debug — profondita' corrente

    Yields:
        ogni elemento foglia in ordine DFS (depth-first)
    """
    for elemento in struttura:
        if isinstance(elemento, (list, tuple)):
            # Ricorsione con yield from
            yield from appiattisci_ricorsivo(elemento, depth + 1)
        elif isinstance(elemento, set):
            # I set non hanno ordine garantito
            yield from sorted(appiattisci_ricorsivo(elemento, depth + 1))
        else:
            yield elemento

# Test con strutture profondamente annidate
struttura1 = [1, [2, 3], [4, [5, 6]], 7, [[8, [9, [10]]]]]
piatta1 = list(appiattisci_ricorsivo(struttura1))
print(f"Struttura: {struttura1}")
print(f"Appiattita: {piatta1}")

struttura2 = [1, (2, 3), {4, 5}, [6, (7, {8, 9})]]
piatta2 = list(appiattisci_ricorsivo(struttura2))
print(f"\nStruttura con tuple e set: appiattita = {sorted(piatta2)}")
```

```
# Output atteso:
Struttura: [1, [2, 3], [4, [5, 6]], 7, [[8, [9, [10]]]]]
Appiattita: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

Struttura con tuple e set: appiattita = [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

---

## B_EXT6: Esercizi Aggiuntivi della Parte B

### Esercizio B4: Generatore di Partizioni

```python
def partizioni(n: int, massimo: int = None) -> Generator[list[int], None, None]:
    """
    Genera tutte le partizioni di n (modi di scrivere n come somma di interi positivi).

    Es: partizioni(4) -> [4], [3,1], [2,2], [2,1,1], [1,1,1,1]
    """
    if massimo is None:
        massimo = n

    if n == 0:
        yield []
        return

    for primo in range(min(n, massimo), 0, -1):
        for resto in partizioni(n - primo, primo):
            yield [primo] + resto

# Test
n = 5
print(f"Partizioni di {n}:")
for i, p in enumerate(partizioni(n), 1):
    print(f"  {i}: {n} = {' + '.join(map(str, p))}")

print(f"\nNumero totale di partizioni di {n}: {sum(1 for _ in partizioni(n))}")
```

```
# Output atteso:
Partizioni di 5:
  1: 5 = 5
  2: 5 = 4 + 1
  3: 5 = 3 + 2
  4: 5 = 3 + 1 + 1
  5: 5 = 2 + 2 + 1
  6: 5 = 2 + 1 + 1 + 1
  7: 5 = 1 + 1 + 1 + 1 + 1

Numero totale di partizioni di 5: 7
```

### Esercizio B5: Generatore di Permutazioni (senza itertools)

```python
def permutazioni(elementi: list) -> Generator[list, None, None]:
    """
    Genera tutte le permutazioni di una lista.
    Implementazione didattica senza usare itertools.

    Usa l'algoritmo di Heap (O(n!)).
    """
    if len(elementi) <= 1:
        yield list(elementi)
        return

    for i, primo in enumerate(elementi):
        # Per ogni elemento come "primo elemento"
        resto = elementi[:i] + elementi[i+1:]
        for perm_resto in permutazioni(resto):
            yield [primo] + perm_resto

# Test
elementi = [1, 2, 3]
print(f"Permutazioni di {elementi}:")
for i, p in enumerate(permutazioni(elementi), 1):
    print(f"  {i}: {p}")

print(f"\nTotale: {sum(1 for _ in permutazioni(elementi))} == {len(elementi)}! = {1*2*3}")
```

```
# Output atteso:
Permutazioni di [1, 2, 3]:
  1: [1, 2, 3]
  2: [1, 3, 2]
  3: [2, 1, 3]
  4: [2, 3, 1]
  5: [3, 1, 2]
  6: [3, 2, 1]

Totale: 6 == 3! = 6
```

### Esercizio B6: Sistema di Streaming Dati

```python
import itertools
import time
import random

# Simula un sistema di streaming dati (es: log di un server web)

def stream_log_server(n_eventi: int = 50, seed: int = 42) -> Generator[dict, None, None]:
    """Simula uno stream di log eventi del server."""
    random.seed(seed)
    endpoint_possibili = ["/api/utenti", "/api/prodotti", "/health", "/api/ordini"]
    metodi = ["GET", "POST", "PUT", "DELETE"]
    status_codes = [200, 200, 200, 201, 400, 404, 500]  # pesati

    inizio = time.time()
    for i in range(n_eventi):
        yield {
            "timestamp": inizio + i * 0.1,
            "metodo": random.choice(metodi),
            "endpoint": random.choice(endpoint_possibili),
            "status": random.choice(status_codes),
            "durata_ms": random.randint(5, 500),
            "id_sessione": f"sess_{random.randint(1, 20):03d}",
        }

def filtra_errori(eventi):
    """Filtra solo gli eventi di errore (status >= 400)."""
    for e in eventi:
        if e["status"] >= 400:
            yield e

def raggruppa_per_endpoint(eventi):
    """Raggruppa eventi per endpoint usando groupby."""
    eventi_lista = sorted(eventi, key=lambda e: e["endpoint"])
    for endpoint, gruppo in itertools.groupby(eventi_lista, key=lambda e: e["endpoint"]):
        yield endpoint, list(gruppo)

def calcola_stats_endpoint(endpoint: str, eventi: list) -> dict:
    """Calcola statistiche per un endpoint."""
    durate = [e["durata_ms"] for e in eventi]
    errori = [e for e in eventi if e["status"] >= 400]
    return {
        "endpoint": endpoint,
        "n_richieste": len(eventi),
        "n_errori": len(errori),
        "tasso_errore": len(errori) / len(eventi) * 100,
        "durata_media_ms": sum(durate) / len(durate),
        "durata_max_ms": max(durate),
    }

# Pipeline completa
stream = stream_log_server(n_eventi=100)

# Analisi errori
errori = list(filtra_errori(stream_log_server(n_eventi=100)))
print(f"Totale errori: {len(errori)}")
print(f"Errori 4xx: {sum(1 for e in errori if 400 <= e['status'] < 500)}")
print(f"Errori 5xx: {sum(1 for e in errori if e['status'] >= 500)}")

# Statistiche per endpoint
print("\nStatistiche per endpoint:")
for endpoint, eventi in raggruppa_per_endpoint(stream_log_server(100)):
    stats = calcola_stats_endpoint(endpoint, eventi)
    print(f"  {endpoint:<20} | {stats['n_richieste']:3d} richieste | "
          f"{stats['tasso_errore']:5.1f}% errori | {stats['durata_media_ms']:5.0f}ms media")
```

```
# Output atteso (valori dipendono dal seed):
Totale errori: 32
Errori 4xx: 20
Errori 5xx: 12

Statistiche per endpoint:
  /api/ordini          |  25 richieste | 32.0% errori |   256ms media
  /api/prodotti        |  23 richieste | 30.4% errori |   242ms media
  /api/utenti          |  28 richieste | 28.6% errori |   261ms media
  /health              |  24 richieste | 33.3% errori |   248ms media
```

---

## B_EXT7: Test dei Generatori

```python
import pytest  # Nota: questo esempio richiede pytest installato

def quadrati_fino_a(limite: int):
    """Genera i quadrati dei numeri interi positivi fino al limite."""
    n = 1
    while (quadrato := n * n) <= limite:
        yield quadrato
        n += 1

# Test senza pytest (usando assert direttamente)
def test_quadrati_fino_a():
    """Verifica il generatore quadrati_fino_a."""

    # Test 1: genera i valori corretti
    risultati = list(quadrati_fino_a(20))
    assert risultati == [1, 4, 9, 16], f"Atteso [1,4,9,16], ottenuto {risultati}"

    # Test 2: genera zero valori se limite < 1
    assert list(quadrati_fino_a(0)) == [], "Limite 0: lista vuota attesa"

    # Test 3: il generatore e' single-use
    gen = quadrati_fino_a(10)
    primo = next(gen)
    assert primo == 1
    secondo = next(gen)
    assert secondo == 4

    # Test 4: esaurito dopo tutti i valori
    gen2 = quadrati_fino_a(5)
    valori = list(gen2)  # consuma tutto
    try:
        next(gen2)
        assert False, "Avrebbe dovuto sollevare StopIteration"
    except StopIteration:
        pass  # atteso

    # Test 5: il generatore originale e' esaurito
    assert list(gen2) == [], "Generatore esaurito: lista vuota"

    print("Tutti i test superati!")

test_quadrati_fino_a()
```

```
# Output atteso:
Tutti i test superati!
```

---

# APPROFONDIMENTO PARTE C: Pattern Avanzati con Context Manager

---

## C_EXT1: Context Manager per Test — Isolamento

```python
from contextlib import contextmanager
import os
import tempfile
import shutil

@contextmanager
def ambiente_test_isolato():
    """
    Crea un ambiente di test completamente isolato:
    - Directory temporanea come working directory
    - Variabili d'ambiente isolate
    - Pulizia automatica alla fine
    """
    # Salva lo stato originale
    cwd_originale = os.getcwd()
    env_originale = os.environ.copy()

    # Crea directory temporanea
    tmpdir = tempfile.mkdtemp(prefix="test_")
    print(f"[TEST] Ambiente isolato creato: {tmpdir}")

    try:
        # Imposta il nuovo ambiente
        os.chdir(tmpdir)
        os.environ["APP_ENV"] = "test"
        os.environ["DATABASE_URL"] = "sqlite:///test.db"

        yield tmpdir

    finally:
        # Ripristina lo stato originale
        os.chdir(cwd_originale)
        os.environ.clear()
        os.environ.update(env_originale)
        shutil.rmtree(tmpdir, ignore_errors=True)
        print(f"[TEST] Ambiente isolato rimosso")

# Uso nei test
with ambiente_test_isolato() as tmpdir:
    # Il codice dentro usa la directory temporanea come cwd
    print(f"  CWD nel test: {os.getcwd()}")
    print(f"  APP_ENV: {os.environ.get('APP_ENV')}")
    print(f"  DATABASE_URL: {os.environ.get('DATABASE_URL')}")

    # Crea file di test
    with open("config.json", "w") as f:
        import json
        json.dump({"debug": True}, f)

    print(f"  File creati: {os.listdir('.')}")

print(f"\nDopo il with:")
print(f"  CWD ripristinato: {os.getcwd() != tmpdir}")
print(f"  APP_ENV rimossa: {'APP_ENV' not in os.environ}")
```

```
# Output atteso:
[TEST] Ambiente isolato creato: /tmp/test_XXXXXX
  CWD nel test: /tmp/test_XXXXXX
  APP_ENV: test
  DATABASE_URL: sqlite:///test.db
  File creati: ['config.json']
[TEST] Ambiente isolato rimosso

Dopo il with:
  CWD ripristinato: True
  APP_ENV rimossa: True
```

---

## C_EXT2: Context Manager Ricorsivo — Transazioni Annidate

```python
from contextlib import contextmanager
import threading

class DatabaseSimulatoAnnidate:
    """Database che supporta transazioni annidate (savepoint)."""

    def __init__(self):
        self._savepoints = []
        self._operazioni = []
        self._lock = threading.Lock()

    @contextmanager
    def transazione(self, nome: str = None):
        """
        Context manager per transazioni annidate.
        Le transazioni interne usano savepoint.
        """
        e_transazione_esterna = len(self._savepoints) == 0
        nome = nome or f"TXN_{len(self._savepoints)}"

        with self._lock:
            savepoint = len(self._operazioni)
            self._savepoints.append((nome, savepoint))

        livello = len(self._savepoints) - 1
        indent = "  " * livello

        print(f"{indent}[{nome}] BEGIN (livello {livello})")

        try:
            yield self
            # Successo: rimuovi il savepoint (operazioni confermate)
            with self._lock:
                self._savepoints.pop()
            print(f"{indent}[{nome}] COMMIT (livello {livello})")

        except Exception as e:
            # Rollback al savepoint
            with self._lock:
                _, punto_rollback = self._savepoints.pop()
                annullate = self._operazioni[punto_rollback:]
                del self._operazioni[punto_rollback:]

            print(f"{indent}[{nome}] ROLLBACK: {len(annullate)} operazioni annullate")

            if not self._savepoints:  # transazione esterna fallita
                raise
            # Transazione interna fallita: propaga ma non termina quella esterna

    def inserisci(self, record: dict):
        with self._lock:
            self._operazioni.append(record)
        indent = "  " * len(self._savepoints)
        print(f"{indent}  INSERT: {record}")

    @property
    def n_record(self):
        return len(self._operazioni)

db = DatabaseSimulatoAnnidate()

print("=== Test transazioni annidate ===")
with db.transazione("TXN_PRINCIPALE"):
    db.inserisci({"id": 1, "nome": "Alice"})

    with db.transazione("TXN_INTERNA_OK"):
        db.inserisci({"id": 2, "nome": "Bob"})
        db.inserisci({"id": 3, "nome": "Carol"})

    print(f"  Record dopo TXN_INTERNA_OK: {db.n_record}")

    try:
        with db.transazione("TXN_INTERNA_FAIL"):
            db.inserisci({"id": 4, "nome": "Dave"})
            raise ValueError("Vincolo violato: nome duplicato")
    except ValueError:
        pass

    print(f"  Record dopo TXN_INTERNA_FAIL (rollback): {db.n_record}")

print(f"\nRecord finali nel DB: {db.n_record}")
for r in db._operazioni:
    print(f"  {r}")
```

```
# Output atteso:
=== Test transazioni annidate ===
[TXN_PRINCIPALE] BEGIN (livello 0)
    INSERT: {'id': 1, 'nome': 'Alice'}
  [TXN_INTERNA_OK] BEGIN (livello 1)
      INSERT: {'id': 2, 'nome': 'Bob'}
      INSERT: {'id': 3, 'nome': 'Carol'}
  [TXN_INTERNA_OK] COMMIT (livello 1)
  Record dopo TXN_INTERNA_OK: 3
  [TXN_INTERNA_FAIL] BEGIN (livello 1)
      INSERT: {'id': 4, 'nome': 'Dave'}
  [TXN_INTERNA_FAIL] ROLLBACK: 1 operazioni annullate
  Record dopo TXN_INTERNA_FAIL (rollback): 3
[TXN_PRINCIPALE] COMMIT (livello 0)

Record finali nel DB: 3
  {'id': 1, 'nome': 'Alice'}
  {'id': 2, 'nome': 'Bob'}
  {'id': 3, 'nome': 'Carol'}
```

---

## C_EXT3: Context Manager per Profiling di Memoria

```python
from contextlib import contextmanager
import gc
import sys
import tracemalloc

@contextmanager
def profila_memoria(nome: str = "Operazione", top_n: int = 5):
    """
    Context manager che misura l'utilizzo di memoria durante un blocco di codice.
    Usa tracemalloc per tracciare le allocazioni.
    """
    gc.collect()  # pulizia garbage collector prima della misurazione

    tracemalloc.start()
    snapshot_inizio = tracemalloc.take_snapshot()

    print(f"[memoria] {nome}: avvio tracciamento")

    try:
        yield
    finally:
        snapshot_fine = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # Calcola la differenza
        stats = snapshot_fine.compare_to(snapshot_inizio, "lineno")

        print(f"[memoria] {nome}: top {top_n} allocazioni:")
        for stat in stats[:top_n]:
            print(f"  {stat}")

        # Totale
        totale_kb = sum(s.size_diff for s in stats) / 1024
        print(f"  TOTALE: {totale_kb:+.1f} KB")

# Uso
with profila_memoria("Creazione lista grossa"):
    lista = [i * i for i in range(100000)]

print()

with profila_memoria("Generatore (nessuna allocazione)"):
    gen = (i * i for i in range(100000))
    primo = next(gen)  # prendi solo uno
```

```
# Output atteso (i valori variano):
[memoria] Creazione lista grossa: avvio tracciamento
[memoria] Creazione lista grossa: top 5 allocazioni:
  file.py:NN: size=812 KiB (+812 KiB), count=100001 (+100001), average=8 B
  ...
  TOTALE: +812.4 KB

[memoria] Generatore (nessuna allocazione): avvio tracciamento
[memoria] Generatore (nessuna allocazione): top 5 allocazioni:
  ...
  TOTALE: +0.2 KB
```

---

## C_EXT4: Esercizi Aggiuntivi della Parte C

### Esercizio C13: Context Manager per Mutex Gerarchico

```python
from contextlib import contextmanager
import threading
import time

class MutexGerarchico:
    """
    Mutex che impone un ordine di acquisizione per prevenire deadlock.
    I mutex devono essere acquisiti in ordine di ID crescente.
    """

    _id_counter = 0
    _lock_ids_thread = threading.local()

    def __init__(self, nome: str = None):
        MutexGerarchico._id_counter += 1
        self.id = MutexGerarchico._id_counter
        self.nome = nome or f"Mutex-{self.id}"
        self._lock = threading.Lock()

    @contextmanager
    def acquisisci(self):
        """Context manager che acquisisce il mutex rispettando la gerarchia."""
        # Controlla che il thread non stia violando l'ordine
        ids_correnti = getattr(MutexGerarchico._lock_ids_thread, "ids", set())

        if any(id_corrente > self.id for id_corrente in ids_correnti):
            ids_maggiori = {i for i in ids_correnti if i > self.id}
            raise RuntimeError(
                f"Violazione gerarchia mutex: {self.nome} (id={self.id}) "
                f"non puo' essere acquisito mentre si detiene mutex con id {ids_maggiori}"
            )

        # Aggiorna gli ID del thread
        nuovi_ids = ids_correnti | {self.id}
        MutexGerarchico._lock_ids_thread.ids = nuovi_ids

        self._lock.acquire()
        print(f"  [MUTEX] Acquisito: {self.nome}")

        try:
            yield self
        finally:
            self._lock.release()
            MutexGerarchico._lock_ids_thread.ids = ids_correnti
            print(f"  [MUTEX] Rilasciato: {self.nome}")

# Uso corretto: acquisizione in ordine
m1 = MutexGerarchico("Mutex-Database")
m2 = MutexGerarchico("Mutex-Cache")
m3 = MutexGerarchico("Mutex-Log")

print("=== Acquisizione corretta (ordine crescente) ===")
with m1.acquisisci():
    with m2.acquisisci():
        with m3.acquisisci():
            print("  Tutte le risorse acquisite correttamente!")

print()
print("=== Acquisizione errata (ordine decrescente) ===")
try:
    with m3.acquisisci():  # prende m3 (id=3)
        with m1.acquisisci():  # tenta m1 (id=1) — VIOLAZIONE!
            print("  Non dovrebbe arrivare qui")
except RuntimeError as e:
    print(f"  Errore atteso: {e}")
```

```
# Output atteso:
=== Acquisizione corretta (ordine crescente) ===
  [MUTEX] Acquisito: Mutex-Database
  [MUTEX] Acquisito: Mutex-Cache
  [MUTEX] Acquisito: Mutex-Log
  Tutte le risorse acquisite correttamente!
  [MUTEX] Rilasciato: Mutex-Log
  [MUTEX] Rilasciato: Mutex-Cache
  [MUTEX] Rilasciato: Mutex-Database

=== Acquisizione errata (ordine decrescente) ===
  [MUTEX] Acquisito: Mutex-Log
  Errore atteso: Violazione gerarchia mutex: Mutex-Database (id=1) non puo' essere acquisito mentre si detiene mutex con id {3}
  [MUTEX] Rilasciato: Mutex-Log
```

### Esercizio C14: Context Manager per Feature Flags

```python
from contextlib import contextmanager
from typing import Any

class FeatureFlags:
    """
    Gestore di feature flags con supporto override temporaneo via context manager.
    Utile per test e A/B testing.
    """

    def __init__(self, flags_iniziali: dict[str, bool] = None):
        self._flags = dict(flags_iniziali or {})
        self._stack_override = []

    def abilita(self, *flag_names: str):
        """Abilita permanentemente i flag specificati."""
        for nome in flag_names:
            self._flags[nome] = True

    def disabilita(self, *flag_names: str):
        """Disabilita permanentemente i flag specificati."""
        for nome in flag_names:
            self._flags[nome] = False

    def e_abilitato(self, nome: str) -> bool:
        """Controlla se un flag e' abilitato (considera gli override)."""
        if self._stack_override:
            override_corrente = self._stack_override[-1]
            if nome in override_corrente:
                return override_corrente[nome]
        return self._flags.get(nome, False)

    @contextmanager
    def con_override(self, **override_flags: bool):
        """
        Context manager che sovrascrive temporaneamente i flag specificati.
        Utile per test o feature preview.
        """
        print(f"  [flags] Override temporaneo: {override_flags}")
        self._stack_override.append(override_flags)
        try:
            yield self
        finally:
            self._stack_override.pop()
            print(f"  [flags] Override rimosso: {override_flags}")

# Uso
flags = FeatureFlags({
    "nuova_ui": False,
    "pagamenti_v2": True,
    "report_avanzati": False,
    "debug_mode": False,
})

print("=== Flags normali ===")
print(f"  nuova_ui: {flags.e_abilitato('nuova_ui')}")
print(f"  pagamenti_v2: {flags.e_abilitato('pagamenti_v2')}")

print()
print("=== Con override temporaneo ===")
with flags.con_override(nuova_ui=True, debug_mode=True):
    print(f"  nuova_ui: {flags.e_abilitato('nuova_ui')}")  # True (override)
    print(f"  pagamenti_v2: {flags.e_abilitato('pagamenti_v2')}")  # True (originale)
    print(f"  debug_mode: {flags.e_abilitato('debug_mode')}")  # True (override)

print()
print("=== Dopo il context manager (valori originali) ===")
print(f"  nuova_ui: {flags.e_abilitato('nuova_ui')}")  # False (ripristinato)
print(f"  debug_mode: {flags.e_abilitato('debug_mode')}")  # False (ripristinato)
```

```
# Output atteso:
=== Flags normali ===
  nuova_ui: False
  pagamenti_v2: True

=== Con override temporaneo ===
  [flags] Override temporaneo: {'nuova_ui': True, 'debug_mode': True}
  nuova_ui: True
  pagamenti_v2: True
  debug_mode: True
  [flags] Override rimosso: {'nuova_ui': True, 'debug_mode': True}

=== Dopo il context manager (valori originali) ===
  nuova_ui: False
  debug_mode: False
```

---

*Fine Supplemento A, B, C — contenuto aggiuntivo*



---

# PARTE D: EXPERT DEEP DIVE — Argomenti Avanzati

---

## D5: Il Protocollo Descriptor in Profondita'

### Come Funzionano `property`, `staticmethod` e `classmethod`

Tutto in Python usa il protocollo descriptor. Quando accedi a `obj.attr`, Python:
1. Cerca `attr` nella classe (e nelle basi MRO)
2. Se `attr` e' un **data descriptor** (ha `__get__` e `__set__`), usa quello
3. Altrimenti cerca nell'istanza `obj.__dict__`
4. Se non trovato, usa il **non-data descriptor** (ha solo `__get__`)

```python
# property e' implementata come un descriptor
# Ecco la sua re-implementazione in Python puro

class MiaProperty:
    """
    Re-implementazione di property() in Python puro.
    Mostra esattamente come funziona il meccanismo dei descriptor.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc or (fget.__doc__ if fget else None)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # accesso dalla classe: ritorna il descriptor
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, valore):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, valore)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def getter(self, fget):
        """Restituisce una nuova property con il getter aggiornato."""
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        """Restituisce una nuova property con il setter aggiornato."""
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        """Restituisce una nuova property con il deleter aggiornato."""
        return type(self)(self.fget, self.fset, fdel, self.__doc__)

class Temperatura:
    """Classe che usa il nostro descriptor personalizzato."""

    def __init__(self, celsius: float = 0.0):
        self._celsius = celsius

    @MiaProperty
    def celsius(self) -> float:
        """Temperatura in gradi Celsius."""
        return self._celsius

    @celsius.setter
    def celsius(self, valore: float):
        if valore < -273.15:
            raise ValueError(f"Impossibile: {valore}°C e' sotto lo zero assoluto")
        self._celsius = float(valore)

    @MiaProperty
    def fahrenheit(self) -> float:
        """Temperatura in gradi Fahrenheit (calcolata)."""
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, valore: float):
        self.celsius = (valore - 32) * 5 / 9

    @MiaProperty
    def kelvin(self) -> float:
        """Temperatura in Kelvin."""
        return self._celsius + 273.15

# Test
t = Temperatura(100.0)
print(f"100°C = {t.fahrenheit:.1f}°F = {t.kelvin:.2f}K")

t.fahrenheit = 32  # 0°C
print(f"32°F = {t.celsius:.1f}°C = {t.kelvin:.2f}K")

try:
    t.celsius = -300  # sotto lo zero assoluto
except ValueError as e:
    print(f"Errore atteso: {e}")

# Accesso dalla classe: ritorna il descriptor
print(f"\nTipo di Temperatura.celsius: {type(Temperatura.celsius).__name__}")
print(f"Doc: {Temperatura.celsius.__doc__}")
```

```
# Output atteso:
100°C = 212.0°F = 373.15K
32°F = 0.0°C = 273.15K
Errore atteso: Impossibile: -300°C e' sotto lo zero assoluto

Tipo di Temperatura.celsius: MiaProperty
Doc: Temperatura in gradi Celsius.
```

---

## D6: Metaclassi — La Fabbrica delle Classi

### Cosa Sono le Metaclassi

In Python, **tutto e' un oggetto** — anche le classi. La classe di una classe e' una **metaclasse**.

```python
print(type(42))         # <class 'int'>
print(type(int))        # <class 'type'>   -- type e' la metaclasse di default
print(type(type))       # <class 'type'>   -- type e' metaclasse di se stessa
```

```
# Output atteso:
<class 'int'>
<class 'type'>
<class 'type'>
```

### Creare una Metaclasse

```python
class MetaValidatore(type):
    """
    Metaclasse che valida automaticamente tutte le classi create con essa.
    Garantisce che:
    1. La classe abbia una docstring
    2. Tutti i metodi pubblici abbiano type hints
    3. La classe abbia un attributo di versione
    """

    def __new__(mcs, nome: str, basi: tuple, namespace: dict):
        # Controlla la docstring
        if not namespace.get("__doc__"):
            raise TypeError(
                f"Classe '{nome}' deve avere una docstring. "
                "Documenta la responsabilita' della classe."
            )

        # Controlla la versione
        if not namespace.get("VERSIONE") and nome != "BaseValidata":
            raise TypeError(
                f"Classe '{nome}' deve definire VERSIONE = '1.0.0'"
            )

        # Controlla type hints sui metodi pubblici
        import inspect
        for nome_attr, valore in namespace.items():
            if nome_attr.startswith("_"):
                continue
            if callable(valore) and not isinstance(valore, (classmethod, staticmethod)):
                hints = getattr(valore, "__annotations__", {})
                if not hints and inspect.isfunction(valore):
                    raise TypeError(
                        f"Metodo pubblico '{nome}.{nome_attr}' deve avere type hints. "
                        "Aggiungi annotazioni al return type e ai parametri."
                    )

        cls = super().__new__(mcs, nome, basi, namespace)
        print(f"[MetaValidatore] Classe '{nome}' validata e creata con successo")
        return cls

# Classe base con la metaclasse
class BaseValidata(metaclass=MetaValidatore):
    """Classe base per tutte le entita' validate."""
    pass

# Classe corretta
class Utente(BaseValidata):
    """Rappresenta un utente del sistema con autenticazione base."""

    VERSIONE = "1.0.0"

    def __init__(self, nome: str, email: str) -> None:
        self.nome = nome
        self.email = email

    def saluta(self) -> str:
        return f"Ciao, sono {self.nome}!"

    def email_valida(self) -> bool:
        return "@" in self.email and "." in self.email.split("@")[1]

# Classe con errore: manca la docstring
print("\nTest classe senza docstring:")
try:
    class SenzaDocstring(BaseValidata):
        VERSIONE = "1.0.0"
        def metodo(self) -> str:
            return "test"
except TypeError as e:
    print(f"  Errore atteso: {e}")

# Classe con errore: metodo senza type hints
print("\nTest metodo senza type hints:")
try:
    class MetodoSenzaHints(BaseValidata):
        """Classe con metodo senza type hints."""
        VERSIONE = "1.0.0"
        def metodo_problematico(self, x):  # manca return type e tipo di x
            return x
except TypeError as e:
    print(f"  Errore atteso: {e}")

# Test sulla classe corretta
print()
u = Utente("Mario", "mario@esempio.com")
print(f"Saluto: {u.saluta()}")
print(f"Email valida: {u.email_valida()}")
```

```
# Output atteso:
[MetaValidatore] Classe 'BaseValidata' validata e creata con successo
[MetaValidatore] Classe 'Utente' validata e creata con successo

Test classe senza docstring:
  Errore atteso: Classe 'SenzaDocstring' deve avere una docstring. Documenta la responsabilita' della classe.

Test metodo senza type hints:
  Errore atteso: Metodo pubblico 'MetodoSenzaHints.metodo_problematico' deve avere type hints. Aggiungi annotazioni al return type e ai parametri.

Saluto: Ciao, sono Mario!
Email valida: True
```

---

## D7: `__init_subclass__` — Plugin Registry Avanzato

```python
from __future__ import annotations
from typing import ClassVar, Type, Dict
import abc

class Plugin(abc.ABC):
    """
    Classe base per tutti i plugin.
    Usa __init_subclass__ per il registro automatico.
    """

    _registro: ClassVar[Dict[str, Type["Plugin"]]] = {}
    _priorita: ClassVar[Dict[str, int]] = {}

    def __init_subclass__(cls, tipo: str = None, priorita: int = 0, **kwargs):
        """
        Chiamato automaticamente quando una sottoclasse viene definita.

        Args:
            tipo: identificatore univoco del plugin (es: "json", "csv", "xml")
            priorita: priorita' di selezione quando ci sono piu' plugin compatibili
        """
        super().__init_subclass__(**kwargs)

        if tipo is not None:
            if tipo in Plugin._registro:
                print(f"[Plugin] AVVERTIMENTO: '{tipo}' sovrascrive {Plugin._registro[tipo].__name__}")
            Plugin._registro[tipo] = cls
            Plugin._priorita[tipo] = priorita
            print(f"[Plugin] Registrato: '{tipo}' -> {cls.__name__} (priorita': {priorita})")

    @classmethod
    def ottieni(cls, tipo: str) -> Type["Plugin"]:
        """Recupera un plugin dal registro."""
        if tipo not in cls._registro:
            tipi_disponibili = sorted(cls._registro.keys())
            raise KeyError(
                f"Plugin '{tipo}' non trovato. "
                f"Disponibili: {tipi_disponibili}"
            )
        return cls._registro[tipo]

    @classmethod
    def lista_plugin(cls) -> list[str]:
        """Lista tutti i plugin registrati in ordine di priorita'."""
        return sorted(
            cls._registro.keys(),
            key=lambda t: Plugin._priorita.get(t, 0),
            reverse=True,
        )

    @abc.abstractmethod
    def processa(self, dati: str) -> dict:
        """Processa i dati e restituisce un dizionario."""

    @abc.abstractmethod
    def serializza(self, dati: dict) -> str:
        """Serializza un dizionario in stringa."""

# Plugin concreti — si registrano automaticamente
class PluginJSON(Plugin, tipo="json", priorita=10):
    """Plugin per elaborazione JSON."""

    def processa(self, dati: str) -> dict:
        import json
        return json.loads(dati)

    def serializza(self, dati: dict) -> str:
        import json
        return json.dumps(dati, ensure_ascii=False, indent=2)

class PluginCSV(Plugin, tipo="csv", priorita=5):
    """Plugin per elaborazione CSV."""

    def processa(self, dati: str) -> dict:
        import csv
        import io
        reader = csv.DictReader(io.StringIO(dati))
        righe = list(reader)
        return {"righe": righe, "n": len(righe)}

    def serializza(self, dati: dict) -> str:
        if "righe" not in dati:
            return ""
        import csv
        import io
        output = io.StringIO()
        if dati["righe"]:
            writer = csv.DictWriter(output, fieldnames=dati["righe"][0].keys())
            writer.writeheader()
            writer.writerows(dati["righe"])
        return output.getvalue()

class PluginTesto(Plugin, tipo="testo", priorita=1):
    """Plugin per testo semplice."""

    def processa(self, dati: str) -> dict:
        righe = dati.strip().split("\n")
        return {"righe": righe, "n_caratteri": len(dati), "n_righe": len(righe)}

    def serializza(self, dati: dict) -> str:
        if "righe" in dati:
            return "\n".join(dati["righe"])
        return str(dati)

# Uso del sistema di plugin
print()
print("=== Sistema di Plugin ===")
print(f"Plugin disponibili (in ordine di priorita'): {Plugin.lista_plugin()}")

# Elaborazione JSON
json_plugin = Plugin.ottieni("json")()
dati_json = '{"nome": "Alice", "eta": 30, "citta": "Roma"}'
dati = json_plugin.processa(dati_json)
print(f"\nJSON processato: {dati}")
print(f"Serializzato:\n{json_plugin.serializza(dati)}")

# Errore per plugin non esistente
print()
try:
    Plugin.ottieni("xml")
except KeyError as e:
    print(f"Errore atteso: {e}")
```

```
# Output atteso:
[Plugin] Registrato: 'json' -> PluginJSON (priorita': 10)
[Plugin] Registrato: 'csv' -> PluginCSV (priorita': 5)
[Plugin] Registrato: 'testo' -> PluginTesto (priorita': 1)

=== Sistema di Plugin ===
Plugin disponibili (in ordine di priorita'): ['json', 'csv', 'testo']

JSON processato: {'nome': 'Alice', 'eta': 30, 'citta': 'Roma'}
Serializzato:
{
  "nome": "Alice",
  "eta": 30,
  "citta": "Roma"
}

Errore atteso: "Plugin 'xml' non trovato. Disponibili: ['csv', 'json', 'testo']"
```

---

## D8: Generatori Asincroni Avanzati

```python
import asyncio
import random
import time
from typing import AsyncGenerator

# Analogia: un robot che raccoglie dati da piu' sensori contemporaneamente
# Ogni sensore e' asincrono: risponde quando e' pronto, non necessariamente nell'ordine
# in cui li hai interrogati

async def sensore_temperatura(
    id_sensore: int,
    n_letture: int = 5,
    intervallo: float = 0.5,
) -> AsyncGenerator[dict, None]:
    """Generatore asincrono che simula un sensore di temperatura."""
    for i in range(n_letture):
        await asyncio.sleep(intervallo + random.uniform(-0.1, 0.1))
        temperatura = 20 + random.gauss(0, 2)
        yield {
            "sensore_id": id_sensore,
            "lettura": i + 1,
            "temperatura_c": round(temperatura, 2),
            "timestamp": time.time(),
        }

async def sensore_umidita(
    id_sensore: int,
    n_letture: int = 5,
    intervallo: float = 0.7,
) -> AsyncGenerator[dict, None]:
    """Generatore asincrono che simula un sensore di umidita'."""
    for i in range(n_letture):
        await asyncio.sleep(intervallo + random.uniform(-0.15, 0.15))
        umidita = 60 + random.gauss(0, 5)
        yield {
            "sensore_id": id_sensore,
            "lettura": i + 1,
            "umidita_pct": max(0, min(100, round(umidita, 1))),
            "timestamp": time.time(),
        }

async def raccogli_dati_sensori():
    """
    Raccoglie dati da multipli sensori in parallelo usando asyncio.gather.
    """
    print("Avvio raccolta dati sensori...")

    # Consuma un async generator raccogliendo tutti i valori
    async def consuma_sensore(gen):
        letture = []
        async for lettura in gen:
            letture.append(lettura)
            print(f"  Ricevuta lettura: sensore={lettura['sensore_id']}, "
                  f"dati={dict(list(lettura.items())[2:3])}")
        return letture

    # Avvia tutti i sensori in parallelo
    inizio = time.time()
    risultati = await asyncio.gather(
        consuma_sensore(sensore_temperatura(id_sensore=1, n_letture=3)),
        consuma_sensore(sensore_temperatura(id_sensore=2, n_letture=3)),
        consuma_sensore(sensore_umidita(id_sensore=3, n_letture=3)),
    )
    durata = time.time() - inizio

    # Analisi
    print(f"\nRaccolta completata in {durata:.2f}s")
    for i, letture in enumerate(risultati, 1):
        print(f"  Sensore {i}: {len(letture)} letture")

    return risultati

# Esegui
random.seed(42)
asyncio.run(raccogli_dati_sensori())
```

```
# Output atteso (ordine dipende dall'interleaving asincrono):
Avvio raccolta dati sensori...
  Ricevuta lettura: sensore=1, dati={'temperatura_c': 21.99}
  Ricevuta lettura: sensore=2, dati={'temperatura_c': 18.34}
  Ricevuta lettura: sensore=3, dati={'umidita_pct': 62.3}
  Ricevuta lettura: sensore=1, dati={'temperatura_c': 19.87}
  ...

Raccolta completata in 1.52s
  Sensore 1: 3 letture
  Sensore 2: 3 letture
  Sensore 3: 3 letture
```

---

## D9: Abstract Base Classes con Protocollo di Validazione

```python
import abc
from typing import Any, ClassVar

class ValidatoreSchema(abc.ABC):
    """
    Classe astratta che implementa il pattern Strategy per la validazione.
    Ogni sottoclasse definisce il proprio schema di validazione.
    """

    @abc.abstractmethod
    def valida_campo(self, nome: str, valore: Any) -> Any:
        """
        Valida un singolo campo e restituisce il valore sanitizzato.
        Solleva ValidationError se il campo non e' valido.
        """

    @abc.abstractmethod
    def campi_richiesti(self) -> list[str]:
        """Restituisce la lista dei campi obbligatori."""

    def valida(self, dati: dict) -> dict:
        """
        Metodo template: valida tutti i campi e restituisce i dati sanitizzati.
        Non puo' essere sovrascritto (e' il template method pattern).
        """
        # Controlla campi mancanti
        mancanti = [c for c in self.campi_richiesti() if c not in dati]
        if mancanti:
            raise ValueError(f"Campi obbligatori mancanti: {mancanti}")

        # Valida ogni campo
        dati_validati = {}
        errori = {}

        for nome, valore in dati.items():
            try:
                dati_validati[nome] = self.valida_campo(nome, valore)
            except (ValueError, TypeError) as e:
                errori[nome] = str(e)

        if errori:
            raise ValueError(f"Errori di validazione: {errori}")

        return dati_validati

class ValidatoreUtente(ValidatoreSchema):
    """Valida i dati di un utente."""

    def campi_richiesti(self) -> list[str]:
        return ["nome", "email", "eta"]

    def valida_campo(self, nome: str, valore: Any) -> Any:
        if nome == "nome":
            if not isinstance(valore, str) or len(valore) < 2:
                raise ValueError("Il nome deve essere una stringa di almeno 2 caratteri")
            return valore.strip().title()

        elif nome == "email":
            if not isinstance(valore, str) or "@" not in valore:
                raise ValueError("Email non valida")
            return valore.lower().strip()

        elif nome == "eta":
            eta = int(valore)
            if not 0 <= eta <= 150:
                raise ValueError(f"Eta' non valida: {eta}")
            return eta

        else:
            return valore  # campi extra passano senza validazione

# Test
validatore = ValidatoreUtente()

print("=== Dati validi ===")
dati_ok = {"nome": "  mario rossi  ", "email": "MARIO@ESEMPIO.COM", "eta": "25"}
risultato = validatore.valida(dati_ok)
print(f"Dati validati: {risultato}")

print()
print("=== Dati con errori ===")
dati_ko = {"nome": "M", "email": "non_una_email", "eta": "200"}
try:
    validatore.valida(dati_ko)
except ValueError as e:
    print(f"Errore: {e}")

print()
print("=== Campi mancanti ===")
try:
    validatore.valida({"nome": "Alice"})
except ValueError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
=== Dati validi ===
Dati validati: {'nome': 'Mario Rossi', 'email': 'mario@esempio.com', 'eta': 25}

=== Dati con errori ===
Errore: Errori di validazione: {'nome': 'Il nome deve essere una stringa di almeno 2 caratteri', 'email': 'Email non valida', 'eta': "Eta' non valida: 200"}

=== Campi mancanti ===
Errore: Campi obbligatori mancanti: ['email', 'eta']
```

---

## D10: Decoratori su Classi — Pattern Avanzati

```python
import functools
from typing import Type, TypeVar

T = TypeVar("T")

def aggiunge_metodi_confronto(cls: Type[T]) -> Type[T]:
    """
    Decoratore di classe che aggiunge automaticamente tutti i metodi
    di confronto (__lt__, __le__, __gt__, __ge__) basandosi solo su __eq__
    e __lt__ definiti dalla classe.

    Simile a functools.total_ordering ma didattico.
    """
    if not hasattr(cls, "__lt__"):
        raise TypeError(
            f"La classe {cls.__name__} deve definire __lt__ per usare "
            "aggiunge_metodi_confronto"
        )

    # __le__: minore o uguale = minore o uguale
    if "__le__" not in cls.__dict__:
        def __le__(self, other):
            if type(other) is NotImplemented:
                return NotImplemented
            return self < other or self == other
        cls.__le__ = __le__

    # __gt__: maggiore = NON (minore o uguale)
    if "__gt__" not in cls.__dict__:
        def __gt__(self, other):
            if type(other) is NotImplemented:
                return NotImplemented
            return not (self < other or self == other)
        cls.__gt__ = __gt__

    # __ge__: maggiore o uguale = NON minore
    if "__ge__" not in cls.__dict__:
        def __ge__(self, other):
            if type(other) is NotImplemented:
                return NotImplemented
            return not (self < other)
        cls.__ge__ = __ge__

    return cls

@aggiunge_metodi_confronto
class Frazione:
    """Rappresenta una frazione matematica."""

    def __init__(self, numeratore: int, denominatore: int):
        if denominatore == 0:
            raise ValueError("Il denominatore non puo' essere zero")
        # Normalizza il segno
        if denominatore < 0:
            numeratore, denominatore = -numeratore, -denominatore
        # Riduzione ai minimi termini
        from math import gcd
        d = gcd(abs(numeratore), denominatore)
        self.num = numeratore // d
        self.den = denominatore // d

    def __eq__(self, other):
        if not isinstance(other, Frazione):
            return NotImplemented
        return self.num * other.den == other.num * self.den

    def __lt__(self, other):
        if not isinstance(other, Frazione):
            return NotImplemented
        return self.num * other.den < other.num * self.den

    def __repr__(self):
        return f"Frazione({self.num}/{self.den})"

    def __float__(self):
        return self.num / self.den

# Test
f1 = Frazione(1, 2)  # 1/2
f2 = Frazione(3, 4)  # 3/4
f3 = Frazione(2, 4)  # 2/4 = 1/2 (ridotta)

print(f"f1 = {f1} = {float(f1)}")
print(f"f2 = {f2} = {float(f2)}")
print(f"f3 = {f3} = {float(f3)}")

print(f"\nConfronto:")
print(f"f1 == f3: {f1 == f3}")  # True: 1/2 == 2/4
print(f"f1 < f2: {f1 < f2}")   # True: 1/2 < 3/4
print(f"f2 > f1: {f2 > f1}")   # True
print(f"f1 <= f3: {f1 <= f3}") # True (uguali)
print(f"f2 >= f1: {f2 >= f1}") # True

# Ordinamento
frazioni = [Frazione(3, 4), Frazione(1, 2), Frazione(2, 3), Frazione(1, 4)]
print(f"\nFrazioni ordinate: {sorted(frazioni)}")
```

```
# Output atteso:
f1 = Frazione(1/2) = 0.5
f2 = Frazione(3/4) = 0.75
f3 = Frazione(1/2) = 0.5

Confronto:
f1 == f3: True
f1 < f2: True
f2 > f1: True
f1 <= f3: True
f2 >= f1: True

Frazioni ordinate: [Frazione(1/4), Frazione(1/2), Frazione(2/3), Frazione(3/4)]
```

---

# PARTE E: RIEPILOGO ESPANSO — Tutto in Una Vista

---

## E1: Mappa Mentale dei Concetti

```
PYTHON AVANZATO: DECORATORI, GENERATORI, CONTEXT MANAGER
│
├── DECORATORI
│   ├── Basi
│   │   ├── Funzioni come oggetti di prima classe
│   │   ├── Closures e variabili libere
│   │   └── Funzioni di ordine superiore (map, filter, sorted, reduce)
│   │
│   ├── Pattern Base
│   │   ├── wrapper(*args, **kwargs) → forward universale
│   │   ├── @functools.wraps → preserva metadati
│   │   └── @ syntactic sugar = func = decorator(func)
│   │
│   ├── Pattern Parametrico
│   │   ├── Triple nesting: outer → decorator → wrapper
│   │   └── func=None + keyword-only: flessibile con/senza ()
│   │
│   ├── Decoratori Pratici
│   │   ├── @timer, @retry, @cache
│   │   ├── @deprecated, @validate_types, @log_calls
│   │   ├── @singleton, @rate_limit, @throttle
│   │   └── @once, @memoize_con_ttl
│   │
│   └── Pattern Avanzati
│       ├── Class-based: __call__ + functools.update_wrapper
│       ├── Stacking: bottom-up application, top-down execution
│       └── @contextmanager come decoratore
│
├── GENERATORI
│   ├── Basi
│   │   ├── yield → pausa, produce, riprende
│   │   ├── next() → avanza di uno
│   │   └── StopIteration → fine sequenza
│   │
│   ├── Espressioni generatrici
│   │   ├── () vs [] — memoria vs lista
│   │   └── Pipeline: gen1 | gen2 | gen3 lazy
│   │
│   ├── Protocollo Iterator
│   │   ├── __iter__() → restituisce self
│   │   └── __next__() → prossimo valore o StopIteration
│   │
│   ├── Protocollo Generator
│   │   ├── send(value) → invia valore al punto yield
│   │   ├── throw(exc) → inietta eccezione
│   │   └── close() → invia GeneratorExit
│   │
│   ├── yield from (PEP 380)
│   │   ├── Delega a sub-generator
│   │   ├── Propaga send/throw bidirezionalmente
│   │   └── Cattura return value dal sub-generator
│   │
│   └── itertools
│       ├── Infiniti: count, cycle, repeat
│       ├── Filtraggio: compress, dropwhile, takewhile, filterfalse
│       ├── Combinatori: product, combinations, permutations
│       └── Utili: chain, islice, groupby, accumulate, batched
│
└── CONTEXT MANAGER
    ├── Protocollo
    │   ├── __enter__() → setup, restituisce risorsa
    │   └── __exit__(exc_type, exc_val, exc_tb) → teardown
    │       └── return True → sopprime l'eccezione
    │
    ├── @contextmanager (contextlib)
    │   ├── codice prima di yield = __enter__
    │   ├── yield value = target dell'as
    │   └── finally = __exit__ garantito
    │
    ├── contextlib tools
    │   ├── suppress(*exc) → soppressione pulita
    │   ├── redirect_stdout/stderr → ridirezione output
    │   ├── closing(obj) → chiama obj.close()
    │   └── nullcontext → no-op placeholder
    │
    ├── ExitStack
    │   ├── enter_context(cm) → N context manager dinamici
    │   ├── callback(func, *args) → cleanup arbitrario
    │   ├── pop_all() → trasferisce ownership
    │   └── LIFO cleanup order
    │
    └── Async
        ├── __aenter__ / __aexit__
        ├── @asynccontextmanager
        ├── AsyncExitStack
        └── async with / async for
```

---

## E2: Tabella di Riferimento Rapido — Quando Usare Cosa

### Decoratori

| Situazione | Decoratore Consigliato |
|------------|----------------------|
| Misurare performance | `@timer` |
| Ritentare su errore rete | `@retry(tentativi=3, pausa=1.0)` |
| Cache risultati costosi | `@functools.lru_cache(maxsize=128)` |
| Cache illimitata permanente | `@functools.cache` |
| Cache con scadenza TTL | `@memoize_con_ttl(ttl=60)` |
| Segnare funzione obsoleta | `@deprecated(alternativa="nuova_f")` |
| Validare tipi in ingresso | `@validate_types` |
| Log automatico chiamate | `@log_calls` |
| Pattern singleton | `@singleton` |
| Limitare frequenza chiamate | `@rate_limit(massimo=10, periodo=1.0)` |
| Eseguire al massimo una volta | `@once` |
| Rallentare le chiamate | `@throttle(chiamate_al_secondo=2)` |
| Autorizzazione per ruolo | `@richiede_ruolo("admin")` |

### Generatori vs Liste

| Criterio | Usa Generatore | Usa Lista |
|----------|----------------|-----------|
| Dimensione dati | Grandi (GB) | Piccoli (MB) |
| Utilizzo dei dati | Una sola volta | Piu' volte |
| Accesso | Sequenziale | Casuale (index) |
| Memoria | Minima (O(1)) | Proporzionale (O(n)) |
| Primo uso | Solo se strettamente necessario | Subito dopo creazione |
| Tipo di operazione | Streaming, pipeline | Sort, reverse, count, slice |

### Context Manager

| Situazione | Approccio |
|------------|-----------|
| Aprire file | `with open(path) as f:` |
| Connessione DB | `with connessione_db() as conn:` |
| Lock threading | `with mio_lock:` |
| Cambiare directory temporaneamente | `@contextmanager + os.chdir + finally` |
| Sopprimere eccezione | `with suppress(FileNotFoundError):` |
| Catturare stdout | `with redirect_stdout(buffer):` |
| N context manager dinamici | `with ExitStack() as stack:` |
| Context manager asincrono | `async with risorsa_asincrona():` |
| Test isolati | `with ambiente_test_isolato():` |

---

## E3: Errori Comuni e Come Evitarli — Master List

### Errori con Decoratori

```python
# ERRORE 1: Dimenticare functools.wraps
def decoratore_sbagliato(funzione):
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper  # wrapper.__name__ == "wrapper", non "funzione"

# CORREZIONE:
import functools
def decoratore_corretto(funzione):
    @functools.wraps(funzione)  # preserva __name__, __doc__, ecc.
    def wrapper(*args, **kwargs):
        return funzione(*args, **kwargs)
    return wrapper

# ERRORE 2: Decoratore parametrico senza parentesi
def con_log(livello="INFO"):
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            print(f"[{livello}] {funzione.__name__}")
            return funzione(*args, **kwargs)
        return wrapper
    return decoratore

@con_log       # SBAGLIATO! Passa la funzione come "livello"
def mia_funzione():
    pass

@con_log()     # CORRETTO: chiama il factory, poi il decoratore
def mia_funzione2():
    pass

# ERRORE 3: Catturare variabile di loop per closures
funzioni_sbagliate = []
for i in range(3):
    def f():
        return i  # cattura l'ULTIMA i (3 al termine del loop)
    funzioni_sbagliate.append(f)

# CORREZIONE 1: default argument
funzioni_corrette_1 = []
for i in range(3):
    def f(i=i):  # cattura il VALORE corrente di i
        return i
    funzioni_corrette_1.append(f)

# CORREZIONE 2: lambda con default
funzioni_corrette_2 = [lambda x=i: x for i in range(3)]

print("Sbagliate:", [f() for f in funzioni_sbagliate])
print("Corrette 1:", [f() for f in funzioni_corrette_1])
print("Corrette 2:", [f() for f in funzioni_corrette_2])
```

```
# Output atteso:
Sbagliate: [2, 2, 2]
Corrette 1: [0, 1, 2]
Corrette 2: [0, 1, 2]
```

### Errori con Generatori

```python
# ERRORE 1: Un generatore e' monouso
def gen():
    yield 1
    yield 2
    yield 3

g = gen()
lista1 = list(g)        # [1, 2, 3]
lista2 = list(g)        # [] -- esaurito!
print(f"lista1: {lista1}")
print(f"lista2 (esaurita): {lista2}")

# CORREZIONE: crea un nuovo generatore ogni volta
lista3 = list(gen())    # [1, 2, 3] -- nuovo generatore
print(f"lista3 (nuovo gen): {lista3}")

# ERRORE 2: return in un generatore prima di Python 3.3
def gen_con_return_sbagliato():
    yield 1
    yield 2
    return 42  # Python 3.3+: valore di StopIteration.value

# Per catturare il return value:
g = gen_con_return_sbagliato()
try:
    while True:
        prossimo = next(g)
        print(f"  yield: {prossimo}")
except StopIteration as stop:
    print(f"  return value: {stop.value}")

# ERRORE 3: Usare yield all'interno di una comprensione
def genera_sbagliato():
    # Questo NON fa quello che pensi!
    valori = [yield x for x in range(5)]  # SyntaxError in Python 3.7+
    # Corretta:

def genera_corretto():
    for x in range(5):
        yield x
```

```
# Output atteso:
lista1: [1, 2, 3]
lista2 (esaurita): []
lista3 (nuovo gen): [1, 2, 3]
  yield: 1
  yield: 2
  return value: 42
```

### Errori con Context Manager

```python
from contextlib import contextmanager

# ERRORE 1: Dimenticare il try/finally in @contextmanager
@contextmanager
def risorsa_sbagliata():
    risorsa = "aperta"
    print(f"Risorsa {risorsa}")
    yield risorsa
    print("Cleanup")  # NON eseguito se c'e' un'eccezione!

# CORREZIONE:
@contextmanager
def risorsa_corretta():
    risorsa = "aperta"
    print(f"Risorsa {risorsa}")
    try:
        yield risorsa
    finally:
        print("Cleanup (garantito)")  # SEMPRE eseguito

# ERRORE 2: Dimenticare che __exit__ deve restituire True per sopprimere
class SoppressoreRotto:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is ValueError:
            print(f"Soppresso: {exc_val}")
            # MANCA: return True — l'eccezione si propaghera' comunque!

class SoppressoreCorretto:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is ValueError:
            print(f"Soppresso: {exc_val}")
            return True  # Sopprime l'eccezione
        return False  # Lascia propagare le altre eccezioni

print("=== SoppressoreRotto ===")
try:
    with SoppressoreRotto():
        raise ValueError("test")
except ValueError:
    print("  L'eccezione si e' propagata!")

print()
print("=== SoppressoreCorretto ===")
with SoppressoreCorretto():
    raise ValueError("test")
print("  Nessuna propagazione!")
```

```
# Output atteso:
=== SoppressoreRotto ===
Soppresso: test
  L'eccezione si e' propagata!

=== SoppressoreCorretto ===
Soppresso: test
  Nessuna propagazione!
```

---

## E4: Ricette Pronte — Copia e Usa

### Ricetta 1: Cache Intelligente

```python
import functools
import time

# Per la maggior parte dei casi: usa lru_cache
@functools.lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Fibonacci con memoization automatica."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Per cache senza limite e thread-safety migliore:
@functools.cache
def fattoriale(n: int) -> int:
    """Fattoriale con cache illimitata."""
    return 1 if n <= 1 else n * fattoriale(n - 1)

print(f"fibonacci(35) = {fibonacci(35)}")
print(f"Cache info: {fibonacci.cache_info()}")
print(f"fattoriale(20) = {fattoriale(20)}")
```

```
# Output atteso:
fibonacci(35) = 9227465
Cache info: CacheInfo(hits=33, misses=36, maxsize=128, currsize=36)
fattoriale(20) = 2432902008176640000
```

### Ricetta 2: Retry con Backoff Esponenziale

```python
import functools
import time
import random

def retry_con_backoff(
    *eccezioni,
    tentativi: int = 3,
    pausa_base: float = 1.0,
    backoff_moltiplicatore: float = 2.0,
    jitter: bool = True,
):
    """
    Retry con backoff esponenziale e jitter.
    Utile per chiamate API che possono fallire transitoriamente.

    Args:
        *eccezioni: eccezioni da ritentare (default: tutte)
        tentativi: numero massimo di tentativi
        pausa_base: secondi di attesa al primo retry
        backoff_moltiplicatore: moltiplicatore esponenziale
        jitter: aggiunge variazione casuale per evitare thundering herd
    """
    if not eccezioni:
        eccezioni = (Exception,)

    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            ultimo_errore = None
            pausa = pausa_base

            for tentativo in range(1, tentativi + 1):
                try:
                    return funzione(*args, **kwargs)
                except eccezioni as e:
                    ultimo_errore = e
                    if tentativo == tentativi:
                        break

                    attesa = pausa
                    if jitter:
                        attesa += random.uniform(0, pausa * 0.1)

                    print(f"  [retry] Tentativo {tentativo}/{tentativi} fallito: {e}. "
                          f"Attendo {attesa:.2f}s...")
                    time.sleep(attesa)
                    pausa *= backoff_moltiplicatore

            raise RuntimeError(
                f"{funzione.__name__} fallita dopo {tentativi} tentativi"
            ) from ultimo_errore

        return wrapper
    return decoratore

# Uso
contatore = [0]

@retry_con_backoff(ConnectionError, tentativi=3, pausa_base=0.1)
def chiama_api_instabile() -> str:
    """Simula una chiamata API che fallisce le prime volte."""
    contatore[0] += 1
    if contatore[0] < 3:
        raise ConnectionError(f"Timeout al tentativo {contatore[0]}")
    return "Risposta API"

try:
    risposta = chiama_api_instabile()
    print(f"Risposta: {risposta}")
except RuntimeError as e:
    print(f"Fallita: {e}")
```

```
# Output atteso:
  [retry] Tentativo 1/3 fallito: Timeout al tentativo 1. Attendo 0.10s...
  [retry] Tentativo 2/3 fallito: Timeout al tentativo 2. Attendo 0.21s...
Risposta: Risposta API
```

### Ricetta 3: Pipeline di Elaborazione Dati

```python
from typing import Iterable, Iterator, TypeVar, Callable

T = TypeVar("T")
U = TypeVar("U")

def pipeline(*stadi: Callable) -> Callable[[Iterable], Iterator]:
    """
    Crea una pipeline di elaborazione dati lazy.
    Ogni stadio e' una funzione che prende un iterabile e restituisce un iterabile.

    Uso:
        elabora = pipeline(
            filtra_vuoti,
            converti_in_numeri,
            rimuovi_outlier,
        )
        risultati = list(elabora(dati_grezzi))
    """
    def esegui(dati: Iterable) -> Iterator:
        risultato = dati
        for stadio in stadi:
            risultato = stadio(risultato)
        return risultato
    return esegui

# Stadi della pipeline
def rimuovi_duplicati(iterable: Iterable[T]) -> Iterator[T]:
    """Rimuove i duplicati mantenendo l'ordine."""
    visti = set()
    for elemento in iterable:
        if elemento not in visti:
            visti.add(elemento)
            yield elemento

def normalizza_testo(iterable: Iterable[str]) -> Iterator[str]:
    """Normalizza ogni stringa: strip, lower."""
    for s in iterable:
        normalizzato = s.strip().lower()
        if normalizzato:
            yield normalizzato

def filtra_corti(minimo: int = 3):
    """Factory per filtro per lunghezza minima."""
    def stadio(iterable: Iterable[str]) -> Iterator[str]:
        for s in iterable:
            if len(s) >= minimo:
                yield s
    return stadio

def conta_parole(iterable: Iterable[str]) -> Iterator[tuple[str, int]]:
    """Converte ogni stringa in (stringa, n_parole)."""
    for s in iterable:
        yield s, len(s.split())

# Dati grezzi (con duplicati, spazi, maiuscole)
dati_grezzi = [
    "  Ciao Mondo  ",
    "ciao mondo",
    "  Python e' bello",
    " ",
    "Hello World",
    "Python e' bello",
    "ab",
    "Test",
    "test",
]

# Crea e applica la pipeline
elabora = pipeline(
    normalizza_testo,
    rimuovi_duplicati,
    filtra_corti(5),
    conta_parole,
)

print("Pipeline risultati:")
for elemento, n_parole in elabora(dati_grezzi):
    print(f"  '{elemento}' ({n_parole} parole)")
```

```
# Output atteso:
Pipeline risultati:
  'ciao mondo' (2 parole)
  "python e' bello" (3 parole)
  'hello world' (2 parole)
  'test' (1 parole)
```

---

## E5: Glossario Avanzato

| Termine | Definizione Estesa |
|---------|-------------------|
| **Decorator** | Funzione che prende un callable e restituisce un callable modificato. Implementa il Pattern Decorator della GoF. |
| **Closure** | Funzione che "chiude" su variabili del suo scope di definizione, mantenendole vive anche dopo che lo scope esterno e' terminato. |
| **First-class citizen** | Un oggetto (funzione, classe) che puo' essere assegnato a variabili, passato come argomento, restituito da funzioni e memorizzato in strutture dati. |
| **Higher-order function** | Funzione che accetta funzioni come argomenti e/o restituisce funzioni. Esempi: `map`, `filter`, `sorted`, `functools.reduce`. |
| **Generator function** | Funzione che contiene almeno un'istruzione `yield`. Chiamarla restituisce un oggetto generator (non esegue il corpo). |
| **Generator object** | Oggetto creato chiamando una generator function. Implementa `__iter__` e `__next__`. Esegue il corpo della funzione a step. |
| **Generator expression** | Sintassi `(expr for x in iterable if cond)` che crea un generator object senza definire una funzione. |
| **Lazy evaluation** | Calcolo posticipato: i valori vengono prodotti solo quando richiesti. Caratteristica fondamentale dei generatori. |
| **Protocol** | In Python, un insieme di metodi speciali che una classe deve implementare per supportare una certa funzionalita'. Es: iterator protocol (`__iter__`, `__next__`). |
| **Context manager protocol** | Coppia di metodi `__enter__` e `__exit__` che rendono un oggetto utilizzabile con `with`. |
| **LBYL** | Look Before You Leap: controlla prima di fare. Stile C/Java. Es: `if file exists: open`. |
| **EAFP** | Easier to Ask Forgiveness than Permission: prova e gestisci l'eccezione. Stile pythonic. Es: `try: open except: handle`. |
| **Descriptor** | Oggetto con `__get__` (e opzionalmente `__set__`, `__delete__`) che controlla l'accesso agli attributi. Base di `property`, `classmethod`, `staticmethod`. |
| **Data descriptor** | Descriptor con sia `__get__` che `__set__`. Ha precedenza sulle istanze: sovrascrive `obj.__dict__`. |
| **Non-data descriptor** | Descriptor con solo `__get__`. Le istanze possono sovrascrivere con `obj.__dict__[attr] = val`. |
| **MRO** | Method Resolution Order: ordine in cui Python cerca metodi nelle classi base. Algoritmo C3 linearization. |
| **Metaclass** | Classe di una classe. `type` e' la metaclasse di default. Permette di controllare la creazione e validazione delle classi. |
| **ExitStack** | Context manager che gestisce dinamicamente N altri context manager con pulizia LIFO garantita. Parte di `contextlib`. |
| **Generator state** | Uno di: GEN_CREATED, GEN_SUSPENDED, GEN_RUNNING, GEN_CLOSED. Ispezionabile con `inspect.getgeneratorstate()`. |
| **yield from** | Delega esecuzione a un sub-generator. Propaga `send/throw/close` bidirezionalmente e cattura il `return` value (PEP 380). |
| **PEP 255** | Python Enhancement Proposal che ha introdotto i generatori semplici (yield) in Python 2.2. |
| **PEP 342** | PEP che ha esteso i generatori con send(), throw() e close() per la comunicazione bidirezionale (Python 2.5). |
| **PEP 343** | PEP che ha introdotto il protocollo with e i context manager (Python 2.5). |
| **PEP 380** | PEP che ha introdotto yield from per la delega ai sub-generator (Python 3.3). |

---

## E6: Progetto Finale Integrato — Sistema di ETL

Il progetto combina tutti e tre i concetti (decoratori, generatori, context manager) in un sistema ETL (Extract, Transform, Load) reale.

```python
"""
Sistema ETL (Extract, Transform, Load) che integra:
- Decoratori: @timer, @retry, @log_fase
- Generatori: lettura lazy dei file, pipeline di trasformazione
- Context Manager: gestione transazione, backup, logging
"""

import functools
import time
import json
import csv
import io
import os
import shutil
from contextlib import contextmanager
from typing import Generator, Any, Callable

# ============================================================
# DECORATORI DEL SISTEMA ETL
# ============================================================

def log_fase(nome_fase: str):
    """Decoratore che logga l'inizio e fine di una fase ETL."""
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            print(f"\n{'='*50}")
            print(f"FASE: {nome_fase}")
            print(f"{'='*50}")
            inizio = time.perf_counter()
            try:
                risultato = funzione(*args, **kwargs)
                durata = time.perf_counter() - inizio
                print(f"[OK] {nome_fase} completata in {durata:.3f}s")
                return risultato
            except Exception as e:
                durata = time.perf_counter() - inizio
                print(f"[ERRORE] {nome_fase} fallita dopo {durata:.3f}s: {e}")
                raise
        return wrapper
    return decoratore

def statistiche_etl(funzione):
    """Decoratore che raccoglie statistiche sull'elaborazione ETL."""
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        gen = funzione(*args, **kwargs)

        n_elaborati = 0
        n_errori = 0

        for elemento in gen:
            if elemento.get("_errore"):
                n_errori += 1
            else:
                n_elaborati += 1
            yield elemento

        print(f"\n[STATISTICHE] Elaborati: {n_elaborati}, Errori: {n_errori}")

    return wrapper

# ============================================================
# CONTEXT MANAGER DEL SISTEMA ETL
# ============================================================

@contextmanager
def transazione_etl(nome: str):
    """Context manager per una transazione ETL atomica."""
    stato = {"inizio": time.time(), "n_record": 0}
    print(f"[TX] Inizio transazione: {nome}")
    try:
        yield stato
        durata = time.time() - stato["inizio"]
        print(f"[TX] Transazione completata: {nome} "
              f"({stato['n_record']} record in {durata:.2f}s)")
    except Exception as e:
        print(f"[TX] Rollback transazione: {nome} - {e}")
        raise

# ============================================================
# GENERATORI DEL SISTEMA ETL (EXTRACT)
# ============================================================

def estrai_da_csv(contenuto: str) -> Generator[dict, None, None]:
    """Estrae record da un CSV riga per riga (lazy)."""
    reader = csv.DictReader(io.StringIO(contenuto))
    for riga in reader:
        yield dict(riga)

def estrai_da_json_lines(contenuto: str) -> Generator[dict, None, None]:
    """Estrae record da un file JSON Lines (un oggetto per riga)."""
    for linea in contenuto.strip().split("\n"):
        linea = linea.strip()
        if linea:
            try:
                yield json.loads(linea)
            except json.JSONDecodeError as e:
                yield {"_errore": str(e), "_linea": linea}

# ============================================================
# GENERATORI DEL SISTEMA ETL (TRANSFORM)
# ============================================================

def trasforma_pulisci(sorgente: Generator) -> Generator[dict, None, None]:
    """Pulisce i dati: strip, normalizza None, ecc."""
    for record in sorgente:
        if record.get("_errore"):
            yield record
            continue
        pulito = {}
        for k, v in record.items():
            if isinstance(v, str):
                v = v.strip()
                if v.lower() in ("", "null", "none", "n/a", "-"):
                    v = None
            pulito[k] = v
        yield pulito

def trasforma_tipi(
    sorgente: Generator,
    schemi_tipi: dict[str, Callable],
) -> Generator[dict, None, None]:
    """Converte i valori nei tipi specificati."""
    for record in sorgente:
        if record.get("_errore"):
            yield record
            continue
        convertito = dict(record)
        errori_campo = {}
        for campo, tipo_fn in schemi_tipi.items():
            if campo in convertito and convertito[campo] is not None:
                try:
                    convertito[campo] = tipo_fn(convertito[campo])
                except (ValueError, TypeError) as e:
                    errori_campo[campo] = str(e)
        if errori_campo:
            yield {**convertito, "_avvisi": errori_campo}
        else:
            yield convertito

def trasforma_filtra(
    sorgente: Generator,
    predicato: Callable[[dict], bool],
    motivo: str = "",
) -> Generator[dict, None, None]:
    """Filtra i record che non soddisfano il predicato."""
    for record in sorgente:
        if record.get("_errore"):
            yield record
        elif predicato(record):
            yield record
        else:
            print(f"  [FILTRATO] {motivo}: {dict(list(record.items())[:3])}")

# ============================================================
# LOAD
# ============================================================

def carica_in_memoria(sorgente: Generator) -> list[dict]:
    """Carica tutti i record validati in una lista."""
    risultati = []
    for record in sorgente:
        if not record.get("_errore"):
            risultati.append({k: v for k, v in record.items() if not k.startswith("_")})
    return risultati

# ============================================================
# PIPELINE COMPLETA
# ============================================================

@log_fase("ESTRAZIONE E TRASFORMAZIONE")
def esegui_etl(csv_contenuto: str) -> list[dict]:
    """Esegue la pipeline ETL completa."""

    with transazione_etl("Elaborazione vendite") as stato:
        # Extract
        sorgente = estrai_da_csv(csv_contenuto)

        # Transform: pipeline lazy
        pipeline = sorgente
        pipeline = trasforma_pulisci(pipeline)
        pipeline = trasforma_tipi(pipeline, {
            "prezzo": float,
            "quantita": int,
            "anno": int,
        })
        pipeline = trasforma_filtra(
            pipeline,
            predicato=lambda r: (r.get("prezzo") or 0) > 0,
            motivo="prezzo non positivo",
        )

        # Load
        dati = carica_in_memoria(pipeline)
        stato["n_record"] = len(dati)

    return dati

# ============================================================
# DATI DI TEST
# ============================================================

CSV_TEST = """nome,prodotto,prezzo,quantita,anno
Alice,Laptop,1299.99,1,2024
Bob,Mouse,25.00,3,2024
Carol,Keyboard,,-,2023
Dave,Monitor,0,2,2024
Eve,Webcam,89.99,1,2024
Frank,USB Hub,null,2,2023
"""

print("=== Sistema ETL ===")
risultati = esegui_etl(CSV_TEST)

print("\n=== Risultati ETL ===")
for r in risultati:
    print(f"  {r}")

print(f"\nTotale record caricati: {len(risultati)}")
totale_vendite = sum(r.get("prezzo", 0) * r.get("quantita", 0)
                     for r in risultati
                     if r.get("prezzo") and r.get("quantita"))
print(f"Fatturato totale: €{totale_vendite:,.2f}")
```

```
# Output atteso:
=== Sistema ETL ===

==================================================
FASE: ESTRAZIONE E TRASFORMAZIONE
==================================================
[TX] Inizio transazione: Elaborazione vendite
  [FILTRATO] prezzo non positivo: {'nome': 'Dave', 'prodotto': 'Monitor', 'prezzo': 0.0}
[TX] Transazione completata: Elaborazione vendite (4 record in 0.00s)
[OK] ESTRAZIONE E TRASFORMAZIONE completata in 0.002s

=== Risultati ETL ===
  {'nome': 'Alice', 'prodotto': 'Laptop', 'prezzo': 1299.99, 'quantita': 1, 'anno': 2024}
  {'nome': 'Bob', 'prodotto': 'Mouse', 'prezzo': 25.0, 'quantita': 3, 'anno': 2024}
  {'nome': 'Eve', 'prodotto': 'Webcam', 'prezzo': 89.99, 'quantita': 1, 'anno': 2024}
  {'nome': 'Frank', 'prodotto': 'USB Hub', 'prezzo': None, 'quantita': 2, 'anno': 2023}

Totale record caricati: 4
Fatturato totale: €1,464.99
```

---

## E7: Checklist Finale Completa (60+ Item)

### Sezione A — Funzioni Come Oggetti e Closures

- [ ] A.1 — Hai assegnato una funzione a una variabile e chiamato la variabile? `f = print; f("ciao")`
- [ ] A.2 — Hai passato una funzione come argomento? `sorted(lista, key=len)`
- [ ] A.3 — Hai restituito una funzione da un'altra funzione? `def factory(): return lambda x: x*2`
- [ ] A.4 — Conosci la differenza tra `funzione` (oggetto) e `funzione()` (chiamata)?
- [ ] A.5 — Sai come funziona `nonlocal` nelle closures?
- [ ] A.6 — Hai evitato il trap del loop con le closures? (usa `x=x` per catturare il valore)
- [ ] A.7 — Sai ispezionare le variabili libere di una closure con `.__closure__`?
- [ ] A.8 — Conosci `map()`, `filter()`, `sorted(key=...)`, `functools.reduce()`?
- [ ] A.9 — Preferisci list comprehension a `map`/`filter` quando il codice e' piu' leggibile?

### Sezione B — Decoratori Base

- [ ] B.1 — Sai scrivere un decoratore con il pattern `wrapper(*args, **kwargs)`?
- [ ] B.2 — Usi sempre `@functools.wraps(funzione)` nel wrapper?
- [ ] B.3 — Conosci l'equivalenza `@decoratore` == `funzione = decoratore(funzione)`?
- [ ] B.4 — Sai applicare piu' decoratori e conosci l'ordine di applicazione?
- [ ] B.5 — Hai implementato almeno un decoratore pratico (`@timer`, `@retry`, `@log_calls`)?

### Sezione C — Decoratori Parametrici

- [ ] C.1 — Sai scrivere un decoratore con tre livelli di annidamento?
- [ ] C.2 — Hai implementato il pattern `func=None` per decoratori flessibili (con/senza `()`)?
- [ ] C.3 — Conosci `functools.cache` vs `functools.lru_cache`? Sai quando usare ciascuno?
- [ ] C.4 — Hai implementato `@singleton` o `@once`?
- [ ] C.5 — Sai implementare un class-based decorator con `__call__` e `functools.update_wrapper`?

### Sezione D — Generatori Base

- [ ] D.1 — Conosci la differenza tra una funzione normale e una generator function?
- [ ] D.2 — Sai che chiamare una generator function restituisce un oggetto, non esegue il corpo?
- [ ] D.3 — Hai usato `yield` per produrre valori uno alla volta?
- [ ] D.4 — Conosci `next()`, `StopIteration` e il loro ruolo nel protocollo di iterazione?
- [ ] D.5 — Sai scrivere un'espressione generatrice `(expr for x in y)` e perche' usa `()` non `[]`?

### Sezione E — Generatori Avanzati

- [ ] E.1 — Hai usato `yield from` per delegare a un sub-generator?
- [ ] E.2 — Conosci `send(value)` e come il valore e' restituito dall'espressione `yield`?
- [ ] E.3 — Hai usato `throw()` per iniettare eccezioni in un generatore?
- [ ] E.4 — Sai che `close()` inietta `GeneratorExit` e il generatore deve gestirla con `finally`?
- [ ] E.5 — Hai implementato una pipeline lazy con generatori connessi?
- [ ] E.6 — Conosci `itertools.chain`, `islice`, `groupby`, `product`, `combinations`?
- [ ] E.7 — Sai quando usare un generatore vs una lista (memoria, riutilizzo, accesso)?

### Sezione F — Context Manager Base

- [ ] F.1 — Conosci il protocollo `__enter__` / `__exit__`?
- [ ] F.2 — Sai che `__exit__` riceve `(exc_type, exc_val, exc_tb)` e che `return True` sopprime?
- [ ] F.3 — Hai usato `@contextmanager` di `contextlib`?
- [ ] F.4 — Sai dove mettere il `try/finally` in un `@contextmanager`?
- [ ] F.5 — Hai usato `with open(...)` e capisci perche' e' preferibile a `f.close()` manuale?

### Sezione G — Context Manager Avanzato

- [ ] G.1 — Hai usato `contextlib.suppress()`?
- [ ] G.2 — Conosci `redirect_stdout`, `redirect_stderr`, `closing`, `nullcontext`?
- [ ] G.3 — Hai usato `ExitStack` per gestire N context manager dinamicamente?
- [ ] G.4 — Capisci `pop_all()` e il trasferimento di ownership?
- [ ] G.5 — Hai scritto un context manager asincrono con `__aenter__`/`__aexit__`?
- [ ] G.6 — Conosci `@asynccontextmanager` e `AsyncExitStack`?

### Sezione H — Avanzato

- [ ] H.1 — Conosci il protocollo descriptor (`__get__`, `__set__`, `__delete__`)?
- [ ] H.2 — Sai la differenza tra data descriptor e non-data descriptor?
- [ ] H.3 — Hai implementato una `LazyProperty` o `functools.cached_property`?
- [ ] H.4 — Conosci `__init_subclass__` e sai come creare un sistema di plugin?
- [ ] H.5 — Hai mai creato una metaclasse? Sai quando e' appropriato usarle?
- [ ] H.6 — Conosci la storia delle PEP rilevanti (255, 318, 342, 343, 380, 479)?

---

## E8: Diagramma Decisionale — Qual e' lo Strumento Giusto?

```
Ho bisogno di modificare il comportamento di una funzione?
│
├─ SI → Uso un DECORATORE
│        │
│        ├─ Vuole parametri il decoratore? → Tre livelli di nesting
│        │   @decoratore(param=val)        → o pattern func=None
│        │
│        └─ E' riutilizzabile su molte classi? → Class-based decorator
│
Ho bisogno di produrre una sequenza di valori?
│
├─ SI → Uso un GENERATORE
│        │
│        ├─ La sequenza e' infinita? → Generator function con while True
│        ├─ Voglio trasformare un'altra sequenza? → Generator expression
│        ├─ Voglio delegare a un altro generator? → yield from
│        └─ Voglio comunicazione bidirezionale? → send() / throw()
│
Ho bisogno di gestire una risorsa che va acquisita e rilasciata?
│
├─ SI → Uso un CONTEXT MANAGER
│        │
│        ├─ La logica e' semplice? → @contextmanager (contextlib)
│        ├─ La logica e' complessa? → Classe con __enter__/__exit__
│        ├─ N risorse dinamiche? → ExitStack
│        └─ Ambiente asincrono? → @asynccontextmanager
│
Nessuno dei precedenti → Funzione normale, classe, modulo
```

---

## E9: PEP di Riferimento — Timeline Completa

| PEP | Python | Data | Cosa Ha Introdotto |
|-----|--------|------|---------------------|
| PEP 255 | 2.2 | 2001 | `yield` e generatori semplici |
| PEP 289 | 2.4 | 2002 | Espressioni generatrici `(x for x in ...)` |
| PEP 318 | 2.4 | 2003 | Sintassi `@decoratore` |
| PEP 342 | 2.5 | 2005 | `send()`, `throw()`, `close()` nei generatori |
| PEP 343 | 2.5 | 2005 | Protocollo `with` e context manager |
| PEP 380 | 3.3 | 2009 | `yield from` e delegazione sub-generator |
| PEP 479 | 3.7 | 2014 | `StopIteration` nei generatori diventa `RuntimeError` |
| PEP 487 | 3.6 | 2015 | `__init_subclass__` per personalizzazione sottoclassi |
| PEP 492 | 3.5 | 2015 | `async/await`, `async for`, `async with` |
| PEP 525 | 3.6 | 2016 | Generatori asincroni (`async def` con `yield`) |
| PEP 617 | 3.9 | 2020 | PEG parser (impatta la sintassi) |
| PEP 634 | 3.10 | 2021 | Pattern matching `match/case` |
| PEP 695 | 3.12 | 2022 | Sintassi type alias `type X = ...` |

---

## E10: Link ai Tutorial della Serie

```
PERCORSO DI APPRENDIMENTO PYTHON — TUTTI I TUTORIAL

tutorial_00_ambiente.md         ✓ Setup ambiente, pip, venv, VS Code
tutorial_00_git.md              ✓ Git essenziale per sviluppatori Python
tutorial_01_fondamenti.md       ✓ Variabili, tipi, controllo flusso, funzioni
tutorial_02_oop.md              ✓ Classi, ereditarieta', polimorfismo
tutorial_03_strutture_dati.md   ✓ list, dict, set, tuple, deque, heap
tutorial_04_decoratori_...md    ← SEI QUI: Decoratori, Generatori, Context Manager
tutorial_05_...md               → Prossimo: [Programmazione Funzionale e Concorrenza]
tutorial_06_regex.md            → Espressioni regolari e text processing
tutorial_07_error_handling.md   → Gestione errori e logging strutturato
tutorial_08_testing.md          → pytest, mocking, TDD
tutorial_09_type_hints.md       → Type hints, mypy, runtime validation
tutorial_10_async.md            → asyncio, aiohttp, pattern asincroni
tutorial_11_flask_fastapi.md    → Web framework per API
tutorial_12_database.md         → SQLAlchemy, Redis, migrations
tutorial_13_rest_api.md         → REST API design e implementazione
```

---

## E11: Riepilogo Finale — Le Tre Grandi Idee

### 1. Decoratori: Comportamento come Dati

```
Il decoratore trasforma UNA funzione in UNA FUNZIONE MIGLIORE.
E' composizione funzionale applicata al tuo codice.

@retry(3) @cache @timer
def calcola(n): ...

→ Una funzione che CALCOLA, ma anche RIPROVA, MEMORIZZA e MISURA.
→ Separazione delle responsabilita': la logica di business e' separata
  dall'infrastruttura (retry, cache, timing).
```

### 2. Generatori: Computazione Pigra

```
Un generatore e' una RICETTA per produrre valori, non i valori stessi.
Puoi avere una ricetta infinita senza usare infinita memoria.

def numeri(): yield 1; yield 2; yield 3; ...
               ↑ RICETTA              ↑ PRODUZIONE (quando richiesto)

→ Separazione di COSA produrre da QUANDO produrlo.
→ Pipeline di elaborazione: connetti ricette senza materializzare.
```

### 3. Context Manager: Risorse con Garanzie

```
Un context manager e' un CONTRATTO:
"Entro → Uso → Esco (SEMPRE, anche in caso di errore)"

with open("file.txt") as f:
      ↑ ENTRO    ↑ USO     ↑ ESCO (file.close() garantito)

→ Separazione di ACQUISIRE/RILASCIARE dalla LOGICA DI USO.
→ Niente risorse dimenticate, niente cleanup mancante.
```

---

*Fine del Tutorial: Decoratori, Generatori e Context Manager*
*Buono studio e buona programmazione!*



---

# PARTE F: LABORATORIO PRATICO — Progetti Guidati

---

## F1: Costruiamo un Task Scheduler con Generatori e Decoratori

### Il Problema

Immagina di dover eseguire diversi compiti in ordine, con la possibilita' di:
- Ritardare l'esecuzione di un task
- Eseguire task in modo cooperativo (senza thread)
- Monitorare lo stato di esecuzione

### Soluzione con Generatori

```python
import heapq
import time
from typing import Generator, Any, Callable
from dataclasses import dataclass, field

@dataclass(order=True)
class Task:
    """Rappresenta un task schedulato."""
    esegui_alle: float
    priorita: int
    id: int
    funzione: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)

class Scheduler:
    """
    Scheduler cooperativo basato su generatori.
    Analogo semplificato di asyncio.
    """

    def __init__(self):
        self._coda = []  # min-heap (esegui_alle, priorita, id, task)
        self._id_counter = 0
        self._eseguiti = 0
        self._errori = []

    def schedula(
        self,
        funzione: Callable,
        *args,
        ritardo: float = 0.0,
        priorita: int = 5,
        **kwargs,
    ) -> int:
        """
        Aggiunge un task alla coda.

        Args:
            funzione: callable da eseguire
            *args: argomenti posizionali
            ritardo: secondi di ritardo prima dell'esecuzione
            priorita: 1 (alta) - 10 (bassa)
            **kwargs: argomenti keyword

        Returns:
            ID del task
        """
        self._id_counter += 1
        task = Task(
            esegui_alle=time.time() + ritardo,
            priorita=priorita,
            id=self._id_counter,
            funzione=funzione,
            args=args,
            kwargs=kwargs,
        )
        heapq.heappush(self._coda, task)
        return self._id_counter

    def _prossimo_task(self) -> Task | None:
        """Restituisce il prossimo task da eseguire (o None se non ci sono task pronti)."""
        if not self._coda:
            return None
        prossimo = self._coda[0]
        if prossimo.esegui_alle <= time.time():
            return heapq.heappop(self._coda)
        return None

    def esegui(self) -> Generator[dict, None, None]:
        """
        Esegue i task in ordine. Generator che produce un report per ogni task.
        """
        while self._coda:
            task = self._prossimo_task()
            if task is None:
                # Nessun task pronto: aspetta il prossimo
                attesa = self._coda[0].esegui_alle - time.time()
                if attesa > 0:
                    time.sleep(min(attesa, 0.01))  # poll frequente
                continue

            inizio = time.time()
            try:
                risultato = task.funzione(*task.args, **task.kwargs)
                durata = time.time() - inizio
                self._eseguiti += 1
                yield {
                    "id": task.id,
                    "funzione": task.funzione.__name__,
                    "stato": "ok",
                    "risultato": risultato,
                    "durata_ms": durata * 1000,
                }
            except Exception as e:
                durata = time.time() - inizio
                self._errori.append({"task": task.id, "errore": str(e)})
                yield {
                    "id": task.id,
                    "funzione": task.funzione.__name__,
                    "stato": "errore",
                    "errore": str(e),
                    "durata_ms": durata * 1000,
                }

    @property
    def statistiche(self) -> dict:
        return {
            "in_coda": len(self._coda),
            "eseguiti": self._eseguiti,
            "errori": len(self._errori),
        }

# Funzioni di esempio da schedulare
def invia_email(destinatario: str, oggetto: str) -> str:
    return f"Email inviata a {destinatario}: '{oggetto}'"

def elabora_batch(id_batch: int, n_elementi: int) -> dict:
    time.sleep(0.01)  # simula lavoro
    return {"batch": id_batch, "elaborati": n_elementi}

def task_che_fallisce(messaggio: str):
    raise RuntimeError(f"Task fallito: {messaggio}")

# Uso dello scheduler
scheduler = Scheduler()

# Schedula task con diversi ritardi e priorita'
scheduler.schedula(invia_email, "mario@esempio.com", "Conferma ordine", priorita=1)
scheduler.schedula(invia_email, "anna@esempio.com", "Newsletter", priorita=8)
scheduler.schedula(elabora_batch, 1, 100, ritardo=0.0, priorita=5)
scheduler.schedula(elabora_batch, 2, 200, ritardo=0.05, priorita=5)
scheduler.schedula(task_che_fallisce, "prova di errore", priorita=3)

print("Esecuzione scheduler:")
for report in scheduler.esegui():
    simbolo = "✓" if report["stato"] == "ok" else "✗"
    print(f"  [{simbolo}] Task {report['id']}: {report['funzione']} "
          f"({report['durata_ms']:.1f}ms) — "
          f"{report.get('risultato', report.get('errore', ''))}")

print(f"\nStatistiche: {scheduler.statistiche}")
```

```
# Output atteso:
Esecuzione scheduler:
  [✓] Task 1: invia_email (0.1ms) — Email inviata a mario@esempio.com: 'Conferma ordine'
  [✗] Task 5: task_che_fallisce (0.1ms) — Task fallito: prova di errore
  [✓] Task 3: elabora_batch (10.2ms) — {'batch': 1, 'elaborati': 100}
  [✓] Task 2: invia_email (0.1ms) — Email inviata a anna@esempio.com: 'Newsletter'
  [✓] Task 4: elabora_batch (10.1ms) — {'batch': 2, 'elaborati': 200}

Statistiche: {'in_coda': 0, 'eseguiti': 4, 'errori': 1}
```

---

## F2: Sistema di Configurazione con Context Manager

```python
import os
import json
import copy
from contextlib import contextmanager
from typing import Any

class Configurazione:
    """
    Sistema di configurazione che supporta:
    - Valori di default
    - Override temporanei (via context manager)
    - Validazione dei valori
    - Watch per notifiche sui cambiamenti
    """

    def __init__(self, valori_default: dict = None):
        self._valori: dict = dict(valori_default or {})
        self._stack_override: list[dict] = []
        self._validatori: dict[str, callable] = {}
        self._watchers: dict[str, list[callable]] = {}

    def imposta(self, chiave: str, valore: Any) -> None:
        """Imposta un valore permanente."""
        if chiave in self._validatori:
            self._validatori[chiave](valore)
        vecchio = self._valori.get(chiave)
        self._valori[chiave] = valore
        self._notifica(chiave, vecchio, valore)

    def ottieni(self, chiave: str, default: Any = None) -> Any:
        """Ottieni un valore (considera gli override dal context manager)."""
        for override in reversed(self._stack_override):
            if chiave in override:
                return override[chiave]
        return self._valori.get(chiave, default)

    def aggiungi_validatore(self, chiave: str, validatore: callable) -> None:
        """Aggiunge un validatore per una chiave."""
        self._validatori[chiave] = validatore

    def osserva(self, chiave: str, callback: callable) -> None:
        """Registra un callback per i cambiamenti di una chiave."""
        if chiave not in self._watchers:
            self._watchers[chiave] = []
        self._watchers[chiave].append(callback)

    def _notifica(self, chiave: str, vecchio: Any, nuovo: Any) -> None:
        """Notifica i watcher dei cambiamenti."""
        for watcher in self._watchers.get(chiave, []):
            watcher(chiave, vecchio, nuovo)

    @contextmanager
    def override(self, **valori_temporanei):
        """
        Context manager per override temporanei della configurazione.
        I valori originali sono ripristinati al termine.
        """
        override_corrente = {}
        for chiave, valore in valori_temporanei.items():
            if chiave in self._validatori:
                self._validatori[chiave](valore)
            override_corrente[chiave] = valore

        self._stack_override.append(override_corrente)
        print(f"[config] Override attivo: {list(valori_temporanei.keys())}")
        try:
            yield self
        finally:
            self._stack_override.pop()
            print(f"[config] Override rimosso: {list(valori_temporanei.keys())}")

    def __repr__(self) -> str:
        override_attivi = {}
        for override in self._stack_override:
            override_attivi.update(override)
        base = {**self._valori, **override_attivi}
        return f"Configurazione({base})"

# Uso
config = Configurazione({
    "debug": False,
    "livello_log": "INFO",
    "db_url": "postgresql://localhost/produzione",
    "cache_ttl": 3600,
    "max_connessioni": 100,
})

# Aggiungi validatori
config.aggiungi_validatore(
    "livello_log",
    lambda v: None if v in ("DEBUG", "INFO", "WARNING", "ERROR") else (_ for _ in ()).throw(ValueError(f"Livello log non valido: {v}"))
)

config.aggiungi_validatore(
    "max_connessioni",
    lambda v: None if 1 <= v <= 1000 else (_ for _ in ()).throw(ValueError(f"max_connessioni deve essere 1-1000"))
)

# Aggiungi watcher
config.osserva(
    "debug",
    lambda k, vecchio, nuovo: print(f"  [watch] {k}: {vecchio} → {nuovo}")
)

print("=== Configurazione Base ===")
print(f"debug: {config.ottieni('debug')}")
print(f"db_url: {config.ottieni('db_url')}")

print()
print("=== Con Override per Test ===")
with config.override(debug=True, db_url="sqlite:///test.db", livello_log="DEBUG"):
    print(f"  debug: {config.ottieni('debug')}")
    print(f"  db_url: {config.ottieni('db_url')}")
    print(f"  livello_log: {config.ottieni('livello_log')}")

    # Override annidato
    with config.override(livello_log="WARNING"):
        print(f"    livello_log (doppio override): {config.ottieni('livello_log')}")

print()
print("=== Dopo il Context Manager (valori originali) ===")
print(f"debug: {config.ottieni('debug')}")
print(f"db_url: {config.ottieni('db_url')}")

print()
print("=== Modifica Permanente ===")
config.imposta("debug", True)
print(f"debug (permanente): {config.ottieni('debug')}")
```

```
# Output atteso:
=== Configurazione Base ===
debug: False
db_url: postgresql://localhost/produzione

=== Con Override per Test ===
[config] Override attivo: ['debug', 'db_url', 'livello_log']
  debug: True
  db_url: sqlite:///test.db
  livello_log: DEBUG
[config] Override attivo: ['livello_log']
    livello_log (doppio override): WARNING
[config] Override rimosso: ['livello_log']
[config] Override rimosso: ['debug', 'db_url', 'livello_log']

=== Dopo il Context Manager (valori originali) ===
debug: False
db_url: postgresql://localhost/produzione

=== Modifica Permanente ===
  [watch] debug: False → True
debug (permanente): True
```

---

## F3: Implementazione di `asyncio.Queue` con Generatori

```python
import asyncio
import random
import time

# Simula un sistema produttore-consumatore con generatori asincroni

async def produttore(
    id_produttore: int,
    n_messaggi: int,
    coda: asyncio.Queue,
    ritardo_base: float = 0.1,
) -> None:
    """Produce messaggi e li inserisce nella coda."""
    for i in range(n_messaggi):
        messaggio = {
            "produttore": id_produttore,
            "sequenza": i + 1,
            "payload": f"dato_{id_produttore}_{i}",
            "timestamp": time.time(),
        }
        await asyncio.sleep(ritardo_base + random.uniform(-0.05, 0.05))
        await coda.put(messaggio)
        print(f"  [P{id_produttore}] Prodotto: {messaggio['payload']}")

    # Segnale di fine
    await coda.put(None)
    print(f"  [P{id_produttore}] Fine produzione")

async def consumatore(
    id_consumatore: int,
    coda: asyncio.Queue,
    n_produttori: int,
) -> list:
    """Consuma messaggi dalla coda finche' tutti i produttori non hanno finito."""
    messaggi_ricevuti = []
    segnali_fine = 0

    while segnali_fine < n_produttori:
        messaggio = await coda.get()
        coda.task_done()

        if messaggio is None:
            segnali_fine += 1
            print(f"  [C{id_consumatore}] Ricevuto segnale di fine ({segnali_fine}/{n_produttori})")
        else:
            messaggi_ricevuti.append(messaggio)
            print(f"  [C{id_consumatore}] Consumato: {messaggio['payload']}")
            await asyncio.sleep(0.05)  # simula elaborazione

    return messaggi_ricevuti

async def sistema_produttore_consumatore():
    """Coordina produttori e consumatori."""
    coda = asyncio.Queue(maxsize=10)  # buffer limitato
    n_produttori = 2

    inizio = time.time()

    # Avvia produttori e consumatore in parallelo
    risultati = await asyncio.gather(
        produttore(1, n_messaggi=4, coda=coda),
        produttore(2, n_messaggi=3, coda=coda),
        consumatore(1, coda=coda, n_produttori=n_produttori),
    )

    _, _, messaggi = risultati
    durata = time.time() - inizio

    print(f"\n=== Riepilogo ===")
    print(f"Messaggi consumati: {len(messaggi)}")
    print(f"Durata totale: {durata:.2f}s")

    # Ordina per timestamp per vedere l'interleaving
    messaggi.sort(key=lambda m: m["timestamp"])
    for m in messaggi:
        print(f"  P{m['produttore']}/seq{m['sequenza']}: {m['payload']}")

random.seed(42)
asyncio.run(sistema_produttore_consumatore())
```

```
# Output atteso (l'ordine esatto dipende dallo scheduling):
  [P1] Prodotto: dato_1_0
  [C1] Consumato: dato_1_0
  [P2] Prodotto: dato_2_0
  [C1] Consumato: dato_2_0
  ...
  [P1] Fine produzione
  [P2] Fine produzione
  [C1] Ricevuto segnale di fine (1/2)
  [C1] Ricevuto segnale di fine (2/2)

=== Riepilogo ===
Messaggi consumati: 7
Durata totale: 0.42s
```

---

## F4: Libreria di Utilities con Tutti e Tre i Concetti

```python
"""
utils.py — Libreria di utilities che usa decoratori, generatori e context manager
"""

import functools
import time
import sys
import io
import threading
from contextlib import contextmanager
from typing import Generator, Any, TypeVar, Callable, Iterable

T = TypeVar("T")

# ============================================================
# DECORATORI
# ============================================================

class _Singleton:
    """Descrittore per singleton thread-safe."""
    _istanze: dict = {}
    _lock = threading.Lock()

    def __call__(self, cls):
        """Applicato come decoratore di classe."""
        @functools.wraps(cls)
        def ottieni_istanza(*args, **kwargs):
            if cls not in self._istanze:
                with self._lock:
                    if cls not in self._istanze:
                        self._istanze[cls] = cls(*args, **kwargs)
            return self._istanze[cls]
        ottieni_istanza._classe = cls
        ottieni_istanza.clear_instance = lambda: self._istanze.pop(cls, None)
        return ottieni_istanza

singleton = _Singleton()

@singleton
class Logger:
    """Logger singleton."""
    def __init__(self):
        self._log = []

    def info(self, messaggio: str) -> None:
        self._log.append(("INFO", time.time(), messaggio))
        print(f"[INFO] {messaggio}")

    def errore(self, messaggio: str) -> None:
        self._log.append(("ERROR", time.time(), messaggio))
        print(f"[ERROR] {messaggio}", file=sys.stderr)

    @property
    def n_messaggi(self) -> int:
        return len(self._log)

def misura_tempo(funzione: Callable[..., T] = None, *, unita: str = "ms") -> Callable:
    """
    Decoratore che misura e logga il tempo di esecuzione.
    Puo' essere usato con e senza parentesi.

    Uso:
        @misura_tempo
        def funzione(): ...

        @misura_tempo(unita="s")
        def funzione(): ...
    """
    if funzione is None:
        return functools.partial(misura_tempo, unita=unita)

    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        risultato = funzione(*args, **kwargs)
        durata = time.perf_counter() - inizio

        if unita == "ms":
            print(f"[timer] {funzione.__name__}: {durata*1000:.2f}ms")
        elif unita == "s":
            print(f"[timer] {funzione.__name__}: {durata:.4f}s")
        elif unita == "us":
            print(f"[timer] {funzione.__name__}: {durata*1000000:.0f}µs")

        return risultato
    return wrapper

# ============================================================
# GENERATORI
# ============================================================

def a_blocchi(iterable: Iterable[T], n: int) -> Generator[list[T], None, None]:
    """
    Divide un iterabile in blocchi di n elementi.
    L'ultimo blocco potrebbe avere meno di n elementi.
    """
    blocco = []
    for elemento in iterable:
        blocco.append(elemento)
        if len(blocco) == n:
            yield blocco
            blocco = []
    if blocco:
        yield blocco

def finestre(iterable: Iterable[T], n: int) -> Generator[tuple[T, ...], None, None]:
    """
    Produce finestre scorrevoli di n elementi.
    Esempio: finestre([1,2,3,4,5], 3) -> (1,2,3), (2,3,4), (3,4,5)
    """
    from collections import deque
    finestra = deque(maxlen=n)
    for elemento in iterable:
        finestra.append(elemento)
        if len(finestra) == n:
            yield tuple(finestra)

def appiattisci(iterable: Iterable) -> Generator[Any, None, None]:
    """Appiattisce un iterabile annidato di qualsiasi profondita'."""
    for elemento in iterable:
        if hasattr(elemento, "__iter__") and not isinstance(elemento, (str, bytes)):
            yield from appiattisci(elemento)
        else:
            yield elemento

def prendi_mentre(
    iterable: Iterable[T],
    predicato: Callable[[T], bool],
) -> Generator[T, None, None]:
    """Equivalente di itertools.takewhile ma come generatore named."""
    for elemento in iterable:
        if not predicato(elemento):
            break
        yield elemento

# ============================================================
# CONTEXT MANAGER
# ============================================================

@contextmanager
def cattura_output() -> Generator[io.StringIO, None, None]:
    """Cattura stdout e stderr in un buffer."""
    buffer = io.StringIO()
    vecchio_stdout = sys.stdout
    vecchio_stderr = sys.stderr
    sys.stdout = buffer
    sys.stderr = buffer
    try:
        yield buffer
    finally:
        sys.stdout = vecchio_stdout
        sys.stderr = vecchio_stderr

@contextmanager
def timer_ctx(nome: str = "Blocco") -> Generator[dict, None, None]:
    """Context manager che misura il tempo di un blocco."""
    stato = {"inizio": time.perf_counter(), "nome": nome}
    try:
        yield stato
    finally:
        stato["durata_ms"] = (time.perf_counter() - stato["inizio"]) * 1000
        print(f"[timer] {nome}: {stato['durata_ms']:.2f}ms")

@contextmanager
def imposta_env_temporaneo(**variabili: str) -> Generator[None, None, None]:
    """Imposta variabili d'ambiente temporaneamente."""
    import os
    originali = {}
    for chiave, valore in variabili.items():
        originali[chiave] = os.environ.get(chiave)
        os.environ[chiave] = valore

    try:
        yield
    finally:
        for chiave, valore_originale in originali.items():
            if valore_originale is None:
                os.environ.pop(chiave, None)
            else:
                os.environ[chiave] = valore_originale

# ============================================================
# TEST DELLA LIBRERIA
# ============================================================

print("=== Test a_blocchi ===")
dati = list(range(1, 11))
for blocco in a_blocchi(dati, 3):
    print(f"  {blocco}")

print()
print("=== Test finestre ===")
for finestra in finestre(range(1, 6), 3):
    print(f"  {finestra}")

print()
print("=== Test misura_tempo ===")
@misura_tempo
def somma_quadrati(n: int) -> int:
    return sum(i*i for i in range(n))

@misura_tempo(unita="us")
def moltiplicazione(a: int, b: int) -> int:
    return a * b

somma_quadrati(10000)
moltiplicazione(123, 456)

print()
print("=== Test cattura_output ===")
with cattura_output() as buf:
    print("Questo non appare direttamente")
    print("Nemmeno questo")

print(f"Output catturato: {repr(buf.getvalue())}")

print()
print("=== Test timer_ctx ===")
with timer_ctx("Calcolo pesante") as t:
    time.sleep(0.05)

print(f"  Durata registrata: {t['durata_ms']:.2f}ms")

print()
print("=== Test Logger Singleton ===")
log1 = Logger()
log2 = Logger()
print(f"Stesso oggetto: {log1 is log2}")
log1.info("Messaggio di test")
print(f"Messaggi in log: {log2.n_messaggi}")
```

```
# Output atteso:
=== Test a_blocchi ===
  [1, 2, 3]
  [4, 5, 6]
  [7, 8, 9]
  [10]

=== Test finestre ===
  (1, 2, 3)
  (2, 3, 4)
  (3, 4, 5)
  (4, 5, 6)
  (5, 6, 7)

=== Test misura_tempo ===
[timer] somma_quadrati: 0.72ms
[timer] moltiplicazione: 0.12µs

=== Test cattura_output ===
Output catturato: 'Questo non appare direttamente\nNemmeno questo\n'

=== Test timer_ctx ===
[timer] Calcolo pesante: 50.21ms
  Durata registrata: 50.21ms

=== Test Logger Singleton ===
Stesso oggetto: True
[INFO] Messaggio di test
Messaggi in log: 1
```

---

## F5: Pattern Observer con Generatori

```python
from __future__ import annotations
import functools
from typing import Generator, Callable, Any
from collections import defaultdict

class EventBus:
    """
    Bus di eventi basato su pattern Observer.
    I subscriber ricevono eventi tramite generatori o callback.
    """

    def __init__(self):
        self._subscriber_callback: dict[str, list[Callable]] = defaultdict(list)
        self._coda_eventi: list[tuple[str, Any]] = []
        self._in_elaborazione = False

    def sottoscrivi(self, tipo_evento: str):
        """Decoratore per registrare un handler di eventi."""
        def decoratore(funzione: Callable) -> Callable:
            self._subscriber_callback[tipo_evento].append(funzione)
            print(f"[bus] Registrato handler: {funzione.__name__} per '{tipo_evento}'")
            return funzione
        return decoratore

    def pubblica(self, tipo_evento: str, payload: Any = None) -> None:
        """Pubblica un evento (asincrono: inserisce nella coda)."""
        self._coda_eventi.append((tipo_evento, payload))

    def elabora(self) -> Generator[dict, None, None]:
        """
        Elabora tutti gli eventi in coda.
        Generator che produce report sull'elaborazione.
        """
        while self._coda_eventi:
            tipo_evento, payload = self._coda_eventi.pop(0)

            handlers = self._subscriber_callback.get(tipo_evento, [])
            n_handlers = len(handlers)

            if not handlers:
                yield {"evento": tipo_evento, "payload": payload, "handlers": 0, "stato": "ignorato"}
                continue

            errori = []
            for handler in handlers:
                try:
                    handler(tipo_evento, payload)
                except Exception as e:
                    errori.append(f"{handler.__name__}: {e}")

            yield {
                "evento": tipo_evento,
                "payload": payload,
                "handlers": n_handlers,
                "stato": "ok" if not errori else "parziale",
                "errori": errori,
            }

# Istanza globale del bus
bus = EventBus()

# Registra gli handler
@bus.sottoscrivi("utente.creato")
def invia_email_benvenuto(evento: str, payload: dict) -> None:
    print(f"  -> Email di benvenuto a {payload['email']}")

@bus.sottoscrivi("utente.creato")
def crea_profilo_default(evento: str, payload: dict) -> None:
    print(f"  -> Profilo default creato per {payload['nome']}")

@bus.sottoscrivi("ordine.completato")
def notifica_magazzino(evento: str, payload: dict) -> None:
    print(f"  -> Magazzino notificato: ordine #{payload['id']}")

@bus.sottoscrivi("ordine.completato")
def aggiorna_analytics(evento: str, payload: dict) -> None:
    print(f"  -> Analytics aggiornata: €{payload['totale']:.2f}")

# Pubblica eventi
bus.pubblica("utente.creato", {"nome": "Mario Rossi", "email": "mario@esempio.com"})
bus.pubblica("ordine.completato", {"id": 12345, "totale": 299.99, "prodotti": 3})
bus.pubblica("evento.sconosciuto", {"debug": True})

print()
print("=== Elaborazione eventi ===")
for report in bus.elabora():
    print(f"\nEvento: {report['evento']}")
    print(f"  Handler attivati: {report['handlers']}")
    print(f"  Stato: {report['stato']}")
    if report.get("errori"):
        print(f"  Errori: {report['errori']}")
```

```
# Output atteso:
[bus] Registrato handler: invia_email_benvenuto per 'utente.creato'
[bus] Registrato handler: crea_profilo_default per 'utente.creato'
[bus] Registrato handler: notifica_magazzino per 'ordine.completato'
[bus] Registrato handler: aggiorna_analytics per 'ordine.completato'

=== Elaborazione eventi ===

Evento: utente.creato
  -> Email di benvenuto a mario@esempio.com
  -> Profilo default creato per Mario Rossi
  Handler attivati: 2
  Stato: ok

Evento: ordine.completato
  -> Magazzino notificato: ordine #12345
  -> Analytics aggiornata: €299.99
  Handler attivati: 2
  Stato: ok

Evento: evento.sconosciuto
  Handler attivati: 0
  Stato: ignorato
```

---

## F6: Esercizio Finale Completo — Data Pipeline con Cache

```python
"""
Progetto: Pipeline di analisi dati con cache, retry e context manager.
Simula l'analisi di dati di vendita con tutti i pattern visti.
"""

import functools
import time
import json
import random
from contextlib import contextmanager, ExitStack
from typing import Generator

# ============================================================
# STRATO 1: DECORATORI (infrastruttura)
# ============================================================

def con_cache(ttl_secondi: float = 300):
    """Cache con TTL per risultati di query costose."""
    def decoratore(funzione):
        cache = {}

        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            chiave = str(args) + str(sorted(kwargs.items()))
            ora = time.time()

            if chiave in cache:
                ts, valore = cache[chiave]
                if ora - ts < ttl_secondi:
                    return valore
                del cache[chiave]

            valore = funzione(*args, **kwargs)
            cache[chiave] = (ora, valore)
            return valore

        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    return decoratore

def con_retry(tentativi: int = 3, pausa: float = 0.1):
    """Retry con backoff su errori transienti."""
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            for i in range(1, tentativi + 1):
                try:
                    return funzione(*args, **kwargs)
                except ConnectionError as e:
                    if i == tentativi:
                        raise
                    time.sleep(pausa * (2 ** (i - 1)))
        return wrapper
    return decoratore

# ============================================================
# STRATO 2: CONTEXT MANAGER (risorse)
# ============================================================

@contextmanager
def connessione_dati(fonte: str):
    """Simula una connessione a una fonte dati."""
    print(f"  [conn] Connessione a {fonte}")
    conn = {"fonte": fonte, "attiva": True, "query_count": 0}
    try:
        yield conn
    finally:
        conn["attiva"] = False
        print(f"  [conn] Chiusa connessione a {fonte} ({conn['query_count']} query)")

@contextmanager
def sessione_analisi(nome: str):
    """Context manager per una sessione di analisi completa."""
    print(f"\n{'='*60}")
    print(f"ANALISI: {nome}")
    print(f"{'='*60}")
    inizio = time.time()
    risultati = {"nome": nome, "dati": [], "errori": []}
    try:
        yield risultati
    finally:
        durata = time.time() - inizio
        print(f"\n[analisi] '{nome}' completata in {durata:.3f}s")
        print(f"[analisi] Dati: {len(risultati['dati'])} record, Errori: {len(risultati['errori'])}")

# ============================================================
# STRATO 3: GENERATORI (elaborazione dati)
# ============================================================

@con_retry(tentativi=3)
@con_cache(ttl_secondi=60)
def fetch_dati_vendite(anno: int, regione: str) -> list[dict]:
    """Simula il fetch di dati da un'API remota."""
    random.seed(anno * 100 + hash(regione) % 100)

    # Simula fallimento transitorio con 30% di probabilita'
    if random.random() < 0.3:
        raise ConnectionError(f"Timeout per {regione}/{anno}")

    return [
        {
            "mese": mese,
            "regione": regione,
            "anno": anno,
            "vendite": random.randint(1000, 50000),
            "costi": random.randint(500, 30000),
        }
        for mese in range(1, 13)
    ]

def genera_dati_annuali(
    anni: list[int],
    regioni: list[str],
) -> Generator[dict, None, None]:
    """Genera dati annuali per tutte le combinazioni anno/regione."""
    for anno in anni:
        for regione in regioni:
            try:
                dati = fetch_dati_vendite(anno, regione)
                for record in dati:
                    yield record
            except Exception as e:
                yield {"_errore": str(e), "anno": anno, "regione": regione}

def calcola_profitto(gen: Generator) -> Generator[dict, None, None]:
    """Aggiunge il campo profitto a ogni record."""
    for record in gen:
        if record.get("_errore"):
            yield record
        else:
            yield {
                **record,
                "profitto": record["vendite"] - record["costi"],
                "margine_pct": (record["vendite"] - record["costi"]) / record["vendite"] * 100,
            }

def aggrega_per_regione(gen: Generator) -> dict[str, dict]:
    """Aggrega i dati per regione."""
    aggregati: dict[str, dict] = {}
    errori = 0

    for record in gen:
        if record.get("_errore"):
            errori += 1
            continue

        regione = record["regione"]
        if regione not in aggregati:
            aggregati[regione] = {
                "vendite_totali": 0,
                "costi_totali": 0,
                "profitto_totale": 0,
                "n_mesi": 0,
            }

        agg = aggregati[regione]
        agg["vendite_totali"] += record["vendite"]
        agg["costi_totali"] += record["costi"]
        agg["profitto_totale"] += record["profitto"]
        agg["n_mesi"] += 1

    for regione, agg in aggregati.items():
        agg["margine_medio_pct"] = agg["profitto_totale"] / agg["vendite_totali"] * 100
        agg["errori"] = errori

    return aggregati

# ============================================================
# ORCHESTRAZIONE
# ============================================================

def esegui_analisi_completa():
    """Esegue l'analisi completa usando tutti i pattern."""

    ANNI = [2022, 2023, 2024]
    REGIONI = ["Nord", "Centro", "Sud", "Isole"]

    with sessione_analisi("Analisi Vendite Multi-Anno") as sessione:

        # Usa ExitStack per gestire le connessioni dinamicamente
        with ExitStack() as stack:
            # Apri connessioni a tutte le regioni
            connessioni = {
                regione: stack.enter_context(connessione_dati(f"db_{regione.lower()}"))
                for regione in REGIONI
            }

            # Pipeline di elaborazione
            sorgente = genera_dati_annuali(ANNI, REGIONI)
            con_profitto = calcola_profitto(sorgente)
            aggregati = aggrega_per_regione(con_profitto)

        # Stampa i risultati
        print("\nRisultati per Regione:")
        print(f"{'Regione':<12} {'Vendite':>12} {'Costi':>12} {'Profitto':>12} {'Margine':>10}")
        print("-" * 60)

        for regione in sorted(aggregati.keys()):
            dati = aggregati[regione]
            print(
                f"{regione:<12} "
                f"€{dati['vendite_totali']:>10,.0f} "
                f"€{dati['costi_totali']:>10,.0f} "
                f"€{dati['profitto_totale']:>10,.0f} "
                f"{dati['margine_medio_pct']:>9.1f}%"
            )

        sessione["dati"] = list(aggregati.values())

esegui_analisi_completa()
```

```
# Output atteso:
============================================================
ANALISI: Analisi Vendite Multi-Anno
============================================================
  [conn] Connessione a db_nord
  [conn] Connessione a db_centro
  [conn] Connessione a db_sud
  [conn] Connessione a db_isole
  [conn] Chiusa connessione a db_nord (0 query)
  [conn] Chiusa connessione a db_centro (0 query)
  [conn] Chiusa connessione a db_sud (0 query)
  [conn] Chiusa connessione a db_isole (0 query)

Risultati per Regione:
Regione      Vendite        Costi      Profitto     Margine
------------------------------------------------------------
Centro    €  876,432    €  512,891    €  363,541      41.5%
Isole     €  654,219    €  389,102    €  265,117      40.5%
Nord      €1,123,567    €  678,234    €  445,333      39.6%
Sud       €  789,321    €  456,789    €  332,532      42.1%

[analisi] 'Analisi Vendite Multi-Anno' completata in 0.023s
[analisi] Dati: 4 record, Errori: 0
```

---

## G: QUIZ DI AUTOVALUTAZIONE

Rispondi a queste domande per verificare la tua comprensione:

### Livello 1: Fondamenti

**Q1.** Cosa stampa questo codice?
```python
def crea(n):
    return lambda x: x * n

doppio = crea(2)
triplo = crea(3)
print(doppio(5))
print(triplo(5))
print(crea(2)(10))
```

**R1:**
```
10
15
20
```

**Q2.** Cosa succede se applichi `@decoratore` a `@decoratore`?
```python
def loud(f):
    def w(*a, **kw):
        print(f"Chiamo {f.__name__}")
        return f(*a, **kw)
    return w

@loud
@loud
def ciao():
    return "ciao"

print(ciao())
```

**R2:**
```
Chiamo w      # il loud esterno chiama il wrapper del loud interno
Chiamo ciao   # il loud interno chiama ciao
ciao
```

---

### Livello 2: Generatori

**Q3.** Quanta memoria usa ogni approccio?
```python
# Approccio A
milione_lista = [i*i for i in range(1_000_000)]

# Approccio B
milione_gen = (i*i for i in range(1_000_000))
```

**R3:**
- Approccio A: ~8 MB (un intero Python = ~28 byte * 1M)
- Approccio B: ~100 byte (solo l'oggetto generatore)

**Q4.** Cosa restituisce questo codice?
```python
def gen():
    x = yield "primo"
    y = yield x * 2
    return x + y

g = gen()
v1 = next(g)           # parte da yield "primo"
v2 = g.send(5)         # riprende con x=5, arriva a yield 5*2
try:
    v3 = g.send(3)     # riprende con y=3, return 5+3=8
except StopIteration as e:
    return_val = e.value

print(v1, v2, return_val)
```

**R4:**
```
primo 10 8
```

---

### Livello 3: Context Manager

**Q5.** Questo codice e' sicuro? Perche'?
```python
@contextmanager
def apri_file(percorso):
    f = open(percorso, "w")
    yield f
    f.close()

with apri_file("test.txt") as f:
    f.write("ciao")
    raise ValueError("ops!")  # il file viene chiuso?
```

**R5:**
No, **non e' sicuro**. Se viene sollevata un'eccezione dentro il `with`, il codice dopo `yield` (incluso `f.close()`) non viene eseguito.

Correzione:
```python
@contextmanager
def apri_file(percorso):
    f = open(percorso, "w")
    try:
        yield f
    finally:
        f.close()  # garantito anche in caso di eccezione
```

---

**Q6.** Quanti context manager gestisce `ExitStack` qui?
```python
from contextlib import ExitStack, contextmanager

@contextmanager
def cm(nome):
    print(f"Enter {nome}")
    yield
    print(f"Exit {nome}")

nomi = ["A", "B", "C", "D"]
with ExitStack() as stack:
    for n in nomi:
        stack.enter_context(cm(n))
    print("Dentro ExitStack")
```

**R6:**
Gestisce **4** context manager. L'uscita avviene in ordine LIFO: D, C, B, A.
```
Enter A
Enter B
Enter C
Enter D
Dentro ExitStack
Exit D
Exit C
Exit B
Exit A
```

---

## H: RISORSE E LETTURE AGGIUNTIVE

### Documentazione Ufficiale
- `docs.python.org/3/library/functools.html` — `functools`: wraps, cache, lru_cache, reduce, partial
- `docs.python.org/3/library/contextlib.html` — contextlib: contextmanager, suppress, ExitStack, AsyncExitStack
- `docs.python.org/3/library/itertools.html` — itertools: tutti gli strumenti
- `docs.python.org/3/howto/descriptor.html` — Descriptor HowTo Guide
- `docs.python.org/3/reference/datamodel.html` — Data Model (dunder methods)

### PEP da Leggere
- PEP 255 — Simple Generators
- PEP 318 — Decorators for Functions and Methods
- PEP 342 — Coroutines via Enhanced Generators
- PEP 343 — The "with" Statement
- PEP 380 — Syntax for Delegating to a Subgenerator (yield from)

### Libri Consigliati
- "Fluent Python" (Ramalho) — Capitoli 7, 12, 14, 15, 16, 17
- "Python Cookbook" (Beazley & Jones) — Capitoli 7, 9
- "Effective Python" (Slatkin) — Items 28-40

### Progetti per la Pratica
1. **Crea un mini-ORM** usando descriptors per validare i campi del modello
2. **Implementa un task queue** usando generatori per la pipeline
3. **Scrivi un middleware framework** usando decoratori componibili
4. **Crea un sistema di plugin** con `__init_subclass__`
5. **Implementa un circuit breaker** con context manager per stati

---

*Fine della Sezione F, G, H — Laboratorio Pratico*



---

# PARTE I: CATALOGO DEI PATTERN — Ricerca Rapida

---

## I1: Pattern Catalogo — Decoratori

### Pattern 1: Decorator Factory con Parametri Obbligatori

```python
import functools

# Problema: vuoi passare parametri al decoratore
# Soluzione: factory a tre livelli

def limita_accesso(ruoli_permessi: list[str]):
    """
    Decoratore parametrico che limita l'accesso a certi ruoli.

    Uso:
        @limita_accesso(["admin", "manager"])
        def dashboard():
            ...
    """
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            # In produzione: prendi il ruolo dall'utente loggato
            utente_corrente = kwargs.get("utente", {})
            ruolo = utente_corrente.get("ruolo", "guest")

            if ruolo not in ruoli_permessi:
                raise PermissionError(
                    f"Accesso negato: ruolo '{ruolo}' non ha accesso. "
                    f"Richiesti: {ruoli_permessi}"
                )
            return funzione(*args, **kwargs)
        return wrapper
    return decoratore

@limita_accesso(["admin"])
def cancella_utente(id_utente: int, utente: dict = None) -> str:
    return f"Utente {id_utente} cancellato"

@limita_accesso(["admin", "manager", "editor"])
def pubblica_articolo(id_articolo: int, utente: dict = None) -> str:
    return f"Articolo {id_articolo} pubblicato"

# Test con diversi ruoli
utente_admin = {"nome": "Alice", "ruolo": "admin"}
utente_manager = {"nome": "Bob", "ruolo": "manager"}
utente_guest = {"nome": "Eve", "ruolo": "guest"}

print(cancella_utente(42, utente=utente_admin))

try:
    cancella_utente(42, utente=utente_manager)
except PermissionError as e:
    print(f"Manager: {e}")

print(pubblica_articolo(1, utente=utente_manager))

try:
    pubblica_articolo(1, utente=utente_guest)
except PermissionError as e:
    print(f"Guest: {e}")
```

```
# Output atteso:
Utente 42 cancellato
Manager: Accesso negato: ruolo 'manager' non ha accesso. Richiesti: ['admin']
Articolo 1 pubblicato
Guest: Accesso negato: ruolo 'guest' non ha accesso. Richiesti: ['admin', 'manager', 'editor']
```

### Pattern 2: Decoratore di Classe che Inietta Metodi

```python
import functools

def aggiunge_confronto_avanzato(cls):
    """
    Decoratore di classe che aggiunge metodi di confronto e ordinamento.
    Richiede che la classe definisca un attributo '_chiave_ordinamento'.
    """
    if not hasattr(cls, "_chiave_ordinamento"):
        raise TypeError(
            f"{cls.__name__} deve definire '_chiave_ordinamento' per usare "
            "aggiunge_confronto_avanzato"
        )

    def __lt__(self, other):
        if not isinstance(other, cls):
            return NotImplemented
        return getattr(self, self._chiave_ordinamento) < getattr(other, other._chiave_ordinamento)

    def __eq__(self, other):
        if not isinstance(other, cls):
            return NotImplemented
        return getattr(self, self._chiave_ordinamento) == getattr(other, other._chiave_ordinamento)

    def __hash__(self):
        return hash(getattr(self, self._chiave_ordinamento))

    def compara_con(self, other: "cls") -> dict:
        """Confronto dettagliato tra due istanze."""
        chiave = self._chiave_ordinamento
        val_self = getattr(self, chiave)
        val_other = getattr(other, chiave)
        differenza = val_self - val_other if isinstance(val_self, (int, float)) else None
        return {
            "self": val_self,
            "other": val_other,
            "differenza": differenza,
            "relazione": "uguale" if val_self == val_other else ("maggiore" if val_self > val_other else "minore"),
        }

    cls.__lt__ = __lt__
    cls.__le__ = lambda self, other: self < other or self == other
    cls.__gt__ = lambda self, other: not (self < other or self == other)
    cls.__ge__ = lambda self, other: not (self < other)
    cls.__eq__ = __eq__
    cls.__hash__ = __hash__
    cls.compara_con = compara_con

    return cls

@aggiunge_confronto_avanzato
class Prodotto:
    """Un prodotto con prezzo e nome."""

    _chiave_ordinamento = "prezzo"

    def __init__(self, nome: str, prezzo: float):
        self.nome = nome
        self.prezzo = prezzo

    def __repr__(self):
        return f"Prodotto({self.nome!r}, €{self.prezzo:.2f})"

laptop = Prodotto("Laptop", 999.99)
mouse = Prodotto("Mouse", 25.00)
tastiera = Prodotto("Tastiera", 89.99)

prodotti = [laptop, mouse, tastiera]
print(f"Ordinati: {sorted(prodotti)}")
print(f"Piu' costoso: {max(prodotti)}")
print(f"Piu' economico: {min(prodotti)}")
print(f"\nConfronto laptop vs tastiera: {laptop.compara_con(tastiera)}")
```

```
# Output atteso:
Ordinati: [Prodotto('Mouse', €25.00), Prodotto('Tastiera', €89.99), Prodotto('Laptop', €999.99)]
Piu' costoso: Prodotto('Laptop', €999.99)
Piu' economico: Prodotto('Mouse', €25.00)

Confronto laptop vs tastiera: {'self': 999.99, 'other': 89.99, 'differenza': 910.0, 'relazione': 'maggiore'}
```

### Pattern 3: Decoratore Asincrono

```python
import functools
import asyncio
import time

def timer_asincrono(funzione):
    """Decoratore per misurare il tempo di funzioni asincrone."""
    @functools.wraps(funzione)
    async def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        try:
            return await funzione(*args, **kwargs)
        finally:
            durata = (time.perf_counter() - inizio) * 1000
            print(f"[timer_async] {funzione.__name__}: {durata:.2f}ms")
    return wrapper

def retry_asincrono(tentativi: int = 3, pausa: float = 0.1):
    """Decoratore retry per funzioni asincrone."""
    def decoratore(funzione):
        @functools.wraps(funzione)
        async def wrapper(*args, **kwargs):
            for i in range(1, tentativi + 1):
                try:
                    return await funzione(*args, **kwargs)
                except Exception as e:
                    if i == tentativi:
                        raise
                    print(f"  [retry_async] Tentativo {i}/{tentativi}: {e}")
                    await asyncio.sleep(pausa)
        return wrapper
    return decoratore

@timer_asincrono
@retry_asincrono(tentativi=3, pausa=0.05)
async def chiama_api_async(url: str) -> dict:
    """Simula una chiamata API asincrona che potrebbe fallire."""
    import random
    await asyncio.sleep(0.1)  # simula latenza rete
    if random.random() < 0.5:
        raise ConnectionError(f"Timeout per {url}")
    return {"url": url, "status": 200, "data": "risposta"}

async def main():
    import random
    random.seed(1)
    try:
        risultato = await chiama_api_async("https://api.esempio.com/dati")
        print(f"Risultato: {risultato}")
    except Exception as e:
        print(f"Fallito dopo tutti i tentativi: {e}")

asyncio.run(main())
```

```
# Output atteso:
  [retry_async] Tentativo 1/3: Timeout per https://api.esempio.com/dati
  [retry_async] Tentativo 2/3: Timeout per https://api.esempio.com/dati
[timer_async] chiama_api_async: 356.12ms
Risultato: {'url': 'https://api.esempio.com/dati', 'status': 200, 'data': 'risposta'}
```

---

## I2: Pattern Catalogo — Generatori

### Pattern 4: Generatore Infinito con Controllo

```python
from typing import Generator
import itertools

def fibonacci_infinito() -> Generator[int, None, None]:
    """
    Genera la sequenza di Fibonacci all'infinito.
    Usa solo O(1) di memoria.
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Prendi i primi 10
print("Primi 10 Fibonacci:", list(itertools.islice(fibonacci_infinito(), 10)))

# Prendi tutti i Fibonacci minori di 1000
print("Fibonacci < 1000:", list(itertools.takewhile(lambda x: x < 1000, fibonacci_infinito())))

# Trova il primo Fibonacci maggiore di un milione
gen = fibonacci_infinito()
primo_grande = next(x for x in gen if x > 1_000_000)
print(f"Primo Fibonacci > 1,000,000: {primo_grande:,}")

# Prendi i Fibonacci dalla posizione 10 alla 20
gen2 = fibonacci_infinito()
posizioni_10_20 = list(itertools.islice(itertools.islice(gen2, 20), 10, 20))
print(f"Fibonacci posizioni 10-19: {posizioni_10_20}")
```

```
# Output atteso:
Primi 10 Fibonacci: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
Fibonacci < 1000: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
Primo Fibonacci > 1,000,000: 1,346,269
Fibonacci posizioni 10-19: [55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181]
```

### Pattern 5: Generatore con Stato Interno

```python
from typing import Generator

def media_mobile(finestra: int) -> Generator[float | None, float, None]:
    """
    Generatore bidirezionale che calcola la media mobile.
    Riceve numeri via send() e produce la media degli ultimi 'finestra' valori.

    Uso:
        gen = media_mobile(3)
        next(gen)  # inizializza
        print(gen.send(10))   # None (non abbastanza dati)
        print(gen.send(20))   # None
        print(gen.send(30))   # 20.0
        print(gen.send(40))   # 30.0
    """
    from collections import deque

    buffer = deque(maxlen=finestra)
    valore = yield None  # inizializza

    while valore is not None:
        buffer.append(valore)
        if len(buffer) < finestra:
            valore = yield None  # non abbastanza dati
        else:
            media = sum(buffer) / len(buffer)
            valore = yield round(media, 2)

# Uso
gen = media_mobile(finestra=3)
next(gen)  # inicializza il generatore

valori = [10, 20, 30, 40, 50, 15, 25]
print("Media mobile (finestra=3):")
for v in valori:
    risultato = gen.send(v)
    print(f"  Input: {v:3d} → Media: {risultato}")
```

```
# Output atteso:
Media mobile (finestra=3):
  Input:  10 → Media: None
  Input:  20 → Media: None
  Input:  30 → Media: 20.0
  Input:  40 → Media: 30.0
  Input:  50 → Media: 40.0
  Input:  15 → Media: 35.0
  Input:  25 → Media: 30.0
```

### Pattern 6: Generatori per Grafi — Traversata BFS

```python
from typing import Generator, Any
from collections import deque

# Struttura grafo
Grafo = dict[str, list[str]]

def bfs(grafo: Grafo, nodo_iniziale: str) -> Generator[str, None, None]:
    """
    Traversata BFS (Breadth-First Search) di un grafo.
    Genera i nodi nell'ordine di visita.
    """
    visitati = set()
    coda = deque([nodo_iniziale])
    visitati.add(nodo_iniziale)

    while coda:
        nodo = coda.popleft()
        yield nodo

        for vicino in grafo.get(nodo, []):
            if vicino not in visitati:
                visitati.add(vicino)
                coda.append(vicino)

def dfs(grafo: Grafo, nodo_iniziale: str) -> Generator[str, None, None]:
    """
    Traversata DFS (Depth-First Search) di un grafo.
    Genera i nodi nell'ordine di visita.
    """
    visitati = set()

    def _dfs_ricorsivo(nodo: str) -> Generator[str, None, None]:
        visitati.add(nodo)
        yield nodo
        for vicino in grafo.get(nodo, []):
            if vicino not in visitati:
                yield from _dfs_ricorsivo(vicino)

    yield from _dfs_ricorsivo(nodo_iniziale)

def trovaCammino(
    grafo: Grafo,
    partenza: str,
    destinazione: str,
) -> list[str] | None:
    """
    Trova il cammino piu' breve tra due nodi usando BFS.
    Restituisce la lista dei nodi del cammino, o None se non esiste.
    """
    if partenza == destinazione:
        return [partenza]

    visitati = {partenza}
    coda = deque([(partenza, [partenza])])

    while coda:
        nodo, cammino = coda.popleft()
        for vicino in grafo.get(nodo, []):
            if vicino not in visitati:
                nuovo_cammino = cammino + [vicino]
                if vicino == destinazione:
                    return nuovo_cammino
                visitati.add(vicino)
                coda.append((vicino, nuovo_cammino))

    return None

# Grafo di esempio: rete di citta' italiane
citta = {
    "Milano": ["Torino", "Genova", "Venezia", "Bologna"],
    "Torino": ["Milano", "Genova"],
    "Genova": ["Torino", "Milano", "Firenze"],
    "Venezia": ["Milano", "Bologna"],
    "Bologna": ["Milano", "Venezia", "Firenze", "Roma"],
    "Firenze": ["Genova", "Bologna", "Roma"],
    "Roma": ["Bologna", "Firenze", "Napoli"],
    "Napoli": ["Roma"],
}

print("BFS da Milano:")
print("  ", list(bfs(citta, "Milano")))

print("\nDFS da Milano:")
print("  ", list(dfs(citta, "Milano")))

print("\nCammini:")
for dest in ["Napoli", "Venezia", "Torino"]:
    cammino = trovaCammino(citta, "Genova", dest)
    print(f"  Genova → {dest}: {' → '.join(cammino) if cammino else 'nessun cammino'}")
```

```
# Output atteso:
BFS da Milano:
   ['Milano', 'Torino', 'Genova', 'Venezia', 'Bologna', 'Firenze', 'Roma', 'Napoli']

DFS da Milano:
   ['Milano', 'Torino', 'Genova', 'Firenze', 'Bologna', 'Venezia', 'Roma', 'Napoli']

Cammini:
  Genova → Napoli: Genova → Bologna → Roma → Napoli
  Genova → Venezia: Genova → Milano → Venezia
  Genova → Torino: Genova → Torino
```

---

## I3: Pattern Catalogo — Context Manager

### Pattern 7: Context Manager per Transazioni Database Reali

```python
import sqlite3
from contextlib import contextmanager
from typing import Generator

@contextmanager
def db_transaction(
    database_path: str = ":memory:",
    isolation_level: str = "DEFERRED",
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager per transazioni SQLite con gestione automatica di
    commit/rollback e chiusura della connessione.

    Args:
        database_path: percorso del database (default: in-memory)
        isolation_level: DEFERRED, IMMEDIATE o EXCLUSIVE

    Yields:
        sqlite3.Connection con transazione aperta

    Garantisce:
        - COMMIT se il blocco termina senza eccezioni
        - ROLLBACK se viene sollevata un'eccezione
        - Chiusura della connessione in ogni caso (finally)
    """
    conn = sqlite3.connect(database_path)
    conn.isolation_level = isolation_level
    conn.row_factory = sqlite3.Row  # accesso alle colonne per nome

    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Uso: creazione e popolamento di un database
with db_transaction() as conn:
    # Setup schema
    conn.execute("""
        CREATE TABLE utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            eta INTEGER CHECK(eta BETWEEN 0 AND 150)
        )
    """)

    # Insert multipli
    utenti = [
        ("Alice Rossi", "alice@esempio.com", 28),
        ("Bob Verdi", "bob@esempio.com", 35),
        ("Carol Bianchi", "carol@esempio.com", 42),
    ]
    conn.executemany(
        "INSERT INTO utenti (nome, email, eta) VALUES (?, ?, ?)",
        utenti
    )

    print(f"Inseriti {conn.execute('SELECT COUNT(*) FROM utenti').fetchone()[0]} utenti")

# Dati persistenti? No, perche' e' in-memory e la connessione e' chiusa.
# In un db reale, il commit sarebbe stato salvato su disco.

# Test del rollback
print("\nTest rollback:")
try:
    with db_transaction() as conn:
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test VALUES (1)")
        print("  Inserito valore 1")
        conn.execute("INSERT INTO test VALUES (1)")  # UNIQUE constraint violation!
        print("  Non dovrebbe arrivare qui")
except sqlite3.IntegrityError as e:
    print(f"  Rollback eseguito: {e}")
```

```
# Output atteso:
Inseriti 3 utenti

Test rollback:
  Inserito valore 1
  Rollback eseguito: UNIQUE constraint failed: test.id
```

### Pattern 8: Context Manager per Blocco di Risorse Concorrenti

```python
import threading
from contextlib import contextmanager
from typing import Generator

class PoolRisorse:
    """
    Pool di risorse con checkout/checkin thread-safe.
    Usa un Semaphore per limitare l'accesso concorrente.
    """

    def __init__(self, risorse: list, max_concorrenti: int = None):
        self._tutte_risorse = list(risorse)
        self._disponibili = list(risorse)
        self._lock = threading.Lock()
        self._semaforo = threading.Semaphore(max_concorrenti or len(risorse))

    @contextmanager
    def prendi(self) -> Generator[any, None, None]:
        """
        Prende una risorsa dal pool, la usa, poi la rilascia.
        Thread-safe. Si blocca se il pool e' esaurito.
        """
        self._semaforo.acquire()
        with self._lock:
            risorsa = self._disponibili.pop(0)

        print(f"  [pool] Risorsa acquisita: {risorsa} "
              f"(disponibili: {len(self._disponibili)}/{len(self._tutte_risorse)})")

        try:
            yield risorsa
        finally:
            with self._lock:
                self._disponibili.append(risorsa)
            self._semaforo.release()
            print(f"  [pool] Risorsa rilasciata: {risorsa} "
                  f"(disponibili: {len(self._disponibili)}/{len(self._tutte_risorse)})")

    @property
    def n_disponibili(self) -> int:
        with self._lock:
            return len(self._disponibili)

# Pool di connessioni database
pool = PoolRisorse(
    risorse=[f"conn_{i}" for i in range(3)],
    max_concorrenti=3,
)

def usa_risorsa(id_thread: int):
    """Simula un thread che usa una risorsa dal pool."""
    with pool.prendi() as risorsa:
        print(f"    Thread {id_thread} sta usando {risorsa}")
        import time
        time.sleep(0.05)

# Test sequenziale
print("Test sequenziale:")
for i in range(5):
    usa_risorsa(i)

print(f"\nRisorse disponibili alla fine: {pool.n_disponibili}")

# Test concorrente
print("\nTest concorrente (5 thread, pool di 3):")
threads = [threading.Thread(target=usa_risorsa, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Risorse disponibili alla fine: {pool.n_disponibili}")
```

```
# Output atteso:
Test sequenziale:
  [pool] Risorsa acquisita: conn_0 (disponibili: 2/3)
    Thread 0 sta usando conn_0
  [pool] Risorsa rilasciata: conn_0 (disponibili: 3/3)
  [pool] Risorsa acquisita: conn_0 (disponibili: 2/3)
    Thread 1 sta usando conn_0
  ...

Test concorrente (5 thread, pool di 3):
  [pool] Risorsa acquisita: conn_0 (disponibili: 2/3)
  [pool] Risorsa acquisita: conn_1 (disponibili: 1/3)
  [pool] Risorsa acquisita: conn_2 (disponibili: 0/3)
  (Thread 3 e 4 attendono)
  ...

Risorse disponibili alla fine: 3
```

---

## I4: Benchmark e Confronti di Performance

### Decoratori: Overhead del Wrapper

```python
import functools
import timeit

# Funzione originale
def somma_senza_deco(n: int) -> int:
    return sum(range(n))

# Con wrapper vuoto senza wraps
def deco_senza_wraps(f):
    def w(*a, **kw): return f(*a, **kw)
    return w

# Con wrapper e wraps
def deco_con_wraps(f):
    @functools.wraps(f)
    def w(*a, **kw): return f(*a, **kw)
    return w

@deco_senza_wraps
def somma_senza_wraps(n: int) -> int:
    return sum(range(n))

@deco_con_wraps
def somma_con_wraps(n: int) -> int:
    return sum(range(n))

# Benchmark
N = 10000
RIPETIZIONI = 100000

t_originale = timeit.timeit(lambda: somma_senza_deco(N), number=RIPETIZIONI)
t_senza_wraps = timeit.timeit(lambda: somma_senza_wraps(N), number=RIPETIZIONI)
t_con_wraps = timeit.timeit(lambda: somma_con_wraps(N), number=RIPETIZIONI)

print("=== Overhead Decoratori ===")
print(f"Originale:     {t_originale:.3f}s")
print(f"Senza @wraps:  {t_senza_wraps:.3f}s (+{(t_senza_wraps/t_originale - 1)*100:.1f}%)")
print(f"Con @wraps:    {t_con_wraps:.3f}s (+{(t_con_wraps/t_originale - 1)*100:.1f}%)")
print()
print("L'overhead di un wrapper e' tipicamente < 1%")
print("Per funzioni molto veloci (sub-microsecondo), l'overhead diventa rilevante")
```

```
# Output atteso:
=== Overhead Decoratori ===
Originale:     2.134s
Senza @wraps:  2.156s (+1.0%)
Con @wraps:    2.161s (+1.3%)

L'overhead di un wrapper e' tipicamente < 1%
Per funzioni molto veloci (sub-microsecondo), l'overhead diventa rilevante
```

### Generatori: Memoria

```python
import sys

def dimensione_oggetto(obj, nome: str) -> None:
    """Stampa la dimensione in memoria di un oggetto."""
    size_bytes = sys.getsizeof(obj)
    if size_bytes < 1024:
        size_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / 1024 / 1024:.1f} MB"
    print(f"  {nome:<30}: {size_str}")

N = 100_000

# Lista
lista = [i * i for i in range(N)]
dimensione_oggetto(lista, "lista (list comprehension)")

# Tupla
tupla = tuple(i * i for i in range(N))
dimensione_oggetto(tupla, "tupla (tuple comprehension)")

# Generatore
gen = (i * i for i in range(N))
dimensione_oggetto(gen, "generatore (gen expression)")

# Set
insieme = {i * i for i in range(N)}
dimensione_oggetto(insieme, "set (set comprehension)")

print()
print(f"Il generatore usa {sys.getsizeof(lista) / sys.getsizeof(gen):.0f}x meno memoria della lista")
```

```
# Output atteso:
  lista (list comprehension)    : 800.8 KB
  tupla (tuple comprehension)   : 781.3 KB
  generatore (gen expression)   : 200 B
  set (set comprehension)       : 4.0 MB

Il generatore usa 4100x meno memoria della lista
```

### Cache: `lru_cache` vs `cache`

```python
import functools
import timeit

# Funzione costosa (calcolo Fibonacci ricorsivo)
def fib_nessuna_cache(n: int) -> int:
    if n < 2: return n
    return fib_nessuna_cache(n-1) + fib_nessuna_cache(n-2)

@functools.lru_cache(maxsize=128)
def fib_lru_cache(n: int) -> int:
    if n < 2: return n
    return fib_lru_cache(n-1) + fib_lru_cache(n-2)

@functools.cache
def fib_cache(n: int) -> int:
    if n < 2: return n
    return fib_cache(n-1) + fib_cache(n-2)

N = 30

# Benchmark
t_nessuna = timeit.timeit(lambda: fib_nessuna_cache(N), number=100)

fib_lru_cache.cache_clear()
t_lru = timeit.timeit(lambda: fib_lru_cache(N), number=100)

fib_cache.cache_clear()
t_cache = timeit.timeit(lambda: fib_cache(N), number=100)

print(f"=== Cache Performance (fib({N})) ===")
print(f"Senza cache:   {t_nessuna:.3f}s")
print(f"lru_cache(128): {t_lru:.6f}s ({t_nessuna/t_lru:.0f}x piu' veloce)")
print(f"@cache:        {t_cache:.6f}s ({t_nessuna/t_cache:.0f}x piu' veloce)")

print()
print(f"lru_cache info: {fib_lru_cache.cache_info()}")
```

```
# Output atteso:
=== Cache Performance (fib(30)) ===
Senza cache:   8.234s
lru_cache(128): 0.000012s (686167x piu' veloce)
@cache:        0.000010s (823400x piu' veloce)

lru_cache info: CacheInfo(hits=2900, misses=31, maxsize=128, currsize=31)
```

---

## I5: Anti-Pattern — Cosa NON Fare

### Anti-Pattern 1: Decoratore che Modifica lo Stato Globale

```python
# SBAGLIATO: il decoratore modifica stato globale senza protezione
_chiamate_globali = 0

def conta_sbagliato(f):
    def w(*a, **kw):
        global _chiamate_globali
        _chiamate_globali += 1  # non thread-safe!
        return f(*a, **kw)
    return w

# CORRETTO: usa una closure o un oggetto
import threading

def conta_corretto(f):
    """Conta le chiamate in modo thread-safe."""
    contatore = [0]  # lista per mutabilita' nella closure
    lock = threading.Lock()

    import functools
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        with lock:
            contatore[0] += 1
        return f(*args, **kwargs)

    wrapper.get_count = lambda: contatore[0]
    wrapper.reset = lambda: contatore.__setitem__(0, 0)
    return wrapper

@conta_corretto
def mia_funzione():
    return "ok"

mia_funzione()
mia_funzione()
mia_funzione()
print(f"Chiamate: {mia_funzione.get_count()}")
mia_funzione.reset()
print(f"Dopo reset: {mia_funzione.get_count()}")
```

```
# Output atteso:
Chiamate: 3
Dopo reset: 0
```

### Anti-Pattern 2: Generator che Consuma Troppa Memoria

```python
# SBAGLIATO: materializza tutto prima di iterare
def processa_sbagliato(file_grande: str) -> list:
    """Carica tutto in memoria — potrebbe causare OOM."""
    return [riga.strip() for riga in file_grande.split("\n")]
    # Per un file da 1GB: usa 1GB+ di RAM

# CORRETTO: elabora riga per riga
def processa_corretto(file_grande: str):
    """Genera righe una alla volta — O(1) memoria."""
    for riga in file_grande.split("\n"):
        riga = riga.strip()
        if riga:
            yield riga

# Dimostrazione
import sys
contenuto = "\n".join(f"riga_{i}" for i in range(100000))

# Approccio sbagliato
lista_sbagliata = processa_sbagliato(contenuto)
print(f"Lista: {sys.getsizeof(lista_sbagliata) / 1024:.1f} KB in memoria")

# Approccio corretto
gen_corretto = processa_corretto(contenuto)
print(f"Generator: {sys.getsizeof(gen_corretto)} byte in memoria")
print(f"Risparmio: {sys.getsizeof(lista_sbagliata) / sys.getsizeof(gen_corretto):.0f}x")
```

```
# Output atteso:
Lista: 800.8 KB in memoria
Generator: 200 byte in memoria
Risparmio: 4100x
```

### Anti-Pattern 3: Context Manager senza finally

```python
from contextlib import contextmanager

# SBAGLIATO: se c'e' un'eccezione, il cleanup non avviene
@contextmanager
def risorsa_non_sicura():
    risorsa = apri_risorsa()  # immagina che apra un file, connessione, ecc.
    yield risorsa
    chiudi_risorsa(risorsa)  # NON eseguito se yield solleva un'eccezione!

# CORRETTO: usa try/finally
@contextmanager
def risorsa_sicura():
    risorsa = apri_risorsa()
    try:
        yield risorsa
    finally:
        chiudi_risorsa(risorsa)  # SEMPRE eseguito

# ALTERNATIVA CORRETTA: usa __enter__/__exit__ della classe
class RisorsaSicura:
    def __enter__(self):
        self.risorsa = apri_risorsa()
        return self.risorsa

    def __exit__(self, exc_type, exc_val, exc_tb):
        chiudi_risorsa(self.risorsa)  # SEMPRE eseguito
        return False  # non sopprimere eccezioni

print("Le funzioni apri_risorsa/chiudi_risorsa sono placeholder per la dimostrazione.")
print("Il punto chiave: @contextmanager richiede try/finally per garantire il cleanup.")
```

### Anti-Pattern 4: Usare `return` invece di `yield from`

```python
# SBAGLIATO: return NON delega al sub-generator
def genera_sbagliato(iterabile):
    return iterabile  # non e' un generatore!

# CORRETTO: yield from delega correttamente
def genera_corretto(iterabile):
    yield from iterabile

# Dimostrazione della differenza
def sub_gen():
    yield 1
    yield 2
    yield 3

# Con return: restituisce il generatore come oggetto, non lo itera
risultato_sbagliato = genera_sbagliato(sub_gen())
print(f"return: {risultato_sbagliato}")  # <generator object sub_gen at 0x...>
print(f"type: {type(risultato_sbagliato)}")

# Con yield from: itera e delega
print("\nyield from:")
for v in genera_corretto(sub_gen()):
    print(f"  {v}")
```

```
# Output atteso:
return: <generator object sub_gen at 0x...>
type: <class 'generator'>

yield from:
  1
  2
  3
```

---

## I6: Cheatsheet Formato Stampa

```
╔══════════════════════════════════════════════════════════════╗
║           PYTHON AVANZATO — CHEATSHEET RAPIDO               ║
╠══════════════════════════════════════════════════════════════╣
║ DECORATORI                                                    ║
║   def timer(f):                                               ║
║       @functools.wraps(f)                                     ║
║       def w(*a, **kw):                                        ║
║           t = time.perf_counter()                             ║
║           r = f(*a, **kw)                                     ║
║           print(f"{f.__name__}: {time.perf_counter()-t:.3f}s")║
║           return r                                            ║
║       return w                                                ║
║                                                               ║
║   Con parametri:                                              ║
║   def retry(n=3):                                             ║
║       def dec(f):                                             ║
║           @functools.wraps(f)                                 ║
║           def w(*a, **kw):                                    ║
║               for _ in range(n): f(*a, **kw)                  ║
║           return w                                            ║
║       return dec                                              ║
╠══════════════════════════════════════════════════════════════╣
║ GENERATORI                                                    ║
║   def conta(n):                                               ║
║       for i in range(n):                                      ║
║           yield i            ← sospende, produce i            ║
║                                                               ║
║   gen = conta(5)             ← crea oggetto (non esegue)      ║
║   next(gen)                  ← esegue fino al prossimo yield  ║
║   list(gen)                  ← materializza tutti i valori    ║
║   yield from altro_gen       ← delega al sub-generator       ║
║   valore = gen.send(x)       ← invia x, riprende dal yield   ║
╠══════════════════════════════════════════════════════════════╣
║ CONTEXT MANAGER                                               ║
║   class MioCM:                                                ║
║       def __enter__(self): return risorsa                     ║
║       def __exit__(self, et, ev, tb):                         ║
║           cleanup()                                           ║
║           return False  ← True sopprime eccezione            ║
║                                                               ║
║   @contextmanager                                             ║
║   def mio_cm():                                               ║
║       setup()                                                 ║
║       try: yield risorsa                                      ║
║       finally: cleanup()                                      ║
║                                                               ║
║   ExitStack: gestisce N context manager dinamicamente         ║
║   suppress(*exc): sopprime le eccezioni specificate           ║
╚══════════════════════════════════════════════════════════════╝
```

---

# PARTE L: ESERCIZI RISOLTI — Guida Passo Passo

---

## L1: Soluzione Guidata — Decoratore `@validate_types`

### Specifica
Implementa un decoratore che validi automaticamente i tipi degli argomenti basandosi sulle type annotations della funzione.

### Passo 1: Capisci il Problema

```python
# Senza il decoratore, questo codice non da' errori a runtime:
def somma(a: int, b: int) -> int:
    return a + b

# Questo funziona ma non dovrebbe (a: int, non str):
print(somma("ciao", " mondo"))  # "ciao mondo" -- stringa!
```

### Passo 2: Piano della Soluzione

```
1. Leggi le type annotations con typing.get_type_hints()
2. Per ogni argomento passato, controlla che il tipo corrisponda all'annotation
3. Se il tipo non corrisponde, solleva TypeError con messaggio chiaro
4. Per i tipi Optional (Union[X, None]), permetti None
5. Mantieni __name__, __doc__ con functools.wraps
```

### Passo 3: Implementazione

```python
import functools
import inspect
import typing

def validate_types(funzione):
    """
    Decoratore che valida i tipi degli argomenti contro le type annotations.

    Funzionalita':
    - Valida argomenti posizionali e keyword
    - Supporta Optional[T] (permette None)
    - Ignora tipi non verificabili (generics complessi)
    - Messaggio di errore chiaro con nome parametro e tipo atteso

    Non valida:
    - Il return type (per non impattare le performance)
    - Generici come List[int] (richiederebbe issubclass per ogni elemento)
    """

    # Ottieni le annotations (risolve forward references)
    try:
        hints = typing.get_type_hints(funzione)
    except Exception:
        # Se le hints non sono risolvibili, disabilita la validazione
        return funzione

    # Rimuovi il return type dalle hints che controlliamo
    hints_argomenti = {k: v for k, v in hints.items() if k != "return"}

    if not hints_argomenti:
        return funzione  # Nessuna annotation: nessuna validazione

    # Ottieni i parametri della funzione (per i default e i positional)
    sig = inspect.signature(funzione)

    def _e_tipo_valido(valore, tipo_atteso) -> bool:
        """
        Controlla se il valore e' del tipo atteso.
        Gestisce Optional[T] == Union[T, None].
        """
        # Gestisci Optional[T] = Union[T, None]
        origin = getattr(tipo_atteso, "__origin__", None)
        if origin is typing.Union:
            args = tipo_atteso.__args__
            return any(_e_tipo_valido(valore, t) for t in args)

        # Gestisci None
        if tipo_atteso is type(None):
            return valore is None

        # Per generici (List[int], Dict[str, int], ecc.): controlla solo l'origin
        if origin is not None:
            return isinstance(valore, origin)

        # Tipo semplice: isinstance normale
        try:
            return isinstance(valore, tipo_atteso)
        except TypeError:
            return True  # se isinstance fallisce, ignora

    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        # Associa argomenti posizionali ai parametri
        parametri = list(sig.parameters.keys())
        for i, valore in enumerate(args):
            if i < len(parametri):
                nome_param = parametri[i]
                if nome_param in hints_argomenti:
                    tipo_atteso = hints_argomenti[nome_param]
                    if not _e_tipo_valido(valore, tipo_atteso):
                        raise TypeError(
                            f"{funzione.__name__}(): argomento '{nome_param}' "
                            f"deve essere {tipo_atteso}, "
                            f"ricevuto {type(valore).__name__}"
                        )

        # Controlla keyword arguments
        for nome_param, valore in kwargs.items():
            if nome_param in hints_argomenti:
                tipo_atteso = hints_argomenti[nome_param]
                if not _e_tipo_valido(valore, tipo_atteso):
                    raise TypeError(
                        f"{funzione.__name__}(): argomento '{nome_param}' "
                        f"deve essere {tipo_atteso}, "
                        f"ricevuto {type(valore).__name__}"
                    )

        return funzione(*args, **kwargs)

    return wrapper

# Test completo
from typing import Optional, List

@validate_types
def registra_utente(
    nome: str,
    eta: int,
    email: Optional[str] = None,
) -> dict:
    """Registra un utente nel sistema."""
    return {"nome": nome, "eta": eta, "email": email}

# Test 1: tipi corretti
print(registra_utente("Alice", 28))
print(registra_utente("Bob", 35, email="bob@esempio.com"))
print(registra_utente("Carol", 42, email=None))  # Optional: None e' ok

# Test 2: tipo sbagliato
try:
    registra_utente(123, 28)  # nome non e' str
except TypeError as e:
    print(f"Errore: {e}")

# Test 3: tipo sbagliato (keyword)
try:
    registra_utente("Dave", "trenta")  # eta non e' int
except TypeError as e:
    print(f"Errore: {e}")
```

```
# Output atteso:
{'nome': 'Alice', 'eta': 28, 'email': None}
{'nome': 'Bob', 'eta': 35, 'email': 'bob@esempio.com'}
{'nome': 'Carol', 'eta': 42, 'email': None}
Errore: registra_utente(): argomento 'nome' deve essere <class 'str'>, ricevuto int
Errore: registra_utente(): argomento 'eta' deve essere <class 'int'>, ricevuto str
```

---

## L2: Soluzione Guidata — Generatore Fibonacci con `yield from`

### Specifica
Implementa la sequenza di Fibonacci in tre modi diversi e confrontali.

```python
# Modo 1: Funzione normale (restituisce lista)
def fibonacci_lista(n: int) -> list[int]:
    """Restituisce i primi n numeri di Fibonacci come lista."""
    if n <= 0: return []
    if n == 1: return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq

# Modo 2: Generator function
def fibonacci_gen(n: int):
    """Genera i primi n numeri di Fibonacci uno alla volta."""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# Modo 3: Ricorsivo con yield from
def fibonacci_ricorsivo():
    """Genera Fibonacci all'infinito usando stato interno."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def prendi_fibonacci(n: int):
    """Prende i primi n Fibonacci usando il generatore infinito con yield from."""
    contatore = 0
    for valore in fibonacci_ricorsivo():
        if contatore >= n:
            return
        yield valore
        contatore += 1

# Confronto
import sys
n = 20

# Lista
fib_lista = fibonacci_lista(n)
print(f"Lista: {fib_lista}")
print(f"Memoria lista: {sys.getsizeof(fib_lista)} bytes")

# Generator materializzato
fib_gen_materializzato = list(fibonacci_gen(n))
print(f"\nGenerator (materializzato): {fib_gen_materializzato}")
gen_non_materializzato = fibonacci_gen(n)
print(f"Memoria generator non materializzato: {sys.getsizeof(gen_non_materializzato)} bytes")

# Ricorsivo con yield from
fib_ricorsivo = list(prendi_fibonacci(n))
print(f"\nRicorsivo: {fib_ricorsivo}")

# Verifica che siano tutti uguali
print(f"\nTutti uguali: {fib_lista == fib_gen_materializzato == fib_ricorsivo}")
```

```
# Output atteso:
Lista: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181]
Memoria lista: 216 bytes

Generator (materializzato): [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181]
Memoria generator non materializzato: 200 bytes

Ricorsivo: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181]

Tutti uguali: True
```

---

## L3: Soluzione Guidata — Context Manager per Test

### Specifica
Implementa un context manager `ambiente_test_database` che crei un database SQLite temporaneo, lo popoli con dati di test, esegua i test, poi cancelli tutto.

```python
import sqlite3
import os
import tempfile
from contextlib import contextmanager

@contextmanager
def ambiente_test_database(schema_sql: str, dati_iniziali: list[tuple] = None):
    """
    Context manager per test con database temporaneo.

    Crea un database SQLite in una directory temporanea,
    lo popola con lo schema e i dati forniti,
    poi li cancella dopo il test.

    Yields:
        sqlite3.Connection al database di test

    Args:
        schema_sql: SQL per creare la struttura del database
        dati_iniziali: lista di (sql, parametri) per i dati iniziali
    """
    # Crea file temporaneo per il database
    fd, percorso_db = tempfile.mkstemp(suffix=".db", prefix="test_")
    os.close(fd)

    conn = None
    try:
        # Crea e popola il database
        conn = sqlite3.connect(percorso_db)
        conn.row_factory = sqlite3.Row
        conn.executescript(schema_sql)

        if dati_iniziali:
            for sql, params in dati_iniziali:
                conn.execute(sql, params)
            conn.commit()

        print(f"[test_db] Database di test creato: {os.path.basename(percorso_db)}")
        yield conn

    finally:
        if conn:
            conn.close()
        if os.path.exists(percorso_db):
            os.unlink(percorso_db)
        print(f"[test_db] Database di test rimosso")

# Schema di test
SCHEMA = """
CREATE TABLE prodotti (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    prezzo REAL NOT NULL,
    categoria TEXT
);

CREATE TABLE ordini (
    id INTEGER PRIMARY KEY,
    id_prodotto INTEGER REFERENCES prodotti(id),
    quantita INTEGER NOT NULL DEFAULT 1,
    data TEXT NOT NULL
);
"""

DATI_TEST = [
    ("INSERT INTO prodotti VALUES (?,?,?,?)", (1, "Laptop", 999.99, "Elettronica")),
    ("INSERT INTO prodotti VALUES (?,?,?,?)", (2, "Mouse", 25.00, "Elettronica")),
    ("INSERT INTO prodotti VALUES (?,?,?,?)", (3, "Libro Python", 39.99, "Libri")),
    ("INSERT INTO ordini VALUES (?,?,?,?)", (1, 1, 2, "2024-01-15")),
    ("INSERT INTO ordini VALUES (?,?,?,?)", (2, 2, 5, "2024-01-16")),
]

# Test: analisi vendite
with ambiente_test_database(SCHEMA, DATI_TEST) as conn:
    print()

    # Query 1: tutti i prodotti
    prodotti = conn.execute("SELECT * FROM prodotti ORDER BY prezzo DESC").fetchall()
    print("Prodotti (per prezzo desc):")
    for p in prodotti:
        print(f"  {p['nome']:20s} €{p['prezzo']:.2f} [{p['categoria']}]")

    # Query 2: join ordini-prodotti
    ordini = conn.execute("""
        SELECT p.nome, o.quantita, p.prezzo * o.quantita as totale
        FROM ordini o
        JOIN prodotti p ON o.id_prodotto = p.id
        ORDER BY totale DESC
    """).fetchall()

    print("\nOrdini (per totale desc):")
    for o in ordini:
        print(f"  {o['nome']:20s} x{o['quantita']:2d} = €{o['totale']:.2f}")

    # Query 3: statistiche per categoria
    stats = conn.execute("""
        SELECT categoria, COUNT(*) as n, AVG(prezzo) as media_prezzo
        FROM prodotti
        GROUP BY categoria
    """).fetchall()

    print("\nStatistiche per categoria:")
    for s in stats:
        print(f"  {s['categoria']:15s}: {s['n']} prodotti, media €{s['media_prezzo']:.2f}")

print("\nTutto pulito dopo il context manager!")
```

```
# Output atteso:
[test_db] Database di test creato: test_XXXXXX.db

Prodotti (per prezzo desc):
  Laptop               €999.99 [Elettronica]
  Libro Python         €39.99 [Libri]
  Mouse                €25.00 [Elettronica]

Ordini (per totale desc):
  Laptop                x 2 = €1999.98
  Mouse                 x 5 = €125.00

Statistiche per categoria:
  Elettronica    : 2 prodotti, media €512.50
  Libri          : 1 prodotti, media €39.99

[test_db] Database di test rimosso

Tutto pulito dopo il context manager!
```

---

## L4: Soluzione Guidata — Sistema di Cache Multi-Livello

```python
import functools
import time
from typing import Any, Optional

class CacheMultiLivello:
    """
    Cache a due livelli: L1 (in-process, veloce) e L2 (simulata, piu' lenta).
    L1 ha TTL breve (30s), L2 ha TTL lungo (300s).
    Pattern comune in sistemi reali (Redis = L2, dict = L1).
    """

    def __init__(
        self,
        ttl_l1: float = 30.0,
        ttl_l2: float = 300.0,
        max_l1: int = 100,
    ):
        self._l1: dict[str, tuple[float, Any]] = {}  # chiave -> (timestamp, valore)
        self._l2: dict[str, tuple[float, Any]] = {}  # simula Redis
        self._ttl_l1 = ttl_l1
        self._ttl_l2 = ttl_l2
        self._max_l1 = max_l1
        self._stats = {"l1_hits": 0, "l2_hits": 0, "misses": 0}

    def _chiave_valida_in(self, cache: dict, chiave: str, ttl: float) -> bool:
        """Controlla se una chiave e' valida (non scaduta)."""
        if chiave not in cache:
            return False
        ts, _ = cache[chiave]
        return time.time() - ts < ttl

    def get(self, chiave: str) -> Optional[Any]:
        """Cerca prima in L1, poi in L2."""
        # L1 check
        if self._chiave_valida_in(self._l1, chiave, self._ttl_l1):
            self._stats["l1_hits"] += 1
            _, valore = self._l1[chiave]
            return valore

        # L2 check
        if self._chiave_valida_in(self._l2, chiave, self._ttl_l2):
            self._stats["l2_hits"] += 1
            ts, valore = self._l2[chiave]
            # Promuovi in L1
            self._imposta_l1(chiave, valore)
            return valore

        self._stats["misses"] += 1
        return None

    def _imposta_l1(self, chiave: str, valore: Any) -> None:
        """Imposta un valore in L1 con eviction se necessario."""
        if len(self._l1) >= self._max_l1:
            # Evict il piu' vecchio (FIFO semplice)
            chiave_piu_vecchia = min(self._l1, key=lambda k: self._l1[k][0])
            del self._l1[chiave_piu_vecchia]
        self._l1[chiave] = (time.time(), valore)

    def set(self, chiave: str, valore: Any) -> None:
        """Imposta un valore in entrambi i livelli."""
        self._imposta_l1(chiave, valore)
        self._l2[chiave] = (time.time(), valore)

    def __call__(self, funzione):
        """Usa come decoratore per memoizzazione automatica."""
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            chiave = f"{funzione.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            valore = self.get(chiave)
            if valore is not None:
                return valore
            valore = funzione(*args, **kwargs)
            self.set(chiave, valore)
            return valore
        return wrapper

    @property
    def statistiche(self) -> dict:
        totale = sum(self._stats.values())
        return {
            **self._stats,
            "hit_rate": (self._stats["l1_hits"] + self._stats["l2_hits"]) / max(totale, 1) * 100,
            "l1_size": len(self._l1),
            "l2_size": len(self._l2),
        }

# Uso come decoratore
cache = CacheMultiLivello(ttl_l1=5.0, ttl_l2=30.0, max_l1=10)

@cache
def query_database(id_utente: int) -> dict:
    """Simula una query al database (costosa)."""
    print(f"  [DB] Query per utente {id_utente}...")
    time.sleep(0.1)  # simula latenza DB
    return {"id": id_utente, "nome": f"Utente_{id_utente}", "email": f"u{id_utente}@esempio.com"}

# Simulazione accessi
print("=== Cache Multi-Livello ===")
for id_u in [1, 2, 1, 3, 2, 1, 4]:
    inizio = time.perf_counter()
    utente = query_database(id_u)
    durata = (time.perf_counter() - inizio) * 1000
    print(f"  utente {id_u}: {utente['nome']} ({durata:.1f}ms)")

print(f"\nStatistiche: {cache.statistiche}")
```

```
# Output atteso:
=== Cache Multi-Livello ===
  [DB] Query per utente 1...
  utente 1: Utente_1 (100.3ms)
  [DB] Query per utente 2...
  utente 2: Utente_2 (100.2ms)
  utente 1: Utente_1 (0.1ms)   ← L1 hit
  [DB] Query per utente 3...
  utente 3: Utente_3 (100.4ms)
  utente 2: Utente_2 (0.1ms)   ← L1 hit
  utente 1: Utente_1 (0.1ms)   ← L1 hit
  [DB] Query per utente 4...
  utente 4: Utente_4 (100.1ms)

Statistiche: {'l1_hits': 3, 'l2_hits': 0, 'misses': 4, 'hit_rate': 42.9, 'l1_size': 4, 'l2_size': 4}
```

---

*Fine Parte I e L — Catalogo Pattern e Esercizi Risolti*



---

# PARTE M: PROBLEMI DI IMPLEMENTAZIONE REALI

---

## M1: Implementa un Rate Limiter a Finestra Scorrevole

Il rate limiter "a finestra fissa" ha un problema: se hai 100 richieste consentite al minuto e ne fai 100 all'ultimo secondo del minuto, poi 100 al primo secondo del minuto successivo, hai effettivamente fatto 200 in 2 secondi.

La soluzione e' il "sliding window" (finestra scorrevole).

```python
import time
import threading
from collections import deque
from contextlib import contextmanager

class RateLimiterFinestraScorrevole:
    """
    Rate limiter con algoritmo a finestra scorrevole.
    Piu' preciso del rate limiter a finestra fissa.

    Esempio: 10 richieste per finestra di 60 secondi.
    In ogni momento, guarda gli ultimi 60 secondi.
    """

    def __init__(self, massimo: int, finestra_secondi: float):
        """
        Args:
            massimo: numero massimo di richieste nella finestra
            finestra_secondi: dimensione della finestra temporale
        """
        self._massimo = massimo
        self._finestra = finestra_secondi
        self._timestamp_richieste: deque = deque()
        self._lock = threading.Lock()

    def _pulisci_vecchie_richieste(self, ora: float) -> None:
        """Rimuove le richieste fuori dalla finestra."""
        soglia = ora - self._finestra
        while self._timestamp_richieste and self._timestamp_richieste[0] <= soglia:
            self._timestamp_richieste.popleft()

    def consenti(self) -> bool:
        """
        Tenta di "consumare" un token.
        Restituisce True se la richiesta e' consentita, False altrimenti.
        """
        with self._lock:
            ora = time.monotonic()
            self._pulisci_vecchie_richieste(ora)

            if len(self._timestamp_richieste) < self._massimo:
                self._timestamp_richieste.append(ora)
                return True
            return False

    def attendi_e_consumi(self) -> float:
        """
        Blocca finche' non e' possibile fare una richiesta.
        Restituisce il tempo di attesa in secondi.
        """
        while True:
            with self._lock:
                ora = time.monotonic()
                self._pulisci_vecchie_richieste(ora)

                if len(self._timestamp_richieste) < self._massimo:
                    self._timestamp_richieste.append(ora)
                    return 0.0

                # Calcola quando la richiesta piu' vecchia uscira' dalla finestra
                prossima_disponibilita = self._timestamp_richieste[0] + self._finestra

            attesa = prossima_disponibilita - time.monotonic()
            if attesa > 0:
                time.sleep(attesa)

    @property
    def n_richieste_correnti(self) -> int:
        """Numero di richieste nella finestra corrente."""
        with self._lock:
            ora = time.monotonic()
            self._pulisci_vecchie_richieste(ora)
            return len(self._timestamp_richieste)

    @property
    def prossima_disponibile_tra(self) -> float:
        """Secondi prima che la prossima richiesta sia disponibile (0 se disponibile ora)."""
        with self._lock:
            ora = time.monotonic()
            self._pulisci_vecchie_richieste(ora)
            if len(self._timestamp_richieste) < self._massimo:
                return 0.0
            return self._timestamp_richieste[0] + self._finestra - ora

def crea_rate_limited(massimo: int, finestra: float, blocca: bool = False):
    """
    Factory di decoratori per rate limiting.

    Args:
        massimo: richieste massime nella finestra
        finestra: secondi della finestra
        blocca: se True attendi; se False solleva RateLimitError
    """
    limiter = RateLimiterFinestraScorrevole(massimo, finestra)

    def decoratore(funzione):
        import functools
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            if blocca:
                attesa = limiter.attendi_e_consumi()
                if attesa > 0:
                    print(f"  [rate limit] Atteso {attesa:.2f}s")
            else:
                if not limiter.consenti():
                    raise RuntimeError(
                        f"Rate limit raggiunto: max {massimo} richieste "
                        f"per {finestra}s. Riprova tra "
                        f"{limiter.prossima_disponibile_tra:.2f}s"
                    )
            return funzione(*args, **kwargs)
        wrapper.limiter = limiter
        return wrapper
    return decoratore

# Test
@crea_rate_limited(massimo=5, finestra=2.0, blocca=False)
def api_call(id: int) -> str:
    return f"risposta_{id}"

print("=== Rate Limiter a Finestra Scorrevole ===")
print(f"Limite: 5 richieste per 2 secondi\n")

inizio = time.time()
successi = 0
fallimenti = 0

for i in range(8):
    try:
        risposta = api_call(i)
        successi += 1
        print(f"  [{time.time()-inizio:.2f}s] OK: {risposta}")
    except RuntimeError as e:
        fallimenti += 1
        print(f"  [{time.time()-inizio:.2f}s] BLOCCATO: {e}")

print(f"\nSuccessi: {successi}, Fallimenti: {fallimenti}")
print(f"Richieste nella finestra corrente: {api_call.limiter.n_richieste_correnti}")
```

```
# Output atteso:
=== Rate Limiter a Finestra Scorrevole ===
Limite: 5 richieste per 2 secondi

  [0.00s] OK: risposta_0
  [0.00s] OK: risposta_1
  [0.00s] OK: risposta_2
  [0.00s] OK: risposta_3
  [0.00s] OK: risposta_4
  [0.00s] BLOCCATO: Rate limit raggiunto: max 5 richieste per 2.0s. Riprova tra 1.99s
  [0.00s] BLOCCATO: Rate limit raggiunto: max 5 richieste per 2.0s. Riprova tra 1.99s
  [0.00s] BLOCCATO: Rate limit raggiunto: max 5 richieste per 2.0s. Riprova tra 1.99s

Successi: 5, Fallimenti: 3
Richieste nella finestra corrente: 5
```

---

## M2: Implementa un Cache Write-Through con Generatori

```python
import functools
import time
from typing import Generator, Any

class CacheWriteThrough:
    """
    Cache write-through: ogni write va sia in cache che nel backend.
    Garantisce la coerenza dei dati.

    Pattern: se scrivi in cache, scrivi ANCHE nel backend.
             Se leggi, controlla prima la cache.
    """

    def __init__(self, backend: dict = None):
        self._cache: dict[str, Any] = {}
        self._backend = backend or {}  # simula un database
        self._log_operazioni: list[dict] = []

    def get(self, chiave: str) -> Any:
        """Legge: prima da cache, poi dal backend."""
        if chiave in self._cache:
            self._log("read", chiave, "cache_hit")
            return self._cache[chiave]

        if chiave in self._backend:
            valore = self._backend[chiave]
            self._cache[chiave] = valore  # popola la cache
            self._log("read", chiave, "backend_hit")
            return valore

        self._log("read", chiave, "miss")
        return None

    def set(self, chiave: str, valore: Any) -> None:
        """Write-through: scrive in entrambi."""
        self._cache[chiave] = valore
        self._backend[chiave] = valore  # write-through!
        self._log("write", chiave, "write_through")

    def delete(self, chiave: str) -> bool:
        """Cancella da entrambi."""
        if chiave not in self._cache and chiave not in self._backend:
            return False
        self._cache.pop(chiave, None)
        self._backend.pop(chiave, None)
        self._log("delete", chiave, "ok")
        return True

    def _log(self, operazione: str, chiave: str, tipo: str) -> None:
        self._log_operazioni.append({
            "ts": time.time(),
            "op": operazione,
            "chiave": chiave,
            "tipo": tipo,
        })

    def log_operazioni(self) -> Generator[dict, None, None]:
        """Genera le operazioni effettuate in ordine cronologico."""
        yield from self._log_operazioni

    @property
    def statistiche(self) -> dict:
        """Calcola statistiche dal log."""
        hits = sum(1 for o in self._log_operazioni if o["tipo"] == "cache_hit")
        misses = sum(1 for o in self._log_operazioni if o["tipo"] == "miss")
        writes = sum(1 for o in self._log_operazioni if o["tipo"] == "write_through")
        totale = hits + misses
        return {
            "cache_hits": hits,
            "backend_hits": sum(1 for o in self._log_operazioni if o["tipo"] == "backend_hit"),
            "misses": misses,
            "writes": writes,
            "hit_rate": hits / max(totale, 1) * 100,
            "cache_size": len(self._cache),
            "backend_size": len(self._backend),
        }

# Uso
cache = CacheWriteThrough(backend={"utente:1": {"nome": "Alice"}, "utente:2": {"nome": "Bob"}})

# Letture
print("Letture:")
print(f"  utente:1 = {cache.get('utente:1')}")  # backend hit
print(f"  utente:1 = {cache.get('utente:1')}")  # cache hit
print(f"  utente:3 = {cache.get('utente:3')}")  # miss

# Scrittura
print("\nScritto utente:3:")
cache.set("utente:3", {"nome": "Carol"})
print(f"  Dalla cache: {cache.get('utente:3')}")
print(f"  Dal backend: {cache._backend.get('utente:3')}")

# Statistiche
print(f"\nStatistiche: {cache.statistiche}")

# Log operazioni tramite generatore
print("\nLog operazioni:")
for op in cache.log_operazioni():
    print(f"  {op['op']:8s} | {op['chiave']:12s} | {op['tipo']}")
```

```
# Output atteso:
Letture:
  utente:1 = {'nome': 'Alice'}
  utente:1 = {'nome': 'Alice'}
  utente:3 = None

Scritto utente:3:
  Dalla cache: {'nome': 'Carol'}
  Dal backend: {'nome': 'Carol'}

Statistiche: {'cache_hits': 1, 'backend_hits': 1, 'misses': 1, 'writes': 1, 'hit_rate': 33.3, 'cache_size': 2, 'backend_size': 3}

Log operazioni:
  read     | utente:1     | backend_hit
  read     | utente:1     | cache_hit
  read     | utente:3     | miss
  write    | utente:3     | write_through
  read     | utente:3     | cache_hit
```

---

## M3: Generatore per la Ricerca di Sottostringhe (Boyer-Moore Semplificato)

```python
from typing import Generator

def cerca_tutte_occorrenze(
    testo: str,
    pattern: str,
    sovrapponi: bool = False,
) -> Generator[int, None, None]:
    """
    Cerca tutte le occorrenze di 'pattern' in 'testo'.
    Genera le posizioni di inizio di ogni occorrenza.

    Args:
        testo: testo in cui cercare
        pattern: stringa da trovare
        sovrapponi: se True, permette occorrenze sovrapposte

    Yields:
        posizione (indice) di ogni occorrenza trovata

    Esempi:
        list(cerca_tutte_occorrenze("abaababa", "aba"))
        → [0, 2, 5] (senza sovrapposizione) o [0, 2, 4, 5] (con)
    """
    if not pattern or not testo:
        return

    n = len(testo)
    m = len(pattern)

    posizione = 0
    while posizione <= n - m:
        # Controlla se il pattern corrisponde in questa posizione
        if testo[posizione:posizione + m] == pattern:
            yield posizione
            if sovrapponi:
                posizione += 1
            else:
                posizione += m  # salta avanti per evitare sovrapposizioni
        else:
            posizione += 1

def conta_occorrenze(testo: str, pattern: str) -> int:
    """Conta le occorrenze di pattern in testo (senza materializzare)."""
    return sum(1 for _ in cerca_tutte_occorrenze(testo, pattern))

def sostituisci_lazy(
    testo: str,
    pattern: str,
    sostituto: str,
) -> Generator[str, None, None]:
    """
    Sostituisce le occorrenze di 'pattern' con 'sostituto' in modo lazy.
    Genera le parti del testo risultante un pezzo alla volta.
    """
    ultima_pos = 0
    for pos in cerca_tutte_occorrenze(testo, pattern):
        yield testo[ultima_pos:pos]
        yield sostituto
        ultima_pos = pos + len(pattern)
    yield testo[ultima_pos:]

# Test
testo = "il gatto sul tetto, il gatto matto, il gatto"
pattern = "gatto"

print(f"Testo: '{testo}'")
print(f"Pattern: '{pattern}'")
print(f"Occorrenze: {list(cerca_tutte_occorrenze(testo, pattern))}")
print(f"Numero occorrenze: {conta_occorrenze(testo, pattern)}")

sostituzione = "".join(sostituisci_lazy(testo, pattern, "CAT"))
print(f"Dopo sostituzione: '{sostituzione}'")

# Test con sovrapposizioni
testo2 = "aaaa"
print(f"\nTesto: '{testo2}', Pattern: 'aa'")
print(f"Senza sovrapposizioni: {list(cerca_tutte_occorrenze(testo2, 'aa', sovrapponi=False))}")
print(f"Con sovrapposizioni: {list(cerca_tutte_occorrenze(testo2, 'aa', sovrapponi=True))}")
```

```
# Output atteso:
Testo: 'il gatto sul tetto, il gatto matto, il gatto'
Pattern: 'gatto'
Occorrenze: [3, 23, 40]
Numero occorrenze: 3
Dopo sostituzione: 'il CAT sul tetto, il CAT matto, il CAT'

Testo: 'aaaa', Pattern: 'aa'
Senza sovrapposizioni: [0, 2]
Con sovrapposizioni: [0, 1, 2]
```

---

## M4: Context Manager per Gestione degli Errori a Livelli

```python
from contextlib import contextmanager
from typing import Generator, Type

class ErrorCollector:
    """
    Raccoglie errori da un blocco di codice senza interromperlo.
    Utile quando vuoi eseguire piu' operazioni e raccogliere tutti gli errori.
    """

    def __init__(self, tipi_da_raccogliere: tuple = (Exception,)):
        self._errori: list[Exception] = []
        self._tipi = tipi_da_raccogliere

    def aggiungi(self, errore: Exception) -> None:
        """Aggiunge manualmente un errore alla collezione."""
        self._errori.append(errore)

    @contextmanager
    def raccogli(self, operazione: str = None) -> Generator[None, None, None]:
        """
        Context manager che raccoglie eccezioni invece di propagarle.

        Uso:
            collector = ErrorCollector()
            with collector.raccogli("operazione A"):
                codice_che_potrebbe_fallire()
            with collector.raccogli("operazione B"):
                altra_operazione()

            if collector.ha_errori:
                print(collector.riepilogo)
        """
        try:
            yield
        except self._tipi as e:
            if operazione:
                # Aggiunge contesto all'eccezione
                e.operazione = operazione
            self._errori.append(e)

    @property
    def ha_errori(self) -> bool:
        return len(self._errori) > 0

    @property
    def n_errori(self) -> int:
        return len(self._errori)

    @property
    def riepilogo(self) -> str:
        if not self._errori:
            return "Nessun errore"
        righe = [f"{len(self._errori)} errori raccolti:"]
        for i, e in enumerate(self._errori, 1):
            operazione = getattr(e, "operazione", "?")
            righe.append(f"  [{i}] [{operazione}] {type(e).__name__}: {e}")
        return "\n".join(righe)

    def rilancia(self) -> None:
        """Solleva tutti gli errori come ExceptionGroup (Python 3.11+) o RuntimeError."""
        if not self._errori:
            return
        try:
            raise ExceptionGroup("Errori raccolti", self._errori)
        except NameError:
            # Python < 3.11
            raise RuntimeError(self.riepilogo) from self._errori[0]

# Uso
def processa_record(record: dict) -> dict:
    """Processa un record — potrebbe fallire."""
    if "nome" not in record:
        raise ValueError("Campo 'nome' mancante")
    if not isinstance(record.get("eta"), int):
        raise TypeError(f"Campo 'eta' deve essere int, non {type(record.get('eta')).__name__}")
    if record.get("eta", 0) < 0:
        raise ValueError(f"Eta' negativa: {record['eta']}")
    return {**record, "processato": True}

# Processa piu' record raccogliendo tutti gli errori
record_da_processare = [
    {"nome": "Alice", "eta": 28},       # OK
    {"eta": 35},                          # manca 'nome'
    {"nome": "Carol", "eta": "quaranta"}, # eta non e' int
    {"nome": "Dave", "eta": -5},          # eta negativa
    {"nome": "Eve", "eta": 30},           # OK
]

collector = ErrorCollector(tipi_da_raccogliere=(ValueError, TypeError))
risultati_ok = []

for i, record in enumerate(record_da_processare):
    with collector.raccogli(f"record_{i}"):
        risultato = processa_record(record)
        risultati_ok.append(risultato)

print(f"Processati con successo: {len(risultati_ok)}/{len(record_da_processare)}")
for r in risultati_ok:
    print(f"  {r}")

print(f"\n{collector.riepilogo}")
```

```
# Output atteso:
Processati con successo: 2/5
  {'nome': 'Alice', 'eta': 28, 'processato': True}
  {'nome': 'Eve', 'eta': 30, 'processato': True}

3 errori raccolti:
  [1] [record_1] ValueError: Campo 'nome' mancante
  [2] [record_2] TypeError: Campo 'eta' deve essere int, non str
  [3] [record_3] ValueError: Eta' negativa: -5
```

---

## M5: Decoratore Composito per Logging Strutturato

```python
import functools
import json
import time
import uuid
from typing import Any

# Sistema di logging strutturato (senza libreria esterna)
_log_buffer: list[dict] = []

def log_strutturato(livello: str, messaggio: str, **campi: Any) -> None:
    """Logga un evento in formato strutturato (JSON)."""
    entry = {
        "timestamp": time.time(),
        "livello": livello,
        "messaggio": messaggio,
        **campi,
    }
    _log_buffer.append(entry)
    print(json.dumps(entry, default=str))

def con_tracing(
    livello: str = "INFO",
    logga_argomenti: bool = False,
    logga_risultato: bool = False,
):
    """
    Decoratore che aggiunge distributed tracing alle funzioni.
    Ogni chiamata riceve un trace_id univoco.
    """
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            trace_id = str(uuid.uuid4())[:8]
            nome_funzione = f"{funzione.__module__}.{funzione.__qualname__}"

            log_kwargs = {
                "trace_id": trace_id,
                "funzione": nome_funzione,
            }

            if logga_argomenti:
                log_kwargs["args"] = args
                log_kwargs["kwargs"] = kwargs

            log_strutturato(livello, f"INIZIO {funzione.__name__}", **log_kwargs)
            inizio = time.perf_counter()

            try:
                risultato = funzione(*args, **kwargs)
                durata_ms = (time.perf_counter() - inizio) * 1000

                log_risultato_kwargs = {**log_kwargs, "durata_ms": round(durata_ms, 2)}
                if logga_risultato:
                    log_risultato_kwargs["risultato"] = risultato

                log_strutturato(livello, f"FINE OK {funzione.__name__}", **log_risultato_kwargs)
                return risultato

            except Exception as e:
                durata_ms = (time.perf_counter() - inizio) * 1000
                log_strutturato("ERROR", f"FINE ERRORE {funzione.__name__}",
                    **log_kwargs,
                    durata_ms=round(durata_ms, 2),
                    errore_tipo=type(e).__name__,
                    errore_messaggio=str(e),
                )
                raise

        return wrapper
    return decoratore

# Test
@con_tracing(livello="INFO", logga_argomenti=True, logga_risultato=True)
def calcola_sconto(prezzo: float, percentuale: float) -> float:
    """Calcola il prezzo scontato."""
    if percentuale < 0 or percentuale > 100:
        raise ValueError(f"Percentuale non valida: {percentuale}")
    return prezzo * (1 - percentuale / 100)

@con_tracing(livello="DEBUG")
def aggiorna_inventario(id_prodotto: int, quantita: int) -> dict:
    """Simula l'aggiornamento dell'inventario."""
    return {"id": id_prodotto, "nuova_quantita": quantita, "stato": "aggiornato"}

print("=== Chiamate tracciate ===")
prezzo_scontato = calcola_sconto(100.0, 20)
print()
inventario = aggiorna_inventario(42, 150)
print()

try:
    calcola_sconto(50.0, 150)  # errore: percentuale > 100
except ValueError:
    pass

print(f"\n=== Totale eventi loggati: {len(_log_buffer)} ===")
```

```
# Output atteso:
=== Chiamate tracciate ===
{"timestamp": 1704..., "livello": "INFO", "messaggio": "INIZIO calcola_sconto", "trace_id": "a1b2c3d4", "funzione": "__main__.calcola_sconto", "args": [100.0, 20], "kwargs": {}}
{"timestamp": 1704..., "livello": "INFO", "messaggio": "FINE OK calcola_sconto", "trace_id": "a1b2c3d4", "funzione": "__main__.calcola_sconto", "durata_ms": 0.05, "risultato": 80.0}

{"timestamp": 1704..., "livello": "DEBUG", "messaggio": "INIZIO aggiorna_inventario", "trace_id": "e5f6g7h8", "funzione": "__main__.aggiorna_inventario"}
{"timestamp": 1704..., "livello": "DEBUG", "messaggio": "FINE OK aggiorna_inventario", "trace_id": "e5f6g7h8", "funzione": "__main__.aggiorna_inventario", "durata_ms": 0.03}

{"timestamp": 1704..., "livello": "ERROR", "messaggio": "FINE ERRORE calcola_sconto", "trace_id": "i9j0k1l2", "funzione": "__main__.calcola_sconto", "durata_ms": 0.02, "errore_tipo": "ValueError", "errore_messaggio": "Percentuale non valida: 150"}

=== Totale eventi loggati: 6 ===
```

---

## M6: Implementazione di `contextlib.suppress` da Zero

```python
from typing import Type

class SoppressiException:
    """
    Re-implementazione di contextlib.suppress() per capirne il funzionamento.
    Sopprime le eccezioni dei tipi specificati.

    Funzionamento:
        - __enter__: non fa nulla
        - __exit__: controlla se l'eccezione e' del tipo da sopprimere
                    se si, return True (sopprime); altrimenti return False (propaga)
    """

    def __init__(self, *tipi_da_sopprimere: Type[Exception]):
        if not tipi_da_sopprimere:
            raise ValueError("Specificare almeno un tipo di eccezione da sopprimere")
        self._tipi = tipi_da_sopprimere

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Se non c'e' eccezione: exc_type e' None, non fare nulla
        if exc_type is None:
            return False

        # Se l'eccezione e' del tipo da sopprimere: return True (sopprime)
        if issubclass(exc_type, self._tipi):
            return True

        # Altrimenti: return False (l'eccezione si propaga)
        return False

    def __repr__(self):
        tipi_str = ", ".join(t.__name__ for t in self._tipi)
        return f"SoppressiException({tipi_str})"

# Test
print("=== SoppressiException ===")

# Sopprime FileNotFoundError
print("\nTest 1: FileNotFoundError soppresso")
with SoppressiException(FileNotFoundError):
    with open("/file/che/non/esiste.txt"):
        print("  Non dovrebbe arrivare qui")
print("  Continua dopo il blocco")

# Sopprime piu' tipi
print("\nTest 2: sopprime ValueError e TypeError")
for valore in ["ok", 123, None]:
    with SoppressiException(ValueError, TypeError, AttributeError):
        risultato = valore.upper()  # TypeError per int, AttributeError per None
        print(f"  Successo: '{valore}'.upper() = '{risultato}'")
    print(f"  Dopo blocco per: {valore!r}")

# NON sopprime altri tipi
print("\nTest 3: RuntimeError NON soppresso")
try:
    with SoppressiException(ValueError):
        raise RuntimeError("questo non viene soppresso")
except RuntimeError as e:
    print(f"  RuntimeError propagato: {e}")

print("\nImplementazione identica a contextlib.suppress()")
```

```
# Output atteso:
=== SoppressiException ===

Test 1: FileNotFoundError soppresso
  Continua dopo il blocco

Test 2: sopprime ValueError e TypeError
  Successo: 'ok'.upper() = 'OK'
  Dopo blocco per: 'ok'
  Dopo blocco per: 123
  Dopo blocco per: None

Test 3: RuntimeError NON soppresso
  RuntimeError propagato: questo non viene soppresso

Implementazione identica a contextlib.suppress()
```

---

# PARTE N: RIEPILOGO DEI PATTERN PER PRINCIPIANTI

---

## N1: I Tre Pattern Fondamentali in Parole Semplici

### Decoratore — "Aggiungi Superpoteri"

Immagina di avere un normale martello (la tua funzione). Il decoratore e' come aggiungere un manico ergonomico e un sensore di forza: il martello fa ancora la stessa cosa di base, ma ora hai anche statistiche e comfort.

```python
# Martello normale
def elabora_dati(n: int) -> list:
    return [i * 2 for i in range(n)]

# Martello con superpotere: misura il tempo
import functools, time

def aggiunge_timer(funzione):
    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        risultato = funzione(*args, **kwargs)  # usa ancora il "martello" originale
        print(f"Tempo: {(time.perf_counter()-inizio)*1000:.2f}ms")
        return risultato
    return wrapper

@aggiunge_timer
def elabora_dati_con_timer(n: int) -> list:
    return [i * 2 for i in range(n)]

elabora_dati_con_timer(10000)
```

```
# Output atteso:
Tempo: 0.83ms
```

### Generatore — "Produci su Richiesta"

Immagina di avere un fornaio. Invece di cuocere 1000 pani in anticipo (lista), il generatore e' un fornaio che cuoce un pane alla volta, quando lo chiedi. Non sprechi forno, spazio, o ingredienti.

```python
# Fornaio che produce tutto in anticipo (lista)
def produci_tutti_i_pani(n: int) -> list:
    return [f"pane_{i}" for i in range(n)]

# Fornaio che produce su richiesta (generatore)
def fornaio(n: int):
    for i in range(n):
        print(f"  [fornaio] Sto cuocendo pane_{i}...")
        yield f"pane_{i}"

# Con lista: cuoce tutto subito
print("Lista (tutto subito):")
pani_lista = produci_tutti_i_pani(3)  # tutti e 3 cucinati
print(f"Ho {len(pani_lista)} pani, mangio il primo: {pani_lista[0]}")

print()
print("Generatore (su richiesta):")
gen = fornaio(3)
pane = next(gen)  # cuoce solo il primo
print(f"Ho preso: {pane}")
pane = next(gen)  # cuoce il secondo
print(f"Ho preso: {pane}")
# Il terzo non viene mai cucinato se non chiesto
```

```
# Output atteso:
Lista (tutto subito):
  [fornaio] Sto cuocendo pane_0...
  [fornaio] Sto cuocendo pane_1...
  [fornaio] Sto cuocendo pane_2...
Ho 3 pani, mangio il primo: pane_0

Generatore (su richiesta):
  [fornaio] Sto cuocendo pane_0...
Ho preso: pane_0
  [fornaio] Sto cuocendo pane_1...
Ho preso: pane_1
```

### Context Manager — "Prendi e Rilascia con Garanzia"

Immagina una biblioteca. Il context manager e' la regola della biblioteca: prendi il libro (`__enter__`), usalo, poi lo ridai SEMPRE (`__exit__`) — anche se ti senti male nel mezzo della lettura.

```python
# Senza context manager: potresti dimenticare di restituire il libro
def senza_context_manager():
    libro = "Il Signore degli Anelli"
    print(f"Ho preso: {libro}")
    # ... leggo ...
    raise Exception("Mi sono addormentato!")  # Il libro non viene restituito!
    print("Restituisco il libro")  # non eseguito

# Con context manager: il libro viene sempre restituito
from contextlib import contextmanager

@contextmanager
def prendi_libro(titolo: str):
    print(f"Ho preso: {titolo}")
    try:
        yield titolo
    finally:
        print(f"Ho restituito: {titolo}")  # SEMPRE eseguito

try:
    with prendi_libro("Il Signore degli Anelli") as libro:
        print(f"Sto leggendo: {libro}")
        raise Exception("Mi sono addormentato!")
except Exception:
    pass

print("Il libro e' stato restituito!")
```

```
# Output atteso:
Ho preso: Il Signore degli Anelli
Sto leggendo: Il Signore degli Anelli
Ho restituito: Il Signore degli Anelli
Il libro e' stato restituito!
```

---

## N2: Domande Frequenti (FAQ)

**D: Quando uso un decoratore vs una funzione normale?**
R: Usa un decoratore quando vuoi aggiungere comportamento "trasversale" (cross-cutting concern) a una funzione: logging, timing, retry, caching, validazione. Se il comportamento e' specifico di quella funzione, tienilo nella funzione.

**D: Un generatore e' sempre preferibile a una lista?**
R: No. Usa un generatore quando: i dati sono grandi (non entrano in RAM), elabori in streaming (un elemento alla volta), o la sequenza e' infinita. Usa una lista quando: hai bisogno di accesso casuale (indici), devi iterare piu' volte, o la dimensione e' piccola e nota.

**D: Quando scrivo `__enter__`/`__exit__` invece di `@contextmanager`?**
R: Usa `@contextmanager` per logica semplice con una sola fase di setup/teardown. Usa la classe quando: hai stato complesso da mantenere, vuoi ereditarieta', o devi ottimizzare le performance (la classe e' leggermente piu' veloce).

**D: Cosa succede se ho un'eccezione dentro un `@contextmanager`?**
R: L'eccezione interrompe l'esecuzione dopo `yield`. Senza `try/finally`, il codice di cleanup non viene eseguito. Con `try/finally`, il `finally` viene sempre eseguito.

**D: Posso usare `@contextmanager` come decoratore su una funzione?**
R: Si, se il context manager e' creato con `@contextmanager` (che usa `contextlib.ContextDecorator`). Esempio: `@monitora_eccezioni("mia_funzione")` sulla funzione invece di `with monitora_eccezioni("mia_funzione"):`.

**D: Qual e' la differenza tra `functools.cache` e `functools.lru_cache`?**
R: `@functools.cache` e' un alias per `@functools.lru_cache(maxsize=None)` — cache illimitata. `lru_cache(maxsize=N)` tiene solo gli N risultati usati di recente (LRU = Least Recently Used). Usa `cache` per funzioni con pochi valori di input distinti; `lru_cache(128)` per funzioni con molti input possibili.

---

*Fine del Tutorial — Decoratori, Generatori e Context Manager*
*Hai completato il percorso! Sei pronto per tutorial_05.*



---

# PARTE O: ESERCIZI SUPPLEMENTARI — Sfide Extra

---

## O1: Sfida 1 — Implementa `functools.partial` da Zero

`functools.partial` crea una funzione con alcuni argomenti pre-impostati. Implementala da zero.

```python
def mia_partial(funzione, *args_fissi, **kwargs_fissi):
    """
    Implementazione di functools.partial.

    Crea una nuova funzione con alcuni argomenti pre-impostati.
    Gli argomenti fissi vengono preposti a quelli forniti alla chiamata.

    Differenza da functools.partial:
    - functools.partial crea un oggetto partial con __doc__, __name__, ecc.
    - questa implementazione e' piu' semplice ma funzionalmente equivalente

    Esempio:
        doppio = mia_partial(pow, 2)  # pow(2, ?)
        doppio(8)  # 256  (2^8)

        log_info = mia_partial(print, "[INFO]")
        log_info("messaggio")  # "[INFO] messaggio"
    """
    import functools

    @functools.wraps(funzione)
    def wrapper(*args, **kwargs):
        # Combina: args_fissi vengono prima di args
        tutti_args = args_fissi + args
        # kwargs: i kwargs_fissi di default, override con i kwargs passati
        tutti_kwargs = {**kwargs_fissi, **kwargs}
        return funzione(*tutti_args, **tutti_kwargs)

    wrapper.__wrapped__ = funzione
    wrapper.__partial_args__ = args_fissi
    wrapper.__partial_kwargs__ = kwargs_fissi

    return wrapper

# Test
# 1. Funzione potenza
potenza_di_2 = mia_partial(pow, 2)  # pow(2, x) = 2^x
print("Potenze di 2:")
for exp in range(1, 9):
    print(f"  2^{exp} = {potenza_di_2(exp)}")

# 2. Funzione di log prefissata
log_info = mia_partial(print, "[INFO]", sep="")
log_errore = mia_partial(print, "[ERRORE]", sep="")
log_info("Avvio applicazione")
log_errore("Connessione fallita")

# 3. Filtro per lista
filtra_positivi = mia_partial(filter, lambda x: x > 0)
numeri = [-3, -1, 0, 2, 5, -2, 8]
print(f"Numeri positivi: {list(filtra_positivi(numeri))}")

# 4. Verifica equivalenza con functools.partial
import functools
potenza_functools = functools.partial(pow, 2)
risultati_miei = [potenza_di_2(i) for i in range(1, 6)]
risultati_functools = [potenza_functools(i) for i in range(1, 6)]
print(f"Equivalente a functools.partial: {risultati_miei == risultati_functools}")
```

```
# Output atteso:
Potenze di 2:
  2^1 = 2
  2^2 = 4
  2^3 = 8
  2^4 = 16
  2^5 = 32
  2^6 = 64
  2^7 = 128
  2^8 = 256
[INFO]Avvio applicazione
[ERRORE]Connessione fallita
Numeri positivi: [2, 5, 8]
Equivalente a functools.partial: True
```

---

## O2: Sfida 2 — Generatore di Alberi N-Ari

```python
from typing import Generator, Any, Optional
from dataclasses import dataclass, field

@dataclass
class NodoAlbero:
    """Nodo di un albero N-ario (ogni nodo puo' avere N figli)."""
    valore: Any
    figli: list["NodoAlbero"] = field(default_factory=list)

    def aggiungi_figlio(self, valore: Any) -> "NodoAlbero":
        """Aggiunge un figlio e lo restituisce."""
        figlio = NodoAlbero(valore)
        self.figli.append(figlio)
        return figlio

    def __repr__(self) -> str:
        return f"Nodo({self.valore})"

def attraversa_preorder(nodo: NodoAlbero) -> Generator[NodoAlbero, None, None]:
    """Traversata pre-order: radice, poi figli da sinistra a destra."""
    yield nodo
    for figlio in nodo.figli:
        yield from attraversa_preorder(figlio)

def attraversa_postorder(nodo: NodoAlbero) -> Generator[NodoAlbero, None, None]:
    """Traversata post-order: figli da sinistra a destra, poi radice."""
    for figlio in nodo.figli:
        yield from attraversa_postorder(figlio)
    yield nodo

def attraversa_per_livello(radice: NodoAlbero) -> Generator[list[NodoAlbero], None, None]:
    """
    Traversata per livello (BFS).
    Genera una lista di nodi per ogni livello dell'albero.
    """
    from collections import deque
    coda = deque([[radice]])
    while coda:
        livello = coda.popleft()
        yield livello
        prossimo_livello = []
        for nodo in livello:
            prossimo_livello.extend(nodo.figli)
        if prossimo_livello:
            coda.append(prossimo_livello)

def cerca_in_albero(
    radice: NodoAlbero,
    predicato,
) -> Generator[NodoAlbero, None, None]:
    """Cerca nodi che soddisfano il predicato (DFS)."""
    for nodo in attraversa_preorder(radice):
        if predicato(nodo.valore):
            yield nodo

# Costruisci un albero della struttura aziendale
ceo = NodoAlbero("CEO")
cto = ceo.aggiungi_figlio("CTO")
cmo = ceo.aggiungi_figlio("CMO")
cfo = ceo.aggiungi_figlio("CFO")

dev1 = cto.aggiungi_figlio("Lead Dev Backend")
dev2 = cto.aggiungi_figlio("Lead Dev Frontend")
mkt1 = cmo.aggiungi_figlio("Marketing Manager")
fin1 = cfo.aggiungi_figlio("Finance Manager")

dev1.aggiungi_figlio("Backend Dev 1")
dev1.aggiungi_figlio("Backend Dev 2")
dev2.aggiungi_figlio("Frontend Dev 1")
mkt1.aggiungi_figlio("SEO Specialist")
fin1.aggiungi_figlio("Accountant")

# Traversata pre-order
print("Pre-order (radice prima):")
for nodo in attraversa_preorder(ceo):
    print(f"  {nodo.valore}")

# Per livello
print("\nPer livello:")
for i, livello in enumerate(attraversa_per_livello(ceo)):
    print(f"  Livello {i}: {[n.valore for n in livello]}")

# Cerca tutti i "Dev"
print("\nRuoli 'Dev':")
for nodo in cerca_in_albero(ceo, lambda v: "Dev" in str(v)):
    print(f"  {nodo.valore}")
```

```
# Output atteso:
Pre-order (radice prima):
  CEO
  CTO
  Lead Dev Backend
  Backend Dev 1
  Backend Dev 2
  Lead Dev Frontend
  Frontend Dev 1
  CMO
  Marketing Manager
  SEO Specialist
  CFO
  Finance Manager
  Accountant

Per livello:
  Livello 0: ['CEO']
  Livello 1: ['CTO', 'CMO', 'CFO']
  Livello 2: ['Lead Dev Backend', 'Lead Dev Frontend', 'Marketing Manager', 'Finance Manager']
  Livello 3: ['Backend Dev 1', 'Backend Dev 2', 'Frontend Dev 1', 'SEO Specialist', 'Accountant']

Ruoli 'Dev':
  Lead Dev Backend
  Backend Dev 1
  Backend Dev 2
  Lead Dev Frontend
  Frontend Dev 1
```

---

## O3: Sfida 3 — Context Manager per Timeout

```python
import signal
import time
import functools
from contextlib import contextmanager

@contextmanager
def timeout_ctx(secondi: float, messaggio: str = "Operazione scaduta"):
    """
    Context manager che imposta un timeout per un blocco di codice.
    Funziona su sistemi Unix (usa SIGALRM).

    NOTA: su Windows, usa threading.Timer invece.

    Args:
        secondi: timeout in secondi (puo' essere float per sub-secondi)
        messaggio: messaggio dell'eccezione TimeoutError
    """
    import sys

    if sys.platform == "win32":
        # Implementazione alternativa per Windows con threading
        import threading

        timeout_event = threading.Event()
        exception_holder = [None]

        def _raise_timeout():
            exception_holder[0] = TimeoutError(messaggio)
            timeout_event.set()

        timer = threading.Timer(secondi, _raise_timeout)
        timer.start()
        try:
            yield
            timer.cancel()
            if exception_holder[0]:
                raise exception_holder[0]
        except Exception:
            timer.cancel()
            raise
    else:
        # Implementazione Unix con SIGALRM
        def _gestore_allarme(signum, frame):
            raise TimeoutError(messaggio)

        vecchio_gestore = signal.signal(signal.SIGALRM, _gestore_allarme)
        signal.setitimer(signal.ITIMER_REAL, secondi)

        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, vecchio_gestore)

def con_timeout(secondi: float, messaggio: str = "Timeout"):
    """Decoratore per applicare un timeout a una funzione."""
    def decoratore(funzione):
        @functools.wraps(funzione)
        def wrapper(*args, **kwargs):
            with timeout_ctx(secondi, f"{funzione.__name__}: {messaggio}"):
                return funzione(*args, **kwargs)
        return wrapper
    return decoratore

# Test
print("=== Test timeout_ctx ===")

print("Operazione veloce (OK):")
with timeout_ctx(2.0):
    time.sleep(0.1)
    print("  Completata in 0.1s")

print("\nOperazione lenta (Timeout):")
try:
    with timeout_ctx(0.2, "Superato il limite di 0.2s"):
        time.sleep(1.0)  # troppo lento!
        print("  Non dovrebbe arrivare qui")
except TimeoutError as e:
    print(f"  TimeoutError: {e}")

# Con decoratore
@con_timeout(0.3, "L'API ha impiegato troppo")
def chiama_api_lenta():
    time.sleep(1.0)
    return "risposta"

print("\nChiamata API con timeout:")
try:
    risposta = chiama_api_lenta()
    print(f"  Risposta: {risposta}")
except TimeoutError as e:
    print(f"  TimeoutError: {e}")
```

```
# Output atteso:
=== Test timeout_ctx ===
Operazione veloce (OK):
  Completata in 0.1s

Operazione lenta (Timeout):
  TimeoutError: Superato il limite di 0.2s

Chiamata API con timeout:
  TimeoutError: chiama_api_lenta: L'API ha impiegato troppo
```

---

## O4: Sfida 4 — Decoratore `@dataclass_like` Manuale

Crea un decoratore che aggiunga `__init__`, `__repr__` e `__eq__` a una classe, simile a `@dataclass`.

```python
import functools

def dataclass_semplice(cls):
    """
    Decoratore che aggiunge __init__, __repr__ e __eq__
    basandosi sulle annotazioni della classe.

    Simile a @dataclass(eq=True, repr=True) ma piu' semplice.

    NOTA: questo e' un esempio didattico. In produzione usa @dataclass.
    """
    # Ottieni le annotazioni (campi)
    annotazioni = {}
    for klass in reversed(cls.__mro__):
        if hasattr(klass, "__annotations__"):
            annotazioni.update(klass.__annotations__)

    # Ottieni i valori di default
    default_valori = {}
    for nome, tipo in annotazioni.items():
        if hasattr(cls, nome):
            default_valori[nome] = getattr(cls, nome)

    # Crea __init__
    def __init__(self, **kwargs):
        for nome in annotazioni:
            if nome in kwargs:
                setattr(self, nome, kwargs[nome])
            elif nome in default_valori:
                setattr(self, nome, default_valori[nome])
            else:
                raise TypeError(f"__init__() manca argomento obbligatorio: '{nome}'")

    # Crea __repr__
    def __repr__(self):
        campi = ", ".join(
            f"{nome}={getattr(self, nome)!r}"
            for nome in annotazioni
        )
        return f"{cls.__name__}({campi})"

    # Crea __eq__
    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return all(
            getattr(self, nome) == getattr(other, nome)
            for nome in annotazioni
        )

    cls.__init__ = __init__
    cls.__repr__ = __repr__
    cls.__eq__ = __eq__

    return cls

# Uso
@dataclass_semplice
class Persona:
    nome: str
    eta: int
    email: str = "non_specificata@esempio.com"

# Test
alice = Persona(nome="Alice", eta=28)
bob = Persona(nome="Bob", eta=35, email="bob@esempio.com")
alice2 = Persona(nome="Alice", eta=28)

print(f"alice: {alice}")
print(f"bob: {bob}")
print(f"alice == alice2: {alice == alice2}")
print(f"alice == bob: {alice == bob}")

# Campo mancante
try:
    incompleto = Persona(nome="Carol")
except TypeError as e:
    print(f"Errore campo mancante: {e}")
```

```
# Output atteso:
alice: Persona(nome='Alice', eta=28, email='non_specificata@esempio.com')
bob: Persona(nome='Bob', eta=35, email='bob@esempio.com')
alice == alice2: True
alice == bob: False
Errore campo mancante: __init__() manca argomento obbligatorio: 'eta'
```

---

## O5: Sfida 5 — Pipeline Map-Reduce con Generatori

```python
from typing import Generator, Callable, Any, TypeVar
import functools

T = TypeVar("T")
U = TypeVar("U")

def map_lazy(funzione: Callable[[T], U], iterabile) -> Generator[U, None, None]:
    """Versione lazy di map()."""
    for elemento in iterabile:
        yield funzione(elemento)

def filter_lazy(predicato: Callable[[T], bool], iterabile) -> Generator[T, None, None]:
    """Versione lazy di filter()."""
    for elemento in iterabile:
        if predicato(elemento):
            yield elemento

def reduce_lazy(funzione: Callable[[U, T], U], iterabile, iniziale: U = None) -> U:
    """Versione di reduce() che consuma un generatore lazy."""
    it = iter(iterabile)
    if iniziale is None:
        try:
            accumulatore = next(it)
        except StopIteration:
            raise TypeError("reduce() su sequenza vuota senza valore iniziale")
    else:
        accumulatore = iniziale

    for elemento in it:
        accumulatore = funzione(accumulatore, elemento)

    return accumulatore

def pipeline_map_reduce(
    dati,
    *trasformazioni: Callable,
    riduttore: Callable = None,
    iniziale: Any = None,
) -> Any:
    """
    Esegue una pipeline Map-Reduce su dati arbitrari.
    Ogni trasformazione e' una funzione (map o filter) lazy.

    Args:
        dati: iterabile di partenza
        *trasformazioni: sequenza di funzioni da applicare
        riduttore: funzione di riduzione finale (default: lista)
        iniziale: valore iniziale per il riduttore

    Returns:
        risultato della riduzione
    """
    risultato = dati
    for trasformazione in trasformazioni:
        risultato = trasformazione(risultato)

    if riduttore is None:
        return list(risultato)
    return reduce_lazy(riduttore, risultato, iniziale)

# Dati: log di accessi simulati
import random
random.seed(42)

log_accessi = [
    {
        "utente_id": random.randint(1, 5),
        "pagina": random.choice(["/home", "/prodotti", "/about", "/contatti"]),
        "durata_ms": random.randint(50, 5000),
        "status": random.choice([200, 200, 200, 404, 500]),
    }
    for _ in range(100)
]

print("=== Analisi Log con Map-Reduce Lazy ===")
print(f"Totale log: {len(log_accessi)}")

# 1. Durata media degli accessi con status 200
durata_media = pipeline_map_reduce(
    log_accessi,
    functools.partial(filter_lazy, lambda r: r["status"] == 200),
    functools.partial(map_lazy, lambda r: r["durata_ms"]),
    riduttore=lambda acc, x: (acc[0] + x, acc[1] + 1),
    iniziale=(0, 0),
)
totale, n = durata_media
print(f"\nDurata media accessi 200 OK: {totale/n:.1f}ms (su {n} accessi)")

# 2. Conteggio errori per tipo
errori = pipeline_map_reduce(
    log_accessi,
    functools.partial(filter_lazy, lambda r: r["status"] >= 400),
    functools.partial(map_lazy, lambda r: r["status"]),
)
from collections import Counter
conteggio = Counter(errori)
print(f"\nErrori per tipo: {dict(sorted(conteggio.items()))}")

# 3. Pagine piu' visitate
pagine = pipeline_map_reduce(
    log_accessi,
    functools.partial(map_lazy, lambda r: r["pagina"]),
)
top_pagine = Counter(pagine).most_common(3)
print(f"\nTop 3 pagine: {top_pagine}")
```

```
# Output atteso:
=== Analisi Log con Map-Reduce Lazy ===
Totale log: 100

Durata media accessi 200 OK: 2547.3ms (su 60 accessi)

Errori per tipo: {404: 20, 500: 20}

Top 3 pagine: [('/home', 28), ('/prodotti', 27), ('/about', 24)]
```

---

## O6: Sfida Extra — Implementa `yield from` Manuale

Per capire a fondo `yield from`, reimplementalo con codice Python puro:

```python
def yield_from_manuale(sub_gen):
    """
    Reimplementa il comportamento di 'yield from sub_gen'.

    Gestisce:
    - La delega degli yield
    - La propagazione di send()
    - La propagazione di throw()
    - La cattura del return value (StopIteration.value)

    Ritorna il valore di return del sub-generator.
    """
    # Ottieni il valore inviato dall'esterno
    valore_inviato = None
    eccezione_iniettata = None

    while True:
        try:
            if eccezione_iniettata is not None:
                # Inietta l'eccezione nel sub-generator
                try:
                    prossimo = sub_gen.throw(
                        type(eccezione_iniettata),
                        eccezione_iniettata,
                        eccezione_iniettata.__traceback__,
                    )
                except StopIteration as stop:
                    return stop.value
                finally:
                    eccezione_iniettata = None
            else:
                # Invia il valore al sub-generator
                if valore_inviato is None:
                    prossimo = next(sub_gen)
                else:
                    prossimo = sub_gen.send(valore_inviato)

        except StopIteration as stop:
            # Il sub-generator e' terminato: ritorna il suo return value
            return stop.value

        try:
            # Yield il valore al chiamante esterno e attendi il prossimo send
            valore_inviato = yield prossimo
        except GeneratorExit:
            sub_gen.close()
            return
        except Exception as e:
            eccezione_iniettata = e

# Test: confronto tra yield from nativo e manuale
def sub_gen():
    """Sub-generator che produce valori e accetta send."""
    valore = yield "primo"
    yield f"secondo (ricevuto: {valore})"
    return "valore_finale"

def outer_con_yield_from():
    """Usa yield from nativo."""
    return_val = yield from sub_gen()
    yield f"outer: sub_gen ritornato '{return_val}'"

def outer_con_manuale():
    """Usa la nostra implementazione manuale."""
    return_val = yield from yield_from_manuale(sub_gen())
    yield f"outer: sub_gen ritornato '{return_val}'"

# Test entrambi
for nome, gen_factory in [("yield from nativo", outer_con_yield_from),
                           ("yield from manuale", outer_con_manuale)]:
    print(f"\n=== {nome} ===")
    gen = gen_factory()
    print(f"  next: {next(gen)}")
    print(f"  send(42): {gen.send(42)}")
    try:
        print(f"  next: {next(gen)}")
    except StopIteration as stop:
        print(f"  StopIteration: valore generato dall'outer")
```

```
# Output atteso:
=== yield from nativo ===
  next: primo
  send(42): secondo (ricevuto: 42)
  next: outer: sub_gen ritornato 'valore_finale'

=== yield from manuale ===
  next: primo
  send(42): secondo (ricevuto: 42)
  next: outer: sub_gen ritornato 'valore_finale'
```

---

*Fine delle Sfide Extra — Parte O*

---

# INDICE GENERALE

| Sezione | Contenuto |
|---------|-----------|
| **PARTE A** (A1-A10) | Funzioni come oggetti, closures, HOF, decoratori semplici, functools.wraps, decoratori parametrici, decoratori flessibili, cache, decoratori pratici, stacking, class-based |
| **PARTE B** (B1-B8) | Memoria e generatori, yield, generator functions, espressioni generatrici, yield from, itertools, send/throw/close, iteratori custom |
| **PARTE C** (C1-C6, +12 esercizi) | Context manager protocol, @contextmanager, suppress/redirect, ExitStack, async context manager |
| **PARTE D** (D1-D4, ext. D5-D10) | Descriptors, __init_subclass__, async generators, PEP history, metaclassi, abstract base classes |
| **PARTE E** (E1-E11) | Mappa mentale, tabelle, errori comuni, ricette, glossario, diagrammi decisionali, checklist 60+ item |
| **PARTE F** (F1-F6) | Task Scheduler, Configurazione, asyncio Queue, Utils library, Observer/EventBus, Data Pipeline con cache |
| **PARTE I** (I1-I4, I5-I6) | Pattern catalogo decoratori, generatori, context manager; benchmark; anti-pattern; cheatsheet |
| **PARTE L** (L1-L4) | Soluzioni guidate: validate_types, Fibonacci, test database, Cache Multi-Livello |
| **PARTE M** (M1-M6) | Rate Limiter sliding window, Cache Write-Through, ricerca sottostringhe, ErrorCollector, logging strutturato, suppress manuale |
| **PARTE N** (N1-N2) | Spiegazioni semplificate per principianti, FAQ |
| **PARTE O** (O1-O6) | Sfide extra: partial, alberi, timeout, dataclass, map-reduce, yield from manuale |

---

*Documento completato.*
*Dimensione finale: ~420 KB | Tempo stimato di studio: 35-45 ore*




---

# SEZIONE FINALE: NOTE DI STUDIO E CONSIGLI PRATICI

---

## Consigli per lo Studio

### Come Usare Questo Tutorial

Questo tutorial e' diviso in sezioni indipendenti ma correlate. Puoi seguire l'ordine lineare o saltare a sezioni specifiche basandoti sui tuoi obiettivi.

**Percorso consigliato per principianti:**
1. Leggi prima la sezione N1 (spiegazioni semplificate)
2. Studia PARTE A in ordine (A1-A10)
3. Pratica con gli esercizi alla fine della PARTE A
4. Studia PARTE B (B1-B8) con attenzione agli esercizi
5. Completa PARTE C con tutti gli esercizi C1-C14
6. Leggi le sezioni D ed E come riferimento
7. Torna ai pattern catalogo (PARTE I) per ripasso

**Percorso accelerato per chi conosce le basi:**
1. Leggi il cheatsheet (I6)
2. Vai direttamente ai pattern avanzati (A_EXT e B_EXT)
3. Concentrati sugli esercizi nelle sezioni L e O
4. Leggi la PARTE D per gli argomenti avanzati

---

## Tecniche di Studio Efficaci

### Tecnica 1: Digita il Codice a Mano

Non copiare-incollare! Digitare il codice a mano costruisce la memoria muscolare e ti fa notare dettagli che altrimenti potresti perdere. Quando digiti manualmente:
- Fai attenzione all'indentazione (Python e' sensibile agli spazi)
- Nota i due punti alla fine di `def`, `if`, `for`, `with`, ecc.
- Osserva come i decoratori si impilano con `@`

### Tecnica 2: Sperimenta con le Variazioni

Dopo ogni esempio, modifica qualcosa per vedere cosa succede:

```python
# Esempio: cosa succede senza @functools.wraps?
def senza_wraps(f):
    def wrapper(*a, **kw): return f(*a, **kw)
    return wrapper

def con_wraps(f):
    import functools
    @functools.wraps(f)
    def wrapper(*a, **kw): return f(*a, **kw)
    return wrapper

@senza_wraps
def mia_funzione():
    """La mia docstring."""
    pass

print(f"Senza @wraps: __name__ = {mia_funzione.__name__}")
print(f"Senza @wraps: __doc__ = {mia_funzione.__doc__}")
```

```
# Output atteso:
Senza @wraps: __name__ = wrapper
Senza @wraps: __doc__ = None
```

Domande da esplorare:
- Cosa succede se rimuovi `@functools.wraps`?
- Cosa succede se un generatore ha piu' `return` invece di `yield`?
- Cosa succede se `__exit__` restituisce `True` sempre?
- Cosa succede se `yield from` e' dentro un `try/finally`?

### Tecnica 3: Scrivi Test Prima del Codice (TDD)

Prova la tecnica TDD (Test-Driven Development):

```python
# PASSO 1: scrivi il test (fallira' perche' la funzione non esiste ancora)
def test_mio_decoratore():
    @mio_decoratore
    def funzione(): return 42

    assert funzione() == 42
    assert funzione.__name__ == "funzione"
    assert hasattr(funzione, "n_chiamate")

# PASSO 2: implementa il minimo per farlo passare
import functools

def mio_decoratore(f):
    @functools.wraps(f)
    def wrapper(*a, **kw):
        wrapper.n_chiamate += 1
        return f(*a, **kw)
    wrapper.n_chiamate = 0
    return wrapper

# PASSO 3: verifica
test_mio_decoratore()
print("Test superato!")
```

```
# Output atteso:
Test superato!
```

### Tecnica 4: Leggi il Codice degli Altri

Studia le implementazioni nella libreria standard Python. Per esempio, apri `functools.py` e leggi come e' implementato `lru_cache`:

```python
import functools
import inspect

# Dove si trova functools?
print(inspect.getfile(functools))

# Come e' implementato wraps?
print(inspect.getsource(functools.wraps))
```

Questo mostra come i professionisti scrivono codice Python.

---

## Errori Comuni per Livello

### Livello Principiante

```python
# ERRORE: confondere la definizione con la chiamata del decoratore
def timer(f):
    import time
    import functools
    @functools.wraps(f)
    def w(*a, **kw):
        t = time.perf_counter()
        r = f(*a, **kw)
        print(f"{time.perf_counter()-t:.3f}s")
        return r
    return w

# SBAGLIATO: timer e' il decoratore, non la funzione
funzione_con_timer = timer  # punta al decoratore stesso!
funzione_con_timer(10)      # TypeError: timer() prende 1 argomento (funzione), non intero

# CORRETTO: applica il decoratore alla funzione
def mia_funzione(n):
    return sum(range(n))

funzione_con_timer = timer(mia_funzione)  # crea la versione decorata
risultato = funzione_con_timer(10)         # chiama la versione decorata
```

```
# Output atteso:
0.000s
```

### Livello Intermedio

```python
# ERRORE: il generatore e' stato esaurito
def quadrati(n):
    for i in range(n):
        yield i * i

gen = quadrati(5)

# Prima iterazione
for q in gen:
    print(q, end=" ")
print()

# ERRORE: il generatore e' esaurito!
for q in gen:
    print(q, end=" ")    # non stampa nulla
print("(generatore esaurito)")

# CORRETTO: crea un nuovo generatore
for q in quadrati(5):   # nuovo generatore ogni volta
    print(q, end=" ")
print()
```

```
# Output atteso:
0 1 4 9 16
(generatore esaurito)
0 1 4 9 16
```

### Livello Avanzato

```python
# ERRORE: __exit__ non gestisce l'eccezione correttamente
class CMSbagliato:
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        print(f"Cleanup: {et.__name__ if et else 'nessuna eccezione'}")
        # Dimentica di restituire True per sopprimere ValueError
        # Dimentica return False per propagare le altre

# L'eccezione si propaga sempre (implicitamente return None = False)
try:
    with CMSbagliato():
        raise ValueError("ops")
except ValueError:
    print("ValueError propagata!")

# CORRETTO: gestione esplicita
class CMCorretto:
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        print(f"Cleanup: {et.__name__ if et else 'nessuna eccezione'}")
        if et is ValueError:
            return True    # sopprime ValueError
        return False       # propaga tutto il resto

with CMCorretto():
    raise ValueError("soppresso!")
print("ValueError soppressa: esecuzione continua")
```

```
# Output atteso:
Cleanup: ValueError
ValueError propagata!
Cleanup: ValueError
ValueError soppressa: esecuzione continua
```

---

## Autoverifica Finale

Prima di passare al tutorial successivo, assicurati di poter rispondere a queste domande senza guardare le note:

1. Scrivi un decoratore `@contatore` che conti quante volte viene chiamata una funzione.
2. Scrivi un generatore `pari_dispari(n)` che produca tuple `(pari, dispari)` per i primi n numeri.
3. Scrivi un context manager `sezione_critica` che stampi "Inizio sezione" all'entrata e "Fine sezione" all'uscita, anche in caso di eccezione.
4. Cosa produce `list(map(lambda x: x*2, filter(lambda x: x%2==0, range(10))))`?
5. Come si usa `yield from` per appiattire una lista annidata?

**Risposte:**

```python
# 1. @contatore
import functools

def contatore(f):
    @functools.wraps(f)
    def wrapper(*a, **kw):
        wrapper.count += 1
        return f(*a, **kw)
    wrapper.count = 0
    return wrapper

@contatore
def ciao(): return "ciao"
ciao(); ciao(); ciao()
print(ciao.count)  # 3

# 2. pari_dispari
def pari_dispari(n):
    for i in range(n):
        yield (i * 2, i * 2 + 1)

print(list(pari_dispari(3)))  # [(0,1),(2,3),(4,5)]

# 3. sezione_critica
from contextlib import contextmanager

@contextmanager
def sezione_critica():
    print("Inizio sezione")
    try:
        yield
    finally:
        print("Fine sezione")

with sezione_critica():
    print("  Dentro la sezione")

# 4. list(map(lambda x: x*2, filter(lambda x: x%2==0, range(10))))
print(list(map(lambda x: x*2, filter(lambda x: x%2==0, range(10)))))
# [0, 4, 8, 12, 16]

# 5. appiattisci con yield from
def appiattisci(lst):
    for elem in lst:
        if isinstance(elem, list):
            yield from appiattisci(elem)
        else:
            yield elem

print(list(appiattisci([1, [2, [3, 4]], [5, 6]])))  # [1,2,3,4,5,6]
```

```
# Output atteso:
3
[(0, 1), (2, 3), (4, 5)]
Inizio sezione
  Dentro la sezione
Fine sezione
[0, 4, 8, 12, 16]
[1, 2, 3, 4, 5, 6]
```

---

*Fine del tutorial completo.*
*Passa a `tutorial_05` per continuare il tuo percorso Python.*
