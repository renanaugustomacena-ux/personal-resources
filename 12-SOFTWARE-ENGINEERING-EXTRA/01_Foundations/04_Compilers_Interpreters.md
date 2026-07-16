# Module 1.4: Compilers & Interpreters Internals

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
