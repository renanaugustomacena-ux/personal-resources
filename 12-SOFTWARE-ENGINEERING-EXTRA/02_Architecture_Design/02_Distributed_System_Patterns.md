---
corso: "SWE Masterclass"
fase: "2 — Architecture & Design"
modulo: "2.2"
titolo: "Distributed System Patterns"
versione: "2026-05-29"
livello: "Advanced"
prerequisiti:
  - "Solid understanding of microservices architecture (Module 01)"
  - "Familiarity with message brokers (Kafka, RabbitMQ) and relational databases"
obiettivi:
  - "Implement sagas with both choreography and orchestration coordination"
  - "Apply the transactional outbox pattern to guarantee at-least-once event delivery"
  - "Design resilient service communication using circuit breaker, bulkhead, and retry patterns"
  - "Evaluate trade-offs between strong and eventual consistency models for a given use case"
  - "Instrument a distributed system with OpenTelemetry for end-to-end tracing"
tag: [distributed-systems, saga, cqrs, event-sourcing, outbox, circuit-breaker, consensus, microservices]
---

# Module 2.2: Distributed System Patterns

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Implement sagas with both choreography and orchestration coordination
> - Apply the transactional outbox pattern to guarantee at-least-once event delivery
> - Design resilient service communication using circuit breaker, bulkhead, and retry patterns
> - Evaluate trade-offs between strong and eventual consistency models for a given use case
> - Instrument a distributed system with OpenTelemetry for end-to-end tracing

> **Module 02.2** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Saga: distributed transaction with compensation.** Choreography vs orchestration.
2. **Event sourcing: state = log of events; replayable.**
3. **CQRS: separate read model + write model.**
4. **Outbox pattern: atomic DB write + message queue.**
5. **Idempotency key + dedup mandatory.**

---

## Table of Contents

1. Data Consistency in Microservices — The Saga Pattern
2. The Transactional Outbox Pattern
3. Resiliency Patterns — Circuit Breaker, Bulkhead, Retry
4. Service Mesh & Sidecar
5. Event-Driven Architecture
6. Eventual Consistency
7. Distributed Tracing
8. Idempotency
9. Distributed Locking
10. Leader Election
11. Putting It Together — A Resilient Order Pipeline
12. Common Pitfalls & Troubleshooting
13. Q&A — Frequently Asked Questions
14. Hands-On Exercises
15. References

---

## 1. Data Consistency in Microservices — The Saga Pattern

In a monolith, a single database transaction guarantees ACID. In microservices, each service owns its database. Cross-service transactions require a different mechanism.

### 1.1 Why 2PC (Two-Phase Commit) Fails in Microservices

**2PC protocol:**
1. **Prepare:** coordinator asks all participants "Can you commit?"
2. **Commit:** if all say "yes," coordinator says "commit."

**Problems in microservices:**
- **Synchronous blocking:** all participants hold locks during the prepare phase.
- **Coordinator is SPOF:** if coordinator crashes between prepare and commit, all participants are in limbo.
- **Heterogeneous stores:** each service may use a different DB (Postgres, MongoDB, Redis) — 2PC requires XA support from all.
- **Latency:** network round trips between services add up.

2PC works within a single database or between a few homogeneous nodes. For cross-service orchestration, use sagas.

### 1.2 The Saga Pattern

A saga is a sequence of local transactions. Each local transaction updates one service's database and publishes an event or sends a command to trigger the next step. If a step fails, previously completed steps are *compensated* (rolled back).

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Order   │───▶│ Payment │───▶│  Stock  │───▶│ Shipping│
│ Service  │    │ Service │    │ Service │    │ Service │
└────┬────┘    └────┬────┘    └────┬────┘    └─────────┘
     │              │              │
     │  Compensate  │  Compensate  │
     │◀─────────────│◀─────────────│
     │  (Cancel     │  (Refund     │
     │   Order)     │   Payment)   │
```

Two coordination styles:

#### Choreography (Event-Driven)

Each service listens for events and decides what to do next. No central controller.

```
1. OrderService:
   - Creates order (status=PENDING)
   - Publishes "OrderCreated" event

2. PaymentService:
   - Listens for "OrderCreated"
   - Charges credit card
   - Publishes "PaymentProcessed" or "PaymentFailed"

3. StockService:
   - Listens for "PaymentProcessed"
   - Reserves inventory
   - Publishes "StockReserved" or "StockInsufficient"

4. ShippingService:
   - Listens for "StockReserved"
   - Creates shipment
   - Publishes "ShipmentCreated"

5. OrderService:
   - Listens for "ShipmentCreated"
   - Updates order to CONFIRMED

COMPENSATION PATH:
- StockService publishes "StockInsufficient"
- PaymentService listens → issues refund → publishes "PaymentRefunded"
- OrderService listens → cancels order
```

**Pros:** Fully decoupled, no SPOF, each service is autonomous.
**Cons:** Hard to visualize the full flow, risk of cyclic event dependencies, debugging is difficult (events scattered across logs).

#### Orchestration (Command-Driven)

A central **Saga Orchestrator** (a state machine) directs each step.

```
┌──────────────────────────────────────────────┐
│              Saga Orchestrator               │
│                                              │
│  State Machine:                              │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
│  │ STARTED │─▶│ PAYMENT  │─▶│  STOCK     │  │
│  │         │  │ PENDING  │  │  PENDING   │  │
│  └─────────┘  └────┬─────┘  └─────┬──────┘  │
│                    │              │          │
│               ┌────▼─────┐  ┌────▼──────┐   │
│               │ PAYMENT  │  │  STOCK    │   │
│               │ DONE     │  │  RESERVED │   │
│               └──────────┘  └─────┬─────┘   │
│                                   │         │
│                          ┌────────▼───────┐  │
│                          │   COMPLETED    │  │
│                          └────────────────┘  │
└──────────────────────────────────────────────┘
```

```python
class OrderSagaOrchestrator:
    """State machine that coordinates the order saga."""

    def __init__(self, payment_client, stock_client, order_repo):
        self._payment = payment_client
        self._stock = stock_client
        self._repo = order_repo

    def execute(self, order_id: UUID) -> None:
        saga_state = SagaState(order_id=order_id, step="STARTED")

        # Step 1: Process payment
        try:
            self._payment.charge(order_id)
            saga_state.step = "PAYMENT_DONE"
        except PaymentFailedError:
            saga_state.step = "FAILED"
            self._repo.cancel_order(order_id)
            return

        # Step 2: Reserve stock
        try:
            self._stock.reserve(order_id)
            saga_state.step = "STOCK_RESERVED"
        except StockInsufficientError:
            saga_state.step = "COMPENSATING"
            self._payment.refund(order_id)  # compensate step 1
            self._repo.cancel_order(order_id)
            return

        # Step 3: Confirm
        self._repo.confirm_order(order_id)
        saga_state.step = "COMPLETED"
```

**Pros:** Clear flow, easy to debug (one place to inspect), straightforward error handling.
**Cons:** Orchestrator is a conceptual SPOF (make it stateless + persistent state), couples the orchestrator to all services.

### 1.3 Choreography vs Orchestration — Decision Matrix

| Factor | Choreography | Orchestration |
|---|---|---|
| Number of steps | < 4 (simple flow) | > 4 (complex flow) |
| Team autonomy | High — each team owns their events | Lower — must coordinate with orchestrator team |
| Visibility | Low — distributed across services | High — state machine shows full flow |
| Error handling | Complex — scattered compensations | Centralized — orchestrator handles all paths |
| Coupling | Loose — services only know events | Tighter — orchestrator knows all services |
| Testing | Hard — requires full event chain | Easier — test orchestrator state machine |

### 1.4 Handling Compensation Failures — The "Zombie Saga"

What if the compensation itself fails?

**Scenario:** Payment charged. Stock reservation fails. We try to refund, but PaymentService is down.

**Solutions:**

1. **Retry with backoff:** Compensations must be idempotent and retried until they succeed. Use a persistent retry queue.

2. **Dead letter queue (DLQ):** After N retries, move the compensation to a DLQ for manual intervention.

3. **Saga log:** Store the saga state in a durable log. A background reconciler picks up stuck sagas and retries compensations.

```python
# Compensation retry with persistent state
class SagaCompensator:
    def __init__(self, saga_store, payment_client, max_retries=10):
        self._store = saga_store
        self._payment = payment_client
        self._max_retries = max_retries

    def compensate(self, saga_id: UUID) -> None:
        saga = self._store.load(saga_id)
        for attempt in range(self._max_retries):
            try:
                if saga.needs_refund:
                    self._payment.refund(saga.order_id)
                    saga.refund_completed = True
                    self._store.save(saga)
                    return
            except ServiceUnavailableError:
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)

        # All retries exhausted — move to DLQ
        self._store.move_to_dlq(saga_id)
        alert_ops_team(saga_id)
```

**Rule:** Compensations must be idempotent. If a refund is executed twice, the customer must not receive double the money. The payment service must check: "Has this refund already been processed?"

---

## 2. The Transactional Outbox Pattern

### 2.1 The Dual-Write Problem

```
App writes to DB:     INSERT INTO orders (id, ...) VALUES (...)   ← SUCCESS
App publishes event:  kafka.produce("OrderCreated", {...})         ← FAIL (broker down)

Result: DB has the order, but no event was published.
        Downstream services never learn about it.
```

This is a **dual-write** — two systems updated non-atomically. Any failure between the two writes leaves the system inconsistent.

### 2.2 Solution: Outbox Table

Write the event *into the same database* as the business data, in the same transaction.

```sql
-- Same transaction
BEGIN;
INSERT INTO orders (id, customer_id, status)
  VALUES ('ord-1', 'cust-1', 'CREATED');

INSERT INTO outbox (id, aggregate_type, aggregate_id, event_type, payload, created_at)
  VALUES (
    'evt-1',
    'Order',
    'ord-1',
    'OrderCreated',
    '{"order_id":"ord-1","customer_id":"cust-1"}',
    NOW()
  );
COMMIT;
```

Both writes succeed or both fail — ACID guarantees within one database.

### 2.3 Relay: Getting Events Out of the Outbox

**Option 1 — Polling Publisher:**

```python
class OutboxPoller:
    """Background thread that polls the outbox table."""
    def __init__(self, db, kafka_producer, poll_interval=1.0):
        self._db = db
        self._kafka = kafka_producer
        self._interval = poll_interval

    def run(self):
        while True:
            rows = self._db.execute(
                "SELECT id, event_type, payload FROM outbox "
                "ORDER BY created_at LIMIT 100"
            )
            for row in rows:
                self._kafka.produce(
                    topic=row["event_type"],
                    value=row["payload"],
                )
                self._db.execute(
                    "DELETE FROM outbox WHERE id = %s", (row["id"],)
                )
            time.sleep(self._interval)
```

**Pros:** Simple, works with any DB.
**Cons:** Polling delay (up to `poll_interval` seconds), DB load from frequent polls.

**Option 2 — Log Tailing (CDC):**

Use Debezium to read the database's write-ahead log (WAL / binlog) and publish changes to Kafka in near-real-time.

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   App    │────▶│ Database │────▶│ Debezium │────▶│  Kafka   │
│          │     │ (outbox  │     │ (CDC)    │     │          │
│          │     │  table)  │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                     WAL/Binlog ──▶
```

**Pros:** Near-real-time, no polling, no missed events.
**Cons:** Operational complexity (Debezium connectors, Kafka Connect), requires WAL access.

### 2.4 Outbox Table Schema

```sql
CREATE TABLE outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(255) NOT NULL,   -- e.g., "Order"
    aggregate_id    VARCHAR(255) NOT NULL,   -- e.g., "ord-1"
    event_type      VARCHAR(255) NOT NULL,   -- e.g., "OrderCreated"
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published       BOOLEAN NOT NULL DEFAULT FALSE
);

-- Index for the poller
CREATE INDEX idx_outbox_unpublished ON outbox (created_at)
  WHERE published = FALSE;
```

---

## 3. Resiliency Patterns

### 3.1 Circuit Breaker

Prevents cascading failures by "failing fast" when a downstream service is unhealthy.

#### State Machine

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ┌──────────┐    error rate    ┌──────────┐            │
│   │  CLOSED  │───exceeds────▶│   OPEN   │            │
│   │ (Normal) │    threshold     │ (Failing │            │
│   └────▲─────┘                  │  Fast)   │            │
│        │                        └────┬─────┘            │
│        │                             │                  │
│        │   success                   │ sleep window     │
│        │                             │ expires          │
│        │                             ▼                  │
│        │                        ┌──────────┐            │
│        └────────────────────────│HALF-OPEN │            │
│              test request       │ (Probe)  │            │
│              succeeds           └────┬─────┘            │
│                                      │                  │
│                     test request     │                  │
│                     fails            │                  │
│                          ┌───────────┘                  │
│                          ▼                              │
│                     Back to OPEN                        │
└─────────────────────────────────────────────────────────┘
```

#### Implementation

```python
import time
from enum import Enum
from threading import Lock


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 30.0,
    ):
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._lock = Lock()

    def call(self, func, *args, **kwargs):
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self._timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise CircuitOpenError(
                        f"Circuit is OPEN. Retry after "
                        f"{self._timeout - (time.time() - self._last_failure_time):.1f}s"
                    )

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self._on_failure()
            raise
        else:
            self._on_success()
            return result

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0


class CircuitOpenError(Exception):
    pass
```

#### Configuration Guidelines

| Parameter | Typical Range | Guidance |
|---|---|---|
| Failure threshold | 3-10 | Lower = faster detection, but more false positives |
| Success threshold | 1-5 | How many successes in HALF_OPEN before closing |
| Timeout (sleep window) | 10-60 seconds | How long OPEN state lasts before probing |
| Monitoring window | 30-120 seconds | Sliding window for counting failures |

**Libraries:** Resilience4j (Java), Polly (.NET), pybreaker (Python), sony/gobreaker (Go).

### 3.2 Bulkhead Pattern

Isolates failures so that a problem in one part of the system does not consume all resources and bring down unrelated parts.

#### Thread Pool Bulkhead

```
┌────────────────────────────────────────────────┐
│                 Service A                       │
│                                                 │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │  Pool: Payment   │  │  Pool: Inventory    │   │
│  │  (10 threads)    │  │  (10 threads)       │   │
│  │                  │  │                     │   │
│  │  ████████░░      │  │  ██░░░░░░░░         │   │
│  │  8/10 busy       │  │  2/10 busy          │   │
│  └─────────────────┘  └─────────────────────┘   │
│                                                 │
│  If Payment pool exhausts all 10 threads:       │
│  → Payment calls fail fast (rejected)           │
│  → Inventory pool is unaffected                 │
└────────────────────────────────────────────────┘
```

```java
// Resilience4j Bulkhead configuration
BulkheadConfig config = BulkheadConfig.custom()
    .maxConcurrentCalls(10)         // max threads
    .maxWaitDuration(Duration.ofMillis(500))  // wait before rejecting
    .build();

Bulkhead paymentBulkhead = Bulkhead.of("payment", config);

Supplier<PaymentResult> decorated = Bulkhead.decorateSupplier(
    paymentBulkhead,
    () -> paymentService.charge(orderId)
);
```

#### Semaphore Bulkhead

Lighter weight — uses a semaphore instead of separate thread pools:

```python
import asyncio

class SemaphoreBulkhead:
    def __init__(self, name: str, max_concurrent: int):
        self._name = name
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rejected = 0

    async def execute(self, coro):
        if self._semaphore.locked():
            self._rejected += 1
            raise BulkheadFullError(f"Bulkhead '{self._name}' is full")

        async with self._semaphore:
            return await coro
```

### 3.3 Retry with Exponential Backoff & Jitter

When a transient failure occurs, retry the operation with increasing delays.

#### The Retry Storm Problem

```
Without jitter (1000 clients fail at t=0):
  t=1s:   1000 clients retry → spike
  t=2s:   1000 clients retry → spike
  t=4s:   1000 clients retry → spike

With jitter:
  t=0.8-1.2s:  clients spread across 400ms window
  t=1.6-2.4s:  spread across 800ms window
  t=3.2-4.8s:  spread across 1600ms window
```

#### Implementation

```python
import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.5,
    retryable_exceptions: tuple = (Exception,),
) -> T:
    """
    Retry a function with exponential backoff and jitter.

    Delay formula: min(max_delay, base_delay * 2^attempt * (1 + random * jitter))
    """
    for attempt in range(max_retries):
        try:
            return func()
        except retryable_exceptions as e:
            if attempt == max_retries - 1:
                raise  # exhausted retries

            delay = min(
                max_delay,
                base_delay * (2 ** attempt)
            )
            jitter = delay * jitter_factor * random.random()
            total_delay = delay + jitter

            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {total_delay:.2f}s"
            )
            time.sleep(total_delay)
```

#### Backoff Strategies Comparison

| Strategy | Formula | Use Case |
|---|---|---|
| **Fixed** | `delay = constant` | Simple, but causes retry storms |
| **Linear** | `delay = base * attempt` | Gentle increase |
| **Exponential** | `delay = base * 2^attempt` | Standard for transient failures |
| **Exponential + jitter** | `delay = base * 2^attempt * rand()` | Best for high-concurrency systems |
| **Decorrelated jitter** | `delay = rand(base, prev_delay * 3)` | AWS recommendation, least correlated |

### 3.4 Timeout Pattern

Never call a remote service without a timeout. Unbounded waits consume threads, connections, and memory.

```python
import httpx

# Connection timeout + read timeout
client = httpx.Client(
    timeout=httpx.Timeout(
        connect=5.0,     # 5s to establish connection
        read=10.0,       # 10s to receive response
        write=5.0,       # 5s to send request
        pool=2.0,        # 2s to acquire connection from pool
    )
)
```

**Guideline:** Set timeouts at every network boundary. If a service has a p99 latency of 200ms, set the timeout to 3-5x that (600ms-1s), not infinity.

### 3.5 Fallback Pattern

When a circuit is open or a call fails after retries, provide a degraded response instead of an error.

```python
class ProductService:
    def __init__(self, product_client, cache):
        self._client = product_client
        self._cache = cache
        self._breaker = CircuitBreaker()

    def get_product(self, product_id: str) -> Product:
        try:
            product = self._breaker.call(
                self._client.fetch, product_id
            )
            self._cache.set(product_id, product)  # update cache
            return product
        except (CircuitOpenError, TimeoutError):
            # Fallback: serve from cache
            cached = self._cache.get(product_id)
            if cached:
                return cached
            # Fallback: return default
            return Product(
                id=product_id,
                name="Product Unavailable",
                price=Money(Decimal("0"), "USD"),
            )
```

### 3.6 Rate Limiter

Protects a service from being overwhelmed.

#### Token Bucket Algorithm

```
Bucket capacity: 100 tokens
Refill rate: 10 tokens/second

Request arrives:
  - If bucket has >= 1 token: take a token, process request
  - If bucket is empty: reject request (429 Too Many Requests)

Bucket refills at 10 tokens/second, up to max 100.
```

```python
import time
from threading import Lock


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self._capacity = capacity
        self._refill_rate = refill_rate  # tokens per second
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                self._capacity,
                self._tokens + elapsed * self._refill_rate,
            )
            self._last_refill = now

            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False
```

#### Sliding Window Algorithm

Counts requests in a rolling time window instead of fixed buckets. Smoother than fixed window but slightly more memory.

---

## 4. Service Mesh & Sidecar Pattern

### 4.1 The Problem

As the number of microservices grows, each service must implement:
- Service discovery
- Load balancing
- Circuit breakers
- Retries
- mTLS
- Observability (metrics, tracing)
- Rate limiting

Implementing this in every service (in every language) is wasteful.

### 4.2 Sidecar Pattern

Deploy a proxy process alongside each service instance. The proxy handles all network concerns. The service communicates only with its local sidecar.

```
┌──────────────────────────────────────────────────┐
│                     Pod / VM                     │
│                                                  │
│  ┌──────────────┐     localhost    ┌───────────┐ │
│  │  Application │ ◀──────────────▶ │  Sidecar  │ │
│  │  (business   │                  │  Proxy    │ │
│  │   logic)     │                  │ (Envoy)   │ │
│  └──────────────┘                  └─────┬─────┘ │
│                                          │       │
└──────────────────────────────────────────┼───────┘
                                           │ mTLS
                                           ▼
                                    Other services
                                    (via their sidecars)
```

The sidecar intercepts all inbound and outbound traffic. The application is unaware of the mesh — it just calls `localhost:port`.

### 4.3 Service Mesh Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Control Plane                        │
│  (Istio's istiod, Linkerd's control plane)             │
│                                                        │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Certificate │  │  Config  │  │  Service         │  │
│  │ Authority   │  │  Server  │  │  Discovery       │  │
│  └─────────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────┬──────────────────────────────┘
                          │ Config push (xDS)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     Data Plane                          │
│                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │ App A + │───▶│ App B + │───▶│ App C + │             │
│  │ Sidecar │    │ Sidecar │    │ Sidecar │             │
│  └─────────┘    └─────────┘    └─────────┘             │
└─────────────────────────────────────────────────────────┘
```

**Control plane:** manages certificates, distributes configuration, handles service discovery.
**Data plane:** the sidecars that proxy actual traffic.

### 4.4 What a Service Mesh Provides

| Feature | Without Mesh | With Mesh |
|---|---|---|
| mTLS between services | Each service manages certificates | Automatic, transparent |
| Retries & timeouts | Library-level (language-specific) | Sidecar-level (language-agnostic) |
| Circuit breaking | Library per service | Configured in control plane |
| Traffic splitting | Load balancer config | Declarative (canary, A/B) |
| Distributed tracing | SDK integration per service | Header propagation by sidecar |
| Access control | Per-service authz code | Policy-based (OPA, RBAC) |

### 4.5 When to Use a Service Mesh

**Good fit:**
- 20+ microservices.
- Polyglot environment (Go, Java, Python services).
- Strong security requirements (mTLS everywhere).
- Complex traffic management (canary, fault injection testing).

**Bad fit:**
- < 10 services (overhead exceeds benefit).
- Single-language environment (use language-native libraries instead).
- Latency-critical paths (sidecar adds ~1-3ms per hop).

---

## 5. Event-Driven Architecture

### 5.1 Core Concepts

**Event:** An immutable record of something that happened. Named in the past tense.

Three types:
- **Domain event:** Business-relevant fact. `OrderPlaced`, `PaymentReceived`.
- **Integration event:** Published for external consumers across bounded contexts.
- **System event:** Infrastructure-level. `InstanceStarted`, `CircuitBreakerOpened`.

### 5.2 Event-Driven Topologies

#### Event Notification

Services publish events without caring who consumes them. Consumer decides how to react.

```
Publisher ──publish──▶ Event Bus ──deliver──▶ Consumer A
                                 ──deliver──▶ Consumer B
                                 ──deliver──▶ Consumer C
```

Low coupling. Publisher does not know consumers exist.

#### Event-Carried State Transfer

Events carry the full state needed by consumers, so consumers do not need to call back to the publisher.

```json
// Lean event (notification only)
{"type": "OrderPlaced", "order_id": "ord-1"}
// Consumer must call OrderService to get details

// Fat event (state transfer)
{
  "type": "OrderPlaced",
  "order_id": "ord-1",
  "customer_name": "Alice",
  "total": 99.99,
  "items": [{"sku": "A1", "qty": 2}]
}
// Consumer has everything it needs — no callback
```

Trade-off: fat events reduce coupling (no sync call) but increase message size and schema coupling.

#### Event Sourcing

Already covered in Module 2.1. The event log is the source of truth, not a notification mechanism.

### 5.3 Message Broker Patterns

#### Point-to-Point (Queue)

One message → one consumer. Used for task distribution.

```
Producer ──▶ [Queue] ──▶ Consumer 1
                     ──▶ Consumer 2  (competing consumers)
                     ──▶ Consumer 3
```

Each message is processed by exactly one consumer. Load balancing is built in.

#### Publish-Subscribe (Topic)

One message → all subscribers. Used for event notification.

```
Producer ──▶ [Topic] ──▶ Subscriber A (all messages)
                     ──▶ Subscriber B (all messages)
                     ──▶ Subscriber C (all messages)
```

#### Consumer Groups (Kafka)

Hybrid: each consumer group gets all messages, but within a group, each partition is assigned to one consumer.

```
Producer ──▶ [Topic: 4 partitions]
                │
                ├──▶ Group A: Consumer A1 (p0,p1), Consumer A2 (p2,p3)
                │    (each message processed once by group A)
                │
                └──▶ Group B: Consumer B1 (p0,p1,p2,p3)
                     (each message processed once by group B)
```

### 5.4 Ordering Guarantees

| Guarantee | How | Cost |
|---|---|---|
| **No ordering** | Messages processed in any order | Highest throughput |
| **Partition ordering** | Messages with same key go to same partition → ordered within partition | Good throughput, ordered per entity |
| **Total ordering** | Single partition (or single consumer) | Lowest throughput, strongest guarantee |

**Best practice:** Use `entity_id` as the partition key. All events for `order-123` go to the same partition and are processed in order.

### 5.5 Delivery Guarantees

| Guarantee | Meaning | Implication |
|---|---|---|
| **At-most-once** | Message may be lost, never duplicated | Lowest latency, acceptable for metrics |
| **At-least-once** | Message delivered one or more times | Most common; requires idempotent consumers |
| **Exactly-once** | Message delivered exactly once | Hardest to achieve; Kafka achieves via idempotent producers + transactional consumers |

**Rule:** Design for at-least-once delivery with idempotent consumers. Exactly-once is expensive and often unnecessary.

---

## 6. Eventual Consistency

### 6.1 Definition

A system is eventually consistent if, given no new updates, all replicas will converge to the same state. There is no bound on *when* convergence occurs (without anti-entropy mechanisms).

### 6.2 Anti-Entropy Mechanisms

| Mechanism | How It Works |
|---|---|
| **Read repair** | On read, compare replicas. If diverged, update the stale one. |
| **Hinted handoff** | If target replica is down, store the write as a "hint" on another node. When the target comes back, forward the hint. |
| **Merkle tree comparison** | Hash data ranges into a tree. Compare trees between replicas. Sync only divergent ranges. Used by Cassandra, DynamoDB. |
| **Gossip protocol** | Nodes periodically exchange state with random peers. Convergence is probabilistic but fast. |

### 6.3 Conflict Resolution Strategies

When concurrent updates reach different replicas:

| Strategy | Description | Drawback |
|---|---|---|
| **Last-Writer-Wins (LWW)** | Highest timestamp wins. Simple. | Loses data. Clock skew causes incorrect ordering. |
| **Vector Clocks** | Track causality. Detect conflicts, present both versions to application for resolution. | Complex, vector grows with number of writers. |
| **CRDTs** | Conflict-free Replicated Data Types. Mathematical structures that always converge. | Limited data types (counters, sets, registers). |
| **Application-level merge** | Application defines merge semantics. | Most flexible but most work. |

### 6.4 CRDTs — Deep Dive

Conflict-free Replicated Data Types guarantee convergence without coordination.

**G-Counter (Grow-only Counter):**

```python
class GCounter:
    """Each node maintains its own count. Total = sum of all nodes."""
    def __init__(self, node_id: str, nodes: list):
        self._node_id = node_id
        self._counts = {n: 0 for n in nodes}

    def increment(self):
        self._counts[self._node_id] += 1

    def value(self) -> int:
        return sum(self._counts.values())

    def merge(self, other: "GCounter") -> "GCounter":
        merged = GCounter(self._node_id, list(self._counts.keys()))
        for node in self._counts:
            merged._counts[node] = max(
                self._counts.get(node, 0),
                other._counts.get(node, 0),
            )
        return merged
```

**PN-Counter (Positive-Negative Counter):**

Two G-Counters: one for increments, one for decrements. Value = P.value() - N.value().

---

## 7. Distributed Tracing

### 7.1 The Problem

A single user request in a microservices system traverses 5-15 services. When something is slow or fails, which service is the bottleneck?

### 7.2 Concepts

| Term | Definition |
|---|---|
| **Trace** | The full journey of a request through the system. Has a unique `trace_id`. |
| **Span** | A single operation within a trace (e.g., "query database", "call payment API"). |
| **Parent span** | The span that initiated this span. |
| **Context propagation** | Passing `trace_id` and `span_id` between services via HTTP headers or message metadata. |

### 7.3 Trace Anatomy

```
Trace: abc-123
│
├── Span: API Gateway (50ms)
│   │
│   ├── Span: OrderService.submitOrder (40ms)
│   │   │
│   │   ├── Span: DB: SELECT order (5ms)
│   │   │
│   │   ├── Span: PaymentService.charge (25ms)  ← slowest
│   │   │   │
│   │   │   ├── Span: DB: INSERT payment (3ms)
│   │   │   │
│   │   │   └── Span: Stripe API call (20ms)  ← external
│   │   │
│   │   └── Span: Kafka: produce OrderSubmitted (2ms)
│   │
│   └── Span: Response serialization (1ms)
```

### 7.4 Context Propagation

```
Service A                         Service B
┌──────────┐                      ┌──────────┐
│ Generate │  HTTP Request        │ Extract  │
│ trace_id │ ──────────────────▶  │ trace_id │
│ span_id  │  Headers:            │ from     │
│          │  traceparent:        │ headers  │
│          │  00-abc123-def456-01 │          │
└──────────┘                      └──────────┘
```

W3C Trace Context header format:
```
traceparent: {version}-{trace-id}-{parent-span-id}-{trace-flags}
traceparent: 00-abc123def456...-span789...-01
```

### 7.5 Sampling Strategies

Tracing every request at full detail is expensive. Sampling strategies:

| Strategy | Description | Use Case |
|---|---|---|
| **Head-based** | Decide at the start of the trace whether to sample. | Simple, low overhead. |
| **Tail-based** | Decide after the trace completes (based on latency, errors). | More useful traces, higher cost. |
| **Adaptive** | Adjust sampling rate based on traffic volume. | Production systems with variable load. |
| **Priority** | Always trace requests with certain headers/tags. | Debugging specific users or flows. |

### 7.6 Tooling

| Tool | Type | Notes |
|---|---|---|
| Jaeger | Open source | Uber-originated, CNCF graduated |
| Zipkin | Open source | Twitter-originated |
| OpenTelemetry | Standard | Vendor-neutral SDK, replaces OpenTracing + OpenCensus |
| Tempo (Grafana) | Backend | Pairs with Grafana for visualization |
| Datadog APM | Commercial | Full-stack observability |

---

## 8. Idempotency

### 8.1 Why Idempotency Matters

Networks are unreliable. Clients retry. Without idempotency, a retry can cause double-charging, duplicate records, or inconsistent state.

```
Client ──POST /payments──▶ Server (charges card)
Client ◀──── (network drops response) ────
Client ──POST /payments──▶ Server (charges card AGAIN)

Result: Customer charged twice.
```

### 8.2 The Idempotency-Key Pattern (Stripe-style)

```
1. Client generates UUID: "idem-abc-123"
2. Client sends: POST /payments
                 Idempotency-Key: idem-abc-123
                 Body: { amount: 50.00, ... }

3. Server:
   a. Lookup key "idem-abc-123" in idempotency store
   b. NOT FOUND:
      - SETNX "idem-abc-123" → "IN_PROGRESS" (lock)
      - Execute payment logic
      - Store response under "idem-abc-123"
      - Return 200 + response
   c. FOUND + status=COMPLETED:
      - Return stored response (200 OK)
      - Do NOT re-execute
   d. FOUND + status=IN_PROGRESS:
      - Return 409 Conflict or wait
```

### 8.3 Implementation

```python
import json
import redis
from uuid import UUID


class IdempotencyStore:
    def __init__(self, redis_client: redis.Redis, ttl: int = 86400):
        self._redis = redis_client
        self._ttl = ttl  # 24 hours

    def try_acquire(self, key: str) -> bool:
        """Attempt to acquire the idempotency lock. Returns True if acquired."""
        return self._redis.set(
            f"idem:{key}",
            json.dumps({"status": "IN_PROGRESS"}),
            nx=True,    # only set if not exists
            ex=self._ttl,
        )

    def complete(self, key: str, response: dict) -> None:
        """Mark the operation as completed with the response."""
        self._redis.set(
            f"idem:{key}",
            json.dumps({"status": "COMPLETED", "response": response}),
            ex=self._ttl,
        )

    def get(self, key: str) -> dict | None:
        """Retrieve the stored state for an idempotency key."""
        data = self._redis.get(f"idem:{key}")
        if data:
            return json.loads(data)
        return None


class PaymentHandler:
    def __init__(self, idem_store: IdempotencyStore, payment_gateway):
        self._idem = idem_store
        self._gateway = payment_gateway

    def handle(self, idempotency_key: str, amount: float) -> dict:
        # Check for existing result
        existing = self._idem.get(idempotency_key)
        if existing:
            if existing["status"] == "COMPLETED":
                return existing["response"]  # return cached response
            elif existing["status"] == "IN_PROGRESS":
                raise ConflictError("Request is already being processed")

        # Acquire lock
        if not self._idem.try_acquire(idempotency_key):
            raise ConflictError("Concurrent request with same key")

        # Execute
        try:
            result = self._gateway.charge(amount)
            response = {"payment_id": result.id, "status": "charged"}
            self._idem.complete(idempotency_key, response)
            return response
        except Exception:
            # Remove the IN_PROGRESS key so the client can retry
            self._idem._redis.delete(f"idem:{idempotency_key}")
            raise
```

### 8.4 Naturally Idempotent Operations

Some operations are inherently idempotent:

| Method | Idempotent? | Why |
|---|---|---|
| GET | Yes | Read-only, no state change |
| PUT | Yes | Replaces entire resource; repeating produces same result |
| DELETE | Yes | Deleting an already-deleted resource is a no-op (return 204 or 404) |
| POST | **No** | Creates a new resource each time → needs idempotency key |
| PATCH | **Depends** | `SET balance = 100` is idempotent; `SET balance = balance - 10` is not |

---

## 9. Distributed Locking

### 9.1 When You Need It

When multiple instances of the same service must coordinate access to a shared resource (e.g., only one instance should process a scheduled job).

### 9.2 Redis-Based Lock (Redlock Considerations)

```python
class RedisLock:
    def __init__(self, redis_client, lock_name: str, ttl: int = 30):
        self._redis = redis_client
        self._lock_name = f"lock:{lock_name}"
        self._ttl = ttl
        self._lock_value = str(uuid4())

    def acquire(self) -> bool:
        return self._redis.set(
            self._lock_name,
            self._lock_value,
            nx=True,
            ex=self._ttl,
        )

    def release(self) -> None:
        # Lua script for atomic check-and-delete
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        self._redis.eval(script, 1, self._lock_name, self._lock_value)
```

**Critical:** Use Lua script for release to avoid deleting another process's lock. The TTL prevents deadlocks if the holder crashes.

### 9.3 Fencing Tokens

A lock alone is not safe. If process A holds a lock, gets paused by GC, the lock expires, process B acquires the lock and starts writing, then process A resumes and also writes — data corruption.

**Solution:** Fencing tokens. Each lock acquisition returns a monotonically increasing token. The storage system rejects writes with a stale token.

```
Process A acquires lock → token 33
Process A pauses (GC)
Lock expires
Process B acquires lock → token 34
Process B writes to storage with token 34 → accepted
Process A resumes, writes with token 33 → REJECTED (token < 34)
```

---

## 10. Leader Election

### 10.1 Problem

In a cluster of N instances, exactly one must be the "leader" (e.g., to run scheduled jobs, manage partitions).

### 10.2 Approach: Coordination Service

Use a consensus-based system (ZooKeeper, etcd, Consul) for leader election.

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Node A  │  │ Node B  │  │ Node C  │
│ (Leader)│  │(Follower│  │(Follower│
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │
           ┌──────▼──────┐
           │    etcd      │
           │ (lease-based │
           │  election)   │
           └─────────────┘
```

```python
# etcd-based leader election (simplified)
import etcd3

client = etcd3.client()
lease = client.lease(ttl=10)  # 10-second lease

# Try to become leader by creating a key with the lease
success, _ = client.transaction(
    compare=[client.transactions.create("leader/order-processor") == 0],
    success=[client.transactions.put(
        "leader/order-processor",
        "node-A",
        lease=lease,
    )],
    failure=[],
)

if success:
    print("I am the leader")
    # Must keep renewing the lease
    while True:
        lease.refresh()
        do_leader_work()
        time.sleep(5)
else:
    print("Another node is leader, waiting...")
    # Watch for key deletion (leader crash)
    events_iterator, cancel = client.watch("leader/order-processor")
    for event in events_iterator:
        if isinstance(event, etcd3.events.DeleteEvent):
            print("Leader is gone, trying to become leader...")
            break
```

---

## 11. Putting It Together — A Resilient Order Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│  Rate limiter: 1000 req/s per IP                                 │
│  Auth: JWT validation                                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  Order Service                                                   │
│  ┌─────────────────┐                                             │
│  │ Circuit Breaker │                                             │
│  │ (payment calls) │                                             │
│  └────────┬────────┘                                             │
│           │                                                      │
│  ┌────────▼────────┐    ┌──────────────┐                         │
│  │  Saga           │───▶│  Outbox      │──▶ [CDC/Poller] ──▶ Kafka│
│  │  Orchestrator   │    │  Table       │                         │
│  └─────────────────┘    └──────────────┘                         │
│           │                                                      │
│  Bulkhead: 20 threads for payment, 20 for inventory              │
│  Retry: 3x exponential backoff + jitter                          │
│  Timeout: 5s connect, 10s read                                   │
│  Idempotency: Redis key per order submission                     │
└──────────────────────────────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │  Payment    │ │  Inventory  │ │  Shipping   │
  │  Service    │ │  Service    │ │  Service    │
  └─────────────┘ └─────────────┘ └─────────────┘
```

**Resilience stack per service call:**

```
1. Rate Limiter (API Gateway) — reject excess traffic
2. Timeout (connect + read) — bound wait time
3. Circuit Breaker — fail fast if downstream is sick
4. Bulkhead — isolate thread pools per downstream
5. Retry (exponential + jitter) — handle transient failures
6. Fallback — degrade gracefully when all else fails
7. Idempotency Key — safe retries at the application level
```

---

## 12. Common Pitfalls & Troubleshooting

### Pitfall 1: Saga Without Idempotent Compensations

**Symptom:** Refund applied twice. Customer gets double their money back.
**Fix:** Every compensation must check if it has already been applied. Use the saga ID + step number as the idempotency key.

### Pitfall 2: Outbox Table Grows Unbounded

**Symptom:** Outbox table has millions of rows. Queries slow down.
**Fix:** Delete published events immediately (polling) or use CDC (Debezium reads WAL and does not query the table). Add a TTL-based cleanup job as a safety net.

### Pitfall 3: Circuit Breaker Opens Too Aggressively

**Symptom:** One slow request triggers OPEN state. All subsequent requests fail.
**Fix:** Use a sliding window (not a simple counter). Require a minimum number of requests in the window before calculating error rate. Resilience4j default: minimum 10 calls in the window.

### Pitfall 4: Retry Without Backoff

**Symptom:** Service recovers but is immediately overwhelmed by a retry storm.
**Fix:** Always use exponential backoff with jitter. Never use fixed-delay retries in production.

### Pitfall 5: Distributed Tracing Gaps

**Symptom:** Trace shows 3 spans but the request traversed 5 services.
**Fix:** Ensure context propagation is configured in every service. For async (Kafka), propagate trace context in message headers, not just HTTP headers.

### Pitfall 6: Event Ordering Violated

**Symptom:** Consumer sees `OrderCancelled` before `OrderCreated`.
**Fix:** Use `order_id` as the Kafka partition key. All events for the same order go to the same partition and are consumed in order.

### Pitfall 7: Consumer Lag

**Symptom:** Events are produced faster than consumed. Consumer falls hours behind.
**Fix:** Scale consumers (add instances to the consumer group). Increase partition count. Optimize consumer processing time. Monitor lag with Kafka Lag Exporter or Burrow.

---

## 13. Q&A — Frequently Asked Questions

**Q1: When should I use choreography vs orchestration for sagas?**
A: Choreography for simple flows (< 4 steps) where services are truly independent. Orchestration for complex flows (> 4 steps), especially when you need clear visibility and centralized error handling.

**Q2: Is the outbox pattern mandatory for event-driven systems?**
A: If you need guaranteed delivery (i.e., every DB write produces a corresponding event), yes. If you can tolerate occasional lost events (metrics, non-critical notifications), you can publish directly.

**Q3: Can I use a circuit breaker for database calls?**
A: Yes, especially for remote databases or when the DB is behind a network. Less useful for local/embedded databases.

**Q4: How do I test sagas?**
A: Unit test the saga orchestrator as a state machine: given current state and an event, assert the next state and the command issued. Integration test with in-memory message broker (e.g., Testcontainers + Kafka).

**Q5: What is the difference between eventual consistency and inconsistency?**
A: Eventual consistency guarantees convergence — given time, all replicas agree. Inconsistency has no such guarantee.

**Q6: How long is "eventual" in eventual consistency?**
A: Depends on the anti-entropy mechanism. Cassandra read repair: next read. Gossip: seconds. No anti-entropy: unbounded.

**Q7: Should every microservice have its own message broker?**
A: No. Share the broker (Kafka cluster), but give each service its own topics and consumer groups. The broker is shared infrastructure, like a network.

**Q8: How do I handle poison messages (messages that always fail)?**
A: After N retries, move the message to a Dead Letter Queue (DLQ). Alert the operations team. Fix the bug, then replay from the DLQ.

**Q9: Can circuit breakers cause starvation?**
A: Yes. If the circuit stays OPEN too long, legitimate traffic is rejected. Solution: tune the sleep window aggressively and monitor circuit state. Some implementations support "forced closed" for maintenance.

**Q10: What is the difference between a service mesh and an API gateway?**
A: An API gateway handles north-south traffic (external clients → internal services). A service mesh handles east-west traffic (service-to-service within the cluster). They are complementary, not competing.

---

## 14. Hands-On Exercises

### Exercise 1: Build a Saga Orchestrator (Intermediate)

Build a saga for an order flow: Order → Payment → Inventory.

**Requirements:**
- Implement a state machine with states: STARTED, PAYMENT_PENDING, PAYMENT_DONE, STOCK_PENDING, STOCK_RESERVED, COMPLETED, COMPENSATING, FAILED.
- Implement compensation for each forward step.
- Persist saga state to a database.
- Test: inject a failure at the stock step and verify that payment is refunded.

**Acceptance criteria:**
- Saga state is durable — if the orchestrator crashes and restarts, it resumes from the last saved state.
- Compensations are idempotent.
- All state transitions are logged for debugging.

### Exercise 2: Implement Circuit Breaker with Metrics (Beginner)

Build a circuit breaker from scratch (no libraries).

**Requirements:**
- Implement the three states: CLOSED, OPEN, HALF_OPEN.
- Use a sliding window (not a simple counter) for error rate calculation.
- Expose metrics: current state, failure count, success count, rejected count.
- Write tests for each state transition.

**Acceptance criteria:**
- Under 100% error rate, circuit opens within N failures.
- After sleep window, circuit transitions to HALF_OPEN.
- M consecutive successes in HALF_OPEN close the circuit.

### Exercise 3: Outbox Pattern with Polling (Intermediate)

Build the transactional outbox pattern.

**Requirements:**
- Write a service that saves an entity and an outbox event in the same database transaction.
- Write a background poller that reads unpublished events and "publishes" them (print to console or send to an in-memory queue).
- Mark events as published after successful delivery.
- Handle concurrent pollers (two instances running the poller must not double-publish).

**Acceptance criteria:**
- No event is lost (every DB write produces a published event).
- No event is published twice (use `SELECT ... FOR UPDATE SKIP LOCKED`).

### Exercise 4: Distributed Tracing Lab (Intermediate)

Set up distributed tracing across three services.

**Requirements:**
- Three services: API Gateway, OrderService, PaymentService.
- Use OpenTelemetry SDK to instrument each service.
- Propagate trace context via HTTP headers.
- Visualize traces in Jaeger (use Docker).
- Add custom spans for database queries and external API calls.

**Acceptance criteria:**
- A single trace shows spans across all three services.
- Each span has meaningful attributes (service name, operation, status).
- Latency breakdown is visible per span.

### Exercise 5: Idempotency-Key Middleware (Beginner)

Build a reusable middleware that enforces idempotency for POST requests.

**Requirements:**
- Middleware reads the `Idempotency-Key` header.
- If the key has been seen before and the operation completed, return the cached response.
- If the key is in progress, return 409 Conflict.
- If the key is new, acquire a lock, let the handler execute, cache the response.
- Use Redis for storage with a 24-hour TTL.

**Acceptance criteria:**
- Sending the same request twice with the same key returns the same response.
- The underlying handler executes exactly once per key.

### Exercise 6: Event-Driven Notification System (Advanced)

Build a notification system using event-driven architecture.

**Requirements:**
- OrderService publishes `OrderPlaced`, `OrderShipped`, `OrderDelivered` events to Kafka.
- NotificationService consumes events and sends notifications (email, SMS, push).
- EmailNotifier, SmsNotifier, PushNotifier are separate consumers in the same consumer group.
- Handle consumer lag: if a consumer falls behind, implement backpressure (pause partition assignment).

**Acceptance criteria:**
- Each event is processed exactly once per notification channel.
- Consumer lag is visible via metrics.
- Poison messages go to DLQ after 3 retries.

### Exercise 7: Chaos Engineering Experiment (Advanced)

Design and execute a chaos experiment for the saga from Exercise 1.

**Requirements:**
- Inject a 5-second latency into PaymentService responses.
- Inject a 50% error rate into StockService.
- Kill the saga orchestrator mid-saga (between payment and stock steps).
- After restart, verify the saga resumes from its last persisted state.

**Acceptance criteria:**
- Circuit breaker opens for StockService after threshold is reached.
- Saga compensations trigger correctly for failed flows.
- No orphaned sagas: all reach a terminal state (COMPLETED or FAILED).
- Metrics show: circuit state transitions, retry counts, saga durations.

---

## 15. Backpressure

### 15.1 The Problem

When a producer generates data faster than a consumer can process it, the system must decide what to do with the excess.

Without backpressure:
- Queues grow unbounded → OOM.
- Latency increases → cascading timeouts.
- Message broker disk fills → cluster instability.

### 15.2 Backpressure Strategies

| Strategy | Description | Trade-off |
|---|---|---|
| **Drop** | Discard excess messages | Data loss, but system stays stable. Good for metrics/telemetry. |
| **Buffer** | Queue messages and process later | Latency increases. Requires bounded buffer to avoid OOM. |
| **Throttle producer** | Tell the producer to slow down | Producer must support flow control (e.g., TCP window, HTTP 429). |
| **Scale consumer** | Add more consumer instances | Takes time to scale; may not help if the bottleneck is external. |
| **Sample** | Process every Nth message | Acceptable for aggregates/analytics, not for transactional workloads. |

### 15.3 Implementation Example — Bounded Queue with Rejection

```python
import asyncio
from collections import deque


class BoundedQueue:
    def __init__(self, max_size: int = 1000):
        self._queue = deque(maxlen=max_size)
        self._overflow_count = 0

    def enqueue(self, item) -> bool:
        if len(self._queue) >= self._queue.maxlen:
            self._overflow_count += 1
            return False  # signal backpressure to producer
        self._queue.append(item)
        return True

    def dequeue(self):
        if self._queue:
            return self._queue.popleft()
        return None

    @property
    def overflow_count(self) -> int:
        return self._overflow_count
```

### 15.4 Reactive Streams (Java)

The Reactive Streams specification (java.util.concurrent.Flow in JDK 9+) formalizes backpressure:

```
Publisher ──subscribe──▶ Subscriber
Subscriber ──request(N)──▶ Publisher
Publisher ──onNext(item) x N──▶ Subscriber
```

The subscriber tells the publisher how many items it can handle. The publisher must not exceed that count. This is **pull-based** backpressure.

---

## 16. Dead Letter Queues (DLQ)

### 16.1 When Messages Cannot Be Processed

A message may fail processing due to:
- **Transient failure:** downstream is temporarily unavailable → retry with backoff.
- **Permanent failure (poison message):** malformed data, schema mismatch, business rule violation → retries will never succeed.

After N retries, move the message to a DLQ for manual inspection.

### 16.2 DLQ Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Producer │────▶│ Main     │────▶│ Consumer │
│          │     │ Queue    │     │          │
└──────────┘     └──────────┘     └─────┬────┘
                                        │
                                  Retry N times
                                        │
                                  ┌─────▼────┐
                                  │   DLQ    │
                                  │          │
                                  └─────┬────┘
                                        │
                                  Manual review
                                  Fix bug, replay
```

### 16.3 DLQ Best Practices

1. **Preserve original message metadata:** timestamp, source topic, partition, offset, retry count, error message.
2. **Alert on DLQ growth:** if DLQ receives messages, something is wrong.
3. **Replay tooling:** build a tool to replay DLQ messages back to the main queue after the bug is fixed.
4. **TTL on DLQ:** do not keep messages forever. Set a retention policy (e.g., 7 days).
5. **Separate DLQ per topic:** do not mix unrelated failures.

---

## 17. Observability Triad

Distributed systems require three pillars of observability:

### 17.1 Metrics

Aggregated numerical measurements over time. Use for alerting and dashboards.

**RED Method (for request-driven services):**
- **R**ate: requests per second
- **E**rrors: failed requests per second
- **D**uration: latency distribution (p50, p95, p99)

**USE Method (for infrastructure):**
- **U**tilization: percentage of resource in use
- **S**aturation: degree of queueing (work waiting)
- **E**rrors: error events

### 17.2 Logs

Structured, context-rich records of discrete events.

```json
{
  "timestamp": "2026-05-22T14:30:00.123Z",
  "level": "ERROR",
  "service": "order-service",
  "trace_id": "abc-123",
  "span_id": "def-456",
  "message": "Failed to reserve stock",
  "order_id": "ord-789",
  "error": "StockInsufficientError",
  "retry_count": 3
}
```

**Best practices:**
- Always include `trace_id` and `span_id` for correlation with traces.
- Use structured JSON, not free-text.
- Log at appropriate levels: ERROR for failures, WARN for degradation, INFO for business events, DEBUG for troubleshooting.
- Never log PII, credentials, or tokens.

### 17.3 Traces

Distributed request flow visualization (covered in Section 7).

### 17.4 Correlation

The power is in connecting all three:

```
Alert: p99 latency > 2s on OrderService
  → Metric dashboard: spike at 14:30
    → Trace search: find slow traces at 14:30
      → Span: PaymentService.charge took 1.8s
        → Logs with trace_id: "Stripe API timeout after 1.5s"
          → Root cause: Stripe had an outage
```

---

## 18. Pattern Decision Matrix

| Problem | Pattern | Alternatives |
|---|---|---|
| Cross-service transaction | Saga (orchestration) | 2PC (only if same DB vendor), Event choreography |
| Atomic DB write + event publish | Outbox + CDC | Listen-to-yourself, dual-write with reconciliation |
| Cascading failure | Circuit breaker | Timeout, load shedding |
| Resource isolation | Bulkhead | Rate limiter, queue isolation |
| Transient failure | Retry + backoff + jitter | Timeout + fallback |
| Service-to-service networking | Service mesh | Library-based (Resilience4j, Polly) |
| Request tracking | Distributed tracing | Centralized logging with correlation IDs |
| Duplicate operations | Idempotency key | Natural idempotency (PUT/DELETE) |
| Shared resource coordination | Distributed lock | Leader election, optimistic locking |
| Consumer overwhelm | Backpressure | DLQ, sampling, scaling |

---

## 19. Glossary

| Term | Definition |
|---|---|
| **Anti-entropy** | Mechanisms that actively push replicas toward consistency (read repair, Merkle trees, gossip). |
| **Backpressure** | A mechanism for a consumer to signal a producer to slow down when overwhelmed. |
| **Bulkhead** | Resource isolation pattern that prevents failure in one component from consuming resources needed by others. |
| **CDC** | Change Data Capture — streaming database changes (WAL/binlog) to external consumers. |
| **Circuit breaker** | A state machine that prevents calls to a failing service, allowing it time to recover. |
| **Compensation** | The undo operation in a saga. Reverses the effect of a previous step. Must be idempotent. |
| **Consumer group** | A set of consumers that coordinate to process a topic's partitions. Each message is consumed by one member. |
| **CRDT** | Conflict-free Replicated Data Type — a data structure that guarantees convergence without coordination. |
| **Dead Letter Queue** | A queue for messages that cannot be processed after multiple retries. Used for manual inspection. |
| **Dual write** | Writing to two systems non-atomically. Leads to inconsistency. |
| **Fencing token** | A monotonically increasing token used to prevent stale writes from processes that held an expired lock. |
| **Idempotency** | The property that performing an operation multiple times produces the same result as performing it once. |
| **Outbox** | A database table used to store events atomically alongside business data. A relay publishes them to a broker. |
| **Saga** | A sequence of local transactions with compensating actions for handling distributed transactions. |
| **Service mesh** | Infrastructure layer that handles service-to-service communication (mTLS, retries, tracing). |
| **Sidecar** | A proxy process deployed alongside a service to handle cross-cutting concerns. |
| **Trace** | The full journey of a request through a distributed system, composed of spans. |

---

## 20. Resiliency Pattern Composition — Code Walkthrough

Combining circuit breaker, retry, bulkhead, timeout, and fallback into a single call stack. Order matters.

### 20.1 Composition Order (outer to inner)

```
Bulkhead → Circuit Breaker → Retry → Timeout → Actual Call

Why this order:
1. Bulkhead (outermost): limits total concurrent calls.
   If pool is exhausted, reject immediately (do not even enter CB).
2. Circuit Breaker: if open, fail fast (do not retry or wait).
3. Retry: retry only if the inner call fails and CB is still closed.
4. Timeout: each individual attempt is bounded.
5. Actual call: the real network request.
```

### 20.2 Java Example with Resilience4j

```java
// Configuration
CircuitBreakerConfig cbConfig = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)
    .slidingWindowSize(10)
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .permittedNumberOfCallsInHalfOpenState(3)
    .build();

RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(500))
    .retryExceptions(IOException.class, TimeoutException.class)
    .build();

BulkheadConfig bulkheadConfig = BulkheadConfig.custom()
    .maxConcurrentCalls(20)
    .maxWaitDuration(Duration.ofMillis(100))
    .build();

TimeLimiterConfig timeConfig = TimeLimiterConfig.custom()
    .timeoutDuration(Duration.ofSeconds(5))
    .build();

// Compose
CircuitBreaker cb = CircuitBreaker.of("payment", cbConfig);
Retry retry = Retry.of("payment", retryConfig);
Bulkhead bulkhead = Bulkhead.of("payment", bulkheadConfig);
TimeLimiter timeLimiter = TimeLimiter.of("payment", timeConfig);

Supplier<PaymentResult> call = () -> paymentClient.charge(orderId, amount);

// Decoration order: bulkhead → cb → retry → timeLimiter → call
Supplier<CompletionStage<PaymentResult>> decorated =
    Bulkhead.decorateCompletionStage(bulkhead,
        CircuitBreaker.decorateCompletionStage(cb,
            Retry.decorateCompletionStage(retry,
                () -> timeLimiter.executeCompletionStage(
                    () -> CompletableFuture.supplyAsync(call)
                )
            )
        )
    );
```

### 20.3 Python Example

```python
class ResilientCaller:
    """Composes multiple resilience patterns."""

    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        max_retries: int = 3,
        timeout_seconds: float = 5.0,
        max_concurrent: int = 20,
        fallback=None,
    ):
        self._cb = circuit_breaker
        self._max_retries = max_retries
        self._timeout = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._fallback = fallback

    async def call(self, func, *args, **kwargs):
        # Layer 1: Bulkhead
        if self._semaphore.locked():
            if self._fallback:
                return await self._fallback(*args, **kwargs)
            raise BulkheadFullError("Max concurrent calls reached")

        async with self._semaphore:
            # Layer 2: Circuit Breaker
            try:
                return await self._cb.call(
                    self._retry_with_timeout, func, *args, **kwargs
                )
            except CircuitOpenError:
                if self._fallback:
                    return await self._fallback(*args, **kwargs)
                raise

    async def _retry_with_timeout(self, func, *args, **kwargs):
        last_error = None
        for attempt in range(self._max_retries):
            try:
                # Layer 3: Timeout per attempt
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self._timeout,
                )
            except (asyncio.TimeoutError, TransientError) as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
        raise last_error
```

### 20.4 Monitoring the Composition

Every layer should emit metrics:

| Pattern | Key Metrics |
|---|---|
| Bulkhead | current_active, rejected_count, queue_depth |
| Circuit Breaker | state (closed/open/half-open), failure_count, success_count |
| Retry | retry_count, retries_exhausted_count |
| Timeout | timeout_count |
| Fallback | fallback_invocations |

```
Dashboard layout:
┌─────────────────────────────────────────────────────────────┐
│  Payment Service Resilience                                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ CB State     │  │ Bulkhead     │  │ Retry Rate   │       │
│  │  ● CLOSED    │  │  12/20 used  │  │  2.3/min     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐        │
│  │  Error Rate & Latency (last 1h)                  │        │
│  │  ────────────────────────────────────             │        │
│  │  p50: 45ms   p95: 120ms   p99: 450ms            │        │
│  │  Error rate: 0.3%   Timeout rate: 0.1%           │        │
│  └──────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 21. Testing Distributed Patterns

### 21.1 Testing Sagas

```python
def test_saga_compensates_on_stock_failure():
    """Given payment succeeds, when stock fails, then payment is refunded."""
    # Arrange
    payment_mock = Mock()
    payment_mock.charge.return_value = PaymentResult(id="pay-1")
    stock_mock = Mock()
    stock_mock.reserve.side_effect = StockInsufficientError()
    order_repo = InMemoryOrderRepo()
    order_repo.save(Order(id="ord-1", status="PENDING"))

    saga = OrderSagaOrchestrator(payment_mock, stock_mock, order_repo)

    # Act
    saga.execute(UUID("ord-1"))

    # Assert
    payment_mock.refund.assert_called_once_with(UUID("ord-1"))
    assert order_repo.find_by_id(UUID("ord-1")).status == "CANCELLED"
```

### 21.2 Testing Circuit Breakers

```python
def test_circuit_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

    def failing_call():
        raise ConnectionError("service down")

    # 3 failures
    for _ in range(3):
        with pytest.raises(ConnectionError):
            cb.call(failing_call)

    # 4th call should be rejected by circuit
    with pytest.raises(CircuitOpenError):
        cb.call(failing_call)

    assert cb._state == CircuitState.OPEN
```

### 21.3 Testing with Testcontainers

For integration tests involving Kafka, Redis, or databases:

```python
import testcontainers.kafka
import testcontainers.redis


@pytest.fixture(scope="module")
def kafka():
    with testcontainers.kafka.KafkaContainer() as container:
        yield container.get_bootstrap_server()


@pytest.fixture(scope="module")
def redis():
    with testcontainers.redis.RedisContainer() as container:
        yield container.get_connection_url()


def test_outbox_publishes_to_kafka(kafka, redis):
    # Full integration: DB write → outbox → poller → Kafka
    ...
```

### 21.4 Chaos Testing in CI

Use libraries like `toxiproxy` or `chaos-mesh` to inject failures:

| Fault | Tool | What It Tests |
|---|---|---|
| Network latency | Toxiproxy, tc | Timeout handling, circuit breaker |
| Packet loss | Toxiproxy, iptables | Retry logic, idempotency |
| Service crash | Kill process, Kubernetes pod deletion | Saga compensation, leader re-election |
| Disk full | fallocate | Graceful degradation, error messages |
| Clock skew | libfaketime | Timestamp-based logic, TTL, leases |

---

## 22. References

1. Garcia-Molina, H., Salem, K. "Sagas" (1987). ACM SIGMOD.
2. Richardson, C. *Microservices Patterns* (Manning, 2018). Chapters 4 (Sagas) and 13 (Observability).
3. Nygard, M.T. *Release It!* (Pragmatic Bookshelf, 2nd edition, 2018). — Circuit breaker, bulkhead, timeout.
4. Kleppmann, M. *Designing Data-Intensive Applications* (O'Reilly, 2017). Chapters 8-9 (distributed systems).
5. Shapiro, M. et al. "Conflict-free Replicated Data Types" (2011). INRIA Research Report.
6. Burns, B. *Designing Distributed Systems* (O'Reilly, 2018). — Sidecar, ambassador, adapter patterns.
7. W3C Trace Context Specification. https://www.w3.org/TR/trace-context/
8. OpenTelemetry Documentation. https://opentelemetry.io/docs/
9. Stripe. "Idempotent Requests." https://stripe.com/docs/api/idempotent_requests
10. Debezium Documentation. https://debezium.io/documentation/
11. Martin, J. "The Outbox Pattern" (2019). Microservices.io.
12. Li, W. et al. "Redlock: Distributed Lock in Redis." Redis documentation.
13. Reactive Streams Specification. https://www.reactive-streams.org/
14. Rosenthal, C. et al. *Chaos Engineering* (O'Reilly, 2020).

---

*End of Module 2.2*

1. Garcia-Molina, H., Salem, K. "Sagas" (1987). ACM SIGMOD.
2. Richardson, C. *Microservices Patterns* (Manning, 2018). Chapters 4 (Sagas) and 13 (Observability).
3. Nygard, M.T. *Release It!* (Pragmatic Bookshelf, 2nd edition, 2018). — Circuit breaker, bulkhead, timeout.
4. Kleppmann, M. *Designing Data-Intensive Applications* (O'Reilly, 2017). Chapters 8-9 (distributed systems).
5. Shapiro, M. et al. "Conflict-free Replicated Data Types" (2011). INRIA Research Report.
6. Burns, B. *Designing Distributed Systems* (O'Reilly, 2018). — Sidecar, ambassador, adapter patterns.
7. W3C Trace Context Specification. https://www.w3.org/TR/trace-context/
8. OpenTelemetry Documentation. https://opentelemetry.io/docs/
9. Stripe. "Idempotent Requests." https://stripe.com/docs/api/idempotent_requests
10. Debezium Documentation. https://debezium.io/documentation/
11. Martin, J. "The Outbox Pattern" (2019). Microservices.io.
12. Li, W. et al. "Redlock: Distributed Lock in Redis." Redis documentation.
13. Reactive Streams Specification. https://www.reactive-streams.org/

---

*End of Module 2.2*

1. Garcia-Molina, H., Salem, K. "Sagas" (1987). ACM SIGMOD.
2. Richardson, C. *Microservices Patterns* (Manning, 2018). Chapters 4 (Sagas) and 13 (Observability).
3. Nygard, M.T. *Release It!* (Pragmatic Bookshelf, 2nd edition, 2018). — Circuit breaker, bulkhead, timeout.
4. Kleppmann, M. *Designing Data-Intensive Applications* (O'Reilly, 2017). Chapters 8-9 (distributed systems).
5. Shapiro, M. et al. "Conflict-free Replicated Data Types" (2011). INRIA Research Report.
6. Burns, B. *Designing Distributed Systems* (O'Reilly, 2018). — Sidecar, ambassador, adapter patterns.
7. W3C Trace Context Specification. https://www.w3.org/TR/trace-context/
8. OpenTelemetry Documentation. https://opentelemetry.io/docs/
9. Stripe. "Idempotent Requests." https://stripe.com/docs/api/idempotent_requests
10. Debezium Documentation. https://debezium.io/documentation/
11. Martin, J. "The Outbox Pattern" (2019). Microservices.io.
12. Li, W. et al. "Redlock: Distributed Lock in Redis." Redis documentation.
13. Reactive Streams Specification. https://www.reactive-streams.org/
14. Rosenthal, C. et al. *Chaos Engineering* (O'Reilly, 2020).
15. Fowler, M. "Circuit Breaker" (2014). https://martinfowler.com/bliki/CircuitBreaker.html
16. Newman, S. *Building Microservices* (O'Reilly, 2nd edition, 2021).
17. Stopford, B. *Designing Event-Driven Systems* (O'Reilly, 2018).

---

## Exercises

### Exercise 1: Design a Consensus Protocol (Advanced)

Design a simplified consensus protocol for a 5-node cluster that must agree on a single integer value.

**Requirements:**
- Define message types (Propose, Promise, Accept, Accepted, Reject).
- Handle leader election when the current leader fails.
- Demonstrate fault tolerance: the system must reach consensus even when 2 of 5 nodes are unreachable.
- Write pseudocode for each phase (prepare, accept, learn).
- Explain what happens during a network partition where 3 nodes are on one side and 2 on the other.

**Deliverable:** Protocol specification document + sequence diagrams for the happy path and one failure scenario.

### Exercise 2: Saga Orchestrator with Compensation (Intermediate)

Implement an order processing saga with an orchestrator that coordinates three services: Payment, Inventory, and Shipping.

**Requirements:**
- Define the forward transactions and their compensating actions (refund, restock, cancel shipment).
- Implement timeout handling: if Inventory does not respond within 5 seconds, trigger compensation.
- Log the saga state machine transitions (STARTED, PAYMENT_OK, INVENTORY_OK, SHIPPING_OK, COMPLETED, COMPENSATING, FAILED).
- Write integration tests that simulate each service failure scenario.
- Compare your orchestrator implementation with a choreography-based alternative: document the trade-offs.

### Exercise 3: Transactional Outbox with Debezium (Intermediate)

Set up a transactional outbox pipeline using PostgreSQL and Debezium.

**Requirements:**
- Create an `outbox_events` table with columns: `id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload`, `created_at`.
- Write application code that atomically inserts a domain record and an outbox event in a single transaction.
- Configure Debezium to capture changes from the outbox table and publish them to Kafka.
- Implement a consumer that processes the events idempotently (use an idempotency key table).
- Verify exactly-once semantics by replaying the Debezium connector from an earlier offset and confirming no duplicate side effects.

### Exercise 4: Circuit Breaker State Machine (Intermediate)

Implement a circuit breaker that protects calls to an external payment API.

**Requirements:**
- Three states: CLOSED (normal), OPEN (fail-fast), HALF_OPEN (probe).
- Configurable thresholds: failure count to open (default 5), timeout in OPEN state before probing (default 30 s), success count in HALF_OPEN to close (default 3).
- Expose metrics: total calls, successful calls, failed calls, rejected calls, state transitions.
- Write unit tests covering: transitions CLOSED → OPEN, OPEN → HALF_OPEN, HALF_OPEN → CLOSED, HALF_OPEN → OPEN.
- Bonus: add bulkhead isolation so the circuit breaker protects a bounded thread pool.

### Exercise 5: Distributed Tracing with OpenTelemetry (Advanced)

Instrument a 3-service pipeline (API Gateway → Order Service → Notification Service) with OpenTelemetry.

**Requirements:**
- Propagate W3C Trace Context headers across HTTP and Kafka boundaries.
- Create spans for: HTTP request handling, database queries, Kafka produce/consume.
- Add semantic attributes: `service.name`, `http.method`, `db.system`, `messaging.system`.
- Export traces to Jaeger and verify the full trace appears as a single tree.
- Measure the overhead of instrumentation by comparing p99 latency with and without tracing enabled.

---

## Readings and References

### Official Documentation (retrieved: 2026-05-29)

- OpenTelemetry Documentation — https://opentelemetry.io/docs/
- W3C Trace Context Specification — https://www.w3.org/TR/trace-context/
- Debezium Documentation — https://debezium.io/documentation/
- Microservices.io Saga Pattern — https://microservices.io/patterns/data/saga.html
- Microservices.io Event Sourcing — https://microservices.io/patterns/data/event-sourcing.html
- Reactive Streams Specification — https://www.reactive-streams.org/
- Stripe Idempotent Requests — https://stripe.com/docs/api/idempotent_requests

### Books

- Kleppmann, M. *Designing Data-Intensive Applications* (O'Reilly, 2017). Chapters 8-9 (distributed consistency, consensus).
- Richardson, C. *Microservices Patterns* (Manning, 2018). Chapters 4 (Sagas), 13 (Observability).
- Nygard, M.T. *Release It!* 2nd edition (Pragmatic Bookshelf, 2018). Circuit breaker, bulkhead, timeout.
- Newman, S. *Building Microservices* 2nd edition (O'Reilly, 2021). Service decomposition, integration patterns.
- Burns, B. *Designing Distributed Systems* (O'Reilly, 2018). Sidecar, ambassador, adapter patterns.
- Stopford, B. *Designing Event-Driven Systems* (O'Reilly, 2018). Event streaming architectures with Kafka.
- Rosenthal, C. et al. *Chaos Engineering* (O'Reilly, 2020). Failure injection and resilience testing.

### Papers

- Lamport, L. "Time, Clocks, and the Ordering of Events in a Distributed System." *Communications of the ACM*, 21(7), 558-565 (1978). https://dl.acm.org/doi/10.1145/359545.359563
- Garcia-Molina, H., Salem, K. "Sagas." *ACM SIGMOD Record*, 16(3), 249-259 (1987).
- Ongaro, D., Ousterhout, J. "In Search of an Understandable Consensus Algorithm." *USENIX ATC 2014*. https://raft.github.io/raft.pdf
- Shapiro, M. et al. "Conflict-free Replicated Data Types." INRIA Research Report RR-7687 (2011).
- Fowler, M. "Circuit Breaker" (2014). https://martinfowler.com/bliki/CircuitBreaker.html

---

## Cross-References

| Topic | Module | File |
|---|---|---|
| CAP theorem, PACELC trade-offs | 2.4 | `04_System_Design_CAP_PACELC.md` |
| SOLID principles applied to service boundaries | 2.3 | `03_Design_Principles_SOLID_etc.md` |
| Code-level architecture (hexagonal, clean) | 2.1 | `01_Code_Level_Architecture.md` |
| High-performance system design (lock-free, cache) | 2.2b | `02_b_High_Performance_System_Design.md` |
| API design and versioning for inter-service contracts | 2.2c | `02_c_API_Design_Evolution.md` |
| Database replication, sharding, and consistency | — | `03_Database_Engineering/` |

---

## Glossary

| Term | Definition |
|---|---|
| **Saga** | A sequence of local transactions where each step publishes an event or command to trigger the next; failures are handled by executing compensating transactions in reverse order. |
| **Choreography** | A saga coordination style where each service reacts to events independently without a central controller. |
| **Orchestration** | A saga coordination style where a central orchestrator directs each participant step-by-step. |
| **Transactional Outbox** | A pattern that atomically writes a domain change and an event record in the same database transaction, then asynchronously relays the event to a message broker. |
| **Circuit Breaker** | A stability pattern that detects repeated failures and short-circuits calls to a failing dependency, allowing it time to recover. |
| **Bulkhead** | A resilience pattern that isolates resources (threads, connections) so that a failure in one subsystem does not cascade to others. |
| **Idempotency** | The property of an operation that produces the same result regardless of how many times it is executed with the same input. |
| **Event Sourcing** | A persistence strategy that stores state as an append-only log of domain events rather than mutable rows. |
| **CQRS** | Command Query Responsibility Segregation — separating the write model (commands) from the read model (queries) so each can be optimized independently. |
| **Eventual Consistency** | A consistency model where replicas are guaranteed to converge to the same state given sufficient time without new updates. |
| **Distributed Tracing** | Instrumentation that correlates requests across service boundaries into a single trace, enabling end-to-end latency analysis. |
| **Leader Election** | A protocol by which a set of nodes selects one node to act as coordinator for a particular task or partition. |
| **Consensus** | An agreement protocol (e.g., Paxos, Raft) ensuring that a majority of nodes in a distributed system agree on a single value despite failures. |
| **Backpressure** | A flow-control mechanism where a consumer signals the producer to slow down when it cannot keep up with the incoming rate. |
| **Compensation** | A reverse operation that semantically undoes a previously completed local transaction in a saga. |

---

*End of Module 2.2*
