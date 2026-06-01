---
corso: "Programmazione Python"
fase: "2 — Strumenti Essenziali"
modulo: "07"
titolo: "Error Handling e Logging"
versione: "Python 3.12+ / structlog 24.x / Sentry SDK 2.x"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01 — Fondamenti del Linguaggio"
  - "02 — OOP"
  - "04 — Decoratori, Generatori e Context Manager"
obiettivi:
  - "Progettare gerarchie di eccezioni personalizzate con contesto strutturato"
  - "Gestire ExceptionGroup e except* in codice asincrono con TaskGroup"
  - "Configurare logging strutturato JSON con structlog e processori"
  - "Implementare correlation ID con contextvars e propagarli ad async task"
  - "Collegare structlog a OpenTelemetry LoggerProvider per correlazione trace-log"
  - "Applicare pattern di retry, circuit breaker e graceful degradation"
  - "Integrare Sentry con contesto strutturato e breadcrumbs"
tag: [error-handling, logging, eccezioni, structlog, sentry, ExceptionGroup, retry, circuit-breaker]
---

# Error Handling e Logging — Guida Completa

> **Modulo 07** · **Aggiornamento:** 2026-05-24 · **Versione:** Python 3.12+ / structlog 24.x / Sentry SDK 2.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Fondamenti](01-fondamenti-linguaggio.md), [OOP](02-oop.md), [Decoratori e Context Manager](04-decoratori-generatori-context-manager.md)
>
> Al termine di questo modulo saprai:
> 1. Progettare gerarchie di eccezioni personalizzate con contesto strutturato
> 2. Gestire `ExceptionGroup` e `except*` in codice asincrono con `TaskGroup`
> 3. Configurare pipeline di logging strutturato JSON con `structlog` e processori
> 4. Implementare correlation ID con `contextvars` e propagarli ad async task
> 5. Collegare structlog a OpenTelemetry `LoggerProvider` per correlazione trace-log
> 6. Applicare pattern di retry con budget, circuit breaker e graceful degradation
> 7. Integrare Sentry con contesto strutturato e breadcrumbs per error reporting
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato
> **Ultimo aggiornamento:** 2026-05-23
> **Versioni di riferimento:** Python 3.12+ · structlog 24.4+ · opentelemetry-sdk 1.27+ · tenacity 9.0+ · sentry-sdk 2.x

## Mappa concettuale

```
                        ┌──────────────────────────────────────────────────────┐
                        │               EXCEPTION HIERARCHY                    │
                        │                                                      │
                        │   BaseException                                      │
                        │   ├── KeyboardInterrupt                              │
                        │   ├── SystemExit                                     │
                        │   ├── GeneratorExit                                  │
                        │   ├── BaseExceptionGroup (3.11+)                     │
                        │   └── Exception  ← catturare qui, mai sopra         │
                        │       ├── ValueError, TypeError, KeyError ...        │
                        │       ├── OSError (FileNotFoundError, PermissionE.)  │
                        │       ├── ExceptionGroup (3.11+)                     │
                        │       ├── CustomException (dominio applicativo)      │
                        │       └── Warning                                    │
                        └──────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                        LOGGING FLOW                                      │
    │                                                                          │
    │   Codice App                                                             │
    │     │                                                                    │
    │     ▼                                                                    │
    │   structlog.get_logger()  ───bind()───→  Bound Logger                   │
    │     │                                      │                             │
    │     ▼                                      ▼                             │
    │   Processor Chain                    contextvars.merge                    │
    │   ┌────────────────┐                 (correlation_id,                     │
    │   │ merge_contextvars │               request_id, ...)                   │
    │   │ add_log_level    │                                                   │
    │   │ add_timestamp    │                                                   │
    │   │ StackInfoRenderer│                                                   │
    │   │ JSONRenderer     │──→ stdout/file (JSON)                            │
    │   └────────────────┘                                                     │
    │         │                                                                │
    │         ▼ (via ProcessorFormatter)                                       │
    │   stdlib logging                                                         │
    │     │                                                                    │
    │     ▼                                                                    │
    │   OTel LoggingHandler ──→ LoggerProvider ──→ OTLP Exporter              │
    │         │                                        │                       │
    │         └── trace_id + span_id injection ────────┘                       │
    │                                                                          │
    └──────────────────────────────────────────────────────────────────────────┘
```

## Idee guida
1. **Mai `except:` bare; sempre `except SpecificError:`.**
2. **structlog > stdlib logging per JSON.** OTel logs integration.
3. **`contextvars` per correlation ID propagation async.**
4. **OTel logs spec: link a trace_id automatic.**


## Indice

1. [Panoramica](#panoramica)
2. [Eccezioni in Python](#eccezioni-in-python)
   - [Gerarchia delle Eccezioni](#gerarchia-delle-eccezioni)
   - [try/except/else/finally](#tryexceptelsefinally)
   - [Raising Exceptions](#raising-exceptions)
   - [Eccezioni Personalizzate](#eccezioni-personalizzate)
   - [Gerarchie di Eccezioni per Domain-Driven Design](#gerarchie-di-eccezioni-per-domain-driven-design)
   - [Exception Groups (Python 3.11+)](#exception-groups-python-311)
3. [EAFP vs LBYL](#eafp-vs-lbyl)
4. [Context Manager per Error Handling](#context-manager-per-error-handling)
5. [Logging](#logging)
   - [Modulo logging](#modulo-logging)
   - [Configurazione Logger](#configurazione-logger)
   - [Configurazione Avanzata](#configurazione-avanzata)
   - [Logging Strutturato](#logging-strutturato)
   - [Logging in Produzione](#logging-in-produzione)
6. [structlog — Logging Strutturato Avanzato](#structlog--logging-strutturato-avanzato)
   - [Architettura e concetti fondamentali](#architettura-e-concetti-fondamentali)
   - [Configurazione globale](#configurazione-globale)
   - [Processori built-in e custom](#processori-built-in-e-custom)
   - [Bound Logger e contesto](#bound-logger-e-contesto)
   - [Rendering JSON e console](#rendering-json-e-console)
   - [Integrazione con stdlib logging](#integrazione-con-stdlib-logging)
   - [Filtraggio e sampling](#filtraggio-e-sampling)
   - [Logging Asincrono — QueueHandler e QueueListener](#logging-asincrono--queuehandler-e-queuelistener)
7. [Correlation ID con contextvars e structlog](#correlation-id-con-contextvars-e-structlog)
   - [Pattern contextvars nativo](#pattern-contextvars-nativo)
   - [Middleware ASGI/WSGI](#middleware-asgiwsgi)
   - [Propagazione ad asyncio task figli](#propagazione-ad-asyncio-task-figli)
8. [OTel Log Bridge — Correlazione Trace-Log](#otel-log-bridge--correlazione-trace-log)
   - [Architettura del bridge](#architettura-del-bridge)
   - [Setup LoggerProvider e OTLP exporter](#setup-loggerprovider-e-otlp-exporter)
   - [Integrazione structlog → stdlib → OTel](#integrazione-structlog--stdlib--otel)
   - [Correlazione trace_id e span_id](#correlazione-trace_id-e-span_id)
9. [Error Handling in FastAPI e Django](#error-handling-in-fastapi-e-django)
   - [FastAPI — Exception Handler e Middleware](#fastapi--exception-handler-e-middleware)
   - [Django — Middleware e DRF Exception Handler](#django--middleware-e-drf-exception-handler)
10. [Pattern Avanzati](#pattern-avanzati)
   - [Retry Pattern](#retry-pattern)
   - [Retry Budget](#retry-budget)
   - [Graceful Degradation](#graceful-degradation)
   - [Error Reporting](#error-reporting)
11. [Warnings](#warnings)
12. [Debugging](#debugging)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)
15. [Esercizi](#esercizi)
16. [Auto-valutazione](#auto-valutazione)
17. [Letture primarie consigliate](#letture-primarie-consigliate)
18. [Collegamenti incrociati](#collegamenti-incrociati)
19. [Glossario locale](#glossario-locale)

---

## Panoramica

La gestione degli errori e il logging sono due pilastri fondamentali di qualsiasi applicazione Python robusta e mantenibile. Un programma che non gestisce correttamente le situazioni anomale risulta fragile, difficile da diagnosticare e potenzialmente pericoloso in ambienti di produzione. Allo stesso modo, un sistema privo di logging adeguato trasforma ogni problema in un mistero irrisolvibile.

Python offre un meccanismo di gestione delle eccezioni estremamente potente e flessibile, basato sul paradigma `try/except`. A differenza di linguaggi come C che utilizzano codici di ritorno, o Go che restituisce tuple `(valore, errore)`, Python adotta un modello in cui le condizioni anomale vengono segnalate attraverso il lancio di oggetti eccezione che risalgono lo stack di chiamate fino a trovare un gestore appropriato.

Il modulo `logging` della libreria standard, invece, fornisce un framework completo per registrare eventi a diversi livelli di gravita, instradare i messaggi verso destinazioni multiple e formattarli in modo strutturato. Padroneggiare entrambi questi strumenti e la loro interazione e essenziale per scrivere codice Python professionale.

In questa guida esploreremo in profondita la gerarchia delle eccezioni, i pattern di gestione errori, il sistema di logging dalla configurazione base a quella avanzata, i pattern di retry e degradazione, il modulo warnings e le tecniche di debugging.

> **Approfondimento:** A partire da Python 3.12 la PEP 678 (`ExceptionGroup` notes via `add_note()`) e la PEP 654 (Exception Groups) sono stabilizzate. Python 3.13 introduce ulteriori miglioramenti nei traceback con suggerimenti di correzione. Tutti gli esempi in questo modulo sono testati su Python 3.12+.

---

## Eccezioni in Python

### Gerarchia delle Eccezioni

Tutte le eccezioni in Python derivano dalla classe `BaseException`. La gerarchia e strutturata in modo da permettere la cattura selettiva degli errori a diversi livelli di granularita.

```
BaseException
├── BaseExceptionGroup
├── GeneratorExit
├── KeyboardInterrupt
├── SystemExit
└── Exception
    ├── ArithmeticError
    │   ├── FloatingPointError
    │   ├── OverflowError
    │   └── ZeroDivisionError
    ├── AssertionError
    ├── AttributeError
    ├── BufferError
    ├── EOFError
    ├── ImportError
    │   └── ModuleNotFoundError
    ├── LookupError
    │   ├── IndexError
    │   └── KeyError
    ├── MemoryError
    ├── NameError
    │   └── UnboundLocalError
    ├── OSError
    │   ├── ConnectionError
    │   │   ├── BrokenPipeError
    │   │   ├── ConnectionAbortedError
    │   │   ├── ConnectionRefusedError
    │   │   └── ConnectionResetError
    │   ├── FileExistsError
    │   ├── FileNotFoundError
    │   ├── IsADirectoryError
    │   ├── NotADirectoryError
    │   ├── PermissionError
    │   └── TimeoutError
    ├── ReferenceError
    ├── RuntimeError
    │   ├── NotImplementedError
    │   └── RecursionError
    ├── StopAsyncIteration
    ├── StopIteration
    ├── SyntaxError
    │   └── IndentationError
    ├── SystemError
    ├── TypeError
    ├── ValueError
    │   └── UnicodeError
    └── Warning
```

Le eccezioni al di fuori di `Exception` (`KeyboardInterrupt`, `SystemExit`, `GeneratorExit`) non vengono catturate da un generico `except Exception`. Questo e intenzionale: quando l'utente preme Ctrl+C o quando si invoca `sys.exit()`, il programma deve potersi terminare senza interferenze.

> **Errore comune:** Catturare `BaseException` invece di `Exception` impedisce la terminazione del processo via `KeyboardInterrupt` e `SystemExit`. L'unico caso legittimo per `except BaseException` e nei framework di logging che devono garantire il flush dei buffer prima del crash, e anche in quel caso l'eccezione va ri-sollevata immediatamente.

Le eccezioni piu comuni che incontrerai quotidianamente sono:

- **`ValueError`** — un valore ha il tipo giusto ma contenuto errato (`int("abc")`)
- **`TypeError`** — operazione su un tipo non appropriato (`"testo" + 42`)
- **`KeyError`** — chiave assente in un dizionario (`d["chiave_inesistente"]`)
- **`IndexError`** — indice fuori dai limiti di una sequenza (`lista[100]` su una lista corta)
- **`FileNotFoundError`** — file o directory non trovata
- **`PermissionError`** — permessi insufficienti per l'operazione richiesta
- **`ConnectionError`** — errore di connessione di rete (e le sue sottoclassi)
- **`TimeoutError`** — operazione scaduta per timeout
- **`OSError`** — errore generico del sistema operativo (classe base per molte eccezioni I/O)
- **`AttributeError`** — attributo non trovato su un oggetto
- **`ImportError`** — impossibile importare un modulo o un nome da un modulo
- **`RuntimeError`** — errore generico a runtime che non rientra in altre categorie
- **`StopIteration`** — segnala la fine di un iteratore (usata internamente dai cicli `for`)
- **`NotImplementedError`** — metodo non ancora implementato (utile nelle classi astratte)

### try/except/else/finally

Il blocco `try/except` e il meccanismo principale per gestire le eccezioni in Python. La struttura completa include quattro clausole con ruoli distinti.

**Blocco try/except base:**

```python
try:
    risultato = int(input("Inserisci un numero: "))
    print(f"Hai inserito: {risultato}")
except ValueError:
    print("Input non valido: inserisci un numero intero.")
```

**Clausole except multiple — ogni tipo di eccezione puo avere un gestore dedicato:**

```python
def leggi_configurazione(percorso: str) -> dict:
    try:
        with open(percorso, 'r') as f:
            import json
            return json.load(f)
    except FileNotFoundError:
        print(f"File di configurazione '{percorso}' non trovato.")
        return {}
    except PermissionError:
        print(f"Permessi insufficienti per leggere '{percorso}'.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing JSON alla riga {e.lineno}: {e.msg}")
        return {}
```

**Catturare piu eccezioni in una singola clausola:**

```python
try:
    valore = dizionario[chiave]
    elemento = lista[indice]
except (KeyError, IndexError) as e:
    print(f"Accesso fallito: {e}")
```

**La clausola `else` — viene eseguita solo se nessuna eccezione e stata sollevata nel blocco `try`:**

```python
def dividi(a: float, b: float) -> float | None:
    try:
        risultato = a / b
    except ZeroDivisionError:
        print("Impossibile dividere per zero.")
        return None
    else:
        # Eseguito solo se la divisione e riuscita
        print(f"{a} / {b} = {risultato}")
        return risultato
```

La clausola `else` e utile per separare il codice che potrebbe generare eccezioni dal codice che dovrebbe essere eseguito solo in caso di successo, migliorando la leggibilita e evitando di catturare eccezioni non intenzionali.

**La clausola `finally` — viene eseguita sempre, indipendentemente dall'esito:**

```python
def elabora_file(percorso: str) -> None:
    risorsa = None
    try:
        risorsa = open(percorso, 'r')
        dati = risorsa.read()
        processa(dati)
    except FileNotFoundError:
        print("File non trovato.")
    except IOError as e:
        print(f"Errore I/O: {e}")
    else:
        print("Elaborazione completata con successo.")
    finally:
        # Eseguito SEMPRE: pulizia risorse garantita
        if risorsa is not None:
            risorsa.close()
            print("Risorsa rilasciata.")
```

> **Approfondimento:** Il blocco `finally` viene eseguito anche se il blocco `try` contiene un `return`, `break` o `continue`. L'unica eccezione e `os._exit()`, che termina il processo immediatamente senza eseguire cleanup. Riferimento: [Python docs — compound statements, try](https://docs.python.org/3/reference/compound_stmts.html#the-try-statement).

**Exception chaining con `from` — preserva il contesto dell'eccezione originale:**

```python
class ErroreConfigurazione(Exception):
    pass

def carica_config(percorso: str) -> dict:
    try:
        with open(percorso) as f:
            import json
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ErroreConfigurazione(
            f"Configurazione malformata in '{percorso}'"
        ) from e
```

Quando si cattura l'eccezione risultante, l'attributo `__cause__` contiene l'eccezione originale, e il traceback mostra l'intera catena causale.

### Raising Exceptions

Il comando `raise` permette di sollevare eccezioni esplicitamente.

**Sollevare un'eccezione direttamente:**

```python
def imposta_eta(eta: int) -> None:
    if not isinstance(eta, int):
        raise TypeError(f"L'eta deve essere un intero, ricevuto {type(eta).__name__}")
    if eta < 0 or eta > 150:
        raise ValueError(f"Eta non valida: {eta}. Deve essere tra 0 e 150.")
    # ... logica di impostazione
```

**`raise from` per il chaining esplicito:**

```python
def connetti_database(url: str):
    try:
        connessione = driver.connect(url)
    except driver.ConnectionError as e:
        raise RuntimeError(
            f"Impossibile connettersi al database: {url}"
        ) from e
```

**Ri-sollevare l'eccezione corrente con `raise` nudo — utile per loggare e propagare:**

```python
def operazione_critica():
    try:
        esegui_lavoro()
    except Exception:
        import logging
        logging.exception("Errore durante operazione critica")
        raise  # Ri-solleva l'eccezione originale intatta
```

Il `raise` senza argomenti preserva il traceback originale completo, risultando molto piu informativo di `raise e` che creerebbe un nuovo traceback dal punto corrente.

> **Errore comune:** Usare `raise e` invece di `raise` in un blocco `except Exception as e` crea un nuovo traceback che parte dal punto del `raise`, perdendo le informazioni sullo stack originale. Usare sempre `raise` senza argomenti per ri-sollevare.

### Eccezioni Personalizzate

Per applicazioni di dimensioni significative, definire eccezioni personalizzate e una pratica essenziale. Permette di creare una gerarchia di errori specifica per il dominio applicativo.

**Creazione di classi eccezione personalizzate:**

```python
class ErroreApplicazione(Exception):
    """Eccezione base per l'applicazione."""
    pass


class ErroreValidazione(ErroreApplicazione):
    """Errore di validazione dei dati in input."""

    def __init__(self, campo: str, valore, messaggio: str):
        self.campo = campo
        self.valore = valore
        self.messaggio = messaggio
        super().__init__(f"Validazione fallita per '{campo}': {messaggio}")


class ErroreAutenticazione(ErroreApplicazione):
    """Errore di autenticazione utente."""

    def __init__(self, username: str, motivo: str = "credenziali non valide"):
        self.username = username
        self.motivo = motivo
        super().__init__(f"Autenticazione fallita per '{username}': {motivo}")


class ErroreAutorizzazione(ErroreApplicazione):
    """L'utente non ha i permessi necessari."""

    def __init__(self, utente: str, risorsa: str, azione: str):
        self.utente = utente
        self.risorsa = risorsa
        self.azione = azione
        super().__init__(
            f"Utente '{utente}' non autorizzato a {azione} su '{risorsa}'"
        )


class ErroreRisorsa(ErroreApplicazione):
    """Eccezione base per errori relativi a risorse."""
    pass


class RisorsaNonTrovata(ErroreRisorsa):
    """La risorsa richiesta non esiste."""

    def __init__(self, tipo_risorsa: str, identificatore):
        self.tipo_risorsa = tipo_risorsa
        self.identificatore = identificatore
        super().__init__(f"{tipo_risorsa} con id '{identificatore}' non trovato")


class RisorsaGiaEsistente(ErroreRisorsa):
    """La risorsa che si tenta di creare esiste gia."""

    def __init__(self, tipo_risorsa: str, identificatore):
        self.tipo_risorsa = tipo_risorsa
        self.identificatore = identificatore
        super().__init__(f"{tipo_risorsa} con id '{identificatore}' esiste gia")
```

**Utilizzo della gerarchia personalizzata:**

```python
def gestisci_richiesta(richiesta):
    try:
        utente = autentica(richiesta)
        verifica_permessi(utente, richiesta.risorsa)
        risultato = elabora(richiesta)
        return risultato
    except ErroreAutenticazione:
        return risposta_errore(401, "Non autenticato")
    except ErroreAutorizzazione:
        return risposta_errore(403, "Non autorizzato")
    except RisorsaNonTrovata as e:
        return risposta_errore(404, str(e))
    except ErroreValidazione as e:
        return risposta_errore(422, str(e))
    except ErroreApplicazione as e:
        # Cattura qualsiasi altra eccezione dell'applicazione
        return risposta_errore(500, str(e))
```

**Buone pratiche per eccezioni personalizzate:**

- Derivare sempre da `Exception`, mai da `BaseException`
- Creare una eccezione base per l'applicazione da cui derivano tutte le altre
- Aggiungere attributi strutturati (non solo il messaggio stringa)
- Chiamare sempre `super().__init__()` con un messaggio leggibile
- Documentare ogni eccezione con una docstring chiara

> **Approfondimento:** A partire da Python 3.11, il metodo `add_note()` (PEP 678) permette di aggiungere note contestuali a qualsiasi eccezione dopo la sua creazione. Questo e utile per arricchire l'eccezione con contesto aggiuntivo mentre risale lo stack, senza creare nuove eccezioni wrapper.
>
> ```python
> try:
>     processa_record(record)
> except ValueError as e:
>     e.add_note(f"Errore durante elaborazione record #{record.id}")
>     e.add_note(f"Batch: {batch_id}, offset: {offset}")
>     raise
> ```

### Gerarchie di Eccezioni per Domain-Driven Design

Nelle applicazioni strutturate secondo i principi del Domain-Driven Design (DDD), la gerarchia delle eccezioni riflette la separazione tra errori di dominio (regole di business violate) ed errori infrastrutturali (database non raggiungibile, timeout di rete). Questa distinzione e fondamentale perche i due tipi di errore richiedono strategie di gestione completamente diverse: gli errori di dominio producono risposte deterministiche al chiamante, mentre gli errori infrastrutturali attivano pattern di retry, circuit breaker e alerting.

**Separazione dominio vs infrastruttura con codici errore strutturati:**

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone


class CodiceErroreDominio(Enum):
    """Codici errore di dominio — stabili, documentati nell'API pubblica."""
    ORDINE_IMPORTO_INVALIDO = "ORD-001"
    ORDINE_STATO_INVALIDO = "ORD-002"
    PRODOTTO_NON_DISPONIBILE = "ORD-003"
    UTENTE_NON_VERIFICATO = "USR-001"
    LIMITE_CREDITO_SUPERATO = "PAY-001"
    PAGAMENTO_RIFIUTATO = "PAY-002"


class CodiceErroreInfrastruttura(Enum):
    """Codici errore infrastrutturali — interni, non esposti all'API."""
    DATABASE_NON_RAGGIUNGIBILE = "INFRA-DB-001"
    CACHE_TIMEOUT = "INFRA-CACHE-001"
    SERVIZIO_ESTERNO_ERRORE = "INFRA-EXT-001"
    CODA_MESSAGGI_PIENA = "INFRA-MQ-001"


@dataclass(frozen=True)
class ErroreDominio(Exception):
    """Base per errori di business logic — il chiamante puo gestirli."""
    codice: CodiceErroreDominio
    messaggio: str
    dettagli: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __str__(self) -> str:
        return f"[{self.codice.value}] {self.messaggio}"

    def to_dict(self) -> dict:
        return {
            "codice": self.codice.value,
            "messaggio": self.messaggio,
            "dettagli": self.dettagli,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class ErroreInfrastruttura(Exception):
    """Base per errori infrastrutturali — retry e alerting, mai esposti al client."""
    codice: CodiceErroreInfrastruttura
    messaggio: str
    causa: Exception | None = None
    retry_consentito: bool = True

    def __str__(self) -> str:
        return f"[{self.codice.value}] {self.messaggio}"


# --- Eccezioni di dominio specifiche ---

@dataclass(frozen=True)
class ImportoOrdineInvalido(ErroreDominio):
    """L'importo dell'ordine viola le regole di business."""
    importo: float = 0.0
    limite: float = 0.0

    def __post_init__(self):
        # frozen=True richiede object.__setattr__ per inizializzazione condizionale
        if not self.messaggio:
            object.__setattr__(
                self, "messaggio",
                f"Importo {self.importo} supera il limite {self.limite}"
            )


@dataclass(frozen=True)
class ProdottoNonDisponibile(ErroreDominio):
    """Il prodotto richiesto non e disponibile nella quantita richiesta."""
    prodotto_id: str = ""
    quantita_richiesta: int = 0
    quantita_disponibile: int = 0
```

**Mappatura centralizzata eccezioni → risposte HTTP:**

Separare la logica di mappatura in un unico punto permette di mantenere i layer di dominio completamente agnostici rispetto al protocollo HTTP. Il handler centralizzato traduce ogni tipo di eccezione nel codice di stato e nel formato di risposta appropriato.

```python
from typing import Any


# Mappatura tipo eccezione → (codice_http, include_dettagli)
MAPPA_ECCEZIONI_HTTP: dict[type[Exception], tuple[int, bool]] = {
    ErroreDominio: (400, True),
    ImportoOrdineInvalido: (422, True),
    ProdottoNonDisponibile: (409, True),
    ErroreAutenticazione: (401, False),
    ErroreAutorizzazione: (403, False),
    RisorsaNonTrovata: (404, True),
    RisorsaGiaEsistente: (409, True),
    ErroreInfrastruttura: (503, False),  # Mai esporre dettagli interni
}


def traduci_eccezione_http(eccezione: Exception) -> tuple[int, dict[str, Any]]:
    """Traduce un'eccezione di dominio in codice HTTP e body di risposta.

    Il Method Resolution Order (MRO) garantisce che le classi piu specifiche
    vengono matchate prima delle classi base.
    """
    for tipo_exc, (codice, mostra_dettagli) in MAPPA_ECCEZIONI_HTTP.items():
        if isinstance(eccezione, tipo_exc):
            body: dict[str, Any] = {"errore": str(eccezione)}
            if mostra_dettagli and hasattr(eccezione, "to_dict"):
                body = eccezione.to_dict()
            return codice, body

    # Eccezione non mappata — errore generico senza dettagli
    return 500, {"errore": "Errore interno del server"}
```

> **Approfondimento:** L'uso di `@dataclass(frozen=True)` per le eccezioni di dominio garantisce l'immutabilita degli errori dopo la creazione, coerente con il principio DDD che gli errori di dominio sono fatti immutabili. Il pattern `frozen=True` previene anche modifiche accidentali degli attributi durante la propagazione dello stack. L'approccio con `Enum` per i codici errore crea un contratto stabile: i codici diventano parte dell'API pubblica e possono essere documentati nella specifica OpenAPI.

> **Errore comune:** Mischiare eccezioni di dominio e infrastrutturali nella stessa gerarchia. Se `ErrorePagamento` eredita da `ErroreApplicazione` insieme a `ErroreDatabaseNonRaggiungibile`, il chiamante non puo distinguere tra "il pagamento e stato rifiutato dalla banca" (errore deterministico) e "il database non risponde" (errore transitorio retryable). Mantenere le due gerarchie separate permette al middleware di applicare strategie diverse: risposta immediata per errori di dominio, retry + alerting per errori infrastrutturali.

### Exception Groups (Python 3.11+)

A partire da Python 3.11, e possibile sollevare e gestire gruppi di eccezioni simultanee. Questo e particolarmente utile per operazioni concorrenti dove piu task possono fallire indipendentemente.

**`ExceptionGroup` — raggruppare eccezioni multiple:**

```python
def valida_dati_utente(dati: dict) -> None:
    errori = []

    if not dati.get("email"):
        errori.append(ValueError("Email obbligatoria"))
    elif "@" not in dati["email"]:
        errori.append(ValueError("Formato email non valido"))

    if not dati.get("nome"):
        errori.append(ValueError("Nome obbligatorio"))

    eta = dati.get("eta")
    if eta is not None and (not isinstance(eta, int) or eta < 0):
        errori.append(TypeError("Eta deve essere un intero non negativo"))

    if errori:
        raise ExceptionGroup("Errori di validazione", errori)
```

**La sintassi `except*` — gestire tipi specifici all'interno di un gruppo:**

```python
try:
    valida_dati_utente({"email": "invalida", "eta": -5})
except* ValueError as eg:
    print(f"Errori di valore ({len(eg.exceptions)}):")
    for e in eg.exceptions:
        print(f"  - {e}")
except* TypeError as eg:
    print(f"Errori di tipo ({len(eg.exceptions)}):")
    for e in eg.exceptions:
        print(f"  - {e}")
```

**Caso d'uso con operazioni concorrenti:**

```python
import asyncio

async def raccogli_dati():
    """Esegue operazioni concorrenti, raccogliendo tutti gli errori."""
    async with asyncio.TaskGroup() as tg:
        task_utenti = tg.create_task(carica_utenti())
        task_ordini = tg.create_task(carica_ordini())
        task_prodotti = tg.create_task(carica_prodotti())
    # Se piu task falliscono, viene sollevato un ExceptionGroup

# Gestione degli errori del TaskGroup
async def main():
    try:
        await raccogli_dati()
    except* ConnectionError as eg:
        print("Errori di connessione — riprova piu tardi")
    except* TimeoutError as eg:
        print("Timeout — i servizi sono sovraccarichi")
```

La differenza chiave rispetto al tradizionale `except` e che `except*` puo gestire un sottoinsieme delle eccezioni nel gruppo, lasciando che le restanti vengano propagate.

> **Errore comune:** Non si possono mischiare `except` e `except*` nello stesso blocco `try`. Se si usa `except*`, tutti i gestori devono essere `except*`. Tentare di mischiare i due stili genera un `SyntaxError`.

> **Caso reale:** `asyncio.TaskGroup` (Python 3.11+) solleva sempre `ExceptionGroup` quando piu task falliscono. Se si usa il vecchio `asyncio.gather(return_exceptions=True)`, gli errori vengono restituiti come valori nella lista dei risultati — un pattern error-prone che `TaskGroup` + `except*` sostituisce in modo piu sicuro. Riferimento: [PEP 654 — Exception Groups](https://peps.python.org/pep-0654/).

#### Metodi di ExceptionGroup: subgroup() e derive()

`ExceptionGroup` espone metodi per filtrare e trasformare i gruppi di eccezioni in modo programmatico, senza dover iterare manualmente sulle eccezioni contenute.

**`subgroup(condizione)`** restituisce un nuovo `ExceptionGroup` contenente solo le eccezioni che soddisfano la condizione (un tipo o un callable). La struttura annidata viene preservata: se il gruppo contiene sotto-gruppi, `subgroup()` applica il filtro ricorsivamente.

```python
import asyncio

async def task_rete():
    raise ConnectionError("server irraggiungibile")

async def task_validazione():
    raise ValueError("campo 'email' mancante")

async def task_timeout():
    raise TimeoutError("scaduto dopo 30s")

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(task_rete())
            tg.create_task(task_validazione())
            tg.create_task(task_timeout())
    except* BaseException as eg:
        # Filtra solo le eccezioni di rete
        errori_rete = eg.subgroup(ConnectionError)
        if errori_rete:
            print(f"Errori rete: {len(errori_rete.exceptions)}")
            for exc in errori_rete.exceptions:
                print(f"  - {exc}")

        # Filtra con callable per logica custom
        errori_transitori = eg.subgroup(
            lambda e: isinstance(e, (ConnectionError, TimeoutError))
        )
        print(f"Errori transitori: {len(errori_transitori.exceptions)}")

asyncio.run(main())
# Output:
# Errori rete: 1
#   - server irraggiungibile
# Errori transitori: 2
```

**`derive(excs)`** crea un nuovo `ExceptionGroup` con lo stesso messaggio dell'originale ma con un diverso insieme di eccezioni. E utile per trasformare le eccezioni all'interno di un gruppo, ad esempio convertendo errori di basso livello in errori di dominio:

```python
def converti_errori_dominio(eg: ExceptionGroup) -> ExceptionGroup:
    """Trasforma eccezioni di rete in errori di dominio."""
    nuove_eccezioni = []
    for exc in eg.exceptions:
        if isinstance(exc, ConnectionError):
            nuovo = ServizioNonDisponibileError(str(exc))
            nuovo.__cause__ = exc  # preserva la causa originale
            nuove_eccezioni.append(nuovo)
        else:
            nuove_eccezioni.append(exc)
    return eg.derive(nuove_eccezioni)
```

#### ExceptionGroup annidati e pattern reali

Un `ExceptionGroup` puo contenere altri `ExceptionGroup` come sotto-eccezioni, creando strutture ad albero. Questo accade naturalmente quando si annidano `TaskGroup`:

```python
async def pipeline_etl():
    """Pipeline ETL con TaskGroup annidati."""
    async with asyncio.TaskGroup() as tg_principale:
        tg_principale.create_task(fase_estrazione())    # puo fallire
        tg_principale.create_task(fase_trasformazione())  # contiene un suo TaskGroup

async def fase_trasformazione():
    async with asyncio.TaskGroup() as tg_trasf:
        tg_trasf.create_task(trasforma_csv())
        tg_trasf.create_task(trasforma_json())
```

Se entrambi i task interni di `fase_trasformazione` falliscono e anche `fase_estrazione` fallisce, il risultato e un `ExceptionGroup` che contiene un altro `ExceptionGroup`:

```
ExceptionGroup("unhandled errors in a TaskGroup", [
    <ErroreEstrazione>,
    ExceptionGroup("unhandled errors in a TaskGroup", [
        <ErroreCSV>,
        <ErroreJSON>,
    ]),
])
```

`subgroup()` attraversa questa struttura ricorsivamente, il che e fondamentale per non perdere eccezioni in strutture profonde.

#### PEP 678 — add_note() e arricchimento eccezioni

PEP 678 (Python 3.11+) aggiunge il metodo `add_note()` a tutte le eccezioni, permettendo di arricchire un'eccezione con contesto aggiuntivo senza creare una nuova eccezione o usare chaining:

```python
async def processa_batch(items: list[dict]) -> list:
    risultati = []
    try:
        async with asyncio.TaskGroup() as tg:
            for item in items:
                tg.create_task(processa_singolo(item))
    except* ValueError as eg:
        for exc in eg.exceptions:
            exc.add_note(f"Batch ID: {batch_id}")
            exc.add_note(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        raise  # ri-propaga con le note aggiunte
    return risultati
```

Le note appaiono nel traceback sotto l'eccezione originale, fornendo contesto senza alterare il tipo o il messaggio dell'eccezione.

#### Gestione multipla con except*

Un singolo blocco `try` puo avere piu clausole `except*`, ciascuna che gestisce un tipo diverso. Ogni clausola riceve solo le eccezioni del tipo corrispondente; se rimangono eccezioni non gestite, vengono ri-propagate automaticamente:

```python
async def esegui_microservizi():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(servizio_autenticazione())
            tg.create_task(servizio_pagamento())
            tg.create_task(servizio_inventario())
            tg.create_task(servizio_notifiche())
    except* PermissionError as eg:
        log.error("errori_autenticazione",
                  count=len(eg.exceptions),
                  dettagli=[str(e) for e in eg.exceptions])
        # Non ri-lanciare: gli errori di autenticazione sono gestiti
    except* PaymentError as eg:
        log.critical("errori_pagamento", count=len(eg.exceptions))
        for exc in eg.exceptions:
            sentry_sdk.capture_exception(exc)
        raise  # I pagamenti falliti devono propagarsi
    except* (ConnectionError, TimeoutError) as eg:
        log.warning("errori_transitori",
                    count=len(eg.exceptions),
                    tipi=[type(e).__name__ for e in eg.exceptions])
        # Tentare fallback per errori transitori
```

> **Approfondimento:** `except*` non e solo zucchero sintattico — cambia la semantica dell'error handling. Con `except` tradizionale, la prima clausola che corrisponde vince e il resto viene ignorato. Con `except*`, **tutte** le clausole applicabili vengono eseguite, ciascuna sul proprio sottoinsieme dell'`ExceptionGroup`. Le eccezioni non corrispondenti a nessuna clausola vengono automaticamente ri-propagate in un nuovo `ExceptionGroup`. Riferimento: [PEP 654 — Exception Groups and except*](https://peps.python.org/pep-0654/).

> **Errore comune:** Usare `except*` per catturare `ExceptionGroup` stesso non funziona come ci si aspetta. `except* ExceptionGroup` corrisponde alle eccezioni *contenute* nel gruppo che sono a loro volta `ExceptionGroup` (gruppi annidati), non al gruppo esterno. Per ispezionare il gruppo esterno, usare un normale `except ExceptionGroup as eg:` in un blocco `try` separato.

---

## EAFP vs LBYL

Python adotta culturalmente il paradigma **EAFP** (Easier to Ask Forgiveness than Permission), in contrasto con lo stile **LBYL** (Look Before You Leap) piu comune in linguaggi come C o Java.

**LBYL — controllare prima di agire:**

```python
# Stile LBYL
def ottieni_valore_lbyl(dizionario: dict, chiave: str):
    if chiave in dizionario:
        return dizionario[chiave]
    else:
        return "valore_predefinito"

# LBYL con file
import os
def leggi_file_lbyl(percorso: str) -> str:
    if os.path.exists(percorso):
        if os.path.isfile(percorso):
            if os.access(percorso, os.R_OK):
                with open(percorso) as f:
                    return f.read()
    return ""
```

**EAFP — provare e gestire l'eccezione:**

```python
# Stile EAFP
def ottieni_valore_eafp(dizionario: dict, chiave: str):
    try:
        return dizionario[chiave]
    except KeyError:
        return "valore_predefinito"

# EAFP con file
def leggi_file_eafp(percorso: str) -> str:
    try:
        with open(percorso) as f:
            return f.read()
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return ""
```

**Quando usare ciascun approccio:**

EAFP e preferibile quando:
- L'operazione ha successo nella maggior parte dei casi (il "happy path" e comune)
- Il controllo preventivo introduce una race condition (come verificare l'esistenza di un file prima di aprirlo: un altro processo potrebbe eliminarlo nell'intervallo)
- Il controllo e costoso quanto l'operazione stessa
- Si lavora con duck typing dove il tipo non si conosce in anticipo

LBYL e preferibile quando:
- L'operazione ha effetti collaterali irreversibili
- Il fallimento e la condizione comune, non l'eccezione
- La condizione da verificare e semplice e non soggetta a race condition
- Le eccezioni hanno un costo significativo in un hot path

**Implicazioni sulle prestazioni:**

```python
import timeit

dizionario = {str(i): i for i in range(1000)}

# LBYL - leggermente piu veloce quando la chiave NON esiste
def lbyl():
    if "chiave_assente" in dizionario:
        return dizionario["chiave_assente"]
    return None

# EAFP - leggermente piu veloce quando la chiave ESISTE
def eafp():
    try:
        return dizionario["chiave_assente"]
    except KeyError:
        return None
```

In Python, la creazione e la gestione delle eccezioni ha un costo, quindi nei cicli ad alta frequenza dove l'eccezione e prevista spesso, LBYL puo essere piu performante. Al contrario, il blocco `try` senza eccezione sollevata ha un costo quasi nullo.

---

## Context Manager per Error Handling

I context manager, gia esplorati nella guida dedicata, offrono strumenti eleganti per la gestione degli errori.

**`suppress()` da contextlib — silenziare eccezioni specifiche:**

```python
from contextlib import suppress

# Invece di:
try:
    os.remove("file_temporaneo.tmp")
except FileNotFoundError:
    pass

# Si puo scrivere:
with suppress(FileNotFoundError):
    os.remove("file_temporaneo.tmp")
```

**Context manager personalizzato per la gestione errori:**

```python
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def gestione_errori(operazione: str, errore_default=None):
    """Context manager che logga gli errori e restituisce un valore di default."""
    try:
        yield
    except Exception as e:
        logger.error(f"Errore durante {operazione}: {e}", exc_info=True)
        if errore_default is not None:
            return errore_default
        raise

# Utilizzo
with gestione_errori("caricamento configurazione"):
    config = carica_configurazione()
```

**Context manager per transazioni database:**

```python
from contextlib import contextmanager

@contextmanager
def transazione(connessione):
    """Gestisce commit/rollback automatico di una transazione."""
    cursore = connessione.cursor()
    try:
        yield cursore
        connessione.commit()
    except Exception:
        connessione.rollback()
        raise
    finally:
        cursore.close()

# Utilizzo
with transazione(db_conn) as cursore:
    cursore.execute("INSERT INTO utenti (nome) VALUES (?)", ("Mario",))
    cursore.execute("INSERT INTO log (azione) VALUES (?)", ("nuovo_utente",))
    # Se una query fallisce, viene eseguito il rollback di entrambe
```

---

## Logging

### Modulo logging

Il modulo `logging` della libreria standard di Python e un framework completo e flessibile per la registrazione di eventi. A differenza dei semplici `print()`, il logging offre livelli di gravita, output multipli, formattazione configurabile e filtraggio avanzato.

**Livelli di log (in ordine crescente di gravita):**

| Livello    | Valore | Utilizzo                                           |
|------------|--------|----------------------------------------------------|
| `DEBUG`    | 10     | Dettagli diagnostici, utili solo durante lo sviluppo |
| `INFO`     | 20     | Conferma che le operazioni funzionano come previsto  |
| `WARNING`  | 30     | Qualcosa di inatteso, ma il programma funziona ancora |
| `ERROR`    | 40     | Errore che impedisce l'esecuzione di una funzionalita |
| `CRITICAL` | 50     | Errore grave, il programma potrebbe non continuare    |

**Configurazione rapida con `basicConfig()`:**

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.debug("Messaggio di debug")
logging.info("Applicazione avviata")
logging.warning("Disco quasi pieno")
logging.error("Connessione al database fallita")
logging.critical("Sistema in stato inconsistente")
```

**Architettura del modulo logging — quattro componenti fondamentali:**

- **Logger** — l'oggetto su cui si invocano i metodi di log (`logger.info()`, ecc.)
- **Handler** — determina dove vengono inviati i messaggi (console, file, rete, ecc.)
- **Formatter** — definisce il formato del messaggio di log
- **Filter** — permette il filtraggio granulare dei messaggi

```python
import logging

# Creare un logger con nome (best practice)
logger = logging.getLogger("mia_app.modulo")
logger.setLevel(logging.DEBUG)

# Handler per la console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Handler per il file
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)

# Formattazione
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Aggiungere gli handler al logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Utilizzo
logger.info("Server avviato sulla porta 8080")
logger.debug("Parametri di connessione: host=localhost, pool_size=5")
```

### Configurazione Logger

**`getLogger()` e la gerarchia dei logger:**

I logger sono organizzati in una gerarchia basata sul nome, separato da punti. Un logger figlio eredita la configurazione del padre.

```python
import logging

# Logger radice
root_logger = logging.getLogger()

# Logger dell'applicazione
app_logger = logging.getLogger("mia_app")

# Logger dei moduli — ereditano da "mia_app"
db_logger = logging.getLogger("mia_app.database")
api_logger = logging.getLogger("mia_app.api")
auth_logger = logging.getLogger("mia_app.api.auth")

# Impostare il livello sul padre influenza i figli
app_logger.setLevel(logging.INFO)

# Ma un figlio puo sovrascrivere
db_logger.setLevel(logging.DEBUG)  # Piu verboso per il debug del database
```

La convenzione piu diffusa e usare `__name__` come nome del logger in ogni modulo:

```python
# In qualsiasi modulo
logger = logging.getLogger(__name__)
```

Questo crea automaticamente una gerarchia che rispecchia la struttura dei package Python.

**Tipi di Handler:**

```python
import logging
from logging.handlers import (
    RotatingFileHandler,
    TimedRotatingFileHandler,
    SocketHandler,
    SMTPHandler,
    SysLogHandler,
)

# StreamHandler — scrive su stdout/stderr
console = logging.StreamHandler()

# FileHandler — scrive su un file
file_h = logging.FileHandler("app.log", encoding="utf-8")

# RotatingFileHandler — ruota il file quando raggiunge una certa dimensione
rotating = RotatingFileHandler(
    "app.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,               # Mantiene fino a 5 file di backup
    encoding="utf-8"
)

# TimedRotatingFileHandler — ruota il file a intervalli temporali
timed = TimedRotatingFileHandler(
    "app.log",
    when="midnight",     # Ruota a mezzanotte
    interval=1,          # Ogni giorno
    backupCount=30,      # Mantiene 30 giorni
    encoding="utf-8"
)

# SocketHandler — invia i log via rete TCP
socket_h = SocketHandler("logserver.example.com", 9020)

# SMTPHandler — invia email per errori critici
smtp = SMTPHandler(
    mailhost=("smtp.example.com", 587),
    fromaddr="app@example.com",
    toaddrs=["admin@example.com"],
    subject="Errore Critico nell'Applicazione",
    credentials=("utente", "password"),
    secure=()
)
smtp.setLevel(logging.CRITICAL)

# SysLogHandler — invia al syslog del sistema
syslog = SysLogHandler(address="/dev/log")
```

**Sintassi del Formatter e formatter personalizzati:**

```python
import logging
from datetime import datetime, timezone

# Attributi disponibili nel format string:
# %(asctime)s      — timestamp
# %(name)s         — nome del logger
# %(levelname)s    — livello (DEBUG, INFO, ...)
# %(message)s      — il messaggio di log
# %(filename)s     — nome del file sorgente
# %(lineno)d       — numero di riga
# %(funcName)s     — nome della funzione
# %(process)d      — ID del processo
# %(thread)d       — ID del thread
# %(threadName)s   — nome del thread
# %(pathname)s     — percorso completo del file sorgente
# %(module)s       — nome del modulo

formatter_dettagliato = logging.Formatter(
    fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Formatter personalizzato con colori per il terminale
class FormatterColorato(logging.Formatter):
    COLORI = {
        logging.DEBUG: "\033[36m",      # Ciano
        logging.INFO: "\033[32m",       # Verde
        logging.WARNING: "\033[33m",    # Giallo
        logging.ERROR: "\033[31m",      # Rosso
        logging.CRITICAL: "\033[41m",   # Sfondo rosso
    }
    RESET = "\033[0m"

    def format(self, record):
        colore = self.COLORI.get(record.levelno, self.RESET)
        record.levelname = f"{colore}{record.levelname}{self.RESET}"
        return super().format(record)
```

**Implementazione di un Filter:**

```python
import logging

class FiltroModulo(logging.Filter):
    """Filtra i log accettando solo quelli da moduli specifici."""

    def __init__(self, moduli_permessi: list[str]):
        super().__init__()
        self.moduli_permessi = moduli_permessi

    def filter(self, record: logging.LogRecord) -> bool:
        return any(record.name.startswith(m) for m in self.moduli_permessi)


class FiltroParoleChiave(logging.Filter):
    """Esclude i messaggi che contengono parole sensibili."""

    PAROLE_SENSIBILI = {"password", "secret", "token", "api_key"}

    def filter(self, record: logging.LogRecord) -> bool:
        messaggio = record.getMessage().lower()
        return not any(parola in messaggio for parola in self.PAROLE_SENSIBILI)

# Applicazione del filtro
logger = logging.getLogger("mia_app")
logger.addFilter(FiltroParoleChiave())
```

### Configurazione Avanzata

**`dictConfig()` — l'approccio raccomandato per la configurazione:**

```python
import logging.config

CONFIG_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "dettagliato": {
            "format": (
                "%(asctime)s [%(levelname)s] %(name)s "
                "(%(filename)s:%(lineno)d) %(funcName)s: %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    "filters": {
        "no_sensitive": {
            "()": "mia_app.logging_filters.FiltroParoleChiave",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file_debug": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "dettagliato",
            "filename": "logs/debug.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "file_errori": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "dettagliato",
            "filename": "logs/errori.log",
            "maxBytes": 10485760,
            "backupCount": 10,
            "encoding": "utf-8",
            "filters": ["no_sensitive"],
        },
        "email_critico": {
            "class": "logging.handlers.SMTPHandler",
            "level": "CRITICAL",
            "formatter": "dettagliato",
            "mailhost": ["smtp.example.com", 587],
            "fromaddr": "app@example.com",
            "toaddrs": ["admin@example.com"],
            "subject": "CRITICO: Errore nell'applicazione",
            "credentials": ["utente", "password"],
            "secure": [],
        },
    },

    "loggers": {
        "mia_app": {
            "level": "DEBUG",
            "handlers": ["console", "file_debug", "file_errori"],
            "propagate": False,
        },
        "mia_app.database": {
            "level": "WARNING",
            "handlers": ["console", "file_debug", "file_errori"],
            "propagate": False,
        },
    },

    "root": {
        "level": "WARNING",
        "handlers": ["console"],
    },
}

logging.config.dictConfig(CONFIG_LOGGING)
```

**`fileConfig()` — configurazione da file INI:**

```ini
; logging.conf
[loggers]
keys=root,miaApp

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=WARNING
handlers=consoleHandler

[logger_miaApp]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=mia_app
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('app.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

```python
import logging.config

logging.config.fileConfig("logging.conf")
```

**Configurazione basata su YAML (richiede PyYAML):**

```yaml
# logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: standard
    filename: logs/app.log
    maxBytes: 10485760
    backupCount: 5

root:
  level: DEBUG
  handlers: [console, file]
```

```python
import logging.config
import yaml

with open("logging.yaml") as f:
    config = yaml.safe_load(f)

logging.config.dictConfig(config)
```

### Logging Strutturato

Il logging tradizionale produce messaggi di testo non strutturati, difficili da analizzare automaticamente. Il logging strutturato utilizza un formato come JSON, rendendo i log facilmente interrogabili e analizzabili.

**JSON logging con `python-json-logger`:**

```python
# pip install python-json-logger
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("mia_app")
handler = logging.StreamHandler()

formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
    datefmt="%Y-%m-%dT%H:%M:%S%z"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Log con campi strutturati aggiuntivi
logger.info(
    "Ordine creato",
    extra={
        "ordine_id": "ORD-12345",
        "utente_id": "USR-789",
        "importo": 129.99,
        "valuta": "EUR",
    }
)
# Output JSON:
# {"timestamp": "2026-03-27T10:30:00+0100", "name": "mia_app",
#  "level": "INFO", "message": "Ordine creato",
#  "ordine_id": "ORD-12345", "utente_id": "USR-789",
#  "importo": 129.99, "valuta": "EUR"}
```

**Correlation ID per tracciare le richieste attraverso i microservizi:**

```python
import logging
import uuid
import contextvars

# Variabile di contesto per il correlation ID
correlation_id_var = contextvars.ContextVar("correlation_id", default=None)


class FiltroCorrelazione(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get() or "N/A"
        return True


def imposta_correlation_id(correlation_id: str | None = None) -> str:
    """Imposta un correlation ID per la richiesta corrente."""
    cid = correlation_id or str(uuid.uuid4())
    correlation_id_var.set(cid)
    return cid


# Configurazione
logger = logging.getLogger("mia_app")
logger.addFilter(FiltroCorrelazione())
formatter = logging.Formatter(
    "%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s: %(message)s"
)
```

**Logging del contesto delle richieste HTTP:**

```python
import logging
import time

logger = logging.getLogger("mia_app.api")

def middleware_logging(richiesta, prossimo_handler):
    """Middleware che logga dettagli di ogni richiesta HTTP."""
    correlation_id = imposta_correlation_id(
        richiesta.headers.get("X-Correlation-ID")
    )

    logger.info(
        "Richiesta ricevuta",
        extra={
            "metodo": richiesta.method,
            "percorso": richiesta.path,
            "ip_client": richiesta.remote_addr,
            "user_agent": richiesta.headers.get("User-Agent"),
        }
    )

    inizio = time.perf_counter()
    risposta = prossimo_handler(richiesta)
    durata_ms = (time.perf_counter() - inizio) * 1000

    logger.info(
        "Risposta inviata",
        extra={
            "codice_stato": risposta.status_code,
            "durata_ms": round(durata_ms, 2),
            "dimensione_risposta": len(risposta.data),
        }
    )

    risposta.headers["X-Correlation-ID"] = correlation_id
    return risposta
```

**Performance logging:**

```python
import logging
import time
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger("mia_app.performance")

@contextmanager
def misura_tempo(operazione: str, soglia_warning_ms: float = 1000):
    """Context manager per misurare e loggare la durata di un'operazione."""
    inizio = time.perf_counter()
    try:
        yield
    finally:
        durata_ms = (time.perf_counter() - inizio) * 1000
        extra = {"operazione": operazione, "durata_ms": round(durata_ms, 2)}
        if durata_ms > soglia_warning_ms:
            logger.warning(f"Operazione lenta: {operazione}", extra=extra)
        else:
            logger.debug(f"Operazione completata: {operazione}", extra=extra)


def log_prestazioni(soglia_ms: float = 500):
    """Decoratore per loggare la durata delle funzioni."""
    def decoratore(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with misura_tempo(func.__qualname__, soglia_ms):
                return func(*args, **kwargs)
        return wrapper
    return decoratore


# Utilizzo
@log_prestazioni(soglia_ms=200)
def query_complessa(parametri):
    # ... esecuzione query
    pass

with misura_tempo("elaborazione_batch"):
    elabora_tutti_i_record()
```

### Logging in Produzione

**Strategie di rotazione dei log:**

```python
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Rotazione per dimensione — ideale per log ad alto volume
rotating = RotatingFileHandler(
    "logs/app.log",
    maxBytes=50 * 1024 * 1024,  # 50 MB per file
    backupCount=10,              # Totale: ~500 MB di log
    encoding="utf-8"
)

# Rotazione temporale — ideale per analisi cronologiche
timed = TimedRotatingFileHandler(
    "logs/app.log",
    when="midnight",
    interval=1,
    backupCount=90,    # 90 giorni di log
    encoding="utf-8",
    utc=True           # Usa UTC per evitare ambiguita
)
timed.suffix = "%Y-%m-%d"  # Formato del suffisso dei file ruotati
```

**Logging centralizzato — integrazione con ELK Stack e Grafana Loki:**

```python
# Per ELK Stack (Elasticsearch, Logstash, Kibana)
# I log JSON vengono inviati a Logstash via SocketHandler o file
# che Filebeat raccoglie

# Esempio con invio diretto a Logstash via TCP
import logging
from logging.handlers import SocketHandler
import json

class LogstashHandler(logging.Handler):
    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port

    def emit(self, record):
        import socket
        try:
            log_entry = {
                "@timestamp": self.format(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "host": socket.gethostname(),
                "application": "mia_app",
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            s = socket.create_connection((self.host, self.port), timeout=5)
            s.sendall((json.dumps(log_entry) + "\n").encode())
            s.close()
        except Exception:
            self.handleError(record)
```

**Livelli di log nei diversi ambienti:**

```python
import os

AMBIENTE = os.getenv("APP_ENV", "development")

LIVELLI_PER_AMBIENTE = {
    "development": {
        "root": "DEBUG",
        "mia_app": "DEBUG",
        "mia_app.database": "DEBUG",
        "urllib3": "WARNING",
    },
    "staging": {
        "root": "INFO",
        "mia_app": "DEBUG",
        "mia_app.database": "INFO",
        "urllib3": "WARNING",
    },
    "production": {
        "root": "WARNING",
        "mia_app": "INFO",
        "mia_app.database": "WARNING",
        "urllib3": "ERROR",
    },
}
```

**Mascheramento dei dati sensibili:**

```python
import logging
import re

class FiltroMascheramentoDati(logging.Filter):
    """Maschera dati sensibili nei messaggi di log."""

    PATTERN = [
        (re.compile(r'(?i)(password|pwd|secret|token|api_key)\s*[=:]\s*\S+'),
         r'\1=***MASCHERATO***'),
        (re.compile(r'\b\d{16}\b'),                  # Numeri carta di credito
         '****-****-****-****'),
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
         '***@***.***'),                               # Email
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),       # SSN (formato US)
         '***-**-****'),
    ]

    def filter(self, record):
        messaggio = record.getMessage()
        for pattern, sostituzione in self.PATTERN:
            messaggio = pattern.sub(sostituzione, messaggio)
        record.msg = messaggio
        record.args = ()
        return True
```

**Impatto sulle prestazioni del logging:**

```python
import logging

logger = logging.getLogger("mia_app")

# MALE: la stringa viene sempre formattata, anche se il livello e disabilitato
logger.debug(f"Risultato query: {risultato_complesso.to_dict()}")

# BENE: la formattazione avviene solo se il messaggio viene effettivamente loggato
logger.debug("Risultato query: %s", risultato_complesso)

# BENE: controllo esplicito per operazioni costose
if logger.isEnabledFor(logging.DEBUG):
    dettagli = genera_report_dettagliato()  # Operazione costosa
    logger.debug("Report dettagliato: %s", dettagli)
```

---

## structlog — Logging Strutturato Avanzato

`structlog` e la libreria di riferimento per il logging strutturato in Python. A differenza di `python-json-logger` che aggiunge la serializzazione JSON al modulo `logging` stdlib, structlog ridisegna l'intero flusso del logging attorno a due principi: **log events come dizionari** e **processori componibili in pipeline**.

Riferimento: [structlog documentation](https://www.structlog.org/en/stable/) — consultato 2026-05-23.

### Architettura e concetti fondamentali

structlog opera su un modello a pipeline: ogni log event e un dizionario Python che attraversa una catena di **processori**. Ogni processore riceve il dizionario, lo modifica (o decide di scartarlo) e lo passa al successivo. L'ultimo processore nella catena e il **renderer**, che produce l'output finale (JSON, testo formattato per console, ecc.).

```
  logger.info("evento", chiave="valore")
       │
       ▼
  ┌─────────────────────────┐
  │   merge_contextvars()   │  ← inietta bind da contextvars
  ├─────────────────────────┤
  │   add_log_level()       │  ← aggiunge "level": "info"
  ├─────────────────────────┤
  │   add_logger_name()     │  ← aggiunge "logger": "mia_app.api"
  ├─────────────────────────┤
  │   TimeStamper(utc=True) │  ← aggiunge "timestamp": "2026-..."
  ├─────────────────────────┤
  │   StackInfoRenderer()   │  ← aggiunge stack trace se richiesto
  ├─────────────────────────┤
  │   format_exc_info()     │  ← formatta eccezioni
  ├─────────────────────────┤
  │   JSONRenderer()        │  ← serializza in JSON → stdout
  └─────────────────────────┘
```

I concetti chiave:

- **Logger factory** — funzione che crea il logger sottostante (puo essere stdlib `logging.getLogger` o `PrintLogger`)
- **Wrapper class** — la classe del bound logger restituito da `structlog.get_logger()` (default: `BoundLogger`)
- **Processor chain** — lista ordinata di callable, ciascuno con firma `(logger, method_name, event_dict) -> event_dict`
- **Renderer** — l'ultimo processore, che produce la stringa finale

### Configurazione globale

La configurazione di structlog si fa una sola volta all'avvio dell'applicazione con `structlog.configure()`. Tutte le chiamate successive a `structlog.get_logger()` utilizzano questa configurazione.

**Configurazione per sviluppo (output colorato su console):**

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.dev.ConsoleRenderer(),  # Output colorato e leggibile
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

**Configurazione per produzione (JSON su stdout per raccolta centralizzata):**

```python
import logging
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

> **Errore comune:** Chiamare `structlog.configure()` piu volte in moduli diversi. La configurazione e globale e deve essere invocata una sola volta, tipicamente nel modulo di entry point (`main.py`, `app.py`, o la funzione `create_app()` di un framework web). Chiamate successive sovrascrivono la configurazione precedente senza warning.

**Scegliere la `wrapper_class`:**

```python
# Filtraggio a livello di bind (piu veloce, non passa per stdlib)
# make_filtering_bound_logger accetta il livello minimo come intero
wrapper = structlog.make_filtering_bound_logger(logging.WARNING)

# BoundLogger standard (nessun filtraggio a livello structlog)
wrapper = structlog.stdlib.BoundLogger
```

`make_filtering_bound_logger()` e la scelta raccomandata quando non si ha bisogno di routing tramite stdlib: i messaggi sotto la soglia vengono scartati immediatamente senza attraversare la pipeline dei processori, risparmiando cicli CPU.

### Processori built-in e custom

**Processori piu utilizzati dalla libreria:**

| Processore | Funzione |
|---|---|
| `merge_contextvars` | Inietta i binding da `contextvars` nel dizionario evento |
| `add_log_level` | Aggiunge la chiave `level` (`info`, `warning`, ecc.) |
| `add_logger_name` | Aggiunge `logger` con il nome del logger |
| `TimeStamper(fmt="iso", utc=True)` | Aggiunge `timestamp` in formato ISO 8601 UTC |
| `StackInfoRenderer()` | Aggiunge stack trace se `stack_info=True` |
| `format_exc_info` | Formatta `exc_info` come stringa leggibile |
| `UnicodeDecoder()` | Decodifica bytes in stringhe |
| `ExceptionRenderer()` | Rendering dettagliato delle eccezioni |
| `JSONRenderer()` | Serializza l'evento in JSON |
| `dev.ConsoleRenderer()` | Rendering colorato per terminale |
| `CallsiteParameterAdder()` | Aggiunge file, linea, funzione del chiamante |

**Scrivere un processore custom:**

```python
import structlog

def aggiungi_ambiente(logger, method_name, event_dict):
    """Processore custom: aggiunge informazioni sull'ambiente."""
    import os
    event_dict["ambiente"] = os.getenv("APP_ENV", "development")
    event_dict["servizio"] = os.getenv("SERVICE_NAME", "sconosciuto")
    event_dict["hostname"] = os.getenv("HOSTNAME", "localhost")
    return event_dict


def censura_dati_sensibili(logger, method_name, event_dict):
    """Processore custom: maschera campi sensibili nel log event."""
    CAMPI_SENSIBILI = {"password", "token", "secret", "api_key", "authorization"}
    for chiave in list(event_dict.keys()):
        if chiave.lower() in CAMPI_SENSIBILI:
            event_dict[chiave] = "***CENSURATO***"
    return event_dict


def filtra_per_livello_minimo(livello_minimo: int):
    """Factory di processore: scarta eventi sotto il livello minimo."""
    def processore(logger, method_name, event_dict):
        livello_corrente = event_dict.get("_level", 0)
        if livello_corrente < livello_minimo:
            raise structlog.DropEvent
        return event_dict
    return processore
```

**Ordine dei processori nella pipeline:**

```python
structlog.configure(
    processors=[
        # 1. Prima iniettare il contesto
        structlog.contextvars.merge_contextvars,
        # 2. Poi aggiungere metadata
        structlog.processors.add_log_level,
        structlog.processors.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        # 3. Processori custom dell'applicazione
        aggiungi_ambiente,
        censura_dati_sensibili,
        # 4. Gestione eccezioni
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # 5. Ultimo: rendering
        structlog.processors.JSONRenderer(),
    ],
    # ...
)
```

> **Approfondimento:** L'ordine dei processori e critico. `merge_contextvars` deve essere il primo (o tra i primi) per garantire che i binding da contextvars siano disponibili a tutti i processori successivi. I processori di censura/sanitizzazione devono precedere il renderer finale. Riferimento: [structlog — Processors](https://www.structlog.org/en/stable/processors.html), consultato 2026-05-23.

### Bound Logger e contesto

Un **bound logger** e un logger a cui sono stati associati coppie chiave-valore persistenti. Ogni successiva chiamata di log include automaticamente questi campi.

```python
import structlog

log = structlog.get_logger()

# Bind crea un NUOVO logger con i campi aggiuntivi (immutabile)
log_utente = log.bind(utente_id="USR-789", ruolo="admin")

log_utente.info("login_riuscito")
# {"utente_id": "USR-789", "ruolo": "admin", "event": "login_riuscito", ...}

log_utente.info("accesso_risorsa", risorsa="/api/admin/config")
# {"utente_id": "USR-789", "ruolo": "admin", "event": "accesso_risorsa",
#  "risorsa": "/api/admin/config", ...}

# unbind rimuove campi
log_base = log_utente.unbind("ruolo")
log_base.info("operazione")
# {"utente_id": "USR-789", "event": "operazione", ...}

# new() crea un logger pulito con solo i processori configurati
log_pulito = log_utente.new()
log_pulito.info("nuova_sessione")
# {"event": "nuova_sessione", ...}
```

**Pattern per servizio con contesto ricco:**

```python
import structlog

class ServizioOrdini:
    def __init__(self):
        self.log = structlog.get_logger().bind(servizio="ordini")

    def crea_ordine(self, utente_id: str, prodotti: list[dict]) -> str:
        log = self.log.bind(
            utente_id=utente_id,
            n_prodotti=len(prodotti),
        )

        log.info("creazione_ordine_iniziata")

        try:
            ordine_id = self._processa_ordine(prodotti)
            log.info("ordine_creato", ordine_id=ordine_id)
            return ordine_id
        except Exception:
            log.exception("creazione_ordine_fallita")
            raise

    def _processa_ordine(self, prodotti: list[dict]) -> str:
        # ... logica di business
        return "ORD-12345"
```

### Rendering JSON e console

**`JSONRenderer` — per produzione:**

```python
import structlog

# JSONRenderer usa json.dumps() con parametri configurabili
renderer = structlog.processors.JSONRenderer(
    serializer=None,      # default: json.dumps
    sort_keys=False,       # mantiene ordine di inserimento
)

# Con serializzatore custom (es. orjson per performance)
import orjson

def serializza_orjson(obj, **kwargs):
    return orjson.dumps(obj, option=orjson.OPT_NON_STR_KEYS).decode()

renderer_veloce = structlog.processors.JSONRenderer(
    serializer=serializza_orjson
)
```

**`ConsoleRenderer` — per sviluppo:**

```python
import structlog

# Output colorato e formattato per il terminale
renderer_console = structlog.dev.ConsoleRenderer(
    colors=True,           # ANSI colors
    pad_event=40,          # padding dell'evento per allineamento
    repr_native_str=False, # non wrappare stringhe in repr()
)

# Output esempio:
# 2026-05-23T10:30:00Z [info     ] ordine_creato    ordine_id=ORD-12345 utente_id=USR-789
```

### Integrazione con stdlib logging

Il pattern piu potente di structlog e l'integrazione con il modulo `logging` stdlib. Questo permette di:

1. Usare structlog come interfaccia di logging nell'applicazione
2. Passare gli eventi attraverso stdlib `logging` per il routing (handler, filtri)
3. Catturare anche i log di librerie terze che usano stdlib

La chiave e `structlog.stdlib.ProcessorFormatter`, che permette a stdlib di usare la pipeline di processori di structlog per il rendering finale.

```python
import logging
import structlog

# --- Processori condivisi (usati sia da structlog che da stdlib) ---
shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

# --- Configurazione structlog → stdlib bridge ---
structlog.configure(
    processors=shared_processors + [
        # Questo processore DEVE essere l'ultimo prima di stdlib
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# --- Configurazione stdlib logging con ProcessorFormatter ---
formatter = structlog.stdlib.ProcessorFormatter(
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.processors.JSONRenderer(),  # o ConsoleRenderer() per dev
    ],
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)
```

Con questa configurazione:

```python
# Codice applicativo — usa structlog
import structlog
log = structlog.get_logger()
log.info("ordine_creato", ordine_id="ORD-123")
# → JSON su stdout

# Librerie terze — usano stdlib logging
import logging
lib_logger = logging.getLogger("httpx")
lib_logger.warning("Connection pool exhausted")
# → anche questo viene formattato da ProcessorFormatter come JSON
```

> **Approfondimento:** La differenza critica tra `structlog.PrintLoggerFactory()` e `structlog.stdlib.LoggerFactory()`: la prima crea `PrintLogger` che scrive direttamente su stdout, bypassando completamente stdlib. La seconda crea wrapper attorno a `logging.getLogger()`, permettendo l'uso di handler, filtri e la gerarchia stdlib. Per applicazioni in produzione che necessitano anche di OTel log bridge, usare sempre `stdlib.LoggerFactory()`.

### Filtraggio e sampling

**Filtraggio per livello con `make_filtering_bound_logger()`:**

```python
import logging
import structlog

# Scarta tutti gli eventi sotto WARNING a livello structlog
# (non arrivano nemmeno alla pipeline dei processori)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
    # ...
)
```

**Sampling dei log ad alto volume:**

```python
import random
import structlog

def sample_processor(rate: float):
    """Processore che campiona una percentuale dei log DEBUG/INFO."""
    def processor(logger, method_name, event_dict):
        level = event_dict.get("level", "info")
        if level in ("debug", "info") and random.random() > rate:
            raise structlog.DropEvent
        return event_dict
    return processor

# Campiona il 10% dei log DEBUG/INFO, mantiene tutti WARNING+
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        sample_processor(rate=0.1),
        # ... altri processori
        structlog.processors.JSONRenderer(),
    ],
    # ...
)
```

### Logging Asincrono — QueueHandler e QueueListener

In applicazioni async (FastAPI, Starlette, aiohttp), le operazioni di I/O nel logging — scrittura su file, invio su rete, rotazione file — possono bloccare l'event loop. Il pattern `QueueHandler` + `QueueListener` della stdlib risolve questo problema disaccoppiando l'emissione del log dalla sua elaborazione.

**Il problema:** un handler come `RotatingFileHandler` esegue I/O sincrono durante `emit()`. Se invocato dall'event loop di asyncio, blocca tutte le coroutine in attesa fino al completamento della scrittura su disco.

**La soluzione:** `QueueHandler` inserisce il `LogRecord` in una `queue.Queue` (operazione non bloccante), e `QueueListener` in un thread separato estrae i record dalla coda e li passa agli handler reali:

```python
import logging
import logging.handlers
import queue

def configura_logging_asincrono(
    percorso_log: str = "app.log",
    livello: int = logging.INFO,
) -> logging.handlers.QueueListener:
    """Configura logging non-bloccante con QueueHandler + QueueListener."""

    # Coda condivisa tra handler e listener
    coda_log: queue.Queue[logging.LogRecord] = queue.Queue(maxsize=10_000)

    # Handler reali che fanno I/O — eseguiti nel thread del listener
    handler_file = logging.handlers.RotatingFileHandler(
        percorso_log,
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler_console = logging.StreamHandler()

    # Formatter condiviso
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler_file.setFormatter(formatter)
    handler_console.setFormatter(formatter)

    # QueueHandler: l'unico handler sul logger root
    handler_coda = logging.handlers.QueueHandler(coda_log)

    root_logger = logging.getLogger()
    root_logger.setLevel(livello)
    root_logger.addHandler(handler_coda)

    # QueueListener: thread dedicato che consuma la coda
    listener = logging.handlers.QueueListener(
        coda_log,
        handler_file,
        handler_console,
        respect_handler_level=True,
    )
    listener.start()
    return listener


# --- Lifecycle in FastAPI ---
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    listener = configura_logging_asincrono()
    yield
    listener.stop()  # Svuota la coda e ferma il thread

app = FastAPI(lifespan=lifespan)
```

**Integrazione con structlog e ProcessorFormatter:**

Quando si usa structlog con stdlib, `QueueHandler` si inserisce naturalmente nella pipeline. structlog processa l'evento fino a `wrap_for_formatter`, poi `QueueHandler` lo accoda, e infine `QueueListener` lo passa all'handler con il `ProcessorFormatter`:

```python
import logging
import logging.handlers
import queue
import structlog

def configura_structlog_async(
    percorso_log: str = "app.jsonl",
) -> logging.handlers.QueueListener:
    """Pipeline completa: structlog → stdlib → QueueHandler → QueueListener."""

    # 1. Pipeline structlog (eseguita nel thread chiamante — leggera)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    # 2. Formatter structlog per gli handler reali
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    # 3. Handler reali con formatter structlog
    handler_file = logging.handlers.RotatingFileHandler(
        percorso_log, maxBytes=50_000_000, backupCount=5,
    )
    handler_file.setFormatter(formatter)

    # 4. Coda + QueueHandler + QueueListener
    coda: queue.Queue = queue.Queue(maxsize=10_000)
    handler_coda = logging.handlers.QueueHandler(coda)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler_coda)
    root.setLevel(logging.DEBUG)

    listener = logging.handlers.QueueListener(
        coda, handler_file, respect_handler_level=True,
    )
    listener.start()
    return listener
```

> **Approfondimento:** `QueueHandler` e `QueueListener` sono nella stdlib da Python 3.2, ma rimangono sotto-utilizzati. La coda ha una dimensione massima configurabile (`maxsize`): se la coda si riempie e i consumer non riescono a tenere il passo, `QueueHandler.emit()` blocca fino a che non si libera spazio. In scenari ad altissimo throughput, si puo usare `queue.SimpleQueue` (senza limite di dimensione, lock-free per `put()`) o impostare `maxsize=0` per coda illimitata — a rischio di consumo di memoria. Riferimento: [Python docs — logging.handlers.QueueHandler](https://docs.python.org/3/library/logging.handlers.html#queuehandler).

> **Errore comune:** Non chiamare `listener.stop()` allo shutdown. Senza `stop()`, i log nella coda vengono persi e il thread del listener rimane attivo come thread non-daemon, impedendo la terminazione pulita del processo. Usare sempre `atexit.register(listener.stop)` o il pattern `lifespan` di FastAPI.

---

## Correlation ID con contextvars e structlog

### Pattern contextvars nativo

`contextvars` (PEP 567, stdlib da Python 3.7) fornisce variabili di contesto thread-safe e async-safe. Ogni coroutine asyncio riceve automaticamente una copia del contesto del padre, rendendo `contextvars` il meccanismo ideale per propagare metadata come correlation ID, request ID e tenant ID attraverso l'intera catena di chiamate.

```python
import contextvars
import uuid

# Definizione delle variabili di contesto
correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
tenant_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_id", default=None
)


def genera_correlation_id() -> str:
    """Genera e imposta un nuovo correlation ID."""
    cid = str(uuid.uuid4())
    correlation_id_ctx.set(cid)
    return cid
```

**Integrazione con `structlog.contextvars`:**

structlog offre un modulo `contextvars` dedicato che automatizza il pattern: `bind_contextvars()` e `unbind_contextvars()` impostano variabili che `merge_contextvars` (processore) inietta automaticamente in ogni log event.

```python
import structlog

# All'inizio della richiesta (nel middleware):
structlog.contextvars.clear_contextvars()
structlog.contextvars.bind_contextvars(
    correlation_id=str(uuid.uuid4()),
    request_id=str(uuid.uuid4()),
    tenant_id="TENANT-42",
    metodo="POST",
    percorso="/api/ordini",
)

# In QUALSIASI punto del codice chiamato da questa richiesta:
log = structlog.get_logger()
log.info("elaborazione_ordine", ordine_id="ORD-123")
# Output include automaticamente correlation_id, request_id, tenant_id, metodo, percorso

# Alla fine della richiesta:
structlog.contextvars.unbind_contextvars("metodo", "percorso")
```

### Middleware ASGI/WSGI

**Middleware ASGI per FastAPI/Starlette:**

```python
import uuid
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware che imposta correlation ID e logga richiesta/risposta."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Pulisci contesto dalla richiesta precedente (riuso worker)
        structlog.contextvars.clear_contextvars()

        # Propaga o genera correlation ID
        correlation_id = request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())
        )

        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=str(uuid.uuid4()),
            http_method=request.method,
            http_path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
        )

        log.info("request_started")

        inizio = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("request_failed")
            raise
        else:
            durata_ms = (time.perf_counter() - inizio) * 1000
            log.info(
                "request_completed",
                http_status=response.status_code,
                duration_ms=round(durata_ms, 2),
            )
            response.headers["X-Correlation-ID"] = correlation_id
            return response


# Registrazione in FastAPI:
# app.add_middleware(CorrelationMiddleware)
```

**Middleware WSGI per Flask:**

```python
import uuid
import time
import structlog
from flask import Flask, request, g

log = structlog.get_logger()


def init_correlation_logging(app: Flask) -> None:
    """Registra hook before/after request per correlation ID."""

    @app.before_request
    def imposta_contesto():
        structlog.contextvars.clear_contextvars()
        g.correlation_id = request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())
        )
        g.request_start = time.perf_counter()

        structlog.contextvars.bind_contextvars(
            correlation_id=g.correlation_id,
            http_method=request.method,
            http_path=request.path,
        )
        log.info("request_started")

    @app.after_request
    def logga_risposta(response):
        durata_ms = (time.perf_counter() - g.request_start) * 1000
        log.info(
            "request_completed",
            http_status=response.status_code,
            duration_ms=round(durata_ms, 2),
        )
        response.headers["X-Correlation-ID"] = g.correlation_id
        return response
```

### Propagazione ad asyncio task figli

`contextvars` si propaga automaticamente ai task creati con `asyncio.create_task()` e `asyncio.TaskGroup`. Tuttavia, `contextvars.copy_context().run()` e necessario per thread o executor.

```python
import asyncio
import structlog
from concurrent.futures import ThreadPoolExecutor

log = structlog.get_logger()


async def gestisci_ordine(ordine_id: str) -> None:
    """I task figli ereditano il contesto (correlation_id incluso)."""
    structlog.contextvars.bind_contextvars(ordine_id=ordine_id)

    # TaskGroup: i task figli vedono correlation_id + ordine_id
    async with asyncio.TaskGroup() as tg:
        tg.create_task(valida_pagamento(ordine_id))
        tg.create_task(verifica_inventario(ordine_id))
        tg.create_task(notifica_magazzino(ordine_id))


async def valida_pagamento(ordine_id: str) -> None:
    # correlation_id e ordine_id sono disponibili automaticamente
    log.info("pagamento_validazione_iniziata")
    await asyncio.sleep(0.1)
    log.info("pagamento_validato")


# Per thread pool: serve copy_context()
async def operazione_con_thread() -> None:
    import contextvars
    ctx = contextvars.copy_context()
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=4) as pool:
        # ctx.run() garantisce che il thread veda lo stesso contesto
        risultato = await loop.run_in_executor(
            pool,
            ctx.run,
            operazione_cpu_intensiva,
        )
    log.info("thread_completato", risultato=risultato)


def operazione_cpu_intensiva():
    log = structlog.get_logger()
    # correlation_id e disponibile grazie a ctx.run()
    log.info("elaborazione_cpu_in_corso")
    return 42
```

> **Errore comune:** Usare `loop.run_in_executor(pool, func)` senza `copy_context().run()` perde il contesto delle `contextvars` nel thread. Il thread vedra i valori di default, non quelli impostati nella coroutine chiamante.

---

## OTel Log Bridge — Correlazione Trace-Log

OpenTelemetry Logs segue un modello a **bridge**: non sostituisce la libreria di logging dell'applicazione, ma si collega ad essa per raccogliere i log events e arricchirli con `trace_id` e `span_id` dal contesto di tracing corrente. Questo crea la correlazione automatica tra traces e logs, permettendo di passare da un trace in Jaeger/Tempo direttamente ai log correlati in Loki/Elasticsearch.

Riferimento: [OpenTelemetry Logs specification](https://opentelemetry.io/docs/specs/otel/logs/) — consultato 2026-05-23.

### Architettura del bridge

```
  structlog.get_logger()
       │
       ▼
  Processor chain
  (merge_contextvars, add_level, timestamp, ...)
       │
       ▼
  ProcessorFormatter.wrap_for_formatter
       │
       ▼
  stdlib logging.Logger
       │
       ├──→ StreamHandler (console/file)
       │
       └──→ opentelemetry.sdk._logs.LoggingHandler
                    │
                    ▼
              LoggerProvider
              (con trace_id/span_id dal contesto OTel corrente)
                    │
                    ▼
              OTLPLogExporter → OTel Collector → Loki/Elasticsearch/...
```

### Setup LoggerProvider e OTLP exporter

```python
# pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource

# Risorsa che identifica il servizio
resource = Resource.create({
    "service.name": "ordini-api",
    "service.version": "1.2.3",
    "deployment.environment": "production",
})

# LoggerProvider con exporter OTLP
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(
        OTLPLogExporter(
            endpoint="http://otel-collector:4317",
            insecure=True,
        ),
        max_queue_size=2048,
        max_export_batch_size=512,
        schedule_delay_millis=5000,
    )
)

# Handler stdlib che invia i log a OTel
otel_handler = LoggingHandler(
    level=logging.INFO,
    logger_provider=logger_provider,
)
```

### Integrazione structlog → stdlib → OTel

La configurazione completa che unisce structlog, stdlib e OTel in un'unica pipeline:

```python
import logging
import structlog
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource


def configura_logging(
    service_name: str,
    otel_endpoint: str = "http://localhost:4317",
    livello: int = logging.INFO,
    ambiente: str = "development",
) -> None:
    """Configura la pipeline completa: structlog → stdlib → OTel + console."""

    # --- OTel LoggerProvider ---
    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": ambiente,
    })
    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=otel_endpoint, insecure=True)
        )
    )

    # --- Processori condivisi ---
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # --- structlog → stdlib ---
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # --- Formatter per output leggibile o JSON ---
    if ambiente == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # --- Handler console ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # --- Handler OTel ---
    otel_handler = LoggingHandler(
        level=livello,
        logger_provider=log_provider,
    )

    # --- Root logger ---
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(otel_handler)
    root.setLevel(livello)


# Utilizzo all'avvio dell'applicazione:
configura_logging(
    service_name="ordini-api",
    otel_endpoint="http://otel-collector:4317",
    livello=logging.INFO,
    ambiente="production",
)
```

### Correlazione trace_id e span_id

Quando OTel tracing e attivo, il `LoggingHandler` arricchisce automaticamente ogni `LogRecord` con `trace_id`, `span_id` e `trace_flags` dal contesto corrente. Questo significa che un log emesso all'interno di uno span OTel viene correlato automaticamente.

```python
from opentelemetry import trace
import structlog

tracer = trace.get_tracer("ordini-api")
log = structlog.get_logger()


async def processa_ordine(ordine_id: str) -> dict:
    with tracer.start_as_current_span("processa_ordine") as span:
        span.set_attribute("ordine.id", ordine_id)

        # Questo log viene automaticamente correlato allo span
        log.info("elaborazione_ordine", ordine_id=ordine_id)

        with tracer.start_as_current_span("valida_pagamento"):
            log.info("pagamento_in_validazione")
            # trace_id e lo stesso, span_id e diverso
            risultato = await gateway_pagamento.valida(ordine_id)

        log.info("ordine_completato", risultato=risultato)
        return risultato
```

In Grafana, cio permette di:
1. Aprire un trace in Tempo e vedere gli span
2. Cliccare su uno span e vedere i log correlati in Loki
3. Da un log in Loki, seguire il `trace_id` per aprire il trace completo

> **Approfondimento:** Il `LoggingHandler` di OTel SDK inietta `otelTraceID`, `otelSpanID` e `otelTraceSampled` nel `LogRecord` stdlib. Se si vuole includerli anche nell'output JSON di structlog, si puo aggiungere un processore custom:
>
> ```python
> def aggiungi_otel_context(logger, method_name, event_dict):
>     record = event_dict.get("_record")
>     if record:
>         trace_id = getattr(record, "otelTraceID", "")
>         span_id = getattr(record, "otelSpanID", "")
>         if trace_id:
>             event_dict["trace_id"] = trace_id
>             event_dict["span_id"] = span_id
>     return event_dict
> ```

> **Caso reale:** La correlazione trace-log e stata determinante nell'indagine dell'outage di Cloudflare di ottobre 2024: i team hanno usato i log correlati ai trace per identificare che un singolo deployment aveva introdotto un loop infinito in un percorso di codice critico. Senza la correlazione, avrebbero dovuto correlare manualmente timestamp e request ID — un processo che avrebbe richiesto ore invece di minuti.

---

## Error Handling in FastAPI e Django

Le applicazioni web richiedono strategie di error handling specifiche: tradurre le eccezioni in risposte HTTP appropriate, loggare il contesto della richiesta, e presentare errori user-friendly senza esporre dettagli interni.

### FastAPI — Exception Handler e Middleware

FastAPI (basato su Starlette) offre un sistema di exception handler registrabili che intercettano le eccezioni prima che raggiungano il client.

**Registrazione di handler personalizzati:**

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import structlog

app = FastAPI()
log = structlog.get_logger()


@app.exception_handler(RequestValidationError)
async def handler_validazione(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    """Errori di validazione Pydantic → risposta 422 strutturata."""
    errori = []
    for err in exc.errors():
        errori.append({
            "campo": " → ".join(str(loc) for loc in err["loc"]),
            "messaggio": err["msg"],
            "tipo": err["type"],
        })
    log.warning(
        "validazione_fallita",
        path=str(request.url),
        method=request.method,
        errori=errori,
    )
    return JSONResponse(
        status_code=422,
        content={"errore": "Dati non validi", "dettagli": errori},
    )


@app.exception_handler(HTTPException)
async def handler_http(
    request: Request, exc: HTTPException,
) -> JSONResponse:
    """HTTPException → risposta JSON uniforme."""
    log.info(
        "http_exception",
        status=exc.status_code,
        detail=exc.detail,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"errore": exc.detail},
        headers=exc.headers,
    )
```

**Middleware per eccezioni non gestite:**

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import sentry_sdk

class MiddlewareErroriGlobali(BaseHTTPMiddleware):
    """Cattura eccezioni non gestite, logga e restituisce 500 generico."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            log.error(
                "eccezione_non_gestita",
                exc_type=type(exc).__name__,
                exc_msg=str(exc),
                path=str(request.url),
                method=request.method,
            )
            sentry_sdk.capture_exception(exc)
            return JSONResponse(
                status_code=500,
                content={"errore": "Errore interno del server"},
            )

app.add_middleware(MiddlewareErroriGlobali)
```

**Integrazione con le gerarchie DDD:**

Collegando il middleware agli errori di dominio definiti in precedenza:

```python
from eccezioni_dominio import (
    ErroreDominio,
    ErroreInfrastruttura,
    traduci_eccezione_http,
)

@app.exception_handler(ErroreDominio)
async def handler_errore_dominio(
    request: Request, exc: ErroreDominio,
) -> JSONResponse:
    """Mappa errori di dominio → risposte HTTP via mappa centralizzata."""
    codice_http, mostra_dettagli = traduci_eccezione_http(exc)
    dettaglio = exc.messaggio if mostra_dettagli else "Errore nell'operazione"
    log.warning(
        "errore_dominio",
        tipo=type(exc).__name__,
        codice=exc.codice.value if hasattr(exc, "codice") else None,
        messaggio=exc.messaggio,
        http_status=codice_http,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=codice_http,
        content={
            "errore": dettaglio,
            "codice": exc.codice.value if hasattr(exc, "codice") else "ERRORE",
        },
    )


@app.exception_handler(ErroreInfrastruttura)
async def handler_errore_infrastruttura(
    request: Request, exc: ErroreInfrastruttura,
) -> JSONResponse:
    """Errori infrastrutturali → 503 generico, dettagli solo nei log."""
    codice_http, _ = traduci_eccezione_http(exc)
    log.error(
        "errore_infrastruttura",
        tipo=type(exc).__name__,
        servizio=exc.servizio if hasattr(exc, "servizio") else None,
        messaggio=exc.messaggio,
        path=str(request.url),
    )
    return JSONResponse(
        status_code=codice_http,
        content={"errore": "Servizio temporaneamente non disponibile"},
    )
```

### Django — Middleware e DRF Exception Handler

Django usa un sistema di middleware a strati (onion model). Il metodo `process_exception()` intercetta le eccezioni non gestite nelle view.

**Middleware di error handling per Django:**

```python
# middleware/error_handling.py
import logging
import traceback
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger("django.errors")


class ErrorHandlingMiddleware:
    """Middleware che cattura eccezioni non gestite e le converte in JSON."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Invocato per ogni eccezione non gestita dalla view."""
        logger.error(
            "Eccezione non gestita in %s %s: %s",
            request.method,
            request.path,
            exception,
            exc_info=True,
            extra={
                "request_path": request.path,
                "request_method": request.method,
                "user_id": getattr(request.user, "pk", None),
            },
        )

        if settings.DEBUG:
            return JsonResponse(
                {
                    "errore": str(exception),
                    "tipo": type(exception).__name__,
                    "traceback": traceback.format_exc(),
                },
                status=500,
            )

        return JsonResponse(
            {"errore": "Errore interno del server"},
            status=500,
        )
```

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ... altri middleware ...
    "middleware.error_handling.ErrorHandlingMiddleware",  # ultimo della catena
]
```

**Django REST Framework — Exception handler custom:**

DRF permette di sovrascrivere il suo exception handler globale per uniformare il formato di risposta:

```python
# exceptions.py
from rest_framework.views import exception_handler as drf_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger("api.errors")


def handler_eccezioni_api(exc, context):
    """Exception handler custom per DRF con formato risposta uniforme."""
    # Prima, gestire le eccezioni che DRF gia conosce
    response = drf_handler(exc, context)

    if response is not None:
        # DRF ha gestito l'eccezione (ValidationError, PermissionDenied, etc.)
        response.data = {
            "errore": True,
            "codice": response.status_code,
            "dettagli": response.data,
        }
        return response

    # Eccezioni non gestite da DRF → 500
    view = context.get("view")
    logger.error(
        "Eccezione non gestita nella view %s: %s",
        view.__class__.__name__ if view else "sconosciuta",
        exc,
        exc_info=True,
    )

    return Response(
        {"errore": True, "codice": 500, "dettagli": "Errore interno"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
```

```python
# settings.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "exceptions.handler_eccezioni_api",
}
```

> **Approfondimento:** In FastAPI, l'ordine degli exception handler importa: handler piu specifici (es. `ErroreDominio`) devono essere registrati prima di quelli generici. Se si registra un handler per `Exception` prima di `ErroreDominio`, l'handler generico cattura tutto e quelli specifici non vengono mai invocati. Django DRF inverte la logica: `exception_handler` riceve tutte le eccezioni e la funzione custom decide come gestirle con `isinstance()`. Riferimento: [FastAPI — Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [DRF — Exceptions](https://www.django-rest-framework.org/api-guide/exceptions/).

> **Errore comune:** Esporre traceback e dettagli interni (nomi di tabelle, query SQL, percorsi del filesystem) nelle risposte di errore in produzione. Usare sempre `DEBUG=False` in Django e non includere `str(exception)` nelle risposte JSON a meno che l'eccezione sia stata progettata per essere user-facing (come gli errori di dominio con `mostra_dettagli=True`).

---

## Pattern Avanzati

### Retry Pattern

Il retry pattern implementa la ripetizione automatica di operazioni che possono fallire per cause transitorie.

**Decoratore retry semplice:**

```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry(
    max_tentativi: int = 3,
    attesa_base: float = 1.0,
    backoff_fattore: float = 2.0,
    eccezioni: tuple = (Exception,)
):
    """Decoratore che ripete l'esecuzione in caso di eccezione."""
    def decoratore(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_errore = None
            for tentativo in range(1, max_tentativi + 1):
                try:
                    return func(*args, **kwargs)
                except eccezioni as e:
                    ultimo_errore = e
                    if tentativo < max_tentativi:
                        attesa = attesa_base * (backoff_fattore ** (tentativo - 1))
                        logger.warning(
                            f"{func.__name__}: tentativo {tentativo}/{max_tentativi} "
                            f"fallito ({e}). Riprovo tra {attesa:.1f}s"
                        )
                        time.sleep(attesa)
                    else:
                        logger.error(
                            f"{func.__name__}: tutti i {max_tentativi} "
                            f"tentativi esauriti"
                        )
            raise ultimo_errore
        return wrapper
    return decoratore


@retry(max_tentativi=3, eccezioni=(ConnectionError, TimeoutError))
def chiama_api_esterna(url: str) -> dict:
    risposta = requests.get(url, timeout=10)
    risposta.raise_for_status()
    return risposta.json()
```

**Libreria `tenacity` — retry avanzato e configurabile:**

```python
# pip install tenacity
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_random,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),                        # Max 5 tentativi
    wait=wait_exponential(multiplier=1, min=1, max=60),# Backoff esponenziale
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.DEBUG),
)
def connetti_servizio(host: str, porta: int):
    """Connessione con retry automatico e backoff esponenziale."""
    return crea_connessione(host, porta)

# Combinare condizioni di stop
@retry(
    stop=(stop_after_attempt(10) | stop_after_delay(300)),  # 10 tentativi O 5 min
    wait=wait_exponential(multiplier=1, min=2, max=30) + wait_random(0, 2),
    retry=retry_if_exception_type(ConnectionError),
)
def operazione_resiliente():
    pass
```

### Retry Budget

Il retry budget limita il numero totale di retry che un servizio puo eseguire in una finestra temporale, indipendentemente dal numero di chiamate. Questo previene cascate di retry che possono amplificare un problema.

```python
import time
import threading
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RetryBudget:
    """Budget di retry: limita il numero totale di retry in una finestra temporale.

    Quando il budget e esaurito, le operazioni fallite vengono propagate
    immediatamente senza tentare retry, evitando di sovraccaricare
    un servizio gia in difficolta.

    Riferimento: pattern descritto in "Site Reliability Engineering" (Google),
    capitolo 22 — "Addressing Cascading Failures".
    """

    def __init__(
        self,
        max_retry_ratio: float = 0.1,
        finestra_secondi: float = 60.0,
        min_richieste: int = 20,
    ):
        self.max_retry_ratio = max_retry_ratio
        self.finestra_secondi = finestra_secondi
        self.min_richieste = min_richieste
        self._richieste: list[float] = []
        self._retry: list[float] = []
        self._lock = threading.Lock()

    def _pulisci(self, adesso: float) -> None:
        limite = adesso - self.finestra_secondi
        self._richieste = [t for t in self._richieste if t > limite]
        self._retry = [t for t in self._retry if t > limite]

    def puo_riprovare(self) -> bool:
        """Verifica se il budget consente un retry."""
        adesso = time.monotonic()
        with self._lock:
            self._pulisci(adesso)
            totale = len(self._richieste)
            if totale < self.min_richieste:
                return True
            ratio = len(self._retry) / totale if totale > 0 else 0
            return ratio < self.max_retry_ratio

    def registra_richiesta(self) -> None:
        adesso = time.monotonic()
        with self._lock:
            self._richieste.append(adesso)

    def registra_retry(self) -> None:
        adesso = time.monotonic()
        with self._lock:
            self._retry.append(adesso)


# Budget condiviso per servizio
budget_pagamenti = RetryBudget(max_retry_ratio=0.1, finestra_secondi=60)


def retry_con_budget(budget: RetryBudget, max_tentativi: int = 3):
    """Decoratore retry che rispetta un budget globale."""
    def decoratore(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            budget.registra_richiesta()
            ultimo_errore = None
            for tentativo in range(max_tentativi):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ultimo_errore = e
                    if tentativo < max_tentativi - 1 and budget.puo_riprovare():
                        budget.registra_retry()
                        logger.warning(
                            "%s: retry %d/%d (budget ok)",
                            func.__name__, tentativo + 1, max_tentativi,
                        )
                        time.sleep(2 ** tentativo)
                    else:
                        if not budget.puo_riprovare():
                            logger.error(
                                "%s: retry budget esaurito, propagazione immediata",
                                func.__name__,
                            )
                        break
            raise ultimo_errore
        return wrapper
    return decoratore
```

**Circuit Breaker — evitare di sovraccaricare un servizio gia in difficolta:**

```python
import time
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class StatoCircuito(Enum):
    CHIUSO = "chiuso"          # Funzionamento normale
    APERTO = "aperto"          # Blocca tutte le richieste
    SEMI_APERTO = "semi_aperto"  # Permette una richiesta di test

class CircuitBreaker:
    def __init__(
        self,
        soglia_fallimenti: int = 5,
        timeout_reset: float = 60.0,
        eccezioni_monitorate: tuple = (Exception,)
    ):
        self.soglia_fallimenti = soglia_fallimenti
        self.timeout_reset = timeout_reset
        self.eccezioni_monitorate = eccezioni_monitorate
        self.stato = StatoCircuito.CHIUSO
        self.conteggio_fallimenti = 0
        self.ultimo_fallimento = None

    def __call__(self, func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.stato == StatoCircuito.APERTO:
                if time.time() - self.ultimo_fallimento >= self.timeout_reset:
                    self.stato = StatoCircuito.SEMI_APERTO
                    logger.info(f"Circuit breaker per {func.__name__}: SEMI_APERTO")
                else:
                    raise RuntimeError(
                        f"Circuit breaker APERTO per {func.__name__}"
                    )

            try:
                risultato = func(*args, **kwargs)
                if self.stato == StatoCircuito.SEMI_APERTO:
                    self.stato = StatoCircuito.CHIUSO
                    self.conteggio_fallimenti = 0
                    logger.info(f"Circuit breaker per {func.__name__}: CHIUSO")
                return risultato
            except self.eccezioni_monitorate as e:
                self.conteggio_fallimenti += 1
                self.ultimo_fallimento = time.time()
                if self.conteggio_fallimenti >= self.soglia_fallimenti:
                    self.stato = StatoCircuito.APERTO
                    logger.error(
                        f"Circuit breaker per {func.__name__}: APERTO "
                        f"dopo {self.conteggio_fallimenti} fallimenti"
                    )
                raise
        return wrapper

# Utilizzo
@CircuitBreaker(soglia_fallimenti=3, timeout_reset=30)
def chiama_servizio_pagamento(importo: float):
    return gateway_pagamento.processa(importo)
```

### Graceful Degradation

La degradazione graduale consiste nel continuare a fornire un servizio ridotto quando un componente fallisce, invece di bloccare l'intera applicazione.

**Strategie di fallback:**

```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

def con_fallback(*funzioni):
    """Esegue le funzioni in ordine, restituendo il primo risultato valido."""
    errori = []
    for func in funzioni:
        try:
            return func()
        except Exception as e:
            errori.append((func.__name__, e))
            logger.warning(f"Fallback: {func.__name__} fallito ({e})")
    raise RuntimeError(
        f"Tutti i fallback esauriti: "
        + ", ".join(f"{nome}: {err}" for nome, err in errori)
    )


# Esempio: ottenere dati con cache a piu livelli
def ottieni_profilo_utente(utente_id: str) -> dict:
    return con_fallback(
        lambda: cache_locale.get(f"profilo:{utente_id}"),
        lambda: cache_redis.get(f"profilo:{utente_id}"),
        lambda: database.query_profilo(utente_id),
        lambda: {"utente_id": utente_id, "nome": "Utente", "stato": "sconosciuto"},
    )
```

**Valori di default e feature flag:**

```python
import logging

logger = logging.getLogger(__name__)

class ServizioRaccomandazioni:
    def ottieni_raccomandazioni(self, utente_id: str) -> list[dict]:
        try:
            return self._algoritmo_ml(utente_id)
        except Exception as e:
            logger.error(f"ML fallito per utente {utente_id}: {e}")
            try:
                return self._raccomandazioni_popolari()
            except Exception as e2:
                logger.error(f"Anche le raccomandazioni popolari sono fallite: {e2}")
                return self._raccomandazioni_statiche()

    def _algoritmo_ml(self, utente_id):
        """Raccomandazioni personalizzate via modello ML."""
        return servizio_ml.predici(utente_id)

    def _raccomandazioni_popolari(self):
        """Fallback: prodotti piu venduti."""
        return database.top_prodotti(limite=10)

    def _raccomandazioni_statiche(self):
        """Ultimo fallback: lista statica curata manualmente."""
        return [
            {"id": "PROD-001", "nome": "Prodotto in evidenza"},
            {"id": "PROD-002", "nome": "Bestseller"},
        ]
```

### Error Reporting

**Integrazione con Sentry per il monitoraggio degli errori in produzione:**

```python
# pip install sentry-sdk
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Configurazione iniziale
sentry_sdk.init(
    dsn="https://chiave@sentry.example.com/progetto",
    environment="production",
    release="mia-app@1.2.3",
    traces_sample_rate=0.1,   # Campiona il 10% delle transazioni
    integrations=[
        LoggingIntegration(
            level=logging.INFO,         # Cattura breadcrumbs da INFO in su
            event_level=logging.ERROR,  # Invia eventi a Sentry da ERROR in su
        ),
    ],
    before_send=filtra_eventi_sentry,
)

def filtra_eventi_sentry(evento, hint):
    """Filtra eventi prima dell'invio a Sentry."""
    # Non inviare errori di connessione transitori
    if "exc_info" in hint:
        tipo_eccezione = hint["exc_info"][0]
        if tipo_eccezione in (ConnectionError, TimeoutError):
            return None
    return evento


# Utilizzo: gli errori vengono catturati automaticamente
# Ma si possono aggiungere informazioni contestuali:
def processa_ordine(ordine_id: str, utente_id: str):
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("tipo_operazione", "ordine")
        scope.set_user({"id": utente_id})
        scope.set_extra("ordine_id", ordine_id)
        try:
            # ... logica ordine
            pass
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise
```

**Aggregazione errori e configurazione alert:**

```python
import logging
from collections import Counter
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class AggregatorErrori:
    """Aggrega errori e notifica quando una soglia viene superata."""

    def __init__(self, soglia: int = 10, finestra_minuti: int = 5):
        self.soglia = soglia
        self.finestra = timedelta(minutes=finestra_minuti)
        self.errori: list[tuple[datetime, str]] = []
        self.lock = threading.Lock()

    def registra(self, tipo_errore: str) -> None:
        adesso = datetime.now()
        with self.lock:
            self.errori.append((adesso, tipo_errore))
            # Rimuovi errori fuori dalla finestra temporale
            limite = adesso - self.finestra
            self.errori = [(t, e) for t, e in self.errori if t > limite]

            conteggio = Counter(e for _, e in self.errori)
            for tipo, n in conteggio.items():
                if n >= self.soglia:
                    self._invia_alert(tipo, n)

    def _invia_alert(self, tipo_errore: str, conteggio: int):
        logger.critical(
            f"ALERT: {conteggio} errori di tipo '{tipo_errore}' "
            f"negli ultimi {self.finestra.total_seconds() / 60:.0f} minuti"
        )
        # Qui si invierebbe una notifica (email, Slack, PagerDuty, ecc.)

aggregatore = AggregatorErrori(soglia=10, finestra_minuti=5)
```

> **Caso reale:** Sentry ha rilevato che il 70% degli errori non catturati in produzione proviene da eccezioni non gestite in background task (Celery, RQ, asyncio). Integrare `sentry_sdk` con queste piattaforme richiede l'uso delle integration specifiche: `CeleryIntegration`, `RqIntegration`, `AsyncioIntegration`. Riferimento: [Sentry Python SDK — Integrations](https://docs.sentry.io/platforms/python/integrations/), consultato 2026-05-23.

#### Breadcrumbs manuali e contesto strutturato

Sentry cattura automaticamente i breadcrumbs da log, richieste HTTP e query DB. Tuttavia, per tracciare il percorso logico specifico dell'applicazione, i breadcrumbs manuali forniscono contesto che le integrazioni automatiche non possono dedurre:

```python
import sentry_sdk

def processa_checkout(carrello_id: str, utente_id: str) -> dict:
    """Pipeline di checkout con breadcrumbs manuali per debugging."""

    sentry_sdk.add_breadcrumb(
        category="checkout",
        message=f"Inizio checkout per carrello {carrello_id}",
        level="info",
        data={"carrello_id": carrello_id, "utente_id": utente_id},
    )

    # Validazione carrello
    carrello = carica_carrello(carrello_id)
    sentry_sdk.add_breadcrumb(
        category="checkout.validazione",
        message="Carrello caricato e validato",
        level="info",
        data={
            "num_articoli": len(carrello.articoli),
            "totale": str(carrello.totale),
        },
    )

    # Tentativo pagamento
    try:
        risultato = gateway_pagamento.addebita(carrello.totale)
        sentry_sdk.add_breadcrumb(
            category="checkout.pagamento",
            message="Pagamento completato",
            level="info",
            data={"transazione_id": risultato.transazione_id},
        )
    except PaymentError as exc:
        sentry_sdk.add_breadcrumb(
            category="checkout.pagamento",
            message=f"Pagamento fallito: {exc.codice_errore}",
            level="error",
            data={"codice_errore": exc.codice_errore},
        )
        raise

    return {"ordine_id": risultato.ordine_id}
```

Quando un errore viene catturato, Sentry mostra la sequenza completa dei breadcrumbs nell'issue, ricostruendo il percorso che ha portato al fallimento.

**Contesti personalizzati con `set_context()`:**

A differenza dei tag (stringhe brevi, indicizzate, usate per filtrare), i contesti accettano strutture dati arbitrarie e vengono visualizzati nella sezione "Additional Data" dell'issue:

```python
import sentry_sdk

def analizza_documento(doc_id: str, contenuto: bytes) -> dict:
    """Analisi documento con contesto Sentry per debugging."""

    # Contesto strutturato — visibile nell'issue Sentry
    sentry_sdk.set_context("documento", {
        "id": doc_id,
        "dimensione_bytes": len(contenuto),
        "formato": rileva_formato(contenuto),
        "encoding": rileva_encoding(contenuto),
    })

    sentry_sdk.set_context("ambiente_analisi", {
        "parser_versione": PARSER_VERSION,
        "memoria_disponibile_mb": get_memoria_disponibile(),
        "worker_id": os.getenv("WORKER_ID"),
    })

    # Tag per filtraggio rapido nella dashboard
    sentry_sdk.set_tag("formato_documento", rileva_formato(contenuto))
    sentry_sdk.set_tag("dimensione_categoria", classifica_dimensione(len(contenuto)))

    risultato = esegui_analisi(contenuto)
    return risultato
```

#### Transazioni e span personalizzati per performance monitoring

Sentry Performance usa transazioni (unita di lavoro di alto livello) e span (sotto-operazioni) per misurare le prestazioni. Con il Python SDK si possono creare span personalizzati per misurare operazioni specifiche:

```python
import sentry_sdk

def importa_catalogo(file_path: str) -> dict:
    """Importazione catalogo con performance monitoring Sentry."""

    with sentry_sdk.start_transaction(
        op="importazione",
        name="importa_catalogo",
        description=f"Import da {file_path}",
    ) as transaction:
        transaction.set_tag("formato", file_path.rsplit(".", 1)[-1])

        # Span per la fase di lettura
        with sentry_sdk.start_span(
            op="file.read",
            description="Lettura file catalogo",
        ) as span_lettura:
            dati = leggi_file(file_path)
            span_lettura.set_data("righe", len(dati))
            span_lettura.set_data("bytes", os.path.getsize(file_path))

        # Span per la fase di validazione
        with sentry_sdk.start_span(
            op="validazione",
            description="Validazione prodotti",
        ) as span_val:
            validi, invalidi = valida_prodotti(dati)
            span_val.set_data("validi", len(validi))
            span_val.set_data("invalidi", len(invalidi))

        # Span per la fase di persistenza
        with sentry_sdk.start_span(
            op="db.write",
            description="Scrittura nel database",
        ) as span_db:
            risultato = salva_prodotti(validi)
            span_db.set_data("inseriti", risultato["inseriti"])
            span_db.set_data("aggiornati", risultato["aggiornati"])

        transaction.set_data("totale_processati", len(dati))
        return risultato
```

#### Hook before_send e before_breadcrumb

Gli hook `before_send` e `before_breadcrumb` permettono di filtrare, modificare o scartare eventi e breadcrumbs prima dell'invio a Sentry. Sono essenziali per la privacy (rimozione PII) e il controllo del volume:

```python
import sentry_sdk
import re

# Pattern per dati sensibili
PATTERN_PII = re.compile(
    r"(password|token|secret|api_key|authorization|cookie|session_id)"
    r"\s*[=:]\s*\S+",
    re.IGNORECASE,
)


def before_send_sanitizzato(event, hint):
    """Filtra eventi e rimuove PII prima dell'invio."""

    # Scarta errori transitori che non richiedono investigazione
    if "exc_info" in hint:
        tipo_exc = hint["exc_info"][0]
        if tipo_exc in (ConnectionResetError, BrokenPipeError):
            return None

    # Sanitizza i dati nell'evento
    if "request" in event:
        request_data = event["request"]
        # Rimuovi header sensibili
        if "headers" in request_data:
            headers = request_data["headers"]
            for header_sensibile in ("authorization", "cookie", "x-api-key"):
                if header_sensibile in headers:
                    headers[header_sensibile] = "[REDACTED]"
        # Sanitizza query string
        if "query_string" in request_data:
            request_data["query_string"] = PATTERN_PII.sub(
                r"\1=[REDACTED]", request_data["query_string"]
            )

    return event


def before_breadcrumb_filtrato(crumb, hint):
    """Filtra breadcrumbs rumorosi o contenenti PII."""

    # Scarta breadcrumbs da query di health check
    if crumb.get("category") == "query":
        query = crumb.get("data", {}).get("query", "")
        if "health_check" in query or "SELECT 1" in query:
            return None

    # Sanitizza URL nei breadcrumbs HTTP
    if crumb.get("category") == "http":
        url = crumb.get("data", {}).get("url", "")
        crumb["data"]["url"] = PATTERN_PII.sub(r"\1=[REDACTED]", url)

    return crumb


sentry_sdk.init(
    dsn="https://chiave@sentry.example.com/progetto",
    environment="production",
    release="mia-app@1.2.3",
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,   # Profiling (richiede sentry_sdk[profiling])
    before_send=before_send_sanitizzato,
    before_breadcrumb=before_breadcrumb_filtrato,
)
```

> **Approfondimento:** `profiles_sample_rate` abilita il profiling continuo di Sentry, che registra stack trace campionati durante le transazioni. E particolarmente utile per identificare funzioni lente in produzione senza dover riprodurre il problema in locale. Il profiling aggiunge un overhead del 2-5% e va campionato (tipicamente al 10-20% delle transazioni). Richiede l'installazione del pacchetto extra: `pip install sentry-sdk[profiling]`. Riferimento: [Sentry Profiling — Python](https://docs.sentry.io/product/explore/profiling/), consultato 2026-05-23.

> **Errore comune:** Usare `set_tag()` con valori lunghi o strutturati. I tag Sentry sono stringhe brevi indicizzate, usati per filtrare e raggruppare issues. Per dati strutturati (dizionari, liste, valori lunghi), usare `set_context()` che non ha limiti di lunghezza ma non e indicizzato. Mescolare i due causa tag troncati e contesto mancante nella dashboard.

#### Sentry e ExceptionGroup

Sentry SDK 2.x supporta nativamente `ExceptionGroup` di Python 3.11+. Quando un `ExceptionGroup` viene catturato, Sentry crea un issue con tutte le eccezioni contenute visualizzate come sotto-eccezioni nell'interfaccia. Per ottenere il massimo valore, combinare i breadcrumbs manuali con la gestione `except*`:

```python
import asyncio
import sentry_sdk

async def pipeline_con_sentry():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(servizio_a())
            tg.create_task(servizio_b())
    except* ConnectionError as eg:
        for exc in eg.exceptions:
            sentry_sdk.add_breadcrumb(
                category="pipeline.errore_rete",
                message=str(exc),
                level="error",
            )
            sentry_sdk.capture_exception(exc)
    except* ValueError as eg:
        sentry_sdk.set_context("errori_validazione", {
            "count": len(eg.exceptions),
            "dettagli": [str(e) for e in eg.exceptions],
        })
        sentry_sdk.capture_exception(eg)
```

Questo garantisce che ogni tipo di errore venga tracciato separatamente nella dashboard Sentry, con il contesto appropriato per il debugging.

---

## Warnings

Il modulo `warnings` di Python fornisce un meccanismo per segnalare situazioni che non sono errori ma che meritano l'attenzione dello sviluppatore, come l'uso di API deprecate.

```python
import warnings

# Emettere un warning
def funzione_vecchia(x):
    warnings.warn(
        "funzione_vecchia() e deprecata, usa funzione_nuova()",
        DeprecationWarning,
        stacklevel=2   # Il warning punta al chiamante, non a questa riga
    )
    return funzione_nuova(x)

# Categorie di warning
# DeprecationWarning    — funzionalita deprecata (nascosta per default agli utenti)
# FutureWarning         — cambio di comportamento futuro (sempre visibile)
# PendingDeprecationWarning — deprecazione imminente
# RuntimeWarning        — comportamento runtime sospetto
# UserWarning           — warning generico dell'utente
# SyntaxWarning         — sintassi dubbia
# ResourceWarning       — gestione risorse problematica
```

> **Approfondimento:** `DeprecationWarning` e nascosto per default quando il codice chiamante non e `__main__` o un test (Python 3.2+). Questo significa che gli utenti finali non vedono warning di deprecazione delle librerie, ma gli sviluppatori li vedono nei test. Per forzare la visibilita: `python -W default::DeprecationWarning`. Riferimento: [PEP 565 — Show DeprecationWarning in __main__](https://peps.python.org/pep-0565/).

**Controllare il comportamento dei warnings:**

```python
import warnings

# Ignorare tutti i DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Mostrare un warning solo la prima volta
warnings.filterwarnings("once", category=UserWarning)

# Trasformare un warning in errore (utile nei test)
warnings.filterwarnings("error", category=DeprecationWarning)

# Filtrare per modulo o messaggio
warnings.filterwarnings(
    "ignore",
    message=".*deprecata.*",
    module="libreria_vecchia"
)
```

**Convertire warnings in eccezioni nei test:**

```python
import warnings
import pytest

# Con pytest: il flag -W error trasforma i warning in errori
# pytest -W error::DeprecationWarning

# Nel codice:
def test_nessun_warning_deprecazione():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        # Se il codice sotto emette un DeprecationWarning, il test fallisce
        risultato = funzione_da_testare()
```

---

## Debugging

### pdb e breakpoint()

Python include un debugger interattivo integrato, `pdb`, accessibile in modo comodo tramite la funzione built-in `breakpoint()`.

**Inserire un breakpoint nel codice:**

```python
def calcola_sconto(prezzo: float, percentuale: float) -> float:
    sconto = prezzo * percentuale / 100
    breakpoint()  # Il programma si ferma qui
    prezzo_finale = prezzo - sconto
    return prezzo_finale
```

A partire da Python 3.7, `breakpoint()` e l'approccio raccomandato. Equivale a `import pdb; pdb.set_trace()` ma e configurabile tramite la variabile d'ambiente `PYTHONBREAKPOINT`:

```bash
# Disabilitare tutti i breakpoint
PYTHONBREAKPOINT=0 python script.py

# Usare un debugger alternativo
PYTHONBREAKPOINT=ipdb.set_trace python script.py
PYTHONBREAKPOINT=pudb.set_trace python script.py
```

**Comandi principali di pdb:**

| Comando | Abbreviazione | Descrizione                                      |
|---------|---------------|--------------------------------------------------|
| `next`  | `n`           | Esegui la riga corrente (senza entrare nelle funzioni) |
| `step`  | `s`           | Esegui la riga corrente (entra nelle funzioni)   |
| `continue` | `c`        | Continua l'esecuzione fino al prossimo breakpoint |
| `print` | `p`           | Stampa il valore di un'espressione               |
| `list`  | `l`           | Mostra il codice sorgente attorno alla riga corrente |
| `where` | `w`           | Mostra lo stack trace completo                   |
| `break` | `b`           | Imposta un breakpoint (es. `b 42` alla riga 42)  |
| `up`    | `u`           | Sali di un frame nello stack                     |
| `down`  | `d`           | Scendi di un frame nello stack                   |
| `quit`  | `q`           | Esci dal debugger                                |
| `pp`    |               | Pretty-print di un'espressione                   |
| `args`  | `a`           | Mostra gli argomenti della funzione corrente     |

**Sessione pdb tipica:**

```
> /home/utente/progetto/calcoli.py(5)calcola_sconto()
-> prezzo_finale = prezzo - sconto
(Pdb) p prezzo
100.0
(Pdb) p percentuale
15.0
(Pdb) p sconto
15.0
(Pdb) l
  1  def calcola_sconto(prezzo: float, percentuale: float) -> float:
  2      sconto = prezzo * percentuale / 100
  3      breakpoint()
  4  ->  prezzo_finale = prezzo - sconto
  5      return prezzo_finale
(Pdb) n
> /home/utente/progetto/calcoli.py(6)calcola_sconto()
-> return prezzo_finale
(Pdb) p prezzo_finale
85.0
(Pdb) c
```

### Debugging con IDE

**VS Code:**
- Impostare breakpoint cliccando a sinistra del numero di riga
- Configurare `launch.json` per opzioni avanzate
- Pannelli: Variables, Watch, Call Stack, Breakpoints
- Breakpoint condizionali: click destro sul breakpoint e impostare una condizione
- Logpoint: stampa un messaggio senza fermare l'esecuzione

**PyCharm:**
- Breakpoint visivi con click sul margine sinistro
- Valutazione espressioni al volo durante il debug
- Debug di test, applicazioni Django, processi remoti
- Breakpoint condizionali e con log integrati

### Post-mortem Debugging

Analizzare un'eccezione dopo che si e verificata:

```python
import pdb

def funzione_buggy():
    lista = [1, 2, 3]
    return lista[10]  # IndexError

# Metodo 1: try/except con post-mortem
try:
    funzione_buggy()
except Exception:
    pdb.post_mortem()  # Apre pdb nel punto esatto dell'eccezione

# Metodo 2: da linea di comando
# python -m pdb script.py
# Quando si verifica un'eccezione non gestita, pdb si attiva automaticamente
```

### Modulo traceback

Il modulo `traceback` permette di catturare, formattare e manipolare le informazioni di traceback programmaticamente.

```python
import traceback
import logging

logger = logging.getLogger(__name__)

def operazione_rischiosa():
    try:
        risultato = 1 / 0
    except ZeroDivisionError:
        # Ottenere il traceback come stringa
        tb_stringa = traceback.format_exc()
        logger.error(f"Errore catturato:\n{tb_stringa}")

        # Ottenere informazioni strutturate
        import sys
        tipo, valore, tb = sys.exc_info()
        frame_info = traceback.extract_tb(tb)
        for frame in frame_info:
            logger.debug(
                f"  File: {frame.filename}, Riga: {frame.lineno}, "
                f"Funzione: {frame.name}, Codice: {frame.line}"
            )

# Stampare il traceback senza ri-sollevare l'eccezione
def esegui_con_report(funzione, *args):
    try:
        return funzione(*args)
    except Exception:
        traceback.print_exc()
        return None
```

---

## Best Practices

**1. Catturare eccezioni specifiche, mai generiche.**

Non utilizzare mai `except:` senza tipo o `except Exception:` come gestore generico a meno che non si stia ri-sollevando l'eccezione o si sia all'ultimo livello dello stack (entry point dell'applicazione). Catturare eccezioni troppo ampie nasconde bug e rende il debugging impossibile.

```python
# MALE
try:
    elabora_dati(input_utente)
except:
    print("Errore")

# BENE
try:
    elabora_dati(input_utente)
except ValueError as e:
    logger.warning(f"Input non valido: {e}")
except ConnectionError as e:
    logger.error(f"Servizio non raggiungibile: {e}")
```

**2. Usare il blocco `else` per separare il codice protetto da quello conseguente.**

Il codice nella clausola `else` viene eseguito solo se il `try` ha avuto successo, evitando di catturare eccezioni provenienti da codice che non si intendeva proteggere.

```python
try:
    dati = json.loads(payload)
except json.JSONDecodeError:
    logger.error("Payload JSON malformato")
    return errore_400()
else:
    # Questo codice non e protetto dal try/except sopra
    risultato = processa_dati(dati)
    return successo_200(risultato)
```

**3. Loggare le eccezioni con `logger.exception()` o `exc_info=True`.**

Queste opzioni includono automaticamente il traceback completo nel messaggio di log, informazione cruciale per il debugging.

```python
try:
    connessione = database.connetti()
except DatabaseError as e:
    # logger.exception() logga a livello ERROR con traceback
    logger.exception(f"Connessione al database fallita")
    # Equivalente a:
    # logger.error(f"Connessione al database fallita", exc_info=True)
```

**4. Preferire EAFP a LBYL in contesti Pythonic.**

Quando l'operazione ha buone probabilita di successo, il pattern try/except e piu leggibile, piu sicuro rispetto alle race condition e piu performante.

```python
# Pythonic (EAFP)
try:
    valore = dizionario[chiave]
except KeyError:
    valore = calcola_valore_default()
```

**5. Creare eccezioni personalizzate per il dominio applicativo.**

Le eccezioni personalizzate permettono di distinguere gli errori dell'applicazione da quelli generici di Python, rendono il codice piu leggibile e consentono una gestione granulare degli errori.

```python
class ErrorePagamento(ErroreApplicazione):
    def __init__(self, ordine_id: str, motivo: str, codice: str):
        self.ordine_id = ordine_id
        self.codice = codice
        super().__init__(f"Pagamento fallito per ordine {ordine_id}: {motivo}")
```

**6. Usare `logging` con nomi di logger gerarchici, mai `print()` per il monitoraggio.**

Il sistema di logging offre livelli, filtri, handler multipli e formattazione configurabile. I `print()` non offrono nessuno di questi vantaggi e non possono essere disabilitati selettivamente.

```python
# In ogni modulo:
import logging
logger = logging.getLogger(__name__)

# Il nome segue la gerarchia dei package
# mia_app.servizi.pagamento -> eredita la config di mia_app
```

**7. Configurare il logging con `dictConfig()` e differenziare per ambiente.**

Centralizzare la configurazione del logging in un unico punto permette di gestire facilmente i diversi ambienti (sviluppo, staging, produzione) e di modificare il comportamento senza toccare il codice applicativo.

```python
import os
import logging.config

config = carica_config_logging(os.getenv("APP_ENV", "development"))
logging.config.dictConfig(config)
```

**8. Implementare retry con backoff esponenziale per le operazioni di rete.**

Le connessioni di rete sono intrinsecamente inaffidabili. Un retry con backoff esponenziale da tempo al servizio remoto di recuperare senza sovraccaricarlo con richieste ripetute immediate.

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
def chiama_api(endpoint: str) -> dict:
    return requests.get(endpoint, timeout=10).json()
```

**9. Proteggere i dati sensibili nei log e nei messaggi di errore.**

Mai includere password, token, numeri di carta di credito o dati personali nei messaggi di log. Implementare filtri di mascheramento e verificare regolarmente che i log non contengano informazioni sensibili.

```python
# MALE
logger.info(f"Login utente {username} con password {password}")

# BENE
logger.info(f"Login utente {username} completato con successo")
```

**10. Usare `finally` o context manager per garantire la pulizia delle risorse.**

Le risorse (file, connessioni, lock) devono essere sempre rilasciate, indipendentemente dal verificarsi di eccezioni. I context manager (`with`) sono la soluzione piu elegante e sicura; `finally` e l'alternativa quando un context manager non e disponibile.

```python
# Preferire i context manager
with open("dati.txt") as f, connessione_db() as db:
    dati = f.read()
    db.inserisci(dati)
# File e connessione chiusi automaticamente, anche in caso di eccezione
```

---

> **Nota finale:** La gestione degli errori e il logging non sono attivita secondarie da aggiungere a sviluppo completato. Devono essere progettati fin dall'inizio come parte integrante dell'architettura dell'applicazione. Un sistema con una buona gestione degli errori e un logging strutturato e un sistema che puo essere diagnosticato, monitorato e mantenuto nel tempo. Investire in queste pratiche fin dalle prime fasi di sviluppo ripaga enormemente durante la manutenzione e l'operazione in produzione.

---

## Troubleshooting

Problemi comuni e soluzioni durante l'implementazione di error handling e logging.

### structlog non produce output

**Sintomo:** Nessun log appare su console o file nonostante le chiamate a `log.info()`.

**Cause e soluzioni:**

1. **`structlog.configure()` non e stato chiamato.** Senza configurazione esplicita, structlog usa impostazioni di default che potrebbero non avere un renderer configurato. Assicurarsi di chiamare `structlog.configure()` prima di qualsiasi `structlog.get_logger()`.

2. **Livello di filtraggio troppo alto.** Se si usa `make_filtering_bound_logger(logging.WARNING)`, tutti i log INFO e DEBUG vengono scartati silenziosamente. Verificare il livello:
   ```python
   # Temporaneamente per debug:
   structlog.configure(
       wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
   )
   ```

3. **Logger cachato con configurazione precedente.** Se `cache_logger_on_first_use=True` e si cambia la configurazione dopo il primo uso, i logger gia creati non vengono aggiornati. Riavviare il processo o impostare `cache_logger_on_first_use=False` durante lo sviluppo.

### Log duplicati su console

**Sintomo:** Ogni messaggio appare due o piu volte.

**Causa:** Due handler sullo stesso logger stdlib, oppure `propagate=True` (default) che propaga i log dal logger figlio al padre (e al root logger), ognuno con il proprio handler.

**Soluzione:**
```python
# Opzione 1: disabilitare la propagazione
logging.getLogger("mia_app").propagate = False

# Opzione 2: handler solo sul root logger
root = logging.getLogger()
root.handlers.clear()
root.addHandler(handler_unico)
```

### correlation_id assente nei log di thread pool

**Sintomo:** I log emessi da funzioni eseguite in `ThreadPoolExecutor` non contengono il `correlation_id`.

**Causa:** `contextvars` non si propaga automaticamente ai thread. Solo `asyncio.create_task()` e `TaskGroup` propagano il contesto.

**Soluzione:**
```python
import contextvars
import asyncio
from concurrent.futures import ThreadPoolExecutor

ctx = contextvars.copy_context()
loop = asyncio.get_running_loop()
risultato = await loop.run_in_executor(pool, ctx.run, funzione_target)
```

### OTel LoggingHandler non invia log

**Sintomo:** I log appaiono su console ma non arrivano all'OTel Collector.

**Cause:**

1. **Endpoint errato.** Verificare che `OTLPLogExporter(endpoint=...)` punti all'indirizzo corretto del Collector (porta 4317 per gRPC, 4318 per HTTP).

2. **`LoggerProvider` non registrato.** Il `LoggingHandler` deve ricevere un `LoggerProvider` configurato con almeno un processor e un exporter.

3. **`BatchLogRecordProcessor` non ha flushato.** In sviluppo, chiamare `logger_provider.force_flush()` prima di terminare il processo per assicurarsi che i log pending vengano inviati.

4. **Collector non accetta logs.** Verificare che la configurazione del Collector includa `receivers: otlp: protocols: grpc:` e che il pipeline `logs` sia definito.

### Exception in processore structlog silenziosamente ignorata

**Sintomo:** Un processore custom lancia un'eccezione ma non appare alcun messaggio di errore.

**Causa:** Per default, structlog cattura le eccezioni nei processori per evitare che un errore di logging faccia crashare l'applicazione. Il log event viene scartato silenziosamente.

**Soluzione per il debugging:**
```python
# Aggiungere un processore di debug all'inizio della catena
def debug_processor(logger, method_name, event_dict):
    try:
        return event_dict
    except Exception as e:
        import sys
        print(f"ERRORE PROCESSORE: {e}", file=sys.stderr)
        raise
```

### `except*` e `except` mischiati

**Sintomo:** `SyntaxError` quando si usa `except*` insieme a `except` nello stesso blocco `try`.

**Causa:** Python non permette di mischiare `except` tradizionale e `except*` nello stesso `try`. Sono due meccanismi mutuamente esclusivi.

**Soluzione:** Se serve gestire sia eccezioni singole che gruppi, nidificare i blocchi `try`:
```python
try:
    try:
        risultato = operazione_concorrente()
    except* ValueError as eg:
        gestisci_errori_valore(eg)
    except* TypeError as eg:
        gestisci_errori_tipo(eg)
except RuntimeError as e:
    gestisci_errore_runtime(e)
```

---

## Esercizi

### Esercizio 1 — Gerarchia di eccezioni per un e-commerce

Progettare una gerarchia completa di eccezioni personalizzate per un sistema e-commerce che gestisca: ordini, pagamenti, inventario e spedizioni. Ogni eccezione deve includere attributi strutturati (non solo il messaggio stringa). Implementare un handler centralizzato che mappa ogni eccezione a un codice HTTP appropriato.

**Criterio di successo:** La gerarchia ha almeno 3 livelli di profondita, ogni eccezione ha almeno 2 attributi strutturati, e il handler copre almeno 6 eccezioni diverse.

### Esercizio 2 — Pipeline structlog con processori custom

Configurare una pipeline structlog completa con:
- Un processore custom che aggiunge l'hash del commit Git corrente a ogni log
- Un processore di censura che maschera qualsiasi valore associato a chiavi come `password`, `token`, `secret`, `authorization`
- Output JSON in produzione, output colorato in sviluppo
- Integrazione con stdlib `logging` via `ProcessorFormatter`

Scrivere un test che verifica che i campi sensibili vengono mascherati e che l'hash del commit appare nei log JSON.

**Criterio di successo:** I test passano, i campi sensibili sono censurati, l'output cambia formato in base alla variabile `APP_ENV`.

### Esercizio 3 — Correlation ID end-to-end con FastAPI

Implementare un middleware FastAPI che:
1. Legge `X-Correlation-ID` dall'header della richiesta, o ne genera uno nuovo
2. Lo propaga a tutti i log via `structlog.contextvars.bind_contextvars()`
3. Lo propaga a chiamate HTTP in uscita (via header)
4. Lo include nell'header della risposta
5. Verificare che funziona con `asyncio.TaskGroup` (i task figli vedono lo stesso ID)

Scrivere un test E2E con `httpx.AsyncClient` che verifica la propagazione.

**Criterio di successo:** Tutti i log di una richiesta condividono lo stesso `correlation_id`, inclusi quelli emessi da task figli.

### Esercizio 4 — OTel log bridge + trace correlation

Configurare l'integrazione completa structlog + stdlib + OTel:
1. Setup `LoggerProvider` con `OTLPLogExporter` (puo puntare a un Collector locale o a `ConsoleLogExporter` per test)
2. Creare uno span OTel e verificare che i log emessi all'interno dello span contengono `trace_id` e `span_id`
3. Verificare che i log fuori da uno span attivo non contengono trace context

Usare `docker compose` con OTel Collector + Grafana Loki per visualizzare la correlazione.

**Criterio di successo:** In Grafana, navigare da un trace ai log correlati e viceversa.

### Esercizio 5 — Circuit breaker + retry budget

Implementare un client HTTP resiliente che combina:
1. Retry con backoff esponenziale e jitter (tenacity)
2. Circuit breaker con 3 stati (chiuso/aperto/semi-aperto)
3. Retry budget globale (max 10% delle richieste in una finestra di 60 secondi)
4. Logging strutturato di ogni transizione di stato e decisione di retry/stop

Scrivere un test con `responses` o `respx` che simula fallimenti intermittenti e verifica il comportamento del circuit breaker.

**Criterio di successo:** Il circuit breaker si apre dopo N fallimenti consecutivi, il retry budget impedisce cascade di retry, i test coprono tutti e 3 gli stati.

### Esercizio 6 — ExceptionGroup per validazione multi-campo

Implementare un validatore di form che:
1. Raccoglie tutti gli errori di validazione (non si ferma al primo)
2. Solleva un `ExceptionGroup` con tutti gli errori trovati
3. Il chiamante usa `except*` per gestire separatamente errori di tipo (`TypeError`), valore (`ValueError`) e autorizzazione (`PermissionError`)
4. Ogni errore ha una nota aggiuntiva via `add_note()` con il contesto del campo

**Criterio di successo:** Un form con 5 campi errati produce un `ExceptionGroup` con 5 eccezioni, ciascuna gestita dal handler appropriato.

---

## Auto-valutazione

Rispondi a queste domande per verificare la comprensione dei concetti. Le risposte sono nel blocco nascosto sotto.

1. Perche `except BaseException:` e quasi sempre sbagliato? Quali eccezioni cattura che `except Exception:` non cattura?

2. Qual e la differenza tra `raise e` e `raise` (senza argomenti) in un blocco `except`? Quale preserva il traceback originale?

3. In structlog, qual e il ruolo di `ProcessorFormatter.wrap_for_formatter` e perche deve essere l'ultimo processore nella catena di structlog?

4. Come si propaga il contesto delle `contextvars` a un thread creato via `ThreadPoolExecutor`? Perche `asyncio.create_task()` non ha questo problema?

5. Nella configurazione OTel log bridge, quali componenti sono coinvolti nel percorso: log event dell'applicazione -> OTLP exporter?

6. Qual e la differenza tra `except` e `except*`? Possono coesistere nello stesso blocco `try`?

7. Perche il retry budget e importante in un'architettura a microservizi? Come previene le cascate di fallimenti?

8. Quale metodo di `logging.Logger` include automaticamente il traceback dell'eccezione corrente nel messaggio di log?

<details>
<summary>Risposte</summary>

1. `except BaseException:` cattura anche `KeyboardInterrupt`, `SystemExit` e `GeneratorExit`, impedendo la terminazione controllata del processo. L'unico uso legittimo e nei framework che devono garantire il flush prima del crash, e anche li l'eccezione va ri-sollevata.

2. `raise` (senza argomenti) ri-solleva l'eccezione corrente preservando il traceback originale completo. `raise e` crea un nuovo traceback dal punto del raise, perdendo le informazioni sullo stack originale. Usare sempre `raise` senza argomenti.

3. `ProcessorFormatter.wrap_for_formatter` e un processore che prepara il log event per essere consumato da `ProcessorFormatter` di stdlib. Deve essere l'ultimo perche i processori successivi (rendering) vengono eseguiti dal `ProcessorFormatter` nel contesto di stdlib, non dalla pipeline di structlog. Dopo `wrap_for_formatter`, l'evento esce da structlog e entra in stdlib.

4. Per i thread, serve `contextvars.copy_context().run(funzione)` che crea una copia del contesto e la usa per eseguire la funzione nel thread. `asyncio.create_task()` propaga automaticamente il contesto corrente al task figlio perche asyncio e integrato con il meccanismo di `contextvars` dal design (PEP 567).

5. Il percorso completo: `structlog.get_logger().info()` -> processor chain di structlog -> `wrap_for_formatter` -> stdlib `logging.Logger` -> `LoggingHandler` di OTel SDK -> `LoggerProvider` (che inietta trace_id/span_id) -> `BatchLogRecordProcessor` -> `OTLPLogExporter` -> OTel Collector.

6. `except` gestisce una singola eccezione alla volta. `except*` gestisce un sottoinsieme di eccezioni all'interno di un `ExceptionGroup`, lasciando propagare le restanti. Non possono coesistere nello stesso blocco `try` — genera `SyntaxError`.

7. Il retry budget limita la percentuale totale di retry in una finestra temporale. Senza budget, quando un servizio downstream e in difficolta, ogni client riprova indipendentemente, moltiplicando il carico sul servizio e ritardandone il recupero (cascading failure). Con un budget del 10%, al massimo il 10% delle richieste nella finestra sono retry.

8. `logger.exception()` logga a livello ERROR e include automaticamente il traceback dell'eccezione corrente. Equivale a `logger.error(msg, exc_info=True)`.

</details>

---

## Letture primarie consigliate

1. **Python docs — Built-in Exceptions** — gerarchia completa delle eccezioni built-in, con descrizione di ogni classe e attributo. URL: https://docs.python.org/3/library/exceptions.html (consultato 2026-05-23).

2. **Python docs — logging module** — documentazione ufficiale del modulo logging, inclusi handler, formatter, filtri e configurazione avanzata. URL: https://docs.python.org/3/library/logging.html (consultato 2026-05-23).

3. **Python docs — logging.config** — riferimento per `dictConfig()`, `fileConfig()` e gli schemi di configurazione. URL: https://docs.python.org/3/library/logging.config.html (consultato 2026-05-23).

4. **PEP 654 — Exception Groups and except*** — specifica formale di `ExceptionGroup` e sintassi `except*`, con motivazione e casi d'uso. URL: https://peps.python.org/pep-0654/ (consultato 2026-05-23).

5. **PEP 678 — Enriching Exceptions with Notes** — specifica di `add_note()` per arricchire eccezioni con contesto aggiuntivo. URL: https://peps.python.org/pep-0678/ (consultato 2026-05-23).

6. **PEP 567 — Context Variables** — specifica di `contextvars`, il meccanismo per variabili di contesto async-safe. URL: https://peps.python.org/pep-0567/ (consultato 2026-05-23).

7. **structlog documentation** — guida completa alla configurazione, processori, bound logger, integrazione con stdlib. URL: https://www.structlog.org/en/stable/ (consultato 2026-05-23).

8. **OpenTelemetry Python SDK — Logs** — documentazione del log bridge OTel per Python, incluso `LoggingHandler` e `LoggerProvider`. URL: https://opentelemetry.io/docs/languages/python/instrumentation/#logs (consultato 2026-05-23).

9. **OpenTelemetry Logs Specification** — specifica del data model dei log in OTel, correlazione con traces. URL: https://opentelemetry.io/docs/specs/otel/logs/ (consultato 2026-05-23).

10. **tenacity documentation** — libreria di retry per Python, backoff esponenziale, condizioni di stop, logging. URL: https://tenacity.readthedocs.io/ (consultato 2026-05-23).

11. **Sentry Python SDK** — documentazione dell'SDK Python di Sentry, integrations, breadcrumbs, scope. URL: https://docs.sentry.io/platforms/python/ (consultato 2026-05-23).

12. **"Site Reliability Engineering" (Google)** — Capitolo 22: "Addressing Cascading Failures" — pattern retry budget e circuit breaker. O'Reilly, 2016. ISBN: 978-1-491-92912-4. Disponibile gratuitamente: https://sre.google/sre-book/addressing-cascading-failures/

---

## Collegamenti incrociati

### Nello stesso corso (04-PROGRAMMAZIONE-PYTHON)

- [01-fondamenti-linguaggio.md](./01-fondamenti-linguaggio.md) — sintassi base, tipi built-in
- [02-oop.md](./02-oop.md) — classi, ereditarieta (base per eccezioni personalizzate)
- [04-decoratori-generatori-context-manager.md](./04-decoratori-generatori-context-manager.md) — context manager, decoratori (usati in retry pattern e gestione errori)
- [08-testing.md](./08-testing.md) — pytest, test delle eccezioni con `pytest.raises`
- [10-programmazione-asincrona.md](./10-programmazione-asincrona.md) — asyncio, TaskGroup, correlazione ID in contesto async
- [18-sicurezza.md](./18-sicurezza.md) — protezione dati sensibili nei log, mascheramento
- [25-performance.md](./25-performance.md) — impatto prestazionale del logging, ottimizzazione
- [29-pydantic-e-validazione.md](./29-pydantic-e-validazione.md) — validazione strutturata, `ValidationError`
- [31-osservabilita-otel-prometheus.md](./31-osservabilita-otel-prometheus.md) — OTel completo (traces, metrics, logs), Prometheus, Grafana

### In altri corsi

- [06-GESTIONE-PIATTAFORME/08-monitoring-observability.md](../06-GESTIONE-PIATTAFORME/08-monitoring-observability.md) — OTel Collector, OTLP, Grafana stack
- [08-MANUTENZIONE-IT/07-monitoraggio-incidenti.md](../08-MANUTENZIONE-IT/07-monitoraggio-incidenti.md) — monitoraggio incidenti, correlazione traces-logs-metrics
- [12-SOFTWARE-ENGINEERING-EXTRA/05_DevOps_Cloud_Native/05_Observability_SLI_SLO_SLA.md](../12-SOFTWARE-ENGINEERING-EXTRA/05_DevOps_Cloud_Native/05_Observability_SLI_SLO_SLA.md) — SLI/SLO/SLA, error budget

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **BaseException** | Classe radice di tutte le eccezioni Python. Non catturare direttamente tranne casi eccezionali. |
| **add_note()** | Metodo PEP 678 (Python 3.11+) che aggiunge note testuali a un'eccezione senza alterarne tipo o messaggio. |
| **before_send** | Hook Sentry SDK invocato prima dell'invio di ogni evento, per filtrare o sanitizzare dati sensibili. |
| **Bound Logger** | Logger structlog a cui sono stati associati campi chiave-valore persistenti via `bind()`. |
| **Breadcrumb** | Evento contestuale Sentry (automatico o manuale) che traccia il percorso di esecuzione precedente un errore. |
| **Circuit Breaker** | Pattern che interrompe le chiamate a un servizio dopo un numero di fallimenti, prevenendo cascate. |
| **Correlation ID** | Identificatore univoco (tipicamente UUID) che collega tutti i log e le operazioni di una singola richiesta. |
| **contextvars** | Modulo stdlib (PEP 567) per variabili di contesto thread-safe e async-safe. |
| **derive()** | Metodo di ExceptionGroup che crea un nuovo gruppo con lo stesso messaggio ma eccezioni diverse. |
| **dictConfig** | Funzione di `logging.config` per configurare il logging da un dizionario Python. Approccio raccomandato. |
| **DRF** | Django REST Framework — libreria per costruire API REST con Django, include exception handler configurabile. |
| **DropEvent** | Eccezione structlog che un processore puo sollevare per scartare un log event dalla pipeline. |
| **EAFP** | "Easier to Ask Forgiveness than Permission" — pattern Pythonic: provare l'operazione e gestire l'eccezione. |
| **ExceptionGroup** | Classe Python 3.11+ che raggruppa piu eccezioni in un singolo oggetto, gestibile con `except*`. |
| **except*** | Sintassi Python 3.11+ per gestire un sottoinsieme di eccezioni all'interno di un `ExceptionGroup`. |
| **Handler** | Componente del modulo `logging` che determina la destinazione dei messaggi (console, file, rete). |
| **HTTPException** | Eccezione FastAPI/Starlette che rappresenta una risposta HTTP con status code e dettaglio specifico. |
| **LBYL** | "Look Before You Leap" — controllare le precondizioni prima di tentare un'operazione. |
| **LoggerProvider** | Componente OTel SDK che gestisce i logger e collega i log record agli exporter. |
| **LoggingHandler** | Handler stdlib fornito da OTel SDK che invia i log a un `LoggerProvider` per l'esportazione. |
| **OTLP** | OpenTelemetry Protocol — protocollo di trasporto per traces, metrics e logs verso il Collector. |
| **ProcessorFormatter** | Classe structlog che funge da bridge: usa la pipeline di processori structlog come formatter per stdlib. |
| **QueueHandler** | Handler stdlib che inserisce LogRecord in una coda, disaccoppiando emissione da elaborazione I/O. |
| **QueueListener** | Componente stdlib che in un thread separato consuma LogRecord dalla coda e li passa agli handler reali. |
| **RequestValidationError** | Eccezione FastAPI sollevata quando i dati della richiesta non superano la validazione Pydantic. |
| **Retry Budget** | Limite sulla percentuale di retry in una finestra temporale, per prevenire cascate di fallimenti. |
| **set_context()** | Funzione Sentry SDK che associa dati strutturati arbitrari (dizionari) a un evento, visualizzati nella dashboard. |
| **structlog** | Libreria Python per logging strutturato basata su pipeline di processori componibili. |
| **subgroup()** | Metodo di ExceptionGroup che filtra ricorsivamente le eccezioni contenute per tipo o predicato. |
| **Traceback** | Sequenza di frame dello stack che descrive il percorso di esecuzione fino al punto di un'eccezione. |
| **trace_id** | Identificatore univoco OTel che collega tutti gli span e i log di una singola richiesta distribuita. |
