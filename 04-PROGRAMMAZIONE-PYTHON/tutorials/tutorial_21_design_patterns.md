# Tutorial 21 — Design Patterns in Python: GoF e Pattern Moderni

> **Companion a:** `21-design-patterns.md`
> **Scope:** Creazionali, strutturali, comportamentali, pattern Python-specific
> **Prerequisiti:** `tutorial_02_oop.md`, `tutorial_04_decoratori_generatori_context_manager.md`
> **Durata stimata:** 16-20 ore

---

## Mappa concettuale

```
Design Patterns in Python
│
├── Creazionali — come creare oggetti
│   ├── Singleton — una sola istanza
│   ├── Factory Method — delega la creazione
│   ├── Abstract Factory — famiglie di oggetti
│   └── Builder — costruzione passo-passo
│
├── Strutturali — come comporre oggetti
│   ├── Adapter — interfaccia compatibile
│   ├── Decorator — aggiunge responsabilità
│   ├── Facade — interfaccia semplificata
│   ├── Proxy — surrogato controllato
│   └── Composite — struttura ad albero
│
├── Comportamentali — come comunicano
│   ├── Observer — pubblica/iscriviti
│   ├── Strategy — algoritmi intercambiabili
│   ├── Command — incapsula azioni
│   ├── State — comportamento per stato
│   ├── Template Method — scheletro algoritmo
│   └── Chain of Responsibility — catena handler
│
└── Pattern Python-specific
    ├── Protocol — duck typing strutturale
    ├── Context Manager — resource management
    ├── Descriptor — attributi personalizzati
    └── Registry — autoregistrazione classi
```

---

# Parte A — Creazionali

---

## A1. Singleton

```python
from threading import Lock

class SingletonMeta(type):
    """Metaclasse thread-safe per Singleton."""
    _istanze: dict = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._istanze:
                cls._istanze[cls] = super().__call__(*args, **kwargs)
        return cls._istanze[cls]

class ConfigurazioneGlobale(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._dati: dict = {}

    def imposta(self, chiave: str, valore: object) -> None:
        self._dati[chiave] = valore

    def ottieni(self, chiave: str, default: object = None) -> object:
        return self._dati.get(chiave, default)

# Sempre la stessa istanza
cfg1 = ConfigurazioneGlobale()
cfg2 = ConfigurazioneGlobale()
assert cfg1 is cfg2   # True

# Alternativa Python moderna: module-level singleton
# Il modulo è caricato una volta — oggetto module-level = singleton naturale
```

---

## A2. Factory Method e Abstract Factory

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ProdottoBase:
    nome: str
    prezzo: float

class CreatoreProdotto(ABC):
    @abstractmethod
    def crea(self, nome: str) -> ProdottoBase: ...

    def ordina(self, nome: str) -> str:
        prodotto = self.crea(nome)
        return f"Ordine: {prodotto.nome} a €{prodotto.prezzo}"

class CreatoreDigitale(CreatoreProdotto):
    def crea(self, nome: str) -> ProdottoBase:
        return ProdottoBase(nome=f"[Digital] {nome}", prezzo=9.99)

class CreatoreFisico(CreatoreProdotto):
    def crea(self, nome: str) -> ProdottoBase:
        return ProdottoBase(nome=f"[Fisico] {nome}", prezzo=29.99)

# Abstract Factory — famiglie di oggetti correlati
class InterfacciaUI(ABC):
    @abstractmethod
    def crea_bottone(self) -> str: ...
    @abstractmethod
    def crea_checkbox(self) -> str: ...

class UIWindows(InterfacciaUI):
    def crea_bottone(self) -> str: return "Windows Button"
    def crea_checkbox(self) -> str: return "Windows Checkbox"

class UIMac(InterfacciaUI):
    def crea_bottone(self) -> str: return "Mac Button"
    def crea_checkbox(self) -> str: return "Mac Checkbox"

def crea_ui_per_os(sistema: str) -> InterfacciaUI:
    factory_map = {"windows": UIWindows, "mac": UIMac}
    cls = factory_map.get(sistema.lower())
    if cls is None:
        raise ValueError(f"Sistema non supportato: {sistema}")
    return cls()
```

---

## A3. Builder

```python
from dataclasses import dataclass, field

@dataclass
class ConnessioneDB:
    host: str
    porta: int
    database: str
    utente: str
    password: str
    pool_size: int = 5
    timeout: float = 30.0
    ssl: bool = False

class ConnessioneDBBuilder:
    def __init__(self) -> None:
        self._host = "localhost"
        self._porta = 5432
        self._database = ""
        self._utente = ""
        self._password = ""
        self._pool_size = 5
        self._timeout = 30.0
        self._ssl = False

    def host(self, host: str) -> "ConnessioneDBBuilder":
        self._host = host; return self

    def porta(self, porta: int) -> "ConnessioneDBBuilder":
        self._porta = porta; return self

    def database(self, nome: str) -> "ConnessioneDBBuilder":
        self._database = nome; return self

    def credenziali(self, utente: str, password: str) -> "ConnessioneDBBuilder":
        self._utente = utente; self._password = password; return self

    def pool(self, size: int) -> "ConnessioneDBBuilder":
        self._pool_size = size; return self

    def con_ssl(self) -> "ConnessioneDBBuilder":
        self._ssl = True; return self

    def costruisci(self) -> ConnessioneDB:
        if not self._database:
            raise ValueError("Nome database obbligatorio")
        return ConnessioneDB(
            host=self._host, porta=self._porta, database=self._database,
            utente=self._utente, password=self._password,
            pool_size=self._pool_size, timeout=self._timeout, ssl=self._ssl,
        )

# Uso fluente
conn = (
    ConnessioneDBBuilder()
    .host("db.produzione.com")
    .porta(5432)
    .database("miodb")
    .credenziali("admin", "secret")
    .pool(20)
    .con_ssl()
    .costruisci()
)
```

---

# Parte B — Strutturali

---

## B1. Adapter e Facade

```python
# Adapter — rende compatibile un'interfaccia esistente
class ClienteHTTPLegacy:
    """Libreria legacy con interfaccia diversa."""
    def get_request(self, endpoint: str, api_key: str) -> dict:
        return {"status": "ok", "data": f"da {endpoint}"}

class ClienteHTTPModerno:
    """Interfaccia attesa dal codice nuovo."""
    def get(self, url: str, headers: dict | None = None) -> dict: ...

class AdapterHTTP(ClienteHTTPModerno):
    def __init__(self, legacy: ClienteHTTPLegacy, api_key: str) -> None:
        self._legacy = legacy
        self._api_key = api_key

    def get(self, url: str, headers: dict | None = None) -> dict:
        endpoint = url.split("/")[-1]
        return self._legacy.get_request(endpoint, self._api_key)

# Facade — interfaccia semplificata per un sottosistema complesso
class SistemaPagamento:
    def verifica_frode(self, carta: str) -> bool: return True
    def verifica_saldo(self, carta: str, importo: float) -> bool: return True
    def addebita(self, carta: str, importo: float) -> str: return "TXN123"
    def invia_ricevuta(self, email: str, txn: str) -> None: pass
    def aggiorna_registro(self, txn: str) -> None: pass

class FacadePagamento:
    """Nasconde la complessità del sistema di pagamento."""
    def __init__(self) -> None:
        self._sistema = SistemaPagamento()

    def processa_acquisto(self, carta: str, importo: float, email: str) -> str:
        if not self._sistema.verifica_frode(carta):
            raise ValueError("Frode rilevata")
        if not self._sistema.verifica_saldo(carta, importo):
            raise ValueError("Saldo insufficiente")
        txn = self._sistema.addebita(carta, importo)
        self._sistema.invia_ricevuta(email, txn)
        self._sistema.aggiorna_registro(txn)
        return txn
```

---

## B2. Decorator pattern (non @decorator)

```python
from abc import ABC, abstractmethod

class FileReader(ABC):
    @abstractmethod
    def leggi(self, percorso: str) -> str: ...

class FileReaderBase(FileReader):
    def leggi(self, percorso: str) -> str:
        with open(percorso, encoding="utf-8") as f:
            return f.read()

class FileReaderConCache(FileReader):
    """Decorator: aggiunge cache al reader."""
    def __init__(self, reader: FileReader) -> None:
        self._reader = reader
        self._cache: dict[str, str] = {}

    def leggi(self, percorso: str) -> str:
        if percorso not in self._cache:
            self._cache[percorso] = self._reader.leggi(percorso)
        return self._cache[percorso]

class FileReaderConLog(FileReader):
    """Decorator: aggiunge logging al reader."""
    def __init__(self, reader: FileReader) -> None:
        self._reader = reader

    def leggi(self, percorso: str) -> str:
        print(f"Lettura: {percorso}")
        risultato = self._reader.leggi(percorso)
        print(f"Letti {len(risultato)} caratteri")
        return risultato

# Composizione decoratori
reader = FileReaderConLog(FileReaderConCache(FileReaderBase()))
```

---

# Parte C — Comportamentali

---

## C1. Observer

```python
from collections.abc import Callable
from dataclasses import dataclass, field

@dataclass
class EventoOrdine:
    tipo: str   # "creato", "pagato", "spedito"
    ordine_id: int
    dati: dict = field(default_factory=dict)

ObserverFn = Callable[[EventoOrdine], None]

class EventBus:
    """Bus eventi semplice (pattern Observer)."""
    def __init__(self) -> None:
        self._abbonati: dict[str, list[ObserverFn]] = {}

    def iscriviti(self, tipo_evento: str, handler: ObserverFn) -> None:
        self._abbonati.setdefault(tipo_evento, []).append(handler)

    def disiscriviti(self, tipo_evento: str, handler: ObserverFn) -> None:
        handlers = self._abbonati.get(tipo_evento, [])
        if handler in handlers:
            handlers.remove(handler)

    def pubblica(self, evento: EventoOrdine) -> None:
        for handler in self._abbonati.get(evento.tipo, []):
            try:
                handler(evento)
            except Exception as e:
                print(f"Handler {handler.__name__} ha fallito: {e}")

bus = EventBus()

def invia_email_conferma(evento: EventoOrdine) -> None:
    print(f"Email: ordine {evento.ordine_id} creato")

def aggiorna_magazzino(evento: EventoOrdine) -> None:
    print(f"Magazzino: scala stock per ordine {evento.ordine_id}")

bus.iscriviti("creato", invia_email_conferma)
bus.iscriviti("creato", aggiorna_magazzino)
bus.pubblica(EventoOrdine("creato", 42, {"prodotto_id": 7}))
```

---

## C2. Strategy e Command

```python
from abc import ABC, abstractmethod
from typing import Protocol
import json

# Strategy — algoritmi intercambiabili
class StrategiaOrdinamento(Protocol):
    def ordina(self, dati: list) -> list: ...

def ordina_per_nome(dati: list) -> list:
    return sorted(dati, key=lambda x: x.get("nome", ""))

def ordina_per_prezzo(dati: list) -> list:
    return sorted(dati, key=lambda x: x.get("prezzo", 0))

def ordina_per_popolarita(dati: list) -> list:
    return sorted(dati, key=lambda x: x.get("vendite", 0), reverse=True)

class CatalogoProdotti:
    def __init__(self, strategia: StrategiaOrdinamento = ordina_per_nome) -> None:
        self._strategia = strategia
        self._prodotti: list[dict] = []

    def cambia_ordinamento(self, strategia: StrategiaOrdinamento) -> None:
        self._strategia = strategia

    def lista(self) -> list[dict]:
        return self._strategia(self._prodotti)

# Command — incapsula azioni come oggetti
class ComandoBase(ABC):
    @abstractmethod
    def esegui(self) -> None: ...
    @abstractmethod
    def annulla(self) -> None: ...

class ComandoAggiunta(ComandoBase):
    def __init__(self, lista: list, elemento: object) -> None:
        self._lista = lista
        self._elemento = elemento

    def esegui(self) -> None:
        self._lista.append(self._elemento)

    def annulla(self) -> None:
        if self._elemento in self._lista:
            self._lista.remove(self._elemento)

class StoricoComandi:
    def __init__(self) -> None:
        self._storico: list[ComandoBase] = []

    def esegui(self, comando: ComandoBase) -> None:
        comando.esegui()
        self._storico.append(comando)

    def annulla(self) -> None:
        if self._storico:
            self._storico.pop().annulla()
```

---

## C3. State Machine

```python
from enum import Enum, auto
from typing import Protocol

class StatoOrdine(Enum):
    BOZZA = auto()
    IN_ATTESA = auto()
    CONFERMATO = auto()
    IN_ELABORAZIONE = auto()
    SPEDITO = auto()
    CONSEGNATO = auto()
    ANNULLATO = auto()

class TransizioneNonPermessa(Exception):
    pass

TRANSIZIONI: dict[StatoOrdine, set[StatoOrdine]] = {
    StatoOrdine.BOZZA: {StatoOrdine.IN_ATTESA, StatoOrdine.ANNULLATO},
    StatoOrdine.IN_ATTESA: {StatoOrdine.CONFERMATO, StatoOrdine.ANNULLATO},
    StatoOrdine.CONFERMATO: {StatoOrdine.IN_ELABORAZIONE, StatoOrdine.ANNULLATO},
    StatoOrdine.IN_ELABORAZIONE: {StatoOrdine.SPEDITO},
    StatoOrdine.SPEDITO: {StatoOrdine.CONSEGNATO},
    StatoOrdine.CONSEGNATO: set(),
    StatoOrdine.ANNULLATO: set(),
}

class Ordine:
    def __init__(self, id: int) -> None:
        self.id = id
        self._stato = StatoOrdine.BOZZA
        self._storico: list[StatoOrdine] = [StatoOrdine.BOZZA]

    @property
    def stato(self) -> StatoOrdine:
        return self._stato

    def transita_a(self, nuovo_stato: StatoOrdine) -> None:
        if nuovo_stato not in TRANSIZIONI[self._stato]:
            raise TransizioneNonPermessa(
                f"Impossibile passare da {self._stato.name} a {nuovo_stato.name}"
            )
        self._stato = nuovo_stato
        self._storico.append(nuovo_stato)

    def conferma(self) -> None: self.transita_a(StatoOrdine.CONFERMATO)
    def elabora(self) -> None: self.transita_a(StatoOrdine.IN_ELABORAZIONE)
    def spedisci(self) -> None: self.transita_a(StatoOrdine.SPEDITO)
    def consegna(self) -> None: self.transita_a(StatoOrdine.CONSEGNATO)
    def annulla(self) -> None: self.transita_a(StatoOrdine.ANNULLATO)
```

---

# Parte D — Registry pattern

---

## D1. Plugin Registry con metaclassi

```python
from abc import ABC, abstractmethod

class ProcessoreBase(ABC):
    _registro: dict[str, type] = {}

    def __init_subclass__(cls, nome: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if nome:
            ProcessoreBase._registro[nome] = cls

    @abstractmethod
    def processa(self, dati: dict) -> dict: ...

    @classmethod
    def crea(cls, nome: str) -> "ProcessoreBase":
        try:
            return cls._registro[nome]()
        except KeyError:
            raise ValueError(f"Processore '{nome}' non trovato. Disponibili: {list(cls._registro)}")

# Autoregistrazione tramite ereditarietà
class ProcessoreJSON(ProcessoreBase, nome="json"):
    def processa(self, dati: dict) -> dict:
        import json
        return {"tipo": "json", "payload": json.dumps(dati)}

class ProcessoreXML(ProcessoreBase, nome="xml"):
    def processa(self, dati: dict) -> dict:
        xml = "".join(f"<{k}>{v}</{k}>" for k, v in dati.items())
        return {"tipo": "xml", "payload": f"<root>{xml}</root>"}

# Uso
proc = ProcessoreBase.crea("json")
risultato = proc.processa({"chiave": "valore"})
```

---

# Parte E — Riepilogo

## Quale pattern per quale problema

| Problema | Pattern |
|---|---|
| Una sola istanza di configurazione | Singleton / Module-level |
| Creare oggetti senza hardcodare la classe | Factory Method |
| Costruire oggetti complessi step-by-step | Builder |
| Adattare API legacy | Adapter |
| Semplificare sottosistema complesso | Facade |
| Aggiungere funzionalità senza ereditarietà | Decorator |
| Reagire a eventi senza accoppiamento | Observer / EventBus |
| Algoritmi intercambiabili | Strategy / Protocol |
| Azioni con undo/redo | Command |
| Comportamento dipendente dallo stato | State Machine |
| Plugin autoregistrati | Registry + `__init_subclass__` |

## Prossimi passi

- `tutorial_22_clean_code.md` — come scrivere codice pulito e mantenibile
