# Module 2.1: Code-Level Architecture & Principles

> **Module 02.1** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Hexagonal/Ports & Adapters > layered.** Better testability.
2. **DDD: bounded context = service boundary.**
3. **Dependency rule: stable depends on stable; volatile inverts.**
4. **CQRS for asymmetric read/write workload.**
5. **Event sourcing: truth = ordered event log; state is derived.**

---

## Table of Contents

1. Clean Architecture
2. Hexagonal Architecture (Ports & Adapters)
3. Onion Architecture
4. CQRS — Command Query Responsibility Segregation
5. Event Sourcing
6. Domain-Driven Design — Tactical Patterns
7. Package & Module Structure
8. Dependency Injection & Inversion of Control
9. Putting It All Together — A Reference Service
10. Common Pitfalls & Troubleshooting
11. Q&A — Frequently Asked Questions
12. Hands-On Exercises
13. References

---

## 1. Clean Architecture

Robert C. Martin (Uncle Bob), 2012. Distills ideas from Hexagonal Architecture, Onion Architecture, DCI, and BCE into a single dependency rule.

### 1.1 Core Idea

> **The Dependency Rule:** Source code dependencies must point only inward — toward higher-level policies.

Nothing in an inner circle may know anything about something in an outer circle.

### 1.2 The Layers

```
┌──────────────────────────────────────────────────────────┐
│                  Frameworks & Drivers                    │
│  (Web server, DB driver, message broker, UI framework)   │
│  ┌──────────────────────────────────────────────────┐    │
│  │            Interface Adapters                     │    │
│  │  (Controllers, Presenters, Gateways, Repos impl) │    │
│  │  ┌──────────────────────────────────────────┐    │    │
│  │  │          Application / Use Cases         │    │    │
│  │  │  (Interactors, application services,     │    │    │
│  │  │   command/query handlers, DTOs)          │    │    │
│  │  │  ┌──────────────────────────────────┐    │    │    │
│  │  │  │       Enterprise Entities        │    │    │    │
│  │  │  │  (Domain models, value objects,  │    │    │    │
│  │  │  │   domain events, specifications) │    │    │    │
│  │  │  └──────────────────────────────────┘    │    │    │
│  │  └──────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

#### Layer 1 — Entities (innermost)

Enterprise-wide business rules. These objects embody the most general and high-level rules. They are the least likely to change when something external changes. No dependency on any framework, database, or delivery mechanism.

```python
# entities/order.py
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)


@dataclass(frozen=True)
class OrderLine:
    product_id: UUID
    quantity: int
    unit_price: Money

    def line_total(self) -> Money:
        return Money(
            amount=self.unit_price.amount * self.quantity,
            currency=self.unit_price.currency,
        )


@dataclass
class Order:
    id: UUID = field(default_factory=uuid4)
    customer_id: UUID = field(default_factory=uuid4)
    lines: List[OrderLine] = field(default_factory=list)
    status: str = "DRAFT"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_line(self, line: OrderLine) -> None:
        if self.status != "DRAFT":
            raise ValueError("Cannot add lines to a non-draft order")
        self.lines.append(line)

    def total(self) -> Money:
        if not self.lines:
            return Money(Decimal("0"))
        result = self.lines[0].line_total()
        for line in self.lines[1:]:
            result = result.add(line.line_total())
        return result

    def submit(self) -> None:
        if not self.lines:
            raise ValueError("Cannot submit an empty order")
        if self.status != "DRAFT":
            raise ValueError(f"Order in {self.status} cannot be submitted")
        self.status = "SUBMITTED"
```

Key: `Order` has zero imports from frameworks. It is a pure domain object.

#### Layer 2 — Use Cases (Application)

Application-specific business rules. Orchestrates the flow of data to and from entities and directs those entities to use their enterprise-wide rules.

```python
# use_cases/submit_order.py
from dataclasses import dataclass
from uuid import UUID

from entities.order import Order


class OrderRepository:
    """Port — defined at the use-case layer, implemented at the adapter layer."""
    def find_by_id(self, order_id: UUID) -> Order:
        raise NotImplementedError

    def save(self, order: Order) -> None:
        raise NotImplementedError


class EventPublisher:
    """Port — publishes domain events."""
    def publish(self, event_name: str, payload: dict) -> None:
        raise NotImplementedError


@dataclass
class SubmitOrderCommand:
    order_id: UUID


class SubmitOrderUseCase:
    def __init__(self, repo: OrderRepository, events: EventPublisher):
        self._repo = repo
        self._events = events

    def execute(self, cmd: SubmitOrderCommand) -> None:
        order = self._repo.find_by_id(cmd.order_id)
        order.submit()  # domain logic
        self._repo.save(order)
        self._events.publish("OrderSubmitted", {
            "order_id": str(order.id),
            "total": str(order.total().amount),
        })
```

Notice: `OrderRepository` and `EventPublisher` are abstract ports. The use-case layer *owns* the interface. Implementations live in the adapter layer.

#### Layer 3 — Interface Adapters

Convert data between the format most convenient for use cases and entities, and the format most convenient for an external agency (DB, web, etc.).

```python
# adapters/postgres_order_repo.py
import psycopg2
from uuid import UUID
from entities.order import Order, OrderLine, Money
from use_cases.submit_order import OrderRepository
from decimal import Decimal


class PostgresOrderRepository(OrderRepository):
    def __init__(self, dsn: str):
        self._dsn = dsn

    def find_by_id(self, order_id: UUID) -> Order:
        conn = psycopg2.connect(self._dsn)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, customer_id, status, created_at "
                "FROM orders WHERE id = %s",
                (str(order_id),),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Order {order_id} not found")

            cur.execute(
                "SELECT product_id, quantity, unit_price, currency "
                "FROM order_lines WHERE order_id = %s",
                (str(order_id),),
            )
            lines = [
                OrderLine(
                    product_id=UUID(r[0]),
                    quantity=r[1],
                    unit_price=Money(Decimal(str(r[2])), r[3]),
                )
                for r in cur.fetchall()
            ]
            return Order(
                id=UUID(row[0]),
                customer_id=UUID(row[1]),
                lines=lines,
                status=row[2],
                created_at=row[3],
            )
        finally:
            conn.close()

    def save(self, order: Order) -> None:
        conn = psycopg2.connect(self._dsn)
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE orders SET status = %s WHERE id = %s",
                (order.status, str(order.id)),
            )
            conn.commit()
        finally:
            conn.close()
```

#### Layer 4 — Frameworks & Drivers (outermost)

The web server, the ORM, the message broker client. Typically thin glue code.

```python
# frameworks/flask_app.py
from flask import Flask, request, jsonify
from uuid import UUID

from adapters.postgres_order_repo import PostgresOrderRepository
from adapters.kafka_event_publisher import KafkaEventPublisher
from use_cases.submit_order import SubmitOrderUseCase, SubmitOrderCommand


app = Flask(__name__)
repo = PostgresOrderRepository(dsn="postgresql://localhost/orders")
events = KafkaEventPublisher(broker="localhost:9092")
submit_uc = SubmitOrderUseCase(repo, events)


@app.post("/orders/<order_id>/submit")
def submit_order(order_id: str):
    cmd = SubmitOrderCommand(order_id=UUID(order_id))
    submit_uc.execute(cmd)
    return jsonify({"status": "submitted"}), 200
```

### 1.3 Data Crossing Boundaries

Data that crosses a boundary must be in the form most convenient for the *inner* circle. Never pass DB rows or ORM entities inward. Use DTOs, plain data structures, or value objects.

```
┌───────────────────────────────────────────────────┐
│  Controller receives HTTP JSON                    │
│      │                                            │
│      ▼                                            │
│  Controller maps JSON → SubmitOrderCommand (DTO)  │
│      │                                            │
│      ▼                                            │
│  Use Case works with domain objects               │
│      │                                            │
│      ▼                                            │
│  Repository maps domain → SQL rows                │
└───────────────────────────────────────────────────┘
```

### 1.4 Testing Benefits

With Clean Architecture, you can test each ring independently:

| Layer | Test Type | Dependencies Needed |
|---|---|---|
| Entities | Unit tests | None — pure domain logic |
| Use Cases | Unit tests | Mock ports (repositories, publishers) |
| Adapters | Integration tests | Real DB, real message broker |
| Framework | E2E tests | Full stack |

This gives you a fast feedback loop: entity and use-case tests run in milliseconds because they never touch I/O.

---

## 2. Hexagonal Architecture (Ports & Adapters)

Alistair Cockburn, 2005. Independently derived the same core idea as Clean Architecture but with a different metaphor.

### 2.1 Core Metaphor

The application is a hexagon. Each face of the hexagon is a *port*. Connected to each port is an *adapter*.

```
                    ┌───────────────────────┐
                    │     Driving Side      │
                    │   (Primary Adapters)  │
                    └────────┬──────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │             Port: OrderAPI               │
        │  ┌─────────────────────────────────────┐ │
        │  │                                     │ │
REST ───┤  │        Application Core             │ ├─── PostgreSQL
        │  │                                     │ │
CLI  ───┤  │   (Domain Model + Use Cases)        │ ├─── Redis
        │  │                                     │ │
gRPC ───┤  │                                     │ ├─── Kafka
        │  └─────────────────────────────────────┘ │
        │             Port: Persistence            │
        └────────────────────┬────────────────────┘
                             │
                    ┌────────▼──────────────┐
                    │     Driven Side       │
                    │  (Secondary Adapters) │
                    └───────────────────────┘
```

### 2.2 Ports

A port is an interface. It defines a protocol of interaction but says nothing about the implementation.

**Primary (Driving) Ports** — define what the application *offers*. Typically the use case boundary.

```java
// port/in/SubmitOrderPort.java
public interface SubmitOrderPort {
    void submitOrder(UUID orderId);
}
```

**Secondary (Driven) Ports** — define what the application *needs*. Typically infrastructure concerns.

```java
// port/out/LoadOrderPort.java
public interface LoadOrderPort {
    Order loadById(UUID orderId);
}

// port/out/SaveOrderPort.java
public interface SaveOrderPort {
    void save(Order order);
}

// port/out/PublishEventPort.java
public interface PublishEventPort {
    void publish(String eventName, Map<String, Object> payload);
}
```

### 2.3 Adapters

An adapter implements a port.

**Primary Adapter** — drives the application from the outside.

```java
// adapter/in/web/OrderController.java
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final SubmitOrderPort submitOrderPort;

    public OrderController(SubmitOrderPort submitOrderPort) {
        this.submitOrderPort = submitOrderPort;
    }

    @PostMapping("/{id}/submit")
    public ResponseEntity<Void> submit(@PathVariable UUID id) {
        submitOrderPort.submitOrder(id);
        return ResponseEntity.ok().build();
    }
}
```

**Secondary Adapter** — reacts to the application's needs.

```java
// adapter/out/persistence/JpaOrderRepository.java
@Repository
public class JpaOrderRepository implements LoadOrderPort, SaveOrderPort {
    private final JpaOrderEntityRepository jpa;
    private final OrderMapper mapper;

    @Override
    public Order loadById(UUID orderId) {
        JpaOrderEntity entity = jpa.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
        return mapper.toDomain(entity);
    }

    @Override
    public void save(Order order) {
        jpa.save(mapper.toEntity(order));
    }
}
```

### 2.4 Hexagonal vs Clean Architecture — Comparison

| Dimension | Hexagonal | Clean |
|---|---|---|
| Metaphor | Ports on a hexagon | Concentric rings |
| Number of rings | Not prescriptive (core vs adapters) | Four explicit rings |
| Driving vs Driven | Explicitly named | Implicit in data flow |
| Data transfer | Not prescriptive | Strict: DTOs at boundaries |
| Origin | Cockburn 2005 | Martin 2012 |
| Practical difference | Minimal | Minimal |

Both enforce the same dependency direction. In practice, teams blend them.

### 2.5 The Configurator

Someone must wire ports to adapters. This is the *composition root* — typically `main()` or a DI container configuration.

```python
# main.py  (composition root)
def create_app():
    repo = PostgresOrderRepository(dsn=os.environ["DATABASE_URL"])
    events = KafkaEventPublisher(broker=os.environ["KAFKA_BROKER"])
    submit_uc = SubmitOrderUseCase(repo=repo, events=events)
    app = create_flask_app(submit_order_port=submit_uc)
    return app
```

This is the *only* place where concrete implementations are known. Every other module works with abstractions.

---

## 3. Onion Architecture

Jeffrey Palermo, 2008. A visual variant that emphasizes layering from the inside out, similar to Clean Architecture but chronologically between Hexagonal and Clean.

```
┌──────────────────────────────────────────────┐
│             Infrastructure                   │
│  ┌──────────────────────────────────────┐    │
│  │        Application Services          │    │
│  │  ┌──────────────────────────────┐    │    │
│  │  │       Domain Services        │    │    │
│  │  │  ┌──────────────────────┐    │    │    │
│  │  │  │    Domain Model      │    │    │    │
│  │  │  └──────────────────────┘    │    │    │
│  │  └──────────────────────────────┘    │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

Key distinction: Onion separates *Domain Services* (business logic spanning multiple aggregates) from *Application Services* (workflow orchestration, transaction management).

All three — Hexagonal, Onion, Clean — share the **dependency rule**: outer depends on inner, never the reverse.

---

## 4. CQRS — Command Query Responsibility Segregation

Greg Young, 2010. Evolved from Bertrand Meyer's CQS (Command-Query Separation) principle applied at the architectural level.

### 4.1 Motivation

In many systems, read and write workloads are asymmetric:

| Dimension | Writes | Reads |
|---|---|---|
| Volume | 10% of traffic | 90% of traffic |
| Model | Complex validation, invariants | Denormalized projections, joins |
| Consistency | Must be strongly consistent | Eventual consistency often acceptable |
| Scaling | Needs durable, ordered writes | Can be cached, replicated, materialized |

A single model that serves both is a compromise.

### 4.2 The Pattern

```
                ┌──────────────┐
                │   Client     │
                └──┬────────┬──┘
                   │        │
            Command│        │Query
                   ▼        ▼
         ┌─────────────┐ ┌─────────────┐
         │  Write Model │ │  Read Model  │
         │  (Commands)  │ │  (Queries)   │
         └──────┬──────┘ └──────▲──────┘
                │               │
                ▼               │
         ┌──────────┐   ┌──────┴──────┐
         │ Write DB  │──▶│  Read DB     │
         │ (Source   │   │ (Projections,│
         │  of Truth)│   │  Materialized│
         └──────────┘   │  Views)      │
                        └─────────────┘
```

**Write Side (Command Model):**
- Enforces business rules, validates invariants.
- Stores normalized data.
- Rejects invalid state transitions.
- Uses domain objects with rich behavior.

**Read Side (Query Model):**
- Optimized for specific UI views.
- Denormalized: pre-computed joins, flattened structures.
- Can use different storage technology (Elasticsearch, Redis, a read replica).
- Updated asynchronously from the write side.

### 4.3 Synchronization Strategies

The read model must stay synchronized with the write model.

**Strategy 1 — Database Views / Materialized Views:**

```sql
-- Write model: normalized tables
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE order_lines (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    product_name VARCHAR(255),
    quantity INT,
    unit_price NUMERIC(10,2)
);

-- Read model: materialized view
CREATE MATERIALIZED VIEW order_summary AS
SELECT
    o.id AS order_id,
    o.customer_id,
    o.status,
    o.created_at,
    COUNT(ol.id) AS line_count,
    SUM(ol.quantity * ol.unit_price) AS total_amount
FROM orders o
LEFT JOIN order_lines ol ON o.id = ol.order_id
GROUP BY o.id, o.customer_id, o.status, o.created_at;

-- Refresh periodically or on trigger
REFRESH MATERIALIZED VIEW CONCURRENTLY order_summary;
```

**Strategy 2 — Domain Events:**

```python
class OrderSubmittedHandler:
    """Listens for OrderSubmitted events, updates the read model."""
    def __init__(self, read_db):
        self._read_db = read_db

    def handle(self, event: dict) -> None:
        self._read_db.execute(
            "UPDATE order_summary SET status = 'SUBMITTED', "
            "submitted_at = %s WHERE order_id = %s",
            (event["timestamp"], event["order_id"]),
        )
```

**Strategy 3 — CDC (Change Data Capture):**

Use Debezium to tail the write DB's WAL/binlog and project changes into the read store automatically.

### 4.4 When to Use CQRS

**Good fit:**
- Read/write ratio heavily skewed (10:1 or more).
- Read model needs a different storage engine (e.g., writes in Postgres, reads in Elasticsearch).
- Multiple UI views need different projections of the same data.
- Combined with event sourcing.

**Bad fit:**
- Simple CRUD with no asymmetry.
- Small teams that cannot afford the operational overhead of two data stores.
- Use cases where strong read-after-write consistency is required everywhere.

### 4.5 CQRS vs CQS

| | CQS | CQRS |
|---|---|---|
| Scope | Method level | Architecture level |
| Rule | A method either *commands* (mutates, returns void) or *queries* (returns data, no side effects) | Separate *models* for read and write |
| Author | Bertrand Meyer | Greg Young |
| Overhead | None — just a coding convention | Significant — separate data stores, sync |

---

## 5. Event Sourcing

### 5.1 Core Idea

Instead of storing current state, store the *sequence of events* that led to the current state. The event log is the source of truth; current state is derived by replaying events.

```
Traditional:  Account { balance: 750 }

Event Sourced:
  1. AccountCreated   { id: A1, owner: "Alice" }
  2. MoneyDeposited   { id: A1, amount: 1000 }
  3. MoneyWithdrawn   { id: A1, amount: 200 }
  4. MoneyWithdrawn   { id: A1, amount: 50 }

Current state = replay(events) → balance = 0 + 1000 - 200 - 50 = 750
```

### 5.2 Event Store Structure

```
┌────────────────────────────────────────────────────────────┐
│                    EVENT STORE                             │
├──────────┬─────────────┬────────────────┬─────────────────┤
│ StreamID │ Version     │ EventType      │ Payload (JSON)  │
├──────────┼─────────────┼────────────────┼─────────────────┤
│ acct-A1  │ 1           │ AccountCreated │ {"owner":"..."}  │
│ acct-A1  │ 2           │ MoneyDeposited │ {"amount":1000} │
│ acct-A1  │ 3           │ MoneyWithdrawn │ {"amount":200}  │
│ acct-A1  │ 4           │ MoneyWithdrawn │ {"amount":50}   │
└──────────┴─────────────┴────────────────┴─────────────────┘
```

Key properties:
- **Append-only:** events are immutable. You never UPDATE or DELETE.
- **Versioned:** optimistic concurrency via version numbers.
- **Ordered:** within a stream, events have a strict total order.

### 5.3 Aggregate Reconstruction

```python
class BankAccount:
    def __init__(self):
        self.id = None
        self.balance = Decimal("0")
        self.status = "UNINITIALIZED"
        self._pending_events = []

    # --- Command methods ---
    def deposit(self, amount: Decimal) -> None:
        if self.status != "ACTIVE":
            raise ValueError("Account not active")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self._apply(MoneyDeposited(account_id=self.id, amount=amount))

    def withdraw(self, amount: Decimal) -> None:
        if self.status != "ACTIVE":
            raise ValueError("Account not active")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self._apply(MoneyWithdrawn(account_id=self.id, amount=amount))

    # --- Event application (state transitions) ---
    def _apply(self, event):
        self._on(event)
        self._pending_events.append(event)

    def _on(self, event):
        if isinstance(event, AccountCreated):
            self.id = event.account_id
            self.status = "ACTIVE"
        elif isinstance(event, MoneyDeposited):
            self.balance += event.amount
        elif isinstance(event, MoneyWithdrawn):
            self.balance -= event.amount

    # --- Reconstruction ---
    @classmethod
    def from_events(cls, events):
        account = cls()
        for event in events:
            account._on(event)
        return account
```

### 5.4 Snapshots

Replaying 10 million events per request is not viable. Snapshots solve this.

```
Events:      [1] [2] [3] ... [999] [1000]  ← snapshot taken here
                                     │
                                     ▼
Snapshot:    { balance: 87500, status: "ACTIVE", version: 1000 }

Load: snapshot(1000) + events[1001..1003] → current state
```

Snapshot strategies:
- **Periodic:** every N events (e.g., 100).
- **On demand:** when load time exceeds a threshold.
- **Scheduled:** background job.

### 5.5 Event Sourcing + CQRS

Event sourcing and CQRS are natural partners:

```
                  ┌──────────┐
                  │ Command  │
                  └────┬─────┘
                       │
                       ▼
               ┌───────────────┐
               │   Aggregate   │
               │ (Apply Events)│
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │  Event Store  │──────┐
               │ (Append Only) │      │ Publish
               └───────────────┘      │
                                      ▼
                              ┌───────────────┐
                              │  Projector    │
                              │ (Event Handler│
                              │  → Read Model)│
                              └───────┬───────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │   Read DB     │
                              │ (Denormalized)│
                              └───────────────┘
                                      ▲
                                      │
                              ┌───────┴───────┐
                              │    Query       │
                              └───────────────┘
```

### 5.6 Event Versioning & Upcasting

Events are immutable, but schemas evolve. You cannot ALTER old events. Instead, use upcasters.

```python
# Version 1 event
{"type": "AddressChanged", "v": 1, "city": "NYC", "state": "NY"}

# Version 2 adds zip code (new field, default)
# Upcaster transforms v1 → v2 on read
class AddressChangedV1ToV2Upcaster:
    def upcast(self, event):
        if event["v"] == 1:
            event["zip"] = "UNKNOWN"
            event["v"] = 2
        return event
```

Rules for event evolution:
1. **Add fields** with defaults — safe.
2. **Rename fields** — upcaster transforms old events.
3. **Remove fields** — old events keep them; new code ignores them.
4. **Never** change the semantic meaning of an existing field.

### 5.7 When to Use Event Sourcing

**Good fit:**
- Audit-critical domains (finance, healthcare, legal).
- Temporal queries ("What was the portfolio value at 3pm yesterday?").
- Complex domain logic with many state transitions.
- Need to replay events to rebuild read models or fix projection bugs.

**Bad fit:**
- Simple CRUD with no audit requirements.
- High-volume, low-value events (sensor telemetry — consider time-series DB instead).
- Team unfamiliar with eventual consistency.

---

## 6. Domain-Driven Design — Tactical Patterns

Eric Evans (2003) and Vaughn Vernon (2013). Tactical patterns are the building blocks used *within* a bounded context.

### 6.1 Building Block Overview

```
┌────────────────────────────────────────────────────────────┐
│                    Bounded Context                         │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │   Aggregate   │  │   Aggregate  │  │   Aggregate    │   │
│  │  ┌─────────┐  │  │  ┌────────┐ │  │  ┌──────────┐  │   │
│  │  │ Entity  │  │  │  │ Entity │ │  │  │  Entity   │  │   │
│  │  │ (Root)  │  │  │  │ (Root) │ │  │  │  (Root)   │  │   │
│  │  └─────────┘  │  │  └────────┘ │  │  └──────────┘  │   │
│  │  ┌─────────┐  │  │  ┌────────┐ │  │  ┌──────────┐  │   │
│  │  │  Value   │  │  │  │ Value  │ │  │  │  Entity   │  │   │
│  │  │  Object  │  │  │  │ Object │ │  │  │  (Child)  │  │   │
│  │  └─────────┘  │  │  └────────┘ │  │  └──────────┘  │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ Domain Event │  │  Repository  │  │ Domain Service │   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  Factory     │  │ Specification│                        │
│  └──────────────┘  └──────────────┘                        │
└────────────────────────────────────────────────────────────┘
```

### 6.2 Entity

An object defined by its **identity**, not its attributes. Two entities with the same attributes but different IDs are different.

```python
@dataclass
class Customer:
    id: UUID                   # <-- identity
    name: str
    email: str
    registered_at: datetime

    def __eq__(self, other):
        if not isinstance(other, Customer):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
```

### 6.3 Value Object

An object defined by its **attributes**. Two value objects with the same attributes are interchangeable. Immutable.

```python
@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str

    def with_updated_zip(self, new_zip: str) -> "Address":
        """Value objects are immutable — return a new instance."""
        return Address(
            street=self.street,
            city=self.city,
            state=self.state,
            zip_code=new_zip,
            country=self.country,
        )


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: int) -> "Money":
        return Money(self.amount * factor, self.currency)
```

Key: `frozen=True` enforces immutability at the language level. Equality is structural (all fields match), not identity-based.

### 6.4 Aggregate

A cluster of entities and value objects treated as a single unit for data changes. One entity is the **Aggregate Root** — the only entry point for external access.

```python
class Order:  # Aggregate Root
    def __init__(self, order_id: UUID, customer_id: UUID):
        self._id = order_id
        self._customer_id = customer_id
        self._lines: List[OrderLine] = []      # internal entities
        self._status = OrderStatus.DRAFT
        self._events: List[DomainEvent] = []

    @property
    def id(self) -> UUID:
        return self._id

    def add_line(self, product_id: UUID, qty: int, price: Money) -> None:
        """All mutations go through the aggregate root."""
        if self._status != OrderStatus.DRAFT:
            raise InvalidOperationError("Cannot modify a non-draft order")
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        line = OrderLine(
            line_id=uuid4(), product_id=product_id,
            quantity=qty, unit_price=price,
        )
        self._lines.append(line)

    def submit(self) -> None:
        if not self._lines:
            raise InvalidOperationError("Cannot submit empty order")
        self._status = OrderStatus.SUBMITTED
        self._events.append(OrderSubmitted(
            order_id=self._id,
            total=self._calculate_total(),
        ))

    def pull_events(self) -> List[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def _calculate_total(self) -> Money:
        totals = [line.line_total() for line in self._lines]
        result = totals[0]
        for t in totals[1:]:
            result = result.add(t)
        return result
```

**Aggregate Rules (Evans):**
1. Reference other aggregates *by ID only*, never by direct object reference.
2. A single transaction modifies *one* aggregate.
3. Invariants within an aggregate are enforced synchronously.
4. Invariants across aggregates are enforced with eventual consistency (domain events).

### 6.5 Domain Event

Something that happened in the domain that domain experts care about.

```python
@dataclass(frozen=True)
class OrderSubmitted:
    order_id: UUID
    total: Money
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
```

Domain events enable loose coupling between aggregates and bounded contexts. Published after the aggregate is saved, consumed by event handlers, projectors, or sagas.

### 6.6 Repository

A collection-like interface for retrieving and persisting aggregates. One repository per aggregate root.

```python
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: UUID) -> Order:
        ...

    @abstractmethod
    def save(self, order: Order) -> None:
        ...

    @abstractmethod
    def next_id(self) -> UUID:
        ...
```

The repository hides persistence mechanics. The domain layer never knows whether data lives in Postgres, MongoDB, or an in-memory dict.

### 6.7 Domain Service

Logic that does not naturally belong to any single entity or value object. Typically involves coordination across multiple aggregates or external policies.

```python
class TransferService:
    """Domain service: transfer money between two accounts."""
    def __init__(self, account_repo: AccountRepository):
        self._repo = account_repo

    def transfer(self, from_id: UUID, to_id: UUID, amount: Money) -> None:
        source = self._repo.find_by_id(from_id)
        target = self._repo.find_by_id(to_id)

        source.withdraw(amount)
        target.deposit(amount)

        self._repo.save(source)
        self._repo.save(target)
```

Note: In a microservices world, this would likely be a saga (see Module 2.2), because each account might be in a different service.

### 6.8 Factory

Encapsulates complex creation logic.

```python
class OrderFactory:
    @staticmethod
    def create_from_cart(cart: ShoppingCart, customer_id: UUID) -> Order:
        order = Order(order_id=uuid4(), customer_id=customer_id)
        for item in cart.items:
            order.add_line(
                product_id=item.product_id,
                qty=item.quantity,
                price=item.unit_price,
            )
        return order
```

### 6.9 Specification Pattern

Encapsulates a business rule as a reusable, composable predicate.

```python
from abc import ABC, abstractmethod


class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool:
        ...

    def and_(self, other: "Specification") -> "Specification":
        return AndSpecification(self, other)

    def or_(self, other: "Specification") -> "Specification":
        return OrSpecification(self, other)

    def not_(self) -> "Specification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left, right):
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate) -> bool:
        return (self._left.is_satisfied_by(candidate)
                and self._right.is_satisfied_by(candidate))


# Usage
class IsHighValue(Specification):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.total().amount > Decimal("10000")

class IsInternational(Specification):
    def is_satisfied_by(self, order: Order) -> bool:
        return order.shipping_address.country != "US"

needs_review = IsHighValue().and_(IsInternational())
if needs_review.is_satisfied_by(order):
    order.flag_for_manual_review()
```

### 6.10 Bounded Context Mapping

Tactical patterns live *inside* a bounded context. Between contexts, define relationships:

```
┌──────────────┐                ┌──────────────┐
│   Orders     │  Conformist    │  Shipping     │
│   Context    │ ─────────────▶ │  Context      │
└──────────────┘                └──────────────┘
       │                               │
       │  Customer/Supplier            │ Anti-Corruption Layer
       ▼                               ▼
┌──────────────┐                ┌──────────────┐
│   Payment    │  Shared Kernel │  Inventory    │
│   Context    │ ◀────────────▶ │  Context      │
└──────────────┘                └──────────────┘
```

| Pattern | Description |
|---|---|
| **Shared Kernel** | Two contexts share a small, co-evolved model. Requires coordination. |
| **Customer/Supplier** | Upstream (supplier) provides; downstream (customer) conforms or negotiates. |
| **Conformist** | Downstream fully adopts upstream's model. No translation. |
| **Anti-Corruption Layer (ACL)** | Downstream translates upstream's model into its own. Protects domain purity. |
| **Open Host Service** | Upstream publishes a well-defined protocol (API) for multiple consumers. |
| **Published Language** | Shared interchange format (protobuf, JSON schema, Avro). |
| **Separate Ways** | No integration; contexts are independent. |

---

## 7. Package & Module Structure

### 7.1 Package by Feature vs Package by Layer

**Package by Layer (common but inferior):**

```
src/
├── controllers/
│   ├── OrderController.java
│   ├── CustomerController.java
│   └── ProductController.java
├── services/
│   ├── OrderService.java
│   ├── CustomerService.java
│   └── ProductService.java
├── repositories/
│   ├── OrderRepository.java
│   ├── CustomerRepository.java
│   └── ProductRepository.java
└── models/
    ├── Order.java
    ├── Customer.java
    └── Product.java
```

Problems: high coupling between layers, low cohesion within packages, changing a feature requires touching 4+ packages, package-private visibility is useless.

**Package by Feature (recommended):**

```
src/
├── order/
│   ├── Order.java               # Entity
│   ├── OrderLine.java           # Value Object
│   ├── OrderRepository.java     # Port
│   ├── OrderService.java        # Use Case
│   ├── OrderController.java     # Adapter
│   └── JpaOrderRepository.java  # Adapter impl
├── customer/
│   ├── Customer.java
│   ├── CustomerRepository.java
│   └── ...
└── product/
    ├── Product.java
    └── ...
```

Benefits: high cohesion (everything about orders is together), easy to extract into a microservice, package-private visibility works (implementation details are hidden).

### 7.2 Hexagonal Package Structure

When using Hexagonal Architecture, combine feature-based and port/adapter grouping:

```
src/
├── order/
│   ├── domain/
│   │   ├── Order.java
│   │   ├── OrderLine.java
│   │   ├── OrderStatus.java
│   │   └── OrderSubmitted.java        # Domain Event
│   ├── application/
│   │   ├── port/
│   │   │   ├── in/
│   │   │   │   └── SubmitOrderPort.java
│   │   │   └── out/
│   │   │       ├── LoadOrderPort.java
│   │   │       └── SaveOrderPort.java
│   │   └── service/
│   │       └── SubmitOrderService.java  # Use Case
│   └── adapter/
│       ├── in/
│       │   └── web/
│       │       ├── OrderController.java
│       │       └── OrderDto.java
│       └── out/
│           └── persistence/
│               ├── JpaOrderRepository.java
│               └── JpaOrderEntity.java
├── customer/
│   └── ...
└── shared/
    └── kernel/
        ├── Money.java
        └── DomainEvent.java
```

### 7.3 Module Dependency Rules

Enforce with build tools (Gradle, Maven, Go modules, Python namespace packages):

```
order.domain         → depends on nothing (or shared.kernel)
order.application    → depends on order.domain
order.adapter.in     → depends on order.application
order.adapter.out    → depends on order.application + order.domain
```

In Java, use ArchUnit to enforce:

```java
@AnalyzeClasses(packages = "com.example")
class ArchitectureTest {
    @ArchTest
    static final ArchRule domain_does_not_depend_on_adapters =
        noClasses().that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..adapter..");

    @ArchTest
    static final ArchRule domain_does_not_depend_on_application =
        noClasses().that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..application..");
}
```

---

## 8. Dependency Injection & Inversion of Control

### 8.1 IoC — The Principle

**Inversion of Control** is a design principle where the framework or container controls the flow, not the application code. DI is one *mechanism* for achieving IoC.

Other IoC manifestations:
- Template Method pattern (framework calls your override).
- Event-driven systems (framework dispatches your handler).
- Plugin architectures (framework loads your module).

### 8.2 DI Mechanisms

#### Constructor Injection (preferred)

```java
public class OrderService {
    private final OrderRepository repo;
    private final EventPublisher events;

    // All dependencies explicit, immutable after construction
    public OrderService(OrderRepository repo, EventPublisher events) {
        this.repo = Objects.requireNonNull(repo);
        this.events = Objects.requireNonNull(events);
    }
}
```

Advantages: explicit dependencies, immutable fields, compile-time safety, easy to test.

#### Setter Injection

```java
public class OrderService {
    private OrderRepository repo;

    public void setRepo(OrderRepository repo) {
        this.repo = repo;
    }
}
```

Disadvantages: mutable, partially constructed objects possible, hard to enforce required dependencies.

#### Interface Injection

```java
public interface RepositoryAware {
    void injectRepository(OrderRepository repo);
}

public class OrderService implements RepositoryAware {
    private OrderRepository repo;

    @Override
    public void injectRepository(OrderRepository repo) {
        this.repo = repo;
    }
}
```

Rarely used in modern systems. Constructor injection is almost always the right choice.

### 8.3 Container Implementations

#### Reflection-Based (Spring, Guice, NestJS)

```
Startup:
  1. Scan classpath / module graph
  2. Find classes annotated with @Component / @Injectable / etc.
  3. Build dependency graph
  4. Detect cycles (throw if found)
  5. Topological sort
  6. Instantiate in order using reflection
```

**Pros:** Easy to use, highly dynamic (profiles, conditional beans).
**Cons:** Slow startup (classpath scanning), runtime errors for missing dependencies, harder to trace call graph.

#### Compile-Time Code Generation (Dagger 2, Wire)

```
Compile time:
  1. Annotation processor reads @Inject annotations
  2. Builds dependency graph
  3. Generates concrete factory classes:
     DaggerAppComponent.java:
       OrderService provideOrderService() {
           return new OrderService(
               new PostgresOrderRepository(dataSource),
               new KafkaEventPublisher(config)
           );
       }
  4. Build fails if graph is incomplete or cyclic
```

**Pros:** Zero reflection overhead, compile-time validation, fast startup, AOT-friendly.
**Cons:** More boilerplate, generated code can be hard to read.

#### Manual / Pure DI (no container)

```python
# main.py
def main():
    config = load_config()
    db = create_connection_pool(config.database_url)
    repo = PostgresOrderRepository(db)
    events = KafkaEventPublisher(config.kafka_broker)
    service = OrderService(repo, events)
    app = create_web_app(service)
    app.run()
```

**Pros:** No magic, trivial to debug, no framework dependency.
**Cons:** Manual wiring becomes tedious in large systems, no lifecycle management (scopes).

### 8.4 Service Locator vs DI

Service Locator is an anti-pattern when used as a replacement for DI.

```java
// Service Locator — AVOID
public class OrderService {
    public void submitOrder(UUID orderId) {
        OrderRepository repo = ServiceLocator.get(OrderRepository.class);
        repo.findById(orderId);
    }
}
```

Problems:
- **Hidden dependencies:** the class signature does not reveal what it needs.
- **Testing difficulty:** must configure global locator in every test.
- **Runtime failures:** missing registrations found only at runtime.

DI makes dependencies explicit in the constructor, visible in the type signature, and injectable in tests.

### 8.5 Scopes and Lifecycles

| Scope | Lifetime | Use Case |
|---|---|---|
| **Singleton** | One instance for the app's lifetime | Stateless services, connection pools |
| **Prototype / Transient** | New instance per injection | Stateful objects, builders |
| **Request** | One instance per HTTP request | Request-scoped data (user context) |
| **Session** | One instance per user session | Shopping cart, wizard state |

```java
// Spring scope examples
@Component
@Scope("singleton")       // default
public class OrderService { }

@Component
@Scope("request")
public class RequestContext { }
```

---

## 9. Putting It All Together — A Reference Service

Combining Clean/Hexagonal Architecture, DDD Tactical Patterns, CQRS, and DI for a single microservice:

```
order-service/
├── src/
│   ├── domain/                    # Inner ring — no external deps
│   │   ├── model/
│   │   │   ├── Order.py           # Aggregate Root (Entity)
│   │   │   ├── OrderLine.py       # Entity (child)
│   │   │   ├── OrderStatus.py     # Value Object (enum)
│   │   │   └── Money.py           # Value Object
│   │   ├── event/
│   │   │   ├── OrderSubmitted.py  # Domain Event
│   │   │   └── OrderCancelled.py
│   │   ├── service/
│   │   │   └── PricingService.py  # Domain Service
│   │   └── spec/
│   │       └── HighValueOrder.py  # Specification
│   │
│   ├── application/               # Use cases — depends on domain only
│   │   ├── port/
│   │   │   ├── inbound/
│   │   │   │   ├── SubmitOrderPort.py
│   │   │   │   └── CancelOrderPort.py
│   │   │   └── outbound/
│   │   │       ├── OrderRepository.py
│   │   │       ├── EventPublisher.py
│   │   │       └── PaymentGateway.py
│   │   ├── command/
│   │   │   ├── SubmitOrderHandler.py
│   │   │   └── CancelOrderHandler.py
│   │   └── query/
│   │       └── GetOrderSummaryHandler.py
│   │
│   ├── adapter/                   # Outer ring — framework-specific
│   │   ├── inbound/
│   │   │   ├── rest/
│   │   │   │   ├── OrderController.py
│   │   │   │   └── OrderDto.py
│   │   │   └── grpc/
│   │   │       └── OrderGrpcService.py
│   │   └── outbound/
│   │       ├── persistence/
│   │       │   ├── PostgresOrderRepo.py
│   │       │   └── OrderEntity.py
│   │       ├── messaging/
│   │       │   └── KafkaEventPublisher.py
│   │       └── payment/
│   │           └── StripePaymentGateway.py
│   │
│   └── config/                    # Composition root
│       └── container.py           # Wires ports to adapters
│
├── tests/
│   ├── unit/
│   │   ├── domain/                # Fast — no I/O
│   │   └── application/           # Mock ports
│   ├── integration/
│   │   └── adapter/               # Real DB, real Kafka
│   └── e2e/
│       └── test_order_flow.py     # Full stack
│
└── main.py                        # Entry point
```

### Data Flow for "Submit Order"

```
1. HTTP POST /orders/{id}/submit
          │
          ▼
2. OrderController (Adapter/In)
   → parses request, creates SubmitOrderCommand
          │
          ▼
3. SubmitOrderHandler (Application/Command)
   → calls repo.find_by_id(id)
   → calls order.submit()            # Domain logic
   → calls repo.save(order)
   → calls events.publish(order.pull_events())
          │                │
          ▼                ▼
4a. PostgresOrderRepo  4b. KafkaEventPublisher
    (Adapter/Out)           (Adapter/Out)
    → UPDATE orders         → produce to topic
      SET status=...          "order.submitted"
```

---

## 10. Common Pitfalls & Troubleshooting

### Pitfall 1: Anemic Domain Model

**Symptom:** Entities are data bags with getters/setters. All logic lives in services.

```python
# ANEMIC — entity is just a struct
class Order:
    id: UUID
    status: str
    lines: list

class OrderService:
    def submit(self, order: Order):
        if not order.lines:
            raise ValueError("Empty")
        order.status = "SUBMITTED"  # logic belongs on the entity
```

**Fix:** Push behavior onto the entity. The entity enforces its own invariants.

```python
class Order:
    def submit(self) -> None:
        if not self._lines:
            raise ValueError("Cannot submit empty order")
        self._status = OrderStatus.SUBMITTED
```

### Pitfall 2: Leaking Domain Objects Through API Boundaries

**Symptom:** Controller returns the domain entity directly as JSON.

```python
@app.get("/orders/{id}")
def get_order(id):
    order = repo.find_by_id(id)
    return jsonify(order.__dict__)  # leaks internal structure
```

**Fix:** Map to a DTO. Internal changes do not break the API contract.

```python
@app.get("/orders/{id}")
def get_order(id):
    order = repo.find_by_id(id)
    return jsonify({
        "id": str(order.id),
        "status": order.status.value,
        "total": str(order.total().amount),
    })
```

### Pitfall 3: Over-Engineering for a CRUD App

**Symptom:** Full hexagonal + CQRS + event sourcing for a two-entity admin panel.

**Fix:** Use the simplest architecture that works. Graduate to more complex patterns when the domain demands it.

| Complexity Level | Architecture |
|---|---|
| Simple CRUD (< 5 entities, no business logic) | MVC + ORM |
| Moderate (business rules, some invariants) | Clean/Hexagonal |
| Complex (many aggregates, workflows, audit) | Hexagonal + DDD |
| Event-driven (temporal queries, replay, audit log) | Hexagonal + DDD + CQRS + Event Sourcing |

### Pitfall 4: Aggregate Too Large

**Symptom:** One aggregate contains hundreds of entities. Loading it requires multiple JOINs. Transaction contention is high.

**Fix:** Split into smaller aggregates. Use domain events for eventual consistency between them.

```
BEFORE: Order (aggregate root)
  └── 10,000 OrderLines (all loaded, all locked)

AFTER:  Order (aggregate root, lightweight)
  └── references OrderLineGroup by ID

        OrderLineGroup (separate aggregate)
        └── 100 OrderLines
```

### Pitfall 5: Circular Dependencies Between Packages

**Symptom:** `order.domain` imports from `customer.domain`, and `customer.domain` imports from `order.domain`.

**Fix options:**
1. Extract the shared concept into `shared.kernel`.
2. Introduce a domain event: `Order` publishes `OrderSubmitted`, `Customer` subscribes.
3. Use an interface in one package, implement in the other.

### Pitfall 6: Injecting the Container

**Symptom:** Classes depend on the DI container itself.

```java
public class OrderService {
    private final ApplicationContext ctx;

    public void submit(UUID id) {
        OrderRepository repo = ctx.getBean(OrderRepository.class);
        // ...
    }
}
```

This is Service Locator disguised as DI. Dependencies are hidden. Fix: inject the actual dependencies, not the container.

---

## 11. Q&A — Frequently Asked Questions

**Q1: Must I use all four Clean Architecture layers?**
A: No. The dependency rule is the invariant. If your system is simple, two layers (domain + infrastructure) suffice. Add layers as complexity demands.

**Q2: How do I handle cross-cutting concerns (logging, metrics, auth) in Clean Architecture?**
A: Use decorators or middleware at the adapter/framework layer. Never pollute the domain with infrastructure concerns.

```python
class LoggingOrderRepository(OrderRepository):
    def __init__(self, inner: OrderRepository, logger):
        self._inner = inner
        self._logger = logger

    def find_by_id(self, order_id: UUID) -> Order:
        self._logger.info(f"Loading order {order_id}")
        return self._inner.find_by_id(order_id)

    def save(self, order: Order) -> None:
        self._inner.save(order)
        self._logger.info(f"Saved order {order.id}")
```

**Q3: Can I use an ORM inside the domain layer?**
A: No. ORM annotations (JPA `@Entity`, `@Column`) couple the domain to a framework. Options:
1. Map domain objects to/from ORM entities in the adapter layer.
2. Use lightweight mapping (data classes + manual SQL) instead of a full ORM.

**Q4: When should I introduce DI container vs manual DI?**
A: Manual DI works well up to ~30-50 components. Beyond that, the wiring code becomes tedious and error-prone. Introduce a container when the composition root becomes a maintenance burden.

**Q5: How does CQRS handle "read-after-write" consistency?**
A: Options:
1. **Synchronous projection:** update read model in the same transaction (simple, but couples read/write).
2. **Polling:** client polls until the read model catches up (adds latency perception).
3. **Subscription:** client subscribes to the event stream and updates locally.
4. **Causal tokens:** write returns a token; read passes it and blocks until the projection reaches that token's version.

**Q6: What is the difference between Application Service and Domain Service?**
A: Application services orchestrate *infrastructure* (transactions, event publishing, auth checks). Domain services encapsulate *domain logic* that spans multiple aggregates. Domain services are part of the domain layer; application services are part of the application layer.

**Q7: How many events before I need snapshots in event sourcing?**
A: Benchmark your specific case, but a common rule of thumb: snapshot every 100-500 events per stream. If reconstruction takes > 50ms, snapshot.

**Q8: How do I test aggregates that produce domain events?**
A: Assert on the events returned by `pull_events()`.

```python
def test_submit_order_produces_event():
    order = Order(order_id=uuid4(), customer_id=uuid4())
    order.add_line(product_id=uuid4(), qty=2, price=Money(Decimal("10"), "USD"))

    order.submit()

    events = order.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], OrderSubmitted)
    assert events[0].total == Money(Decimal("20"), "USD")
```

**Q9: Is Hexagonal Architecture only for microservices?**
A: No. It works for monoliths, CLIs, batch jobs, desktop apps — any system where you want to isolate domain logic from infrastructure. It is architecture-scale-agnostic.

**Q10: How do I evolve from a monolith to microservices using these patterns?**
A: The "Strangler Fig" approach:
1. Identify bounded contexts in the monolith.
2. Structure them as feature packages with clear ports.
3. Extract one context at a time into its own deployable service.
4. Replace internal method calls with HTTP/gRPC/events via an ACL.
5. Keep the monolith running until all contexts are extracted.

---

## 12. Hands-On Exercises

### Exercise 1: Implement a Banking Domain (Beginner)

Build a bank account module using Hexagonal Architecture.

**Requirements:**
- Create an `Account` entity (aggregate root) with `deposit()`, `withdraw()`, `getBalance()`.
- Create a `Money` value object with currency safety.
- Define an `AccountRepository` port.
- Implement an in-memory adapter for the repository.
- Write a `TransferFundsUseCase` that transfers money between two accounts.
- Write unit tests for the domain (no I/O).

**Acceptance criteria:**
- Overdraft is rejected.
- Currency mismatch is rejected.
- Transfer is atomic (both accounts updated or neither).
- Tests run in < 100ms.

### Exercise 2: CQRS Order Dashboard (Intermediate)

Build a read model projection for an order system.

**Requirements:**
- Write model: `Order` aggregate with `addLine()`, `removeLine()`, `submit()`, `cancel()`.
- Read model: `OrderSummary` table with `order_id`, `status`, `line_count`, `total_amount`, `last_updated`.
- Implement an event handler that updates the read model when `OrderSubmitted` or `OrderCancelled` events occur.
- Query the read model for a dashboard endpoint: `GET /orders/summary?status=SUBMITTED`.

**Stretch goals:**
- Add a second read model optimized for search (e.g., full-text on product names).
- Implement eventual consistency with a 500ms simulated delay.

### Exercise 3: Event-Sourced Shopping Cart (Advanced)

Build a shopping cart using event sourcing.

**Requirements:**
- Events: `CartCreated`, `ItemAdded`, `ItemRemoved`, `QuantityChanged`, `CartCheckedOut`.
- Reconstruct cart state by replaying events.
- Implement snapshots every 50 events.
- Implement upcasting: v1 `ItemAdded` has `price` as float; v2 has `price` as `Money` (amount + currency).
- Write a projector that maintains a `cart_summary` read model.

**Acceptance criteria:**
- Cart can be reconstructed from any point in the event stream.
- Snapshot loading + event replay matches full replay.
- v1 events are transparently upcasted to v2 on read.

### Exercise 4: Enforce Architecture with Tests (Intermediate)

Write architecture tests that enforce the dependency rule.

**Requirements (Java/Kotlin with ArchUnit, or Python with import_linter):**
- Domain layer must not import from application, adapter, or framework layers.
- Application layer must not import from adapter or framework layers.
- Adapter.in and adapter.out must not import from each other.
- Run these tests in CI. A violation fails the build.

### Exercise 5: Package Refactor (Beginner)

Take an existing codebase structured by layer (controllers/, services/, repositories/) and refactor it to package-by-feature. Track:
- Number of files that change per feature request (before vs after).
- Whether package-private visibility now protects implementation details.

### Exercise 6: Anti-Corruption Layer (Intermediate)

You depend on a third-party `LegacyInventoryAPI` that returns XML like:

```xml
<item>
  <sku>ABC-123</sku>
  <qty_on_hand>42</qty_on_hand>
  <whs_code>WH-EAST</whs_code>
</item>
```

**Requirements:**
- Define a domain-native `InventoryLevel` value object: `product_id: UUID, available: int, warehouse: Warehouse`.
- Build an ACL adapter that calls the legacy API and translates XML into your domain model.
- The domain layer never sees XML, HTTP, or any legacy naming conventions.
- Write tests for the ACL using a stubbed HTTP client.

**Acceptance criteria:**
- If the legacy API changes its XML schema, only the ACL adapter changes.
- Domain code compiles and tests pass without any legacy API dependency.

### Exercise 7: Compare DI Approaches (Beginner)

Implement the same small service (a `NotificationService` that depends on `EmailSender` and `UserRepository`) three ways:

1. **Manual DI** — wire everything in `main()`.
2. **Reflection-based container** — use Spring (Java), NestJS (TypeScript), or FastAPI `Depends` (Python).
3. **Code-gen container** — use Dagger 2 (Java/Kotlin) or Wire (Go).

Compare:
- Startup time.
- Error experience when a dependency is missing.
- Lines of boilerplate.
- Testability (how easy is it to swap a mock?).

Write a short report (not a separate file — inline comments in the code) documenting your observations.

### Exercise 8: Event Sourcing — Temporal Queries (Advanced)

Extend Exercise 3 with temporal query support.

**Requirements:**
- Implement `get_cart_at(timestamp: datetime) -> Cart` that reconstructs the cart state as it was at a specific point in time.
- Implement `get_cart_diff(t1: datetime, t2: datetime) -> List[Event]` that returns all events between two timestamps.
- Write a "rewind and replay" tool: given a projection bug fix, replay all events from scratch to rebuild the read model.

**Acceptance criteria:**
- Temporal query returns the correct state for any past timestamp.
- Rebuild produces the same read model as the live projection for a known event sequence.
- Performance: replay of 10,000 events completes in < 5 seconds.

---

## 13. Architecture Decision Records (ADRs)

When choosing between architectural styles, document the decision using an ADR. Template:

```
# ADR-001: Use Hexagonal Architecture for Order Service

## Status
Accepted — 2026-05-22

## Context
The order service has complex domain logic (pricing rules, tax calculations,
multi-step workflows) and must integrate with 4 external systems
(payment, inventory, shipping, notifications). We need testability
and swappable adapters.

## Decision
Adopt Hexagonal Architecture with ports and adapters.
Domain layer owns all business logic with zero framework imports.
Adapters implement ports for each external system.

## Consequences
+ Domain logic is fully unit-testable without I/O.
+ Adding a new integration (e.g., new payment provider) requires only
  a new adapter, no domain changes.
- More files and packages than a simple MVC structure.
- Team must learn the port/adapter vocabulary.

## Alternatives Considered
- Layered MVC: simpler but domain logic bleeds into controllers.
- Clean Architecture: functionally equivalent, chose Hexagonal for
  its explicit driving/driven adapter distinction.
```

### When to Write an ADR

Write one whenever:
- Choosing an architectural style for a new service.
- Adopting or dropping a pattern (CQRS, event sourcing, saga).
- Changing a technology (switching from REST to gRPC, Postgres to DynamoDB).
- Making a trade-off that future developers will question ("why not X?").

---

## 14. Architectural Fitness Functions

Automated tests that verify architectural properties remain true as the codebase evolves (Ford, Parsons, Kua — *Building Evolutionary Architectures*).

### 14.1 Dependency Direction

Already shown with ArchUnit in Section 7.3. This is the most common fitness function.

### 14.2 Component Coupling

Measure afferent (incoming) and efferent (outgoing) coupling per package:

```
Instability = Ce / (Ca + Ce)

Ca = afferent coupling  (how many packages depend on me)
Ce = efferent coupling  (how many packages I depend on)

Instability 0 = maximally stable (many dependents, few deps)
Instability 1 = maximally unstable (few dependents, many deps)
```

**Stable Abstractions Principle (SAP):** packages that are *stable* should also be *abstract*. Packages that are *unstable* should be *concrete*.

```
Abstractness = Na / Nc

Na = number of abstract classes/interfaces in the package
Nc = total number of classes in the package
```

**Main Sequence:** plot Abstractness vs Instability. Ideal packages lie on the line from (0,1) to (1,0). Distance from this line is the "pain" metric.

```
Abstractness
     1 ┤ ●  Zone of Uselessness
       │   ╲
       │     ╲  Main Sequence
       │       ╲
       │         ╲
     0 ┤           ●  Zone of Pain
       └─────────────────
       0                1
            Instability
```

### 14.3 Cyclic Dependency Detection

Run in CI. No cycles allowed between packages/modules.

```bash
# Python: import-linter
import-linter --config .importlinter

# Java: jdepend, ArchUnit
# Go: go vet + custom analyzer
```

### 14.4 Layer Size Budget

Set a maximum file count or line count per layer. If the domain layer grows past 2000 lines, the aggregate might need splitting. If the adapter layer is 10x the domain, the domain might be anemic.

---

## 15. Technology Mapping

How these patterns map to real frameworks:

| Pattern | Java/Kotlin | Python | TypeScript | Go |
|---|---|---|---|---|
| Hexagonal | Spring Boot + ArchUnit | FastAPI + abc | NestJS modules | stdlib interfaces |
| DI Container | Spring, Guice, Dagger | dependency-injector, FastAPI Depends | NestJS, tsyringe | Wire, fx |
| CQRS | Axon Framework | Django + separate read DB | MediatR-like handler | custom |
| Event Sourcing | Axon, EventStoreDB client | eventsourcing lib | NestJS CQRS | custom + EventStoreDB |
| Repository | Spring Data JPA | SQLAlchemy | TypeORM, Prisma | sqlc, GORM |
| Specification | custom | custom | custom | custom |
| Architecture Tests | ArchUnit | import-linter, pytestarch | ts-arch | go vet custom |

---

## 16. References

1. Martin, R.C. *Clean Architecture* (Prentice Hall, 2017).
2. Cockburn, A. "Hexagonal Architecture" (2005). https://alistair.cockburn.us/hexagonal-architecture/
3. Palermo, J. "The Onion Architecture" (2008).
4. Evans, E. *Domain-Driven Design: Tackling Complexity in the Heart of Software* (Addison-Wesley, 2003).
5. Vernon, V. *Implementing Domain-Driven Design* (Addison-Wesley, 2013).
6. Young, G. "CQRS Documents" (2010). https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf
7. Fowler, M. "Event Sourcing" (2005). https://martinfowler.com/eaaDev/EventSourcing.html
8. Seemann, M. *Dependency Injection in .NET* (Manning, 2nd edition, 2019).
9. Gamma, E. et al. *Design Patterns* (Addison-Wesley, 1994). — GoF.
10. Parnas, D.L. "On the Criteria To Be Used in Decomposing Systems into Modules" (1972). *Communications of the ACM*.
11. Ford, N., Parsons, R., Kua, P. *Building Evolutionary Architectures* (O'Reilly, 2017).
12. Martin, R.C. "Stable Dependencies Principle" and "Stable Abstractions Principle" — *Agile Software Development* (Prentice Hall, 2002).

---

## 17. Glossary

| Term | Definition |
|---|---|
| **Aggregate** | A cluster of domain objects (entities + value objects) treated as a single unit for data changes. One entity is the root. |
| **Aggregate Root** | The single entity through which all external access to the aggregate occurs. Owns the transactional boundary. |
| **Anti-Corruption Layer (ACL)** | A translation layer that protects one bounded context's domain model from another context's model or from a legacy system. |
| **Bounded Context** | An explicit boundary within which a particular domain model is defined and applicable. Each bounded context has its own ubiquitous language. |
| **Command** | An instruction to perform an action that changes state. Named in the imperative mood (e.g., `SubmitOrder`). Returns void or acknowledgment. |
| **Composition Root** | The single location in the application (typically `main()` or a startup module) where all dependencies are wired together. |
| **CQRS** | Architectural pattern that uses separate models for reading and writing data. |
| **Domain Event** | A record of something that happened in the domain. Named in the past tense (e.g., `OrderSubmitted`). Immutable. |
| **Domain Service** | A stateless service in the domain layer that encapsulates business logic spanning multiple aggregates. |
| **DTO** | Data Transfer Object — a simple data carrier used to cross architectural boundaries without exposing domain internals. |
| **Entity** | A domain object defined by its identity (ID), not its attributes. Two entities with the same attributes but different IDs are different. |
| **Event Sourcing** | A persistence pattern where state is stored as an append-only log of events rather than as current-state snapshots. |
| **Fitness Function** | An automated test that verifies a specific architectural property (e.g., no cyclic dependencies, coupling budget). |
| **Hexagonal Architecture** | Architectural style where the application core communicates with the outside world through ports (interfaces) and adapters (implementations). |
| **IoC (Inversion of Control)** | A design principle where the framework or container controls the flow of execution, calling user-provided components at defined extension points. |
| **Port** | An interface defining a protocol of interaction. Primary ports define what the app offers; secondary ports define what the app needs. |
| **Query** | A request for data that does not change state. Returns a result. |
| **Repository** | A collection-like interface for loading and saving aggregates. Hides persistence details from the domain. |
| **Snapshot** | A serialized copy of an aggregate's current state at a specific event version. Used to avoid replaying the entire event history. |
| **Specification** | A reusable, composable predicate that encapsulates a business rule. |
| **Ubiquitous Language** | A common language shared by developers and domain experts within a bounded context. Code, tests, and conversations use the same terms. |
| **Upcaster** | A component that transforms an older event schema into a newer one, enabling backward-compatible event evolution. |
| **Value Object** | A domain object defined by its attributes, not its identity. Immutable. Two value objects with the same attributes are equal. |

---

## 18. Architecture Style Decision Matrix

Use this matrix to choose the right level of architectural complexity:

```
┌─────────────────────┬───────────────┬──────────────────┬─────────────────────────┐
│ Project Signals      │ Recommended   │ Key Patterns     │ Overhead                │
│                      │ Architecture  │                  │                         │
├─────────────────────┼───────────────┼──────────────────┼─────────────────────────┤
│ < 5 entities         │ MVC + ORM     │ Active Record    │ Minimal                 │
│ No business logic    │               │                  │                         │
│ Single developer     │               │                  │                         │
├─────────────────────┼───────────────┼──────────────────┼─────────────────────────┤
│ 5-20 entities        │ Clean /       │ Repository,      │ Moderate: separate      │
│ Business invariants  │ Hexagonal     │ Domain Model,    │ layers, port/adapter    │
│ Multiple integrations│               │ Use Cases        │ wiring                  │
├─────────────────────┼───────────────┼──────────────────┼─────────────────────────┤
│ 20+ entities         │ Hexagonal +   │ Aggregates,      │ Significant: bounded    │
│ Complex workflows    │ DDD           │ Value Objects,   │ context mapping,        │
│ Domain experts avail │               │ Domain Events,   │ ubiquitous language     │
│                      │               │ Specifications   │                         │
├─────────────────────┼───────────────┼──────────────────┼─────────────────────────┤
│ Heavy read/write     │ Hexagonal +   │ All DDD +        │ High: two data stores,  │
│ asymmetry, audit     │ DDD + CQRS    │ Command/Query    │ projection sync,        │
│ requirements         │ + Event       │ models, Event    │ event versioning,       │
│                      │ Sourcing      │ Store, Snapshots │ eventual consistency    │
└─────────────────────┴───────────────┴──────────────────┴─────────────────────────┘
```

Rule of thumb: start at the simplest level that covers your requirements. Migrate upward when pain signals appear (untestable domain logic, read/write contention, audit gaps, integration sprawl).

---

## 19. Migration Playbook — Layered MVC to Hexagonal

Step-by-step guide for teams migrating an existing layered codebase.

### Phase 1: Introduce the Domain Layer (1-2 sprints)

1. Create a `domain/` package alongside existing `services/`.
2. Move entity classes into `domain/model/`. Remove framework annotations.
3. Push business logic from services *into* the entities. Services become thin orchestrators.
4. Create abstract repository interfaces in `domain/` or `application/port/`.
5. Existing DAO/repository classes now implement those interfaces.
6. Verify: domain package has zero imports from frameworks, ORM, or HTTP.

### Phase 2: Extract Use Cases (1-2 sprints)

1. Create `application/` package.
2. Refactor service methods into dedicated use-case classes (one class per action).
3. Each use case depends only on ports (interfaces), not on concrete adapters.
4. Wire use cases to adapters in the composition root.
5. Write architecture tests (ArchUnit / import-linter) to enforce the dependency rule.
6. Run tests: existing behavior must not change.

### Phase 3: Segregate Adapters (1 sprint)

1. Create `adapter/in/web/` for HTTP controllers.
2. Create `adapter/out/persistence/` for DB access.
3. Create `adapter/out/messaging/` for event publishing.
4. Each adapter implements a port from the application layer.
5. Controllers now call use cases, not services.
6. Remove old `services/`, `repositories/`, `controllers/` packages.

### Phase 4: Verify and Harden

1. Run full test suite. No regressions.
2. Architecture tests pass in CI. Violations fail the build.
3. Measure: coupling metrics (Ca, Ce, Instability) should show improved modularity.
4. Document the architecture decision in an ADR.

### Common Pitfalls During Migration

| Pitfall | Symptom | Fix |
|---|---|---|
| Big bang rewrite | Everything breaks at once | Migrate one bounded context at a time |
| Leaking ORM into domain | `@Entity` on domain classes | Create separate persistence entities in adapter layer |
| Bypassing ports | Adapter directly calls another adapter | Always go through use case → port → adapter |
| Over-abstracting | Port per method | Group related methods into cohesive ports (LoadOrderPort, SaveOrderPort) |
| Ignoring the read path | Only refactor write side | Apply the same port/adapter pattern to query handlers |

---

*End of Module 2.1*
