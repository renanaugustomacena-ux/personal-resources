---
corso: "SWE Masterclass"
fase: "8 — SDLC & Process"
modulo: "8.2"
titolo: "Testing Strategies — Unit, Integration, E2E, Property, Fuzz, Chaos"
versione: "Playwright 1.x · Hypothesis 6.x · fast-check 3.x · AFL++ · k6 · Chaos Mesh"
livello: "Intermediate-Advanced"
prerequisiti:
  - "Comfortable writing and running tests in at least one language (pytest, Jest, JUnit, Go testing)"
  - "Familiarity with CI/CD pipeline concepts"
  - "Basic understanding of software architecture boundaries (modules, services, APIs)"
obiettivi:
  - "Design a multi-layer test strategy (unit, integration, E2E) calibrated to a project's failure modes and architecture shape"
  - "Implement property-based tests that express algebraic invariants and leverage shrinking to produce minimal failing examples"
  - "Set up a coverage-guided fuzzer (AFL++ or cargo-fuzz) against a parser or decoder and triage the resulting crash corpus"
  - "Plan and execute a chaos engineering experiment with a defined steady-state hypothesis, blast-radius cap, and rollback trigger"
  - "Evaluate test quality beyond line coverage using mutation testing scores and identify surviving mutants"
tag: [testing, unit-test, integration-test, e2e, property-based, fuzzing, chaos-engineering, mutation-testing, coverage, tdd]
---

# Module 8.2: Testing Strategies — Unit, Integration, E2E, Property, Fuzz, Chaos

> **Learning objectives** — After completing this module you will be able to: (1) architect a test pyramid (or trophy) proportioned to your project's risk profile; (2) write property-based tests with shrinking in Hypothesis or fast-check; (3) configure and interpret coverage-guided fuzzing sessions; (4) design chaos experiments with steady-state hypotheses and blast-radius controls; (5) measure test effectiveness through mutation scores rather than line coverage alone.

> **Module 08.2** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Test pyramid: many unit, few integration, fewer E2E.**
2. **Property-based testing (Hypothesis Python, fast-check JS).**
3. **Fuzzing: AFL++, libFuzzer for C/C++; cargo-fuzz Rust.**
4. **Chaos engineering: Netflix Chaos Monkey paradigm.**


**Date:** 2026-04-22
**Status:** Completed

## 1. The Test Pyramid

Mike Cohn, *Succeeding with Agile*. Three tiers, base = many, top = few:

*   **Base — Unit:** fast, isolated, deterministic. Milliseconds. Thousands per project.
*   **Middle — Integration:** real collaborators (DB, queue, HTTP). Seconds. Hundreds.
*   **Top — E2E:** full system through UI/API. Tens of seconds to minutes. Tens.

### 1.1 Inverted Ice-Cream Cone (antipattern)
Lots of E2E, almost no unit tests. Symptoms: long CI, flakiness, hours to localize failure cause. Common in QA-team-led shops where dev doesn't own tests.

### 1.2 Honeycomb / Trophy Variants
Modern microservice / TS-frontend takes argue for *integration-heavy* shapes (Kent C. Dodds Testing Trophy). Reasoning: most bugs live at component boundaries. Both shapes are valid — pick by failure mode you keep seeing.

## 2. Unit Tests

### 2.1 FIRST Principles (Robert Martin)
*   **Fast** — millisecond budget.
*   **Isolated/Independent** — order doesn't matter.
*   **Repeatable** — same result every run, anywhere.
*   **Self-validating** — pass/fail, no manual diff.
*   **Timely** — written with (TDD) or before (test-first) the code.

### 2.2 AAA Pattern
```
// Arrange — set up state
// Act     — invoke the unit under test
// Assert  — verify outcome
```

### 2.3 Test Doubles (Meszaros taxonomy)
*   **Dummy** — passed but never used (fills a parameter).
*   **Stub** — returns canned answers.
*   **Spy** — stub + records calls for later assertion.
*   **Mock** — pre-programmed with expectations; *fails* if not called as expected.
*   **Fake** — working implementation, unfit for prod (in-memory DB, fake clock).

Mocks couple tests to call structure → refactor-fragile. Prefer fakes/stubs.

## 3. Integration Tests

### 3.1 Testcontainers
Spin up real Postgres/Redis/Kafka in Docker per-test or per-suite. JVM, Go, .NET, Python, Node bindings. Beats H2/SQLite-as-Postgres-substitute, which lies about behavior (different SQL dialect, different lock semantics).

### 3.2 Real DB vs Mocked DB
*   Mocked: fast, but the mock encodes assumptions about the DB that drift from reality. Classic burn: ORM lazy-loading mocked away → N+1 explodes only in prod.
*   Real (testcontainer): catches schema drift, query plan regressions, transaction isolation bugs.
*   **Heuristic:** mock the network you don't own; use the real thing for storage you do.

### 3.3 Contract Tests
*   **Pact** (consumer-driven contracts): consumer writes expectations → publishes contract → provider verifies in its CI. Decouples microservice releases.
*   Beats schema-only tools (OpenAPI diff) because it captures *semantic* expectations.

## 4. E2E Tests

### 4.1 Tools
*   **Playwright** — multi-browser, auto-waits, trace viewer. Current best-in-class.
*   **Cypress** — DX-focused, JS-only, single-browser-context limits.
*   **Selenium** — historical baseline, still required for niche browser combos.

### 4.2 Page Object Model
Encapsulate page structure behind a class. Test code uses domain verbs (`loginPage.submitWith(user, pwd)`), not selectors. Selector changes touch one file.

### 4.3 Determinism
*   **Never sleep** — wait for state (`expect(locator).toBeVisible()`).
*   Seed DB to a known state per test.
*   Freeze the clock.
*   Stub third-party APIs at the network layer (MSW, WireMock).

## 5. Property-Based Testing

Generate inputs, assert *properties* hold ∀ input.

*   **QuickCheck** (Haskell, Claessen & Hughes 2000) — originator.
*   **Hypothesis** (Python), **fast-check** (JS/TS), **PropEr** (Erlang), **proptest** (Rust).
*   **Shrinking:** when a failing input is found, the framework reduces it to the *minimal* case (e.g., 1000-item list → 2-item).
*   Catches edge cases example-based tests miss: empty, max-int, unicode, negative-zero.

Example properties:
*   `decode(encode(x)) == x` (round-trip)
*   `sort(sort(x)) == sort(x)` (idempotence)
*   `len(merge(a, b)) == len(a) + len(b)` (algebraic)

## 6. Mutation Testing

Tools deliberately mutate the source (`==` → `!=`, `+` → `-`, delete a return) and re-run tests. If tests still pass → the mutant *survived* → coverage is illusory.

*   **Stryker** (JS, .NET, Scala), **PIT** (Java), **mutmut** (Python), **cargo-mutants** (Rust).
*   **Mutation score** = killed mutants / total. Targets 60–80% are realistic; 100% impractical.
*   Far better quality signal than line coverage.

## 7. Fuzzing

Random/structured input generation against parsers, decoders, FFI boundaries.

*   **AFL / AFL++** — coverage-guided, instrumented binary.
*   **libFuzzer** — in-process, LLVM-integrated.
*   **Go native fuzzing** (`go test -fuzz`) — first-class since Go 1.18.
*   **cargo-fuzz** (Rust), **Jazzer** (JVM), **Atheris** (Python).
*   **OSS-Fuzz** — Google runs continuous fuzzing for open-source projects free of charge; has found tens of thousands of bugs.

## 8. Chaos Engineering

Production-failure rehearsal. Principles (principlesofchaos.org):
1.  Define **steady state** (e.g., 99% success rate).
2.  Hypothesize it holds under failure.
3.  Inject real-world variables (kill node, latency, disk fill).
4.  Try to disprove the hypothesis.

*   **Chaos Monkey** (Netflix) — random instance termination.
*   **Chaos Mesh / LitmusChaos** — Kubernetes-native fault injection.
*   **Gremlin** — commercial.
*   **Blast radius:** cap experiments to one region, one service, off-peak.
*   **Game Days:** scheduled, multi-team chaos exercises with on-call participating.

## 9. Snapshot Testing

Serialize output, diff against committed baseline.
*   **Useful for:** large structured outputs (rendered HTML, API responses, codegen).
*   **Brittle when:** every commit churns the snapshot — signals tests assert too much. Limit snapshot scope.

## 10. Coverage Metrics

| Metric | What it measures |
|---|---|
| Line | executed lines / total |
| Branch | executed branches / total (better) |
| Path | executed paths / total (combinatorial) |
| **MC/DC** | each condition independently affects outcome |

MC/DC (Modified Condition/Decision Coverage) is mandatory for **DO-178C Level A** avionics. Overkill elsewhere. Coverage is necessary, not sufficient — combine with mutation testing.

## 11. Performance / Load Testing

*   **k6** (Go core, JS scripting) — modern default.
*   **Locust** (Python) — pythonic load model.
*   **Gatling** (Scala/Kotlin DSL) — heavyweight, great reports.
*   **JMeter** — venerable, GUI-driven, still common in enterprise.
*   Test at and **beyond** expected peak. Measure p50/p95/p99/p999, not averages.

## 12. Visual Regression

*   **Percy**, **Chromatic** (for Storybook), **BackstopJS**.
*   Pixel-diff renders across browsers/breakpoints.
*   Pair with Playwright screenshots in CI; fail PR on visual change without explicit baseline approval.

---

## Exercises

1. **Test pyramid audit** — Take an existing open-source project (or your own codebase). Categorize every test file as unit, integration, or E2E. Draw the resulting shape (pyramid, trophy, or ice-cream cone). Identify the two riskiest untested boundaries and write integration tests for them using Testcontainers or an equivalent.

2. **Property-based round-trip** — Choose a serialization pair in your stack (e.g., JSON encode/decode, protobuf serialize/deserialize, URL encode/decode). Write a property-based test using Hypothesis (Python) or fast-check (JS/TS) asserting the round-trip invariant `decode(encode(x)) == x`. Run at least 1,000 examples, observe shrinking on any failure, and document three edge cases the framework discovered that you would not have written by hand.

3. **Mutation testing campaign** — Install Stryker (JS/.NET), PIT (Java), mutmut (Python), or cargo-mutants (Rust) on a project with ≥70% line coverage. Run a full mutation campaign. Identify the five most dangerous surviving mutants (mutations that should have been caught but were not). Write tests to kill them and report the before/after mutation score.

4. **Fuzz a parser** — Select a small parser (JSON, CSV, TOML, or a custom format). Instrument it with AFL++, libFuzzer, Go native fuzzing (`go test -fuzz`), or cargo-fuzz. Run the fuzzer for at least 30 minutes. Triage the crash corpus: classify each unique crash by root cause (buffer overread, panic on malformed input, infinite loop). Fix at least two crashes and re-run to confirm they no longer reproduce.

5. **Chaos experiment design** — For a multi-service system (real or simulated with Docker Compose), define a steady-state hypothesis (e.g., "p99 latency stays below 500 ms when one replica of service-B is killed"). Use Chaos Mesh, LitmusChaos, or `docker stop` to inject the fault. Record metrics before, during, and after. Write a one-page post-experiment report with findings and remediation actions.

---

## Readings and References

- Cohn, M. — *Succeeding with Agile: Software Development Using Scrum*. Addison-Wesley, 2009. (Originator of the Test Pyramid.)
- Meszaros, G. — *xUnit Test Patterns: Refactoring Test Code*. Addison-Wesley, 2007. (Definitive test-doubles taxonomy.)
- Claessen, K. & Hughes, J. — "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs." *ICFP 2000*.
- Hypothesis documentation — <https://hypothesis.readthedocs.io/> (retrieved: 2026-05-29)
- Playwright documentation — <https://playwright.dev/> (retrieved: 2026-05-29)
- Principles of Chaos Engineering — <https://principlesofchaos.org/> (retrieved: 2026-05-29)
- Google OSS-Fuzz — <https://github.com/google/oss-fuzz> (retrieved: 2026-05-29)
- Stryker Mutator — <https://stryker-mutator.io/> (retrieved: 2026-05-29)
- Pact contract testing — <https://docs.pact.io/> (retrieved: 2026-05-29)
- k6 load testing — <https://k6.io/docs/> (retrieved: 2026-05-29)

---

## Cross-References

| Module | Relevance |
|---|---|
| [01_Methodologies_Agile_Scrum_Kanban.md](01_Methodologies_Agile_Scrum_Kanban.md) | Test cadence maps to sprint length; Definition of Done includes test gates |
| [03_Code_Quality_Static_Analysis.md](03_Code_Quality_Static_Analysis.md) | Coverage metrics feed SonarQube quality gates; mutation score complements line coverage |
| [06_Code_Review_Rubrics.md](06_Code_Review_Rubrics.md) | Review checklists verify test presence and meaningfulness before merge |
| [08_Secure_SDLC_OWASP_SAMM.md](08_Secure_SDLC_OWASP_SAMM.md) | Fuzzing and SAST are OWASP SAMM verification activities; chaos tests validate security-related resilience |
| [../02_Architecture_Design/](../02_Architecture_Design/) | Architecture boundaries define integration-test scope; contract tests enforce service interfaces |
| [../05_DevOps_Cloud_Native/](../05_DevOps_Cloud_Native/) | CI/CD pipelines orchestrate test tiers; chaos experiments require observability infrastructure |

---

## Glossary

| Term | Definition |
|---|---|
| **Test Pyramid** | A heuristic (Cohn) prescribing many fast unit tests at the base, fewer integration tests in the middle, and few slow E2E tests at the top |
| **Test Double** | A generic term (Meszaros) for any object that substitutes a production dependency in a test — includes dummies, stubs, spies, mocks, and fakes |
| **Shrinking** | The process by which a property-based testing framework reduces a failing input to the smallest example that still triggers the failure |
| **Mutation Score** | The percentage of source-code mutants killed by the test suite; a stronger quality signal than line coverage |
| **Coverage-Guided Fuzzing** | Fuzzing that uses code-coverage instrumentation to steer input generation toward unexplored branches |
| **Steady-State Hypothesis** | In chaos engineering, the measurable system behavior (e.g., error rate < 1%) expected to hold even under injected failure |
| **Blast Radius** | The scope of impact a chaos experiment is permitted to have — limited by region, service, or traffic percentage |
| **Consumer-Driven Contract** | A testing pattern (Pact) where the API consumer publishes expected interactions and the provider verifies them independently |
| **Flaky Test** | A test that non-deterministically passes or fails without code changes; typically caused by timing, ordering, or shared state |
| **Page Object Model** | An E2E testing pattern that encapsulates page structure behind a class, isolating selector changes from test logic |
| **MC/DC** | Modified Condition/Decision Coverage — each Boolean sub-condition must independently affect the decision outcome; mandatory in DO-178C Level A |
| **Testcontainers** | A library that spins up real infrastructure (databases, message brokers) in Docker containers for integration tests |
| **Game Day** | A scheduled, multi-team chaos exercise where on-call engineers participate and incident-response procedures are rehearsed |
| **Visual Regression Test** | An automated comparison of rendered UI screenshots against committed baselines to detect unintended visual changes |
