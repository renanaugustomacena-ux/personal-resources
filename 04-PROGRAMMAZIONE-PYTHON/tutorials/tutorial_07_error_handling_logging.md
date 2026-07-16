# Tutorial: Error Handling e Logging — Dal Principiante all'Esperto

> **Companion to:** `07-error-handling-e-logging.md`
> **Scope:** tipi di errori, leggere il traceback, try/except/else/finally, raise, gerarchia eccezioni, eccezioni custom, exception chaining, ExceptionGroup (3.11+), logging stdlib, structlog, correlation ID, OTel log bridge
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md` completato
> **Durata stimata:** 25–30 ore
> **Lingua:** Italiano

---

## Mappa del Tutorial

```
PARTE A — Le Eccezioni (Blocco 1 + 2)
  A1. Cos'è un errore: tre analogie
  A2. Come leggere un traceback riga per riga (sezione lunga, fondamentale)
  A3. try/except base — il piano B
  A4. Gerarchia delle eccezioni — la mappa completa
  A5. except multipli, else, finally
  A6. raise — generare e rilanciare errori
  A7. Eccezioni custom — progettare la propria gerarchia
  A8. Exception chaining — raise X from Y
  A9. contextlib.suppress
  A10. ExceptionGroup e except* (Python 3.11+)
  A11. PERICOLO: except: pass — sezione speciale (≥200 righe)

PARTE B — Il Logging (Blocco 3)
  B1. Perché print() non va in produzione (5 motivi concreti)
  B2. I cinque livelli e le loro analogie
  B3. Architettura Logger/Handler/Formatter/Filter
  B4. Configurazione: basicConfig vs dictConfig vs fileConfig
  B5. Handler avanzati: RotatingFile, TimedRotating, SMTP, Queue
  B6. structlog — logging strutturato moderno

PARTE C — Esercizi Guidati (Blocco 4)
  10 esercizi con soluzione commentata

PARTE D — Argomenti Esperti (Blocco 5)
  D1. sys.exc_info() e il modulo traceback
  D2. faulthandler — catturare segfault
  D3. QueueHandler multi-processo
  D4. Correlation ID e OpenTelemetry Log Bridge
  D5. Pattern: Retry, Circuit Breaker, Graceful Degradation
  D6. Sentry SDK

PARTE E — Riferimenti (Blocco 5)
  Checklist 35+, tabella tipo-errore→strategia, glossario, link
```

---

# PARTE A — Le Eccezioni

---

## A1. Cos'è un Errore: Tre Analogie

Prima di scrivere una sola riga di codice Python, capiamo cosa sono gli errori con tre analogie concrete. Questo ti salverà dal panico quando il terminale ti mostra uno schermo rosso.

### Analogia 1 — SyntaxError: l'errore grammaticale

Immagina di ricevere una lettera con questa frase:

> "Caro amico, ho andato alla negozio ieri."

Sai immediatamente che qualcosa non va prima ancora di capire il significato: la grammatica è sbagliata. Python fa esattamente lo stesso quando legge il tuo codice. Prima di eseguire qualsiasi istruzione, Python analizza l'intera struttura sintattica del file. Se trova un errore grammaticale — una parentesi mancante, una parola chiave scritta male, un'indentazione sbagliata — si rifiuta di avviare il programma e ti mostra un `SyntaxError`.

Il `SyntaxError` è l'unico errore che Python trova **prima** di eseguire il codice. Tutti gli altri vengono trovati **durante** l'esecuzione.

```python
# Esempio di SyntaxError: parentesi non chiusa
risultato = (10 + 5
# Python non eseguirà MAI questo file
# L'errore è trovato nella fase di parsing
```

### Analogia 2 — RuntimeError: l'incidente in corsa

Immagina di essere alla guida in un percorso che conosci a memoria. Tutto procede bene finché, all'improvviso, ti accorgi che il ponte che di solito attraversi è crollato. Il percorso sembrava valido, ma a runtime è emerso un problema che non era prevedibile staticamente.

Gli errori di runtime in Python funzionano così. Il codice è sintatticamente corretto, l'interprete inizia ad eseguirlo, e a un certo punto incontra una situazione impossibile da gestire: dividere per zero, cercare una chiave che non esiste in un dizionario, aprire un file che non c'è. A quel punto Python lancia un'eccezione.

```python
# Questo codice è sintatticamente corretto al 100%
# L'errore emerge solo quando viene eseguito

numeri = [10, 20, 30]
indice = int(input("Inserisci indice: "))  # l'utente digita 99
print(numeri[indice])  # <- qui esplode: IndexError a runtime
```

### Analogia 3 — LogicError: arrivi alla destinazione sbagliata

La terza categoria è la più insidiosa: **non c'è nessuna eccezione**. Il programma gira perfettamente. Produce output. Sembra funzionare. Ma il risultato è sbagliato.

Immagina di voler andare a Roma e di seguire scrupolosamente le indicazioni stradali. Arrivi a destinazione, ma la destinazione era Milano. Le istruzioni erano corrette ma il tuo punto di partenza era sbagliato, o le istruzioni portavano nel posto sbagliato.

```python
def calcola_media(valori: list[float]) -> float:
    """Calcola la media aritmetica."""
    # BUG: dovrebbe essere len(valori) al denominatore
    # ma il codice NON lancia nessuna eccezione
    return sum(valori) / len(valori) + 1  # off-by-one silenzioso

media = calcola_media([10, 20, 30])
# Restituisce 21.0 invece di 20.0
# Nessun errore, nessun warning, risultato silenziosamente sbagliato
```

I logic error non si catturano con try/except: si trovano con i **test** e con la **revisione del codice**.

> **Mappa dei tre tipi:**
> ```
> SyntaxError   → trovato PRIMA dell'esecuzione (fase di parsing)
> RuntimeError  → trovato DURANTE l'esecuzione (exception lanciata)
> Logic Error   → NON trovato da Python, solo dai test
> ```

---

## A2. Come Leggere un Traceback Riga per Riga

Questa è la sezione più importante del tutorial per un principiante. Quasi tutti i principianti vedono il traceback, si spaventano, e leggono solo l'ultima riga. È un errore che costa ore di debug.

Il traceback è la tua mappa del tesoro. Ti dice **esattamente** dove il problema si è verificato e come ci sei arrivato. Impara a leggerlo e ridurrai il tempo di debug dell'80%.

### Il traceback più semplice possibile

Creiamo un file chiamato `esempio.py`:

```python
# file: esempio.py

def moltiplicatore(x):
    return x * "ciao"  # errore: non si può moltiplicare str per str

risultato = moltiplicatore(10)
print(risultato)
```

Eseguiamo: `python esempio.py`

Output nel terminale:

```
Traceback (most recent call last):
  File "esempio.py", line 6, in <module>
    risultato = moltiplicatore(10)
  File "esempio.py", line 4, in moltiplicatore
    return x * "ciao"
TypeError: can't multiply sequence by non-int of type 'str'
```

Ora analizziamo ogni riga:

---

#### Riga 1: `Traceback (most recent call last):`

Questa riga è un'intestazione. Traduzione letterale: "Traccia delle chiamate (quella più recente è l'ultima)".

Il significato pratico è cruciale: **leggi il traceback dal basso verso l'alto** per trovare il problema. L'errore concreto è in fondo. Le righe sopra mostrano il percorso che ha portato lì.

"Most recent call last" significa che l'ultima riga del traceback è la più vicina all'errore reale.

---

#### Riga 2-3: il primo frame

```
  File "esempio.py", line 6, in <module>
    risultato = moltiplicatore(10)
```

Queste due righe formano un **frame**. Un frame descrive una singola chiamata di funzione nello stack.

- `File "esempio.py"` → il nome del file
- `line 6` → il numero di riga esatto
- `in <module>` → il contesto: `<module>` significa "livello principale del file, non dentro nessuna funzione"
- `risultato = moltiplicatore(10)` → il codice **esatto** della riga, ricopiato per te

Questo ti dice: "A riga 6, nel corpo principale del file, Python stava eseguendo la chiamata `moltiplicatore(10)` quando è andato qualcosa storto."

---

#### Riga 4-5: il secondo frame

```
  File "esempio.py", line 4, in moltiplicatore
    return x * "ciao"
```

- `line 4` → il numero di riga dentro la funzione
- `in moltiplicatore` → il nome della funzione
- `return x * "ciao"` → il codice esatto della riga problematica

Questo ti dice: "Python è entrato nella funzione `moltiplicatore`, è arrivato a riga 4, e qui è esploso."

---

#### Riga 6 (ultima): il tipo e messaggio dell'errore

```
TypeError: can't multiply sequence by non-int of type 'str'
```

- `TypeError` → il tipo di eccezione (appartiene alla gerarchia delle eccezioni Python)
- `can't multiply sequence by non-int of type 'str'` → la descrizione testuale del problema

Il messaggio ti dice: "Stai cercando di usare l'operatore `*` tra una stringa e qualcosa che non è un intero."

**Come si legge insieme:** il modulo principale (riga 6) ha chiamato `moltiplicatore(10)`, che a riga 4 ha tentato `10 * "ciao"`. Ma l'ordine degli argomenti in `*` è sbagliato: `str * int` funziona (`"ciao" * 3 = "ciaociaociao"`), mentre `int * str` doveva funzionare ugualmente ma in questo caso la variabile `x` era un intero passato correttamente, e il vero bug è che `"ciao"` non è il fattore giusto.

---

### Un traceback più profondo: la catena di chiamate

Ora vediamo un traceback realistico con più frame. Questo è quello che troverai nella maggior parte dei progetti.

```python
# file: app.py

import json

def carica_configurazione(percorso: str) -> dict:
    with open(percorso) as f:
        return json.load(f)

def inizializza_app(percorso_config: str) -> None:
    config = carica_configurazione(percorso_config)
    porta = config["porta"]
    print(f"Avvio su porta {porta}")

def main() -> None:
    inizializza_app("config.json")

main()
```

Eseguiamo con un file `config.json` che contiene JSON non valido:

```
Traceback (most recent call last):
  File "app.py", line 16, in <module>
    main()
  File "app.py", line 14, in main
    inizializza_app("config.json")
  File "app.py", line 10, in inizializza_app
    config = carica_configurazione(percorso_config)
  File "app.py", line 7, in carica_configurazione
    return json.load(f)
  File "/usr/lib/python3.12/json/__init__.py", line 293, in load
    return loads(fp.read(),
  File "/usr/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
  File "/usr/lib/python3.12/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
  File "/usr/lib/python3.12/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Questo spaventa molti principianti. Analizziamolo sistematicamente.

---

#### Come orientarsi in un traceback lungo

**Regola 1: leggi prima l'ultima riga.**

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Questo ti dice subito: "Il JSON è vuoto o non è JSON valido (riga 1, colonna 1 del file JSON)."

**Regola 2: scorri dal basso verso l'alto fino al TUO codice.**

Le righe con percorsi come `/usr/lib/python3.12/json/...` sono **dentro la libreria standard**. Di solito il bug non è lì. Risali fino al tuo codice:

```
  File "app.py", line 7, in carica_configurazione
    return json.load(f)
```

Questa è la riga nel tuo codice che ha scatenato la cascata. La funzione `carica_configurazione` ha chiamato `json.load(f)` che ha fallito perché il file era vuoto.

**Regola 3: risali ulteriormente per capire il contesto.**

```
  File "app.py", line 10, in inizializza_app
    config = carica_configurazione(percorso_config)
```

`inizializza_app` ha chiamato `carica_configurazione` con il percorso `"config.json"`.

**Regola 4: identifica la radice del problema.**

Il file `config.json` era vuoto o inesistente (in questo esempio era vuoto). Il problema non è nel codice Python ma nell'input. La soluzione non è cambiare il parsing JSON, ma validare il file prima di aprirlo, o gestire l'eccezione.

---

#### Il pattern "Your code → Library code → Your code"

Nei progetti reali il traceback spesso alterna righe del tuo codice con righe di librerie:

```
Traceback (most recent call last):
  File "app.py", line X, in <module>          ← TUO codice
    ...
  File "lib/django/core/handlers/base.py"      ← libreria
    ...
  File "app.py", line Y, in my_view            ← TUO codice  <--- LEGGI QUESTO
    ...
  File "lib/sqlalchemy/engine/base.py"         ← libreria
    ...
OperationalError: ...                          ← LEGGI QUESTO
```

La strategia è sempre: **ultima riga** + **ultime righe del tuo codice**.

---

### Traceback con eccezioni concatenate

Python 3.3+ supporta l'exception chaining: un'eccezione può essere il risultato diretto di un'altra. Il traceback lo mostra con frasi speciali.

#### "During handling of the above exception, another exception occurred"

```python
# file: chaining_demo.py

def leggi_numero(testo: str) -> int:
    return int(testo)

def processa_input(testo: str) -> str:
    try:
        numero = leggi_numero(testo)
        return f"Numero: {numero}"
    except ValueError as e:
        raise RuntimeError("Input non processabile") from e
```

Con `processa_input("abc")`:

```
Traceback (most recent call last):
  File "chaining_demo.py", line 8, in processa_input
    numero = leggi_numero(testo)
  File "chaining_demo.py", line 4, in leggi_numero
    return int(testo)
ValueError: invalid literal for int() with base 10: 'abc'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "chaining_demo.py", line 12, in <module>
    print(processa_input("abc"))
  File "chaining_demo.py", line 10, in processa_input
    raise RuntimeError("Input non processabile") from e
RuntimeError: Input non processabile
```

Questo traceback ha due parti separate da:

```
The above exception was the direct cause of the following exception:
```

**Come leggerlo:**
1. Prima parte: il `ValueError` originale — `int("abc")` non funziona
2. "The above exception was the direct cause" → il programmatore ha esplicitamente usato `raise X from Y` (exception chaining intenzionale)
3. Seconda parte: il `RuntimeError` lanciato nel blocco except

Questo è un traceback **ben progettato**: la causa originale è preservata, il contesto è aggiunto, e puoi risalire l'intera catena causale.

---

#### "During handling of the above exception, another exception occurred" (accidentale)

```python
def salva_su_file(dati: dict, percorso: str) -> None:
    try:
        with open(percorso, "w") as f:
            import json
            json.dump(dati, f)
    except IOError as e:
        # BUG: questa riga stessa lancia un errore!
        log.error(f"Impossibile salvare: {e}")  # log non è definito
```

```
Traceback (most recent call last):
  File "demo.py", line 4, in salva_su_file
    with open(percorso, "w") as f:
IOError: [Errno 2] No such file or directory: '/root/dati.json'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "demo.py", line 8, in salva_su_file
    log.error(f"Impossibile salvare: {e}")
NameError: name 'log' is not defined
```

La frase chiave qui è **"During handling"** (non "direct cause"). Significa:

1. L'`IOError` è avvenuto
2. Mentre Python stava eseguendo il blocco `except`, è avvenuto UN ALTRO errore (accidentale)
3. Il secondo errore oscura il primo

**Come distinguere i due tipi:**
- `"The above exception was the direct cause"` → `raise X from Y` → intenzionale
- `"During handling of the above exception"` → eccezione accidentale nel blocco except → quasi sempre un bug

---

### Errori comuni nella lettura del traceback

#### Errore 1: leggere solo l'ultima riga

```
KeyError: 'nome'
```

Senza il traceback completo non sai in quale dei 50 posti nel codice dove accedi ai dizionari è avvenuto il problema. Leggi sempre il traceback completo.

#### Errore 2: fermarsi al codice di libreria

Se il traceback passa attraverso SQLAlchemy o Django, è facile fermarsi alle righe della libreria e pensare "il bug è in SQLAlchemy". Quasi mai è così. Risali alle righe del tuo codice.

#### Errore 3: confondere la riga dell'errore con la riga della causa

Considera:

```python
dati = None
lunghezza = len(dati)  # <- errore qui
```

```
TypeError: object of type 'NoneType' has no len()
```

L'errore è a riga 2 (`len(dati)`), ma la **causa** è a riga 1 dove `dati` vale `None`. Spesso bisogna risalire per trovare dove una variabile è stata impostata al valore sbagliato.

#### Errore 4: ignorare i numeri di riga

I numeri di riga nel traceback sono precisi. Apri il file, vai a quella riga, e leggi il codice esatto. Molti principianti cercano "visivamente" il codice senza usare il numero di riga.

#### Errore 5: non leggere il messaggio di errore

Il messaggio di errore di Python è spesso auto-esplicativo:

```
AttributeError: 'NoneType' object has no attribute 'upper'
```

Traduzione: "Stai chiamando `.upper()` su qualcosa che è `None`, non su una stringa."

```
FileNotFoundError: [Errno 2] No such file or directory: 'dati.csv'
```

Traduzione: "Il file `dati.csv` non esiste nel percorso che hai specificato."

```
RecursionError: maximum recursion depth exceeded
```

Traduzione: "La tua funzione ricorsiva non ha un caso base valido e si chiama all'infinito."

---

### Workshop: analizza questi traceback

Esercitati su questi traceback reali. Prima di leggere la spiegazione, prova a diagnosticare il problema da solo.

#### Traceback 1

```
Traceback (most recent call last):
  File "script.py", line 15, in <module>
    utenti = carica_utenti()
  File "script.py", line 8, in carica_utenti
    return db.query("SELECT * FROM utenti")
  File "/usr/local/lib/python3.12/site-packages/mydb/connection.py", line 234, in query
    self._cursor.execute(sql)
AttributeError: 'NoneType' object has no attribute 'execute'
```

**Analisi:**
- Tipo: `AttributeError`
- Messaggio: `'NoneType' object has no attribute 'execute'`
- Il tuo codice: riga 8, `db.query(...)`
- Diagnosi probabile: `db` è `None`. La connessione al database non è stata inizializzata prima di usarla, o la funzione che crea `db` ha restituito `None` invece dell'oggetto di connessione.
- Dove cercare la fix: controlla dove `db` viene creato/assegnato nel tuo codice.

#### Traceback 2

```
Traceback (most recent call last):
  File "processa.py", line 22, in <module>
    for record in csv_reader:
  File "/usr/lib/python3.12/csv.py", line 112, in __next__
    self._parse_process_char(char)
  File "/usr/lib/python3.12/csv.py", line 89, in _parse_process_char
    raise Error(self.error_msg)
_csv.Error: line contains NUL
```

**Analisi:**
- Tipo: `_csv.Error` (errore specifico del modulo csv)
- Messaggio: `line contains NUL`
- Il tuo codice: riga 22, iterazione sul `csv_reader`
- Diagnosi: il file CSV contiene caratteri NUL (byte `\x00`), che è comune in file CSV corrotti, esportati da Excel con encoding sbagliato, o in file binari aperti erroneamente in modalità testo.
- Soluzione: apri il file con `open(percorso, errors='replace')` oppure filtra i caratteri NUL con una pre-elaborazione.

#### Traceback 3

```
Traceback (most recent call last):
  File "server.py", line 45, in handle_request
    risposta = self.router.dispatch(richiesta)
  File "router.py", line 23, in dispatch
    handler = self.routes[richiesta.path]
KeyError: '/api/v2/utenti'
```

**Analisi:**
- Tipo: `KeyError`
- Messaggio: `'/api/v2/utenti'` (il percorso mancante)
- Contesto: il router cerca la route `/api/v2/utenti` nel dizionario `self.routes`
- Diagnosi: la route `/api/v2/utenti` non è registrata. O è un errore di versioning (forse esiste solo `/api/v1/utenti`), o la registrazione della route manca, o il percorso è scritto diversamente nel router.

---

### Traceback in ambienti speciali

#### IPython / Jupyter

In Jupyter il traceback è colorato e ha un formato leggermente diverso. La struttura è la stessa ma l'output è dentro una cella. Il numero di riga si riferisce alla cella, non al file.

#### Pytest

```
FAILED tests/test_calcoli.py::test_media - AssertionError: assert 21.0 == 20.0
```

Pytest mostra: nome file, nome test, tipo eccezione, e dettaglio dell'asserzione. Nella sezione "FAILURES" sotto vedrai il traceback completo con il codice del test evidenziato.

#### Django / Flask

I framework web catturano le eccezioni e le mostrano in una pagina HTML durante lo sviluppo. Cercate la sezione "Traceback" nella pagina di errore. Il principio è identico al terminale.

#### Logging strutturato

Quando usi il modulo `logging` (che vedrai nella Parte B), le eccezioni vengono catturate e scritte nel log con `logger.exception(...)`. Il traceback appare nel log come parte del campo `exc_info`. Cerca sempre `exc_info` o `exception` nei tuoi log quando qualcosa va storto in produzione.

---

### Strumenti per lavorare meglio con i traceback

#### better_exceptions

```bash
pip install better_exceptions
```

```python
import better_exceptions
better_exceptions.hook()
```

Mostra i valori delle variabili nel traceback, non solo il codice.

#### rich

```bash
pip install rich
```

```python
from rich.traceback import install
install(show_locals=True)
```

Mostra il traceback in colori con i valori locali di ogni frame. Utile in sviluppo.

#### traceback module (stdlib)

Il modulo `traceback` della libreria standard permette di catturare e formattare il traceback come stringa:

```python
import traceback
import logging

logger = logging.getLogger(__name__)

def operazione_rischiosa() -> None:
    try:
        1 / 0
    except ZeroDivisionError:
        # Cattura il traceback completo come stringa
        tb_stringa = traceback.format_exc()
        logger.error("Operazione fallita:\n%s", tb_stringa)
        raise
```

---

### Checklist per leggere un traceback

Prima di cercare soluzioni online o fare modifiche al codice, percorri questa checklist ogni volta:

```
[ ] 1. Ho letto l'ULTIMA RIGA (tipo e messaggio dell'errore)?
[ ] 2. Ho localizzato le righe del MIO codice (non librerie)?
[ ] 3. Ho aperto il file e letto la riga indicata nel traceback?
[ ] 4. Ho tracciato a ritroso dove la variabile problematica è stata assegnata?
[ ] 5. Il messaggio contiene un valore concreto? (nome file, chiave, tipo)
[ ] 6. Ci sono due traceback separati (exception chaining)?
[ ] 7. La seconda eccezione è nel blocco except (errore nel gestore)?
```

---

## A3. try/except Base — Il Piano B

### L'analogia della cintura di sicurezza

Guidare un'auto non significa anticipare e prevenire ogni incidente possibile. Significa avere un **piano B** se qualcosa va storto. La cintura di sicurezza non impedisce gli incidenti: li gestisce quando accadono.

`try/except` in Python funziona esattamente così. Non previeni l'errore: descrivi cosa fare **se e quando** l'errore accade.

### Sintassi base

```python
try:
    # Codice che potrebbe fallire
    risultato = 10 / divisore
except ZeroDivisionError:
    # Cosa fare se accade ZeroDivisionError
    risultato = 0
```

**Come funziona:**

1. Python esegue il blocco `try`
2. Se nessuna eccezione viene lanciata: il blocco `except` viene saltato
3. Se viene lanciata l'eccezione specificata: Python salta al blocco `except`
4. Se viene lanciata un'eccezione **diversa** da quella specificata: l'eccezione NON viene catturata e si propaga

### Il principio fondamentale: cattura l'eccezione più specifica possibile

```python
# SBAGLIATO: troppo generico
try:
    valore = dizionario[chiave]
except Exception:
    valore = None

# CORRETTO: eccezione specifica
try:
    valore = dizionario[chiave]
except KeyError:
    valore = None
```

Perché importa? Se usi `except Exception` potresti nascondere errori completamente diversi: `NameError` perché hai sbagliato il nome della variabile, `TypeError` perché il tipo è sbagliato, ecc.

### Catturare il valore dell'eccezione

```python
import logging

logger = logging.getLogger(__name__)

def apri_file(percorso: str) -> str:
    try:
        with open(percorso) as f:
            return f.read()
    except FileNotFoundError as errore:
        logger.warning("File non trovato: %s — %s", percorso, errore)
        return ""
```

La clausola `as errore` ti dà accesso all'oggetto eccezione. Puoi leggere:
- `str(errore)` → messaggio testuale
- `errore.args` → tupla degli argomenti
- Attributi specifici (es. `errore.filename` per eccezioni file)

### Quando usare try/except

Non tutto va avvolto in try/except. Usa try/except quando:

1. L'errore è **prevedibile e recuperabile**: es. file non trovato → usa un default
2. Stai interagendo con **sistemi esterni**: rete, filesystem, database
3. L'input proviene da **sorgenti non controllate**: utente, API, file

Non usare try/except quando:
1. Il codice "non dovrebbe mai fallire" → lascia fallire esplicitamente
2. Vuoi nascondere un bug → i bug devono emergere
3. Puoi usare una guardia preventiva (`if x is not None:`) altrettanto chiara

---

## A4. Gerarchia delle Eccezioni — La Mappa Completa

Python ha una gerarchia di eccezioni strutturata ad albero. Capire questa gerarchia è fondamentale perché determina cosa cattura ogni clausola `except`.

### La regola fondamentale dell'ereditarietà

Se `B` eredita da `A`, allora `except A` cattura anche le istanze di `B`.

```python
# ValueError eredita da Exception
# quindi:
try:
    int("abc")
except Exception:       # cattura ValueError (e tutto il resto)
    pass

try:
    int("abc")
except ValueError:      # cattura solo ValueError e le sue sottoclassi
    pass
```

### L'albero completo delle eccezioni built-in

```
BaseException
├── SystemExit                    ← sys.exit() — NON eredita da Exception
├── KeyboardInterrupt             ← Ctrl+C — NON eredita da Exception
├── GeneratorExit                 ← generator.close()
└── Exception
    ├── ArithmeticError
    │   ├── FloatingPointError
    │   ├── OverflowError
    │   └── ZeroDivisionError
    ├── AssertionError
    ├── AttributeError
    ├── BufferError
    ├── EOFError
    ├── ExceptionGroup           ← Python 3.11+
    ├── ImportError
    │   └── ModuleNotFoundError
    ├── LookupError
    │   ├── IndexError
    │   └── KeyError
    ├── MemoryError
    ├── NameError
    │   └── UnboundLocalError
    ├── OSError (= IOError = EnvironmentError)
    │   ├── BlockingIOError
    │   ├── ChildProcessError
    │   ├── ConnectionError
    │   │   ├── BrokenPipeError
    │   │   ├── ConnectionAbortedError
    │   │   ├── ConnectionRefusedError
    │   │   └── ConnectionResetError
    │   ├── FileExistsError
    │   ├── FileNotFoundError
    │   ├── InterruptedError
    │   ├── IsADirectoryError
    │   ├── NotADirectoryError
    │   ├── PermissionError
    │   ├── ProcessLookupError
    │   └── TimeoutError
    ├── ReferenceError
    ├── RuntimeError
    │   ├── NotImplementedError
    │   └── RecursionError
    ├── StopAsyncIteration
    ├── StopIteration
    ├── SyntaxError
    │   └── IndentationError
    │       └── TabError
    ├── SystemError
    ├── TypeError
    ├── ValueError
    │   └── UnicodeError
    │       ├── UnicodeDecodeError
    │       ├── UnicodeEncodeError
    │       └── UnicodeTranslateError
    └── Warning
        ├── BytesWarning
        ├── DeprecationWarning
        ├── EncodingWarning
        ├── FutureWarning
        ├── ImportWarning
        ├── PendingDeprecationWarning
        ├── ResourceWarning
        ├── RuntimeWarning
        ├── SyntaxWarning
        ├── UnicodeWarning
        └── UserWarning
```

### Tabella delle eccezioni più comuni

| Eccezione | Quando si verifica | Esempio trigger |
|-----------|-------------------|-----------------|
| `SyntaxError` | Codice non parsabile | `if x == :` |
| `IndentationError` | Indentazione errata | riga non allineata |
| `NameError` | Nome non definito | `print(variabile_mai_definita)` |
| `UnboundLocalError` | Locale usata prima di assegnazione | uso di `x` prima di `x = 5` in funzione |
| `TypeError` | Tipo sbagliato per operazione | `"ciao" + 5` |
| `ValueError` | Tipo giusto, valore sbagliato | `int("abc")` |
| `AttributeError` | Attributo non esiste | `None.upper()` |
| `KeyError` | Chiave non in dizionario | `d["chiave_mancante"]` |
| `IndexError` | Indice fuori range | `lista[100]` su lista di 3 elementi |
| `ZeroDivisionError` | Divisione per zero | `10 / 0` |
| `FileNotFoundError` | File non trovato | `open("file_inesistente.txt")` |
| `PermissionError` | Permessi insufficienti | `open("/root/segreto")` |
| `OSError` | Errore generico del SO | disco pieno, path non valido |
| `ImportError` | Modulo non trovato | `import modulo_inesistente` |
| `ModuleNotFoundError` | (sottoclasse) modulo non installato | `import pandas` senza pip install |
| `RuntimeError` | Errore generico di runtime | thread non avviato correttamente |
| `RecursionError` | Stack overflow ricorsivo | funzione senza caso base |
| `MemoryError` | Memoria esaurita | lista enorme |
| `StopIteration` | Iteratore esaurito | `next()` su iteratore vuoto |
| `AssertionError` | `assert` fallisce | `assert 1 == 2` |
| `NotImplementedError` | Metodo astratto non implementato | sottoclasse non implementa metodo |

### Perché `SystemExit` e `KeyboardInterrupt` non ereditano da `Exception`

Questa è una scelta di design intenzionale. Considera:

```python
# PROBLEMA: questo cattura anche SystemExit e KeyboardInterrupt
try:
    ...
except Exception:
    pass  # SystemExit viene inghiottito! sys.exit() smette di funzionare
```

Poiché `SystemExit` e `KeyboardInterrupt` ereditano da `BaseException` (non da `Exception`), un `except Exception` non li cattura. Questo significa che `sys.exit()` e `Ctrl+C` funzioneranno sempre, a meno che tu non scriva esplicitamente `except BaseException` o `except SystemExit`.

```python
# CORRETTO: SystemExit si propaga normalmente
try:
    import sys
    sys.exit(0)
except Exception:
    pass  # SystemExit NON viene catturato qui — esce normalmente
```

### Alias storici: OSError, IOError, EnvironmentError

In Python 3, `IOError` e `EnvironmentError` sono alias di `OSError`. Puoi usare tutti e tre i nomi, ma `OSError` è il preferito.

```python
# Questi tre fanno esattamente la stessa cosa in Python 3:
except OSError:        # preferito
except IOError:        # alias (per compatibilità con Python 2)
except EnvironmentError:  # alias (per compatibilità con Python 2)
```

---

*Fine Blocco 1. Continua nel Blocco 2 con: except multipli, else, finally, raise, eccezioni custom, exception chaining, ExceptionGroup, e la sezione speciale sul divieto di `except: pass`.*
---

## A5. except Multipli, else, finally

### Catturare più eccezioni diverse

Un singolo blocco `try` può avere più clausole `except`. Python le prova in ordine e usa la prima che corrisponde.

```python
import logging

logger = logging.getLogger(__name__)

def converti_in_numero(testo: str) -> float:
    try:
        return float(testo)
    except ValueError:
        logger.warning("Valore non convertibile: %r", testo)
        return 0.0
    except TypeError:
        logger.warning("Tipo non valido: %r (tipo: %s)", testo, type(testo).__name__)
        return 0.0
```

**Regola critica:** metti le eccezioni più specifiche **prima** di quelle più generali.

```python
# SBAGLIATO: Exception cattura tutto prima — ValueError non viene mai raggiunto
try:
    elabora()
except Exception:
    gestisci_generico()
except ValueError:      # unreachable: Exception cattura gia ValueError
    gestisci_valore()

# CORRETTO: dal piu specifico al piu generico
try:
    elabora()
except ValueError:
    gestisci_valore()
except OSError:
    gestisci_io()
except Exception:
    gestisci_generico()
```

### Catturare piu eccezioni nella stessa clausola

```python
try:
    risultato = int(valore) / divisore
except (ValueError, ZeroDivisionError) as errore:
    logger.error("Errore nel calcolo: %s", errore)
    risultato = None
```

La sintassi `except (A, B)` cattura sia `A` che `B` — equivalente a due clausole separate ma con lo stesso corpo.

### La clausola `else`

Il blocco `else` viene eseguito **solo se nessuna eccezione e stata lanciata** nel blocco `try`:

```python
import json
import logging

logger = logging.getLogger(__name__)

def carica_json(percorso: str) -> dict | None:
    try:
        with open(percorso) as f:
            dati = json.load(f)
    except FileNotFoundError:
        logger.error("File non trovato: %s", percorso)
        return None
    except json.JSONDecodeError as e:
        logger.error("JSON non valido in %s: %s", percorso, e)
        return None
    else:
        # Eseguito SOLO se try ha avuto successo
        logger.info("File caricato: %s (%d chiavi)", percorso, len(dati))
        return dati
```

**Perche usare `else` invece di mettere il codice alla fine di `try`?**

```python
# Senza else: il log e dentro try, viene catturato da except se lancia
try:
    with open(percorso) as f:
        dati = json.load(f)
    logger.info("Caricato: %d chiavi", len(dati))  # se len() lancia, except lo cattura!
except json.JSONDecodeError:
    ...

# Con else: il log NON e catturato dagli except precedenti
try:
    with open(percorso) as f:
        dati = json.load(f)
except json.JSONDecodeError:
    ...
else:
    logger.info("Caricato: %d chiavi", len(dati))
```

`else` separa il codice del "percorso felice" dalla gestione degli errori. Qualsiasi eccezione nel blocco `else` si propaga normalmente senza essere catturata dagli `except` precedenti.

### La clausola `finally`

Il blocco `finally` viene eseguito **sempre**: con successo, con eccezione catturata, con eccezione non catturata, e anche quando c'e un `return` nel blocco `try`.

```python
import logging

logger = logging.getLogger(__name__)

def elabora_risorsa(risorsa_id: int) -> dict:
    risorsa = acquisisci_risorsa(risorsa_id)
    try:
        risultato = trasforma(risorsa)
        return risultato
    except TransformazioneError as e:
        logger.error("Trasformazione fallita per risorsa %d: %s", risorsa_id, e)
        raise
    finally:
        # Eseguito SEMPRE — anche dopo il raise sopra
        rilascia_risorsa(risorsa)
        logger.debug("Risorsa %d rilasciata", risorsa_id)
```

**Usa `finally` per:** chiusura di file o connessioni, rilascio di lock, pulizia di risorse temporanee, logging di fine operazione (audit trail).

**Trappola: `return` nel `finally`**

```python
def funzione_strana() -> str:
    try:
        return "try"
    finally:
        return "finally"  # sovrascrive il return del try!

print(funzione_strana())  # stampa "finally", non "try"
```

Evita `return` nel `finally` — e una fonte comune di bug sottili.

### Schema completo: tutti i blocchi insieme

```
try:
    # 1. Codice principale (puo lanciare eccezioni)
except EccezioneSpecifica as e:
    # 2. Gestione errore specifico
except (AltraEccezione, AncoraUna) as e:
    # 3. Gestione raggruppata
except Exception as e:
    # 4. Fallback generico (usa raramente)
else:
    # 5. Eseguito SOLO se try ha avuto successo
finally:
    # 6. Eseguito SEMPRE
```

Combinazioni piu frequenti nella pratica: `try/except`, poi `try/except/finally`, poi `try/except/else`.


---

## A6. raise — Generare e Rilanciare Errori

### Lanciare un'eccezione

```python
def dividi(a: float, b: float) -> float:
    if b == 0:
        raise ValueError(f"Il divisore non puo essere zero (ricevuto: b={b!r})")
    return a / b
```

`raise` termina immediatamente la funzione e propaga l'eccezione verso l'alto nello stack. Non esiste un valore di ritorno dopo `raise`.

### Quando usare `raise`

**1. Validazione di input — contratti della funzione:**

```python
def imposta_eta(eta: int) -> None:
    if not isinstance(eta, int):
        raise TypeError(f"L'eta deve essere un intero, ricevuto: {type(eta).__name__}")
    if eta < 0 or eta > 150:
        raise ValueError(f"Eta non plausibile: {eta}. Atteso: 0-150.")
```

**2. Stato impossibile:**

```python
def gestisci_stato(stato: str) -> None:
    if stato == "attivo":
        avvia()
    elif stato == "inattivo":
        ferma()
    else:
        raise RuntimeError(f"Stato non riconosciuto: {stato!r}")
```

**3. Metodi astratti non implementati:**

```python
class ElaboratoreBase:
    def elabora(self, dati: bytes) -> bytes:
        raise NotImplementedError(
            f"{type(self).__name__} deve implementare il metodo 'elabora'"
        )
```

In Python moderno preferisci `abc.ABC` + `@abstractmethod` invece di `raise NotImplementedError` manuale.

### Bare `raise`: rilanciare preservando il traceback

```python
import logging

logger = logging.getLogger(__name__)

def operazione_critica(valore: int) -> int:
    try:
        return calcola(valore)
    except ValueError as e:
        logger.error("Calcolo fallito per valore=%d: %s", valore, e, exc_info=True)
        raise  # rilancia preservando il traceback originale
```

**`raise` bare vs `raise e` — differenza tecnica:**

```python
# raise (bare): il traceback punta alla riga DENTRO la funzione originale
try:
    funzione_profonda()
except ValueError:
    logger.error("Errore")
    raise

# raise e: crea un NUOVO punto di inizio del traceback (info perdute!)
try:
    funzione_profonda()
except ValueError as e:
    logger.error("Errore")
    raise e  # il traceback parte da QUESTA riga, non da funzione_profonda
```

Usa sempre `raise` (bare) per rilanciare. Usa `raise e` solo se stai modificando l'eccezione prima di rilanciarla.

### Messaggi di errore utili

Un buon messaggio risponde a: cosa e andato storto, quale valore ha causato il problema, cosa era atteso.

```python
# Inutile
raise ValueError("Valore non valido")

# Utile
raise ValueError(
    f"Eta non valida: {eta!r}. "
    f"Atteso: intero in [0, 150]. "
    f"Ricevuto: {type(eta).__name__}={eta!r}"
)
```

---

## A7. Eccezioni Custom — Progettare la Propria Gerarchia

### Perche creare eccezioni custom

Le eccezioni built-in (`ValueError`, `RuntimeError`, ecc.) sono generiche. In un'applicazione reale vuoi:

1. Nomi **significativi** per il dominio del problema
2. Dati **strutturati** oltre al semplice messaggio testuale
3. Cattura **selettiva** in base al livello di astrazione

```python
# Con eccezioni generiche: ambiguo
except ValueError:
    ...  # Validazione? Parsing? Logica di business?

# Con eccezioni custom: chiarissimo
except ValidationError:
    ...  # Certamente un errore di validazione dell'input
```

### Schema base: gerarchia a due livelli

```python
class AppError(Exception):
    """Eccezione base per tutta l'applicazione."""

class ValidationError(AppError):
    """Errore di validazione dei dati in input."""

class DatabaseError(AppError):
    """Errore di accesso al database."""

class NotFoundError(DatabaseError):
    """La risorsa richiesta non esiste nel database."""

class ConflictError(DatabaseError):
    """Conflitto: la risorsa esiste gia o viola un vincolo di unicita."""
```

**Beneficio pratico:**

```python
try:
    salva_utente(dati)
except ValidationError as e:
    return risposta_400(str(e))   # input non valido: colpa del client
except NotFoundError as e:
    return risposta_404(str(e))   # risorsa non trovata
except ConflictError as e:
    return risposta_409(str(e))   # conflitto: email gia presente
except DatabaseError as e:
    logger.critical("Errore DB: %s", e, exc_info=True)
    return risposta_500()         # qualsiasi altro errore DB
```

### Eccezioni con attributi strutturati: uso di dataclass

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class ValidationError(AppError):
    campo: str
    valore: object
    motivo: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return (
            f"Validazione fallita per '{self.campo}': {self.motivo} "
            f"(valore: {self.valore!r})"
        )
```

`@dataclass(frozen=True)` per le eccezioni e una best practice moderna:
- `frozen=True` rende l'eccezione immutabile dopo la creazione
- I campi documentati con type hints
- `__init__`, `__repr__`, `__eq__` generati automaticamente

```python
# Lancio con dati strutturati
raise ValidationError(
    campo="email",
    valore="mario.rossi",
    motivo="formato email non valido: manca dominio dopo '@'",
)

# Cattura con accesso agli attributi strutturati
try:
    valida(dati)
except ValidationError as e:
    logger.warning(
        "Validazione fallita",
        extra={"campo": e.campo, "valore": str(e.valore), "motivo": e.motivo},
    )
```

### Pattern Domain-Driven Design

```python
# Separazione per livello architetturale
class DomainError(Exception):
    """Errori di logica di business (dipendono dal dominio)."""

class InfrastructureError(Exception):
    """Errori tecnici (dipendono dall'infrastruttura)."""


# Errori di dominio
@dataclass(frozen=True)
class SaldoInsufficienteError(DomainError):
    disponibile: float
    richiesto: float
    def __str__(self) -> str:
        return f"Saldo insufficiente: {self.disponibile:.2f} < {self.richiesto:.2f}"

@dataclass(frozen=True)
class OrdineNonTrovatoError(DomainError):
    ordine_id: int
    def __str__(self) -> str:
        return f"Ordine #{self.ordine_id} non trovato"


# Errori infrastrutturali
@dataclass(frozen=True)
class DatabaseConnectionError(InfrastructureError):
    host: str
    porta: int
    causa: str
    def __str__(self) -> str:
        return f"Impossibile connettersi a {self.host}:{self.porta} ({self.causa})"
```

**Il layer API cattura:** `DomainError` per HTTP 4xx, `InfrastructureError` per HTTP 5xx — senza conoscere i dettagli implementativi di ogni caso.


---

## A8. Exception Chaining — `raise X from Y`

### Il problema: perdere il contesto originale

```python
# SBAGLIATO: chi cattura RuntimeError non sa che era un OSError
def salva_configurazione(config: dict) -> None:
    try:
        with open("config.json", "w") as f:
            import json
            json.dump(config, f)
    except OSError:
        raise RuntimeError("Impossibile salvare la configurazione")
        # Il chiamante riceve RuntimeError senza sapere il motivo tecnico
```

### La soluzione: `raise X from Y`

```python
import json
import logging

logger = logging.getLogger(__name__)

def salva_configurazione(config: dict) -> None:
    try:
        with open("config.json", "w") as f:
            json.dump(config, f)
    except OSError as causa:
        raise RuntimeError(
            "Impossibile salvare la configurazione"
        ) from causa
```

Il traceback mostrera entrambe le eccezioni collegate:

```
OSError: [Errno 13] Permission denied: 'config.json'

The above exception was the direct cause of the following exception:

RuntimeError: Impossibile salvare la configurazione
```

`raise X from Y` imposta `X.__cause__ = Y` e `X.__suppress_context__ = True`.

### Accedere alla catena in codice

```python
try:
    salva_configurazione(dati)
except RuntimeError as e:
    causa = e.__cause__               # OSError originale
    contesto_implicito = e.__context__ # impostato automaticamente da Python
    if causa:
        logger.error("Causa tecnica: %s — %s", type(causa).__name__, causa)
    logger.error("Errore applicativo: %s", e)
```

### `raise X from None`: sopprimere il contesto

```python
def converti_eta(valore: str) -> int:
    try:
        return int(valore)
    except ValueError:
        raise ValueError(
            f"Formato eta non valido: {valore!r}. Atteso: numero intero positivo."
        ) from None
        # Il ValueError interno non appare nel traceback
        # Solo il messaggio personalizzato e visibile al chiamante
```

Usa `from None` quando il contesto tecnico interno sarebbe confusionario (un dettaglio implementativo che i tuoi chiamanti non devono conoscere).

---

## A9. contextlib.suppress — Ignorare Eccezioni in Modo Esplicito

Quando vuoi deliberatamente ignorare un'eccezione specifica, `contextlib.suppress` offre una sintassi chiara e intenzionale.

```python
from contextlib import suppress
import os

# Invece di:
try:
    os.remove("file_temporaneo.txt")
except FileNotFoundError:
    pass  # il file potrebbe non esistere

# Scrivi:
with suppress(FileNotFoundError):
    os.remove("file_temporaneo.txt")
```

`suppress` accetta piu tipi di eccezione:

```python
from contextlib import suppress

with suppress(FileNotFoundError, PermissionError):
    os.remove(percorso_temporaneo)
```

**Quando usare `suppress`:**
- Operazioni di pulizia opzionali (rimozione file temporanei)
- Chiusura di risorse gia chiuse
- Operazioni idempotenti dove "gia fatto" non e un errore

**Quando NON usare `suppress`:**
- Come sostituto alla gestione reale degli errori
- Quando l'eccezione indica un bug
- Quando vuoi loggare o reagire all'errore

`suppress` e la versione esplicita e documentata del pattern "ignora questa eccezione specifica". La differenza cruciale rispetto a `except: pass`: dichiara esplicitamente il tipo ignorato e non rischia di inghiottire eccezioni diverse.

---

## A10. ExceptionGroup e `except*` — Python 3.11+

Python 3.11 ha introdotto `ExceptionGroup` (PEP 654) per gestire scenari dove **piu eccezioni accadono contemporaneamente**, tipico in codice asincrono con `asyncio.TaskGroup`.

### Il problema che ExceptionGroup risolve

Prima di Python 3.11, con `asyncio.gather()` potevi propagare solo **una** eccezione anche se piu task fallivano simultaneamente. Le altre eccezioni andavano perse o richiedevano gestione manuale complessa.

### Struttura di ExceptionGroup

```python
# Creare un ExceptionGroup manualmente (per illustrare la struttura)
gruppo = ExceptionGroup(
    "errori di elaborazione batch",   # messaggio descrittivo
    [
        ValueError("valore non valido nel record 3"),
        ConnectionError("timeout connessione al server B"),
        TimeoutError("timeout scaduto per operazione C"),
    ]
)
```

`ExceptionGroup` contiene un messaggio e una lista di eccezioni figlie. Puo essere annidato: un `ExceptionGroup` puo contenere altri `ExceptionGroup`.

### `except*`: catturare selettivamente

La sintassi `except*` e nuova e funziona diversamente da `except`:

```python
try:
    raise ExceptionGroup(
        "test multi-errore",
        [ValueError("v1"), TypeError("t1"), ValueError("v2")]
    )
except* ValueError as eg:
    # eg e un ExceptionGroup contenente SOLO i ValueError del gruppo
    print(f"Errori di valore: {[str(e) for e in eg.exceptions]}")
    # Output: Errori di valore: ['v1', 'v2']
except* TypeError as eg:
    # eg contiene SOLO i TypeError
    print(f"Errori di tipo: {[str(e) for e in eg.exceptions]}")
```

**Differenza cruciale tra `except` e `except*`:**

| Caratteristica | `except` | `except*` |
|---------------|---------|-----------|
| Cosa cattura | Prima eccezione corrispondente | Tutte le eccezioni del tipo nel gruppo |
| Eccezioni non catturate | Propagate normalmente | Continuano a propagarsi nel gruppo |
| Quante clausole eseguono | Una sola | Piu clausole possono eseguire |

### Uso reale con asyncio.TaskGroup

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

async def scarica(url: str) -> str:
    ...

async def elabora_batch(urls: list[str]) -> list[str]:
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(scarica(url)) for url in urls]
        # Se task falliscono, TaskGroup raccoglie le eccezioni in ExceptionGroup
        return [t.result() for t in tasks]
    except* ConnectionError as eg:
        logger.error(
            "Connessione fallita per %d URL",
            len(eg.exceptions),
            exc_info=True,
        )
        return []
    except* TimeoutError as eg:
        logger.warning("Timeout per %d URL", len(eg.exceptions))
        return []
```

### Metodi utili di ExceptionGroup

```python
eg = ExceptionGroup("test", [ValueError("a"), TypeError("b"), ValueError("c")])

# split: divide in match + resto
match, resto = eg.split(ValueError)
# match = ExceptionGroup("test", [ValueError("a"), ValueError("c")])
# resto = ExceptionGroup("test", [TypeError("b")])

# subgroup: restituisce solo il sotto-gruppo corrispondente (o None)
solo_value_error = eg.subgroup(ValueError)

# add_note (PEP 678, Python 3.11+): aggiunge note contestuali a qualsiasi eccezione
try:
    elabora_record(record)
except ValueError as e:
    e.add_note(f"Errore nel record id={record.id}")
    e.add_note(f"Campo problematico: {campo_corrente!r}")
    raise
```

`add_note()` funziona su qualsiasi eccezione, non solo su `ExceptionGroup`. Le note appaiono nel traceback dopo il messaggio principale e sono utili per aggiungere contesto senza modificare il tipo o il messaggio dell'eccezione originale.


---

## A11. PERICOLO: `except: pass` e Vietato — Sezione Speciale

> **Questa sezione e lunga e deliberata. `except: pass` e la singola pratica Python piu pericolosa che esiste. Ogni parola qui sotto conta.**

### Cosa fa `except: pass`

```python
try:
    operazione()
except:
    pass
```

Questa combinazione fa due cose devastanti insieme:

**Prima devastazione — `except:` senza tipo** cattura letteralmente **tutto**:

- `ValueError` — errore di valore: normale
- `KeyboardInterrupt` — l'utente ha premuto Ctrl+C: **inghiottito**
- `SystemExit` — `sys.exit()` e stato chiamato: **inghiottito**
- `MemoryError` — memoria esaurita: **inghiottito**
- `RecursionError` — stack overflow: **inghiottito**
- `GeneratorExit` — generatore chiuso: **inghiottito**

Non e equivalente a `except Exception`. E equivalente a `except BaseException`. Cattura **qualsiasi** segnale o condizione di terminazione del sistema, inclusi quelli che dovrebbero far chiudere il processo.

**Seconda devastazione — `pass`** significa: nessun log, nessuna notifica, nessuna metrica, nessuna reazione. Il fallimento viene **inghiottito silenziosamente**. Il programma mente: invece di fallire visibilmente, continua in uno stato potenzialmente corrotto.

### Caso reale 1 — Il saldo bancario che scompare

```python
def trasferisci_fondi(
    conto_origine: str,
    conto_destinazione: str,
    importo: float,
) -> bool:
    try:
        db.begin_transaction()
        saldo_origine = db.get_saldo(conto_origine)
        db.update_saldo(conto_origine, saldo_origine - importo)
        saldo_dest = db.get_saldo(conto_destinazione)
        db.update_saldo(conto_destinazione, saldo_dest + importo)
        db.commit()
        return True
    except:
        pass        # CODICE CATASTROFICO
    return False
```

**Scenario di fallimento:** `db.update_saldo(conto_origine, ...)` ha successo — il saldo e decrementato. Poi la connessione al DB cade: `db.get_saldo(conto_destinazione)` lancia `ConnectionError`. L'`except: pass` lo cattura silenziosamente. `db.commit()` non viene mai chiamato.

A seconda del database e del livello di isolamento, il decremento del saldo origine potrebbe essere gia persistito su disco. I soldi sono scomparsi. Il chiamante riceve `False`. Mostra "Trasferimento fallito". L'utente riprova. Il saldo si decrementa di nuovo.

**Nessun log. Nessun alert. Nessun traceback.** Il bug potrebbe restare nascosto per settimane. Solo la riconciliazione contabile lo trovera — quando il danno e gia fatto.

**La versione corretta:**

```python
import logging

logger = logging.getLogger(__name__)

def trasferisci_fondi(
    conto_origine: str,
    conto_destinazione: str,
    importo: float,
) -> bool:
    try:
        db.begin_transaction()
        saldo_origine = db.get_saldo(conto_origine)
        if saldo_origine < importo:
            raise SaldoInsufficienteError(
                disponibile=saldo_origine, richiesto=importo
            )
        db.update_saldo(conto_origine, saldo_origine - importo)
        saldo_dest = db.get_saldo(conto_destinazione)
        db.update_saldo(conto_destinazione, saldo_dest + importo)
        db.commit()
        logger.info(
            "Trasferimento completato: %s -> %s, importo=%.2f",
            conto_origine, conto_destinazione, importo,
        )
        return True
    except SaldoInsufficienteError as e:
        db.rollback()
        logger.warning("Saldo insufficiente: %s", e)
        return False
    except Exception as e:
        db.rollback()
        logger.critical(
            "Trasferimento FALLITO — rollback eseguito",
            exc_info=True,
            extra={
                "origine": conto_origine,
                "destinazione": conto_destinazione,
                "importo": importo,
            },
        )
        raise   # propaga: il sistema non puo gestire questo silenziosamente
```

### Caso reale 2 — La configurazione che carica il valore sbagliato

```python
class Configurazione:
    def __init__(self, percorso: str) -> None:
        self._dati: dict = {}
        try:
            with open(percorso) as f:
                import json
                self._dati = json.load(f)
        except:
            pass  # "tanto usa i valori di default"
```

**Scenario:** il file `config.json` esiste ma contiene un typo nel JSON:

```json
{"host": "db.produzione.com", "porta": 5432, "timeout":  }
```

`json.load()` lancia `JSONDecodeError`. L'`except: pass` lo cattura. `self._dati` rimane `{}`.

I valori di default entrano in gioco. Il default per `host` e `"localhost"`. Il server si connette al database di sviluppo locale invece di quello di produzione. Le query sembrano funzionare (c'e un database su localhost). I dati vengono scritti nel database sbagliato.

**Impatto:** ore o giorni di dati di produzione sul database sbagliato. Nessun errore visibile. La riconciliazione notturna trovera il problema — ma il danno e fatto.

**La versione corretta:**

```python
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Configurazione:
    def __init__(self, percorso: str) -> None:
        percorso_path = Path(percorso)
        if not percorso_path.exists():
            raise FileNotFoundError(
                f"File di configurazione non trovato: {percorso}"
            )
        try:
            with percorso_path.open(encoding="utf-8") as f:
                self._dati: dict = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Configurazione non valida in {percorso}: {e}"
            ) from e
        logger.info(
            "Configurazione caricata da %s (%d chiavi)", percorso, len(self._dati)
        )
```


### Caso reale 3 — Il thread che cicla su MemoryError

```python
import threading
import time

def worker() -> None:
    while True:
        try:
            elabora_prossimo_job()
            time.sleep(1)
        except:
            pass  # "non voglio che il thread muoia"
```

**Scenario A — MemoryError:** il sistema e a corto di memoria. `elabora_prossimo_job()` lancia `MemoryError`. L'`except: pass` lo cattura. Il thread continua. Ma ogni iterazione successiva rilancia `MemoryError`. Il thread cicla al 100% della CPU, consumando il poco stack rimasto in un loop frenetico. Completamente silenzioso.

**Scenario B — KeyboardInterrupt:** l'operatore preme Ctrl+C. `KeyboardInterrupt` viene lanciato. `except:` lo cattura. Il processo non risponde a Ctrl+C. Per fermarlo serve `kill -9`. Pulizia? Zero.

**Scenario C — SystemExit:** qualcuno chiama `sys.exit()` per un arresto controllato. `except:` cattura `SystemExit`. Il worker continua a girare. Il processo non si spegne. Docker deve inviare SIGKILL. Le transazioni in corso vengono troncate.

**La versione corretta:**

```python
import threading
import time
import logging

logger = logging.getLogger(__name__)

def worker() -> None:
    while True:
        try:
            elabora_prossimo_job()
        except KeyboardInterrupt:
            logger.info("Worker fermato da segnale utente")
            break
        except Exception as e:
            logger.error(
                "Errore nel worker — riprovo tra 5 secondi",
                exc_info=True,
            )
            time.sleep(5)  # backoff prima del retry, evita hot-loop
        else:
            time.sleep(1)  # pausa normale tra job
```

### Caso reale 4 — Il `SystemExit` inghiottito

```python
import sys

def spegni_applicazione() -> None:
    try:
        chiudi_connessioni()
        sys.exit(0)  # lancia SystemExit
    except:
        pass          # SystemExit catturato e ignorato!

spegni_applicazione()
# L'applicazione NON esce. Continua a girare indefinitamente.
```

`sys.exit(0)` lancia `SystemExit`, sottoclasse di `BaseException` (non di `Exception`). Un `except:` senza tipo lo cattura. L'applicazione che "dovrebbe chiudersi" continua a girare.

**Impatto reale:** `docker stop` invia SIGTERM. L'applicazione chiama `sys.exit()`. L'`except: pass` lo ingoia. Dopo 10 secondi, Docker invia SIGKILL. Il processo viene terminato brutalmente, senza la pulizia pianificata: nessun flush dei buffer, nessuna chiusura delle transazioni, nessuna deregistrazione dai servizi. Dati potenzialmente corrotti.

### Caso reale 5 — La serializzazione con riferimenti circolari

```python
def serializza(oggetto: object) -> str:
    try:
        return str(oggetto)
    except:
        return ""  # "se non riesce, stringa vuota"
```

**Scenario:** `oggetto` ha un riferimento circolare (`a.figlio = b`, `b.genitore = a`). `str(oggetto)` causa `RecursionError`. `except: pass` lo cattura. La funzione restituisce `""`.

Il sistema esporta migliaia di record. Uno ha un riferimento circolare. Viene serializzato come stringa vuota, silenziosamente. Il file di export ha record vuoti. Il sistema di import li salta. Dati persi in modo irreversibile. Nessuna traccia di quale record fosse.

### Perche "mettere un try/except" non e una rete di sicurezza

Molti principianti mettono `except: pass` pensando: "Cosi il programma non esplode". Paradossalmente, e **piu pericoloso** che lasciare esplodere il programma:

1. Un programma che fallisce esplicitamente ti dice **cosa**, **dove**, e **quando** ha fallito.
2. Un programma con `except: pass` continua in uno stato sconosciuto, potenzialmente corrompendo dati o producendo risultati sbagliati per ore.

**Fallire in modo esplicito e visibile e una funzionalita, non un difetto.**

Un processo che crasha immediatamente con un traceback chiaro costa 5 minuti di debug. Un processo con `except: pass` che silenziosamente produce dati sbagliati puo costare giorni di investigazione, perdita di dati, e danni irreparabili.

### Le alternative corrette per ogni scenario

| Intenzione | Sbagliato | Corretto |
|-----------|-----------|---------|
| Ignorare file mancante | `except: pass` | `with suppress(FileNotFoundError):` |
| Continuare dopo errore rete | `except: pass` | `except NetworkError as e: logger.warning(...)` |
| Valore di default | `except: pass` | `except KeyError: valore = default` |
| Non bloccare il thread | `except: pass` | `except Exception as e: logger.error(..., exc_info=True)` |
| Chiudere risorse comunque | `except: pass` | `finally:` o context manager `with:` |
| Permettere Ctrl+C | `except: pass` | `except Exception:` lascia passare `KeyboardInterrupt` |
| Permettere `sys.exit()` | `except: pass` | `except Exception:` lascia passare `SystemExit` |

### La regola in dieci parole

> **Se catturi un'eccezione, devi fare qualcosa di osservabile.**

"Osservabile" significa: log strutturato, metrica incrementata, notifica inviata, eccezione rilanciata, oppure valore sentinella documentato restituito. Non `pass`. Non silenzio.

### `except Exception: pass` — e meglio ma non basta

Anche `except Exception: pass` e quasi sempre sbagliato. Almeno lascia passare `KeyboardInterrupt` e `SystemExit`. Se per qualche ragione devi avere un `except Exception` generico, scrivi almeno:

```python
except Exception:
    logger.error("Errore imprevisto", exc_info=True)
    raise  # o: metrics.increment("errors.unexpected")
```

Niente `pass`. Mai. Senza eccezioni. Nemmeno "solo temporaneamente per il debug" — rimane per sempre.

### Checklist: come verificare il tuo codice

Prima di fare commit, cerca nel tuo codice tutti i `except:` e `except Exception:`. Per ognuno, chiediti:

```
[ ] Sto loggando l'eccezione (con exc_info=True per il traceback)?
[ ] Sto incrementando una metrica o notificando qualcuno?
[ ] Se "ignoro" intenzionalmente, sto usando contextlib.suppress?
[ ] Il tipo di eccezione catturata e il piu specifico possibile?
[ ] Se rilanscio, uso raise (bare) e non raise e?
[ ] Sto evitando di catturare KeyboardInterrupt/SystemExit per errore?
```

---

*Fine Blocco 2. Continua nel Blocco 3 con la Parte B — Logging: perche `print()` non basta in produzione, i cinque livelli, l'architettura Logger/Handler/Formatter/Filter, configurazione basicConfig/dictConfig, e structlog.*

---

# PARTE B — Il Logging

---

## B1. Perche `print()` Non Va in Produzione: 5 Motivi Concreti

Molti principianti usano `print()` per "vedere cosa succede" nel codice. In sviluppo locale e tollerabile. In produzione e un disastro. Ecco perche.

### Motivo 1 — Nessuna informazione di contesto

```python
# Con print:
print("Errore nel processamento")
# Output: Errore nel processamento
# Non sai: quando? quale modulo? quale funzione? quale riga?

# Con logging:
logger.error("Errore nel processamento", extra={"user_id": 42, "operazione": "trasferimento"})
# Output: 2024-01-15 14:32:07,891 ERROR app.services [user_id=42 operazione=trasferimento] Errore nel processamento
```

Il log include timestamp, livello, modulo, e qualsiasi campo strutturato che aggiungi. Il `print` non include niente di tutto cio.

### Motivo 2 — Impossibile filtrare in produzione

In produzione hai migliaia di log al secondo. Con `print()`, vedi tutto o niente. Con il modulo `logging`, puoi:

```python
# In sviluppo: vedi tutto da DEBUG in su
logging.basicConfig(level=logging.DEBUG)

# In produzione: vedi solo WARNING e superiori
logging.basicConfig(level=logging.WARNING)

# Per un modulo specifico: abbassa solo quel modulo
logging.getLogger("app.database").setLevel(logging.DEBUG)
```

Puoi cambiare il livello di log **senza modificare il codice** — solo la configurazione.

### Motivo 3 — Nessun controllo sulla destinazione

Con `print()`, l'output va sempre su stdout. In produzione vuoi:
- Log critici via email
- Log di errore su Sentry
- Log su filesystem con rotazione automatica
- Log su sistema centralizzato (Loki, ELK Stack, Splunk)
- Log su socket per aggregatori

Il modulo `logging` gestisce tutto questo con `Handler` diversi senza cambiare il codice applicativo.

### Motivo 4 — Performance: stampa anche quando non serve

In produzione tipicamente vuoi solo WARNING e superiori. Con `print()`, il codice esegue sempre la formattazione della stringa:

```python
# Con print: formatta la stringa SEMPRE, anche se non vuoi vederla
print(f"Debug: {calcolo_costoso()}")  # calcolo_costoso() eseguito sempre

# Con logging: se il livello e troppo basso, non esegue nemmeno la formattazione
logger.debug("Debug: %s", calcolo_costoso())
# Se il livello e WARNING, calcolo_costoso() NON viene chiamato
```

Questa ottimizzazione lazy di logging puo fare una differenza significativa in loop stretti.

### Motivo 5 — Thread safety e buffering

`print()` non e thread-safe in CPython: in un programma multi-thread, righe di `print()` diverse si possono mescolare producendo output corrotto. Il modulo `logging` usa un lock interno e gestisce correttamente la concorrenza.

Inoltre, `stdout` e bufferizzato: in caso di crash, le ultime righe di `print()` potrebbero non essere scritte. I log del modulo `logging` possono essere configurati per essere unbuffered o con flush automatico dopo ogni scrittura.

---

## B2. I Cinque Livelli di Logging e le Loro Analogie

Il modulo `logging` definisce cinque livelli standard, in ordine crescente di gravita:

```
DEBUG    (10) — Informazioni dettagliate per il debugging
INFO     (20) — Conferma che le cose funzionano come previsto
WARNING  (30) — Qualcosa di inaspettato, ma il programma continua
ERROR    (40) — Un errore serio — la funzione non ha potuto completare
CRITICAL (50) — Un errore grave — il programma potrebbe non continuare
```

### DEBUG — Il detective che annota tutto

```python
logger.debug("Connessione al DB: host=%s, porta=%d, timeout=%d", host, porta, timeout)
logger.debug("Cache miss per chiave: %r — carico dal DB", chiave)
logger.debug("Token JWT decodificato: sub=%s, exp=%d", payload["sub"], payload["exp"])
```

`DEBUG` e per informazioni che vuoi vedere solo quando stai investigando un problema specifico. Non attivare `DEBUG` in produzione per default — genera troppo rumore e puo esporre dati sensibili.

### INFO — Il diario di bordo

```python
logger.info("Applicazione avviata su porta %d", porta)
logger.info("Utente %s autenticato con successo", user_id)
logger.info("Elaborati %d record in %.2f secondi", count, elapsed)
logger.info("Cache caricata: %d chiavi", len(cache))
```

`INFO` registra gli eventi normali del sistema: avvii, autenticazioni, completamenti di operazioni significative. Il livello standard per la produzione quando vuoi un log operativo.

### WARNING — Il cartello "attenzione"

```python
logger.warning("Riprovo connessione al DB (tentativo %d/%d)", tentativo, max_tentativi)
logger.warning(
    "Tasso di errori alto: %.1f%% negli ultimi 5 minuti (soglia: 5%%)",
    tasso_errori * 100
)
logger.warning("File di configurazione mancante — uso valori di default")
logger.warning("Deprecazione: usa nuovo_metodo() invece di vecchio_metodo()")
```

`WARNING` segnala situazioni anomale che non impediscono il funzionamento corrente ma che potrebbero indicare un problema futuro o richiedere attenzione.

### ERROR — La funzione ha fallito

```python
logger.error(
    "Impossibile salvare il record utente id=%d: %s",
    user_id,
    errore,
    exc_info=True,  # include il traceback completo nel log
)
logger.error(
    "Pagamento fallito per ordine #%d: %s",
    ordine_id,
    str(errore_pagamento),
)
```

`ERROR` indica che qualcosa e andato male e la funzione non ha completato il suo lavoro. Il sistema e ancora in piedi, ma questa operazione specifica ha fallito. Usa `exc_info=True` per includere il traceback.

### CRITICAL — Il sistema potrebbe non continuare

```python
logger.critical(
    "Connessione al database persa — impossibile continuare",
    exc_info=True,
)
logger.critical(
    "Disco pieno (%.1f%% usato) — impossibile scrivere log",
    uso_disco_percentuale,
)
logger.critical("Chiave di cifratura non trovata — avvio annullato")
```

`CRITICAL` indica una condizione talmente grave che il programma potrebbe non essere in grado di continuare. Tipicamente seguita da un arresto controllato del processo.

### Regola pratica per scegliere il livello

```
DEBUG    → "Voglio vedere questo solo quando debug-go questo modulo specifico"
INFO     → "Questo e un evento normale che voglio tracciare in produzione"
WARNING  → "Questo e inaspettato ma sto gestendo la situazione"
ERROR    → "Questa operazione e fallita — qualcuno dovrebbe saperlo"
CRITICAL → "Il sistema e in pericolo serio"
```


---

## B3. Architettura Logger/Handler/Formatter/Filter

Il modulo `logging` ha un'architettura a quattro componenti. Capirla e fondamentale per configurare il logging correttamente.

### Diagramma dell'architettura

```
Il tuo codice chiama:
  logger.error("Messaggio", extra={...})
       |
       v
  [Logger]  ─── ha un nome gerarchico: "app.services.ordini"
       |          ─── ha un livello minimo (es. DEBUG)
       |          ─── propaga al Logger padre? (propagate=True)
       |
  [Filter]  ─── filtra record basandosi su attributi personalizzati
       |          ─── es. "accetta solo log con user_id != None"
       |
       v
  [Handler] ─── decide dove va il messaggio (stream, file, email, rete)
       |          ─── ha il proprio livello minimo
       |
  [Filter]  ─── filtro a livello di Handler (secondo livello di filtraggio)
       |
       v
  [Formatter] ─── decide come appare il messaggio
                    ─── formato, timestamp, campo extra, JSON, ecc.
```

### I quattro componenti in dettaglio

#### Logger

Il Logger e l'oggetto con cui il tuo codice interagisce. Si ottiene per nome:

```python
import logging

# Convezione: usa sempre il nome del modulo corrente
logger = logging.getLogger(__name__)
```

I Logger formano una gerarchia basata sui nomi separati da punti:
```
root                    (il logger radice)
  app                   (logging.getLogger("app"))
    app.services        (logging.getLogger("app.services"))
      app.services.ordini  (logging.getLogger("app.services.ordini"))
```

Quando un Logger non ha un Handler, il messaggio si propaga al Logger padre (fino al root logger). Questo permette di configurare il logging in un unico posto (il root logger) e tutti i sotto-logger lo usano.

#### Handler

L'Handler decide **dove** va il messaggio:

```python
import logging
import logging.handlers

# StreamHandler: stdout o stderr
stream_handler = logging.StreamHandler()  # default: stderr

# FileHandler: file su disco
file_handler = logging.FileHandler("app.log", encoding="utf-8")

# RotatingFileHandler: file con rotazione per dimensione
rotating_handler = logging.handlers.RotatingFileHandler(
    "app.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,               # mantieni 5 backup
    encoding="utf-8",
)

# TimedRotatingFileHandler: file con rotazione per tempo
timed_handler = logging.handlers.TimedRotatingFileHandler(
    "app.log",
    when="midnight",   # ruota a mezzanotte
    backupCount=30,    # mantieni 30 giorni
    encoding="utf-8",
)
```

#### Formatter

Il Formatter decide **come** appare il messaggio:

```python
# Formato leggibile per sviluppo
formatter_dev = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Formato compatto per produzione
formatter_prod = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
```

**Campi disponibili nel Formatter:**
```
%(asctime)s     — timestamp formattato
%(created)f     — timestamp Unix float
%(filename)s    — nome del file sorgente
%(funcName)s    — nome della funzione
%(levelname)s   — nome del livello (DEBUG, INFO, ...)
%(lineno)d      — numero di riga nel file sorgente
%(message)s     — il messaggio formattato
%(module)s      — nome del modulo
%(name)s        — nome del logger
%(pathname)s    — percorso completo del file sorgente
%(process)d     — PID del processo
%(thread)d      — ID del thread
%(threadName)s  — nome del thread
```

#### Filter

Il Filter permette di filtrare i messaggi in base a criteri personalizzati:

```python
import logging

class FiltroSensibile(logging.Filter):
    """Rimuove i log che contengono dati PII."""

    CAMPI_SENSIBILI = {"password", "token", "carta_credito", "ssn"}

    def filter(self, record: logging.LogRecord) -> bool:
        # Restituisce True se il record DEVE essere loggato
        for campo in self.CAMPI_SENSIBILI:
            if campo in str(record.getMessage()).lower():
                return False  # blocca il record
        return True

# Aggiungere il filtro a un handler
handler = logging.StreamHandler()
handler.addFilter(FiltroSensibile())
```

### Come collegare i componenti

```python
import logging
import logging.handlers

def configura_logging_manuale() -> None:
    # 1. Creare il formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 2. Creare e configurare l'handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    # 3. Configurare il root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
```

Questo approccio manuale e utile per capire l'architettura, ma nella pratica si usa `basicConfig`, `dictConfig`, o `fileConfig`.


---

## B4. Configurazione: basicConfig vs dictConfig vs fileConfig

Ci sono tre modi principali per configurare il logging. Ognuno ha il suo caso d'uso.

### `basicConfig` — Per script semplici e prototipi

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),                        # console
        logging.FileHandler("app.log", encoding="utf-8"),  # file
    ],
)

logger = logging.getLogger(__name__)
logger.info("Applicazione avviata")
```

**Limitazioni di `basicConfig`:**
- Si puo chiamare solo UNA volta — le chiamate successive vengono ignorate se il root logger ha gia handler
- Non permette configurazioni granulari per modulo specifico
- Non e adatto per applicazioni complesse con molti componenti

**Uso ideale:** script standalone, prototipi, applicazioni a singolo file, test.

### `dictConfig` — Per applicazioni reali

```python
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # IMPORTANTE: non disabilitare i logger esistenti

    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)-8s %(name)-30s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "errori": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": "logs/errori.log",
            "maxBytes": 10485760,
            "backupCount": 10,
            "encoding": "utf-8",
        },
    },

    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file", "errori"],
            "propagate": False,  # non propagare al root logger
        },
        "app.database": {
            "level": "INFO",    # il DB genera molto DEBUG — lo sopprimo
            "propagate": True,  # propaga al logger "app"
        },
        "sqlalchemy.engine": {
            "level": "WARNING", # le query SQL sono rumorose
            "propagate": True,
        },
    },

    "root": {
        "level": "WARNING",     # per tutto il resto: solo WARNING+
        "handlers": ["console"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

**Vantaggi di `dictConfig`:**
- Configurazione in Python puro (dizionario) — type-safe, refactorable
- Si puo leggere da JSON, YAML, o costruire programmaticamente
- Granulare: ogni logger puo avere livello e handler diversi
- `disable_existing_loggers: False` e cruciale: se True, disabilita i logger di librerie terze

### `fileConfig` — Per configurazione in file INI

```ini
# logging.conf

[loggers]
keys=root,app

[handlers]
keys=console,file

[formatters]
keys=standard

[logger_root]
level=WARNING
handlers=console

[logger_app]
level=DEBUG
handlers=console,file
qualname=app
propagate=0

[handler_console]
class=StreamHandler
level=DEBUG
formatter=standard
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=standard
args=('app.log', 'a', 10485760, 5, 'utf-8')

[formatter_standard]
format=%(asctime)s %(levelname)-8s %(name)s %(message)s
datefmt=%Y-%m-%d %H:%M:%S
```

```python
import logging.config

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
```

**`fileConfig` e legacy** — introdotto in Python 2. Preferisci `dictConfig` per nuovi progetti: e piu espressivo e non richiede la sintassi INI.

### Quale scegliere

| Scenario | Soluzione |
|---------|-----------|
| Script one-shot, prototipo | `basicConfig` |
| Applicazione Flask/FastAPI con YAML config | `dictConfig` + `yaml.safe_load` |
| Applicazione Django | `LOGGING` dict nel `settings.py` (usa `dictConfig`) |
| Legacy codebase con file .conf | `fileConfig` |
| Logging strutturato JSON in produzione | `dictConfig` + formatter JSON o structlog |

### Configurare il logging da YAML

```python
import yaml
import logging.config
from pathlib import Path

def configura_logging(config_path: str = "logging.yaml") -> None:
    percorso = Path(config_path)
    if percorso.exists():
        with percorso.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(
            "File logging.yaml non trovato — uso configurazione di base"
        )
```


---

## B5. Handler Avanzati: Rotazione, Email, Queue

### RotatingFileHandler — Rotazione per dimensione

```python
import logging
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    filename="logs/app.log",
    mode="a",              # append
    maxBytes=10 * 1024 * 1024,   # 10 MB
    backupCount=5,                # mantieni 5 backup: app.log.1, .2, ..., .5
    encoding="utf-8",
    delay=False,           # crea il file subito (True = solo alla prima scrittura)
)
```

**Come funziona la rotazione:**
- Quando `app.log` raggiunge 10 MB, viene rinominato `app.log.1`
- `app.log.1` diventa `app.log.2`, ecc.
- Se esistono gia 5 backup, `app.log.5` viene eliminato
- Viene creato un nuovo `app.log` vuoto

### TimedRotatingFileHandler — Rotazione per tempo

```python
handler = logging.handlers.TimedRotatingFileHandler(
    filename="logs/app.log",
    when="midnight",    # ruota a mezzanotte locale
    interval=1,         # ogni 1 giorno
    backupCount=30,     # mantieni 30 giorni di log
    encoding="utf-8",
    utc=False,          # usa ora locale (True = usa UTC)
)
```

**Valori per `when`:**
```
"S"          — secondi
"M"          — minuti
"H"          — ore
"D"          — giorni
"W0"-"W6"    — giorno specifico della settimana (W0 = lunedi)
"midnight"   — a mezzanotte
```

Il file viene rinominato con il timestamp: `app.log.2024-01-15`.

### SMTPHandler — Email per errori critici

```python
import logging.handlers

smtp_handler = logging.handlers.SMTPHandler(
    mailhost=("smtp.gmail.com", 587),
    fromaddr="alerts@azienda.com",
    toaddrs=["team@azienda.com"],
    subject="[CRITICO] Errore applicazione in produzione",
    credentials=("alerts@azienda.com", "password_app"),
    secure=(),   # usa STARTTLS
)
smtp_handler.setLevel(logging.CRITICAL)

root_logger = logging.getLogger()
root_logger.addHandler(smtp_handler)
```

**Attenzione:** `SMTPHandler` e sincrono — blocca il thread mentre invia l'email. In produzione combinalo con `QueueHandler` per non bloccare.

### QueueHandler e QueueListener — Logging Asincrono

In applicazioni ad alta concorrenza, scrivere su file o inviare email per ogni log puo essere un collo di bottiglia. `QueueHandler` + `QueueListener` separa la produzione dei log dalla loro elaborazione:

```python
import logging
import logging.handlers
import queue
import atexit

def configura_logging_asincrono() -> None:
    # 1. Crea la coda in memoria
    log_queue: queue.Queue = queue.Queue(maxsize=10000)

    # 2. QueueHandler: il tuo codice scrive qui — veloce, non blocca
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # 3. Gli handler reali (lenti) vengono gestiti in un thread separato
    file_handler = logging.handlers.RotatingFileHandler(
        "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    ))

    # 4. QueueListener: thread separato che consuma dalla coda
    listener = logging.handlers.QueueListener(
        log_queue,
        file_handler,
        respect_handler_level=True,
    )
    listener.start()

    # 5. Ferma il listener alla chiusura dell'applicazione
    atexit.register(listener.stop)

    # 6. Configura il root logger con solo il QueueHandler
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.DEBUG)
```

**Flusso dei messaggi:**
```
Thread 1: logger.error(...)  -->  QueueHandler --> [coda in memoria]
Thread 2: logger.info(...)   -->  QueueHandler --> [coda in memoria]
Thread 3: logger.debug(...) -->  QueueHandler --> [coda in memoria]
                                                         |
                                               [Thread del listener]
                                                         |
                                               FileHandler / SMTPHandler / ...
```

Il QueueListener usa un thread daemon separato: i thread principali non aspettano mai che il log venga scritto su disco.

### NullHandler — Per le librerie

Se stai sviluppando una libreria (non un'applicazione), aggiungi solo un `NullHandler`:

```python
# nel file __init__.py della tua libreria
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
```

Questo segue la best practice: le librerie NON configurano il logging. E responsabilita dell'applicazione che le usa. Il `NullHandler` previene il warning "No handlers could be found for logger 'mia_libreria'".


---

## B6. structlog — Logging Strutturato Moderno

Il modulo `logging` della stdlib e potente ma verboso e orientato a messaggi in formato testo. `structlog` e una libreria moderna che produce log strutturati (JSON) e ha un'architettura a processori piu componibile.

```bash
pip install structlog
```

### Perche structlog

Con la stdlib, un log strutturato richiede questo:

```python
logger.info(
    "Pagamento elaborato",
    extra={
        "user_id": 42,
        "importo": 99.99,
        "valuta": "EUR",
        "metodo": "carta",
    }
)
```

Con structlog, la sintassi e piu naturale:

```python
logger.info(
    "pagamento_elaborato",
    user_id=42,
    importo=99.99,
    valuta="EUR",
    metodo="carta",
)
```

### Configurazione base di structlog

```python
import structlog
import logging

def configura_structlog() -> None:
    # Configurare la stdlib per gestire i log passati da structlog
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG,
    )

    structlog.configure(
        processors=[
            # 1. Aggiunge timestamp ISO 8601
            structlog.processors.TimeStamper(fmt="iso"),
            # 2. Aggiunge livello di log come campo
            structlog.stdlib.add_log_level,
            # 3. Aggiunge nome del logger
            structlog.stdlib.add_logger_name,
            # 4. Renderizza lo stack trace come stringa
            structlog.processors.StackInfoRenderer(),
            # 5. Formatta le eccezioni
            structlog.processors.ExceptionRenderer(),
            # 6. Output finale: JSON in produzione, colori in sviluppo
            structlog.dev.ConsoleRenderer(),   # sviluppo
            # structlog.processors.JSONRenderer(),  # produzione
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Bound logger e context binding

Una delle funzionalita piu potenti di structlog e il "context binding": puoi associare campi a un logger e questi appaiono in tutti i log successivi.

```python
import structlog

logger = structlog.get_logger(__name__)

def processa_ordine(ordine_id: int, user_id: int) -> None:
    # Crea un logger con contesto legato: tutti i log successivi includeranno questi campi
    log = logger.bind(ordine_id=ordine_id, user_id=user_id)

    log.info("inizio_elaborazione_ordine")

    try:
        carica_prodotti(ordine_id)
        log.info("prodotti_caricati")

        processa_pagamento(ordine_id)
        log.info("pagamento_completato")

    except PagamentoError as e:
        log.error("pagamento_fallito", errore=str(e), codice=e.codice)
        raise

    log.info("ordine_completato")
```

Output JSON (produzione):
```json
{"timestamp": "2024-01-15T14:32:07.891Z", "level": "info", "logger": "app.ordini", "event": "inizio_elaborazione_ordine", "ordine_id": 12345, "user_id": 42}
{"timestamp": "2024-01-15T14:32:07.921Z", "level": "info", "logger": "app.ordini", "event": "prodotti_caricati", "ordine_id": 12345, "user_id": 42}
```

### Context vars: correlation ID automatico

In applicazioni web, ogni richiesta HTTP dovrebbe avere un `correlation_id` unico che appare in tutti i log generati durante quella richiesta. Con `structlog.contextvars`:

```python
import structlog
import uuid
from structlog.contextvars import bind_contextvars, clear_contextvars

def configura_strutlog_con_contextvars() -> None:
    structlog.configure(
        processors=[
            # IMPORTANTE: deve essere il primo processore
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


# Middleware FastAPI per correlation ID
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Genera o usa il correlation_id dall'header
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )

        # Pulisci il contesto dalla richiesta precedente
        clear_contextvars()

        # Binding del contesto per TUTTI i log di questa richiesta
        bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        # Includi il correlation_id nella risposta per il client
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

Con questo middleware, qualsiasi `logger.info(...)` dentro qualsiasi funzione chiamata durante la richiesta includera automaticamente `correlation_id`, `method`, e `path` nel log — senza doverli passare esplicitamente.

### Integration con la stdlib logging

structlog puo essere usato insieme alla stdlib logging. Questo e utile quando hai librerie che usano la stdlib e vuoi che tutti i log siano nello stesso formato:

```python
import logging
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,  # passa a stdlib logging
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configura la stdlib per il formato finale
logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()],
)
```

---

*Fine Blocco 3. Continua nel Blocco 4 con la Parte C — 10 esercizi guidati con soluzione commentata.*


---

# PARTE C — Esercizi Guidati

Ogni esercizio indica il livello di difficolta:
- **Base**: applica direttamente i concetti del tutorial
- **Intermedio**: combina piu concetti, richiede ragionamento
- **Avanzato**: richiede pattern non triviali, progettazione

---

## Esercizio 1 — Sistema di Validazione con Gerarchia di Eccezioni

**Livello:** Base

**Obiettivo:** Costruire un sistema di validazione utente con eccezioni custom strutturate.

**Requisiti:**
- Crea una gerarchia: `ValidazioneError` (base) > `CampoMancanteError`, `FormatoNonValidoError`, `ValoreOutOfRangeError`
- Implementa `valida_utente(dati: dict) -> None` che valida nome, email, eta, telefono
- Ogni eccezione deve portare: `campo`, `valore`, `motivo`

**Soluzione commentata:**

```python
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


class ValidazioneError(Exception):
    """Errore base per la validazione."""

@dataclass(frozen=True)
class CampoMancanteError(ValidazioneError):
    campo: str
    def __str__(self) -> str:
        return f"Campo obbligatorio mancante: {self.campo!r}"

@dataclass(frozen=True)
class FormatoNonValidoError(ValidazioneError):
    campo: str
    valore: str
    motivo: str
    def __str__(self) -> str:
        return f"Formato non valido per {self.campo!r}: {self.motivo} (valore: {self.valore!r})"

@dataclass(frozen=True)
class ValoreOutOfRangeError(ValidazioneError):
    campo: str
    valore: object
    minimo: object
    massimo: object
    def __str__(self) -> str:
        return (
            f"Valore fuori intervallo per {self.campo!r}: "
            f"{self.valore!r} non in [{self.minimo}, {self.massimo}]"
        )


def valida_nome(nome: object) -> None:
    if nome is None or nome == "":
        raise CampoMancanteError(campo="nome")
    if not isinstance(nome, str):
        raise FormatoNonValidoError(campo="nome", valore=str(nome), motivo="deve essere una stringa")
    if len(nome) > 100:
        raise FormatoNonValidoError(campo="nome", valore=nome, motivo="massimo 100 caratteri")

def valida_email(email: object) -> None:
    if email is None or email == "":
        raise CampoMancanteError(campo="email")
    if not isinstance(email, str):
        raise FormatoNonValidoError(campo="email", valore=str(email), motivo="deve essere una stringa")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise FormatoNonValidoError(campo="email", valore=email, motivo="formato email non valido")

def valida_eta(eta: object) -> None:
    if eta is None:
        raise CampoMancanteError(campo="eta")
    if not isinstance(eta, int):
        raise FormatoNonValidoError(campo="eta", valore=str(eta), motivo="deve essere un intero")
    if not (18 <= eta <= 120):
        raise ValoreOutOfRangeError(campo="eta", valore=eta, minimo=18, massimo=120)

def valida_telefono(telefono: object) -> None:
    if telefono is None:
        return  # campo opzionale
    if not isinstance(telefono, str):
        raise FormatoNonValidoError(campo="telefono", valore=str(telefono), motivo="deve essere una stringa")
    pattern = re.compile(r"^\+?[\d\s\-()]{7,20}$")
    if not pattern.match(telefono):
        raise FormatoNonValidoError(
            campo="telefono",
            valore=telefono,
            motivo="solo cifre, +, spazi, trattini e parentesi (7-20 caratteri)",
        )

def valida_utente(dati: dict) -> None:
    valida_nome(dati.get("nome"))
    valida_email(dati.get("email"))
    valida_eta(dati.get("eta"))
    valida_telefono(dati.get("telefono"))
    logger.info("Validazione utente OK: email=%s", dati.get("email"))
```

---

## Esercizio 2 — Decorator Retry con Backoff Esponenziale e Logging

**Livello:** Intermedio

**Obiettivo:** Implementare un decorator `@retry` generico con backoff e jitter.

**Requisiti:**
- Parametri: `max_tentativi`, `eccezioni`, `backoff_base` (secondi), `jitter` (bool)
- Loggare ogni tentativo fallito con WARNING, ultimo con ERROR
- Con jitter: aggiungi rumore casuale al backoff per evitare thundering herd

**Soluzione commentata:**

```python
import functools
import logging
import random
import time
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_tentativi: int = 3,
    eccezioni: tuple[type[Exception], ...] = (Exception,),
    backoff_base: float = 1.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """Decorator: riprova in caso di eccezioni con backoff esponenziale.

    Parametri:
        max_tentativi: numero massimo di tentativi (incluso il primo)
        eccezioni: tupla dei tipi di eccezione da riprovare
        backoff_base: tempo base in secondi (raddoppia ogni tentativo)
        jitter: se True, aggiunge rumore casuale (+/- 10%) per evitare
                thundering herd in sistemi distribuiti
    """
    def decorator(funzione: F) -> F:
        @functools.wraps(funzione)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for tentativo in range(1, max_tentativi + 1):
                try:
                    return funzione(*args, **kwargs)
                except eccezioni as e:
                    if tentativo == max_tentativi:
                        logger.error(
                            "Tutti i %d tentativi esauriti per %s: %s",
                            max_tentativi, funzione.__name__, e,
                            exc_info=True,
                        )
                        raise

                    attesa = backoff_base * (2 ** (tentativo - 1))
                    if jitter:
                        attesa += random.uniform(0, attesa * 0.1)

                    logger.warning(
                        "Tentativo %d/%d fallito per %s: %s — riprovo tra %.2fs",
                        tentativo, max_tentativi, funzione.__name__, e, attesa,
                    )
                    time.sleep(attesa)

            raise RuntimeError("Stato impossibile nel retry decorator")

        return wrapper  # type: ignore[return-value]
    return decorator


@retry(max_tentativi=3, eccezioni=(ConnectionError, TimeoutError), backoff_base=0.5)
def chiama_api_esterna(url: str) -> dict:
    """Chiama un endpoint remoto con retry automatico."""
    import urllib.request, json
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())
```

---

## Esercizio 3 — CLI App con Logging Configurabile

**Livello:** Base

**Obiettivo:** CLI che accetta `--verbose` / `--quiet` e configura il logging di conseguenza.

**Soluzione commentata:**

```python
import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def configura_logging(verboso: bool, silenzioso: bool, log_file: str | None) -> None:
    if verboso and silenzioso:
        print("ERRORE: --verbose e --quiet sono incompatibili", file=sys.stderr)
        sys.exit(1)

    livello = logging.DEBUG if verboso else (logging.ERROR if silenzioso else logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=livello,
        format="%(asctime)s %(levelname)-8s %(message)s",
        handlers=handlers,
    )


def elabora_file(percorso: Path) -> None:
    if not percorso.exists():
        raise FileNotFoundError(f"File non trovato: {percorso}")
    logger.debug("Inizio elaborazione: %s", percorso)
    logger.info("Elaborazione completata: %s (%d byte)", percorso, percorso.stat().st_size)


def main() -> int:
    parser = argparse.ArgumentParser(description="Elabora file di dati")
    parser.add_argument("file", nargs="+", help="File da elaborare")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("--log-file", help="Salva log su file")
    args = parser.parse_args()

    configura_logging(args.verbose, args.quiet, args.log_file)
    logger.info("Avvio elaborazione di %d file", len(args.file))

    errori = 0
    for percorso_str in args.file:
        try:
            elabora_file(Path(percorso_str))
        except FileNotFoundError as e:
            logger.error("File non trovato: %s", e)
            errori += 1
        except Exception as e:
            logger.error("Errore inatteso su %s: %s", percorso_str, e, exc_info=True)
            errori += 1

    if errori:
        logger.warning("Completato con %d errori su %d file", errori, len(args.file))
        return 1
    logger.info("Completato senza errori")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## Esercizio 4 — Context Manager per Transazioni con Rollback

**Livello:** Intermedio

**Obiettivo:** Implementare un context manager che garantisce rollback automatico in caso di errore.

**Soluzione commentata:**

```python
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)


class TransazioneError(Exception):
    """Errore durante una transazione di database."""


@contextmanager
def transazione(connessione) -> Generator[None, None, None]:
    """Context manager che avvolge operazioni DB in una transazione.

    Esegue commit se il blocco with termina senza eccezioni.
    Esegue rollback se viene lanciata qualsiasi eccezione.
    Rilancia sempre l'eccezione originale dopo il rollback.
    """
    connessione.begin()
    logger.debug("Transazione avviata")
    try:
        yield  # il codice del blocco with esegue qui
    except Exception as e:
        logger.warning("Errore in transazione — eseguo rollback: %s", e)
        connessione.rollback()
        raise  # rilancia sempre — non inghiottire mai l'errore
    else:
        connessione.commit()
        logger.debug("Transazione completata con commit")


# Uso
def crea_ordine_con_inventario(conn, ordine_data: dict, prodotto_id: int) -> None:
    with transazione(conn):
        # Entrambe queste operazioni sono atomiche
        ordine_id = conn.execute(
            "INSERT INTO ordini (cliente_id, totale) VALUES (?, ?)",
            (ordine_data["cliente_id"], ordine_data["totale"]),
        ).lastrowid
        conn.execute(
            "UPDATE prodotti SET quantita = quantita - 1 WHERE id = ?",
            (prodotto_id,),
        )
        logger.info("Ordine %d creato, inventario aggiornato", ordine_id)
    # commit automatico all'uscita dal with
    # rollback automatico se qualsiasi operazione lancia un'eccezione
```

---

## Esercizio 5 — Parser CSV con Gestione Errori per Record

**Livello:** Intermedio

**Obiettivo:** Leggere un CSV, gestire errori per singolo record senza bloccare l'intera elaborazione.

**Soluzione commentata:**

```python
import csv
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Prodotto:
    id: int
    nome: str
    prezzo: float
    quantita: int


@dataclass
class RisultatoParsing:
    prodotti: list[Prodotto]
    errori: list[dict]  # lista di {"riga": N, "dato": ..., "errore": ...}


def parse_prodotto(riga: dict, numero_riga: int) -> Prodotto:
    """Converte una riga CSV in Prodotto. Lancia ValueError se non valido."""
    try:
        return Prodotto(
            id=int(riga["id"]),
            nome=riga["nome"].strip(),
            prezzo=float(riga["prezzo"]),
            quantita=int(riga["quantita"]),
        )
    except (KeyError, ValueError) as e:
        raise ValueError(f"Riga {numero_riga}: dato non valido — {e}") from e


def carica_prodotti_csv(percorso: Path) -> RisultatoParsing:
    """Carica prodotti da CSV, loggando gli errori senza bloccarsi."""
    prodotti: list[Prodotto] = []
    errori: list[dict] = []

    with percorso.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for numero_riga, riga in enumerate(reader, start=2):  # 2: header e riga 1
            try:
                prodotto = parse_prodotto(riga, numero_riga)
                prodotti.append(prodotto)
            except ValueError as e:
                logger.warning("Riga %d ignorata: %s", numero_riga, e)
                errori.append({"riga": numero_riga, "dato": dict(riga), "errore": str(e)})

    logger.info(
        "CSV caricato: %d prodotti OK, %d errori su %d righe totali",
        len(prodotti), len(errori), len(prodotti) + len(errori),
    )
    return RisultatoParsing(prodotti=prodotti, errori=errori)
```

---

## Esercizio 6 — Circuit Breaker Semplice

**Livello:** Avanzato

**Obiettivo:** Implementare un Circuit Breaker con tre stati: CLOSED, OPEN, HALF-OPEN.

**Concetto:** Il Circuit Breaker protegge un sistema da chiamate ripetute a un servizio che sta fallendo. Dopo N fallimenti consecutivi, apre il circuito (OPEN) per un periodo, poi lo mette in HALF-OPEN per testare se il servizio e tornato.

**Soluzione commentata:**

```python
import logging
import time
from enum import Enum, auto
from typing import Callable, Any

logger = logging.getLogger(__name__)


class StatoCircuito(Enum):
    CLOSED = auto()       # funzionamento normale — le chiamate passano
    OPEN = auto()         # circuito aperto — le chiamate sono bloccate
    HALF_OPEN = auto()    # test — una chiamata di prova viene tentata


class CircuitBreakerAperto(Exception):
    """Lanciata quando il circuito e aperto e la chiamata e bloccata."""


class CircuitBreaker:
    """Implementazione del pattern Circuit Breaker.

    Parametri:
        soglia_fallimenti: fallimenti consecutivi prima di aprire
        timeout_apertura: secondi da aspettare prima di provare HALF_OPEN
        soglia_successi_half_open: successi in HALF_OPEN prima di chiudere
    """

    def __init__(
        self,
        soglia_fallimenti: int = 5,
        timeout_apertura: float = 60.0,
        soglia_successi_half_open: int = 1,
    ) -> None:
        self._stato = StatoCircuito.CLOSED
        self._fallimenti_consecutivi = 0
        self._successi_half_open = 0
        self._apertura_timestamp: float | None = None
        self.soglia_fallimenti = soglia_fallimenti
        self.timeout_apertura = timeout_apertura
        self.soglia_successi_half_open = soglia_successi_half_open

    def chiama(self, funzione: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Esegue la funzione attraverso il circuit breaker."""
        self._aggiorna_stato()

        if self._stato == StatoCircuito.OPEN:
            raise CircuitBreakerAperto(
                f"Circuito APERTO — servizio non disponibile. "
                f"Riprova tra {self._secondi_rimanenti():.0f}s"
            )

        try:
            risultato = funzione(*args, **kwargs)
            self._registra_successo()
            return risultato
        except Exception as e:
            self._registra_fallimento(e)
            raise

    def _aggiorna_stato(self) -> None:
        if self._stato == StatoCircuito.OPEN:
            if self._apertura_timestamp and (
                time.monotonic() - self._apertura_timestamp >= self.timeout_apertura
            ):
                self._stato = StatoCircuito.HALF_OPEN
                self._successi_half_open = 0
                logger.info("Circuit Breaker: OPEN -> HALF_OPEN (test probe)")

    def _registra_successo(self) -> None:
        if self._stato == StatoCircuito.HALF_OPEN:
            self._successi_half_open += 1
            if self._successi_half_open >= self.soglia_successi_half_open:
                self._stato = StatoCircuito.CLOSED
                self._fallimenti_consecutivi = 0
                logger.info("Circuit Breaker: HALF_OPEN -> CLOSED (servizio recuperato)")
        elif self._stato == StatoCircuito.CLOSED:
            self._fallimenti_consecutivi = 0

    def _registra_fallimento(self, errore: Exception) -> None:
        self._fallimenti_consecutivi += 1
        logger.warning(
            "Circuit Breaker: fallimento #%d/%d: %s",
            self._fallimenti_consecutivi, self.soglia_fallimenti, errore,
        )
        if self._fallimenti_consecutivi >= self.soglia_fallimenti:
            self._stato = StatoCircuito.OPEN
            self._apertura_timestamp = time.monotonic()
            logger.error(
                "Circuit Breaker: CLOSED -> OPEN (soglia %d fallimenti raggiunta)",
                self.soglia_fallimenti,
            )

    def _secondi_rimanenti(self) -> float:
        if self._apertura_timestamp is None:
            return 0.0
        trascorso = time.monotonic() - self._apertura_timestamp
        return max(0.0, self.timeout_apertura - trascorso)


# Uso
cb = CircuitBreaker(soglia_fallimenti=3, timeout_apertura=30.0)

def chiama_servizio_esterno(dato: str) -> dict:
    try:
        return cb.chiama(api_client.post, "/processa", json={"dato": dato})
    except CircuitBreakerAperto as e:
        logger.warning("Servizio non disponibile (circuit open): %s", e)
        return {"status": "degraded", "risultato": None}
```

END4A


---

## Esercizio 7 — Analizzatore di File di Log

**Livello:** Base-Intermedio

**Obiettivo:** Leggere un file di log e produrre statistiche su errori, livelli, e moduli.

**Requisiti:**
- Leggi un file di log con formato `timestamp LEVEL modulo messaggio`
- Conta occorrenze per livello (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Trova i 5 moduli con piu errori
- Identifica le righe malformate e loggale come warning

**Soluzione commentata:**

```python
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*)"
    r"\s+(?P<livello>DEBUG|INFO|WARNING|ERROR|CRITICAL)"
    r"\s+(?P<modulo>\S+)"
    r"\s+(?P<messaggio>.+)"
)


@dataclass
class Statistichelog:
    per_livello: Counter = field(default_factory=Counter)
    per_modulo: Counter = field(default_factory=Counter)
    righe_malformate: int = 0
    righe_totali: int = 0


def analizza_log(percorso: Path) -> Statistichelog:
    if not percorso.exists():
        raise FileNotFoundError(f"File di log non trovato: {percorso}")

    stats = Statistichelog()

    with percorso.open(encoding="utf-8", errors="replace") as f:
        for numero_riga, riga in enumerate(f, start=1):
            riga = riga.rstrip()
            if not riga:
                continue

            stats.righe_totali += 1
            match = LOG_PATTERN.match(riga)

            if not match:
                stats.righe_malformate += 1
                logger.debug("Riga %d malformata: %r", numero_riga, riga[:80])
                continue

            livello = match.group("livello")
            modulo = match.group("modulo")

            stats.per_livello[livello] += 1
            if livello in ("ERROR", "CRITICAL"):
                stats.per_modulo[modulo] += 1

    logger.info(
        "Analisi completata: %d righe, %d malformate",
        stats.righe_totali, stats.righe_malformate,
    )
    return stats


def stampa_report(stats: Statistichelog) -> None:
    print(f"\nRighe totali: {stats.righe_totali}")
    print(f"Righe malformate: {stats.righe_malformate}")
    print("\nDistribuzione per livello:")
    for livello in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        count = stats.per_livello.get(livello, 0)
        print(f"  {livello:10s}: {count:6d}")
    print("\nTop 5 moduli per errori:")
    for modulo, count in stats.per_modulo.most_common(5):
        print(f"  {modulo:40s}: {count:4d} errori")
```

---

## Esercizio 8 — Logging con Correlation ID per Web App

**Livello:** Avanzato

**Obiettivo:** Implementare un sistema di correlation ID che persiste attraverso tutte le chiamate di una richiesta HTTP, usando contextvars.

**Requisiti:**
- Ogni richiesta ottiene un UUID unico come correlation_id
- Tutti i log generati durante la richiesta includono il correlation_id
- Non usare variabili globali — usa `contextvars.ContextVar`

**Soluzione commentata:**

```python
import contextvars
import logging
import uuid
from typing import Any

# ContextVar: valore isolato per ogni task/coroutine/thread
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id",
    default="no-correlation-id",
)


class CorrelationIDFilter(logging.Filter):
    """Inietta il correlation_id da ContextVar in ogni LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        return True


def configura_logging_con_correlation() -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s [%(correlation_id)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIDFilter())

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)


def imposta_correlation_id(cid: str | None = None) -> str:
    """Imposta il correlation_id per il contesto corrente."""
    cid = cid or str(uuid.uuid4())
    correlation_id_var.set(cid)
    return cid


logger = logging.getLogger(__name__)


def servizio_a(dato: str) -> str:
    logger.info("Servizio A elabora dato: %s", dato)
    return f"A({dato})"


def servizio_b(dato: str) -> str:
    logger.info("Servizio B elabora dato: %s", dato)
    return f"B({dato})"


def processa_richiesta(dato: str, cid: str | None = None) -> dict[str, Any]:
    correlation_id = imposta_correlation_id(cid)
    logger.info("Inizio elaborazione richiesta")

    try:
        risultato_a = servizio_a(dato)
        risultato_b = servizio_b(risultato_a)
        logger.info("Richiesta completata con successo")
        return {"correlation_id": correlation_id, "risultato": risultato_b}
    except Exception as e:
        logger.error("Richiesta fallita: %s", e, exc_info=True)
        raise


# Esempio di output con correlation_id in ogni riga di log:
# 2024-01-15 14:32:07 INFO     [a3f4b5c6-...] __main__ — Inizio elaborazione
# 2024-01-15 14:32:07 INFO     [a3f4b5c6-...] __main__ — Servizio A elabora...
# 2024-01-15 14:32:07 INFO     [a3f4b5c6-...] __main__ — Servizio B elabora...
```

---

## Esercizio 9 — Test Unitari per Eccezioni Custom

**Livello:** Intermedio

**Obiettivo:** Scrivere test pytest per verificare il comportamento delle eccezioni custom.

**Soluzione commentata:**

```python
import pytest
import logging
from app.validazione import (
    valida_utente,
    ValidazioneError,
    CampoMancanteError,
    FormatoNonValidoError,
    ValoreOutOfRangeError,
)


# TEST PER valida_nome
class TestValidaNome:
    def test_nome_valido(self) -> None:
        valida_utente({"nome": "Mario Rossi", "email": "m@e.it", "eta": 30})

    def test_nome_mancante_lancia_campo_mancante(self) -> None:
        with pytest.raises(CampoMancanteError) as exc_info:
            valida_utente({"nome": None, "email": "m@e.it", "eta": 30})
        assert exc_info.value.campo == "nome"

    def test_nome_vuoto_lancia_campo_mancante(self) -> None:
        with pytest.raises(CampoMancanteError) as exc_info:
            valida_utente({"nome": "", "email": "m@e.it", "eta": 30})
        assert exc_info.value.campo == "nome"

    def test_nome_troppo_lungo_lancia_formato(self) -> None:
        nome_lungo = "X" * 101
        with pytest.raises(FormatoNonValidoError) as exc_info:
            valida_utente({"nome": nome_lungo, "email": "m@e.it", "eta": 30})
        assert exc_info.value.campo == "nome"
        assert "100" in exc_info.value.motivo


# TEST PER valida_email
class TestValidaEmail:
    def test_email_senza_at_lancia_formato(self) -> None:
        with pytest.raises(FormatoNonValidoError) as exc_info:
            valida_utente({"nome": "Mario", "email": "mario-no-at.com", "eta": 30})
        assert exc_info.value.campo == "email"


# TEST PER valida_eta
class TestValidaEta:
    @pytest.mark.parametrize("eta", [18, 50, 120])
    def test_eta_valida(self, eta: int) -> None:
        valida_utente({"nome": "Mario", "email": "m@e.it", "eta": eta})

    @pytest.mark.parametrize("eta", [17, -1, 121, 0])
    def test_eta_fuori_range_lancia_out_of_range(self, eta: int) -> None:
        with pytest.raises(ValoreOutOfRangeError) as exc_info:
            valida_utente({"nome": "Mario", "email": "m@e.it", "eta": eta})
        assert exc_info.value.campo == "eta"
        assert exc_info.value.minimo == 18
        assert exc_info.value.massimo == 120


# TEST PER LA GERARCHIA
class TestGerarchia:
    def test_campo_mancante_e_validazione_error(self) -> None:
        with pytest.raises(ValidazioneError):
            valida_utente({"nome": None, "email": "m@e.it", "eta": 30})

    def test_formato_non_valido_e_validazione_error(self) -> None:
        with pytest.raises(ValidazioneError):
            valida_utente({"nome": "M", "email": "non-email", "eta": 30})


# TEST PER IL LOGGING
class TestLoggingValidazione:
    def test_validazione_ok_genera_log_info(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO):
            valida_utente({"nome": "Mario", "email": "mario@e.it", "eta": 30})
        assert any("Validazione utente OK" in r.message for r in caplog.records)

    def test_validazione_ko_non_genera_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO):
            with pytest.raises(CampoMancanteError):
                valida_utente({"nome": None, "email": "m@e.it", "eta": 30})
        # Nessun log INFO deve essere stato emesso (la validazione e fallita)
        assert not any("OK" in r.message for r in caplog.records)
```

---

## Esercizio 10 — Sistema di Notifica con Fallback

**Livello:** Avanzato

**Obiettivo:** Implementare un sistema di notifica con degradazione graceful: prova Email, poi SMS, poi log, con logging completo di ogni tentativo.

**Soluzione commentata:**

```python
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Notifica:
    titolo: str
    messaggio: str
    destinatario: str
    priorita: int = 1  # 1=normale, 2=alta, 3=critica


class CanaleFallito(Exception):
    """Il canale di notifica ha fallito."""


class CanaleNotifica(ABC):
    @property
    @abstractmethod
    def nome(self) -> str: ...

    @abstractmethod
    def invia(self, notifica: Notifica) -> None: ...


class CanaleEmail(CanaleNotifica):
    @property
    def nome(self) -> str:
        return "email"

    def invia(self, notifica: Notifica) -> None:
        # Simulazione: in produzione qui si chiama un SMTP server
        logger.debug("Email a %s: %s", notifica.destinatario, notifica.titolo)
        # raise CanaleFallito("SMTP server non raggiungibile")  # per testare fallback


class CanaleSlack(CanaleNotifica):
    @property
    def nome(self) -> str:
        return "slack"

    def invia(self, notifica: Notifica) -> None:
        logger.debug("Slack a %s: %s", notifica.destinatario, notifica.titolo)


class CanaleSMS(CanaleNotifica):
    @property
    def nome(self) -> str:
        return "sms"

    def invia(self, notifica: Notifica) -> None:
        logger.debug("SMS a %s: %s", notifica.destinatario, notifica.titolo)


class SistemaNotifica:
    """Sistema di notifica con fallback automatico tra canali.

    Prova i canali in ordine di priorita. Se uno fallisce, passa al
    successivo. Se tutti falliscono, logga come CRITICAL ma NON lancia
    eccezione (non vogliamo che una notifica fallita blocchi il flusso
    principale dell'applicazione).
    """

    def __init__(self, canali: list[CanaleNotifica]) -> None:
        if not canali:
            raise ValueError("Almeno un canale e richiesto")
        self._canali = canali
        logger.info(
            "SistemaNotifica inizializzato con %d canali: %s",
            len(canali),
            [c.nome for c in canali],
        )

    def invia(self, notifica: Notifica) -> bool:
        for canale in self._canali:
            try:
                canale.invia(notifica)
                logger.info(
                    "Notifica inviata via %s a %s: %s",
                    canale.nome, notifica.destinatario, notifica.titolo,
                )
                return True
            except CanaleFallito as e:
                logger.warning(
                    "Canale %s fallito: %s — provo il successivo",
                    canale.nome, e,
                )
            except Exception as e:
                logger.error(
                    "Errore imprevisto nel canale %s: %s",
                    canale.nome, e,
                    exc_info=True,
                )

        # Tutti i canali hanno fallito
        logger.critical(
            "TUTTI I CANALI FALLITI per notifica a %s: %s",
            notifica.destinatario, notifica.titolo,
        )
        return False


# Uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sistema = SistemaNotifica([
        CanaleEmail(),
        CanaleSlack(),
        CanaleSMS(),
    ])

    notifica = Notifica(
        titolo="Pagamento fallito",
        messaggio="Il pagamento per l'ordine #12345 non e andato a buon fine.",
        destinatario="mario.rossi@example.com",
        priorita=2,
    )

    successo = sistema.invia(notifica)
    if not successo:
        logger.critical("Impossibile notificare l'utente — intervento manuale richiesto")
```

---

*Fine Blocco 4. Continua nel Blocco 5 con la Parte D — Argomenti Esperti e la Parte E — Riepilogo, Checklist, Glossario.*


---

# PARTE D — Argomenti Esperti

---

## D1. `sys.exc_info()` e il Modulo `traceback`

### sys.exc_info()

`sys.exc_info()` restituisce una tupla `(tipo, valore, traceback)` dell'eccezione correntemente attiva. Utile quando si deve accedere alle informazioni sull'eccezione in un contesto dove non si ha direttamente accesso alla variabile `as e`.

```python
import sys
import logging

logger = logging.getLogger(__name__)

def log_eccezione_corrente() -> None:
    exc_type, exc_value, exc_tb = sys.exc_info()

    if exc_type is None:
        logger.debug("Nessuna eccezione corrente")
        return

    logger.error(
        "Eccezione attiva: tipo=%s, messaggio=%s",
        exc_type.__name__,
        exc_value,
    )
```

Fuori da un blocco `except`, `sys.exc_info()` restituisce `(None, None, None)`.

### Il modulo `traceback`

Il modulo `traceback` permette di formattare e manipolare i traceback programmaticamente.

```python
import traceback
import logging

logger = logging.getLogger(__name__)

def operazione_rischiosa() -> None:
    try:
        1 / 0
    except ZeroDivisionError:
        # Cattura il traceback come lista di stringhe
        righe_tb = traceback.format_exc()
        logger.error("Errore catturato:\n%s", righe_tb)
        raise


def ispeziona_stack_corrente() -> None:
    # Stampa lo stack di chiamate corrente (senza eccezione)
    for frame_info in traceback.extract_stack():
        logger.debug(
            "Frame: %s:%d in %s",
            frame_info.filename,
            frame_info.lineno,
            frame_info.name,
        )


def format_exception_per_log(e: Exception) -> str:
    """Formatta un'eccezione come stringa per l'inclusione in log strutturati."""
    return "".join(traceback.format_exception(type(e), e, e.__traceback__))
```

**Funzioni piu usate del modulo `traceback`:**

| Funzione | Restituisce | Uso tipico |
|---------|-------------|-----------|
| `format_exc()` | `str` | Log dell'eccezione corrente come stringa |
| `format_exception(t, v, tb)` | `list[str]` | Formatta un'eccezione specifica |
| `print_exc()` | `None` | Stampa su stderr (solo per debug) |
| `extract_tb(tb)` | `StackSummary` | Estrae frame da un traceback |
| `extract_stack()` | `StackSummary` | Estrae lo stack di chiamate corrente |
| `format_tb(tb)` | `list[str]` | Formatta un traceback specifico |

---

## D2. `faulthandler` — Catturare Segfault e Crash Critici

Il modulo `faulthandler` permette di stampare il traceback Python quando il processo riceve un segnale fatale come `SIGSEGV` (segmentation fault), che normalmente causa un crash senza traceback.

```python
import faulthandler
import sys

# Abilita faulthandler su stderr
faulthandler.enable()

# Oppure su un file di log
faulthandler.enable(file=open("crash.log", "w"))
```

Una volta abilitato, se il processo va in segfault, il traceback Python viene scritto su stderr (o sul file specificato) prima della terminazione.

**Quando e utile:**
- Codice che usa estensioni C (`.so`, `.pyd`) che possono crashare
- Codice con `ctypes` o `cffi`
- Debug di crash misteriosi in produzione

**`faulthandler.dump_traceback()` — dump manuale:**

```python
import faulthandler
import signal

# Rispondi a SIGUSR1 con un dump del traceback (utile per debug in produzione)
faulthandler.register(signal.SIGUSR1)
# Poi: kill -SIGUSR1 <PID>  per ottenere il traceback senza fermare il processo
```

---

## D3. QueueHandler Multi-Processo

Quando si usa `multiprocessing`, ogni processo figlio ha il proprio sistema di logging indipendente. Per centralizzare i log di tutti i processi su un file condiviso senza race condition, si usa `QueueHandler` con `multiprocessing.Queue`.

```python
import logging
import logging.handlers
import multiprocessing
import multiprocessing.queues
from typing import Any

logger = logging.getLogger(__name__)


def configura_worker_logging(log_queue: multiprocessing.Queue) -> None:
    """Configura il logging in un processo worker per scrivere sulla queue."""
    # Rimuovi gli handler esistenti (ereditati dal processo padre)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Aggiungi solo il QueueHandler che invia alla queue condivisa
    queue_handler = logging.handlers.QueueHandler(log_queue)
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.DEBUG)


def worker_function(log_queue: multiprocessing.Queue, task_id: int) -> str:
    """Funzione eseguita in un processo worker."""
    configura_worker_logging(log_queue)
    logger_worker = logging.getLogger(f"worker.{task_id}")

    logger_worker.info("Worker %d avviato", task_id)
    try:
        risultato = f"risultato_{task_id}"
        logger_worker.info("Worker %d completato: %s", task_id, risultato)
        return risultato
    except Exception as e:
        logger_worker.error("Worker %d fallito: %s", task_id, e, exc_info=True)
        raise


def avvia_elaborazione_parallela(n_workers: int) -> list[str]:
    log_queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=50000)

    # Handler reale che scrive su file — eseguito nel processo principale
    file_handler = logging.handlers.RotatingFileHandler(
        "workers.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)-30s %(message)s")
    )

    # QueueListener: thread nel processo principale che drena la queue
    listener = logging.handlers.QueueListener(log_queue, file_handler)
    listener.start()

    try:
        with multiprocessing.Pool(processes=n_workers) as pool:
            tasks = [(log_queue, i) for i in range(n_workers)]
            risultati = pool.starmap(worker_function, tasks)
    finally:
        listener.stop()

    return risultati
```

**Perche non puoi scrivere direttamente su file da piu processi:**

Se piu processi scrivono sullo stesso file contemporaneamente senza sincronizzazione, le righe di log si mescolano. La soluzione con `multiprocessing.Queue` garantisce che un solo processo (il padre) scrive su disco.

END5A


---

## D4. OpenTelemetry Log Bridge

OpenTelemetry (OTel) e lo standard de facto per observability distribuita. Il "log bridge" permette di connettere il modulo `logging` della stdlib con il backend OTel, in modo che i log vengano esportati con i campi `trace_id` e `span_id` per correlare log con trace distribuiti.

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

```python
import logging
import logging.config
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs._internal.export import ConsoleLogExporter
from opentelemetry._logs import std_to_otel

logger = logging.getLogger(__name__)


def configura_otel(service_name: str, otel_endpoint: str) -> None:
    resource = Resource.create({"service.name": service_name})

    # 1. Configurare il TracerProvider (per span/trace)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otel_endpoint))
    )
    trace.set_tracer_provider(tracer_provider)

    # 2. Configurare il LoggerProvider (per log)
    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=otel_endpoint))
    )
    set_logger_provider(log_provider)

    # 3. Collegare la stdlib logging a OTel (il "log bridge")
    otel_handler = std_to_otel.LoggingHandler(
        level=logging.DEBUG,
        logger_provider=log_provider,
    )

    # 4. Aggiungere l'handler OTel al root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(otel_handler)
    root_logger.setLevel(logging.DEBUG)

    logger.info("OpenTelemetry configurato: service=%s, endpoint=%s", service_name, otel_endpoint)


# Con questa configurazione, ogni chiamata a logger.info(...) produce:
# - Un LogRecord inviato al backend OTel con trace_id e span_id se in un contesto di trace
# - I log e i trace sono correlati automaticamente nel backend (Jaeger, Grafana Tempo, ecc.)
```

**Perche OTel Log Bridge:**

In sistemi distribuiti, un errore in un servizio A causa una richiesta lenta nel servizio B che causa un timeout nel servizio C. Senza correlation tra log e trace, trovare la root cause richiede di correlare manualmente log di tre servizi. Con OTel, ogni log ha il `trace_id` dello span corrente, permettendo di vedere TUTTI i log di una richiesta distribuita in una vista unica.

---

## D5. Pattern Resiliency: Retry, Circuit Breaker, Graceful Degradation

Questi pattern (gia visti nell'Esercizio 2 e 6) formano la triade della resiliency nei sistemi distribuiti.

### Il problema comune

I sistemi distribuiti falliscono. La rete e inaffidabile. I servizi esterni vanno down. La domanda non e "se" un componente fallira, ma "quando" — e "come reagiamo?"

### Retry con Backoff Esponenziale e Jitter

**Quando usare:** errori transitori (timeout, 503 temporaneo, connessione persa).

**Quando NON usare:** errori permanenti (404, 400 Bad Request, 403 Forbidden) — riprovare non aiuta.

```python
import time
import random
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")

ERRORI_NON_RIPROVABILI = {400, 401, 403, 404, 405, 409, 410, 422}

def retry_http(
    chiamata: Callable[..., Any],
    max_tentativi: int = 3,
    backoff_base: float = 1.0,
) -> Any:
    for tentativo in range(1, max_tentativi + 1):
        risposta = chiamata()
        if risposta.status_code in ERRORI_NON_RIPROVABILI:
            risposta.raise_for_status()  # non riprovare, fallisci subito
        if risposta.status_code < 500:
            return risposta

        if tentativo < max_tentativi:
            attesa = backoff_base * (2 ** (tentativo - 1)) + random.uniform(0, 1)
            logger.warning("Tentativo %d/%d: status=%d — riprovo tra %.1fs",
                           tentativo, max_tentativi, risposta.status_code, attesa)
            time.sleep(attesa)

    risposta.raise_for_status()
```

### Retry Budget (Pattern Google SRE)

Il Retry Budget limita il numero totale di retry in una finestra di tempo per evitare di amplificare i problemi quando un servizio e gia sovraccarico.

```python
import time
import threading
from collections import deque

class BudgetRetry:
    def __init__(self, max_retry_per_minuto: int = 10) -> None:
        self._tentativi: deque[float] = deque()
        self._lock = threading.Lock()
        self._max = max_retry_per_minuto

    def puo_riprovare(self) -> bool:
        ora = time.monotonic()
        with self._lock:
            # Rimuovi retry piu vecchi di 60 secondi
            while self._tentativi and ora - self._tentativi[0] > 60:
                self._tentativi.popleft()
            if len(self._tentativi) >= self._max:
                return False
            self._tentativi.append(ora)
            return True
```

### Graceful Degradation con Fallback

```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

def ottieni_raccomandazioni(user_id: int) -> list[dict]:
    try:
        # Livello 1: raccomandazioni personalizzate (ML model)
        return raccomandazioni_personalizzate(user_id)
    except Exception as e:
        logger.warning(
            "Raccomandazioni personalizzate non disponibili per user=%d: %s",
            user_id, e,
        )

    try:
        # Livello 2: raccomandazioni per categoria (query DB)
        return raccomandazioni_per_categoria(user_id)
    except Exception as e:
        logger.warning(
            "Raccomandazioni per categoria non disponibili: %s", e,
        )

    # Livello 3: fallback statico — sempre disponibile
    logger.info("Usando fallback statico per raccomandazioni")
    return RACCOMANDAZIONI_DEFAULT
```

---

## D6. Sentry SDK — Error Tracking in Produzione

Sentry e un sistema di error tracking che cattura eccezioni in produzione, le de-duplica, e le presenta con contesto completo: breadcrumb, variabili locali, utente, ambiente.

```bash
pip install sentry-sdk
```

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

def configura_sentry(dsn: str, ambiente: str, versione: str) -> None:
    sentry_logging = LoggingIntegration(
        level=logging.WARNING,       # cattura WARNING+ come breadcrumb
        event_level=logging.ERROR,   # invia ERROR+ come eventi Sentry
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=ambiente,        # "production", "staging", "development"
        release=versione,            # "myapp@1.2.3"
        integrations=[sentry_logging],
        traces_sample_rate=0.1,      # campiona 10% delle transazioni per performance
        send_default_pii=False,      # non inviare PII (email, IP) per GDPR
        before_send=filtra_errori_noti,
    )

def filtra_errori_noti(event, hint):
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type = exc_info[0]
        # Non inviare a Sentry gli errori di rate limiting (aspettati)
        if exc_type and issubclass(exc_type, RateLimitError):
            return None
    return event


# Uso con contesto arricchito
def processa_ordine_con_sentry(ordine_id: int, user_id: int) -> None:
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("ordine.id", ordine_id)
        scope.set_user({"id": user_id})
        scope.set_context("ordine", {"id": ordine_id, "stato": "elaborazione"})

        sentry_sdk.add_breadcrumb(
            category="ordine",
            message=f"Inizio elaborazione ordine {ordine_id}",
            level="info",
        )

        try:
            elabora(ordine_id)
            sentry_sdk.add_breadcrumb(
                category="ordine",
                message="Pagamento processato",
                level="info",
            )
        except Exception:
            # Sentry cattura automaticamente l'eccezione con tutto il contesto
            sentry_sdk.capture_exception()
            raise
```

END5B


---

# PARTE E — Riepilogo, Checklist e Riferimenti

---

## Checklist: 40 Punti da Verificare

Usa questa checklist prima di ogni code review o commit su codice che gestisce errori e logging.

### Eccezioni

```
STRUTTURA DEL CODICE
[ ] 01. Ogni blocco except cattura un'eccezione specifica (non Exception generico ovunque)
[ ] 02. Nessun "except: pass" nel codice (VIETATO senza eccezioni)
[ ] 03. Nessun "except Exception: pass" (quasi sempre sbagliato)
[ ] 04. I blocchi except vanno dal piu specifico al piu generico
[ ] 05. "else" usato per separare logica di successo dalla gestione errori
[ ] 06. "finally" usato per rilascio risorse (non per logica di business)
[ ] 07. Nessun "return" nel blocco finally (a meno che sia davvero intenzionale)
[ ] 08. Usato "raise" (bare) invece di "raise e" per rilanciare
[ ] 09. Exception chaining "raise X from Y" preserva il contesto originale
[ ] 10. "raise X from None" usato solo quando il contesto interno e irrilevante

ECCEZIONI CUSTOM
[ ] 11. Esiste una classe base AppError per l'applicazione
[ ] 12. La gerarchia riflette i livelli architetturali (domain, infrastructure, application)
[ ] 13. Le eccezioni custom usano @dataclass(frozen=True)
[ ] 14. Ogni eccezione custom ha campi strutturati (non solo un messaggio)
[ ] 15. Il metodo __str__ produce un messaggio chiaro e utile
[ ] 16. Le eccezioni non portano dati mutable (frozen=True)

MESSAGGI DI ERRORE
[ ] 17. I messaggi di errore includono il valore problematico
[ ] 18. I messaggi di errore includono il valore atteso
[ ] 19. Nessun messaggio generico tipo "Errore" o "Qualcosa e andato storto"
[ ] 20. I messaggi non espongono dettagli di implementazione interna agli utenti
```

### Logging

```
STRUTTURA
[ ] 21. Ogni modulo usa logging.getLogger(__name__)
[ ] 22. Nessun print() usato per output operativo (solo per CLI user-facing output)
[ ] 23. Il livello DEBUG e usato per informazioni di diagnostica
[ ] 24. Il livello INFO e usato per eventi normali del sistema
[ ] 25. Il livello WARNING e usato per situazioni anomale ma gestite
[ ] 26. Il livello ERROR e usato per operazioni fallite (con exc_info=True)
[ ] 27. Il livello CRITICAL e usato per condizioni che mettono a rischio il sistema

CONTENUTO DEI LOG
[ ] 28. Ogni log ERROR include exc_info=True (il traceback)
[ ] 29. I log contengono ID rilevanti (user_id, ordine_id, request_id)
[ ] 30. Nessun dato PII nei log (password, token, carta di credito, SSN)
[ ] 31. Nessuna stringa f-string come primo argomento (usa % formatting)
[ ] 32. I log sono leggibili e utili per chi non conosce il codice
[ ] 33. I log usano correlation_id per tracciare le richieste

CONFIGURAZIONE
[ ] 34. Le librerie usano solo NullHandler (non configurano il logging)
[ ] 35. Le applicazioni configurano il logging all'avvio (una volta sola)
[ ] 36. La configurazione usa dictConfig (non solo basicConfig in produzione)
[ ] 37. I file di log hanno rotazione configurata (RotatingFileHandler o TimedRotating)
[ ] 38. Il livello di log e configurabile senza modificare il codice (variabile d'ambiente)
[ ] 39. I log di produzione sono in formato strutturato (JSON)
[ ] 40. I log di errore vanno in un file separato per facilitare il triage
```

---

## Tabella: Tipo di Errore e Strategia di Gestione

| Tipo di Errore | Esempio Concreto | Strategia | Logging |
|----------------|-----------------|-----------|---------|
| Input invalido da utente | Email senza @, eta negativa | `raise ValidationError` con campo e valore | `WARNING` |
| File non trovato | `config.json` mancante | `raise FileNotFoundError` con percorso | `ERROR` |
| File corrotto | JSON malformato | `raise ValueError from JSONDecodeError` | `ERROR` |
| Chiave mancante in dizionario | `dati["campo"]` mancante | Check preventivo o `except KeyError` con default | `WARNING` o niente |
| Errore di rete temporaneo | Timeout, ConnectionReset | Retry con backoff esponenziale | `WARNING` per tentativo, `ERROR` dopo tutti |
| Servizio esterno down | HTTP 503 | Circuit Breaker + graceful degradation | `WARNING` aperto, `ERROR` se fallisce dopo timeout |
| Database non raggiungibile | ConnectionError a Postgres | `raise DatabaseConnectionError` + retry | `CRITICAL` |
| Record non trovato in DB | `SELECT` restituisce 0 righe | `raise NotFoundError(id=...)` | `INFO` o `WARNING` |
| Errore di concorrenza | Race condition, deadlock | Rollback + retry a livello applicativo | `ERROR` |
| Memoria esaurita | `MemoryError` | Terminazione controllata o riduzione carico | `CRITICAL` |
| Stack overflow | `RecursionError` | Refactoring a iterativo, aumento limite | `CRITICAL` |
| Errore di logica | Risultato sbagliato silenzioso | Prevenzione con test; non catturabile | Test unitari |
| KeyboardInterrupt | Ctrl+C | Pulizia e uscita controllata | `INFO` |
| Exception in thread worker | Qualsiasi eccezione in thread | Log + backoff, non lasciare il thread morire silenziosamente | `ERROR` con exc_info |
| Errore asincrono multiplo | Piu task falliscono in TaskGroup | `except*` per tipo, log ogni sotto-gruppo | `ERROR` |

---

## Glossario (35 Termini)

**`add_note()`**
Metodo Python 3.11+ (PEP 678) per aggiungere una nota contestuale a qualsiasi eccezione. Le note appaiono nel traceback dopo il messaggio principale.

**`asyncio.TaskGroup`**
Context manager Python 3.11+ per avviare task asincroni in parallelo. Se uno o piu task falliscono, raccoglie le eccezioni in un `ExceptionGroup`.

**Backoff Esponenziale**
Strategia di retry dove il tempo di attesa raddoppia a ogni tentativo (1s, 2s, 4s, 8s...). Previene il "thundering herd" su servizi in recovery.

**`BaseException`**
La classe radice di tutte le eccezioni Python. Include `SystemExit`, `KeyboardInterrupt`, `GeneratorExit` che non ereditano da `Exception`.

**Breadcrumb (Sentry)**
Evento registrato cronologicamente che contribuisce al contesto di un errore in Sentry. Permette di ricostruire la sequenza di azioni prima del crash.

**Circuit Breaker**
Pattern che monitora i fallimenti di chiamate a servizi esterni. Dopo N fallimenti consecutivi, "apre il circuito" bloccando le chiamate per un periodo, poi le riprova in HALF-OPEN.

**Correlation ID**
Identificatore univoco (UUID) associato a una richiesta e propagato attraverso tutti i servizi e i log per permettere di tracciare l'intera catena di elaborazione.

**`contextlib.suppress`**
Context manager che sopprime eccezioni specificate senza loggare. Alternativa esplicita a `except: pass` per i casi dove ignorare e davvero la risposta corretta.

**`dictConfig`**
Funzione `logging.config.dictConfig()` per configurare il sistema di logging da un dizionario Python. Approccio preferito per applicazioni complesse.

**EAFP (Easier to Ask Forgiveness than Permission)**
Stile Python che assume che un'operazione riuscira e gestisce le eccezioni se non riesce. Contrapposto a LBYL.

**`Exception`**
Classe base per tutte le eccezioni "normali". Non include `SystemExit`, `KeyboardInterrupt`, `GeneratorExit`.

**Exception Chaining (`raise X from Y`)**
Meccanismo Python che preserva l'eccezione originale (`__cause__`) mentre se ne propaga una nuova. Permette di arricchire il contesto senza perdere la causa tecnica.

**`ExceptionGroup`**
Tipo Python 3.11+ (PEP 654) che contiene multiple eccezioni. Usato da `asyncio.TaskGroup` quando piu task falliscono contemporaneamente.

**`except*`**
Sintassi Python 3.11+ per catturare selettivamente eccezioni da un `ExceptionGroup`. Piu clausole `except*` possono eseguire per lo stesso gruppo.

**`exc_info`**
Parametro del modulo `logging` (es. `logger.error(..., exc_info=True)`) che include il traceback completo nel record di log.

**`faulthandler`**
Modulo stdlib che stampa il traceback Python in caso di crash del processo (SIGSEGV, SIGABRT). Utile per debug di estensioni C.

**Filter (logging)**
Componente del modulo `logging` che filtra i record basandosi su criteri personalizzati (livello, contenuto, attributi extra).

**Formatter (logging)**
Componente che determina il formato finale del messaggio di log (timestamp, livello, nome logger, testo).

**Graceful Degradation**
Strategia di fallback dove il sistema continua a funzionare con funzionalita ridotte quando un componente non e disponibile.

**Handler (logging)**
Componente che invia i record di log a una destinazione specifica (file, console, email, rete, coda).

**Jitter**
Rumore casuale aggiunto al backoff esponenziale per evitare che tutti i client riprovino esattamente nello stesso momento ("thundering herd").

**LBYL (Look Before You Leap)**
Stile che verifica le precondizioni prima di tentare un'operazione. Contrapposto a EAFP.

**Logger (logging)**
Oggetto usato dal codice per emettere messaggi di log. Ha un nome gerarchico e propaga al logger padre.

**`logging.NullHandler`**
Handler che non fa nulla. Usato nelle librerie per evitare il warning "No handlers could be found" senza configurare il logging.

**LogRecord**
Oggetto interno del modulo `logging` che contiene tutti i metadati di un singolo evento di log.

**OpenTelemetry (OTel)**
Standard open-source per observability distribuita (trace, metriche, log). Il "log bridge" connette la stdlib logging a OTel.

**`propagate`**
Attributo del Logger che determina se i messaggi vengono passati al logger padre. Default: `True`.

**`QueueHandler` / `QueueListener`**
Coppia di componenti per logging asincrono: `QueueHandler` scrive su una coda in memoria (veloce), `QueueListener` consuma la coda in un thread separato.

**Retry Budget**
Pattern (Google SRE) che limita il numero totale di retry in una finestra di tempo per evitare di amplificare i problemi su servizi sovraccarichi.

**`raise` (bare)**
`raise` senza argomenti rilancia l'eccezione corrente preservando il traceback originale. Preferito a `raise e` per rilanciare.

**`raise X from None`**
Lancia una nuova eccezione sopprimendo il contesto (la catena al predecessore non appare nel traceback). Usato per nascondere dettagli implementativi.

**Structured Logging**
Approccio al logging dove ogni evento e un record con campi chiave-valore (JSON) invece di una stringa libera. Facilita il parsing e la ricerca.

**`structlog`**
Libreria Python per logging strutturato moderno. Pipeline di processori componibili, bound loggers, JSON renderer, integrazione con contextvars.

**Thundering Herd**
Problema in sistemi distribuiti dove molti client riprovano simultaneamente dopo un fallimento, sommergendo ulteriormente il servizio in recovery. Risolto con jitter.

**Traceback**
Sequenza di frame di esecuzione che mostra il percorso delle chiamate che ha portato a un'eccezione. Fondamentale per il debug.

---

## Auto-Valutazione: 8 Domande

Prima di continuare al prossimo tutorial, verifica di saper rispondere a queste domande senza consultare gli appunti:

1. Qual e la differenza tra `except:` e `except Exception:`? Perche la prima e pericolosa?

2. Cosa fa `raise` (senza argomenti) rispetto a `raise e`? Qual e la differenza tecnica?

3. In che ordine vengono eseguiti `except`, `else`, e `finally` in tutti i possibili scenari?

4. Qual e la differenza tra `raise X from Y` e `raise X from None`? Quando usi ciascuno?

5. Perche le librerie Python devono usare solo `NullHandler` e non configurare il logging?

6. Cosa fa `dictConfig` con `disable_existing_loggers: False`? Cosa succederebbe con `True`?

7. Qual e la differenza tra `QueueHandler` e `QueueListener`? Perche sono utili insieme?

8. Come funziona `except*` (con asterisco)? Come si differenzia da `except` normale?

---

## Link e Risorse

### Prossimo Tutorial

`tutorial_08_testing.md` — Testing con pytest: fixture, parametrize, mock, coverage, TDD.

### PEP di Riferimento

- **PEP 654** — Exception Groups e `except*` (Python 3.11)
- **PEP 678** — `add_note()` sulle eccezioni (Python 3.11)
- **PEP 567** — `contextvars.ContextVar` per stato isolato per task

### Documentazione Ufficiale

- Python Logging HOWTO: `https://docs.python.org/3/howto/logging.html`
- logging.config: `https://docs.python.org/3/library/logging.config.html`
- Python Exception Hierarchy: `https://docs.python.org/3/library/exceptions.html`
- structlog docs: `https://www.structlog.org/`
- OpenTelemetry Python: `https://opentelemetry-python.readthedocs.io/`
- Sentry Python SDK: `https://docs.sentry.io/platforms/python/`

---

*Fine Tutorial 07 — Error Handling e Logging.*
*Torna alla directory: `04-PROGRAMMAZIONE-PYTHON/`*
*Prossimo: `tutorial_08_testing.md`*
