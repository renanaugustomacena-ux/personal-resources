---
corso: "Programmazione Python"
fase: "3 — Concorrenza e Asincronia"
modulo: "10"
titolo: "Programmazione Asincrona"
versione: "Python 3.12+ / asyncio / aiohttp / uvloop"
livello: "Avanzato"
prerequisiti:
  - "01-06 — Python Base"
  - "04 — Decoratori, Generatori e Context Manager"
  - "07 — Error Handling e Logging"
obiettivi:
  - "Padroneggiare asyncio: event loop, coroutine, Task e TaskGroup"
  - "Implementare I/O concorrente con aiohttp, aiofiles e asyncpg"
  - "Gestire ExceptionGroup e except* in codice asincrono"
  - "Applicare pattern di concorrenza: semafori, lock, queue asincrone"
  - "Ottimizzare performance con uvloop e structured concurrency"
  - "Integrare codice sincrono e asincrono con run_in_executor"
tag: [asyncio, async-await, coroutine, concorrenza, aiohttp, uvloop, TaskGroup, structured-concurrency]
---

# Programmazione Asincrona — Guida Completa

> **Modulo 10** · **Aggiornamento:** 2026-05-24 · **Versione:** Python 3.12+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Decoratori e Generatori](04-decoratori-generatori-context-manager.md), [Error Handling](07-error-handling-e-logging.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare asyncio: event loop, coroutine, Task e TaskGroup
> 2. Implementare I/O concorrente con aiohttp, aiofiles e asyncpg
> 3. Gestire `ExceptionGroup` e `except*` in codice asincrono
> 4. Applicare pattern di concorrenza: semafori, lock, queue asincrone
> 5. Ottimizzare performance con uvloop e structured concurrency
> 6. Integrare codice sincrono e asincrono con `run_in_executor`
>
> **Tempo stimato:** 8-10 ore · **Livello:** Avanzato

---

## Frontmatter

| Campo | Valore |
|-------|--------|
| **Corso** | Programmazione Python — Percorso Completo |
| **Fase** | Fase 3 — Concorrenza e Parallelismo |
| **Modulo** | 10 — Programmazione Asincrona |
| **Versione Python** | 3.12+ (sezioni dedicate a feature 3.11, 3.12, 3.13) |
| **Livello** | Proficient |
| **Prerequisiti** | Modulo 01 (fondamenti), Modulo 04 (generatori, context manager), Modulo 07 (error handling) |
| **Tempo stimato** | 20-25 ore di studio + esercizi |

### Obiettivi di apprendimento

Al completamento di questo modulo lo studente sara in grado di:

1. **Progettare e implementare applicazioni I/O-bound concorrenti** utilizzando `asyncio`, coroutine, task e le API di alto livello del modulo.
2. **Applicare structured concurrency con `TaskGroup`** (Python 3.11+) per gestire gruppi di task con cancellazione automatica e gestione errori tramite `ExceptionGroup`.
3. **Utilizzare `asyncio.Runner`** (Python 3.11+) per controllare il ciclo di vita dell'event loop in scenari avanzati che richiedono riuso del loop o configurazione del contesto.
4. **Gestire timeout con `asyncio.timeout()`** (Python 3.11+) come sostituto idiomatico di `asyncio.wait_for()` tramite pattern context manager.
5. **Scegliere il modello di concorrenza appropriato** (asyncio vs threading vs multiprocessing) in base al tipo di workload, giustificando la scelta con considerazioni su GIL, I/O-bound vs CPU-bound e overhead.
6. **Implementare pattern producer-consumer, fan-out/fan-in e pipeline** con code asincrone, semafori e primitive di sincronizzazione.
7. **Integrare codice sincrono bloccante** nell'event loop tramite `asyncio.to_thread()`, `run_in_executor()` e executor personalizzati.
8. **Comprendere le implicazioni di PEP 703 (free-threading)** sulla programmazione asincrona e anticipare l'evoluzione dell'ecosistema Python senza GIL.
9. **Testare codice asincrono** con `pytest-asyncio`, `anyio` e tecniche di mocking per coroutine e context manager asincroni.
10. **Diagnosticare problemi comuni** (event loop bloccato, coroutine non awaitate, task reference loss, deadlock) con debug mode, profiling e strumenti di osservabilita.

---

## Mappa Concettuale

```
                          ┌─────────────────────────┐
                          │      EVENT LOOP          │
                          │  (selectors, callbacks,  │
                          │   scheduling, I/O poll)  │
                          └────────┬────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
              │ COROUTINE  │ │   TASK     │ │  FUTURE   │
              │ async def  │ │ create_    │ │ risultato │
              │ await      │ │ task()     │ │ di basso  │
              │ async for  │ │ TaskGroup  │ │ livello   │
              │ async with │ │ gather()   │ │           │
              └─────┬──────┘ └─────┬──────┘ └─────┬─────┘
                    │              │              │
         ┌──────────┴──────────────┴──────────────┘
         │
    ┌────▼───────────────────────────────────────────┐
    │            PRIMITIVE DI CONCORRENZA            │
    │                                                │
    │  Sincronizzazione    │    I/O Asincrono        │
    │  ─────────────────   │    ──────────────       │
    │  Lock                │    Streams API          │
    │  Semaphore           │    aiohttp / httpx      │
    │  Event               │    asyncpg / aiosqlite  │
    │  Condition           │    aiofiles             │
    │  Barrier (3.11+)     │                         │
    │                      │    Code Asincrone       │
    │  Timeout             │    ──────────────       │
    │  ──────────          │    Queue                │
    │  asyncio.timeout()   │    PriorityQueue        │
    │  wait_for()          │    LifoQueue            │
    └───────────┬──────────┴─────────────────────────┘
                │
    ┌───────────▼──────────────────────────────────────┐
    │          INTEGRAZIONE CON THREAD/PROCESSI        │
    │                                                  │
    │  to_thread()  │  run_in_executor()  │  uvloop    │
    │  Runner       │  ProcessPoolExecutor│            │
    └──────────────────────────────────────────────────┘
                │
    ┌───────────▼──────────────────────────────────────┐
    │          PEP 703 — FREE-THREADING (3.13+)        │
    │  Rimozione GIL  │  Implicazioni per asyncio      │
    │  Compatibilita  │  Timeline                      │
    └──────────────────────────────────────────────────┘
```

**Relazioni chiave:**

- L'**event loop** e il motore centrale: schedula coroutine, gestisce callback I/O tramite selectors, coordina timer e segnali.
- Una **coroutine** (`async def`) e un'unita di lavoro sospendibile. Da sola non fa nulla: deve essere schedulata come **task** o awaitata.
- Un **task** (`asyncio.Task`) e una coroutine wrappata e registrata nell'event loop. Inizia l'esecuzione immediatamente alla creazione.
- Un **future** (`asyncio.Future`) e il contenitore di basso livello per un risultato che sara disponibile in futuro. I task ereditano da Future.
- Le **primitive di sincronizzazione** (Lock, Semaphore, Event, Condition, Barrier) coordinano l'accesso a risorse condivise tra coroutine.
- L'**I/O asincrono** (Streams, HTTP client, database driver) sfrutta l'event loop per operazioni non bloccanti.
- L'**integrazione con thread/processi** permette di delegare lavoro bloccante o CPU-bound senza fermare l'event loop.

---

## Idee guida

1. **`asyncio.Runner` (3.11+) offre controllo avanzato sul ciclo di vita dell'event loop**, superando `asyncio.run()` in scenari che richiedono riuso del loop, configurazione del contesto o loop factory personalizzata.
2. **`asyncio.TaskGroup` (3.11+) implementa structured concurrency**: quando un task nel gruppo fallisce, tutti gli altri vengono cancellati automaticamente, prevenendo task orfani e garantendo cleanup deterministico.
3. **`asyncio.timeout()` (3.11+) sostituisce `wait_for` con un'API context manager piu pulita**, eliminando la necessita di wrappare singole coroutine e permettendo timeout su blocchi di codice arbitrari.
4. **PEP 703 (free-threading, 3.13+ sperimentale)**: la rimozione del GIL non rende asyncio obsoleto — l'I/O asincrono rimane piu efficiente del threading per carichi I/O-bound con migliaia di connessioni.
5. **uvloop sostituisce il default event loop su Linux/macOS** con un'implementazione basata su libuv, ottenendo throughput 2-4x superiore senza modifiche al codice applicativo.
6. **Il modello mentale corretto**: asyncio e concorrenza cooperativa su singolo thread. Ogni `await` e un punto di cessione esplicita del controllo. Bloccare il thread dell'event loop blocca tutto.

---

## Indice

1. [Panoramica](#panoramica)
   - [Sincrono vs Asincrono](#sincrono-vs-asincrono)
   - [Concorrenza vs Parallelismo](#concorrenza-vs-parallelismo)
   - [I/O Bound vs CPU Bound](#io-bound-vs-cpu-bound)
   - [Il Concetto di Event Loop](#il-concetto-di-event-loop)
   - [Il GIL e le Sue Implicazioni](#il-gil-e-le-sue-implicazioni)
2. [Fondamenti asyncio](#fondamenti-asyncio)
   - [Coroutine](#coroutine)
   - [Event Loop](#event-loop)
   - [Task](#task)
3. [Event Loop Internals](#event-loop-internals)
   - [Selectors e I/O Multiplexing](#selectors-e-io-multiplexing)
   - [Callback e Scheduling](#callback-e-scheduling)
   - [loop.run_in_executor](#looprun_in_executor)
   - [Loop Factory e Politiche](#loop-factory-e-politiche)
4. [asyncio.Runner (3.11+)](#asynciorunner-311)
   - [Sostituzione di asyncio.run](#sostituzione-di-asynciorun)
   - [Context Manager e Riuso del Loop](#context-manager-e-riuso-del-loop)
   - [Loop Factory Personalizzata](#loop-factory-personalizzata)
5. [TaskGroup e Structured Concurrency (3.11+)](#taskgroup-e-structured-concurrency-311)
   - [Principi di Structured Concurrency](#principi-di-structured-concurrency)
   - [Cancellazione Automatica](#cancellazione-automatica)
   - [ExceptionGroup e except*](#exceptiongroup-e-except)
   - [gather vs TaskGroup — Confronto](#gather-vs-taskgroup--confronto)
6. [asyncio.timeout (3.11+)](#asynciotimeout-311)
   - [Context Manager Pattern](#context-manager-pattern)
   - [timeout_at — Deadline Assolute](#timeout_at--deadline-assolute)
   - [Confronto con wait_for](#confronto-con-wait_for)
7. [Concorrenza con asyncio](#concorrenza-con-asyncio)
   - [gather](#gather)
   - [wait](#wait)
   - [as_completed](#as_completed)
   - [Semaphore e Lock](#semaphore-e-lock)
8. [Coroutine vs Generator](#coroutine-vs-generator)
   - [Evoluzione: yield → yield from → async/await](#evoluzione-yield--yield-from--asyncawait)
   - [async def, await, async for, async with](#async-def-await-async-for-async-with)
   - [Protocolli Asincroni: __aiter__, __anext__](#protocolli-asincroni-__aiter__-__anext__)
9. [Streams API](#streams-api)
   - [open_connection e start_server](#open_connection-e-start_server)
   - [StreamReader e StreamWriter](#streamreader-e-streamwriter)
   - [Esempio: Server Echo TCP](#esempio-server-echo-tcp)
   - [Esempio: Client HTTP Minimale](#esempio-client-http-minimale)
10. [Queue Patterns](#queue-patterns)
    - [asyncio.Queue](#asyncioqueue)
    - [Producer-Consumer Avanzato](#producer-consumer-avanzato)
    - [PriorityQueue e LifoQueue](#priorityqueue-e-lifoqueue)
    - [Bounded Queue e Backpressure](#bounded-queue-e-backpressure)
11. [Primitive di Sincronizzazione](#primitive-di-sincronizzazione)
    - [Lock e RLock Equivalente](#lock-e-rlock-equivalente)
    - [Event](#event)
    - [Semaphore e BoundedSemaphore](#semaphore-e-boundedsemaphore)
    - [Condition](#condition)
    - [Barrier (3.11+)](#barrier-311)
12. [Async Context Manager](#async-context-manager)
    - [Protocollo __aenter__ / __aexit__](#protocollo-__aenter__--__aexit__)
    - [@asynccontextmanager](#asynccontextmanager)
    - [Pattern Compositi](#pattern-compositi)
13. [Async I/O Pratico](#async-io-pratico)
    - [HTTP con aiohttp](#http-con-aiohttp)
    - [File I/O con aiofiles](#file-io-con-aiofiles)
    - [Database Asincrono](#database-asincrono)
14. [aiohttp vs httpx](#aiohttp-vs-httpx)
    - [Architettura e Design](#architettura-e-design)
    - [Performance e Compatibilita](#performance-e-compatibilita)
    - [Migrazione da aiohttp a httpx](#migrazione-da-aiohttp-a-httpx)
15. [Database Asincrono Avanzato](#database-asincrono-avanzato)
    - [asyncpg — Deep Dive](#asyncpg--deep-dive)
    - [SQLAlchemy Async — Pattern Avanzati](#sqlalchemy-async--pattern-avanzati)
    - [Connection Pooling Asincrono](#connection-pooling-asincrono)
16. [Async Generator e Context Manager](#async-generator-e-context-manager)
17. [Threading vs Multiprocessing vs Asyncio](#threading-vs-multiprocessing-vs-asyncio)
    - [threading](#threading)
    - [multiprocessing](#multiprocessing)
    - [concurrent.futures](#concurrentfutures)
    - [Combinare asyncio con Threading/Multiprocessing](#combinare-asyncio-con-threadingmultiprocessing)
18. [uvloop](#uvloop)
    - [Installazione e Attivazione](#installazione-e-attivazione)
    - [Benchmark e Comparazione](#benchmark-e-comparazione)
    - [Compatibilita e Limitazioni](#compatibilita-e-limitazioni)
19. [PEP 703 — Free-Threading](#pep-703--free-threading)
    - [La Rimozione del GIL](#la-rimozione-del-gil)
    - [Implicazioni per il Codice Asincrono](#implicazioni-per-il-codice-asincrono)
    - [Timeline e Build Sperimentale](#timeline-e-build-sperimentale)
    - [Compatibilita dell'Ecosistema](#compatibilita-dellecosistema)
20. [Testing Codice Asincrono](#testing-codice-asincrono)
    - [pytest-asyncio](#pytest-asyncio)
    - [anyio e Backend-Agnostic Testing](#anyio-e-backend-agnostic-testing)
    - [Mock di Funzioni Asincrone](#mock-di-funzioni-asincrone)
    - [Test di Timeout e Cancellazione](#test-di-timeout-e-cancellazione)
21. [Pattern Avanzati](#pattern-avanzati)
    - [Producer-Consumer](#producer-consumer)
    - [Fan-out/Fan-in](#fan-outfan-in)
    - [Graceful Shutdown](#graceful-shutdown)
22. [Pitfall Comuni](#pitfall-comuni)
    - [Bloccare l'Event Loop](#bloccare-levent-loop)
    - [Dimenticare await](#dimenticare-await)
    - [Task Reference Loss](#task-reference-loss)
    - [Deadlock con Primitive di Sincronizzazione](#deadlock-con-primitive-di-sincronizzazione)
    - [Starvation e Fairness](#starvation-e-fairness)
23. [Performance e Debugging](#performance-e-debugging)
24. [Troubleshooting](#troubleshooting)
25. [Best Practices](#best-practices)
26. [Esercizi](#esercizi)
27. [Letture e Riferimenti](#letture-e-riferimenti)
28. [Cross-Link ad Altri Moduli](#cross-link-ad-altri-moduli)
29. [Glossario](#glossario)

---

## Panoramica

La programmazione asincrona rappresenta un cambio di paradigma nel modo di concepire l'esecuzione del codice. Nei programmi tradizionali sincroni, ogni operazione viene completata prima di passare alla successiva. Nella programmazione asincrona, il programma puo avviare un'operazione e, mentre attende il risultato, proseguire con altre attivita. Questo approccio si rivela particolarmente efficace quando il programma trascorre la maggior parte del tempo in attesa di risorse esterne — risposte di rete, lettura da disco, query al database.

Python ha introdotto il supporto nativo per la programmazione asincrona con il modulo `asyncio` a partire da Python 3.4, e le keyword `async` e `await` dalla versione 3.5. Da allora l'ecosistema si e evoluto enormemente, con librerie mature per HTTP, database, file I/O e molto altro.

### Sincrono vs Asincrono

In un programma **sincrono**, le operazioni vengono eseguite in sequenza rigorosa. Se una funzione impiega 3 secondi per completare una richiesta HTTP, il programma rimane bloccato per tutta la durata dell'attesa.

```python
import time
import requests

def scarica_pagina(url):
    risposta = requests.get(url)
    return len(risposta.content)

# Esecuzione sincrona: ogni richiesta blocca fino al completamento
inizio = time.time()
urls = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
]
for url in urls:
    dimensione = scarica_pagina(url)
    print(f"Scaricato {url}: {dimensione} bytes")

print(f"Tempo totale: {time.time() - inizio:.2f}s")
# Tempo totale: ~3.00s (1s + 1s + 1s in sequenza)
```

In un programma **asincrono**, le tre richieste vengono lanciate contemporaneamente. Mentre una richiesta attende la risposta dal server, il programma puo gestire le altre.

```python
import asyncio
import aiohttp
import time

async def scarica_pagina(session, url):
    async with session.get(url) as risposta:
        contenuto = await risposta.read()
        return len(contenuto)

async def main():
    inizio = time.time()
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]
    async with aiohttp.ClientSession() as session:
        task = [scarica_pagina(session, url) for url in urls]
        risultati = await asyncio.gather(*task)
        for url, dimensione in zip(urls, risultati):
            print(f"Scaricato {url}: {dimensione} bytes")

    print(f"Tempo totale: {time.time() - inizio:.2f}s")
    # Tempo totale: ~1.00s (tutte e tre in parallelo)

asyncio.run(main())
```

La differenza e drammatica: da 3 secondi a circa 1 secondo. Questo guadagno si amplifica enormemente quando si gestiscono centinaia o migliaia di operazioni I/O.

### Concorrenza vs Parallelismo

Questi due concetti vengono spesso confusi, ma descrivono meccanismi distinti.

**Concorrenza** significa gestire piu attivita nello stesso periodo di tempo, alternando l'esecuzione tra di esse. Un singolo cuoco che prepara tre piatti diversi, passando dall'uno all'altro mentre aspetta che l'acqua bolle o che il forno si scaldi, lavora in modo concorrente. Non prepara i tre piatti simultaneamente, ma li porta avanti tutti gestendo intelligentemente i tempi morti.

**Parallelismo** significa eseguire piu attivita nello stesso istante. Tre cuochi che preparano ciascuno un piatto diverso contemporaneamente lavorano in parallelo. Questo richiede risorse hardware multiple (core della CPU).

`asyncio` implementa la concorrenza: un singolo thread gestisce molte operazioni alternando tra di esse. Il parallelismo vero richiede `multiprocessing` o librerie che sfruttano piu core della CPU.

### I/O Bound vs CPU Bound

La scelta dell'approccio di concorrenza dipende dal tipo di carico di lavoro.

**I/O Bound** — il programma trascorre la maggior parte del tempo in attesa di operazioni di input/output: richieste HTTP, query al database, lettura e scrittura di file, comunicazione di rete. In questi casi, `asyncio` e la scelta ideale perche permette di utilizzare il tempo di attesa per gestire altre operazioni.

**CPU Bound** — il programma trascorre la maggior parte del tempo in calcoli intensivi: elaborazione di immagini, calcoli matematici complessi, compressione dati, machine learning. In questi casi, `multiprocessing` e la scelta corretta perche distribuisce il lavoro su piu core della CPU.

```
Tipo di lavoro        Soluzione ottimale        Esempio
-----------------------------------------------------------------
I/O bound             asyncio                   Web scraping, API calls
I/O bound             threading                 Download paralleli
CPU bound             multiprocessing           Elaborazione immagini
Misto                 asyncio + ProcessPool     Web server con calcoli
```

### Il Concetto di Event Loop

L'event loop e il cuore della programmazione asincrona. Funziona come un direttore d'orchestra che coordina l'esecuzione di tutte le coroutine nel programma.

Il ciclo di vita dell'event loop segue questo schema:

1. Controlla se ci sono coroutine pronte per essere eseguite
2. Esegue la coroutine fino al prossimo punto di `await`
3. Quando la coroutine raggiunge un `await`, sospende l'esecuzione e registra l'operazione I/O
4. Passa alla prossima coroutine pronta
5. Quando un'operazione I/O si completa, marca la coroutine corrispondente come pronta
6. Ripete dal punto 1

Questo meccanismo permette a un singolo thread di gestire migliaia di connessioni simultanee, rendendolo estremamente efficiente per applicazioni di rete come web server, crawler e microservizi.

### Il GIL e le Sue Implicazioni

Il **Global Interpreter Lock (GIL)** e un mutex nell'interprete CPython che permette a un solo thread di eseguire bytecode Python alla volta. Questo significa che anche su un processore multicore, i thread Python non possono eseguire codice Python in vero parallelismo.

Le implicazioni sono significative:

- **Threading** — utile per operazioni I/O bound (il GIL viene rilasciato durante le operazioni I/O), ma non migliora le prestazioni per codice CPU bound
- **Multiprocessing** — aggira completamente il GIL creando processi separati, ciascuno con il proprio interprete e la propria copia della memoria
- **asyncio** — non e influenzato dal GIL perche opera su un singolo thread. La sua efficienza deriva dalla gestione intelligente dei tempi di attesa I/O, non dall'esecuzione parallela

A partire da Python 3.13, il progetto "free-threaded Python" (PEP 703) introduce una build sperimentale senza GIL, che potrebbe in futuro rendere il threading efficace anche per carichi CPU bound.

---

## Fondamenti asyncio

### Coroutine

Una coroutine e una funzione speciale definita con `async def` che puo sospendere la propria esecuzione con `await`, cedendo il controllo all'event loop. A differenza delle funzioni normali, chiamare una coroutine non la esegue immediatamente: restituisce un oggetto coroutine che deve essere schedulato nell'event loop.

```python
import asyncio

# Definizione di una coroutine
async def saluta(nome):
    print(f"Inizio saluto per {nome}")
    await asyncio.sleep(1)  # Simula un'operazione I/O
    print(f"Ciao, {nome}!")
    return f"Saluto completato per {nome}"

# ERRORE COMUNE: chiamare la coroutine senza await
# risultato = saluta("Mario")  # Restituisce un oggetto coroutine, NON esegue

# Modo corretto: eseguire con asyncio.run()
async def main():
    risultato = await saluta("Mario")
    print(risultato)

asyncio.run(main())
```

La keyword `await` puo essere utilizzata solo all'interno di funzioni `async def`. Quando il programma incontra un `await`, la coroutine corrente sospende l'esecuzione e restituisce il controllo all'event loop, che puo eseguire altre coroutine in attesa.

```python
import asyncio

async def operazione_lenta(id_operazione, durata):
    print(f"Operazione {id_operazione}: inizio")
    await asyncio.sleep(durata)
    print(f"Operazione {id_operazione}: completata dopo {durata}s")
    return id_operazione

async def main():
    # Esecuzione sequenziale: ogni await blocca fino al completamento
    r1 = await operazione_lenta(1, 2)
    r2 = await operazione_lenta(2, 1)
    # Tempo totale: 3s (sequenziale)

asyncio.run(main())
```

L'oggetto coroutine rappresenta un'esecuzione sospesa. Puo essere ispezionato prima di essere schedulato.

```python
import asyncio

async def calcola(x, y):
    await asyncio.sleep(0.1)
    return x + y

# Creazione dell'oggetto coroutine (non ancora eseguito)
coro = calcola(3, 4)
print(type(coro))  # <class 'coroutine'>

# Esecuzione effettiva
async def main():
    risultato = await coro
    print(risultato)  # 7

asyncio.run(main())
```

### Event Loop

L'event loop e il meccanismo centrale che orchestra l'esecuzione di tutte le coroutine. In Python moderno (3.7+), `asyncio.run()` e il modo raccomandato per avviare l'event loop. Gestisce automaticamente la creazione, l'esecuzione e la chiusura del loop.

```python
import asyncio

async def main():
    print("L'event loop e in esecuzione")
    await asyncio.sleep(0.5)
    print("Operazione completata")

# Metodo raccomandato (Python 3.7+)
asyncio.run(main())
```

Per scenari piu avanzati, e possibile interagire direttamente con l'event loop.

```python
import asyncio

async def mostra_loop():
    # Ottenere il loop corrente dall'interno di una coroutine
    loop = asyncio.get_running_loop()
    print(f"Loop in esecuzione: {loop}")
    print(f"Loop chiuso: {loop.is_closed()}")
    print(f"Loop in esecuzione: {loop.is_running()}")

asyncio.run(mostra_loop())
```

Il ciclo di vita dell'event loop segue fasi precise:

```python
import asyncio

async def fase_1():
    print("Fase 1: inizializzazione")
    await asyncio.sleep(0.1)
    return "dati_fase_1"

async def fase_2(dati):
    print(f"Fase 2: elaborazione di {dati}")
    await asyncio.sleep(0.1)
    return "risultato_finale"

async def main():
    # L'event loop gestisce l'ordine di esecuzione
    dati = await fase_1()
    risultato = await fase_2(dati)
    print(f"Risultato: {risultato}")

# asyncio.run() crea il loop, esegue main(), chiude il loop
asyncio.run(main())
```

### Task

Un `Task` e un wrapper attorno a una coroutine che ne schedula l'esecuzione nell'event loop. A differenza di un semplice `await`, creare un task permette alla coroutine di iniziare l'esecuzione immediatamente in background, senza attendere il completamento prima di procedere.

```python
import asyncio

async def scarica(nome, durata):
    print(f"Inizio download: {nome}")
    await asyncio.sleep(durata)
    print(f"Download completato: {nome}")
    return f"{nome}: {durata}s"

async def main():
    # Creare task: le coroutine iniziano subito
    task1 = asyncio.create_task(scarica("file_a.zip", 3))
    task2 = asyncio.create_task(scarica("file_b.zip", 1))
    task3 = asyncio.create_task(scarica("file_c.zip", 2))

    # Tutti e tre i download procedono in concorrenza
    r1 = await task1
    r2 = await task2
    r3 = await task3
    print(f"Risultati: {r1}, {r2}, {r3}")
    # Tempo totale: ~3s (non 6s)

asyncio.run(main())
```

La differenza cruciale tra task e coroutine e che il task inizia l'esecuzione immediatamente quando viene creato con `create_task()`, mentre una coroutine semplice viene eseguita solo quando raggiunta da un `await`.

**Cancellazione dei task** — un task in esecuzione puo essere cancellato programmaticamente.

```python
import asyncio

async def operazione_lunga():
    try:
        print("Operazione avviata")
        await asyncio.sleep(10)
        print("Operazione completata")  # Non verra mai stampato
    except asyncio.CancelledError:
        print("Operazione cancellata! Pulizia in corso...")
        # Esegui operazioni di cleanup
        raise  # Ri-solleva per propagare la cancellazione

async def main():
    task = asyncio.create_task(operazione_lunga())
    await asyncio.sleep(1)  # Lascia eseguire per 1 secondo
    task.cancel()  # Richiedi la cancellazione

    try:
        await task
    except asyncio.CancelledError:
        print("Task confermato cancellato")

    print(f"Task cancellato: {task.cancelled()}")  # True

asyncio.run(main())
```

**TaskGroup (Python 3.11+)** — introdotto per gestire gruppi di task in modo strutturato, con gestione automatica degli errori e cancellazione.

```python
import asyncio

async def elabora_elemento(id_elemento):
    await asyncio.sleep(0.5)
    if id_elemento == 3:
        raise ValueError(f"Errore nell'elemento {id_elemento}")
    return f"Risultato {id_elemento}"

async def main():
    # TaskGroup: structured concurrency
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(elabora_elemento(1))
            task2 = tg.create_task(elabora_elemento(2))
            task3 = tg.create_task(elabora_elemento(3))  # Questo fallira
            task4 = tg.create_task(elabora_elemento(4))
    except* ValueError as eg:
        # ExceptionGroup (Python 3.11+)
        for exc in eg.exceptions:
            print(f"Errore catturato: {exc}")
    # Quando un task nel gruppo fallisce, tutti gli altri vengono cancellati

asyncio.run(main())
```

Il `TaskGroup` garantisce che tutti i task vengano completati (o cancellati) prima di uscire dal blocco `async with`. Questo pattern e noto come **structured concurrency** e previene problemi comuni come task orfani o errori silenziosi.

---

## Event Loop Internals

L'event loop di asyncio e costruito sopra il modulo `selectors` della libreria standard, che a sua volta si appoggia alle system call del sistema operativo per l'I/O multiplexing: `epoll` su Linux, `kqueue` su macOS/BSD, `IOCP` su Windows.

### Selectors e I/O Multiplexing

Il selettore monitora piu file descriptor contemporaneamente, svegliando l'event loop quando uno o piu di essi sono pronti per operazioni di lettura o scrittura. Questo e il meccanismo che permette a un singolo thread di gestire migliaia di connessioni di rete.

```python
import selectors
import socket

# Esempio di basso livello: selectors (cio che asyncio usa internamente)
sel = selectors.DefaultSelector()

def accetta_connessione(sock, mask):
    conn, addr = sock.accept()
    print(f"Connessione accettata da {addr}")
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, leggi_dati)

def leggi_dati(conn, mask):
    dati = conn.recv(1024)
    if dati:
        print(f"Ricevuto: {dati.decode()}")
        conn.sendall(dati)  # Echo
    else:
        print("Connessione chiusa")
        sel.unregister(conn)
        conn.close()

# Setup del server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("localhost", 8888))
sock.listen(100)
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accetta_connessione)

# Event loop manuale (cio che asyncio automatizza)
# while True:
#     eventi = sel.select(timeout=None)  # Blocca fino a I/O pronto
#     for key, mask in eventi:
#         callback = key.data
#         callback(key.fileobj, mask)
```

Internamente, l'event loop di asyncio esegue un ciclo simile a questo pseudocodice:

```
loop._run_once():
    1. Calcola il timeout minimo tra i callback schedulati
    2. Chiama selector.select(timeout) — blocca fino a I/O o timeout
    3. Processa i file descriptor pronti → schedula le callback I/O
    4. Esegue tutte le callback pronte (dalla coda ready)
    5. Esegue le callback schedulte con call_soon()
```

### Callback e Scheduling

L'event loop mantiene una coda di callback pronte per l'esecuzione. Le API di basso livello permettono di schedulare callback direttamente.

```python
import asyncio

async def dimostra_scheduling():
    loop = asyncio.get_running_loop()

    # call_soon: schedula una callback per la prossima iterazione del loop
    loop.call_soon(print, "Eseguito alla prossima iterazione")

    # call_later: schedula dopo un ritardo in secondi
    loop.call_later(0.5, print, "Eseguito dopo 0.5 secondi")

    # call_at: schedula a un tempo assoluto (loop.time())
    tempo_corrente = loop.time()
    loop.call_at(tempo_corrente + 1.0, print, "Eseguito a tempo assoluto")

    # loop.time() restituisce il clock monotono interno
    print(f"Tempo loop corrente: {loop.time():.4f}")

    await asyncio.sleep(1.5)  # Attendi che tutte le callback vengano eseguite

asyncio.run(dimostra_scheduling())
```

**Risoluzione DNS asincrona** — l'event loop delega la risoluzione DNS a un thread pool per evitare di bloccare il loop:

```python
import asyncio
import socket

async def risolvi_dns():
    loop = asyncio.get_running_loop()

    # getaddrinfo asincrono (internamente usa un thread)
    info = await loop.getaddrinfo(
        "www.python.org", 443,
        family=socket.AF_INET,
        type=socket.SOCK_STREAM
    )
    for famiglia, tipo, proto, nome_canonico, indirizzo in info:
        print(f"  {indirizzo[0]}:{indirizzo[1]}")

asyncio.run(risolvi_dns())
```

### loop.run_in_executor

`run_in_executor` e il ponte tra il mondo asincrono e quello sincrono. Delega una funzione sincrona bloccante a un executor (thread pool o process pool) e restituisce un awaitable.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import math

def io_bloccante(percorso: str) -> str:
    """Simula lettura file sincrona pesante."""
    time.sleep(1)
    return f"Contenuto di {percorso}"

def calcolo_cpu(n: int) -> int:
    """Operazione CPU-bound."""
    return len([i for i in range(n) if all(i % j != 0 for j in range(2, int(math.sqrt(i)) + 1)) and i > 1])

async def main():
    loop = asyncio.get_running_loop()

    # Executor di default (ThreadPoolExecutor) — per I/O bloccante
    risultato = await loop.run_in_executor(None, io_bloccante, "/tmp/dati.txt")
    print(risultato)

    # ThreadPoolExecutor esplicito con dimensione personalizzata
    with ThreadPoolExecutor(max_workers=8) as thread_pool:
        risultati = await asyncio.gather(
            loop.run_in_executor(thread_pool, io_bloccante, "a.txt"),
            loop.run_in_executor(thread_pool, io_bloccante, "b.txt"),
            loop.run_in_executor(thread_pool, io_bloccante, "c.txt"),
        )
        print(f"File letti: {len(risultati)}")

    # ProcessPoolExecutor — per CPU-bound
    with ProcessPoolExecutor(max_workers=4) as process_pool:
        conteggio_primi = await loop.run_in_executor(
            process_pool, calcolo_cpu, 100_000
        )
        print(f"Numeri primi trovati: {conteggio_primi}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Loop Factory e Politiche

Le politiche dell'event loop determinano quale implementazione di loop viene usata. Questo e il meccanismo che permette a uvloop di sostituire il loop di default.

```python
import asyncio

# Ottenere la politica corrente
politica = asyncio.get_event_loop_policy()
print(f"Politica corrente: {type(politica).__name__}")

# Su Windows, la politica di default per Python 3.8+ e ProactorEventLoop
# Su Linux/macOS, e SelectorEventLoop

# Impostare una politica personalizzata (esempio con uvloop)
# import uvloop
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Oppure, con asyncio.Runner (3.11+), si puo specificare la loop_factory
# runner = asyncio.Runner(loop_factory=uvloop.new_event_loop)
```

---

## asyncio.Runner (3.11+)

`asyncio.Runner` e stato introdotto in Python 3.11 (documentato in [What's New in Python 3.11](https://docs.python.org/3.11/whatsnew/3.11.html)) come alternativa avanzata ad `asyncio.run()`. Mentre `asyncio.run()` crea un nuovo event loop, esegue la coroutine e chiude il loop ad ogni invocazione, `Runner` permette di riusare lo stesso loop per piu esecuzioni.

### Sostituzione di asyncio.run

Il caso d'uso piu semplice: `Runner` come sostituto diretto di `asyncio.run()`.

```python
import asyncio

async def compito_a():
    await asyncio.sleep(0.1)
    return "risultato_a"

async def compito_b():
    await asyncio.sleep(0.1)
    return "risultato_b"

# Con asyncio.run(): due loop separati (il secondo non puo riusare il primo)
r1 = asyncio.run(compito_a())
r2 = asyncio.run(compito_b())

# Con Runner: un solo loop, riusato per entrambe le esecuzioni
with asyncio.Runner() as runner:
    r1 = runner.run(compito_a())
    r2 = runner.run(compito_b())
    print(f"Risultati: {r1}, {r2}")
# Il loop viene chiuso all'uscita dal context manager
```

### Context Manager e Riuso del Loop

Il vantaggio principale di `Runner` e il riuso del loop. Questo e utile in scenari come:

- Test suite: eseguire piu test asincroni sullo stesso loop senza overhead di creazione/distruzione.
- Applicazioni CLI: eseguire piu operazioni asincrone in sequenza.
- Framework: controllare il ciclo di vita del loop dall'esterno.

```python
import asyncio

async def inizializza_risorse():
    """Setup iniziale: connessioni, cache, etc."""
    print("Inizializzazione risorse...")
    await asyncio.sleep(0.1)
    return {"db": "connessa", "cache": "pronta"}

async def elabora_richiesta(risorse: dict, id_richiesta: int):
    """Elabora una richiesta usando le risorse inizializzate."""
    print(f"Elaboro richiesta {id_richiesta} con {risorse}")
    await asyncio.sleep(0.05)
    return f"risposta_{id_richiesta}"

async def cleanup_risorse(risorse: dict):
    """Cleanup finale."""
    print(f"Cleanup risorse: {risorse}")
    await asyncio.sleep(0.05)

# Il Runner mantiene il loop aperto per tutta la sessione
with asyncio.Runner() as runner:
    # Fase 1: inizializzazione
    risorse = runner.run(inizializza_risorse())

    # Fase 2: elaborazione multipla (stesso loop)
    for i in range(5):
        risultato = runner.run(elabora_richiesta(risorse, i))
        print(f"  -> {risultato}")

    # Fase 3: cleanup
    runner.run(cleanup_risorse(risorse))
```

### Loop Factory Personalizzata

`Runner` accetta un parametro `loop_factory` che permette di specificare quale implementazione di event loop usare. Questo e il modo idiomatico per integrare uvloop o altri loop personalizzati.

```python
import asyncio

# Con uvloop (quando installato)
# import uvloop
# with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
#     runner.run(main())

# Loop factory personalizzata con configurazione
def crea_loop_configurato():
    loop = asyncio.new_event_loop()
    # Configura il loop
    loop.set_debug(True)
    loop.slow_callback_duration = 0.05  # Soglia per callback lente (50ms)
    return loop

with asyncio.Runner(loop_factory=crea_loop_configurato) as runner:
    async def main():
        loop = asyncio.get_running_loop()
        print(f"Debug mode: {loop.get_debug()}")
        print(f"Slow callback threshold: {loop.slow_callback_duration}s")
        await asyncio.sleep(0.1)

    runner.run(main())
```

**`Runner` vs `asyncio.run()` — quando usare quale:**

| Scenario | Scelta | Motivo |
|----------|--------|--------|
| Script semplice | `asyncio.run()` | Piu conciso, unica coroutine |
| Test suite | `Runner` | Riuso del loop tra test, overhead minore |
| CLI con piu comandi async | `Runner` | Riuso risorse tra comandi |
| Integrazione uvloop | `Runner(loop_factory=...)` | API pulita per loop factory |
| Framework/libreria | `Runner` | Controllo esplicito del ciclo di vita |

---

## TaskGroup e Structured Concurrency (3.11+)

`asyncio.TaskGroup` e la risposta di Python alla structured concurrency, un paradigma formalizzato da Nathaniel J. Smith nel paper "Notes on structured concurrency" e implementato in Trio prima di arrivare nella libreria standard.

### Principi di Structured Concurrency

Il principio fondamentale: **il ciclo di vita di un task concorrente non deve superare quello del blocco che lo ha creato.** Quando si esce da un `async with TaskGroup()`, tutti i task del gruppo sono garantiti essere completati (o cancellati). Non ci sono task orfani.

```python
import asyncio

async def operazione_veloce():
    await asyncio.sleep(0.1)
    return "veloce"

async def operazione_media():
    await asyncio.sleep(0.5)
    return "media"

async def operazione_lenta():
    await asyncio.sleep(1.0)
    return "lenta"

async def main():
    # Tutti i task completano (o sono cancellati) prima di uscire dal blocco
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(operazione_veloce())
        t2 = tg.create_task(operazione_media())
        t3 = tg.create_task(operazione_lenta())

    # Qui TUTTI i task sono completati — garantito
    print(f"Veloce: {t1.result()}")
    print(f"Media: {t2.result()}")
    print(f"Lenta: {t3.result()}")

asyncio.run(main())
```

### Cancellazione Automatica

Quando un task nel gruppo solleva un'eccezione, `TaskGroup` cancella automaticamente tutti gli altri task ancora in esecuzione, attende la loro cancellazione e poi solleva un `ExceptionGroup`.

```python
import asyncio

async def task_riuscito(id_task: int, durata: float):
    print(f"Task {id_task}: inizio")
    await asyncio.sleep(durata)
    print(f"Task {id_task}: completato")
    return f"risultato_{id_task}"

async def task_fallimentare(id_task: int, durata: float):
    print(f"Task {id_task}: inizio")
    await asyncio.sleep(durata)
    raise RuntimeError(f"Task {id_task} fallito!")

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            # Task 1: completa dopo 0.1s
            t1 = tg.create_task(task_riuscito(1, 0.1))
            # Task 2: fallisce dopo 0.3s
            t2 = tg.create_task(task_fallimentare(2, 0.3))
            # Task 3: sarebbe completato dopo 1s, ma verra cancellato
            t3 = tg.create_task(task_riuscito(3, 1.0))
            # Task 4: sarebbe completato dopo 2s, ma verra cancellato
            t4 = tg.create_task(task_riuscito(4, 2.0))
    except* RuntimeError as eg:
        print(f"Catturati {len(eg.exceptions)} errori:")
        for exc in eg.exceptions:
            print(f"  - {exc}")

    # Task 1 completato (era gia finito prima dell'errore)
    print(f"Task 1 completato: {t1.done()}, cancellato: {t1.cancelled()}")
    # Task 3 e 4 cancellati
    print(f"Task 3 cancellato: {t3.cancelled()}")
    print(f"Task 4 cancellato: {t4.cancelled()}")

asyncio.run(main())
```

### ExceptionGroup e except*

Python 3.11 ha introdotto `ExceptionGroup` e la sintassi `except*` specificamente per gestire le eccezioni multiple che `TaskGroup` puo produrre.

```python
import asyncio

async def task_tipo_a():
    await asyncio.sleep(0.1)
    raise ValueError("Errore di validazione")

async def task_tipo_b():
    await asyncio.sleep(0.2)
    raise TypeError("Errore di tipo")

async def task_tipo_c():
    await asyncio.sleep(0.15)
    raise ConnectionError("Errore di connessione")

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(task_tipo_a())
            tg.create_task(task_tipo_b())
            tg.create_task(task_tipo_c())
    except* ValueError as eg:
        print(f"Errori di validazione ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  -> {e}")
    except* (TypeError, ConnectionError) as eg:
        print(f"Errori di tipo/connessione ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  -> {type(e).__name__}: {e}")

asyncio.run(main())
```

### gather vs TaskGroup — Confronto

| Aspetto | `asyncio.gather()` | `asyncio.TaskGroup` |
|---------|---------------------|---------------------|
| **Versione** | Python 3.4+ | Python 3.11+ |
| **Errore in un task** | Dipende da `return_exceptions` | Cancella tutti gli altri, solleva `ExceptionGroup` |
| **Task orfani** | Possibili se non gestiti | Impossibili — structured concurrency |
| **Aggiunta dinamica** | No (lista fissa) | Si, dentro il blocco `async with` |
| **Cancellazione** | Manuale | Automatica |
| **Eccezioni multiple** | Con `return_exceptions=True`, mescolate ai risultati | `ExceptionGroup` separato, gestibile con `except*` |
| **API** | Funzione | Context manager |

```python
import asyncio

async def operazione(id_op: int, fallisci: bool = False):
    await asyncio.sleep(0.1)
    if fallisci:
        raise ValueError(f"Errore in operazione {id_op}")
    return f"ok_{id_op}"

# --- gather: errori mescolati ai risultati ---
async def con_gather():
    risultati = await asyncio.gather(
        operazione(1),
        operazione(2, fallisci=True),
        operazione(3),
        return_exceptions=True
    )
    for r in risultati:
        if isinstance(r, Exception):
            print(f"  Errore: {r}")
        else:
            print(f"  Successo: {r}")

# --- TaskGroup: errori separati, cancellazione automatica ---
async def con_taskgroup():
    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(operazione(1))
            t2 = tg.create_task(operazione(2, fallisci=True))
            t3 = tg.create_task(operazione(3))
    except* ValueError as eg:
        for e in eg.exceptions:
            print(f"  Errore gestito: {e}")

asyncio.run(con_gather())
asyncio.run(con_taskgroup())
```

---

## asyncio.timeout (3.11+)

`asyncio.timeout()` e stato introdotto in Python 3.11 come sostituto idiomatico di `asyncio.wait_for()`. La differenza fondamentale: `timeout()` e un context manager che puo contenere piu operazioni, mentre `wait_for()` wrappa una singola coroutine.

Riferimento: [asyncio.timeout — Python docs](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.timeout)

### Context Manager Pattern

```python
import asyncio

async def fase_1():
    print("Fase 1: inizio")
    await asyncio.sleep(0.3)
    print("Fase 1: completata")
    return "dati_fase_1"

async def fase_2(dati: str):
    print(f"Fase 2: elaboro {dati}")
    await asyncio.sleep(0.3)
    print("Fase 2: completata")
    return "risultato_finale"

async def main():
    # Timeout su un blocco intero di operazioni
    try:
        async with asyncio.timeout(1.0):
            dati = await fase_1()
            risultato = await fase_2(dati)
            print(f"Risultato: {risultato}")
    except TimeoutError:
        print("Il blocco di operazioni ha superato il timeout di 1 secondo")

    # Timeout su una singola operazione
    try:
        async with asyncio.timeout(0.1):
            await asyncio.sleep(10)  # Troppo lento
    except TimeoutError:
        print("Singola operazione scaduta")

asyncio.run(main())
```

**Timeout reschedulabile** — il context manager espone un metodo `reschedule()` per modificare la deadline durante l'esecuzione:

```python
import asyncio

async def main():
    async with asyncio.timeout(1.0) as cm:
        print(f"Deadline iniziale: {cm.when():.2f}")

        await asyncio.sleep(0.5)

        # Estendi il timeout di altri 2 secondi dalla deadline corrente
        cm.reschedule(cm.when() + 2.0)
        print(f"Deadline estesa: {cm.when():.2f}")

        await asyncio.sleep(1.5)  # OK, rientra nella nuova deadline
        print("Operazione completata entro la deadline estesa")

    print(f"Timeout scaduto: {cm.expired()}")  # False

asyncio.run(main())
```

### timeout_at — Deadline Assolute

`asyncio.timeout_at()` accetta un tempo assoluto (dal clock monotono del loop) invece di un intervallo relativo.

```python
import asyncio

async def main():
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 2.0  # 2 secondi da adesso

    try:
        async with asyncio.timeout_at(deadline):
            print(f"Deadline assoluta: {deadline:.2f}")
            print(f"Tempo corrente: {loop.time():.2f}")
            await asyncio.sleep(1.0)
            print("Prima operazione completata")
            await asyncio.sleep(0.5)
            print("Seconda operazione completata")
    except TimeoutError:
        print("Deadline assoluta superata")

    # timeout_at(None) = nessun timeout
    async with asyncio.timeout_at(None):
        await asyncio.sleep(0.1)  # Nessun limite di tempo

asyncio.run(main())
```

### Confronto con wait_for

| Aspetto | `asyncio.wait_for()` | `asyncio.timeout()` |
|---------|----------------------|----------------------|
| **Versione** | Python 3.4+ | Python 3.11+ |
| **API** | Funzione, wrappa una singola coroutine | Context manager, wrappa un blocco |
| **Eccezione** | `asyncio.TimeoutError` | `TimeoutError` (built-in) |
| **Rescheduling** | No | Si, con `cm.reschedule()` |
| **Deadline assoluta** | No | Si, con `timeout_at()` |
| **Piu operazioni** | No (serve nesting) | Si, naturalmente |

```python
import asyncio

async def operazione_lenta():
    await asyncio.sleep(10)
    return "completato"

async def main():
    # Vecchio stile: wait_for
    try:
        risultato = await asyncio.wait_for(operazione_lenta(), timeout=1.0)
    except asyncio.TimeoutError:
        print("wait_for: timeout")

    # Nuovo stile: timeout context manager
    try:
        async with asyncio.timeout(1.0):
            risultato = await operazione_lenta()
    except TimeoutError:
        print("timeout(): timeout")

asyncio.run(main())
```

---

## Concorrenza con asyncio

### gather

`asyncio.gather()` e il modo piu diretto per eseguire piu coroutine in concorrenza e raccogliere i risultati. I risultati vengono restituiti nello stesso ordine in cui le coroutine sono state passate, indipendentemente dall'ordine di completamento.

```python
import asyncio
import random

async def interroga_servizio(nome_servizio):
    durata = random.uniform(0.5, 2.0)
    await asyncio.sleep(durata)
    return f"{nome_servizio}: risposta in {durata:.2f}s"

async def main():
    # Esegui tutte le chiamate in concorrenza
    risultati = await asyncio.gather(
        interroga_servizio("auth"),
        interroga_servizio("utenti"),
        interroga_servizio("prodotti"),
        interroga_servizio("ordini"),
    )
    # I risultati mantengono l'ordine originale
    for r in risultati:
        print(r)

asyncio.run(main())
```

Il parametro `return_exceptions` controlla il comportamento in caso di errore.

```python
import asyncio

async def operazione_sicura(n):
    await asyncio.sleep(0.1)
    return n * 2

async def operazione_fallimentare(n):
    await asyncio.sleep(0.1)
    raise ValueError(f"Errore con {n}")

async def main():
    # Senza return_exceptions: il primo errore interrompe gather
    try:
        risultati = await asyncio.gather(
            operazione_sicura(1),
            operazione_fallimentare(2),
            operazione_sicura(3),
        )
    except ValueError as e:
        print(f"gather interrotto: {e}")

    # Con return_exceptions=True: gli errori vengono restituiti come risultati
    risultati = await asyncio.gather(
        operazione_sicura(1),
        operazione_fallimentare(2),
        operazione_sicura(3),
        return_exceptions=True
    )
    for r in risultati:
        if isinstance(r, Exception):
            print(f"Errore: {r}")
        else:
            print(f"Successo: {r}")
    # Successo: 2
    # Errore: Errore con 2
    # Successo: 6

asyncio.run(main())
```

### wait

`asyncio.wait()` offre un controllo piu granulare rispetto a `gather`, permettendo di specificare quando restituire i risultati.

```python
import asyncio

async def operazione(nome, durata):
    await asyncio.sleep(durata)
    return f"{nome} completato"

async def main():
    tasks = [
        asyncio.create_task(operazione("A", 3), name="task_A"),
        asyncio.create_task(operazione("B", 1), name="task_B"),
        asyncio.create_task(operazione("C", 2), name="task_C"),
    ]

    # FIRST_COMPLETED: ritorna appena il primo task finisce
    completati, in_attesa = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED
    )
    print("Primo completato:")
    for t in completati:
        print(f"  {t.get_name()}: {t.result()}")
    print(f"Ancora in attesa: {len(in_attesa)} task")

    # Attendi i rimanenti
    completati, _ = await asyncio.wait(in_attesa)
    print("Tutti completati:")
    for t in completati:
        print(f"  {t.get_name()}: {t.result()}")

asyncio.run(main())
```

`asyncio.wait_for()` aggiunge un timeout a una singola coroutine.

```python
import asyncio

async def operazione_lenta():
    await asyncio.sleep(10)
    return "completato"

async def main():
    try:
        risultato = await asyncio.wait_for(
            operazione_lenta(),
            timeout=2.0
        )
    except asyncio.TimeoutError:
        print("Operazione scaduta dopo 2 secondi")

asyncio.run(main())
```

### as_completed

`asyncio.as_completed()` restituisce un iteratore che produce i risultati nell'ordine in cui le coroutine si completano, non nell'ordine in cui sono state passate. Questo e ideale quando si vogliono elaborare i risultati il prima possibile.

```python
import asyncio
import random

async def scarica_risorsa(id_risorsa):
    durata = random.uniform(0.5, 3.0)
    await asyncio.sleep(durata)
    return f"Risorsa {id_risorsa} ({durata:.2f}s)"

async def main():
    coroutines = [scarica_risorsa(i) for i in range(5)]

    # Elabora i risultati man mano che arrivano
    for coro in asyncio.as_completed(coroutines):
        risultato = await coro
        print(f"Ricevuto: {risultato}")
        # I risultati appaiono in ordine di completamento, non di creazione

asyncio.run(main())
```

### Semaphore e Lock

Le primitive di sincronizzazione in asyncio sono essenziali per controllare l'accesso concorrente alle risorse condivise.

**asyncio.Semaphore** — limita il numero di coroutine che possono accedere a una risorsa simultaneamente.

```python
import asyncio

async def accedi_api(semaforo, id_richiesta):
    async with semaforo:
        print(f"Richiesta {id_richiesta}: inizio (slot acquisito)")
        await asyncio.sleep(1)  # Simula chiamata API
        print(f"Richiesta {id_richiesta}: completata")
        return f"Risultato {id_richiesta}"

async def main():
    # Massimo 3 richieste simultanee
    semaforo = asyncio.Semaphore(3)

    tasks = [accedi_api(semaforo, i) for i in range(10)]
    risultati = await asyncio.gather(*tasks)
    print(f"Tutte {len(risultati)} richieste completate")

asyncio.run(main())
```

**asyncio.Lock** — garantisce che solo una coroutine alla volta possa accedere a una sezione critica.

```python
import asyncio

class ContoBancario:
    def __init__(self, saldo_iniziale):
        self.saldo = saldo_iniziale
        self._lock = asyncio.Lock()

    async def trasferisci(self, importo, descrizione):
        async with self._lock:
            saldo_precedente = self.saldo
            await asyncio.sleep(0.1)  # Simula latenza del database
            self.saldo += importo
            print(f"{descrizione}: {saldo_precedente} -> {self.saldo}")

async def main():
    conto = ContoBancario(1000)
    await asyncio.gather(
        conto.trasferisci(-200, "Pagamento bolletta"),
        conto.trasferisci(500, "Stipendio"),
        conto.trasferisci(-50, "Spesa supermercato"),
    )
    print(f"Saldo finale: {conto.saldo}")

asyncio.run(main())
```

**asyncio.Event** — permette a una o piu coroutine di attendere un segnale da un'altra coroutine.

```python
import asyncio

async def produttore(evento):
    print("Produttore: preparazione dati...")
    await asyncio.sleep(2)
    print("Produttore: dati pronti, segnalo l'evento")
    evento.set()

async def consumatore(evento, nome):
    print(f"Consumatore {nome}: in attesa dei dati...")
    await evento.wait()
    print(f"Consumatore {nome}: dati ricevuti, elaborazione in corso")

async def main():
    evento = asyncio.Event()
    await asyncio.gather(
        produttore(evento),
        consumatore(evento, "A"),
        consumatore(evento, "B"),
        consumatore(evento, "C"),
    )

asyncio.run(main())
```

**asyncio.Queue** — coda asincrona per lo scambio di dati tra coroutine, ideale per pattern producer-consumer.

```python
import asyncio

async def produttore(coda, id_produttore):
    for i in range(3):
        elemento = f"Prodotto-{id_produttore}-{i}"
        await coda.put(elemento)
        print(f"Produttore {id_produttore}: inserito {elemento}")
        await asyncio.sleep(0.5)

async def consumatore(coda, id_consumatore):
    while True:
        elemento = await coda.get()
        print(f"Consumatore {id_consumatore}: elaboro {elemento}")
        await asyncio.sleep(1)
        coda.task_done()

async def main():
    coda = asyncio.Queue(maxsize=5)

    # Avvia produttori e consumatori
    produttori = [
        asyncio.create_task(produttore(coda, i))
        for i in range(2)
    ]
    consumatori = [
        asyncio.create_task(consumatore(coda, i))
        for i in range(3)
    ]

    # Attendi che tutti i produttori finiscano
    await asyncio.gather(*produttori)
    # Attendi che la coda venga svuotata
    await coda.join()
    # Cancella i consumatori (loop infinito)
    for c in consumatori:
        c.cancel()

asyncio.run(main())
```

---

## Coroutine vs Generator

La relazione tra generatori e coroutine e storica. Le coroutine asincrone di Python si sono evolute dai generatori, ma oggi sono concetti distinti con semantiche diverse.

### Evoluzione: yield → yield from → async/await

```python
# --- FASE 1: Generatori (Python 2.2+, PEP 255) ---
def generatore_semplice():
    """Produce valori uno alla volta."""
    yield 1
    yield 2
    yield 3

# --- FASE 2: Generatori come coroutine (Python 2.5+, PEP 342) ---
def coroutine_vecchio_stile():
    """Riceve valori tramite send()."""
    totale = 0
    while True:
        valore = yield totale
        if valore is None:
            break
        totale += valore

# --- FASE 3: yield from (Python 3.3+, PEP 380) ---
def sotto_generatore():
    yield 1
    yield 2
    return "fine"

def generatore_delegante():
    """Delega a un sotto-generatore."""
    risultato = yield from sotto_generatore()
    print(f"Sotto-generatore ha restituito: {risultato}")

# --- FASE 4: asyncio con generatori (Python 3.4, PEP 3156) ---
import asyncio
# @asyncio.coroutine  # Deprecato in 3.8, rimosso in 3.11
# def vecchia_coroutine_asyncio():
#     yield from asyncio.sleep(1)
#     return "completato"

# --- FASE 5: async/await nativi (Python 3.5+, PEP 492) ---
async def coroutine_moderna():
    """Coroutine nativa con async/await."""
    await asyncio.sleep(1)
    return "completato"
```

### async def, await, async for, async with

Le quattro keyword asincrone di Python coprono tutti i casi d'uso:

```python
import asyncio
from contextlib import asynccontextmanager

# async def — definisce una coroutine
async def operazione():
    return 42

# await — sospende fino al completamento
async def usa_await():
    risultato = await operazione()
    print(risultato)

# async for — iterazione asincrona
async def generatore_asincrono():
    for i in range(5):
        await asyncio.sleep(0.1)
        yield i * 10

async def usa_async_for():
    async for valore in generatore_asincrono():
        print(f"Ricevuto: {valore}")

# async with — context manager asincrono
@asynccontextmanager
async def risorsa_asincrona():
    print("Acquisizione")
    yield "risorsa"
    print("Rilascio")

async def usa_async_with():
    async with risorsa_asincrona() as r:
        print(f"Uso: {r}")

async def main():
    await usa_await()
    await usa_async_for()
    await usa_async_with()

asyncio.run(main())
```

### Protocolli Asincroni: __aiter__, __anext__

Per creare iterable asincroni personalizzati, si implementano i metodi `__aiter__` e `__anext__`.

```python
import asyncio

class PaginatoreAPI:
    """Iterable asincrono che pagina automaticamente un'API."""

    def __init__(self, url_base: str, per_pagina: int = 10):
        self.url_base = url_base
        self.per_pagina = per_pagina
        self._pagina_corrente = 0
        self._esaurito = False

    def __aiter__(self):
        return self

    async def __anext__(self) -> list[dict]:
        if self._esaurito:
            raise StopAsyncIteration

        self._pagina_corrente += 1
        await asyncio.sleep(0.2)  # Simula chiamata API

        # Simula dati paginati
        if self._pagina_corrente > 3:
            self._esaurito = True
            raise StopAsyncIteration

        return [
            {"id": (self._pagina_corrente - 1) * self.per_pagina + i,
             "dato": f"elemento_{i}"}
            for i in range(self.per_pagina)
        ]

async def main():
    paginatore = PaginatoreAPI("https://api.esempio.com/items")
    async for pagina in paginatore:
        print(f"Pagina con {len(pagina)} elementi, "
              f"primo id: {pagina[0]['id']}")

asyncio.run(main())
```

---

## Streams API

L'API Streams di asyncio fornisce un'astrazione di alto livello per lavorare con connessioni di rete TCP (e Unix socket), senza dover gestire direttamente i transport e i protocol del livello basso.

Riferimento: [asyncio Streams — Python docs](https://docs.python.org/3.12/library/asyncio-stream.html)

### open_connection e start_server

```python
import asyncio

# --- CLIENT: open_connection ---
async def client_tcp():
    reader, writer = await asyncio.open_connection("httpbin.org", 80)

    # Invia richiesta HTTP minimale
    richiesta = "GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
    writer.write(richiesta.encode())
    await writer.drain()

    # Leggi la risposta
    risposta = await reader.read(4096)
    print(f"Risposta ({len(risposta)} bytes):")
    print(risposta.decode()[:200])

    writer.close()
    await writer.wait_closed()

# asyncio.run(client_tcp())
```

### StreamReader e StreamWriter

`StreamReader` fornisce metodi per leggere dati in modo asincrono, `StreamWriter` per scrivere.

```python
import asyncio

async def gestisci_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handler per ogni connessione client."""
    addr = writer.get_extra_info("peername")
    print(f"Nuova connessione da {addr}")

    try:
        while True:
            # readline() legge fino a \n
            dati = await reader.readline()
            if not dati:
                break

            messaggio = dati.decode().strip()
            print(f"[{addr}] Ricevuto: {messaggio}")

            # readexactly(n) legge esattamente n bytes
            # readuntil(separator) legge fino a un separatore

            # Rispondi al client
            risposta = f"ECHO: {messaggio}\n"
            writer.write(risposta.encode())
            await writer.drain()  # Svuota il buffer di scrittura

            if messaggio.lower() == "quit":
                break
    except asyncio.IncompleteReadError:
        print(f"[{addr}] Connessione interrotta")
    finally:
        print(f"[{addr}] Connessione chiusa")
        writer.close()
        await writer.wait_closed()
```

### Esempio: Server Echo TCP

```python
import asyncio

async def handle_echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    print(f"Connessione: {addr}")

    while True:
        dati = await reader.read(1024)
        if not dati:
            break
        writer.write(dati)
        await writer.drain()

    writer.close()
    await writer.wait_closed()
    print(f"Disconnessione: {addr}")

async def main():
    server = await asyncio.start_server(handle_echo, "127.0.0.1", 8888)
    addr = server.sockets[0].getsockname()
    print(f"Server echo in ascolto su {addr}")

    async with server:
        await server.serve_forever()

# asyncio.run(main())
```

### Esempio: Client HTTP Minimale

```python
import asyncio

async def http_get(host: str, percorso: str = "/") -> str:
    """Client HTTP/1.1 minimale usando Streams API."""
    reader, writer = await asyncio.open_connection(host, 80)

    richiesta = (
        f"GET {percorso} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n"
        f"User-Agent: PythonAsyncClient/1.0\r\n"
        f"\r\n"
    )
    writer.write(richiesta.encode())
    await writer.drain()

    # Leggi headers
    headers = {}
    while True:
        riga = await reader.readline()
        riga_dec = riga.decode().strip()
        if not riga_dec:
            break
        if ": " in riga_dec:
            chiave, valore = riga_dec.split(": ", 1)
            headers[chiave.lower()] = valore

    # Leggi body
    body = await reader.read()

    writer.close()
    await writer.wait_closed()

    return body.decode(errors="replace")

# async def main():
#     html = await http_get("example.com")
#     print(html[:500])
# asyncio.run(main())
```

---

## Queue Patterns

Le code asincrone (`asyncio.Queue`, `PriorityQueue`, `LifoQueue`) sono fondamentali per implementare pipeline di elaborazione dati, sistemi di task distribution e pattern di backpressure.

### asyncio.Queue

La coda base FIFO (First In, First Out).

```python
import asyncio

async def main():
    coda = asyncio.Queue(maxsize=0)  # 0 = illimitata

    # Operazioni base
    await coda.put("primo")
    await coda.put("secondo")

    print(f"Dimensione: {coda.qsize()}")
    print(f"Vuota: {coda.empty()}")
    print(f"Piena: {coda.full()}")  # Sempre False se maxsize=0

    elemento = await coda.get()
    print(f"Estratto: {elemento}")  # "primo"

    # get_nowait / put_nowait: non bloccanti
    coda.put_nowait("terzo")
    try:
        elemento = coda.get_nowait()
    except asyncio.QueueEmpty:
        print("Coda vuota!")

    # task_done() e join(): coordinamento producer-consumer
    coda2 = asyncio.Queue()
    await coda2.put("lavoro_1")
    await coda2.put("lavoro_2")

    # Il consumatore chiama task_done() dopo aver elaborato ogni elemento
    elemento = await coda2.get()
    coda2.task_done()
    elemento = await coda2.get()
    coda2.task_done()

    # join() ritorna quando tutti i task_done() sono stati chiamati
    await coda2.join()
    print("Tutti gli elementi elaborati")

asyncio.run(main())
```

### Producer-Consumer Avanzato

Pattern con graceful shutdown, metriche e gestione errori.

```python
import asyncio
import time
from dataclasses import dataclass, field

@dataclass
class Messaggio:
    id: int
    payload: str
    timestamp: float = field(default_factory=time.monotonic)
    tentativi: int = 0
    max_tentativi: int = 3

class PipelineRobusta:
    """Pipeline producer-consumer con retry, DLQ e metriche."""

    def __init__(self, max_concorrenza: int = 5, dimensione_coda: int = 100):
        self.coda_lavoro = asyncio.Queue(maxsize=dimensione_coda)
        self.coda_dlq = asyncio.Queue()  # Dead Letter Queue
        self.semaforo = asyncio.Semaphore(max_concorrenza)
        self.elaborati = 0
        self.falliti = 0
        self._in_esecuzione = True

    async def produci(self, messaggi: list[Messaggio]):
        for msg in messaggi:
            await self.coda_lavoro.put(msg)
        print(f"Prodotti {len(messaggi)} messaggi")

    async def consuma(self, id_worker: int):
        while self._in_esecuzione:
            try:
                msg = await asyncio.wait_for(
                    self.coda_lavoro.get(), timeout=2.0
                )
            except asyncio.TimeoutError:
                continue

            async with self.semaforo:
                try:
                    await self._elabora(msg, id_worker)
                    self.elaborati += 1
                except Exception as e:
                    msg.tentativi += 1
                    if msg.tentativi < msg.max_tentativi:
                        await self.coda_lavoro.put(msg)  # Retry
                        print(f"Worker {id_worker}: retry {msg.id} "
                              f"(tentativo {msg.tentativi})")
                    else:
                        await self.coda_dlq.put((msg, str(e)))
                        self.falliti += 1
                        print(f"Worker {id_worker}: DLQ per {msg.id}")
                finally:
                    self.coda_lavoro.task_done()

    async def _elabora(self, msg: Messaggio, id_worker: int):
        await asyncio.sleep(0.1)  # Simula elaborazione
        if msg.id % 7 == 0:
            raise ValueError(f"Errore elaborazione {msg.id}")
        print(f"Worker {id_worker}: elaborato {msg.id}")

    async def esegui(self, messaggi: list[Messaggio], n_workers: int = 3):
        workers = [
            asyncio.create_task(self.consuma(i))
            for i in range(n_workers)
        ]
        await self.produci(messaggi)
        await self.coda_lavoro.join()
        self._in_esecuzione = False

        for w in workers:
            w.cancel()

        print(f"\nRiepilogo: {self.elaborati} elaborati, "
              f"{self.falliti} in DLQ, "
              f"{self.coda_dlq.qsize()} nella dead letter queue")

async def main():
    pipeline = PipelineRobusta(max_concorrenza=3)
    messaggi = [Messaggio(id=i, payload=f"dati_{i}") for i in range(20)]
    await pipeline.esegui(messaggi, n_workers=4)

asyncio.run(main())
```

### PriorityQueue e LifoQueue

```python
import asyncio

async def main():
    # PriorityQueue: estrae sempre l'elemento con priorita piu bassa
    pq = asyncio.PriorityQueue()
    await pq.put((3, "bassa priorita"))
    await pq.put((1, "alta priorita"))
    await pq.put((2, "media priorita"))

    while not pq.empty():
        priorita, messaggio = await pq.get()
        print(f"Priorita {priorita}: {messaggio}")
    # Output: alta, media, bassa

    # LifoQueue: stack (Last In, First Out)
    lifo = asyncio.LifoQueue()
    await lifo.put("primo")
    await lifo.put("secondo")
    await lifo.put("terzo")

    while not lifo.empty():
        print(await lifo.get())
    # Output: terzo, secondo, primo

asyncio.run(main())
```

### Bounded Queue e Backpressure

Le code limitate (`maxsize > 0`) implementano automaticamente backpressure: quando la coda e piena, `put()` blocca il produttore fino a che non si libera spazio.

```python
import asyncio
import time

async def produttore_veloce(coda: asyncio.Queue, n_elementi: int):
    for i in range(n_elementi):
        inizio = time.monotonic()
        await coda.put(f"elemento_{i}")
        attesa = time.monotonic() - inizio
        if attesa > 0.01:
            print(f"Produttore rallentato: {attesa:.3f}s di backpressure "
                  f"(coda piena, elemento {i})")
        await asyncio.sleep(0.01)  # Produzione veloce

async def consumatore_lento(coda: asyncio.Queue, id_cons: int):
    while True:
        elemento = await coda.get()
        await asyncio.sleep(0.2)  # Consumo lento
        coda.task_done()
        print(f"Consumatore {id_cons}: {elemento}")

async def main():
    # maxsize=5: la coda accetta al massimo 5 elementi
    coda = asyncio.Queue(maxsize=5)

    consumatori = [
        asyncio.create_task(consumatore_lento(coda, i))
        for i in range(2)
    ]

    await produttore_veloce(coda, 15)
    await coda.join()

    for c in consumatori:
        c.cancel()

asyncio.run(main())
```

---

## Primitive di Sincronizzazione

Oltre a Lock, Event, Semaphore e Queue gia trattate nella sezione Concorrenza, asyncio offre primitive aggiuntive per scenari di coordinamento piu complessi.

### Lock e RLock Equivalente

asyncio non ha un `RLock` nativo (un lock rientrante non ha senso nel modello cooperativo single-threaded, perche una coroutine non puo acquisire un lock mentre lo detiene gia — il suo flusso e lineare tra i punti di `await`). Se si necessita di un pattern simile, si puo usare un flag booleano.

```python
import asyncio

class RisorsaCondivisa:
    """Esempio di accesso serializzato con Lock."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._dati = {}

    async def aggiorna(self, chiave: str, valore):
        async with self._lock:
            vecchio = self._dati.get(chiave)
            await asyncio.sleep(0.05)  # Simula I/O
            self._dati[chiave] = valore
            return vecchio

    async def leggi(self, chiave: str):
        async with self._lock:
            return self._dati.get(chiave)

    # Operazione composta sotto lock
    async def incrementa(self, chiave: str, delta: int = 1):
        async with self._lock:
            corrente = self._dati.get(chiave, 0)
            await asyncio.sleep(0.01)
            self._dati[chiave] = corrente + delta
            return self._dati[chiave]
```

### Semaphore e BoundedSemaphore

`BoundedSemaphore` impedisce di rilasciare il semaforo piu volte di quante lo si sia acquisito.

```python
import asyncio

async def main():
    # Semaphore: il contatore puo salire sopra il valore iniziale
    sem = asyncio.Semaphore(2)

    # BoundedSemaphore: solleva ValueError se release() > acquire()
    bsem = asyncio.BoundedSemaphore(2)

    async with bsem:
        async with bsem:
            print("Entrambi gli slot acquisiti")
        print("Un slot rilasciato")

    # Questo solleverebbe ValueError con BoundedSemaphore:
    # bsem.release()  # ValueError: BoundedSemaphore released too many times

asyncio.run(main())
```

### Condition

`asyncio.Condition` combina Lock e notifica, permettendo a coroutine di attendere che una condizione specifica sia soddisfatta.

```python
import asyncio

async def main():
    coda = []
    condition = asyncio.Condition()

    async def consumatore(nome: str):
        async with condition:
            # Attendi finche la coda non ha almeno 3 elementi
            await condition.wait_for(lambda: len(coda) >= 3)
            print(f"{nome}: coda ha {len(coda)} elementi, procedo")
            elemento = coda.pop(0)
            print(f"{nome}: consumato {elemento}")

    async def produttore():
        for i in range(5):
            await asyncio.sleep(0.2)
            async with condition:
                coda.append(f"item_{i}")
                print(f"Produttore: aggiunto item_{i}, coda={len(coda)}")
                condition.notify_all()  # Sveglia tutti i consumatori in attesa

    await asyncio.gather(
        consumatore("C1"),
        consumatore("C2"),
        produttore()
    )

asyncio.run(main())
```

### Barrier (3.11+)

`asyncio.Barrier` (introdotta in Python 3.11) sincronizza un numero fisso di coroutine: tutte devono raggiungere la barriera prima che qualsiasi possa proseguire.

```python
import asyncio

async def worker_sincronizzato(barrier: asyncio.Barrier, id_worker: int):
    print(f"Worker {id_worker}: preparazione...")
    await asyncio.sleep(id_worker * 0.2)  # Tempo variabile

    print(f"Worker {id_worker}: raggiunta la barriera, attendo gli altri")
    await barrier.wait()

    # Tutti i worker raggiungono questo punto contemporaneamente
    print(f"Worker {id_worker}: barriera superata, procedo!")

async def main():
    n_workers = 4
    barrier = asyncio.Barrier(n_workers)

    async with asyncio.TaskGroup() as tg:
        for i in range(n_workers):
            tg.create_task(worker_sincronizzato(barrier, i))

    print("Tutti i worker hanno completato")

asyncio.run(main())
```

---

## Async Context Manager

### Protocollo __aenter__ / __aexit__

Un async context manager implementa i metodi `__aenter__` e `__aexit__` come coroutine.

```python
import asyncio
import time

class PoolConnessioni:
    """Pool di connessioni con async context manager."""

    def __init__(self, url: str, dimensione: int = 5):
        self.url = url
        self.dimensione = dimensione
        self._connessioni: list = []
        self._semaforo = asyncio.Semaphore(dimensione)

    async def __aenter__(self):
        print(f"Inizializzazione pool ({self.dimensione} connessioni)...")
        for i in range(self.dimensione):
            await asyncio.sleep(0.05)  # Simula setup connessione
            self._connessioni.append(f"conn_{i}")
        print("Pool pronto")
        return self

    async def __aexit__(self, tipo_exc, valore_exc, traceback):
        print("Chiusura pool...")
        for conn in self._connessioni:
            await asyncio.sleep(0.02)  # Simula chiusura connessione
        self._connessioni.clear()
        print("Pool chiuso")
        return False  # Non sopprimere eccezioni

    async def esegui(self, query: str):
        async with self._semaforo:
            conn = self._connessioni[0]  # Semplificato
            await asyncio.sleep(0.05)
            return f"[{conn}] Risultato di: {query}"

async def main():
    async with PoolConnessioni("postgresql://localhost/db") as pool:
        risultati = await asyncio.gather(
            pool.esegui("SELECT 1"),
            pool.esegui("SELECT 2"),
            pool.esegui("SELECT 3"),
        )
        for r in risultati:
            print(r)

asyncio.run(main())
```

### @asynccontextmanager

Il decoratore `@asynccontextmanager` da `contextlib` semplifica la creazione.

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def transazione(nome: str):
    """Context manager per transazioni con rollback automatico."""
    print(f"[{nome}] BEGIN TRANSACTION")
    stato = {"committata": False}
    try:
        yield stato
        print(f"[{nome}] COMMIT")
        stato["committata"] = True
    except Exception as e:
        print(f"[{nome}] ROLLBACK (errore: {e})")
        raise
    finally:
        if not stato["committata"]:
            print(f"[{nome}] Cleanup post-rollback")

async def main():
    # Transazione riuscita
    async with transazione("tx_1") as stato:
        await asyncio.sleep(0.1)
        print("Operazione completata")

    # Transazione fallita
    try:
        async with transazione("tx_2") as stato:
            await asyncio.sleep(0.1)
            raise ValueError("Errore dati")
    except ValueError:
        print("Errore gestito")

asyncio.run(main())
```

### Pattern Compositi

Combinare piu context manager asincroni.

```python
import asyncio
from contextlib import asynccontextmanager, AsyncExitStack

@asynccontextmanager
async def risorsa(nome: str):
    print(f"  Acquisisco {nome}")
    await asyncio.sleep(0.05)
    try:
        yield nome
    finally:
        print(f"  Rilascio {nome}")
        await asyncio.sleep(0.02)

async def main():
    # AsyncExitStack: gestisci un numero dinamico di context manager
    async with AsyncExitStack() as stack:
        nomi_risorse = ["db", "cache", "queue", "lock"]
        risorse = []
        for nome in nomi_risorse:
            r = await stack.enter_async_context(risorsa(nome))
            risorse.append(r)
        print(f"Tutte le risorse acquisite: {risorse}")
        # Uso delle risorse...
    # Tutte rilasciate in ordine inverso (LIFO)

asyncio.run(main())
```

---

## Async I/O Pratico

### HTTP con aiohttp

`aiohttp` e la libreria di riferimento per eseguire richieste HTTP asincrone in Python. Supporta sia il ruolo client che server, con connection pooling integrato tramite `ClientSession`.

```python
import asyncio
import aiohttp

async def esempio_base():
    async with aiohttp.ClientSession() as session:
        # GET request
        async with session.get("https://httpbin.org/get") as risposta:
            dati = await risposta.json()
            print(f"Status: {risposta.status}")
            print(f"Content-Type: {risposta.headers['Content-Type']}")

        # POST request con JSON
        payload = {"nome": "Mario", "citta": "Roma"}
        async with session.post(
            "https://httpbin.org/post",
            json=payload
        ) as risposta:
            dati = await risposta.json()
            print(f"Dati inviati: {dati['json']}")

asyncio.run(esempio_base())
```

**Richieste HTTP concorrenti con rate limiting** — pattern fondamentale per chiamate batch a API esterne.

```python
import asyncio
import aiohttp
from dataclasses import dataclass

@dataclass
class RisultatoAPI:
    url: str
    status: int
    dati: dict | None
    errore: str | None = None

async def chiama_api(
    session: aiohttp.ClientSession,
    url: str,
    semaforo: asyncio.Semaphore,
    max_tentativi: int = 3
) -> RisultatoAPI:
    """Chiamata API con rate limiting, retry e gestione errori."""
    async with semaforo:
        for tentativo in range(max_tentativi):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as risposta:
                    if risposta.status == 429:  # Too Many Requests
                        attesa = int(risposta.headers.get("Retry-After", 2))
                        print(f"Rate limit raggiunto, attendo {attesa}s...")
                        await asyncio.sleep(attesa)
                        continue

                    if risposta.status == 200:
                        dati = await risposta.json()
                        return RisultatoAPI(url=url, status=200, dati=dati)
                    else:
                        return RisultatoAPI(
                            url=url,
                            status=risposta.status,
                            dati=None,
                            errore=f"HTTP {risposta.status}"
                        )
            except asyncio.TimeoutError:
                if tentativo < max_tentativi - 1:
                    await asyncio.sleep(2 ** tentativo)  # Backoff esponenziale
                    continue
                return RisultatoAPI(
                    url=url, status=0, dati=None, errore="Timeout"
                )
            except aiohttp.ClientError as e:
                return RisultatoAPI(
                    url=url, status=0, dati=None, errore=str(e)
                )

    return RisultatoAPI(url=url, status=0, dati=None, errore="Max tentativi esauriti")

async def batch_api_calls(urls: list[str], max_concorrenza: int = 10):
    """Esegue chiamate API in batch con concorrenza limitata."""
    semaforo = asyncio.Semaphore(max_concorrenza)

    async with aiohttp.ClientSession() as session:
        tasks = [chiama_api(session, url, semaforo) for url in urls]
        risultati = await asyncio.gather(*tasks)

    successi = [r for r in risultati if r.errore is None]
    errori = [r for r in risultati if r.errore is not None]
    print(f"Completato: {len(successi)} successi, {len(errori)} errori")
    return risultati

# Esempio di utilizzo
async def main():
    urls = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 51)]
    risultati = await batch_api_calls(urls, max_concorrenza=5)

asyncio.run(main())
```

### File I/O con aiofiles

`aiofiles` fornisce un'interfaccia asincrona per operazioni su file. E utile in contesti dove il programma gestisce molte operazioni I/O concorrenti e non si vuole bloccare l'event loop durante la lettura o scrittura di file.

```python
import asyncio
import aiofiles
import json

async def scrivi_file_asincrono(percorso, contenuto):
    async with aiofiles.open(percorso, mode='w', encoding='utf-8') as f:
        await f.write(contenuto)
    print(f"File scritto: {percorso}")

async def leggi_file_asincrono(percorso):
    async with aiofiles.open(percorso, mode='r', encoding='utf-8') as f:
        contenuto = await f.read()
    return contenuto

async def elabora_file_json(percorso_input, percorso_output):
    """Legge un file JSON, elabora i dati e scrive il risultato."""
    async with aiofiles.open(percorso_input, 'r') as f:
        contenuto = await f.read()
        dati = json.loads(contenuto)

    # Elaborazione dei dati
    dati_elaborati = {k: v.upper() if isinstance(v, str) else v
                      for k, v in dati.items()}

    async with aiofiles.open(percorso_output, 'w') as f:
        await f.write(json.dumps(dati_elaborati, indent=2))

async def leggi_file_per_righe(percorso):
    """Lettura riga per riga, utile per file di grandi dimensioni."""
    righe_totali = 0
    async with aiofiles.open(percorso, 'r') as f:
        async for riga in f:
            righe_totali += 1
            # Elabora ogni riga
    return righe_totali
```

Nota importante: per la maggior parte delle applicazioni, le operazioni su file locale sono abbastanza veloci da non richiedere I/O asincrono. `aiofiles` diventa realmente utile quando si combinano operazioni su file con altre operazioni I/O asincrone (ad esempio, scaricare dati dalla rete e salvarli su disco) all'interno dello stesso event loop.

### Database Asincrono

I driver di database asincroni permettono di eseguire query senza bloccare l'event loop, fondamentale per applicazioni web ad alto throughput.

**asyncpg (PostgreSQL)** — driver nativo asincrono ad alte prestazioni.

```python
import asyncio
import asyncpg

async def esempio_asyncpg():
    # Connection pool per gestire piu connessioni
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='utente',
        password='password',
        database='mio_db',
        min_size=5,
        max_size=20
    )

    async with pool.acquire() as conn:
        # Query singola
        riga = await conn.fetchrow(
            'SELECT id, nome, email FROM utenti WHERE id = $1', 42
        )
        print(f"Utente: {riga['nome']} ({riga['email']})")

        # Query multipla
        righe = await conn.fetch(
            'SELECT * FROM ordini WHERE utente_id = $1 ORDER BY data DESC',
            42
        )
        for riga in righe:
            print(f"Ordine {riga['id']}: {riga['totale']}")

        # Inserimento con ritorno dell'ID
        nuovo_id = await conn.fetchval(
            'INSERT INTO utenti(nome, email) VALUES($1, $2) RETURNING id',
            'Luigi', 'luigi@esempio.it'
        )

        # Transazione
        async with conn.transaction():
            await conn.execute(
                'UPDATE conti SET saldo = saldo - $1 WHERE id = $2',
                100.0, 1
            )
            await conn.execute(
                'UPDATE conti SET saldo = saldo + $1 WHERE id = $2',
                100.0, 2
            )

    await pool.close()

asyncio.run(esempio_asyncpg())
```

**aiosqlite** — wrapper asincrono per SQLite.

```python
import asyncio
import aiosqlite

async def esempio_aiosqlite():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS prodotti (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                prezzo REAL NOT NULL
            )
        """)

        await db.execute(
            "INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)",
            ("Espresso", 1.50)
        )
        await db.commit()

        async with db.execute("SELECT * FROM prodotti") as cursore:
            async for riga in cursore:
                print(f"Prodotto: {riga[1]} - {riga[2]}EUR")

asyncio.run(esempio_aiosqlite())
```

**SQLAlchemy 2.0+ async** — ORM asincrono completo.

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, String

class Base(DeclarativeBase):
    pass

class Utente(Base):
    __tablename__ = "utenti"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)

async def esempio_sqlalchemy_async():
    engine = create_async_engine(
        "postgresql+asyncpg://utente:password@localhost/mio_db",
        pool_size=10,
        max_overflow=20
    )

    async_session = async_sessionmaker(engine, class_=AsyncSession)

    # Creare le tabelle
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Operazioni CRUD
    async with async_session() as session:
        # Create
        nuovo_utente = Utente(nome="Anna", email="anna@esempio.it")
        session.add(nuovo_utente)
        await session.commit()

        # Read
        stmt = select(Utente).where(Utente.nome == "Anna")
        risultato = await session.execute(stmt)
        utente = risultato.scalar_one()
        print(f"Trovato: {utente.nome} ({utente.email})")

    await engine.dispose()

asyncio.run(esempio_sqlalchemy_async())
```

---

## aiohttp vs httpx

Due librerie dominanti per HTTP asincrono in Python, con filosofie diverse.

### Architettura e Design

| Aspetto | aiohttp | httpx |
|---------|---------|-------|
| **Modello** | Solo asyncio | Sync + async (stesso API) |
| **Server integrato** | Si (aiohttp.web) | No |
| **WebSocket** | Si (nativo) | No (serve websockets) |
| **HTTP/2** | No | Si |
| **API** | Specifica aiohttp | Compatibile con requests |
| **Dipendenze** | multidict, yarl, aiosignal | httpcore, anyio, certifi |
| **Streaming** | Si | Si |

### Performance e Compatibilita

```python
# --- aiohttp: alta performance, API propria ---
import aiohttp
import asyncio

async def con_aiohttp():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://httpbin.org/get") as resp:
            dati = await resp.json()
            print(f"aiohttp status: {resp.status}")

# --- httpx: API compatibile con requests, HTTP/2 ---
import httpx

async def con_httpx():
    async with httpx.AsyncClient(http2=True) as client:
        resp = await client.get("https://httpbin.org/get")
        dati = resp.json()
        print(f"httpx status: {resp.status_code}")

# httpx offre anche un client sincrono con la stessa API
def httpx_sincrono():
    with httpx.Client() as client:
        resp = client.get("https://httpbin.org/get")
        print(f"httpx sync status: {resp.status_code}")
```

### Migrazione da aiohttp a httpx

```python
import httpx

# Equivalenze principali:
#   aiohttp.ClientSession()       → httpx.AsyncClient()
#   session.get(url)              → client.get(url)
#   resp.status                   → resp.status_code
#   await resp.json()             → resp.json()  (non serve await)
#   await resp.text()             → resp.text     (proprieta, non metodo)
#   await resp.read()             → resp.content  (proprieta, non metodo)
#   aiohttp.ClientTimeout(total=) → httpx.Timeout(timeout=)
#   session.post(url, json=...)   → client.post(url, json=...)

async def esempio_httpx_avanzato():
    timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
        http2=True,
    ) as client:
        # Richiesta con headers personalizzati
        resp = await client.get(
            "https://httpbin.org/get",
            headers={"X-Custom": "valore"}
        )
        print(f"Status: {resp.status_code}")
        print(f"HTTP version: {resp.http_version}")

# asyncio.run(esempio_httpx_avanzato())
```

**Quando scegliere quale:**

- **aiohttp**: server web asincrono integrato, WebSocket, ecosistema consolidato, massima performance I/O.
- **httpx**: HTTP/2, stessa API sync/async, migrazione facile da requests, testing piu semplice.

---

## Database Asincrono Avanzato

### asyncpg — Deep Dive

Pattern avanzati con asyncpg: prepared statements, copy, listeners, custom types.

```python
import asyncio
import asyncpg

async def asyncpg_avanzato():
    pool = await asyncpg.create_pool(
        "postgresql://utente:password@localhost/db",
        min_size=5,
        max_size=20,
        command_timeout=30,
    )

    async with pool.acquire() as conn:
        # Prepared statements: compilati una volta, eseguiti molte
        stmt = await conn.prepare(
            "SELECT id, nome FROM utenti WHERE citta = $1 LIMIT $2"
        )
        righe = await stmt.fetch("Roma", 10)
        for r in righe:
            print(f"  {r['id']}: {r['nome']}")

        # COPY: bulk insert ad alte prestazioni
        dati = [(f"utente_{i}", f"utente_{i}@mail.it") for i in range(1000)]
        await conn.copy_records_to_table(
            "utenti",
            records=dati,
            columns=["nome", "email"]
        )

        # LISTEN/NOTIFY: pub/sub tramite PostgreSQL
        async def on_notifica(conn, pid, canale, payload):
            print(f"Notifica su {canale}: {payload}")

        await conn.add_listener("aggiornamenti", on_notifica)
        # Da un'altra sessione: NOTIFY aggiornamenti, 'nuovo ordine'

    await pool.close()

# asyncio.run(asyncpg_avanzato())
```

### SQLAlchemy Async — Pattern Avanzati

```python
import asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import select, String, ForeignKey, func

class Base(DeclarativeBase):
    pass

class Autore(Base):
    __tablename__ = "autori"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    libri: Mapped[list["Libro"]] = relationship(back_populates="autore")

class Libro(Base):
    __tablename__ = "libri"
    id: Mapped[int] = mapped_column(primary_key=True)
    titolo: Mapped[str] = mapped_column(String(200))
    autore_id: Mapped[int] = mapped_column(ForeignKey("autori.id"))
    autore: Mapped["Autore"] = relationship(back_populates="libri")

async def pattern_sqlalchemy():
    engine = create_async_engine(
        "postgresql+asyncpg://utente:password@localhost/db",
        pool_size=10,
        pool_pre_ping=True,  # Verifica connessioni stale
    )
    Session = async_sessionmaker(engine, class_=AsyncSession)

    async with Session() as session:
        # Eager loading con selectinload
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Autore)
            .options(selectinload(Autore.libri))
            .where(Autore.nome.ilike("%rossi%"))
        )
        result = await session.execute(stmt)
        autori = result.scalars().all()

        # Aggregazione
        stmt_count = (
            select(Autore.nome, func.count(Libro.id).label("n_libri"))
            .join(Libro)
            .group_by(Autore.nome)
            .having(func.count(Libro.id) > 3)
        )
        result = await session.execute(stmt_count)
        for nome, n in result:
            print(f"{nome}: {n} libri")

    await engine.dispose()

# asyncio.run(pattern_sqlalchemy())
```

### Connection Pooling Asincrono

Principi di dimensionamento del pool:

```python
# Formula di base per il pool size:
# pool_size = num_worker_concorrenti * query_per_richiesta
#
# Esempio: 50 richieste concorrenti, 2 query per richiesta
# pool_size = 50 * 2 = 100 (con margine: ~120)
#
# Regola pratica: max_connections del DB / numero di istanze dell'app

import asyncpg

async def pool_configurato():
    pool = await asyncpg.create_pool(
        dsn="postgresql://utente:password@localhost/db",
        min_size=5,         # Connessioni mantenute sempre aperte
        max_size=20,        # Massimo connessioni totali
        max_inactive_connection_lifetime=300,  # Chiudi connessioni idle dopo 5min
        command_timeout=30,  # Timeout per singola query
    )

    # Monitoraggio del pool
    print(f"Connessioni libere: {pool.get_idle_size()}")
    print(f"Connessioni totali: {pool.get_size()}")
    print(f"Dimensione min: {pool.get_min_size()}")
    print(f"Dimensione max: {pool.get_max_size()}")

    await pool.close()

# asyncio.run(pool_configurato())
```

---

## Async Generator e Context Manager

Gli async generator e gli async context manager estendono i pattern familiari di Python al mondo asincrono, permettendo di scrivere codice elegante che combina iterazione e gestione delle risorse con operazioni I/O non bloccanti.

**async for** — iterazione asincrona su sequenze prodotte da async generator o async iterable.

```python
import asyncio

async def genera_dati_da_api(pagine):
    """Async generator che simula la paginazione di un'API."""
    for pagina in range(1, pagine + 1):
        await asyncio.sleep(0.5)  # Simula chiamata API
        dati = [f"elemento_{pagina}_{i}" for i in range(3)]
        yield dati

async def main():
    # async for itera sui risultati man mano che arrivano
    async for batch in genera_dati_da_api(5):
        print(f"Ricevuto batch: {batch}")
        # Elabora ogni batch immediatamente

asyncio.run(main())
```

**async with** — context manager asincrono per la gestione di risorse che richiedono setup e teardown asincroni.

```python
import asyncio
from contextlib import asynccontextmanager

class ConnessioneDatabase:
    """Esempio di context manager asincrono implementato con protocollo."""

    def __init__(self, url):
        self.url = url
        self.connessione = None

    async def __aenter__(self):
        print(f"Connessione a {self.url}...")
        await asyncio.sleep(0.3)  # Simula connessione
        self.connessione = f"conn_{id(self)}"
        print(f"Connesso: {self.connessione}")
        return self

    async def __aexit__(self, tipo_exc, valore_exc, traceback):
        print(f"Chiusura connessione {self.connessione}...")
        await asyncio.sleep(0.1)  # Simula chiusura
        self.connessione = None
        print("Connessione chiusa")
        return False  # Non sopprimere eccezioni

    async def esegui_query(self, query):
        await asyncio.sleep(0.2)
        return f"Risultato di '{query}'"

async def main():
    async with ConnessioneDatabase("postgresql://localhost/db") as db:
        risultato = await db.esegui_query("SELECT * FROM utenti")
        print(risultato)
    # La connessione viene chiusa automaticamente

asyncio.run(main())
```

**@asynccontextmanager** — decoratore per creare context manager asincroni in modo conciso.

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def sessione_temporanea(nome_risorsa):
    """Context manager asincrono creato con il decoratore."""
    print(f"Acquisizione risorsa: {nome_risorsa}")
    await asyncio.sleep(0.2)
    risorsa = {"nome": nome_risorsa, "attiva": True}
    try:
        yield risorsa
    finally:
        print(f"Rilascio risorsa: {nome_risorsa}")
        risorsa["attiva"] = False
        await asyncio.sleep(0.1)

@asynccontextmanager
async def timer_operazione(nome):
    """Misura il tempo di esecuzione di un blocco asincrono."""
    import time
    inizio = time.perf_counter()
    try:
        yield
    finally:
        durata = time.perf_counter() - inizio
        print(f"{nome}: completato in {durata:.3f}s")

async def main():
    async with sessione_temporanea("cache_redis") as risorsa:
        print(f"Uso risorsa: {risorsa}")

    async with timer_operazione("Batch di richieste"):
        await asyncio.gather(
            asyncio.sleep(0.5),
            asyncio.sleep(0.3),
            asyncio.sleep(0.7),
        )

asyncio.run(main())
```

**Async generator con yield** — combinazione di generatore e operazioni asincrone.

```python
import asyncio

async def stream_eventi(sorgente, max_eventi=10):
    """Async generator che simula uno stream di eventi."""
    for i in range(max_eventi):
        await asyncio.sleep(0.3)
        evento = {
            "id": i,
            "sorgente": sorgente,
            "timestamp": asyncio.get_event_loop().time()
        }
        yield evento

async def filtra_e_trasforma(stream_asincrono):
    """Async generator che filtra e trasforma uno stream."""
    async for evento in stream_asincrono:
        if evento["id"] % 2 == 0:  # Filtra solo eventi pari
            evento["elaborato"] = True
            yield evento

async def main():
    stream = stream_eventi("sensore_temperatura", max_eventi=8)
    async for evento in filtra_e_trasforma(stream):
        print(f"Evento elaborato: {evento}")

asyncio.run(main())
```

---

## Threading vs Multiprocessing vs Asyncio

La scelta tra threading, multiprocessing e asyncio dipende dalla natura del problema. Questa sezione analizza ciascun approccio in dettaglio, evidenziando quando e perche utilizzarli.

### threading

Il modulo `threading` permette di eseguire piu thread all'interno dello stesso processo. Ogni thread condivide lo stesso spazio di memoria, il che rende la comunicazione tra thread semplice ma richiede attenzione per evitare race condition.

```python
import threading
import time

def scarica_file(nome_file, durata):
    """Simula il download di un file."""
    thread_corrente = threading.current_thread().name
    print(f"[{thread_corrente}] Inizio download: {nome_file}")
    time.sleep(durata)
    print(f"[{thread_corrente}] Completato: {nome_file}")

# Creazione e avvio dei thread
threads = []
files = [("report.pdf", 3), ("dati.csv", 1), ("immagine.png", 2)]

for nome, durata in files:
    t = threading.Thread(target=scarica_file, args=(nome, durata), daemon=True)
    threads.append(t)
    t.start()

# Attendi il completamento di tutti i thread
for t in threads:
    t.join()

print("Tutti i download completati")
```

**Primitive di sincronizzazione** — fondamentali per evitare race condition.

```python
import threading
import time

class ContatoreSicuro:
    """Contatore thread-safe usando Lock."""

    def __init__(self):
        self.valore = 0
        self._lock = threading.Lock()

    def incrementa(self, n=1):
        with self._lock:
            corrente = self.valore
            time.sleep(0.001)  # Simula elaborazione
            self.valore = corrente + n

    def ottieni(self):
        with self._lock:
            return self.valore

# RLock: rientrante, puo essere acquisito piu volte dallo stesso thread
class Cache:
    def __init__(self):
        self._dati = {}
        self._lock = threading.RLock()

    def imposta(self, chiave, valore):
        with self._lock:
            self._dati[chiave] = valore
            self._log(f"Impostato {chiave}")  # Usa lo stesso lock

    def _log(self, messaggio):
        with self._lock:  # RLock permette riacquisizione
            print(f"[Cache] {messaggio}")

# Event: segnalazione tra thread
def lavoratore(evento, id_lavoratore):
    print(f"Lavoratore {id_lavoratore}: attendo il segnale...")
    evento.wait()
    print(f"Lavoratore {id_lavoratore}: segnale ricevuto, inizio lavoro")

evento = threading.Event()
for i in range(3):
    threading.Thread(target=lavoratore, args=(evento, i)).start()

time.sleep(1)
print("Invio segnale a tutti i lavoratori")
evento.set()

# Semaphore: limita l'accesso concorrente
semaforo = threading.Semaphore(3)

def accedi_risorsa(id_thread):
    with semaforo:
        print(f"Thread {id_thread}: accesso alla risorsa")
        time.sleep(1)
        print(f"Thread {id_thread}: rilascio risorsa")
```

**ThreadPoolExecutor** — interfaccia ad alto livello per la gestione di pool di thread.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def elabora_dato(dato):
    time.sleep(1)
    return dato * 2

# Con context manager per gestione automatica del pool
with ThreadPoolExecutor(max_workers=4) as executor:
    dati = range(10)
    risultati = list(executor.map(elabora_dato, dati))
    print(f"Risultati: {risultati}")
```

### multiprocessing

Il modulo `multiprocessing` crea processi separati, ciascuno con il proprio interprete Python e la propria memoria. Questo aggira completamente il GIL, permettendo vero parallelismo su CPU multicore.

```python
import multiprocessing
import time
import os

def calcolo_intensivo(n):
    """Funzione CPU-bound: calcola i numeri primi fino a n."""
    pid = os.getpid()
    primi = []
    for num in range(2, n):
        if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
            primi.append(num)
    print(f"[PID {pid}] Trovati {len(primi)} primi fino a {n}")
    return len(primi)

if __name__ == "__main__":
    # Creazione di processi individuali
    processi = []
    for n in [50000, 60000, 70000, 80000]:
        p = multiprocessing.Process(target=calcolo_intensivo, args=(n,))
        processi.append(p)
        p.start()

    for p in processi:
        p.join()

    # Uso di Pool per distribuire il lavoro
    with multiprocessing.Pool(processes=4) as pool:
        numeri = [50000, 60000, 70000, 80000]
        risultati = pool.map(calcolo_intensivo, numeri)
        print(f"Risultati: {risultati}")
```

**Comunicazione tra processi** — Queue e Pipe per lo scambio di dati.

```python
import multiprocessing
import time

def produttore(coda, id_produttore):
    for i in range(5):
        elemento = f"P{id_produttore}-{i}"
        coda.put(elemento)
        time.sleep(0.1)
    coda.put(None)  # Segnale di terminazione

def consumatore(coda, id_consumatore):
    while True:
        elemento = coda.get()
        if elemento is None:
            break
        print(f"Consumatore {id_consumatore}: elaborato {elemento}")

if __name__ == "__main__":
    coda = multiprocessing.Queue()

    prod = multiprocessing.Process(target=produttore, args=(coda, 1))
    cons = multiprocessing.Process(target=consumatore, args=(coda, 1))

    prod.start()
    cons.start()

    prod.join()
    cons.join()
```

**Shared Memory (Python 3.8+)** — per condividere dati tra processi senza serializzazione.

```python
from multiprocessing import shared_memory, Process
import numpy as np

def elabora_segmento(nome_shm, forma, dtype, inizio, fine):
    """Elabora un segmento dell'array in shared memory."""
    shm = shared_memory.SharedMemory(name=nome_shm)
    array = np.ndarray(forma, dtype=dtype, buffer=shm.buf)
    array[inizio:fine] *= 2  # Raddoppia i valori nel segmento
    shm.close()

if __name__ == "__main__":
    dati = np.arange(1000, dtype=np.float64)
    shm = shared_memory.SharedMemory(create=True, size=dati.nbytes)
    array_condiviso = np.ndarray(dati.shape, dtype=dati.dtype, buffer=shm.buf)
    array_condiviso[:] = dati[:]

    processi = []
    dimensione_segmento = 250
    for i in range(4):
        p = Process(
            target=elabora_segmento,
            args=(shm.name, dati.shape, dati.dtype,
                  i * dimensione_segmento, (i + 1) * dimensione_segmento)
        )
        processi.append(p)
        p.start()

    for p in processi:
        p.join()

    print(f"Primi 10 valori: {array_condiviso[:10]}")
    shm.close()
    shm.unlink()
```

### concurrent.futures

Il modulo `concurrent.futures` fornisce un'interfaccia unificata ad alto livello per threading e multiprocessing tramite `ThreadPoolExecutor` e `ProcessPoolExecutor`.

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from concurrent.futures import as_completed
import time
import math

# ThreadPoolExecutor per I/O bound
def scarica_url(url):
    time.sleep(1)  # Simula download
    return f"Contenuto di {url}"

# ProcessPoolExecutor per CPU bound
def calcola_fattoriale(n):
    return math.factorial(n)

def esempio_futures():
    # submit() restituisce un oggetto Future
    with ThreadPoolExecutor(max_workers=5) as executor:
        urls = [f"https://esempio.com/pagina/{i}" for i in range(10)]
        # submit() permette di gestire ogni Future individualmente
        futures = {executor.submit(scarica_url, url): url for url in urls}

        for future in as_completed(futures):
            url = futures[future]
            try:
                risultato = future.result(timeout=5)
                print(f"Completato: {url}")
            except TimeoutError:
                print(f"Timeout: {url}")
            except Exception as e:
                print(f"Errore {url}: {e}")

    # ProcessPoolExecutor per calcoli pesanti
    with ProcessPoolExecutor(max_workers=4) as executor:
        numeri = [100000, 200000, 300000, 400000]
        # map() mantiene l'ordine dei risultati
        risultati = list(executor.map(calcola_fattoriale, numeri))
        for n, r in zip(numeri, risultati):
            cifre = len(str(r))
            print(f"{n}! ha {cifre} cifre")

if __name__ == "__main__":
    esempio_futures()
```

**Oggetti Future** — rappresentano il risultato di un'operazione asincrona.

```python
from concurrent.futures import ThreadPoolExecutor, Future
import time

def operazione(valore):
    time.sleep(1)
    if valore < 0:
        raise ValueError("Valore negativo non ammesso")
    return valore ** 2

with ThreadPoolExecutor(max_workers=3) as executor:
    future: Future = executor.submit(operazione, 5)

    # Verifica lo stato
    print(f"In esecuzione: {future.running()}")
    print(f"Completato: {future.done()}")

    # Attendi il risultato con timeout opzionale
    risultato = future.result(timeout=3)
    print(f"Risultato: {risultato}")

    # Gestione eccezioni tramite Future
    future_errore = executor.submit(operazione, -1)
    eccezione = future_errore.exception(timeout=3)
    print(f"Eccezione: {eccezione}")

    # Callback al completamento
    def al_completamento(future):
        if future.exception():
            print(f"Operazione fallita: {future.exception()}")
        else:
            print(f"Operazione riuscita: {future.result()}")

    future_cb = executor.submit(operazione, 7)
    future_cb.add_done_callback(al_completamento)
```

### Combinare asyncio con Threading/Multiprocessing

In applicazioni reali, spesso e necessario combinare asyncio con thread o processi per gestire sia operazioni I/O bound che CPU bound.

**asyncio.to_thread() (Python 3.9+)** — esegue una funzione sincrona bloccante in un thread separato senza bloccare l'event loop.

```python
import asyncio
import time

def operazione_bloccante_sincorna(dato):
    """Funzione sincrona che non puo essere resa async."""
    time.sleep(2)  # Simula libreria sincrona (es. PIL, pandas)
    return f"Elaborato: {dato}"

async def main():
    # Esegui la funzione sincrona in un thread separato
    risultato = await asyncio.to_thread(
        operazione_bloccante_sincorna, "immagine.jpg"
    )
    print(risultato)

    # Piu operazioni bloccanti in concorrenza
    risultati = await asyncio.gather(
        asyncio.to_thread(operazione_bloccante_sincorna, "file1.csv"),
        asyncio.to_thread(operazione_bloccante_sincorna, "file2.csv"),
        asyncio.to_thread(operazione_bloccante_sincorna, "file3.csv"),
    )
    # Tempo totale: ~2s invece di ~6s
    print(risultati)

asyncio.run(main())
```

**run_in_executor()** — approccio piu flessibile che supporta sia thread che processi.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import math

def calcolo_pesante(n):
    """Operazione CPU-bound."""
    return sum(math.factorial(i) for i in range(n))

def lettura_file_sincrona(percorso):
    """Operazione I/O con libreria sincrona."""
    import time
    time.sleep(1)
    return f"Contenuto di {percorso}"

async def main():
    loop = asyncio.get_running_loop()

    # ThreadPoolExecutor per I/O bound
    thread_pool = ThreadPoolExecutor(max_workers=4)
    risultato_io = await loop.run_in_executor(
        thread_pool, lettura_file_sincrona, "/tmp/dati.txt"
    )
    print(risultato_io)

    # ProcessPoolExecutor per CPU bound
    process_pool = ProcessPoolExecutor(max_workers=4)
    risultato_cpu = await loop.run_in_executor(
        process_pool, calcolo_pesante, 500
    )
    print(f"Risultato calcolo: {risultato_cpu}")

    # Combinazione: I/O e CPU in concorrenza
    risultati = await asyncio.gather(
        loop.run_in_executor(thread_pool, lettura_file_sincrona, "a.txt"),
        loop.run_in_executor(thread_pool, lettura_file_sincrona, "b.txt"),
        loop.run_in_executor(process_pool, calcolo_pesante, 300),
        loop.run_in_executor(process_pool, calcolo_pesante, 400),
    )
    print(f"Tutti i risultati: {risultati}")

    thread_pool.shutdown(wait=False)
    process_pool.shutdown(wait=False)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## uvloop

uvloop e un'implementazione dell'event loop di asyncio basata su libuv (la stessa libreria usata da Node.js). Offre prestazioni significativamente superiori al loop di default, in particolare per workload I/O-intensivi.

Riferimento: [uvloop GitHub](https://github.com/MagicStack/uvloop)

### Installazione e Attivazione

```bash
pip install uvloop
```

```python
import asyncio

# Metodo 1: sostituzione globale della politica (pre-3.11)
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
asyncio.run(main())

# Metodo 2: con asyncio.Runner (3.11+) — raccomandato
import uvloop
with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
    runner.run(main())

# Metodo 3: shortcut uvloop.run() (uvloop 0.18+)
import uvloop
uvloop.run(main())
```

### Benchmark e Comparazione

Risultati tipici (variano in base al workload e all'hardware):

```
Operazione                     Default Loop    uvloop      Speedup
──────────────────────────────────────────────────────────────────
TCP echo server (req/s)        ~25,000         ~75,000     3.0x
HTTP requests (aiohttp)        ~8,000          ~18,000     2.2x
DNS resolution                 ~5,000          ~12,000     2.4x
Pipe I/O                       ~30,000         ~90,000     3.0x
Timer callbacks                ~50,000         ~120,000    2.4x
```

```python
import asyncio
import time

async def benchmark_echo(n_messaggi: int = 10_000):
    """Benchmark semplice: crea e awaita N coroutine."""
    inizio = time.perf_counter()

    async def noop():
        await asyncio.sleep(0)

    await asyncio.gather(*[noop() for _ in range(n_messaggi)])
    durata = time.perf_counter() - inizio
    print(f"{n_messaggi} coroutine in {durata:.3f}s "
          f"({n_messaggi / durata:.0f} ops/s)")

# Test con loop di default
asyncio.run(benchmark_echo())

# Test con uvloop (risultato tipicamente 2-3x piu veloce)
# import uvloop
# uvloop.run(benchmark_echo())
```

### Compatibilita e Limitazioni

- **Piattaforme**: Linux e macOS. Non supporta Windows.
- **Compatibilita API**: 100% compatibile con l'API asyncio standard. Nessuna modifica al codice applicativo.
- **subprocess**: uvloop reimplementa la gestione dei subprocessi. Su alcuni sistemi puo comportarsi diversamente dal loop di default.
- **Segnali**: gestione dei segnali compatibile ma con implementazione diversa.
- **Debug mode**: `loop.set_debug(True)` funziona, ma l'overhead di debug e differente.
- **Free-threading (PEP 703)**: la compatibilita con la build no-GIL non e ancora garantita; verificare le release notes.

---

## PEP 703 — Free-Threading

PEP 703 ("Making the Global Interpreter Lock Optional in CPython") e il progetto per rimuovere il GIL dall'interprete CPython, permettendo vero parallelismo tra thread Python.

Riferimento: [PEP 703](https://peps.python.org/pep-0703/)

### La Rimozione del GIL

Il GIL esiste dal 1992 e garantisce che un solo thread alla volta possa eseguire bytecode Python. Questo semplifica enormemente l'implementazione dell'interprete e delle estensioni C, ma impedisce il parallelismo reale su CPU multicore.

PEP 703 propone:

1. **Reference counting bidirezionale**: sostituzione del reference count semplice con un contatore thread-safe che usa operazioni atomiche.
2. **Biased reference counting**: ottimizzazione per il caso comune (singolo thread) che mantiene le prestazioni single-threaded.
3. **Deferred reference counting**: per oggetti immortali (moduli, piccoli interi, stringhe internate).
4. **Lock-free data structures**: dict, list e altri tipi built-in diventano thread-safe senza lock globale.

### Implicazioni per il Codice Asincrono

La domanda chiave: **asyncio diventa obsoleto con la rimozione del GIL?**

La risposta e no, per diverse ragioni:

```
Scenario                         Senza GIL (threading)    asyncio
──────────────────────────────────────────────────────────────────
10 connessioni TCP                Adeguato                 Adeguato
1,000 connessioni TCP             Costoso (1000 thread)    Efficiente
10,000 connessioni TCP            Impraticabile             Efficiente
CPU-bound parallelo               Eccellente (nuovo!)      Non applicabile
I/O + CPU misto                   Buono                    Buono + executor
Overhead per connessione          ~8MB per thread           ~2KB per coroutine
Context switch                    OS-level (costoso)       User-level (economico)
```

**asyncio rimane la scelta migliore per I/O-bound ad alta concorrenza** (migliaia di connessioni), anche senza GIL. I thread hanno un overhead di memoria e context switching molto superiore alle coroutine.

```python
# Con free-threading, QUESTO diventa finalmente efficace per CPU-bound:
import threading

def calcolo_parallelo(dati):
    risultati = []
    threads = []
    for chunk in dati:
        t = threading.Thread(target=lambda c: risultati.append(elabora(c)), args=(chunk,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return risultati

# Ma per I/O-bound, asyncio resta piu efficiente:
import asyncio

async def io_concorrente(urls):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(
            *[session.get(url) for url in urls]
        )
    # 10,000 richieste concorrenti con ~20KB di memoria totale
    # vs 10,000 thread = ~80GB di memoria
```

### Timeline e Build Sperimentale

| Versione | Stato |
|----------|-------|
| **Python 3.13** (2024-10) | Build sperimentale `--disable-gil`. Opt-in, non di default. Disponibile tramite `python3.13t`. |
| **Python 3.14** (2025-10) | Build free-threaded migliorata. Ancora sperimentale ma piu stabile. Performance gap ridotto. |
| **Python 3.15+** (2026+) | Obiettivo: free-threading come opzione di build supportata. Possibile default futuro. |

```bash
# Installare la build free-threaded (3.13+)
# Su Ubuntu/Debian:
# sudo apt install python3.13-nogil
# oppure compilare da sorgente:
# ./configure --disable-gil && make && sudo make install

# Verificare se il GIL e disabilitato
python3 -c "import sys; print(sys._is_gil_enabled())"
# False = free-threaded build
```

### Compatibilita dell'Ecosistema

La transizione al free-threading richiede che le estensioni C siano aggiornate per essere thread-safe.

**Stato attuale (2026):**

| Libreria | Compatibilita free-threading |
|----------|------------------------------|
| NumPy | In corso (parziale) |
| asyncio | Compatibile (single-threaded by design) |
| aiohttp | Da verificare per versione |
| uvloop | Non ancora garantito |
| Cython | Supporto in sviluppo |
| pybind11 | Supporto in sviluppo |

**Impatto pratico**: il codice asyncio puro non e influenzato dalla rimozione del GIL perche opera su un singolo thread. Le estensioni C usate da librerie asincrone (es. il parser HTTP di aiohttp) devono essere verificate per thread safety.

---

## Testing Codice Asincrono

Testare codice asincrono richiede strumenti specifici. I tre approcci principali: `pytest-asyncio`, `anyio` e mocking manuale.

### pytest-asyncio

`pytest-asyncio` permette di scrivere test asincroni direttamente come coroutine.

```bash
pip install pytest-asyncio
```

```python
# test_async.py
import asyncio
import pytest

# Configurazione: auto mode (raccomandato per pytest-asyncio 0.21+)
# In pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"

@pytest.mark.asyncio
async def test_coroutine_semplice():
    risultato = await asyncio.sleep(0.01, result="ok")
    assert risultato == "ok"

@pytest.mark.asyncio
async def test_task_group():
    risultati = []

    async def accumula(valore):
        await asyncio.sleep(0.01)
        risultati.append(valore)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(accumula(1))
        tg.create_task(accumula(2))
        tg.create_task(accumula(3))

    assert sorted(risultati) == [1, 2, 3]

@pytest.mark.asyncio
async def test_timeout():
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.01):
            await asyncio.sleep(10)

# Fixture asincrona
@pytest.fixture
async def connessione_db():
    """Setup e teardown asincrono per test."""
    conn = await crea_connessione_test()
    yield conn
    await conn.close()

@pytest.mark.asyncio
async def test_con_fixture(connessione_db):
    risultato = await connessione_db.execute("SELECT 1")
    assert risultato is not None

# Helper: crea connessione fittizia per l'esempio
async def crea_connessione_test():
    class FakeConn:
        async def execute(self, query):
            await asyncio.sleep(0.01)
            return {"query": query}
        async def close(self):
            pass
    return FakeConn()
```

### anyio e Backend-Agnostic Testing

`anyio` fornisce un layer di astrazione sopra asyncio e Trio, permettendo di scrivere test che funzionano con entrambi i backend.

```bash
pip install anyio pytest-anyio
```

```python
import anyio
import pytest

@pytest.mark.anyio
async def test_backend_agnostico():
    """Questo test funziona sia con asyncio che con trio."""
    async with anyio.create_task_group() as tg:
        risultati = []

        async def lavoro(valore):
            await anyio.sleep(0.01)
            risultati.append(valore)

        tg.start_soon(lavoro, 1)
        tg.start_soon(lavoro, 2)

    assert sorted(risultati) == [1, 2]

@pytest.mark.anyio
async def test_timeout_anyio():
    with pytest.raises(TimeoutError):
        with anyio.fail_after(0.01):
            await anyio.sleep(10)
```

### Mock di Funzioni Asincrone

```python
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Classe da testare
class ServizioUtenti:
    def __init__(self, client_http):
        self.client = client_http

    async def ottieni_utente(self, id_utente: int) -> dict:
        risposta = await self.client.get(f"/utenti/{id_utente}")
        return risposta

    async def crea_utente(self, dati: dict) -> dict:
        risposta = await self.client.post("/utenti", json=dati)
        return risposta

# Test con AsyncMock
@pytest.mark.asyncio
async def test_ottieni_utente():
    # AsyncMock simula una coroutine
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value={"id": 1, "nome": "Mario"})

    servizio = ServizioUtenti(mock_client)
    utente = await servizio.ottieni_utente(1)

    assert utente["nome"] == "Mario"
    mock_client.get.assert_awaited_once_with("/utenti/1")

@pytest.mark.asyncio
async def test_crea_utente():
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value={"id": 42, "nome": "Luigi"})

    servizio = ServizioUtenti(mock_client)
    risultato = await servizio.crea_utente({"nome": "Luigi"})

    assert risultato["id"] == 42
    mock_client.post.assert_awaited_once()

# Mock con side_effect per simulare errori
@pytest.mark.asyncio
async def test_errore_rete():
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("Timeout"))

    servizio = ServizioUtenti(mock_client)
    with pytest.raises(ConnectionError):
        await servizio.ottieni_utente(1)
```

### Test di Timeout e Cancellazione

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_cancellazione_task():
    eseguito_cleanup = False

    async def task_con_cleanup():
        nonlocal eseguito_cleanup
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            eseguito_cleanup = True
            raise

    task = asyncio.create_task(task_con_cleanup())
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert eseguito_cleanup is True
    assert task.cancelled() is True

@pytest.mark.asyncio
async def test_timeout_con_cleanup():
    risorse_rilasciate = False

    async def operazione_con_risorse():
        nonlocal risorse_rilasciate
        try:
            await asyncio.sleep(100)
        finally:
            risorse_rilasciate = True

    try:
        async with asyncio.timeout(0.01):
            await operazione_con_risorse()
    except TimeoutError:
        pass

    assert risorse_rilasciate is True
```

---

## Pattern Avanzati

### Producer-Consumer

Il pattern producer-consumer e uno dei piu comuni nella programmazione asincrona. Utilizza una coda asincrona per disaccoppiare la produzione dei dati dalla loro elaborazione.

```python
import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Lavoro:
    id: int
    payload: str
    priorita: int = 0
    creato: datetime = field(default_factory=datetime.now)

async def produttore(coda: asyncio.Queue, id_produttore: int, n_lavori: int):
    """Produce lavori e li inserisce nella coda."""
    for i in range(n_lavori):
        lavoro = Lavoro(
            id=id_produttore * 1000 + i,
            payload=f"Dati dal produttore {id_produttore}, batch {i}",
            priorita=random.randint(1, 5)
        )
        await coda.put(lavoro)
        print(f"[P{id_produttore}] Inserito lavoro {lavoro.id}")
        await asyncio.sleep(random.uniform(0.1, 0.5))

    print(f"[P{id_produttore}] Produzione completata")

async def consumatore(coda: asyncio.Queue, id_consumatore: int):
    """Consuma lavori dalla coda e li elabora."""
    lavori_elaborati = 0
    while True:
        try:
            lavoro = await asyncio.wait_for(coda.get(), timeout=2.0)
        except asyncio.TimeoutError:
            print(f"[C{id_consumatore}] Nessun lavoro per 2s, termino")
            break

        print(f"[C{id_consumatore}] Elaboro lavoro {lavoro.id} "
              f"(priorita: {lavoro.priorita})")
        await asyncio.sleep(random.uniform(0.2, 1.0))
        lavori_elaborati += 1
        coda.task_done()

    print(f"[C{id_consumatore}] Totale elaborati: {lavori_elaborati}")

async def main():
    coda = asyncio.Queue(maxsize=20)

    # Avvia 3 produttori e 5 consumatori
    produttori = [
        asyncio.create_task(produttore(coda, i, 10))
        for i in range(3)
    ]
    consumatori = [
        asyncio.create_task(consumatore(coda, i))
        for i in range(5)
    ]

    # Attendi che tutti i produttori finiscano
    await asyncio.gather(*produttori)
    # Attendi che la coda venga completamente svuotata
    await coda.join()
    # I consumatori termineranno per timeout

    await asyncio.gather(*consumatori)
    print("Pipeline completata")

asyncio.run(main())
```

### Fan-out/Fan-in

Il pattern fan-out/fan-in distribuisce il lavoro a piu worker (fan-out) e poi raccoglie e combina i risultati (fan-in).

```python
import asyncio
import random

async def recupera_dati(sorgente: str) -> list[dict]:
    """Fan-out: recupera dati da una sorgente."""
    await asyncio.sleep(random.uniform(0.5, 2.0))
    # Simula dati recuperati
    return [
        {"sorgente": sorgente, "valore": random.randint(1, 100)}
        for _ in range(random.randint(3, 8))
    ]

async def elabora_batch(dati: list[dict]) -> dict:
    """Elabora un batch di dati."""
    await asyncio.sleep(0.3)
    totale = sum(d["valore"] for d in dati)
    return {
        "sorgente": dati[0]["sorgente"] if dati else "nessuna",
        "conteggio": len(dati),
        "totale": totale,
        "media": totale / len(dati) if dati else 0
    }

async def pipeline_fan_out_fan_in():
    """Pipeline completa con fan-out e fan-in."""
    sorgenti = ["database_A", "api_esterna", "cache_redis",
                "database_B", "file_system"]

    # Fan-out: recupera dati da tutte le sorgenti in parallelo
    print("--- Fan-out: recupero dati ---")
    dati_grezzi = await asyncio.gather(
        *[recupera_dati(s) for s in sorgenti]
    )

    # Elaborazione intermedia: elabora ogni batch in parallelo
    print("--- Elaborazione parallela ---")
    risultati = await asyncio.gather(
        *[elabora_batch(batch) for batch in dati_grezzi]
    )

    # Fan-in: combina tutti i risultati
    print("--- Fan-in: combinazione risultati ---")
    report = {
        "sorgenti_totali": len(risultati),
        "record_totali": sum(r["conteggio"] for r in risultati),
        "valore_totale": sum(r["totale"] for r in risultati),
        "dettagli": risultati
    }

    print(f"Report finale:")
    print(f"  Sorgenti interrogate: {report['sorgenti_totali']}")
    print(f"  Record totali: {report['record_totali']}")
    print(f"  Valore aggregato: {report['valore_totale']}")
    for d in report["dettagli"]:
        print(f"  - {d['sorgente']}: {d['conteggio']} record, "
              f"media={d['media']:.1f}")

asyncio.run(pipeline_fan_out_fan_in())
```

### Graceful Shutdown

Un graceful shutdown garantisce che l'applicazione termini in modo pulito: completa i lavori in corso, salva lo stato e rilascia le risorse. Questo e essenziale per applicazioni di produzione.

```python
import asyncio
import signal
from contextlib import suppress

class ApplicationeAsincrona:
    """Applicazione con gestione corretta dello shutdown."""

    def __init__(self):
        self.in_esecuzione = True
        self._tasks: list[asyncio.Task] = []
        self._coda = asyncio.Queue()

    async def worker(self, id_worker: int):
        """Worker che elabora lavori dalla coda."""
        while self.in_esecuzione:
            try:
                lavoro = await asyncio.wait_for(
                    self._coda.get(), timeout=1.0
                )
                print(f"Worker {id_worker}: elaboro {lavoro}")
                await asyncio.sleep(0.5)
                self._coda.task_done()
            except asyncio.TimeoutError:
                continue  # Controlla se deve fermarsi
            except asyncio.CancelledError:
                print(f"Worker {id_worker}: cancellato, pulizia...")
                break

        print(f"Worker {id_worker}: terminato")

    async def produttore(self):
        """Produce lavori continuamente."""
        contatore = 0
        while self.in_esecuzione:
            await self._coda.put(f"lavoro_{contatore}")
            contatore += 1
            await asyncio.sleep(0.3)

    def gestisci_segnale(self, sig):
        """Handler per segnali di sistema (SIGINT, SIGTERM)."""
        print(f"\nRicevuto segnale {sig.name}, avvio shutdown...")
        self.in_esecuzione = False

    async def avvia(self):
        """Avvia l'applicazione con gestione dei segnali."""
        loop = asyncio.get_running_loop()

        # Registra handler per segnali di sistema
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: self.gestisci_segnale(s)
            )

        # Avvia i worker
        self._tasks = [
            asyncio.create_task(self.worker(i))
            for i in range(3)
        ]
        self._tasks.append(asyncio.create_task(self.produttore()))

        print("Applicazione avviata. Premi Ctrl+C per terminare.")

        # Attendi che tutti i task terminino
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Svuota la coda rimanente
        while not self._coda.empty():
            try:
                self._coda.get_nowait()
                self._coda.task_done()
            except asyncio.QueueEmpty:
                break

        print("Shutdown completato")

async def main():
    app = ApplicationeAsincrona()
    await app.avvia()

# In un ambiente reale: asyncio.run(main())
```

---

## Pitfall Comuni

Questa sezione raccoglie gli errori piu frequenti nella programmazione asincrona Python, con diagnosi e soluzioni.

### Bloccare l'Event Loop

Il problema piu grave: eseguire codice sincrono bloccante nel thread dell'event loop.

```python
import asyncio
import time

# SBAGLIATO: blocca l'intero event loop
async def handler_sbagliato(request):
    time.sleep(5)  # BLOCCA TUTTO per 5 secondi
    dati = open("file_grande.bin", "rb").read()  # BLOCCA durante I/O disco
    import requests
    resp = requests.get("https://api.esempio.com")  # BLOCCA durante HTTP
    return dati

# CORRETTO: delegare a thread per operazioni bloccanti
async def handler_corretto(request):
    # Operazione bloccante in thread separato
    dati = await asyncio.to_thread(open_and_read, "file_grande.bin")
    # Libreria sincrona in thread separato
    resp = await asyncio.to_thread(requests.get, "https://api.esempio.com")
    return dati

def open_and_read(path):
    with open(path, "rb") as f:
        return f.read()

# DIAGNOSI: abilitare debug mode per individuare il blocco
# asyncio.run(main(), debug=True)
# Output: "Executing ... took 5.001 seconds"
```

### Dimenticare await

Una coroutine non awaitata non viene eseguita. Python emette un `RuntimeWarning`.

```python
import asyncio

async def salva_dati(dati):
    await asyncio.sleep(0.1)
    print(f"Dati salvati: {dati}")

async def main():
    # SBAGLIATO: la coroutine non viene eseguita
    salva_dati({"chiave": "valore"})
    # RuntimeWarning: coroutine 'salva_dati' was never awaited

    # CORRETTO:
    await salva_dati({"chiave": "valore"})

    # SBAGLIATO con create_task:
    asyncio.create_task(salva_dati({"a": 1}))
    # Funziona MA il task potrebbe non completarsi se main() termina prima

    # CORRETTO con create_task:
    task = asyncio.create_task(salva_dati({"a": 1}))
    await task

asyncio.run(main())
```

### Task Reference Loss

Se si perde il riferimento a un task, il garbage collector puo raccoglierlo prima che completi. Python emette un warning: "Task was destroyed but it is pending!"

```python
import asyncio

async def operazione_lunga():
    await asyncio.sleep(10)
    print("Mai raggiunto")

async def main():
    # SBAGLIATO: il task puo essere raccolto dal GC
    asyncio.create_task(operazione_lunga())
    await asyncio.sleep(0.1)
    # Il task potrebbe essere distrutto qui

    # CORRETTO: mantieni un riferimento
    task = asyncio.create_task(operazione_lunga())
    # ... usa il task ...
    await task

    # PATTERN per task di background: usa un set per mantenere i riferimenti
    _background_tasks = set()

    async def avvia_background(coro):
        task = asyncio.create_task(coro)
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    await avvia_background(operazione_lunga())
```

### Deadlock con Primitive di Sincronizzazione

```python
import asyncio

# DEADLOCK: due coroutine che attendono i lock l'una dell'altra
async def deadlock_esempio():
    lock_a = asyncio.Lock()
    lock_b = asyncio.Lock()

    async def task_1():
        async with lock_a:
            await asyncio.sleep(0.1)
            async with lock_b:  # Attende lock_b, detenuto da task_2
                print("Task 1 completato")

    async def task_2():
        async with lock_b:
            await asyncio.sleep(0.1)
            async with lock_a:  # Attende lock_a, detenuto da task_1
                print("Task 2 completato")

    # DEADLOCK!
    # await asyncio.gather(task_1(), task_2())

    # SOLUZIONE 1: ordinamento coerente dei lock
    async def task_1_fix():
        async with lock_a:
            async with lock_b:
                print("Task 1 fix completato")

    async def task_2_fix():
        async with lock_a:  # Stesso ordine di task_1
            async with lock_b:
                print("Task 2 fix completato")

    await asyncio.gather(task_1_fix(), task_2_fix())

asyncio.run(deadlock_esempio())
```

### Starvation e Fairness

```python
import asyncio

async def task_goloso():
    """Task che non cede mai il controllo."""
    contatore = 0
    while contatore < 1_000_000:
        contatore += 1
        # SBAGLIATO: nessun await, l'event loop non puo schedulare altri task
    print(f"Goloso: {contatore}")

async def task_affamato():
    """Questo task non viene mai eseguito."""
    print("Affamato: finalmente il mio turno!")

async def main():
    # task_affamato non viene eseguito fino a che task_goloso non finisce
    # await asyncio.gather(task_goloso(), task_affamato())

    # SOLUZIONE: inserire yield point periodici
    async def task_cooperativo():
        contatore = 0
        while contatore < 1_000_000:
            contatore += 1
            if contatore % 10_000 == 0:
                await asyncio.sleep(0)  # Cede il controllo all'event loop

    await asyncio.gather(task_cooperativo(), task_affamato())

asyncio.run(main())
```

---

## Performance e Debugging

L'ottimizzazione e il debugging del codice asincrono richiedono strumenti e tecniche specifici. Questa sezione copre gli approcci piu importanti.

**asyncio debug mode** — attiva controlli aggiuntivi che identificano problemi comuni.

```python
import asyncio
import warnings

# Metodo 1: variabile d'ambiente
# PYTHONASYNCIODEBUG=1 python script.py

# Metodo 2: nel codice
async def main():
    # Il debug mode segnala:
    # - Coroutine mai awaitate
    # - Callback che impiegano troppo tempo
    # - Handler di risorse non chiuse
    pass

asyncio.run(main(), debug=True)

# Metodo 3: abilitare warnings per coroutine non awaitate
warnings.filterwarnings("error", category=RuntimeWarning)
```

**Profiling del codice asincrono** — misurare le prestazioni delle coroutine.

```python
import asyncio
import time
from functools import wraps

def profila_coroutine(func):
    """Decoratore per profilare coroutine."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        inizio = time.perf_counter()
        risultato = await func(*args, **kwargs)
        durata = time.perf_counter() - inizio
        print(f"[PROFILER] {func.__name__}: {durata:.4f}s")
        return risultato
    return wrapper

@profila_coroutine
async def operazione_misurata():
    await asyncio.sleep(0.5)
    return "completato"

class ProfiloEventLoop:
    """Monitora la salute dell'event loop."""

    def __init__(self, soglia_ms=100):
        self.soglia = soglia_ms / 1000
        self._ultimo_check = None

    async def monitora(self):
        """Rileva quando l'event loop e bloccato."""
        while True:
            inizio = time.perf_counter()
            await asyncio.sleep(0.1)
            durata = time.perf_counter() - inizio
            ritardo = durata - 0.1
            if ritardo > self.soglia:
                print(f"[ATTENZIONE] Event loop bloccato per "
                      f"{ritardo*1000:.1f}ms")

async def main():
    await operazione_misurata()

asyncio.run(main())
```

**Errori comuni e come evitarli:**

```python
import asyncio
import time

# ERRORE 1: Bloccare l'event loop con operazioni sincrone
async def blocca_event_loop():
    # MAI fare questo: time.sleep blocca l'intero event loop
    time.sleep(5)  # SBAGLIATO
    await asyncio.sleep(5)  # CORRETTO

# ERRORE 2: Dimenticare await
async def dimentica_await():
    # Questo crea la coroutine ma non la esegue
    asyncio.sleep(1)  # SBAGLIATO: manca await
    await asyncio.sleep(1)  # CORRETTO

# ERRORE 3: Creare task senza mantenerli referenziati
async def task_persi():
    # Il task puo essere raccolto dal garbage collector
    asyncio.create_task(asyncio.sleep(1))  # SBAGLIATO: nessun riferimento

    # CORRETTO: mantieni un riferimento
    task = asyncio.create_task(asyncio.sleep(1))
    await task

# ERRORE 4: Non gestire le eccezioni nei task
async def eccezione_silenziosa():
    async def task_fallito():
        raise ValueError("Errore!")

    task = asyncio.create_task(task_fallito())
    # Se non si fa await, l'eccezione viene persa silenziosamente
    # CORRETTO:
    try:
        await task
    except ValueError as e:
        print(f"Errore gestito: {e}")

# ERRORE 5: Usare asyncio.gather senza gestire gli errori
async def gather_senza_errori():
    # Se una coroutine fallisce, le altre vengono cancellate
    # CORRETTO: usa return_exceptions=True oppure try/except
    risultati = await asyncio.gather(
        asyncio.sleep(1),
        asyncio.sleep(2),
        return_exceptions=True
    )
```

---

## Troubleshooting

### Problema: "RuntimeWarning: coroutine was never awaited"

**Causa**: una coroutine e stata chiamata senza `await`, creando un oggetto coroutine che non viene mai eseguito.

**Soluzione**:
```python
# Identificare la riga con il warning e aggiungere await
# PRIMA:  funzione_asincrona(argomenti)
# DOPO:   await funzione_asincrona(argomenti)
# OPPURE: asyncio.create_task(funzione_asincrona(argomenti))
```

**Diagnosi**: eseguire con `python -W error::RuntimeWarning script.py` per trasformare i warning in errori e ottenere un traceback completo.

### Problema: "Task was destroyed but it is pending!"

**Causa**: un task e stato creato ma mai awaitato, e il garbage collector lo ha raccolto mentre era ancora in esecuzione.

**Soluzione**: mantenere un riferimento al task e farne `await` prima della terminazione.

```python
# Pattern: set di background tasks
_background = set()

async def lancia_background(coro):
    task = asyncio.create_task(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)
    return task
```

### Problema: "Event loop is closed"

**Causa**: si tenta di usare l'event loop dopo che `asyncio.run()` lo ha chiuso. Comune quando si chiama `asyncio.run()` piu volte o si usano fixture pytest non configurate correttamente.

**Soluzione**: usare `asyncio.Runner` per riusare il loop, oppure assicurarsi che `asyncio.run()` venga chiamato una sola volta.

### Problema: "Cannot run the event loop while another loop is running"

**Causa**: si tenta di chiamare `asyncio.run()` o `loop.run_until_complete()` dall'interno di una coroutine gia in esecuzione. Comune in Jupyter notebook.

**Soluzione**:
```python
# In Jupyter: usare await direttamente (il notebook ha gia un event loop)
# await main()

# In codice non-Jupyter: usare nest_asyncio come workaround temporaneo
# import nest_asyncio
# nest_asyncio.apply()
# asyncio.run(main())

# Soluzione corretta: ristrutturare il codice per non annidare event loop
```

### Problema: performance degradata senza errori visibili

**Diagnosi**:

1. Abilitare debug mode: `asyncio.run(main(), debug=True)`
2. Cercare "took X.XXX seconds" nei log — indica callback bloccanti
3. Usare il decoratore `profila_coroutine` sulle coroutine sospette
4. Verificare che non ci siano `time.sleep()` o operazioni sincroni nel codice async
5. Controllare il numero di coroutine concorrenti — troppo alta concorrenza senza semafori puo degradare le performance

### Problema: test asincroni falliscono con "no running event loop"

**Soluzione**: assicurarsi che pytest-asyncio sia configurato correttamente.

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## Best Practices

1. **Utilizzare `asyncio.run()` come unico punto di ingresso.** Non creare event loop manualmente con `get_event_loop()` o `new_event_loop()` a meno che non sia strettamente necessario (ad esempio, in ambienti embedded o framework specifici). `asyncio.run()` gestisce correttamente la creazione, l'esecuzione e la chiusura del loop, incluso il cleanup delle risorse.

2. **Non bloccare mai l'event loop con operazioni sincrone.** Qualsiasi funzione che impiega piu di qualche millisecondo deve essere eseguita in un thread separato usando `asyncio.to_thread()` o `run_in_executor()`. Operazioni come `time.sleep()`, I/O su file senza aiofiles, chiamate a librerie sincrone bloccanti (requests, PIL) devono sempre essere delegate a un thread. Un event loop bloccato impedisce a tutte le altre coroutine di progredire.

3. **Utilizzare `async with` per tutte le risorse che richiedono cleanup.** Sessioni HTTP, connessioni a database, file aperti, lock e semafori devono essere gestiti come context manager asincroni. Questo garantisce il rilascio corretto delle risorse anche in presenza di eccezioni, prevenendo memory leak e connessioni orfane.

4. **Preferire `TaskGroup` a `gather` per la gestione strutturata della concorrenza (Python 3.11+).** `TaskGroup` implementa il pattern structured concurrency: se un task fallisce, tutti gli altri vengono cancellati automaticamente, prevenendo task orfani e semplificando la gestione degli errori. Per versioni precedenti di Python, utilizzare `gather` con `return_exceptions=True` e gestire le eccezioni esplicitamente.

5. **Limitare sempre la concorrenza con semafori quando si accede a risorse esterne.** Lanciare migliaia di richieste HTTP simultanee puo sovraccaricare il server remoto, esaurire i file descriptor o triggerare rate limiting. Usare `asyncio.Semaphore` per controllare il numero massimo di operazioni simultanee. Valori tipici: 10-50 per API esterne, 5-20 per connessioni database.

6. **Gestire sempre le eccezioni nei task.** Un task che solleva un'eccezione senza che venga catturata produce solo un warning nel log. Fare sempre `await` su ogni task creato, oppure aggiungere un callback con `add_done_callback()` per gestire gli errori. Con `gather`, usare `return_exceptions=True` per evitare che un singolo fallimento cancelli tutte le operazioni.

7. **Implementare sempre il graceful shutdown per applicazioni di produzione.** Registrare handler per `SIGINT` e `SIGTERM`, impostare un flag di terminazione, attendere il completamento dei task in corso e rilasciare le risorse. Utilizzare `asyncio.wait_for()` con un timeout per evitare che il processo rimanga bloccato indefinitamente durante lo shutdown.

8. **Scegliere il modello di concorrenza appropriato al tipo di problema.** Usare asyncio per operazioni I/O bound con molte connessioni simultanee (web server, crawler, microservizi). Usare threading per operazioni I/O bound con librerie sincrone che rilasciano il GIL. Usare multiprocessing per operazioni CPU bound. Combinare i modelli quando il carico e misto.

9. **Attivare il debug mode durante lo sviluppo e il testing.** Eseguire con `asyncio.run(main(), debug=True)` o impostare `PYTHONASYNCIODEBUG=1`. Il debug mode segnala coroutine non awaitate, callback lente e risorse non chiuse. Disattivarlo in produzione per evitare l'overhead delle verifiche aggiuntive.

10. **Mantenere le coroutine piccole e focalizzate.** Ogni coroutine dovrebbe svolgere un compito specifico e ben definito. Coroutine troppo grandi sono difficili da testare, debuggare e riutilizzare. Comporre coroutine semplici in pipeline piu complesse usando `gather`, `TaskGroup` o il pattern producer-consumer. Questo approccio migliora la leggibilita, la testabilita e la manutenibilita del codice asincrono.

11. **Utilizzare `asyncio.timeout()` (3.11+) al posto di `wait_for()` per i nuovi progetti.** Il context manager pattern e piu flessibile (permette timeout su blocchi di codice, non singole coroutine) e usa `TimeoutError` standard anziche `asyncio.TimeoutError`.

12. **Considerare uvloop per applicazioni di produzione su Linux/macOS.** L'installazione e banale (`pip install uvloop`) e l'attivazione richiede una sola riga. Il guadagno di performance e tipicamente 2-4x senza alcuna modifica al codice applicativo.

---

## Esercizi

### Esercizio 1 — Crawler concorrente con TaskGroup

**Livello**: intermedio

Implementare un crawler HTTP che visita una lista di URL concorrentemente utilizzando `TaskGroup` e `asyncio.Semaphore`. Requisiti:

- Massimo 5 richieste concorrenti
- Timeout di 10 secondi per richiesta
- Raccogliere status code, tempo di risposta e dimensione del contenuto per ogni URL
- Gestire errori (timeout, connessione rifiutata, DNS failure) senza interrompere il crawling
- Stampare un report finale ordinato per tempo di risposta

### Esercizio 2 — Pipeline Producer-Consumer con PriorityQueue

**Livello**: intermedio

Creare una pipeline di elaborazione messaggi con:

- 2 produttori che generano messaggi con priorita casuale (1-5)
- Una `PriorityQueue` con `maxsize=10` (backpressure)
- 3 consumatori che elaborano messaggi in ordine di priorita
- Metriche: messaggi elaborati per consumatore, latenza media, messaggi in DLQ
- Graceful shutdown con SIGINT

### Esercizio 3 — Server TCP Echo con Streams API

**Livello**: intermedio

Implementare un server echo TCP usando `asyncio.start_server` che:

- Gestisce connessioni multiple concorrenti
- Logga connessioni/disconnessioni con indirizzo client
- Supporta un comando `STATS` che restituisce il numero di connessioni attive e messaggi elaborati
- Supporta un comando `QUIT` che chiude la connessione
- Si spegne gracefully con SIGTERM

### Esercizio 4 — Runner per Test Suite

**Livello**: avanzato

Creare un test runner personalizzato che usa `asyncio.Runner` per:

- Eseguire una suite di test asincroni su un singolo loop
- Supportare setup/teardown asincroni a livello di suite (non per singolo test)
- Misurare il tempo di ogni test
- Supportare timeout per test (`@timeout(seconds)` decoratore)
- Generare un report con test passati, falliti e saltati

### Esercizio 5 — Rate Limiter Token Bucket

**Livello**: avanzato

Implementare un rate limiter basato sul token bucket algorithm come async context manager:

- Configurabile: rate (token/secondo), burst (dimensione bucket)
- Supportare multipli "bucket" (per IP, per API key, etc.)
- Implementare `async with rate_limiter.acquire(key, tokens=1)`
- Se il bucket e vuoto, attendere (non rifiutare)
- Metodo `get_stats(key)` per monitorare l'utilizzo

### Esercizio 6 — Free-Threading Benchmark

**Livello**: avanzato

Scrivere uno script che confronti le performance di:

- `asyncio.gather` con coroutine I/O-bound
- `threading.Thread` con funzioni I/O-bound
- `asyncio.gather` + `to_thread` misto
- (Se disponibile) threading su build free-threaded con lavoro CPU-bound

Misurare tempo di esecuzione, uso di memoria (via `tracemalloc`) e throughput.

---

## Letture e Riferimenti

### Documentazione Ufficiale

- [asyncio — Asynchronous I/O](https://docs.python.org/3.12/library/asyncio.html) — documentazione completa del modulo asyncio
- [What's New in Python 3.11 — asyncio](https://docs.python.org/3.11/whatsnew/3.11.html#asyncio) — TaskGroup, Runner, timeout, ExceptionGroup
- [What's New in Python 3.12 — asyncio](https://docs.python.org/3.12/whatsnew/3.12.html) — miglioramenti performance e API
- [What's New in Python 3.13 — Free Threading](https://docs.python.org/3.13/whatsnew/3.13.html#free-threaded-cpython) — build sperimentale senza GIL

### PEP di Riferimento

- [PEP 492 — Coroutines with async and await syntax](https://peps.python.org/pep-0492/) — le keyword async/await (Python 3.5)
- [PEP 525 — Asynchronous Generators](https://peps.python.org/pep-0525/) — async generator con yield (Python 3.6)
- [PEP 530 — Asynchronous Comprehensions](https://peps.python.org/pep-0530/) — async comprehension (Python 3.6)
- [PEP 654 — Exception Groups and except*](https://peps.python.org/pep-0654/) — ExceptionGroup per TaskGroup (Python 3.11)
- [PEP 703 — Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/) — free-threading

### Librerie Esterne

- [aiohttp](https://docs.aiohttp.org/) — HTTP client/server asincrono
- [httpx](https://www.python-httpx.org/) — HTTP client con supporto sync/async e HTTP/2
- [uvloop](https://github.com/MagicStack/uvloop) — event loop ad alte prestazioni basato su libuv
- [asyncpg](https://magicstack.github.io/asyncpg/) — driver PostgreSQL asincrono nativo
- [aiofiles](https://github.com/Tinche/aiofiles) — file I/O asincrono
- [anyio](https://anyio.readthedocs.io/) — layer di astrazione per asyncio e Trio
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) — plugin pytest per test asincroni
- [Trio](https://trio.readthedocs.io/) — libreria alternativa per structured concurrency

### Articoli e Paper

- Nathaniel J. Smith, ["Notes on structured concurrency, or: Go statement considered harmful"](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) — fondamenti teorici della structured concurrency
- Guido van Rossum, [asyncio retrospective](https://www.python.org/dev/peps/pep-3156/) — PEP 3156 originale
- Sam Gross, [PEP 703 rationale](https://peps.python.org/pep-0703/#rationale) — motivazioni per la rimozione del GIL

---

## Cross-Link ad Altri Moduli

| Modulo | Relazione |
|--------|-----------|
| [01-fondamenti-linguaggio.md](01-fondamenti-linguaggio.md) | Basi: funzioni, generatori, iteratori |
| [04-decoratori-generatori-context-manager.md](04-decoratori-generatori-context-manager.md) | Generatori (base per coroutine), context manager (`__enter__`/`__exit__` → `__aenter__`/`__aexit__`) |
| [07-error-handling-e-logging.md](07-error-handling-e-logging.md) | Gestione eccezioni, ExceptionGroup (3.11+), logging strutturato |
| [08-testing.md](08-testing.md) | pytest, fixture, mock — esteso con pytest-asyncio |
| [09-type-hints-e-mypy.md](09-type-hints-e-mypy.md) | Typing per coroutine: `Coroutine[YieldType, SendType, ReturnType]`, `Awaitable`, `AsyncIterator` |
| [11-web-framework.md](11-web-framework.md) | FastAPI (ASGI, async handlers), Starlette |
| [12-database.md](12-database.md) | SQLAlchemy async, asyncpg, connection pooling |
| [13-rest-api.md](13-rest-api.md) | API asincrone, client HTTP, rate limiting |
| [17-network-programming.md](17-network-programming.md) | Socket programming, protocolli di rete |
| [25-performance.md](25-performance.md) | Profiling, benchmarking, ottimizzazione |
| [31-osservabilita-otel-prometheus.md](31-osservabilita-otel-prometheus.md) | Tracing di coroutine, metriche asincrone, OTel context propagation |
| [33-profiling-memoria-gc.md](33-profiling-memoria-gc.md) | tracemalloc, gc, memory profiling per applicazioni async |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Awaitable** | Qualsiasi oggetto su cui si puo fare `await`: coroutine, task, future, oggetti con `__await__` |
| **Backpressure** | Meccanismo per cui un consumatore lento rallenta il produttore, prevenendo accumulo illimitato di lavoro in coda |
| **Barrier** | Primitiva di sincronizzazione (3.11+) che blocca N coroutine fino a che tutte non raggiungono il punto di sincronizzazione |
| **Callback** | Funzione registrata per essere eseguita dall'event loop in risposta a un evento (I/O pronto, timer scaduto, segnale) |
| **Concorrenza cooperativa** | Modello in cui le coroutine cedono volontariamente il controllo (ad ogni `await`), a differenza del preemptive scheduling dei thread |
| **Coroutine** | Funzione definita con `async def` che puo sospendere l'esecuzione con `await`. Restituisce un oggetto coroutine |
| **Coroutine object** | L'oggetto restituito chiamando una coroutine senza `await`. Deve essere schedulato nell'event loop per essere eseguito |
| **Dead Letter Queue (DLQ)** | Coda dove finiscono i messaggi che non possono essere elaborati dopo il numero massimo di tentativi |
| **Event Loop** | Il motore centrale di asyncio: schedula coroutine, gestisce callback I/O, coordina timer e segnali |
| **ExceptionGroup** | Contenitore (3.11+) per eccezioni multiple, usato da TaskGroup quando piu task falliscono. Gestibile con `except*` |
| **Executor** | Thread pool o process pool usato per eseguire funzioni sincrone bloccanti dall'interno di codice asincrono (`run_in_executor`) |
| **Fan-out/Fan-in** | Pattern architetturale: distribuisce lavoro a piu worker (fan-out), poi raccoglie e combina i risultati (fan-in) |
| **Free-threading** | Build sperimentale di CPython (3.13+, PEP 703) senza GIL, che permette vero parallelismo tra thread |
| **Future** | Oggetto di basso livello che rappresenta un risultato che sara disponibile in futuro. `asyncio.Task` eredita da `Future` |
| **GIL** | Global Interpreter Lock — mutex in CPython che permette a un solo thread di eseguire bytecode alla volta |
| **Graceful Shutdown** | Terminazione controllata: completa i lavori in corso, salva lo stato, rilascia le risorse, poi esce |
| **I/O Multiplexing** | Tecnica OS-level (epoll, kqueue, IOCP) per monitorare piu file descriptor contemporaneamente con un singolo thread |
| **libuv** | Libreria C per I/O asincrono multipiattaforma, usata da Node.js e uvloop |
| **Producer-Consumer** | Pattern in cui produttori inseriscono lavoro in una coda e consumatori lo estraggono e lo elaborano |
| **Runner** | `asyncio.Runner` (3.11+) — context manager per il ciclo di vita dell'event loop con riuso del loop |
| **Selector** | Modulo stdlib che wrappa le system call di I/O multiplexing del SO (epoll, kqueue, select) |
| **Semaphore** | Primitiva di sincronizzazione che limita il numero di coroutine che possono accedere a una risorsa simultaneamente |
| **Structured Concurrency** | Paradigma in cui il ciclo di vita di un task concorrente e legato al blocco che lo ha creato (TaskGroup) |
| **Task** | `asyncio.Task` — wrapper attorno a una coroutine, registrato nell'event loop. Inizia l'esecuzione immediatamente alla creazione |
| **TaskGroup** | `asyncio.TaskGroup` (3.11+) — gestore strutturato di gruppi di task con cancellazione automatica in caso di errore |
| **uvloop** | Event loop alternativo per asyncio, basato su libuv, con performance 2-4x superiori al loop di default |
| **Yield point** | Punto nel codice dove una coroutine cede il controllo all'event loop (ogni `await`) |
