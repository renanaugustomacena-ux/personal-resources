# Phase 8: SDLC & Process — Syllabus

This phase covers the *process scaffolding* around code: the methodologies, ceremonies, quality gates, and documentation practices that turn individual contributions into shippable, maintainable systems. Where Phases 1–7 build technical depth, Phase 8 builds the engineering discipline that makes that depth sustainable across teams and time. Topics span methodology choice (Waterfall through Kanban), full-spectrum testing strategy (unit through chaos), code-quality enforcement (static analysis, complexity metrics, refactoring catalogs), and documentation as a first-class artifact (Diátaxis, ADRs, C4, diagrams as code). The aim is to make process choices *deliberate and measurable* — not cargo-culted from conference talks or imposed by a heavyweight framework.

## Module 8.1: SDLC Methodologies — Agile, Scrum, Kanban, Waterfall, V-Model
**Goal:** Pick the right cadence and ceremony for the work, not for the brand.
*   SDLC families (plan-driven, iterative, flow-based), Waterfall and V-Model where they remain correct (DO-178C, IEC 62304, ISO 26262), Agile Manifesto values and principles, Scrum (roles, events, artifacts, DoR/DoD, story points and velocity caveats), Kanban (WIP limits, Little's Law, CFD, classes of service), scaling (SAFe, LeSS, the Spotify-model trap), XP engineering practices, DORA metrics (Deployment Frequency, Lead Time, MTTR, CFR), Continuous Discovery vs Continuous Delivery.

## Module 8.2: Testing Strategies — Unit, Integration, E2E, Property, Fuzz, Chaos
**Goal:** Build a multi-layer test strategy with high signal per unit of CI time.
*   Test pyramid and its inverted ice-cream antipattern, FIRST principles, AAA pattern, Meszaros test-double taxonomy, Testcontainers and the mock-vs-real-DB tradeoff, consumer-driven contract tests with Pact, E2E with Playwright/Cypress/Selenium and Page Object Model, property-based testing (Hypothesis, fast-check, QuickCheck, shrinking), mutation testing (Stryker, PIT) as the quality signal beyond coverage, fuzzing (AFL++, libFuzzer, Go native fuzz, OSS-Fuzz), chaos engineering (Chaos Monkey/Mesh, blast radius, Game Days), snapshot testing pitfalls, coverage metrics including MC/DC for safety-critical, performance testing (k6, Locust, Gatling, JMeter), visual regression (Percy, Chromatic).

## Module 8.3: Code Quality — Static Analysis, Linting, Code Review, Refactoring
**Goal:** Make quality enforceable, not aspirational.
*   Static analysis taxonomy (lint vs SAST vs type checking vs taint), per-language tool stacks (Biome/Ruff/staticcheck/clippy/SpotBugs/Roslyn/clang-tidy), SonarQube quality gates with the new-code leak model, complexity metrics (cyclomatic, NPath, cognitive, maintainability index), technical debt accounting (SQALE), code review effectiveness (PR size, conventional comments, async vs sync, pair as live review), Fowler refactoring catalog, Strangler Fig and Mikado Method for legacy migration, code smells, architecture fitness functions with ArchUnit and Dependency Cruiser.

## Module 8.4: Documentation — Technical Writing, ADRs, C4 Model, Diagrams as Code
**Goal:** Treat docs as a versioned product with users and CI.
*   Diátaxis framework (tutorials/how-to/reference/explanation), README essentials, when to write inline comments and when not, ADRs (Nygard and MADR formats, immutability and supersession, adr-tools), C4 Model (Context/Container/Component/Code), diagrams as code (PlantUML, Mermaid, Structurizr DSL, D2), API docs (OpenAPI, AsyncAPI, GraphQL, gRPC), living documentation (Cucumber, doctests, ArchUnit), docs CI (Vale, link checkers, markdownlint), wiki anti-patterns and the docs-as-code remedy.

## Learning Objectives

After Phase 8, the reader should be able to:
*   Choose a development methodology defensibly based on regulatory regime, team size, and feedback latency — not on framework popularity.
*   Design a test pyramid for a given system with explicit budgets per layer and cover the long tail with property/fuzz/mutation testing where it pays.
*   Configure a CI quality gate (lint, type-check, SAST, coverage, mutation, complexity) tuned to the new-code leak model.
*   Run effective code reviews under 400 LOC with a shared comment vocabulary and clear severity escalation.
*   Apply Fowler refactorings and the Strangler Fig pattern to migrate legacy systems incrementally.
*   Write ADRs that future maintainers can act on, and structure documentation by Diátaxis mode.
*   Author C4 and sequence diagrams as code that live in the repo and break the build when they drift.

## Prerequisites

*   **Phase 1 (Foundations)** for vocabulary on systems, networks, and runtimes used in test/CI examples.
*   **Phase 2 (Architecture & Design)** because architectural decisions are the primary subject of ADRs and C4 diagrams.
*   Working familiarity with at least one CI system (GitHub Actions, GitLab CI, or equivalent) — Phase 8 frequently references CI gates.

## Recommended Reading Order

1.  **8.1 Methodologies** first — establishes the *cadence* the rest of the practices live inside.
2.  **8.2 Testing** second — the largest CI investment and the foundation for any quality gate.
3.  **8.3 Code Quality** third — adds enforcement layers on top of the test foundation.
4.  **8.4 Documentation** last — codifies the decisions and architecture produced by the previous three.

Each chapter is self-contained for reference; the order above is for first-pass learning.
