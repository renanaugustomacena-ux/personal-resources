# Master Syllabus — Software Engineering Masterclass

> **Language:** English
> **Last updated:** 2026-04-27
> **Pinned versions:** Distributed systems theory references; Kubernetes 1.30+; OAuth 2.1 RFC 9700; OpenTelemetry 1.x; LangChain/LlamaIndex current; OWASP Top 10 2023/2024.

## Course identity

**"Software engineering — temi avanzati / Advanced topics"** — full-stack masterclass covering CS foundations through distributed systems, security, cloud-native, AI/ML integration, and SDLC process. Bridges intermediate engineer to senior/principal level.

**Target competence:** competent → expert (Dreyfus 3 → 5). Capable of designing microservice with Saga + consensus, OTel observability, SBOM-tracked supply chain, secure SDLC.

## Prerequisites

- Solid programming foundation (any language); preferably 2+ professional years.
- Linux/CLI fluent; Git fluent.
- Basic algorithm/data structure knowledge.
- One full-stack project shipped.

## Master objectives

1. Understand OS internals enough to debug at any layer (CPU rings, syscall boundary, kernel scheduler).
2. Design distributed systems with CAP/PACELC awareness, Saga pattern, consensus algorithms.
3. Choose database engines with informed trade-offs (relational vs NoSQL, OLAP vs OLTP).
4. Implement application security applying OWASP Top 10 + threat modeling (STRIDE/DREAD).
5. Operate K8s production clusters with Pod Security, OTel, SLI/SLO/SLA.
6. Integrate AI/ML into apps: HNSW vector DB, prompt injection mitigation, RAG patterns.
7. Establish SDLC: testing pyramid, code review rubrics, incident response, ADR documentation.

## Structure (8 phases, 49+ modules + new)

### Phase 1 — Foundations (5 modules)
- 01.1.1: OS Internals
- 01.1.2: CPU & Kernel Boundary
- 01.1.3: Scheduler Data Structures
- 01.1.4: Memory Management Algorithms
- 01.1.5: File Systems Storage
- 01.2: Networking TCP/IP Deep Dive
- 01.2.a: Modern Protocols HTTP/QUIC
- 01.3: Advanced Data Structures Algorithms
- 01.4: Compilers Interpreters

### Phase 2 — Architecture & Design (6 modules)
- 02.1: Code-Level Architecture
- 02.2: Distributed System Patterns
- 02.2.b: High-Performance System Design
- 02.2.c: API Design Evolution
- 02.3: Design Principles SOLID
- 02.4: System Design CAP/PACELC

### Phase 3 — Database Engineering (4 modules)
- 03.1: Relational Internals
- 03.2: Distributed Consensus
- 03.3: Storage Engines NoSQL
- 03.4: Data Engineering OLAP/OLTP

### Phase 4 — Security & Cryptography (4 modules + 1 NEW)
- 04.1: Application Security
- 04.2: Cryptography Engineering
- 04.3: IAM OAuth JWT
- 04.4: Threat Modeling STRIDE/DREAD
- 04.5 (NEW): Supply Chain SBOM SCA

### Phase 5 — DevOps & Cloud Native (6 modules)
- 05.1: Container Internals
- 05.2: Kubernetes Architecture
- 05.3: Site Reliability Engineering
- 05.4: Infrastructure as Code
- 05.5: Observability SLI/SLO/SLA
- 05.6: Cloud Architecture AWS/Azure/GCP

### Phase 6 — Backend & Frontend (3 modules)
- 06.1: Backend Concurrency
- 06.2: Frontend Engineering
- 06.3: Mobile CrossPlatform

### Phase 7 — AI/ML Integration (3 modules)
- 07.1: AI Engineering Patterns
- 07.2: LLM Integration RAG VectorDB
- 07.3: MLOps Pipelines

### Phase 8 — SDLC Process (4 modules + 4 NEW)
- 08.1: Methodologies Agile/Scrum/Kanban
- 08.2: Testing Strategies
- 08.3: Code Quality Static Analysis
- 08.4: Documentation ADR/C4
- 08.5 (NEW): Git Branching Strategies
- 08.6 (NEW): Code Review Rubrics
- 08.7 (NEW): Incident Response Postmortems
- 08.8 (NEW): Secure SDLC OWASP SAMM

### Phase 9 — Capstone
- `00-CAPSTONE.md`: Saga microservice with consensus, OTel, SBOM, secure SDLC.

## Capstone

Microservice ecosystem (5+ services) with: Saga pattern + Raft consensus for ordering, OTel cross-service tracing, SBOM CycloneDX per service, OWASP SAMM L2 secure SDLC, SLI/SLO defined + multi-burn-rate alerting, CAP/PACELC reasoning documented, ADR for major decisions.

## Pacing

| Mode | Hours/week | Weeks |
|---|---|---|
| Full-time intensive | 40 | 8-10 |
| Part-time evening | 10 | 32-40 |
| Self-paced weekend | 5 | 60+ |

This is a multi-month commitment by design — depth is the point.
