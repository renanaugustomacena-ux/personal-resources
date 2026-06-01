---
corso: "Programmazione Python"
fase: "5 — Qualità e Manutenzione"
modulo: "22"
titolo: "Clean Code Python"
versione: "Python 3.12+ / Ruff 0.5+"
livello: "Intermedio"
prerequisiti:
  - "03 — Funzioni e Scope"
  - "07 — OOP"
  - "21 — Design Patterns"
obiettivi:
  - "Applicare le convenzioni PEP 8 e PEP 257 in modo sistematico"
  - "Scrivere funzioni e classi con responsabilita singola e naming espressivo"
  - "Applicare i principi SOLID con pragmatismo Pythonico"
  - "Riconoscere code smells e applicare refactoring appropriati"
  - "Utilizzare type hints, Ruff e mypy per analisi statica"
  - "Misurare la qualita del codice con metriche oggettive (complessita, copertura)"
tag: [clean-code, PEP8, ruff, SOLID, refactoring, type-hints, code-quality, mypy]
---

# Clean Code Python — Guida Completa

> **Modulo 22** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Funzioni e Scope](03-funzioni-scope.md), [OOP](07-oop.md), [Design Patterns](21-design-patterns.md)
>
> Al termine di questo modulo saprai:
> 1. Applicare le convenzioni PEP 8 e PEP 257 in modo sistematico
> 2. Scrivere funzioni piccole (<50 righe) con naming espressivo e responsabilita singola
> 3. Applicare i principi SOLID con pragmatismo Pythonico
> 4. Riconoscere code smells e applicare le tecniche di refactoring appropriate
> 5. Utilizzare type hints, Ruff e mypy per il controllo statico del codice
> 6. Misurare la qualita del codice con metriche oggettive (complessita ciclomatica, copertura)
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio

## Idee guida
1. **PEP 8 + ruff (replaces black + isort + flake8).**
2. **Type hints non opzionali per produzione.**
3. **Function < 50 linee, file < 800 linee.**
4. **Cyclomatic complexity < 10 per function.**


## Indice

1. [Panoramica](#panoramica)
2. [Naming Conventions](#naming-conventions)
3. [Struttura Funzioni](#struttura-funzioni)
4. [Struttura Classi](#struttura-classi)
5. [Code Smells e Refactoring](#code-smells-e-refactoring)
6. [SOLID Principles in Python](#solid-principles-in-python)
7. [Linting e Formatting](#linting-e-formatting)
8. [Documentazione](#documentazione)
9. [Testing come Documentazione](#testing-come-documentazione)
10. [Metriche di Qualita](#metriche-di-qualita)
11. [Best Practices](#best-practices)
12. [Immutabilita in Python](#immutabilita-in-python)
13. [Gestione della Configurazione](#gestione-della-configurazione)
14. [Naming Conventions — Approfondimento](#naming-conventions--approfondimento)
15. [Design delle Funzioni — Approfondimento](#design-delle-funzioni--approfondimento)
16. [Catalogo Esteso dei Code Smells](#catalogo-esteso-dei-code-smells)
17. [Tecniche di Refactoring — Approfondimento](#tecniche-di-refactoring--approfondimento)
18. [Documentazione — Type Stubs e Analisi Statica](#documentazione--type-stubs-e-analisi-statica)
19. [Checklist di Code Review](#checklist-di-code-review)
20. [Gestione del Debito Tecnico](#gestione-del-debito-tecnico)
21. [Clean Architecture in Python](#clean-architecture-in-python)
22. [Pre-commit Hooks — Setup Completo](#pre-commit-hooks--setup-completo)

---

## Panoramica

### Che cos'e il Clean Code

Il termine **clean code** (codice pulito) indica codice sorgente scritto in modo chiaro, leggibile e
manutenibile. Robert C. Martin, nel suo celebre libro *Clean Code: A Handbook of Agile Software
Craftsmanship*, lo definisce cosi: "Il codice pulito e semplice e diretto. Il codice pulito si legge
come una prosa ben scritta."

In Python, il clean code non e un concetto astratto: e parte integrante della filosofia del
linguaggio stesso. Python privilegia la leggibilita sopra ogni altra cosa, e scrivere codice pulito
significa rispettare lo spirito del linguaggio.

**Perche e importante:**

- **Leggibilita**: il codice viene letto molte piu volte di quante venga scritto. Un codice chiaro
  riduce il tempo necessario per comprenderlo.
- **Manutenibilita**: un progetto con codice pulito e piu facile da modificare, estendere e
  correggere.
- **Collaborazione**: in un team, il codice pulito riduce i fraintendimenti e accelera le code
  review.
- **Riduzione dei bug**: il codice chiaro e meno soggetto a errori logici nascosti.
- **Debito tecnico**: scrivere codice pulito fin dall'inizio previene l'accumulo di technical debt.

### Lo Zen di Python

Python ha una filosofia incorporata, accessibile tramite il comando `import this` nell'interprete.
Questi principi guidano ogni decisione di design del linguaggio e dovrebbero guidare anche il nostro
codice:

```python
import this
```

I principi piu rilevanti per il clean code sono:

- **Beautiful is better than ugly** — Il codice dovrebbe essere esteticamente gradevole.
- **Explicit is better than implicit** — Preferire sempre la chiarezza alla brevita criptica.
- **Simple is better than complex** — Se una soluzione semplice funziona, usarla.
- **Complex is better than complicated** — Quando la complessita e necessaria, evitare che diventi
  complicazione.
- **Flat is better than nested** — Evitare nesting eccessivo.
- **Readability counts** — La leggibilita e un requisito, non un optional.
- **There should be one — and preferably only one — obvious way to do it** — Cercare il modo
  idiomatico (Pythonic) di risolvere un problema.
- **If the implementation is hard to explain, it's a bad idea** — Se non riesci a spiegarlo
  facilmente, probabilmente il design e sbagliato.

### PEP 8 — La Guida di Stile Ufficiale

La **PEP 8** e la guida di stile ufficiale per il codice Python. Non e un suggerimento, ma una
convenzione ampiamente adottata dall'intera comunita. I punti principali includono:

- **Indentazione**: 4 spazi (mai tab).
- **Lunghezza righe**: massimo 79 caratteri per il codice, 72 per i docstring.
- **Righe vuote**: 2 righe vuote prima delle definizioni top-level (funzioni, classi), 1 riga vuota
  tra i metodi di una classe.
- **Import**: raggruppati in ordine (standard library, third-party, locali), separati da righe
  vuote.
- **Spazi**: intorno agli operatori di assegnazione, dopo le virgole, mai dentro le parentesi.
- **Encoding**: UTF-8 (default in Python 3).

```python
# Buono - conforme PEP 8
import os
import sys

from collections import defaultdict

from mypackage.mymodule import MyClass


def calcola_totale(prezzi: list[float], sconto: float = 0.0) -> float:
    """Calcola il totale applicando un eventuale sconto."""
    subtotale = sum(prezzi)
    return subtotale * (1 - sconto)


# Cattivo - viola PEP 8
import os, sys
from collections import *
def calcola_totale(prezzi,sconto=0.0):
    subtotale=sum(prezzi)
    return subtotale*(1-sconto)
```

---

## Naming Conventions

Le convenzioni di denominazione sono forse l'aspetto piu impattante del clean code. Un nome ben
scelto elimina la necessita di commenti, rende il codice auto-documentante e riduce il carico
cognitivo di chi legge.

### Variabili e Funzioni: snake_case

In Python, variabili e funzioni usano il formato **snake_case** (tutte le lettere minuscole, parole
separate da underscore):

```python
# Buono
nome_utente = "Mario Rossi"
eta_minima = 18
lista_prodotti = []

def calcola_importo_totale(prodotti: list[Prodotto]) -> Decimal:
    ...

def invia_email_conferma(destinatario: str, ordine: Ordine) -> None:
    ...

# Cattivo
NomeUtente = "Mario Rossi"     # Sembra una classe
etaMinima = 18                 # camelCase (stile Java/JavaScript)
ListaProdotti = []             # PascalCase
```

### Classi: PascalCase

Le classi utilizzano il formato **PascalCase** (CamelCase con la prima lettera maiuscola):

```python
# Buono
class GestoreOrdini:
    ...

class ConnessioneDatabase:
    ...

class ValidatoreEmail:
    ...

# Cattivo
class gestore_ordini:    # Sembra una funzione
    ...

class CONNESSIONE_DB:    # Sembra una costante
    ...
```

### Costanti: UPPER_SNAKE_CASE

Le costanti usano lettere maiuscole con underscore:

```python
# Buono
NUMERO_MASSIMO_TENTATIVI = 3
TIMEOUT_CONNESSIONE_SECONDI = 30
URL_BASE_API = "https://api.esempio.com/v1"
CODICI_ERRORE_CRITICI = frozenset({500, 502, 503})

# Cattivo
maxRetries = 3
timeout = 30          # Non si capisce che e una costante
url_base = "..."      # Sembra una variabile modificabile
```

### Attributi Privati: _prefix e __prefix

Python utilizza le convenzioni di underscore per indicare la visibilita:

```python
class ContoBancario:
    def __init__(self, titolare: str, saldo_iniziale: float = 0.0):
        self.titolare = titolare          # Pubblico
        self._saldo = saldo_iniziale     # "Protetto" (convenzione)
        self.__pin = None                 # Name mangling (fortemente privato)

    def _valida_importo(self, importo: float) -> bool:
        """Metodo interno, non parte dell'API pubblica."""
        return importo > 0

    def __genera_codice_transazione(self) -> str:
        """Metodo strettamente privato, name-mangled."""
        ...
```

- **Singolo underscore** `_attributo`: convenzione che indica "uso interno". Non impedisce l'accesso
  ma segnala che non fa parte dell'API pubblica.
- **Doppio underscore** `__attributo`: attiva il name mangling di Python. L'attributo viene
  rinominato internamente a `_NomeClasse__attributo`. Usare con parsimonia, principalmente per
  evitare conflitti di nomi in gerarchie di ereditarieta.
- **Singolo underscore finale** `attributo_`: usato per evitare conflitti con keyword Python
  (es. `class_`, `type_`, `id_`).

### Nomi Significativi: Evitare Abbreviazioni

I nomi devono comunicare l'intento. Evitare abbreviazioni criptiche e nomi di una sola lettera
(tranne che per variabili di ciclo come `i`, `j`, `k` o per comprehension molto brevi):

```python
# Cattivo - abbreviazioni incomprensibili
def calc_tot(lst, sc):
    t = 0
    for p in lst:
        t += p.pr * p.qt
    return t * (1 - sc)

# Buono - nomi espressivi
def calcola_totale_ordine(prodotti: list[Prodotto], sconto: float) -> Decimal:
    totale = Decimal("0")
    for prodotto in prodotti:
        totale += prodotto.prezzo * prodotto.quantita
    return totale * (1 - Decimal(str(sconto)))

# Eccezione accettabile - variabili di ciclo brevi
matrice = [[1, 2], [3, 4]]
for i, riga in enumerate(matrice):
    for j, valore in enumerate(riga):
        matrice[i][j] = valore * 2

# Eccezione accettabile - comprehension semplici
quadrati = [x ** 2 for x in range(10)]
```

### Nomi Booleani: is_, has_, can_, should_

Le variabili e funzioni booleane dovrebbero iniziare con prefissi che indicano chiaramente una
condizione:

```python
# Buono - esprimono chiaramente una condizione
is_attivo = True
has_permesso_admin = False
can_modificare_profilo = utente.ruolo in ("admin", "editor")
should_inviare_notifica = ordine.stato == "completato"

def is_email_valida(email: str) -> bool:
    ...

def has_scorte_sufficienti(prodotto: Prodotto, quantita: int) -> bool:
    ...

# Cattivo - ambiguo
attivo = True               # Aggettivo da solo, poco chiaro
permesso = False            # Potrebbe essere un oggetto, non un booleano
controlla_email = True      # Sembra il nome di una funzione
```

### Esempi di Naming: Cattivo vs Buono

```python
# --- CATTIVO ---
def proc(d):
    r = []
    for i in d:
        if i["s"] == "a":
            r.append(i)
    return r

# --- BUONO ---
def filtra_utenti_attivi(utenti: list[dict]) -> list[dict]:
    return [
        utente for utente in utenti
        if utente["stato"] == "attivo"
    ]

# --- CATTIVO ---
class Mgr:
    def do(self, t, a):
        ...

# --- BUONO ---
class GestoreTransazioni:
    def esegui_trasferimento(self, conto_origine: str, importo: Decimal):
        ...

# --- CATTIVO ---
x = time.time()
# ...molto codice dopo...
y = time.time()
print(y - x)

# --- BUONO ---
timestamp_inizio = time.time()
# ...molto codice dopo...
timestamp_fine = time.time()
durata_secondi = timestamp_fine - timestamp_inizio
print(f"Operazione completata in {durata_secondi:.2f} secondi")
```

---

## Struttura Funzioni

### Single Responsibility Principle per le Funzioni

Ogni funzione dovrebbe avere una sola responsabilita ben definita. Se la descrizione della funzione
contiene la parola "e" (and), probabilmente sta facendo troppe cose:

```python
# Cattivo - fa troppe cose
def elabora_ordine(ordine: Ordine) -> None:
    # Valida l'ordine
    if not ordine.prodotti:
        raise ValueError("Ordine vuoto")
    if ordine.totale < 0:
        raise ValueError("Totale negativo")

    # Calcola il totale
    totale = sum(p.prezzo * p.quantita for p in ordine.prodotti)
    ordine.totale = totale

    # Salva nel database
    db.session.add(ordine)
    db.session.commit()

    # Invia email di conferma
    msg = crea_messaggio_conferma(ordine)
    server_smtp.send(msg)

# Buono - ogni funzione ha una responsabilita
def valida_ordine(ordine: Ordine) -> None:
    if not ordine.prodotti:
        raise OrdineVuotoError("L'ordine non contiene prodotti")
    if ordine.totale < 0:
        raise TotaleNonValidoError("Il totale non puo essere negativo")

def calcola_totale_ordine(ordine: Ordine) -> Decimal:
    return sum(p.prezzo * p.quantita for p in ordine.prodotti)

def salva_ordine(ordine: Ordine) -> None:
    db.session.add(ordine)
    db.session.commit()

def invia_conferma_ordine(ordine: Ordine) -> None:
    messaggio = crea_messaggio_conferma(ordine)
    server_smtp.send(messaggio)

def elabora_ordine(ordine: Ordine) -> None:
    valida_ordine(ordine)
    ordine.totale = calcola_totale_ordine(ordine)
    salva_ordine(ordine)
    invia_conferma_ordine(ordine)
```

### Funzioni Piccole

Una funzione dovrebbe essere abbastanza piccola da poter essere compresa con un singolo sguardo.
Come regola empirica, una funzione non dovrebbe superare le 20-25 righe. Se supera questo limite, e
probabile che stia facendo troppe cose e andrebbe suddivisa.

### Argomenti delle Funzioni

Il numero ideale di argomenti per una funzione e zero (niladico). Poi uno (monadico), poi due
(diadico). Tre argomenti (triadico) dovrebbero essere evitati dove possibile. Piu di tre richiedono
una giustificazione molto forte.

```python
# Cattivo - troppi argomenti posizionali
def crea_utente(nome, cognome, email, telefono, indirizzo, citta, cap, ruolo):
    ...

# Buono - usare keyword arguments
def crea_utente(
    *,
    nome: str,
    cognome: str,
    email: str,
    telefono: str | None = None,
    indirizzo: str | None = None,
    citta: str | None = None,
    cap: str | None = None,
    ruolo: str = "utente",
) -> Utente:
    ...

# Ancora meglio - usare una dataclass come parameter object
@dataclass
class DatiRegistrazione:
    nome: str
    cognome: str
    email: str
    telefono: str | None = None
    indirizzo: str | None = None
    citta: str | None = None
    cap: str | None = None
    ruolo: str = "utente"

def crea_utente(dati: DatiRegistrazione) -> Utente:
    ...
```

### Pattern Return Early

Il pattern **return early** (uscita anticipata) consiste nel gestire i casi eccezionali all'inizio
della funzione e restituire immediatamente, evitando nesting profondo:

```python
# Cattivo - nesting profondo
def processa_pagamento(ordine: Ordine) -> Risultato:
    if ordine is not None:
        if ordine.stato == "confermato":
            if ordine.totale > 0:
                if ordine.metodo_pagamento is not None:
                    # Finalmente la logica principale, indentata 4 livelli
                    risultato = gateway.addebita(ordine)
                    return risultato
                else:
                    return Risultato(errore="Metodo di pagamento mancante")
            else:
                return Risultato(errore="Totale non valido")
        else:
            return Risultato(errore="Ordine non confermato")
    else:
        return Risultato(errore="Ordine nullo")

# Buono - return early (guard clauses)
def processa_pagamento(ordine: Ordine) -> Risultato:
    if ordine is None:
        return Risultato(errore="Ordine nullo")
    if ordine.stato != "confermato":
        return Risultato(errore="Ordine non confermato")
    if ordine.totale <= 0:
        return Risultato(errore="Totale non valido")
    if ordine.metodo_pagamento is None:
        return Risultato(errore="Metodo di pagamento mancante")

    return gateway.addebita(ordine)
```

### Evitare Side Effects

Una funzione con **side effects** modifica stato al di fuori del proprio scope locale. Questo rende
il codice piu difficile da testare, ragionare e debuggare:

```python
# Cattivo - side effects nascosti
totale_globale = 0

def aggiungi_al_totale(importo: float) -> float:
    global totale_globale
    totale_globale += importo    # Side effect: modifica stato globale
    log.info(f"Aggiunto {importo}")  # Side effect: I/O
    return totale_globale

# Buono - funzione pura (o side effects espliciti)
def calcola_nuovo_totale(totale_corrente: float, importo: float) -> float:
    """Calcola il nuovo totale. Funzione pura senza side effects."""
    return totale_corrente + importo
```

### Funzioni Pure

Una **funzione pura** e una funzione che: (1) dato lo stesso input, restituisce sempre lo stesso
output, (2) non ha side effects. Le funzioni pure sono piu facili da testare, comporre e ragionare:

```python
# Funzione pura - ideale
def calcola_sconto(prezzo: Decimal, percentuale: float) -> Decimal:
    return prezzo * Decimal(str(1 - percentuale))

# Funzione pura - nessuna dipendenza esterna
def filtra_prodotti_disponibili(prodotti: list[Prodotto]) -> list[Prodotto]:
    return [p for p in prodotti if p.quantita_disponibile > 0]

# Non pura ma necessaria - i side effects sono evidenti dal nome
def salva_prodotto_su_database(prodotto: Prodotto) -> None:
    db.session.add(prodotto)
    db.session.commit()
```

### Docstrings

Python supporta tre stili principali di docstring. Indipendentemente dallo stile scelto, la
coerenza all'interno del progetto e fondamentale.

**Stile Google:**

```python
def cerca_utenti(query: str, limite: int = 10, solo_attivi: bool = True) -> list[Utente]:
    """Cerca utenti nel database in base a una query testuale.

    Esegue una ricerca full-text sui campi nome, cognome e email.
    I risultati sono ordinati per rilevanza decrescente.

    Args:
        query: Testo da cercare nei campi utente.
        limite: Numero massimo di risultati da restituire.
        solo_attivi: Se True, esclude gli utenti disattivati.

    Returns:
        Lista di oggetti Utente corrispondenti alla query, ordinati
        per rilevanza. Lista vuota se nessun risultato.

    Raises:
        QueryNonValidaError: Se la query e vuota o contiene solo spazi.
        ConnessioneDBError: Se il database non e raggiungibile.
    """
    ...
```

**Stile NumPy:**

```python
def calcola_statistiche(valori: list[float]) -> dict[str, float]:
    """
    Calcola le statistiche descrittive di una serie di valori.

    Parameters
    ----------
    valori : list[float]
        Lista di valori numerici da analizzare.
        Deve contenere almeno un elemento.

    Returns
    -------
    dict[str, float]
        Dizionario con le seguenti chiavi:
        - 'media': media aritmetica
        - 'mediana': valore mediano
        - 'dev_std': deviazione standard

    Raises
    ------
    ValueError
        Se la lista e vuota.
    """
    ...
```

**Stile Sphinx (reST):**

```python
def invia_notifica(destinatario: str, messaggio: str, priorita: int = 1) -> bool:
    """Invia una notifica push al destinatario specificato.

    :param destinatario: ID univoco del destinatario.
    :param messaggio: Testo della notifica da inviare.
    :param priorita: Livello di priorita (1=bassa, 5=critica).
    :returns: True se la notifica e stata inviata con successo.
    :rtype: bool
    :raises DestinatarioNonTrovatoError: Se l'ID non corrisponde a nessun utente.
    """
    ...
```

---

## Struttura Classi

### Single Responsibility per le Classi

Cosi come per le funzioni, ogni classe dovrebbe avere una sola ragione per cambiare. Se una classe
gestisce sia la logica di business che la persistenza dei dati, ha troppe responsabilita:

```python
# Cattivo - troppe responsabilita
class Ordine:
    def calcola_totale(self) -> Decimal:
        ...
    def applica_sconto(self, codice: str) -> None:
        ...
    def salva_su_database(self) -> None:           # Persistenza
        ...
    def invia_email_conferma(self) -> None:        # Notifiche
        ...
    def genera_pdf_fattura(self) -> bytes:          # Rendering
        ...

# Buono - responsabilita separate
class Ordine:
    def calcola_totale(self) -> Decimal:
        ...
    def applica_sconto(self, codice: str) -> None:
        ...

class RepositoryOrdini:
    def salva(self, ordine: Ordine) -> None:
        ...

class NotificatoreOrdini:
    def invia_conferma(self, ordine: Ordine) -> None:
        ...

class GeneratoreFattureOrdini:
    def genera_pdf(self, ordine: Ordine) -> bytes:
        ...
```

### Classi Piccole e Focalizzate

Una classe dovrebbe essere piccola non in termini di righe, ma in termini di responsabilita. Se non
riesci a descrivere lo scopo della classe in una frase senza usare "e" o "o", probabilmente fa
troppe cose.

### Composizione invece di Ereditarieta

L'ereditarieta crea un accoppiamento forte tra le classi. La composizione offre maggiore
flessibilita e rende il codice piu facile da modificare:

```python
# Cattivo - ereditarieta profonda e fragile
class Animale:
    def muovi(self): ...

class Mammifero(Animale):
    def allatta(self): ...

class Cane(Mammifero):
    def abbaia(self): ...

class CaneGuida(Cane):
    def guida_persona(self): ...

# Buono - composizione con comportamenti iniettati
class Cane:
    def __init__(
        self,
        movimento: StrategiaMovimento,
        addestramento: Addestramento | None = None,
    ):
        self._movimento = movimento
        self._addestramento = addestramento

    def muovi(self):
        self._movimento.esegui()

    def esegui_compito(self):
        if self._addestramento:
            self._addestramento.esegui()
```

### @property per Attributi Calcolati

Usare `@property` per esporre attributi calcolati come se fossero attributi normali, mantenendo
l'incapsulamento:

```python
class Rettangolo:
    def __init__(self, larghezza: float, altezza: float):
        self._larghezza = larghezza
        self._altezza = altezza

    @property
    def larghezza(self) -> float:
        return self._larghezza

    @larghezza.setter
    def larghezza(self, valore: float) -> None:
        if valore <= 0:
            raise ValueError("La larghezza deve essere positiva")
        self._larghezza = valore

    @property
    def area(self) -> float:
        """Attributo calcolato, di sola lettura."""
        return self._larghezza * self._altezza

    @property
    def perimetro(self) -> float:
        return 2 * (self._larghezza + self._altezza)
```

### __slots__ per Ottimizzazione

Quando una classe ha un set fisso di attributi, `__slots__` riduce il consumo di memoria e
velocizza l'accesso agli attributi:

```python
class Punto:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Utile per classi con molte istanze (es. nodi di un grafo, pixel, ecc.)
class Particella:
    __slots__ = ("posizione_x", "posizione_y", "velocita_x", "velocita_y", "massa")

    def __init__(self, x: float, y: float, vx: float, vy: float, massa: float):
        self.posizione_x = x
        self.posizione_y = y
        self.velocita_x = vx
        self.velocita_y = vy
        self.massa = massa
```

### Dataclasses per Contenitori di Dati

Le `dataclass` sono perfette per classi che servono principalmente a contenere dati, riducendo il
boilerplate e mantenendo il codice pulito:

```python
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Prodotto:
    nome: str
    prezzo: Decimal
    categoria: str
    quantita: int = 0
    tags: list[str] = field(default_factory=list)

    @property
    def is_disponibile(self) -> bool:
        return self.quantita > 0

    @property
    def valore_inventario(self) -> Decimal:
        return self.prezzo * self.quantita


@dataclass(frozen=True)
class Coordinate:
    """Dataclass immutabile per coordinate geografiche."""
    latitudine: float
    longitudine: float

    def __post_init__(self):
        if not -90 <= self.latitudine <= 90:
            raise ValueError(f"Latitudine non valida: {self.latitudine}")
        if not -180 <= self.longitudine <= 180:
            raise ValueError(f"Longitudine non valida: {self.longitudine}")
```

---

## Code Smells e Refactoring

### Code Smells Comuni

I **code smells** (odori del codice) sono segnali che indicano problemi strutturali. Non sono bug,
ma indizi che il design potrebbe essere migliorato.

#### Long Methods (Metodi Lunghi)

Funzioni che superano le 20-30 righe sono spesso troppo complesse. Contengono troppa logica e
dovrebbero essere suddivise in funzioni piu piccole con nomi descrittivi.

#### God Classes (Classi Dio)

Classi che sanno troppo e fanno troppo. Una classe con decine di metodi e centinaia di righe e un
chiaro segnale che le responsabilita non sono state distribuite correttamente.

#### Feature Envy

Quando un metodo utilizza piu dati e metodi di un'altra classe che della propria. Questo suggerisce
che il metodo dovrebbe essere spostato nella classe di cui "invidia" le caratteristiche:

```python
# Code smell: feature envy
class CalcolatoreSpedizione:
    def calcola_costo(self, ordine: Ordine) -> Decimal:
        # Usa quasi esclusivamente attributi di Ordine
        peso = sum(p.peso * p.quantita for p in ordine.prodotti)
        indirizzo = ordine.indirizzo_spedizione
        distanza = self._calcola_distanza(ordine.magazzino, indirizzo)
        return Decimal(str(peso * distanza * ordine.tariffa_spedizione))
```

#### Magic Numbers e Magic Strings

Valori letterali nel codice senza spiegazione del loro significato:

```python
# Cattivo - numeri e stringhe magici
if utente.eta >= 18:                      # Perche 18?
    ...
if risposta.status_code == 429:           # Cosa significa 429?
    time.sleep(60)                        # Perche 60?
if tipo == "PRE":                         # Cosa e "PRE"?
    ...

# Buono - costanti con nomi esplicativi
ETA_MINIMA_LEGALE = 18
HTTP_TOO_MANY_REQUESTS = 429
PAUSA_RATE_LIMIT_SECONDI = 60
TIPO_CLIENTE_PREMIUM = "PRE"

if utente.eta >= ETA_MINIMA_LEGALE:
    ...
if risposta.status_code == HTTP_TOO_MANY_REQUESTS:
    time.sleep(PAUSA_RATE_LIMIT_SECONDI)
if tipo == TIPO_CLIENTE_PREMIUM:
    ...
```

#### Deep Nesting (Nesting Profondo)

Il codice con piu di 2-3 livelli di indentazione diventa difficile da seguire. Usare return early,
estrarre funzioni ausiliarie o invertire le condizioni:

```python
# Cattivo - nesting troppo profondo
def processa_dati(dati):
    if dati:
        for elemento in dati:
            if elemento.is_valido:
                for campo in elemento.campi:
                    if campo.tipo == "numerico":
                        if campo.valore is not None:
                            # Logica principale sepolta sotto 5 livelli
                            ...

# Buono - logica piatta
def processa_dati(dati):
    if not dati:
        return

    for elemento in dati:
        if not elemento.is_valido:
            continue
        processa_elemento(elemento)

def processa_elemento(elemento):
    for campo in elemento.campi:
        if campo.tipo != "numerico" or campo.valore is None:
            continue
        processa_campo_numerico(campo)
```

#### Codice Duplicato

Il principio **DRY** (Don't Repeat Yourself) e fondamentale. Il codice duplicato significa che ogni
modifica deve essere fatta in piu punti, aumentando il rischio di inconsistenze.

#### Dead Code (Codice Morto)

Codice che non viene mai eseguito: funzioni mai chiamate, variabili mai lette, blocchi `if` con
condizioni sempre false, import inutilizzati. Eliminare senza pieta: il version control conserva la
storia.

#### Commenti che Spiegano il "Cosa" invece del "Perche"

```python
# Cattivo - il commento ripete il codice
# Incrementa il contatore di 1
contatore += 1

# Buono - il commento spiega il perche
# Compensiamo l'offset zero-based dell'API esterna che
# restituisce indici a partire da 0 mentre il nostro sistema usa 1
contatore += 1
```

#### Parametri Booleani (Flag Arguments)

Un parametro booleano spesso indica che la funzione fa due cose diverse:

```python
# Cattivo - il booleano nasconde due comportamenti
def crea_report(dati, dettagliato=False):
    if dettagliato:
        # 50 righe di logica per report dettagliato
        ...
    else:
        # 30 righe di logica per report sintetico
        ...

# Buono - due funzioni separate e chiare
def crea_report_sintetico(dati):
    ...

def crea_report_dettagliato(dati):
    ...
```

### Tecniche di Refactoring

#### Extract Method / Function

Estrarre un blocco di codice in una funzione separata con un nome che ne descrive l'intento:

```python
# Prima del refactoring
def stampa_fattura(ordine):
    print("=" * 40)
    print(f"Fattura #{ordine.id}")
    print(f"Data: {ordine.data}")
    print("-" * 40)
    totale = Decimal("0")
    for prodotto in ordine.prodotti:
        riga = prodotto.prezzo * prodotto.quantita
        totale += riga
        print(f"{prodotto.nome:30s} {riga:>8.2f}")
    print("-" * 40)
    iva = totale * Decimal("0.22")
    print(f"{'Subtotale':30s} {totale:>8.2f}")
    print(f"{'IVA 22%':30s} {iva:>8.2f}")
    print(f"{'TOTALE':30s} {totale + iva:>8.2f}")

# Dopo il refactoring
def stampa_fattura(ordine):
    stampa_intestazione(ordine)
    totale = stampa_righe_prodotti(ordine.prodotti)
    stampa_riepilogo_totali(totale)

def stampa_intestazione(ordine):
    print("=" * 40)
    print(f"Fattura #{ordine.id}")
    print(f"Data: {ordine.data}")
    print("-" * 40)

def stampa_righe_prodotti(prodotti) -> Decimal:
    totale = Decimal("0")
    for prodotto in prodotti:
        riga = prodotto.prezzo * prodotto.quantita
        totale += riga
        print(f"{prodotto.nome:30s} {riga:>8.2f}")
    print("-" * 40)
    return totale

def stampa_riepilogo_totali(totale: Decimal):
    iva = totale * Decimal("0.22")
    print(f"{'Subtotale':30s} {totale:>8.2f}")
    print(f"{'IVA 22%':30s} {iva:>8.2f}")
    print(f"{'TOTALE':30s} {totale + iva:>8.2f}")
```

#### Extract Class

Quando una classe ha troppe responsabilita, estrarre un gruppo coeso di attributi e metodi in una
nuova classe.

#### Replace Conditional with Polymorphism

Sostituire catene di if/elif con il polimorfismo:

```python
# Prima - catena di condizionali
def calcola_area(forma):
    if forma.tipo == "cerchio":
        return math.pi * forma.raggio ** 2
    elif forma.tipo == "rettangolo":
        return forma.larghezza * forma.altezza
    elif forma.tipo == "triangolo":
        return forma.base * forma.altezza / 2
    else:
        raise ValueError(f"Forma sconosciuta: {forma.tipo}")

# Dopo - polimorfismo
from abc import ABC, abstractmethod

class Forma(ABC):
    @abstractmethod
    def calcola_area(self) -> float:
        ...

class Cerchio(Forma):
    def __init__(self, raggio: float):
        self.raggio = raggio

    def calcola_area(self) -> float:
        return math.pi * self.raggio ** 2

class Rettangolo(Forma):
    def __init__(self, larghezza: float, altezza: float):
        self.larghezza = larghezza
        self.altezza = altezza

    def calcola_area(self) -> float:
        return self.larghezza * self.altezza
```

#### Introduce Parameter Object

Raggruppare parametri correlati in un oggetto:

```python
# Prima
def cerca_voli(partenza, arrivo, data_andata, data_ritorno, adulti, bambini, classe):
    ...

# Dopo
@dataclass
class CriterioRicercaVolo:
    partenza: str
    arrivo: str
    data_andata: date
    data_ritorno: date | None = None
    adulti: int = 1
    bambini: int = 0
    classe: str = "economy"

def cerca_voli(criterio: CriterioRicercaVolo):
    ...
```

#### Replace Magic Numbers with Constants

Come gia mostrato nella sezione code smells, sostituire ogni valore letterale con una costante
dal nome significativo.

#### Replace Nested Conditionals with Guard Clauses

Trasformare nesting profondo in una sequenza di guard clauses con return early (come dimostrato
nella sezione sulle funzioni).

#### Move Method

Spostare un metodo nella classe a cui appartiene logicamente, ovvero la classe i cui dati usa
maggiormente. Questa tecnica risolve il code smell di feature envy.

---

## SOLID Principles in Python

I principi **SOLID** sono cinque principi di progettazione orientata agli oggetti che producono
codice piu robusto, flessibile e manutenibile. In Python assumono forme particolari grazie alla
flessibilita del linguaggio.

### S — Single Responsibility Principle (SRP)

Una classe dovrebbe avere una sola ragione per cambiare. In Python, questo si applica anche ai
moduli:

```python
# Cattivo - la classe gestisce sia dati che persistenza e serializzazione
class Utente:
    def __init__(self, nome: str, email: str):
        self.nome = nome
        self.email = email

    def salva_su_db(self): ...
    def carica_da_db(self, id: int): ...
    def to_json(self) -> str: ...
    def from_json(self, data: str): ...
    def invia_email_benvenuto(self): ...

# Buono - responsabilita separate
@dataclass
class Utente:
    nome: str
    email: str

class RepositoryUtenti:
    def salva(self, utente: Utente) -> None: ...
    def carica(self, id: int) -> Utente: ...

class SerializzatoreUtenti:
    def to_json(self, utente: Utente) -> str: ...
    def from_json(self, data: str) -> Utente: ...

class ServizioNotifiche:
    def invia_benvenuto(self, utente: Utente) -> None: ...
```

### O — Open/Closed Principle (OCP)

Le entita software dovrebbero essere aperte all'estensione ma chiuse alla modifica. In Python si
realizza con classi base astratte (ABC) o sfruttando il duck typing:

```python
from abc import ABC, abstractmethod


class EsportatoreDati(ABC):
    @abstractmethod
    def esporta(self, dati: list[dict]) -> bytes:
        ...

class EsportatoreCsv(EsportatoreDati):
    def esporta(self, dati: list[dict]) -> bytes:
        # Logica per CSV
        ...

class EsportatoreJson(EsportatoreDati):
    def esporta(self, dati: list[dict]) -> bytes:
        # Logica per JSON
        ...

class EsportatoreExcel(EsportatoreDati):
    def esporta(self, dati: list[dict]) -> bytes:
        # Aggiunto senza modificare il codice esistente
        ...


# Utilizzo - il codice client non cambia quando si aggiunge un nuovo formato
def genera_report(dati: list[dict], esportatore: EsportatoreDati) -> bytes:
    return esportatore.esporta(dati)
```

### L — Liskov Substitution Principle (LSP)

Le sottoclassi devono poter sostituire le classi base senza alterare il corretto funzionamento del
programma:

```python
# Violazione di LSP
class Uccello:
    def vola(self) -> str:
        return "Sto volando"

class Pinguino(Uccello):
    def vola(self) -> str:
        raise NotImplementedError("I pinguini non volano!")  # Viola LSP!

# Rispetta LSP - gerarchia corretta
class Uccello(ABC):
    @abstractmethod
    def muovi(self) -> str:
        ...

class UccelloVolante(Uccello):
    def muovi(self) -> str:
        return "Sto volando"

class UccelloNonVolante(Uccello):
    def muovi(self) -> str:
        return "Sto camminando"

class Aquila(UccelloVolante):
    pass

class Pinguino(UccelloNonVolante):
    pass

# Qualsiasi Uccello puo essere usato senza sorprese
def fai_muovere(uccello: Uccello) -> str:
    return uccello.muovi()  # Funziona sempre, senza eccezioni inattese
```

### I — Interface Segregation Principle (ISP)

I client non dovrebbero essere forzati a dipendere da interfacce che non usano. In Python, si
realizza con `Protocol` (typing) per interfacce snelle:

```python
from typing import Protocol


# Cattivo - interfaccia troppo ampia
class Lavoratore(Protocol):
    def lavora(self) -> None: ...
    def mangia(self) -> None: ...
    def dormi(self) -> None: ...
    def programma(self) -> None: ...

# Buono - interfacce segregate
class Lavorabile(Protocol):
    def lavora(self) -> None: ...

class Alimentabile(Protocol):
    def mangia(self) -> None: ...

class Programmabile(Protocol):
    def programma(self) -> None: ...


# Le classi implementano solo le interfacce di cui hanno bisogno
class Sviluppatore:
    def lavora(self) -> None:
        self.programma()

    def mangia(self) -> None:
        print("Pausa pranzo")

    def programma(self) -> None:
        print("Scrivo codice Python")

class Robot:
    def lavora(self) -> None:
        print("Eseguo task automatizzato")

    # Non implementa mangia() - non ne ha bisogno!


def assegna_lavoro(lavoratore: Lavorabile) -> None:
    lavoratore.lavora()  # Funziona con Sviluppatore e Robot
```

### D — Dependency Inversion Principle (DIP)

I moduli di alto livello non dovrebbero dipendere da moduli di basso livello. Entrambi dovrebbero
dipendere da astrazioni. In Python, si realizza tramite dependency injection:

```python
from typing import Protocol


class Repository(Protocol):
    def salva(self, entita: dict) -> None: ...
    def trova(self, id: str) -> dict | None: ...

class RepositoryPostgreSQL:
    def salva(self, entita: dict) -> None:
        # Implementazione specifica PostgreSQL
        ...

    def trova(self, id: str) -> dict | None:
        ...

class RepositoryInMemoria:
    """Utile per i test."""
    def __init__(self):
        self._dati: dict[str, dict] = {}

    def salva(self, entita: dict) -> None:
        self._dati[entita["id"]] = entita

    def trova(self, id: str) -> dict | None:
        return self._dati.get(id)


# Il servizio dipende dall'astrazione, non dall'implementazione
class ServizioOrdini:
    def __init__(self, repository: Repository):
        self._repository = repository

    def crea_ordine(self, dati_ordine: dict) -> None:
        # Logica di business
        self._repository.salva(dati_ordine)


# In produzione
servizio = ServizioOrdini(RepositoryPostgreSQL())

# Nei test
servizio_test = ServizioOrdini(RepositoryInMemoria())
```

---

## Linting e Formatting

Gli strumenti di linting e formatting automatizzano il rispetto delle convenzioni stilistiche,
liberando lo sviluppatore dal dover pensare alla formattazione e permettendogli di concentrarsi
sulla logica.

### Ruff

**Ruff** e il linter e formatter piu moderno e veloce per Python. Scritto in Rust, e ordini di
grandezza piu veloce dei tool tradizionali e li sostituisce quasi tutti: flake8, isort, pycodestyle,
pydocstyle, pyupgrade e molti altri.

**Configurazione in `pyproject.toml`:**

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "D",     # pydocstyle
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "SIM",   # flake8-simplify
    "C4",    # flake8-comprehensions
    "RUF",   # ruff-specific rules
    "S",     # flake8-bandit (sicurezza)
    "PTH",   # flake8-use-pathlib
    "ERA",   # eradicate (dead code)
]
ignore = [
    "D100",  # Missing docstring in public module
    "D104",  # Missing docstring in public package
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
known-first-party = ["mio_progetto"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Comandi principali:**

```bash
# Analizzare il codice
ruff check .

# Correggere automaticamente i problemi risolvibili
ruff check --fix .

# Formattare il codice (sostituto di Black)
ruff format .

# Controllare senza modificare
ruff format --check .
```

**Ruff come sostituto universale:** Ruff sostituisce flake8, isort, pycodestyle, pydocstyle e molti
plugin di flake8. Questo semplifica enormemente la configurazione del progetto: un singolo tool
invece di una dozzina.

### Black

**Black** e il formatter "opinionated" per eccellenza. Non offre quasi nessuna opzione di
configurazione, e questa e la sua forza: elimina tutti i dibattiti sulla formattazione.

**Configurazione in `pyproject.toml`:**

```toml
[tool.black]
line-length = 88
target-version = ["py312"]
skip-string-normalization = false  # Black converte in doppi apici per default
```

**Nota:** Ruff include ora un formatter compatibile con Black (`ruff format`). Molti progetti
stanno migrando verso Ruff come unico tool, eliminando la necessita di Black separato.

**Comandi principali:**

```bash
# Formattare tutti i file
black .

# Controllare senza modificare
black --check .

# Mostrare le differenze
black --diff .
```

### isort

**isort** ordina e organizza gli import automaticamente. Con Ruff, isort e integrato e non richiede
installazione separata.

**Configurazione per compatibilita con Black:**

```toml
[tool.isort]
profile = "black"
known_first_party = ["mio_progetto"]
known_third_party = ["fastapi", "pydantic", "sqlalchemy"]
```

**Risultato dell'ordinamento:**

```python
# Prima di isort - import disordinati
from mio_progetto.utils import helper
import json
from collections import defaultdict
import os
from fastapi import FastAPI
import sys

# Dopo isort - import ordinati e raggruppati
import json
import os
import sys
from collections import defaultdict

from fastapi import FastAPI

from mio_progetto.utils import helper
```

### Pre-commit Hooks

I **pre-commit hooks** eseguono automaticamente i controlli prima di ogni commit, impedendo che
codice non conforme entri nel repository.

**Installazione:**

```bash
pip install pre-commit
pre-commit install
```

**File `.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.1
    hooks:
      - id: mypy
        additional_dependencies:
          - types-requests
          - pydantic

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: debug-statements
```

**Comandi utili:**

```bash
# Eseguire su tutti i file (non solo quelli staged)
pre-commit run --all-files

# Aggiornare le versioni dei hook
pre-commit autoupdate

# Installare anche per commit-msg
pre-commit install --hook-type commit-msg
```

**Custom hooks** — E possibile creare hook personalizzati per verifiche specifiche del progetto:

```yaml
  - repo: local
    hooks:
      - id: controlla-migrazioni
        name: Verifica coerenza migrazioni DB
        entry: python scripts/controlla_migrazioni.py
        language: python
        files: ^alembic/versions/
```

---

## Documentazione

### Docstrings

Le docstring sono stringhe di documentazione che descrivono moduli, classi, funzioni e metodi.
In Python, sono la forma primaria di documentazione e sono accessibili a runtime tramite
l'attributo `__doc__`.

**Docstring di modulo:**

```python
"""Modulo per la gestione degli ordini e-commerce.

Questo modulo contiene le classi e le funzioni necessarie per creare,
validare e processare gli ordini del sistema e-commerce. Supporta
pagamenti tramite carta di credito, PayPal e bonifico bancario.

Esempio tipico di utilizzo:

    ordine = crea_ordine(carrello, utente)
    risultato = processa_pagamento(ordine)

Attributi del modulo:
    STATI_ORDINE: Insieme degli stati validi per un ordine.
    TIMEOUT_PAGAMENTO: Timeout in secondi per le operazioni di pagamento.
"""
```

**Docstring di classe:**

```python
class GestoreCache:
    """Cache in memoria con scadenza automatica degli elementi.

    Implementa una cache LRU (Least Recently Used) con supporto per
    TTL (Time To Live) configurabile per ogni elemento inserito.
    Thread-safe tramite l'uso di threading.Lock.

    Attributes:
        capacita: Numero massimo di elementi nella cache.
        ttl_default: Tempo di vita predefinito in secondi.

    Example:
        >>> cache = GestoreCache(capacita=1000, ttl_default=300)
        >>> cache.inserisci("utente:42", dati_utente)
        >>> risultato = cache.recupera("utente:42")
    """
```

**Docstring di funzione — confronto tra i tre stili:**

I tre stili principali sono stati mostrati nella sezione "Struttura Funzioni". La scelta dipende
dal progetto:

- **Google style**: compatto, leggibile, molto diffuso nei progetti open source.
- **NumPy style**: piu verboso, standard nel mondo scientifico (NumPy, SciPy, pandas).
- **Sphinx (reST) style**: integrazione nativa con Sphinx per generare documentazione HTML/PDF.

**Cosa documentare:**

- Lo scopo della funzione/classe (non il "come", ma il "cosa" e il "perche").
- Tutti i parametri con tipo e descrizione.
- Il valore di ritorno con tipo e descrizione.
- Le eccezioni che possono essere sollevate.
- Effetti collaterali significativi.
- Esempi di utilizzo per casi non banali.
- Precondizioni e postcondizioni importanti.

### Type Hints come Documentazione

I type hints rendono le firme delle funzioni auto-documentanti. Combinati con buoni nomi di
parametri, spesso rendono superflua parte della documentazione:

```python
# Senza type hints - servono commenti/docstring per capire i tipi
def filtra_transazioni(transazioni, data_inizio, data_fine, importo_minimo, stati):
    """
    Filtra le transazioni.

    Args:
        transazioni: Lista di dizionari rappresentanti transazioni.
        data_inizio: Data di inizio in formato datetime.
        data_fine: Data di fine in formato datetime.
        importo_minimo: Importo minimo come Decimal.
        stati: Insieme di stringhe con gli stati da includere.
    """
    ...

# Con type hints - la firma si documenta da sola
def filtra_transazioni(
    transazioni: list[Transazione],
    data_inizio: datetime,
    data_fine: datetime,
    importo_minimo: Decimal = Decimal("0"),
    stati: frozenset[StatoTransazione] = TUTTI_GLI_STATI,
) -> list[Transazione]:
    """Filtra le transazioni in base a periodo, importo e stato.

    Restituisce solo le transazioni che rientrano nel periodo specificato,
    superano l'importo minimo e hanno uno degli stati indicati.
    """
    ...
```

### Commenti

#### Quando commentare: il "perche", non il "cosa"

I commenti migliori spiegano il motivo di una decisione, non cosa fa il codice (quello dovrebbe
essere chiaro dal codice stesso):

```python
# Cattivo - descrive il "cosa" (ovvio dal codice)
# Controlla se l'utente e maggiorenne
if utente.eta >= 18:
    ...

# Buono - spiega il "perche"
# L'API del gateway di pagamento richiede un delay minimo di 100ms
# tra richieste consecutive per evitare il rate limiting (vedi doc: link)
time.sleep(0.1)

# Buono - spiega una decisione non ovvia
# Usiamo bisect invece di un semplice 'in' perche la lista e ordinata
# e contiene >100k elementi; la ricerca binaria e O(log n) vs O(n)
indice = bisect.bisect_left(prezzi_ordinati, prezzo_cercato)
```

#### Convenzioni TODO, FIXME, HACK

```python
# TODO: Implementare la paginazione quando il dataset supera i 10k record
# (ticket: PROJ-1234)
risultati = repository.trova_tutti()

# FIXME: Race condition quando due thread accedono simultaneamente alla cache
# Necessario aggiungere un lock o usare una struttura thread-safe
cache[chiave] = valore

# HACK: Workaround per il bug #5678 nella libreria requests v2.31
# Rimuovere quando aggiornano alla v2.32 (fix confermato nel changelog)
risposta.encoding = "utf-8-sig"
```

#### Quando NON commentare

Non commentare nei seguenti casi:

- **Codice ovvio**: `x += 1  # Incrementa x` — inutile.
- **Codice commentato**: eliminare il codice morto; il version control lo conserva.
- **Journal comments**: non usare commenti come changelog all'interno del file; usare i commit
  di git.
- **Commenti di chiusura**: `} # fine del for` — se servono, la funzione e troppo lunga.
- **Commenti come scusa per codice cattivo**: se il codice ha bisogno di spiegazioni dettagliate
  su cosa fa, spesso la soluzione migliore e riscriverlo in modo piu chiaro.

---

## Testing come Documentazione

### I Test come Specifica

Test ben scritti fungono da documentazione eseguibile. Descrivono il comportamento atteso del
sistema in modo preciso e verificabile. A differenza dei commenti, i test non possono diventare
obsoleti: se il codice cambia e i test non vengono aggiornati, falliscono.

```python
class TestCalcoloSconto:
    """Specifica il comportamento del calcolo sconti per gli ordini."""

    def test_sconto_non_applicato_sotto_soglia_minima(self):
        """Gli ordini sotto i 50 EUR non ricevono alcuno sconto."""
        ordine = Ordine(totale=Decimal("49.99"))
        assert calcola_sconto(ordine) == Decimal("0")

    def test_sconto_10_percento_per_ordini_sopra_100_euro(self):
        """Gli ordini sopra i 100 EUR ricevono il 10% di sconto."""
        ordine = Ordine(totale=Decimal("150.00"))
        assert calcola_sconto(ordine) == Decimal("15.00")

    def test_sconto_massimo_non_superato(self):
        """Lo sconto non puo mai superare i 50 EUR."""
        ordine = Ordine(totale=Decimal("1000.00"))
        assert calcola_sconto(ordine) == Decimal("50.00")
```

### Convenzioni di Denominazione dei Test

I nomi dei test dovrebbero descrivere il comportamento atteso in modo leggibile:

```python
# Pattern: test_<comportamento>_<condizione>
def test_registrazione_fallisce_con_email_duplicata():
    ...

def test_login_blocca_account_dopo_5_tentativi_falliti():
    ...

def test_ricerca_restituisce_lista_vuota_senza_risultati():
    ...

# Oppure con classi di raggruppamento
class TestRegistrazioneUtente:
    def test_successo_con_dati_validi(self): ...
    def test_fallimento_con_email_duplicata(self): ...
    def test_fallimento_con_password_debole(self): ...
```

### Pattern Given-When-Then

Il pattern **Given-When-Then** (Arrange-Act-Assert in linguaggio tecnico) struttura ogni test in
tre fasi chiare:

```python
def test_aggiunta_prodotto_aggiorna_totale_carrello():
    # Given (Arrange) - stato iniziale
    carrello = Carrello()
    prodotto = Prodotto(nome="Tastiera", prezzo=Decimal("79.90"))

    # When (Act) - azione da testare
    carrello.aggiungi(prodotto, quantita=2)

    # Then (Assert) - verifica del risultato atteso
    assert carrello.numero_articoli == 2
    assert carrello.totale == Decimal("159.80")


def test_rimozione_ultimo_prodotto_svuota_carrello():
    # Given
    carrello = Carrello()
    prodotto = Prodotto(nome="Mouse", prezzo=Decimal("29.90"))
    carrello.aggiungi(prodotto, quantita=1)

    # When
    carrello.rimuovi(prodotto)

    # Then
    assert carrello.is_vuoto
    assert carrello.totale == Decimal("0")
```

Questo pattern rende ogni test una piccola storia: data una certa situazione, quando succede
qualcosa, allora ci si aspetta un certo risultato. E il modo piu efficace per rendere i test
leggibili e manutenibili.

---

## Metriche di Qualita

Le metriche di qualita del codice forniscono misurazioni oggettive che aiutano a identificare
problemi e a monitorare l'evoluzione della codebase nel tempo.

### Complessita Ciclomatica (radon)

La **complessita ciclomatica** misura il numero di percorsi indipendenti attraverso il codice di
una funzione. Piu alta e la complessita, piu la funzione e difficile da testare e comprendere.

**Installazione e utilizzo di radon:**

```bash
pip install radon

# Calcola la complessita ciclomatica
radon cc mio_progetto/ -a -s

# Output di esempio:
# mio_progetto/ordini.py
#     F 15:0 processa_ordine - C (12)
#     F 45:0 calcola_sconto - A (3)
#     M 80:4 Ordine.valida - B (7)
```

**Scala di valutazione:**

| Grado | Complessita | Rischio               |
| ----- | ----------- | --------------------- |
| A     | 1-5         | Basso, semplice       |
| B     | 6-10        | Basso, ben strutturato |
| C     | 11-20       | Moderato, da rivedere |
| D     | 21-30       | Alto, da semplificare |
| E     | 31-40       | Molto alto, critico   |
| F     | 41+         | Ingestibile           |

**Obiettivo**: mantenere tutte le funzioni sotto il grado C (complessita <= 10). Le funzioni con
complessita > 15 dovrebbero essere prioritarie per il refactoring.

### Maintainability Index

L'**indice di manutenibilita** combina diverse metriche (complessita ciclomatica, Halstead metrics,
righe di codice) in un singolo valore che indica quanto il codice e facile da manutenere:

```bash
# Calcola il maintainability index
radon mi mio_progetto/ -s

# Output di esempio:
# mio_progetto/ordini.py - A (85.32)
# mio_progetto/utils.py - A (92.17)
# mio_progetto/legacy.py - C (45.21)
```

**Scala:**

| Grado | Punteggio | Significato           |
| ----- | --------- | --------------------- |
| A     | 20-100    | Alta manutenibilita   |
| B     | 10-19     | Manutenibilita media  |
| C     | 0-9       | Bassa manutenibilita  |

### Code Coverage

La **copertura del codice** misura quale percentuale del codice viene eseguita durante i test.
E una metrica utile ma non sufficiente: una copertura del 100% non garantisce che tutti i casi
limite siano testati.

```bash
# Installazione
pip install pytest-cov

# Esecuzione con report di copertura
pytest --cov=mio_progetto --cov-report=term-missing --cov-report=html

# Output di esempio:
# Name                      Stmts   Miss  Cover   Missing
# -------------------------------------------------------
# mio_progetto/ordini.py       85     12    86%   45-48, 72-78
# mio_progetto/utils.py        42      3    93%   88-90
# mio_progetto/servizi.py     120     28    77%   ...
# -------------------------------------------------------
# TOTAL                       247     43    83%
```

**Configurazione in `pyproject.toml`:**

```toml
[tool.coverage.run]
source = ["mio_progetto"]
branch = true
omit = [
    "*/test_*",
    "*/migrations/*",
    "*/__main__.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
    "@abstractmethod",
]
```

**Linee guida per la copertura:**

- **80%** e un obiettivo ragionevole per la maggior parte dei progetti.
- **90%+** per librerie pubbliche e codice critico.
- Non inseguire il 100%: alcune righe (error handling estremo, codice di bootstrap) non meritano
  test dedicati.
- La **branch coverage** e piu significativa della line coverage.

### Misurazione del Debito Tecnico

Il **debito tecnico** (technical debt) rappresenta il costo futuro delle scorciatoie prese oggi.
Si puo misurare in modo approssimativo con:

- **Numero di TODO/FIXME/HACK** nel codice.
- **Complessita ciclomatica media** del progetto.
- **Percentuale di codice duplicato**.
- **Numero di violazioni del linter** ignorate o soppresse.
- **Eta delle issue** aperte relative a refactoring.

```bash
# Contare i TODO/FIXME/HACK con ruff
ruff check . --select FIX,TD

# Analisi completa con radon
radon cc . -a -nc    # Solo funzioni con complessita >= C
radon hal .          # Metriche di Halstead
radon raw .          # Metriche raw (LOC, SLOC, commenti, ecc.)
```

### SonarQube — Panoramica

**SonarQube** e una piattaforma di analisi statica del codice che fornisce un quadro completo della
qualita. Supporta Python e offre:

- **Bug detection**: identifica potenziali bug e vulnerabilita.
- **Code smells**: rileva problemi di design e manutenibilita.
- **Security hotspots**: evidenzia potenziali problemi di sicurezza.
- **Technical debt**: stima il tempo necessario per risolvere tutti i problemi.
- **Quality gates**: soglie configurabili per il deploy (es. "niente bug critici, copertura > 80%").
- **Dashboard**: visualizzazione storica dell'evoluzione della qualita.

**Configurazione minima per un progetto Python (`sonar-project.properties`):**

```properties
sonar.projectKey=mio-progetto
sonar.projectName=Il Mio Progetto
sonar.sources=mio_progetto
sonar.tests=tests
sonar.python.version=3.12
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.pylint.reportPaths=pylint-report.txt
```

SonarQube e particolarmente utile in team di grandi dimensioni e in contesti aziendali dove e
necessario monitorare la qualita del codice nel tempo e imporre standard minimi tramite quality
gates nella pipeline CI/CD.

---

## Best Practices

Dieci pratiche fondamentali che riassumono i principi del clean code in Python:

**1. Segui le convenzioni PEP 8 e usa strumenti automatici.**
Non perdere tempo a formattare manualmente il codice. Configura Ruff (o Black + isort) e
pre-commit hooks nel progetto fin dal primo giorno. Lascia che gli strumenti si occupino della
formattazione e concentrati sulla logica.

**2. Scegli nomi significativi e auto-documentanti.**
Un nome ben scelto vale piu di qualsiasi commento. Usa `is_`, `has_`, `can_` per i booleani.
Preferisci nomi lunghi e chiari a abbreviazioni criptiche. Il codice viene letto molte piu volte
di quante venga scritto.

**3. Scrivi funzioni piccole con una sola responsabilita.**
Ogni funzione dovrebbe fare una cosa sola e farla bene. Se supera le 20 righe, valuta se puoi
estrarre sotto-funzioni. Usa il pattern return early per evitare il nesting profondo. Limita gli
argomenti a 3-4 e usa keyword arguments o dataclass per i casi complessi.

**4. Applica i principi SOLID con pragmatismo.**
I principi SOLID non sono regole rigide ma linee guida. In Python, sfrutta Protocol per le
interfacce, la dependency injection per l'inversione delle dipendenze e la composizione al posto
dell'ereditarieta. Non over-engineerizzare: applica SOLID quando la complessita lo giustifica.

**5. Elimina i code smells sistematicamente.**
Impara a riconoscere i code smells (metodi lunghi, classi dio, numeri magici, codice duplicato) e
applica le tecniche di refactoring appropriate. Non lasciare che il debito tecnico si accumuli:
segui la regola del Boy Scout ("lascia il codice piu pulito di come l'hai trovato").

**6. Usa i type hints ovunque.**
I type hints rendono il codice auto-documentante, abilitano il controllo statico con mypy e
migliorano l'esperienza con gli IDE. Dalla Python 3.10+ la sintassi e pulita ed espressiva
(es. `str | None` invece di `Optional[str]`).

**7. Documenta il "perche", non il "cosa".**
Scrivi docstring per le API pubbliche (moduli, classi, funzioni). Nei commenti inline, spiega
le decisioni non ovvie, i workaround e i vincoli esterni. Evita commenti che ripetono il codice.
Usa i test come documentazione eseguibile del comportamento atteso.

**8. Scrivi test leggibili con il pattern Given-When-Then.**
I test sono documentazione vivente. Dai loro nomi descrittivi che spieghino il comportamento
testato. Strutturali con Given (setup), When (azione), Then (asserzione). Mantieni ogni test
focalizzato su un singolo comportamento.

**9. Misura e monitora la qualita del codice.**
Usa radon per la complessita ciclomatica, pytest-cov per la copertura dei test, e Ruff per
l'analisi statica. Configura soglie minime nella CI/CD. Monitora le tendenze nel tempo con
strumenti come SonarQube. Le metriche non mentono.

**10. Rendi il clean code un'abitudine, non un evento.**
Il codice pulito non si ottiene con un "grande refactoring" una volta all'anno. Si costruisce
giorno per giorno, commit dopo commit. Configura gli strumenti automatici, fai code review,
discuti le convenzioni con il team e migliora continuamente. Il clean code e un processo, non
una destinazione.

---

## Immutabilita in Python

L'immutabilita e uno dei pilastri del clean code: un oggetto immutabile, una volta creato, non puo
essere modificato. Questo elimina intere categorie di bug legati a side effects nascosti, race
condition e stato condiviso inaspettato. Python offre diversi meccanismi per implementare
l'immutabilita a vari livelli di rigore.

### Perche l'Immutabilita e Importante

- **Prevedibilita**: un oggetto immutabile si comporta sempre allo stesso modo. Nessun codice
  puo alterarlo dopo la creazione.
- **Thread-safety**: gli oggetti immutabili possono essere condivisi tra thread senza lock.
- **Hashability**: gli oggetti immutabili possono essere usati come chiavi di dizionari e elementi
  di set.
- **Debug semplificato**: se un valore non cambia mai, non serve tracciare chi lo ha modificato.
- **Ragionamento locale**: puoi comprendere il comportamento di una funzione guardando solo i suoi
  input e output, senza preoccuparti di mutazioni esterne.

### Tipi Immutabili Built-in

Python fornisce diversi tipi immutabili nativi:

```python
# Tipi immutabili built-in
stringa: str = "ciao"              # Le stringhe sono sempre immutabili
tupla: tuple[int, ...] = (1, 2, 3) # Le tuple sono immutabili
insieme: frozenset[str] = frozenset({"a", "b", "c"})  # Set immutabile
numero: int = 42                   # int, float, bool, complex sono immutabili
byte_data: bytes = b"dati"         # bytes e immutabile (bytearray no)

# Errore a runtime se si tenta la modifica
try:
    tupla[0] = 99  # TypeError: 'tuple' object does not support item assignment
except TypeError:
    pass

# ATTENZIONE: una tupla di oggetti mutabili non e veramente immutabile
tupla_con_lista = ([1, 2], [3, 4])
tupla_con_lista[0].append(99)  # Funziona! La lista interna e mutabile
# Per vera immutabilita, usare solo tipi immutabili all'interno
tupla_sicura = ((1, 2), (3, 4))  # Tuple di tuple: completamente immutabile
```

### Frozen Dataclass

Le `frozen=True` dataclass sono il modo piu idiomatico in Python moderno per creare oggetti
immutabili con campi nominati, validazione e metodi:

```python
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Denaro:
    """Valore monetario immutabile con valuta."""
    importo: Decimal
    valuta: str = "EUR"

    def __post_init__(self):
        if self.importo < 0:
            raise ValueError(f"Importo negativo non consentito: {self.importo}")
        if len(self.valuta) != 3:
            raise ValueError(f"Codice valuta non valido: {self.valuta}")

    def aggiungi(self, altro: "Denaro") -> "Denaro":
        """Restituisce un NUOVO oggetto Denaro, non modifica questo."""
        if self.valuta != altro.valuta:
            raise ValueError(
                f"Impossibile sommare {self.valuta} e {altro.valuta}"
            )
        return Denaro(importo=self.importo + altro.importo, valuta=self.valuta)

    def applica_sconto(self, percentuale: float) -> "Denaro":
        """Restituisce un NUOVO oggetto con lo sconto applicato."""
        fattore = Decimal(str(1 - percentuale))
        return Denaro(importo=self.importo * fattore, valuta=self.valuta)


# Utilizzo — ogni operazione produce un nuovo oggetto
prezzo = Denaro(importo=Decimal("100.00"))
prezzo_scontato = prezzo.applica_sconto(0.15)
# prezzo e ancora Decimal("100.00") — non e stato modificato

# Hashable — utilizzabile come chiave di dizionario
prezzi_per_prodotto: dict[Denaro, str] = {prezzo: "Tastiera"}


@dataclass(frozen=True, slots=True)
class IndirizzoSpedizione:
    """Value object immutabile per indirizzi."""
    via: str
    civico: str
    cap: str
    citta: str
    provincia: str
    paese: str = "IT"


@dataclass(frozen=True, slots=True)
class RigaOrdine:
    """Singola riga di un ordine — immutabile."""
    prodotto_id: str
    nome_prodotto: str
    prezzo_unitario: Denaro
    quantita: int

    @property
    def totale_riga(self) -> Denaro:
        importo = self.prezzo_unitario.importo * self.quantita
        return Denaro(importo=importo, valuta=self.prezzo_unitario.valuta)
```

Il parametro `slots=True` (Python 3.10+) aggiunge `__slots__` alla classe, riducendo il consumo
di memoria del 25-40% rispetto alle dataclass standard e velocizzando l'accesso agli attributi.

### NamedTuple

Le `NamedTuple` sono un'alternativa leggera alle frozen dataclass, particolarmente adatte per
record di dati semplici dove non servono metodi complessi:

```python
from typing import NamedTuple


class Coordinata(NamedTuple):
    latitudine: float
    longitudine: float
    altitudine: float = 0.0


class RisultatoQuery(NamedTuple):
    """Risultato immutabile di una query al database."""
    righe: tuple[dict, ...]
    totale: int
    tempo_ms: float


# NamedTuple supporta lo unpacking
coord = Coordinata(45.4642, 9.1900)
lat, lon, alt = coord  # Unpacking come una tupla normale

# Confronto e hashing automatici
coord_a = Coordinata(45.4642, 9.1900)
coord_b = Coordinata(45.4642, 9.1900)
assert coord_a == coord_b
assert hash(coord_a) == hash(coord_b)
```

**Quando scegliere NamedTuple vs frozen dataclass:**

| Criterio | NamedTuple | frozen dataclass |
|---|---|---|
| Memoria | Leggermente piu leggera | Leggera con `slots=True` |
| Velocita istanziazione | ~15% piu veloce | Piu lenta |
| Metodi personalizzati | Supportati ma meno naturali | Pienamente supportati |
| Validazione `__post_init__` | Non disponibile | Disponibile |
| Compatibilita con tuple | Si, e una tupla | No |
| Ereditarieta | Limitata | Piena |

**Regola pratica**: usare `NamedTuple` per semplici record dati (coordinate, risultati, punti).
Usare `frozen dataclass` per value object con logica di business (denaro, indirizzi, intervalli
temporali).

### Pattern di Aggiornamento Immutabile

Quando si lavora con oggetti immutabili, l'aggiornamento richiede la creazione di nuove copie.
Python 3.13+ offre `dataclasses.replace()` e i `NamedTuple` hanno `_replace()`:

```python
from dataclasses import replace


@dataclass(frozen=True, slots=True)
class ConfigurazioneApp:
    host: str = "localhost"
    porta: int = 8000
    debug: bool = False
    max_connessioni: int = 100
    timeout_secondi: int = 30

# Creare una variante modificando solo alcuni campi
config_dev = ConfigurazioneApp(debug=True)
config_prod = replace(config_dev, debug=False, host="0.0.0.0", porta=443)
# config_dev NON e stata modificata

# Con NamedTuple
coord_originale = Coordinata(45.4642, 9.1900, 0.0)
coord_alta = coord_originale._replace(altitudine=1500.0)


# Pattern builder per aggiornamenti complessi
@dataclass(frozen=True, slots=True)
class StatoApplicazione:
    utente_corrente: str | None = None
    pagina: str = "home"
    filtri: tuple[str, ...] = ()
    ordinamento: str = "data_desc"

    def con_utente(self, utente: str) -> "StatoApplicazione":
        return replace(self, utente_corrente=utente)

    def con_pagina(self, pagina: str) -> "StatoApplicazione":
        return replace(self, pagina=pagina)

    def con_filtro_aggiunto(self, filtro: str) -> "StatoApplicazione":
        return replace(self, filtri=(*self.filtri, filtro))


# Fluent API immutabile
stato = (
    StatoApplicazione()
    .con_utente("mario.rossi")
    .con_pagina("ordini")
    .con_filtro_aggiunto("stato:attivo")
    .con_filtro_aggiunto("anno:2025")
)
```

### Collezioni Immutabili

Per garantire l'immutabilita delle collezioni, usare i tipi immutabili di Python:

```python
from types import MappingProxyType

# Dizionario di sola lettura con MappingProxyType
_CONFIGURAZIONE_INTERNA = {"livello_log": "INFO", "max_retry": 3}
CONFIGURAZIONE: MappingProxyType = MappingProxyType(_CONFIGURAZIONE_INTERNA)

# CONFIGURAZIONE["livello_log"] = "DEBUG"  # TypeError!

# frozenset per insiemi immutabili
RUOLI_VALIDI: frozenset[str] = frozenset({"admin", "editor", "viewer"})
STATI_ORDINE: frozenset[str] = frozenset({
    "bozza", "confermato", "spedito", "consegnato", "annullato",
})

# tuple per sequenze immutabili
GIORNI_FERIALI: tuple[str, ...] = (
    "lunedi", "martedi", "mercoledi", "giovedi", "venerdi",
)

# Nelle dataclass, usare tuple e frozenset invece di list e set
@dataclass(frozen=True, slots=True)
class Permessi:
    ruoli: frozenset[str]
    azioni_consentite: tuple[str, ...]
    azioni_negate: tuple[str, ...] = ()
```

### Pattern Builder Immutabile

Quando un oggetto immutabile ha molti campi opzionali, il pattern builder evita costruttori
con decine di parametri mantenendo l'immutabilita del risultato finale:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self


@dataclass(frozen=True, slots=True)
class ConfigurazioneServer:
    host: str
    porta: int
    workers: int
    timeout_secondi: int
    ssl_abilitato: bool
    certificato_path: str | None
    log_level: str
    max_connessioni: int


class BuilderConfigurazioneServer:
    """Builder mutabile che produce un oggetto immutabile."""

    def __init__(self, host: str, porta: int) -> None:
        self._host = host
        self._porta = porta
        self._workers = 4
        self._timeout = 30
        self._ssl = False
        self._cert_path: str | None = None
        self._log_level = "INFO"
        self._max_conn = 1000

    def con_workers(self, n: int) -> Self:
        self._workers = n
        return self

    def con_timeout(self, secondi: int) -> Self:
        self._timeout = secondi
        return self

    def con_ssl(self, certificato_path: str) -> Self:
        self._ssl = True
        self._cert_path = certificato_path
        return self

    def con_log_level(self, livello: str) -> Self:
        self._log_level = livello
        return self

    def con_max_connessioni(self, n: int) -> Self:
        self._max_conn = n
        return self

    def costruisci(self) -> ConfigurazioneServer:
        """Produce l'oggetto immutabile finale."""
        if self._ssl and self._cert_path is None:
            raise ValueError("SSL abilitato ma nessun certificato specificato")
        return ConfigurazioneServer(
            host=self._host,
            porta=self._porta,
            workers=self._workers,
            timeout_secondi=self._timeout,
            ssl_abilitato=self._ssl,
            certificato_path=self._cert_path,
            log_level=self._log_level,
            max_connessioni=self._max_conn,
        )


# Uso fluente
config = (
    BuilderConfigurazioneServer("0.0.0.0", 8443)
    .con_workers(8)
    .con_ssl("/etc/ssl/cert.pem")
    .con_log_level("WARNING")
    .con_max_connessioni(5000)
    .costruisci()
)
# config e completamente immutabile — nessun attributo puo essere modificato
```

Il builder stesso e mutabile (necessario per la costruzione fluente), ma il prodotto
finale — `ConfigurazioneServer` — e un frozen dataclass che non puo essere modificata
dopo la creazione. Questo pattern separa la complessita della costruzione dalla semplicita
dell'uso: chi riceve un `ConfigurazioneServer` ha la garanzia che i suoi valori non
cambieranno mai.

---

## Gestione della Configurazione

La gestione della configurazione e un aspetto critico del clean code che spesso viene trascurato.
Una configurazione mal gestita porta a hardcoded values, segreti nel codice sorgente e difficolta
nel deployment su ambienti diversi.

### La Metodologia 12-Factor App

La [12-Factor App](https://12factor.net/it/) e un insieme di best practice per costruire
applicazioni moderne e scalabili. Il fattore III riguarda specificamente la configurazione:

> *Immagazzina la configurazione nell'ambiente.*

**Principi chiave:**

1. **Separazione rigida** tra configurazione e codice. La configurazione varia tra deploy
   (staging, produzione, dev locale); il codice no.
2. **Variabili d'ambiente** come meccanismo universale. Niente file di configurazione specifici
   per ambiente committati nel repository.
3. **Nessun segreto nel codice**. Mai. API key, password, token, certificati devono provenire
   dall'ambiente o da un secret manager.
4. **Validazione al boot**. Se una variabile d'ambiente richiesta manca, l'applicazione deve
   fallire immediatamente con un messaggio chiaro, non ore dopo con un errore criptico.

### pydantic-settings

Il pacchetto `pydantic-settings` e lo standard de facto per la gestione tipizzata della
configurazione in Python moderno. Combina la validazione di Pydantic con il caricamento
automatico da variabili d'ambiente e file `.env`:

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImpostazioniDatabase(BaseSettings):
    """Configurazione del database con validazione automatica."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    host: str = "localhost"
    porta: int = Field(default=5432, ge=1, le=65535)
    nome: str
    utente: str
    password: SecretStr  # Non viene mai stampata nei log
    pool_size: int = Field(default=10, ge=1, le=100)
    ssl_mode: str = "require"

    @property
    def url_connessione(self) -> str:
        pwd = self.password.get_secret_value()
        return (
            f"postgresql://{self.utente}:{pwd}"
            f"@{self.host}:{self.porta}/{self.nome}"
            f"?sslmode={self.ssl_mode}"
        )


class ImpostazioniApp(BaseSettings):
    """Configurazione principale dell'applicazione."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora variabili d'ambiente non previste
    )

    nome_app: str = "mia-app"
    ambiente: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = False
    livello_log: str = "INFO"
    secret_key: SecretStr
    allowed_hosts: list[str] = ["localhost"]

    # Sotto-configurazioni composte
    database: ImpostazioniDatabase = ImpostazioniDatabase()


# Utilizzo — fail-fast al boot se manca una variabile obbligatoria
try:
    config = ImpostazioniApp()
except Exception as e:
    # Errore chiaro: "Field required [type=missing, input_value=...]"
    raise SystemExit(f"Configurazione non valida: {e}") from e
```

**File `.env` di esempio** (mai committato nel repository):

```ini
# .env — aggiunto a .gitignore
NOME_APP=ordini-api
AMBIENTE=production
DEBUG=false
SECRET_KEY=supersegreta-mai-nel-codice
ALLOWED_HOSTS=["api.esempio.com","api2.esempio.com"]
DB_HOST=db.produzione.interno
DB_PORTA=5432
DB_NOME=ordini_prod
DB_UTENTE=app_user
DB_PASSWORD=password-sicura-dal-vault
```

**Vantaggi di pydantic-settings:**

- **Validazione al boot**: errori di configurazione emergono subito, non a runtime.
- **Type-safety**: ogni valore e tipizzato e validato (porta e un int tra 1 e 65535, ambiente e
  uno dei tre valori ammessi).
- **SecretStr**: i segreti non appaiono nei log, `repr()` o traceback.
- **Composizione**: sotto-configurazioni modulari e riutilizzabili.
- **Compatibilita CI/CD**: funziona con Docker, Kubernetes, Heroku e qualsiasi sistema che
  inietti variabili d'ambiente.

### Anti-Pattern da Evitare

```python
# CATTIVO — segreti hardcoded nel codice sorgente
DATABASE_URL = "postgresql://admin:password123@localhost/mydb"
API_KEY = "sk-1234567890abcdef"

# CATTIVO — os.getenv senza validazione ne default sicuro
porta = int(os.getenv("PORTA"))  # Crash se PORTA non e definita

# CATTIVO — configurazione sparsa in piu file senza schema
import yaml
with open("config.yml") as f:
    config = yaml.safe_load(f)  # Nessuna validazione, nessun tipo

# BUONO — pydantic-settings con validazione completa
config = ImpostazioniApp()  # Fail-fast, tipizzato, validato
```

---

## Naming Conventions — Approfondimento

### Contesto e Dominio nei Nomi

Oltre alle regole base di naming (snake_case, PascalCase, UPPER_SNAKE_CASE), il clean code
avanzato richiede che i nomi riflettano il dominio del problema, non i dettagli implementativi:

```python
# CATTIVO — nomi orientati all'implementazione
lista_stringhe = ["mario@email.com", "luigi@email.com"]
dict_dati = {"nome": "Mario", "eta": 30}
flag_bool = True

# BUONO — nomi orientati al dominio
indirizzi_email_destinatari = ["mario@email.com", "luigi@email.com"]
profilo_utente = {"nome": "Mario", "eta": 30}
is_abbonamento_attivo = True
```

### Lunghezza del Nome Proporzionale allo Scope

La lunghezza di un nome dovrebbe essere proporzionale al suo scope. Variabili con scope ristretto
possono avere nomi brevi; variabili con scope ampio richiedono nomi piu descrittivi:

```python
# Scope locale stretto — nome breve accettabile
quadrati = [x ** 2 for x in range(10)]

for i, elemento in enumerate(lista_corta):
    print(f"{i}: {elemento}")

# Scope ampio (modulo/classe) — nome lungo e descrittivo
TIMEOUT_CONNESSIONE_DATABASE_SECONDI = 30
numero_massimo_tentativi_autenticazione = 5

# Scope di funzione — bilanciare tra chiarezza e concisione
def calcola_media_ponderata(
    valori: list[float],
    pesi: list[float],
) -> float:
    somma_ponderata = sum(v * p for v, p in zip(valori, pesi))
    somma_pesi = sum(pesi)
    return somma_ponderata / somma_pesi
```

### Nomi che Rivelano l'Intento

Un nome dovrebbe rispondere alla domanda "perche esiste questa variabile/funzione?" senza
bisogno di commenti:

```python
# CATTIVO — richiede un commento per capire cosa fa
d = 86400  # secondi in un giorno

# BUONO — il nome stesso e il commento
SECONDI_IN_UN_GIORNO = 86_400

# CATTIVO — cosa restituisce?
def get_them(the_list):
    return [x for x in the_list if x[0] == 4]

# BUONO — cristallino
def filtra_celle_contrassegnate(celle: list[Cella]) -> list[Cella]:
    return [cella for cella in celle if cella.is_contrassegnata]
```

### Verbi per le Funzioni, Sostantivi per le Classi

Le funzioni rappresentano azioni e dovrebbero usare verbi. Le classi rappresentano entita e
dovrebbero usare sostantivi. Questa regola semplice migliora enormemente la leggibilita:

```python
# Funzioni — verbi che descrivono l'azione
def calcola_totale(ordine: Ordine) -> Decimal: ...
def valida_email(indirizzo: str) -> bool: ...
def invia_notifica(destinatario: str, messaggio: str) -> None: ...
def genera_report_mensile(mese: int, anno: int) -> Report: ...

# Classi — sostantivi che descrivono entita
class CalcolatoreImposte: ...
class ValidatoreCredenziali: ...
class GeneratoreReport: ...
class RegistroEventi: ...

# CATTIVO — la classe ha un nome da funzione
class CalcolaPrezzo: ...   # Dovrebbe essere CalcolatorePrezzo

# CATTIVO — la funzione ha un nome da classe
def Validatore(dati): ...  # Dovrebbe essere valida(dati)
```

---

## Design delle Funzioni — Approfondimento

### Command-Query Separation (CQS)

Il principio **Command-Query Separation** (CQS), formulato da Bertrand Meyer, stabilisce che
ogni funzione dovrebbe essere o un **command** (modifica lo stato, non restituisce nulla) o una
**query** (restituisce un valore, non modifica lo stato). Mai entrambi.

```python
# VIOLAZIONE CQS — la funzione modifica stato E restituisce un valore
class Carrello:
    def __init__(self):
        self._articoli: list[Articolo] = []
        self._totale: Decimal = Decimal("0")

    def aggiungi_e_calcola(self, articolo: Articolo) -> Decimal:
        """Aggiunge l'articolo E restituisce il nuovo totale."""
        self._articoli.append(articolo)  # Command: modifica stato
        self._totale += articolo.prezzo
        return self._totale               # Query: restituisce valore
        # Chi chiama non sa se il valore restituito e un effetto
        # collaterale o il risultato principale


# RISPETTA CQS — command e query separati
class Carrello:
    def __init__(self):
        self._articoli: list[Articolo] = []

    # COMMAND — modifica stato, non restituisce nulla
    def aggiungi(self, articolo: Articolo) -> None:
        self._articoli.append(articolo)

    def rimuovi(self, articolo: Articolo) -> None:
        self._articoli.remove(articolo)

    def svuota(self) -> None:
        self._articoli.clear()

    # QUERY — restituisce informazioni, non modifica stato
    @property
    def totale(self) -> Decimal:
        return sum(a.prezzo for a in self._articoli)

    @property
    def numero_articoli(self) -> int:
        return len(self._articoli)

    def contiene(self, prodotto_id: str) -> bool:
        return any(a.prodotto_id == prodotto_id for a in self._articoli)
```

**Benefici del CQS:**

- **Prevedibilita**: sapere che una query non modifica mai lo stato permette di chiamarla
  liberamente senza conseguenze.
- **Testabilita**: i command possono essere testati verificando lo stato dopo l'esecuzione;
  le query possono essere testate verificando il valore restituito.
- **Concorrenza**: le query pure possono essere eseguite in parallelo in sicurezza.
- **Debugging**: quando qualcosa cambia inaspettatamente, basta cercare nei command.

**Eccezione pragmatica**: operazioni come `stack.pop()` (rimuove e restituisce l'ultimo elemento)
violano tecnicamente il CQS ma sono idiomatiche e universalmente comprese. Il principio e una
guida, non un dogma.

### Funzioni di Ordine Superiore

Le funzioni di ordine superiore (che accettano o restituiscono funzioni) sono un pattern potente
per il riuso e la composizione, ma devono essere usate con giudizio per non sacrificare la
leggibilita:

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def con_retry(
    max_tentativi: int = 3,
    eccezioni: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decoratore che riprova una funzione in caso di fallimento."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            ultimo_errore: Exception | None = None
            for tentativo in range(max_tentativi):
                try:
                    return func(*args, **kwargs)
                except eccezioni as e:
                    ultimo_errore = e
                    log.warning(
                        "Tentativo %d/%d fallito: %s",
                        tentativo + 1,
                        max_tentativi,
                        e,
                    )
            raise ultimo_errore  # type: ignore[misc]
        return wrapper
    return decorator


@con_retry(max_tentativi=3, eccezioni=(ConnectionError, TimeoutError))
def chiama_api_esterna(endpoint: str) -> dict:
    ...
```

### Funzioni come Contratti

Una funzione ben progettata definisce un **contratto** chiaro: precondizioni (cosa deve essere
vero prima della chiamata), postcondizioni (cosa sara vero dopo la chiamata) e invarianti (cosa
resta sempre vero):

```python
from decimal import Decimal


def trasferisci_fondi(
    conto_origine: ContoBancario,
    conto_destinazione: ContoBancario,
    importo: Decimal,
) -> None:
    """Trasferisce fondi tra due conti.

    Precondizioni:
        - importo > 0
        - conto_origine.saldo >= importo
        - conto_origine != conto_destinazione

    Postcondizioni:
        - conto_origine.saldo diminuito di importo
        - conto_destinazione.saldo aumentato di importo
        - La somma totale dei saldi non cambia

    Raises:
        ValueError: Se l'importo e <= 0 o i conti sono uguali.
        FondiInsufficentiError: Se il saldo del conto origine e insufficiente.
    """
    # Verifica precondizioni esplicite
    if importo <= 0:
        raise ValueError(f"Importo deve essere positivo, ricevuto: {importo}")
    if conto_origine.id == conto_destinazione.id:
        raise ValueError("Impossibile trasferire allo stesso conto")
    if conto_origine.saldo < importo:
        raise FondiInsufficentiError(
            f"Saldo {conto_origine.saldo} insufficiente per trasferire {importo}"
        )

    conto_origine.addebita(importo)
    conto_destinazione.accredita(importo)
```

---

## Catalogo Esteso dei Code Smells

Oltre ai code smells gia trattati (long methods, god classes, feature envy, magic numbers, deep
nesting, codice duplicato, dead code), esistono diversi altri smell che meritano attenzione.

### Data Clumps (Gruppi di Dati)

Un **data clump** si verifica quando lo stesso gruppo di variabili appare ripetutamente insieme
in piu punti del codice. Questo indica che quei dati appartengono a un unico concetto che
merita una propria classe o dataclass:

```python
# CODE SMELL: Data Clump — gli stessi 3 parametri appaiono ovunque
def crea_fattura(
    nome_cliente: str,
    indirizzo_cliente: str,
    codice_fiscale_cliente: str,
    articoli: list[Articolo],
) -> Fattura:
    ...

def invia_fattura(
    nome_cliente: str,
    indirizzo_cliente: str,
    codice_fiscale_cliente: str,
    fattura: Fattura,
) -> None:
    ...

def genera_ricevuta(
    nome_cliente: str,
    indirizzo_cliente: str,
    codice_fiscale_cliente: str,
    importo: Decimal,
) -> Ricevuta:
    ...


# REFACTORING: Estrarre una dataclass per il gruppo di dati
@dataclass(frozen=True, slots=True)
class DatiCliente:
    nome: str
    indirizzo: str
    codice_fiscale: str

def crea_fattura(cliente: DatiCliente, articoli: list[Articolo]) -> Fattura:
    ...

def invia_fattura(cliente: DatiCliente, fattura: Fattura) -> None:
    ...

def genera_ricevuta(cliente: DatiCliente, importo: Decimal) -> Ricevuta:
    ...
```

### Shotgun Surgery (Chirurgia a Pallettoni)

Lo **shotgun surgery** si verifica quando una modifica logicamente unitaria richiede piccole
modifiche in molte classi o moduli diversi. E il sintomo di una responsabilita frammentata:

```python
# CODE SMELL: Shotgun Surgery
# Aggiungere un nuovo campo "telefono" all'utente richiede modifiche in:
# 1. models.py — aggiungere il campo al modello
# 2. serializers.py — aggiungere il campo al serializer
# 3. forms.py — aggiungere il campo al form
# 4. views.py — gestire il nuovo campo nella view
# 5. templates/ — aggiungere il campo al template
# 6. api.py — aggiungere il campo all'endpoint API
# 7. tests/ — aggiornare tutti i test
# 8. migrations/ — creare la migrazione
# 9. admin.py — aggiungere il campo all'admin

# REFACTORING: Centralizzare la definizione del campo in un unico punto
# e derivare tutto il resto automaticamente

@dataclass
class CampoUtente:
    nome: str
    tipo: type
    obbligatorio: bool = True
    validatore: Callable | None = None

SCHEMA_UTENTE: tuple[CampoUtente, ...] = (
    CampoUtente("nome", str),
    CampoUtente("cognome", str),
    CampoUtente("email", str, validatore=valida_email),
    CampoUtente("telefono", str, obbligatorio=False, validatore=valida_telefono),
)

# Serializer, form e validazione sono generati dallo schema
# Una modifica allo schema si propaga automaticamente
```

**Segnali di shotgun surgery:**

- Aggiungere un campo richiede modifiche in 5+ file.
- Un cambio di business rule tocca 3+ classi non correlate.
- Il grep del nome di un campo mostra risultati in moduli che non dovrebbero conoscerlo.

**Rimedi:**

- Centralizzare la definizione in un unico punto (single source of truth).
- Usare il pattern Observer o eventi per disaccoppiare i moduli.
- Applicare il principio "Tell, Don't Ask" per spostare la logica dove risiedono i dati.

### Primitive Obsession (Ossessione per i Primitivi)

La **primitive obsession** e l'uso eccessivo di tipi primitivi (str, int, float) per rappresentare
concetti di dominio che meriterebbero un tipo dedicato:

```python
# CODE SMELL: Primitive Obsession
def crea_utente(
    email: str,           # E davvero qualsiasi stringa?
    telefono: str,        # Formato? Prefisso internazionale?
    codice_fiscale: str,  # 16 caratteri alfanumerici con checksum
    importo_credito: float,  # Valuta? Precisione?
) -> dict:
    # Validazione sparsa e ripetuta ovunque
    if "@" not in email:
        raise ValueError("Email non valida")
    if len(codice_fiscale) != 16:
        raise ValueError("Codice fiscale non valido")
    ...


# REFACTORING: Tipi di dominio dedicati (Value Objects)
@dataclass(frozen=True, slots=True)
class Email:
    """Value object per indirizzi email validati."""
    valore: str

    def __post_init__(self):
        if "@" not in self.valore or "." not in self.valore.split("@")[1]:
            raise ValueError(f"Email non valida: {self.valore}")
        # Normalizzazione: lowercase
        object.__setattr__(self, "valore", self.valore.lower().strip())

    def __str__(self) -> str:
        return self.valore


@dataclass(frozen=True, slots=True)
class CodiceFiscale:
    """Value object per codici fiscali italiani."""
    valore: str

    def __post_init__(self):
        valore_normalizzato = self.valore.upper().strip()
        if len(valore_normalizzato) != 16:
            raise ValueError(
                f"Codice fiscale deve avere 16 caratteri: {valore_normalizzato}"
            )
        object.__setattr__(self, "valore", valore_normalizzato)


@dataclass(frozen=True, slots=True)
class Telefono:
    """Value object per numeri di telefono con prefisso internazionale."""
    prefisso: str  # es. "+39"
    numero: str    # es. "3331234567"

    def __post_init__(self):
        if not self.prefisso.startswith("+"):
            raise ValueError(f"Prefisso deve iniziare con '+': {self.prefisso}")
        if not self.numero.isdigit():
            raise ValueError(f"Numero deve contenere solo cifre: {self.numero}")

    @property
    def formato_internazionale(self) -> str:
        return f"{self.prefisso}{self.numero}"


# Ora i tipi sono auto-validanti e la funzione e piu chiara
def crea_utente(
    email: Email,
    telefono: Telefono,
    codice_fiscale: CodiceFiscale,
    credito: Denaro,
) -> Utente:
    # Nessuna validazione necessaria qui — i tipi sono gia validati
    ...
```

**Benefici dei value object:**

- La validazione avviene una sola volta, alla creazione.
- E impossibile passare un codice fiscale dove serve un'email — il type checker lo impedisce.
- La logica di formattazione e normalizzazione e incapsulata nel tipo stesso.
- I test dei value object sono semplici e isolati.

### Inappropriate Intimacy (Intimita Inappropriata)

Quando due classi conoscono troppi dettagli interni l'una dell'altra, violando l'incapsulamento:

```python
# CODE SMELL: Inappropriate Intimacy
class Motore:
    def __init__(self):
        self._temperatura = 20.0
        self._rpm = 0
        self._olio_livello = 1.0

class Automobile:
    def __init__(self, motore: Motore):
        self._motore = motore

    def diagnostica(self) -> str:
        # Accede direttamente agli attributi interni del motore
        if self._motore._temperatura > 100:  # Accesso a _privato!
            return "Motore surriscaldato"
        if self._motore._olio_livello < 0.3:
            return "Olio basso"
        return "OK"


# REFACTORING: Il motore espone metodi di query, non i suoi attributi interni
class Motore:
    def __init__(self):
        self._temperatura = 20.0
        self._rpm = 0
        self._olio_livello = 1.0

    def is_surriscaldato(self) -> bool:
        return self._temperatura > 100

    def is_olio_basso(self) -> bool:
        return self._olio_livello < 0.3

    def diagnostica(self) -> str:
        if self.is_surriscaldato():
            return "Motore surriscaldato"
        if self.is_olio_basso():
            return "Olio basso"
        return "OK"

class Automobile:
    def __init__(self, motore: Motore):
        self._motore = motore

    def diagnostica(self) -> str:
        return self._motore.diagnostica()  # Delega, non ispeziona
```

---

## Tecniche di Refactoring — Approfondimento

Oltre alle tecniche gia presentate (extract method, extract class, replace conditional with
polymorphism, introduce parameter object), il catalogo di Martin Fowler include decine di
trasformazioni. Le piu utili in Python sono descritte di seguito.

### Replace Conditional with Polymorphism — Caso Avanzato

Un caso piu complesso e frequente rispetto al semplice calcolo di aree: la gestione di diversi
tipi di notifica, dove ogni tipo ha logica di composizione e invio completamente diversa:

```python
# PRIMA — catena di condizionali che cresce a ogni nuovo tipo
def invia_notifica(utente: Utente, evento: Evento) -> None:
    if utente.preferenza_notifica == "email":
        corpo = formatta_html(evento)
        smtp.invia(utente.email, "Notifica", corpo)
    elif utente.preferenza_notifica == "sms":
        testo = formatta_testo_breve(evento)
        gateway_sms.invia(utente.telefono, testo)
    elif utente.preferenza_notifica == "push":
        payload = crea_payload_push(evento)
        servizio_push.invia(utente.device_token, payload)
    elif utente.preferenza_notifica == "webhook":
        dati = serializza_evento(evento)
        httpx.post(utente.webhook_url, json=dati)
    # ...ogni nuovo tipo richiede di modificare questa funzione


# DOPO — polimorfismo con Protocol
from typing import Protocol


class Notificatore(Protocol):
    def invia(self, utente: Utente, evento: Evento) -> None: ...


class NotificatoreEmail:
    def __init__(self, client_smtp: ClientSMTP):
        self._smtp = client_smtp

    def invia(self, utente: Utente, evento: Evento) -> None:
        corpo = formatta_html(evento)
        self._smtp.invia(utente.email, "Notifica", corpo)


class NotificatoreSMS:
    def __init__(self, gateway: GatewaySMS):
        self._gateway = gateway

    def invia(self, utente: Utente, evento: Evento) -> None:
        testo = formatta_testo_breve(evento)
        self._gateway.invia(utente.telefono, testo)


class NotificatorePush:
    def __init__(self, servizio: ServizioPush):
        self._servizio = servizio

    def invia(self, utente: Utente, evento: Evento) -> None:
        payload = crea_payload_push(evento)
        self._servizio.invia(utente.device_token, payload)


# Registry — aggiungere un nuovo tipo non modifica il codice esistente
NOTIFICATORI: dict[str, Notificatore] = {
    "email": NotificatoreEmail(client_smtp),
    "sms": NotificatoreSMS(gateway_sms),
    "push": NotificatorePush(servizio_push),
}

def invia_notifica(utente: Utente, evento: Evento) -> None:
    notificatore = NOTIFICATORI.get(utente.preferenza_notifica)
    if notificatore is None:
        raise ValueError(f"Tipo notifica sconosciuto: {utente.preferenza_notifica}")
    notificatore.invia(utente, evento)
```

### Introduce Null Object

Sostituire i controlli ripetuti di `None` con un oggetto speciale che implementa il
comportamento di default (pattern Null Object):

```python
# PRIMA — controlli None sparsi ovunque
class ServizioOrdini:
    def processa(self, ordine: Ordine) -> None:
        # ...logica di business...

        if self._logger is not None:
            self._logger.info(f"Ordine {ordine.id} processato")

        if self._metriche is not None:
            self._metriche.incrementa("ordini_processati")

        if self._cache is not None:
            self._cache.invalida(f"ordine:{ordine.id}")


# DOPO — Null Object elimina i controlli
class LoggerNullo:
    """Non fa nulla — sostituisce i controlli None."""
    def info(self, msg: str) -> None:
        pass
    def warning(self, msg: str) -> None:
        pass
    def error(self, msg: str) -> None:
        pass

class MetricheNulle:
    def incrementa(self, nome: str) -> None:
        pass

class CacheNulla:
    def invalida(self, chiave: str) -> None:
        pass


class ServizioOrdini:
    def __init__(
        self,
        logger: Logger = LoggerNullo(),
        metriche: Metriche = MetricheNulle(),
        cache: Cache = CacheNulla(),
    ):
        self._logger = logger
        self._metriche = metriche
        self._cache = cache

    def processa(self, ordine: Ordine) -> None:
        # Nessun controllo None — il Null Object gestisce il caso
        self._logger.info(f"Ordine {ordine.id} processato")
        self._metriche.incrementa("ordini_processati")
        self._cache.invalida(f"ordine:{ordine.id}")
```

### Decompose Conditional

Scomporre una condizione complessa in funzioni con nomi che ne rivelano l'intento:

```python
# PRIMA — condizione complessa e opaca
def calcola_prezzo(ordine: Ordine) -> Decimal:
    if (
        ordine.data >= date(2025, 6, 1)
        and ordine.data <= date(2025, 8, 31)
        and ordine.totale > Decimal("200")
        and ordine.cliente.is_premium
    ):
        return ordine.totale * Decimal("0.80")
    elif (
        ordine.cliente.anni_fedelta >= 5
        and ordine.totale > Decimal("500")
    ):
        return ordine.totale * Decimal("0.85")
    else:
        return ordine.totale


# DOPO — condizioni decomposte in funzioni leggibili
def _is_promozione_estiva(ordine: Ordine) -> bool:
    return (
        date(2025, 6, 1) <= ordine.data <= date(2025, 8, 31)
        and ordine.totale > Decimal("200")
        and ordine.cliente.is_premium
    )

def _is_sconto_fedelta(ordine: Ordine) -> bool:
    return (
        ordine.cliente.anni_fedelta >= 5
        and ordine.totale > Decimal("500")
    )

SCONTO_PROMOZIONE_ESTIVA = Decimal("0.80")
SCONTO_FEDELTA = Decimal("0.85")

def calcola_prezzo(ordine: Ordine) -> Decimal:
    if _is_promozione_estiva(ordine):
        return ordine.totale * SCONTO_PROMOZIONE_ESTIVA
    if _is_sconto_fedelta(ordine):
        return ordine.totale * SCONTO_FEDELTA
    return ordine.totale
```

---

## Documentazione — Type Stubs e Analisi Statica

### Type Stubs (.pyi)

I **type stubs** sono file con estensione `.pyi` che contengono solo le annotazioni di tipo
per un modulo Python, senza implementazione. Servono per aggiungere informazioni di tipo a
librerie che non le includono nativamente:

```python
# mia_libreria_legacy.pyi — stub per una libreria senza type hints

def connetti(host: str, porta: int, timeout: float = 30.0) -> Connessione: ...
def esegui_query(connessione: Connessione, sql: str, params: tuple = ()) -> Risultato: ...

class Connessione:
    host: str
    porta: int
    is_connesso: bool
    def chiudi(self) -> None: ...
    def ping(self) -> bool: ...

class Risultato:
    righe: list[dict[str, Any]]
    colonne: tuple[str, ...]
    tempo_esecuzione_ms: float
    def prima_riga(self) -> dict[str, Any] | None: ...
    def __iter__(self) -> Iterator[dict[str, Any]]: ...
    def __len__(self) -> int: ...
```

**Installare type stubs per librerie note:**

```bash
# Molte librerie hanno pacchetti di stub su PyPI
pip install types-requests     # Per requests
pip install types-PyYAML       # Per PyYAML
pip install types-redis        # Per redis
pip install types-Pillow       # Per Pillow
pip install types-python-dateutil  # Per python-dateutil

# mypy suggerisce automaticamente i pacchetti di stub mancanti
mypy mio_progetto/
# note: install types-requests: pip install types-requests
```

### mypy in Modalita Strict

La modalita **strict** di mypy abilita tutti i controlli opzionali, rendendo il type checking
il piu rigoroso possibile. E raccomandata per progetti nuovi e come obiettivo per quelli
esistenti:

```toml
# pyproject.toml — configurazione mypy strict
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true
show_error_codes = true
pretty = true

# Configurazione per moduli specifici che non hanno ancora type hints completi
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "alembic.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "mio_progetto.legacy.*"
disallow_untyped_defs = false
disallow_untyped_calls = false
```

**Cosa abilita `strict = true`:**

| Flag | Significato |
|---|---|
| `disallow_untyped_defs` | Tutte le funzioni devono avere annotazioni di tipo |
| `disallow_any_generics` | Vieta `list` senza parametri (deve essere `list[int]`) |
| `warn_return_any` | Avvisa quando una funzione restituisce `Any` |
| `no_implicit_optional` | `None` deve essere esplicito: `str \| None`, non `str = None` |
| `check_untyped_defs` | Controlla anche il corpo delle funzioni senza annotazioni |
| `disallow_untyped_calls` | Vieta chiamate a funzioni non annotate |

**Strategia di adozione graduale per codebase esistenti:**

1. Iniziare con `strict = true` a livello globale.
2. Aggiungere override per i moduli legacy che non sono ancora pronti.
3. Ridurre progressivamente gli override, modulo per modulo.
4. Usare `warn_unused_ignores = true` per rimuovere i `# type: ignore` non piu necessari.

---

## Checklist di Code Review

Una checklist strutturata garantisce che le code review siano sistematiche e non dipendano
dalla memoria o dall'umore del reviewer. Ogni pull request dovrebbe essere verificata contro
i seguenti criteri.

### Leggibilita e Naming

- [ ] I nomi di variabili, funzioni e classi sono descrittivi e seguono le convenzioni Python
- [ ] Le funzioni sono piccole (< 50 righe) con una sola responsabilita
- [ ] I file sono focalizzati (< 800 righe)
- [ ] Non ci sono abbreviazioni criptiche o nomi di una sola lettera (tranne loop brevi)
- [ ] I booleani usano prefissi `is_`, `has_`, `can_`, `should_`
- [ ] Le costanti usano `UPPER_SNAKE_CASE` e sono definite a livello di modulo

### Struttura e Design

- [ ] Nessun nesting superiore a 4 livelli (usare guard clauses)
- [ ] Le condizioni complesse sono decomposte in funzioni con nomi significativi
- [ ] Composizione preferita a ereditarieta profonda
- [ ] I principi SOLID sono rispettati dove appropriato
- [ ] Non ci sono God class o funzioni monolitiche
- [ ] I pattern di refactoring sono applicati dove servono (extract method, introduce parameter
  object, ecc.)

### Type Safety

- [ ] Tutte le funzioni pubbliche hanno type hints completi
- [ ] `mypy` passa senza errori (idealmente in modalita strict)
- [ ] I `# type: ignore` sono giustificati con un commento
- [ ] I type stubs sono installati per le dipendenze di terze parti
- [ ] `Any` e usato solo quando strettamente necessario

### Sicurezza

- [ ] Nessun segreto hardcoded (API key, password, token)
- [ ] Input utente validato prima dell'uso
- [ ] Query SQL parametrizzate (no string concatenation)
- [ ] Nessun `eval()`, `exec()`, o `pickle.loads()` su dati non fidati
- [ ] Le eccezioni non espongono stack trace o dati sensibili all'utente

### Testing

- [ ] I nuovi path di codice sono coperti da test
- [ ] La copertura del modulo modificato e >= 80%
- [ ] I test seguono il pattern AAA (Arrange-Act-Assert)
- [ ] I nomi dei test descrivono il comportamento atteso
- [ ] Nessun test disabilitato (`@pytest.mark.skip`) senza giustificazione

### Qualita del Codice

- [ ] Nessun codice duplicato (DRY)
- [ ] Nessun dead code (funzioni mai chiamate, import inutilizzati)
- [ ] Nessun `TODO` / `FIXME` senza ticket associato
- [ ] Gli errori sono gestiti esplicitamente, non silenziati
- [ ] Le funzioni pure sono preferite dove possibile
- [ ] Il pattern CQS e rispettato (command separati dalle query)

### Configurazione e Ambiente

- [ ] Nessun valore hardcoded che dovrebbe provenire dalla configurazione
- [ ] I nuovi parametri di configurazione hanno valori di default sensati
- [ ] Il file `.env.example` e aggiornato con le nuove variabili
- [ ] Le variabili sensibili usano `SecretStr` (pydantic-settings)

---

## Gestione del Debito Tecnico

Il **debito tecnico** (technical debt) e una metafora coniata da Ward Cunningham per descrivere
il costo futuro delle scorciatoie tecniche prese oggi. Come il debito finanziario, accumula
"interessi" sotto forma di maggiore complessita, bug piu frequenti e rallentamento dello
sviluppo.

### Classificazione del Debito Tecnico

Il debito tecnico non e tutto uguale. Martin Fowler lo classifica in quattro quadranti:

| | Deliberato | Involontario |
|---|---|---|
| **Prudente** | "Sappiamo che non e ideale, ma consegniamo ora e rifattorizziamo nella prossima sprint" | "Ora che abbiamo finito, ci rendiamo conto che avremmo dovuto usare un pattern diverso" |
| **Imprudente** | "Non abbiamo tempo per il design" | "Cos'e il Dependency Inversion Principle?" |

- **Prudente e deliberato**: accettabile, purche tracciato e pianificato.
- **Imprudente e deliberato**: pericoloso, spesso nasconde incompetenza o pressione eccessiva.
- **Prudente e involontario**: normale, emerge con la comprensione del dominio.
- **Imprudente e involontario**: sintomo di mancanza di formazione.

### Strategie di Gestione

#### 1. La Regola del Boy Scout

> "Lascia il codice piu pulito di come l'hai trovato."

Ogni volta che si tocca un file per una modifica, migliorare almeno una piccola cosa: rinominare
una variabile, estrarre una funzione, aggiungere un type hint. Queste micro-migliorie si
accumulano nel tempo senza richiedere sprint dedicati al refactoring.

#### 2. Tracciamento Sistematico

Il debito tecnico deve essere tracciato come qualsiasi altro lavoro di sviluppo:

```python
# Nel codice — collegare il TODO a un ticket
# TODO(PROJ-1234): Sostituire questo parsing manuale con pydantic model
# Scadenza: 2025-Q3. Rischio: medio (parsing fragile, nessuna validazione)
dati = json.loads(risposta.text)
nome = dati.get("name", "")

# FIXME(PROJ-5678): Race condition nella cache condivisa
# Impatto: corruzione dati sotto carico. Priorita: CRITICA
# Soluzione proposta: usare Redis con lock distribuito
cache[chiave] = valore
```

#### 3. Prioritizzazione con la Matrice Impatto-Sforzo

| | Basso sforzo | Alto sforzo |
|---|---|---|
| **Alto impatto** | **Fare subito** (quick wins) | **Pianificare nella roadmap** |
| **Basso impatto** | **Fare durante la manutenzione** | **Rivalutare se necessario** |

#### 4. Budget Dedicato

Riservare il 15-20% della capacita di ogni sprint alla riduzione del debito tecnico. Questo
approccio e sostenibile e previene l'accumulo che rende necessari i "grandi refactoring"
distruttivi.

#### 5. Metriche di Monitoraggio

```bash
# Script di monitoraggio del debito tecnico

# Contare TODO/FIXME/HACK con contesto
ruff check . --select FIX,TD --output-format json | python -c "
import json, sys
dati = json.load(sys.stdin)
print(f'TODO/FIXME totali: {len(dati)}')
"

# Complessita ciclomatica — funzioni sopra soglia
radon cc . -a -nc  # Solo grado C o peggiore

# Codice morto
vulture . --min-confidence 80

# Copertura dei test
pytest --cov=mio_progetto --cov-fail-under=80
```

### Quando Refactorizzare e Quando Riscrivere

**Refactorizzare** (miglioramento incrementale) quando:
- Il codice ha test che lo proteggono.
- La struttura di base e ragionevole.
- Le modifiche sono localizzabili.
- Il team comprende il codice esistente.

**Riscrivere** (sostituzione completa) solo quando:
- Il codice non ha test e non e testabile nella sua forma attuale.
- La tecnologia sottostante e obsoleta (es. Python 2).
- Il costo del refactoring supera il costo della riscrittura.
- Il debito e cosi pervasivo che ogni modifica introduce nuovi bug.

**Attenzione**: la riscrittura e quasi sempre piu rischiosa e costosa di quanto ci si aspetti.
La preferenza default dovrebbe essere sempre il refactoring incrementale.

---

## Clean Architecture in Python

La **Clean Architecture** (o architettura esagonale / ports and adapters) e un approccio alla
strutturazione del codice che separa rigorosamente la logica di business (domain) dalle
dipendenze esterne (database, API, framework web). L'obiettivo e rendere la logica di business
testabile, comprensibile e indipendente dalle scelte tecnologiche.

### Principi Fondamentali

1. **La regola della dipendenza**: le dipendenze nel codice puntano sempre verso l'interno
   (dal framework verso il dominio), mai verso l'esterno.
2. **Il dominio e indipendente**: la logica di business non sa nulla di database, HTTP, file
   system o framework.
3. **Le interfacce ai confini**: le porte (ports) definiscono cosa il dominio ha bisogno
   dal mondo esterno; gli adattatori (adapters) implementano queste porte.

### Struttura dei Layer

```
mio_progetto/
├── dominio/                    # Layer piu interno — logica di business pura
│   ├── entita/                 # Entita e value object del dominio
│   │   ├── ordine.py
│   │   ├── prodotto.py
│   │   └── valore/
│   │       ├── denaro.py
│   │       └── indirizzo.py
│   ├── servizi/                # Servizi di dominio (logica che non appartiene a una singola entita)
│   │   └── calcolo_prezzi.py
│   ├── porte/                  # Interfacce (Protocol) — cosa serve dal mondo esterno
│   │   ├── repository.py       # Port per la persistenza
│   │   ├── notifiche.py        # Port per le notifiche
│   │   └── pagamenti.py        # Port per i pagamenti
│   └── eccezioni.py            # Eccezioni di dominio
│
├── applicazione/               # Layer intermedio — casi d'uso / orchestrazione
│   ├── casi_uso/
│   │   ├── crea_ordine.py
│   │   ├── annulla_ordine.py
│   │   └── cerca_ordini.py
│   └── dto/                    # Data Transfer Objects per input/output dei casi d'uso
│       ├── ordine_dto.py
│       └── risultato.py
│
├── infrastruttura/             # Layer esterno — implementazioni concrete
│   ├── persistenza/
│   │   ├── repository_postgres.py   # Adapter per PostgreSQL
│   │   └── repository_memoria.py    # Adapter in memoria (per test)
│   ├── notifiche/
│   │   ├── email_smtp.py
│   │   └── notifiche_noop.py        # Null object per test/dev
│   └── pagamenti/
│       ├── stripe_adapter.py
│       └── pagamenti_mock.py
│
└── interfaccia/                # Layer piu esterno — entry points
    ├── api/
    │   ├── routes_ordini.py    # Endpoint HTTP (FastAPI/Flask)
    │   └── middleware.py
    ├── cli/
    │   └── comandi.py          # Comandi CLI
    └── composizione.py         # Dependency injection / wiring
```

### Implementazione Pratica

**Layer Dominio — entita e porte:**

```python
# dominio/entita/ordine.py
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class StatoOrdine(Enum):
    BOZZA = "bozza"
    CONFERMATO = "confermato"
    PAGATO = "pagato"
    SPEDITO = "spedito"
    ANNULLATO = "annullato"


@dataclass
class RigaOrdine:
    prodotto_id: UUID
    nome_prodotto: str
    prezzo_unitario: Decimal
    quantita: int

    @property
    def totale(self) -> Decimal:
        return self.prezzo_unitario * self.quantita


@dataclass
class Ordine:
    """Entita di dominio — contiene logica di business."""
    id: UUID = field(default_factory=uuid4)
    cliente_id: UUID = field(default_factory=uuid4)
    righe: list[RigaOrdine] = field(default_factory=list)
    stato: StatoOrdine = StatoOrdine.BOZZA

    @property
    def totale(self) -> Decimal:
        return sum(riga.totale for riga in self.righe)

    def conferma(self) -> None:
        if self.stato != StatoOrdine.BOZZA:
            raise StatoNonValidoError(
                f"Impossibile confermare un ordine in stato {self.stato.value}"
            )
        if not self.righe:
            raise OrdineVuotoError("Impossibile confermare un ordine senza righe")
        self.stato = StatoOrdine.CONFERMATO

    def annulla(self) -> None:
        stati_annullabili = {StatoOrdine.BOZZA, StatoOrdine.CONFERMATO}
        if self.stato not in stati_annullabili:
            raise StatoNonValidoError(
                f"Impossibile annullare un ordine in stato {self.stato.value}"
            )
        self.stato = StatoOrdine.ANNULLATO


# dominio/porte/repository.py
from typing import Protocol
from uuid import UUID


class RepositoryOrdini(Protocol):
    """Port — interfaccia che il dominio richiede per la persistenza."""
    def salva(self, ordine: Ordine) -> None: ...
    def trova_per_id(self, id: UUID) -> Ordine | None: ...
    def trova_per_cliente(self, cliente_id: UUID) -> list[Ordine]: ...
    def elimina(self, id: UUID) -> None: ...


class ServizioNotifiche(Protocol):
    """Port — interfaccia per l'invio di notifiche."""
    def notifica_ordine_confermato(self, ordine: Ordine) -> None: ...
    def notifica_ordine_annullato(self, ordine: Ordine) -> None: ...
```

**Layer Applicazione — casi d'uso:**

```python
# applicazione/casi_uso/crea_ordine.py
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ComandoCreaOrdine:
    """DTO di input per il caso d'uso."""
    cliente_id: UUID
    righe: tuple[RigaOrdineDTO, ...]


@dataclass(frozen=True, slots=True)
class RigaOrdineDTO:
    prodotto_id: UUID
    nome_prodotto: str
    prezzo_unitario: Decimal
    quantita: int


class CreaOrdine:
    """Caso d'uso: crea e conferma un nuovo ordine."""

    def __init__(
        self,
        repository: RepositoryOrdini,
        notifiche: ServizioNotifiche,
    ):
        self._repository = repository
        self._notifiche = notifiche

    def esegui(self, comando: ComandoCreaOrdine) -> UUID:
        ordine = Ordine(cliente_id=comando.cliente_id)

        for riga_dto in comando.righe:
            ordine.righe.append(RigaOrdine(
                prodotto_id=riga_dto.prodotto_id,
                nome_prodotto=riga_dto.nome_prodotto,
                prezzo_unitario=riga_dto.prezzo_unitario,
                quantita=riga_dto.quantita,
            ))

        ordine.conferma()
        self._repository.salva(ordine)
        self._notifiche.notifica_ordine_confermato(ordine)

        return ordine.id
```

**Layer Infrastruttura — adattatori concreti:**

```python
# infrastruttura/persistenza/repository_postgres.py
import sqlalchemy as sa
from sqlalchemy.orm import Session


class RepositoryOrdiniPostgreSQL:
    """Adapter — implementa la port RepositoryOrdini con PostgreSQL."""

    def __init__(self, sessione: Session):
        self._sessione = sessione

    def salva(self, ordine: Ordine) -> None:
        # Logica di mappatura ORM
        modello_db = self._mappa_a_modello_db(ordine)
        self._sessione.merge(modello_db)
        self._sessione.flush()

    def trova_per_id(self, id: UUID) -> Ordine | None:
        modello = self._sessione.get(OrdineDB, str(id))
        if modello is None:
            return None
        return self._mappa_a_dominio(modello)

    def trova_per_cliente(self, cliente_id: UUID) -> list[Ordine]:
        modelli = (
            self._sessione
            .query(OrdineDB)
            .filter(OrdineDB.cliente_id == str(cliente_id))
            .all()
        )
        return [self._mappa_a_dominio(m) for m in modelli]

    def elimina(self, id: UUID) -> None:
        self._sessione.query(OrdineDB).filter(OrdineDB.id == str(id)).delete()


# infrastruttura/persistenza/repository_memoria.py
class RepositoryOrdiniInMemoria:
    """Adapter in memoria — per test e sviluppo locale."""

    def __init__(self):
        self._ordini: dict[UUID, Ordine] = {}

    def salva(self, ordine: Ordine) -> None:
        self._ordini[ordine.id] = ordine

    def trova_per_id(self, id: UUID) -> Ordine | None:
        return self._ordini.get(id)

    def trova_per_cliente(self, cliente_id: UUID) -> list[Ordine]:
        return [o for o in self._ordini.values() if o.cliente_id == cliente_id]

    def elimina(self, id: UUID) -> None:
        self._ordini.pop(id, None)
```

**Composizione — wiring delle dipendenze:**

```python
# interfaccia/composizione.py
def crea_servizio_ordini_produzione(sessione_db: Session) -> CreaOrdine:
    """Factory per il contesto di produzione."""
    return CreaOrdine(
        repository=RepositoryOrdiniPostgreSQL(sessione_db),
        notifiche=NotificatoreEmailSMTP(client_smtp),
    )

def crea_servizio_ordini_test() -> CreaOrdine:
    """Factory per i test — nessuna dipendenza esterna."""
    return CreaOrdine(
        repository=RepositoryOrdiniInMemoria(),
        notifiche=NotificatoreNullo(),
    )
```

### Vantaggi della Clean Architecture

- **Testabilita**: la logica di business si testa senza database, rete o file system. I test
  girano in millisecondi usando adattatori in memoria.
- **Indipendenza dal framework**: cambiare da Flask a FastAPI o da PostgreSQL a MongoDB richiede
  solo un nuovo adattatore, senza toccare il dominio.
- **Leggibilita**: la struttura a layer rende chiaro dove trovare ogni tipo di logica.
- **Evoluzione**: il dominio evolve indipendentemente dall'infrastruttura.

### Quando Usare la Clean Architecture

La clean architecture aggiunge complessita strutturale. Non e appropriata per:
- Script una tantum o prototipi.
- CRUD semplici senza logica di business.
- Progetti con un singolo sviluppatore e durata breve.

E fortemente raccomandata per:
- Applicazioni con logica di business complessa.
- Progetti con lunga durata di vita (anni).
- Team di piu sviluppatori.
- Sistemi dove le scelte tecnologiche possono cambiare.

### Testing nella Clean Architecture

Uno dei vantaggi piu importanti della Clean Architecture e la facilita con cui si testano i
diversi layer in isolamento. Ogni layer ha una strategia di test distinta.

**Test del dominio — puri e velocissimi:**

```python
# test/dominio/test_ordine.py
from decimal import Decimal
from uuid import uuid4

import pytest
from dominio.entita.ordine import Ordine, RigaOrdine, StatoOrdine


class TestOrdine:
    """Test dell'entita Ordine — nessuna dipendenza esterna."""

    def test_crea_ordine_vuoto(self) -> None:
        ordine = Ordine(cliente_id=uuid4())
        assert ordine.stato == StatoOrdine.BOZZA
        assert ordine.totale == Decimal("0")
        assert len(ordine.righe) == 0

    def test_aggiungi_riga_calcola_totale(self) -> None:
        ordine = Ordine(cliente_id=uuid4())
        riga = RigaOrdine(
            prodotto_id=uuid4(),
            nome_prodotto="Widget",
            prezzo_unitario=Decimal("9.99"),
            quantita=3,
        )
        ordine_aggiornato = ordine.aggiungi_riga(riga)
        assert ordine_aggiornato.totale == Decimal("29.97")

    def test_conferma_ordine_vuoto_solleva_errore(self) -> None:
        ordine = Ordine(cliente_id=uuid4())
        with pytest.raises(ValueError, match="vuoto"):
            ordine.conferma()

    def test_annulla_ordine_pagato_solleva_errore(self) -> None:
        ordine = Ordine(cliente_id=uuid4(), stato=StatoOrdine.PAGATO)
        with pytest.raises(ValueError, match="pagato"):
            ordine.annulla()

    def test_transizione_stati_valida(self) -> None:
        """Verifica il flusso BOZZA -> CONFERMATO -> PAGATO -> SPEDITO."""
        ordine = Ordine(cliente_id=uuid4())
        riga = RigaOrdine(
            prodotto_id=uuid4(),
            nome_prodotto="Widget",
            prezzo_unitario=Decimal("10.00"),
            quantita=1,
        )
        ordine = ordine.aggiungi_riga(riga)
        ordine = ordine.conferma()
        assert ordine.stato == StatoOrdine.CONFERMATO

        ordine = ordine.segna_pagato()
        assert ordine.stato == StatoOrdine.PAGATO

        ordine = ordine.segna_spedito()
        assert ordine.stato == StatoOrdine.SPEDITO
```

**Test del layer applicazione — con adattatori in memoria:**

```python
# test/applicazione/test_crea_ordine.py
from decimal import Decimal
from uuid import uuid4

from applicazione.casi_uso.crea_ordine import ComandoCreaOrdine, CreaOrdine
from infrastruttura.persistenza.repository_memoria import RepositoryOrdiniInMemoria
from infrastruttura.notifiche.notifiche_noop import NotificatoreNullo


class TestCreaOrdine:
    """Test del caso d'uso — usa adattatori in memoria, nessun DB reale."""

    def setup_method(self) -> None:
        self.repository = RepositoryOrdiniInMemoria()
        self.notifiche = NotificatoreNullo()
        self.caso_uso = CreaOrdine(
            repository=self.repository,
            notifiche=self.notifiche,
        )

    def test_crea_ordine_con_righe(self) -> None:
        comando = ComandoCreaOrdine(
            cliente_id=uuid4(),
            righe=[
                {"prodotto_id": uuid4(), "nome": "Widget A", "prezzo": Decimal("15.00"), "quantita": 2},
                {"prodotto_id": uuid4(), "nome": "Widget B", "prezzo": Decimal("25.00"), "quantita": 1},
            ],
        )
        risultato = self.caso_uso.esegui(comando)
        assert risultato.successo is True

        ordine_salvato = self.repository.trova_per_id(risultato.ordine_id)
        assert ordine_salvato is not None
        assert len(ordine_salvato.righe) == 2
        assert ordine_salvato.totale == Decimal("55.00")

    def test_ordine_senza_righe_fallisce(self) -> None:
        comando = ComandoCreaOrdine(cliente_id=uuid4(), righe=[])
        risultato = self.caso_uso.esegui(comando)
        assert risultato.successo is False
        assert "vuoto" in risultato.messaggio_errore.lower()

    def test_notifica_inviata_dopo_creazione(self) -> None:
        comando = ComandoCreaOrdine(
            cliente_id=uuid4(),
            righe=[{"prodotto_id": uuid4(), "nome": "X", "prezzo": Decimal("10.00"), "quantita": 1}],
        )
        self.caso_uso.esegui(comando)
        assert self.notifiche.messaggi_inviati == 1
```

La piramide dei test nella Clean Architecture segue un pattern preciso:

| Layer | Tipo di Test | Velocita | Dipendenze Esterne |
|-------|-------------|----------|-------------------|
| Dominio | Unit test puri | < 1ms ciascuno | Nessuna |
| Applicazione | Test con mock/stub | < 10ms ciascuno | Adattatori in memoria |
| Infrastruttura | Test di integrazione | 100ms+ | Database, API reali |
| Interfaccia | Test E2E | 1s+ | Stack completo |

La regola fondamentale: **la maggior parte dei test deve vivere nei layer interni**. Se la
maggioranza dei test richiede un database, la separazione dei layer non e stata rispettata.

---

## Pre-commit Hooks — Setup Completo

I **pre-commit hooks** automatizzano i controlli di qualita prima di ogni commit, impedendo che
codice non conforme entri nel repository. Il framework `pre-commit` semplifica la gestione di
questi hook, supportando tool scritti in qualsiasi linguaggio.

### Installazione e Configurazione Base

```bash
# Installazione del framework pre-commit
pip install pre-commit

# Generazione del file di configurazione iniziale
pre-commit sample-config > .pre-commit-config.yaml

# Installazione degli hook nel repository git
pre-commit install

# Esecuzione manuale su tutti i file (utile dopo la prima configurazione)
pre-commit run --all-files
```

### Configurazione Completa per Python

```yaml
# .pre-commit-config.yaml
repos:
  # Ruff — linting e formatting in un unico tool
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        types_or: [python, pyi, jupyter]
      - id: ruff-format
        types_or: [python, pyi, jupyter]

  # Mypy — type checking statico
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic
          - types-requests
        args: [--strict]

  # Hook generici di pre-commit
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--unsafe]
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key
      - id: no-commit-to-branch
        args: [--branch, main, --branch, master]

  # Bandit — analisi di sicurezza statica
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]

  # Controllo delle dipendenze per vulnerabilita note
  - repo: https://github.com/pyupio/safety
    rev: 3.2.14
    hooks:
      - id: safety
        args: [check, --full-report]
```

### Integrazione con pyproject.toml

```toml
# pyproject.toml — sezione complementare per pre-commit

[tool.bandit]
exclude_dirs = ["tests", "scripts"]
skips = ["B101"]  # Permetti assert nei test

[tool.ruff]
target-version = "py312"
line-length = 99

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "UP",    # pyupgrade
    "B",     # bugbear
    "SIM",   # simplify
    "S",     # bandit (security)
    "C4",    # comprehensions
    "DTZ",   # datetime timezone
    "T20",   # print statements
    "RUF",   # ruff-specific rules
    "PT",    # pytest style
    "ERA",   # eradicate (commented code)
]
ignore = ["E501"]  # Line length gestito da ruff-format

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S106"]  # Permetti assert e password hardcoded nei test
```

### Best Practices per Pre-commit Hooks

1. **Pinning delle versioni**: usa sempre `rev` con un tag specifico, non `main` o `HEAD`.
   Aggiorna le versioni periodicamente con `pre-commit autoupdate`.

2. **Hook locali per tool custom**: per script specifici del progetto, usa hook locali:

```yaml
  - repo: local
    hooks:
      - id: controlla-migrazioni
        name: Verifica coerenza migrazioni
        entry: python scripts/controlla_migrazioni.py
        language: python
        files: "migrations/"
        pass_filenames: false
```

3. **CI integration**: esegui `pre-commit run --all-files` nella pipeline CI per
   garantire che nessun commit sfugga ai controlli locali.

4. **Velocita**: ordina gli hook dal piu veloce al piu lento. Se mypy rallenta troppo
   il flusso locale, spostalo in CI e tienilo fuori dai pre-commit hooks locali.

5. **Cache**: pre-commit mantiene una cache degli ambienti virtuali per ogni hook.
   Se qualcosa si corrompe, usa `pre-commit clean` per ripulire la cache.

6. **Skip temporaneo**: in casi eccezionali (merge urgente, hotfix critico), e possibile
   saltare i controlli con `git commit --no-verify`. Documentare sempre il motivo nel
   messaggio di commit e risolvere i problemi immediatamente dopo.

---

## Esercizi

1. **Refactoring di una God Class** — Prendi una classe con piu di 300 righe e almeno 5 responsabilita diverse (es. una classe `UserManager` che gestisce autenticazione, validazione, persistenza, notifiche e logging). Applica il Single Responsibility Principle estraendo classi focalizzate. Misura la complessita ciclomatica prima e dopo con `radon cc -a`. L'obiettivo e che nessun metodo superi complessita C.

2. **Type hints retrofit** — Prendi un modulo Python esistente (almeno 200 righe) senza type hints e aggiungi annotazioni di tipo complete. Configura `mypy --strict` e risolvi tutti gli errori. Documenta i casi in cui hai dovuto usare `cast()`, `TYPE_CHECKING`, o `@overload` e spiega perche. Verifica che `mypy` passi senza errori.

3. **Configurazione Ruff completa** — Configura Ruff in un progetto Python esistente: (a) abilita le regole PEP 8, isort, pyflakes, bugbear, e pyupgrade nel `pyproject.toml`, (b) correggi tutti gli errori segnalati, (c) configura un pre-commit hook che esegua `ruff check --fix` e `ruff format`, (d) documenta le regole che hai deliberatamente disabilitato e perche.

4. **Code smells hunting** — Analizza un progetto open-source Python di media dimensione (3000-5000 righe) con `radon cc`, `radon mi`, `vulture` e `ruff`. Identifica almeno 10 code smells distinti, classificali per severita, e proponi un piano di refactoring ordinato per priorita (fix first: bug risk > maintainability > style).

5. **Test come documentazione** — Per un modulo con almeno 5 funzioni pubbliche, scrivi una suite di test che serva simultaneamente come documentazione del comportamento. Ogni test deve avere un nome che descriva il comportamento (`test_returns_empty_list_when_no_items_match_query`), usare il pattern Given-When-Then, e coprire almeno: happy path, edge case, e error case per ogni funzione. Target: 90%+ coverage.

---

## Letture e Riferimenti

### Fonti primarie

- PEP 8 — *Style Guide for Python Code* — https://peps.python.org/pep-0008/ (consultato: 2026-05-24)
- PEP 257 — *Docstring Conventions* — https://peps.python.org/pep-0257/ (consultato: 2026-05-24)
- PEP 484 — *Type Hints* — https://peps.python.org/pep-0484/ (consultato: 2026-05-24)
- PEP 612 — *Parameter Specification Variables* — https://peps.python.org/pep-0612/ (consultato: 2026-05-24)
- Ruff Documentation — https://docs.astral.sh/ruff/ (consultato: 2026-05-24)
- mypy Documentation — https://mypy.readthedocs.io/ (consultato: 2026-05-24)
- radon Documentation — https://radon.readthedocs.io/ (consultato: 2026-05-24)
- Python Documentation — *`typing` module* — https://docs.python.org/3/library/typing.html (consultato: 2026-05-24)
- vulture — *Find dead Python code* — https://github.com/jendrikseipp/vulture (consultato: 2026-05-24)

### Libri consigliati

- *Clean Code* — Robert C. Martin — Prentice Hall, 2008
- *Refactoring: Improving the Design of Existing Code, 2nd Edition* — Martin Fowler — Addison-Wesley, 2018
- *Robust Python* — Patrick Viafore — O'Reilly, 2021

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [21 — Design Patterns](21-design-patterns.md) | Pattern GoF e principi SOLID applicati al codice Python |
| [23 — Testing](23-testing.md) | Test come documentazione, TDD, copertura del codice |
| [25 — Performance](25-performance.md) | Profiling e ottimizzazione — clean code vs performance |
| [07 — OOP](07-oop.md) | Classi, ereditarieta, composizione — fondamenta per SOLID |
| [27 — CI/CD](27-ci-cd-per-python.md) | Automazione di linting, formatting e type checking nella CI |
| [03 — Funzioni e Scope](03-funzioni-scope.md) | Funzioni piccole, naming, scope — blocchi base del clean code |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Clean Code** | Codice sorgente scritto in modo chiaro, leggibile e manutenibile, che si legge come prosa ben scritta |
| **PEP 8** | Guida di stile ufficiale per il codice Python, che definisce convenzioni su indentazione, naming, spaziatura e organizzazione |
| **Ruff** | Linter e formatter Python ultra-veloce (scritto in Rust) che sostituisce black, isort, flake8 e molti altri strumenti |
| **mypy** | Type checker statico per Python che verifica la correttezza delle annotazioni di tipo senza eseguire il codice |
| **Type Hint** | Annotazione di tipo nel codice Python (`def f(x: int) -> str`) che abilita il controllo statico e migliora la documentazione |
| **Code Smell** | Indicatore superficiale di un possibile problema piu profondo nel codice (metodo lungo, classe troppo grande, naming oscuro) |
| **Refactoring** | Ristrutturazione del codice che ne migliora la qualita interna senza modificarne il comportamento esterno osservabile |
| **Complessita Ciclomatica** | Metrica che misura il numero di percorsi indipendenti attraverso il codice; valori alti indicano codice difficile da testare |
| **SOLID** | Cinque principi di progettazione OOP: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| **DRY** | Don't Repeat Yourself — principio che esorta a eliminare la duplicazione estraendo logica comune |
| **KISS** | Keep It Simple, Stupid — principio che favorisce la soluzione piu semplice che funziona |
| **YAGNI** | You Aren't Gonna Need It — principio che sconsiglia di costruire funzionalita prima che siano realmente necessarie |
| **Docstring** | Stringa di documentazione posta come prima istruzione di modulo, classe o funzione, accessibile tramite `__doc__` |
| **Protocol** | Classe astratta strutturale (`typing.Protocol`) per definire interfacce senza richiedere ereditarieta esplicita |
