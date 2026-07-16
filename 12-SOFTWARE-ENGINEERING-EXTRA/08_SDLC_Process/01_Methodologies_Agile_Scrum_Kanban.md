# Module 8.1: SDLC Methodologies — Agile, Scrum, Kanban, Waterfall, V-Model

> **Module 08.1** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Scrum: sprints; Kanban: continuous flow.**
2. **Waterfall valid for fixed-scope (regulated industry).**
3. **Hybrid common in practice.**
4. **Agile != good. Bad agile worse than honest waterfall.**


**Date:** 2026-04-22
**Status:** Completed

## 1. SDLC Overview

The Software Development Life Cycle is the meta-process around code: requirements, design, implementation, verification, deployment, maintenance. Methodology = the *cadence and ceremony* layered on top. Choice is driven by feedback latency, regulatory burden, and integration cost — never by fashion.

*   **Plan-driven (Waterfall, V-Model):** Cheap change early, expensive late.
*   **Iterative (Scrum, XP):** Fixed-length feedback loops, embraces late change.
*   **Flow-based (Kanban):** Continuous pull, no iterations, optimizes throughput.

## 2. Waterfall

*   **Phases:** Requirements → Design → Implementation → Verification → Maintenance. Each gate signed off before next starts.
*   **Origin:** Royce 1970 — paper that *introduced* it as a strawman to argue against, but industry adopted the strawman.
*   **Where it is correct:**
    *   Safety-critical (DO-178C avionics, IEC 62304 medical, EN 50128 rail).
    *   Hardware-bound projects with long fab cycles.
    *   Fixed-price gov contracts where requirements are legally frozen.
*   **Failure mode:** Late discovery of misunderstood requirements; integration phase uncovers everything at once.

## 3. V-Model

*   **Shape:** Left arm = decomposition (Requirements → System Design → Architecture → Module Design → Code). Right arm = integration (Unit Test → Integration Test → System Test → Acceptance Test).
*   **Pairing:** Each left node has a *verification counterpart* on the right at the same level. Module Design ↔ Unit Tests. Requirements ↔ Acceptance Tests. Forces test planning to start with the artifact it verifies.
*   Used heavily in automotive (ISO 26262 ASIL workflows) and defense.

## 4. Agile Manifesto (2001)

Four values (left over right, not "instead of"):
1.  Individuals and interactions over processes and tools
2.  Working software over comprehensive documentation
3.  Customer collaboration over contract negotiation
4.  Responding to change over following a plan

Twelve principles — operationalize the values. Notable ones:
*   Highest priority: early and continuous delivery of valuable software.
*   Welcome changing requirements, even late.
*   Deliver working software *frequently* (weeks, not months).
*   Sustainable pace — constant indefinitely.
*   Continuous attention to technical excellence and good design enhances agility.

## 5. Scrum

Empirical process control: transparency, inspection, adaptation.

### 5.1 Roles
*   **Product Owner:** Owns the *what* and *why*. Single throat to choke for backlog priority. Maximizes product value.
*   **Scrum Master:** Servant-leader. Removes impediments. Owns the *process*, not the people.
*   **Developers:** Self-organizing team that builds the increment. Cross-functional.

### 5.2 Events (timeboxed)
*   **Sprint** — 1–4 weeks. Container for the others.
*   **Sprint Planning** (≤8h for 4-week sprint): What can be done? How?
*   **Daily Scrum** (15 min): Sync on Sprint Goal. Not a status report to the SM.
*   **Sprint Review** (≤4h): Demo to stakeholders, inspect increment, adapt backlog.
*   **Retrospective** (≤3h): Inspect process, adapt next sprint. Skipping this kills the loop.

### 5.3 Artifacts and Commitments
| Artifact | Commitment |
|---|---|
| Product Backlog | Product Goal |
| Sprint Backlog | Sprint Goal |
| Increment | Definition of Done |

*   **Definition of Ready (DoR):** Story has acceptance criteria, dependencies resolved, estimable. Pre-sprint gate.
*   **Definition of Done (DoD):** Code merged, tests passing, deployed to staging, docs updated. Non-negotiable quality bar.
*   **Story points:** Relative effort (Fibonacci). Velocity = points completed/sprint. **Never** compare velocity across teams — points are team-local.

## 6. Kanban

Pull system from Toyota TPS, adapted to knowledge work by David Anderson.

*   **Visualize the workflow:** columns = states (Backlog, In Progress, Review, Done).
*   **Limit Work In Progress (WIP):** per-column caps. Forces finishing before starting.
*   **Manage flow:** measure and improve.
*   **Make policies explicit.**
*   **Improve collaboratively** (kaizen).

### 6.1 Flow Metrics
*   **Lead Time:** customer request → delivery.
*   **Cycle Time:** work started → work done.
*   **Throughput:** items completed per unit time.
*   **Little's Law:** `L = λ × W` — Avg WIP = arrival rate × avg cycle time. Reducing WIP cuts cycle time *linearly* if throughput holds.
*   **Cumulative Flow Diagram (CFD):** stacked-area of states over time. Widening band = WIP growing = trouble.

### 6.2 Classes of Service
*   **Expedite** — drop everything (prod outage).
*   **Fixed-date** — regulatory deadline.
*   **Standard** — normal flow.
*   **Intangible** — tech debt, refactor.

Each class gets its own WIP slot and SLA.

## 7. Scaling Frameworks

*   **SAFe (Scaled Agile Framework):** Hierarchical (Team → Program → Solution → Portfolio). Heavyweight, popular in enterprise. Critics call it "agile theater."
*   **LeSS (Large-Scale Scrum):** Multiple teams, *one* product backlog, *one* PO. Stays close to Scrum.
*   **Spotify Model (squads/tribes/chapters/guilds):** Often cargo-culted. **Spotify itself abandoned it.** It was a snapshot, never a framework.

## 8. Extreme Programming (XP)

Engineering practices Scrum is silent on:
*   **Pair programming** — two devs, one keyboard.
*   **TDD** — red/green/refactor.
*   **Continuous Integration** — merge to trunk daily, automated build.
*   **Refactoring** — relentless small improvements.
*   **Collective code ownership.**
*   **YAGNI, simple design.**

## 9. DORA Metrics (Accelerate, Forsgren et al.)

Four key metrics; elite teams measurably outperform on all four:
*   **Deployment Frequency** — how often code reaches prod.
*   **Lead Time for Changes** — commit → prod.
*   **Mean Time to Restore (MTTR)** — outage → recovery.
*   **Change Failure Rate** — % of deploys causing incident/rollback.

## 10. Continuous Discovery vs Delivery

*   **Continuous Delivery:** every commit is releasable.
*   **Continuous Discovery (Teresa Torres):** weekly customer touchpoints feeding opportunity-solution tree. Prevents shipping fast in the wrong direction.

## 11. When to Use What

| Context | Methodology |
|---|---|
| Avionics, medical device firmware | V-Model + Waterfall |
| New product, unstable requirements | Scrum |
| Ops/support team, mixed-priority queue | Kanban |
| Mature product, optimization phase | Kanban or Scrumban |
| Multi-team feature, single product | LeSS |
| Enterprise with PMO mandate | SAFe (reluctantly) |

The methodology serves the work, not the reverse.
