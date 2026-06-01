---
corso: "Programmazione Python"
fase: "5 — Qualità e Manutenzione"
modulo: "30"
titolo: "Troubleshooting e Guide Pratiche"
versione: "pdb (stdlib) / py-spy 0.3+ / tracemalloc (stdlib) / pytest 8.x / ruff 0.4+"
livello: "Intermedio"
prerequisiti:
  - "07 — Error Handling e Logging"
  - "08 — Testing"
  - "25 — Performance"
obiettivi:
  - "Diagnosticare e risolvere problemi comuni di runtime Python"
  - "Utilizzare pdb, breakpoint() e debugger IDE per debug interattivo"
  - "Analizzare memory leak con tracemalloc e objgraph"
  - "Profilare applicazioni con py-spy e cProfile"
  - "Risolvere problemi di import, encoding e compatibilita versioni"
  - "Applicare checklist di troubleshooting sistematiche"
tag: [troubleshooting, debugging, pdb, py-spy, tracemalloc, profiling, diagnostica]
---

# Troubleshooting e Guide Pratiche — Guida Completa

> **Modulo 30** · **Aggiornamento:** 2026-05-24 · **Versione:** pdb (stdlib) / py-spy 0.3+ / tracemalloc (stdlib) / pytest 8.x / ruff 0.4+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Error Handling](07-error-handling-e-logging.md), [Testing](08-testing.md), [Performance](25-performance.md)
>
> Al termine di questo modulo saprai:
> 1. Diagnosticare e risolvere problemi comuni di runtime Python
> 2. Utilizzare `pdb`, `breakpoint()` e debugger IDE per debug interattivo
> 3. Analizzare memory leak con `tracemalloc` e `objgraph`
> 4. Profilare applicazioni con py-spy e cProfile
> 5. Risolvere problemi di import, encoding e compatibilita versioni
> 6. Applicare checklist di troubleshooting sistematiche
>
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida
1. **`pdb`/`ipdb` per debugging interattivo.**
2. **`pytest --pdb` entra in debugger su fail.**
3. **Memory leak: `tracemalloc.start()` + snapshot diff.**
4. **CPU profile: py-spy (no code change).**

### Mappa concettuale

```
                      ┌──────────────────────────┐
                      │    TROUBLESHOOTING        │
                      └────────────┬─────────────┘
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Errori Comuni   │     │  Debugging       │      │  Profiling      │
 │  SyntaxError    │     │  pdb / ipdb     │      │  py-spy         │
 │  TypeError      │     │  breakpoint()   │      │  tracemalloc    │
 │  ImportError    │     │  VS Code debug  │      │  cProfile       │
 └────────┬────────┘     └────────┬────────┘      └────────┬────────┘
          │                       │                        │
          ▼                       ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Pitfall Python  │     │  Guide Pratiche  │      │  Produzione     │
 │  Mutable default│     │  Setup progetto │      │  Deploy checklist│
 │  Late binding   │     │  REST API       │      │  Error monitoring│
 │  GIL            │     │  CLI tool       │      │  Sentry / logs  │
 └─────────────────┘     └─────────────────┘      └─────────────────┘
```


## Indice

1. [Panoramica](#panoramica)
2. [Errori Comuni Python](#errori-comuni-python)
   - [SyntaxError](#syntaxerror)
   - [TypeError](#typeerror)
   - [ValueError](#valueerror)
   - [KeyError e IndexError](#keyerror-e-indexerror)
   - [AttributeError](#attributeerror)
   - [ImportError e ModuleNotFoundError](#importerror-e-modulenotfounderror)
   - [FileNotFoundError e PermissionError](#filenotfounderror-e-permissionerror)
   - [MemoryError e RecursionError](#memoryerror-e-recursionerror)
3. [Debugging](#debugging)
   - [pdb (Python Debugger)](#pdb-python-debugger)
   - [VS Code Debugging](#vs-code-debugging)
   - [Tecniche di Debugging](#tecniche-di-debugging)
   - [Strumenti di Debugging](#strumenti-di-debugging)
4. [Guide Pratiche](#guide-pratiche)
   - [Progetto 1: Setup Progetto Python Completo](#progetto-1-setup-progetto-python-completo)
   - [Progetto 2: REST API con FastAPI](#progetto-2-rest-api-con-fastapi)
   - [Progetto 3: CLI Tool Professionale](#progetto-3-cli-tool-professionale)
   - [Progetto 4: Automazione IT con Python](#progetto-4-automazione-it-con-python)
5. [Ambiente di Sviluppo](#ambiente-di-sviluppo)
   - [VS Code per Python](#vs-code-per-python)
   - [PyCharm (Panoramica)](#pycharm-panoramica)
6. [Risorse e Riferimenti](#risorse-e-riferimenti)
7. [Best Practices Generali](#best-practices-generali)
8. [Debugging Avanzato — pdb, breakpoint() e VS Code](#debugging-avanzato--pdb-breakpoint-e-vs-code)
   - [Debugger Alternativi: pdb++, ipdb e pudb](#debugger-alternativi-pdb-ipdb-e-pudb)
   - [Personalizzazione Avanzata di breakpoint()](#personalizzazione-avanzata-di-breakpoint)
   - [Debugging Multi-Thread](#debugging-multi-thread)
9. [Pitfall Classici di Python](#pitfall-classici-di-python)
   - [Argomenti Mutabili di Default](#argomenti-mutabili-di-default-mutable-default-arguments)
   - [Late Binding nelle Closure](#late-binding-nelle-closure)
   - [Import Circolari](#import-circolari)
   - [Confronto tra is e ==](#confronto-tra-is-e-)
   - [Scope e la Regola LEGB](#scope-e-la-regola-legb)
   - [Copia Superficiale vs Profonda](#copia-superficiale-vs-profonda)
10. [Profiling Recipes](#profiling-recipes)
    - [cProfile — Profiling Deterministico](#cprofile--profiling-deterministico)
    - [line_profiler — Profiling Riga per Riga](#line_profiler--profiling-riga-per-riga)
    - [py-spy — Profiling Sampling Senza Overhead](#py-spy--profiling-sampling-senza-overhead)
    - [Scalene — Profiler CPU + Memoria Unificato](#scalene--profiler-cpu--memoria-unificato)
11. [Rilevamento Memory Leak](#rilevamento-memory-leak)
    - [tracemalloc](#tracemalloc--tracciamento-allocazioni-nella-stdlib)
    - [objgraph](#objgraph--visualizzazione-dei-grafi-di-riferimento)
    - [Pympler](#pympler--analisi-approfondita-del-consumo-di-memoria)
    - [Pattern Comuni di Memory Leak](#pattern-comuni-di-memory-leak-e-soluzioni)
12. [GIL e Problematiche di Concorrenza](#gil-e-problematiche-di-concorrenza)
    - [Python 3.13+ e il Free-Threading](#python-313-e-il-free-threading-no-gil)
13. [Troubleshooting Encoding e Unicode](#troubleshooting-encoding-e-unicode)
14. [Datetime e Timezone — Trappole Comuni](#datetime-e-timezone--trappole-comuni)
15. [Debugging Asyncio](#debugging-asyncio)
16. [Debugging in Produzione](#debugging-in-produzione)
    - [faulthandler](#faulthandler--diagnostica-crash-a-livello-c)
    - [Remote Debugging con debugpy](#remote-debugging-con-debugpy)
    - [Logging Strutturato per Debugging](#logging-strutturato-per-debugging-in-produzione)
17. [Conflitti di Dipendenze e Gestione Ambienti](#conflitti-di-dipendenze-e-gestione-ambienti)
18. [Troubleshooting dell'Ambiente: PATH, PYTHONPATH e site-packages](#troubleshooting-dellambiente-path-pythonpath-e-site-packages)
19. [Deployment Checklist](#deployment-checklist)
20. [Error Monitoring in Produzione](#error-monitoring-in-produzione)
21. [FAQ](#faq)
22. [Esercizi](#esercizi)
23. [Letture](#letture)
24. [Glossario](#glossario)

---

## Panoramica

Ogni sviluppatore Python, indipendentemente dal livello di esperienza, trascorre una porzione significativa del proprio tempo a diagnosticare errori, interpretare traceback e cercare soluzioni a problemi imprevisti. La capacita di effettuare troubleshooting in modo efficiente e sistematico non e un talento innato, ma una competenza che si costruisce attraverso la conoscenza approfondita dei messaggi di errore, la padronanza degli strumenti di debugging e l'accumulo di esperienza pratica.

Questa guida rappresenta il capitolo conclusivo della sezione dedicata alla programmazione Python. Il suo obiettivo e duplice: da un lato, fornire un riferimento rapido e completo per la risoluzione degli errori piu comuni; dall'altro, offrire guide pratiche passo-passo che integrano tutte le competenze acquisite nei capitoli precedenti — dai fondamenti del linguaggio al testing, dal packaging alla CI/CD, dalla sicurezza alle performance.

La struttura segue un approccio pragmatico. Si inizia con un catalogo ragionato degli errori Python piu frequenti, ciascuno corredato di cause tipiche, esempi concreti e soluzioni collaudate. Si prosegue con una sezione dedicata al debugging, che copre sia gli strumenti integrati nel linguaggio sia le configurazioni per gli IDE moderni. Infine, quattro progetti guidati dimostrano come applicare le conoscenze in scenari reali completi, dalla configurazione iniziale al deployment.

---

## Errori Comuni Python

### SyntaxError

Il `SyntaxError` e l'errore piu elementare: il parser Python non riesce a interpretare il codice perche la struttura sintattica non e valida. Viene rilevato prima dell'esecuzione, durante la fase di parsing.

**Causa 1 — Due punti mancanti dopo le dichiarazioni composte.**

```python
# ERRORE
def calcola_totale(prezzi)
    return sum(prezzi)

# CORRETTO
def calcola_totale(prezzi):
    return sum(prezzi)
```

Questo vale per `def`, `class`, `if`, `elif`, `else`, `for`, `while`, `try`, `except`, `finally`, `with`.

**Causa 2 — Parentesi non bilanciate.**

```python
# ERRORE — parentesi aperta mai chiusa
risultato = (valore_1 + valore_2 * (fattore - 1)

# CORRETTO
risultato = (valore_1 + valore_2 * (fattore - 1))
```

Il traceback spesso indica la riga successiva a quella contenente l'errore reale, perche Python continua a cercare la chiusura della parentesi. Quando il `SyntaxError` segnala una riga che sembra corretta, controllare sempre le righe precedenti.

**Causa 3 — Indentazione errata.**

```python
# ERRORE — mix di tab e spazi (invisibile ma devastante)
def processo():
    passo_1()
	passo_2()  # tab invece di spazi

# SOLUZIONE: configurare l'editor per convertire tab in spazi
# In VS Code: "editor.insertSpaces": true, "editor.tabSize": 4
```

**Causa 4 — Problemi con le f-string.**

```python
# ERRORE — backslash dentro le espressioni f-string (prima di Python 3.12)
nome = f"{'\\n'.join(lista)}"  # SyntaxError

# CORRETTO — estrarre in variabile
separatore = '\n'
nome = f"{separatore.join(lista)}"

# ERRORE — dizionario con stesse virgolette
msg = f"Valore: {dati["chiave"]}"  # SyntaxError

# CORRETTO — usare virgolette diverse
msg = f"Valore: {dati['chiave']}"
```

**Causa 5 — Sintassi Python 2 in codice Python 3.**

```python
# Python 2 (obsoleto)
print "Messaggio"
raise ValueError, "errore"
except Exception, e:

# Python 3 (corretto)
print("Messaggio")
raise ValueError("errore")
except Exception as e:
```

---

### TypeError

Il `TypeError` si verifica quando un'operazione o una funzione viene applicata a un oggetto di tipo inappropriato. A differenza del `SyntaxError`, viene rilevato a runtime.

**"unsupported operand type(s)"**

```python
# ERRORE
eta = "25"
anno_nascita = 2026 - eta  # TypeError: unsupported operand type(s) for -: 'int' and 'str'

# CORRETTO
eta = int("25")
anno_nascita = 2026 - eta
```

**"'NoneType' object is not subscriptable" / "not callable"**

```python
# ERRORE — metodi che modificano in-place restituiscono None
lista = [3, 1, 2]
lista_ordinata = lista.sort()  # sort() restituisce None!
primo = lista_ordinata[0]  # TypeError: 'NoneType' object is not subscriptable

# CORRETTO — usare sorted() per ottenere una nuova lista
lista_ordinata = sorted(lista)
primo = lista_ordinata[0]

# ERRORE — sovrascrittura accidentale di un nome
len = 5  # ora len non e piu una funzione
len("test")  # TypeError: 'int' object is not callable
```

**"takes N positional arguments but M were given"**

```python
# ERRORE — self dimenticato nei metodi
class Servizio:
    def elabora(dati):  # manca self!
        return dati.upper()

s = Servizio()
s.elabora("test")  # TypeError: elabora() takes 1 positional argument but 2 were given

# CORRETTO
class Servizio:
    def elabora(self, dati):
        return dati.upper()
```

**La trappola degli argomenti mutabili di default.**

Questo e uno degli errori piu insidiosi in Python perche non genera un `TypeError` evidente ma produce comportamenti inattesi.

```python
# PERICOLOSO — l'oggetto mutabile e condiviso tra tutte le chiamate
def aggiungi_elemento(elemento, lista=[]):
    lista.append(elemento)
    return lista

print(aggiungi_elemento("a"))  # ['a']
print(aggiungi_elemento("b"))  # ['a', 'b'] — inatteso!

# CORRETTO — usare None come sentinel
def aggiungi_elemento(elemento, lista=None):
    if lista is None:
        lista = []
    lista.append(elemento)
    return lista
```

---

### ValueError

Il `ValueError` indica che una funzione riceve un argomento del tipo corretto ma con un valore inappropriato.

**"invalid literal for int() with base 10"**

```python
# ERRORE
numero = int("12.5")    # ValueError — non e un intero
numero = int("dodici")  # ValueError — non e un numero

# CORRETTO — validazione preventiva
testo = "12.5"
try:
    numero = int(testo)
except ValueError:
    try:
        numero = int(float(testo))  # converte prima in float, poi in int
    except ValueError:
        print(f"Impossibile convertire '{testo}' in numero")
```

**"not enough values to unpack" / "too many values to unpack"**

```python
# ERRORE
coordinate = (10, 20, 30)
x, y = coordinate  # ValueError: too many values to unpack

# CORRETTO — usare * per catturare il resto
x, y, *resto = coordinate  # x=10, y=20, resto=[30]

# ERRORE comune con enumerate
dati = [("Alice", 25), ("Bob", 30)]
for nome, eta in dati:  # funziona
    pass

for i, nome, eta in dati:  # ValueError!
    pass

# CORRETTO
for i, (nome, eta) in enumerate(dati):
    pass
```

**Problemi di conversione dati comuni.**

```python
# Conversione date — errore frequente
from datetime import datetime

# ERRORE — formato non corrispondente
data = datetime.strptime("28/03/2026", "%Y-%m-%d")  # ValueError

# CORRETTO — specificare il formato esatto
data = datetime.strptime("28/03/2026", "%d/%m/%Y")

# JSON — valori non serializzabili
import json
from datetime import date

# ERRORE
json.dumps({"data": date.today()})  # TypeError (non ValueError, ma correlato)

# CORRETTO — serializzatore personalizzato
json.dumps({"data": date.today().isoformat()})
```

---

### KeyError e IndexError

Questi errori si verificano quando si tenta di accedere a elementi inesistenti in dizionari o sequenze.

**KeyError — accesso a chiavi inesistenti nei dizionari.**

```python
utente = {"nome": "Alice", "eta": 25}

# ERRORE
email = utente["email"]  # KeyError: 'email'

# SOLUZIONE 1 — .get() con valore di default
email = utente.get("email", "non specificata")

# SOLUZIONE 2 — controllo preventivo
if "email" in utente:
    email = utente["email"]

# SOLUZIONE 3 — defaultdict per strutture complesse
from collections import defaultdict

contatori = defaultdict(int)
contatori["visite"] += 1  # nessun KeyError, inizializza a 0

raggruppamento = defaultdict(list)
raggruppamento["backend"].append("Python")  # nessun KeyError
```

**IndexError — indice fuori range nelle sequenze.**

```python
elementi = ["a", "b", "c"]

# ERRORE
quarto = elementi[3]  # IndexError: list index out of range

# PATTERN DIFENSIVI
# 1. Controllo lunghezza
if len(elementi) > 3:
    quarto = elementi[3]

# 2. Slicing sicuro (non genera mai IndexError)
quarto = elementi[3:4]  # restituisce [] se non esiste

# 3. next() con default per iterabili
primo = next(iter(elementi), None)  # None se vuoto

# 4. Accesso sicuro a liste annidate
def safe_get(lista, indice, default=None):
    """Accesso sicuro a lista con indice."""
    try:
        return lista[indice]
    except (IndexError, TypeError):
        return default
```

---

### AttributeError

L'`AttributeError` si verifica quando si tenta di accedere a un attributo o metodo che non esiste sull'oggetto.

**NoneType — la causa piu frequente.**

```python
# ERRORE — una funzione restituisce None inaspettatamente
import re

risultato = re.search(r"\d+", "nessun numero")
numero = risultato.group()  # AttributeError: 'NoneType' has no attribute 'group'

# CORRETTO — verificare il risultato
risultato = re.search(r"\d+", "nessun numero")
if risultato:
    numero = risultato.group()
else:
    numero = None

# Con l'operatore walrus (Python 3.8+)
if risultato := re.search(r"\d+", "ci sono 42 elementi"):
    numero = risultato.group()
```

**Circular import — causa sottile di AttributeError.**

```python
# modulo_a.py
from modulo_b import funzione_b

def funzione_a():
    return "A"

# modulo_b.py
from modulo_a import funzione_a  # ImportError o AttributeError a runtime

def funzione_b():
    return funzione_a()

# SOLUZIONE 1 — import all'interno della funzione (lazy import)
# modulo_b.py
def funzione_b():
    from modulo_a import funzione_a
    return funzione_a()

# SOLUZIONE 2 — ristrutturare il codice estraendo le dipendenze comuni
```

---

### ImportError e ModuleNotFoundError

`ModuleNotFoundError` (sottoclasse di `ImportError` da Python 3.6) indica che il modulo richiesto non e stato trovato nel path di ricerca.

**Cause e soluzioni.**

```python
# 1. Modulo non installato
import fastapi  # ModuleNotFoundError

# Verifica: pip list | grep fastapi
# Soluzione: pip install fastapi (nel virtual environment corretto!)

# 2. Virtual environment non attivato
# Verifica quale Python si sta usando
import sys
print(sys.executable)  # deve puntare al venv
print(sys.path)        # deve includere il path del venv

# 3. Import relativo vs assoluto
# struttura:
# progetto/
#   src/
#     __init__.py
#     modulo_a.py
#     sottopacchetto/
#       __init__.py
#       modulo_b.py

# Da modulo_b.py:
from ..modulo_a import funzione  # import relativo (richiede __init__.py)
from src.modulo_a import funzione  # import assoluto (richiede src nel path)

# 4. Circular import — cause e soluzioni
# PROBLEMA: A importa B, B importa A
# SOLUZIONI:
# a) Spostare l'import dentro la funzione (lazy import)
# b) Usare import del modulo invece di from ... import
# c) Ristrutturare il codice (estrarre dipendenze comuni in un terzo modulo)
# d) Usare TYPE_CHECKING per import solo di type hints
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modulo_a import ClasseA  # importato solo per i type hints, non a runtime
```

---

### FileNotFoundError e PermissionError

Errori legati al filesystem sono estremamente comuni, specialmente in applicazioni che operano su file e directory.

**Path relativi vs assoluti.**

```python
# ERRORE — il path relativo dipende dalla directory di lavoro corrente
with open("config.json") as f:  # FileNotFoundError se cwd != directory del progetto
    config = json.load(f)

# CORRETTO — path assoluto basato sulla posizione dello script
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / "config.json"

with open(config_path) as f:
    config = json.load(f)
```

**Compatibilita tra Windows e Linux.**

```python
# ERRORE — hardcoding del separatore
path = "C:\\Users\\utente\\documenti\\file.txt"  # non funziona su Linux

# CORRETTO — usare pathlib per la portabilita
from pathlib import Path

# Funziona su qualsiasi sistema operativo
percorso = Path.home() / "documenti" / "file.txt"

# Creare directory se non esistono
percorso.parent.mkdir(parents=True, exist_ok=True)
```

**PermissionError.**

```python
# Gestione dei permessi
from pathlib import Path
import os

percorso = Path("/var/log/applicazione.log")

# Verifica preventiva dei permessi
if not os.access(percorso.parent, os.W_OK):
    print(f"Nessun permesso di scrittura su {percorso.parent}")
    # Fallback su directory scrivibile
    percorso = Path.home() / ".local" / "log" / "applicazione.log"
    percorso.parent.mkdir(parents=True, exist_ok=True)

# Su Linux: fix permessi
# chmod 644 /var/log/applicazione.log
# chown utente:gruppo /var/log/applicazione.log
```

---

### MemoryError e RecursionError

Questi errori indicano l'esaurimento delle risorse del sistema.

**MemoryError — gestione di grandi volumi di dati.**

```python
# ERRORE — caricare tutto in memoria
with open("file_enorme.csv") as f:
    righe = f.readlines()  # MemoryError su file da diversi GB

# CORRETTO — processing riga per riga (streaming)
with open("file_enorme.csv") as f:
    for riga in f:  # itera senza caricare tutto in memoria
        elabora(riga)

# CORRETTO — usare generatori invece di liste
# Invece di:
quadrati = [x**2 for x in range(10_000_000)]  # lista enorme in memoria

# Usare:
quadrati = (x**2 for x in range(10_000_000))  # generatore, memoria costante

# Per dati tabulari grandi: pandas con chunk
import pandas as pd

for chunk in pd.read_csv("enorme.csv", chunksize=10_000):
    elabora_chunk(chunk)
```

**RecursionError — limite di ricorsione raggiunto.**

```python
# ERRORE — ricorsione senza caso base corretto
def fattoriale(n):
    return n * fattoriale(n - 1)  # manca il caso base!

fattoriale(1000)  # RecursionError: maximum recursion depth exceeded

# CORRETTO — caso base esplicito
def fattoriale(n):
    if n <= 1:
        return 1
    return n * fattoriale(n - 1)

# Per ricorsioni profonde legittime: aumentare il limite (con cautela)
import sys
sys.setrecursionlimit(5000)  # default e 1000

# ALTERNATIVA MIGLIORE — conversione a iterativo
def fattoriale_iterativo(n):
    risultato = 1
    for i in range(2, n + 1):
        risultato *= i
    return risultato

# Oppure usare @functools.lru_cache per memoization
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

---

## Debugging

### pdb (Python Debugger)

Il modulo `pdb` e il debugger integrato nella libreria standard di Python. Da Python 3.7, la funzione built-in `breakpoint()` offre un punto di ingresso immediato e configurabile.

**Inserire un breakpoint.**

```python
def calcola_prezzo_finale(prezzo_base, sconto, iva=22):
    prezzo_scontato = prezzo_base * (1 - sconto / 100)
    breakpoint()  # il programma si ferma qui — Python 3.7+
    totale = prezzo_scontato * (1 + iva / 100)
    return totale
```

**Comandi fondamentali di pdb.**

| Comando | Abbreviazione | Descrizione |
|---------|--------------|-------------|
| `next` | `n` | Esegue la riga corrente, passa alla successiva |
| `step` | `s` | Entra dentro la funzione chiamata |
| `continue` | `c` | Continua l'esecuzione fino al prossimo breakpoint |
| `print expr` | `p expr` | Stampa il valore di un'espressione |
| `pretty-print` | `pp expr` | Stampa formattata (per strutture complesse) |
| `list` | `l` | Mostra il codice sorgente attorno alla riga corrente |
| `where` | `w` | Mostra lo stack trace completo |
| `up` | `u` | Sale di un livello nello stack |
| `down` | `d` | Scende di un livello nello stack |
| `break` | `b` | Imposta un breakpoint |
| `clear` | `cl` | Rimuove un breakpoint |
| `quit` | `q` | Esce dal debugger |

**Breakpoint condizionali.**

```python
# Da pdb
# b 42, contatore > 100  — si ferma alla riga 42 solo se contatore > 100

# Oppure nel codice
for i, elemento in enumerate(dati):
    if i == 500:  # breakpoint solo alla 500esima iterazione
        breakpoint()
    elabora(elemento)
```

**Post-mortem debugging — analisi dopo un crash.**

```python
# Da riga di comando
# python -m pdb script.py  — entra in pdb al primo crash

# Nel codice
import pdb

try:
    risultato = funzione_problematica()
except Exception:
    pdb.post_mortem()  # apre pdb nello stato esatto del crash

# Disabilitare breakpoint() senza rimuoverlo dal codice
# PYTHONBREAKPOINT=0 python script.py
```

---

### VS Code Debugging

VS Code offre un debugger grafico potente per Python, integrato con l'estensione ufficiale Python.

**Configurazione launch.json.**

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: File Corrente",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: Modulo",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload"],
            "console": "integratedTerminal"
        },
        {
            "name": "pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["-xvs", "tests/"],
            "console": "integratedTerminal"
        },
        {
            "name": "Django",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": ["runserver", "--noreload"],
            "django": true
        },
        {
            "name": "Remote Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ]
        }
    ]
}
```

**Remote debugging con debugpy (utile per Docker e server remoti).**

```python
# Aggiungere nel codice del server remoto / container Docker
import debugpy

debugpy.listen(("0.0.0.0", 5678))
print("In attesa del debugger...")
debugpy.wait_for_client()  # si ferma qui fino alla connessione del debugger
print("Debugger connesso!")
```

**Funzionalita chiave.**

- **Breakpoints**: click sulla colonna sinistra del numero di riga. Supporta breakpoint condizionali (tasto destro sul breakpoint) e logpoint (stampa un messaggio senza fermarsi).
- **Watch**: aggiungere espressioni da monitorare continuamente durante l'esecuzione.
- **Call Stack**: visualizzare e navigare lo stack di chiamate, passare da un thread all'altro.
- **Variables**: esplorare variabili locali, globali e di closure.
- **Debug Console**: eseguire espressioni Python nel contesto corrente del breakpoint.

---

### Tecniche di Debugging

Oltre agli strumenti formali, esistono tecniche e approcci mentali fondamentali per il debugging efficace.

**Print debugging — la tecnica piu immediata.**

```python
# Semplice ma efficace con f-string
def processa_ordine(ordine):
    print(f"DEBUG: ordine ricevuto = {ordine!r}")  # !r usa repr()
    totale = calcola_totale(ordine)
    print(f"DEBUG: totale calcolato = {totale}")
    return totale

# Per strutture complesse, usare pprint
from pprint import pprint

def analizza_risposta(risposta):
    print("=== RISPOSTA API ===")
    pprint(risposta, width=120, depth=3)
    print("=" * 40)
```

**Logging-based debugging — persistente e configurabile.**

```python
import logging

# Configurazione rapida per debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d — %(message)s"
)
logger = logging.getLogger(__name__)

def processa_dati(dati):
    logger.debug("Input ricevuto: %r", dati)
    risultato = trasforma(dati)
    logger.debug("Risultato trasformazione: %r", risultato)
    return risultato
```

**Binary search debugging (bisect) — isolare il problema rapidamente.**

Quando un bug si manifesta in un processo con molti passaggi, il metodo bisect dimezza iterativamente lo spazio di ricerca.

```python
# Se un processo di 100 passi fallisce:
# 1. Verificare lo stato a meta (passo 50)
# 2. Se corretto, il bug e nei passi 51-100 -> verificare passo 75
# 3. Se errato, il bug e nei passi 1-50 -> verificare passo 25
# In poche iterazioni si isola il passo problematico

# Applicabile anche ai commit git:
# git bisect start
# git bisect bad          (commit corrente e rotto)
# git bisect good abc123  (questo commit era OK)
# Git esegue binary search automaticamente tra i commit
```

**Rubber duck debugging.**

Tecnica che consiste nello spiegare il problema ad alta voce, riga per riga, a un oggetto inanimato (la "paperella di gomma"). Il processo di verbalizzazione obbliga a esaminare ogni assunzione e spesso rivela l'errore. E sorprendentemente efficace e sottovalutata.

**Esempio riproducibile minimo (MRE).**

Quando si richiede aiuto, creare il piu piccolo frammento di codice che riproduce il problema. Il processo di riduzione stessa spesso rivela la causa.

```python
# Invece di incollare 200 righe, isolare il problema:
# PRIMA: "il mio programma non funziona"
# DOPO (MRE):
d = {}
d.setdefault("chiave", []).append("valore")
# Perche d["chiave"] restituisce ['valore'] e non 'valore'?
# -> Ora il problema e chiaro: setdefault restituisce la lista, non l'elemento
```

---

### Strumenti di Debugging

**icecream (ic) — print debugging evoluto.**

```python
# pip install icecream
from icecream import ic

def calcola(x, y):
    ic(x, y)  # stampa: ic| x: 10, y: 20
    risultato = x * y + x
    ic(risultato)  # stampa: ic| risultato: 210
    return risultato

# Mostra automaticamente nome variabile, file, riga e funzione
# Configurazione globale
ic.configureOutput(prefix="DEBUG | ", includeContext=True)
```

**PySnooper — tracing automatico.**

```python
# pip install pysnooper
import pysnooper

@pysnooper.snoop()
def calcola_media(numeri):
    totale = 0
    for n in numeri:
        totale += n
    return totale / len(numeri)

# Stampa automaticamente ogni assegnazione, ogni riga eseguita,
# i valori delle variabili modificate — senza scrivere alcun print
```

**Modulo traceback — per catturare e formattare stack trace.**

```python
import traceback

try:
    funzione_rischiosa()
except Exception as e:
    # Salvare il traceback completo in una stringa
    tb = traceback.format_exc()
    logger.error("Errore durante l'elaborazione:\n%s", tb)

    # Oppure stampare solo le ultime N frame
    traceback.print_exc(limit=3)
```

**faulthandler — per crash a livello C o deadlock.**

```python
# Abilitare all'avvio dell'applicazione
import faulthandler
faulthandler.enable()

# Oppure da riga di comando:
# python -X faulthandler script.py

# Dump dello stato di tutti i thread (utile per deadlock)
# Inviare SIGUSR1 al processo:
# kill -USR1 <pid>
faulthandler.register(signal.SIGUSR1)
```

---

## Guide Pratiche

### Progetto 1: Setup Progetto Python Completo

Questa guida passo-passo mostra come configurare un progetto Python professionale da zero, integrando tutte le best practice moderne.

**Passo 1 — Creare la struttura delle directory (src layout).**

```bash
mkdir -p mio-progetto/{src/mio_progetto,tests,docs}
cd mio-progetto

# Struttura risultante:
# mio-progetto/
# ├── src/
# │   └── mio_progetto/
# │       ├── __init__.py
# │       └── core.py
# ├── tests/
# │   ├── __init__.py
# │   └── test_core.py
# ├── docs/
# ├── pyproject.toml
# ├── .gitignore
# └── .pre-commit-config.yaml
```

**Passo 2 — Inizializzare git e .gitignore.**

```bash
git init

# .gitignore per Python
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.env
*.db
.mypy_cache/
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage
EOF
```

**Passo 3 — Creare pyproject.toml.**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mio-progetto"
version = "0.1.0"
description = "Descrizione del progetto"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
    "pre-commit>=3.7",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

**Passo 4 — Setup virtual environment.**

```bash
# Con uv (consigliato — velocissimo)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Oppure con il metodo classico
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Passo 5 — Configurare linting, formatting e type checking.**

```bash
# Ruff (linting + formatting) — gia configurato in pyproject.toml
ruff check src/ tests/
ruff format src/ tests/

# Mypy (type checking)
mypy src/
```

**Passo 6 — Setup pre-commit hooks.**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: []

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
```

```bash
pre-commit install
pre-commit run --all-files  # verifica iniziale
```

**Passo 7 — Scrivere il primo test.**

```python
# src/mio_progetto/core.py
def saluta(nome: str) -> str:
    """Restituisce un saluto personalizzato."""
    if not nome.strip():
        raise ValueError("Il nome non puo essere vuoto")
    return f"Ciao, {nome}!"

# tests/test_core.py
import pytest
from mio_progetto.core import saluta

def test_saluta_nome_valido():
    assert saluta("Alice") == "Ciao, Alice!"

def test_saluta_nome_vuoto():
    with pytest.raises(ValueError, match="vuoto"):
        saluta("   ")
```

```bash
pytest  # esegue i test
pytest --cov=mio_progetto --cov-report=term-missing  # con coverage
```

**Passo 8 — Configurare CI con GitHub Actions.**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv pip install -e ".[dev]" --system

      - name: Lint
        run: ruff check src/ tests/

      - name: Type check
        run: mypy src/

      - name: Test
        run: pytest --cov=mio_progetto --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

### Progetto 2: REST API con FastAPI

Guida completa per costruire una REST API professionale con FastAPI, database e autenticazione.

**Passo 1 — Struttura del progetto.**

```
fastapi-progetto/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── utente.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── utente.py
│       ├── routers/
│       │   ├── __init__.py
│       │   └── utenti.py
│       └── auth/
│           ├── __init__.py
│           └── jwt.py
├── alembic/
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

**Passo 2 — Database con SQLAlchemy e Alembic.**

```python
# src/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session

# src/app/models/utente.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Utente(Base):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
```

```bash
# Inizializzare Alembic
alembic init alembic
# Configurare alembic.ini e env.py con il modello e la connessione
alembic revision --autogenerate -m "create utenti table"
alembic upgrade head
```

**Passo 3 — Modelli Pydantic.**

```python
# src/app/schemas/utente.py
from pydantic import BaseModel, EmailStr, ConfigDict

class UtenteBase(BaseModel):
    nome: str
    email: EmailStr

class UtenteCreate(UtenteBase):
    password: str

class UtenteResponse(UtenteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

**Passo 4 — Endpoint CRUD.**

```python
# src/app/routers/utenti.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.utente import Utente
from app.schemas.utente import UtenteCreate, UtenteResponse

router = APIRouter(prefix="/utenti", tags=["utenti"])

@router.post("/", response_model=UtenteResponse, status_code=status.HTTP_201_CREATED)
async def crea_utente(dati: UtenteCreate, db: AsyncSession = Depends(get_db)):
    utente = Utente(nome=dati.nome, email=dati.email, password_hash=hash_password(dati.password))
    db.add(utente)
    await db.commit()
    await db.refresh(utente)
    return utente

@router.get("/{utente_id}", response_model=UtenteResponse)
async def leggi_utente(utente_id: int, db: AsyncSession = Depends(get_db)):
    risultato = await db.execute(select(Utente).where(Utente.id == utente_id))
    utente = risultato.scalar_one_or_none()
    if not utente:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return utente
```

**Passo 5 — Autenticazione JWT.**

```python
# src/app/auth/jwt.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "chiave-segreta-da-env"  # in produzione: da variabile d'ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def crea_token(dati: dict) -> str:
    payload = dati.copy()
    scadenza = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": scadenza})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def utente_corrente(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        utente_id: int = payload.get("sub")
        if utente_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return utente_id
```

**Passo 6 — Testing.**

```python
# tests/test_utenti.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_crea_utente(client):
    risposta = await client.post("/utenti/", json={
        "nome": "Alice",
        "email": "alice@example.com",
        "password": "password123"
    })
    assert risposta.status_code == 201
    assert risposta.json()["nome"] == "Alice"
```

**Passo 7 — Deployment con Docker.**

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/app
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

---

### Progetto 3: CLI Tool Professionale

Guida completa per costruire un tool da riga di comando professionale con Typer, output formattato e distribuzione.

**Passo 1 — Setup con Typer.**

```python
# src/mytool/cli.py
import typer
from typing import Optional
from typing_extensions import Annotated

app = typer.Typer(
    name="mytool",
    help="Tool CLI professionale per gestione progetti.",
    add_completion=False,
)

# Sottogruppo di comandi
progetto_app = typer.Typer(help="Gestione progetti.")
app.add_typer(progetto_app, name="progetto")
```

**Passo 2 — Comandi e sottocomandi.**

```python
@progetto_app.command()
def init(
    nome: Annotated[str, typer.Argument(help="Nome del progetto")],
    template: Annotated[str, typer.Option("--template", "-t", help="Template da usare")] = "base",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    """Inizializza un nuovo progetto con il template specificato."""
    if verbose:
        typer.echo(f"Inizializzazione progetto '{nome}' con template '{template}'...")
    crea_progetto(nome, template)
    typer.echo(f"Progetto '{nome}' creato con successo.")

@progetto_app.command()
def lista(
    filtro: Annotated[Optional[str], typer.Option("--filtro", "-f")] = None,
    formato: Annotated[str, typer.Option("--formato")] = "tabella",
):
    """Elenca tutti i progetti disponibili."""
    progetti = carica_progetti(filtro)
    mostra_progetti(progetti, formato)
```

**Passo 3 — Gestione configurazione.**

```python
# src/mytool/config.py
from pathlib import Path
import tomllib

CONFIG_DIR = Path.home() / ".config" / "mytool"
CONFIG_FILE = CONFIG_DIR / "config.toml"

def carica_config() -> dict:
    """Carica la configurazione da file TOML."""
    if not CONFIG_FILE.exists():
        return config_default()

    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)

def config_default() -> dict:
    return {
        "generale": {
            "editor": "vim",
            "colori": True,
        },
        "progetti": {
            "directory_base": str(Path.home() / "progetti"),
        },
    }
```

**Passo 4 — Output formattato con Rich.**

```python
# src/mytool/output.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

console = Console()

def mostra_progetti(progetti: list[dict], formato: str):
    if formato == "tabella":
        tabella = Table(title="Progetti")
        tabella.add_column("Nome", style="cyan", no_wrap=True)
        tabella.add_column("Stato", style="green")
        tabella.add_column("Ultimo aggiornamento", style="magenta")

        for p in progetti:
            tabella.add_row(p["nome"], p["stato"], p["aggiornato"])

        console.print(tabella)
    elif formato == "json":
        import json
        console.print_json(json.dumps(progetti))

def mostra_errore(messaggio: str):
    console.print(Panel(messaggio, title="Errore", border_style="red"))

def progresso(iterable, description="Elaborazione..."):
    return track(iterable, description=description)
```

**Passo 5 — Gestione errori.**

```python
# src/mytool/errori.py
import typer
from rich.console import Console

console = Console(stderr=True)

class MytoolError(Exception):
    """Errore base dell'applicazione."""
    pass

class ProgettoNonTrovatoError(MytoolError):
    """Progetto specificato non trovato."""
    pass

def gestisci_errori(func):
    """Decorator per gestione centralizzata degli errori nei comandi CLI."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MytoolError as e:
            console.print(f"[red]Errore:[/red] {e}")
            raise typer.Exit(code=1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operazione interrotta.[/yellow]")
            raise typer.Exit(code=130)
        except Exception as e:
            console.print(f"[red]Errore imprevisto:[/red] {e}")
            console.print("[dim]Usa --verbose per maggiori dettagli.[/dim]")
            raise typer.Exit(code=2)
    return wrapper
```

**Passo 6 — Testing con CliRunner.**

```python
# tests/test_cli.py
from typer.testing import CliRunner
from mytool.cli import app

runner = CliRunner()

def test_init_progetto():
    risultato = runner.invoke(app, ["progetto", "init", "test-progetto"])
    assert risultato.exit_code == 0
    assert "creato con successo" in risultato.stdout

def test_init_progetto_verbose():
    risultato = runner.invoke(app, ["progetto", "init", "test-progetto", "--verbose"])
    assert risultato.exit_code == 0
    assert "Inizializzazione" in risultato.stdout

def test_lista_progetti_vuota():
    risultato = runner.invoke(app, ["progetto", "lista"])
    assert risultato.exit_code == 0
```

**Passo 7 — Packaging e distribuzione.**

```toml
# In pyproject.toml
[project.scripts]
mytool = "mytool.cli:app"
```

```bash
# Build e installazione locale
pip install -e .
mytool --help

# Build per distribuzione
pip install build
python -m build
# Produce dist/mytool-0.1.0.tar.gz e dist/mytool-0.1.0-py3-none-any.whl

# Pubblicazione su PyPI
pip install twine
twine upload dist/*
```

---

### Progetto 4: Automazione IT con Python

Guida completa per costruire un sistema di automazione IT che monitora l'infrastruttura, genera report e invia notifiche.

**Passo 1 — Script di monitoraggio infrastruttura.**

```python
# src/automazione/monitor.py
import psutil
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class StatoSistema:
    hostname: str
    timestamp: datetime
    cpu_percent: float
    memoria_percent: float
    disco_percent: dict[str, float] = field(default_factory=dict)
    servizi_attivi: list[str] = field(default_factory=list)
    allarmi: list[str] = field(default_factory=list)

def raccogli_metriche() -> StatoSistema:
    """Raccoglie metriche di sistema."""
    stato = StatoSistema(
        hostname=socket.gethostname(),
        timestamp=datetime.now(timezone.utc),
        cpu_percent=psutil.cpu_percent(interval=1),
        memoria_percent=psutil.virtual_memory().percent,
    )

    # Spazio disco per ogni partizione
    for partizione in psutil.disk_partitions():
        try:
            uso = psutil.disk_usage(partizione.mountpoint)
            stato.disco_percent[partizione.mountpoint] = uso.percent
        except PermissionError:
            continue

    # Verifica soglie
    if stato.cpu_percent > 90:
        stato.allarmi.append(f"CPU al {stato.cpu_percent}%")
    if stato.memoria_percent > 85:
        stato.allarmi.append(f"Memoria al {stato.memoria_percent}%")
    for mount, percent in stato.disco_percent.items():
        if percent > 90:
            stato.allarmi.append(f"Disco {mount} al {percent}%")

    return stato
```

**Passo 2 — Automazione Active Directory (con ldap3).**

```python
# src/automazione/ad_manager.py
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE

class ADManager:
    """Gestore operazioni Active Directory."""

    def __init__(self, server_url: str, utente: str, password: str):
        self.server = Server(server_url, get_info=ALL)
        self.conn = Connection(self.server, user=utente, password=password, auto_bind=True)

    def cerca_utenti(self, filtro: str, base_dn: str) -> list[dict]:
        """Cerca utenti in Active Directory."""
        self.conn.search(
            search_base=base_dn,
            search_filter=f"(&(objectClass=user)(cn=*{filtro}*))",
            attributes=["cn", "mail", "department", "whenCreated"],
        )
        return [
            {
                "nome": entry.cn.value,
                "email": entry.mail.value if entry.mail else None,
                "dipartimento": entry.department.value if entry.department else None,
            }
            for entry in self.conn.entries
        ]

    def disabilita_utente(self, dn: str) -> bool:
        """Disabilita un account utente."""
        return self.conn.modify(dn, {
            "userAccountControl": [(MODIFY_REPLACE, [514])]  # 514 = account disabilitato
        })
```

**Passo 3 — Generazione report.**

```python
# src/automazione/report.py
from pathlib import Path
from datetime import datetime, timezone
import csv
import json

class GeneratoreReport:
    """Genera report in diversi formati."""

    def __init__(self, directory_output: Path):
        self.directory_output = directory_output
        self.directory_output.mkdir(parents=True, exist_ok=True)

    def genera_csv(self, dati: list[dict], nome_file: str) -> Path:
        """Genera report in formato CSV."""
        percorso = self.directory_output / f"{nome_file}_{self._timestamp()}.csv"
        if not dati:
            return percorso

        with open(percorso, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=dati[0].keys())
            writer.writeheader()
            writer.writerows(dati)

        return percorso

    def genera_html(self, stato: "StatoSistema", template: str = "base") -> Path:
        """Genera report HTML dal template."""
        percorso = self.directory_output / f"report_{self._timestamp()}.html"
        html = f"""<!DOCTYPE html>
<html>
<head><title>Report Sistema — {stato.hostname}</title></head>
<body>
    <h1>Report Infrastruttura</h1>
    <p>Host: {stato.hostname} | Data: {stato.timestamp:%d/%m/%Y %H:%M}</p>
    <table border="1">
        <tr><th>Metrica</th><th>Valore</th><th>Stato</th></tr>
        <tr><td>CPU</td><td>{stato.cpu_percent}%</td>
            <td>{"ALLARME" if stato.cpu_percent > 90 else "OK"}</td></tr>
        <tr><td>Memoria</td><td>{stato.memoria_percent}%</td>
            <td>{"ALLARME" if stato.memoria_percent > 85 else "OK"}</td></tr>
    </table>
</body>
</html>"""
        percorso.write_text(html, encoding="utf-8")
        return percorso

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
```

**Passo 4 — Distribuzione email.**

```python
# src/automazione/notifiche.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

class NotificatoreEmail:
    """Invia notifiche via email con allegati."""

    def __init__(self, smtp_host: str, smtp_port: int, utente: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.utente = utente
        self.password = password

    def invia(
        self,
        destinatari: list[str],
        oggetto: str,
        corpo_html: str,
        allegati: list[Path] | None = None,
    ) -> bool:
        """Invia email con corpo HTML e allegati opzionali."""
        msg = MIMEMultipart()
        msg["From"] = self.utente
        msg["To"] = ", ".join(destinatari)
        msg["Subject"] = oggetto
        msg.attach(MIMEText(corpo_html, "html"))

        for allegato in (allegati or []):
            with open(allegato, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
            encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={allegato.name}")
            msg.attach(parte)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.utente, self.password)
                server.send_message(msg)
            return True
        except smtplib.SMTPException as e:
            logger.error("Errore invio email: %s", e)
            return False
```

**Passo 5 — Scheduling.**

```python
# src/automazione/scheduler.py
import schedule
import time
import logging

logger = logging.getLogger(__name__)

def configura_scheduler():
    """Configura le attivita pianificate."""

    # Monitoraggio ogni 5 minuti
    schedule.every(5).minutes.do(esegui_monitoraggio)

    # Report giornaliero alle 8:00
    schedule.every().day.at("08:00").do(genera_report_giornaliero)

    # Pulizia settimanale il lunedi alle 2:00
    schedule.every().monday.at("02:00").do(pulizia_settimanale)

    # Report mensile il primo del mese
    schedule.every().day.at("07:00").do(report_mensile_se_primo)

def esegui_scheduler():
    """Loop principale dello scheduler."""
    configura_scheduler()
    logger.info("Scheduler avviato")

    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Scheduler fermato")
            break
        except Exception as e:
            logger.exception("Errore nello scheduler: %s", e)
            time.sleep(60)  # attende prima di riprovare
```

**Passo 6 — Logging e alerting.**

```python
# src/automazione/logging_config.py
import logging
import logging.handlers
from pathlib import Path

def configura_logging(livello: str = "INFO", directory_log: Path | None = None):
    """Configura il sistema di logging per l'automazione."""
    directory_log = directory_log or Path("/var/log/automazione")
    directory_log.mkdir(parents=True, exist_ok=True)

    # Formatter dettagliato
    formatter = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler con rotazione giornaliera
    file_handler = logging.handlers.TimedRotatingFileHandler(
        directory_log / "automazione.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Handler per errori critici (file separato)
    error_handler = logging.FileHandler(
        directory_log / "errori.log",
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configurazione root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, livello.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
```

---

## Ambiente di Sviluppo

### VS Code per Python

VS Code e l'editor piu utilizzato per lo sviluppo Python, grazie alla sua leggerezza, estensibilita e all'eccellente supporto tramite estensioni ufficiali.

**Estensioni essenziali.**

| Estensione | Descrizione |
|-----------|-------------|
| **Python** (Microsoft) | Supporto base: IntelliSense, linting, debugging, Jupyter |
| **Pylance** (Microsoft) | Language server avanzato: type checking, auto-import, analisi statica |
| **Ruff** (Astral) | Linting e formatting ultra-veloce, sostituisce flake8, isort, black |
| **Python Test Explorer** | Interfaccia grafica per eseguire e navigare i test |
| **Even Better TOML** | Supporto per pyproject.toml |
| **GitLens** | Annotazioni git inline, cronologia file |
| **Error Lens** | Mostra errori e warning direttamente sulla riga di codice |

**Configurazione settings.json ottimale per Python.**

```json
{
    // Python
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,

    // Type checking con Pylance
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.diagnosticMode": "workspace",

    // Formatting e linting con Ruff
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },

    // Testing
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/", "-v"],

    // Editor generale
    "editor.rulers": [100],
    "editor.insertSpaces": true,
    "editor.tabSize": 4,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
```

**Scorciatoie da tastiera utili per Python.**

| Scorciatoia | Azione |
|-------------|--------|
| `F5` | Avvia debugging |
| `F9` | Toggle breakpoint |
| `F10` / `F11` | Step over / Step into |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+Shift+T` | Riaprire file chiuso |
| `Ctrl+K Ctrl+I` | Mostra hover (documentazione) |
| `F12` | Vai alla definizione |
| `Shift+F12` | Trova tutti i riferimenti |
| `F2` | Rinomina simbolo |
| `Ctrl+Shift+M` | Mostra pannello problemi |

**Snippet personalizzati per Python (python.json).**

```json
{
    "Main guard": {
        "prefix": "main",
        "body": [
            "def main():",
            "    ${1:pass}",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    main()"
        ]
    },
    "Dataclass": {
        "prefix": "dc",
        "body": [
            "from dataclasses import dataclass",
            "",
            "@dataclass",
            "class ${1:NomeClasse}:",
            "    ${2:campo}: ${3:str}"
        ]
    },
    "Logger setup": {
        "prefix": "logger",
        "body": [
            "import logging",
            "",
            "logger = logging.getLogger(__name__)"
        ]
    }
}
```

---

### PyCharm (Panoramica)

PyCharm di JetBrains e l'IDE dedicato piu completo per Python. Offre funzionalita integrate che in VS Code richiedono estensioni separate.

**Community vs Professional.**

| Funzionalita | Community (gratuita) | Professional |
|-------------|---------------------|-------------|
| Editing Python | Si | Si |
| Debugging | Si | Si |
| Testing (pytest, unittest) | Si | Si |
| Refactoring avanzato | Si | Si |
| Git integration | Si | Si |
| Web framework (Django, Flask, FastAPI) | No | Si |
| Database tools | No | Si |
| Remote interpreters | No | Si |
| Docker support | No | Si |
| Profiler | No | Si |
| HTTP client | No | Si |

**Funzionalita chiave di PyCharm.**

- **Refactoring intelligente**: rinomina che comprende il contesto semantico, estrazione di metodi, variabili e costanti, inline, cambio firma delle funzioni.
- **Ispezioni di codice**: analisi statica integrata che identifica problemi potenziali, codice morto, violazioni di convenzioni.
- **Database integrato**: editor SQL, visualizzatore di schemi, esecuzione query con autocompletamento context-aware.
- **Debugger avanzato**: visualizzazione di DataFrame pandas, supporto multithread, debugger asincrono.
- **Run configurations**: configurazioni multiple per script, test, server, con parametri salvati.

**Configurazione consigliata.**

```
Settings → Editor → Code Style → Python:
  - Tab size: 4, Indent: 4, Continuation indent: 8
  - Hard wrap at: 100

Settings → Tools → Python Integrated Tools:
  - Default test runner: pytest
  - Docstring format: Google

Settings → Editor → Inspections:
  - Abilitare PEP 8 coding style violation
  - Abilitare Type checker (livello: Warning)
```

---

## Risorse e Riferimenti

**Documentazione ufficiale.**

- [Python Documentation](https://docs.python.org/3/) — la risorsa primaria e piu autorevole.
- [Python Tutorial](https://docs.python.org/3/tutorial/) — tutorial ufficiale per principianti.
- [Python Library Reference](https://docs.python.org/3/library/) — riferimento completo della libreria standard.
- [PEP Index](https://peps.python.org/) — tutte le Python Enhancement Proposals.
- [What's New](https://docs.python.org/3/whatsnew/) — novita di ogni versione.

**Libri consigliati.**

- **Fluent Python** (Luciano Ramalho) — il testo di riferimento per passare da principiante a esperto. Copre in profondita il data model, i protocolli, i generatori, la concorrenza e molto altro. La seconda edizione (2022) copre fino a Python 3.10.
- **Python Cookbook** (David Beazley, Brian K. Jones) — ricette pratiche per problemi comuni. Ogni ricetta include una spiegazione dettagliata del perche la soluzione funziona.
- **Effective Python** (Brett Slatkin) — 90 modi specifici per scrivere Python migliore. Ogni consiglio e conciso, motivato e immediatamente applicabile.
- **Architecture Patterns with Python** (Harry Percival, Bob Gregory) — pattern architetturali (Repository, Unit of Work, CQRS) applicati a Python.
- **Robust Python** (Patrick Viafore) — guida alla type safety e alla scrittura di codice robusto con type hints, protocolli e strumenti di analisi statica.

**Risorse online.**

- [Real Python](https://realpython.com/) — tutorial approfonditi e ben strutturati su ogni aspetto di Python.
- [Python Package Index (PyPI)](https://pypi.org/) — repository ufficiale dei pacchetti Python.
- [Awesome Python](https://github.com/vinta/awesome-python) — lista curata di framework, librerie e risorse.
- [Python Weekly](https://www.pythonweekly.com/) — newsletter settimanale con le novita dell'ecosistema.
- [Talk Python to Me](https://talkpython.fm/) — podcast con interviste a sviluppatori e maintainer dell'ecosistema.
- [testdriven.io](https://testdriven.io/) — tutorial orientati al testing e al deployment.

**Community italiana.**

- [Python Italia](https://www.python.it/) — associazione ufficiale della comunita Python italiana.
- [PyCon Italia](https://pycon.it/) — la conferenza annuale italiana su Python, una delle piu grandi in Europa.
- [Python Milano](https://www.meetup.com/Python-Milano/) — meetup mensili a Milano.
- [Python Roma](https://www.meetup.com/Python-Roma/) — meetup a Roma.
- [Telegram: Python Italia](https://t.me/python_ita) — gruppo Telegram attivo della comunita italiana.

**Certificazioni.**

- **PCEP** (Certified Entry-Level Python Programmer) — livello base, valida le conoscenze fondamentali.
- **PCAP** (Certified Associate in Python Programming) — livello intermedio, copre OOP, moduli, eccezioni.
- **PCPP1/PCPP2** (Certified Professional in Python Programming) — livello avanzato, copre design patterns, GUI, networking, testing.
- Le certificazioni sono rilasciate dal Python Institute e sono riconosciute internazionalmente.

---

## Best Practices Generali

Queste dieci best practice riassumono i principi fondamentali emersi dall'intera sezione dedicata alla programmazione Python. Rappresentano una sintesi operativa delle lezioni piu importanti, applicabili a qualsiasi progetto.

**1. Usare sempre un virtual environment.** Mai installare pacchetti nel Python di sistema. Creare un `.venv` per ogni progetto con `uv venv` o `python -m venv .venv`. Specificare le dipendenze in `pyproject.toml` con versioni vincolate. Generare un lock file per la riproducibilita.

**2. Scrivere type hints fin dall'inizio.** I type hints non sono un optional ma uno strumento di documentazione vivente e prevenzione errori. Usare `mypy` in modalita strict sui nuovi progetti. Le annotazioni rendono il codice piu leggibile, abilitano il completamento automatico nell'IDE e catturano intere categorie di bug prima dell'esecuzione.

**3. Testare in modo sistematico.** Ogni funzione pubblica merita almeno un test. Usare `pytest` come framework di test. Puntare a una coverage dell'80% come minimo ragionevole. Scrivere test che verificano il comportamento, non l'implementazione. Includere test per i casi limite e per le condizioni di errore.

**4. Automatizzare la qualita del codice.** Configurare `ruff` per linting e formatting, `mypy` per il type checking, `pre-commit` per eseguire i controlli automaticamente prima di ogni commit. L'automazione elimina le discussioni sullo stile e garantisce uniformita nel codice.

**5. Gestire gli errori in modo esplicito.** Mai catturare eccezioni generiche (`except Exception`) senza una ragione specifica. Usare eccezioni personalizzate per il dominio applicativo. Loggare sempre il traceback completo. Fallire rapidamente e in modo prevedibile piuttosto che propagare stati corrotti.

**6. Loggare, non stampare.** Sostituire ogni `print()` di debug con `logging.debug()`. Configurare il logging all'avvio dell'applicazione con livelli appropriati, rotazione dei file e formattazione strutturata. Il logging e configurabile, filtrabile e persistente; `print()` non lo e.

**7. Strutturare i progetti con il src layout.** Usare la struttura `src/nome_pacchetto/` per separare il codice sorgente dai test, dalla configurazione e dagli script. Questa struttura previene import accidentali del codice locale e rende il packaging corretto per definizione.

**8. Usare pathlib per ogni operazione sul filesystem.** Abbandonare `os.path` in favore di `pathlib.Path`. I path diventano oggetti con metodi espressivi (`.exists()`, `.read_text()`, `.mkdir(parents=True)`), la concatenazione usa l'operatore `/` e il codice funziona su tutti i sistemi operativi senza modifiche.

**9. Documentare le decisioni, non il codice ovvio.** Il codice ben scritto si documenta da solo attraverso nomi significativi e struttura chiara. I commenti devono spiegare il *perche*, non il *cosa*. Le docstring devono documentare il contratto della funzione: cosa accetta, cosa restituisce, quali eccezioni puo lanciare.

**10. Imparare a fare debugging in modo sistematico.** Non affidarsi solo all'intuizione. Formulare un'ipotesi, verificarla con un test o un breakpoint, procedere per eliminazione. Utilizzare `breakpoint()` e il debugger dell'IDE. Creare un esempio riproducibile minimo. La capacita di diagnosticare problemi in modo metodico distingue lo sviluppatore esperto dal principiante.

---

## Debugging Avanzato — pdb, breakpoint() e VS Code

Questa sezione approfondisce le tecniche di debugging avanzato che vanno oltre l'uso base di `pdb`. Copre debugger alternativi piu potenti, la personalizzazione di `breakpoint()`, e strategie avanzate per scenari complessi come il multi-threading e il debugging remoto.

### Debugger Alternativi: pdb++, ipdb e pudb

Il debugger standard `pdb` e funzionale ma spartano. L'ecosistema Python offre alternative significativamente piu comode che mantengono la stessa interfaccia di base aggiungendo funzionalita avanzate.

**pdb++ (pdbpp) — sostituzione drop-in di pdb.**

`pdb++` si installa con `pip install pdbpp` e sostituisce automaticamente `pdb` senza richiedere modifiche al codice. Offre syntax highlighting, completamento con tab, sticky mode (mostra il codice sorgente aggiornato a ogni step) e supporto per le espressioni lunghe.

```python
# Dopo aver installato pdbpp, breakpoint() usa automaticamente pdb++
# pip install pdbpp

def analizza_dati(dataset):
    risultati = []
    for record in dataset:
        breakpoint()  # si apre pdb++ con syntax highlighting e completamento
        valore = trasforma(record)
        risultati.append(valore)
    return risultati

# Comandi esclusivi di pdb++:
# sticky        — mostra il codice sorgente aggiornato continuamente
# longlist (ll) — mostra l'intera funzione corrente
# interact      — apre un interprete Python nel contesto corrente
# display expr  — monitora un'espressione e mostra quando cambia
# undisplay     — rimuove un'espressione monitorata
```

**ipdb — pdb con la potenza di IPython.**

`ipdb` integra il debugger con IPython, offrendo syntax highlighting, autocompletamento avanzato, magic commands e accesso alla cronologia dei comandi IPython.

```python
# pip install ipdb

# Uso diretto nel codice
import ipdb; ipdb.set_trace()

# Oppure configurare breakpoint() per usare ipdb
# PYTHONBREAKPOINT=ipdb.set_trace python script.py

# Funzionalita aggiuntive rispetto a pdb:
# - Tab completion avanzato con introspezione degli oggetti
# - Syntax highlighting automatico
# - %timeit per micro-benchmark inline durante il debug
# - ? e ?? per documentazione rapida degli oggetti
# - Cronologia comandi persistente tra sessioni

# Uso con pytest
# pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb tests/
```

**pudb — debugger visuale nel terminale.**

`pudb` offre un'interfaccia TUI (Text User Interface) completa con pannelli per sorgente, variabili, stack e breakpoint, tutto nel terminale.

```python
# pip install pudb

# Avvio diretto
# python -m pudb script.py

# Nel codice
import pudb; pudb.set_trace()

# O tramite breakpoint()
# PYTHONBREAKPOINT=pudb.set_trace python script.py

# Caratteristiche uniche di pudb:
# - Interfaccia a pannelli: codice sorgente, variabili, stack, breakpoints
# - Navigazione con tastiera (simile a vim)
# - Visualizzazione a struttura ad albero delle variabili complesse
# - Supporto per temi di colore personalizzabili
# - Shell integrata accessibile con Ctrl+X
# - Impostazione preferenze persistenti tra le sessioni
```

### Personalizzazione Avanzata di breakpoint()

La funzione `breakpoint()` introdotta in Python 3.7 (PEP 553) e molto piu flessibile di quanto la maggior parte degli sviluppatori realizzi. La variabile d'ambiente `PYTHONBREAKPOINT` controlla quale debugger viene invocato.

```python
# Disabilitare tutti i breakpoint senza rimuoverli dal codice
# PYTHONBREAKPOINT=0 python script.py

# Usare un debugger specifico
# PYTHONBREAKPOINT=ipdb.set_trace python script.py
# PYTHONBREAKPOINT=pudb.set_trace python script.py
# PYTHONBREAKPOINT=web_pdb.set_trace python script.py  # debugger web-based

# Creare un handler personalizzato per breakpoint()
# myproject/debug.py
import sys
import logging

logger = logging.getLogger("debug")

def custom_breakpoint(*args, **kwargs):
    """Handler personalizzato che logga lo stato prima di entrare nel debugger."""
    frame = sys._getframe(1)  # frame del chiamante
    logger.debug(
        "Breakpoint in %s:%d — funzione %s",
        frame.f_code.co_filename,
        frame.f_lineno,
        frame.f_code.co_name,
    )
    # Logga le variabili locali
    for nome, valore in frame.f_locals.items():
        logger.debug("  %s = %r", nome, valore)

    # Poi delega a pdb
    import pdb
    pdb.Pdb().set_trace(frame)

# Registrare il handler:
# PYTHONBREAKPOINT=myproject.debug.custom_breakpoint python script.py

# Breakpoint condizionale programmatico
import os

def breakpoint_if(condizione: bool, messaggio: str = ""):
    """Breakpoint che si attiva solo se la condizione e vera."""
    if condizione and os.environ.get("PYTHONBREAKPOINT") != "0":
        if messaggio:
            print(f"BREAKPOINT: {messaggio}")
        breakpoint()

# Uso
for i, record in enumerate(dati_grandi):
    breakpoint_if(record.get("anomalia"), f"Anomalia trovata al record {i}")
    elabora(record)
```

### Debugging Multi-Thread

Il debugging di applicazioni multi-thread richiede attenzione particolare per evitare di alterare il comportamento del programma durante l'ispezione.

```python
import threading
import pdb

# Problema: breakpoint() in un thread puo bloccare l'intero processo
# perche pdb acquisisce lo stdin nel thread sbagliato

# Soluzione 1: usare un debugger remoto per thread specifici
import debugpy

def worker(dati, thread_id):
    for item in dati:
        if item.get("errore"):
            # debugpy supporta il debugging multi-thread nativamente
            debugpy.breakpoint()
        elabora(item)

# Soluzione 2: logging strutturato per debugging non-intrusivo
import logging

logger = logging.getLogger(__name__)

def worker_con_logging(dati, thread_id):
    thread_name = threading.current_thread().name
    for i, item in enumerate(dati):
        logger.debug(
            "[%s] Elaborazione item %d/%d: %r",
            thread_name, i + 1, len(dati), item
        )
        risultato = elabora(item)
        if risultato is None:
            logger.warning(
                "[%s] Risultato None per item %d: %r",
                thread_name, i, item
            )

# Soluzione 3: forzare l'arresto di tutti i thread per ispezione
def debug_tutti_i_thread():
    """Stampa lo stack trace di tutti i thread attivi."""
    import sys
    import traceback

    print(f"\n{'='*60}")
    print(f"Thread attivi: {threading.active_count()}")
    print(f"{'='*60}")

    for thread_id, frame in sys._current_frames().items():
        thread = None
        for t in threading.enumerate():
            if t.ident == thread_id:
                thread = t
                break
        nome = thread.name if thread else f"Thread-{thread_id}"
        print(f"\n--- {nome} (id={thread_id}) ---")
        traceback.print_stack(frame)
    print(f"{'='*60}\n")
```

---

## Pitfall Classici di Python

Python e un linguaggio che privilegia la leggibilita e la semplicita, ma nasconde trappole sottili che possono confondere anche gli sviluppatori esperti. Questa sezione cataloga le insidie piu pericolose, ciascuna con spiegazione del meccanismo interno, esempio riproducibile e soluzione idiomatica.

### Argomenti Mutabili di Default (Mutable Default Arguments)

Questo e probabilmente il pitfall piu noto di Python, ma continua a mietere vittime perche il comportamento e controintuitivo per chiunque provenga da altri linguaggi.

```python
# Il problema: Python valuta gli argomenti di default UNA sola volta,
# al momento della DEFINIZIONE della funzione, non a ogni chiamata.

def aggiungi_tag(tag, lista_tag=[]):
    lista_tag.append(tag)
    return lista_tag

# Prima chiamata — sembra corretto
print(aggiungi_tag("python"))     # ['python']

# Seconda chiamata — inatteso!
print(aggiungi_tag("debugging"))  # ['python', 'debugging']

# La stessa lista viene riusata tra le chiamate!
# Verifica: id(lista_tag) e identico in entrambe le chiamate

# Il meccanismo interno:
# La funzione e un oggetto, e i default sono attributi dell'oggetto funzione
print(aggiungi_tag.__defaults__)  # (['python', 'debugging'],)

# SOLUZIONE CANONICA: usare None come sentinel
def aggiungi_tag_corretto(tag, lista_tag=None):
    if lista_tag is None:
        lista_tag = []
    lista_tag.append(tag)
    return lista_tag

# Questo vale per TUTTI gli oggetti mutabili: list, dict, set, bytearray
# E anche per oggetti personalizzati con stato mutabile

# ATTENZIONE: anche le date sono un caso subdolo
from datetime import datetime

def crea_evento(nome, timestamp=datetime.now()):  # BUG!
    # timestamp viene valutato una sola volta all'importazione
    return {"nome": nome, "timestamp": timestamp}

# CORRETTO
def crea_evento_corretto(nome, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    return {"nome": nome, "timestamp": timestamp}
```

### Late Binding nelle Closure

Le closure in Python catturano le variabili per riferimento, non per valore. Questo significa che il valore della variabile viene cercato solo al momento dell'esecuzione della closure, non al momento della sua creazione.

```python
# Il problema classico: lambda in un loop
funzioni = []
for i in range(5):
    funzioni.append(lambda: i)

# Tutte le lambda restituiscono 4 (l'ultimo valore di i)!
print([f() for f in funzioni])  # [4, 4, 4, 4, 4]

# Perche: la lambda cattura la VARIABILE i, non il suo VALORE
# Quando la lambda viene eseguita, i vale 4 (fine del loop)

# SOLUZIONE 1: argomento di default (cattura il valore al momento della creazione)
funzioni_corrette = []
for i in range(5):
    funzioni_corrette.append(lambda i=i: i)  # i=i "congela" il valore

print([f() for f in funzioni_corrette])  # [0, 1, 2, 3, 4]

# SOLUZIONE 2: functools.partial
from functools import partial

def restituisci_valore(x):
    return x

funzioni_partial = [partial(restituisci_valore, i) for i in range(5)]
print([f() for f in funzioni_partial])  # [0, 1, 2, 3, 4]

# SOLUZIONE 3: usare una factory function
def crea_funzione(valore):
    def funzione():
        return valore
    return funzione

funzioni_factory = [crea_funzione(i) for i in range(5)]
print([f() for f in funzioni_factory])  # [0, 1, 2, 3, 4]

# Il problema si manifesta anche con list comprehension + lambda
callbacks = {nome: lambda: nome for nome in ["alice", "bob", "carol"]}
print(callbacks["alice"]())  # "carol" — NON "alice"!

# CORRETTO
callbacks = {nome: (lambda n=nome: n) for nome in ["alice", "bob", "carol"]}
print(callbacks["alice"]())  # "alice"
```

### Import Circolari

Gli import circolari si verificano quando due o piu moduli si importano a vicenda, direttamente o indirettamente. Python gestisce gli import circolari in modo parziale, ma il risultato dipende dall'ordine di esecuzione e dal tipo di import.

```python
# ========== Scenario: import circolare diretto ==========

# modulo_a.py
from modulo_b import funzione_b  # durante l'import di modulo_a

def funzione_a():
    return "risultato A"

# modulo_b.py
from modulo_a import funzione_a  # circolare!

def funzione_b():
    return funzione_a() + " + B"

# Se si esegue: python modulo_a.py
# ImportError: cannot import name 'funzione_a' from partially initialized module

# ========== Perche accade ==========
# 1. Python inizia a importare modulo_a
# 2. Incontra "from modulo_b import funzione_b" -> inizia a importare modulo_b
# 3. modulo_b incontra "from modulo_a import funzione_a"
# 4. modulo_a e solo PARZIALMENTE inizializzato (funzione_a non e ancora definita)
# 5. -> ImportError o AttributeError

# ========== SOLUZIONE 1: Import lazy (dentro la funzione) ==========
# modulo_b.py (corretto)
def funzione_b():
    from modulo_a import funzione_a  # importato solo quando serve
    return funzione_a() + " + B"

# ========== SOLUZIONE 2: Import del modulo intero ==========
# modulo_b.py (corretto)
import modulo_a  # importa il modulo, non l'attributo

def funzione_b():
    return modulo_a.funzione_a() + " + B"  # risolto a runtime

# ========== SOLUZIONE 3: TYPE_CHECKING per i type hints ==========
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modulo_a import ClasseA  # importato solo dal type checker

def funzione_b(obj: "ClasseA") -> str:
    return str(obj)

# ========== SOLUZIONE 4: Estrarre le dipendenze comuni ==========
# modulo_comune.py  <- nuova interfaccia condivisa
# modulo_a.py       <- importa da modulo_comune
# modulo_b.py       <- importa da modulo_comune

# ========== Diagnosi degli import circolari ==========
# python -v script.py  — mostra l'ordine degli import
# python -c "import modulo_a" 2>&1 | grep "import"  — traccia gli import
```

### Confronto tra `is` e `==`

```python
# `is` confronta l'IDENTITA (stesso oggetto in memoria)
# `==` confronta l'UGUAGLIANZA (stesso valore)

a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)  # True — stesso contenuto
print(a is b)  # False — oggetti diversi in memoria

# La trappola degli interi piccoli (integer interning)
x = 256
y = 256
print(x is y)  # True — Python "interna" gli interi da -5 a 256

x = 257
y = 257
print(x is y)  # False (o True nel REPL — dipende dall'implementazione!)
# MAI usare `is` per confrontare valori numerici

# La trappola delle stringhe (string interning)
a = "hello"
b = "hello"
print(a is b)  # True — Python interna le stringhe brevi

a = "hello world!"
b = "hello world!"
print(a is b)  # Potrebbe essere False — non garantito

# REGOLA: usare `is` SOLO per None, True, False e singleton espliciti
if risultato is None:      # CORRETTO
    ...
if risultato == None:      # SBAGLIATO — funziona ma non e idiomatico
    ...
```

### Scope e la Regola LEGB

```python
# Python risolve i nomi con la regola LEGB:
# Local -> Enclosing -> Global -> Built-in

x = "globale"

def funzione_esterna():
    x = "enclosing"

    def funzione_interna():
        # x = "locale"  # se decommentato, shadowing
        print(x)  # "enclosing" — cerca in L, non trova, va a E

    funzione_interna()

# La trappola di UnboundLocalError
contatore = 0

def incrementa():
    contatore += 1  # UnboundLocalError!
    # Python vede l'assegnamento e tratta contatore come locale
    # Ma contatore locale non e ancora stato assegnato -> errore

# SOLUZIONE 1: global (da evitare quando possibile)
def incrementa_global():
    global contatore
    contatore += 1

# SOLUZIONE 2: nonlocal (per closure)
def crea_contatore():
    contatore = 0
    def incrementa():
        nonlocal contatore
        contatore += 1
        return contatore
    return incrementa

# SOLUZIONE 3: usare un oggetto mutabile (pattern piu pulito)
class Contatore:
    def __init__(self):
        self.valore = 0

    def incrementa(self):
        self.valore += 1
        return self.valore
```

### Copia Superficiale vs Profonda

```python
import copy

# Lista di liste — la copia superficiale condivide i riferimenti interni
originale = [[1, 2], [3, 4], [5, 6]]

# Copia superficiale (shallow copy) — copia la lista esterna, non le interne
copia_shallow = originale.copy()  # oppure list(originale) o originale[:]
copia_shallow[0].append(99)
print(originale[0])  # [1, 2, 99] — modificato anche l'originale!

# Copia profonda (deep copy) — copia ricorsivamente tutto
originale2 = [[1, 2], [3, 4], [5, 6]]
copia_deep = copy.deepcopy(originale2)
copia_deep[0].append(99)
print(originale2[0])  # [1, 2] — l'originale e intatto

# ATTENZIONE: lo slicing fa copia superficiale
matrice = [[0]*3 for _ in range(3)]  # CORRETTO
matrice_bug = [[0]*3] * 3  # BUG! Tre riferimenti alla STESSA lista

matrice_bug[0][0] = 1
print(matrice_bug)  # [[1, 0, 0], [1, 0, 0], [1, 0, 0]] — tutte modificate!

# I dizionari hanno lo stesso problema
config = {"database": {"host": "localhost", "porta": 5432}}
config_copia = config.copy()  # shallow!
config_copia["database"]["porta"] = 3306
print(config["database"]["porta"])  # 3306 — modificato anche l'originale!

# SOLUZIONE: usare copy.deepcopy() per strutture annidate
config_sicura = copy.deepcopy(config)
```

---

## Profiling Recipes

Il profiling e il processo sistematico di misurazione delle prestazioni del codice per identificare i colli di bottiglia. Questa sezione fornisce ricette pratiche per i principali strumenti di profiling Python, organizzate in un workflow progressivo dal macro al micro.

### Workflow di Profiling Raccomandato

Il profiling efficace segue un approccio stratificato: si parte da una visione d'insieme per poi zoomare sui punti critici. L'errore piu comune e ottimizzare prima di misurare.

```
1. IDENTIFICARE il problema        → py-spy / pyinstrument (sampling, overhead minimo)
2. QUANTIFICARE i bottleneck       → cProfile / yappi (deterministico, per-function)
3. ANALIZZARE riga per riga        → line_profiler (per le funzioni critiche)
4. MISURARE CPU + Memoria insieme  → Scalene (profiling completo)
5. OTTIMIZZARE e VERIFICARE        → benchmark con timeit / pytest-benchmark
```

### cProfile — Profiling Deterministico

`cProfile` e il profiler deterministico della libreria standard. Misura il tempo di esecuzione di ogni chiamata di funzione con precisione, ma introduce un overhead significativo (tipicamente 2-5x rallentamento).

```python
# Uso base dalla riga di comando
# python -m cProfile -s cumulative script.py

# Uso programmatico con output ordinato
import cProfile
import pstats
from io import StringIO

def profila_funzione(func, *args, **kwargs):
    """Profila una funzione e stampa le statistiche ordinate."""
    profiler = cProfile.Profile()
    profiler.enable()
    risultato = func(*args, **kwargs)
    profiler.disable()

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # prime 20 funzioni
    print(stream.getvalue())
    return risultato

# Salvataggio per analisi successiva
def profila_e_salva(func, output_file="profile.prof"):
    """Profila e salva i risultati per snakeviz o gprof2dot."""
    profiler = cProfile.Profile()
    profiler.enable()
    func()
    profiler.disable()
    profiler.dump_stats(output_file)
    # Visualizzare con: snakeviz profile.prof
    # O con: gprof2dot -f pstats profile.prof | dot -Tpng -o profilo.png

# Context manager per profiling di sezioni specifiche
import contextlib

@contextlib.contextmanager
def profila_sezione(nome="sezione"):
    """Context manager per profilare un blocco di codice."""
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield profiler
    finally:
        profiler.disable()
        stats = pstats.Stats(profiler)
        print(f"\n--- Profilo: {nome} ---")
        stats.sort_stats("cumulative")
        stats.print_stats(10)

# Uso:
with profila_sezione("elaborazione_dati"):
    risultato = elabora_dataset_grande(dati)
```

**Interpretare l'output di cProfile.**

| Colonna | Significato |
|---------|-------------|
| `ncalls` | Numero di chiamate alla funzione |
| `tottime` | Tempo totale speso nella funzione (escluse le sotto-chiamate) |
| `percall` | tottime / ncalls |
| `cumtime` | Tempo cumulativo (incluse le sotto-chiamate) |
| `percall` (seconda) | cumtime / ncalls |
| `filename:lineno(function)` | Posizione della funzione |

La colonna piu utile e `cumtime` ordinata in modo decrescente: identifica le funzioni che consumano piu tempo complessivo.

### line_profiler — Profiling Riga per Riga

`line_profiler` mostra il tempo speso su ogni singola riga di una funzione. Ideale per ottimizzare le funzioni gia identificate come bottleneck da cProfile.

```python
# pip install line_profiler

# Decorare le funzioni da profilare con @profile
# NOTA: il decoratore @profile viene iniettato da line_profiler, non va importato

# script.py
@profile
def calcola_statistiche(dati):
    media = sum(dati) / len(dati)
    varianza = sum((x - media) ** 2 for x in dati) / len(dati)
    deviazione = varianza ** 0.5
    ordinati = sorted(dati)
    mediana = ordinati[len(ordinati) // 2]
    return {"media": media, "deviazione": deviazione, "mediana": mediana}

# Esecuzione: kernprof -l -v script.py
# Output:
# Line #  Hits  Time  Per Hit  % Time  Line Contents
# ====================================================
#      3     1   0.2    0.2      0.1   media = sum(dati) / len(dati)
#      4     1  45.3   45.3     52.1   varianza = sum((x-media)**2 for x in dati)...
#      5     1   0.1    0.1      0.1   deviazione = varianza ** 0.5
#      6     1  38.7   38.7     44.5   ordinati = sorted(dati)
#      7     1   0.1    0.1      0.1   mediana = ordinati[len(ordinati) // 2]

# Uso programmatico (senza il decoratore magico @profile)
from line_profiler import LineProfiler

def profila_riga_per_riga(func, *args, **kwargs):
    profiler = LineProfiler()
    profiler.add_function(func)
    profiler.enable_by_count()
    risultato = func(*args, **kwargs)
    profiler.disable_by_count()
    profiler.print_stats()
    return risultato
```

### py-spy — Profiling Sampling Senza Overhead

`py-spy` e un profiler sampling scritto in Rust che si connette a un processo Python in esecuzione senza modificarlo e senza introdurre overhead misurabile. E lo strumento ideale per il profiling in produzione.

```bash
# Installazione
# pip install py-spy

# Profiling di uno script
py-spy record -o profilo.svg -- python script.py

# Connessione a un processo Python gia in esecuzione
py-spy record -o profilo.svg --pid 12345

# Visualizzazione in tempo reale (tipo top)
py-spy top --pid 12345

# Generare un flame graph SVG interattivo
py-spy record -o flamegraph.svg --format speedscope -- python app.py

# Profiling con durata limitata
py-spy record -o profilo.svg --duration 30 --pid 12345

# Profiling di tutti i thread
py-spy dump --pid 12345

# Profiling nativo (include estensioni C)
py-spy record --native -o profilo.svg -- python script.py
```

**Interpretare i flame graph generati da py-spy.**

I flame graph si leggono dal basso verso l'alto. La larghezza di ogni barra rappresenta la proporzione di tempo speso in quella funzione. Le barre piu larghe in cima allo stack sono i punti caldi da ottimizzare. I flame graph sono particolarmente utili per identificare call chain inaspettate e funzioni che consumano tempo in modo non ovvio.

### Scalene — Profiler CPU + Memoria Unificato

`Scalene` e il profiler Python piu completo disponibile nel 2025. Combina profiling CPU (distinguendo tra tempo Python e tempo nativo/C), profiling memoria (allocazioni e deallocazioni riga per riga), e identificazione di colli di bottiglia I/O — tutto con overhead ridotto.

```bash
# pip install scalene

# Uso base
scalene script.py

# Output HTML interattivo
scalene --html --outfile profilo.html script.py

# Profiling solo CPU
scalene --cpu-only script.py

# Profiling con soglia minima (ignora funzioni che usano < 1% del tempo)
scalene --cpu-percent-threshold 1 script.py

# Profilare solo moduli specifici (esclude librerie di terze parti)
scalene --profile-only mio_pacchetto script.py
```

**Interpretare l'output di Scalene.**

Scalene divide il tempo CPU in tre categorie:
- **Python**: tempo speso nell'interprete Python puro
- **Native**: tempo speso in estensioni C/C++ (numpy, pandas, ecc.)
- **System**: tempo speso in chiamate di sistema (I/O, syscall)

Se la colonna "Python" domina, l'ottimizzazione algoritmica puo aiutare. Se "Native" domina, il codice e gia efficiente dal punto di vista Python. Se "System" domina, il bottleneck e l'I/O.

### Benchmark con timeit e pytest-benchmark

```python
# timeit — micro-benchmark dalla riga di comando
# python -m timeit -s "dati = list(range(1000))" "sorted(dati)"
# python -m timeit -s "dati = list(range(1000))" "dati.sort()"

# timeit — uso programmatico
import timeit

# Confrontare due approcci
tempo_list_comp = timeit.timeit(
    "[x**2 for x in range(1000)]",
    number=10_000,
)
tempo_map = timeit.timeit(
    "list(map(lambda x: x**2, range(1000)))",
    number=10_000,
)
print(f"List comprehension: {tempo_list_comp:.3f}s")
print(f"map + lambda:       {tempo_map:.3f}s")

# pytest-benchmark — benchmark integrati nei test
# pip install pytest-benchmark

# tests/test_performance.py
def test_ordinamento_benchmark(benchmark):
    dati = list(range(10_000, 0, -1))
    risultato = benchmark(sorted, dati)
    assert risultato == list(range(1, 10_001))
```

---

## Rilevamento Memory Leak

I memory leak in Python sono meno comuni che nei linguaggi con gestione manuale della memoria, ma si verificano quando il garbage collector non riesce a liberare oggetti che non sono piu necessari — tipicamente a causa di riferimenti circolari con `__del__`, cache non limitate, listener non rimossi, o variabili globali che accumulano dati.

### tracemalloc — Tracciamento Allocazioni nella Stdlib

`tracemalloc` e il modulo della libreria standard per tracciare le allocazioni di memoria. Permette di confrontare snapshot di memoria in momenti diversi per identificare dove la memoria cresce.

```python
import tracemalloc

# Avviare il tracciamento (nframes=25 per stack trace piu profondi)
tracemalloc.start(25)

# ... eseguire il codice sospetto ...

# Scattare uno snapshot
snapshot1 = tracemalloc.take_snapshot()

# ... eseguire altra operazione sospetta ...

snapshot2 = tracemalloc.take_snapshot()

# Confrontare i due snapshot — mostra dove la memoria e cresciuta
statistiche = snapshot2.compare_to(snapshot1, "lineno")
print("\n=== TOP 10 incrementi di memoria ===")
for stat in statistiche[:10]:
    print(stat)

# Per dettaglio maggiore: raggruppare per traceback completo
statistiche_traceback = snapshot2.compare_to(snapshot1, "traceback")
for stat in statistiche_traceback[:5]:
    print(f"\n{stat}")
    for riga in stat.traceback.format():
        print(f"  {riga}")

# Filtrare per escludere le allocazioni del modulo tracemalloc stesso
from tracemalloc import Filter

filtri = [
    Filter(False, tracemalloc.__file__),  # escludi tracemalloc
    Filter(False, "<frozen importlib._bootstrap>"),  # escludi importlib
]
snapshot_filtrato = snapshot2.filter_traces(filtri)
for stat in snapshot_filtrato.statistics("lineno")[:10]:
    print(stat)

# Monitoraggio continuo in un'applicazione long-running
import threading
import time

def monitor_memoria(intervallo_secondi=60, soglia_mb=500):
    """Thread di monitoraggio memoria che logga le allocazioni principali."""
    tracemalloc.start(10)
    snapshot_precedente = tracemalloc.take_snapshot()

    while True:
        time.sleep(intervallo_secondi)
        snapshot_corrente = tracemalloc.take_snapshot()
        statistiche = snapshot_corrente.compare_to(snapshot_precedente, "lineno")

        # Loggare solo se ci sono incrementi significativi
        incrementi_significativi = [
            s for s in statistiche
            if s.size_diff > 1_000_000  # > 1 MB di incremento
        ]
        if incrementi_significativi:
            for stat in incrementi_significativi[:5]:
                logging.warning("Memory growth: %s", stat)

        corrente, picco = tracemalloc.get_traced_memory()
        if picco / 1_000_000 > soglia_mb:
            logging.critical(
                "Memoria: corrente=%.1fMB, picco=%.1fMB — SOGLIA SUPERATA",
                corrente / 1_000_000, picco / 1_000_000,
            )

        snapshot_precedente = snapshot_corrente
```

### objgraph — Visualizzazione dei Grafi di Riferimento

`objgraph` e una libreria specializzata nella visualizzazione delle relazioni tra oggetti Python. Genera diagrammi che mostrano perche un oggetto non viene deallocato dal garbage collector.

```python
# pip install objgraph

import objgraph

# Mostrare i tipi di oggetto piu comuni in memoria
objgraph.show_most_common_types(limit=15)
# Output:
# dict                   12345
# list                    8901
# tuple                   6789
# function                3456
# ...

# Tracciare la crescita degli oggetti nel tempo
objgraph.show_growth(limit=10)
# ... eseguire operazioni ...
objgraph.show_growth(limit=10)  # mostra solo i tipi che sono cresciuti

# Trovare oggetti specifici che non vengono liberati
# Utile quando si sospetta un leak in una classe specifica
oggetti_sospetti = objgraph.by_type("MioOggettoGrande")
print(f"Istanze di MioOggettoGrande in memoria: {len(oggetti_sospetti)}")

# Visualizzare la catena di riferimenti che mantiene vivo un oggetto
# Richiede graphviz: apt install graphviz
if oggetti_sospetti:
    objgraph.show_backrefs(
        oggetti_sospetti[0],
        max_depth=5,
        filename="riferimenti.png",
    )

# Trovare riferimenti circolari
import gc
gc.collect()  # forzare la garbage collection
oggetti_irraggiungibili = gc.garbage
print(f"Oggetti in gc.garbage (cicli con __del__): {len(oggetti_irraggiungibili)}")
```

### Pympler — Analisi Approfondita del Consumo di Memoria

`Pympler` offre strumenti complementari per misurare la dimensione reale degli oggetti (inclusi gli oggetti referenziati) e monitorare la crescita della memoria nel tempo.

```python
# pip install pympler

from pympler import asizeof, tracker, muppy

# asizeof: dimensione REALE di un oggetto (inclusi tutti i sotto-oggetti)
import sys

lista = [{"chiave": "valore" * 100} for _ in range(1000)]

# sys.getsizeof conta solo l'oggetto diretto, non il contenuto
print(f"sys.getsizeof: {sys.getsizeof(lista):,} bytes")  # solo la lista esterna

# asizeof conta ricorsivamente tutto
print(f"pympler asizeof: {asizeof.asizeof(lista):,} bytes")  # lista + dicts + stringhe

# tracker: monitorare la crescita nel tempo
tr = tracker.SummaryTracker()
# ... eseguire operazioni ...
tr.print_diff()  # mostra cosa e cresciuto tra una chiamata e l'altra

# muppy: ispezionare tutti gli oggetti in memoria
tutti_gli_oggetti = muppy.get_objects()
print(f"Oggetti totali in memoria: {len(tutti_gli_oggetti):,}")
```

### Pattern Comuni di Memory Leak e Soluzioni

```python
# ========== LEAK 1: Cache senza limiti ==========
# PROBLEMA
_cache = {}

def calcola_costoso(chiave):
    if chiave not in _cache:
        _cache[chiave] = operazione_costosa(chiave)  # la cache cresce all'infinito
    return _cache[chiave]

# SOLUZIONE: usare lru_cache con maxsize
from functools import lru_cache

@lru_cache(maxsize=1024)
def calcola_costoso_limitato(chiave):
    return operazione_costosa(chiave)

# ========== LEAK 2: Listener/callback non rimossi ==========
# PROBLEMA
class EventEmitter:
    def __init__(self):
        self._listeners = []

    def on(self, callback):
        self._listeners.append(callback)  # mantiene un riferimento forte

# SOLUZIONE: usare weakref
import weakref

class EventEmitterSicuro:
    def __init__(self):
        self._listeners = []

    def on(self, callback):
        self._listeners.append(weakref.ref(callback))

    def emit(self, *args):
        vivi = []
        for ref in self._listeners:
            callback = ref()
            if callback is not None:
                callback(*args)
                vivi.append(ref)
        self._listeners = vivi  # rimuove i riferimenti morti

# ========== LEAK 3: Riferimenti circolari con __del__ ==========
# PROBLEMA: il gc non puo raccogliere cicli che hanno __del__
class Nodo:
    def __init__(self, nome):
        self.nome = nome
        self.figlio = None
        self.genitore = None

    def __del__(self):
        print(f"Distruzione di {self.nome}")

a = Nodo("A")
b = Nodo("B")
a.figlio = b
b.genitore = a  # ciclo! Con __del__, gc non puo raccoglierli

# SOLUZIONE: usare weakref per il back-reference
class NodoSicuro:
    def __init__(self, nome):
        self.nome = nome
        self.figlio = None
        self._genitore_ref = None

    @property
    def genitore(self):
        return self._genitore_ref() if self._genitore_ref else None

    @genitore.setter
    def genitore(self, valore):
        self._genitore_ref = weakref.ref(valore) if valore else None
```

---

## GIL e Problematiche di Concorrenza

Il Global Interpreter Lock (GIL) e il meccanismo di CPython che permette a un solo thread di eseguire bytecode Python alla volta. Comprendere il GIL e fondamentale per diagnosticare problemi di performance nelle applicazioni multi-thread.

### Come Funziona il GIL

Il GIL e un mutex che protegge l'accesso agli oggetti Python, impedendo la corruzione della memoria durante le operazioni concorrenti. Viene rilasciato durante le operazioni di I/O (lettura file, chiamate di rete, sleep), ma e mantenuto durante l'esecuzione di bytecode Python puro.

```python
import threading
import time

# ESEMPIO: il GIL limita il parallelismo CPU-bound
def lavoro_cpu(n):
    """Calcolo intensivo — il GIL impedisce il parallelismo reale."""
    totale = 0
    for i in range(n):
        totale += i * i
    return totale

# Single-thread
inizio = time.perf_counter()
lavoro_cpu(10_000_000)
lavoro_cpu(10_000_000)
print(f"Sequenziale: {time.perf_counter() - inizio:.2f}s")

# Multi-thread — NON piu veloce a causa del GIL
inizio = time.perf_counter()
t1 = threading.Thread(target=lavoro_cpu, args=(10_000_000,))
t2 = threading.Thread(target=lavoro_cpu, args=(10_000_000,))
t1.start(); t2.start()
t1.join(); t2.join()
print(f"Multi-thread: {time.perf_counter() - inizio:.2f}s")
# Tipicamente uguale o piu lento del sequenziale!
```

### Workaround Classici per il GIL

```python
# ========== SOLUZIONE 1: multiprocessing per lavoro CPU-bound ==========
from multiprocessing import Pool
import os

def lavoro_cpu_pesante(dati):
    return sum(x * x for x in dati)

if __name__ == "__main__":
    dati_suddivisi = [range(i, i + 1_000_000) for i in range(0, 4_000_000, 1_000_000)]

    with Pool(processes=os.cpu_count()) as pool:
        risultati = pool.map(lavoro_cpu_pesante, dati_suddivisi)
    print(f"Totale: {sum(risultati)}")

# ========== SOLUZIONE 2: concurrent.futures per interfaccia unificata ==========
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

# CPU-bound: ProcessPoolExecutor (processi separati, no GIL)
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(lavoro_cpu, 10_000_000) for _ in range(4)]
    risultati = [f.result() for f in futures]

# I/O-bound: ThreadPoolExecutor (il GIL viene rilasciato durante I/O)
import urllib.request

def scarica(url):
    with urllib.request.urlopen(url) as risposta:
        return len(risposta.read())

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(scarica, url) for url in urls]
    dimensioni = [f.result() for f in futures]

# ========== SOLUZIONE 3: estensioni C/Cython che rilasciano il GIL ==========
# In estensioni C, si puo rilasciare il GIL con:
# Py_BEGIN_ALLOW_THREADS
# ... codice C che non tocca oggetti Python ...
# Py_END_ALLOW_THREADS

# In Cython:
# with nogil:
#     ... codice Cython senza accesso a oggetti Python ...

# ========== SOLUZIONE 4: asyncio per I/O-bound concorrente ==========
import asyncio
import aiohttp

async def scarica_async(session, url):
    async with session.get(url) as risposta:
        return len(await risposta.read())

async def scarica_tutti(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [scarica_async(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

### Python 3.13+ e il Free-Threading (No-GIL)

A partire da Python 3.13, CPython supporta una build sperimentale senza GIL (PEP 703). In Python 3.14, il free-threading non e piu considerato sperimentale (PEP 779), sebbene non sia ancora la build di default.

```python
# Verificare se la build corrente supporta il free-threading
import sys
print(sys.flags)  # cercare il flag "nogil"

# Con Python 3.13+ free-threaded:
# - I thread possono eseguire bytecode in parallelo su core diversi
# - Il reference counting usa contatori biased per ridurre l'overhead atomico
# - Il GIL puo essere disabilitato con PYTHON_GIL=0 o -X gil=0

# Installazione della build free-threaded
# macOS/Windows: installer ufficiale con opzione "free-threaded"
# Linux:
# sudo add-apt-repository ppa:deadsnakes/ppa
# sudo apt install python3.13-nogil

# Verificare la compatibilita delle librerie di terze parti
# Molte estensioni C non sono ancora compatibili con il free-threading
# Controllare: https://py-free-threading.github.io/

# Trade-off della build free-threaded:
# - Codice single-thread ~5-10% piu lento (overhead per il locking fine-grained)
# - Codice multi-thread CPU-bound significativamente piu veloce
# - Non tutte le librerie C sono compatibili (numpy, pandas in fase di adattamento)
# - In produzione: valutare attentamente prima di adottare
```

---

## Troubleshooting Encoding e Unicode

I problemi di encoding sono tra i piu frustranti da diagnosticare perche si manifestano in modo imprevedibile — spesso funzionano in sviluppo e falliscono in produzione, o su un sistema operativo ma non su un altro.

### Fondamenti: bytes vs str in Python 3

```python
# In Python 3, str e SEMPRE Unicode, bytes e SEMPRE una sequenza di byte
testo = "ciao mondo"        # str — sequenza di code point Unicode
raw = b"ciao mondo"         # bytes — sequenza di byte grezzi
print(type(testo))          # <class 'str'>
print(type(raw))            # <class 'bytes'>

# Conversione esplicita: encode e decode
byte_utf8 = testo.encode("utf-8")        # str -> bytes
testo_da_bytes = byte_utf8.decode("utf-8")  # bytes -> str

# L'errore si verifica quando l'encoding non corrisponde
byte_latin1 = "café".encode("utf-8")
try:
    byte_latin1.decode("ascii")  # UnicodeDecodeError!
except UnicodeDecodeError as e:
    print(f"Errore: {e}")
    # 'ascii' codec can't decode byte 0xc3 in position 3
```

### Diagnosi e Risoluzione di UnicodeDecodeError

```python
# ========== Strategia 1: Identificare l'encoding reale ==========
# pip install chardet

import chardet

with open("file_misterioso.txt", "rb") as f:
    raw = f.read()
    rilevamento = chardet.detect(raw)
    print(rilevamento)
    # {'encoding': 'ISO-8859-1', 'confidence': 0.73, 'language': 'Italian'}

# Poi aprire con l'encoding corretto
with open("file_misterioso.txt", encoding=rilevamento["encoding"]) as f:
    testo = f.read()

# ========== Strategia 2: Gestione errori controllata ==========
# errors="replace" — sostituisce i byte non decodificabili con U+FFFD
with open("file.txt", encoding="utf-8", errors="replace") as f:
    testo = f.read()  # i caratteri non validi diventano '?'

# errors="ignore" — ignora i byte non decodificabili (rischio perdita dati)
with open("file.txt", encoding="utf-8", errors="ignore") as f:
    testo = f.read()

# errors="surrogateescape" — utile per i nomi di file su filesystem
import os
for nome in os.listdir(b"/tmp"):
    nome_str = nome.decode("utf-8", errors="surrogateescape")

# ========== Strategia 3: UTF-8 globale ==========
# Python 3.15+ adottera UTF-8 come encoding di default su tutte le piattaforme
# Per ora, forzare UTF-8 globalmente:
# PYTHONUTF8=1 python script.py
# oppure: python -X utf8 script.py

# ========== Strategia 4: Normalizzazione Unicode ==========
import unicodedata

# Due modi di rappresentare "e" con accento:
e_composta = "é"        # e — un singolo code point
e_decomposta = "é"     # e + combining acute accent — due code point

print(e_composta == e_decomposta)  # False! Ma visivamente identici

# Normalizzare per confronto
e_nfc = unicodedata.normalize("NFC", e_decomposta)
print(e_nfc == e_composta)  # True

# REGOLA: normalizzare SEMPRE in NFC all'ingresso nel sistema
def normalizza_input(testo: str) -> str:
    return unicodedata.normalize("NFC", testo)
```

### Encoding nei Contesti Comuni

```python
# ========== File CSV con encoding misto ==========
import csv

# PROBLEMA: CSV esportato da Excel in Italia usa spesso cp1252, non UTF-8
try:
    with open("dati.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        righe = list(reader)
except UnicodeDecodeError:
    with open("dati.csv", encoding="cp1252") as f:
        reader = csv.reader(f)
        righe = list(reader)

# ========== Risposte HTTP ==========
import urllib.request

with urllib.request.urlopen("https://example.com") as risposta:
    # L'encoding e nell'header Content-Type
    content_type = risposta.headers.get_content_charset()
    encoding = content_type or "utf-8"
    testo = risposta.read().decode(encoding)

# ========== Database ==========
# Assicurarsi che la connessione al database usi UTF-8
# PostgreSQL: CREATE DATABASE mydb ENCODING 'UTF8';
# MySQL: ALTER DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# SQLite: usa UTF-8 di default

# ========== JSON ==========
import json

# json.dumps produce str (Unicode), non bytes
dati = {"nome": "Rene Descartes", "citta": "La Haye en Touraine"}
json_str = json.dumps(dati, ensure_ascii=False)  # mantiene i caratteri Unicode
# ensure_ascii=False evita l'escape é -> e
```

---

## Datetime e Timezone — Trappole Comuni

La gestione di date, orari e fusi orari e una delle aree piu insidiose della programmazione. Python offre gli strumenti giusti, ma le trappole sono numerose e i bug spesso si manifestano solo con dati provenienti da fusi orari diversi.

### Naive vs Aware Datetime

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# NAIVE: datetime senza informazioni di timezone
# Non sai in quale fuso orario si trova — e una bomba a orologeria
dt_naive = datetime(2026, 3, 15, 14, 30)
print(dt_naive.tzinfo)  # None

# AWARE: datetime con timezone esplicita
dt_aware = datetime(2026, 3, 15, 14, 30, tzinfo=timezone.utc)
print(dt_aware.tzinfo)  # UTC

# REGOLA FONDAMENTALE: usare SEMPRE datetime aware
# REGOLA 2: salvare SEMPRE in UTC, convertire solo per la visualizzazione

# Creare datetime aware con zoneinfo (Python 3.9+, stdlib)
roma = ZoneInfo("Europe/Rome")
dt_roma = datetime(2026, 3, 15, 14, 30, tzinfo=roma)
print(dt_roma)  # 2026-03-15 14:30:00+01:00

# Convertire tra fusi orari
dt_utc = dt_roma.astimezone(timezone.utc)
print(dt_utc)  # 2026-03-15 13:30:00+00:00

dt_tokyo = dt_roma.astimezone(ZoneInfo("Asia/Tokyo"))
print(dt_tokyo)  # 2026-03-15 22:30:00+09:00
```

### Trappole Specifiche

```python
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# ========== TRAPPOLA 1: datetime.now() senza timezone ==========
# SBAGLIATO — produce un datetime naive
adesso_sbagliato = datetime.now()

# CORRETTO — specificare sempre il timezone
adesso_utc = datetime.now(timezone.utc)
adesso_roma = datetime.now(ZoneInfo("Europe/Rome"))

# ========== TRAPPOLA 2: replace() non converte, solo etichetta ==========
dt_naive = datetime(2026, 6, 15, 10, 0)

# SBAGLIATO — etichetta come UTC senza convertire
dt_falso_utc = dt_naive.replace(tzinfo=timezone.utc)
# Se dt_naive era ora locale Roma (CEST, UTC+2), questo e SBAGLIATO di 2 ore!

# CORRETTO — localizzare prima, poi convertire
roma = ZoneInfo("Europe/Rome")
dt_roma = dt_naive.replace(tzinfo=roma)  # "questo era ora di Roma"
dt_utc = dt_roma.astimezone(timezone.utc)  # converti a UTC

# ========== TRAPPOLA 3: Confronto tra naive e aware ==========
dt_naive = datetime(2026, 1, 1, 12, 0)
dt_aware = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

try:
    risultato = dt_naive > dt_aware  # TypeError in Python 3!
except TypeError as e:
    print(f"Errore: {e}")
    # can't compare offset-naive and offset-aware datetimes

# ========== TRAPPOLA 4: Ora legale (DST) ==========
roma = ZoneInfo("Europe/Rome")

# L'ultima domenica di marzo, alle 2:00 si passa alle 3:00 (ora legale)
# Le 2:30 di quella notte NON ESISTONO
dt_inesistente = datetime(2026, 3, 29, 2, 30, tzinfo=roma)
# zoneinfo gestisce correttamente, ma il risultato potrebbe non essere quello atteso

# L'ultima domenica di ottobre, alle 3:00 si torna alle 2:00
# Le 2:30 di quella notte ESISTONO DUE VOLTE
# Usare fold=0 (prima occorrenza) o fold=1 (seconda occorrenza)
dt_ambiguo = datetime(2026, 10, 25, 2, 30, tzinfo=roma, fold=0)  # ora legale
dt_ambiguo2 = datetime(2026, 10, 25, 2, 30, tzinfo=roma, fold=1)  # ora solare

# ========== TRAPPOLA 5: Non usare pytz nei nuovi progetti ==========
# pytz ha un'API NON compatibile con il costruttore datetime
# import pytz
# roma_pytz = pytz.timezone("Europe/Rome")
# SBAGLIATO: datetime(2026, 1, 1, tzinfo=roma_pytz)  # produce offset errato!
# pytz richiede .localize(): roma_pytz.localize(datetime(2026, 1, 1))

# Da Python 3.9: usare SOLO zoneinfo (stdlib), non pytz

# ========== TRAPPOLA 6: Serializzazione ISO 8601 ==========
# ISO 8601 e lo standard per serializzare date con timezone
dt = datetime.now(timezone.utc)
iso_str = dt.isoformat()  # '2026-05-24T10:30:00+00:00'

# Deserializzazione
dt_parsed = datetime.fromisoformat(iso_str)  # Python 3.7+ (parziale), 3.11+ (completo)
```

---

## Debugging Asyncio

Il debugging di codice asincrono presenta sfide uniche: le coroutine possono essere sospese in qualsiasi punto di `await`, gli errori possono essere silenziati se un `Task` non viene atteso, e i traceback possono essere frammentati.

### Modalita Debug di asyncio

```python
import asyncio
import logging

# ========== Abilitare la modalita debug ==========
# Metodo 1: variabile d'ambiente
# PYTHONASYNCIODEBUG=1 python script.py

# Metodo 2: parametro di asyncio.run()
async def main():
    await asyncio.sleep(0.1)

asyncio.run(main(), debug=True)

# Metodo 3: programmatico
loop = asyncio.get_event_loop()
loop.set_debug(True)

# ========== Cosa fa la modalita debug ==========
# 1. Logga le coroutine non attese (forgotten await)
# 2. Logga i callback che impiegano piu di 100ms
# 3. Logga le operazioni I/O lente
# 4. Verifica che le API asyncio siano chiamate dal thread corretto

# Configurare il logging per asyncio
logging.basicConfig(level=logging.DEBUG)
asyncio.get_event_loop().set_debug(True)
```

### Problemi Comuni e Soluzioni

```python
import asyncio

# ========== PROBLEMA 1: Coroutine non attesa (forgotten await) ==========
async def recupera_dati():
    await asyncio.sleep(0.1)
    return {"risultato": 42}

async def main_bug():
    # BUG: la coroutine viene creata ma MAI eseguita
    dati = recupera_dati()  # manca await!
    # RuntimeWarning: coroutine 'recupera_dati' was never awaited
    print(dati)  # <coroutine object recupera_dati at 0x...>

async def main_corretto():
    dati = await recupera_dati()  # con await
    print(dati)  # {'risultato': 42}

# ========== PROBLEMA 2: Eccezione silenziata in un Task ==========
async def task_che_fallisce():
    await asyncio.sleep(0.1)
    raise ValueError("Errore nel task!")

async def main_eccezione_silenziata():
    # BUG: il task viene creato ma l'eccezione non viene mai raccolta
    task = asyncio.create_task(task_che_fallisce())
    await asyncio.sleep(1)
    # L'eccezione viene stampata solo quando il task viene garbage-collected
    # "Task exception was never retrieved"

async def main_eccezione_gestita():
    task = asyncio.create_task(task_che_fallisce())
    try:
        await task  # l'eccezione viene propagata qui
    except ValueError as e:
        print(f"Task fallito: {e}")

# Gestione centralizzata con TaskGroup (Python 3.11+)
async def main_task_group():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(recupera_dati())
        task2 = tg.create_task(task_che_fallisce())
    # Se un task fallisce, tutti vengono cancellati e l'eccezione viene propagata

# ========== PROBLEMA 3: Blocco dell'event loop ==========
import time

async def blocca_event_loop():
    # BUG: time.sleep() blocca TUTTO l'event loop
    time.sleep(5)  # SBAGLIATO — nessuna altra coroutine puo eseguire

async def non_blocca_event_loop():
    # CORRETTO: asyncio.sleep() cede il controllo all'event loop
    await asyncio.sleep(5)

    # Per operazioni CPU-bound, usare run_in_executor
    loop = asyncio.get_event_loop()
    risultato = await loop.run_in_executor(None, operazione_cpu_pesante, dati)

# ========== PROBLEMA 4: Cancellazione non gestita ==========
async def operazione_lunga():
    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        # Pulizia necessaria prima della cancellazione
        print("Operazione cancellata, eseguo cleanup...")
        await chiudi_connessione()
        raise  # IMPORTANTE: ri-lanciare CancelledError

# ========== Python 3.14: Strumenti di introspezione asyncio ==========
# asyncio.capture_call_graph() — cattura il grafo delle chiamate
# sys.remote_exec() — esecuzione remota per debugging di processi asyncio
# Modulo asyncio.tools con funzionalita di ispezione avanzate
```

---

## Debugging in Produzione

Il debugging in produzione richiede strumenti e tecniche specifiche che minimizzano l'impatto sul sistema in esecuzione. Non si puo inserire un breakpoint in un server che gestisce migliaia di richieste al secondo.

### faulthandler — Diagnostica Crash a Livello C

```python
import faulthandler
import signal

# Abilitare faulthandler all'avvio dell'applicazione
faulthandler.enable()

# Equivalente da riga di comando:
# python -X faulthandler app.py
# O con variabile d'ambiente:
# PYTHONFAULTHANDLER=1 python app.py

# Registrare un segnale per il dump dei thread
# Utile per diagnosticare deadlock in produzione
faulthandler.register(signal.SIGUSR1)
# Ora: kill -USR1 <pid> stampa lo stack di tutti i thread

# Dump con timeout — utile per rilevare hang
faulthandler.dump_traceback_later(
    timeout=300,  # 5 minuti
    repeat=True,  # ripeti ogni 5 minuti
    file=open("/var/log/app_traceback.txt", "a"),
)

# faulthandler cattura anche segfault da estensioni C
# Produce un traceback Python anche quando il crash avviene in codice nativo
```

### Remote Debugging con debugpy

```python
# debugpy permette di connettere un debugger VS Code a un processo remoto
# Essenziale per debugging in container Docker o server remoti

# pip install debugpy

# Nel codice dell'applicazione (SOLO in modalita debug)
import os

if os.environ.get("REMOTE_DEBUG") == "1":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Debugger remoto in ascolto sulla porta 5678")
    # Opzionale: attendere la connessione del client
    # debugpy.wait_for_client()

# Dockerfile — esporre la porta di debug
# EXPOSE 5678

# docker-compose.yml — mapping porta
# ports:
#   - "5678:5678"
# environment:
#   - REMOTE_DEBUG=1

# In VS Code, configurare launch.json con "request": "attach"
# e la connessione al container/server remoto
```

### Core Dump e Analisi Post-Mortem

```python
# Abilitare i core dump su Linux
# ulimit -c unlimited
# echo "/tmp/core.%e.%p" > /proc/sys/kernel/core_pattern

# Analizzare un core dump Python con gdb
# gdb python /tmp/core.app.12345
# (gdb) py-bt         — backtrace Python
# (gdb) py-list       — codice sorgente al punto del crash
# (gdb) py-locals     — variabili locali Python

# Per applicazioni in produzione, considerare l'uso di Sentry
# pip install sentry-sdk

import sentry_sdk

sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    traces_sample_rate=0.1,  # campionare il 10% delle transazioni
    profiles_sample_rate=0.1,
    environment="production",
    release="myapp@1.2.3",
)

# Sentry cattura automaticamente le eccezioni non gestite
# e fornisce traceback completi con contesto delle variabili locali
```

### Logging Strutturato per Debugging in Produzione

Il logging ben strutturato e la prima linea di difesa per il debugging in produzione. Un sistema di log efficace permette di ricostruire la sequenza di eventi che ha portato a un errore senza dover riprodurre il problema.

```python
import logging
import json
from datetime import datetime, timezone

# ========== JSON Structured Logging ==========
class JSONFormatter(logging.Formatter):
    """Formatter che produce log in formato JSON per aggregatori (ELK, Datadog)."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Aggiungere campi extra
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        return json.dumps(log_entry)

# Configurazione
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("app")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ========== Context-aware logging con extra ==========
def gestisci_richiesta(request_id: str, user_id: str):
    extra = {"request_id": request_id, "user_id": user_id}
    logger.info("Richiesta ricevuta", extra=extra)
    try:
        risultato = elabora(request_id)
        logger.info("Richiesta completata", extra=extra)
    except Exception:
        logger.exception("Errore nella richiesta", extra=extra)
        raise

# ========== Configurazione per livelli diversi in produzione ==========
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": JSONFormatter},
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO",
        },
        "file_errori": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/app/errori.log",
            "maxBytes": 10_000_000,
            "backupCount": 5,
            "formatter": "json",
            "level": "ERROR",
        },
        "file_debug": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "/var/log/app/debug.log",
            "when": "midnight",
            "backupCount": 7,
            "formatter": "standard",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "app": {"handlers": ["console", "file_errori", "file_debug"], "level": "DEBUG"},
        "sqlalchemy.engine": {"handlers": ["file_debug"], "level": "WARNING"},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

## Conflitti di Dipendenze e Gestione Ambienti

I conflitti di dipendenze sono tra i problemi piu comuni e frustranti nello sviluppo Python. Si verificano quando due o piu pacchetti richiedono versioni incompatibili della stessa dipendenza.

### Diagnosi dei Conflitti con pip

```bash
# Verificare lo stato delle dipendenze installate
pip check
# Output: pacchetto_a 1.0 requires pacchetto_c>=2.0, but you have pacchetto_c 1.5

# Visualizzare l'albero delle dipendenze
# pip install pipdeptree
pipdeptree
pipdeptree --warn fail  # errore in caso di conflitti
pipdeptree -p requests  # albero per un pacchetto specifico
pipdeptree --reverse requests  # chi dipende da requests?

# Trovare versioni compatibili manualmente
pip install "pacchetto_a" "pacchetto_b" --dry-run
# Mostra cosa verrebbe installato senza installare nulla
```

### Gestione Ambienti con uv

```bash
# uv e il gestore di pacchetti Python moderno (2024+), 10-100x piu veloce di pip
# Installazione: curl -LsSf https://astral.sh/uv/install.sh | sh

# Creare un progetto con uv
uv init mio-progetto
cd mio-progetto

# Aggiungere dipendenze (risoluzione automatica dei conflitti)
uv add requests fastapi sqlalchemy
uv add --dev pytest ruff mypy

# Generare il lockfile (risoluzione deterministica)
uv lock

# Installare da lockfile (riproducibilita garantita)
uv sync

# Diagnosticare conflitti
uv pip compile requirements.in --verbose
# Output dettagliato del processo di risoluzione

# Forzare una versione specifica (override)
# In pyproject.toml:
# [tool.uv]
# override-dependencies = ["numpy==1.26.4"]

# Eseguire con un Python specifico
uv run --python 3.12 python script.py
```

### Problemi Comuni di Virtual Environment

```python
# ========== PROBLEMA: "ModuleNotFoundError" dopo aver installato il pacchetto ==========
# Causa 1: il pacchetto e installato nel Python di sistema, non nel venv
import sys
print(sys.executable)   # DEVE puntare al .venv/bin/python
print(sys.prefix)       # DEVE puntare al .venv

# Causa 2: il terminale usa un Python diverso dall'IDE
# Verificare:
# which python && python --version
# which pip && pip --version

# Causa 3: il venv e stato creato con una versione diversa di Python
# Ricreare il venv:
# rm -rf .venv && python3.12 -m venv .venv && source .venv/bin/activate

# ========== PROBLEMA: conflitto tra pip e uv ==========
# Non mescolare pip e uv nello stesso progetto
# Scegliere uno e usare solo quello

# ========== PROBLEMA: pacchetto installato ma import fallisce ==========
# Il nome del pacchetto su PyPI puo differire dal nome di import
# Esempi:
# pip install Pillow         -> import PIL
# pip install python-dateutil -> import dateutil
# pip install scikit-learn    -> import sklearn
# pip install beautifulsoup4  -> import bs4
# pip install opencv-python   -> import cv2

# Trovare il nome di import corretto:
# pip show nome-pacchetto  # campo "Name" vs contenuto della directory
```

---

## Troubleshooting dell'Ambiente: PATH, PYTHONPATH e site-packages

La configurazione dell'ambiente Python e spesso la causa nascosta di errori apparentemente inspiegabili. Comprendere come Python trova i moduli e gli eseguibili e fondamentale per risolvere una vasta categoria di problemi.

### Come Python Trova i Moduli

```python
import sys

# sys.path e la lista delle directory in cui Python cerca i moduli
# L'ordine e importante: il primo match vince
for i, percorso in enumerate(sys.path):
    print(f"{i}: {percorso}")

# Ordine tipico di sys.path:
# 0: "" (directory corrente)
# 1: directory dello script eseguito
# 2: PYTHONPATH (se definito)
# 3: librerie standard (es. /usr/lib/python3.12)
# 4: site-packages del venv (es. .venv/lib/python3.12/site-packages)
# 5: site-packages di sistema

# PYTHONPATH aggiunge directory PRIMA di site-packages
# Utile per progetti non pacchettizzati, ma pericoloso se usato male
# export PYTHONPATH="/path/al/mio/progetto/src:$PYTHONPATH"

# Verificare da dove viene importato un modulo
import requests
print(requests.__file__)  # mostra il percorso del file importato
# Se punta a una directory inattesa, c'e un problema di PATH
```

### Diagnosi dei Problemi di PATH

```bash
# Verificare quale Python sta usando il sistema
which python
which python3
python --version
python3 --version

# Su sistemi con piu installazioni Python
ls -la /usr/bin/python*
ls -la /usr/local/bin/python*

# Verificare il PATH
echo $PATH

# Problema comune: il PATH non include la directory degli script pip
# pip install --user installa in ~/.local/bin (Linux) o ~/Library/Python/X.Y/bin (macOS)
# Se non e nel PATH, i comandi installati non vengono trovati

# SOLUZIONE Linux:
# export PATH="$HOME/.local/bin:$PATH"  # aggiungere a ~/.bashrc

# Verificare PYTHONPATH
echo $PYTHONPATH

# Verificare site-packages
python -m site
# Output:
# sys.path = [...]
# USER_BASE: '/home/utente/.local'
# USER_SITE: '/home/utente/.local/lib/python3.12/site-packages'
# ENABLE_USER_SITE: True

# Trovare la directory site-packages del venv
python -c "import site; print(site.getsitepackages())"
```

### Conflitti tra Installazioni Python Multiple

```bash
# PROBLEMA: "python" e "python3" puntano a versioni diverse
python --version   # Python 3.11.2
python3 --version  # Python 3.12.4

# PROBLEMA: pip installa nel Python sbagliato
pip --version     # pip 24.0 from /usr/lib/python3.11/...
pip3 --version    # pip 24.0 from /usr/lib/python3.12/...

# SOLUZIONE: usare SEMPRE python -m pip (oppure uv)
python3.12 -m pip install pacchetto

# SOLUZIONE DEFINITIVA: usare uv per gestire le versioni Python
uv python install 3.12 3.13
uv python list  # mostra le versioni installate
uv python pin 3.12  # fissa la versione per il progetto corrente

# Verificare se il venv e attivato correttamente
echo $VIRTUAL_ENV  # deve essere non-vuoto quando il venv e attivo
# Se vuoto: source .venv/bin/activate
```

### Troubleshooting site-packages e Pacchetti .pth

```python
# I file .pth in site-packages aggiungono percorsi a sys.path
# Possono causare import inattesi o conflitti

# Trovare tutti i file .pth
import site
import os

for directory in site.getsitepackages():
    if os.path.isdir(directory):
        pth_files = [f for f in os.listdir(directory) if f.endswith(".pth")]
        if pth_files:
            print(f"\n{directory}:")
            for f in pth_files:
                print(f"  {f}")

# Installazioni "editable" (pip install -e .) creano file .pth
# Verificare se un pacchetto e installato in modalita editable
# pip list --editable

# PROBLEMA: un pacchetto installato localmente (editable) sovrascrive
# la versione installata normalmente
# SOLUZIONE: pip uninstall pacchetto && pip install pacchetto
```

---

## Deployment Checklist

Checklist operativa da seguire prima di ogni deployment in produzione. Ogni punto rappresenta una lezione appresa da errori reali in produzione.

### Pre-Deployment

- [ ] Tutti i test passano (unit, integration, e2e)
- [ ] Coverage dei test >= 80%
- [ ] Nessun warning di deprecazione nelle dipendenze
- [ ] Il lockfile (uv.lock / requirements.txt) e aggiornato e committato
- [ ] Le variabili d'ambiente di produzione sono configurate e validate
- [ ] I secrets sono in un vault (non nel codice, non nelle variabili d'ambiente del CI)
- [ ] Le migrazioni del database sono state testate con dati realistici
- [ ] Il logging e configurato correttamente per la produzione (livello INFO, rotazione)
- [ ] Health check endpoint funzionante
- [ ] Rate limiting configurato sugli endpoint pubblici

### Sicurezza

- [ ] Nessun secret hardcoded nel codice (grep per API_KEY, PASSWORD, SECRET, TOKEN)
- [ ] HTTPS obbligatorio (redirect HTTP -> HTTPS)
- [ ] Header di sicurezza configurati (HSTS, X-Content-Type-Options, CSP)
- [ ] CORS configurato con whitelist esplicita
- [ ] Input validation su tutti gli endpoint
- [ ] Autenticazione e autorizzazione verificate per ogni endpoint protetto

### Performance

- [ ] Query database ottimizzate (nessuna N+1, indici appropriati)
- [ ] Caching configurato dove appropriato
- [ ] Connessione pool database configurato con limiti ragionevoli
- [ ] Timeout configurati per tutte le chiamate esterne (HTTP, database, cache)
- [ ] Dimensione massima upload configurata
- [ ] Compressione gzip/brotli abilitata

### Monitoraggio

- [ ] Error tracking configurato (Sentry o equivalente)
- [ ] Metriche applicative esposte (Prometheus, StatsD, o equivalente)
- [ ] Alerting configurato per errori critici (5xx rate, latenza, memoria)
- [ ] Log aggregation funzionante (ELK, Loki, CloudWatch)
- [ ] Dashboard operativa con metriche chiave

### Rollback

- [ ] Procedura di rollback documentata e testata
- [ ] Migrazioni database reversibili
- [ ] Deploy blue/green o canary configurato
- [ ] Backup database recente verificato

---

## Error Monitoring in Produzione

Il monitoring degli errori in produzione e il complemento essenziale del testing: i test verificano i casi noti, il monitoring cattura quelli imprevisti.

### Sentry — Setup Completo

```python
# pip install sentry-sdk

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",  # da variabile d'ambiente!
    environment="production",
    release="myapp@1.2.3",
    traces_sample_rate=0.1,        # campionare il 10% delle transazioni
    profiles_sample_rate=0.1,      # profiling in produzione
    send_default_pii=False,        # NON inviare dati personali
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR),
    ],
    before_send=filtra_eventi_sensibili,
)

def filtra_eventi_sensibili(event, hint):
    """Rimuove dati sensibili prima dell'invio a Sentry."""
    if "request" in event:
        headers = event["request"].get("headers", {})
        # Rimuovere header sensibili
        for header in ["Authorization", "Cookie", "X-API-Key"]:
            headers.pop(header, None)
    return event
```

### Metriche Applicative con structlog

```python
# pip install structlog

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

# Logging strutturato con contesto
logger.info(
    "richiesta_completata",
    endpoint="/api/utenti",
    metodo="GET",
    durata_ms=45.2,
    status_code=200,
    utente_id="user-123",
)

# Il contesto si propaga automaticamente alle sotto-funzioni
structlog.contextvars.bind_contextvars(request_id="req-456")
logger.info("elaborazione_iniziata")  # include automaticamente request_id
```

---

## FAQ

**D: Perche il mio script funziona nel terminale ma non in cron/systemd?**

R: I cron job e i servizi systemd eseguono con un ambiente minimale. Le cause piu comuni sono: (1) PATH diverso — il virtual environment non e attivato; (2) directory di lavoro diversa — i path relativi non funzionano; (3) variabili d'ambiente mancanti. Soluzione: usare path assoluti per tutto, attivare esplicitamente il venv nello script, e definire le variabili d'ambiente nel file .service o nella crontab.

**D: Come faccio a capire quale pacchetto sta causando un conflitto di dipendenze?**

R: Usare `pipdeptree --warn fail` per visualizzare l'albero delle dipendenze con i conflitti evidenziati. Se si usa uv, `uv pip compile --verbose` mostra il processo di risoluzione passo per passo. In ultimo, `pip check` elenca le dipendenze non soddisfatte.

**D: Il mio programma Python consuma sempre piu memoria. Come faccio a trovare il leak?**

R: Seguire questo workflow: (1) abilitare `tracemalloc.start()` all'avvio; (2) dopo un periodo di funzionamento, prendere due snapshot con `tracemalloc.take_snapshot()` e confrontarli con `snapshot2.compare_to(snapshot1, "lineno")`; (3) se serve piu dettaglio, usare `objgraph.show_growth()` per identificare i tipi di oggetto che crescono; (4) usare `objgraph.show_backrefs()` per capire chi mantiene i riferimenti agli oggetti sospetti.

**D: Come profilo un'applicazione Python in produzione senza fermarla?**

R: Usare `py-spy`. Si connette a un processo Python in esecuzione tramite PID senza modificarlo e senza introdurre overhead significativo: `py-spy record --pid 12345 -o profilo.svg`. Per un quadro in tempo reale: `py-spy top --pid 12345`.

**D: Perche ricevo UnicodeDecodeError solo su alcuni file/server?**

R: L'encoding di default dipende dal sistema operativo e dalla locale. Windows usa spesso cp1252, Linux in genere UTF-8. Soluzioni: (1) specificare SEMPRE l'encoding esplicitamente quando si aprono file: `open("file.txt", encoding="utf-8")`; (2) usare `PYTHONUTF8=1` per forzare UTF-8 globalmente; (3) per file con encoding ignoto, usare `chardet.detect()` per identificarlo.

**D: Come faccio a debuggare un'applicazione Python in un container Docker?**

R: Usare `debugpy`. Nel Dockerfile, esporre la porta 5678 e nel codice aggiungere `debugpy.listen(("0.0.0.0", 5678))` condizionato a una variabile d'ambiente. Da VS Code, configurare un launch.json con `"request": "attach"` e la connessione al container. Per un'analisi senza debugger, usare `py-spy` montando `/proc` del container: `docker exec -it container py-spy top --pid 1`.

**D: Il mio test passa localmente ma fallisce nella CI. Come faccio a diagnosticare?**

R: Le cause piu comuni sono: (1) dipendenze di sistema mancanti nella CI (librerie C, font, ecc.); (2) test che dipendono dall'ordine di esecuzione (usare `pytest-randomly` per verificare); (3) test che dipendono dal fuso orario o dalla locale; (4) test che dipendono da risorse di rete; (5) race condition nei test paralleli. Per diagnosticare: eseguire i test con `pytest -x --tb=long -v` nella CI e aggiungere `--randomly-seed=last` per riprodurre l'ordine esatto.

**D: Come gestisco il GIL per applicazioni CPU-bound?**

R: Per lavoro CPU-bound puro, il threading non aiuta a causa del GIL. Le alternative sono: (1) `multiprocessing` o `concurrent.futures.ProcessPoolExecutor` per parallelizzare su piu processi; (2) librerie come `numpy` che rilasciano il GIL nelle operazioni interne; (3) estensioni C/Cython con `nogil`; (4) dalla versione 3.13+, la build free-threaded che disabilita il GIL.

---

## Esercizi

1. **Debug di un memory leak** — Prendi un'applicazione Python long-running (es. un web server di esempio) e introduci deliberatamente un memory leak (lista che cresce, cache senza limiti). Usa `tracemalloc` per identificare il leak, `objgraph` per visualizzare i reference graph, e implementa la correzione. Documenta il processo diagnostico passo per passo.

2. **Profiling di un endpoint lento** — Crea un endpoint API che esegua operazioni inefficienti (N+1 query, loop non vettorizzati, I/O sincrono). Profilalo con `cProfile`, `py-spy` e `line_profiler`. Identifica i 3 bottleneck principali, ottimizza ciascuno e misura il miglioramento. L'endpoint deve diventare almeno 5x piu veloce.

3. **Troubleshooting di import circolari** — Costruisci un progetto con 5 moduli che abbiano dipendenze circolari intenzionali. Documenta l'errore risultante, poi risolvi con almeno 3 tecniche diverse: riorganizzazione dei moduli, import lazy, `TYPE_CHECKING`, dependency injection. Confronta i trade-off di ogni approccio.

4. **Checklist di troubleshooting** — Crea una checklist sistematica per i 10 problemi Python piu comuni (ImportError, TypeError, AttributeError, encoding, performance, memory, deadlock, race condition, dependency conflict, build failure). Per ogni problema: sintomi tipici, strumenti diagnostici, passaggi di risoluzione, e prevenzione.

5. **Riproduzione e fix di un bug da traceback** — Parti da un traceback reale (o simulato) di un'applicazione multi-layer (API → service → repository → database). Senza leggere il codice sorgente inizialmente, analizza il traceback per formulare un'ipotesi. Poi verifica l'ipotesi con un test che riproduca il bug, implementa la fix, e aggiungi un test di regressione.

---

## Letture e Riferimenti

### Fonti primarie

- Python Documentation — *`pdb` — The Python Debugger* — https://docs.python.org/3/library/pdb.html (consultato: 2026-05-24)
- Python Documentation — *`tracemalloc`* — https://docs.python.org/3/library/tracemalloc.html (consultato: 2026-05-24)
- Python Documentation — *`cProfile`* — https://docs.python.org/3/library/profile.html (consultato: 2026-05-24)
- py-spy Documentation — https://github.com/benfred/py-spy (consultato: 2026-05-24)
- objgraph Documentation — https://mg.pov.lt/objgraph/ (consultato: 2026-05-24)
- Ruff Documentation — https://docs.astral.sh/ruff/ (consultato: 2026-05-24)
- Python Institute Certifications — https://pythoninstitute.org/ (consultato: 2026-05-24)

### Libri consigliati

- *Effective Python, 3rd Edition* — Brett Slatkin — Addison-Wesley, 2024
- *Python Debugging Handbook* — David Beazley — 2023

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [07 — Error Handling e Logging](07-error-handling-e-logging.md) | Gestione eccezioni, logging strutturato per diagnostica |
| [08 — Testing](08-testing.md) | Test di regressione, TDD per bug fix |
| [25 — Performance](25-performance.md) | Profiling, ottimizzazione, benchmarking |
| [33 — Profiling e Memoria](33-profiling-memoria-gc.md) | Analisi approfondita di memoria e garbage collection |
| [22 — Clean Code](22-clean-code.md) | Refactoring, code smells, manutenibilita |
| [24 — Virtual Environments](24-virtual-environments.md) | Risoluzione conflitti di dipendenze |

---

## Glossario

| Termine | Definizione |
|---|---|
| **pdb** | Python Debugger — debugger interattivo della stdlib per eseguire codice passo-passo |
| **breakpoint()** | Funzione built-in Python 3.7+ che attiva il debugger al punto di chiamata |
| **tracemalloc** | Modulo stdlib per tracciare le allocazioni di memoria e identificare leak |
| **py-spy** | Profiler sampling per Python che non richiede modifiche al codice, opera dall'esterno del processo |
| **cProfile** | Profiler deterministico della stdlib che misura il tempo di esecuzione di ogni funzione |
| **Memory Leak** | Condizione in cui la memoria allocata non viene rilasciata, causando consumo crescente nel tempo |
| **Traceback** | Stack trace dell'eccezione che mostra la sequenza di chiamate dal punto di errore alla radice |
| **Import Circolare** | Dipendenza ciclica tra moduli che causa `ImportError` o attributi non ancora definiti |
| **PCEP/PCAP/PCPP** | Certificazioni Python del Python Institute a livello entry, associate e professional |
| **Profiling** | Processo di misurazione delle prestazioni del codice per identificare bottleneck |
| **Race Condition** | Bug concorrente in cui il risultato dipende dall'ordine temporale imprevedibile delle operazioni |
| **Deadlock** | Situazione in cui due o piu thread si bloccano reciprocamente attendendo risorse detenute dall'altro |
| **GIL** | Global Interpreter Lock — mutex di CPython che permette a un solo thread di eseguire bytecode Python alla volta |
| **Free-Threading** | Build sperimentale di CPython 3.13+ (PEP 703) che rimuove il GIL per consentire parallelismo reale tra thread |
| **pdb++** | Sostituzione drop-in di pdb con syntax highlighting, completamento tab e sticky mode |
| **ipdb** | Debugger Python basato su IPython con autocompletamento avanzato e magic commands |
| **pudb** | Debugger Python con interfaccia TUI a pannelli (codice, variabili, stack, breakpoints) nel terminale |
| **Scalene** | Profiler Python che combina analisi CPU (Python vs nativo), memoria e I/O con overhead ridotto |
| **line_profiler** | Profiler che misura il tempo di esecuzione di ogni singola riga di una funzione Python |
| **objgraph** | Libreria per visualizzare i grafi di riferimento tra oggetti Python per diagnosticare memory leak |
| **Pympler** | Suite di strumenti per misurare la dimensione reale degli oggetti Python e monitorare la crescita della memoria |
| **faulthandler** | Modulo stdlib che produce traceback Python in caso di crash a livello C (segfault, SIGABRT) |
| **debugpy** | Debugger Python di Microsoft per VS Code che supporta debugging remoto e multi-thread |
| **zoneinfo** | Modulo stdlib (Python 3.9+) per la gestione corretta dei fusi orari, sostituto di pytz |
| **structlog** | Libreria di logging strutturato che produce log in formato JSON con contesto automatico |
| **Naive Datetime** | Oggetto datetime senza informazioni di timezone — non rappresenta un istante univoco nel tempo |
| **Aware Datetime** | Oggetto datetime con timezone esplicita — rappresenta un istante preciso e confrontabile |
| **UnicodeDecodeError** | Eccezione che si verifica quando Python non riesce a decodificare byte nell'encoding specificato |
| **pipdeptree** | Strumento che visualizza l'albero delle dipendenze Python per diagnosticare conflitti di versione |
| **uv** | Gestore di pacchetti e ambienti Python scritto in Rust, 10-100x piu veloce di pip |
