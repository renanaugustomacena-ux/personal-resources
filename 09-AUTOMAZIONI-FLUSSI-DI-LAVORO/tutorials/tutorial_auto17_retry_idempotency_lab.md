# Tutorial Lab — Retry, Idempotency e Circuit Breaker

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `17-retry-idempotency-pattern.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3-4 ore (lab completo)
> **Prerequisiti:** Python async I/O, Redis base, HTTP status codes, thread safety
> **Versioni di riferimento:** Python 3.11+ · tenacity 9.x · redis-py 5.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Implementare exponential backoff con jitter da zero, poi con tenacity
2. Distinguere errori retriable (5xx, timeout) da non-retriable (4xx, validation)
3. Costruire un Circuit Breaker completo con stati closed/open/half-open
4. Progettare idempotency key robuste e archiviarle in Redis con TTL
5. Dimostrare "exactly-once è impossibile" e il perché di "at-least-once + idempotency"
6. Integrare tutti i pattern in una pipeline di processing messaggi realistica

---

## Lab Environment Setup

```bash
# Verifica prerequisiti
python3 --version          # Richiede 3.11+
docker compose version     # Richiede 2.x per Redis lab

pip install tenacity==9.0.0 redis==5.0.8 httpx==0.27.0 structlog==24.0.0

# Avvia Redis (usato per idempotency key store)
docker run -d --name redis-retry-lab \
  -p 6379:6379 \
  redis:7.2-alpine \
  redis-server --save "" --loglevel warning

# Verifica
redis-cli -p 6379 ping  # → PONG

# Struttura progetto
mkdir -p retry-lab/{backoff,circuit_breaker,idempotency,pipeline}
```

---

## Analogia Introduttiva

> **Retry è come richiamare un medico**:
> Non smetti di chiamare subito se la linea è occupata.
> Ma non chiami ogni secondo — aspetti qualche minuto, poi riprovi.
> Aspetti sempre un po' di più ad ogni tentativo (exponential backoff).
> Aggiungi un po' di variazione casuale così non chiami tutti nello stesso secondo (jitter).
>
> Il **Circuit Breaker** è il tuo segretario:
> Se il medico risponde "fuori ufficio" per la quinta volta,
> smetti di chiamare per un'ora (stato OPEN) per non intasare la linea.
> Poi riprovi una sola volta (HALF-OPEN) — se risponde, torni normale.
>
> L'**Idempotency key** è il numero di pratica:
> Il medico può ricevere la tua richiesta 5 volte ma la risposta
> è sempre la stessa per quella pratica — "già elaborata".

---

## Architettura del Lab

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT (tu / task)                          │
│                                                                  │
│   richiesta → [Idempotency Check] → [Circuit Breaker]          │
│                       │                    │                     │
│                 Redis SETNX              ┌─┴─┐                  │
│                 (chiave TTL)         CLOSED/OPEN/HALF           │
│                                          │                       │
│                                   [Retry Engine]                │
│                                    (backoff+jitter)             │
│                                          │                       │
└──────────────────────────────────────────┼──────────────────────┘
                                           │
                               ┌───────────▼──────────┐
                               │   EXTERNAL SERVICE    │
                               │  (HTTP API / queue)   │
                               │  200 OK / 503 / 429   │
                               └──────────────────────┘
                                           │
                                   Redis 7.2 Alpine
                               ┌───────────▼──────────┐
                               │  idempotency_keys:    │
                               │  key → status/result  │
                               │  TTL: 24h             │
                               │                       │
                               │  circuit_breaker:     │
                               │  failures_count       │
                               │  state / opened_at    │
                               └──────────────────────┘
```

---

## PART A — Backoff e Jitter

### A1 — Implementazione da Zero (senza librerie)

```python
#!/usr/bin/env python3
# file: backoff/backoff_manual.py
"""
Exponential backoff con full jitter da zero.
Capire il meccanismo prima di usare le librerie.

Formula:
  delay = min(cap, base * 2^attempt) * random(0, 1)  ← full jitter
  delay = min(cap, base * 2^attempt) + random(0, 0.5) ← jitter additivo
"""
from __future__ import annotations

import random
import time
import logging
from dataclasses import dataclass
from typing import Callable, TypeVar, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

T = TypeVar("T")

# ─── Costanti ──────────────────────────────────────────────────────────────────

RETRY_BASE_DELAY_S = 1.0      # Attesa base (secondi)
RETRY_MAX_DELAY_S = 60.0      # Attesa massima
RETRY_MAX_ATTEMPTS = 5        # Tentativi massimi
RETRY_JITTER_MAX_S = 0.5      # Jitter additivo massimo

# HTTP status che NON devono essere ritentati
NON_RETRIABLE_STATUS = frozenset({400, 401, 403, 404, 409, 410, 422})


class RetryExhausted(Exception):
    """Tutti i tentativi esauriti."""
    def __init__(self, attempts: int, last_error: Exception):
        super().__init__(f"Esauriti {attempts} tentativi. Ultimo errore: {last_error}")
        self.last_error = last_error


class NonRetriableError(Exception):
    """Errore che non deve essere ritentato (es. 400 Bad Request)."""


@dataclass
class RetryStats:
    """Statistiche di una sequenza di retry."""
    tentativi: int = 0
    durata_totale_s: float = 0.0
    tempo_attesa_totale_s: float = 0.0
    successo: bool = False


def calcola_delay(
    tentativo: int,
    base: float = RETRY_BASE_DELAY_S,
    cap: float = RETRY_MAX_DELAY_S,
    jitter_type: str = "full",  # "full" | "additivo" | "none"
) -> float:
    """
    Calcola il delay per il tentativo N.
    
    - full jitter:     delay = rand(0, min(cap, base * 2^n)) — distribuisce carico
    - jitter additivo: delay = min(cap, base * 2^n) + rand(0, JITTER_MAX)
    - none:            delay = min(cap, base * 2^n) — non usare in produzione
    """
    exponential = min(cap, base * (2 ** tentativo))
    
    if jitter_type == "full":
        return random.uniform(0, exponential)
    elif jitter_type == "additivo":
        return exponential + random.uniform(0, RETRY_JITTER_MAX_S)
    else:
        return exponential


def con_retry_manuale(
    fn: Callable[[], T],
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY_S,
    max_delay: float = RETRY_MAX_DELAY_S,
    jitter_type: str = "full",
    nome: str = "operazione",
    dry_run: bool = False,  # Non dorme effettivamente (per test)
) -> tuple[T, RetryStats]:
    """
    Esegue fn con retry + exponential backoff + jitter.
    
    Ritorna (risultato, stats).
    Solleva NonRetriableError se fn() solleva eccezione non retriable.
    Solleva RetryExhausted se tutti i tentativi falliscono.
    """
    stats = RetryStats()
    start = time.monotonic()
    ultimo_errore: Optional[Exception] = None
    
    for tentativo in range(max_attempts):
        stats.tentativi = tentativo + 1
        try:
            result = fn()
            stats.successo = True
            stats.durata_totale_s = time.monotonic() - start
            if tentativo > 0:
                logger.info("[%s] Successo al tentativo %d", nome, tentativo + 1)
            return result, stats
        
        except NonRetriableError:
            # Non ritentare mai — propaga immediatamente
            stats.durata_totale_s = time.monotonic() - start
            logger.error("[%s] Errore non retriable — stop", nome)
            raise
        
        except Exception as e:
            ultimo_errore = e
            if tentativo < max_attempts - 1:
                delay = calcola_delay(tentativo, base_delay, max_delay, jitter_type)
                logger.warning(
                    "[%s] Tentativo %d/%d fallito (%s: %s). Retry in %.2fs",
                    nome, tentativo + 1, max_attempts, type(e).__name__, e, delay
                )
                stats.tempo_attesa_totale_s += delay
                if not dry_run:
                    time.sleep(delay)
            else:
                logger.error("[%s] Tutti i tentativi esauriti", nome)
    
    stats.durata_totale_s = time.monotonic() - start
    raise RetryExhausted(max_attempts, ultimo_errore)


# ─── Demo confronto jitter ─────────────────────────────────────────────────────

def demo_distribuzione_delay():
    """Dimostra la distribuzione dei delay con full jitter vs nessuno."""
    print("=== CONFRONTO DISTRIBUZIONE DELAY ===\n")
    
    tentativi = [0, 1, 2, 3, 4]
    print(f"{'Tentativo':>10} {'No Jitter':>12} {'Full Jitter':>14} {'Additivo':>10}")
    print("-" * 50)
    
    for t in tentativi:
        no_jit = calcola_delay(t, jitter_type="none")
        full_jit_samples = [calcola_delay(t, jitter_type="full") for _ in range(5)]
        add_jit = calcola_delay(t, jitter_type="additivo")
        print(f"{t:>10} {no_jit:>11.2f}s  "
              f"[{min(full_jit_samples):.2f}–{max(full_jit_samples):.2f}]s  "
              f"{add_jit:>9.2f}s")
    
    print("\nPerché full jitter?")
    print("  Con N client in retry simultaneo e NO jitter:")
    print("  → tutti chiamano il server nello stesso momento (thundering herd)")
    print("  Con full jitter:")
    print("  → le chiamate si distribuiscono nel tempo → meno picchi carico\n")


if __name__ == "__main__":
    demo_distribuzione_delay()
    
    # Simula servizio instabile
    tentativi_globali = [0]
    
    def servizio_instabile() -> str:
        tentativi_globali[0] += 1
        n = tentativi_globali[0]
        if n < 4:
            raise ConnectionError(f"Connection refused (tentativo {n})")
        return f"OK dopo {n} tentativi"
    
    print("=== TEST RETRY ===")
    result, stats = con_retry_manuale(
        servizio_instabile,
        nome="API_Pagamenti",
        dry_run=True  # Non aspetta nei test
    )
    print(f"Risultato: {result}")
    print(f"Stats: {stats}")
```

### A2 — Retry con tenacity (libreria standard)

```python
#!/usr/bin/env python3
# file: backoff/backoff_tenacity.py
"""
Retry con tenacity — la libreria standard Python per retry.
Più espressivo, testabile, composable del retry manuale.
"""
from __future__ import annotations

import logging
import random
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential_jitter,
    wait_random_exponential,
    before_sleep_log,
    RetryError,
    TryAgain,
)

logger = logging.getLogger(__name__)


# ─── Errori da distinguere ────────────────────────────────────────────────────

RETRIABLE_HTTP_STATUS = {429, 500, 502, 503, 504}

def is_retriable_response(response: httpx.Response) -> bool:
    """True se la risposta HTTP merita un retry."""
    return response.status_code in RETRIABLE_HTTP_STATUS

def is_retriable_exception(exc: BaseException) -> bool:
    """True per errori di rete transitori."""
    return isinstance(exc, (httpx.ConnectError, httpx.TimeoutException, ConnectionError))


# ─── Client HTTP con retry ─────────────────────────────────────────────────────

class ApiClientConRetry:
    """Client HTTP che gestisce retry automaticamente con tenacity."""

    def __init__(self, base_url: str, timeout_s: float = 10.0):
        self._client = httpx.Client(base_url=base_url, timeout=timeout_s)

    @retry(
        # Quando ritentare
        retry=(
            retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
            | retry_if_result(is_retriable_response)
        ),
        # Quante volte
        stop=stop_after_attempt(4),
        # Quanto aspettare
        wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
        # Log prima di ogni sleep
        before_sleep=before_sleep_log(logger, logging.WARNING),
        # Non wrappare in RetryError — propaga l'originale
        reraise=True,
    )
    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """GET con retry automatico su errori transitori."""
        response = self._client.get(path, **kwargs)
        if response.status_code in RETRIABLE_HTTP_STATUS:
            # tenacity ritenta se il risultato soddisfa retry_if_result
            return response
        response.raise_for_status()  # Solleva su 4xx non retriable
        return response

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=1, max=20),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def post(self, path: str, json: dict, idempotency_key: str) -> httpx.Response:
        """
        POST con retry. NOTA CRITICA:
        POST non è idempotente per default — usiamo idempotency_key
        nell'header per garantire che il server processi la richiesta una sola volta.
        """
        response = self._client.post(
            path,
            json=json,
            headers={"Idempotency-Key": idempotency_key}
        )
        response.raise_for_status()
        return response

    def close(self) -> None:
        self._client.close()


# ─── Retry asincrono ──────────────────────────────────────────────────────────

import asyncio
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter


async def chiama_api_async(url: str, max_attempts: int = 3) -> dict:
    """
    Versione async del retry con tenacity.
    Usa AsyncRetrying come context manager.
    """
    async with httpx.AsyncClient() as client:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential_jitter(initial=0.5, max=15),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        ):
            with attempt:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return response.json()
    raise RuntimeError("Unreachable")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("tenacity demo — imposta un server mock per testare")
    print("In alternativa: usa pytest + respx per mock HTTP")
```

---

## PART B — Circuit Breaker

### B1 — Implementazione Completa

```python
#!/usr/bin/env python3
# file: circuit_breaker/breaker.py
"""
Circuit Breaker con tre stati:
  CLOSED:    funziona normalmente, conta i fallimenti
  OPEN:      blocca tutte le chiamate, risponde con errore immediato
  HALF-OPEN: permette UN tentativo di probe; successo → CLOSED, errore → OPEN
"""
from __future__ import annotations

import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class StatoCircuito(str, Enum):
    CLOSED = "CLOSED"        # Normale
    OPEN = "OPEN"            # Bloccato
    HALF_OPEN = "HALF_OPEN"  # Probe


class CircuitOpenError(Exception):
    """Circuito aperto — chiamata bloccata."""
    def __init__(self, nome: str, timeout_rimanente_s: float):
        super().__init__(
            f"Circuit '{nome}' è OPEN. Timeout rimanente: {timeout_rimanente_s:.1f}s"
        )
        self.timeout_rimanente_s = timeout_rimanente_s


@dataclass
class CircuitBreakerConfig:
    soglia_fallimenti: int = 5        # Fallimenti consecutivi prima di OPEN
    timeout_open_s: float = 60.0      # Secondi in stato OPEN prima di tentare HALF-OPEN
    soglia_successi_halfopen: int = 2  # Successi consecutivi in HALF-OPEN per tornare CLOSED


@dataclass
class StatisticheBreaker:
    """Statistiche correnti del circuit breaker."""
    stato: StatoCircuito
    fallimenti_consecutivi: int
    successi_consecutivi: int
    totale_chiamate: int
    totale_successi: int
    totale_fallimenti: int
    totale_bloccate: int


class CircuitBreaker:
    """
    Circuit breaker thread-safe con contatori e tempi.
    Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
    """

    def __init__(self, nome: str, config: Optional[CircuitBreakerConfig] = None):
        self.nome = nome
        self.config = config or CircuitBreakerConfig()
        
        self._lock = threading.RLock()
        self._stato = StatoCircuito.CLOSED
        self._fallimenti_consecutivi = 0
        self._successi_consecutivi = 0
        self._opened_at: Optional[float] = None
        
        # Metriche totali
        self._totale_chiamate = 0
        self._totale_successi = 0
        self._totale_fallimenti = 0
        self._totale_bloccate = 0

    def _timeout_elapsed(self) -> bool:
        """True se il timeout OPEN è scaduto."""
        return (
            self._opened_at is not None
            and (time.monotonic() - self._opened_at) >= self.config.timeout_open_s
        )

    def _passa_a_open(self) -> None:
        logger.error(
            "[CircuitBreaker:%s] → OPEN dopo %d fallimenti consecutivi",
            self.nome, self._fallimenti_consecutivi
        )
        self._stato = StatoCircuito.OPEN
        self._opened_at = time.monotonic()
        self._successi_consecutivi = 0

    def _passa_a_half_open(self) -> None:
        logger.warning("[CircuitBreaker:%s] → HALF-OPEN (probe)", self.nome)
        self._stato = StatoCircuito.HALF_OPEN
        self._successi_consecutivi = 0

    def _passa_a_closed(self) -> None:
        logger.info("[CircuitBreaker:%s] → CLOSED (recuperato)", self.nome)
        self._stato = StatoCircuito.CLOSED
        self._fallimenti_consecutivi = 0
        self._successi_consecutivi = 0
        self._opened_at = None

    def chiama(self, fn: Callable[[], T]) -> T:
        """
        Esegui fn attraverso il circuit breaker.
        
        Raises:
            CircuitOpenError: se il circuito è OPEN e il timeout non è scaduto
            Exception: qualsiasi eccezione sollevata da fn (registrata come fallimento)
        """
        with self._lock:
            self._totale_chiamate += 1
            
            if self._stato == StatoCircuito.OPEN:
                if self._timeout_elapsed():
                    self._passa_a_half_open()
                else:
                    self._totale_bloccate += 1
                    rimanente = self.config.timeout_open_s - (
                        time.monotonic() - self._opened_at
                    )
                    raise CircuitOpenError(self.nome, rimanente)
            
            # CLOSED o HALF-OPEN: esegui la chiamata
            fn_to_call = fn
        
        # Esegui fuori dal lock per non bloccare altri thread
        try:
            result = fn_to_call()
            
            with self._lock:
                self._totale_successi += 1
                
                if self._stato == StatoCircuito.HALF_OPEN:
                    self._successi_consecutivi += 1
                    if self._successi_consecutivi >= self.config.soglia_successi_halfopen:
                        self._passa_a_closed()
                else:
                    self._fallimenti_consecutivi = 0  # Reset su successo
            
            return result
        
        except Exception as e:
            with self._lock:
                self._totale_fallimenti += 1
                self._fallimenti_consecutivi += 1
                self._successi_consecutivi = 0
                
                if self._stato == StatoCircuito.HALF_OPEN:
                    # Probe fallita → torna OPEN
                    logger.warning("[CircuitBreaker:%s] Probe fallita → OPEN", self.nome)
                    self._stato = StatoCircuito.OPEN
                    self._opened_at = time.monotonic()
                elif (self._stato == StatoCircuito.CLOSED
                      and self._fallimenti_consecutivi >= self.config.soglia_fallimenti):
                    self._passa_a_open()
            
            raise

    def statistiche(self) -> StatisticheBreaker:
        """Ritorna snapshot statistiche (thread-safe)."""
        with self._lock:
            return StatisticheBreaker(
                stato=self._stato,
                fallimenti_consecutivi=self._fallimenti_consecutivi,
                successi_consecutivi=self._successi_consecutivi,
                totale_chiamate=self._totale_chiamate,
                totale_successi=self._totale_successi,
                totale_fallimenti=self._totale_fallimenti,
                totale_bloccate=self._totale_bloccate,
            )


# ─── Demo interattiva ─────────────────────────────────────────────────────────

def demo_circuit_breaker():
    """Simula un servizio che va giù e poi si riprende."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    
    cb = CircuitBreaker(
        "API_Pagamenti",
        CircuitBreakerConfig(
            soglia_fallimenti=3,
            timeout_open_s=2.0,  # 2 secondi per la demo
            soglia_successi_halfopen=2,
        )
    )
    
    servizio_su = [False]  # Shared state per la simulazione
    
    def chiama_servizio() -> str:
        if not servizio_su[0]:
            raise ConnectionError("Servizio non raggiungibile")
        return "OK"
    
    print("=== DEMO CIRCUIT BREAKER ===\n")
    
    # Fase 1: servizio down → apre circuito
    print("FASE 1: Servizio DOWN → accumula fallimenti")
    for i in range(6):
        try:
            result = cb.chiama(chiama_servizio)
            print(f"  Chiamata {i+1}: {result} | stato={cb.statistiche().stato}")
        except CircuitOpenError as e:
            print(f"  Chiamata {i+1}: BLOCCATA (circuito OPEN) | {e}")
        except ConnectionError as e:
            print(f"  Chiamata {i+1}: FALLITA ({e}) | stato={cb.statistiche().stato}")
    
    # Fase 2: aspetta timeout
    print(f"\nFASE 2: Attesa timeout OPEN ({cb.config.timeout_open_s}s)...")
    time.sleep(cb.config.timeout_open_s + 0.1)
    
    # Fase 3: servizio torna su → prime chiamate in HALF-OPEN
    print("\nFASE 3: Servizio torna UP → probe HALF-OPEN")
    servizio_su[0] = True
    for i in range(4):
        try:
            result = cb.chiama(chiama_servizio)
            print(f"  Chiamata {i+1}: {result} | stato={cb.statistiche().stato}")
        except CircuitOpenError as e:
            print(f"  Chiamata {i+1}: BLOCCATA | {e}")
    
    stats = cb.statistiche()
    print(f"\nSTATISTICHE FINALI:")
    print(f"  Stato:       {stats.stato}")
    print(f"  Totale:      {stats.totale_chiamate}")
    print(f"  Successi:    {stats.totale_successi}")
    print(f"  Fallimenti:  {stats.totale_fallimenti}")
    print(f"  Bloccate:    {stats.totale_bloccate}")


if __name__ == "__main__":
    demo_circuit_breaker()
```

---

## PART C — Idempotency Key in Redis

### C1 — Impossibilità di Exactly-Once

```python
#!/usr/bin/env python3
# file: idempotency/exactly_once_demo.py
"""
Dimostrazione: exactly-once è impossibile in un sistema distribuito.

Il problema: transazione a due fasi impossibile senza coordinatore.
  1. Invio la richiesta al server
  2. Il server la elabora
  3. Il server INVIA la risposta → CRASH prima di ricevere ACK
  
  Stato client: non so se la richiesta è stata elaborata o no.
  Stato server: ha elaborato, ma non sa se il client l'ha ricevuto.
  
SOLUZIONE PRATICA: at-least-once + idempotency key
  - Ritento liberamente
  - Il server riconosce elaborazioni duplicate tramite idempotency key
  - Stesso risultato garantito per la stessa key
"""


def illustra_problema():
    """Illustra il problema con text art."""
    print("""
┌──────────────────────────────────────────────────────────────────┐
│            PERCHÉ EXACTLY-ONCE È IMPOSSIBILE                      │
│                                                                    │
│  Client ──── REQUEST ────▶ Server                                 │
│                              │                                     │
│                              ▼                                     │
│                        ELABORA ✓                                  │
│                              │                                     │
│                              ▼                                     │
│               RISPOSTA ◀──── CRASH 💥                            │
│                                                                    │
│  ┌─────────────────────────────────────────┐                      │
│  │ Client non sa se la request è arrivata  │                      │
│  │ Server ha elaborato ma non sa se ACK    │                      │
│  │ Nessun protocollo può risolvere questo  │                      │
│  │ senza un terzo partecipante (coordinator│                      │
│  └─────────────────────────────────────────┘                      │
│                                                                    │
│  SOLUZIONE: at-least-once + idempotency key                       │
│                                                                    │
│  Client ──── REQUEST + key ────▶ Server                           │
│                                    │                               │
│               RISPOSTA ◀─── check key: GIA VISTA? return stored   │
│                                    │                               │
│               RISPOSTA ◀─── PRIMA VOLTA: elabora + salva + return │
└──────────────────────────────────────────────────────────────────┘
""")
    print("Conclusione: progetta SEMPRE per at-least-once con idempotency.")
    print("Non cercare di costruire exactly-once nell'infrastruttura.\n")
```

### C2 — Idempotency Store con Redis

```python
#!/usr/bin/env python3
# file: idempotency/idempotency_store.py
"""
Idempotency key store su Redis.

Protocollo:
  1. Client genera idempotency_key = UUID v4 (univoco per richiesta logica)
  2. Server: SETNX key "processing" EX TTL → se 0 (esiste già): await poll o return cached
  3. Server elabora
  4. Server: SET key "{json result}" EX TTL (sovrascrive "processing")
  5. Qualsiasi retry futuro: GET key → già elaborato → return cached result

TTL: 24 ore è il valore standard (Stripe usa 24h, molti gateway usano 48h)
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import redis

IDEMPOTENCY_TTL_S = 86400  # 24 ore
PROCESSING_TTL_S = 300      # 5 minuti per processing (timeout massimo operazione)
PROCESSING_SENTINEL = "__PROCESSING__"


class IdempotencyStatus(str, Enum):
    PRIMA_VOLTA = "prima_volta"
    IN_ELABORAZIONE = "in_elaborazione"
    GIA_ELABORATO = "gia_elaborato"


@dataclass
class CheckResult:
    status: IdempotencyStatus
    risultato_cached: Optional[Any] = None


class IdempotencyStore:
    """
    Store Redis per idempotency key con stato processing.
    
    Gestisce tre stati per ogni key:
    - Non esiste: prima volta → il caller deve elaborare
    - PROCESSING: un altro worker sta elaborando (evita doppia elaborazione parallela)
    - JSON result: già elaborato → ritorna cached
    """

    def __init__(self, redis_client: redis.Redis, prefisso: str = "idm"):
        self._r = redis_client
        self._prefisso = prefisso

    def _chiave(self, idempotency_key: str) -> str:
        return f"{self._prefisso}:{idempotency_key}"

    def controlla_e_prenota(self, idempotency_key: str) -> CheckResult:
        """
        Controlla lo stato di una key e la prenota se è la prima volta.
        Atomico via SET NX.
        
        Returns:
            CheckResult con status e risultato cached (se disponibile)
        """
        key = self._chiave(idempotency_key)
        
        # SETNX atomico: set solo se non esiste
        # Se ritorna True → prima volta
        prenotato = self._r.set(
            key,
            PROCESSING_SENTINEL,
            ex=PROCESSING_TTL_S,
            nx=True,  # Set iF Not eXists
        )
        
        if prenotato:
            return CheckResult(status=IdempotencyStatus.PRIMA_VOLTA)
        
        # La key esiste già — leggi il valore
        valore = self._r.get(key)
        if valore is None:
            # Race condition: scaduta tra SET NX e GET → tratta come prima volta
            return CheckResult(status=IdempotencyStatus.PRIMA_VOLTA)
        
        valore_str = valore.decode() if isinstance(valore, bytes) else valore
        
        if valore_str == PROCESSING_SENTINEL:
            return CheckResult(status=IdempotencyStatus.IN_ELABORAZIONE)
        
        # È un risultato JSON → già elaborato
        try:
            risultato = json.loads(valore_str)
            return CheckResult(
                status=IdempotencyStatus.GIA_ELABORATO,
                risultato_cached=risultato
            )
        except json.JSONDecodeError:
            # Dato corrotto → riprocessa
            return CheckResult(status=IdempotencyStatus.PRIMA_VOLTA)

    def salva_risultato(
        self,
        idempotency_key: str,
        risultato: Any,
        ttl_s: int = IDEMPOTENCY_TTL_S
    ) -> None:
        """Salva il risultato finale. Sovrascrive il PROCESSING sentinel."""
        key = self._chiave(idempotency_key)
        self._r.set(key, json.dumps(risultato), ex=ttl_s)

    def segna_errore_permanente(self, idempotency_key: str, errore: str) -> None:
        """
        Segna che questa key ha avuto un errore permanente.
        I retry futuri riceveranno l'errore cached invece di ritentare.
        """
        key = self._chiave(idempotency_key)
        self._r.set(
            key,
            json.dumps({"error": errore, "permanent": True}),
            ex=IDEMPOTENCY_TTL_S
        )

    def cancella(self, idempotency_key: str) -> None:
        """Rimuovi la key (es. per testing o rollback)."""
        self._r.delete(self._chiave(idempotency_key))


# ─── Context manager per uso semplice ─────────────────────────────────────────

from contextlib import contextmanager

@contextmanager
def elaborazione_idempotente(
    store: IdempotencyStore,
    idempotency_key: str,
    nome: str = "operazione",
):
    """
    Context manager che gestisce il ciclo completo idempotency.
    Yields il risultato cached se disponibile, altrimenti None.
    
    Uso:
        with elaborazione_idempotente(store, key) as cached:
            if cached is not None:
                return cached  # Già elaborato
            # ... fai il lavoro ...
            # Il context manager salva il risultato automaticamente
    """
    check = store.controlla_e_prenota(idempotency_key)
    
    if check.status == IdempotencyStatus.GIA_ELABORATO:
        print(f"  [{nome}] Key {idempotency_key[:8]}... già elaborata → cached")
        yield check.risultato_cached
        return
    
    if check.status == IdempotencyStatus.IN_ELABORAZIONE:
        print(f"  [{nome}] Key {idempotency_key[:8]}... in elaborazione da altro worker")
        yield None
        return
    
    # Prima volta — esegui e salva
    risultato_holder = [None]
    errore_holder = [None]
    
    try:
        yield risultato_holder
        # Il caller imposta risultato_holder[0] = risultato
        if risultato_holder[0] is not None:
            store.salva_risultato(idempotency_key, risultato_holder[0])
    except Exception as e:
        errore_holder[0] = str(e)
        store.segna_errore_permanente(idempotency_key, str(e))
        raise


def genera_idempotency_key(payload: dict) -> str:
    """
    Genera una idempotency key deterministica dal payload.
    ATTENZIONE: UUID v4 è random — usare solo se il client decide la key.
    UUID v5 (namespace + payload hash) è deterministico.
    """
    import hashlib
    # Ordina il payload per garantire serializzazione deterministica
    payload_str = json.dumps(payload, sort_keys=True)
    return str(uuid.uuid5(uuid.NAMESPACE_OID, payload_str))


# ─── Demo ─────────────────────────────────────────────────────────────────────

def demo(r: redis.Redis):
    store = IdempotencyStore(r, prefisso="demo")
    
    print("=== DEMO IDEMPOTENCY STORE ===\n")
    
    def processa_ordine(ordine_id: str, importo: float, key: str) -> dict:
        check = store.controlla_e_prenota(key)
        
        if check.status == IdempotencyStatus.GIA_ELABORATO:
            print(f"  [{ordine_id}] GIÀ ELABORATO → ritorno cached")
            return check.risultato_cached
        
        if check.status == IdempotencyStatus.IN_ELABORAZIONE:
            print(f"  [{ordine_id}] IN ELABORAZIONE → attendo o ritorno 202")
            return {"status": "pending"}
        
        # Prima volta — elabora
        print(f"  [{ordine_id}] PRIMA VOLTA → elaboro...")
        time.sleep(0.01)  # Simula elaborazione
        risultato = {
            "ordine_id": ordine_id,
            "importo": importo,
            "stato": "confermato",
            "timestamp": time.time(),
        }
        store.salva_risultato(key, risultato)
        return risultato
    
    # Simula 3 retry della stessa richiesta
    ordine_key = str(uuid.uuid4())
    print("Simulazione 3 retry della stessa richiesta:")
    for i in range(3):
        result = processa_ordine("ORD-001", 99.99, ordine_key)
        print(f"  Tentativo {i+1}: stato={result.get('stato', result.get('status'))}")
    
    # Key diversa = nuova elaborazione
    print("\nNuova key → nuova elaborazione:")
    result = processa_ordine("ORD-002", 149.99, str(uuid.uuid4()))
    print(f"  Risultato: {result}")


if __name__ == "__main__":
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    try:
        r.ping()
        demo(r)
    except redis.ConnectionError:
        print("ERRORE: Redis non raggiungibile. Avvia: docker run -d -p 6379:6379 redis:7.2-alpine")
    finally:
        r.close()
```

---

## PART D — Pipeline Integrata

### D1 — Processing Pipeline con tutti i Pattern

```python
#!/usr/bin/env python3
# file: pipeline/processing_pipeline.py
"""
Pipeline completa: idempotency + circuit breaker + retry + logging strutturato.
Simula un worker che processa messaggi da una coda.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

import redis
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)

# Import dai moduli precedenti
# from circuit_breaker.breaker import CircuitBreaker, CircuitOpenError, CircuitBreakerConfig
# from idempotency.idempotency_store import IdempotencyStore, IdempotencyStatus

logger = logging.getLogger(__name__)


@dataclass
class MessaggioOrdine:
    ordine_id: str
    cliente_id: str       # Solo ID — niente PII nel messaggio!
    importo: float
    valuta: str
    idempotency_key: str  # Generato dal producer


class PaymentGatewayError(Exception):
    """Errore gateway pagamento — retriable."""


class PaymentRejectedError(Exception):
    """Pagamento rifiutato — NON retriable (carta non valida, fondi insufficienti)."""


class ProcessingPipeline:
    """
    Worker pipeline con tutti i pattern di resilienza.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        gateway_url: str = "http://gateway.example.com",
    ):
        from circuit_breaker.breaker import CircuitBreaker, CircuitBreakerConfig
        from idempotency.idempotency_store import IdempotencyStore
        
        self._idempotency = IdempotencyStore(redis_client, prefisso="ordini")
        self._gateway_cb = CircuitBreaker(
            "payment_gateway",
            CircuitBreakerConfig(
                soglia_fallimenti=5,
                timeout_open_s=30.0,
                soglia_successi_halfopen=2,
            )
        )
        self._gateway_url = gateway_url

    @retry(
        retry=retry_if_exception_type(PaymentGatewayError),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=2, max=20),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _chiama_gateway(self, messaggio: MessaggioOrdine) -> dict:
        """
        Chiama il gateway pagamenti attraverso il circuit breaker.
        retry solo per PaymentGatewayError (errori transitori).
        """
        from circuit_breaker.breaker import CircuitOpenError
        try:
            return self._gateway_cb.chiama(
                lambda: self._http_post_gateway(messaggio)
            )
        except CircuitOpenError as e:
            # Circuit aperto → non ritentare, propaga
            logger.error(
                "Gateway circuit OPEN per %s — skip retry",
                messaggio.ordine_id
            )
            raise  # Non wrapped in PaymentGatewayError → non retriato

    def _http_post_gateway(self, messaggio: MessaggioOrdine) -> dict:
        """Chiamata HTTP reale al gateway (simulata)."""
        import random
        # Simula vari scenari
        r = random.random()
        if r < 0.1:
            raise PaymentRejectedError("Carta non valida")
        if r < 0.3:
            raise PaymentGatewayError("Gateway timeout")
        return {"transaction_id": f"TXN-{uuid.uuid4().hex[:8]}", "status": "approved"}

    def processa(self, messaggio: MessaggioOrdine) -> dict:
        """
        Punto di ingresso principale.
        1. Controlla idempotency key
        2. Elabora con circuit breaker + retry
        3. Salva risultato
        """
        from idempotency.idempotency_store import IdempotencyStatus
        from circuit_breaker.breaker import CircuitOpenError
        
        # Step 1: Idempotency check
        check = self._idempotency.controlla_e_prenota(messaggio.idempotency_key)
        
        if check.status == IdempotencyStatus.GIA_ELABORATO:
            logger.info(
                "Ordine %s già elaborato (idempotent) → cached",
                messaggio.ordine_id
            )
            return check.risultato_cached
        
        if check.status == IdempotencyStatus.IN_ELABORAZIONE:
            logger.warning(
                "Ordine %s in elaborazione da altro worker",
                messaggio.ordine_id
            )
            return {"status": "processing", "ordine_id": messaggio.ordine_id}
        
        # Step 2: Elabora (prima volta)
        logger.info("Processing ordine %s (%.2f %s)",
                    messaggio.ordine_id, messaggio.importo, messaggio.valuta)
        
        try:
            gateway_result = self._chiama_gateway(messaggio)
            
            # Step 3: Salva risultato idempotente
            risultato = {
                "ordine_id": messaggio.ordine_id,
                "transaction_id": gateway_result["transaction_id"],
                "status": gateway_result["status"],
                "importo": messaggio.importo,
                "valuta": messaggio.valuta,
            }
            self._idempotency.salva_risultato(messaggio.idempotency_key, risultato)
            
            logger.info("Ordine %s processato → TXN %s",
                        messaggio.ordine_id, gateway_result["transaction_id"])
            return risultato
        
        except PaymentRejectedError as e:
            # Errore permanente — salva nel idempotency store per non ritentare
            self._idempotency.segna_errore_permanente(
                messaggio.idempotency_key, str(e)
            )
            logger.error("Ordine %s rifiutato (permanente): %s", messaggio.ordine_id, e)
            raise
        
        except Exception as e:
            # Errore transitorio — non salva nel idempotency (permettiamo retry)
            logger.error("Ordine %s fallito (transitorio): %s", messaggio.ordine_id, e)
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    print("Pipeline integrata — avvia Redis prima di eseguire")
    print("docker run -d -p 6379:6379 redis:7.2-alpine")
```

---

## Esercizi

### Esercizio 1 — Misura il Thundering Herd (15 min)

```python
# Simula 50 client che ritentano tutti nello stesso momento
# Confronta il numero di richieste/secondo con:
# a) No jitter → tutti chiamano contemporaneamente
# b) Full jitter → distribuiti nel tempo

import random
import collections

def simula_retry_timing(n_client: int, jitter: bool) -> dict:
    """Ritorna {secondo: n_richieste} per visualizzare la distribuzione."""
    richieste_per_secondo = collections.Counter()
    
    for _ in range(n_client):
        for tentativo in range(3):
            base_delay = min(60, 1 * (2 ** tentativo))
            if jitter:
                delay = random.uniform(0, base_delay)
            else:
                delay = base_delay
            secondo = int(delay)
            richieste_per_secondo[secondo] += 1
    
    return dict(sorted(richieste_per_secondo.items()))

print("No jitter:", simula_retry_timing(50, jitter=False))
print("Full jitter:", simula_retry_timing(50, jitter=True))
```

### Esercizio 2 — Circuit Breaker con Health Check (30 min)

Estendi `CircuitBreaker` con:
- Metodo `health_check_url: str` — URL pingato in HALF-OPEN invece di aspettare una chiamata reale
- Metodo `reset_forzato()` — amministrativo, resetta a CLOSED (con log di audit)
- Esporta le statistiche in formato Prometheus (testo plain)

### Esercizio 3 — Idempotency Key Distribuita (20 min)

Genera idempotency key deterministiche basate sul contenuto:
```python
def genera_key_deterministica(endpoint: str, payload: dict) -> str:
    """
    Key = UUID v5(namespace, endpoint + sorted_payload_json)
    Stessi dati → stessa key → idempotenza garantita anche se il client non ha persistenza
    """
    pass
```

---

## Riferimenti

- AWS Architecture Blog — "Exponential Backoff and Jitter"
- Michael Nygard — "Release It!" (Circuit Breaker pattern)
- Stripe Idempotency Keys: https://stripe.com/docs/api/idempotent_requests
- tenacity docs: https://tenacity.readthedocs.io/
- Modulo sorgente: `17-retry-idempotency-pattern.md`
