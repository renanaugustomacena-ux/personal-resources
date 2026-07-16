# Module 8.3: Code Quality — Static Analysis, Linting, Code Review, Refactoring

> **Module 08.3** · **Last updated:** 2026-04-27

## Guiding ideas
1. **SonarQube + linguaggio-specific tools (ruff, eslint, golangci-lint).**
2. **Cyclomatic complexity < 10 per function.**
3. **Code review: structural + behavioral; 30 min max sitting.**
4. **Refactoring: small + tested; never big bang.**


**Date:** 2026-04-22
**Status:** Completed

## 1. Static Analysis Taxonomy

Different tools, often confused, all run *without executing the code*:

| Tool class | What it catches | Example finding |
|---|---|---|
| **Linter** | style, idiom, simple bugs | `==` instead of `===` |
| **Formatter** | layout only | 2 vs 4 spaces |
| **Type checker** | type errors | passing `string` to `int` param |
| **SAST** (Security Static Analysis) | security flaws | SQLi, XSS sinks |
| **Taint analysis** | untrusted data → sensitive sink | request body → `eval` |
| **Dataflow / abstract interpretation** | reachability, null deref | NPE on uncovered branch |

A "lint" finding and a SAST finding are different categories — don't merge them in the same gate.

## 2. Language-Specific Tooling

| Language | Format | Lint | Type | SAST |
|---|---|---|---|---|
| JS/TS | Prettier, **Biome** | ESLint, Biome | tsc | Semgrep, CodeQL |
| Python | Black, **Ruff format** | **Ruff**, Pylint | mypy, **pyright** | Bandit, Semgrep |
| Go | gofmt, goimports | **staticcheck**, golangci-lint | (built-in) | gosec |
| Rust | rustfmt | **clippy** | (built-in) | cargo-audit |
| Java | google-java-format | Checkstyle, **SpotBugs**, SonarLint | (javac) | SpotBugs-FindSecBugs |
| C# / .NET | dotnet format | **Roslyn analyzers**, StyleCop | (roslyn) | Security Code Scan |
| C++ | clang-format | **clang-tidy**, cppcheck | (compiler) | clang-analyzer |

Trend: **Ruff** and **Biome** (Rust-implemented) replacing the old Python/JS tool stacks for 10–100× speedups.

## 3. SonarQube Quality Gates

*   Aggregates lint + complexity + coverage + duplication + security.
*   **Quality gate** = pass/fail boolean attached to PR. Default "Sonar way" gate: 0 new bugs, 0 new vulnerabilities, ≥80% coverage on new code, ≤3% duplication on new code.
*   **Don't gate on legacy code metrics** — use "new code" leak model. Prevents the gate from being permanently red and ignored.

## 4. Complexity Metrics

### 4.1 Cyclomatic Complexity (McCabe, 1976)
Number of linearly independent paths through code = (edges − nodes + 2). Each `if`/`for`/`case` adds 1.
*   ≤10: simple.
*   11–20: moderate.
*   21–50: complex, refactor candidate.
*   >50: untestable.

### 4.2 NPath Complexity
Number of *acyclic execution paths*. Multiplicative (where cyclomatic is additive). Two nested `if`s = NPath 4, cyclomatic 3. Better predictor of test count needed.

### 4.3 Cognitive Complexity (Sonar)
Penalizes nesting more than branching. Aligns better with subjective "hard to read." `if (a) { if (b) { if (c) }}` scores much higher than three flat `if`s.

### 4.4 Maintainability Index
`171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)` — composite of Halstead Volume, cyclomatic complexity, LOC. 0–100 scale. Coarse but useful trend signal.

## 5. Technical Debt

*   **SQALE method** (Software Quality Assessment based on Lifecycle Expectations): assigns *remediation cost* (in time) to each issue.
*   **Debt ratio** = remediation cost / dev cost to rebuild from scratch. Sonar's "A–E" rating maps to bands (A: ≤5%, E: >50%).
*   Treat debt like financial debt: track principal, pay interest in slowdowns. Bankruptcy = rewrite.

## 6. Code Review Patterns

### 6.1 PR Size
SmartBear study (Cohen 2006) and Google internal data converge: **defect detection drops sharply above ~400 LOC** per review. Reviewer fatigue is non-linear.
*   Target: <200 LOC, <60 min review.
*   Big PR? Split by commit, review commit-by-commit, or use *stacked PRs*.

### 6.2 Review Checklist (excerpt)
*   Does it do what the description says?
*   Are tests present and meaningful?
*   Error paths handled?
*   Inputs validated at boundary?
*   Logging without secrets/PII?
*   Backwards-compatible? Migration path?
*   Reverts cleanly?

### 6.3 Comment Conventions
*   `nit:` — taste, not blocking.
*   `suggestion:` — non-blocking improvement.
*   `question:` — clarification, may or may not block.
*   `blocking:` — must address before merge.
*   `praise:` — explicit positive — yes, write these.

Conventional Comments spec formalizes this.

### 6.4 Async vs Sync Review
*   **Async (PR comments):** scales, leaves searchable record, default for distributed teams.
*   **Sync (pair, review meeting):** needed for architectural changes, security-sensitive code, junior onboarding.

### 6.5 Pair Programming as Live Review
Continuous review at typing speed. Eliminates the PR queue but doubles human cost. Best for risky code, tricky algorithms, knowledge transfer.

## 7. Refactoring Catalog (Fowler, *Refactoring* 2nd ed.)

Mechanical, behavior-preserving transformations. Names matter — they're the shared vocabulary.

| Refactoring | Trigger |
|---|---|
| **Extract Function** | Comment explaining a block → that block is a function |
| **Inline Function** | Body more obvious than the name |
| **Rename Variable** | Name lies or hides intent |
| **Move Function** | Function uses another module's data more than its own |
| **Replace Conditional with Polymorphism** | Switch on type tag |
| **Replace Loop with Pipeline** | Loop is filter-map-reduce in disguise |
| **Introduce Parameter Object** | Same 3+ params travel together |
| **Replace Magic Literal** | Literal with meaning beyond its value |

## 8. Strangler Fig Pattern (Fowler, 2004)

Migrate legacy by routing new functionality to a new system, gradually peeling features off the old one. Old system shrinks until it can be removed. Inspired by strangler fig vines that grow on host trees.

*   Beats big-bang rewrite (Joel Spolsky's "single worst strategic mistake").
*   Requires a routing seam — gateway, facade, or feature flag.

## 9. Big Refactor vs Mikado Method

*   **Big refactor:** stop feature work, rewrite. Politically toxic, often abandoned.
*   **Mikado Method:** want goal G; try it; it breaks; record prerequisites; revert; tackle prereqs. Forms a dependency graph. Land safe, small commits along the leaves inward.

## 10. Code Smells (Fowler/Beck)

*   **Duplicated Code** — most common smell.
*   **Long Method** — split.
*   **Large Class** — extract class.
*   **Long Parameter List** — introduce parameter object.
*   **Feature Envy** — method uses another class's data more than its own.
*   **Shotgun Surgery** — one change requires edits in many places (low cohesion).
*   **Divergent Change** — one class changes for many reasons (mixed concerns).
*   **Primitive Obsession** — `string` for everything; prefer value types (`EmailAddress`, `Money`).
*   **Data Clumps** — same fields appearing together.

## 11. Architecture Fitness Functions

Coined by Ford/Parsons/Kua (*Building Evolutionary Architectures*). Automated tests for **architectural** properties, not behavior:
*   Layer X must not depend on layer Y.
*   No cycle in module graph.
*   p99 latency stays under N ms.
*   Bundle stays under N kb.

Tools:
*   **ArchUnit** (Java) — assertions in JUnit syntax: `noClasses().that().resideIn("..service..").should().dependOn("..controller..")`.
*   **Dependency Cruiser** (JS/TS) — module dependency rules in config.
*   **Modulith** (Spring) — package-relative module verification.
*   **Konsist** (Kotlin), **NetArchTest** (.NET).

Run them in CI alongside unit tests. Architecture decay becomes a build failure, not a six-month review finding.
