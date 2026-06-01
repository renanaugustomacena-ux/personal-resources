---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "04"
titolo: "Compilers & Interpreters Internals"
versione: "LLVM 20.x · JDK 21+ (ZGC/Shenandoah) · V8 Maglev/TurboFan · Go 1.22+"
livello: "Advanced"
prerequisiti:
  - "Formal languages and automata theory (regex, DFA/NFA, context-free grammars)"
  - "Basic computer architecture (registers, memory hierarchy, instruction sets)"
  - "Proficiency in at least one compiled and one interpreted language"
obiettivi:
  - "Trace the full compilation pipeline from source text through lexing, parsing, IR, optimization, to code generation"
  - "Construct LL and LR parse tables and implement a Pratt parser for expression grammars"
  - "Explain SSA form construction via dominance frontiers and its role in enabling optimization passes"
  - "Compare JIT tiered compilation (HotSpot C1/C2, V8 Ignition/TurboFan) against AOT compilation trade-offs"
  - "Analyze garbage collection strategies (generational, concurrent mark-sweep, ZGC, Go tri-color) and their latency/throughput implications"
tag: [compilers, interpreters, lexer, parser, AST, SSA, LLVM, JIT, AOT, garbage-collection, V8, HotSpot, ZGC]
---

# Module 1.4: Compilers & Interpreters Internals

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Trace the full compilation pipeline from source text through lexing, parsing, IR, optimization, to code generation
> - Construct LL and LR parse tables and implement a Pratt parser for expression grammars
> - Explain SSA form construction via dominance frontiers and its role in enabling optimization passes
> - Compare JIT tiered compilation (HotSpot C1/C2, V8 Ignition/TurboFan) against AOT compilation trade-offs
> - Analyze garbage collection strategies (generational, concurrent mark-sweep, ZGC, Go tri-color) and their latency/throughput implications

> **Module 01.4** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Lexing → Parsing → AST → IR → Optimization → Codegen.**
2. **AOT (ahead-of-time, Rust/Go) vs JIT (HotSpot, V8) vs Interpreted (CPython).**
3. **LLVM IR + LLVM as backend for many languages.**
4. **Rust borrow checker: type system extension.**


**Date:** 2026-04-22
**Status:** Completed

## 1. The Compilation Pipeline

Source text → executable artifact via discrete passes. Same pipeline applies to AOT (`gcc`, `rustc`), JIT (HotSpot, V8), and transpilers (TypeScript, Babel).

```
Source → Lexer → Tokens → Parser → CST/AST → Sema (type/scope) →
   IR (HIR → MIR → LIR) → Optimizer → CodeGen → Object → Linker → Binary
```

*   **Front-end:** language-specific (lexer, parser, sema).
*   **Middle-end:** language- and target-agnostic IR + optimization.
*   **Back-end:** target-specific (instruction selection, register allocation, scheduling).

LLVM enforces this split rigidly; that is why one optimizer serves Clang, Rust, Swift, Julia.

## 2. Lexical Analysis

Convert character stream to tokens (kind + lexeme + source span).

### 2.1 Regex → DFA Construction
*   **Thompson construction:** regex → ε-NFA in `O(|r|)`. Each operator (`|`, `*`, concat) maps to a fixed gadget.
*   **Subset construction:** ε-NFA → DFA. Worst-case `2^n` states; in practice tractable.
*   **Hopcroft minimization:** DFA → minimal DFA in `O(n s log n)` where `s = |Σ|`.
*   Generators: `flex`, `re2c`, `logos` (Rust). RE2 / Hyperscan use lazy DFA / bit-parallel NFAs to bound memory.

### 2.2 Practical Notes
*   Longest-match rule resolves ambiguity (`>>` vs `>`, `==` vs `=`).
*   Keywords are recognized as identifiers then reclassified via a perfect-hash table (`gperf`).

## 3. Parsing

Token stream → tree.

### 3.1 Top-Down: LL(k) / Recursive Descent
*   **LL(1):** decide production from one lookahead. Requires grammar with no left recursion and disjoint FIRST sets.
*   Hand-written **recursive descent** is the standard for production compilers (`gcc`, `clang`, `rustc`, V8): better error messages, easier disambiguation.
*   ANTLR generates LL(*) parsers with arbitrary lookahead via DFA caching.

### 3.2 Bottom-Up: LR / LALR
*   **LR(k):** shift-reduce parser driven by a state automaton. Strictly more powerful than LL(k).
*   **LALR(1):** merges LR(1) states with identical cores → smaller tables. Used by `yacc`/`bison`.
*   **GLR:** handles ambiguous grammars by forking; used by tree-sitter (with conflict resolution).

### 3.3 Pratt Parsing (Top-Down Operator Precedence)
*   Each token has a left binding power (LBP) and a `nud`/`led` function.
*   Naturally handles infix, prefix, postfix, mixfix operators with priorities.
*   Used by Crockford's JSLint, Go's expression parser, Rust's `syn`.

### 3.4 CST vs AST
*   **CST (parse tree / concrete):** every grammar production materialized; preserves whitespace, parens. Required for refactoring tools (tree-sitter, Roslyn).
*   **AST (abstract):** strips syntactic noise; what optimizers operate on.

## 4. Intermediate Representations

### 4.1 Three-Address Code (TAC)
*   Each instruction: `x = y op z`. Easy to translate to assembly.

### 4.2 Static Single Assignment (SSA)
*   Every variable assigned exactly once; merges use **φ-functions** at join points.
*   Enables sparse, fast dataflow: const propagation, dead-code elim, GVN run in near-linear time.
*   Construction: dominance frontiers (Cytron et al. 1991).

### 4.3 LLVM IR
*   Typed, SSA-based, RISC-like. Three forms: textual `.ll`, bitcode `.bc`, in-memory C++.
*   Pass manager runs `-O0`..`-O3`,`-Os`,`-Oz` pipelines composed of ~100+ passes.

### 4.4 MLIR
*   Multi-level IR with dialects (affine, linalg, gpu, llvm). Used by TensorFlow, Mojo, CIRCT.

## 5. Optimization Passes

| Pass | What |
|---|---|
| **DCE** | Remove instructions with no observable effect |
| **Constant folding** | Evaluate `2+3` at compile time |
| **Constant propagation** | Replace uses of known constants |
| **CSE / GVN** | Eliminate redundant computations |
| **Inlining** | Replace call with callee body; enables further opts |
| **Loop unrolling** | Reduce branch/index overhead; expose ILP |
| **LICM** | Hoist loop-invariant code |
| **Vectorization (SLP, loop)** | Emit SIMD (`SSE`/`AVX`/`NEON`/`SVE`) |
| **Tail-call elim** | Convert tail recursion to jumps |
| **Devirtualization** | Replace indirect call with direct when type known |
| **Escape analysis** | Allocate on stack instead of heap when lifetime is bounded |

Order matters: inlining unlocks devirt → unlocks more inlining; canonicalization passes (`instcombine`) run repeatedly between others.

## 6. JIT vs AOT

### 6.1 AOT
*   Whole program compiled before execution: `gcc`, `rustc`, `go build`, `swiftc`.
*   Pros: no runtime warmup, predictable performance, smaller runtime.
*   Cons: no profile-guided specialization (unless explicit PGO).

### 6.2 JIT — HotSpot Tiered Compilation
*   **Tier 0:** interpreter.
*   **Tier 1-3:** C1 compiler (client) — fast compile, basic opts, profiling.
*   **Tier 4:** C2 compiler (server) — aggressive opts (escape analysis, scalar replacement, deopt-based speculation).
*   Method invocation/back-edge counters trigger promotion. Deoptimization falls back to interpreter on assumption violation.

### 6.3 JIT — V8 Ignition + TurboFan
*   **Ignition:** register-based bytecode interpreter. Collects type feedback in *inline caches* (ICs).
*   **TurboFan:** speculative optimizing compiler. Sea-of-nodes IR. Speculates on observed types; deopts on shape change.
*   **Sparkplug** (intermediate, non-optimizing baseline) bridges Ignition→TurboFan latency.

## 7. Garbage Collection

### 7.1 Tracing vs Reference Counting
*   **Reference counting** (CPython, Swift ARC): increments/decrements on every assignment; cannot collect cycles without auxiliary cycle collector.
*   **Tracing:** roots → mark live → reclaim unreachable.

### 7.2 Mark-Sweep / Mark-Compact
*   Mark phase: DFS from roots. Sweep: free unmarked. Compact: relocate live objects to defragment (requires updating pointers).

### 7.3 Generational Hypothesis
*   *Most objects die young.* Heap split into Young (Eden + 2 Survivors) and Old.
*   Minor GC scavenges Young (copying collector, fast). Major GC handles Old.
*   **Card tables** / **remembered sets** track Old→Young pointers for write barriers.

### 7.4 Low-Latency Collectors (JVM)
*   **ZGC:** colored pointers (load barriers), region-based, concurrent everything. Pause times sub-millisecond, scales to TB heaps.
*   **Shenandoah:** concurrent compaction via Brooks forwarding pointers. Sub-10 ms pauses.
*   **G1:** region-based, mostly concurrent, predictable pause-time goal.

### 7.5 Go's Tri-Color Concurrent Collector
*   **White / Gray / Black** invariant: black objects never reference white.
*   Concurrent mark with **write barrier (Yuasa-style hybrid since Go 1.8)** preserves invariant under mutator activity.
*   Non-moving (no compaction) → no read barrier needed; simplifies cgo, defrag handled by allocator (size-classed, like tcmalloc).
*   STW phases bounded to sub-millisecond goals.

---

## Exercises

### Exercise 1 — Hand-Written Lexer
Implement a lexer for a minimal expression language supporting integer literals, identifiers, `+`, `-`, `*`, `/`, `(`, `)`, and `=`. Use longest-match semantics. The lexer should emit tokens with kind, lexeme, and source span (line:col). Test it against edge cases: `>=` vs `> =`, multi-digit integers, and unterminated string literals. Do not use a generator — write the DFA transitions by hand.

### Exercise 2 — Pratt Parser for Arithmetic
Build a Pratt (top-down operator precedence) parser on top of the Exercise 1 lexer. Support infix `+`, `-`, `*`, `/` with standard precedence, prefix unary `-`, and parenthesized groups. Emit an AST. Then add a right-associative `^` (exponentiation) operator and verify the parse tree for `2 ^ 3 ^ 4` is right-leaning.

### Exercise 3 — SSA Construction and Constant Propagation
Take a small control-flow graph (3 basic blocks with a branch and a join) written as three-address code. Manually compute dominance frontiers, insert phi-functions, and rename variables into SSA form following the Cytron et al. algorithm. Then apply sparse conditional constant propagation on the resulting SSA to eliminate dead assignments.

### Exercise 4 — LLVM IR Exploration
Write a function in C that computes the dot product of two float arrays. Compile it to LLVM IR at `-O0` and `-O3` (`clang -S -emit-llvm`). Diff the two `.ll` files. Identify which optimization passes fired (inlining, loop vectorization, LICM) by examining the IR annotations. Report the vectorization width chosen for your target architecture.

### Exercise 5 — GC Pause Measurement
Write a JVM application that allocates 10 million short-lived objects per second with a 1 GB heap. Run it with three collectors: `-XX:+UseG1GC`, `-XX:+UseZGC`, and `-XX:+UseShenandoahGC`. Enable GC logging (`-Xlog:gc*`). Parse the logs and plot: (a) p99 pause time, (b) total pause time, (c) throughput (application time / total time). Summarize which collector wins on latency vs. throughput.

---

## Readings and References

### Official documentation
- **LLVM Language Reference Manual** — Typed SSA-based IR specification, instruction semantics, pass pipeline. <https://llvm.org/docs/LangRef.html> (retrieved: 2026-05-29)
- **V8 Blog — TurboFan JIT** — Architecture of V8's speculative optimizing compiler. <https://v8.dev/blog/turbofan-jit> (retrieved: 2026-05-29)
- **V8 Blog — Maglev** — Mid-tier optimizing JIT bridging Sparkplug and TurboFan. <https://v8.dev/blog/maglev> (retrieved: 2026-05-29)
- **OpenJDK ZGC Project** — Design, tuning, and performance characteristics of the Z Garbage Collector. <https://openjdk.org/projects/zgc/> (retrieved: 2026-05-29)
- **JEP 439: Generational ZGC** — Generational extension of ZGC, production-ready in JDK 21+. <https://openjdk.org/jeps/439> (retrieved: 2026-05-29)
- **Go GC Guide** — Design rationale and tuning of Go's concurrent tri-color collector. <https://tip.golang.org/doc/gc-guide> (retrieved: 2026-05-29)

### Books
- Aho, A.V., Lam, M.S., Sethi, R., Ullman, J.D., *Compilers: Principles, Techniques, and Tools*, 2nd ed., Addison-Wesley, 2006. ISBN 978-0-321-48681-3. (Dragon Book)
- Nystrom, R., *Crafting Interpreters*, Genever Benning, 2021. ISBN 978-0-9905829-3-9. Also available free at <https://www.craftinginterpreters.com/>.
- Cooper, K.D., Torczon, L., *Engineering a Compiler*, 3rd ed., Morgan Kaufmann, 2022. ISBN 978-0-12-815412-0.
- Appel, A.W., *Modern Compiler Implementation in ML*, Cambridge University Press, 2004. ISBN 978-0-521-60764-3.

### Papers and articles
- Cytron, R. et al., "Efficiently Computing Static Single Assignment Form and the Control Dependence Graph", *ACM TOPLAS*, 13(4), pp. 451–490, 1991. <https://www.cs.utexas.edu/~pingali/CS380C/2010/papers/ssaCytron.pdf>
- Click, C., Paleczny, M., "A Simple Graph-Based Intermediate Representation", *ACM SIGPLAN Notices*, 30(3), 1995. (Sea-of-Nodes IR used by HotSpot C2 and V8 TurboFan)
- Liden, P., Karlsson, S., "Deep Dive into ZGC: A Modern Garbage Collector in OpenJDK", *ACM TOPLAS*, 44(4), 2022. <https://dl.acm.org/doi/full/10.1145/3538532>
- Hudson, R.L., "Getting to Go: The Journey of Go's Garbage Collector", *GopherCon 2018*. <https://go.dev/blog/ismmkeynote>

---

## Cross-References

| Module | Relationship |
|---|---|
| `03_Advanced_Data_Structures_Algorithms.md` | Graph algorithms (DFS, topological sort) used in compiler IR; skip lists used in JIT profiling data structures |
| `01_OS_Internals_Processes_Memory.md` | Virtual memory, page tables, and mmap — how compilers and GCs interact with the OS memory subsystem |
| `01_a_CPU_Kernel_Boundary.md` | System calls, context switches — runtime cost of GC stop-the-world pauses at the kernel level |
| `01_c_Memory_Management_Algorithms.md` | Heap allocators (buddy, slab, tcmalloc) underlying GC allocation strategies and Go's size-classed allocator |
| `04_Security_Cryptography/` | JIT spraying attacks, W^X enforcement — security implications of JIT-compiled code in writable+executable memory |
| `07_AI_ML_Integration/` | MLIR multi-level IR used by TensorFlow/XLA and Mojo; compiler optimizations for ML workloads (vectorization, tiling) |

---

## Glossary

| Term | Definition |
|---|---|
| **Lexer (tokenizer)** | The compiler front-end stage that converts a character stream into a sequence of tokens |
| **Parser** | The stage that transforms a token stream into a parse tree (CST) or abstract syntax tree (AST) |
| **AST** | Abstract Syntax Tree; a tree representation of source code with syntactic noise removed |
| **SSA** | Static Single Assignment; an IR form where every variable is assigned exactly once, using phi-functions at control-flow joins |
| **Phi-function (φ)** | A pseudo-instruction in SSA form that selects a value based on which control-flow predecessor was taken |
| **Dominance frontier** | The set of nodes where dominance by a given node ends; used to determine phi-function placement in SSA construction |
| **LLVM IR** | The typed, SSA-based intermediate representation used by the LLVM compiler infrastructure |
| **JIT compilation** | Just-In-Time compilation; translating bytecode or IR to native machine code at runtime |
| **AOT compilation** | Ahead-Of-Time compilation; producing native machine code before program execution |
| **Deoptimization** | The process of falling back from optimized JIT code to an interpreter when speculative assumptions are violated |
| **Generational GC** | A garbage collection strategy that partitions the heap by object age, exploiting the generational hypothesis |
| **Tri-color marking** | A concurrent GC algorithm using white/gray/black states to safely mark live objects while mutators run |
| **Write barrier** | Code injected at pointer stores to maintain GC invariants (e.g., preventing black-to-white references in tri-color marking) |
| **Colored pointers** | A technique used by ZGC where metadata bits are embedded in object pointers for concurrent relocation |
| **Pratt parser** | A top-down operator-precedence parsing technique where each token carries binding power and parse functions |
