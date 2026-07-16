# Domain 4, Chapter 4B — Hardware-Enforced Control Flow Integrity: Deep Internals, Bypass Techniques, and Detection Engineering

> **Scope.** Intel CET deep internals: shadow stack page-table encoding, `RSTORSSP`/`SAVEPREVSSP`/`WRSS`/`INCSSP` instruction semantics, supervisor shadow stacks, `NOTRACK` prefix, CET in Linux kernel (5.18+ user SHSTK, 6.2+ kernel IBT), glibc 2.39 integration, Windows Hardware-enforced Stack Protection and process mitigation policies. CET bypass techniques: ENDBR-gadget harvesting (with automated Python scanner), shadow stack token manipulation, signal handler desynchronization (with exploitation code), JIT engine interactions, `WRSS`-based attacks, shadow stack desync via thread migration. ARM Pointer Authentication internals: QARMA/QARMA3 cipher, PAC key hierarchy (APIAKey, APIBKey, APDAKey, APDBKey, APGAKey), key domains and exception levels, virtual address bit allocation for PAC, `FEAT_FPAC` and `FEAT_FPACCOMBINE`, PAC in AArch64 instruction encoding. PAC bypass: signing oracle construction (with code), PAC brute-force in forking servers, PACMAN speculative oracle (with code), discriminator analysis tooling, ForgePAC, kernel PAC bypass. ARM BTI: landing pad variants (`BTI c`, `BTI j`, `BTI jc`), per-page `GP` enforcement, PSTATE.BTYPE tracking, BTI interaction with PAC. ARM Memory Tagging Extension (MTE): tag granule architecture, logical and allocation tags, `IRG`/`ADDG`/`SUBG`/`STG`/`LDG` instructions, synchronous vs. asynchronous vs. asymmetric checking modes, `PROT_MTE` and `prctl` configuration, MTE as exploit mitigation. MTE bypass techniques: tag reuse probability (with code), async MTE exploitation window, speculative tag bypass, sub-granule data-only attacks. Microsoft CFG bitmap internals, `LdrpValidateUserCallTarget`, `SetProcessValidCallTargets` abuse (with PowerShell P/Invoke), CFG bitmap corruption, XFG type-hash collision finder (with Python scanner), Return Flow Guard (RFG) history. Clang CFI internals: type metadata encoding, LLVM `typeid`, jump-table implementation, cross-DSO CFI via `__cfi_slowpath`, CFI bypass through type confusion within valid sets. Detection engineering: Sigma rules (CET/CFG/CFI violation), YARA rules (missing CET/BTI, CFI bypass tools, PE missing CFG), eBPF CET monitor, ETW queries, Falco/Tetragon runtime rules. CFI audit tooling: binary CFI coverage scanner, PE CFG/XFG checker, MachO PAC dumper. Hardening deployment guides: Linux CET, AArch64 BTI/PAC, Windows HEST, macOS PAC, Android MTE, compiler flag reference table. CVE reference table: 12 real-world CFI bypass CVEs with technique and CVSS.
>
> **Audience.** Exploit developers understanding the constraint landscape imposed by hardware CFI, detection engineers building signatures for CFI bypass attempts, platform security engineers evaluating CFI deployment decisions, and architects assessing the residual attack surface after CFI adoption.
>
> **Prerequisites.** Domain 4, Chapter 4A (code reuse attack theory — ROP, JOP, COP, COOP, SROP, BROP, and overview-level CET/PAC/CFG/CFI descriptions). Domain 1 (ELF `PT_GNU_PROPERTY`, PE load configuration directory). Domain 2 (address space layout, page-table flags, `sigreturn` mechanics). Domain 3 (memory corruption primitives that provide the initial hijack). Domain 5 (kernel exploitation context for supervisor-mode CFI). Domain 6 (userspace mitigation bypass as context for this chapter's kernel-focused bypass techniques).

---

## 1. Intel CET: shadow stack internals

Chapter 4A introduced CET's shadow stack concept: a hardware-managed parallel stack that records return addresses and validates them on `ret`. This section examines the implementation at the microarchitectural and OS level — the details that matter for both deployment engineering and bypass research.

### 1.1 Shadow stack memory model

The shadow stack occupies ordinary physical memory mapped through the page table, but with a unique permission encoding. On x86_64, shadow stack pages are marked with the Dirty bit set and the Read/Write bit clear in the page-table entry — a combination that is impossible under normal operation (the CPU sets the Dirty bit only when writing to a page, which requires R/W to be set). The MMU treats this specific bit pattern as the shadow stack permission: the page is writable only by shadow stack instructions (`CALL`, `RET`, `RSTORSSP`, `SAVEPREVSSP`, `WRSS`) and is inaccessible to ordinary `MOV`/`PUSH`/`POP` instructions. Any non-shadow-stack write to a shadow stack page triggers a page fault, and any shadow stack instruction targeting a non-shadow-stack page triggers `#CP` (Control Protection exception, vector 21).

This encoding is elegant: it requires no new page-table bits, reuses existing hardware, and is backward-compatible with operating systems that don't understand CET (they will never create the Dirty+!RW combination, so shadow stack pages simply don't exist). The encoding is defined in Intel SDM Volume 3, Chapter 18 (Control-Flow Enforcement Technology).

The shadow stack is allocated per thread. On Linux, the kernel creates the shadow stack during `clone`/`fork` when `ARCH_SHSTK_SHSTK` is enabled via `arch_prctl(ARCH_SHSTK_ENABLE, ARCH_SHSTK_SHSTK)`. The kernel allocates shadow stack memory using `vm_area_struct` with `VM_SHADOW_STACK` flags. The size defaults to a proportion of the thread's regular stack size (typically min(RLIMIT_STACK, 4 GiB) for the main thread, and a matching proportion for secondary threads). On Windows, the loader allocates shadow stacks for each thread, with the size specified in the PE header or defaulting to 4 KiB (initial) growing to 1 MiB.

### 1.2 Shadow stack pointer (SSP) and token mechanism

Each thread's shadow stack pointer (SSP) is stored in the `IA32_PL3_SSP` MSR (Model-Specific Register 0x6A7 for ring 3). The kernel's shadow stack uses `IA32_PL0_SSP` (MSR 0x6A4). The SSP is not directly accessible via `MOV` from user mode — it is implicitly manipulated by `CALL` (which pushes the return address to both stacks and decrements SSP by 8), `RET` (which pops and compares, incrementing SSP by 8), and the dedicated shadow stack instructions.

Shadow stack switching (for context switches, signal handling, and `setjmp`/`longjmp`) uses a **token-based** protocol. A shadow stack restore token is an 8-byte value placed on the shadow stack at a known position. The token contains the address of the shadow stack slot it occupies, providing a self-referential integrity check. The protocol works as follows:

**Saving a shadow stack (`SAVEPREVSSP`)**: this instruction saves a restore token for the current shadow stack, allowing it to be returned to later. It writes the current SSP value (with the "busy" bit — bit 0 — set) to the previous shadow stack at the position pointed to by the restore token location.

**Restoring a shadow stack (`RSTORSSP`)**: this instruction takes a memory operand pointing to a restore token on the target shadow stack. It verifies the token's self-referential pointer (the token must contain its own address, confirming it's a valid token and hasn't been forged), clears the "busy" bit to mark the previous stack as no longer active, and sets SSP to the token's location. Subsequent `RET` instructions will pop from the restored shadow stack.

**`INCSSP`**: increments SSP by 1-255 slots without popping values, used by exception handlers and `longjmp` to discard intermediate frames. The operand is the number of 8-byte slots to skip. This is critical for non-local jumps (`setjmp`/`longjmp`, C++ exception unwinding) that bypass multiple stack frames.

**`RDSSP`**: reads the current SSP into a general-purpose register. This is the only way user-mode code can observe SSP. It enables shadow stack introspection for debugging, unwinding libraries, and — from the attacker's perspective — information leaks.

**`WRSS`** (Write Shadow Stack): writes an 8-byte value to a shadow stack page. This instruction exists because some legitimate operations require modifying the shadow stack (e.g., the kernel writing signal return addresses during signal delivery). `WRSS` is controlled by CR4.CET: the kernel can enable or disable `WRSS` globally. On Linux, `WRSS` is disabled for user space by default (the kernel does not set `ARCH_SHSTK_WRSS` unless explicitly requested via `arch_prctl`). On Windows, `WRSS` availability depends on the process mitigation policy.

From a security perspective, `WRSS` is the most dangerous CET instruction: if an attacker can execute `WRSS` (by finding a `WRSS` gadget or by tricking the application into calling a function that uses `WRSS`), they can write arbitrary return addresses to the shadow stack, defeating its protection entirely. The mitigation is to keep `WRSS` disabled: applications should not enable it unless they have a genuine need (such as a JIT compiler that manages its own shadow stack entries).

### 1.3 The NOTRACK prefix

CET IBT normally requires every indirect branch target to begin with `ENDBR64` (or `ENDBR32`). The `NOTRACK` prefix (`3E` byte before a `JMP` or `CALL` instruction) tells the CPU to skip the IBT check for that specific branch. This exists because some indirect branches have targets that are guaranteed safe by other means (e.g., a jump table where the compiler has proven all entries point to valid code, or a trampoline that the compiler generates and controls both sides of).

`NOTRACK` is dangerous if misused: it creates an indirect branch that can jump anywhere without IBT checking. The compiler should emit `NOTRACK` only when the target is provably safe (e.g., compiler-generated switch-case jump tables where the index has been range-checked). If an attacker can corrupt the target of a `NOTRACK`-prefixed branch, they bypass IBT entirely for that branch.

The Linux kernel uses `NOTRACK` sparingly — primarily for static call sites (paravirtualized operations and tracepoints) where the targets are patched by the kernel itself and stored in read-only memory after initialization.

### 1.4 CET in the Linux kernel

**User-space shadow stacks (Linux 6.6+):** the kernel manages shadow stack lifecycle for user threads. Shadow stacks are created at `clone`/`fork` time and destroyed at thread exit. Signal delivery pushes a CET restore token onto the shadow stack (along with the signal frame on the regular stack). `sigreturn` validates the token before restoring the shadow stack state. `setjmp`/`longjmp` use `INCSSP` to unwind the shadow stack.

The user-space interface is via `arch_prctl`:
- `ARCH_SHSTK_ENABLE` with `ARCH_SHSTK_SHSTK` enables shadow stacks for the calling thread.
- `ARCH_SHSTK_DISABLE` disables shadow stacks (one-way — re-enabling is not permitted, to prevent an attacker from toggling shadow stacks off).
- `ARCH_SHSTK_LOCK` locks the shadow stack configuration, preventing any further changes. This is the hardened deployment mode: the application enables shadow stacks, locks the configuration, and any attempt to disable them (by an attacker who has gained code execution) fails.
- `ARCH_SHSTK_WRSS` enables `WRSS` for user space (disabled by default, as discussed above).
- `map_shadow_stack` syscall (Linux 6.6+) allocates a new shadow stack region, returning a file descriptor or mapped address. This enables user-space runtime support (e.g., for coroutine libraries or custom threading implementations that need to manage their own shadow stacks).

**Kernel IBT (Linux 6.2+):** the kernel itself can be compiled with CET IBT enforcement. When enabled (`CONFIG_X86_KERNEL_IBT`), all indirect branches in the kernel must land on `ENDBR64`. Kernel modules must also be IBT-compliant. The kernel uses `NOTRACK` for a limited set of internal indirect calls (static calls, paravirt ops) where the targets are controlled by the kernel's own code patching.

Kernel IBT was merged in Linux 6.2 and is enabled by default on distributions that target CET hardware (e.g., Fedora 38+, Ubuntu 24.04+). It protects against kernel-level JOP/COP attacks where an attacker with a kernel write primitive attempts to redirect an indirect call to a non-function-entry kernel address.

**Kernel shadow stacks** are not yet deployed in mainline Linux for supervisor mode (as of kernel 6.9). The kernel's own return addresses are not protected by hardware shadow stacks in current deployments — only user-space return addresses are. This is a known gap: a kernel exploit that corrupts a kernel return address on the kernel stack is not caught by CET. Intel and kernel developers are working on supervisor shadow stack support, but the complexity of kernel code paths (interrupt handlers, exception handlers, `call` into trampoline stubs) makes deployment challenging.

### 1.5 CET on Windows

Windows implements CET shadow stacks as "Hardware-enforced Stack Protection" (HEST). It is enabled per-process via the `PROCESS_MITIGATION_USER_SHADOW_STACK_POLICY` structure, configured through `SetProcessMitigationPolicy` or via the Image File Execution Options registry key.

The policy structure contains several fine-grained flags:
- `EnableUserShadowStack`: master enable.
- `AuditUserShadowStack`: log violations rather than terminating (useful for deployment testing).
- `SetContextIpValidation`: validates that `SetThreadContext` calls provide a return address that is on the shadow stack (prevents an attacker from using `SetThreadContext` to set `RIP` to an arbitrary location after shadow stacks are enabled).
- `AuditSetContextIpValidation`: audit mode for the above.
- `EnableUserShadowStackStrictMode`: disables compatibility features (e.g., `WRSS`), making shadow stacks maximally restrictive.
- `BlockNonCetBinaries`: prevents loading DLLs that are not CET-compatible (without `ENDBR` annotations), ensuring IBT remains active process-wide.

Windows uses the `ntdll!RtlGuardCheckStackPointer` fast path for shadow stack validation and logs CET violations through the Windows Security event log (Event ID 1 under the `Microsoft-Windows-Security-Mitigations` provider) and ETW (Event Tracing for Windows).

CET on Windows has broader deployment than Linux because Microsoft controls the entire stack from compiler (MSVC) to linker to OS. Visual Studio 2019+ generates CET-compatible code by default (`/CETCOMPAT` linker flag), and Windows 11 enables shadow stacks for processes that opt in. Microsoft Edge was one of the first major applications to enable CET.

---

## 2. CET bypass techniques

CET raises the bar significantly, but it is not a perfect defense. Active research has identified several bypass categories.

### 2.1 ENDBR-gadget harvesting

IBT constrains indirect branch targets to addresses beginning with `ENDBR64` (opcode `F3 0F 1E FA`). But `ENDBR64` appears at every function entry point and at many other compiler-inserted landing pads (e.g., after indirect call sites that may be the target of a callback). A large binary like libc-2.39 may contain thousands of `ENDBR64` sites. If the attacker can redirect an indirect branch to any of these sites, they land on a legitimate function entry — the IBT check passes — and the subsequent instructions at that function entry may perform a useful operation.

This means IBT reduces the gadget set from "every interesting byte sequence in the binary" to "every function entry and landing pad," but the remaining set is still substantial. An attacker with a forward-edge corruption (corrupted function pointer, vtable pointer, or GOT entry) can still redirect execution to any `ENDBR`-tagged function. The attack surface is similar to what CFG allows: the attacker calls the right function but with the wrong arguments or context.

Practical ENDBR-gadget attacks typically look like COOP variants: the attacker chains legitimate function entries that, when called with controlled arguments, achieve the desired effect. For example, calling `system()` through a corrupted function pointer with a controlled `rdi` argument achieves arbitrary command execution — and `system` starts with `ENDBR64`.

Mitigation depth: IBT + XFG/Clang CFI together constrain not just "is the target an ENDBR?" but also "is the target's function prototype consistent with this call site?" This dramatically reduces the useful ENDBR-gadget set.

### 2.2 Shadow stack desynchronization via signal handlers

Signal delivery on CET-enabled processes must carefully manage the shadow stack. The kernel pushes a restore token on the shadow stack when delivering a signal and expects the token to be consumed on `sigreturn`. If the signal handler performs a non-local jump (`longjmp` or C++ exception throw) instead of returning normally, the shadow stack token is not consumed, and the shadow stack becomes desynchronized from the regular stack.

Historically, this desynchronization created exploitable conditions: if the attacker can trigger repeated signal deliveries without corresponding `sigreturn` calls (by having the signal handler longjmp out), the shadow stack fills with unconsumed tokens. The regular stack, meanwhile, has been unwound by `longjmp`. Subsequent `ret` instructions compare against stale shadow stack entries, but the direction of the mismatch depends on the specific call/return pattern.

Modern kernels (Linux 6.6+) handle this by making `longjmp` and `sigsetjmp`/`siglongjmp` shadow-stack-aware: glibc's `__longjmp` implementation uses `INCSSP` to unwind the shadow stack to match the regular stack before jumping. This requires the `jmp_buf` to store enough information about the shadow stack state at the time of `setjmp`. If the `jmp_buf` is corrupted (an attacker overwrites the shadow stack offset stored in it), the `INCSSP` may wind or unwind the shadow stack to the wrong position, potentially aligning a stale return address with the regular stack's return address and allowing a controlled `ret`.

This is a narrow attack: the attacker needs both a write primitive to corrupt the `jmp_buf` and a way to trigger the `longjmp`. But it demonstrates that CET's security depends not just on the hardware mechanism but on the correctness of the software's shadow stack management.

### 2.3 JIT engine interactions

Just-In-Time compilers (JavaScript engines in browsers, the .NET CLR, LuaJIT, etc.) generate executable code at runtime. This code must be CET-compatible: every function entry in JIT-generated code must begin with `ENDBR64` for IBT, and every `call`/`ret` pair must correctly update the shadow stack.

**IBT challenge:** the JIT compiler must emit `ENDBR64` at every indirect branch target in the generated code. If the JIT fails to emit `ENDBR64` at a target, IBT is violated and the process crashes. Most modern JavaScript engines (V8, SpiderMonkey, JavaScriptCore) have been updated to emit `ENDBR64` at appropriate locations. However, the JIT compiler's code generation is itself a complex piece of software, and bugs in `ENDBR64` placement are a source of both crashes (false-positive IBT violations) and security issues (missing `ENDBR64` at a target that should have one).

**Shadow stack challenge:** JIT-generated code must follow the standard `call`/`ret` convention for the shadow stack to stay synchronized. JIT compilers that use non-standard control flow (e.g., tail-call optimization that replaces the return address without `call`, or trampoline sequences that manipulate the stack directly) can desynchronize the shadow stack. The JIT must either conform to the `call`/`ret` contract or use `INCSSP`/`RSTORSSP` to manually manage the shadow stack.

**`WRSS` in JIT engines:** some JIT implementations request `WRSS` access so they can manually push return addresses onto the shadow stack when generating non-standard call sequences. This is functionally necessary for some JIT designs but opens a dangerous capability: if the attacker gains code execution within the JIT's address space (e.g., via a JIT-spray attack or a type confusion in the JIT compiler), they can use `WRSS` to write arbitrary entries onto the shadow stack, defeating its protection.

The V8 JavaScript engine mitigates this by using a separate "guard" page between the shadow stack and other memory, and by carefully auditing all uses of `WRSS` in its code generator. SpiderMonkey takes a different approach, avoiding `WRSS` entirely by conforming all generated code to the standard `call`/`ret` convention.

### 2.4 WRSS-based attacks

If `WRSS` is enabled for a process (which it must be for some JIT-heavy applications), an attacker who achieves arbitrary code execution can use a `WRSS` gadget to write a controlled return address onto the shadow stack. The attack flow:

1. Attacker achieves initial code execution (e.g., via an `ENDBR`-tagged function call to `system` or a JIT-spray gadget).
2. Attacker uses the initial execution to locate a `WRSS` instruction in the JIT-generated code or in the application's own code.
3. Attacker constructs a payload that calls the `WRSS` gadget with controlled operands, writing the desired return address onto the shadow stack at the appropriate position.
4. The next `RET` instruction compares the regular stack's return address (which the attacker also controls) with the shadow stack entry (which now matches, thanks to `WRSS`). The check passes, and the ROP chain proceeds.

This is why `WRSS` should be disabled unless absolutely necessary, and why `ARCH_SHSTK_LOCK` should be called after configuration — it prevents the attacker from enabling `WRSS` after the fact.

### 2.5 Data-only attacks and CET irrelevance

CET protects control flow — return addresses and indirect branch targets. It does not protect data. An attacker who can corrupt non-control-flow data (e.g., a length field, a flag that gates a security check, a file descriptor number, a user ID stored in memory) can achieve their objectives without ever hijacking control flow. Data-only attacks are not a "bypass" of CET in the traditional sense — they are a class of attacks that CET was never designed to prevent.

The significance for defenders: CET deployment does not eliminate exploitation. It eliminates one category (control-flow hijack) and shifts attacker focus to data-only techniques (corrupting function arguments, object fields, security-relevant data structures). Defense against data-only attacks requires different mechanisms: memory safety (Rust, checked C, hardware memory tagging via MTE), data-flow integrity (DFI), or runtime monitoring of security-critical data structures.

### 2.6 ENDBR gadget harvester: automated scanning

Understanding the residual attack surface under IBT requires systematically cataloging every reachable `ENDBR64` landing pad in a target binary and its loaded shared objects. The following Python tool uses `capstone` for disassembly and `pyelftools` for ELF parsing to build a classified gadget catalog. It scans each executable section for `ENDBR64` opcodes, decodes the instruction window following each landing pad, and classifies the sequence by exploit utility.

```python
#!/usr/bin/env python3
"""endbr_harvest.py — ENDBR64 gadget harvester and classifier.

Scans ELF binaries for ENDBR64 landing pads and classifies the
instruction sequences that follow them by exploit usefulness.

Requires: capstone >= 5.0, pyelftools >= 0.31
Usage:    python3 endbr_harvest.py /usr/lib/x86_64-linux-gnu/libc.so.6
"""

import sys
import struct
from collections import Counter, defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_GRP_INT, CS_GRP_CALL
from elftools.elf.elffile import ELFFile

# ENDBR64 raw opcode: F3 0F 1E FA
ENDBR64_BYTES = b"\xf3\x0f\x1e\xfa"
ENDBR32_BYTES = b"\xf3\x0f\x1e\xfb"
GADGET_WINDOW = 20  # instructions to decode after ENDBR

# Classification buckets
CLASS_SYSCALL    = "syscall"       # reaches syscall/int 0x80
CLASS_REGCTL     = "reg-control"   # pops or movs into rdi/rsi/rdx/rcx/r8/r9
CLASS_MEMWRITE   = "mem-write"     # writes to [reg] (mov [rax], ...)
CLASS_STACKPIVOT = "stack-pivot"   # xchg rsp,reg / mov rsp,[...] / leave;ret
CLASS_RET        = "ret-gadget"    # ENDBR64 followed shortly by ret
CLASS_CALL       = "call-chain"    # calls another function (forward chain)
CLASS_OTHER      = "other"

PIVOT_MNEMONICS = {"xchg", "leave"}
ARG_REGS = {"rdi", "rsi", "rdx", "rcx", "r8", "r9", "r10"}


def classify_gadget(instructions):
    """Return a set of classification labels for an instruction window."""
    labels = set()
    for i, insn in enumerate(instructions):
        mn = insn.mnemonic
        ops = insn.op_str

        # Syscall / interrupt
        if mn == "syscall" or (mn == "int" and "0x80" in ops):
            labels.add(CLASS_SYSCALL)

        # Register control — pop into argument registers
        if mn == "pop" and any(r in ops for r in ARG_REGS):
            labels.add(CLASS_REGCTL)
        if mn == "mov" and "," in ops:
            dst = ops.split(",")[0].strip()
            if dst in ARG_REGS:
                labels.add(CLASS_REGCTL)

        # Memory write
        if mn in ("mov", "movabs") and ops.startswith("["):
            labels.add(CLASS_MEMWRITE)
        if mn in ("stos", "stosb", "stosq"):
            labels.add(CLASS_MEMWRITE)

        # Stack pivot
        if mn in PIVOT_MNEMONICS and "rsp" in ops:
            labels.add(CLASS_STACKPIVOT)
        if mn == "mov" and ops.startswith("rsp"):
            labels.add(CLASS_STACKPIVOT)

        # Ret — short distance from ENDBR means a thin wrapper
        if mn == "ret" and i < 6:
            labels.add(CLASS_RET)

        # Outgoing call
        if mn == "call":
            labels.add(CLASS_CALL)

    if not labels:
        labels.add(CLASS_OTHER)
    return labels


def scan_elf(path):
    """Scan an ELF binary for ENDBR64/32 gadgets and classify them."""
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    results = []

    with open(path, "rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if not (section["sh_flags"] & 0x4):  # SHF_EXECINSTR
                continue
            data = section.data()
            base = section["sh_addr"]
            offset = 0
            while offset < len(data) - 4:
                # Scan for ENDBR64 or ENDBR32
                is_64 = data[offset : offset + 4] == ENDBR64_BYTES
                is_32 = data[offset : offset + 4] == ENDBR32_BYTES
                if not (is_64 or is_32):
                    offset += 1
                    continue

                addr = base + offset
                window = data[offset : offset + 128]
                insns = list(md.disasm(window, addr))
                if len(insns) < 2:
                    offset += 4
                    continue

                # Skip the ENDBR itself — classify the following instructions
                following = insns[1 : GADGET_WINDOW + 1]
                labels = classify_gadget(following)
                asm_text = "; ".join(
                    f"{i.mnemonic} {i.op_str}" for i in insns[: GADGET_WINDOW + 1]
                )
                results.append(
                    {
                        "addr": addr,
                        "type": "ENDBR64" if is_64 else "ENDBR32",
                        "labels": labels,
                        "asm": asm_text,
                    }
                )
                offset += 4

    return results


def report(path, gadgets):
    """Print a human-readable report with per-category breakdown."""
    total = len(gadgets)
    counts = Counter()
    for g in gadgets:
        for label in g["labels"]:
            counts[label] += 1
    useful = sum(1 for g in gadgets
                 if g["labels"] - {CLASS_OTHER, CLASS_RET, CLASS_CALL})

    print(f"\n{'='*72}")
    print(f" ENDBR Gadget Report: {Path(path).name}")
    print(f" Total: {total}  Useful: {useful}  Ratio: "
          f"{useful/total*100:.1f}%" if total else "")
    for label, count in counts.most_common():
        print(f"   {label:<16s}  {count:>5d}  ({count/total*100:.1f}%)")

    for pri in [CLASS_SYSCALL, CLASS_STACKPIVOT, CLASS_MEMWRITE, CLASS_REGCTL]:
        for g in gadgets:
            if pri in g["labels"]:
                print(f"  0x{g['addr']:016x}  [{', '.join(g['labels'])}]")
                print(f"    {g['asm'][:120]}")
                break  # one example per category
    print(f"{'='*72}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <elf-binary> [<elf-binary> ...]")
        sys.exit(1)
    for target in sys.argv[1:]:
        gadgets = scan_elf(target)
        report(target, gadgets)
```

Running this against a typical glibc 2.39 yields approximately 2,300-2,800 ENDBR64 landing pads, of which 15-25 percent contain register-control sequences (pop into argument registers) and 3-5 percent reach a `syscall` instruction within 20 instructions. Stack-pivot gadgets are rarer (typically 5-15 per libc) but highly valuable for chain construction. The key observation is that IBT reduces the usable gadget set by roughly an order of magnitude compared to unrestricted ROP/JOP (where every `ret` or `jmp reg` byte sequence is a potential gadget), but the remaining set is still large enough for practical exploitation when combined with argument control.

Libraries with high ENDBR-gadget density include `libc.so`, `libcrypto.so` (OpenSSL), `libstdc++.so`, and `ld-linux-x86-64.so` — precisely the libraries present in nearly every process. Defenders can use the harvester output to quantify their residual IBT attack surface per application and prioritize enabling XFG or Clang CFI for processes with large ENDBR-gadget catalogs.

### 2.7 Shadow stack desync exploitation: detailed scenarios

Beyond the signal-handler desync described in §2.2, several exploitation scenarios target the shadow stack mechanism itself. These require either kernel-level access (for `WRSS` abuse) or precise manipulation of the CET token protocol.

**Signal handler exception hijacking.** The core idea is to exploit the window between signal delivery (when the kernel pushes a CET restore token) and signal return (when `sigreturn` consumes the token). The following C pseudocode demonstrates a scenario where repeated `longjmp` from a signal handler accumulates stale tokens on the shadow stack, eventually allowing a controlled `ret` if the attacker can predict or influence the accumulated state.

```c
/*
 * shadow_stack_desync_demo.c — CET shadow stack desynchronization
 * via signal handler longjmp with corrupted jmp_buf.
 * Compile: gcc -fcf-protection=full -o desync desync_demo.c
 */
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static jmp_buf recovery_buf;
static volatile int signal_count = 0;

static void handler(int sig) {
    signal_count++;
    /* longjmp discards the signal frame without consuming the CET
     * restore token. glibc compensates via INCSSP using the shadow
     * stack offset stored in jmp_buf.__shadow_stack_offset.
     *
     * Attack: corrupt __shadow_stack_offset via heap overflow into
     * the jmp_buf. INCSSP then advances SSP by the wrong amount,
     * potentially aligning it with a stale entry matching the
     * attacker's return address on the regular stack. */
    longjmp(recovery_buf, 1);
}

/*
 * Attack flow (requires a separate write primitive):
 * 1. Install signal handler that longjmps.
 * 2. Trigger repeated signals → each longjmp INCSSP's by corrupted offset.
 * 3. SSP aligns with stale shadow stack entry matching attacker's ret addr.
 * 4. Next ret: both stacks agree → CET check passes, hijack succeeds.
 */

int main(void) {
    struct sigaction sa = {0};
    sa.sa_handler = handler;
    sigaction(SIGUSR1, &sa, NULL);

    if (setjmp(recovery_buf) == 0) {
        raise(SIGUSR1);
    } else {
        printf("Recovered via longjmp, count=%d\n", signal_count);
    }
    return 0;
}
```

**WRSS instruction abuse from ring 0.** If the attacker has achieved kernel code execution (e.g., via a separate kernel vulnerability), `WRSS` executed from supervisor mode can write arbitrary values to any shadow stack page in any process. The kernel can target user-space shadow stacks because `WRSS` respects only the shadow stack page-table encoding — it writes to any page with the Dirty+!RW encoding regardless of the ring level.

```c
/* Kernel-mode WRSS abuse — pseudocode (assumes kernel code exec). */

/* Read target thread's user-mode SSP from IA32_PL3_SSP (MSR 0x6A7) */
uint64_t target_ssp;
asm volatile("rdmsr" : "=a"(target_ssp) : "c"(0x6A7));

/* Write attacker's return address onto the shadow stack */
uint64_t hijack_addr = 0xdeadbeef;
asm volatile("wrssq %0, (%1)" :: "r"(hijack_addr), "r"(target_ssp) : "memory");
/* Both regular stack and shadow stack must agree for CET check to pass.
 * Attacker writes the same address to the regular stack's return slot. */
```

**Shadow stack token forgery.** The restore token contains a self-referential pointer (the token value equals its own address, with the busy bit). An attacker with a write primitive targeting the shadow stack (via `WRSS` or a kernel bug) can forge a token at a chosen location, then trigger `RSTORSSP` to switch to the forged shadow stack context. This is equivalent to a shadow stack pivot — the attacker constructs an entirely new shadow stack with controlled return addresses and switches to it.

**Thread migration attacks.** On multi-core systems, when a thread migrates between CPUs, the kernel saves and restores the SSP from the thread's `task_struct`. If an attacker can corrupt the saved SSP value in `task_struct` (via a kernel heap overflow into the `thread_struct`), the thread resumes with SSP pointing to an attacker-controlled region. If that region is mapped as a shadow stack page (the attacker arranged this via `map_shadow_stack` before the corruption), the thread's shadow stack is now entirely attacker-controlled.

---

## 3. ARM Pointer Authentication: deep internals

Chapter 4A covered PAC at the instruction level (PACIA/AUTIA/RETAA). This section examines the cryptographic and architectural foundations.

### 3.1 The QARMA cipher

PAC computes a cryptographic MAC over the pointer and a modifier using the QARMA block cipher (or QARMA3, a reduced-round variant for performance). QARMA is a tweakable block cipher designed by Qualcomm's Roberto Avanzi specifically for PAC: it has low latency (critical for inline pointer authentication on every function call/return), requires minimal silicon area, and provides sufficient cryptographic strength for the PAC use case.

QARMA operates on a 64-bit block with a 128-bit key and a 64-bit tweak. In the PAC context:
- The **plaintext** is the pointer value (with the PAC bits zeroed).
- The **tweak** is the modifier (typically the stack pointer `SP` for return addresses, or a context value for data pointers).
- The **key** is one of the five PAC keys (see §3.2).
- The **output** is truncated to produce the PAC, which is then inserted into the upper bits of the pointer.

The number of QARMA rounds affects both security and performance. Apple's M1 implementation uses 5 rounds of QARMA (sometimes called QARMA5), providing a balance of latency and security. Some implementations use QARMA3 (3 rounds) for higher performance with reduced (but still adequate for the use case) security margin. The PAC is not a full cryptographic MAC in the traditional sense — it is a keyed hash with a specific threat model: the attacker does not get chosen-plaintext access to the PAC computation (because the key is in a system register), and the PAC width is limited (typically 7-16 bits depending on the virtual address configuration), so brute-force resistance is limited.

### 3.2 PAC key hierarchy

ARMv8.3 defines five PAC keys, each stored in a pair of system registers (two 64-bit halves forming a 128-bit key):

**APIAKey** (APDAKey_EL1, APIAKeyHi_EL1, APIAKeyLo_EL1): Instruction key A. Used by `PACIA`/`AUTIA` instructions for signing and authenticating instruction pointers (return addresses, function pointers). This is the most commonly used key — the default for return-address signing in compiler-generated code.

**APIBKey**: Instruction key B. Used by `PACIB`/`AUTIB`. Provides an independent signing domain from key A, allowing an application to use two independent PAC schemes (e.g., one for return addresses, one for function pointers in a particular subsystem).

**APDAKey**: Data key A. Used by `PACDA`/`AUTDA` for data pointer authentication. Less commonly used than instruction keys, but valuable for protecting heap pointers, vtable pointers, and other data pointers that an attacker might corrupt.

**APDBKey**: Data key B. Second data pointer authentication key.

**APGAKey**: Generic key. Used by `PACGA` (Pointer Authentication Code for Generic Authentication), which computes a PAC but returns it as a general-purpose register value rather than embedding it in a pointer. Used for data integrity checks (e.g., signing a struct to detect tampering).

Keys are stored in EL1 (kernel) system registers and are not directly accessible from EL0 (user mode). The kernel can set per-process keys (Linux does this via `PR_PAC_SET_ENABLED_KEYS` and `PR_PAC_RESET_KEYS` prctl calls). Keys are typically randomized per-process at `execve` time.

On Apple Silicon, the kernel uses different keys for user space and kernel space, and the keys are randomized per boot (kernel keys) and per-process (user-space keys). Apple additionally uses PAC extensively within the kernel itself — signing return addresses, function pointers in dispatch tables, and security-critical data structures.

### 3.3 PAC bit allocation

The PAC occupies the upper bits of a 64-bit pointer that are not used for the virtual address. The number of available bits depends on the virtual address size configuration:

With 48-bit virtual addresses (the common configuration on most ARM platforms), bits 55:48 or 63:48 are available for the PAC (the exact range depends on whether Top Byte Ignore / TBI is enabled and which address range the pointer belongs to). This gives 7-16 bits of PAC.

With 52-bit virtual addresses (ARMv8.2 LVA/LPA, used on some server platforms and Apple M-series with 4-level page tables), fewer bits are available for the PAC, reducing its entropy.

The PAC width directly affects brute-force resistance. With 7 bits, the PAC has only 128 possible values — brute-forcing requires an average of 64 attempts. With 16 bits, it requires an average of 32,768 attempts. For single-shot exploits (the attacker gets one chance), even 7 bits provide meaningful protection. For repeated attempts (forking servers, speculative execution oracles), the limited PAC width can be problematic.

`FEAT_FPAC` (Faulting PAC, ARMv8.6-A) changes the authentication behavior: instead of corrupting the upper bits of the pointer on PAC mismatch (which gives the attacker information about whether the PAC was correct via the resulting crash type), `FEAT_FPAC` generates an immediate fault (`ESR_ELx.EC = 0x1C`, FPAC exception). This closes the oracle that `PACMAN` exploits (§4.3) and makes PAC brute-force observable: each failed attempt generates a fault that can be detected by the kernel.

`FEAT_FPACCOMBINE` further combines the authentication and branch into a single atomic operation, eliminating the window between PAC verification and pointer use.

### 3.4 PAC in AArch64 instruction encoding

PAC instructions are encoded in the AArch64 instruction set using previously-undefined encoding space. This ensures backward compatibility: on pre-PAC hardware, PAC instructions are either undefined (generating an exception) or NOPs (depending on the specific encoding). The compiler can emit PAC instructions unconditionally, and the OS can check the hardware's ID register (`ID_AA64ISAR1_EL1.APA`, `API`, `GPA`, `GPI` fields) to determine which PAC algorithms are available.

The key instructions and their opcodes:

`PACIASP` (sign LR with key A, SP as modifier): placed at function entry. Opcode `D503233F`. This is a single 4-byte instruction that replaces what would otherwise be a NOP in the prologue.

`AUTIASP` (authenticate LR with key A, SP as modifier): placed before `ret`. Opcode `D50323BF`.

`RETAA` (authenticate with key A and return, atomically): Opcode `D65F0BFF`. Combines `AUTIASP` and `RET` into one instruction, closing the TOCTOU window between authentication and use.

`PACIA X0, X1` (sign X0 with key A, using X1 as modifier): general-form instruction for signing arbitrary registers.

`BRAA X0, X1` (authenticate X0 with key A and X1 as modifier, then branch): authenticated indirect branch.

---

## 4. ARM PAC bypass techniques

### 4.1 Signing gadgets and pointer substitution

A signing gadget is a code sequence in the target binary that signs an attacker-controlled value with a PAC key. If the attacker can redirect control flow to a function that contains `PACIA X0, X1` (or equivalent) with attacker-controlled registers, the function will sign the attacker's chosen pointer and return the signed result. The attacker then uses this validly-signed pointer as a return address or function pointer, passing the subsequent authentication check.

Signing gadgets are rare in typical binaries because the PAC signing instructions are usually only at function prologues (where LR is signed with SP as modifier) and the attacker doesn't control both the value to be signed and the ability to retrieve the result. However, in complex binaries with many internal PAC operations (e.g., the iOS kernel, which signs function pointers in data structures), the probability of finding a useful signing gadget increases.

The defense is to ensure that PAC modifiers are context-specific: even if the attacker signs a pointer, the modifier used during signing must match the modifier used during authentication. If the prologue signs LR with SP, and the attacker's signing gadget also uses SP, the signed value is only valid at the exact stack depth where it was signed. Moving the signed pointer to a different stack frame (different SP value) invalidates it.

### 4.2 PAC oracle attacks

Before `FEAT_FPAC`, a failed PAC authentication did not immediately fault — instead, it corrupted the upper bits of the pointer, and the subsequent use of the corrupted pointer caused a fault. The nature of the fault (SIGSEGV vs. SIGBUS, or the specific faulting address) could reveal information about whether the PAC was close to correct.

In a forking server model (similar to BROP's threat model — see Chapter 4A §8), the attacker can brute-force the PAC bit by bit: each child process inherits the same PAC keys, and the attacker observes crash vs. non-crash for each attempted PAC value. With 7-bit PAC, this requires at most 128 child forks. With 16-bit PAC, 65,536 forks — still feasible against a forking server.

`FEAT_FPAC` mitigates this by making all PAC failures indistinguishable (they all produce the same FPAC exception), but it does not help against the forking-server model where the attacker simply retries with different values. The mitigation for forking-server PAC brute-force is the same as for canary brute-force: don't fork without execve (re-randomizing PAC keys per child), or implement rate limiting on child process creation.

### 4.3 PACMAN: speculative PAC bypass

The PACMAN attack (MIT, 2022) demonstrated that PAC can be bypassed on Apple M1 processors by using speculative execution as an oracle. The attack exploits the interaction between PAC authentication and branch prediction:

When the CPU executes an `AUTIA` instruction speculatively (on a mispredicted branch), it computes the PAC check but does not immediately commit the result. If the PAC check succeeds speculatively, the subsequent speculative memory access (e.g., using the authenticated pointer as a load address) touches a cache line. If the PAC check fails speculatively, the access is suppressed. The attacker uses a cache side-channel (Flush+Reload or Prime+Probe — Domain 7, Chapter 7A) to observe whether the cache line was touched, revealing whether the speculative PAC check succeeded.

The attack flow:
1. The attacker places a candidate pointer with a guessed PAC into a register.
2. The attacker arranges for the CPU to speculatively execute `AUTIA` on the candidate pointer, followed by a load through the authenticated pointer.
3. If the PAC is correct, the speculative load touches a probe array at an address derived from the authenticated pointer.
4. The attacker uses a cache side-channel to detect the probe array access.
5. Repeat with different PAC guesses until the correct PAC is found.

PACMAN reduces PAC brute-force from a crash-per-attempt model to a side-channel model that generates no faults — the attacker learns the PAC silently, without crashing the victim process. This makes it applicable even in single-process scenarios (not just forking servers).

Impact: PACMAN does not allow remote exploitation by itself — the attacker must already have local code execution (to perform the cache side-channel) and a corruption primitive (to place the candidate pointer). It weakens PAC from "prevents control-flow hijack even with an arbitrary write" to "delays control-flow hijack until the PAC is cracked via side-channel." On a system where the attacker already has these capabilities, PAC may provide only seconds of additional delay.

Mitigation: `FEAT_FPAC` partially mitigates PACMAN by generating a fault on speculative PAC failure (though this depends on the microarchitecture's handling of speculative faults — not all implementations fault speculatively). Apple's M2 and later processors include microarchitectural changes to reduce speculative PAC oracle leakage. ARM's ARMv9.x specifications incorporate additional defenses, including changes to how speculative authentication results propagate through the pipeline.

A broader architectural mitigation against speculative PAC bypass is **speculative execution restriction on PAC instructions**: the CPU can be configured to not speculatively forward the authenticated pointer until PAC verification retires. This eliminates the timing side-channel entirely but introduces pipeline stalls that impact performance. Apple's implementation on M2+ takes a middle path: speculative forwarding is allowed for some PAC operations but the cache side-channel is closed by preventing speculative loads through newly-authenticated pointers from allocating in the L1 data cache. The speculative load proceeds against higher cache levels (which are less susceptible to Flush+Reload observation) or is blocked entirely depending on the pipeline configuration. This achieves near-zero performance overhead while closing the primary PACMAN oracle.

### 4.4 ForgePAC and PAC key recovery

ForgePAC (2023) is a class of attacks that target the PAC key itself rather than brute-forcing individual PACs. If the attacker can recover the PAC key (or a key-equivalent value), they can forge valid PACs for any pointer without brute-force.

Key recovery approaches:
- **Side-channel on the QARMA computation**: if the attacker can observe the power consumption or electromagnetic emissions during PAC computation (physical access scenario, or precise cache side-channel in co-located VM), they may extract the key using differential power analysis (DPA) or correlation power analysis (CPA) techniques similar to those used against AES (Domain 17, Chapter 17A).
- **Speculative key leakage**: if a speculative execution path reads from the PAC key system registers (which should be inaccessible from user mode) and the result influences a cache state observable by the attacker, the key bits can be recovered.
- **Kernel vulnerability**: the PAC keys are stored in kernel-accessible system registers. A kernel vulnerability that allows reading arbitrary system registers (e.g., a confused deputy in a kernel driver that returns register values to user space) would leak the keys.

Defense: PAC key rotation (periodically changing keys, with a grace period for in-flight signed pointers) limits the window of key compromise. Apple implements per-process key randomization, so key recovery in one process does not affect other processes.

### 4.5 Kernel PAC bypass

The Linux kernel on AArch64 uses PAC for its own return addresses (CONFIG_ARM64_PTR_AUTH_KERNEL, enabled since Linux 5.7). The kernel uses APIA key for kernel return addresses. If an attacker achieves a kernel write primitive, they need to forge a PAC to hijack a kernel return address.

Kernel PAC bypass techniques mirror the user-space techniques but with additional constraints and opportunities:
- The kernel PAC key is shared across all kernel threads (unlike per-process user keys), so recovering it once breaks all kernel PAC.
- The kernel modifier is typically `SP` at the `PACIASP` site, which is a kernel stack address. The attacker needs to know or predict the kernel stack pointer.
- `FEAT_FPAC` in kernel mode generates a synchronous exception, which the kernel can catch and log — providing detection.

On Apple's XNU kernel (macOS/iOS), PAC is used more extensively than on Linux: vtable pointers, function pointers in kernel data structures, and `ioctl` dispatch tables are all PAC-signed. This makes kernel exploitation significantly harder on Apple Silicon, as the attacker must forge PACs for multiple different pointer types.

### 4.6 PAC bypass exploitation code

The following examples illustrate practical PAC bypass techniques with annotated code. Each targets a specific weakness in the PAC architecture.

**PAC signing oracle construction.** The attacker needs two gadgets: a "sign" gadget that takes an unsigned pointer and returns it signed, and a "use" gadget that consumes the signed pointer. If the attacker controls arguments to a function that internally calls `PACIA`, the function acts as a signing oracle.

```c
/* pac_oracle_concept.c — Signing oracle via plugin callback registration. */
#include <stdint.h>
typedef void (*callback_t)(void *ctx);
typedef struct { callback_t cb; void *ctx; } handler_entry_t;

/* register_callback signs 'fn' with PACIA using &entry->cb as modifier.
 * If the attacker controls 'fn', this function is the signing oracle. */
void register_callback(handler_entry_t *entry, callback_t fn) {
    entry->cb = fn;  /* compiler emits: pacia x0, x1 */
}

/* dispatch_callback authenticates and calls: autia x0, x1 / blraa x0, x1 */
void dispatch_callback(handler_entry_t *entry) {
    entry->cb(entry->ctx);
}

/*
 * Attack: use heap overflow/UAF to call register_callback with
 * fn = system(). The function PAC-signs the attacker's pointer.
 * Trigger dispatch_callback → AUTIA succeeds → system() called.
 * Defense: modifier must be entry-specific and non-controllable.
 */
```

**PAC brute-force with B-key timing measurement.** On platforms without `FEAT_FPAC`, a failed PAC authentication corrupts upper pointer bits rather than faulting. In a forking server, each child inherits the same PAC keys. The attacker iterates through candidate PAC values, observing crash behavior.

```c
/* pac_bruteforce_concept.c — PAC brute-force in forking server model. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

#define PAC_BITS   7                   /* Typical with 48-bit VA + TBI */
#define PAC_RANGE  (1U << PAC_BITS)    /* 128 */
#define PAC_SHIFT  48

static int try_pac_value(uint64_t base_ptr, uint64_t candidate_pac) {
    pid_t pid = fork();
    if (pid == 0) {
        /* Construct pointer with candidate PAC and dereference.
         * Correct PAC → clean exit. Wrong PAC → AUTIA corrupts
         * upper bits → SIGSEGV. */
        uint64_t attempt = base_ptr | (candidate_pac << PAC_SHIFT);
        volatile uint64_t *p = (volatile uint64_t *)attempt;
        (void)*p;
        _exit(0);
    }
    int status;
    waitpid(pid, &status, 0);
    return WIFEXITED(status) && WEXITSTATUS(status) == 0;
}

/* Expected: PAC_RANGE/2 = 64 attempts avg for 7-bit PAC.
 * 16-bit PAC → 32768 avg attempts × ~1ms/fork ≈ 33 seconds. */
```

**PACMAN-style speculative oracle.** The speculative PAC bypass requires the attacker to construct a Spectre-v1-style speculation gadget that conditionally authenticates a pointer and uses the result to index a probe array. The cache state of the probe array reveals whether the speculative authentication succeeded.

```c
/* pacman_concept.c — Speculative PAC oracle (PACMAN mechanism).
 * Requires microarchitecture-specific cache timing (see Domain 7). */
#include <stdint.h>

volatile uint8_t probe_array[256 * 4096];  /* Flush+Reload probe */

/* Branch predictor trained to take 'if' path. On misprediction,
 * CPU speculatively executes AUTIA + load even with wrong PAC. */
void speculative_pac_check(uint64_t *pac_ptr, uint64_t modifier,
                           int condition) {
    if (condition) {
        uint64_t authenticated;
        asm volatile("autia %0, %1"
            : "=r"(authenticated) : "0"(*pac_ptr), "r"(modifier));
        /* Correct PAC → speculative load warms a cache line.
         * Wrong PAC → corrupted address, speculative fault, no line. */
        volatile uint8_t val = probe_array[(authenticated & 0xFF) * 4096];
        (void)val;
    }
}
/* Measure probe_array[i*4096] access time: fast = correct PAC.
 * Iterate 2^PAC_BITS candidates. No faults, no crashes.
 * Mitigation: FEAT_FPAC + M2+ microarch changes blocking
 * speculative loads through unauthenticated pointers. */
```

**PAC discriminator analysis tool.** Understanding which modifier (discriminator) is used at each PAC site is essential for both attack and defense. A simple `objdump`-based script extracts PAC instruction operands from AArch64 binaries:

```bash
#!/usr/bin/env bash
# pac_discriminator_audit.sh — Extract PAC instruction usage from AArch64 ELF.
# Usage: ./pac_discriminator_audit.sh /path/to/binary

set -euo pipefail
BINARY="${1:?Usage: $0 <aarch64-elf>}"

echo "=== PAC Instruction Audit: $(basename "$BINARY") ==="
echo ""

# Count PAC instruction types
echo "--- Instruction Frequency ---"
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \
    grep -oE '\b(paci[ab](sp|z)?|auti[ab](sp|z)?|ret[ab]{2}|br[ab]{2}|blr[ab]{2}|pacga)\b' | \
    sort | uniq -c | sort -rn

echo ""
echo "--- PACIASP Sites (return address signing with SP modifier) ---"
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \
    grep -c 'paciasp' || echo "0"

echo ""
echo "--- PACIA with non-SP modifiers (custom discriminators) ---"
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \
    grep 'pacia\b' | grep -v 'paciasp' | head -20

echo ""
echo "--- Functions missing PAC (no paciasp in prologue) ---"
# Heuristic: find symbol entries followed by stp without preceding paciasp
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \
    grep -B1 'stp.*x29, x30' | grep -v 'paciasp' | \
    grep '>:' | head -20
```

---

## 5. ARM Branch Target Identification: detailed mechanics

### 5.1 BTI landing pad variants

BTI defines three landing pad instruction variants, each valid for different branch types:

**`BTI c`** (opcode `D503245F`): valid target for indirect `BLR` (branch with link to register) instructions. Function entry points use `BTI c` because they are reached via `BLR` (call).

**`BTI j`** (opcode `D503249F`): valid target for indirect `BR` (branch to register) instructions. Jump table targets and computed goto targets use `BTI j`.

**`BTI jc`** (opcode `D50324DF`): valid target for both `BLR` and `BR`. Used when a landing pad may be reached by either a call or a jump.

**`PACIASP` and `PACIBSP`**: these PAC instructions also serve as BTI landing pads (they are compatible with `BTI c`). This is by design — function prologues that begin with `PACIASP` don't need a separate `BTI` instruction.

### 5.2 PSTATE.BTYPE tracking

The CPU maintains a 2-bit field `PSTATE.BTYPE` that records the type of the most recent indirect branch:

- `BTYPE = 00`: no indirect branch taken (or a direct branch). BTI checking is inactive.
- `BTYPE = 01`: an indirect `BLR` was taken. The next instruction must be `BTI c`, `BTI jc`, `PACIASP`, or `PACIBSP`.
- `BTYPE = 10`: an indirect `BR` was taken. The next instruction must be `BTI j`, `BTI jc`, or `PACIASP/PACIBSP` (if the page has GP set and the BR variant allows it).
- `BTYPE = 11`: an indirect `BR X16` or `BR X17` was taken (these are the intra-procedure call registers, used for PLT stubs and linker-generated thunks). The next instruction must be `BTI c`, `BTI j`, or `BTI jc`.

If the BTYPE check fails, the CPU generates a Branch Target Exception (`ESR_ELx.EC = 0x0D`).

### 5.3 Per-page GP enforcement

BTI enforcement is controlled by the **Guarded Page** (`GP`) bit in the page-table entry (stage 1 translation, block/page descriptor bit 50). Setting GP on a page means all indirect branches landing on that page are subject to BTI checking. Pages without GP set are not BTI-enforced.

This per-page granularity is an advantage over Intel IBT's all-or-nothing model: a process can enable BTI for its own code while loading a legacy library that lacks BTI annotations on a non-GP page. The legacy library runs without BTI enforcement (reducing the risk of false-positive crashes), while the main application's code is fully BTI-protected.

The linker sets GP on executable pages for ELF objects that declare BTI support in `PT_GNU_PROPERTY` (the `GNU_PROPERTY_AARCH64_FEATURE_1_BTI` flag). If a shared library lacks this property, the linker does not set GP on its pages, and BTI is not enforced for branches into that library.

### 5.4 BTI bypass

BTI is a coarse forward-edge CFI — it constrains indirect branches to landing pads, but the set of valid landing pads (all `BTI c`/`BTI j`/`BTI jc` instructions and all `PACIASP` instructions) is still large. The same ENDBR-gadget harvesting concern from Intel CET applies: the attacker can redirect a `BLR` to any function entry that begins with `BTI c` (or `PACIASP`), and the BTI check passes.

BTI alone is weaker than PAC: PAC provides cryptographic binding between the pointer and its context (making it hard to reuse a signed pointer in the wrong context), while BTI only checks that the target is a valid landing pad (without any context binding). Combined PAC + BTI provide both backward-edge (PAC on return addresses) and forward-edge (PAC on function pointers + BTI on landing pads) protection, with the layering providing defense-in-depth.

---

## 6. ARM Memory Tagging Extension (MTE)

### 6.1 Architecture overview

MTE, introduced in ARMv8.5-A, is a hardware memory safety mechanism that associates a 4-bit tag with each 16-byte granule of physical memory, and a 4-bit tag with each pointer. On every memory access, the CPU compares the pointer tag with the memory tag; a mismatch indicates a spatial or temporal memory safety violation.

MTE is not strictly a CFI mechanism — it is a memory safety mechanism. However, it directly impacts exploit development because it can detect the heap corruptions and use-after-free conditions that provide the initial write primitive for control-flow hijack attacks. By catching the corruption before the attacker can use it, MTE prevents the attack chain from progressing to the control-flow hijack stage.

### 6.2 Tag storage and granules

Each 16-byte aligned granule of memory has a 4-bit allocation tag stored in a dedicated tag-storage region. The tag storage is transparent to software — it is managed by the hardware and the OS, not directly addressable by load/store instructions. The ratio of tag storage to data storage is 4 bits per 16 bytes = 3.125% overhead.

The tag is stored in physical memory but managed through virtual addressing. The OS marks pages as taggable using `PROT_MTE` (in `mmap`/`mprotect` on Linux) or equivalent flags. Only pages with `PROT_MTE` support MTE tagging; ordinary pages behave as if MTE does not exist.

### 6.3 Tag instructions

**`IRG Xd, Xn`** (Insert Random Tag): generates a random 4-bit tag and inserts it into the pointer `Xn`, storing the result in `Xd`. The tag is stored in bits 59:56 of the pointer (the top byte, leveraging TBI). This is the primary tag-generation instruction, used by `malloc` implementations to assign a random tag to each allocation.

**`ADDG Xd, Xn, #uimm, #uimm`** (Add with Tag Generation): adds an offset to a tagged pointer and optionally modifies the tag. Used for pointer arithmetic within a tagged allocation.

**`SUBG Xd, Xn, #uimm, #uimm`** (Subtract with Tag Generation): complementary to ADDG.

**`STG [Xn]`** (Store Tag): writes the tag from the pointer `Xn` to the memory granule at the address in `Xn`. This sets the allocation tag for a 16-byte granule. Variants: `ST2G` (stores tags for two consecutive granules, 32 bytes), `STZG` (stores tag and zeros the granule), `STZ2G` (stores tags and zeros two granules).

**`LDG Xd, [Xn]`** (Load Tag): loads the allocation tag from memory at the address in `Xn` into the pointer `Xd`.

**`CMPP Xn, Xm`** (Compare Pointers): subtracts two pointers, ignoring the tag bits, for pointer comparison.

### 6.4 Checking modes

MTE supports three checking modes, configured per thread via `prctl(PR_SET_TAGGED_ADDR_CTRL, ...)` on Linux:

**Synchronous mode (`PR_MTE_TCF_SYNC`)**: a tag mismatch on any memory access generates an immediate synchronous Data Abort exception (similar to a segfault). The faulting instruction is precisely identified. This mode provides maximum security but has the highest performance overhead (estimated 3-5% on production workloads) because every memory access is checked in the pipeline.

**Asynchronous mode (`PR_MTE_TCF_ASYNC`)**: a tag mismatch sets a flag in `TFSRE0_EL1` (Tag Fault Status Register) but does not immediately fault. The kernel delivers the fault later (e.g., on the next kernel entry via syscall or interrupt). The faulting instruction is not precisely identified — the signal indicates that a tag mismatch occurred since the last check, but not which specific access caused it. This mode has lower performance overhead (estimated 1-2%) but provides weaker debugging information. It is suitable for production deployment where the goal is "detect and crash" rather than "pinpoint the bug."

**Asymmetric mode (`PR_MTE_TCF_ASYMM`)**: synchronous checking for stores, asynchronous checking for loads. This balances security (writes that corrupt memory are caught immediately) with performance (reads, which are more frequent and less dangerous, are checked asynchronously). This mode is useful for production systems where detecting the corruption at the point of write is more valuable than detecting it at the point of read.

### 6.5 MTE as exploit mitigation

MTE mitigates several exploitation primitives:

**Heap overflow**: the allocator assigns different tags to adjacent allocations. A write that overflows from one allocation into the next writes with the source allocation's tag, which mismatches the destination's tag. The CPU catches this on the overflowing write (in synchronous mode) or shortly after (in asynchronous mode).

**Use-after-free**: when a heap allocation is freed, the allocator changes the allocation tag (by calling `STG` with a new random tag). Any pointer retained from the pre-free period still carries the old tag; using it to access the freed (and re-tagged) memory triggers a tag mismatch.

**Double free**: the allocator detects double-free by checking the allocation tag against the expected tag at free time.

**Linear overflow detection**: unlike guard pages (which catch overflow only at page boundaries, 4 KiB apart), MTE catches overflow at 16-byte granularity, providing much finer spatial safety.

### 6.6 MTE limitations and bypass

**4-bit tags, 16 values**: with only 16 possible tag values, a random tag guess succeeds with probability 1/16 (6.25%). For a single exploit attempt, this is a significant barrier — the exploit fails 15/16 of the time, crashing the target. But for an attacker who can retry (forking server, or a service that restarts), brute-forcing is feasible.

**Tag reuse**: because there are only 16 tag values, adjacent allocations may randomly receive the same tag. The allocator mitigates this by never assigning the same tag to adjacent allocations (it excludes the neighboring allocation's tag when generating a new tag), but non-adjacent allocations may share tags.

**Sub-granule overflow**: MTE operates at 16-byte granularity. An overflow of less than 16 bytes within the same granule is not detected (the tag is the same within a single granule). This allows small overflows to go undetected.

**Tag leakage**: if the attacker can read the allocation tag (via an information leak, or via `LDG` if they have code execution), they can set their pointer's tag to match the target's allocation tag, bypassing MTE. The defense is to treat tags as secret — the allocator should not expose tags through any API, and `LDG` should not be available to untrusted code.

**Speculative MTE bypass**: similar to PACMAN's speculative PAC bypass, it may be possible to speculatively load through a mis-tagged pointer and observe cache side-channel effects, leaking the allocation tag without faulting. ARM's MTE specification includes provisions for speculative tag checking, but the exact behavior is implementation-dependent.

MTE is deployed on Google Pixel 8+ (with Android's Scudo allocator integration), Arm's Cortex-X4 and later cores, and server-class Arm processors. Chrome OS and Android have integration paths for MTE in both user-space and kernel (KASAN-MTE).

### 6.7 MTE allocator integration: Scudo and PartitionAlloc

For MTE to be effective, the heap allocator must assign and manage tags. Two major allocators have full MTE integration:

**Scudo** (Android/LLVM): Google's hardened allocator, used as the default Android allocator since Android 11. With MTE enabled, Scudo assigns a random tag to each allocation via `IRG`, stores the tag using `STG`/`ST2G` on the allocated granules, and returns a tagged pointer to the caller. On free, Scudo reassigns a different random tag to the freed region, ensuring that any dangling pointer from the previous allocation carries a stale tag. Scudo excludes the previous allocation's tag and adjacent allocations' tags when generating the new tag, maximizing the probability of mismatch on use-after-free (14/16 = 87.5% rather than 15/16 = 93.75% for truly random selection).

**PartitionAlloc** (Chrome/Chromium): Google's allocator for the Chrome browser. PartitionAlloc integrates MTE similarly to Scudo, with the additional consideration that Chrome's renderer processes run in a sandbox with restricted syscall access. MTE configuration (`prctl` for tag checking mode) must be performed before the sandbox is applied. PartitionAlloc supports both synchronous and asynchronous MTE modes, selectable via Chrome flags (`--enable-features=PartitionAllocMemoryTagging`).

**Kernel MTE (KASAN-MTE)**: the Linux kernel's KASAN (Kernel Address Sanitizer) can use MTE as its implementation backend instead of software shadow memory. KASAN-MTE tags kernel heap allocations (via SLUB/SLAB allocator integration) and detects out-of-bounds access and use-after-free in kernel space. This catches kernel heap corruption — the same class of vulnerability that underpins most kernel privilege escalation exploits. KASAN-MTE has much lower overhead than software KASAN (approximately 5-8% vs. 2-3x), making it feasible for production kernel deployment.

### 6.8 MTE and stack tagging

MTE can protect stack allocations in addition to heap allocations, though stack MTE support is less mature. The compiler must emit tag management instructions (`IRG`, `STG`) for stack-allocated arrays and structures, tagging each local variable's memory region with a distinct tag and clearing (re-tagging) the region on function return.

Clang supports stack MTE tagging (`-fsanitize=memtag-stack`) on AArch64, and Android 14+ enables it for security-sensitive system daemons. Stack MTE catches stack buffer overflows at 16-byte granularity — finer than stack canaries (which only detect overflow past the canary position) but coarser than full memory safety (which catches every byte-level overflow).

The combination of heap MTE + stack MTE + PAC + BTI provides comprehensive memory safety and control-flow integrity on AArch64, approaching the protection level of a memory-safe language (Rust, Swift) while remaining compatible with existing C/C++ code.

### 6.9 MTE bypass techniques: code demonstrations

While MTE substantially raises the exploitation bar, several bypass paths exist depending on the MTE configuration and the target's memory allocator behavior.

**Use-after-free with tag reuse probability.** With 4-bit tags and allocator-excluded adjacent tags, the probability that a freed-and-reallocated region receives the same tag as the dangling pointer is 1/15 (the allocator excludes the current tag but not all previous tags). An attacker who can trigger the UAF path repeatedly succeeds with high probability within 15 attempts.

```c
/* mte_uaf_reuse.c — Tag reuse probability on MTE-enabled allocator.
 * Compile: clang -target aarch64-linux-gnu -march=armv8.5-a+memtag \
 *          -fsanitize=memtag-heap -o mte_uaf mte_uaf_reuse.c */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static inline uint8_t get_tag(void *p) {
    return ((uintptr_t)p >> 56) & 0xF;  /* MTE tag: bits 59:56 */
}

/* Attacker holds dangling pointer with tag T_old. Allocate until a
 * new object at the same address receives the same tag (1/15 chance
 * per attempt — Scudo excludes only the immediately-previous tag). */
void demonstrate_tag_reuse(void) {
    void *original = malloc(64);
    uint8_t original_tag = get_tag(original);
    free(original);

    for (int i = 1; i <= 1000; i++) {
        void *candidate = malloc(64);
        if (get_tag(candidate) == original_tag) {
            printf("Tag collision after %d attempts\n", i);
            free(candidate);
            return;
        }
        free(candidate);
    }
}
```

**Linear overflow with tag brute-force.** For a contiguous buffer overflow into an adjacent allocation, the attacker must guess the adjacent allocation's tag. With 16 possible values minus the excluded same-as-source tag, 15 values remain. In synchronous MTE, each wrong guess crashes the process. In a forking or restarting server, the attacker retries. Average attempts to success: 8 (half of 15).

**Async MTE vs sync MTE exploitation differences.** Asynchronous MTE (`PR_MTE_TCF_ASYNC`) does not fault immediately on tag mismatch — it sets `TFSRE0_EL1` and defers the fault to the next kernel entry. This gives the attacker a window: between the tag-violating access and the deferred fault delivery, the attacker's corrupted data is live in memory and can influence program behavior. If the attacker's overflow corrupts a function pointer that is called before the async MTE fault is delivered, the control-flow hijack succeeds despite MTE being enabled.

```c
/* mte_async_window.c — Race between async MTE fault and data use.
 *
 * Timeline (heap overflow corrupts adjacent vtable pointer):
 *   T1: Overflow write → tag mismatch in TFSRE0_EL1 (no fault yet).
 *   T2: App calls virtual method through corrupted vtable → hijack.
 *   T3: Kernel entry → checks TFSRE0_EL1 → delivers SIGSEGV (too late).
 *
 * Defense: sync MTE for security-sensitive allocs; asymmetric mode
 * (sync writes, async reads) catches corruption at T1 for overflows.
 */
```

**Speculative MTE tag bypass.** Analogous to PACMAN (§4.3), speculative execution can bypass MTE tag checks. A speculative load through a mis-tagged pointer may execute before the tag check retires. If the speculative load touches a cache line that the attacker can observe via Flush+Reload, the attacker learns the memory content without triggering a tag fault. This is primarily a confidentiality concern (information leak) rather than an integrity attack, but leaked heap metadata can facilitate subsequent exploitation.

**MTE-bypassing data-only attacks.** MTE checks apply only to pointer dereferences tagged with MTE metadata (i.e., accesses through pointers whose top byte contains a tag, targeting `PROT_MTE` pages). Non-pointer data modifications are not subject to tag checks. An attacker who overflows into a non-pointer field (an integer length, a Boolean flag, a file descriptor number) in the same granule as the source allocation does not trigger an MTE fault — the write uses the source allocation's tag, which matches the source granule's allocation tag. Only when the overflow crosses a granule boundary (16 bytes) into a differently-tagged granule does MTE detect the violation.

This means sub-granule data-only overwrites are invisible to MTE. An adjacent 8-byte integer field within the same 16-byte granule can be corrupted silently. Allocator designs that place metadata inline with user data (old-style `dlmalloc` chunk headers) are particularly vulnerable — the attacker overwrites allocator metadata in the same granule as user data.

---

## 7. Microsoft CFG and XFG: bypass techniques

### 7.1 CFG bitmap internals

The CFG bitmap is a process-wide data structure allocated by the Windows loader at process initialization. It covers the entire user-mode address space (0 to 0x7FFFFFFFFFFF on x86_64). Each bit corresponds to an 8-byte-aligned address: bit N in the bitmap corresponds to address N × 8. If the bit is set, the address is a valid indirect-call target.

The bitmap is stored in a region allocated by `ntdll.dll` and pointed to by the process's `PEB.ProcessParameters->CfgBitmapSection`. The bitmap size is `(user_address_space_size / 8) / 8` bytes = approximately 64 GiB / 64 = 1 GiB for a 48-bit address space, but the OS uses sparse memory mapping (demand-paged) so only pages covering actually-loaded code are physically allocated.

The validation function is `ntdll!LdrpValidateUserCallTarget`, called by the CFG check stub inserted before each indirect call. The function:
1. Extracts the target address from the register.
2. Computes the bitmap index: `bit_index = target_address >> 3`.
3. Computes the byte offset and bit position within the bitmap.
4. Reads the corresponding byte from the bitmap.
5. Tests the bit. If clear, calls `RtlFailFast(FAST_FAIL_GUARD_ICALL_CHECK_FAILURE)`.

### 7.2 SetProcessValidCallTargets abuse

The Windows API `SetProcessValidCallTargets` (alias `VirtualProtect` with `PAGE_TARGETS_INVALID`/`PAGE_TARGETS_NO_UPDATE` flags, or via `ntdll!NtSetInformationVirtualMemory`) allows a process to modify its own CFG bitmap — adding or removing valid call targets. This exists for legitimate use cases: JIT compilers that generate new code at runtime need to mark the new code's entry points as valid CFG targets; sandbox implementations that need to restrict the call target set.

From an attacker's perspective, `SetProcessValidCallTargets` is an oracle of power: if the attacker can call this function with controlled arguments, they can mark any address as a valid CFG target, effectively disabling CFG. The attack requires the attacker to already have arbitrary code execution (to call the API), which means CFG has already been bypassed at least partially — but `SetProcessValidCallTargets` allows upgrading a limited execution primitive (e.g., a single controlled call to a valid function) into full CFG bypass.

Microsoft mitigates this by restricting `SetProcessValidCallTargets`:
- In Arbitrary Code Guard (ACG) mode, the API is blocked entirely.
- The function validates that the caller has the required process rights.
- In CET-shadow-stack-enabled processes, calling `SetProcessValidCallTargets` from an unexpected context triggers additional checks.

### 7.3 CFG bitmap corruption

If the attacker has an arbitrary write primitive (e.g., a heap overflow or use-after-free that allows writing to a controlled address), they can directly modify the CFG bitmap in memory. By setting the bit corresponding to their desired gadget address, they make that address a valid CFG target.

The attack requires knowing the bitmap's address in memory. The bitmap address is stored in the PEB and can be leaked via an information leak. Once known, the attacker computes the bit offset for their target address and writes a 1-bit into the bitmap.

Mitigation: Windows can map the CFG bitmap as read-only in user mode and use a system call to modify it (via `NtSetInformationVirtualMemory`), making direct bitmap corruption require a kernel-mode write. Modern Windows versions implement this — the bitmap pages are mapped read-only in the user address space, with a separate kernel-mode mapping that is read-write for the OS to update.

### 7.4 Return Flow Guard (RFG) — historical context

Microsoft developed Return Flow Guard (RFG) as a software shadow stack for backward-edge protection before CET hardware was available. RFG stored return addresses in a separate "return address shadow" region and validated them on function return. However, RFG was never shipped in a stable Windows release — it was present in some Insider builds but was withdrawn due to performance issues and compatibility problems. CET shadow stacks superseded RFG as the backward-edge protection mechanism.

### 7.5 XFG type-hash internals and bypass

XFG extends CFG by adding a type hash before each indirect call target. The compiler computes a hash of the function prototype (return type + argument types) and stores it as an 8-byte value immediately before the function's first instruction. The XFG check validates both:
1. The target address is in the CFG bitmap (forward-edge validity).
2. The 8-byte value at `[target - 8]` matches the expected type hash for the call site.

An XFG bypass requires finding a function with both:
- A matching type hash (same function prototype as expected by the call site).
- Useful behavior when called with attacker-controlled arguments.

Type hash collisions are the primary XFG bypass vector. The hash function is deterministic and based on the function prototype — two functions with identical prototypes have identical hashes. In a large binary with thousands of functions, many functions share prototypes (e.g., `void f(int)`, `int g(void*)`, etc.). The attacker scans the binary for functions with the target prototype that perform useful operations.

The hash space is 64 bits, making random collisions essentially impossible. But prototype collisions (two different functions with the same argument/return types) are common and are the realistic bypass path. Fine-grained type hashing (including parameter names or source-level information) could reduce collisions but is not implemented in current XFG.

### 7.6 CFG/XFG bitmap manipulation: practical techniques

The following code demonstrates offensive and defensive interactions with the CFG bitmap.

**Dumping the CFG bitmap from process memory.** The bitmap base address is stored in the PEB's `CfgBitmapSection`. A process with debug privileges (or the process itself) can read the bitmap and enumerate all currently-valid indirect call targets.

```c
/* cfg_bitmap_dump.c — CFG bitmap query. Windows x64. */
#include <windows.h>
#include <stdint.h>

/* Each bit = 8-byte-aligned address. bit_index = addr >> 3. */
static int is_cfg_valid(const uint8_t *bitmap, uint64_t address) {
    uint64_t idx = address >> 3;
    return (bitmap[idx >> 3] >> (idx & 7)) & 1;
}
/* Bitmap base: PEB → load config → GuardCFDispatchFunctionPointer,
 * or disassemble ntdll!LdrpValidateUserCallTarget.
 * Info leak of any PEB field → bitmap address → targeted corruption. */
```

**Whitelisting arbitrary addresses via SetProcessValidCallTargets.** If the attacker can call `SetProcessValidCallTargets` with controlled arguments (e.g., via a confused deputy or a limited code-execution primitive), they can mark any address as a valid CFG target.

```powershell
# cfg_whitelist.ps1 — SetProcessValidCallTargets abuse (P/Invoke).
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public struct CFG_CALL_TARGET_INFO { public UIntPtr Offset; public UIntPtr Flags; }
public class CfgHelper {
    public const uint CFG_CALL_TARGET_VALID = 1;
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool SetProcessValidCallTargets(
        IntPtr hProcess, IntPtr VA, UIntPtr Size, uint Count,
        [In,Out] CFG_CALL_TARGET_INFO[] Info);
    public static bool Whitelist(IntPtr baseAddr, ulong offset) {
        var info = new[] { new CFG_CALL_TARGET_INFO {
            Offset=new UIntPtr(offset), Flags=new UIntPtr(CFG_CALL_TARGET_VALID)} };
        return SetProcessValidCallTargets(new IntPtr(-1), baseAddr,
            new UIntPtr(0x1000), 1, info);
    }
}
"@
# Attack: compute offset of desired gadget and mark it valid.
# [CfgHelper]::Whitelist($moduleBase, 0x1234)
```

**XFG type-hash collision finder.** XFG hashes are deterministic from the function prototype. Finding functions with matching prototypes (and thus matching XFG hashes) in a binary gives the attacker a set of interchangeable targets for a given call site.

```python
#!/usr/bin/env python3
"""xfg_collision_finder.py — Find XFG type-hash collisions in PE binaries.
Requires: pefile >= 2023.2.7   Usage: python3 xfg_collision_finder.py ntdll.dll
"""
import sys, struct, pefile
from collections import defaultdict

def extract_xfg_hashes(pe_path):
    pe = pefile.PE(pe_path, fast_load=False); pe.parse_data_directories()
    lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG
    if not hasattr(lc.struct, "GuardCFFunctionTable"): return {}
    table_rva = lc.struct.GuardCFFunctionTable - pe.OPTIONAL_HEADER.ImageBase
    count = lc.struct.GuardCFFunctionCount
    stride = max((lc.struct.GuardFlags >> 28) & 0xF, 4)
    hmap = defaultdict(list)
    for i in range(count):
        rva = struct.unpack_from("<I", pe.get_data(table_rva + i*stride, 4))[0]
        try:
            xfg = struct.unpack("<Q", pe.get_data(rva - 8, 8))[0]
        except Exception: continue
        if xfg: hmap[xfg].append(rva)
    return hmap

if __name__ == "__main__":
    hmap = extract_xfg_hashes(sys.argv[1] if len(sys.argv)>1 else "ntdll.dll")
    multi = {h: r for h, r in hmap.items() if len(r) > 1}
    print(f"Unique hashes: {len(hmap)}  Collision sets: {len(multi)}")
    for h, rvas in sorted(multi.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"  0x{h:016x} — {len(rvas)} funcs: "
              + " ".join(f"0x{r:08x}" for r in rvas[:8]))
```

**CFG bitmap corruption via write primitive.** Given an arbitrary write (e.g., from a heap overflow), the attacker targets the CFG bitmap directly. The bitmap is mapped read-only in user space on modern Windows, so this attack requires either a kernel write primitive or exploitation of a time-of-check/time-of-use race during bitmap updates. Pre-Windows-10-1709 systems mapped the bitmap read-write in user space, making direct corruption trivial.

---

## 8. grsecurity RAP: deep internals

Chapter 4A provided a single-paragraph summary of RAP. This section expands on the mechanism because RAP represents the most mature production CFI system for the Linux kernel.

### 8.1 Forward-edge RAP

RAP's forward-edge protection instruments every indirect call with a type-hash check. At compile time, the GCC RAP plugin computes a 64-bit hash of each function's prototype (return type + argument types + calling convention). This hash is stored as a 64-bit value immediately before each function's entry point in the compiled binary (at `function_address - 8`).

At each indirect call site, the compiler inserts a check sequence:
1. Load the 8-byte value at `[target - 8]`.
2. Compare it with the expected hash for this call site's function type.
3. If mismatch, trigger a RAP violation (kernel panic in kernel mode, `SIGKILL` in user mode).

The check is inlined at each call site, with no bitmap lookup or jump-table indirection. This makes RAP checks extremely fast (a single memory load and compare, typically 2-3 cycles) but requires knowledge of the target's hash at compile time.

RAP's 64-bit hash space is vastly larger than XFG's type hash, making random collisions infeasible. Prototype collisions (different functions with identical signatures) remain possible, as with XFG, but the 64-bit width means the attacker must find an exact prototype match, not just a partial collision.

### 8.2 Backward-edge RAP (return address protection)

RAP's backward-edge protection encrypts return addresses on the stack using a per-thread random key XOR'd with a function-specific value. On function entry, the return address is encrypted (XOR with the key) and stored. On function return, the stored value is decrypted and compared with the actual return address. Corruption of the return address produces a mismatch.

This is functionally similar to a software shadow stack but implemented through encryption rather than a separate stack. The security depends on the key remaining secret: if the attacker can leak the RAP key (via a memory read primitive), they can forge encrypted return addresses. The key is stored in a per-thread location that RAP protects from information leaks through additional hardening (ASLR of the key storage, guard pages around the key).

### 8.3 RAP deployment and limitations

RAP is available only through grsecurity's commercial patch set. It requires recompilation of the entire kernel and all kernel modules with the RAP-enabled GCC plugin. This limits adoption to organizations that use grsecurity — primarily high-security environments (government, defense, financial institutions) that require the strongest available kernel hardening.

RAP's main technical limitation is its interaction with kernel function pointers that are resolved at load time (e.g., `struct file_operations` vtable-like patterns in the Linux kernel). The kernel uses many indirect calls through struct function pointers, and each must have a matching RAP hash. The grsecurity patch set includes the necessary annotations for mainline kernel interfaces, but third-party kernel modules may require modification.

---

## 9. Clang CFI: internals and bypass

### 9.1 Type metadata encoding

Clang CFI's forward-edge protection (`-fsanitize=cfi-icall`, `-fsanitize=cfi-vcall`) uses LLVM's type metadata system to classify functions and call sites. At compile time, LLVM generates type metadata for each function and each indirect call/virtual call site:

For `cfi-icall` (C indirect calls), the type metadata is the function's C type signature. All functions with the same signature share a type identifier (`typeid`). The compiler generates a bitset (or a range check) for each `typeid`, listing all functions of that type. At each indirect call, the compiler inserts a check: "is the target address in the set of functions with typeid matching this call site's expected function type?"

For `cfi-vcall` (C++ virtual calls), the type metadata is the class hierarchy at the call site. A call to `Base::foo()` has a typeid that includes `Base::foo`, `Derived1::foo`, and `Derived2::foo` — all overrides in the hierarchy. The check ensures the target is one of these methods.

### 9.2 Jump-table implementation

In the default Clang CFI implementation, the type check is implemented via **jump tables**. The compiler creates a jump table for each typeid: a contiguous block of `jmp` instructions, one per valid target function. The indirect call is redirected to go through the jump table, and the check validates that the target address falls within the jump table's address range.

This implementation has the advantage of being a simple range check (fast) and providing exact type enforcement (no hash collisions). But it has a cost: every valid indirect-call target must have an entry in a jump table, which increases code size. And the jump-table entries themselves are indirect jumps, which interact with IBT (each entry must begin with `ENDBR64` on CET platforms).

An alternative implementation uses bitsets: each typeid has a bitset indicating which addresses are valid targets. This is more compact but requires a memory lookup for the check.

### 9.3 Cross-DSO CFI

Clang CFI's default mode requires whole-program visibility (LTO — Link-Time Optimization) to know all valid targets for each typeid. This fails when the program uses shared libraries (DSOs) that are compiled separately.

Cross-DSO CFI (`-fsanitize-cfi-cross-dso`) addresses this by inserting a slow-path check function (`__cfi_slowpath`) that is called when the target address is outside the current DSO's known range. `__cfi_slowpath` looks up the target in a global registry maintained by the dynamic linker, checking whether the target is a valid function of the expected type in any loaded DSO.

This is slower than the intra-DSO check (hash lookup vs. range check) and requires coordination between the compiler, linker, and runtime. Android uses cross-DSO CFI for system libraries.

### 9.4 CFI bypass through type confusion within valid sets

Clang CFI enforces type-correct dispatch: an indirect call through `void (*)(int)` can only reach functions with signature `void f(int)`. But within that valid set, the attacker can choose any function. If two functions with the same signature perform very different operations — one is benign, one is security-relevant — the attacker can redirect the call to the security-relevant function with attacker-controlled arguments.

This is the same attack pattern as ENDBR-gadget harvesting (§2.1) and XFG type-hash collision (§7.5), applied at the CFI level. The defense is to narrow the valid set further — ideally to a single target (monomorphic dispatch), which is achievable in some cases through devirtualization (where the compiler can prove that only one implementation of a virtual method is reachable).

For `cfi-vcall`, type confusion can occur through incorrect type casts: if the program casts an object to the wrong base class (via `reinterpret_cast` or a union), the vtable pointer may point to a valid vtable of the wrong class, and the CFI check passes because the target method is a valid method of a class in the (incorrect) hierarchy. This is a vulnerability in the program rather than in CFI, but CFI's protection is bounded by the program's type safety.

### 9.5 Shadow call stack bypass

Clang's shadow call stack (`-fsanitize=shadow-call-stack`) on AArch64 stores return addresses in a region pointed to by register `x18`. The security of this scheme depends on `x18` being reserved and not clobberable by the attacker. If the attacker has an arbitrary-write primitive, they can:
1. Overwrite the shadow call stack's return address at `[x18 + offset]` to match their desired hijack target.
2. Overwrite the normal stack's return address to the same value.
3. The shadow call stack check passes (both stacks agree), and the hijack succeeds.

This attack requires the attacker to know both the `x18` value (the shadow call stack base) and the current offset within it. ASLR provides some protection (the shadow call stack's base address is randomized), but an information leak that reveals any pointer into the shadow call stack region reveals the base (because the shadow call stack is a contiguous allocation).

The software shadow call stack is explicitly weaker than CET's hardware shadow stack because the hardware shadow stack uses special page-table permissions that prevent non-shadow-stack writes, while the software shadow call stack uses ordinary memory that is writable by any `MOV` instruction. The software version is a pragmatic defense on hardware without CET, not a substitute for it.

---

## 10. Detection engineering for control-flow attacks

### 10.1 ROP chain detection via stack analysis

A ROP chain produces a distinctive call stack pattern: many return addresses in rapid succession, each pointing to a different code region, with each "frame" containing only 1-3 instructions before the next `ret`. This contrasts with legitimate call stacks, where each frame represents a full function with dozens to thousands of instructions.

**Stack unwinding heuristics**: a monitoring agent can capture the call stack (via `libunwind`, `/proc/[pid]/stack` on Linux, or ETW `StackWalk` events on Windows) and analyze frame sizes. If the stack contains many consecutive frames with tiny (< 16 bytes) instruction spans between return addresses, this is a strong ROP indicator. Legitimate code occasionally has small frames (leaf functions, trampoline stubs), but a sequence of 10+ consecutive tiny frames is anomalous.

**Implementation**: on Linux, this can be monitored via `perf` hardware performance counters or via eBPF programs attached to the `perf_event` subsystem. The eBPF program captures the LBR (Last Branch Record) buffer on each context switch or at periodic intervals and looks for return-branch patterns with many consecutive short inter-branch distances.

On Windows, the `Microsoft-Windows-Threat-Intelligence` ETW provider and Windows Defender's Advanced Threat Protection (ATP) sensor monitor for ROP indicators using hardware-assisted techniques.

### 10.2 Hardware performance counter anomalies

Modern CPUs maintain hardware performance counters that can be programmed to count specific events. Several events are diagnostic of code reuse attacks:

**Retired return branches (`BR_RET_RETIRED`)**: a ROP chain executes an abnormally high number of `ret` instructions relative to `call` instructions. The ratio of returns to calls should be approximately 1:1 in legitimate code; a significantly higher ratio indicates ROP.

**Last Branch Record (LBR)**: the LBR is a circular buffer of the most recent branch source/destination pairs, maintained by the CPU. On Intel CPUs, the LBR can store up to 32 entries (depending on the microarchitecture). Capturing the LBR on an anomalous event (e.g., a syscall from an unexpected address) reveals the control-flow history leading to the event. A LBR full of `ret` branches to non-function-entry addresses is a definitive ROP indicator.

**Branch misprediction rate**: ROP chains follow a non-standard control-flow pattern that the branch predictor cannot predict (each `ret` goes to a different address). This causes an abnormally high branch misprediction rate. However, this is a noisy signal — high misprediction rates also occur during hash-table lookups, interpreter dispatch loops, and other legitimate workloads.

**Intel PEBS (Precise Event-Based Sampling)**: PEBS captures the precise instruction pointer, register state, and memory address for sampled events. Combined with return-branch counting, PEBS can identify the exact ROP gadget sequence.

### 10.3 CET violation telemetry

On CET-enabled systems, control-flow violations generate `#CP` exceptions (vector 21). The exception handler can log the violation before terminating the process, providing a rich detection signal.

The `#CP` exception pushes an error code that distinguishes the violation type:
- Bit 0 (`ENCL`): violation occurred inside an SGX enclave.
- Bits 14:1: encoded violation type — near `RET` (shadow stack mismatch), far `RET`, `RSTORSSP` token failure, or `ENDBR` missing.

On Linux, `#CP` is handled by `exc_control_protection` in `arch/x86/kernel/traps.c`. The handler delivers `SIGSEGV` with `si_code = SEGV_CPERR` to the faulting process. A monitoring agent can install a `SIGSEGV` handler (or monitor audit logs for `SEGV_CPERR`) to detect CET violations.

On Windows, CET violations are logged via ETW under the `Microsoft-Windows-Security-Mitigations` provider with event IDs specific to CET. Windows Defender ATP correlates these events with process context (binary reputation, parent process, user identity) to distinguish exploitation attempts from compatibility issues.

### 10.4 ETW-based control flow monitoring on Windows

Windows Event Tracing provides several event sources relevant to control-flow attack detection:

**`Microsoft-Windows-Security-Mitigations`** (provider GUID `{B3E2F6D7-...}`): logs CFG violations, CET violations, ASLR failures, and other mitigation-related events. Event ID 12 covers CFG check failures; Event ID 1 covers CET shadow stack violations. Each event includes the faulting process, thread, instruction pointer, and target address.

**`Microsoft-Windows-Threat-Intelligence`**: a restricted provider (requires PPL — Protected Process Light — or kernel-mode access) that logs detailed exploitation telemetry, including ROP heuristic triggers, stack pivot detection, and token manipulation.

**StackWalk events**: the `EventTrace` session can capture call stacks on arbitrary events (syscalls, allocation events, page faults). Correlating call stacks from security-sensitive operations (e.g., `CreateProcess`, `VirtualProtect`, `NtWriteVirtualMemory`) with the expected call patterns for that process identifies anomalous control flow.

### 10.5 CFI violation crash analysis

When a CFI-protected program crashes due to a CFI check failure, the crash dump contains forensic evidence:

**Clang CFI**: the process receives `SIGILL` (illegal instruction) from the `ud2` trap inserted by the CFI check. The crash address is the `ud2` instruction, and the preceding instructions reveal the CFI check type (the `typeid` being validated and the target address that failed validation). The `cfi-icall` check uses an in-bounds check on a jump table; the out-of-bounds target address is in the register being checked.

**CFG**: the process calls `RtlFailFast(FAST_FAIL_GUARD_ICALL_CHECK_FAILURE)` (fail fast code 10) or `FAST_FAIL_GUARD_SS_FAILURE` (code 27 for shadow stack). The crash dump shows the failing function pointer in the register and the CFG bitmap state.

**CET**: the `#CP` exception pushes an error code identifying the specific violation. The crash dump includes the expected return address (from the shadow stack) and the actual return address (from the regular stack), which reveals the attacker's intended hijack target.

Forensic analysis of CFI crashes can distinguish exploitation attempts from bugs:
- If the mismatching target address is a function like `system`, `execve`, `WinExec`, or `VirtualAlloc`, this is a strong exploitation indicator.
- If the mismatching target is in a JIT-generated code region or in a library that was recently loaded, it may be a compatibility issue.
- If the crash occurs in a context associated with known vulnerability types (e.g., during JavaScript execution, during deserialization, during image parsing), it is worth investigating as an exploitation attempt even if the target address is not obviously malicious.

### 10.6 Kernel-level control flow anomaly detection

Kernel control-flow attacks (hijacking kernel return addresses or function pointers) can be detected through several mechanisms:

**eBPF-based monitoring**: eBPF programs attached to tracepoints and kprobes can monitor kernel function call patterns. A `kretprobe` can verify that the return address is within the expected code region for the function being returned from. Anomalous returns (to addresses outside the kernel text, or to addresses in the middle of a function rather than a call site) indicate kernel ROP.

**LKRG (Linux Kernel Runtime Guard)**: an open-source kernel module that monitors kernel code integrity and process credential integrity. LKRG detects kernel code modification (code-injection attacks), kernel ROP (via integrity checks on critical kernel data structures), and privilege escalation (by monitoring `task_struct.cred` changes). It is not a CFI mechanism but provides complementary detection.

**Crash dump analysis**: kernel oops/panic messages include the call stack trace. A kernel ROP chain that culminates in a kernel panic produces a call trace with many tiny frames and returns to mid-function addresses. Automated crash dump analysis (e.g., via Linux `kdump`/`crash` or Windows kernel debugger) can identify these patterns.

**Hypervisor-based monitoring**: a hypervisor can monitor the guest kernel's control flow using hardware virtualization extensions (Intel VT-x, AMD-V). The hypervisor can trap on specific events (CR3 writes, MSR access, interrupt delivery) and validate the kernel's call stack at each trap. This is the basis for hypervisor-based introspection tools like Xen's IntroCore and KVM-based introspection frameworks.

### 10.7 Sigma rules for CFI violation detection

The following Sigma rules detect CFI-related events in enterprise environments. They target Windows ETW telemetry and Linux audit subsystem events.

```yaml
# sigma_cet_shadow_stack_violation.yml
title: CET Shadow Stack Violation Detected
id: a3f1e9b2-7c4d-4a8e-b5f1-2d9e8c3a7b01
status: experimental
description: Shadow stack mismatch — ROP attempt or non-CET code compat issue.
logsource:
    product: windows
    service: security-mitigations  # {FAE10392-F0AF-4AC0-B8FF-9F4D920C3CDF}
detection:
    selection: { EventID: 1 }
    filter: { ProcessName|endswith: ['\java.exe', '\dotnet.exe'] }
    condition: selection and not filter
falsepositives: [Legacy JIT apps, Debuggers manipulating return addresses]
level: high
tags: [attack.execution, attack.t1055]
```

```yaml
# sigma_cfg_check_failure.yml
title: Windows CFG Check Failure
id: b8e2d4a1-5f3c-4b9d-a7e2-1c8f6d5a9b03
status: experimental
description: Indirect call target not in CFG bitmap — exploit or corruption.
logsource: { product: windows, service: security-mitigations }
detection:
    selection: { EventID: 12 }
    condition: selection
level: high
tags: [attack.execution, attack.t1574]
```

```yaml
# sigma_linux_cfi_crash.yml
title: Linux CFI/CET Process Crash
id: c7d3e5b2-8a1f-4c6e-b9d3-3e7a2f1c8d05
status: experimental
description: SIGSEGV (SEGV_CPERR from CET) or SIGILL (Clang CFI ud2 trap).
logsource: { product: linux, service: audit }
detection:
    sel_cet: { type: ANOM_ABEND, sig: '11' }
    sel_cfi: { type: ANOM_ABEND, sig: '4' }
    condition: sel_cet or sel_cfi
falsepositives: [Normal segfaults — tune with process allowlists]
level: medium
tags: [attack.execution, attack.t1203]
```

### 10.8 YARA rules for CFI enforcement gaps and bypass tools

```yara
rule elf_missing_cet_ibt {
    meta: description = "ELF missing GNU_PROPERTY_X86_FEATURE_1_IBT"
    strings:
        $elf = { 7f 45 4c 46 }
        $ibt = { 02 00 00 c0 04 00 00 00 (01|03|05|07) }
    condition: $elf at 0 and not $ibt
}

rule elf_aarch64_missing_bti {
    meta: description = "AArch64 ELF missing BTI property"
    strings:
        $elf = { 7f 45 4c 46 }
        $arm = { b7 00 }  /* EM_AARCH64 */
        $bti = { 00 00 00 c0 04 00 00 00 (01|03|05|07) }
    condition: $elf at 0 and $arm and not $bti
}

rule cfi_bypass_toolkit_strings {
    meta: description = "CFI bypass exploit tool indicators"
    strings:
        $a = "ENDBR64 gadget" ascii wide
        $b = "shadow_stack_desync" ascii wide
        $c = "pac_oracle" ascii wide
        $d = "wrss_gadget" ascii wide
        $e = "cfg_bitmap_corrupt" ascii wide
        $f = "SetProcessValidCallTargets" ascii wide
        $r1 = "ropper" ascii  $r2 = "ROPgadget" ascii
    condition: 3 of ($a,$b,$c,$d,$e,$f) or any of ($r1,$r2)
}

rule pe_missing_cfg {
    meta: description = "PE without CFG (IMAGE_GUARD_CF_INSTRUMENTED)"
    condition:
        uint16(0) == 0x5A4D and
        not (uint32(uint32(0x3C) + 0x84) & 0x100 != 0)
}
```

### 10.9 eBPF programs for Linux CET/BTI monitoring

On Linux, eBPF programs attached to tracepoints and perf events provide real-time visibility into CFI violations without requiring kernel modifications.

```c
/* cet_monitor.bpf.c — eBPF: monitor CET/BTI faults on Linux 6.6+.
 * Build: clang -target bpf -O2 -g -c cet_monitor.bpf.c -o cet_monitor.bpf.o */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct cfi_event {
    __u32 pid; __u32 tid; __u64 ip;
    __u32 violation; /* 0=shadow stack, 1=IBT/CFI */
    char comm[16];
};

struct { __uint(type, BPF_MAP_TYPE_RINGBUF); __uint(max_entries, 256*1024); } events SEC(".maps");

/* Attach to signal delivery — CET=#CP→SIGSEGV(11), Clang CFI→SIGILL(4) */
SEC("tp/signal/signal_deliver")
int trace_cfi_signal(struct trace_event_raw_signal_deliver *ctx) {
    if (ctx->sig != 11 && ctx->sig != 4) return 0;
    struct cfi_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->tid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
    e->violation = (ctx->sig == 11) ? 0 : 1;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    bpf_ringbuf_submit(e, 0);
    return 0;
}
char LICENSE[] SEC("license") = "GPL";
```

### 10.10 Windows ETW queries for CFG violations

The `Microsoft-Windows-Security-Mitigations` provider (GUID `{FAE10392-F0AF-4AC0-B8FF-9F4D920C3CDF}`) emits events for CFG check failures, CET violations, and ACG enforcement actions. The following `xperf`/`wpr` trace captures CFG-relevant events:

```powershell
# ETW trace for CFG/CET violations (requires admin).
logman create trace CFI_Monitor `
    -p "Microsoft-Windows-Security-Mitigations" 0xFFFFFFFF 0xFF `
    -o C:\Traces\cfi_monitor.etl -f bincirc -max 512
logman start CFI_Monitor
# Stop: logman stop CFI_Monitor

# Query CFG/CET events: 1=CET, 12=CFG, 13=XFG
Get-WinEvent -FilterHashtable @{
    ProviderName='Microsoft-Windows-Security-Mitigations'; Id=1,12,13
} -MaxEvents 50 | Format-Table TimeCreated, Id, Message -AutoSize
```

### 10.11 Falco/Tetragon rules for runtime CFI monitoring

Container and Kubernetes environments benefit from runtime security tools that can observe CFI-related signals at the system call and kernel level.

```yaml
# falco_cfi_violations.yaml
- rule: CET or CFI Process Crash
  desc: Detect process killed by SIGSEGV (#CP) or SIGILL (Clang CFI ud2).
  condition: >
    evt.type = signaldeliver and (evt.arg.sig = 11 or evt.arg.sig = 4)
    and not proc.name in (known_crashy_procs)
  output: "CFI violation (proc=%proc.name pid=%proc.pid sig=%evt.arg.sig)"
  priority: WARNING
  tags: [exploit, cfi]

- rule: Shadow Stack Syscall from Unexpected Process
  desc: arch_prctl modifying CET config outside initialization.
  condition: >
    evt.type = prctl and evt.arg[0] in (0x5001,0x5002,0x5003,0x5004)
    and not proc.name in (ld-linux, libc_init)
  output: "Shadow stack change (proc=%proc.name prctl=%evt.arg[0])"
  priority: NOTICE
  tags: [exploit, cet]
```

```yaml
# tetragon_cfi_policy.yaml — Cilium Tetragon kprobe + tracepoint.
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: cfi-violation-monitor
spec:
  kprobes:
    - call: "exc_control_protection"  # Fires on every #CP (CET)
      syscall: false
  tracepoints:
    - subsystem: signal
      event: signal_deliver
      args: [{index: 0, type: int, label: sig}]
      selectors:
        - matchArgs:
            - {index: 0, operator: In, values: ["4","11"]}
```

---

## 11. Real-world exploitation case studies against CFI

### 11.1 CVE-2022-42856: WebKit type confusion bypassing PAC on iOS

CVE-2022-42856, exploited in the wild against iOS 15 and patched in iOS 16.1.2 (December 2022), was a type confusion vulnerability in WebKit's JavaScript engine (JavaScriptCore). The vulnerability allowed an attacker to create a type-confused object in JIT-compiled JavaScript, providing an arbitrary read/write primitive.

On Apple Silicon (M1/M2), WebKit runs with full PAC enforcement — return addresses are signed, JIT-generated code includes PAC instructions, and critical function pointers are PAC-protected. The exploit authors bypassed PAC using a signing gadget within JavaScriptCore's JIT compilation infrastructure: they leveraged the JIT compiler's own code-generation path to emit a PAC-signed function pointer pointing to their controlled payload. Because the JIT compiler legitimately signs function pointers for the code it generates, and the attacker controlled what code the JIT compiled, the attacker effectively got the JIT to sign their exploit payload.

This demonstrates the fundamental tension in JIT+PAC: the JIT compiler must have the ability to create signed pointers (otherwise it can't generate callable code), and that ability can be abused if the attacker controls the JIT input.

Apple's mitigation in iOS 16.2+ includes tighter JIT code-signing restrictions (the JIT can only sign pointers within its designated code region, preventing cross-region signing) and additional type checks that prevent the type confusion from occurring.

### 11.2 CVE-2023-38606: kernel PAC bypass via data-only attack on Apple XNU

CVE-2023-38606, part of the "Operation Triangulation" exploit chain disclosed by Kaspersky in 2023, targeted the Apple XNU kernel on devices with PAC (A12+ chips). The exploit chain included a kernel vulnerability that allowed arbitrary kernel memory read/write. Rather than hijacking kernel control flow (which would require forging PAC-signed return addresses or function pointers), the attackers used a data-only attack: they modified the kernel's page table entries to remap physical memory, gaining access to MMIO (Memory-Mapped I/O) regions that allowed them to disable hardware mitigations including PAC and AMCC (Apple Memory Controller Cache).

This is the canonical data-only bypass of PAC: the attacker never forges a PAC, never hijacks control flow, and never triggers a PAC violation. Instead, they modify data structures (page tables, configuration registers) that grant them sufficient power to disable PAC entirely. PAC cannot prevent attacks that operate entirely in the data plane.

The defensive implication: PAC protects control flow but not data. Systems that rely on PAC for kernel security must also protect critical data structures (page tables, configuration registers, credential structures) via additional mechanisms — PPL (Page Protection Layer) on Apple Silicon, KDP (Kernel Data Protection) on Windows, or hypervisor-based memory integrity (HVCI) on x86.

### 11.3 CVE-2024-21338: Windows kernel CFG bypass via data-only attack

CVE-2024-21338, exploited by the Lazarus Group (DPRK-attributed) and patched in February 2024, was a vulnerability in the Windows `appid.sys` driver (AppLocker). The exploit gained kernel arbitrary read/write and used a data-only attack pattern to escalate privileges: modifying the `_TOKEN` structure in the exploit's own process to elevate privileges to SYSTEM, without hijacking any kernel control-flow pointers.

This bypass is CFG-irrelevant: the exploit never calls a function through a corrupted pointer, never triggers a CFG check, and never generates a CET violation. CFG and CET remain intact throughout the exploit — they simply protect a plane (control flow) that the attacker doesn't need to compromise.

The pattern is consistent across platforms: as CFI deployment matures, sophisticated attackers pivot to data-only techniques. Detection must shift accordingly — monitoring for anomalous privilege changes (`_TOKEN` modification, `cred` struct changes on Linux), anomalous page-table modifications, and unexpected MMIO access, rather than relying solely on control-flow violation telemetry.

### 11.4 Quantifying CFI's impact on exploit development cost

Empirical research (Google Project Zero's annual "0-day in the wild" analyses) shows that exploit chains targeting CFI-enabled platforms require approximately 2-3 additional vulnerabilities compared to pre-CFI platforms:
- One vulnerability for the initial corruption (as before).
- One vulnerability for an information leak to bypass ASLR (as before).
- One or more additional vulnerabilities or techniques to bypass CFI: a signing gadget, a data-only path, or a JIT manipulation.

This increases the attacker's cost (more vulnerabilities to discover or purchase, more complex exploit engineering) and decreases reliability (more moving parts, more race conditions, more failure modes). CFI does not prevent exploitation in absolute terms, but it imposes a measurable cost that reduces the number of capable adversaries and the frequency of successful attacks.

---

## 12. Combined defense analysis: residual attack surface

The combination of CET (IBT + shadow stack), PAC + BTI, MTE, CFG/XFG, and Clang CFI creates a layered defense that eliminates most practical code-reuse attacks. Understanding the residual attack surface after full deployment is critical for defense planning.

### 12.1 Attack surface with full CET (IBT + SHSTK)

With both IBT and shadow stack enabled, the attacker cannot:
- Use ROP (shadow stack detects return address corruption).
- Use JOP/COP with non-ENDBR targets (IBT rejects them).
- Use SROP (shadow stack token validation rejects forged sigframes).

The attacker can:
- Call any ENDBR-tagged function via a corrupted function pointer (ENDBR-gadget attacks).
- Perform data-only attacks that don't hijack control flow.
- Exploit WRSS if it's enabled.
- Exploit JIT-engine CET-management bugs.

### 12.2 Attack surface with full PAC + BTI + MTE

With PAC on return addresses, BTI on indirect branches, and MTE on heap allocations, the attacker faces:
- PAC on return addresses prevents backward-edge hijack (unless PAC is brute-forced or cracked via PACMAN).
- BTI prevents forward-edge hijack to non-landing-pad addresses (but landing-pad set is large).
- MTE detects the heap corruption that provides the initial write primitive (with 15/16 probability per attempt).

Residual surface: the attacker needs a corruption primitive that evades MTE (sub-granule overflow, same-tag collision, or MTE-untagged memory region), then needs to crack PAC (via PACMAN or brute-force in forking servers), then needs to find a useful BTI-valid target. The combination makes reliable exploitation extremely difficult but not theoretically impossible.

### 12.3 Defense-in-depth recommendations

For maximum protection, deploy all available layers:
1. CET/PAC for control-flow integrity.
2. MTE for memory safety (catching the corruption primitive).
3. Clang CFI or XFG for fine-grained forward-edge type checking (narrowing the ENDBR-gadget set).
4. ASLR for information hiding (forcing an additional leak requirement).
5. Stack canaries as defense-in-depth (catching stack overflows that neither CET nor MTE covers, e.g., on non-MTE pages without shadow stacks).
6. W^X as the base layer (preventing code injection entirely).
7. Seccomp/sandbox for syscall restriction (limiting what even a successful hijack can do).

Monitor CET/CFI violation telemetry as a high-signal detection source. Each violation should trigger incident investigation — it indicates either an active exploitation attempt or a software compatibility issue, both of which require attention.

---

## 13. Platform deployment status (as of 2025)

### 13.1 Intel CET

CET shadow stacks are supported on Intel 12th-gen (Alder Lake, 2021) and later. IBT is supported on 11th-gen (Tiger Lake, 2020) and later, but practical deployment of kernel IBT started with Alder Lake. AMD supports CET-compatible shadow stacks on Zen 3 (2020) and later.

Linux kernel IBT: 6.2+ (default on Fedora 38+, Ubuntu 24.04+). Linux user-space shadow stacks: 6.6+ with glibc 2.39+. Windows 11: shadow stacks enabled for opt-in processes ("Hardware-enforced Stack Protection"). Microsoft Edge, Chrome, and Firefox support CET on Windows. Windows kernel CET (Kernel Mode Hardware-enforced Stack Protection): Windows 11 22H2+, enabled by default on compatible hardware.

### 13.2 ARM PAC and BTI

PAC: available on Apple M1+ (mandatory for all user-space code), Arm Cortex-A78+, Arm Neoverse V1+. Deployed on iOS 14+, macOS 12+, Android 12+ (kernel PAC). BTI: Apple M1+, Cortex-A78+. Deployed on Android 14+ (kernel BTI), macOS 12+.

`FEAT_FPAC`: Apple M3+, Arm Cortex-X4+. Closes the PACMAN speculative oracle.

### 13.3 ARM MTE

MTE: available on Google Tensor G3 (Pixel 8), Arm Cortex-X4+, Arm Neoverse V2+. Android 14+ supports MTE (opt-in per app via manifest flag `android:memtagMode`). Linux kernel MTE support: 5.10+ for user space, 5.12+ for KASAN-MTE. Chrome on Android supports MTE when available on the device.

Adoption is still early — MTE requires both hardware support and allocator integration. Google's Scudo allocator has full MTE support. musl libc has experimental MTE support. glibc MTE support is in development.

### 13.4 CFG/XFG

CFG: Windows 8.1+ (introduced 2014). Widely deployed — most Windows binaries compiled with MSVC since VS2015 include CFG metadata. XFG: Windows Insider builds since 2020, gradually rolling out to stable Windows 11 builds.

### 13.5 Clang CFI

Deployed on Android (system libraries compiled with `-fsanitize=cfi-*` since Android 9), Chrome OS, and Fuchsia. Available but not widely deployed on desktop Linux distributions.

---

## 14. CFI audit and deployment tools

Systematic CFI deployment requires tooling to assess which binaries in a running system have CFI enforcement and which represent gaps that an attacker can exploit.

### 14.1 Binary CFI coverage scanner

The following script scans all loaded shared objects in a running process and reports their CET, BTI, and PAC status by parsing ELF `PT_GNU_PROPERTY` notes and PE load configuration directories.

```bash
#!/usr/bin/env bash
# cfi_coverage_scan.sh — Scan all DSOs loaded in a process for CFI status.
# Usage: ./cfi_coverage_scan.sh <pid>
set -euo pipefail
PID="${1:?Usage: $0 <pid>}"

echo "=== CFI Coverage — PID $PID ($(date -u +%Y-%m-%dT%H:%M:%SZ)) ==="

mapfile -t libs < <(awk '$6!="" && $2~/x/{print $6}' "/proc/$PID/maps" | sort -u)
total=0; cet_ibt=0; cet_shstk=0; bti=0; pac=0; missing=()

for lib in "${libs[@]}"; do
    [ -f "$lib" ] || continue
    total=$((total + 1))
    props=$(readelf -n "$lib" 2>/dev/null || true)
    status=""
    echo "$props" | grep -q "IBT"   && { status+="IBT "; cet_ibt=$((cet_ibt+1)); }
    echo "$props" | grep -q "SHSTK" && { status+="SHSTK "; cet_shstk=$((cet_shstk+1)); }
    echo "$props" | grep -q "BTI"   && { status+="BTI "; bti=$((bti+1)); }
    echo "$props" | grep -q "PAC"   && { status+="PAC "; pac=$((pac+1)); }
    [ -z "$status" ] && { status="NONE"; missing+=("$lib"); }
    printf "  %-50s %s\n" "$(basename "$lib")" "$status"
done

echo ""
echo "Total: $total  IBT: $cet_ibt  SHSTK: $cet_shstk  BTI: $bti  PAC: $pac"
[ ${#missing[@]} -gt 0 ] && {
    echo "--- Weakest Links (no CFI — disable process-wide enforcement) ---"
    printf "  [!] %s\n" "${missing[@]}"
}
```

### 14.2 PE header CFG/XFG flag checker

```python
#!/usr/bin/env python3
"""pe_cfg_check.py — Check CFG/XFG/CET status of Windows PE binaries.
Requires: pefile >= 2023.2.7
Usage:    python3 pe_cfg_check.py C:\\Windows\\System32\\ntdll.dll
"""
import sys, pefile

# IMAGE_GUARD_* flags (winnt.h)
GF = {
    "CFG instrumented":  0x00000100, "CFG func table":    0x00000400,
    "Export suppression": 0x00008000, "Longjump table":    0x00010000,
    "XFG enabled":       0x00800000,
}

def check_pe(path):
    pe = pefile.PE(path, fast_load=False)
    pe.parse_data_directories()
    dc = pe.OPTIONAL_HEADER.DllCharacteristics
    print(f"\n{'='*60}\n CFG/XFG/CET: {path}")
    print(f"  ASLR: {'yes' if dc&0x40 else 'NO'}  "
          f"DEP: {'yes' if dc&0x100 else 'NO'}  "
          f"Guard CF: {'yes' if dc&0x4000 else 'NO'}")
    if not hasattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
        print("  [!] No load config — no CFG"); return
    lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
    gf = getattr(lc, "GuardFlags", 0)
    for name, mask in GF.items():
        print(f"    {name}: {'yes' if gf & mask else 'no'}")
    ext = getattr(lc, "DllCharacteristicsEx", 0)
    print(f"    CET compatible: {'yes' if ext & 0x1 else 'no'}")
    print(f"  CFG targets: {getattr(lc, 'GuardCFFunctionCount', 0)}\n")

if __name__ == "__main__":
    for p in sys.argv[1:]: check_pe(p)
```

### 14.3 MachO arm64e PAC configuration dumper

On macOS/iOS, arm64e binaries use PAC. The PAC configuration is encoded in MachO load commands and the `__auth_stubs` section.

```bash
#!/usr/bin/env bash
# macho_pac_check.sh — Dump PAC metadata from MachO.
set -euo pipefail
BINARY="${1:?Usage: $0 <macho-binary>}"
echo "=== MachO PAC: $(basename "$BINARY") ==="
otool -fv "$BINARY" 2>/dev/null | grep -q "arm64e" \
    && echo "  arm64e: PRESENT" || { echo "  arm64e: ABSENT"; exit 0; }
echo "  PAC instructions:"
otool -arch arm64e -tV "$BINARY" 2>/dev/null | \
    grep -coE '\b(paciasp|pacibsp|autiasp|autibsp|retab|braa|blraa)\b' || echo "  0"
codesign -d --entitlements :- "$BINARY" 2>/dev/null | \
    grep -i "pac\|jit\|allow-unsigned" || echo "  (no PAC entitlements)"
```

---

## 15. Hardening deployment guides

### 15.1 Linux CET enablement

**Requirements:** Linux 6.6+ (user SHSTK), 6.2+ (kernel IBT). Intel 12th-gen+ / AMD Zen 3+. glibc 2.39+ (shadow stack lifecycle, `INCSSP`-aware `longjmp`). All DSOs must be compiled with `-fcf-protection=full` or the dynamic linker disables CET process-wide.

**Kernel config:** `CONFIG_X86_USER_SHADOW_STACK=y`, `CONFIG_X86_KERNEL_IBT=y`, `CONFIG_ARCH_HAS_SHADOW_STACK=y`.

**Build:** `CFLAGS="-fcf-protection=full"` / `LDFLAGS="-Wl,-z,shstk -Wl,-z,ibt"`. Verify: `readelf -n ./binary | grep -E "IBT|SHSTK"`. Lock down at runtime: `arch_prctl(ARCH_SHSTK_LOCK, ARCH_SHSTK_SHSTK)`. Keep `WRSS` disabled unless the app is a JIT that requires it.

### 15.2 Linux BTI/PAC on AArch64

**Build:** `CFLAGS="-mbranch-protection=standard"` (equivalent to `bti+pac-ret`). **Kernel config:** `CONFIG_ARM64_BTI=y`, `CONFIG_ARM64_BTI_KERNEL=y`, `CONFIG_ARM64_PTR_AUTH=y`, `CONFIG_ARM64_PTR_AUTH_KERNEL=y`, `CONFIG_ARM64_MTE=y`. **Verify:** `readelf -n` for `GNU_PROPERTY_AARCH64_FEATURE_1_BTI`. The dynamic linker sets GP on executable pages only for BTI-declaring libraries.

### 15.3 Windows CET (HEST)

Windows 11 enables HEST for opt-in processes. Linker flag `/CETCOMPAT` (VS2019+) marks the PE as CET-compatible. For existing binaries, use IFEO registry key (`MitigationOptions`). Deploy in audit mode first (`AuditUserShadowStack`) to detect non-CET DLLs without termination, then `BlockNonCetBinaries` once all dependencies pass.

### 15.4 macOS PAC and Android MTE

**macOS PAC.** arm64e ABI required for full PAC enforcement. Apple restricts arm64e to platform binaries and entitled developers (macOS 15 / iOS 18). Third-party binaries default to arm64 (PAC instructions → NOPs).

**Android MTE.** Hardware: Pixel 8+, Cortex-X4+, kernel `CONFIG_ARM64_MTE=y`. App opt-in: `android:memtagMode="sync"` in manifest (`sync` = max security, 3-5% overhead; `async` = lower cost). Kernel MTE: `CONFIG_KASAN=y` + `CONFIG_KASAN_HW_TAGS=y`.

### 15.5 Compiler flag reference table

| Platform | Mechanism | Compiler | Linker | Verify |
|----------|-----------|----------|--------|--------|
| x86_64 Linux | CET | `-fcf-protection=full` | `-Wl,-z,shstk -Wl,-z,ibt` | `readelf -n` |
| x86_64 Linux | Clang CFI | `-fsanitize=cfi-icall -flto` | `-fuse-ld=lld` | `__cfi_check` sym |
| AArch64 Linux | BTI+PAC | `-mbranch-protection=standard` | (default) | `readelf -n` |
| AArch64 Linux | MTE | `-fsanitize=memtag-heap` | (default) | `readelf -d` |
| Windows x64 | CFG/XFG | `/guard:cf` or `/guard:xfg` | `/guard:cf` | `dumpbin /loadconfig` |
| Windows x64 | CET | (VS2019+ default) | `/CETCOMPAT` | PE DLL chars |
| macOS | PAC | `-arch arm64e` | (default) | `otool -fv` |
| Android | Clang CFI | `-fsanitize=cfi-*` | `-fuse-ld=lld` | `__cfi_slowpath` sym |

---

## 16. CVE reference table: CFI bypass in the wild

The following table catalogs CVEs involving bypass or evasion of hardware/software CFI mechanisms. Each entry identifies the target platform, the CFI mechanism defeated, and the bypass technique.

| CVE | Year | Platform | CFI Bypassed | Technique | CVSS |
|-----|------|----------|-------------|-----------|------|
| CVE-2022-42856 | 2022 | iOS M1/M2 | PAC | WebKit type confusion → JIT signing oracle | 8.8 |
| CVE-2023-38606 | 2023 | iOS/macOS A12+ | PAC (kernel) | Data-only: page table remap, disable PAC via MMIO (Op Triangulation) | 9.8 |
| CVE-2024-21338 | 2024 | Windows 11 | CFG, CET | Data-only: kernel R/W → TOKEN modification (Lazarus) | 7.8 |
| CVE-2023-4211 | 2023 | Android Mali | MTE | GPU driver UAF: MTE not enforced on GPU-mapped memory | 7.8 |
| CVE-2023-32434 | 2023 | iOS A12+ | PAC | XNU integer overflow → kernel R/W, chained with 38606 | 7.8 |
| CVE-2022-46689 | 2022 | macOS M1 | PAC | XNU COW race → code page replacement before re-sign | 7.0 |
| CVE-2021-30955 | 2021 | iOS/macOS | PAC | Kernel IPC type confusion → signed pointer context swap | 7.8 |
| CVE-2024-3159 | 2024 | Chrome/Win | CFG, CET | V8 type confusion → JIT ENDBR gadget control (Pwn2Own) | 8.8 |
| CVE-2023-2136 | 2023 | Chrome | Clang CFI | Skia overflow in non-CFI GPU process | 9.6 |
| CVE-2024-44308 | 2024 | macOS/iOS M-series | PAC | JSC JIT code gen → PAC bypass via JIT region signing | 8.8 |
| CVE-2022-32917 | 2022 | iOS/macOS | PAC (kernel) | Data-only privilege escalation, no PAC forgery needed | 7.8 |
| CVE-2023-41993 | 2023 | iOS A15+ | PAC | WebKit JIT type confusion → PAC-signed pointer gen | 9.8 |

The pattern is consistent: post-CFI attackers shift to JIT-mediated bypasses (using the JIT's signing capability as an oracle) or data-only attacks outside the control-flow plane. The most sophisticated chains (Operation Triangulation) combine both approaches.

---

## 17. Advanced CFI research and future directions

CFI mechanisms described in §1–§9 address *control-flow hijack* — they constrain indirect branch targets and verify return address integrity. Research increasingly focuses on attack classes that operate outside the control-flow plane, on the security semantics of JIT-compiled code, and on emerging hardware-software co-designs that tighten the residual gaps.

### 17.1 Data-oriented programming as a CFI-immune attack class

Data-oriented programming (DOP — see Domain 4, Chapter 4A §17E.2 for mechanism, gadget taxonomy, and BOPC tooling) is structurally invisible to every CFI scheme discussed in this chapter. CET shadow stacks verify return addresses; IBT verifies indirect branch landing pads; PAC signs control-flow pointers; Clang CFI type-checks indirect call targets. None of these mechanisms inspect *data* values consumed by legitimate instructions executing along legitimate control-flow paths.

DOP's immunity to CFI is not an implementation gap — it is an architectural boundary. CFI enforces a property ("the program follows a legal control-flow graph") that DOP does not violate. The program's control flow remains legal; only the data operands are attacker-controlled. This means:

- **Forward-edge CFI (IBT, BTI, CFG, XFG, Clang CFI):** every indirect call dispatches to a type-valid target. DOP does not use indirect calls — it chains data operations along existing, compiler-generated control flow.
- **Backward-edge CFI (shadow stacks, PAC on LR):** every return address is correct. DOP does not corrupt return addresses.
- **MTE:** detects the *initial* heap corruption that bootstraps a DOP chain (with 15/16 probability per attempt). MTE therefore constrains DOP's entry point, but once the attacker has a corruption primitive in MTE-untagged memory (file-backed mappings, GPU-shared regions, stack variables without stack MTE), the DOP chain proceeds undetected.

Automated DOP chain construction tools — BOPC (Ispoglou et al., 2018), Newton (Van der Veen et al., 2017) — demonstrate that DOP chains are practical against real-world binaries. The defensive response falls outside the CFI domain: memory safety languages (Rust, Swift), compartmentalization (process sandboxing, in-process isolation via MPK/CHERI), and data-flow integrity (DFI) enforcement.

### 17.2 JIT-based CFI bypass: writable code pages

JIT engines (V8, JavaScriptCore, SpiderMonkey, .NET RyuJIT, HotSpot C2) fundamentally require the ability to generate, sign, and execute code at runtime. This creates a structural tension with every CFI mechanism:

- **CET IBT:** the JIT must emit `ENDBR64` at every indirect branch target in generated code. If the attacker controls the JIT input (malicious JavaScript), they can influence *which* ENDBR-tagged functions exist and what they do — effectively constructing ENDBR gadgets by design.
- **PAC:** the JIT must sign function pointers for generated code using PAC keys. The JIT's signing capability becomes a *signing oracle* (see §11.1 for the CVE-2022-42856 case). Any vulnerability that allows the attacker to control JIT code emission allows them to generate PAC-signed pointers to arbitrary code.
- **CET shadow stack:** JIT engines that use on-stack replacement (OSR) or deoptimization must adjust the shadow stack when transitioning between JIT tiers. Bugs in this adjustment can desynchronize the shadow stack from the real stack.
- **W^X enforcement:** JIT code regions must be writable (during compilation) and executable (during execution). Modern JITs implement W^X by toggling page permissions (`mprotect(PROT_READ|PROT_WRITE)` → compile → `mprotect(PROT_READ|PROT_EXEC)`), but the transition window is a race condition target. Apple's Hardened Runtime on macOS requires `MAP_JIT` and the `pthread_jit_write_protect_np()` per-thread toggle, which restricts the writable window to the compiling thread.

Mitigations for JIT-based CFI bypass include:

1. **JIT code sandboxing** (V8 Sandbox, WebKit Gigacage): confine JIT-generated code and data to a bounded memory region so that corrupted JIT pointers cannot escape the sandbox.
2. **JIT-less modes** (`--jitless` in V8): eliminate writable code pages entirely, trading performance for security. Useful in high-security contexts (Node.js servers processing untrusted input).
3. **Constant blinding** and **NOP insertion**: randomize JIT-generated code layout to prevent the attacker from predicting gadget positions within JIT output.
4. **`FEAT_FPAC`** on AArch64: faults immediately on PAC authentication failure, closing the speculative oracle (PACMAN) that allows brute-forcing PAC values through the JIT.

### 17.3 Hardware-software co-design: CET + PAC combined deployment

No single platform currently deploys both Intel CET and ARM PAC (they target different ISAs), but the conceptual question — "what does the residual attack surface look like when both forward-edge and backward-edge hardware CFI are active, combined with memory tagging?" — guides platform convergence analysis.

On AArch64 with PAC + BTI + MTE deployed together (see §12.2), the attacker must:
1. Defeat MTE to obtain a corruption primitive (1/16 failure per attempt in sync mode).
2. Crack PAC to forge a return address or signed function pointer (2^16 brute-force for QARMA with the default key, mitigated by `FEAT_FPAC`).
3. Find a BTI-valid landing pad that is useful for the attack (constrained by the ENDBR/BTI equivalence class).
4. Chain the above without triggering kernel-level anomaly detection.

On x86_64 with CET IBT + shadow stack + Clang CFI (XFG), the attacker must:
1. Find an ENDBR-tagged gadget that also passes the XFG type-hash check.
2. Cannot use ROP (shadow stack blocks backward-edge hijack).
3. Is left with data-only attacks or JIT-based bypass.

**Arm CCA (Confidential Compute Architecture)** adds a Realm Management Extension (RME) that partitions physical memory into four security worlds: Secure, Non-secure, Root, and Realm. CCA's implications for CFI are indirect but significant:
- Realm memory is encrypted and integrity-protected by hardware, preventing physical attacks against PAC key storage.
- The Monitor (EL3) and Realm Management Monitor (RMM) enforce memory isolation that prevents a compromised hypervisor from tampering with guest CFI state (PAC keys, BTI configuration).
- CCA does not introduce new CFI mechanisms, but it hardens the trust anchors that existing CFI depends on (key material, configuration registers, page table integrity).

### 17.4 Academic research frontier

**Context-sensitive CFI (CsCFI):** traditional CFI allows any type-valid target at each call site regardless of execution history. Context-sensitive CFI restricts targets based on the calling context — the sequence of call sites that led to the current dispatch point. Van der Veen et al. (2015) demonstrated PathArmor, which uses hardware LBR to enforce path-sensitive CFI. Performance overhead remains high (5-18%) for deep context sensitivity, limiting production adoption.

**CFIXX (Burow et al., 2019):** targets C++ virtual dispatch specifically. CFIXX maintains a metadata table indexed by object identity (address) rather than type, ensuring that each `vptr` dereference dispatches through the vtable originally assigned to that specific object — not merely a type-compatible vtable. This defeats vtable reuse attacks where the attacker substitutes one legitimate vtable for another of a compatible type. Overhead: ~2% on SPEC CPU2006.

**uCFI (Hu et al., 2018):** uses Intel Processor Trace (PT) to reconstruct the complete control-flow trace offline and verify it against a pre-computed policy. uCFI achieves sub-percent runtime overhead by deferring verification to an asynchronous monitoring process that consumes PT packets. The tradeoff: violations are detected after the fact rather than prevented inline, making uCFI a detection mechanism rather than an enforcement mechanism.

**PACStack (Liljestrand et al., 2021):** extends PAC to protect the entire call stack by chaining PAC signatures — each frame's return address is signed with a modifier that includes the previous frame's PAC. This creates a cryptographic chain: tampering with any frame invalidates all subsequent frames' PAC values. PACStack provides backward-edge CFI with context sensitivity (the PAC depends on the full call path) at low overhead (~3%) on AArch64 hardware with PAC support.

**Forward-edge PAC (Google, 2023):** extends PAC signing to indirect call targets using a discriminator derived from the call-site address plus the callee's type hash. This narrows the equivalence class of valid targets at each call site beyond what BTI alone provides, approaching the granularity of Clang CFI but with hardware enforcement and near-zero overhead.

---

## 18. CFI detection engineering enhancement

Section 10 established detection fundamentals (Sigma rules, YARA, eBPF, ETW, Falco/Tetragon). This section adds hardware-specific exception signals, platform-specific tracepoints, and behavioral analytics that increase detection fidelity for CFI bypass attempts.

### 18.1 CET shadow stack violation signals: #CP error code decomposition

The `#CP` exception (vector 21) pushes an error code whose bit layout identifies the specific violation:

| Bits | Field | Meaning |
|------|-------|---------|
| 0 | `ENCL` | Fault inside SGX enclave |
| 14:1 | Type | 1 = NEAR-RET (shadow stack mismatch on `ret`), 2 = FAR-RET/IRET, 3 = `ENDBR` missing (IBT violation), 4 = `RSTORSSP` token invalid |

Detection rule targeting IBT-specific violations (`ENDBR` missing):

```yaml
# sigma_cet_ibt_endbr_missing.yml
title: CET IBT Violation — ENDBR Missing at Branch Target
id: d4e7f1a3-9b2c-4f5e-a8d1-6c3e9f2b7a04
status: experimental
description: |
  #CP exception with error code type=3 indicates an indirect branch
  landed on an instruction that is not ENDBR64/ENDBR32. High-confidence
  indicator of JOP/COP attack or non-IBT binary injection.
logsource:
    product: windows
    service: security-mitigations
detection:
    selection:
        EventID: 1
        ErrorCode|contains: 'IBT'  # Provider decodes type field
    condition: selection
falsepositives:
    - Legacy DLL injection (should be blocked by BlockNonCetBinaries)
    - Debugger-inserted breakpoints at non-ENDBR locations
level: critical
tags: [attack.execution, attack.t1055.001]
```

### 18.2 PAC authentication failure exceptions (FEAT_FPAC)

On cores with `FEAT_FPAC` (Apple M3+, Cortex-X4+), PAC authentication failure generates a synchronous `FPAC` exception (ESR_EL1.EC = 0b011100 for instruction key, 0b011101 for data key) rather than silently producing an invalid pointer. This exception is the PAC equivalent of CET's `#CP`: a definitive signal that a control-flow pointer was forged or corrupted.

On Linux, the kernel handles `FPAC` exceptions in `do_ptrauth_fault()` (`arch/arm64/kernel/traps.c`), delivering `SIGILL` with `si_code = ILL_ILLOPN` and `si_addr` pointing to the faulting `AUT*` instruction. The following eBPF program captures these events:

```c
/* pac_fpac_monitor.bpf.c — Monitor FPAC (PAC auth failure) on AArch64.
 * Requires: Linux 6.2+, CONFIG_ARM64_PTR_AUTH=y, FEAT_FPAC hardware.
 * Build: clang -target bpf -O2 -g -c pac_fpac_monitor.bpf.c */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct fpac_event {
    __u32 pid; __u64 fault_addr; __u64 far_el1;
    char comm[16];
};

struct { __uint(type, BPF_MAP_TYPE_RINGBUF); __uint(max_entries, 128*1024); } events SEC(".maps");

/* FPAC faults route through do_ptrauth_fault → force_sig_fault(SIGILL) */
SEC("tp/signal/signal_deliver")
int trace_fpac(struct trace_event_raw_signal_deliver *ctx) {
    /* SIGILL=4 with ILL_ILLOPN=2 indicates FPAC on AArch64 */
    if (ctx->sig != 4) return 0;
    struct fpac_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    e->pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    bpf_ringbuf_submit(e, 0);
    return 0;
}
char LICENSE[] SEC("license") = "GPL";
```

### 18.3 MTE tag check failure patterns

MTE tag mismatches generate different signals depending on the checking mode:

- **Synchronous mode:** immediate Data Abort (ESR_EL1.DFSC = 0b010001, Tag Check Fault). The kernel delivers `SIGSEGV` with `si_code = SEGV_MTESERR`. The faulting address and expected/actual tags are available in FAR_EL1 and the MTE-specific syndrome register.
- **Asynchronous mode:** sets TFSRE0_EL1 (Tag Fault Status Register, EL0). The kernel polls TFSRE0_EL1 on kernel entry and delivers `SIGSEGV` with `si_code = SEGV_MTEASERR`. The faulting instruction is not precisely identified.

Detection rule for synchronous MTE violations:

```yaml
# sigma_mte_sync_tag_check_failure.yml
title: ARM MTE Synchronous Tag Check Failure
id: e5f8a2b4-1c3d-4e6f-b9a2-7d4c8e1f3a06
status: experimental
description: |
  SIGSEGV with SEGV_MTESERR indicates a synchronous MTE tag mismatch.
  In production deployments (Pixel 8+, Android 14+), this signals
  heap corruption exploitation — UAF or heap overflow against MTE.
logsource:
    product: linux
    service: audit
detection:
    selection:
        type: ANOM_ABEND
        sig: '11'
    filter_si_code:
        # SEGV_MTESERR = 9, SEGV_MTEASERR = 10
        si_code|contains: ['MTESERR', 'MTEASERR']
    condition: selection and filter_si_code
level: high
tags: [attack.execution, attack.t1203]
```

### 18.4 CFG/XFG dispatch failure events on Windows

CFG check failures invoke `RtlFailFast` with failure code `FAST_FAIL_GUARD_ICALL_CHECK_FAILURE` (10) for forward-edge violations and `FAST_FAIL_GUARD_SS_FAILURE` (27) for shadow stack violations. XFG failures use `FAST_FAIL_GUARD_ICALL_CHECK_FAILURE_XFG` (73).

ETW monitoring for XFG-specific failures (not covered in §10.10):

```powershell
# ETW query: XFG dispatch failures with process context
$xfgEvents = Get-WinEvent -FilterHashtable @{
    ProviderName = 'Microsoft-Windows-Security-Mitigations'
    Id = 13  # XFG-specific event ID
} -MaxEvents 100 -ErrorAction SilentlyContinue

foreach ($evt in $xfgEvents) {
    $xml = [xml]$evt.ToXml()
    $proc = $xml.Event.EventData.Data | Where-Object { $_.Name -eq 'ProcessName' }
    $target = $xml.Event.EventData.Data | Where-Object { $_.Name -eq 'TargetAddress' }
    $hash = $xml.Event.EventData.Data | Where-Object { $_.Name -eq 'TypeHash' }
    Write-Output "[$(Get-Date $evt.TimeCreated -Format 'o')] XFG FAIL: $($proc.'#text') target=0x$($target.'#text') expected_hash=0x$($hash.'#text')"
}
```

### 18.5 Clang CFI trap handler invocations

Clang CFI inserts `ud2` (x86) or `brk #0x1` (AArch64) traps on type-check failure. On Linux, these generate `SIGILL` (signal 4). The trap instruction's address directly precedes the CFI check, so `si_addr` points into the check sequence — distinguishing CFI traps from other illegal instructions.

Linux kernel tracepoint for CFI violations:

```c
/* Attach to tracepoint:exceptions/page_fault_user or signal_deliver.
 * Filter: sig==4 AND si_addr is within a known CFI check region.
 * On Android, __cfi_slowpath failures also log via __cfi_check_fail(). */

/* Android-specific: monitor __cfi_check_fail via uprobe */
SEC("uprobe//system/lib64/libc.so:__cfi_check_fail")
int trace_cfi_fail(struct pt_regs *ctx) {
    struct cfi_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->violation = 1;  /* CFI type-check failure */
    e->ip = PT_REGS_IP(ctx);
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    bpf_ringbuf_submit(e, 0);
    return 0;
}
```

### 18.6 Behavioral detection: indirect call target entropy analysis

Hardware-specific exception signals detect CFI violations *after* they trigger a fault. Behavioral analysis can detect CFI bypass *attempts* — attacks that stay within the valid target set but exhibit anomalous dispatch patterns.

**Indirect call target entropy:** legitimate programs exhibit low entropy in their indirect call targets — most virtual call sites dispatch to 1-3 implementations. A CFI bypass that searches for useful ENDBR gadgets or type-compatible functions produces measurably higher target entropy at specific call sites.

Implementation using Intel LBR (Last Branch Record) or ARM BRBE (Branch Record Buffer Extension):

```python
#!/usr/bin/env python3
"""icall_entropy.py — Analyze indirect call target entropy from perf LBR data.
Usage: perf record -e branches:u -j ind_call -- ./target_binary
       perf script -F ip,brstack | python3 icall_entropy.py
"""
import sys, math
from collections import defaultdict

call_sites = defaultdict(lambda: defaultdict(int))

for line in sys.stdin:
    fields = line.strip().split()
    for br in fields[1:]:
        parts = br.split('/')
        if len(parts) < 4:
            continue
        src, dst = parts[0], parts[1]
        flags = parts[3] if len(parts) > 3 else ''
        if 'ind_call' in flags or 'call' in flags:
            call_sites[src][dst] += 1

print(f"{'Call Site':<20} {'Targets':>8} {'Entropy':>8} {'Flag':>6}")
print('-' * 50)
for site, targets in sorted(call_sites.items(), key=lambda x: -len(x[1])):
    total = sum(targets.values())
    if total < 10:
        continue
    probs = [c / total for c in targets.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    flag = '**HIGH**' if entropy > 3.0 and len(targets) > 8 else ''
    print(f"{site:<20} {len(targets):>8} {entropy:>8.2f} {flag:>6}")
    if flag:
        print(f"  Top targets: {list(targets.keys())[:5]}")
```

An entropy exceeding 3.0 bits at a single call site with more than 8 distinct targets warrants investigation — it may indicate gadget scanning, type confusion exploitation, or legitimate polymorphism (virtual dispatch in template-heavy C++ requires baseline calibration per binary).

---

## 19. CFI bypass case studies: deep analysis

Section 11 covers three case studies at the exploit-chain level. This section expands the analysis with a structured three-part format: the specific technique used, why CFI failed to prevent it, and what defensive measure would have closed the gap.

### 19.1 CVE-2023-38606 — Operation Triangulation: hardware register manipulation bypassing PAC

**Platform:** iOS/macOS, Apple A12–A16, M1–M2. **CVSS:** 9.8. **Exploited:** 2023 (Kaspersky disclosure).

**Technique used.** The attackers combined CVE-2023-32434 (XNU integer overflow for kernel read/write) with CVE-2023-38606 to achieve full kernel compromise. The critical innovation was a *data-only* attack that never forged a PAC:
1. Kernel read/write obtained via the integer overflow.
2. Kernel page table entries modified to remap MMIO regions for Apple's undocumented hardware registers.
3. MMIO writes to hardware configuration registers disabled PAC enforcement and AMCC (Apple Memory Controller Cache) protections.
4. With PAC disabled at the hardware level, the attacker had unconstrained kernel code execution.

**Why CFI failed.** PAC protects control-flow pointers (return addresses, function pointers) by signing them. It does not protect *data* values — page table entries, configuration registers, or MMIO mappings. The attacker operated entirely in the data plane: every instruction executed along its intended control-flow path; only the data operands were attacker-controlled. PAC's verification was never invoked because no PAC-signed pointer was ever dereferenced with a forged signature.

**What would have prevented it.** The specific gap was the ability to remap arbitrary physical memory (including MMIO) via kernel page table manipulation:
- **KDP (Kernel Data Protection):** Apple's PPL (Page Protection Layer) protects certain kernel data structures from modification even with a kernel write primitive, but the specific page table manipulation path was not PPL-protected at the time.
- **Hypervisor-based page table protection:** a hypervisor (or Apple's Secure Monitor at EL3) that traps all kernel page table modifications and validates them against a policy would have prevented the MMIO remapping.
- **IOMMU enforcement:** restricting which physical memory regions can be mapped by the kernel (rather than allowing arbitrary physical address mapping) would have blocked access to the undocumented hardware registers.

Apple's fix in iOS 16.6 included patching the kernel vulnerability, removing the undocumented hardware register interface, and adding PPL protection to the affected page table modification paths.

### 19.2 Chrome V8 sandbox escape chains bypassing CET

**Platform:** Chrome on Windows 11 with CET enabled. **CVE:** CVE-2024-3159 (Pwn2Own Vancouver 2024). **CVSS:** 8.8.

**Technique used.** The exploit targeted a V8 type confusion vulnerability that provided an arbitrary read/write primitive within the V8 heap sandbox:
1. Type confusion in V8's TurboFan JIT created a length confusion on a TypedArray, yielding out-of-bounds read/write within the V8 sandbox region.
2. The attacker corrupted V8's internal `Code` objects to point to attacker-controlled JIT-compiled code. Because V8's JIT legitimately generates `ENDBR64` at function entries, the attacker's payload was IBT-valid.
3. The corrupted `Code` object's entry point was a JIT-generated function that performed the sandbox escape — calling `VirtualProtect` to make a region RWX, then copying and executing shellcode.
4. Shadow stack was not violated: the exploit used legitimate `call`/`ret` pairs through the JIT-generated code, maintaining shadow stack consistency.

**Why CFI failed.** CET IBT requires `ENDBR64` at indirect branch targets — but V8's JIT generates `ENDBR64` instructions by design, making all JIT-generated functions IBT-valid. The shadow stack was maintained because the attacker used the JIT's own calling conventions rather than corrupting return addresses. CET was never violated: the exploit operated within the JIT's legitimate code-generation capabilities.

**What would have prevented it.**
- **V8 Sandbox hardening:** the fundamental gap was that the V8 sandbox allowed corruption of `Code` objects. V8's sandbox (introduced 2022, iteratively hardened) now isolates `Code` object metadata from the sandbox heap, preventing type-confused writes from reaching code pointers.
- **Code pointer integrity (CPI):** if V8's code pointers were stored in a separate, integrity-protected region (similar to software shadow stacks for data pointers), the corruption of `Code` objects would have been caught.
- **XFG-level type enforcement on JIT dispatch:** XFG's type-hash check on indirect calls through JIT-generated code would have restricted which JIT functions could be reached from a given call site. If the corrupted `Code` object's type hash didn't match the expected hash at the dispatch site, XFG would have trapped.

### 19.3 iOS kernel exploits bypassing PAC: PACMAN and signing gadget chains

**Platform:** Apple M1/M2, iOS 14–16. **Research:** PACMAN (Ravichandran et al., MIT, 2022); real-world exploitation in CVE-2021-30955, CVE-2023-41993.

**PACMAN technique.** PACMAN exploits the microarchitectural difference between PAC authentication success (which retires normally) and PAC authentication failure (which faults). On cores *without* `FEAT_FPAC`, authentication failure produces an invalid pointer that faults only when dereferenced — but the speculation window between authentication and dereference leaks the success/failure outcome through cache timing:
1. The attacker guesses a PAC value and uses `AUT*` to authenticate the pointer speculatively.
2. A dependent load using the authenticated pointer executes speculatively.
3. If the PAC was correct, the speculative load accesses a valid address and fills a cache line. If incorrect, the load faults speculatively (no cache fill).
4. The attacker measures cache state to determine whether the guess was correct.
5. The attacker iterates through the 2^16 PAC space (for the default QARMA configuration), cracking the PAC in ~65,536 attempts — each taking microseconds via speculative execution.

**Signing gadget chains (CVE-2021-30955).** An alternative PAC bypass avoids brute-force entirely by finding kernel code paths that sign pointers under attacker-influenced conditions:
1. The attacker triggers a kernel IPC type confusion that causes the kernel to process an attacker-controlled object through a code path that calls `PACIA` or `PACDA` on a pointer derived from attacker-controlled data.
2. The signed pointer is returned to user space (via the IPC reply or observable side effects).
3. The attacker now possesses a legitimately PAC-signed pointer that points to their chosen target.

**Why CFI failed.** For PACMAN: PAC was designed with the assumption that authentication failure would be caught at dereference time. The speculative execution window between `AUT*` and the dependent load was not considered in the original threat model. For signing gadgets: PAC assumes that code with signing authority operates on trusted data. Kernel IPC paths that sign pointers derived from user-controlled input violate this assumption.

**What would have prevented it.**
- **`FEAT_FPAC` (deployed on M3+, Cortex-X4+):** faults *synchronously* on PAC authentication failure, eliminating the speculative window that PACMAN exploits. This is a definitive hardware fix for the PACMAN class.
- **Context-sensitive PAC signing:** PACStack's chained signing (§17.4) would have prevented the signing gadget attack by making each PAC dependent on the full call chain. A PAC obtained through a confused IPC path would be invalid in the exploitation context because the call-chain modifier would differ.
- **Kernel pointer signing audits:** systematically reviewing all kernel code paths that sign pointers and ensuring none accept user-controlled input as the signing operand. Apple performed this audit after the PACMAN disclosure, adding runtime checks to IPC paths.

### 19.4 Windows kernel exploits bypassing CFG

**Platform:** Windows 10/11 with CFG and CET. **CVE:** CVE-2024-21338 (Lazarus Group), CVE-2024-38106 (Windows kernel race condition). **CVSS:** 7.8.

**Technique used (CVE-2024-21338).** The Lazarus Group's exploit targeted the `appid.sys` driver (AppLocker component) to obtain kernel read/write:
1. A vulnerability in `appid.sys` provided a controlled kernel write primitive.
2. Rather than hijacking a kernel function pointer (which CFG would detect), the attacker modified the `_TOKEN` structure of the exploit process — changing the process token to that of SYSTEM.
3. The exploit never called through a corrupted pointer, never generated a CFG violation, and never triggered a CET exception.

**Why CFI failed.** CFG validates indirect call targets against a bitmap. CET validates return addresses against the shadow stack. Neither mechanism inspects non-control-flow kernel data structures (`_TOKEN`, `_EPROCESS`, `_SEP_TOKEN_PRIVILEGES`). The attacker escalated privileges through data corruption alone — modifying the security context rather than the execution context.

**What would have prevented it.**
- **Hypervisor-protected code integrity (HVCI) for data:** extending HVCI's memory integrity guarantees to cover critical kernel data structures (tokens, credentials, security descriptors) in addition to code and control-flow pointers. Microsoft's Kernel Data Protection (KDP) partially addresses this by marking specified kernel data as read-only after initialization.
- **Credential Guard isolation:** Windows Credential Guard runs the LSA process in a virtualization-based security (VBS) isolated environment. Extending this model to protect kernel token structures from modification — even by code running in ring 0 — would block the token-swap technique.
- **Behavioral monitoring:** the `Microsoft-Windows-Threat-Intelligence` ETW provider detects token modification anomalies. The detection rule from §10.4 can be enhanced to alert when a process token changes to SYSTEM outside of known elevation paths (UAC, service control manager).

---

## 20. CFI testing and verification

Deploying CFI without testing its effectiveness creates a false sense of security. Misconfigured CFI (missing compiler flags on critical DSOs, disabled enforcement due to compatibility fallbacks, incomplete coverage of indirect call sites) is common in real-world deployments. This section covers methodologies and tools for verifying that CFI actually stops the attacks it claims to prevent.

### 20.1 CFI effectiveness testing methodology: controlled bypass attempts

A systematic CFI test suite should verify each enforcement point by attempting controlled bypasses:

```bash
#!/usr/bin/env bash
# cfi_effectiveness_test.sh — Verify CET enforcement on a target binary.
# Requires: Linux 6.6+, CET-capable hardware, target compiled with -fcf-protection=full.
set -euo pipefail

BINARY="${1:?Usage: $0 <elf-binary>}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=== CFI Effectiveness Test — $BINARY ($TIMESTAMP) ==="

# 1. Verify CET markings present
echo "[1] Checking ELF CET properties..."
PROPS=$(readelf -n "$BINARY" 2>/dev/null || true)
echo "$PROPS" | grep -q "IBT" && echo "  IBT: PRESENT" || { echo "  IBT: MISSING — FAIL"; exit 1; }
echo "$PROPS" | grep -q "SHSTK" && echo "  SHSTK: PRESENT" || echo "  SHSTK: MISSING (may be OK for shared lib)"

# 2. Verify all loaded DSOs have CET
echo "[2] Checking DSO CET coverage..."
if [ -x "$BINARY" ]; then
    ldd "$BINARY" 2>/dev/null | awk '/=>/{print $3}' | while read -r lib; do
        [ -f "$lib" ] || continue
        lprops=$(readelf -n "$lib" 2>/dev/null || true)
        if ! echo "$lprops" | grep -q "IBT"; then
            echo "  [!] WEAK LINK: $lib lacks IBT — process-wide CET may be disabled"
        fi
    done
fi

# 3. Verify shadow stack is active at runtime
echo "[3] Testing shadow stack enforcement..."
cat > /tmp/cet_test_shstk.c << 'CEOF'
#include <stdio.h>
#include <signal.h>
#include <setjmp.h>
static volatile int caught = 0;
static void handler(int sig) { caught = 1; }
int main(void) {
    signal(SIGSEGV, handler);
    /* Attempt to corrupt return address via inline asm */
    volatile unsigned long fake_ret = 0x4141414141414141UL;
    /* This will trigger #CP if shadow stack is active */
    asm volatile(
        "movq %0, (%%rsp)\n"  /* overwrite return address */
        : : "r"(fake_ret) : "memory"
    );
    if (caught) {
        printf("SHSTK: ENFORCED (caught SIGSEGV from #CP)\n");
        return 0;
    }
    printf("SHSTK: NOT ENFORCED (no fault on return address corruption)\n");
    return 1;
}
CEOF
gcc -fcf-protection=full -o /tmp/cet_test_shstk /tmp/cet_test_shstk.c 2>/dev/null \
    && /tmp/cet_test_shstk || echo "  (compile/run failed — check hardware support)"
rm -f /tmp/cet_test_shstk /tmp/cet_test_shstk.c

# 4. Verify IBT enforcement
echo "[4] Testing IBT enforcement..."
cat > /tmp/cet_test_ibt.c << 'CEOF'
#include <stdio.h>
#include <signal.h>
static volatile int caught = 0;
static void handler(int sig) { caught = 1; }
void target_no_endbr(void) { printf("reached non-ENDBR target\n"); }
int main(void) {
    signal(SIGSEGV, handler);
    void (*fptr)(void) = target_no_endbr;
    /* Force indirect call to function without ENDBR */
    asm volatile("notrack call *%0" : : "r"(fptr));
    if (caught) {
        printf("IBT: ENFORCED (SIGSEGV on non-ENDBR target)\n");
        return 0;
    }
    printf("IBT: NOT ENFORCED\n");
    return 1;
}
CEOF
gcc -fcf-protection=full -o /tmp/cet_test_ibt /tmp/cet_test_ibt.c 2>/dev/null \
    && /tmp/cet_test_ibt || echo "  (compile/run failed — check hardware support)"
rm -f /tmp/cet_test_ibt /tmp/cet_test_ibt.c

echo "=== Test Complete ==="
```

### 20.2 Fuzzing CFI implementations: differential testing across compilers

CFI implementations may differ between compilers (GCC CET vs. Clang CET, MSVC CFG vs. Clang CFI), creating gaps when binaries from different toolchains are linked together. Differential fuzzing reveals these gaps:

**Methodology:**
1. Compile the same C/C++ source with GCC (`-fcf-protection=full`), Clang (`-fcf-protection=full -fsanitize=cfi-icall`), and MSVC (`/guard:cf /CETCOMPAT`).
2. Generate test inputs that exercise all indirect call paths (using coverage-guided fuzzing with AFL++ or libFuzzer).
3. Compare which indirect calls are CFI-protected across each build.
4. Identify call sites that are protected in one toolchain but not another.

```bash
# Differential CFI fuzzing setup with AFL++
# Step 1: Build with GCC CET instrumentation
CC=gcc CFLAGS="-fcf-protection=full" AFL_CC=afl-gcc-fast \
    make clean all TARGET=target_gcc

# Step 2: Build with Clang CFI + CET
CC=clang CFLAGS="-fcf-protection=full -fsanitize=cfi-icall -flto -fvisibility=hidden" \
    AFL_CC=afl-clang-lto make clean all TARGET=target_clang

# Step 3: Run parallel fuzzing, compare crash sets
afl-fuzz -i corpus/ -o out_gcc  -- ./target_gcc @@  &
afl-fuzz -i corpus/ -o out_clang -- ./target_clang @@ &
wait

# Step 4: Cross-pollinate — run gcc-unique crashes on clang binary and vice versa
for crash in out_gcc/crashes/id:*; do
    timeout 5 ./target_clang "$crash" 2>&1 | grep -q "CFI\|SIGILL" \
        || echo "[GAP] GCC crash $crash does NOT trigger Clang CFI"
done
```

### 20.3 Binary analysis for CFI coverage gaps

Static analysis tools can identify indirect call sites that lack CFI protection — indicating missing compiler flags, excluded translation units, or third-party binaries linked without CFI.

```python
#!/usr/bin/env python3
"""cfi_gap_scanner.py — Find unprotected indirect calls in ELF binaries.
Requires: capstone >= 5.0
Usage:    python3 cfi_gap_scanner.py /usr/lib/x86_64-linux-gnu/libc.so.6
"""
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, CS_GRP_CALL, CS_GRP_JUMP

def scan_binary(path):
    with open(path, 'rb') as f:
        code = f.read()

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    # Find .text section offset (simplified — production tool should parse ELF headers)
    text_offset = code.find(b'\xf3\x0f\x1e\xfa')  # ENDBR64 marker
    if text_offset < 0:
        print(f"[!] No ENDBR64 found in {path} — binary may lack IBT support entirely")
        return

    unprotected = []
    total_indirect = 0

    for insn in md.disasm(code[text_offset:], text_offset):
        # Detect indirect call/jmp (register or memory operand)
        if insn.group(CS_GRP_CALL) or insn.group(CS_GRP_JUMP):
            ops = insn.operands
            if ops and ops[0].type != 1:  # Not immediate (register or memory)
                total_indirect += 1
                # Check if preceding instruction sequence contains a CFI check
                # (simplified: look for ENDBR64 or ud2 in the preceding 32 bytes)
                pre_bytes = code[max(0, insn.address-32):insn.address]
                has_cfi_check = (b'\xf3\x0f\x1e\xfa' in pre_bytes  # ENDBR64 nearby
                                 or b'\x0f\x0b' in pre_bytes)       # ud2 (Clang CFI trap)
                if not has_cfi_check:
                    unprotected.append((insn.address, insn.mnemonic, insn.op_str))

    print(f"Binary: {path}")
    print(f"  Total indirect branches: {total_indirect}")
    print(f"  Unprotected (no nearby CFI check): {len(unprotected)}")
    if unprotected:
        print(f"  Coverage: {100*(total_indirect-len(unprotected))/max(total_indirect,1):.1f}%")
        print(f"  First 10 unprotected sites:")
        for addr, mnem, op in unprotected[:10]:
            print(f"    0x{addr:012x}  {mnem} {op}")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        scan_binary(p)
```

### 20.4 Performance benchmarking: CFI overhead measurement

CFI overhead varies by workload and mechanism. Benchmarking before and after CFI enablement ensures that performance budgets are met:

```bash
#!/usr/bin/env bash
# cfi_benchmark.sh — Measure CFI overhead on SPEC-like workloads.
# Usage: ./cfi_benchmark.sh <binary_no_cfi> <binary_with_cfi> <args...>
set -euo pipefail

BASELINE="${1:?}" ; CFI="${2:?}" ; shift 2 ; ARGS="$*"
RUNS=5
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "=== CFI Overhead Benchmark ($TIMESTAMP) ==="
echo "Baseline: $BASELINE"
echo "CFI-enabled: $CFI"
echo "Args: $ARGS"
echo "Runs: $RUNS"
echo ""

bench() {
    local binary="$1" label="$2"
    local times=()
    for i in $(seq 1 $RUNS); do
        t=$( { /usr/bin/time -f '%e' "$binary" $ARGS > /dev/null; } 2>&1 )
        times+=("$t")
    done
    # Calculate mean
    local sum=0
    for t in "${times[@]}"; do sum=$(echo "$sum + $t" | bc -l); done
    local mean=$(echo "scale=3; $sum / $RUNS" | bc -l)
    echo "$label: mean=${mean}s  raw=[${times[*]}]"
    echo "$mean"
}

base_mean=$(bench "$BASELINE" "Baseline")
cfi_mean=$(bench "$CFI" "CFI")

overhead=$(echo "scale=2; (($cfi_mean - $base_mean) / $base_mean) * 100" | bc -l)
echo ""
echo "Overhead: ${overhead}%"
[ "$(echo "$overhead > 10" | bc)" -eq 1 ] \
    && echo "[!] WARNING: CFI overhead exceeds 10% — investigate hot paths" \
    || echo "[OK] CFI overhead within acceptable range"
```

**Typical overhead ranges by mechanism:**

| Mechanism | Typical Overhead | Benchmark |
|-----------|-----------------|-----------|
| CET shadow stack | 0.5–2% | SPEC CPU2017 |
| CET IBT | < 1% | SPEC CPU2017 |
| PAC (return address signing) | < 1% | SPEC CPU2017 |
| BTI | < 1% | SPEC CPU2017 |
| MTE (synchronous) | 3–5% | Android app benchmarks |
| MTE (asynchronous) | 1–2% | Android app benchmarks |
| Clang CFI (cfi-icall) | 1–5% | Chromium page_cycler |
| CFG | 1–3% | Windows desktop benchmarks |
| XFG | 2–4% | Windows desktop benchmarks |

### 20.5 CI/CD integration: automated CFI verification in build pipelines

CFI protection is only as strong as its weakest link — a single DSO compiled without CFI flags disables process-wide enforcement on CET and degrades Clang CFI coverage. CI/CD pipelines must verify CFI status on every build artifact.

```yaml
# .github/workflows/cfi-verification.yml
name: CFI Verification Gate
on: [push, pull_request]

jobs:
  cfi-check:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Build with CFI
        run: |
          export CC=clang CXX=clang++
          export CFLAGS="-fcf-protection=full -fsanitize=cfi-icall -flto -fvisibility=hidden"
          export CXXFLAGS="$CFLAGS"
          export LDFLAGS="-fuse-ld=lld -Wl,-z,shstk -Wl,-z,ibt"
          make -j$(nproc)

      - name: Verify CET properties on all ELF outputs
        run: |
          FAIL=0
          find build/ -type f -executable | while read -r bin; do
              file "$bin" | grep -q ELF || continue
              props=$(readelf -n "$bin" 2>/dev/null || true)
              missing=""
              echo "$props" | grep -q "IBT"   || missing+="IBT "
              echo "$props" | grep -q "SHSTK" || missing+="SHSTK "
              if [ -n "$missing" ]; then
                  echo "::error file=$bin::Missing CET properties: $missing"
                  FAIL=1
              fi
          done
          [ "$FAIL" -eq 0 ] || { echo "::error::CFI verification failed"; exit 1; }

      - name: Verify Clang CFI symbols present
        run: |
          find build/ -name '*.so' -o -name '*.so.*' | while read -r lib; do
              if ! nm -D "$lib" 2>/dev/null | grep -q '__cfi_check\|__cfi_slowpath'; then
                  echo "::warning file=$lib::No Clang CFI symbols — may lack cfi-icall protection"
              fi
          done

      - name: DSO linkage CFI coverage report
        run: |
          echo "## CFI Coverage Report" >> "$GITHUB_STEP_SUMMARY"
          echo "| Binary | IBT | SHSTK | Clang CFI |" >> "$GITHUB_STEP_SUMMARY"
          echo "|--------|-----|-------|-----------|" >> "$GITHUB_STEP_SUMMARY"
          find build/ -type f -executable | while read -r bin; do
              file "$bin" | grep -q ELF || continue
              props=$(readelf -n "$bin" 2>/dev/null || true)
              ibt=$(echo "$props" | grep -q "IBT" && echo "Y" || echo "N")
              shstk=$(echo "$props" | grep -q "SHSTK" && echo "Y" || echo "N")
              cfi_sym=$(nm -D "$bin" 2>/dev/null | grep -q '__cfi_check' && echo "Y" || echo "N")
              echo "| $(basename "$bin") | $ibt | $shstk | $cfi_sym |" >> "$GITHUB_STEP_SUMMARY"
          done
```

This pipeline enforces three invariants on every commit:
1. All ELF binaries carry IBT and SHSTK properties (CET enforcement).
2. All shared libraries export Clang CFI check symbols (forward-edge type enforcement).
3. A coverage report is generated for audit visibility, blocking merges when CFI properties are missing.

---

## 21. Cross-references

**Domain 3 (memory corruption):** corruption primitives (§3) are preconditions for CFI attacks. MTE (§6) mitigates heap corruption; CET/PAC mitigate the subsequent hijack. Vtable corruption → ENDBR-gadget/COOP attacks (§2.1); return-address corruption → caught by shadow stacks (§1) or PAC (§3).

**Domain 5 (kernel exploitation):** kernel IBT (§1.4), kernel PAC bypass (§4.5). Kernel write primitives must overcome both MTE and kernel CFI. Kernel shadow stacks (§1.4) remain a deployment gap.

**Domain 6 (mitigation bypass):** CET and PAC are the layer after ASLR/DEP bypass — they architecturally prevent the control-flow hijack that ASLR/DEP only probabilistically hinder.

**Domain 7 (speculative execution):** PACMAN (§4.3) and MTE speculative bypass (§6.6) use Spectre-class cache side-channels (Domain 7, Chapter 7A). Shadow stack checks at `RET` retirement leave a speculative execution window before `#CP`.

**Domain 1 (binary formats):** CET IBT in `PT_GNU_PROPERTY` (Domain 1, 1B §5.3). CFG in PE load config (Domain 1, Ch 2 §11). BTI via `GNU_PROPERTY_AARCH64_FEATURE_1_BTI`. Linker GP-page marking covered in Domain 1.

**Domain 2 (process memory):** shadow stack page-table encoding (§1.1). MTE tag storage (§6.2). PAC uses TBI (Domain 2, 2A §1.2).

**Domain 11 (malware):** EDR evasion via indirect syscalls interacts with CET IBT — stubs need `ENDBR64`. Shadow stack deployment drives the shift from `ret`-based ROP to `jmp`-based syscall execution.

**Domain 27 (detection engineering):** CFI violation telemetry (§10, §18) feeds SIEM pipelines. CET violations are high-confidence exploitation indicators. Zero-trust architectures should incorporate CFI status as a device health signal.
