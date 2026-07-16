# Tutorial 09 — Type Hints e Mypy: Dal Principiante all'Esperto

> **Companion a:** `09-type-hints-e-mypy.md`
> **Scope:** PEP 484/604/612/673, TypeVar, Generic, Protocol, Literal, TypedDict, mypy strict, pyright
> **Prerequisiti:** `tutorial_02_oop.md`, `tutorial_01_fondamenti_linguaggio.md`
> **Durata stimata:** 15-20 ore
> **Versione Python:** 3.12+ (usa `from __future__ import annotations` per compatibilità 3.10)

---

## Indice

- [Parte A — Basi: annotazioni di tipo fondamentali](#parte-a--basi)
- [Parte B — Comprensione profonda: sistema dei tipi avanzato](#parte-b--comprensione-profonda)
- [Parte C — Esercizi pratici guidati](#parte-c--esercizi-pratici-guidati)
- [Parte D — Mypy e Pyright in produzione](#parte-d--mypy-e-pyright-in-produzione)
- [Parte E — Riepilogo e prossimi passi](#parte-e--riepilogo-e-prossimi-passi)

---

## Mappa concettuale

```
Sistema dei tipi Python
│
├── Tipi semplici
│   ├── int, float, str, bool, bytes
│   ├── None (per return void)
│   └── Any (escape hatch — evitare)
│
├── Tipi composti (Python 3.9+ senza import)
│   ├── list[str], dict[str, int], set[float]
│   ├── tuple[int, str, float]  (fisso)
│   ├── tuple[int, ...]         (variabile omogenea)
│   └── X | Y  (union, Python 3.10+)
│
├── typing module
│   ├── Optional[X]  → X | None
│   ├── Union[X, Y]  → X | Y  (legacy)
│   ├── Callable[[Arg1, Arg2], Ret]
│   ├── TypeVar, Generic — tipi generici
│   ├── Protocol — structural subtyping
│   ├── TypedDict — dict strutturato
│   ├── Literal — valore esatto
│   ├── Final — costante
│   ├── ClassVar — attributo di classe
│   └── TypeAlias — alias di tipo
│
├── PEP più recenti
│   ├── PEP 604 (3.10) — X | Y union syntax
│   ├── PEP 612 (3.10) — ParamSpec
│   ├── PEP 673 (3.11) — Self type
│   ├── PEP 675 (3.11) — LiteralString
│   └── PEP 695 (3.12) — type X = ... syntax
│
└── Type checkers
    ├── mypy — standard, configurabile
    └── pyright — usato da Pylance/VS Code
```

---

# Parte A — Basi

---

## A1. Perché i type hints?

> **Analogia:** Il codice Python senza type hints è come un magazzino senza etichette — funziona, ma trovare il prodotto giusto richiede aprire ogni scatola. I type hints sono le etichette: non cambiano il contenuto, ma rendono tutto trovabile a colpo d'occhio.

Python è a tipizzazione dinamica — il tipo viene determinato a runtime. I type hints (PEP 484, Python 3.5+) aggiungono annotazioni **opzionali** che:
- Documentano l'interfaccia senza scrivere docstring ripetitive
- Permettono ai type checker (mypy, pyright) di trovare bug prima dell'esecuzione
- Abilitano autocompletamento intelligente negli IDE
- Rendono il refactoring sicuro

**I type hints non influenzano l'esecuzione** — Python li ignora a runtime (salvo usi espliciti con `get_type_hints()`).

```python
# Senza type hints — cosa aspettarsi da process()?
def process(data, config, callback):
    ...

# Con type hints — immediatamente chiaro
def process(
    data: list[dict[str, str]],
    config: dict[str, int],
    callback: Callable[[str], None],
) -> list[str]:
    ...
```

---

## A2. Annotazioni base

```python
# Variabili
nome: str = "Anna"
eta: int = 30
saldo: float = 1500.50
attivo: bool = True
dati: bytes = b"\x00\xFF"

# Funzioni
def saluta(nome: str) -> str:
    return f"Ciao, {nome}!"

def somma(a: int, b: int) -> int:
    return a + b

def stampa(messaggio: str) -> None:  # None = void
    print(messaggio)

# Python 3.9+ — tipi built-in come generici
def inverti(lista: list[int]) -> list[int]:
    return lista[::-1]

def conta(testo: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for char in testo:
        result[char] = result.get(char, 0) + 1
    return result

# Tuple — tipo fisso con tipi posizionali
Coordinata = tuple[float, float]

def distanza(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5

# Tuple omogenea — lunghezza variabile
def media(valori: tuple[float, ...]) -> float:
    return sum(valori) / len(valori)
```

---

## A3. Optional e Union

```python
from __future__ import annotations  # abilita le string annotations per compatibilità 3.10

# Python 3.10+ — sintassi | (PEP 604)
def trova_utente(id: int) -> dict[str, str] | None:
    """Restituisce l'utente o None se non trovato."""
    ...

# Python 3.9 e precedenti — Optional da typing
from typing import Optional
def trova_utente_legacy(id: int) -> Optional[dict[str, str]]:
    ...

# Union con più tipi
def converti(valore: int | float | str) -> float:
    return float(valore)

# Pattern comune: controllare None prima di usare
def lunghezza_sicura(s: str | None) -> int:
    if s is None:
        return 0
    return len(s)   # qui mypy sa che s è str
```

---

## A4. Callable, Sequence, Mapping

```python
from collections.abc import Callable, Sequence, Mapping, Iterable, Iterator

# Callable[[TipiArgs], TipoReturn]
def applica(func: Callable[[int], str], valore: int) -> str:
    return func(valore)

def trasforma_lista(
    dati: list[int],
    funzione: Callable[[int], int]
) -> list[int]:
    return [funzione(x) for x in dati]

# Callable senza argomenti
def esegui(azione: Callable[[], None]) -> None:
    azione()

# Sequence — qualsiasi sequenza indicizzabile (list, tuple, str...)
def primo_elemento(seq: Sequence[str]) -> str | None:
    return seq[0] if seq else None

# Mapping — dict-like
def configura(opzioni: Mapping[str, str]) -> None:
    for chiave, valore in opzioni.items():
        print(f"  {chiave} = {valore}")

# Iterable e Iterator
def prendi_n(it: Iterable[int], n: int) -> list[int]:
    return [x for x, _ in zip(it, range(n))]

def genera_quadrati(n: int) -> Iterator[int]:
    for i in range(n):
        yield i ** 2
```

---

## A5. Final, ClassVar, Literal

```python
from typing import Final, ClassVar, Literal

# Final — costante che non può essere riassegnata
MAX_TENTATIVI: Final[int] = 3
URL_BASE: Final = "https://api.example.com"   # tipo inferito

# ClassVar — attributo di classe (non di istanza)
class Configurazione:
    _istanza_globale: ClassVar["Configurazione | None"] = None
    MAX_CONNESSIONI: ClassVar[int] = 10

    def __init__(self, host: str):
        self.host = host   # attributo di istanza — NO ClassVar

# Literal — valore esatto tra un insieme finito
Direzione = Literal["nord", "sud", "est", "ovest"]
Livello = Literal[1, 2, 3, 4, 5]
ModalitaHTTP = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

def muovi(direzione: Direzione, passi: int) -> None:
    print(f"Muovo {passi} passi verso {direzione}")

def imposta_livello(livello: Livello) -> None:
    print(f"Livello: {livello}")

muovi("nord", 5)     # OK
# muovi("sopra", 5) # mypy error: Argument 1 ... has incompatible type "Literal['sopra']"

# TypeAlias — alias di tipo esplicito (Python 3.10+)
from typing import TypeAlias
Matrice: TypeAlias = list[list[float]]
# Python 3.12+: type Matrice = list[list[float]]

def trasponi(m: Matrice) -> Matrice:
    return [list(riga) for riga in zip(*m)]
```

---

## A6. TypedDict: dizionari strutturati

```python
from typing import TypedDict, NotRequired

class IndirizzoDict(TypedDict):
    via: str
    citta: str
    cap: str
    paese: str

class UtenteDict(TypedDict):
    id: int
    nome: str
    email: str
    indirizzo: NotRequired[IndirizzoDict]  # campo opzionale

def crea_utente(nome: str, email: str) -> UtenteDict:
    return {"id": 0, "nome": nome, "email": email}

# Alternativa funzionale — utile per creare dinamicamente
Config = TypedDict("Config", {"host": str, "porta": int, "debug": bool})

# TypedDict con total=False — tutti i campi opzionali
class AggiornamentoUtente(TypedDict, total=False):
    nome: str
    email: str
    attivo: bool

def aggiorna(id: int, dati: AggiornamentoUtente) -> None:
    print(f"Aggiorno utente {id} con: {dati}")

aggiorna(1, {"email": "nuova@mail.com"})  # OK — solo email aggiornata
```

---

# Parte B — Comprensione profonda

---

## B1. TypeVar e Generic

```python
from typing import TypeVar, Generic

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Funzione generica — T viene inferito dal tipo dell'argomento
def primo(lista: list[T]) -> T | None:
    return lista[0] if lista else None

risultato_str = primo(["a", "b", "c"])   # mypy inferisce str | None
risultato_int = primo([1, 2, 3])          # mypy inferisce int | None

# TypeVar con bound — T deve essere una sottoclasse di Comparable
from typing import SupportsLessThan

Ordinabile = TypeVar("Ordinabile", bound="SupportsLessThan")

def massimo(a: T, b: T) -> T:
    return a if a > b else b   # type: ignore  (operatore > non garantito per T generico)

# Classe generica
class Pila(Generic[T]):
    def __init__(self) -> None:
        self._elementi: list[T] = []

    def push(self, elemento: T) -> None:
        self._elementi.append(elemento)

    def pop(self) -> T:
        if not self._elementi:
            raise IndexError("Pila vuota")
        return self._elementi.pop()

    def peek(self) -> T | None:
        return self._elementi[-1] if self._elementi else None

    def __len__(self) -> int:
        return len(self._elementi)


pila_int: Pila[int] = Pila()
pila_int.push(1)
pila_int.push(2)
print(pila_int.pop())   # int

pila_str: Pila[str] = Pila()
pila_str.push("ciao")
# pila_str.push(42)   # mypy error: Argument 1 ... has incompatible type "int"; expected "str"
```

```python
# Classe generica con due TypeVar
class Coppia(Generic[K, V]):
    def __init__(self, chiave: K, valore: V) -> None:
        self.chiave = chiave
        self.valore = valore

    def scambia(self) -> "Coppia[V, K]":
        return Coppia(self.valore, self.chiave)

    def __repr__(self) -> str:
        return f"Coppia({self.chiave!r}, {self.valore!r})"


c: Coppia[str, int] = Coppia("età", 30)
c_inv = c.scambia()   # tipo: Coppia[int, str]
```

---

## B2. Protocol per type checking strutturale

```python
from typing import Protocol, runtime_checkable

# Protocol — definisce un'interfaccia strutturale
class Comparabile(Protocol):
    def __lt__(self, altro: "Comparabile") -> bool: ...
    def __eq__(self, altro: object) -> bool: ...

# Funzione che accetta qualsiasi tipo Comparabile
def ordina_e_dedup(elementi: list[T]) -> list[T]:
    return sorted(set(elementi))

# Protocol con attributi
class HasNome(Protocol):
    nome: str
    cognome: str

    def nome_completo(self) -> str: ...

# Protocol generico
class Repository(Protocol[T]):
    def trova(self, id: int) -> T | None: ...
    def salva(self, entita: T) -> None: ...
    def elimina(self, id: int) -> bool: ...
    def lista_tutti(self) -> list[T]: ...

# Implementazione — non richiede ereditarietà
class UtenteRepo:
    def __init__(self) -> None:
        self._store: dict[int, dict] = {}

    def trova(self, id: int) -> dict | None:
        return self._store.get(id)

    def salva(self, entita: dict) -> None:
        self._store[entita["id"]] = entita

    def elimina(self, id: int) -> bool:
        return self._store.pop(id, None) is not None

    def lista_tutti(self) -> list[dict]:
        return list(self._store.values())
```

---

## B3. Self, ParamSpec, Concatenate

```python
from typing import Self  # Python 3.11+

class Builder:
    def __init__(self) -> None:
        self._params: dict[str, str] = {}

    def set(self, chiave: str, valore: str) -> Self:
        """Self garantisce che il tipo di ritorno sia la classe concreta, non Builder."""
        self._params[chiave] = valore
        return self

    def build(self) -> dict[str, str]:
        return dict(self._params)


class QueryBuilder(Builder):
    def where(self, condizione: str) -> Self:
        self._params["where"] = condizione
        return self

# Self garantisce che QueryBuilder.set() ritorni QueryBuilder, non Builder
qb = QueryBuilder().set("tabella", "utenti").where("età > 18")
print(qb.build())   # {'tabella': 'utenti', 'where': 'età > 18'}
```

```python
from typing import ParamSpec, Concatenate
from collections.abc import Callable

P = ParamSpec("P")

# Decoratore che preserva la firma della funzione decorata
def con_log(func: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"Chiamo {func.__name__}")
        risultato = func(*args, **kwargs)
        print(f"Fine {func.__name__}: {risultato!r}")
        return risultato
    return wrapper

@con_log
def somma(a: int, b: int) -> int:
    return a + b

somma(3, 4)   # type checker sa che somma accetta (int, int) → int
```

---

## B4. Narrowing e type guards

Il type narrowing è il processo con cui il type checker restringe il tipo di una variabile in base al flusso del codice:

```python
def processa(valore: int | str | None) -> str:
    # Narrowing con isinstance
    if isinstance(valore, int):
        return str(valore * 2)     # qui valore: int
    if isinstance(valore, str):
        return valore.upper()      # qui valore: str
    return "nessun valore"         # qui valore: None

# Narrowing con assert
def richiede_stringa(valore: str | None) -> str:
    assert valore is not None, "valore non può essere None"
    return valore.upper()          # mypy sa che valore è str

# TypeGuard — funzioni di narrowing custom
from typing import TypeGuard

def è_lista_str(lista: list) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in lista)

def processa_lista(dati: list[object]) -> None:
    if è_lista_str(dati):
        for s in dati:    # mypy sa: s è str
            print(s.upper())
```

---

## B5. Overload

```python
from typing import overload

# overload permette firme multiple per la stessa funzione
@overload
def converti(valore: int) -> str: ...
@overload
def converti(valore: str) -> int: ...
@overload
def converti(valore: float) -> str: ...

def converti(valore: int | str | float) -> str | int:
    if isinstance(valore, (int, float)):
        return str(valore)
    return int(valore)

# Il type checker vede il tipo specifico in base all'argomento
risultato1: str = converti(42)       # mypy sa: str
risultato2: int = converti("42")     # mypy sa: int
```

---

## B6. Annotazioni su dataclass e NamedTuple

```python
from dataclasses import dataclass, field
from typing import NamedTuple, ClassVar

@dataclass
class PuntoAnnotato:
    x: float
    y: float
    etichetta: str = ""
    _cache: ClassVar[dict[tuple[float, float], float]] = {}

    def distanza_dall_origine(self) -> float:
        chiave = (self.x, self.y)
        if chiave not in PuntoAnnotato._cache:
            PuntoAnnotato._cache[chiave] = (self.x**2 + self.y**2) ** 0.5
        return PuntoAnnotato._cache[chiave]


# NamedTuple tipizzata — immutabile e più leggera di dataclass
class Coordinata(NamedTuple):
    lat: float
    lon: float
    altitudine: float = 0.0

    def come_tupla(self) -> tuple[float, float]:
        return (self.lat, self.lon)


roma = Coordinata(41.9028, 12.4964)
print(roma.lat)      # 41.9028
lat, lon, alt = roma   # unpack funziona
```

---

# Parte C — Esercizi pratici guidati

---

## C1. Esercizio: tipizza una libreria esistente

Dato questo codice non tipizzato, aggiungere le annotazioni corrette:

```python
# Prima — senza type hints
def carica_config(percorso):
    import json
    with open(percorso) as f:
        return json.load(f)

def valida_utente(utente):
    errori = []
    if not utente.get("nome"):
        errori.append("nome obbligatorio")
    if "@" not in utente.get("email", ""):
        errori.append("email non valida")
    return errori

def trasforma_eventi(eventi, callback):
    return [callback(e) for e in eventi]
```

```python
# Dopo — con type hints corretti
import json
from pathlib import Path
from collections.abc import Callable

ConfigDict = dict[str, str | int | bool | list | dict]

def carica_config(percorso: str | Path) -> ConfigDict:
    with open(percorso) as f:
        return json.load(f)

def valida_utente(utente: dict[str, str]) -> list[str]:
    errori: list[str] = []
    if not utente.get("nome"):
        errori.append("nome obbligatorio")
    if "@" not in utente.get("email", ""):
        errori.append("email non valida")
    return errori

E = TypeVar("E")
R = TypeVar("R")

def trasforma_eventi(eventi: list[E], callback: Callable[[E], R]) -> list[R]:
    return [callback(e) for e in eventi]
```

---

## C2. Implementare un Result type

Pattern funzionale per gestire errori senza eccezioni:

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, NoReturn

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Ok(Generic[T]):
    valore: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def map(self, func: Callable[[T], U]) -> "Ok[U]":
        return Ok(func(self.valore))

    def unwrap(self) -> T:
        return self.valore

    def unwrap_or(self, default: T) -> T:
        return self.valore


@dataclass(frozen=True)
class Err(Generic[E]):
    errore: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def map(self, func: Callable) -> "Err[E]":
        return self

    def unwrap(self) -> NoReturn:
        raise ValueError(f"Chiamato unwrap() su Err: {self.errore}")

    def unwrap_or(self, default: T) -> T:
        return default


Result = Ok[T] | Err[E]


def dividi(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("divisione per zero")
    return Ok(a / b)

def parse_intero(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"non è un intero: {s!r}")


# Uso
r = dividi(10, 2)
match r:
    case Ok(valore=v):
        print(f"Risultato: {v}")
    case Err(errore=e):
        print(f"Errore: {e}")

# Chaining
risultato = parse_intero("42").map(lambda x: x * 2)
print(risultato.unwrap())   # 84
```

---

## C3. Sistema di validazione tipizzato

```python
from __future__ import annotations
from typing import TypeVar, Generic, Protocol, runtime_checkable
from dataclasses import dataclass
from collections.abc import Callable

T = TypeVar("T")

@runtime_checkable
class Validatore(Protocol[T]):
    def valida(self, valore: T) -> list[str]: ...

@dataclass
class ValidatoreStringa:
    min_len: int = 0
    max_len: int = 1000
    pattern: str | None = None

    def valida(self, valore: str) -> list[str]:
        import re
        errori: list[str] = []
        if len(valore) < self.min_len:
            errori.append(f"troppo corto (min {self.min_len})")
        if len(valore) > self.max_len:
            errori.append(f"troppo lungo (max {self.max_len})")
        if self.pattern and not re.fullmatch(self.pattern, valore):
            errori.append(f"non corrisponde al pattern {self.pattern!r}")
        return errori

@dataclass
class ValidatoreNumero:
    minimo: float | None = None
    massimo: float | None = None

    def valida(self, valore: float) -> list[str]:
        errori: list[str] = []
        if self.minimo is not None and valore < self.minimo:
            errori.append(f"deve essere >= {self.minimo}")
        if self.massimo is not None and valore > self.massimo:
            errori.append(f"deve essere <= {self.massimo}")
        return errori

class Schema(Generic[T]):
    def __init__(self, validatori: list[Validatore[T]]) -> None:
        self._validatori = validatori

    def valida(self, valore: T) -> list[str]:
        errori: list[str] = []
        for v in self._validatori:
            errori.extend(v.valida(valore))
        return errori

    def è_valido(self, valore: T) -> bool:
        return len(self.valida(valore)) == 0


schema_nome = Schema([ValidatoreStringa(min_len=2, max_len=50)])
schema_eta = Schema([ValidatoreNumero(minimo=0, massimo=150)])

print(schema_nome.valida("A"))         # ['troppo corto (min 2)']
print(schema_nome.valida("Anna"))      # []
print(schema_eta.valida(200))          # ['deve essere <= 150']
print(schema_eta.è_valido(25))         # True
```

---

# Parte D — Mypy e Pyright in produzione

---

## D1. Configurare mypy

File `mypy.ini` o sezione `[tool.mypy]` in `pyproject.toml`:

```ini
[mypy]
python_version = 3.12
strict = true
# strict abilita tutte queste opzioni:
# --disallow-untyped-defs
# --disallow-incomplete-defs
# --check-untyped-defs
# --disallow-untyped-decorators
# --warn-redundant-casts
# --warn-unused-ignores
# --warn-return-any
# --no-implicit-reexport
# --strict-equality

# Ignora librerie senza stub
[[tool.mypy.overrides]]
module = ["requests.*", "boto3.*"]
ignore_missing_imports = true
```

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
```

---

## D2. Errori mypy comuni e soluzioni

```python
# Errore 1: "Function is missing a return type annotation"
# Fix: aggiungere -> tipo
def foo():  # error
    pass

def foo() -> None:  # OK
    pass

# Errore 2: "Argument has incompatible type"
def accetta_int(n: int) -> None:
    pass

accetta_int("ciao")  # error: Argument 1 has incompatible type "str"; expected "int"

# Errore 3: "Item has no attribute"
def usa(x: int | str) -> None:
    x.upper()  # error: Item "int" of "int | str" has no attribute "upper"

def usa_corretto(x: int | str) -> None:
    if isinstance(x, str):
        x.upper()  # OK — narrowing

# Errore 4: "Incompatible return value type"
def ritorna_int() -> int:
    return "ciao"  # error

# Errore 5: "Cannot determine type of"
def calcola():
    if True:
        return 1
    # nessun return nell'altro ramo → tipo implicito None
    # mypy: "Missing return statement"

# Sopprimere errori noti (con codice errore)
x: int = "ciao"  # type: ignore[assignment]

# cast — forzare un tipo senza runtime check
from typing import cast
dati: object = ottieni_dati()
lista_str = cast(list[str], dati)  # mypy crede che sia list[str]
```

---

## D3. Stub file (.pyi)

I file `.pyi` forniscono type hints per moduli senza annotazioni:

```python
# math_utils.pyi — stub per math_utils.py
from typing import overload

@overload
def converti(valore: int) -> str: ...
@overload
def converti(valore: str) -> int: ...

def somma_lista(numeri: list[float]) -> float: ...
def normalizza(valori: list[float], min_v: float = ..., max_v: float = ...) -> list[float]: ...
```

Per le librerie di terze parti, usare i pacchetti `types-*`:
```bash
pip install types-requests types-PyYAML types-redis
```

---

## D4. Py.typed e distribuzione

Per indicare che un pacchetto supporta i type hints:

```
mio_pacchetto/
├── __init__.py
├── py.typed          ← file vuoto, segnala che il pacchetto è typed
├── modulo_a.py
└── modulo_b.py
```

```toml
# pyproject.toml
[tool.setuptools.package-data]
"mio_pacchetto" = ["py.typed"]
```

---

## D5. Pattern avanzati: NewType e annotazioni runtime

```python
from typing import NewType

# NewType — crea un tipo distinto a livello statico (nessun overhead runtime)
UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def trova_ordini(user_id: UserId) -> list[OrderId]:
    ...

uid = UserId(42)
oid = OrderId(100)

# trova_ordini(oid)   # mypy error: incompatible type
trova_ordini(uid)      # OK

# Accedere alle annotazioni a runtime
import inspect
from typing import get_type_hints

class Servizio:
    def processa(self, dati: list[str], max_n: int = 10) -> dict[str, int]:
        return {}

hints = get_type_hints(Servizio.processa)
print(hints)
# {'dati': list[str], 'max_n': int, 'return': dict[str, int]}
```

---

# Parte E — Riepilogo e prossimi passi

## Riepilogo

| Concetto | Sintassi | Quando usare |
|---|---|---|
| Tipo semplice | `x: int` | Sempre |
| Opzionale | `x: str \| None` | Valore che può mancare |
| Union | `x: int \| str` | Tipi multipli ammessi |
| Lista tipizzata | `x: list[str]` | Collezione omogenea |
| Dict tipizzato | `x: dict[str, int]` | Map chiave→valore |
| TypeVar | `T = TypeVar("T")` | Funzioni/classi generiche |
| Generic | `class C(Generic[T])` | Classi generiche |
| Protocol | `class P(Protocol)` | Duck typing statico |
| TypedDict | `class C(TypedDict)` | Dict con schema fisso |
| Literal | `Literal["a", "b"]` | Valore da insieme finito |
| Final | `x: Final = 42` | Costante non riassegnabile |
| Self | `def f(self) -> Self` | Metodi che ritornano self |
| TypeAlias | `type X = list[str]` | Alias leggibile |

## Checklist mypy strict

- [ ] Tutte le funzioni pubbliche hanno annotazioni di return
- [ ] Nessun parametro non tipizzato nelle funzioni pubbliche
- [ ] Nessun `Any` non giustificato
- [ ] Ogni `# type: ignore` ha il codice di errore
- [ ] `py.typed` presente per i pacchetti distribuiti
- [ ] Stub installati per le librerie di terze parti usate

## Prossimi passi

- `tutorial_08_testing.md` — pytest con tipizzazione, fixture tipizzate
- `tutorial_11_web_framework.md` — FastAPI e Pydantic sfruttano pesantemente i type hints
- `tutorial_29_pydantic.md` — validazione runtime basata su type hints
