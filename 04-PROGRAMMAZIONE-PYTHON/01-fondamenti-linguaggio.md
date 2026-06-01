---
corso: Programmazione Python
fase: 1 — Fondamenti
modulo: "01"
versione: Python 3.12+
livello: principiante-intermedio
prerequisiti:
  - uso base del terminale (shell Bash o PowerShell)
  - conoscenza elementare di almeno un linguaggio di programmazione
  - installazione di Python 3.12+ funzionante
obiettivi:
  - padroneggiare il sistema di tipi primitivi e il modello a oggetti di Python
  - scrivere codice idiomatico con f-string, comprehension e pattern matching
  - applicare le regole di scope LEGB e comprendere le closure
  - riconoscere e prevenire le trappole classiche (mutable default, late binding, integer caching)
  - utilizzare le funzioni built-in fondamentali (zip, enumerate, map, filter, sorted, any, all)
  - comprendere la semantica a riferimento e la differenza tra copia superficiale e profonda
  - leggere e applicare i principi dello Zen of Python al codice quotidiano
tag:
  - python
  - fondamenti
  - tipi-di-dato
  - funzioni
  - scope
  - pattern-matching
  - comprehension
  - data-model
---

# Fondamenti del Linguaggio Python — Guida Completa

> **Modulo 01** · **Versione:** Python 3.12+ · **Aggiornamento:** 2026-04-27

## Idee guida
1. **Pythonic > clever.** "Readability counts" — Zen of Python.
2. **f-string > `format()` > `%` formatting.**
3. **List comprehension > map+filter per readability.**
4. **`is None` not `== None`.** Identity vs equality.


## Indice

1. [Panoramica](#panoramica)
2. [Mappa Concettuale — Sistema di Tipi](#mappa-concettuale--sistema-di-tipi)
3. [Tipi di Dati Primitivi](#tipi-di-dati-primitivi)
4. [Variabili e Assegnazione](#variabili-e-assegnazione)
5. [Strutture Dati Built-in](#strutture-dati-built-in)
6. [Controllo di Flusso](#controllo-di-flusso)
7. [Funzioni](#funzioni)
8. [Moduli e Pacchetti](#moduli-e-pacchetti)
9. [Input/Output Base](#inputoutput-base)
10. [Best Practices](#best-practices)
11. [Modello di Dati Python](#modello-di-dati-python)
12. [Modello di Memoria](#modello-di-memoria)
13. [Lo Zen di Python — PEP 20](#lo-zen-di-python--pep-20)
14. [Confronti e Identita](#confronti-e-identita)
15. [Unpacking Approfondito](#unpacking-approfondito)
16. [Troubleshooting — Errori Classici](#troubleshooting--errori-classici)
17. [Esercizi](#esercizi)
18. [Letture e Riferimenti](#letture-e-riferimenti)
19. [Riferimenti Incrociati](#riferimenti-incrociati)
20. [Glossario](#glossario)

---

## Panoramica

### Storia e Filosofia

Python nasce alla fine degli anni '80 per mano di Guido van Rossum presso il Centrum Wiskunde & Informatica (CWI) nei Paesi Bassi. La prima versione pubblica, Python 0.9.0, viene rilasciata nel febbraio 1991. Il nome del linguaggio non deriva dal serpente, bensì dal gruppo comico britannico Monty Python, riflettendo fin dall'inizio una filosofia che valorizza il piacere nella programmazione.

Python 2.0, rilasciato nell'ottobre 2000, ha introdotto funzionalita fondamentali come le list comprehension e il garbage collector con rilevamento dei cicli di riferimento. Python 3.0, rilasciato nel dicembre 2008, ha rappresentato una rottura deliberata con la retrocompatibilita per correggere difetti strutturali del linguaggio. Python 2 ha raggiunto il fine vita (End of Life) il 1 gennaio 2020 e non riceve piu aggiornamenti di sicurezza. Oggi Python 3.12+ rappresenta la versione corrente di riferimento.

La filosofia di Python e sintetizzata nello **Zen of Python** (PEP 20), accessibile digitando `import this` nell'interprete. I principi fondamentali includono:

```
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Readability counts.
There should be one-- and preferably only one --obvious way to do it.
```

Questi principi guidano ogni aspetto del design del linguaggio: la sintassi privilegia la leggibilita, l'indentazione obbligatoria impone una struttura visiva coerente, e le scelte progettuali favoriscono l'esplicitezza rispetto alla magia implicita.

Il principio "There should be one obvious way to do it" contrasta con la filosofia di linguaggi come Perl ("There's more than one way to do it") e si traduce in una comunita che valorizza la coerenza stilistica. Questo approccio ha prodotto PEP 8, la guida di stile ufficiale, che e diventata uno standard de facto seguito da praticamente tutti i progetti Python professionali. La combinazione di sintassi pulita, libreria standard estesa e comunita accogliente ha reso Python il linguaggio piu insegnato nelle universita e uno dei piu richiesti nel mercato del lavoro.

### Linguaggio Interpretato e CPython

Python e un linguaggio **interpretato** — il codice sorgente non viene compilato direttamente in codice macchina come avviene per C o Rust. L'implementazione di riferimento e **CPython**, scritta in C, che compila il sorgente Python in **bytecode** (file `.pyc` nella directory `__pycache__`) e lo esegue su una macchina virtuale (Python Virtual Machine). Altre implementazioni includono PyPy (con compilatore JIT per prestazioni superiori), Jython (sulla JVM) e IronPython (su .NET).

Un aspetto cruciale di CPython e il **GIL (Global Interpreter Lock)**: un mutex che permette a un solo thread alla volta di eseguire bytecode Python. Questo semplifica la gestione della memoria ma limita il parallelismo effettivo nei programmi CPU-bound. Per aggirare questa limitazione si ricorre al modulo `multiprocessing` o, a partire da Python 3.13, alla modalita sperimentale free-threaded (PEP 703).

### REPL e Esecuzione degli Script

Il **REPL** (Read-Eval-Print Loop) e l'ambiente interattivo di Python, accessibile digitando `python3` nel terminale. Permette di testare espressioni, esplorare API e prototipare rapidamente:

```python
>>> 2 + 3
5
>>> "ciao".upper()
'CIAO'
>>> [x**2 for x in range(5)]
[0, 1, 4, 9, 16]
```

Per eseguire uno script si utilizza il comando `python3 nome_script.py`. E possibile anche rendere uno script eseguibile direttamente su sistemi Unix aggiungendo lo **shebang** in prima riga:

```python
#!/usr/bin/env python3
print("Esecuzione diretta dello script")
```

Un'alternativa moderna al REPL standard e **IPython**, che offre autocompletamento avanzato, syntax highlighting, comandi magici (come `%timeit` per il benchmarking) e integrazione con Jupyter Notebook. Per ambienti di sviluppo professionali, strumenti come `ptpython` forniscono un'esperienza REPL ancora piu ricca con supporto per la validazione della sintassi in tempo reale.

Python supporta anche l'esecuzione diretta di moduli tramite il flag `-m`: il comando `python3 -m http.server 8000` avvia un server HTTP di sviluppo, mentre `python3 -m venv mio_ambiente` crea un ambiente virtuale. Questo meccanismo sfrutta il file `__main__.py` all'interno dei pacchetti per definire il comportamento quando vengono eseguiti come script.

---

## Mappa Concettuale — Sistema di Tipi

La seguente mappa ASCII illustra la gerarchia del sistema di tipi in Python. Ogni valore in Python e un oggetto; la radice della gerarchia e `object`.

```
                               object
                                 |
            +--------------------+---------------------+
            |                    |                     |
         NoneType             numbers               Iterable
         (None)                 |                     |
                    +-----------+---------+     +-----+-------+--------+
                    |           |         |     |     |       |        |
                  Number     Integral   Real  str   bytes   tuple   frozenset
                    |           |         |               (immut.)  (immut.)
                +---+---+    int  bool  float                |
                |       |                  |              namedtuple
              complex Decimal           Fraction
                                                    +------+------+-------+
                                                    |      |      |       |
                                                   list   dict   set   bytearray
                                                 (mut.)  (mut.) (mut.)  (mut.)
                                                    |
                                                  deque
                                                (collections)

    Legenda:
    (mut.)   = mutabile      — il contenuto puo cambiare dopo la creazione
    (immut.) = immutabile    — il contenuto e fisso dopo la creazione
    ------   = ereditarieta  — la classe figlia estende la classe genitore

    Gerarchia ABC (Abstract Base Class) di numbers:
    numbers.Number  >  numbers.Complex  >  numbers.Real  >  numbers.Rational  >  numbers.Integral

    Protocolli chiave:
    Hashable   = implementa __hash__  (necessario per chiavi dict e elementi set)
    Iterable   = implementa __iter__ (utilizzabile in cicli for)
    Sized      = implementa __len__  (supporta len())
    Container  = implementa __contains__ (supporta l'operatore in)
    Callable   = implementa __call__ (invocabile con ())
```

Questa gerarchia riflette un principio fondamentale: in Python, **tutto e un oggetto**. Un intero `42` e un'istanza della classe `int`; la funzione `len` e un'istanza della classe `builtin_function_or_method`; persino una classe e un'istanza della metaclasse `type`. Questa uniformita rende il linguaggio coerente: ogni valore possiede un tipo, un identita (`id()`) e un insieme di attributi e metodi ispezionabili.

Riferimento: https://docs.python.org/3/library/stdtypes.html (consultato: 2026-05-23)

---

## Tipi di Dati Primitivi

### Numeri

Python offre tre tipi numerici fondamentali: **int**, **float** e **complex**.

#### Interi (int)

Gli interi in Python hanno **precisione arbitraria**: non esiste un limite massimo di valore, la dimensione cresce dinamicamente in base alla necessita di memoria. Questa caratteristica distingue Python dalla maggior parte dei linguaggi che impongono limiti a 32 o 64 bit.

```python
# Precisione arbitraria
numero_grande = 10 ** 100  # googol, nessun overflow
print(numero_grande)

# Basi numeriche diverse
decimale = 255
binario = 0b11111111     # prefisso 0b per binario
ottale = 0o377           # prefisso 0o per ottale
esadecimale = 0xFF       # prefisso 0x per esadecimale

# Underscore come separatore visivo (Python 3.6+)
popolazione_mondiale = 8_000_000_000
```

#### Numeri in Virgola Mobile (float)

I float seguono lo standard **IEEE 754** a doppia precisione (64 bit), offrendo circa 15-17 cifre significative di precisione. Questo comporta le classiche problematiche di approssimazione:

```python
>>> 0.1 + 0.2
0.30000000000000004

# Per calcoli finanziari usare il modulo decimal
from decimal import Decimal
Decimal('0.1') + Decimal('0.2')  # Decimal('0.3')
```

I float supportano anche i valori speciali `float('inf')`, `float('-inf')` e `float('nan')`.

#### Numeri Complessi (complex)

Python supporta nativamente i numeri complessi con la notazione `j` per la parte immaginaria:

```python
z = 3 + 4j
print(z.real)       # 3.0
print(z.imag)       # 4.0
print(abs(z))       # 5.0 (modulo)
print(z.conjugate()) # (3-4j)
```

#### Operazioni Aritmetiche

```python
a, b = 17, 5

print(a + b)    # 22   — addizione
print(a - b)    # 12   — sottrazione
print(a * b)    # 85   — moltiplicazione
print(a / b)    # 3.4  — divisione float (restituisce sempre float)
print(a // b)   # 3    — divisione intera (floor division)
print(a % b)    # 2    — modulo (resto della divisione)
print(a ** b)   # 1419857 — potenza (elevamento)
```

La differenza tra `/` e `//` e fondamentale: `/` restituisce sempre un float, mentre `//` arrotonda verso il basso (floor) e restituisce un intero se entrambi gli operandi sono interi.

#### Funzioni Built-in per i Numeri

```python
print(abs(-42))          # 42 — valore assoluto
print(round(3.14159, 2)) # 3.14 — arrotondamento a 2 decimali
print(round(2.5))        # 2 — arrotondamento bancario (al pari piu vicino)

quoziente, resto = divmod(17, 5)
print(quoziente, resto)  # 3 2

print(pow(2, 10))        # 1024 — equivalente a 2 ** 10
print(pow(2, 10, 1000))  # 24 — (2 ** 10) % 1000, efficiente per modular exponentiation
```

#### Il Modulo math

```python
import math

print(math.pi)          # 3.141592653589793
print(math.e)           # 2.718281828459045
print(math.sqrt(144))   # 12.0
print(math.ceil(3.2))   # 4 — arrotondamento verso l'alto
print(math.floor(3.8))  # 3 — arrotondamento verso il basso
print(math.log(100, 10))# 2.0 — logaritmo in base 10
print(math.factorial(6))# 720
print(math.gcd(48, 18)) # 6 — massimo comun divisore
print(math.isclose(0.1 + 0.2, 0.3))  # True — confronto con tolleranza
```

#### Approfondimento — int a Precisione Illimitata

L'implementazione CPython rappresenta gli interi piccoli come un singolo "digit" in base 2^30 (su piattaforme a 64 bit). Quando il valore supera questa dimensione, CPython alloca automaticamente un array di digit, estendendolo senza limite. Questo significa che operazioni come `2 ** 1_000_000` funzionano correttamente, ma con costo computazionale crescente: l'addizione di interi di N cifre e O(N), la moltiplicazione usa l'algoritmo di Karatsuba per grandi valori.

```python
import sys

# Dimensione in memoria di un intero piccolo vs grande
print(sys.getsizeof(0))          # 28 byte (overhead oggetto)
print(sys.getsizeof(2 ** 30))    # 32 byte (1 digit aggiuntivo)
print(sys.getsizeof(2 ** 1000))  # 164 byte (molti digit)

# Conversioni esplicite tra basi
n = 255
print(bin(n))    # '0b11111111'
print(oct(n))    # '0o377'
print(hex(n))    # '0xff'

# bit_length(): numero minimo di bit per rappresentare il valore
print((1024).bit_length())    # 11
print((0).bit_length())       # 0

# bit_count(): numero di bit a 1 nella rappresentazione binaria (Python 3.10+)
print((255).bit_count())      # 8
print((1024).bit_count())     # 1

# Conversione da stringa con base arbitraria
print(int('ff', 16))          # 255
print(int('111', 2))          # 7
print(int('77', 8))           # 63
```

Riferimento: https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex (consultato: 2026-05-23)

#### Approfondimento — IEEE 754 e le Sue Trappole

Il formato IEEE 754 a doppia precisione utilizza 1 bit di segno, 11 bit di esponente e 52 bit di mantissa, per un totale di 64 bit. Questa rappresentazione binaria non puo codificare esattamente tutte le frazioni decimali, il che produce errori di arrotondamento che sorprendono regolarmente i principianti.

```python
# Confronto diretto di float: MAI usare ==
>>> 0.1 + 0.2 == 0.3
False

# Usare math.isclose() con tolleranze esplicite
import math
print(math.isclose(0.1 + 0.2, 0.3))                    # True (rel_tol=1e-9)
print(math.isclose(0.1 + 0.2, 0.3, abs_tol=1e-15))     # True

# Valori speciali IEEE 754
inf = float('inf')
print(inf > 10 ** 308)        # True
print(inf + 1 == inf)         # True (assorbimento)
print(inf - inf)              # nan (indeterminato)

nan = float('nan')
print(nan == nan)              # False — NaN non e uguale a se stesso
print(math.isnan(nan))         # True — il modo corretto per verificare

# Errore di cancellazione: sottrarre numeri quasi uguali amplifica l'errore
a = 1.0000000000000002
b = 1.0000000000000001
print(a - b)                   # 0.0 — la differenza e sotto la precisione
                               # il risultato corretto sarebbe 1e-16

# Limiti del float
print(sys.float_info.max)      # ~1.8e+308 — valore massimo
print(sys.float_info.min)      # ~2.2e-308 — valore minimo normalizzato positivo
print(sys.float_info.epsilon)  # ~2.2e-16  — la piu piccola differenza da 1.0
```

Riferimento: https://docs.python.org/3/tutorial/floatingpoint.html (consultato: 2026-05-23)

#### Approfondimento — Decimal per Calcoli Finanziari

Il modulo `decimal` implementa l'aritmetica decimale a precisione arbitraria secondo lo standard IEEE 854. E la scelta obbligata per calcoli finanziari, fiscali, e qualsiasi dominio dove l'errore di arrotondamento del float e inaccettabile.

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, getcontext

# REGOLA: creare Decimal sempre da stringa, MAI da float
corretto = Decimal('0.1') + Decimal('0.2')
print(corretto)                # 0.3 — esatto

sbagliato = Decimal(0.1)      # Decimal('0.1000000000000000055511151231257827021181583404541015625')
# Il float 0.1 e gia approssimato PRIMA della conversione

# Arrotondamento esplicito: fondamentale per contabilita
prezzo = Decimal('19.99')
iva = Decimal('0.22')
totale = prezzo * (1 + iva)
print(totale)                                           # 24.3878
print(totale.quantize(Decimal('0.01'), ROUND_HALF_UP))  # 24.39

# Precisione globale
getcontext().prec = 50
print(Decimal(1) / Decimal(7))
# 0.14285714285714285714285714285714285714285714285714

# Confronto: Decimal vs float in una somma ripetuta
somma_float = sum(0.1 for _ in range(10))
somma_decimal = sum(Decimal('0.1') for _ in range(10))
print(somma_float)     # 0.9999999999999999
print(somma_decimal)   # 1.0
```

Per la libreria `fractions` (frazioni esatte come `Fraction(1, 3)`) si vedano le strutture dati avanzate nel **Modulo 03**.

Riferimento: https://docs.python.org/3/library/decimal.html (consultato: 2026-05-23)

### Stringhe

Le stringhe in Python sono sequenze immutabili di caratteri Unicode, il che garantisce supporto nativo per qualsiasi lingua e insieme di simboli.

#### Creazione

```python
# Apici singoli e doppi sono equivalenti
s1 = 'Ciao mondo'
s2 = "Ciao mondo"

# Triple quotes per stringhe multilinea
s3 = """Questa e una stringa
che si estende su
piu righe"""

s4 = '''Anche questa
e multilinea'''

# Raw strings: i backslash non vengono interpretati come escape
percorso = r"C:\Users\nome\documenti"
pattern = r"\d+\.\d+"

# Byte strings per dati binari
b = b"dati binari"
```

#### Indicizzazione e Slicing

```python
testo = "Programmazione"

# Indicizzazione (base zero)
print(testo[0])     # 'P'
print(testo[-1])    # 'e' (indice negativo: dal fondo)
print(testo[-3])    # 'n'

# Slicing: [inizio:fine:passo]
print(testo[0:6])   # 'Progra' (fine escluso)
print(testo[6:])    # 'mmazione'
print(testo[:6])    # 'Progra'
print(testo[::2])   # 'Pormzoe' (ogni 2 caratteri)
print(testo[::-1])  # 'enoizammargorP' (stringa invertita)

# Slicing con passo negativo
print(testo[10:4:-1])  # 'izamm'
```

#### Metodi Principali

```python
testo = "  Ciao Mondo Python  "

# Trasformazione di caso
print(testo.upper())       # '  CIAO MONDO PYTHON  '
print(testo.lower())       # '  ciao mondo python  '
print(testo.title())       # '  Ciao Mondo Python  '
print(testo.capitalize())  # '  ciao mondo python  '
print(testo.swapcase())    # '  cIAO mONDO pYTHON  '

# Rimozione spazi
print(testo.strip())       # 'Ciao Mondo Python'
print(testo.lstrip())      # 'Ciao Mondo Python  '
print(testo.rstrip())      # '  Ciao Mondo Python'

# Suddivisione e unione
parole = "uno,due,tre,quattro".split(",")
print(parole)              # ['uno', 'due', 'tre', 'quattro']
print(" - ".join(parole))  # 'uno - due - tre - quattro'

# Ricerca e sostituzione
frase = "Python e un linguaggio potente"
print(frase.find("linguaggio"))     # 13 (indice della prima occorrenza)
print(frase.find("Java"))           # -1 (non trovato)
print(frase.count("e"))             # 2
print(frase.replace("potente", "versatile"))  # 'Python e un linguaggio versatile'

# Verifica prefisso e suffisso
print("documento.pdf".startswith("doc"))   # True
print("documento.pdf".endswith(".pdf"))    # True
print("12345".isdigit())                   # True
print("ciao".isalpha())                    # True

# Codifica
testo_utf8 = "caffe".encode("utf-8")      # b'caff\xc3\xa8'
print(testo_utf8.decode("utf-8"))          # 'caffe'
```

#### f-string (Formatted String Literals)

Introdotte con Python 3.6, le f-string rappresentano il modo piu leggibile e performante per formattare le stringhe:

```python
nome = "Marco"
eta = 28
altezza = 1.753

# Espressioni inline
print(f"Mi chiamo {nome} e ho {eta} anni.")
print(f"Tra 5 anni ne avro {eta + 5}.")
print(f"Nome in maiuscolo: {nome.upper()}")

# Specifiche di formattazione
print(f"Altezza: {altezza:.1f} m")          # 'Altezza: 1.8 m'
print(f"Percentuale: {0.856:.1%}")          # 'Percentuale: 85.6%'
print(f"Numero: {42:05d}")                  # 'Numero: 00042'
print(f"Allineamento: {'testo':>20}")       # allineato a destra su 20 caratteri
print(f"Allineamento: {'testo':^20}")       # centrato su 20 caratteri
print(f"Separatore migliaia: {1000000:,.2f}")  # '1,000,000.00'

# Debug con = (Python 3.8+)
x = 42
print(f"{x = }")           # 'x = 42'
print(f"{x * 2 = }")       # 'x * 2 = 84'

# Annidamento di espressioni
larghezza = 15
print(f"{'Python':*^{larghezza}}")  # '****Python*****'
```

#### Immutabilita delle Stringhe

Le stringhe sono **immutabili**: non e possibile modificare un singolo carattere in-place. Ogni operazione che sembra modificare una stringa in realta crea un nuovo oggetto stringa:

```python
s = "Python"
# s[0] = 'J'  # TypeError: 'str' object does not support item assignment

# Per "modificare" si crea una nuova stringa
s = 'J' + s[1:]  # 'Jython'
```

#### Approfondimento — Encoding, Decoding e il Modello str / bytes

In Python 3, `str` e una sequenza di **codepoint Unicode**, non di byte. I byte grezzi sono rappresentati dal tipo `bytes`. Questa separazione netta e una delle differenze fondamentali rispetto a Python 2 ed elimina un'intera categoria di bug legati alla codifica.

```python
# str -> bytes: encode()
testo = "caffe espresso"
utf8_bytes = testo.encode("utf-8")
print(utf8_bytes)           # b'caff\xc3\xa8 espresso'
print(type(utf8_bytes))     # <class 'bytes'>
print(len(testo))           # 14 (14 codepoint Unicode)
print(len(utf8_bytes))      # 15 (il carattere 'e' occupa 2 byte in UTF-8)

# bytes -> str: decode()
recuperato = utf8_bytes.decode("utf-8")
print(recuperato == testo)  # True

# Errori di codifica
try:
    "caffe".encode("ascii")
except UnicodeEncodeError as e:
    print(e)  # 'ascii' codec can't encode character '\xe8' in position 4

# Gestione degli errori di codifica
print("caffe".encode("ascii", errors="replace"))   # b'caff?'
print("caffe".encode("ascii", errors="ignore"))     # b'caff'
print("caffe".encode("ascii", errors="xmlcharrefreplace"))  # b'caff&#232;'

# Differenza fondamentale: operazioni su str vs bytes
testo_str = "ABC"
testo_bytes = b"ABC"
print(testo_str[0])         # 'A' (stringa di un carattere)
print(testo_bytes[0])       # 65  (intero — il valore del byte)

# bytes e bytearray
immutabile = b"dati"
mutabile = bytearray(b"dati")
mutabile[0] = ord('D')
print(mutabile)             # bytearray(b'Dati')

# Pratica comune: leggere un file binario e decodificare
from pathlib import Path
# contenuto = Path("file.txt").read_bytes().decode("utf-8")
```

Il consiglio operativo: specificare **sempre** `encoding="utf-8"` in `open()`, `encode()`, `decode()`, e in qualsiasi interfaccia che accetti una codifica. Non affidarsi mai al default di sistema (`locale.getpreferredencoding()`), che varia tra piattaforme.

Riferimento: https://docs.python.org/3/howto/unicode.html (consultato: 2026-05-23)

#### Approfondimento — f-string per il Debug e Formattazione Avanzata

La sintassi `f"{expr=}"` introdotta da Python 3.8 (PEP 572 / implementata nel frame delle f-string) stampa sia l'espressione sia il suo risultato. E uno strumento di debug rapido che sostituisce molte occorrenze di `print("variabile:", variabile)`.

```python
# Debug con = : mostra espressione E risultato
lista = [1, 2, 3]
print(f"{len(lista) = }")            # len(lista) = 3
print(f"{lista[::-1] = }")           # lista[::-1] = [3, 2, 1]

# Combinazione di = con format spec
import math
print(f"{math.pi = :.4f}")           # math.pi = 3.1416

# Conversione esplicita con !r, !s, !a
nome = "caffe"
print(f"{nome!r}")                    # 'caffe' (repr — con apici)
print(f"{nome!s}")                    # caffe   (str — senza apici)
print(f"{nome!a}")                    # 'caff\xe8' (ASCII safe)

# Formattazione di date
from datetime import datetime
adesso = datetime.now()
print(f"{adesso:%Y-%m-%d %H:%M}")    # 2026-05-23 14:30

# Formattazione di numeri con locale
valore = 1234567.89
print(f"{valore:,.2f}")               # 1,234,567.89
print(f"{valore:_,.2f}")              # 1_234_567.89 (con underscore)

# Multilinea con f-string (Python 3.12+: le f-string possono contenere
# espressioni multilinea e commenti — PEP 701)
risultato = f"Totale: {
    sum(range(10))  # somma dei primi 10 numeri
}"
print(risultato)                       # Totale: 45
```

Riferimento: PEP 498 — Literal String Interpolation, https://peps.python.org/pep-0498/ (consultato: 2026-05-23);
PEP 701 — Syntactic formalization of f-strings, https://peps.python.org/pep-0701/ (consultato: 2026-05-23)

#### Approfondimento — Metodi Stringa: Catalogo Esteso

Oltre ai metodi gia presentati, le stringhe offrono un repertorio completo per la manipolazione testuale.

```python
# --- Partizione e suddivisione avanzata ---
testo = "chiave=valore=extra"
print(testo.partition("="))           # ('chiave', '=', 'valore=extra')
print(testo.rpartition("="))          # ('chiave=valore', '=', 'extra')
print(testo.split("=", maxsplit=1))   # ['chiave', 'valore=extra']

# splitlines() gestisce tutti i terminatori di riga (\n, \r\n, \r)
multilinea = "riga1\nriga2\r\nriga3\rriga4"
print(multilinea.splitlines())        # ['riga1', 'riga2', 'riga3', 'riga4']

# --- Allineamento e padding ---
print("titolo".center(30, '-'))       # '------------titolo------------'
print("42".zfill(8))                  # '00000042'
print("hello".ljust(10, '.'))         # 'hello.....'
print("hello".rjust(10, '.'))         # '.....hello'

# --- Verifica del contenuto ---
print("abc123".isalnum())             # True  (alfanumerico)
print("   ".isspace())                # True  (solo spazi bianchi)
print("Titolo Frase".istitle())       # True  (ogni parola inizia con maiuscola)
print("MAIUSCOLO".isupper())          # True
print("minuscolo".islower())          # True
print("12345".isdecimal())            # True  (cifre decimali — sottoinsieme di isdigit)
print("identifier_1".isidentifier())  # True  (nome Python valido)

# --- Rimozione selettiva ---
print("###titolo###".strip("#"))      # 'titolo'
print("xxxhelloxxxworldxxx".removeprefix("xxx"))  # 'helloxxxworldxxx' (Python 3.9+)
print("xxxhelloxxxworldxxx".removesuffix("xxx"))  # 'xxxhelloxxxworld' (Python 3.9+)

# --- maketrans / translate per sostituzioni di massa ---
tabella = str.maketrans("aeiou", "12345")
print("ciao mondo".translate(tabella))  # 'c31o mondo'  (a->1, i->3, o->5)

# Rimozione di caratteri specifici
rimuovi = str.maketrans("", "", ".,;:!?")
print("Ciao! Come stai? Bene.".translate(rimuovi))  # 'Ciao Come stai Bene'
```

> **Nota:** la PEP 750 (Template Strings / t-string) prevista per Python 3.14 introdurra una nuova sintassi `t"..."` che produrra un oggetto `Template` invece di una stringa, consentendo sanitizzazione e trasformazione programmatica. Non e disponibile in Python 3.12.

### Booleani

Il tipo **bool** ha esattamente due valori: `True` e `False`. In Python, `bool` e una sottoclasse di `int`, quindi `True` equivale a `1` e `False` a `0`.

#### Valori Truthy e Falsy

In un contesto booleano, i seguenti valori sono considerati **falsy** (equivalenti a False):

```python
# Tutti i seguenti valutano a False
bool(False)      # False
bool(None)       # False
bool(0)          # False
bool(0.0)        # False
bool("")         # False (stringa vuota)
bool([])         # False (lista vuota)
bool(())         # False (tupla vuota)
bool({})         # False (dizionario vuoto)
bool(set())      # False (set vuoto)

# Tutto il resto e truthy
bool(1)          # True
bool(-1)         # True
bool("ciao")     # True
bool([0])        # True (lista non vuota, anche se contiene zero)
```

#### Il Meccanismo Interno — `__bool__` e `__len__`

Python determina la truthiness di un oggetto seguendo questa catena di priorita:

1. Se la classe definisce `__bool__`, il risultato di `__bool__()` decide.
2. Se `__bool__` non e definito ma `__len__` lo e, l'oggetto e falsy quando `__len__()` restituisce `0`.
3. Se nessuno dei due e definito, l'oggetto e sempre truthy.

```python
class Inventario:
    def __init__(self, articoli):
        self.articoli = articoli

    def __len__(self):
        return len(self.articoli)

    def __bool__(self):
        # Truthy solo se contiene articoli disponibili
        return any(a.disponibile for a in self.articoli)

class Articolo:
    def __init__(self, nome, disponibile=True):
        self.nome = nome
        self.disponibile = disponibile

# __len__ restituisce 2, ma __bool__ ha priorita
inv = Inventario([Articolo("A", False), Articolo("B", False)])
print(len(inv))     # 2
print(bool(inv))    # False — nessun articolo disponibile
```

Questa meccanica spiega perche contenitori vuoti sono falsy: la loro `__len__` restituisce `0`, e `bool` vi fa ricorso.

#### Operatori Logici

```python
a, b = True, False

print(a and b)   # False — AND logico
print(a or b)    # True  — OR logico
print(not a)     # False — negazione

# Short-circuit evaluation (valutazione a corto circuito)
# and restituisce il primo valore falsy, o l'ultimo se tutti truthy
print(1 and 2 and 3)    # 3
print(1 and 0 and 3)    # 0

# or restituisce il primo valore truthy, o l'ultimo se tutti falsy
print(0 or "" or "ciao")  # 'ciao'
print(0 or "" or [])       # []

# Utilizzo pratico del short-circuit
nome = input_utente or "Anonimo"  # default se input vuoto
```

#### Operatori di Confronto e Concatenazione

```python
x = 10

# Confronti standard
print(x == 10)   # True  — uguaglianza
print(x != 5)    # True  — disuguaglianza
print(x > 5)     # True  — maggiore
print(x >= 10)   # True  — maggiore o uguale
print(x < 20)    # True  — minore
print(x <= 10)   # True  — minore o uguale

# Concatenazione di confronti (caratteristica unica di Python)
print(1 < x < 20)       # True — equivalente a (1 < x) and (x < 20)
print(1 < x < 5)        # False
print(0 <= x <= 100)    # True

# Operatori di identita
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)    # True  — stesso valore
print(a is b)    # False — oggetti diversi in memoria
```

### None

`None` e il singleton che rappresenta l'assenza di valore in Python. E l'unica istanza del tipo `NoneType`.

```python
risultato = None

# Verifica con l'operatore is (non usare ==)
if risultato is None:
    print("Nessun risultato disponibile")

if risultato is not None:
    print(f"Risultato: {risultato}")

# Utilizzi comuni
def cerca_utente(id):
    """Restituisce None se l'utente non viene trovato."""
    utenti = {1: "Alice", 2: "Bob"}
    return utenti.get(id)  # get() restituisce None se la chiave manca

utente = cerca_utente(99)
if utente is None:
    print("Utente non trovato")

# None come valore di default per parametri mutabili
def aggiungi_elemento(elemento, lista=None):
    if lista is None:
        lista = []
    lista.append(elemento)
    return lista
```

---

## Variabili e Assegnazione

### Tipizzazione Dinamica

Python utilizza la **tipizzazione dinamica**: il tipo di una variabile viene determinato a runtime dal valore assegnato, non da una dichiarazione esplicita. Una variabile e semplicemente un nome (etichetta) che fa riferimento a un oggetto in memoria.

```python
x = 42          # x riferisce un oggetto int
print(type(x))  # <class 'int'>

x = "ciao"      # ora x riferisce un oggetto str
print(type(x))  # <class 'str'>

x = [1, 2, 3]   # ora x riferisce un oggetto list
print(type(x))  # <class 'list'>
```

### Convenzioni di Nomenclatura (PEP 8)

```python
# Variabili e funzioni: snake_case
nome_utente = "Mario"
contatore_elementi = 0

# Costanti: UPPER_SNAKE_CASE
MAX_TENTATIVI = 3
PI_GRECO = 3.14159

# Classi: PascalCase (CamelCase)
# class MioOggetto:
#     pass

# Nomi privati per convenzione: prefisso underscore
_variabile_interna = 42

# Name mangling: doppio underscore
# __variabile_privata (usato nelle classi)

# Nomi da evitare: l, O, I (confusi con 1 e 0)
# Non usare nomi di built-in come: list, str, dict, type, id
```

### Assegnazione Multipla e Augmented Assignment

```python
# Assegnazione multipla
a, b, c = 1, 2, 3

# Swap elegante senza variabile temporanea
a, b = b, a
print(a, b)  # 2 1

# Unpacking con asterisco
primo, *centro, ultimo = [1, 2, 3, 4, 5]
print(primo)   # 1
print(centro)  # [2, 3, 4]
print(ultimo)  # 5

# Assegnazione a catena
x = y = z = 0

# Augmented assignment (assegnazione aumentata)
n = 10
n += 5    # n = n + 5  -> 15
n -= 3    # n = n - 3  -> 12
n *= 2    # n = n * 2  -> 24
n //= 5   # n = n // 5 -> 4
n **= 3   # n = n ** 3 -> 64
n %= 10   # n = n % 10 -> 4

# Walrus operator := (Python 3.8+)
# Assegnazione all'interno di un'espressione
import re
if (match := re.search(r"\d+", "codice 42 errore")):
    print(f"Trovato numero: {match.group()}")  # 'Trovato numero: 42'
```

### Scope delle Variabili (Regola LEGB)

Python risolve i nomi delle variabili secondo la regola **LEGB**:

1. **Local** — scope della funzione corrente
2. **Enclosing** — scope delle funzioni contenenti (closures)
3. **Global** — scope del modulo
4. **Built-in** — scope dei nomi predefiniti di Python

```python
x = "globale"  # scope Global

def funzione_esterna():
    x = "enclosing"  # scope Enclosing

    def funzione_interna():
        x = "locale"  # scope Local
        print(x)       # 'locale'

    funzione_interna()
    print(x)           # 'enclosing'

funzione_esterna()
print(x)               # 'globale'
```

#### global e nonlocal

```python
contatore = 0

def incrementa():
    global contatore  # riferimento alla variabile globale
    contatore += 1

incrementa()
print(contatore)  # 1

def esterna():
    valore = 10

    def interna():
        nonlocal valore  # riferimento alla variabile dell'enclosing scope
        valore += 5

    interna()
    print(valore)  # 15

esterna()
```

L'uso di `global` e generalmente sconsigliato: e preferibile passare valori come parametri e restituirli come risultati delle funzioni.

#### Approfondimento — Closure su Variabili Mutabili

Le closure catturano il **riferimento** alla variabile dell'enclosing scope, non il suo valore al momento della definizione. Questo porta a un comportamento che sorprende frequentemente i programmatori:

```python
# Trappola classica: closure in un ciclo
funzioni = []
for i in range(5):
    funzioni.append(lambda: i)

# Tutte le lambda condividono lo STESSO riferimento a i
print([f() for f in funzioni])  # [4, 4, 4, 4, 4] — non [0, 1, 2, 3, 4]!

# Soluzione 1: argomento con valore di default (cattura il valore)
funzioni_corrette = []
for i in range(5):
    funzioni_corrette.append(lambda i=i: i)

print([f() for f in funzioni_corrette])  # [0, 1, 2, 3, 4]

# Soluzione 2: functools.partial
from functools import partial
funzioni_partial = [partial(lambda x: x, i) for i in range(5)]
print([f() for f in funzioni_partial])  # [0, 1, 2, 3, 4]

# Closure su strutture mutabili: attenzione alla modifica condivisa
def crea_accumulatore():
    risultati = []  # lista mutabile nell'enclosing scope

    def aggiungi(valore):
        risultati.append(valore)
        return risultati

    return aggiungi

acc = crea_accumulatore()
print(acc(1))  # [1]
print(acc(2))  # [1, 2] — la stessa lista e condivisa
print(acc(3))  # [1, 2, 3]
```

Questo comportamento e trattato in dettaglio nella sezione [Troubleshooting](#troubleshooting--errori-classici) (late binding closure).

#### Nota — `__slots__` e l'Ottimizzazione della Memoria

Le classi Python usano per default un dizionario `__dict__` per memorizzare gli attributi di ogni istanza. Il meccanismo `__slots__` sostituisce questo dizionario con una struttura piu compatta a dimensione fissa, riducendo il consumo di memoria del 30-50% per classi con molte istanze. `__slots__` vincola anche l'insieme degli attributi ammessi, prevenendo errori da typo.

Per un trattamento completo di `__slots__`, ereditarieta e le sue limitazioni si rimanda al **Modulo 02** — [Programmazione Orientata agli Oggetti](02-oop.md).

---

## Strutture Dati Built-in

### Liste

Le liste sono sequenze **mutabili** e **ordinate** che possono contenere elementi di tipi diversi. Sono la struttura dati piu versatile e utilizzata in Python.

```python
# Creazione
vuota = []
numeri = [1, 2, 3, 4, 5]
mista = [1, "due", 3.0, True, None]
da_range = list(range(10))  # [0, 1, 2, 3, ..., 9]
```

#### Metodi Fondamentali

```python
frutti = ["mela", "banana", "ciliegia"]

# Aggiunta di elementi
frutti.append("dattero")           # aggiunge alla fine
frutti.insert(1, "arancia")        # inserisce all'indice 1
frutti.extend(["fico", "uva"])     # estende con un iterabile

# Rimozione di elementi
frutti.remove("banana")            # rimuove la prima occorrenza
ultimo = frutti.pop()              # rimuove e restituisce l'ultimo
secondo = frutti.pop(1)            # rimuove e restituisce l'indice 1
# del frutti[0]                    # rimuove per indice senza restituire

# Ricerca
indice = frutti.index("ciliegia")  # indice della prima occorrenza
conteggio = frutti.count("mela")   # numero di occorrenze

# Ordinamento e inversione
numeri = [3, 1, 4, 1, 5, 9, 2]
numeri.sort()                      # ordinamento in-place: [1, 1, 2, 3, 4, 5, 9]
numeri.sort(reverse=True)          # ordine decrescente
numeri.reverse()                   # inverte l'ordine

# Copia
copia_superficiale = numeri.copy()  # equivalente a numeri[:]
import copy
copia_profonda = copy.deepcopy(numeri)  # copia ricorsiva degli oggetti annidati
```

#### List Comprehension

Le list comprehension offrono una sintassi concisa ed espressiva per creare liste:

```python
# Sintassi base: [espressione for elemento in iterabile]
quadrati = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# Con condizione di filtro
pari = [x for x in range(20) if x % 2 == 0]
# [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# Con trasformazione condizionale
classificazione = ["pari" if x % 2 == 0 else "dispari" for x in range(6)]
# ['pari', 'dispari', 'pari', 'dispari', 'pari', 'dispari']

# Comprehension annidata (prodotto cartesiano)
matrice = [(r, c) for r in range(3) for c in range(3)]
# [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)]

# Appiattimento di una lista di liste
lista_annidata = [[1, 2], [3, 4], [5, 6]]
piatta = [elem for sottolista in lista_annidata for elem in sottolista]
# [1, 2, 3, 4, 5, 6]
```

#### Approfondimento — Comprehension: Internals e Performance

Le comprehension (list, dict, set, generator) sono compilate in bytecode ottimizzato da CPython. L'interprete alloca la struttura risultante in un blocco unico e utilizza un'istruzione `LIST_APPEND` (o equivalente) che evita la ricerca ripetuta del metodo `.append()`. Il risultato e che una list comprehension e tipicamente **15-30% piu veloce** del ciclo `for` equivalente con `append`.

```python
import timeit

# Confronto di performance: list comprehension vs ciclo for
n = 100_000

# Ciclo for classico
def con_ciclo():
    risultato = []
    for i in range(n):
        risultato.append(i ** 2)
    return risultato

# List comprehension
def con_comprehension():
    return [i ** 2 for i in range(n)]

# Misura (risultati tipici su CPython 3.12)
# con_ciclo:          ~12.5 ms
# con_comprehension:  ~9.8 ms  (~22% piu veloce)
```

**Dict comprehension e set comprehension** seguono le stesse regole:

```python
# Dict comprehension
quadrati_dict = {x: x ** 2 for x in range(10)}
# {0: 0, 1: 1, 2: 4, ..., 9: 81}

# Set comprehension
vocali = {c for c in "ciao mondo" if c in "aeiou"}
# {'a', 'i', 'o'}

# Generator expression — parentesi tonde, nessuna lista in memoria
somma_quadrati = sum(x ** 2 for x in range(1_000_000))
# Calcola la somma senza creare la lista intermedia
```

**Generator expression vs list comprehension:** La generator expression (`(expr for ...)`) non materializza una lista in memoria. Produce valori uno alla volta (lazy evaluation), rendendola ideale quando l'iterabile e grande e serve solo un aggregato (sum, max, min, any, all) o un singolo passaggio.

```python
# Memoria: list comprehension alloca tutta la lista
lista = [x ** 2 for x in range(10_000_000)]   # ~80 MB di RAM

# Memoria: generator expression usa pochi byte
gen = (x ** 2 for x in range(10_000_000))      # ~120 byte
# I valori vengono calcolati al bisogno
print(sum(gen))  # somma calcolata senza allocare la lista
```

**Comprehension annidate — quando evitarle:** Se la comprehension contiene piu di due clausole `for` o condizioni complesse, la leggibilita crolla. La regola pratica: se non entra su una riga da 80 caratteri leggibile, usare un ciclo esplicito.

```python
# Accettabile: due clausole for, logica lineare
matrice = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
diagonale = [matrice[i][i] for i in range(len(matrice))]

# Troppo complesso: meglio un ciclo esplicito
# NON FARE:
# risultato = [f(x, y, z) for x in A for y in B if g(x, y) for z in C if h(y, z)]

# FARE INVECE:
risultato = []
for x in A:
    for y in B:
        if g(x, y):
            for z in C:
                if h(y, z):
                    risultato.append(f(x, y, z))
```

#### Ordinamento Avanzato

```python
# sorted() crea una nuova lista, .sort() modifica in-place
studenti = [("Alice", 88), ("Bob", 95), ("Clara", 82), ("Dario", 91)]

# Ordinamento per voto (secondo elemento della tupla)
per_voto = sorted(studenti, key=lambda s: s[1], reverse=True)
# [('Bob', 95), ('Dario', 91), ('Alice', 88), ('Clara', 82)]

# Ordinamento di stringhe per lunghezza
parole = ["Python", "e", "un", "linguaggio", "potente"]
per_lunghezza = sorted(parole, key=len)
# ['e', 'un', 'Python', 'potente', 'linguaggio']

# Ordinamento stabile con chiave multipla (usando operator)
from operator import itemgetter
dati = [("Roma", 3), ("Milano", 1), ("Roma", 1), ("Milano", 3)]
ordinati = sorted(dati, key=itemgetter(0, 1))
# [('Milano', 1), ('Milano', 3), ('Roma', 1), ('Roma', 3)]
```

### Tuple

Le tuple sono sequenze **immutabili** e ordinate. L'immutabilita le rende hashable (se contengono solo elementi hashable) e quindi utilizzabili come chiavi di dizionario.

```python
# Creazione
vuota = ()
singola = (42,)          # la virgola e obbligatoria per le tuple con un solo elemento
coordinate = (45.46, 9.19)
mista = (1, "due", 3.0)

# Packing e unpacking
punto = 10, 20, 30       # packing: le parentesi sono opzionali
x, y, z = punto          # unpacking

# Unpacking avanzato
primo, *resto = (1, 2, 3, 4, 5)
print(primo)  # 1
print(resto)  # [2, 3, 4, 5]

# Restituire valori multipli da una funzione
def min_max(numeri):
    return min(numeri), max(numeri)

minimo, massimo = min_max([3, 7, 1, 9, 4])
```

#### Named Tuple

Le named tuple combinano la leggerezza delle tuple con la leggibilita degli attributi con nome:

```python
from collections import namedtuple

# Definizione
Punto = namedtuple("Punto", ["x", "y", "z"])
Studente = namedtuple("Studente", "nome cognome voto")

# Utilizzo
p = Punto(1, 2, 3)
print(p.x, p.y, p.z)     # 1 2 3
print(p[0])               # 1 (accesso per indice funziona ancora)

s = Studente("Alice", "Rossi", 28)
print(f"{s.nome} {s.cognome}: {s.voto}")

# Conversione a dizionario
print(s._asdict())  # {'nome': 'Alice', 'cognome': 'Rossi', 'voto': 28}

# Creazione con sostituzione
s2 = s._replace(voto=30)
```

Le tuple sono ideali per rappresentare record di dati eterogenei, come risultati di funzioni con valori multipli, coordinate, e chiavi composite per dizionari.

### Dizionari

I dizionari sono collezioni **mutabili** di coppie chiave-valore, implementati come hash table. A partire da Python 3.7, mantengono l'ordine di inserimento come garanzia del linguaggio.

```python
# Creazione
vuoto = {}
persona = {"nome": "Alice", "eta": 30, "citta": "Roma"}
da_coppie = dict([("a", 1), ("b", 2)])
da_kwargs = dict(nome="Bob", eta=25)

# Accesso
print(persona["nome"])          # 'Alice'
# print(persona["telefono"])    # KeyError!
print(persona.get("telefono"))  # None (nessun errore)
print(persona.get("telefono", "N/D"))  # 'N/D' (valore di default)
```

#### Metodi Fondamentali

```python
dati = {"a": 1, "b": 2, "c": 3}

# Iterazione
for chiave in dati:                    # itera sulle chiavi
    print(chiave)

for chiave, valore in dati.items():    # itera su coppie (chiave, valore)
    print(f"{chiave}: {valore}")

print(list(dati.keys()))    # ['a', 'b', 'c']
print(list(dati.values()))  # [1, 2, 3]

# Modifica
dati.update({"d": 4, "e": 5})          # aggiunge/aggiorna multiple coppie
rimosso = dati.pop("c")                # rimuove e restituisce il valore
dati.setdefault("f", 6)                # inserisce solo se la chiave non esiste

# Verifica appartenenza
print("a" in dati)      # True
print("z" not in dati)  # True
```

#### Dictionary Comprehension

```python
# Sintassi: {chiave: valore for elemento in iterabile}
quadrati = {x: x**2 for x in range(6)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# Inversione chiavi-valori
originale = {"a": 1, "b": 2, "c": 3}
invertito = {v: k for k, v in originale.items()}
# {1: 'a', 2: 'b', 3: 'c'}

# Con filtro
parole = ["ciao", "mondo", "Python", "e", "fantastico"]
lunghezze = {p: len(p) for p in parole if len(p) > 3}
# {'ciao': 4, 'mondo': 5, 'Python': 6, 'fantastico': 10}
```

#### Strutture Avanzate dal Modulo collections

```python
from collections import defaultdict, OrderedDict, Counter

# defaultdict: valore di default automatico per chiavi mancanti
conteggio_lettere = defaultdict(int)
for lettera in "abracadabra":
    conteggio_lettere[lettera] += 1
# defaultdict(<class 'int'>, {'a': 5, 'b': 2, 'r': 2, 'c': 1, 'd': 1})

# Raggruppamento con defaultdict(list)
studenti = [("matematica", "Alice"), ("fisica", "Bob"), ("matematica", "Clara")]
per_materia = defaultdict(list)
for materia, nome in studenti:
    per_materia[materia].append(nome)
# {'matematica': ['Alice', 'Clara'], 'fisica': ['Bob']}

# Counter: conteggio di occorrenze
parole = ["mela", "banana", "mela", "ciliegia", "banana", "mela"]
contatore = Counter(parole)
print(contatore.most_common(2))  # [('mela', 3), ('banana', 2)]

# Operatori di merge per dizionari (Python 3.9+)
d1 = {"a": 1, "b": 2}
d2 = {"b": 3, "c": 4}
unione = d1 | d2         # {'a': 1, 'b': 3, 'c': 4} — d2 prevale
d1 |= d2                 # aggiornamento in-place
```

### Set

I set sono collezioni **mutabili** e **non ordinate** di elementi unici e hashable. Sono ottimizzati per operazioni di appartenenza e operazioni insiemistiche.

```python
# Creazione
vuoto = set()            # NON {} che crea un dizionario vuoto
numeri = {1, 2, 3, 4, 5}
da_lista = set([1, 2, 2, 3, 3, 3])  # {1, 2, 3} — duplicati rimossi

# Operazioni di base
numeri.add(6)            # aggiunge un elemento
numeri.discard(3)        # rimuove se presente (nessun errore se assente)
numeri.remove(4)         # rimuove (KeyError se assente)
elemento = numeri.pop()  # rimuove e restituisce un elemento arbitrario
```

#### Operazioni Insiemistiche

```python
a = {1, 2, 3, 4, 5}
b = {4, 5, 6, 7, 8}

# Unione
print(a | b)              # {1, 2, 3, 4, 5, 6, 7, 8}
print(a.union(b))         # equivalente

# Intersezione
print(a & b)              # {4, 5}
print(a.intersection(b))  # equivalente

# Differenza
print(a - b)              # {1, 2, 3} — elementi in a ma non in b
print(a.difference(b))    # equivalente

# Differenza simmetrica
print(a ^ b)                      # {1, 2, 3, 6, 7, 8}
print(a.symmetric_difference(b))  # equivalente

# Verifica sottoinsieme e sovrainsieme
print({1, 2}.issubset(a))     # True
print(a.issuperset({1, 2}))   # True
print(a.isdisjoint(b))        # False (hanno elementi in comune)
```

#### Set Comprehension e frozenset

```python
# Set comprehension
vocali_in_frase = {c.lower() for c in "Ciao Mondo" if c.lower() in "aeiou"}
# {'a', 'i', 'o'}

# frozenset: set immutabile, utilizzabile come chiave di dizionario
fs = frozenset([1, 2, 3])
dizionario = {fs: "valore"}  # possibile perche frozenset e hashable
```

I set sono particolarmente efficienti per la **deduplicazione** (`list(set(lista_con_duplicati))`) e per il **membership testing**: verificare se un elemento appartiene a un set e un'operazione O(1) in media, mentre per una lista e O(n).

```python
# Esempio pratico: trovare elementi comuni e unici tra due fonti dati
utenti_app_mobile = {"alice", "bob", "clara", "dario", "elena"}
utenti_app_web = {"bob", "dario", "franco", "giulia", "elena"}

# Utenti presenti su entrambe le piattaforme
su_entrambe = utenti_app_mobile & utenti_app_web
print(f"Su entrambe: {su_entrambe}")  # {'bob', 'dario', 'elena'}

# Utenti esclusivamente su mobile
solo_mobile = utenti_app_mobile - utenti_app_web
print(f"Solo mobile: {solo_mobile}")  # {'alice', 'clara'}

# Tutti gli utenti unici
tutti = utenti_app_mobile | utenti_app_web
print(f"Totale utenti unici: {len(tutti)}")  # 7
```

---

## Controllo di Flusso

### Condizionali

#### if / elif / else

```python
temperatura = 25

if temperatura < 0:
    print("Sotto zero: ghiaccio")
elif temperatura < 15:
    print("Freddo")
elif temperatura < 25:
    print("Mite")
elif temperatura < 35:
    print("Caldo")
else:
    print("Molto caldo")

# Operatore ternario (conditional expression)
stato = "maggiorenne" if eta >= 18 else "minorenne"

# Operatore ternario annidato (usare con moderazione per la leggibilita)
categoria = "bambino" if eta < 12 else "adolescente" if eta < 18 else "adulto"
```

#### match / case (Structural Pattern Matching, Python 3.10+)

Il pattern matching strutturale e una funzionalita potente che va ben oltre un semplice switch/case:

```python
def analizza_comando(comando):
    match comando.split():
        case ["quit"]:
            print("Uscita dal programma")
        case ["saluta", nome]:
            print(f"Ciao, {nome}!")
        case ["muovi", direzione, distanza]:
            print(f"Movimento: {direzione} per {distanza} unita")
        case ["imposta", chiave, "=", valore]:
            print(f"Impostazione {chiave} = {valore}")
        case _:
            print("Comando non riconosciuto")

analizza_comando("saluta Marco")    # 'Ciao, Marco!'
analizza_comando("muovi nord 10")   # 'Movimento: nord per 10 unita'

# Pattern matching con guard clause
def classifica_numero(n):
    match n:
        case x if x < 0:
            return "negativo"
        case 0:
            return "zero"
        case x if x % 2 == 0:
            return "pari positivo"
        case _:
            return "dispari positivo"

# Pattern matching su strutture dati
def processa_punto(punto):
    match punto:
        case (0, 0):
            print("Origine")
        case (x, 0):
            print(f"Sull'asse X a x={x}")
        case (0, y):
            print(f"Sull'asse Y a y={y}")
        case (x, y):
            print(f"Punto ({x}, {y})")
```

#### Approfondimento — Structural Pattern Matching Avanzato

Il pattern matching di Python 3.10+ (PEP 634) supporta pattern molto piu ricchi rispetto a quelli mostrati sopra. Ecco le categorie principali.

**OR Pattern (`|`):** permette di unificare piu pattern in un singolo ramo.

```python
def classifica_codice_http(codice):
    match codice:
        case 200 | 201 | 204:
            return "successo"
        case 301 | 302 | 307 | 308:
            return "redirect"
        case 400 | 403 | 404 | 422:
            return "errore client"
        case 500 | 502 | 503:
            return "errore server"
        case _:
            return f"codice non classificato: {codice}"
```

**Mapping Pattern:** fa match su dizionari, estraendo valori da chiavi specifiche.

```python
def processa_evento(evento):
    match evento:
        case {"tipo": "click", "x": x, "y": y}:
            print(f"Click a ({x}, {y})")
        case {"tipo": "keypress", "tasto": tasto, "modificatore": mod}:
            print(f"Tasto {tasto} con modificatore {mod}")
        case {"tipo": "keypress", "tasto": tasto}:
            print(f"Tasto {tasto} senza modificatore")
        case {"tipo": tipo, **resto}:
            print(f"Evento sconosciuto: {tipo}, dati extra: {resto}")

processa_evento({"tipo": "click", "x": 100, "y": 200, "timestamp": 12345})
# Click a (100, 200)  — la chiave "timestamp" e ignorata, non impedisce il match
```

**Class Pattern:** fa match su istanze di classi, destrutturando gli attributi.

```python
from dataclasses import dataclass

@dataclass
class Punto3D:
    x: float
    y: float
    z: float

@dataclass
class Cerchio:
    centro: Punto3D
    raggio: float

def descrivi_forma(forma):
    match forma:
        case Cerchio(centro=Punto3D(x=0, y=0, z=0), raggio=r):
            print(f"Cerchio centrato nell'origine con raggio {r}")
        case Cerchio(centro=Punto3D(x=cx, y=cy), raggio=r) if r > 100:
            print(f"Cerchio grande a ({cx}, {cy}) con raggio {r}")
        case Cerchio(raggio=r):
            print(f"Cerchio con raggio {r}")

descrivi_forma(Cerchio(Punto3D(0, 0, 0), 5.0))
# Cerchio centrato nell'origine con raggio 5.0
```

**Guard Clause con Walrus Operator:** il walrus operator `:=` non si usa direttamente come pattern, ma le guard clause (`if`) possono contenere espressioni complesse che lo sfruttano.

```python
import re

def analizza_input(testo):
    match testo.strip():
        case s if (m := re.match(r"(\d+)\s*\+\s*(\d+)", s)):
            a, b = int(m.group(1)), int(m.group(2))
            print(f"Somma: {a} + {b} = {a + b}")
        case s if (m := re.match(r"(\w+)\s*=\s*(.+)", s)):
            print(f"Assegnazione: {m.group(1)} = {m.group(2)}")
        case "":
            print("Input vuoto")
        case _:
            print(f"Input non riconosciuto: {testo!r}")

analizza_input("  42 + 8  ")   # Somma: 42 + 8 = 50
analizza_input("nome = Alice") # Assegnazione: nome = Alice
```

**Sequence Pattern con `*rest`:** cattura gli elementi rimanenti.

```python
def analizza_percorso(segmenti):
    match segmenti:
        case ["api", "v1", risorsa, *rest]:
            print(f"API v1, risorsa={risorsa}, sotto-percorso={rest}")
        case ["api", "v2", *rest]:
            print(f"API v2, percorso rimanente={rest}")
        case [singolo]:
            print(f"Percorso a singolo segmento: {singolo}")
        case []:
            print("Percorso vuoto (root)")

analizza_percorso(["api", "v1", "utenti", "42", "profilo"])
# API v1, risorsa=utenti, sotto-percorso=['42', 'profilo']
```

Riferimento: PEP 634 — Structural Pattern Matching: Specification, https://peps.python.org/pep-0634/ (consultato: 2026-05-23)

### Cicli

#### for loop

Il ciclo `for` in Python itera sempre su un **iterabile** (non utilizza un contatore come in C):

```python
# Iterazione su lista
frutti = ["mela", "banana", "ciliegia"]
for frutto in frutti:
    print(frutto)

# range(start, stop, step)
for i in range(5):           # 0, 1, 2, 3, 4
    print(i)

for i in range(2, 10, 3):   # 2, 5, 8
    print(i)

# enumerate: indice + valore
for indice, frutto in enumerate(frutti):
    print(f"{indice}: {frutto}")

for indice, frutto in enumerate(frutti, start=1):  # indice da 1
    print(f"{indice}. {frutto}")

# zip: iterazione parallela su piu iterabili
nomi = ["Alice", "Bob", "Clara"]
voti = [28, 30, 25]
for nome, voto in zip(nomi, voti):
    print(f"{nome}: {voto}")

# zip con lunghezze diverse (si ferma al piu corto)
# Per mantenere tutti: itertools.zip_longest
```

#### while loop

```python
# While con condizione
contatore = 0
while contatore < 5:
    print(contatore)
    contatore += 1

# While con input dell'utente
while (risposta := input("Continua? (s/n): ")) != "n":
    print(f"Hai risposto: {risposta}")
```

#### break, continue e else

```python
# break: esce dal ciclo
for n in range(100):
    if n > 5:
        break
    print(n)  # stampa 0, 1, 2, 3, 4, 5

# continue: salta all'iterazione successiva
for n in range(10):
    if n % 2 == 0:
        continue
    print(n)  # stampa solo i dispari: 1, 3, 5, 7, 9

# else: eseguito se il ciclo termina senza break
def trova_primo(n):
    """Verifica se n e primo."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            break
    else:
        # Eseguito solo se il for termina senza break
        return True
    return False
```

### Iterazione Avanzata

```python
numeri = [3, 1, 4, 1, 5, 9, 2, 6]

# sorted(): restituisce nuova lista ordinata
print(sorted(numeri))                      # [1, 1, 2, 3, 4, 5, 6, 9]
print(sorted(numeri, reverse=True))        # [9, 6, 5, 4, 3, 2, 1, 1]

# map(): applica una funzione a ogni elemento
quadrati = list(map(lambda x: x**2, numeri))
# [9, 1, 16, 1, 25, 81, 4, 36]

# filter(): filtra elementi secondo una condizione
maggiori_di_3 = list(filter(lambda x: x > 3, numeri))
# [4, 5, 9, 6]

# any() e all()
valori = [True, False, True, True]
print(any(valori))   # True  — almeno uno e True
print(all(valori))   # False — non tutti sono True

# Utilizzo pratico
numeri_lista = [2, 4, 6, 8]
print(all(n % 2 == 0 for n in numeri_lista))  # True — tutti pari
print(any(n > 7 for n in numeri_lista))        # True — almeno uno > 7
```

#### Approfondimento — Funzioni Built-in per l'Iterazione

Python fornisce un ricco set di funzioni built-in che operano su iterabili. Comprenderne il comportamento e fondamentale per scrivere codice idiomatico.

**`zip()` — Iterazione Parallela e Trucchi Avanzati**

```python
# zip base: si ferma al piu corto
nomi = ["Alice", "Bob", "Clara"]
eta = [30, 25, 28, 35]
for nome, e in zip(nomi, eta):
    print(f"{nome}: {e}")
# Alice: 30, Bob: 25, Clara: 28 — "35" ignorato

# strict=True (Python 3.10+): errore se le lunghezze differiscono
try:
    list(zip(nomi, eta, strict=True))
except ValueError as e:
    print(e)  # zip() has arguments with different lengths

# zip per trasporre una matrice
matrice = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
trasposta = list(zip(*matrice))
print(trasposta)  # [(1, 4, 7), (2, 5, 8), (3, 6, 9)]

# zip per creare dizionari
chiavi = ["nome", "eta", "citta"]
valori = ["Alice", 30, "Roma"]
dizionario = dict(zip(chiavi, valori))
print(dizionario)  # {'nome': 'Alice', 'eta': 30, 'citta': 'Roma'}

# "unzip" con zip(*iterabile)
coppie = [("a", 1), ("b", 2), ("c", 3)]
lettere, numeri = zip(*coppie)
print(lettere)  # ('a', 'b', 'c')
print(numeri)   # (1, 2, 3)
```

**`enumerate()` — Non Solo Indici**

```python
# Indice personalizzato con start
mesi = ["gennaio", "febbraio", "marzo"]
for n, mese in enumerate(mesi, start=1):
    print(f"Mese {n}: {mese}")

# enumerate restituisce un iteratore di tuple (indice, elemento)
# Utile per trovare posizioni specifiche
testo = "ciao mondo ciao tutti"
posizioni = [i for i, parola in enumerate(testo.split()) if parola == "ciao"]
print(posizioni)  # [0, 2]
```

**`sorted()` — Stabilita e Chiavi Complesse**

```python
# L'algoritmo di sorting di Python (Timsort) e STABILE:
# elementi con chiave uguale mantengono l'ordine originale
dati = [("Alice", "B"), ("Bob", "A"), ("Clara", "B"), ("Dario", "A")]
per_voto = sorted(dati, key=lambda x: x[1])
# [('Bob', 'A'), ('Dario', 'A'), ('Alice', 'B'), ('Clara', 'B')]
# Bob prima di Dario perche cosi erano nell'input (stabilita)

# Ordinamento case-insensitive
parole = ["banana", "Alice", "arancia", "Bob"]
print(sorted(parole, key=str.lower))
# ['Alice', 'arancia', 'banana', 'Bob']

# Ordinamento per chiave composita con tupla
studenti = [("Alice", 28, "Roma"), ("Bob", 30, "Milano"), ("Clara", 28, "Napoli")]
# Prima per voto (decrescente), poi per nome (crescente)
ordinati = sorted(studenti, key=lambda s: (-s[1], s[0]))
print(ordinati)
# [('Bob', 30, 'Milano'), ('Alice', 28, 'Roma'), ('Clara', 28, 'Napoli')]
```

**`map()` e `filter()` vs Comprehension**

```python
# map/filter sono piu funzionali, le comprehension piu pythonice
numeri = range(10)

# Equivalenti — la comprehension e generalmente preferita per leggibilita
quadrati_map = list(map(lambda x: x ** 2, numeri))
quadrati_comp = [x ** 2 for x in numeri]

pari_filter = list(filter(lambda x: x % 2 == 0, numeri))
pari_comp = [x for x in numeri if x % 2 == 0]

# map e utile quando hai gia una funzione con nome
valori_stringa = ["1", "2", "3", "4"]
valori_int = list(map(int, valori_stringa))  # piu pulito di [int(x) for x in ...]
```

**`any()` e `all()` — Short-circuit su Iterabili**

```python
# any() e all() cortocircuitano: si fermano appena conoscono la risposta
# any() restituisce True appena trova un elemento truthy
# all() restituisce False appena trova un elemento falsy

numeri_grandi = range(1_000_000)

# any si ferma al primo match, non itera tutto
print(any(n > 500 for n in numeri_grandi))  # True (si ferma a n=501)

# Verifica con all
password = "MyP@ssw0rd!"
requisiti = [
    any(c.isupper() for c in password),    # almeno una maiuscola
    any(c.islower() for c in password),    # almeno una minuscola
    any(c.isdigit() for c in password),    # almeno un numero
    len(password) >= 8,                     # lunghezza minima
]
print(all(requisiti))  # True — tutti i requisiti soddisfatti
```

#### itertools: Strumenti per l'Iterazione

```python
import itertools

# chain: concatena piu iterabili
uniti = list(itertools.chain([1, 2], [3, 4], [5, 6]))
# [1, 2, 3, 4, 5, 6]

# product: prodotto cartesiano
carte = list(itertools.product(["cuori", "quadri"], ["asso", "re"]))
# [('cuori', 'asso'), ('cuori', 're'), ('quadri', 'asso'), ('quadri', 're')]

# permutations e combinations
perm = list(itertools.permutations([1, 2, 3], 2))
# [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]

comb = list(itertools.combinations([1, 2, 3, 4], 2))
# [(1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]

# groupby: raggruppamento (richiede dati ordinati per la chiave)
dati = [("frutta", "mela"), ("frutta", "banana"), ("verdura", "carota"), ("verdura", "spinaci")]
for chiave, gruppo in itertools.groupby(dati, key=lambda x: x[0]):
    print(f"{chiave}: {[item[1] for item in gruppo]}")
# frutta: ['mela', 'banana']
# verdura: ['carota', 'spinaci']

# islice: slicing su iteratori (lazy)
primi_5_pari = list(itertools.islice((x for x in range(100) if x % 2 == 0), 5))
# [0, 2, 4, 6, 8]

# accumulate: somme parziali cumulative
cumulativa = list(itertools.accumulate([1, 2, 3, 4, 5]))
# [1, 3, 6, 10, 15]
```

---

## Funzioni

### Definizione e Parametri

Le funzioni in Python sono oggetti di prima classe: possono essere assegnate a variabili, passate come argomenti e restituite da altre funzioni.

```python
def saluta(nome, titolo="Sig."):
    """Restituisce un saluto formale.

    Args:
        nome: Il nome della persona da salutare.
        titolo: Il titolo da usare (default: "Sig.").

    Returns:
        Una stringa con il saluto formattato.
    """
    return f"Buongiorno, {titolo} {nome}!"

# Chiamata con argomenti posizionali e keyword
print(saluta("Rossi"))                    # 'Buongiorno, Sig. Rossi!'
print(saluta("Bianchi", titolo="Dott."))  # 'Buongiorno, Dott. Bianchi!'
```

#### Tipi di Parametri

```python
# *args: numero variabile di argomenti posizionali (raccolti in tupla)
def somma(*numeri):
    return sum(numeri)

print(somma(1, 2, 3, 4))  # 10

# **kwargs: numero variabile di argomenti keyword (raccolti in dizionario)
def crea_profilo(**kwargs):
    for chiave, valore in kwargs.items():
        print(f"{chiave}: {valore}")

crea_profilo(nome="Alice", eta=30, citta="Roma")

# Combinazione completa di parametri
def funzione_completa(pos1, pos2, /, norm1, norm2, *, kw1, kw2="default"):
    """
    pos1, pos2:   solo posizionali (prima di /)
    norm1, norm2: posizionali o keyword
    kw1, kw2:     solo keyword (dopo *)
    """
    pass

# Unpacking nella chiamata
args = [1, 2, 3]
kwargs = {"chiave": "valore"}
funzione(*args, **kwargs)
```

#### Approfondimento — Firme di Funzione: `/`, `*`, PEP 3102

La sintassi completa delle firme Python offre un controllo granulare su come gli argomenti vengono passati.

**Parametri solo-posizionali (`/`)** — introdotti formalmente dalla PEP 570 (Python 3.8). Il separatore `/` indica che tutti i parametri alla sua sinistra possono essere passati solo per posizione, non per nome.

```python
def potenza(base, esponente, /):
    """base e esponente DEVONO essere passati per posizione."""
    return base ** esponente

potenza(2, 10)              # OK: 1024
# potenza(base=2, esponente=10)  # TypeError!

# Caso d'uso: evitare che il nome del parametro diventi parte dell'API pubblica
def crea_range(stop, /, *, step=1):
    """stop e posizionale, step e solo keyword."""
    return list(range(0, stop, step))

crea_range(10, step=2)      # OK: [0, 2, 4, 6, 8]
```

**Parametri solo-keyword (`*`)** — introdotti dalla PEP 3102 (Python 3.0). Tutto cio che segue `*` nella firma deve essere passato per nome.

```python
def connetti(host, porta, *, timeout=30, ssl=False, retry=3):
    """host e porta posizionali; timeout, ssl, retry solo keyword."""
    print(f"Connessione a {host}:{porta} (timeout={timeout}, ssl={ssl})")

connetti("localhost", 5432, timeout=10, ssl=True)  # OK
# connetti("localhost", 5432, 10, True)  # TypeError!
# Obbliga l'esplicitezza: il chiamante deve nominare i parametri
```

**Schema completo e ordine obbligatorio:**

```
def f(pos_only, /, pos_or_kw, *, kw_only, **kwargs):
          ^           ^           ^          ^
    solo posiz.   normale    solo keyword  cattura resto

Ordine nella firma:
1. parametri solo-posizionali
2. /
3. parametri normali (posizionali o keyword)
4. *args (se presente)
5. * (se *args non c'e, come separatore)
6. parametri solo-keyword
7. **kwargs
```

```python
# Esempio reale dalla libreria standard: dict.pop
# dict.pop(key, default=<sentinel>, /)
# key e default sono solo posizionali — non si puo scrivere dict.pop(key=x)

# Firma massimale con tutti gli elementi
def api_call(metodo, url, /, dati=None, *args, timeout=30, headers=None, **opzioni):
    print(f"{metodo} {url}")
    print(f"dati={dati}, args={args}")
    print(f"timeout={timeout}, headers={headers}")
    print(f"opzioni extra={opzioni}")

api_call("GET", "/api/utenti", None, "extra1", timeout=5, verify=True)
```

Riferimento: PEP 570 — Python Positional-Only Parameters, https://peps.python.org/pep-0570/ (consultato: 2026-05-23);
PEP 3102 — Keyword-Only Arguments, https://peps.python.org/pep-3102/ (consultato: 2026-05-23)

#### Valori di Ritorno

```python
# Restituzione multipla (in realta restituisce una tupla)
def analizza_testo(testo):
    parole = testo.split()
    return len(parole), len(testo), testo.upper()

n_parole, n_caratteri, maiuscolo = analizza_testo("ciao mondo")

# Funzioni senza return esplicito restituiscono None
def procedura(messaggio):
    print(messaggio)
    # return implicito: None

risultato = procedura("test")
print(risultato)  # None
```

### Lambda

Le funzioni lambda sono funzioni anonime limitate a una singola espressione:

```python
# Sintassi: lambda parametri: espressione
quadrato = lambda x: x ** 2
somma = lambda a, b: a + b

print(quadrato(5))   # 25
print(somma(3, 4))   # 7

# Utilizzo tipico: funzioni come argomento
studenti = [("Alice", 88), ("Bob", 95), ("Clara", 82)]
ordinati = sorted(studenti, key=lambda s: s[1])

# Con condizionale
classifica = lambda x: "positivo" if x > 0 else "negativo" if x < 0 else "zero"
```

### Funzioni di Ordine Superiore

Le funzioni di ordine superiore accettano funzioni come parametri o le restituiscono:

```python
def applica_operazione(lista, operazione):
    """Applica una funzione a ogni elemento della lista."""
    return [operazione(elemento) for elemento in lista]

numeri = [1, 2, 3, 4, 5]
print(applica_operazione(numeri, lambda x: x ** 2))     # [1, 4, 9, 16, 25]
print(applica_operazione(numeri, lambda x: x * 10))     # [10, 20, 30, 40, 50]

# Funzione che restituisce una funzione
def crea_moltiplicatore(fattore):
    def moltiplicatore(x):
        return x * fattore
    return moltiplicatore

doppio = crea_moltiplicatore(2)
triplo = crea_moltiplicatore(3)
print(doppio(5))   # 10
print(triplo(5))   # 15
```

### Closure

Una closure e una funzione interna che ricorda l'ambiente della funzione esterna anche dopo che quest'ultima ha terminato l'esecuzione:

```python
def contatore():
    """Crea un contatore con stato interno."""
    conteggio = 0

    def incrementa():
        nonlocal conteggio
        conteggio += 1
        return conteggio

    return incrementa

c = contatore()
print(c())  # 1
print(c())  # 2
print(c())  # 3
# conteggio e incapsulato: non accessibile dall'esterno
```

### Ricorsione con Memoizzazione

```python
# Ricorsione classica: calcolo di Fibonacci
def fibonacci_naive(n):
    """Calcolo naive — complessita esponenziale O(2^n)."""
    if n <= 1:
        return n
    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)

# Con memoizzazione manuale
def fibonacci_memo(n, cache={}):
    """Calcolo con memoizzazione — complessita O(n)."""
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    cache[n] = fibonacci_memo(n - 1, cache) + fibonacci_memo(n - 2, cache)
    return cache[n]

# Con functools.lru_cache (approccio consigliato)
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    """Calcolo con cache automatica tramite decoratore."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(100))  # 354224848179261915075 — calcolato istantaneamente
```

E importante notare che Python impone un limite di profondita della ricorsione (default: 1000), consultabile e modificabile tramite `sys.getrecursionlimit()` e `sys.setrecursionlimit()`. Per algoritmi che richiedono ricorsione profonda, e spesso preferibile convertire la soluzione ricorsiva in una iterativa oppure utilizzare tecniche come la tail-call optimization manuale tramite cicli while.

---

## Moduli e Pacchetti

### Sistema di Import

```python
# Import del modulo intero
import os
print(os.getcwd())

# Import con alias
import numpy as np
import pandas as pd

# Import selettivo
from pathlib import Path
from collections import defaultdict, Counter

# Import di tutto (sconsigliato: inquina il namespace)
# from os import *

# Import relativo (all'interno di un pacchetto)
# from . import modulo_fratello
# from ..pacchetto_padre import qualcosa
```

### Il Pattern \_\_name\_\_ == '\_\_main\_\_'

Questo pattern consente a un file di comportarsi sia come modulo importabile sia come script eseguibile:

```python
# file: utilita.py

def calcola_media(numeri):
    """Calcola la media aritmetica di una lista di numeri."""
    if not numeri:
        return 0
    return sum(numeri) / len(numeri)

def calcola_mediana(numeri):
    """Calcola la mediana di una lista di numeri."""
    ordinati = sorted(numeri)
    n = len(ordinati)
    if n % 2 == 0:
        return (ordinati[n // 2 - 1] + ordinati[n // 2]) / 2
    return ordinati[n // 2]

if __name__ == "__main__":
    # Questo codice viene eseguito solo quando il file e lanciato come script
    # Non viene eseguito quando il modulo viene importato
    dati = [4, 8, 15, 16, 23, 42]
    print(f"Media: {calcola_media(dati)}")
    print(f"Mediana: {calcola_mediana(dati)}")
```

### Struttura di un Pacchetto

Un pacchetto Python e una directory contenente un file `__init__.py` (che puo essere vuoto):

```
mio_progetto/
    __init__.py
    core/
        __init__.py
        motore.py
        configurazione.py
    utilita/
        __init__.py
        helpers.py
        validatori.py
    test/
        __init__.py
        test_motore.py
        test_helpers.py
```

Il file `__init__.py` puo esporre un'API pubblica del pacchetto:

```python
# mio_progetto/core/__init__.py
from .motore import Motore
from .configurazione import carica_config

__all__ = ["Motore", "carica_config"]
```

### Libreria Standard — Moduli Essenziali

Python dispone di una libreria standard estremamente ricca, spesso definita "batteries included":

```python
# os e sys: interazione con il sistema operativo
import os
import sys
print(os.getcwd())                    # directory corrente
print(os.listdir("."))                # contenuto directory
print(sys.argv)                       # argomenti da linea di comando
print(sys.version)                    # versione Python

# pathlib: gestione dei percorsi (approccio moderno, preferito a os.path)
from pathlib import Path
percorso = Path.home() / "documenti" / "file.txt"
print(percorso.exists())
print(percorso.suffix)                # '.txt'
print(percorso.stem)                  # 'file'

# datetime: date e orari
from datetime import datetime, timedelta
adesso = datetime.now()
print(adesso.strftime("%d/%m/%Y %H:%M"))  # '27/03/2026 14:30'
tra_una_settimana = adesso + timedelta(weeks=1)

# json: serializzazione dati
import json
dati = {"nome": "Alice", "eta": 30, "attivo": True}
testo_json = json.dumps(dati, indent=2, ensure_ascii=False)
dati_recuperati = json.loads(testo_json)

# csv: file tabellari
import csv
# Lettura
with open("dati.csv", "r") as f:
    lettore = csv.DictReader(f)
    for riga in lettore:
        print(riga)

# re: espressioni regolari
import re
testo = "Il mio numero e 333-1234567"
match = re.search(r"(\d{3})-(\d{7})", testo)
if match:
    print(f"Prefisso: {match.group(1)}, Numero: {match.group(2)}")

# collections: strutture dati specializzate (gia visto defaultdict, Counter)
# itertools: strumenti per iteratori (gia trattato)

# functools: strumenti per funzioni
from functools import reduce, partial
somma_totale = reduce(lambda a, b: a + b, [1, 2, 3, 4, 5])  # 15
doppio_print = partial(print, end="\n\n")  # print con doppio a capo

# pathlib: percorsi come oggetti (introdotto in Python 3.4)
from pathlib import Path
progetto = Path.cwd() / "src" / "main.py"
print(progetto.parent)    # directory genitore
print(progetto.name)      # 'main.py'
for py_file in Path(".").rglob("*.py"):  # ricerca ricorsiva
    print(py_file)
```

La scelta di quale modulo della libreria standard utilizzare dipende dal contesto. Per la gestione dei percorsi, `pathlib` e oggi preferito rispetto a `os.path` per la sua interfaccia orientata agli oggetti e la maggiore leggibilita. Per la serializzazione dei dati, `json` e il formato universale per le API web, mentre `csv` resta lo standard per l'interscambio con fogli di calcolo e database. Il modulo `re` per le espressioni regolari e indispensabile per il parsing avanzato di testo, ma per pattern semplici i metodi delle stringhe (`split`, `replace`, `startswith`) sono piu leggibili e performanti.

---

## Input/Output Base

### La Funzione print()

```python
# Parametri di print: sep, end, file, flush
print("Python", "e", "potente")                       # Python e potente
print("Python", "e", "potente", sep=" - ")             # Python - e - potente
print("Prima riga", end=" | ")
print("Stessa riga")                                    # Prima riga | Stessa riga

# Stampa su file
with open("output.txt", "w") as f:
    print("Scritto su file", file=f)

# Stampa formattata
nome = "Mondo"
print(f"Ciao, {nome}!")                                 # f-string (consigliato)
print("Ciao, {}!".format(nome))                         # str.format()
print("Ciao, %s!" % nome)                               # old-style (sconsigliato)

# Tabella formattata
intestazioni = ["Nome", "Voto", "Media"]
print(f"{'Nome':<15} {'Voto':>5} {'Media':>8}")
print("-" * 30)
dati_studenti = [("Alice Rossi", 28, 27.5), ("Bob Verdi", 30, 29.0)]
for nome, voto, media in dati_studenti:
    print(f"{nome:<15} {voto:>5} {media:>8.1f}")
```

### La Funzione input()

```python
# Input di base (restituisce sempre una stringa)
nome = input("Come ti chiami? ")
print(f"Ciao, {nome}!")

# Conversione del tipo
eta = int(input("Quanti anni hai? "))
altezza = float(input("Quanto sei alto (in metri)? "))

# Input con validazione
while True:
    try:
        numero = int(input("Inserisci un numero intero: "))
        break
    except ValueError:
        print("Input non valido. Riprova.")

# Input multiplo su una riga
valori = input("Inserisci numeri separati da spazio: ").split()
numeri = [int(v) for v in valori]
```

### Operazioni sui File

```python
# Scrittura
with open("esempio.txt", "w", encoding="utf-8") as f:
    f.write("Prima riga\n")
    f.write("Seconda riga\n")
    f.writelines(["Terza riga\n", "Quarta riga\n"])

# Lettura completa
with open("esempio.txt", "r", encoding="utf-8") as f:
    contenuto = f.read()        # stringa con tutto il contenuto
    print(contenuto)

# Lettura riga per riga (efficiente per file grandi)
with open("esempio.txt", "r", encoding="utf-8") as f:
    for riga in f:              # iterazione lazy — una riga alla volta in memoria
        print(riga.strip())

# Lettura in lista di righe
with open("esempio.txt", "r", encoding="utf-8") as f:
    righe = f.readlines()       # lista di stringhe

# Append (aggiunta in coda)
with open("esempio.txt", "a", encoding="utf-8") as f:
    f.write("Riga aggiunta\n")

# Context manager (with statement)
# Garantisce la chiusura automatica del file, anche in caso di eccezione.
# E SEMPRE preferibile rispetto all'uso manuale di open()/close().
```

Il **context manager** (istruzione `with`) e fondamentale per la gestione sicura delle risorse. Garantisce che il file venga chiuso correttamente anche se si verifica un'eccezione durante l'elaborazione, eliminando il rischio di file handle orfani e perdita di dati.

Le modalita principali di apertura sono: `"r"` (lettura, default), `"w"` (scrittura, sovrascrive), `"a"` (append), `"x"` (creazione esclusiva, errore se esiste), `"b"` (modalita binaria, combinabile con le precedenti). Specificare sempre `encoding="utf-8"` per i file di testo garantisce la portabilita tra sistemi operativi diversi.

Un approccio moderno per la gestione dei file e l'utilizzo di `pathlib.Path`, che offre metodi integrati per la lettura e la scrittura:

```python
from pathlib import Path

percorso = Path("dati") / "configurazione.txt"

# Scrittura rapida
percorso.write_text("chiave=valore\n", encoding="utf-8")

# Lettura rapida
contenuto = percorso.read_text(encoding="utf-8")

# Verifica esistenza e creazione directory
percorso.parent.mkdir(parents=True, exist_ok=True)

# Lettura binaria (per immagini, file compressi, etc.)
dati_binari = Path("immagine.png").read_bytes()
```

Per file di grandi dimensioni e consigliabile evitare `read()` e `readlines()` che caricano l'intero file in memoria. L'iterazione diretta sull'oggetto file (`for riga in f`) e il generatore piu efficiente: legge una riga alla volta, mantenendo il consumo di memoria costante indipendentemente dalla dimensione del file.

---

## Best Practices

1. **Seguire PEP 8 rigorosamente.** Utilizzare 4 spazi per livello di indentazione (mai tab), limitare le righe a 79-99 caratteri, inserire due righe vuote prima delle definizioni di funzioni e classi a livello di modulo. Adottare un formatter automatico come `black` o `ruff format` per garantire la coerenza senza sforzo manuale.

2. **Usare nomi significativi e coerenti.** Le variabili e le funzioni devono rivelare la propria intenzione: `calcola_sconto_totale()` e infinitamente piu chiaro di `calc()`. Seguire le convenzioni: `snake_case` per variabili e funzioni, `PascalCase` per le classi, `UPPER_SNAKE_CASE` per le costanti. Evitare nomi a singola lettera tranne che in cicli brevi (`i`, `j`) o in comprehension dove il contesto e evidente.

3. **Preferire le idiomi pythonici.** Utilizzare list comprehension al posto dei cicli for con append; usare `enumerate()` invece di gestire manualmente un indice; usare `zip()` per iterare su piu sequenze in parallelo; usare l'unpacking delle tuple. Scrivere codice "pythonico" significa sfruttare le costruzioni native del linguaggio piuttosto che replicare pattern di altri linguaggi.

4. **Scrivere docstring per ogni funzione e classe pubblica.** Adottare uno stile consistente (Google style, NumPy style o reStructuredText) e documentare almeno i parametri, i valori di ritorno e le eccezioni sollevate. Le docstring sono accessibili tramite `help()` e sono lo strumento primario di documentazione in Python.

5. **Gestire le risorse con i context manager.** Usare sempre l'istruzione `with` per file, connessioni di rete, lock e qualsiasi risorsa che richieda una fase di cleanup. Questo garantisce il rilascio corretto delle risorse anche in presenza di eccezioni, ed e piu leggibile del pattern try/finally.

6. **Evitare oggetti mutabili come valori di default dei parametri.** Non scrivere mai `def f(lista=[])`: il valore di default viene creato una sola volta alla definizione della funzione e condiviso tra tutte le chiamate. Usare `None` come sentinella e creare l'oggetto nel corpo della funzione: `def f(lista=None): if lista is None: lista = []`.

7. **Preferire la composizione di funzioni piccole e mirate.** Ogni funzione dovrebbe svolgere un unico compito ben definito (principio di responsabilita singola). Funzioni corte (idealmente sotto le 20 righe) sono piu facili da testare, riusare e comprendere. Se una funzione richiede troppi commenti per spiegare i suoi passaggi interni, probabilmente va suddivisa in funzioni piu piccole.

8. **Usare le eccezioni in modo appropriato.** Catturare eccezioni specifiche, mai un generico `except:` o `except Exception:` senza una ragione precisa. Il pattern EAFP (Easier to Ask Forgiveness than Permission) e preferito rispetto a LBYL (Look Before You Leap) in Python: provare l'operazione e gestire l'eccezione e spesso piu chiaro e piu efficiente che verificare preventivamente ogni condizione.

9. **Sfruttare i type hints per documentare e validare.** A partire da Python 3.5+ le type annotations migliorano la leggibilita e consentono analisi statica con strumenti come `mypy`. Scrivere `def calcola_media(numeri: list[float]) -> float:` rende immediatamente chiaro il contratto della funzione senza dover consultare la documentazione.

10. **Strutturare il codice come pacchetti fin dall'inizio.** Anche per progetti piccoli, organizzare il codice in moduli separati per responsabilita (logica di business, accesso ai dati, utilita, configurazione) facilita la manutenzione e la crescita del progetto. Usare sempre il pattern `if __name__ == "__main__"` per rendere i moduli importabili e al contempo eseguibili come script autonomi.

---

## Modello di Dati Python

### Tutto e un Oggetto

In Python, **ogni valore e un oggetto**. Numeri interi, stringhe, funzioni, classi, moduli — ogni entita possiede tre proprietà fondamentali:

1. **Identita** (`id()`) — l'indirizzo di memoria dell'oggetto, immutabile per tutta la sua vita.
2. **Tipo** (`type()`) — la classe dell'oggetto, che determina le operazioni ammesse.
3. **Valore** — il contenuto effettivo dell'oggetto, che puo essere mutabile o immutabile.

```python
x = 42
print(id(x))      # es. 140234567890  — indirizzo di memoria
print(type(x))     # <class 'int'>

# Anche le funzioni sono oggetti
def saluta():
    """Una funzione e un oggetto di tipo function."""
    return "ciao"

print(type(saluta))            # <class 'function'>
print(id(saluta))              # un indirizzo di memoria
print(saluta.__doc__)          # 'Una funzione e un oggetto di tipo function.'
print(saluta.__name__)         # 'saluta'

# Le classi stesse sono oggetti (istanze di type)
print(type(int))               # <class 'type'>
print(type(type))              # <class 'type'> — type e metaclasse di se stessa

# Ispezione degli attributi di un oggetto
print(dir(42))                 # lista di tutti i metodi di un intero
print((42).__add__(8))         # 50 — l'operatore + e un metodo!
```

### isinstance vs type()

Per verificare il tipo di un oggetto, preferire **sempre** `isinstance()` rispetto a `type() ==`. La differenza e fondamentale: `isinstance` rispetta l'ereditarieta, `type` no.

```python
# bool e sottoclasse di int
valore = True

print(type(valore) == int)       # False — type e esattamente bool, non int
print(type(valore) == bool)      # True
print(isinstance(valore, int))   # True  — rispetta l'ereditarieta
print(isinstance(valore, bool))  # True

# isinstance accetta anche tuple di tipi (OR logico)
def processa(dato):
    if isinstance(dato, (int, float)):
        return dato * 2
    elif isinstance(dato, str):
        return dato.upper()
    elif isinstance(dato, (list, tuple)):
        return len(dato)
    else:
        raise TypeError(f"Tipo non supportato: {type(dato).__name__}")

print(processa(3.14))      # 6.28
print(processa("ciao"))    # 'CIAO'
print(processa([1, 2]))    # 2
```

### Attributi Speciali degli Oggetti

Ogni oggetto Python espone attributi speciali (dunder attributes) che permettono introspezione:

```python
class Punto:
    """Rappresenta un punto nel piano."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Punto(3, 4)

# Attributi di introspezione
print(p.__class__)          # <class '__main__.Punto'>
print(p.__class__.__name__) # 'Punto'
print(p.__dict__)           # {'x': 3, 'y': 4} — attributi dell'istanza
print(Punto.__doc__)        # 'Rappresenta un punto nel piano.'
print(Punto.__module__)     # '__main__'
print(Punto.__bases__)      # (<class 'object'>,) — classi genitore

# hasattr, getattr, setattr: accesso dinamico agli attributi
print(hasattr(p, 'x'))              # True
print(getattr(p, 'z', 'default'))   # 'default' (attributo non esiste)
setattr(p, 'z', 5)                  # aggiunge dinamicamente l'attributo z
print(p.z)                          # 5
```

Per un approfondimento completo su classi, ereditarieta, dunder method e il protocollo descriptor si veda il **Modulo 02** — [Programmazione Orientata agli Oggetti](02-oop.md).

---

## Modello di Memoria

### Semantica a Riferimento

Le variabili Python non "contengono" valori: sono **nomi** (etichette) che **riferiscono** oggetti in memoria. L'assegnazione `a = b` non copia l'oggetto: fa puntare `a` allo stesso oggetto a cui punta `b`.

```python
# Due nomi, un oggetto
a = [1, 2, 3]
b = a              # b punta allo STESSO oggetto di a
b.append(4)
print(a)            # [1, 2, 3, 4] — anche a vede la modifica!
print(a is b)       # True — stessa identita

# Assegnazione crea un nuovo binding, non una copia
a = [1, 2, 3]
b = a
a = [10, 20]        # a ora punta a un NUOVO oggetto
print(b)            # [1, 2, 3] — b punta ancora al vecchio
print(a is b)       # False
```

### Copia Superficiale vs Copia Profonda

Quando serve una copia indipendente di un oggetto mutabile, la distinzione tra copia superficiale e profonda e critica.

```python
import copy

# --- Copia superficiale (shallow copy) ---
# Copia l'oggetto esterno, ma gli elementi interni restano condivisi
originale = [[1, 2], [3, 4], [5, 6]]
superficiale = copy.copy(originale)   # equivalente a originale[:] per le liste

superficiale.append([7, 8])
print(originale)                       # [[1, 2], [3, 4], [5, 6]] — non toccato

superficiale[0].append(999)
print(originale)                       # [[1, 2, 999], [3, 4], [5, 6]] — MODIFICATO!
# Le sottoliste sono condivise

# --- Copia profonda (deep copy) ---
# Copia ricorsivamente tutti gli oggetti annidati
originale = [[1, 2], [3, 4], [5, 6]]
profonda = copy.deepcopy(originale)

profonda[0].append(999)
print(originale)                       # [[1, 2], [3, 4], [5, 6]] — intatto

# Metodi per la copia superficiale delle strutture built-in
lista_copia = lista.copy()             # metodo .copy()
lista_copia = lista[:]                 # slicing completo
lista_copia = list(lista)              # costruttore
dict_copia = dizionario.copy()         # metodo .copy()
set_copia = insieme.copy()             # metodo .copy()
```

### La Trappola dell'Argomento Mutabile di Default

Questo e probabilmente l'errore piu insidioso di Python per i principianti: un argomento con valore di default mutabile viene creato **una sola volta** alla definizione della funzione, non ad ogni chiamata.

```python
# ===== SBAGLIATO =====
def aggiungi_elemento(elemento, lista=[]):
    lista.append(elemento)
    return lista

print(aggiungi_elemento("a"))    # ['a']       — sembra corretto
print(aggiungi_elemento("b"))    # ['a', 'b']  — BUG: la lista persiste!
print(aggiungi_elemento("c"))    # ['a', 'b', 'c']

# Ispezione: il default e un singolo oggetto condiviso
print(aggiungi_elemento.__defaults__)  # (['a', 'b', 'c'],)

# ===== CORRETTO =====
def aggiungi_elemento(elemento, lista=None):
    if lista is None:
        lista = []       # nuova lista ad ogni chiamata
    lista.append(elemento)
    return lista

print(aggiungi_elemento("a"))    # ['a']
print(aggiungi_elemento("b"))    # ['b'] — corretto: lista indipendente
```

Questo pattern si applica a **qualsiasi** oggetto mutabile: liste, dizionari, set, oggetti personalizzati. L'unico default sicuro e `None` (o un altro immutabile).

### Garbage Collection e Reference Counting

CPython gestisce la memoria attraverso due meccanismi complementari: il **reference counting** e il **garbage collector ciclico**. Ogni oggetto Python mantiene un contatore di riferimenti (`ob_refcnt` nella struttura C interna). Quando un nuovo nome punta all'oggetto il contatore aumenta; quando un nome viene riassegnato, esce dallo scope, o viene esplicitamente cancellato con `del`, il contatore diminuisce. Quando il contatore raggiunge zero l'oggetto viene deallocato immediatamente — questo e il motivo per cui CPython ha un comportamento deterministico nella deallocazione, a differenza di implementazioni con garbage collector non-deterministico come PyPy o Jython.

```python
import sys

a = [1, 2, 3]
print(sys.getrefcount(a))  # 2 — 'a' + argomento temporaneo di getrefcount

b = a
print(sys.getrefcount(a))  # 3 — 'a', 'b', argomento temporaneo

del b
print(sys.getrefcount(a))  # 2 — solo 'a' + argomento temporaneo
```

Il reference counting da solo non gestisce i **cicli di riferimento**: se l'oggetto A referenzia B e B referenzia A, entrambi i contatori restano a 1 anche quando nessun nome esterno li raggiunge. Per questo esiste il modulo `gc` (garbage collector ciclico), che periodicamente ispeziona gli oggetti alla ricerca di cicli non raggiungibili e li dealloca.

```python
import gc

# Ispezionare lo stato del garbage collector
print(gc.get_threshold())  # (700, 10, 10) — soglie per le tre generazioni
print(gc.get_count())      # (N, M, K) — contatori correnti per generazione

# Il GC opera su tre generazioni:
# Gen 0: oggetti appena creati — ispezionata frequentemente
# Gen 1: oggetti sopravvissuti a una raccolta Gen 0
# Gen 2: oggetti sopravvissuti a una raccolta Gen 1 — ispezionata raramente

# Forzare una raccolta manuale (raramente necessario):
raccolti = gc.collect()
print(f"Oggetti ciclici raccolti: {raccolti}")
```

La strategia generazionale si basa sull'**ipotesi generazionale**: la maggior parte degli oggetti ha vita breve. Ispezionando frequentemente la generazione 0 e raramente la generazione 2, il GC minimizza l'overhead. La soglia `(700, 10, 10)` significa: la Gen 0 viene ispezionata quando il numero di allocazioni meno le deallocazioni supera 700; la Gen 1 viene ispezionata ogni 10 raccolte di Gen 0; la Gen 2 ogni 10 raccolte di Gen 1.

### Interning e Ottimizzazioni dell'Interprete

CPython implementa diverse ottimizzazioni trasparenti che possono sorprendere chi non le conosce. La piu nota e l'**interning delle stringhe**: stringhe che assomigliano a identificatori Python (lettere, cifre, underscore) vengono automaticamente interned — cioe condividono lo stesso oggetto in memoria. Questo accelera il confronto tramite `is` (confronto di puntatori) anziche confronto carattere per carattere.

```python
# Stringhe interned automaticamente (sembrano identificatori):
a = "hello_world"
b = "hello_world"
print(a is b)  # True — stesso oggetto in memoria

# Stringhe NON interned (contengono spazi o caratteri speciali):
c = "hello world"
d = "hello world"
print(c is d)  # False (o True, dipende dall'implementazione e dal contesto)
# NON fare affidamento su questo comportamento — usare sempre ==

# Interning esplicito:
import sys
e = sys.intern("stringa con spazi")
f = sys.intern("stringa con spazi")
print(e is f)  # True — forzato dall'interning esplicito
```

L'interning esplicito tramite `sys.intern()` e utile quando si gestiscono grandi quantita di stringhe ripetute (parsing di log, processamento di dati tabellari) per ridurre il consumo di memoria e accelerare i confronti. Tuttavia e un'ottimizzazione che ha senso solo quando misurata: in scenari normali il costo dell'interning puo superare il beneficio.

Un'altra ottimizzazione di CPython e il **small integer pool**: gli interi da -5 a 256 sono pre-allocati all'avvio dell'interprete e condivisi tra tutte le parti del programma. Questo spiega un comportamento spesso citato:

```python
a = 256
b = 256
print(a is b)   # True — stesso oggetto dalla pool

a = 257
b = 257
print(a is b)   # False (in REPL interattivo) — oggetti diversi
# ATTENZIONE: in uno script .py, il compilatore puo ottimizzare
# costanti nello stesso blocco di codice, rendendo il risultato True.
# Non fare MAI affidamento su "is" per confronti di valori.
```

Infine, il **peephole optimizer** (e dalla 3.8, l'AST optimizer) applica ottimizzazioni al bytecode compilato: constant folding (`3 * 4` diventa `12` a compile-time), dead code elimination, e ottimizzazione di sequenze di confronto. Queste ottimizzazioni sono trasparenti al programmatore ma contribuiscono a rendere Python piu veloce senza sacrificare la leggibilita del codice sorgente.

### Bytecode e il Modulo `dis`

Il modulo `dis` (disassembler) permette di ispezionare il bytecode generato dal compilatore CPython. Questo e utile per comprendere come il linguaggio traduce le espressioni ad alto livello in istruzioni per la macchina virtuale Python e per confrontare l'efficienza di costrutti alternativi.

```python
import dis

def somma_lista(n):
    return sum(range(n))

dis.dis(somma_lista)
# Output:
#   0 RESUME                   0
#   2 LOAD_GLOBAL              0 (sum)
#  12 LOAD_GLOBAL              2 (range)
#  22 LOAD_FAST                0 (n)
#  24 CALL                     1
#  32 CALL                     1
#  40 RETURN_VALUE

# Confronto: list comprehension vs generator expression
dis.dis(compile("[x*2 for x in range(10)]", "<string>", "eval"))
dis.dis(compile("list(x*2 for x in range(10))", "<string>", "eval"))
```

Ogni istruzione bytecode ha un opcode numerico e opzionalmente un argomento. Le istruzioni `LOAD_FAST` sono piu veloci di `LOAD_GLOBAL` perche accedono a un array indicizzato anziche a un dizionario — questo e il motivo per cui le variabili locali in Python sono piu veloci delle globali. La comprensione del bytecode non e necessaria per scrivere buon codice Python, ma diventa preziosa per l'ottimizzazione di hot path e per il debugging di comportamenti inattesi del compilatore.

---

## Lo Zen di Python — PEP 20

Lo Zen di Python e l'insieme di 19 aforismi (su 20 previsti — l'ultimo non e mai stato scritto) che sintetizzano la filosofia del linguaggio. Si accede digitando `import this` nel REPL. Di seguito, ogni principio e accompagnato da un'applicazione pratica.

```
>>> import this
The Zen of Python, by Tim Peters
```

**1. Beautiful is better than ugly.**
Scegliere nomi espressivi, allineamento coerente, struttura visiva pulita. Il codice e letto molto piu spesso di quanto sia scritto.

**2. Explicit is better than implicit.**
Preferire `if x is not None:` a `if x:` quando il test specifico e per None. Dichiarare i tipi con type hints. Non affidarsi a effetti collaterali nascosti.

**3. Simple is better than complex.**
Se un dizionario basta, non creare una classe. Se un ciclo for e chiaro, non usare reduce con una lambda incomprensibile.

**4. Complex is better than complicated.**
Quando la complessita e necessaria (pattern matching, decoratori, metaclassi), e accettabile — purche non diventi contorta. Complessita ben strutturata e meglio di semplicita caotica.

**5. Flat is better than nested.**
Limitare l'annidamento a 3-4 livelli. Usare early return per eliminare i rami else. Estrarre funzioni helper per le clausole interne.

```python
# Troppo annidato
def processa(dati):
    if dati:
        if isinstance(dati, list):
            for item in dati:
                if item.attivo:
                    elabora(item)

# Piatto — early return + guard clause
def processa(dati):
    if not dati:
        return
    if not isinstance(dati, list):
        return
    for item in dati:
        if not item.attivo:
            continue
        elabora(item)
```

**6. Sparse is better than dense.**
Una riga per concetto. Non comprimere tre operazioni in un'unica riga. Le righe vuote separano i blocchi logici.

**7. Readability counts.**
Il principio cardine. Ogni scelta stilistica — nomi, struttura, commenti — serve la leggibilita.

**8. Special cases aren't special enough to break the rules. / 9. Although practicality beats purity.**
Seguire le convenzioni tranne quando romperle produce codice oggettivamente piu chiaro o piu sicuro. La pragmaticita e un valore.

**10. Errors should never pass silently. / 11. Unless explicitly silenced.**
Mai `except:` vuoto. Mai `except Exception: pass`. Se si silenzia un errore, deve essere con un commento che spiega perche.

```python
# SBAGLIATO
try:
    risultato = operazione()
except:
    pass

# CORRETTO
try:
    risultato = operazione()
except OperazioneNonDisponibile:
    # Fallback intenzionale: l'operazione e opzionale in questo contesto
    risultato = valore_default
```

**12. In the face of ambiguity, refuse the temptation to guess.**
Se il significato di un parametro non e chiaro, usare argomenti keyword. Se il tipo di ritorno e ambiguo, annotarlo.

**13. There should be one-- and preferably only one --obvious way to do it.**
Python non e Perl. Preferire l'idioma canonico: f-string per la formattazione, `pathlib` per i percorsi, `with` per le risorse.

**14. Although that way may not be obvious at first unless you're Dutch.**
Un riferimento umoristico a Guido van Rossum (olandese). L'"ovvio" richiede esperienza.

**15. Now is better than never. / 16. Although never is often better than *right* now.**
Scrivere il codice quando serve, ma non affrettarsi con implementazioni premature che poi diventano debito tecnico.

**17. If the implementation is hard to explain, it's a bad idea. / 18. If the implementation is easy to explain, it may be a good idea.**
Il test del "puoi spiegarlo a un collega in 30 secondi?" e un buon indicatore di qualita progettuale.

**19. Namespaces are one honking great idea -- let's do more of those!**
Usare moduli, classi e funzioni per creare spazi di nomi. Evitare `from modulo import *`. Preferire `import modulo` per mantenere esplicita la provenienza di ogni nome.

Riferimento: PEP 20 — The Zen of Python, https://peps.python.org/pep-0020/ (consultato: 2026-05-23)

---

## Confronti e Identita

### `is` vs `==`: Identita vs Uguaglianza

L'operatore `==` confronta i **valori** (invoca `__eq__`), mentre `is` confronta le **identita** (verifica se due nomi puntano allo stesso oggetto in memoria tramite `id()`).

```python
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(a == b)     # True  — stesso valore
print(a is b)     # False — oggetti diversi
print(a is c)     # True  — stesso oggetto

# REGOLA: usare "is" SOLO per confronti con singleton
# I singleton di Python sono: None, True, False, NotImplemented, Ellipsis
if risultato is None:       # CORRETTO
    pass
if risultato == None:       # SBAGLIATO — invoca __eq__, puo essere sovrascritto
    pass
```

### Confronti Concatenati

Python supporta la concatenazione dei confronti, una caratteristica sintattica unica:

```python
x = 15
# Concatenati: piu leggibili e piu efficienti
print(0 < x < 100)            # True
print(10 <= x <= 20)          # True
print(0 < x < 10 < 100)       # False (x non e < 10)

# Equivalente espanso — ogni variabile e valutata UNA sola volta nel concatenato
# 0 < x < 100  equivale a  (0 < x) and (x < 100)
# ma nel concatenato, x e valutato una volta sola (rilevante se x e un'espressione costosa)
```

### Il Contratto `__eq__` / `__hash__`

Se una classe sovrascrive `__eq__`, **deve** sovrascrivere anche `__hash__` per mantenere la coerenza. La regola e: se `a == b`, allora `hash(a) == hash(b)`. La violazione di questo contratto produce comportamenti imprevedibili con dizionari e set.

```python
class Moneta:
    def __init__(self, valore, valuta):
        self.valore = valore
        self.valuta = valuta

    def __eq__(self, altra):
        if not isinstance(altra, Moneta):
            return NotImplemented
        return self.valore == altra.valore and self.valuta == altra.valuta

    def __hash__(self):
        # OBBLIGATORIO se __eq__ e definito
        return hash((self.valore, self.valuta))

    def __repr__(self):
        return f"Moneta({self.valore}, '{self.valuta}')"

m1 = Moneta(100, "EUR")
m2 = Moneta(100, "EUR")
print(m1 == m2)                    # True
print(hash(m1) == hash(m2))       # True — contratto rispettato
print({m1, m2})                    # {Moneta(100, 'EUR')} — deduplicati nel set

# ATTENZIONE: se __eq__ e definito ma __hash__ NO, la classe diventa unhashable
# e non puo essere usata come chiave di dict o elemento di set
```

Se una classe e mutabile e definisce `__eq__`, la scelta sicura e impostare `__hash__ = None` esplicitamente per renderla unhashable (Python lo fa automaticamente se definisci `__eq__` senza `__hash__`).

Riferimento: https://docs.python.org/3/reference/datamodel.html#object.__hash__ (consultato: 2026-05-23)

---

## Unpacking Approfondito

### Extended Unpacking con `*`

L'operatore `*` nell'unpacking (PEP 3132) cattura gli elementi "rimanenti" in una lista:

```python
# Cattura testa e coda
primo, *resto = [1, 2, 3, 4, 5]
print(primo)    # 1
print(resto)    # [2, 3, 4, 5]

# Cattura testa, corpo e coda
primo, *centro, ultimo = [1, 2, 3, 4, 5]
print(primo)    # 1
print(centro)   # [2, 3, 4]
print(ultimo)   # 5

# Con zero elementi nel mezzo
a, *b, c = [1, 2]
print(a)        # 1
print(b)        # []
print(c)        # 2

# Scartare esplicitamente con _
primo, *_, ultimo = range(100)
print(primo)    # 0
print(ultimo)   # 99
```

### Unpacking Annidato

Python supporta l'unpacking di strutture annidate, destrutturando in un unico passo:

```python
# Unpacking di tuple annidate
dati = ("Alice", (30, "Roma"), [95, 88, 92])
nome, (eta, citta), voti = dati
print(nome)     # 'Alice'
print(eta)      # 30
print(citta)    # 'Roma'
print(voti)     # [95, 88, 92]

# In un ciclo for
studenti = [
    ("Alice", (28, "Roma")),
    ("Bob", (30, "Milano")),
    ("Clara", (25, "Napoli")),
]
for nome, (voto, citta) in studenti:
    print(f"{nome} da {citta} con voto {voto}")

# Unpacking di dizionario con **
defaults = {"timeout": 30, "retry": 3, "ssl": True}
custom = {"timeout": 10, "debug": True}
config = {**defaults, **custom}
print(config)   # {'timeout': 10, 'retry': 3, 'ssl': True, 'debug': True}
# Le chiavi in custom sovrascrivono quelle in defaults
```

### Lo Swap Idiom

Lo swap di Python e un caso speciale di unpacking di tupla che funziona senza variabile temporanea:

```python
a, b = 1, 2
a, b = b, a       # il lato destro crea una tupla (2, 1), poi viene decomposta
print(a, b)        # 2 1

# Funziona anche con piu variabili (rotazione)
a, b, c = 1, 2, 3
a, b, c = c, a, b
print(a, b, c)     # 3 1 2

# Internamente: Python valuta TUTTO il lato destro prima di assegnare
# Equivalente a: temp = (b, a); a = temp[0]; b = temp[1]
```

Riferimento: PEP 3132 — Extended Iterable Unpacking, https://peps.python.org/pep-3132/ (consultato: 2026-05-23)

---

## Troubleshooting — Errori Classici

### 1. Mutable Default Argument

**Sintomo:** Una funzione accumula risultati tra chiamate successive.

```python
# BUG
def registra(evento, log=[]):
    log.append(evento)
    return log

print(registra("login"))     # ['login']
print(registra("logout"))    # ['login', 'logout'] — inaspettato!

# FIX
def registra(evento, log=None):
    if log is None:
        log = []
    log.append(evento)
    return log
```

**Perche accade:** I valori di default vengono valutati una sola volta, al momento della definizione della funzione (quando l'istruzione `def` viene eseguita). L'oggetto default e memorizzato in `funzione.__defaults__` e condiviso tra tutte le chiamate.

### 2. Late Binding Closure

**Sintomo:** Tutte le funzioni create in un ciclo restituiscono lo stesso valore.

```python
# BUG
moltiplicatori = []
for i in range(5):
    moltiplicatori.append(lambda x: x * i)

print(moltiplicatori[0](10))  # 40 — non 0!
print(moltiplicatori[1](10))  # 40 — non 10!
print(moltiplicatori[4](10))  # 40

# FIX 1: argomento con default (cattura il valore corrente)
moltiplicatori = []
for i in range(5):
    moltiplicatori.append(lambda x, i=i: x * i)

print(moltiplicatori[0](10))  # 0
print(moltiplicatori[2](10))  # 20

# FIX 2: usare functools.partial
from functools import partial
def moltiplica(x, fattore):
    return x * fattore

moltiplicatori = [partial(moltiplica, fattore=i) for i in range(5)]
```

**Perche accade:** Le closure catturano il **riferimento** alla variabile `i`, non il suo valore. Quando la lambda viene eseguita, `i` ha gia raggiunto il valore finale del ciclo (4). Il parametro con default `i=i` risolve perche il default e valutato al momento della definizione della lambda.

### 3. Integer Caching (Small Integer Pool)

**Sintomo:** `is` funziona per numeri piccoli ma fallisce per numeri grandi.

```python
# CPython mantiene un pool di interi nell'intervallo [-5, 256]
a = 256
b = 256
print(a is b)   # True — stesso oggetto dal pool

a = 257
b = 257
print(a is b)   # False (in genere) — oggetti diversi
                # Nota: nel REPL, a volte True per ottimizzazioni del compilatore

# REGOLA: NON usare mai "is" per confrontare valori numerici
# Usare SEMPRE ==
print(a == b)   # True — sempre corretto
```

**Perche accade:** CPython pre-alloca gli interi da -5 a 256 in un array fisso all'avvio dell'interprete. Ogni occorrenza di un intero in questo range punta allo stesso oggetto. Fuori da questo range, CPython crea nuovi oggetti. Il comportamento e un dettaglio implementativo di CPython e **non** e garantito dalla specifica del linguaggio.

### 4. Modifica di una Lista durante l'Iterazione

**Sintomo:** Elementi saltati o `IndexError` durante l'iterazione.

```python
# BUG: rimuovere elementi da una lista mentre la si itera
numeri = [1, 2, 3, 4, 5, 6]
for n in numeri:
    if n % 2 == 0:
        numeri.remove(n)   # modifica la lista durante l'iterazione
print(numeri)               # [1, 3, 5] a volte, ma comportamento non garantito

# FIX 1: iterare su una copia
numeri = [1, 2, 3, 4, 5, 6]
for n in numeri[:]:          # numeri[:] crea una copia superficiale
    if n % 2 == 0:
        numeri.remove(n)

# FIX 2: list comprehension (idiomatico)
numeri = [1, 2, 3, 4, 5, 6]
numeri = [n for n in numeri if n % 2 != 0]
print(numeri)               # [1, 3, 5]
```

### 5. Confusione tra `=` e `==` negli if

**Sintomo:** `SyntaxError` o assegnazione indesiderata.

```python
# In Python, l'assegnazione in un if causa SyntaxError (protezione del linguaggio)
# if x = 10:     # SyntaxError!
# if x == 10:    # Corretto: confronto

# Il walrus operator := e l'UNICO modo legittimo di assegnare in un'espressione
if (n := len("ciao")) > 3:
    print(f"Lunghezza {n} > 3")
```

---

## Esercizi

### Domande Aperte

1. **Spiega la differenza tra `is` e `==` in Python.** Fornisci un esempio con oggetti mutabili dove i due operatori restituiscono risultati diversi e spiega perche. In quali casi e corretto usare `is`?

2. **Descrivi il meccanismo LEGB di risoluzione dei nomi in Python.** Crea un esempio con una funzione annidata che dimostri tutti e quattro i livelli di scope (Local, Enclosing, Global, Built-in) e spiega come `nonlocal` modifica il comportamento.

3. **Perche il valore di default mutabile e considerato un anti-pattern in Python?** Spiega il meccanismo interno che causa il bug, mostra il pattern corretto con `None`, e indica dove CPython memorizza i valori di default di una funzione.

4. **Confronta list comprehension e generator expression.** Descrivi le differenze in termini di sintassi, consumo di memoria e casi d'uso ideali. Quando preferiresti un generatore a una lista?

5. **Illustra il contratto tra `__eq__` e `__hash__`.** Spiega cosa succede quando una classe definisce `__eq__` ma non `__hash__`, e perche questo e problematico per dizionari e set. Mostra un esempio di implementazione corretta.

### Vero o Falso

1. In Python, `bool` e una sottoclasse di `int`, e `True + True` restituisce `2`. **(Vero)**

2. La list comprehension `[x for x in range(10)]` e l'espressione `list(range(10))` producono lo stesso risultato, ma la list comprehension e sempre piu veloce. **(Falso)** — `list(range(10))` e piu veloce perche usa un'implementazione C interna senza overhead di bytecode Python.

3. In CPython, gli interi nell'intervallo [-5, 256] sono cachati e condividono la stessa identita, quindi `a = 100; b = 100; a is b` restituisce sempre `True`. **(Vero)** — Ma questo e un dettaglio implementativo di CPython, non una garanzia del linguaggio.

4. Lo structural pattern matching (`match/case`) introdotto in Python 3.10 e equivalente a uno `switch/case` di C o Java. **(Falso)** — Il pattern matching di Python e molto piu potente: supporta destrutturazione, guard clause, class pattern, mapping pattern e OR pattern.

5. L'operatore `//` (floor division) restituisce sempre un intero. **(Falso)** — Se uno degli operandi e float, il risultato e un float arrotondato verso il basso: `7.0 // 2` restituisce `3.0`, non `3`.

### Coding Challenge

**Sfida 1 — Analizzatore di Frequenze:**
Scrivi una funzione `analizza_frequenze(testo: str) -> dict[str, int]` che riceve un testo e restituisce un dizionario con la frequenza di ogni parola (case-insensitive), ordinato dalla piu frequente alla meno frequente. Usa solo strutture dati built-in (niente `Counter`).

**Sfida 2 — Validatore di Password:**
Scrivi una funzione `valida_password(password: str) -> tuple[bool, list[str]]` che verifica che una password soddisfi tutti i seguenti requisiti: almeno 8 caratteri, almeno una maiuscola, almeno una minuscola, almeno un numero, almeno un carattere speciale. Restituisci un booleano e la lista dei requisiti non soddisfatti.

**Sfida 3 — Appiattimento Ricorsivo:**
Scrivi una funzione `appiattisci(struttura)` che riceve una struttura annidata arbitrariamente (liste dentro liste dentro liste...) e restituisce una lista piatta con tutti gli elementi non-lista. Esempio: `appiattisci([1, [2, [3, 4], 5], [6, 7]])` → `[1, 2, 3, 4, 5, 6, 7]`.

**Sfida 4 — Pattern Matching Pratico:**
Usando `match/case`, scrivi un interprete per un mini-calcolatore che accetta comandi nella forma `"3 + 5"`, `"10 * 2"`, `"quit"`, `"help"`, e `"set variabile = valore"`. Gestisci i casi non riconosciuti con un messaggio di errore.

**Sfida 5 — Decorator con Memoria:**
Scrivi un decoratore `conta_chiamate` che tiene traccia del numero di volte in cui una funzione e stata invocata. La funzione decorata deve esporre un attributo `.chiamate` con il conteggio corrente. Usa una closure per lo stato.

---

## Letture e Riferimenti

### Fonti Primarie

- **Tutorial Python ufficiale** — https://docs.python.org/3/tutorial/index.html (consultato: 2026-05-23). Introduzione completa al linguaggio scritta dal core team. Copre tutti gli argomenti di questo modulo.

- **Python Language Reference — Data Model** — https://docs.python.org/3/reference/datamodel.html (consultato: 2026-05-23). Documentazione tecnica sul modello a oggetti, dunder method, e il protocollo dei tipi.

- **Built-in Types** — https://docs.python.org/3/library/stdtypes.html (consultato: 2026-05-23). Riferimento completo per int, float, str, list, dict, set, tuple, bytes.

- **Built-in Functions** — https://docs.python.org/3/library/functions.html (consultato: 2026-05-23). Documentazione di tutte le funzioni built-in (zip, enumerate, map, filter, sorted, ecc.).

### PEP di Riferimento

- **PEP 8 — Style Guide for Python Code** — https://peps.python.org/pep-0008/ (consultato: 2026-05-23). La guida di stile ufficiale.

- **PEP 20 — The Zen of Python** — https://peps.python.org/pep-0020/ (consultato: 2026-05-23). I principi filosofici del linguaggio.

- **PEP 498 — Literal String Interpolation** — https://peps.python.org/pep-0498/ (consultato: 2026-05-23). Specifica delle f-string.

- **PEP 634 — Structural Pattern Matching** — https://peps.python.org/pep-0634/ (consultato: 2026-05-23). Specifica del match/case.

- **PEP 570 — Python Positional-Only Parameters** — https://peps.python.org/pep-0570/ (consultato: 2026-05-23). Il separatore `/` nelle firme.

- **PEP 3102 — Keyword-Only Arguments** — https://peps.python.org/pep-3102/ (consultato: 2026-05-23). Il separatore `*` nelle firme.

- **PEP 3132 — Extended Iterable Unpacking** — https://peps.python.org/pep-3132/ (consultato: 2026-05-23). L'operatore `*` nell'unpacking.

- **PEP 701 — Syntactic formalization of f-strings** — https://peps.python.org/pep-0701/ (consultato: 2026-05-23). Nuova grammatica delle f-string in Python 3.12.

### Testi Consigliati

- **"Fluent Python" di Luciano Ramalho (2a edizione, O'Reilly)** — Trattamento approfondito del data model, delle sequenze e delle funzioni come oggetti di prima classe.

- **"Python Cookbook" di David Beazley e Brian K. Jones (3a edizione, O'Reilly)** — Ricettario pratico con soluzioni idiomatiche a problemi comuni.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| Classi, ereditarieta, `__slots__`, dunder method | 02 | [02-oop.md](02-oop.md) |
| `deque`, `heapq`, `OrderedDict`, `ChainMap`, `Fraction` | 03 | [03-strutture-dati-avanzate.md](03-strutture-dati-avanzate.md) |
| Decoratori, generatori, `yield`, context manager | 04 | [04-decoratori-generatori-context-manager.md](04-decoratori-generatori-context-manager.md) |
| Type hints, `mypy`, `Protocol`, generics | 09 | [09-type-hints-e-mypy.md](09-type-hints-e-mypy.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **bytecode** | Rappresentazione intermedia del codice Python compilata da CPython, memorizzata nei file `.pyc`. Viene eseguita dalla Python Virtual Machine. |
| **closure** | Funzione interna che cattura e mantiene un riferimento a variabili del suo enclosing scope, anche dopo che la funzione esterna ha terminato l'esecuzione. |
| **comprehension** | Sintassi concisa per creare liste (`[...]`), dizionari (`{k: v ...}`), set (`{...}`) o generatori (`(...)`) tramite un'espressione iterativa inline. |
| **CPython** | L'implementazione di riferimento del linguaggio Python, scritta in C. E l'interprete usato nella stragrande maggioranza dei casi. |
| **dunder method** | Metodo speciale con doppio underscore (es. `__init__`, `__eq__`, `__hash__`). Definisce il comportamento degli operatori e dei protocolli del linguaggio. |
| **EAFP** | "Easier to Ask Forgiveness than Permission" — pattern in cui si tenta un'operazione e si gestisce l'eccezione, piuttosto che verificare preventivamente le condizioni. |
| **f-string** | Stringa letterale con prefisso `f` che consente l'interpolazione diretta di espressioni Python tra parentesi graffe `{}`. Introdotta in Python 3.6. |
| **falsy** | Valore che viene valutato come `False` in un contesto booleano: `None`, `0`, `0.0`, `""`, `[]`, `()`, `{}`, `set()`. |
| **GIL** | Global Interpreter Lock — mutex di CPython che consente l'esecuzione di un solo thread di bytecode Python alla volta. |
| **hashable** | Oggetto che possiede un valore hash fisso per tutta la sua vita (implementa `__hash__`) e puo essere confrontato per uguaglianza (`__eq__`). Requisito per chiavi di dict e elementi di set. |
| **IEEE 754** | Standard internazionale per l'aritmetica in virgola mobile. Python `float` usa la rappresentazione a doppia precisione (64 bit) definita da questo standard. |
| **immutabile** | Oggetto il cui valore non puo essere modificato dopo la creazione. Esempi: `int`, `float`, `str`, `tuple`, `frozenset`. |
| **iterabile** | Oggetto che implementa il metodo `__iter__` e puo essere usato in un ciclo `for`. Esempi: liste, tuple, stringhe, dizionari, set, generatori. |
| **LEGB** | Regola di risoluzione dei nomi: Local, Enclosing, Global, Built-in. Python cerca un nome in questo ordine. |
| **mutabile** | Oggetto il cui valore puo essere modificato dopo la creazione. Esempi: `list`, `dict`, `set`, `bytearray`. |
| **PEP** | Python Enhancement Proposal — documento formale che propone modifiche al linguaggio, alla libreria standard o ai processi della comunita Python. |
| **REPL** | Read-Eval-Print Loop — ambiente interattivo che legge un'espressione, la valuta, stampa il risultato e ripete. Accessibile con il comando `python3`. |
| **singleton** | Oggetto di cui esiste una sola istanza. In Python: `None`, `True`, `False`, `NotImplemented`, `Ellipsis` (`...`). |
| **truthiness** | La proprieta di un oggetto di essere valutato come `True` o `False` in un contesto booleano, determinata dai metodi `__bool__` e `__len__`. |
| **type hint** | Annotazione di tipo opzionale (es. `x: int = 42`) che documenta il tipo atteso e consente l'analisi statica con strumenti come `mypy`. |
| **unpacking** | Destrutturazione di un iterabile nei suoi elementi componenti tramite assegnazione multipla (es. `a, b, c = [1, 2, 3]`). |
| **walrus operator** | L'operatore `:=` (Python 3.8+) che consente l'assegnazione all'interno di un'espressione (es. `if (n := len(x)) > 0:`). |
