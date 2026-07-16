# Module 8.2: Testing Strategies — Unit, Integration, E2E, Property, Fuzz, Chaos

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
