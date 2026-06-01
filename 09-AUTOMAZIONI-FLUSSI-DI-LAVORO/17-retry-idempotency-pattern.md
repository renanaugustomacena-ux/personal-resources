---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 17
titolo: "Pattern Retry, Idempotency e Exactly-Once nelle Automazioni"
versione: "indipendente da piattaforma"
livello: "proficient → expert"
prerequisiti: ["Modulo 04 — Integrazione API", "Modulo 15 — Webhook Security HMAC", "Modulo 16 — Event-Driven Architecture", "Two Generals Problem"]
obiettivi:
  - "Implementare retry con exponential backoff e jitter per evitare retry-storm sincronizzati"
  - "Progettare idempotency key con TTL corretto per garantire effective-once semantics"
  - "Dimostrare perche exactly-once e impossibile in sistemi distribuiti e applicare at-least-once + dedup"
  - "Configurare circuit breaker con stati closed/open/half-open per proteggere servizi downstream"
  - "Integrare pattern retry e idempotency in workflow n8n, Temporal e code-based"
tag: [retry, idempotency, exactly-once, circuit-breaker, exponential-backoff, jitter, distributed-systems]
---

# Pattern Retry, Idempotency e Exactly-Once nelle Automazioni

> **Obiettivi di apprendimento**
> 1. Implementare retry con exponential backoff e jitter per evitare retry-storm sincronizzati
> 2. Progettare idempotency key con TTL corretto per garantire effective-once semantics
> 3. Dimostrare perche exactly-once e impossibile in sistemi distribuiti e applicare at-least-once + dedup
> 4. Configurare circuit breaker con stati closed/open/half-open per proteggere servizi downstream
> 5. Integrare pattern retry e idempotency in workflow n8n, Temporal e code-based

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 4 — Pattern di affidabilita · Modulo 17
> **Prerequisiti:** Moduli 04, 15, 16; concetto Two Generals Problem.
> **Obiettivi:** retry exponential backoff con jitter; idempotency key; exactly-once impossibile in distributed systems; at-least-once + dedup = effective once.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** proficient → expert
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida

1. **Exactly-once e impossibile in distributed.** Pretendere = bug. Pattern: at-least-once + idempotency.
2. **Retry exponential backoff + jitter.** Senza jitter, retry-storm sincronizzato.
3. **Circuit breaker dopo N fallimenti consecutivi.** Smetti di battere su servizio down.
4. **Idempotency key TTL >= max retry window.** Se TTL < retry window, dedup fallisce.
5. **Vendor retry knobs coordinano con tua idempotency.** Stripe retry 3x; tua idempotency deve coprire 3+ ricezioni.

---

## Indice

- [Panoramica](#panoramica)
- [Concetti Fondamentali](#concetti-fondamentali)
- [Perché Retry sono Necessari](#perché-retry-sono-necessari)
- [Tassonomia delle Delivery Semantics](#tassonomia-delle-delivery-semantics)
- [Retry Strategies](#retry-strategies)
- [Backoff: Exponential, Jitter, Decorrelated Jitter](#backoff-exponential-jitter-decorrelated-jitter)
- [Librerie di Retry per Linguaggio](#librerie-di-retry-per-linguaggio)
- [Circuit Breaker Pattern](#circuit-breaker-pattern)
- [Idempotency Keys](#idempotency-keys)
- [Idempotent Operations Design](#idempotent-operations-design)
- [Exactly-Once via Two-Phase Commit](#exactly-once-via-two-phase-commit)
- [Transactional Outbox Pattern](#transactional-outbox-pattern)
- [Inbox Pattern Lato Consumer](#inbox-pattern-lato-consumer)
- [Saga Compensation](#saga-compensation)
- [Esempi Pratici](#esempi-pratici)
- [Anti-Pattern e Errori Comuni](#anti-pattern-e-errori-comuni)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Ogni sistema di automazione che attraversa la rete è destinato a fallire prima o poi. Una API esterna restituisce 503, una connessione TCP cade per il riavvio di un load balancer, un rate limit viene superato, un broker accumula backpressure, un nodo del database va in manutenzione. La differenza tra un'automazione fragile e una resiliente non è l'assenza di fallimenti — è la loro gestione disciplinata. I pattern retry e idempotency sono la base operativa di questa disciplina.

Il problema centrale è una tensione tra due obiettivi apparentemente opposti: vogliamo che ogni operazione abbia successo (quindi ritentiamo) ma non vogliamo che la stessa operazione avvenga due volte (quindi serve idempotency). Senza idempotency, un retry di un pagamento Stripe dopo un timeout potrebbe addebitare due volte il cliente. Senza retry, una transazione persa per un errore transitorio richiede intervento manuale. Tutti i protocolli di consegna distribuita modernamente robusti — webhook firmati di Stripe, AWS SNS, Kafka exactly-once, Temporal workflows — risolvono il problema con la stessa ricetta: at-least-once delivery + idempotency consumer-side = exactly-once effect.

Questa guida copre le strategie di retry (immediate, fixed, exponential, jittered), l'implementazione dell'idempotency tramite chiavi e operazioni naturalmente idempotenti, i pattern transactional outbox e inbox per garantire exactly-once effect tra database e message broker, le compensazioni saga per workflow distribuiti long-running, e gli anti-pattern che amplificano i fallimenti anziché contenerli (retry storm, dead-end retry, retry su 4xx). Gli esempi sono in Python, Node.js, Go e Bash, calati su scenari realistici: integrazione Stripe, retry in n8n/Make, processamento batch fatture, integrazione AS400 legacy.

---

## Concetti Fondamentali

Un'operazione è **idempotente** se applicarla N volte produce lo stesso risultato di applicarla una volta. `SET x = 5` è idempotente. `INCREMENT x` non lo è. `DELETE FROM users WHERE id = 42` è idempotente (la seconda volta non fa nulla). `INSERT INTO users (id, ...) VALUES (42, ...)` non lo è di default (la seconda volta dà conflict).

Un **retry** è la rietribuzione automatica di un'operazione fallita. Il **backoff** è il ritardo crescente tra retry successivi, per non saturare il sistema downstream già in difficoltà. Il **jitter** è la randomizzazione del backoff, per evitare che molti client ritentino sincronizzati creando "thundering herd".

Un **idempotency key** è un identificatore univoco che il client invia con la richiesta, e che il server usa per rilevare duplicati. La stessa chiave invocata due volte non produce due esecuzioni — la seconda restituisce il risultato cached della prima.

Le **delivery semantics** definiscono quante volte un messaggio può essere consegnato:

- **At-most-once**: 0 o 1 volta. Il messaggio può essere perso ma mai duplicato. Tipico di UDP, fire-and-forget, telemetria a basso valore.
- **At-least-once**: 1 o più volte. Il messaggio non viene perso ma può essere duplicato. È il default robusto di Kafka, RabbitMQ, SQS, webhook Stripe.
- **Exactly-once**: esattamente 1 volta. Tecnicamente impossibile in un sistema distribuito senza coordinazione (vedi teorema dei due generali). In pratica si ottiene con at-least-once + idempotency = "exactly-once effect".

---

## Perché Retry sono Necessari

I motivi per cui un'operazione di rete fallisce sono numerosi e raramente correlati a bug del codice chiamante:

**Network failure transienti**: TCP reset, connection refused, DNS lookup failure, routing change. Tipicamente risolti in pochi secondi.

**Server temporary unavailable (5xx)**: il servizio è in restart, in deploy rolling, sotto carico picco. Risposte 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout. Quasi sempre risolte da un retry dopo backoff.

**Rate limit (429 Too Many Requests)**: il client ha superato la soglia. Il server tipicamente restituisce header `Retry-After` con il delay raccomandato. Retry rispettoso della direttiva è obbligatorio.

**Timeout lato client**: la risposta non arriva entro il deadline. Pericoloso perché non sappiamo se il server ha completato l'operazione. Idempotency qui è critica.

**Lock contention nel database**: deadlock, lock wait timeout. Retry immediato ha alta probabilità di successo perché la finestra di contesa è breve.

**Quota / budget exceeded**: variante del rate limit, tipicamente risolto solo con escalation o reset periodico — retry inutile.

**Errori applicativi 4xx**: validazione fallita, autenticazione negata, risorsa non trovata. Retry inutile e dannoso — fissa il problema, non ritentare.

La regola d'oro: ritenta solo errori che hanno probabilità ragionevole di risolversi spontaneamente. Per tutti gli altri, fail fast, log, alert.

---

## Tassonomia delle Delivery Semantics

### At-Most-Once

Il produttore invia il messaggio, dimentica. Nessun ack richiesto. Implementazione semplice, latenza minima, throughput massimo. Il messaggio può essere perso per qualsiasi failure di rete o consumer.

Use case appropriati: telemetria di alta frequenza dove la perdita di un sample è ininfluente (CPU usage ogni secondo, sensor IoT con campionamento alto), log non critici, metriche di analytics aggregabili.

### At-Least-Once

Il produttore richiede ack del consumer. Se non riceve ack entro timeout, ritrasmette. Il consumer può ricevere lo stesso messaggio più volte (per timeout di ack, retry del produttore, redelivery del broker).

Use case appropriati: la maggior parte dei sistemi business. Eventi di dominio, comandi, notifiche, integrazioni. Sempre con idempotency consumer-side.

### Exactly-Once (l'illusione)

L'illusione è il termine usato dalla letteratura distribuita. Tecnicamente, exactly-once delivery end-to-end senza idempotency è impossibile in presenza di failure. Quello che si ottiene è una di queste configurazioni:

1. **At-least-once + idempotent consumer**: il consumer deduplica internamente. Sistema robusto e generale.
2. **Transactional broker (Kafka exactly-once semantics)**: Kafka con transazioni atomiche tra produce e commit offset garantisce exactly-once *all'interno del cluster Kafka*. Quando il consumer scrive in un sistema esterno (DB, API), serve comunque idempotency.
3. **Two-phase commit (XA transactions)**: coordinator distribuito che commit atomicamente su più resource manager. Fragile, costoso, raramente usato in pratica moderna.

In nessun caso esiste exactly-once "magia" — sotto il cofano c'è sempre at-least-once + meccanismo di deduplica.

---

## Retry Strategies

### Immediate Retry

Ritenta subito senza delay. Adatto solo per failure veramente istantanee (lock contention DB, race condition transienta). Limitare a 2-3 tentativi massimo per evitare di amplificare il problema.

```python
def with_immediate_retry(fn, max_attempts=3):
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError as e:
            last_exc = e
    raise last_exc
```

### Fixed Delay

Retry con delay costante (es. 1 secondo tra tentativi). Semplice ma rischiosa: molti client che ritentano sincronizzati a intervalli fissi creano "thundering herd" sul downstream.

```python
import time

def with_fixed_delay(fn, max_attempts=5, delay_s=1):
    for attempt in range(max_attempts):
        try:
            return fn()
        except TransientError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(delay_s)
```

### Exponential Backoff

Il delay raddoppia ad ogni tentativo: 1s, 2s, 4s, 8s, 16s. Dà al downstream tempo crescente di ripristinarsi. Cap massimo per evitare delay assurdi (es. max 60s).

Formula base: `delay = base * 2^attempt`

```python
def exponential_backoff(attempt: int, base_s: float = 1.0, cap_s: float = 60.0) -> float:
    return min(cap_s, base_s * (2 ** attempt))

# Senza jitter: 1, 2, 4, 8, 16, 32, 60, 60, ...
```

### Exponential Backoff + Jitter

Aggiungi randomizzazione per de-sincronizzare i client. Tre varianti dal paper AWS Architecture Blog "Exponential Backoff and Jitter":

**Full Jitter** — il delay è uniforme tra 0 e l'exponential value:

```python
import random

def full_jitter(attempt: int, base_s: float = 1.0, cap_s: float = 60.0) -> float:
    expo = min(cap_s, base_s * (2 ** attempt))
    return random.uniform(0, expo)
```

**Equal Jitter** — metà del delay è exponential, metà è random:

```python
def equal_jitter(attempt: int, base_s: float = 1.0, cap_s: float = 60.0) -> float:
    expo = min(cap_s, base_s * (2 ** attempt))
    return expo / 2 + random.uniform(0, expo / 2)
```

**Decorrelated Jitter** — il delay corrente dipende dal precedente, non dal counter:

```python
def decorrelated_jitter(prev_delay: float, base_s: float = 1.0, cap_s: float = 60.0) -> float:
    return min(cap_s, random.uniform(base_s, prev_delay * 3))
```

In pratica, **full jitter** è il default robusto raccomandato per la maggior parte dei casi.

### Formula Pratica Combinata

```python
def jittered_backoff(attempt: int, base_s: float = 1.0, cap_s: float = 60.0) -> float:
    """delay = random(0, min(cap, base * 2^attempt))"""
    return random.uniform(0, min(cap_s, base_s * (2 ** attempt)))
```

---

## Librerie di Retry per Linguaggio

### Python — tenacity

`tenacity` è la libreria de facto. Decorator-based, supporta tutte le strategie, retry condizionato per eccezione/risultato, hook before/after.

```python
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
import logging
import requests

logger = logging.getLogger(__name__)

class TransientError(Exception):
    pass

@retry(
    stop=stop_after_attempt(6) | stop_after_delay(120),
    wait=wait_exponential_jitter(initial=1, max=30),
    retry=retry_if_exception_type((TransientError, requests.ConnectionError, requests.Timeout)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def fetch_invoice(invoice_id: str) -> dict:
    response = requests.get(
        f'https://api.example.com/invoices/{invoice_id}',
        timeout=10,
    )
    if response.status_code >= 500:
        raise TransientError(f'Server error: {response.status_code}')
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        raise TransientError(f'Rate limited, retry after {retry_after}s')
    response.raise_for_status()
    return response.json()
```

### Node.js — p-retry

```javascript
import pRetry, { AbortError } from 'p-retry';
import { fetch } from 'undici';

async function fetchInvoice(invoiceId) {
  return pRetry(
    async () => {
      const res = await fetch(`https://api.example.com/invoices/${invoiceId}`, {
        signal: AbortSignal.timeout(10_000),
      });
      if (res.status >= 400 && res.status < 500) {
        throw new AbortError(`Client error ${res.status} — non ritentabile`);
      }
      if (!res.ok) {
        throw new Error(`Server error ${res.status}`);
      }
      return res.json();
    },
    {
      retries: 5,
      factor: 2,
      minTimeout: 1000,
      maxTimeout: 30_000,
      randomize: true,
      onFailedAttempt: (error) => {
        console.warn(`Tentativo ${error.attemptNumber} fallito: ${error.message}. Restano ${error.retriesLeft}.`);
      },
    },
  );
}
```

### Go — cenkalti/backoff

```go
package main

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/cenkalti/backoff/v4"
)

func fetchInvoice(ctx context.Context, invoiceID string) ([]byte, error) {
	var body []byte

	operation := func() error {
		req, _ := http.NewRequestWithContext(ctx, "GET", "https://api.example.com/invoices/"+invoiceID, nil)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		if resp.StatusCode >= 400 && resp.StatusCode < 500 {
			return backoff.Permanent(errors.New("client error, non ritentabile"))
		}
		if resp.StatusCode >= 500 {
			return errors.New("server error")
		}
		return nil
	}

	expo := backoff.NewExponentialBackOff()
	expo.InitialInterval = 1 * time.Second
	expo.MaxInterval = 30 * time.Second
	expo.MaxElapsedTime = 2 * time.Minute

	err := backoff.Retry(operation, backoff.WithContext(expo, ctx))
	return body, err
}
```

### Bash con curl

```bash
#!/usr/bin/env bash
set -euo pipefail

retry_curl() {
  local url="$1"
  local max_attempts=5
  local attempt=1
  local delay=1

  while (( attempt <= max_attempts )); do
    if curl --fail --silent --show-error --max-time 10 "$url"; then
      return 0
    fi
    local status=$?
    if (( attempt == max_attempts )); then
      echo "Failed after $max_attempts attempts" >&2
      return $status
    fi
    local jitter=$(( RANDOM % delay + 1 ))
    sleep "$jitter"
    delay=$(( delay * 2 ))
    if (( delay > 30 )); then delay=30; fi
    (( attempt++ ))
  done
}

retry_curl "https://api.example.com/health"
```

---

## Circuit Breaker Pattern

Il retry blind è una cattiva idea quando il downstream è saturo: ogni retry aggrava il problema. Il **circuit breaker** monitora il tasso di failure e, superata una soglia, "apre il circuito" — fa fallire immediatamente le chiamate senza nemmeno tentare, dando tempo al downstream di recuperare.

Tre stati:

- **Closed**: chiamate passano normalmente. Si conta il tasso di failure.
- **Open**: tutte le chiamate falliscono immediatamente con `CircuitBreakerOpenError`. Dopo `reset_timeout` si passa a half-open.
- **Half-open**: si lascia passare un numero limitato di chiamate di "prova". Se hanno successo, torna closed; se falliscono, torna open.

Tuning tipico: threshold 50% failure rate su finestra di 20 richieste, reset timeout 30s, success threshold in half-open 5 chiamate.

```python
from pybreaker import CircuitBreaker

invoice_api_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    exclude=[ValueError],
)

@invoice_api_breaker
def call_invoice_api(invoice_id: str) -> dict:
    return requests.get(f'https://api.example.com/invoices/{invoice_id}', timeout=10).json()
```

### Librerie

- **Python**: `pybreaker`, `circuitbreaker`.
- **C#/.NET**: `Polly` (la più matura del panorama, pipeline di policy componibili).
- **Java**: `resilience4j` (successore di Hystrix, ora deprecato).
- **Node.js**: `opossum`.
- **Go**: `sony/gobreaker`.

Combinare retry e circuit breaker: il retry gestisce failure transienti puntuali, il circuit breaker protegge da downstream prolungatamente in difficoltà. Il pattern raccomandato è circuit breaker *fuori* dal retry — quando il breaker è open, il retry interno fallisce subito senza ritentare.

---

## Idempotency Keys

Lo standard de facto per idempotency in API HTTP è l'header `Idempotency-Key` (RFC draft di IETF "The Idempotency-Key HTTP Header Field"). Stripe l'ha popolarizzato e la maggior parte delle API moderne lo supporta.

### Generazione lato Client

Due strategie:

**UUIDv4** — random, semplice, generato fresco per ogni "intent" del client (non per retry). Il retry usa la stessa key.

```python
import uuid

idempotency_key = str(uuid.uuid4())

response = requests.post(
    'https://api.stripe.com/v1/charges',
    headers={'Idempotency-Key': idempotency_key},
    data={'amount': 10870, 'currency': 'eur', 'source': 'tok_visa'},
)
```

**Hash deterministico della richiesta** — calcola SHA-256 di body + endpoint + user. Stesso input → stessa key. Utile quando il client non può persistere la key tra retry (es. funzioni serverless stateless).

```python
import hashlib
import json

def deterministic_key(method: str, path: str, body: dict, user_id: str) -> str:
    payload = json.dumps({
        'method': method,
        'path': path,
        'body': body,
        'user': user_id,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
```

Attenzione: con hash deterministico, due intent semanticamente diversi ma con body identico (es. due richieste consecutive di rinnovo abbonamento) collidono. Includi un timestamp o un counter nel material di hash quando appropriato.

### Lifetime e Storage Server-Side

Stripe mantiene le idempotency key per 24 ore. Per la maggior parte dei sistemi business, 24-72 ore è ragionevole — copre la finestra di retry plausibile e non esplode lo storage.

Implementazione lato server con Redis:

```python
import redis
import json
import hashlib

r = redis.Redis()
IDEMPOTENCY_TTL = 24 * 3600

def handle_request_with_idempotency(idempotency_key: str, request_body: dict, executor):
    cache_key = f'idemp:{idempotency_key}'
    body_hash = hashlib.sha256(json.dumps(request_body, sort_keys=True).encode()).hexdigest()
    
    cached = r.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        if cached_data['body_hash'] != body_hash:
            raise IdempotencyKeyConflict('Same key used with different body')
        return cached_data['response']
    
    lock_key = f'idemp:lock:{idempotency_key}'
    lock_acquired = r.set(lock_key, '1', nx=True, ex=30)
    if not lock_acquired:
        raise ConcurrentRequestError('Request with same key in flight')
    
    try:
        response = executor(request_body)
        r.setex(cache_key, IDEMPOTENCY_TTL, json.dumps({
            'body_hash': body_hash,
            'response': response,
        }))
        return response
    finally:
        r.delete(lock_key)
```

Per garanzie più forti (dato critico, audit), usare tabella DB dedicata anziché Redis:

```sql
CREATE TABLE idempotency_records (
    key VARCHAR(128) PRIMARY KEY,
    body_hash VARCHAR(64) NOT NULL,
    response_body JSONB NOT NULL,
    response_status INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_idempotency_expires ON idempotency_records(expires_at);
```

Cleanup periodico via job: `DELETE FROM idempotency_records WHERE expires_at < NOW()`.

---

## Idempotent Operations Design

L'idempotency esterna (chiavi) è una soluzione di compromesso. Quando possibile, progetta operazioni naturalmente idempotenti.

### PUT vs POST

**PUT** è naturalmente idempotente per definizione HTTP: `PUT /users/42 {name: "Mario"}` può essere ripetuto N volte con lo stesso effetto. **POST** non lo è (di default crea una nuova risorsa ogni volta).

Quando crei una risorsa nuova, preferisci PUT con UUID generato dal client se possibile:

```http
PUT /orders/d4f7a3e0-8c5b-4f9e-9a2c-1e3f7b8d5e6f
Content-Type: application/json

{"customerId": "CUST-449", "items": [...]}
```

Il client genera l'UUID, il server fa upsert. Retry con stessa UUID = nessun duplicato.

### INSERT ... ON CONFLICT

PostgreSQL e MySQL supportano upsert atomico:

```sql
INSERT INTO orders (id, customer_id, total_eur, created_at)
VALUES ('ORD-2026-04-22-7281', 'CUST-449', 108.70, NOW())
ON CONFLICT (id) DO NOTHING;
```

Per logica di update su conflitto:

```sql
INSERT INTO orders (id, customer_id, total_eur, status, updated_at)
VALUES ('ORD-2026-04-22-7281', 'CUST-449', 108.70, 'placed', NOW())
ON CONFLICT (id) DO UPDATE
SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at
WHERE orders.status != 'cancelled';
```

### MERGE / UPSERT

Standard SQL `MERGE` (SQL Server, Oracle, Postgres 15+):

```sql
MERGE INTO orders o
USING (VALUES ('ORD-2026-04-22-7281', 'CUST-449', 108.70)) AS src(id, customer_id, total_eur)
ON o.id = src.id
WHEN NOT MATCHED THEN
    INSERT (id, customer_id, total_eur, created_at) VALUES (src.id, src.customer_id, src.total_eur, NOW())
WHEN MATCHED THEN
    UPDATE SET total_eur = src.total_eur, updated_at = NOW();
```

### Conditional Updates con If-Match (ETag)

Per evitare lost update concorrenti, usare ETag e header `If-Match`:

```http
PUT /orders/ORD-2026-04-22-7281
If-Match: "abc123"
Content-Type: application/json

{"status": "shipped"}
```

Il server confronta l'ETag fornito con la versione corrente. Se non matcha, restituisce `412 Precondition Failed` — il client deve rileggere e ritentare. Combinato con idempotency key, questo previene sia i duplicati che gli update obsoleti.

---

## Exactly-Once via Two-Phase Commit

Il **two-phase commit (2PC)** distribuisce una transazione su più resource manager (RM) coordinati da un transaction manager (TM). Fasi:

1. **Prepare**: TM chiede a tutti gli RM di prepararsi al commit. Ogni RM esegue la transazione localmente e risponde "ready" o "abort". Una volta in "ready", l'RM è obbligato a poter committare anche dopo crash.
2. **Commit/Abort**: se tutti sono "ready", TM ordina commit; altrimenti abort. Tutti gli RM eseguono.

XA è lo standard per 2PC, supportato da DB enterprise (Oracle, DB2, SQL Server, MySQL Cluster) e middleware JEE.

**Quando funziona**: ambiente controllato, pochi RM, latenze basse, RM affidabili che non vanno mai persi a lungo. Ambienti tradizionali enterprise on-premise.

**Quando fallisce**: RM heterogenei (uno è un servizio REST esterno, non XA-aware), failure del TM in fase 2 (RM bloccati in "prepared" indefinitamente), latenza inaccettabile (lock distribuiti su rete), scaling orizzontale impossibile. Questi limiti hanno reso 2PC raramente usato in architetture cloud-native moderne.

---

## Transactional Outbox Pattern

Il problema "dual write": come scrivere atomicamente nel database E pubblicare un evento sul broker? Senza atomicità, hai due scenari di failure:

1. DB scrive, broker fallisce → evento perso, downstream non sa del cambiamento.
2. Broker pubblica, DB fallisce → evento "fantasma", downstream agisce su uno stato che non esiste.

L'**outbox pattern** risolve scrivendo l'evento in una tabella `outbox_events` *nella stessa transazione* del business write. Atomicità garantita dal DB.

```sql
BEGIN;

INSERT INTO orders (id, customer_id, total_eur, status, created_at)
VALUES ('ORD-2026-04-22-7281', 'CUST-449', 108.70, 'placed', NOW());

INSERT INTO outbox_events (id, aggregate_id, event_type, payload, created_at, published)
VALUES (
    gen_random_uuid(),
    'ORD-2026-04-22-7281',
    'OrderPlaced',
    '{"orderId":"ORD-2026-04-22-7281","totalEur":108.70,"customerId":"CUST-449"}',
    NOW(),
    false
);

COMMIT;
```

Un processo separato (relay) legge la tabella e pubblica:

**Polling relay** (semplice, un po' di delay):

```python
import time
import psycopg2
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='kafka:9092', acks='all')
conn = psycopg2.connect(...)

POLL_INTERVAL_S = 1
BATCH_SIZE = 100

while True:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, aggregate_id, event_type, payload
            FROM outbox_events
            WHERE published = false
            ORDER BY created_at
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        """, (BATCH_SIZE,))
        rows = cur.fetchall()
        
        for event_id, agg_id, event_type, payload in rows:
            try:
                future = producer.send(
                    topic=f'orders.{event_type.lower()}',
                    key=agg_id.encode(),
                    value=payload.encode() if isinstance(payload, str) else payload,
                )
                future.get(timeout=10)
                cur.execute("UPDATE outbox_events SET published = true, published_at = NOW() WHERE id = %s", (event_id,))
            except Exception:
                logger.exception(f'Publish failed for event {event_id}, sarà ritentato')
                conn.rollback()
                break
        else:
            conn.commit()
    
    if not rows:
        time.sleep(POLL_INTERVAL_S)
```

**CDC relay** (raccomandato, latenza ms): Debezium legge il WAL Postgres e pubblica automaticamente. Vedi capitolo precedente sulla configurazione.

Nota chiave: il relay deve essere idempotent — se crasha tra publish e mark-as-published, al riavvio può ripubblicare. Il consumer downstream deve essere idempotent (vedi sezione successiva).

---

## Inbox Pattern Lato Consumer

Lo specchio dell'outbox: il consumer scrive in una tabella `inbox_events` (con `message_id` come PK) all'inizio del processing, *nella stessa transazione* del business update.

```python
def process_event_idempotent(message_id: str, event: dict, conn):
    with conn.cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO inbox_events (message_id, processed_at) VALUES (%s, NOW())",
                (message_id,),
            )
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            logger.info(f'Message {message_id} già processato — skip')
            return
        
        update_business_state(cur, event)
        conn.commit()
```

Il vincolo PK su `message_id` garantisce che una seconda esecuzione fallisca al primo INSERT, prima di toccare lo stato di business. Atomic, semplice, efficace.

Cleanup tabella inbox: TTL job che cancella record più vecchi di N giorni (dove N > massima finestra di redelivery del broker).

---

## Saga Compensation

In un workflow distribuito long-running che attraversa più servizi, una vera transazione globale ACID non è praticabile. Si usa il pattern **saga**: sequenza di transazioni locali, ognuna seguita da un evento; se una step fallisce, si eseguono **compensazioni** per le step già completate.

Esempio: prenotazione viaggio composta da volo + hotel + auto.

```
1. ReserveFlight  --> (success) --> emit FlightReserved
2. ReserveHotel   --> (success) --> emit HotelReserved
3. ReserveCar     --> (FAIL)    --> emit CarReservationFailed
   ↓
   COMPENSATION:
   - CancelHotel  (reverse step 2)
   - CancelFlight (reverse step 1)
```

Implementazione choreography (eventi):

```python
# car-service consumer
def on_hotel_reserved(event):
    try:
        car = reserve_car(event['booking_id'])
        publish('saga.events', 'CarReserved', {'booking_id': event['booking_id']})
    except CarUnavailable:
        publish('saga.events', 'CarReservationFailed', {'booking_id': event['booking_id'], 'reason': 'unavailable'})

# hotel-service consumer
def on_car_reservation_failed(event):
    cancel_hotel_reservation(event['booking_id'])
    publish('saga.events', 'HotelCancelled', {'booking_id': event['booking_id']})

# flight-service consumer
def on_hotel_cancelled(event):
    cancel_flight_reservation(event['booking_id'])
    publish('saga.events', 'FlightCancelled', {'booking_id': event['booking_id']})
```

Implementazione orchestration con Temporal:

```python
from temporalio import workflow, activity

@activity.defn
async def reserve_flight(booking_id: str) -> str: ...

@activity.defn
async def cancel_flight(booking_id: str) -> None: ...

@workflow.defn
class TravelBookingWorkflow:
    @workflow.run
    async def run(self, booking_id: str) -> dict:
        compensations = []
        try:
            flight_ref = await workflow.execute_activity(reserve_flight, booking_id)
            compensations.append(('flight', flight_ref))
            
            hotel_ref = await workflow.execute_activity(reserve_hotel, booking_id)
            compensations.append(('hotel', hotel_ref))
            
            car_ref = await workflow.execute_activity(reserve_car, booking_id)
            return {'flight': flight_ref, 'hotel': hotel_ref, 'car': car_ref}
        except Exception:
            for kind, ref in reversed(compensations):
                if kind == 'flight':
                    await workflow.execute_activity(cancel_flight, ref)
                elif kind == 'hotel':
                    await workflow.execute_activity(cancel_hotel, ref)
            raise
```

Temporal gestisce automaticamente persistence, retry, timeout, compensazioni in caso di crash del worker. Per workflow oltre 3-4 step, è la scelta operativa preferita.

---

## Esempi Pratici

### Stripe con Idempotency-Key

```python
import stripe
import uuid

stripe.api_key = os.environ['STRIPE_SECRET_KEY']

def charge_customer(customer_id: str, amount_cents: int, intent_id: str) -> dict:
    """
    intent_id è generato dall'applicazione e persistito ASSIEME al record di transazione.
    Retry usano lo stesso intent_id => Stripe deduplica.
    """
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency='eur',
        customer=customer_id,
        idempotency_key=intent_id,
    )

# Uso:
intent_id = str(uuid.uuid4())
db.save_payment_intent(intent_id, customer_id, amount_cents)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=2, max=30),
    retry=retry_if_exception_type(stripe.error.APIConnectionError),
)
def safe_charge():
    return charge_customer(customer_id, 10870, intent_id)

result = safe_charge()
```

### Retry in n8n

n8n offre retry built-in a livello di nodo: nelle "Settings" del nodo, abilita "Retry on Fail" e configura "Max Tries" e "Wait Between Tries (ms)". Per logica più sofisticata, usa il nodo "Error Trigger" che si attiva su errori del workflow e implementa retry custom con loop.

```json
{
  "parameters": {
    "url": "https://api.example.com/invoices",
    "method": "POST",
    "options": {
      "retry": {
        "maxTries": 5,
        "waitBetweenTries": 2000
      },
      "timeout": 10000
    }
  },
  "name": "POST Invoice",
  "type": "n8n-nodes-base.httpRequest",
  "continueOnFail": true
}
```

In Make (Integromat), ogni modulo ha "Error handlers" con "Retry" route configurabile per max retry e delay. Aggiungi un router su tipo errore per distinguere 5xx (retry) da 4xx (alert + commit).

### Processamento Batch Fatture con Checkpoint

Per processare 100k fatture mensili con riprese da crash:

```python
import sqlite3
from contextlib import closing

CHECKPOINT_DB = '/var/lib/invoice-batch/checkpoint.db'

def init_checkpoint_db():
    with closing(sqlite3.connect(CHECKPOINT_DB)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_invoices (
                invoice_id TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.commit()

def is_processed(invoice_id: str) -> bool:
    with closing(sqlite3.connect(CHECKPOINT_DB)) as conn:
        row = conn.execute(
            'SELECT 1 FROM processed_invoices WHERE invoice_id = ?',
            (invoice_id,),
        ).fetchone()
        return row is not None

def mark_processed(invoice_id: str, status: str):
    with closing(sqlite3.connect(CHECKPOINT_DB)) as conn:
        conn.execute(
            'INSERT OR REPLACE INTO processed_invoices VALUES (?, ?, ?)',
            (invoice_id, datetime.utcnow().isoformat(), status),
        )
        conn.commit()

def batch_process(invoice_ids: list[str]):
    init_checkpoint_db()
    for inv_id in invoice_ids:
        if is_processed(inv_id):
            continue
        try:
            process_single_invoice(inv_id)
            mark_processed(inv_id, 'success')
        except PermanentError as e:
            mark_processed(inv_id, f'failed: {e}')
            logger.error(f'Permanent failure on {inv_id}: {e}')
        except TransientError:
            logger.warning(f'Transient on {inv_id}, riprenderà al prossimo run')
```

Il batch può essere killato in qualsiasi momento — il prossimo run salta automaticamente le fatture già processate. Usa un DB locale (SQLite) o Redis per il checkpoint a seconda del volume e dei vincoli operativi.

### Integrazione AS400 Legacy con Queue + Retry Budget

I sistemi AS400/iSeries non espongono REST API moderne. Tipicamente si usa MQ Series (IBM MQ) o un middleware che traduce. Il pattern robusto:

```
[Modern app] --> [RabbitMQ: as400.commands] --> [as400-bridge worker] --> [AS400 via XML/SOAP/MQ]
                                                       |
                                                       v
                                       [RabbitMQ: as400.responses]
```

Il worker AS400-bridge implementa **retry budget**: massimo N retry per un certo intervallo di tempo (es. 100 retry totali ogni 60s). Se il budget si esaurisce, il worker smette di ritentare e va in degraded mode — questo previene retry storm verso AS400 quando è veramente giù.

```python
from collections import deque
from time import time

class RetryBudget:
    def __init__(self, max_retries: int, window_seconds: int):
        self.max = max_retries
        self.window = window_seconds
        self.events = deque()
    
    def can_retry(self) -> bool:
        now = time()
        while self.events and self.events[0] < now - self.window:
            self.events.popleft()
        return len(self.events) < self.max
    
    def record(self):
        self.events.append(time())

budget = RetryBudget(max_retries=100, window_seconds=60)

def process_message(msg):
    try:
        send_to_as400(msg)
    except TransientError:
        if budget.can_retry():
            budget.record()
            schedule_retry(msg, delay=jittered_backoff(msg.attempt))
        else:
            send_to_dlq(msg, reason='retry budget exhausted')
            alert_oncall('AS400 bridge: retry budget exhausted')
```

---

## Anti-Pattern e Errori Comuni

### Retry Storm

100 client che ritentano sincronizzati ogni 1s = 100 req/s. 1000 client = 1000 req/s. Il downstream già in difficoltà va completamente giù. **Soluzione**: jitter sempre, circuit breaker, retry budget.

### Dead-End Retry su 4xx

Ritentare un 401 Unauthorized non risolverà magicamente la scadenza del token. Ritentare un 422 Unprocessable Entity non correggerà il payload invalido. **Regola**: 4xx non si ritenta mai (eccezione: 408 Request Timeout, 425 Too Early, 429 Too Many Requests con `Retry-After`). 5xx si ritenta con backoff. Network errors si ritentano.

### Hedged Requests

Variante avanzata: invece di aspettare timeout prima di ritentare, invia una seconda richiesta in parallelo dopo P99 di latenza, accetta la prima risposta valida. Riduce la latenza tail al costo di carico aggiuntivo (~10-20%). Adatto solo per operazioni veramente idempotenti e dove la latenza tail è critica. Usato da Google Bigtable, Cassandra. **Trappola**: se non è idempotente, hai duplicati garantiti.

### Retry Senza Limite

`while True: try: ... except: sleep(1); continue`. Sembra robusto, è una bomba a orologeria. Bug permanenti diventano cicli infiniti che bruciano CPU e log. **Sempre** un limite massimo di tentativi e un timeout massimo totale.

### Idempotency-Key Riusato Tra Operazioni Diverse

Se generi una idempotency key fissa `"my-app-v1"` per tutte le richieste, la prima chiamata ha successo, tutte le successive ritornano il primo risultato. Ogni "intent" semantico distinto deve avere la propria key.

### Mescolare Idempotency e Lost Update

Idempotency key garantisce "non duplicare". Non garantisce "applica l'ultima versione". Se due client modificano la stessa risorsa con key diverse, l'ordine di arrivo determina il risultato — possibile lost update. Per quello serve concorrenza ottimistica (ETag/version).

---

## Best Practices

- **Sempre jitter sul backoff**, sempre. Non usare delay fissi in produzione.
- **Distingui errori transient da permanent** nel codice. `TransientError` ritentabile, `PermanentError` no.
- **Cap massimo sui retry**: max 5-7 attempt, max 2 minuti elapsed totale per la maggior parte dei use case.
- **Idempotency by design** quando possibile (PUT, UPSERT, deterministic IDs). Idempotency key come fallback.
- **Outbox pattern non opzionale** quando devi pubblicare eventi correlati a scritture DB.
- **Monitoring del retry rate**: spike di retry indica problema downstream. Allarme su retry rate > 5%.
- **Circuit breaker sulle dipendenze esterne**, sempre. Soglia tipica 50% failure su 20 richieste.
- **DLQ con monitoring + runbook documentato**. Cosa fare quando un messaggio finisce in DLQ deve essere scritto, non ricordato.
- **Testing del fallimento**: chaos engineering. Kill periodici di dipendenze in staging.
- **Idempotency key generata dal client persistita prima dell'invio**: se il client crasha tra generazione e invio, al restart può recuperare la key e ritentare correttamente.

---

## Troubleshooting

**Pagamenti duplicati nonostante idempotency key**: verifica che la key sia generata una sola volta per intent (non rigenerata ad ogni retry). Verifica che lo storage server-side della key non scada prima della finestra di retry. Verifica che non ci siano gateway intermedi che strippano l'header `Idempotency-Key`.

**Retry che non si ferma mai**: cerca `while True` senza limite, o configurazione di `max_attempts` mancante. Verifica che `PermanentError` sia distinta da `TransientError` nel codice.

**Latenza percepita esplosa durante outage**: probabilmente il client sta esaurendo tutti i retry prima di rispondere all'utente. Riduci `max_attempts` per richieste user-facing (3-4 max), aggiungi circuit breaker per fallire fast.

**Outbox table che cresce indefinitamente**: il relay non sta marcando i messaggi come pubblicati. Verifica i log del relay, verifica che il job di cleanup runni periodicamente per cancellare vecchi messaggi pubblicati.

**Inbox table conflict spurioso**: due thread del consumer che processano lo stesso messaggio simultaneamente (race). Usa lock pessimistico o serialization isolation level per la transazione che fa l'INSERT su inbox.

**Saga "stuck" in stato intermedio**: probabilmente una compensation è fallita silenziosamente. In choreography, manca alert su eventi di compensation senza ack. In orchestration con Temporal, ispeziona il workflow stuck via UI e identifica l'activity bloccante.

**429 ricevuti continuamente nonostante backoff**: rispetta `Retry-After`. Se il server lo manda, ignorarlo aggrava il problema. Implementa rate limiting client-side proattivo (token bucket) per restare sotto la soglia.

---

## Riferimenti

- "Exponential Backoff and Jitter" — AWS Architecture Blog: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- "Idempotency-Key HTTP Header Field" — IETF draft: https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/
- Stripe API Idempotency: https://docs.stripe.com/api/idempotent_requests
- "Patterns of Enterprise Application Architecture" (Martin Fowler) — capitoli su Unit of Work, Optimistic Locking
- "Microservices Patterns" (Chris Richardson) — capitoli su Saga, Transactional Outbox
- "Designing Data-Intensive Applications" (Martin Kleppmann) — capitoli su Replication, Transactions
- Polly (.NET): https://github.com/App-vNext/Polly
- resilience4j (Java): https://resilience4j.readme.io/
- tenacity (Python): https://tenacity.readthedocs.io/
- p-retry (Node): https://github.com/sindresorhus/p-retry
- cenkalti/backoff (Go): https://github.com/cenkalti/backoff
- Temporal: https://docs.temporal.io/
- "The Two Generals' Problem" (Gray, 1978) — base teorica dell'impossibilità di exactly-once

---

## Esercizi

1. **Lab — retry library Python.** Implementa decorator `@retry(max_attempts, base_delay, jitter)` con exponential backoff. Test su mock API che fallisce 3x poi succede.
2. **Lab — circuit breaker.** Wrappa una API con circuit breaker (closed → open → half-open) usando `pybreaker` o equivalente.
3. **Stretch — Temporal workflow.** Implementa long-running workflow di 5 step con Temporal; simula crash + recovery.

## Auto-valutazione

1. Exactly-once: perche e impossibile?
2. At-least-once + idempotency = ?
3. Jitter: perche serve?
4. Circuit breaker stati: closed/open/half-open.
5. Idempotency key TTL: come dimensionarlo?

## Collegamenti incrociati

- Modulo 15 — `15-webhook-security-hmac-verifica.md`: idempotency in webhook.
- Modulo 16 — `16-event-driven-architecture-pratica.md`: messaging.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Retry** | Riprovare operazione fallita. |
| **Exponential backoff** | Delay che cresce esponenzialmente. |
| **Jitter** | Random delay per disperdere retry. |
| **Circuit breaker** | Stop tentativi quando servizio down. |
| **Idempotency** | Operazione ripetibile senza side effects. |
| **At-least-once** | Garanzia: messaggio consegnato >= 1 volta. |
| **At-most-once** | Garanzia: messaggio consegnato <= 1 volta. |
| **Exactly-once** | Garanzia matematica impossibile in distributed. |
| **Effective once** | At-least-once + idempotency = no duplicate effetti. |
| **Two Generals Problem** | Risultato classico CS sul consensus. |

---

## Letture e Riferimenti

- Marc Brooker — Exponential Backoff and Jitter. https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- AWS — Retry behavior (SDK & Tools). https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
- Microsoft — Retry pattern (Cloud Design Patterns). https://learn.microsoft.com/en-us/azure/architecture/patterns/retry
- Microsoft — Circuit Breaker pattern. https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- Stripe — Idempotent Requests. https://docs.stripe.com/api/idempotent_requests
- n8n — Error handling and retries. https://docs.n8n.io/flow-logic/error-handling/
- Temporal — Activity retry policies. https://docs.temporal.io/retry-policies
- Kleppmann, Martin. *Designing Data-Intensive Applications*. O'Reilly, 2017. — Cap. 8-9 (fault tolerance, consistency).
- Hohpe, Gregor; Woolf, Bobby. *Enterprise Integration Patterns*. Addison-Wesley, 2003. — Messaging reliability patterns.
