---
corso: "SWE Masterclass"
fase: "8 — SDLC & Process"
modulo: "8.1"
titolo: "SDLC Methodologies — Agile, Scrum, Kanban, Waterfall, V-Model"
versione: "Scrum Guide 2020 · SAFe 6.0 · DORA 2024"
livello: "Intermediate-Advanced"
prerequisiti:
  - "Basic understanding of software project lifecycle phases"
  - "Familiarity with team collaboration and iterative delivery concepts"
  - "Exposure to at least one development project (academic or professional)"
obiettivi:
  - "Compare plan-driven, iterative, and flow-based SDLC models and justify methodology selection for a given project context"
  - "Design a Scrum board with correct roles, events, artifacts, and commitments conforming to the 2020 Scrum Guide"
  - "Configure a Kanban system with WIP limits and measure lead time, cycle time, and throughput using Little's Law"
  - "Evaluate scaling frameworks (SAFe, LeSS, Spotify model) against organizational constraints and recommend one with trade-off rationale"
  - "Instrument a delivery pipeline with the four DORA metrics and interpret the resulting performance cluster"
tag: [sdlc, agile, scrum, kanban, waterfall, v-model, dora, safe, xp, methodology]
---

# Module 8.1: SDLC Methodologies — Agile, Scrum, Kanban, Waterfall, V-Model

> **Learning objectives** — After completing this module you will be able to: (1) select and justify an SDLC methodology based on project risk profile, regulatory constraints, and feedback-latency requirements; (2) run a Scrum sprint end-to-end with proper ceremonies and artifacts; (3) set up and optimize a Kanban board using flow metrics; (4) evaluate scaling frameworks for multi-team environments; (5) measure delivery performance with DORA metrics and propose targeted improvements.

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

---

## Exercises

1. **Methodology selection matrix** — You receive three project briefs: (a) a cardiac-monitor firmware upgrade under IEC 62304, (b) a consumer mobile app exploring product-market fit, (c) an internal IT-support ticket queue. For each, choose a methodology (Waterfall/V-Model, Scrum, Kanban, or hybrid), write a one-page justification covering feedback latency, regulatory burden, and integration cost, and present your rationale in a 10-minute peer review.

2. **Sprint simulation** — Form a 5-person cross-functional team. Create a Product Backlog of 15 user stories for a fictional to-do application. Run a single 1-week sprint end-to-end: Sprint Planning (select a Sprint Goal and forecast items), three Daily Scrums, a Sprint Review (demo the increment to a stakeholder proxy), and a Retrospective. Document velocity, impediments raised, and one process improvement committed for the next sprint.

3. **Kanban board optimization** — Set up a physical or digital Kanban board (Trello, Jira, or sticky notes) with columns Backlog → Ready → In Progress → Review → Done. Process 20 work items over five simulated days. Start without WIP limits, then add a WIP limit of 3 to "In Progress." Measure lead time and cycle time for both phases, plot a Cumulative Flow Diagram, and explain the impact of WIP limits using Little's Law.

4. **DORA metrics baseline** — Given a sample dataset of 50 deployments (timestamps, success/failure, rollback events, commit SHAs), compute: deployment frequency, median lead time for changes, change failure rate, and mean time to restore. Classify the team into the DORA performance cluster (elite, high, medium, low) per the *Accelerate* benchmarks. Propose two concrete improvements to move one tier up.

5. **Scaling framework comparison** — Research SAFe 6.0, LeSS, and the Spotify model. Create a comparison table with columns: governance overhead, backlog ownership, inter-team coordination mechanism, cultural prerequisites, and known failure modes. Present a recommendation for a 120-person engineering org with three product lines and a shared platform team.

---

## Readings and References

- Schwaber, K. & Sutherland, J. — *The 2020 Scrum Guide*. <https://scrumguides.org/scrum-guide.html> (retrieved: 2026-05-29)
- Anderson, D. J. — *Kanban: Successful Evolutionary Change for Your Technology Business*. Blue Hole Press, 2010.
- Forsgren, N., Humble, J. & Kim, G. — *Accelerate: The Science of Lean Software and DevOps*. IT Revolution Press, 2018.
- DORA Team — *Accelerate State of DevOps Report 2024*. <https://dora.dev/research/2024/dora-report/> (retrieved: 2026-05-29)
- Beck, K. — *Extreme Programming Explained: Embrace Change*, 2nd ed. Addison-Wesley, 2004.
- Scaled Agile, Inc. — *SAFe 6.0 Framework*. <https://scaledagileframework.com/> (retrieved: 2026-05-29)
- Kniberg, H. & Ivarsson, A. — *Scaling Agile @ Spotify*. 2012. <https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf> (retrieved: 2026-05-29)
- Royce, W. W. — "Managing the Development of Large Software Systems." *Proceedings of IEEE WESCON*, 1970.
- Agile Alliance — *Agile Manifesto*. <https://agilemanifesto.org/> (retrieved: 2026-05-29)

---

## Cross-References

| Module | Relevance |
|---|---|
| [02_Testing_Strategies.md](02_Testing_Strategies.md) | Testing cadence aligns with sprint/flow cycle; test pyramid shapes DoD |
| [05_Git_Branching_Strategies.md](05_Git_Branching_Strategies.md) | Branch model (trunk-based vs GitFlow) must match methodology cadence |
| [06_Code_Review_Rubrics.md](06_Code_Review_Rubrics.md) | Review turnaround is a flow metric; WIP limits apply to review queues |
| [07_Incident_Response_Postmortems.md](07_Incident_Response_Postmortems.md) | MTTR (DORA) directly feeds incident-response SLO design |
| [../02_Architecture_Design/](../02_Architecture_Design/) | Architecture decisions (monolith vs microservice) constrain team topology and methodology choice |
| [../05_DevOps_Cloud_Native/](../05_DevOps_Cloud_Native/) | CI/CD pipeline maturity determines achievable deployment frequency and lead time |

---

## Glossary

| Term | Definition |
|---|---|
| **Sprint** | A fixed-length iteration (1–4 weeks) in Scrum during which a potentially releasable Increment is created |
| **WIP Limit** | A constraint on the maximum number of work items allowed in a Kanban column at any time |
| **Velocity** | The amount of Product Backlog (in story points) a Scrum team completes per sprint; team-local, never for cross-team comparison |
| **Lead Time** | Elapsed time from a customer request entering the system to its delivery |
| **Cycle Time** | Elapsed time from work actively started to work completed |
| **Throughput** | Number of work items completed per unit of time |
| **Definition of Done (DoD)** | A shared, non-negotiable checklist of quality criteria an Increment must satisfy before it is considered complete |
| **Definition of Ready (DoR)** | Entry criteria a Product Backlog Item must meet before it can be selected into a Sprint |
| **Cumulative Flow Diagram (CFD)** | A stacked-area chart showing item counts per workflow state over time; widening bands signal WIP growth |
| **DORA Metrics** | Four key software-delivery metrics (deployment frequency, lead time for changes, MTTR, change failure rate) from the *Accelerate* research program |
| **Empirical Process Control** | Scrum's foundation — transparency, inspection, and adaptation — as opposed to defined (predictive) process control |
| **Scrumban** | A hybrid approach combining Scrum's cadence with Kanban's flow mechanics and WIP limits |
| **Kaizen** | Continuous incremental improvement; a core principle of Kanban borrowed from the Toyota Production System |
| **Product Goal** | A long-term objective for the Scrum Team that describes a future state of the product; introduced in the 2020 Scrum Guide |
