---
corso: "SWE Masterclass"
fase: "2 — Architecture & Design"
modulo: "2.3"
titolo: "Design Principles — SOLID, DRY, KISS, YAGNI, Demeter"
versione: "2026-05 (post-Clean Code era)"
livello: "Advanced"
prerequisiti:
  - "Proficiency in at least one OOP language (Java, C#, Python, TypeScript, Kotlin)"
  - "Familiarity with class hierarchies, interfaces, and polymorphism"
  - "Experience maintaining a production codebase (>6 months)"
  - "Basic understanding of coupling and cohesion concepts"
obiettivi:
  - "Apply each SOLID principle to refactor a violating codebase and verify correctness with tests"
  - "Distinguish knowledge duplication from code-shape duplication when evaluating DRY violations"
  - "Use YAGNI as a decision filter to prevent speculative abstractions during design reviews"
  - "Identify and eliminate Law of Demeter violations using Tell-Don't-Ask refactoring"
  - "Evaluate trade-offs between composition and inheritance for a given design problem"
tag: [solid, srp, ocp, lsp, isp, dip, dry, kiss, yagni, law-of-demeter, composition-over-inheritance, cohesion, coupling, design-principles]
---

# Module 2.3: Design Principles — SOLID, DRY, KISS, YAGNI, Demeter

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Recognize violations of each SOLID principle in production code and apply targeted refactorings
> - Apply the Rule of Three to avoid premature abstraction while honoring DRY at the knowledge level
> - Use KISS and YAGNI as complementary filters to reject unnecessary complexity before it enters the codebase
> - Refactor train-wreck chains into Law-of-Demeter-compliant designs using Tell-Don't-Ask
> - Measure cohesion and coupling at the module level and relate improvements back to specific principles

> **Module 02.3** · **Last updated:** 2026-04-27

## Guiding ideas
1. **SOLID: 5 principles guide OOP design.**
2. **DRY (Don't Repeat Yourself) ≠ over-abstract.**
3. **YAGNI (You Aren't Gonna Need It) > speculative generality.**
4. **Demeter (Law of Demeter): talk to friends only.**


**Date:** 2026-04-22
**Status:** Completed

## 1. SOLID

Five OOD principles distilled by Robert Martin from Bertrand Meyer, Barbara Liskov, and Parnas.

### 1.1 S — Single Responsibility Principle
*A module should have one, and only one, reason to change.* "Reason to change" = one *actor* (a stakeholder group).

```text
// VIOLATION: serializer + persistence + reporting in one class
class Employee:
    calculatePay()        // CFO
    save()                // CTO/DBA
    reportHours()         // COO

// FIX: split by actor
class PayCalculator { calculatePay(emp) }
class EmployeeRepository { save(emp) }
class HoursReporter { reportHours(emp) }
```

### 1.2 O — Open/Closed Principle
*Open for extension, closed for modification.* Add behavior without editing existing tested code. Mechanism: polymorphism + dependency inversion.

```text
// VIOLATION: switch over type
function area(shape):
    if shape.kind == "circle": return π * shape.r^2
    if shape.kind == "square": return shape.s * shape.s
    // adding Triangle requires editing this function

// FIX
interface Shape { area(): float }
class Circle  implements Shape { area() = π * r^2 }
class Square  implements Shape { area() = s * s }
// new Triangle: add a class, do not touch existing code
```

### 1.3 L — Liskov Substitution Principle
*Subtypes must be substitutable for their base types* without altering correctness. Preconditions cannot be strengthened, postconditions cannot be weakened, invariants must hold.

*Classic violation:* `Square extends Rectangle`. Setting width independently of height breaks rectangle invariants. Fix: model `Square` and `Rectangle` as separate types or as immutable values.

### 1.4 I — Interface Segregation Principle
*Clients should not depend on methods they do not use.* Fat interfaces force unwanted recompilation/coupling.

```text
// VIOLATION
interface Worker { work(); eat(); sleep() }
class Robot implements Worker { eat() = throw NotSupported }   // LSP smell too

// FIX: role interfaces
interface Workable { work() }
interface Feedable { eat() }
interface Restable  { sleep() }
```

### 1.5 D — Dependency Inversion Principle
*High-level modules must not depend on low-level modules; both depend on abstractions.* Abstractions must not depend on details.

```text
// VIOLATION
class OrderService { db = new MySQLDriver() }       // hard-coded low-level dep

// FIX
interface OrderRepository { save(o); findById(id) }
class OrderService(repo: OrderRepository) { ... }   // injected
class MySQLOrderRepo implements OrderRepository { ... }
```

DI containers (Spring, Dagger, NestJS) automate the wiring; the principle is independent of the container.

## 2. DRY — Don't Repeat Yourself

*Every piece of knowledge must have a single, unambiguous, authoritative representation* (Hunt & Thomas).

*   DRY targets **knowledge duplication**, not code-shape duplication. Two functions with identical bodies that change for *different reasons* are not a DRY violation.
*   **Rule of Three:** wait until the pattern appears three times before extracting. Two occurrences may diverge.
*   **Premature abstraction trap:** a wrong abstraction costs more than duplication. Sandi Metz: *"duplication is far cheaper than the wrong abstraction."*

## 3. KISS — Keep It Simple, Stupid

*The simplest design that satisfies the requirement is the correct one.*

*   Prefer first-party / stdlib over a new dependency.
*   Prefer pure functions over class hierarchies when state is not required.
*   Prefer explicit data flow over magic frameworks for small systems.
*   Complexity is justified by an *observed* requirement, not an *imagined* one.

## 4. YAGNI — You Aren't Gonna Need It

XP principle (Beck). *Do not build it until you need it.*

Cost of speculative generality:
*   **Carry cost:** every speculative path must be tested, documented, maintained, secured.
*   **Lock-in:** the wrong abstraction shapes future code around itself.
*   **Opportunity cost:** time spent on the imagined future is time not spent validating the present.

*Heuristic:* if the requirement is not in a ticket, a contract, or a test, it does not exist.

## 5. Law of Demeter (Principle of Least Knowledge)

A method `m` of object `O` may only invoke methods on:
1.  `O` itself.
2.  `m`'s parameters.
3.  Objects `m` creates.
4.  `O`'s direct components.

### 5.1 Train-Wreck Antipattern
```text
// VIOLATION: order traverses three foreign objects
total = order.getCustomer().getAccount().getBalance()

// FIX: ask, do not navigate
total = order.getCustomerBalance()
```

The fix pushes behavior toward the data (Tell-Don't-Ask) and isolates the caller from internal structure changes.

## 6. Composition Over Inheritance

*Favor object composition over class inheritance* (GoF).

*   Inheritance binds subclass to superclass implementation at compile time → fragile base class problem.
*   Composition delegates behavior to a contained collaborator selected at runtime → flexible, testable, no diamond.
*   Languages without implementation inheritance (Go, Rust) prove the point: composition + interfaces/traits cover the same design space without the hazards.

## 7. Tell-Don't-Ask

Send the object a command; do not extract its state and decide externally.

```text
// ASK
if account.getBalance() >= amount: account.setBalance(account.getBalance() - amount)

// TELL
account.withdraw(amount)   // object enforces its own invariants
```

Encapsulation is preserved; invariants live with the data; race windows shrink.

## 8. Hollywood Principle / IoC

*"Don't call us, we'll call you."* The framework owns the main loop; user code provides callbacks/components plugged into well-defined extension points.

*   Manifestations: servlet containers, React component lifecycle, Spring DI, plugin systems, event-driven runtimes.
*   IoC + DI together invert both **flow** and **dependency**.

## 9. Information Hiding (Parnas, 1972)

*Modules should hide design decisions likely to change.* Parnas's seminal *On the Criteria To Be Used in Decomposing Systems into Modules* predates SOLID.

*   Decompose by **secret** (what changes), not by processing step.
*   The interface exposes only what callers must know; everything else is private and substitutable.
*   This is the foundation underneath SRP, OCP, and DIP.

## 10. Cohesion vs Coupling

| Cohesion (high → good) | Coupling (low → good) |
|---|---|
| **Functional** — single, well-defined task | **Data** — pass primitives only |
| **Sequential** — output of one step feeds the next | **Stamp** — pass structures |
| **Communicational** — operate on the same data | **Control** — pass flags that alter callee behavior |
| **Procedural** — related by control flow only | **Common** — share global state |
| **Temporal** — executed at the same time | **Content** — read/write internals of another module |
| **Logical** / **Coincidental** (worst) | **External** — share format/protocol with outside system |

Target: **maximize cohesion within a module, minimize coupling across modules.** Every other principle in this document is a tactic toward that strategic goal.

---

## Exercises

### Exercise 1: SRP Decomposition (Beginner)

You are given a `UserService` class that handles registration, authentication, password reset, profile updates, email notifications, and audit logging — all in one class (~600 lines).

1. Identify the distinct actors (stakeholders) whose change requests would affect this class.
2. Decompose the class into separate modules, each with a single reason to change.
3. Define the interfaces (contracts) between the new modules.
4. Write unit tests for each module in isolation, mocking cross-module dependencies.

**Acceptance criteria:** No module exceeds 150 lines. A change to email templates touches only the notification module.

### Exercise 2: LSP Violation Detection (Intermediate)

Given a class hierarchy where `Square extends Rectangle`:

1. Write a test that demonstrates the LSP violation: a function that accepts `Rectangle` breaks when given a `Square`.
2. Refactor using two approaches: (a) separate types with a shared `Shape` interface; (b) immutable value objects.
3. Compare the two approaches on: type safety, number of classes, ease of adding new shapes.
4. Identify one LSP violation in an open-source project (search GitHub) and describe how you would fix it.

**Acceptance criteria:** Both refactored solutions pass the original test without modification.

### Exercise 3: DRY vs. Wrong Abstraction (Intermediate)

You have three functions with near-identical bodies (~20 lines each) but different domain contexts: order pricing, tax calculation, and discount application.

1. Extract a shared abstraction.
2. After extraction, introduce a new requirement that affects only tax calculation (e.g., regional tax rules).
3. Observe how the shared abstraction now requires conditional logic or parameter flags.
4. Revert the extraction. Apply the Rule of Three — keep the duplication and document why.
5. Write a brief inline analysis: at what point would extraction become justified?

**Acceptance criteria:** The final code has no shared abstraction, each function is self-contained, and the inline analysis references Sandi Metz's "wrong abstraction" argument.

### Exercise 4: Law of Demeter Refactoring (Intermediate)

Given a codebase with at least five train-wreck chains (e.g., `order.getCustomer().getAddress().getCity()`):

1. Identify each chain and count the depth of navigation.
2. Refactor each using Tell-Don't-Ask: move the behavior toward the data.
3. Measure before/after: number of public methods exposed, number of import statements per file.
4. Write a linter rule (ESLint custom rule, Pylint checker, or ArchUnit test) that flags chains deeper than 2 dots.

**Acceptance criteria:** No chain exceeds depth 2 after refactoring. The linter rule catches violations in CI.

### Exercise 5: Principle Trade-Off Analysis (Advanced)

Design a plugin system for a text editor. Apply all principles from this module and document the trade-offs:

1. Start with YAGNI: implement only the three plugins the spec requires (syntax highlighting, auto-save, spell check).
2. Apply OCP: design the plugin interface so new plugins can be added without modifying the editor core.
3. Apply ISP: ensure each plugin depends only on the editor capabilities it needs (not a monolithic `EditorAPI`).
4. Apply DIP: the editor core depends on the `Plugin` abstraction, not on concrete plugin implementations.
5. Evaluate: did following OCP/ISP/DIP add complexity that YAGNI would have prevented? Write a 200-word trade-off assessment.

**Acceptance criteria:** Three plugins work. A fourth plugin can be added by creating one new class and zero edits to existing code. The trade-off assessment is included as inline documentation.

---

## Readings and References

### Books

1. Martin, R.C. *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall, 2008. ISBN 978-0132350884.
2. Martin, R.C. *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall, 2002. ISBN 978-0135974445. — Original source for SOLID principles.
3. Martin, R.C. *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall, 2017. ISBN 978-0134494166.
4. Hunt, A., Thomas, D. *The Pragmatic Programmer*. 20th Anniversary ed., Addison-Wesley, 2019. ISBN 978-0135957059. — DRY origin.
5. Metz, S. *Practical Object-Oriented Design: An Agile Primer Using Ruby*. 2nd ed., Addison-Wesley, 2018. ISBN 978-0134456478.
6. Gamma, E., Helm, R., Johnson, R., Vlissides, J. *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994. ISBN 978-0201633610. — "Favor composition over inheritance."
7. Meyer, B. *Object-Oriented Software Construction*. 2nd ed., Prentice Hall, 1997. ISBN 978-0136291558. — Open/Closed Principle origin.

### Articles and Online Resources

8. Martin, R.C. "The Principles of OOD." Retrieved: 2026-05-29. http://butunclebob.com/ArticleS.UncleBob.PrinciplesOfOod
9. Liskov, B., Wing, J. "A Behavioral Notion of Subtyping." *ACM TOPLAS*, 16(6), 1994, pp. 1811-1841.
10. Parnas, D.L. "On the Criteria To Be Used in Decomposing Systems into Modules." *Communications of the ACM*, 15(12), 1972, pp. 1053-1058.
11. Metz, S. "The Wrong Abstraction" (2016). Retrieved: 2026-05-29. https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction
12. DesignGurus. "Essential Software Design Principles (SOLID)." Retrieved: 2026-05-29. https://www.designgurus.io/blog/essential-software-design-principles-you-should-know-before-the-interview
13. Scalastic. "Principles of Software Development: SOLID, DRY, KISS, and more." Retrieved: 2026-05-29. https://scalastic.io/en/solid-dry-kiss/
14. Fowler, M. "bliki: Domain Driven Design." Retrieved: 2026-05-29. https://martinfowler.com/bliki/DomainDrivenDesign.html

### Papers

15. Liskov, B. "Data Abstraction and Hierarchy." *SIGPLAN Notices*, 23(5), 1988.
16. Parnas, D.L. "On the Criteria To Be Used in Decomposing Systems into Modules." *Communications of the ACM*, 15(12), 1972.

---

## Cross-References

| Module | Relationship to This Module |
|---|---|
| [01_Code_Level_Architecture.md](./01_Code_Level_Architecture.md) | Applies SOLID (especially DIP and ISP) as the foundation for the Dependency Rule, port design, and adapter segregation |
| [02_Distributed_System_Patterns.md](./02_Distributed_System_Patterns.md) | SRP and ISP guide service boundary definition; DIP enables contract-first service communication |
| [02_c_API_Design_Evolution.md](./02_c_API_Design_Evolution.md) | OCP and LSP govern API versioning strategies — new versions extend behavior without breaking existing clients |
| [04_System_Design_CAP_PACELC.md](./04_System_Design_CAP_PACELC.md) | KISS and YAGNI apply to consistency model selection — choose the simplest model that satisfies the SLA |
| [../01_Foundations/](../01_Foundations/) | Foundational programming concepts (types, functions, modules) that these principles operate on |
| [../04_Security_Cryptography/](../04_Security_Cryptography/) | Information Hiding and Least Knowledge (Demeter) directly map to security principles of least privilege and defense in depth |

---

## Glossary

| Term | Definition |
|---|---|
| **Actor (SRP)** | A stakeholder group whose change requests constitute a single "reason to change" for a module. |
| **Afferent Coupling (Ca)** | The count of external modules that depend on a given module. High Ca means the module is depended-upon and should be stable. |
| **Cohesion** | The degree to which elements within a module belong together. Functional cohesion (highest) means every element contributes to a single, well-defined task. |
| **Composition** | An object-design strategy where behavior is delegated to contained collaborators rather than inherited from a parent class. |
| **Coupling** | The degree of interdependence between modules. Lower coupling means changes in one module are less likely to require changes in others. |
| **DIP (Dependency Inversion Principle)** | High-level modules depend on abstractions, not on low-level implementation details. Both levels depend on the abstraction. |
| **DRY (Don't Repeat Yourself)** | Every piece of knowledge must have a single, unambiguous, authoritative representation in the system. Targets knowledge duplication, not code shape. |
| **Fragile Base Class Problem** | A defect pattern where changes to a base class break subclasses due to tight inheritance coupling. |
| **ISP (Interface Segregation Principle)** | Clients should not be forced to depend on interfaces they do not use. Prefer many small role interfaces over one fat interface. |
| **KISS (Keep It Simple, Stupid)** | The simplest design that satisfies the requirement is the correct one. Complexity must be justified by observed need. |
| **LSP (Liskov Substitution Principle)** | Subtypes must be substitutable for their base types without altering correctness. Preconditions cannot be strengthened; postconditions cannot be weakened. |
| **OCP (Open/Closed Principle)** | Modules should be open for extension (new behavior) and closed for modification (existing tested code remains untouched). |
| **Rule of Three** | Wait until a pattern appears in three distinct places before extracting a shared abstraction. Two occurrences may diverge. |
| **SRP (Single Responsibility Principle)** | A module should have one, and only one, reason to change — meaning it serves exactly one actor. |
| **Tell-Don't-Ask** | Send an object a command rather than extracting its state and deciding externally. Keeps invariants with the data. |
