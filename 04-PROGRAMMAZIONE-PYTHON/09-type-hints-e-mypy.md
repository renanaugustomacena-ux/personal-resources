---
corso: "Programmazione Python"
fase: "2 — Typing e Qualità del Codice"
modulo: "09"
titolo: "Type Hints e Mypy"
versione: "Python 3.12+ (PEP 695 type statement)"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti del Linguaggio"
  - "02 — OOP"
  - "03 — Funzioni e Scope"
obiettivi:
  - "Padroneggiare il sistema di type hints da PEP 484 a PEP 742"
  - "Scrivere codice generico type-safe con TypeVar, ParamSpec, Protocol"
  - "Configurare mypy in modalita strict con plugin e daemon"
  - "Confrontare mypy e pyright e integrarli nella CI/CD"
  - "Applicare gradual typing a codebase esistenti"
  - "Utilizzare pattern avanzati: TYPE_CHECKING, Concatenate, TypeIs"
tag: [type-hints, mypy, pyright, typing, Protocol, TypeVar, ParamSpec, gradual-typing]
---

# Type Hints e Mypy — Guida Completa

> **Modulo 09** · **Aggiornamento:** 2026-05-24 · **Versione:** Python 3.12+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti](01-fondamenti-linguaggio.md), [OOP](02-oop.md), [Funzioni e Scope](03-funzioni-scope.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare il sistema di type hints da PEP 484 a PEP 742, inclusa la sintassi `type` di Python 3.12+
> 2. Scrivere codice generico type-safe con `TypeVar`, `ParamSpec`, `TypeVarTuple` e `Protocol`
> 3. Configurare e utilizzare mypy in modalita `strict`, con plugin, daemon e configurazione per modulo
> 4. Confrontare mypy e pyright e integrarli efficacemente nella pipeline CI/CD
> 5. Applicare strategie di gradual typing per aggiungere type hints a codebase esistenti
> 6. Utilizzare pattern avanzati: `TYPE_CHECKING`, forward references, `Concatenate`, `TypeIs`
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

---

## Mappa concettuale

```
                        ┌──────────────────────────────┐
                        │      SISTEMA DI TIPI         │
                        │        PYTHON                │
                        └──────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────▼────────┐  ┌───────▼───────┐   ┌───────▼───────┐
     │  FONDAMENTI      │  │  TIPI AVANZATI│   │ TYPE CHECKER  │
     │  PEP 484/526/604│  │  Generic/Proto│   │  mypy/pyright │
     └────────┬────────┘  └───────┬───────┘   └───────┬───────┘
              │                    │                    │
     ┌────────▼────────┐  ┌───────▼───────┐   ┌───────▼───────┐
     │ str, int, float │  │ TypeVar       │   │ Configurazione│
     │ list[], dict[]  │  │ ParamSpec     │   │ strict mode   │
     │ X | Y (union)   │  │ Protocol      │   │ plugin        │
     │ Optional        │  │ TypeVarTuple  │   │ daemon (dmypy)│
     └────────┬────────┘  │ Overload      │   │ CI/CD         │
              │           │ TypeGuard/Is  │   └───────┬───────┘
              │           │ Concatenate   │           │
              │           └───────┬───────┘           │
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     PATTERN PRATICI          │
                    │ TYPE_CHECKING · forward ref  │
                    │ gradual typing · runtime     │
                    │ decoratori · generici        │
                    └─────────────────────────────┘
```

---

## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti Type Hints](#fondamenti-type-hints)
3. [Tipi dal Modulo typing](#tipi-dal-modulo-typing)
4. [Tipi Avanzati](#tipi-avanzati)
5. [Mypy](#mypy)
6. [Altri Type Checker](#altri-type-checker)
7. [Pattern Pratici](#pattern-pratici)
8. [Pattern Avanzati: TYPE_CHECKING e Forward References](#pattern-avanzati-type_checking-e-forward-references)
9. [Runtime Type Checking](#runtime-type-checking)
10. [Migrazione a Strict Typing](#migrazione-di-una-codebase-a-strict-typing--guida-passo-passo)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [Esercizi](#esercizi)
14. [Letture e Risorse](#letture-e-risorse)
15. [Cross-link](#cross-link)
16. [Glossario](#glossario)

---

## Panoramica

Python e un linguaggio a **tipizzazione dinamica**: le variabili non dichiarano esplicitamente il loro tipo e i controlli avvengono a runtime. Questa flessibilita e uno dei punti di forza del linguaggio, ma nei progetti di media e grande dimensione puo diventare una fonte significativa di bug difficili da individuare.

I **type hints** (annotazioni di tipo), introdotti ufficialmente con il **PEP 484** in Python 3.5, permettono di aggiungere informazioni sui tipi direttamente nel codice sorgente. Si tratta di annotazioni puramente **opzionali** e **dichiarative**: l'interprete CPython le ignora completamente a runtime (salvo casi particolari come `dataclasses` e `pydantic`), ma strumenti esterni di analisi statica possono leggerle per verificare la coerenza del programma prima dell'esecuzione.

**Mypy** e il type checker statico di riferimento per Python, sviluppato originariamente da Jukka Lehtosalo presso Dropbox. Analizza il codice annotato e segnala incongruenze di tipo senza mai eseguirlo. Insieme a mypy esistono altri strumenti come **pyright** (Microsoft) e **pytype** (Google), ciascuno con le proprie peculiarita.

### Perche usare i type hints?

- **Rilevamento precoce dei bug**: errori di tipo vengono individuati prima che il codice raggiunga la produzione.
- **Documentazione vivente**: le annotazioni fungono da documentazione che non puo andare "out of sync" col codice, perche i type checker la verificano.
- **Supporto IDE migliorato**: autocompletamento, refactoring e navigazione del codice diventano molto piu precisi.
- **Manutenibilita**: in un team o in un progetto a lungo termine, i type hints rendono il codice piu leggibile e comprensibile.
- **Refactoring sicuro**: cambiare la firma di una funzione rivela immediatamente tutti i punti del codice che devono essere aggiornati.

### Comportamento a runtime

Un punto cruciale da comprendere: **Python non applica i type hints a runtime**. Le annotazioni vengono memorizzate nell'attributo `__annotations__` di funzioni, classi e moduli, ma l'interprete non le utilizza per verificare i tipi durante l'esecuzione:

```python
def somma(a: int, b: int) -> int:
    return a + b

# Nessun errore a runtime, nonostante il tipo errato
risultato = somma("ciao", "mondo")  # "ciaomondo"
```

L'applicazione dei type hints avviene tramite strumenti esterni come mypy, pyright o pytype, eseguiti separatamente (tipicamente nella pipeline CI/CD o nell'IDE). Librerie come `beartype` o `typeguard` possono aggiungere il controllo a runtime tramite decoratori, ma questo non fa parte del comportamento standard di Python.

### PEP fondamentali

| PEP | Versione | Descrizione |
|-----|----------|-------------|
| PEP 3107 | 3.0 | Sintassi base per le annotazioni sulle funzioni |
| PEP 484 | 3.5 | Type hints formali, modulo `typing` |
| PEP 526 | 3.6 | Annotazioni per le variabili (`x: int = 5`) |
| PEP 544 | 3.8 | `Protocol` per structural subtyping |
| PEP 585 | 3.9 | Generici built-in (`list[int]` al posto di `List[int]`) |
| PEP 604 | 3.10 | Sintassi `X | Y` al posto di `Union[X, Y]` |
| PEP 612 | 3.10 | `ParamSpec` per typing dei decoratori |
| PEP 613 | 3.10 | `TypeAlias` esplicito |
| PEP 646 | 3.11 | `TypeVarTuple` per tuple variadiche |
| PEP 673 | 3.11 | `Self` type |
| PEP 695 | 3.12 | Nuova sintassi `type X = ...` e generici inline |
| PEP 696 | 3.13 | Valori predefiniti per `TypeVar`, `ParamSpec`, `TypeVarTuple` |
| PEP 698 | 3.12 | Decoratore `@override` per metodi sovrascritti |
| PEP 742 | 3.13 | `TypeIs` (versione migliorata di `TypeGuard`) |

### Evoluzione della sintassi: da typing a built-in

Un trend fondamentale nel sistema di tipi Python e la migrazione progressiva dalla necessita di importare da `typing` verso costrutti built-in nativi. Questo semplifica il codice e riduce il boilerplate:

```python
# Evoluzione nel tempo:

# Python 3.5 (PEP 484)
from typing import List, Dict, Optional, Union
def f(x: List[int]) -> Optional[Dict[str, int]]:
    ...

# Python 3.9 (PEP 585) — generici built-in
def f(x: list[int]) -> dict[str, int] | None:  # 3.10 per |
    ...

# Python 3.10 (PEP 604) — union con pipe
def f(x: list[int]) -> dict[str, int] | None:
    ...

# Python 3.12 (PEP 695) — type statement e generici inline
type NumeroOStringa = int | str
def primo[T](lista: list[T]) -> T:
    return lista[0]
```

Per supportare la sintassi moderna anche su versioni precedenti, si puo usare `from __future__ import annotations` (PEP 563), che trasforma tutte le annotazioni in stringhe valutate lazily. Tuttavia, questo approccio ha dei limiti con il runtime type checking (ad es. Pydantic v1).

---

## Fondamenti Type Hints

### Annotazioni di base

I tipi fondamentali di Python corrispondono direttamente alle classi built-in:

```python
# Tipi scalari fondamentali
nome: str = "Mario"
eta: int = 30
altezza: float = 1.75
attivo: bool = True
valore: None = None
dati: bytes = b"ciao"
```

Le annotazioni **non modificano il comportamento a runtime**. Scrivere `eta: int = "trenta"` non genera alcun errore durante l'esecuzione, ma un type checker come mypy segnalera l'incongruenza.

### Annotazioni sulle funzioni

Le annotazioni sulle funzioni coprono sia i **parametri** sia il **valore di ritorno**:

```python
def saluta(nome: str) -> str:
    return f"Ciao, {nome}!"

def somma(a: int, b: int) -> int:
    return a + b

def stampa_messaggio(msg: str) -> None:
    print(msg)
```

Il tipo di ritorno `-> None` indica esplicitamente che la funzione non restituisce un valore significativo. E buona pratica annotarlo sempre, anche quando sembra ovvio.

#### Parametri con valore predefinito

```python
def connetti(host: str, porta: int = 5432, ssl: bool = True) -> None:
    ...
```

#### Parametri *args e **kwargs

```python
def log(*messaggi: str, **opzioni: bool) -> None:
    # messaggi e una tuple[str, ...]
    # opzioni e un dict[str, bool]
    for msg in messaggi:
        print(msg)
```

Quando si annota `*args: str`, ogni singolo argomento posizionale deve essere `str`. Analogamente, `**kwargs: bool` indica che ogni valore nel dizionario dei keyword arguments deve essere `bool`.

### Annotazioni per variabili (PEP 526)

A partire da Python 3.6, le variabili possono essere annotate senza necessariamente assegnare un valore:

```python
# Con assegnamento
contatore: int = 0
nomi: list[str] = []

# Senza assegnamento (dichiarazione)
risultato: float
messaggi: list[str]
```

Le annotazioni senza assegnamento sono utili per dichiarare il tipo atteso di una variabile che verra inizializzata successivamente, ad esempio all'interno di un blocco condizionale.

### Annotazioni in classi

```python
class Persona:
    nome: str
    eta: int
    email: str | None

    def __init__(self, nome: str, eta: int, email: str | None = None) -> None:
        self.nome = nome
        self.eta = eta
        self.email = email

    def presentati(self) -> str:
        return f"Mi chiamo {self.nome} e ho {self.eta} anni."
```

### La sintassi union con pipe (PEP 604, Python 3.10+)

Prima di Python 3.10, per indicare che una variabile poteva avere piu di un tipo si usava `Union`:

```python
from typing import Union

def elabora(dato: Union[str, int]) -> Union[str, int]:
    ...
```

Da Python 3.10 in poi, la sintassi e stata semplificata con l'operatore `|`:

```python
def elabora(dato: str | int) -> str | int:
    ...

# Equivalente a Optional[str]:
nome: str | None = None
```

Per utilizzare la nuova sintassi anche in versioni precedenti a Python 3.10, e possibile importare `annotations` dal modulo `__future__`:

```python
from __future__ import annotations

# Ora X | Y funziona anche su Python 3.7+
def elabora(valore: int | str) -> int | str:
    ...
```

---

## Tipi dal Modulo typing

Il modulo `typing` fornisce costrutti avanzati per descrivere tipi complessi. Con l'evoluzione di Python, molti di questi costrutti hanno ottenuto alternative built-in piu semplici.

### Collezioni generiche

```python
# Python 3.5-3.8: si usano i tipi dal modulo typing
from typing import List, Dict, Set, Tuple, FrozenSet

nomi: List[str] = ["Alice", "Bob"]
voti: Dict[str, int] = {"Alice": 30, "Bob": 28}
tag: Set[str] = {"python", "typing"}
coordinate: Tuple[float, float] = (45.46, 9.19)
costanti: FrozenSet[int] = frozenset({1, 2, 3})

# Python 3.9+: si usano direttamente i tipi built-in (PEP 585)
nomi: list[str] = ["Alice", "Bob"]
voti: dict[str, int] = {"Alice": 30, "Bob": 28}
tag: set[str] = {"python", "typing"}
coordinate: tuple[float, float] = (45.46, 9.19)
costanti: frozenset[int] = frozenset({1, 2, 3})
```

**Nota**: `Tuple[float, float]` indica una tupla di esattamente due elementi `float`. Per una tupla di lunghezza variabile si usa `tuple[float, ...]`.

### Tipi di collezione astratti

Quando si annotano i parametri di una funzione, e buona pratica usare i tipi astratti (interfacce) piuttosto che quelli concreti, per massimizzare la flessibilita:

```python
from collections.abc import Sequence, Mapping, MutableMapping, Iterable, Iterator

# Sequence: qualsiasi sequenza (list, tuple, str, ...)
def primo_elemento(seq: Sequence[int]) -> int:
    return seq[0]

# Mapping: qualsiasi mapping in sola lettura
def cerca_valore(mappa: Mapping[str, int], chiave: str) -> int | None:
    return mappa.get(chiave)

# Iterable: qualsiasi oggetto iterabile
def somma_tutti(elementi: Iterable[int]) -> int:
    return sum(elementi)

# Iterator: un iteratore specifico
def prossimi_n(it: Iterator[int], n: int) -> list[int]:
    return [next(it) for _ in range(n)]
```

### Optional

`Optional[X]` e un alias per `Union[X, None]`, cioe indica che il valore puo essere di tipo `X` oppure `None`:

```python
from typing import Optional

def trova_utente(user_id: int) -> Optional[str]:
    # Restituisce il nome se trovato, None altrimenti
    if user_id in database:
        return database[user_id]
    return None

# Python 3.10+: equivalente con la sintassi pipe
def trova_utente(user_id: int) -> str | None:
    ...
```

**Attenzione**: `Optional[str]` non significa "parametro opzionale". Un parametro e opzionale quando ha un valore predefinito, indipendentemente dal tipo:

```python
# Il parametro `nome` e obbligatorio anche se Optional
def saluta(nome: Optional[str]) -> str:
    if nome is None:
        return "Ciao, sconosciuto!"
    return f"Ciao, {nome}!"

# Parametro opzionale con valore predefinito None
def salva(nome: str, nota: str | None = None) -> None:
    ...
```

### Union

`Union` descrive un tipo che puo essere uno tra diversi tipi specificati:

```python
from typing import Union

def converti(valore: Union[str, int, float]) -> str:
    return str(valore)

# Python 3.10+
def converti(valore: str | int | float) -> str:
    return str(valore)
```

### Any

`Any` e il tipo "jolly" compatibile con qualunque altro tipo. Usarlo equivale essenzialmente a disabilitare il type checking per quella particolare annotazione:

```python
from typing import Any

def log(messaggio: Any) -> None:
    print(str(messaggio))

# Any e compatibile in entrambe le direzioni:
x: Any = 42
y: str = x  # OK per mypy (ma potenzialmente errato!)
```

`Any` andrebbe usato con parsimonia: il suo impiego eccessivo vanifica i benefici del type checking. Si noti la differenza con `object`: un valore di tipo `object` richiede controlli espliciti prima di poter essere usato come tipo specifico, mentre `Any` bypassa completamente il type checker.

### Literal

`Literal` restringe il tipo a un insieme specifico di valori costanti:

```python
from typing import Literal

Direzione = Literal["nord", "sud", "est", "ovest"]

def muovi(direzione: Direzione, passi: int) -> None:
    print(f"Muovo {passi} passi verso {direzione}")

muovi("nord", 3)   # OK
muovi("alto", 3)   # Errore mypy: "alto" non e tra i valori ammessi

# Literal con numeri e booleani
def imposta_livello(livello: Literal[0, 1, 2]) -> None:
    ...

# Combinazione: utile per distinguere il tipo di ritorno
Modalita = Literal["lettura", "scrittura", "aggiunta"]
```

### Final

`Final` dichiara che una variabile non deve essere riassegnata dopo l'inizializzazione:

```python
from typing import Final

MAX_TENTATIVI: Final = 3
PI_GRECO: Final[float] = 3.14159

MAX_TENTATIVI = 5  # Errore mypy: non si puo riassegnare un Final
```

Per le classi, `@final` (decoratore) impedisce l'override di un metodo o l'ereditarieta di una classe:

```python
from typing import final

class Base:
    @final
    def metodo_critico(self) -> None:
        ...

class Derivata(Base):
    def metodo_critico(self) -> None:  # Errore mypy
        ...

@final
class Immutabile:
    ...

class Tentativo(Immutabile):  # Errore mypy: non si puo ereditare da @final
    ...
```

### ClassVar

`ClassVar` indica che un attributo appartiene alla classe e non alle singole istanze:

```python
from typing import ClassVar

class Connessione:
    max_connessioni: ClassVar[int] = 100  # Attributo di classe
    host: str                              # Attributo di istanza

    def __init__(self, host: str) -> None:
        self.host = host
```

### TypeAlias (Python 3.10+)

`TypeAlias` rende esplicita la creazione di un alias di tipo, eliminando l'ambiguita con una semplice assegnazione:

```python
from typing import TypeAlias

# Python 3.10+
Coordinate: TypeAlias = tuple[float, float]
Matrice: TypeAlias = list[list[float]]
RispostaJSON: TypeAlias = dict[str, Any]

# Python 3.12+ (PEP 695): sintassi nativa
type Coordinate = tuple[float, float]
type Matrice = list[list[float]]
type RispostaJSON = dict[str, Any]
```

Senza `TypeAlias`, mypy potrebbe confondere un alias di tipo con una semplice assegnazione di variabile, portando a comportamenti inaspettati nell'analisi statica.

### Self (Python 3.11+)

`Self` rappresenta il tipo della classe corrente, particolarmente utile per metodi che restituiscono l'istanza stessa (pattern fluent/builder):

```python
from typing import Self

class QueryBuilder:
    def __init__(self) -> None:
        self._tabella: str = ""
        self._condizioni: list[str] = []

    def da(self, tabella: str) -> Self:
        self._tabella = tabella
        return self

    def dove(self, condizione: str) -> Self:
        self._condizioni.append(condizione)
        return self

class QueryBuilderEsteso(QueryBuilder):
    def limite(self, n: int) -> Self:
        return self

# Senza Self, il metodo `da` restituirebbe QueryBuilder, non QueryBuilderEsteso
obj = QueryBuilderEsteso().da("utenti").limite(10)  # OK, tipo: QueryBuilderEsteso
```

Prima di Python 3.11, si otteneva lo stesso risultato con `TypeVar`:

```python
from typing import TypeVar

T = TypeVar("T", bound="QueryBuilder")

class QueryBuilder:
    def da(self: T, tabella: str) -> T:
        self._tabella = tabella
        return self
```

---

## Tipi Avanzati

### TypeVar e generics

`TypeVar` definisce una **variabile di tipo** che permette di scrivere funzioni e classi generiche, mantenendo la relazione tra i tipi di input e output:

```python
from typing import TypeVar

T = TypeVar("T")

def primo_elemento(lista: list[T]) -> T:
    return lista[0]

# Il type checker deduce che `risultato` e `str`
risultato = primo_elemento(["ciao", "mondo"])

# Il type checker deduce che `numero` e `int`
numero = primo_elemento([1, 2, 3])
```

#### TypeVar con bound

Il parametro `bound` limita il TypeVar a un tipo specifico o ai suoi sottotipi:

```python
from typing import TypeVar

class Animale:
    nome: str

class Cane(Animale):
    razza: str

class Gatto(Animale):
    indoor: bool

A = TypeVar("A", bound=Animale)

def nome_animale(animale: A) -> str:
    return animale.nome  # OK: `nome` esiste in Animale e tutti i suoi sottotipi

nome_animale(Cane())   # OK
nome_animale(Gatto())  # OK
nome_animale("testo")  # Errore: str non e sottotipo di Animale
```

#### TypeVar con constraints

Le constraints specificano un insieme finito di tipi ammessi (diverso da `Union` perche il tipo viene "fissato" a uno dei tipi ammessi per ogni invocazione):

```python
from typing import TypeVar

NumeroT = TypeVar("NumeroT", int, float)

def doppio(valore: NumeroT) -> NumeroT:
    return valore * 2

doppio(5)     # Restituisce int
doppio(3.14)  # Restituisce float
doppio("ab")  # Errore: str non e tra i tipi ammessi
```

La differenza rispetto a `Union[int, float]` e sottile ma importante: con `TypeVar`, se il parametro e `int`, il tipo di ritorno e garantito essere `int` (non `int | float`).

#### Sintassi Python 3.12+ (PEP 695)

Da Python 3.12, i generici possono essere definiti direttamente nella firma della funzione o della classe, senza creare `TypeVar` separatamente:

```python
# Python 3.12+: non serve piu creare TypeVar separatamente
def primo_elemento[T](lista: list[T]) -> T:
    return lista[0]

class Contenitore[T]:
    def __init__(self, valore: T) -> None:
        self.valore = valore

    def ottieni(self) -> T:
        return self.valore
```

#### Bound e constraints con PEP 695

La sintassi PEP 695 supporta anche bound e constraints inline:

```python
# Bound inline
def nome_animale[A: Animale](animale: A) -> str:
    return animale.nome

# Constraints inline
def doppio[N: (int, float)](valore: N) -> N:
    return valore * 2

# Type alias con generici
type Lista[T] = list[T]
type Risultato[T, E] = T | E

# Classe generica con bound
class Cache[K: str, V]:
    def __init__(self) -> None:
        self._dati: dict[K, V] = {}

    def ottieni(self, chiave: K) -> V | None:
        return self._dati.get(chiave)

    def imposta(self, chiave: K, valore: V) -> None:
        self._dati[chiave] = valore
```

### PEP 695 — Approfondimento: la dichiarazione `type`

Il PEP 695, introdotto in Python 3.12, non si limita a semplificare la sintassi dei generici. Introduce un cambiamento fondamentale nella filosofia del sistema di tipi Python: i parametri di tipo diventano costrutti **nativi del linguaggio** invece di oggetti creati a runtime tramite chiamate a factory.

#### Valutazione lazy degli alias di tipo

Un aspetto cruciale della dichiarazione `type` e che il lato destro viene valutato in modo **lazy** (differito). Questo significa che l'espressione del tipo non viene eseguita al momento dell'import, ma solo quando il type checker o il runtime ne hanno effettivamente bisogno. Questo risolve automaticamente il problema delle forward references negli alias:

```python
# Python 3.12+: valutazione lazy, nessun problema di ordine
type Albero[T] = Nodo[T] | Foglia[T]  # OK anche se Nodo e Foglia non esistono ancora

class Nodo[T]:
    def __init__(self, valore: T, sinistro: Albero[T], destro: Albero[T]) -> None:
        self.valore = valore
        self.sinistro = sinistro
        self.destro = destro

class Foglia[T]:
    def __init__(self, valore: T) -> None:
        self.valore = valore

# Prima di PEP 695: richiedeva stringhe o __future__ annotations
from typing import TypeAlias, TypeVar, Union
T = TypeVar("T")
Albero: TypeAlias = "Union[Nodo[T], Foglia[T]]"  # Stringa obbligatoria
```

#### Alias di tipo ricorsivi

La valutazione lazy consente di definire **tipi ricorsivi** in modo naturale, cosa che era problematica con la vecchia sintassi:

```python
# Struttura JSON ricorsiva — Python 3.12+
type ValoreJSON = str | int | float | bool | None | list[ValoreJSON] | dict[str, ValoreJSON]

def valida_json(valore: ValoreJSON) -> bool:
    """Verifica che un valore sia conforme alla struttura JSON."""
    if isinstance(valore, (str, int, float, bool, type(None))):
        return True
    if isinstance(valore, list):
        return all(valida_json(elem) for elem in valore)
    if isinstance(valore, dict):
        return all(
            isinstance(k, str) and valida_json(v)
            for k, v in valore.items()
        )
    return False
```

#### Scope dei parametri di tipo

I parametri di tipo dichiarati con la sintassi PEP 695 hanno uno **scope lessicale** limitato alla funzione, classe o alias in cui sono definiti. Questo previene collisioni di nome tra TypeVar diversi:

```python
# Ogni T e indipendente: non c'e conflitto
def identita[T](x: T) -> T:
    return x

def duplica[T](x: T) -> tuple[T, T]:
    return (x, x)

class Contenitore[T]:
    # Questo T e diverso dal T delle funzioni sopra
    def __init__(self, valore: T) -> None:
        self.valore = valore

# Con la vecchia sintassi, lo stesso TypeVar era condiviso (potenziale confusione)
# T = TypeVar("T")
# def identita(x: T) -> T: ...    # Usa lo stesso T!
# def duplica(x: T) -> tuple[T, T]: ...  # Possibile confusione
```

#### Migrazione dalla vecchia alla nuova sintassi

La transizione e meccanica ma richiede attenzione ad alcuni dettagli:

```python
# ─── PRIMA (Python <3.12) ───
from typing import TypeVar, Generic, TypeAlias

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

MioAlias: TypeAlias = dict[str, list[int]]

class MiaClasse(Generic[T]):
    def metodo(self) -> T: ...

def mia_funzione(x: T) -> list[T]: ...

# ─── DOPO (Python 3.12+) ───
type MioAlias = dict[str, list[int]]

class MiaClasse[T]:
    def metodo(self) -> T: ...

def mia_funzione[T](x: T) -> list[T]: ...

# ─── NOTA: varianza esplicita non e piu necessaria ───
# Prima: T_co = TypeVar("T_co", covariant=True)
# Dopo: la varianza viene inferita automaticamente dai type checker
```

### PEP 696 — Valori predefiniti per i parametri di tipo (Python 3.13+)

Il PEP 696 introduce la possibilita di specificare **valori predefiniti** per `TypeVar`, `ParamSpec` e `TypeVarTuple`. Quando il parametro di tipo non viene specificato esplicitamente dall'utente, il type checker utilizza il valore predefinito.

#### Motivazione

Molte classi generiche nella libreria standard e in librerie di terze parti hanno parametri di tipo che nella grande maggioranza dei casi vengono utilizzati con lo stesso tipo. Obbligare l'utente a specificarli ogni volta aggiunge boilerplate senza aggiungere informazione. Con PEP 696, i casi comuni diventano concisi e i casi speciali restano espliciti.

#### Sintassi e uso pratico

```python
# Python 3.13+ — sintassi con PEP 695
class Risposta[T = dict[str, object]]:
    """Container generico per risposte.
    Default: dict[str, object] (struttura JSON tipica).
    """
    def __init__(self, dati: T, status: int = 200) -> None:
        self.dati = dati
        self.status = status

# Senza specificare il tipo: T = dict[str, object] (il default)
r1 = Risposta({"nome": "Mario"})  # Risposta[dict[str, object]]

# Con tipo esplicito: sovrascrive il default
r2 = Risposta[list[int]]([1, 2, 3])  # Risposta[list[int]]

# Vecchia sintassi equivalente (compatibile con Python <3.13 via typing_extensions)
from typing import TypeVar
T = TypeVar("T", default=dict[str, object])
```

#### Casi d'uso pratici

**1. Generator con default per SendType e ReturnType:**

```python
# Nella maggior parte dei generatori, SendType e None e ReturnType e None
class MioGeneratore[YieldT, SendT = None, ReturnT = None]:
    """Generatore tipizzato con default sensati."""
    ...

# Uso semplificato: basta specificare il tipo di yield
gen: MioGeneratore[int] = ...  # SendT=None, ReturnT=None (impliciti)

# Uso completo quando necessario
gen2: MioGeneratore[int, str, bool] = ...  # Tutti specificati
```

**2. Event handler con firma predefinita:**

```python
from typing import ParamSpec

# Python 3.13+
class EventoHandler[P: ParamSpec = [str, int]]:
    """Handler di eventi con firma predefinita (nome: str, priorita: int)."""
    def __init__(self, callback: Callable[P, None]) -> None:
        self._callback = callback

# Il tipo predefinito e Callable[[str, int], None]
handler = EventoHandler(lambda nome, priorita: print(f"{nome}: {priorita}"))
```

**3. Contenitore con tipo di errore predefinito:**

```python
class Risultato[T, E = Exception]:
    """Tipo Result con errore predefinito Exception."""
    def __init__(self, valore: T | None = None, errore: E | None = None) -> None:
        self._valore = valore
        self._errore = errore

    def e_ok(self) -> bool:
        return self._errore is None

# Uso comune: errore generico Exception
r: Risultato[int] = Risultato(valore=42)

# Uso con errore specifico
r2: Risultato[int, ValueError] = Risultato(errore=ValueError("negativo"))
```

#### Compatibilita con `typing_extensions`

Per usare PEP 696 su Python 3.12 e precedenti:

```python
from typing_extensions import TypeVar

T = TypeVar("T", default=int)

# Supportato da pyright e da mypy 1.10+
# typing_extensions >= 4.4.0
```

### PEP 698 — Il decoratore `@override` (Python 3.12+)

Il PEP 698 introduce il decoratore `@override` nel modulo `typing`, progettato per prevenire una classe insidiosa di bug: i metodi che **credono** di sovrascrivere un metodo della classe base ma in realta non lo fanno (ad esempio per un errore di battitura nel nome del metodo o un cambiamento nella classe base).

#### Il problema

Senza `@override`, un errore di battitura nel nome di un metodo sovrascritto passa completamente inosservato — il codice compila e viene eseguito, ma il metodo della classe base continua a essere invocato al posto di quello "sovrascritto":

```python
class Animale:
    def emetti_suono(self) -> str:
        return "..."

class Cane(Animale):
    def emmetti_suono(self) -> str:  # Typo! Dovrebbe essere emetti_suono
        return "Bau!"

# Nessun errore a runtime, ma il metodo giusto non viene mai chiamato
rex = Cane()
print(rex.emetti_suono())  # Stampa "..." invece di "Bau!"
```

#### La soluzione con `@override`

```python
from typing import override

class Animale:
    def emetti_suono(self) -> str:
        return "..."

    def descrizione(self) -> str:
        return "Un animale generico"

class Cane(Animale):
    @override
    def emetti_suono(self) -> str:
        return "Bau!"

    @override
    def emmetti_suono(self) -> str:  # Errore mypy/pyright!
        # error: Method "emmetti_suono" is marked as an override
        # but no base method was found with that name
        return "Bau!"
```

Il type checker segnala immediatamente che `emmetti_suono` non corrisponde ad alcun metodo nella gerarchia delle classi base.

#### Uso con proprieta, staticmethod e classmethod

`@override` funziona con tutti i tipi di metodo:

```python
from typing import override

class Base:
    @property
    def nome(self) -> str:
        return "Base"

    @classmethod
    def crea(cls) -> "Base":
        return cls()

    @staticmethod
    def versione() -> str:
        return "1.0"

class Derivata(Base):
    @property
    @override
    def nome(self) -> str:
        return "Derivata"

    @classmethod
    @override
    def crea(cls) -> "Derivata":
        return cls()

    @staticmethod
    @override
    def versione() -> str:
        return "2.0"
```

#### Protezione durante il refactoring

Il beneficio principale di `@override` emerge durante il refactoring. Se la classe base rinomina un metodo, tutti i sottotipi con `@override` vengono segnalati immediatamente dal type checker:

```python
class Repository:
    def trova_tutti(self) -> list[object]:  # Rinominato da "lista_tutti"
        return []

class UtenteRepo(Repository):
    @override
    def lista_tutti(self) -> list[object]:  # Errore: "lista_tutti" non esiste piu in Repository
        return [...]

# Senza @override, questo bug sarebbe rimasto silenzioso
```

#### Backporting con typing_extensions

Per Python 3.11 e precedenti:

```python
from typing_extensions import override  # typing_extensions >= 4.4.0
```

### Classi generiche

Una classe generica e parametrizzata da uno o piu `TypeVar`:

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Pila(Generic[T]):
    def __init__(self) -> None:
        self._elementi: list[T] = []

    def push(self, elemento: T) -> None:
        self._elementi.append(elemento)

    def pop(self) -> T:
        if not self._elementi:
            raise IndexError("La pila e vuota")
        return self._elementi.pop()

    def vuota(self) -> bool:
        return len(self._elementi) == 0

    def __len__(self) -> int:
        return len(self._elementi)

# Uso
pila_interi: Pila[int] = Pila()
pila_interi.push(42)
pila_interi.push("testo")  # Errore mypy

pila_stringhe: Pila[str] = Pila()
pila_stringhe.push("ciao")
```

Per classi con piu parametri di tipo:

```python
from typing import TypeVar, Generic

K = TypeVar("K")
V = TypeVar("V")

class Coppia(Generic[K, V]):
    def __init__(self, chiave: K, valore: V) -> None:
        self.chiave = chiave
        self.valore = valore

    def scambia(self) -> "Coppia[V, K]":
        return Coppia(self.valore, self.chiave)
```

#### Classi generiche con metodi di fabbrica

Un pattern comune e la combinazione di generici con `classmethod`:

```python
from typing import TypeVar, Generic, Self
import json

T = TypeVar("T")

class Risultato(Generic[T]):
    """Container per operazioni che possono fallire."""

    def __init__(self, valore: T | None, errore: str | None = None) -> None:
        self._valore = valore
        self._errore = errore

    @classmethod
    def successo(cls, valore: T) -> "Risultato[T]":
        return cls(valore=valore)

    @classmethod
    def fallimento(cls, errore: str) -> "Risultato[T]":
        return cls(valore=None, errore=errore)

    def e_ok(self) -> bool:
        return self._errore is None

    def valore_o_default(self, default: T) -> T:
        if self._valore is not None:
            return self._valore
        return default

    def mappa(self, func: "Callable[[T], V]") -> "Risultato[V]":
        """Trasforma il valore contenuto, se presente."""
        if self._valore is not None:
            try:
                return Risultato.successo(func(self._valore))
            except Exception as e:
                return Risultato.fallimento(str(e))
        return Risultato.fallimento(self._errore or "Nessun valore")

V = TypeVar("V")

# Uso
r1: Risultato[int] = Risultato.successo(42)
r2: Risultato[str] = r1.mappa(str)  # Risultato[str]
r3: Risultato[int] = Risultato.fallimento("errore di rete")
```

### Covarianza e controvarianza

La varianza descrive come le relazioni di sottotipo tra tipi generici si rapportano alle relazioni di sottotipo dei loro parametri:

```python
from typing import TypeVar, Generic

# Covariante: se Cane <: Animale, allora Sorgente[Cane] <: Sorgente[Animale]
# Usato per tipi "produttori" (sola lettura)
T_co = TypeVar("T_co", covariant=True)

class SorgenteReadOnly(Generic[T_co]):
    def __init__(self, valore: T_co) -> None:
        self._valore = valore

    def leggi(self) -> T_co:
        return self._valore

# Controvariante: se Cane <: Animale, allora Handler[Animale] <: Handler[Cane]
# Usato per tipi "consumatori" (sola scrittura)
T_contra = TypeVar("T_contra", contravariant=True)

class Handler(Generic[T_contra]):
    def gestisci(self, valore: T_contra) -> None:
        ...

# Invariante (default): nessuna relazione di sottotipo
T = TypeVar("T")  # invariante per default
```

**Regola pratica per la varianza:**

| Ruolo del tipo | Varianza | Esempio stdlib |
|---------------|----------|----------------|
| Solo produttore (output) | Covariante | `Iterator[T_co]`, `Sequence[T_co]` |
| Solo consumatore (input) | Controvariante | `Callable[..., T_contra]` (parametri) |
| Sia input che output | Invariante | `list[T]`, `dict[K, V]` |

```python
# Perche list e invariante:
class Animale: ...
class Cane(Animale): ...

def aggiungi_animale(animali: list[Animale]) -> None:
    animali.append(Animale())  # Lecito per list[Animale]

cani: list[Cane] = [Cane()]
# Se list fosse covariante, questo sarebbe permesso:
# aggiungi_animale(cani)  # Ma inserirebbe un Animale generico in una lista di Cani!
# Per questo list e invariante: list[Cane] NON e sottotipo di list[Animale]
```

### ParamSpec (Python 3.10+, PEP 612)

`ParamSpec` cattura l'intera **firma dei parametri** di una callable, fondamentale per annotare correttamente i decoratori:

```python
from typing import ParamSpec, TypeVar, Callable
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

def log_chiamata(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Chiamo {func.__name__}")
        risultato = func(*args, **kwargs)
        print(f"{func.__name__} ha restituito {risultato}")
        return risultato
    return wrapper

@log_chiamata
def somma(a: int, b: int) -> int:
    return a + b

# Il type checker sa che `somma` accetta (int, int) -> int
somma(1, 2)       # OK
somma("a", "b")   # Errore mypy
```

#### Concatenate: aggiungere parametri alla firma

`Concatenate` (PEP 612) permette di descrivere decoratori che aggiungono parametri alla firma della funzione decorata:

```python
from typing import Callable, Concatenate, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def con_contesto(
    func: Callable[Concatenate[str, P], R],
) -> Callable[P, R]:
    """Decoratore che inietta un contesto come primo argomento."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        contesto = "contesto_applicazione"
        return func(contesto, *args, **kwargs)
    return wrapper

@con_contesto
def salva_dato(ctx: str, chiave: str, valore: int) -> bool:
    print(f"[{ctx}] Salvo {chiave}={valore}")
    return True

# La firma visibile e (chiave: str, valore: int) -> bool
salva_dato("nome", 42)      # OK
salva_dato("ctx", "nome", 42)  # Errore: troppi argomenti
```

Uso tipico: dependency injection, middleware, autenticazione:

```python
from typing import Callable, Concatenate, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

class UtenteAutenticato:
    def __init__(self, user_id: int, ruolo: str) -> None:
        self.user_id = user_id
        self.ruolo = ruolo

def richiede_autenticazione(
    func: Callable[Concatenate[UtenteAutenticato, P], R],
) -> Callable[P, R]:
    """Inietta l'utente autenticato come primo parametro."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        utente = _ottieni_utente_corrente()  # Da sessione/token
        return func(utente, *args, **kwargs)
    return wrapper

@richiede_autenticazione
def elimina_risorsa(utente: UtenteAutenticato, risorsa_id: int) -> bool:
    if utente.ruolo != "admin":
        raise PermissionError("Solo admin")
    # ... eliminazione
    return True

# La firma visibile e (risorsa_id: int) -> bool
elimina_risorsa(42)  # OK: utente iniettato automaticamente
```

### TypeVarTuple (Python 3.11+, PEP 646)

`TypeVarTuple` cattura un numero variabile di tipi, utile per funzioni che operano su tuple di lunghezza arbitraria:

```python
from typing import TypeVarTuple, Unpack

Ts = TypeVarTuple("Ts")

def prima_e_resto(tup: tuple[int, *Ts]) -> tuple[int, tuple[*Ts]]:
    return tup[0], tup[1:]

# Python 3.12+
def prima_e_resto[*Ts](tup: tuple[int, *Ts]) -> tuple[int, tuple[*Ts]]:
    return tup[0], tup[1:]
```

### Pattern avanzati con generici variadici (TypeVarTuple)

`TypeVarTuple` (PEP 646) apre possibilita di typing prima impossibili in Python. Il caso d'uso principale e la tipizzazione di operazioni su array multidimensionali e pipeline di trasformazione dati.

#### Funzioni su strutture dati multidimensionali

```python
# Python 3.12+
def trasponi[*Shape](matrice: "Array[*Shape]") -> "Array[*reversed(Shape)]":
    """Tipo concettuale: trasporre le dimensioni di un array."""
    ...

# Uso pratico: preservare la struttura delle tuple
def aggiungi_dimensione[*Ts](dati: tuple[*Ts]) -> tuple[int, *Ts]:
    """Aggiunge una dimensione in testa alla tupla."""
    return (0, *dati)

# Il type checker traccia le dimensioni esatte
r1 = aggiungi_dimensione((1.0, "ciao"))       # tuple[int, float, str]
r2 = aggiungi_dimensione((True, 42, "test"))   # tuple[int, bool, int, str]
```

#### Pipeline tipizzate con composizione

```python
from typing import Callable

def componi[A, B, C](
    f: Callable[[A], B],
    g: Callable[[B], C],
) -> Callable[[A], C]:
    """Componi due funzioni preservando i tipi."""
    def composta(x: A) -> C:
        return g(f(x))
    return composta

# Il type checker traccia la catena di trasformazioni
str_to_int = componi(str.strip, int)     # Callable[[str], int]
int_to_hex = componi(int, hex)           # Callable[[int], str]
```

### ParamSpec: approfondimento e pattern avanzati

Oltre all'uso base nei decoratori, `ParamSpec` abilita pattern sofisticati per la composizione di funzioni e la dependency injection.

#### Decoratore con trasformazione asincrona

```python
import asyncio
from typing import ParamSpec, TypeVar, Callable, Awaitable
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

def rendi_asincrono(func: Callable[P, R]) -> Callable[P, Awaitable[R]]:
    """Trasforma una funzione sincrona in asincrona preservando la firma."""
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper

@rendi_asincrono
def calcolo_pesante(n: int, precisione: float = 0.001) -> float:
    return sum(1.0 / i for i in range(1, n + 1))

# Il type checker sa che calcolo_pesante ha firma:
# (n: int, precisione: float = 0.001) -> Awaitable[float]
```

#### Factory di callback type-safe

```python
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec("P")
R = TypeVar("R")

class RegistroCallback[P: ParamSpec, R]:
    """Registro type-safe per callback con firma specifica."""

    def __init__(self) -> None:
        self._callbacks: list[Callable[P, R]] = []

    def registra(self, callback: Callable[P, R]) -> None:
        self._callbacks.append(callback)

    def esegui_tutti(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        return [cb(*args, **kwargs) for cb in self._callbacks]

# Uso
registro: RegistroCallback[[str, int], bool] = RegistroCallback()
registro.registra(lambda nome, eta: eta >= 18)
registro.registra(lambda nome, eta: len(nome) > 0)

risultati = registro.esegui_tutti("Mario", 30)  # list[bool]
```

### Protocol (structural subtyping, PEP 544)

`Protocol` definisce un'interfaccia strutturale: un tipo e compatibile se possiede i metodi e gli attributi richiesti, **indipendentemente dalla gerarchia di ereditarieta** (duck typing statico):

```python
from typing import Protocol

class Leggibile(Protocol):
    def leggi(self) -> str:
        ...

class FileLocale:
    def leggi(self) -> str:
        return "contenuto del file"

class RispostaHTTP:
    def leggi(self) -> str:
        return "corpo della risposta"

def elabora(sorgente: Leggibile) -> None:
    contenuto = sorgente.leggi()
    print(contenuto)

elabora(FileLocale())     # OK: ha il metodo `leggi`
elabora(RispostaHTTP())   # OK: ha il metodo `leggi`
elabora("stringa")        # Errore: str non ha il metodo `leggi`
```

I Protocol possono anche specificare attributi e composizione tra interfacce:

```python
from typing import Protocol, runtime_checkable

class Scrivibile(Protocol):
    def scrivi(self, dati: str) -> int:
        ...

class Chiudibile(Protocol):
    def chiudi(self) -> None:
        ...

# Composizione di Protocol
class StreamOutput(Scrivibile, Chiudibile, Protocol):
    pass

@runtime_checkable
class Dimensionabile(Protocol):
    larghezza: float
    altezza: float

class Rettangolo:
    def __init__(self, larghezza: float, altezza: float) -> None:
        self.larghezza = larghezza
        self.altezza = altezza

# Con @runtime_checkable, funziona anche isinstance()
r = Rettangolo(5, 3)
print(isinstance(r, Dimensionabile))  # True
```

**Nota**: il controllo a runtime con `@runtime_checkable` verifica solo la **presenza** dei metodi e degli attributi, non le loro firme o i tipi dei parametri.

#### Protocol generici

I Protocol possono essere parametrizzati con `TypeVar` per definire interfacce generiche:

```python
from typing import Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)

class Repository(Protocol[T_co]):
    def trova_per_id(self, id: int) -> T_co | None: ...
    def trova_tutti(self) -> list[T_co]: ...

class Utente:
    def __init__(self, id: int, nome: str) -> None:
        self.id = id
        self.nome = nome

class UtenteRepo:
    """Non eredita da Repository, ma soddisfa il Protocol."""
    def trova_per_id(self, id: int) -> Utente | None:
        return None  # implementazione

    def trova_tutti(self) -> list[Utente]:
        return []

def conta_entita(repo: Repository[Utente]) -> int:
    return len(repo.trova_tutti())

conta_entita(UtenteRepo())  # OK: soddisfa il Protocol strutturalmente
```

#### Confronto con ABC

| Aspetto | ABC | Protocol |
|---------|-----|----------|
| Tipo di subtyping | Nominale (ereditarieta esplicita) | Strutturale (duck typing) |
| Richiede ereditarieta | Si | No |
| Metodi astratti | `@abstractmethod` | Metodi con `...` nel body |
| Controllo runtime | `isinstance()` nativo | Solo con `@runtime_checkable` |
| Utilizzo tipico | Gerarchie di classi formali | Interfacce leggere, interoperabilita |

### Callable

`Callable` descrive il tipo di un oggetto invocabile (funzione, metodo, lambda, classe con `__call__`):

```python
from typing import Callable

# Callable[[TipiParametri], TipoRitorno]
def applica(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

risultato = applica(lambda x, y: x + y, 3, 4)  # 7

# Funzione senza parametri
GeneratoreID = Callable[[], str]

# Callable con qualsiasi firma (meno preciso)
from typing import Any
QualsiasiFunzione = Callable[..., Any]
```

### Overload

`@overload` permette di definire piu firme per una stessa funzione, consentendo al type checker di determinare il tipo di ritorno in base ai tipi degli argomenti:

```python
from typing import overload, Literal

@overload
def processa(dato: str) -> list[str]: ...
@overload
def processa(dato: int) -> list[int]: ...
@overload
def processa(dato: list[str]) -> str: ...

def processa(dato: str | int | list[str]) -> list[str] | list[int] | str:
    if isinstance(dato, str):
        return dato.split()
    elif isinstance(dato, int):
        return list(range(dato))
    else:
        return " ".join(dato)

# Il type checker conosce il tipo esatto del risultato
parole = processa("ciao mondo")       # list[str]
numeri = processa(5)                   # list[int]
frase = processa(["ciao", "mondo"])   # str
```

Le firme `@overload` esistono solo per il type checker; a runtime viene eseguita esclusivamente l'implementazione finale (senza decoratore `@overload`).

Esempio avanzato con `Literal`:

```python
@overload
def leggi_config(chiave: str, tipo: Literal["str"]) -> str: ...
@overload
def leggi_config(chiave: str, tipo: Literal["int"]) -> int: ...
@overload
def leggi_config(chiave: str, tipo: Literal["bool"]) -> bool: ...

def leggi_config(chiave: str, tipo: str) -> str | int | bool:
    valore_grezzo = _config[chiave]
    if tipo == "str":
        return str(valore_grezzo)
    elif tipo == "int":
        return int(valore_grezzo)
    elif tipo == "bool":
        return valore_grezzo.lower() in ("true", "1", "si")
    raise ValueError(f"Tipo non supportato: {tipo}")

# mypy inferisce i tipi di ritorno corretti
nome: str = leggi_config("app_name", "str")    # OK
porta: int = leggi_config("port", "int")        # OK
debug: bool = leggi_config("debug", "bool")     # OK
```

### TypeGuard e TypeIs

`TypeGuard` (Python 3.10+) e `TypeIs` (Python 3.13+) permettono di creare **funzioni di narrowing personalizzate** che informano il type checker sul tipo effettivo di una variabile dopo un controllo:

```python
from typing import TypeGuard

def e_lista_stringhe(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(elem, str) for elem in val)

def elabora(dati: list[object]) -> None:
    if e_lista_stringhe(dati):
        # Qui il type checker sa che `dati` e list[str]
        for s in dati:
            print(s.upper())  # OK: s e str
```

`TypeIs` (PEP 742, Python 3.13+) e una versione migliorata di `TypeGuard` con semantica piu precisa. La differenza principale e che `TypeIs[X]` effettua il narrowing in **entrambi i rami** (if e else), mentre `TypeGuard[X]` lo fa solo nel ramo `if`:

```python
from typing import TypeIs

def e_stringa(val: str | int) -> TypeIs[str]:
    return isinstance(val, str)

def elabora(valore: str | int) -> None:
    if e_stringa(valore):
        # valore e str
        print(valore.upper())
    else:
        # valore e int (narrowing anche nel ramo else!)
        print(valore + 1)
```

#### TypeGuard vs TypeIs: quando usare quale

| Aspetto | `TypeGuard` (PEP 647) | `TypeIs` (PEP 742) |
|---------|----------------------|-------------------|
| Narrowing nel ramo `if` | Si | Si |
| Narrowing nel ramo `else` | No | Si |
| Tipo di input e output | Possono essere scorrelati | Output deve essere sottotipo dell'input |
| Disponibile da | Python 3.10 | Python 3.13 |
| Caso d'uso tipico | Narrowing "largo" (es. `object` -> `list[str]`) | Narrowing "stretto" (es. `str | int` -> `str`) |

```python
# TypeGuard: utile quando il tipo risultante NON e sottotipo del tipo di input
def e_dati_validi(raw: object) -> TypeGuard[dict[str, list[int]]]:
    """Verifica una struttura complessa da JSON."""
    if not isinstance(raw, dict):
        return False
    return all(
        isinstance(k, str) and isinstance(v, list) and all(isinstance(i, int) for i in v)
        for k, v in raw.items()
    )

# TypeIs: preferibile quando il tipo e gia nell'union
def e_numero(val: str | int | float) -> TypeIs[int | float]:
    return isinstance(val, (int, float))
```

### NewType

`NewType` crea un tipo distinto che e un sottotipo del tipo base. E utile per differenziare semanticamente valori che hanno lo stesso tipo sottostante:

```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def ottieni_ordine(user_id: UserId, order_id: OrderId) -> dict:
    ...

uid = UserId(42)
oid = OrderId(100)

ottieni_ordine(uid, oid)  # OK
ottieni_ordine(oid, uid)  # Errore mypy: argomenti invertiti!
ottieni_ordine(42, 100)   # Errore mypy: int non e UserId/OrderId
```

A runtime, `NewType` e semplicemente una funzione identita (nessun overhead), ma per il type checker `UserId` e `OrderId` sono tipi distinti e incompatibili tra loro.

### TypedDict

`TypedDict` definisce un dizionario con chiavi specifiche, ciascuna con il proprio tipo:

```python
from typing import TypedDict, NotRequired

class Indirizzo(TypedDict):
    via: str
    citta: str
    cap: str
    provincia: NotRequired[str]  # Chiave opzionale (Python 3.11+)

class Persona(TypedDict):
    nome: str
    eta: int
    indirizzo: Indirizzo

# Uso
mario: Persona = {
    "nome": "Mario Rossi",
    "eta": 30,
    "indirizzo": {
        "via": "Via Roma 1",
        "citta": "Milano",
        "cap": "20100",
    }
}

mario["nome"]       # str
mario["cognome"]    # Errore mypy: chiave non definita
mario["eta"] = "30" # Errore mypy: deve essere int
```

Si puo anche usare la forma funzionale per chiavi che non sono identificatori Python validi:

```python
Risposta = TypedDict("Risposta", {
    "status-code": int,
    "content-type": str,
    "body": str,
})
```

Ereditarieta tra TypedDict:

```python
class UtenteBase(TypedDict):
    nome: str
    email: str

class UtenteCompleto(UtenteBase):
    ruolo: str
    attivo: bool
```

### NamedTuple

`NamedTuple` fornisce una versione tipizzata delle named tuple:

```python
from typing import NamedTuple

class Punto(NamedTuple):
    x: float
    y: float
    z: float = 0.0  # Valore predefinito

p = Punto(1.0, 2.0)
print(p.x, p.y, p.z)  # 1.0 2.0 0.0

# E immutabile come una tuple
p.x = 5.0  # Errore a runtime (e segnalato da mypy)

# Supporta unpacking
x, y, z = p
```

---

## Mypy

### Configurazione

#### Installazione

```bash
pip install mypy

# Oppure con extra per framework specifici
pip install mypy[reports]

# Plugin comuni
pip install django-stubs          # Per Django
pip install sqlalchemy-stubs      # Per SQLAlchemy (versioni precedenti)
pip install pydantic              # Pydantic include il plugin mypy

# Verifica installazione
mypy --version
```

#### File di configurazione

Mypy supporta tre formati di configurazione. Il formato consigliato per nuovi progetti e `pyproject.toml`:

**pyproject.toml** (consigliato):

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_unreachable = true
show_error_codes = true
pretty = true

# Configurazione per modulo
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "libreria_senza_tipi.*"
ignore_missing_imports = true
```

**mypy.ini** (formato classico):

```ini
[mypy]
python_version = 3.12
strict = True
warn_return_any = True
show_error_codes = True
pretty = True

[mypy-tests.*]
disallow_untyped_defs = False

[mypy-libreria_senza_tipi.*]
ignore_missing_imports = True
```

**setup.cfg**:

```ini
[mypy]
python_version = 3.12
strict = True
```

#### Impostazioni chiave

| Impostazione | Descrizione |
|-------------|-------------|
| `strict` | Attiva tutte le opzioni di rigore (consigliato per nuovi progetti) |
| `disallow_untyped_defs` | Richiede annotazioni per tutte le funzioni |
| `disallow_incomplete_defs` | Errore se solo alcuni parametri sono annotati |
| `check_untyped_defs` | Controlla anche il corpo delle funzioni senza annotazioni |
| `ignore_missing_imports` | Ignora gli import di moduli senza stubs |
| `warn_return_any` | Avvisa se una funzione annotata restituisce `Any` |
| `warn_redundant_casts` | Avvisa se un cast e superfluo |
| `warn_unused_ignores` | Avvisa se un `# type: ignore` non e necessario |
| `warn_unreachable` | Avvisa se del codice non e raggiungibile |
| `no_implicit_optional` | `def f(x: int = None)` richiede `int | None` esplicito |
| `show_error_codes` | Mostra il codice errore (es. `[assignment]`, `[arg-type]`) |
| `pretty` | Formattazione piu leggibile dell'output |
| `plugins` | Lista di plugin mypy (es. `pydantic.mypy`, `sqlmypy`) |

#### Cosa attiva `strict`

L'opzione `strict = true` e un'abbreviazione che attiva simultaneamente molti flag. E utile sapere cosa include:

```toml
# strict = true equivale a tutti questi flag contemporaneamente:
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
no_implicit_reexport = true
strict_equality = true
extra_checks = true  # aggiunto in mypy 1.0+
```

Si puo attivare `strict` e poi rilassare singoli flag dove necessario:

```toml
[tool.mypy]
strict = true

# Permetti decoratori non annotati (utile con librerie legacy)
disallow_untyped_decorators = false
```

#### Configurazione per modulo

La configurazione per modulo e particolarmente utile durante l'adozione incrementale dei type hints:

```toml
# Moduli legacy: controllo rilassato
[[tool.mypy.overrides]]
module = "vecchio_modulo.*"
disallow_untyped_defs = false
ignore_errors = true

# Librerie esterne senza stubs
[[tool.mypy.overrides]]
module = ["requests.*", "pandas.*"]
ignore_missing_imports = true

# Moduli critici: controllo massimo
[[tool.mypy.overrides]]
module = "core.sicurezza.*"
disallow_any_explicit = true
disallow_any_generics = true
```

#### Plugin

Mypy supporta plugin che forniscono supporto specifico per framework popolari:

```toml
[tool.mypy]
plugins = [
    "pydantic.mypy",
    "mypy_django_plugin.main",
    "sqlalchemy.ext.mypy.plugin",
]

# Configurazione plugin Pydantic
[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true

# Configurazione plugin Django
[tool.django-stubs]
django_settings_module = "mio_progetto.settings"
```

### Uso Pratico

#### Esecuzione di mypy

```bash
# Controlla un singolo file
mypy script.py

# Controlla un intero pacchetto
mypy src/mio_progetto/

# Controlla piu percorsi
mypy src/ tests/

# Controlla con configurazione specifica
mypy --config-file pyproject.toml src/

# Modalita strict
mypy --strict src/

# Mostra il contesto dell'errore
mypy --show-error-context --pretty src/
```

#### Mypy Daemon (dmypy)

Il daemon mypy (`dmypy`) mantiene un processo in background con lo stato del progetto in memoria. Le analisi successive diventano incrementali e molto piu veloci:

```bash
# Avviare il daemon
dmypy start

# Eseguire il check (usa il daemon se disponibile)
dmypy run -- src/

# Controllare un singolo file (molto veloce dopo il primo run)
dmypy check src/modulo.py

# Verificare lo stato del daemon
dmypy status

# Fermare il daemon
dmypy stop

# Riavviare (utile dopo aggiornamento mypy o cambio config)
dmypy restart
```

Confronto prestazioni su un progetto medio (~500 file):

| Operazione | mypy (cold) | mypy (warm, cache disco) | dmypy (warm) |
|-----------|-------------|--------------------------|--------------|
| Prima esecuzione | ~15s | ~15s | ~15s |
| Modifica 1 file | ~15s | ~5s | ~0.5s |
| Nessuna modifica | ~15s | ~3s | ~0.1s |

**Nota**: `dmypy` usa piu memoria (mantiene l'AST in RAM), ma l'accelerazione e drastica per lo sviluppo iterativo. Integrarlo con l'editor (es. tramite un wrapper in VS Code tasks) migliora significativamente il workflow.

#### Interpretare l'output

L'output di mypy segue il formato:

```
file.py:riga:colonna: livello: messaggio  [codice-errore]
```

Esempio pratico:

```
app/servizi.py:25:12: error: Argument 1 to "connetti" has
    incompatible type "str"; expected "int"  [arg-type]
app/servizi.py:40:5: error: Incompatible return value type
    (got "str", expected "int")  [return-value]
app/modelli.py:15:1: error: Function is missing a type
    annotation  [no-untyped-def]
Found 3 errors in 2 files (checked 5 source files)
```

#### Errori comuni e soluzioni

**1. Incompatible types in assignment**

```python
# Errore
x: int = "ciao"  # error: Incompatible types in assignment [assignment]

# Soluzione
x: str = "ciao"
# oppure
x: int | str = "ciao"
```

**2. Item of Optional has no attribute**

```python
# Errore
def ottieni_nome(utente: Utente | None) -> str:
    return utente.nome  # error: Item "None" of "Utente | None" has no attribute "nome"

# Soluzione: narrowing con if
def ottieni_nome(utente: Utente | None) -> str:
    if utente is None:
        return "Sconosciuto"
    return utente.nome  # OK: dopo il check, utente e Utente

# Alternativa con assert
def ottieni_nome(utente: Utente | None) -> str:
    assert utente is not None
    return utente.nome
```

**3. Missing return statement**

```python
# Errore
def classifica(valore: int) -> str:  # error: Missing return statement
    if valore > 0:
        return "positivo"
    elif valore < 0:
        return "negativo"
    # Manca il caso valore == 0!

# Soluzione
def classifica(valore: int) -> str:
    if valore > 0:
        return "positivo"
    elif valore < 0:
        return "negativo"
    else:
        return "zero"
```

**4. Cannot infer type of list**

```python
# Errore
risultati = []  # error: Need type annotation for "risultati"

# Soluzione
risultati: list[str] = []
```

**5. Incompatible return value type**

```python
# Errore
def calcola() -> int:
    return "42"  # error: Incompatible return value type (got "str", expected "int")

# Soluzione
def calcola() -> int:
    return int("42")
```

#### Commenti type: ignore

Quando e necessario silenziare un errore specifico di mypy:

```python
# Ignorare un errore specifico (consigliato)
risultato = funzione_problematica()  # type: ignore[no-untyped-call]

# Ignorare tutti gli errori sulla riga (sconsigliato)
risultato = funzione_problematica()  # type: ignore

# Con spiegazione (buona pratica)
# La libreria xyz non ha stubs e restituisce Any
dati = xyz.carica()  # type: ignore[no-any-return]

import modulo_senza_stubs  # type: ignore[import-untyped]  # stubs non disponibili
```

**Regola**: usare `# type: ignore` solo come ultima risorsa, sempre con il codice errore specifico e possibilmente con un commento che spiega il motivo.

#### reveal_type() per il debugging

`reveal_type()` e una funzione speciale riconosciuta da mypy che mostra il tipo inferito di un'espressione:

```python
x = [1, 2, 3]
reveal_type(x)  # note: Revealed type is "builtins.list[builtins.int]"

d = {"nome": "Mario", "eta": 30}
reveal_type(d)  # note: Revealed type is "builtins.dict[builtins.str, builtins.object]"

# Utile per capire cosa deduce mypy in situazioni ambigue
def misteriosa(x: int) -> None:
    y = x if x > 0 else None
    reveal_type(y)  # note: Revealed type is "builtins.int | None"
```

Non serve importare nulla per usarla con mypy. In Python 3.11+ `reveal_type` e stato aggiunto anche a runtime nel modulo `typing`, quindi funziona anche durante l'esecuzione:

```python
from typing import reveal_type  # Python 3.11+
reveal_type(42)  # Funziona a runtime, stampa il tipo
```

#### Strategia di adozione incrementale

Per introdurre i type hints in un progetto esistente senza dover annotare tutto in una volta:

**Fase 1: Configurazione minima**

```toml
[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
check_untyped_defs = true
show_error_codes = true
```

Eseguire mypy per avere una baseline degli errori.

**Fase 2: Annotare le interfacce pubbliche**

Iniziare dalle funzioni e classi pubbliche dei moduli principali, concentrandosi sulle firme delle funzioni. Usare `# type: ignore` per gli errori che non si possono correggere immediatamente.

**Fase 3: Aumentare la rigidita per modulo**

```toml
[[tool.mypy.overrides]]
module = "mio_progetto.core.*"
disallow_untyped_defs = true
warn_return_any = true
```

**Fase 4: Attivare strict sui nuovi moduli**

```toml
[[tool.mypy.overrides]]
module = "mio_progetto.nuovi_moduli.*"
strict = true
```

**Fase 5: Strict globale** (obiettivo finale)

```toml
[tool.mypy]
strict = true
```

Integrare mypy nella pipeline CI/CD per impedire regressioni.

#### Metriche di copertura dei tipi

Mypy puo generare report sulla copertura delle annotazioni:

```bash
# Report testuale su linee tipizzate vs non tipizzate
mypy --txt-report rapporti/ src/

# Report HTML interattivo
mypy --html-report rapporti/ src/

# Report in formato linecoverage (per CI)
mypy --linecount-report rapporti/ src/

# Report XML (per integrazione con strumenti CI)
mypy --xml-report rapporti/ src/
```

Il report `--linecount-report` produce un file CSV con la percentuale di linee tipizzate per ogni modulo, utile per tracciare la progressione dell'adozione nel tempo:

```
Modulo,Linee totali,Linee tipizzate,Copertura
core.auth,245,230,93.9%
core.db,180,95,52.8%
utils.helpers,120,40,33.3%
```

### Stub Files

#### File .pyi

I file stub (`.pyi`) contengono solo le annotazioni di tipo, senza implementazione. Sono utili per:

- Annotare librerie di terze parti prive di type hints.
- Separare le annotazioni dal codice di produzione.
- Fornire type hints per moduli C/C++ (extension modules).

```python
# mio_modulo.pyi
from typing import Any

def connetti(host: str, porta: int = ...) -> bool: ...
def invia(dati: bytes) -> int: ...

class Client:
    timeout: float
    def __init__(self, url: str) -> None: ...
    def richiedi(self, metodo: str, percorso: str) -> dict[str, Any]: ...
    def chiudi(self) -> None: ...
```

I puntini di sospensione (`...`) sostituiscono il corpo dell'implementazione. I valori predefiniti sono indicati semplicemente con `= ...`.

#### typeshed

[typeshed](https://github.com/python/typeshed) e il repository ufficiale che contiene gli stubs per la libreria standard di Python e per le librerie di terze parti piu diffuse. Mypy include automaticamente gli stubs di typeshed.

Per installare stubs di librerie esterne:

```bash
# Installare stubs per una libreria specifica
pip install types-requests
pip install types-PyYAML
pip install types-redis
pip install types-beautifulsoup4

# Mypy puo suggerire automaticamente stubs mancanti
mypy --install-types src/
```

#### Creare stubs personalizzati

Per creare stubs per una libreria senza annotazioni:

```bash
# Generare uno stub automatico (punto di partenza)
stubgen -p nome_libreria -o stubs/

# Generare stubs da sorgenti
stubgen percorso/al/sorgente.py

# Struttura directory degli stubs
stubs/
  nome_libreria/
    __init__.pyi
    modulo.pyi
    sotto_pacchetto/
      __init__.pyi
```

I file generati da `stubgen` spesso richiedono revisione manuale per sostituire i generici `Any` con tipi piu precisi.

Configurare mypy per trovare gli stubs personalizzati:

```toml
[tool.mypy]
mypy_path = "stubs"
```

---

## Altri Type Checker

Oltre a mypy, esistono altri strumenti di analisi statica per Python. Ciascuno ha i propri punti di forza.

### Pyright (VS Code / Pylance)

**Pyright** e il type checker sviluppato da Microsoft, scritto in TypeScript. E il motore che alimenta **Pylance**, l'estensione Python per Visual Studio Code.

**Punti di forza**:
- Estremamente veloce (ordini di grandezza piu rapido di mypy su grandi progetti).
- Eccellente inferenza dei tipi, spesso piu precisa di mypy.
- Integrazione nativa in VS Code tramite Pylance.
- Supporta rapidamente le ultime novita del linguaggio.
- Modalita `strict` molto rigorosa.

**Installazione e uso**:

```bash
pip install pyright

# Esecuzione
pyright src/
```

**Configurazione** (in `pyproject.toml` oppure `pyrightconfig.json`):

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingImports = true
reportMissingTypeStubs = false
```

```json
{
    "include": ["src"],
    "exclude": ["**/node_modules", "**/__pycache__"],
    "typeCheckingMode": "strict",
    "pythonVersion": "3.12",
    "reportMissingImports": true,
    "reportMissingTypeStubs": false
}
```

#### Pyright: flag diagnostici utili

Pyright offre controlli granulari che mypy non ha:

```json
{
    "reportUnusedVariable": "warning",
    "reportUnusedImport": "error",
    "reportDuplicateImport": "error",
    "reportMissingParameterType": "error",
    "reportUnnecessaryTypeIgnoreComment": "warning",
    "reportUnnecessaryIsInstance": "information",
    "reportShadowedImports": "error"
}
```

### Pytype (Google)

**Pytype** e il type checker sviluppato da Google, scritto in Python. Ha un approccio piu permissivo rispetto a mypy e pyright.

**Punti di forza**:
- Puo inferire i tipi anche senza annotazioni (analizza il flusso del codice).
- Piu tollerante con il codice Python idiomatico.
- Genera automaticamente file `.pyi` con `merge-pyi`.
- Utile per analizzare codebase legacy senza annotazioni.

**Installazione e uso**:

```bash
pip install pytype

# Esecuzione
pytype src/

# Generare stubs automaticamente
merge-pyi -i src/modulo.py .pytype/pyi/src/modulo.pyi
```

### Tabella comparativa

| Caratteristica | mypy | pyright | pytype |
|---------------|------|---------|--------|
| **Linguaggio** | Python | TypeScript | Python |
| **Velocita** | Media | Molto veloce | Lenta |
| **Rigidita** | Configurabile | Configurabile | Permissiva |
| **Inferenza** | Buona | Eccellente | Eccellente |
| **Integrazione IDE** | Plugin vari | VS Code (Pylance) | Limitata |
| **Generazione stubs** | `stubgen` | No | Si (`merge-pyi`) |
| **Maturita** | Alta | Alta | Media |
| **Adozione** | Standard de facto | In forte crescita | Nicchia (Google) |
| **Strict mode** | Si | Si | No |
| **Plugin** | Si (es. pydantic, django) | Limitati | No |
| **CI/CD** | Eccellente | Eccellente | Buona |
| **Supporto PEP recenti** | Buono | Eccellente | Variabile |
| **Daemon mode** | Si (`dmypy`) | No (ma persistente in IDE) | No |
| **Watch mode** | No nativo | Si (in VS Code) | No |

**Consiglio pratico**: mypy resta la scelta piu diffusa e con il miglior ecosistema di plugin. Pyright e consigliato se si usa VS Code e si desidera feedback immediato durante la scrittura del codice. Molti team li utilizzano entrambi in parallelo: pyright nell'IDE per il feedback in tempo reale e mypy nella CI/CD come gate di qualita.

### Usare mypy e pyright insieme

Una strategia consolidata per team medio-grandi:

```toml
# pyproject.toml — configurazione dual checker

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
```

```yaml
# CI/CD: entrambi come gate
- name: mypy check
  run: mypy --strict src/

- name: pyright check
  run: pyright src/
```

I due tool hanno differenze sottili nell'interpretazione di certi PEP. Se uno segnala un errore e l'altro no, investigare quale ha ragione piuttosto che silenziare con `# type: ignore`.

### Confronto approfondito: mypy vs pyright

Le differenze tra mypy e pyright vanno oltre la semplice velocita. Comprendere i punti di forza di ciascuno aiuta a scegliere lo strumento giusto per il proprio progetto e, idealmente, a usarli in modo complementare.

#### Filosofia di checking: opt-in vs opt-out

La differenza architetturale piu significativa riguarda il trattamento del codice **non annotato**:

- **mypy**: adotta un approccio **opt-in**. Per impostazione predefinita, le funzioni senza annotazioni vengono sostanzialmente ignorate. Per controllarle, bisogna abilitare `--check-untyped-defs` o `--strict`. Questo rende l'adozione graduale piu semplice: mypy analizza solo cio che e stato esplicitamente annotato.

- **pyright**: adotta un approccio **opt-out**. Controlla **tutto** il codice, anche quello senza annotazioni, usando tipi inferiti. Questo significa che pyright trova errori anche in codice completamente privo di type hints, ma puo generare falsi positivi in codebase legacy.

```python
# Esempio: funzione senza annotazioni
def calcola(x, y):
    return x + y

calcola("ciao", 42)

# mypy (default): NESSUN errore — la funzione non e annotata
# mypy --strict: error: Function is missing a type annotation

# pyright (basic): NESSUN errore — inferenza permissiva
# pyright (strict): error: Type of parameter "x" is unknown
# pyright (standard): potenziale warning a seconda del contesto
```

#### Inferenza dei tipi

Pyright ha un motore di inferenza piu aggressivo e sofisticato. In molti casi deduce tipi precisi dove mypy restituisce `Any` o tipi piu generici:

```python
# pyright inferisce il tipo esatto della lambda
callback = lambda x: x.upper()
# pyright: (x: str) -> str (inferito dal contesto)
# mypy: potrebbe richiedere annotazione esplicita

# Inferenza di dizionari complessi
config = {"host": "localhost", "porta": 5432, "ssl": True}
# pyright: dict[str, str | int | bool]
# mypy: dict[str, str | int | bool] (simile, ma meno preciso in casi complessi)
```

#### Livelli di rigidita a confronto

| Livello | mypy | pyright |
|---------|------|---------|
| **Minimo** | Default (ignora non annotato) | `off` (nessun controllo) |
| **Base** | `--check-untyped-defs` | `basic` (errori evidenti) |
| **Standard** | N/A | `standard` (default, buon bilanciamento) |
| **Rigido** | `--strict` | `strict` (massima rigidita) |

Pyright `strict` e generalmente **piu rigido** di mypy `--strict`. Pyright richiede annotazioni di tipo per tutti i parametri, le variabili di ritorno, e segnala tipi `Unknown` che mypy accetterebbe come inferiti.

#### Conformita alle specifiche

Pyright raggiunge circa il **98% di conformita** con le specifiche ufficiali del sistema di tipi Python (typing spec), il punteggio piu alto tra i type checker disponibili. Mypy segue le specifiche fedelmente ma ha alcune aree dove l'implementazione diverge leggermente, specialmente per i PEP piu recenti.

#### Velocita: benchmark reali

Su un progetto di circa 100.000 righe di codice Python:

| Operazione | mypy 1.20 (mypyc) | pyright 1.1.x | dmypy (warm) |
|-----------|-------------------|---------------|--------------|
| Cold start | ~12s | ~4s | ~12s |
| Modifica 1 file | ~8s (cache disco) | ~1s | ~0.3s |
| Nessuna modifica | ~3s (cache disco) | ~0.5s | ~0.05s |

**Nota**: a partire da mypy 1.18+, le build compilate con mypyc hanno significativamente ridotto il divario prestazionale con pyright. Il daemon `dmypy` resta la scelta piu veloce per il feedback interattivo durante lo sviluppo.

#### Plugin e ecosistema

| Aspetto | mypy | pyright |
|---------|------|---------|
| Plugin Django | `django-stubs` (maturo) | Supporto base senza plugin |
| Plugin Pydantic | `pydantic.mypy` (ufficiale) | Supporto nativo (senza plugin) |
| Plugin SQLAlchemy | `sqlalchemy.ext.mypy.plugin` | Supporto parziale nativo |
| Plugin personalizzati | API plugin Python estensibile | Non supportato |
| Estensioni IDE | Plugin per vari editor | Nativo in VS Code (Pylance) |

#### Quando scegliere quale

**Preferire mypy quando:**
- Si usa Django, SQLAlchemy o framework con plugin mypy maturi
- Si vuole un controllo fine tramite plugin personalizzati
- Il progetto usa `dmypy` per il feedback rapido
- Il team ha gia un workflow consolidato con mypy

**Preferire pyright quando:**
- Si sviluppa principalmente con VS Code
- Si vuole il feedback piu veloce possibile nell'IDE
- Si lavora con codebase non annotate (inferenza superiore)
- Si necessita della massima conformita alle specifiche typing

**Usare entrambi quando:**
- Si desidera la massima copertura di errori
- Si ha una CI/CD robusta che puo eseguire entrambi
- Si lavorano progetti dove la correttezza dei tipi e critica

### typing_extensions: portabilita tra versioni Python

Il pacchetto `typing_extensions` e il ponte che permette di utilizzare le novita del sistema di tipi su versioni precedenti di Python. I type checker (mypy, pyright) trattano `typing_extensions.X` esattamente come `typing.X`.

#### Funzionalita disponibili per versione

| Feature | `typing` (versione minima) | `typing_extensions` (backport) |
|---------|---------------------------|-------------------------------|
| `TypeGuard` | Python 3.10 | Si |
| `Self` | Python 3.11 | Si |
| `TypeVarTuple`, `Unpack` | Python 3.11 | Si |
| `override` | Python 3.12 | Si (>= 4.4.0) |
| `TypeVar(default=...)` | Python 3.13 | Si (>= 4.4.0) |
| `TypeIs` | Python 3.13 | Si (>= 4.10.0) |
| `ReadOnly` (TypedDict) | Python 3.13 | Si |
| `TypeForm` | Python 3.14 (PEP 747) | Si (sperimentale) |

#### Pattern di import condizionale

Per scrivere codice compatibile con piu versioni di Python:

```python
import sys

if sys.version_info >= (3, 13):
    from typing import TypeIs, override
else:
    from typing_extensions import TypeIs, override

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar  # Per il parametro default

# Alternativa pragmatica: importare sempre da typing_extensions
# per uniformita e semplicita
from typing_extensions import TypeIs, override, TypeVar
```

La seconda strategia (importare sempre da `typing_extensions`) e piu semplice da mantenere, ma aggiunge una dipendenza runtime. Per librerie che devono minimizzare le dipendenze, l'import condizionale con `sys.version_info` e preferibile.

---

## Pattern Pratici

### Typing dei decoratori

Annotare correttamente un decoratore richiede `ParamSpec` per preservare la firma della funzione decorata:

```python
from typing import ParamSpec, TypeVar, Callable
from functools import wraps
import time

P = ParamSpec("P")
R = TypeVar("R")

def misura_tempo(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        inizio = time.perf_counter()
        risultato = func(*args, **kwargs)
        durata = time.perf_counter() - inizio
        print(f"{func.__name__} eseguita in {durata:.4f}s")
        return risultato
    return wrapper

@misura_tempo
def calcola(n: int) -> float:
    return sum(i ** 0.5 for i in range(n))

# Il type checker sa che `calcola` ha firma (int) -> float
```

Decoratore factory (decoratore con parametri):

```python
def riprova(tentativi: int = 3) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decoratore factory che riprova in caso di eccezione."""
    def decoratore(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            ultima_eccezione: Exception | None = None
            for tentativo in range(tentativi):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ultima_eccezione = e
                    print(f"Tentativo {tentativo + 1}/{tentativi} fallito: {e}")
            raise ultima_eccezione  # type: ignore[misc]
        return wrapper
    return decoratore

@riprova(tentativi=3)
def scarica_dati(url: str, timeout: int = 30) -> dict[str, object]:
    ...
```

Decoratore che modifica il tipo di ritorno:

```python
def come_stringa(func: Callable[P, object]) -> Callable[P, str]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
        return str(func(*args, **kwargs))
    return wrapper

@come_stringa
def somma(a: int, b: int) -> int:
    return a + b

# reveal_type(somma(1, 2)) -> str
```

### Typing dei context manager

```python
from typing import Generator
from contextlib import contextmanager

@contextmanager
def gestisci_connessione(url: str) -> Generator[Connessione, None, None]:
    conn = Connessione(url)
    try:
        yield conn
    finally:
        conn.chiudi()
```

Con la classe che implementa il protocollo context manager:

```python
from types import TracebackType
from typing import IO

class GestoreFile:
    def __init__(self, percorso: str, modalita: str = "r") -> None:
        self.percorso = percorso
        self.modalita = modalita
        self.file: IO[str] | None = None

    def __enter__(self) -> "GestoreFile":
        self.file = open(self.percorso, self.modalita)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        if self.file:
            self.file.close()
        return None  # Non sopprimere eccezioni
```

### Typing dei generatori e iteratori

```python
from typing import Generator, Iterator, Iterable

# Generator[YieldType, SendType, ReturnType]
def conta_fino_a(n: int) -> Generator[int, None, None]:
    for i in range(1, n + 1):
        yield i

# Se non si usa send() ne return, si puo semplificare con Iterator
def fibonacci() -> Iterator[int]:
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Iterable e piu generico (qualsiasi oggetto iterabile)
def somma_elementi(elementi: Iterable[int]) -> int:
    return sum(elementi)

# Funziona con liste, tuple, generatori, set, ecc.
somma_elementi([1, 2, 3])
somma_elementi(range(10))
somma_elementi(conta_fino_a(5))

# Generatore con send()
def accumulatore() -> Generator[float, float, str]:
    totale = 0.0
    while True:
        valore = yield totale
        if valore < 0:
            return f"Totale finale: {totale}"
        totale += valore
```

### Typing dei metodi di classe

```python
from typing import Self, ClassVar

class Configurazione:
    _istanza: ClassVar["Configurazione | None"] = None  # Singleton

    def __init__(self, host: str, porta: int) -> None:
        self.host = host
        self.porta = porta

    @classmethod
    def da_env(cls) -> Self:
        import os
        return cls(
            host=os.environ.get("HOST", "localhost"),
            porta=int(os.environ.get("PORTA", "8080")),
        )

    @classmethod
    def predefinita(cls) -> Self:
        return cls("localhost", 8080)

    @staticmethod
    def valida_porta(porta: int) -> bool:
        return 0 < porta < 65536
```

### Typing delle callback

```python
from typing import Callable, Protocol

# Callback semplice
def esegui_con_retry(
    operazione: Callable[[], bool],
    tentativi: int = 3,
    on_errore: Callable[[Exception], None] | None = None,
) -> bool:
    for i in range(tentativi):
        try:
            if operazione():
                return True
        except Exception as e:
            if on_errore:
                on_errore(e)
    return False

# Callback complessa con Protocol (piu leggibile di Callable per firme articolate)
class GestoreEventi(Protocol):
    def __call__(self, evento: str, dati: dict[str, object]) -> bool: ...

def registra_gestore(
    tipo_evento: str,
    gestore: GestoreEventi,
) -> None:
    ...
```

### Typing dei dizionari con chiavi specifiche (TypedDict)

```python
from typing import TypedDict, Required, NotRequired

class ConfigurazioneDB(TypedDict):
    host: str
    porta: int
    nome_db: str
    utente: str
    password: str
    ssl: NotRequired[bool]
    pool_size: NotRequired[int]

class RispostaAPI(TypedDict):
    successo: bool
    dati: list[dict[str, object]]
    errore: NotRequired[str]
    paginazione: NotRequired["InfoPaginazione"]

class InfoPaginazione(TypedDict):
    pagina: int
    per_pagina: int
    totale: int

def configura_database(config: ConfigurazioneDB) -> None:
    print(f"Connessione a {config['host']}:{config['porta']}/{config['nome_db']}")
    # mypy verifica che tutte le chiavi obbligatorie siano presenti

configura_database({
    "host": "localhost",
    "porta": 5432,
    "nome_db": "mio_db",
    "utente": "admin",
    "password": "segreta",
})
```

### Pattern Repository generico

```python
from typing import TypeVar, Generic, Protocol
from abc import ABC, abstractmethod

class Entita(Protocol):
    id: int

T = TypeVar("T", bound=Entita)

class Repository(ABC, Generic[T]):
    @abstractmethod
    def trova_per_id(self, id: int) -> T | None:
        ...

    @abstractmethod
    def trova_tutti(self) -> list[T]:
        ...

    @abstractmethod
    def salva(self, entita: T) -> T:
        ...

    @abstractmethod
    def elimina(self, id: int) -> bool:
        ...

class Utente:
    def __init__(self, id: int, nome: str, email: str) -> None:
        self.id = id
        self.nome = nome
        self.email = email

class UtenteRepository(Repository[Utente]):
    def __init__(self) -> None:
        self._storage: dict[int, Utente] = {}

    def trova_per_id(self, id: int) -> Utente | None:
        return self._storage.get(id)

    def trova_tutti(self) -> list[Utente]:
        return list(self._storage.values())

    def salva(self, entita: Utente) -> Utente:
        self._storage[entita.id] = entita
        return entita

    def elimina(self, id: int) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

# Il type checker garantisce che UtenteRepository
# implementi correttamente tutti i metodi astratti
# con i tipi specifici per Utente
repo: Repository[Utente] = UtenteRepository()
utente = repo.trova_per_id(1)  # tipo inferito: Utente | None
tutti = repo.trova_tutti()     # tipo inferito: list[Utente]
```

---

## Pattern Avanzati: TYPE_CHECKING e Forward References

### Il problema delle dipendenze circolari nei tipi

Quando due moduli si riferiscono l'uno ai tipi dell'altro, si crea una dipendenza circolare di import. Le annotazioni di tipo sono la causa piu comune di import circolari in Python, perche richiedono di importare classi che altrimenti non servirebbero a runtime.

### La costante TYPE_CHECKING

`typing.TYPE_CHECKING` e una costante che vale `True` solo durante l'analisi statica (mypy, pyright) e `False` a runtime. Questo permette di importare tipi necessari solo per le annotazioni senza creare dipendenze circolari a runtime:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modulo_pesante import ClassePesante
    from altro_modulo import AltroTipo

class MioServizio:
    def elabora(self, dati: ClassePesante) -> AltroTipo:
        # A runtime, ClassePesante e AltroTipo non sono importati
        # Ma mypy sa quali tipi sono
        ...
```

**Requisiti per funzionare:**

1. `from __future__ import annotations` (PEP 563) **deve** essere presente, altrimenti Python tenta di valutare le annotazioni a runtime e fallisce con `NameError`.
2. Oppure, le annotazioni devono essere scritte come stringhe: `def elabora(self, dati: "ClassePesante") -> "AltroTipo":`.

### Forward references (riferimenti in avanti)

Un forward reference e un'annotazione che si riferisce a un tipo non ancora definito nel punto in cui compare. Ci sono due modi per gestirli:

#### 1. Stringhe letterali

```python
class Nodo:
    def __init__(self, valore: int) -> None:
        self.valore = valore
        self.figli: list["Nodo"] = []  # Forward reference come stringa

    def aggiungi_figlio(self, figlio: "Nodo") -> None:
        self.figli.append(figlio)

    def crea_fratello(self) -> "Nodo":
        return Nodo(self.valore)
```

#### 2. from \_\_future\_\_ import annotations (PEP 563)

```python
from __future__ import annotations

class Nodo:
    def __init__(self, valore: int) -> None:
        self.valore = valore
        self.figli: list[Nodo] = []  # Non serve piu la stringa

    def aggiungi_figlio(self, figlio: Nodo) -> None:
        self.figli.append(figlio)
```

Con `from __future__ import annotations`, **tutte** le annotazioni del modulo diventano stringhe lazy (non vengono valutate a runtime). Questo e il comportamento che diventa il default in Python 3.14+ (PEP 649 / PEP 749).

**Attenzione**: `from __future__ import annotations` puo causare problemi con librerie che accedono alle annotazioni a runtime, come Pydantic v1, FastAPI (in alcuni casi), e `dataclasses.fields()`. Pydantic v2 gestisce questo caso correttamente.

### Pattern completo: TYPE_CHECKING con dipendenze circolari

Scenario: `ordine.py` deve fare riferimento a `utente.py` e viceversa.

```python
# utente.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ordine import Ordine

class Utente:
    def __init__(self, nome: str) -> None:
        self.nome = nome
        self.ordini: list[Ordine] = []

    def ultimo_ordine(self) -> Ordine | None:
        return self.ordini[-1] if self.ordini else None
```

```python
# ordine.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utente import Utente

class Ordine:
    def __init__(self, numero: int, proprietario: Utente) -> None:
        self.numero = numero
        self.proprietario = proprietario

    def descrizione(self) -> str:
        return f"Ordine #{self.numero} di {self.proprietario.nome}"
```

### get_type_hints() e annotazioni lazy

Quando si ha bisogno di accedere alle annotazioni a runtime (ad es. per serializzazione, validazione, dependency injection), `typing.get_type_hints()` risolve le forward references e le stringhe:

```python
from typing import get_type_hints

class Esempio:
    valore: "int"
    nome: str

# __annotations__ contiene le stringhe non risolte
print(Esempio.__annotations__)
# {'valore': 'int', 'nome': <class 'str'>}

# get_type_hints() risolve le stringhe
print(get_type_hints(Esempio))
# {'valore': <class 'int'>, 'nome': <class 'str'>}
```

### Annotazioni e performance: il costo reale

Le annotazioni hanno un impatto misurabile sulla performance di importazione dei moduli, perche Python valuta le espressioni di annotazione al momento dell'import (a meno che non si usi `from __future__ import annotations`):

```python
# Senza __future__ annotations: le annotazioni vengono valutate
# Cio significa che `list[int]` crea un oggetto GenericAlias a ogni import
class Esempio:
    dati: list[int]  # Valutato a import-time

# Con __future__ annotations: le annotazioni restano stringhe
from __future__ import annotations
class Esempio:
    dati: list[int]  # Memorizzato come stringa "list[int]", zero overhead
```

Per moduli con migliaia di annotazioni, la differenza puo essere significativa. Questa e una delle ragioni per cui PEP 649/749 adotta la valutazione lazy come default futuro.

---

## Runtime Type Checking

I type hints di Python sono, per impostazione predefinita, annotazioni puramente statiche. Tuttavia, esistono casi in cui si desidera verificare i tipi anche a **runtime**, ad esempio per la validazione degli input nelle API pubbliche o ai confini del sistema (dati da fonti esterne, input utente, risposte API).

### isinstance() e type hints

Python supporta `isinstance()` con i tipi di base, ma non con tutti i costrutti di `typing`:

```python
# Funziona con i tipi di base
isinstance(42, int)                    # True
isinstance("ciao", str)               # True
isinstance([1, 2], list)              # True

# NON funziona con i generici parametrizzati
isinstance([1, 2], list[int])         # TypeError!

# Funziona con Protocol decorati con @runtime_checkable
from typing import Protocol, runtime_checkable

@runtime_checkable
class Supporta_len(Protocol):
    def __len__(self) -> int: ...

isinstance([1, 2, 3], Supporta_len)   # True
isinstance(42, Supporta_len)          # False
```

**Nota importante**: il controllo con `@runtime_checkable` verifica solo la **presenza** dei metodi, non le loro firme o i tipi dei parametri. E un controllo meno rigoroso di quello statico.

Il type narrowing con `isinstance` e fondamentale per lavorare con i Union types:

```python
def elabora(dato: str | int | list[str]) -> str:
    if isinstance(dato, str):
        return dato.upper()          # mypy sa che `dato` e str
    elif isinstance(dato, int):
        return str(dato)             # mypy sa che `dato` e int
    else:
        return ", ".join(dato)       # mypy sa che `dato` e list[str]
```

### beartype

[beartype](https://github.com/beartype/beartype) e una libreria leggera per la validazione dei tipi a runtime con overhead minimo:

```python
from beartype import beartype

@beartype
def saluta(nome: str, volte: int = 1) -> list[str]:
    return [f"Ciao {nome}!"] * volte

saluta("Mario", 3)      # OK
saluta(42, 3)            # BeartypeCallHintParamViolation!
saluta("Mario", "tre")   # BeartypeCallHintParamViolation!
```

beartype supporta la quasi totalita dei costrutti di `typing` e ha un overhead estremamente basso (O(1)) rispetto ad alternative come `typeguard`, perche genera controlli ottimizzati al momento della decorazione:

```python
from beartype import beartype

@beartype
def elabora_dati(
    dati: list[dict[str, int | float]],
    filtro: str | None = None,
) -> dict[str, float]:
    risultato: dict[str, float] = {}
    for elemento in dati:
        for chiave, valore in elemento.items():
            if filtro is None or chiave.startswith(filtro):
                risultato[chiave] = float(valore)
    return risultato
```

beartype puo essere configurato anche a livello globale per decorare automaticamente tutte le funzioni di un modulo, senza aggiungere `@beartype` a ogni funzione:

```python
from beartype.claw import beartype_this_package

beartype_this_package()  # Da inserire nel __init__.py del pacchetto
```

### Pydantic

[Pydantic](https://docs.pydantic.dev/) e la libreria di riferimento per la **validazione dei dati** in Python, utilizzata ampiamente in FastAPI e in molti altri framework. Pydantic usa i type hints per definire lo schema dei dati e esegue validazione e coercizione automatica a runtime:

```python
from pydantic import BaseModel, Field, field_validator

class Utente(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    eta: int = Field(ge=0, le=150)
    email: str
    ruoli: list[str] = []

    @field_validator("email")
    @classmethod
    def valida_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Email non valida")
        return v.lower()

# Validazione automatica
utente = Utente(nome="Mario", eta=30, email="Mario@Example.com")
print(utente.email)  # mario@example.com (normalizzata)

# Errore di validazione
try:
    Utente(nome="", eta=-5, email="invalida")
except Exception as e:
    print(e)  # Dettagli sugli errori di validazione
```

Pydantic va oltre il semplice type checking: esegue **coercizione** dei tipi (converte automaticamente i valori quando possibile), validazione personalizzata e serializzazione/deserializzazione.

Per un approfondimento completo su Pydantic, consultare il file dedicato **29-pydantic-e-validazione.md**.

### typeguard

[typeguard](https://github.com/agronholm/typeguard) e un'altra libreria per il runtime type checking, piu rigorosa di beartype ma con un overhead maggiore:

```python
from typeguard import typechecked

@typechecked
def calcola_media(valori: list[float]) -> float:
    if not valori:
        raise ValueError("Lista vuota")
    return sum(valori) / len(valori)

calcola_media([1.0, 2.0, 3.0])   # OK
calcola_media([1, 2, 3])          # OK (int e sottotipo di float per typeguard)
calcola_media("non una lista")    # TypeCheckError!
```

typeguard puo anche essere usato come plugin pytest per controllare automaticamente tutte le funzioni annotate durante i test:

```bash
pytest --typeguard-packages=mio_progetto
```

### Confronto tra le librerie di runtime type checking

| Caratteristica | beartype | typeguard | pydantic |
|---------------|----------|-----------|----------|
| **Overhead** | Minimo (O(1)) | Moderato | Moderato |
| **Approccio** | Decoratore | Decoratore / plugin | Modelli dati |
| **Copertura tipi** | Quasi completa | Completa | Completa + coercizione |
| **Uso principale** | Validazione interna | Testing | Validazione dati esterni |
| **Serializzazione** | No | No | Si (JSON, dict) |
| **Integrazione pytest** | No | Si | No (ma testabile) |

### Pattern avanzati di runtime type checking

#### beartype: decorazione a livello di pacchetto

beartype offre un meccanismo potente per applicare il type checking a **tutte le funzioni** di un pacchetto senza modificare ogni singolo file. Questo avviene tramite l'import hook `beartype_this_package`:

```python
# mio_progetto/__init__.py
from beartype.claw import beartype_this_package

# Abilita il controllo automatico per TUTTO il pacchetto
beartype_this_package()

# Da questo momento, ogni funzione annotata in mio_progetto
# viene automaticamente decorata con @beartype
```

Si puo configurare il comportamento con la classe `BeartypeConf`:

```python
from beartype import BeartypeConf
from beartype.claw import beartype_this_package

beartype_this_package(conf=BeartypeConf(
    is_color=True,             # Output colorato negli errori
    is_debug=False,            # Disabilita il debug logging
    violation_type=TypeError,  # Tipo di eccezione da sollevare
))
```

#### typeguard: checking completo e integrazione con pytest

typeguard esegue un controllo **completo** di tutti i tipi, inclusi i generici parametrizzati (a differenza di beartype che usa campionamento O(1)):

```python
from typeguard import typechecked, check_type

# Decoratore per funzioni
@typechecked
def elabora_dati(
    elementi: list[dict[str, int]],
    limite: int | None = None,
) -> list[int]:
    risultati = []
    for elem in elementi:
        valori = list(elem.values())
        if limite is not None:
            valori = valori[:limite]
        risultati.extend(valori)
    return risultati

# Controllo standalone su un singolo valore
check_type([1, 2, 3], list[int])          # OK
check_type(["a", "b"], list[int])         # TypeCheckError!

# Controllo di tipi complessi
check_type(
    {"utenti": [{"nome": "Mario"}]},
    dict[str, list[dict[str, str]]],
)  # OK
```

L'integrazione con pytest avviene senza modificare il codice di produzione:

```bash
# Controlla tutti i tipi nelle funzioni annotate durante i test
pytest --typeguard-packages=mio_progetto

# Solo moduli specifici
pytest --typeguard-packages=mio_progetto.core,mio_progetto.api
```

Questo e particolarmente utile per la **transizione verso il type checking**: si aggiungono annotazioni al codice e si verificano tramite i test esistenti, senza modificare il comportamento a runtime in produzione.

#### Strategia ibrida: statico + runtime ai confini

La best practice e combinare il type checking statico (mypy/pyright) con quello runtime **solo ai confini del sistema**, dove i dati provengono da fonti non controllate:

```python
from beartype import beartype
from typing import Any

# ─── Confine del sistema: dati da API esterna ───
@beartype
def processa_risposta_api(dati: dict[str, list[int]]) -> list[int]:
    """Validazione runtime: i dati vengono da una fonte esterna non tipizzata."""
    return [v for valori in dati.values() for v in valori]

# ─── Logica interna: solo type checking statico ───
def calcola_statistiche(valori: list[int]) -> dict[str, float]:
    """Nessuna validazione runtime: i dati sono gia stati validati al confine."""
    n = len(valori)
    media = sum(valori) / n
    varianza = sum((x - media) ** 2 for x in valori) / n
    return {"media": media, "varianza": varianza, "deviazione": varianza ** 0.5}
```

Questa strategia mantiene l'overhead di runtime al minimo: il costo della validazione viene pagato solo una volta, al punto di ingresso dei dati nel sistema.

---

## Migrazione di una codebase a strict typing — Guida passo-passo

Migrare un progetto Python esistente al type checking strict e un processo **iterativo e incrementale**. Tentare di annotare tutto in una volta e controproducente: genera centinaia di errori simultanei, demoralizza il team e introduce il rischio di annotazioni affrettate e imprecise.

### Fase 0: Preparazione e baseline

**Obiettivo**: capire lo stato attuale e preparare l'infrastruttura.

```bash
# Installare gli strumenti
pip install mypy types-requests types-PyYAML  # + stubs per le librerie usate

# Eseguire mypy con la configurazione minima per stabilire la baseline
mypy --ignore-missing-imports --show-error-codes src/
```

Creare la configurazione iniziale in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
# Fase 0: configurazione minima, zero errori
ignore_missing_imports = true
check_untyped_defs = true     # Controlla anche le funzioni non annotate
show_error_codes = true
pretty = true
```

Registrare il **numero totale di errori** come metrica di partenza. Questo numero dovra solo diminuire nel tempo.

### Fase 1: Annotare i moduli critici (settimane 1-2)

**Obiettivo**: annotare le **interfacce pubbliche** dei moduli piu importanti del progetto.

Selezionare 3-5 moduli critici (ad es. `core/`, `api/`, `modelli/`) e annotare solo le firme delle funzioni e classi pubbliche. Non preoccuparsi del corpo delle funzioni:

```python
# Prima
def calcola_prezzo(prodotto, quantita, sconto=None):
    prezzo_base = prodotto["prezzo"] * quantita
    if sconto:
        prezzo_base *= (1 - sconto / 100)
    return round(prezzo_base, 2)

# Dopo: solo firma annotata
def calcola_prezzo(
    prodotto: dict[str, object],
    quantita: int,
    sconto: float | None = None,
) -> float:
    prezzo_base = prodotto["prezzo"] * quantita  # type: ignore[operator]
    if sconto:
        prezzo_base *= (1 - sconto / 100)
    return round(prezzo_base, 2)
```

I `# type: ignore` temporanei sono accettabili in questa fase. Verranno rimossi nelle fasi successive.

### Fase 2: Eliminare gli Any impliciti (settimane 3-4)

**Obiettivo**: ridurre l'uso di `Any` e sostituirlo con tipi specifici.

Abilitare flag piu restrittivi per i moduli gia annotati:

```toml
[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
check_untyped_defs = true
show_error_codes = true

# Fase 2: rigidita crescente
warn_return_any = true
no_implicit_optional = true
warn_redundant_casts = true

# Moduli gia migrati: disallow_untyped_defs
[[tool.mypy.overrides]]
module = "mio_progetto.core.*"
disallow_untyped_defs = true

# Moduli non ancora migrati: nessuna restrizione aggiuntiva
[[tool.mypy.overrides]]
module = "mio_progetto.legacy.*"
disallow_untyped_defs = false
ignore_errors = true
```

### Fase 3: Strict per i nuovi moduli (settimane 5-8)

**Obiettivo**: tutti i **nuovi** moduli nascono con `strict = true`.

```toml
[[tool.mypy.overrides]]
module = "mio_progetto.nuovi_moduli.*"
strict = true
```

Regola del team: ogni nuovo file o modulo deve passare `mypy --strict` prima del merge. I moduli legacy continuano con le regole rilassate della Fase 2.

### Fase 4: Migrazione dei moduli legacy (settimane 8-16)

**Obiettivo**: portare progressivamente i moduli legacy a `strict`.

Procedere modulo per modulo, in ordine di importanza. Per ogni modulo:

1. Eseguire `mypy --strict modulo.py` e registrare il numero di errori
2. Annotare le firme delle funzioni
3. Sostituire i `dict[str, object]` con `TypedDict` dove appropriato
4. Rimuovere i `# type: ignore` non piu necessari
5. Eseguire i test per verificare che nulla si sia rotto
6. Spostare il modulo nella sezione `strict` del `pyproject.toml`

### Fase 5: Strict globale (obiettivo finale)

**Obiettivo**: `strict = true` a livello globale.

```toml
[tool.mypy]
python_version = "3.12"
strict = true
show_error_codes = true
pretty = true

# Eccezioni residue (idealmente nessuna)
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Integrazione nella CI/CD

Una volta raggiunta una copertura di tipo soddisfacente, integrare mypy come gate bloccante nella pipeline:

```yaml
# .github/workflows/type-check.yml
name: Type Check
on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: mypy --strict src/

  pyright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]" pyright
      - run: pyright src/
```

### Metriche di progresso

Tracciare la migrazione con uno script che misura la copertura:

```bash
# Generare report di copertura dei tipi
mypy --linecount-report rapporti/ src/

# Output: CSV con percentuali per modulo
# mio_progetto.core.auth,245,230,93.9%
# mio_progetto.core.db,180,95,52.8%
```

Obiettivi suggeriti per fase:

| Fase | Copertura moduli critici | Copertura globale |
|------|--------------------------|-------------------|
| 0 | 0% | 0% |
| 1 | 60% interfacce | 15-20% |
| 2 | 80% interfacce | 30-40% |
| 3 | 100% nuovi moduli | 50-60% |
| 4 | 90% legacy | 80-90% |
| 5 | 100% | 95%+ |

---

## Best Practices

### 1. Iniziare dalle interfacce pubbliche

Quando si adottano i type hints in un progetto esistente, annotare prima le **funzioni e classi pubbliche** (quelle importate da altri moduli). Questo offre il massimo beneficio con il minimo sforzo iniziale. Le variabili locali possono spesso essere inferite automaticamente da mypy.

```python
# Priorita alta: API pubblica del modulo
def calcola_sconto(prezzo: float, percentuale: float) -> float:
    ...

# Priorita minore: funzione interna (mypy inferisce i tipi locali)
def _arrotonda(valore):
    ...
```

### 2. Evitare Any quando possibile

`Any` disabilita il type checking. Usarlo e come non avere annotazioni. Se il tipo e veramente sconosciuto, preferire `object` (che richiede controlli espliciti prima dell'uso) oppure un `TypeVar` per preservare le relazioni tra tipi.

```python
# Sconsigliato
def elabora(dati: Any) -> Any:
    ...

# Meglio: essere specifici
def elabora(dati: dict[str, str | int]) -> list[str]:
    ...

# Se il tipo e veramente generico, usare TypeVar
T = TypeVar("T")
def identita(valore: T) -> T:
    return valore
```

### 3. Usare Protocol al posto dell'ereditarieta quando appropriato

I Protocol permettono il **duck typing statico**: definiscono cosa un oggetto deve saper fare, non da cosa deve ereditare. Questo porta a codice piu flessibile e disaccoppiato, ideale per definire interfacce tra componenti.

```python
class Serializzabile(Protocol):
    def to_json(self) -> str: ...

def salva(oggetto: Serializzabile) -> None:
    dati = oggetto.to_json()
    # Qualsiasi classe con to_json() -> str e accettata,
    # senza dover ereditare da nulla
```

Usare ABC con `@abstractmethod` solo quando si ha bisogno dell'applicazione a runtime o quando la classe base fornisce implementazione condivisa.

### 4. Annotare i tipi di ritorno in modo preciso

Evitare di restituire tipi troppo generici. Un tipo di ritorno preciso permette al type checker e all'IDE di fornire un aiuto migliore al codice chiamante.

```python
# Troppo generico
def ottieni_utenti() -> list:
    ...

# Preciso
def ottieni_utenti() -> list[Utente]:
    ...

# Usare overload quando il tipo di ritorno dipende dagli argomenti
@overload
def cerca(query: str, singolo: Literal[True]) -> Utente | None: ...
@overload
def cerca(query: str, singolo: Literal[False] = ...) -> list[Utente]: ...
```

### 5. Preferire tipi astratti nei parametri, concreti nei ritorni

Per i parametri delle funzioni, usare tipi astratti (`Iterable`, `Sequence`, `Mapping`) invece di tipi concreti (`list`, `dict`). Questo rende le funzioni piu flessibili. Per i valori di ritorno, usare tipi concreti per dare al chiamante la massima informazione.

```python
from collections.abc import Iterable, Sequence, Mapping

# Consigliato: accetta list, tuple, generator, ecc.
def media(valori: Iterable[float]) -> float:
    totale = 0.0
    conteggio = 0
    for v in valori:
        totale += v
        conteggio += 1
    return totale / conteggio

# Se serve l'accesso per indice, usare Sequence
def primo(elementi: Sequence[str]) -> str:
    return elementi[0]

# Per i dizionari, usare Mapping (sola lettura)
def cerca(dati: Mapping[str, int], chiave: str) -> int | None:
    return dati.get(chiave)
```

### 6. Usare Final e Literal per i valori costanti

`Final` impedisce la riassegnazione accidentale di costanti. `Literal` restringe i valori ammessi a un insieme specifico, piu preciso di un semplice `str` o `int`.

```python
from typing import Final, Literal

MAX_CONNESSIONI: Final = 100
VERSIONE_API: Final = "v2"

def imposta_livello_log(
    livello: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
) -> None:
    ...

# Il type checker segnala errori di battitura
imposta_livello_log("DEUBG")  # Errore: "DEUBG" non e ammesso
```

### 7. Integrare mypy nella CI/CD

Aggiungere mypy alla pipeline di integrazione continua garantisce che le annotazioni di tipo vengano verificate automaticamente a ogni commit. Nessun codice con errori di tipo dovrebbe raggiungere il branch principale.

```yaml
# Esempio con GitHub Actions
- name: Type check
  run: |
    pip install mypy
    mypy --strict src/
```

```yaml
# Con pre-commit
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### 8. Documentare le scelte di tipo non ovvie

Quando un'annotazione di tipo non e immediatamente comprensibile, aggiungere un commento che ne spieghi il motivo. Questo vale specialmente per `# type: ignore`, `cast()`, e tipi complessi.

```python
from typing import cast

# Il parser JSON restituisce Any, ma conosciamo la struttura
# dal contratto API, verificata dai test di integrazione.
risposta = cast(dict[str, list[int]], json.loads(payload))

# Ignoriamo l'errore perche la libreria xyz non ha stubs
# e il tipo e stato verificato manualmente.
risultato = xyz.calcola(dati)  # type: ignore[no-any-return]
```

### 9. Usare TypedDict per le strutture dati JSON-like

Quando si lavora con API REST o configurazioni JSON, `TypedDict` fornisce type safety senza richiedere una classe completa. Per strutture piu complesse con validazione, considerare Pydantic.

```python
from typing import TypedDict

class RispostaLogin(TypedDict):
    token: str
    scadenza: int
    utente: "DatiUtente"

class DatiUtente(TypedDict):
    id: int
    nome: str
    permessi: list[str]

def gestisci_login(risposta: RispostaLogin) -> str:
    return risposta["token"]  # Type-safe, autocompletamento IDE
```

### 10. Mantenere aggiornate le annotazioni durante il refactoring

Le annotazioni di tipo sono una forma di documentazione vivente: se non vengono aggiornate quando il codice cambia, diventano fuorvianti. Il type checker aiuta in questo, segnalando le incongruenze. Per questo e fondamentale che mypy venga eseguito regolarmente (idealmente a ogni commit tramite CI/CD o pre-commit hook). Un errore di tipo dovrebbe bloccare il merge, esattamente come un test fallito.

```python
# Prima del refactoring
def cerca_utenti(filtro: str) -> list[Utente]:
    ...

# Dopo il refactoring: il tipo di ritorno deve aggiornarsi
def cerca_utenti(filtro: str, pagina: int = 1) -> PaginaRisultati[Utente]:
    ...

# Se ci si dimentica di aggiornare i chiamanti,
# mypy li segnalera automaticamente
```

---

## Troubleshooting

### Problema 1: Import circolari causati dai type hints

**Sintomo**: `ImportError: cannot import name 'X' from partially initialized module 'y'` a runtime, ma mypy non segnala errori.

**Causa**: due moduli si importano reciprocamente per le annotazioni di tipo.

**Soluzione**:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from altro_modulo import TipoProblematico

# Usare la stringa come annotazione se non si ha __future__
def funzione(param: "TipoProblematico") -> None:
    ...
```

### Problema 2: mypy segnala errori su librerie di terze parti

**Sintomo**: `error: Library stubs not installed for "requests"` o `error: Skipping analyzing "pandas": module is installed, but missing library stubs`.

**Soluzione**:

```bash
# Installare stubs ufficiali
pip install types-requests types-PyYAML

# Oppure lasciare che mypy li suggerisca
mypy --install-types src/

# Per librerie senza stubs disponibili, silenziare per modulo
```

```toml
[[tool.mypy.overrides]]
module = ["pandas.*", "numpy.*"]
ignore_missing_imports = true
```

### Problema 3: TypedDict e Unpack con **kwargs

**Sintomo**: si vuole tipizzare `**kwargs` con un TypedDict (PEP 692), ma mypy non lo supporta ancora completamente.

**Soluzione**: usare pyright (supporto migliore per PEP 692) o attendere il supporto mypy. Workaround:

```python
from typing import TypedDict, Unpack

class OpzioniConnessione(TypedDict, total=False):
    timeout: int
    retry: bool
    ssl: bool

# PEP 692 (Python 3.12+, supporto pyright)
def connetti(host: str, **kwargs: Unpack[OpzioniConnessione]) -> None:
    ...

# Workaround per mypy: usare un parametro esplicito
def connetti_compat(host: str, opzioni: OpzioniConnessione | None = None) -> None:
    ...
```

### Problema 4: Overload non riconosciuti correttamente

**Sintomo**: mypy segnala `error: Overloaded function implementation does not accept all possible arguments`.

**Causa**: l'implementazione effettiva non copre tutti i tipi dichiarati nelle firme `@overload`.

**Soluzione**: l'implementazione deve accettare l'unione di tutti i tipi degli overload:

```python
@overload
def parse(dato: str) -> list[str]: ...
@overload
def parse(dato: bytes) -> list[bytes]: ...

# ERRORE: l'implementazione accetta solo str
def parse(dato: str) -> list[str]:  # Manca bytes!
    ...

# CORRETTO: accetta str | bytes
def parse(dato: str | bytes) -> list[str] | list[bytes]:
    if isinstance(dato, str):
        return dato.split()
    return dato.split(b" ")
```

### Problema 5: Generici non inferiti correttamente

**Sintomo**: mypy inferisce `Any` o un tipo troppo ampio dove ci si aspetta un tipo specifico.

**Causa comune**: il TypeVar e usato in una posizione dove mypy non riesce a inferirlo.

**Soluzione**: usare `reveal_type()` per diagnosticare e, se necessario, fornire annotazioni esplicite:

```python
T = TypeVar("T")

def crea_lista(elem: T, n: int) -> list[T]:
    return [elem] * n

# Se mypy non inferisce:
risultato = crea_lista(42, 3)
reveal_type(risultato)  # Verificare cosa inferisce

# Forzare il tipo se necessario:
risultato: list[int] = crea_lista(42, 3)
```

### Problema 6: cast() vs assert per il narrowing

**Sintomo**: si usa `cast()` quando `assert` o un check `isinstance` sarebbe piu sicuro.

**Soluzione**: preferire sempre il narrowing basato su controlli reali. `cast()` **non fa alcun controllo a runtime** — e una dichiarazione al type checker che puo nascondere bug:

```python
from typing import cast

dati: dict[str, object] = carica_json()

# PERICOLOSO: nessun controllo a runtime, puo causare bug silenziosi
valore = cast(int, dati["campo"])

# MEGLIO: controllo reale
valore_raw = dati["campo"]
assert isinstance(valore_raw, int), f"Atteso int, ottenuto {type(valore_raw)}"
valore = valore_raw  # mypy sa che e int

# MIGLIORE in produzione: eccezione gestita
valore_raw = dati["campo"]
if not isinstance(valore_raw, int):
    raise TypeError(f"Campo 'campo' deve essere int, ottenuto {type(valore_raw)}")
valore = valore_raw
```

### Problema 7: mypy lento su grandi progetti

**Sintomo**: `mypy src/` impiega minuti su ogni esecuzione.

**Soluzioni**, in ordine di efficacia:

1. **Usare il daemon**: `dmypy run -- src/` (vedi sezione dedicata)
2. **Cache incrementale**: assicurarsi che `.mypy_cache/` non sia in `.gitignore` (o usare `--cache-dir` condiviso)
3. **Controllare solo i file modificati** in CI:

```bash
# In CI, controllare solo i file modificati
git diff --name-only origin/main...HEAD -- '*.py' | xargs mypy
```

4. **Parallelizzare**: mypy non ha flag nativo di parallelismo per modulo, ma si puo dividere il check:

```bash
# Controllare pacchetti separatamente in parallelo
mypy src/core/ &
mypy src/api/ &
mypy src/utils/ &
wait
```

5. **Considerare pyright** per il feedback in sviluppo (ordini di grandezza piu veloce).

### Problema 8: Conflitti tra mypy e pyright

**Sintomo**: mypy accetta del codice che pyright rifiuta, o viceversa.

**Causa**: i due strumenti hanno interpretazioni leggermente diverse di certi PEP. Differenze comuni:

| Scenario | mypy | pyright |
|----------|------|---------|
| `tuple[int, ...]` come `Sequence[int]` | Accetta | Accetta |
| Inferenza di lambda | Limitata | Precisa |
| `@overload` con implementation | Rigoroso | Piu flessibile |
| TypeVar non vincolato | Errore se ambiguo | Piu permissivo |
| `type: ignore` | Accetta sempre | Solo con `reportUnnecessaryTypeIgnoreComment` |

**Soluzione**: quando i due tool discordano, investigare quale interpretazione e corretta secondo il PEP di riferimento. In caso di divergenza genuina, usare commenti specifici per strumento:

```python
# mypy e pyright hanno commenti ignore diversi
x = funzione()  # type: ignore[return-value]  # solo mypy
x = funzione()  # pyright: ignore[reportReturnType]  # solo pyright
```

---

## Esercizi

### Esercizio 1: Annotare una funzione di filtraggio generica

Scrivere una funzione `filtra` che accetti un `Iterable[T]` e un predicato `Callable[[T], bool]`, restituendo una `list[T]`. Verificare con mypy che le annotazioni siano corrette.

```python
# Scheletro
def filtra(elementi: ..., predicato: ...) -> ...:
    return [e for e in elementi if predicato(e)]

# Test
numeri_pari = filtra([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
# reveal_type(numeri_pari) deve essere list[int]

nomi_lunghi = filtra(["ab", "abcdef", "x"], lambda s: len(s) > 3)
# reveal_type(nomi_lunghi) deve essere list[str]
```

### Esercizio 2: Protocol per un sistema di notifiche

Definire un `Protocol` chiamato `Notificatore` con un metodo `invia(destinatario: str, messaggio: str) -> bool`. Implementare tre classi concrete (`EmailNotificatore`, `SMSNotificatore`, `SlackNotificatore`) che soddisfino il protocol senza ereditare da esso. Scrivere una funzione `notifica_tutti` che accetti una lista di `Notificatore`.

### Esercizio 3: Decoratore type-safe con ParamSpec

Scrivere un decoratore `cache_risultato` che memorizzi il risultato dell'ultima chiamata. Il decoratore deve:
- Preservare la firma della funzione decorata usando `ParamSpec`.
- Restituire il risultato memorizzato se i parametri sono identici all'ultima chiamata.
- Essere completamente annotato e superare `mypy --strict`.

### Esercizio 4: TypedDict per un'API REST

Definire i `TypedDict` per modellare la risposta di un'API che restituisce una lista paginata di prodotti. La struttura:

```json
{
    "risultati": [
        {"id": 1, "nome": "Widget", "prezzo": 9.99, "in_stock": true}
    ],
    "paginazione": {
        "pagina_corrente": 1,
        "per_pagina": 20,
        "totale_pagine": 5,
        "totale_elementi": 95
    },
    "meta": {
        "versione_api": "v2",
        "timestamp": "2026-05-23T10:30:00Z"
    }
}
```

Scrivere una funzione `estrai_nomi_prodotti(risposta: RispostaProdotti) -> list[str]` e verificare con mypy.

### Esercizio 5: Gradual typing su codice esistente

Dato il seguente codice senza annotazioni, aggiungere type hints incrementalmente e risolvere tutti gli errori mypy in modalita strict:

```python
def processa_dati(dati, trasforma=None, filtro=None):
    risultati = []
    for elemento in dati:
        if filtro and not filtro(elemento):
            continue
        if trasforma:
            elemento = trasforma(elemento)
        risultati.append(elemento)
    return risultati

def aggrega(gruppi, operazione):
    return {chiave: operazione(valori) for chiave, valori in gruppi.items()}
```

### Esercizio 6: Overload e Literal per un parser configurabile

Scrivere una funzione `parse_valore` con overload che accetti un parametro `tipo: Literal["int", "float", "str", "bool"]` e restituisca il tipo corrispondente. Mypy deve inferire il tipo di ritorno corretto in base al valore letterale di `tipo`.

---

## Letture e Risorse

### Documentazione ufficiale

- [typing — Support for type hints](https://docs.python.org/3/library/typing.html) — Riferimento completo del modulo `typing`.
- [mypy documentation](https://mypy.readthedocs.io/) — Guida ufficiale mypy con esempi e configurazione.
- [Pyright documentation](https://microsoft.github.io/pyright/) — Documentazione ufficiale pyright.
- [typeshed](https://github.com/python/typeshed) — Repository stubs per la stdlib e librerie popolari.

### PEP fondamentali (testo completo)

- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/) — Il PEP fondante del sistema di type hints.
- [PEP 544 – Protocols: Structural subtyping](https://peps.python.org/pep-0544/) — Specifica completa dei Protocol.
- [PEP 612 – Parameter Specification Variables](https://peps.python.org/pep-0612/) — ParamSpec e Concatenate.
- [PEP 695 – Type Parameter Syntax](https://peps.python.org/pep-0695/) — Nuova sintassi `type` e generici inline.
- [PEP 742 – Narrowing types with TypeIs](https://peps.python.org/pep-0742/) — TypeIs, evoluzione di TypeGuard.
- [PEP 649 – Deferred evaluation of annotations](https://peps.python.org/pep-0649/) — Futuro default per le annotazioni lazy.

### Libri e articoli

- Luciano Ramalho, *Fluent Python*, 2nd ed. (O'Reilly, 2022) — Capitolo 8 "Type Hints in Functions" e Capitolo 15 "More About Type Hints".
- Dusty Phillips, *Python Object-Oriented Programming*, 4th ed. (Packt, 2021) — Sezione su Protocol e structural subtyping.
- [mypy cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) — Riferimento rapido delle annotazioni piu comuni.

### Strumenti correlati

- [beartype](https://github.com/beartype/beartype) — Runtime type checking O(1).
- [typeguard](https://github.com/agronholm/typeguard) — Runtime checking con integrazione pytest.
- [Pydantic](https://docs.pydantic.dev/) — Validazione dati basata su type hints.
- [MonkeyType](https://github.com/Instagram/MonkeyType) — Genera annotazioni automatiche monitorando l'esecuzione (Instagram).
- [pytype](https://google.github.io/pytype/) — Type checker Google con inferenza avanzata.

---

## Cross-link

| Modulo | Relazione |
|--------|-----------|
| **01 — Fondamenti** | Tipi base Python, variabili, funzioni |
| **02 — OOP** | Classi, ereditarieta, ABC — base per `Protocol` e classi generiche |
| **04 — Decoratori, Generatori, Context Manager** | Typing di decoratori con `ParamSpec`, generatori con `Generator[Y,S,R]`, context manager con `__enter__`/`__exit__` |
| **06 — Moduli e Pacchetti** | `__init__.py`, import system — rilevante per `TYPE_CHECKING` e import circolari |
| **07 — Error Handling** | Pattern di gestione errori tipizzati, eccezioni custom con annotazioni |
| **10 — Async** | Typing di coroutine (`Coroutine[Y,S,R]`), async generators (`AsyncGenerator`), `AsyncIterator` |
| **14 — Database e ORM** | SQLAlchemy plugin mypy, typing dei modelli ORM |
| **22 — Design Patterns** | Repository pattern generico, factory tipizzati, strategy con Protocol |
| **23 — Dipendenze e uv** | Gestione stubs come dipendenze di sviluppo |
| **25 — Packaging** | `py.typed` marker per pacchetti tipizzati (PEP 561) |
| **29 — Pydantic** | Runtime type checking avanzato, validazione basata su type hints |
| **31 — Osservabilita** | Typing delle metriche e degli span OpenTelemetry |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Annotazione di tipo** | Espressione che indica il tipo atteso di una variabile, parametro o valore di ritorno. Non ha effetto a runtime in CPython. |
| **Any** | Tipo speciale compatibile con qualunque altro tipo in entrambe le direzioni. Disabilita di fatto il type checking. |
| **Bound (TypeVar)** | Limite superiore di un TypeVar: il tipo generico deve essere un sottotipo del bound specificato. |
| **Callable** | Tipo che descrive un oggetto invocabile (funzione, metodo, lambda, classe con `__call__`). |
| **Cast** | Funzione `typing.cast(T, val)` che dichiara al type checker che `val` e di tipo `T`. Nessun controllo a runtime. |
| **ClassVar** | Annotazione che indica un attributo di classe (non di istanza). |
| **Concatenate** | Costruttore usato con `ParamSpec` per aggiungere parametri alla firma di una callable. |
| **Constraint (TypeVar)** | Insieme finito di tipi ammessi per un TypeVar. Diverso da Union perche il tipo viene fissato a una delle opzioni. |
| **Controvarianza** | Relazione di sottotipo invertita: se A <: B, allora `C[B] <: C[A]`. Per tipi "consumatori". |
| **Covarianza** | Relazione di sottotipo preservata: se A <: B, allora `C[A] <: C[B]`. Per tipi "produttori". |
| **dmypy** | Daemon mypy che mantiene lo stato in memoria per analisi incrementali veloci. |
| **Final** | Annotazione che impedisce la riassegnazione di una variabile o l'override di un metodo. |
| **Forward reference** | Annotazione che si riferisce a un tipo non ancora definito, espressa come stringa o tramite `from __future__ import annotations`. |
| **Generic** | Classe base per definire classi parametrizzate da TypeVar. In Python 3.12+, sostituita dalla sintassi inline `class C[T]`. |
| **Gradual typing** | Strategia di adozione incrementale dei type hints in un progetto esistente. |
| **Invarianza** | Assenza di relazione di sottotipo tra tipi generici: `C[A]` non e ne sottotipo ne supertipo di `C[B]`. |
| **Literal** | Tipo che restringe i valori ammessi a un insieme di costanti specifiche. |
| **Narrowing** | Processo per cui il type checker restringe il tipo di una variabile dopo un controllo (es. `isinstance`, `TypeIs`). |
| **override** | Decoratore (PEP 698, Python 3.12+) che marca un metodo come override di un metodo della classe base. Errore se il metodo base non esiste. |
| **NewType** | Crea un tipo nominale distinto dal tipo base, senza overhead a runtime. |
| **Overload** | Decoratore che dichiara piu firme per una funzione, permettendo al type checker di inferire il tipo di ritorno in base agli argomenti. |
| **ParamSpec** | Variabile di tipo che cattura l'intera firma dei parametri di una callable (PEP 612). |
| **Protocol** | Interfaccia strutturale (duck typing statico). Un tipo e compatibile se possiede i metodi/attributi richiesti (PEP 544). |
| **py.typed** | File marker (PEP 561) che indica che un pacchetto distribuito include annotazioni di tipo inline. |
| **reveal_type()** | Funzione speciale che mostra il tipo inferito dal type checker. In Python 3.11+, disponibile anche a runtime. |
| **Self** | Tipo che rappresenta la classe corrente, utile per pattern fluent/builder (PEP 673). |
| **Stub (.pyi)** | File contenente solo annotazioni di tipo senza implementazione, usato per annotare librerie senza type hints. |
| **TYPE_CHECKING** | Costante `typing.TYPE_CHECKING`: `True` durante l'analisi statica, `False` a runtime. Per import condizionali. |
| **type statement** | Sintassi Python 3.12+ (`type X = ...`) per definire alias di tipo (PEP 695). |
| **TypeAlias** | Annotazione esplicita per alias di tipo (PEP 613), sostituita da `type` in Python 3.12+. |
| **TypedDict** | Tipo per dizionari con chiavi fisse e tipizzate. |
| **TypeGuard** | Funzione di narrowing che informa il type checker sul tipo nel ramo `if` (PEP 647). |
| **TypeIs** | Versione migliorata di TypeGuard con narrowing in entrambi i rami if/else (PEP 742). |
| **TypeVar** | Variabile di tipo per la programmazione generica. Puo avere bound, constraints e default (PEP 696). |
| **typing_extensions** | Pacchetto che fornisce backport delle novita di `typing` per versioni precedenti di Python. |
| **TypeVarTuple** | Variabile di tipo che cattura un numero variabile di tipi (PEP 646). |
| **typeshed** | Repository ufficiale contenente stubs per la libreria standard e librerie di terze parti. |
| **Union** | Tipo che indica che un valore puo essere uno tra diversi tipi. In Python 3.10+, sostituito da `X | Y`. |

---

> **Riepilogo**: I type hints trasformano Python da un linguaggio puramente dinamico a uno con un sistema di tipi **graduale** (gradual typing). Non e necessario annotare tutto il codice in una volta: si puo iniziare dalle parti piu critiche e aumentare la copertura nel tempo. Strumenti come mypy, pyright e pytype verificano la coerenza delle annotazioni senza mai eseguire il codice, individuando intere classi di bug prima che raggiungano la produzione. Combinati con un buon supporto IDE, i type hints migliorano significativamente la produttivita, la leggibilita e la manutenibilita del codice Python.
