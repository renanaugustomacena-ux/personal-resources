---
corso: "Programmazione Python"
fase: "4 — Progettazione e Architettura"
modulo: "21"
titolo: "Design Patterns in Python"
versione: "Python 3.12+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "07 — OOP"
  - "03 — Funzioni e Scope"
  - "06 — Moduli e Pacchetti"
obiettivi:
  - "Applicare i pattern creazionali GoF in modo Pythonico"
  - "Implementare pattern strutturali con decorator, descriptor e context manager"
  - "Utilizzare pattern comportamentali sfruttando funzioni first-class e generatori"
  - "Riconoscere pattern Python-specifici (duck typing, mixin, metaclassi)"
  - "Identificare anti-pattern e sapere quando NON usare un pattern"
  - "Scegliere il pattern appropriato in base al problema reale"
tag: [design-patterns, GoF, creational, structural, behavioral, Python-patterns, SOLID]
---

# Design Patterns in Python — Guida Completa

> **Modulo 21** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [OOP](07-oop.md), [Funzioni e Scope](03-funzioni-scope.md), [Moduli e Pacchetti](06-moduli-pacchetti.md)
>
> Al termine di questo modulo saprai:
> 1. Applicare i pattern creazionali GoF (Singleton, Factory, Builder, Prototype) in Python
> 2. Implementare pattern strutturali (Adapter, Decorator, Facade, Proxy, Composite)
> 3. Utilizzare pattern comportamentali (Observer, Strategy, Command, Iterator, State)
> 4. Riconoscere e sfruttare pattern Python-specifici (duck typing, mixin, metaclassi)
> 5. Identificare anti-pattern comuni e le relative soluzioni
> 6. Valutare quando un pattern aggiunge valore e quando aggiunge solo complessita
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **Python ha first-class function: pattern come Strategy diventano funcs.**
2. **Singleton: usa modulo Python (gia singleton).**
3. **Factory > __init__ logic complex.**
4. **Observer pattern: signal libraries (blinker, signalslot).**


## Indice

1. [Panoramica](#panoramica)
2. [Pattern Creazionali](#pattern-creazionali)
3. [Pattern Strutturali](#pattern-strutturali)
4. [Pattern Comportamentali](#pattern-comportamentali)
5. [Pattern Python-Specifici](#pattern-python-specifici)
6. [Anti-Pattern e Code Smells](#anti-pattern)
7. [Principi SOLID in Python](#principi-solid-in-python)
8. [Dependency Injection](#dependency-injection)
9. [Pattern Funzionali](#pattern-funzionali)
10. [Pattern di Concorrenza](#pattern-di-concorrenza)
11. [Best Practices](#best-practices)

---

## Panoramica

I **design patterns** (schemi di progettazione) sono soluzioni ricorrenti e consolidate a problemi comuni che si presentano nella progettazione del software. Non sono codice pronto da copiare, ma piuttosto *modelli concettuali* che guidano lo sviluppatore verso scelte architetturali robuste, manutenibili e scalabili. Il concetto fu formalizzato nel 1994 dal celebre libro *"Design Patterns: Elements of Reusable Object-Oriented Software"* scritto dalla cosiddetta **Gang of Four** (GoF) — Erich Gamma, Richard Helm, Ralph Johnson e John Vlissides — che catalogò 23 pattern fondamentali suddivisi in tre categorie.

Le tre categorie classiche sono:

- **Pattern Creazionali** — si occupano dei meccanismi di creazione degli oggetti, cercando di rendere il sistema indipendente dal modo in cui gli oggetti vengono creati, composti e rappresentati. Esempi: Singleton, Factory Method, Abstract Factory, Builder, Prototype.
- **Pattern Strutturali** — riguardano la composizione di classi e oggetti in strutture più ampie, mantenendo la flessibilità e l'efficienza del sistema. Esempi: Adapter, Decorator, Facade, Proxy, Composite.
- **Pattern Comportamentali** — si concentrano sulla comunicazione e l'interazione tra oggetti, definendo come le responsabilità sono distribuite e come gli oggetti collaborano. Esempi: Observer, Strategy, Command, Iterator, Template Method, State, Chain of Responsibility.

### Considerazioni specifiche per Python

Python possiede caratteristiche che influenzano profondamente il modo in cui i design patterns vengono implementati. In molti casi, pattern che in Java o C++ richiedono strutture elaborate diventano in Python straordinariamente semplici — talvolta riducendosi a poche righe di codice o addirittura a funzionalità già integrate nel linguaggio.

Le caratteristiche di Python che maggiormente influenzano i design patterns sono:

- **Funzioni come oggetti di prima classe** — le funzioni possono essere assegnate a variabili, passate come argomenti e restituite da altre funzioni. Questo rende superflue molte classi usate in altri linguaggi solo per incapsulare un singolo comportamento (ad esempio, il pattern Strategy può essere implementato con una semplice funzione).
- **Duck typing** — Python non richiede che un oggetto appartenga a una specifica gerarchia di classi per essere utilizzato in un certo contesto; è sufficiente che risponda ai metodi necessari (*"se cammina come un'anatra e starnazza come un'anatra, allora è un'anatra"*). Questo riduce drasticamente la necessità di interfacce formali.
- **Natura dinamica** — attributi e metodi possono essere aggiunti, modificati o rimossi a runtime. Le classi stesse sono oggetti e possono essere manipolate dinamicamente.
- **Protocolli e dunder methods** — il modello a oggetti di Python si basa su protocolli impliciti (iterazione, confronto, accesso agli attributi) che permettono di implementare molti pattern in modo idiomatico.
- **Moduli come singleton naturali** — un modulo Python viene importato una sola volta e il suo stato è condiviso globalmente, fungendo da singleton naturale.

L'approccio corretto in Python non è tradurre pedissequamente i pattern GoF da Java, ma comprenderne l'*intento* e trovare la soluzione più *Pythonic* — cioè quella che sfrutta le peculiarità del linguaggio per ottenere lo stesso risultato con meno complessità.

---

## Pattern Creazionali

I pattern creazionali astraggono il processo di istanziazione degli oggetti, rendendo il sistema più flessibile riguardo a *cosa* viene creato, *chi* lo crea, *come* e *quando*.

### Singleton

Il **Singleton** garantisce che di una determinata classe esista al massimo una sola istanza nell'intero programma, fornendo un punto di accesso globale a quell'istanza. È utile per risorse condivise come pool di connessioni, configurazioni globali o registri centralizzati.

**Approccio Pythonico: singleton a livello di modulo**

Il modo più semplice e idiomatico in Python è utilizzare un modulo. Poiché ogni modulo viene caricato una sola volta dall'interprete, le variabili definite al suo interno sono di fatto singleton:

```python
# config.py — singleton a livello di modulo
class _Configurazione:
    def __init__(self):
        self.debug = False
        self.database_url = "sqlite:///app.db"
        self.log_level = "INFO"

    def da_dizionario(self, dati):
        for chiave, valore in dati.items():
            setattr(self, chiave, valore)

# Istanza unica — importata ovunque come:
# from config import configurazione
configurazione = _Configurazione()
```

Ogni modulo che importa `configurazione` ottiene lo stesso identico oggetto, senza alcun meccanismo aggiuntivo.

**Override di `__new__`**

Quando si desidera una classe esplicitamente singleton, si può sovrascrivere il metodo `__new__`, che controlla la creazione dell'istanza:

```python
class Singleton:
    _istanza = None

    def __new__(cls, *args, **kwargs):
        if cls._istanza is None:
            cls._istanza = super().__new__(cls)
        return cls._istanza

    def __init__(self, valore=None):
        # Attenzione: __init__ viene chiamato a ogni "creazione"
        if not hasattr(self, '_inizializzato'):
            self.valore = valore
            self._inizializzato = True

a = Singleton("primo")
b = Singleton("secondo")
print(a is b)        # True
print(a.valore)      # "primo" — non sovrascritto
```

**Singleton con metaclass**

Una metaclass permette di controllare la creazione di istanze a livello di classe, offrendo una soluzione riutilizzabile:

```python
class SingletonMeta(type):
    _istanze = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._istanze:
            cls._istanze[cls] = super().__call__(*args, **kwargs)
        return cls._istanze[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self, url):
        self.url = url

db1 = Database("postgresql://localhost/app")
db2 = Database("mysql://localhost/altro")
print(db1 is db2)    # True
print(db1.url)       # "postgresql://localhost/app"
```

**Singleton con decorator**

Un decorator di classe offre un approccio leggibile e modulare:

```python
def singleton(cls):
    istanze = {}
    def ottieni_istanza(*args, **kwargs):
        if cls not in istanze:
            istanze[cls] = cls(*args, **kwargs)
        return istanze[cls]
    return ottieni_istanza

@singleton
class CacheGlobale:
    def __init__(self):
        self._dati = {}

    def imposta(self, chiave, valore):
        self._dati[chiave] = valore

    def ottieni(self, chiave):
        return self._dati.get(chiave)
```

### Factory Method

Il **Factory Method** definisce un'interfaccia per la creazione di un oggetto, ma lascia alle sottoclassi la decisione su quale classe concreta istanziare. Il metodo factory *delega* la creazione dell'oggetto alle classi derivate.

```python
from abc import ABC, abstractmethod

class Notifica(ABC):
    """Prodotto astratto."""
    @abstractmethod
    def invia(self, messaggio: str) -> None:
        pass

class NotificaEmail(Notifica):
    def invia(self, messaggio: str) -> None:
        print(f"[EMAIL] Invio: {messaggio}")

class NotificaSMS(Notifica):
    def invia(self, messaggio: str) -> None:
        print(f"[SMS] Invio: {messaggio}")

class NotificaPush(Notifica):
    def invia(self, messaggio: str) -> None:
        print(f"[PUSH] Invio: {messaggio}")

class ServizioNotifiche(ABC):
    """Creator astratto con factory method."""
    @abstractmethod
    def crea_notifica(self) -> Notifica:
        pass

    def notifica(self, messaggio: str) -> None:
        """Template method che utilizza il factory method."""
        notifica = self.crea_notifica()
        notifica.invia(messaggio)

class ServizioEmail(ServizioNotifiche):
    def crea_notifica(self) -> Notifica:
        return NotificaEmail()

class ServizioSMS(ServizioNotifiche):
    def crea_notifica(self) -> Notifica:
        return NotificaSMS()

class ServizioPush(ServizioNotifiche):
    def crea_notifica(self) -> Notifica:
        return NotificaPush()

# Utilizzo
servizio = ServizioEmail()
servizio.notifica("Benvenuto nella piattaforma!")
```

Un approccio più Pythonico utilizza un dizionario come registro di factory:

```python
class NotificaFactory:
    _registry = {
        "email": NotificaEmail,
        "sms": NotificaSMS,
        "push": NotificaPush,
    }

    @classmethod
    def crea(cls, tipo: str) -> Notifica:
        classe = cls._registry.get(tipo)
        if classe is None:
            raise ValueError(f"Tipo di notifica sconosciuto: {tipo}")
        return classe()

    @classmethod
    def registra(cls, tipo: str, classe: type) -> None:
        cls._registry[tipo] = classe

notifica = NotificaFactory.crea("email")
notifica.invia("Ordine confermato")
```

### Abstract Factory

L'**Abstract Factory** fornisce un'interfaccia per creare *famiglie di oggetti correlati* senza specificare le classi concrete. È utile quando un sistema deve essere indipendente da come i suoi prodotti vengono creati e composti.

```python
from abc import ABC, abstractmethod

# Prodotti astratti
class Pulsante(ABC):
    @abstractmethod
    def disegna(self) -> str:
        pass

class CampoTesto(ABC):
    @abstractmethod
    def disegna(self) -> str:
        pass

# Famiglia "Chiaro"
class PulsanteChiaro(Pulsante):
    def disegna(self) -> str:
        return "[Pulsante tema chiaro]"

class CampoTestoChiaro(CampoTesto):
    def disegna(self) -> str:
        return "[Campo testo tema chiaro]"

# Famiglia "Scuro"
class PulsanteScuro(Pulsante):
    def disegna(self) -> str:
        return "[Pulsante tema scuro]"

class CampoTestoScuro(CampoTesto):
    def disegna(self) -> str:
        return "[Campo testo tema scuro]"

# Factory astratta
class UIFactory(ABC):
    @abstractmethod
    def crea_pulsante(self) -> Pulsante:
        pass

    @abstractmethod
    def crea_campo_testo(self) -> CampoTesto:
        pass

class FactoryTemaChiaro(UIFactory):
    def crea_pulsante(self) -> Pulsante:
        return PulsanteChiaro()

    def crea_campo_testo(self) -> CampoTesto:
        return CampoTestoChiaro()

class FactoryTemaScuro(UIFactory):
    def crea_pulsante(self) -> Pulsante:
        return PulsanteScuro()

    def crea_campo_testo(self) -> CampoTesto:
        return CampoTestoScuro()

# Il codice client lavora con la factory astratta
def costruisci_interfaccia(factory: UIFactory):
    pulsante = factory.crea_pulsante()
    campo = factory.crea_campo_testo()
    print(pulsante.disegna())
    print(campo.disegna())

costruisci_interfaccia(FactoryTemaScuro())
```

### Builder

Il **Builder** separa la costruzione di un oggetto complesso dalla sua rappresentazione, permettendo di creare oggetti passo dopo passo. È particolarmente utile quando un oggetto ha molti parametri opzionali o configurazioni complesse.

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class QuerySQL:
    tabella: str = ""
    colonne: list[str] = field(default_factory=lambda: ["*"])
    condizioni: list[str] = field(default_factory=list)
    ordinamento: Optional[str] = None
    limite: Optional[int] = None

    def __str__(self) -> str:
        query = f"SELECT {', '.join(self.colonne)} FROM {self.tabella}"
        if self.condizioni:
            query += " WHERE " + " AND ".join(self.condizioni)
        if self.ordinamento:
            query += f" ORDER BY {self.ordinamento}"
        if self.limite:
            query += f" LIMIT {self.limite}"
        return query

class QueryBuilder:
    """Builder con fluent interface."""

    def __init__(self):
        self._query = QuerySQL()

    def da(self, tabella: str) -> "QueryBuilder":
        self._query.tabella = tabella
        return self

    def seleziona(self, *colonne: str) -> "QueryBuilder":
        self._query.colonne = list(colonne)
        return self

    def dove(self, condizione: str) -> "QueryBuilder":
        self._query.condizioni.append(condizione)
        return self

    def ordina_per(self, colonna: str) -> "QueryBuilder":
        self._query.ordinamento = colonna
        return self

    def limita(self, n: int) -> "QueryBuilder":
        self._query.limite = n
        return self

    def costruisci(self) -> QuerySQL:
        if not self._query.tabella:
            raise ValueError("La tabella è obbligatoria")
        return self._query

# Fluent interface — lettura naturale
query = (
    QueryBuilder()
    .da("utenti")
    .seleziona("nome", "email", "citta")
    .dove("eta > 18")
    .dove("attivo = true")
    .ordina_per("nome")
    .limita(50)
    .costruisci()
)
print(query)
# SELECT nome, email, citta FROM utenti WHERE eta > 18 AND attivo = true ORDER BY nome LIMIT 50
```

### Prototype

Il **Prototype** crea nuovi oggetti clonando un'istanza esistente, evitando il costo di una costruzione da zero. Python supporta nativamente questo pattern tramite il modulo `copy`.

```python
import copy

class Configurazione:
    def __init__(self, parametri: dict, sotto_config: list):
        self.parametri = parametri
        self.sotto_config = sotto_config

    def __copy__(self):
        """Copia superficiale personalizzata."""
        nuovo = self.__class__.__new__(self.__class__)
        nuovo.__dict__.update(self.__dict__)
        # I riferimenti interni puntano agli stessi oggetti
        return nuovo

    def __deepcopy__(self, memo):
        """Copia profonda personalizzata."""
        nuovo = self.__class__.__new__(self.__class__)
        memo[id(self)] = nuovo
        nuovo.parametri = copy.deepcopy(self.parametri, memo)
        nuovo.sotto_config = copy.deepcopy(self.sotto_config, memo)
        return nuovo

# Prototipo base
config_base = Configurazione(
    parametri={"debug": False, "log_level": "INFO"},
    sotto_config=[{"db": "sqlite"}, {"cache": "redis"}]
)

# Clonazione profonda — indipendente dall'originale
config_sviluppo = copy.deepcopy(config_base)
config_sviluppo.parametri["debug"] = True
config_sviluppo.parametri["log_level"] = "DEBUG"

# L'originale rimane intatto
print(config_base.parametri["debug"])  # False
```

La differenza tra `copy.copy()` (copia superficiale) e `copy.deepcopy()` (copia profonda) è cruciale: la copia superficiale condivide i riferimenti agli oggetti interni, mentre la copia profonda crea copie ricorsive di ogni oggetto annidato.

### Object Pool

L'**Object Pool** gestisce un insieme di oggetti pre-inizializzati pronti all'uso, evitando il costo ripetuto di creazione e distruzione. È particolarmente utile quando l'inizializzazione di un oggetto è costosa (connessioni di rete, thread, risorse di sistema) e gli oggetti vengono richiesti e rilasciati frequentemente.

```python
import threading
from collections import deque
from typing import TypeVar, Generic, Callable

T = TypeVar("T")

class ObjectPool(Generic[T]):
    """Pool generico thread-safe con dimensione minima e massima."""

    def __init__(
        self,
        factory: Callable[[], T],
        min_size: int = 2,
        max_size: int = 10,
        reset_fn: Callable[[T], None] | None = None,
    ):
        self._factory = factory
        self._max_size = max_size
        self._reset_fn = reset_fn or (lambda _: None)
        self._pool: deque[T] = deque()
        self._in_uso: int = 0
        self._lock = threading.Lock()

        # Pre-popola il pool con il minimo richiesto
        for _ in range(min_size):
            self._pool.append(self._factory())

    def acquisisci(self) -> T:
        """Preleva un oggetto dal pool o ne crea uno nuovo."""
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self._in_uso += 1
                return obj
            if self._in_uso < self._max_size:
                obj = self._factory()
                self._in_uso += 1
                return obj
        raise RuntimeError(
            f"Pool esaurito: {self._in_uso}/{self._max_size} oggetti in uso"
        )

    def rilascia(self, obj: T) -> None:
        """Restituisce un oggetto al pool dopo il reset."""
        with self._lock:
            self._reset_fn(obj)
            self._pool.append(obj)
            self._in_uso -= 1

    @property
    def disponibili(self) -> int:
        with self._lock:
            return len(self._pool)

    @property
    def in_uso(self) -> int:
        with self._lock:
            return self._in_uso
```

L'Object Pool si integra naturalmente con il context manager di Python per garantire il rilascio automatico:

```python
from contextlib import contextmanager

@contextmanager
def prendi_dal_pool(pool: ObjectPool[T]):
    """Context manager per acquisizione/rilascio automatico."""
    obj = pool.acquisisci()
    try:
        yield obj
    finally:
        pool.rilascia(obj)

# Esempio: pool di connessioni database simulate
class ConnessioneDB:
    _contatore = 0

    def __init__(self):
        ConnessioneDB._contatore += 1
        self.id = ConnessioneDB._contatore
        self.aperta = True

    def esegui(self, query: str) -> str:
        return f"[Conn-{self.id}] Risultato di: {query}"

    def reset(self) -> None:
        """Ripristina lo stato della connessione."""
        self.aperta = True

pool_connessioni = ObjectPool(
    factory=ConnessioneDB,
    min_size=3,
    max_size=10,
    reset_fn=lambda c: c.reset(),
)

# Utilizzo sicuro con context manager
with prendi_dal_pool(pool_connessioni) as conn:
    print(conn.esegui("SELECT * FROM utenti"))
# La connessione viene rilasciata automaticamente
```

Il pattern Object Pool è alla base di molte librerie Python di produzione: `sqlalchemy.pool`, `redis.ConnectionPool`, `urllib3.HTTPConnectionPool`. In applicazioni moderne ad alta concorrenza, è quasi sempre preferibile usare un pool di libreria consolidato piuttosto che implementarne uno da zero.

---

## Pattern Strutturali

I pattern strutturali si occupano di come classi e oggetti vengono composti per formare strutture più grandi, mantenendo la flessibilità del sistema.

### Adapter

L'**Adapter** converte l'interfaccia di una classe in un'interfaccia diversa attesa dal client. Permette a classi con interfacce incompatibili di collaborare. In Python si distinguono tre varianti principali.

**Object Adapter (composizione)**

```python
class SistemaLegacy:
    """Sistema esistente con interfaccia non compatibile."""
    def ottieni_dati_xml(self) -> str:
        return "<utente><nome>Alice</nome></utente>"

class ClienteModerno:
    """Il client si aspetta dati in formato dizionario."""
    def elabora(self, dati: dict) -> None:
        print(f"Elaborazione: {dati}")

class AdapterXMLVersDizionario:
    """Adapter che converte l'interfaccia XML in dizionario."""
    def __init__(self, sistema_legacy: SistemaLegacy):
        self._legacy = sistema_legacy

    def ottieni_dati(self) -> dict:
        xml = self._legacy.ottieni_dati_xml()
        # Parsing semplificato per l'esempio
        import xml.etree.ElementTree as ET
        radice = ET.fromstring(xml)
        return {figlio.tag: figlio.text for figlio in radice}

# Utilizzo
legacy = SistemaLegacy()
adapter = AdapterXMLVersDizionario(legacy)
dati = adapter.ottieni_dati()  # {"nome": "Alice"}
ClienteModerno().elabora(dati)
```

**Function Adapter (approccio Pythonico)**

In Python, un semplice callable può fungere da adapter senza bisogno di classi:

```python
def adapter_ordinamento(funzione_confronto):
    """Adatta una funzione di confronto vecchio stile a una key function."""
    import functools
    return functools.cmp_to_key(funzione_confronto)

def confronta_lunghezza(a, b):
    """Funzione di confronto vecchio stile (ritorna -1, 0, 1)."""
    return len(a) - len(b)

parole = ["Python", "è", "straordinario", "per", "i", "design", "patterns"]
ordinate = sorted(parole, key=adapter_ordinamento(confronta_lunghezza))
print(ordinate)  # ['è', 'i', 'per', 'Python', 'design', 'patterns', 'straordinario']
```

### Bridge

Il **Bridge** separa un'astrazione dalla sua implementazione, in modo che le due possano variare indipendentemente. A differenza dell'Adapter (che adatta un'interfaccia esistente), il Bridge viene progettato fin dall'inizio per disaccoppiare interfaccia e implementazione. È utile quando si ha una matrice di varianti: ad esempio, forme geometriche (cerchio, rettangolo) che possono essere renderizzate con motori diversi (SVG, Canvas, PDF).

```python
from abc import ABC, abstractmethod

# Implementazioni (la "piattaforma")
class MotoreRendering(ABC):
    @abstractmethod
    def disegna_cerchio(self, x: int, y: int, raggio: int) -> str:
        pass

    @abstractmethod
    def disegna_rettangolo(self, x: int, y: int, larghezza: int, altezza: int) -> str:
        pass

class MotoreSVG(MotoreRendering):
    def disegna_cerchio(self, x: int, y: int, raggio: int) -> str:
        return f'<circle cx="{x}" cy="{y}" r="{raggio}" />'

    def disegna_rettangolo(self, x: int, y: int, larghezza: int, altezza: int) -> str:
        return f'<rect x="{x}" y="{y}" width="{larghezza}" height="{altezza}" />'

class MotoreCanvas(MotoreRendering):
    def disegna_cerchio(self, x: int, y: int, raggio: int) -> str:
        return f"ctx.arc({x}, {y}, {raggio}, 0, 2*Math.PI); ctx.stroke();"

    def disegna_rettangolo(self, x: int, y: int, larghezza: int, altezza: int) -> str:
        return f"ctx.strokeRect({x}, {y}, {larghezza}, {altezza});"

# Astrazioni (le "forme")
class Forma(ABC):
    def __init__(self, motore: MotoreRendering):
        self._motore = motore

    @abstractmethod
    def disegna(self) -> str:
        pass

class Cerchio(Forma):
    def __init__(self, motore: MotoreRendering, x: int, y: int, raggio: int):
        super().__init__(motore)
        self.x = x
        self.y = y
        self.raggio = raggio

    def disegna(self) -> str:
        return self._motore.disegna_cerchio(self.x, self.y, self.raggio)

class Rettangolo(Forma):
    def __init__(self, motore: MotoreRendering, x: int, y: int, larghezza: int, altezza: int):
        super().__init__(motore)
        self.x = x
        self.y = y
        self.larghezza = larghezza
        self.altezza = altezza

    def disegna(self) -> str:
        return self._motore.disegna_rettangolo(
            self.x, self.y, self.larghezza, self.altezza
        )

# Le forme funzionano con qualsiasi motore senza modifiche
cerchio_svg = Cerchio(MotoreSVG(), 50, 50, 30)
cerchio_canvas = Cerchio(MotoreCanvas(), 50, 50, 30)
print(cerchio_svg.disegna())     # <circle cx="50" cy="50" r="30" />
print(cerchio_canvas.disegna())  # ctx.arc(50, 50, 30, 0, 2*Math.PI); ctx.stroke();
```

Senza il Bridge, servirebbero classi come `CerchioSVG`, `CerchioCanvas`, `RettangoloSVG`, `RettangoloCanvas` — una crescita combinatoria che diventa rapidamente ingestibile con M forme e N motori (M x N classi). Il Bridge mantiene le due gerarchie (forme e motori) completamente indipendenti, riducendo la complessità a M + N classi.

**Quando usare il Bridge vs l'Adapter:** l'Adapter viene applicato *dopo* la progettazione, per far collaborare interfacce incompatibili già esistenti. Il Bridge viene progettato *prima*, quando si prevede che astrazione e implementazione debbano evolversi indipendentemente. In Python, il Bridge si combina naturalmente con il dependency injection: il motore di rendering viene iniettato nella forma tramite il costruttore, e la stessa forma può essere utilizzata con motori diversi senza alcuna modifica.

### Decorator (Pattern)

Il **Decorator** (da non confondere con il decorator sintattico `@` di Python) aggiunge dinamicamente responsabilità a un oggetto, senza modificare la sua classe originale. Offre un'alternativa flessibile all'ereditarietà per estendere le funzionalità.

```python
from abc import ABC, abstractmethod

class Componente(ABC):
    @abstractmethod
    def costo(self) -> float:
        pass

    @abstractmethod
    def descrizione(self) -> str:
        pass

class CaffeBase(Componente):
    def costo(self) -> float:
        return 1.50

    def descrizione(self) -> str:
        return "Caffè base"

class DecoratoreCaffe(Componente):
    """Decorator base — avvolge un Componente."""
    def __init__(self, componente: Componente):
        self._componente = componente

    def costo(self) -> float:
        return self._componente.costo()

    def descrizione(self) -> str:
        return self._componente.descrizione()

class ConLatte(DecoratoreCaffe):
    def costo(self) -> float:
        return super().costo() + 0.50

    def descrizione(self) -> str:
        return super().descrizione() + " + latte"

class ConZucchero(DecoratoreCaffe):
    def costo(self) -> float:
        return super().costo() + 0.20

    def descrizione(self) -> str:
        return super().descrizione() + " + zucchero"

class ConPannaFresca(DecoratoreCaffe):
    def costo(self) -> float:
        return super().costo() + 0.80

    def descrizione(self) -> str:
        return super().descrizione() + " + panna fresca"

# Composizione dinamica dei decorator
bevanda = ConPannaFresca(ConLatte(ConZucchero(CaffeBase())))
print(f"{bevanda.descrizione()}: €{bevanda.costo():.2f}")
# Caffè base + zucchero + latte + panna fresca: €3.00
```

**Confronto con il decorator Python (`@`)**

Il decorator sintattico `@` di Python è un *meccanismo linguistico* che trasforma funzioni o classi al momento della definizione. Il Decorator *pattern* è un *concetto architetturale* che aggiunge comportamento a un oggetto a runtime. Sebbene condividano il nome e l'idea di "avvolgere", operano a livelli diversi. Un decorator `@` Python può tuttavia essere usato per implementare il Decorator pattern in modo conciso:

```python
import functools
import time

def con_logging(func):
    """Decorator Python che implementa il concetto del Decorator pattern."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] Chiamata a {func.__name__}")
        inizio = time.perf_counter()
        risultato = func(*args, **kwargs)
        durata = time.perf_counter() - inizio
        print(f"[LOG] {func.__name__} completata in {durata:.4f}s")
        return risultato
    return wrapper

@con_logging
def calcola_totale(prezzi: list[float]) -> float:
    return sum(prezzi)
```

### Facade

La **Facade** fornisce un'interfaccia semplificata a un sottosistema complesso. Non nasconde il sottosistema — il client può comunque accedervi direttamente — ma offre una via d'accesso comoda per i casi d'uso più comuni.

```python
class MotoreDiRicerca:
    def cerca(self, query: str) -> list[dict]:
        return [{"id": 1, "titolo": f"Risultato per '{query}'"}]

class SistemaRaccomandazioni:
    def raccomanda(self, utente_id: int) -> list[dict]:
        return [{"id": 42, "titolo": "Articolo consigliato"}]

class CacheContenuti:
    def __init__(self):
        self._cache = {}

    def ottieni(self, chiave: str):
        return self._cache.get(chiave)

    def imposta(self, chiave: str, valore):
        self._cache[chiave] = valore

class AnalitichePiattaforma:
    def registra_evento(self, evento: str, dati: dict) -> None:
        print(f"[Analitiche] {evento}: {dati}")

class PiattaformaContenuti:
    """Facade — interfaccia semplificata per il sottosistema."""

    def __init__(self):
        self._ricerca = MotoreDiRicerca()
        self._raccomandazioni = SistemaRaccomandazioni()
        self._cache = CacheContenuti()
        self._analitiche = AnalitichePiattaforma()

    def cerca_contenuti(self, query: str, utente_id: int) -> list[dict]:
        """Un metodo semplice che coordina quattro sottosistemi."""
        # Controlla la cache
        chiave_cache = f"ricerca:{query}:{utente_id}"
        risultato = self._cache.ottieni(chiave_cache)
        if risultato:
            return risultato

        # Cerca e arricchisci con raccomandazioni
        risultati = self._ricerca.cerca(query)
        suggeriti = self._raccomandazioni.raccomanda(utente_id)
        risultato_finale = risultati + suggeriti

        # Aggiorna cache e analitiche
        self._cache.imposta(chiave_cache, risultato_finale)
        self._analitiche.registra_evento("ricerca", {"query": query, "utente": utente_id})

        return risultato_finale

# Il client usa un solo metodo chiaro
piattaforma = PiattaformaContenuti()
risultati = piattaforma.cerca_contenuti("python design patterns", utente_id=7)
```

### Proxy

Il **Proxy** fornisce un surrogato o un segnaposto per un altro oggetto, controllando l'accesso ad esso. I casi d'uso più comuni sono: lazy loading, controllo degli accessi e logging.

```python
from abc import ABC, abstractmethod

class Servizio(ABC):
    @abstractmethod
    def esegui_operazione(self, dati: str) -> str:
        pass

class ServizioPesante(Servizio):
    """Servizio che richiede inizializzazione costosa."""
    def __init__(self):
        print("Inizializzazione costosa in corso...")
        import time
        time.sleep(1)  # Simula caricamento pesante
        self._pronto = True

    def esegui_operazione(self, dati: str) -> str:
        return f"Elaborato: {dati}"

class ProxyLazyLoading(Servizio):
    """Proxy che ritarda l'inizializzazione fino al primo utilizzo."""
    def __init__(self):
        self._servizio: ServizioPesante | None = None

    def esegui_operazione(self, dati: str) -> str:
        if self._servizio is None:
            self._servizio = ServizioPesante()
        return self._servizio.esegui_operazione(dati)

class ProxyControllo(Servizio):
    """Proxy che verifica le autorizzazioni."""
    def __init__(self, servizio: Servizio, ruoli_permessi: set[str]):
        self._servizio = servizio
        self._ruoli_permessi = ruoli_permessi
        self._ruolo_corrente = "ospite"

    def imposta_ruolo(self, ruolo: str) -> None:
        self._ruolo_corrente = ruolo

    def esegui_operazione(self, dati: str) -> str:
        if self._ruolo_corrente not in self._ruoli_permessi:
            raise PermissionError(
                f"Il ruolo '{self._ruolo_corrente}' non è autorizzato"
            )
        return self._servizio.esegui_operazione(dati)

class ProxyLogging(Servizio):
    """Proxy che registra ogni operazione."""
    def __init__(self, servizio: Servizio):
        self._servizio = servizio
        self._log: list[dict] = []

    def esegui_operazione(self, dati: str) -> str:
        from datetime import datetime
        self._log.append({"timestamp": datetime.now(), "dati": dati})
        print(f"[LOG] Operazione con dati: {dati}")
        return self._servizio.esegui_operazione(dati)

    @property
    def registro(self) -> list[dict]:
        return self._log.copy()
```

### Composite

Il **Composite** compone oggetti in strutture ad albero per rappresentare gerarchie parte-tutto. Permette ai client di trattare oggetti singoli e composizioni di oggetti in modo uniforme.

```python
from abc import ABC, abstractmethod

class ComponenteFileSystem(ABC):
    def __init__(self, nome: str):
        self.nome = nome

    @abstractmethod
    def dimensione(self) -> int:
        pass

    @abstractmethod
    def mostra(self, indentazione: int = 0) -> str:
        pass

class File(ComponenteFileSystem):
    def __init__(self, nome: str, dim: int):
        super().__init__(nome)
        self._dimensione = dim

    def dimensione(self) -> int:
        return self._dimensione

    def mostra(self, indentazione: int = 0) -> str:
        return f"{'  ' * indentazione}{self.nome} ({self._dimensione} B)"

class Cartella(ComponenteFileSystem):
    def __init__(self, nome: str):
        super().__init__(nome)
        self._figli: list[ComponenteFileSystem] = []

    def aggiungi(self, componente: ComponenteFileSystem) -> None:
        self._figli.append(componente)

    def rimuovi(self, componente: ComponenteFileSystem) -> None:
        self._figli.remove(componente)

    def dimensione(self) -> int:
        return sum(figlio.dimensione() for figlio in self._figli)

    def mostra(self, indentazione: int = 0) -> str:
        righe = [f"{'  ' * indentazione}{self.nome}/"]
        for figlio in self._figli:
            righe.append(figlio.mostra(indentazione + 1))
        return "\n".join(righe)

# Costruzione di una struttura ad albero
radice = Cartella("progetto")
src = Cartella("src")
src.aggiungi(File("main.py", 2048))
src.aggiungi(File("utils.py", 1024))

test = Cartella("test")
test.aggiungi(File("test_main.py", 1536))

radice.aggiungi(src)
radice.aggiungi(test)
radice.aggiungi(File("README.md", 512))

print(radice.mostra())
print(f"Dimensione totale: {radice.dimensione()} B")
```

### Flyweight

Il **Flyweight** riduce il consumo di memoria condividendo il più possibile lo stato tra oggetti simili. Lo stato viene suddiviso in *intrinseco* (condiviso, immutabile) ed *estrinseco* (unico per ogni contesto, passato dall'esterno). È fondamentale in scenari con milioni di oggetti simili — editor di testo con caratteri, particelle in un gioco, nodi di un albero di rendering.

```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class StileCarattere:
    """Stato intrinseco (condiviso) — flyweight immutabile."""
    font: str
    dimensione: int
    grassetto: bool
    corsivo: bool

class FlyweightFactory:
    """Factory che gestisce la cache dei flyweight."""
    _cache: ClassVar[dict[tuple, StileCarattere]] = {}

    @classmethod
    def ottieni_stile(
        cls, font: str, dimensione: int,
        grassetto: bool = False, corsivo: bool = False
    ) -> StileCarattere:
        chiave = (font, dimensione, grassetto, corsivo)
        if chiave not in cls._cache:
            cls._cache[chiave] = StileCarattere(
                font=font, dimensione=dimensione,
                grassetto=grassetto, corsivo=corsivo
            )
        return cls._cache[chiave]

    @classmethod
    def conteggio_stili(cls) -> int:
        return len(cls._cache)

@dataclass
class CarattereDocumento:
    """Stato estrinseco (unico) — posizione e carattere specifico."""
    carattere: str
    riga: int
    colonna: int
    stile: StileCarattere  # Riferimento al flyweight condiviso

# Simulazione di un documento con 10.000 caratteri
caratteri: list[CarattereDocumento] = []
testo = "Lorem ipsum dolor sit amet " * 400  # ~10.800 caratteri

for i, char in enumerate(testo[:10000]):
    stile = FlyweightFactory.ottieni_stile(
        font="Arial",
        dimensione=12,
        grassetto=(i % 100 < 10),  # Ogni 100 caratteri, i primi 10 in grassetto
    )
    caratteri.append(CarattereDocumento(
        carattere=char, riga=i // 80, colonna=i % 80, stile=stile
    ))

print(f"Caratteri totali: {len(caratteri)}")
print(f"Stili unici in memoria: {FlyweightFactory.conteggio_stili()}")
# Caratteri totali: 10000
# Stili unici in memoria: 2  (invece di 10.000 oggetti stile)
```

In Python, il Flyweight si implementa spesso tramite `__slots__` per ridurre ulteriormente il footprint di memoria degli oggetti, e con `@dataclass(frozen=True)` per garantire l'immutabilità dello stato condiviso. Il metodo `str.intern()` di Python è un esempio nativo di Flyweight applicato alle stringhe. Anche il caching degli interi piccoli (-5 a 256) nell'interprete CPython è un'applicazione implicita del principio Flyweight: Python riutilizza sempre lo stesso oggetto per questi valori, evitando allocazioni ridondanti. Quando si implementa un Flyweight personalizzato, è essenziale che lo stato intrinseco (condiviso) sia rigorosamente immutabile — qualsiasi mutazione accidentale dello stato condiviso corromperebbe tutti gli oggetti che lo riferiscono simultaneamente.

---

## Pattern Comportamentali

I pattern comportamentali definiscono i meccanismi di comunicazione tra oggetti e la distribuzione delle responsabilità.

### Observer

L'**Observer** definisce una dipendenza uno-a-molti tra oggetti: quando un oggetto (il *soggetto*) cambia stato, tutti i suoi dipendenti (gli *osservatori*) vengono notificati e aggiornati automaticamente.

```python
from abc import ABC, abstractmethod
from weakref import WeakSet

class Evento:
    """Sistema di eventi generico con supporto per weak references."""

    def __init__(self):
        self._ascoltatori: dict[str, WeakSet] = {}

    def registra(self, tipo_evento: str, ascoltatore) -> None:
        if tipo_evento not in self._ascoltatori:
            self._ascoltatori[tipo_evento] = WeakSet()
        self._ascoltatori[tipo_evento].add(ascoltatore)

    def cancella(self, tipo_evento: str, ascoltatore) -> None:
        if tipo_evento in self._ascoltatori:
            self._ascoltatori[tipo_evento].discard(ascoltatore)

    def emetti(self, tipo_evento: str, **dati) -> None:
        if tipo_evento in self._ascoltatori:
            for ascoltatore in list(self._ascoltatori[tipo_evento]):
                ascoltatore.aggiorna(tipo_evento, dati)

class Osservatore(ABC):
    @abstractmethod
    def aggiorna(self, tipo_evento: str, dati: dict) -> None:
        pass

class NegozioOnline:
    """Soggetto osservabile."""

    def __init__(self):
        self.eventi = Evento()
        self._prodotti: dict[str, float] = {}

    def aggiungi_prodotto(self, nome: str, prezzo: float) -> None:
        self._prodotti[nome] = prezzo
        self.eventi.emetti("nuovo_prodotto", nome=nome, prezzo=prezzo)

    def aggiorna_prezzo(self, nome: str, nuovo_prezzo: float) -> None:
        vecchio_prezzo = self._prodotti.get(nome)
        self._prodotti[nome] = nuovo_prezzo
        self.eventi.emetti(
            "cambio_prezzo",
            nome=nome,
            vecchio_prezzo=vecchio_prezzo,
            nuovo_prezzo=nuovo_prezzo
        )

class ClienteNotificato(Osservatore):
    def __init__(self, nome: str):
        self.nome = nome

    def aggiorna(self, tipo_evento: str, dati: dict) -> None:
        if tipo_evento == "cambio_prezzo":
            print(
                f"[{self.nome}] Il prezzo di '{dati['nome']}' è cambiato "
                f"da €{dati['vecchio_prezzo']:.2f} a €{dati['nuovo_prezzo']:.2f}"
            )
        elif tipo_evento == "nuovo_prodotto":
            print(f"[{self.nome}] Nuovo prodotto disponibile: {dati['nome']}")

negozio = NegozioOnline()
alice = ClienteNotificato("Alice")
marco = ClienteNotificato("Marco")

negozio.eventi.registra("cambio_prezzo", alice)
negozio.eventi.registra("nuovo_prodotto", marco)
negozio.eventi.registra("nuovo_prodotto", alice)

negozio.aggiungi_prodotto("Laptop", 999.99)
negozio.aggiorna_prezzo("Laptop", 849.99)
```

L'uso di `WeakSet` evita che il sistema di eventi impedisca la garbage collection degli osservatori: se un osservatore non è più referenziato altrove, viene automaticamente rimosso.

### Strategy

Lo **Strategy** definisce una famiglia di algoritmi, li incapsula e li rende intercambiabili. In Python, grazie alle funzioni di prima classe, questo pattern diventa estremamente conciso.

**Approccio Pythonico (con funzioni)**

```python
from typing import Callable

# Strategie come semplici funzioni
def sconto_nessuno(prezzo: float) -> float:
    return prezzo

def sconto_percentuale_10(prezzo: float) -> float:
    return prezzo * 0.9

def sconto_fisso_5(prezzo: float) -> float:
    return max(0, prezzo - 5.0)

def sconto_fedelta(prezzo: float) -> float:
    return prezzo * 0.85 if prezzo > 50 else prezzo * 0.95

class CarrelloSpesa:
    def __init__(self, strategia_sconto: Callable[[float], float] = sconto_nessuno):
        self._articoli: list[tuple[str, float]] = []
        self._strategia_sconto = strategia_sconto

    def aggiungi(self, nome: str, prezzo: float) -> None:
        self._articoli.append((nome, prezzo))

    @property
    def strategia_sconto(self) -> Callable[[float], float]:
        return self._strategia_sconto

    @strategia_sconto.setter
    def strategia_sconto(self, strategia: Callable[[float], float]) -> None:
        self._strategia_sconto = strategia

    def totale(self) -> float:
        subtotale = sum(prezzo for _, prezzo in self._articoli)
        return self._strategia_sconto(subtotale)

carrello = CarrelloSpesa(sconto_percentuale_10)
carrello.aggiungi("Libro", 25.0)
carrello.aggiungi("Penna", 3.0)
print(f"Totale con 10%: €{carrello.totale():.2f}")  # €25.20

# Cambio strategia a runtime
carrello.strategia_sconto = sconto_fedelta
print(f"Totale fedelta: €{carrello.totale():.2f}")   # €26.60
```

**Approccio class-based (quando la strategia ha stato interno)**

```python
from abc import ABC, abstractmethod

class StrategiaSpedizione(ABC):
    @abstractmethod
    def calcola(self, peso: float, distanza: float) -> float:
        pass

class SpedizioneStandard(StrategiaSpedizione):
    def calcola(self, peso: float, distanza: float) -> float:
        return peso * 0.5 + distanza * 0.01

class SpedizioneEspressa(StrategiaSpedizione):
    def __init__(self, supplemento: float = 10.0):
        self.supplemento = supplemento

    def calcola(self, peso: float, distanza: float) -> float:
        return peso * 1.0 + distanza * 0.02 + self.supplemento
```

### Command

Il **Command** incapsula una richiesta come un oggetto, permettendo di parametrizzare i client con richieste diverse, accodarle, registrarle e supportare operazioni di annullamento (undo/redo).

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

class Comando(ABC):
    @abstractmethod
    def esegui(self) -> None:
        pass

    @abstractmethod
    def annulla(self) -> None:
        pass

class EditorTesto:
    """Receiver — l'oggetto su cui operano i comandi."""
    def __init__(self):
        self.contenuto = ""

    def inserisci(self, testo: str, posizione: int) -> None:
        self.contenuto = (
            self.contenuto[:posizione] + testo + self.contenuto[posizione:]
        )

    def elimina(self, posizione: int, lunghezza: int) -> str:
        eliminato = self.contenuto[posizione:posizione + lunghezza]
        self.contenuto = (
            self.contenuto[:posizione] + self.contenuto[posizione + lunghezza:]
        )
        return eliminato

class ComandoInserisci(Comando):
    def __init__(self, editor: EditorTesto, testo: str, posizione: int):
        self._editor = editor
        self._testo = testo
        self._posizione = posizione

    def esegui(self) -> None:
        self._editor.inserisci(self._testo, self._posizione)

    def annulla(self) -> None:
        self._editor.elimina(self._posizione, len(self._testo))

class ComandoElimina(Comando):
    def __init__(self, editor: EditorTesto, posizione: int, lunghezza: int):
        self._editor = editor
        self._posizione = posizione
        self._lunghezza = lunghezza
        self._testo_eliminato = ""

    def esegui(self) -> None:
        self._testo_eliminato = self._editor.elimina(
            self._posizione, self._lunghezza
        )

    def annulla(self) -> None:
        self._editor.inserisci(self._testo_eliminato, self._posizione)

class GestoreComandi:
    """Invoker con supporto undo/redo."""
    def __init__(self):
        self._storico: list[Comando] = []
        self._annullati: list[Comando] = []

    def esegui(self, comando: Comando) -> None:
        comando.esegui()
        self._storico.append(comando)
        self._annullati.clear()  # Il redo si invalida dopo un nuovo comando

    def annulla(self) -> None:
        if not self._storico:
            raise IndexError("Nessun comando da annullare")
        comando = self._storico.pop()
        comando.annulla()
        self._annullati.append(comando)

    def ripeti(self) -> None:
        if not self._annullati:
            raise IndexError("Nessun comando da ripetere")
        comando = self._annullati.pop()
        comando.esegui()
        self._storico.append(comando)

class MacroComando(Comando):
    """Comando composto — esegue una sequenza di comandi."""
    def __init__(self, comandi: list[Comando]):
        self._comandi = comandi

    def esegui(self) -> None:
        for comando in self._comandi:
            comando.esegui()

    def annulla(self) -> None:
        for comando in reversed(self._comandi):
            comando.annulla()

# Utilizzo
editor = EditorTesto()
gestore = GestoreComandi()

gestore.esegui(ComandoInserisci(editor, "Ciao ", 0))
gestore.esegui(ComandoInserisci(editor, "mondo!", 5))
print(editor.contenuto)  # "Ciao mondo!"

gestore.annulla()
print(editor.contenuto)  # "Ciao "

gestore.ripeti()
print(editor.contenuto)  # "Ciao mondo!"
```

### Iterator

L'**Iterator** fornisce un modo per accedere sequenzialmente agli elementi di una collezione senza esporre la struttura interna. Python integra questo pattern a livello di linguaggio tramite il protocollo `__iter__`/`__next__` e i generatori.

```python
class IntervalloInverso:
    """Iteratore personalizzato — conta alla rovescia."""

    def __init__(self, inizio: int, fine: int = 0):
        self._corrente = inizio
        self._fine = fine

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self._corrente <= self._fine:
            raise StopIteration
        self._corrente -= 1
        return self._corrente + 1

for numero in IntervalloInverso(5):
    print(numero, end=" ")  # 5 4 3 2 1

# Generatori — il modo Pythonico per creare iteratori
def fibonacci(limite: int):
    """Generatore che produce la sequenza di Fibonacci."""
    a, b = 0, 1
    while a <= limite:
        yield a
        a, b = b, a + b

for n in fibonacci(100):
    print(n, end=" ")  # 0 1 1 2 3 5 8 13 21 34 55 89

# Generatori per attraversamento di alberi
class Nodo:
    def __init__(self, valore, figli=None):
        self.valore = valore
        self.figli = figli or []

def attraversa_profondita(nodo: Nodo):
    """Generatore per attraversamento in profondita (DFS)."""
    yield nodo.valore
    for figlio in nodo.figli:
        yield from attraversa_profondita(figlio)

albero = Nodo("A", [
    Nodo("B", [Nodo("D"), Nodo("E")]),
    Nodo("C", [Nodo("F")])
])

print(list(attraversa_profondita(albero)))  # ['A', 'B', 'D', 'E', 'C', 'F']
```

I generatori sono la soluzione idiomatica di Python per il pattern Iterator: eliminano la necessità di classi dedicate, gestiscono automaticamente lo stato e sono *lazy* (producono valori su richiesta, senza caricare tutto in memoria).

### Template Method

Il **Template Method** definisce lo scheletro di un algoritmo in un metodo, delegando alcuni passaggi alle sottoclassi. Permette alle sottoclassi di ridefinire certi passi dell'algoritmo senza modificarne la struttura complessiva.

```python
from abc import ABC, abstractmethod

class PipelineElaborazioneDati(ABC):
    """Template Method — definisce lo scheletro dell'algoritmo."""

    def esegui(self, sorgente: str) -> dict:
        """Metodo template — la struttura dell'algoritmo è fissa."""
        dati_grezzi = self.estrai(sorgente)
        dati_puliti = self.pulisci(dati_grezzi)
        dati_trasformati = self.trasforma(dati_puliti)
        self.carica(dati_trasformati)
        return dati_trasformati

    @abstractmethod
    def estrai(self, sorgente: str) -> list:
        """Passo 1: estrazione dei dati."""
        pass

    def pulisci(self, dati: list) -> list:
        """Passo 2: pulizia (hook — implementazione di default)."""
        return [d for d in dati if d is not None]

    @abstractmethod
    def trasforma(self, dati: list) -> dict:
        """Passo 3: trasformazione."""
        pass

    def carica(self, dati: dict) -> None:
        """Passo 4: caricamento (hook — implementazione di default)."""
        print(f"Caricati {len(dati)} elementi")

class PipelineCSV(PipelineElaborazioneDati):
    def estrai(self, sorgente: str) -> list:
        print(f"Estrazione dati da CSV: {sorgente}")
        return [{"nome": "Alice", "eta": 30}, {"nome": "Bob", "eta": None}]

    def pulisci(self, dati: list) -> list:
        # Override: rimuove record con campi None
        return [d for d in dati if all(v is not None for v in d.values())]

    def trasforma(self, dati: list) -> dict:
        return {d["nome"]: d for d in dati}

class PipelineAPI(PipelineElaborazioneDati):
    def estrai(self, sorgente: str) -> list:
        print(f"Estrazione dati da API: {sorgente}")
        return [{"id": 1, "valore": 42}, {"id": 2, "valore": 99}]

    def trasforma(self, dati: list) -> dict:
        return {str(d["id"]): d["valore"] for d in dati}

pipeline = PipelineCSV()
risultato = pipeline.esegui("utenti.csv")
```

### State

Lo **State** permette a un oggetto di alterare il proprio comportamento quando il suo stato interno cambia. L'oggetto sembrerà cambiare classe.

```python
from abc import ABC, abstractmethod

class StatoOrdine(ABC):
    @abstractmethod
    def processa(self, ordine: "Ordine") -> None:
        pass

    @abstractmethod
    def annulla(self, ordine: "Ordine") -> None:
        pass

    @abstractmethod
    def descrizione(self) -> str:
        pass

class StatoNuovo(StatoOrdine):
    def processa(self, ordine: "Ordine") -> None:
        print("Ordine confermato. Pagamento in corso...")
        ordine.stato = StatoPagato()

    def annulla(self, ordine: "Ordine") -> None:
        print("Ordine annullato.")
        ordine.stato = StatoAnnullato()

    def descrizione(self) -> str:
        return "Nuovo"

class StatoPagato(StatoOrdine):
    def processa(self, ordine: "Ordine") -> None:
        print("Ordine in preparazione per la spedizione...")
        ordine.stato = StatoSpedito()

    def annulla(self, ordine: "Ordine") -> None:
        print("Rimborso in corso...")
        ordine.stato = StatoAnnullato()

    def descrizione(self) -> str:
        return "Pagato"

class StatoSpedito(StatoOrdine):
    def processa(self, ordine: "Ordine") -> None:
        print("Ordine consegnato!")
        ordine.stato = StatoConsegnato()

    def annulla(self, ordine: "Ordine") -> None:
        print("Impossibile annullare: ordine già spedito.")

    def descrizione(self) -> str:
        return "Spedito"

class StatoConsegnato(StatoOrdine):
    def processa(self, ordine: "Ordine") -> None:
        print("Ordine già consegnato. Nessuna azione.")

    def annulla(self, ordine: "Ordine") -> None:
        print("Impossibile annullare: ordine già consegnato.")

    def descrizione(self) -> str:
        return "Consegnato"

class StatoAnnullato(StatoOrdine):
    def processa(self, ordine: "Ordine") -> None:
        print("Ordine annullato. Nessuna azione possibile.")

    def annulla(self, ordine: "Ordine") -> None:
        print("Ordine già annullato.")

    def descrizione(self) -> str:
        return "Annullato"

class Ordine:
    def __init__(self, id_ordine: str):
        self.id_ordine = id_ordine
        self.stato: StatoOrdine = StatoNuovo()

    def processa(self) -> None:
        self.stato.processa(self)

    def annulla(self) -> None:
        self.stato.annulla(self)

    def __str__(self) -> str:
        return f"Ordine {self.id_ordine}: {self.stato.descrizione()}"

ordine = Ordine("ORD-001")
print(ordine)          # Ordine ORD-001: Nuovo
ordine.processa()      # Ordine confermato. Pagamento in corso...
print(ordine)          # Ordine ORD-001: Pagato
ordine.processa()      # Ordine in preparazione per la spedizione...
ordine.annulla()       # Impossibile annullare: ordine già spedito.
```

### Chain of Responsibility

La **Chain of Responsibility** permette di passare una richiesta lungo una catena di gestori. Ogni gestore decide se elaborare la richiesta o passarla al successivo nella catena.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Richiesta:
    tipo: str
    contenuto: str
    livello_priorita: int = 0

class Gestore(ABC):
    def __init__(self):
        self._successivo: Gestore | None = None

    def imposta_successivo(self, gestore: "Gestore") -> "Gestore":
        self._successivo = gestore
        return gestore  # Permette il chaining

    @abstractmethod
    def gestisci(self, richiesta: Richiesta) -> str | None:
        pass

    def passa_al_successivo(self, richiesta: Richiesta) -> str | None:
        if self._successivo:
            return self._successivo.gestisci(richiesta)
        return None

class GestoreAutenticazione(Gestore):
    def gestisci(self, richiesta: Richiesta) -> str | None:
        if richiesta.tipo == "autenticazione":
            return f"[Auth] Gestita richiesta: {richiesta.contenuto}"
        return self.passa_al_successivo(richiesta)

class GestoreAutorizzazione(Gestore):
    def gestisci(self, richiesta: Richiesta) -> str | None:
        if richiesta.tipo == "autorizzazione":
            return f"[Authz] Gestita richiesta: {richiesta.contenuto}"
        return self.passa_al_successivo(richiesta)

class GestoreValidazione(Gestore):
    def gestisci(self, richiesta: Richiesta) -> str | None:
        if richiesta.tipo == "validazione":
            return f"[Valid] Gestita richiesta: {richiesta.contenuto}"
        return self.passa_al_successivo(richiesta)

class GestorePredefinito(Gestore):
    def gestisci(self, richiesta: Richiesta) -> str | None:
        return f"[Default] Nessun gestore specifico per: {richiesta.tipo}"

# Costruzione della catena
auth = GestoreAutenticazione()
authz = GestoreAutorizzazione()
valid = GestoreValidazione()
default = GestorePredefinito()

auth.imposta_successivo(authz).imposta_successivo(valid).imposta_successivo(default)

# Le richieste attraversano la catena
richieste = [
    Richiesta("autenticazione", "Login utente"),
    Richiesta("validazione", "Verifica dati form"),
    Richiesta("sconosciuto", "Richiesta generica"),
]

for r in richieste:
    risultato = auth.gestisci(r)
    print(risultato)
```

Questo pattern si ritrova frequentemente nelle pipeline middleware dei framework web (Django, Flask, FastAPI), dove ogni middleware processa o inoltra la richiesta HTTP al successivo.

### Mediator

Il **Mediator** definisce un oggetto che incapsula il modo in cui un insieme di oggetti interagisce. Invece di permettere agli oggetti di comunicare direttamente tra loro (creando un grafo di dipendenze intricato), il Mediator centralizza la comunicazione: ogni componente conosce solo il mediatore, non gli altri componenti. Questo riduce drasticamente l'accoppiamento.

```python
from abc import ABC, abstractmethod

class Mediatore(ABC):
    @abstractmethod
    def notifica(self, mittente: "Componente", evento: str, dati: dict) -> None:
        pass

class Componente:
    """Classe base per i componenti che partecipano alla mediazione."""
    def __init__(self, nome: str):
        self.nome = nome
        self._mediatore: Mediatore | None = None

    def imposta_mediatore(self, mediatore: Mediatore) -> None:
        self._mediatore = mediatore

    def invia(self, evento: str, dati: dict | None = None) -> None:
        if self._mediatore:
            self._mediatore.notifica(self, evento, dati or {})

class FormRegistrazione(Componente):
    def invia_dati(self, email: str, password: str) -> None:
        print(f"[{self.nome}] Invio dati di registrazione")
        self.invia("registrazione_inviata", {"email": email, "password": password})

class ValidatoreEmail(Componente):
    def valida(self, email: str) -> bool:
        valido = "@" in email and "." in email
        stato = "valida" if valido else "non valida"
        print(f"[{self.nome}] Email {stato}: {email}")
        self.invia("email_validata", {"email": email, "valido": valido})
        return valido

class ServizioNotifica(Componente):
    def invia_benvenuto(self, email: str) -> None:
        print(f"[{self.nome}] Email di benvenuto inviata a: {email}")

class LogAudit(Componente):
    def registra(self, azione: str, dettagli: dict) -> None:
        print(f"[{self.nome}] LOG: {azione} — {dettagli}")

class MediatoreRegistrazione(Mediatore):
    """Mediatore concreto che coordina il flusso di registrazione."""

    def __init__(self):
        self.form = FormRegistrazione("Form")
        self.validatore = ValidatoreEmail("Validatore")
        self._notificatore = ServizioNotifica("Notifiche")
        self.log = LogAudit("Audit")

        # Registra tutti i componenti
        for componente in [self.form, self.validatore, self._notificatore, self.log]:
            componente.imposta_mediatore(self)

    def notifica(self, mittente: Componente, evento: str, dati: dict) -> None:
        if evento == "registrazione_inviata":
            self.log.registra("tentativo_registrazione", dati)
            self.validatore.valida(dati["email"])
        elif evento == "email_validata" and dati.get("valido"):
            self._notificatore.invia_benvenuto(dati["email"])
            self.log.registra("registrazione_completata", dati)

# I componenti non si conoscono — comunicano solo tramite il mediatore
mediatore = MediatoreRegistrazione()
mediatore.form.invia_dati("utente@esempio.com", "s3cur3Pa$$")
```

Il pattern Mediator è alla base dei framework di segnali come `blinker` e del sistema di segnali di Django, dove componenti disaccoppiati comunicano attraverso un dispatcher centralizzato.

**Mediator vs Observer:** entrambi i pattern gestiscono la comunicazione tra componenti, ma con approcci diversi. L'Observer definisce una relazione diretta (anche se loose) tra soggetto e osservatori — il soggetto sa di avere osservatori e li notifica. Il Mediator elimina completamente la consapevolezza reciproca: i componenti conoscono solo il mediatore e non sanno chi riceverà i loro messaggi. Il Mediator è preferibile quando la logica di coordinazione è complessa e centralizzata, mentre l'Observer è più adatto per notifiche semplici e disaccoppiate.

### Memento

Il **Memento** cattura e esternalizza lo stato interno di un oggetto senza violare l'incapsulamento, permettendo di ripristinare l'oggetto a uno stato precedente. È il pattern alla base delle funzionalità di undo/redo e dei checkpoint di salvataggio.

```python
from dataclasses import dataclass, field
from datetime import datetime
import copy

@dataclass(frozen=True)
class Memento:
    """Snapshot immutabile dello stato."""
    stato: dict
    timestamp: str
    descrizione: str

class DocumentoTesto:
    """Originator — l'oggetto il cui stato viene salvato."""

    def __init__(self, titolo: str):
        self.titolo = titolo
        self.contenuto: list[str] = []
        self.metadata: dict = {"autore": "", "versione": 1}

    def aggiungi_paragrafo(self, testo: str) -> None:
        self.contenuto.append(testo)
        self.metadata["versione"] += 1

    def rimuovi_ultimo(self) -> str | None:
        if self.contenuto:
            rimosso = self.contenuto.pop()
            self.metadata["versione"] += 1
            return rimosso
        return None

    def salva_stato(self, descrizione: str = "") -> Memento:
        """Crea un memento dello stato corrente."""
        return Memento(
            stato=copy.deepcopy({
                "titolo": self.titolo,
                "contenuto": self.contenuto,
                "metadata": self.metadata,
            }),
            timestamp=datetime.now().isoformat(),
            descrizione=descrizione,
        )

    def ripristina_stato(self, memento: Memento) -> None:
        """Ripristina lo stato da un memento."""
        stato = copy.deepcopy(memento.stato)
        self.titolo = stato["titolo"]
        self.contenuto = stato["contenuto"]
        self.metadata = stato["metadata"]

    def __str__(self) -> str:
        testo = "\n".join(self.contenuto) if self.contenuto else "(vuoto)"
        return f"[{self.titolo} v{self.metadata['versione']}]\n{testo}"

class CronologiaDocumento:
    """Caretaker — gestisce la cronologia dei memento."""

    def __init__(self, documento: DocumentoTesto):
        self._documento = documento
        self._cronologia: list[Memento] = []
        self._posizione: int = -1

    def salva(self, descrizione: str = "") -> None:
        # Elimina gli stati futuri se abbiamo fatto undo
        self._cronologia = self._cronologia[:self._posizione + 1]
        memento = self._documento.salva_stato(descrizione)
        self._cronologia.append(memento)
        self._posizione += 1

    def annulla(self) -> bool:
        if self._posizione <= 0:
            return False
        self._posizione -= 1
        self._documento.ripristina_stato(self._cronologia[self._posizione])
        return True

    def ripeti(self) -> bool:
        if self._posizione >= len(self._cronologia) - 1:
            return False
        self._posizione += 1
        self._documento.ripristina_stato(self._cronologia[self._posizione])
        return True

# Utilizzo
doc = DocumentoTesto("Relazione")
cronologia = CronologiaDocumento(doc)

cronologia.salva("stato iniziale")
doc.aggiungi_paragrafo("Primo paragrafo del documento.")
cronologia.salva("aggiunto primo paragrafo")
doc.aggiungi_paragrafo("Secondo paragrafo con analisi.")
cronologia.salva("aggiunto secondo paragrafo")

print(doc)  # Mostra entrambi i paragrafi

cronologia.annulla()
print(doc)  # Mostra solo il primo paragrafo

cronologia.annulla()
print(doc)  # Documento vuoto

cronologia.ripeti()
print(doc)  # Primo paragrafo ripristinato
```

Il Memento utilizza `copy.deepcopy` per garantire che lo snapshot sia completamente indipendente dall'oggetto originale. Lo stato salvato è `frozen=True` per prevenire modifiche accidentali ai checkpoint.

### Visitor

Il **Visitor** permette di definire nuove operazioni su una struttura di oggetti senza modificare le classi degli oggetti stessi. Separa l'algoritmo dalla struttura dati su cui opera, seguendo il principio Open/Closed.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Elementi della struttura
class NodoAST(ABC):
    @abstractmethod
    def accetta(self, visitatore: "VisitatorAST"):
        pass

@dataclass
class NodoNumero(NodoAST):
    valore: float

    def accetta(self, visitatore: "VisitatorAST"):
        return visitatore.visita_numero(self)

@dataclass
class NodoOperazione(NodoAST):
    operatore: str
    sinistra: NodoAST
    destra: NodoAST

    def accetta(self, visitatore: "VisitatorAST"):
        return visitatore.visita_operazione(self)

@dataclass
class NodoFunzione(NodoAST):
    nome: str
    argomento: NodoAST

    def accetta(self, visitatore: "VisitatorAST"):
        return visitatore.visita_funzione(self)

# Interfaccia Visitor
class VisitatorAST(ABC):
    @abstractmethod
    def visita_numero(self, nodo: NodoNumero):
        pass

    @abstractmethod
    def visita_operazione(self, nodo: NodoOperazione):
        pass

    @abstractmethod
    def visita_funzione(self, nodo: NodoFunzione):
        pass

# Visitor concreti — ogni nuovo visitor aggiunge un'operazione
# senza modificare le classi dei nodi
class ValutatoreEspressione(VisitatorAST):
    """Valuta l'espressione e restituisce il risultato numerico."""
    import math

    _operazioni = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b if b != 0 else float("inf"),
    }

    def visita_numero(self, nodo: NodoNumero) -> float:
        return nodo.valore

    def visita_operazione(self, nodo: NodoOperazione) -> float:
        sinistra = nodo.sinistra.accetta(self)
        destra = nodo.destra.accetta(self)
        return self._operazioni[nodo.operatore](sinistra, destra)

    def visita_funzione(self, nodo: NodoFunzione) -> float:
        import math
        argomento = nodo.argomento.accetta(self)
        funzioni = {"sqrt": math.sqrt, "abs": abs, "neg": lambda x: -x}
        return funzioni[nodo.nome](argomento)

class StampatorNotazione(VisitatorAST):
    """Converte l'AST in notazione infissa leggibile."""

    def visita_numero(self, nodo: NodoNumero) -> str:
        return str(nodo.valore)

    def visita_operazione(self, nodo: NodoOperazione) -> str:
        s = nodo.sinistra.accetta(self)
        d = nodo.destra.accetta(self)
        return f"({s} {nodo.operatore} {d})"

    def visita_funzione(self, nodo: NodoFunzione) -> str:
        arg = nodo.argomento.accetta(self)
        return f"{nodo.nome}({arg})"

# AST per l'espressione: sqrt((3 + 4) * 2)
espressione = NodoFunzione(
    "sqrt",
    NodoOperazione(
        "*",
        NodoOperazione("+", NodoNumero(3), NodoNumero(4)),
        NodoNumero(2),
    ),
)

valutatore = ValutatoreEspressione()
stampatore = StampatorNotazione()

print(espressione.accetta(stampatore))   # sqrt(((3 + 4) * 2))
print(espressione.accetta(valutatore))   # 3.7416573867739413
```

Il Visitor è particolarmente utile nell'elaborazione di AST (Abstract Syntax Tree), compilatori, linter e tool di analisi statica. In Python, il modulo `ast` della libreria standard utilizza concettualmente questo pattern tramite `ast.NodeVisitor`.

---

## Pattern Python-Specifici

Oltre ai pattern classici GoF, Python offre pattern peculiari che nascono dalle caratteristiche uniche del linguaggio.

### Borg Pattern

Il **Borg** (o Monostate) rappresenta un'alternativa al Singleton: anziché garantire un'unica istanza, garantisce che tutte le istanze condividano lo *stesso stato*. Ogni istanza è un oggetto distinto, ma l'attributo `__dict__` è condiviso.

```python
class Borg:
    _stato_condiviso: dict = {}

    def __init__(self):
        self.__dict__ = self._stato_condiviso

class ConfigurazioneBorg(Borg):
    def __init__(self):
        super().__init__()
        # Inizializza solo se lo stato è vuoto
        if not self._stato_condiviso:
            self.debug = False
            self.database = "sqlite:///app.db"

a = ConfigurazioneBorg()
b = ConfigurazioneBorg()

a.debug = True
print(b.debug)      # True — stato condiviso
print(a is b)       # False — istanze diverse
print(a.__dict__ is b.__dict__)  # True — stesso dizionario
```

Il vantaggio del Borg rispetto al Singleton è che funziona naturalmente con l'ereditarietà e non richiede override di `__new__` o metaclass.

### Mixin

Un **Mixin** è una classe pensata per essere usata esclusivamente con l'ereditarietà multipla, fornendo funzionalità aggiuntive specifiche senza rappresentare un tipo autonomo. A differenza di una classe base, un mixin non è pensato per essere istanziato direttamente.

```python
import json
from datetime import datetime

class SerializzazioneJSONMixin:
    """Mixin che aggiunge la capacita di serializzazione JSON."""

    def a_json(self) -> str:
        def serializzatore(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Tipo non serializzabile: {type(obj)}")
        return json.dumps(self.__dict__, default=serializzatore, indent=2)

    @classmethod
    def da_json(cls, dati_json: str):
        dati = json.loads(dati_json)
        istanza = cls.__new__(cls)
        istanza.__dict__.update(dati)
        return istanza

class TimestampMixin:
    """Mixin che aggiunge timestamp automatici."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        init_originale = cls.__init__

        def nuovo_init(self, *args, **kwargs):
            init_originale(self, *args, **kwargs)
            self.creato_il = datetime.now()
            self.aggiornato_il = datetime.now()

        cls.__init__ = nuovo_init

class ValidazioneMixin:
    """Mixin che aggiunge la validazione degli attributi."""

    _regole_validazione: dict = {}

    def valida(self) -> list[str]:
        errori = []
        for campo, regola in self._regole_validazione.items():
            valore = getattr(self, campo, None)
            if not regola(valore):
                errori.append(f"Validazione fallita per '{campo}': {valore}")
        return errori

class Utente(SerializzazioneJSONMixin, TimestampMixin, ValidazioneMixin):
    _regole_validazione = {
        "nome": lambda v: isinstance(v, str) and len(v) >= 2,
        "email": lambda v: isinstance(v, str) and "@" in v,
        "eta": lambda v: isinstance(v, int) and 0 < v < 150,
    }

    def __init__(self, nome: str, email: str, eta: int):
        self.nome = nome
        self.email = email
        self.eta = eta

utente = Utente("Alice", "alice@example.com", 30)
print(utente.a_json())       # Serializzazione JSON
print(utente.creato_il)      # Timestamp automatico
print(utente.valida())       # [] — nessun errore
```

I mixin sono uno strumento potente ma devono essere usati con disciplina. Ogni mixin dovrebbe fornire una singola responsabilita ben definita, e il nome dovrebbe terminare con `Mixin` per chiarezza.

### Monkey Patching

Il **Monkey Patching** consiste nel modificare dinamicamente classi, moduli o oggetti a runtime. In Python, essendo tutto un oggetto, questa tecnica è tecnicamente semplice — ma va usata con estrema cautela poiché rende il codice difficile da comprendere e debuggare.

```python
# Esempio: aggiungere un metodo a una classe esistente
class Calcolatrice:
    def somma(self, a, b):
        return a + b

# Monkey patch — aggiunta di un metodo a runtime
def moltiplica(self, a, b):
    return a * b

Calcolatrice.moltiplica = moltiplica

calc = Calcolatrice()
print(calc.moltiplica(3, 4))  # 12

# Caso d'uso legittimo: mock nei test
import unittest
from unittest.mock import patch

class TestServizio:
    def ottieni_dati(self):
        # In produzione chiama un'API esterna
        import urllib.request
        return urllib.request.urlopen("https://api.example.com").read()

def test_servizio():
    """Il monkey patching e accettabile nei test."""
    with patch.object(TestServizio, 'ottieni_dati', return_value=b'{"test": true}'):
        servizio = TestServizio()
        assert servizio.ottieni_dati() == b'{"test": true}'
```

Il monkey patching e accettabile nei test (tramite `unittest.mock`) e per hotfix temporanei, ma deve essere evitato nel codice di produzione come pratica abituale. Il codice che dipende dal monkey patching e fragile e difficile da mantenere.

### Descriptor

I **descriptor** sono oggetti che implementano il protocollo descriptor (`__get__`, `__set__`, `__delete__`), permettendo di personalizzare l'accesso agli attributi. Sono il meccanismo su cui si basano `property`, `classmethod`, `staticmethod` e molte altre funzionalita di Python.

```python
class ValidatoPositivo:
    """Descriptor che valida che il valore sia positivo."""

    def __init__(self, nome: str):
        self.nome = nome
        self.nome_privato = f"_desc_{nome}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.nome_privato, None)

    def __set__(self, obj, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError(f"'{self.nome}' deve essere numerico, ricevuto {type(valore).__name__}")
        if valore < 0:
            raise ValueError(f"'{self.nome}' deve essere positivo, ricevuto {valore}")
        setattr(obj, self.nome_privato, valore)

    def __delete__(self, obj):
        raise AttributeError(f"Impossibile eliminare '{self.nome}'")

class ProprietaLazy:
    """Descriptor per proprieta calcolate pigramente (lazy)."""

    def __init__(self, funzione):
        self.funzione = funzione
        self.nome_attr = f"_lazy_{funzione.__name__}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if not hasattr(obj, self.nome_attr):
            setattr(obj, self.nome_attr, self.funzione(obj))
        return getattr(obj, self.nome_attr)

class Prodotto:
    prezzo = ValidatoPositivo("prezzo")
    quantita = ValidatoPositivo("quantita")

    def __init__(self, nome: str, prezzo: float, quantita: int):
        self.nome = nome
        self.prezzo = prezzo       # Passa attraverso __set__ del descriptor
        self.quantita = quantita

    @ProprietaLazy
    def codice_hash(self):
        """Calcolato una sola volta, poi memorizzato."""
        import hashlib
        dati = f"{self.nome}:{self.prezzo}:{self.quantita}"
        return hashlib.sha256(dati.encode()).hexdigest()[:12]

p = Prodotto("Widget", 9.99, 100)
print(p.prezzo)        # 9.99
print(p.codice_hash)   # Calcolato al primo accesso

try:
    p.prezzo = -5  # ValueError: 'prezzo' deve essere positivo
except ValueError as e:
    print(e)
```

I descriptor sono il fondamento del modello a oggetti di Python. Comprendere come funzionano permette di creare API eleganti e sicure, con validazione trasparente e proprietà calcolate.

**Protocollo Descriptor completo e `__set_name__`**

A partire da Python 3.6, il metodo `__set_name__` (PEP 487) viene invocato automaticamente quando il descriptor viene assegnato a un attributo di classe. Questo elimina la necessità di passare manualmente il nome dell'attributo al costruttore del descriptor:

```python
class Validato:
    """Descriptor generico con __set_name__ — non richiede nome esplicito."""

    def __init__(self, tipo: type, *, minimo=None, massimo=None):
        self.tipo = tipo
        self.minimo = minimo
        self.massimo = massimo

    def __set_name__(self, owner, name):
        """Chiamato automaticamente da Python alla definizione della classe."""
        self.nome_pubblico = name
        self.nome_privato = f"_desc_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.nome_privato, None)

    def __set__(self, obj, valore):
        if not isinstance(valore, self.tipo):
            raise TypeError(
                f"'{self.nome_pubblico}' richiede {self.tipo.__name__}, "
                f"ricevuto {type(valore).__name__}"
            )
        if self.minimo is not None and valore < self.minimo:
            raise ValueError(
                f"'{self.nome_pubblico}' minimo è {self.minimo}, ricevuto {valore}"
            )
        if self.massimo is not None and valore > self.massimo:
            raise ValueError(
                f"'{self.nome_pubblico}' massimo è {self.massimo}, ricevuto {valore}"
            )
        setattr(obj, self.nome_privato, valore)

class Sensore:
    temperatura = Validato(float, minimo=-40.0, massimo=125.0)
    umidita = Validato(float, minimo=0.0, massimo=100.0)
    nome = Validato(str)

    def __init__(self, nome: str, temperatura: float, umidita: float):
        self.nome = nome
        self.temperatura = temperatura
        self.umidita = umidita

s = Sensore("Lab-A", 22.5, 45.0)
# s.temperatura = 200.0  # ValueError: massimo è 125.0
# s.umidita = "alta"     # TypeError: richiede float
```

**Data descriptor vs Non-data descriptor** — Un *data descriptor* implementa sia `__get__` che `__set__` (o `__delete__`). Un *non-data descriptor* implementa solo `__get__`. La distinzione è cruciale per l'ordine di ricerca degli attributi di Python: i data descriptor hanno precedenza sull'`__dict__` dell'istanza, mentre i non-data descriptor cedono il passo. Questo meccanismo è quello che permette a `property` di funzionare correttamente anche quando l'istanza ha un attributo con lo stesso nome.

### Metaclass

Le **metaclass** sono classi le cui istanze sono a loro volta classi. In Python, `type` e la metaclass di default: quando si scrive `class Foo: pass`, Python invoca internamente `type('Foo', (), {})` per creare la classe `Foo`. Definendo metaclass personalizzate, si puo controllare il processo di creazione delle classi stesse.

```python
class RegistroMeta(type):
    """Metaclass che registra automaticamente ogni sottoclasse."""
    _registro: dict[str, type] = {}

    def __new__(mcs, nome, basi, namespace):
        cls = super().__new__(mcs, nome, basi, namespace)
        if basi:  # Non registra la classe base stessa
            mcs._registro[nome] = cls
        return cls

    @classmethod
    def ottieni_classe(mcs, nome: str) -> type:
        return mcs._registro[nome]

    @classmethod
    def classi_registrate(mcs) -> dict[str, type]:
        return dict(mcs._registro)

class Plugin(metaclass=RegistroMeta):
    """Classe base per i plugin."""
    def esegui(self):
        raise NotImplementedError

class PluginPDF(Plugin):
    def esegui(self):
        return "Generazione PDF..."

class PluginCSV(Plugin):
    def esegui(self):
        return "Esportazione CSV..."

class PluginExcel(Plugin):
    def esegui(self):
        return "Esportazione Excel..."

# Tutte le sottoclassi sono registrate automaticamente
print(RegistroMeta.classi_registrate())
# {'PluginPDF': <class 'PluginPDF'>, 'PluginCSV': ...}

# Creazione dinamica per nome
plugin = RegistroMeta.ottieni_classe("PluginPDF")()
print(plugin.esegui())  # "Generazione PDF..."
```

**Metaclass per validazione della struttura di classe**

```python
class ValidaInterfacciaMeta(type):
    """Metaclass che verifica che una classe implementi i metodi richiesti."""
    _metodi_richiesti: list[str] = []

    def __new__(mcs, nome, basi, namespace):
        cls = super().__new__(mcs, nome, basi, namespace)

        if basi:  # Salta la classe base
            mancanti = [
                metodo for metodo in mcs._metodi_richiesti
                if metodo not in namespace
            ]
            if mancanti:
                raise TypeError(
                    f"La classe '{nome}' non implementa i metodi "
                    f"richiesti: {', '.join(mancanti)}"
                )
        return cls

class RepositoryMeta(ValidaInterfacciaMeta):
    _metodi_richiesti = ["trova", "salva", "elimina"]

class Repository(metaclass=RepositoryMeta):
    pass

class RepositoryUtenti(Repository):
    def trova(self, id): ...
    def salva(self, entita): ...
    def elimina(self, id): ...

# Questa classe provocherebbe un TypeError:
# class RepositoryIncompleto(Repository):
#     def trova(self, id): ...
#     # Mancano 'salva' e 'elimina'
```

Le metaclass sono uno strumento avanzato che va usato con parsimonia. Nella maggior parte dei casi, decorator di classe o `__init_subclass__` offrono soluzioni piu semplici per gli stessi problemi. Le metaclass trovano impiego legittimo nella costruzione di framework e ORM (come l'ORM di Django, dove i `Model` usano una metaclass per configurare i campi del database).

### Context Manager come Pattern

Il **context manager** di Python (protocollo `__enter__`/`__exit__`) è un pattern architetturale fondamentale che va ben oltre la semplice gestione dei file. Implementa il concetto di *resource acquisition is initialization* (RAII) e può incapsulare qualsiasi scenario con semantica di setup/teardown: transazioni, lock, stati temporanei, connessioni, misurazioni e ambienti temporanei.

```python
from contextlib import contextmanager
import time
import os

class Transazione:
    """Context manager per transazioni con rollback automatico."""

    def __init__(self, registro: dict):
        self._registro = registro
        self._backup: dict = {}
        self._operazioni: list[tuple[str, str, object]] = []

    def __enter__(self):
        self._backup = dict(self._registro)
        return self

    def imposta(self, chiave: str, valore) -> None:
        self._operazioni.append(("imposta", chiave, valore))
        self._registro[chiave] = valore

    def elimina(self, chiave: str) -> None:
        self._operazioni.append(("elimina", chiave, self._registro.get(chiave)))
        self._registro.pop(chiave, None)

    def __exit__(self, tipo_exc, valore_exc, traceback):
        if tipo_exc is not None:
            # Rollback: ripristina lo stato originale
            self._registro.clear()
            self._registro.update(self._backup)
            print(f"Transazione annullata: {valore_exc}")
            return True  # Sopprime l'eccezione
        print(f"Transazione completata: {len(self._operazioni)} operazioni")
        return False

# Utilizzo — rollback automatico in caso di errore
dati = {"utente": "Alice", "ruolo": "admin"}

with Transazione(dati) as tx:
    tx.imposta("ruolo", "superadmin")
    tx.imposta("ultimo_accesso", "2026-05-24")
print(dati)  # {"utente": "Alice", "ruolo": "superadmin", "ultimo_accesso": "2026-05-24"}

with Transazione(dati) as tx:
    tx.imposta("ruolo", "guest")
    raise ValueError("Operazione non autorizzata")
# Transazione annullata — dati ripristinati
print(dati["ruolo"])  # "superadmin" — stato invariato
```

Il decoratore `@contextmanager` di `contextlib` semplifica la creazione di context manager usando generatori:

```python
@contextmanager
def ambiente_temporaneo(**variabili):
    """Imposta variabili d'ambiente temporanee, le ripristina all'uscita."""
    originali = {}
    try:
        for chiave, valore in variabili.items():
            originali[chiave] = os.environ.get(chiave)
            os.environ[chiave] = valore
        yield
    finally:
        for chiave, originale in originali.items():
            if originale is None:
                os.environ.pop(chiave, None)
            else:
                os.environ[chiave] = originale

@contextmanager
def misura_tempo(etichetta: str):
    """Misura e stampa il tempo di esecuzione di un blocco."""
    inizio = time.perf_counter()
    yield
    durata = time.perf_counter() - inizio
    print(f"[{etichetta}] Durata: {durata:.4f}s")

# Composizione di context manager
with ambiente_temporaneo(DATABASE_URL="sqlite:///test.db", DEBUG="1"):
    with misura_tempo("operazione_db"):
        print(f"DB: {os.environ['DATABASE_URL']}")
```

I context manager sono il pattern Pythonico per eccellenza per la gestione delle risorse. `contextlib` fornisce anche `ExitStack` per gestire dinamicamente un numero variabile di context manager, `suppress` per ignorare eccezioni specifiche e `asynccontextmanager` per i contesti asincroni.

### `__init_subclass__` — Hook di Registrazione

Il metodo `__init_subclass__`, introdotto in Python 3.6 (PEP 487), offre un'alternativa leggera alle metaclass per intercettare la creazione di sottoclassi. Viene invocato automaticamente sulla classe genitore ogni volta che viene definita una nuova sottoclasse.

```python
class Serializzatore:
    """Classe base con auto-registrazione tramite __init_subclass__."""
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, formato: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if formato:
            cls._formato = formato
            Serializzatore._registry[formato] = cls

    @classmethod
    def per_formato(cls, formato: str) -> "Serializzatore":
        classe = cls._registry.get(formato)
        if classe is None:
            formati = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Formato '{formato}' non supportato. Disponibili: {formati}"
            )
        return classe()

    def serializza(self, dati) -> str:
        raise NotImplementedError

    def deserializza(self, payload: str):
        raise NotImplementedError

class SerializzatoreJSON(Serializzatore, formato="json"):
    def serializza(self, dati) -> str:
        import json
        return json.dumps(dati)

    def deserializza(self, payload: str):
        import json
        return json.loads(payload)

class SerializzatoreCSV(Serializzatore, formato="csv"):
    def serializza(self, dati: list[dict]) -> str:
        if not dati:
            return ""
        intestazione = ",".join(dati[0].keys())
        righe = [",".join(str(v) for v in riga.values()) for riga in dati]
        return intestazione + "\n" + "\n".join(righe)

    def deserializza(self, payload: str) -> list[dict]:
        righe = payload.strip().split("\n")
        campi = righe[0].split(",")
        return [dict(zip(campi, r.split(","))) for r in righe[1:]]

# Le sottoclassi si registrano automaticamente alla definizione
serializzatore = Serializzatore.per_formato("json")
print(serializzatore.serializza({"nome": "Alice", "eta": 30}))

print(Serializzatore._registry)
# {"json": <class 'SerializzatoreJSON'>, "csv": <class 'SerializzatoreCSV'>}
```

Il vantaggio di `__init_subclass__` rispetto alle metaclass è la semplicità: non richiede la comprensione del protocollo metaclass, non introduce conflitti di metaclass nell'ereditarietà multipla e rende esplicito il meccanismo di registrazione. È la soluzione preferita per plugin system, registry pattern e validazione della struttura delle sottoclassi in Python moderno.

**Validazione della struttura delle sottoclassi**

```python
class ValidatoBase:
    """Verifica che le sottoclassi implementino gli attributi richiesti."""
    _attributi_richiesti: list[str] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr in cls._attributi_richiesti:
            if not hasattr(cls, attr) or getattr(cls, attr) is None:
                raise TypeError(
                    f"La classe '{cls.__name__}' deve definire l'attributo '{attr}'"
                )

class HandlerHTTP(ValidatoBase):
    _attributi_richiesti = ["metodo", "percorso"]
    metodo: str
    percorso: str

class HandlerLogin(HandlerHTTP):
    metodo = "POST"
    percorso = "/api/login"

    def gestisci(self, richiesta):
        return {"status": "ok"}

# Questa definizione provocherebbe TypeError:
# class HandlerIncompleto(HandlerHTTP):
#     metodo = "GET"
#     # Manca 'percorso' → TypeError alla definizione della classe
```

---

## Anti-Pattern

Gli anti-pattern sono soluzioni ricorrenti che *sembrano* risolvere un problema ma in realta introducono piu problemi di quanti ne risolvano. Riconoscerli e tanto importante quanto conoscere i pattern corretti.

### God Object

Il **God Object** (oggetto divino) e una classe che sa troppo o fa troppo. Concentra in se troppe responsabilita, violando il principio di responsabilita singola (SRP). Sintomi tipici: file con migliaia di righe, decine di metodi non correlati tra loro, forte accoppiamento con il resto del sistema.

```python
# ANTI-PATTERN: God Object
class Applicazione:
    def gestisci_utente(self, ...): ...
    def invia_email(self, ...): ...
    def genera_report(self, ...): ...
    def processa_pagamento(self, ...): ...
    def scrivi_log(self, ...): ...
    def gestisci_cache(self, ...): ...
    # Centinaia di altri metodi...

# SOLUZIONE: dividere in classi con responsabilita specifiche
class GestoreUtenti: ...
class ServizioEmail: ...
class GeneratoreReport: ...
class ProcessorePagamenti: ...
```

### Spaghetti Code

Lo **Spaghetti Code** e caratterizzato da un flusso di controllo intricato e difficile da seguire: funzioni lunghe, annidamento eccessivo, `goto` concettuali (in Python: eccezioni usate per il flusso di controllo), assenza di struttura modulare. Il codice diventa impossibile da testare, comprendere e modificare.

La soluzione e applicare principi di progettazione: suddividere le funzioni lunghe, eliminare l'annidamento eccessivo (con early return), estrarre la logica in moduli e classi coerenti.

### Premature Optimization

L'**Ottimizzazione Prematura** e l'abitudine di ottimizzare il codice prima di avere dati concreti sui colli di bottiglia. Come affermava Donald Knuth: *"L'ottimizzazione prematura e la radice di ogni male"*. Porta a codice complesso, difficile da leggere e manutenere, spesso senza benefici reali in termini di prestazioni.

L'approccio corretto e: scrivere codice chiaro e corretto, misurare le prestazioni con strumenti di profiling (`cProfile`, `line_profiler`), e ottimizzare solo i punti che rappresentano effettivamente un collo di bottiglia.

### Over-Engineering

L'**Over-Engineering** (sovra-ingegnerizzazione) consiste nel progettare soluzioni eccessivamente complesse per problemi semplici. Si manifesta con l'uso di pattern dove non servono, gerarchie di classi profonde per gestire un singolo caso d'uso, astrazioni premature e configurabilita non richiesta.

```python
# OVER-ENGINEERING: tre classi e un pattern per una semplice somma
class StrategiaSomma(ABC):
    @abstractmethod
    def esegui(self, a, b): pass

class SommaIntera(StrategiaSomma):
    def esegui(self, a, b):
        return a + b

class Calcolatrice:
    def __init__(self, strategia: StrategiaSomma):
        self._strategia = strategia

    def calcola(self, a, b):
        return self._strategia.esegui(a, b)

# SOLUZIONE: semplicita
def somma(a, b):
    return a + b
```

### Copy-Paste Programming

Il **Copy-Paste Programming** consiste nel duplicare codice anziché estrarre funzionalita comuni in funzioni, classi o moduli riutilizzabili. Il codice duplicato diventa rapidamente incoerente: quando si corregge un bug in una copia, le altre copie rimangono difettose. La soluzione e il principio DRY (Don't Repeat Yourself): estrarre la logica comune in un unico punto e riutilizzarla.

### Code Smells — Segnali di Allarme nel Codice

I **code smells** non sono bug, ma indicatori di debolezze progettuali che rendono il codice fragile, difficile da estendere e propenso a sviluppare difetti. Riconoscerli precocemente permette di intervenire con refactoring mirati prima che il debito tecnico diventi ingestibile.

**Feature Envy** — Un metodo utilizza più dati e metodi di un'altra classe rispetto alla propria. Questo indica che il metodo dovrebbe probabilmente appartenere all'altra classe:

```python
# CODE SMELL: Feature Envy
class Rapporto:
    def genera_sommario(self, ordine):
        # Questo metodo "invidia" la classe Ordine
        totale = sum(a.prezzo * a.quantita for a in ordine.articoli)
        sconto = ordine.calcola_sconto()
        iva = ordine.calcola_iva()
        return f"Totale: {totale - sconto + iva}"

# REFACTORING: spostare la logica nella classe Ordine
class Ordine:
    def sommario(self) -> str:
        return f"Totale: {self.totale_finale()}"
```

**Data Clumps** — Gruppi di dati che appaiono sempre insieme in firme di metodi o attributi di classe. Devono essere estratti in una dataclass o named tuple:

```python
# CODE SMELL: Data Clumps
def crea_fattura(nome_cliente, indirizzo_cliente, citta_cliente,
                 cap_cliente, telefono_cliente):
    ...

# REFACTORING: estrarre in una dataclass
@dataclass
class IndirizzoCliente:
    nome: str
    indirizzo: str
    citta: str
    cap: str
    telefono: str

def crea_fattura(cliente: IndirizzoCliente):
    ...
```

**Shotgun Surgery** — Una singola modifica concettuale richiede piccole modifiche in molte classi diverse. È il sintomo di responsabilità distribuite anziché coesive. La soluzione è raggruppare la logica correlata in un modulo o classe unica.

**Primitive Obsession** — Uso eccessivo di tipi primitivi (stringhe, interi) dove un tipo di dominio sarebbe più espressivo e sicuro. Ad esempio, usare `str` per email, URL, codice fiscale anziché creare tipi dedicati con validazione integrata.

**Long Parameter List** — Funzioni con molti parametri indicano che la funzione fa troppo o che i parametri dovrebbero essere raggruppati in un oggetto. In Python, questo si risolve con dataclass, `TypedDict` o il pattern Builder.

**Dead Code** — Codice mai raggiunto: funzioni mai chiamate, rami `if` impossibili, import inutilizzati. Il dead code aggiunge rumore cognitivo e va rimosso. Strumenti come `vulture` e `pylint` lo rilevano automaticamente.

I tool di analisi statica per individuare code smells in Python includono `pylint` (analisi generale), `flake8` (stile e complessità), `radon` (complessità ciclomatica), `mypy` (type checking) e `bandit` (vulnerabilità di sicurezza). Integrarli nella CI/CD permette di intercettare i code smells prima che raggiungano il repository condiviso.

---

## Principi SOLID in Python

I principi **SOLID**, formulati da Robert C. Martin, sono cinque linee guida fondamentali per la progettazione orientata agli oggetti. In Python, l'applicazione di questi principi si adatta alle peculiarità del linguaggio — duck typing, funzioni di prima classe, protocolli — producendo codice idiomatico e robusto.

### S — Single Responsibility Principle (SRP)

Ogni classe deve avere una sola responsabilità, ovvero una sola ragione per cambiare. In Python, dove i moduli sono cittadini di prima classe, il SRP si applica anche a livello di modulo e funzione.

```python
# VIOLAZIONE SRP: la classe fa troppe cose
class GestoreOrdini:
    def crea_ordine(self, dati): ...
    def calcola_totale(self, ordine): ...
    def salva_nel_database(self, ordine): ...
    def invia_email_conferma(self, ordine): ...
    def genera_pdf_fattura(self, ordine): ...

# SRP APPLICATO: ogni classe ha una responsabilità
class Ordine:
    """Logica di dominio dell'ordine."""
    def __init__(self, articoli: list[dict]):
        self.articoli = articoli

    def totale(self) -> float:
        return sum(a["prezzo"] * a["quantita"] for a in self.articoli)

class RepositoryOrdini:
    """Persistenza dell'ordine nel database."""
    def salva(self, ordine: Ordine) -> int:
        print(f"Ordine salvato con totale: {ordine.totale()}")
        return 1  # ID simulato

class NotificatoreOrdini:
    """Invio notifiche relative agli ordini."""
    def invia_conferma(self, ordine: Ordine, email: str) -> None:
        print(f"Conferma inviata a {email}")

class GeneratoreFatture:
    """Generazione documenti fiscali."""
    def genera_pdf(self, ordine: Ordine) -> bytes:
        return b"%PDF-simulato"
```

### O — Open/Closed Principle (OCP)

Le entità software devono essere aperte all'estensione ma chiuse alla modifica. In Python, questo si realizza tramite ereditarietà, composizione, protocolli e il pattern Strategy con funzioni first-class.

```python
from typing import Protocol

class CalcolatoreSconto(Protocol):
    """Protocollo — qualsiasi callable con questa firma è uno sconto valido."""
    def __call__(self, prezzo: float, quantita: int) -> float: ...

def sconto_volume(prezzo: float, quantita: int) -> float:
    if quantita >= 100:
        return prezzo * 0.15
    if quantita >= 50:
        return prezzo * 0.10
    return 0.0

def sconto_stagionale(prezzo: float, quantita: int) -> float:
    from datetime import date
    mese = date.today().month
    if mese in (1, 7):  # Saldi invernali ed estivi
        return prezzo * 0.20
    return 0.0

class MotorePrezzo:
    """Aperto all'estensione (nuovi sconti), chiuso alla modifica."""

    def __init__(self):
        self._sconti: list[CalcolatoreSconto] = []

    def aggiungi_sconto(self, sconto: CalcolatoreSconto) -> None:
        self._sconti.append(sconto)

    def prezzo_finale(self, prezzo_base: float, quantita: int) -> float:
        sconto_totale = sum(
            s(prezzo_base, quantita) for s in self._sconti
        )
        return max(0, prezzo_base * quantita - sconto_totale)

# Aggiungere un nuovo sconto non richiede modifiche al MotorePrezzo
motore = MotorePrezzo()
motore.aggiungi_sconto(sconto_volume)
motore.aggiungi_sconto(sconto_stagionale)
print(motore.prezzo_finale(10.0, 100))
```

### L — Liskov Substitution Principle (LSP)

Le sottoclassi devono poter sostituire le classi base senza alterare la correttezza del programma. Le precondizioni non possono essere rafforzate, le postcondizioni non possono essere indebolite.

```python
from abc import ABC, abstractmethod

class Collezione(ABC):
    @abstractmethod
    def aggiungi(self, elemento) -> None:
        pass

    @abstractmethod
    def contiene(self, elemento) -> bool:
        pass

    @abstractmethod
    def dimensione(self) -> int:
        pass

class ListaOrdinata(Collezione):
    """Rispetta LSP: soddisfa il contratto di Collezione."""
    def __init__(self):
        self._elementi: list = []

    def aggiungi(self, elemento) -> None:
        import bisect
        bisect.insort(self._elementi, elemento)

    def contiene(self, elemento) -> bool:
        import bisect
        i = bisect.bisect_left(self._elementi, elemento)
        return i < len(self._elementi) and self._elementi[i] == elemento

    def dimensione(self) -> int:
        return len(self._elementi)

# VIOLAZIONE LSP: restringe le precondizioni
class CollezioneRistretta(Collezione):
    def __init__(self, tipo_ammesso: type):
        self._tipo = tipo_ammesso
        self._elementi: list = []

    def aggiungi(self, elemento) -> None:
        # Rafforza la precondizione — viola LSP
        if not isinstance(elemento, self._tipo):
            raise TypeError(f"Solo {self._tipo.__name__} ammessi")
        self._elementi.append(elemento)

    def contiene(self, elemento) -> bool:
        return elemento in self._elementi

    def dimensione(self) -> int:
        return len(self._elementi)

# Codice client che si aspetta qualsiasi Collezione si rompe con CollezioneRistretta
def popola_collezione(c: Collezione):
    c.aggiungi(1)
    c.aggiungi("stringa")  # Fallisce con CollezioneRistretta!
```

### I — Interface Segregation Principle (ISP)

I client non devono essere forzati a dipendere da interfacce che non utilizzano. In Python, questo si realizza con `Protocol` e classi astratte piccole e focalizzate.

```python
from typing import Protocol, runtime_checkable

# VIOLAZIONE ISP: interfaccia troppo ampia
class LavoratoreCompleto(Protocol):
    def lavora(self) -> None: ...
    def mangia(self) -> None: ...
    def dorme(self) -> None: ...
    def programma(self) -> None: ...
    def gestisci_team(self) -> None: ...

# ISP APPLICATO: interfacce piccole e specifiche
@runtime_checkable
class Lavoratore(Protocol):
    def lavora(self) -> None: ...

@runtime_checkable
class Programmatore(Protocol):
    def programma(self) -> None: ...

@runtime_checkable
class Manager(Protocol):
    def gestisci_team(self) -> None: ...

class SviluppatoreSenior:
    """Implementa solo le interfacce pertinenti."""
    def lavora(self) -> None:
        print("Lavoro in corso...")

    def programma(self) -> None:
        print("Scrittura codice...")

# Type checking strutturale — nessuna ereditarietà esplicita necessaria
def assegna_compito(lavoratore: Lavoratore) -> None:
    lavoratore.lavora()

dev = SviluppatoreSenior()
assegna_compito(dev)  # Funziona — soddisfa il Protocol Lavoratore
print(isinstance(dev, Lavoratore))      # True (grazie a runtime_checkable)
print(isinstance(dev, Manager))         # False
```

### D — Dependency Inversion Principle (DIP)

I moduli di alto livello non devono dipendere dai moduli di basso livello. Entrambi devono dipendere da astrazioni. Le astrazioni non devono dipendere dai dettagli; i dettagli devono dipendere dalle astrazioni.

```python
from typing import Protocol
from dataclasses import dataclass

class Repository(Protocol):
    """Astrazione — contratto per l'accesso ai dati."""
    def trova_per_id(self, id: int) -> dict | None: ...
    def salva(self, entita: dict) -> int: ...

class NotificatoreProtocol(Protocol):
    """Astrazione — contratto per le notifiche."""
    def invia(self, destinatario: str, messaggio: str) -> None: ...

# Implementazioni concrete di basso livello
class RepositoryPostgreSQL:
    def trova_per_id(self, id: int) -> dict | None:
        print(f"[PostgreSQL] SELECT * FROM entita WHERE id = {id}")
        return {"id": id, "nome": "Esempio"}

    def salva(self, entita: dict) -> int:
        print(f"[PostgreSQL] INSERT INTO entita VALUES ...")
        return 1

class NotificatoreEmail:
    def invia(self, destinatario: str, messaggio: str) -> None:
        print(f"[Email] A: {destinatario} — {messaggio}")

# Modulo di alto livello — dipende SOLO dalle astrazioni
class ServizioUtenti:
    def __init__(self, repo: Repository, notificatore: NotificatoreProtocol):
        self._repo = repo
        self._notificatore = notificatore

    def registra(self, nome: str, email: str) -> int:
        id_utente = self._repo.salva({"nome": nome, "email": email})
        self._notificatore.invia(email, f"Benvenuto, {nome}!")
        return id_utente

# L'assemblaggio avviene al livello più esterno (composition root)
servizio = ServizioUtenti(
    repo=RepositoryPostgreSQL(),
    notificatore=NotificatoreEmail(),
)
servizio.registra("Alice", "alice@esempio.com")
```

Il DIP è il fondamento della dependency injection e della testabilità: nei test, si iniettano mock che rispettano lo stesso Protocol, senza modificare il codice di business logic.

### Riepilogo SOLID — Quando Applicare e Quando No

I principi SOLID non sono regole assolute ma linee guida pragmatiche. Applicarli eccessivamente a codice semplice produce over-engineering; ignorarli in codice complesso produce debito tecnico. La tabella seguente sintetizza quando ogni principio ha il maggiore impatto:

| Principio | Applica quando... | Evita quando... |
|---|---|---|
| **SRP** | La classe supera 200 righe o ha metodi non correlati | La responsabilità è intrinsecamente unica e coesa |
| **OCP** | Prevedi estensioni concrete e frequenti (plugin, strategie) | Il dominio è stabile e le varianti non cresceranno |
| **LSP** | Stai progettando gerarchie di ereditarietà condivise | Usi composizione e non esponi la gerarchia al client |
| **ISP** | L'interfaccia ha metodi che molti implementatori non usano | L'interfaccia è piccola (2-3 metodi) e coesa |
| **DIP** | Il modulo di alto livello è riutilizzabile o testabile separatamente | Lo script è un one-off o l'accoppiamento è trascurabile |

In Python, la combinazione di `Protocol` (ISP), constructor injection (DIP) e funzioni di prima classe (OCP con Strategy) copre la grande maggioranza dei casi dove SOLID aggiunge valore concreto. Il duck typing nativo del linguaggio rende spesso superflua la creazione di interfacce esplicite per piccole API interne.

### Riconoscere Violazioni SOLID nel Codice Esistente

**Segnali di violazione SRP:**
- La classe ha metodi che importano moduli non correlati tra loro
- Il nome della classe contiene "Manager", "Handler", "Utils" senza qualificazione
- I test della classe richiedono molti mock non correlati

**Segnali di violazione OCP:**
- Catene di `if/elif` che crescono ogni volta che si aggiunge una variante
- Modifiche a una classe ogni volta che si aggiunge un nuovo tipo di prodotto
- Costanti magiche sparse nel codice anziché registry o mapping

**Segnali di violazione LSP:**
- Sottoclassi che lanciano `NotImplementedError` per metodi ereditati
- Codice client che controlla `isinstance` prima di chiamare un metodo
- Override che cambiano la semantica del metodo (effetti collaterali non attesi)

**Segnali di violazione ISP:**
- Classi concrete che implementano metodi con `pass` o `raise NotImplementedError`
- Interfacce astratte con più di 5-6 metodi
- I test di un componente richiedono mock per metodi che il componente non usa

**Segnali di violazione DIP:**
- Costruttori che istanziano direttamente le proprie dipendenze (`self._db = PostgreSQL()`)
- Moduli di alto livello che importano direttamente implementazioni di basso livello
- Impossibilità di testare una classe senza un database o servizio esterno reale

---

## Dependency Injection

La **Dependency Injection** (DI) è un pattern in cui un oggetto riceve le proprie dipendenze dall'esterno anziché crearle internamente. Non è un pattern GoF, ma è strettamente legato al Dependency Inversion Principle (la "D" di SOLID) e rappresenta una delle pratiche più importanti per scrivere codice testabile, modulare e manutenibile.

### Tipi di Injection

Esistono tre modi fondamentali per iniettare le dipendenze in Python:

```python
from typing import Protocol

class Logger(Protocol):
    def log(self, messaggio: str) -> None: ...

class LoggerConsole:
    def log(self, messaggio: str) -> None:
        print(f"[LOG] {messaggio}")

# 1. Constructor Injection (preferito)
class ServizioA:
    def __init__(self, logger: Logger):
        self._logger = logger

# 2. Setter Injection (per dipendenze opzionali)
class ServizioB:
    def __init__(self):
        self._logger: Logger | None = None

    @property
    def logger(self) -> Logger | None:
        return self._logger

    @logger.setter
    def logger(self, logger: Logger) -> None:
        self._logger = logger

# 3. Method Injection (per dipendenze specifiche di un'operazione)
class ServizioC:
    def elabora(self, dati: str, logger: Logger) -> str:
        logger.log(f"Elaborazione: {dati}")
        return dati.upper()
```

La **constructor injection** è l'approccio preferito perché rende le dipendenze esplicite e garantisce che l'oggetto sia sempre in uno stato valido.

### Composition Root

Il **composition root** è il punto unico dell'applicazione in cui tutte le dipendenze vengono assemblate. In genere coincide con il punto di ingresso (`main.py`, `app.py`):

```python
# composition_root.py — assemblaggio delle dipendenze
from typing import Protocol

class Cache(Protocol):
    def ottieni(self, chiave: str) -> str | None: ...
    def imposta(self, chiave: str, valore: str) -> None: ...

class CacheRedis:
    def __init__(self, url: str):
        self._url = url
    def ottieni(self, chiave: str) -> str | None:
        return None  # Simulato
    def imposta(self, chiave: str, valore: str) -> None:
        pass

class CacheInMemoria:
    def __init__(self):
        self._dati: dict[str, str] = {}
    def ottieni(self, chiave: str) -> str | None:
        return self._dati.get(chiave)
    def imposta(self, chiave: str, valore: str) -> None:
        self._dati[chiave] = valore

class ServizioProdotti:
    def __init__(self, cache: Cache, logger: Logger):
        self._cache = cache
        self._logger = logger

    def cerca(self, query: str) -> list[str]:
        self._logger.log(f"Ricerca: {query}")
        cached = self._cache.ottieni(f"ricerca:{query}")
        if cached:
            return cached.split(",")
        risultati = [f"Prodotto-{i}" for i in range(5)]
        self._cache.imposta(f"ricerca:{query}", ",".join(risultati))
        return risultati

def crea_applicazione(ambiente: str = "produzione") -> ServizioProdotti:
    """Composition root — assembla le dipendenze in base all'ambiente."""
    logger = LoggerConsole()

    if ambiente == "produzione":
        cache = CacheRedis(url="redis://localhost:6379")
    else:
        cache = CacheInMemoria()

    return ServizioProdotti(cache=cache, logger=logger)

# Punto di ingresso
servizio = crea_applicazione(ambiente="sviluppo")
print(servizio.cerca("widget"))
```

### Framework di Dependency Injection

Per applicazioni di grandi dimensioni con grafi di dipendenze complessi, i framework di DI automatizzano il wiring. I due più diffusi in Python sono `dependency-injector` e `injector`.

**`dependency-injector`** — Il framework più maturo e completo, con supporto per container, provider e wiring automatico:

```python
# Esempio concettuale con dependency-injector
# pip install dependency-injector
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """Container IoC — dichiara come costruire le dipendenze."""

    config = providers.Configuration()

    logger = providers.Singleton(LoggerConsole)

    cache = providers.Selector(
        config.ambiente,
        produzione=providers.Singleton(CacheRedis, url=config.redis_url),
        sviluppo=providers.Singleton(CacheInMemoria),
    )

    servizio_prodotti = providers.Factory(
        ServizioProdotti,
        cache=cache,
        logger=logger,
    )

# Il container gestisce il ciclo di vita e le dipendenze
container = Container()
container.config.ambiente.from_value("sviluppo")
container.config.redis_url.from_value("redis://localhost:6379")

servizio = container.servizio_prodotti()
```

**`injector`** — Un framework più leggero ispirato a Guice di Java, con supporto per i type hints:

```python
# Esempio concettuale con injector
# pip install injector
from injector import Injector, inject, Module, singleton, provider

class AppModule(Module):
    def configure(self, binder):
        binder.bind(Logger, to=LoggerConsole, scope=singleton)

    @singleton
    @provider
    def provide_cache(self) -> Cache:
        return CacheInMemoria()

class ServizioIniettato:
    @inject
    def __init__(self, cache: Cache, logger: Logger):
        self._cache = cache
        self._logger = logger

iniettore = Injector([AppModule()])
servizio = iniettore.get(ServizioIniettato)
```

Per la maggior parte dei progetti Python di dimensioni piccole e medie, la DI manuale tramite constructor injection e un composition root esplicito è sufficiente e preferibile alla complessità di un framework. I framework diventano utili quando il grafo delle dipendenze supera le 20-30 classi o quando si gestiscono ambienti multipli con configurazioni diverse.

---

## Pattern Funzionali

Python è un linguaggio multi-paradigma e supporta costrutti di programmazione funzionale che danno origine a pattern distinti da quelli OOP classici. Questi pattern enfatizzano immutabilità, composizione di funzioni e assenza di effetti collaterali.

### Currying e Applicazione Parziale

Il **currying** trasforma una funzione che accetta N argomenti in una catena di N funzioni, ciascuna che accetta un singolo argomento. L'**applicazione parziale** fissa alcuni argomenti di una funzione, producendo una nuova funzione con meno parametri. In Python, `functools.partial` è lo strumento nativo per l'applicazione parziale.

```python
from functools import partial

# Applicazione parziale con functools.partial
def moltiplica(a: float, b: float) -> float:
    return a * b

doppio = partial(moltiplica, 2)
triplo = partial(moltiplica, 3)

print(doppio(5))   # 10
print(triplo(5))   # 15

# Currying manuale con closure
def curry_log(livello: str):
    def con_prefisso(prefisso: str):
        def log(messaggio: str) -> str:
            return f"[{livello}] {prefisso}: {messaggio}"
        return log
    return con_prefisso

log_errore_db = curry_log("ERRORE")("Database")
print(log_errore_db("Connessione persa"))
# [ERRORE] Database: Connessione persa

# Decorator generico per currying automatico
def curry(func):
    """Trasforma una funzione in versione curried."""
    import inspect
    n_args = len(inspect.signature(func).parameters)

    def curried(*args):
        if len(args) >= n_args:
            return func(*args[:n_args])
        return lambda *more: curried(*args, *more)
    return curried

@curry
def somma_tre(a, b, c):
    return a + b + c

print(somma_tre(1)(2)(3))     # 6
print(somma_tre(1, 2)(3))     # 6
print(somma_tre(1)(2, 3))     # 6
```

### Pipe e Composizione di Funzioni

Il pattern **pipe** applica una sequenza di trasformazioni a un valore iniziale, dove l'output di ogni funzione diventa l'input della successiva. La **composizione** combina funzioni in una nuova funzione, senza eseguirle immediatamente.

```python
from typing import Callable, TypeVar
from functools import reduce

T = TypeVar("T")

def pipe(valore, *funzioni: Callable):
    """Applica una catena di funzioni a un valore iniziale."""
    return reduce(lambda acc, fn: fn(acc), funzioni, valore)

def componi(*funzioni: Callable) -> Callable:
    """Compone funzioni da destra a sinistra (ordine matematico)."""
    def composizione(valore):
        for fn in reversed(funzioni):
            valore = fn(valore)
        return valore
    return composizione

# Trasformazioni come funzioni pure
def normalizza(testo: str) -> str:
    return testo.strip().lower()

def rimuovi_punteggiatura(testo: str) -> str:
    return "".join(c for c in testo if c.isalnum() or c.isspace())

def dividi_parole(testo: str) -> list[str]:
    return testo.split()

def conta_parole(parole: list[str]) -> dict[str, int]:
    conteggio: dict[str, int] = {}
    for parola in parole:
        conteggio[parola] = conteggio.get(parola, 0) + 1
    return conteggio

# Pipe: leggibile come una pipeline di dati
risultato = pipe(
    "  Ciao Mondo! Ciao Python, ciao!  ",
    normalizza,
    rimuovi_punteggiatura,
    dividi_parole,
    conta_parole,
)
print(risultato)  # {'ciao': 3, 'mondo': 1, 'python': 1}

# Composizione: crea una funzione riutilizzabile
preprocessa = componi(dividi_parole, rimuovi_punteggiatura, normalizza)
print(preprocessa("  Testo di PROVA!  "))  # ['testo', 'di', 'prova']
```

La libreria `toolz` offre implementazioni robuste di `pipe`, `compose`, `curry` e molte altre utility funzionali. Per pipeline più complesse, `toolz.functoolz.pipe` gestisce correttamente generatori ed effetti collaterali.

### Monad Pattern (Maybe / Result)

Le **monad** incapsulano valori con contesto aggiuntivo (errore, assenza, effetto) e permettono di concatenare operazioni senza controlli espliciti a ogni passo. In Python, il pattern monadico più utile è il **Result** (o **Either**), che rappresenta il successo o il fallimento di un'operazione senza usare eccezioni per il flusso di controllo.

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Callable

T = TypeVar("T")
U = TypeVar("U")

@dataclass(frozen=True)
class Successo(Generic[T]):
    valore: T

    def mappa(self, fn: Callable[[T], U]) -> "Risultato[U]":
        try:
            return Successo(fn(self.valore))
        except Exception as e:
            return Fallimento(str(e))

    def poi(self, fn: Callable[[T], "Risultato[U]"]) -> "Risultato[U]":
        """Bind/flatMap — concatena operazioni che restituiscono Risultato."""
        try:
            return fn(self.valore)
        except Exception as e:
            return Fallimento(str(e))

    @property
    def ok(self) -> bool:
        return True

@dataclass(frozen=True)
class Fallimento:
    errore: str

    def mappa(self, fn) -> "Fallimento":
        return self  # Propaga l'errore senza eseguire fn

    def poi(self, fn) -> "Fallimento":
        return self

    @property
    def ok(self) -> bool:
        return False

Risultato = Successo[T] | Fallimento

# Pipeline di validazione con Result monad
def valida_email(email: str) -> Risultato[str]:
    if "@" not in email:
        return Fallimento("Email non valida: manca @")
    return Successo(email.lower().strip())

def valida_eta(eta_str: str) -> Risultato[int]:
    try:
        eta = int(eta_str)
    except ValueError:
        return Fallimento(f"Eta non numerica: {eta_str}")
    if eta < 0 or eta > 150:
        return Fallimento(f"Eta fuori range: {eta}")
    return Successo(eta)

def crea_profilo(email: str, eta: int) -> Risultato[dict]:
    return Successo({"email": email, "eta": eta, "attivo": True})

# Concatenazione monadica — l'errore interrompe la catena
risultato_email = valida_email("ALICE@esempio.com")
risultato_eta = valida_eta("30")

if risultato_email.ok and risultato_eta.ok:
    profilo = crea_profilo(risultato_email.valore, risultato_eta.valore)
    print(profilo)  # Successo(valore={'email': 'alice@esempio.com', ...})

# Con errore — il Fallimento si propaga
risultato_cattivo = valida_email("invalido").poi(
    lambda e: crea_profilo(e, 25)
)
print(risultato_cattivo)  # Fallimento(errore='Email non valida: manca @')
```

La libreria `returns` (PyPI) fornisce implementazioni complete di Result, Maybe, IO e altre monad con supporto completo per type checking e pipeline funzionali. Per progetti di produzione, è preferibile usare `returns` piuttosto che re-implementare le monad da zero.

### Funzioni di Ordine Superiore come Pattern

Le **funzioni di ordine superiore** (higher-order functions) accettano funzioni come argomenti o restituiscono funzioni come risultato. In Python, `map`, `filter`, `reduce`, `sorted` sono funzioni di ordine superiore native. Questo concetto è alla base di molti pattern funzionali avanzati.

```python
from typing import Callable, TypeVar
from functools import reduce

T = TypeVar("T")

def mappa_selettiva(
    predicato: Callable[[T], bool],
    trasformazione: Callable[[T], T],
    elementi: list[T],
) -> list[T]:
    """Applica una trasformazione solo agli elementi che soddisfano il predicato."""
    return [
        trasformazione(e) if predicato(e) else e
        for e in elementi
    ]

# Raddoppia solo i numeri pari
numeri = [1, 2, 3, 4, 5, 6, 7, 8]
risultato = mappa_selettiva(
    predicato=lambda x: x % 2 == 0,
    trasformazione=lambda x: x * 2,
    elementi=numeri,
)
print(risultato)  # [1, 4, 3, 8, 5, 12, 7, 16]
```

**Memoizzazione** — Un pattern funzionale cruciale per il caching dei risultati di funzioni pure. Python lo supporta nativamente con `functools.lru_cache` e `functools.cache` (Python 3.9+):

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """Fibonacci con memoizzazione automatica — da O(2^n) a O(n)."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(100))  # 354224848179261915075 — istantaneo
print(fibonacci.cache_info())
# CacheInfo(hits=98, misses=101, maxsize=128, currsize=101)
```

La memoizzazione funziona correttamente solo con funzioni pure (senza effetti collaterali) e argomenti hashable. Per funzioni con argomenti non hashable (dizionari, liste), si possono convertire gli argomenti in tuple frozen o usare un wrapper personalizzato.

### Immutabilità Funzionale in Python

L'immutabilità è il pilastro della programmazione funzionale. In Python, si ottiene tramite diverse strutture:

```python
from dataclasses import dataclass, replace
from typing import NamedTuple

# NamedTuple — immutabile per definizione
class Punto(NamedTuple):
    x: float
    y: float

    def trasla(self, dx: float, dy: float) -> "Punto":
        """Restituisce un NUOVO punto — non modifica l'originale."""
        return Punto(self.x + dx, self.y + dy)

# Frozen dataclass — immutabilità verificata dal decoratore
@dataclass(frozen=True)
class Configurazione:
    host: str
    porta: int
    debug: bool = False

    def con_debug(self) -> "Configurazione":
        """Crea una copia con debug attivato."""
        return replace(self, debug=True)

config = Configurazione(host="localhost", porta=8080)
config_debug = config.con_debug()
# config.debug = True  # FrozenInstanceError!

# tuple e frozenset — collezioni immutabili native
coordinate = (1.0, 2.0, 3.0)  # Immutabile
tag_univoci = frozenset({"python", "design-patterns", "funzionale"})  # Immutabile
```

La funzione `dataclasses.replace()` è il modo idiomatico per creare copie modificate di dataclass frozen — equivale al pattern `copy-on-write` della programmazione funzionale.

---

## Pattern di Concorrenza

I pattern di concorrenza gestiscono l'esecuzione parallela o asincrona di operazioni, la coordinazione tra task e la comunicazione tra componenti concorrenti. Python offre due ecosistemi principali: `threading`/`multiprocessing` per concorrenza basata su thread/processi e `asyncio` per I/O asincrono cooperativo.

### Producer-Consumer

Il pattern **Producer-Consumer** disaccoppia la produzione di dati dal loro consumo tramite una coda intermedia. I produttori inseriscono elementi nella coda senza preoccuparsi di chi li elaborerà; i consumatori prelevano elementi senza conoscere la sorgente.

```python
import asyncio
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Compito:
    id: int
    payload: str
    priorita: int = 0
    creato: str = ""

    def __post_init__(self):
        if not self.creato:
            self.creato = datetime.now().isoformat()

async def produttore(
    nome: str, coda: asyncio.Queue[Compito], n_compiti: int
) -> None:
    """Produce compiti e li inserisce nella coda."""
    for i in range(n_compiti):
        compito = Compito(id=i, payload=f"{nome}-lavoro-{i}", priorita=i % 3)
        await coda.put(compito)
        print(f"[Produttore {nome}] Inserito compito {compito.id}")
        await asyncio.sleep(0.1)  # Simula tempo di generazione

async def consumatore(nome: str, coda: asyncio.Queue[Compito]) -> None:
    """Consuma compiti dalla coda fino a ricevere None."""
    while True:
        compito = await coda.get()
        if compito is None:
            coda.task_done()
            break
        print(f"[Consumatore {nome}] Elabora: {compito.payload}")
        await asyncio.sleep(0.2)  # Simula tempo di elaborazione
        coda.task_done()

async def main_producer_consumer():
    coda: asyncio.Queue[Compito | None] = asyncio.Queue(maxsize=10)

    # Avvia 2 produttori e 3 consumatori
    produttori = [
        asyncio.create_task(produttore("P1", coda, 5)),
        asyncio.create_task(produttore("P2", coda, 5)),
    ]
    consumatori = [
        asyncio.create_task(consumatore(f"C{i}", coda))
        for i in range(3)
    ]

    # Attendi che i produttori finiscano
    await asyncio.gather(*produttori)

    # Segnala ai consumatori di terminare
    for _ in consumatori:
        await coda.put(None)

    await asyncio.gather(*consumatori)
    print("Pipeline completata")

# asyncio.run(main_producer_consumer())
```

### Pipeline Asincrona

Il pattern **Pipeline** organizza l'elaborazione in fasi sequenziali connesse da code. Ogni fase è specializzata in un'operazione specifica e può avere il proprio livello di concorrenza.

```python
import asyncio
from typing import Any

async def fase_estrazione(
    coda_uscita: asyncio.Queue, sorgente: list[str]
) -> None:
    """Fase 1: estrae dati grezzi dalla sorgente."""
    for elemento in sorgente:
        await coda_uscita.put({"grezzo": elemento, "fase": "estratto"})
        print(f"[Estrazione] {elemento}")
    await coda_uscita.put(None)  # Segnale di terminazione

async def fase_trasformazione(
    coda_ingresso: asyncio.Queue,
    coda_uscita: asyncio.Queue,
) -> None:
    """Fase 2: trasforma i dati."""
    while True:
        dato = await coda_ingresso.get()
        if dato is None:
            await coda_uscita.put(None)
            break
        risultato = {
            "valore": dato["grezzo"].upper(),
            "lunghezza": len(dato["grezzo"]),
            "fase": "trasformato",
        }
        print(f"[Trasformazione] {dato['grezzo']} -> {risultato['valore']}")
        await coda_uscita.put(risultato)

async def fase_caricamento(coda_ingresso: asyncio.Queue) -> list[dict]:
    """Fase 3: carica i dati trasformati."""
    risultati: list[dict] = []
    while True:
        dato = await coda_ingresso.get()
        if dato is None:
            break
        dato["fase"] = "caricato"
        risultati.append(dato)
        print(f"[Caricamento] {dato['valore']}")
    return risultati

async def esegui_pipeline(dati: list[str]) -> list[dict]:
    """Orchestratore della pipeline a tre fasi."""
    coda_1: asyncio.Queue = asyncio.Queue(maxsize=5)
    coda_2: asyncio.Queue = asyncio.Queue(maxsize=5)

    # Le fasi operano in parallelo, connesse dalle code
    _, _, risultati = await asyncio.gather(
        fase_estrazione(coda_1, dati),
        fase_trasformazione(coda_1, coda_2),
        fase_caricamento(coda_2),
    )
    return risultati

# risultati = asyncio.run(esegui_pipeline(["alfa", "beta", "gamma"]))
```

### Fan-Out / Fan-In

Il pattern **Fan-Out / Fan-In** distribuisce un singolo lavoro a molteplici worker paralleli (fan-out) e poi raccoglie e aggrega i risultati (fan-in). È ideale per operazioni I/O-bound come chiamate API, query a database o download paralleli.

```python
import asyncio
from typing import Callable, Awaitable

async def fan_out_fan_in(
    compiti: list[dict],
    worker_fn: Callable[[dict], Awaitable[dict]],
    max_concorrenza: int = 5,
) -> list[dict]:
    """Distribuisce compiti a worker paralleli con limite di concorrenza."""
    semaforo = asyncio.Semaphore(max_concorrenza)
    risultati: list[dict] = []

    async def worker_controllato(compito: dict) -> dict:
        async with semaforo:
            return await worker_fn(compito)

    # Fan-out: lancia tutti i task in parallelo (limitati dal semaforo)
    task_asincroni = [
        asyncio.create_task(worker_controllato(c)) for c in compiti
    ]

    # Fan-in: raccoglie i risultati mantenendo l'ordine
    risultati = await asyncio.gather(*task_asincroni)
    return list(risultati)

async def scarica_pagina(compito: dict) -> dict:
    """Worker simulato — scarica una pagina web."""
    url = compito["url"]
    await asyncio.sleep(0.3)  # Simula latenza di rete
    return {
        "url": url,
        "status": 200,
        "dimensione": len(url) * 100,
    }

async def main_fan_out():
    pagine = [{"url": f"https://api.esempio.com/pagina/{i}"} for i in range(20)]

    risultati = await fan_out_fan_in(
        compiti=pagine,
        worker_fn=scarica_pagina,
        max_concorrenza=5,  # Max 5 download simultanei
    )

    completati = sum(1 for r in risultati if r["status"] == 200)
    print(f"Scaricate {completati}/{len(pagine)} pagine")

# asyncio.run(main_fan_out())
```

Il `Semaphore` è fondamentale nel fan-out per evitare di sovraccaricare risorse esterne (API con rate limit, database con limite di connessioni). Senza il semaforo, tutti i task verrebbero lanciati simultaneamente, rischiando timeout, throttling o esaurimento delle risorse.

### Worker Pool con Graceful Shutdown

Un pattern avanzato combina producer-consumer con gestione del ciclo di vita dei worker, incluso lo shutdown controllato:

```python
import asyncio
import signal

class WorkerPool:
    """Pool di worker asincroni con shutdown controllato."""

    def __init__(self, n_worker: int, coda: asyncio.Queue):
        self._n_worker = n_worker
        self._coda = coda
        self._worker_tasks: list[asyncio.Task] = []
        self._attivo = True

    async def _worker(self, worker_id: int) -> None:
        """Worker loop con gestione degli errori."""
        while self._attivo:
            try:
                compito = await asyncio.wait_for(
                    self._coda.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            if compito is None:
                break

            try:
                print(f"[Worker-{worker_id}] Elabora: {compito}")
                await asyncio.sleep(0.2)  # Lavoro simulato
            except Exception as e:
                print(f"[Worker-{worker_id}] Errore: {e}")
            finally:
                self._coda.task_done()

    async def avvia(self) -> None:
        """Avvia tutti i worker."""
        self._worker_tasks = [
            asyncio.create_task(self._worker(i))
            for i in range(self._n_worker)
        ]

    async def ferma(self) -> None:
        """Shutdown controllato: completa i compiti in coda, poi termina."""
        self._attivo = False
        # Segnala a ogni worker di terminare
        for _ in self._worker_tasks:
            await self._coda.put(None)
        await asyncio.gather(*self._worker_tasks)
        print("Pool terminato")
```

### Scelta del Modello di Concorrenza

La scelta tra i diversi modelli di concorrenza di Python dipende dalla natura del workload:

| Modello | Caso d'uso ideale | Limitazioni |
|---|---|---|
| **`asyncio`** | I/O-bound: HTTP, database, file, socket | Non accelera codice CPU-bound; richiede librerie async-compatibili |
| **`threading`** | I/O-bound con librerie bloccanti (non async) | GIL limita il parallelismo CPU; race condition possibili |
| **`multiprocessing`** | CPU-bound: calcolo scientifico, compressione, ML | Overhead di serializzazione (pickle); memoria non condivisa |
| **`concurrent.futures`** | API unificata per thread pool e process pool | Meno controllo fine rispetto ad asyncio |

**Pattern thread-safe con `threading`:**

```python
import threading
from queue import Queue

class ContatoreSicuro:
    """Contatore thread-safe con lock."""

    def __init__(self):
        self._valore = 0
        self._lock = threading.Lock()

    def incrementa(self, n: int = 1) -> int:
        with self._lock:
            self._valore += n
            return self._valore

    @property
    def valore(self) -> int:
        with self._lock:
            return self._valore
```

Per I/O-bound con librerie legacy non async, `concurrent.futures.ThreadPoolExecutor` offre un'API ad alto livello che si integra bene con `asyncio.to_thread()` (Python 3.9+) per bridge tra codice sincrono e asincrono:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def operazione_bloccante(dato: str) -> str:
    """Funzione sincrona bloccante — non compatibile con asyncio."""
    import time
    time.sleep(0.5)
    return dato.upper()

async def main_bridge():
    """Esegue codice bloccante in un thread pool senza bloccare il loop."""
    risultati = await asyncio.gather(
        asyncio.to_thread(operazione_bloccante, "alfa"),
        asyncio.to_thread(operazione_bloccante, "beta"),
        asyncio.to_thread(operazione_bloccante, "gamma"),
    )
    print(risultati)  # ['ALFA', 'BETA', 'GAMMA']

# asyncio.run(main_bridge())
```

Questi pattern di concorrenza si combinano tra loro: un sistema reale potrebbe usare un producer-consumer per ingerire dati, una pipeline per trasformarli e un fan-out/fan-in per caricarli in parallelo su molteplici destinazioni. La chiave è mantenere ogni componente semplice e indipendente, connesso dagli altri tramite code e protocolli ben definiti.

---

## Best Practices

1. **Preferire la semplicita** — Il principio KISS (Keep It Simple, Stupid) e fondamentale. Scegliere sempre la soluzione piu semplice che risolve il problema. In Python, un modulo e spesso sufficiente dove in Java servirebbe un Singleton complesso. Una funzione semplice e spesso preferibile a una classe con un solo metodo.

2. **Composizione rispetto all'ereditarieta** — Favorire la composizione degli oggetti rispetto all'ereditarieta delle classi. La composizione offre maggiore flessibilita, accoppiamento minore e codice piu facile da testare. L'ereditarieta crea dipendenze rigide e fragili; la composizione permette di cambiare comportamento a runtime.

3. **Rispettare i principi SOLID** — I cinque principi SOLID guidano verso una progettazione robusta: **S**ingle Responsibility (ogni classe ha una sola responsabilita), **O**pen/Closed (aperto all'estensione, chiuso alla modifica), **L**iskov Substitution (le sottoclassi devono essere sostituibili alle classi base), **I**nterface Segregation (interfacce piccole e specifiche), **D**ependency Inversion (dipendere da astrazioni, non da implementazioni concrete).

4. **Pensare in modo Pythonico** — Non tradurre ciecamente i pattern da Java o C++. In Python, le funzioni di prima classe, i generatori, i decorator, i context manager e il duck typing rendono molti pattern classici superflui o drasticamente piu semplici. Chiedersi sempre: "Esiste un modo piu Pythonico per ottenere questo risultato?"

5. **Applicare i pattern solo quando necessario** — Un pattern risolve un problema specifico. Se il problema non esiste, il pattern aggiunge solo complessita. Non introdurre mai un'Abstract Factory per gestire due varianti che non cambieranno mai. I pattern emergono dalla necessita, non vengono imposti a priori.

6. **Privilegiare la leggibilita del codice** — Un design pattern ben implementato rende il codice piu chiaro, non piu oscuro. Se l'applicazione di un pattern rende il codice piu difficile da comprendere per il team, probabilmente non e il pattern giusto o non e applicato nel contesto giusto. Codice leggibile e codice manutenibile.

7. **Testare ogni pattern implementato** — Ogni pattern introdotto deve essere accompagnato da test. Il Singleton deve essere testato per verificare l'unicita dell'istanza, il Factory Method per verificare che crei il tipo corretto, l'Observer per verificare la corretta notifica. I test documentano l'intento del pattern e prevengono regressioni.

8. **Documentare l'intento, non l'implementazione** — Quando si utilizza un design pattern, documentare *perche* e stato scelto e *quale problema* risolve. L'implementazione si legge nel codice; l'intento si perde senza documentazione. Un commento come "Usiamo Strategy per permettere il cambio di algoritmo di pricing a runtime" e molto piu utile di "Questa classe implementa lo Strategy pattern".

9. **Favorire l'immutabilita quando possibile** — Gli oggetti immutabili sono piu facili da ragionare, testare e condividere tra thread. In Python, usare `@dataclass(frozen=True)`, `NamedTuple` e tuple anziché liste quando i dati non devono cambiare. L'immutabilita semplifica molti pattern, in particolare State e Prototype.

10. **Evolvere l'architettura incrementalmente** — Non progettare l'architettura perfetta al primo tentativo. Partire con una soluzione semplice e refactorizzare verso pattern piu sofisticati solo quando la complessita effettiva del sistema lo richiede. Il codice migliore e quello che risolve i problemi di oggi senza ipotecare le soluzioni di domani.

---

## Esercizi

1. **Factory Method per parser di file** — Implementa un sistema che legga file in formati diversi (CSV, JSON, YAML, TOML) utilizzando il Factory Method. Crea una classe base `FileParser` con metodo astratto `parse()`, implementa un parser concreto per ogni formato e una factory function `create_parser(filepath)` che restituisca il parser appropriato in base all'estensione. Scrivi test per almeno 3 formati.

2. **Observer pattern per sistema di notifiche** — Progetta un sistema di notifiche con il pattern Observer. Un `EventBus` gestisce la registrazione di listener e l'emissione di eventi tipizzati. Implementa almeno tre observer concreti (console logger, file logger, email notifier stub). Usa type hints, `Protocol` per l'interfaccia observer e `dataclass` per gli eventi. Verifica con test che tutti gli observer vengano notificati e che la rimozione di un observer funzioni correttamente.

3. **Decorator pattern vs Python decorator** — Implementa lo stesso comportamento (logging + timing + retry) in due modi: (a) con il Decorator pattern classico GoF (classi wrapper), (b) con decorator Python (`@functools.wraps`). Confronta leggibilita, testabilita e flessibilita di composizione. Documenta in un commento quale approccio preferiresti in un progetto reale e perche.

4. **Strategy con funzioni first-class** — Implementa un sistema di pricing con 4 strategie di sconto (percentuale, importo fisso, buy-one-get-one, sconto progressivo per volume). Implementalo in due versioni: (a) con classi Strategy classiche e (b) con semplici funzioni passate come argomento. Misura la complessita ciclomatica di entrambe le versioni con `radon`.

5. **Refactoring da anti-pattern a pattern** — Prendi un modulo con almeno 3 anti-pattern evidenti (God Class, Spaghetti Code, Premature Optimization) e refactorizzalo applicando i pattern appropriati. Documenta ogni anti-pattern individuato, il pattern applicato e il risultato. Mantieni la backward compatibility dell'API pubblica e verifica con test prima e dopo il refactoring.

---

## Letture e Riferimenti

### Fonti primarie

- Gamma, Helm, Johnson, Vlissides — *Design Patterns: Elements of Reusable Object-Oriented Software* — Addison-Wesley, 1994
- Luciano Ramalho — *Fluent Python, 2nd Edition* — O'Reilly, 2022 — Capitoli 9-11 (pattern Pythonici)
- Brandon Rhodes — *Python Design Patterns* — https://python-patterns.guide/ (consultato: 2026-05-24)
- Python Documentation — *`abc` module* — https://docs.python.org/3/library/abc.html (consultato: 2026-05-24)
- Python Documentation — *Descriptor HowTo Guide* — https://docs.python.org/3/howto/descriptor.html (consultato: 2026-05-24)
- Python Documentation — *`functools` module* — https://docs.python.org/3/library/functools.html (consultato: 2026-05-24)
- Refactoring Guru — *Design Patterns in Python* — https://refactoring.guru/design-patterns/python (consultato: 2026-05-24)

### Libri consigliati

- *Head First Design Patterns, 2nd Edition* — Eric Freeman, Elisabeth Robson — O'Reilly, 2020
- *Architecture Patterns with Python* — Harry Percival, Bob Gregory — O'Reilly, 2020

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [07 — OOP](07-oop.md) | Classi, ereditarieta, polimorfismo — fondamenta per i pattern GoF |
| [03 — Funzioni e Scope](03-funzioni-scope.md) | Funzioni first-class, closure — alternative Pythoniche ai pattern classici |
| [22 — Clean Code](22-clean-code.md) | Principi SOLID, refactoring, naming — qualita del codice nei pattern |
| [06 — Moduli e Pacchetti](06-moduli-pacchetti.md) | Organizzazione del codice in moduli — Singleton come modulo Python |
| [23 — Testing](23-testing.md) | Test dei pattern: mock, dependency injection, testabilita |
| [08 — Concorrenza](08-concorrenza.md) | Pattern thread-safe: Singleton con lock, Producer-Consumer |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Design Pattern** | Soluzione ricorrente e consolidata a un problema comune nella progettazione software, descritta in forma riutilizzabile |
| **GoF (Gang of Four)** | I quattro autori (Gamma, Helm, Johnson, Vlissides) del libro fondativo sui design patterns del 1994 |
| **Pattern Creazionale** | Categoria di pattern che gestisce i meccanismi di creazione degli oggetti (Singleton, Factory, Builder, Prototype) |
| **Pattern Strutturale** | Categoria di pattern che compone classi e oggetti in strutture piu ampie (Adapter, Decorator, Facade, Proxy, Composite) |
| **Pattern Comportamentale** | Categoria di pattern che gestisce comunicazione e interazione tra oggetti (Observer, Strategy, Command, Iterator, State) |
| **Singleton** | Pattern che garantisce l'esistenza di una sola istanza di una classe; in Python, un modulo e gia un singleton naturale |
| **Factory Method** | Pattern che delega la creazione di oggetti a sottoclassi o funzioni, disaccoppiando il codice dal tipo concreto |
| **Observer** | Pattern in cui un oggetto (subject) notifica automaticamente i suoi dipendenti (observer) quando cambia stato |
| **Strategy** | Pattern che incapsula algoritmi intercambiabili; in Python, spesso implementato con funzioni first-class |
| **Decorator (GoF)** | Pattern strutturale che aggiunge responsabilita a un oggetto dinamicamente tramite wrapping — distinto dal decorator Python (`@`) |
| **Duck Typing** | Filosofia Python per cui il tipo di un oggetto e determinato dal suo comportamento (metodi/attributi), non dalla sua classe |
| **Mixin** | Classe che fornisce metodi a sottoclassi tramite ereditarieta multipla senza essere progettata per l'istanziazione diretta |
| **Protocol** | Classe astratta strutturale (`typing.Protocol`) che definisce un'interfaccia senza richiedere ereditarieta esplicita |
| **Anti-pattern** | Soluzione ricorrente che appare intuitiva ma produce risultati negativi (God Class, Spaghetti Code, Premature Optimization) |
| **Code Smell** | Indicatore di debolezza progettuale nel codice — non un bug, ma un segnale che suggerisce refactoring (Feature Envy, Data Clumps, Shotgun Surgery) |
| **SOLID** | Cinque principi di progettazione OOP: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| **Dependency Injection** | Pattern in cui un oggetto riceve le proprie dipendenze dall'esterno (iniettate) anziché crearle internamente, migliorando testabilità e modularità |
| **Composition Root** | Punto unico dell'applicazione dove tutte le dipendenze vengono assemblate e collegate tra loro |
| **Object Pool** | Pattern creazionale che gestisce un insieme di oggetti pre-inizializzati riutilizzabili, evitando il costo ripetuto di creazione e distruzione |
| **Bridge** | Pattern strutturale che separa un'astrazione dalla sua implementazione, permettendo a entrambe di variare indipendentemente |
| **Flyweight** | Pattern strutturale che condivide stato intrinseco tra oggetti simili per ridurre il consumo di memoria |
| **Mediator** | Pattern comportamentale che centralizza la comunicazione tra componenti, riducendo le dipendenze dirette tra di essi |
| **Memento** | Pattern comportamentale che cattura e ripristina lo stato interno di un oggetto senza violare l'incapsulamento |
| **Visitor** | Pattern comportamentale che permette di definire nuove operazioni su una struttura di oggetti senza modificarne le classi |
| **Context Manager** | Protocollo Python (`__enter__`/`__exit__`) che gestisce risorse con semantica di setup/teardown automatico |
| **`__init_subclass__`** | Hook Python (PEP 487) invocato sulla classe genitore alla definizione di ogni nuova sottoclasse — alternativa leggera alle metaclass |
| **Currying** | Trasformazione di una funzione con N argomenti in una catena di N funzioni ciascuna con un singolo argomento |
| **Pipe** | Pattern funzionale che applica una sequenza di trasformazioni a un valore, dove l'output di ogni funzione diventa l'input della successiva |
| **Monad (Result)** | Struttura che incapsula un valore con contesto (successo/fallimento) e permette la concatenazione di operazioni con propagazione automatica degli errori |
| **Producer-Consumer** | Pattern di concorrenza che disaccoppia la produzione di dati dal loro consumo tramite una coda intermedia |
| **Fan-Out / Fan-In** | Pattern che distribuisce lavoro a molteplici worker paralleli (fan-out) e aggrega i risultati (fan-in) |
| **Pipeline (concorrenza)** | Pattern che organizza l'elaborazione asincrona in fasi sequenziali connesse da code, con ogni fase operante in parallelo |