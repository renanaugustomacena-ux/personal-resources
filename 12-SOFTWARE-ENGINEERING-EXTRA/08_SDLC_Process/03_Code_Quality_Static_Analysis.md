---
corso: "SWE Masterclass"
fase: "8 — SDLC & Process"
modulo: "8.3"
titolo: "Code Quality — Static Analysis, Linting, Code Review, Refactoring"
versione: "SonarQube 10.x · Ruff 0.8+ · Biome 1.x · ESLint 9 · Semgrep"
livello: "Intermediate-Advanced"
prerequisiti:
  - "Ability to read and write code in at least one statically or dynamically typed language"
  - "Basic familiarity with CI/CD pipelines and PR-based workflows"
  - "Understanding of software testing fundamentals (unit tests, coverage reports)"
obiettivi:
  - "Classify static-analysis tool categories (linter, formatter, type checker, SAST, taint analyzer) and select the correct tool chain for a given language"
  - "Configure a SonarQube quality gate using the new-code leak model and interpret its bug, vulnerability, coverage, and duplication verdicts"
  - "Calculate cyclomatic, NPath, and cognitive complexity for a function and apply targeted refactoring to bring each below threshold"
  - "Conduct a structured code review using conventional-comments taxonomy, PR-size heuristics, and a defined severity rubric"
  - "Execute Fowler-catalog refactorings (Extract Function, Replace Conditional with Polymorphism, Strangler Fig) on legacy code with full test coverage preserved"
tag: [code-quality, static-analysis, linting, sonarqube, refactoring, code-review, complexity, technical-debt, sast, semgrep]
---

# Module 8.3: Code Quality — Static Analysis, Linting, Code Review, Refactoring

> **Learning objectives** — After completing this module you will be able to: (1) select and integrate language-specific static-analysis tool chains into CI; (2) configure and interpret SonarQube quality gates on new code; (3) measure and reduce cyclomatic, NPath, and cognitive complexity; (4) run structured code reviews with conventional comments and severity levels; (5) apply catalog refactorings and the Strangler Fig pattern to evolve legacy code safely.

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

---

## Exercises

1. **Tool-chain assembly** — Pick a polyglot project (e.g., Python backend + TypeScript frontend). For each language, configure a formatter, linter, type checker, and SAST scanner from the table in Section 2. Wire all four into a single CI pipeline (GitHub Actions or GitLab CI). Verify that a PR introducing a deliberate type error, a style violation, and an insecure `eval()` call is blocked by the quality gate before merge.

2. **SonarQube quality gate lab** — Install SonarQube Community Edition (Docker). Scan a medium-sized open-source project. Review the default "Sonar way" quality gate results. Then create a custom gate that enforces: 0 new bugs, 0 new vulnerabilities, ≥85% coverage on new code, ≤2% duplication on new code, and cognitive complexity ≤15 per function. Introduce a deliberately complex function and observe the gate fail. Fix the function and re-scan.

3. **Complexity reduction kata** — Find a function in your codebase (or use a provided sample) with cyclomatic complexity >20. Calculate its cyclomatic, NPath, and cognitive complexity by hand. Then apply at least three named Fowler refactorings (e.g., Extract Function, Replace Conditional with Polymorphism, Introduce Parameter Object) to bring cyclomatic complexity below 10. Run the existing test suite after each refactoring to confirm behavior preservation.

4. **Structured code review** — Exchange a 200-LOC PR with a peer. Review it using Conventional Comments (`nit:`, `suggestion:`, `question:`, `blocking:`, `praise:`). Apply the severity rubric from Section 6. Time-box the review to 30 minutes. After the review, the author addresses every `blocking:` comment and responds to each `question:`. Both parties write a brief retrospective on the review quality.

5. **Strangler Fig migration** — Take a monolithic module with at least three tightly coupled responsibilities. Identify one responsibility to extract. Implement the Strangler Fig pattern: (a) create a routing seam (feature flag or gateway), (b) implement the new module behind the seam, (c) gradually route traffic to the new module, (d) verify with integration tests, (e) remove the old code path. Document the dependency graph using the Mikado Method at each step.

---

## Readings and References

- Fowler, M. — *Refactoring: Improving the Design of Existing Code*, 2nd ed. Addison-Wesley, 2018. Online catalog: <https://refactoring.com/catalog/> (retrieved: 2026-05-29)
- McCabe, T. J. — "A Complexity Measure." *IEEE Transactions on Software Engineering*, SE-2(4), 1976.
- Ford, N., Parsons, R. & Kua, P. — *Building Evolutionary Architectures*, 2nd ed. O'Reilly, 2023.
- SonarSource — *SonarQube Documentation*. <https://docs.sonarsource.com/sonarqube-server/latest/> (retrieved: 2026-05-29)
- Semgrep documentation — <https://semgrep.dev/docs/> (retrieved: 2026-05-29)
- Conventional Comments — <https://conventionalcomments.org/> (retrieved: 2026-05-29)
- Ruff documentation — <https://docs.astral.sh/ruff/> (retrieved: 2026-05-29)
- Biome documentation — <https://biomejs.dev/> (retrieved: 2026-05-29)
- CodeQL documentation — <https://codeql.github.com/docs/> (retrieved: 2026-05-29)
- Cohen, J. — *Best Practices for Peer Code Review*. SmartBear, 2006.

---

## Cross-References

| Module | Relevance |
|---|---|
| [01_Methodologies_Agile_Scrum_Kanban.md](01_Methodologies_Agile_Scrum_Kanban.md) | Definition of Done typically includes passing quality gates and static-analysis checks |
| [02_Testing_Strategies.md](02_Testing_Strategies.md) | Coverage metrics gate in SonarQube; mutation testing complements complexity analysis |
| [04_Documentation_ADR_C4.md](04_Documentation_ADR_C4.md) | Architecture Decision Records capture rationale behind refactoring choices and tool-chain selections |
| [05_Git_Branching_Strategies.md](05_Git_Branching_Strategies.md) | PR size heuristics and stacked PRs align with branching strategy; trunk-based dev favors small, reviewed commits |
| [../02_Architecture_Design/](../02_Architecture_Design/) | Architecture fitness functions (ArchUnit, Dependency Cruiser) enforce structural constraints alongside static analysis |
| [../05_DevOps_Cloud_Native/](../05_DevOps_Cloud_Native/) | CI/CD pipeline integrates linters, formatters, SAST, and quality gates as automated stages |

---

## Glossary

| Term | Definition |
|---|---|
| **Linter** | A static-analysis tool that checks source code for style violations, simple bugs, and idiomatic issues without executing it |
| **Formatter** | A tool that rewrites source code layout (indentation, line breaks) to enforce a canonical style; deterministic and non-semantic |
| **SAST** | Static Application Security Testing — analysis that identifies security vulnerabilities (SQLi, XSS, path traversal) in source code without running it |
| **Taint Analysis** | A dataflow technique that tracks untrusted input ("tainted" data) through the program to detect when it reaches a sensitive sink (e.g., `eval`, SQL query) |
| **Cyclomatic Complexity** | McCabe's metric counting linearly independent paths through a function; each `if`/`for`/`case` adds 1 |
| **Cognitive Complexity** | SonarSource's metric that penalizes nesting depth more heavily than branching, aligning better with perceived readability difficulty |
| **NPath Complexity** | The number of acyclic execution paths; multiplicative where cyclomatic is additive, making it a stronger predictor of required test cases |
| **Technical Debt** | The implied cost of future rework caused by choosing a quick, suboptimal solution now; tracked as remediation time (SQALE method) |
| **Quality Gate** | A pass/fail checkpoint in CI (typically SonarQube) that blocks a merge when code does not meet defined thresholds for bugs, vulnerabilities, coverage, or duplication |
| **Conventional Comments** | A specification for code-review comment prefixes (`nit:`, `blocking:`, `suggestion:`, `question:`, `praise:`) that convey intent and severity |
| **Strangler Fig Pattern** | A migration strategy (Fowler, 2004) that incrementally replaces a legacy system by routing new functionality to a new implementation behind a seam |
| **Mikado Method** | A technique for large refactorings that records prerequisite dependencies as a graph, reverting failed attempts and landing safe leaf commits inward |
| **Architecture Fitness Function** | An automated test (Ford/Parsons/Kua) that asserts an architectural property (dependency rules, latency budgets, bundle size) in CI |
| **Code Smell** | A surface indication (Fowler/Beck) that a deeper design problem may exist — e.g., Long Method, Feature Envy, Primitive Obsession |
| **Maintainability Index** | A composite metric combining Halstead Volume, cyclomatic complexity, and LOC into a 0–100 scale; useful as a coarse trend signal |
