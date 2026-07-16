# Module 2.3: Design Principles — SOLID, DRY, KISS, YAGNI, Demeter

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
