# Phase 2: Software Architecture & Design — Syllabus

> **Last updated:** 2026-05-29

This phase moves from "how the machine works" to "how to structure complex software".

## Module 2.1: Code-Level Architecture & Principles

**Goal:** Write maintainable, testable code within a single service.

| File | Focus |
|---|---|
| [01_Code_Level_Architecture.md](01_Code_Level_Architecture.md) | Clean/Hexagonal architecture, DDD, CQRS, event sourcing, functional core |

*   **SOLID Deep Dive:**
    *   **LSP (Liskov Substitution):** Covariance (Return types) and Contravariance (Argument types). Preconditions and Postconditions.
    *   **DIP (Dependency Inversion):** The boundary between high-level policy and low-level detail.
*   **Architectural Styles:**
    *   **Clean Architecture (Uncle Bob):** The Dependency Rule. Entities vs Use Cases.
    *   **Hexagonal (Ports & Adapters):** Decoupling the "Core" from "Infrastructure" (DB, Web, CLI).
    *   **Functional Core, Imperative Shell:** The functional programming approach to architecture.

## Module 2.2: Distributed System Patterns

**Goal:** Coordinate state across multiple unreliable machines.

| Sub-module | File | Focus |
|---|---|---|
| 2.2 | [02_Distributed_System_Patterns.md](02_Distributed_System_Patterns.md) | Sagas, outbox, circuit breaker, bulkhead, retry patterns |
| 2.2b | [02_b_High_Performance_System_Design.md](02_b_High_Performance_System_Design.md) | Caching, sharding, load balancing, back-pressure, zero-copy |
| 2.2c | [02_c_API_Design_Evolution.md](02_c_API_Design_Evolution.md) | REST/HATEOAS, GraphQL, gRPC, versioning, idempotency |

*   **Data Consistency:**
    *   **Sagas:** Choreography (Events) vs Orchestration (Central Controller).
    *   **The Outbox Pattern:** Guaranteeing "At Least Once" delivery in dual-write scenarios (DB + Message Bus).
    *   **2PC (Two-Phase Commit):** Why it's slow and when to use it (XA Transactions).
*   **Resiliency:**
    *   **Circuit Breaker:** State machine (Closed -> Open -> Half-Open).
    *   **Bulkhead:** Isolating failure domains (Thread pools, Connection pools).
    *   **Retry Patterns:** Exponential Backoff, Jitter, and "Retry Storms".

## Module 2.3: Design Principles — SOLID, DRY, KISS, YAGNI, Demeter

**Goal:** Internalize the principles that prevent accidental complexity.

| File | Focus |
|---|---|
| [03_Design_Principles_SOLID_etc.md](03_Design_Principles_SOLID_etc.md) | SOLID with violation detection, DRY vs wrong abstraction, Law of Demeter |

## Module 2.4: System Design — Scalability, CAP, PACELC

**Goal:** Handle high load and massive data.

| File | Focus |
|---|---|
| [04_System_Design_CAP_PACELC.md](04_System_Design_CAP_PACELC.md) | CAP/PACELC trade-offs, caching strategies, consistent hashing, load balancing |

*   **The CAP Theorem & PACELC:** Trade-offs between Latency and Consistency.
*   **Caching Strategies:** Cache-Aside, Write-Through, Write-Back. Eviction: LRU, LFU, W-TinyLFU.
*   **Sharding & Partitioning:** Consistent Hashing, virtual nodes, hot partitions.
*   **Load Balancing:** L4 vs L7. Round Robin, Least Connections, Power of Two Choices.
